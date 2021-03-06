import pandas as pd
import geopandas as gpd
from compactness import get_compactness
import os

work_dir = '/Users/paullindseth/Downloads/'
os.chdir(work_dir)

states = pd.read_csv('District Scorecard - State Table.csv', dtype=str)

result = pd.DataFrame()

map_type = 'ideal' # as opposed to 'actual'

national_districts = gpd.read_file('districtShapes/')

for index, row in states.iterrows():
    if row['1 District'] == 'Y' or row['Name'] in ['Kentucky', 'Oregon', 'Rhode Island']:
        result = result.append({'Name': row['Name'], 'Compactness': ''}, ignore_index=True)
    else:
        result = result.append({'Name': row['Name'], 'Compactness': get_compactness(row['ID'], row['Name'], row['State'], map_type, national_districts)}, ignore_index=True)

result.to_csv('compactness_results_' + map_type + '_new.csv')



