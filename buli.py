#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Analyze historical Bundesliga results
#
########################################

# path='/home/eric/Dropbox/buli/'
# path = 'Z:/test/buli/'


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from functions import get_full_team_names, correct_signs

# from buli_rawdata_rssf import *
# from buli_process import *
from crawler import crawler, correct_names

path = os.getcwd() + "/"

# SWITCHES

# Crawl and reproduce data.
crawl = 0

produce_graphs = 0

teamname = "Freiburg"

seasons_to_crawl = list(range(1995, 2017))

# SET VARIABLES FOR OUTPUT
spieltag = 24
team_points = 27
# Plot since season..
min_season = 1980


def make_boxplot_by_spieltag(df):
    for sp in range(9, 35):
        plt.clf()
        df[df["spieltag"] == sp].boxplot(column="points_cum", by=["rank"])
        plt.savefig("box_" + str(sp) + ".png")
        plt.close()


def get_prob_abstieg(df, spieltag, team_points):
    """ A team has 'team_points' after matchday 'spieltag'
        How did other teams with these parameters fare in the past regarding relegation?
    """
    export = df[["season", "team", "rank", "end_rank", "diff16", "diff17"]][
        (df.spieltag == spieltag) & (df.points_cum == team_points)
    ]

    with open(
        os.path.join(
            path, "bl_hist_sp" + str(spieltag) + "pt" + str(team_points) + ".txt"
        ),
        "w",
    ) as outfile:
        export.to_string(outfile)

    # Noch interessanter: Ziehe eine Liste von Listen, die die Tabellenplatz-Entwicklung dieser Teams beschreibt
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


def ewigetabelle(df):
    """ Ewige Tabelle: Cumulated Table of all seasons
    """
    # Now, create Rank.
    df = df.sort_values(by=["season", "team", "spieltag"])
    # various cumulative sums
    df["goals_for_cum_ever"] = df.groupby(["team"])["goals_for"].apply(
        lambda x: x.cumsum()
    )
    df["goals_against_cum_ever"] = df.groupby(["team"])["goals_against"].apply(
        lambda x: x.cumsum()
    )
    df["goal_diff_ever"] = df["goals_for_cum_ever"] - df["goals_against_cum_ever"]
    df["points_cum_ever"] = df.groupby(["team"])["pts"].apply(lambda x: x.cumsum())
    # Number of seasons played. don't know yet how to bring to ewige tabelle
    n_seasons = df.groupby("team")["season"].unique().apply(len)
    # n_seasons['team'] = n_seasons.index
    # also add number of games, including wins, draws, losses

    ewigetabelle = df.groupby("team").last()
    ewigetabelle["team"] = ewigetabelle.index
    ewigetabelle = ewigetabelle.sort_values(
        by=["points_cum_ever", "goal_diff_ever"], ascending=[False, False]
    )
    ewigetabelle["rank"] = ewigetabelle.rank(ascending=True)

    full_names = get_full_team_names()

    ewigetabelle = ewigetabelle.replace({"team": full_names})

    ewigetabelle[
        [
            "rank",
            "team",
            "goals_for_cum_ever",
            "goals_against_cum_ever",
            "goal_diff_ever",
            "points_cum_ever",
        ]
    ].to_excel("ewigetabelle.xls")


def teambilanz(df, teamname="Freiburg"):
    """ Show historical matchup of a team against all other Teams.
    """
    # keep only team
    teamdf = df[df["team"] == teamname]
    teamdf["win"] = 1 * (teamdf["goals_for"] > teamdf["goals_against"])
    teamdf["draw"] = 1 * (teamdf["goals_for"] == teamdf["goals_against"])
    teamdf["loss"] = 1 * (teamdf["goals_for"] < teamdf["goals_against"])
    bilanz = teamdf.groupby("opponent")[
        ["pts", "goals_for", "goals_against", "win", "draw", "loss"]
    ].sum()
    bilanz["goal_diff"] = bilanz["goals_for"] - bilanz["goals_against"]
    bilanz["winshare"] = bilanz["win"] / (
        bilanz["win"] + bilanz["draw"] + bilanz["loss"]
    )
    bilanz = bilanz.sort_values(by=["winshare"], ascending=[False])

    print("Bilanz von {}".format(teamname))
    print(bilanz[["pts", "goal_diff", "win", "draw", "loss", "winshare"]])
    print("Spiele von {} mit mehr als 5 Toren".format(teamname))
    print(
        df[["season", "spieltag", "team", "opponent", "goals_for", "goals_against"]][
            (df["team"] == teamname) & (df["goals_for"] >= 5)
        ]
    )


def game_analysis(df):
    # drop missing
    df = df.dropna(how="any")
    df["season"] = df["season"].astype(int)
    # few checks on the data
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

    dfhome = dfhome.drop(["hometeam", "awayteam", "homegoals", "awaygoals"], 1)
    dfaway = dfaway.drop(["hometeam", "awayteam", "homegoals", "awaygoals"], 1)
    dfhome["home"] = 1
    dfaway["home"] = 0
    # Packe home und away zusammen
    df = dfhome.append(dfaway)

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

    df = df.sort_values(by=["season", "spieltag"])
    goals_mday = df.groupby(["season", "spieltag"])["goals_for"].sum()
    goals_mday = goals_mday.sort_values(0)
    # mingoals = goals_mday.min()

    # Now, create Rank.
    df = df.sort_values(by=["season", "team", "spieltag"])
    # various cumulative sums
    df["goals_for_cum"] = df.groupby(["season", "team"])["goals_for"].apply(
        lambda x: x.cumsum()
    )
    df["goals_against_cum"] = df.groupby(["season", "team"])["goals_against"].apply(
        lambda x: x.cumsum()
    )
    df["goal_diff"] = df["goals_for_cum"] - df["goals_against_cum"]
    df["points_cum"] = df.groupby(["season", "team"])["pts"].apply(lambda x: x.cumsum())

    df = df.sort_values(
        by=["season", "spieltag", "points_cum", "goal_diff"],
        ascending=[True, True, False, False],
    )
    df["rank"] = df.groupby(["season", "spieltag"]).cumcount() + 1

    # obtain rank at end of season
    end_rank = df[["team", "season", "rank"]][df.spieltag == 34]
    end_rank = end_rank.rename(columns={"rank": "end_rank"})
    df = pd.merge(df, end_rank, on=["team", "season"])

    # get difference to each rank
    for p in range(0, 18):
        temp = df[["season", "spieltag", "points_cum"]][df["rank"] == p + 1]
        temp = temp.rename(columns={"points_cum": "pts" + str(p + 1)})
        df = pd.merge(df, temp, on=["season", "spieltag"])
        df["diff" + str(p + 1)] = df["points_cum"] - df["pts" + str(p + 1)]
        df = df.drop(["pts" + str(p + 1)], 1)

    # print(df[['season','spieltag','team','rank','points_cum','diff5']].head())
    # pd.to_pickle(df, path + "buli_final")

    # print("Punktzahl aller Zweitplatzierten am ",spieltag,".Spieltag")
    # zweite = df[['season','team','points_cum']][(df['spieltag']==spieltag) & (df['rank']==2)]
    # zweite['points_cum'].hist(bins=20)
    # zweite = zweite.sort_values(by='points_cum')
    # zweite.head(10)
    if produce_graphs == 1:
        make_boxplot_by_spieltag(df)

    get_prob_abstieg(df, spieltag, team_points)

    get_streaks(df)

    ewigetabelle(df)

    # Ab wann ist die Tabelle aussagekräftig
    df["diff_rank"] = df["end_rank"] - df["rank"]
    df["close"] = abs(df["diff_rank"]) <= 2
    print(df.groupby(["spieltag"])["close"].mean())

    teambilanz(df, teamname)


def goal_analysis(df):
    # get last name of scorer
    namesplit = df['scorer'].str.split('-', expand=True)
    df['scorer_lastname'] = ''

    for c in np.arange(4, -1, -1):
        df.loc[(~namesplit[c].isna()) &
        (df['scorer_lastname'] == ''),
        'scorer_lastname'] = namesplit[c]

    # dissolve line up list
    for t in ['home', 'away']:
        for tt in ['starting', 'substi']:
            df[t+'_'+tt] = df[t+'_'+tt].str.join(",").str.lower()
        df['lineup_'+t] = df[t+'_starting'] + df[t+'_substi']
        # correct ö,ä,ü
        df['lineup_'+t] = df['lineup_'+t].apply(correct_signs)

        df['scorer_'+t] = [y in x for x, y in zip(df["lineup_"+t], df['scorer_lastname'])]


    # Torschützenliste
    scorerlist = df['scorer'].value_counts()
    print(scorerlist[scorerlist > 50])
    # To Do: Top Scorers by team
    df.loc[df['scorer_home'], 'team'] = df['hometeam']
    df.loc[df['scorer_away'], 'team'] = df['awayteam']
    df.groupby(['team'])['scorer'].value_counts().to_excel('scorer_by_team.xlsx')


# Load Data
if crawl == 1:
    gameresults, goals = crawler(path, seasons_to_crawl)
else:
    gameresults = pd.read_json(
        "all_game_results_since{}.json".format(seasons_to_crawl[0])
    )
    goals = pd.read_json("all_goals_since{}.json".format(seasons_to_crawl[0]))
    lineups = pd.read_json("all_rosters_since{}.json".format(seasons_to_crawl[0]))

game_analysis(gameresults)

# merge lineups to goal data
goals = goals.merge(lineups, on = 'game_id', validate='m:1')
# merge teams
goals = goals.merge(gameresults, on='game_id', validate='m:1')

goal_analysis(goals)

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
