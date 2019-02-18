from Process_ADL import ReadADLFile, ProcessARVFlights, Retrieve_ADL_File, CheckingInputParameters
from Process_TOS import ReadTOSFile, PrepareInputLightCTOP
from Global_Variables import *
from datetime import datetime, timedelta

"""Compare the Difference Between Two Files"""

ADL_File1     = ADL_Folder + "dfw__.lcdm.15194521.01.all.gamf"
ADL_File2     = ADL_Folder + "dfw__.lcdm.15201520.01.all.gamf"

# ADL_File1     = ADL_Folder + "dfw__.lcdm.15201520.01.all.gamf"
# ADL_File2     = ADL_Folder + "dfw__.lcdm.15204521.01.all.gamf"

# ADL_File1     = ADL_Folder + "dfw__.lcdm.15204521.01.all.gamf"
# ADL_File2     = ADL_Folder + "dfw__.lcdm.15213020.01.all.gamf"

TOSFile       = TOS_Folder + "cannedrouteexport. 20180606_1707.csv"
AFIX          = "BRDJE"
Start         = datetime(2018, 6, 15, 22, 0)
End           = datetime(2018, 6, 15, 23, 0)

def CompareADL_AFIX_Time( ADL_File1, ADL_File2, Start, End, AFIX ):
    """
    This file is used to compare two ADL files
    1. the flights which are captured
    2. flight's status and arrival fix changes
    """
    Current_Time, ARV_Flights, Column_Names, Date, _, _, _ = ReadADLFile(  ADL_File1 )
    TOS            = ReadTOSFile( AFIXs, TOSFile )
    CheckingInputParameters( Current_Time )
    FLs1, CTOP_FLs1 = ProcessARVFlights( ARV_Flights, Column_Names, TOS, Date, Current_Time )

    Current_Time, ARV_Flights, Column_Names, Date, _, _, _ = ReadADLFile(  ADL_File2 )
    TOS             = ReadTOSFile( AFIXs, TOSFile )
    FLs2, CTOP_FLs2 = ProcessARVFlights( ARV_Flights, Column_Names, TOS, Date, Current_Time )

    Condition1 = (CTOP_FLs1['EAFT'] >= Start ) & (CTOP_FLs1['EAFT'] <  End ) & (CTOP_FLs1['AFIX'] == AFIX )
    Condition2 = (CTOP_FLs2['EAFT'] >= Start ) & (CTOP_FLs2['EAFT'] <  End ) & (CTOP_FLs2['AFIX'] == AFIX )

    FL_Out_List   =  list( set( CTOP_FLs1[Condition1]['ACID'] ).difference( set( CTOP_FLs2[Condition2]['ACID'] ) ) )
    FL_Out        =  CTOP_FLs1[Condition1][ CTOP_FLs1[Condition1]['ACID'].isin( FL_Out_List ) ][['ACID','ORIG','AFIX','EAFT']]
    FL_Out        =  FL_Out.reset_index(drop=True)
    FL_Out_New_Col=  CTOP_FLs2[CTOP_FLs2['ACID'].isin(FL_Out_List)][['ACID','AFIX', 'EAFT']]
    FL_Out_New_Col=  FL_Out_New_Col.reset_index(drop=True)
    FL_Out_New_Col.columns = ['ACID','AFIX_Now','EAFT_Now']

    FileName   = "Data\\File_Comparision\\" + ADL_File1[-18:-14] + '-' + ADL_File2[-18:-14] + '-' +'Out'+'.csv'
    FL_Out_File= pd.merge( FL_Out, FL_Out_New_Col, on=['ACID'] , how='outer')
    FL_Out_File.to_csv( FileName )

    FL_In_List   =  list( set( CTOP_FLs2[Condition2]['ACID'] ).difference( set( CTOP_FLs1[Condition1]['ACID'] ) ) )
    FL_In        =  CTOP_FLs2[Condition2][ CTOP_FLs2[Condition2]['ACID'].isin( FL_In_List ) ][['ACID','ORIG','AFIX','EAFT']]
    FL_In        =  FL_In.reset_index(drop=True)
    FL_In_New_Col=  CTOP_FLs1[CTOP_FLs1['ACID'].isin(FL_In_List)][['ACID','AFIX', 'EAFT']]
    FL_In_New_Col=  FL_In_New_Col.reset_index(drop=True)
    FL_In_New_Col.columns = ['ACID','AFIX_Old','EAFT_Old']

    FileName   = "Data\\File_Comparision\\" + ADL_File1[-18:-14] + '-' + ADL_File2[-18:-14] + '-' +'In'+'.csv'
    FL_In_File = pd.merge( FL_In, FL_In_New_Col, on=['ACID'] , how='outer')
    FL_In_File.to_csv( FileName )