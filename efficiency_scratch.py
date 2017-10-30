import pandas as pd
import geopandas as gpd
import os
import pdb

# Ideal efficiency using precinct files

work_dir = '/Users/paullindseth/Downloads/'
os.chdir(work_dir)

# state_abbrev = 'CO'
# state_num = '08'

state_abbrev = 'MD'
state_num = '24'

national_counties = pd.read_csv('national_county.txt', names=['STATE', 'STATEFP', 'COUNTYFP', 'COUNTYNAME', 'CLASSFP'], dtype=str)
counties = national_counties[national_counties['STATE'] == state_abbrev].reset_index(drop=True)

def county_strip(s):
    if 'County' in s:
        return s[:-7]
    else:
        return s

counties['COUNTYNAME'] = counties['COUNTYNAME'].map(lambda s: county_strip(s).lower()) # truncate county

csv_filename = '20161108__' + state_abbrev.lower() + '__general__precinct'
if state_abbrev in ['FL', 'MD', 'NC']:
    csv_filename += '__raw'

votes = pd.read_csv(csv_filename + '.csv', dtype=str)

if state_abbrev in ['HI', 'NV']:
    office = 'U.S. House'
elif state_abbrev in ['OH']:
    office = 'Representative to Congress'
elif state_abbrev in ['NM']:
    office = 'House'
elif state_abbrev in ['NC']:
    office = 'US HOUSE OF REPRESENTATIVES'
elif state_abbrev in ['CO']:
    office = 'United States Representative'
elif state_abbrev in ['MD']: #proxy
    office = 'U.S. Senator'

votes = votes[votes['office'] == office]
if state_abbrev in ['MD', 'NC']:
    votes['county'] = votes['parent_jurisdiction']
votes['county'] = votes['county'].map(lambda s: s.lower()) # make counties lower case in both county-file and vote-file

if state_abbrev in ['CO', 'HI', 'NM', 'NV']:
    vote_precinct_col = 'precinct'
elif state_abbrev in ['OH']:
    vote_precinct_col = 'Precinct Code'
elif state_abbrev in ['MD', 'NC']:
    vote_precinct_col = 'jurisdiction'
elif False:
    vote_precinct_col = 'precinct'


print "Election file rows:" + str(len(votes))

# pdb.set_trace()

print "Election file rows with empty precinct fields: " + str(len(votes[votes[vote_precinct_col].isnull()]))

votes = votes[~votes[vote_precinct_col].isnull()]

print "Election file rows with empty or \"0\" votes fields: " + str(len(votes[votes['votes'].isnull()]) + len(votes[votes['votes'] == '0']))

votes = votes[~votes['votes'].isnull()]
votes = votes[votes['votes'] != '0']

# pdb.set_trace()

print "Election file rows with absentee fields: " + str(len(votes[votes[vote_precinct_col].map(lambda s: 'ABSENTEE' in s)]))
votes = votes[~votes[vote_precinct_col].map(lambda s: 'ABSENTEE' in s)]
print "Election file rows with one stop fields: " + str(len(votes[votes[vote_precinct_col].map(lambda s: 'ONE STOP' in s)]))
votes = votes[~votes[vote_precinct_col].map(lambda s: 'ONE STOP' in s)]

votes = votes.merge(counties, how='outer', left_on='county', right_on='COUNTYNAME')
# need to check for isnull b/c of the outer join
print "Election file rows that did not match with a county: " + str(len(votes[votes['COUNTYNAME'].isnull()]))
print "County file rows that did not match with an election-file county: " + str(len(votes[votes['county'].isnull()]))




state_vtds = gpd.read_file('tl_2012_%s_vtd10/' % state_num)
print "Number of precincts from shapefile: " + str(len(state_vtds))


# from compactness.py
dir_name = 'BlockAssign_ST' + state_num + '_' + state_abbrev
blockfile = pd.read_csv(dir_name + '/' + dir_name + '_VTD.txt', dtype=str)
block_solution = pd.read_csv(state_abbrev + '_Congress.csv', names=['BLOCKID', 'DIST_NUM'], dtype=str)
blockfile['GEOID10'] = state_num + blockfile['COUNTYFP'] + blockfile['DISTRICT']  # GEOID10 is VTD
blockfile = blockfile.merge(block_solution, on='BLOCKID')
blockfile = blockfile.groupby('GEOID10', group_keys=False).apply(lambda df: df.sample(1)).reset_index(drop=True)
#

new_districts = blockfile[['GEOID10', 'DIST_NUM']].copy() #avoid settingwithcopywarning when I map on new_districts
print "Number of precincts from blockfiles: " + str(len(new_districts))

###

# TEMP
if state_abbrev not in ['MD']: # shouldn't this be taken out altogether
    new_districts = new_districts[~new_districts['GEOID10'].map(lambda s: '-' in s)]
# should this also be TEMP?
new_districts = new_districts[~new_districts['GEOID10'].map(lambda s: 'ZZZZZZ' in s)]

# this might not deal with 3 digit VTD numbers well '133' -> '0133' is that correct? *** NOW FIXED I THINK
# # and how about hyphenated stuff like '-1' -> '0-1'

def precinct_prefix_zero(s):
    if s[0] == '0' or int(s) >= 100:
        return s
    else:
        return '0' + s

def precinct_infix_zero(s):
    state_county_part = s[:5] # 2 digits for state, 3 for county
    precinct_part = s[5:]
    return state_county_part + precinct_prefix_zero(precinct_part)


# vvv I think this was for FL
# votes['precinct_id'] = state_num + votes['COUNTYFP'] + votes['precinct'].map(lambda s: s[-5:])

if state_abbrev in ['NV']:
    new_districts['precinct'] = new_districts['GEOID10'].map(lambda s: precinct_infix_zero(s))
    votes['precinct_id'] = state_num + votes['COUNTYFP'] + votes[vote_precinct_col].map(lambda s: precinct_prefix_zero(s))
elif state_abbrev in ['OH']:
    new_districts['precinct'] = new_districts['GEOID10']
    # yes, that doubling is intentional
    votes['precinct_id'] = state_num + votes['COUNTYFP'] + votes['COUNTYFP'] + votes[vote_precinct_col]
elif state_abbrev in ['NC', 'NM']:
    new_districts['precinct'] = new_districts['GEOID10']
    votes['precinct_id'] = state_num + votes['COUNTYFP'] + votes[vote_precinct_col]
elif state_abbrev in ['HI']:
    new_districts = new_districts.merge(state_vtds, how='inner', left_on='GEOID10', right_on='GEOID10')
    new_districts = new_districts[['GEOID10', 'DIST_NUM', 'VTDST10']].copy()
    new_districts['precinct'] = new_districts['VTDST10']
    votes['precinct_id'] = votes['precinct'].astype(str).map(lambda s: s.replace('-',''))
elif state_abbrev in ['MD']:
    new_districts['precinct'] = new_districts['GEOID10']
    votes['precinct_id'] = state_num + votes['COUNTYFP'] + votes[vote_precinct_col].map(lambda s: s[1:])
elif state_abbrev in ['CO']:
    new_districts['precinct'] = new_districts['GEOID10']
    votes['precinct_id'] = state_num + votes['COUNTYFP'] + votes['precinct'].map(lambda s: s[-5:])

###


# x = votes.merge(new_districts, how='outer', left_on='precinct_id', right_on='precinct')
# this ensures everything is counted
# x = votes.merge(new_districts, how='left', left_on='precinct_id', right_on='precinct')

x = votes.merge(new_districts, how='outer', left_on='precinct_id', right_on='precinct')

print "Election file precincts that did not match with a shapefile precinct: " + str(len(x[x['GEOID10'].isnull()]['precinct_id'].unique()))
print "Shapefile precincts that did not match with an election file precinct: " + str(len(x[x['precinct_id'].isnull()]['GEOID10'].unique()))

x = votes.merge(new_districts, how='inner', left_on='precinct_id', right_on='precinct')

# len(x[x['county'].isnull()])
# len(x[x['GEOID10'].isnull()])

# pdb.set_trace()

###
x['votes'] = x['votes'].map(lambda s: s.replace(',', ''))
x['votes'] = pd.to_numeric(x['votes'])
x = x.pivot_table(index='DIST_NUM',columns='party',aggfunc=sum)
x = x.fillna(0)
###

if state_abbrev in ['HI', 'OH']:
    dem_col_name = 'D'
    rep_col_name = 'R'
elif state_abbrev in ['NM']:
    dem_col_name = 'Democratic'
    rep_col_name = 'Republican'
elif state_abbrev in ['MD', 'NC']:
    dem_col_name = 'DEM'
    rep_col_name = 'REP'


wasted_votes = 0

for index, row in x.iterrows():
    # print index
    dem_v = row['votes'][dem_col_name]
    rep_v = row['votes'][rep_col_name]
    if dem_v > rep_v:
        wasted_votes += (dem_v - rep_v) / 2
        wasted_votes -= rep_v
    else:
        wasted_votes -= (rep_v - dem_v) / 2
        wasted_votes += dem_v

total_votes = x.values.sum()

print "Total Seats: " + str(len(x['votes']))
print "Democratic Seats: " + str((x['votes'][dem_col_name] > x['votes'][rep_col_name]).sum())
print "Efficiency Gap:" + str(wasted_votes*1.0 / total_votes)