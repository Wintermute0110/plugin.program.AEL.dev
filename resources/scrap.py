# -*- coding: utf-8 -*-

# Advanced Emulator Launcher scraping engine.
#
# --- Information about scraping ---
# https://github.com/muldjord/skyscraper
# https://github.com/muldjord/skyscraper/blob/master/docs/SCRAPINGMODULES.md

# Copyright (c) 2016-2019 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division
import abc
import base64
import collections
import datetime
import json
import time
import urllib
import urlparse
import socket

# --- AEL packages ---
from .constants import *
from .platforms import *
from .utils import *
from .disk_IO import *
from .net_IO import *
from .objects import *
from .rom_audit import *

# --- Scraper use cases ---------------------------------------------------------------------------
# The ScraperFactory class is resposible to create a ScraperStrategy object according to the
# addon settings and to keep a cached dictionary of Scraper objects.
#
# The actual scraping is done by the ScraperStrategy object, which has the logic to download
# images, rename them, etc., and to interact with the scraped object (ROM, Std Launchers).
#
# The Scraper objects only know of to pull information from websites or offline XML databases.
# Scraper objects do not need to reference Launcher or ROM objects. Pass to them the required
# properties like platform. Launcher and ROM objects are know by the ScraperStrategy but not
# by the Scraper objects.
#
# --- NOTES ---
# 1) There is one and only one global ScraperFactory object named g_scraper_factory.
#
# 2) g_scraper_factory keeps a list of instantiated scraper objects. Scrapers are identified
#    with a numerical list index. This is required to identify a concrete scraper object
#    from the addon settings.
#
# 3) g_scraper_factory must be able to report each scraper capabilities.
#
# 4) The actual object metadata/asset scraping is done by an scrap_strategy object instance.
#
# 5) progress_dialog_obj object instance is passed to the scrap_strategy instance.
#    In the ROM scanner the progress dialog is created in the scanner instance and 
#    changed by the scanner/scraper objects.
#
# --- Use case A: ROM scanner ---------------------------------------------------------------------
# The ROM scanner case also applies when the user selects "Rescrape ROM assets" in the Launcher
# context menu.
#
# --- Algorithm ---
# 1) Create a ScraperFactory global object g_scraper_factory.
# 1.1) For each scraper class one and only one object is instantiated and initialised.
#      This per-scraper unique object simplifies the coding of the scraper cache.
#      The unique scraper objects are stored inside the global g_scraper_factory and can
#      be reused.
#
# 2) Create a ScraperStrategy object with the g_scraper_factory object.
# 2.1) g_scraper_factory checks for unset artwork directories. Disable unconfigured assets.
# 2.2) Check for duplicate artwork directories. Disable assets for duplicated directories.
# 2.3) Read the addon settings and create the metadata scraper to process ROMs.
# 2.4) For each asset type not disabled create the asset scraper.
# 2.5) Finally, create and return the ScraperStrategy object.
#
# 3) For each ROM object scrape the metadata and assets with the ScraperStrategy object.
#
# --- Code example ---
# scrap_strategy.process_ROM_assets() scrapes all enabled assets in sequence using all the
# configured scrapers (primary, secondary).
#
# g_scraper_factory = ScraperFactory(g_PATHS, g_settings)
# scrap_strategy = g_scraper_factory.create_scanner(launcher_obj, progress_dialog_obj)
# scrap_strategy.process_ROM_metadata(rom_obj)
# scrap_strategy.process_ROM_assets(rom_obj)
#
# --- Use case B: ROM context menu ---------------------------------------------------------------
# In the ROM context menu the scraper object may be called multiple times by the recursive
# context menu.
#
# Scrapers should report the assets they support to build the dynamic context menu.
#
# The scraping mode when using the context menu is always manual.
#
# --- Code example METADATA ---
# >> g_scraper_factory is a global object created when the addon is initialised.
# g_scrap_factory = ScraperFactory(g_PATHS, self.settings)
# scraper_menu_list = g_scrap_factory.get_metadata_scraper_menu_list()
# scraper_index = dialog.select( ... )
# scraper_ID = g_scrap_factory.get_metadata_scraper_ID_from_menu_idx(scraper_index)
# scrap_strategy = g_scrap_factory.create_CM_metadata(scraper_ID)
# >> data_dic has auxiliar data to do the scraping process.
# scrap_strategy.scrap_CM_metadata_ROM(object_dic, data_dic)
# scrap_strategy.scrap_CM_metadata_Launcher(object_dic, data_dic)
#
# --- Code example ASSETS ---
# >> g_scraper_factory is a global object created when the addon is initialised.
# g_scrap_factory = ScraperFactory(g_PATHS, self.settings)
# scraper_menu_list = g_scrap_factory.get_asset_scraper_menu_list(asset_ID)
# scraper_index = dialog.select( ... )
# scraper_ID = g_scrap_factory.get_asset_scraper_ID_from_menu_idx(scraper_index)
# scrap_strategy = g_scrap_factory.create_CM_asset(scraper_ID)
# >> data_dic has auxiliar data to do the scraping process.
# scrap_strategy.scrap_CM_asset(object_dic, asset_ID, data_dic)
#
# --- Use case C: Standalone Launcher context menu -----------------------------------------------
# In the Standalone Launcher context menu the situation is similar to the ROM context menu.
# The difference is that rom_obj is a Launcher object instance instead of a ROM object.
# ------------------------------------------------------------------------------------------------
class ScraperFactory(object):
    def __init__(self, PATHS, settings):
        # log_debug('ScraperFactory::__init__() BEGIN ...')
        self.PATHS = PATHS
        self.settings = settings

        # Instantiate the scraper objects and cache them in a dictionary. Each scraper is a
        # unique object instance which is reused as many times as necessary. For example,
        # the cached search hits and asset hits will be reused and less web calls need
        # to be performed.
        #
        # Keep instantiated scrapers in an OrderedDictionary.
        # The order is necessary when checking the scraper capabilities and building menus for
        # the scrapers to show always in the same order.
        log_debug('ScraperFactory::__init__() Creating scraper objects...')
        self.scraper_objs = collections.OrderedDict()
        if SCRAPER_NULL_ID in SCRAPER_LIST:
            self.scraper_objs[SCRAPER_NULL_ID] = Null_Scraper(self.settings)
        if SCRAPER_AEL_OFFLINE_ID in SCRAPER_LIST:
            self.scraper_objs[SCRAPER_AEL_OFFLINE_ID] = AEL_Offline(self.settings)
        if SCRAPER_THEGAMESDB_ID in SCRAPER_LIST:
            self.scraper_objs[SCRAPER_THEGAMESDB_ID] = TheGamesDB(self.settings)
        if SCRAPER_MOBYGAMES_ID in SCRAPER_LIST:
            self.scraper_objs[SCRAPER_MOBYGAMES_ID] = MobyGames(self.settings)
        if SCRAPER_SCREENSCRAPER_ID in SCRAPER_LIST:
           self.scraper_objs[SCRAPER_SCREENSCRAPER_ID] = ScreenScraper_V1(self.settings)
        if SCRAPER_GAMEFAQS_ID in SCRAPER_LIST:
            self.scraper_objs[SCRAPER_GAMEFAQS_ID] = GameFAQs(self.settings)
        if SCRAPER_ARCADEDB_ID in SCRAPER_LIST:
            self.scraper_objs[SCRAPER_ARCADEDB_ID] = ArcadeDB(self.settings)
        if SCRAPER_LIBRETRO_ID in SCRAPER_LIST:
           self.scraper_objs[SCRAPER_LIBRETRO_ID] = Libretro(self.settings)

    # Return a list with instantiated scrapers IDs. List always has same order.
    def get_scraper_list(self):
        return list(self.scraper_objs.keys())

    # Returns a scraper object reference.
    def get_scraper_object(self, scraper_ID):
        return self.scraper_objs[scraper_ID]

    def get_name(self, scraper_ID):
        return self.scraper_objs[scraper_ID].get_name()

    def supports_metadata(self, scraper_ID, metadata_ID):
        return self.scraper_objs[scraper_ID].supports_metadata_ID(metadata_ID)

    def supports_asset(self, scraper_ID, asset_ID):
        return self.scraper_objs[scraper_ID].supports_asset_ID(asset_ID)

    def get_metadata_scraper_menu_list(self):
        log_debug('ScraperFactory::get_metadata_scraper_menu_list() Building scraper list...')
        scraper_menu_list = []
        self.metadata_menu_ID_list = []
        for scraper_ID in self.scraper_objs:
            scraper_obj = self.scraper_objs[scraper_ID]
            s_name = scraper_obj.get_name()
            if scraper_obj.supports_metadata():
                scraper_menu_list.append('Scrape with {0}'.format(s_name))
                self.metadata_menu_ID_list.append(scraper_ID)
                log_verb('Scraper {0} supports metadata (ENABLED)'.format(s_name))
            else:
                log_verb('Scraper {0} lacks metadata (DISABLED)'.format(s_name))

        return scraper_menu_list

    def get_metadata_scraper_ID_from_menu_idx(self, menu_index):
        return self.metadata_menu_ID_list[menu_index]

    # Traverses all instantiated scraper objects and checks if the scraper supports the particular
    # kind of asset. If so, it adds the scraper name to the list.
    #
    # @return: [list of strings]
    def get_asset_scraper_menu_list(self, asset_ID):
        log_debug('ScraperFactory::get_asset_scraper_menu_list() Building scraper list...')
        AInfo = g_assetFactory.get_asset_info(asset_ID)
        scraper_menu_list = []
        self.asset_menu_ID_list = []
        for scraper_ID in self.scraper_objs:
            scraper_obj = self.scraper_objs[scraper_ID]
            s_name = scraper_obj.get_name()
            if scraper_obj.supports_asset_ID(asset_ID):
                scraper_menu_list.append('Scrape {0} with {1}'.format(AInfo.name, s_name))
                self.asset_menu_ID_list.append(scraper_ID)
                log_verb('Scraper {0} supports asset {1} (ENABLED)'.format(s_name, AInfo.name))
            else:
                log_verb('Scraper {0} lacks asset {1} (DISABLED)'.format(s_name, AInfo.name))

        return scraper_menu_list

    # You must call get_asset_scraper_menu_list before calling this function.
    def get_asset_scraper_ID_from_menu_idx(self, menu_index):
        return self.asset_menu_ID_list[menu_index]

    # 1) Create the ScraperStrategy object to be used in the ROM Scanner.
    #
    # 2) Read the addon settings and choose the metadata and asset scrapers selected
    #    by the user. Note that the scrapers used depend on the scraping policies.
    #
    # In AEL 0.9.x series launcher is a dictionary. In 0.10.x series it will be a Launcher object.
    #
    # Returns a ScrapeStrategy object which is used for the actual scraping.
    def create_scanner(self, launcher):
        # log_debug('ScraperFactory::create_scanner() BEGIN ...')
        strategy_obj = ScrapeStrategy(self.PATHS, self.settings)

        platform = launcher.get_platform()
        # --- Read addon settings and configure the scrapers selected -----------------------------
        if platform == 'MAME':
            log_debug('ScraperFactory::create_scanner() Platform is MAME.')
            log_debug('Using MAME scrapers from settings.xml')
            scraper_metadata_index = self.settings['scraper_metadata_MAME']
            scraper_asset_index = self.settings['scraper_asset_MAME']
            scraper_metadata_ID = SCRAP_METADATA_MAME_SETTINGS_LIST[scraper_metadata_index]
            scraper_asset_ID = SCRAP_ASSET_MAME_SETTINGS_LIST[scraper_asset_index]
        else:
            log_debug('ScraperFactory::create_scanner() Platform is NON-MAME.')
            log_debug('Using standard scrapers from settings.xml')
            scraper_metadata_index = self.settings['scraper_metadata']
            scraper_asset_index = self.settings['scraper_asset']
            scraper_metadata_ID = SCRAP_METADATA_SETTINGS_LIST[scraper_metadata_index]
            scraper_asset_ID = SCRAP_ASSET_SETTINGS_LIST[scraper_asset_index]
        log_debug('scraper metadata name {} (index {}, ID {})'.format(
            self.scraper_objs[scraper_metadata_ID].get_name(), scraper_metadata_index, scraper_metadata_ID))
        log_debug('scraper asset name    {} (index {}, ID {})'.format(
            self.scraper_objs[scraper_asset_ID].get_name(), scraper_asset_index, scraper_asset_ID))

        # For now the ScraperStrategy object will use the first scraper of this list. In the
        # future maybe multiple scrapers can be used and these lists will have more than one
        # object.
        strategy_obj.metadata_scraper_list = [ self.scraper_objs[scraper_metadata_ID] ]
        strategy_obj.asset_scraper_list = [ self.scraper_objs[scraper_asset_ID] ]

        # --- Add launcher properties to ScrapeStrategy object ---
        strategy_obj.platform = platform

        return strategy_obj

    # 1) Create a ScraperStrategy object to be used in the "Edit metadata" context menu.
    def create_CM_metadata(self, scraper_ID):
        log_debug('ScraperFactory::create_CM_metadata() BEGIN ...')
        strategy_obj = ScrapeStrategy(self.PATHS, self.settings)

        # --- Choose scraper ---
        strategy_obj.scraper_obj = self.scraper_objs[scraper_ID]
        log_debug('User chose scraper "{0}"'.format(strategy_obj.scraper_obj.get_name()))

        return strategy_obj

    # 1) Create a ScraperStrategy object to be used in the "Edit asset" context menu.
    #
    # Returns a ScrapeStrategy object which is used for the actual scraping.
    # In AEL 0.9.x this object will be used once. In AEL 0.10.x with recursive CM this object
    # may be used multiple times. Make sure cache works OK.
    def create_CM_asset(self, scraper_ID):
        log_debug('ScraperFactory::create_CM_asset() BEGIN ...')
        strategy_obj = ScrapeStrategy(self.PATHS, self.settings)

        # --- Choose scraper ---
        strategy_obj.scraper_obj = self.scraper_objs[scraper_ID]
        log_debug('User chose scraper "{0}"'.format(strategy_obj.scraper_obj.get_name()))

        return strategy_obj

SCRAPE_ROM      = 'ROM'
SCRAPE_LAUNCHER = 'Launcher'

#
# Main scraping logic.
#
class ScrapeStrategy(object):
    # --- Class variables ------------------------------------------------------------------------
    # --- Metadata actions ---
    ACTION_META_TITLE_ONLY = 100
    ACTION_META_NFO_FILE   = 200
    ACTION_META_SCRAPER    = 300

    # --- Asset actions ---
    ACTION_ASSET_LOCAL_ASSET = 100
    ACTION_ASSET_SCRAPER     = 200

    # --- Constructor ----------------------------------------------------------------------------
    # @param PATHS: PATH object.
    # @param settings: [dict] Addon settings.
    # @param launcher: [dict] Launcher dictionary.
    # @param pdialog: [KodiProgressDialog] object instance.
    # @param pdialog_verbose: [bool] verbose progress dialog.
    def __init__(self, PATHS, settings):
        log_debug('ScrapeStrategy::__init__() Initializing ScrapeStrategy...')
        self.PATHS = PATHS
        self.settings = settings

        # --- Read addon settings and configure scraper setings ---
        self.scan_metadata_policy = self.settings['scan_metadata_policy']
        self.scan_asset_policy    = self.settings['scan_asset_policy']
        self.game_selection_mode  = self.settings['game_selection_mode']
        self.asset_selection_mode = self.settings['asset_selection_mode']

        # Boolean options used by the scanner.
        self.scan_ignore_scrap_title = self.settings['scan_ignore_scrap_title']
        self.scan_clean_tags         = self.settings['scan_clean_tags']
        self.scan_update_NFO_files   = self.settings['scan_update_NFO_files']

    # Call this function before the scanner starts.
    def begin_ROM_scanner(self, launcher, pdialog, pdialog_verbose):
        log_debug('ScrapeStrategy::begin_ROM_scanner() Initialising ROM Scanner engine...')
        self.launcher = launcher
        self.platform = launcher.get_platform()
        self.pdialog = pdialog
        self.pdialog_verbose = pdialog_verbose

        # --- Metadata scraper ---
        # For now just use the first scraper
        self.meta_scraper_obj = self.metadata_scraper_list[0]
        self.meta_scraper_name = self.meta_scraper_obj.get_name()
        # log_debug('Using metadata scraper "{0}"'.format(self.meta_scraper_name))

        # --- Asset scraper ---
        self.asset_scraper_obj = self.asset_scraper_list[0]
        self.asset_scraper_name = self.asset_scraper_obj.get_name()
        # log_debug('Using asset scraper "{0}"'.format(self.asset_scraper_name))

        # This will be used later
        self.flag_meta_and_asset_scraper_same = self.meta_scraper_obj is self.asset_scraper_obj
        log_debug('Are metadata and asset scrapers the same? {}'.format(self.flag_meta_and_asset_scraper_same))

    def check_launcher_unset_asset_dirs(self):
        log_debug('ScrapeStrategy::check_launcher_unset_asset_dirs() BEGIN ...')
        self.enabled_asset_list = self.launcher.get_enabled_asset_list()
        self.unconfigured_name_list = asset_get_unconfigured_name_list(self.enabled_asset_list)
 
    # Determine the actions to be carried out by process_ROM_metadata() and process_ROM_assets().
    # Must be called before the aforementioned methods.
    def process_ROM_begin(self, ROM):
        log_debug('ScrapeStrategy::process_ROM_begin() Determining metadata and asset actions...')
        # --- Determine metadata action ----------------------------------------------------------
        # --- Test if NFO file exists ---
        ROM_path = ROM.get_file()
        NFO_file = FileName(ROM_path.getPathNoExt() + '.nfo')
        NFO_file_found = True if NFO_file.exists() else False
        if NFO_file_found:
            log_debug('NFO file found "{0}"'.format(NFO_file.getPath()))
        else:
            log_debug('NFO file NOT found "{0}"'.format(NFO_file.getPath()))

        # Action depends configured metadata policy and wheter the NFO files was found or not.
        if self.scan_metadata_policy == 0:
            log_verb('Metadata policy: Read NFO file OFF | Scraper OFF')
            log_verb('Metadata policy: Only cleaning ROM name.')
            self.metadata_action = ScrapeStrategy.ACTION_META_TITLE_ONLY

        elif self.scan_metadata_policy == 1:
            log_verb('Metadata policy: Read NFO file ON | Scraper OFF')
            if NFO_file_found:
                log_verb('Metadata policy: NFO file found.')
                self.metadata_action = ScrapeStrategy.ACTION_META_NFO_FILE
            else:
                log_verb('Metadata policy: NFO file not found. Only cleaning ROM name')
                self.metadata_action = ScrapeStrategy.ACTION_META_TITLE_ONLY

        elif self.scan_metadata_policy == 2:
            log_verb('Metadata policy: Read NFO file ON | Scraper ON')
            if NFO_file_found:
                log_verb('Metadata policy: NFO file found. Scraper not used.')
                self.metadata_action = ScrapeStrategy.ACTION_META_NFO_FILE
            else:
                log_verb('Metadata policy: NFO file not found. Using scraper.')
                self.metadata_action = ScrapeStrategy.ACTION_META_SCRAPER

        elif self.scan_metadata_policy == 3:
            log_verb('Metadata policy: Read NFO file OFF | Scraper ON')
            log_verb('Metadata policy: Using metadata scraper {}'.format(self.meta_scraper_name))
            self.metadata_action = ScrapeStrategy.ACTION_META_SCRAPER

        else:
            raise ValueError('Invalid scan_metadata_policy value {0}'.format(self.scan_metadata_policy))

        # --- Determine Asset action -------------------------------------------------------------
        # --- Search for local artwork/assets ---
        # Always look for local assets whatever the scanner settings. For unconfigured assets
        # local_asset_list will have the default database value empty string ''.
        self.local_asset_list = assets_search_local_cached_assets(self.launcher, ROM, self.enabled_asset_list)
        self.asset_action_list = [ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET] * len(ROM_ASSET_ID_LIST)
        # Print information to the log
        if self.scan_asset_policy == 0:
            log_error('Asset policy: Local images ON | Scraper OFF')
        elif self.scan_asset_policy == 1:
            log_error('Asset policy: Local images ON | Scraper ON')
        elif self.scan_asset_policy == 2:
            log_error('Asset policy: Local images OFF | Scraper ON')
        else:
            raise ValueError('Invalid scan_asset_policy value {0}'.format(self.scan_asset_policy))
        # Process asset by asset
        for i, asset_ID in enumerate(ROM_ASSET_ID_LIST):
            AInfo = g_assetFactory.get_asset_info(asset_ID)
            if self.scan_asset_policy == 0:
                if not self.enabled_asset_list[i]:
                    log_error('Skipping {0} (dir not configured).'.format(AInfo.name))
                elif self.local_asset_list[i]:
                    log_error('Local {0} FOUND'.format(AInfo.name))
                else:
                    log_error('Local {0} NOT found.'.format(AInfo.name))
                self.asset_action_list[i] = ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET
            elif self.scan_asset_policy == 1:
                if not self.enabled_asset_list[i]:
                    log_error('Skipping {0} (dir not configured).'.format(AInfo.name))
                    self.asset_action_list[i] = ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET
                elif self.local_asset_list[i]:
                    log_error('Local {0} FOUND'.format(AInfo.name))
                    self.asset_action_list[i] = ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET
                else:
                    log_error('Local {0} NOT found. Scraping.'.format(AInfo.name))
                    self.asset_action_list[i] = ScrapeStrategy.ACTION_ASSET_SCRAPER
            elif self.scan_asset_policy == 2:
                if not self.enabled_asset_list[i]:
                    log_error('Skipping {0} (dir not configured).'.format(AInfo.name))
                    self.asset_action_list[i] = ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET
                # Scraper does not support asset but local asset found.
                elif not self.asset_scraper_obj.supports_asset_ID(asset_ID) and self.local_asset_list[i]:
                    log_error('Scraper {} does not support {}. Using local asset.'.format(
                        self.asset_scraper_name, AInfo.name))
                    self.asset_action_list[i] = ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET
                # Scraper does not support asset and local asset not found.
                elif not self.asset_scraper_obj.supports_asset_ID(asset_ID) and not self.local_asset_list[i]:
                    log_error('Scraper {} does not support {}. Local asset not found.'.format(
                        self.asset_scraper_name, AInfo.name))
                    self.asset_action_list[i] = ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET
                # Scraper supports asset. Scrape wheter local asset is found or not.
                elif self.asset_scraper_obj.supports_asset_ID(asset_ID):
                    log_error('Scraping {} with {}.'.format(AInfo.name, self.asset_scraper_name))
                    self.asset_action_list[i] = ScrapeStrategy.ACTION_ASSET_SCRAPER
                else:
                    raise ValueError('Logical error')

        # --- If metadata or any asset is scraped then select the game among the candidates ---
        # Note that the metadata and asset scrapers may be different. If so, candidates
        # must be selected for both scrapers.
        status_dic = kodi_new_status_dic('No error')
        if self.metadata_action == ScrapeStrategy.ACTION_META_SCRAPER:
            log_debug('Getting metadata candidate game')
            self.candidate_metadata = self._scanner_get_candidate(
                ROM, self.meta_scraper_obj, self.meta_scraper_name, status_dic)
        else:
            self.candidate_metadata = None

        temp_asset_list = [x == ScrapeStrategy.ACTION_ASSET_SCRAPER for x in self.asset_action_list]
        if any(temp_asset_list) and self.flag_meta_and_asset_scraper_same:
            log_debug('Asset candidate game same as metadata candidate.')
            self.candidate_asset = self.candidate_metadata
        elif any(temp_asset_list) and not self.flag_meta_and_asset_scraper_same:
            log_debug('Getting asset candidate game.')
            self.candidate_asset = self._scanner_get_candidate(
                ROM, self.asset_scraper_obj, self.asset_scraper_name, status_dic)
        else:
            self.candidate_asset = None

    # Called by the ROM scanner. Fills in the ROM metadata.
    #
    # @param ROM: [Rom] ROM object.
    def process_ROM_metadata(self, ROM):
        log_debug('ScrapeStrategy::process_ROM_metadata() Processing metadata action...')
        
        if self.metadata_action == ScrapeStrategy.ACTION_META_TITLE_ONLY:
            if self.pdialog_verbose:
                self.pdialog.updateMessage2('Formatting ROM name...')
            ROM_path = ROM.get_file()
            ROM.set_name(text_format_ROM_title(ROM_path.getBaseNoExt(), self.scan_clean_tags))

        elif self.metadata_action == ScrapeStrategy.ACTION_META_NFO_FILE:
            ROM_path = ROM.get_file()
            NFO_file = FileName(ROM_path.getPathNoExt() + '.nfo')
        
            if self.pdialog_verbose:
                self.pdialog.updateMessage2('Loading NFO file {0}'.format(NFO_file.getPath()))
            # If this point is reached the NFO file was found previosly.
            log_debug('Loading NFO P "{0}"'.format(NFO_file.getPath()))
            nfo_dic = fs_import_ROM_NFO_file_scanner(NFO_file)
            # NOTE <platform> is chosen by AEL, never read from NFO files. Indeed, platform
            #      is a Launcher property, not a ROM property.
            ROM.set_name(nfo_dic['title'])                  # <title>
            ROM.set_releaseyear(nfo_dic['year'])            # <year>
            ROM.set_genre(nfo_dic['genre'])                 # <genre>
            ROM.set_developer(nfo_dic['developer'])         # <developer>
            ROM.set_number_of_players(nfo_dic['nplayers'])  # <nplayers>
            ROM.set_esrb_rating(nfo_dic['esrb'])            # <esrb>
            ROM.set_rating(nfo_dic['rating'])               # <rating>
            ROM.set_plot(nfo_dic['plot'])                   # <plot>

        elif self.metadata_action == ScrapeStrategy.ACTION_META_SCRAPER:
            self._scanner_scrap_ROM_metadata(ROM)
            
        else:
            raise ValueError('Invalid metadata_action value {0}'.format(self.metadata_action))
    
    # Called by the ROM scanner.
    #
    # @param ROM: [Rom] ROM filename object.
    def process_ROM_assets(self, ROM):
        log_debug('ScrapeStrategy::process_ROM_assets() Processing asset actions...')
        
        # --- Process asset by asset actions ---
        # --- Asset scraping ---
        for i, asset_ID in enumerate(ROM_ASSET_ID_LIST):
            AInfo = g_assetFactory.get_asset_info(asset_ID)
            if self.asset_action_list[i] == ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET:
                log_debug('Using local asset for {}'.format(AInfo.name))
                ROM.set_asset(AInfo, self.local_asset_list[i])
            elif self.asset_action_list[i] == ScrapeStrategy.ACTION_ASSET_SCRAPER:                
                ROM.set_asset(AInfo, self._scanner_scrap_ROM_asset(
                    AInfo, self.local_asset_list[i], ROM))
            else:
                raise ValueError('Asset {} index {} ID {} unknown action {}'.format(
                    AInfo.name, i, asset_ID, self.asset_action_list[i]))

        # --- Print some debug info ---
        romdata = ROM.get_data_dic()
        log_verb('Set Title     file "{0}"'.format(romdata['s_title']))
        log_verb('Set Snap      file "{0}"'.format(romdata['s_snap']))
        log_verb('Set Boxfront  file "{0}"'.format(romdata['s_boxfront']))
        log_verb('Set Boxback   file "{0}"'.format(romdata['s_boxback']))
        log_verb('Set Cartridge file "{0}"'.format(romdata['s_cartridge']))
        log_verb('Set Fanart    file "{0}"'.format(romdata['s_fanart']))
        log_verb('Set Banner    file "{0}"'.format(romdata['s_banner']))
        log_verb('Set Clearlogo file "{0}"'.format(romdata['s_clearlogo']))
        log_verb('Set Flyer     file "{0}"'.format(romdata['s_flyer']))
        log_verb('Set Map       file "{0}"'.format(romdata['s_map']))
        log_verb('Set Manual    file "{0}"'.format(romdata['s_manual']))
        log_verb('Set Trailer   file "{0}"'.format(romdata['s_trailer']))

        return ROM

    # Get a candidate game in the ROM scanner.
    def _scanner_get_candidate(self, ROM, scraper_obj, scraper_name, status_dic):
        # --- Update scanner progress dialog ---
        if self.pdialog_verbose:
            scraper_text = 'Searching games with scraper {}...'.format(scraper_name)
            self.pdialog.updateMessage2(scraper_text)
        log_debug('Searching games with scraper {}'.format(scraper_name))
        
        # --- Call scraper and get a list of games ---
        ROM_path = ROM.get_file()
        rom_name_scraping = text_format_ROM_name_for_scraping(ROM_path.getBaseNoExt())
        candidates = scraper_obj.get_candidates(
            rom_name_scraping, ROM_path.getBaseNoExt(), self.platform, status_dic)
        # * If the scraper produced an error notification show it and continue operation.
        #   Note that if a number of errors/exceptions happen (for example, network is down) then
        #   the scraper will disable itself and only a limited number of messages will be shown.
        # * In the scanner treat any scraper error message as an OK dialog.
        # * Once the error is displayed reset status_dic
        if not status_dic['status']:
            self.pdialog.close()
            kodi_dialog_OK(status_dic['msg'])
            status_dic = kodi_new_status_dic('No error')
            self.pdialog.reopen()
        if candidates is None or not candidates:
            log_verb('Found no candidates after searching.')
            return None
        log_debug('Scraper {0} found {1} candidate/s'.format(scraper_name, len(candidates)))
        # --- Choose game to download metadata ---
        if self.game_selection_mode == 0:
            log_debug('Metadata manual scraping')
            if len(candidates) == 1:
                log_debug('get_candidates() returned 1 game. Automatically selected.')
                select_candidate_idx = 0
            else:
                # Display game list found so user choses.
                log_debug('Metadata manual scraping. User chooses game.')
                self.pdialog.close()
                game_name_list = [candidate['display_name'] for candidate in candidates]
                select_candidate_idx = xbmcgui.Dialog().select(
                    'Select game for ROM {0}'.format(ROM_path.getBaseNoExt()), game_name_list)
                if select_candidate_idx < 0: select_candidate_idx = 0
                self.pdialog.reopen()
        elif self.game_selection_mode == 1:
            log_debug('Metadata automatic scraping. Selecting first result.')
            select_candidate_idx = 0
        else:
            raise ValueError('Invalid game_selection_mode {0}'.format(self.game_selection_mode))
        candidate = candidates[select_candidate_idx]

        return candidate

    # Scraps ROM metadata in the ROM scanner.
    def _scanner_scrap_ROM_metadata(self, ROM):
        log_debug('ScrapeStrategy::_scanner_scrap_ROM_metadata() Scraping metadata...')

        # --- Update scanner progress dialog ---
        if self.pdialog_verbose:
            scraper_text = 'Scraping metadata with {}...'.format(self.meta_scraper_name)
            self.pdialog.updateMessage2(scraper_text)

        # --- If no candidates available just clean the ROM Title and return ---
        if self.candidate_metadata is None and not self.candidate_metadata:
            log_verb('No medatada candidates (or previous error). Cleaning ROM name only.')
            ROM_file = ROM.get_file()
            ROM.set_name(text_format_ROM_title(ROM_file.getBaseNoExt(), self.scan_clean_tags))
            return

        # --- Grab metadata for selected game and put into ROM ---
        status_dic = kodi_new_status_dic('No error')
        game_data = self.meta_scraper_obj.get_metadata(self.candidate_metadata, status_dic)
        if not status_dic['status']:
            self.pdialog.close()
            kodi_dialog_OK(status_dic['msg'])
            self.pdialog.reopen()
            return
        scraper_applied = self._apply_candidate_on_metadata(game_data, ROM)

        # --- Update ROM NFO file after scraping ---
        if self.scan_update_NFO_files:
            log_debug('User wants to update NFO file after scraping.')
            fs_export_ROM_NFO(ROM.get_data_dic(), False)
        else:
            log_debug('User wants to NOT update NFO file after scraping. Doing nothing.')

    #
    # Returns a valid filename of the downloaded scrapped image, filename of local image
    # or empty string if scraper finds nothing or download failed.
    #
    # @param asset_info [AssetInfo object]
    # @param local_asset_path: [str]
    # @param ROM: [Rom object]
    # @return: [str] Filename string with the asset path.
    def _scanner_scrap_ROM_asset(self, asset_info, local_asset_path, ROM):
        # --- Cached frequent used things ---
        asset_name = asset_info.name
        asset_dir_FN  = self.launcher.get_asset_path(asset_info)
        asset_path_noext_FN = assets_get_path_noext_DIR(asset_info, asset_dir_FN, ROM.get_file())
        log_debug('ScrapeStrategy::_scanner_scrap_ROM_asset() Scraping {} with scraper {}...'.format(
            asset_name, self.asset_scraper_name))
        status_dic = kodi_new_status_dic('No error')
        
        # By default always use local image if found in case scraper fails.
        ret_asset_path = local_asset_path
        candidate = self.candidate_asset
        log_debug('local_asset_path "{}"'.format(local_asset_path))
        log_debug('asset_path_noext "{}"'.format(asset_path_noext_FN.getPath()))

        # --- If no candidates available just clean the ROM Title and return ---
        if self.candidate_asset is None or not self.candidate_asset:
            log_verb('No asset candidates (or previous error).')
            return ret_asset_path

        # --- If scraper does not support particular asset return inmediately ---
        if not self.asset_scraper_obj.supports_asset_ID(asset_info.id):
            log_debug('Scraper {0} does not support asset {1}.'.format(
                self.asset_scraper_name, asset_name))
            return ret_asset_path

        # --- Update scanner progress dialog ---
        if self.pdialog_verbose:
            scraper_text = 'Getting {0} images with {1}...'.format(
                asset_name, self.asset_scraper_name)
            self.pdialog.updateMessage2(scraper_text)

        # --- Grab list of images/assets for the selected candidate ---
        assetdata_list = self.asset_scraper_obj.get_assets(candidate, asset_info, status_dic)
        if not status_dic['status']:
            self.pdialog.close()
            kodi_dialog_OK(status_dic['msg'])
            status_dic = kodi_new_status_dic('No error')
            self.pdialog.reopen()
        if assetdata_list is None or not assetdata_list:
            # If scraper returns no images return current local asset.
            log_debug('{0} {1} found no images.'.format(self.asset_scraper_name, asset_name))
            return ret_asset_path
        log_verb('{0} scraper returned {1} images.'.format(asset_name, len(assetdata_list)))

        # --- Semi-automatic scraping (user choses an image from a list) ---
        if self.asset_selection_mode == 0:
            # If there is a local image add it to the list and show it to the user
            local_asset_in_list_flag = False
            if local_asset_path:
                local_asset = {
                    'asset_ID'     : asset_info.id,
                    'display_name' : 'Current local image',
                    'url_thumb'    : local_asset_path,
                }
                assetdata_list.insert(0, local_asset)
                local_asset_in_list_flag = True

            # Convert list returned by scraper into a list the select window uses.
            ListItem_list = []
            for item in assetdata_list:
                listitem_obj = xbmcgui.ListItem(label = item['display_name'], label2 = item['url_thumb'])
                listitem_obj.setArt({'icon' : item['url_thumb']})
                ListItem_list.append(listitem_obj)
            # ListItem_list has 1 or more elements at this point.
            # If assetdata_list has only 1 element do not show select dialog. Note that the
            # length of assetdata_list is 1 only if scraper returned 1 image and a local image
            # does not exist. If the scraper returned no images this point is never reached.
            if len(ListItem_list) == 1:
                image_selected_index = 0
            else:
                self.pdialog.close()
                image_selected_index = xbmcgui.Dialog().select(
                    'Select {0} image'.format(asset_name), list = ListItem_list, useDetails = True)
                log_debug('{0} dialog returned index {1}'.format(asset_name, image_selected_index))
                if image_selected_index < 0: image_selected_index = 0
                self.pdialog.reopen()
            # User chose to keep current asset.
            if local_asset_in_list_flag and image_selected_index == 0:
                log_debug('User chose local asset. Returning.')
                return ret_asset_path
        # --- Automatic scraping. Pick first image. ---
        elif self.asset_selection_mode == 1:
            image_selected_index = 0
        else:
            raise AddonError('Invalid asset_selection_mode {0}'.format(self.asset_selection_mode))

        # --- Download scraped image --------------------------------------------------------------
        selected_asset = assetdata_list[image_selected_index]

        # --- Resolve asset URL ---
        log_debug('Resolving asset URL...')
        if self.pdialog_verbose:
            scraper_text = 'Scraping {0} with {1} (Resolving URL...)'.format(
                asset_name, self.asset_scraper_name)
            self.pdialog.updateMessage2(scraper_text)
        image_url = self.asset_scraper_obj.resolve_asset_URL(selected_asset, status_dic)
        if not status_dic['status']:
            self.pdialog.close()
            kodi_dialog_OK(status_dic['msg'])
            status_dic = kodi_new_status_dic('No error')
            self.pdialog.reopen()
        if image_url is None or not image_url:
            log_debug('Error resolving URL')
            return ret_asset_path
        log_debug('Resolved {0} to URL "{1}"'.format(asset_name, image_url))

        # --- Resolve URL extension ---
        log_debug('Resolving asset URL extension...')
        image_ext = self.asset_scraper_obj.resolve_asset_URL_extension(image_url, status_dic)
        if not status_dic['status']:
            self.pdialog.close()
            kodi_dialog_OK(status_dic['msg'])
            status_dic = kodi_new_status_dic('No error')
            self.pdialog.reopen()
        if image_ext is None or not image_ext:
            log_debug('Error resolving URL')
            return ret_asset_path
        log_debug('Resolved URL extension "{0}"'.format(image_ext))

        # --- Download image ---
        if self.pdialog_verbose:
            scraper_text = 'Downloading {} from {}...'.format(
                asset_name, self.asset_scraper_name)
            self.pdialog.updateMessage2(scraper_text)
        image_local_path = asset_path_noext_FN.append('.' + image_ext)
        log_verb('Downloading URL  "{0}"'.format(image_url))
        log_verb('Into local file  "{0}"'.format(image_local_path))
        try:
            net_download_img(image_url, image_local_path)
        except socket.timeout:
            self.pdialog.close()
            kodi_dialog_OK('Cannot download {0} image (Timeout)'.format(asset_name))
            self.pdialog.reopen()

        # --- Update Kodi cache with downloaded image ---
        # Recache only if local image is in the Kodi cache, this function takes care of that.
        # kodi_update_image_cache(image_path)

        # --- Return value is downloaded image ---
        return image_local_path
    
    # This function to be used in AEL 0.9.x series.
    #
    # @param gamedata: Dictionary with game data.
    # @param romdata: ROM/Launcher data dictionary.
    # @return: True if metadata is valid an applied, False otherwise.
    def _apply_candidate_on_metadata_old(self, gamedata, romdata, ROM):
        if not gamedata: return False

        # --- Put metadata into ROM/Launcher dictionary ---
        if self.scan_ignore_scrap_title:
            romdata['m_name'] = text_format_ROM_title(ROM.getBaseNoExt(), self.scan_clean_tags)
            log_debug('User wants to ignore scraped name and use filename.')
        else:
            romdata['m_name'] = gamedata['title']
            log_debug('User wants scrapped name and not filename.')
        log_debug('Setting ROM name to "{0}"'.format(romdata['m_name']))
        romdata['m_year']      = gamedata['year']
        romdata['m_genre']     = gamedata['genre']
        romdata['m_developer'] = gamedata['developer']
        romdata['m_nplayers']  = gamedata['nplayers']
        romdata['m_esrb']      = gamedata['esrb']
        romdata['m_plot']      = gamedata['plot']

        return True

    # This function to be used in AEL 0.10.x series.
    #
    # @param gamedata: Dictionary with game data.
    # @param rom: ROM/Launcher object to apply metadata.
    # @return: True if metadata is valid an applied, False otherwise.
    def _apply_candidate_on_metadata(self, gamedata, rom):
        if not gamedata: return False

        # --- Put metadata into ROM/Launcher object ---
        if self.scan_ignore_scrap_title:
            rom_file = rom.get_file()
            rom_name = text_format_ROM_title(rom_file.getBaseNoExt(), self.scan_clean_tags)
            rom.set_name(rom_name)
            log_debug("User wants to ignore scraper name. Setting name to '{0}'".format(rom_name))
        else:
            rom_name = gamedata['title']
            rom.set_name(rom_name)
            log_debug("User wants scrapped name. Setting name to '{0}'".format(rom_name))

        rom.set_releaseyear(gamedata['year'])           # <year>
        rom.set_genre(gamedata['genre'])                # <genre>
        rom.set_developer(gamedata['developer'])        # <developer>
        rom.set_number_of_players(gamedata['nplayers']) # <nplayers>
        rom.set_esrb_rating(gamedata['esrb'])           # <esrb>
        rom.set_plot(gamedata['plot'])                  # <plot>

        return True
    
    # Called when editing a ROM by _command_edit_rom()
    # Always do MANUAL scraping mode when editing ROMs/Launchers.
    # In the future object_dic will be a Launcher/ROM object, not a dictionary.
    # TODO Merge scrap_CM_metadata_ROM() and scrap_CM_metadata_launcher() into a generic function.
    #
    # @return: [dic] kodi_new_status_dic() status dictionary.
    def scrap_CM_metadata_ROM(self, object_dic, data_dic):
        log_debug('ScrapeStrategy::scrap_CM_metadata_ROM() BEGIN ...')
        # In AEL 0.10.x this data is grabed from the objects, not passed using a dictionary.
        rom_base_noext = data_dic['rom_base_noext']
        status_dic = kodi_new_status_dic('ROM metadata updated')
        scraper_name = self.scraper_obj.get_name()

        # --- Check if scraper is OK (API keys configured, etc.) ---
        self.scraper_obj.check_before_scraping(status_dic)
        if not status_dic['status']: return status_dic

        # --- Grab candidate game ---
        candidate = self._scrap_CM_get_candidate(SCRAPE_ROM, object_dic, data_dic, status_dic)
        if not status_dic['status']: return status_dic

        # --- Grab metadata ---
        pdialog = KodiProgressDialog()
        pdialog.startProgress('{0} scraper. Getting ROM metadata...'.format(scraper_name))
        gamedata = self.scraper_obj.get_metadata(candidate, status_dic)
        pdialog.endProgress()
        if not status_dic['status']: return status_dic

        # --- Put metadata into ROM dictionary ---
        if self.scan_ignore_scrap_title:
            log_debug('User wants to ignore scraper name.')
            object_dic['m_name'] = text_format_ROM_title(rom_base_noext, self.scan_clean_tags)
        else:
            log_debug('User wants scrapped name.')
            object_dic['m_name'] = gamedata['title']
        log_debug('Setting ROM title to "{0}"'.format(object_dic['m_name']))
        object_dic['m_year']      = gamedata['year']
        object_dic['m_genre']     = gamedata['genre']
        object_dic['m_developer'] = gamedata['developer']
        object_dic['m_nplayers']  = gamedata['nplayers']
        object_dic['m_esrb']      = gamedata['esrb']
        object_dic['m_plot']      = gamedata['plot']

        return status_dic

    # Called when editing a launcher by _command_edit_launcher()
    # Note that launcher maybe a ROM launcher or a Standalone Launcher (game, app)
    #
    # @return: [dic] kodi_new_status_dic() status dictionary.
    def scrap_CM_metadata_Launcher(self, object_dic, data_dic):
        log_debug('ScrapeStrategy::scrap_CM_metadata_Launcher() BEGIN ...')
        status_dic = kodi_new_status_dic('Launcher metadata updated')
        scraper_name = self.scraper_obj.get_name()

        # --- Check if scraper is OK (API keys configured, etc.) ---
        self.scraper_obj.check_before_scraping(status_dic)
        if not status_dic['status']: return status_dic

        # --- Grab candidate game ---
        candidate = self._scrap_CM_get_candidate(SCRAPE_LAUNCHER, object_dic, data_dic, status_dic)
        if not status_dic['status']: return status_dic

        # --- Grab metadata ---
        pdialog = KodiProgressDialog()
        pdialog.startProgress('{0} scraper. Getting Launcher metadata...'.format(scraper_name))
        gamedata = self.scraper_obj.get_metadata(candidate)
        pdialog.endProgress()
        if not status_dic['status']: return status_dic

        # --- Put metadata into launcher dictionary ---
        # Scraper should not change launcher title.
        # 'nplayers' and 'esrb' ignored for launchers
        launcher.set_releaseyear(gamedata['year'])           # <year>
        launcher.set_genre(gamedata['genre'])                # <genre>
        launcher.set_developer(gamedata['developer'])        # <developer>
        launcher.set_plot(gamedata['plot'])                  # <plot>

        return status_dic

    # Called when scraping an asset in the context menu.
    # In the future object_dic will be a Launcher/ROM object, not a dictionary.
    #
    # @return: [dic] kodi_new_status_dic() status dictionary.
    def scrap_CM_asset(self, object_dic, asset_ID, data_dic):
        # log_debug('ScrapeStrategy::scrap_CM_asset() BEGIN...')

        # --- Cached frequent used things ---
        asset_info = g_assetFactory.get_asset_info(asset_ID)
        asset_name = asset_info.name
        # In AEL 0.10.x this data is grabed from the objects, not passed using a dictionary.
        rom_base_noext = data_dic['rom_base_noext']
        platform = data_dic['platform']
        current_asset_FN = data_dic['current_asset_FN']
        asset_path_noext_FN = data_dic['asset_path_noext']
        log_info('ScrapeStrategy::scrap_CM_asset() Scraping {0}...'.format(object_dic['m_name']))
        status_dic = kodi_new_status_dic('Asset updated')
        scraper_name = self.scraper_obj.get_name()

        # --- Check if scraper is OK (API keys configured, etc.) ---
        self.scraper_obj.check_before_scraping(status_dic)
        if not status_dic['status']: return status_dic

        # --- Grab candidate game ---
        candidate = self._scrap_CM_get_candidate(SCRAPE_ROM, object_dic, data_dic, status_dic)
        if not status_dic['status']: return status_dic

        # --- Grab list of images for the selected game -------------------------------------------
        pdialog = KodiProgressDialog()
        pdialog.startProgress('{} scraper (Getting {} assets...)'.format(scraper_name, asset_name))
        assetdata_list = self.scraper_obj.get_assets(candidate, asset_ID, status_dic)
        pdialog.endProgress()
        # Error/exception.
        if not status_dic['status']: return status_dic
        log_verb('{0} {1} scraper returned {2} images'.format(
            scraper_name, asset_name, len(assetdata_list)))
        # Scraper found no assets. Return immediately.
        if not assetdata_list:
            status_dic['status'] = False
            status_dic['dialog'] = KODI_MESSAGE_DIALOG
            status_dic['msg'] = '{0} {1} scraper found no '.format(scraper_name, asset_name) + \
                                'images for game "{0}".'.format(candidate['display_name'])
            return status_dic

        # If there is a local image add it to the list and show it to the user.
        local_asset_in_list_flag = False
        if current_asset_FN.exists():
            local_asset = {
                'asset_ID'     : asset_ID,
                'display_name' : 'Current local image',
                'url_thumb'    : current_asset_FN.getPath(),
            }
            assetdata_list.insert(0, local_asset)
            local_asset_in_list_flag = True

        # Convert list returned by scraper into a list the Kodi select dialog uses.
        ListItem_list = []
        for item in assetdata_list:
            listitem_obj = xbmcgui.ListItem(label = item['display_name'], label2 = item['url_thumb'])
            listitem_obj.setArt({'icon' : item['url_thumb']})
            ListItem_list.append(listitem_obj)
        # ListItem_list has 1 or more elements at this point.
        # If there is only one item in the list do not show select dialog.
        if len(ListItem_list) == 1:
            log_debug('_gui_edit_asset() ListItem_list has one element. Do not show select dialog.')
            image_selected_index = 0
        else:
            image_selected_index = xbmcgui.Dialog().select(
                'Select image', list = ListItem_list, useDetails = True)
            log_debug('{0} dialog returned index {1}'.format(asset_name, image_selected_index))
        # User cancelled dialog
        if image_selected_index < 0:
            log_debug('_gui_edit_asset() User cancelled image select dialog. Returning.')
            status_dic['status'] = False
            status_dic['msg'] = 'Image not changed'
            return status_dic
        # User chose to keep current asset.
        if local_asset_in_list_flag and image_selected_index == 0:
            log_debug('_gui_edit_asset() Selected current image "{0}"'.format(current_asset_FN.getPath()))
            status_dic['status'] = False
            status_dic['msg'] = 'Image not changed'
            return status_dic

        # --- Download scraped image (or use local image) ----------------------------------------
        selected_asset = assetdata_list[image_selected_index]
        log_debug('Selected asset_ID {0}'.format(selected_asset['asset_ID']))
        log_debug('Selected display_name {0}'.format(selected_asset['display_name']))

        # --- Resolve asset URL ---
        log_debug('Resolving asset URL ...')
        pdialog.startProgress('{} scraper (Resolving asset URL...)'.format(scraper_name), 100)
        image_url = self.scraper_obj.resolve_asset_URL(selected_asset, status_dic)
        pdialog.endProgress()
        log_debug('Resolved {} to URL "{}"'.format(asset_name, image_url))
        if not image_url:
            log_error('_gui_edit_asset() Error in scraper.resolve_asset_URL()')
            status_dic['status'] = False
            status_dic['msg'] = 'Error downloading asset'
            return status_dic
        pdialog.startProgress('{} scraper (Resolving URL extension...)'.format(scraper_name), 100)
        image_ext = self.scraper_obj.resolve_asset_URL_extension(image_url, status_dic)
        pdialog.endProgress()
        log_debug('Resolved URL extension "{}"'.format(image_ext))
        if not image_ext:
            log_error('_gui_edit_asset() Error in scraper.resolve_asset_URL_extension()')
            status_dic['status'] = False
            status_dic['msg'] = 'Error downloading asset'
            return status_dic

        # --- Download image ---
        log_debug('Downloading image ...')
        image_local_path = asset_path_noext_FN.append('.' + image_ext).getPath()
        log_verb('Downloading URL "{0}"'.format(image_url))
        log_verb('Into local file "{0}"'.format(image_local_path))
        pdialog.startProgress('Downloading {0}...'.format(asset_name), 100)
        try:
            net_download_img(image_url, image_local_path)
        except socket.timeout:
            pdialog.endProgress()
            kodi_notify_warn('Cannot download {0} image (Timeout)'.format(asset_name))
            status_dic['status'] = False
            status_dic['msg'] = 'Network timeout'
            return status_dic
        else:
            pdialog.endProgress()

        # --- Update Kodi cache with downloaded image ---
        # Recache only if local image is in the Kodi cache, this function takes care of that.
        # kodi_update_image_cache(image_local_path)

        # --- Edit using Python pass by assigment ---
        # If we reach this point is because an image was downloaded.
        # Caller is responsible to save Categories/Launchers/ROMs databases.
        object_dic[asset_info.key] = image_local_path
        status_dic['msg'] = 'Downloaded {0} with {1} scraper'.format(asset_name, scraper_name)

        return status_dic

    #
    # When scraping metadata or assets in the context menu, introduce the search strin,
    # grab candidate games, and select a candidate for scraping.
    #
    # @param object_name: [str] SCRAPE_ROM, SCRAPE_LAUNCHER.
    # @return: [dict] Dictionary with candidate data. None if error.
    def _scrap_CM_get_candidate(self, object_name, object_dic, data_dic, status_dic):
        # log_debug('ScrapeStrategy::_scrap_CM_get_candidate() BEGIN...')

        # In AEL 0.10.x this data is grabed from the objects, not passed using a dictionary.
        rom_base_noext = data_dic['rom_base_noext']
        platform = data_dic['platform']
        scraper_name = self.scraper_obj.get_name()

        # --- Ask user to enter ROM metadata search string ---
        # If ROM title has tags remove them for scraping.
        search_term = text_format_ROM_name_for_scraping(object_dic['m_name'])
        keyboard = xbmc.Keyboard(search_term, 'Enter the search term ...')
        keyboard.doModal()
        if not keyboard.isConfirmed():
            status_dic['status'] = False
            status_dic['dialog'] = KODI_MESSAGE_NOTIFY
            status_dic['msg'] = '{0} metadata unchanged'.format(object_name)
            return
        search_term = keyboard.getText().decode('utf-8')

        # --- Do a search and get a list of games ---
        pdialog = KodiProgressDialog()
        pdialog.startProgress('{0} scraper (Search game candidates...)'.format(scraper_name))
        candidate_list = self.scraper_obj.get_candidates(
            search_term, rom_base_noext, platform, status_dic)
        # If the there was an error in the scraper return immediately.
        if not status_dic['status']: return status_dic
        log_verb('Scraper found {0} result/s'.format(len(candidate_list)))
        if not candidate_list:
            status_dic['status'] = False
            status_dic['dialog'] = KODI_MESSAGE_NOTIFY_WARN
            status_dic['msg'] = 'Scraper found no matching games'
            return

        # --- Display corresponding game list found so user choses ---
        # If there is only one item in the list then don't show select dialog
        game_name_list = [c['display_name'] for c in candidate_list]
        if len(game_name_list) == 1:
            select_candidate_idx = 0
        else:
            select_candidate_idx = xbmcgui.Dialog().select(
                'Select game for ROM {0}'.format(object_dic['m_name']), game_name_list)
            if select_candidate_idx < 0:
                status_dic['status'] = False
                status_dic['dialog'] = KODI_MESSAGE_NOTIFY
                status_dic['msg'] = '{0} metadata unchanged'.format(object_name)
                return
        # log_debug('select_candidate_idx {0}'.format(select_candidate_idx))
        candidate = candidate_list[select_candidate_idx]
        log_verb('User chose game "{0}"'.format(candidate['display_name']))

        return candidate

#
# Abstract base class for all scrapers (offline or online, metadata or asset).
# The scrapers are Launcher and ROM agnostic. All the required Launcher/ROM properties are
# stored in the strategy object.
#
class Scraper(object):
    __metaclass__ = abc.ABCMeta

    # --- Class variables ------------------------------------------------------------------------
    # When then number of network error/exceptions is bigger than this threshold the scraper
    # is deactivated. This is useful in the ROM Scanner to not flood the user with error
    # messages in case something is wrong (for example, the internet connection is broken or
    # the number of API calls is exceeded).
    EXCEPTION_COUNTER_THRESHOLD = 3
    
    # Maximum amount of retries of certain requests
    RETRY_THRESHOLD = 4

    # --- Constructor ----------------------------------------------------------------------------
    # @param settings: [dict] Addon settings.
    def __init__(self, settings, fallbackScraper = None):
        self.settings = settings
        self.verbose_flag = False
        self.dump_file_flag = False
        # Record the number of network error/exceptions. If this number is bigger than a
        # threshold disable the scraper.
        self.exception_counter = 0
        # If this is True the scraper is internally disabled. A disabled scraper alwats returns
        # empty data like the NULL scraper.
        self.scraper_disabled = False

    # --- Methods --------------------------------------------------------------------------------
    # Scraper is much more verbose (even more than AEL Debug level).
    def set_verbose_mode(self, verbose_flag):
        log_debug('Scraper::set_verbose_mode() verbose_flag {0}'.format(verbose_flag))
        self.verbose_flag = verbose_flag

    # Dump scraper data into files for debugging.
    def set_debug_file_dump(self, dump_file_flag, dump_dir):
        log_debug('Scraper::set_verbose_mode() dump_file_flag {0}'.format(dump_file_flag))
        log_debug('Scraper::set_verbose_mode() dump_dir {0}'.format(dump_dir))
        self.dump_file_flag = dump_file_flag
        self.dump_dir = dump_dir

    # Dump dictionary as JSON file for debugging purposes.
    # This function is used internally by the scrapers if the flag self.dump_file_flag is True.
    def _dump_json_debug(self, file_name, data_dic):
        if not self.dump_file_flag: return
        file_path = os.path.join(self.dump_dir, file_name)
        json_str = json.dumps(data_dic, indent = 4, separators = (', ', ' : '))
        text_dump_str_to_file(file_path, json_str)

    def _dump_file_debug(self, file_name, page_data):
        if not self.dump_file_flag: return
        file_path = os.path.join(self.dump_dir, file_name)
        text_dump_str_to_file(file_path, page_data)

    @abc.abstractmethod
    def get_name(self): pass

    @abc.abstractmethod
    def supports_metadata_ID(self, metadata_ID): pass

    @abc.abstractmethod
    def supports_metadata(self): pass

    @abc.abstractmethod
    def supports_asset_ID(self, asset_ID): pass

    @abc.abstractmethod
    def supports_assets(self): pass

    # Check if the scraper is ready to work. For example, check if required API keys are
    # configured, etc. If there is some fatal errors then deactivate the scraper.
    #
    # @return: [dic] kodi_new_status_dic() status dictionary.
    @abc.abstractmethod
    def check_before_scraping(self, status_dic): pass

    # Search for candidates and return a list of dictionaries _new_candidate_dic().
    # * Every request to this function must be cached. Cached is done in the concrete scraper
    #   objects because the caching process i shihgly dependant on the scraper internals.
    # * If no candidates found by the scraper return an empty list and status is True.
    # * If there is an error/exception (network error, bad data returned) return None,
    #   the cause is printed in the log, status is False and the status dictionary contains
    #   a user notification.
    # * The number of network error/exceptions is recorded internally by the scraper. If the
    #   number of errors is **bigger than a threshold**, **the scraper is deactivated** (no more
    #   errors reported in the future, just empty data is returned).
    # * If the scraper is overloaded (maximum number of API/web requests) it is considered and
    #   error and the scraper is internally deactivated immediately. The error message associated
    #   with the scraper overloading must be printed once like any other error.
    #
    # @param search_term: [str] String to be searched.
    # @param rombase_noext: [str] rombase_noext is used by some scrapers instead of search_term,
    #                       notably the offline scrapers. Some scrapers require the literal name
    #                       of the ROM.
    # @param platform: [str] AEL platform.
    # @param status_dic: [dict] kodi_new_status_dic() status dictionary.
    # @return: [list] List of _new_candidate_dic() dictionaries. None if error/exception. Empty
    #          list if no candidates found.
    @abc.abstractmethod
    def get_candidates(self, search_term, rombase_noext, platform, status_dic): pass

    # Returns the metadata for a candidate (search result).
    # * See comments in get_candidates()
    #
    # @param candidate: [dict] Candidate returned by get_candidates()
    # @param status_dic: [dict] kodi_new_status_dic() status dictionary.
    # @return: [dict] Dictionary self._new_gamedata_dic(). If no metadata found (very unlikely)
    #          then a dictionary with default values is returned. If there is an error/exception
    #          None is returned, the cause printed in the log and status_dic has a message to show.
    @abc.abstractmethod
    def get_metadata(self, candidate, status_dic): pass

    # Returns a list of assets for a candidate (search result).
    # * Note that this function maybe called many times for the same candidate but
    #   different asset type, so a cache is necessary.
    # * See comments in get_candidates()
    #
    # @param candidate: [dict] Candidate returned by get_candidates()
    # @param status_dic: [dict] kodi_new_status_dic() status dictionary.
    # @return: [list] List of _new_assetdata_dic() dictionaries. If no assets found then an empty
    #          list is returned. If there is an error/exception None is returned, the cause printed
    #          in the log and status_dic has a message to show.
    @abc.abstractmethod
    def get_assets(self, candidate, asset_info, status_dic): pass

    # When returning the asset list with get_assets(), some sites return thumbnails images
    # because the real assets are on a single dedicate page. For this sites, resolve_asset_URL()
    # returns the true, full size URL of the asset.
    # Other scrapers, for example MobyGames, return both the thumbnail and the true asset URLs
    # in get_assets(). In such case, the implementation of this method is trivial.
    #
    # @param candidate: [dict] Candidate returned by get_candidates()
    # @param status_dic: [dict] kodi_new_status_dic() status dictionary.
    # @return: [str] String with the URL to download the asset. None is returned in case of
    #          error and status_dic updated.
    @abc.abstractmethod
    def resolve_asset_URL(self, candidate, status_dic): pass

    # Get the URL image extension. In some scrapers the type of asset cannot be obtained by
    # the asset URL and must be resolved to save the asset in the filesystem.
    #
    # @param image_url: [str] URL of the asset.
    # @param status_dic: [dict] kodi_new_status_dic() status dictionary.
    # @return: [str] String with the image extension in lowercase 'png', 'jpg', etc.
    #          None is returned in case or error/exception and status_dic updated.
    @abc.abstractmethod
    def resolve_asset_URL_extension(self, image_url, status_dic): pass

    # Not used now. candidate['id'] is used as hash value for the whole candidate dictionary.
    # candidate['id'] must be unique for each game.
    # def _dictionary_hash(self, my_dict):
    #     return hash(frozenset(sorted(my_dict.items())))

    # Nested dictionaries are not allowed. All the dictionaries here must be "hashable".
    # If your dictionary is not nested, you could make a frozenset with the dict's items
    # and use hash():
    #
    # hash(frozenset(sorted(my_dict.items())))
    #
    # This is much less computationally intensive than generating the JSON string
    # or representation of the dictionary.
    # See https://stackoverflow.com/questions/5884066/hashing-a-dictionary
    def _new_candidate_dic(self):
        return {
            'id'               : '',
            'display_name'     : '',
            'platform'         : '',
            'scraper_platform' : '',
            'order'            : 0,
        }

    def _new_gamedata_dic(self):
        return {
            'title'     : '',
            'year'      : '',
            'genre'     : '',
            'developer' : '',
            'nplayers'  : '',
            'esrb'      : '',
            'plot'      : ''
        }

    # url_thumb is always returned by get_assets().
    # url is returned by resolve_asset_URL().
    # Note that some scrapers (MobyGames) return both url_thumb and url in get_assets(). Always
    # call resolve_asset_URL() for compabilitity with all scrapers.
    def _new_assetdata_dic(self):
        return {
            'asset_ID'     : None,
            'display_name' : '',
            'url_thumb'    : '',
            'url'          : '',
            'is_online'    : True,
            'is_on_page'   : False
        }

    # This functions is called when an error that is not an exception and needs to increase
    # the scraper error limit happens.
    # All messages generated in the scrapers are KODI_MESSAGE_DIALOG.
    def _handle_error(self, status_dic, user_msg):
        # Print error message to the log.
        log_error('Scraper::_handle_error() user_msg "{}"'.format(user_msg))

        # Fill in the status dictionary so the error message will be propagated up in the
        # stack and the error message printed in the GUI.
        status_dic['status'] = False
        status_dic['dialog'] = KODI_MESSAGE_DIALOG
        status_dic['msg'] = user_msg
        
        # Record the number of error/exceptions produced in the scraper and disable the scraper
        # if the number of errors is higher than a threshold.
        self.exception_counter += 1
        if self.exception_counter > Scraper.EXCEPTION_COUNTER_THRESHOLD:
            err_m = 'Maximum number of errors exceeded. Disabling scraper.'
            log_error(err_m)
            self.scraper_disabled = True
            # Replace error message witht the one that the scraper is disabled.
            status_dic['msg'] = err_m

    # This function is called when an exception in the scraper code happens.
    # All messages from the scrapers are KODI_MESSAGE_DIALOG.
    def _handle_exception(self, ex, status_dic, user_msg):
        log_error('(Exception) Object type "{}"'.format(type(ex)))
        log_error('(Exception) Message "{}"'.format(str(ex)))
        self._handle_error(status_dic, user_msg)

# ------------------------------------------------------------------------------------------------
# NULL scraper, does nothing.
# ------------------------------------------------------------------------------------------------
class Null_Scraper(Scraper):
    # @param settings: [dict] Addon settings. Particular scraper settings taken from here.
    def __init__(self, settings): super(Null_Scraper, self).__init__(settings)

    def get_name(self): return 'Null'

    def supports_metadata_ID(self, metadata_ID): return False

    def supports_metadata(self): return False

    def supports_asset_ID(self, asset_ID): return False

    def supports_assets(self): return False

    def check_before_scraping(self, status_dic): return status_dic

    # Null scraper never finds candidates.
    def get_candidates(self, search_term, rombase_noext, platform, status_dic): return []

    # Null scraper never returns valid scraped metadata.
    def get_metadata(self, candidate, status_dic): return self._new_gamedata_dic()

    def get_assets(self, candidate, asset_info, status_dic): return []

    def resolve_asset_URL(self, candidate, status_dic): pass

    def resolve_asset_URL_extension(self, image_url, status_dic): return text_get_URL_extension(image_url)

# ------------------------------------------------------------------------------------------------
# AEL offline metadata scraper.
# ------------------------------------------------------------------------------------------------
class AEL_Offline(Scraper):
    # --- Class variables ------------------------------------------------------------------------
    supported_metadata_list = [
        META_TITLE_ID,
        META_YEAR_ID,
        META_GENRE_ID,
        META_DEVELOPER_ID,
        META_NPLAYERS_ID,
        META_ESRB_ID,
        META_PLOT_ID,
    ]

    # --- Constructor ----------------------------------------------------------------------------
    # @param settings: [dict] Addon settings. Particular scraper settings taken from here.
    def __init__(self, settings):
        # --- This scraper settings ---
        self.addon_dir = settings['scraper_aeloffline_addon_code_dir']
        log_debug('AEL_Offline::__init__() Setting addon dir "{}"'.format(self.addon_dir))

        # --- Cached TGDB metadata ---
        self._reset_cached_games()

        # --- Pass down common scraper settings ---
        super(AEL_Offline, self).__init__(settings)

    # --- Base class abstract methods ------------------------------------------------------------
    def get_name(self): return 'AEL Offline'

    def supports_metadata_ID(self, metadata_ID):
        return True if metadata_ID in ScreenScraper_V1.supported_metadata_list else False

    def supports_metadata(self): return True

    def supports_asset_ID(self, asset_ID): return False

    def supports_assets(self): return False

    def check_before_scraping(self, status_dic): return status_dic

    def get_candidates(self, search_term, rombase_noext, platform, status_dic):
        log_debug('AEL_Offline::get_candidates() search_term   "{0}"'.format(search_term))
        log_debug('AEL_Offline::get_candidates() rombase_noext "{0}"'.format(rombase_noext))
        log_debug('AEL_Offline::get_candidates() AEL platform  "{0}"'.format(platform))

        # If not cached XML data found (maybe offline scraper does not exist for this platform or 
        # cannot be loaded) return an empty list of candidates.
        self._initialise_platform(platform)
        if not self.cached_games: return []

        if platform == 'MAME':
            # --- Search MAME games ---
            candidate_list = self._get_MAME_candidates(search_term, rombase_noext, platform)
        else:
            # --- Search No-Intro games ---
            candidate_list = self._get_NoIntro_candidates(search_term, rombase_noext, platform)

        return candidate_list

    def get_metadata(self, candidate, status_dic):
        gamedata = self._new_gamedata_dic()

        if self.cached_platform == 'MAME':
            # --- MAME scraper ---
            key_id = candidate['id']
            log_verb("AEL_Offline::get_metadata() Mode MAME id = '{0}'".format(key_id))
            gamedata['title']     = self.cached_games[key_id]['description']
            gamedata['year']      = self.cached_games[key_id]['year']
            gamedata['genre']     = self.cached_games[key_id]['genre']
            gamedata['developer'] = self.cached_games[key_id]['manufacturer']
        elif self.cached_platform == 'Unknown':
            # --- Unknown platform. Behave like NULL scraper ---
            log_verb("AEL_Offline::get_metadata() Mode Unknown. Doing nothing.")
        else:
            # --- No-Intro scraper ---
            key_id = candidate['id']
            log_verb("AEL_Offline::get_metadata() Mode No-Intro id = '{0}'".format(key_id))
            gamedata['title']     = self.cached_games[key_id]['description']
            gamedata['year']      = self.cached_games[key_id]['year']
            gamedata['genre']     = self.cached_games[key_id]['genre']
            gamedata['developer'] = self.cached_games[key_id]['manufacturer']
            gamedata['nplayers']  = self.cached_games[key_id]['player']
            gamedata['esrb']      = self.cached_games[key_id]['rating']
            gamedata['plot']      = self.cached_games[key_id]['story']

        return gamedata

    def get_assets(self, candidate, asset_info, status_dic): return []

    def resolve_asset_URL(self, candidate, status_dic): pass

    def resolve_asset_URL_extension(self, image_url, status_dic): pass

    # --- This class own methods -----------------------------------------------------------------
    def _get_MAME_candidates(self, search_term, rombase_noext, platform):
        log_verb("AEL_Offline::_get_MAME_candidates() Scraper working in MAME mode.")

        # --- MAME rombase_noext is exactly the rom name ---
        # MAME offline scraper either returns one candidate game or nothing at all.
        rom_base_noext_lower = rombase_noext.lower()
        if rom_base_noext_lower in self.cached_games:
            candidate = self._new_candidate_dic()
            candidate['id'] = self.cached_games[rom_base_noext_lower]['name']
            candidate['display_name'] = self.cached_games[rom_base_noext_lower]['description']
            candidate['platform'] = platform
            candidate['scraper_platform'] = platform
            candidate['order'] = 1
            return [candidate]
        else:
            return []

    def _get_NoIntro_candidates(self, search_term, rombase_noext, platform):
        # --- First try an exact match using rombase_noext ---
        log_verb("AEL_Offline::_get_NoIntro_candidates() Scraper working in No-Intro mode.")
        log_verb("AEL_Offline::_get_NoIntro_candidates() Trying exact search for '{0}'".format(
            rombase_noext))
        candidate_list = []
        if rombase_noext in self.cached_games:
            log_verb("AEL_Offline::_get_NoIntro_candidates() Exact match found.")
            candidate = self._new_candidate_dic()
            candidate['id'] = rombase_noext
            candidate['display_name'] = self.cached_games[rombase_noext]['name']
            candidate['platform'] = platform
            candidate['scraper_platform'] = platform
            candidate['order'] = 1
            candidate_list.append(candidate)
        else:
            # --- If nothing found, do a fuzzy search ---
            log_verb("AEL_Offline::_get_NoIntro_candidates() No exact match found.")
            log_verb("AEL_Offline::_get_NoIntro_candidates() Trying fuzzy search '{0}'".format(
                search_term))
            search_string_lower = search_term.lower()
            regexp = '.*{0}.*'.format(search_string_lower)
            try:
                # Sometimes this produces: raise error, v # invalid expression
                p = re.compile(regexp)
            except:
                log_info('AEL_Offline::_get_NoIntro_candidates() Exception in re.compile(regexp)')
                log_info('AEL_Offline::_get_NoIntro_candidates() regexp = "{0}"'.format(regexp))
                return []

            for key in self.cached_games:
                this_game_name = self.cached_games[key]['name']
                this_game_name_lower = this_game_name.lower()
                match = p.match(this_game_name_lower)
                if not match: continue
                # --- Add match to candidate list ---
                candidate = self._new_candidate_dic()
                candidate['id'] = self.cached_games[key]['name']
                candidate['display_name'] = self.cached_games[key]['name']
                candidate['platform'] = platform
                candidate['scraper_platform'] = platform
                candidate['order'] = 1
                # If there is an exact match of the No-Intro name put that candidate game first.
                if search_term == this_game_name:                          candidate['order'] += 1
                if rombase_noext == this_game_name:                        candidate['order'] += 1
                if self.cached_games[key]['name'].startswith(search_term): candidate['order'] += 1
                candidate_list.append(candidate)
            candidate_list.sort(key = lambda result: result['order'], reverse = True)

        return candidate_list

    # Load XML database and keep it cached in memory.
    def _initialise_platform(self, platform):
        # Check if we have data already cached in object memory for this platform
        if self.cached_platform == platform:
            log_debug('AEL_Offline::_initialise_platform() platform = "{0}" is cached in object.'.format(
                platform))
            return
        else:
            log_debug('AEL_Offline::_initialise_platform() platform = "{0}" not cached. Loading XML.'.format(
                platform))

        # What if platform is not in the official list dictionary? Then load
        # nothing and behave like the NULL scraper.
        try:
            xml_file = platform_AEL_to_Offline_GameDBInfo_XML[platform]
        except:
            log_debug('AEL_Offline::_initialise_platform() Platform {0} not found'.format(platform))
            log_debug('AEL_Offline::_initialise_platform() Defaulting to Unknown')
            self._reset_cached_games()
            return

        # Load XML database and keep it in memory for subsequent calls
        xml_path = os.path.join(self.addon_dir, xml_file)
        # log_debug('AEL_Offline::_initialise_platform() Loading XML {0}'.format(xml_path))
        self.cached_games = audit_load_OfflineScraper_XML(xml_path)
        if not self.cached_games:
            self._reset_cached_games()
            return
        self.cached_xml_path = xml_path
        self.cached_platform = platform
        log_debug('AEL_Offline::_initialise_platform() cached_xml_path = {0}'.format(self.cached_xml_path))
        log_debug('AEL_Offline::_initialise_platform() cached_platform = {0}'.format(self.cached_platform))

    def _reset_cached_games(self):
        self.cached_games = {}
        self.cached_xml_path = ''
        self.cached_platform = 'Unknown'

# ------------------------------------------------------------------------------------------------
# LaunchBox offline metadata scraper.
# Do not implement this scraper. It is better to have one good offline scraper than many bad.
# Users will be encouraged to improve the AEL Offline scraper.
# ------------------------------------------------------------------------------------------------
# class LB_Offline(Scraper): pass

# ------------------------------------------------------------------------------------------------
# TheGamesDB online scraper (metadata and assets).
# TheGamesDB is the scraper reference implementation. Always look here for comments when
# developing other scrapers.
#
# | Site     | https://thegamesdb.net      |
# | API info | https://api.thegamesdb.net/ |
# ------------------------------------------------------------------------------------------------
class TheGamesDB(Scraper):
    # --- Class variables ------------------------------------------------------------------------
    supported_metadata_list = [
        META_TITLE_ID,
        META_YEAR_ID,
        META_GENRE_ID,
        META_DEVELOPER_ID,
        META_NPLAYERS_ID,
        META_ESRB_ID,
        META_PLOT_ID,
    ]
    supported_asset_list = [
        ASSET_FANART_ID,
        ASSET_BANNER_ID,
        ASSET_CLEARLOGO_ID,
        ASSET_SNAP_ID,
        ASSET_BOXFRONT_ID,
        ASSET_BOXBACK_ID,
    ]
    asset_name_mapping = {
        'screenshot': ASSET_SNAP_ID,
        'boxart' : ASSET_BOXFRONT_ID,
        'boxartfront': ASSET_BOXFRONT_ID,
        'boxartback': ASSET_BOXBACK_ID,
        'fanart' : ASSET_FANART_ID,
        'clearlogo': ASSET_CLEARLOGO_ID,
        'banner': ASSET_BANNER_ID,
    }

    # --- Constructor ----------------------------------------------------------------------------
    def __init__(self, settings):
        # --- This scraper settings ---
        # Make sure this is the public key (limited by IP) and not the private key.
        self.api_public_key = '828be1fb8f3182d055f1aed1f7d4da8bd4ebc160c3260eae8ee57ea823b42415'
        if settings['scraper_thegamesdb_apikey'] is not None:
            self.api_public_key = settings['scraper_thegamesdb_apikey']
            
        # --- Cached TGDB metadata ---
        self.cache_candidates = {}
        self.cache_metadata = {}
        self.cache_assets = {}
        self.all_asset_cache = {}

        self.genres_cached = {}
        self.developers_cached = {}
        self.publishers_cached = {}

        # --- Pass down common scraper settings ---
        super(TheGamesDB, self).__init__(settings)

    # --- Base class abstract methods ------------------------------------------------------------
    def get_name(self): return 'TheGamesDB'

    def supports_metadata_ID(self, metadata_ID):
        return True if metadata_ID in TheGamesDB.supported_metadata_list else False

    def supports_metadata(self): return True

    def supports_asset_ID(self, asset_ID):
        return True if asset_ID in TheGamesDB.supported_asset_list else False

    def supports_assets(self): return True

    # TGDB does not require any API keys. By default status_dic is configured for successful
    # operation so return it as it is.
    def check_before_scraping(self, status_dic): return status_dic

    # This function may be called many times in the ROM Scanner. All calls to this function
    # must be cached. See comments for this function in the Scraper abstract class.
    def get_candidates(self, search_term, rombase_noext, platform, status_dic):
        # --- If scraper is disabled return immediately and silently ---
        if self.scraper_disabled:
            log_debug('TheGamesDB::get_candidates() Scraper disabled. Returning empty data.')
            return []

        # --- Check if search term is in the cache ---
        cache_key = search_term + '__' + rombase_noext + '__' + platform
        if cache_key in self.cache_candidates:
            log_debug('TheGamesDB::get_candidates() Cache hit "{0}"'.format(cache_key))
            candidate_list = self.cache_candidates[cache_key]
            return candidate_list

        # --- Request is not cached. Get candidates and introduce in the cache ---
        log_debug('TheGamesDB::get_candidates() Cache miss "{0}"'.format(cache_key))
        scraper_platform = AEL_platform_to_TheGamesDB(platform)
        log_debug('TheGamesDB::get_candidates() search_term         "{0}"'.format(search_term))
        log_debug('TheGamesDB::get_candidates() rom_base_noext      "{0}"'.format(rombase_noext))
        log_debug('TheGamesDB::get_candidates() AEL platform        "{0}"'.format(platform))
        log_debug('TheGamesDB::get_candidates() TheGamesDB platform "{0}"'.format(scraper_platform))
        candidate_list = self._search_candidates(
            search_term, rombase_noext, platform, scraper_platform, status_dic)
        # If an error happened do not update the cache.
        if not status_dic['status']: return None

        # --- Add candidate games to the cache ---
        log_debug('TheGamesDB::get_candidates() Adding to cache "{0}"'.format(cache_key))
        self.cache_candidates[cache_key] = candidate_list

        # --- Deactivate this for now ---
        # if len(candidate_list) == 0:
        #     altered_search_term = self._cleanup_searchterm(search_term, rombase_noext, platform)
        #     log_debug('Cleaning search term. Before "{0}"'.format(search_term))
        #     log_debug('After "{0}"'.format(altered_search_term))
        #     if altered_search_term != search_term:
        #         log_debug('No matches, trying again with altered search terms: {0}'.format(
        #             altered_search_term))
        #         return self._get_candidates(altered_search_term, rombase_noext, platform)

        return candidate_list
    
    # This function may be called many times in the ROM Scanner. All calls to this function
    # must be cached. See comments for this function in the Scraper abstract class.
    def get_metadata(self, candidate, status_dic):
        # --- If scraper is disabled return immediately and silently ---
        if self.scraper_disabled:
            log_debug('TheGamesDB::get_metadata() Scraper disabled. Returning empty data.')
            return self._new_gamedata_dic()

        # --- Check if search term is in the cache ---
        cache_key = str(candidate['id'])
        if cache_key in self.cache_metadata:
            log_debug('TheGamesDB::get_metadata() Cache hit "{0}"'.format(cache_key))
            gamedata = self.cache_metadata[cache_key]
            return gamedata

        # --- Request is not cached. Get candidates and introduce in the cache ---
        # | Mandatory field | JSON example                          | Used |
        # |-----------------|---------------------------------------|------|
        # | id              | "id": 1                               | N/A  |
        # | game_title      | "game_title": "Halo: Combat Evolved"  | N/A  |
        # | release_date    | "release_date": "2001-11-15"          | N/A  |
        # | developers      | "developers": [ 1389 ]                | N/A  |
        # |-----------------|---------------------------------------|------|
        # | Optional field  | JSON example                          | Used |
        # |-----------------|---------------------------------------|------|
        # | players         | "players" : 1                         | Yes  |
        # | publishers      | "publishers": [ 1 ]                   | No   |
        # | genres          | "genres": [ 8 ]                       | Yes  |
        # | overview        | "overview": "In Halo's ..."           | Yes  |
        # | last_updated    | "last_updated": "2018-07-11 21:05:01" | No   |
        # | rating          | "rating": "M - Mature"                | Yes  |
        # | platform        | "platform": 1                         | No   |
        # | coop            | "coop": "No"                          | No   |
        # | youtube         | "youtube": "dR3Hm8scbEw"              | No   |
        # | alternates      | "alternates": null                    | No   |
        # |-----------------|---------------------------------------|------|
        log_debug('TheGamesDB::get_metadata() Cache miss "{0}"'.format(cache_key))
        url_a = 'https://api.thegamesdb.net/Games/ByGameID?apikey={0}&id={1}'
        url_b = '&fields=players%2Cgenres%2Coverview%2Crating'
        url_a = url_a.format(self._get_API_key(), candidate['id'])
        url = url_a + url_b
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('TGDB_get_metadata.json', json_data)

        # --- Parse game page data ---
        log_debug('TheGamesDB::get_metadata() Parsing game metadata...')
        online_data = json_data['data']['games'][0]
        gamedata = self._new_gamedata_dic()
        gamedata['title']     = self._parse_metadata_title(online_data)
        gamedata['year']      = self._parse_metadata_year(online_data)
        gamedata['genre']     = self._parse_metadata_genres(online_data, status_dic)
        if not status_dic['status']: return None
        gamedata['developer'] = self._parse_metadata_developer(online_data, status_dic)
        if not status_dic['status']: return None
        gamedata['nplayers']  = self._parse_metadata_nplayers(online_data)
        gamedata['esrb']      = self._parse_metadata_esrb(online_data)
        gamedata['plot']      = self._parse_metadata_plot(online_data)

        # --- Put metadata in the cache ---
        log_debug('TheGamesDB::get_metadata() Adding to cache "{0}"'.format(cache_key))
        self.cache_metadata[cache_key] = gamedata

        return gamedata
 
    # This function may be called many times in the ROM Scanner. All calls to this function
    # must be cached. See comments for this function in the Scraper abstract class.
    def get_assets(self, candidate, asset_info, status_dic):
        # --- If scraper is disabled return immediately and silently ---
        if self.scraper_disabled:
            log_debug('TheGamesDB::get_assets() Scraper disabled. Returning empty data.')
            return []

        log_debug('Scraper::get_assets() Getting assets {} (ID {}) for candidate ID = {}'.format(
            asset_info.name, asset_info.id, candidate['id']))

        # --- Check if search term is in the cache ---
        cache_key = str(candidate['id']) + '__' + asset_info.name + '__' + str(asset_info.id)
        if cache_key in self.cache_assets:
            log_debug('Scraper::get_assets() Cache hit "{0}"'.format(cache_key))
            asset_list = self.cache_assets[cache_key]
            return asset_list

        # --- Request is not cached. Get candidates and introduce in the cache ---
        log_debug('Scraper::get_assets() Cache miss "{0}"'.format(cache_key))
        # Get all assets for candidate. _scraper_get_assets_all() caches all assets for a
        # candidate. Then select asset of a particular type.
        all_asset_list = self._retrieve_all_assets(candidate, status_dic)
        if not status_dic['status']: return None
        asset_list = [asset_dic for asset_dic in all_asset_list if asset_dic['asset_ID'] == asset_info.id]
        log_debug('TheGamesDB::get_assets() Total assets {0} / Returned assets {1}'.format(
        len(all_asset_list), len(asset_list)))

        # --- Put metadata in the cache ---
        self.cache_assets[cache_key] = asset_list

        return asset_list

    def resolve_asset_URL(self, candidate, status_dic):
        return candidate['url']

    def resolve_asset_URL_extension(self, image_url, status_dic):
        return text_get_URL_extension(image_url)

    # --- This class own methods -----------------------------------------------------------------
    def debug_get_platforms(self, status_dic):
        log_debug('TheGamesDB::debug_get_platforms() BEGIN...')
        url = 'https://api.thegamesdb.net/Platforms?apikey={}'.format(self._get_API_key())
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('TGDB_get_platforms.json', json_data)

        return json_data

    def debug_get_genres(self, status_dic):
        log_debug('TheGamesDB::debug_get_genres() BEGIN...')
        url = 'https://api.thegamesdb.net/Genres?apikey={}'.format(self._get_API_key())
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('TGDB_get_genres.json', json_data)

        return json_data

    # Always use the developer public key which is limited per IP address. This function
    # may return the private key during scraper development for debugging purposes.
    def _get_API_key(self): return self.api_public_key

    # --- Retrieve list of games ---
    def _search_candidates(self, search_term, rombase_noext, platform, scraper_platform, status_dic):
        # quote_plus() will convert the spaces into '+'. Note that quote_plus() requires an
        # UTF-8 encoded string and does not work with Unicode strings.
        # https://stackoverflow.com/questions/22415345/using-pythons-urllib-quote-plus-on-utf-8-strings-with-safe-arguments
        search_string_encoded = urllib.quote_plus(search_term.encode('utf8'))
        url_str = 'https://api.thegamesdb.net/Games/ByGameName?apikey={0}&name={1}&filter[platform]={2}'
        url = url_str.format(self._get_API_key(), search_string_encoded, scraper_platform)
        # _retrieve_games_from_url() may load files recursively from several pages so this code
        # must be in a separate function.
        candidate_list = self._retrieve_games_from_url(
            url, search_term, platform, scraper_platform, status_dic)
        if not status_dic['status']: return None

        # --- Sort game list based on the score. High scored candidates go first ---
        candidate_list.sort(key = lambda result: result['order'], reverse = True)

        return candidate_list

    # Return a list of candiate games. Return None if error/exception.
    def _retrieve_games_from_url(self, url, search_term, platform, scraper_platform, status_dic):
        # --- Get URL data as JSON ---
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('TGDB_get_candidates.json', json_data)

        # --- Parse game list ---
        games_json = json_data['data']['games']
        candidate_list = []
        for item in games_json:
            title = item['game_title']
            candidate = self._new_candidate_dic()
            candidate['id'] = item['id']
            candidate['display_name'] = title
            candidate['platform'] = platform
            candidate['scraper_platform'] = scraper_platform
            candidate['order'] = 1
            # Increase search score based on our own search.
            if title.lower() == search_term.lower():                  candidate['order'] += 2
            if title.lower().find(search_term.lower()) != -1:         candidate['order'] += 1
            if scraper_platform > 0 and platform == scraper_platform: candidate['order'] += 1
            candidate_list.append(candidate)

        log_debug('TheGamesDB:: Found {0} titles with last request'.format(len(candidate_list)))
        # --- Recursively load more games ---
        next_url = json_data['pages']['next']
        if next_url is not None:
            log_debug('TheGamesDB::_retrieve_games_from_url() Recursively loading game page')
            candidate_list = candidate_list + self._retrieve_games_from_url(
                next_url, search_term, scraper_platform)

        return candidate_list

    def _cleanup_searchterm(self, search_term, rom_path, rom):
        altered_term = search_term.lower().strip()
        for ext in self.launcher.get_rom_extensions():
            altered_term = altered_term.replace(ext, '')
        return altered_term

    def _parse_metadata_title(self, online_data):
        if 'game_title' in online_data: title_str = online_data['game_title']
        else:                           title_str = DEFAULT_META_TITLE

        return title_str

    def _parse_metadata_year(self, online_data):
        if 'release_date' in online_data and \
           online_data['release_date'] is not None and \
           online_data['release_date'] != '':
            year_str = online_data['release_date'][:4]
        else:
            year_str = DEFAULT_META_YEAR
        return year_str

    def _parse_metadata_genres(self, online_data, status_dic):
        if 'genres' not in online_data: return ''
        # "genres" : [ 1 , 15 ],
        genre_ids = online_data['genres']
        # log_variable('genre_ids', genre_ids)
        # For some games genre_ids is None. In that case return an empty string (default DB value).
        if not genre_ids: return DEFAULT_META_GENRE
        TGDB_genres = self._retrieve_genres(status_dic)
        if not status_dic['status']: return None
        genre_list = [TGDB_genres[genre_id] for genre_id in genre_ids]
        return ', '.join(genre_list)

    def _parse_metadata_developer(self, online_data, status_dic):
        if 'developers' not in online_data: return ''
        # "developers" : [ 7979 ],
        developers_ids = online_data['developers']
        # For some games developers_ids is None. In that case return an empty string (default DB value).
        if not developers_ids: return DEFAULT_META_DEVELOPER
        TGDB_developers = self._retrieve_developers(status_dic)
        if not status_dic['status']: return None
        developer_list = [TGDB_developers[dev_id] for dev_id in developers_ids]

        return ', '.join(developer_list)

    def _parse_metadata_nplayers(self, online_data):
        if 'players' in online_data: nplayers_str = str(online_data['players'])
        else:                        nplayers_str = DEFAULT_META_NPLAYERS

        return nplayers_str

    def _parse_metadata_esrb(self, online_data):
        if 'rating' in online_data: esrb_str = online_data['rating']
        else:                       esrb_str = DEFAULT_META_ESRB

        return esrb_str

    def _parse_metadata_plot(self, online_data):
        if 'overview' in online_data: plot_str = online_data['overview']
        else:                         plot_str = DEFAULT_META_PLOT

        return plot_str

    # Get a dictionary of TGDB genres (integers) to AEL genres (strings).
    # TGDB genres are cached in an object variable.
    def _retrieve_genres(self, status_dic):
        # --- Cache hit ---
        if self.genres_cached:
            log_debug('TheGamesDB::_retrieve_genres() Genres cache hit.')
            return self.genres_cached

        # --- Cache miss. Retrieve data ---
        log_debug('TheGamesDB::_retrieve_genres() Genres cache miss. Retrieving genres...')
        url = 'https://api.thegamesdb.net/Genres?apikey={}'.format(self._get_API_key())
        page_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('TGDB_get_genres.json', page_data)

        # --- Update cache ---
        self.genres_cached = {}
        for genre_id in page_data['data']['genres']:
            self.genres_cached[int(genre_id)] = page_data['data']['genres'][genre_id]['name']
        log_debug('TheGamesDB::_retrieve_genres() There are {} genres'.format(len(self.genres_cached)))

        return self.genres_cached

    def _retrieve_developers(self, status_dic):
        # --- Cache hit ---
        if self.developers_cached:
            log_debug('TheGamesDB::_retrieve_developers() Developers cache hit.')
            return self.developers_cached

        # --- Cache miss. Retrieve data ---
        log_debug('TheGamesDB::_retrieve_developers() Developers cache miss. Retrieving developers...')
        url = 'https://api.thegamesdb.net/Developers?apikey={}'.format(self._get_API_key())
        page_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('TGDB_get_developers.json', page_data)

        # --- Update cache ---
        self.developers_cached = {}
        for developer_id in page_data['data']['developers']:
            self.developers_cached[int(developer_id)] = page_data['data']['developers'][developer_id]['name']
        log_debug('TheGamesDB::_retrieve_developers() There are {} developers'.format(len(self.genres_cached)))

        return self.developers_cached

    # Publishers is not used in AEL at the moment.
    # THIS FUNCTION CODE MUST BE UPDATED.
    def _retrieve_publishers(self, publisher_ids):
        if publisher_ids is None: return ''
        if self.publishers_cached is None:
            log_debug('TheGamesDB:: No cached publishers. Retrieving from online.')
            url = 'https://api.thegamesdb.net/Publishers?apikey={}'.format(self._get_API_key())
            page_data_raw = net_get_URL(url, self._clean_URL_for_log(url))
            publishers_json = json.loads(page_data_raw)
            self.publishers_cached = {}
            for publisher_id in publishers_json['data']['publishers']:
                self.publishers_cached[int(publisher_id)] = publishers_json['data']['publishers'][publisher_id]['name']
        publisher_names = [self.publishers_cached[publisher_id] for publisher_id in publisher_ids]

        return ' / '.join(publisher_names)

    # Get ALL available assets for game.
    # Cache the results because this function may be called multiple times.
    def _retrieve_all_assets(self, candidate, status_dic):
        # --- Cache hit ---
        cache_key = str(candidate['id'])
        if cache_key in self.all_asset_cache:
            log_debug('TheGamesDB::_retrieve_all_assets() Cache hit "{0}"'.format(cache_key))
            asset_list = self.all_asset_cache[cache_key]
            return asset_list

        # --- Cache miss. Retrieve data and update cache ---
        log_debug('TheGamesDB::_retrieve_all_assets() Cache miss "{0}". Retrieving all assets...'.format(
            cache_key))
        url = 'https://api.thegamesdb.net/Games/Images?apikey={}&games_id={}'.format(
            self._get_API_key(), candidate['id'])
        asset_list = self._retrieve_assets_from_url(url, candidate['id'], status_dic)
        if not status_dic['status']: return None
        log_debug('A total of {0} assets found for candidate ID {1}'.format(
            len(asset_list), candidate['id']))
        self.all_asset_cache[cache_key] = asset_list

        return asset_list

    def _retrieve_assets_from_url(self, url, candidate_id, status_dic):
        # --- Read URL JSON data ---
        page_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('TGDB_get_assets.json', page_data)

        # --- Parse images page data ---
        base_url_thumb = page_data['data']['base_url']['thumb']
        base_url = page_data['data']['base_url']['original']
        assets_list = []
        for image_data in page_data['data']['images'][str(candidate_id)]:
            asset_name = '{0} ID {1}'.format(image_data['type'], image_data['id'])
            if image_data['type'] == 'boxart':
                if   image_data['side'] == 'front': asset_ID = ASSET_BOXFRONT_ID
                elif image_data['side'] == 'back':  asset_ID = ASSET_BOXBACK_ID
                else:                               raise ValueError
            else:
                asset_ID = TheGamesDB.asset_name_mapping[image_data['type']]
            asset_fname = image_data['filename']

            # url_thumb is mandatory.
            # url is not mandatory here but MobyGames provides it anyway.
            asset_data = self._new_assetdata_dic()
            asset_data['asset_ID'] = asset_ID
            asset_data['display_name'] = asset_name
            asset_data['url_thumb'] = base_url_thumb + asset_fname
            asset_data['url'] = base_url + asset_fname
            if self.verbose_flag:
                log_debug('TheGamesDB:: Found Asset {0}'.format(asset_data['name']))
            assets_list.append(asset_data)

        # --- Recursively load more assets ---
        next_url = page_data['pages']['next']
        if next_url is not None:
            log_debug('TheGamesDB::_retrieve_assets_from_url() Recursively loading assets page')
            assets_list = assets_list + self._retrieve_assets_from_url(next_url, candidate_id)

        return assets_list

    # TGDB URLs are safe for printing, however the API key is too long.
    # Clean URLs for safe logging.
    def _clean_URL_for_log(self, url):
        clean_url = url
        # apikey is followed by more arguments
        clean_url = re.sub('apikey=[^&]*&', 'apikey=***&', clean_url)
        # apikey is at the end of the string
        clean_url = re.sub('apikey=[^&]*$', 'apikey=***', clean_url)
        # log_variable('url', url)
        # log_variable('clean_url', clean_url)

        return clean_url

    # Retrieve URL and decode JSON object.
    def _retrieve_URL_as_JSON(self, url, status_dic):
        page_data_raw, http_code = net_get_URL(url, self._clean_URL_for_log(url))
        if page_data_raw is None:
            self._handle_error(status_dic, 'TGDB: Network error in net_get_URL()')
            return None
        try:
            json_data = json.loads(page_data_raw)
        except Exception as ex:
            self._handle_exception(ex, status_dic, 'Error decoding JSON data from TheGamesDB.')
            return None
        # Check for scraper overloading. Scraper is disabled if overloaded.
        # Does the scraper return valid JSON when it is overloaded??? I have to confirm this point.
        self._check_overloading(json_data, status_dic)
        if not status_dic['status']: return None

        return json_data

    # Checks if TDGB scraper is overloaded (maximum number of API requests exceeded).
    # If the scraper is overloaded is immediately disabled.
    #
    # @param json_data: [dict] Dictionary with JSON data retrieved from TGDB.
    # @returns: [None]
    def _check_overloading(self, json_data, status_dic):
        # This is an integer.
        remaining_monthly_allowance = json_data['remaining_monthly_allowance']
        extra_allowance = json_data['extra_allowance']
        log_debug('TheGamesDB::_check_overloading() remaining_monthly_allowance = {}'.format(
            remaining_monthly_allowance))
        if extra_allowance:
            log_debug('TheGamesDB::_check_overloading() extra_allowance = {}'.format(
                extra_allowance))
        else: extra_allowance = 0
        if remaining_monthly_allowance > 0 or extra_allowance > 0: return
        log_error('TheGamesDB::_check_overloading() remaining_monthly_allowance <= 0')
        log_error('Disabling TGDB scraper.')
        self.scraper_disabled = True
        status_dic['status'] = False
        status_dic['dialog'] = KODI_MESSAGE_DIALOG
        status_dic['msg'] = 'TGDB monthly allowance is {0}. Scraper disabled.'.format(
            remaining_monthly_allowance)

# ------------------------------------------------------------------------------------------------
# MobyGames online scraper.
#
# TODO
# 1) Detect 401 Unauthorized and warn user.
#
# 2) Detect 429 Too Many Requests and disable scraper. We never do more than one call per second
#    so if we get 429 is because the 360 API requests per hour are consumed.
#
# | Site     | https://www.mobygames.com          |
# | API info | https://www.mobygames.com/info/api |
# ------------------------------------------------------------------------------------------------
class MobyGames(Scraper):
    # --- Class variables ------------------------------------------------------------------------
    supported_metadata_list = [
        META_TITLE_ID,
        META_YEAR_ID,
        META_GENRE_ID,
        META_PLOT_ID,
    ]
    supported_asset_list = [
        ASSET_TITLE_ID,
        ASSET_SNAP_ID,
        ASSET_BOXFRONT_ID,
        ASSET_BOXBACK_ID,
        ASSET_CARTRIDGE_ID,
        ASSET_MANUAL_ID,
    ]
    asset_name_mapping = {
        'media'         : ASSET_CARTRIDGE_ID,
        'manual'        : ASSET_MANUAL_ID,
        'front cover'   : ASSET_BOXFRONT_ID,
        'back cover'    : ASSET_BOXBACK_ID,
        'spine/sides'   : None,
        'other'         : None,
        'advertisement' : None,
        'extras'        : None,
        'inside cover'  : None,
        'full cover'    : None,
        'soundtrack'    : None,
        'map'           : ASSET_MAP_ID
    }

    # --- Constructor ----------------------------------------------------------------------------
    def __init__(self, settings):
        # --- This scraper settings ---
        self.api_key = settings['scraper_mobygames_apikey']

        # --- Misc stuff ---
        self.cache_candidates = {}
        self.cache_metadata = {}
        self.cache_assets = {}
        self.all_asset_cache = {}
        self.last_http_call = datetime.now()
        # --- Pass down common scraper settings ---
        super(MobyGames, self).__init__(settings)

    # --- Base class abstract methods ------------------------------------------------------------
    def get_name(self): return 'MobyGames'

    def supports_metadata_ID(self, metadata_ID):
        return True if metadata_ID in MobyGames.supported_metadata_list else False

    def supports_metadata(self): return True

    def supports_asset_ID(self, asset_ID):
        return True if asset_ID in MobyGames.supported_asset_list else False

    def supports_assets(self): return True

    # If the MobyGames API key is not configured in the settings then disable the scraper
    # and print an error.
    def check_before_scraping(self, status_dic):
        if self.api_key:
            log_error('MobyGames::check_before_scraping() MobiGames API key looks OK.')
            return
        log_error('MobyGames::check_before_scraping() MobiGames API key not configured.')
        log_error('MobyGames::check_before_scraping() Disabling MobyGames scraper.')
        self.scraper_disabled = True
        status_dic['status'] = False
        status_dic['dialog'] = KODI_MESSAGE_DIALOG
        status_dic['msg'] = (
            'AEL requires your MobyGames API key. '
            'Visit https://www.mobygames.com/info/api for directions about how to get your key '
            'and introduce the API key in AEL addon settings.'
        )

    # This function may be called many times in the ROM Scanner. All calls to this function
    # must be cached. See comments for this function in the Scraper abstract class.
    def get_candidates(self, search_term, rombase_noext, platform, status_dic):
        # --- If scraper is disabled return immediately and silently ---
        if self.scraper_disabled:
            log_debug('MobyGames::get_candidates() Scraper disabled. Returning empty data.')
            return []

        # --- Check if search term is in the cache ---
        cache_key = search_term + '__' + rombase_noext + '__' + platform
        if cache_key in self.cache_candidates:
            log_debug('MobyGames::get_candidates() Cache hit "{0}"'.format(cache_key))
            candidate_list = self.cache_candidates[cache_key]
            return candidate_list

        # --- Request is not cached. Get candidates and introduce in the cache ---
        log_debug('MobyGames::get_candidates() Cache miss "{0}"'.format(cache_key))
        scraper_platform = AEL_platform_to_MobyGames(platform)
        log_debug('MobyGames::get_candidates() search_term        "{0}"'.format(search_term))
        log_debug('MobyGames::get_candidates() rom_base_noext     "{0}"'.format(rombase_noext))
        log_debug('MobyGames::get_candidates() AEL platform       "{0}"'.format(platform))
        log_debug('MobyGames::get_candidates() MobyGames platform "{0}"'.format(scraper_platform))
        candidate_list = self._search_candidates(
            search_term, rombase_noext, platform, scraper_platform, status_dic)
        if not status_dic['status']: return None

        # --- Add candidate games to the cache ---
        log_debug('MobyGames::get_candidates() Adding to cache "{0}"'.format(cache_key))
        self.cache_candidates[cache_key] = candidate_list

        return candidate_list

    def get_metadata(self, candidate, status_dic):
        # --- If scraper is disabled return immediately and silently ---
        if self.scraper_disabled:
            log_debug('MobyGames::get_metadata() Scraper disabled. Returning empty data.')
            return self._new_gamedata_dic()

        # --- Check if search term is in the cache ---
        cache_key = str(candidate['id'])
        if cache_key in self.cache_metadata:
            log_debug('MobyGames::get_metadata() Cache hit "{0}"'.format(cache_key))
            gamedata = self.cache_metadata[cache_key]
            return gamedata

        # --- Request is not cached. Get candidates and introduce in the cache ---
        log_debug('TheGamesDB::get_metadata() Cache miss "{0}"'.format(cache_key))
        url = 'https://api.mobygames.com/v1/games/{}?api_key={}'.format(candidate['id'], self.api_key)
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('MobyGames_get_metadata.json', json_data)

        # --- Parse game page data ---
        gamedata = self._new_gamedata_dic()
        gamedata['title'] = self._parse_metadata_title(json_data)
        gamedata['year']  = self._parse_metadata_year(json_data, candidate['scraper_platform'])
        gamedata['genre'] = self._parse_metadata_genre(json_data)
        gamedata['plot']  = self._parse_metadata_plot(json_data)

        # --- Put metadata in the cache ---
        log_debug('MobyGames::get_metadata() Adding to cache "{0}"'.format(cache_key))
        self.cache_metadata[cache_key] = gamedata

        return gamedata

    # In the MobyGames scraper is convenient to grab all the available assets for a candidate,
    # cache the assets, and then select the assets of a specific type from the cached list.
    def get_assets(self, candidate, asset_info, status_dic):
        # --- If scraper is disabled return immediately and silently ---
        if self.scraper_disabled:
            log_debug('TheGamesDB::get_assets() Scraper disabled. Returning empty data.')
            return []

        # log_debug('MobyGames::_scraper_get_assets() asset_ID = {0} ...'.format(asset_ID))
        # Get all assets for candidate. _scraper_get_assets_all() caches all assets for a candidate.
        # Then select asset of a particular type.
        all_asset_list = self._scraper_get_assets_all(candidate, status_dic)
        asset_list = [asset_dic for asset_dic in all_asset_list if asset_dic['asset_ID'] == asset_info.id]
        log_debug('MobyGames::_scraper_get_assets() Total assets {0} / Returned assets {1}'.format(
            len(all_asset_list), len(asset_list)))

        return asset_list

    # Mobygames returns both the asset thumbnail URL and the full resolution URL so in
    # this scraper this method is trivial.
    def resolve_asset_URL(self, candidate, status_dic):
        # Transform http to https
        url = candidate['url']
        if url[0:4] == 'http': url = 'https' + url[4:]

        return url

    def resolve_asset_URL_extension(self, image_url, status_dic):
        return text_get_URL_extension(image_url)

    # --- This class own methods -----------------------------------------------------------------
    def debug_get_platforms(self, status_dic):
        log_debug('MobyGames::get_platforms() BEGIN...')
        url_str = 'https://api.mobygames.com/v1/platforms?api_key={}'
        url = url_str.format(self.api_key)
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        self._dump_json_debug('MobyGames_get_platforms.json', json_data)

        return json_data

    # --- Retrieve list of games ---
    def _search_candidates(self, search_term, rombase_noext, platform, scraper_platform, status_dic):
        # --- Retrieve JSON data with list of games ---
        search_string_encoded = urllib.quote_plus(search_term.encode('utf8'))
        url_str = 'https://api.mobygames.com/v1/games?api_key={0}&format=brief&title={1}&platform={2}'
        url = url_str.format(self.api_key, search_string_encoded, scraper_platform)
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('MobyGames_get_candidates.json', json_data)

        # --- Parse game list ---
        games_json = json_data['games']
        candidate_list = []
        for item in games_json:
            title = item['title']
            candidate = self._new_candidate_dic()
            candidate['id'] = item['game_id']
            candidate['display_name'] = title
            candidate['platform'] = platform
            candidate['scraper_platform'] = scraper_platform
            candidate['order'] = 1

            # Increase search score based on our own search.
            if title.lower() == search_term.lower():          candidate['order'] += 2
            if title.lower().find(search_term.lower()) != -1: candidate['order'] += 1
            candidate_list.append(candidate)

        # --- Sort game list based on the score. High scored candidates go first ---
        candidate_list.sort(key = lambda result: result['order'], reverse = True)

        return candidate_list

    def _parse_metadata_title(self, json_data):
        if 'title' in json_data: title_str = json_data['title']
        else:                    title_str = DEFAULT_META_TITLE

        return title_str

    def _parse_metadata_year(self, json_data, scraper_platform):
        platform_data = json_data['platforms']
        if len(platform_data) == 0: return DEFAULT_META_YEAR
        year_data = None
        for platform in platform_data:
            if platform['platform_id'] == int(scraper_platform):
                year_data = platform['first_release_date']
                break
        if year_data is None: year_data = platform_data[0]['first_release_date']

        return year_data[:4]

    def _parse_metadata_genre(self, json_data):
        if 'genres' in json_data:
            genre_names = []
            for genre in json_data['genres']: genre_names.append(genre['genre_name'])
            genre_str = ', '.join(genre_names)
        else:
            genre_str = DEFAULT_META_GENRE

        return genre_str

    def _parse_metadata_plot(self, json_data):
        if 'description' in json_data:
            plot_str = json_data['description']
            plot_str = text_remove_HTML_tags(plot_str) # Clean HTML tags like <i>, </i>
        else:
            plot_str = DEFAULT_META_PLOT

        return plot_str

    # Get ALL available assets for game.
    # Cache the results because this function may be called multiple times for the
    # same candidate game.
    def _scraper_get_assets_all(self, candidate, status_dic):
        cache_key = str(candidate['id'])
        if cache_key in self.all_asset_cache:
            log_debug('MobyGames::_scraper_get_assets_all() Cache hit "{0}"'.format(cache_key))
            asset_list = self.all_asset_cache[cache_key]
        else:
            log_debug('MobyGames::_scraper_get_assets_all() Cache miss "{0}"'.format(cache_key))
            snap_assets = self._load_snap_assets(candidate, candidate['scraper_platform'], status_dic)
            cover_assets = self._load_cover_assets(candidate, candidate['scraper_platform'], status_dic)
            asset_list = snap_assets + cover_assets
            log_debug('A total of {0} assets found for candidate ID {1}'.format(
                len(asset_list), candidate['id']))
            self.all_asset_cache[cache_key] = asset_list

        return asset_list

    def _load_snap_assets(self, candidate, platform_id, status_dic):
        log_debug('MobyGames::_load_snap_assets() Getting Snaps...')
        url = 'https://api.mobygames.com/v1/games/{0}/platforms/{1}/screenshots?api_key={2}'.format(
            candidate['id'], platform_id, self.api_key)
        page_data = self._retrieve_URL_as_JSON(url, status_dic)        
        self._dump_json_debug('MobyGames_snap_assets.json', page_data)

        # --- Parse images page data ---
        asset_list = []
        for image_data in page_data['screenshots']:
            # log_debug('Snap caption "{0}"'.format(image_data['caption']))
            asset_data = self._new_assetdata_dic()
            # In MobyGames typically the Title snaps have the word "Title" in the caption.
            # Search for it
            caption_lower = image_data['caption'].lower()
            if caption_lower.find('title') >= 0:
                asset_data['asset_ID'] = ASSET_TITLE_ID
            else:
                asset_data['asset_ID'] = ASSET_SNAP_ID
            asset_data['display_name'] = image_data['caption']
            asset_data['url_thumb'] = image_data['thumbnail_image']
            # URL is not mandatory here but MobyGames provides it anyway.
            asset_data['url'] = image_data['image']
            if self.verbose_flag:
                log_debug('MobyGames:: Found Snap {0}'.format(asset_data['url_thumb']))
            asset_list.append(asset_data)
        log_debug('Found {0} snap assets for candidate #{1}'.format(len(asset_list), candidate['id']))

        return asset_list

    def _load_cover_assets(self, candidate, platform_id, status_dic):
        log_debug('MobyGames::_load_cover_assets() Getting Covers...')
        url = 'https://api.mobygames.com/v1/games/{0}/platforms/{1}/covers?api_key={2}'.format(
            candidate['id'], platform_id, self.api_key)
        page_data = self._retrieve_URL_as_JSON(url, status_dic)
        self._dump_json_debug('mobygames_cover_assets.txt', page_data)

        if page_data is None:
            return []

        # --- Parse images page data ---
        asset_list = []
        for group_data in page_data['cover_groups']:
            country_names = ' / '.join(group_data['countries'])
            for image_data in group_data['covers']:
                asset_name = '{0} - {1} ({2})'.format(
                    image_data['scan_of'], image_data['description'], country_names)
                if image_data['scan_of'].lower() in MobyGames.asset_name_mapping:
                    asset_ID = MobyGames.asset_name_mapping[image_data['scan_of'].lower()]
                else:
                    log_warning('Scan type "{}" not implemented yet.'.format(image_data['scan_of']))

                # url_thumb is mandatory.
                # url is not mandatory here but MobyGames provides it anyway.
                asset_data = self._new_assetdata_dic()
                asset_data['asset_ID'] = asset_ID
                asset_data['display_name'] = asset_name
                asset_data['url_thumb'] = image_data['thumbnail_image']
                asset_data['url'] = image_data['image']
                if self.verbose_flag:
                    log_debug('MobyGames:: Found Cover {0}'.format(asset_data['url_thumb']))
                asset_list.append(asset_data)
        log_debug('Found {0} cover assets for candidate #{1}'.format(len(asset_list), candidate['id']))

        return asset_list

    # MobyGames URLs have the API developer id and password.
    # Clean URLs for safe logging.
    def _clean_URL_for_log(self, url):
        clean_url = url
        clean_url = re.sub('api_key=[^&]*&', 'api_key=***&', clean_url)
        clean_url = re.sub('api_key=[^&]*$', 'api_key=***', clean_url)
        # log_variable('url', url)
        # log_variable('clean_url', clean_url)

        return clean_url

    # Retrieve URL and decode JSON object.
    def _retrieve_URL_as_JSON(self, url, status_dic, retry=0):
        self._wait_for_API_request()
        # If the MobyGames API key is wrong or empty string, MobyGames will reply with an 
        # "HTTP Error 401: UNAUTHORIZED" response which is an IOError expection in net_get_URL().
        # Generally, if a JSON object cannot be decoded some error happened in net_get_URL().
        page_data_raw, http_code = net_get_URL(url, self._clean_URL_for_log(url))
        self.last_http_call = datetime.now()
        if page_data_raw is None:
            if http_code == 429 and retry < Scraper.RETRY_THRESHOLD:
                # 360 per hour limit, wait at least 16 minutes
                wait_till_time = datetime.now() + timedelta(seconds=960)
                kodi_dialog_OK('You\'ve exceeded the max rate limit of 360 requests/hour.',
                                'Respect the website and wait at least till {}.'.format(wait_till_time))
                # waited long enough? Try again
                if (datetime.now() - wait_till_time).total_seconds() > 1:
                    return self._retrieve_URL_as_JSON(url, status_dic, retry+1)
                            
            self._handle_error(status_dic, 'MobyGames: Network error in net_get_URL()')
            return None
        try:
            json_data = json.loads(page_data_raw)
        except Exception as ex:
            self._handle_exception(ex, status_dic, 'Error decoding JSON data from MobyGames.')
            return None

        return json_data

    # From xxxxx
    # 
    def _wait_for_API_request(self):
        # Make sure we dont go over the TooManyRequests limit of 1 second.
        now = datetime.now()
        if (now - self.last_http_call).total_seconds() < 1:
            log_debug('MobyGames::_wait_for_API_request() Sleeping 1 second to avoid overloading...')
            time.sleep(1)
            
# ------------------------------------------------------------------------------------------------
# ScreenScraper online scraper.
#
# | Site        | https://www.screenscraper.fr             |
# | API V1 docs | https://www.screenscraper.fr/webapi.php  |
# | API V2 docs | |
#
# Some API functions can be called to test, for example:
# https://www.screenscraper.fr/api/genresListe.php?devid=xxx&devpassword=yyy&softname=zzz&output=xml
# https://www.screenscraper.fr/api/regionsListe.php?devid=xxx&devpassword=yyy&softname=zzz&output=xml
# https://www.screenscraper.fr/api/systemesListe.php?devid=xxx&devpassword=yyy&softname=zzz&output=xml
#
# https://www.screenscraper.fr/api/mediaSysteme.php?devid=xxx&devpassword=yyy&softname=zzz&ssid=test&sspassword=test&crc=&md5=&sha1=&systemeid=1&media=wheel(wor)
# https://www.screenscraper.fr/api/mediaVideoSysteme.php?devid=xxx&devpassword=yyy&softname=zzz&ssid=test&sspassword=test&crc=&md5=&sha1=&systemeid=1&media=video
#
# https://www.screenscraper.fr/api/jeuInfos.php?
#     devid=xxx&devpassword=yyy&softname=zzz&output=xml
#     &ssid=test&sspassword=test
#     &systemeid=1
#     &romtype=rom
#     &crc=50ABC90A
#     &romnom=Sonic%20The%20Hedgehog%202%20(World).zip
#     &romtaille=749652
#
# https://www.screenscraper.fr/api/mediaJeu.php?devid=xxx&devpassword=yyy&softname=zzz&ssid=test&sspassword=test&crc=&md5=&sha1=&systemeid=1&jeuid=3&media=wheel-hd(wor)
# https://www.screenscraper.fr/api/mediaVideoJeu.php?devid=xxx&devpassword=yyy&softname=zzz&ssid=test&sspassword=test&crc=&md5=&sha1=&systemeid=1&jeuid=3&media=video
# ------------------------------------------------------------------------------------------------
class ScreenScraper_V1(Scraper):
    # --- Class variables ------------------------------------------------------------------------
    supported_metadata_list = [
        META_TITLE_ID,
        META_YEAR_ID,
        META_GENRE_ID,
        META_DEVELOPER_ID,
        META_NPLAYERS_ID,
        META_ESRB_ID,
        META_PLOT_ID,
    ]
    supported_asset_list = [
        ASSET_FANART_ID,
        ASSET_CLEARLOGO_ID,
        ASSET_TRAILER_ID,
        ASSET_TITLE_ID,
        ASSET_SNAP_ID,
        ASSET_BOXFRONT_ID,
        ASSET_BOXBACK_ID,
        ASSET_3DBOX_ID,
        ASSET_CARTRIDGE_ID,
        ASSET_MAP_ID,
        ASSET_MANUAL_ID,
    ]

    # List of country/region suffixes supported by ScreenScraper.
    # Get list with https://www.screenscraper.fr/api/regionsListe.php?devid=xxx&devpassword=yyy&softname=zzz&output=xml&ssid=test&sspassword=test
    # Items at the beginning will be searched first.
    # Creation of this must be automatised with some script...
    region_list = [
        '_wor', # World
        '_eu',  # Europe
        '_us',  # USA
        '_ame', # America
        '_oce', # Oceania
        '_jp',  # Japan
        '_asi', # Asia
        '_de',  # Germany
        '_au',  # Australia
        '_br',  # Brazil
        '_bg',  # Bulgarie
        '_ca',  # Canada
        '_cl',  # Chile
        '_kr',  # Korea
        '_dk',  # Denmark
        '_sp',  # Spain
        '_fi',  # Finland
        '_fr',  # France
        '_gr',  # Greece
        '_uk',  # United Kingdom
        '_cus', # Custom
        '_ss',  # ScreenScraper
        '',     # Empty string. Use as a last resource.
    ]

    # --- Constructor ----------------------------------------------------------------------------
    def __init__(self, settings):
        # --- This scraper settings ---
        self.dev_id     = 'V2ludGVybXV0ZTAxMTA='
        self.dev_pass   = 'VDlwU3J6akZCbWZRbWM4Yg=='
        self.softname   = settings['scraper_screenscraper_AEL_softname']
        self.ssid       = settings['scraper_screenscraper_ssid']
        self.sspassword = settings['scraper_screenscraper_sspass']

        # --- Internal stuff ---
        # Cache all data returned by jeuInfos.php
        self.cache_jeuInfos = {}

        # --- Pass down common scraper settings ---
        super(ScreenScraper_V1, self).__init__(settings)

    # --- Base class abstract methods ------------------------------------------------------------
    def get_name(self): return 'ScreenScraper'

    def supports_metadata_ID(self, metadata_ID):
        return True if asset_ID in ScreenScraper_V1.supported_metadata_list else False

    def supports_metadata(self): return True

    def supports_asset_ID(self, asset_ID):
        return True if asset_ID in ScreenScraper_V1.supported_asset_list else False

    def supports_assets(self): return True

    # ScreenScraper user login/password is mandatory. Actually, SS seems to work if no user
    # login/password is given, however it seems that the number of API requests is very
    # limited.
    def check_before_scraping(self, status_dic):
        if self.ssid and self.sspassword:
            log_debug('ScreenScraper_V1::check_before_scraping() ScreenScraper user name and pass OK.')
            return
        log_error('ScreenScraper_V1::check_before_scraping() ScreenScraper user name and/or pass not configured.')
        log_error('ScreenScraper_V1::check_before_scraping() Disabling ScreenScraper scraper.')
        self.scraper_deactivated = True
        status_dic['status'] = False
        status_dic['dialog'] = KODI_MESSAGE_DIALOG
        status_dic['msg'] = (
            'AEL requires your ScreenScraper user name and password. '
            'Create a user account in https://www.screenscraper.fr/ '
            'and set you user name and password in AEL addon settings.'
        )

    def get_candidates(self, search_term, rombase_noext, platform, status_dic):
        scraper_platform = AEL_platform_to_ScreenScraper(platform)
        log_debug('ScreenScraper_V1::get_candidates() search_term   "{0}"'.format(search_term))
        log_debug('ScreenScraper_V1::get_candidates() rombase_noext "{0}"'.format(rombase_noext))
        log_debug('ScreenScraper_V1::get_candidates() AEL platform  "{0}"'.format(platform))
        log_debug('ScreenScraper_V1::get_candidates() SS platform   "{0}"'.format(scraper_platform))

        # --- Get scraping data and cache it ---
        # ScreenScraper jeuInfos.php returns absolutely everything about a single ROM, including
        # metadata, artwork, etc. jeuInfos.php returns one game or nothing at all.
        # The data returned by jeuInfos.php must be cached in this object for every request done.
        # ScreenScraper returns only one game or nothing at all.
        cache_str = search_term + '__' + rombase_noext + '__' + scraper_platform
        if cache_str in self.cache_jeuInfos:
            log_debug('ScreenScraper_V1::get_candidates() Cache hit "{0}"'.format(cache_str))
            gameInfos_dic = self.cache_jeuInfos[cache_str]
        else:
            log_debug('ScreenScraper_V1::get_candidates() Cache miss "{0}"'.format(cache_str))
            gameInfos_dic = self._get_gameInfos(search_term, rombase_noext, scraper_platform)
            self.cache_jeuInfos[cache_str] = gameInfos_dic

        # --- Deal with errors returned by api/jeuInfos.php ---
        # If the JSON could not be decoded gameInfos_dic is an empty dictionary.
        # Do not forget to reset the cache to clear the empty dictionary from the cache.
        jeu_dic = gameInfos_dic['response']['jeu']
        log_debug('Game "{}" (ID {}, ROMID {})'.format(jeu_dic['nom'], jeu_dic['id'], jeu_dic['romid']))
        log_debug('Num ROMs {}'.format(len(jeu_dic['roms'])))

        # --- Build candidate_list from ScreenScraper gameInfos_dic returned by jeuInfos.php ---
        candidate = self._new_candidate_dic()
        candidate['id'] = jeu_dic['id']
        candidate['display_name'] = jeu_dic['nom']
        candidate['platform'] = platform
        candidate['scraper_platform'] = scraper_platform
        candidate['order'] = 1
        candidate['cache_str'] = cache_str # Special field to retrieve game from cache.

        # Always return a list, even if only with 1 element.
        return [ candidate ]

    def get_metadata(self, candidate, status_dic):
        # --- Retrieve gameInfos_dic from cache ---
        log_debug('ScreenScraper_V1::_scraper_get_metadata() Cache retrieving "{}"'.format(candidate['cache_str']))
        gameInfos_dic = self.cache_jeuInfos[candidate['cache_str']]
        jeu_dic = gameInfos_dic['response']['jeu']

        # --- Parse game metadata ---
        gamedata = self._new_gamedata_dic()
        gamedata['title']     = self._parse_meta_title(jeu_dic)
        gamedata['year']      = self._parse_meta_year(jeu_dic)
        gamedata['genre']     = self._parse_meta_genre(jeu_dic)
        gamedata['developer'] = self._parse_meta_developer(jeu_dic)
        gamedata['nplayers']  = self._parse_meta_nplayers(jeu_dic)
        gamedata['esrb']      = self._parse_meta_esrb(jeu_dic)
        gamedata['plot']      = self._parse_meta_plot(jeu_dic)

        return gamedata

    def get_assets(self, candidate, asset_info, status_dic):
        # --- Retrieve gameInfos_dic from cache ---
        log_debug('ScreenScraper_V1::_scraper_get_assets() Cache retrieving "{}"'.format(candidate['cache_str']))
        gameInfos_dic = self.cache_jeuInfos[candidate['cache_str']]
        jeu_dic = gameInfos_dic['response']['jeu']

        # --- Parse game assets ---
        all_asset_list = self._get_assets_all(jeu_dic)
        asset_list = [asset_dic for asset_dic in all_asset_list if asset_dic['asset_ID'] == asset_info.id]
        log_debug('ScreenScraper_V1::_scraper_get_assets() Total assets {0} / Returned assets {1}'.format(
            len(all_asset_list), len(asset_list)))

        return asset_list

    def resolve_asset_URL(self, candidate, status_dic): return candidate['url']

    def resolve_asset_URL_extension(self, image_url, status_dic):
        o = urlparse(image_url)
        url_args = parse_qs(o.query)
        # log_debug(unicode(o))
        # log_debug(unicode(url_args))
        image_ext = url_args['mediaformat'][0] if 'mediaformat' in url_args else ''

        return '.' + image_ext

    # --- This class own methods -----------------------------------------------------------------
    # Plumbing function to get the cached raw game dictionary returned by ScreenScraper.
    # Scraper::get_candiates() must be called before this function to fill the cache.
    def get_gameInfos_dic(self, candidate):
        log_debug('ScreenScraper_V1::get_gameInfos_dic() Cache retrieving "{}"'.format(candidate['cache_str']))
        gameInfos_dic = self.cache_jeuInfos[candidate['cache_str']]

        return gameInfos_dic

    def get_user_info(self, status_dic):
        log_debug('ScreenScraper_V1::get_ROM_types() BEGIN...')
        url_a = 'https://www.screenscraper.fr/api/ssuserInfos.php'
        url_b = '?devid={}&devpassword={}&softname={}&output=json'
        url_c = '&ssid={}&sspassword={}'
        url = url_a + \
            url_b.format(base64.b64decode(self.dev_id), base64.b64decode(self.dev_pass), self.softname) + \
            url_c.format(self.ssid, self.sspassword)
        page_raw_data = net_get_URL(url)
        log_debug(unicode(page_raw_data))
        json_data = json.loads(page_raw_data)
        self._dump_json_debug('ScreenScraper_get_user_info.json', json_data)

        return json_data

    # Some functions to grab data from ScreenScraper.
    def get_ROM_types(self):
        log_debug('ScreenScraper_V1::get_ROM_types() BEGIN...')
        url_str = 'https://www.screenscraper.fr/api/romTypesListe.php?devid={}&devpassword={}&softname={}&output=json'
        url = url_str.format(base64.b64decode(self.dev_id), base64.b64decode(self.dev_pass), self.softname)
        page_raw_data = net_get_URL(url)
        log_debug(unicode(page_raw_data))
        json_data = json.loads(page_raw_data)
        self._dump_json_debug('ScreenScraper_get_ROM_types.txt', json_data)

        return json_data

    def get_genres_list(self):
        log_debug('ScreenScraper_V1::get_genres_list() BEGIN...')
        url_str = 'https://www.screenscraper.fr/api/genresListe.php?devid={}&devpassword={}&softname={}&output=json'
        url = url_str.format(base64.b64decode(self.dev_id), base64.b64decode(self.dev_pass), self.softname)
        page_raw_data = net_get_URL(url)
        # log_debug(unicode(page_raw_data))
        page_data = json.loads(page_raw_data)
        self._dump_json_debug('ScreenScraper_get_genres_list.txt', page_data)

        return page_data

    def get_regions_list(self):
        log_debug('ScreenScraper_V1::get_regions_list() BEGIN...')
        url_str = 'https://www.screenscraper.fr/api/regionsListe.php?devid={}&devpassword={}&softname={}&output=json'
        url = url_str.format(base64.b64decode(self.dev_id), base64.b64decode(self.dev_pass), self.softname)
        page_raw_data = net_get_URL(url)
        # log_debug(unicode(page_raw_data))
        page_data = json.loads(page_raw_data)
        self._dump_json_debug('ScreenScraper_get_regions_list.txt', page_data)

        return page_data

    # Call to ScreenScraper jeuInfos.php
    def _get_gameInfos(self, search_term, rombase_noext, scraper_platform):
        # --- Test data ---
        # Example from ScreenScraper API info page.
        # crc=50ABC90A&systemeid=1&romtype=rom&romnom=Sonic%20The%20Hedgehog%202%20(World).zip&romtaille=749652
        # NOTE that if the CRC is all zeros and the filesize also 0 it seems to work.
        # Also, if no file extension is passed it seems to work. Looks like SS is capable of
        # fuzzy searches.
        # ssid = 
        # sspassword = 
        # system_id = 1
        # rom_type = 'rom'
        # crc_str = '50ABC90A'
        # rom_name = urllib.quote('Sonic The Hedgehog 2 (World).zip')
        # rom_size = 749652

        # --- Actual data for scraping in AEL ---
        system_id = scraper_platform
        rom_type = 'rom'
        crc_str = '00000000'
        rom_name = urllib.quote(rombase_noext)
        rom_size = 0
        log_debug('ScreenScraper_V1::_get_gameInfos() ssid       "{0}"'.format(self.ssid))
        # log_debug('ScreenScraper_V1::_get_gameInfos() ssid       "{0}"'.format('***'))
        # log_debug('ScreenScraper_V1::_get_gameInfos() sspassword "{0}"'.format(self.sspassword))
        log_debug('ScreenScraper_V1::_get_gameInfos() sspassword "{0}"'.format('***'))
        log_debug('ScreenScraper_V1::_get_gameInfos() system_id  "{0}"'.format(system_id))
        log_debug('ScreenScraper_V1::_get_gameInfos() rom_type   "{0}"'.format(rom_type))
        log_debug('ScreenScraper_V1::_get_gameInfos() crc_str    "{0}"'.format(crc_str))
        log_debug('ScreenScraper_V1::_get_gameInfos() rom_name   "{0}"'.format(rom_name))
        log_debug('ScreenScraper_V1::_get_gameInfos() rom_size   "{0}"'.format(rom_size))

        # --- Build URL ---
        # It is more convenient to dump XML files for development.
        # For regular scraping JSON is more efficient.
        url_a = 'https://www.screenscraper.fr/api/jeuInfos.php?'
        url_b = 'devid={}&devpassword={}&softname={}&output=json'.format(
            base64.b64decode(self.dev_id), base64.b64decode(self.dev_pass), self.softname)
        url_c = '&ssid={}&sspassword={}&systemeid={}&romtype={}'.format(
            self.ssid, self.sspassword, system_id, rom_type)
        url_d = '&crc={}&romnom={}&romtaille={}'.format(crc_str, rom_name, rom_size)
        url = url_a + url_b + url_c + url_d

        # --- Grab and parse URL data ---
        page_raw_data = net_get_URL(url, self._clean_URL_for_log(url))
        try:
            gameInfos_dic = json.loads(page_raw_data)
        except Exception as ex:
            log_error('(Exception) In ScreenScraper_V1::_get_gameInfos()')
            log_error('(Exception) Object type "{}"'.format(type(ex)))
            log_error('(Exception) Message "{}"'.format(str(ex)))
            log_error('Problem in json.loads(url). Returning empty list of candidate games.')
            gameInfos_dic = page_raw_data
        self._dump_json_debug('ScreenScraper_get_gameInfo.json', gameInfos_dic)

        return gameInfos_dic

    def _parse_meta_title(self, jeu_dic):
        # First search for regional name.
        for region in ScreenScraper_V1.region_list:
            key = 'nom' + region
            if key in jeu_dic['noms']: return jeu_dic['noms'][key]

        # Default name
        if 'nom' in jeu_dic: return jeu_dic['nom']

        return ''

    def _parse_meta_year(self, jeu_dic):
        # Search regional dates. Only return year (first 4 characters)
        for region in ScreenScraper_V1.region_list:
            key = 'date' + region
            if key in jeu_dic['dates']: return jeu_dic['dates'][key][0:4]

        return ''

    def _parse_meta_genre(self, jeu_dic):
        # Only the first gender in the list is supported now.
        for region in ScreenScraper_V1.region_list:
            key = 'genres' + region
            if key in jeu_dic['genres']: return jeu_dic['genres'][key][0]

        return ''

    def _parse_meta_developer(self, jeu_dic):
        if 'developpeur' in jeu_dic: return jeu_dic['developpeur']

        return ''

    def _parse_meta_nplayers(self, jeu_dic):
        if 'joueurs' in jeu_dic: return jeu_dic['joueurs']

        return ''

    def _parse_meta_esrb(self, jeu_dic):
        if 'classifications' in jeu_dic and 'ESRB' in jeu_dic['classifications']:
            return jeu_dic['classifications']['ESRB']

        return ''

    def _parse_meta_plot(self, jeu_dic):
        for region in ScreenScraper_V1.region_list:
            key = 'synopsis' + region
            if key in jeu_dic['synopsis']: return jeu_dic['synopsis'][key]

        return ''

    # Returns all assets found in the jeu_dic dictionary.
    def _get_assets_all(self, jeu_dic):
        all_asset_list = []
        medias_dic = jeu_dic['medias']

        # --- Fanart ---
        asset_data = self._get_asset_simple(medias_dic, ASSET_FANART_ID, 'Fanart', 'media_fanart')
        if asset_data is not None: all_asset_list.append(asset_data)

        # --- Clearlogos are called Wheels in ScreenScraper ---
        # SS supports Normal, Carbon and Steel Wheels.
        # media_wheels, media_wheelscarbon, media_wheelssteel
        asset_data = self._get_asset_anidated(
            medias_dic, ASSET_CLEARLOGO_ID, 'Clearlogo (Normal wheel)', 'media_wheels', 'media_wheel')
        if asset_data is not None: all_asset_list.append(asset_data)

        # --- Trailer (media_video) ---

        # --- SS seems to support only one Title screenshot ---
        asset_data = self._get_asset_simple(
            medias_dic, ASSET_TITLE_ID, 'Title screenshot', 'media_screenshottitle')
        if asset_data is not None: all_asset_list.append(asset_data)

        # --- SS seems to support only one Snap screenshot ---
        asset_data = self._get_asset_simple(
            medias_dic, ASSET_SNAP_ID, 'Snap screenshot', 'media_screenshot')
        if asset_data is not None: all_asset_list.append(asset_data)

        if 'media_boxs' in medias_dic:
            boxs_dic = medias_dic['media_boxs']
            # --- Boxfront ---
            asset_data = self._get_asset_anidated(
                boxs_dic, ASSET_BOXFRONT_ID, 'BoxFront', 'media_boxs2d', 'media_box2d')
            if asset_data is not None: all_asset_list.append(asset_data)

            # --- Boxback ---
            asset_data = self._get_asset_anidated(
                boxs_dic, ASSET_BOXBACK_ID, 'BoxBack', 'media_boxs2d-back', 'media_box2d-back')
            if asset_data is not None: all_asset_list.append(asset_data)

            # Spine (not supported by AEL at the moment)

            # --- 3D box ---
            asset_data = self._get_asset_anidated(
                boxs_dic, ASSET_3DBOX_ID, '3D Box', 'media_boxs3d', 'media_box3d')
            if asset_data is not None: all_asset_list.append(asset_data)

            # --- Box texture (not supported by AEL at the moment) ---

        # Cartridge are called Supports in SS.
        if 'media_supports' in medias_dic:
            supports_dic = medias_dic['media_supports']
            # Boxfront
            asset_data = self._get_asset_anidated(
                supports_dic, ASSET_CARTRIDGE_ID, 'Cartridge', 'media_supports2d', 'media_support2d')
            if asset_data is not None: all_asset_list.append(asset_data)

        # Maps ()

        # Manuals (media_manuels)

        return all_asset_list

    # Search for regional assets.
    # If asset cannot be found then return None.
    # Now, this function only returns the first regional asset found. Would not be interesting
    # to return ALL the regional assets so the user chooses.
    def _get_asset_simple(self, data_dic, asset_ID, title_str, key):
        for region_str in ScreenScraper_V1.region_list:
            region_key = key + region_str
            if region_key in data_dic:
                asset_data = self._new_assetdata_dic()
                asset_data['asset_ID'] = asset_ID
                asset_data['display_name'] = title_str + ' ' + region_str
                asset_data['url_thumb'] = data_dic[region_key]
                asset_data['url'] = data_dic[region_key]
                return asset_data

        return None

    def _get_asset_anidated(self, data_dic, asset_ID, title_str, key, subkey):
        for region_str in ScreenScraper_V1.region_list:
            region_subkey = subkey + region_str
            if region_subkey in data_dic[key]:
                asset_data = self._new_assetdata_dic()
                asset_data['asset_ID'] = asset_ID
                asset_data['display_name'] = title_str + ' ' + region_str
                asset_data['url_thumb'] = data_dic[key][region_subkey]
                asset_data['url'] = data_dic[key][region_subkey]
                return asset_data

        return None

    # ScreenScraper URLs have the developer password and the user password.
    # Clean URLs for safe logging.
    #
    # https://docs.python.org/2/library/urlparse.html
    # Note: The urlparse module is renamed to urllib.parse in Python 3. The 2to3 tool will
    # automatically adapt imports when converting your sources to Python 3. 
    def _clean_URL_for_log(self, url):
        # This is too complicated and the order of the parameters in the query is changed.
        # o = urlparse.urlparse(url)
        # log_variable('o', o)
        # query_dic = urlparse.parse_qs(o.query)
        # query_dic['devpassword'] = 'ooo'
        # query_dic['sspassword'] = 'ooo'
        # query_qs = urllib.urlencode(query_dic)
        # clean_url = urlparse.urlunparse((o.scheme, o.netloc, o.path, o.params, query_qs, o.fragment))
        # log_variable('clean_url', clean_url)

        # --- Keep things simple! ---
        clean_url = url
        clean_url = re.sub('devid=[^&]*&', 'devid=***&', clean_url)
        clean_url = re.sub('devpassword=[^&]*&', 'devpassword=***&', clean_url)
        clean_url = re.sub('ssid=[^&]*&', 'ssid=***&', clean_url)
        clean_url = re.sub('sspassword=[^&]*&', 'sspassword=***&', clean_url)
        # log_variable('url', url)
        # log_variable('clean_url', clean_url)

        return clean_url

# ------------------------------------------------------------------------------------------------
# ScreenScraper online scraper.
# Uses version 2 of the API.
#
# | Site     | https://www.screenscraper.fr             |
# | API info | complete                                 |
# ------------------------------------------------------------------------------------------------
class ScreenScraper_v2(Scraper):
    pass

# ------------------------------------------------------------------------------------------------
# GameFAQs online scraper.
#
# | Site     | https://gamefaqs.gamespot.com/ |
# | API info | GameFAQs has no API            |
# ------------------------------------------------------------------------------------------------
class GameFAQs(Scraper):
    # --- Class variables ------------------------------------------------------------------------
    supported_metadata_list = [
        META_TITLE_ID,
        META_YEAR_ID,
        META_GENRE_ID,
        META_DEVELOPER_ID,
        META_PLOT_ID,
    ]
    supported_asset_list = [
        ASSET_TITLE_ID,
        ASSET_SNAP_ID,
        ASSET_BOXFRONT_ID,
        ASSET_BOXBACK_ID,
    ]

    # --- Constructor ----------------------------------------------------------------------------
    def __init__(self, settings):
        # --- This scraper settings ---
        
        # --- Internal stuff ---
        self.all_asset_cache = {}

        # --- Pass down common scraper settings ---
        super(GameFAQs, self).__init__(settings)

    # --- Base class abstract methods ------------------------------------------------------------
    def get_name(self): return 'GameFAQs'
        
    def supports_metadata_ID(self, metadata_ID):
        return True if metadata_ID in GameFAQs.supported_metadata_list else False

    def supports_metadata(self): return True

    def supports_asset_ID(self, asset_ID):
        return True if asset_ID in GameFAQs.supported_asset_list else False

    def supports_assets(self): return True
    
    # GameFAQs does not require any API keys. By default status_dic is configured for successful
    # operation so return it as it is.
    def check_before_scraping(self, status_dic): return status_dic

    def get_candidates(self, search_term, rombase_noext, platform, status_dic):
        scraper_platform = AEL_platform_to_GameFAQs(platform)
        log_debug('GameFAQs::get_candidates() search_term      "{0}"'.format(search_term))
        log_debug('GameFAQs::get_candidates() rombase_noext    "{0}"'.format(rombase_noext))
        log_debug('GameFAQs::get_candidates() platform         "{0}"'.format(platform))
        log_debug('GameFAQs::get_candidates() scraper_platform "{0}"'.format(scraper_platform))

        # Order list based on score
        game_list = self._get_candidates_from_page(search_term, platform, scraper_platform)
        game_list.sort(key = lambda result: result['order'], reverse = True)

        return game_list

    # --- Example URLs ---
    # https://gamefaqs.gamespot.com/snes/519824-super-mario-world
    def get_metadata(self, candidate, status_dic):
        # --- Grab game information page ---
        log_debug('GameFAQs::_scraper_get_metadata() Get metadata from {}'.format(candidate['id']))
        url = 'https://gamefaqs.gamespot.com{}'.format(candidate['id'])
        page_data = net_get_URL(url)
        self._dump_file_debug('GameFAQs_get_metadata.html', page_data)

        # --- Parse data ---
        game_year      = self._parse_year(page_data)
        game_genre     = self._parse_genre(page_data)
        game_developer = self._parse_developer(page_data)
        game_plot      = self._parse_plot(page_data)

        # --- Build metadata dictionary ---
        game_data = self._new_gamedata_dic()
        game_data['title']     = candidate['game_name']
        game_data['year']      = game_year
        game_data['genre']     = game_genre
        game_data['developer'] = game_developer
        game_data['nplayers']  = ''
        game_data['esrb']      = ''
        game_data['plot']      = game_plot

        return game_data

    def get_assets(self, candidate, asset_info, status_dic):
        # log_debug('GameFAQs::_scraper_get_assets() asset_ID = {0} ...'.format(asset_ID))
        # Get all assets for candidate. _scraper_get_assets_all() caches all assets for a candidate.
        # Then select asset of a particular type.
        all_asset_list = self._scraper_get_assets_all(candidate, status_dic)
        asset_list = [asset_dic for asset_dic in all_asset_list if asset_dic['asset_ID'] == asset_info.id]
        log_debug('GameFAQs::_scraper_get_assets() Total assets {0} / Returned assets {1}'.format(
            len(all_asset_list), len(asset_list)))

        return asset_list

    # In GameFAQs the candidate['url'] field is the URL of the image page.
    # For screenshots, the image page contains one image (the screenshot).
    # For boxart, the image page contains boxfront, boxback and spine.
    #
    # Boxart examples:
    # https://gamefaqs.gamespot.com/snes/519824-super-mario-world/images/158851
    # https://gamefaqs.gamespot.com/snes/588741-super-metroid/images/149897
    #
    # Screenshot examples:
    # https://gamefaqs.gamespot.com/snes/519824-super-mario-world/images/21
    # https://gamefaqs.gamespot.com/snes/519824-super-mario-world/images/29
    def resolve_asset_URL(self, candidate, status_dic):
        url = 'https://gamefaqs.gamespot.com{}'.format(candidate['url'])
        log_debug('GameFAQs::_scraper_resolve_asset_URL() Get image from "{}" for asset type {}'.format(
            url, asset_info.name))
        page_data = net_get_URL(url)
        self._dump_json_debug('GameFAQs_scraper_resolve_asset_URL.html', page_data)

        r_str = '<img (class="full_boxshot cte" )?data-img-width="\d+" data-img-height="\d+" data-img="(?P<url>.+?)" (class="full_boxshot cte" )?src=".+?" alt="(?P<alt>.+?)"(\s/)?>'
        images_on_page = re.finditer(r_str, page_data)
        for image_data in images_on_page:
            image_on_page = image_data.groupdict()
            image_asset_ids = self._parse_asset_type(image_on_page['alt'])
            log_verb('Found "{}" of types {} with url {}'.format(image_on_page['alt'], image_asset_ids, image_on_page['url']))
            if asset_info.id in image_asset_ids:
                log_debug('GameFAQs::_scraper_resolve_asset_URL() Found match {}'.format(image_on_page['alt']))
                return image_on_page['url']
        log_debug('GameFAQs::_scraper_resolve_asset_URL() No correct match')

        return ''

    # NOT IMPLEMENTED YET.
    def resolve_asset_URL_extension(self, image_url, status_dic): return None

    # --- This class own methods -----------------------------------------------------------------
    def _parse_asset_type(self, header):
        if 'Screenshots' in header: return [ASSET_SNAP_ID, ASSET_TITLE_ID]
        elif 'Box Back' in header:  return [ASSET_BOXBACK_ID]
        elif 'Box Front' in header: return [ASSET_BOXFRONT_ID]
        elif 'Box' in header:       return [ASSET_BOXFRONT_ID, ASSET_BOXBACK_ID]

        return [ASSET_SNAP_ID]

    # Deactivate the recursive search with no platform if no games found with platform.
    # Could be added later.
    def _get_candidates_from_page(self, search_term, platform, scraper_platform, url = None):
        # --- Get URL data as a text string ---
        if url is None:
            url = 'https://gamefaqs.gamespot.com/search_advanced'
            data = urllib.urlencode({'game': search_term, 'platform': scraper_platform})
            page_data = net_post_URL(url, data)
        else:
            page_data = net_get_URL(url)
        self._dump_file_debug('GameFAQs_get_candidates.html', page_data)

        # --- Parse game list ---
        # --- First row ---
        # <div class="sr_cell sr_platform">Platform</div>
        # <div class="sr_cell sr_title">Game</div>
        # <div class="sr_cell sr_release">Release</div>
        #
        # --- Game row ---
        # <div class="sr_cell sr_platform">SNES</div>
        # <div class="sr_cell sr_title"><a class="log_search" data-row="1" data-col="1" data-pid="519824" href="/snes/519824-super-mario-world">Super Mario World</a></div>
        # <div class="sr_cell sr_release">1990</div>
        r = r'<div class="sr_cell sr_platform">(.*?)</div>\s*<div class="sr_cell sr_title"><a class="log_search" data-row="[0-9]+" data-col="1" data-pid="[0-9]+" href="(.*?)">(.*?)</a></div>'
        regex_results = re.findall(r, page_data, re.MULTILINE)
        game_list = []
        for result in regex_results:
            game = self._new_candidate_dic()
            game_platform = result[0]
            game_id       = result[1]
            game_name     = text_unescape_HTML(result[2])
            game['id']               = result[1]
            game['display_name']     = game_name + ' / ' + game_platform.capitalize()
            game['platform']         = platform
            game['scraper_platform'] = scraper_platform
            game['order']            = 1
            game['game_name']        = game_name # Additional GameFAQs scraper field
            # Skip first row of the games table.
            if game_name == 'Game': continue
            # Increase search score based on our own search.
            # In the future use an scoring algortihm based on Levenshtein distance.
            title = game_name
            if title.lower() == search_term.lower():          game['order'] += 1
            if title.lower().find(search_term.lower()) != -1: game['order'] += 1
            if platform > 0 and game_platform == platform:    game['order'] += 1
            game_list.append(game)

        # --- Recursively load more games ---
        # Deactivate for now, just get all the games on the first page which should be
        # more than enough.
        # next_page_result = re.findall('<li><a href="(\S*?)">Next Page\s<i', page_data, re.MULTILINE)
        # if len(next_page_result) > 0:
        #     link = next_page_result[0].replace('&amp;', '&')
        #     new_url = 'https://gamefaqs.gamespot.com' + link
        #     game_list = game_list + self._get_candidates_from_page(search_term, no_platform, new_url)

        # --- Sort game list based on the score ---
        game_list.sort(key = lambda result: result['order'], reverse = True)
        
        return game_list
              
    #
    # Functions to parse metadata from game web page.
    #
    def _parse_year(self, page_data):
        # <li><b>Release:</b> <a href="/snes/519824-super-mario-world/data">August 13, 1991</a></li>
        # <li><b>Release:</b> <a href="/snes/588699-street-fighter-alpha-2/data">November 1996</a></li>
        re_str = '<li><b>Release:</b> <a href=".*?">(.*?)</a></li>'
        m_date = re.search(re_str, page_data)
        game_year = ''
        if m_date:
            # Matches the year in the date string.
            date_str = m_date.group(1)
            m_year = re.search('\d\d\d\d', date_str)
            if m_year: game_year = m_year.group(0)

        return game_year
    
    def _parse_genre(self, page_data):
        # Parse only the first genre. Later versions will parse all the genres and return a list.
        # <li><b>Genre:</b> <a href="/snes/category/163-action-adventure">Action Adventure</a> &raquo; <a href="/snes/category/292-action-adventure-open-world">Open-World</a>
        m_genre = re.search('<li><b>Genre:</b> <a href=".*?">(.*?)</a>', page_data)
        if m_genre: game_genre = m_genre.group(1)

        return game_genre

    def _parse_developer(self, page_data):
        # --- Developer and publisher are the same
        # <li><b>Developer/Publisher: </b><a href="/company/2324-capcom">Capcom</a></li>
        # --- Developer and publisher separated
        # <li><b>Developer:</b> <a href="/company/45872-intelligent-systems">Intelligent Systems</a></li>
        # <li><b>Publisher:</b> <a href="/company/1143-nintendo">Nintendo</a></li>
        m_dev_a = re.search('<li><b>Developer/Publisher: </b><a href=".*?">(.*?)</a></li>', page_data)
        m_dev_b = re.search('<li><b>Developer: </b><a href=".*?">(.*?)</a></li>', page_data)
        if   m_dev_a: game_developer = m_dev_a.group(1)
        elif m_dev_b: game_developer = m_dev_b.group(1)
        else:         game_developer = ''

        return game_developer

    def _parse_plot(self, page_data):
        # <script type="application/ld+json">
        # {
        #     "name":"Super Metroid",
        #     "description":"Take on a legion of Space Pirates ....",
        #     "keywords":"" }
        # </script>
        m_plot = re.search('"description":"(.*?)",', page_data)
        if m_plot: game_plot = m_plot.group(1)

        return game_plot
        
    # Get ALL available assets for game.
    # Cache the results because this function may be called multiple times for the
    # same candidate game.
    def _scraper_get_assets_all(self, candidate, status_dic):
        cache_key = str(candidate['id'])
        if cache_key in self.all_asset_cache:
            log_debug('MobyGames::_scraper_get_assets_all() Cache hit "{0}"'.format(cache_key))
            asset_list = self.all_asset_cache[cache_key]
        else:
            log_debug('MobyGames::_scraper_get_assets_all() Cache miss "{0}"'.format(cache_key))
            asset_list = self._load_assets_from_page(candidate)
            log_debug('A total of {0} assets found for candidate ID {1}'.format(
                len(asset_list), candidate['id']))
            self.all_asset_cache[cache_key] = asset_list

        return asset_list
    
    # Load assets from assets web page.
    # The Game Images URL shows a page with boxart and screenshots thumbnails.
    # Boxart can be diferent depending on the ROM/game region. Each region has then a 
    # separate page with the full size artwork (boxfront, boxback, etc.)
    #
    # TODO In the assets web page only the Boxfront is shown. The Boxback and Spine are in the
    #      image web page. Currently I do not know how to solve this...
    #      The easiest thing to do is to support only Boxfront.
    #
    # https://gamefaqs.gamespot.com/snes/519824-super-mario-world/images
    # https://gamefaqs.gamespot.com/snes/588741-super-metroid/images
    # https://gamefaqs.gamespot.com/genesis/563316-chakan/images
    #
    # <div class="pod game_imgs">
    #   <div class="head"><h2 class="title">Game Box Shots</h2></div>
    #   <div class="body">
    #   <table class="contrib">
    #   <tr>
    #     <td class="thumb index:0 modded:0 iteration:1 modded:1">
    #       <div class="img boxshot">
    #         <a href="/genesis/563316-chakan/images/145463">
    #           <img class="img100 imgboxart" src="https://gamefaqs.akamaized.net/box/3/1/7/2317_thumb.jpg" alt="Chakan (US)" />
    #         </a>
    #         <div class="region">US 1992</div>
    #       </div>
    #     </td>
    #   ......
    #     <td></td>
    #   </tr>
    #   </table>
    #   </div>
    #   <div class="head"><h2 class="title">GameFAQs Reader Screenshots</h2></div>
    #   <div class="body"><table class="contrib">
    #   <tr>
    #     <td class="thumb">
    #     <a href="/genesis/563316-chakan/images/21">
    #       <img class="imgboxart" src="https://gamefaqs.akamaized.net/screens/f/c/b/gfs_45463_1_1_thm.jpg" />
    #     </a>
    #   </td>
    def _load_assets_from_page(self, candidate):
        url = 'https://gamefaqs.gamespot.com{}/images'.format(candidate['id'])
        log_debug('GameFAQs::_scraper_get_assets_all() Get asset data from {}'.format(url))
        page_data = net_get_URL(url)
        self._dump_file_debug('GameFAQs_load_assets_from_page.html', page_data)

        # --- Parse all assets ---
        # findall() returns a list of strings OR a list of tuples of strings (re with groups).
        # This RE picks the contents inside the screenshoots tables.
        r_str = '<div class="head"><h2 class="title">([\w\s]+?)</h2></div><div class="body"><table class="contrib">(.*?)</table></div>'
        m_asset_blocks = re.findall(r_str, page_data)
        assets_list = []
        for asset_block in m_asset_blocks:
            asset_table_title = asset_block[0]
            asset_table_data = asset_block[1]
            log_debug('Collecting assets from "{}"'.format(asset_table_title))
            
            # --- Depending on the table title select assets ---
            title_snap_taken = True
            if 'Box' in asset_table_title:
                asset_infos = [ASSET_BOXFRONT_ID, ASSET_BOXBACK_ID]
            # Title is usually the first or first snapshots in GameFAQs.
            elif 'Screenshots' in asset_table_title:
                asset_infos = [ASSET_SNAP_ID]
                if not('?page=' in url):
                    asset_infos.append(ASSET_TITLE_ID)
                    title_snap_taken = False

            # --- Parse all image links in table ---
            # <a href="/nes/578318-castlevania/images/135454">
            # <img class="img100 imgboxart" src="https://gamefaqs.akamaized.net/box/2/7/6/2276_thumb.jpg" alt="Castlevania (US)" />
            # </a>
            r_str = '<a href="(?P<lnk>.+?)"><img class="(img100\s)?imgboxart" src="(?P<thumb>.+?)" (alt="(?P<alt>.+?)")?\s?/></a>'
            block_items = re.finditer(r_str, asset_table_data)
            for m in block_items:
                image_data = m.groupdict()
                # log_variable('image_data', image_data)
                for asset_id in asset_infos:
                    if asset_id == ASSET_TITLE_ID and title_snap_taken: continue
                    if asset_id == ASSET_TITLE_ID: title_snap_taken = True
                    asset_data = self._new_assetdata_dic()
                    asset_data['asset_ID']     = asset_id
                    asset_data['display_name'] = image_data['alt'] if image_data['alt'] else ''
                    asset_data['url_thumb']    = image_data['thumb']
                    asset_data['url']          = image_data['lnk']
                    asset_data['is_on_page']   = True
                    assets_list.append(asset_data)
                    # log_variable('asset_data', asset_data)

        # --- Recursively load more image pages ---
        # Deactivated for now. Images on the first page should me more than enough.
        # next_page_result = re.findall('<li><a href="(\S*?)">Next Page\s<i', page_data, re.MULTILINE)
        # if len(next_page_result) > 0:
        #     new_url = 'https://gamefaqs.gamespot.com{}'.format(next_page_result[0])
        #     assets_list = assets_list + self._load_assets_from_url(new_url)

        return assets_list
    
# -------------------------------------------------------------------------------------------------
# Arcade Database online scraper (for MAME).
#
# | Site     | http://adb.arcadeitalia.net/                    |
# | API info | http://adb.arcadeitalia.net/service_scraper.php |
# -------------------------------------------------------------------------------------------------
class ArcadeDB(Scraper):
    # --- Class variables ------------------------------------------------------------------------
    supported_metadata_list = [
        META_TITLE_ID,
        META_YEAR_ID,
        META_GENRE_ID,
        META_DEVELOPER_ID,
        META_NPLAYERS_ID,
        META_PLOT_ID,
    ]
    supported_asset_list = [
        ASSET_TITLE_ID,
        ASSET_SNAP_ID,
        ASSET_BOXFRONT_ID,
        ASSET_FLYER_ID,
    ]

    # --- Constructor ----------------------------------------------------------------------------
    def __init__(self, settings):
        # --- Internal stuff ---
        # Cache all data returned by API QUERY_MAME function.
        self.cache_QUERY_MAME = {}

        # --- Pass down common scraper settings ---
        super(ArcadeDB, self).__init__(settings)

    # --- Base class abstract methods ------------------------------------------------------------
    def get_name(self): return 'ArcadeDB'

    def supports_metadata_ID(self, metadata_ID):
        return True if metadata_ID in ArcadeDB.supported_metadata_list else False

    def supports_metadata(self): return True

    def supports_asset_ID(self, asset_ID):
        return True if asset_ID in ArcadeDB.supported_asset_list else False

    def supports_assets(self): return True
            
    # ArcadeDB does not require any API keys.
    def check_before_scraping(self, status_dic): return status_dic
    
    def get_candidates(self, search_term, rombase_noext, platform, status_dic):
        log_debug('ArcadeDB::get_candidates() search_term    "{0}"'.format(search_term))
        log_debug('ArcadeDB::get_candidates() rom_base_noext "{0}"'.format(rombase_noext))
        log_debug('ArcadeDB::get_candidates() AEL platform   "{0}"'.format(platform))

        # --- Get scraping data and cache it ---
        # ArcadeDB QUERY_MAME returns absolutely everything about a single ROM, including
        # metadata, artwork, etc.
        # This data must be cached in this object for every request done.
        cache_str = search_term + '__' + rombase_noext + '__' + platform
        if cache_str in self.cache_QUERY_MAME:
            log_debug('ArcadeDB::get_candidates() Cache hit "{0}"'.format(cache_str))
            json_response_dic = self.cache_QUERY_MAME[cache_str]
        else:
            log_debug('ArcadeDB::get_candidates() Cache miss "{0}"'.format(cache_str))
            json_response_dic = self._get_QUERY_MAME(search_term, rombase_noext, platform)
            self.cache_QUERY_MAME[cache_str] = json_response_dic

        # --- Return cadidate list ---
        num_games = len(json_response_dic['result'])
        candidate_list = []
        if num_games == 0:
            log_debug('ArcadeDB::get_candidates() Scraper found no game.')
        elif num_games == 1:
            log_debug('ArcadeDB::get_candidates() Scraper found one game.')
            gameinfo_dic = json_response_dic['result'][0]
            candidate = self._new_candidate_dic()
            candidate['id'] = rombase_noext
            candidate['display_name'] = gameinfo_dic['title']
            candidate['platform'] = platform
            candidate['scraper_platform'] = platform
            candidate['order'] = 1
            candidate['cache_str'] = cache_str # Special field to retrieve game from cache.
            candidate_list.append(candidate)
        else:
            raise AddonError('Unexpected number of games returned (more than one).')

        return candidate_list

    def get_metadata(self, candidate, status_dic):
        # --- Retrieve game data from cache ---
        log_debug('ArcadeDB::get_metadata() Cache retrieving "{}"'.format(candidate['cache_str']))
        json_response_dic = self.cache_QUERY_MAME[candidate['cache_str']]
        gameinfo_dic = json_response_dic['result'][0]

        # --- Parse game metadata ---
        gamedata = self._new_gamedata_dic()
        gamedata['title']     = gameinfo_dic['title']
        gamedata['year']      = gameinfo_dic['year']
        gamedata['genre']     = gameinfo_dic['genre']
        gamedata['developer'] = gameinfo_dic['manufacturer']
        gamedata['nplayers']  = str(gameinfo_dic['players'])
        gamedata['esrb']      = ''
        gamedata['plot']      = gameinfo_dic['history']

        return gamedata

    def get_assets(self, candidate, asset_info, status_dic):
        # --- Retrieve game data from cache ---
        log_debug('ArcadeDB::_scraper_get_assets() Cache retrieving "{}"'.format(candidate['cache_str']))
        json_response_dic = self.cache_QUERY_MAME[candidate['cache_str']]
        gameinfo_dic = json_response_dic['result'][0]

        # --- Parse game assets ---
        all_asset_list = self._get_assets_all(gameinfo_dic)
        asset_list = [asset_dic for asset_dic in all_asset_list if asset_dic['asset_ID'] == asset_info.id]
        log_debug('ArcadeDB::_scraper_get_assets() Total assets {0} / Returned assets {1}'.format(
            len(all_asset_list), len(asset_list)))

        return asset_list

    def resolve_asset_URL(self, candidate, status_dic):
        return candidate['url']

    def resolve_asset_URL_extension(self, image_url, status_dic):
        # All ArcadeDB images are in PNG format?
        return '.png'

    # --- This class own methods -----------------------------------------------------------------
    # Call ArcadeDB API only function to retrieve all game metadata.
    def _get_QUERY_MAME(self, search_term, rombase_noext, platform):
        game_name = rombase_noext
        log_debug('ArcadeDB::_get_QUERY_MAME() game_name "{0}"'.format(game_name))

        # --- Build URL ---
        url_a = 'http://adb.arcadeitalia.net/service_scraper.php?ajax=query_mame'
        url_b = '&game_name={0}'.format(game_name)
        url = url_a + url_b

        # --- Grab and parse URL data ---
        page_raw_data = net_get_URL(url)
        try:
            json_response_dic = json.loads(page_raw_data)
        except ValueError as ex:
            json_response_dic = page_raw_data
            log_error('(ValueError Exception) {0}'.format(ex))
            log_error('Message "{0}"'.format(page_raw_data))
        except Exception as ex:
            json_response_dic = page_raw_data
            log_error('(Generic Exception) {0}'.format(ex))
            log_error('Message "{0}"'.format(page_raw_data))
        # Dump file if debug flag is True.
        self._dump_json_debug('ArcadeDB_get_QUERY_MAME.json', json_response_dic)

        return json_response_dic

    # Returns all assets found in the gameinfo_dic dictionary.
    def _get_assets_all(self, gameinfo_dic):
        all_asset_list = []

        # --- Banner (Marquee in MAME) ---
        asset_data = self._get_asset_simple(
            gameinfo_dic, ASSET_BANNER_ID, 'Banner (Marquee)', 'url_image_marquee')
        if asset_data is not None: all_asset_list.append(asset_data)

        # --- Title ---
        asset_data = self._get_asset_simple(
            gameinfo_dic, ASSET_TITLE_ID, 'Title screenshot', 'url_image_title')
        if asset_data is not None: all_asset_list.append(asset_data)

        # --- Snap ---
        asset_data = self._get_asset_simple(
            gameinfo_dic, ASSET_SNAP_ID, 'Snap screenshot', 'url_image_ingame')
        if asset_data is not None: all_asset_list.append(asset_data)

        # --- BoxFront (Cabinet in MAME) ---
        asset_data = self._get_asset_simple(
            gameinfo_dic, ASSET_BOXFRONT_ID, 'BoxFront (Cabinet)', 'url_image_cabinet')
        if asset_data is not None: all_asset_list.append(asset_data)

        # --- BoxBack (CPanel in MAME) ---
        # asset_data = self._get_asset_simple(
        #     gameinfo_dic, ASSET_BOXBACK_ID, 'BoxBack (CPanel)', '')
        # if asset_data is not None: all_asset_list.append(asset_data)

        # --- Cartridge (PCB in MAME) ---
        # asset_data = self._get_asset_simple(
        #     gameinfo_dic, ASSET_CARTRIDGE_ID, 'Cartridge (PCB)', '')
        # if asset_data is not None: all_asset_list.append(asset_data)

        # --- Flyer ---
        asset_data = self._get_asset_simple(
            gameinfo_dic, ASSET_FLYER_ID, 'Flyer', 'url_image_flyer')
        if asset_data is not None: all_asset_list.append(asset_data)

        return all_asset_list
    
    def _get_asset_simple(self, data_dic, asset_ID, title_str, key):
        if key in data_dic:
            asset_data = self._new_assetdata_dic()
            asset_data['asset_ID'] = asset_ID
            asset_data['display_name'] = title_str
            asset_data['url_thumb'] = data_dic[key]
            asset_data['url'] = data_dic[key]
            return asset_data
        else:
            return None
        
class Libretro(Scraper):
    
    # --- Constructor ----------------------------------------------------------------------------
    def __init__(self, settings):
        # --- Pass down common scraper settings ---
        super(Libretro, self).__init__(settings)