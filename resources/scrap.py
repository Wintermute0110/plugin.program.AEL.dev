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
import copy
import datetime
import json
import socket
import time
import urllib
import urlparse
import socket
import zipfile

# --- AEL packages ---
from .constants import *
from .platforms import *
from .utils import *
from .disk_IO import *
from .net_IO import *
from .objects import *
from .rom_audit import *

# --- Scraper use cases ---------------------------------------------------------------------------
# THIS DOCUMENTATION IS OBSOLETE, IT MUST BE UPDATED TO INCLUDE THE SCRAPER DISK CACHE.
#
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
        # log_debug('ScraperFactory.__init__() BEGIN ...')
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
        log_debug('ScraperFactory.__init__() Creating scraper objects...')
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
           self.scraper_objs[SCRAPER_SCREENSCRAPER_ID] = ScreenScraper(self.settings)
        if SCRAPER_GAMEFAQS_ID in SCRAPER_LIST:
            self.scraper_objs[SCRAPER_GAMEFAQS_ID] = GameFAQs(self.settings)
        if SCRAPER_ARCADEDB_ID in SCRAPER_LIST:
            self.scraper_objs[SCRAPER_ARCADEDB_ID] = ArcadeDB(self.settings)
        if SCRAPER_LIBRETRO_ID in SCRAPER_LIST:
           self.scraper_objs[SCRAPER_LIBRETRO_ID] = Libretro(self.settings)
        if SCRAPER_STEAMGRIDDB_ID in SCRAPER_LIST:
            self.scraper_objs[SCRAPER_STEAMGRIDDB_ID] = SteamGridDB(self.settings)

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
        log_debug('ScraperFactory.get_metadata_scraper_menu_list() Building scraper list...')
        scraper_menu_list = {}
        self.metadata_menu_ID_list = []
    
        for scraper_ID in self.scraper_objs:
            scraper_obj = self.scraper_objs[scraper_ID]
            s_name = scraper_obj.get_name()
            if scraper_obj.supports_metadata():
                scraper_menu_list['SCRAPE_' + s_name] = ('Scrape with {0}'.format(s_name))
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
    # @return: dict of scraper ids and scraper names
    def get_asset_scraper_menu_list(self, asset_info):
        log_debug('ScraperFactory::get_asset_scraper_menu_list() Building scraper list...')
        scraper_menu_list = {}
        for scraper_ID in self.scraper_objs:
            scraper_obj = self.scraper_objs[scraper_ID]
            s_name = scraper_obj.get_name()
            if scraper_obj.supports_asset_ID(asset_info.id):
                scraper_menu_list[scraper_ID] = 'Scrape {0} with {1}'.format(asset_info.name, s_name)
                log_verb('Scraper {0} supports asset {1} (ENABLED)'.format(s_name, asset_info.name))
            else:
                log_verb('Scraper {0} lacks asset {1} (DISABLED)'.format(s_name, asset_info.name))

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
        # log_debug('ScraperFactory.create_scanner() BEGIN ...')
        self.strategy_obj = ScrapeStrategy(self.PATHS, self.settings)

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
            log_debug('ScraperFactory.create_scanner() Platform is NON-MAME.')
            log_debug('Using standard scrapers from settings.xml')
            scraper_metadata_index = self.settings['scraper_metadata']
            scraper_asset_index = self.settings['scraper_asset']
            scraper_metadata_ID = SCRAP_METADATA_SETTINGS_LIST[scraper_metadata_index]
            scraper_asset_ID = SCRAP_ASSET_SETTINGS_LIST[scraper_asset_index]
        log_debug('Metadata scraper name {} (index {}, ID {})'.format(
            self.scraper_objs[scraper_metadata_ID].get_name(), scraper_metadata_index, scraper_metadata_ID))
        log_debug('Asset scraper name    {} (index {}, ID {})'.format(
            self.scraper_objs[scraper_asset_ID].get_name(), scraper_asset_index, scraper_asset_ID))

        # Set scraper objects.
        self.strategy_obj.meta_scraper_obj   = self.scraper_objs[scraper_metadata_ID]
        self.strategy_obj.meta_scraper_name  = self.strategy_obj.meta_scraper_obj.get_name()
        self.strategy_obj.asset_scraper_obj  = self.scraper_objs[scraper_asset_ID]
        self.strategy_obj.asset_scraper_name = self.strategy_obj.asset_scraper_obj.get_name()

        flag = self.strategy_obj.meta_scraper_obj is self.strategy_obj.asset_scraper_obj
        self.strategy_obj.meta_and_asset_scraper_same = flag
        log_debug('Are metadata and asset scrapers the same? {}'.format(
            self.strategy_obj.meta_and_asset_scraper_same))

        # --- Add launcher properties to ScrapeStrategy object ---
        self.strategy_obj.launcher = launcher
        self.strategy_obj.platform = platform

        return self.strategy_obj

    # * Flush caches before dereferencing object.
    def destroy_scanner(self, pdialog = None):
        log_debug('ScraperFactory.destroy_scanner() Flushing disk caches...')
        if pdialog is None: pdialog = KodiProgressDialog()
        self.strategy_obj.meta_scraper_obj.flush_disk_cache(pdialog)
        # Only flush asset cache if object is different from metadata.
        if not self.strategy_obj.meta_scraper_obj is self.strategy_obj.asset_scraper_obj:
            self.strategy_obj.asset_scraper_obj.flush_disk_cache()
        else:
            log_debug('Metadata and asset scraper same. Not flushing asset scraper disk cache.')
        self.strategy_obj = None

    # * Create a ScraperStrategy object to be used in the "Edit metadata" context menu.
    # * The scraper disk cache is organised by platform. The scraper object is restricted
    #   to scrape one platform per session.
    def create_CM_metadata(self, scraper_ID):
        log_debug('ScraperFactory.create_CM_metadata() Creating ScrapeStrategy {}'.format(
            scraper_ID))
        self.scraper_ID = scraper_ID
        self.strategy_obj = ScrapeStrategy(self.PATHS, self.settings)

        # --- Choose scraper and set platform ---
        self.strategy_obj.scraper_obj = self.scraper_objs[scraper_ID]
        log_debug('User chose scraper "{0}"'.format(self.strategy_obj.scraper_obj.get_name()))

        # --- Load candidate cache ---
        # We do lazy loading when calling Scraper.check_candidates_cache
        # self.strategy_obj.scraper_obj.load_candidates_cache(platform)

        return self.strategy_obj

    # * Create a ScraperStrategy object to be used in the "Edit asset" context menu.
    #
    # Returns a ScrapeStrategy object which is used for the actual scraping.
    # In AEL 0.9.x this object will be used once. In AEL 0.10.x with recursive CM this object
    # may be used multiple times. Make sure cache works OK.
    def create_CM_asset(self, scraper_ID):
        log_debug('ScraperFactory.create_CM_asset() BEGIN ...')
        self.scraper_ID = scraper_ID
        self.strategy_obj = ScrapeStrategy(self.PATHS, self.settings)

        # --- Choose scraper ---
        self.strategy_obj.scraper_obj = self.scraper_objs[scraper_ID]
        log_debug('User chose scraper "{0}"'.format(self.strategy_obj.scraper_obj.get_name()))

        return self.strategy_obj

    # * Flush caches before dereferencing object.
    def destroy_CM(self, pdialog = None):
        log_debug('ScraperFactory.destroy_CM() Flushing disk caches...')
        if pdialog is None: pdialog = KodiProgressDialog()
        self.strategy_obj.scraper_obj.flush_disk_cache(pdialog)
        self.strategy_obj.scraper_obj = None
        self.strategy_obj = None

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

    SCRAPE_ROM      = 'ROM'
    SCRAPE_LAUNCHER = 'Launcher'

    # --- Constructor ----------------------------------------------------------------------------
    # @param PATHS: PATH object.
    # @param settings: [dict] Addon settings.
    def __init__(self, PATHS, settings):
        log_debug('ScrapeStrategy.__init__() Initializing ScrapeStrategy...')
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

    # Call this function before the ROM Scanning starts.
    def scanner_set_progress_dialog(self, pdialog, pdialog_verbose):
        log_debug('ScrapeStrategy.scanner_set_progress_dialog() Setting progress dialog...')
        self.pdialog = pdialog
        self.pdialog_verbose = pdialog_verbose

        # DEBUG code, never use in a release.
        # log_debug('ScrapeStrategy.begin_ROM_scanner() DEBUG dumping of scraper data ON.')
        # self.meta_scraper_obj.set_debug_file_dump(True, '/home/kodi/')
        # self.asset_scraper_obj.set_debug_file_dump(True, '/home/kodi/')

    # Check if scraper is ready for operation (missing API keys, etc.). If not disable scraper.
    # Display error reported in status_dic as Kodi dialogs.
    def scanner_check_before_scraping(self):
        status_dic = kodi_new_status_dic('No error')
        self.meta_scraper_obj.check_before_scraping(status_dic)
        if not status_dic['status']: kodi_dialog_OK(status_dic['msg'])

        # Only check asset scraper if it's different from the metadata scraper.
        if not self.meta_and_asset_scraper_same:
            status_dic = kodi_new_status_dic('No error')
            self.asset_scraper_obj.check_before_scraping(status_dic)
            if not status_dic['status']: kodi_dialog_OK(status_dic['msg'])

    def scanner_check_launcher_unset_asset_dirs(self):
        log_debug('ScrapeStrategy::scanner_check_launcher_unset_asset_dirs() BEGIN ...')
        
        rom_asset_states = self.launcher.get_ROM_assets_enabled_statusses()
        self.enabled_asset_list = rom_asset_states.values()
        self.unconfigured_name_list = []
        for rom_asset, enabled_state in rom_asset_states.items():
            if not enabled_state:
                self.unconfigured_name_list.append(rom_asset.name)
 
    # Determine the actions to be carried out by process_ROM_metadata() and process_ROM_assets().
    # Must be called before the aforementioned methods.
    def scanner_process_ROM_begin(self, ROM, ROM_checksums):
        log_debug('ScrapeStrategy.scanner_process_ROM_begin() Determining metadata and asset actions...')

        # --- Determine metadata action ----------------------------------------------------------
        # --- Test if NFO file exists ---
        ROM_path = ROM.get_file()
        self.NFO_file = FileName(ROM_path.getPathNoExt() + '.nfo')
        NFO_file_found = True if self.NFO_file.exists() else False
        if NFO_file_found:
            log_debug('NFO file found "{0}"'.format(self.NFO_file.getPath()))
        else:
            log_debug('NFO file NOT found "{0}"'.format(self.NFO_file.getPath()))

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
        self.local_asset_list = g_assetFactory.assets_search_local_cached_assets(self.launcher, ROM, self.enabled_asset_list)
        self.asset_action_list = [ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET] * len(ROM_ASSET_ID_LIST)
        # Print information to the log
        if self.scan_asset_policy == 0:
            log_debug('Asset policy: Local images ON | Scraper OFF')
        elif self.scan_asset_policy == 1:
            log_debug('Asset policy: Local images ON | Scraper ON')
        elif self.scan_asset_policy == 2:
            log_debug('Asset policy: Local images OFF | Scraper ON')
        else:
            raise ValueError('Invalid scan_asset_policy value {0}'.format(self.scan_asset_policy))
        # Process asset by asset
        for i, asset_ID in enumerate(ROM_ASSET_ID_LIST):
            AInfo = g_assetFactory.get_asset_info(asset_ID)
            # Local artwork.
            if self.scan_asset_policy == 0:
                if not self.enabled_asset_list[i]:
                    log_debug('Skipping {0} (dir not configured).'.format(AInfo.name))
                elif self.local_asset_list[i]:
                    log_debug('Local {0} FOUND'.format(AInfo.name))
                else:
                    log_debug('Local {0} NOT found.'.format(AInfo.name))
                self.asset_action_list[i] = ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET
            # Local artwork + Scrapers.
            elif self.scan_asset_policy == 1:
                if not self.enabled_asset_list[i]:
                    log_debug('Skipping {0} (dir not configured).'.format(AInfo.name))
                    self.asset_action_list[i] = ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET
                elif self.local_asset_list[i]:
                    log_debug('Local {0} FOUND'.format(AInfo.name))
                    self.asset_action_list[i] = ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET
                elif self.asset_scraper_obj.supports_asset_ID(asset_ID):
                    # Scrape only if scraper supports asset.
                    log_debug('Local {0} NOT found. Scraping.'.format(AInfo.name))
                    self.asset_action_list[i] = ScrapeStrategy.ACTION_ASSET_SCRAPER
                else:
                    log_debug('Local {0} NOT found. No scraper support.'.format(AInfo.name))
                    self.asset_action_list[i] = ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET
            # Scrapers.
            elif self.scan_asset_policy == 2:
                if not self.enabled_asset_list[i]:
                    log_debug('Skipping {0} (dir not configured).'.format(AInfo.name))
                    self.asset_action_list[i] = ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET
                # Scraper does not support asset but local asset found.
                elif not self.asset_scraper_obj.supports_asset_ID(asset_ID) and self.local_asset_list[i]:
                    log_debug('Scraper {} does not support {}. Using local asset.'.format(
                        self.asset_scraper_name, AInfo.name))
                    self.asset_action_list[i] = ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET
                # Scraper does not support asset and local asset not found.
                elif not self.asset_scraper_obj.supports_asset_ID(asset_ID) and not self.local_asset_list[i]:
                    log_debug('Scraper {} does not support {}. Local asset not found.'.format(
                        self.asset_scraper_name, AInfo.name))
                    self.asset_action_list[i] = ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET
                # Scraper supports asset. Scrape wheter local asset is found or not.
                elif self.asset_scraper_obj.supports_asset_ID(asset_ID):
                    log_debug('Scraping {} with {}.'.format(AInfo.name, self.asset_scraper_name))
                    self.asset_action_list[i] = ScrapeStrategy.ACTION_ASSET_SCRAPER
                else:
                    raise ValueError('Logical error')

        # --- If metadata or any asset is scraped then select the game among the candidates ---
        # Note that the metadata and asset scrapers may be different. If so, candidates
        # must be selected for both scrapers.
        if self.metadata_action == ScrapeStrategy.ACTION_META_SCRAPER:
            log_debug('Getting metadata candidate game')
            # What if status_dic reports and error here? Is it ignored?
            status_dic = kodi_new_status_dic('No error')
            self._scanner_get_candidate(
                ROM, ROM_checksums, self.meta_scraper_obj, self.meta_scraper_name, status_dic)
        else:
            log_debug('Metadata candidate game is None')
            self.meta_scraper_obj.candidate = None

        # Asset scraper is needed and metadata and asset scrapers are the same.
        # Do nothing because both scraper objects are really the same object and candidate has been
        # set internally in the scraper object. Unless candidate selection was skipped for metadata.
        temp_asset_list = [x == ScrapeStrategy.ACTION_ASSET_SCRAPER for x in self.asset_action_list]
        if any(temp_asset_list):    
            if self.meta_and_asset_scraper_same and self.meta_scraper_obj.candidate is not None:
                log_debug('Asset candidate game same as metadata candidate. Doing nothing.')
            # Otherwise search for an asset scraper candidate if needed.
            else:
                log_debug('Getting asset candidate game.')
                # What if status_dic reports and error here? Is it ignored?
                status_dic = kodi_new_status_dic('No error')
                self._scanner_get_candidate(
                    ROM, ROM_checksums, self.asset_scraper_obj, self.asset_scraper_name, status_dic)
        # Asset scraper not needed.
        else:
            log_debug('Asset candidate game is None')

    # Called by the ROM scanner. Fills in the ROM metadata.
    #
    # @param ROM: [Rom] ROM object.
    def scanner_process_ROM_metadata(self, ROM):
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
                self.pdialog.updateMessage2('Loading NFO file {0}'.format(self.NFO_file.getPath()))
            # If this point is reached the NFO file was found previosly.
            log_debug('Loading NFO P "{0}"'.format(self.NFO_file.getPath()))
            nfo_dic = fs_import_ROM_NFO_file_scanner(self.NFO_file)
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
            raise ValueError('Invalid metadata_action value {0}'.format(metadata_action))

    # Called by the ROM scanner. Fills in the ROM assets.
    #
    # @param ROM: [ROM] ROM data object. Mutable and edited by assignment.
    def scanner_process_ROM_assets(self, ROM):
        log_debug('ScrapeStrategy.scanner_process_ROM_assets() Processing asset actions...')
        # --- Process asset by asset actions ---
        # --- Asset scraping ---
        for i, asset_ID in enumerate(ROM_ASSET_ID_LIST):
            AInfo = g_assetFactory.get_asset_info(asset_ID)
            if self.asset_action_list[i] == ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET:
                log_debug('Using local asset for {}'.format(AInfo.name))
                ROM.set_asset(AInfo, self.local_asset_list[i])
            elif self.asset_action_list[i] == ScrapeStrategy.ACTION_ASSET_SCRAPER:   
                asset_path = self._scanner_scrap_ROM_asset(AInfo, self.local_asset_list[i], ROM)                             
                ROM.set_asset(AInfo, asset_path)
            else:
                raise ValueError('Asset {} index {} ID {} unknown action {}'.format(
                    AInfo.name, i, asset_ID, self.asset_action_list[i]))

        romdata = ROM.get_data_dic()
        # --- Print some debug info ---
        log_verb('Set Title     file "{}"'.format(romdata['s_title']))
        log_verb('Set Snap      file "{}"'.format(romdata['s_snap']))
        log_verb('Set Boxfront  file "{}"'.format(romdata['s_boxfront']))
        log_verb('Set Boxback   file "{}"'.format(romdata['s_boxback']))
        log_verb('Set Cartridge file "{}"'.format(romdata['s_cartridge']))
        log_verb('Set Fanart    file "{}"'.format(romdata['s_fanart']))
        log_verb('Set Banner    file "{}"'.format(romdata['s_banner']))
        log_verb('Set Clearlogo file "{}"'.format(romdata['s_clearlogo']))
        log_verb('Set Flyer     file "{}"'.format(romdata['s_flyer']))
        log_verb('Set Map       file "{}"'.format(romdata['s_map']))
        log_verb('Set Manual    file "{}"'.format(romdata['s_manual']))
        log_verb('Set Trailer   file "{}"'.format(romdata['s_trailer']))

        return ROM

    # Get a candidate game in the ROM scanner.
    # Returns nothing.
    def _scanner_get_candidate(self, ROM, ROM_checksums_FN, scraper_obj, scraper_name, status_dic):
        # --- Update scanner progress dialog ---
        if self.pdialog_verbose:
            scraper_text = 'Searching games with scraper {}...'.format(scraper_name)
            self.pdialog.updateMessage2(scraper_text)
        log_debug('Searching games with scaper {}'.format(scraper_name))

        # * The scanner uses the cached ROM candidate always.
        # * If the candidate is empty it means it was previously searched and the scraper
        #   found no candidates. In this case, the context menu must be used to manually
        #   change the search string and set a valid candidate.
        ROM_path = ROM.get_file()
        if scraper_obj.check_candidates_cache(ROM_path, self.platform):
            log_debug('ROM "{}" in candidates cache.'.format(ROM_path.getPath()))
            candidate = scraper_obj.retrieve_from_candidates_cache(ROM_path, self.platform)
            if not candidate:
                log_debug('Candidate game is empty. ROM will not be scraped again by the scanner.')
            use_from_cache = True
        else:
            log_debug('ROM "{}" NOT in candidates cache.'.format(ROM_path.getPath()))
            use_from_cache = False
        log_debug('use_from_cache "{}"'.format(use_from_cache))

        if use_from_cache:
            scraper_obj.set_candidate_from_cache(ROM_path, self.platform)
        else:
            # Clear all caches to remove preexiting information, just in case user is rescraping.
            scraper_obj.clear_cache(ROM_path, self.platform)

            # --- Call scraper and get a list of games ---
            # In manual scanner mode should we ask the user for a search string
            # if the scraper supports it?
            # I think it is better to keep things like this. If the scraper does not
            # find a proper candidate game the user can fix the scraper cache with the
            # context menu.
            rom_name_scraping = text_format_ROM_name_for_scraping(ROM_path.getBaseNoExt())                
            candidates = scraper_obj.get_candidates(rom_name_scraping, ROM_path, ROM_checksums_FN, self.platform, status_dic)
            # * If the scraper produced an error notification show it and continue scanner operation.
            # * Note that if many errors/exceptions happen (for example, network is down) then
            #   the scraper will disable itself after a number of errors and only a limited number
            #   of messages will be displayed.
            # * In the scanner treat any scraper error message as a Kodi OK dialog.
            # * Once the error is displayed reset status_dic
            if not status_dic['status']:
                self.pdialog.close()
                # Close error message dialog automatically 1 minute to keep scanning.
                # kodi_dialog_OK(status_dic['msg'])
                kodi_dialog_yesno_timer(status_dic['msg'], 60000)
                status_dic = kodi_new_status_dic('No error')
                self.pdialog.reopen()
            # * If candidates is None some kind of error/exception happened.
            # * None is also returned if the scraper is disabled (also no error in status_dic).
            # * Set the candidate to None in the scraper object so later calls to get_metadata()
            #   and get_assets() do not fail (they will return None immediately).
            # * It will NOT be introduced in the cache to be rescraped. Objects with None value are
            #   never introduced in the cache.
            if candidates is None:
                log_debug('Error getting the candidate (None).')
                scraper_obj.set_candidate(ROM_path, self.platform, None)
                return
            # * If candidates list is empty scraper operation was correct but no candidate was
            # * found. In this case set the candidate in the scraper object to an empty
            # * dictionary and introduce it in the cache.
            if not candidates:
                log_debug('Found no candidates after searching.')
                scraper_obj.set_candidate(ROM_path, self.platform, dict())
                return
            log_debug('Scraper {} found {} candidate/s'.format(scraper_name, len(candidates)))

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
                        'Select game for ROM {}'.format(ROM_path.getBaseNoExt()), game_name_list)
                    if select_candidate_idx < 0: select_candidate_idx = 0
                    self.pdialog.reopen()
            elif self.game_selection_mode == 1:
                log_debug('Metadata automatic scraping. Selecting first result.')
                select_candidate_idx = 0
            else:
                raise ValueError('Invalid game_selection_mode {}'.format(self.game_selection_mode))
            candidate = candidates[select_candidate_idx]

            # --- Set candidate. This will introduce it in the cache ---
            scraper_obj.set_candidate(ROM_path, self.platform, candidate)

    # Scraps ROM metadata in the ROM scanner.
    def _scanner_scrap_ROM_metadata(self, ROM):
        log_debug('ScrapeStrategy._scanner_scrap_ROM_metadata() Scraping metadata...')

        # --- Update scanner progress dialog ---
        if self.pdialog_verbose:
            scraper_text = 'Scraping metadata with {}...'.format(self.meta_scraper_name)
            self.pdialog.updateMessage2(scraper_text)

        # --- If no candidates available just clean the ROM Title and return ---
        if self.meta_scraper_obj.candidate is None:
            log_verb('Medatada candidates is None. Cleaning ROM name only.')
            ROM_file = ROM.get_file()
            ROM.set_name(text_format_ROM_title(ROM_file.getBaseNoExt(), self.scan_clean_tags))
            return
        if not self.meta_scraper_obj.candidate:
            log_verb('Medatada candidate is empty (no candidates found). Cleaning ROM name only.')
            ROM_file = ROM.get_file()
            ROM.set_name(text_format_ROM_title(ROM_file.getBaseNoExt(), self.scan_clean_tags))
            # Update the empty NFO file to mark the ROM as scraped and avoid rescraping
            # if launcher is scanned again.
            self._scanner_update_NFO_file(ROM)
            return

        # --- Grab metadata for selected game and put into ROM ---
        status_dic = kodi_new_status_dic('No error')
        game_data = self.meta_scraper_obj.get_metadata(status_dic)
        if not status_dic['status']:
            self.pdialog.close()
            # Close error message dialog automatically 1 minute to keep scanning.
            # kodi_dialog_OK(status_dic['msg'])
            kodi_dialog_yesno_timer(status_dic['msg'], 60000)
            self.pdialog.reopen()
            return
        scraper_applied = self._apply_candidate_on_metadata(game_data, ROM)
        self._scanner_update_NFO_file(ROM)

    # Update ROM NFO file after scraping.
    def _scanner_update_NFO_file(self, ROM):
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
        asset_path_noext_FN = asset_dir_FN + ROM.get_file().getBaseNoExt()
        t = 'ScrapeStrategy._scanner_scrap_ROM_asset() Scraping {} with scraper {} ------------------------------'
        log_debug(t.format(asset_name, self.asset_scraper_name))
        status_dic = kodi_new_status_dic('No error')
        
        # By default always use local image if found in case scraper fails.
        ret_asset_path = local_asset_path
        log_debug('local_asset_path "{}"'.format(local_asset_path))
        log_debug('asset_path_noext "{}"'.format(asset_path_noext_FN.getPath()))

        # --- If no candidates available just clean the ROM Title and return ---
        if self.asset_scraper_obj.candidate is None:
            log_verb('Asset candidate is None (previous error). Doing nothing.')
            return ret_asset_path
        if not self.asset_scraper_obj.candidate:
            log_verb('Asset candidate is empty (no candidates found). Doing nothing.')
            return ret_asset_path

        # --- If scraper does not support particular asset return inmediately ---
        if not self.asset_scraper_obj.supports_asset_ID(asset_info.id):
            log_debug('Scraper {} does not support asset {}.'.format(
                self.asset_scraper_name, asset_name))
            return ret_asset_path

        # --- Update scanner progress dialog ---
        if self.pdialog_verbose:
            scraper_text = 'Getting {} images from {}...'.format(
                asset_name, self.asset_scraper_name)
            self.pdialog.updateMessage2(scraper_text)

        # --- Grab list of images/assets for the selected candidate ---
        assetdata_list = self.asset_scraper_obj.get_assets(asset_info, status_dic)
        if not status_dic['status']:
            self.pdialog.close()
            # Close error message dialog automatically 1 minute to keep scanning.
            # kodi_dialog_OK(status_dic['msg'])
            kodi_dialog_yesno_timer(status_dic['msg'], 60000)
            status_dic = kodi_new_status_dic('No error')
            self.pdialog.reopen()
        if assetdata_list is None or not assetdata_list:
            # If scraper returns no images return current local asset.
            log_debug('{} {} found no images.'.format(self.asset_scraper_name, asset_name))
            return ret_asset_path
        # log_verb('{} scraper returned {} images.'.format(asset_name, len(assetdata_list)))

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
        image_url, image_url_log = self.asset_scraper_obj.resolve_asset_URL(
            selected_asset, status_dic)
        if not status_dic['status']:
            self.pdialog.close()
            # Close error message dialog automatically 1 minute to keep scanning.
            # kodi_dialog_OK(status_dic['msg'])
            kodi_dialog_yesno_timer(status_dic['msg'], 60000)
            status_dic = kodi_new_status_dic('No error')
            self.pdialog.reopen()
        if image_url is None or not image_url:
            log_debug('Error resolving URL')
            return ret_asset_path
        log_debug('Resolved {0} to URL "{1}"'.format(asset_name, image_url_log))

        # --- Resolve URL extension ---
        log_debug('Resolving asset URL extension...')
        image_ext = self.asset_scraper_obj.resolve_asset_URL_extension(
            selected_asset, image_url, status_dic)
        if not status_dic['status']:
            self.pdialog.close()
            # Close error message dialog automatically 1 minute to keep scanning.
            # kodi_dialog_OK(status_dic['msg'])
            kodi_dialog_yesno_timer(status_dic['msg'], 60000)
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
        log_verb('Download  "{0}"'.format(image_url_log))
        log_verb('Into file "{0}"'.format(image_local_path.getPath()))
        try:
            # net_download_img() never prints URLs or paths.
            net_download_img(image_url, image_local_path)
        except socket.timeout:
            self.pdialog.close()
            # Close error message dialog automatically 1 minute to keep scanning.
            # kodi_dialog_OK(status_dic['msg'])
            kodi_dialog_yesno_timer('Cannot download {} image (Timeout)'.format(asset_name), 60000)
            self.pdialog.reopen()

        # --- Update Kodi cache with downloaded image ---
        # Recache only if local image is in the Kodi cache, this function takes care of that.
        # kodi_update_image_cache(image_path)

        # --- Check if downloaded image file is OK ---
        # For example, check if a PNG image is really a PNG, a JPG is really JPG, etc.
        # Check for 0 byte files and delete them.
        # Etc.

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
        log_debug('ScrapeStrategy.scrap_CM_metadata_ROM() BEGIN ...')
        # In AEL 0.10.x this data is grabed from the objects, not passed using a dictionary.
        rom_FN = data_dic['rom_FN']
        rom_base_noext = rom_FN.getBaseNoExt()
        status_dic = kodi_new_status_dic('ROM metadata updated')
        scraper_name = self.scraper_obj.get_name()

        # --- Check if scraper is OK (API keys configured, etc.) ---
        self.scraper_obj.check_before_scraping(status_dic)
        if not status_dic['status']: return status_dic

        # --- Grab and set candidate game ---
        self._scrap_CM_get_candidate(ScrapeStrategy.SCRAPE_ROM, object_dic, data_dic, status_dic)
        if not status_dic['status']: return status_dic

        # --- Grab metadata ---
        pdialog = KodiProgressDialog()
        pdialog.startProgress('Scraping metadata with {}...'.format(scraper_name))
        gamedata = self.scraper_obj.get_metadata(status_dic)
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
        log_debug('ScrapeStrategy.scrap_CM_metadata_Launcher() BEGIN ...')
        status_dic = kodi_new_status_dic('Launcher metadata updated')
        scraper_name = self.scraper_obj.get_name()

        # --- Check if scraper is OK (API keys configured, etc.) ---
        self.scraper_obj.check_before_scraping(status_dic)
        if not status_dic['status']: return status_dic

        # --- Grab candidate game ---
        self._scrap_CM_get_candidate(ScrapeStrategy.SCRAPE_LAUNCHER, object_dic, data_dic, status_dic)
        if not status_dic['status']: return status_dic

        # --- Grab metadata ---
        pdialog = KodiProgressDialog()
        pdialog.startProgress('Scraping metadata with {}...'.format(scraper_name))
        gamedata = self.scraper_obj.get_metadata(candiate)
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
        # log_debug('ScrapeStrategy.scrap_CM_asset() BEGIN...')

        # --- Cached frequent used things ---
        asset_info = g_assetFactory.get_asset_info(asset_ID)
        asset_name = asset_info.name
        # In AEL 0.10.x this data is grabed from the objects, not passed using a dictionary.
        platform = data_dic['platform']
        current_asset_FN = data_dic['current_asset_FN']
        asset_path_noext_FN = data_dic['asset_path_noext']
        log_info('ScrapeStrategy.scrap_CM_asset() Scraping {0}...'.format(object_dic['m_name']))
        status_dic = kodi_new_status_dic('Asset updated')
        scraper_name = self.scraper_obj.get_name()

        # --- Check if scraper is OK (API keys configured, etc.) ---
        self.scraper_obj.check_before_scraping(status_dic)
        if not status_dic['status']: return status_dic

        # --- Grab candidate game ---
        self._scrap_CM_get_candidate(ScrapeStrategy.SCRAPE_ROM, object_dic, data_dic, status_dic)
        if not status_dic['status']: return status_dic

        # --- Grab list of images for the selected game -------------------------------------------
        pdialog = KodiProgressDialog()
        pdialog.startProgress('Getting {} images from {}...'.format(asset_name, scraper_name))
        assetdata_list = self.scraper_obj.get_assets(asset_ID, status_dic)
        pdialog.endProgress()
        # Error/exception.
        if not status_dic['status']: return status_dic
        log_verb('{0} {1} scraper returned {2} images'.format(
            scraper_name, asset_name, len(assetdata_list)))
        # Scraper found no assets. Return immediately.
        if not assetdata_list:
            status_dic['status'] = False
            status_dic['dialog'] = KODI_MESSAGE_DIALOG
            status_dic['msg'] = '{} scraper found no {} images.'.format(scraper_name, asset_name)

            return status_dic

        # If there is a local image add it to the list and show it to the user.
        local_asset_in_list_flag = False
        if current_asset_FN.exists():
            local_asset = {
                'asset_ID'     : asset_ID,
                'display_name' : 'Current local image',
                'url_thumb'    : current_asset_FN.getPath(),
            }
            # Make a copy of the asset list to not mess up with the asset cache.
            assetdata_list_returned = assetdata_list
            assetdata_list = copy.deepcopy(assetdata_list)
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
        pdialog.startProgress('Resolving asset URL with {}...'.format(scraper_name))
        image_url, image_url_log = self.scraper_obj.resolve_asset_URL(selected_asset, status_dic)
        pdialog.endProgress()
        log_debug('Resolved {} to URL "{}"'.format(asset_name, image_url_log))
        if not image_url:
            log_error('_gui_edit_asset() Error in scraper.resolve_asset_URL()')
            status_dic['status'] = False
            status_dic['msg'] = 'Error downloading asset'
            return status_dic
        pdialog.startProgress('Resolving URL extension with {}...'.format(scraper_name))
        image_ext = self.scraper_obj.resolve_asset_URL_extension(selected_asset, image_url, status_dic)
        pdialog.endProgress()        
        log_debug('Resolved URL extension "{}"'.format(image_ext))
        if not image_ext:
            log_error('_gui_edit_asset() Error in scraper.resolve_asset_URL_extension()')
            status_dic['status'] = False
            status_dic['msg'] = 'Error downloading asset'
            return status_dic

        # --- Download image ---
        log_debug('Downloading image from {}...'.format(scraper_name))
        image_local_path = asset_path_noext_FN.append('.' + image_ext).getPath()
        log_verb('Download  "{0}"'.format(image_url_log))
        log_verb('Into file "{0}"'.format(image_local_path))
        pdialog.startProgress('Downloading {} from {}...'.format(asset_name, scraper_name))
        try:
            self.scraper_obj.download_image(image_url, image_local_path)
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
        status_dic['msg'] = 'Downloaded {} with {} scraper'.format(asset_name, scraper_name)

        return status_dic

    # This function is used when scraping stuff from the context menu.
    # Introduce the search string, grab candidate games, and select a candidate for scraping.
    #
    # * Scraping from the context menu is always in manual mode.
    #
    # @param object_name: [str] SCRAPE_ROM, SCRAPE_LAUNCHER.
    def _scrap_CM_get_candidate(self, object_name, object_dic, data_dic, status_dic):
        # log_debug('ScrapeStrategy._scrap_CM_get_candidate() BEGIN...')

        # In AEL 0.10.x this data is grabed from the objects, not passed using a dictionary.
        rom_FN = data_dic['rom_FN']
        rom_checksums_FN = data_dic['rom_checksums_FN']
        platform = data_dic['platform']
        scraper_name = self.scraper_obj.get_name()

        # * Note that empty candidates may be in the cache. An empty candidate means that
        #   the scraper search was unsucessful. For some scrapers, changing the search
        #   string may produce a valid candidate.
        # * In the context menu always rescrape empty candidates.
        # * In the ROM scanner empty candidates are never rescraped. In that cases
        #   the user must use the context menu to find a valid candidate.
        if self.scraper_obj.check_candidates_cache(rom_FN, platform):
            log_debug('ROM "{}" in candidates cache.'.format(rom_FN.getBaseNoExt()))
            candidate = self.scraper_obj.retrieve_from_candidates_cache(rom_FN, platform)
            if not candidate:
                kodi_dialog_OK(
                    'Candidate game in the scraper disk cache but empty. '
                    'Forcing rescraping.')
                log_debug('ROM "{}" candidate is empting. Force rescraping.')
                use_from_cache = False
            else:
                ret = kodi_dialog_yesno_custom(
                    'Candidate game in the scraper disk cache. '
                    'Use candidate from cache or rescrape?',
                    'Scrape', 'Use from cache')
                use_from_cache = False if ret else True
        else:
            log_debug('ROM "{}" NOT in candidates cache.'.format(rom_FN.getBaseNoExt()))
            use_from_cache = False
        log_debug('use_from_cache "{}"'.format(use_from_cache))

        if use_from_cache:
            self.scraper_obj.set_candidate_from_cache(rom_FN, platform)
        else:
            # Clear all caches to remove preexiting information, just in case user is rescraping.
            self.scraper_obj.clear_cache(rom_FN, platform)

            # --- Ask user to enter ROM metadata search term ---
            # Only ask user for a search term if the scraper supports it.
            # Scrapers that do exact matches, like AEL Offline, ScreenScraper and ArcadeDB
            # do not need this so set the search term to None.
            if self.scraper_obj.supports_search_string():
                log_debug('Asking user for a search string.')
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
            else:
                log_debug('Scraper does not support search strings. Setting it to None.')
                search_term = None

            # --- Do a search and get a list of games ---
            pdialog = KodiProgressDialog()
            pdialog.startProgress('Searching games with scaper {}...'.format(scraper_name))
            candidate_list = self.scraper_obj.get_candidates(
                search_term, rom_FN, rom_checksums_FN, platform, status_dic)
            # If the there was an error/exception in the scraper return immediately.
            if not status_dic['status']: return status_dic
            # If the scraper is disabled candidate_list will be None. However, it is impossible
            # that the scraper is disabled when scraping from the context menu.
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
                    'Select game for ROM "{0}"'.format(object_dic['m_name']), game_name_list)
                if select_candidate_idx < 0:
                    status_dic['status'] = False
                    status_dic['dialog'] = KODI_MESSAGE_NOTIFY
                    status_dic['msg'] = '{0} metadata unchanged'.format(object_name)
                    return
            # log_debug('select_candidate_idx {0}'.format(select_candidate_idx))
            candidate = candidate_list[select_candidate_idx]
            log_verb('User chose game "{0}"'.format(candidate['display_name']))

            # --- Set candidate. This will introduce it in the cache ---
            self.scraper_obj.set_candidate(rom_FN, platform, candidate)

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
    EXCEPTION_COUNTER_THRESHOLD = 5
    
    # Maximum amount of retries of certain requests
    RETRY_THRESHOLD = 4

    # Disk cache types. These string will be part of the cache file names.
    CACHE_CANDIDATES = 'candidates'
    CACHE_METADATA   = 'metadata'
    CACHE_ASSETS     = 'assets'
    CACHE_INTERNAL   = 'internal'
    CACHE_LIST = [
        CACHE_CANDIDATES, CACHE_METADATA, CACHE_ASSETS, CACHE_INTERNAL,
    ]

    GLOBAL_CACHE_TGDB_GENRES     = 'TGDB_genres'
    GLOBAL_CACHE_TGDB_DEVELOPERS = 'TGDB_developers'
    GLOBAL_CACHE_LIST = [
        GLOBAL_CACHE_TGDB_GENRES, GLOBAL_CACHE_TGDB_DEVELOPERS,
    ]

    JSON_indent = 1
    JSON_separators = (',', ':')

    # --- Constructor ----------------------------------------------------------------------------
    # @param settings: [dict] Addon settings.
    def __init__(self, settings, fallbackScraper = None):
        self.settings = settings
        self.verbose_flag = False
        self.dump_file_flag = False
        self.debug_checksums_flag = False
        # Record the number of network error/exceptions. If this number is bigger than a
        # threshold disable the scraper.
        self.exception_counter = 0
        # If this is True the scraper is internally disabled. A disabled scraper alwats returns
        # empty data like the NULL scraper.
        self.scraper_disabled = False
        # Directory to store on-disk scraper caches.
        self.scraper_cache_dir = settings['scraper_cache_dir']
        # Do not log here. Otherwise the same thing will be printed for every scraper instantiated.
        # log_debug('Scraper.__init__() scraper_cache_dir "{}"'.format(self.scraper_cache_dir))

        self.last_http_call = datetime.now()
        
        # --- Disk caches ---
        self.disk_caches = {}
        self.disk_caches_loaded = {}
        self.disk_caches_dirty = {}
        for cache_name in Scraper.CACHE_LIST:
            self.disk_caches[cache_name] = {}
            self.disk_caches_loaded[cache_name] = False
            self.disk_caches_dirty[cache_name] = False
        # Candidate game is set with functions set_candidate_from_cache() or set_candidate()
        # and used by functions get_metadata() and get_assets()
        self.candidate = None

        # --- Global disk caches ---
        self.global_disk_caches = {}
        self.global_disk_caches_loaded = {}
        self.global_disk_caches_dirty = {}
        for cache_name in Scraper.GLOBAL_CACHE_LIST:
            self.global_disk_caches[cache_name] = {}
            self.global_disk_caches_loaded[cache_name] = False
            self.global_disk_caches_dirty[cache_name] = False

    # --- Methods --------------------------------------------------------------------------------
    # Scraper is much more verbose (even more than AEL Debug level).
    def set_verbose_mode(self, verbose_flag):
        log_debug('Scraper.set_verbose_mode() verbose_flag {0}'.format(verbose_flag))
        self.verbose_flag = verbose_flag

    # Dump scraper data into files for debugging. Used in the development scripts.
    def set_debug_file_dump(self, dump_file_flag, dump_dir):
        log_debug('Scraper.set_debug_file_dump() dump_file_flag {0}'.format(dump_file_flag))
        log_debug('Scraper.set_debug_file_dump() dump_dir {0}'.format(dump_dir))
        self.dump_file_flag = dump_file_flag
        self.dump_dir = dump_dir

    # ScreenScraper needs the checksum of the file scraped. This function sets the checksums
    # externally for debugging purposes, for example when debugging the scraper with
    # fake filenames.
    def set_debug_checksums(self, debug_checksums, crc_str = '', md5_str = '', sha1_str = '', size = 0):
        log_debug('Scraper.set_debug_checksums() debug_checksums {0}'.format(debug_checksums))
        self.debug_checksums_flag = debug_checksums
        self.debug_crc  = crc_str
        self.debug_md5  = md5_str
        self.debug_sha1 = sha1_str
        self.debug_size = size

    # Dump dictionary as JSON file for debugging purposes.
    # This function is used internally by the scrapers if the flag self.dump_file_flag is True.
    def _dump_json_debug(self, file_name, data_dic):
        if not self.dump_file_flag: return
        file_path = os.path.join(self.dump_dir, file_name)
        if SCRAPER_CACHE_HUMAN_JSON:
            json_str = json.dumps(data_dic, indent = 4, separators = (', ', ' : '))
        else:
            json_str = json.dumps(data_dic)
        text_dump_str_to_file(file_path, json_str)

    def _dump_file_debug(self, file_name, page_data):
        if not self.dump_file_flag: return
        file_path = os.path.join(self.dump_dir, file_name)
        text_dump_str_to_file(file_path, page_data)

    @abc.abstractmethod
    def get_name(self): pass

    @abc.abstractmethod
    def get_filename(self): pass

    @abc.abstractmethod
    def supports_disk_cache(self): pass

    @abc.abstractmethod
    def supports_search_string(self): pass

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

    # The *_candidates_cache_*() functions use the low level cache functions which are internal
    # to the Scraper object. The functions next are public, however.

    # Returns True if candidate is in disk cache, False otherwise.
    # Lazy loads candidate cache from disk.
    def check_candidates_cache(self, rom_FN, platform):
        self.cache_key = rom_FN.getBase()
        self.platform = platform

        return self._check_disk_cache(Scraper.CACHE_CANDIDATES, self.cache_key)

    # Not necesary to lazy load the cache because before calling this function
    # check_candidates_cache() must be called.
    def retrieve_from_candidates_cache(self, rom_FN, platform):
        self.cache_key = rom_FN.getBase()

        return self._retrieve_from_disk_cache(Scraper.CACHE_CANDIDATES, self.cache_key)

    def set_candidate_from_cache(self, rom_FN, platform):
        self.cache_key = rom_FN.getBase()
        self.platform  = platform
        self.candidate = self._retrieve_from_disk_cache(Scraper.CACHE_CANDIDATES, self.cache_key)

    def set_candidate(self, rom_FN, platform, candidate):
        self.cache_key = rom_FN.getBase()
        self.platform  = platform
        self.candidate = candidate
        log_debug('Scrape.set_candidate() Setting "{}" "{}"'.format(self.cache_key, platform))
        # Do not introduce None candidates in the cache so the game will be rescraped later.
        # Keep the None candidate in the object internal variables so later calls to 
        # get_metadata() and get_assets() will know an error happened.
        if candidate is None: return
        self._update_disk_cache(Scraper.CACHE_CANDIDATES, self.cache_key, candidate)
        log_debug('Scrape.set_candidate() Added "{}" to cache'.format(self.cache_key))

    # When the user decides to rescrape an item that was in the cache make sure all
    # the caches are purged.
    def clear_cache(self, rom_FN, platform):
        self.cache_key = rom_FN.getBase()
        self.platform = platform
        log_debug('Scraper.clear_cache() Clearing caches "{}" "{}"'.format(
            self.cache_key, platform))
        for cache_type in Scraper.CACHE_LIST:
            if self._check_disk_cache(cache_type, self.cache_key):
                self._delete_from_disk_cache(cache_type, self.cache_key)

    # Only write to disk non-empty caches.
    # Only write to disk dirty caches. If cache has not been modified then do not write it.
    def flush_disk_cache(self, pdialog = None):
        # If scraper does not use disk cache (notably AEL Offline) return.
        if not self.supports_disk_cache():
            log_debug('Scraper.flush_disk_cache() Scraper {} does not use disk cache.'.format(
                self.get_name()))
            return

        # Create progress dialog.
        num_steps = len(Scraper.CACHE_LIST) + len(Scraper.GLOBAL_CACHE_LIST)
        step_count = 0
        if pdialog is not None:
            pdialog.startProgress('Flushing scraper disk caches...', num_steps)

        # --- Scraper caches ---
        log_debug('Scraper.flush_disk_cache() Saving scraper {} disk cache...'.format(
            self.get_name()))
        for cache_type in Scraper.CACHE_LIST:
            if pdialog is not None:
                pdialog.updateProgress(step_count)
                step_count += 1

            # Skip unloaded caches
            if not self.disk_caches_loaded[cache_type]:
                log_debug('Skipping {} (Unloaded)'.format(cache_type))
                continue
            # Skip empty caches
            if not self.disk_caches[cache_type]:
                log_debug('Skipping {} (Empty)'.format(cache_type))
                continue
            # Skip clean caches.
            if not self.disk_caches_dirty[cache_type]:
                log_debug('Skipping {} (Clean)'.format(cache_type))
                continue

            # Get JSON data.
            json_data = json.dumps(
                self.disk_caches[cache_type], ensure_ascii = False, sort_keys = True,
                indent = Scraper.JSON_indent, separators = Scraper.JSON_separators)

            # Write to disk
            json_file_path, json_fname = self._get_scraper_file_name(cache_type, self.platform)
            file = io.open(json_file_path, 'w', encoding = 'utf-8')
            file.write(unicode(json_data))
            file.close()
            # log_debug('Saved "{}"'.format(json_file_path))
            log_debug('Saved "<SCRAPER_CACHE_DIR>/{}"'.format(json_fname))

            # Cache written to disk is clean gain.
            self.disk_caches_dirty[cache_type] = False

        # --- Global caches ---
        log_debug('Scraper.flush_disk_cache() Saving scraper {} global disk cache...'.format(
                self.get_name()))
        for cache_type in Scraper.GLOBAL_CACHE_LIST:
            if pdialog is not None:
                pdialog.updateProgress(step_count)
                step_count += 1

            # Skip unloaded caches
            if not self.global_disk_caches_loaded[cache_type]:
                log_debug('Skipping global {} (Unloaded)'.format(cache_type))
                continue
            # Skip empty caches
            if not self.global_disk_caches[cache_type]:
                log_debug('Skipping global {} (Empty)'.format(cache_type))
                continue
            # Skip clean caches.
            if not self.global_disk_caches_dirty[cache_type]:
                log_debug('Skipping global {} (Clean)'.format(cache_type))
                continue

            # Get JSON data.
            json_data = json.dumps(
                self.global_disk_caches[cache_type], ensure_ascii = False, sort_keys = True,
                indent = Scraper.JSON_indent, separators = Scraper.JSON_separators)

            # Write to disk
            json_file_path, json_fname = self._get_global_file_name(cache_type)
            file = io.open(json_file_path, 'w', encoding = 'utf-8')
            file.write(unicode(json_data))
            file.close()
            # log_debug('Saved global "{}"'.format(json_file_path))
            log_debug('Saved global "<SCRAPER_CACHE_DIR>/{}"'.format(json_fname))

            # Cache written to disk is clean gain.
            self.global_disk_caches_dirty[cache_type] = False
        if pdialog is not None: pdialog.endProgress()

    # Search for candidates and return a list of dictionaries _new_candidate_dic().
    #
    # * This function is never cached. What is cached is the chosen candidate games.
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
    # @param rom_FN: [FileName] Scraper will get whatever part of the filename they want.
    # @param rom_checksums_FN: [FileName] File to be used when computing checksums. For
    #                          multidisc ROMs rom_FN is a fake file but rom_checksums_FN is a real
    #                          file belonging to the set.
    # @param platform: [str] AEL platform.
    # @param status_dic: [dict] kodi_new_status_dic() status dictionary.
    # @return: [list] or None.
    @abc.abstractmethod
    def get_candidates(self, search_term, rom_FN, rom_checksums_FN, platform, status_dic): pass

    # Returns the metadata for a candidate (search result).
    #
    # * See comments in get_candidates()
    #
    # @param status_dic: [dict] kodi_new_status_dic() status dictionary.
    # @return: [dict] Dictionary self._new_gamedata_dic(). If no metadata found (very unlikely)
    #          then a dictionary with default values is returned. If there is an error/exception
    #          None is returned, the cause printed in the log and status_dic has a message to show.
    @abc.abstractmethod
    def get_metadata(self, status_dic): pass

    # Returns a list of assets for a candidate (search result).
    #
    # * See comments in get_candidates()
    #
    # @param status_dic: [dict] kodi_new_status_dic() status dictionary.
    # @return: [list] List of _new_assetdata_dic() dictionaries. If no assets found then an empty
    #          list is returned. If there is an error/exception None is returned, the cause printed
    #          in the log and status_dic has a message to show.
    @abc.abstractmethod
    def get_assets(self, asset_info, status_dic): pass

    # When returning the asset list with get_assets(), some sites return thumbnails images
    # because the real assets are on a single dedicated page. For this sites, resolve_asset_URL()
    # returns the true, full size URL of the asset.
    #
    # Other scrapers, for example MobyGames, return both the thumbnail and the true asset URLs
    # in get_assets(). In such case, the implementation of this method is trivial.
    #
    # @param selected_asset: 
    # @param status_dic: [dict] kodi_new_status_dic() status dictionary.
    # @return: [tuple of strings] or None 
    #          First item, string with the URL to download the asset.
    #          Second item, string with the URL for printing in logs. URL may have sensitive
    #          information in some scrapers.
    #          None is returned in case of error and status_dic updated.
    @abc.abstractmethod
    def resolve_asset_URL(self, selected_asset, status_dic): pass

    # Get the URL image extension. In some scrapers the type of asset cannot be obtained by
    # the asset URL and must be resolved to save the asset in the filesystem.
    #
    # @param selected_asset: 
    # @param image_url: 
    # @param status_dic: [dict] kodi_new_status_dic() status dictionary.
    # @return: [str] String with the image extension in lowercase 'png', 'jpg', etc.
    #          None is returned in case or error/exception and status_dic updated.
    @abc.abstractmethod
    def resolve_asset_URL_extension(self, selected_asset, image_url, status_dic): pass

    # Downloads an image from the given url to the local path.
    # Can overwrite this method in scraper implementation to support extra actions, like
    # request throttling.
    def download_image(self, image_url, image_local_path):
        # net_download_img() never prints URLs or paths.
        net_download_img(image_url, image_local_path)

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
        }

    # This functions is called when an error that is not an exception and needs to increase
    # the scraper error limit happens.
    # All messages generated in the scrapers are KODI_MESSAGE_DIALOG.
    def _handle_error(self, status_dic, user_msg):
        # Print error message to the log.
        log_error('Scraper._handle_error() user_msg "{}"'.format(user_msg))

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

    # --- Private disk cache functions -----------------------------------------------------------
    def _get_scraper_file_name(self, cache_type, platform):
        scraper_filename = self.get_filename()
        json_fname = scraper_filename + '__' + platform + '__' + cache_type + '.json'
        json_full_path = os.path.join(self.scraper_cache_dir, json_fname).decode('utf-8')

        return json_full_path, json_fname

    def _lazy_load_disk_cache(self, cache_type):
        if not self.disk_caches_loaded[cache_type]:
            self._load_disk_cache(cache_type, self.platform)

    def _load_disk_cache(self, cache_type, platform):
        # --- Get filename ---
        json_file_path, json_fname = self._get_scraper_file_name(cache_type, platform)
        log_debug('Scraper._load_disk_cache() Loading cache "{}"'.format(cache_type))

        # --- Load cache if file exists ---
        if os.path.isfile(json_file_path):
            file = open(json_file_path)
            file_contents = file.read()
            file.close()
            self.disk_caches[cache_type] = json.loads(file_contents)
            # log_debug('Loaded "{}"'.format(json_file_path))
            log_debug('Loaded "<SCRAPER_CACHE_DIR>/{}"'.format(json_fname))
        else:
            log_debug('Cache file not found. Resetting cache.')
            self.disk_caches[cache_type] = {}
        self.disk_caches_loaded[cache_type] = True
        self.disk_caches_dirty[cache_type] = False

    # Returns True if item is in the cache, False otherwise.
    # Lazy loads cache files from disk.
    def _check_disk_cache(self, cache_type, cache_key):
        self._lazy_load_disk_cache(cache_type)

        return True if cache_key in self.disk_caches[cache_type] else False

    # _check_disk_cache() must be called before this.
    def _retrieve_from_disk_cache(self, cache_type, cache_key):
        return self.disk_caches[cache_type][cache_key]

    # _check_disk_cache() must be called before this.
    def _delete_from_disk_cache(self, cache_type, cache_key):
        del self.disk_caches[cache_type][cache_key]
        self.disk_caches_dirty[cache_type] = True

    # Lazy loading should be done here because the internal cache for ScreenScraper
    # could be updated withouth being loaded first with _check_disk_cache().
    def _update_disk_cache(self, cache_type, cache_key, data):
        self._lazy_load_disk_cache(cache_type)
        self.disk_caches[cache_type][cache_key] = data
        self.disk_caches_dirty[cache_type] = True

    # --- Private global disk caches -------------------------------------------------------------
    def _get_global_file_name(self, cache_type):
        json_fname = cache_type + '.json'
        json_full_path = os.path.join(self.scraper_cache_dir, json_fname).decode('utf-8')

        return json_full_path, json_fname

    def _lazy_load_global_disk_cache(self, cache_type):
        if not self.global_disk_caches_loaded[cache_type]:
            self._load_global_cache(cache_type)

    def _load_global_cache(self, cache_type):
        # --- Get filename ---
        json_file_path, json_fname = self._get_global_file_name(cache_type)
        log_debug('Scraper._load_global_cache() Loading cache "{}"'.format(cache_type))

        # --- Load cache if file exists ---
        if os.path.isfile(json_file_path):
            file = open(json_file_path)
            file_contents = file.read()
            file.close()
            self.global_disk_caches[cache_type] = json.loads(file_contents)
            # log_debug('Loaded "{}"'.format(json_file_path))
            log_debug('Loaded "<SCRAPER_CACHE_DIR>/{}"'.format(json_fname))
        else:
            log_debug('Cache file not found. Resetting cache.')
            self.global_disk_caches[cache_type] = {}
        self.global_disk_caches_loaded[cache_type] = True
        self.global_disk_caches_dirty[cache_type] = False

    def _check_global_cache(self, cache_type):
        self._lazy_load_global_disk_cache(cache_type)

        return self.global_disk_caches[cache_type]

    # _check_global_cache() must be called before this.
    def _retrieve_global_cache(self, cache_type):
        return self.global_disk_caches[cache_type]

    # _check_global_cache() must be called before this.
    def _reset_global_cache(self, cache_type):
        self.global_disk_caches[cache_type] = {}
        self.global_disk_caches_dirty[cache_type] = True

    def _update_global_cache(self, cache_type, data):
        self._lazy_load_global_disk_cache(cache_type)
        self.global_disk_caches[cache_type] = data
        self.global_disk_caches_dirty[cache_type] = True

    # Generic waiting method to avoid too many requests
    # and website abuse. 
    def _wait_for_API_request(self, wait_time_in_miliseconds = 1000):
        if wait_time_in_miliseconds == 0:
            return
        
        # Make sure we dont go over the TooManyRequests limit of 1 second.
        now = datetime.now()
        if (now - self.last_http_call).total_seconds() * 1000 < wait_time_in_miliseconds:
            log_debug('Scraper._wait_for_API_request() Sleeping {}ms to avoid overloading...'.format(wait_time_in_miliseconds))
            time.sleep(wait_time_in_miliseconds / 1000)
            
# ------------------------------------------------------------------------------------------------
# NULL scraper, does nothing.
# ------------------------------------------------------------------------------------------------
class Null_Scraper(Scraper):
    # @param settings: [dict] Addon settings. Particular scraper settings taken from here.
    def __init__(self, settings): super(Null_Scraper, self).__init__(settings)

    def get_name(self): return 'Null'

    def get_filename(self): return 'Null'

    def supports_disk_cache(self): return False

    def supports_search_string(self): return True

    def supports_metadata_ID(self, metadata_ID): return False

    def supports_metadata(self): return False

    def supports_asset_ID(self, asset_ID): return False

    def supports_assets(self): return False

    def check_before_scraping(self, status_dic): return status_dic

    # Null scraper never finds candidates.
    def get_candidates(self, search_term, rom_FN, rom_checksums_FN, platform, status_dic): return []

    # Null scraper never returns valid scraped metadata.
    def get_metadata(self, status_dic): return self._new_gamedata_dic()

    def get_assets(self, asset_info, status_dic): return []

    def resolve_asset_URL(self, selected_asset, status_dic): return ('', '')

    def resolve_asset_URL_extension(self, selected_asset, image_url, status_dic): return ''

    def download_image(self, image_url, image_local_path): pass
    
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
        log_debug('AEL_Offline.__init__() Setting addon dir "{}"'.format(self.addon_dir))

        # --- Cached TGDB metadata ---
        self._reset_cached_games()

        # --- Pass down common scraper settings ---
        super(AEL_Offline, self).__init__(settings)

    # --- Base class abstract methods ------------------------------------------------------------
    def get_name(self): return 'AEL Offline'

    def get_filename(self): return 'AEL_Offline'

    def supports_disk_cache(self): return False

    def supports_search_string(self): return False

    def supports_metadata_ID(self, metadata_ID):
        return True if metadata_ID in ScreenScraper.supported_metadata_list else False

    def supports_metadata(self): return True

    def supports_asset_ID(self, asset_ID): return False

    def supports_assets(self): return False

    def check_before_scraping(self, status_dic): return status_dic

    # Search term is always None for this scraper.
    def get_candidates(self, search_term, rom_FN, rom_checksums_FN, platform, status_dic):
        # AEL Offline cannot be disabled.
        # Prepare data for scraping.
        rombase_noext = rom_FN.getBaseNoExt()
        log_debug('AEL_Offline.get_candidates() rombase_noext "{0}"'.format(rombase_noext))
        log_debug('AEL_Offline.get_candidates() AEL platform  "{0}"'.format(platform))

        # If not cached XML data found (maybe offline scraper does not exist for this platform or 
        # cannot be loaded) return an empty list of candidates.
        self._initialise_platform(platform)
        if not self.cached_games: return []

        if platform == 'MAME':
            # --- Search MAME games ---
            candidate_list = self._get_MAME_candidates(rombase_noext, platform)
        else:
            # --- Search No-Intro games ---
            candidate_list = self._get_NoIntro_candidates(rombase_noext, platform)

        return candidate_list

    def get_metadata(self, status_dic):
        gamedata = self._new_gamedata_dic()

        if self.cached_platform == 'MAME':
            # --- MAME scraper ---
            key_id = self.candidate['id']
            log_verb("AEL_Offline.get_metadata() Mode MAME id = '{0}'".format(key_id))
            gamedata['title']     = self.cached_games[key_id]['description']
            gamedata['year']      = self.cached_games[key_id]['year']
            gamedata['genre']     = self.cached_games[key_id]['genre']
            gamedata['developer'] = self.cached_games[key_id]['manufacturer']
        elif self.cached_platform == 'Unknown':
            # --- Unknown platform. Behave like NULL scraper ---
            log_verb("AEL_Offline.get_metadata() Mode Unknown. Doing nothing.")
        else:
            # --- No-Intro scraper ---
            key_id = self.candidate['id']
            log_verb("AEL_Offline.get_metadata() Mode No-Intro id = '{0}'".format(key_id))
            gamedata['title']     = self.cached_games[key_id]['description']
            gamedata['year']      = self.cached_games[key_id]['year']
            gamedata['genre']     = self.cached_games[key_id]['genre']
            gamedata['developer'] = self.cached_games[key_id]['manufacturer']
            gamedata['nplayers']  = self.cached_games[key_id]['player']
            gamedata['esrb']      = self.cached_games[key_id]['rating']
            gamedata['plot']      = self.cached_games[key_id]['story']

        return gamedata

    def get_assets(self, asset_info, status_dic): return []

    def resolve_asset_URL(self, selected_asset, status_dic): pass

    def resolve_asset_URL_extension(self, selected_asset, image_url, status_dic): pass
        
    # --- This class own methods -----------------------------------------------------------------
    def _get_MAME_candidates(self, rombase_noext, platform):
        log_verb("AEL_Offline._get_MAME_candidates() Scraper working in MAME mode.")

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

    def _get_NoIntro_candidates(self, rombase_noext, platform):
        # --- First try an exact match using rombase_noext ---
        log_verb("AEL_Offline._get_NoIntro_candidates() Scraper working in No-Intro mode.")
        log_verb("AEL_Offline._get_NoIntro_candidates() Trying exact search for '{0}'".format(
            rombase_noext))
        candidate_list = []
        if rombase_noext in self.cached_games:
            log_verb("AEL_Offline._get_NoIntro_candidates() Exact match found.")
            candidate = self._new_candidate_dic()
            candidate['id'] = rombase_noext
            candidate['display_name'] = self.cached_games[rombase_noext]['name']
            candidate['platform'] = platform
            candidate['scraper_platform'] = platform
            candidate['order'] = 1
            candidate_list.append(candidate)
        else:
            # --- If nothing found, do a fuzzy search ---
            # Here implement a Levenshtein distance algorithm.
            search_term = text_format_ROM_name_for_scraping(rombase_noext)
            log_verb("AEL_Offline._get_NoIntro_candidates() No exact match found.")
            log_verb("AEL_Offline._get_NoIntro_candidates() Trying fuzzy search '{0}'".format(
                search_term))
            search_string_lower = rombase_noext.lower()
            regexp = '.*{}.*'.format(search_string_lower)
            try:
                # Sometimes this produces: raise error, v # invalid expression
                p = re.compile(regexp)
            except:
                log_info('AEL_Offline._get_NoIntro_candidates() Exception in re.compile(regexp)')
                log_info('AEL_Offline._get_NoIntro_candidates() regexp = "{0}"'.format(regexp))
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
            log_debug('AEL_Offline._initialise_platform() platform = "{0}" is cached in object.'.format(
                platform))
            return
        else:
            log_debug('AEL_Offline._initialise_platform() platform = "{0}" not cached. Loading XML.'.format(
                platform))

        # What if platform is not in the official list dictionary? Then load
        # nothing and behave like the NULL scraper.
        try:
            xml_file = platform_AEL_to_Offline_GameDBInfo_XML[platform]
        except:
            log_debug('AEL_Offline._initialise_platform() Platform {0} not found'.format(platform))
            log_debug('AEL_Offline._initialise_platform() Defaulting to Unknown')
            self._reset_cached_games()
            return

        # Load XML database and keep it in memory for subsequent calls
        xml_path = os.path.join(self.addon_dir, xml_file)
        # log_debug('AEL_Offline._initialise_platform() Loading XML {0}'.format(xml_path))
        self.cached_games = audit_load_OfflineScraper_XML(xml_path)
        if not self.cached_games:
            self._reset_cached_games()
            return
        self.cached_xml_path = xml_path
        self.cached_platform = platform
        log_debug('AEL_Offline._initialise_platform() cached_xml_path = {0}'.format(self.cached_xml_path))
        log_debug('AEL_Offline._initialise_platform() cached_platform = {0}'.format(self.cached_platform))

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

    def get_filename(self): return 'TGDB'

    def supports_disk_cache(self): return True

    def supports_search_string(self): return True

    def supports_metadata_ID(self, metadata_ID):
        return True if metadata_ID in TheGamesDB.supported_metadata_list else False

    def supports_metadata(self): return True

    def supports_asset_ID(self, asset_ID):
        return True if asset_ID in TheGamesDB.supported_asset_list else False

    def supports_assets(self): return True

    # TGDB does not require any API keys. By default status_dic is configured for successful
    # operation so return it as it is.
    def check_before_scraping(self, status_dic): return status_dic

    def get_candidates(self, search_term, rom_FN, rom_checksums_FN, platform, status_dic):
        # If the scraper is disabled return None and do not mark error in status_dic.
        # Candidate will not be introduced in the disk cache and will be scraped again.
        if self.scraper_disabled:
            log_debug('TheGamesDB.get_candidates() Scraper disabled. Returning empty data.')
            return None

        # Prepare data for scraping.
        rombase_noext = rom_FN.getBaseNoExt()

        # --- Get candidates ---
        scraper_platform = AEL_platform_to_TheGamesDB(platform)
        log_debug('TheGamesDB.get_candidates() search_term         "{0}"'.format(search_term))
        log_debug('TheGamesDB.get_candidates() rombase_noext       "{0}"'.format(rombase_noext))
        log_debug('TheGamesDB.get_candidates() AEL platform        "{0}"'.format(platform))
        log_debug('TheGamesDB.get_candidates() TheGamesDB platform "{0}"'.format(scraper_platform))
        candidate_list = self._search_candidates(
            search_term, platform, scraper_platform, status_dic)
        if not status_dic['status']: return None

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
    def get_metadata(self, status_dic):
        # --- If scraper is disabled return immediately and silently ---
        if self.scraper_disabled:
            log_debug('TheGamesDB.get_metadata() Scraper disabled. Returning empty data.')
            return self._new_gamedata_dic()

        # --- Check if search term is in the cache ---
        if self._check_disk_cache(Scraper.CACHE_METADATA, self.cache_key):
            log_debug('TheGamesDB.get_metadata() Metadata cache hit "{0}"'.format(self.cache_key))
            return self._retrieve_from_disk_cache(Scraper.CACHE_METADATA, self.cache_key)

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
        log_debug('TheGamesDB.get_metadata() Metadata cache miss "{0}"'.format(self.cache_key))
        url_a = 'https://api.thegamesdb.net/v1/Games/ByGameID?apikey={0}&id={1}'
        url_b = '&fields=players%2Cgenres%2Coverview%2Crating'
        url_a = url_a.format(self._get_API_key(), self.candidate['id'])
        url = url_a + url_b
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('TGDB_get_metadata.json', json_data)

        # --- Parse game page data ---
        log_debug('TheGamesDB.get_metadata() Parsing game metadata...')
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
        log_debug('TheGamesDB.get_metadata() Adding to metadata cache "{0}"'.format(self.cache_key))
        self._update_disk_cache(Scraper.CACHE_METADATA, self.cache_key, gamedata)

        return gamedata
 
    # This function may be called many times in the ROM Scanner. All calls to this function
    # must be cached. See comments for this function in the Scraper abstract class.
    def get_assets(self, asset_info, status_dic):
        # --- If scraper is disabled return immediately and silently ---
        if self.scraper_disabled:
            log_debug('TheGamesDB.get_assets() Scraper disabled. Returning empty data.')
            return []

        log_debug('TheGamesDB.get_assets() Getting assets {} (ID {}) for candidate ID "{}"'.format(
            asset_info.name, asset_info.id, self.candidate['id']))

        # --- Request is not cached. Get candidates and introduce in the cache ---
        # Get all assets for candidate. _scraper_get_assets_all() caches all assets for a
        # candidate. Then select asset of a particular type.
        all_asset_list = self._retrieve_all_assets(self.candidate, status_dic)
        if not status_dic['status']: return None
        asset_list = [asset_dic for asset_dic in all_asset_list if asset_dic['asset_ID'] == asset_info.id]
        log_debug('TheGamesDB::get_assets() Total assets {0} / Returned assets {1}'.format(
            len(all_asset_list), len(asset_list)))

        return asset_list

    def resolve_asset_URL(self, selected_asset, status_dic):
        url = selected_asset['url']
        url_log = self._clean_URL_for_log(url)

        return url, url_log

    def resolve_asset_URL_extension(self, selected_asset, image_url, status_dic):
        return text_get_URL_extension(image_url)

    # --- This class own methods -----------------------------------------------------------------
    def debug_get_platforms(self, status_dic):
        log_debug('TheGamesDB.debug_get_platforms() BEGIN...')
        url = 'https://api.thegamesdb.net/v1/Platforms?apikey={}'.format(self._get_API_key())
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('TGDB_get_platforms.json', json_data)

        return json_data

    def debug_get_genres(self, status_dic):
        log_debug('TheGamesDB.debug_get_genres() BEGIN...')
        url = 'https://api.thegamesdb.net/v1/Genres?apikey={}'.format(self._get_API_key())
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('TGDB_get_genres.json', json_data)

        return json_data

    # Always use the developer public key which is limited per IP address. This function
    # may return the private key during scraper development for debugging purposes.
    def _get_API_key(self): return self.api_public_key

    # --- Retrieve list of games ---
    def _search_candidates(self, search_term, platform, scraper_platform, status_dic):
        # quote_plus() will convert the spaces into '+'. Note that quote_plus() requires an
        # UTF-8 encoded string and does not work with Unicode strings.
        # https://stackoverflow.com/questions/22415345/using-pythons-urllib-quote-plus-on-utf-8-strings-with-safe-arguments
        search_string_encoded = urllib.quote_plus(search_term.encode('utf8'))
        url_a = 'https://api.thegamesdb.net/v1/Games/ByGameName?'
        url_b = 'apikey={0}&name={1}&filter[platform]={2}'.format(
            self._get_API_key(), search_string_encoded, scraper_platform)
        url = url_a + url_b
        # _retrieve_games_from_url() may load files recursively from several pages so this code
        # must be in a separate function.
        candidate_list = self._retrieve_games_from_url(
            url, search_term, platform, scraper_platform, status_dic)
        if not status_dic['status']: return None

        # --- Sort game list based on the score. High scored candidates go first ---
        candidate_list.sort(key = lambda result: result['order'], reverse = True)

        return candidate_list

    # Return a list of candiate games.
    # Return None if error/exception.
    # Return empty list if no candidates found.
    def _retrieve_games_from_url(self, url, search_term, platform, scraper_platform, status_dic):
        # --- Get URL data as JSON ---
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        # If status_dic mark an error there was an exception. Return None.
        if not status_dic['status']: return None
        # If no games were found status_dic['status'] is True and json_data is None.
        # Return empty list of candidates.
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
            # Candidate platform may be different from scraper_platform if scraper_platform = 0
            # Always trust TGDB API about the platform of the returned candidates.
            candidate['scraper_platform'] = item['platform']
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
            log_debug('TheGamesDB._retrieve_games_from_url() Recursively loading game page')
            candidate_list = candidate_list + self._retrieve_games_from_url(
                next_url, search_term, platform, scraper_platform, status_dic)
            if not status_dic['status']: return None

        return candidate_list

    # Not used at the moment, I think.
    def _cleanup_searchterm(self, search_term, rom_path, rom):
        altered_term = search_term.lower().strip()
        for ext in self.launcher.get_rom_extensions():
            altered_term = altered_term.replace(ext, '')
        return altered_term

    # Search for the game title.
    # "noms" : [
    #     { "text" : "Super Mario World", "region" : "ss" },
    #     { "text" : "Super Mario World", "region" : "us" },
    #     ...
    # ]
    def _parse_metadata_title(self, jeu_dic):
        if 'game_title' in jeu_dic and jeu_dic['game_title'] is not None:
            title_str = jeu_dic['game_title']
        else:
            title_str = DEFAULT_META_TITLE

        return title_str

    def _parse_metadata_year(self, online_data):
        if 'release_date' in online_data and online_data['release_date'] is not None and \
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
        # Convert integers to strings because the cached genres dictionary keys are strings.
        # This is because a JSON limitation.
        genre_ids = [str(id) for id in genre_ids]
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
        # Convert integers to strings because the cached genres dictionary keys are strings.
        # This is because a JSON limitation.
        developers_ids = [str(id) for id in developers_ids]
        TGDB_developers = self._retrieve_developers(status_dic)
        if not status_dic['status']: return None
        developer_list = [TGDB_developers[dev_id] for dev_id in developers_ids]

        return ', '.join(developer_list)

    def _parse_metadata_nplayers(self, online_data):
        if 'players' in online_data and online_data['players'] is not None:
            nplayers_str = str(online_data['players'])
        else:
            nplayers_str = DEFAULT_META_NPLAYERS

        return nplayers_str

    def _parse_metadata_esrb(self, online_data):
        if 'rating' in online_data and online_data['rating'] is not None:
            esrb_str = online_data['rating']
        else:
            esrb_str = DEFAULT_META_ESRB

        return esrb_str

    def _parse_metadata_plot(self, online_data):
        if 'overview' in online_data and online_data['overview'] is not None:
            plot_str = online_data['overview']
        else:
            plot_str = DEFAULT_META_PLOT

        return plot_str

    # Get a dictionary of TGDB genres (integers) to AEL genres (strings).
    # TGDB genres are cached in an object variable.
    def _retrieve_genres(self, status_dic):
        # --- Cache hit ---
        if self._check_global_cache(Scraper.GLOBAL_CACHE_TGDB_GENRES):
            log_debug('TheGamesDB._retrieve_genres() Genres global cache hit.')
            return self._retrieve_global_cache(Scraper.GLOBAL_CACHE_TGDB_GENRES)

        # --- Cache miss. Retrieve data ---
        log_debug('TheGamesDB._retrieve_genres() Genres global cache miss. Retrieving genres...')
        url = 'https://api.thegamesdb.net/v1/Genres?apikey={}'.format(self._get_API_key())
        page_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('TGDB_get_genres.json', page_data)

        # --- Update cache ---
        genres = {}
        # Keep genres dictionary keys as strings and not integers. Otherwise, Python json
        # module will conver the integers to strings.
        # https://stackoverflow.com/questions/1450957/pythons-json-module-converts-int-dictionary-keys-to-strings/34346202
        for genre_id in page_data['data']['genres']:
            genres[genre_id] = page_data['data']['genres'][genre_id]['name']
        log_debug('TheGamesDB._retrieve_genres() There are {} genres'.format(len(genres)))
        self._update_global_cache(Scraper.GLOBAL_CACHE_TGDB_GENRES, genres)

        return genres

    def _retrieve_developers(self, status_dic):
        # --- Cache hit ---
        if self._check_global_cache(Scraper.GLOBAL_CACHE_TGDB_DEVELOPERS):
            log_debug('TheGamesDB._retrieve_developers() Genres global cache hit.')
            return self._retrieve_global_cache(Scraper.GLOBAL_CACHE_TGDB_DEVELOPERS)

        # --- Cache miss. Retrieve data ---
        log_debug('TheGamesDB._retrieve_developers() Developers global cache miss. Retrieving developers...')
        url = 'https://api.thegamesdb.net/v1/Developers?apikey={}'.format(self._get_API_key())
        page_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('TGDB_get_developers.json', page_data)

        # --- Update cache ---
        developers = {}
        for developer_id in page_data['data']['developers']:
            developers[developer_id] = page_data['data']['developers'][developer_id]['name']
        log_debug('TheGamesDB._retrieve_developers() There are {} developers'.format(len(developers)))
        self._update_global_cache(Scraper.GLOBAL_CACHE_TGDB_DEVELOPERS, developers)

        return developers

    # Publishers is not used in AEL at the moment.
    # THIS FUNCTION CODE MUST BE UPDATED.
    def _retrieve_publishers(self, publisher_ids):
        if publisher_ids is None: return ''
        if self.publishers_cached is None:
            log_debug('TheGamesDB:: No cached publishers. Retrieving from online.')
            url = 'https://api.thegamesdb.net/v1/Publishers?apikey={}'.format(self._get_API_key())
            page_data_raw = net_get_URL(url, self._clean_URL_for_log(url))
            publishers_json = json.loads(page_data_raw)
            self.publishers_cached = {}
            for publisher_id in publishers_json['data']['publishers']:
                self.publishers_cached[int(publisher_id)] = publishers_json['data']['publishers'][publisher_id]['name']
        publisher_names = [self.publishers_cached[publisher_id] for publisher_id in publisher_ids]

        return ' / '.join(publisher_names)

    # Get ALL available assets for game.
    # Cache all assets in the internal disk cache.
    def _retrieve_all_assets(self, candidate, status_dic):
        # --- Cache hit ---
        if self._check_disk_cache(Scraper.CACHE_INTERNAL, self.cache_key):
            log_debug('TheGamesDB._retrieve_all_assets() Internal cache hit "{0}"'.format(self.cache_key))
            return self._retrieve_from_disk_cache(Scraper.CACHE_INTERNAL, self.cache_key)

        # --- Cache miss. Retrieve data and update cache ---
        log_debug('TheGamesDB._retrieve_all_assets() Internal cache miss "{0}"'.format(self.cache_key))
        url = 'https://api.thegamesdb.net/v1/Games/Images?apikey={}&games_id={}'.format(
            self._get_API_key(), candidate['id'])
        asset_list = self._retrieve_assets_from_url(url, candidate['id'], status_dic)
        if not status_dic['status']: return None
        log_debug('A total of {0} assets found for candidate ID {1}'.format(
            len(asset_list), candidate['id']))

        # --- Put metadata in the cache ---
        log_debug('TheGamesDB._retrieve_all_assets() Adding to internal cache "{0}"'.format(self.cache_key))
        self._update_disk_cache(Scraper.CACHE_INTERNAL, self.cache_key, asset_list)

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
                log_debug('TheGamesDB. Found Asset {0}'.format(asset_data['name']))
            assets_list.append(asset_data)

        # --- Recursively load more assets ---
        next_url = page_data['pages']['next']
        if next_url is not None:
            log_debug('TheGamesDB._retrieve_assets_from_url() Recursively loading assets page')
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
    # TGDB API info https://api.thegamesdb.net/
    #
    # * When the API number of calls is exhausted TGDB ...
    # * When a game search is not succesfull TGDB returns valid JSON with an empty list.
    def _retrieve_URL_as_JSON(self, url, status_dic):
        page_data_raw, http_code = net_get_URL(url, self._clean_URL_for_log(url))

        # --- Check HTTP error codes ---
        if http_code != 200:
            try:
                json_data = json.loads(page_data_raw)
                error_msg = json_data['message']
            except:
                error_msg = 'Unknown/unspecified error.'
            log_error('TGDB msg "{}"'.format(error_msg))
            self._handle_error(status_dic, 'HTTP code {} message "{}"'.format(http_code, error_msg))
            return None

        # If page_data_raw is None at this point is because of an exception in net_get_URL()
        # which is not urllib2.HTTPError.
        if page_data_raw is None:
            self._handle_error(status_dic, 'TGDB: Network error in net_get_URL()')
            return None

        # Convert data to JSON.
        try:
            json_data = json.loads(page_data_raw)
        except Exception as ex:
            self._handle_exception(ex, status_dic, 'Error decoding JSON data from TGDB.')
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
        if not extra_allowance:
            extra_allowance = 0
            
        log_debug('TheGamesDB::_check_overloading() remaining_monthly_allowance = {}'.format(remaining_monthly_allowance))
        log_debug('TheGamesDB::_check_overloading() extra_allowance = {}'.format(extra_allowance))
        total_allowance = remaining_monthly_allowance + extra_allowance
        
        if total_allowance > 0: return
        log_error('TheGamesDB::_check_overloading() remaining total allowance <= 0')
        log_error('Disabling TGDB scraper.')
        self.scraper_disabled = True
        status_dic['status'] = False
        status_dic['dialog'] = KODI_MESSAGE_DIALOG
        status_dic['msg'] = 'TGDB monthly/total allowance is {}. Scraper disabled.'.format(
            total_allowance)

# ------------------------------------------------------------------------------------------------
# MobyGames online scraper.
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
    ]
    asset_name_mapping = {
        'front cover'   : ASSET_BOXFRONT_ID,
        'back cover'    : ASSET_BOXBACK_ID,
        'media'         : ASSET_CARTRIDGE_ID,
        'manual'        : None,
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
        # --- Pass down common scraper settings ---
        super(MobyGames, self).__init__(settings)

    # --- Base class abstract methods ------------------------------------------------------------
    def get_name(self): return 'MobyGames'

    def get_filename(self): return 'MobyGames'

    def supports_disk_cache(self): return True

    def supports_search_string(self): return True

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
            log_error('MobyGames.check_before_scraping() MobiGames API key looks OK.')
            return
        log_error('MobyGames.check_before_scraping() MobiGames API key not configured.')
        log_error('MobyGames.check_before_scraping() Disabling MobyGames scraper.')
        self.scraper_disabled = True
        status_dic['status'] = False
        status_dic['dialog'] = KODI_MESSAGE_DIALOG
        status_dic['msg'] = (
            'AEL requires your MobyGames API key. '
            'Visit https://www.mobygames.com/info/api for directions about how to get your key '
            'and introduce the API key in AEL addon settings.'
        )

    def get_candidates(self, search_term, rom_FN, rom_checksums_FN, platform, status_dic):
        # --- If scraper is disabled return immediately and silently ---
        if self.scraper_disabled:
            # If the scraper is disabled return None and do not mark error in status_dic.
            log_debug('MobyGames.get_candidates() Scraper disabled. Returning empty data.')
            return None

        # Prepare data for scraping.
        rombase_noext = rom_FN.getBaseNoExt()

        # --- Request is not cached. Get candidates and introduce in the cache ---
        scraper_platform = AEL_platform_to_MobyGames(platform)
        log_debug('MobyGames.get_candidates() search_term        "{0}"'.format(search_term))
        log_debug('MobyGames.get_candidates() rombase_noext      "{0}"'.format(rombase_noext))
        log_debug('MobyGames.get_candidates() AEL platform       "{0}"'.format(platform))
        log_debug('MobyGames.get_candidates() MobyGames platform "{0}"'.format(scraper_platform))
        candidate_list = self._search_candidates(
            search_term, platform, scraper_platform, status_dic)
        if not status_dic['status']: return None

        return candidate_list

    # This function may be called many times in the ROM Scanner. All calls to this function
    # must be cached. See comments for this function in the Scraper abstract class.
    def get_metadata(self, status_dic):
        # --- If scraper is disabled return immediately and silently ---
        if self.scraper_disabled:
            log_debug('MobyGames.get_metadata() Scraper disabled. Returning empty data.')
            return self._new_gamedata_dic()

        # --- Check if search term is in the cache ---
        if self._check_disk_cache(Scraper.CACHE_METADATA, self.cache_key):
            log_debug('MobyGames.get_metadata() Metadata cache hit "{0}"'.format(self.cache_key))
            return self._retrieve_from_disk_cache(Scraper.CACHE_METADATA, self.cache_key)

        # --- Request is not cached. Get candidates and introduce in the cache ---
        log_debug('MobyGames.get_metadata() Metadata cache miss "{0}"'.format(self.cache_key))
        url = 'https://api.mobygames.com/v1/games/{}?api_key={}'.format(self.candidate['id'], self.api_key)
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('MobyGames_get_metadata.json', json_data)

        # --- Parse game page data ---
        gamedata = self._new_gamedata_dic()
        gamedata['title'] = self._parse_metadata_title(json_data)
        gamedata['year']  = self._parse_metadata_year(json_data, self.candidate['scraper_platform'])
        gamedata['genre'] = self._parse_metadata_genre(json_data)
        gamedata['plot']  = self._parse_metadata_plot(json_data)

        # --- Put metadata in the cache ---
        log_debug('MobyGames.get_metadata() Adding to metadata cache "{0}"'.format(self.cache_key))
        self._update_disk_cache(Scraper.CACHE_METADATA, self.cache_key, gamedata)

        return gamedata

    # This function may be called many times in the ROM Scanner. All calls to this function
    # must be cached. See comments for this function in the Scraper abstract class.
    #
    # In the MobyGames scraper is convenient to grab all the available assets for a candidate,
    # cache the assets, and then select the assets of a specific type from the cached list.
    def get_assets(self, asset_info, status_dic):
        # --- If scraper is disabled return immediately and silently ---
        if self.scraper_disabled:
            log_debug('MobyGames.get_assets() Scraper disabled. Returning empty data.')
            return []

        log_debug('MobyGames.get_assets() Getting assets {} (ID {}) for candidate ID "{}"'.format(
            asset_info.name, asset_info.id, self.candidate['id']))

        # --- Request is not cached. Get candidates and introduce in the cache ---
        # Get all assets for candidate. _retrieve_all_assets() caches all assets for a candidate.
        # Then select asset of a particular type.
        all_asset_list = self._retrieve_all_assets(self.candidate, status_dic)
        if not status_dic['status']: return None
        asset_list = [asset_dic for asset_dic in all_asset_list if asset_dic['asset_ID'] == asset_info.id]
        log_debug('MobyGames::get_assets() Total assets {0} / Returned assets {1}'.format(
            len(all_asset_list), len(asset_list)))

        return asset_list

    # Mobygames returns both the asset thumbnail URL and the full resolution URL so in
    # this scraper this method is trivial.
    def resolve_asset_URL(self, selected_asset, status_dic):
        # Transform http to https
        url = selected_asset['url']
        if url[0:4] == 'http': url = 'https' + url[4:]
        url_log = self._clean_URL_for_log(url)

        return url, url_log

    def resolve_asset_URL_extension(self, selected_asset, image_url, status_dic):
        return text_get_URL_extension(image_url)

    def download_image(self, image_url, image_local_path):
        self._wait_for_API_request()
        # net_download_img() never prints URLs or paths.
        net_download_img(image_url, image_local_path)
        
        # failed? retry after 5 seconds
        if not image_local_path.exists():
            log_debug('Download failed. Retry after 5 seconds')
            self._wait_for_API_request(5000)
            net_download_img(image_url, image_local_path)
        
    # --- This class own methods -----------------------------------------------------------------
    def debug_get_platforms(self, status_dic):
        log_debug('MobyGames.debug_get_platforms() BEGIN...')
        url_str = 'https://api.mobygames.com/v1/platforms?api_key={}'
        url = url_str.format(self.api_key)
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('MobyGames_get_platforms.json', json_data)

        return json_data

    # --- Retrieve list of games ---
    def _search_candidates(self, search_term, platform, scraper_platform, status_dic):
        # --- Retrieve JSON data with list of games ---
        search_string_encoded = urllib.quote_plus(search_term.encode('utf8'))
        if scraper_platform == '0':
            # Unkwnon or wrong platform case.
            url_str = 'https://api.mobygames.com/v1/games?api_key={}&format=brief&title={}'
            url = url_str.format(self.api_key, search_string_encoded)
        else:
            url_str = 'https://api.mobygames.com/v1/games?api_key={}&format=brief&title={}&platform={}'
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
        for platform in platform_data:
            if platform['platform_id'] == int(scraper_platform):
                return platform['first_release_date'][0:4]

        # If platform not found then take first result.
        return platform_data[0]['first_release_date'][0:4]

    def _parse_metadata_genre(self, json_data):
        if 'genres' in json_data:
            genre_names = []
            for genre in json_data['genres']: genre_names.append(genre['genre_name'])
            genre_str = ', '.join(genre_names)
        else:
            genre_str = DEFAULT_META_GENRE

        return genre_str

    def _parse_metadata_plot(self, json_data):
        if 'description' in json_data and json_data['description'] is not None:
            plot_str = json_data['description']
            plot_str = text_remove_HTML_tags(plot_str) # Clean HTML tags like <i>, </i>
        else:
            plot_str = DEFAULT_META_PLOT

        return plot_str

    # Get ALL available assets for game.
    # Cache all assets in the internal disk cache.
    def _retrieve_all_assets(self, candidate, status_dic):
        # --- Cache hit ---
        if self._check_disk_cache(Scraper.CACHE_INTERNAL, self.cache_key):
            log_debug('MobyGames._retrieve_all_assets() Internal cache hit "{0}"'.format(self.cache_key))
            return self._retrieve_from_disk_cache(Scraper.CACHE_INTERNAL, self.cache_key)

        # --- Cache miss. Retrieve data and update cache ---
        log_debug('MobyGames._retrieve_all_assets() Internal cache miss "{0}"'.format(self.cache_key))
        snap_assets = self._retrieve_snap_assets(candidate, candidate['scraper_platform'], status_dic)
        if not status_dic['status']: return None
        cover_assets = self._retrieve_cover_assets(candidate, candidate['scraper_platform'], status_dic)
        if not status_dic['status']: return None
        asset_list = snap_assets + cover_assets
        log_debug('MobyGames._retrieve_all_assets() A total of {0} assets found for candidate ID {1}'.format(
            len(asset_list), candidate['id']))

        # --- Put metadata in the cache ---
        log_debug('MobyGames._retrieve_all_assets() Adding to internal cache "{0}"'.format(self.cache_key))
        self._update_disk_cache(Scraper.CACHE_INTERNAL, self.cache_key, asset_list)

        return asset_list

    def _retrieve_snap_assets(self, candidate, platform_id, status_dic):
        log_debug('MobyGames._retrieve_snap_assets() Getting Snaps...')
        url = 'https://api.mobygames.com/v1/games/{}/platforms/{}/screenshots?api_key={}'.format(
            candidate['id'], platform_id, self.api_key)
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('MobyGames_assets_snap.json', json_data)

        # --- Parse images page data ---
        asset_list = []
        for image_data in json_data['screenshots']:
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
            if self.verbose_flag: log_debug('Found Snap {0}'.format(asset_data['url_thumb']))
            asset_list.append(asset_data)
        log_debug('MobyGames._retrieve_snap_assets() Found {} snap assets for candidate #{}'.format(
            len(asset_list), candidate['id']))

        return asset_list

    def _retrieve_cover_assets(self, candidate, platform_id, status_dic):
        log_debug('MobyGames._retrieve_cover_assets() Getting Covers...')
        url = 'https://api.mobygames.com/v1/games/{}/platforms/{}/covers?api_key={}'.format(
            candidate['id'], platform_id, self.api_key)
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('MobyGames_assets_cover.json', json_data)

        if json_data is None:
            return []

        # --- Parse images page data ---
        asset_list = []
        for group_data in json_data['cover_groups']:
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
                if self.verbose_flag: log_debug('Found Cover {0}'.format(asset_data['url_thumb']))
                asset_list.append(asset_data)
        log_debug('MobyGames._retrieve_cover_assets() Found {} cover assets for candidate #{}'.format(
            len(asset_list), candidate['id']))

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
    # MobyGames API info https://www.mobygames.com/info/api
    #
    # * When the API key is not configured or invalid MobyGames returns HTTP status code 401.
    # * When the API number of calls is exhausted MobyGames returns HTTP status code 429.
    # * When a game search is not succesfull MobyGames returns valid JSON with an empty list.
    def _retrieve_URL_as_JSON(self, url, status_dic, retry=0):
        self._wait_for_API_request()
        page_data_raw, http_code = net_get_URL(url, self._clean_URL_for_log(url))
        self.last_http_call = datetime.now()

        # --- Check HTTP error codes ---
        if http_code != 200:
            # 400 Bad Request.
            # Sent if your query could not be processed, possibly due to invalid parameter types.
            # 401 Unauthorized
            # Sent if you attempt to access an endpoint without providing a valid API key.
            # ...
            # 429 Too Many Requests
            # Sent if you make a request exceeding your API quota.
            #
            # Try go get error message from MobyGames. Even if the server returns an
            # HTTP status code it also has valid JSON.
            try:
                # log_variable('page_data_raw', page_data_raw)
                json_data = json.loads(page_data_raw)
                error_msg = json_data['message']
            except:
                error_msg = 'Unknown/unspecified error.'
            log_error('MobyGames msg "{}"'.format(error_msg))
            
            if http_code == 429 and retry < Scraper.RETRY_THRESHOLD:
                # 360 per hour limit, wait at least 16 minutes
                wait_till_time = datetime.now() + timedelta(seconds=960)
                if kodi_dialog_OK('You\'ve exceeded the max rate limit of 360 requests/hour.',
                                'Respect the website and wait at least till {}.'.format(wait_till_time)):
                    # waited long enough? Try again
                    if (datetime.now() - wait_till_time).total_seconds() > 1:
                        retry_after_wait = retry + 1
                        return self._retrieve_URL_as_JSON(url, status_dic, retry_after_wait)
                
            self._handle_error(status_dic, 'HTTP code {} message "{}"'.format(http_code, error_msg))
            return None

        # If page_data_raw is None at this point is because of an exception in net_get_URL()
        # which is not urllib2.HTTPError.
        if page_data_raw is None:
            self._handle_error(status_dic, 'Network error/exception in net_get_URL()')
            return None

        # Convert data to JSON.
        try:
            json_data = json.loads(page_data_raw)
        except Exception as ex:
            self._handle_exception(ex, status_dic, 'Error decoding JSON data from MobyGames.')
            return None

        return json_data

# ------------------------------------------------------------------------------------------------
# ScreenScraper online scraper. Uses V2 API.
#
# | Site        | https://www.screenscraper.fr             |
# | API V1 docs | https://www.screenscraper.fr/webapi.php  |
# | API V2 docs | https://www.screenscraper.fr/webapi2.php |
#
# In the API documentation page some API function can be called as a test. Other test functions
# fail when called (invalid data, no user name/pass, etc.).
#
# * If no games are found with jeuInfos.php an HTTP status code 404 is returned.
# * If no platform (platform id = 0) is used ScreenScraper returns garbage, a totally unrelated
#   game to the one being searched. It is not advisable to use this scraper with a wrong
#   platform.
#
# ssuserInfos.php : Informations sur l'utilisateur ScreenScraper
# userlevelsListe.php : Liste des niveaux utilisateurs de ScreenScraper 
# nbJoueursListe.php : Liste des nombres de joueurs
# supportTypesListe.php : Liste des types de supports
# romTypesListe.php : Liste des types de roms
# genresListe.php : Liste des genres
# regionsListe.php : Liste des regions
# languesListe.php : Liste des langues
# classificationListe.php : Liste des Classification (Game Rating)
#
# mediaGroup.php : Téléchargement des médias images des groupes de jeux
# mediaCompagnie.php : Téléchargement des médias images des groupes de jeux
#
# systemesListe.php : Liste des systèmes / informations systèmes / informations médias systèmes
# mediaSysteme.php : Téléchargement des médias images des systèmes
# mediaVideoSysteme.php : Téléchargement des médias vidéos des systèmes
#
# jeuRecherche.php : Recherche d'un jeu avec son nom (retourne une table de jeux (limité a 30 jeux)
#                    classés par probabilité)
# jeuInfos.php : Informations sur un jeu / Médias d'un jeu
# mediaJeu.php : Téléchargement des médias images des jeux
# mediaVideoJeu.php : Téléchargement des médias vidéos des jeux
# mediaManuelJeu.php : Téléchargement des manuels des jeux
#
# botNote.php : Système pour l'automatisation d'envoi de note de jeu d'un membre ScreenScraper
# botProposition.php : Système pour automatisation d'envoi de propositions d'infos ou de médias
#                      a ScreenScraper
#
# >>> Liste des types d'infos textuelles pour les jeux (modiftypeinfo) <<<
# >>> Liste des types d'infos textuelles pour les roms (modiftypeinfo) <<<
#
# >>> Liste des types de média (regionsListe) <<<
# sstitle  Screenshot  Titre  png  obligatoire
# ss       Screenshot         png  obligatoire
# fanart   Fan Art            jpg
# ...
#
# --- API call examples ---
# * All API calls have parameters devid, devpassword, softname, output, ssid, sspassword
#   so I do not include them in the examples.
#
# * API call to get all game information. This API call return one game or fails.
#
#   https://www.screenscraper.fr/api/jeuInfos.php?
#   &crc=50ABC90A
#   &systemeid=1
#   &romtype=rom
#   &romnom=Sonic%20The%20Hedgehog%202%20(World).zip
#   &romtaille=749652
#   &gameid=1234 (Forces game, ROM info not necessary in this case).
#
# * API call to search for games:
#
#   https://www.screenscraper.fr/api/jeuRecherche.php?
#   &systemeid  (Optional)
#   &recherche  (Mandatory)
#
# ------------------------------------------------------------------------------------------------
class ScreenScraper(Scraper):
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
        ASSET_TITLE_ID,
        ASSET_SNAP_ID,
        ASSET_BOXFRONT_ID,
        ASSET_BOXBACK_ID,
        ASSET_3DBOX_ID,
        ASSET_CARTRIDGE_ID,
        ASSET_MAP_ID,
        # ASSET_MANUAL_ID,
        # ASSET_TRAILER_ID,
    ]
    # Unsupported AEL types:
    # manuel (Manual)
    # screenmarquee (Marquee with lower aspec ratio, more squared than rectangular).
    # box-2D-side (Box spine)
    # box-texture (Box front, spine and back combined).
    # support-texture (Cartridge/CD scan texture)
    # bezel-16-9 (Bezel for 16:9 horizontal monitors)
    # mixrbv1 (Mix recalbox Version 1)
    # mixrbv2 (Mix recalbox Version 2)
    asset_name_mapping = {
        'fanart'             : ASSET_FANART_ID,
        'screenmarqueesmall' : ASSET_BANNER_ID,
        'steamgrid'          : ASSET_BANNER_ID,
        'wheel'              : ASSET_CLEARLOGO_ID,
        'wheel-carbon'       : ASSET_CLEARLOGO_ID,
        'wheel-steel'        : ASSET_CLEARLOGO_ID,
        'sstitle'            : ASSET_TITLE_ID,
        'ss'                 : ASSET_SNAP_ID,
        'box-2D'             : ASSET_BOXFRONT_ID,
        'box-2D-back'        : ASSET_BOXBACK_ID,
        'box-3D'             : ASSET_3DBOX_ID,
        'support-2D'         : ASSET_CARTRIDGE_ID,
        'maps'               : ASSET_MAP_ID,
    }

    # List of country/region suffixes supported by ScreenScraper.
    # Get list with API regionsListe.php call.
    # Items at the beginning will be searched first.
    # This code is automatically generated by script scrap_ScreenScraper_list_regions.py
    region_list = [
        'wor', # World
        'eu',  # Europe
        'us',  # USA
        'jp',  # Japan
        'ss',  # ScreenScraper
        'ame', # American continent
        'asi', # Asia
        'au',  # Australia
        'bg',  # Bulgaria
        'br',  # Brazil
        'ca',  # Canada
        'cl',  # Chile
        'cn',  # China
        'cus', # Custom
        'cz',  # Czech republic
        'de',  # Germany
        'dk',  # Denmark
        'fi',  # Finland
        'fr',  # France
        'gr',  # Greece
        'hu',  # Hungary
        'il',  # Israel
        'it',  # Italy
        'kr',  # Korea
        'kw',  # Kuwait
        'mor', # Middle East
        'nl',  # Netherlands
        'no',  # Norway
        'nz',  # New Zealand
        'oce', # Oceania
        'pe',  # Peru
        'pl',  # Poland
        'pt',  # Portugal
        'ru',  # Russia
        'se',  # Sweden
        'sk',  # Slovakia
        'sp',  # Spain
        'tr',  # Turkey
        'tw',  # Taiwan
        'uk',  # United Kingdom
    ]

    # This code is automatically generated by script scrap_ScreenScraper_list_languages.py
    language_list = [
        'en',  # English
        'es',  # Spanish
        'ja',  # Japanese
        'cz',  # Czech
        'da',  # Danish
        'de',  # German
        'fi',  # Finnish
        'fr',  # French
        'hu',  # Hungarian
        'it',  # Italian
        'ko',  # Korean
        'nl',  # Dutch
        'no',  # Norwegian
        'pl',  # Polish
        'pt',  # Portuguese
        'ru',  # Russian
        'sk',  # Slovak
        'sv',  # Swedish
        'tr',  # Turkish
        'zh',  # Chinese
    ]

    # --- Constructor ----------------------------------------------------------------------------
    def __init__(self, settings):
        # --- This scraper settings ---
        self.dev_id     = 'V2ludGVybXV0ZTAxMTA='
        self.dev_pass   = 'VDlwU3J6akZCbWZRbWM4Yg=='
        self.softname   = settings['scraper_screenscraper_AEL_softname']
        self.ssid       = settings['scraper_screenscraper_ssid']
        self.sspassword = settings['scraper_screenscraper_sspass']
        self.region_idx = settings['scraper_screenscraper_region']
        self.language_idx = settings['scraper_screenscraper_language']

        # --- Internal stuff ---
        # Create list of regions to search stuff. Put the user preference first.
        self.user_region = ScreenScraper.region_list[self.region_idx]
        log_debug('ScreenScraper.__init__() User preferred region "{}"'.format(self.user_region))

        # Create list of languages to search stuff. Put the user preference first.
        self.user_language = ScreenScraper.language_list[self.language_idx]
        log_debug('ScreenScraper.__init__() User preferred language "{}"'.format(self.user_language))

        # --- Pass down common scraper settings ---
        super(ScreenScraper, self).__init__(settings)

    # --- Base class abstract methods ------------------------------------------------------------
    def get_name(self): return 'ScreenScraper'

    def get_filename(self): return 'ScreenScraper'

    def supports_disk_cache(self): return True

    def supports_search_string(self): return False

    def supports_metadata_ID(self, metadata_ID):
        return True if metadata_ID in ScreenScraper.supported_metadata_list else False

    def supports_metadata(self): return True

    def supports_asset_ID(self, asset_ID):
        return True if asset_ID in ScreenScraper.supported_asset_list else False

    def supports_assets(self): return True

    # ScreenScraper user login/password is mandatory. Actually, SS seems to work if no user
    # login/password is given, however it seems that the number of API requests is very
    # limited.
    def check_before_scraping(self, status_dic):
        if self.ssid and self.sspassword:
            log_debug('ScreenScraper.check_before_scraping() ScreenScraper user name and pass OK.')
            return
        log_error('ScreenScraper.check_before_scraping() ScreenScraper user name and/or pass not configured.')
        log_error('ScreenScraper.check_before_scraping() Disabling ScreenScraper scraper.')
        self.scraper_deactivated = True
        status_dic['status'] = False
        status_dic['dialog'] = KODI_MESSAGE_DIALOG
        status_dic['msg'] = (
            'AEL requires your ScreenScraper user name and password. '
            'Create a user account in https://www.screenscraper.fr/ '
            'and set you user name and password in AEL addon settings.'
        )

    # _search_candidates_jeuInfos() uses the internal cache.
    # ScreenScraper uses the candidates and internal cache. It does not use the
    # medatada and asset caches at all because the metadata and assets are generated
    # with the internal cache.
    # Search term is always None for this scraper.
    def get_candidates(self, search_term, rom_FN, rom_checksums_FN, platform, status_dic):
        # If the scraper is disabled return None and do not mark error in status_dic.
        # Candidate will not be introduced in the disk cache and will be scraped again.
        if self.scraper_disabled:
            log_debug('ScreenScraper.get_candidates() Scraper disabled. Returning empty data.')
            return None

        # Prepare data for scraping.
        rombase = rom_FN.getBase()
        rompath = rom_FN.getPath()
        romchecksums_path = rom_checksums_FN.getPath() if rom_checksums_FN is not None else None
        scraper_platform = AEL_platform_to_ScreenScraper(platform)

        # --- Get candidates ---
        # ScreenScraper jeuInfos.php returns absolutely everything about a single ROM, including
        # metadata, artwork, etc. jeuInfos.php returns one game or nothing at all.
        # ScreenScraper returns only one game or nothing at all.
        log_debug('ScreenScraper.get_candidates() rompath      "{}"'.format(rompath))
        log_debug('ScreenScraper.get_candidates() romchecksums "{}"'.format(romchecksums_path))
        log_debug('ScreenScraper.get_candidates() AEL platform "{}"'.format(platform))
        log_debug('ScreenScraper.get_candidates() SS platform  "{}"'.format(scraper_platform))
        candidate_list = self._search_candidates_jeuInfos(
            rom_FN, rom_checksums_FN, platform, scraper_platform, status_dic)
        # _search_candidates_jeuRecherche() does not work for get_metadata() and get_assets()
        # because jeu_dic is not introduced in the internal cache.
        # candidate_list = self._search_candidates_jeuRecherche(
        #     search_term, rombase_noext, platform, scraper_platform, status_dic)
        if not status_dic['status']: return None

        return candidate_list

    # This function may be called many times in the ROM Scanner. All calls to this function
    # must be cached. See comments for this function in the Scraper abstract class.
    def get_metadata(self, status_dic):
        # --- If scraper is disabled return immediately and silently ---
        if self.scraper_disabled:
            log_debug('ScreenScraper.get_metadata() Scraper disabled. Returning empty data.')
            return self._new_gamedata_dic()

        # --- Retrieve jeu_dic from internal cache ---
        if self._check_disk_cache(Scraper.CACHE_INTERNAL, self.cache_key):
            log_debug('ScreenScraper.get_metadata() Internal cache hit "{0}"'.format(self.cache_key))
            jeu_dic = self._retrieve_from_disk_cache(Scraper.CACHE_INTERNAL, self.cache_key)
        else:
            raise ValueError('Logic error')

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

    # This function may be called many times in the ROM Scanner. All calls to this function
    # must be cached. See comments for this function in the Scraper abstract class.
    def get_assets(self, asset_info, status_dic):
        # --- If scraper is disabled return immediately and silently ---
        if self.scraper_disabled:
            log_debug('ScreenScraper.get_assets() Scraper disabled. Returning empty data.')
            return []

        log_debug('ScreenScraper.get_assets() Getting assets {} (ID {}) for candidate ID = {}'.format(
            asset_info.name, asset_info.id, self.candidate['id']))

        # --- Retrieve jeu_dic from internal cache ---
        if self._check_disk_cache(Scraper.CACHE_INTERNAL, self.cache_key):
            log_debug('ScreenScraper.get_assets() Internal cache hit "{0}"'.format(self.cache_key))
            jeu_dic = self._retrieve_from_disk_cache(Scraper.CACHE_INTERNAL, self.cache_key)
        else:
            raise ValueError('Logic error')

        # --- Parse game assets ---
        all_asset_list = self._retrieve_all_assets(jeu_dic, status_dic)
        if not status_dic['status']: return None
        asset_list = [asset_dic for asset_dic in all_asset_list if asset_dic['asset_ID'] == asset_info.id]
        log_debug('ScreenScraper.get_assets() Total assets {} / Returned assets {}'.format(
            len(all_asset_list), len(asset_list)))

        return asset_list

    # Sometimes ScreenScraper URLs have spaces. One example is the map images of Genesis Sonic 1.
    # https://www.screenscraper.fr/gameinfos.php?plateforme=1&gameid=5
    # Make sure to escape the spaces in the returned URL.
    def resolve_asset_URL(self, selected_asset, status_dic):
        # For some reason this code does not work well...
        # url = selected_asset['url']
        # if url.startswith('http://'):    return 'http://' + urllib.quote(url[7:])
        # elif url.startswith('https://'): return 'https://' + urllib.quote(url[8:])
        # else:                            raise ValueError
        url = selected_asset['url']
        url_log = self._clean_URL_for_log(url)

        return url, url_log

    def resolve_asset_URL_extension(self, selected_asset, url, status_dic):
        return selected_asset['SS_format']

    # --- This class own methods -----------------------------------------------------------------
    # Plumbing function to get the cached jeu_dic dictionary returned by ScreenScraper.
    # This is cached in the internal cache.
    # Scraper.get_candiates() must be called before this function to fill the cache.
    #
    # THIS FUNCTION IS OBSOLETE. jeu_dic is now in the internal cache.
    def debug_get_gameInfos_dic(self, candidate):
        log_debug('ScreenScraper.debug_get_gameInfos_dic() Internal cache retrieving "{}"'.format(
            candidate['SS_cache_str']))
        gameInfos_dic = self.cache_jeuInfos[candidate['SS_cache_str']]

        return gameInfos_dic

    def debug_get_user_info(self, status_dic):
        log_debug('ScreenScraper.debug_get_user_info() Geting SS user info...')
        url_a = 'https://www.screenscraper.fr/api2/ssuserInfos.php?devid={}&devpassword={}'
        url_b = '&softname={}&output=json&ssid={}&sspassword={}'
        url = url_a.format(base64.b64decode(self.dev_id), base64.b64decode(self.dev_pass), ) + \
              url_b.format(self.softname, self.ssid, self.sspassword)
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('ScreenScraper_get_user_info.json', json_data)

        return json_data

    def debug_get_user_levels(self, status_dic):
        log_debug('ScreenScraper.debug_get_user_levels() Geting SS user level list...')
        url_a = 'https://www.screenscraper.fr/api2/userlevelsListe.php?devid={}&devpassword={}'
        url_b = '&softname={}&output=json&ssid={}&sspassword={}'
        url = url_a.format(base64.b64decode(self.dev_id), base64.b64decode(self.dev_pass), ) + \
              url_b.format(self.softname, self.ssid, self.sspassword)
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('ScreenScraper_get_user_level_list.json', json_data)

        return json_data

    # nbJoueursListe.php : Liste des nombres de joueurs 

    def debug_get_support_types(self, status_dic):
        log_debug('ScreenScraper.debug_get_support_types() Geting SS Support Types list...')
        url_a = 'https://www.screenscraper.fr/api2/supportTypesListe.php?devid={}&devpassword={}'
        url_b = '&softname={}&output=json&ssid={}&sspassword={}'
        url = url_a.format(base64.b64decode(self.dev_id), base64.b64decode(self.dev_pass), ) + \
              url_b.format(self.softname, self.ssid, self.sspassword)
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('ScreenScraper_get_support_types_list.json', json_data)

        return json_data

    def debug_get_ROM_types(self, status_dic):
        log_debug('ScreenScraper.debug_get_ROM_types() Geting SS ROM types list...')
        url_a = 'https://www.screenscraper.fr/api2/romTypesListe.php?devid={}&devpassword={}'
        url_b = '&softname={}&output=json&ssid={}&sspassword={}'
        url = url_a.format(base64.b64decode(self.dev_id), base64.b64decode(self.dev_pass), ) + \
              url_b.format(self.softname, self.ssid, self.sspassword)
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('ScreenScraper_get_ROM_types_list.json', json_data)

        return json_data

    def debug_get_genres(self, status_dic):
        log_debug('ScreenScraper.debug_get_genres() Geting SS Genre list...')
        url_a = 'https://www.screenscraper.fr/api2/genresListe.php?devid={}&devpassword={}'
        url_b = '&softname={}&output=json&ssid={}&sspassword={}'
        url = url_a.format(base64.b64decode(self.dev_id), base64.b64decode(self.dev_pass), ) + \
              url_b.format(self.softname, self.ssid, self.sspassword)
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('ScreenScraper_get_genres_list.json', json_data)

        return json_data

    def debug_get_regions(self, status_dic):
        log_debug('ScreenScraper.debug_get_regions() Geting SS Regions list...')
        url_a = 'https://www.screenscraper.fr/api2/regionsListe.php?devid={}&devpassword={}'
        url_b = '&softname={}&output=json&ssid={}&sspassword={}'
        url = url_a.format(base64.b64decode(self.dev_id), base64.b64decode(self.dev_pass), ) + \
              url_b.format(self.softname, self.ssid, self.sspassword)
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('ScreenScraper_get_regions_list.json', json_data)

        return json_data

    def debug_get_languages(self, status_dic):
        log_debug('ScreenScraper.debug_get_languages() Geting SS Languages list...')
        url_a = 'https://www.screenscraper.fr/api2/languesListe.php?devid={}&devpassword={}'
        url_b = '&softname={}&output=json&ssid={}&sspassword={}'
        url = url_a.format(base64.b64decode(self.dev_id), base64.b64decode(self.dev_pass), ) + \
              url_b.format(self.softname, self.ssid, self.sspassword)
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('ScreenScraper_get_language_list.json', json_data)

        return json_data

    def debug_get_clasifications(self, status_dic):
        log_debug('ScreenScraper.debug_get_clasifications() Geting SS Clasifications list...')
        url_a = 'https://www.screenscraper.fr/api2/classificationListe.php?devid={}&devpassword={}'
        url_b = '&softname={}&output=json&ssid={}&sspassword={}'
        url = url_a.format(base64.b64decode(self.dev_id), base64.b64decode(self.dev_pass), ) + \
              url_b.format(self.softname, self.ssid, self.sspassword)
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('ScreenScraper_get_clasifications_list.json', json_data)

        return json_data

    def debug_get_platforms(self, status_dic):
        log_debug('ScreenScraper.debug_get_platforms() Getting SS platforms...')
        url_a = 'https://www.screenscraper.fr/api2/systemesListe.php?'
        url_b = 'devid={}&devpassword={}&softname={}&output=json&ssid={}&sspassword={}'.format(
            base64.b64decode(self.dev_id), base64.b64decode(self.dev_pass),
            self.softname, self.ssid, self.sspassword)
        url = url_a + url_b
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('ScreenScraper_get_platform_list.json', json_data)

        return json_data

    # Debug test function for jeuRecherche.php (game search).
    def debug_game_search(self, search_term, rombase_noext, platform, status_dic):
        log_debug('ScreenScraper.debug_game_search() Calling jeuRecherche.php...')
        scraper_platform = AEL_platform_to_ScreenScraper(platform)
        system_id = scraper_platform
        recherche = urllib.quote(rombase_noext)
        log_debug('ScreenScraper.debug_game_search() system_id  "{0}"'.format(system_id))
        log_debug('ScreenScraper.debug_game_search() recherche  "{0}"'.format(recherche))

        url_a = 'https://www.screenscraper.fr/api2/jeuRecherche.php?'
        url_b = 'devid={}&devpassword={}&softname={}&output=json&ssid={}&sspassword={}'.format(
            base64.b64decode(self.dev_id), base64.b64decode(self.dev_pass),
            self.softname, self.ssid, self.sspassword)
        url_c = '&systemeid={}&recherche={}'.format(system_id, recherche)
        url = url_a + url_b + url_c
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if json_data is None or not status_dic['status']: return None
        self._dump_json_debug('ScreenScraper_gameSearch.json', json_data)

    # Call to ScreenScraper jeuInfos.php.
    def _search_candidates_jeuInfos(self, rom_FN, rom_checksums_FN, platform, scraper_platform, status_dic):
        # --- Test data ---
        # * Example from ScreenScraper API info page.
        #   #crc=50ABC90A&systemeid=1&romtype=rom&romnom=Sonic%20The%20Hedgehog%202%20(World).zip&romtaille=749652
        # * Note that if the CRC is all zeros and the filesize also 0 it seems to work.
        #   Also, if no file extension is passed it seems to work. Looks like SS is capable of
        #   fuzzy searches to some degree.
        # * If rom_type = 'rom' SS returns gargabe for CD-based platforms like Playstation.

        # ISO-based platform set.
        ISO_platform_set = set([
            'Fujitsu FM Towns Marty',
            'NEC PC Engine CDROM2',
            'NEC TurboGrafx CD',
            'Nintendo GameCube',
            'Nintendo Wii',
            'Sega Dreamcast',
            'Sega Saturn',
            'Sony PlayStation',
            'Sony PlayStation 2',
            'Sony PlayStation Portable',
        ])

        # --- IMPORTANT ---
        # ScreenScraper requires all CRC, MD5 and SHA1 and the correct file size of the
        # files scraped.
        if self.debug_checksums_flag:
            # Use fake checksums when developing the scraper with fake 0-sized files.
            log_info('Using debug checksums and not computing real ones.')
            checksums = {
                'crc'  : self.debug_crc, 'md5'  : self.debug_md5, 'sha1' : self.debug_sha1,
                'size' : self.debug_size, 'rom_name' : rom_FN.getBase(),
            }
        else:
            checksums = self._get_SS_checksum(rom_checksums_FN)
            if checksums is None:
                status_dic['status'] = False
                status_dic['msg'] = 'Error computing file checksums.'
                return None

        # --- Actual data for scraping in AEL ---
        # Change rom_type for ISO-based platforms
        rom_type = 'iso' if platform in ISO_platform_set else 'rom'
        system_id = scraper_platform
        crc_str = checksums['crc']
        md5_str = checksums['md5']
        sha1_str = checksums['sha1']
        # rom_name = urllib.quote(checksums['rom_name'])
        rom_name = urllib.quote_plus(checksums['rom_name'])
        rom_size = checksums['size']
        # log_debug('ScreenScraper._search_candidates_jeuInfos() ssid       "{0}"'.format(self.ssid))
        # log_debug('ScreenScraper._search_candidates_jeuInfos() ssid       "{0}"'.format('***'))
        # log_debug('ScreenScraper._search_candidates_jeuInfos() sspassword "{0}"'.format(self.sspassword))
        # log_debug('ScreenScraper._search_candidates_jeuInfos() sspassword "{0}"'.format('***'))
        log_debug('ScreenScraper._search_candidates_jeuInfos() rom_type   "{0}"'.format(rom_type))
        log_debug('ScreenScraper._search_candidates_jeuInfos() system_id  "{0}"'.format(system_id))
        log_debug('ScreenScraper._search_candidates_jeuInfos() crc_str    "{0}"'.format(crc_str))
        log_debug('ScreenScraper._search_candidates_jeuInfos() md5_str    "{0}"'.format(md5_str))
        log_debug('ScreenScraper._search_candidates_jeuInfos() sha1_str   "{0}"'.format(sha1_str))
        log_debug('ScreenScraper._search_candidates_jeuInfos() rom_name   "{0}"'.format(rom_name))
        log_debug('ScreenScraper._search_candidates_jeuInfos() rom_size   "{0}"'.format(rom_size))

        # --- Build URL and retrieve JSON ---
        # It is more convenient to dump XML files for development.
        # For regular scraping JSON is more efficient.
        url_a = 'https://www.screenscraper.fr/api2/jeuInfos.php?'
        url_b = 'devid={}&devpassword={}&softname={}&output=json&ssid={}&sspassword={}'.format(
            base64.b64decode(self.dev_id), base64.b64decode(self.dev_pass),
            self.softname, self.ssid, self.sspassword)
        url_c = '&romtype={}&systemeid={}&crc={}&md5={}&sha1={}&romnom={}&romtaille={}'.format(
            rom_type, system_id, crc_str, md5_str, sha1_str, rom_name, rom_size)
        url = url_a + url_b + url_c
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        # If status_dic mark an error there was an exception. Return None.
        if not status_dic['status']: return None
        # If no games were found status_dic['status'] is True and json_data is None.
        # Return empty list of candidates.
        if json_data is None: return []
        self._dump_json_debug('ScreenScraper_gameInfo.json', json_data)

        # --- Print some info ---
        jeu_dic = json_data['response']['jeu']
        id_str = str(jeu_dic['id'])
        title = jeu_dic['noms'][0]['text']
        log_debug('Game "{}" (ID {})'.format(title, id_str))
        log_debug('Number of ROMs {} / Number of assets {}'.format(
            len(jeu_dic['roms']), len(jeu_dic['medias'])))

        # --- Build candidate_list from ScreenScraper jeu_dic returned by jeuInfos.php ---
        # SS returns one candidate or no candidate.
        candidate = self._new_candidate_dic()
        candidate['id'] = id_str
        candidate['display_name'] = title
        candidate['platform'] = platform
        candidate['scraper_platform'] = scraper_platform
        candidate['order'] = 1

        # --- Add candidate jeu_dic to the internal cache ---
        log_debug('ScreenScraper._search_candidates_jeuInfos() Adding to internal cache "{}"'.format(
            self.cache_key))
        # IMPORTANT Do not clean URLs. There could be problems reconstructing some URLs.
        # self._clean_JSON_for_dumping(jeu_dic)
        jeu_dic['roms'] = []
        self._update_disk_cache(Scraper.CACHE_INTERNAL, self.cache_key, jeu_dic)

        return [ candidate ]

    # Call to ScreenScraper jeuRecherche.php.
    def _search_candidates_jeuRecherche(self, search_term, rombase_noext, platform, scraper_platform, status_dic):
        # --- Actual data for scraping in AEL ---
        log_debug('ScreenScraper._search_candidates_jeuRecherche() Calling jeuRecherche.php...')
        scraper_platform = AEL_platform_to_ScreenScraper(platform)
        system_id = scraper_platform
        recherche = urllib.quote_plus(rombase_noext)
        log_debug('ScreenScraper._search_candidates_jeuRecherche() system_id  "{0}"'.format(system_id))
        log_debug('ScreenScraper._search_candidates_jeuRecherche() recherche  "{0}"'.format(recherche))

        # --- Build URL and retrieve JSON ---
        url_a = 'https://www.screenscraper.fr/api2/jeuRecherche.php?'
        url_b = 'devid={}&devpassword={}&softname={}&output=json&ssid={}&sspassword={}'.format(
            base64.b64decode(self.dev_id), base64.b64decode(self.dev_pass),
            self.softname, self.ssid, self.sspassword)
        url_c = '&systemeid={}&recherche={}'.format(system_id, recherche)
        url = url_a + url_b + url_c
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if json_data is None or not status_dic['status']: return None
        self._dump_json_debug('ScreenScraper_gameSearch.json', json_data)

        # * If no games were found server replied with a HTTP 404 error. json_data is None and
        #  status_dic signals operation succesfull. Return empty list of candidates.
        # * If an error/exception happened then it is marked in status_dic.
        if json_data is None: return []
        jeu_list = json_data['response']['jeux']
        log_debug('Number of games {}'.format(len(jeu_list)))

        # --- Build candidate_list ---
        # cache_key = search_term + '__' + rombase_noext + '__' + platform
        candidate_list = []
        for jeu_dic in jeu_list:
            id_str = jeu_dic['id']
            title = jeu_dic['noms'][0]['text']
            candidate = self._new_candidate_dic()
            candidate['id'] = id_str
            candidate['display_name'] = title
            candidate['platform'] = platform
            candidate['scraper_platform'] = scraper_platform
            candidate['order'] = 1
            # candidate['SS_cache_str'] = cache_key # Special field to retrieve game from SS cache.
            candidate_list.append(candidate)

        # --- Add candidate games to the internal cache ---
        # log_debug('ScreenScraper._search_candidates_jeuInfos() Adding to internal cache')
        # self.cache_jeuInfos[cache_key] = jeu_dic

        return candidate_list

    def _parse_meta_title(self, jeu_dic):
        try:
            # First search for the user preferred region.
            for n in jeu_dic['noms']:
                if n['region'] == self.user_region: return n['text']
            # If nothing found then search in the sorted list of regions.
            for region in ScreenScraper.region_list:
                for n in jeu_dic['noms']:
                    if n['region'] == region: return n['text']
        except KeyError:
            pass

        return DEFAULT_META_TITLE

    def _parse_meta_year(self, jeu_dic):
        try:
            for n in jeu_dic['dates']:
                if n['region'] == self.user_region: return n['text'][0:4]
            for region in ScreenScraper.region_list:
                for n in jeu_dic['dates']:
                    if n['region'] == region: return n['text'][0:4]
        except KeyError:
            pass

        return DEFAULT_META_YEAR

    # Use first genre only for now.
    def _parse_meta_genre(self, jeu_dic):
        try:
            genre_item = jeu_dic['genres'][0]
            for n in genre_item['noms']:
                if n['langue'] == self.user_language: return n['text']
            for language in ScreenScraper.language_list:
                for n in genre_item['noms']:
                    if n['langue'] == language: return n['text']
        except KeyError:
            pass

        return DEFAULT_META_GENRE

    def _parse_meta_developer(self, jeu_dic):
        try:
            return jeu_dic['developpeur']['text']
        except KeyError:
            pass

        return DEFAULT_META_DEVELOPER

    def _parse_meta_nplayers(self, jeu_dic):
        # EAFP Easier to ask for forgiveness than permission.
        try:
            return jeu_dic['joueurs']['text']
        except KeyError:
            pass

        return DEFAULT_META_NPLAYERS

    # Do not working at the moment.
    def _parse_meta_esrb(self, jeu_dic):
        # if 'classifications' in jeu_dic and 'ESRB' in jeu_dic['classifications']:
        #     return jeu_dic['classifications']['ESRB']

        return DEFAULT_META_ESRB

    def _parse_meta_plot(self, jeu_dic):
        try:
            for n in jeu_dic['synopsis']:
                if n['langue'] == self.user_language: return n['text']
            for language in ScreenScraper.language_list:
                for n in jeu_dic['synopsis']:
                    if n['langue'] == language: return n['text']
        except KeyError:
            pass

        return DEFAULT_META_PLOT

    # Get ALL available assets for game.
    # Returns all assets found in the jeu_dic dictionary. It is not necessary to cache this
    # because it can be easily generated.
    # For now asset do not support region or language settings.
    #
    # Examples:
    # https://www.screenscraper.fr/gameinfos.php?gameid=5     # Sonic 1 Megadrive
    # https://www.screenscraper.fr/gameinfos.php?gameid=3     # Sonic 2 Megadrive
    # https://www.screenscraper.fr/gameinfos.php?gameid=1187  # Sonic 3 Megadrive
    # https://www.screenscraper.fr/gameinfos.php?gameid=19249 # Final Fantasy VII PSX
    #
    # Example of download and thumb URLs. Thumb URLs are used to display media in the website:
    # https://www.screenscraper.fr/image.php?gameid=5&media=sstitle&hd=0&region=wor&num=&version=&maxwidth=338&maxheight=190
    # https://www.screenscraper.fr/image.php?gameid=5&media=fanart&hd=0&region=&num=&version=&maxwidth=338&maxheight=190
    # https://www.screenscraper.fr/image.php?gameid=5&media=steamgrid&hd=0&region=&num=&version=&maxwidth=338&maxheight=190
    #
    # TODO: support Manuals and Trailers.
    def _retrieve_all_assets(self, jeu_dic, status_dic):
        asset_list = []
        medias_list = jeu_dic['medias']
        for media_dic in medias_list:
            # Find known asset types. ScreenScraper has really a lot of different assets.
            if media_dic['type'] in ScreenScraper.asset_name_mapping:
                asset_ID = ScreenScraper.asset_name_mapping[media_dic['type']]
            else:
                # Skip unknwon assets
                continue
            # Build thumb URL
            game_ID = jeu_dic['id']
            region = media_dic['region'] if 'region' in media_dic else ''
            if region: media_type = media_dic['type'] + ' ' + region
            else:      media_type = media_dic['type']
            # Build thumb URL
            url_thumb_a = 'https://www.screenscraper.fr/image.php?'
            url_thumb_b = 'gameid={}&media={}&region={}'.format(game_ID, media_type, region)
            url_thumb_c = '&hd=0&num=&version=&maxwidth=338&maxheight=190'
            url_thumb = url_thumb_a + url_thumb_b + url_thumb_c
            # Build asset URL. ScreenScraper URLs are stripped down when saved to the cache
            # to save space and time. FEATURE CANCELED. There could be problems reconstructing
            # some URLs and the space saved is not so great for most games.
            # systemeid = jeu_dic['systemeid']
            # media = '{}({})'.format(media_type, region)
            # url_thumb_a = 'https://www.screenscraper.fr/api2/mediaJeu.php?'
            # url_b = 'devid={}&devpassword={}&softname={}&ssid={}&sspassword={}'.format(
            #     base64.b64decode(self.dev_id), base64.b64decode(self.dev_pass),
            #     self.softname, self.ssid, self.sspassword)
            # url_thumb_c = '&systemeid={}&jeuid={}&media={}'.format(systemeid, game_ID, media)
            # url_asset = url_thumb_a + url_thumb_b + url_thumb_c
            # log_debug('URL "{}"'.format(url_asset))
            # Create asset dictionary
            asset_data = self._new_assetdata_dic()
            asset_data['asset_ID'] = asset_ID
            asset_data['display_name'] = media_type
            asset_data['url_thumb'] = url_thumb
            asset_data['url'] = media_dic['url']
            # Special ScreenScraper field to resolve URL extension later.
            asset_data['SS_format'] = media_dic['format']
            asset_list.append(asset_data)

        return asset_list

    # 1) If rom_checksums_FN is a ZIP file and contains one and only one file, then consider that
    #    file the ROM, decompress in memory and calculate the checksums.
    # 2) If rom_checksums_FN is a standard file or 1) fails then calculate the checksums of
    #    the file.
    # 3) Return a checksums dictionary if everything is OK. Return None in case of any error.
    def _get_SS_checksum(self, rom_checksums_FN):
        f_basename = rom_checksums_FN.getBase()
        f_path = rom_checksums_FN.getPath()
        log_debug('_get_SS_checksum() Processing "{}"'.format(f_path))
        if f_basename.lower().endswith('.zip'):
            log_debug('_get_SS_checksum() ZIP file detected.')
            if not zipfile.is_zipfile(f_path):
                log_error('zipfile.is_zipfile() returns False. Bad ZIP file.')
                return None
            else:
                log_debug('_get_SS_checksum() ZIP file seems to be correct.')
            zip = zipfile.ZipFile(f_path)
            namelist = zip.namelist()
            # log_variable('namelist', namelist)
            if len(namelist) == 1:
                log_debug('_get_SS_checksum() ZIP file has one file only.')
                log_debug('_get_SS_checksum() Decompressing file "{}"'.format(namelist[0]))
                file_bytes = zip.read(namelist[0])
                log_debug('_get_SS_checksum() Decompressed size is {} bytes'.format(len(file_bytes)))
                checksums = misc_calculate_stream_checksums(file_bytes)
                checksums['rom_name'] = namelist[0]
                log_debug('_get_SS_checksum() ROM name is "{}"'.format(checksums['rom_name']))
                return checksums
            else:
                log_debug('_get_SS_checksum() ZIP file has {} files.'.format(len(namelist)))
                log_debug('_get_SS_checksum() Computing checksum of whole ZIP file.')
        else:
            log_debug('_get_SS_checksum() File is not ZIP. Computing checksum of whole file.')
        # Otherwise calculate checksums of the whole file
        checksums = misc_calculate_checksums(f_path)
        checksums['rom_name'] = f_basename
        log_debug('_get_SS_checksum() ROM name is "{}"'.format(checksums['rom_name']))

        return checksums

    # ScreenScraper URLs have the developer password and the user password.
    # Clean URLs for safe logging.
    def _clean_URL_for_log(self, url):
        # --- Keep things simple! ---
        clean_url = url
        # --- Basic cleaning ---
        # clean_url = re.sub('devid=[^&]*&', 'devid=***&', clean_url)
        # clean_url = re.sub('devpassword=[^&]*&', 'devpassword=***&', clean_url)
        # clean_url = re.sub('ssid=[^&]*&', 'ssid=***&', clean_url)
        # clean_url = re.sub('sspassword=[^&]*&', 'sspassword=***&', clean_url)
        # clean_url = re.sub('sspassword=[^&]*$', 'sspassword=***', clean_url)
        # --- Mr Propoer. SS URLs are very long ---
        clean_url = re.sub('devid=[^&]*&', '', clean_url)
        clean_url = re.sub('devid=[^&]*$', '', clean_url)
        clean_url = re.sub('devpassword=[^&]*&', '', clean_url)
        clean_url = re.sub('devpassword=[^$]*$', '', clean_url)
        clean_url = re.sub('softname=[^&]*&', '', clean_url)
        clean_url = re.sub('softname=[^&]*$', '', clean_url)
        clean_url = re.sub('output=[^&]*&', '', clean_url)
        clean_url = re.sub('output=[^&]*$', '', clean_url)
        clean_url = re.sub('ssid=[^&]*&', '', clean_url)
        clean_url = re.sub('ssid=[^&]*$', '', clean_url)
        clean_url = re.sub('sspassword=[^&]*&', '', clean_url)
        clean_url = re.sub('sspassword=[^&]*$', '', clean_url)

        # log_variable('url', url)
        # log_variable('clean_url', clean_url)

        return clean_url

    # Reimplementation of base class method.
    # ScreenScraper needs URL cleaning in JSON before dumping because URL have passwords.
    # Only clean data if JSON file is dumped.
    def _dump_json_debug(self, file_name, json_data):
        if not self.dump_file_flag: return
        json_data_clean = self._clean_JSON_for_dumping(json_data)
        super(ScreenScraper, self)._dump_json_debug(file_name, json_data)

    # JSON recursive iterator generator. Keeps also track of JSON keys.
    # yield from added in Python 3.3
    # https://stackoverflow.com/questions/38397285/iterate-over-all-items-in-json-object
    # https://stackoverflow.com/questions/14692690/access-nested-dictionary-items-via-a-list-of-keys
    def _recursive_iter(self, obj, keys = ()):
        if isinstance(obj, dict):
            for k, v in obj.iteritems():
                # yield from self._recursive_iter(item)
                for k_t, v_t in self._recursive_iter(v, keys + (k,)):
                    yield k_t, v_t
        elif any(isinstance(obj, t) for t in (list, tuple)):
            for idx, item in enumerate(obj):
                # yield from recursive_iter(item, keys + (idx,))
                for k_t, v_t in self._recursive_iter(item, keys + (idx,)):
                    yield k_t, v_t
        else:
            yield keys, obj

    # Get a given data from a dictionary with position provided as a list (iterable)
    # Example maplist = ["b", "v", "y"] or ("b", "v", "y")
    def _getFromDict(self, dataDict, mapList):
        for k in mapList: dataDict = dataDict[k]

        return dataDict

    # Recursively cleans URLs in a JSON data structure for safe JSON file data dumping.
    def _clean_JSON_for_dumping(self, json_data):
        # --- Recursively iterate data ---
        # Do not modify dictionary when it is recursively iterated.
        URL_key_list = []
        log_debug('ScreenScraper._clean_JSON_for_dumping() Cleaning JSON URLs.')
        for keys, item in self._recursive_iter(json_data):
            # log_debug('{} "{}"'.format(keys, item))
            # log_debug('Type item "{}"'.format(type(item)))
            # Skip non string objects.
            if not isinstance(item, str) and not isinstance(item, unicode): continue
            if item.startswith('http'):
                # log_debug('Adding URL "{}"'.format(item))
                URL_key_list.append(keys)

        # --- Do the actual cleaning ---
        for keys in URL_key_list:
            # log_debug('Cleaning "{}"'.format(keys))
            url = self._getFromDict(json_data, keys)
            clean_url = self._clean_URL_for_log(url)
            # log_debug('Cleaned  "{}"'.format(clean_url))
            self._setInDict(json_data, keys, clean_url)
        log_debug('ScreenScraper._clean_JSON_for_dumping() Cleaned {} URLs'.format(len(URL_key_list)))

    # Set a given data in a dictionary with position provided as a list (iterable)
    def _setInDict(self, dataDict, mapList, value):
        for k in mapList[:-1]: dataDict = dataDict[k]
        dataDict[mapList[-1]] = value

    # Retrieve URL and decode JSON object.
    #
    # * When the API user/pass is not configured or invalid SS returns ...
    # * When the API number of calls is exhausted SS returns a HTTP 429 error code.
    # * When the API number of calls for the whole day is exhausted SS returns HTTP status code 430.
    #   In this case mark error in status_dic and return None.
    # * In case of any error/exception mark error in status_dic and return None.
    # * When the a game search is not succesfull SS returns a "HTTP Error 404: Not Found" error.
    #   In this case status_dic marks no error and return None.
    def _retrieve_URL_as_JSON(self, url, status_dic, retry=0):
        self._wait_for_API_request(2000)
        page_data_raw, http_code = net_get_URL(url, self._clean_URL_for_log(url))
        self.last_http_call = datetime.now()

        # --- Check HTTP error codes ---
        if http_code == 400:
            # Code 400 describes an error. See API description page.
            log_debug('ScreenScraper._retrieve_URL_as_JSON() HTTP status 400: general error.')
            self._handle_error(status_dic, 'Bad HTTP status code {}'.format(http_code))
            return None
        elif http_code == 429 and retry < Scraper.RETRY_THRESHOLD:
            log_debug('ScreenScraper._retrieve_URL_as_JSON() HTTP status 429: Limit exceeded.')
            # Number of requests limit, wait at least 2 minutes. Increments with every retry.
            amount_seconds = 120*(retry+1)
            wait_till_time = datetime.now() + timedelta(seconds=amount_seconds)
            kodi_dialog_OK('You\'ve exceeded the max rate limit.', 
                           'Respecting the website and we wait at least till {}.'.format(wait_till_time))
            self._wait_for_API_request(amount_seconds*1000)
            # waited long enough? Try again
            retry_after_wait = retry + 1
            return self._retrieve_URL_as_JSON(url, status_dic, retry_after_wait)
        elif http_code == 404:
            # Code 404 in SS means the ROM was not found. Return None but do not mark
            # error in status_dic.
            log_debug('ScreenScraper._retrieve_URL_as_JSON() HTTP status 404: no candidates found.')
            return None
        elif http_code != 200:
            # Unknown HTTP status code.
            self._handle_error(status_dic, 'Bad HTTP status code {}'.format(http_code))
            return None
        # self._dump_file_debug('ScreenScraper_data_raw.txt', page_data_raw)

        # If page_data_raw is None at this point is because of an exception in net_get_URL()
        # which is not urllib2.HTTPError.
        if page_data_raw is None:
            self._handle_error(status_dic, 'Network error/exception in net_get_URL()')
            return None

        # Convert data to JSON.
        try:
            return json.loads(page_data_raw)
        except Exception as ex:
            log_error('Error decoding JSON data from ScreenScraper.')

        # This point is reached if there was an exception decoding JSON.
        # Sometimes ScreenScraper API V2 returns badly formatted JSON. Try to fix this.
        # See https://github.com/muldjord/skyscraper/blob/master/src/screenscraper.cpp
        # The badly formatted JSON is at the end of the file, for example:
        #
        #			],     <-- Here it should be a ']' and not '],'.
        #		}
        #	}
        #}
        log_error('Trying to repair ScreenScraper data string before parsing JSON again.')
        page_data_raw = page_data_raw.replace('],\n\t\t}', ']\n\t\t}')
        try:
            return json.loads(page_data_raw)
        except:
            self._handle_exception(ex, status_dic,
                'Error decoding JSON data from ScreenScraper (fixed version).')
            return None

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

    def get_filename(self): return 'GameFAQs'

    def supports_disk_cache(self): return True

    def supports_search_string(self): return True

    def supports_metadata_ID(self, metadata_ID):
        return True if metadata_ID in GameFAQs.supported_metadata_list else False

    def supports_metadata(self): return True

    def supports_asset_ID(self, asset_ID):
        return True if asset_ID in GameFAQs.supported_asset_list else False

    def supports_assets(self): return True
    
    # GameFAQs does not require any API keys. By default status_dic is configured for successful
    # operation so return it as it is.
    def check_before_scraping(self, status_dic): return status_dic

    def get_candidates(self, search_term, rom_FN, rom_checksums_FN, platform, status_dic):
        scraper_platform = AEL_platform_to_GameFAQs(platform)
        rombase_noext = rom_FN.getBaseNoExt()
        log_debug('GameFAQs.get_candidates() search_term      "{0}"'.format(search_term))
        log_debug('GameFAQs.get_candidates() rombase_noext    "{0}"'.format(rombase_noext))
        log_debug('GameFAQs.get_candidates() platform         "{0}"'.format(platform))
        log_debug('GameFAQs.get_candidates() scraper_platform "{0}"'.format(scraper_platform))

        # Order list based on score
        game_list = self._get_candidates_from_page(search_term, platform, scraper_platform)
        game_list.sort(key = lambda result: result['order'], reverse = True)

        return game_list

    # --- Example URLs ---
    # https://gamefaqs.gamespot.com/snes/519824-super-mario-world
    def get_metadata(self, status_dic):
        # --- Grab game information page ---
        log_debug('GameFAQs._scraper_get_metadata() Get metadata from {}'.format(self.candidate['id']))
        url = 'https://gamefaqs.gamespot.com{}'.format(self.candidate['id'])
        page_data = net_get_URL(url)
        self._dump_file_debug('GameFAQs_get_metadata.html', page_data)

        # --- Parse data ---
        game_year      = self._parse_year(page_data)
        game_genre     = self._parse_genre(page_data)
        game_developer = self._parse_developer(page_data)
        game_plot      = self._parse_plot(page_data)

        # --- Build metadata dictionary ---
        game_data = self._new_gamedata_dic()
        game_data['title']     = self.candidate['game_name']
        game_data['year']      = game_year
        game_data['genre']     = game_genre
        game_data['developer'] = game_developer
        game_data['nplayers']  = ''
        game_data['esrb']      = ''
        game_data['plot']      = game_plot

        return game_data

    def get_assets(self, asset_info, status_dic):
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
        log_debug('GameFAQs._scraper_resolve_asset_URL() Get image from "{}" for asset type {}'.format(
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
                log_debug('GameFAQs._scraper_resolve_asset_URL() Found match {}'.format(image_on_page['alt']))
                return image_on_page['url']
        log_debug('GameFAQs._scraper_resolve_asset_URL() No correct match')

        return '', ''

    # NOT IMPLEMENTED YET.
    def resolve_asset_URL_extension(self, candidate, image_url, status_dic): return None

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
            log_debug('MobyGames._scraper_get_assets_all() Cache hit "{0}"'.format(cache_key))
            asset_list = self.all_asset_cache[cache_key]
        else:
            log_debug('MobyGames._scraper_get_assets_all() Cache miss "{0}"'.format(cache_key))
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
        log_debug('GameFAQs._scraper_get_assets_all() Get asset data from {}'.format(url))
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
# Implementation logic of this scraper is very similar to ScreenScraper.
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
        # --- Pass down common scraper settings ---
        super(ArcadeDB, self).__init__(settings)

    # --- Base class abstract methods ------------------------------------------------------------
    def get_name(self): return 'ArcadeDB'

    def get_filename(self): return 'ADB'

    def supports_disk_cache(self): return True

    def supports_search_string(self): return False

    def supports_metadata_ID(self, metadata_ID):
        return True if metadata_ID in ArcadeDB.supported_metadata_list else False

    def supports_metadata(self): return True

    def supports_asset_ID(self, asset_ID):
        return True if asset_ID in ArcadeDB.supported_asset_list else False

    def supports_assets(self): return True
            
    # ArcadeDB does not require any API keys.
    def check_before_scraping(self, status_dic): return status_dic

    # Search term is always None for this scraper.
    def get_candidates(self, search_term, rom_FN, rom_checksums_FN, platform, status_dic):
        # --- If scraper is disabled return immediately and silently ---
        if self.scraper_disabled:
            # If the scraper is disabled return None and do not mark error in status_dic.
            log_debug('ArcadeDB.get_candidates() Scraper disabled. Returning empty data.')
            return None

        # Prepare data for scraping.
        # rombase = rom_FN.getBase()
        rombase_noext = rom_FN.getBaseNoExt()

        # --- Request is not cached. Get candidates and introduce in the cache ---
        # ArcadeDB QUERY_MAME returns absolutely everything about a single ROM, including
        # metadata, artwork, etc. This data must be cached in this object for every request done.
        # See ScreenScraper comments for more info about the implementation.
        # log_debug('ArcadeDB.get_candidates() search_term   "{0}"'.format(search_term))
        # log_debug('ArcadeDB.get_candidates() rombase       "{0}"'.format(rombase))
        log_debug('ArcadeDB.get_candidates() rombase_noext "{0}"'.format(rombase_noext))
        log_debug('ArcadeDB.get_candidates() AEL platform  "{0}"'.format(platform))
        json_response_dic = self._get_QUERY_MAME(rombase_noext, platform, status_dic)
        if not status_dic['status']: return None

        # --- Return cadidate list ---
        num_games = len(json_response_dic['result'])
        candidate_list = []
        if num_games == 0:
            log_debug('ArcadeDB.get_candidates() Scraper found no game.')
        elif num_games == 1:
            log_debug('ArcadeDB.get_candidates() Scraper found one game.')
            gameinfo_dic = json_response_dic['result'][0]
            candidate = self._new_candidate_dic()
            candidate['id'] = rombase_noext
            candidate['display_name'] = gameinfo_dic['title']
            candidate['platform'] = platform
            candidate['scraper_platform'] = platform
            candidate['order'] = 1
            candidate_list.append(candidate)

            # --- Add candidate games to the cache ---
            log_debug('ArcadeDB.get_candidates() Adding to internal cache "{}"'.format(
                self.cache_key))
            self._update_disk_cache(Scraper.CACHE_INTERNAL, self.cache_key, json_response_dic)
        else:
            raise ValueError('Unexpected number of games returned (more than one).')

        return candidate_list

    def get_metadata(self, status_dic):
        # --- If scraper is disabled return immediately and silently ---
        if self.scraper_disabled:
            log_debug('ArcadeDB.get_metadata() Scraper disabled. Returning empty data.')
            return self._new_gamedata_dic()

        # --- Retrieve json_response_dic from internal cache ---
        if self._check_disk_cache(Scraper.CACHE_INTERNAL, self.cache_key):
            log_debug('ArcadeDB.get_metadata() Internal cache hit "{0}"'.format(self.cache_key))
            json_response_dic = self._retrieve_from_disk_cache(Scraper.CACHE_INTERNAL, self.cache_key)
        else:
            raise ValueError('Logic error')

        # --- Parse game metadata ---
        gameinfo_dic = json_response_dic['result'][0]
        gamedata = self._new_gamedata_dic()
        gamedata['title']     = gameinfo_dic['title']
        gamedata['year']      = gameinfo_dic['year']
        gamedata['genre']     = gameinfo_dic['genre']
        gamedata['developer'] = gameinfo_dic['manufacturer']
        gamedata['nplayers']  = str(gameinfo_dic['players'])
        gamedata['esrb']      = DEFAULT_META_ESRB
        gamedata['plot']      = gameinfo_dic['history']

        return gamedata

    def get_assets(self, asset_info, status_dic):
        # --- If scraper is disabled return immediately and silently ---
        if self.scraper_disabled:
            log_debug('ArcadeDB.get_assets() Scraper disabled. Returning empty data.')
            return []

        log_debug('ArcadeDB.get_assets() Getting assets {} (ID {}) for candidate ID "{}"'.format(
            asset_info.name, asset_info.id, self.candidate['id']))

        # --- Retrieve json_response_dic from internal cache ---
        if self._check_disk_cache(Scraper.CACHE_INTERNAL, self.cache_key):
            log_debug('ArcadeDB.get_assets() Internal cache hit "{0}"'.format(self.cache_key))
            json_response_dic = self._retrieve_from_disk_cache(Scraper.CACHE_INTERNAL, self.cache_key)
        else:
            raise ValueError('Logic error')

        # --- Parse game assets ---
        gameinfo_dic = json_response_dic['result'][0]
        all_asset_list = self._retrieve_all_assets(gameinfo_dic, status_dic)
        if not status_dic['status']: return None
        asset_list = [asset_dic for asset_dic in all_asset_list if asset_dic['asset_ID'] == asset_info.id]
        log_debug('ArcadeDB.get_assets() Total assets {0} / Returned assets {1}'.format(
            len(all_asset_list), len(asset_list)))

        return asset_list

    def resolve_asset_URL(self, selected_asset, status_dic):
        url = selected_asset['url']
        url_log = self._clean_URL_for_log(url)

        return url, url_log

    def resolve_asset_URL_extension(self, selected_asset, image_url, status_dic):
        # All ArcadeDB images are in PNG format?
        return 'png'

    # --- This class own methods -----------------------------------------------------------------
    # Plumbing function to get the cached jeu_dic dictionary returned by ScreenScraper.
    # Cache must be lazy loaded before calling this function.
    def debug_get_QUERY_MAME_dic(self, candidate):
        log_debug('ArcadeDB.debug_get_QUERY_MAME_dic() Internal cache retrieving "{}"'.format(
            self.cache_key))
        json_response_dic = self._retrieve_from_disk_cache(Scraper.CACHE_INTERNAL, self.cache_key)

        return json_response_dic

    # Call ArcadeDB API only function to retrieve all game metadata.
    def _get_QUERY_MAME(self, rombase_noext, platform, status_dic):
        game_name = rombase_noext
        log_debug('ArcadeDB._get_QUERY_MAME() game_name "{0}"'.format(game_name))

        # --- Build URL ---
        url_a = 'http://adb.arcadeitalia.net/service_scraper.php?ajax=query_mame'
        url_b = '&game_name={}'.format(game_name)
        url = url_a + url_b

        # --- Grab and parse URL data ---
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('ArcadeDB_get_QUERY_MAME.json', json_data)

        return json_data

    # Returns all assets found in the gameinfo_dic dictionary.
    def _retrieve_all_assets(self, gameinfo_dic, status_dic):
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

    # No need for URL cleaning in ArcadeDB.
    def _clean_URL_for_log(self, url): return url

    # Retrieve URL and decode JSON object.
    # ArcadeDB API info http://adb.arcadeitalia.net/service_scraper.php
    #
    # * ArcadeDB has no API restrictions.
    # * When a game search is not succesfull ArcadeDB returns valid JSON with an empty list.
    def _retrieve_URL_as_JSON(self, url, status_dic):
        page_data_raw, http_code = net_get_URL(url, self._clean_URL_for_log(url))
        # self._dump_file_debug('ArcadeDB_data_raw.txt', page_data_raw)

        # --- Check HTTP error codes ---
        if http_code != 200:
            try:
                json_data = json.loads(page_data_raw)
                error_msg = json_data['message']
            except:
                error_msg = 'Unknown/unspecified error.'
            log_error('ArcadeDB msg "{}"'.format(error_msg))
            self._handle_error(status_dic, 'HTTP code {} message "{}"'.format(http_code, error_msg))
            return None

        # If page_data_raw is None at this point is because of an exception in net_get_URL()
        # which is not urllib2.HTTPError.
        if page_data_raw is None:
            self._handle_error(status_dic, 'Network error/exception in net_get_URL()')
            return None

        # Convert data to JSON.
        try:
            json_data = json.loads(page_data_raw)
        except Exception as ex:
            self._handle_exception(ex, status_dic, 'Error decoding JSON data from ArcadeDB.')
            return None

        return json_data

# ------------------------------------------------------------------------------------------------
# SteamGridDB online scraper.
#
# | Site     | https://www.steamgriddb.com        |
# | API info | https://www.steamgriddb.com/api/v2 |
# ------------------------------------------------------------------------------------------------
class SteamGridDB(Scraper):
    # --- Class variables ------------------------------------------------------------------------
    supported_metadata_list = [
    ]
    supported_asset_list = [
        ASSET_BOXFRONT_ID,
        ASSET_CLEARLOGO_ID,
        ASSET_FANART_ID
    ]
    asset_name_mapping = {
        'grids'   : ASSET_BOXFRONT_ID,
        'logos'   : ASSET_CLEARLOGO_ID,
        'heroes'  : ASSET_FANART_ID
    }
    # --- Constructor ----------------------------------------------------------------------------
    def __init__(self, settings):
        # --- This scraper settings ---
        self.api_key = settings['scraper_steamgriddb_apikey']

        # --- Misc stuff ---
        self.cache_candidates = {}
        self.cache_metadata = {}
        self.cache_assets = {}
        self.all_asset_cache = {}
        # --- Pass down common scraper settings ---
        super(SteamGridDB, self).__init__(settings)

    # --- Base class abstract methods ------------------------------------------------------------
    def get_name(self): return 'SteamGridDB'

    def get_filename(self): return 'SteamGridDB'

    def supports_disk_cache(self): return True

    def supports_search_string(self): return True

    def supports_metadata_ID(self, metadata_ID): return False

    def supports_metadata(self): return False

    def supports_asset_ID(self, asset_ID):
        return True if asset_ID in SteamGridDB.supported_asset_list else False

    def supports_assets(self): return True

    # If the SteamGridDB API key is not configured in the settings then disable the scraper
    # and print an error.
    def check_before_scraping(self, status_dic):
        if self.api_key:
            log_error('SteamGridDB.check_before_scraping() SteamGridDB API key looks OK.')
            return
        log_error('SteamGridDB.check_before_scraping() SteamGridDB API key not configured.')
        log_error('SteamGridDB.check_before_scraping() Disabling SteamGridDB scraper.')
        self.scraper_disabled = True
        status_dic['status'] = False
        status_dic['dialog'] = KODI_MESSAGE_DIALOG
        status_dic['msg'] = (
            'AEL requires your SteamGridDB API key. '
            'Visit https://www.steamgriddb.com/api/v2#section/Authentication for directions about how to get your key '
            'and introduce the API key in AEL addon settings.'
        )

    def get_candidates(self, search_term, rom_FN, rom_checksums_FN, platform, status_dic):
        # --- If scraper is disabled return immediately and silently ---
        if self.scraper_disabled:
            # If the scraper is disabled return None and do not mark error in status_dic.
            log_debug('SteamGridDB.get_candidates() Scraper disabled. Returning empty data.')
            return None

        if platform <> 'Microsoft Windows':
            log_error('SteamGridDB.get_candidates() SteamGridDB called with incompatible platform')
            status_dic['status'] = False
            status_dic['dialog'] = KODI_MESSAGE_DIALOG
            status_dic['msg'] = (
                'SteamGridDB only supports Windows as a platform.'
            )

        # Prepare data for scraping.
        rombase_noext = rom_FN.getBaseNoExt()

        # --- Request is not cached. Get candidates and introduce in the cache ---
        log_debug('SteamGridDB.get_candidates() search_term          "{0}"'.format(search_term))
        log_debug('SteamGridDB.get_candidates() rombase_noext        "{0}"'.format(rombase_noext))
        log_debug('SteamGridDB.get_candidates() AEL platform         "{0}"'.format(platform))
        candidate_list = self._search_candidates(search_term, platform, status_dic)
        if not status_dic['status']: return None

        return candidate_list

    # SteamGridDB does not support metadata
    def get_metadata(self, status_dic):
        return None

    # This function may be called many times in the ROM Scanner.
    # See comments for this function in the Scraper abstract class.
    def get_assets(self, asset_info, status_dic):
        # --- If scraper is disabled return immediately and silently ---
        if self.scraper_disabled:
            log_debug('SteamGridDB.get_assets() Scraper disabled. Returning empty data.')
            return []

        log_debug('SteamGridDB.get_assets() Getting assets {} (ID {}) for candidate ID "{}"'.format(
            asset_info.name, asset_info.id, self.candidate['id']))

        # Get all assets for candidate. _retrieve_all_assets() caches all assets for a candidate.
        # Then select asset of a particular type.
        all_asset_list = self._retrieve_all_assets(self.candidate, status_dic)
        if not status_dic['status']: return None
        asset_list = [asset_dic for asset_dic in all_asset_list if asset_dic['asset_ID'] == asset_info.id]
        log_debug('SteamGridDB::get_assets() Total assets {0} / Returned assets {1}'.format(
            len(all_asset_list), len(asset_list)))

        return asset_list

    # SteamGridDB returns both the asset thumbnail URL and the full resolution URL so in
    # this scraper this method is trivial.
    def resolve_asset_URL(self, selected_asset, status_dic):
        # Transform http to https
        url = selected_asset['url']
        if url[0:4] == 'http': url = 'https' + url[4:]

        return url, url

    def resolve_asset_URL_extension(self, selected_asset, image_url, status_dic):
        return text_get_URL_extension(image_url)

    def download_image(self, image_url, image_local_path):
        self._wait_for_API_request(100)
        # net_download_img() never prints URLs or paths.
        net_download_img(image_url, image_local_path)
        
        # failed? retry after 5 seconds
        if not image_local_path.exists():
            log_debug('Download failed. Retry after 5 seconds')
            self._wait_for_API_request(5000)
            net_download_img(image_url, image_local_path)

    # --- Retrieve list of games ---
    def _search_candidates(self, search_term, platform, status_dic):
        # --- Retrieve JSON data with list of games ---
        search_string_encoded = urllib.quote_plus(search_term.encode('utf8'))
        url = 'https://www.steamgriddb.com/api/v2/search/autocomplete/{}'.format(search_string_encoded)
        
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('SteamGridDB_get_candidates.json', json_data)

        # --- Parse game list ---
        games_json = json_data['data']
        candidate_list = []
        for item in games_json:
            title = item['name']
            candidate = self._new_candidate_dic()
            candidate['id'] = item['id']
            candidate['display_name'] = title
            candidate['platform'] = platform
            candidate['scraper_platform'] = platform
            candidate['order'] = 1

            # Increase search score based on our own search.
            if title.lower() == search_term.lower():          candidate['order'] += 2
            if title.lower().find(search_term.lower()) != -1: candidate['order'] += 1
            candidate_list.append(candidate)

        # --- Sort game list based on the score. High scored candidates go first ---
        candidate_list.sort(key = lambda result: result['order'], reverse = True)

        return candidate_list

    # Get ALL available assets for game.
    # Cache all assets in the internal disk cache.
    def _retrieve_all_assets(self, candidate, status_dic):
        # --- Cache hit ---
        if self._check_disk_cache(Scraper.CACHE_INTERNAL, self.cache_key):
            log_debug('SteamGridDB._retrieve_all_assets() Internal cache hit "{0}"'.format(self.cache_key))
            return self._retrieve_from_disk_cache(Scraper.CACHE_INTERNAL, self.cache_key)

        # --- Cache miss. Retrieve data and update cache ---
        log_debug('SteamGridDB._retrieve_all_assets() Internal cache miss "{0}"'.format(self.cache_key))
               
        cover_assets = self._retrieve_cover_assets(candidate, status_dic)
        if not status_dic['status']: return None
        fanart_assets = self._retrieve_fanart_assets(candidate, status_dic)
        if not status_dic['status']: return None
        logo_assets = self._retrieve_logo_assets(candidate, status_dic)
        if not status_dic['status']: return None
        
        asset_list = cover_assets + fanart_assets + logo_assets
        log_debug('SteamGridDB._retrieve_all_assets() A total of {0} assets found for candidate ID {1}'.format(
            len(asset_list), candidate['id']))

        # --- Put metadata in the cache ---
        log_debug('SteamGridDB._retrieve_all_assets() Adding to internal cache "{0}"'.format(self.cache_key))
        self._update_disk_cache(Scraper.CACHE_INTERNAL, self.cache_key, asset_list)

        return asset_list

    def _retrieve_cover_assets(self, candidate, status_dic):
        log_debug('SteamGridDB._retrieve_cover_assets() Getting Covers...')
        url = 'https://www.steamgriddb.com/api/v2/grids/game/{}'.format(candidate['id'])
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('SteamGridDB_assets_covers.json', json_data)

        # --- Parse images page data ---
        asset_list = []
        for image_data in json_data['data']:
            asset_data = self._new_assetdata_dic()
            asset_data['asset_ID'] = ASSET_BOXFRONT_ID
            asset_data['display_name'] = "{} by {}".format(image_data['style'], image_data['author']['name'])
            asset_data['url_thumb'] = image_data['thumb']
            asset_data['url'] = image_data['url']
            if self.verbose_flag: log_debug('Found cover {0}'.format(asset_data['url_thumb']))
            asset_list.append(asset_data)
            
        log_debug('SteamGridDB._retrieve_cover_assets() Found {} cover assets for candidate #{}'.format(
            len(asset_list), candidate['id']))

        return asset_list
    
    def _retrieve_logo_assets(self, candidate, status_dic):
        log_debug('SteamGridDB._retrieve_logo_assets() Getting Logos...')
        url = 'https://www.steamgriddb.com/api/v2/logos/game/{}'.format(candidate['id'])
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('SteamGridDB_assets_logos.json', json_data)

        # --- Parse images page data ---
        asset_list = []
        for image_data in json_data['data']:
            asset_data = self._new_assetdata_dic()
            asset_data['asset_ID'] = ASSET_CLEARLOGO_ID
            asset_data['display_name'] = "{} by {}".format(image_data['style'], image_data['author']['name'])
            asset_data['url_thumb'] = image_data['thumb']
            asset_data['url'] = image_data['url']
            if self.verbose_flag: log_debug('Found logo {0}'.format(asset_data['url_thumb']))
            asset_list.append(asset_data)
            
        log_debug('SteamGridDB._retrieve_logo_assets() Found {} logo assets for candidate #{}'.format(
            len(asset_list), candidate['id']))

        return asset_list
    
    def _retrieve_fanart_assets(self, candidate, status_dic):
        log_debug('SteamGridDB._retrieve_fanart_assets() Getting Fanarts...')
        url = 'https://www.steamgriddb.com/api/v2/heroes/game/{}'.format(candidate['id'])
        json_data = self._retrieve_URL_as_JSON(url, status_dic)
        if not status_dic['status']: return None
        self._dump_json_debug('SteamGridDB_assets_fanarts.json', json_data)

        # --- Parse images page data ---
        asset_list = []
        for image_data in json_data['data']:
            asset_data = self._new_assetdata_dic()
            asset_data['asset_ID'] = ASSET_FANART_ID
            asset_data['display_name'] = "{} by {}".format(image_data['style'], image_data['author']['name'])
            asset_data['url_thumb'] = image_data['thumb']
            asset_data['url'] = image_data['url']
            if self.verbose_flag: log_debug('Found fanart {0}'.format(asset_data['url_thumb']))
            asset_list.append(asset_data)
            
        log_debug('SteamGridDB._retrieve_fanart_assets() Found {} fanart assets for candidate #{}'.format(
            len(asset_list), candidate['id']))

        return asset_list

    # Retrieve URL and decode JSON object.
    # SteamGridDB API info https://www.steamgriddb.com/api/v2
    #
    # * When the API key is not configured or invalid SteamGridDB returns HTTP status code 401.
    def _retrieve_URL_as_JSON(self, url, status_dic, retry=0):
        self._wait_for_API_request(100)
        page_data_raw, http_code = net_get_URL(url, None, {"Authorization": "Bearer {}".format(self.api_key) })
        self.last_http_call = datetime.now()

        # --- Check HTTP error codes ---
        if http_code == 400:
            # Code 400 describes an error. See API description page.
            log_debug('SteamGridDB._retrieve_URL_as_JSON() HTTP status 400: general error.')
            self._handle_error(status_dic, 'Bad HTTP status code {}'.format(http_code))
            return None
        elif http_code == 429 and retry < Scraper.RETRY_THRESHOLD:
            log_debug('SteamGridDB._retrieve_URL_as_JSON() HTTP status 429: Limit exceeded.')
            # Number of requests limit, wait at least 2 minutes. Increments with every retry.
            amount_seconds = 120*(retry+1)
            wait_till_time = datetime.now() + timedelta(seconds=amount_seconds)
            kodi_dialog_OK('You\'ve exceeded the max rate limit.', 
                           'Respecting the website and we wait at least till {}.'.format(wait_till_time))
            self._wait_for_API_request(amount_seconds*1000)
            # waited long enough? Try again
            retry_after_wait = retry + 1
            return self._retrieve_URL_as_JSON(url, status_dic, retry_after_wait)
        elif http_code == 404:
            # Code 404 means the Game was not found. Return None but do not mark
            # error in status_dic.
            log_debug('SteamGridDB._retrieve_URL_as_JSON() HTTP status 404: no candidates found.')
            return None
        elif http_code != 200:
            # Unknown HTTP status code.
            self._handle_error(status_dic, 'Bad HTTP status code {}'.format(http_code))
            return None
        
        # If page_data_raw is None at this point is because of an exception in net_get_URL()
        # which is not urllib2.HTTPError.
        if page_data_raw is None:
            self._handle_error(status_dic, 'Network error/exception in net_get_URL()')
            return None

        # Convert data to JSON.
        try:
            return json.loads(page_data_raw)
        except Exception as ex:
            log_error('Error decoding JSON data from SteamGridDB.')
            self._handle_error(status_dic, 'Error decoding JSON data from SteamGridDB.')
            return None
        
class Libretro(Scraper):
    
    # --- Constructor ----------------------------------------------------------------------------
    def __init__(self, settings):
        # --- Pass down common scraper settings ---
        super(Libretro, self).__init__(settings)