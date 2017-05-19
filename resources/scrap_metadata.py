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

# --- AEL modules ---
from scrap import *
from scrap_common import *
from disk_IO import *

# -----------------------------------------------------------------------------
# NULL scraper, does nothing
# -----------------------------------------------------------------------------
class metadata_NULL(Scraper_Metadata):
    def __init__(self):
        self.name = 'NULL'

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

    # --- Search games and return list of matches ---
    def get_search(self, search_string, rom_base_noext, platform):
        log_verb("metadata_Offline::get_search Searching '{0}' | '{1}' | '{2}'".format(search_string, rom_base_noext, platform))
        results_ret = []

        # If not cached XML data found (maybe offline scraper does not exist for this platform or 
        # cannot be loaded) return.
        self.initialise_scraper(platform)
        if not self.games: return results_ret

        # --- Search MAME games ---
        if platform == 'MAME':
            log_verb("metadata_Offline::get_search Mode MAME -> Search '{0}'".format(rom_base_noext))
            
            # --- MAME rom_base_noext is exactly the rom name ---
            rom_base_noext_lower = rom_base_noext.lower()
            if rom_base_noext_lower in self.games:
                game = {'id'           : self.games[rom_base_noext_lower]['name'], 
                        'display_name' : self.games[rom_base_noext_lower]['description']}
                results_ret.append(game)
            else:
                return results_ret

        # --- Search No-Intro games ---
        else:
            # --- First try an exact match using rom_base_noext ---
            log_verb("metadata_Offline::get_search Mode No-Intro -> Exact search '{0}'".format(rom_base_noext))
            if rom_base_noext in self.games:
                log_verb("metadata_Offline::get_search Mode No-Intro -> Exact match found")
                game = {'id'           : rom_base_noext,
                        'display_name' : self.games[rom_base_noext]['name']}
                results_ret.append(game)
                return results_ret
            log_verb("metadata_Offline::get_search Mode No-Intro -> No exact match found")

            # --- If nothing found, do a fuzzy search ---
            log_verb("metadata_Offline::get_search Mode No-Intro -> Fuzzy search '{0}'".format(search_string))
            search_string_lower = search_string.lower()
            regexp = '.*{0}.*'.format(search_string_lower)
            try:
                # >> Sometimes this produces: raise error, v # invalid expression
                p = re.compile(regexp)
            except:
                log_info('metadata_Offline::get_search Exception in re.compile(regexp)')
                log_info('metadata_Offline::get_search regexp = "{0}"'.format(regexp))
                return results_ret

            game_list = []
            for key in self.games:
                this_game_name       = self.games[key]['name']
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
        gamedata = new_gamedata_dic()

        # --- MAME scraper ---
        if self.cached_platform == 'MAME':
            key = game['id']
            log_verb("metadata_Offline::get_metadata Mode MAME id = '{0}'".format(key))
            gamedata['title']  = self.games[key]['description']
            gamedata['year']   = self.games[key]['year']
            gamedata['genre']  = self.games[key]['genre']
            gamedata['studio'] = self.games[key]['manufacturer']

        # >> Unknown platform. Behave like NULL scraper
        elif self.cached_platform == 'Unknown':
            log_verb("metadata_Offline::get_metadata Mode Unknown. Doing nothing.")

        # --- No-Intro scraper ---
        else:
            key = game['id']
            log_verb("metadata_Offline::get_metadata Mode No-Intro id = '{0}'".format(key))
            gamedata['title']    = self.games[key]['description']
            gamedata['year']     = self.games[key]['year']
            gamedata['genre']    = self.games[key]['genre']
            gamedata['studio']   = self.games[key]['manufacturer']
            gamedata['nplayers'] = self.games[key]['player']
            gamedata['esrb']     = self.games[key]['rating']
            gamedata['plot']     = self.games[key]['story']

        return gamedata

# -----------------------------------------------------------------------------
# TheGamesDB online metadata scraper
# -----------------------------------------------------------------------------
class metadata_TheGamesDB(Scraper_Metadata, Scraper_TheGamesDB):
    def __init__(self):
        self.name = 'TheGamesDB'
        Scraper_TheGamesDB.__init__(self)

    def set_addon_dir(self, plugin_dir):
        pass

    # Call common code in parent class
    def get_search(self, search_string, rom_base_noext, platform):
        return Scraper_TheGamesDB.get_search(self, search_string, rom_base_noext, platform)

    # game is dictionary returned by the Scraper_TheGamesDB.get_game_search()
    def get_metadata(self, game):
        gamedata = new_gamedata_dic()

        # --- TheGamesDB returns an XML file with GetGame.php?id ---
        game_id_url = 'http://thegamesdb.net/api/GetGame.php?id=' + game['id']
        log_debug('metadata_TheGamesDB::get_metadata Game URL "{0}"'.format(game_id_url))
        page_data = net_get_URL_oneline(game_id_url)

        # --- Parse game page data ---
        game_title = ''.join(re.findall('<GameTitle>(.*?)</GameTitle>', page_data))
        gamedata['title'] = text_unescape_and_untag_HTML(game_title) if game_title else ''

        game_release = ''.join(re.findall('<ReleaseDate>(.*?)</ReleaseDate>', page_data))
        gamedata['year'] = text_unescape_and_untag_HTML(game_release[-4:]) if game_release else ''

        game_genre = ' / '.join(re.findall('<genre>(.*?)</genre>', page_data))
        gamedata['genre'] = text_unescape_and_untag_HTML(game_genre) if game_genre else ''

        game_studio = ''.join(re.findall('<Developer>(.*?)</Developer>', page_data))
        gamedata['studio'] = text_unescape_and_untag_HTML(game_studio) if game_studio else ''

        game_studio = ''.join(re.findall('<Players>(.*?)</Players>', page_data))
        gamedata['nplayers'] = text_unescape_and_untag_HTML(game_studio) if game_studio else ''

        game_studio = ''.join(re.findall('<ESRB>(.*?)</ESRB>', page_data))
        gamedata['esrb'] = text_unescape_and_untag_HTML(game_studio) if game_studio else ''

        game_plot = ''.join(re.findall('<Overview>(.*?)</Overview>', page_data))
        gamedata['plot'] = text_unescape_and_untag_HTML(game_plot) if game_plot else ''

        return gamedata

# -----------------------------------------------------------------------------
# GameFAQs online metadata scraper
# -----------------------------------------------------------------------------
class metadata_GameFAQs(Scraper_Metadata, Scraper_GameFAQs):
    def __init__(self):
        self.name = 'GameFAQs'
        Scraper_GameFAQs.__init__(self)

    def set_addon_dir(self, plugin_dir):
        pass

    # >> Call common code in parent class
    def get_search(self, search_string, rom_base_noext, platform):
        return Scraper_GameFAQs.get_search(self, search_string, rom_base_noext, platform)

    # >> URL example https://www.gamefaqs.com/genesis/454495-sonic-the-hedgehog
    def get_metadata(self, game):
        # --- Get game page ---
        game_id_url = 'http://www.gamefaqs.com' + game['id']
        log_debug('metadata_GameFAQs::get_metadata game_id_url "{0}"'.format(game_id_url))
        page_data = net_get_URL_oneline(game_id_url)

        # --- Process metadata ---
        gamedata = new_gamedata_dic()
        gamedata['title'] = game['game_name']

        # <li><b>Release:</b> <a href="/snes/588699-street-fighter-alpha-2/data">November 1996 ?</a></li>
        game_release = re.findall('<li><b>Release:</b> <a href="(.*?)">(.*?) &raquo;</a></li>', page_data)
        if game_release: gamedata['year'] = game_release[0][1][-4:]

        # <ol class="crumbs">
        # <li class="crumb top-crumb"><a href="/snes">Super Nintendo</a></li>
        # <li class="crumb"><a href="/snes/category/54-action">Action</a></li>
        # <li class="crumb"><a href="/snes/category/57-action-fighting">Fighting</a></li>
        # <li class="crumb"><a href="/snes/category/86-action-fighting-2d">2D</a></li>
        # </ol>
        game_genre = re.findall('<ol class="crumbs"><li class="crumb top-crumb"><a href="(.*?)">(.*?)</a></li><li class="crumb"><a href="(.*?)">(.*?)</a></li>', page_data)
        if game_genre: gamedata['genre'] = game_genre[0][3]

        # <li><a href="/company/2324-capcom">Capcom</a></li>
        game_studio = re.findall('<li><a href="/company/(.*?)">(.*?)</a>', page_data)
        if game_studio:
            p = re.compile(r'<.*?>')
            gamedata['studio'] = p.sub('', game_studio[0][1])

        game_plot = re.findall('Description</h2></div><div class="body game_desc"><div class="desc">(.*?)</div>', page_data)
        if game_plot: gamedata['plot'] = text_unescape_and_untag_HTML(game_plot[0])
            
        return gamedata

# -----------------------------------------------------------------------------
# MobyGames http://www.mobygames.com
# -----------------------------------------------------------------------------
class metadata_MobyGames(Scraper_Metadata, Scraper_MobyGames):
    def __init__(self):
        self.name = 'MobyGames'
        Scraper_MobyGames.__init__(self)

    def set_addon_dir(self, plugin_dir):
        pass

    # Call common code in parent class
    def get_search(self, search_string, rom_base_noext, platform):
        return Scraper_MobyGames.get_search(self, search_string, rom_base_noext, platform)

    def get_metadata(self, game):
        # --- Get game page ---
        game_id_url = 'http://www.mobygames.com' + game['id']
        log_debug('metadata_MobyGames::get_metadata game_id_url "{0}"'.format(game_id_url))
        page_data = net_get_URL_oneline(game_id_url)

        # --- Process metadata ---
        # Example: http://www.mobygames.com/game/chakan
        #
        # <td width="48%"><div id="coreGameRelease">
        # ...
        # <div style="font-size: 100%; font-weight: bold;">Released</div>
        # <div style="font-size: 90%; padding-left: 1em; padding-bottom: 0.25em;"><a href="/game/chakan/release-info">1992</a></div>
        # ...
        # </td>
        gamedata = new_gamedata_dic()
        gamedata['title'] = game['game_name']

        # NOTE Year can be
        #      A) YYYY
        #      B) MMM, YYYY (MMM is Jan, Feb, ...)
        #      C) MMM DD, YYYY
        game_year = re.findall('Released</div><div style="font-size: 90%; padding-left: 1em; padding-bottom: 0.25em;"><a href="(.*?)">(.*?)</a>', page_data)
        if game_year: 
            year_str = text_unescape_and_untag_HTML(game_year[0][1])
            # print('Year_str = "' + year_str + '"')
            year_A = re.findall('^([0-9]{4})', year_str)
            year_B = re.findall('([\w]{3}), ([0-9]{4})', year_str)
            year_C = re.findall('([\w]{3}) ([0-9]{2}), ([0-9]{4})', year_str)
            # print('Year_A ' + unicode(year_A))
            # print('Year_B ' + unicode(year_B))
            # print('Year_C ' + unicode(year_C))
            if year_A:   gamedata['year'] = year_A[0]
            elif year_B: gamedata['year'] = year_B[0][1]
            elif year_C: gamedata['year'] = year_C[0][2]

        game_genre = re.findall('Genre</div><div style="font-size: 90%; padding-left: 1em; padding-bottom: 0.25em;"><a href="(.*?)">(.*?)</a>', page_data)
        if game_genre: gamedata['genre'] = text_unescape_and_untag_HTML(game_genre[0][1])

        game_studio = re.findall('Published by</div><div style="font-size: 90%; padding-left: 1em; padding-bottom: 0.25em;"><a href="(.*?)">(.*?)</a>', page_data)
        if game_studio: gamedata['studio'] = text_unescape_and_untag_HTML(game_studio[0][1])

        game_description = re.findall('<h2>Description</h2>(.*?)<div class="sideBarLinks">', page_data)
        if game_description: gamedata['plot'] = text_unescape_and_untag_HTML(game_description[0])
        
        return gamedata

# -----------------------------------------------------------------------------
# Arcade Database (for MAME) http://adb.arcadeitalia.net/
# ----------------------------------------------------------------------------- 
class metadata_ArcadeDB(Scraper_Metadata, Scraper_ArcadeDB):
    def __init__(self):
        self.name = 'Arcade Database'
        Scraper_ArcadeDB.__init__(self)

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
        # text_dump_str_to_file('arcadedb_get_metadata.txt', page_data)

        # --- Process metadata ---
        # Example game page: http://adb.arcadeitalia.net/dettaglio_mame.php?lang=en&game_name=aliens
        #
        # --- Title ---
        # <div class="table_caption">Name: </div> <div class="table_value"> <span class="dettaglio">Aliens (World set 1)</span>
        fa_title = re.findall('<div class="table_caption">Name: </div> <div class="table_value"> <span class="dettaglio">(.*?)</span>', page_data)
        if fa_title: gamedata['title'] = fa_title[0]

        # --- Genre/Category ---
        # <div class="table_caption">Category: </div> <div class="table_value"> <span class="dettaglio">Platform / Shooter Scrolling</span>
        fa_genre = re.findall('<div class="table_caption">Category: </div> <div class="table_value"> <span class="dettaglio">(.*?)</span>', page_data)
        if fa_genre: gamedata['genre'] = fa_genre[0]

        # --- Year ---
        # <div class="table_caption">Year: </div> <div class="table_value"> <span class="dettaglio">1990</span> <div id="inputid89"
        fa_year = re.findall('<div class="table_caption">Year: </div> <div class="table_value"> <span class="dettaglio">(.*?)</span>', page_data)
        if fa_year: gamedata['year'] = fa_year[1]

        # --- Studio ---
        # <div class="table_caption">Manufacturer: </div> <div class="table_value"> <span class="dettaglio">Konami</span> </div>
        fa_studio = re.findall('<div class="table_caption">Manufacturer: </div> <div class="table_value"> <span class="dettaglio">(.*?)</span> </div>', page_data)
        if fa_studio: gamedata['studio'] = fa_studio[0]
        
        # --- Plot ---
        # <div id="history_detail" class="extra_info_detail"><div class="history_title"></div>Aliens © 1990 Konami........&amp;id=63&amp;o=2</div>
        fa_plot = re.findall('<div id="history_detail" class="extra_info_detail"><div class=\'history_title\'></div>(.*?)</div>', page_data)
        if fa_plot: gamedata['plot'] = text_unescape_and_untag_HTML(fa_plot[0])

        return gamedata
