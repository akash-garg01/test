# -*- coding: utf-8 -*-
"""
Created on Sun May 06 20:46:36 2018

@author: Guodong

https://stackoverflow.com/questions/3869487/how-do-i-create-a-dictionary-with-keys-from-a-list-and-values-defaulting-to-say
https://matplotlib.org/examples/pylab_examples/subplots_demo.html
"""

from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
sns.set(color_codes=True)
from Global_Variables import *
import pickle

def Demand_By_FCA_Interval( CTOP_FLs, Bin, Current_Time, FCA, Solved = False):
    """
    1 The key point is that we will focus on FCA one by one
    2 This function just differentiate flights operated by AA and OA. There is no additional information like en route, etc.
    3 Color coding is as follows:
      grey exempted, OA flights
      black landed, both OA and AA
      red, enroute
    """
    AAFLs = CTOP_FLs[CTOP_FLs['Flight_Status'] != 'OA']
    OAFLs = CTOP_FLs[CTOP_FLs['Flight_Status'] == 'OA']

    AA, OA       = {}, {} # dictionary, datetime: count
    i            = 0 
    
    while True:
        """"""
        for dic, pd in zip( [AA, OA], [ AAFLs, OAFLs] ):
            if Solved == False or len( pd ) == len( OAFLs ):
                Condition = ( pd['EAFT'] >= CTOP_START + timedelta( minutes = i * Bin ) ) & \
                            ( pd['EAFT'] <  CTOP_START + timedelta( minutes = (i+1) * Bin ) ) & \
                            ( pd['AFIX'] == FCA )
            else:
                Condition = ( pd['EAFT_New'] >= CTOP_START + timedelta( minutes = i * Bin ) ) & \
                ( pd['EAFT_New'] <  CTOP_START + timedelta( minutes = (i+1) * Bin ) ) & \
                ( pd['AFIX_New'] == FCA )

            dic[ CTOP_START + timedelta( minutes = i * Bin ) ] = len( pd[Condition] )
        
        if CTOP_START + timedelta( minutes = (i+1) * Bin ) > CTOP_END:
            break
        
        i += 1
    
    fig, ax         = plt.subplots()
    ind             = np.arange( len( AA.keys() ) )
    Times, AA_Count = zip( *sorted( AA.items( ) ) ) 
    OA_Count        = zip( *sorted( OA.items( ) ) )[1]
    
    rects1        = ax.bar( ind, OA_Count, color='grey')
    rects2        = ax.bar( ind, AA_Count, bottom = OA_Count, color = 'g' )

    #Plot the capacity information
    ind_p, cap_p  = np.insert( ind * 1.0, 0 ,-1 ), np.insert( Capacity[FCA], 0, Capacity[FCA][0] )
    ind_p, cap_p  = np.append( ind_p , ind_p[-1] + 1 ), np.append( cap_p, Capacity[FCA][-1] )
    rate_line,    = ax.plot( ind_p, cap_p, linestyle='dashed' )
    # rate_line,    = ax.plot( ind, Capacity[FCA], linestyle='dashed' )
    
    ax.set_xticks( ind )
    ax.set_xticklabels( [ interval.strftime("%H:%M") for interval in Times], rotation='vertical')
    #plt.grid() #+ 'Current Time ' 
    ax.legend( ( rects1[0], rects2[0], rate_line ), ('OA', 'AA', 'FCA Rate') )

    if False == Solved:
        SolvedInfo = "Before Optimization"
    else:
        SolvedInfo = "After Optimization"
    ax.set_title( FCA + Space + FCAs_Info[FCA] + Space + \
                     Current_Time.strftime("%B %d %H:%M:%S") + Space + SolvedInfo )
    ax.set_ylabel('Num of Inbound Flights per ' + str(Bin) + ' Mins')
    plt.show()   

def Demand_By_FCA_Interval_Flight_Status( CTOP_FLs, Bin, Current_Time, FCA , Solved = False, ax = None, Show_ylabel = True ):
    """
    1 This function shows more information about AA flights
    2 The color coding is as follows:
        grey exempted, OA flights
        black, landed
        red, enroute,
        orange, exempted (including current time is within 45 mins of scheduled departure time or select group)
        green, active/reroutable
    3 This function can display the information before Opt and after Opt. The difference is that to show results after Opt,
      we will need to use EAFT_New, etc
    """

    OAFLs       = CTOP_FLs[CTOP_FLs['Flight_Status'] == 'OA']
    OA, AA      = {}, {} # dictionary, datetime: count
    Status_List = ['OA', 'Landed', 'En route', 'Exempted', 'AA No TOS', 'Reroutable']
    AA['Landed'], AA['En route'], AA['Exempted'], AA['AA No TOS'], AA['Reroutable'] = {}, {}, {}, {}, {}

    i = 0

    while True:
        Condition = ( OAFLs['EAFT'] >= CTOP_START + timedelta( minutes = i * Bin) ) & \
                    ( OAFLs['EAFT'] < CTOP_START + timedelta( minutes = (i + 1) * Bin) ) & \
                    ( OAFLs['AFIX'] == FCA )
        OA[CTOP_START + timedelta( minutes=i * Bin )] = len( OAFLs[Condition] )

        if Solved == False:
            Condition = ( CTOP_FLs['EAFT'] >= CTOP_START + timedelta(minutes=i * Bin) ) & \
                        ( CTOP_FLs['EAFT'] < CTOP_START + timedelta(minutes=(i + 1) * Bin) ) & \
                        ( CTOP_FLs['AFIX'] == FCA)
        else:
            Condition = ( CTOP_FLs['EAFT_New'] >= CTOP_START + timedelta( minutes = i * Bin) ) & \
                        ( CTOP_FLs['EAFT_New'] <  CTOP_START + timedelta(  minutes = (i + 1) * Bin) ) & \
                        ( CTOP_FLs['AFIX_New'] == FCA)

        AA[ 'Landed'    ][ CTOP_START + timedelta( minutes=i * Bin )] = len( CTOP_FLs[Condition & ( CTOP_FLs['Flight_Status'] == 'Landed'   )])
        AA[ 'En route'  ][ CTOP_START + timedelta( minutes=i * Bin )] = len( CTOP_FLs[Condition & ( CTOP_FLs['Flight_Status'] == 'En route' )])
        AA[ 'Exempted'  ][ CTOP_START + timedelta( minutes=i * Bin )] = len( CTOP_FLs[Condition & ( CTOP_FLs['Flight_Status'] == 'Exempted' )])
        AA[ 'AA No TOS' ][ CTOP_START + timedelta( minutes=i * Bin )] = len( CTOP_FLs[Condition & ( CTOP_FLs['Flight_Status'] == 'AA No TOS' )])
        AA[ 'Reroutable'][ CTOP_START + timedelta( minutes=i * Bin )] = len( CTOP_FLs[Condition & ( CTOP_FLs['Flight_Status'] == 'Reroutable' )])

        if CTOP_START + timedelta(minutes=(i + 1) * Bin) > CTOP_END:
            break

        i += 1

    Counts          = {} #key OA, FCA, reroute to other FCAs
    rects           = {}
    Options         = []
    Colors = dict(zip(Status_List, ['grey', 'black', 'red', 'orange', 'plum', 'g']))
    Times           = zip(*sorted(OA.items()))[0]

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

    print(Counts)
    
    for option in Options:
        rects[ option ] = ax.bar( ind, Counts[ option ], bottom = CalBottomValue( option, ind, Options, Counts ), color = Colors[option] )

    # Plot the capacity information
    ind_p, cap_p = np.insert(ind * 1.0, 0, -1), np.insert(Capacity[FCA], 0, Capacity[FCA][0])
    ind_p, cap_p = np.append(ind_p, ind_p[-1] + 1), np.append(cap_p, Capacity[FCA][-1])
    rate_line, = ax.plot( ind_p, cap_p, linestyle='dashed' )
    # rate_line,    = ax.plot( ind, Capacity[FCA], linestyle='dashed' )

    file = open(Output_Dir + FCA + " capacity.txt","a") 
    for category in Status_List:        
        if category == 'OA':
            count_list1 = np.array( zip( *sorted( OA.items() ) )[1] )
        else:
            count_list1 = np.array( zip( *sorted( AA[ category ].items() ) )[1] )
        if ~ np.all( count_list1 == 0 ):
            file.write(category)
            for i in range(len(Counts[category])):
                file.write(str(Counts[category][i]))
                file.write(" ")
                
            file.write("\r\n")
            
    file.close() 
               
    y_max = max( sum( Counts.values() ).max() + 1, max( cap_p ) + 1 )
    ax.set_yticks( range( 0, y_max  ) )

    ax.set_xticks( ind )
    ax.set_xticklabels([interval.strftime("%H:%M") for interval in Times], rotation='vertical')

    # plt.grid() #+ 'Current Time '
    # ax.legend((rects1[0], rects2[0], rate_line), ('OA', 'AA', 'FCA Rate'))
    ax.legend( [ rects[ option ][0] for option in Options ] + [rate_line], Options + ['FCA Rate'] )
    # ax.set_title(FCA + Space + FCAs_Info[FCA] + Space + \
    #              Current_Time.strftime("%B %d %H:%M:%S") + Space + 'Solved=' + str(Solved))

    if False == Solved:
        SolvedInfo = "Before Opti" #"Before Optimization"
    else:
        SolvedInfo = "After Opti"  #"After Optimization"
    ax.set_title( FCA + Space + FCAs_Info[FCA] + Space + \
                     Current_Time.strftime("%B %d %H:%M:%S") + Space + SolvedInfo )

    if Show_ylabel:
        ax.set_ylabel('Num of Inbound Flights per ' + str(Bin) + ' Mins')
    #plt.show()

def Demand_Capacity( CTOP_FLs, Bin, Current_Time, Flight_Status = True, Solved = False):
    """
    This function create 2*2 or 2*4 plot by calling function that draws individual plot
    """
    if False == Flight_Status:
        pass
    else:
        if 'DFW' == Airport:
            f, ((ax1, ax2), (ax3, ax4)) = plt.subplots( 2, 2, figsize = Fig_Size )
            plt.tight_layout(pad=2.0, w_pad=0.5, h_pad=3.5)
            Demand_By_FCA_Interval_Flight_Status(CTOP_FLs, Bin, Current_Time, 'BRDJE', Solved, ax = ax2, Show_ylabel = False)
            Demand_By_FCA_Interval_Flight_Status(CTOP_FLs, Bin, Current_Time, 'VKTRY', Solved, ax = ax1)
            Demand_By_FCA_Interval_Flight_Status(CTOP_FLs, Bin, Current_Time, 'BOOVE', Solved, ax = ax3)
            Demand_By_FCA_Interval_Flight_Status(CTOP_FLs, Bin, Current_Time, 'BEREE', Solved, ax = ax4, Show_ylabel = False)
        elif 'CLT' == Airport:
            f, ((ax1, ax2, ax3, ax4 ), (ax5, ax6, ax7, ax8)) = plt.subplots( 2, 4, figsize = Fig_Size )
            plt.tight_layout(pad=2.0, w_pad=1, h_pad=3.5)

            Demand_By_FCA_Interval_Flight_Status(CTOP_FLs, Bin, Current_Time, 'FILPZ', Solved, ax = ax1 )
            Demand_By_FCA_Interval_Flight_Status(CTOP_FLs, Bin, Current_Time, 'PARQR', Solved, ax = ax2, Show_ylabel = False)
            Demand_By_FCA_Interval_Flight_Status(CTOP_FLs, Bin, Current_Time, 'CHSLY', Solved, ax = ax3, Show_ylabel = False)

            ax4.set_visible( False )

            Demand_By_FCA_Interval_Flight_Status(CTOP_FLs, Bin, Current_Time, 'JONZE', Solved, ax = ax5)
            Demand_By_FCA_Interval_Flight_Status(CTOP_FLs, Bin, Current_Time, 'BANKR', Solved, ax = ax6, Show_ylabel = False)
            Demand_By_FCA_Interval_Flight_Status(CTOP_FLs, Bin, Current_Time, 'STOCR', Solved, ax = ax7, Show_ylabel = False)
            Demand_By_FCA_Interval_Flight_Status(CTOP_FLs, Bin, Current_Time, 'MLLET', Solved, ax = ax8, Show_ylabel = False)

    #only used for the filename
    if False == Solved:
        SolvedInfo = "Before Optimization"
    else:
        SolvedInfo = "After Optimization"

    plt.savefig( Output_Dir + 'Demand Capacity Info at ' + Current_Time.strftime("%B %d %H_%M_%S") + Space + SolvedInfo + ".png" )

def Demand_Capacity_Single_Window(CTOP_FLs, Current_Time, Flight_Status = True, Solved = False):
    """
    This function will draw figures for each FCA by calling
    """
    for FCA in FCAs:
        if False == Flight_Status:
            Demand_By_FCA_Interval(CTOP_FLs, Bin, Current_Time, FCA, Solved )
        else:
            Demand_By_FCA_Interval_Flight_Status( CTOP_FLs, Bin, Current_Time, FCA, Solved  )


#%%
# For comparision with FSM
# Condition = ( pd['ETA'] >= CTOP_START + timedelta( minutes = i * Bin ) ) & \
#             ( pd['ETA'] <  CTOP_START + timedelta( minutes = (i+1) * Bin ) ) & \
#             ( pd['AFIX'] == FCA )