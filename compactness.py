import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import time
from helper import haversine
import pdb

def get_compactness(state_num, state_name, state_abbrev, map_type, national_districts):

    start = time.time()

    print state_num + ' ' + state_abbrev + ' ' + state_name + ', ' + map_type

    state_vtds = gpd.read_file('tl_2012_%s_vtd10/' % state_num)

    dir_name = 'BlockAssign_ST' + state_num + '_' + state_abbrev
    block_vtd = pd.read_csv(dir_name + '/' + dir_name + '_VTD.txt', dtype=str)
    # block_cd = pd.read_csv(dir_name + '/' + dir_name + '_CD.txt', dtype=str)
    block_cd = pd.read_csv('CD113/'+state_num+'_'+state_abbrev+'_CD113.txt', dtype=str).rename(
        columns={'CD113': 'DISTRICT'})
    block_cd = block_cd[block_cd['DISTRICT'] != 'ZZ']
    if map_type == 'actual':
        state_districts = national_districts[national_districts['STATENAME'] == state_name].copy()

        blockfile = pd.merge(block_vtd, block_cd, how='inner', left_on='BLOCKID', right_on='BLOCKID')

        blockfile['VTD'] = state_num + blockfile['COUNTYFP'] + blockfile['DISTRICT_x']

        blockfile = blockfile[['DISTRICT_y', 'VTD']]

        vtd_district = blockfile.groupby(['VTD', 'DISTRICT_y']).size().reset_index(name="Freq")

        # temp = vtd_district['VTD'].value_counts()

        idx = vtd_district.groupby(['VTD'])['Freq'].transform(max) == vtd_district['Freq']

        vtd_district = vtd_district[idx]

        state_vtds = state_vtds.merge(vtd_district, how='inner', left_on='GEOID10', right_on='VTD')

        # pdb.set_trace()


        district_centroids = state_districts.geometry.to_crs(epsg=5070).centroid.to_crs(epsg=4269)
        state_districts['dist_cent'] = district_centroids
        state_districts['DISTRICT'] = pd.to_numeric(state_districts['DISTRICT'])

    if map_type == 'ideal':
        ## block_solution = pd.read_csv(state_abbrev + '_Congress.csv', names=['BLOCKID', 'DIST_NUM'], dtype=str)
        block_solution = pd.read_csv(state_abbrev + '_Congress.csv', names=['BLOCKID', 'DISTRICT'], dtype=str)

        #
        blockfile = pd.merge(block_vtd, block_solution, how='inner', left_on='BLOCKID', right_on='BLOCKID')

        blockfile['VTD'] = state_num + blockfile['COUNTYFP'] + blockfile['DISTRICT_x']

        blockfile = blockfile[['DISTRICT_y', 'VTD']]

        vtd_district = blockfile.groupby(['VTD', 'DISTRICT_y']).size().reset_index(name="Freq")

        # temp = vtd_district['VTD'].value_counts()

        idx = vtd_district.groupby(['VTD'])['Freq'].transform(max) == vtd_district['Freq']

        vtd_district = vtd_district[idx]
        #

        ## block_vtd['GEOID10'] = state_num + block_vtd['COUNTYFP'] + block_vtd['DISTRICT']  # GEOID10 is VTD
        ## block_vtd = block_vtd.merge(block_solution, on='BLOCKID')

        ## # block_vtd = block_vtd.groupby('GEOID10', group_keys=False).apply(lambda df: df.sample(1))

        ## state_vtds = state_vtds.merge(blockfile, on='GEOID10')
        state_vtds = state_vtds.merge(vtd_district, how='inner', left_on='GEOID10', right_on='VTD')

        if state_num == '01':
            for i in range(int(max(state_vtds['DIST_NUM']))):
                print str(i)
                state_vtds[state_vtds['DISTRICT_y'] == str(i+1)].to_file('alabama_dist_'+str(i)+'idealnew')

        # pdb.set_trace()

        # need to be really careful with how strings are handled here
        inclusion_matrix = [(state_vtds.DIST_NUM == str(dist_num)) for dist_num in
                            range(0, int(max(block_vtd.DIST_NUM)))]  # using int on a max of a string is an abuse

        hard_version = True  # i.e. geographical centroid vs. average of centroids

        crs = {'init': 'epsg:5070'}
        if hard_version:
            districts = state_vtds[['geometry', 'DIST_NUM']].to_crs(epsg=5070).groupby('DIST_NUM',
                                                                                       as_index=False).apply(
                lambda df: reduce(lambda a, b: a.union(b), df.geometry))
            district_centroids = districts.apply(lambda poly: poly.centroid)
            district_centroids = gpd.GeoSeries(district_centroids, crs=crs).to_crs(epsg=4269)
        else:
            # need to use area times x/y coords to make this correct
            district_centroids = state_vtds[['geometry', 'DIST_NUM']].to_crs(epsg=5070).groupby('DIST_NUM',
                                                                                                as_index=False).apply(
                lambda df: Point(pd.Series([poly.centroid.x for poly in df.geometry]).mean(),
                                 pd.Series([poly.centroid.y for poly in df.geometry]).mean()))
            # .reset_index(drop=True).to_crs(epsg=4269)

            district_centroids = gpd.GeoSeries(district_centroids, crs=crs).to_crs(epsg=4269)

    seg0 = time.time()
    print(seg0 - start)

    vtd_centroids = state_vtds.geometry.to_crs(epsg=5070).centroid.to_crs(epsg=4269)
    state_vtds['cent'] = vtd_centroids

    state_2016_vtd_pop = pd.read_csv('%s_vtd_pop.csv' % state_name, dtype={'GeoID2': str}).rename(
        columns={'GeoID2': 'GEOID10'})
    state_vtds = state_vtds.merge(state_2016_vtd_pop, on='GEOID10')



    sum = 0



    # pdb.set_trace()
    state_vtds['DISTRICT_y'] = pd.to_numeric(state_vtds['DISTRICT_y'])
    state_vtds = state_vtds.merge(state_districts[['DISTRICT', 'dist_cent']], how='inner', left_on='DISTRICT_y', right_on='DISTRICT')

    for i in range(len(state_vtds)):
        sum += state_vtds.iloc[i]['Total Population'] * haversine(state_vtds.iloc[i]['cent'].x, state_vtds.iloc[i]['cent'].y, state_vtds.iloc[i]['dist_cent'].x, state_vtds.iloc[i]['dist_cent'].y)

    ###

    # pdb.set_trace()

    state_pop = state_vtds['Total Population'].sum()
    compactness = sum / state_pop

    finish = time.time()
    print(finish - seg0)

    print "compactness: " + str(compactness)

    return compactness


