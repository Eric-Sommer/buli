# -*- coding: utf-8 -*-
"""
CRAWLING KICKER.DE
"""
import os
import re
import time
import urllib.request as MyBrowser
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
        if tmp_lst[s] == "Blau-Weiß 90 Ber.":
            res[s] = "Blau-Weiß 90 Berlin"
        if tmp_lst[s] == "TSV 1860":
            res[s] = "1860 München"
        if tmp_lst[s] == "HSV":
            res[s] = "Hamburger SV"

    return res


def mkURL(season, spieltag, liga):
    ligastr1 = {1: "bundesliga", 2: "2bundesliga", 3: "3-liga"}
    ligastr2 = {1: "1-bundesliga", 2: "2-bundesliga", 3: "3-liga"}
    seasonstring = str(season) + "-" + str(season + 1)[-2:]
    url = "http://www.kicker.de/news/fussball/{}/spieltag/{}/{}/{}/spieltag.html".format(
        ligastr1[liga], ligastr2[liga], seasonstring, spieltag
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


def crawler(path, seasons, liga, resultsonly=False):
    """ Crawls through the seasons.
        1. Download game results if not yet existent
            - assign game_id
            - collect link to match information
        2. process game results and export to HD
        3. download match details if not yet existent
        4. process match details
            - lineups
            - goals
            - bookings
            - other (date, place, attendance, referee)
    """
    print(f"CRAWLING LIGA {liga} FROM {seasons[0]} to {seasons[-1]}")
    datadir = f"{path}/data/league_{liga}"
    if not os.path.exists(datadir):
        os.mkdir(datadir)

    if not os.path.exists(f"{datadir}/games"):
        os.mkdir(f"{datadir}/games")

    rawdir = f"{datadir}/raw/"
    if not os.path.exists(rawdir):
        os.mkdir(rawdir)

    for s in seasons:
        print(f"Downloading season {s}...")
        if (
            (liga == 3)
            or ((liga == 1) and (s == 1991))
            or ((liga == 2) and (s <= 1993))
        ):
            n_matchdays = 38
        else:
            n_matchdays = 34

        for sp in range(1, n_matchdays + 1):
            request = MyBrowser.Request(mkURL(s, sp, liga))

            rawfile = f"{rawdir}kicker_{s}_{sp}.html"
            # print(f"{mkURL(s, sp, liga)} to {rawfile}.")
            if not os.path.exists(rawfile):
                dl_and_save(rawfile, request)

    print("Finished Downloading Match Results")

    get_game_results(seasons, rawdir, path, liga, resultsonly)


def get_game_results(seasons, rawdir, path, liga, resultsonly):
    """ converts html data into game results
    """
    print("Processing Match Results \n")
    # Initialize DataFrame
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
    TeamRegEx = '<div class="kick__v100-gameCell__team__shortname">(.+?) <span'
    ScoreRegEx = """<div class="kick__v100-scoreBoard__scoreHolder ">
            <div class="kick__v100-scoreBoard__scoreHolder__score">(\d*)</div>
            <div class="kick__v100-scoreBoard__scoreHolder__divider">:</div>
            <div class="kick__v100-scoreBoard__scoreHolder__score">(\d*)</div>
        </div>"""
    GameLinkRegEx = re.compile(
        '<a href="(.+?)" class="kick__v100-scoreBoard kick__v100'
    )

    for s in seasons:
        # how many matches per matchday?
        if (
            (liga == 3)
            or ((liga == 1) and (s == 1991))
            or ((liga == 2) and (s == 1993))
        ):
            n_matches = 10
            spieltage = 38
        elif (liga == 1) & (s <= 1964):
            n_matches = 8
            spieltage = 30
        else:
            n_matches = 9
            spieltage = 34

        print(f"{s} ")
        for sp in range(1, spieltage + 1):
            html_raw = open(
                f"{rawdir}/kicker_{s}_{sp}.html", "r", encoding="utf-8"
            ).read()
            # Kick out postponed games
            html = html_raw.split("Verlegte Spielpaarungen")[0]

            try:
                all_teams = np.array(re.findall(TeamRegEx, html)).reshape(
                    (n_matches, 2)
                )
            except ValueError:
                print(
                    f"something wrong with the number of matches. Season {s}, Matchday {sp}."
                )
            score = np.array(re.findall(ScoreRegEx, html))
            gamelink = re.findall(GameLinkRegEx, html)

            spt = pd.DataFrame(
                data=[
                    [s] * n_matches,
                    [sp] * n_matches,
                    all_teams[:, 0],
                    all_teams[:, 1],
                    score[:, 0],
                    score[:, 1],
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
    if not resultsonly:
        buli_results = buli_results[buli_results["gamelink"] != ""]
        buli_results = buli_results[~buli_results["gamelink"].isna()]
        # Check for duplicate entries. Postponed matches sometimes appear several times
        # kick one of them
        occ = buli_results.groupby("gamelink")["game_id"].cumcount()
        buli_results = buli_results[occ == 0]
    # export
    print(buli_results["season"].value_counts())
    buli_results.to_csv(
        os.path.join(
            path, f"data/league_{liga}/all_game_results_since{seasons[0]}.csv"
        ),
        index=False,
    )
    if not resultsonly:
        # initiate game-specific data frames
        goals = pd.DataFrame(columns=["game_id", "goal_nr", "scorer", "minute"])
        rosters = pd.DataFrame(
            columns=["game_id", "player_id", "player_name", "role", "minute"]
        )
        game_details = pd.DataFrame(
            columns=["game_id", "date", "stadium", "attendance", "schiri"]
        )
        bookings = pd.DataFrame(columns=["game_id", "yellow", "yellowred", "red"])

        # Download game-specific informations.
        for g, gid in zip(buli_results["gamelink"], buli_results["game_id"]):
            # check for link being a nonempty string
            if g != "" and isinstance(g, str):
                gamefile = f"data/league_{liga}/games/game_{gid}.html"

                request = MyBrowser.Request(f"http://www.kicker.de{g}")
                if not os.path.exists(gamefile):
                    html = dl_and_save(gamefile, request)
        tt = pd.Series()
        print("Processing Match Details... \n")
        # After downloading, process the stuff
        for g, gid in zip(buli_results["gamelink"], buli_results["game_id"]):
            html = open(
                f"data/league_{liga}/games/game_{gid}.html", "r", encoding="utf-8"
            ).read()
            tt = tt.append(pd.Series(time.perf_counter()))
            show_remaining_time(buli_results["game_id"].max(), gid, tt)

            goals_one_g, game_details_one_g, bookings_one_g = get_game_details(
                html, gid, s
            )
            goals = goals.append(goals_one_g, ignore_index=True)

            home_start, away_start, home_sub, away_sub = get_lineups(html, gid)
            lineup = pd.DataFrame(
                columns=["player_id", "player_name", "role", "minute"]
            )
            try:
                for var in ["player_id", "player_name"]:
                    lineup[var] = (
                        list(home_start[var])
                        + list(away_start[var])
                        + list(home_sub[var])
                        + list(away_sub[var])
                    )
                lineup["role"] = (
                    ["home_start" for i in range(len(home_start))]
                    + ["away_start" for i in range(len(away_start))]
                    + ["home_sub" for i in range(len(home_sub))]
                    + ["away_sub" for i in range(len(away_sub))]
                )
                lineup["minute"] = (
                    [np.nan for i in range(len(home_start) + len(away_start))]
                    + list(home_sub["minute"])
                    + list(away_sub["minute"])
                )
                lineup["game_id"] = gid
            except TypeError:
                pass

            rosters = rosters.append(lineup, ignore_index=True)
            game_details = game_details.append(game_details_one_g, ignore_index=True)
            bookings = bookings.append(bookings_one_g, ignore_index=True)
            # name the dfs
            goals.name = "goals"
            rosters.name = "rosters"
            game_details.name = "match_details"
            bookings.name = "bookings"

        # save raw data
        for df in [goals, rosters, game_details, bookings]:
            export_to_csv(df, path, liga, seasons[0])

    return buli_results


def get_lineups(html, game_id):

    game = BeautifulSoup(html, "lxml")

    lineups = {}
    # FETCH LINEUPS
    html_tags_start = {"homelineup": "ausstellungHeim", "awaylineup": "ausstellungAusw"}
    html_tags_sub = {"homesub": "einwechslungenHeim", "awaysub": "einwechslungenAusw"}

    lineupregex = r"""<div class="spielerdiv"><a class="link_noicon" href=".+?/(\d+)/
    spieler_(.+?).html">.+?</div>"""
    subregex = r'<span>(\d+)\. .+?<a class="link_noicon" href=".+?/(\d+)/spieler_(.+?).html">.+?</div>'
    for lineup, s in html_tags_start.items():
        try:
            lineups[lineup] = clean_roster(
                re.findall(
                    lineupregex,
                    str(
                        game.find_all(
                            "div", {"id": "ctl00_PlaceHolderHalf_ctl00_" + s}
                        )[0].contents[1]
                    ),
                ),
                game_id,
            )
        except IndexError:
            print(f"Warning: Something wrong with {s} in Match {game_id}")
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
            lineups[lineup] = pd.DataFrame(
                columns=["minute", "player_id", "player_name"]
            )

    return (
        lineups["homelineup"],
        lineups["awaylineup"],
        lineups["homesub"],
        lineups["awaysub"],
    )


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

    try:
        other_game_details = pd.DataFrame(
            {
                "game_id": game_id,
                "date": re.findall(
                    'wert">(.+?)</div',
                    str(
                        game.find_all(
                            "div", {"id": f"ctl00_PlaceHolderHalf_ctl0{num}_anstoss"}
                        )[0]
                    ),
                )[0],
                "stadium": re.findall(
                    'wert">(.+?)</div',
                    str(
                        game.find_all(
                            "div", {"id": f"ctl00_PlaceHolderHalf_ctl0{num}_stadion"}
                        )[0]
                    ),
                )[0],
                "attendance": int(
                    re.findall(
                        'wert">(\d+).*</div',
                        str(
                            game.find_all(
                                "div",
                                {"id": f"ctl00_PlaceHolderHalf_ctl0{num}_zuschauer"},
                            )[0]
                        ),
                    )[0]
                ),
                "schiri": re.findall(
                    ">(.+?)</a>",
                    str(
                        game.find_all(
                            "div",
                            {"id": f"ctl00_PlaceHolderHalf_ctl0{num}_schiedsrichter"},
                        )[0]
                    ),
                )[0],
            },
            index=[game_id],
        )
    except IndexError:
        print(f"Error in fetching match details for id {game_id}")
        other_game_details = pd.DataFrame(
            columns=["game_id", "date", "stadium", "attendance", "schiri"]
        )
    # Finally, fetch bookings
    html_tags_bookings = {
        "yellow": "ctl00_PlaceHolderHalf_ctl01_gelb2",
        "yellowred": "ctl00_PlaceHolderHalf_ctl01_gelbrot2",
        "red": "ctl00_PlaceHolderHalf_ctl01_rot2",
    }
    regex_bookings = {
        "yellow": ScorerRegEx,
        "yellowred": ScorerRegEx,
        "red": '<\/div><a.*?href=".+?\/(\d+?)\/spieler_.+?.html"',
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
                str(game.find_all("tr", {"id": html_tags_bookings["red"]})),
            ),
        )
    )

    bookings = pd.DataFrame(
        {"game_id": game_id, "yellow": [yellow], "yellowred": [yellowred], "red": [red]}
    )

    return goals, other_game_details, bookings


def export_to_csv(df, path, liga, s0):
    filename = f"{path}/data/league_{liga}/all_{df.name}_since{s0}.csv"
    print(f"Saving {filename}")
    df.to_csv(filename, index=False)


def show_remaining_time(N, gid, tt):
    REM_TIME = (N - gid) * (tt.iloc[-10:].diff().mean())
    if gid % 10 == 0:
        print(
            "Match {0} / {1} ({2:.0f}:{3:02.0f} remaining)".format(
                gid, N, REM_TIME // 60, REM_TIME - (REM_TIME // 60 * 60)
            )
        )
