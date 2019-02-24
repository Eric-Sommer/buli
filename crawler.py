# -*- coding: utf-8 -*-
"""
CRAWLING KICKER.DE
"""
import urllib.request as MyBrowser
import os
import re
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup

def correct_names(str_list):
    res = list(str_list)
    tmp_lst = list(str_list)
    # for s,t in str_list.iteritems():
    for s in range(0, len(str_list)):
        if tmp_lst[s] == "Meidericher SV":
            res[s] = "Duisburg"
        if tmp_lst[s] == "Waldhof":
            res[s] = "Waldhof Mannheim"
        if tmp_lst[s] == "Haching":
            res[s] = "Unterhaching"
    return res


def mkURL(season, spieltag):
    seasonstring = str(season) + "-" + str(season + 1)[-2:]
    url = "http://www.kicker.de/news/fussball/bundesliga/spieltag/1-bundesliga/{}/{}/spieltag.html".format(
        seasonstring, spieltag
    )
    return url


def dl_and_save(targetfile, request):
    """ carries out a HTML request and saves the response to HD
    """
    print("Writing {}".format(targetfile))
    response = MyBrowser.urlopen(request)
    page = response.read()
    file = open(targetfile, "wb")
    file.write(page)
    file.close()

    return page

def crawler(path, seasons):
    datadir = path + "data/"
    if not os.path.exists(datadir):
        os.mkdir(datadir)

    rawdir = datadir + "raw/"
    if not os.path.exists(rawdir):
        os.mkdir(rawdir)

    for s in seasons:
        print("Downloading season " + str(s) + "...")
        for sp in range(1, 35):
            request = MyBrowser.Request(mkURL(s, sp))

            rawfile = "{}kicker_{}_{}.html".format(rawdir, s, sp)
            if not os.path.exists(rawfile):
                html = dl_and_save(rawfile, request)

    print("Finished Downloading")

    game_results = get_game_results(seasons, rawdir, path)

    return game_results


def get_game_results(seasons, rawdir, path):
    """ converts html data into game results
    """
    print("Processing Game Results")
    # Initiatilize DataFrame
    buli_results = pd.DataFrame(
        columns=["season",
                 "spieltag",
                 "hometeam",
                 "awayteam",
                 "homegoals",
                 "awaygoals",
                 "gamelink"
                 ]
    )
    for s in seasons:
        print(str(s), end=" ")
        for sp in range(1, 35):
            html = open(
                rawdir + "/kicker_" + str(s) + "_" + str(sp) + ".html",
                "r",
                encoding="utf-8",
            ).read()
            # find hometeam, awayteam, result in string.
            hometeam = []
            awayteam = []
            homegoals = []
            awaygoals = []
            gamelink = []
            HomeRegEx = re.compile('class="ovVrn ovVrnRight">(.+?)</a>')
            AwayRegEx = re.compile('class="ovVrn">(.+?)</a>')
            HomeGoalsRegEx = re.compile(r'<td class="alignleft nowrap" >(\d*):')
            AwayGoalsRegEx = re.compile(
                r'<td class="alignleft nowrap" >\d*:(\d*)&nbsp;'
            )
            GameLinkRegEx = re.compile('class="link" href="(.+?)">Analyse')

            for match in HomeRegEx.finditer(html):
                hometeam.append(match.group(1))
            for match in AwayRegEx.finditer(html):
                awayteam.append(match.group(1))
            for match in HomeGoalsRegEx.finditer(html):
                homegoals.append(match.group(1))
            for match in AwayGoalsRegEx.finditer(html):
                awaygoals.append(match.group(1))
            for match in GameLinkRegEx.finditer(html):
                gamelink.append(match.group(1))

            spt = pd.DataFrame(
                data=[[s] * 9, [sp] * 9, hometeam, awayteam, homegoals, awaygoals, gamelink]
            ).T
            spt = spt.rename(
                columns={
                    0: "season",
                    1: "spieltag",
                    2: "hometeam",
                    3: "awayteam",
                    4: "homegoals",
                    5: "awaygoals",
                    6: "gamelink"
                }
            )
            buli_results = buli_results.append(spt, ignore_index=True)

    buli_results['game_id'] = buli_results.index
    # initiate goals data frame
    goals = pd.DataFrame(columns = ['game_id',
                                    'goal_nr',
                                    'scorer',
                                    'minute'
                                    ])
    # Download game details
    print(buli_results[['gamelink', 'game_id']].head())
    for g, gid in zip(buli_results['gamelink'], buli_results['game_id']):
        gamefile = "{}game_{}.html".format('data/games/',
                    gid)
        request = MyBrowser.Request('http://www.kicker.de{}'.format(g))
        if not os.path.exists(gamefile):
            dl_and_save(gamefile, request)
        # Now
        html = open('data/games/game_{}.html'.format(gid),
                "r",
                encoding="utf-8",
            ).read()
        goals_one_g = get_game_details(html, gid)
        goals_one_g['game_id'] = gid

        goals = goals.append(goals_one_g, ignore_index=True)

    # save raw data
    buli_results.to_json(path + "all_game_results.json")
    goals.to_json(path + "all_goals.json")

    print(goals)

    return buli_results


def get_game_details(html, game_id):
    gnr = 0
    out = pd.DataFrame(columns = ['goal_nr',
                                  'scorer',
                                  'minute'])
    game = BeautifulSoup(html, 'lxml')
    ScorerRegEx = r'spieler_(.+?).html'
    goal_nr = []
    scorer = []
    minute = []
    # loop through all goals
    for bit in game.find_all("div", {"class": "spieler"}):
        gnr += 1
        goal_nr.append(gnr)
        # the first entry is the scorer, the second one the assist (if available)
        scorer.append(re.findall(ScorerRegEx, str(bit))[0])
        minute.append(int(re.findall(r'\((\d+)\.', str(bit))[0]))

    out = out.append(pd.DataFrame({'goal_nr': goal_nr,
                                   'scorer': scorer,
                                   'minute': minute},
        ), ignore_index=True)

    return out