"""
To analyze the new schedule,
"""
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from pytz import UTC, timezone

from Process_ADL import ReadADLFile, ProcessARVFlights, Retrieve_ADL_File, CheckingInputParameters
from Process_TOS import ReadTOSFile, PrepareInputLightCTOP, TOS_Market_Analysis
from Process_Capacity import * #
from datetime import datetime, timedelta
from Global_Variables import *
# from LightCTOP import LightCTOPModel
from LightCTOP_Xpress import LightCTOPModel, LightCTOPModel_Main
from Visualization import Demand_Capacity_Single_Window, Demand_Capacity
from Analyze_Solution import Process_Solution, Visualize_RerouteInfo_Single_Window, Visualize_RerouteInfo
from Analyze_Solution import Generate_OneLineTOS_For_Submission
from Sensitivity_Analysis import Power_Run
import pytz
import matplotlib.pyplot as plt

plt.close("all")
#%%
FLs_All  = pd.read_excel( "Data\\DFW900 2019 Fix Load-Guodong.xlsx"  )
AA_FLs   = FLs_All[ FLs_All['Year'] == 2019 ]
ADLFile  = 'Data\\ADL_Files\\dfw__.lcdm.11102207.01.all.gamf'
TOSFile  = "Data\\cannedrouteexport. 20180606_1707.csv"
Current_Time, ARV_Flights, Column_Names, Date, _, _, _ = ReadADLFile(  ADLFile )

TOS           = ReadTOSFile( AFIXs, TOSFile )
CheckingInputParameters( Current_Time )
_, CTOP_FLs = ProcessARVFlights( ARV_Flights, Column_Names, TOS, Date, Current_Time )
#%%
def Process_Schedule_File( AA_FLs, CTOP_FLs, TOS, Current_Time ):
    Cols = ['ACID', 'DEST', 'ORIG', 'ETD', 'ETA', 'AFIX', 'EAFT', 'TYPE', 'MAJOR', 'Carrier', 'ID',
            'AFIX_New', 'EAFT_New', 'Route_ID', 'Route_ID_New', 'Route_ID_New_TOS', 'Extra Wind Miles',
            'Flight_Status', 'Ref_Central_Time']
    CTOP_FLs = CTOP_FLs[Cols]
    CTOP_FLs = CTOP_FLs[CTOP_FLs['MAJOR'] != 'AAL']

    AA_FLs['MAJOR'] = 'AAL'
    AA_FLs['ACID'] = 'AAL' + AA_FLs['fltno'].astype(str)
    AA_FLs = AA_FLs.rename(columns={'dest': 'DEST', 'orig': 'ORIG', 'fltno': 'ID', 'ArrivalFixDrn1': 'AFIX',
                                    'depgmt': 'ETD', 'arrgmt': 'ETA', 'fixarrloc1': 'EAFT', 'eqp': 'TYPE'})
    AA_FLs['Carrier'] = 'AAL'

    for (key, fca) in FCAs_Info.iteritems():
        AA_FLs['AFIX'] = AA_FLs['AFIX'].str.replace(fca, key)

    central = timezone('US/Central')
    AA_FLs['EAFT'] = AA_FLs['EAFT'].apply(central.localize)
    AA_FLs['EAFT'] = AA_FLs['EAFT'].dt.tz_convert('UTC')
    AA_FLs['EAFT'] = AA_FLs['EAFT'].dt.tz_localize(None)  # tz_aware to tz_native

    for col in ['ETD', 'ETA', 'EAFT']:
        AA_FLs[col] = AA_FLs[col] - pd.offsets.DateOffset(years=1)

    Condition = (AA_FLs['EAFT'] >= CTOP_START) & (AA_FLs['EAFT'] <= CTOP_END)
    AA_FLs = AA_FLs[Condition]

    AA_FLs['Ref_Central_Time'] = AA_FLs['ETD'] - timedelta(minutes=ReferenceTime)
    AA_FLs['Ref_Central_Time'] = AA_FLs['Ref_Central_Time'].dt.tz_localize('UTC').dt.tz_convert('US/Central')

    AA_FLs = AA_FLs.reindex(columns=Cols)
    AA_FLs['AFIX_New'] = AA_FLs['AFIX']
    AA_FLs['EAFT_New'] = AA_FLs['EAFT']

    Condition = (AA_FLs['ETA'] <= Current_Time)
    AA_FLs.at[Condition, 'Flight_Status'] = 'Landed'

    Condition = (AA_FLs['ETA'] > Current_Time) & (AA_FLs['ETD'] <= Current_Time)  # departed but not landed yet
    AA_FLs.at[Condition, 'Flight_Status'] = 'En route'

    """Reroutable if they have TOS options and they are not exempted"""
    Condition = (AA_FLs['ETD'] > Current_Time) & (AA_FLs['ETD'] - Current_Time > ExemptTime)
    AA_FLs.at[Condition, 'Flight_Status'] = 'Reroutable'

    """Further Investigate if a flight has TOS route or not"""
    Reroutables = AA_FLs[AA_FLs['Flight_Status'] == 'Reroutable']
    for index, row in Reroutables.iterrows():
        ACID = row['ACID']
        ORIG = row['ORIG']
        DEST = row['DEST']
        airline_code = row['Carrier']

        #Condition = (TOS['airline_code'] == airline_code) & (TOS['departure_station'] == ORIG)
        Condition = (TOS['departure_station'] == ORIG)
        if 0 == len(TOS[Condition]):
            AA_FLs.at[index, 'Flight_Status'] = 'AA No TOS'

    # two scenarios that flights will be exempted 1. explicated exempted 2. not departed yet, but very close to departure
    Condition = (AA_FLs['ETD'] <= Current_Time) & (AA_FLs['ETD'] - Current_Time <= ExemptTime)
    AA_FLs.at[Condition, 'Flight_Status'] = 'Exempted'

    CTOP_FLs = CTOP_FLs.append(AA_FLs)
    CTOP_FLs.reset_index(drop=True, inplace = True)

    return CTOP_FLs


def PrepareInputLightCTOP_Schedule(TOS, CTOP_FLs, ExtraMileMax, Current_Time):
    """
    1 Process the reroutable flights and prepare the input for optimization models
    2 All reroutable flights will have at least two TOS options, otherwise it will be categorized as AA NO_TOS
    3 Ideally the FAA modeled route is the shortest wind mile route, in some cases this may not be true
    4 The key assumption is that delta[i,0] is the default route, therefore we will first need to find the default/modeled route
    5 We will not use the route whose delta mile is larger than a threshold. It is possible that a flight is reroutable but
      after imposing the delta mile constraint, there is no reroute option any more
    6 as long as delta[i,0] is the default route, we don't care if delta[i,1] is shortest or second shortest route
    """
    Reroutables = CTOP_FLs[CTOP_FLs['Flight_Status'] == 'Reroutable']
    Reroutables.reset_index(inplace=True)

    N = {}
    Q = {}
    Ti = {}  # Ti[(i,j,k)]
    Route_ID = {}

    for index, row in Reroutables.iterrows():
        ACID = row['ACID']
        ORIG = row['ORIG']
        DEST = row['DEST']
        FLs_index = row['index']
        TYPE = row['TYPE']
        airline_code = row['Carrier']

        Condition = (TOS['airline_code'] == airline_code) & (TOS['departure_station'] == ORIG)
        TOS_Options = TOS[Condition]

        if len(TOS_Options) == 0:
            Condition = (TOS['departure_station'] == ORIG)
            TOS_Options = TOS[Condition]

            #delete duplicate
            TOS_Options.drop_duplicates( ['route_id_in_FOS'], inplace = True )

        TOS_Options.sort_values(by=['Wind Miles'], inplace=True)

        # If a flight doesn't have TOS route, it will be exempted
        # A rare case is that the modeled route is NOT in the TOS file, then this flight will also be exempted
        # This is because we don't know how to calculate the delta mileage

        if len(TOS_Options) == 0 or row['AFIX'] not in list(TOS_Options['AFIX']):
            N[index] = 1
            Q[index, 0] = 0
            Ti[index, 0, row['AFIX']] = (row['EAFT'] - CTOP_START).seconds / (15 * 60) + 1
        else:
            route_count = 0

            """Find the index of modeled route"""
            for modeled_route, route_row in TOS_Options.iterrows():
                if route_row['AFIX'] == row['AFIX']:
                    # route_seq = [ modeled_route ] + [i for i in TOS_Options.index if i != modeled_route]
                    break

            """We will not use route which delta mileage is greater than ExtraMileMax"""
            ModeledRouteMiles = TOS_Options.loc[modeled_route]['Wind Miles']
            for route_index, route_row in TOS_Options.iterrows():
                TOS_Options.at[route_index, 'Wind Miles'] -= ModeledRouteMiles

            TOS_Options = TOS_Options[TOS_Options['Wind Miles'] <= ExtraMileMax]
            N[index] = len(TOS_Options)
            route_seq = [modeled_route] + [i for i in TOS_Options.index if i != modeled_route]

            for route_index, route_row in TOS_Options.loc[route_seq].iterrows():
                Q[index, route_count] = route_row['Wind Miles']
                assert (np.isfinite(Q[index, route_count])), "Check Route Cost Q!"

                EAFT = row['EAFT'] + timedelta(minutes=Q[index, route_count] * 1.0 / Cruise_Speed(TYPE) * 60)
                Ti[index, route_count, route_row['AFIX']] = (EAFT - CTOP_START).seconds / (15 * 60) + 1
                Route_ID[index, route_count] = route_row['route_id_in_FOS']

                # if Q[index, route_count] < 0:
                #    Q[index, route_count] = 0

                route_count += 1

    PhiT = {k: [] for k in FCAs}
    SigmaT = {i: [] for i in N.keys()}
    Sigma = {}

    for i in N.keys():
        for j in range(N[i]):
            Sigma[(i, j)] = []

    for fca in FCAs:
        for key in Ti.keys():
            if key[2] == fca and key[0] not in PhiT[fca]:
                PhiT[fca].append(key[0])
                SigmaT[key[0]].append(fca)

            if key[2] == fca:
                Sigma[key[0:2]] = fca

    return (N, Q, Ti, PhiT, SigmaT, Sigma, Route_ID)

#%%

CTOP_FLs = Process_Schedule_File( AA_FLs, CTOP_FLs, TOS, Current_Time )
#Model_Input   = PrepareInputLightCTOP( TOS, CTOP_FLs, ExtraMileMax, Current_Time )
Model_Input   = PrepareInputLightCTOP_Schedule( TOS, CTOP_FLs, ExtraMileMax, Current_Time )
M, Vio_Num    = CapacityData( CTOP_FLs )
#%%
plt.close( 'all' )
#Demand_Capacity_Single_Window( CTOP_FLs, Current_Time, Flight_Status = True )
Demand_Capacity( CTOP_FLs, Bin, Current_Time, Flight_Status = True )
#%%
#plt.close( 'all' )
#Solution       = LightCTOPModel( M, *Model_Input)
Solution       = LightCTOPModel_Main( M, *Model_Input )
CTOP_FLs       = Process_Solution( Current_Time, CTOP_FLs, Vio_Num, *Model_Input + Solution )
#Demand_Capacity_Single_Window( CTOP_FLs, Current_Time, Flight_Status = True, Solved = True)
Demand_Capacity( CTOP_FLs, Bin, Current_Time, Flight_Status = True, Solved = True )
# Visualize_RerouteInfo_Single_Window( CTOP_FLs, Current_Time )
Visualize_RerouteInfo( CTOP_FLs, Current_Time )
#%%
#TOS_Market_Analysis( CTOP_FLs, TOS )
#Power_Run( TOS, CTOP_FLs, Current_Time, M )




#CTOP_FLs[ CTOP_FLs['Flight_Status'] == 'Reroutable' ]['EAFT']









