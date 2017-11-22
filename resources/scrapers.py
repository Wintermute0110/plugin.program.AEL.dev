from abc import ABCMeta, abstractmethod

from disk_IO import *
from utils import *
from utils_kodi import *

from scrap import *
from assets import *

class ScraperFactory(ProgressDialogStrategy):
    
    def __init__(self, settings, addon_dir):

        self.settings = settings
        self.addon_dir = addon_dir

        super(ScraperFactory, self).__init__()

        
        # --- Initialise cache used in _roms_scrap_asset() ---
        # >> This cache is used to store the selected game from the get_search() returned list.
        # >> The idea is that get_search() is used only once for each asset.
       # self.scrap_asset_cached_dic = {}


    def create(self, launcher):
        
        scan_metadata_policy    = self.settings['scan_metadata_policy']
        scan_asset_policy       = self.settings['scan_asset_policy']

        scrapers = []

        metadata_scraper = self._get_metadata_scraper(scan_metadata_policy)
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
                
                if asset_scraper is not None:
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
    def _get_metadata_scraper(self, scan_metadata_policy):

        cleanTitleScraper = CleanTitleScraper(self.settings)

        if scan_metadata_policy == 0:
            log_verb('Metadata policy: No NFO reading, no scraper. Only cleaning ROM name.')
            return cleanTitleScraper

        elif scan_metadata_policy == 1:
            log_verb('Metadata policy: Read NFO file only | Scraper OFF')
            return NfoScraper(self.settings, cleanTitleScraper)

        elif scan_metadata_policy == 2:
            log_verb('Metadata policy: Read NFO file ON, if not NFO then Scraper ON')
            
            # --- Metadata scraper ---
            scraper_implementation = scrapers_metadata[self.settings['scraper_metadata']]
            scraper_implementation.set_addon_dir(self.addon_dir.getPath())

            log_verb('Loaded metadata scraper "{0}"'.format(scraper_implementation.name))

            onlineScraper = OnlineMetadataScraper(scraper_implementation, self.settings, cleanTitleScraper)
            return NfoScraper(self.settings, onlineScraper)


        elif scan_metadata_policy == 3:
            log_verb('Metadata policy: Read NFO file OFF | Scraper ON')
            log_verb('Metadata policy: Forced scraper ON')

            scraper_implementation = scrapers_metadata[self.settings['scraper_metadata']]
            scraper_implementation.set_addon_dir(self.addon_dir.getPath())

            log_verb('Loaded metadata scraper "{0}"'.format(scraper_implementation.name))

            return OnlineMetadataScraper(scraper_implementation, self.settings, cleanTitleScraper)
        
        log_error('Invalid scan_metadata_policy value = {0}. Fallback on clean title only'.format(scan_metadata_policy))
        return cleanTitleScraper

    def _get_asset_scraper(self, scan_asset_policy, asset_kind, asset_info, launcher):

        # --- Create a cache of assets ---
        # >> misc_add_file_cache() creates a set with all files in a given directory.
        # >> That set is stored in a function internal cache associated with the path.
        # >> Files in the cache can be searched with misc_search_file_cache()
        misc_add_file_cache(launcher[asset_info.path_key])
        
        # >> Scrapers for MAME platform are different than rest of the platforms
        scraper_implementation = getScraper(asset_kind, self.settings, launcher['platform'] == 'MAME')
        
        log_verb('Loaded {0:<10} asset scraper "{1}"'.format(asset_info.name, scraper_implementation.name))
           
        if scan_asset_policy == 0:
            log_verb('Asset policy: local images only | Scraper OFF')
            return LocalAssetScraper(asset_kind, asset_info, self.settings)
        
        elif scan_asset_policy == 1:
            log_verb('Asset policy: if not Local Image then Scraper ON')
            
            onlineScraper = OnlineAssetScraper(scraper_implementation, asset_kind, asset_info, self.settings)
            return LocalAssetScraper(asset_kind, asset_info, self.settings, onlineScraper)
        
        # >> Initialise options of the thumb scraper (NOT SUPPORTED YET)
        # region = self.settings['scraper_region']
        # thumb_imgsize = self.settings['scraper_thumb_size']
        # self.scraper_asset.set_options(region, thumb_imgsize)

        return NullScraper()

            #for i, asset_kind in enumerate(ROM_ASSET_LIST):
            #    A = assets_get_info_scheme(asset_kind)
            #    romdata[A.key] = local_asset_list[i]

            # selected_title = self._roms_process_asset_policy_2(ASSET_TITLE, local_title, ROM, launcher)
            # i, asset_kind in enumerate(ROM_ASSET_LIST):
            # A = assets_get_info_scheme(asset_kind)
            # if not self.enabled_asset_list[i]:
            #     romdata[A.key] = ''
            #     log_verb('Skipped {0} (dir not configured)'.format(A.name))
            #     continue
            # if local_asset_list[i]:
            #     log_verb('Asset policy: local {0} FOUND | Scraper OFF'.format(A.name))
            #     romdata[A.key] = local_asset_list[i]
            # else:
            #     log_verb('Asset policy: local {0} NOT found | Scraper ON'.format(A.name))
            #     # >> Set the asset-specific scraper before calling _roms_scrap_asset()
            #     romdata[A.key] = self._roms_scrap_asset(self.scraper_dic[A.key], asset_kind,
            #                                             local_asset_list[i], ROM, launcher)
            #
        pass

class Scraper():
    __metaclass__ = ABCMeta
    
    def __init__(self, settings, fallbackScraper = None):
                
        self.settings = settings
        self.fallbackScraper = fallbackScraper
        
        # id="metadata_scraper_mode" values="Semi-automatic|Automatic"
        self.semi_automatic_scraping    = self.settings['metadata_scraper_mode']

    def scrape(self, searchTerm, romPath, rom):
                
        results = self._getCandidates(searchTerm, romPath, rom)
        log_debug('Scraper found {0} result/s'.format(len(results)))

        if not results or len(results) == 0:
            log_verb('Scraper found no games after searching.')
            
            if self.fallbackScraper is not None:
                return self.fallbackScraper.scrape(searchTerm, romPath, rom)

        selectgame = 0
        if len(results) > 1 and self.semi_automatic_scraping == 0:
            log_debug('Metadata semi-automatic scraping')
            # >> Close progress dialog (and check it was not canceled)
            # ?? todo again

            # >> Display corresponding game list found so user choses
            dialog = xbmcgui.Dialog()
            rom_name_list = []
            for game in results: 
                rom_name_list.append(game['display_name'])

            selectgame = dialog.select('Select game for ROM {0}'.format(romPath.getBase_noext()), rom_name_list)
            if selectgame < 0: selectgame = 0

            # >> Open progress dialog again
            # ?? todo again
        
        self._loadCandidate(results[selectgame])

        #if not gamedata:
        #    log_verb('Metadata scraper did not get the correct data.')
        #    if self.fallbackScraper is not None:
        #        return self.fallbackScraper.scrape(searchTerm, romPath, rom)

        # --- Grab metadata for selected game ---
        
        scraper_applied = self._applyCandidate(romPath, rom)
                
        if not scraper_applied and self.fallbackScraper is not None:
            scraper_applied = self.fallbackScraper.scrape(searchTerm, romPath, rom)
        
        return scraper_applied


    @abstractmethod
    def _getCandidates(self, searchTerm, romPath, rom):
        pass
    
    @abstractmethod
    def _loadCandidate(self, candidate):        
        pass

    @abstractmethod
    def _applyCandidate(self, romPath, rom):
        pass

class NullScraper(Scraper):

    def _getCandidates(self, searchTerm, romPath, rom):
        return None

    def _loadCandidate(self, candidate):
        return None

    def _applyCandidate(self, romPath, rom):
        return True

class CleanTitleScraper(Scraper):

    def __init__(self, settings):
        
        self.scan_clean_tags = settings['scan_clean_tags']
        super(CleanTitleScraper, self).__init__(settings)

    def _getCandidates(self, searchTerm, romPath, rom):
        games = []
        games.append('dummy')
        return games

    def _loadCandidate(self, candidate):
        return super(CleanTitleScraper, self)._loadCandidate(candidate)

    def _applyCandidate(self, romPath, rom):        

        log_debug('Only cleaning ROM name.')
        rom['m_name'] = text_format_ROM_title(romPath.getBase_noext(), self.scan_clean_tags)
        return True


class NfoScraper(Scraper):

    def _getCandidates(self, searchTerm, romPath, rom):
        NFO_file = romPath.switchExtension('nfo')
        log_debug('Testing NFO file "{0}"'.format(NFO_file.getOriginalPath()))

        games = []
        if NFO_file.exists():
            games.append(NFO_file)
        else:
            log_debug('NFO file not found.')

        return games

    def _loadCandidate(self, candidate):
        
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
    
    def __init__(self, scraper_implementation, settings, fallbackScraper = None): 
        
        self.scraper_implementation = scraper_implementation
        self.scan_ignore_scrapped_title = settings['scan_ignore_scrap_title']

        super(OnlineMetadataScraper, self).__init__(settings, fallbackScraper)

    def _getCandidates(self, searchTerm, romPath, rom):
        
        platform = rom['platform']
        results = self.scraper_implementation.get_search(searchTerm, romPath.getBase_noext(), platform)

        return results

    def _loadCandidate(self, candidate):
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
    
    def __init__(self, asset_kind, asset_info, settings, fallbackScraper = None): 
        
        self.asset_kind = asset_kind
        self.asset_info = asset_info

        super(LocalAssetScraper, self).__init__(settings, fallbackScraper)

    def _getCandidates(self, searchTerm, romPath, rom):
        return super(LocalAssetScraper, self)._getCandidates(searchTerm, romPath, rom)

    def _loadCandidate(self, candidate):
        return super(LocalAssetScraper, self)._loadCandidate(candidate)

    def _applyCandidate(self, rom):
                
        A = assets_get_info_scheme(asset_kind)
        rom[A.key] = local_asset_list[i]

class OnlineAssetScraper(Scraper):
    
    def __init__(self, scraper_implementation, asset_kind, asset_info, settings, fallbackScraper = None): 

        self.scraper_implementation = scraper_implementation
        
        self.asset_kind = asset_kind
        self.asset_info = asset_info
        
        super(OnlineAssetScraper, self).__init__(settings, fallbackScraper)
    
    def _getCandidates(self, searchTerm, romPath, rom):
        return super(OnlineAssetScraper, self)._getCandidates(searchTerm, romPath, rom)

    def _loadCandidate(self, candidate):
        return super(OnlineAssetScraper, self)._loadCandidate(candidate)

    def _applyCandidate(self, rom):
                        
        asset_info = assets_get_info_scheme(asset_kind)
        # >> Set the asset-specific scraper before calling _roms_scrap_asset()
        rom[asset_info.key] = self._roms_scrap_asset(self.scraper_implementation, asset_kind, local_asset_list[i], ROM, launcher)


        # ~~~ Asset scraping ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # settings.xml -> id="scan_asset_policy" default="0" values="Local Assets|Local Assets + Scrapers|Scrapers only"
        scan_asset_policy = self.settings['scan_asset_policy']
        if scan_asset_policy == 0:
            log_verb('Asset policy: local images only | Scraper OFF')
            for i, asset_kind in enumerate(ROM_ASSET_LIST):
                A = assets_get_info_scheme(asset_kind)
                romdata[A.key] = local_asset_list[i]

        elif scan_asset_policy == 1:
            log_verb('Asset policy: if not Local Image then Scraper ON')
            # selected_title = self._roms_process_asset_policy_2(ASSET_TITLE, local_title, ROM, launcher)
            for i, asset_kind in enumerate(ROM_ASSET_LIST):
                A = assets_get_info_scheme(asset_kind)
                if not self.enabled_asset_list[i]:
                    romdata[A.key] = ''
                    log_verb('Skipped {0} (dir not configured)'.format(A.name))
                    continue
                if local_asset_list[i]:
                    log_verb('Asset policy: local {0} FOUND | Scraper OFF'.format(A.name))
                    romdata[A.key] = local_asset_list[i]
                else:
                    log_verb('Asset policy: local {0} NOT found | Scraper ON'.format(A.name))
                    # >> Set the asset-specific scraper before calling _roms_scrap_asset()
                    romdata[A.key] = self._roms_scrap_asset(self.scraper_dic[A.key], asset_kind,
                                                            local_asset_list[i], ROM, launcher)

        elif scan_asset_policy == 2:
            log_verb('Asset policy: scraper will overwrite local assets | Scraper ON')
            # selected_title = self._roms_scrap_asset(ASSET_TITLE, local_title, ROM, launcher)
            for i, asset_kind in enumerate(ROM_ASSET_LIST):
                A = assets_get_info_scheme(asset_kind)
                if not self.enabled_asset_list[i]:
                    romdata[A.key] = ''
                    log_verb('Skipped {0} (dir not configured)'.format(A.name))
                    continue
                log_verb('Asset policy: local {0} NOT found | Scraper ON'.format(A.name))
                # >> Set the asset-specific scraper before calling _roms_scrap_asset()
                romdata[A.key] = self._roms_scrap_asset(self.scraper_dic[A.key], asset_kind, 
                                                        local_asset_list[i], ROM, launcher)