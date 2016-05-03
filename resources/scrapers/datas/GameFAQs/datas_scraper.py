# -*- coding: UTF-8 -*-

import re
import os
import urllib2
from xbmcaddon import Addon

# Return Game search list
def _get_games_list(search):
    display=[]
    results=[]
    try:
        req = urllib2.Request('http://www.gamefaqs.com/search/index.html?platform=0&game='+search.replace(' ','+')+'')
        req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
        f = urllib2.urlopen(req)
        gets = {}
        gets = re.findall('<td class="rtitle">(.*?)<a href="(.*?)"(.*?)class="sevent_(.*?)">(.*?)</a></td>', f.read().replace('\r\n', ''))
        for get in gets:
            game = {}
            gamesystem = get[1].split('/')
            game["id"] = 'http://www.gamefaqs.com'+get[1]
            game["title"] = unescape(get[4])
            game["gamesys"] = gamesystem[1].capitalize()
            results.append(game)
            display.append(game["title"]+" / "+game["gamesys"])
        return results,display
    except:
        return results,display

# Return 1st Game search
def _get_first_game(search,gamesys):
    platform = _system_conversion(gamesys)
    results = []
    try:
        req = urllib2.Request('http://www.gamefaqs.com/search/index.html?platform='+platform+'&game='+search.replace(' ','+')+'')
        req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
        f = urllib2.urlopen(req)
        gets = {}
        gets = re.findall('<td class="rtitle">(.*?)<a href="(.*?)"(.*?)class="sevent_(.*?)">(.*?)</a></td>', f.read().replace('\r\n', ''))
        for get in gets:
            game = {}
            game["id"] = 'http://www.gamefaqs.com'+get[1]
            game["title"] = unescape(get[4])
            game["gamesys"] = gamesys
            results.append(game)
        return results
    except:
        return results

# Return Game data
def _get_game_data(game_url):
    print game_url
    gamedata = {}
    gamedata["genre"] = ""
    gamedata["release"] = ""
    gamedata["studio"] = ""
    gamedata["plot"] = ""
    try:
        req = urllib2.Request(game_url)
        req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
        f = urllib2.urlopen(req)
        page = f.read().replace('\r\n', '')
        game_genre = re.findall('<li class="crumb top-crumb"><a href="/(.*?)">(.*?)</a></li><li class="crumb"><a href="/(.*?)/list-(.*?)">(.*?)</a></li>', page)
        if game_genre:
            gamedata["genre"] = game_genre[0][4]
        game_release = re.findall('Release: <a href="(.*?)">(.*?) &raquo;</a>', page)
        if game_release:
            gamedata["release"] = game_release[0][1][-4:]
        game_studio = re.findall('<li><a href="/features/company/(.*?)">(.*?)</a>', page)
        if game_studio:
            p = re.compile(r'<.*?>')
            gamedata["studio"] = p.sub('', game_studio[0][1])
        game_plot = re.findall('Description</h2></div><div class="body game_desc"><div class="desc">(.*?)</div>', page)
        if game_plot:
            gamedata["plot"] = unescape(game_plot[0])
        return gamedata
    except:
        return gamedata  

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
        
def unescape(s):
    s = s.replace('<br />',' ')
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&amp;", "&")
    s = s.replace("&#039;","'")
    s = s.replace('<br />',' ')
    s = s.replace('&quot;','"')
    s = s.replace('&nbsp;',' ')
    s = s.replace('&#x26;','&')
    s = s.replace('&#x27;',"'")
    s = s.replace('&#xB0;',"°")
    return s

