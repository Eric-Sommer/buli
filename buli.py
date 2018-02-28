#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 25 20:09:50 2018

@author: eric
"""
path='/home/eric/Dropbox/buli/'

import pandas as pd
import numpy as np
import sys


#SWITCHES
raw_data = 0
process_data = 0

spieltag = 24
scf_points = 29
  
def correct_names(str_list):        
    res = list(str_list)
    tmp_lst = list(str_list)        
    #for s,t in str_list.iteritems():                       
    for s in range(0,len(str_list)):            
        if tmp_lst[s].find("lautern") >= 0: 
            res[s] = 'Kaiserslautern'
        if (tmp_lst[s].find("Köln") >= 0) & (tmp_lst[s].find("Fortuna") == -1):
            res[s] = 'Koeln'
        if tmp_lst[s].find("Nürnberg") >= 0:
            res[s] = 'Nuernberg'
        if tmp_lst[s].find("Mainz") >= 0:
            res[s] = 'Mainz'
        if tmp_lst[s].find('1860') >= 0:
            res[s] = '1860Muenchen'
        if tmp_lst[s].find('Hoffenheim') >= 0:
            res[s] = 'Hoffenheim'
        if tmp_lst[s].find('Alemannia') >= 0:
            res[s] = 'Aachen'
        if tmp_lst[s].find('Arminia') >= 0:
            res[s] = 'Bielefeld'
        if tmp_lst[s].find('Leverkusen') >= 0:
            res[s] = 'Leverkusen'
        if (tmp_lst[s].find('Munchen') >= 0) | (tmp_lst[s].find('Bayern') >= 0) | (tmp_lst[s].find('München') >= 0):
            res[s] = 'BMuenchen'
        if tmp_lst[s].find('Hertha') >= 0:
            res[s] = 'Berlin'
        if (tmp_lst[s].find('Dortmund') >= 0) | (tmp_lst[s].find('Borussia D') >= 0):
            res[s] = 'Dortmund'
        if (tmp_lst[s] in ['Borussia MG','Borussia M','Bourssia MG']) | (tmp_lst[s].find('ladbach')>0):
            res[s] = 'MGladbach'
        if tmp_lst[s].find('Energie') >= 0:
            res[s] = 'Cottbus'
        if tmp_lst[s].find('Dynamo') >= 0:
            res[s] = 'Dresden'
        if tmp_lst[s].find('Düsseldorf') >= 0:
            res[s] = 'Duesseldorf'    
        if (tmp_lst[s].find('Frankfurt') >= 0) | (tmp_lst[s] == 'Eintracht F') | (tmp_lst[s].find('Eintrcaht') >= 0):
            res[s] = 'Frankfurt'
        if tmp_lst[s].find('Schalke') >= 0:
            res[s] = 'Schalke'
        if tmp_lst[s].find('Pauli') >= 0:
            res[s] = 'St.Pauli'
        if (tmp_lst[s] == 'HSV') | (tmp_lst[s].find('Hamburg') >= 0):
            res[s] = 'Hamburg'
        if (tmp_lst[s].find('Hansa') >= 0):
            res[s] = 'Rostock'
        if tmp_lst[s].find('Karlsruhe') >= 0:
            res[s] = 'Karlsruhe'
        if tmp_lst[s].find('Freiburg') >= 0:
            res[s] = 'Freiburg'
        if tmp_lst[s].find('Stuttgart') >= 0:
            res[s] = 'Stuttgart'
        if tmp_lst[s].find('Wolfsburg') >= 0:
            res[s] = 'Wolfsburg'
        if (tmp_lst[s] == "W'scheid") | (tmp_lst[s].find('Wattenscheid') >= 0):
            res[s] = 'Wattenscheid'
        if tmp_lst[s].find('Werder') >= 0:
            res[s] = 'Bremen'
        if tmp_lst[s].find('MSV') >= 0:
            res[s] = 'Duisburg'
        if tmp_lst[s].find('Hannover') >= 0:
            res[s] = 'Hannover'
        if tmp_lst[s].find('Uerdingen') >= 0:
            res[s] = 'Uerdingen'
#        if tmp_lst[s].find('Leipzig') >= 0 & season < 2000:
 #           res[s] = 'VfBLeipzig'
        if tmp_lst[s].find('Leipzig') >= 0:
            res[s] = 'RBLeipzig'
        if tmp_lst[s].find('Ulm') >= 0:
            res[s] = 'Ulm'
        if tmp_lst[s].find('Unterhaching') >= 0:
            res[s] = 'Unterhaching'
        if tmp_lst[s].find('Bochum') >= 0:
            res[s] = 'Bochum'
        if tmp_lst[s].find('Braunschweig') >= 0:
            res[s] = 'Braunschweig'
        if tmp_lst[s].find('Augsburg') >= 0:
            res[s] = 'Augsburg'
        if tmp_lst[s].find('Paderborn') >= 0:
            res[s] = 'Paderborn'
        if tmp_lst[s].find('Ingolstadt') >= 0:
            res[s] = 'Ingolstadt'
        if tmp_lst[s].find('Darmstadt') >= 0:
            res[s] = 'Darmstadt'  
        if tmp_lst[s] == "S'brücken":
            res[s] = 'Saarbruecken'
            
    return res
    
if raw_data == 1:
    # Hier kommen alle jährlichen Datensätze rein
    df_dict = {}
    
    for yr in np.arange(1992,2017):
        print('Running Year ' + str(yr))
        df = pd.read_excel(path+'buli_results.xls',sheetname=str(yr),names=['home','result','away'])
        df['season'] = yr
        # clear the data
        # clear empty rows
        df = df.dropna(how='any')
        # clear everything with "[" or "]"
        if yr != 2007:
            for var in ['home','result','away']:
                df = df.drop(df[df[var].str.contains('\[', na = False)].index)
                df = df.drop(df[df[var].str.contains('\]', na = False)].index)        
        # trim the strings
        #df['home'] = df['home'].str.strip(' ')
        #df['away'] = df['away'].str.strip(' ')
        
        # in 2003, lots of rows start with a number and a colon
        if yr == 2003:                        
            df = df.drop(df[df['home'].str.contains('^ +?\d:', na = False)].index)
        
        df = df.drop(df[df['home'].str.contains('Round', na = False)].index)
        if len(df) != 306:
            sys.exit("Wrong number of matches")
    
        df = df.reset_index(drop=True)    
        # make sure we have strings
        df['home'] = df['home'].astype(str)
        df['away'] = df['away'].astype(str)
        df['result'] = df['result'].str.strip(' ')
        df['goalshome'] = pd.to_numeric(df['result'].str[0:1])
        df['goalsaway'] = pd.to_numeric(df['result'].str[2:3])
        
        #df['home'] = correct_names(df['home'],yr)
        #df['away'] = correct_names(df['away'],yr)
        
        df['spieltag'] = (df.index // 9) + 1
          
        df = df.drop('result',1)
        # Alle ergebnisse sind jetzt drin... jetzt vervielfältigen auf Team-Datensatz!    
        dfhome = df.copy()
        dfaway = df.copy()
        
        dfhome['team'] = dfhome['home']
        dfhome['opponent'] = dfhome['away']
        dfhome['goals_for'] = dfhome['goalshome']
        dfhome['goals_against'] = dfhome['goalsaway']
        
        dfaway['team'] = dfaway['away']
        dfaway['opponent'] = dfaway['home']
        dfaway['goals_for'] = dfaway['goalsaway']
        dfaway['goals_against'] = dfaway['goalshome']
        
        dfhome = dfhome.drop(['away','goalshome','goalsaway'],1)
        dfaway = dfaway.drop(['away','goalshome','goalsaway'],1)
        dfhome['home'] = 1
        dfaway['home'] = 0
        
        df = dfhome.append(dfaway)
        if len(df) != 612:
            sys.exit('wrong number of team obs')
                    
        df['pts'] = 3 * (df['goals_for'] > df['goals_against']) + (df['goals_for'] == df['goals_against'])
                
        # add yearly dataframe to dictionary    
        df_dict[yr]= df.reset_index()  
    
    # yearly results done, create one dataset for everything
    bl = pd.DataFrame(columns=['season','spieltag','team','opponent','goals_for','goals_against','pts']) 
    for yr in np.arange(1992,2017):
        bl = bl.append(df_dict[yr])
    bl = bl.reset_index(drop=True)
    bl['team'] = bl['team'].str.strip(' ')
    bl['opponent'] = bl['opponent'].str.strip(' ')
    bl['team'] = correct_names(bl['team'])
    bl['oppenent'] = correct_names(bl['opponent'])
          
    # check team x season
    print(pd.crosstab(df['team'], df['season']))
        
    bl.to_pickle(path+'buli')

## ENDE RAW DATA

if process_data == 1:
    df = pd.read_pickle(path+'buli')
    df = df.drop('index',1)
    
    df = df.drop(df[df.season==2017].index)
    
    df = df.sort_values(by=['season','spieltag'])
    goals_mday = df.groupby(['season','spieltag'])['goals_for'].sum()
    goals_mday = goals_mday.sort_values(0)
    mingoals = goals_mday.min()
    print('Seasons and Matchday with least goals')
    print(goals_mday[0:9])
    
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
    
    df.to_pickle(path+'buli_final')

df = pd.read_pickle(path+'buli_final')
print("Endplatzierung aller Mannschaften, die am ",spieltag,".Spieltag ",scf_points, " Punkte hatten.")
print(df[['season','team','rank','end_rank']][(df.spieltag==spieltag)&(df.points_cum==scf_points)])

# Noch interessanter: Ziehe eine Liste von Listen, die die Tabellenplatz-Entwicklung dieser Teams beschreibt
plotcases = df[['season','team']][(df.spieltag==spieltag)&(df.points_cum==scf_points)]
plotseasons = []
plotteams = []
for i in plotcases['season'].iteritems():
    plotseasons.append(i[1])
for i in plotteams['season'].iteritems():
    plotteams.append(i[1])
    
df[['spieltag','rank']][(df.season==1994)&(df.team=='Schalke')&(df['spieltag']>=spieltag)]
