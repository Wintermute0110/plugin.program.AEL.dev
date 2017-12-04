from abc import ABCMeta, abstractmethod

from disk_IO import *
from utils import *
from utils_kodi import *
from utils_kodi_cache import *

from scrap import *
from assets import *

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
        for i, asset_kind in enumerate(ROM_ASSET_LIST):
            
            asset_info = assets_get_info_scheme(asset_kind)
            if not launcher[asset_info.path_key]:
                unconfigured_name_list.append(asset_info.name)
                log_verb('ScraperFactory.create() {0:<9} path unconfigured'.format(asset_info.name))
            else:
                log_debug('ScraperFactory.create() {0:<9} path configured'.format(asset_info.name))
                asset_scraper = self._get_asset_scraper(scan_asset_policy, asset_kind, asset_info, launcher)
                
                if asset_scraper:
                    scrapers.append(asset_scraper)
                
            self._updateProgress((100*i)/len(ROM_ASSET_LIST))
            
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
        duplicated_name_list = asset_get_duplicated_dir_list(launcher)

        if duplicated_name_list:
            duplicated_asset_srt = ', '.join(duplicated_name_list)
            log_info('Duplicated asset dirs: {0}'.format(duplicated_asset_srt))
            kodi_dialog_OK('Duplicated asset directories: {0}. '.format(duplicated_asset_srt) +
                           'Change asset directories before continuing.')
            return True
        
        log_info('No duplicated asset dirs found')
        return False        

    # >> Determine metadata action based on policy
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
            scraper_implementation = scrapers_metadata[self.settings['scraper_metadata']]
            scraper_implementation.set_addon_dir(self.addon_dir.getPath())

            log_verb('Loaded metadata scraper "{0}"'.format(scraper_implementation.name))

            onlineScraper = OnlineMetadataScraper(scraper_implementation, self.settings, launcher, cleanTitleScraper)
            return NfoScraper(self.settings, launcher, onlineScraper)


        elif scan_metadata_policy == 3:
            log_verb('Metadata policy: Read NFO file OFF | Scraper ON')
            log_verb('Metadata policy: Forced scraper ON')

            scraper_implementation = scrapers_metadata[self.settings['scraper_metadata']]
            scraper_implementation.set_addon_dir(self.addon_dir.getPath())

            log_verb('Loaded metadata scraper "{0}"'.format(scraper_implementation.name))

            return OnlineMetadataScraper(scraper_implementation, self.settings, launcher, cleanTitleScraper)
        
        log_error('Invalid scan_metadata_policy value = {0}. Fallback on clean title only'.format(scan_metadata_policy))
        return cleanTitleScraper

    def _get_asset_scraper(self, scan_asset_policy, asset_kind, asset_info, launcher):
                
        # >> Scrapers for MAME platform are different than rest of the platforms
        scraper_implementation = getScraper(asset_kind, self.settings, launcher['platform'] == 'MAME')
        
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

class Scraper():
    __metaclass__ = ABCMeta
    
    def __init__(self, settings, launcher, scraping_mode, fallbackScraper = None):
                
        self.settings = settings
        self.launcher = launcher
        
        # --- Set scraping mode ---
        # values="Semi-automatic|Automatic"
        self.scraping_mode = scraping_mode
        
        self.fallbackScraper = fallbackScraper

    def scrape(self, searchTerm, romPath, rom):
                
        results = self._getCandidates(searchTerm, romPath, rom)
        log_debug('Scraper \'{0}\' found {1} result/s'.format(self.getName(), len(results)))

        if not results or len(results) == 0:
            log_verb('Scraper \'{0}\' found no games after searching.'.format(self.getName()))
            
            if self.fallbackScraper:
                return self.fallbackScraper.scrape(searchTerm, romPath, rom)

            return False

        selected_candidate = 0
        if len(results) > 1 and self.scraping_mode == 0:
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
        
        self._loadCandidate(results[selected_candidate], romPath)
                
        scraper_applied = self._applyCandidate(romPath, rom)
                
        if not scraper_applied and self.fallbackScraper is not None:
            log_verb('Scraper \'{0}\' did not get the correct data. Using fallback scraping method: {1}.'.format(self.getName(), self.fallbackScraper.getName()))
            scraper_applied = self.fallbackScraper.scrape(searchTerm, romPath, rom)
        
        log_verb('Scraper \'{0}\' could not be applied.'.format(self.getName()))
        return scraper_applied
    
    @abstractmethod
    def getName(self):
        return ''

    @abstractmethod
    def _getCandidates(self, searchTerm, romPath, rom):
        return []
    
    @abstractmethod
    def _loadCandidate(self, candidate, romPath):        
        pass

    @abstractmethod
    def _applyCandidate(self, romPath, rom):
        pass

class NullScraper(Scraper):

    def __init__(self):
        super(NullScraper, self).__init__(None, None, 1, None)
        
    def scrape(self, searchTerm, romPath, rom):
        return True

    def getName(self):
        return 'Empty scraper'

    def _getCandidates(self, searchTerm, romPath, rom):
        return []

    def _loadCandidate(self, candidate, romPath):
        return None

    def _applyCandidate(self, romPath, rom):
        return True

class CleanTitleScraper(Scraper):

    def __init__(self, settings, launcher):
        
        self.scan_clean_tags = settings['scan_clean_tags']
        super(CleanTitleScraper, self).__init__(settings, launcher, 1)

    def getName(self):
        return 'Clean title only scraper'

    def _getCandidates(self, searchTerm, romPath, rom):
        games = []
        games.append('dummy')
        return games

    def _loadCandidate(self, candidate, romPath):
        return super(CleanTitleScraper, self)._loadCandidate(candidate, romPath)

    def _applyCandidate(self, romPath, rom):        

        log_debug('Only cleaning ROM name.')
        rom['m_name'] = text_format_ROM_title(romPath.getBase_noext(), self.scan_clean_tags)
        return True


class NfoScraper(Scraper):
    
    def __init__(self, settings, launcher, fallbackScraper = None):

        super(NfoScraper, self).__init__(settings, launcher, 1, fallbackScraper)

    def getName(self):
        return 'NFO scraper'

    def _getCandidates(self, searchTerm, romPath, rom):
        NFO_file = romPath.switchExtension('nfo')
        log_debug('Testing NFO file "{0}"'.format(NFO_file.getOriginalPath()))

        games = []
        if NFO_file.exists():
            games.append(NFO_file)
        else:
            log_debug('NFO file not found.')

        return games

    def _loadCandidate(self, candidate, romPath):
        
        log_debug('NFO file found. Loading it.')
        self.nfo_dic = fs_import_NFO_file_scanner(candidate)

    def _applyCandidate(self, romPath, rom):
        
        # NOTE <platform> is chosen by AEL, never read from NFO files
        rom['m_name']      = self.nfo_dic['title']     # <title>
        rom['m_year']      = self.nfo_dic['year']      # <year>
        rom['m_genre']     = self.nfo_dic['genre']     # <genre>
        rom['m_developer'] = self.nfo_dic['publisher'] if 'publisher' in self.nfo_dic else self.nfo_dic['developer'] # <publisher> rename to <developer>
        rom['m_plot']      = self.nfo_dic['plot']      # <plot>

        # romdata['m_nplayers']  = nfo_dic['nplayers']  # <nplayers>
        # romdata['m_esrb']      = nfo_dic['esrb']      # <esrb>
        # romdata['m_rating']    = nfo_dic['rating']    # <rating>
        return True


# -------------------------------------------------- #
# Needs to be divided into separate classes for each actual scraper.
# Could only inherit OnlineScraper and implement _getCandidates()
# and _getCandidate()
# -------------------------------------------------- #
class OnlineMetadataScraper(Scraper):
    
    def __init__(self, scraper_implementation, settings, launcher, fallbackScraper = None): 
        
        self.scraper_implementation = scraper_implementation
        self.scan_ignore_scrapped_title = settings['scan_ignore_scrap_title']
        
        scraping_mode = settings['metadata_scraper_mode']
        super(OnlineMetadataScraper, self).__init__(settings, launcher, scraping_mode, fallbackScraper)
        
    def getName(self):
        return 'Online Metadata scraper using {0}'.format(self.scraper_implementation.name)

    def _getCandidates(self, searchTerm, romPath, rom):
        
        platform = self.launcher['platform']
        results = self.scraper_implementation.get_search(searchTerm, romPath.getBase_noext(), platform)

        return results

    def _loadCandidate(self, candidate, romPath):
        self.gamedata = self.scraper_implementation.get_metadata(candidate)
        
    def _applyCandidate(self, romPath, rom):
        
        if not self.gamedata:
            log_verb('Metadata scraper did not get the correct data.')
            return False

        # --- Put metadata into ROM dictionary ---
        if self.scan_ignore_scrapped_title:
            rom['m_name'] = text_format_ROM_title(ROM.getBase_noext(), scan_clean_tags)
            log_debug("User wants to ignore scraper name. Setting name to '{0}'".format(rom['m_name']))
        else:
            rom['m_name'] = self.gamedata['title']
            log_debug("User wants scrapped name. Setting name to '{0}'".format(rom['m_name']))

        rom['m_year']      = self.gamedata['year']
        rom['m_genre']     = self.gamedata['genre']
        rom['m_developer'] = self.gamedata['developer']
        rom['m_nplayers']  = self.gamedata['nplayers']
        rom['m_esrb']      = self.gamedata['esrb']
        rom['m_plot']      = self.gamedata['plot']
        
        return True

class LocalAssetScraper(Scraper):
    
    def __init__(self, asset_kind, asset_info, settings, launcher, fallbackScraper = None): 
        
        self.asset_kind = asset_kind
        self.asset_info = asset_info
        
        scraping_mode = settings['asset_scraper_mode']
        
        # --- Create a cache of assets ---
        # >> misc_add_file_cache() creates a set with all files in a given directory.
        # >> That set is stored in a function internal cache associated with the path.
        # >> Files in the cache can be searched with misc_search_file_cache()
        misc_add_file_cache(launcher[asset_info.path_key])

        super(LocalAssetScraper, self).__init__(settings, launcher, scraping_mode, fallbackScraper)
        
    def getName(self):
        return 'Local assets scraper'

    def _getCandidates(self, searchTerm, romPath, rom):

        # ~~~~~ Search for local artwork/assets ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        rom_basename_noext = romPath.getBase_noext()
        local_asset = misc_search_file_cache(self.launcher[self.asset_info.path_key], rom_basename_noext, self.asset_info.exts)

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

    def _loadCandidate(self, candidate, romPath):
        
        self.image_url = candidate['file'].getOriginalPath()
        log_debug('OnlineAssetScraper._applyCandidate() local_asset_path "{0}"'.format(self.image_url))

    def _applyCandidate(self, romPath, rom):
                
        log_debug('{0} scraper: user chose local image "{1}"'.format(self.asset_info.name, self.image_url))
        rom[self.asset_info.key] = self.image_url
        
        return True

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

        self.asset_directory = FileName(launcher[asset_info.path_key])
        scraping_mode = settings['asset_scraper_mode']
        
        # --- Initialise cache used in OnlineAssetScraper() as a static variable ---
        # >> This cache is used to store the selected game from the get_search() returned list.
        # >> The idea is that get_search() is used only once for each asset.
        if OnlineAssetScraper.scrap_asset_cached_dic is None:
            OnlineAssetScraper.scrap_asset_cached_dic = {}
        
        super(OnlineAssetScraper, self).__init__(settings, launcher, scraping_mode, fallbackScraper)
    
    def getName(self):
        return 'Online assets scraper for \'{0}\' ({1})'.format(self.asset_info.name, self.scraper_implementation.name)

    def _getCandidates(self, searchTerm, romPath, rom):
        log_verb('OnlineAssetScraper._getCandidates(): Scraping {0} with {1}. Searching for matching games ...'.format(self.asset_info.name, self.scraper_implementation.name))
        platform = self.launcher['platform']

        # --- Check cache to check if user choose a game previously ---
        log_debug('_getCandidates() Scraper ID          "{0}"'.format(self.scraper_id))
        log_debug('_getCandidates() Scraper obj name    "{0}"'.format(self.scraper_implementation.name))
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
        search_results = self.scraper_implementation.get_search(searchTerm, romPath.getBase_noext(), platform)
        return search_results

    def _loadCandidate(self, candidate, romPath):
        
         # --- Cache selected game from get_search() ---
        OnlineAssetScraper.scrap_asset_cached_dic[self.scraper_id] = {
            'ROM_base_noext' : romPath.getBase_noext(),
            'platform' : self.launcher['platform'],
            'game_dic' : candidate
        }

        log_error('_loadCandidate() Caching selected game "{0}"'.format(candidate['display_name']))
        log_error('_loadCandidate() Scraper object ID {0} (name {1})'.format(self.scraper_id, self.scraper_implementation.name))
        
        self.selected_game = OnlineAssetScraper.scrap_asset_cached_dic[self.scraper_id]['game_dic']

    def _applyCandidate(self, romPath, rom):
        
        asset_path_noext_FN = assets_get_path_noext_DIR(self.asset_info, self.asset_directory, romPath)
        log_debug('OnlineAssetScraper._applyCandidate() asset_path_noext "{0}"'.format(asset_path_noext_FN.getOriginalPath()))

        image_list = self.scraper_implementation.get_images(self.selected_game, self.asset_kind)
        log_verb('{0} scraper returned {1} images'.format(self.asset_info.name, len(image_list)))
        if not image_list:
            log_debug('{0} scraper get_images() returned no images.'.format(self.asset_info.name))
            return False

         # --- Semi-automatic scraping (user choses an image from a list) ---
        if self.scraping_mode == 0:
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
                    listitem_obj = xbmcgui.ListItem(label = item['name'], label2 = item['URL'])
                    listitem_obj.setArt({'icon' : item['URL']})
                    ListItem_list.append(listitem_obj)

                image_selected_index = xbmcgui.Dialog().select('Select {0} image'.format(self.asset_info.name),
                                                               list = ListItem_list, useDetails = True)
                log_debug('{0} dialog returned index {1}'.format(self.asset_info.name, image_selected_index))
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

        log_debug('OnlineAssetScraper._applyCandidate() Downloading selected image ...')

        # --- Resolve image URL ---
        image_url, image_ext = self.scraper_implementation.resolve_image_URL(selected_image)
        log_debug('Selected image URL "{1}"'.format(self.asset_info.name, image_url))

        # ~~~ Download image ~~~
        image_path = asset_path_noext_FN.append(image_ext)
        log_verb('Downloading URL  "{0}"'.format(image_url))
        log_verb('Into local file  "{0}"'.format(image_path.getOriginalPath()))
        try:
            net_download_img(image_url, image_path)
        except socket.timeout:
            log_error('Cannot download {0} image (Timeout)'.format(self.asset_info.name))
            kodi_notify_warn('Cannot download {0} image (Timeout)'.format(self.asset_info.name))

        # ~~~ Update Kodi cache with downloaded image ~~~
        # Recache only if local image is in the Kodi cache, this function takes care of that.
        kodi_update_image_cache(image_path)

        rom[self.asset_info.key] = image_path.getOriginalPath()
        
        return True
  
    #
    # Returns a valid filename of the downloaded scrapped image, filename of local image
    # or empty string if scraper finds nothing or download failed.
    #
    def _roms_scrap_asset(self, scraper_obj, asset_kind, local_asset_path, ROM):
        # >> By default always use local image in case scraper fails
        ret_asset_path = local_asset_path

        # --- Customise function depending of image_king ---
        A = assets_get_info_scheme(asset_kind)
        asset_directory  = FileName(self.launcher[A.path_key])
        asset_path_noext_FN = assets_get_path_noext_DIR(A, asset_directory, ROM)
        platform = self.launcher['platform']

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
            local_asset_obj = FileName(local_asset_path)
            if local_asset_obj.exists():
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
            image_path = asset_path_noext_FN.append(image_ext)
            log_verb('Downloading URL  "{0}"'.format(image_url))
            log_verb('Into local file  "{0}"'.format(image_path.getPath()))
            try:
                net_download_img(image_url, image_path)
            except socket.timeout:
                kodi_notify_warn('Cannot download {0} image (Timeout)'.format(A.name))

            # ~~~ Update Kodi cache with downloaded image ~~~
            # Recache only if local image is in the Kodi cache, this function takes care of that.
            kodi_update_image_cache(image_path)

            # --- Return value is downloaded image ---
            ret_asset_path = image_path.getOriginalPath()
        else:
            log_debug('{0} scraper: user chose local image "{1}"'.format(A.name, image_url))
            ret_asset_path = image_url

        # --- Returned value ---
        return ret_asset_path