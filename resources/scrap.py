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
from datetime import datetime
from time import time

from urllib import quote_plus, urlencode

# --- AEL packages ---
from resources.constants import *
from resources.platforms import *
from resources.utils import *
from resources.net_IO import *
from resources.disk_IO import FileName, fs_import_ROM_NFO_file_scanner

from resources.objects import LauncherABC, ROMLauncherABC, ROM
from resources.objects import g_assetFactory, assets_get_path_noext_DIR, ASSET_SETTING_KEYS

class ScraperFactory(KodiProgressDialogStrategy):
    def __init__(self, PATHS, settings):
        self.settings = settings
        self.addon_dir = PATHS.ADDON_DATA_DIR
        super(ScraperFactory, self).__init__()

    def create(self, launcher):
        scan_metadata_policy    = self.settings['scan_metadata_policy']
        scan_asset_policy       = self.settings['scan_asset_policy']

        if self._hasDuplicateArtworkDirs(launcher):
            return None

        available_scrapers = self._initialize_possible_scrapers(launcher)
        metadata_scraper = self._get_metadata_scraper(scan_metadata_policy, launcher, available_scrapers)

        self._startProgressPhase('Advanced Emulator Launcher', 'Preparing scrapers ...')

        # --- Assets/artwork stuff ----------------------------------------------------------------
        # ~~~ Check asset dirs and disable scanning for unset dirs ~~~
        unconfigured_name_list = []
        rom_asset_infos = g_assetFactory.get_asset_kinds_for_roms()
        i = 0

        asset_scrapers = {}
        for asset_info in rom_asset_infos:
            
            asset_path = launcher.get_asset_path(asset_info)
            if not asset_path:
                unconfigured_name_list.append(asset_info.name)
                log_verb('ScraperFactory.create() {0:<9} path unconfigured'.format(asset_info.name))
            else:
                log_debug('ScraperFactory.create() {0:<9} path configured'.format(asset_info.name))
                asset_scraper = self._get_asset_scraper(scan_asset_policy, asset_info, launcher)
                
                if asset_scraper:
                    asset_scrapers[asset_info] = asset_scraper
                
            self._updateProgress((100*i)/len(ROM_ASSET_ID_LIST))
            i += 1

        self._endProgressPhase()
        
        if unconfigured_name_list:
            unconfigured_asset_srt = ', '.join(unconfigured_name_list)
            kodi_dialog_OK('Assets directories not set: {0}. '.format(unconfigured_asset_srt) +
                           'Asset scanner will be disabled for this/those.')

        strategy = ScrapingStrategy(metadata_scraper, asset_scrapers)
        return strategy

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

    #
    # Initializes all the possible scraper instances beforehand for the launcher.
    # This way the same instances can be reused between metadata and different asset types
    # when the user wants the same scraper source for those. 
    # This way the cached search hits and asset hits will be reused and less web calls need
    # to be performed.
    #
    def _initialize_possible_scrapers(self, launcher):

        # default scrapers
        cleanTitleScraper = CleanTitleScraper(self.settings, launcher)

        available_scrapers = {}
        available_scrapers[0] = cleanTitleScraper
        available_scrapers[1] = TheGamesDbScraper(self.settings, launcher, cleanTitleScraper)
        available_scrapers[2] = GameFaqScraper(self.settings, launcher, cleanTitleScraper)
        available_scrapers[3] = MobyGamesScraper(self.settings, launcher, cleanTitleScraper)
        available_scrapers[3] = ArcadeDbScraper(self.settings, launcher, cleanTitleScraper)
        
        return available_scrapers
    
    # >> Determine metadata action based on configured metadata policy
    # >> scan_metadata_policy -> values="None|NFO Files|NFO Files + Scrapers|Scrapers"    
    # 
    def _get_metadata_scraper(self, scan_metadata_policy, launcher, available_scrapers):
        
        if scan_metadata_policy == 0:
            log_verb('Metadata policy: No NFO reading, no scraper. Only cleaning ROM name.')
            return available_scrapers[0]

        elif scan_metadata_policy == 1:
            log_verb('Metadata policy: Read NFO file only | Scraper OFF')
            return NfoScraper(self.settings, launcher, available_scrapers[0])

        elif scan_metadata_policy == 2:
            log_verb('Metadata policy: Read NFO file ON, if not NFO then Scraper ON')
            
            # --- Metadata scraper ---
            scraper_index = self.settings['scraper_metadata']
            onlineScraper = available_scrapers[scraper_index]
            log_verb('Loaded metadata scraper "{0}"'.format(onlineScraper.getName()))
            return NfoScraper(self.settings, launcher, onlineScraper)

        elif scan_metadata_policy == 3:
            log_verb('Metadata policy: Read NFO file OFF | Scraper ON')
            log_verb('Metadata policy: Forced scraper ON')
            
            # --- Metadata scraper ---
            scraper_index = self.settings['scraper_metadata']
            onlineScraper = available_scrapers[scraper_index]
            log_verb('Loaded metadata scraper "{0}"'.format(onlineScraper.getName()))            
            return onlineScraper

        log_error('Invalid scan_metadata_policy value = {0}. Fallback on clean title only'.format(scan_metadata_policy))
        return available_scrapers[0]
    
    # todo
    # NOTE: previously AEL had per asset type (and MAME) an array with possible scrapers.
    # The actual scraper was selected by getting the correct index from the settings for that particular type.
    # I propose we give each scraper class an unique id and just store that id in the settings. 
    #
    # >> Scrapers for MAME platform are different than rest of the platforms
    def _get_asset_scraper(self, scan_asset_policy, asset_info, launcher):

        
        # ~~~ Asset scraping ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # settings.xml -> id="scan_asset_policy" default="0" values="Local Assets|Local Assets + Scrapers|Scrapers only"
        if scan_asset_policy == 0:
            log_verb('Asset policy: local images only | Scraper OFF')
            return LocalAssetScraper(self.settings, launcher)
                
        key = ASSET_SETTING_KEYS[asset_info.id]
        if key == '':
            return None
            
        if key not in settings:
            log_warning("Scraper with key {} not set in settings".format(key))
            return None

        scraper_index = settings[key]

        # --- Asset scraper ---
        onlineScraper = available_scrapers[scraper_index]

        if not onlineScraper:
            log_verb('Loaded {0:<10} asset scraper "NONE"'.format(asset_info.name))
            return NullScraper()

        # --- If scraper does not support particular asset return inmediately ---
        if not onlineScraper.supports_asset(asset_info):
            log_debug('ScraperFactory._get_asset_scraper() Scraper {0} does not support asset {1}. '
                      'Skipping.'.format(onlineScraper.name, asset_info.name))
            return NullScraper()
                
        log_verb('Loaded {0:<10} asset scraper "{1}"'.format(asset_info.name, onlineScraper.name))
                
        if scan_asset_policy == 1:
            log_verb('Asset policy: if not Local Image then Scraper ON')
            return LocalAssetScraper(self.settings, launcher, onlineScraper)
        
        # >> Initialise options of the thumb scraper (NOT SUPPORTED YET)
        # region = self.settings['scraper_region']
        # thumb_imgsize = self.settings['scraper_thumb_size']
        # self.scraper_asset.set_options(region, thumb_imgsize)
        return NullScraper()

class ScrapingStrategy(object):

    # metadata_scraper = single instance of a scraper
    # assets_scrapers = dictionary of asset info id & scraper to use
    def __init__(self, metadata_scraper, asset_scrapers):
        self.metadata_scraper = metadata_scraper
        self.asset_scrapers = asset_scrapers

    # Actual scrape process
    # Leave assets_to_scrape with none value if you want to scrape all available assets
    def scrape(self, search_term, rom_path, rom, scrape_metadata = True, assets_to_scrape = None):
                
        #self._updateProgressMessage(file_text, 'Scraping {0}...'.format(scraper.getName()))
        if scrape_metadata and self.metadata_scraper:
            log_debug('ScrapingStrategy:: Scraping metadata with scraper \'{0}\''.format(self.metadata_scraper.getName()))
            self.metadata_scraper.scrape_metadata(search_term, rom_path, rom)

        for asset_info in self.asset_scrapers.keys():
            
            if assets_to_scrape is not None and not asset_info in assets_to_scrape:
                continue
                
            scraper = self.asset_scrapers[asset_info]

            log_debug('ScrapingStrategy:: Scraping asset {} with scraper \'{}\''.format(asset_info.name, scraper.getName()))
            scraper.scrape_asset(search_term, asset_info, rom_path, rom)
            
        romdata = rom.get_data()
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

class Scraper(object):
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, scraper_settings, launcher, fallbackScraper = None):
        
        self.cache = {}
        self.assets_cache = {}
        
        self.scraper_settings = scraper_settings
        self.launcher = launcher
                
        self.fallbackScraper = fallbackScraper

    def scrape_metadata(self, search_term, rom_path, rom):
        
        candidates = self._get_candidates(search_term, rom_path, rom)
        log_debug('Scraper \'{0}\' found {1} result/s'.format(self.getName(), len(candidates)))

        if not candidates or len(candidates) == 0:
            log_verb('Scraper \'{0}\' found no games after searching.'.format(self.getName()))
            
            if self.fallbackScraper:
                return self.fallbackScraper.scrape_metadata(search_term, rom_path, rom)

            return False
        
        selected_candidate = 0
        if len(candidates) > 1 and self.scraper_settings.metadata_scraping_mode == 0:
            log_debug('Metadata semi-automatic scraping')
            # >> Close progress dialog (and check it was not canceled)
            # ?? todo again

            # >> Display corresponding game list found so user choses
            dialog = xbmcgui.Dialog()
            rom_name_list = []
            for game in candidates: 
                rom_name_list.append(game['display_name'])

            selected_candidate = dialog.select('Select game for ROM {0}'.format(rom_path.getBase_noext()), rom_name_list)
            if selected_candidate < 0: 
                selected_candidate = 0

            # >> Open progress dialog again
            # ?? todo again

        
            
        candidate = candidates[selected_candidate]

        # Update cache so future searches will automatically select this candidate for this particular search term
        self._update_cache(search_term, candidate)
        
        game_data = self._load_metadata(candidate, rom_path, rom)        
        scraper_applied = self._apply_candidate_on_metadata(rom_path, rom, game_data)
                
        if not scraper_applied and self.fallbackScraper is not None:
            log_verb('Scraper \'{0}\' did not get the correct data. Using fallback scraping method: {1}.'.format(self.getName(), self.fallbackScraper.getName()))
            return self.fallbackScraper.scrape_metadata(search_term, rom_path, rom)
        
        return scraper_applied

    def scrape_asset(self, search_term, asset_info_to_scrape, rom_path, rom):
        
        log_debug('Scraper \'{0}\' searching for asset {1}'.format(self.getName(), asset_info_to_scrape.name))
        candidates = self._get_candidates(search_term, rom_path, rom)
        log_debug('Scraper \'{0}\' found {1} result/s'.format(self.getName(), len(candidates)))

        if not candidates or len(candidates) == 0:
            log_verb('Scraper \'{0}\' found no games after searching.'.format(self.getName()))
            
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

            selected_candidate = dialog.select('Select game for ROM {0}'.format(rom_path.getBase_noext()), rom_name_list)
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
            log_verb('Scraper \'{0}\' did not get the correct data. Using fallback scraping method: {1}.'.format(self.getName(), self.fallbackScraper.getName()))
            return self.fallbackScraper.scrape_asset(search_term, rom_path, rom)
        
        return scraper_applied
        
    @abc.abstractmethod
    def getName(self):
        return ''

    @abc.abstractmethod
    def supports_asset_type(self, asset_info):
        return True

    # search for candidates and return list with following item data:
    # { 'id' : <unique id>, 'display_name' : <name to be displayed>, 'order': <number to sort by/relevance> }
    @abc.abstractmethod
    def _get_candidates(self, search_term, romPath, rom):
        return []
            
    @abc.abstractmethod
    def _load_metadata(self, candidate, romPath, rom):        
        return self._new_gamedata_dic()
    
    @abc.abstractmethod
    def _load_assets(self, candidate, romPath, rom):        
        pass
    
    def _apply_candidate_on_metadata(self, rom_path, rom, candidate_data):

        if candidate_data is None:
            return False

        # --- Put metadata into ROM dictionary ---
        if self.scraper_settings.ignore_scraped_title:
            rom_name = text_format_ROM_title(rom.getBase_noext(), self.scraper_settings.scan_clean_tags)
            rom.set_name(rom_name)
            log_debug("User wants to ignore scraper name. Setting name to '{0}'".format(rom_name))
        else:
            rom_name = candidate_data['title']
            rom.set_name(rom_name)
            log_debug("User wants scrapped name. Setting name to '{0}'".format(rom_name))

        rom.set_releaseyear(candidate_data['year'])           # <year>
        rom.set_genre(candidate_data['genre'])                # <genre>
        rom.set_developer(candidate_data['developer'])        # <developer>
        rom.set_number_of_players(candidate_data['nplayers']) # <nplayers>
        rom.set_esrb_rating(candidate_data['esrb'])           # <esrb>
        rom.set_plot(candidate_data['plot'])                  # <plot>

        return True
    
    def _apply_candidate_on_asset(self, rom_path, rom, asset_info, found_assets):
   
        if not found_assets:
            log_debug('{0} scraper has not collected images.'.format(self.getName()))
            return False
                
        asset_directory     = self.launcher.get_asset_path(asset_info)
        asset_path_noext_FN = assets_get_path_noext_DIR(asset_info, asset_directory, rom_path)
        log_debug('Scraper.apply_candidate_on_asset() asset_path_noext "{0}"'.format(asset_path_noext_FN.getPath()))

        specific_images_list = [image_entry for image_entry in found_assets if image_entry['type'].id == asset_info.id]

        log_debug('{} scraper has collected {} assets of type {}.'.format(self.getName(), len(specific_images_list), asset_info.name))
        if len(specific_images_list) == 0:
            log_debug('{0} scraper has not collected images for asset {}.'.format(self.getName(), asset_info.name))
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
                log_debug('{0} scraper: user chose local image "{1}"'.format(self.asset_info.name, selected_image['url']))
                image_path = FileName(selected_image['url'])

            if image_path:
                rom.set_asset(asset_info, image_path)        
        
        return True
 
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
                    image_path = FileName(selected_image['url'])

                if image_path:
                    rom.set_asset(asset_info, image_path)        
        
        return True

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
    
    @abc.abstractmethod
    def _get_image_url_from_page(self, candidate, asset_info):        
        return ''

    def _get_from_cache(self, search_term):

        if search_term in self.cache:
            return self.cache[search_term]
        
        return None

    def _get_from_assets_cache(self, candidate_id):

        if candidate_id in self.assets_cache:
            return self.assets_cache[candidate_id]
        
        return None

    def _update_cache(self, search_term, data):
        self.cache[search_term] = data
        
    def _update_assets_cache(self, candidate_id, data):
        self.assets_cache[candidate_id] = data

    def _reset_cache(self):
        self.cache = {}
        self.assets_cache = {}
        
    def _new_gamedata_dic(self):
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
        if self.launcher.get_launcher_type() == OBJ_LAUNCHER_STEAM:
            log_debug('CleanTitleScraper: Detected Steam launcher, leaving rom name untouched.')
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

        NFO_file = romPath.switchExtension('nfo')
        games = []

        if NFO_file.exists():
            games.append({ 'id' : NFO_file.getPath(), 'display_name' : NFO_file.getBase(), 'order': 1 , 'file': NFO_file })
            log_debug('NFO file found "{0}"'.format(NFO_file.getOriginalPath()))
        else:
            log_debug('NFO file NOT found "{0}"'.format(NFO_file.getOriginalPath()))

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
            asset_data['url']       = local_asset.getOriginalPath()
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