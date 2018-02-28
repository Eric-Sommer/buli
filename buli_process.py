#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 28 14:37:23 2018

@author: eric
"""
import pandas as pd

def processdata(path):
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
