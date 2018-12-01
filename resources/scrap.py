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
import abc
import datetime, time

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

class ScraperFactory(KodiProgressDialogStrategy):
    def __init__(self, settings, PATHS):
        self.settings = settings
        self.addon_dir = PATHS.ADDON_DATA_DIR
    
        super(ScraperFactory, self).__init__()
        
    def create(self, launcher):
        
        scan_metadata_policy    = self.settings['scan_metadata_policy']
        scan_asset_policy       = self.settings['scan_asset_policy']

        scrapers = []


        metadata_scraper = self._get_metadata_scraper(scan_metadata_policy, launcher)
        scrapers.append(metadata_scraper)

        if self._hasDuplicateArtworkDirs(launcher):
            return None

        self._startProgressPhase('Advanced Emulator Launcher', 'Preparing scrapers ...')
        
        # --- Assets/artwork stuff ----------------------------------------------------------------
        # ~~~ Check asset dirs and disable scanning for unset dirs ~~~
        unconfigured_name_list = []
        asset_factory = AssetInfoFactory.create()
        rom_asset_infos = asset_factory.get_asset_kinds_for_roms()
        i = 0;

        for asset_info in rom_asset_infos:
            
            asset_path = launcher.get_asset_path(asset_info)
            if not asset_path:
                unconfigured_name_list.append(asset_info.name)
                log_verb('ScraperFactory.create() {0:<9} path unconfigured'.format(asset_info.name))
            else:
                log_debug('ScraperFactory.create() {0:<9} path configured'.format(asset_info.name))
                asset_scraper = self._get_asset_scraper(scan_asset_policy, asset_info.kind, asset_info, launcher)
                
                if asset_scraper:
                    scrapers.append(asset_scraper)
                
            self._updateProgress((100*i)/len(ROM_ASSET_LIST))
            i += 1

        self._endProgressPhase()
        
        if unconfigured_name_list:
            unconfigured_asset_srt = ', '.join(unconfigured_name_list)
            kodi_dialog_OK('Assets directories not set: {0}. '.format(unconfigured_asset_srt) +
                           'Asset scanner will be disabled for this/those.')
        return scrapers
     
    # ~~~ Ensure there is no duplicate asset dirs ~~~
    # >> Abort scanning of assets if duplicates found
    def _hasDuplicateArtworkDirs(self, launcher):
        
        log_info('Checking for duplicated artwork directories ...')
        duplicated_name_list = launcher.get_duplicated_asset_dirs()

        if duplicated_name_list:
            duplicated_asset_srt = ', '.join(duplicated_name_list)
            log_info('Duplicated asset dirs: {0}'.format(duplicated_asset_srt))
            kodi_dialog_OK('Duplicated asset directories: {0}. '.format(duplicated_asset_srt) +
                           'Change asset directories before continuing.')
            return True
        
        log_info('No duplicated asset dirs found')
        return False        

    # >> Determine metadata action based on configured metadata policy
    # >> scan_metadata_policy -> values="None|NFO Files|NFO Files + Scrapers|Scrapers"    
    def _get_metadata_scraper(self, scan_metadata_policy, launcher):

        cleanTitleScraper = CleanTitleScraper(self.settings, launcher)

        if scan_metadata_policy == 0:
            log_verb('Metadata policy: No NFO reading, no scraper. Only cleaning ROM name.')
            return cleanTitleScraper

        elif scan_metadata_policy == 1:
            log_verb('Metadata policy: Read NFO file only | Scraper OFF')
            return NfoScraper(self.settings, launcher, cleanTitleScraper)

        elif scan_metadata_policy == 2:
            log_verb('Metadata policy: Read NFO file ON, if not NFO then Scraper ON')
            
            # --- Metadata scraper ---
            scraper_index = self.settings['scraper_metadata']

            if scraper_index == 1:
                onlineScraper = TheGamesDbScraper(self.settings, launcher, True, [], cleanTitleScraper)
                log_verb('Loaded metadata scraper "{0}"'.format(onlineScraper.getName()))
            else:
                scraper_implementation = scrapers_metadata[scraper_index]
                scraper_implementation.set_addon_dir(self.addon_dir.getPath())
                log_verb('Loaded metadata scraper "{0}"'.format(scraper_implementation.name))
                onlineScraper = OnlineMetadataScraper(scraper_implementation, self.settings, launcher, cleanTitleScraper)
            
            return NfoScraper(self.settings, launcher, onlineScraper)


        elif scan_metadata_policy == 3:
            log_verb('Metadata policy: Read NFO file OFF | Scraper ON')
            log_verb('Metadata policy: Forced scraper ON')
            scraper_index = self.settings['scraper_metadata']

            if scraper_index == 1:
                onlineScraper = TheGamesDbScraper(self.settings, launcher, True, [], cleanTitleScraper)
                log_verb('Loaded metadata scraper "{0}"'.format(onlineScraper.getName()))
                return onlineScraper
            else:
                scraper_implementation = scrapers_metadata[scraper_index]
                scraper_implementation.set_addon_dir(self.addon_dir.getPath())

                log_verb('Loaded metadata scraper "{0}"'.format(scraper_implementation.name))

                return OnlineMetadataScraper(scraper_implementation, self.settings, launcher, cleanTitleScraper)
        
        log_error('Invalid scan_metadata_policy value = {0}. Fallback on clean title only'.format(scan_metadata_policy))
        return cleanTitleScraper

    def _get_asset_scraper(self, scan_asset_policy, asset_kind, asset_info, launcher):
                
        # >> Scrapers for MAME platform are different than rest of the platforms
        scraper_implementation = getScraper(asset_kind, self.settings, launcher.get_platform() == 'MAME')
        
        # --- If scraper does not support particular asset return inmediately ---
        if scraper_implementation and not scraper_implementation.supports_asset(asset_kind):
            log_debug('ScraperFactory._get_asset_scraper() Scraper {0} does not support asset {1}. '
                      'Skipping.'.format(scraper_implementation.name, asset_info.name))
            return NullScraper()

        log_verb('Loaded {0:<10} asset scraper "{1}"'.format(asset_info.name, scraper_implementation.name if scraper_implementation else 'NONE'))
        if not scraper_implementation:
            return NullScraper()
        
        # ~~~ Asset scraping ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # settings.xml -> id="scan_asset_policy" default="0" values="Local Assets|Local Assets + Scrapers|Scrapers only"
        if scan_asset_policy == 0:
            log_verb('Asset policy: local images only | Scraper OFF')
            return LocalAssetScraper(asset_kind, asset_info, self.settings, launcher)
        
        elif scan_asset_policy == 1:
            log_verb('Asset policy: if not Local Image then Scraper ON')
            
            if scraper_implementation.name == 'TheGamesDB':
                onlineScraper = TheGamesDbScraper(self.settings, launcher, False, [asset_info])
                return LocalAssetScraper(asset_kind, asset_info, self.settings, launcher, onlineScraper)

            onlineScraper = OnlineAssetScraper(scraper_implementation, asset_kind, asset_info, self.settings, launcher)
            return LocalAssetScraper(asset_kind, asset_info, self.settings, launcher, onlineScraper)
        
        # >> Initialise options of the thumb scraper (NOT SUPPORTED YET)
        # region = self.settings['scraper_region']
        # thumb_imgsize = self.settings['scraper_thumb_size']
        # self.scraper_asset.set_options(region, thumb_imgsize)

        return NullScraper()

class ScraperSettings(object):
    
    def __init__(self, metadata_scraping_mode=1, asset_scraping_mode=1, ignore_scraped_title=False, scan_clean_tags=True):        
        # --- Set scraping mode ---
        # values="Semi-automatic|Automatic"
        self.metadata_scraping_mode  = metadata_scraping_mode
        self.asset_scraping_mode = asset_scraping_mode
        self.ignore_scraped_title = ignore_scraped_title
        self.scan_clean_tags = scan_clean_tags

    @staticmethod
    def create_from_settings(settings):        
        return ScraperSettings(
            settings['metadata_scraper_mode'] if 'metadata_scraper_mode' in settings else 1,
            settings['asset_scraper_mode'] if 'asset_scraper_mode' in settings else 1,
            settings['scan_ignore_scrap_title'] if 'scan_ignore_scrap_title' in settings else False,
            settings['scan_clean_tags'] if 'scan_clean_tags' in settings else True)

class ScrapeResult(object):
    metada_scraped  = False
    assets_scraped  = []

class Scraper(object):
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, scraper_settings, launcher, scrape_metadata, assets_to_scrape, fallbackScraper = None):
        
        self.cache = {}
        
        self.scraper_settings = scraper_settings
        self.launcher = launcher
                
        self.scrape_metadata = scrape_metadata
        self.assets_to_scrape = assets_to_scrape
        
        self.fallbackScraper = fallbackScraper

    def scrape(self, search_term, romPath, rom):
                
        results = self._get_candidates(search_term, romPath, rom)
        log_debug('Scraper \'{0}\' found {1} result/s'.format(self.getName(), len(results)))

        if not results or len(results) == 0:
            log_verb('Scraper \'{0}\' found no games after searching.'.format(self.getName()))
            
            if self.fallbackScraper:
                return self.fallbackScraper.scrape(search_term, romPath, rom)

            return False

        selected_candidate = 0
        if len(results) > 1 and self.scraper_settings.metadata_scraping_mode == 0:
            log_debug('Metadata semi-automatic scraping')
            # >> Close progress dialog (and check it was not canceled)
            # ?? todo again

            # >> Display corresponding game list found so user choses
            dialog = xbmcgui.Dialog()
            rom_name_list = []
            for game in results: 
                rom_name_list.append(game['display_name'])

            selected_candidate = dialog.select('Select game for ROM {0}'.format(romPath.getBase_noext()), rom_name_list)
            if selected_candidate < 0: selected_candidate = 0

            # >> Open progress dialog again
            # ?? todo again
        
        self._loadCandidate(results[selected_candidate], romPath, rom)
                
        scraper_applied = self._apply_candidate(romPath, rom)
                
        if not scraper_applied and self.fallbackScraper is not None:
            log_verb('Scraper \'{0}\' did not get the correct data. Using fallback scraping method: {1}.'.format(self.getName(), self.fallbackScraper.getName()))
            scraper_applied = self.fallbackScraper.scrape(search_term, romPath, rom)
        
        return scraper_applied
    
    @abc.abstractmethod
    def getName(self):
        return ''

    # search for candidates and return list with following item data:
    # { 'id' : <unique id>, 'display_name' : <name to be displayed>, 'order': <number to sort by/relevance> }
    @abc.abstractmethod
    def _get_candidates(self, search_term, romPath, rom):
        return []
    
    def _loadCandidate(self, candidate, romPath, rom):
        
        self.gamedata = self._new_gamedata_dic()
        
        if self.scrape_metadata:
            self._load_metadata(candidate, romPath, rom)

        if self.assets_to_scrape is not None and len(self.assets_to_scrape) > 0:
            self._load_assets(candidate, romPath, rom)
    
    @abc.abstractmethod
    def _load_metadata(self, candidate, romPath, rom):        
        pass
    
    @abc.abstractmethod
    def _load_assets(self, candidate, romPath, rom):        
        pass
        
    def _apply_candidate(self, romPath, rom):
        
        if not self.gamedata:
            log_verb('Scraper did not get the correct data.')
            return False

        if self.scrape_metadata:
            # --- Put metadata into ROM dictionary ---
            if self.scraper_settings.ignore_scraped_title:
                rom_name = text_format_ROM_title(rom.getBase_noext(), self.scraper_settings.scan_clean_tags)
                rom.set_name(rom_name)
                log_debug("User wants to ignore scraper name. Setting name to '{0}'".format(rom_name))
            else:
                rom_name = self.gamedata['title']
                rom.set_name(rom_name)
                log_debug("User wants scrapped name. Setting name to '{0}'".format(rom_name))

            rom.set_releaseyear(self.gamedata['year'])           # <year>
            rom.set_genre(self.gamedata['genre'])                # <genre>
            rom.set_developer(self.gamedata['developer'])        # <developer>
            rom.set_number_of_players(self.gamedata['nplayers']) # <nplayers>
            rom.set_esrb_rating(self.gamedata['esrb'])           # <esrb>
            rom.set_plot(self.gamedata['plot'])                  # <plot>
        
        if self.assets_to_scrape is not None and len(self.assets_to_scrape) > 0:
            image_list = self.gamedata['assets']    
            if not image_list:
                log_debug('{0} scraper has not collected images.'.format(self.getName()))
                return False

            for asset_info in self.assets_to_scrape:
                
                asset_directory     = self.launcher.get_asset_path(asset_info)
                asset_path_noext_FN = assets_get_path_noext_DIR(asset_info, asset_directory, romPath)
                log_debug('Scraper._apply_candidate() asset_path_noext "{0}"'.format(asset_path_noext_FN.getOriginalPath()))

                specific_images_list = [image_entry for image_entry in image_list if image_entry['type'].kind == asset_info.kind]

                log_debug('{} scraper has collected {} assets of type {}.'.format(self.getName(), len(specific_images_list), asset_info.name))
                if len(specific_images_list) == 0:
                    continue

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

                log_debug('Scraper._apply_candidate() Downloading selected image ...')

                # --- Resolve image URL ---
                if selected_image['is_online']:
                    
                    if selected_image['is_on_page']:
                        image_url = self._get_image_url_from_page(selected_image, asset_info)
                    else:
                        image_url = selected_image['url']

                    image_path = self._download_image(asset_info, image_url, asset_path_noext_FN)

                else:
                    log_debug('{0} scraper: user chose local image "{1}"'.format(self.asset_info.name, selected_image['url']))
                    image_path = FileNameFactory.create(selected_image['url'])

                if image_path:
                    rom.set_asset(asset_info, image_path)        
        
        return True

    def _download_image(self, asset_info, image_url, destination_folder):

        if image_url is None or image_url == '':
            log_debug('No image to download. Skipping')
            return None

        image_ext = text_get_image_URL_extension(image_url)
        log_debug('Downloading image URL "{1}"'.format(asset_info.name, image_url))

        # ~~~ Download image ~~~
        image_path = destination_folder.append(image_ext)
        log_verb('Downloading URL  "{0}"'.format(image_url))
        log_verb('Into local file  "{0}"'.format(image_path.getOriginalPath()))
        try:
            net_download_img(image_url, image_path)
        except socket.timeout:
            log_error('Cannot download {0} image (Timeout)'.format(asset_info.name))
            kodi_notify_warn('Cannot download {0} image (Timeout)'.format(asset_info.name))
            return None

        return image_path
    
    @abc.abstractmethod
    def _get_image_url_from_page(self, candidate, asset_info):        
        return ''

    def _get_from_cache(self, search_term):

        if search_term in self.cache:
            return self.cache[search_term]
        
        return None

    def _update_cache(self, search_term, data):
        self.cache[search_term] = data

    def _reset_cache(self):
        self.cache = {}

    def _new_gamedata_dic(self):
        gamedata = {
            'title'     : '',
            'year'      : '',
            'genre'     : '',
            'developer' : '',
            'nplayers'  : '',
            'esrb'      : '',
            'plot'      : '',
            'assets'    : []
        }

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

class NullScraper(Scraper):

    def __init__(self):
        super(NullScraper, self).__init__(None, None, False, None)
        
    def scrape(self, search_term, romPath, rom):
        return True

    def getName(self):
        return 'Empty scraper'

    def _get_candidates(self, search_term, romPath, rom):
        return []

    def _load_metadata(self, candidate, romPath, rom):        
        pass
    
    def _load_assets(self, candidate, romPath, rom):
        pass

class CleanTitleScraper(Scraper):

    def __init__(self, settings, launcher):
        
        scraper_settings = ScraperSettings.create_from_settings(settings)
        scraper_settings.metadata_scraping_mode = 1
        scraper_settings.ignore_scraped_title = False

        super(CleanTitleScraper, self).__init__(scraper_settings, launcher, True, [])

    def getName(self):
        return 'Clean title only scraper'

    def _get_candidates(self, search_term, romPath, rom):
        games = []
        games.append('dummy')
        return games
    
    def _load_metadata(self, candidate, romPath, rom):        
        if self.launcher.get_launcher_type() == LAUNCHER_STEAM:
            log_debug('CleanTitleScraper: Detected Steam launcher, leaving rom name untouched.')
            return

        log_debug('Only cleaning ROM name.')
        self.gamedata['title'] = text_format_ROM_title(romPath.getBase_noext(), self.scraper_settings.scan_clean_tags)

    def _load_assets(self, candidate, romPath, rom):
        pass

    def _get_image_url_from_page(self, candidate, asset_info):        
        return candidate['url']
    
class NfoScraper(Scraper):
    
    def __init__(self, settings, launcher, fallbackScraper = None):
                
        scraper_settings = ScraperSettings.create_from_settings(settings)
        scraper_settings.metadata_scraping_mode = 1

        super(NfoScraper, self).__init__(scraper_settings, launcher, True, [], fallbackScraper)

    def getName(self):
        return 'NFO scraper'

    def _get_candidates(self, search_term, romPath, rom):

        NFO_file = romPath.switchExtension('nfo')
        games = []

        if NFO_file.exists():
            games.append(NFO_file)
            log_debug('NFO file found "{0}"'.format(NFO_file.getOriginalPath()))
        else:
            log_debug('NFO file NOT found "{0}"'.format(NFO_file.getOriginalPath()))

        return games

    def _load_metadata(self, candidate, romPath, rom):        
        
        log_debug('Reading NFO file')
        # NOTE <platform> is chosen by AEL, never read from NFO files. Indeed, platform
        #      is a Launcher property, not a ROM property.
        self.gamedata = fs_import_ROM_NFO_file_scanner(candidate)

    def _load_assets(self, candidate, romPath, rom):
        pass
    
    def _get_image_url_from_page(self, candidate, asset_info):        
        return candidate['url']

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

class LocalAssetScraper(Scraper):
    
    def __init__(self, asset_kind, asset_info, settings, launcher, fallbackScraper = None): 
                
        # --- Create a cache of assets ---
        # >> misc_add_file_cache() creates a set with all files in a given directory.
        # >> That set is stored in a function internal cache associated with the path.
        # >> Files in the cache can be searched with misc_search_file_cache()
        asset_path = launcher.get_asset_path(asset_info)
        misc_add_file_cache(asset_path)

        self.asset_kind = asset_kind
        self.asset_info = asset_info
                
        scraper_settings = ScraperSettings.create_from_settings(settings)

        super(LocalAssetScraper, self).__init__(scraper_settings, launcher, False, [asset_info], fallbackScraper)
        
    def getName(self):
        return 'Local assets scraper'

    def _get_candidates(self, search_term, romPath, rom):

        # ~~~~~ Search for local artwork/assets ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        rom_basename_noext = romPath.getBase_noext()
        asset_path = self.launcher.get_asset_path(self.asset_info)
        local_asset = misc_search_file_cache(asset_path, rom_basename_noext, self.asset_info.exts)

        if not local_asset:
            log_verb('LocalAssetScraper._get_candidates() Missing  {0:<9}'.format(self.asset_info.name))
            return []
        
        log_verb('LocalAssetScraper._get_candidates() Found    {0:<9} "{1}"'.format(self.asset_info.name, local_asset.getOriginalPath()))
        local_asset_info = {
           'id' : local_asset.getOriginalPath(),
           'display_name' : local_asset.getBase(), 
           'order' : 1,
           'file': local_asset
        }

        return [local_asset_info]

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


class TheGamesDbScraper(Scraper): 

    def __init__(self, settings, launcher, scrape_metadata, assets_to_scrape, fallbackScraper = None):

        self.publishers = None
        self.genres = None
        self.developers = None

        self.api_key = settings['thegamesdb_apikey']
        scraper_settings = ScraperSettings.create_from_settings(settings)

        super(TheGamesDbScraper, self).__init__(scraper_settings, launcher, scrape_metadata, assets_to_scrape, fallbackScraper)
        
    def getName(self):
        return 'TheGamesDB'
    
    def _get_candidates(self, search_term, romPath, rom):
        
        platform = self.launcher.get_platform()
        scraper_platform = AEL_platform_to_TheGamesDB(platform)
        
        log_debug('TheGamesDbScraper::_get_candidates() search_term         "{0}"'.format(search_term))
        log_debug('TheGamesDbScraper::_get_candidates() rom_base_noext      "{0}"'.format(self.launcher.get_roms_base()))
        log_debug('TheGamesDbScraper::_get_candidates() AEL platform        "{0}"'.format(platform))
        log_debug('TheGamesDbScraper::_get_candidates() TheGamesDB platform "{0}"'.format(scraper_platform))
        
        # >> Check if search term page data is in cache. If so it's a cache hit.
        game_id_from_cache = self._get_from_cache(search_term)
        
        if game_id_from_cache is not None and game_id_from_cache > 0:
            return [{ 'id' : game_id_from_cache, 'display_name' : 'cached', 'order': 1 }]

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

        # --- Parse game page data ---
        self.gamedata['title']      = online_data['game_title'] if 'game_title' in online_data else '' 
        self.gamedata['nplayers']   = online_data['players'] if 'players' in online_data else '' 
        self.gamedata['esrb']       = online_data['rating'] if 'rating' in online_data else '' 
        self.gamedata['plot']       = online_data['overview'] if 'overview' in online_data else '' 
        self.gamedata['genre']      = self._get_genres(online_data['genres']) if 'genres' in online_data else '' 
        self.gamedata['developer']  = self._get_developers(online_data['developers']) if 'developers' in online_data else '' 
        self.gamedata['year']       = online_data['release_date'][:4] if 'release_date' in online_data and online_data['release_date'] is not None and online_data['release_date'] != '' else ''

    def _load_assets(self, candidate, romPath, rom):
        
        url = 'https://api.thegamesdb.net/Games/Images?apikey={}&games_id={}'.format(self.api_key, candidate['id'])
        asset_list = self._read_assets_from_url(url, candidate['id'])

        log_debug('Found {} assets for candidate #{}'.format(len(asset_list), candidate['id']))

        for asset in asset_list:
            
            allowed_asset = next((allowed_asset for allowed_asset in self.assets_to_scrape if allowed_asset.kind == asset['type']), None)
            if allowed_asset is not None:
                asset['type'] = allowed_asset
                self.gamedata['assets'].append(asset)

        log_debug('After filtering {} assets left for candidate #{}'.format(len(self.gamedata['assets']), candidate['id']))

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

            asset_data['type']  = asset_kind
            asset_data['url']   = base_url + image_data['filename']
            asset_data['name']  = ' '.join(filter(None, [image_data['type'], image_data['side'], image_data['resolution']]))

            log_debug('TheGamesDbScraper:: found asset {}'.format(asset_data))
            assets_list.append(asset_data)
            
        next_url = page_data['pages']['next']
        if next_url is not None:
            assets_list = assets_list + self._read_assets_from_url(next_url, candidate_id)

        return assets_list


    asset_name_mapping = {
        'fanart' : ASSET_FANART,
        'clearlogo': ASSET_CLEARLOGO,
        'banner': ASSET_BANNER,
        'boxartfront': ASSET_BOXFRONT,
        'boxartback': ASSET_BOXBACK,
        'screenshot': ASSET_SNAP
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


class MobyGamesScraper(Scraper): 
        
    def __init__(self, settings, launcher, scrape_metadata, assets_to_scrape, fallbackScraper = None):

        self.api_key = settings['mobygames_apikey']
        scraper_settings = ScraperSettings.create_from_settings(settings)

        self.last_http_call = datetime.datetime.now()

        super(MobyGamesScraper, self).__init__(scraper_settings, launcher, scrape_metadata, assets_to_scrape, fallbackScraper)
        
    def getName(self):
        return 'MobyGames'
    
    def _get_candidates(self, search_term, romPath, rom):
        
        platform = self.launcher.get_platform()
        scraper_platform = AEL_platform_to_MobyGames(platform)
        
        log_debug('MobyGamesScraper::_get_candidates() search_term         "{0}"'.format(search_term))
        log_debug('MobyGamesScraper::_get_candidates() rom_base_noext      "{0}"'.format(self.launcher.get_roms_base()))
        log_debug('MobyGamesScraper::_get_candidates() AEL platform        "{0}"'.format(platform))
        log_debug('MobyGamesScraper::_get_candidates() MobyGames platform  "{0}"'.format(scraper_platform))
        
        # >> Check if search term page data is in cache. If so it's a cache hit.
        game_id_from_cache = self._get_from_cache(search_term)
        
        if game_id_from_cache is not None and game_id_from_cache > 0:
            return [{ 'id' : game_id_from_cache, 'display_name' : 'cached', 'order': 1 }]

        game_list = []            
        search_string_encoded = urllib.quote_plus(search_term.encode('utf8'))
        url = 'https://api.mobygames.com/v1/games?api_key={}&format=brief&title={}&platform={}'.format(self.api_key, search_string_encoded, scraper_platform)
            
        game_list = self._read_games_from_url(url, search_term, scraper_platform)
        
        # >> Order list based on score
        game_list.sort(key = lambda result: result['order'], reverse = True)

        return game_list
        
    def _read_games_from_url(self, url, search_term, scraper_platform):
        
        self._do_toomanyrequests_check()
            
        page_data = net_get_URL_as_json(url)
        self.last_http_call = datetime.datetime.now()

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

        self.last_http_call = datetime.datetime.now()
        
        platform = self.launcher.get_platform()
        scraper_platform = AEL_platform_to_MobyGames(platform)
        
        # --- Parse game page data ---
        self.gamedata['title']      = online_data['title'] if 'title' in online_data else '' 
        self.gamedata['plot']       = online_data['description'] if 'description' in online_data else '' 
        self.gamedata['genre']      = self._get_genres(online_data['genres']) if 'genres' in online_data else '' 
        self.gamedata['year']       = self._get_year_by_platform(online_data['platforms'], scraper_platform)

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

        for asset in assets_list:
            
            allowed_asset = next((allowed_asset for allowed_asset in self.assets_to_scrape if allowed_asset.kind == asset['type']), None)
            if allowed_asset is not None:
                asset['type'] = allowed_asset
                self.gamedata['assets'].append(asset)

        log_debug('After filtering {} assets left for candidate #{}'.format(len(self.gamedata['assets']), candidate['id']))


    def _load_snap_assets(self, candidate, platform_id):

        if len(filter(lambda a: a.kind == ASSET_SNAP, self.assets_to_scrape)) < 1:
            return []

        url = 'https://api.mobygames.com/v1/games/{}/platforms/{}/screenshots?api_key={}'.format(candidate['id'], platform_id, self.api_key)        
        log_debug('Get screenshot image data from {}'.format(url))
        
        self._do_toomanyrequests_check()

        page_data   = net_get_URL_as_json(url)
        online_data = page_data['screenshots']

        assets_list = []
        # --- Parse images page data ---
        for image_data in online_data:
            asset_data = self._new_assetdata_dic()

            asset_data['type']  = ASSET_SNAP
            asset_data['url']   = image_data['image']
            asset_data['name']  = image_data['caption']

            log_debug('MobyGamesScraper:: found asset {}'.format(asset_data))
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
                
                asset_type = image_data['scan_of']
                asset_kind = MobyGamesScraper.asset_name_mapping[asset_type.lower()]

                asset_data['type']  = asset_kind
                asset_data['url']   = image_data['image']
                asset_data['name']  = '{} - {} ({})'.format(image_data['scan_of'], image_data['description'], country_names)

                log_debug('MobyGamesScraper:: found asset {}'.format(asset_data))
                assets_list.append(asset_data)

        log_debug('Found {} cover assets for candidate #{}'.format(len(assets_list), candidate['id']))    
        return assets_list
        
    asset_name_mapping = {
        'media' : ASSET_CARTRIDGE,
        'manual': ASSET_MANUAL,
        'front cover': ASSET_BOXFRONT,
        'back cover': ASSET_BOXBACK,
        'spine/sides': 0 # not supported by AEL?
    }

    
    def _get_image_url_from_page(self, candidate, asset_info):        
        return candidate['url']

    def _do_toomanyrequests_check(self):
        # make sure we dont go over the TooManyRequests limit of 1 second
        now = datetime.datetime.now()
        if (now-self.last_http_call).total_seconds() < 1:
            time.sleep(1)
        
#
# Scraper implementation for GameFaq website
#            
class GameFaqScraper(Scraper):
         
    def __init__(self, settings, launcher, scrape_metadata, assets_to_scrape, fallbackScraper = None):

        scraper_settings = ScraperSettings.create_from_settings(settings)
        super(GameFaqScraper, self).__init__(scraper_settings, launcher, scrape_metadata, assets_to_scrape, fallbackScraper)
        
    def getName(self):
        return 'GameFaq'

    def _get_candidates(self, search_term, romPath, rom):
               
        platform = self.launcher.get_platform()
        scraper_platform = AEL_platform_to_GameFAQs(platform)
        
        log_debug('GamesFaqScraper::_get_candidates() search_term         "{0}"'.format(search_term))
        log_debug('GamesFaqScraper::_get_candidates() rom_base_noext      "{0}"'.format(self.launcher.get_roms_base()))
        log_debug('GamesFaqScraper::_get_candidates() AEL platform        "{0}"'.format(platform))
        log_debug('GamesFaqScraper::_get_candidates() GameFAQs platform   "{0}"'.format(scraper_platform))
        
        # >> Check if search term page data is in cache. If so it's a cache hit.
        game_id_from_cache = self._get_from_cache(search_term)
        
        if game_id_from_cache is not None and game_id_from_cache > 0:
            return [{ 'id' : game_id_from_cache, 'display_name' : 'cached', 'order': 1 }]

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
            
        # --- Set game page data ---
        self.gamedata['title']      = candidate['game_name'] 
        self.gamedata['plot']       = text_unescape_and_untag_HTML(game_plot[0]) if game_plot else ''        
        self.gamedata['genre']      = game_genre[0][3] if game_genre else '' 
        self.gamedata['year']       = game_release[0][1][-4:] if game_release else ''
        self.gamedata['developer']  = game_developer

        log_debug('GamesFaqScraper::_load_metadata() Collected all metadata from {}'.format(url))

        
    def _load_assets(self, candidate, romPath, rom):
        
        url = 'https://gamefaqs.gamespot.com{}/images'.format(candidate['id'])
        assets_list = self._load_assets_from_url(url)
        self.gamedata['assets'] = assets_list
        
        log_debug('GamesFaqScraper:: Found {} assets for candidate #{}'.format(len(assets_list), candidate['id']))    
        
    def _load_assets_from_url(self, url):
        log_debug('GamesFaqScraper::_load_assets_from_url() Get asset data from {}'.format(url))
        page_data = net_get_URL_oneline(url)
        assets_list = []

        asset_blocks = re.findall('<div class=\"head\"><h2 class=\"title\">((\w|\s)+?)</h2></div><div class=\"body\"><table class=\"contrib\">(.*?)</table></div>', page_data)
        for asset_block in asset_blocks:
            remote_asset_type = asset_block[0]
            assets_page_data = asset_block[2]
            asset_kind = self._parse_asset_type(remote_asset_type)
            
            allowed_asset = next((allowed_asset for allowed_asset in self.assets_to_scrape if allowed_asset.kind == asset_kind), None)
            if allowed_asset is None:
                continue
            
            log_debug('Collecting assets from {}'.format(remote_asset_type))
            
            # <a href="/nes/578318-castlevania/images/135454"><img class="img100 imgboxart" src="https://gamefaqs.akamaized.net/box/2/7/6/2276_thumb.jpg" alt="Castlevania (US)" /></a>
            block_items = re.finditer('<a href=\"(?P<lnk>.+?)\"><img class=\"(img100\s)?imgboxart\" src=\"(.+?)\" (alt=\"(?P<alt>.+?)\")?\s?/></a>', assets_page_data)
            for m in block_items:
                image_data = m.groupdict()
                asset_data = self._new_assetdata_dic()
                
                asset_data['type']  = allowed_asset
                asset_data['url']   = image_data['lnk']
                asset_data['name']  = image_data['alt'] if 'alt' in image_data else image_data['link']
                asset_data['is_on_page'] = True

                assets_list.append(asset_data)

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
            image_on_page = image_data.groupdict()
            image_asset_kind = self._parse_asset_type(image_on_page['alt'])
            log_verb('Found "{}" type {} with url {}'.format(image_on_page['alt'], image_asset_kind, image_on_page['url']))
            
            if asset_info.kind == image_asset_kind:
                log_debug('GamesFaqScraper::_get_image_url_from_page() Found match {}'.format(image_on_page['alt']))
                return image_on_page['url']

        log_debug('GamesFaqScraper::_get_image_url_from_page() No correct match')
        return ''

    def _parse_asset_type(self, header):

        if 'Screenshots' in header:
            return ASSET_SNAP
        if 'Box Back' in header:
            return ASSET_BOXBACK
        if 'Box Front' in header:
            return ASSET_BOXFRONT
        if 'Box' in header:
            return ASSET_BOXFRONT

        return ASSET_SNAP