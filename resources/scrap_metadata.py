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

# --- Python standard library ---
from __future__ import unicode_literals

# --- AEL modules ---
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
        self.name       = 'NULL'

    def set_addon_dir(self, plugin_dir):
        pass

    def get_search(self, search_string, rom_base_noext, platform):
        return {}
    
    def get_metadata(self, game):
        return {}

# -----------------------------------------------------------------------------
# Offline scraper using XML files for MAME and No-Intro ROMs.
# -----------------------------------------------------------------------------
class metadata_Offline(Scraper_Metadata):
    # Offline XML data will be cached here (from disk)
    games = {}
    cached_xml_path = ''
    cached_platform = ''
    addon_dir = ''

    def __init__(self):
        self.name = 'AEL/GameDBInfo Offline'

    def set_addon_dir(self, plugin_dir):
        self.addon_dir = plugin_dir
        log_debug('metadata_Offline::set_addon_dir() self.addon_dir = {0}'.format(self.addon_dir))
        
    # Load XML information for this scraper and keep it cached in memory.
    # For offline scrapers.
    def initialise_scraper(self, platform):
        # Check if we have data already cached in object memory for this platform
        if self.cached_platform == platform:
            log_debug('metadata_Offline::initialise_scraper platform = {0} is cached in object.'.format(platform))
            return
    
        # What if platform is not in the official list dictionary? Then load
        # nothing and behave like the NULL scraper.
        try:
            xml_file = platform_AEL_to_Offline_GameDBInfo_XML[platform]
        except:
            log_debug('metadata_Offline::initialise_scraper Platform {0} not found'.format(platform))
            log_debug('metadata_Offline::initialise_scraper Defaulting to Unknown')
            self.games = {}
            self.cached_xml_path = ''
            self.cached_platform = 'Unknown'
            return

        # Load XML database and keep it in memory for subsequent calls
        xml_path = os.path.join(self.addon_dir, xml_file)
        log_debug('metadata_Offline::initialise_scraper Loading XML {0}'.format(xml_path))
        self.games = fs_load_GameInfo_XML(xml_path)
        if not self.games:
            self.games = {}
            self.cached_xml_path = ''
            self.cached_platform = 'Unknown'
            return
        self.cached_xml_path = xml_path
        self.cached_platform = platform
        log_debug('metadata_Offline::initialise_scraper cached_xml_path = {0}'.format(self.cached_xml_path))
        log_debug('metadata_Offline::initialise_scraper cached_platform = {0}'.format(self.cached_platform))

    # List of games found
    def get_search(self, search_string, rom_base_noext, platform):
        log_verb("metadata_Offline::get_search Searching '{0}' '{1}' '{2}'".format(search_string, rom_base_noext, platform))
        results_ret = []

        # If not cached XML data found (maybe offline scraper does not exist
        # for this platform or cannot be loaded) return.
        self.initialise_scraper(platform)
        if not self.games:
            return results_ret

        # Search MAME games
        if platform == 'MAME':
            log_verb("metadata_Offline::get_search Mode MAME searching for '{0}'".format(rom_base_noext))
            
            # --- MAME rom_base_noext is exactly the rom name ---
            if rom_base_noext.lower() in self.games:
                game = {'id'           : self.games[rom_base_noext]['name'], 
                        'display_name' : self.games[rom_base_noext]['description'] }
                results_ret.append(game)
            else:
                return results_ret

        # Search No-Intro games
        else:
            log_verb("metadata_Offline::get_search Mode No-Intro searching for '{0}'".format(search_string))
            search_string_lower = search_string.lower()
            regexp = '.*{0}.*'.format(search_string_lower)
            try:
                # Sometimes this produces raise error, v # invalid expression
                p = re.compile(regexp)
            except:
                log_info('metadata_Offline::get_search Exception in re.compile(regexp)')
                log_info('metadata_Offline::get_search regexp = "{0}"'.format(regexp))
                return results_ret

            game_list = []
            for key in self.games:
                this_game_name = self.games[key]['name']
                this_game_name_lower = this_game_name.lower()
                match = p.match(this_game_name_lower)
                if match:
                    game = {'id'           : self.games[key]['name'], 
                            'display_name' : self.games[key]['name'],
                            'order': 1 }
                    # If there is an exact match of the No-Intro name put that game first.
                    if search_string == this_game_name: game['order'] += 1
                    if rom_base_noext == this_game_name: game['order'] += 1
                    # Append to list
                    game_list.append(game)
            game_list.sort(key = lambda result: result['order'], reverse = True)
            results_ret = game_list

        return results_ret

    # game is dictionary returned by the metadata_Offline.get_game_search()
    def get_metadata(self, game):
        gamedata = {'title' : '', 'genre' : '', 'year' : '', 'studio' : '', 'plot' : ''}

        if self.cached_platform == 'MAME':
            key = game['id']
            log_verb("metadata_Offline::get_metadata Mode MAME id = '{0}'".format(key))
            gamedata['title']  = self.games[key]['description']
            gamedata['genre']  = self.games[key]['genre']
            gamedata['year']   = self.games[key]['year']
            gamedata['studio'] = self.games[key]['manufacturer']
            # gamedata['plot'] = self.games[key]['plot']

        # Unknown platform. Behave like NULL scraper
        elif self.cached_platform == 'Unknown':
            log_verb("metadata_Offline::get_metadata Mode Unknown. Doing nothing.")

        # No-Intro scraper
        else:
            key = game['id']
            log_verb("metadata_Offline::get_metadata Mode No-Intro id = '{0}'".format(key))
            gamedata['title']  = self.games[key]['description']
            gamedata['genre']  = self.games[key]['genre']
            gamedata['year']   = self.games[key]['year']
            gamedata['studio'] = self.games[key]['manufacturer']
            gamedata['plot']   = self.games[key]['story']

        return gamedata

# -----------------------------------------------------------------------------
# TheGamesDB online metadata scraper
# -----------------------------------------------------------------------------
class metadata_TheGamesDB(Scraper_Metadata, Scraper_TheGamesDB):
    def __init__(self):
        self.name = 'TheGamesDB'

    def set_addon_dir(self, plugin_dir):
        pass

    # Call common code in parent class
    def get_search(self, search_string, rom_base_noext, platform):
        return Scraper_TheGamesDB.get_search(self, search_string, rom_base_noext, platform)

    # game is dictionary returned by the Scraper_TheGamesDB.get_game_search()
    def get_metadata(self, game):
        gamedata = {'title' : '', 'genre' : '', 'year' : '', 'studio' : '', 'plot' : ''}

        # --- TheGamesDB returns an XML file with GetGame.php?id ---
        game_id_url = 'http://thegamesdb.net/api/GetGame.php?id=' + game['id']
        log_debug('metadata_TheGamesDB::get_metadata Game URL "{0}"'.format(game_id_url))
        page_data = net_get_URL_oneline(game_id_url)

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

    def set_addon_dir(self, plugin_dir):
        pass

    # Call common code in parent class
    def get_search(self, search_string, rom_base_noext, platform):
        return Scraper_GameFAQs.get_search(self, search_string, rom_base_noext, platform)

    def get_metadata(self, game):
        # --- Get game page ---
        game_id_url = 'http://www.gamefaqs.com' + game['id']
        log_debug('metadata_GameFAQs::get_metadata game_id_url "{0}"'.format(game_id_url))
        page_data = net_get_URL_oneline(game_id_url)

        # --- Process metadata ---
        gamedata = {'title' : '', 'genre' : '', 'year' : '', 'studio' : '', 'plot' : ''}
        gamedata['title'] = game['display_name']

        # <ol class="crumbs">
        # <li class="crumb top-crumb"><a href="/snes">Super Nintendo</a></li>
        # <li class="crumb"><a href="/snes/category/54-action">Action</a></li>
        # <li class="crumb"><a href="/snes/category/57-action-fighting">Fighting</a></li>
        # <li class="crumb"><a href="/snes/category/86-action-fighting-2d">2D</a></li>
        # </ol>
        game_genre = re.findall('<ol class="crumbs"><li class="crumb top-crumb"><a href="(.*?)">(.*?)</a></li><li class="crumb"><a href="(.*?)">(.*?)</a></li>', page_data)
        if game_genre: gamedata['genre'] = game_genre[0][3]

        # <li><b>Release:</b> <a href="/snes/588699-street-fighter-alpha-2/data">November 1996 ?</a></li>
        game_release = re.findall('<li><b>Release:</b> <a href="(.*?)">(.*?) &raquo;</a></li>', page_data)
        if game_release: gamedata['year'] = game_release[0][1][-4:]

        # <li><a href="/company/2324-capcom">Capcom</a></li>
        game_studio = re.findall('<li><a href="/company/(.*?)">(.*?)</a>', page_data)
        if game_studio:
            p = re.compile(r'<.*?>')
            gamedata['studio'] = p.sub('', game_studio[0][1])

        game_plot = re.findall('Description</h2></div><div class="body game_desc"><div class="desc">(.*?)</div>', page_data)
        if game_plot: gamedata['plot'] = text_unescape_HTML(game_plot[0])
            
        return gamedata

# -----------------------------------------------------------------------------
# MobyGames http://www.mobygames.com
# -----------------------------------------------------------------------------
class metadata_MobyGames(Scraper_Metadata, Scraper_MobyGames):
    def __init__(self):
        self.name = 'MobyGames'

    def set_addon_dir(self, plugin_dir):
        pass

    # Call common code in parent class
    def get_search(self, search_string, rom_base_noext, platform):
        return Scraper_MobyGames.get_search(self, search_string, rom_base_noext, platform)

    def get_metadata(self, game):
        gamedata = {'title' : '', 'genre' : '', 'year' : '', 'studio' : '', 'plot' : ''}

        # --- Get game page ---
        game_id_url = 'http://www.mobygames.com' + game['id']
        log_debug('metadata_MobyGames::get_metadata game_id_url "{0}"'.format(game_id_url))
        page_data = net_get_URL_oneline(game_id_url)

        # --- Process metadata ---
        # Example: http://www.mobygames.com/game/chakan
        #
        # <td width="48%"><div id="coreGameRelease">
        # <div style="font-size: 100%; font-weight: bold;">Published by</div>
        # <div style="font-size: 90%; padding-left: 1em; padding-bottom: 0.25em;"><a href="/company/sega-of-america-inc">SEGA&nbsp;of&nbsp;America,&nbsp;Inc.</a></div>
        # <div style="font-size: 100%; font-weight: bold;">Developed by</div>
        # <div style="font-size: 90%; padding-left: 1em; padding-bottom: 0.25em;"><a href="/company/extended-play">Extended&nbsp;Play</a></div>
        # <div style="font-size: 100%; font-weight: bold;">Released</div>
        # <div style="font-size: 90%; padding-left: 1em; padding-bottom: 0.25em;"><a href="/game/chakan/release-info">1992</a></div>
        # <div style="font-size: 100%; font-weight: bold;">Platforms</div>
        # <div style="font-size: 90%; padding-left: 1em; padding-bottom: 0.25em;"><a href="/game/game-gear/chakan">Game Gear</a>, 
        # <a href="/game/genesis/chakan">Genesis</a></div></div>
        # </td>
        # <td width="48%"><div id="coreGameGenre"><div>
        # <div style="font-size: 100%; font-weight: bold;">Genre</div>
        # <div style="font-size: 90%; padding-left: 1em; padding-bottom: 0.25em;"><a href="/genre/sheet/action/">Action</a></div>
        # <div style="font-size: 100%; font-weight: bold;">Perspective</div>
        # <div style="font-size: 90%; padding-left: 1em; padding-bottom: 0.25em;"><a href="/genre/sheet/3rd-person-perspective/">3rd-person&nbsp;[DEPRECATED]</a>, 
        # <a href="/genre/sheet/side-view/">Side&nbsp;view</a></div><div style="font-size: 100%; font-weight: bold;">Gameplay</div>
        # <div style="font-size: 90%; padding-left: 1em; padding-bottom: 0.25em;"><a href="/genre/sheet/fighting/">Fighting</a>, 
        # <a href="/genre/sheet/platform/">Platform</a></div><div style="font-size: 100%; font-weight: bold;">Misc</div>
        # <div style="font-size: 90%; padding-left: 1em; padding-bottom: 0.25em;"><a href="/genre/sheet/licensed-title/">Licensed&nbsp;Title</a></div></div></div>
        # </td>
        gamedata = {'title' : '', 'genre' : '', 'year' : '', 'studio' : '', 'plot' : ''}
        gamedata['title'] = game['display_name']

        game_genre = re.findall('Genre</div><div style="font-size: 90%; padding-left: 1em; padding-bottom: 0.25em;"><a href="(.*?)">(.*?)</a>', page_data)
        print(game_genre)
        if game_genre: gamedata['genre'] = text_unescape_HTML(game_genre[0][1])

        game_year = re.findall('Released</div><div style="font-size: 90%; padding-left: 1em; padding-bottom: 0.25em;"><a href="(.*?)">(.*?)</a>', page_data)
        if game_year: gamedata['year'] = text_unescape_HTML(game_year[0][1])

        return gamedata

# -----------------------------------------------------------------------------
# Arcade Database (for MAME) http://adb.arcadeitalia.net/
# ----------------------------------------------------------------------------- 
class metadata_ArcadeDB(Scraper_Metadata, Scraper_ArcadeDB):
    def __init__(self):
        self.name = 'GameFAQs'

    def set_addon_dir(self, plugin_dir):
        pass

    # Call common code in parent class
    def get_search(self, search_string, rom_base_noext, platform):
        return Scraper_ArcadeDB.get_search(self, search_string, rom_base_noext, platform)

    def get_metadata(self, game):
        gamedata = {'title' : '', 'genre' : '', 'year' : '', 'studio' : '', 'plot' : ''}

        # --- Get game page ---
        game_id_url = game['id'] 
        log_debug('metadata_ArcadeDB::get_metadata game_id_url "{0}"'.format(game_id_url))
        page_data = net_get_URL_oneline(game_id_url)

        # --- Process metadata ---
        m_title = re.findall('<div id="game_description" class="invisibile">(.+?)</div>', page_data)


        return gamedata
