# -*- coding: utf-8 -*-
"""
CRAWLING KICKER.DE
"""
import urllib.request as MyBrowser
import os
import re
import pandas as pd
import numpy as np

seasons = list(range(1963, 2019))

def correct_names(str_list):
    res = list(str_list)
    tmp_lst = list(str_list)
    # for s,t in str_list.iteritems():                       
    for s in range(0, len(str_list)):
        if tmp_lst[s] == 'Meidericher SV':
            res[s] = 'Duisburg'
        if tmp_lst[s] == 'Waldhof':
            res[s] = 'Waldhof Mannheim'
        if tmp_lst[s] == 'Haching':
            res[s] = 'Unterhaching'
    return res


def mkURL(season, spieltag):
    seasonstring = str(season) + '-' + str(season+1)[-2:]
    url = ("http://www.kicker.de/news/fussball/bundesliga/spieltag/1-bundesliga/" +
           seasonstring +
           '/' + str(spieltag) + '/0/spieltag.html')
    return url


def crawler(path):
    datadir = path + 'data/'
    if not os.path.exists(datadir):
        os.mkdir(datadir)

    rawdir = datadir + 'raw/'
    if not os.path.exists(rawdir):
        os.mkdir(rawdir)

    for s in seasons:
        print('Downloading season ' + str(s) + '...')
        for sp in range(1,35):
            request = MyBrowser.Request((mkURL(s, sp)))

            rawfile = rawdir + 'kicker_' + str(s) + '_' + str(sp) + ".html"
            if not os.path.exists(rawfile):
                response = MyBrowser.urlopen(request)
                page = response.read()
                file = open(rawfile, "wb")
                file.write(page)
                file.close()

    print("Finished Downloading")

    buli_results = pd.DataFrame(columns=['season',
                                         'spieltag',
                                         'hometeam',
                                         'awayteam',
                                         'homegoals',
                                         'awaygoals'])
    for s in seasons:
        print(str(s), end=' ')
        for sp in range(1, 35):
            html = open(rawdir +
                        '/kicker_' +
                        str(s) + '_' + str(sp) + ".html",
                        "r",
                        encoding="utf-8").read()
            # find hometeam, awayteam, result in string.
            hometeam = []
            awayteam = []
            homegoals = []
            awaygoals = []
            HomeRegEx = re.compile('class="ovVrn ovVrnRight">(.+?)</a>')
            AwayRegEx = re.compile('class="ovVrn">(.+?)</a>')
            HomeGoalsRegEx = re.compile('<td class="alignleft nowrap" >(\d*):')
            AwayGoalsRegEx = re.compile('<td class="alignleft nowrap" >\d*:(\d*)&nbsp;')            

            for match in HomeRegEx.finditer(html):
                hometeam.append(match.group(1))
            for match in AwayRegEx.finditer(html):
                awayteam.append(match.group(1))
            for match in HomeGoalsRegEx.finditer(html):
                homegoals.append(match.group(1))
            for match in AwayGoalsRegEx.finditer(html):
                awaygoals.append(match.group(1))

            spt = pd.DataFrame(data=[[s]*9,
                                     [sp]*9,
                                     hometeam,
                                     awayteam,
                                     homegoals,
                                     awaygoals]).T
            spt = spt.rename(columns={0: 'season',
                                      1: 'spieltag',
                                      2: 'hometeam',
                                      3: 'awayteam',
                                      4: 'homegoals',
                                      5: 'awaygoals'})
            buli_results = buli_results.append(spt, ignore_index=True)            

    # save raw data        
    buli_results.to_json(path + 'all_kicker_results.json')

    return buli_results    