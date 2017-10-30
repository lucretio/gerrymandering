import pandas as pd
import geopandas as gpd
import os
import pdb

# Ideal efficiency using precinct files

def get_old_efficiency(state_num, state_name, state_abbrev):

    work_dir = '/Users/paullindseth/Downloads/'
    os.chdir(work_dir)

    votes = pd.read_csv('%s_vtd_pop.csv' % state_name, dtype={'GeoID2': str}).rename(
        columns={'GeoID2': 'GEOID10'})


    # from compactness.py
    dir_name = 'BlockAssign_ST' + state_num + '_' + state_abbrev
    blockfile = pd.read_csv(dir_name + '/' + dir_name + '_VTD.txt', dtype=str)
    block_solution = pd.read_csv(state_abbrev + '_Congress.csv', names=['BLOCKID', 'DIST_NUM'], dtype=str)
    blockfile['GEOID10'] = state_num + blockfile['COUNTYFP'] + blockfile['DISTRICT']  # GEOID10 is VTD
    blockfile = blockfile.merge(block_solution, on='BLOCKID')
    blockfile = blockfile.groupby('GEOID10', group_keys=False).apply(lambda df: df.sample(1)).reset_index(drop=True)
    #

    new_districts = blockfile[['GEOID10', 'DIST_NUM']].copy() #avoid settingwithcopywarning when I map on new_districts

    x = votes.merge(new_districts, how='outer', left_on='GEOID10', right_on='GEOID10')

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