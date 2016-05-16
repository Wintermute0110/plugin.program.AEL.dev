# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher scraping engine
#

# Copyright (c) 2016 Wintermute0110 <wintermute0110@gmail.com>
# Portions (c) 2010-2015 Angelscry
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import sys, urllib, urllib2, re

from scrap import *
from scrap_info import *
from net_IO import *
from utils import *

# -----------------------------------------------------------------------------
# TheGamesDB scraper common code
# ----------------------------------------------------------------------------- 
class Scraper_TheGamesDB():
    # Executes a search and returns a list of games found.
    def get_games_search(self, search_string, platform, rom_base_noext = ''):
        results_ret = []
        scraper_platform = AEL_platform_to_TheGamesDB(platform)
        if DEBUG_SCRAPERS:
            log_debug('get_games_search() AEL platform         "{}"'.format(platform))
            log_debug('get_games_search() TheGamesDB platform  "{}"'.format(scraper_platform))

        # --- This returns an XML file ---
        # <Data>
        #   <Game>
        #     <id>26095</id>
        #     <GameTitle>Super Mario World: Brutal Mario</GameTitle>
        #     <ReleaseDate>01/01/2005</ReleaseDate>
        #     <Platform>Super Nintendo (SNES)</Platform>
        #   </Game>
        # </Data>
        req = urllib2.Request('http://thegamesdb.net/api/GetGamesList.php?' +
                              'name=' + urllib.quote_plus(search_string) +
                              '&platform=' + urllib.quote_plus(scraper_platform))
        req.add_unredirected_header('User-Agent', USER_AGENT)
        page_data = net_get_URL_text(req)

        # --- Parse list of games ---
        games = re.findall("<Game><id>(.*?)</id><GameTitle>(.*?)</GameTitle><ReleaseDate>(.*?)</ReleaseDate><Platform>(.*?)</Platform></Game>", page_data)
        game_list = []
        for item in games:
            game = {'id' : item[0], 'display_name' : item[1], 'order' : 1}
            # Increase search score based on our own search
            title = item[1]
            if title.lower() == search_string.lower():          game["order"] += 1
            if title.lower().find(search_string.lower()) != -1: game["order"] += 1
            game_list.append(game)
        game_list.sort(key = lambda result: result["order"], reverse = True)
        results_ret = game_list

        return results_ret

# -----------------------------------------------------------------------------
# GameFAQs online metadata scraper
# ----------------------------------------------------------------------------- 
class Scraper_GameFAQs():
    # Executes a search and returns a list of games found.
    def get_games_search(self, search_string, platform, rom_base_noext = ''):
        results_ret = []
        scraper_platform = AEL_platform_to_GameFAQs(platform)
        if DEBUG_SCRAPERS:
            log_debug('get_games_search() AEL platform       "{}"'.format(platform))
            log_debug('get_games_search() GameFAQs platform  "{}"'.format(scraper_platform))

        # Example: 'street fighter', 'Nintendo SNES'
        # http://www.gamefaqs.com/search?platform=63&game=street+fighter
        search_string = search_string.replace(' ','+')
        req = urllib2.Request('http://www.gamefaqs.com/search/index.html?' +
                              'platform={}'.format(scraper_platform) +
                              '&game=' + search_string + '')
        req.add_unredirected_header('User-Agent', USER_AGENT)
        page_data = net_get_URL_text(req)

        # --- Old Parse list of games ---
        gets = {}
        gets = re.findall('<td class="rtitle">(.*?)<a href="(.*?)"(.*?)class="sevent_(.*?)">(.*?)</a></td>', page_data)
        game_list = []
        for get in gets:
            game = {}
            gamesystem = get[1].split('/')
            game["id"]           = get[1]
            game["title"]        = text_unescape_HTML(get[4])
            game["display_name"] = text_unescape_HTML(get[4])
            game["gamesys"]      = gamesystem[1].capitalize()
            game["order"]        = 1
            # Increase search score based on our own search
            title = game["title"] 
            if title.lower() == search_string.lower():          game["order"] += 1
            if title.lower().find(search_string.lower()) != -1: game["order"] += 1
            game_list.append(game)
        game_list.sort(key = lambda result: result["order"], reverse = True)
        results_ret = game_list

        return results_ret

# -----------------------------------------------------------------------------
# arcadeHITS
# ----------------------------------------------------------------------------- 
class Scraper_arcadeHITS():
    # Executes a search and returns a list of games found.
    def get_games_search(self, search_string, platform, rom_base_noext = ''):
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
                display.append(romname + " / " + game["gamesys"])
            return results,display
        except:
            return results,display

# -----------------------------------------------------------------------------
# MobyGames (http://www.mobygames.com)
# MobyGames makes it difficult to extract information. Maybe a grammar parser
# will be needed.
# ----------------------------------------------------------------------------- 
class Scraper_MobyGames():
    # Executes a search and returns a list of games found.
    #
    # http://www.mobygames.com/search/quick?q=super+mario+world
    # <div class="searchResult">
    # <div class="searchNumber">1.</div>
    # <div class="searchImage">
    # <a href="/game/super-mario-world">
    # <img class="searchResultImage" alt="Super Mario World New" src="/images/covers/t/324893-super-mario-world-new-nintendo-3ds-front-cover.jpg" border="0" height="57" width="60">
    # </a>
    # </div>
    # <div class="searchData">
    # <div class="searchTitle">Game: <a href="/game/super-mario-world">Super Mario World</a></div>
    # <div class="searchDetails">
    # <span style="white-space: nowrap"><a href="/game/arcade/super-mario-world">Arcade</a> (<em>1991</em>)</span>, 
    # <span style="white-space: nowrap"><a href="/game/new-nintendo-3ds/super-mario-world">New Nintendo 3DS</a> (<em>2016</em>)</span>, 
    # <span style="white-space: nowrap"><a href="/game/snes/super-mario-world">SNES</a> (<em>1990</em>)</span>, 
    # <span style="white-space: nowrap"><a href="/game/wii/super-mario-world">Wii</a> (<em>2006</em>)</span> and 
    # <span style="white-space: nowrap"><a href="/game/wii-u/super-mario-world">Wii U</a> (<em>2013</em>)</span>
    # </div>
    # </div>
    # </div>
    # <br clear="all">
    # </div>
    # <div class="d90b5a09a3d745cdd81e22d52188f8000">
    # <div class="searchResult">
    # <div class="searchNumber">2.</div>
    # ... 
    def get_games_search(self, search_string, platform, rom_base_noext = ''):
        return []
