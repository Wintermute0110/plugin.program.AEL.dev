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

# --- AEL packages ---
from .constants import *
from .platforms import *
from .utils import *
from .assets import *
from .disk_IO import *
from .net_IO import *

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
        log_debug('ScraperFactory::__init__() BEGIN ...')
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

    # Return a list with instantiated scrapers. List always has same order.
    def get_scraper_list(self):
        return list(self.scraper_objs.keys())

    def get_name(self, scraper_ID):
        return self.scraper_objs[scraper_ID].get_name()

    def supports_metadata(self, scraper_ID, metadata_ID):
        return self.scraper_objs[scraper_ID].supports_metadata_ID(metadata_ID)

    def supports_asset(self, scraper_ID, asset_ID):
        return self.scraper_objs[scraper_ID].supports_asset_ID(asset_ID)

    def get_metadata_scraper_menu_list(self):
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

    # Traverses all valid scraper objects and checks if the scraper supports the particular
    # kind of asset. If so, it adds the scraper name to the list.
    #
    # @return: [list of strings]
    def get_asset_scraper_menu_list(self, asset_ID):
        AInfo = assets_get_info_scheme(asset_ID)
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
        log_debug('ScraperFactory::create_scanner() BEGIN ...')
        strategy_obj = ScrapeStrategy(self.PATHS, self.settings)

        # --- Read addon settings and configure the scrapers selected -----------------------------
        if launcher['platform'] == 'MAME':
            metadata_scraper_list = [ self.scraper_objs[SCRAPER_NULL_ID] ]
            asset_scraper_list = [ self.scraper_objs[SCRAPER_NULL_ID] ]
        else:
            # Force Null scraper
            # metadata_scraper_list = [ self.scraper_objs[SCRAPER_NULL_ID] ]
            # asset_scraper_list = [ self.scraper_objs[SCRAPER_NULL_ID] ]
            # Force Mobygames scraper
            metadata_scraper_list = [ self.scraper_objs[SCRAPER_MOBYGAMES_ID] ]
            asset_scraper_list = [ self.scraper_objs[SCRAPER_MOBYGAMES_ID] ]
        strategy_obj.metadata_scraper_list = metadata_scraper_list
        strategy_obj.asset_scraper_list = asset_scraper_list

        # --- Add launcher properties to ScrapeStrategy object ---
        strategy_obj.platform = launcher['platform']

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
    # @param PATHS: PATH object.
    # @param settings: [dict] Addon settings.
    # @param launcher: [dict] Launcher dictionary.
    # @param pdialog: [KodiProgressDialog] object instance.
    # @param pdialog_verbose: [bool] verbose progress dialog.
    def __init__(self, PATHS, settings):
        log_debug('ScrapeStrategy::__init__() BEGIN ...')
        self.PATHS = PATHS
        self.settings = settings

        # --- Read addon settings and configure scraper setings ---
        # scan_metadata_policy values="None|NFO Files|NFO Files + Scrapers|Scrapers"
        # scan_asset_policy values="Local images|Local images + Scrapers|Scrapers"
        self.scan_metadata_policy    = self.settings['scan_metadata_policy']
        self.scan_asset_policy       = self.settings['scan_asset_policy']
        # metadata_scraper_mode values="Manual|Automatic"
        # asset_scraper_mode values="Manual|Automatic"
        self.metadata_scraper_mode   = self.settings['metadata_scraper_mode']
        self.asset_scraper_mode      = self.settings['asset_scraper_mode']
        # Scanner boolean options
        self.scan_ignore_scrap_title = self.settings['scan_ignore_scrap_title']
        self.scan_clean_tags         = self.settings['scan_clean_tags']

    # Call this function before the scanner starts.
    def begin_ROM_scanner(self, launcher, pdialog, pdialog_verbose):
        log_debug('ScrapeStrategy::begin_ROM_scanner() BEGIN ...')
        self.launcher = launcher
        self.platform = launcher['platform']
        self.pdialog = pdialog
        self.pdialog_verbose = pdialog_verbose

    def check_launcher_unset_asset_dirs(self):
        log_debug('ScrapeStrategy::check_launcher_unset_asset_dirs() BEGIN ...')
        self.enabled_asset_list = asset_get_enabled_asset_list(self.launcher)
        self.unconfigured_name_list = asset_get_unconfigured_name_list(self.enabled_asset_list)

    # Called by the ROM scanner. Fills in the ROM metadata.
    #
    # @param romdata: [dict] ROM data dictionary. Mutable and edited by assignment.
    # @param ROM: [Filename] ROM filename object.
    def process_ROM_metadata(self, romdata, ROM):
        log_debug('ScrapeStrategy::process_ROM_metadata() BEGIN ...')

        # --- Metadata actions ---
        ACTION_META_TITLE_ONLY = 100
        ACTION_META_NFO_FILE   = 200
        ACTION_META_SCRAPER    = 300

        # --- Test if NFO file exists ---
        NFO_file = FileName(ROM.getPath_noext() + '.nfo')
        NFO_file_found = True if NFO_file.exists() else False
        if NFO_file_found: log_debug('NFO file found "{0}"'.format(NFO_file.getPath()))
        else:              log_debug('NFO file NOT found "{0}"'.format(NFO_file.getPath()))

        # --- Determine metadata action -----------------------------------------------------------
        # Action depends configured metadata policy and wheter the NFO files was found or not.
        metadata_action = ACTION_META_TITLE_ONLY
        if self.scan_metadata_policy == 0:
            log_verb('Metadata policy: Read NFO file OFF | Scraper OFF')
            log_verb('Metadata policy: Only cleaning ROM name.')
            metadata_action = ACTION_META_TITLE_ONLY

        elif self.scan_metadata_policy == 1:
            log_verb('Metadata policy: Read NFO file ON | Scraper OFF')
            if NFO_file_found:
                log_verb('Metadata policy: NFO file found.')
                metadata_action = ACTION_META_NFO_FILE
            else:
                log_verb('Metadata policy: NFO file not found. Only cleaning ROM name')
                metadata_action = ACTION_META_TITLE_ONLY

        elif self.scan_metadata_policy == 2 and NFO_file_found:
            log_verb('Metadata policy: Read NFO file ON | Scraper ON')
            if NFO_file_found:
                log_verb('Metadata policy: NFO file found. Scraper not used.')
                metadata_action = ACTION_META_NFO_FILE
            else:
                log_verb('Metadata policy: NFO file not found. Using scraper.')
                metadata_action = ACTION_META_SCRAPER

        elif self.scan_metadata_policy == 3:
            log_verb('Metadata policy: Read NFO file OFF | Scraper ON')
            log_verb('Metadata policy: Using metadata scraper.')
            metadata_action = ACTION_META_SCRAPER

        else:
            log_error('Invalid scan_metadata_policy value = {0}'.format(self.scan_metadata_policy))

        # --- Execute metadata action -------------------------------------------------------------
        if metadata_action == ACTION_META_TITLE_ONLY:
            if self.pdialog_verbose:
                self.pdialog.updateMessage2('Formatting ROM name...')
            romdata['m_name'] = text_format_ROM_title(ROM.getBase_noext(), self.scan_clean_tags)

        elif metadata_action == ACTION_META_NFO_FILE:
            if self.pdialog_verbose:
                self.pdialog.updateMessage2('Loading NFO file {0}'.format(NFO_file.getPath()))
            # If this point is reached the NFO file was found previosly.
            log_debug('Loading NFO P "{0}"'.format(NFO_file.getPath()))
            nfo_dic = fs_import_ROM_NFO_file_scanner(NFO_file)
            # NOTE <platform> is chosen by AEL, never read from NFO files. Indeed, platform
            #      is a Launcher property, not a ROM property.
            romdata['m_name']      = nfo_dic['title']     # <title>
            romdata['m_year']      = nfo_dic['year']      # <year>
            romdata['m_genre']     = nfo_dic['genre']     # <genre>
            romdata['m_developer'] = nfo_dic['developer'] # <developer>
            romdata['m_nplayers']  = nfo_dic['nplayers']  # <nplayers>
            romdata['m_esrb']      = nfo_dic['esrb']      # <esrb>
            romdata['m_rating']    = nfo_dic['rating']    # <rating>
            romdata['m_plot']      = nfo_dic['plot']      # <plot>

        elif metadata_action == ACTION_META_SCRAPER:
            self._scrap_ROM_metadata_scanner(romdata, ROM)

        else:
            log_error('Invalid metadata_action value = {0}'.format(metadata_action))

    # Called by the ROM scanner.
    #
    # @param romdata: [dict] ROM data dictionary. Mutable and edited by assignment.
    # @param ROM: [Filename] ROM filename object.
    def process_ROM_assets(self, romdata, ROM):
        log_debug('ScrapeStrategy::process_ROM_assets() BEGIN ...')

        # --- Search for local artwork/assets ---
        # Always look for local assets whatever the scanner settings.
        local_asset_list = assets_search_local_cached_assets(self.launcher, ROM, self.enabled_asset_list)

        # --- Asset scraping ---
        if self.scan_asset_policy == 0:
            log_verb('Asset policy: Local images ON | Scraper OFF')
            for i, asset_ID in enumerate(ROM_ASSET_ID_LIST):
                A = assets_get_info_scheme(asset_ID)
                romdata[A.key] = local_asset_list[i]

        elif self.scan_asset_policy == 1:
            log_verb('Asset policy: Local images ON | Scraper ON')
            for i, asset_ID in enumerate(ROM_ASSET_ID_LIST):
                A = assets_get_info_scheme(asset_ID)
                if not self.enabled_asset_list[i]:
                    romdata[A.key] = ''
                    log_verb('Skipped {0} (dir not configured)'.format(A.name))
                    continue
                if local_asset_list[i]:
                    log_verb('Local {0} FOUND'.format(A.name))
                    romdata[A.key] = local_asset_list[i]
                else:
                    log_verb('Local {0} NOT found. Scraping...'.format(A.name))
                    romdata[A.key] = self._scrap_ROM_asset_scanner(asset_ID, local_asset_list[i], ROM)

        elif self.scan_asset_policy == 2:
            log_verb('Asset policy: Local images OFF | Scraper ON')
            for i, asset_ID in enumerate(ROM_ASSET_ID_LIST):
                A = assets_get_info_scheme(asset_ID)
                if not self.enabled_asset_list[i]:
                    romdata[A.key] = ''
                    log_verb('Skipped {0} (dir not configured)'.format(A.name))
                    continue
                romdata[A.key] = self._scrap_ROM_asset_scanner(asset_ID, local_asset_list[i], ROM)

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

        return romdata

    #
    # Scraps ROM metadata in the ROM scanner.
    #
    def _scrap_ROM_metadata_scanner(self, romdata, ROM):
        log_debug('ScrapeStrategy::_scrap_ROM_metadata_scanner() BEGIN...')

        # For now just use the first scraper
        scraper_obj = self.metadata_scraper_list[0]
        scraper_name = scraper_obj.get_name()
        log_debug('Using scraper "{0}"'.format(scraper_name))

        # --- Update scanner progress dialog ---
        if self.pdialog_verbose:
            scraper_text = 'Scraping metadata with {0} (Searching...)'.format(scraper_name)
            self.pdialog.updateMessage2(scraper_text)

        # --- Do a search and get a list of games ---
        rom_name_scraping = text_format_ROM_name_for_scraping(ROM.getBase_noext())
        candidates = scraper_obj.get_candidates(rom_name_scraping, ROM.getBase_noext(), self.platform)
        log_debug('Scraper {0} found {1} candidate/s'.format(scraper_name, len(candidates)))
        if not candidates:
            log_verb('Found no candidates after searching. Cleaning ROM name only.')
            romdata['m_name'] = text_format_ROM_title(ROM.getBase_noext(), self.scan_clean_tags)
            return

        # --- Choose game to download metadata ---
        # metadata_scraper_mode values="Semi-automatic|Automatic"
        if self.metadata_scraper_mode == 0:
            log_debug('Metadata manual scraping')
            if len(candidates) == 1:
                log_debug('get_candidates() returned 1 game. Automatically selected.')
                select_candidate_idx = 0
            else:
                log_debug('Metadata manual scraping. User chooses game.')
                self.pdialog.close()
                # Display game list found so user choses.
                game_name_list = [candidate['display_name'] for candidate in candidates]
                select_candidate_idx = xbmcgui.Dialog().select(
                    'Select game for ROM {0}'.format(ROM.getBase_noext()), game_name_list)
                if select_candidate_idx < 0: select_candidate_idx = 0
                self.pdialog.reopen()
        elif self.metadata_scraper_mode == 1:
            log_debug('Metadata automatic scraping. Selecting first result.')
            select_candidate_idx = 0
        else:
            raise AddonError('Invalid metadata_scraper_mode {0}'.format(self.metadata_scraper_mode))

        # --- Update scanner progress dialog ---
        if self.pdialog_verbose:
            scraper_text = 'Scraping metadata with {0} (Getting metadata...)'.format(scraper_obj.get_name())
            self.pdialog.updateMessage2(scraper_text)

        # --- Grab metadata for selected game and put into ROM ---
        game_data = scraper_obj.get_metadata(candidates[select_candidate_idx])
        scraper_applied = self._apply_candidate_on_metadata_old(game_data, romdata, ROM)

        # --- Update ROM NFO file after scraping ---
        if self.settings['scan_update_NFO_files']:
            log_debug('User wants to update NFO file after scraping')
            fs_export_ROM_NFO(romdata, False)

    #
    # Returns a valid filename of the downloaded scrapped image, filename of local image
    # or empty string if scraper finds nothing or download failed.
    #
    # @param asset_ID
    # @param local_asset_path: [str]
    # @param ROM: [Filename object]
    # @return: [str] Filename string with the asset path.
    def _scrap_ROM_asset_scanner(self, asset_ID, local_asset_path, ROM):
        # --- Cached frequent used things ---
        asset_info = assets_get_info_scheme(asset_ID)
        asset_name = asset_info.name
        asset_dir_FN  = FileName(self.launcher[asset_info.path_key])
        asset_path_noext_FN = assets_get_path_noext_DIR(asset_info, asset_dir_FN, ROM)
        log_debug('ScrapeStrategy::_scrap_ROM_asset_scanner() Scraping {0}...'.format(asset_name))

        # --- For now just use the first configured asset scraper ---
        scraper_obj = self.metadata_scraper_list[0]
        scraper_name = scraper_obj.get_name()
        log_debug('Using scraper "{0}"'.format(scraper_name))

        # By default always use local image if found in case scraper fails.
        ret_asset_path = local_asset_path

        # --- If scraper does not support particular asset return inmediately ---
        if not scraper_obj.supports_asset(asset_ID):
            log_debug('Scraper {0} does not support asset {1}.'.format(scraper_name, asset_name))
            return ret_asset_path

        # --- Updated progress dialog ---
        if self.pdialog_verbose:
            scraper_text = 'Scraping {0} with {1} (Searching...)'.format(asset_name, scraper_name)
            self.pdialog.updateMessage2(scraper_text)
        log_debug('_scrap_ROM_asset_scanner() Scraping {0} with {1}'.format(asset_name, scraper_name))
        log_debug('_scrap_ROM_asset_scanner() local_asset_path "{0}"'.format(local_asset_path))
        log_debug('_scrap_ROM_asset_scanner() asset_path_noext "{0}"'.format(asset_path_noext_FN.getPath()))

        # --- Call scraper and get a list of games ---
        # Note that scraper_obj.get_candidates() always caches information so no need to worry
        # about caches here.
        rom_name_scraping = text_format_ROM_name_for_scraping(ROM.getBase_noext())
        candidates = scraper_obj.get_candidates(rom_name_scraping, ROM.getBase_noext(), self.platform)
        log_debug('Scraper {0} found {1} candidate/s'.format(scraper_name, len(candidates)))
        if not candidates:
            log_verb('Found no candidates after searching.')
            return ret_asset_path

        # --- Choose game to download image ---
        # TODO This function is called many times so if the user chose a game before remember
        #      the election. Now the user is asked to choose a candidate for each asset for the
        #      same game.
        if self.asset_scraper_mode == 0:
            log_debug('Asset manual scraping')
            if len(candidates) == 1:
                log_debug('get_candidates() returned 1 game. Automatically selected.')
                selected_game_index = 0
            else:
                log_debug('{0} manual scraping. User chooses game.'.format(asset_name))
                self.pdialog.close()
                # Display game list found so user choses.
                rom_name_list = [candidate['display_name'] for candidate in candidates]
                selected_game_index = xbmcgui.Dialog().select(
                    '{0} game for ROM "{1}"'.format(scraper_obj.name, ROM.getBase_noext()),
                    rom_name_list)
                if selected_game_index < 0: selected_game_index = 0
                self.pdialog.reopen()
        elif self.asset_scraper_mode == 1:
            log_debug('{0} automatic scraping. Selecting first result.'.format(asset_name))
            selected_game_index = 0
        else:
            raise AddonError('Invalid asset_scraper_mode {0}'.format(self.asset_scraper_mode))
        candidate = candidates[selected_game_index]

        # --- Update scanner progress dialog ---
        if self.pdialog_verbose:
            scraper_text = 'Scraping {0} with {1} (Getting images...)'.format(
                asset_name, scraper_name)
            self.pdialog.updateMessage2(scraper_text)

        # --- Grab list of images/assets for the selected candidate ---
        assetdata_list = scraper_obj.get_assets(candidate, asset_ID)
        log_verb('{0} scraper returned {1} images'.format(asset_name, len(assetdata_list)))
        if not assetdata_list:
            log_debug('{0} scraper get_images() returned no images.'.format(asset_name))
            return ret_asset_path

        # If scraper returns no images return current local asset.
        if len(assetdata_list) == 0:
            log_debug('{0} {1} found no images.'.format(scraper_name, asset_name))
            return ret_asset_path

        # --- Semi-automatic scraping (user choses an image from a list) ---
        if self.asset_scraper_mode == 0:
            # If there is a local image add it to the list and show it to the user
            local_asset_in_list_flag = False
            if local_asset_path:
                local_asset = {
                    'asset_ID'     : asset_ID,
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
        elif self.asset_scraper_mode == 1:
            image_selected_index = 0
        else:
            raise AddonError('Invalid asset_scraper_mode {0}'.format(self.asset_scraper_mode))

        # --- Download scraped image --------------------------------------------------------------
        selected_asset = assetdata_list[image_selected_index]

        # --- Resolve asset URL ---
        log_debug('Resolving asset URL...')
        if self.pdialog_verbose:
            scraper_text = 'Scraping {0} with {1} (Resolving URL...)'.format(
                asset_name, scraper_name)
            self.pdialog.updateMessage2(scraper_text)
        image_url = scraper_obj.resolve_asset_URL(selected_asset)
        image_ext = self.scraper_obj.resolve_asset_URL_extension(image_url)
        log_debug('Resolved {0} to URL "{1}"'.format(asset_name, image_url))
        log_debug('Resolved URL extension "{0}"'.format(image_ext))
        if not image_url or not image_ext:
            log_debug('Error resolving URL')
            return ret_asset_path

        # --- Download image ---
        log_debug('Downloading {0} ...'.format(image_url))
        if self.pdialog_verbose:
            scraper_text = 'Scraping {0} with {1} (Downloading asset...)'.format(
                asset_name, scraper_name)
            self.pdialog.updateMessage2(scraper_text)
        image_local_path = asset_path_noext_FN.append(image_ext).getPath()
        log_verb('Downloading URL  "{0}"'.format(image_url))
        log_verb('Into local file  "{0}"'.format(image_local_path))
        try:
            net_download_img(image_url, image_local_path)
        except socket.timeout:
            kodi_notify_warn('Cannot download {0} image (Timeout)'.format(asset_name))

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
            romdata['m_name'] = text_format_ROM_title(ROM.getBase_noext(), self.scan_clean_tags)
            log_debug('User wants to ignore scraper name. Setting name to "{0}"'.format(romdata['m_name']))
        else:
            romdata['m_name'] = gamedata['title']
            log_debug('User wants scrapped name. Setting name to "{0}"'.format(romdata['m_name']))
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
    def _apply_candidate_on_metadata_new(self, gamedata, rom):
        if not gamedata: return False

        # --- Put metadata into ROM/Launcher object ---
        if self.scraper_settings.ignore_scraped_title:
            rom_name = text_format_ROM_title(rom.getBase_noext(), self.scraper_settings.scan_clean_tags)
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
    # @return: [bool] True if metadata was changed, False otherwise (no need to save DB).
    def scrap_CM_metadata_ROM(self, object_dic, data_dic):
        log_debug('ScrapeStrategy::scrap_CM_metadata_ROM() BEGIN ...')
        # In AEL 0.10.x this data is grabed from the objects, not passed using a dictionary.
        rom_base_noext = data_dic['rom_base_noext']
        scraper_name = self.scraper_obj.get_name()

        # If status if True scraping was OK. If status is False there was some problem.
        # dialog is the type of message to show the user (notify, OK dialog, etc.)
        # msg always has a message to display.
        op_dic = {
            'status' : True,
            'dialog' : KODI_MESSAGE_NOTIFY,
            'msg'    : 'ROM metadata updated',
        }

        # --- Grab candidate game ---
        # If op_dic['status'] = False there was some problem, return inmediately.
        candidate = self._scrap_CM_get_candidate(SCRAPE_ROM, object_dic, data_dic, op_dic)
        if not op_dic['status']: return op_dic

        # --- Grab metadata ---
        pdialog = KodiProgressDialog()
        pdialog.startProgress('{0} scraper. Getting ROM metadata...'.format(scraper_name))
        gamedata = self.scraper_obj.get_metadata(candidate)
        pdialog.endProgress()
        if not gamedata:
            op_dic['status'] = False
            op_dic['dialog'] = KODI_MESSAGE_NOTIFY_WARN
            op_dic['msg'] = 'Cannot download game metadata'

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

        return op_dic

    # Called when editing a launcher by _command_edit_launcher()
    # Note that launcher maybe a ROM launcher or a standalone launcher (game, app)
    # Scrap standalone launcher (typically a game) metadata
    # Always do manual scraping when editing ROMs/Launchers
    #
    # @return: [bool] True if metadata was changed, False otherwise (no need to save DB).
    def scrap_CM_metadata_Launcher(self, object_dic, data_dic):
        log_debug('ScrapeStrategy::scrap_CM_metadata_Launcher() BEGIN ...')
        scraper_name = self.scraper_obj.get_name()

        # See scrap_CM_metadata_ROM() for documentation of op_dic.
        op_dic = {
            'status' : True,
            'dialog' : KODI_MESSAGE_NOTIFY,
            'msg' : 'Launcher metadata updated',
        }

        # --- Grab candidate game ---
        # If op_dic['status'] = False there was some problem, return inmediately.
        candidate = self._scrap_CM_get_candidate(SCRAPE_LAUNCHER, object_dic, data_dic, op_dic)
        if not op_dic['status']: return op_dic

        # --- Grab metadata ---
        pdialog = KodiProgressDialog()
        pdialog.startProgress('{0} scraper. Getting Launcher metadata...'.format(scraper_name))
        gamedata = self.scraper_obj.get_metadata(candiate)
        pdialog.endProgress()
        if not gamedata:
            op_dic['status'] = False
            op_dic['dialog'] = KODI_MESSAGE_NOTIFY_WARN
            op_dic['msg'] = 'Cannot download game metadata'

        # --- Put metadata into launcher dictionary ---
        # Scraper should not change launcher title.
        # 'nplayers' and 'esrb' ignored for launchers
        launcher['m_year']      = gamedata['year']
        launcher['m_genre']     = gamedata['genre']
        launcher['m_developer'] = gamedata['developer']
        launcher['m_plot']      = gamedata['plot']

        return op_dic

    # Called when scraping an asset in the context menu.
    # In the future object_dic will be a Launcher/ROM object, not a dictionary.
    #
    # @return: [dict] op_dic with status flag and error message.
    def scrap_CM_asset(self, object_dic, asset_ID, data_dic):
        # log_debug('ScrapeStrategy::scrap_CM_asset() BEGIN...')

        # --- Cached frequent used things ---
        asset_info = assets_get_info_scheme(asset_ID)
        asset_name = asset_info.name
        # In AEL 0.10.x this data is grabed from the objects, not passed using a dictionary.
        rom_base_noext = data_dic['rom_base_noext']
        platform = data_dic['platform']
        current_asset_FN = data_dic['current_asset_FN']
        asset_path_noext_FN = data_dic['asset_path_noext']
        log_info('ScrapeStrategy::scrap_CM_asset() Scraping {0}...'.format(object_dic['m_name']))

        # --- Cached frequent used things ---
        scraper_name = self.scraper_obj.get_name()

        # If status if True scraping was OK. If status is False there was some problem.
        # dialog is the type of message to show the user.
        # msg always has a message to display.
        op_dic = {
            'status' : True,
            'dialog' : KODI_MESSAGE_NOTIFY,
            'msg' : 'Asset updated',
        }

        # --- Grab candidate game ---
        # If op_dic['status'] = False there was some problem, return inmediately.
        candidate = self._scrap_CM_get_candidate(SCRAPE_ROM, object_dic, data_dic, op_dic)
        if not op_dic['status']: return op_dic

        # --- Grab list of images for the selected game -------------------------------------------
        pdialog = KodiProgressDialog()
        pdialog.startProgress('{0} scraper (Getting assets...)'.format(scraper_name))
        assetdata_list = self.scraper_obj.get_assets(candidate, asset_ID)
        pdialog.endProgress()
        log_verb('{0} {1} scraper returned {2} images'.format(
            scraper_name, asset_name, len(assetdata_list)))
        # Scraper found no assets. Return immediately.
        if not assetdata_list:
            op_dic['status'] = False
            op_dic['dialog'] = KODI_MESSAGE_DIALOG
            op_dic['msg'] = '{0} {1} scraper found no '.format(scraper_name, asset_name) + \
                            'images for game "{0}".'.format(candidate['display_name'])
            return op_dic

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
            op_dic['status'] = False
            op_dic['msg'] = 'Image not changed'
            return op_dic
        # User chose to keep current asset.
        if local_asset_in_list_flag and image_selected_index == 0:
            log_debug('_gui_edit_asset() Selected current image "{0}"'.format(current_asset_FN.getPath()))
            op_dic['status'] = False
            op_dic['msg'] = 'Image not changed'
            return op_dic

        # --- Download scraped image (or use local image) ----------------------------------------
        selected_asset = assetdata_list[image_selected_index]
        log_debug('Selected asset_ID {0}'.format(selected_asset['asset_ID']))
        log_debug('Selected display_name {0}'.format(selected_asset['display_name']))

        # --- Resolve asset URL ---
        log_debug('Resolving asset URL...')
        pdialog.startProgress('{0} scraper (Resolving asset...)'.format(scraper_name), 100)
        image_url = self.scraper_obj.resolve_asset_URL(selected_asset)
        log_debug('Resolved {0} to URL "{1}"'.format(asset_name, image_url))
        pdialog.endProgress()
        if not image_url:
            log_error('_gui_edit_asset() Error in scraper.resolve_asset_URL()')
            op_dic['status'] = False
            op_dic['msg'] = 'Error downloading asset'
            return op_dic
        image_ext = self.scraper_obj.resolve_asset_URL_extension(image_url)
        log_debug('Resolved URL extension "{0}"'.format(image_ext))
        if not image_ext:
            log_error('_gui_edit_asset() Error in scraper.resolve_asset_URL_extension()')
            op_dic['status'] = False
            op_dic['msg'] = 'Error downloading asset'
            return op_dic

        # --- Download image ---
        log_debug('Downloading image ...')
        image_local_path = asset_path_noext_FN.append(image_ext).getPath()
        log_verb('Downloading URL "{0}"'.format(image_url))
        log_verb('Into local file "{0}"'.format(image_local_path))
        pdialog.startProgress('Downloading {0}...'.format(asset_name), 100)
        try:
            net_download_img(image_url, image_local_path)
        except socket.timeout:
            pdialog.endProgress()
            kodi_notify_warn('Cannot download {0} image (Timeout)'.format(image_name))
            op_dic['status'] = False
            op_dic['msg'] = 'Network timeout'
            return op_dic
        else:
            pdialog.endProgress()

        # --- Update Kodi cache with downloaded image ---
        # Recache only if local image is in the Kodi cache, this function takes care of that.
        # kodi_update_image_cache(image_local_path)

        # --- Edit using Python pass by assigment ---
        # If we reach this point is because an image was downloaded.
        # Caller is responsible to save Categories/Launchers/ROMs databases.
        object_dic[asset_info.key] = image_local_path
        op_dic['msg'] = 'Downloaded {0} with {1} scraper'.format(asset_name, scraper_name)

        return op_dic

    #
    # When scraping metadata or assets in the context menu, introduce the search strin,
    # grab candidate games, and select a candidate for scraping.
    #
    # @param object_name: [str] SCRAPE_ROM, SCRAPE_LAUNCHER.
    # @return: [dict] Dictionary with candidate data. None if error.
    def _scrap_CM_get_candidate(self, object_name, object_dic, data_dic, op_dic):
        log_debug('ScrapeStrategy::_scrap_CM_get_candidate() BEGIN...')

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
            op_dic['status'] = False
            op_dic['msg'] = '{0} metadata unchanged'.format(object_name)
            return
        search_term = keyboard.getText().decode('utf-8')

        # --- Do a search and get a list of games ---
        pdialog = KodiProgressDialog()
        pdialog.startProgress('{0} scraper (Getting games...)'.format(scraper_name))
        candidate_list = self.scraper_obj.get_candidates(search_term, rom_base_noext, platform)
        log_verb('Scraper found {0} result/s'.format(len(candidate_list)))
        if not candidate_list:
            op_dic['status'] = False
            op_dic['dialog'] = KODI_MESSAGE_NOTIFY_WARN
            op_dic['msg'] = 'Scraper found no matching games'
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
                op_dic['status'] = False
                op_dic['msg'] = '{0} metadata unchanged'.format(object_name)
                return
        # log_debug('select_candidate_idx {0}'.format(select_candidate_idx))
        candidate = candidate_list[select_candidate_idx]
        log_verb('User chose game "{0}"'.format(candidate['display_name']))

        return candidate

#
# Base class for all scrapers (offline or online, metadata or asset).
# The scrapers are Launcher and ROM agnostic. All the required Launcher/ROM properties are
# stored in the strategy object.
# The Scraper base class is responsible for caching all data to reduce network traffic.
#
class Scraper(object):
    __metaclass__ = abc.ABCMeta

    # @param settings: [dict] Addon settings.
    def __init__(self, settings):
        self.settings = settings
        self.verbose_flag = False
        self.dump_file_flag = False
        self._reset_caches()

        # --- Initialize common scraper settings ---
        # None at the moment. Note that settings that affect the scraping policy belong
        # in the ScrapeStrategy class and not here.

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

    # Search for candidates and return a list of dictionaries _new_candidate_dic()
    # Caches all searches. If search is not cached then call abstract method and update the cache.
    #
    # @param search_term: [str] String to be searched.
    # @param rombase_noext" [str] rombase_noext is used by some scrapers instead of search_term,
    #        notably the offline scrapers. Some scrapers require the literal name of the ROM.
    # @param platform: [str] AEL platform.
    # @return: [list] List of _new_candidate_dic() dictionaries.
    def get_candidates(self, search_term, rombase_noext, platform):
        # Check if search term is in the cache.
        cache_str = search_term + '__' + rombase_noext + '__' + platform
        if cache_str in self.cache_candidates:
            log_debug('Scraper::get_candidates() Cache hit "{0}"'.format(cache_str))
            candidate_list = self.cache_candidates[cache_str]
        else:
            log_debug('Scraper::get_candidates() Cache miss "{0}"'.format(cache_str))
            candidate_list = self._scraper_get_candidates(search_term, rombase_noext, platform)
            self.cache_candidates[cache_str] = candidate_list

        return candidate_list

    # Returns the metadata for a candidate (search result).
    # Caches all searches. If search is not cached then call abstract method and update the cache.
    #
    # @param candidate: [dict] Candidate returned by get_candidates()
    # @return: [dict] Dictionary _new_gamedata_dic(). None or empty dictionary if error
    #                 getting the metadata.
    def get_metadata(self, candidate):
        cache_key = str(candidate['id'])
        if cache_key in self.cache_metadata:
            log_debug('Scraper::get_metadata() Cache hit "{0}"'.format(cache_key))
            gamedata = self.cache_metadata[cache_key]
        else:
            log_debug('Scraper::get_metadata() Cache miss "{0}"'.format(cache_key))
            gamedata = self._scraper_get_metadata(candidate)
            self.cache_metadata[cache_key] = gamedata

        return gamedata

    # Returns a list of assets for a candidate (search result).
    # Transparently cache returned results for that candidate and asset type.
    # Note that the scraper object may do additional internal caching in _scraper_get_assets().
    #
    # @param candidate: [dict] Candidate returned by get_candidates()
    # @return: [list] List of _new_assetdata_dic() dictionaries. None if error getting the metadata.
    def get_assets(self, candidate, asset_ID):
        asset_info = assets_get_info_scheme(asset_ID)
        log_debug('Scraper::get_assets() candidate ID = {0}, asset {1} (ID {2})'.format(
            candidate['id'], asset_info.name, asset_ID))
        cache_key = str(candidate['id']) + '__' + str(asset_ID)
        if cache_key in self.cache_assets:
            log_debug('Scraper::get_assets() Cache hit "{0}"'.format(cache_key))
            assetdata_list = self.cache_assets[cache_key]
        else:
            log_debug('Scraper::get_assets() Cache miss "{0}"'.format(cache_key))
            assetdata_list = self._scraper_get_assets(candidate, asset_ID)
            self.cache_assets[cache_key] = assetdata_list

        return assetdata_list

    # When returning the asset list with get_assets(), some sites return thumbnails images
    # because the real assets are on a single dedicate page. For this sites, resolve_asset_URL()
    # returns the true, full size URL of the asset.
    # Other scrapers, for example MobyGames, return both the thumbnail and the true asset URLs
    # in get_assets(). In such case, the implementation of this method is trivial.
    #
    # This method caches all requests, just in case.
    def resolve_asset_URL(self, candidate):
        return self._scraper_resolve_asset_URL(candidate)

    def resolve_asset_URL_extension(self, image_url):
        return self._scraper_resolve_asset_URL_extension(image_url)

    # Called by get_candidates().
    # Search for candidates and return a list of dictionaries _new_candidate_dic()
    @abc.abstractmethod
    def _scraper_get_candidates(self, search_term, rombase_noext, platform): pass

    # @param candidate: [dict] Candidate returned by get_candidates()
    # @return: [dict] Dictionary _new_gamedata_dic(). None if error getting the metadata.
    @abc.abstractmethod
    def _scraper_get_metadata(self, candidate): pass

    # @param candidate: [dict] Candidate returned by get_candidates()
    # @return: [dict] Dictionary _new_assetdata_dic(). None if error getting the metadata.
    @abc.abstractmethod
    def _scraper_get_assets(self, candidate, asset_ID): pass

    # Abstrac method called by resolve_asset_URL()
    @abc.abstractmethod
    def _scraper_resolve_asset_URL(self, candidate): pass

    def _reset_caches(self):
        self.cache_candidates = {}
        self.cache_metadata = {}
        self.cache_assets = {}

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
    #
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

    # Null scraper never finds candidates.
    def _scraper_get_candidates(self, search_term, rombase_noext, platform): return []

    # Null scraper never returns valid scraped metadata.
    def _scraper_get_metadata(self, candidate): return {}

    def _scraper_get_assets(self, candidate, asset_ID): return {}

    def _scraper_resolve_asset_URL(self, candidate): pass

    def _scraper_resolve_asset_URL_extension(self, image_url): return text_get_URL_extension(image_url)

# ------------------------------------------------------------------------------------------------
# AEL offline metadata scraper.
# ------------------------------------------------------------------------------------------------
class AEL_Offline(Scraper):
    # @param settings: [dict] Addon settings. Particular scraper settings taken from here.
    def __init__(self, settings):
        # Pass down settings that apply to all scrapers.
        super(AEL_Offline, self).__init__(settings)

    def get_name(self): return 'AEL Offline'

    def supports_metadata_ID(self, metadata_ID): return True

    def supports_metadata(self): return True

    def supports_asset_ID(self, asset_ID): return False

    def supports_assets(self): return False

    def _scraper_get_candidates(self, search_term, rombase_noext, platform): return []

    def _scraper_get_metadata(self, candidate): return {}

    def _scraper_get_assets(self, candidate, asset_ID): return {}

    def _scraper_resolve_asset_URL(self, candidate): pass

    def _scraper_resolve_asset_URL_extension(self, image_url): return text_get_URL_extension(image_url)

# ------------------------------------------------------------------------------------------------
# LaunchBox offline metadata scraper.
# Do not implement this scraper. It is better to have one good offline scraper than many bad.
# Users will be encouraged to improve the AEL Offline scraper.
# ------------------------------------------------------------------------------------------------
class LB_Offline(Scraper): pass

# ------------------------------------------------------------------------------------------------
# TheGamesDB online scraper (metadata and assets)
#
# | Site     | https://thegamesdb.net      |
# | API info | https://api.thegamesdb.net/ |
# ------------------------------------------------------------------------------------------------
class TheGamesDB(Scraper):
    # --- Class variables ---
    supported_metadata_list = [
        META_TITLE_ID, META_YEAR_ID, META_GENRE_ID, META_DEVELOPER_ID,
        META_NPLAYERS_ID, META_ESRB_ID, META_PLOT_ID
    ]
    supported_asset_list = [
        ASSET_SNAP_ID, ASSET_BOXFRONT_ID, ASSET_BOXBACK_ID,
        ASSET_FANART_ID, ASSET_CLEARLOGO_ID, ASSET_BANNER_ID,
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

    def __init__(self, settings):
        # --- This scraper settings ---
        self.api_key = settings['scraper_thegamesdb_apikey']
        self.api_public_key = '828be1fb8f3182d055f1aed1f7d4da8bd4ebc160c3260eae8ee57ea823b42415'

        # --- Cached TGDB metadata ---
        self.genres_cached = {}
        self.developers_cached = {}
        self.publishers_cached = {}
        self.all_asset_cache = {}

        # --- Pass down common scraper settings ---
        super(TheGamesDB, self).__init__(settings)

    # --- Base class abstract methods ------------------------------------------------------------
    def get_name(self): return 'TheGamesDB'

    def supports_metadata_ID(self, metadata_ID):
        return True if asset_ID in TheGamesDB.supported_metadata_list else False

    def supports_metadata(self): return True

    def supports_asset_ID(self, asset_ID):
        return True if asset_ID in TheGamesDB.supported_asset_list else False

    def supports_assets(self): return True

    def _scraper_get_candidates(self, search_term, rombase_noext, platform):
        scraper_platform = AEL_platform_to_TheGamesDB(platform)
        log_debug('TheGamesDB::_scraper_get_candidates() search_term         "{0}"'.format(search_term))
        log_debug('TheGamesDB::_scraper_get_candidates() rom_base_noext      "{0}"'.format(rombase_noext))
        log_debug('TheGamesDB::_scraper_get_candidates() AEL platform        "{0}"'.format(platform))
        log_debug('TheGamesDB::_scraper_get_candidates() TheGamesDB platform "{0}"'.format(scraper_platform))

        # quote_plus() will convert the spaces into '+'. Note that quote_plus() requires an
        # UTF-8 encoded string and does not work with Unicode strings.
        # https://stackoverflow.com/questions/22415345/using-pythons-urllib-quote-plus-on-utf-8-strings-with-safe-arguments
        search_string_encoded = urllib.quote_plus(search_term.encode('utf8'))
        api_key = self._get_API_key()
        url_str = 'https://api.thegamesdb.net/Games/ByGameName?apikey={0}&name={1}&filter[platform]={2}'
        url = url_str.format(api_key, search_string_encoded, scraper_platform)
        game_list = self._read_games_from_url(url, search_term, scraper_platform)

        # if len(game_list) == 0:
        #     altered_search_term = self._cleanup_searchterm(search_term, rombase_noext, platform)
        #     log_debug('Cleaning search term. Before "{0}"'.format(search_term))
        #     log_debug('After "{0}"'.format(altered_search_term))
        #     if altered_search_term != search_term:
        #         log_debug('No matches, trying again with altered search terms: {0}'.format(
        #             altered_search_term))
        #         return self._get_candidates(altered_search_term, rombase_noext, platform)

        # --- Order list based on score. High score goes first ---
        game_list.sort(key = lambda result: result['order'], reverse = True)

        return game_list

    def _scraper_get_metadata(self, candidate):
        api_key = self._get_API_key()
        url = 'https://api.thegamesdb.net/Games/ByGameID?apikey={}&id={}&fields=players%2Cpublishers%2Cgenres%2Coverview%2Crating%2Cplatform%2Ccoop%2Cyoutube'.format(
            api_key, candidate['id'])
        # log_debug('Get metadata from {0}'.format(url))
        page_data_raw = net_get_URL_original(url)
        page_data = json.loads(page_data_raw)
        if self.dump_file_flag:
            file_path = os.path.join(self.dump_dir, 'TGDB_get_metadata.txt')
            text_dump_str_to_file(file_path, json.dumps(
                page_data, indent = 1, separators = (', ', ' : ')))

        # --- Parse game page data ---
        log_debug('TheGamesDB::_scraper_get_metadata() Parsing game metadata...')
        online_data = page_data['data']['games'][0]
        game_data = self._new_gamedata_dic()
        game_data['title']     = online_data['game_title'] if 'game_title' in online_data else ''
        game_data['year']      = self._parse_metadata_year(online_data)
        game_data['genre']     = self._parse_metadata_genres(online_data)
        game_data['developer'] = self._parse_metadata_developer(online_data)
        game_data['nplayers']  = str(online_data['players']) if 'players' in online_data else ''
        game_data['esrb']      = online_data['rating'] if 'rating' in online_data else ''
        game_data['plot']      = online_data['overview'] if 'overview' in online_data else ''

        return game_data

    def _scraper_get_assets(self, candidate, asset_ID):
        # log_debug('TheGamesDB::_scraper_get_assets() asset_ID = {0} ...'.format(asset_ID))
        # Get all assets for candidate. _scraper_get_assets_all() caches all assets for a candidate.
        # Then select asset of a particular type.
        all_asset_list = self._scraper_get_assets_all(candidate)
        asset_list = [asset_dic for asset_dic in all_asset_list if asset_dic['asset_ID'] == asset_ID]
        log_debug('TheGamesDB::_scraper_get_assets() Total assets {0} / Returned assets {1}'.format(
            len(all_asset_list), len(asset_list)))
        return asset_list

    def _scraper_resolve_asset_URL(self, candidate):
        return candidate['url']

    def _scraper_resolve_asset_URL_extension(self, image_url):
        return text_get_URL_extension(image_url)

    # --- This class methods own -----------------------------------------------------------------
    def get_platforms(self):
        log_debug('TheGamesDB::get_platforms() BEGIN...')
        api_key = self._get_API_key()
        url = 'https://api.thegamesdb.net/Platforms?apikey={}'.format(api_key)
        page_data = json.loads(net_get_URL_original(url))
        self._dump_json_debug('TGDB_get_platforms.txt', page_data)

        return page_data

    def _get_API_key(self):
        if self.api_key:
            return self.api_key
        else:
            return self.api_public_key

    # --- Parse list of games ---
    #{
    #  "code": 200,
    #  "status": "Success",
    #  "data": {
    #    "count": 20,
    #    "games": [
    #      {
    #        "id": 40154,
    #        "game_title": "Castlevania Double Pack: Aria of Sorrow/Harmony of Dissonance",
    #        "release_date": "2006-01-11",
    #        "platform": 5,
    #        "rating": "T - Teen",
    #        "overview": "CASTLEVANIA DOUBLE PACK collects two great .....",
    #        "coop": "No",
    #        "youtube": null,
    #        "developers": [
    #          4765
    #        ],
    #        "genres": [
    #          1,
    #          2
    #        ],
    #        "publishers": [
    #          23
    #        ]
    #},
    def _read_games_from_url(self, url, search_term, scraper_platform):
        # --- Get URL data as JSON ---
        page_data_raw = net_get_URL_original(url)
        page_data = json.loads(page_data_raw)
        self._dump_json_debug('TGDB_get_candidates.txt', page_data)

        # --- Parse game list ---
        games = page_data['data']['games']
        game_list = []
        for item in games:
            title = item['game_title']
            platform = item['platform']
            display_name = title
            game = self._new_candidate_dic()
            game['id'] = item['id']
            game['display_name'] = display_name
            game['platform'] = platform
            game['scraper_platform'] = scraper_platform
            game['order'] = 1
            # Increase search score based on our own search.
            if title.lower() == search_term.lower():                  game['order'] += 2
            if title.lower().find(search_term.lower()) != -1:         game['order'] += 1
            if scraper_platform > 0 and platform == scraper_platform: game['order'] += 1
            game_list.append(game)

        # --- Recursively load more games ---
        next_url = page_data['pages']['next']
        if next_url is not None:
            log_debug('TheGamesDB::_read_games_from_url() Recursively loading games page')
            game_list = game_list + self._read_games_from_url(next_url, search_term, scraper_platform)

        # --- Sort game list based on the score ---
        game_list.sort(key = lambda result: result['order'], reverse = True)

        return game_list

    def _cleanup_searchterm(self, search_term, rom_path, rom):
        altered_term = search_term.lower().strip()
        for ext in self.launcher.get_rom_extensions():
            altered_term = altered_term.replace(ext, '')
        return altered_term

    def _parse_metadata_year(self, online_data):
        if 'release_date' in online_data and \
           online_data['release_date'] is not None and \
           online_data['release_date'] != '':
           year_str = online_data['release_date'][:4]
        else:
            year_str = ''
        return year_str

    def _parse_metadata_genres(self, online_data):
        if 'genres' not in online_data: return ''
        # "genres" : [ 1 , 15 ],
        genre_ids = online_data['genres']
        TGDB_genres = self._get_genres()
        genre_list = [TGDB_genres[genre_id] for genre_id in genre_ids]
        return ', '.join(genre_list)

    # Get a dictionary of TGDB genres (integers) to AEL genres (strings).
    # TGDB genres are cached in an object variable.
    def _get_genres(self):
        # If genres are cached return immediately.
        if self.genres_cached: return self.genres_cached
        log_debug('TheGamesDB::_get_genres() No cached genres. Retrieving...')
        api_key = self._get_API_key()
        url = 'https://api.thegamesdb.net/Genres?apikey={}'.format(api_key)
        page_data_raw = net_get_URL_original(url)
        page_data = json.loads(page_data_raw)
        self._dump_json_debug('TGDB_get_genres.txt', page_data)
        self.genres_cached = {}
        for genre_id in page_data['data']['genres']:
            self.genres_cached[int(genre_id)] = page_data['data']['genres'][genre_id]['name']
        return self.genres_cached

    def _parse_metadata_developer(self, online_data):
        if 'developers' not in online_data: return ''
        # "developers" : [ 7979 ],
        developers_ids = online_data['developers']
        TGDB_developers = self._get_developers()
        developer_list = [TGDB_developers[dev_id] for dev_id in developers_ids]

        return ', '.join(developer_list)

    def _get_developers(self):
        # If developers are cached return immediately.
        if self.developers_cached: return self.developers_cached
        log_debug('TheGamesDB::_get_developers() No cached developers. Retrieving...')
        api_key = self._get_API_key()
        url = 'https://api.thegamesdb.net/Developers?apikey={}'.format(api_key)
        page_data_raw = net_get_URL_original(url)
        page_data = json.loads(page_data_raw)
        self._dump_json_debug('TGDB_get_developers.txt', page_data)
        self.developers_cached = {}
        for developer_id in page_data['data']['developers']:
            self.developers_cached[int(developer_id)] = page_data['data']['developers'][developer_id]['name']

        return self.developers_cached

    # Publishers is not used in AEL at the moment.
    def _get_publishers(self, publisher_ids):
        if publisher_ids is None: return ''
        if self.publishers is None:
            log_debug('TheGamesDB:: No cached publishers. Retrieving from online.')
            api_key = self._get_API_key()
            url = 'https://api.thegamesdb.net/Publishers?apikey={}'.format(api_key)
            publishers_json = net_get_URL_as_json(url)
            self.publishers = {}
            for publisher_id in publishers_json['data']['publishers']:
                self.publishers[int(publisher_id)] = publishers_json['data']['publishers'][publisher_id]['name']
        publisher_names = [self.publishers[publisher_id] for publisher_id in publisher_ids]

        return ' / '.join(publisher_names)

    # Get ALL available assets for game.
    # Cache the results because this function may be called multiple times.
    def _scraper_get_assets_all(self, candidate):
        # log_debug('TheGamesDB::_scraper_get_assets_all() BEGIN ...')
        cache_key = str(candidate['id'])
        if cache_key in self.all_asset_cache:
            log_debug('TheGamesDB::_scraper_get_assets_all() Cache hit "{0}"'.format(cache_key))
            asset_list = self.all_asset_cache[cache_key]
            return asset_list

        # --- Cache miss ---
        log_debug('TheGamesDB::_scraper_get_assets_all() Cache miss "{0}"'.format(cache_key))
        api_key = self._get_API_key()
        url = 'https://api.thegamesdb.net/Games/Images?apikey={}&games_id={}'.format(
            api_key, candidate['id'])
        asset_list = self._read_assets_from_url(url, candidate['id'])
        log_debug('A total of {0} assets found for candidate ID {1}'.format(
            len(asset_list), candidate['id']))
        self.all_asset_cache[cache_key] = asset_list

        return asset_list

    def _read_assets_from_url(self, url, candidate_id):
        # --- Read URL JSON data ---
        page_data_raw = net_get_URL_original(url)
        page_data = json.loads(page_data_raw)
        self._dump_json_debug('TGDB_get_assets.txt', page_data)

        # --- Parse images page data ---
        base_url_thumb = page_data['data']['base_url']['thumb']
        base_url = page_data['data']['base_url']['original']
        assets_list = []
        for image_data in page_data['data']['images'][str(candidate_id)]:
            asset_name = '{0} ID {1}'.format(image_data['type'], image_data['id'])
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
            log_debug('TheGamesDB::_read_assets_from_url() Recursively loading games page')
            assets_list = assets_list + self._read_assets_from_url(next_url, candidate_id)

        return assets_list

# ------------------------------------------------------------------------------------------------
# MobyGames online scraper http://www.mobygames.com
#
# TODO
# 1) Detect 401 Unauthorized and warn user.
#
# 2) Detect 429 Too Many Requests and disable scraper. We never do more than one call per second
#    so if we get 429 is because the 360 API requests per hour are consumed.
#
# MobiGames API info https://www.mobygames.com/info/api
# ------------------------------------------------------------------------------------------------
class MobyGames(Scraper):
    # Class variables
    supported_metadata_list = [
        META_TITLE_ID, META_YEAR_ID, META_GENRE_ID, META_PLOT_ID,
    ]
    supported_asset_list = [
        ASSET_TITLE_ID, ASSET_SNAP_ID,
        ASSET_BOXFRONT_ID, ASSET_BOXBACK_ID, ASSET_CARTRIDGE_ID, ASSET_MANUAL_ID,
    ]
    asset_name_mapping = {
        'media'         : ASSET_CARTRIDGE_ID,
        'manual'        : ASSET_MANUAL_ID,
        'front cover'   : ASSET_BOXFRONT_ID,
        'back cover'    : ASSET_BOXBACK_ID,
        'spine/sides'   : None, # not supported by AEL?
        'other'         : None,
        'advertisement' : None,
        'extras'        : None,
        'inside cover'  : None,
        'full cover'    : None,
        'soundtrack'    : None,
    }

    def __init__(self, settings):
        # --- This scraper settings ---
        self.api_key = settings['scraper_mobygames_apikey']
        # --- Misc stuff ---
        self.all_asset_cache = {}
        self.last_http_call = datetime.datetime.now()
        # --- Pass down common scraper settings ---
        super(MobyGames, self).__init__(settings)

    # --- Base class abstract methods ------------------------------------------------------------
    def get_name(self): return 'MobyGames'

    def supports_metadata_ID(self, metadata_ID):
        return True if asset_ID in MobyGames.supported_metadata_list else False

    def supports_metadata(self): return True

    def supports_asset_ID(self, asset_ID):
        return True if asset_ID in MobyGames.supported_asset_list else False

    def supports_assets(self): return True

    # Cache is done in the base class. If this function is called it was a cache miss.
    # The cache will be updated with whatever this functions returns.
    def _scraper_get_candidates(self, search_term, rombase_noext, platform):
        scraper_platform = AEL_platform_to_MobyGames(platform)
        log_debug('MobyGames::_scraper_get_candidates() search_term        "{0}"'.format(search_term))
        log_debug('MobyGames::_scraper_get_candidates() rom_base_noext     "{0}"'.format(rombase_noext))
        log_debug('MobyGames::_scraper_get_candidates() AEL platform       "{0}"'.format(platform))
        log_debug('MobyGames::_scraper_get_candidates() MobyGames platform "{0}"'.format(scraper_platform))

        search_string_encoded = urllib.quote_plus(search_term.encode('utf8'))
        url_str = 'https://api.mobygames.com/v1/games?api_key={0}&format=brief&title={1}&platform={2}'
        url = url_str.format(self.api_key, search_string_encoded, scraper_platform)
        game_list = self._read_games_from_url(url, search_term, platform, scraper_platform)
        # Order list based on score. High score first.
        game_list.sort(key = lambda result: result['order'], reverse = True)

        return game_list

    def _scraper_get_metadata(self, candidate):
        self._do_toomanyrequests_check()
        url = 'https://api.mobygames.com/v1/games/{}?api_key={}'.format(candidate['id'], self.api_key)
        log_debug('Get metadata from {0}'.format(url))
        page_data_raw = net_get_URL_original(url)
        self.last_http_call = datetime.datetime.now()
        online_data = json.loads(page_data_raw)
        if self.dump_file_flag:
            file_path = os.path.join(self.dump_dir, 'mobygames_get_metadata.txt')
            text_dump_str_to_file(file_path, page_data_raw)

        # --- Parse game page data ---
        gamedata = self._new_gamedata_dic()
        gamedata['title'] = online_data['title'] if 'title' in online_data else ''
        gamedata['plot']  = online_data['description'] if 'description' in online_data else ''
        gamedata['genre'] = self._get_genres(online_data['genres']) if 'genres' in online_data else ''
        gamedata['year']  = self._get_year_by_platform(online_data['platforms'], candidate['scraper_platform'])

        return gamedata

    # Get assets of a particular type. Note that this function maybe called many times for
    # the same candidate but different asset type, so cache data if necessary.
    #
    # In the MobyGames scraper is convenient to grab all the available assets for a candidate,
    # cache the assets, and then select the assets of a specific type from the cached list.
    #
    def _scraper_get_assets(self, candidate, asset_ID):
        # log_debug('MobyGames::_scraper_get_assets() asset_ID = {0} ...'.format(asset_ID))
        # Get all assets for candidate. _scraper_get_assets_all() caches all assets for a candidate.
        # Then select asset of a particular type.
        all_asset_list = self._scraper_get_assets_all(candidate)
        asset_list = [asset_dic for asset_dic in all_asset_list if asset_dic['asset_ID'] == asset_ID]
        log_debug('MobyGames::_scraper_get_assets() Total assets {0} / Returned assets {1}'.format(
            len(all_asset_list), len(asset_list)))

        return asset_list

    # Mobygames returns both the asset thumbnail URL and the full resolution URL so in
    # this scraper this method is trivial.
    def _scraper_resolve_asset_URL(self, candidate):
        # Transform http to https
        url = candidate['url']
        if url[0:4] == 'http': url = 'https' + url[4:]

        return url

    def _scraper_resolve_asset_URL_extension(self, image_url):
        return text_get_URL_extension(image_url)

    # --- This class methods ---------------------------------------------------------------------
    def _read_games_from_url(self, url, search_term, platform, scraper_platform):
        self._do_toomanyrequests_check()
        page_data_raw = net_get_URL_original(url)
        self.last_http_call = datetime.datetime.now()
        page_data = json.loads(page_data_raw)
        if self.dump_file_flag:
            file_path = os.path.join(self.dump_dir, 'mobygames_get_candidates.txt')
            text_dump_str_to_file(file_path, page_data_raw)

        # If nothing is returned maybe a timeout happened. In this case, reset the cache.
        if page_data is None: self._reset_cache()

        # --- Parse game list ---
        games = page_data['games']
        game_list = []
        for item in games:
            title = item['title']
            game = self._new_candidate_dic()
            game['id'] = item['game_id']
            game['display_name'] = title
            game['platform'] = platform
            game['scraper_platform'] = scraper_platform
            game['order'] = 1

            # Increase search score based on our own search.
            if title.lower() == search_term.lower():          game['order'] += 2
            if title.lower().find(search_term.lower()) != -1: game['order'] += 1
            game_list.append(game)

        return game_list

    def _get_genres(self, genre_data):
        genre_names = []
        for genre in genre_data:
            genre_names.append(genre['genre_name'])

        return ' / '.join(genre_names)

    def _get_year_by_platform(self, platform_data, platform_id):
        if len(platform_data) == 0: return ''
        year_data = None
        for platform in platform_data:
            if platform['platform_id'] == int(platform_id):
                year_data = platform['first_release_date']
                break
        if year_data is None:
            year_data = platform_data[0]['first_release_date']

        return year_data[:4]

    # Get ALL available assets for game.
    # Cache the results because this function may be called multiple times.
    def _scraper_get_assets_all(self, candidate):
        # log_debug('MobyGames::_scraper_get_assets_all() BEGIN ...')
        cache_key = str(candidate['id'])
        if cache_key in self.all_asset_cache:
            log_debug('MobyGames::_scraper_get_assets_all() Cache hit "{0}"'.format(cache_key))
            asset_list = self.all_asset_cache[cache_key]
            return asset_list

        # --- Cache miss ---
        log_debug('MobyGames::_scraper_get_assets_all() Cache miss "{0}"'.format(cache_key))
        snap_assets = self._load_snap_assets(candidate, candidate['scraper_platform'])
        cover_assets = self._load_cover_assets(candidate, candidate['scraper_platform'])
        asset_list = snap_assets + cover_assets
        log_debug('A total of {0} assets found for candidate ID {1}'.format(
            len(asset_list), candidate['id']))
        self.all_asset_cache[cache_key] = asset_list

        return asset_list

    def _load_snap_assets(self, candidate, platform_id):
        log_debug('MobyGames::_load_snap_assets() Getting Snaps...')
        url = 'https://api.mobygames.com/v1/games/{0}/platforms/{1}/screenshots?api_key={2}'.format(
            candidate['id'], platform_id, self.api_key)
        self._do_toomanyrequests_check()
        page_data_raw = net_get_URL_original(url)
        page_data = json.loads(page_data_raw)
        self.last_http_call = datetime.datetime.now()
        self._dump_json_debug('mobygames_snap_assets.txt', page_data)

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

    def _load_cover_assets(self, candidate, platform_id):
        log_debug('MobyGames::_load_cover_assets() Getting Covers...')
        url = 'https://api.mobygames.com/v1/games/{0}/platforms/{1}/covers?api_key={2}'.format(
            candidate['id'], platform_id, self.api_key)
        self._do_toomanyrequests_check()
        page_data_raw = net_get_URL_original(url)
        page_data = json.loads(page_data_raw)
        self.last_http_call = datetime.datetime.now()
        self._dump_json_debug('mobygames_cover_assets.txt', page_data)

        # --- Parse images page data ---
        asset_list = []
        for group_data in page_data['cover_groups']:
            country_names = ' / '.join(group_data['countries'])
            for image_data in group_data['covers']:
                asset_name = '{0} - {1} ({2})'.format(
                    image_data['scan_of'], image_data['description'], country_names)
                asset_ID = MobyGames.asset_name_mapping[image_data['scan_of'].lower()]

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

    def _do_toomanyrequests_check(self):
        # Make sure we dont go over the TooManyRequests limit of 1 second.
        now = datetime.datetime.now()
        if (now - self.last_http_call).total_seconds() < 1:
            log_debug('MobyGames_Scraper:: Sleeping 1 second to avoid overloading...')
            time.sleep(1)

# ------------------------------------------------------------------------------------------------
# ScreenScraper online scraper.
#
# | Site     | https://www.screenscraper.fr             |
# | API info | https://www.screenscraper.fr/webapi.php  |
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
        self.ssid       = settings['scraper_screenscraper_ssid']
        self.sspassword = settings['scraper_screenscraper_sspass']
        self.softname   = settings['scraper_screenscraper_AEL_softname']

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

    def _scraper_get_candidates(self, search_term, rombase_noext, platform):
        scraper_platform = AEL_platform_to_ScreenScraper(platform)
        log_debug('ScreenScraper_V1::_scraper_get_candidates() search_term   "{0}"'.format(search_term))
        log_debug('ScreenScraper_V1::_scraper_get_candidates() rombase_noext "{0}"'.format(rombase_noext))
        log_debug('ScreenScraper_V1::_scraper_get_candidates() AEL platform  "{0}"'.format(platform))
        log_debug('ScreenScraper_V1::_scraper_get_candidates() SS platform   "{0}"'.format(scraper_platform))

        # --- Get scraping data and cache it ---
        # ScreenScraper jeuInfos.php returns absolutely everything about a single ROM, including
        # metadata, artwork, etc. jeuInfos.php returns one game or nothing at all.
        # The data returned by jeuInfos.php must be cached in this object for every request done.
        # ScreenScraper returns only one game or nothing at all.
        cache_str = search_term + '__' + rombase_noext + '__' + scraper_platform
        if cache_str in self.cache_jeuInfos:
            log_debug('ScreenScraper_V1::_scraper_get_candidates() Cache hit "{0}"'.format(cache_str))
            gameInfos_dic = self.cache_jeuInfos[cache_str]
        else:
            log_debug('ScreenScraper_V1::_scraper_get_candidates() Cache miss "{0}"'.format(cache_str))
            gameInfos_dic = self._get_gameInfos(search_term, rombase_noext, scraper_platform)
            self.cache_jeuInfos[cache_str] = gameInfos_dic
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

    def _scraper_get_metadata(self, candidate):
        # --- Retrieve gameInfos_dic from cache ---
        log_debug('ScreenScraper_V1::_scraper_get_metadata() Cache retrieving "{}"'.format(candidate['cache_str']))
        gameInfos_dic = self.cache_jeuInfos[candidate['cache_str']]
        jeu_dic = gameInfos_dic['response']['jeu']

        # --- Parse game metadata ---
        gamedata = self._new_gamedata_dic()
        gamedata['title']     = self._get_meta_title(jeu_dic)
        gamedata['year']      = self._get_meta_year(jeu_dic)
        gamedata['genre']     = self._get_meta_genre(jeu_dic)
        gamedata['developer'] = self._get_meta_developer(jeu_dic)
        gamedata['nplayers']  = self._get_meta_nplayers(jeu_dic)
        gamedata['esrb']      = self._get_meta_esrb(jeu_dic)
        gamedata['plot']      = self._get_meta_plot(jeu_dic)

        return gamedata

    def _scraper_get_assets(self, candidate, asset_ID):
        # --- Retrieve gameInfos_dic from cache ---
        log_debug('ScreenScraper_V1::_scraper_get_assets() Cache retrieving "{}"'.format(candidate['cache_str']))
        gameInfos_dic = self.cache_jeuInfos[candidate['cache_str']]
        jeu_dic = gameInfos_dic['response']['jeu']

        # --- Parse game assets ---
        all_asset_list = self._get_assets_all(jeu_dic)
        asset_list = [asset_dic for asset_dic in all_asset_list if asset_dic['asset_ID'] == asset_ID]
        log_debug('ScreenScraper_V1::_scraper_get_assets() Total assets {0} / Returned assets {1}'.format(
            len(all_asset_list), len(asset_list)))

        return asset_list

    def _scraper_resolve_asset_URL(self, candidate): return candidate['url']

    def _scraper_resolve_asset_URL_extension(self, image_url):
        o = urlparse.urlparse(image_url)
        url_args = urlparse.parse_qs(o.query)
        # log_debug(unicode(o))
        # log_debug(unicode(url_args))
        image_ext = url_args['mediaformat'][0] if 'mediaformat' in url_args else ''

        return '.' + image_ext

    # --- This class own methods -----------------------------------------------------------------
    # Plumbing function to the the raw game dictionary returned by ScreenScraper.
    # Scraper::get_candiates() must be called before this function.
    def get_gameInfos_dic(self, candidate):
        log_debug('ScreenScraper_V1::get_gameInfos_dic() Cache retrieving "{}"'.format(candidate['cache_str']))
        gameInfos_dic = self.cache_jeuInfos[candidate['cache_str']]

        return gameInfos_dic

    # Some functions to grab data from ScreenScraper.
    def get_ROM_types(self):
        log_debug('ScreenScraper_V1::get_ROM_types() BEGIN...')
        url_str = 'https://www.screenscraper.fr/api/romTypesListe.php?devid={}&devpassword={}&softname={}&output=json'
        url = url_str.format(base64.b64decode(self.dev_id), base64.b64decode(self.dev_pass), self.softname)
        page_raw_data = net_get_URL_original(url)
        log_debug(unicode(page_raw_data))
        page_data = json.loads(page_raw_data)
        self._dump_json_debug('ScreenScraper_get_ROM_types.txt', page_data)

        return page_data

    def get_genres_list(self):
        log_debug('ScreenScraper_V1::get_genres_list() BEGIN...')
        url_str = 'https://www.screenscraper.fr/api/genresListe.php?devid={}&devpassword={}&softname={}&output=json'
        url = url_str.format(base64.b64decode(self.dev_id), base64.b64decode(self.dev_pass), self.softname)
        page_raw_data = net_get_URL_original(url)
        # log_debug(unicode(page_raw_data))
        page_data = json.loads(page_raw_data)
        self._dump_json_debug('ScreenScraper_get_genres_list.txt', page_data)

        return page_data

    def get_regions_list(self):
        log_debug('ScreenScraper_V1::get_regions_list() BEGIN...')
        url_str = 'https://www.screenscraper.fr/api/regionsListe.php?devid={}&devpassword={}&softname={}&output=json'
        url = url_str.format(base64.b64decode(self.dev_id), base64.b64decode(self.dev_pass), self.softname)
        page_raw_data = net_get_URL_original(url)
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
        log_debug('ScreenScraper_V1::_get_gameInfos() sspassword "{0}"'.format('********'))
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
        page_raw_data = net_get_URL_original(url)
        try:
            gameInfos_dic = json.loads(page_raw_data)
        except ValueError as ex:
            gameInfos_dic = page_raw_data
            log_error('(ValueError Exception) {0}'.format(ex))
            log_error('Message "{0}"'.format(page_raw_data))
        except Exception as ex:
            gameInfos_dic = page_raw_data
            log_error('(Generic Exception) {0}'.format(ex))
            log_error('Message "{0}"'.format(page_raw_data))
        # Dump file if debug flag is True.
        self._dump_json_debug('ScreenScraper_get_gameInfo.txt', gameInfos_dic)

        return gameInfos_dic

    def _get_meta_title(self, jeu_dic):
        # First search for regional name.
        for region in ScreenScraper_V1.region_list:
            key = 'nom' + region
            if key in jeu_dic['noms']: return jeu_dic['noms'][key]

        # Default name
        return jeu_dic['nom']

    def _get_meta_year(self, jeu_dic):
        # Search regional dates. Only return year (first 4 characters)
        for region in ScreenScraper_V1.region_list:
            key = 'date' + region
            if key in jeu_dic['dates']: return jeu_dic['dates'][key][0:4]

        return ''

    def _get_meta_genre(self, jeu_dic):
        # Only the first gender in the list is supported now.
        for region in ScreenScraper_V1.region_list:
            key = 'genres' + region
            if key in jeu_dic['genres']: return jeu_dic['genres'][key][0]

        return ''

    def _get_meta_developer(self, jeu_dic):
        return jeu_dic['developpeur']

    def _get_meta_nplayers(self, jeu_dic):
        return jeu_dic['joueurs']

    def _get_meta_esrb(self, jeu_dic):
        return jeu_dic['classifications']['ESRB']

    def _get_meta_plot(self, jeu_dic):
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
    ]
    supported_asset_list = [
    ]

    # --- Constructor ----------------------------------------------------------------------------
    def __init__(self, settings):
        # --- This scraper settings ---

        # --- Internal stuff ---

        # --- Pass down common scraper settings ---
        super(GameFAQs, self).__init__(settings)

    # --- Base class abstract methods ------------------------------------------------------------
    def get_name(self): return 'GameFAQs'

    def supports_metadata_ID(self, metadata_ID):
        return True if asset_ID in ScreenScraper_V1.supported_metadata_list else False

    def supports_metadata(self): return True

    def supports_asset_ID(self, asset_ID):
        return True if asset_ID in ScreenScraper_V1.supported_asset_list else False

    def supports_assets(self): return True

    def _scraper_get_candidates(self, search_term, rombase_noext, platform):
        scraper_platform = AEL_platform_to_GameFAQs(platform)
        log_debug('GameFAQs::_scraper_get_candidates() search_term      "{0}"'.format(search_term))
        log_debug('GameFAQs::_scraper_get_candidates() rombase_noext    "{0}"'.format(rombase_noext))
        log_debug('GameFAQs::_scraper_get_candidates() platform         "{0}"'.format(platform))
        log_debug('GameFAQs::_scraper_get_candidates() scraper_platform "{0}"'.format(scraper_platform))

        # Order list based on score
        game_list = self._get_candidates_from_page(search_term, platform, scraper_platform)
        game_list.sort(key = lambda result: result['order'], reverse = True)

        return game_list

    # Example URLs:
    # https://gamefaqs.gamespot.com/snes/519824-super-mario-world
    def _scraper_get_metadata(self, candidate):
        # --- Grab game information page ---
        log_debug('GameFAQs::_scraper_get_metadata() Get metadata from {}'.format(candidate['id']))
        url = 'https://gamefaqs.gamespot.com{}'.format(candidate['id'])
        page_data = net_get_URL(url)
        self._dump_file_debug('GameFAQs_get_metadata.html', page_data)

        # --- Parse data ---
        # <li><b>Release:</b> <a href="/snes/588699-street-fighter-alpha-2/data">November 1996 ?</a></li>
        game_release = re.findall('<li><b>Release:</b> <a href="(.*?)">(.*?) &raquo;</a></li>', page_data)

        # <ol class="crumbs">
        # <li class="crumb top-crumb"><a href="/snes">Super Nintendo</a></li>
        # <li class="crumb"><a href="/snes/category/54-action">Action</a></li>
        # <li class="crumb"><a href="/snes/category/57-action-fighting">Fighting</a></li>
        # <li class="crumb"><a href="/snes/category/86-action-fighting-2d">2D</a></li>
        # </ol>
        game_genre = re.findall('<ol class="crumbs"><li class="crumb top-crumb"><a href="(.*?)">(.*?)</a></li><li class="crumb"><a href="(.*?)">(.*?)</a></li>', page_data)

        game_developer = ''
        # <li><a href="/company/2324-capcom">Capcom</a></li>
        game_studio = re.findall('<li><a href="/company/(.*?)">(.*?)</a>', page_data)
        if game_studio:
            p = re.compile(r'<.*?>')
            game_developer = p.sub('', game_studio[0][1])

        # game_plot = re.findall('<h2 class="title">Description</h2></div><div class="body game_desc" style=".*?">(.*?)</div>', page_data)
        game_plot = re.findall('<h2 class="title">Description</h2></div><div class="body game_desc">(.*?)</div>', page_data)

        # --- Build metadata dictionary ---
        game_data = self._new_gamedata_dic()
        game_data['title']     = candidate['game_name'] 
        game_data['plot']      = text_unescape_and_untag_HTML(game_plot[0]) if game_plot else ''
        game_data['genre']     = game_genre[0][3] if game_genre else '' 
        game_data['year']      = game_release[0][1][-4:] if game_release else ''
        game_data['developer'] = game_developer

        return game_data

    def _scraper_get_assets(self, candidate, asset_ID):
        url = 'https://gamefaqs.gamespot.com{}/images'.format(candidate['id'])
        assets_list = self._load_assets_from_url(url)
        log_debug('GamesFaqScraper:: Found {} assets for candidate #{}'.format(len(assets_list), candidate['id']))    

        return assets_list

    def _scraper_resolve_asset_URL(self, candidate): return candidate['url']

    def _scraper_resolve_asset_URL_extension(self, image_url): return None

    def _get_image_url_from_page(self, candidate, asset_info):
        url = 'https://gamefaqs.gamespot.com{}'.format(candidate['url'])
        log_debug('GamesFaqScraper::_get_image_url_from_page() Get image from "{}" for asset type {}'.format(url, asset_info.name))
        page_data = net_get_URL_oneline(url)
        images_on_page = re.finditer('<img (class="full_boxshot cte" )?data-img-width="\d+" data-img-height="\d+" data-img="(?P<url>.+?)" (class="full_boxshot cte" )?src=".+?" alt="(?P<alt>.+?)"(\s/)?>', page_data)
        for image_data in images_on_page:
            image_on_page   = image_data.groupdict()
            image_asset_ids = self._parse_asset_type(image_on_page['alt'])
            log_verb('Found "{}" of types {} with url {}'.format(image_on_page['alt'], image_asset_ids, image_on_page['url']))
            if asset_info.id in image_asset_ids:
                log_debug('GamesFaqScraper::_get_image_url_from_page() Found match {}'.format(image_on_page['alt']))
                return image_on_page['url']
        log_debug('GamesFaqScraper::_get_image_url_from_page() No correct match')

        return ''

    # --- This class own methods -----------------------------------------------------------------
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
        #
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

    def _load_assets_from_url(self, url):
        log_debug('GamesFaqScraper::_load_assets_from_url() Get asset data from {}'.format(url))
        page_data = net_get_URL_oneline(url)
        assets_list = []

        asset_blocks = re.findall('<div class=\"head\"><h2 class=\"title\">((\w|\s)+?)</h2></div><div class=\"body\"><table class=\"contrib\">(.*?)</table></div>', page_data)
        for asset_block in asset_blocks:
            remote_asset_type   = asset_block[0]
            assets_page_data    = asset_block[2]
            log_debug('Collecting assets from {}'.format(remote_asset_type))
            asset_infos = []

            # The Game Images URL shows a page with boxart and screenshots thumbnails.
            # Boxart can be diferent depending on the ROM/game region. Each region has then a 
            # separate page with the full size artwork (boxfront, boxback, etc.)
            #
            # URL Example:
            # http://www.gamefaqs.com/snes/588741-super-metroid/images
            if 'Box' in remote_asset_type:
                asset_infos = [g_assetFactory.get_asset_info(ASSET_BOXFRONT_ID), g_assetFactory.get_asset_info(ASSET_BOXBACK_ID)]
                
            # In an screenshot artwork page there is only one image.
            # >> Title is usually the first or first snapshots in GameFAQs.
            title_snap_taken = True
            if 'Screenshots' in remote_asset_type:
                asset_infos = [g_assetFactory.get_asset_info(ASSET_SNAP_ID)]
                
                if not('?page=' in url):
                    asset_infos.append(g_assetFactory.get_asset_info(ASSET_TITLE_ID))
                    title_snap_taken = False
                                    
            # <a href="/nes/578318-castlevania/images/135454"><img class="img100 imgboxart" src="https://gamefaqs.akamaized.net/box/2/7/6/2276_thumb.jpg" alt="Castlevania (US)" /></a>
            block_items = re.finditer('<a href=\"(?P<lnk>.+?)\"><img class=\"(img100\s)?imgboxart\" src=\"(.+?)\" (alt=\"(?P<alt>.+?)\")?\s?/></a>', assets_page_data)
            for m in block_items:
                image_data = m.groupdict()

                for asset_info in asset_infos:

                    if asset_info.id == ASSET_TITLE_ID and title_snap_taken:
                        continue

                    asset_data = self._new_assetdata_dic()
                
                    asset_data['type']  = asset_info
                    asset_data['url']   = image_data['lnk']
                    asset_data['name']  = image_data['alt'] if 'alt' in image_data else image_data['link']
                    asset_data['is_on_page'] = True
                    
                    assets_list.append(asset_data)
                    if asset_info.id == ASSET_TITLE_ID:
                        title_snap_taken = True

        next_page_result = re.findall('<li><a href="(\S*?)">Next Page\s<i', page_data, re.MULTILINE)
        if len(next_page_result) > 0:
            new_url = 'https://gamefaqs.gamespot.com{}'.format(next_page_result[0])
            assets_list = assets_list + self._load_assets_from_url(new_url)

        return assets_list

    def _parse_asset_type(self, header):
        if 'Screenshots' in header:
            return [ASSET_SNAP_ID, ASSET_TITLE_ID]
        if 'Box Back' in header:
            return [ASSET_BOXBACK_ID]
        if 'Box Front' in header:
            return [ASSET_BOXFRONT_ID]
        if 'Box' in header:
            return [ASSET_BOXFRONT_ID, ASSET_BOXBACK_ID]

        return [ASSET_SNAP_ID]

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
        return True if asset_ID in ArcadeDB.supported_metadata_list else False

    def supports_metadata(self): return True

    def supports_asset_ID(self, asset_ID):
        return True if asset_ID in ArcadeDB.supported_asset_list else False

    def supports_assets(self): return True

    def _scraper_get_candidates(self, search_term, rombase_noext, platform):
        log_debug('ArcadeDB::_scraper_get_candidates() search_term    "{0}"'.format(search_term))
        log_debug('ArcadeDB::_scraper_get_candidates() rom_base_noext "{0}"'.format(rombase_noext))
        log_debug('ArcadeDB::_scraper_get_candidates() AEL platform   "{0}"'.format(platform))

        # --- Get scraping data and cache it ---
        # ArcadeDB QUERY_MAME returns absolutely everything about a single ROM, including
        # metadata, artwork, etc.
        # This data must be cached in this object for every request done.
        cache_str = search_term + '__' + rombase_noext + '__' + platform
        if cache_str in self.cache_QUERY_MAME:
            log_debug('ArcadeDB::_scraper_get_candidates() Cache hit "{0}"'.format(cache_str))
            json_response_dic = self.cache_QUERY_MAME[cache_str]
        else:
            log_debug('ArcadeDB::_scraper_get_candidates() Cache miss "{0}"'.format(cache_str))
            json_response_dic = self._get_QUERY_MAME(search_term, rombase_noext, platform)
            self.cache_QUERY_MAME[cache_str] = json_response_dic

        # --- Return cadidate list ---
        num_games = len(json_response_dic['result'])
        candidate_list = []
        if num_games == 0:
            log_debug('ArcadeDB::_scraper_get_candidates() Scraper found no game.')
        elif num_games == 1:
            log_debug('ArcadeDB::_scraper_get_candidates() Scraper found one game.')
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

    def _scraper_get_metadata(self, candidate):
        # --- Retrieve game data from cache ---
        log_debug('ArcadeDB::_scraper_get_metadata() Cache retrieving "{}"'.format(candidate['cache_str']))
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

    def _scraper_get_assets(self, candidate, asset_ID):
        # --- Retrieve game data from cache ---
        log_debug('ArcadeDB::_scraper_get_assets() Cache retrieving "{}"'.format(candidate['cache_str']))
        json_response_dic = self.cache_QUERY_MAME[candidate['cache_str']]
        gameinfo_dic = json_response_dic['result'][0]

        # --- Parse game assets ---
        all_asset_list = self._get_assets_all(gameinfo_dic)
        asset_list = [asset_dic for asset_dic in all_asset_list if asset_dic['asset_ID'] == asset_ID]
        log_debug('ArcadeDB::_scraper_get_assets() Total assets {0} / Returned assets {1}'.format(
            len(all_asset_list), len(asset_list)))

        return asset_list

    def _scraper_resolve_asset_URL(self, candidate): return candidate['url']

    def _scraper_resolve_asset_URL_extension(self, image_url):
        # All ArcadeDB images are in PNG format
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
        page_raw_data = net_get_URL_original(url)
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
