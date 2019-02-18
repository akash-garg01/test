# -*- coding: utf-8 -*-
"""
Created on Wed May 16 16:56:38 2018

@author: Guodong

df.rename(columns={'oldName1': 'newName1', 'oldName2': 'newName2'}, inplace=True)
"""

from itertools import combinations, permutations
from Global_Variables import *
import matplotlib.pyplot as plt
import seaborn as sns
sns.set(color_codes=True)
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from Visualization import Demand_By_FCA_Interval, Demand_By_FCA_Interval_Flight_Status

def Process_Solution( Current_Time, CTOP_FLs, Vio_Num, N, Q, Ti, PhiT, SigmaT, Sigma, Route_ID, prob, delta, B, E ):
    """
    1 From the model inputs delta, B, E and model output prob, this function updates EAFT_New and AFIX_New in CTOP_FLs
    2 This function will print detailed reroute flight information
    3 This function can show the distribution of extra mileage delay
    4 This function analyze and plot the current demand capacity violation information
    5
    """
    Count           = 1
    reroute_info    = "(%3d) flight %8s from %4s ETD %6s rerouted from %5s to %5s route ID %3d -> %3d (%4d)"
    AFIX_Changes    = dict.fromkeys( list( permutations(FCAs, 2) ), 0 ) #all possible arrival fix changes
    Reroute_cost    = []
    Reroutables     = CTOP_FLs[ CTOP_FLs['Flight_Status'] == 'Reroutable' ]
    Reroutables.reset_index( inplace = True )

    log = open( Report_File , "a+")
    print('-'*100)
    log.write('-'*100 + '\n')

    for i, flight in Reroutables.iterrows(): #
        index = flight['index']
        TYPE  = flight['TYPE']
        for j in range( N[i] ):
            if j != 0 and prob.getSolution( delta[i,j] ) == 1:
                print( reroute_info % ( Count, flight['ACID'], flight['ORIG'], flight['ETD'].strftime("%m-%d %H:%M"), Sigma[i,0], Sigma[i,j], Route_ID[i, 0], \
                                        Route_ID[i, j], Q[i,j]) )

                log.write( reroute_info % ( Count, flight['ACID'], flight['ORIG'], flight['ETD'].strftime("%m-%d %H:%M"), Sigma[i,0], Sigma[i,j], Route_ID[i, 0], \
                                        Route_ID[i, j], Q[i,j])  )
                log.write("\n")

                Count += 1
                
                AFIX_Changes[( Sigma[i,0], Sigma[i,j] )] += 1
                Reroute_cost.append( Q[i,j] )

                CTOP_FLs.at[index,'AFIX_New']     = Sigma[i, j]
                CTOP_FLs.at[index,'EAFT_New']     = CTOP_FLs.at[index,'EAFT'] + timedelta( minutes = Q[i, j] /Cruise_Speed( TYPE )*60 )

                if flight['Carrier'] in ['AAL','ENY']:
                    CTOP_FLs.at[index,'Route_ID']      = Route_ID[i, 0]
                    CTOP_FLs.at[index,'Route_ID_New']  = Route_ID[i, j]

                CTOP_FLs.at[index, 'Route_ID_New_TOS'] = Route_ID[i,j]
                CTOP_FLs.at[index,'Extra Wind Miles']  = Q[i,j]

    Condition =  ( CTOP_FLs['AFIX'] != CTOP_FLs['AFIX_New'] )
    CTOP_FLs[ Condition ][['Carrier', 'ID', 'ORIG', 'Ref_Central_Time','ETD', 'AFIX', 'AFIX_New', 'EAFT', 'EAFT_New', 'Route_ID_New', 'Extra Wind Miles']]\
        .to_csv( Output_Dir + 'Reroute_Results.csv', index = False, date_format='%Y-%m-%d %H:%M:%S')

    print('-'*100)
    log.write( '-'*100 + '\n' )

    #for key, value in AFIX_Changes.iteritems():  #[(key, M[key]) for key in FCAs]
    for key, value in [(key, AFIX_Changes[key]) for key in list( permutations(FCAs, 2) ) ]:
        if value != 0:
            afix_change_info = "%3d flights reroute from %5s to %5s"
            print( afix_change_info % ( value, key[0], key[1] ) )
            log.write( afix_change_info % ( value, key[0], key[1] ) )
            log.write( "\n" )
    print( "Total Number of Rerouted Flights: %3d"% sum( AFIX_Changes.values() ) )
    log.write( "Total Number of Rerouted Flights: %3d\n"% sum( AFIX_Changes.values() ) )

    print('-'*100)
    log.write('-'*100 + '\n')

    fca_violation_count = 0
    for k in FCAs:
        for t in TIME:
            if prob.getSolution( E[k,t] ) != 0:
                capacity_info = "%2d FCA capacity violations at %5s at %5s"
                cross_time    = CTOP_START + timedelta( minutes = ( t - 1 ) * 15 )
                print( capacity_info % ( prob.getSolution( E[k,t] ), k, cross_time.strftime("%m-%d %H:%M") ) )
                log.write( capacity_info % ( prob.getSolution( E[k,t] ), k, cross_time.strftime("%m-%d %H:%M") ) )
                log.write( "\n" )

                fca_violation_count += prob.getSolution( E[k,t] )

    print("Total Number of FCA Capacity Violations: %3d" % fca_violation_count  )
    log.write("Total Number of FCA Capacity Violations: %3d\n" % fca_violation_count)

    """------------------------------------------------------------------------------------------------------------"""

    print('-' * 100)
    print('%3d flights cross four DFW corner post during CTOP planning horizon' % len( CTOP_FLs ) )
    print('%3d flights are OA flights, they are exempted'                       % sum( CTOP_FLs['Flight_Status'] == 'OA' ) )
    print('%3d flights are AA flights in total'                                 % (len( CTOP_FLs ) - sum( CTOP_FLs['Flight_Status'] == 'OA' )) )
    print('%3d AA flights have landed by the time of running this fix balancing program'         % sum( CTOP_FLs['Flight_Status'] == 'Landed' ) )
    print('%3d AA flights have taken off by the time of running this fix balancing program'      % sum( CTOP_FLs['Flight_Status'] == 'En route' ) )
    print('%3d AA flights are exempted due to various reasons'                  % sum( CTOP_FLs['Flight_Status'] == 'Exempted' ) )

    potential_reroutable = sum( (CTOP_FLs['Flight_Status'] == 'Reroutable') | (CTOP_FLs['Flight_Status'] == 'AA No TOS') )
    print('%3d AA flights can be potentially rerouted if they have TOS set submitted'   % potential_reroutable )
    print('Among the above %3d AA flights, %3d actually have TOS sets and reroutable'   % (potential_reroutable, sum( CTOP_FLs['Flight_Status'] == 'Reroutable' )) )
    print('-' * 100)
    Summary = 'Summary: FCA Capacity Violation Can Decrease from %3d to %2d at the Cost of Extra %5.1f En Route Miles'
    print( Summary % ( Vio_Num, fca_violation_count, sum(Q[i, j] * prob.getSolution( delta[i, j] ) for (i,j) in delta.keys() ) ) )
    print('-' * 100)

    log.write('-' * 100 + "\n" )
    log.write( '%3d Flights cross four DFW corner post during CTOP planning horizon\n' % len( CTOP_FLs )  )
    log.write( '%3d Flights are OA flights, they are exempted\n'                       % sum( CTOP_FLs['Flight_Status'] == 'OA' ) )
    log.write( '%3d Flights are AA flights in total\n'                                 % (len( CTOP_FLs ) - sum( CTOP_FLs['Flight_Status'] == 'OA' )) )
    log.write( '%3d AA Flights have landed by the time of running this fix balancing program\n'         % sum( CTOP_FLs['Flight_Status'] == 'Landed' ) )
    log.write( '%3d AA Flights have taken off by the time of running this fix balancing program\n'      % sum( CTOP_FLs['Flight_Status'] == 'En route' ) )
    log.write( '%3d AA Flights are exempted due to various reasons\n'                  % sum( CTOP_FLs['Flight_Status'] == 'Exempted' ) )

    log.write('%3d AA Flights can be potentially rerouted if they have TOS set submitted\n'   % potential_reroutable )
    log.write('Among the above %3d AA Flights, %3d actually have TOS sets and reroutable\n'   % (potential_reroutable, sum( CTOP_FLs['Flight_Status'] == 'Reroutable' )) )
    log.write('-' * 100 + '\n')
    log.write( Summary % ( Vio_Num, fca_violation_count, sum(Q[i, j] * prob.getSolution( delta[i, j] ) for (i,j) in delta.keys() ) ) )
    log.write("\n")
    log.write('-' * 100 + '\n')
    """------------------------------------------------------------------------------------------------------------"""
    # fig, ax         = plt.subplots()
    # sns.distplot( Reroute_cost, kde=False)
    # ax.set_xlabel( ' Extra Miles ' )
    # ax.set_ylabel( ' Flight Counts ' )
    # ax.set_title( 'Histogram of Extra Miles' )
    # ax.hist( Reroute_cost )
    # plt.show()

    # for FCA in FCAs:
    #     # Demand_By_FCA_Interval( CTOP_FLs, Bin, Current_Time, FCA , Solved = True)
    #     Demand_By_FCA_Interval_Flight_Status(CTOP_FLs, Bin, Current_Time, FCA, Solved = True)

    log.close()
    return CTOP_FLs

def Generate_OneLineTOS_For_Submission( CTOP_FLs, TOS ):
    """
    This function generate one line TOS file which can be directed read by CTOP platform
    """
    CTOP_FLs = pd.concat( [CTOP_FLs, pd.DataFrame( columns=['miles', 'Wind Miles', 'route_string'])], sort=False, axis = 1 )

    # Only file one line TOS for flights which have changed the arrival fixes
    Condition = (CTOP_FLs['AFIX'] != CTOP_FLs['AFIX_New'])
    for index, reroute_fl in CTOP_FLs[Condition].iterrows():
        carrier  = reroute_fl['Carrier']
        ORIG     = reroute_fl['ORIG']
        route_id = reroute_fl['Route_ID_New_TOS']

        Condition = ( TOS['airline_code'] == carrier ) & ( TOS['departure_station'] == ORIG ) & ( TOS['route_id_in_FOS'] == route_id )
        CTOP_FLs.at[index, 'miles']        = TOS[ Condition ].iloc[0]['miles']
        CTOP_FLs.at[index, 'Wind Miles']   = TOS[ Condition ].iloc[0]['Wind Miles']
        CTOP_FLs.at[index, 'route_string'] = TOS[ Condition ].iloc[0]['route']

    # df.rename(columns={'oldName1': 'newName1', 'oldName2': 'newName2'}, inplace=True)
    Condition = (CTOP_FLs['AFIX'] != CTOP_FLs['AFIX_New'])
    TOS_For_Submission = CTOP_FLs[ Condition ][ ['Carrier', 'ORIG', 'DEST', 'Route_ID_New_TOS', 'miles', 'Wind Miles', 'route_string' ] ]
    TOS_For_Submission.rename( columns = {'Carrier':'airline_code', 'ORIG':'departure_station', 'DEST':'arrival_station',
                                          'Route_ID_New_TOS':'route_id_in_FOS', 'route_string':'route_string(excluding departure and arrival stations)'},
                               inplace = True)
    TOS_For_Submission.reset_index( inplace = True, drop = True )
    TOS_For_Submission.index += 1
    TOS_For_Submission.to_csv( Output_Dir + 'Oneline_TOS.csv', index = True, index_label = "id")

    return TOS_For_Submission

def Visualize_FCAInfo( CTOP_FLs, Bin, Current_Time, FCA ):
    """
    """
    OAFLs = CTOP_FLs[CTOP_FLs['Flight_Status'] == 'OA']
    OA    = {} # dictionary, datetime: count
    AA    = {} #
    for fca in FCAs: AA[fca] = {}
    i     = 0

    """ Get the number of AA and OA flights by each time period """
    while True:
        Condition = ( OAFLs['EAFT'] >= CTOP_START + timedelta( minutes = i * Bin) ) & \
                    ( OAFLs['EAFT'] <  CTOP_START + timedelta( minutes = (i + 1) * Bin) ) & \
                    ( OAFLs['AFIX'] == FCA )
        OA[CTOP_START + timedelta( minutes=i * Bin )] = len( OAFLs[Condition] )

        for fca in FCAs:
            Condition = ( CTOP_FLs['EAFT'] >= CTOP_START + timedelta(minutes = i * Bin) ) & \
                        ( CTOP_FLs['EAFT'] < CTOP_START  + timedelta(minutes = (i + 1) * Bin) ) & \
                        ( CTOP_FLs['AFIX'] == FCA) & ( CTOP_FLs['AFIX_New'] == fca ) & \
                        ( CTOP_FLs['Flight_Status'] != 'OA' )

            AA[ fca ][ CTOP_START + timedelta( minutes=i * Bin ) ] = len( CTOP_FLs[Condition] )

        if CTOP_START + timedelta(minutes=(i + 1) * Bin) > CTOP_END:
            break

        i += 1

    Counts          = {} #key OA, FCA, reroute to other FCAs
    rects           = {}
    Categories      = ['OA'] + [ FCA ] + [ fca for fca in FCAs if fca!= FCA ]
    Options         = ['OA']
    Colors          = dict( zip( FCAs, ['b','cyan','magenta','y'] ) )
    Times           = zip( *sorted(OA.items()) )[0]
    Counts['OA']    = np.array( zip( *sorted( OA.items() ) )[1] ) #turn the key values into a list

    for category in Categories[1:]:
        count_list = np.array( zip( *sorted( AA[ category ].items() ) )[1] )
        if ~ np.all( count_list == 0 ):
            Counts[category] = count_list
            Options.append( category )

    fig, ax         = plt.subplots()
    ind             = np.arange( len( OA.keys() ) )

    for option in Options:
        if option == 'OA':
            rects[option] = ax.bar(ind, Counts[option], bottom = CalBottomValue(option, ind, Options, Counts), color='grey')
        elif option == FCA:
            rects[option] = ax.bar(ind, Counts[option], bottom = CalBottomValue(option, ind, Options, Counts), color='green')
        else:
            rects[ option ] = ax.bar( ind, Counts[ option ], bottom = CalBottomValue( option, ind, Options, Counts ), color = Colors[option] )

    ind_p, cap_p  = np.insert( ind * 1.0, 0 ,-1 ), np.insert( Capacity[FCA], 0, Capacity[FCA][0] )
    ind_p, cap_p  = np.append( ind_p , ind_p[-1] + 1 ), np.append( cap_p, Capacity[FCA][-1] )
    rate_line,    = ax.plot( ind_p, cap_p, linestyle='dashed' )

    y_max = max( sum( Counts.values() ).max() + 1, max( cap_p ) + 1 )
    ax.set_yticks( range( 0, y_max  ) )

    ax.set_xticks( ind )
    ax.set_xticklabels( [ interval.strftime("%H:%M") for interval in Times], rotation='vertical')
    #plt.grid() #

    # ax.legend( [ rects[ option ][0] for option in Options[2:] ] + [rate_line], Options[2:] + ['FCA Rate'] )
    ax.legend( [rects[option][0] for option in Options[1:]], ['Non-rerouted AA Demand'] + Options[2:]  )
    ax.set_title( FCA + Space + FCAs_Info[FCA] + Space + \
                 Current_Time.strftime("%B %d %H:%M:%S") + Space  + "Reroute Info" )
    ax.set_ylabel('Num of Inbound Flights per ' + str(Bin) + ' Mins')

def Visualize_FCAInfo_Flight_Status( CTOP_FLs, Bin, Current_Time, FCA, ax = None, Show_ylabel = True ):
    """
    1 Similar to Demand_By_FCA_Interval_Flight_Status function, this function also differentiate OA with AA, and also AA flights with different status
    2 The difference is that we further differentiate AA reroutables into flights originally scheduled to land at a time period
      with flights which will rerouted to other arrival fixes
    """
    OAFLs = CTOP_FLs[CTOP_FLs['Flight_Status'] == 'OA']
    OA    = {} # dictionary, datetime: count
    AA    = {} #
    for fca in FCAs: AA[fca] = {}
    AA['Landed'], AA['En route'], AA['Exempted'], AA['AA No TOS'] = {}, {}, {}, {}
    Status_List = ['OA', 'Landed', 'En route', 'Exempted', 'AA No TOS']
    i  = 0

    """ Get the number of AA and OA flights by each time period """
    while True:
        Condition = ( OAFLs['EAFT'] >= CTOP_START + timedelta( minutes = i * Bin) ) & \
                    ( OAFLs['EAFT'] <  CTOP_START + timedelta( minutes = (i + 1) * Bin) ) & \
                    ( OAFLs['AFIX'] == FCA )
        OA[CTOP_START + timedelta( minutes=i * Bin )] = len( OAFLs[Condition] )

        for fca in FCAs:
            Condition = ( CTOP_FLs['EAFT'] >= CTOP_START + timedelta(minutes = i * Bin) ) & \
                        ( CTOP_FLs['EAFT'] < CTOP_START  + timedelta(minutes = (i + 1) * Bin) ) & \
                        ( CTOP_FLs['AFIX'] == FCA) & ( CTOP_FLs['AFIX_New'] == fca ) & \
                        ( CTOP_FLs['Flight_Status'] == 'Reroutable' )

            #Here it shows the reroute information at fca "FCA"
            AA[ fca ][ CTOP_START + timedelta( minutes=i * Bin ) ] = len( CTOP_FLs[Condition] )

        #For landed, En route, Exempted and AA No TOS, EAFT_New and AFIX_New are the same as the old
        Condition = ( CTOP_FLs['EAFT_New'] >= CTOP_START + timedelta( minutes = i * Bin) ) & \
                    ( CTOP_FLs['EAFT_New'] <  CTOP_START + timedelta( minutes = (i + 1) * Bin) ) & \
                    ( CTOP_FLs['AFIX_New'] == FCA )

        AA[ 'Landed'    ][ CTOP_START + timedelta( minutes=i * Bin )] = len( CTOP_FLs[Condition & ( CTOP_FLs['Flight_Status'] == 'Landed'   )])
        AA[ 'En route'  ][ CTOP_START + timedelta( minutes=i * Bin )] = len( CTOP_FLs[Condition & ( CTOP_FLs['Flight_Status'] == 'En route' )])
        AA[ 'Exempted'  ][ CTOP_START + timedelta( minutes=i * Bin )] = len( CTOP_FLs[Condition & ( CTOP_FLs['Flight_Status'] == 'Exempted' )])
        AA[ 'AA No TOS' ][ CTOP_START + timedelta( minutes=i * Bin )] = len( CTOP_FLs[Condition & ( CTOP_FLs['Flight_Status'] == 'AA No TOS' )])

        if CTOP_START + timedelta( minutes=(i + 1) * Bin ) > CTOP_END:
            break

        i += 1

    Counts          = {}
    rects           = {}
    Status_List     = Status_List + [ FCA ] + [ fca for fca in FCAs if fca!= FCA ]
    Options         = []
    Colors_List     = ['grey', 'black', 'red', 'orange', 'plum', 'g','cyan','magenta','y','lightcoral','darkcyan','deeppink']
    Colors          = dict( zip( Status_List, Colors_List[0: len( Status_List )]  ) )
    Times           = zip( *sorted(OA.items()) )[0]

    """If there is no flight belongs to a category, then there will be no legend for that category"""
    for category in Status_List:
        if category == 'OA':
            count_list = np.array( zip( *sorted( OA.items() ) )[1] )
        else:
            count_list = np.array( zip( *sorted( AA[ category ].items() ) )[1] )
        if ~ np.all( count_list == 0 ):
            Counts[category] = count_list
            Options.append( category )

    if None == ax:
        fig, ax         = plt.subplots()
    ind             = np.arange( len( OA.keys() ) )

    for option in Options:
        rects[option] = ax.bar(ind, Counts[option], bottom=CalBottomValue(option, ind, Options, Counts), color=Colors[option])

    ind_p, cap_p  = np.insert( ind * 1.0, 0 ,-1 ), np.insert( Capacity[FCA], 0, Capacity[FCA][0] )
    ind_p, cap_p  = np.append( ind_p , ind_p[-1] + 1 ), np.append( cap_p, Capacity[FCA][-1] )
    rate_line,    = ax.plot( ind_p, cap_p, linestyle='dashed' )

    y_max = max( sum( Counts.values() ).max() + 1, max( cap_p ) + 1 )
    ax.set_yticks( range( 0, y_max  ) )

    ax.set_xticks( ind )
    ax.set_xticklabels( [ interval.strftime("%H:%M") for interval in Times], rotation='vertical')
    #plt.grid() #

    # ax.legend( [ rects[ option ][0] for option in Options[2:] ] + [rate_line], Options[2:] + ['FCA Rate'] )
    ax.legend( [rects[option][0] for option in Options], Options  )
    ax.set_title( FCA + Space + FCAs_Info[FCA] + Space + \
                 Current_Time.strftime("%B %d %H:%M:%S") + Space  + "Reroute Info" )

    if Show_ylabel:
        ax.set_ylabel('Num of Inbound Flights per ' + str(Bin) + ' Mins')

def Visualize_RerouteInfo_Single_Window( CTOP_FLs, Current_Time ):
    Bin = 15
    for FCA in FCAs:
        # Visualize_FCAInfo( CTOP_FLs, Bin, Current_Time, FCA )
        Visualize_FCAInfo_Flight_Status( CTOP_FLs, Bin, Current_Time, FCA )
    
def Visualize_RerouteInfo( CTOP_FLs, Current_Time ):
    """
    Very similar to Demand_Capacity function, this function shows the reroute information for each FCA
    """

    if 'DFW' == Airport:
        f, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize = Fig_Size )
        plt.tight_layout(pad=2.0, w_pad=0.5, h_pad=3.5)

        Visualize_FCAInfo_Flight_Status(CTOP_FLs, Bin, Current_Time, 'BRDJE', ax=ax2, Show_ylabel = False )
        Visualize_FCAInfo_Flight_Status(CTOP_FLs, Bin, Current_Time, 'VKTRY', ax=ax1 )
        Visualize_FCAInfo_Flight_Status(CTOP_FLs, Bin, Current_Time, 'BOOVE', ax=ax3 )
        Visualize_FCAInfo_Flight_Status(CTOP_FLs, Bin, Current_Time, 'BEREE', ax=ax4, Show_ylabel = False )
    elif 'CLT' == Airport:
        f, ((ax1, ax2, ax3, ax4), (ax5, ax6, ax7, ax8)) = plt.subplots(2, 4, figsize=Fig_Size)
        plt.tight_layout(pad=2.0, w_pad=1, h_pad=3.5)

        Visualize_FCAInfo_Flight_Status(CTOP_FLs, Bin, Current_Time, 'FILPZ', ax=ax1)
        Visualize_FCAInfo_Flight_Status(CTOP_FLs, Bin, Current_Time, 'PARQR', ax=ax2, Show_ylabel=False)
        Visualize_FCAInfo_Flight_Status(CTOP_FLs, Bin, Current_Time, 'CHSLY', ax=ax3, Show_ylabel=False)

        ax4.set_visible(False)

        Visualize_FCAInfo_Flight_Status(CTOP_FLs, Bin, Current_Time, 'JONZE', ax=ax5)
        Visualize_FCAInfo_Flight_Status(CTOP_FLs, Bin, Current_Time, 'BANKR', ax=ax6, Show_ylabel=False)
        Visualize_FCAInfo_Flight_Status(CTOP_FLs, Bin, Current_Time, 'STOCR', ax=ax7, Show_ylabel=False)
        Visualize_FCAInfo_Flight_Status(CTOP_FLs, Bin, Current_Time, 'MLLET', ax=ax8, Show_ylabel=False)

    plt.savefig( Output_Dir + 'Reroute Info at ' + Current_Time.strftime("%B %d %H_%M_%S") + Space + ".png" )