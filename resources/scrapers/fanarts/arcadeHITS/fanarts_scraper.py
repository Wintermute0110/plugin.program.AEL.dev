# -*- coding: UTF-8 -*-

import os
import re
import urllib

# Thumbnails list scrapper
def _get_fanarts_list(system,search,imgsize):
    covers = []
    results = []
    try:
        f = urllib.urlopen('http://www.arcadehits.net/page/viewdatfiles.php?show=snap&jeu='+search)
        page = f.read().replace('\r\n', '').replace('\n', '')
        results = re.findall('<img src=(.*?).png', page)
        for index, line in enumerate(results):
            covers.append(['http://www.arcadehits.net/'+line+'.png','http://www.arcadehits.net/'+line+'.png','Image '+str(index+1)])
        return covers
    except:
        return covers

# Get Thumbnail scrapper
def _get_fanart(image_url):
    return image_url

