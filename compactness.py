import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import time
import sys
from helper import haversine
#
# state_num = sys.argv[1]
# state_name = sys.argv[2]
# map_type = sys.argv[3] # 'actual' or 'ideal'

def get_compactness(state_num, state_name, state_abbrev, map_type):

    start = time.time()

    print state_num + ' ' + state_abbrev + ' ' + state_name + ', ' + map_type

    # state_2016_vtd_vote = pd.read_excel('/Users/paullindseth/Downloads/precinct.xlsx', 3, 1, range(0, 4))

    state_vtds = gpd.read_file('tl_2012_%s_vtd10/' % state_num)
    if map_type == 'actual':
        state_districts = gpd.read_file('districtShapes/')
        state_districts = state_districts[state_districts['STATENAME'] == state_name]
        districts_buffered = state_districts.geometry.buffer(.0001)

        # should I change the order of logical or here here???
        inclusion_matrix = [state_vtds.geometry.intersects(dist) | state_vtds.geometry.within(dist_buff) for dist, dist_buff in zip(state_districts.geometry, districts_buffered)]

        for idx in range(1, len(inclusion_matrix)):
            inclusion_matrix[idx] = ~inclusion_matrix[idx-1] & inclusion_matrix[idx]

        district_centroids = state_districts.geometry.to_crs(epsg=5070).centroid.to_crs(epsg=4269)
    if map_type == 'ideal':
        dir_name = 'BlockAssign_ST' + state_num + '_' + state_abbrev
        blockfile = pd.read_csv(dir_name + '/' + dir_name + '_VTD.txt', dtype=str)
        block_solution = pd.read_csv(state_abbrev + '_Congress.csv', names=['BLOCKID', 'DIST_NUM'], dtype=str)
        blockfile['GEOID10'] = state_num + blockfile.COUNTYFP + blockfile.DISTRICT # GEOID10 is VTD
        blockfile = blockfile.merge(block_solution, on = 'BLOCKID')
        blockfile = blockfile.groupby('GEOID10', group_keys=False).apply(lambda df: df.sample(1))

        state_vtds = state_vtds.merge(blockfile, on = 'GEOID10')

        # need to be really careful with how strings are handled here
        inclusion_matrix = [(state_vtds.DIST_NUM == str(dist_num)) for dist_num in range(0, int(max(blockfile.DIST_NUM)))] #using int on a max of a string is an abuse

        hard_version = True # i.e. geographical centroid vs. average of centroids

        crs = {'init': 'epsg:5070'}
        if hard_version:
            districts = state_vtds[['geometry', 'DIST_NUM']].to_crs(epsg=5070).groupby('DIST_NUM', as_index=False).apply(lambda df: reduce(lambda a, b: a.union(b), df.geometry))
            district_centroids = districts.apply(lambda poly: poly.centroid)
            district_centroids = gpd.GeoSeries(district_centroids, crs=crs).to_crs(epsg=4269)
        else:
            # need to use area times x/y coords to make this correct
            district_centroids = state_vtds[['geometry', 'DIST_NUM']].to_crs(epsg=5070).groupby('DIST_NUM', as_index=False).apply(lambda df: Point(pd.Series([poly.centroid.x for poly in df.geometry]).mean(), pd.Series([poly.centroid.y for poly in df.geometry]).mean()))
                #.reset_index(drop=True).to_crs(epsg=4269)

            district_centroids = gpd.GeoSeries(district_centroids, crs=crs).to_crs(epsg=4269)

    seg0 = time.time()
    print(seg0 - start)

    vtd_centroids = state_vtds.geometry.to_crs(epsg=5070).centroid.to_crs(epsg=4269)

    state_2016_vtd_pop = pd.read_csv('%s_vtd_pop.csv' % state_name, dtype={'GeoID2': str}).rename(columns = {'GeoID2': 'GEOID10'})
    state_vtds = state_vtds.merge(state_2016_vtd_pop, on = 'GEOID10')


    sum = 0

    for idx in range(0, len(inclusion_matrix)):
        district_centroid = district_centroids.iloc[idx]
        for cent_idx, vtd_centroid in enumerate(vtd_centroids[inclusion_matrix[idx]]):
            sum += state_vtds['Total Population'][inclusion_matrix[idx]].iloc[cent_idx]*haversine(vtd_centroid.x, vtd_centroid.y, district_centroid.x, district_centroid.y)

    state_pop = state_vtds['Total Population'].sum()
    compactness = sum / state_pop


    finish = time.time()
    print(finish - seg0)

    print "compactness: " + str(compactness)

    return compactness

