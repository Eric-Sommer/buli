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

    try:
        response = MyBrowser.urlopen(request)
    except:
        print("Request {} not possible".format(request))
        return ""

    print("Writing {}".format(targetfile))
    page = response.read()
    file = open(targetfile, "wb")
    file.write(page)
    file.close()

    return page


def clean_roster(roster):
    """ args: roster (string)

        returns a clean list of player names
    """
    red1 = roster.replace("Aufstellung: ", "")
    red2 = red1.replace("\xa0", "")
    red3 = re.sub("\(.+?\)", "", red2)
    red4 = red3.replace("-", " ")

    return red4.replace(",", " ").split()


def clean_sub(string):

    red1 = string.replace("Einwechslungen: ", "")
    red2 = re.sub("\(.+?\)", "", red1)
    red3 = red2.replace("\xa0", "")
    # The substituted player is before "für"
    red4 = re.findall(".+?\. (.+?) für", red3)

    return red4


def crawler(path, seasons):
    """ Crawls through the seasons
        If file is not there, it is downloaded.
    """

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

    game_results, goals = get_game_results(seasons, rawdir, path)

    return game_results, goals


def get_game_results(seasons, rawdir, path):
    """ converts html data into game results
    """
    print("Processing Game Results")
    # Initiatilize DataFrame
    buli_results = pd.DataFrame(
        columns=[
            "season",
            "spieltag",
            "hometeam",
            "awayteam",
            "homegoals",
            "awaygoals",
            "gamelink",
        ]
    )
    HomeRegEx = re.compile('class="ovVrn ovVrnRight">(.+?)</a>')
    AwayRegEx = re.compile('class="ovVrn">(.+?)</a>')
    HomeGoalsRegEx = re.compile(r'<td class="alignleft nowrap" >(\d*):')
    AwayGoalsRegEx = re.compile(r'<td class="alignleft nowrap" >\d*:(\d*)&nbsp;')

    for s in seasons:
        print(str(s), end=" ")
        for sp in range(1, 35):
            html = open("{}/kicker_{}_{}.html".format(rawdir, s, sp),
                "r",
                encoding="utf-8",
            ).read()
            # find hometeam, awayteam, result in string.
            hometeam = []
            awayteam = []
            homegoals = []
            awaygoals = []
            gamelink = []

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
                data=[
                    [s] * 9,
                    [sp] * 9,
                    hometeam,
                    awayteam,
                    homegoals,
                    awaygoals,
                    gamelink,
                ]
            ).T
            spt = spt.rename(
                columns={
                    0: "season",
                    1: "spieltag",
                    2: "hometeam",
                    3: "awayteam",
                    4: "homegoals",
                    5: "awaygoals",
                    6: "gamelink",
                }
            )
            buli_results = buli_results.append(spt, ignore_index=True)

    buli_results["game_id"] = buli_results.index
    buli_results = buli_results[buli_results["gamelink"] != ""]

    # initiate goals data frame
    goals = pd.DataFrame(columns=["game_id", "goal_nr", "scorer", "minute"])
    rosters = pd.DataFrame(
        columns=["game_id", "home_starting", "home_substi", "away_substi"]
    )

    # Download game details.

    for g, gid in zip(buli_results["gamelink"], buli_results["game_id"]):
        if g != "":
            gamefile = "{}game_{}.html".format("data/games/", gid)

            request = MyBrowser.Request("http://www.kicker.de{}".format(g))
            if not os.path.exists(gamefile):
                html = dl_and_save(gamefile, request)
            else:
                html = open(
                    "data/games/game_{}.html".format(gid), "r", encoding="utf-8"
                ).read()
            if html != "":
                if (gid % 50) == 0:
                    print(
                        "Processing Matchday {} Season {}".format(
                            buli_results["spieltag"][
                                buli_results["game_id"] == gid
                            ].max(),
                            buli_results["season"][
                                buli_results["game_id"] == gid
                            ].max(),
                        )
                    )
                goals_one_g, roster_one_g = get_game_details(html, gid)

                goals = goals.append(goals_one_g, ignore_index=True)
                rosters = rosters.append(roster_one_g, ignore_index=True)

    # save raw data
    buli_results.to_json(path + "all_game_results_since{}.json".format(seasons[0]))
    goals.to_json(path + "all_goals_since{}.json".format(seasons[0]))
    rosters.to_json(path + "all_rosters_since{}.json".format(seasons[0]))

    return buli_results, goals


def get_game_details(html, game_id):
    """ returns a dataframe with the following items from the particular game.

        goals = [nr of goal, name of scorer, minute, owngoal-Dummy]
        roster = [homestarting, awaystarting, homesubs, awaysubs]
    """
    gnr = 0
    game = BeautifulSoup(html, "lxml")
    rosters = {}
    # FETCH ROSTERS
    html_tags_start = {"homeroster": "ausstellungHeim", "awayroster": "ausstellungAusw"}
    html_tags_sub = {"homesub": "einwechslungenHeim", "awaysub": "einwechslungenAusw"}

    for roster, s in html_tags_start.items():
        rosters[roster] = clean_roster(
            game.find_all("div", {"id": "ctl00_PlaceHolderHalf_ctl00_" + s})[0]
            .contents[1]
            .text
        )

    for roster, s in html_tags_sub.items():
        try:
            rosters[roster] = clean_sub(
                game.find_all("div", {"id": "ctl00_PlaceHolderHalf_ctl00_" + s})[0]
                .contents[1]
                .text
            )
        except IndexError:
            rosters[roster] = []

    # FETCH GOALS
    ScorerRegEx = r"spieler_(.+?).html"
    goal_nr = []
    scorer = []
    minute = []
    eg = []

    # loop through all goals
    for bit in game.find_all("div", {"class": "spieler"}):
        gnr += 1
        goal_nr.append(gnr)
        # the first entry is the scorer, the second one the assist (if available)
        scorer.append(re.findall(ScorerRegEx, str(bit))[0])
        minute.append(int(re.findall(r"\((\d+)\.", str(bit))[0]))
        try:
            egstring = re.findall(r"\(\d+\., (.+?),", str(bit))[0]
            if egstring == "Eigentor":
                eg.append(True)
            else:
                eg.append(False)
        except IndexError:
            eg.append(False)

    goals = pd.DataFrame(
        {"goal_nr": goal_nr, "scorer": scorer, "minute": minute, "owngoal": eg}
    )
    goals["game_id"] = game_id

    rosters = pd.DataFrame(
        {
            "game_id": game_id,
            "home_starting": [rosters["homeroster"]],
            "away_starting": [rosters["awayroster"]],
            "home_substi": [rosters["homesub"]],
            "away_substi": [rosters["awaysub"]],
        }
    )
    return goals, rosters
