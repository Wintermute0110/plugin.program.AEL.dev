# -*- coding: UTF-8 -*-

import re
import os
import urllib, urllib2

from xbmcaddon import Addon
from operator import itemgetter, attrgetter

# Return Game search list
def _get_games_list(search):
    results = []
    display = []
    try:
        req = urllib2.Request('http://thegamesdb.net/api/GetGamesList.php?name='+urllib.quote_plus(search))
        req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
        f = urllib2.urlopen(req)
        page = f.read().replace("\n", "")
        games = re.findall("<Game><id>(.*?)</id><GameTitle>(.*?)</GameTitle>(.*?)<Platform>(.*?)</Platform></Game>", page)
        for item in games:
            game = {}
            game["id"] = "http://thegamesdb.net/api/GetGame.php?id="+item[0]
            game["title"] = item[1]
            game["gamesys"] = item[3]
            game["order"] = 1
            if ( game["title"].lower() == search.lower() ):
                game["order"] += 1
            if ( game["title"].lower().find(search.lower()) != -1 ):
                game["order"] += 1
            results.append(game)
            print game
        results.sort(key=lambda result: result["order"], reverse=True)
        for result in results:
            display.append(result["title"]+" / "+result["gamesys"])
        return results,display
    except:
        return results,display

# Return 1st Game search
def _get_first_game(search,gamesys):
    platform = _system_conversion(gamesys)
    results = []
    try:
        req = urllib2.Request('http://thegamesdb.net/api/GetGamesList.php?name='+urllib.quote_plus(search)+'&platform='+urllib.quote_plus(platform))
        req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
        f = urllib2.urlopen(req)
        page = f.read().replace("\n", "")
        if (platform == "Sega Genesis" ) :
            req = urllib2.Request('http://thegamesdb.net/api/GetGamesList.php?name='+urllib.quote_plus(search)+'&platform='+urllib.quote_plus('Sega Mega Drive'))
            req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
            f2 = urllib2.urlopen(req)
            page = page + f2.read().replace("\n", "")
        games = re.findall("<Game><id>(.*?)</id><GameTitle>(.*?)</GameTitle>(.*?)<Platform>(.*?)</Platform></Game>", page)
        for item in games:
            game = {}
            game["id"] = "http://thegamesdb.net/api/GetGame.php?id="+item[0]
            game["title"] = item[1]
            game["gamesys"] = item[3]
            game["order"] = 1
            if ( game["title"].lower() == search.lower() ):
                game["order"] += 1
            if ( game["title"].lower().find(search.lower()) != -1 ):
                game["order"] += 1
            results.append(game)
        results.sort(key=lambda result: result["order"], reverse=True)
        return results
    except:
        return results

# Return Game data
def _get_game_data(game_url):
    gamedata = {}
    gamedata["genre"] = ""
    gamedata["release"] = ""
    gamedata["studio"] = ""
    gamedata["plot"] = ""
    try:
        req = urllib2.Request(game_url)
        req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
        f = urllib2.urlopen(req)
        page = f.read().replace('\n', '')
        game_genre = ' / '.join(re.findall('<genre>(.*?)</genre>', page))
        if game_genre:
            gamedata["genre"] = unescape(game_genre)
        game_release = ''.join(re.findall('<ReleaseDate>(.*?)</ReleaseDate>', page))
        if game_release:
            gamedata["release"] = unescape(game_release[-4:])
        game_studio = ''.join(re.findall('<Developer>(.*?)</Developer>', page))
        if game_studio:
            gamedata["studio"] = unescape(game_studio)
        game_plot = ''.join(re.findall('<Overview>(.*?)</Overview>', page))
        if game_plot:
            gamedata["plot"] = unescape(game_plot)
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
                if result[4]:
                    platform = result[4]
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

