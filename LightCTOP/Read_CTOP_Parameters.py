
#%%

from datetime import datetime, timedelta
import xlrd
import numpy as np

CTOP_Parameters_File = "DFW_LightCTOP_Model_Input.xlsx"
Book                 = xlrd.open_workbook( CTOP_Parameters_File )
South                = Book.sheet_by_name("South Flow")

ADLFile              = South.cell_value( rowx = 3, colx = 1 )
TOSFile              = South.cell_value( rowx = 4, colx = 1 )

CTOP_START           = South.cell_value( rowx = 7, colx = 2 )
CTOP_START           = datetime.strptime( CTOP_START, '%m/%d/%Y %H:%M')
CTOP_END             = South.cell_value( rowx = 7, colx = 3 )
CTOP_END             = datetime.strptime( CTOP_END, '%m/%d/%Y %H:%M') + timedelta ( seconds = 59 )

Time_Periods  = ( CTOP_END + timedelta( seconds = 1 ) - CTOP_START ).seconds/(60*15)
TIME          = range( 1, Time_Periods + 1 )


ExemptTime    = South.cell_value( rowx = 16, colx= 6 )
ExemptTime    = timedelta( minutes = ExemptTime )  # timedelta( hours = 1 )

Vio_Penalty   = South.cell_value( rowx = 10, colx = 1 )
ExtraMileMax  = South.cell_value( rowx = 12, colx = 1 )

Capacity      = {}
FCAs          = ['BRDJE', 'VKTRY', 'BOOVE', 'BEREE']
for ( fca, col ) in zip( FCAs, [1, 2, 3, 4] ):
    capacity_list   = South.col_slice( colx = col, start_rowx= 16, end_rowx = 16 + Time_Periods  )
    Capacity[ fca ] = [ int( x.value ) for x in capacity_list]

EXPT          = { 'Airports':[],
                  'Subcarriers':[],
                  'FLT_List':[] }
Categories    = ['Airports', 'Subcarriers', 'FLT_List']

for ( category, col ) in zip( Categories, [7, 8, 9] ):
    count = 0
    while( 0 != South.cell_type( rowx= 16+count, colx= col)  ):
        EXPT[ category ].append( South.cell_value( rowx= 16+count, colx= col ) )
        count += 1

#%%