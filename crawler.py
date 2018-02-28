# -*- coding: utf-8 -*-
"""
CRAWLING FUSSBALLDATEN.DE
"""
import urllib.request as MyBrowser 
import os
import re
import pandas as pd
import numpy as np

seasons = np.arange(1963,2018)

def mkURL(season,spieltag):
    seasonstring = str(season)+'-'+str(season+1)[-2:]
    url = "http://www.kicker.de/news/fussball/bundesliga/spieltag/1-bundesliga/"+seasonstring+'/'+str(spieltag)+'/0/spieltag.html'
    return url
    
def crawler(path):
    datadir=path+'data/'    
    if not os.path.exists(datadir):
        os.mkdir(datadir)
        
    rawdir=datadir+'raw/'
    if not os.path.exists(rawdir):
        os.mkdir(rawdir)
        
    
    for s in seasons:
        for sp in range(1,35):
            request = MyBrowser.Request((mkURL(s,sp)))
            
            rawfile = rawdir+'kicker_'+str(s)+'_'+str(sp)+".html"
            downloaded = False
            if not os.path.isfile(rawfile):
                downloaded = True
                response = MyBrowser.urlopen(request)                   
                page = response.read()                                 
                file = open(rawfile, "wb")              
                file.write(page)
                file.close()
                
    print("Finished Downloading")

    buli_results = pd.DataFrame(columns=['season','spieltag','hometeam','awayteam','result'])    
    for s in seasons:
        print(str(s),end=' ')
        for sp in range(1,35):
            
            html = open(rawdir+'/kicker_'+str(s)+'_'+str(sp)+".html","r",encoding="utf-8").read()
            # find hometeam, awayteam, result in string.
            hometeam = []
            awayteam = []
            result = []
            HomeRegEx = re.compile('class="ovVrn ovVrnRight">(.+?)</a>')
            AwayRegEx = re.compile('class="ovVrn">(.+?)</a>')
            ResultRegEx = re.compile('<td class="alignleft nowrap" >(.+?)&nbsp;')
            
            for match in HomeRegEx.finditer(html):
                hometeam.append(match.group(1))
            for match in AwayRegEx.finditer(html):
                awayteam.append(match.group(1))
            for match in ResultRegEx.finditer(html):
                result.append(match.group(1))
            
            
            spieltag=pd.DataFrame(data=[[s]*9,[sp]*9,hometeam,awayteam,result]).T      
            spieltag = spieltag.rename(columns={0:'season',1:'spieltag',2:'hometeam',3:'awayteam',4:'result'})
            buli_results = buli_results.append(spieltag,ignore_index=True)
            
    # save raw data        
    buli_results.to_pickle(path+'all_kicker_results')

    return 0


    