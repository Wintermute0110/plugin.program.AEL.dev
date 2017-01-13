# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher scraping engine
#

# Copyright (c) 2016-2017 Wintermute0110 <wintermute0110@gmail.com>
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

# --- Python standard library ---
from __future__ import unicode_literals
import sys, urllib, urllib2, re

# --- AEL modules ---
from scrap import *
from scrap_info import *
from net_IO import *
from utils import *

# -----------------------------------------------------------------------------
# TheGamesDB scraper common code
# ----------------------------------------------------------------------------- 
class Scraper_TheGamesDB():
    def __init__(self):
        self.reset_cache()

    def check_cache(self, search_string, rom_base_noext, platform):
        if self.get_search_cached_search_string  == search_string and \
           self.get_search_cached_rom_base_noext == rom_base_noext and \
           self.get_search_cached_platform       == platform:
           log_debug('Scraper_TheGamesDB::check_cache Cache HIT.')
           return True
        log_debug('Scraper_TheGamesDB::check_cache Cache MISS. Updating cache.')

        return False

    def update_cache(self, search_string, rom_base_noext, platform, page_data):
        self.get_search_cached_search_string  = search_string
        self.get_search_cached_rom_base_noext = rom_base_noext
        self.get_search_cached_platform       = platform
        self.get_search_cached_page_data      = page_data

    def reset_cache(self):
        self.get_search_cached_search_string  = ''
        self.get_search_cached_rom_base_noext = ''
        self.get_search_cached_platform       = ''
        self.get_search_cached_page_data      = ''

    def get_cached_pagedata(self):
        return self.get_search_cached_page_data

    # Executes a search and returns a list of games found.
    def get_search(self, search_string, rom_base_noext, platform):
        scraper_platform = AEL_platform_to_TheGamesDB(platform)
        if DEBUG_SCRAPERS:
            log_debug('Scraper_TheGamesDB::get_search search_string       "{0}"'.format(search_string))
            log_debug('Scraper_TheGamesDB::get_search rom_base_noext      "{0}"'.format(rom_base_noext))
            log_debug('Scraper_TheGamesDB::get_search AEL platform        "{0}"'.format(platform))
            log_debug('Scraper_TheGamesDB::get_search TheGamesDB platform "{0}"'.format(scraper_platform))

        # >> Check if URL page data is in cache. If so it's a cache hit.
        # >> If cache miss, then update cache.
        # >> quote_plus() will convert the spaces into '+'.
        scraper_platform = scraper_platform.replace('-', ' ')
        url = 'http://thegamesdb.net/api/GetGamesList.php?' + \
              'name=' + urllib.quote_plus(search_string) + '&platform=' + urllib.quote_plus(scraper_platform)
        if self.check_cache(search_string, rom_base_noext, platform):
            page_data = self.get_cached_pagedata()
        else:
            page_data = net_get_URL_oneline(url)
            # >> If nothing is returned maybe a timeout happened. In this case, reset the cache.
            if page_data: self.update_cache(search_string, rom_base_noext, platform, page_data)
            else:         self.reset_cache()

        # --- Parse list of games ---
        # <Data>
        #   <Game>
        #     <id>26095</id>
        #     <GameTitle>Super Mario World: Brutal Mario</GameTitle>
        #     <ReleaseDate>01/01/2005</ReleaseDate>
        #     <Platform>Super Nintendo (SNES)</Platform>
        #   </Game>
        # </Data>
        games = re.findall("<Game><id>(.*?)</id><GameTitle>(.*?)</GameTitle>"
                           "<ReleaseDate>(.*?)</ReleaseDate><Platform>(.*?)</Platform></Game>", page_data)
        game_list = []
        for item in games:
            title    = text_unescape_and_untag_HTML(item[1])
            platform = text_unescape_and_untag_HTML(item[3])
            display_name = title + ' / ' + platform
            game = {'id' : item[0], 'display_name' : display_name, 'order' : 1}
            # Increase search score based on our own search
            if title.lower() == search_string.lower():          game['order'] += 1
            if title.lower().find(search_string.lower()) != -1: game['order'] += 1
            game_list.append(game)
        # >> Order list based on score
        game_list.sort(key = lambda result: result['order'], reverse = True)

        return game_list

# -----------------------------------------------------------------------------
# GameFAQs online metadata scraper
# ----------------------------------------------------------------------------- 
class Scraper_GameFAQs():
    def __init__(self):
        self.reset_cache()

    def check_cache(self, search_string, rom_base_noext, platform):
        if self.get_search_cached_search_string  == search_string and \
           self.get_search_cached_rom_base_noext == rom_base_noext and \
           self.get_search_cached_platform       == platform:
           log_debug('Scraper_GameFAQs::check_cache Cache HIT.')
           return True
        log_debug('Scraper_GameFAQs::check_cache Cache MISS. Updating cache.')

        return False

    def update_cache(self, search_string, rom_base_noext, platform, page_data):
        self.get_search_cached_search_string  = search_string
        self.get_search_cached_rom_base_noext = rom_base_noext
        self.get_search_cached_platform       = platform
        self.get_search_cached_page_data      = page_data

    def reset_cache(self):
        self.get_search_cached_search_string  = ''
        self.get_search_cached_rom_base_noext = ''
        self.get_search_cached_platform       = ''
        self.get_search_cached_page_data      = ''

    def get_cached_pagedata(self):
        return self.get_search_cached_page_data

    # Executes a search and returns a list of games found.
    def get_search(self, search_string, rom_base_noext, platform):
        scraper_platform = AEL_platform_to_GameFAQs(platform)
        if DEBUG_SCRAPERS:
            log_debug('Scraper_GameFAQs::get_search search_string      "{0}"'.format(search_string))
            log_debug('Scraper_GameFAQs::get_search rom_base_noext     "{0}"'.format(rom_base_noext))
            log_debug('Scraper_GameFAQs::get_search AEL platform       "{0}"'.format(platform))
            log_debug('Scraper_GameFAQs::get_search GameFAQs platform  "{0}"'.format(scraper_platform))

        # Example: 'street fighter', 'Nintendo SNES'
        # http://www.gamefaqs.com/search?platform=63&game=street+fighter
        search_string = search_string.replace(' ', '+')
        url = 'http://www.gamefaqs.com/search/index.html?' + \
              'platform={0}'.format(scraper_platform) + \
              '&game=' + search_string + ''
        if self.check_cache(search_string, rom_base_noext, platform):
            page_data = self.get_cached_pagedata()
        else:
            page_data = net_get_URL_oneline(url)
            # >> If nothing is returned maybe a timeout happened. In this case, reset the cache.
            if page_data: self.update_cache(search_string, rom_base_noext, platform, page_data)
            else:         self.reset_cache()

        # --- Old Parse list of games ---
        gets = re.findall('<td class="rtitle">(.*?)<a href="(.*?)"(.*?)class="sevent_(.*?)">(.*?)</a></td>', page_data)
        game_list = []
        for get in gets:
            game = {}
            game_name = text_unescape_HTML(get[4])
            gamesystem = get[1].split('/')
            game['id']           = get[1]
            game['display_name'] = game_name + ' / ' + gamesystem[1].capitalize()
            game['game_name']    = game_name # Additional GameFAQs scraper field
            game['order']        = 1         # Additional GameFAQs scraper field

            # Increase search score based on our own search
            # In the future use an scoring algortihm based on Levenshtein Distance
            title = text_unescape_HTML(get[4])
            if title.lower() == search_string.lower():          game['order'] += 1
            if title.lower().find(search_string.lower()) != -1: game['order'] += 1
            game_list.append(game)
        game_list.sort(key = lambda result: result['order'], reverse = True)

        return game_list

# -------------------------------------------------------------------------------------------------
# MobyGames (http://www.mobygames.com)
# MobyGames makes it difficult to extract information. Maybe a grammar parser will be needed.
# -------------------------------------------------------------------------------------------------
class Scraper_MobyGames():
    def __init__(self):
        self.reset_cache()

    def check_cache(self, search_string, rom_base_noext, platform):
        if self.get_search_cached_search_string  == search_string and \
           self.get_search_cached_rom_base_noext == rom_base_noext and \
           self.get_search_cached_platform       == platform:
           log_debug('Scraper_MobyGames::check_cache Cache HIT.')
           return True
        log_debug('Scraper_MobyGames::check_cache Cache MISS. Updating cache.')

        return False

    def update_cache(self, search_string, rom_base_noext, platform, page_data):
        self.get_search_cached_search_string  = search_string
        self.get_search_cached_rom_base_noext = rom_base_noext
        self.get_search_cached_platform       = platform
        self.get_search_cached_page_data      = page_data

    def reset_cache(self):
        self.get_search_cached_search_string  = ''
        self.get_search_cached_rom_base_noext = ''
        self.get_search_cached_platform       = ''
        self.get_search_cached_page_data      = ''

    def get_cached_pagedata(self):
        return self.get_search_cached_page_data

    # --- Search with no platform -----------------------------------------------------------------
    # http://www.mobygames.com/search/quick?q=super+mario+world
    #
    # <div class="d90b5a09a3d745cdd81e22d52188f8000">
    # <div class="searchResult"><div class="searchNumber">1.</div>
    # <div class="searchImage">
    #  <a href="/game/super-mario-world">
    #  <img class="searchResultImage" alt="Super Mario World New" 
    #       src="/images/covers/t/324893-super-mario-world-new-nintendo-3ds-front-cover.jpg" border="0" height="57" width="60">
    #  </a>
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
    # <br clear="all"></div>
    # <div class="d90b5a09a3d745cdd81e22d52188f8000">
    # <div class="searchResult"><div class="searchNumber">2.</div>
    # ...
    #
    # --- Search with platform --------------------------------------------------------------------
    # SNES is platform number 15
    # http://www.mobygames.com/search/quick?q=super+mario+world&p=15
    #
    # <h2>Results</h2>
    # <div id="searchResults">
    # <div class="searchSubSection">
    #  <div>Results <b>1</b> - <b>19</b> of <b>19</b> for <b>super mario world</b>
    # </div>
    # <div class="d90b5a09a3d745cdd81e22d52188f8000">
    # <div class="searchResult"><div class="searchNumber">1.</div>
    # <div class="searchImage">
    # <a href="/game/snes/super-mario-world">
    #  <img class="searchResultImage" alt="Super Mario World SNES Front Cover" border="0" 
    #       src="/images/covers/t/79892-super-mario-world-snes-front-cover.jpg" height="42" width="60" >
    # </a>
    # </div>
    # <div class="searchData">
    # <div class="searchTitle">Game: <a href="/game/snes/super-mario-world">Super Mario World</a></div>
    # <div class="searchDetails">
    # <span style="white-space: nowrap">SNES (<em>1990</em>)</span>
    # </div>
    # </div>
    # </div>
    # <br clear="all"></div>
    # <div class="d90b5a09a3d745cdd81e22d52188f8000">
    # <div class="searchResult"><div class="searchNumber">2.</div>
    # ...
    def get_search(self, search_string, rom_base_noext, platform):
        scraper_platform = AEL_platform_to_MobyGames(platform)
        if DEBUG_SCRAPERS:
            log_debug('Scraper_MobyGames::get_search search_string      "{0}"'.format(search_string))
            log_debug('Scraper_MobyGames::get_search rom_base_noext     "{0}"'.format(rom_base_noext))
            log_debug('Scraper_MobyGames::get_search AEL platform       "{0}"'.format(platform))
            log_debug('Scraper_MobyGames::get_search MobyGames platform "{0}"'.format(scraper_platform))

        # --- Search for games and get search page data ---
        # >> NOTE Search result page is a little bit different if platform used or not!!!
        # >> Findall returns a list of tuples. Tuples elements are the groups
        str_tokens = search_string.split(' ')
        str_mobygames = '+'.join(str_tokens)
        log_debug('Scraper_MobyGames::get_search str_mobygames = "{0}"'.format(str_mobygames))
        if scraper_platform == '':
            log_debug('Scraper_MobyGames::get_search NO plaform search')
            url = 'http://www.mobygames.com/search/quick?q={0}'.format(str_mobygames)
        else:
            log_debug('Scraper_MobyGames::get_search Search using platform')
            url = 'http://www.mobygames.com/search/quick?q={0}&p={1}'.format(str_mobygames, scraper_platform)
        if self.check_cache(search_string, rom_base_noext, platform):
            page_data = self.get_cached_pagedata()
        else:
            page_data = net_get_URL_oneline(url)
            # >> If nothing is returned maybe a timeout happened. In this case, reset the cache.
            if page_data: self.update_cache(search_string, rom_base_noext, platform, page_data)
            else:         self.reset_cache()

        # --- Extract information from page data ---
        game_list = []        
        if scraper_platform == '':
            # Search for: <span style="white-space: nowrap"><a href="/game/arcade/super-mario-world">Arcade</a> (<em>1991</em>)</span>
            m = re.findall('<span style="white-space: nowrap"><a href="(.+?)">(.+?)</a> \(<em>(.+?)</em>\)</span>', page_data)
            # print(m)
            for game_tuple in m:
                game = {}
                game_str = game_tuple[0].replace('/game/', '')
                t = re.findall('(.+)/(.+)', game_str)
                # print(game_str)
                # print(t)
                platform_raw = t[0][0]
                game_raw = t[0][1]
                if game_raw[-1] == '_': game_raw = game_raw[:-1]
                game_tokens = game_raw.split('-')
                game_tokens = [x.capitalize() for x in game_tokens]
                game_name   = text_unescape_HTML(' '.join(game_tokens))
                game['id']           = game_tuple[0]
                game['display_name'] = game_name + ' / {0}'.format(game_tuple[1])
                game['game_name']    = game_name # Additional MobyGames scraper field
                game_list.append(game)

        else:
            # Search for: <div class="searchTitle">Game: <a href="/game/snes/super-mario-world">Super Mario World</a>
            m = re.findall('<div class="searchTitle">Game: <a href="(.+?)">(.+?)</a>', page_data)
            # print(m)
            for game_tuple in m:
                game = {}
                game_name = text_unescape_HTML(game_tuple[1])
                game['id']           = game_tuple[0]
                game['display_name'] = game_name + ' / {0}'.format(platform)
                game['game_name']    = game_name # Additional MobyGames scraper field
                game_list.append(game)

        return game_list

# -----------------------------------------------------------------------------
# Arcade Database (for MAME) http://adb.arcadeitalia.net/
# ----------------------------------------------------------------------------- 
class Scraper_ArcadeDB():
    def __init__(self):
        self.get_search_cached_search_string  = ''
        self.get_search_cached_rom_base_noext = ''
        self.get_search_cached_platform       = ''
        self.get_search_cached_page_data      = ''

    def get_search(self, search_string, rom_base_noext, platform):
        if DEBUG_SCRAPERS:
            log_debug('Scraper_ArcadeDB::get_search search_string      "{0}"'.format(search_string))
            log_debug('Scraper_ArcadeDB::get_search rom_base_noext     "{0}"'.format(rom_base_noext))
            log_debug('Scraper_ArcadeDB::get_search AEL platform       "{0}"'.format(platform))

        # >> MAME always uses rom_base_noext and ignores search_string.
        # >> Example game search: http://adb.arcadeitalia.net/dettaglio_mame.php?game_name=dino
        url = 'http://adb.arcadeitalia.net/dettaglio_mame.php?lang=en&game_name={0}'.format(rom_base_noext)
        page_data = net_get_URL_oneline(url)

        # >> DEBUG
        # page_data_original = net_get_URL_original(url)
        # text_dump_str_to_file('arcadedb_search.txt', page_data_original)

        # --- Check if game was found ---
        game_list = []
        m = re.findall('<h2>Error: Game not found</h2>', page_data)
        if m:
            log_debug('Scraper_ArcadeDB::get_search Game NOT found "{0}"'.format(rom_base_noext))
            log_debug('Scraper_ArcadeDB::get_search Returning empty game_list')
        else:
            # >> Example URL: http://adb.arcadeitalia.net/dettaglio_mame.php?game_name=dino&lang=en
            # >> <div id="game_description" class="invisibile">Cadillacs and Dinosaurs (World 930201)</div>
            m_title = re.findall('<div id="game_description" class="invisibile">(.+?)</div>', page_data)
            if not m_title: return game_list
            game = {}
            game['display_name'] = m_title[0]
            game['id']           = url
            game['mame_name']    = rom_base_noext
            game_list.append(game)

        return game_list
