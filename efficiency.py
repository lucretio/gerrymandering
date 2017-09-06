import pandas as pd
import os
import sys

# 4 cases: general with Total, general without Total, general_precinct, and differentiated precinct files

work_dir = '/Users/paullindseth/Downloads/'
os.chdir(work_dir)

state_abbrev = sys.argv[1]
csv_filename = '20161108__' + state_abbrev.lower() + '__general'
if state_abbrev in ['FL']:
    csv_filename += '__county__raw'
elif state_abbrev in ['HI', 'WV']:
    csv_filename += '__county'

house_votes = pd.read_csv(csv_filename + '.csv')

if state_abbrev in ['CO', 'FL']:
    contest_name = 'United States Representative'
elif state_abbrev in ['GA']:
    contest_name = 'U.S. Representative'
elif state_abbrev in ['AL', 'CA', 'HI', 'NY', 'OH', 'WV']:
    contest_name = 'U.S. House'


house_votes = house_votes[house_votes['office'] == contest_name]
# district, party, votes
house_votes = house_votes[['district', 'party', 'votes']]
# sometimes DEM is (DEM and REP is (REP in this file
if state_abbrev == 'GA':
    house_votes['party'] = house_votes['party'].map(lambda s: s.replace('(', ''))
if state_abbrev == 'HI':
    # house_votes['district'] = house_votes['district'].map(lambda s: s.replace('-Unexpired Term', ''))
    house_votes= house_votes[~(house_votes['district'] == '1-Unexpired Term')]
    house_votes['votes'] = house_votes['votes'].map(lambda s: s.replace(',', ''))
    house_votes['votes'] = pd.to_numeric(house_votes['votes'])
house_votes = house_votes.pivot_table(index='district',columns='party',aggfunc=sum)
house_votes = house_votes.fillna(0)

wasted_votes = 0 # + is D, - is R

if state_abbrev in ['OH']:
    dem_col_name = 'Democratic'
    rep_col_name = 'Republican'
elif state_abbrev in ['CA', 'GA', 'NY']:
    dem_col_name = 'DEM'
    rep_col_name = 'REP'
elif state_abbrev in ['AL', 'HI']:
    dem_col_name = 'D'
    rep_col_name = 'R'
elif state_abbrev in ['CO']:
    dem_col_name = 'Democratic Party'
    rep_col_name = 'Republican Party'
elif state_abbrev in ['FL', 'WV']:
    dem_col_name = 'Democrat'
    rep_col_name = 'Republican'

third_party_votes = house_votes['votes'][house_votes['votes'].columns.difference([dem_col_name, rep_col_name])].sum(axis=1)

for index, row in house_votes.iterrows():
    # print index
    dem_v = row['votes'][dem_col_name]
    rep_v = row['votes'][rep_col_name]
    dem_v += third_party_votes[index] / 2     # type BS
    rep_v += third_party_votes[index] / 2
    if dem_v > rep_v:
        wasted_votes += (dem_v - rep_v) / 2
        wasted_votes -= rep_v
    else:
        wasted_votes -= (rep_v - dem_v) / 2
        wasted_votes += dem_v

total_votes = house_votes.values.sum()

print wasted_votes / total_votes