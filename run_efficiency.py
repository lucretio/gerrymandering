import pandas as pd
from ballotpedia_scrape import get_efficiency
import os

work_dir = '/Users/paullindseth/Downloads/'
os.chdir(work_dir)

states = pd.read_csv('District Scorecard - State Table.csv', dtype=str)

result = pd.DataFrame()

map_type = 'actual' # 'actual' or 'ideal'

for index, row in states.iterrows():
    if row['1 District'] == 'Y' or row['Name'] in ['Kentucky', 'Oregon', 'Rhode Island']:
        efficiency = 0
        result = result.append({'Name': row['Name'], 'Efficiency': efficiency}, ignore_index=True)
    else:
        efficiency = get_efficiency(row['Name'], int(row['Districts']))
        result = result.append({'Name': row['Name'], 'Efficiency': efficiency}, ignore_index=True)
    print row['Name'] + ": " + str(efficiency)

result.to_csv('efficiency_results_' + 'actual_scrape' '.csv')



