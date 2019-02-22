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
import sys

# from buli_rawdata_rssf import *
# from buli_process import *
from crawler import *
from colorama import Fore
from colorama import Style

path = os.getcwd() + "/"

# SWITCHES


crawl = 0

produce_graphs = 0

# SET VARIABLES FOR OUTPUT
spieltag = 22
scf_points = 24
# Plot since season..
min_season = 1980


"""
if raw_data == 1:
    rawdata(path)

if process_data == 1:
    processdata(path)
"""
if crawl == 1:
    df = crawler(path)
else:
    df = pd.read_json(path + "all_kicker_results.json")
# drop 2017
# df = df.drop(df[df.season==2017].index)
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


df = df.sort_values(by=["season", "spieltag"])
goals_mday = df.groupby(["season", "spieltag"])["goals_for"].sum()
goals_mday = goals_mday.sort_values(0)
mingoals = goals_mday.min()

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
pd.to_pickle(df, path + "buli_final")

# print("Punktzahl aller Zweitplatzierten am ",spieltag,".Spieltag")
# zweite = df[['season','team','points_cum']][(df['spieltag']==spieltag) & (df['rank']==2)]
# zweite['points_cum'].hist(bins=20)
# zweite = zweite.sort_values(by='points_cum')
# zweite.head(10)
if produce_graphs == 1:
    for sp in range(9, 35):
        plt.clf()
        df[df["spieltag"] == sp].boxplot(column="points_cum", by=["rank"])
        plt.savefig("box_" + str(sp) + ".png")
        plt.close()
"""
print("Endplatzierung aller Mannschaften, die am ",
      spieltag,
      ".Spieltag ",
      scf_points, " Punkte hatten.")
"""
export = df[["season", "team", "rank", "end_rank", "diff16", "diff17"]][
    (df.spieltag == spieltag) & (df.points_cum == scf_points)
]

with open(
    os.path.join(path, "bl_hist_sp" + str(spieltag) + "pt" + str(scf_points) + ".txt"),
    "w",
) as outfile:
    export.to_string(outfile)

# Suche längste Serie ohne Tor
df = df.sort_values(by=["season", "team", "spieltag"])
df["5gamesnogoal"] = (
    (df["goals_for"] == 0)
    & (df["goals_for"].shift(1) == 0)
    & (df["goals_for"].shift(2) == 0)
    & (df["goals_for"].shift(3) == 0)
    & (df["goals_for"].shift(4) == 0)
)

# Noch interessanter: Ziehe eine Liste von Listen, die die Tabellenplatz-Entwicklung dieser Teams beschreibt
plotcases = df[["season", "team", "end_rank", "diff16", "diff17"]][
    (df.spieltag == spieltag)
    & (df.points_cum == scf_points)
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

# Ewige Tabelle
# Now, create Rank.
df = df.sort_values(by=["season", "team", "spieltag"])
# various cumulative sums
df["goals_for_cum_ever"] = df.groupby(["team"])["goals_for"].apply(lambda x: x.cumsum())
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
full_names = {
    "Bayern": "FC Bayern München",
    "Bremen": "SV Werder Bremen",
    "HSV": "Hamburger SV",
    "Dortmund": "Borussia Dortmund",
    "Stuttgart": "VfB Stuttgart",
    "Gladbach": "Borussia Mönchengladbach",
    "Schalke": "FC Schalke 04",
    "Köln": "1. FC Köln",
    "Frankfurt": "Eintracht Frankfurt",
    "Leverkusen": "Bayer 04 Leverkusen",
    "K'lautern": "1. FC Kaiserslautern",
    "Hertha": "Hertha BSC",
    "Bochum": "VfL Bochum",
    "Nürnberg": "1. FC Nürnberg",
    "Hannover": "Hannover 96",
    "Duisburg": "MSV Duisburg",
    "Wolfsburg": "VfL Wolfsburg",
    "Düsseldorf": "Fortuna Düsseldorf",
    "Karlsruhe": "Karlsruher SC",
    "Braunschweig": "Eintracht Braunschweig",
    "TSV 1860": "TSV 1860 München",
    "Freiburg": "SC Freiburg",
    "Bielefeld": "Arminia Bielefeld",
    "Uerdingen": "KFC Uerdingen",
    "Mainz": "1. FSV Mainz 05",
    "Hoffenheim": "1899 Hoffenheim",
    "Rostock": "FC Hansa Rostock",
    "Augsburg": "FC Augsburg",
    "Waldhof Mannheim": "SV Waldhof Mannheim",
    "Offenbach": "Offenbacher Kickers",
    "RW Essen": "Rot-Weiß Essen",
    "St. Pauli": "FC St. Pauli",
    "Cottbus": "Energie Cottbus",
    "Aachen": "Alemannia Aachen",
    "Leipzig": "RB Leipzig",
    "Oberhausen": "Rot-Weiß Oberhausen",
    "Saarbrücken": "1. FC Saarbrücken",
    "Darmstadt": "SV Darmstadt 98",
    "Wattenscheid": "SV Wattenscheid 09",
    "Dresden": "Dynamo Dresden",
    "Homburg": "FC Homburg",
    "Unterhaching": "SpVgg Unterhaching",
    "Ingolstadt": "1. FC Ingolstadt",
    "Neunkirchen": "Borussia Neunkirchen",
    "TeBe Berlin": "Tennis Borussia Berlin",
    "Stuttg. Kick.": "Stuttgarter Kickers",
    "Ulm": "SSV Ulm",
    "F. Köln": "Fortuna Köln",
    "Paderborn": "SC Paderborn 07",
    "Fürth": "Greuther Fürth",
    "Blau-Weiß 90 Ber.": "Blau-Weiß 90 Berlin",
    "Tasmania": "Tasmania Berlin",
}

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

# Ab wann ist die Tabelle aussagekräftig
df["diff_rank"] = df["end_rank"] - df["rank"]
df["close"] = abs(df["diff_rank"]) <= 2
print(df.groupby(["spieltag"])["close"].mean())

# Bilanz SC Freiburg nach Gegner
scf = df[df["team"] == "Freiburg"]
scf["win"] = 1 * (scf["goals_for"] > scf["goals_against"])
scf["draw"] = 1 * (scf["goals_for"] == scf["goals_against"])
scf["loss"] = 1 * (scf["goals_for"] < scf["goals_against"])
scfbilanz = scf.groupby("opponent")[
    ["pts", "goals_for", "goals_against", "win", "draw", "loss"]
].sum()
scfbilanz["goal_diff"] = scfbilanz["goals_for"] - scfbilanz["goals_against"]
scfbilanz = scfbilanz.sort_values(by=["pts", "goal_diff"], ascending=[False, False])
print("SC Bilanz")
print(scfbilanz[["pts", "goal_diff", "win", "draw", "loss"]])


sys.exit("DONE")

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
