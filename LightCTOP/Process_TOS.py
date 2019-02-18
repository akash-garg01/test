# -*- coding: utf-8 -*-
"""
Created on Sun May 06 17:06:03 2018

@author: Guodong
"""

import pandas as pd
import re
from datetime import datetime, timedelta
from Global_Variables import *

#%%
def ReadTOSFile( AFIXs, TOSFile ):
    """
    1. Read TOSFile into Pandas, assume the TOS file to be a CSV file
    2. Create the arrival fix column 'AFIX'
    3. Match the route to the arrival fix AFIXs global variable
    4. We also check if two TOS route will pass the same arrival fix
    """
    # TOS         = pd.read_excel( TOSFile[0], TOSFile[1], index_col = 'id')
    TOS = pd.read_csv( TOSFile, index_col='id' )
    TOS         = TOS.rename_axis( None )
    TOS['AFIX'] = None
    TOS.rename(columns={'route_string(excluding departure and arrival stations)':'route'}, inplace=True)

    log = open( Report_File , "a+")
    print('-' * 100)
    print('TOS File Analysis')

    log.write('-' * 100 + "\n" )
    log.write('TOS File Analysis\n')

    TOS['route'] = TOS['route'].str.rstrip()

    for index, row in TOS.iterrows():
        for key, value in AFIXs.iteritems():
            if row['route'].split( Space )[-1].lower() in value:
                TOS.loc[index, 'AFIX'] = key
                break
    if 0 == pd.isnull( TOS['AFIX'] ).sum():
        print( "Map route to the arrival fix is successful" )
        log.write( "Map route to the arrival fix is successful" )
    else:
        print( "Map route to the arrival fix is NOT successful" )
        log.write( "Map route to the arrival fix is NOT successful" )
    
    """Check if two TOS routes will cross the same AFIX (No)"""
    Column_Key                  = ['airline_code', 'departure_station', 'AFIX']
    if 0 == len( TOS[ TOS.duplicated( Column_Key ,  keep = False ) ] ):
        print('Different Route Option Crosses Different Arrival Fix')
        log.write('Different Route Option Crosses Different Arrival Fix\n')
    else:
        print('')
        print('For the Following Airline/Station, in a TOS Set at Least Two Routes Cross the Same Arrival Fix')
        print( TOS[ TOS.duplicated( Column_Key ,  keep = False ) ][Column_Key] )

        log.write("\n")
        log.write('For the Following Airline/Station, in a TOS Set at Least Two Routes Cross the Same Arrival Fix\n')
        TOS[TOS.duplicated(Column_Key, keep=False)][Column_Key].to_string( log )
        log.write("\n")
    return TOS

#%%
def TOS_Market_Analysis( CTOP_FLs, TOS ):
    AAFLs = CTOP_FLs[CTOP_FLs['Flight_Status'] != 'OA']
    FL_Markets = AAFLs.groupby(['Carrier', 'ORIG']).size()['AAL'].sort_values(ascending=False).to_frame('FL Count')
    FL_Markets = FL_Markets.head( 30 )
    FL_Markets = pd.concat([FL_Markets, pd.DataFrame(columns=['TOS'])], sort=False)

    for market, row in FL_Markets.iterrows(): #
        Condition            = ( TOS['airline_code'] == 'AAL' ) & ( TOS['departure_station'] == market )
        if 0 == len( TOS[Condition] ):
            FL_Markets.at[market,'TOS']  = 'NO'
        else:
            FL_Markets.at[market, 'TOS'] = 'YES'

    print( 'AAL TOS Information by Markets')
    print( FL_Markets )
    print('-'*100)

def PrepareInputLightCTOP( TOS, CTOP_FLs, ExtraMileMax, Current_Time):
    """
    1 Process the reroutable flights and prepare the input for optimization models
    2 All reroutable flights will have at least two TOS options, otherwise it will be categorized as AA NO_TOS
    3 Ideally the FAA modeled route is the shortest wind mile route, in some cases this may not be true
    4 The key assumption is that delta[i,0] is the default route, therefore we will first need to find the default/modeled route
    5 We will not use the route whose delta mile is larger than a threshold. It is possible that a flight is reroutable but
      after imposing the delta mile constraint, there is no reroute option any more
    6 as long as delta[i,0] is the default route, we don't care if delta[i,1] is shortest or second shortest route
    """
    Reroutables        = CTOP_FLs[ CTOP_FLs['Flight_Status'] == 'Reroutable' ]
    Reroutables.reset_index( inplace = True )
    
    N        = {}
    Q        = {}
    Ti       = {} #Ti[(i,j,k)]
    Route_ID = {}

    for index, row in Reroutables.iterrows():
        ACID                 = row['ACID']
        ORIG                 = row['ORIG']
        DEST                 = row['DEST']
        FLs_index            = row['index']
        TYPE                 = row['TYPE']
        airline_code         = row['Carrier']

        Condition            = ( TOS['airline_code'] == airline_code ) & ( TOS['departure_station'] == ORIG )
        TOS_Options          = TOS[Condition]
        TOS_Options.sort_values( by = ['Wind Miles'], inplace = True)

        #If a flight doesn't have TOS route, it will be exempted
        #A rare case is that the modeled route is NOT in the TOS file, then this flight will also be exempted
        #This is because we don't know how to calculate the delta mileage

        if len( TOS_Options ) == 0  or row['AFIX'] not in list( TOS_Options['AFIX'] ):
            N[index]          = 1
            Q[index, 0]       = 0
            Ti[index, 0, row['AFIX']]  = ( row['EAFT'] - CTOP_START ).seconds/(15*60) + 1
        else:
            route_count   = 0

            """Find the index of modeled route"""
            for modeled_route, route_row in TOS_Options.iterrows():
                if route_row['AFIX'] == row['AFIX']:
                    # route_seq = [ modeled_route ] + [i for i in TOS_Options.index if i != modeled_route]
                    break

            """We will not use route which delta mileage is greater than ExtraMileMax"""
            ModeledRouteMiles = TOS_Options.loc[modeled_route]['Wind Miles']
            for route_index, route_row in TOS_Options.iterrows():
                TOS_Options.at[route_index, 'Wind Miles'] -= ModeledRouteMiles

            TOS_Options   = TOS_Options[TOS_Options['Wind Miles'] <= ExtraMileMax]
            N[index]      = len( TOS_Options )
            route_seq     = [modeled_route] + [i for i in TOS_Options.index if i != modeled_route]

            for route_index, route_row in TOS_Options.loc[route_seq].iterrows():
                Q[index, route_count]          = route_row['Wind Miles']
                assert( np.isfinite( Q[index, route_count] ) ), "Check Route Cost Q!"

                EAFT                           = row['EAFT'] + timedelta( minutes = Q[index, route_count]*1.0/Cruise_Speed( TYPE )*60 )
                Ti[index, route_count, route_row['AFIX']] = ( EAFT - CTOP_START ).seconds/(15*60) + 1
                Route_ID[ index, route_count ] = route_row['route_id_in_FOS']

                #if Q[index, route_count] < 0:
                #    Q[index, route_count] = 0

                route_count += 1

    PhiT         = {k: [] for k in FCAs}
    SigmaT       = {i: [] for i in N.keys()}
    Sigma        = {}
    
    for i in N.keys():
        for j in range( N[i] ):
            Sigma[(i,j)] = []
    
    for fca in FCAs:
        for key in Ti.keys():
            if key[2] == fca and key[0] not in PhiT[fca]:
                PhiT[fca].append( key[0] )
                SigmaT[ key[0] ].append( fca )
    
            if key[2] == fca:
                Sigma[ key[0:2] ] = fca
    
    return ( N, Q, Ti, PhiT, SigmaT, Sigma, Route_ID)
















