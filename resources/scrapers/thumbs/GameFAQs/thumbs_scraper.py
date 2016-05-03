# -*- coding: UTF-8 -*-

import os
import re
import urllib2
from xbmcaddon import Addon

# Get Game first page
def _get_game_page_url(system,search):
    platform = _system_conversion(system)
    game = search.replace(' ', '+').lower()
    games = []
    try:
        req = urllib2.Request('http://www.gamefaqs.com/search/index.html?platform='+platform+'&game='+game+'&s=s')
        req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
        search_page = urllib2.urlopen(req)
        for line in search_page.readlines():
            if '>Images</a></td>' in line:
                games.append(re.findall('<td><a class="sevent_(.*?)" href="(.*?)">Images</a></td>', line.replace('\r\n', '')))
        if games:
            return ''.join(games[0][0][1])
    except:
        return ""

# Thumbnails list scrapper
def _get_thumbnails_list(system,search,region,imgsize):
    covers = []
    results = []
    try:
        game_id_url = _get_game_page_url(system,search)
        req = urllib2.Request('http://www.gamefaqs.com'+game_id_url)
        req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
        game_page = urllib2.urlopen(req)
        results = re.findall('<div class="img boxshot"><a href="(.*?)"><img class="img100" src="(.*?)" alt="(.*?)" /></a>', game_page.read().replace('\r\n', ''))
        if (region == "All" ):
            return results
        else:
            for result in results:
                if '('+region+')' in result[2]:
                    covers.append(result)
            return covers
    except:
        return covers

# Get Thumbnail scrapper
def _get_thumbnail(image_url):
    images = []
    try:
        req = urllib2.Request('http://www.gamefaqs.com' + image_url)
        req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
        search_page = urllib2.urlopen(req)
        for line in search_page.readlines():
            if 'Game Box Shot' in line:
                images = re.findall('g"><a href="(.*?)"><img class="full_boxshot" src="(.*?)"', line)
                return images[0][0]
    except:
        return ""

# Game systems DB identification
def _system_conversion(system_id):
    try:
        rootDir = Addon( id="plugin.program.advanced.launcher" ).getAddonInfo('path')
        if rootDir[-1] == ';':rootDir = rootDir[0:-1]
        resDir = os.path.join(rootDir, 'resources')
        scrapDir = os.path.join(resDir, 'scrapers')
        csvfile = open( os.path.join(scrapDir, 'gamesys'), "rb")
        conversion = []
        for line in csvfile.readlines():
            result = line.replace('\n', '').replace('"', '').split(',')
            if result[0].lower() == system_id.lower():
                if result[2]:
                    platform = result[2]
                    return platform
    except:
        return ''
