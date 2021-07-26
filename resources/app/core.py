# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Default launchers
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

import logging
import typing
import re

# --- AEL packages ---
from ael import report, platforms, settings
from ael.utils import io, kodi
from ael.executors import ExecutorFactoryABC
from ael.launchers import LauncherABC, ExecutionSettings
from ael.scanners import RomScannerStrategy, ROMCandidateABC, ROMFileCandidate, ROMData, MultiDiscInfo

from resources.app import globals

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# Default implementation for launching anything ROMs or item based using an application.
# Inherit from this base class to implement your own specific ROM App launcher.
# -------------------------------------------------------------------------------------------------
class AppLauncher(LauncherABC):

    def __init__(self, 
        executorFactory: ExecutorFactoryABC, 
        execution_settings: ExecutionSettings,
        launcher_settings: dict):
        super(AppLauncher, self).__init__(executorFactory, execution_settings, launcher_settings)

    # --------------------------------------------------------------------------------------------
    # Core methods
    # --------------------------------------------------------------------------------------------
    def get_name(self) -> str: return 'App Launcher'
    
    def get_launcher_addon_id(self) -> str: 
        return '{}.AppLauncher'.format(globals.addon_id)

    # --------------------------------------------------------------------------------------------
    # Launcher build wizard methods
    # --------------------------------------------------------------------------------------------
    #
    # Creates a new launcher using a wizard of dialogs. Called by parent build() method.
    #
    def _builder_get_wizard(self, wizard):    
        wizard = kodi.WizardDialog_FileBrowse(wizard, 'application', 'Select the launcher application', 1, self._builder_get_appbrowser_filter)
        wizard = kodi.WizardDialog_Dummy(wizard, 'args', '', self._builder_get_arguments_from_application_path)
        wizard = kodi.WizardDialog_Keyboard(wizard, 'args', 'Application arguments')
        
        return wizard
    
    def _editor_get_wizard(self, wizard):
        wizard = kodi.WizardDialog_YesNo(wizard, 'change_app', 'Change application?', 'Set a different application? Currently "{}"'.format(self.launcher_settings['application']))
        wizard = kodi.WizardDialog_FileBrowse(wizard, 'application', 'Select the launcher application', 1, self._builder_get_appbrowser_filter, 
                                              None, self._builder_wants_to_change_app)
        wizard = kodi.WizardDialog_Keyboard(wizard, 'args', 'Application arguments')
        
        return wizard
            
    def _build_post_wizard_hook(self):        
        self.non_blocking = True
        app = self.launcher_settings['application']
        app_FN = io.FileName(app)
        
        self.launcher_settings['secname'] = app_FN.getBase()
        return True
    
    def _builder_get_arguments_from_application_path(self, input, item_key, launcher_args):
        if input: return input
        app = launcher_args['application']
        appPath = io.FileName(app)
        default_arguments = platforms.emudata_get_program_arguments(appPath.getBase())

        return default_arguments
    
    #
    # Wizard helper, when a user wants to change the application path.
    #
    def _builder_wants_to_change_app(self, item_key, launcher):
        return launcher[item_key] == True

    # ---------------------------------------------------------------------------------------------
    # Execution methods
    # ---------------------------------------------------------------------------------------------
    def get_application(self) -> str:
        if 'application' not in self.launcher_settings:
            logger.error('LauncherABC::launch() No application argument defined')            
            return None
        
        application = io.FileName(self.launcher_settings['application'])
        
        # --- Check for errors and abort if errors found ---
        if not application.exists():
            logger.error('Launching app not found "{0}"'.format(application.getPath()))
            kodi.notify_warn('App {0} not found.'.format(application.getPath()))
            return None
        
        return application.getPath()
        
class RomFolderScanner(RomScannerStrategy):
    
    # --------------------------------------------------------------------------------------------
    # Core methods
    # --------------------------------------------------------------------------------------------
    def get_name(self) -> str: return 'Folder scanner'
    
    def get_scanner_addon_id(self) -> str: 
        return '{}.FolderScanner'.format(globals.addon_id)

    def get_rom_path(self) -> io.FileName:
        str_rom_path = self.scanner_settings['rompath'] if 'rompath' in self.scanner_settings else None
        if str_rom_path is None: return io.FileName("/")
        return io.FileName(str_rom_path)

    def get_rom_extensions(self) -> list:        
        if not 'romext' in self.scanner_settings:
            return []
        return self.scanner_settings['romext'].split("|")
    
    def scan_recursive(self) -> bool:
        return self.scanner_settings['scan_recursive'] if 'scan_recursive' in self.scanner_settings else False
    
    def ignore_bios(self) -> bool:
        return self.scanner_settings['ignore_bios'] if 'ignore_bios' in self.scanner_settings else True
    
    def supports_multidisc(self) -> bool:
        return self.scanner_settings['multidisc']

    def _configure_get_wizard(self, wizard) -> kodi.WizardDialog:
        
        wizard = kodi.WizardDialog_FileBrowse(wizard, 'rompath', 'Select the ROMs path',0, '')
        wizard = kodi.WizardDialog_YesNo(wizard, 'scan_recursive','Scan recursive', 'Scan through this directory and any subdirectories?')
        wizard = kodi.WizardDialog_Dummy(wizard, 'romext', '', self._configuration_get_extensions_from_app_path)
        wizard = kodi.WizardDialog_Keyboard(wizard, 'romext','Set files extensions, use "|" as separator. (e.g lnk|cbr)')
        wizard = kodi.WizardDialog_YesNo(wizard, 'multidisc','Supports multi-disc ROMs?', 'Does this ROM collection contain multi-disc ROMS?')
        wizard = kodi.WizardDialog_YesNo(wizard, 'ignore_bios','Ignore BIOS', 'Ignore any BIOS file found during scanning?')
        
        return wizard
      
    def _configure_post_wizard_hook(self):
        path = self.scanner_settings['rompath']
        self.scanner_settings['secname'] = path
        return True
            
    # ~~~ Scan for new files (*.*) and put them in a list ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def _getCandidates(self, launcher_report: report.Reporter) -> typing.List[ROMCandidateABC]:
        self.progress_dialog.startProgress('Scanning and caching files in ROM path ...')
        files = []
        
        rom_path = self.get_rom_path()
        launcher_report.write('Scanning files in {}'.format(rom_path.getPath()))

        if self.scan_recursive():
            logger.info('Recursive scan activated')
            files = rom_path.recursiveScanFilesInPath('*.*')
        else:
            logger.info('Recursive scan not activated')
            files = rom_path.scanFilesInPath('*.*')

        num_files = len(files)
        launcher_report.write('  File scanner found {} files'.format(num_files))
        self.progress_dialog.endProgress()
        
        return [*(ROMFileCandidate(f) for f in files)]

    # --- Remove dead entries -----------------------------------------------------------------
    def _removeDeadRoms(self, candidates: typing.List[ROMCandidateABC], roms: typing.List[ROMData]):
        num_roms = len(roms)
        num_removed_roms = 0
        if num_roms == 0:
            logger.info('Launcher is empty. No dead ROM check.')
            return num_removed_roms
        
        logger.debug('Starting dead items scan')
        i = 0
            
        self.progress_dialog.startProgress('Checking for dead ROMs ...', num_roms)
            
        for rom in reversed(roms):
            fileName = rom.get_file()
            logger.debug('Searching {0}'.format(fileName.getPath()))
            self.progress_dialog.updateProgress(i)
            
            if not fileName.exists():
                logger.debug('Not found')
                logger.debug('Deleting from DB {0}'.format(fileName.getPath()))
                roms.remove(rom)
                num_removed_roms += 1
            i += 1
            
        self.progress_dialog.endProgress()

        return num_removed_roms

    # ~~~ Now go processing item by item ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def _processFoundItems(self, 
                           candidates: typing.List[ROMCandidateABC], 
                           roms:typing.List[ROMData],
                           launcher_report: report.Reporter) -> typing.List[ROMData]:

        num_items = len(candidates)    
        new_roms:typing.List[ROMData] = []

        self.progress_dialog.startProgress('Scanning found items', num_items)
        logger.debug('============================== Processing ROMs ==============================')
        launcher_report.write('Processing files ...')
        num_items_checked = 0
        
        allowedExtensions = self.get_rom_extensions()
        scanner_multidisc = self.supports_multidisc()

        skip_if_scraping_failed = settings.getSettingAsBool('scan_skip_on_scraping_failure')
        for candidate in sorted(candidates, key=lambda c: c.get_sort_value()):
            file_candidate:ROMFileCandidate = candidate
            ROM_file = file_candidate.file
            
            self.progress_dialog.updateProgress(num_items_checked)
            
            # --- Get all file name combinations ---
            launcher_report.write('>>> {0}'.format(ROM_file.getPath()))

            # ~~~ Update progress dialog ~~~
            file_text = 'ROM {0}'.format(ROM_file.getBase())
            self.progress_dialog.updateMessage('{}\nChecking if has ROM extension ...'.format(file_text))
                        
            # --- Check if filename matchs ROM extensions ---
            # The recursive scan has scanned all files. Check if this file matches some of 
            # the ROM extensions. If this file isn't a ROM skip it and go for next one in the list.
            processROM = False

            for ext in allowedExtensions:
                if ROM_file.getExt() == '.' + ext:
                    launcher_report.write("  Expected '{0}' extension detected".format(ext))
                    processROM = True
                    break

            if not processROM: 
                launcher_report.write('  File has not an expected extension. Skipping file.')
                continue
                        
            # --- Check if ROM belongs to a multidisc set ---
            self.progress_dialog.updateMessage('{}\nChecking if ROM belongs to multidisc set..'.format(file_text))
                       
            MultiDiscInROMs = False
            MDSet = MultiDiscInfo.get_multidisc_info(ROM_file)
            if MDSet.isMultiDisc and scanner_multidisc:
                logger.info('ROM belongs to a multidisc set.')
                logger.info('isMultiDisc "{0}"'.format(MDSet.isMultiDisc))
                logger.info('setName     "{0}"'.format(MDSet.setName))
                logger.info('discName    "{0}"'.format(MDSet.discName))
                logger.info('extension   "{0}"'.format(MDSet.extension))
                logger.info('order       "{0}"'.format(MDSet.order))
                launcher_report.write('  ROM belongs to a multidisc set.')
                
                # >> Check if the set is already in launcher ROMs.
                MultiDisc_rom_id = None
                for new_rom in new_roms:
                    temp_FN = new_rom.get_file()
                    if temp_FN.getBase() == MDSet.setName:
                        MultiDiscInROMs  = True
                        MultiDisc_rom    = new_rom
                        break

                logger.info('MultiDiscInROMs is {0}'.format(MultiDiscInROMs))

                # >> If the set is not in the ROMs then this ROM is the first of the set.
                # >> Add the set
                if not MultiDiscInROMs:
                    logger.info('First ROM in the set. Adding to ROMs ...')
                    # >> Manipulate ROM so filename is the name of the set
                    ROM_dir = io.FileName(ROM_file.getDir())
                    ROM_file_original = ROM_file
                    ROM_temp = ROM_dir.pjoin(MDSet.setName)
                    logger.info('ROM_temp P "{0}"'.format(ROM_temp.getPath()))
                    ROM_file = ROM_temp
                # >> If set already in ROMs, just add this disk into the set disks field.
                else:
                    logger.info('Adding additional disk "{0}"'.format(MDSet.discName))
                    MultiDisc_rom.add_disk(MDSet.discName)
                    # >> Reorder disks like Disk 1, Disk 2, ...
                    
                    # >> Process next file
                    logger.info('Processing next file ...')
                    continue
            elif MDSet.isMultiDisc and not scanner_multidisc:
                launcher_report.write('  ROM belongs to a multidisc set but Multidisc support is disabled.')
            else:
                launcher_report.write('  ROM does not belong to a multidisc set.')
 
            # --- Check that ROM is not already in the list of ROMs ---
            # >> If file already in ROM list skip it
            self.progress_dialog.updateMessage('{}\nChecking if ROM is not already in collection...'.format(file_text))
            repeatedROM = False
            for rom in roms:
                rpath = rom.get_file() 
                if rpath == ROM_file: 
                    repeatedROM = True
        
            if repeatedROM:
                launcher_report.write('  File already into ROM list. Skipping file.')
                continue
            else:
                launcher_report.write('  File not in ROM list. Processing it ...')

            # --- Ignore BIOS ROMs ---
            # Name of bios is: '[BIOS] Rom name example (Rev A).zip'
            if self.ignore_bios:
                BIOS_re = re.findall('\[BIOS\]', ROM_file.getBase())
                if len(BIOS_re) > 0:
                    logger.info("BIOS detected. Skipping ROM '{0}'".format(ROM_file.getPath()))
                    continue

            # ~~~~~ Process new ROM and add to the list ~~~~~
            # --- Create new rom dictionary ---
            # >> Database always stores the original (non transformed/manipulated) path
            new_rom = ROMData()
            new_rom.set_file(ROM_file)
                                    
            # checksums
            ROM_checksums = ROM_file_original if MDSet.isMultiDisc and scanner_multidisc else ROM_file

            # scraping_succeeded = True
            # self.progress_dialog.updateMessages(file_text, 'Scraping {0}...'.format(ROM_file.getBaseNoExt()))
            # try:
            #     self.scraping_strategy.scanner_process_ROM(new_rom, ROM_checksums)
            # except Exception as ex:
            #     scraping_succeeded = False        
            #     logger.error('(Exception) Object type "{}"'.format(type(ex)))
            #     logger.error('(Exception) Message "{}"'.format(str(ex)))
            #     logger.warning('Could not scrape "{}"'.format(ROM_file.getBaseNoExt()))
            #     #logger.debug(traceback.format_exc())
            
            # if not scraping_succeeded and skip_if_scraping_failed:
            #     kodi.display_user_message({
            #         'dialog': KODI_MESSAGE_NOTIFY_WARN,
            #         'msg': 'Scraping "{}" failed. Skipping.'.format(ROM_file.getBaseNoExt())
            #     })
            # else:
            #     # --- This was the first ROM in a multidisc set ---
            #     if scanner_multidisc and MDSet.isMultiDisc and not MultiDiscInROMs:
            #         logger.info('Adding to ROMs dic first disk "{0}"'.format(MDSet.discName))
            #         new_rom.add_disk(MDSet.discName)
                
            new_roms.append(new_rom)
            
            # ~~~ Check if user pressed the cancel button ~~~
            if self.progress_dialog.isCanceled():
                self.progress_dialog.endProgress()
                kodi.dialog_OK('Stopping ROM scanning. No changes have been made.')
                logger.info('User pressed Cancel button when scanning ROMs. ROM scanning stopped.')
                return None
            
            num_items_checked += 1
           
        self.progress_dialog.endProgress()
        return new_roms

    def _configuration_get_extensions_from_app_path(self, input, item_key, scanner_settings):
        if input: return input
        extensions = scanner_settings[item_key] if item_key in scanner_settings else ''
        if extensions != '': return extensions
        
        if self.default_launcher_settings and 'application' in self.default_launcher_settings:
            app = self.default_launcher_settings['application'] 
            appPath = io.FileName(app)

            extensions = platforms.emudata_get_program_extensions(appPath.getBase())
            
        return extensions
             
# ------------------------------------------------------------------------------------------------
# NULL scraper, does nothing.
# ------------------------------------------------------------------------------------------------
class Null_Scraper(Scraper):
    # @param settings: [dict] Addon settings. Particular scraper settings taken from here.
    def __init__(self, settings): super(Null_Scraper, self).__init__(settings)

    def get_id(self):
        return SCRAPER_NULL_ID

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

    def download_image(self, image_url, image_local_path): return None
    
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

    def get_id(self):
        return SCRAPER_AEL_OFFLINE_ID
    
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
        rombase_noext = rom_FN.getBase_noext()
        log_debug('AEL_Offline.get_candidates() rombase_noext "{}"'.format(rombase_noext))
        log_debug('AEL_Offline.get_candidates() AEL platform  "{}"'.format(platform))

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
            key_id = self.candidate['id']
            log_verb("AEL_Offline.get_metadata() Mode MAME id = '{}'".format(key_id))
            gamedata['title']     = self.cached_games[key_id]['title']
            gamedata['year']      = self.cached_games[key_id]['year']
            gamedata['genre']     = self.cached_games[key_id]['genre']
            gamedata['developer'] = self.cached_games[key_id]['developer']
            gamedata['nplayers']  = self.cached_games[key_id]['nplayers']
        elif self.cached_platform == 'Unknown':
            # Unknown platform. Behave like NULL scraper
            log_verb("AEL_Offline.get_metadata() Mode Unknown. Doing nothing.")
        else:
            # No-Intro scraper by default.
            key_id = self.candidate['id']
            log_verb("AEL_Offline.get_metadata() Mode No-Intro id = '{}'".format(key_id))
            gamedata['title']     = self.cached_games[key_id]['title']
            gamedata['year']      = self.cached_games[key_id]['year']
            gamedata['genre']     = self.cached_games[key_id]['genre']
            gamedata['developer'] = self.cached_games[key_id]['developer']
            gamedata['nplayers']  = self.cached_games[key_id]['nplayers']
            gamedata['esrb']      = self.cached_games[key_id]['rating']
            gamedata['plot']      = self.cached_games[key_id]['plot']

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
            candidate['id'] = self.cached_games[rom_base_noext_lower]['ROM']
            candidate['display_name'] = self.cached_games[rom_base_noext_lower]['title']
            candidate['platform'] = platform
            candidate['scraper_platform'] = platform
            candidate['order'] = 1
            return [candidate]
        else:
            return []

    def _get_NoIntro_candidates(self, rombase_noext, platform):
        # --- First try an exact match using rombase_noext ---
        log_verb("AEL_Offline._get_NoIntro_candidates() Scraper working in No-Intro mode.")
        log_verb("AEL_Offline._get_NoIntro_candidates() Trying exact search for '{}'".format(
            rombase_noext))
        candidate_list = []
        if rombase_noext in self.cached_games:
            log_verb("AEL_Offline._get_NoIntro_candidates() Exact match found.")
            candidate = self._new_candidate_dic()
            candidate['id'] = rombase_noext
            candidate['display_name'] = self.cached_games[rombase_noext]['ROM']
            candidate['platform'] = platform
            candidate['scraper_platform'] = platform
            candidate['order'] = 1
            candidate_list.append(candidate)
        else:
            # --- If nothing found, do a fuzzy search ---
            # Here implement a Levenshtein distance algorithm.
            search_term = text_format_ROM_name_for_scraping(rombase_noext)
            log_verb("AEL_Offline._get_NoIntro_candidates() No exact match found.")
            log_verb("AEL_Offline._get_NoIntro_candidates() Trying fuzzy search '{}'".format(
                search_term))
            search_string_lower = rombase_noext.lower()
            regexp = '.*{}.*'.format(search_string_lower)
            try:
                # Sometimes this produces: raise error, v # invalid expression
                p = re.compile(regexp)
            except:
                log_info('AEL_Offline._get_NoIntro_candidates() Exception in re.compile(regexp)')
                log_info('AEL_Offline._get_NoIntro_candidates() regexp = "{}"'.format(regexp))
                return []

            for key in self.cached_games:
                this_game_name = self.cached_games[key]['ROM']
                this_game_name_lower = this_game_name.lower()
                match = p.match(this_game_name_lower)
                if not match: continue
                # --- Add match to candidate list ---
                candidate = self._new_candidate_dic()
                candidate['id'] = self.cached_games[key]['ROM']
                candidate['display_name'] = self.cached_games[key]['ROM']
                candidate['platform'] = platform
                candidate['scraper_platform'] = platform
                candidate['order'] = 1
                # If there is an exact match of the No-Intro name put that candidate game first.
                if search_term == this_game_name:                         candidate['order'] += 1
                if rombase_noext == this_game_name:                       candidate['order'] += 1
                if self.cached_games[key]['ROM'].startswith(search_term): candidate['order'] += 1
                candidate_list.append(candidate)
            candidate_list.sort(key = lambda result: result['order'], reverse = True)

        return candidate_list

    # Load XML database and keep it cached in memory.
    def _initialise_platform(self, platform):
        # Check if we have data already cached in object memory for this platform
        if self.cached_platform == platform:
            log_debug('AEL_Offline._initialise_platform() platform = "{}" is cached in object.'.format(
                platform))
            return
        else:
            log_debug('AEL_Offline._initialise_platform() platform = "{}" not cached. Loading XML.'.format(
                platform))

        # What if platform is not in the official list dictionary?
        # Then load nothing and behave like the NULL scraper.
        if platform in platform_long_to_index_dic:
            # Check for aliased platforms
            pobj = AEL_platforms[platform_long_to_index_dic[platform]]
            if pobj.aliasof:
                log_debug('AEL_Offline._initialise_platform() Aliased platform. Using parent XML.')
                parent_pobj = AEL_platforms[platform_compact_to_index_dic[pobj.aliasof]]
                xml_file = 'data-AOS/' + parent_pobj.long_name + '.xml'
            else:
                xml_file = 'data-AOS/' + platform + '.xml'

        else:
            log_debug('AEL_Offline._initialise_platform() Platform "{}" not found'.format(platform))
            log_debug('AEL_Offline._initialise_platform() Defaulting to Unknown')
            self._reset_cached_games()
            return

        # Load XML database and keep it in memory for subsequent calls
        xml_path = os.path.join(self.addon_dir, xml_file)
        # log_debug('AEL_Offline._initialise_platform() Loading XML {}'.format(xml_path))
        self.cached_games = audit_load_OfflineScraper_XML(xml_path)
        if not self.cached_games:
            self._reset_cached_games()
            return
        self.cached_xml_path = xml_path
        self.cached_platform = platform
        log_debug('AEL_Offline._initialise_platform() cached_xml_path = {}'.format(self.cached_xml_path))
        log_debug('AEL_Offline._initialise_platform() cached_platform = {}'.format(self.cached_platform))

    def _reset_cached_games(self):
        self.cached_games = {}
        self.cached_xml_path = ''
        self.cached_platform = 'Unknown'