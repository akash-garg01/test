# -*- coding: utf-8 -*-
"""
Created on Wed May 02 12:47:37 2018

@author: Guodong

https://stackoverflow.com/questions/20625582/how-to-deal-with-settingwithcopywarning-in-pandas
https://stackoverflow.com/questions/32229419/split-string-into-number-and-text-with-pandas
https://stackoverflow.com/questions/7568627/using-python-string-formatting-with-lists
"""
import pandas as pd
import pytz
import re
pd.options.mode.chained_assignment = None 
from datetime import datetime, timedelta
from Global_Variables import *
import glob, os, shutil
from time import time, gmtime
import gzip

def Retrieve_ADL_File( ADL_Folder  ):
    print('-' * 100)
    print("Retrieving ADL File From Network Drive. It Will Takes ~50 Seconds")

    start         = time()
    List_of_Files = glob.glob('Z:/dfw__.lcdm.' + str( gmtime().tm_mday ) + '*.gz' )
    Latest_ADL    = max( List_of_Files, key = os.path.getctime )
    end           = time()
    print ("Finding ADL File %s Takes: %3.2f seconds" % ( Latest_ADL[3:-3], end - start ))

    with gzip.open( Latest_ADL, 'rb') as f_in:
        with open( ADL_Folder + Latest_ADL[3:-3], 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    print('-' * 100)
    return Latest_ADL[3:-3]

def ReadADLFile( ADLFile  ):
    """
    Read ADL file line by line, and return ARV_Flights, which is a list and has Arrival flights information
    ADL file information can be found in <<R10 ADL File Specification v14.1 (without track changes).pdf>>
    another way to accomplish this is to read whole file to a list, and then process the list f = open("file.txt") lines = f.readlines()
    """
    with open( ADLFile, "r" ) as fp:
    #    lines = fp.readlines()
        
        Counter                = 1
        Arrivals_Counter       = 0 
        ARRIVAL_DATA_BLOCK     = 0
        Column_Names           = []
        Num_Flights            = 0
        ARV_Flights            = []
        Date                   = ''
        START_UPDATE           = ''
        ADL_START_TIME         = ''
        ADL_END_TIME           = ''
        
        for line in fp:
            if len( line.split() ) == 2:
                if line.split()[1] == 'ARRIVALS':
                    ARRIVAL_DATA_BLOCK = 1
                    Counter = Counter + 1
                    continue
            
            if ':Date:' in line.split():
                Date = line.split()[1]
                Counter           += 1
                continue
            
            if 'START_UPDATE' in line.split():
                START_UPDATE = line.split()[1]
                Counter           += 1
                continue                
            
            if 'ADL_START_TIME' in line.split():
                ADL_START_TIME = line.split()[1]
                Counter           += 1
                continue    

            if 'ADL_END_TIME' in line.split():
                ADL_END_TIME = line.split()[1]
                Counter           += 1
                continue                
            
            
            if ARRIVAL_DATA_BLOCK == 1 and Arrivals_Counter == 0:
                Column_Names = line.strip('#').split()
                                          
                Arrivals_Counter  += 1
                Counter           += 1
                continue
            
            if ARRIVAL_DATA_BLOCK == 1 and Arrivals_Counter == 1:
                Num_Flights = int( line.split()[1] )
                
                Arrivals_Counter  += 1
                Counter           += 1
                continue
            
            if ARRIVAL_DATA_BLOCK == 1 and Arrivals_Counter > 1:
                if line.split()[0] != '#':
                    ARV_Flights.append( line.split() )
                    Arrivals_Counter  += 1
                    Counter           += 1
                    continue
                else:
                    ARRIVAL_DATA_BLOCK = 0
            
            Counter = Counter + 1

    Current_Time = datetime.strptime(Date + Space + START_UPDATE[2:], '%m/%d/%Y %H%M%S')

    return Current_Time, ARV_Flights, Column_Names, Date, START_UPDATE, ADL_START_TIME, ADL_END_TIME
        
def ProcessARVFlights( ARV_Flights, Column_Names, TOS, Date, Current_Time):
    """
    1. Find flights which don't have EAFT info
    2. Convert the time string to datetime format
    3. Create departure and arrival status columns 'ETA_Status' and 'ETD_Status'
    4. Create new columns 'AFIX_Current', 'EAFT_Current', which will be used in solution post-analysis
    5. CTOP Captured flights, AA Operated Flights, Exempted, En route flights
    6. Create reference time, which is in central time

    We need two output files, in one file, for non-ENY flights, the new route ID is None
    in another file, which can be directly read by CTOP platform, we also need new route ID,
    therefore we need 'Route_ID_New' and also 'Route_ID_New_TOS'
    """

    log  = open( Report_File , "a+")
    FLs  = pd.DataFrame( ARV_Flights, columns = Column_Names ) #convert list to pandas dateframe

    # """Split ACID into carrier and ID number"""
    #bosung
    #FLs                 = pd.concat([FLs, pd.DataFrame(columns=['Carrier', 'ID'])], sort=False)
    FLs['Carrier']      = FLs['ACID'].apply( carrier_info )
    FLs['ID']           = FLs['ACID'].apply( id_info )

    print ('-' * 100)
    print( "The Following Flights Don't Have EAFT Information" )
    SF = FLs[ FLs['EAFT'] == '-'] #Special flights which don't have EAFT

    print ( SF[['ACID', 'ORIG', 'DCENTR', 'ETD', 'ETA']] )
    SF.to_csv( Output_Dir +  'NO_EAFT_Flights.csv')

    log.write('-' * 100 + '\n')
    log.write("The Following Flights Don't Have EAFT Information"+ '\n')
    SF[['ACID', 'ORIG', 'DCENTR', 'ETD', 'ETA']].to_string( log )
    log.write('\n')

    FLs = FLs[ FLs['EAFT'] != '-']
    FLs['EAFT'] = pd.to_datetime( Date[0:2] + Date[-4:] + FLs['EAFT'], format = "%m%Y%d%H%M")

    FLs['ETA_Status'] = FLs['ETA'].str[0]
    FLs['ETA']        = pd.to_datetime( Date[0:2] + Date[-4:] + FLs['ETA'].str[1:], format = "%m%Y%d%H%M" )

    Condition         = FLs['ETA']  + timedelta( hours = 2 ) < Current_Time
    FLs[Condition]['ETA']        = FLs[Condition]['ETA'] + timedelta( days = 1 )

    FLs['ETD_Status'] = FLs['ETD'].str[0]
    FLs['ETD']        = pd.to_datetime( Date[0:2] + Date[-4:] + FLs['ETD'].str[1:], format = "%m%Y%d%H%M" )

    Condition         = ( FLs['ETA'] - FLs['ETD'] ) > timedelta( hours = 20 )
    FLs[Condition]['ETD'] = FLs[Condition]['ETD'] - timedelta( days = 1 )

    #bosung
    #FLs                 = pd.concat([FLs, pd.DataFrame(columns = [ 'AFIX_New', 'EAFT_New'] )], sort = False)
    FLs['AFIX_New'] = FLs['AFIX']
    FLs['EAFT_New'] = FLs['EAFT']

    #bosung
    #FLs = pd.concat([FLs, pd.DataFrame( columns=['Route_ID', 'Route_ID_New', 'Route_ID_New_TOS', 'Extra Wind Miles', 'Flight_Status'])], sort=False )

    # """Add reference time column, which is in local time"""
    FLs['Ref_Central_Time']     = FLs['ETD'] - timedelta( minutes = ReferenceTime )
    FLs['Ref_Central_Time']     = FLs['Ref_Central_Time'].dt.tz_localize('UTC').dt.tz_convert('US/Central')

    Condition           = ( FLs['EAFT'] >= CTOP_START  ) & ( FLs['EAFT'] <= CTOP_END  )
    CTOP_FLs            = FLs[Condition]

    Cancel_Columns      = ['UX','FX','RZ','RS','TO','DV','RM']
    Cancel_Columns      = ['UX']
    #Condition           = ( CTOP_FLs[ Cancel_Columns ] == 'Y' ).any( axis = 1 )
    Condition           = ( CTOP_FLs[ 'UX' ] == 'Y' )
    #Columns_Status      = list( ( CTOP_FLs[ Cancel_Columns ] == 'Y' ).any() )
    Columns_Status      = list( ( CTOP_FLs[ 'UX' ] == 'Y' ))
    Kept_Columns        = [Column for (Column, Status) in zip( Cancel_Columns, Columns_Status ) if Status == True]

    print ('-' * 100)
    print("The Following Flights Have Been Cancelled")
    Cancelled_FLs       = CTOP_FLs[ Condition ]
    print( Cancelled_FLs[['ACID','ETD','AFIX','EAFT'] + Kept_Columns ] )
    Cancelled_FLs.to_csv( Output_Dir +  'Cancelled_Flights.csv')

    log.write('-' * 100 + '\n')
    log.write("The Following Flights Have Been Cancelled"+ '\n')
    Cancelled_FLs[['ACID', 'ETD', 'AFIX', 'EAFT'] + Kept_Columns].to_string( log )
    log.write('\n')

    CTOP_FLs            = CTOP_FLs[~Condition]

    Condition                                = ( CTOP_FLs['MAJOR']!= 'AAL' )
    CTOP_FLs.at[Condition, 'Flight_Status']  = 'OA'

    Condition                                = ( CTOP_FLs['MAJOR'] == 'AAL') & ( CTOP_FLs['ETA_Status'] == 'A' )
    CTOP_FLs.at[Condition, 'Flight_Status']  = 'Landed'

    Condition                                = ( CTOP_FLs['MAJOR'] == 'AAL') & ( CTOP_FLs['ETA_Status'] != 'A' ) & \
                                               ( CTOP_FLs['ETD_Status'] == 'A' ) #departed but not landed yet
    CTOP_FLs.at[Condition, 'Flight_Status']  = 'En route'

    """Reroutable if they have TOS options and they are not exempted"""
    Condition                                = ( CTOP_FLs['MAJOR'] == 'AAL') & (CTOP_FLs['ETD_Status'] != 'A') & \
                                               ( CTOP_FLs['ETD'] - Current_Time > ExemptTime )
    CTOP_FLs.at[Condition, 'Flight_Status']  = 'Reroutable'

    """Further Investigate if a flight has TOS route or not"""
    Reroutables                              = CTOP_FLs[ CTOP_FLs['Flight_Status'] == 'Reroutable' ]
    for index, row in Reroutables.iterrows():
        ACID         = row['ACID']
        ORIG         = row['ORIG']
        DEST         = row['DEST']
        airline_code = row['Carrier']

        Condition = (TOS['airline_code'] == airline_code) & (TOS['departure_station'] == ORIG)
        if 0 == len( TOS[ Condition ] ):
            CTOP_FLs.at[ index, 'Flight_Status' ] = 'AA No TOS'

    # two scenarios that flights will be exempted 1. explicated exempted 2. not departed yet, but very close to departure
    Condition                                = ( CTOP_FLs['MAJOR'] == 'AAL') & ( CTOP_FLs['ETD_Status'] != 'A' ) & \
    ( CTOP_FLs['ETD'] - Current_Time <= ExemptTime) | CTOP_FLs['ORIG'].isin(EXPT['Airports']) | \
    ( CTOP_FLs['Carrier'].isin(EXPT['Subcarriers']) ) | ( CTOP_FLs['ACID'].isin(EXPT['FLT_List']) )
    CTOP_FLs.at[Condition, 'Flight_Status']  = 'Exempted'

    log.close()
    return FLs, CTOP_FLs

def CheckingInputParameters( Current_Time, ADLFile, TOSFile ):
    """
    This function checks
    1. if the current time, CTOP start and end time are compatible with each other
    2. in general current time is 4-6 hours ahead of CTOP start time
    3. if capacity information is compatible with the number of time periods
    """
    log        = open( Report_File , "a+")
    Error_Flag = 0

    print('-'*100)
    print( 'Current Time      ' + str( Current_Time ) + str('Z') )
    print( 'CTOP Window       ' + str( CTOP_START )+ str('Z') + str(' to ') + str( CTOP_END ) + str('Z') )
    print( 'Airport Flow      ' + str( AirportFlow )  + '\n' )

    if HAND_TYPED == True:
        print('Reading Parameters from Code' + '\n')
    else:
        print('Reading Parameters from Excel File' + '\n' )

    print( 'Capacity Information in Each 15-mins Time Periods' )
    for fca in FCAs:
        print( fca + Space + " ".join(['%2d']*len( Capacity[ fca ] )) %tuple( Capacity[ fca ] )  )

    print('')
    print( 'ADL File     : ' + ADLFile )
    print( 'TOS File     : ' + TOSFile )
    print( 'Output Folder: ' + Output_Dir )

    log.write( '-'*100 + '\n')
    log.write( 'Current Time      ' + str( Current_Time )+ str('Z') + '\n' )
    log.write( 'CTOP Window       ' + str( CTOP_START )+ str('Z') + str(' to ') + str( CTOP_END ) + str('Z') + '\n' )
    log.write( 'Airport Flow      ' + str( AirportFlow ) + '\n' )

    log.write('\n')

    if HAND_TYPED == True:
        log.write('Reading Parameters from Code' + '\n')
    else:
        log.write('Reading Parameters from Excel File' + '\n' )

    log.write('\n')
    log.write( 'Capacity Information in Each 15-mins Time Periods' + '\n' )
    for fca in FCAs:
        log.write( fca + Space + " ".join(['%2d']*len( Capacity[ fca ] )) %tuple( Capacity[ fca ] ) + '\n' )

    log.write('\n')
    log.write( 'ADL File     : ' + ADLFile + '\n' )
    log.write( 'TOS File     : ' + TOSFile + '\n' )
    log.write( 'Output Folder: ' + Output_Dir + '\n' )

    print('-' * 100)
    print('Input CTOP Parameters Checking\n')

    log.write( '-' * 100 + '\n' )
    log.write('Input CTOP Parameters Checking \n')
    assert ( ( Current_Time <= CTOP_END ) & ( CTOP_START < CTOP_END ) & ( CTOP_START - Current_Time <= timedelta( hours = 24) ) ), 'Check CTOP Start and End Times!'
    for value in Capacity.values():
        assert ( Time_Periods == len( value ) ), "Check Capacity Information!"

    print("CTOP Parameters Checking Passed")
    log.write('CTOP Parameters Checking Passed \n')

    log.close()










