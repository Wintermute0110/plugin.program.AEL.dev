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

# -----------------------------------------------------------------------------
# We support online an offline scrapers.
# Note that this module does not depend on Kodi stuff at all, and can be
# called externally from console Python scripts for testing of the scrapers.
# -----------------------------------------------------------------------------

from scrap import *
from scrap_common import *
from disk_IO import *
try:
    import utils_kodi
except:
    import utils_kodi_standalone

# -----------------------------------------------------------------------------
# NULL scraper, does nothing
# -----------------------------------------------------------------------------
class metadata_NULL(Scraper_Metadata):
    def __init__(self):
        self.name = 'NULL'
        self.fancy_name = 'NULL Metadata scraper'

    def get_games_search(self, search_string, platform, rom_base_noext = ''):
        return {}
    
    def get_game_metadata(self, game):
        return {}

# -----------------------------------------------------------------------------
# Offline scraper using XML files for MAME and No-Intro ROMs.
# -----------------------------------------------------------------------------
class metadata_Offline(Scraper_Metadata):
    def __init__(self):
        self.name = 'Offline'
        self.fancy_name = 'Offline Metadata scraper'

    # Offline XML data will be cached here (from disk)
    games = {}
    cached_games_name = ''
    cached_platform = ''

    # Load XML information for this scraper and keep it cached in memory.
    # For offline scrapers.
    def initialise_scraper(self, platform):
        # What if platform is not in the official list dictionary? Then load
        # nothing and behave like the NULL scraper.
        try:
            xml_file = offline_scrapers_dic[platform]
        except:
            games = {}
            cached_games_name = cached_platform = ''
            return

        # Check if we have data already cached in object memory for this platform
        if self.cached_platform == platform:
            return

        # Load XML database and keep it in memory for subsequent calls
        self.games = fs_load_GameInfo_XML(xml_file)
        if not self.games:
            games = {}
            cached_games_name = cached_platform = ''
            return
        self.cached_games_name = xml_file
        self.cached_platform == platform

    # List of games found
    # game = { 'id' : str, 'title' : str, 'display_name' : str, ...}
    def get_games_search(self, search_string, platform, rom_base_noext = ''):
        results = []

        # If not cached XML data found (maybe offline scraper does not exist
        # for this platform or cannot be loaded) return.
        self.initialise_scraper(platform)
        if not self.games:
            return results

        # Search games. Differentitate between MAME and No-Intro scrapers.
        if platform == 'MAME':
            log_verb('Searching for "{0}" in game name'.format(rom_base_noext))

            if rom_base_noext in self.games:
                print(' name         = "{0}"'.format(self.games[rom_base_noext]['name']))
                print(' description  = "{0}"'.format(self.games[rom_base_noext]['description']))
                print(' year         = "{0}"'.format(self.games[rom_base_noext]['year']))
                print(' manufacturer = "{0}"'.format(self.games[rom_base_noext]['manufacturer']))
            else:
                log_verb('Not found')
        else:
            log_verb('Searching for "{0}" in game name'.format(rom_base_noext))
            regexp = '.*{0}.*'.format(rom_base_noext.lower())
            p = re.compile(regexp)
            log_debug('Search regexp "{0}"'.format(regexp))
            for key in self.games:
              # Make search case insensitive.
              name_str = self.games[key]['name'].lower()
              log_debug('Test string "{0}"'.format(name_str))
              match = p.match(name_str)
              if match:
                print(' name        = "{0}"'.format(self.games[key]['name']))
                print(' description = "{0}"'.format(self.games[key]['description']))
                print(' year        = "{0}"'.format(self.games[key]['year']))

        return results

    # game is dictionary returned by the metadata_Offline.get_game_search()
    def get_game_metadata(self, game):
        gamedata = {'title' : '', 'genre' : '', 'release' : '', 'studio' : '', 'plot' : ''}

        return {}

# -----------------------------------------------------------------------------
# TheGamesDB online metadata scraper
# -----------------------------------------------------------------------------
class metadata_TheGamesDB(Scraper_Metadata, Scraper_TheGamesDB):
    def __init__(self):
        self.name = 'TheGamesDB'
        self.fancy_name = 'TheGamesDB Metadata scraper'

    # Call common code in parent class
    def get_games_search(self, search_string, platform, rom_base_noext = ''):
        return Scraper_TheGamesDB.get_games_search(self, search_string, platform, rom_base_noext)

    # game is dictionary returned by the Scraper_TheGamesDB.get_game_search()
    def get_game_metadata(self, game):
        gamedata = {'title' : '', 'genre' : '', 'release' : '', 'studio' : '', 'plot' : ''}

        # --- TheGamesDB returns an XML file with GetGame.php?id ---
        game_id = game['id']
        log_debug('get_game_search() Game ID "{}"'.format(game_id))
        req = urllib2.Request('http://thegamesdb.net/api/GetGame.php?id=' + game_id)
        req.add_unredirected_header('User-Agent', USER_AGENT)
        page_data = net_get_URL_text(req)

        # --- Parse game page data ---
        game_title = ''.join(re.findall('<GameTitle>(.*?)</GameTitle>', page_data))
        gamedata['title'] = text_unescape_HTML(game_title) if game_title else ''

        game_genre = ' / '.join(re.findall('<genre>(.*?)</genre>', page_data))
        gamedata['genre'] = text_unescape_HTML(game_genre) if game_genre else ''

        game_release = ''.join(re.findall('<ReleaseDate>(.*?)</ReleaseDate>', page_data))
        gamedata['release'] = text_unescape_HTML(game_release[-4:]) if game_release else ''
            
        game_studio = ''.join(re.findall('<Developer>(.*?)</Developer>', page_data))
        gamedata['studio'] = text_unescape_HTML(game_studio) if game_studio else ''
            
        game_plot = ''.join(re.findall('<Overview>(.*?)</Overview>', page_data))
        gamedata['plot'] = text_unescape_HTML(game_plot) if game_plot else ''

        return gamedata

# -----------------------------------------------------------------------------
# GameFAQs online metadata scraper
# -----------------------------------------------------------------------------
class metadata_GameFAQs(Scraper_Metadata, Scraper_GameFAQs):
    def __init__(self):
        self.name = 'GameFAQs'
        self.fancy_name = 'GameFAQs Metadata scraper'

    # Call common code in parent class
    def get_games_search(self, search_string, platform, rom_base_noext = ''):
        return Scraper_GameFAQs.get_games_search(self, search_string, platform, rom_base_noext)

    def get_game_metadata(self, game):
        gamedata = {'title' : '', 'genre' : '', 'release' : '', 'studio' : '', 'plot' : ''}
        
        # Get game page
        game_id = game['id']
        log_debug('get_game_search() Game ID "{}"'.format(game_id))
        req = urllib2.Request('http://www.gamefaqs.com' + game_id)
        req.add_unredirected_header('User-Agent', USER_AGENT)
        page_data = net_get_URL_text(req)

        # Process metadata
        gamedata['title'] = game['title']

        # <ol class="crumbs">
        # <li class="crumb top-crumb"><a href="/snes">Super Nintendo</a></li>
        # <li class="crumb"><a href="/snes/category/54-action">Action</a></li>
        # <li class="crumb"><a href="/snes/category/57-action-fighting">Fighting</a></li>
        # <li class="crumb"><a href="/snes/category/86-action-fighting-2d">2D</a></li>
        # </ol>
        game_genre = re.findall('<ol class="crumbs"><li class="crumb top-crumb"><a href="(.*?)">(.*?)</a></li><li class="crumb"><a href="(.*?)">(.*?)</a></li>', page_data)
        if game_genre:
            gamedata["genre"] = game_genre[0][3]

        # <li><b>Release:</b> <a href="/snes/588699-street-fighter-alpha-2/data">November 1996 »</a></li>
        game_release = re.findall('<li><b>Release:</b> <a href="(.*?)">(.*?) &raquo;</a></li>', page_data)
        if game_release:
            gamedata["release"] = game_release[0][1][-4:]

        # <li><a href="/company/2324-capcom">Capcom</a></li>
        game_studio = re.findall('<li><a href="/company/(.*?)">(.*?)</a>', page_data)
        if game_studio:
            p = re.compile(r'<.*?>')
            gamedata["studio"] = p.sub('', game_studio[0][1])
            
        game_plot = re.findall('Description</h2></div><div class="body game_desc"><div class="desc">(.*?)</div>', page_data)
        if game_plot:
            gamedata["plot"] = text_unescape_HTML(game_plot[0])
            
        return gamedata

# -----------------------------------------------------------------------------
# arcadeHITS
# Site in French. Valid for MAME.
# -----------------------------------------------------------------------------
class metadata_arcadeHITS(Scraper_Metadata):
    def __init__(self):
        self.name = 'arcadeHITS'
        self.fancy_name = 'arcadeHITS Metadata scraper'

    def get_game_data(self, game_url):
        gamedata = {'title' : '', 'genre' : '', 'release' : '', 'studio' : '', 'plot' : ''}
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

# -----------------------------------------------------------------------------
# MobyGames http://www.mobygames.com
# -----------------------------------------------------------------------------
