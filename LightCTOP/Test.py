from datetime import datetime
from time import gmtime
datetime.now()
gmtime()

Cancel_Columns
Columns_Status

[Column for (Column, Status) in zip( Cancel_Columns, Columns_Status ) if Status == True]


CTOP_FLs['ACID'].str.split( '\d*' , expand=True)

CTOP_FLs['ACID'].str.split('\d*(\D+)', expand=True).loc[:,1]
CTOP_FLs['ACID'].str.split('\d*(\D+)', expand=True).loc[:,2]


FLs  = pd.concat([FLs, pd.DataFrame(columns = [ 'Test1', 'Test2'] )], sort = False)

#%%
import pandas as pd
import numpy as np


from IPython.utils import io

# with io.capture_output() as captured:
#     print("hello world")
#%%
# CTOP_FLs[ CTOP_FLs['Flight_Status'] == 'AA No TOS' ]
# CTOP_FLs[ CTOP_FLs['Flight_Status'] == 'Reroutable' ][['ACID','ORIG','Route_ID']]
# CTOP_FLs[ CTOP_FLs['Route_ID'].notnull() ]


Condition = (CTOP_FLs['EAFT'] >= CTOP_START + timedelta(minutes=5 * Bin)) & \
            (CTOP_FLs['EAFT'] <  CTOP_START + timedelta(minutes=(5 + 1) * Bin)) & \
            (CTOP_FLs['AFIX'] == "BRDJE") & ( CTOP_FLs['Flight_Status'] == 'Reroutable' )

CTOP_FLs[ Condition ][['ACID','ORIG','Route_ID','AFIX','EAFT']]

#%%
Condition = (CTOP_FLs['EAFT'] >= datetime(2018, 6, 15, 22, 0) ) & \
            (CTOP_FLs['EAFT'] <  datetime(2018, 6, 15, 23, 0) ) & \
            (CTOP_FLs['AFIX'] == "BRDJE")

CTOP_FLs[ Condition ][['ACID','ORIG','AFIX','EAFT']].to_csv("Data\\1945Z.csv")