#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Analyze historical Bundesliga results
#
########################################

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from functions import get_full_team_names
from crawler import crawler, correct_names

# SWITCHES

# Crawl and reproduce data?
CRAWL = 1

SEASONS_TO_CRAWL = list(range(1963, 2022))
PATH = os.getcwd()

# SET VARIABLES FOR OUTPUT
TEAMNAME = "Freiburg"
SPIELTAG = 22
TEAM_POINTS = 42


def make_boxplot_by_spieltag(df):
    """ Produces Boxplot showing the distribution of points by rank for a given matchday
    """
    for sp in range(30, 35):
        plt.clf()
        fig = plt.figure(figsize=(10, 5))
        plt.boxplot(
            [
                df["points_cum"][(df["spieltag"] == sp) & (df["rank"] == r)]
                for r in np.arange(1, 19)
            ]
        )
        plt.scatter(
            x=df["rank"][(df["spieltag"] == sp) & (df["season"] == df["season"].max())],
            y=df["points_cum"][
                (df["spieltag"] == sp) & (df["season"] == df["season"].max())
            ],
        )

        plt.title(
            f"Verteilung der Punkte nach Platzierung nach dem {sp}. Spieltag"
        )

        # plt.xlabel('Platzierung')
        plt.ylabel("Punkte")
        plt.text(
            0, -5, "Bundesliga seit 1963. Blaue Punkte stehen für die Saison 2023/24."
        )
        plt.savefig(f"out/box_{sp}.png")
        plt.close()


def get_prob_abstieg(df, spieltag, team_points, path, min_season=1980):
    """ A team has 'team_points' after matchday 'spieltag'
        How did other teams with these parameters fare in the past
    """
    export = df[["season", "team", "rank", "end_rank", "diff16", "diff17"]][
        (df.spieltag == spieltag) & (df.points_cum == team_points)
    ]

    with open(
        os.path.join(path, f"out/bl_hist_sp{spieltag}pt{team_points}.txt"), "w"
    ) as outfile:
        export.to_string(outfile)
    """
    # Noch interessanter: Ziehe eine Liste von Listen,
    # die die Tabellenplatz-Entwicklung dieser Teams beschreibt
    plotcases = df[["season", "team", "end_rank", "diff16", "diff17"]][
        (df.spieltag == spieltag)
        & (df.points_cum == team_points)
        & (df.season >= min_season)
    ]
    plotcases["seasstr"] = plotcases.season.astype(str)
    plotcases["label"] = plotcases["team"] + " " + plotcases.seasstr

    scfig, ax = plt.subplots()
    ax = plotcases.plot.scatter(x="diff17", y="end_rank")
    ax.invert_yaxis()
    plt.axhline(y=16.5, color="r")
    plotcases[["diff17", "end_rank", "label"]].apply(lambda x: ax.text(*x), axis=1)
    plt.show()
    """


def get_streaks(df):
    """ Looking for a goalless streak
    """
    df = df.sort_values(by=["season", "team", "spieltag"])
    df["5gamesnogoal"] = (
        (df["goals_for"] == 0)
        & (df["goals_for"].shift(1) == 0)
        & (df["goals_for"].shift(2) == 0)
        & (df["goals_for"].shift(3) == 0)
        & (df["goals_for"].shift(4) == 0)
    )
    df.loc[df["season"].shift(4) != df["season"], "5gamesnogoal"] = False
    print(
        "Streaks of five goalless games in a row: \n".format(
            df[["team", "season", "spieltag"]][df["5gamesnogoal"]]
        )
    )


def dewigetabelle(df):
    """ Ewige Tabelle: Cumulated Table of all seasons
    """
    # Now, create Rank.
    df = df.sort_values(by=["season", "team", "spieltag"])
    # various cumulative sums
    df["goals_for_cum_ever"] = df.groupby(["team"])["goals_for"].transform("cumsum")
    df["goals_against_cum_ever"] = df.groupby(["team"])["goals_against"].transform(
        "cumsum"
    )
    df["goal_diff_ever"] = df["goals_for_cum_ever"] - df["goals_against_cum_ever"]
    df["points_cum_ever"] = df.groupby(["team"])["pts"].transform("cumsum")
    df["win"] = (df["goals_for"] > df["goals_against"]).astype(int)
    df["draw"] = (df["goals_for"] == df["goals_against"]).astype(int)
    df["loss"] = (df["goals_for"] < df["goals_against"]).astype(int)

    wdl = df.groupby("team")[["win", "draw", "loss"]].sum()
    wdl["n_games"] = wdl["win"] + wdl["draw"] + wdl["loss"]
    wdl["n_seasons"] = df.groupby("team")["season"].unique().apply(len)

    ewigetabelle = (
        df.drop(columns=["win", "draw", "loss"])
        .groupby("team")
        .last()
        .merge(wdl, on="team")
    )

    ewigetabelle["team"] = ewigetabelle.index
    ewigetabelle = ewigetabelle.sort_values(
        by=["points_cum_ever", "goal_diff_ever"], ascending=[False, False]
    )
    ewigetabelle["rank"] = (
        ewigetabelle[["points_cum_ever"]].rank(ascending=False).astype(int)
    )

    ewigetabelle = ewigetabelle.replace({"team": get_full_team_names()})
    # Reduce colums
    out = ewigetabelle[
        [
            "rank",
            "team",
            "n_seasons",
            "n_games",
            "win",
            "draw",
            "loss",
            "goals_for_cum_ever",
            "goals_against_cum_ever",
            "goal_diff_ever",
            "points_cum_ever",
        ]
    ]
    out = out.rename(
        columns={
            "team": "Team",
            "n_seasons": "Total Seasons",
            "n_games": "Total Games",
            "win": "Wins",
            "draw": "Draws",
            "loss": "Losses",
            "goals_for_cum_ever": "Goals scored",
            "goals_against_cum_ever": "Goals conceded",
            "goal_diff_ever": "Goal Difference",
            "points_cum_ever": "Points",
        }
    )

    out.to_excel("out/ewigetabelle.xlsx", index=False)


def aufbaugegner(df):
    """ checks whethere there are certain matches against whom you want to play
    if you are on a bad streak
    """

    df = df.sort_values(by=["team", "season", "spieltag"])
    df["pts5g"] = (
        df["pts"].shift(5)
        + df["pts"].shift(4)
        + df["pts"].shift(3)
        + df["pts"].shift(2)
        + df["pts"].shift(1)
    )
    # Aufbaugegner is defined as losing against a team that made less than 3 points in the last five matches.
    df["relief"] = (df["pts"] == 3) & (df["pts5g"] <= 3)
    print("Aufbaugegner:\n {}".format(df[df["relief"]]["opponent"].value_counts()))


def teambilanz(df, teamname="Freiburg"):
    """ Show historical matchup of a team against all other Teams.
    """
    # keep only team
    teamdf = df[df["team"] == teamname].copy()
    teamdf["win"] = 1 * (teamdf["goals_for"] > teamdf["goals_against"])
    teamdf["draw"] = 1 * (teamdf["goals_for"] == teamdf["goals_against"])
    teamdf["loss"] = 1 * (teamdf["goals_for"] < teamdf["goals_against"])
    bilanz = teamdf.groupby("opponent")[
        ["pts", "goals_for", "goals_against", "win", "draw", "loss"]
    ].sum()
    bilanz["goal_diff"] = bilanz["goals_for"] - bilanz["goals_against"]
    bilanz["games"] = bilanz["win"] + bilanz["draw"] + bilanz["loss"]
    bilanz["winshare"] = bilanz["win"] / bilanz["games"]
    bilanz["avg_pts"] = bilanz["pts"] / bilanz["games"]
    bilanz = bilanz.sort_values(by=["avg_pts"], ascending=[False])

    print(f"Bilanz von {teamname} erzeugt...")
    # print(bilanz[["pts", "goal_diff", "games", "win", "draw", "loss", "winshare", "avg_pts"]])
    bilanz[
        ["pts", "goal_diff", "games", "win", "draw", "loss", "winshare", "avg_pts"]
    ].to_excel(f"out/teambilanz{teamname}.xlsx")
    print(f"Spiele von {teamname} mit mind. 5 Toren")
    print(
        df[["season", "spieltag", "team", "opponent", "goals_for", "goals_against"]][
            (df["team"] == teamname) & (df["goals_for"] >= 5)
        ]
    )


def clean_booking_data(df, liga):
    """ returns a dataframe with one observation per booking.

    """
    yellow = (
        df["yellow"].str.replace(r"\[|\]", "", regex=True).str.split(",", expand=True)
    )
    yellowred = (
        df["yellowred"]
        .str.replace(r"\[|\]", "", regex=True)
        .str.split(",", expand=True)
    )
    red = df["red"].str.replace(r"\[|\]", "", regex=True).str.split(",", expand=True)
    # Game_id must be maintained!!
    yellow.index = df["game_id"]
    red.index = df["game_id"]
    yellowred.index = df["game_id"]

    yellow_clean = yellow.unstack(level=0).dropna()
    yellow_clean = yellow_clean[yellow_clean != ""]

    red_clean = red.unstack(level=0).dropna()
    red_clean = red_clean[red_clean != ""]

    yellowred_clean = yellowred.unstack(level=0).dropna()
    yellowred_clean = yellowred_clean[yellowred_clean != ""]

    # Export
    yellow_clean.sort_index(level=1).to_csv(
        "data/league_{}/yellowcards.csv".format(liga),
        header=True,
        index_label=["count", "game_id"],
    )
    yellowred_clean.sort_index(level=1).to_csv(
        "data/league_{}/yellowredcards.csv".format(liga),
        header=True,
        index_label=["count", "game_id"],
    )
    red_clean.sort_index(level=1).to_csv(
        "data/league_{}/redcards.csv".format(liga),
        header=True,
        index_label=["count", "game_id"],
    )


def clean_results_data(df):
    # drop missing
    df = df.dropna(how="any")
    df["season"] = df["season"].astype(int)
    # few checks on the data
    print("\n")
    print(df.sort_values(by=["season"])["season"].value_counts())

    df["hometeam"] = df["hometeam"].astype(str)
    df["awayteam"] = df["awayteam"].astype(str)
    df["homegoals"] = pd.to_numeric(df["homegoals"])
    df["awaygoals"] = pd.to_numeric(df["awaygoals"])
    # Baue Teamdatensatz
    dfhome = df.copy()
    dfaway = df.copy()

    dfhome["team"] = dfhome["hometeam"]
    dfhome["opponent"] = dfhome["awayteam"]
    dfhome["goals_for"] = dfhome["homegoals"]
    dfhome["goals_against"] = dfhome["awaygoals"]

    dfaway["team"] = dfaway["awayteam"]
    dfaway["opponent"] = dfaway["hometeam"]
    dfaway["goals_for"] = dfaway["awaygoals"]
    dfaway["goals_against"] = dfaway["homegoals"]

    dfhome = dfhome.drop(columns=["hometeam", "awayteam", "homegoals", "awaygoals"])
    dfaway = dfaway.drop(columns=["hometeam", "awayteam", "homegoals", "awaygoals"])
    dfhome["home"] = 1
    dfaway["home"] = 0
    # Packe home und away zusammen
    df = pd.concat([dfhome, dfaway])

    df["team"] = correct_names(df["team"])
    df["opponent"] = correct_names(df["opponent"])
    # Correct team names
    for t in ["team", "opponent"]:
        df.loc[(df[t] == "Leipzig") & (df["season"] == 1993), t] = "Leipzig2"

    df["pts"] = 3 * (df["goals_for"] > df["goals_against"]) + (
        df["goals_for"] == df["goals_against"]
    )

    for var in ["season", "spieltag", "pts", "goals_for", "goals_against"]:
        df[var] = df[var].astype(int)

    return df


def schedule(df):
    """ does it make a difference whether the schedule is tough in the first half
    or the second half?
    """

    # get end_rank for each opponent
    end_rank = df[["team", "season", "rank"]][df["spieltag"] == 34]
    end_rank = end_rank.rename(columns={"team": "opponent", "rank": "end_rank_opp"})
    end_pts = df.groupby(["team", "season"], as_index=False)["points_cum"].max()
    end_pts = end_pts.rename(columns={"points_cum": "points_end"})
    # reduce to first 17 games
    df = df[df["spieltag"] <= 17]
    df = pd.merge(df, end_rank, on=["opponent", "season"])
    df = pd.merge(df, end_pts, on=["team", "season"])
    sched_diff_1 = (
        df[df["spieltag"] <= 9].groupby(["team", "season"])["end_rank_opp"].mean()
    )
    sched_diff_2 = (
        df[df["spieltag"] > 9].groupby(["team", "season"])["end_rank_opp"].mean()
    )
    schedules = pd.DataFrame({"hard_1": sched_diff_1 < 8, "hard_2": sched_diff_2 < 8})
    schedules = schedules.merge(
        df[["team", "season", "points_end"]], on=["team", "season"]
    )
    # Output
    print(
        "Season points depending on difficulty of schedule \n First 9 games: \n {} \n Last 8 games: \n {}".format(
            schedules.groupby("hard_1")["points_end"].hist(),
            schedules.groupby("hard_2")["points_end"].hist(),
        )
    )


def prepare_game_analysis_data(df):
    df = df.sort_values(by=["season", "spieltag"])
    goals_mday = df.groupby(["season", "spieltag"])["goals_for"].sum()
    goals_mday = goals_mday.sort_values(0)
    # mingoals = goals_mday.min()

    # Now, create Rank.
    df = df.sort_values(by=["season", "team", "spieltag"])
    print(df.columns)
    # various cumulative sums
    df["goals_for_cum"] = df.groupby(["season", "team"])["goals_for"].transform(
        "cumsum"
    )
    df["goals_against_cum"] = df.groupby(["season", "team"])["goals_against"].transform(
        "cumsum"
    )
    df["goal_diff"] = df["goals_for_cum"] - df["goals_against_cum"]
    df["points_cum"] = df.groupby(["season", "team"])["pts"].transform("cumsum")

    df = df.sort_values(
        by=["season", "spieltag", "points_cum", "goal_diff"],
        ascending=[True, True, False, False],
    )
    df["rank"] = df.groupby(["season", "spieltag"]).cumcount() + 1

    # obtain rank at end of season
    df = df.sort_values(by=["season", "team", "spieltag"])
    df["letzer_spieltag"] = 34
    df.loc[df["season"] <= 1964, "letzer_spieltag"] = 30
    df.loc[df["season"] == 1991, "letzer_spieltag"] = 38
    end_rank = df[["team", "season", "rank"]][df["spieltag"] == df["letzer_spieltag"]]

    end_rank = end_rank.rename(columns={"rank": "end_rank"})
    df = pd.merge(df, end_rank, on=["team", "season"])

    # get difference to each rank
    for p in range(0, 18):
        temp = df[["season", "spieltag", "points_cum"]][df["rank"] == p + 1]
        temp = temp.rename(columns={"points_cum": "pts" + str(p + 1)})
        df = pd.merge(df, temp, on=["season", "spieltag"])
        df[f"diff{p+1}"] = df["points_cum"] - df[f"pts{p+1}"]
        df = df.drop(columns=[f"pts{p+1}"])

    return df


def game_analysis(df, spieltag, team_points, teamname, path):
    df = prepare_game_analysis_data(df)

    # print("Punktzahl aller Zweitplatzierten am ",spieltag,".Spieltag")
    # zweite = df[['season','team','points_cum']][(df['spieltag']==spieltag) & (df['rank']==2)]
    # zweite['points_cum'].hist(bins=20)
    # zweite = zweite.sort_values(by='points_cum')
    # zweite.head(10)

    make_boxplot_by_spieltag(df)

    get_prob_abstieg(df, spieltag, team_points, path)

    schedule(df)

    get_streaks(df)

    ewigetabelle(df)

    aufbaugegner(df)

    # Ab wann ist die Tabelle aussagekräftig
    df["diff_rank"] = df["end_rank"] - df["rank"]
    df["close"] = abs(df["diff_rank"]) <= 2
    print(
        f"Anteil der aussagekräftigen Platzierungen nach Spieltag: \n {df.groupby(['spieltag'])['close'].mean()}"
    )

    teambilanz(df, teamname)

    return df


def goal_analysis(df):
    # get last name of scorer
    namesplit = df["player_name"].str.split("-", expand=True)
    df["scorer_lastname"] = ""

    for c in np.arange(3, -1, -1):
        df.loc[
            (~namesplit[c].isna()) & (df["scorer_lastname"] == ""), "scorer_lastname"
        ] = namesplit[c]

    # Torschützenliste
    scorerlist = df["player_name"].value_counts()
    print(f"Best Scorers: \n {scorerlist[scorerlist > 50]}")
    # TO DO: Scorer by team. Need to look for scorer id in lineup.
    # teamtopscorer = df.groupby(["team"])["player_name"].value_counts()
    # teamtopscorer.to_excel("out/scorer_by_team.xlsx")


def clean_all_results(path):
    df = pd.read_csv(path + "/data/league_1/all_game_results_since1963.csv")
    df = df.drop(columns=["gamelink", "game_id"])

    df["hometeam"] = correct_names(df["hometeam"])
    df["awayteam"] = correct_names(df["awayteam"])
    df = df[df["season"] != ""]
    df = df[~df["season"].isna()]
    dropthese = (df["season"] <= 1964) & (df["spieltag"] >= 31)
    df = df[~dropthese].copy()

    # a number of manual corrections
    for var in ["hometeam", "awayteam"]:
        df.loc[(df["season"] == 1993) & (df[var] == "Leipzig"), var] = "VfB Leipzig"
    df.loc[
        (df["season"] == 1976)
        & (df["spieltag"] == 15)
        & (df["awayteam"] == "RW Essen"),
        "awaygoals",
    ] = 1
    df.loc[
        (df["season"] == 1992) & (df["spieltag"] == 32) & (df["awayteam"] == "Bayern"),
        "awaygoals",
    ] = 2
    df.loc[
        (df["season"] == 1994) & (df["spieltag"] == 26) & (df["awayteam"] == "Bochum"),
        "awaygoals",
    ] = 0
    for var in list(df):
        #        assert ~df[var].isna().any()
        print(df[["season", "spieltag"]][df["hometeam"].isna()])
        if var not in ["hometeam", "awayteam"]:
            df[var] = df[var].astype(int)
    #    df = df.rename(columns={"spieltag": "matchday"})

    return df


def create_game_results_since_1963(path, crawl):
    """ run this function to crawl and prepare all match results (without lineups, goals etc.)
        for the Bundesliga since 1963
    """
    # Run Crawler for Bundesliga
    if crawl:
        crawler(path, list(range(1963, 2023)), 1, True)

    df = clean_all_results(path)
    df.to_csv("data/all_bundesliga_results.csv", index=False)
    df = clean_results_data(df)
    game_analysis(df, spieltag=34, team_points=45, teamname="Freiburg", path=path)

    return None


def main(
    path,
    spieltag,
    team_points,
    teamname,
    crawl,
    seasons_to_crawl,
    leagues_to_crawl=[1, 2, 3],
):
    """
    Runs through all functions and returns analyses on
    - game results
    - game details (scorer, bookings)
    - Individual results are possible since:
        - 1963 for league 1
        - 1997 for league 2
        - 2008 for league 3
    """
    # START CRAWLING
    for liga in leagues_to_crawl:
        if liga == 3:
            # 3. Liga existent only since 2008
            seas = list(range(2008, 2023))
        elif liga == 2:
            seas = list(range(1997, 2023))
        else:
            seas = seasons_to_crawl
        if crawl == 1:
            crawler(path, seas, liga)

    gameresults = pd.read_csv(f"data/league_{liga}/all_game_results_since{seas[0]}.csv")
    goals = pd.read_csv(f"data/league_{liga}/all_goals_since{seas[0]}.csv")
    lineups = pd.read_csv(f"data/league_{liga}/all_rosters_since{seas[0]}.csv")
    # export id's
    player_ids = (
        lineups.groupby("player_id").first().drop(columns=["minute", "role", "game_id"])
    )

    clean_res = clean_results_data(gameresults)
    game_analysis(clean_res, spieltag, team_points, teamname, path)

    # merge lineups to goal data
    goals = goals.rename(columns={"scorer": "player_id"})
    goals = goals.merge(player_ids, on="player_id", validate="m:1")
    # merge teams
    goals = goals.merge(gameresults, on="game_id", validate="m:1")
    goal_analysis(goals)

    # create data for individual bookings
    bookings = pd.read_csv(f"data/league_{liga}/bookings_since{seas[0]}.csv")
    clean_booking_data(bookings, liga)


#create_game_results_since_1963(PATH, CRAWL)
crawler(PATH, list(range(1974, 2023)), 2, True)
"""
ranklist=[]

for i in plotcases.index:
    ranklist.append(df['rank'][(df['season']==plotcases['season'][i])&(df['team']==plotcases['team'][i])&(df['spieltag']>=spieltag)]& (df['season'] >= min_season))
plotcases['ranklist'] = ranklist


#spieltagplot = np.arange(spieltag,35)
# Now plot this
#plt.clf()
#for i in plotcases.index:
 #   print(i)
  #  plt.plot(spieltagplot,plotcases['ranklist'][i],label=plotcases['team'][i]+' '+str(plotcases['season'][i]))

#plt.legend(loc='upper center', bbox_to_anchor=(spieltagplot[0], -0.05),fancybox=True, shadow=True, ncol=5)
#plt.show()
"""
