# -*- coding: UTF-8 -*-

import re
import os
import urllib

# Return Game search list
def _get_games_list(search):
    results = []
    display = []
    try:
        f = urllib.urlopen('http://www.arcadehits.net/index.php?p=roms&jeu='+search)
        page = f.read().replace('\r\n', '').replace('\n', '')
        game = {}
        romname = ''.join(re.findall('<h4>(.*?)</h4>', page))
        game["title"] = unescape(romname)
        game["id"] = search
        game["gamesys"] = 'Arcade'
        if game["title"]:
            results.append(game)
            display.append(romname+" / "+game["gamesys"])
        return results,display
    except:
        return results,display

# Return 1st Game search
def _get_first_game(search,gamesys):
    results = []
    try:
        f = urllib.urlopen('http://www.arcadehits.net/index.php?p=roms&jeu='+search)
        page = f.read().replace('\r\n', '').replace('\n', '')
        game = {}
        romname = ''.join(re.findall('<h4>(.*?)</h4>', page))
        game["title"] = unescape(romname)
        game["id"] = search
        game["gamesys"] = 'Arcade'
        results.append(game)
        return results
    except:
        return results

# Return Game data
def _get_game_data(game_id):
    gamedata = {}
    gamedata["genre"] = ""
    gamedata["release"] = ""
    gamedata["studio"] = ""
    gamedata["plot"] = ""
    f = urllib.urlopen('http://www.arcadehits.net/index.php?p=roms&jeu='+game_id)
    page = f.read().replace('\r\n', '').replace('\n', '').replace('\r', '').replace('          ', '')
    game_genre = re.findall('<span class=mini>Genre: </span></td><td align=left>&nbsp;&nbsp;<strong>(.*?)>(.*?)</a>', page)
    if game_genre:
        gamedata["genre"] = game_genre[0][1]
    game_release = re.findall('<span class=mini>Ann&eacute;e: </span></td><td align=left>&nbsp;&nbsp;<strong>(.*?)>(.*?)</a>', page)
    if game_release:
        gamedata["release"] = game_release[0][1]
    game_studio = re.findall('<span class=mini>Fabricant: </span></td><td align=left>&nbsp;&nbsp;<strong>(.*?)>(.*?)</a>', page)
    if game_studio:
        gamedata["studio"] = game_studio[0][1]
    f = urllib.urlopen('http://www.arcadehits.net/page/viewdatfiles.php?show=history&jeu='+game_id)
    page = f.read().replace('\r\n', '').replace('\n', '').replace('\r', '')
    game_plot = re.findall('<br><br>(.*?)<br><br>',page)
    if game_plot:
        gamedata["plot"] = unescape(game_plot[0])
    return gamedata
        
def unescape(s):
    s = s.replace('<br>',' ')
    s = s.replace('<br/>',' ')
    s = s.replace('<br />',' ')
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&amp;", "&")
    s = s.replace("&#039;","'")
    s = s.replace('&quot;','"')
    s = s.replace('&nbsp;',' ')
    s = s.replace('&#x26;','&')
    s = s.replace('&#x27;',"'")
    s = s.replace('&#xB0;',"°")
    return s

