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
    datadir=path+'/data'    
    if not os.path.exists(datadir):
        os.mkdir(datadir)
        
    rawdir=datadir+'/raw'
    if not os.path.exists(rawdir):
        os.mkdir(rawdir)
        
    
    for s in seasons:
        print(str(s),'...',end='')        
        for sp in range(1,35):
            print(str(sp),end=' ')            
            request = MyBrowser.Request((mkURL(s,sp)))
            
            rawfile = rawdir+'/kicker_'+str(s)+'_'+str(sp)+".html"
            downloaded = False
            if not os.path.isfile(rawfile):
                downloaded = True
                response = MyBrowser.urlopen(request)                   
                page = response.read()                                 
                file = open(rawfile, "wb")              
                file.write(page)
                file.close()
                
    print("Finished Downloading")
    return 0
