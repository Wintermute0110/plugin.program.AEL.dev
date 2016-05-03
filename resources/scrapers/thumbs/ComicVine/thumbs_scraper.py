# -*- coding: UTF-8 -*-

import os
import re
import urllib,urllib2
import simplejson
from xbmcaddon import Addon

# Get Comics pages
def _get_game_page_url(system,search):
    comics_results = []
    try:
        f = urllib.urlopen('http://www.comicvine.com/search/?indices[0]=cv_issue&q="'+urllib.quote(search.lower())+'"')
        page = f.read().replace('\r\n', '').replace('\n', '').strip('\t')
        issues = re.findall('/4000-(.*?)/">        <div class="img imgflare">                      <img src="(.*?)" alt="(.*?)">', page)
        for issue in issues:
            comic = {}
            comic["url"] = 'http://www.comicvine.com/issue/4000-'+issue[0]+'/'
            comics_results.append(comic)
        return comics_results
    except:
        return comics_results

# Thumbnails list scrapper
def _get_thumbnails_list(system,search,region,imgsize):
    covers = []
    game_id_url = _get_game_page_url(system,search)
    try:
        for comic in game_id_url:
            cover_number = 1
            game_page = urllib.urlopen(str(comic["url"].encode('utf-8','ignore')))
            if game_page:
                for line in game_page.readlines():
                    if 'fluid-width' in line:
                        result = ''.join(re.findall('<img src="(.*?)" class="fluid-width"/>', line))
                        covers.append((result,result,"Cover "+str(cover_number)))
                        cover_number = cover_number + 1
        return covers
    except:
        return covers

# Get Thumbnail scrapper
def _get_thumbnail(image_url):
    return image_url
