#
# Old or obsolete code.
#


# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher scraping engine
#

# Copyright (c) 2016-2018 Wintermute0110 <wintermute0110@gmail.com>
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
from __future__ import division
import abc
import datetime
import time

# --- AEL packages ---
from utils import *

# -------------------------------------------------------------------------------------------------
# We support online an offline scrapers.
# Note that this module does not depend on Kodi stuff at all, and can be
# called externally from console Python scripts for testing of the scrapers.
# -------------------------------------------------------------------------------------------------

# --- "GLOBALS" -----------------------------------------------------------------------------------
DEBUG_SCRAPERS = 1

#--------------------------------------------------------------------------------------------------
# Base class for all scrapers
#--------------------------------------------------------------------------------------------------
class LegacyScraper:
    # Short name to refer to object in code
    name = ''

    # This function is called when the user wants to search a whole list of games.
    #   search_string   Online scrapers use this
    #   rom_base_noext  Offline scrapers and online MAME require the unmodified ROM name
    #   platform        AEL platform name. Will be translated to scraper internal name
    #
    # Returns:
    #   results = [game, game, ... ]
    #   game = {
    #       'id' : str,             String that allows to obtain the game URL (ID number) or the URL itself.
    #       'display_name' : str,   Scraped name of the ROM/Launcher/Game.
    #       ...
    #   }
    #   game dictionary may have more fields depending on the scraper (which are not used outside that scraper)
    def get_search(self, search_string, rom_base_noext, platform):
        raise NotImplementedError('Subclass must implement get_search() abstract method')

# -------------------------------------------------------------------------------------------------
# Metadata scrapers base class
# All scrapers (offline or online) must implement the abstract methods.
# -------------------------------------------------------------------------------------------------
class Scraper_Metadata(LegacyScraper):
    def new_gamedata_dic(self):
        gamedata = {
            'title'     : '',
            'year'      : '',
            'genre'     : '',
            'developer' : '',
            'nplayers'  : '',
            'esrb'      : '',
            'plot'      : ''
        }

        return gamedata

    # Offline scrapers need to know the plugin installation directory.
    # For offline scrapers just pass.
    def set_addon_dir(self, plugin_dir):
        raise NotImplementedError('Subclass must implement set_addon_dir() abstract method')

    # This is called after get_games_search() to get metadata of a particular ROM.
    # game is a dictionary from the dictionary list returned by get_game_search()
    # get_game_search() is usually common code for the online scrapers.
    #
    # Mandatory fields returned:
    #   gamedata dictionary created by new_gamedata_dic()
    def get_metadata(self, game):
        raise NotImplementedError('Subclass must implement get_metadata() abstract method')

# --- Asset scrapers ------------------------------------------------------------------------------
# All asset scrapers are online scrapers.
# -------------------------------------------------------------------------------------------------
class Scraper_Asset(LegacyScraper):
    # If scraper needs additional configuration then call this function.
    def set_options(self, region, imgsize):
        raise NotImplementedError('Subclass must implement set_options() abstract method')

    # Returns True if scraper supports the asset, False otherwise.
    def supports_asset(self, asset_kind):
        raise NotImplementedError('Subclass must implement supports_asset() abstract method')
        
    # Obtain a set of images of the given kind, based on a previous search with get_search()
    #
    # Returns:
    #   images = [image_dic, image_dic, ... ]
    #   image_dic = {
    #       'name' : str,   Name of the image (e.g., 'Boxfront 1')
    #       'id'   : str,   String that allows to obtain the game URL (ID number) or the URL itself.
    #       'URL'  : str    URL of a thumb to display the image. Some websites have small size
    #                           images for preview. It could be the URL of the full size image itself.
    #       ...    : ...    Scrapers may add additional fields for image_dic dictionary if needed.
    #   }
    def get_images(self, game, asset_kind):
        raise NotImplementedError('Subclass must implement get_images() abstract method')

    # Resolves the full size image URL. id is the string returned by get_images()
    # Returns:
    #   (URL,            Full URL of the full size image.
    #    img_extension)  Extension of the image.
    def resolve_image_URL(self, image_dic):
        raise NotImplementedError('Subclass must implement resolve_image_URL() abstract method')

#--------------------------------------------------------------------------------------------------
# Instantiate scraper objects
#--------------------------------------------------------------------------------------------------
from scrap_metadata import *
from scrap_asset import *

# --- Metadata scraper objects ---
Offline_meta_obj    = metadata_Offline()
TheGamesDB_meta_obj = metadata_TheGamesDB()
GameFAQs_meta_obj   = metadata_GameFAQs()
MobyGames_meta_obj  = metadata_MobyGames()
ArcadeDB_meta_obj   = metadata_ArcadeDB()

# --- Metadata scrapers ---
# >> This list MUST match the settings configuration in settings.xml or bad things will happen.
scrapers_metadata = [
    Offline_meta_obj, TheGamesDB_meta_obj, GameFAQs_meta_obj, MobyGames_meta_obj
]

scrapers_metadata_MAME = [
    Offline_meta_obj, TheGamesDB_meta_obj, GameFAQs_meta_obj, MobyGames_meta_obj, ArcadeDB_meta_obj
]

# --- Asset scraper objects ---
# >> There is only one instantiated object for every scraper. Scraper objects cache all possible
# >> requests made to the scraper to save bandwidth and increase speed.
NULL_obj       = asset_NULL()
TheGamesDB_obj = asset_TheGamesDB()
GameFAQs_obj   = asset_GameFAQs()
MobyGames_obj  = asset_MobyGames()
ArcadeDB_obj   = asset_ArcadeDB()

# --- Asset scrapers ---
# >> This list is used in _gui_edit_asset()
scrapers_asset = [TheGamesDB_obj, GameFAQs_obj, MobyGames_obj, ArcadeDB_obj]

# >> These lists MUST match the settings configuration in settings.xml or bad things will happen.
# >> These lists are used in the ROM Scanner.
# >> Boxfront  -> Cabinet
# >> Boxback   -> CPanel
# >> Cartridge -> PCB
# >> Banner    -> Marquee
scrapers_title          = [ NULL_obj, TheGamesDB_obj, GameFAQs_obj, MobyGames_obj               ]
scrapers_snap           = [ NULL_obj, TheGamesDB_obj, GameFAQs_obj, MobyGames_obj               ]
scrapers_boxfront       = [ NULL_obj, TheGamesDB_obj, GameFAQs_obj, MobyGames_obj               ]
scrapers_boxback        = [ NULL_obj, TheGamesDB_obj, GameFAQs_obj, MobyGames_obj               ]
scrapers_cartridge      = [ NULL_obj,                               MobyGames_obj               ]
scrapers_fanart         = [ NULL_obj, TheGamesDB_obj                                            ]
scrapers_banner         = [ NULL_obj, TheGamesDB_obj                                            ]
scrapers_clearlogo      = [ NULL_obj, TheGamesDB_obj                                            ]

# >> MAME scrapers
scrapers_title_MAME     = [ NULL_obj, TheGamesDB_obj, GameFAQs_obj, MobyGames_obj, ArcadeDB_obj ]
scrapers_snap_MAME      = [ NULL_obj, TheGamesDB_obj, GameFAQs_obj, MobyGames_obj, ArcadeDB_obj ]
scrapers_cabinet_MAME   = [ NULL_obj, TheGamesDB_obj, GameFAQs_obj, MobyGames_obj, ArcadeDB_obj ]
scrapers_cpanel_MAME    = [ NULL_obj, TheGamesDB_obj, GameFAQs_obj, MobyGames_obj, ArcadeDB_obj ]
scrapers_pcb_MAME       = [ NULL_obj,                               MobyGames_obj, ArcadeDB_obj ]
scrapers_fanart_MAME    = [ NULL_obj, TheGamesDB_obj                                            ]
scrapers_marquee_MAME   = [ NULL_obj, TheGamesDB_obj,                              ArcadeDB_obj ]
scrapers_clearlogo_MAME = [ NULL_obj, TheGamesDB_obj,                              ArcadeDB_obj ]
scrapers_flyer_MAME     = [ NULL_obj,                                              ArcadeDB_obj ]

# #################################################################################################
# #################################################################################################
# Scraper factories.
# #################################################################################################
# #################################################################################################

def getScraper(asset_kind, settings, useMame = False):
    if useMame:
        return getMameScraper(asset_kind, settings)

    key = ASSET_SETTING_KEYS[asset_kind]

    if key == '':
        return None

    if key not in settings:
        log_warning("Scraper with key {} not set in settings".format(key))
        return None

    scraper_index = settings[key]

    if asset_kind == ASSET_TITLE:
        return scrapers_title[scraper_index]

    if asset_kind == ASSET_SNAP:
        return scrapers_snap[scraper_index]

    if asset_kind == ASSET_BOXFRONT:
        return scrapers_boxfront[scraper_index]

    if asset_kind == ASSET_BOXBACK:
        return scrapers_boxback[scraper_index]

    if asset_kind == ASSET_CARTRIDGE:
        return scrapers_cartridge[scraper_index]

    if asset_kind == ASSET_FANART:
        return scrapers_fanart[scraper_index]

    if asset_kind == ASSET_BANNER:
        return scrapers_banner[scraper_index]

    if asset_kind == ASSET_CLEARLOGO:
        return scrapers_clearlogo[scraper_index]

    # >> Flyers only supported by ArcadeDB (for MAME). If platform is not MAME then deactivate
    # >> this scraper.
    # >> Map (not supported yet, use a null scraper)
    # >> Manual (not supported yet, use a null scraper)
    # >> Trailer (not supported yet, use a null scraper)
    return NULL_obj

def getMameScraper(asset_kind, settings):
    key = MAME_ASSET_SETTING_KEYS[asset_kind]

    if key == '':
        return None

    if key not in settings:
        log_warning("Scraper with key {} not set in settings".format(key))
        return None

    scraper_index = settings[key]

    if asset_kind == ASSET_TITLE:
        return scrapers_title_MAME[scraper_index]

    if asset_kind == ASSET_SNAP:
        return scrapers_snap_MAME[scraper_index]

    if asset_kind == ASSET_BOXFRONT:
        return scrapers_cabinet_MAME[scraper_index]

    if asset_kind == ASSET_BOXBACK:
        return scrapers_cpanel_MAME[scraper_index]

    if asset_kind == ASSET_CARTRIDGE:
        return scrapers_pcb_MAME[scraper_index]

    if asset_kind == ASSET_FANART:
        return scrapers_fanart_MAME[scraper_index]

    if asset_kind == ASSET_BANNER:
        return scrapers_marquee_MAME[scraper_index]

    if asset_kind == ASSET_CLEARLOGO:
        return scrapers_clearlogo_MAME[scraper_index]

    if asset_kind == ASSET_FLYER:
        return scrapers_flyer_MAME[scraper_index]

    # >> Map (not supported yet, use a null scraper)
    # >> Manual (not supported yet, use a null scraper)
    # >> Trailer (not supported yet, use a null scraper)
    return NULL_obj


# -------------------------------------------------- #
# Needs to be divided into separate classes for each actual scraper.
# Could only inherit OnlineScraper and implement _get_candidates()
# and _get_candidate()
# -------------------------------------------------- #
class OnlineMetadataScraper(Scraper):
    
    def __init__(self, scraper_implementation, settings, launcher, fallbackScraper = None): 
        
        self.scraper_implementation = scraper_implementation 
        scraper_settings = ScraperSettings.create_from_settings(settings)

        super(OnlineMetadataScraper, self).__init__(scraper_settings, launcher, True, [], fallbackScraper)
        
    def getName(self):
        return 'Online Metadata scraper using {0}'.format(self.scraper_implementation.name)

    def _get_candidates(self, search_term, romPath, rom):
        
        platform = self.launcher.get_platform()
        results = self.scraper_implementation.get_search(search_term, romPath.getBase_noext(), platform)

        return results
    
    def _load_metadata(self, candidate, romPath, rom):
        self.gamedata = self.scraper_implementation.get_metadata(candidate)

    def _load_assets(self, candidate, romPath, rom):
        pass
    
    def _get_image_url_from_page(self, candidate, asset_info):        
        return candidate['url']

class OnlineAssetScraper(Scraper):
    
    scrap_asset_cached_dic = None

    def __init__(self, scraper_implementation, asset_kind, asset_info, settings, launcher, fallbackScraper = None): 

        self.scraper_implementation = scraper_implementation

        # >> id(object)
        # >> This is an integer (or long integer) which is guaranteed to be unique and constant for 
        # >> this object during its lifetime.
        self.scraper_id = id(scraper_implementation)
        
        self.asset_kind = asset_kind
        self.asset_info = asset_info

        self.asset_directory = launcher.get_asset_path(asset_info)
        
        
        # --- Initialise cache used in OnlineAssetScraper() as a static variable ---
        # >> This cache is used to store the selected game from the get_search() returned list.
        # >> The idea is that get_search() is used only once for each asset.
        if OnlineAssetScraper.scrap_asset_cached_dic is None:
            OnlineAssetScraper.scrap_asset_cached_dic = {}
        
        scraper_settings = ScraperSettings.create_from_settings(settings)
        super(OnlineAssetScraper, self).__init__(scraper_settings, launcher, False, [asset_info], fallbackScraper)
    
    def getName(self):
        return 'Online assets scraper for \'{0}\' ({1})'.format(self.asset_info.name, self.scraper_implementation.name)

    def _get_candidates(self, search_term, romPath, rom):
        log_verb('OnlineAssetScraper._get_candidates(): Scraping {0} with {1}. Searching for matching games ...'.format(self.asset_info.name, self.scraper_implementation.name))
        platform = self.launcher.get_platform()

        # --- Check cache to check if user choose a game previously ---
        log_debug('_get_candidates() Scraper ID          "{0}"'.format(self.scraper_id))
        log_debug('_get_candidates() Scraper obj name    "{0}"'.format(self.scraper_implementation.name))
        log_debug('_get_candidates() search_term          "{0}"'.format(search_term))
        log_debug('_get_candidates() ROM.getBase_noext() "{0}"'.format(romPath.getBase_noext()))
        log_debug('_get_candidates() platform            "{0}"'.format(platform))
        log_debug('_get_candidates() Entries in cache    {0}'.format(len(self.scrap_asset_cached_dic)))

        if self.scraper_id in OnlineAssetScraper.scrap_asset_cached_dic and \
           OnlineAssetScraper.scrap_asset_cached_dic[self.scraper_id]['ROM_base_noext'] == romPath.getBase_noext() and \
           OnlineAssetScraper.scrap_asset_cached_dic[self.scraper_id]['platform'] == platform:
            cached_game = OnlineAssetScraper.scrap_asset_cached_dic[self.scraper_id]['game_dic']
            log_debug('OnlineAssetScraper._get_candidates() Cache HIT. Using cached game "{0}"'.format(cached_game['display_name']))
            return [cached_game]
        
        log_debug('OnlineAssetScraper._get_candidates() Cache MISS. Calling scraper_implementation.get_search()')

        # --- Call scraper and get a list of games ---
        search_results = self.scraper_implementation.get_search(search_term, romPath.getBase_noext(), platform)
        return search_results

    def _loadCandidate(self, candidate, romPath):
        
         # --- Cache selected game from get_search() ---
        OnlineAssetScraper.scrap_asset_cached_dic[self.scraper_id] = {
            'ROM_base_noext' : romPath.getBase_noext(),
            'platform' : self.launcher.get_platform(),
            'game_dic' : candidate
        }

        log_error('_loadCandidate() Caching selected game "{0}"'.format(candidate['display_name']))
        log_error('_loadCandidate() Scraper object ID {0} (name {1})'.format(self.scraper_id, self.scraper_implementation.name))
        
        self.selected_game = OnlineAssetScraper.scrap_asset_cached_dic[self.scraper_id]['game_dic']
        
    def _load_metadata(self, candidate, romPath, rom):
        pass

    def _load_assets(self, candidate, romPath, rom):
        
        asset_file = candidate['file']
        asset_data = self._new_assetdata_dic()
        asset_data['name'] = asset_file.getBase()
        asset_data['url'] = asset_file.getOriginalPath()
        asset_data['is_online'] = False
        asset_data['type'] = self.assets_to_scrape[0]

        self.gamedata['assets'].append(asset_data)

    def _get_image_url_from_page(self, candidate, asset_info):        
        return candidate['url']
