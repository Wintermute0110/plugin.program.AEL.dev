# --- Python standard library ---
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod
import urllib, urllib2, urlparse, socket, exceptions

from disk_IO import *
from utils import *
from utils_kodi import *

from scrap import *
from assets import *
from constants import *

class ScraperFactory(ProgressDialogStrategy):
    
    def __init__(self, settings, addon_dir):

        self.settings = settings
        self.addon_dir = addon_dir

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
                onlineScraper = TheGamesDbMetadataScraper(self.settings, launcher, cleanTitleScraper)
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
                onlineScraper = TheGamesDbMetadataScraper(self.settings, launcher, cleanTitleScraper)
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

class Scraper():
    __metaclass__ = ABCMeta
    
    def __init__(self, scraper_settings, launcher, scrape_metadata, assets_to_scrape, fallbackScraper = None):
        
        self.cache = {}
        
        self.scraper_settings = scraper_settings
        self.launcher = launcher
                
        self.scrape_metadata = scrape_metadata
        self.assets_to_scrape = assets_to_scrape
        
        self.fallbackScraper = fallbackScraper

    def scrape(self, search_term, romPath, rom):
                
        results = self._getCandidates(search_term, romPath, rom)
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
                
        scraper_applied = self._applyCandidate(romPath, rom)
                
        if not scraper_applied and self.fallbackScraper is not None:
            log_verb('Scraper \'{0}\' did not get the correct data. Using fallback scraping method: {1}.'.format(self.getName(), self.fallbackScraper.getName()))
            scraper_applied = self.fallbackScraper.scrape(search_term, romPath, rom)
        
        return scraper_applied
    
    @abstractmethod
    def getName(self):
        return ''

    # search for candidates and return list with following item data:
    # { 'id' : <unique id>, 'display_name' : <name to be displayed>, 'order': <number to sort by/relevance> }
    @abstractmethod
    def _getCandidates(self, search_term, romPath, rom):
        return []
    
    def _loadCandidate(self, candidate, romPath, rom):
        
        self.gamedata = self._new_gamedata_dic()
        
        if self.scrape_metadata:
            self._load_metadata(candidate, romPath, rom)

        if self.assets_to_scrape is not None and len(self.assets_to_scrape) > 0:
            self._load_assets(candidate, romPath, rom)

    @abstractmethod
    def _load_metadata(self, candidate, romPath, rom):        
        pass
    
    @abstractmethod
    def _load_assets(self, candidate, romPath, rom):        
        pass
        
    def _applyCandidate(self, romPath, rom):
        
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

            rom.update_releaseyear(self.gamedata['year'])        # <year>
            rom.update_genre(self.gamedata['genre'])             # <genre>
            rom.update_developer(self.gamedata['developer'])     # <developer>
            rom.set_number_of_players(self.gamedata['nplayers']) # <nplayers>
            rom.set_esrb_rating(self.gamedata['esrb'])           # <esrb>
            rom.update_plot(self.gamedata['plot'])               # <plot>
        
        if self.assets_to_scrape is not None and len(self.assets_to_scrape) > 0:
            image_list = self.gamedata['assets']    
            if not image_list:
                log_debug('{0} scraper has not collected images.'.format(self.getName()))
                return False

            for asset_info in self.assets_to_scrape:
                
                asset_directory     = self.launcher.get_asset_path(asset_info)
                asset_path_noext_FN = assets_get_path_noext_DIR(asset_info, asset_directory, romPath)
                log_debug('Scraper._applyCandidate() asset_path_noext "{0}"'.format(asset_path_noext_FN.getOriginalPath()))

                specific_images_list = [image_entry for image_entry in image_list if image_entry['type'].kind == asset_info.kind]

                log_debug('{} scraper has collected {} assets of type {}.'.format(self.getName(), len(specific_images_list), asset_info.name))
                if len(specific_images_list) == 0:
                    continue

                # --- Semi-automatic scraping (user choses an image from a list) ---
                if self.scraper_settings.asset_scraping_mode == 0:
                    # >> If image_list has only 1 element do not show select dialog. Note that the length
                    # >> of image_list is 1 only if scraper returned 1 image and a local image does not exist.
                    if len(image_list) == 1:
                        image_selected_index = 0
                    else:
                        # >> Close progress dialog before opening image chosing dialog
                        #if self.pDialog.iscanceled(): self.pDialog_canceled = True
                        #self.pDialog.close()

                        # >> Convert list returned by scraper into a list the select window uses
                        ListItem_list = []
                        for item in image_list:
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

                selected_image = image_list[image_selected_index]

                # --- Update progress dialog ---
                #if self.pDialog_verbose:
                #    scraper_text = 'Scraping {0} with {1}. Downloading image ...'.format(A.name, scraper_obj.name)
                #    self.pDialog.update(self.progress_number, self.file_text, scraper_text)

                log_debug('Scraper._applyCandidate() Downloading selected image ...')

                # --- Resolve image URL ---
                if selected_image['is_online']:
                    image_url = selected_image['url']
                    image_ext = text_get_image_URL_extension(image_url)
                    log_debug('Selected image URL "{1}"'.format(asset_info.name, image_url))

                    # ~~~ Download image ~~~
                    image_path = asset_path_noext_FN.append(image_ext)
                    log_verb('Downloading URL  "{0}"'.format(image_url))
                    log_verb('Into local file  "{0}"'.format(image_path.getOriginalPath()))
                    try:
                        net_download_img(image_url, image_path)
                    except socket.timeout:
                        log_error('Cannot download {0} image (Timeout)'.format(asset_info.name))
                        kodi_notify_warn('Cannot download {0} image (Timeout)'.format(asset_info.name))
                else:
                    log_debug('{0} scraper: user chose local image "{1}"'.format(self.asset_info.name, selected_image['url']))
                    image_path = FileNameFactory.create(selected_image['url'])

                # ~~~ Update Kodi cache with downloaded image ~~~
                # Recache only if local image is in the Kodi cache, this function takes care of that.
                kodi_update_image_cache(image_path)
        
                rom.set_asset(asset_info, image_path)        
        
        return True

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
            'is_online': True
        }
        return assetdata

class NullScraper(Scraper):

    def __init__(self):
        super(NullScraper, self).__init__(None, None, 1, True, None, None)
        
    def scrape(self, search_term, romPath, rom):
        return True

    def getName(self):
        return 'Empty scraper'

    def _getCandidates(self, search_term, romPath, rom):
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

    def _getCandidates(self, search_term, romPath, rom):
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
    
class NfoScraper(Scraper):
    
    def __init__(self, settings, launcher, fallbackScraper = None):
                
        scraper_settings = ScraperSettings.create_from_settings(settings)
        scraper_settings.metadata_scraping_mode = 1

        super(NfoScraper, self).__init__(scraper_settings, launcher, True, [], fallbackScraper)

    def getName(self):
        return 'NFO scraper'

    def _getCandidates(self, search_term, romPath, rom):

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
    
# -------------------------------------------------- #
# Needs to be divided into separate classes for each actual scraper.
# Could only inherit OnlineScraper and implement _getCandidates()
# and _getCandidate()
# -------------------------------------------------- #
class OnlineMetadataScraper(Scraper):
    
    def __init__(self, scraper_implementation, settings, launcher, fallbackScraper = None): 
        
        self.scraper_implementation = scraper_implementation 
        scraper_settings = ScraperSettings.create_from_settings(settings)

        super(OnlineMetadataScraper, self).__init__(scraper_settings, launcher, True, [], fallbackScraper)
        
    def getName(self):
        return 'Online Metadata scraper using {0}'.format(self.scraper_implementation.name)

    def _getCandidates(self, search_term, romPath, rom):
        
        platform = self.launcher.get_platform()
        results = self.scraper_implementation.get_search(search_term, romPath.getBase_noext(), platform)

        return results
    
    def _load_metadata(self, candidate, romPath, rom):
        self.gamedata = self.scraper_implementation.get_metadata(candidate)

    def _load_assets(self, candidate, romPath, rom):
        pass

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

    def _getCandidates(self, search_term, romPath, rom):

        # ~~~~~ Search for local artwork/assets ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        rom_basename_noext = romPath.getBase_noext()
        asset_path = self.launcher.get_asset_path(self.asset_info)
        local_asset = misc_search_file_cache(asset_path, rom_basename_noext, self.asset_info.exts)

        if not local_asset:
            log_verb('LocalAssetScraper._getCandidates() Missing  {0:<9}'.format(self.asset_info.name))
            return []
        
        log_verb('LocalAssetScraper._getCandidates() Found    {0:<9} "{1}"'.format(self.asset_info.name, local_asset.getOriginalPath()))
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

    def _getCandidates(self, search_term, romPath, rom):
        log_verb('OnlineAssetScraper._getCandidates(): Scraping {0} with {1}. Searching for matching games ...'.format(self.asset_info.name, self.scraper_implementation.name))
        platform = self.launcher.get_platform()

        # --- Check cache to check if user choose a game previously ---
        log_debug('_getCandidates() Scraper ID          "{0}"'.format(self.scraper_id))
        log_debug('_getCandidates() Scraper obj name    "{0}"'.format(self.scraper_implementation.name))
        log_debug('_getCandidates() search_term          "{0}"'.format(search_term))
        log_debug('_getCandidates() ROM.getBase_noext() "{0}"'.format(romPath.getBase_noext()))
        log_debug('_getCandidates() platform            "{0}"'.format(platform))
        log_debug('_getCandidates() Entries in cache    {0}'.format(len(self.scrap_asset_cached_dic)))

        if self.scraper_id in OnlineAssetScraper.scrap_asset_cached_dic and \
           OnlineAssetScraper.scrap_asset_cached_dic[self.scraper_id]['ROM_base_noext'] == romPath.getBase_noext() and \
           OnlineAssetScraper.scrap_asset_cached_dic[self.scraper_id]['platform'] == platform:
            cached_game = OnlineAssetScraper.scrap_asset_cached_dic[self.scraper_id]['game_dic']
            log_debug('OnlineAssetScraper._getCandidates() Cache HIT. Using cached game "{0}"'.format(cached_game['display_name']))
            return [cached_game]
        
        log_debug('OnlineAssetScraper._getCandidates() Cache MISS. Calling scraper_implementation.get_search()')

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
    
    def _getCandidates(self, search_term, romPath, rom):
        
        platform = self.launcher.get_platform()
        scraper_platform = AEL_platform_to_TheGamesDB(platform)
        
        log_debug('TheGamesDbMetadataScraper::_getCandidates() search_term         "{0}"'.format(search_term))
        log_debug('TheGamesDbMetadataScraper::_getCandidates() rom_base_noext      "{0}"'.format(self.launcher.get_roms_base()))
        log_debug('TheGamesDbMetadataScraper::_getCandidates() AEL platform        "{0}"'.format(platform))
        log_debug('TheGamesDbMetadataScraper::_getCandidates() TheGamesDB platform "{0}"'.format(scraper_platform))
        
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
        self.gamedata['year']       = online_data['release_date'][:4] if 'release_date' in online_data and online_data['release_date'] is not None and online_data['release_data'] != '' else ''

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

    def _get_publishers(self, publisher_ids):

        if self.publishers is None:
            log_debug('TheGamesDbMetadataScraper::No cached publishers. Retrieving from online.')
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

        if self.genres is None:
            log_debug('TheGamesDbMetadataScraper::No cached genres. Retrieving from online.')
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

        if self.developers is None:
            log_debug('TheGamesDbMetadataScraper::No cached developers. Retrieving from online.')
            self.developers = {}
            url = 'https://api.thegamesdb.net/Developers?apikey={}'.format(self.api_key)
            developers_json = net_get_URL_as_json(url)
            for developer_id in developers_json['data']['developers']:
                self.developers[int(developer_id)] = developers_json['data']['developers'][developer_id]['name']

        developer_names = []
        for developer_id in developer_ids:
            developer_names.append(self.developers[developer_id])

        return ' / '.join(developer_names)