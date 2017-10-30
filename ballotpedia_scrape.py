import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

work_dir = '/Users/paullindseth/Downloads/'
os.chdir(work_dir)


def get_efficiency(state_name, num_districts):

    wasted_votes = 0  # + is D, - is R

    total_votes = 0

    for i in range(num_districts):
        dist_num = i+1
        # ordinal = 'th'
        # if dist_num % 10 == 1:
        #     ordinal = 'st'
        # elif dist_num % 10 == 2:
        #     ordinal = 'nd'
        # elif dist_num % 10 == 3:
        #     ordinal = 'rd'

        # https://stackoverflow.com/questions/9647202/ordinal-numbers-replacement
        ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(n / 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])

        num_ordinal = ordinal(dist_num)

        possessive = 's'

        if state_name[-1:] == 's':
            possessive = ''

        URL = "https://ballotpedia.org/" + state_name + "%27" + possessive + "_" + num_ordinal + "_Congressional_District_election,_2016"

        print URL

        req = requests.get(URL)
        soup = BeautifulSoup(req.content, 'lxml')
        table_ids = {"class": ["collapsible"]}
        tables = soup.findAll("table", table_ids)
        df = pd.read_html(str(tables[0]), skiprows=[0,1])
        df = df[0]



        ####
        dem_v = 0
        rep_v = 0

        for index, row in df.iterrows():
            if row[1] == 'Democratic':
                temp = row[4]
                if type(temp) is str:
                    temp = int(temp.replace(',',''))

                dem_v = temp
            elif row[1] == 'Republican':
                temp = row[4]
                if type(temp) is str:
                    temp = int(temp.replace(',',''))
                rep_v = temp

            if row[0] == 'Total Votes':
                temp = row[1]
                if type(temp) is str:
                    temp = int(temp.replace(',',''))
                district_total = temp

        if state_name == 'Florida' and dist_num == 24:
            dem_v = 64845
            rep_v = 0
            district_total = 0

        if state_name == 'Oklahoma' and dist_num == 1:
            dem_v = 0
            rep_v = 62655
            district_total = rep_v

        print dem_v
        print rep_v
        print district_total

        if dem_v > rep_v:
            wasted_votes += (dem_v - rep_v) / 2
            wasted_votes -= rep_v
        else:
            wasted_votes -= (rep_v - dem_v) / 2
            wasted_votes += dem_v

        total_votes += district_total

    return wasted_votes / total_votes
