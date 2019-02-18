from Process_TOS import ReadTOSFile, PrepareInputLightCTOP, TOS_Market_Analysis
from LightCTOP_Xpress import LightCTOPModel, LightCTOPModel_Main
from Global_Variables import *

def Power_Run( TOS, CTOP_FLs, Current_Time, M ):
    log        = open( Report_File , "a+")

    print('Performing Maximum Mileage Sensitivity Analysis\n')
    log.write('Performing Maximum Mileage Sensitivity Analysis\n')

    df = pd.DataFrame({'Mileage Max': ExtraMileMax_Sensitivity} , dtype = int)
    #bosung
    #df = pd.concat( [df, pd.DataFrame(columns=['FCA Violations', 'Rerouted Flights', 'Reroute Mileages'])], sort=False )

    i = 0
    for extra_mile_max in ExtraMileMax_Sensitivity:
        Model_Input        = PrepareInputLightCTOP(TOS, CTOP_FLs, extra_mile_max, Current_Time)
        prob, delta, B, E  = LightCTOPModel_Main( M, *Model_Input, Message = False)

        df.at[i, 'FCA Violations']   = sum( prob.getSolution(E[t, k]) for (t, k) in E.keys() )
        df.at[i, 'Rerouted Flights'] = sum( prob.getSolution( delta[i, j] ) for (i, j) in delta.keys() if j!=0 )
        df.at[i, 'Reroute Mileages'] = prob.getObjVal()

        i = i + 1
    # df.set_index('Mileage Max')
    print( df )
    print('-' * 100)

    df.to_string( log )
    log.write('\n')
    log.write('-' * 100 + '\n')
    log.close()