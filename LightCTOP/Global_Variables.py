# -*- coding: utf-8 -*-
"""
Created on Mon May 07 17:02:51 2018

@author: Guodong

1. Each time we run, we need to
   a) choose turn on or turn off HAND_TYPED mode
   b) specify the ADL file and TOS file
   c) specify the CTOP time window
   d) specify the output directory
   e) specify the exempted markets, flights,
2. for each new airport/airport flow configuration, we can create a new folder to store the result
3. This piece of code can also be used to analyze new schedules
"""

from datetime import datetime, timedelta
import numpy as np
import xlrd
import re
import pandas as pd
#Make sure the current time and CTOP time is compatible

Bin           = 15
ReferenceTime = 90 #Mins
Space         = ' '

ADL_Folder    = "Data\\ADL_Files\\"
TOS_Folder    = "Data\\"

NON_ENY        = ['ASH', 'ASQ', 'SKW']
CruiseSpeed    = {'B773':557, 'B772':557, 'B789':563, 'B763':540, 'B757':530, 'A321':524, 'B737':524, 'MD80':504, 'A319':520,
                  'A333':544, 'A332':544, 'A320':520, 'E190':520, 'CRJ9':517, 'CRJ7':510, 'CRJ2':497
                 }
Fig_Size       = (16, 9)  #(16, 9) #(10, 7.5)
#%%
HAND_TYPED     = False #True

if HAND_TYPED:
    Airport = 'DFW'  # 'DFW' 'CLT'
    AirportFlow = 'South'

    if 'DFW' == Airport and 'South' == AirportFlow:
        FCAs = ['BRDJE', 'VKTRY', 'BOOVE', 'BEREE']
        FCAs_Info = {'BRDJE': 'NE', 'VKTRY': 'NW', 'BOOVE': 'SW', 'BEREE': 'SE'}
                          #need to be in the lower case
        AFIXs = {'BRDJE': ['brdje3', 'caine2', 'dawgz2', 'fingr5', 'seevr4', 'wilbr4', 'seevr3'],  # FCA1  NE  BRDJE
                 'VKTRY': ['bowie4', 'gibbi2', 'jovem4', 'shaam2', 'ukw4', 'vktry2'],  # FCA2  NW  VKTRY
                 'BOOVE': ['boove4', 'jen1', 'pawlz3', 'sockk3', 'tilla3'],  # FCA3  SW  BOOVE
                 'BEREE': ['beree1', 'cabby2', 'cq8', 'cqy8', 'forny2', 'whiny4', 'yeagr3']  # FCA4  SE  BEREE
                 }
        Output_Dir = "Data\\Model_Output_DFW_South\\"
        #Output_Dir = "Data\\Model_Output_DFW_New_Schedule\\"
        Report_File = Output_Dir + "Model_Print.txt"

        ADLFile = ADL_Folder + "dfw__.lcdm.15175521.01.all.gamf"
        ADLFile = ADL_Folder + "dfw__.lcdm.11102207.01.all.gamf"
        ADLFile = ADL_Folder + "dfw__.lcdm.16100859.01.all.gamf"
        TOSFile = TOS_Folder + "cannedrouteexport. 20180606_1707.csv"
        CTOP_START = datetime(2018, 7, 11, 21, 0, 0)  # Don't forget to change date  #0615
        CTOP_END   = datetime(2018, 7, 12, 1, 59, 59)

        CTOP_START = datetime(2018, 7, 16, 10, 0, 0)  # Don't forget to change date  #0615
        CTOP_END   = datetime(2018, 7, 16, 19, 59, 59)

        log = open(Report_File, "w")
        log.close()

    elif 'DFW' == Airport and 'North' == AirportFlow:
        FCAs      = ['BRDJE', 'JOVEM', 'SOCKK', 'WHINY']
        FCAs_Info = {'BRDJE': 'NE', 'JOVEM': 'NW', 'SOCKK': 'SW', 'WHINY': 'SE'}

        AFIXs = {'BRDJE': ['brdje3'],  # FCA1  NE  BRDJE
                 'JOVEM': ['jovem4'],  # FCA2  NW  VKTRY
                 'SOCKK': ['sockk3'],  # FCA3  SW  BOOVE
                 'WHINY': ['whiny4']  # FCA4  SE  BEREE
                 }
        Output_Dir = "Data\\Model_Output_DFW_North\\"
        Report_File = Output_Dir + "Model_Print.txt"

        ADLFile = ADL_Folder + "dfw__.lcdm.16100859.01.all.gamf"
        TOSFile = TOS_Folder + "canned_route_raw_data_dfw_northflow_04262018.csv"

        CTOP_START = datetime(2018, 7, 10, 10, 0, 0)  # Don't forget to change date  #0615
        CTOP_END   = datetime(2018, 7, 10, 19, 59, 59)

        log = open(Report_File, "w")
        log.close()

    elif 'CLT' == Airport:
        FCAs = ['CHSLY', 'PARQR', 'FILPZ', 'JONZE', 'BANKR', 'STOCR', 'MLLET']
        FCAs_Info = {'CHSLY': 'NE', 'PARQR': 'N', 'FILPZ': 'NW', 'JONZE': 'SWW', 'BANKR': 'SW', 'STOCR': 'SE',
                     'MLLET': 'SEE'}

        AFIXs = {'CHSLY': ['chsly3'],  # FCA1  NE  BRDJE
                 'PARQR': ['parqr3'],  # FCA2  NW  VKTRY
                 'FILPZ': ['filpz3'],  # FCA3  SW  BOOVE
                 'JONZE': ['jonze2', 'jonze1'],  # FCA4  SE  BEREE
                 'BANKR': [],
                 'STOCR': ['stocr2'],
                 'MLLET': ['mllet2']
                 }

        Output_Dir = "Data\\Model_Output_CLT_South\\"
        Report_File = Output_Dir + "Model_Print.txt"

        ADLFile       = ADL_Folder + "clt__.lcdm.19091836.01.all.gamf"
        TOSFile       = TOS_Folder + "CLT CTOP Routes Final V 0 1.csv"
        CTOP_START                 = datetime(2018, 7, 19, 21,  0,  0)    #Don't forget to change date
        CTOP_END                   = datetime(2018, 7, 20,  1, 59, 59)

        log = open(Report_File, "w")
        log.close()
    # ADLFile       = ADL_Folder + "dfw__.lcdm.15193521.01.all.gamf"
    # ADLFile       = ADL_Folder + Retrieve_ADL_File( ADL_Folder )

    Time_Periods               = ( CTOP_END + timedelta( seconds = 1 ) - CTOP_START ).seconds/(60*15)
    TIME                       = range( 1, Time_Periods + 1 )
    ExemptTime                 = timedelta( minutes = 45 )  # timedelta( hours = 1 )
    ExtraMileMax               = 100
    Vio_Penalty                = 500 #Miles
    ExtraMileMax_Sensitivity   = [0, 50, 100, 150, 200, 300] #[50, 100, 150, 200]

    if 'DFW' == Airport and 'South' == AirportFlow:
        """In a good weather day, the nomimal acceptance rates for NE and NW are 10 and 9 """
        Capacity     = {'BRDJE':[10]*Time_Periods,   #FCA1  NE  BRDJE
                        'VKTRY':[9]*Time_Periods,   #FCA2  NW  VKTRY
                        'BOOVE':[8]*Time_Periods,  #FCA3  SW  BOOVE
                        'BEREE':[8]*Time_Periods } #FCA4  SE  BEREE
    elif 'DFW' == Airport and 'North' == AirportFlow:
        Capacity     = {'BRDJE':[8]*Time_Periods,   #FCA1  NE  BRDJE
                        'JOVEM':[8]*Time_Periods,   #FCA2  NW  VKTRY
                        'SOCKK':[9]*Time_Periods,  #FCA3  SW  BOOVE
                        'WHINY':[10]*Time_Periods } #FCA4  SE  BEREE
    elif 'CLT' == Airport:
        """Run way capacity is 23 per 15 time periods, 92 per hour"""
        Capacity = {'CHSLY': [5] * Time_Periods,  #NE
                    'PARQR': [4] * Time_Periods,  #N
                    'FILPZ': [4] * Time_Periods,  #NW
                    'JONZE': [3] * Time_Periods,  #SWW
                    'BANKR': [2] * Time_Periods,  #SW
                    'STOCR': [3] * Time_Periods,  #SE
                    'MLLET': [2] * Time_Periods   #SEE
                    }
    elif 'PHX' == Airport:
        pass

    # Exemption criteria
    # 1. exempt certain airports/markets
    # 2. exempt certain subcarrier AA_Keywords  = ['ENY', 'AAL', 'ASH', 'ASQ', 'SKW']
    # 3. exempt certain flights

    EXPT   = {'Airports'   :[], #e.g. ['PHX', 'LAX']
              'Subcarriers':[], #e.g. ['ENY','ASH']
              'FLT_List'   :[]  #e.g. ['AAL1071']
             }
else:
    CTOP_Parameters_File = "LightCTOP_Model_Config.xlsx"
    Book         = xlrd.open_workbook( CTOP_Parameters_File )

    Config       = Book.sheet_by_name("MODEL")
    AirportFlow = Config.cell_value( rowx = 3, colx = 1 )
    ADLFile      = Config.cell_value( rowx = 5, colx = 1 )
    TOSFile      = Config.cell_value( rowx = 6, colx = 1 )
    Output_Dir   = Config.cell_value( rowx = 7, colx = 1 )
    Report_File  = Output_Dir + "Model_Print.txt"

    log = open(Report_File, "w")
    log.close()

    ExtraMileMax               = Config.cell_value( rowx = 11, colx = 1 )
    ExtraMileMax_Sensitivity   = []
    Vio_Penalty                = Config.cell_value( rowx = 13, colx = 1 )

    column = 1
    while 0 != Config.cell_type( rowx = 12, colx = column ):
        ExtraMileMax_Sensitivity.append( Config.cell_value( rowx = 12, colx = column  ) )
        column = column + 1

    if 'DFW South Flow' == AirportFlow:
        Airport   = 'DFW'
        DFW       = Book.sheet_by_name("DFW South Flow")

        FCAs      = ['BRDJE', 'VKTRY', 'BOOVE', 'BEREE']
        FCAs_Info = {'BRDJE': 'NE', 'VKTRY': 'NW', 'BOOVE': 'SW', 'BEREE': 'SE'}

        AFIXs = {'BRDJE': ['brdje3', 'caine2', 'dawgz2', 'fingr5', 'seevr4', 'wilbr4', 'seevr3'],  # FCA1  NE  BRDJE
                 'VKTRY': ['bowie4', 'gibbi2', 'jovem4', 'shaam2', 'ukw4', 'vktry2'],  # FCA2  NW  VKTRY
                 'BOOVE': ['boove4', 'jen1', 'pawlz3', 'sockk3', 'tilla3'],  # FCA3  SW  BOOVE
                 'BEREE': ['beree1', 'cabby2', 'cq8', 'cqy8', 'forny2', 'whiny4', 'yeagr3']  # FCA4  SE  BEREE
                 }
    if 'DFW North Flow' == AirportFlow:
        Airport      = 'DFW'
        DFW          = Book.sheet_by_name("DFW North Flow")

        FCAs      = ['BRDJE', 'VKTRY', 'BOOVE', 'BEREE']
        FCAs_Info = {'BRDJE': 'NE', 'VKTRY': 'NW', 'BOOVE': 'SW', 'BEREE': 'SE'}

        AFIXs = {'BRDJE': ['brdje3', 'caine2', 'dawgz2', 'fingr5', 'seevr4', 'wilbr4', 'seevr3'],  # FCA1  NE  BRDJE
                 'VKTRY': ['bowie4', 'gibbi2', 'jovem4', 'shaam2', 'ukw4', 'vktry2'],  # FCA2  NW  VKTRY
                 'BOOVE': ['boove4', 'jen1', 'pawlz3', 'sockk3', 'tilla3'],  # FCA3  SW  BOOVE
                 'BEREE': ['beree1', 'cabby2', 'cq8', 'cqy8', 'forny2', 'whiny4', 'yeagr3']  # FCA4  SE  BEREE
                 }
    if 'DFW' in AirportFlow:
        CTOP_START   = DFW.cell_value( rowx = 3, colx = 2 )
        CTOP_START   = datetime.strptime(CTOP_START, '%m/%d/%Y %H:%M')
        CTOP_END     = DFW.cell_value( rowx = 3 , colx = 3 )
        CTOP_END     = datetime.strptime(CTOP_END, '%m/%d/%Y %H:%M') + timedelta(seconds=59)

        Time_Periods = (CTOP_END + timedelta(seconds=1) - CTOP_START).seconds / (60 * 15)
        TIME         = range(1, int(Time_Periods) + 1)

        ExemptTime   = DFW.cell_value(rowx=8, colx=6)
        ExemptTime   = timedelta( minutes = ExemptTime )  # timedelta( hours = 1 )

        Capacity = {}
        for (fca, col) in zip(FCAs, [1, 2, 3, 4]):
            capacity_list = DFW.col_slice(colx=col, start_rowx=8, end_rowx=8 + int(Time_Periods))
            Capacity[fca] = [int(x.value) for x in capacity_list]

        EXPT = {'Airports'   : [],
                'Subcarriers': [],
                'FLT_List'   : [] }
        Categories = ['Airports', 'Subcarriers', 'FLT_List']

        for (category, col) in zip(Categories, [7, 8, 9]):
            count = 0
            while ( 0 != DFW.cell_type( rowx = 8 + count, colx = col ) ):
                EXPT[ category ].append( DFW.cell_value( rowx = 8 + count, colx=col ) )
                count += 1

    elif 'CLT South Flow' == AirportFlow:
        Airport = 'CLT'

        CLT = Book.sheet_by_name("CLT South Flow")

        FCAs = ['CHSLY', 'PARQR', 'FILPZ', 'JONZE', 'BANKR', 'STOCR', 'MLLET']
        FCAs_Info = {'CHSLY': 'NE', 'PARQR': 'N', 'FILPZ': 'NW', 'JONZE': 'SWW', 'BANKR': 'SW', 'STOCR': 'SE',
                     'MLLET': 'SEE'}

        AFIXs = {'CHSLY': ['chsly3'],  # FCA1  NE  BRDJE
                 'PARQR': ['parqr3'],  # FCA2  NW  VKTRY
                 'FILPZ': ['filpz3'],  # FCA3  SW  BOOVE
                 'JONZE': ['jonze2', 'jonze1'],  # FCA4  SE  BEREE
                 'BANKR': [],
                 'STOCR': ['stocr2'],
                 'MLLET': ['mllet2']
                 }

        CTOP_START   = CLT.cell_value( rowx = 3, colx = 2 )
        CTOP_START   = datetime.strptime(CTOP_START, '%m/%d/%Y %H:%M')
        CTOP_END     = CLT.cell_value( rowx = 3 , colx = 3 )
        CTOP_END     = datetime.strptime(CTOP_END, '%m/%d/%Y %H:%M') + timedelta(seconds=59)

        Time_Periods = (CTOP_END + timedelta(seconds=1) - CTOP_START).seconds / (60 * 15)
        TIME         = range(1, Time_Periods + 1)

        ExemptTime   = CLT.cell_value(rowx=8, colx=9)
        ExemptTime   = timedelta( minutes = ExemptTime )  # timedelta( hours = 1 )

        Capacity = {}
        for (fca, col) in zip(FCAs, [1, 2, 3, 4, 5, 6, 7]):
            capacity_list = CLT.col_slice(colx=col, start_rowx=8, end_rowx=8 + Time_Periods)
            Capacity[fca] = [int(x.value) for x in capacity_list]

        EXPT = {'Airports'   : [],
                'Subcarriers': [],
                'FLT_List'   : [] }
        Categories = ['Airports', 'Subcarriers', 'FLT_List']

        for (category, col) in zip(Categories, [10, 11, 12]):
            count = 0
            while ( 0 != CLT.cell_type( rowx = 8 + count, colx = col ) ):
                EXPT[ category ].append( CLT.cell_value( rowx = 8 + count, colx=col ) )
                count += 1

#%%
def Slots( M ):
    Sum = 0
    for key, value in M.items():
        Sum += sum( value )
        
    return Sum

def CalBottomValue( option, ind, Options, Counts ):
    Bottom = np.zeros( len(ind)  )

    for fca in Options[0: Options.index( option )]:
        Bottom = Bottom + np.array( Counts[ fca ] )

    return Bottom

def Cruise_Speed( TYPE ):
    if TYPE in CruiseSpeed.keys():
        cruise_speed = CruiseSpeed[TYPE] * 1.0
    else:
        cruise_speed = 500.0

    return cruise_speed

def carrier_info(x):
    if x.isalpha():
        return x
    else:
        return x.split(x[re.search("\d", x).start()], 1)[0]

def id_info(x):
    #keep the delimiter

    if x.isalpha():
        return ""
    else:
        return x[re.search("\d", x).start()] + x.split(x[re.search("\d", x).start()], 1)[1]

