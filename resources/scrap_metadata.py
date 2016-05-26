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
        self.name       = 'NULL'
        self.fancy_name = 'NULL Metadata scraper'

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
        self.name       = 'Offline'
        self.fancy_name = 'Offline Metadata scraper'

    def set_addon_dir(self, plugin_dir):
        self.addon_dir = plugin_dir
        log_debug('metadata_Offline::set_addon_dir() self.addon_dir = {}'.format(self.addon_dir))
        
    # Load XML information for this scraper and keep it cached in memory.
    # For offline scrapers.
    def initialise_scraper(self, platform):
        # Check if we have data already cached in object memory for this platform
        if self.cached_platform == platform:
            log_debug('metadata_Offline::initialise_scraper platform = {} is cached in object.'.format(platform))
            return
    
        # What if platform is not in the official list dictionary? Then load
        # nothing and behave like the NULL scraper.
        try:
            xml_file = offline_scrapers_dic[platform]
        except:
            log_debug('metadata_Offline::initialise_scraper Platform {} not found'.format(platform))
            log_debug('metadata_Offline::initialise_scraper Defaulting to Unknown')
            self.games = {}
            self.cached_xml_path = ''
            self.cached_platform = 'Unknown'
            return

        # Load XML database and keep it in memory for subsequent calls
        xml_path = os.path.join(self.addon_dir, xml_file)
        log_debug('metadata_Offline::initialise_scraper Loading XML {}'.format(xml_path))
        self.games = fs_load_GameInfo_XML(xml_path)
        if not self.games:
            self.games = {}
            self.cached_xml_path = ''
            self.cached_platform = 'Unknown'
            return
        self.cached_xml_path = xml_path
        self.cached_platform = platform
        log_debug('metadata_Offline::initialise_scraper cached_xml_path = {}'.format(self.cached_xml_path))
        log_debug('metadata_Offline::initialise_scraper cached_platform = {}'.format(self.cached_platform))

    # List of games found
    def get_search(self, search_string, rom_base_noext, platform):
        log_verb("metadata_Offline::get_search Searching '{}' '{}' '{}'".format(search_string, platform, rom_base_noext))
        results_ret = []

        # If not cached XML data found (maybe offline scraper does not exist
        # for this platform or cannot be loaded) return.
        self.initialise_scraper(platform)
        if not self.games:
            return results_ret

        # Search MAME games
        if platform == 'MAME':
            log_verb("metadata_Offline::get_search Mode MAME searching for '{}'".format(rom_base_noext))
            
            # --- MAME rom_base_noext is exactly the rom name ---
            if rom_base_noext.lower() in self.games:
                game = {'id'           : self.games[rom_base_noext]['name'], 
                        'display_name' : self.games[rom_base_noext]['description'] }
                results_ret.append(game)
            else:
                return results_ret

        # Search No-Intro games
        else:
            log_verb("metadata_Offline::get_search Mode No-Intro searching for '{}'".format(search_string))
            search_string_lower = search_string.lower()
            regexp = '.*{}.*'.format(search_string_lower)
            p = re.compile(regexp)
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
            gamedata['title'] = self.games[key]['description']
            # gamedata['genre'] = self.games[key]['category']
            gamedata['year'] = self.games[key]['year']
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
        self.name       = 'TheGamesDB'
        self.fancy_name = 'TheGamesDB Metadata scraper'

    def set_addon_dir(self, plugin_dir):
        pass

    # Call common code in parent class
    def get_search(self, search_string, rom_base_noext, platform):
        log_verb("metadata_TheGamesDB::get_search Searching '{}' '{}' '{}'".format(search_string, platform, rom_base_noext))
        return Scraper_TheGamesDB.get_search(self, search_string, platform, rom_base_noext)

    # game is dictionary returned by the Scraper_TheGamesDB.get_game_search()
    def get_metadata(self, game):
        gamedata = {'title' : '', 'genre' : '', 'year' : '', 'studio' : '', 'plot' : ''}

        # --- TheGamesDB returns an XML file with GetGame.php?id ---
        game_id = game['id']
        log_debug('metadata_TheGamesDB::get_metadata Game ID "{}"'.format(game_id))
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
        self.name       = 'GameFAQs'
        self.fancy_name = 'GameFAQs Metadata scraper'

    def set_addon_dir(self, plugin_dir):
        pass

    # Call common code in parent class
    def get_search(self, search_string, rom_base_noext, platform):
        log_verb("metadata_GameFAQs::get_search Searching '{}' '{}' '{}'".format(search_string, platform, rom_base_noext))
        return Scraper_GameFAQs.get_search(self, search_string, platform, rom_base_noext)

    def get_metadata(self, game):
        gamedata = {'title' : '', 'genre' : '', 'year' : '', 'studio' : '', 'plot' : ''}
        
        # Get game page
        game_id = game['id']
        log_debug('metadata_GameFAQs::get_metadata Game ID "{}"'.format(game_id))
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
            gamedata["year"] = game_release[0][1][-4:]

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
        self.name       = 'arcadeHITS'
        self.fancy_name = 'arcadeHITS Metadata scraper'

    def set_addon_dir(self, plugin_dir):
        pass

    def get_search(self, search_string, rom_base_noext, platform):
        pass

    def get_metadata(self, game_url):
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

# -----------------------------------------------------------------------------
# Giantbomb
# -----------------------------------------------------------------------------
