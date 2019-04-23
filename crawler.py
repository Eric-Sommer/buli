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


def clean_roster(roster, gid, sub=False):
    """ args: roster (string)

        returns a list of player id's and names
    """

    if sub:
        df = pd.DataFrame(roster, columns=["minute", "player_id", "player_name"])
        df["minute"] = df["minute"].astype(int)
        try:
            assert len(df) <= 3
        except AssertionError:
            print("Warning: Too many substituions in Game {}".format(gid))

    else:
        df = pd.DataFrame(roster, columns=["player_id", "player_name"])
        try:
            assert len(df) == 11
        except AssertionError:
            print("Warning: Too many players in one team in Game {}".format(gid))

    df["player_id"] = df["player_id"].astype(int)

    return df


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
                dl_and_save(rawfile, request)

    print("Finished Downloading Match Results")

    game_results, goals = get_game_results(seasons, rawdir, path)

    return game_results, goals


def get_game_results(seasons, rawdir, path):
    """ converts html data into game results
    """
    print("Processing Match Results")
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
            html = open(
                "{}/kicker_{}_{}.html".format(rawdir, s, sp), "r", encoding="utf-8"
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
    # clean
    buli_results = buli_results[buli_results["gamelink"] != ""]
    buli_results = buli_results[~buli_results["gamelink"].isna()]
    # export
    buli_results.to_csv(path + "data/all_game_results_since{}.csv".format(seasons[0]), index=False)

    # initiate game-specific data frames
    goals = pd.DataFrame(columns=["game_id", "goal_nr", "scorer", "minute"])
    rosters = pd.DataFrame(
        columns=["game_id", "player_id", "player_name", "role", "minute"]
    )
    game_details = pd.DataFrame(columns=["game_id", "date", "stadium", "attendance", "schiri"])
    bookings = pd.DataFrame(columns=["game_id", "yellow", "yellowred", "red"])

    # Downloadgame-specific informations.
    for g, gid in zip(buli_results["gamelink"], buli_results["game_id"]):
        # check for link being a nonempty string
        if g != "" and isinstance(g, str):
            gamefile = "{}game_{}.html".format("data/games/", gid)

            request = MyBrowser.Request("http://www.kicker.de{}".format(g))
            if not os.path.exists(gamefile):
                html = dl_and_save(gamefile, request)

    # After downloading, process the stuff
    for g, gid in zip(buli_results["gamelink"], buli_results["game_id"]):
        html = open(
                "data/games/game_{}.html".format(gid), "r", encoding="utf-8"
                ).read()
        print("Match {} / {}".format(gid, len(buli_results)))
        goals_one_g, game_details_one_g, bookings_one_g = get_game_details(
            html, gid, s
        )
        goals = goals.append(goals_one_g, ignore_index=True)

        home_start, away_start, home_sub, away_sub = get_lineups(html, gid)
        lineup = pd.DataFrame(columns=['player_id', 'player_name', 'role', 'minute'])
        try:
            for var in ['player_id', 'player_name']:
                lineup[var] = (list(home_start[var]) +
                               list(away_start[var]) +
                               list(home_sub[var]) +
                               list(away_sub[var])
                               )
            lineup['role'] = (['home_start' for i in range(len(home_start))] +
                              ['away_start' for i in range(len(away_start))] +
                              ['home_sub' for i in range(len(home_sub))] +
                              ['away_sub' for i in range(len(away_sub))])
            lineup['minute'] = ([np.nan for i in range(len(home_start) +
                                                    len(away_start))] +
                                list(home_sub['minute']) +
                                list(away_sub['minute'])
                                )
            lineup['game_id'] = gid
        except TypeError:
            pass

        rosters = rosters.append(lineup, ignore_index=True)
        game_details = game_details.append(
            game_details_one_g, ignore_index=True
        )
        bookings = bookings.append(bookings_one_g, ignore_index=True)

    # save raw data

    goals.to_csv(path + "data/all_goals_since{}.csv".format(seasons[0]), index=False)
    rosters.to_csv(path + "data/all_rosters_since{}.csv".format(seasons[0]), index=False)
    game_details.to_csv(path + "data/match_details_since{}.csv".format(seasons[0]), index=False)
    bookings.to_csv(path + "data/bookings_since{}.csv".format(seasons[0]), index=False)

    return buli_results, goals

def get_lineups(html, game_id):

    game = BeautifulSoup(html, "lxml")

    lineups = {}
    # FETCH LINEUPS
    html_tags_start = {"homelineup": "ausstellungHeim", "awaylineup": "ausstellungAusw"}
    html_tags_sub = {"homesub": "einwechslungenHeim", "awaysub": "einwechslungenAusw"}

    lineupregex = '<div class="spielerdiv"><a class="link_noicon" href=".+?/(\d+)/spieler_(.+?).html">.+?</div>'
    subregex = '<span>(\d+)\. .+?<a class="link_noicon" href=".+?/(\d+)/spieler_(.+?).html">.+?</div>'
    for lineup, s in html_tags_start.items():
        try:
            lineups[lineup] = clean_roster(
                re.findall(
                    lineupregex,
                    str(
                        game.find_all("div", {"id": "ctl00_PlaceHolderHalf_ctl00_" + s})[
                            0
                        ].contents[1]
                    ),
                ),
                game_id,
            )
        except IndexError:
            print("Warning: Something wrong with {} in Match {}".format(s, game_id))
            lineups[lineup] = []

    for lineup, s in html_tags_sub.items():
        try:
            lineups[lineup] = clean_roster(
                re.findall(
                    subregex,
                    str(
                        game.find_all(
                            "div", {"id": "ctl00_PlaceHolderHalf_ctl00_" + s}
                        )[0].contents[1]
                    ),
                ),
                game_id,
                sub=True,
            )
        # maybe there are no substitutions -> create empty data frame
        except IndexError:
            lineups[lineup] = pd.DataFrame(columns=['minute', 'player_id', 'player_name'])

    return lineups['homelineup'], lineups['awaylineup'], lineups['homesub'], lineups['awaysub']


def get_game_details(html, game_id, season):
    """ returns dataframes with the following items from the particular game.

        goals = [nr of goal, id of scorer, minute, owngoal-Dummy]
        other_game_details = [date,
                             name of stadium,
                             attendance
                             name of referee
                             ]
        bookings (yellow, yellow-red, red cards with list of player ids)

    """

    game = BeautifulSoup(html, "lxml")

    # FETCH GOALS
    ScorerRegEx = 'href=".+?/(\d+?)/spieler_.+?.html"'
    goal_nr = []
    scorer = []
    minute = []
    eg = []
    gnr = 0
    # loop through all goals
    for bit in game.find_all("div", {"class": "spieler"}):
        gnr += 1
        goal_nr.append(gnr)
        # the first entry is the scorer id, the second one the assist (if available)
        scorer.append(int(re.findall(ScorerRegEx, str(bit))[0]))
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
    # Sometimes, you need a '3', sometimes a '4'

    if game.find_all("div", {"id": "ctl00_PlaceHolderHalf_ctl03_stadion"}) == []:
        num = 4
    else:
        num = 3

    other_game_details = pd.DataFrame(
        {
            "game_id": game_id,
            "date": re.findall('wert">(.+?)</div',
                               str(game.find_all("div",
                                                 {"id": "ctl00_PlaceHolderHalf_ctl0{}_anstoss".format(num)},
                                                 )[0]
                ),
                )[0],
            "stadium": re.findall(
                'wert">(.+?)</div',
                str(
                    game.find_all(
                        "div",
                        {"id": "ctl00_PlaceHolderHalf_ctl0{}_stadion".format(num)},
                    )[0]
                ),
            )[0],
            "attendance": int(
                re.findall(
                    'wert">(\d+).*</div',
                    str(
                        game.find_all(
                            "div",
                            {
                                "id": "ctl00_PlaceHolderHalf_ctl0{}_zuschauer".format(
                                    num
                                )
                            },
                        )[0]
                    ),
                )[0]
            ),
            "schiri": re.findall(
                ">(.+?)</a>",
                str(
                    game.find_all(
                        "div",
                        {
                            "id": "ctl00_PlaceHolderHalf_ctl0{}_schiedsrichter".format(
                                num
                            )
                        },
                    )[0]
                ),
            )[0],
        },
        index=[game_id],
    )
    # Finally, fetch bookings
    html_tags_bookings = {
        "yellow": "ctl00_PlaceHolderHalf_ctl01_gelb2",
        "yellowred": "ctl00_PlaceHolderHalf_ctl01_gelbrot2",
        "red": "ctl00_PlaceHolderHalf_ctl01_rot2",
    }
    regex_bookings = {"yellow": ScorerRegEx,
                      "yellowred": ScorerRegEx,
                      "red": '<\/div><a.*?href=\".+?\/(\d+?)\/spieler_.+?.html\"'
                      }
    yellow = list(
        map(
            int,
            re.findall(
                regex_bookings["yellow"],
                str(game.find_all("tr", {"id": html_tags_bookings["yellow"]})),
            ),
        )
    )
    yellowred = list(
        map(
            int,
            re.findall(
                regex_bookings["yellowred"],
                str(game.find_all("tr", {"id": html_tags_bookings["yellowred"]})),
            ),
        )
    )
    red = list(
        map(
            int,
            re.findall(
                regex_bookings["red"],
                str(game.find_all("tr", {"id": html_tags_bookings["red"]}))
            ),
        )
    )

    bookings = pd.DataFrame(
        {"game_id": game_id, "yellow": [yellow], "yellowred": [yellowred], "red": [red]}
    )

    return goals, other_game_details, bookings
