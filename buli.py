#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Analyze historical Bundesliga results
# TO DO: 1. improve data. crawl kicker.de for historical results
# 
########################################

#path='/home/eric/Dropbox/buli/'
path='Z:/test/buli/'
    
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

from buli_rawdata_rssf import *
from buli_process import *
from crawler import * 
from colorama import Fore
from colorama import Style

if not os.path.exists(path):
    path=os.getcwd()+'/'

#SWITCHES
raw_data = 0
process_data = 0
crawl = 0

# SET VARIABLES FOR OUTPUT
spieltag = 25
scf_points = 17
# Plot since season..
min_season = 1980
      
if crawl == 1:
    crawler(path)


if raw_data == 1:
    rawdata(path)

if process_data == 1:
    processdata(path)


df = pd.read_pickle(path+'all_kicker_results')
#drop 2017
df = df.drop(df[df.season==2017].index)
# drop missing
df = df.dropna(how='any')

df['hometeam'] = df['hometeam'].astype(str)
df['awayteam'] = df['awayteam'].astype(str)
df['homegoals'] = pd.to_numeric(df['homegoals'])
df['awaygoals'] = pd.to_numeric(df['awaygoals'])
# Baue Teamdatensatz
dfhome = df.copy()
dfaway = df.copy()
        
dfhome['team'] = dfhome['hometeam']
dfhome['opponent'] = dfhome['awayteam']
dfhome['goals_for'] = dfhome['homegoals']
dfhome['goals_against'] = dfhome['awaygoals']
        
dfaway['team'] = dfaway['awayteam']
dfaway['opponent'] = dfaway['hometeam']
dfaway['goals_for'] = dfaway['awaygoals']
dfaway['goals_against'] = dfaway['homegoals']
        
dfhome = dfhome.drop(['hometeam','awayteam','homegoals','awaygoals'],1)
dfaway = dfaway.drop(['hometeam','awayteam','homegoals','awaygoals'],1)
dfhome['home'] = 1
dfaway['home'] = 0
# Packe home und away zusammen        
df = dfhome.append(dfaway)
#print(pd.crosstab(df['team'], df['season']))    

df['team'] = correct_names(df['team'])
df['opponent'] = correct_names(df['opponent'])

df['pts'] = 3 * (df['goals_for'] > df['goals_against']) + (df['goals_for'] == df['goals_against'])


df = df.sort_values(by=['season','spieltag'])
goals_mday = df.groupby(['season','spieltag'])['goals_for'].sum()
goals_mday = goals_mday.sort_values(0)
mingoals = goals_mday.min()
#print('Seasons and Matchday with least goals')
#print(goals_mday[0:9])
    
# Now, create Rank.
df = df.sort_values(by=['season','team','spieltag'])
# various cumulative sums
df['goals_for_cum'] = df.groupby(['season','team'])['goals_for'].apply(lambda x: x.cumsum())
df['goals_against_cum'] = df.groupby(['season','team'])['goals_against'].apply(lambda x: x.cumsum())
df['goal_diff'] = df['goals_for_cum'] - df['goals_against_cum']
df['points_cum'] = df.groupby(['season','team'])['pts'].apply(lambda x: x.cumsum())
    
df = df.sort_values(by=['season','spieltag','points_cum','goal_diff'],ascending=[True,True,False,False])
df['rank'] = df.groupby(['season','spieltag']).cumcount() + 1
    
# obtain rank at end of season
end_rank = df[['team','season','rank']][df.spieltag==34]
end_rank = end_rank.rename(columns={'rank':'end_rank'})
df = pd.merge(df,end_rank,on=['team','season'])

# get difference to each rank
for p in range(0,18):
    temp=df[['season','spieltag','points_cum']][df['rank']==p+1]
    temp = temp.rename(columns={'points_cum':'pts'+str(p+1)})
    df =pd.merge(df,temp,on=['season','spieltag'])
    df['diff'+str(p+1)] = df['points_cum'] - df['pts'+str(p+1)]
    df = df.drop(['pts'+str(p+1)],1)

#print(df[['season','spieltag','team','rank','points_cum','diff5']].head())

pd.to_pickle(df,path+'buli_final')


print("Punktzahl aller Zweitplatzierten am ",spieltag,".Spieltag")
zweite = df[['season','team','points_cum']][(df['spieltag']==spieltag) & (df['rank']==2)]
zweite['points_cum'].hist(bins=20)
zweite = zweite.sort_values(by='points_cum')
zweite.head(10)
for sp in range(9,35):
    plt.clf()
    df[df['spieltag']==sp].boxplot(column='points_cum',by=['rank'])
    plt.savefig('box_'+str(sp)+'.png')

print("Endplatzierung aller Mannschaften, die am ",spieltag,".Spieltag ",scf_points, " Punkte hatten.")
export = df[['season','team','rank','end_rank','diff16','diff17']][(df.spieltag==spieltag)&(df.points_cum==scf_points)]
print(export)



with open(os.path.join(path,'bl_hist_sp'+str(spieltag)+'pt'+str(scf_points)+'.txt'),'w') as outfile:
    export.to_string(outfile)

# Noch interessanter: Ziehe eine Liste von Listen, die die Tabellenplatz-Entwicklung dieser Teams beschreibt
plotcases = df[['season','team','end_rank','diff16','diff17']][(df.spieltag==spieltag)&(df.points_cum==scf_points)&(df.season>=min_season)]
plotcases['seasstr'] = plotcases.season.astype(str)
plotcases['label'] = plotcases['team'] + ' ' + plotcases.seasstr

scfig, ax = plt.subplots()
ax = plotcases.plot.scatter(x='diff17',y='end_rank')
ax.invert_yaxis()
plt.axhline(y=16.5, color='r')
plotcases[['diff17','end_rank','label']].apply(lambda x: ax.text(*x), axis=1)
plt.show()


sys.exit('DONE')
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

