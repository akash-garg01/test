# -*- coding: utf-8 -*-
"""
Created on Sun May 06 17:00:26 2018

@author: Guodong

https://stackoverflow.com/questions/26577516/how-to-test-if-a-string-contains-one-of-the-substrings-in-a-list
"""
#  from IPython import get_ipython
# get_ipython().magic('reset -sf')

#%%
import pandas as pd
from Process_ADL import ReadADLFile, ProcessARVFlights, Retrieve_ADL_File, CheckingInputParameters
from Process_TOS import ReadTOSFile, PrepareInputLightCTOP, TOS_Market_Analysis
from Process_Capacity import * #
from datetime import datetime, timedelta
from Global_Variables import *
# from LightCTOP import LightCTOPModel
#from LightCTOP_Xpr ess import LightCTOPModel, LightCTOPModel_Main
from Visualization import Demand_Capacity_Single_Window, Demand_Capacity
#from Analyze_Solution import Process_Solution, Visualize_RerouteInfo_Single_Window, Visualize_RerouteInfo
#from Analyze_Solution import Generate_OneLineTOS_For_Submission
#from Sensitivity_Analysis import Power_Run
import pytz
import matplotlib.pyplot as plt

plt.close("all")
#%%
Current_Time, ARV_Flights, Column_Names, Date, _, _, _ = ReadADLFile(  ADLFile )
CheckingInputParameters( Current_Time, ADLFile, TOSFile )
TOS           = ReadTOSFile( AFIXs, TOSFile )
FLs, CTOP_FLs = ProcessARVFlights( ARV_Flights, Column_Names, TOS, Date, Current_Time )
Model_Input   = PrepareInputLightCTOP( TOS, CTOP_FLs, ExtraMileMax, Current_Time )
M, Vio_Num    = CapacityData( CTOP_FLs )
#%%
plt.close( 'all' )
#Demand_Capacity_Single_Window( CTOP_FLs, Current_Time, Flight_Status = True )
Demand_Capacity( CTOP_FLs, Bin, Current_Time, Flight_Status = True )
#%%
#plt.close( 'all' )
#Solution       = LightCTOPModel( M, *Model_Input)
#Solution       = LightCTOPModel_Main( M, *Model_Input )
#CTOP_FLs       = Process_Solution( Current_Time, CTOP_FLs, Vio_Num, *Model_Input + Solution )
  #Demand_Capacity_Single_Window( CTOP_FLs, Current_Time, Flight_Status = True, Solved = True)
#Demand_Capacity( CTOP_FLs, Bin, Current_Time, Flight_Status = True, Solved = True )
# Visualize_RerouteInfo_Single_Window( CTOP_FLs, Current_Time )
#Visualize_RerouteInfo( CTOP_FLs, Current_Time )
#TOS_For_Submission = Generate_OneLineTOS_For_Submission( CTOP_FLs, TOS )
#%%
#TOS_Market_Analysis( CTOP_FLs, TOS )
#Power_Run( TOS, CTOP_FLs, Current_Time, M )

      