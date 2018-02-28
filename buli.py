#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# Analyze historical Bundesliga results
# TO DO: 1. improve data. crawl fussballdaten.de for historical results
# 

@author: eric
"""
#path='/home/eric/Dropbox/buli/'
path='Z:/test/buli/'
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from buli_rawdata_rssf import *
from buli_process import *
from crawler import * 
#SWITCHES
raw_data = 0
process_data = 0
crawl = 1

spieltag = 24
scf_points = 17
      
if crawl == 1:
    crawler(path)


if raw_data == 1:
    rawdata(path)

if process_data == 1:
    processdata(path)


df = pd.read_pickle(path+'all_kicker_results')








aaa
df = pd.read_pickle(path+'buli_final')

print("Endplatzierung aller Mannschaften, die am ",spieltag,".Spieltag ",scf_points, " Punkte hatten.")
print(df[['season','team','rank','end_rank']][(df.spieltag==spieltag)&(df.points_cum==scf_points)])

# Noch interessanter: Ziehe eine Liste von Listen, die die Tabellenplatz-Entwicklung dieser Teams beschreibt
plotcases = df[['season','team']][(df.spieltag==spieltag)&(df.points_cum==scf_points)]
ranklist=[]
# Problem: Spieltag ist buggy wegen Nachholspielen.
for i in plotcases.index:
    ranklist.append(df['rank'][(df['season']==plotcases['season'][i])&(df['team']==plotcases['team'][i])&(df['spieltag']>=spieltag)])    
plotcases['ranklist'] = ranklist

spieltagplot = np.arange(spieltag,35)
# Now plot this
plt.clf()
for i in plotcases.index:
    print(i)
    plt.plot(spieltagplot,plotcases['ranklist'][i],label=plotcases['team'][i]+' '+str(plotcases['season'][i]))

plt.legend(loc='upper center', bbox_to_anchor=(spieltagplot[0], -0.05),fancybox=True, shadow=True, ncol=5)
plt.show()

