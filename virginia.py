import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import time
from helper import haversine
import pdb
import os

work_dir = '/Users/paullindseth/Downloads/'
os.chdir(work_dir)

state_num = '51'
state_abbrev = 'VA'
state_vtds = gpd.read_file('tl_2012_%s_vtd10/' % state_num)

##########
national_counties = pd.read_csv('national_county.txt', names=['STATE', 'STATEFP', 'COUNTYFP', 'COUNTYNAME', 'CLASSFP'], dtype=str)
counties = national_counties[national_counties['STATE'] == state_abbrev].reset_index(drop=True)

def county_strip(s):
    if 'County' in s:
        return s[:-7]
    else:
        return s

counties['COUNTYNAME'] = counties['COUNTYNAME'].map(lambda s: county_strip(s).lower()) # truncate county
##########

state_abbrev = 'VA'

csv_filename = '20161108__' + state_abbrev.lower() + '__general__precinct'
csv_filename += '__raw'
votes = pd.read_csv(csv_filename + '.csv', dtype=str)

votes = votes[votes['division'].map(lambda s: 'precinct' in s)]

x = state_vtds.merge(votes, how='outer', left_on='combo', right_on='jurisdiction')

votes['pure_name'] = votes['jurisdiction'].map(lambda s: s.split(' - ')[1])

votes = votes[votes['jurisdiction'].map(lambda s: ' - ' in s)]
votes['pure_name'] = votes['jurisdiction'].map(lambda s: s.split(' - ')[1])
state_vtds['big_name'] = state_vtds['NAME10'].map(lambda s: s.upper())
y = state_vtds.merge(votes, how='outer', left_on='big_name', right_on='pure_name')


'PRECINCT 3-A'.split('PRECINCT ')[-1]
'3-A'

