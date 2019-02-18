# -*- coding: utf-8 -*-
"""
Created on Wed May 16 13:40:39 2018

@author: Guodong
"""
from datetime import datetime, timedelta
from Global_Variables import *
from copy import deepcopy

"""Note that if a moduled has been loaded, if will not be reloaded again"""

def CapacityData( CTOP_FLs ):
    """
    1  We will first get the nominal demand capacity imbalance information. Demand means all CTOP captured flights
    2  We will then get the number of slots available at each time period M. This information will be used in optimization model

    Num_Violations: number fo violations before running optimization model
    """

    EXPT_FLs     = CTOP_FLs[ CTOP_FLs['Flight_Status'] != 'Reroutable' ] #list of all exempted flights
    # Reroutables  = CTOP_FLs[CTOP_FLs['Flight_Status'] == 'Reroutable']
    M            = deepcopy( Capacity )

    #AAFLs['Fix2Runway'] = (AAFLs['ETA']-AAFLs['EAFT']).dt.seconds/60
    #AAFLs.to_csv('Data\\AAFLs.csv')
    
    Num_Violations = 0

    log = open( Report_File , "a+")
    print('-' * 100)
    print('Demand Capacity Imbalance Information')
    imbalance_info = "From %8s to %8s at %s, demand %3d exceed capacity %3d (%2d)"

    log.write('-' * 100 + '\n')
    log.write('Demand Capacity Imbalance Information\n')

    # for key, item in M.items():
    for key, item in [(key, M[key]) for key in FCAs]:
        for t in range( len( TIME ) ):
            Interval_Start = CTOP_START + timedelta( minutes = t * 15 )
            Interval_End   = CTOP_START + timedelta( minutes = (t + 1)*15 )

            Condition = ( CTOP_FLs['AFIX'] == key ) & ( CTOP_FLs['EAFT'] >= Interval_Start ) & \
                        ( CTOP_FLs['EAFT'] < Interval_End )

            if len( CTOP_FLs[ Condition ] ) > M[key][t] :
                print (imbalance_info % (Interval_Start.strftime("%m-%d %H:%M"), (Interval_End - timedelta( minutes = 1 )).strftime("%m-%d %H:%M"), \
                    key, len(CTOP_FLs[Condition]), M[key][t], len(CTOP_FLs[Condition]) - M[key][t] ))

                log.write( imbalance_info % (Interval_Start.strftime("%m-%d %H:%M"), (Interval_End - timedelta( minutes = 1 )).strftime("%m-%d %H:%M"), \
                                             key, len(CTOP_FLs[Condition]), M[key][t], len(CTOP_FLs[Condition]) - M[key][t] ) )
                log.write("\n")

                Num_Violations += len( CTOP_FLs[ Condition ] ) - M[key][t]

            Condition = ( EXPT_FLs['AFIX'] == key ) & ( EXPT_FLs['EAFT'] >= Interval_Start ) & \
                        ( EXPT_FLs['EAFT'] < Interval_End )

            M[key][t] -= len( EXPT_FLs[Condition] )

    print('In total %d FCA Capacity Violations'% Num_Violations )
    log.write( 'In total %d FCA Capacity Violations \n'% Num_Violations )

    log.close()
    return M, Num_Violations




























