### this is for correctly figuring out what vtd is in what district

import os
import pandas as pd

work_dir = '/Users/paullindseth/Downloads/'
os.chdir(work_dir)

state_name = 'Colorado'
state_num = '08'
state_abbrev = 'CO'

dir_name = 'BlockAssign_ST' + state_num + '_' + state_abbrev

blockfile_vtd = pd.read_csv(dir_name + '/' + dir_name + '_VTD.txt', dtype=str)
blockfile_cd = pd.read_csv(dir_name + '/' + dir_name + '_CD.txt', dtype=str)

blockfile = pd.merge(blockfile_vtd, blockfile_cd, how='inner', left_on='BLOCKID', right_on='BLOCKID')

blockfile['VTD'] = state_num + blockfile['COUNTYFP'] + blockfile['DISTRICT_x']

blockfile = blockfile[['DISTRICT_y', 'VTD']]

vtd_district = blockfile.groupby(['VTD', 'DISTRICT_y']).size().reset_index(name="Freq")

# curiosity = vtd_district['VTD'].value_counts()

idx = vtd_district.groupby(['VTD'])['Freq'].transform(max) == vtd_district['Freq']

vtd_district = vtd_district[idx]

