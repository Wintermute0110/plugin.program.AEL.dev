# -*- coding: utf-8 -*-

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
import datetime
import json
import time
import urllib

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
# 4) The actual object metadata/asset scraping is done by an scraper_strategy object instance.
#
# 5) progress_dialog_obj object instance is passed to the scraper_strategy instance.
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
# scraper_strategy.process_ROM_assets() scrapes all enabled assets in sequence using all the
# configured scrapers (primary, secondary).
#
# g_scraper_factory = ScraperFactory(g_PATHS, g_settings)
# scraper_strategy = g_scraper_factory.create_scanner(launcher_obj, progress_dialog_obj)
# scraper_strategy.process_ROM_metadata(rom_obj)
# scraper_strategy.process_ROM_assets(rom_obj)
#
# --- Use case B: ROM context menu ---------------------------------------------------------------
# In the ROM context menu the scraper object may be called multiple times by the recursive
# context menu. Scrapers should report the assets they support to build the dynamic context
# menu.
#
# --- Code example ---
# g_scraper_factory is a global object created when the addon is initialised.
# g_scraper_factory._supports_asset(scraper_ID, asset_ID) is an internal function.
#
# g_scraper_factory = ScraperFactory(g_PATHS, g_settings)
# g_scraper_factory.get_scraper_menu_list(asset_ID)
# index = dialog.select( ... )
# scraper_ID = g_scraper_factory.get_scraper_ID_from_index(index - num_common_menu_items)
#
# THIS (may be called multiple times)
# scraper_strategy = g_scraper_factory.create_metadata(launcher_obj, scraper_ID, progress_dialog_obj)
# scraper_strategy.scrape_metadata(rom_obj)
#
# OR THIS (may be called multiple times)
# scraper_strategy = g_scraper_factory.create_asset(launcher_obj, scraper_ID, progress_dialog_obj)
# scraper_strategy.scrape_asset(rom_obj)
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
        self.scraper_objs = {}
        if SCRAPER_NULL_ID in SCRAPER_LIST:
            self.scraper_objs[SCRAPER_NULL_ID] = Null_Scraper(self.settings)
        if SCRAPER_AEL_OFFLINE_ID in SCRAPER_LIST:
            self.scraper_objs[SCRAPER_AEL_OFFLINE_ID] = AEL_Offline_Scraper(self.settings)
        if SCRAPER_LB_OFFLINE_ID in SCRAPER_LIST:
            self.scraper_objs[SCRAPER_LB_OFFLINE_ID] = LB_Offline_Scraper(self.settings)
        if SCRAPER_THEGAMESDB_ID in SCRAPER_LIST:
            self.scraper_objs[SCRAPER_THEGAMESDB_ID] = TheGamesDB_Scraper(self.settings)
        if SCRAPER_MOBYGAMES_ID in SCRAPER_LIST:
            self.scraper_objs[SCRAPER_MOBYGAMES_ID] = MobyGames_Scraper(self.settings)
        if SCRAPER_GAMEFAQS_ID in SCRAPER_LIST:
            self.scraper_objs[SCRAPER_GAMEFAQS_ID] = GameFAQs_Scraper(self.settings)
        if SCRAPER_ARCADEDB_ID in SCRAPER_LIST:
            self.scraper_objs[SCRAPER_ARCADEDB_ID] = ArcadeDB_Scraper(self.settings)
        if SCRAPER_SCREENSCRAPER_ID in SCRAPER_LIST:
           self.scraper_objs[SCRAPER_SCREENSCRAPER_ID] = ScrrenScraper_Scraper(self.settings)
        if SCRAPER_LIBRETRO_ID in SCRAPER_LIST:
           self.scraper_objs[SCRAPER_LIBRETRO_ID] = Libretro_Scraper(self.settings)

    # 1) Create the ScraperStrategy object.
    #
    # 2) Read the addon settings and choose the metadata and asset scrapers selected
    #    by the user. Note that the scrapers used depend on the scraping policies.
    #
    # In AEL 0.9.x series launcher is a dictionary. In 0.10.x series it will be a Launcher object.
    #
    # Returns a ScrapeStrategy object which is used for the actual scraping.
    def create_scanner(self, launcher, pdialog, pdialog_verbose):
        log_debug('ScraperFactory::create_scanner() BEGIN ...')

        # --- Create strategy object and get required info from launcher for scraping ---
        strategy_obj = ScrapeStrategy(self.PATHS, self.settings, launcher, pdialog, pdialog_verbose)

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

        return strategy_obj

#
# Main scraping logic.
#
class ScrapeStrategy(object):
    # @param PATHS: PATH object.
    # @param settings: [dict] Addon settings.
    # @param launcher: [dict] Launcher dictionary.
    # @param pdialog: [KodiProgressDialog] object instance.
    # @param pdialog_verbose: [bool] verbose progress dialog.
    def __init__(self, PATHS, settings, launcher, pdialog, pdialog_verbose):
        log_info('ScrapeStrategy::__init__() BEGIN ...')
        self.PATHS = PATHS
        self.settings = settings
        self.launcher = launcher
        self.platform = launcher['platform']
        self.pdialog = pdialog
        self.pdialog_verbose = pdialog_verbose

        # --- Read addon settings and configure scraper setings ---
        # scan_metadata_policy values="None|NFO Files|NFO Files + Scrapers|Scrapers"
        # scan_asset_policy values="Local Assets|Local Assets + Scrapers|Scrapers"
        self.scan_metadata_policy    = self.settings['scan_metadata_policy']
        self.scan_asset_policy       = self.settings['scan_asset_policy']
        self.metadata_scraper_mode   = self.settings['metadata_scraper_mode']
        self.asset_scraper_mode      = self.settings['asset_scraper_mode']
        self.scan_ignore_scrap_title = self.settings['scan_ignore_scrap_title']
        self.scan_clean_tags         = self.settings['scan_clean_tags']

    def check_launcher_unset_asset_dirs(self):
        log_info('ScrapeStrategy::check_launcher_unset_asset_dirs() BEGIN ...')
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
            for i, asset_kind in enumerate(ROM_ASSET_ID_LIST):
                A = assets_get_info_scheme(asset_kind)
                romdata[A.key] = local_asset_list[i]

        elif self.scan_asset_policy == 1:
            log_verb('Asset policy: Local images ON | Scraper ON')
            for i, asset_kind in enumerate(ROM_ASSET_ID_LIST):
                A = assets_get_info_scheme(asset_kind)
                if not self.enabled_asset_list[i]:
                    romdata[A.key] = ''
                    log_verb('Skipped {0} (dir not configured)'.format(A.name))
                    continue
                if local_asset_list[i]:
                    log_verb('Local {0} FOUND'.format(A.name))
                    romdata[A.key] = local_asset_list[i]
                else:
                    log_verb('Local {0} NOT found. Scraping...'.format(A.name))
                    romdata[A.key] = self._roms_scrap_asset(asset_kind, local_asset_list[i], ROM)

        elif self.scan_asset_policy == 2:
            log_verb('Asset policy: Local images OFF | Scraper ON')
            for i, asset_kind in enumerate(ROM_ASSET_ID_LIST):
                A = assets_get_info_scheme(asset_kind)
                if not self.enabled_asset_list[i]:
                    romdata[A.key] = ''
                    log_verb('Skipped {0} (dir not configured)'.format(A.name))
                    continue
                romdata[A.key] = self._roms_scrap_asset(asset_kind, local_asset_list[i], ROM)

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
        log_debug('ScrapeStrategy::_scrap_ROM_metadata_scanner() BEGIN ...')

        # For now just use the first scraper
        scraper_obj = self.metadata_scraper_list[0]
        log_debug('Using metadata scraper "{0}"'.format(scraper_obj.get_name()))

        # --- Update scanner progress dialog ---
        if self.pdialog_verbose:
            scraper_text = 'Scraping metadata with {0} (Searching ...)'.format(scraper_obj.get_name())
            self.pdialog.updateMessage2(scraper_text)

        # --- Do a search and get a list of games ---
        search_term = text_format_ROM_name_for_scraping(ROM.getBase_noext())
        candidates = scraper_obj.get_candidates(search_term, ROM.getBase_noext(), self.platform)
        log_debug('Metadata scraper {0} found {1} candidate/s'.format(scraper_obj.get_name(), len(candidates)))
        if not candidates:
            log_verb('Found no candidates after searching. Cleaning ROM name only.')
            romdata['m_name'] = text_format_ROM_title(ROM.getBase_noext(), self.scan_clean_tags)
            return

        # metadata_scraper_mode values="Semi-automatic|Automatic"
        if self.metadata_scraper_mode == 0:
            log_debug('Metadata semi-automatic scraping')
            # Close scanner progress dialog (and check it was not canceled)
            if self.pdialog.iscanceled(): self.pDialog_canceled = True
            self.pdialog.close()

            # Display corresponding game list found so user chooses.
            dialog = xbmcgui.Dialog()
            rom_name_list = [game['display_name'] for game in candidates]
            selected_candidate = dialog.select(
                'Select game for ROM {0}'.format(rom_path.getBaseNoExt()), rom_name_list)
            if selected_candidate < 0: selected_candidate = 0

            # Open scanner progress dialog again
            self.pdialog.create('Advanced Emulator Launcher')
            if not self.pdialog_verbose: self.pdialog.update(self.progress_number, self.file_text)
        elif self.metadata_scraper_mode == 1:
            log_debug('Metadata automatic scraping. Selecting first result.')
            selected_candidate = 0
        else:
            raise AddonError('Invalid metadata_scraper_mode {0}'.format(self.metadata_scraper_mode))

        # --- Update scanner progress dialog ---
        if self.pdialog_verbose:
            scraper_text = 'Scraping metadata with {0} (Getting metadata ...)'.format(scraper_obj.get_name())
            self.pdialog.updateMessage2(scraper_text)

        # --- Grab metadata for selected game and put into ROM ---
        game_data = scraper_obj.get_metadata(candidates[selected_candidate])
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
        log_debug('ScrapeStrategy::_scrap_ROM_asset_scanner() BEGIN ...')

        # For now just use the first scraper
        scraper_obj = self.metadata_scraper_list[0]
        log_debug('Using metadata scraper "{0}"'.format(scraper_obj.get_name()))

        # By default always use local image if found in case scraper fails.
        ret_asset_path = local_asset_path

        # --- Customise function depending of image_king ---
        A = assets_get_info_scheme(asset_kind)
        asset_directory  = FileName(launcher[A.path_key])
        asset_path_noext_FN = assets_get_path_noext_DIR(A, asset_directory, ROM)
        platform = launcher['platform']

        # --- Updated progress dialog ---
        if self.pDialog_verbose:
            scraper_text = 'Scraping {0} with {1}. Searching for matching games ...'.format(A.name, scraper_obj.name)
            self.pDialog.update(self.progress_number, self.file_text, scraper_text)
        log_verb('_roms_scrap_asset() Scraping {0} with {1}'.format(A.name, scraper_obj.name))
        log_debug('_roms_scrap_asset() local_asset_path "{0}"'.format(local_asset_path))
        log_debug('_roms_scrap_asset() asset_path_noext "{0}"'.format(asset_path_noext_FN.getPath()))

        # --- If scraper does not support particular asset return inmediately ---
        if not scraper_obj.supports_asset(asset_kind):
            log_debug('_roms_scrap_asset() Scraper {0} does not support asset {1}. '
                      'Skipping.'.format(scraper_obj.name, A.name))
            return ret_asset_path

        # --- Set scraping mode ---
        # settings.xml: id="asset_scraper_mode"  default="0" values="Semi-automatic|Automatic"
        scraping_mode = self.settings['asset_scraper_mode']

        # --- Check cache to check if user choose a game previously ---
        # >> id(object)
        # >> This is an integer (or long integer) which is guaranteed to be unique and constant for 
        # >> this object during its lifetime.
        scraper_id = id(scraper_obj)
        log_debug('_roms_scrap_asset() Scraper ID          "{0}"'.format(scraper_id))
        log_debug('_roms_scrap_asset() Scraper obj name    "{0}"'.format(scraper_obj.name))
        log_debug('_roms_scrap_asset() ROM.getBase_noext() "{0}"'.format(ROM.getBase_noext()))
        log_debug('_roms_scrap_asset() platform            "{0}"'.format(platform))
        log_debug('_roms_scrap_asset() Entries in cache    {0}'.format(len(self.scrap_asset_cached_dic)))
        if scraper_id in self.scrap_asset_cached_dic and \
           self.scrap_asset_cached_dic[scraper_id]['ROM_base_noext'] == ROM.getBase_noext() and \
           self.scrap_asset_cached_dic[scraper_id]['platform'] == platform:
            selected_game = self.scrap_asset_cached_dic[scraper_id]['game_dic']
            log_debug('_roms_scrap_asset() Cache HIT. Using cached game "{0}"'.format(selected_game['display_name']))
        else:
            log_debug('_roms_scrap_asset() Cache MISS. Calling scraper_obj.get_search()')
            # --- Call scraper and get a list of games ---
            rom_name_scraping = text_format_ROM_name_for_scraping(ROM.getBase_noext())
            search_results = scraper_obj.get_search(rom_name_scraping, ROM.getBase_noext(), platform)
            log_debug('{0} scraper found {1} result/s'.format(A.name, len(search_results)))
            if not search_results:
                log_debug('{0} scraper did not found any game'.format(A.name))
                return ret_asset_path

            # --- Choose game to download image ---
            if scraping_mode == 0:
                if len(search_results) == 1:
                    log_debug('get_search() returned 1 game. Automatically selected.')
                    selected_game_index = 0
                else:
                    log_debug('{0} semi-automatic scraping. User chooses game.'.format(A.name))
                    # >> Close progress dialog (and check it was not canceled)
                    if self.pDialog.iscanceled(): self.pDialog_canceled = True
                    self.pDialog.close()

                    # >> Display game list found so user choses
                    rom_name_list = []
                    for game in search_results:
                        rom_name_list.append(game['display_name'])
                    selected_game_index = xbmcgui.Dialog().select(
                        '{0} game for ROM "{1}"'.format(scraper_obj.name, ROM.getBase_noext()),
                        rom_name_list)
                    if selected_game_index < 0: selected_game_index = 0

                    # >> Open progress dialog again
                    self.pDialog.create('Advanced Emulator Launcher')
                    if not self.pDialog_verbose: self.pDialog.update(self.progress_number, self.file_text)
            elif scraping_mode == 1:
                log_debug('{0} automatic scraping. Selecting first result.'.format(A.name))
                selected_game_index = 0
            else:
                log_error('{0} invalid scraping_mode {1}'.format(A.name, scraping_mode))
                selected_game_index = 0

            # --- Cache selected game from get_search() ---
            self.scrap_asset_cached_dic[scraper_id] = {
                'ROM_base_noext' : ROM.getBase_noext(),
                'platform' : platform,
                'game_dic' : search_results[selected_game_index]
            }
            selected_game = self.scrap_asset_cached_dic[scraper_id]['game_dic']
            log_error('_roms_scrap_asset() Caching selected game "{0}"'.format(selected_game['display_name']))
            log_error('_roms_scrap_asset() Scraper object ID {0} (name {1})'.format(id(scraper_obj), scraper_obj.name))

        # --- Grab list of images for the selected game ---
        # >> ::get_images() always caches URLs for a given selected_game internally.
        if self.pDialog_verbose:
            scraper_text = 'Scraping {0} with {1}. Getting list of images ...'.format(A.name, scraper_obj.name)
            self.pDialog.update(self.progress_number, self.file_text, scraper_text)
        image_list = scraper_obj.get_images(selected_game, asset_kind)
        log_verb('{0} scraper returned {1} images'.format(A.name, len(image_list)))
        if not image_list:
            log_debug('{0} scraper get_images() returned no images.'.format(A.name))
            return ret_asset_path

        # --- Semi-automatic scraping (user choses an image from a list) ---
        if scraping_mode == 0:
            # >> If there is a local image add it to the list and show it to the user
            if os.path.isfile(local_asset_path):
                image_list.insert(0, {'name'       : 'Current local image', 
                                      'id'         : local_asset_path,
                                      'URL'        : local_asset_path,
                                      'asset_kind' : asset_kind})

            # >> If image_list has only 1 element do not show select dialog. Note that the length
            # >> of image_list is 1 only if scraper returned 1 image and a local image does not exist.
            if len(image_list) == 1:
                image_selected_index = 0
            else:
                # >> Close progress dialog before opening image chosing dialog
                if self.pDialog.iscanceled(): self.pDialog_canceled = True
                self.pDialog.close()

                # >> Convert list returned by scraper into a list the select window uses
                ListItem_list = []
                for item in image_list:
                    listitem_obj = xbmcgui.ListItem(label = item['name'], label2 = item['URL'])
                    listitem_obj.setArt({'icon' : item['URL']})
                    ListItem_list.append(listitem_obj)
                image_selected_index = xbmcgui.Dialog().select('Select {0} image'.format(A.name),
                                                               list = ListItem_list, useDetails = True)
                log_debug('{0} dialog returned index {1}'.format(A.name, image_selected_index))
                if image_selected_index < 0: image_selected_index = 0

                # >> Reopen progress dialog
                self.pDialog.create('Advanced Emulator Launcher')
                if not self.pDialog_verbose: self.pDialog.update(self.progress_number, self.file_text)
        # --- Automatic scraping. Pick first image. ---
        else:
            image_selected_index = 0
        selected_image = image_list[image_selected_index]

        # --- Update progress dialog ---
        if self.pDialog_verbose:
            scraper_text = 'Scraping {0} with {1}. Downloading image ...'.format(A.name, scraper_obj.name)
            self.pDialog.update(self.progress_number, self.file_text, scraper_text)

        # --- If user chose the local image don't download anything ---
        if selected_image['id'] != local_asset_path:
            log_debug('_roms_scrap_asset() Downloading selected image ...')

            # --- Resolve image URL ---
            image_url, image_ext = scraper_obj.resolve_image_URL(selected_image)
            log_debug('Selected image URL "{1}"'.format(A.name, image_url))

            # ~~~ Download image ~~~
            image_path = asset_path_noext_FN.append(image_ext).getPath()
            log_verb('Downloading URL  "{0}"'.format(image_url))
            log_verb('Into local file  "{0}"'.format(image_path))
            try:
                net_download_img(image_url, image_path)
            except socket.timeout:
                kodi_notify_warn('Cannot download {0} image (Timeout)'.format(A.name))

            # ~~~ Update Kodi cache with downloaded image ~~~
            # Recache only if local image is in the Kodi cache, this function takes care of that.
            kodi_update_image_cache(image_path)

            # --- Return value is downloaded image ---
            ret_asset_path = image_path
        else:
            log_debug('_roms_scrap_asset() User chose local {0} "{1}"'.format(A.name, local_asset_path))
            ret_asset_path = local_asset_path

        # --- Returned value ---
        return ret_asset_path

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
            rom_name = text_format_ROM_title(rom_path.getBaseNoExt(), self.scraper_settings.scan_clean_tags)
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

    def _apply_candidate_on_asset(self, rom_path, rom, asset_info, found_assets):
        if not found_assets:
            log_debug('{0} scraper has not collected images.'.format(self.getName()))
            return False

        asset_directory = self.launcher.get_asset_path(asset_info)
        asset_path_noext_FN = assets_get_path_noext_DIR(asset_info, asset_directory, rom_path)
        log_debug('Scraper.apply_candidate_on_asset() asset_path_noext "{0}"'.format(asset_path_noext_FN.getPath()))

        specific_images_list = [image_entry for image_entry in found_assets if image_entry['type'].id == asset_info.id]

        log_debug('{} scraper has collected {} assets of type {}.'.format(self.getName(), len(specific_images_list), asset_info.name))
        if len(specific_images_list) == 0:
            log_debug('{0} scraper has not collected images for asset {1}.'.format(self.getName(), asset_info.name))
            return False

        # --- Semi-automatic scraping (user choses an image from a list) ---
        if self.scraper_settings.asset_scraping_mode == 0:
            # >> If specific_images_list has only 1 element do not show select dialog. Note that the length
            # >> of specific_images_list is 1 only if scraper returned 1 image and a local image does not exist.
            if len(specific_images_list) == 1:
                image_selected_index = 0
            else:
                # >> Close progress dialog before opening image chosing dialog
                #if self.pDialog.iscanceled(): self.pDialog_canceled = True
                #self.pDialog.close()

                # >> Convert list returned by scraper into a list the select window uses
                ListItem_list = []
                for item in specific_images_list:
                    listitem_obj = xbmcgui.ListItem(label = item['name'], label2 = item['url'])
                    listitem_obj.setArt({'icon' : item['url']})
                    ListItem_list.append(listitem_obj)

                image_selected_index = xbmcgui.Dialog().select('Select {0} image'.format(asset_info.name),
                                                                list = ListItem_list, useDetails = True)
                log_debug('{0} dialog returned index {1}'.format(asset_info.name, image_selected_index))

            if image_selected_index < 0:
                return False

            # >> Reopen progress dialog
            #self.pDialog.create('Advanced Emulator Launcher')
            #if not self.pDialog_verbose: self.pDialog.update(self.progress_number, self.file_text)

        # --- Automatic scraping. Pick first image. ---
        else:
            image_selected_index = 0

            selected_image = specific_images_list[image_selected_index]

            # --- Update progress dialog ---
            #if self.pDialog_verbose:
            #    scraper_text = 'Scraping {0} with {1}. Downloading image ...'.format(A.name, scraper_obj.name)
            #    self.pDialog.update(self.progress_number, self.file_text, scraper_text)

            log_debug('Scraper.apply_candidate_on_asset() Downloading selected image ...')

            # --- Resolve image URL ---
            if selected_image['is_online']:
                    
                if selected_image['is_on_page']:
                    image_url = self._get_image_url_from_page(selected_image, asset_info)
                else:
                    image_url = selected_image['url']

                image_path = self._download_image(asset_info, image_url, asset_path_noext_FN)

            else:
                log_debug('{0} scraper: user chose local image "{1}"'.format(asset_info.name, selected_image['url']))
                image_path = FileName(selected_image['url'])

            if image_path:
                rom.set_asset(asset_info, image_path)        
        
        return True

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
        self._reset_caches()
        self.verbose_flag = False
        self.dump_file_flag = False

        # --- Initialize common scraper settings ---
        # None at the moment. Note that settings that affect the scraping policy belong
        # in the ScrapeStrategy class and not here.

    # Scraper is much more verbose (even more than AEL Debug level).
    def set_verbose_mode(self, verbose_flag):
        self.verbose_flag = verbose_flag

    # Dump scraper data into files for debugging.
    def set_debug_file_dump(self, dump_file_flag, dump_dir):
        self.dump_file_flag = dump_file_flag
        self.dump_dir = dump_dir

    @abc.abstractmethod
    def get_name(self): pass

    @abc.abstractmethod
    def supports_metadata(self, metadata_ID): pass

    @abc.abstractmethod
    def supports_asset(self, asset_ID): pass

    # OBSOLETE, WILL BE REMOVED SOON.
    # The functionality of this method is being moved to the ScrapeStrategy class.
    def scrape_asset(self, search_term, asset_info_to_scrape, rom_path, rom):
        candidates = self._get_candidates(search_term, rom_path, rom)
        log_debug('Scraper "{0}" found {1} result/s'.format(self.getName(), len(candidates)))

        if not candidates or len(candidates) == 0:
            log_verb('Scraper "{0}" found no games after searching.'.format(self.getName()))
            if self.fallbackScraper:
                return self.fallbackScraper.scrape_asset(search_term, rom_path, rom)
            return False

        selected_candidate = 0
        if len(candidates) > 1 and self.scraper_settings.asset_scraping_mode == 0:
            log_debug('Asset semi-automatic scraping')
            # >> Close progress dialog (and check it was not canceled)
            # ?? todo again

            # >> Display corresponding game list found so user choses
            dialog = xbmcgui.Dialog()
            rom_name_list = []
            for game in candidates: 
                rom_name_list.append(game['display_name'])

            selected_candidate = dialog.select(
                'Select game for ROM {0}'.format(rom_path.getBase_noext()), rom_name_list)
            if selected_candidate < 0: selected_candidate = 0

            # >> Open progress dialog again
            # ?? todo again

        candidate = candidates[selected_candidate]

        # Update cache so future searches will automatically select this candidate for this particular search term
        self._update_cache(search_term, candidate)
        found_assets = self._get_from_assets_cache(candidate['id'])

        # Cache hit?
        if found_assets is None:
            log_debug('No assets matching candidate id in cache. Scraping source for assets.')
            found_assets = self._load_assets(candidate, rom_path, rom)
            # Update assets cache so future searches will automatically select these found assets for this particular search term
            self._update_assets_cache(candidate['id'], found_assets)
        else:
            log_debug('Found cached asset candidates.')

        scraper_applied = self._apply_candidate_on_asset(rom_path, rom, asset_info_to_scrape, found_assets)

        if not scraper_applied and self.fallbackScraper is not None:
            log_verb('Scraper "{0}" did not get the correct data. Using fallback scraping method: {1}.'.format(
                self.getName(), self.fallbackScraper.getName()))
            return self.fallbackScraper.scrape_asset(search_term, rom_path, rom)

        return scraper_applied

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
        cache_str = search_term + rombase_noext + platform
        if cache_str in self.cache_candidates:
            log_debug('Scraper::get_candidates() Cache hit "{0}"'.format(search_term))
            candidate_list = self.cache_candidates[cache_str]
        else:
            log_debug('Scraper::get_candidates() Cache miss "{0}"'.format(search_term))
            candidate_list = self._scraper_get_candidates(search_term, rombase_noext, platform)
            self.cache_candidates[cache_str] = candidate_list

        return candidate_list

    # Returns the metadata for a candidate (search result).
    # Caches all searches. If search is not cached then call abstract method and update the cache.
    #
    # @param candidate: [dict] Candidate returned by get_candidates()
    # @return: [dict] Dictionary _new_gamedata_dic(). None if error getting the metadata.
    def get_metadata(self, candidate):
        if candidate['id'] in self.cache_metadata:
            log_debug('Scraper::get_metadata() Cache hit "{0}"'.format(candidate['id']))
            gamedata = self.cache_metadata[candidate['id']]
        else:
            log_debug('Scraper::get_metadata() Cache miss "{0}"'.format(candidate['id']))
            gamedata = self._scraper_get_metadata(candidate)
            self.cache_metadata[candidate['id']] = gamedata

        return gamedata

    # Returns a list of assets for a candidate (search result).
    #
    # @param candidate: [dict] Candidate returned by get_candidates()
    # @return: [list] List of _new_assetdata_dic() dictionaries. None if error getting the metadata.
    def get_assets(self, candidate):
        if candidate['id'] in self.cache_metadata:
            log_debug('Scraper::get_assets() Cache hit "{0}"'.format(candidate['id']))
            assetdata_list = self.cache_metadata[candidate['id']]
        else:
            log_debug('Scraper::get_assets() Cache miss "{0}"'.format(candidate['id']))
            assetdata_list = self._scraper_get_assets(candidate)
            self.cache_metadata[candidate['id']] = assetdata_list

        return assetdata_list

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
    def _scraper_get_assets(self, candidate): pass

    @abc.abstractmethod
    def _scraper_get_image_url_from_page(self, candidate, asset_info): pass

    def _download_image(self, asset_info, image_url, destination_folder):

        if image_url is None or image_url == '':
            log_debug('No image to download. Skipping')
            return None

        image_ext = text_get_image_URL_extension(image_url)
        log_debug('Downloading  {} from image URL "{}"'.format(asset_info.name, image_url))

        # ~~~ Download image ~~~
        image_path = destination_folder.append(image_ext)
        log_verb('Downloading URL  "{0}"'.format(image_url))
        log_verb('Into local file  "{0}"'.format(image_path.getPath()))
        try:
            net_download_img(image_url, image_path)
        except socket.timeout:
            log_error('Cannot download {0} image (Timeout)'.format(asset_info.name))
            kodi_notify_warn('Cannot download {0} image (Timeout)'.format(asset_info.name))
            return None

        return image_path

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
            'id'                : '',
            'display_name'      : '',
            'platform'          : '',
            'scraper_platform' : '',
            'order'             : 0,
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

    def _new_assetdata_dic(self):
        return {
            'asset_id'   : None,
            'name'       : '',
            'url'        : '',
            'url_thumb'  : '',
            'is_online'  : True,
            'is_on_page' : False
        }

# ------------------------------------------------------------------------------------------------
# NULL scraper, does nothing.
# ------------------------------------------------------------------------------------------------
class Null_Scraper(Scraper):
    # @param settings: [dict] Addon settings. Particular scraper settings taken from here.
    def __init__(self, settings):
        # Pass down settings that apply to all scrapers.
        super(Null_Scraper, self).__init__(settings)

    def get_name(self): return 'Null'

    def supports_metadata(self, metadata_ID): return True

    def supports_asset(self, asset_ID): return True

    # Null scraper never finds candidates.
    def _scraper_get_candidates(self, search_term): return []

    # Null scraper never returns valid scraped metadata.
    def _scraper_get_metadata(self, candidate): return None

    def _scraper_get_assets(self, candidate): return None

    def _scraper_get_image_url_from_page(self, candidate, asset_info): return ''

# ------------------------------------------------------------------------------------------------
# AEL offline metadata scraper.
# ------------------------------------------------------------------------------------------------
class AEL_Offline_Scraper(Scraper):
    # @param settings: [dict] Addon settings. Particular scraper settings taken from here.
    def __init__(self, settings):
        # Pass down settings that apply to all scrapers.
        super(AEL_Offline_Scraper, self).__init__(settings)

    def get_name(self): return 'AEL Offline'

    def supports_metadata(self, asset_ID): return True

    def supports_asset(self, asset_ID): return True

    # Null scraper never finds candidates.
    def _scraper_get_candidates(self, search_term): return []

    # Null scraper never returns valid scraped metadata.
    def _scraper_get_metadata(self, candidate): return None

    def _scraper_get_assets(self, candidate): return None

    def _scraper_get_image_url_from_page(self, candidate, asset_info): return ''

# ------------------------------------------------------------------------------------------------
# LaunchBox offline metadata scraper.
# ------------------------------------------------------------------------------------------------
class LB_Offline_Scraper(Scraper):
    # @param settings: [dict] Addon settings. Particular scraper settings taken from here.
    def __init__(self, settings):
        # Pass down settings that apply to all scrapers.
        super(LB_Offline_Scraper, self).__init__(settings)

    def get_name(self): return 'LB Offline'

    def supports_metadata(self, asset_ID): return True

    def supports_asset(self, asset_ID): return True

    # Null scraper never finds candidates.
    def _scraper_get_candidates(self, search_term): return []

    # Null scraper never returns valid scraped metadata.
    def _scraper_get_metadata(self, candidate, romPath, rom): return None

    def _scraper_get_assets(self, candidate, romPath, rom): return None

    def _scraper_get_image_url_from_page(self, candidate, asset_info): return ''

# ------------------------------------------------------------------------------------------------
# TheGamesDB online scraper (metadata and assets)
# ------------------------------------------------------------------------------------------------
class TheGamesDB_Scraper(Scraper):
    def __init__(self, settings, launcher):
        self.publishers = None
        self.genres = None
        self.developers = None

        self.api_key = settings['thegamesdb_apikey']
        scraper_settings = ScraperSettings.create_from_settings(settings)

        super(TheGamesDB_Scraper, self).__init__(scraper_settings, launcher, fallbackScraper)

    def get_name(self): return 'TheGamesDB'

    def supports_asset(self, asset_ID):
        if asset_info.id == ASSET_CARTRIDGE_ID or asset_info.id == ASSET_FLYER_ID:
            return False

        return True

    def _get_candidates(self, search_term, romPath, rom):
        platform = self.launcher.get_platform()
        scraper_platform = AEL_platform_to_TheGamesDB(platform)
        
        log_debug('TheGamesDB_Scraper::_get_candidates() search_term         "{0}"'.format(search_term))
        log_debug('TheGamesDB_Scraper::_get_candidates() rom_base_noext      "{0}"'.format(romPath.getBaseNoExt()))
        log_debug('TheGamesDB_Scraper::_get_candidates() AEL platform        "{0}"'.format(platform))
        log_debug('TheGamesDB_Scraper::_get_candidates() TheGamesDB platform "{0}"'.format(scraper_platform))
        
        # >> Check if search term page data is in cache. If so it's a cache hit.
        candidate_from_cache = self._get_from_cache(search_term)
        
        if candidate_from_cache is not None:
            log_debug('Using a cached candidate')
            return [candidate_from_cache]

        game_list = []
        # >> quote_plus() will convert the spaces into '+'. Note that quote_plus() requires an
        # >> UTF-8 encoded string and does not work with Unicode strings.
        # added encoding 
        # https://stackoverflow.com/questions/22415345/using-pythons-urllib-quote-plus-on-utf-8-strings-with-safe-arguments
            
        search_string_encoded = urllib.quote_plus(search_term.encode('utf8'))
        url = 'https://api.thegamesdb.net/Games/ByGameName?apikey={}&name={}'.format(self.api_key, search_string_encoded)
            
        game_list = self._read_games_from_url(url, search_term, scraper_platform)
        
        if len(game_list) == 0:
            altered_search_term = self._cleanup_searchterm(search_term, romPath, rom)
            if altered_search_term != search_term:
                log_debug('TheGamesDbScraper::_get_candidates() No hits, trying again with altered search terms: {}'.format(altered_search_term))
                return self._get_candidates(altered_search_term, romPath, rom)

        # >> Order list based on score
        game_list.sort(key = lambda result: result['order'], reverse = True)

        return game_list

    def _load_metadata(self, candidate, romPath, rom):
        url = 'https://api.thegamesdb.net/Games/ByGameID?apikey={}&id={}&fields=players%2Cpublishers%2Cgenres%2Coverview%2Crating%2Cplatform%2Ccoop%2Cyoutube'.format(
                self.api_key, candidate['id'])
        
        log_debug('Get metadata from {}'.format(url))
        page_data = net_get_URL_as_json(url)
        online_data = page_data['data']['games'][0]
        
        game_data = self._new_gamedata_dic()

        # --- Parse game page data ---
        game_data['title']      = online_data['game_title'] if 'game_title' in online_data else '' 
        game_data['nplayers']   = online_data['players'] if 'players' in online_data else '' 
        game_data['esrb']       = online_data['rating'] if 'rating' in online_data else '' 
        game_data['plot']       = online_data['overview'] if 'overview' in online_data else '' 
        game_data['genre']      = self._get_genres(online_data['genres']) if 'genres' in online_data else '' 
        game_data['developer']  = self._get_developers(online_data['developers']) if 'developers' in online_data else '' 
        game_data['year']       = online_data['release_date'][:4] if 'release_date' in online_data and online_data['release_date'] is not None and online_data['release_date'] != '' else ''
        
        return game_data

    def _load_assets(self, candidate, romPath, rom):
        url = 'https://api.thegamesdb.net/Games/Images?apikey={}&games_id={}'.format(self.api_key, candidate['id'])
        asset_list = self._read_assets_from_url(url, candidate['id'])
        log_debug('Found {} assets for candidate #{}'.format(len(asset_list), candidate['id']))
        return asset_list

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
        page_data = net_get_URL_as_json(url)

        # If nothing is returned maybe a timeout happened. In this case, reset the cache.
        if page_data is None:
            self._reset_cache()

        games = page_data['data']['games']
        game_list = []
        for item in games:
            title    = item['game_title']
            platform = item['platform']
            display_name = '{} / {}'.format(title, platform)
            game = self._new_candidate_dic()
            game['id'] = item['id']
            game['display_name'] = display_name
            game['order'] = 1
            # Increase search score based on our own search
            if title.lower() == search_term.lower():                  game['order'] += 2
            if title.lower().find(search_term.lower()) != -1:         game['order'] += 1
            if scraper_platform > 0 and platform == scraper_platform: game['order'] += 1

            game_list.append(game)

        next_url = page_data['pages']['next']
        if next_url is not None:
            game_list = game_list + self._read_games_from_url(next_url, search_term, scraper_platform)

        return game_list

    def _read_assets_from_url(self, url, candidate_id):
        log_debug('Get image data from {}'.format(url))

        page_data   = net_get_URL_as_json(url)
        online_data = page_data['data']['images'][str(candidate_id)]
        base_url    = page_data['data']['base_url']['original']

        assets_list = []
        # --- Parse images page data ---
        for image_data in online_data:
            asset_data = self._new_assetdata_dic()
            asset_kind = self._convert_to_asset_kind(image_data['type'], image_data['side'])

            if asset_kind is None:
                continue

            asset_info = g_assetFactory.get_asset_info(asset_kind)

            asset_data['type']  = asset_info
            asset_data['url']   = base_url + image_data['filename']
            asset_data['name']  = ' '.join(filter(None, [image_data['type'], image_data['side'], image_data['resolution']]))

            log_debug('TheGamesDbScraper:: found asset {}: {}'.format(asset_data['name'], asset_data['url']))
            assets_list.append(asset_data)
            
        next_url = page_data['pages']['next']
        if next_url is not None:
            assets_list = assets_list + self._read_assets_from_url(next_url, candidate_id)

        return assets_list

    asset_name_mapping = {
        'fanart' : ASSET_FANART_ID,
        'clearlogo': ASSET_CLEARLOGO_ID,
        'banner': ASSET_BANNER_ID,
        'boxartfront': ASSET_BOXFRONT_ID,
        'boxartback': ASSET_BOXBACK_ID,
        'screenshot': ASSET_SNAP_ID
    }

    def _convert_to_asset_kind(self, type, side):
        if side is not None:
            type = type + side

        asset_key = TheGamesDbScraper.asset_name_mapping[type]
        return asset_key

    def _cleanup_searchterm(self, search_term, rom_path, rom):
        altered_term = search_term.lower().strip()
        for ext in self.launcher.get_rom_extensions():
            altered_term = altered_term.replace(ext, '')

        return altered_term

    def _get_publishers(self, publisher_ids):
        if publisher_ids is None: return ''

        if self.publishers is None:
            log_debug('TheGamesDbScraper::No cached publishers. Retrieving from online.')
            self.publishers = {}
            url = 'https://api.thegamesdb.net/Publishers?apikey={}'.format(self.api_key)
            publishers_json = net_get_URL_as_json(url)
            for publisher_id in publishers_json['data']['publishers']:
                self.publishers[int(publisher_id)] = publishers_json['data']['publishers'][publisher_id]['name']

        publisher_names = []
        for publisher_id in publisher_ids:
            publisher_names.append(self.publishers[publisher_id])

        return ' / '.join(publisher_names)

    def _get_genres(self, genre_ids):
        if genre_ids is None: return ''

        if self.genres is None:
            log_debug('TheGamesDbScraper::No cached genres. Retrieving from online.')
            self.genres = {}
            url = 'https://api.thegamesdb.net/Genres?apikey={}'.format(self.api_key)
            genre_json = net_get_URL_as_json(url)
            for genre_id in genre_json['data']['genres']:
                self.genres[int(genre_id)] = genre_json['data']['genres'][genre_id]['name']

        genre_names = []
        for genre_id in genre_ids:
            genre_names.append(self.genres[genre_id])

        return ' / '.join(genre_names)

    def _get_developers(self, developer_ids):
        if developer_ids is None: return ''

        if self.developers is None:
            log_debug('TheGamesDbScraper::No cached developers. Retrieving from online.')
            self.developers = {}
            url = 'https://api.thegamesdb.net/Developers?apikey={}'.format(self.api_key)
            developers_json = net_get_URL_as_json(url)
            for developer_id in developers_json['data']['developers']:
                self.developers[int(developer_id)] = developers_json['data']['developers'][developer_id]['name']

        developer_names = []
        for developer_id in developer_ids:
            developer_names.append(self.developers[developer_id])

        return ' / '.join(developer_names)

    def _get_image_url_from_page(self, candidate, asset_info):
        return candidate['url']

# ------------------------------------------------------------------------------------------------
# MobyGames http://www.mobygames.com
#
# TODO
# 1) Detect 401 Unauthorized and warn user.
#
# 2) Detect 429 Too Many Requests and disable scraper. We never do more than one call per second
#    so if we get 429 is because the 360 API requests per hour are consumed.
#
# MobiGames API https://www.mobygames.com/info/api
# ------------------------------------------------------------------------------------------------
class MobyGames_Scraper(Scraper):
    # Class variables
    supported_metadata_list = [
        META_TITLE_ID, META_YEAR_ID, META_GENRE_ID, META_DEVELOPER_ID,
        META_NPLAYERS_ID, META_ESRB_ID, META_RATING_ID, META_PLOT_ID,
    ]
    supported_asset_list = [
        ASSET_FANART_ID, ASSET_BANNER_ID, ASSET_CLEARLOGO_ID, ASSET_FLYER_ID,
    ]
    asset_name_mapping = {
        'media'       : ASSET_CARTRIDGE_ID,
        'manual'      : ASSET_MANUAL_ID,
        'front cover' : ASSET_BOXFRONT_ID,
        'back cover'  : ASSET_BOXBACK_ID,
        'spine/sides' : 0 # not supported by AEL?
    }

    def __init__(self, settings):
        # This scraper settings
        self.api_key = settings['scraper_mobygames_apikey']
        self.last_http_call = datetime.datetime.now()

        # Pass down settings that apply to all scrapers.
        super(MobyGames_Scraper, self).__init__(settings)

    def get_name(self): return 'MobyGames'

    def supports_metadata(self, metadata_ID):
        return True if asset_ID in supported_metadata_list else False

    def supports_asset(self, asset_ID):
        return True if asset_ID in supported_asset_list else False

    # Cache is done in the base class. If this function is called it was a cache miss.
    # The cache will be updated with whatever this functions returns.
    def _scraper_get_candidates(self, search_term, rombase_noext, platform):
        scraper_platform = AEL_platform_to_MobyGames(platform)
        log_debug('MobyGamesScraper::_scraper_get_candidates() search_term        "{0}"'.format(search_term))
        log_debug('MobyGamesScraper::_scraper_get_candidates() rom_base_noext     "{0}"'.format(rombase_noext))
        log_debug('MobyGamesScraper::_scraper_get_candidates() AEL platform       "{0}"'.format(platform))
        log_debug('MobyGamesScraper::_scraper_get_candidates() MobyGames platform "{0}"'.format(scraper_platform))

        search_string_encoded = urllib.quote_plus(search_term.encode('utf8'))
        url_str = 'https://api.mobygames.com/v1/games?api_key={0}&format=brief&title={1}&platform={2}'
        url = url_str.format(self.api_key, search_string_encoded, scraper_platform)
        game_list = self._read_games_from_url(url, search_term, platform, scraper_platform)
        # Order list based on score. High score first.
        game_list.sort(key = lambda result: result['order'], reverse = True)

        return game_list

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
        game_data = self._new_gamedata_dic()
        game_data['title'] = online_data['title'] if 'title' in online_data else ''
        game_data['plot']  = online_data['description'] if 'description' in online_data else ''
        game_data['genre'] = self._get_genres(online_data['genres']) if 'genres' in online_data else ''
        game_data['year']  = self._get_year_by_platform(online_data['platforms'], candidate['scraper_platform'])

        return game_data

    def _get_genres(self, genre_data):
        genre_names = []
        for genre in genre_data:
            genre_names.append(genre['genre_name'])

        return ' / '.join(genre_names)

    def _get_year_by_platform(self, platform_data, platform_id):
        if len(platform_data) == 0:
            return ''

        year_data = None
        for platform in platform_data:
            if platform['platform_id'] == int(platform_id):
                year_data = platform['first_release_date']
                break

        if year_data is None:
            year_data = platform_data[0]['first_release_date']

        return year_data[:4]

    def _scraper_get_assets(self, candidate):
        log_debug('MobyGames_Scraper::_scraper_get_assets() Getting MobyGames Snaps...')
        snap_assets = self._load_snap_assets(candidate, candidate['scraper_platform'])
        log_debug('MobyGames_Scraper::_scraper_get_assets() Getting MobyGames Covers...')
        cover_assets = self._load_cover_assets(candidate, candidate['scraper_platform'])
        asset_list = snap_assets + cover_assets
        log_debug('A total of {0} assets found for candidate ID {1}'.format(
            len(asset_list), candidate['id']))

        return asset_list

    def _load_snap_assets(self, candidate, platform_id):
        url = 'https://api.mobygames.com/v1/games/{0}/platforms/{1}/screenshots?api_key={2}'.format(
            candidate['id'], platform_id, self.api_key)
        self._do_toomanyrequests_check()
        page_data_raw = net_get_URL_original(url)
        self.last_http_call = datetime.datetime.now()
        page_data = json.loads(page_data_raw)
        if self.dump_file_flag:
            file_path = os.path.join(self.dump_dir, 'mobygames_snap_assets.txt')
            text_dump_str_to_file(file_path, page_data_raw)

        # --- Parse images page data ---
        asset_list = []
        for image_data in page_data['screenshots']:
            asset_data = self._new_assetdata_dic()
            asset_data['asset_id']  = ASSET_SNAP_ID
            asset_data['name']      = image_data['caption']
            asset_data['url']       = image_data['image']
            asset_data['url_thumb'] = image_data['thumbnail_image']
            if self.verbose_flag:
                log_debug('MobyGamesScraper:: found Snap {0}'.format(asset_data['url']))
            asset_list.append(asset_data)
        log_debug('Found {0} snap assets for candidate #{1}'.format(len(asset_list), candidate['id']))

        return asset_list

    def _load_cover_assets(self, candidate, platform_id):
        url = 'https://api.mobygames.com/v1/games/{0}/platforms/{1}/covers?api_key={2}'.format(
            candidate['id'], platform_id, self.api_key)
        self._do_toomanyrequests_check()
        page_data_raw = net_get_URL_original(url)
        self.last_http_call = datetime.datetime.now()
        page_data = json.loads(page_data_raw)
        if self.dump_file_flag:
            file_path = os.path.join(self.dump_dir, 'mobygames_cover_assets.txt')
            text_dump_str_to_file(file_path, page_data_raw)

        # --- Parse images page data ---
        asset_list = []
        for group_data in page_data['cover_groups']:
            country_names = ' / '.join(group_data['countries'])
            for image_data in group_data['covers']:
                asset_name = '{0} - {1} ({2})'.format(
                    image_data['scan_of'], image_data['description'], country_names)
                asset_data = self._new_assetdata_dic()
                asset_id   = MobyGames_Scraper.asset_name_mapping[image_data['scan_of'].lower()]
                asset_data['asset_id']  = asset_id
                asset_data['name']      = asset_name
                asset_data['url']       = image_data['image']
                asset_data['url_thumb'] = image_data['thumbnail_image']
                if self.verbose_flag:
                    log_debug('MobyGamesScraper:: found Cover {0}'.format(asset_data['url']))
                asset_list.append(asset_data)
        log_debug('Found {0} cover assets for candidate #{1}'.format(len(asset_list), candidate['id']))

        return asset_list

    def _scraper_get_image_url_from_page(self, candidate, asset_id): return candidate['url']

    def _do_toomanyrequests_check(self):
        # Make sure we dont go over the TooManyRequests limit of 1 second.
        now = datetime.datetime.now()
        if (now - self.last_http_call).total_seconds() < 1:
            log_debug('MobyGames_Scraper:: Sleeping 1 second to avoid overloading...')
            time.sleep(1)

# -----------------------------------------------------------------------------
# GameFAQs online scraper
# -----------------------------------------------------------------------------
class GameFAQs_Scraper(Scraper):
    def __init__(self, settings, launcher, fallbackScraper = None):
        scraper_settings = ScraperSettings.create_from_settings(settings)
        super(GameFAQs_Scraper, self).__init__(scraper_settings, launcher, fallbackScraper)

    def get_name(self): return 'GameFAQs'

    def supports_asset_type(self, asset_info):
        if asset_info.id == ASSET_FANART_ID or asset_info.id == ASSET_BANNER_ID or asset_info.id == ASSET_CLEARLOGO_ID or asset_info.id == ASSET_FLYER_ID or asset_info.id == ASSET_CARTRIDGE_ID:
            return False

        return True

    def _get_candidates(self, search_term, romPath, rom):
        platform = self.launcher.get_platform()
        scraper_platform = AEL_platform_to_GameFAQs(platform)

        log_debug('GamesFaqScraper::_get_candidates() search_term         "{0}"'.format(search_term))
        log_debug('GamesFaqScraper::_get_candidates() rom_base_noext      "{0}"'.format(romPath.getBaseNoExt()))
        log_debug('GamesFaqScraper::_get_candidates() AEL platform        "{0}"'.format(platform))
        log_debug('GamesFaqScraper::_get_candidates() GameFAQs platform   "{0}"'.format(scraper_platform))

        # >> Check if search term page data is in cache. If so it's a cache hit.
        candidate_from_cache = self._get_from_cache(search_term)

        if candidate_from_cache is not None:
            log_debug('Using a cached candidate')
            return [candidate_from_cache]

        game_list = []
        game_list = self._get_candidates_from_page(search_term, scraper_platform)

        # >> Order list based on score
        game_list.sort(key = lambda result: result['order'], reverse = True)

        return game_list

    def _get_candidates_from_page(self, search_term, platform, url = None, no_platform=False):
        search_params = urllib.urlencode({'game': search_term}) if no_platform else urllib.urlencode({'game': search_term, 'platform': platform})
        if url is None:
            url = 'https://gamefaqs.gamespot.com/search_advanced'
            page_data = net_post_URL_original(url, search_params)
        else:
            page_data = net_get_URL_original(url)

        # <div class="sr_row"><div class="sr_cell sr_platform">NES</div><div class="sr_cell sr_title"><a href="/nes/578318-castlevania">Castlevania</a></div><div class="sr_cell sr_release">1987</div>
        regex_results = re.findall(r'<div class="sr_cell sr_platform">(.*?)</div>\s*<div class="sr_cell sr_title"><a href="(.*?)">(.*?)</a>', page_data, re.MULTILINE)
        game_list = []
        for result in regex_results:
            game = {}
            game_name            = text_unescape_HTML(result[2])
            game_platform        = result[0]
            game['id']           = result[1]
            game['display_name'] = game_name + ' / ' + game_platform.capitalize()
            game['game_name']    = game_name # Additional GameFAQs scraper field
            game['order']        = 1         # Additional GameFAQs scraper field
        
            if game_name == 'Game':
                continue

            # Increase search score based on our own search
            # In the future use an scoring algortihm based on Levenshtein Distance
            title = game_name
            if title.lower() == search_term.lower():            game['order'] += 1
            if title.lower().find(search_term.lower()) != -1:   game['order'] += 1
            if platform > 0 and game_platform == platform:      game['order'] += 1

            game_list.append(game)

        if len(game_list) == 0 and not no_platform:
            return self._get_candidates_from_page(search_term, platform, no_platform=True)

        next_page_result = re.findall('<li><a href="(\S*?)">Next Page\s<i', page_data, re.MULTILINE)
        if len(next_page_result) > 0:
            link = next_page_result[0].replace('&amp;', '&')
            new_url = 'https://gamefaqs.gamespot.com' + link
            game_list = game_list + self._get_candidates_from_page(search_term, no_platform, new_url)

        game_list.sort(key = lambda result: result['order'], reverse = True)
        
        return game_list
            
    def _load_metadata(self, candidate, romPath, rom):
        
        url = 'https://gamefaqs.gamespot.com{}'.format(candidate['id'])
        
        log_debug('GamesFaqScraper::_load_metadata() Get metadata from {}'.format(url))
        page_data = net_get_URL_oneline(url)

        # Parse data
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

        game_plot = re.findall('Description</h2></div><div class="body game_desc"><div class="desc">(.*?)</div>', page_data)
        
        game_data = self._new_gamedata_dic()
            
        # --- Set game page data ---
        game_data['title']      = candidate['game_name'] 
        game_data['plot']       = text_unescape_and_untag_HTML(game_plot[0]) if game_plot else ''        
        game_data['genre']      = game_genre[0][3] if game_genre else '' 
        game_data['year']       = game_release[0][1][-4:] if game_release else ''
        game_data['developer']  = game_developer

        log_debug('GamesFaqScraper::_load_metadata() Collected all metadata from {}'.format(url))
        return game_data

        
    def _load_assets(self, candidate, romPath, rom):
        
        url = 'https://gamefaqs.gamespot.com{}/images'.format(candidate['id'])
        assets_list = self._load_assets_from_url(url)
        
        log_debug('GamesFaqScraper:: Found {} assets for candidate #{}'.format(len(assets_list), candidate['id']))    
        return assets_list
        
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

  
# -----------------------------------------------------------------------------
# Arcade Database (for MAME) http://adb.arcadeitalia.net/
# -----------------------------------------------------------------------------   
class ArcadeDbScraper(Scraper): 

    def __init__(self, settings, launcher, fallbackScraper = None):

        scraper_settings = ScraperSettings.create_from_settings(settings)

        super(ArcadeDbScraper, self).__init__(scraper_settings, launcher, fallbackScraper)
        
    def getName(self):
        return 'Arcade Database'
        
    def supports_asset_type(self, asset_info):

        if asset_info.id == ASSET_FANART_ID:
            return False

        return True

    def _get_candidates(self, search_term, romPath, rom):
        
        platform = self.launcher.get_platform()
        
        log_debug('ArcadeDbScraper::_get_candidates() search_term         "{0}"'.format(search_term))
        log_debug('ArcadeDbScraper::_get_candidates() rom_base_noext      "{0}"'.format(romPath.getBaseNoExt()))
        log_debug('ArcadeDbScraper::_get_candidates() AEL platform        "{0}"'.format(platform))
        
        # >> Check if search term page data is in cache. If so it's a cache hit.
        candidate_from_cache = self._get_from_cache(search_term)
        
        if candidate_from_cache is not None:
            log_debug('Using a cached candidate')
            return [candidate_from_cache]       
    
        # >> MAME always uses rom_base_noext and ignores search_string.
        # >> Example game search: http://adb.arcadeitalia.net/dettaglio_mame.php?game_name=dino
        url = 'http://adb.arcadeitalia.net/dettaglio_mame.php?lang=en&game_name={0}'.format(romPath.getBaseNoExt())
        page_data = net_get_URL_oneline(url)

        # >> DEBUG
        # page_data_original = net_get_URL_original(url)
        # text_dump_str_to_file('arcadedb_search.txt', page_data_original)
        #     
       
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
            game['mame_name']    = romPath.getBaseNoExt()
            game_list.append(game)

        return game_list
        
    def _load_metadata(self, candidate, romPath, rom):

        # --- Get game page ---
        game_id_url = candidate['id'] 
        log_debug('ArcadeDbScraper::_load_metadata game_id_url "{0}"'.format(game_id_url))

        page_data = net_get_URL_oneline(game_id_url)
        # text_dump_str_to_file('arcadedb_get_metadata.txt', page_data)
        
        gamedata = self._new_gamedata_dic()

        # --- Process metadata ---
        # Example game page: http://adb.arcadeitalia.net/dettaglio_mame.php?lang=en&game_name=aliens
        #
        # --- Title ---
        # <div class="table_caption">Name: </div> <div class="table_value"> <span class="dettaglio">Aliens (World set 1)</span>
        fa_title = re.findall('<div id="game_description" class="invisibile">(.*?)</div>', page_data)
        if fa_title: gamedata['title'] = fa_title[0]

        # --- Genre/Category ---
        # <div class="table_caption">Category: </div> <div class="table_value"> <span class="dettaglio">Platform / Shooter Scrolling</span>
        fa_genre = re.findall('<div class="table_caption">Category: </div> <div class="table_value"> <span class="dettaglio">(.*?)</span>', page_data)
        if fa_genre: gamedata['genre'] = fa_genre[0]

        # --- Year ---
        # <div class="table_caption">Year: </div> <div class="table_value"> <span class="dettaglio">1990</span> <div id="inputid89"
        fa_year = re.findall('<div class="table_caption">Year: </div> <div class="table_value"> <span class="dettaglio">(.*?)</span>', page_data)
        if fa_year: gamedata['year'] = fa_year[0]

        # --- Developer ---
        # <div class="table_caption">Manufacturer: </div> <div class="table_value"> <span class="dettaglio">Konami</span> </div>
        fa_studio = re.findall('<div class="table_caption">Manufacturer: </div> <div class="table_value"> <span class="dettaglio">(.*?)</span> <div id="inputid88"', page_data)
        if fa_studio: gamedata['developer'] = fa_studio[0]
        
        # --- Plot ---
        # <div id="history_detail" class="extra_info_detail"><div class="history_title"></div>Aliens © 1990 Konami........&amp;id=63&amp;o=2</div>
        fa_plot = re.findall('<div id="history_detail" class="extra_info_detail"><div class=\'history_title\'></div>(.*?)</div>', page_data)
        if fa_plot: gamedata['plot'] = text_unescape_and_untag_HTML(fa_plot[0])

        return gamedata

    def _new_assetdata_dic(self):
        assetdata = {
            'type': '',
            'name': '',
            'url': '',
            'is_online': True,
            'is_on_page': False
        }
        return assetdata

# -----------------------------------------------------------------------------
# NULL scraper, does nothing
# -----------------------------------------------------------------------------
class NullScraper(Scraper):

    def __init__(self):
        super(NullScraper, self).__init__(None, None)
        
    def scrape(self, search_term, romPath, rom):
        return True

    def getName(self):
        return 'Empty scraper'
    
    def supports_asset_type(self, asset_info):
        return True

    def _get_candidates(self, search_term, romPath, rom):
        return []

    def _load_metadata(self, candidate, romPath, rom):
        return self._new_gamedata_dic()
    
    def _load_assets(self, candidate, romPath, rom):
        pass
    
    def _get_image_url_from_page(self, candidate, asset_info):        
        return ''

class CleanTitleScraper(Scraper):

    def __init__(self, settings, launcher):
        
        scraper_settings = ScraperSettings.create_from_settings(settings)
        scraper_settings.metadata_scraping_mode = 1
        scraper_settings.ignore_scraped_title = False

        super(CleanTitleScraper, self).__init__(scraper_settings, launcher)

    def getName(self):
        return 'Clean title only scraper'
    
    def supports_asset_type(self, asset_info):
        return False

    def _get_candidates(self, search_term, romPath, rom):
        games = []
        games.append({ 'id' : 'DUMMY', 'display_name' : 'CleanTitleDummy', 'order': 1 })
        return games
    
    def _load_metadata(self, candidate, romPath, rom):        
        
        game_data = self._new_gamedata_dic()
        if self.launcher.get_launcher_type() == OBJ_LAUNCHER_STEAM or self.launcher.get_launcher_type() == OBJ_LAUNCHER_NVGAMESTREAM:
            log_debug('CleanTitleScraper: Detected Steam or Stream launcher, leaving rom name untouched.')
            game_data['title'] = rom.get_name()
            return game_data

        log_debug('Only cleaning ROM name. Original: {}'.format(romPath.getBaseNoExt()))
        game_data['title'] = text_format_ROM_title(romPath.getBaseNoExt(), self.scraper_settings.scan_clean_tags)
        return game_data

    def _load_assets(self, candidate, romPath, rom):
        pass

    def _get_image_url_from_page(self, candidate, asset_info):        
        return candidate['url']
    
class NfoScraper(Scraper):
    
    def __init__(self, settings, launcher, fallbackScraper = None):
                
        scraper_settings = ScraperSettings.create_from_settings(settings)
        scraper_settings.metadata_scraping_mode = 1

        super(NfoScraper, self).__init__(scraper_settings, launcher, fallbackScraper)

    def getName(self):
        return 'NFO scraper'
    
    def supports_asset_type(self, asset_info):
        return False

    def _get_candidates(self, search_term, romPath, rom):

        NFO_file = romPath.changeExtension('nfo')
        games = []

        if NFO_file.exists():
            games.append({ 'id' : NFO_file.getPath(), 'display_name' : NFO_file.getBase(), 'order': 1 , 'file': NFO_file })
            log_debug('NFO file found "{0}"'.format(NFO_file.getPath()))
        else:
            log_debug('NFO file NOT found "{0}"'.format(NFO_file.getPath()))

        return games

    def _load_metadata(self, candidate, romPath, rom):        
        
        log_debug('Reading NFO file')
        # NOTE <platform> is chosen by AEL, never read from NFO files. Indeed, platform
        #      is a Launcher property, not a ROM property.
        game_data = fs_import_ROM_NFO_file_scanner(candidate['file'])
        return game_data

    def _load_assets(self, candidate, romPath, rom):
        pass
    
    def _get_image_url_from_page(self, candidate, asset_info):        
        return candidate['url']

class LocalAssetScraper(Scraper):
    
    def __init__(self, settings, launcher, fallbackScraper = None): 
                        
        scraper_settings = ScraperSettings.create_from_settings(settings)

        # --- Create a cache of assets ---
        # >> misc_add_file_cache() creates a set with all files in a given directory.
        # >> That set is stored in a function internal cache associated with the path.
        # >> Files in the cache can be searched with misc_search_file_cache()
        all_assets = g_assetFactory.get_all()
        for supported_asset in all_assets:
            asset_path = launcher.get_asset_path(supported_asset)
            if asset_path:
                misc_add_file_cache(asset_path)

        super(LocalAssetScraper, self).__init__(scraper_settings, launcher, fallbackScraper)
        
    def getName(self):
        return 'Local assets scraper'
    
    def supports_asset_type(self, asset_info):
        return True

    def _get_candidates(self, search_term, romPath, rom):

        games = []
        games.append({ 'id' : search_term, 'display_name' : 'LocalAssetsDummy', 'order': 1 })
        return games

    def _load_metadata(self, candidate, romPath, rom):      
        return None

    def _load_assets(self, candidate, romPath, rom):
        
        assets_list = []
        # ~~~~~ Search for local artwork/assets ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        rom_basename_noext = romPath.getBaseNoExt()
        
        all_assets = g_assetFactory.get_all()
        for supported_asset in all_assets:
            asset_path = self.launcher.get_asset_path(supported_asset)
            if not asset_path:
                log_verb('LocalAssetScraper._load_assets() Not supported  {0:<9}'.format(supported_asset.name))
                continue

            local_asset = misc_search_file_cache(asset_path, rom_basename_noext, supported_asset.exts)

            if not local_asset:
                log_verb('LocalAssetScraper._load_assets() Missing  {0:<9}'.format(supported_asset.name))
                continue
        
            log_verb('LocalAssetScraper._get_candidates() Found    {0:<9} "{1}"'.format(supported_asset.name, local_asset.getPath()))
            
            asset_data = self._new_assetdata_dic()

            asset_data['name']      = local_asset.getBase()
            asset_data['url']       = local_asset.getPath()
            asset_data['is_online'] = False
            asset_data['type']      = supported_asset
            
            assets_list.append(asset_data)
            
        return assets_list

    def _get_image_url_from_page(self, candidate, asset_info):        
        return candidate['url']


# -----------------------------------------------------------------------------
# TheGamesDB online scraper
# -----------------------------------------------------------------------------
class TheGamesDbScraper(Scraper): 

    def __init__(self, settings, launcher, fallbackScraper = None):

        self.publishers = None
        self.genres = None
        self.developers = None

        self.api_key = settings['thegamesdb_apikey']
        scraper_settings = ScraperSettings.create_from_settings(settings)

        super(TheGamesDbScraper, self).__init__(scraper_settings, launcher, fallbackScraper)
        
    def getName(self):
        return 'TheGamesDB'
    
    def supports_asset_type(self, asset_info):

        if asset_info.id == ASSET_CARTRIDGE_ID or asset_info.id == ASSET_FLYER_ID:
            return False

        return True

    def _get_candidates(self, search_term, romPath, rom):
        
        platform = self.launcher.get_platform()
        scraper_platform = AEL_platform_to_TheGamesDB(platform)
        
        log_debug('TheGamesDbScraper::_get_candidates() search_term         "{0}"'.format(search_term))
        log_debug('TheGamesDbScraper::_get_candidates() rom_base_noext      "{0}"'.format(romPath.getBaseNoExt()))
        log_debug('TheGamesDbScraper::_get_candidates() AEL platform        "{0}"'.format(platform))
        log_debug('TheGamesDbScraper::_get_candidates() TheGamesDB platform "{0}"'.format(scraper_platform))
        
        # >> Check if search term page data is in cache. If so it's a cache hit.
        candidate_from_cache = self._get_from_cache(search_term)
        
        if candidate_from_cache is not None:
            log_debug('Using a cached candidate')
            return [candidate_from_cache]

        game_list = []
        # >> quote_plus() will convert the spaces into '+'. Note that quote_plus() requires an
        # >> UTF-8 encoded string and does not work with Unicode strings.
        # added encoding 
        # https://stackoverflow.com/questions/22415345/using-pythons-urllib-quote-plus-on-utf-8-strings-with-safe-arguments
            
        search_string_encoded = quote_plus(search_term.encode('utf8'))
        url = 'https://api.thegamesdb.net/Games/ByGameName?apikey={}&name={}'.format(self.api_key, search_string_encoded)
            
        game_list = self._read_games_from_url(url, search_term, scraper_platform)
        
        if len(game_list) == 0:
            altered_search_term = self._cleanup_searchterm(search_term, romPath, rom)
            if altered_search_term != search_term:
                log_debug('TheGamesDbScraper::_get_candidates() No hits, trying again with altered search terms: {}'.format(altered_search_term))
                return self._get_candidates(altered_search_term, romPath, rom)

        # >> Order list based on score
        game_list.sort(key = lambda result: result['order'], reverse = True)

        return game_list
        
    def _load_metadata(self, candidate, romPath, rom):

        url = 'https://api.thegamesdb.net/Games/ByGameID?apikey={}&id={}&fields=players%2Cpublishers%2Cgenres%2Coverview%2Crating%2Cplatform%2Ccoop%2Cyoutube'.format(
                self.api_key, candidate['id'])
        
        log_debug('Get metadata from {}'.format(url))
        page_data = net_get_URL_as_json(url)
        online_data = page_data['data']['games'][0]
        
        game_data = self._new_gamedata_dic()

        # --- Parse game page data ---
        game_data['title']      = online_data['game_title'] if 'game_title' in online_data else '' 
        game_data['nplayers']   = online_data['players'] if 'players' in online_data else '' 
        game_data['esrb']       = online_data['rating'] if 'rating' in online_data else '' 
        game_data['plot']       = online_data['overview'] if 'overview' in online_data else '' 
        game_data['genre']      = self._get_genres(online_data['genres']) if 'genres' in online_data else '' 
        game_data['developer']  = self._get_developers(online_data['developers']) if 'developers' in online_data else '' 
        game_data['year']       = online_data['release_date'][:4] if 'release_date' in online_data and online_data['release_date'] is not None and online_data['release_date'] != '' else ''
        
        return game_data

    def _load_assets(self, candidate, romPath, rom):
        
        url = 'https://api.thegamesdb.net/Games/Images?apikey={}&games_id={}'.format(self.api_key, candidate['id'])
        asset_list = self._read_assets_from_url(url, candidate['id'])

        log_debug('Found {} assets for candidate #{}'.format(len(asset_list), candidate['id']))
        return asset_list

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
        
        page_data = net_get_URL_as_json(url)

        # >> If nothing is returned maybe a timeout happened. In this case, reset the cache.
        if page_data is None:
            self._reset_cache()

        games = page_data['data']['games']
        game_list = []
        for item in games:
            title    = item['game_title']
            platform = item['platform']
            display_name = '{} / {}'.format(title, platform)
            game = { 'id' : item['id'], 'display_name' : display_name, 'order': 1 }
            # Increase search score based on our own search
            if title.lower() == search_term.lower():                    game['order'] += 1
            if title.lower().find(search_term.lower()) != -1:           game['order'] += 1
            if scraper_platform > 0 and platform == scraper_platform:   game['order'] += 1

            game_list.append(game)

        next_url = page_data['pages']['next']
        if next_url is not None:
            game_list = game_list + self._read_games_from_url(next_url, search_term, scraper_platform)

        return game_list

    def _read_assets_from_url(self, url, candidate_id):
        
        log_debug('Get image data from {}'.format(url))
        
        page_data   = net_get_URL_as_json(url)
        online_data = page_data['data']['images'][str(candidate_id)]
        base_url    = page_data['data']['base_url']['original']
        
        assets_list = []
        # --- Parse images page data ---
        for image_data in online_data:
            asset_data = self._new_assetdata_dic()
            asset_kind = self._convert_to_asset_kind(image_data['type'], image_data['side'])

            if asset_kind is None:
                continue

            asset_info = g_assetFactory.get_asset_info(asset_kind)

            asset_data['type']  = asset_info
            asset_data['url']   = base_url + image_data['filename']
            asset_data['name']  = ' '.join(filter(None, [image_data['type'], image_data['side'], image_data['resolution']]))

            log_debug('TheGamesDbScraper:: found asset {}: {}'.format(asset_data['name'], asset_data['url']))
            assets_list.append(asset_data)
            
        next_url = page_data['pages']['next']
        if next_url is not None:
            assets_list = assets_list + self._read_assets_from_url(next_url, candidate_id)

        return assets_list

    asset_name_mapping = {
        'fanart' : ASSET_FANART_ID,
        'clearlogo': ASSET_CLEARLOGO_ID,
        'banner': ASSET_BANNER_ID,
        'boxartfront': ASSET_BOXFRONT_ID,
        'boxartback': ASSET_BOXBACK_ID,
        'screenshot': ASSET_SNAP_ID
    }

    def _convert_to_asset_kind(self, type, side):
        if side is not None:
            type = type + side

        asset_key = TheGamesDbScraper.asset_name_mapping[type]
        return asset_key

    def _cleanup_searchterm(self, search_term, rom_path, rom):
        altered_term = search_term.lower().strip()
        for ext in self.launcher.get_rom_extensions():
            altered_term = altered_term.replace(ext, '')

        return altered_term

    def _get_publishers(self, publisher_ids):
        
        if publisher_ids is None:
            return ''

        if self.publishers is None:
            log_debug('TheGamesDbScraper::No cached publishers. Retrieving from online.')
            self.publishers = {}
            url = 'https://api.thegamesdb.net/Publishers?apikey={}'.format(self.api_key)
            publishers_json = net_get_URL_as_json(url)
            for publisher_id in publishers_json['data']['publishers']:
                self.publishers[int(publisher_id)] = publishers_json['data']['publishers'][publisher_id]['name']

        publisher_names = []
        for publisher_id in publisher_ids:
            publisher_names.append(self.publishers[publisher_id])

        return ' / '.join(publisher_names)
    
    def _get_genres(self, genre_ids):

        if genre_ids is None:
            return ''

        if self.genres is None:
            log_debug('TheGamesDbScraper::No cached genres. Retrieving from online.')
            self.genres = {}
            url = 'https://api.thegamesdb.net/Genres?apikey={}'.format(self.api_key)
            genre_json = net_get_URL_as_json(url)
            for genre_id in genre_json['data']['genres']:
                self.genres[int(genre_id)] = genre_json['data']['genres'][genre_id]['name']

        genre_names = []
        for genre_id in genre_ids:
            genre_names.append(self.genres[genre_id])

        return ' / '.join(genre_names)
        
    def _get_developers(self, developer_ids):
        
        if developer_ids is None:
            return ''

        if self.developers is None:
            log_debug('TheGamesDbScraper::No cached developers. Retrieving from online.')
            self.developers = {}
            url = 'https://api.thegamesdb.net/Developers?apikey={}'.format(self.api_key)
            developers_json = net_get_URL_as_json(url)
            for developer_id in developers_json['data']['developers']:
                self.developers[int(developer_id)] = developers_json['data']['developers'][developer_id]['name']

        developer_names = []
        for developer_id in developer_ids:
            developer_names.append(self.developers[developer_id])

        return ' / '.join(developer_names)
    
    def _get_image_url_from_page(self, candidate, asset_info):        
        return candidate['url']


# -----------------------------------------------------------------------------
# MobyGames http://www.mobygames.com
# -----------------------------------------------------------------------------
class MobyGamesScraper(Scraper): 
        
    def __init__(self, settings, launcher, fallbackScraper = None):

        self.api_key = settings['mobygames_apikey']
        scraper_settings = ScraperSettings.create_from_settings(settings)

        self.last_http_call = datetime.now()

        super(MobyGamesScraper, self).__init__(scraper_settings, launcher, fallbackScraper)
        
    def getName(self):
        return 'MobyGames'    
    
    def supports_asset_type(self, asset_info):

        if asset_info.id == ASSET_FANART_ID or asset_info.id == ASSET_BANNER_ID or asset_info.id == ASSET_CLEARLOGO_ID or asset_info.id == ASSET_FLYER_ID:
            return False

        return True

    def _get_candidates(self, search_term, romPath, rom):
        
        platform = self.launcher.get_platform()
        scraper_platform = AEL_platform_to_MobyGames(platform)
        
        log_debug('MobyGamesScraper::_get_candidates() search_term         "{0}"'.format(search_term))
        log_debug('MobyGamesScraper::_get_candidates() rom_base_noext      "{0}"'.format(romPath.getBaseNoExt()))
        log_debug('MobyGamesScraper::_get_candidates() AEL platform        "{0}"'.format(platform))
        log_debug('MobyGamesScraper::_get_candidates() MobyGames platform  "{0}"'.format(scraper_platform))
        
        # >> Check if search term page data is in cache. If so it's a cache hit.
        candidate_from_cache = self._get_from_cache(search_term)
        
        if candidate_from_cache is not None:
            return [candidate_from_cache]

        game_list = []            
        search_string_encoded = quote_plus(search_term.encode('utf8'))
        url = 'https://api.mobygames.com/v1/games?api_key={}&format=brief&title={}&platform={}'.format(self.api_key, search_string_encoded, scraper_platform)
            
        game_list = self._read_games_from_url(url, search_term, scraper_platform)
        
        # >> Order list based on score
        game_list.sort(key = lambda result: result['order'], reverse = True)

        return game_list
        
    def _read_games_from_url(self, url, search_term, scraper_platform):
        
        self._do_toomanyrequests_check()
            
        page_data = net_get_URL_as_json(url)
        self.last_http_call = datetime.now()

        # >> If nothing is returned maybe a timeout happened. In this case, reset the cache.
        if page_data is None:
            self._reset_cache()

        games = page_data['games']
        game_list = []
        for item in games:
            title    = item['title']
            game = { 'id' : item['game_id'], 'display_name' : title,'order': 1 }
            # Increase search score based on our own search
            if title.lower() == search_term.lower():                    game['order'] += 1
            if title.lower().find(search_term.lower()) != -1:           game['order'] += 1
            
            game_list.append(game)

        return game_list

    def _load_metadata(self, candidate, romPath, rom):

        url = 'https://api.mobygames.com/v1/games/{}?api_key={}'.format(candidate['id'], self.api_key)
                
        self._do_toomanyrequests_check()
        
        log_debug('Get metadata from {}'.format(url))
        online_data = net_get_URL_as_json(url)

        self.last_http_call = datetime.now()
        
        platform = self.launcher.get_platform()
        scraper_platform = AEL_platform_to_MobyGames(platform)
        
        game_data = self._new_gamedata_dic()

        # --- Parse game page data ---
        game_data['title']      = online_data['title'] if 'title' in online_data else '' 
        game_data['plot']       = online_data['description'] if 'description' in online_data else '' 
        game_data['genre']      = self._get_genres(online_data['genres']) if 'genres' in online_data else '' 
        game_data['year']       = self._get_year_by_platform(online_data['platforms'], scraper_platform)

        return game_data

    def _get_genres(self, genre_data):

        genre_names = []
        for genre in genre_data:
            genre_names.append(genre['genre_name'])

        return ' / '.join(genre_names)
        
    def _get_year_by_platform(self, platform_data, platform_id):
        
        if len(platform_data) == 0:
            return ''
        
        year_data = None
        for platform in platform_data:
            if platform['platform_id'] == int(platform_id):
                year_data = platform['first_release_date']
                break

        if year_data is None:
            year_data = platform_data[0]['first_release_date']

        return year_data[:4]

    def _load_assets(self, candidate,  romPath, rom):
        
        platform = self.launcher.get_platform()
        scraper_platform = AEL_platform_to_MobyGames(platform)
                
        #only snaps and covers are supported as assets
        snap_assets = self._load_snap_assets(candidate, scraper_platform)
        cover_assets = self._load_cover_assets(candidate, scraper_platform)
        assets_list = snap_assets + cover_assets

        log_debug('A total of {} assets found for candidate #{}'.format(len(assets_list), candidate['id']))
        return assets_list


    def _load_snap_assets(self, candidate, platform_id):

        url = 'https://api.mobygames.com/v1/games/{}/platforms/{}/screenshots?api_key={}'.format(candidate['id'], platform_id, self.api_key)        
        log_debug('Get screenshot image data from {}'.format(url))
        
        self._do_toomanyrequests_check()

        page_data   = net_get_URL_as_json(url)
        online_data = page_data['screenshots']

        asset_snap = g_assetFactory.get_asset_info(ASSET_SNAP_ID)
        assets_list = []
        # --- Parse images page data ---
        for image_data in online_data:
            asset_data = self._new_assetdata_dic()

            asset_data['type']  = asset_snap
            asset_data['url']   = image_data['image']
            asset_data['name']  = image_data['caption']
            
            log_debug('MobyGamesScraper:: found asset {} @ {}'.format(asset_data['name'], asset_data['url']))
            assets_list.append(asset_data)

        log_debug('Found {} snap assets for candidate #{}'.format(len(assets_list), candidate['id']))    
        return assets_list

    def _load_cover_assets(self, candidate, platform_id):

        url = 'https://api.mobygames.com/v1/games/{}/platforms/{}/covers?api_key={}'.format(candidate['id'], platform_id, self.api_key)        
        log_debug('Get cover image data from {}'.format(url))
        
        self._do_toomanyrequests_check()

        page_data   = net_get_URL_as_json(url)
        online_data = page_data['cover_groups']

        assets_list = []
        # --- Parse images page data ---
        for group_data in online_data:

            country_names = ' / '.join(group_data['countries'])

            for image_data in group_data['covers']:
                asset_data = self._new_assetdata_dic()
                
                asset_type  = image_data['scan_of']
                asset_id    = MobyGamesScraper.asset_name_mapping[asset_type.lower()]
                asset_info  = g_assetFactory.get_asset_info(asset_id)

                if asset_info is None:
                    log_debug('Unsupported asset kind for {}'.format(asset_data['name']))
                    continue

                asset_data['type']  = asset_info
                asset_data['url']   = image_data['image']
                asset_data['name']  = '{} - {} ({})'.format(image_data['scan_of'], image_data['description'], country_names)

                log_debug('MobyGamesScraper:: found asset {} @ {}'.format(asset_data['name'], asset_data['url']))
                assets_list.append(asset_data)

        log_debug('Found {} cover assets for candidate #{}'.format(len(assets_list), candidate['id']))    
        return assets_list

    asset_name_mapping = {
        'media' : ASSET_CARTRIDGE_ID,
        'manual': ASSET_MANUAL_ID,
        'front cover': ASSET_BOXFRONT_ID,
        'back cover': ASSET_BOXBACK_ID,
        'spine/sides': 0 # not supported by AEL?
    }
        
    def _get_image_url_from_page(self, candidate, asset_info):        
        return candidate['url']

    def _do_toomanyrequests_check(self):
        # make sure we dont go over the TooManyRequests limit of 1 second
        now = datetime.now()
        if (now-self.last_http_call).total_seconds() < 1:
            time.sleep(1)

        pass

# -----------------------------------------------------------------------------
# GameFAQs online scraper
# -----------------------------------------------------------------------------
class GameFaqScraper(Scraper):
         
    def __init__(self, settings, launcher, fallbackScraper = None):

        scraper_settings = ScraperSettings.create_from_settings(settings)
        super(GameFaqScraper, self).__init__(scraper_settings, launcher, fallbackScraper)
        
    def getName(self):
        return 'GameFaq'
    
    def supports_asset_type(self, asset_info):

        if asset_info.id == ASSET_FANART_ID or asset_info.id == ASSET_BANNER_ID or asset_info.id == ASSET_CLEARLOGO_ID or asset_info.id == ASSET_FLYER_ID or asset_info.id == ASSET_CARTRIDGE_ID:
            return False

        return True

    def _get_candidates(self, search_term, romPath, rom):
               
        platform = self.launcher.get_platform()
        scraper_platform = AEL_platform_to_GameFAQs(platform)
        
        log_debug('GamesFaqScraper::_get_candidates() search_term         "{0}"'.format(search_term))
        log_debug('GamesFaqScraper::_get_candidates() rom_base_noext      "{0}"'.format(romPath.getBaseNoExt()))
        log_debug('GamesFaqScraper::_get_candidates() AEL platform        "{0}"'.format(platform))
        log_debug('GamesFaqScraper::_get_candidates() GameFAQs platform   "{0}"'.format(scraper_platform))
        
        # >> Check if search term page data is in cache. If so it's a cache hit.
        candidate_from_cache = self._get_from_cache(search_term)
        
        if candidate_from_cache is not None:
            log_debug('Using a cached candidate')
            return [candidate_from_cache]

        game_list = []                        
        game_list = self._get_candidates_from_page(search_term, scraper_platform)
        
        # >> Order list based on score
        game_list.sort(key = lambda result: result['order'], reverse = True)

        return game_list

    def _get_candidates_from_page(self, search_term, platform, url = None, no_platform=False):
        
        search_params = urlencode({'game': search_term}) if no_platform else urlencode({'game': search_term, 'platform': platform})
        if url is None:
            url = 'https://gamefaqs.gamespot.com/search_advanced'
            page_data = net_post_URL_original(url, search_params)
        else:
            page_data = net_get_URL_original(url)
        
        # <div class="sr_row"><div class="sr_cell sr_platform">NES</div><div class="sr_cell sr_title"><a href="/nes/578318-castlevania">Castlevania</a></div><div class="sr_cell sr_release">1987</div>
        regex_results = re.findall(r'<div class="sr_cell sr_platform">(.*?)</div>\s*<div class="sr_cell sr_title"><a href="(.*?)">(.*?)</a>', page_data, re.MULTILINE)
        game_list = []
        for result in regex_results:
            game = {}
            game_name            = text_unescape_HTML(result[2])
            game_platform        = result[0]
            game['id']           = result[1]
            game['display_name'] = game_name + ' / ' + game_platform.capitalize()
            game['game_name']    = game_name # Additional GameFAQs scraper field
            game['order']        = 1         # Additional GameFAQs scraper field
        
            if game_name == 'Game':
                continue

            # Increase search score based on our own search
            # In the future use an scoring algortihm based on Levenshtein Distance
            title = game_name
            if title.lower() == search_term.lower():            game['order'] += 1
            if title.lower().find(search_term.lower()) != -1:   game['order'] += 1
            if len(platform)> 0 and game_platform == platform: game['order'] += 1

            game_list.append(game)

        if len(game_list) == 0 and not no_platform:
            return self._get_candidates_from_page(search_term, platform, no_platform=True)

        next_page_result = re.findall('<li><a href="(\S*?)">Next Page\s<i', page_data, re.MULTILINE)
        if len(next_page_result) > 0:
            link = next_page_result[0].replace('&amp;', '&')
            new_url = 'https://gamefaqs.gamespot.com' + link
            game_list = game_list + self._get_candidates_from_page(search_term, no_platform, new_url)

        game_list.sort(key = lambda result: result['order'], reverse = True)
        
        return game_list
            
    def _load_metadata(self, candidate, romPath, rom):
        
        url = 'https://gamefaqs.gamespot.com{}'.format(candidate['id'])
        
        log_debug('GamesFaqScraper::_load_metadata() Get metadata from {}'.format(url))
        page_data = net_get_URL_oneline(url)

        # Parse data
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

        game_plot = re.findall('Description</h2></div><div class="body game_desc"><div class="desc">(.*?)</div>', page_data)
        
        game_data = self._new_gamedata_dic()
            
        # --- Set game page data ---
        game_data['title']      = candidate['game_name'] 
        game_data['plot']       = text_unescape_and_untag_HTML(game_plot[0]) if game_plot else ''        
        game_data['genre']      = game_genre[0][3] if game_genre else '' 
        game_data['year']       = game_release[0][1][-4:] if game_release else ''
        game_data['developer']  = game_developer

        log_debug('GamesFaqScraper::_load_metadata() Collected all metadata from {}'.format(url))
        return game_data

        
    def _load_assets(self, candidate, romPath, rom):
        
        url = 'https://gamefaqs.gamespot.com{}/images'.format(candidate['id'])
        assets_list = self._load_assets_from_url(url)
        
        log_debug('GamesFaqScraper:: Found {} assets for candidate #{}'.format(len(assets_list), candidate['id']))    
        return assets_list
        
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

  
# -----------------------------------------------------------------------------
# Arcade Database (for MAME) http://adb.arcadeitalia.net/
# -----------------------------------------------------------------------------   
class ArcadeDbScraper(Scraper): 

    def __init__(self, settings, launcher, fallbackScraper = None):

        scraper_settings = ScraperSettings.create_from_settings(settings)

        super(ArcadeDbScraper, self).__init__(scraper_settings, launcher, fallbackScraper)
        
    def getName(self):
        return 'Arcade Database'
        
    def supports_asset_type(self, asset_info):

        if asset_info.id == ASSET_FANART_ID:
            return False

        return True

    def _get_candidates(self, search_term, romPath, rom):
        
        platform = self.launcher.get_platform()
        
        log_debug('ArcadeDbScraper::_get_candidates() search_term         "{0}"'.format(search_term))
        log_debug('ArcadeDbScraper::_get_candidates() rom_base_noext      "{0}"'.format(romPath.getBaseNoExt()))
        log_debug('ArcadeDbScraper::_get_candidates() AEL platform        "{0}"'.format(platform))
        
        # >> Check if search term page data is in cache. If so it's a cache hit.
        candidate_from_cache = self._get_from_cache(search_term)
        
        if candidate_from_cache is not None:
            log_debug('Using a cached candidate')
            return [candidate_from_cache]       
    
        # >> MAME always uses rom_base_noext and ignores search_string.
        # >> Example game search: http://adb.arcadeitalia.net/dettaglio_mame.php?game_name=dino
        url = 'http://adb.arcadeitalia.net/dettaglio_mame.php?lang=en&game_name={0}'.format(romPath.getBaseNoExt())
        page_data = net_get_URL_oneline(url)

        # >> DEBUG
        # page_data_original = net_get_URL_original(url)
        # text_dump_str_to_file('arcadedb_search.txt', page_data_original)
        #     
       
        # --- Check if game was found ---
        game_list = []
        m = re.findall('<h2>Error: Game not found</h2>', page_data)
        if m:
            log_debug('Scraper_ArcadeDB::get_search Game NOT found "{0}"'.format(romPath.getBaseNoExt()))
            log_debug('Scraper_ArcadeDB::get_search Returning empty game_list')
        else:
            # >> Example URL: http://adb.arcadeitalia.net/dettaglio_mame.php?game_name=dino&lang=en
            # >> <div id="game_description" class="invisibile">Cadillacs and Dinosaurs (World 930201)</div>
            m_title = re.findall('<div id="game_description" class="invisibile">(.+?)</div>', page_data)
            if not m_title: return game_list
            game = {}
            game['display_name'] = m_title[0]
            game['id']           = url
            game['mame_name']    = romPath.getBaseNoExt()
            game_list.append(game)

        return game_list
        
    def _load_metadata(self, candidate, romPath, rom):

        # --- Get game page ---
        game_id_url = candidate['id'] 
        log_debug('ArcadeDbScraper::_load_metadata game_id_url "{0}"'.format(game_id_url))

        page_data = net_get_URL_oneline(game_id_url)
        # text_dump_str_to_file('arcadedb_get_metadata.txt', page_data)
        
        gamedata = self._new_gamedata_dic()

        # --- Process metadata ---
        # Example game page: http://adb.arcadeitalia.net/dettaglio_mame.php?lang=en&game_name=aliens
        #
        # --- Title ---
        # <div class="table_caption">Name: </div> <div class="table_value"> <span class="dettaglio">Aliens (World set 1)</span>
        fa_title = re.findall('<div id="game_description" class="invisibile">(.*?)</div>', page_data)
        if fa_title: gamedata['title'] = fa_title[0]

        # --- Genre/Category ---
        # <div class="table_caption">Category: </div> <div class="table_value"> <span class="dettaglio">Platform / Shooter Scrolling</span>
        fa_genre = re.findall('<div class="table_caption">Category: </div> <div class="table_value"> <span class="dettaglio">(.*?)</span>', page_data)
        if fa_genre: gamedata['genre'] = fa_genre[0]

        # --- Year ---
        # <div class="table_caption">Year: </div> <div class="table_value"> <span class="dettaglio">1990</span> <div id="inputid89"
        fa_year = re.findall('<div class="table_caption">Year: </div> <div class="table_value"> <span class="dettaglio">(.*?)</span>', page_data)
        if fa_year: gamedata['year'] = fa_year[0]

        # --- Developer ---
        # <div class="table_caption">Manufacturer: </div> <div class="table_value"> <span class="dettaglio">Konami</span> </div>
        fa_studio = re.findall('<div class="table_caption">Manufacturer: </div> <div class="table_value"> <span class="dettaglio">(.*?)</span> <div id="inputid88"', page_data)
        if fa_studio: gamedata['developer'] = fa_studio[0]
        
        # --- Plot ---
        # <div id="history_detail" class="extra_info_detail"><div class="history_title"></div>Aliens © 1990 Konami........&amp;id=63&amp;o=2</div>
        fa_plot = re.findall('<div id="history_detail" class="extra_info_detail"><div class=\'history_title\'></div>(.*?)</div>', page_data)
        if fa_plot: gamedata['plot'] = text_unescape_and_untag_HTML(fa_plot[0])

        return gamedata

    def _load_assets(self, candidate, romPath, rom):
                
        assets_list = []

        #
        # <li class="mostra_archivio cursor_pointer" title="Show all images, videos and documents archived for this game"> 
        # <a href="javascript:void mostra_media_archivio();"> <span>Other files</span> </a>
        #
        # Function void mostra_media_archivio(); is in file http://adb.arcadeitalia.net/dettaglio_mame.js?release=87
        #
        # AJAX call >> view-source:http://adb.arcadeitalia.net/dettaglio_mame.php?ajax=mostra_media_archivio&game_name=toki
        # AJAX returns HTML code:
        # <xml><html>
        # <content1 id='elenco_anteprime' type='html'>%26lt%3Bli%20class......gt%3B</content1>
        # </html><result></result><message><code></code><title></title><type></type><text></text></message></xml>
        #
        # pprint.pprint(game)
        
        log_debug('asset_ArcadeDB::_load_assets game ID "{0}"'.format(candidate['id']))
        log_debug('asset_ArcadeDB::_load_assets name    "{0}"'.format(candidate['mame_name']))
        
        AJAX_URL  = 'http://adb.arcadeitalia.net/dettaglio_mame.php?ajax=mostra_media_archivio&game_name={0}'.format(candidate['mame_name'])
        page_data  = net_get_URL_oneline(AJAX_URL)
        rcode     = re.findall('<xml><html><content1 id=\'elenco_anteprime\' type=\'html\'>(.*?)</content1></html>', page_data)
        if not rcode: return assets_list

        raw_HTML     = rcode[0]
        decoded_HTML = text_decode_HTML(raw_HTML)
        escaped_HTML = text_unescape_HTML(decoded_HTML)
        # text_dump_str_to_file('ArcadeDB-get_images-AJAX-dino-raw.txt', raw_HTML)
        # text_dump_str_to_file('ArcadeDB-get_images-AJAX-dino-decoded.txt', decoded_HTML)
        # text_dump_str_to_file('ArcadeDB-get_images-AJAX-dino-escaped.txt', escaped_HTML)

        #
        # <li class='cursor_pointer' tag="Boss-0" onclick="javascript:set_media(this,'Boss','current','4','0');"  title="Boss" ><div>
        # <img media_id='1' class='colorbox_image' src='http://adb.arcadeitalia.net/media/mame.current/bosses/small/toki.png'
        #      src_full="http://adb.arcadeitalia.net/media/mame.current/bosses/toki.png"></img>
        # </div><span>Boss</span></li>
        # <li class='cursor_pointer' tag="Cabinet-0" onclick="javascript:set_media(this,'Cabinet','current','5','0');"  title="Cabinet" ><div>
        # <img media_id='2' class='colorbox_image' src='http://adb.arcadeitalia.net/media/mame.current/cabinets/small/toki.png'
        #      src_full="http://adb.arcadeitalia.net/media/mame.current/cabinets/toki.png"></img>
        # </div><span>Cabinet</span></li>
        # .....
        # <li class='cursor_pointer'  title="Manuale" >
        # <a href="http://adb.arcadeitalia.net/download_file.php?tipo=mame_current&amp;codice=toki&amp;entity=manual&amp;oper=view&amp;filler=toki.pdf" target='_blank'>
        # <img src='http://adb.arcadeitalia.net/media/mame.current/manuals/small/toki.png'></img><br/><span>Manuale</span></a></li>
        #

        # ASSET_TITLE:
        cover_index = 1
        asset_type = g_assetFactory.get_asset_info(ASSET_TITLE_ID)
        rlist = re.findall(
            '<li class=\'cursor_pointer\' tag="Titolo-[0-9]" onclick="(.*?)"  title="(.*?)" >' +
            '<div><img media_id=\'(.*?)\' class=\'colorbox_image\' src=\'(.*?)\' src_full="(.*?)"></img></div>', escaped_HTML)
        # pprint.pprint(rlist)
        for index, rtuple in enumerate(rlist):
            art_URL = rtuple[4]
            log_debug('asset_ArcadeDB::get_images() Adding Title #{0:02d}'.format(cover_index))
            
            asset_data = self._new_assetdata_dic()
            asset_data['name']  = 'Title #{0:02d}'.format(cover_index)
            asset_data['type']  = asset_type
            asset_data['url']   = art_URL
            
            assets_list.append(asset_data)
            cover_index += 1

        # ASSET_SNAP:
        cover_index = 1
        asset_type = g_assetFactory.get_asset_info(ASSET_SNAP_ID)
        rlist = re.findall(
            '<li class=\'cursor_pointer\' tag="Gioco-[0-9]" onclick="(.*?)"  title="(.*?)" >' +
            '<div><img media_id=\'(.*?)\' class=\'colorbox_image\' src=\'(.*?)\' src_full="(.*?)"></img></div>', escaped_HTML)
        for index, rtuple in enumerate(rlist):
            art_URL = rtuple[4]
            log_debug('asset_ArcadeDB::get_images() Adding Snap #{0:02d}'.format(cover_index))

            asset_data = self._new_assetdata_dic()
            asset_data['name']  = 'Snap #{0:02d}'.format(cover_index)
            asset_data['type']  = asset_type
            asset_data['url']   = art_URL
            
            assets_list.append(asset_data)
            cover_index += 1

        # ASSET_BANNER:
        # Banner is Marquee
        cover_index = 1
        asset_type = g_assetFactory.get_asset_info(ASSET_BANNER_ID)
        rlist = re.findall(
            '<li class=\'cursor_pointer\' tag="Marquee-[0-9]" onclick="(.*?)"  title="(.*?)" >' +
            '<div><img media_id=\'(.*?)\' class=\'colorbox_image\' src=\'(.*?)\' src_full="(.*?)"></img></div>', escaped_HTML)
        for index, rtuple in enumerate(rlist):
            art_URL = rtuple[4]
            log_debug('asset_ArcadeDB::get_images() Adding Banner/Marquee #{0:02d}'.format(cover_index))
            
            asset_data = self._new_assetdata_dic()
            asset_data['name']  = 'Banner/Marquee #{0:02d}'.format(cover_index)
            asset_data['type']  = asset_type
            asset_data['url']   = art_URL

            assets_list.append(asset_data)
            cover_index += 1
            
        # ASSET_CLEARLOGO:
        # Clearlogo is called Decal in ArcadeDB
        cover_index = 1
        asset_type = g_assetFactory.get_asset_info(ASSET_CLEARLOGO_ID)
        rlist = re.findall(
            '<li class=\'cursor_pointer\' tag="Scritta-[0-9]" onclick="(.*?)"  title="(.*?)" >' +
            '<div><img media_id=\'(.*?)\' class=\'colorbox_image\' src=\'(.*?)\' src_full="(.*?)"></img></div>', escaped_HTML)
        for index, rtuple in enumerate(rlist):
            art_URL = rtuple[4]
            log_debug('asset_ArcadeDB::get_images() Adding Clearlogo #{0:02d}'.format(cover_index))
            
            asset_data = self._new_assetdata_dic()
            asset_data['name']  = 'Clearlogo #{0:02d}'.format(cover_index)
            asset_data['type']  = asset_type
            asset_data['url']   = art_URL

            assets_list.append(asset_data)
            cover_index += 1

        # ASSET_BOXFRONT
        # Boxfront is Cabinet
        cover_index = 1
        asset_type = g_assetFactory.get_asset_info(ASSET_BOXFRONT_ID)
        rlist = re.findall(
            '<li class=\'cursor_pointer\' tag="Cabinet-[0-9]" onclick="(.*?)"  title="(.*?)" >' +
            '<div><img media_id=\'(.*?)\' class=\'colorbox_image\' src=\'(.*?)\' src_full="(.*?)"></img></div>', escaped_HTML)
        for index, rtuple in enumerate(rlist):
            art_URL = rtuple[4]
            log_debug('asset_ArcadeDB::get_images() Adding Boxfront/Cabinet #{0:02d}'.format(cover_index))
            
            asset_data = self._new_assetdata_dic()
            asset_data['name']  = 'Boxfront/Cabinet #{0:02d}'.format(cover_index)
            asset_data['type']  = asset_type
            asset_data['url']   = art_URL

            assets_list.append(asset_data)
            cover_index += 1

        # ASSET_BOXBACK
        # Boxback is ControlPanel
        cover_index = 1
        asset_type = g_assetFactory.get_asset_info(ASSET_BOXBACK_ID)
        rlist = re.findall(
            '<li class=\'cursor_pointer\' tag="CPO-[0-9]" onclick="(.*?)"  title="(.*?)" >' +
            '<div><img media_id=\'(.*?)\' class=\'colorbox_image\' src=\'(.*?)\' src_full="(.*?)"></img></div>', escaped_HTML)
        for index, rtuple in enumerate(rlist):
            art_URL = rtuple[4]
            log_debug('asset_ArcadeDB::get_images() Adding Boxback/CPanel #{0:02d}'.format(cover_index))
                
            asset_data = self._new_assetdata_dic()
            asset_data['name']  = 'Boxback/CPanel #{0:02d}'.format(cover_index)
            asset_data['type']  = asset_type
            asset_data['url']   = art_URL

            assets_list.append(asset_data)
            cover_index += 1

        # ASSET_CARTRIDGE
        # Cartridge is PCB
        cover_index = 1
        asset_type = g_assetFactory.get_asset_info(ASSET_CARTRIDGE_ID)        
        rlist = re.findall(
            '<li class=\'cursor_pointer\' tag="PCB-[0-9]" onclick="(.*?)"  title="(.*?)" >' +
            '<div><img media_id=\'(.*?)\' class=\'colorbox_image\' src=\'(.*?)\' src_full="(.*?)"></img></div>', escaped_HTML)
        for index, rtuple in enumerate(rlist):
            img_name = 'Cartridge/PCB #{0:02d}'.format(cover_index)
            art_URL = rtuple[4]
            log_debug('asset_ArcadeDB::get_images() Adding Cartridge/PCB #{0:02d}'.format(cover_index))
            
            asset_data = self._new_assetdata_dic()
            asset_data['name']  = 'Cartridge/PCB #{0:02d}'.format(cover_index)
            asset_data['type']  = asset_type
            asset_data['url']   = art_URL

            assets_list.append(asset_data)
            cover_index += 1
                
        # ASSET_FLYER
        cover_index = 1
        asset_type = g_assetFactory.get_asset_info(ASSET_FLYER_ID)
        rlist = re.findall(
            '<li class=\'cursor_pointer\' tag="Volantino-[0-9]" onclick="(.*?)"  title="(.*?)" >' +
            '<div><img media_id=\'(.*?)\' class=\'colorbox_image\' src=\'(.*?)\' src_full="(.*?)"></img></div>', escaped_HTML)
        for index, rtuple in enumerate(rlist):
            img_name = 'Flyer #{0:02d}'.format(cover_index)
            art_URL = rtuple[4]
            log_debug('asset_ArcadeDB::get_images() Adding Flyer #{0:02d}'.format(cover_index))
            
            asset_data = self._new_assetdata_dic()
            asset_data['name']  = 'Flyer #{0:02d}'.format(cover_index)
            asset_data['type']  = asset_type
            asset_data['url']   = art_URL

            assets_list.append(asset_data)
            cover_index += 1

        return assets_list

    def _get_image_url_from_page(self, candidate, asset_info):        
        return candidate['url']