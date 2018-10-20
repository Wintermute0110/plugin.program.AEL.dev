# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher miscellaneous set of objects
#

# 1. Always use new style classes in Python 2 to ease the transition to Python 3.
#    All classes in Python 2 must have object as base class.
#    See https://stackoverflow.com/questions/4015417/python-class-inherits-object

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
import collections

# --- AEL packages ---
from utils import *
from disk_IO import *

# #################################################################################################
# #################################################################################################
# ROM scanners
# #################################################################################################
# #################################################################################################
class RomScannersFactory():
    def __init__(self, settings, PATHS):
        self.settings = settings
        self.reports_dir = PATHS.REPORTS_DIR
        self.addon_dir = PATHS.ADDON_DATA_DIR

    def create(self, launcher, scrapers):
        launcherType = launcher.get_launcher_type()
        log_info('RomScannersFactory: Creating romscanner for {}'.format(launcherType))

        if not launcher.supports_launching_roms():
            return NullScanner(launcher, self.settings)
        
        if launcherType == LAUNCHER_STEAM:
            return SteamScanner(self.reports_dir, self.addon_dir, launcher, self.settings, scrapers)

        if launcherType == LAUNCHER_NVGAMESTREAM:
            return NvidiaStreamScanner(self.reports_dir, self.addon_dir, launcher, romset, self.settings, scrapers)
                
        return RomFolderScanner(self.reports_dir, self.addon_dir, launcher, self.settings, scrapers)

class ScannerStrategy(KodiProgressDialogStrategy):
    __metaclass__ = abc.ABCMeta

    def __init__(self, launcher, settings):
        self.launcher = launcher
        self.settings = settings
        super(ScannerStrategy, self).__init__()

    #
    # Scans for new roms based on the type of launcher.
    #
    @abc.abstractmethod
    def scan(self):
        return {}

    #
    # Cleans up ROM collection.
    # Remove Remove dead/missing ROMs ROMs
    #
    @abc.abstractmethod
    def cleanup(self):
        return {}

class NullScanner(ScannerStrategy):
    def scan(self):
        return {}

    def cleanup(self):
        return {}

class RomScannerStrategy(ScannerStrategy):
    __metaclass__ = abc.ABCMeta

    def __init__(self, reports_dir, addon_dir, launcher, settings, scrapers):
        
        self.reports_dir = reports_dir
        self.addon_dir = addon_dir
                
        self.scrapers = scrapers

        super(RomScannerStrategy, self).__init__(launcher, settings)

    def scan(self):
        
        # --- Open ROM scanner report file ---
        launcher_report = FileReporter(self.reports_dir, self.launcher.get_data(), LogReporter(self.launcher.get_data()))
        launcher_report.open('RomScanner() Starting ROM scanner')

        # >> Check if there is an XML for this launcher. If so, load it.
        # >> If file does not exist or is empty then return an empty dictionary.
        launcher_report.write('Loading launcher ROMs ...')
        roms = self.launcher.get_roms()

        if roms is None:
            roms = []
        
        num_roms = len(roms)
        launcher_report.write('{0} ROMs currently in database'.format(num_roms))
        
        launcher_report.write('Collecting candidates ...')
        candidates = self._getCandidates(launcher_report)
        num_candidates = len(candidates)
        log_info('{0} candidates found'.format(num_candidates))

        launcher_report.write('Removing dead ROMs ...')
        num_removed_roms = self._removeDeadRoms(candidates, roms)        

        if num_removed_roms > 0:
            kodi_notify('{0} dead ROMs removed successfully'.format(num_removed_roms))
            log_info('{0} dead ROMs removed successfully'.format(num_removed_roms))
        else:
            log_info('No dead ROMs found')

        new_roms = self._processFoundItems(candidates, roms, launcher_report)
        
        if not new_roms:
            return None

        num_new_roms = len(new_roms)
        roms = roms + new_roms

        launcher_report.write('******************** ROM scanner finished. Report ********************')
        launcher_report.write('Removed dead ROMs {0:6d}'.format(num_removed_roms))
        launcher_report.write('Files checked     {0:6d}'.format(num_candidates))
        launcher_report.write('New added ROMs    {0:6d}'.format(num_new_roms))
        
        if len(roms) == 0:
            launcher_report.write('WARNING Launcher has no ROMs!')
            launcher_report.close()
            kodi_dialog_OK('No ROMs found! Make sure launcher directory and file extensions are correct.')
            return None
        
        if num_new_roms == 0:
            kodi_notify('Added no new ROMs. Launcher has {0} ROMs'.format(len(roms)))
        else:
            kodi_notify('Added {0} new ROMs'.format(num_new_roms))

        # --- Close ROM scanner report file ---
        launcher_report.write('*** END of the ROM scanner report ***')
        launcher_report.close()

        return roms

    def cleanup(self):
        launcher_report = LogReporter(self.launcher.get_data())
        launcher_report.open('RomScanner() Starting Dead ROM cleaning')
        log_debug('RomScanner() Starting Dead ROM cleaning')

        roms = self.launcher.get_roms()
        if roms is None:
            launcher_report.close()
            log_info('RomScanner() No roms available to cleanup')
            return {}
        
        num_roms = len(roms)
        launcher_report.write('{0} ROMs currently in database'.format(num_roms))
        
        launcher_report.write('Collecting candidates ...')
        candidates = self._getCandidates(launcher_report)
        num_candidates = len(candidates)
        log_info('{0} candidates found'.format(num_candidates))

        launcher_report.write('Removing dead ROMs ...')
        num_removed_roms = self._removeDeadRoms(candidates, roms)        

        if num_removed_roms > 0:
            kodi_notify('{0} dead ROMs removed successfully'.format(num_removed_roms))
            log_info('{0} dead ROMs removed successfully'.format(num_removed_roms))
        else:
            log_info('No dead ROMs found')

        launcher_report.close()
        return roms

    # ~~~ Scan for new files (*.*) and put them in a list ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @abc.abstractmethod
    def _getCandidates(self, launcher_report):
        return []

    # --- Remove dead entries -----------------------------------------------------------------
    @abc.abstractmethod
    def _removeDeadRoms(self, candidates, roms):
        return 0

    # ~~~ Now go processing item by item ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @abc.abstractmethod
    def _processFoundItems(self, items, roms, launcher_report):
        return []

class RomFolderScanner(RomScannerStrategy):
    # ~~~ Scan for new files (*.*) and put them in a list ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def _getCandidates(self, launcher_report):
        kodi_busydialog_ON()
        files = []
        launcher_path = self.launcher.get_rom_path()
        launcher_report.write('Scanning files in {0}'.format(launcher_path.getOriginalPath()))

        if self.settings['scan_recursive']:
            log_info('Recursive scan activated')
            files = launcher_path.recursiveScanFilesInPath('*.*')
        else:
            log_info('Recursive scan not activated')
            files = launcher_path.scanFilesInPath('*.*')

        kodi_busydialog_OFF()

        num_files = len(files)
        launcher_report.write('  File scanner found {0} files'.format(num_files))

        return files

    # --- Remove dead entries -----------------------------------------------------------------
    def _removeDeadRoms(self, candidates, roms):
        num_roms = len(roms)
        num_removed_roms = 0
        if num_roms == 0:
            log_info('Launcher is empty. No dead ROM check.')
            return num_removed_roms
        
        log_debug('Starting dead items scan')
        i = 0
            
        self._startProgressPhase('Advanced Emulator Launcher', 'Checking for dead ROMs ...')
            
        for rom in reversed(roms):
            fileName = rom.get_file()
            log_debug('Searching {0}'.format(fileName.getOriginalPath()))
            self._updateProgress(i * 100 / num_roms)
            
            if not fileName.exists():
                log_debug('Not found')
                log_debug('Deleting from DB {0}'.format(fileName.getOriginalPath()))
                roms.remove(rom)
                num_removed_roms += 1
            i += 1
            
        self._endProgressPhase()

        return num_removed_roms

    # ~~~ Now go processing item by item ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def _processFoundItems(self, items, roms, launcher_report):

        num_items = len(items)    
        new_roms = []

        self._startProgressPhase('Advanced Emulator Launcher', 'Scanning found items')
        log_debug('============================== Processing ROMs ==============================')
        launcher_report.write('Processing files ...')
        num_items_checked = 0
        
        allowedExtensions = self.launcher.get_rom_extensions()
        launcher_multidisc = self.launcher.supports_multidisc()

        for item in sorted(items):
            self._updateProgress(num_items_checked * 100 / num_items)
            
            # --- Get all file name combinations ---
            ROM = FileNameFactory.create(item)
            launcher_report.write('>>> {0}'.format(ROM.getOriginalPath()).encode('utf-8'))

            # ~~~ Update progress dialog ~~~
            file_text = 'ROM {0}'.format(ROM.getBase())
            self._updateProgressMessage(file_text, 'Checking if has ROM extension ...')
                        
            # --- Check if filename matchs ROM extensions ---
            # The recursive scan has scanned all files. Check if this file matches some of 
            # the ROM extensions. If this file isn't a ROM skip it and go for next one in the list.
            processROM = False

            for ext in allowedExtensions:
                if ROM.getExt() == '.' + ext:
                    launcher_report.write("  Expected '{0}' extension detected".format(ext))
                    processROM = True
                    break

            if not processROM: 
                launcher_report.write('  File has not an expected extension. Skipping file.')
                continue
                        
            # --- Check if ROM belongs to a multidisc set ---
            self._updateProgressMessage(file_text, 'Checking if ROM belongs to multidisc set..')
                       
            MultiDiscInROMs = False
            MDSet = text_get_multidisc_info(ROM)
            if MDSet.isMultiDisc and launcher_multidisc:
                log_info('ROM belongs to a multidisc set.')
                log_info('isMultiDisc "{0}"'.format(MDSet.isMultiDisc))
                log_info('setName     "{0}"'.format(MDSet.setName))
                log_info('discName    "{0}"'.format(MDSet.discName))
                log_info('extension   "{0}"'.format(MDSet.extension))
                log_info('order       "{0}"'.format(MDSet.order))
                launcher_report.write('  ROM belongs to a multidisc set.')
                
                # >> Check if the set is already in launcher ROMs.
                MultiDisc_rom_id = None
                for new_rom in new_roms:
                    temp_FN = new_rom.get_file()
                    if temp_FN.getBase() == MDSet.setName:
                        MultiDiscInROMs  = True
                        MultiDisc_rom    = new_rom
                        break

                log_info('MultiDiscInROMs is {0}'.format(MultiDiscInROMs))

                # >> If the set is not in the ROMs then this ROM is the first of the set.
                # >> Add the set
                if not MultiDiscInROMs:
                    log_info('First ROM in the set. Adding to ROMs ...')
                    # >> Manipulate ROM so filename is the name of the set
                    ROM_dir = FileNameFactory.create(ROM.getDir())
                    ROM_temp = ROM_dir.pjoin(MDSet.setName)
                    log_info('ROM_temp OP "{0}"'.format(ROM_temp.getOriginalPath()))
                    log_info('ROM_temp  P "{0}"'.format(ROM_temp.getPath()))
                    ROM = ROM_temp
                # >> If set already in ROMs, just add this disk into the set disks field.
                else:
                    log_info('Adding additional disk "{0}"'.format(MDSet.discName))
                    MultiDisc_rom.add_disk(MDSet.discName)
                    # >> Reorder disks like Disk 1, Disk 2, ...
                    
                    # >> Process next file
                    log_info('Processing next file ...')
                    continue
            elif MDSet.isMultiDisc and not launcher_multidisc:
                launcher_report.write('  ROM belongs to a multidisc set but Multidisc support is disabled.')
            else:
                launcher_report.write('  ROM does not belong to a multidisc set.')
 
            # --- Check that ROM is not already in the list of ROMs ---
            # >> If file already in ROM list skip it
            self._updateProgressMessage(file_text, 'Checking if ROM is not already in collection...')
            repeatedROM = False
            for rom in roms:
                rpath = rom.get_filename() 
                if rpath == item: 
                    repeatedROM = True
        
            if repeatedROM:
                launcher_report.write('  File already into launcher ROM list. Skipping file.')
                continue
            else:
                launcher_report.write('  File not in launcher ROM list. Processing it ...')

            # --- Ignore BIOS ROMs ---
            # Name of bios is: '[BIOS] Rom name example (Rev A).zip'
            if self.settings['scan_ignore_bios']:
                BIOS_re = re.findall('\[BIOS\]', ROM.getBase())
                if len(BIOS_re) > 0:
                    log_info("BIOS detected. Skipping ROM '{0}'".format(ROM.path))
                    continue

            # ~~~~~ Process new ROM and add to the list ~~~~~
            # --- Create new rom dictionary ---
            # >> Database always stores the original (non transformed/manipulated) path
            new_rom = Rom()
            new_rom.set_file(ROM)

            searchTerm = text_format_ROM_name_for_scraping(ROM.getBase_noext())

            if self.scrapers:
                for scraper in self.scrapers:
                    self._updateProgressMessage(file_text, 'Scraping {0}...'.format(scraper.getName()))
                    scraper.scrape(searchTerm, ROM, new_rom)
            
            romdata = new_rom.get_data()
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
            
            # --- This was the first ROM in a multidisc set ---
            if launcher_multidisc and MDSet.isMultiDisc and not MultiDiscInROMs:
                log_info('Adding to ROMs dic first disk "{0}"'.format(MDSet.discName))
                new_rom.add_disk(MDSet.discName)
            
            new_roms.append(new_rom)
            
            # ~~~ Check if user pressed the cancel button ~~~
            if self._isProgressCanceled():
                self._endProgressPhase()
                kodi_dialog_OK('Stopping ROM scanning. No changes have been made.')
                log_info('User pressed Cancel button when scanning ROMs. ROM scanning stopped.')
                return None
            
            num_items_checked += 1
           
        self._endProgressPhase()
        return new_roms

class SteamScanner(RomScannerStrategy):
    
    # ~~~ Scan for new items not yet in the rom collection ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def _getCandidates(self, launcher_report):
               
        log_debug('Reading Steam account')
        self._startProgressPhase('Advanced Emulator Launcher', 'Reading Steam account...')

        apikey = self.settings['steam-api-key']
        steamid = self.launcher.get_steam_id()
        url = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={}&steamid={}&include_appinfo=1'.format(apikey, steamid)
        
        self._updateProgress(70)
        body = net_get_URL_original(url)
        self._updateProgress(80)
        
        steamJson = json.loads(body)
        games = steamJson['response']['games']
        
        self._endProgressPhase()
        return games

    # --- Remove dead entries -----------------------------------------------------------------
    def _removeDeadRoms(self, candidates, roms):
    
        if roms is None or len(roms) == 0:
            log_info('Launcher is empty. No dead ROM check.')
            return 0

        log_debug('Starting dead items scan')
        num_roms = len(roms)
        num_removed_roms = 0
        i = 0
            
        self._startProgressPhase('Advanced Emulator Launcher', 'Checking for dead ROMs ...')
        
        steamGameIds = set(steamGame['appid'] for steamGame in candidates)

        for rom in reversed(roms):
            romSteamId = rom.get_custom_attribute('steamid')
            
            log_debug('Searching {0}'.format(romSteamId))
            self._updateProgress(i * 100 / num_roms)
            i += 1

            if romSteamId not in steamGameIds:
                log_debug('Not found. Deleting from DB {0}'.format(rom.get_name()))
                roms.remove(rom)
                num_removed_roms += 1
            
        self._endProgressPhase()

        return num_removed_roms

    def _processFoundItems(self, items, roms, launcher_report):
        
        if items is None or len(items) == 0:
            log_info('No steam games available.')
            return []

        new_roms = []

        num_games = len(items)
        num_items_checked = 0
            
        self._startProgressPhase('Advanced Emulator Launcher', 'Checking for new ROMs ...')
        steamIdsAlreadyInCollection = set(rom.get_custom_attribute('steamid') for rom in roms)
        
        for steamGame in items:
            
            steamId = steamGame['appid']
            log_debug('Searching {} with #{}'.format(steamGame['name'], steamId))

            self._updateProgress(num_items_checked * 100 / num_games, steamGame['name'])
            
            if steamId not in steamIdsAlreadyInCollection:
                
                log_debug('========== Processing Steam game ==========')
                launcher_report.write('>>> title: {0}'.format(steamGame['name']))
                launcher_report.write('>>> ID: {0}'.format(steamGame['appid']))
        
                log_debug('Not found. Item {0} is new'.format(steamGame['name']))

                launcher_path = self.launcher.get_rom_path()
                romPath = launcher_path.pjoin('{0}.rom'.format(steamGame['appid']))

                # ~~~~~ Process new ROM and add to the list ~~~~~
                # --- Create new rom dictionary ---
                # >> Database always stores the original (non transformed/manipulated) path
                new_rom  = Rom()
                new_rom.set_file(romPath)

                new_rom.set_custom_attribute('steamid', steamGame['appid'])
                new_rom.set_custom_attribute('steam_name', steamGame['name'])  # so that we always have the original name
                new_rom.set_name(steamGame['name'])

                searchTerm = steamGame['name']
                
                if self.scrapers:
                    for scraper in self.scrapers:
                        self._updateProgressMessage(steamGame['name'], 'Scraping {0}...'.format(scraper.getName()))
                        scraper.scrape(searchTerm, romPath, new_rom)
                
                romdata = new_rom.get_data()
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
            
                new_roms.append(new_rom)
                            
                # ~~~ Check if user pressed the cancel button ~~~
                if self._isProgressCanceled():
                    self._endProgressPhase()
                    kodi_dialog_OK('Stopping ROM scanning. No changes have been made.')
                    log_info('User pressed Cancel button when scanning ROMs. ROM scanning stopped.')
                    return None
            
                num_items_checked += 1

        self._endProgressPhase()    
        return new_roms

class NvidiaStreamScanner(RomScannerStrategy):

    # ~~~ Scan for new items not yet in the rom collection ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def _getCandidates(self, launcher_report):
        from gamestream import GameStreamServer

        log_debug('Reading Nvidia GameStream server')
        self._startProgressPhase('Advanced Emulator Launcher', 'Reading Nvidia GameStream server...')

        server_host = self.launcher.get_server()
        certificates_path = self.launcher.get_certificates_path()

        streamServer = GameStreamServer(server_host, certificates_path)
        connected = streamServer.connect()

        if not connected:
            kodi_notify_error('Unable to connect to gamestream server')
            return None

        self._updateProgress(50)
        games = streamServer.getApps()
                
        self._endProgressPhase()
        return games

    # --- Remove dead entries -----------------------------------------------------------------
    def _removeDeadRoms(self, candidates, roms):
    
        if roms is None or len(roms) == 0:
            log_info('Launcher is empty. No dead ROM check.')
            return 0

        log_debug('Starting dead items scan')
        num_roms = len(roms)
        num_removed_roms = 0
        i = 0
            
        self._startProgressPhase('Advanced Emulator Launcher', 'Checking for dead ROMs ...')
        
        streamIds = set(streamableGame['ID'] for streamableGame in candidates)

        for rom in reversed(roms):
            romStreamId = rom.get_custom_attribute('streamid')
            
            log_debug('Searching {0}'.format(romStreamId))
            self._updateProgress(i * 100 / num_roms)
            i += 1

            if romStreamId not in streamIds:
                log_debug('Not found. Deleting from DB {0}'.format(rom.get_name()))
                roms.remove(rom)
                num_removed_roms += 1
            
        self._endProgressPhase()

        return num_removed_roms

    def _processFoundItems(self, items, roms, launcher_report):
        
        if items is None or len(items) == 0:
            log_info('No Nvidia Gamestream games available.')
            return []

        new_roms = []

        num_games = len(items)
        num_items_checked = 0
            
        self._startProgressPhase('Advanced Emulator Launcher', 'Checking for new ROMs ...')
        streamIdsAlreadyInCollection = set(rom.get_custom_attribute('streamid') for rom in roms)
        
        for streamableGame in items:
            
            streamId = streamableGame['ID']
            log_debug('Searching {} with #{}'.format(streamableGame['AppTitle'], streamId))

            self._updateProgress(num_items_checked * 100 / num_games, streamableGame['AppTitle'])
            
            if streamId not in streamIdsAlreadyInCollection:
                
                log_debug('========== Processing Nvidia Gamestream game ==========')
                launcher_report.write('>>> title: {0}'.format(streamableGame['AppTitle']))
                launcher_report.write('>>> ID: {0}'.format(streamableGame['ID']))
        
                log_debug('Not found. Item {0} is new'.format(streamableGame['AppTitle']))

                launcher_path = launcher.get_rom_path()
                romPath = launcher_path.pjoin('{0}.rom'.format(streamableGame['ID']))

                # ~~~~~ Process new ROM and add to the list ~~~~~
                # --- Create new rom dictionary ---
                # >> Database always stores the original (non transformed/manipulated) path
                new_rom  = Rom()
                new_rom.set_file(romPath)

                new_rom.set_custom_attribute('streamid',        streamableGame['ID'])
                new_rom.set_custom_attribute('gamestream_name', streamableGame['AppTitle'])  # so that we always have the original name
                new_rom.set_name(streamableGame['AppTitle'])
                
                searchTerm = streamableGame['AppTitle']
                
                if self.scrapers:
                    for scraper in self.scrapers:
                        self._updateProgressMessage(streamableGame['AppTitle'], 'Scraping {0}...'.format(scraper.getName()))
                        scraper.scrape(searchTerm, romPath, new_rom)
            
                romdata = new_rom.get_data()
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
            
                new_roms.append(new_rom)
                            
                # ~~~ Check if user pressed the cancel button ~~~
                if self._isProgressCanceled():
                    self._endProgressPhase()
                    kodi_dialog_OK('Stopping ROM scanning. No changes have been made.')
                    log_info('User pressed Cancel button when scanning ROMs. ROM scanning stopped.')
                    return None
            
                num_items_checked += 1

        self._endProgressPhase()    
        return new_roms

# #################################################################################################
# #################################################################################################
# DAT files and ROM audit
# #################################################################################################
# #################################################################################################

class RomDatFileScanner(KodiProgressDialogStrategy):
    def __init__(self, settings):
        self.settings = settings
        super(RomDatFileScanner, self).__init__()

    #
    # Helper function to update ROMs No-Intro status if user configured a No-Intro DAT file.
    # Dictionaries are mutable, so roms can be changed because passed by assigment.
    # This function also creates the Parent/Clone indices:
    #   1) ADDON_DATA_DIR/db_ROMs/roms_base_noext_PClone_index.json
    #   2) ADDON_DATA_DIR/db_ROMs/roms_base_noext_parents.json
    #
    # A) If there are Unkown ROMs, a fake rom with name [Unknown ROMs] and id UNKNOWN_ROMS_PARENT_ID
    #    is created. This fake ROM is the parent of all Unknown ROMs.
    #    This fake ROM is added to roms_base_noext_parents.json database.
    #    This fake ROM is not present in the main JSON ROM database.
    # 
    # Returns:
    #   True  -> ROM audit was OK
    #   False -> There was a problem with the audit.
    #
    #def _roms_update_NoIntro_status(self, roms, nointro_xml_file_FileName):
    def update_roms_NoIntro_status(self, launcher, roms):
                
        __debug_progress_dialogs = False
        __debug_time_step = 0.0005
        
        # --- Reset the No-Intro status and removed No-Intro missing ROMs ---
        audit_have = audit_miss = audit_unknown = 0
        self._startProgressPhase('Advanced Emulator Launcher', 'Deleting Missing/Dead ROMs and clearing flags ...')
        self.roms_reset_NoIntro_status(launcher, roms)
        self._updateProgress(100)
        if __debug_progress_dialogs: time.sleep(0.5)

        # --- Check if DAT file exists ---
        nointro_xml_file_FileName = launcher.get_nointro_xml_filepath()
        if not nointro_xml_file_FileName.exists():
            log_warning('_roms_update_NoIntro_status() Not found {0}'.format(nointro_xml_file_FileName.getOriginalPath()))
            return False
        
        self._updateProgress(0, 'Loading No-Intro/Redump XML DAT file ...')
        roms_nointro = audit_load_NoIntro_XML_file(nointro_xml_file_FileName)
        self._updateProgress(100)

        if __debug_progress_dialogs: time.sleep(0.5)
        if not roms_nointro:
            log_warning('_roms_update_NoIntro_status() Error loading {0}'.format(nointro_xml_file_FileName.getPath()))
            return False

        # --- Remove BIOSes from No-Intro ROMs ---
        if self.settings['scan_ignore_bios']:
            log_info('_roms_update_NoIntro_status() Removing BIOSes from No-Intro ROMs ...')
            self._updateProgress(0, 'Removing BIOSes from No-Intro ROMs ...')
            num_items = len(roms_nointro)
            item_counter = 0
            filtered_roms_nointro = {}
            for rom_id in roms_nointro:
                rom_data = roms_nointro[rom_id]
                BIOS_str_list = re.findall('\[BIOS\]', rom_data['name'])
                if not BIOS_str_list:
                    filtered_roms_nointro[rom_id] = rom_data
                else:
                    log_debug('_roms_update_NoIntro_status() Removed BIOS "{0}"'.format(rom_data['name']))
                item_counter += 1
                self._updateProgress((item_counter*100)/num_items)
                if __debug_progress_dialogs: time.sleep(__debug_time_step)
            roms_nointro = filtered_roms_nointro
            self._updateProgress(100)
        else:
            log_info('_roms_update_NoIntro_status() User wants to include BIOSes.')

        # --- Put No-Intro ROM names in a set ---
        # >> Set is the fastest Python container for searching elements (implements hashed search).
        # >> No-Intro names include tags
        self._updateProgress(0, 'Creating No-Intro and ROM sets ...')
        roms_nointro_set = set(roms_nointro.keys())
        roms_set = set()
        for rom in roms:
            # >> Use the ROM basename.
            ROMFileName = rom.get_file()
            roms_set.add(ROMFileName.getBase_noext())
        self._updateProgress(100)
        if __debug_progress_dialogs: time.sleep(0.5)

        # --- Traverse Launcher ROMs and check if they are in the No-Intro ROMs list ---
        self._updateProgress(0, 'Audit Step 1/4: Checking Have and Unknown ROMs ...')
        num_items = len(roms)
        item_counter = 0
        for rom in roms:
            ROMFileName = rom.get_file()
            if ROMFileName.getBase_noext() in roms_nointro_set:
                rom.set_nointro_status(NOINTRO_STATUS_HAVE)
                audit_have += 1
                log_debug('_roms_update_NoIntro_status() HAVE    "{0}"'.format(ROMFileName.getBase_noext()))
            else:
                rom.set_nointro_status(NOINTRO_STATUS_UNKNOWN)
                audit_unknown += 1
                log_debug('_roms_update_NoIntro_status() UNKNOWN "{0}"'.format(ROMFileName.getBase_noext()))
            item_counter += 1
            self._updateProgress((item_counter*100)/num_items)
            if __debug_progress_dialogs: time.sleep(__debug_time_step)
        self._updateProgress(100)

        # --- Mark Launcher dead ROMs as missing ---
        self._updateProgress(0, 'Audit Step 2/4: Checking Missing ROMs ...')
        num_items = len(roms)
        item_counter = 0
        for rom in roms:
            ROMFileName = rom.get_file()
            if not ROMFileName.exists():
                rom.set_nointro_status(NOINTRO_STATUS_MISS)
                audit_miss += 1
                log_debug('_roms_update_NoIntro_status() MISSING "{0}"'.format(ROMFileName.getBase_noext()))
            item_counter += 1
            self._updateProgress((item_counter*100)/num_items)
            if __debug_progress_dialogs: time.sleep(__debug_time_step)
        self._updateProgress(100)

        # --- Now add missing ROMs to Launcher ---
        # >> Traverse the No-Intro set and add the No-Intro ROM if it's not in the Launcher
        # >> Added/Missing ROMs have their own romID.
        self._updateProgress(0, 'Audit Step 3/4: Adding Missing ROMs ...')
        num_items = len(roms_nointro_set)
        item_counter = 0
        ROMPath = launcher.get_rom_path()
        for nointro_rom in sorted(roms_nointro_set):
            # log_debug('_roms_update_NoIntro_status() Checking "{0}"'.format(nointro_rom))
            if nointro_rom not in roms_set:
                # Add new "fake" missing ROM. This ROM cannot be launched!
                # Added ROMs have special extension .nointro
                rom = Rom()
                rom.set_file(ROMPath.pjoin(nointro_rom + '.nointro'))
                rom.set_name(nointro_rom)
                rom.set_nointro_status(NOINTRO_STATUS_MISS)
                roms.append(rom)
                audit_miss += 1
                log_debug('_roms_update_NoIntro_status() ADDED   "{0}"'.format(rom.get_name()))
                # log_debug('_roms_update_NoIntro_status()    OP   "{0}"'.format(rom['filename']))
            item_counter += 1
            self._updateProgress((item_counter*100)/num_items)
            if __debug_progress_dialogs: time.sleep(__debug_time_step)
        self._updateProgress(100)

        # --- Detect if the DAT file has PClone information or not ---
        dat_pclone_dic = audit_make_NoIntro_PClone_dic(roms_nointro)
        num_dat_clones = 0
        for parent_name in dat_pclone_dic: num_dat_clones += len(dat_pclone_dic[parent_name])
        log_verb('No-Intro/Redump DAT has {0} clone ROMs'.format(num_dat_clones))

        # --- Generate main pclone dictionary ---
        # >> audit_unknown_roms is an int of list = ['Parents', 'Clones']
        # log_debug("settings['audit_unknown_roms'] = {0}".format(self.settings['audit_unknown_roms']))
        unknown_ROMs_are_parents = True if self.settings['audit_unknown_roms'] == 0 else False
        log_debug('unknown_ROMs_are_parents = {0}'.format(unknown_ROMs_are_parents))
        # if num_dat_clones == 0 and self.settings['audit_create_pclone_groups']:
        #     # --- If DAT has no PClone information and user want then generate filename-based PClone groups ---
        #     # >> This feature is taken from NARS (NARS Advanced ROM Sorting)
        #     log_verb('Generating filename-based Parent/Clone groups')
        #     pDialog(0, 'Building filename-based Parent/Clone index ...')
        #     roms_pclone_index = audit_generate_filename_PClone_index(roms, roms_nointro, unknown_ROMs_are_parents)
        #     pDialog(100)
        #     if __debug_progress_dialogs: time.sleep(0.5)
        # else:
        #     # --- Make a DAT-based Parent/Clone index ---
        #     # >> Here we build a roms_pclone_index with info from the DAT file. 2 issues:
        #     # >> A) Redump DATs do not have cloneof information.
        #     # >> B) Also, it is at this point where a region custom parent may be chosen instead of
        #     # >>    the default one.
        #     log_verb('Generating DAT-based Parent/Clone groups')
        #     pDialog(0, 'Building DAT-based Parent/Clone index ...')
        #     roms_pclone_index = audit_generate_DAT_PClone_index(roms, roms_nointro, unknown_ROMs_are_parents)
        #     pDialog(100)
        #     if __debug_progress_dialogs: time.sleep(0.5)

        # --- Make a DAT-based Parent/Clone index ---
        # >> For 0.9.7 only use the DAT to make the PClone groups. In 0.9.8 decouple the audit
        # >> code from the PClone generation code.
        log_verb('Generating DAT-based Parent/Clone groups')
        self._updateProgress(0, 'Building DAT-based Parent/Clone index ...')
        roms_pclone_index = audit_generate_DAT_PClone_index(roms, roms_nointro, unknown_ROMs_are_parents)
        self._updateProgress(100)
        if __debug_progress_dialogs: time.sleep(0.5)

        # --- Make a Clone/Parent index ---
        # >> This is made exclusively from the Parent/Clone index
        self._updateProgress(0, 'Building Clone/Parent index ...')
        clone_parent_dic = {}
        for parent_id in roms_pclone_index:
            for clone_id in roms_pclone_index[parent_id]:
                clone_parent_dic[clone_id] = parent_id
        self._updateProgress(100)
        if __debug_progress_dialogs: time.sleep(0.5)

        # --- Set ROMs pclone_status flag and update launcher statistics ---
        self._updateProgress(0, 'Audit Step 4/4: Setting Parent/Clone status and cloneof fields...')
        num_items = len(roms)
        item_counter = 0
        audit_parents = audit_clones = 0
        for rom in roms:
            rom_id = rom.get_id()
            if rom_id in roms_pclone_index:
                rom.set_pclone_status(PCLONE_STATUS_PARENT)
                audit_parents += 1
            else:
                rom.set_clone(clone_parent_dic[rom_id])
                rom.set_pclone_status(PCLONE_STATUS_CLONE)
                audit_clones += 1
            item_counter += 1
            self._updateProgress((item_counter*100)/num_items)
            if __debug_progress_dialogs: time.sleep(__debug_time_step)
        self._updateProgress(100)

        launcher.set_audit_stats(len(roms), audit_parents, audit_clones, audit_have, audit_miss, audit_unknown)

        # --- Make a Parent only ROM list and save JSON ---
        # >> This is to speed up rendering of launchers in 1G1R display mode
        self._updateProgress(0, 'Building Parent/Clone index and Parent dictionary ...')
        parent_roms = audit_generate_parent_ROMs_dic(roms, roms_pclone_index)
        self._updateProgress(100)
        if __debug_progress_dialogs: time.sleep(0.5)

        # --- Save JSON databases ---
        self._updateProgress(0, 'Saving NO-Intro/Redump JSON databases ...')
        fs_write_JSON_file(ROMS_DIR, launcher['roms_base_noext'] + '_index_PClone', roms_pclone_index)
        self._updateProgress(30)
        fs_write_JSON_file(ROMS_DIR, launcher['roms_base_noext'] + '_index_CParent', clone_parent_dic)
        self._updateProgress(60)
        fs_write_JSON_file(ROMS_DIR, launcher['roms_base_noext'] + '_parents', parent_roms)
        self._updateProgress(100)
        self._endProgressPhase()

        # --- Update launcher number of ROMs ---
        self.audit_have    = audit_have
        self.audit_miss    = audit_miss
        self.audit_unknown = audit_unknown
        self.audit_total   = len(roms)
        self.audit_parents = audit_parents
        self.audit_clones  = audit_clones

        # --- Report ---
        log_info('********** No-Intro/Redump audit finished. Report ***********')
        log_info('Have ROMs    {0:6d}'.format(self.audit_have))
        log_info('Miss ROMs    {0:6d}'.format(self.audit_miss))
        log_info('Unknown ROMs {0:6d}'.format(self.audit_unknown))
        log_info('Total ROMs   {0:6d}'.format(self.audit_total))
        log_info('Parent ROMs  {0:6d}'.format(self.audit_parents))
        log_info('Clone ROMs   {0:6d}'.format(self.audit_clones))

        return True
    
    #
    # Resets the No-Intro status
    # 1) Remove all ROMs which does not exist.
    # 2) Set status of remaining ROMs to nointro_status = NOINTRO_STATUS_NONE
    #
    def roms_reset_NoIntro_status_roms_reset_NoIntro_status(self, launcher, roms):
        log_info('roms_reset_NoIntro_status() Launcher has {0} ROMs'.format(len(roms)))
        if len(roms) < 1: return

        # >> Step 1) Delete missing/dead ROMs
        num_removed_roms = self._roms_delete_missing_ROMs(roms)
        log_info('roms_reset_NoIntro_status() Removed {0} dead/missing ROMs'.format(num_removed_roms))

        # >> Step 2) Set No-Intro status to NOINTRO_STATUS_NONE and
        #            set PClone status to PCLONE_STATUS_NONE
        log_info('roms_reset_NoIntro_status() Resetting No-Intro status of all ROMs to None')
        for rom in roms: 
            rom.set_nointro_status(NOINTRO_STATUS_NONE)
            rom.set_pclone_status(PCLONE_STATUS_NONE)

        log_info('roms_reset_NoIntro_status() Now launcher has {0} ROMs'.format(len(roms)))

        # >> Step 3) Delete PClone index and Parent ROM list.
        launcher.reset_parent_and_clone_roms()

    # Deletes missing ROMs
    #
    def _roms_delete_missing_ROMs(self, roms):

        num_removed_roms = 0
        num_roms = len(roms)
        log_info('_roms_delete_missing_ROMs() Launcher has {0} ROMs'.format(num_roms))
        if num_roms > 0:
            log_verb('_roms_delete_missing_ROMs() Starting dead items scan')

            for rom in reversed(roms):
            
                ROMFileName = rom.get_file()
                if not rom_file:
                    log_debug('_roms_delete_missing_ROMs() Skip "{0}"'.format(rom.get_name()))
                    continue

                log_debug('_roms_delete_missing_ROMs() Test "{0}"'.format(ROMFileName.getBase()))
                # --- Remove missing ROMs ---
                if not ROMFileName.exists():
                    log_debug('_roms_delete_missing_ROMs() RM   "{0}"'.format(ROMFileName.getBase()))
                    roms.remove(rom)
                    num_removed_roms += 1

            if num_removed_roms > 0:
                log_info('_roms_delete_missing_ROMs() {0} dead ROMs removed successfully'.format(num_removed_roms))
            else:
                log_info('_roms_delete_missing_ROMs() No dead ROMs found.')
        else:
            log_info('_roms_delete_missing_ROMs() Launcher is empty. No dead ROM check.')

        return num_removed_roms

# #################################################################################################
# #################################################################################################
# DAT files and ROM audit objects.
# #################################################################################################
# #################################################################################################


# #################################################################################################
# #################################################################################################
# Launcher objects.
# #################################################################################################
# #################################################################################################

# -------------------------------------------------------------------------------------------------
# UnitOfWork context. Should be a singleton and only used by the repository classes.
# This class holds the actual XML data and reads/writes that data.
# -------------------------------------------------------------------------------------------------
class XmlDataContext(object):
    def __init__(self, xml_file_path):
        log_debug('XmlDataContext::__init__() "{0}"'.format(xml_file_path.getPath()))
        self._xml_root = None
        self.repository_file_path = xml_file_path

    # Lazy loading of xml data through property
    @property
    def xml_data(self):
        if self._xml_root is None:
            self._load_xml()

        return self._xml_root

    def _load_xml(self):
        # --- Parse using cElementTree ---
        # >> If there are issues in the XML file (for example, invalid XML chars)
        # >> ET.parse() will fail.
        log_verb('XmlDataContext::_load_xml() Loading {0}'.format(self.repository_file_path.getOriginalPath()))
        try:
            self._xml_root = self.repository_file_path.readXml()
        except IOError as e:
            log_debug('XmlDataContext::_load_xml() (IOError) errno = {0}'.format(e.errno))
            # log_debug(unicode(errno.errorcode))
            # >> No such file or directory
            if e.errno == errno.ENOENT:
                log_error('XmlDataContext::_load_xml() (IOError) No such file or directory.')
            else:
                log_error('CategoryRepository::_load_xml() (IOError) Unhandled errno value.')
            log_error('XmlDataContext::_load_xml() (IOError) Return empty categories and launchers dictionaries.')
        except ET.ParseError as e:
            log_error('XmlDataContext::_load_xml() (ParseError) Exception parsing XML categories.xml')
            log_error('XmlDataContext::_load_xml() (ParseError) {0}'.format(str(e)))
            kodi_dialog_OK('(ParseError) Exception reading categories.xml. '
                           'Maybe XML file is corrupt or contains invalid characters.')

    def get_nodes(self, tag):
        log_debug('XmlDataContext::get_nodes(): xpath query "{}"'.format(tag))
        return self.xml_data.findall(tag)

    def get_node(self, tag, id):
        query = "{}[id='{}']".format(tag, id)
        log_debug('XmlDataContext::get_node(): xpath query "{}"'.format(query))
        return self.xml_data.find(query)

    def get_nodes_by(self, tag, field, value):
        query = "{}[{}='{}']".format(tag, field, value)
        log_debug('XmlDataContext.get_nodes_by(): xpath query "{}"'.format(query))
        return self.xml_data.findall(query)

    # creates/updates xml node identified by tag and id with the given dictionary of data
    def save_node(self, tag, id, updated_data):
        node_to_update = self.get_node(tag, id)

        if node_to_update is None:
            node_to_update = self.xml_data.makeelement(tag, {}) 
            self.xml_data.append(node_to_update)

        node_to_update.clear()
        
        for key in updated_data:
            element = self.xml_data.makeelement(key, {})  
            updated_value = updated_data[key]
            
            ## >> To simulate a list with XML allow multiple XML tags.
            if isinstance(updated_data, list):
                for extra_value in updated_value:
                    element.text = unicode(extra_value)
                    node_to_update.append(element)
            else:
                element.text = unicode(updated_value)
                node_to_update.append(element)

    def remove_node(self, tag, id):
        node_to_remove = self.get_node(tag, id)

        if node_to_remove is None:
            return

        self.xml_data.remove(node_to_remove)

    def commit(self):
        log_info('Committing changes to XML file. File: {}'.format(self.repository_file_path.getOriginalPath()))
        self.repository_file_path.writeXml(self._xml_root)

# -------------------------------------------------------------------------------------------------
# Repository class for Category objects.
# Arranges retrieving and storing of the categories from and into the XML data file.
# -------------------------------------------------------------------------------------------------
class CategoryRepository(object):
    def __init__(self, data_context):
        log_debug('CategoryRepository::__init__()')
        self.data_context = data_context

    # -------------------------------------------------------------------------------------------------
    # Data model used in the plugin
    # Internally all string in the data model are Unicode. They will be encoded to
    # UTF-8 when writing files.
    # -------------------------------------------------------------------------------------------------
    # These three functions create a new data structure for the given object and (very importantly) 
    # fill the correct default values). These must match what is written/read from/to the XML files.
    # Tag name in the XML is the same as in the data dictionary.
    #
    def _parse_xml_to_dictionary(self, category_element):
        __debug_xml_parser = False
        category = {}
        # Parse child tags of category
        for category_child in category_element:
            
            # By default read strings
            xml_text = category_child.text if category_child.text is not None else ''
            xml_text = text_unescape_XML(xml_text)
            xml_tag  = category_child.tag
            if __debug_xml_parser: log_debug('{0} --> {1}'.format(xml_tag, xml_text.encode('utf-8')))

            # Now transform data depending on tag name
            if xml_tag == 'finished':
                category[xml_tag] = True if xml_text == 'True' else False
            else:
                # Internal data is always stored as Unicode. ElementTree already outputs Unicode.
                category[xml_tag] = xml_text

        return category

    def find(self, category_id):
        if category_id == VCATEGORY_ADDONROOT_ID:
            return Category.create_root_category()

        category_element = self.data_context.get_node('category', category_id)
        if category_element is None:
            log_debug('Cannot find category with id {0}'.format(category_id))
            return None
        category_dic = self._parse_xml_to_dictionary(category_element)
        category = Category(category_dic)

        return category

    def find_all(self):
        categories = []
        category_elements = self.data_context.get_nodes('category')
        log_debug('Found {0} categories'.format(len(category_elements)))
        for category_element in category_elements:
            category_dic = self._parse_xml_to_dictionary(category_element)
            log_debug('Creating category instance for category {0}'.format(category_dic['id']))
            category = Category(category_dic)
            categories.append(category)

        return categories

    def get_simple_list(self):
        category_list = {}
        category_elements = self.data_context.get_nodes('category')
        for category_element in category_elements:
            id = category_element.find('id').text
            name = category_element.find('m_name').text
            category_list[id] = name

        return category_list

    def count(self):
        return len(self.data_context.get_nodes('category'))

    def save(self, category):
        category_id = category.get_id()
        self.data_context.save_node('category', category_id, category.get_data_dic())
        self.data_context.commit()

    def save_multiple(self, categories):
        for category in categories:
            category_id = category.get_id()
            self.data_context.save_node('category', category_id, category.get_data_dic())
        self.data_context.commit()

    def delete(self, category):
        category_id = category.get_id()
        self.data_context.remove_node('category', category_id)
        self.data_context.commit()

# -------------------------------------------------------------------------------------------------
# Repository class for Launchers objects.
# Arranges retrieving and storing of the launchers from and into the xml data file.
# -------------------------------------------------------------------------------------------------
class LauncherRepository(object):
    def __init__(self, data_context, launcher_factory):
        self.data_context = data_context
        self.launcher_factory = launcher_factory

    def _new_launcher_dataset(self):
        l = {'id' : '',
             'm_name' : '',
             'm_year' : '',
             'm_genre' : '',
             'm_developer' : '',
             'm_rating' : '',
             'm_plot' : '',
             'platform' : '',
             'categoryID' : '',
             'application' : '',
             'args' : '',
             'args_extra' : [],
             'rompath' : '',
             'romext' : '',
             'finished': False,
             'toggle_window' : False, # Former 'minimize'
             'non_blocking' : False,
             'multidisc' : True,
             'roms_base_noext' : '',
             'nointro_xml_file' : '',
             'nointro_display_mode' : NOINTRO_DMODE_ALL,
             'launcher_display_mode' : LAUNCHER_DMODE_FLAT,
             'num_roms' : 0,
             'num_parents' : 0,
             'num_clones' : 0,
             'num_have' : 0,
             'num_miss' : 0,
             'num_unknown' : 0,
             'timestamp_launcher' : 0.0,
             'timestamp_report' : 0.0,
             'default_icon' : 's_icon',
             'default_fanart' : 's_fanart',
             'default_banner' : 's_banner',
             'default_poster' : 's_poster',
             'default_clearlogo' : 's_clearlogo',
             'default_controller' : 's_controller',
             'Asset_Prefix' : '',
             's_icon' : '',
             's_fanart' : '',
             's_banner' : '',
             's_poster' : '',
             's_clearlogo' : '',
             's_controller' : '',
             's_trailer' : '',
             'roms_default_icon' : 's_boxfront',
             'roms_default_fanart' : 's_fanart',
             'roms_default_banner' : 's_banner',
             'roms_default_poster' : 's_flyer',
             'roms_default_clearlogo' : 's_clearlogo',
             'ROM_asset_path' : '',
             'path_title' : '',
             'path_snap' : '',
             'path_boxfront' : '',
             'path_boxback' : '',
             'path_cartridge' : '',
             'path_fanart' : '',
             'path_banner' : '',
             'path_clearlogo' : '',
             'path_flyer' : '',
             'path_map' : '',
             'path_manual' : '',
             'path_trailer' : ''
        }
        return l

    def _parse_xml_to_dictionary(self, launcher_element):
        __debug_xml_parser = False
        # Default values
        launcher = self._new_launcher_dataset()

        if __debug_xml_parser: 
            log_debug('Element has {0} child elements'.format(len(launcher_element)))

        # Parse child tags of launcher element
        for element_child in launcher_element:
            # >> By default read strings
            xml_text = element_child.text if element_child.text is not None else ''
            xml_text = text_unescape_XML(xml_text)
            xml_tag  = element_child.tag

            if __debug_xml_parser: 
                log_debug('{0} --> {1}'.format(xml_tag, xml_text.encode('utf-8')))

            # >> Transform list() datatype
            if xml_tag == 'args_extra':
                launcher[xml_tag].append(xml_text)
            # >> Transform Bool datatype
            elif xml_tag == 'finished' or xml_tag == 'toggle_window' or xml_tag == 'non_blocking' or \
                 xml_tag == 'multidisc':
                launcher[xml_tag] = True if xml_text == 'True' else False
            # >> Transform Int datatype
            elif xml_tag == 'num_roms' or xml_tag == 'num_parents' or xml_tag == 'num_clones' or \
                 xml_tag == 'num_have' or xml_tag == 'num_miss' or xml_tag == 'num_unknown':
                launcher[xml_tag] = int(xml_text)
            # >> Transform Float datatype
            elif xml_tag == 'timestamp_launcher' or xml_tag == 'timestamp_report':
                launcher[xml_tag] = float(xml_text)
            else:
                launcher[xml_tag] = xml_text

        return launcher

    def find(self, launcher_id):
        if launcher_id in [VLAUNCHER_FAVOURITES_ID, VLAUNCHER_RECENT_ID, VLAUNCHER_MOST_PLAYED_ID]:
            launcher = self.launcher_factory.create_new(launcher_id)
            return launcher

        launcher_element = self.data_context.get_node('launcher', launcher_id)
        if launcher_element is None:
            log_debug('Launcher #{} not found'.format(launcher_id))
            return None
        launcher_data = self._parse_xml_to_dictionary(launcher_element)
        launcher = self.launcher_factory.create(launcher_data)

        return launcher

    def find_all_ids(self):
        launcher_ids = []
        launcher_id_elements = self.data_context.get_nodes('launcher/id')
        for launcher_id_element in launcher_id_elements:
            launcher_ids.append(launcher_id_element.text())

        return launcher_ids

    def find_all(self):
        launchers = []
        launcher_elements = self.data_context.get_nodes('launcher')
        for launcher_element in launcher_elements:
            launcher_data = self._parse_xml_to_dictionary(launcher_element)
            launcher = launcher_factory.create(launcher_data)
            launchers.append(launcher)

        return launchers

    def find_by_launcher_type(self, launcher_type):
        launchers = []
        launcher_elements = self.data_context.get_nodes_by('launcher', 'type', launcher_type )
        for launcher_element in launcher_elements:
            launcher_data = self._parse_xml_to_dictionary(launcher_element)
            launcher = launcher_factory.create(launcher_data)
            launchers.append(launcher)

        return launchers

    def find_by_category(self, category_id):
        launchers = []
        launcher_elements = self.data_context.get_nodes_by('launcher', 'categoryID', category_id )
        if launcher_elements is None or len(launcher_elements) == 0:
            log_debug('No launchers found in category #{}'.format(category_id))
            return launchers

        log_debug('{} launchers found in category #{}'.format(len(launcher_elements), category_id))
        for launcher_element in launcher_elements:
            launcher_data = self._parse_xml_to_dictionary(launcher_element)
            launcher = self.launcher_factory.create(launcher_data)
            launchers.append(launcher)

        return launchers

    def count(self):
        return len(self.data_context.get_nodes('launcher'))

    def save(self, launcher, update_launcher_timestamp = True):
        if update_launcher_timestamp:
            launcher.update_timestamp()

        launcher_id = launcher.get_id()
        launcher_data = launcher.get_data()
        self.data_context.save_node('launcher', launcher_id, launcher_data)        
        self.data_context.commit()

    def save_multiple(self, launchers, update_launcher_timestamp = True):
        for launcher in launchers:
            if update_launcher_timestamp:
                launcher.update_timestamp()

            launcher_id = launcher.get_id()
            launcher_data = launcher.get_data()
            
            self.data_context.save_node('launcher', launcher_id, launcher_data)       

        self.data_context.commit()

    def delete(self, launcher):
        launcher_id = launcher.get_id()
        self.data_context.remove_node('launcher', launcher_id)
        self.data_context.commit()

# -------------------------------------------------------------------------------------------------
# Repository class for Collection objects.
# Arranges retrieving and storing of the Collection launchers from and into the xml data file.
# -------------------------------------------------------------------------------------------------
class CollectionRepository(object):
    def __init__(self, data_context):
        log_debug('CollectionRepository::__init__()')
        self.data_context = data_context

    def _parse_xml_to_dictionary(self, collection_element):
        __debug_xml_parser = False
        collection = { 'type': LAUNCHER_COLLECTION }
        # Parse child tags of category
        for collection_child in collection_element:
            # By default read strings
            xml_text = collection_child.text if collection_child.text is not None else ''
            xml_text = text_unescape_XML(xml_text)
            xml_tag  = collection_child.tag
            if __debug_xml_parser: log_debug('{0} --> {1}'.format(xml_tag, xml_text.encode('utf-8')))

            # Internal data is always stored as Unicode. ElementTree already outputs Unicode.
            collection[xml_tag] = xml_text

        return collection

    def find(self, collection_id):
        collection_element = self.data_context.get_node('Collection', collection_id)
        if collection_element is None:
            log_debug('Cannot find collection with id {}'.format(collection_id))
            return None
        collection_dic = self._parse_xml_to_dictionary(collection_element)
        collection = self.launcher_factory.create(collection_data)

        return collection

    def find_all(self):
        collections = []
        collection_elements = self.data_context.get_nodes('Collection')
        log_debug('Found {0} collections'.format(len(collection_element)))
        for collection_element in collection_elements:
            collection_dic = self._parse_xml_to_dictionary(collection_element)
            collection = self.launcher_factory.create(collection_data)
            collections.append(collection)

        return collections

    def save(self, collection, update_launcher_timestamp = True):
        if update_launcher_timestamp:
            collection.update_timestamp()
        collection_id   = collection.get_id()
        collection_data = collection.get_data()
        self.data_context.save_node('Collection', collection_id, collection_data)
        self.data_context.commit()

    def save_multiple(self, collections, update_launcher_timestamp = True):
        for collection in collections:
            if update_launcher_timestamp:
                collection.update_timestamp()
            collection_id   = collection.get_id()
            collection_data = collection.get_data()
            self.data_context.save_node('Collection', collection_id, collection_data)
        self.data_context.commit()

    def delete(self, collection):
        collection_id = collection.get_id()
        self.data_context.remove_node('Collection', collection_id)
        self.data_context.commit()

# -------------------------------------------------------------------------------------------------
# Rom sets constants
# -------------------------------------------------------------------------------------------------
ROMSET_CPARENT  = '_index_CParent'
ROMSET_PCLONE   = '_index_PClone'
ROMSET_PARENTS  = '_parents'
ROMSET_DAT      = '_DAT'

# -------------------------------------------------------------------------------------------------
# Repository class for Rom Set objects.
# Arranges retrieving and storing of roms belonging to a particular launcher.
#
# NOTE ROMs in a collection are stored as a list and ROMs in Favourites are stored as
#      a dictionary. Convert the Collection list into an ordered dictionary and then
#      converted back the ordered dictionary into a list before saving the collection.
# -------------------------------------------------------------------------------------------------
class RomSetRepository(object):
    def __init__(self, roms_dir, store_as_dictionary = True):
        self.roms_dir = roms_dir
        self.store_as_dictionary = store_as_dictionary

    def find_by_launcher(self, launcher, view_mode = None):
        roms_base_noext = launcher.get_roms_base()
        if view_mode is None:
            view_mode = launcher.get_display_mode()
        
        if roms_base_noext is None:
            repository_file = self.roms_dir
        elif view_mode == LAUNCHER_DMODE_FLAT:
            repository_file = self.roms_dir.pjoin('{}.json'.format(roms_base_noext))
        else:
            repository_file = self.roms_dir.pjoin('{}_parents.json'.format(roms_base_noext))

        if not repository_file.exists():
            log_warning('Launcher "{0}" JSON not found.'.format(repository_file.getOriginalPath()))
            return None
        
        log_info('RomSetRepository.find_by_launcher() Loading ROMs in Launcher ({}:{}) Mode: {}...'.format(launcher.get_launcher_type_name(), launcher.get_name(), view_mode))

        roms_data = {}
        # --- Parse using json module ---
        # >> On Github issue #8 a user had an empty JSON file for ROMs. This raises
        #    exception exceptions.ValueError and launcher cannot be deleted. Deal
        #    with this exception so at least launcher can be rescanned.
        log_verb('RomSetRepository.find_by_launcher(): Loading roms from file {0}'.format(repository_file.getOriginalPath()))
        try:
            roms_data = repository_file.readJson()
        except ValueError:
            statinfo = repository_file.stat()
            log_error('RomSetRepository.find_by_launcher(): ValueError exception in json.load() function')
            log_error('RomSetRepository.find_by_launcher(): Dir  {0}'.format(repository_file.getOriginalPath()))
            log_error('RomSetRepository.find_by_launcher(): Size {0}'.format(statinfo.st_size))
            return None

        # --- Extract roms from JSON data structure and ensure version is correct ---
        if roms_data and isinstance(roms_data, list) and 'control' in roms_data[0]:
            control_str = roms_data[0]['control']
            version_int = roms_data[0]['version']
            roms_data   = roms_data[1]

        roms = {}
        if isinstance(roms_data, list):
            for rom_data in roms_data:
                r = Rom(rom_data)
                key = r.get_id()
                roms[key] = r
        else:
            for key in roms_data:
                r = Rom(roms_data[key])
                roms[key] = r

        return roms

    def find_index_file_by_launcher(self, launcher, type):
        roms_base_noext = launcher.get_roms_base()
        repository_file = self.roms_dir.pjoin('{}{}.json'.format(roms_base_noext, type))

        if not repository_file.exists():
            log_warning('RomSetRepository.find_index_file_by_launcher(): File not found {0}'.format(repository_file.getOriginalPath()))
            return None

        log_verb('RomSetRepository.find_index_file_by_launcher(): Loading rom index from file {0}'.format(repository_file.getOriginalPath()))
        try:
            index_data = repository_file.readJson()
        except ValueError:
            statinfo = repository_file.stat()
            log_error('RomSetRepository.find_index_file_by_launcher(): ValueError exception in json.load() function')
            log_error('RomSetRepository.find_index_file_by_launcher(): Dir  {0}'.format(repository_file.getOriginalPath()))
            log_error('RomSetRepository.find_index_file_by_launcher(): Size {0}'.format(statinfo.st_size))
            return None

        return index_data


    def save_rom_set(self, launcher, roms, view_mode = None):
        romdata = None
        if self.store_as_dictionary:
            romdata = {key: roms[key].get_data() for (key) in roms}
        else:
            romdata = [roms[key].get_data() for (key) in roms]

        # --- Create JSON data structure, including version number ---
        control_dic = {
            'control' : 'Advanced Emulator {} ROMs'.format(launcher.get_launcher_type_name()),
            'version' : AEL_STORAGE_FORMAT
        }
        raw_data = []
        raw_data.append(control_dic)
        raw_data.append(romdata)

        # >> Get file names
        roms_base_noext = launcher.get_roms_base()

        if view_mode is None:
            view_mode = launcher.get_display_mode()

        if roms_base_noext is None:
            repository_file = self.roms_dir
        elif view_mode == LAUNCHER_DMODE_FLAT:
            repository_file = self.roms_dir.pjoin('{}.json'.format(roms_base_noext))
        else:
            repository_file = self.roms_dir.pjoin('{}_parents.json'.format(roms_base_noext))

        log_verb('RomSetRepository.save_rom_set() Dir  {0}'.format(self.roms_dir.getOriginalPath()))
        log_verb('RomSetRepository.save_rom_set() JSON {0}'.format(repository_file.getOriginalPath()))

        # >> Write ROMs JSON dictionary.
        # >> Do note that there is a bug in the json module where the ensure_ascii=False flag can produce
        # >> a mix of unicode and str objects.
        # >> See http://stackoverflow.com/questions/18337407/saving-utf-8-texts-in-json-dumps-as-utf8-not-as-u-escape-sequence
        try:
            repository_file.writeJson(raw_data)
        except OSError:
            kodi_notify_warn('(OSError) Cannot write {0} file'.format(repository_file.getOriginalPath()))
            log_error('RomSetRepository.save_rom_set() (OSError) Cannot write {0} file'.format(repository_file.getOriginalPath()))
        except IOError:
            kodi_notify_warn('(IOError) Cannot write {0} file'.format(repository_file.getOriginalPath()))
            log_error('RomSetRepository.save_rom_set() (IOError) Cannot write {0} file'.format(repository_file.getOriginalPath()))       

    # -------------------------------------------------------------------------------------------------
    # Standard ROM databases
    # -------------------------------------------------------------------------------------------------
    #
    # <roms_base_noext>.json
    # <roms_base_noext>.xml
    # <roms_base_noext>_index_CParent.json
    # <roms_base_noext>_index_PClone.json
    # <roms_base_noext>_parents.json
    # <roms_base_noext>_DAT.json
    #
    def delete_all_by_launcher(self, launcher):
        roms_base_noext = launcher.get_roms_base()

        # >> Delete ROMs JSON file
        roms_json_FN = self.roms_dir.pjoin(roms_base_noext + '.json')
        if roms_json_FN.exists():
            log_info('Deleting ROMs JSON    "{0}"'.format(roms_json_FN.getOriginalPath()))
            roms_json_FN.unlink()

        # >> Delete ROMs info XML file
        roms_xml_FN = self.roms_dir.pjoin(roms_base_noext + '.xml')
        if roms_xml_FN.exists():
            log_info('Deleting ROMs XML     "{0}"'.format(roms_xml_FN.getOriginalPath()))
            roms_xml_FN.unlink()

        # >> Delete No-Intro/Redump stuff if exist
        roms_index_CParent_FN = self.roms_dir.pjoin(roms_base_noext + '_index_CParent.json')
        if roms_index_CParent_FN.exists():
            log_info('Deleting CParent JSON "{0}"'.format(roms_index_CParent_FN.getOriginalPath()))
            roms_index_CParent_FN.unlink()

        roms_index_PClone_FN = self.roms_dir.pjoin(roms_base_noext + '_index_PClone.json')
        if roms_index_PClone_FN.exists():
            log_info('Deleting PClone JSON  "{0}"'.format(roms_index_PClone_FN.getOriginalPath()))
            roms_index_PClone_FN.unlink()

        roms_parents_FN = self.roms_dir.pjoin(roms_base_noext + '_parents.json')
        if roms_parents_FN.exists():
            log_info('Deleting parents JSON "{0}"'.format(roms_parents_FN.getOriginalPath()))
            roms_parents_FN.unlink()

        roms_DAT_FN = self.roms_dir.pjoin(roms_base_noext + '_DAT.json')
        if roms_DAT_FN.exists():
            log_info('Deleting DAT JSON     "{0}"'.format(roms_DAT_FN.getOriginalPath()))
            roms_DAT_FN.unlink()

        return

    def delete_by_launcher(self, launcher, kind):
        roms_base_noext     = launcher.get_roms_base()
        rom_set_file_name   = roms_base_noext + kind
        rom_set_path        = self.roms_dir.pjoin(rom_set_file_name + '.json')

        if rom_set_path.exists():
            log_info('delete_by_launcher() Deleting {0}'.format(rom_set_path.getPath()))
            rom_set_path.unlink()

        return

# -------------------------------------------------------------------------------------------------
# Factory class for creating the specific/derived launchers based upon the given type and 
# dictionary with launcher data.
# -------------------------------------------------------------------------------------------------
class LauncherFactory(object):
    def __init__(self, settings, g_PATHS, executorFactory):
        self.settings = settings
        self.plugin_data_dir = g_PATHS.ADDON_DATA_DIR
        self.executorFactory = executorFactory

        self._initialize_folders()

        self.virtual_launchers = {}
        self._initialize_virtual_launchers()

    def _initialize_folders(self):
        self.ROMS_DIR                   = self.plugin_data_dir.pjoin('db_ROMs')
        self.COLLECTIONS_FILE_PATH      = self.plugin_data_dir.pjoin('collections.xml')
        self.COLLECTIONS_DIR            = self.plugin_data_dir.pjoin('db_Collections')
        self.VIRTUAL_CAT_TITLE_DIR      = self.plugin_data_dir.pjoin('db_title')
        self.VIRTUAL_CAT_YEARS_DIR      = self.plugin_data_dir.pjoin('db_years')
        self.VIRTUAL_CAT_GENRE_DIR      = self.plugin_data_dir.pjoin('db_genre')
        self.VIRTUAL_CAT_DEVELOPER_DIR  = self.plugin_data_dir.pjoin('db_developer')
        self.VIRTUAL_CAT_CATEGORY_DIR   = self.plugin_data_dir.pjoin('db_category')
        self.VIRTUAL_CAT_NPLAYERS_DIR   = self.plugin_data_dir.pjoin('db_nplayers')
        self.VIRTUAL_CAT_ESRB_DIR       = self.plugin_data_dir.pjoin('db_esrb')
        self.VIRTUAL_CAT_RATING_DIR     = self.plugin_data_dir.pjoin('db_rating')

        if not self.ROMS_DIR.exists():                  self.ROMS_DIR.makedirs()
        if not self.VIRTUAL_CAT_TITLE_DIR.exists():     self.VIRTUAL_CAT_TITLE_DIR.makedirs()
        if not self.VIRTUAL_CAT_YEARS_DIR.exists():     self.VIRTUAL_CAT_YEARS_DIR.makedirs()
        if not self.VIRTUAL_CAT_GENRE_DIR.exists():     self.VIRTUAL_CAT_GENRE_DIR.makedirs()
        if not self.VIRTUAL_CAT_DEVELOPER_DIR.exists(): self.VIRTUAL_CAT_DEVELOPER_DIR.makedirs()
        if not self.VIRTUAL_CAT_CATEGORY_DIR.exists():  self.VIRTUAL_CAT_CATEGORY_DIR.makedirs()
        if not self.VIRTUAL_CAT_NPLAYERS_DIR.exists():  self.VIRTUAL_CAT_NPLAYERS_DIR.makedirs()
        if not self.VIRTUAL_CAT_ESRB_DIR.exists():      self.VIRTUAL_CAT_ESRB_DIR.makedirs()
        if not self.VIRTUAL_CAT_RATING_DIR.exists():    self.VIRTUAL_CAT_RATING_DIR.makedirs()
        if not self.COLLECTIONS_DIR.exists():           self.COLLECTIONS_DIR.makedirs()

    def _initialize_virtual_launchers(self):
        log_info('LauncherFactory::_initialize_virtual_launchers() Preinitializing virtual launchers.')

        # create default data
        recently_played_roms_dic = {'id': VLAUNCHER_RECENT_ID, 'm_name': 'Recently played', 'roms_base_noext': 'history' }
        most_played_roms_dic     = {'id': VLAUNCHER_MOST_PLAYED_ID, 'm_name': 'Most played', 'roms_base_noext': 'most_played' }
        favourites_roms_dic      = {'id': VLAUNCHER_FAVOURITES_ID, 'm_name': 'Favourites', 'roms_base_noext': 'favourites' }

        # fill in memory dictionary
        self.virtual_launchers[VLAUNCHER_RECENT_ID]      = VirtualLauncher(recently_played_roms_dic, self.settings, RomSetRepository(self.plugin_data_dir))
        self.virtual_launchers[VLAUNCHER_MOST_PLAYED_ID] = VirtualLauncher(most_played_roms_dic, self.settings, RomSetRepository(self.plugin_data_dir))
        self.virtual_launchers[VLAUNCHER_FAVOURITES_ID]  = VirtualLauncher(favourites_roms_dic, self.settings, RomSetRepository(self.plugin_data_dir))

    def _load(self, launcher_type, launcher_data):
        if launcher_type in self.virtual_launchers:
            return self.virtual_launchers[launcher_type]

        if launcher_type == LAUNCHER_STANDALONE:
            return ApplicationLauncher(launcher_data, self.settings, self.executorFactory)

        if launcher_type == LAUNCHER_FAVOURITES:
            return KodiLauncher(launcher_data, self.settings, self.executorFactory)
        
        if launcher_type == LAUNCHER_COLLECTION:
            collection_romset_repository = RomSetRepository(self.COLLECTIONS_DIR, False)
            return CollectionLauncher(launcher_data, settings, collection_romset_repository)

        statsStrategy = RomStatisticsStrategy(self.virtual_launchers[VLAUNCHER_RECENT_ID], self.virtual_launchers[VLAUNCHER_MOST_PLAYED_ID])
        romset_repository = RomSetRepository(self.ROMS_DIR)
        if launcher_type == LAUNCHER_RETROPLAYER:
            return RetroplayerLauncher(launcher_data, self.settings, None, romset_repository, None, self.settings['escape_romfile'])

        if launcher_type == LAUNCHER_RETROARCH:
            return RetroarchLauncher(launcher_data, self.settings, self.executorFactory, romset_repository, statsStrategy, self.settings['escape_romfile'])

        if launcher_type == LAUNCHER_ROM:
            return StandardRomLauncher(launcher_data, self.settings, self.executorFactory, romset_repository, statsStrategy, self.settings['escape_romfile'])

        if launcher_type == LAUNCHER_LNK:
            return LnkLauncher(launcher_data, self.settings, self.executorFactory, romset_repository ,statsStrategy, self.settings['escape_romfile'])

        if launcher_type == LAUNCHER_STEAM:
            return SteamLauncher(launcher_data, self.settings, self.executorFactory, romset_repository, statsStrategy)

        if launcher_type == LAUNCHER_NVGAMESTREAM:
            return NvidiaGameStreamLauncher(launcher_data, self.settings, self.executorFactory, romset_repository, statsStrategy)

        log_warning('Unsupported launcher requested. Type "{0}"'.format(launcher_type))

        return None

    def get_supported_types(self):
        typeOptions = collections.OrderedDict()
        typeOptions[LAUNCHER_STANDALONE]   = 'Standalone launcher (Game/Application)'
        typeOptions[LAUNCHER_FAVOURITES]   = 'Kodi favourite launcher'
        typeOptions[LAUNCHER_ROM]          = 'ROM launcher (Emulator)'
        typeOptions[LAUNCHER_RETROPLAYER]  = 'ROM launcher (Kodi Retroplayer)'
        typeOptions[LAUNCHER_RETROARCH]    = 'ROM launcher (Retroarch)'
        typeOptions[LAUNCHER_NVGAMESTREAM] = 'Nvidia GameStream'

        if not is_android():
            typeOptions[LAUNCHER_STEAM] = 'Steam launcher'
        if is_windows():
            typeOptions[LAUNCHER_LNK] = 'LNK launcher (Windows only)'

        return typeOptions

    def create(self, launcher_data):
        launcher_type = launcher_data['type'] if 'type' in launcher_data else None
        log_debug('Creating launcher instance for launcher#{} type({})'.format(launcher_data['id'], launcher_type))
        return self._load(launcher_type, launcher_data)

    def create_new(self, launcher_type):
        return self._load(launcher_type, None)

# -------------------------------------------------------------------------------------------------
# Strategy class for updating the rom play statistics.
# Updates the amount of times a rom is played and which rom recently has been played.
# -------------------------------------------------------------------------------------------------
class RomStatisticsStrategy(object):
    def __init__(self, recent_played_launcher, most_played_launcher):
        self.MAX_RECENT_PLAYED_ROMS = 100
        self.recent_played_launcher = recent_played_launcher
        self.most_played_launcher = most_played_launcher

    def update_launched_rom_stats(self, recent_rom):
        ## --- Compute ROM recently played list ---
        recently_played_roms = self.recent_played_launcher.get_roms()
        recently_played_roms = [rom for rom in recently_played_roms if rom.get_id() != recent_rom.get_id()]
        recently_played_roms.insert(0, recent_rom)

        if len(recently_played_roms) > self.MAX_RECENT_PLAYED_ROMS:
            log_debug('RomStatisticsStrategy() len(recently_played_roms) = {0}'.format(len(recently_played_roms)))
            log_debug('RomStatisticsStrategy() Trimming list to {0} ROMs'.format(self.MAX_RECENT_PLAYED_ROMS))

            temp_list            = recently_played_roms[:self.MAX_RECENT_PLAYED_ROMS]
            recently_played_roms = temp_list

        self.recent_played_launcher.update_rom_set(recently_played_roms)

        recent_rom.increase_launch_count()

        # --- Compute most played ROM statistics ---
        most_played_roms = self.most_played_launcher.get_roms()
        if most_played_roms is None:
            most_played_roms = []
        else:
            most_played_roms = [rom for rom in most_played_roms if rom.get_id() != recent_rom.get_id()]
        most_played_roms.append(recent_rom)
        self.most_played_launcher.update_rom_set(most_played_roms)

# -------------------------------------------------------------------------------------------------
# Abstract base class for business objects which support the generic metadata properties
# -------------------------------------------------------------------------------------------------
class MetaDataItem(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, entity_data):
        self.entity_data = entity_data

    def get_id(self):
        return self.entity_data['id']

    def get_name(self):
        if 'm_name' in self.entity_data:
           return self.entity_data['m_name']
        else:
           return 'Unknown'

    def get_releaseyear(self):
        return self.entity_data['m_year'] if 'm_year' in self.entity_data else ''

    def get_genre(self):
        return self.entity_data['m_genre'] if 'm_genre' in self.entity_data else ''
    
    def get_developer(self):
        return self.entity_data['m_developer'] if 'm_developer' in self.entity_data else ''

    def get_rating(self):
        return int(self.entity_data['m_rating']) if self.entity_data['m_rating'] else -1

    def get_plot(self):
        return self.entity_data['m_plot'] if 'm_plot' in self.entity_data else ''

    def is_finished(self):
        return 'finished' in self.entity_data and self.entity_data['finished']
    
    def get_state(self):
        finished = self.entity_data['finished']
        finished_display = 'Finished' if finished == True else 'Unfinished'
        return finished_display

    def get_data_dic(self):
        return self.entity_data

    def copy_of_data(self):
        return self.entity_data.copy()

    def get_custom_attribute(self, key, default_value = None):
        return self.entity_data[key] if key in self.entity_data else default_value

    def has_asset(self, asset_info):
        if not asset_info.key in self.entity_data: return False

        return self.entity_data[asset_info.key] != None and self.entity_data[asset_info.key] != ''

    def get_asset(self, asset_info):
        return self.entity_data[asset_info.key] if asset_info.key in self.entity_data else None

    def get_asset_file(self, asset_info):
        asset = self.get_asset(asset_info)
        if asset is None: return None

        return FileNameFactory.create(asset)

    def set_id(self, id):
        self.entity_data['id'] = id

    def set_name(self, name):
        self.entity_data['m_name'] = name

    def update_releaseyear(self, releaseyear):
        self.entity_data['m_year'] = releaseyear

    def update_genre(self, genre):
        self.entity_data['m_genre'] = genre

    def update_developer(self, developer):
        self.entity_data['m_developer'] = developer

    def update_rating(self, rating):
        try:
            self.entity_data['m_rating'] = int(rating)
        except:
            self.entity_data['m_rating'] = ''

    def update_plot(self, plot):
        self.entity_data['m_plot'] = plot

    def change_finished_status(self):
        finished = self.entity_data['finished']
        finished = False if finished else True
        self.entity_data['finished'] = finished

    def set_asset(self, asset_info, path):
        self.entity_data[asset_info.key] = path.getOriginalPath()

    def clear_asset(self, asset_info):
        self.entity_data[asset_info.key] = ''

    def import_data(self, data):
        for key in data:
            self.entity_data[key] = data[key]

    def set_custom_attribute(self, key, value):
        self.entity_data[key] = value

    def _get_value_as_filename(self, field):
        if not field in self.entity_data:
            return None

        path = self.entity_data[field]
        if path == '':
            return None

        return FileNameFactory.create(path)

# -------------------------------------------------------------------------------------------------
# Class representing the categories in AEL.
# Contains code to generate the context menus passed to Dialog.select()
# -------------------------------------------------------------------------------------------------
class Category(MetaDataItem):
    def __init__(self, category_data = None):
        super(Category, self).__init__(category_data)

        if self.entity_data is None:
            # NOTE place all new databse dictionary generation code in diso_IO.py to have it
            #      centralised in one place. Easier that have this code disperse over several objects.
            self.entity_data = {
             'id' : misc_generate_random_SID(),
             'm_name' : '',
             'm_year' : '',
             'm_genre' : '',
             'm_developer' : '',
             'm_rating' : '',
             'm_plot' : '',
             'finished' : False,
             'default_icon' : 's_icon',
             'default_fanart' : 's_fanart',
             'default_banner' : 's_banner',
             'default_poster' : 's_poster',
             'default_clearlogo' : 's_clearlogo',
             'Asset_Prefix' : '',
             's_icon' : '',
             's_fanart' : '',
             's_banner' : '',
             's_poster' : '',
             's_clearlogo' : '',
             's_trailer' : ''
             }

    def get_assets(self):
        assets = {}
        asset_keys = [ASSET_BANNER, ASSET_ICON, ASSET_FANART, ASSET_POSTER, ASSET_CLEARLOGO, ASSET_TRAILER]

        asset_factory = AssetInfoFactory.create()
        asset_kinds = asset_factory.get_assets_by(asset_keys)
        for asset_kind in asset_kinds:
            asset = self.entity_data[asset_kind.key] if self.entity_data[asset_kind.key] else ''
            assets[asset_kind] = asset

        return assets

    def is_virtual(self):
        return False

    def get_asset_defaults(self):
        default_assets = {}
        default_asset_keys = [ASSET_BANNER, ASSET_ICON, ASSET_FANART, ASSET_POSTER, ASSET_CLEARLOGO]
        asset_factory = AssetInfoFactory.create()
        default_asset_kinds = asset_factory.get_assets_by(default_asset_keys)

        for asset_kind in default_asset_kinds:
            mapped_asset_key = self.entity_data[asset_kind.default_key] if self.entity_data[asset_kind.default_key] else ''
            mapped_asset_kind = asset_factory.get_asset_info_by_namekey(mapped_asset_key)
            
            default_assets[asset_kind] = mapped_asset_kind

        return default_assets

    def set_default_asset(self, asset_kind, mapped_to_kind):
        self.entity_data[asset_kind.default_key] = mapped_to_kind.key

    def get_trailer(self):
        return self.entity_data['s_trailer']

    def get_edit_options(self):
        options = collections.OrderedDict()
        options['EDIT_METADATA']       = 'Edit Metadata ...'
        options['EDIT_ASSETS']         = 'Edit Assets/Artwork ...'
        options['SET_DEFAULT_ASSETS']  = 'Choose default Assets/Artwork ...'
        options['CATEGORY_STATUS']     = 'Category status: {0}'.format(self.get_state())
        options['EXPORT_CATEGORY_XML'] = 'Export Category XML configuration ...'
        options['DELETE_CATEGORY']     = 'Delete Category'

        return options

    def get_metadata_edit_options(self, settings_dic):
        # >> Metadata edit dialog
        NFO_FileName = fs_get_category_NFO_name(settings_dic, self.entity_data)
        NFO_found_str = 'NFO found' if NFO_FileName.exists() else 'NFO not found'
        plot_str = text_limit_string(self.get_plot(), PLOT_STR_MAXSIZE)

        options = collections.OrderedDict()
        options['EDIT_TITLE']             = "Edit Title: '{0}'".format(self.get_name())
        options['EDIT_RELEASEYEAR']       = "Edit Release Year: '{0}'".format(self.get_releaseyear())
        options['EDIT_GENRE']             = "Edit Genre: '{0}'".format(self.get_genre())
        options['EDIT_DEVELOPER']         = "Edit Developer: '{0}'".format(self.get_developer())
        options['EDIT_RATING']            = "Edit Rating: '{0}'".format(self.get_rating())
        options['EDIT_PLOT']              = "Edit Plot: '{0}'".format(plot_str)
        options['IMPORT_NFO_FILE']        = 'Import NFO file (default, {0})'.format(NFO_found_str)
        options['IMPORT_NFO_FILE_BROWSE'] = 'Import NFO file (browse NFO file) ...'
        options['SAVE_NFO_FILE']          = 'Save NFO file (default location)'

        return options

    @staticmethod
    def create_root_category():
        c = {'id' : VCATEGORY_ADDONROOT_ID, 'm_name' : 'Root category' }
        return Category(c)

# -------------------------------------------------------------------------------------------------
# Class representing the virtual categories in AEL.
# -------------------------------------------------------------------------------------------------
class VirtualCategory(Category):
    def is_virtual(self):
        return True

# -------------------------------------------------------------------------------------------------
# Class representing a ROM file you can play through AEL.
# -------------------------------------------------------------------------------------------------
class Rom(MetaDataItem):
    def __init__(self, rom_data = None):
        super(Rom, self).__init__(rom_data)
        if self.entity_data is None:
            self.entity_data = {
             'id' : misc_generate_random_SID(),
             'm_name' : '',
             'm_year' : '',
             'm_genre' : '',
             'm_developer' : '',
             'm_nplayers' : '',
             'm_esrb' : ESRB_PENDING,
             'm_rating' : '',
             'm_plot' : '',
             'filename' : '',
             'disks' : [],
             'altapp' : '',
             'altarg' : '',
             'finished' : False,
             'nointro_status' : NOINTRO_STATUS_NONE,
             'pclone_status' : PCLONE_STATUS_NONE,
             'cloneof' : '',
             's_title' : '',
             's_snap' : '',
             's_boxfront' : '',
             's_boxback' : '',
             's_cartridge' : '',
             's_fanart' : '',
             's_banner' : '',
             's_clearlogo' : '',
             's_flyer' : '',
             's_map' : '',
             's_manual' : '',
             's_trailer' : ''
             }

    # is this virtual only? Should we make a VirtualRom(Rom)?
    def get_launcher_id(self):
        return self.entity_data['launcherID']

    def is_virtual_rom(self):
        return 'launcherID' in self.entity_data

    def get_nointro_status(self):
        return self.entity_data['nointro_status']

    def get_pclone_status(self):
        return self.entity_data['pclone_status']

    def get_clone(self):
        return self.entity_data['cloneof']
    
    def has_alternative_application(self):
        return 'altapp' in self.entity_data and self.entity_data['altapp']

    def get_alternative_application(self):
        return self.entity_data['altapp']

    def has_alternative_arguments(self):
        return 'altarg' in self.entity_data and self.entity_data['altarg']

    def get_alternative_arguments(self):
        return self.entity_data['altarg']

    def get_filename(self):
        return self.entity_data['filename']

    def get_file(self):
        return self._get_value_as_filename('filename')

    def has_multiple_disks(self):
        return 'disks' in self.entity_data and self.entity_data['disks']

    def get_disks(self):
        if not self.has_multiple_disks():
            return []

        return self.entity_data['disks']

    def get_nfo_file(self):
        ROMFileName = self.get_file()
        nfo_file_path = ROMFileName.switchExtension('.nfo')
        return nfo_file_path

    def get_number_of_players(self):
        return self.entity_data['m_nplayers']

    def get_esrb_rating(self):
        return self.entity_data['m_esrb']

    def get_favourite_status(self):
        return self.entity_data['fav_status']

    def get_launch_count(self):
        return self.entity_data['launch_count']

    def set_file(self, file):
        self.entity_data['filename'] = file.getOriginalPath()

    def add_disk(self, disk):
        self.entity_data['disks'].append(disk)

    def set_number_of_players(self, amount):
        self.entity_data['m_nplayers'] = amount

    def set_esrb_rating(self, esrb):
        self.entity_data['m_esrb'] = esrb

    def set_nointro_status(self, status):
        self.entity_data['nointro_status'] = status

    def set_pclone_status(self, status):
        self.entity_data['pclone_status'] = status

    def set_clone(self, clone):
        self.entity_data['cloneof'] = clone

    # todo: definitly something for a inherited FavouriteRom class
    # >> Favourite ROM unique fields
    # >> Favourite ROMs in "Most played ROMs" DB also have 'launch_count' field.
    def set_favourite_status(self, state):
        self.entity_data['fav_status'] = state

    def increase_launch_count(self):
        launch_count = self.entity_data['launch_count'] if 'launch_count' in self.entity_data else 0
        launch_count += 1
        self.entity_data['launch_count'] = launch_count

    def set_alternative_application(self, application):
        self.entity_data['altapp'] = application

    def set_alternative_arguments(self, arg):
        self.entity_data['altarg'] = arg

    def copy(self):
        data = self.copy_of_data()
        return Rom(data)

    def get_edit_options(self, category_id):
        delete_rom_txt = 'Delete ROM'
        if category_id == VCATEGORY_FAVOURITES_ID:
            delete_rom_txt = 'Delete Favourite ROM'
        if category_id == VCATEGORY_COLLECTIONS_ID:
            delete_rom_txt = 'Delete Collection ROM'

        options = collections.OrderedDict()
        options['EDIT_METADATA']    = 'Edit Metadata ...'
        options['EDIT_ASSETS']      = 'Edit Assets/Artwork ...'
        options['ROM_STATUS']       = 'Status: {0}'.format(self.get_state()).encode('utf-8')

        options['ADVANCED_MODS']    = 'Advanced Modifications ...'
        options['DELETE_ROM']       = delete_rom_txt

        if category_id == VCATEGORY_FAVOURITES_ID:
            options['MANAGE_FAV_ROM']   = 'Manage Favourite ROM object ...'
            
        elif category_id == VCATEGORY_COLLECTIONS_ID:
            options['MANAGE_COL_ROM']       = 'Manage Collection ROM object ...'
            options['MANAGE_COL_ROM_POS']   = 'Manage Collection ROM position ...'

        return options

    # >> Metadata edit dialog
    def get_metadata_edit_options(self):
        NFO_FileName = fs_get_ROM_NFO_name(self.get_data())
        NFO_found_str = 'NFO found' if NFO_FileName.exists() else 'NFO not found'
        plot_str = text_limit_string(self.entity_data['m_plot'], PLOT_STR_MAXSIZE)

        rating = self.get_rating()
        if rating == -1:
            rating = 'not rated'

        options = collections.OrderedDict()
        options['EDIT_TITLE']             = u"Edit Title: '{0}'".format(self.get_name()).encode('utf-8')
        options['EDIT_RELEASEYEAR']       = u"Edit Release Year: '{0}'".format(self.get_releaseyear()).encode('utf-8')
        options['EDIT_GENRE']             = u"Edit Genre: '{0}'".format(self.get_genre()).encode('utf-8')
        options['EDIT_DEVELOPER']         = u"Edit Developer: '{0}'".format(self.get_developer()).encode('utf-8')
        options['EDIT_NPLAYERS']          = u"Edit NPlayers: '{0}'".format(self.get_number_of_players()).encode('utf-8')
        options['EDIT_ESRB']              = u"Edit ESRB rating: '{0}'".format(self.get_esrb_rating()).encode('utf-8')
        options['EDIT_RATING']            = u"Edit Rating: '{0}'".format(rating).encode('utf-8')
        options['EDIT_PLOT']              = u"Edit Plot: '{0}'".format(plot_str).encode('utf-8')
        options['LOAD_PLOT']              = "Load Plot from TXT file ..."
        options['IMPORT_NFO_FILE']        = u"Import NFO file (default, {0})".format(NFO_found_str).encode('utf-8')
        options['SAVE_NFO_FILE']          = "Save NFO file (default location)"

        return options

    #
    # Returns a dictionary of options to choose from
    # with which you can do advanced modifications on this specific rom.
    #
    def get_advanced_modification_options(self):
        options = collections.OrderedDict()
        options['CHANGE_ROM_FILE']          = "Change ROM file: '{0}'".format(self.get_filename())
        options['CHANGE_ALT_APPLICATION']   = "Alternative application: '{0}'".format(self.get_alternative_application())
        options['CHANGE_ALT_ARGUMENTS']     = "Alternative arguments: '{0}'".format(self.get_alternative_arguments())
        return options

    #
    # Reads an NFO file with ROM information.
    # See comments in fs_export_ROM_NFO() about verbosity.
    # About reading files in Unicode http://stackoverflow.com/questions/147741/character-reading-from-file-in-python
    #
    # todo: Replace with nfo_file_path.readXml() and just use XPath
    def update_with_nfo_file(self, nfo_file_path, verbose = True):
        log_debug('Rom.update_with_nfo_file() Loading "{0}"'.format(nfo_file_path.getPath()))
        if not nfo_file_path.exists():
            if verbose:
                kodi_notify_warn('NFO file not found {0}'.format(nfo_file_path.getPath()))
            log_debug("Rom.update_with_nfo_file() NFO file not found '{0}'".format(nfo_file_path.getOriginalPath()))
            return False

        # todo: Replace with nfo_file_path.readXml() and just use XPath

        # --- Import data ---
        # >> Read file, put in a string and remove line endings.
        # >> We assume NFO files are UTF-8. Decode data to Unicode.
        # file = open(nfo_file_path, 'rt')
        nfo_str = nfo_file_path.readAllUnicode()
        nfo_str = nfo_str.replace('\r', '').replace('\n', '')

        # Search for metadata tags. Regular expression is non-greedy.
        # See https://docs.python.org/2/library/re.html#re.findall
        # If RE has no groups it returns a list of strings with the matches.
        # If RE has groups then it returns a list of groups.
        item_title     = re.findall('<title>(.*?)</title>', nfo_str)
        item_year      = re.findall('<year>(.*?)</year>', nfo_str)
        item_genre     = re.findall('<genre>(.*?)</genre>', nfo_str)
        item_developer = re.findall('<developer>(.*?)</developer>', nfo_str)
        item_nplayers  = re.findall('<nplayers>(.*?)</nplayers>', nfo_str)
        item_esrb      = re.findall('<esrb>(.*?)</esrb>', nfo_str)
        item_rating    = re.findall('<rating>(.*?)</rating>', nfo_str)
        item_plot      = re.findall('<plot>(.*?)</plot>', nfo_str)

        # >> Future work: ESRB and maybe nplayer fields must be sanitized.
        if len(item_title) > 0:     self.entity_data['m_name']      = text_unescape_XML(item_title[0])
        if len(item_year) > 0:      self.entity_data['m_year']      = text_unescape_XML(item_year[0])
        if len(item_genre) > 0:     self.entity_data['m_genre']     = text_unescape_XML(item_genre[0])
        if len(item_developer) > 0: self.entity_data['m_developer'] = text_unescape_XML(item_developer[0])
        if len(item_nplayers) > 0:  self.entity_data['m_nplayers']  = text_unescape_XML(item_nplayers[0])
        if len(item_esrb) > 0:      self.entity_data['m_esrb']      = text_unescape_XML(item_esrb[0])
        if len(item_rating) > 0:    self.entity_data['m_rating']    = text_unescape_XML(item_rating[0])
        if len(item_plot) > 0:      self.entity_data['m_plot']      = text_unescape_XML(item_plot[0])

        if verbose:
            kodi_notify('Imported {0}'.format(nfo_file_path.getPath()))

        return

    def __str__(self):
        """Overrides the default implementation"""
        return json.dumps(self.entity_data)

# -------------------------------------------------------------------------------------------------
# Abstract base class for launching anything that is supported.
# Implement classes that inherit this base class to support new ways of launching.
# -------------------------------------------------------------------------------------------------
class Launcher(MetaDataItem):
    __metaclass__ = abc.ABCMeta

    def __init__(self, launcher_data, settings, executorFactory):
        super(Launcher, self).__init__(launcher_data)

        if self.entity_data is None:
            self.entity_data = self._default_data()

        self.settings        = settings
        self.executorFactory = executorFactory
        
        self.application    = None
        self.arguments      = None
        self.title          = None

    def _default_data(self):
        l = {'id' : misc_generate_random_SID(),
             'm_name' : '',
             'm_year' : '',
             'm_genre' : '',
             'm_developer' : '',
             'm_rating' : '',
             'm_plot' : '',
             'platform' : '',
             'categoryID' : '',
             'application' : '',
             'args' : '',
             'args_extra' : [],
             'rompath' : '',
             'romext' : '',
             'finished': False,
             'toggle_window' : False, # Former 'minimize'
             'non_blocking' : False,
             'multidisc' : True,
             'roms_base_noext' : '',
             'nointro_xml_file' : '',
             'nointro_display_mode' : NOINTRO_DMODE_ALL,
             'launcher_display_mode' : LAUNCHER_DMODE_FLAT,
             'num_roms' : 0,
             'num_parents' : 0,
             'num_clones' : 0,
             'num_have' : 0,
             'num_miss' : 0,
             'num_unknown' : 0,
             'timestamp_launcher' : 0.0,
             'timestamp_report' : 0.0,
             'default_icon' : 's_icon',
             'default_fanart' : 's_fanart',
             'default_banner' : 's_banner',
             'default_poster' : 's_poster',
             'default_clearlogo' : 's_clearlogo',
             'default_controller' : 's_controller',
             'Asset_Prefix' : '',
             's_icon' : '',
             's_fanart' : '',
             's_banner' : '',
             's_poster' : '',
             's_clearlogo' : '',
             's_controller' : '',
             's_trailer' : '',
             'roms_default_icon' : 's_boxfront',
             'roms_default_fanart' : 's_fanart',
             'roms_default_banner' : 's_banner',
             'roms_default_poster' : 's_flyer',
             'roms_default_clearlogo' : 's_clearlogo',
             'ROM_asset_path' : '',
             'path_title' : '',
             'path_snap' : '',
             'path_boxfront' : '',
             'path_boxback' : '',
             'path_cartridge' : '',
             'path_fanart' : '',
             'path_banner' : '',
             'path_clearlogo' : '',
             'path_flyer' : '',
             'path_map' : '',
             'path_manual' : '',
             'path_trailer' : ''
        }

        return l

    #
    # Build new launcher.
    # Leave category_id empty to add launcher to root folder.
    #
    def build(self, category):
        wizard = DummyWizardDialog('categoryID', category.get_id(), None)
        wizard = DummyWizardDialog('type', self.get_launcher_type(), wizard)
        wizard = self._get_builder_wizard(wizard)

        # --- Create new launcher. categories.xml is save at the end of this function ---
        # NOTE than in the database original paths are always stored.
        self.entity_data = wizard.runWizard(self.entity_data)
        if not self.entity_data:
            return False

        if self.supports_launching_roms():
            # Choose launcher ROM XML filename. There may be launchers with same name in different categories, or
            # even launcher with the same name in the same category.

            roms_base_noext = fs_get_ROMs_basename(category.get_name(), self.entity_data['m_name'], self.get_id())
            self.entity_data['roms_base_noext'] = roms_base_noext
            
            # --- Selected asset path ---
            # A) User chooses one and only one assets path
            # B) If this path is different from the ROM path then asset naming scheme 1 is used.
            # B) If this path is the same as the ROM path then asset naming scheme 2 is used.
            # >> Create asset directories. Function detects if we are using naming scheme 1 or 2.
            # >> launcher is edited using Python passing by assignment.
            assets_init_asset_dir(FileNameFactory.create(self.entity_data['assets_path']), self.entity_data)

        self.entity_data['timestamp_launcher'] = time.time()

        return True

    #
    # Launchs a ROM launcher or standalone launcher
    # For standalone launchers romext is the extension of the application (only used in Windoze)
    #
    @abc.abstractmethod
    def launch(self):
        executor = self.executorFactory.create(self.application) if self.executorFactory is not None else None
        if executor is None:
            log_error("Cannot create an executor for {0}".format(self.application.getPath()))
            kodi_notify_error('Cannot execute application')
            return

        log_debug('Launcher launching = "{0}"'.format(self.title))
        log_debug('Launcher application = "{0}"'.format(self.application.getPath()))
        log_debug('Launcher arguments = "{0}"'.format(self.arguments))
        log_debug('Launcher executor = "{0}"'.format(executor.__class__.__name__))

        self.preExecution(self.title, self.is_in_windowed_mode())
        executor.execute(self.application, self.arguments, self.is_non_blocking())
        self.postExecution(self.is_in_windowed_mode())

        pass

    #
    # These two functions do things like stopping music before lunch, toggling full screen, etc.
    # Variables set in this function:
    # self.kodi_was_playing      True if Kodi player was ON, False otherwise
    # self.kodi_audio_suspended  True if Kodi audio suspended before launching
    #
    # def _run_before_execution(self, rom_title, toggle_screen_flag):
    def preExecution(self, title, toggle_screen_flag):
        # --- User notification ---
        if self.settings['display_launcher_notify']:
            kodi_notify('Launching {0}'.format(title))

        # --- Stop/Pause Kodi mediaplayer if requested in settings ---
        self.kodi_was_playing = False
        # id="media_state_action" default="0" values="Stop|Pause|Let Play"
        media_state_action = self.settings['media_state_action']
        media_state_str = ['Stop', 'Pause', 'Let Play'][media_state_action]
        log_verb('_run_before_execution() media_state_action is "{0}" ({1})'.format(media_state_str, media_state_action))
        if media_state_action == 0 and xbmc.Player().isPlaying():
            log_verb('_run_before_execution() Calling xbmc.Player().stop()')
            xbmc.Player().stop()
            xbmc.sleep(100)
            self.kodi_was_playing = True
        elif media_state_action == 1 and xbmc.Player().isPlaying():
            log_verb('_run_before_execution() Calling xbmc.Player().pause()')
            xbmc.Player().pause()
            xbmc.sleep(100)
            self.kodi_was_playing = True

        # --- Force audio suspend if requested in "Settings" --> "Advanced"
        # >> See http://forum.kodi.tv/showthread.php?tid=164522
        self.kodi_audio_suspended = False
        if self.settings['suspend_audio_engine']:
            log_verb('_run_before_execution() Suspending Kodi audio engine')
            xbmc.audioSuspend()
            xbmc.enableNavSounds(False)
            xbmc.sleep(100)
            self.kodi_audio_suspended = True
        else:
            log_verb('_run_before_execution() DO NOT suspend Kodi audio engine')

        # --- Force joystick suspend if requested in "Settings" --> "Advanced"
        # >> See https://forum.kodi.tv/showthread.php?tid=287826&pid=2627128#pid2627128
        # >> See https://forum.kodi.tv/showthread.php?tid=157499&pid=1722549&highlight=input.enablejoystick#pid1722549
        # >> See https://forum.kodi.tv/showthread.php?tid=313615
        self.kodi_joystick_suspended = False
        # if self.settings['suspend_joystick_engine']:
            # log_verb('_run_before_execution() Suspending Kodi joystick engine')
            # >> Research. Get the value of the setting first
            # >> Apparently input.enablejoystick is not supported on Kodi Krypton anymore.
            # c_str = ('{"id" : 1, "jsonrpc" : "2.0",'
            #          ' "method" : "Settings.GetSettingValue",'
            #          ' "params" : {"setting":"input.enablejoystick"}}')
            # response = xbmc.executeJSONRPC(c_str)
            # log_debug('JSON      ''{0}'''.format(c_str))
            # log_debug('Response  ''{0}'''.format(response))

            # c_str = ('{"id" : 1, "jsonrpc" : "2.0",'
            #          ' "method" : "Settings.SetSettingValue",'
            #          ' "params" : {"setting" : "input.enablejoystick", "value" : false} }')
            # response = xbmc.executeJSONRPC(c_str)
            # log_debug('JSON      ''{0}'''.format(c_str))
            # log_debug('Response  ''{0}'''.format(response))
            # self.kodi_joystick_suspended = True

            # log_error('_run_before_execution() Suspending Kodi joystick engine not supported on Kodi Krypton!')
        # else:
            # log_verb('_run_before_execution() DO NOT suspend Kodi joystick engine')

        # --- Toggle Kodi windowed/fullscreen if requested ---
        if toggle_screen_flag:
            log_verb('_run_before_execution() Toggling Kodi fullscreen')
            kodi_toogle_fullscreen()
        else:
            log_verb('_run_before_execution() Toggling Kodi fullscreen DEACTIVATED in Launcher')

        # --- Pause Kodi execution some time ---
        delay_tempo_ms = self.settings['delay_tempo']
        log_verb('_run_before_execution() Pausing {0} ms'.format(delay_tempo_ms))
        xbmc.sleep(delay_tempo_ms)
        log_debug('_run_before_execution() function ENDS')

    def postExecution(self, toggle_screen_flag):
        # --- Stop Kodi some time ---
        delay_tempo_ms = self.settings['delay_tempo']
        log_verb('postExecution() Pausing {0} ms'.format(delay_tempo_ms))
        xbmc.sleep(delay_tempo_ms)

        # --- Toggle Kodi windowed/fullscreen if requested ---
        if toggle_screen_flag:
            log_verb('postExecution() Toggling Kodi fullscreen')
            kodi_toogle_fullscreen()
        else:
            log_verb('postExecution() Toggling Kodi fullscreen DEACTIVATED in Launcher')

        # --- Resume audio engine if it was suspended ---
        # Calling xmbc.audioResume() takes a loong time (2/4 secs) if audio was not properly suspended!
        # Also produces this in Kodi's log:
        # WARNING: CActiveAE::StateMachine - signal: 0 from port: OutputControlPort not handled for state: 7
        #   ERROR: ActiveAE::Resume - failed to init
        if self.kodi_audio_suspended:
            log_verb('postExecution() Kodi audio engine was suspended before launching')
            log_verb('postExecution() Resuming Kodi audio engine')
            xbmc.audioResume()
            xbmc.enableNavSounds(True)
            xbmc.sleep(100)
        else:
            log_verb('_run_before_execution() DO NOT resume Kodi audio engine')

        # --- Resume joystick engine if it was suspended ---
        if self.kodi_joystick_suspended:
            log_verb('postExecution() Kodi joystick engine was suspended before launching')
            log_verb('postExecution() Resuming Kodi joystick engine')
            # response = xbmc.executeJSONRPC(c_str)
            # log_debug('JSON      ''{0}'''.format(c_str))
            # log_debug('Response  ''{0}'''.format(response))
            log_verb('postExecution() Not supported on Kodi Krypton!')
        else:
            log_verb('postExecution() DO NOT resume Kodi joystick engine')

        # --- Resume Kodi playing if it was paused. If it was stopped, keep it stopped. ---
        media_state_action = self.settings['media_state_action']
        media_state_str = ['Stop', 'Pause', 'Let Play'][media_state_action]
        log_verb('postExecution() media_state_action is "{0}" ({1})'.format(media_state_str, media_state_action))
        log_verb('postExecution() self.kodi_was_playing is {0}'.format(self.kodi_was_playing))
        if self.kodi_was_playing and media_state_action == 1:
            log_verb('postExecution() Calling xbmc.Player().play()')
            xbmc.Player().play()
        log_debug('postExecution() function ENDS')

    @abc.abstractmethod
    def supports_launching_roms(self):
        return False

    @abc.abstractmethod
    def get_launcher_type(self):
        return LAUNCHER_STANDALONE

    @abc.abstractmethod
    def get_launcher_type_name(self):
        return "Standalone launcher"

    def change_name(self, new_name):
        if new_name == '': 
            return False

        old_launcher_name = self.get_name()
        new_launcher_name = new_name.rstrip()

        log_debug('launcher.change_name() Changing name: old_launcher_name "{0}"'.format(old_launcher_name))
        log_debug('launcher.change_name() Changing name: new_launcher_name "{0}"'.format(new_launcher_name))

        if old_launcher_name == new_launcher_name:
            return False

        self.entity_data['m_name'] = new_launcher_name
        return True

    def get_platform(self):
        return self.entity_data['platform'] if 'platform' in self.entity_data else ''

    def get_category_id(self):
        return self.entity_data['categoryID'] if 'categoryID' in self.entity_data else None
    
    def is_in_windowed_mode(self):
        return self.entity_data['toggle_window']

    def set_windowed_mode(self, windowed_mode):
        self.entity_data['toggle_window'] = windowed_mode
        return self.is_in_windowed_mode()

    def is_non_blocking(self):
        return 'non_blocking' in self.entity_data and self.entity_data['non_blocking']

    def set_non_blocking(self, is_non_blocking):
        self.entity_data['non_blocking'] = is_non_blocking
        return self.is_non_blocking()

    # Change the application this launcher uses
    # Override if changeable.
    def change_application(self):
        return False

    def get_assets(self):
        assets = {}
        asset_keys = [ASSET_BANNER, ASSET_ICON, ASSET_FANART, ASSET_POSTER, ASSET_CLEARLOGO, ASSET_CONTROLLER, ASSET_TRAILER]

        asset_factory = AssetInfoFactory.create()
        asset_kinds = asset_factory.get_assets_by(asset_keys)
        
        for asset_kind in asset_kinds:
            asset = self.entity_data[asset_kind.key] if self.entity_data[asset_kind.key] else ''            
            assets[asset_kind] = asset

        return assets

    def get_asset_defaults(self):
        default_assets = {}
        default_asset_keys = [ASSET_BANNER, ASSET_ICON, ASSET_FANART, ASSET_POSTER, ASSET_CLEARLOGO]
        asset_factory = AssetInfoFactory.create()
        default_asset_kinds = asset_factory.get_assets_by(default_asset_keys)

        for asset_kind in default_asset_kinds:
            mapped_asset_key = self.entity_data[asset_kind.default_key] if self.entity_data[asset_kind.default_key] else ''
            mapped_asset_kind = asset_factory.get_asset_info_by_namekey(mapped_asset_key)
            
            default_assets[asset_kind] = mapped_asset_kind

        return default_assets

    def set_default_asset(self, asset_kind, mapped_to_kind):
        self.entity_data[asset_kind.default_key] = mapped_to_kind.key

    #
    # Returns a dictionary of options to choose from
    # with which you can edit or manage this specific launcher.
    #
    @abc.abstractmethod
    def get_edit_options(self):
        return {}

    #
    # Returns a dictionary of options to choose from
    # with which you can do advanced modifications on this specific launcher.
    #
    @abc.abstractmethod
    def get_advanced_modification_options(self):
        options = collections.OrderedDict()
        return options

    #
    # Returns a dictionary of options to choose from
    # with which you can edit the metadata of this specific launcher.
    #
    def get_metadata_edit_options(self):
        # >> Metadata edit dialog
        NFO_FileName = fs_get_launcher_NFO_name(self.settings, self.entity_data)
        NFO_found_str = 'NFO found' if NFO_FileName.exists() else 'NFO not found'
        plot_str = text_limit_string(self.entity_data['m_plot'], PLOT_STR_MAXSIZE)

        rating = self.get_rating()
        if rating == -1:
            rating = 'not rated'

        options = collections.OrderedDict()
        options['EDIT_TITLE']             = "Edit Title: '{0}'".format(self.get_name())
        options['EDIT_PLATFORM']          = "Edit Platform: {0}".format(self.entity_data['platform'])
        options['EDIT_RELEASEYEAR']       = "Edit Release Year: '{0}'".format(self.entity_data['m_year'])
        options['EDIT_GENRE']             = "Edit Genre: '{0}'".format(self.entity_data['m_genre'])
        options['EDIT_DEVELOPER']         = "Edit Developer: '{0}'".format(self.entity_data['m_developer'])
        options['EDIT_RATING']            = "Edit Rating: '{0}'".format(rating)
        options['EDIT_PLOT']              = "Edit Plot: '{0}'".format(plot_str)
        options['IMPORT_NFO_FILE']        = 'Import NFO file (default, {0})'.format(NFO_found_str)
        options['IMPORT_NFO_FILE_BROWSE'] = 'Import NFO file (browse NFO file) ...'
        options['SAVE_NFO_FILE']          = 'Save NFO file (default location)'

        return options

    def get_timestamp(self):
        timestamp = self.entity_data['timestamp_launcher']
        if timestamp is None or timestamp == '':
            return float(0)

        return float(timestamp)
   
    def get_report_timestamp(self):
        timestamp = self.entity_data['timestamp_report']
        if timestamp is None or timestamp == '':
            return float(0)

        return float(timestamp)

    def update_timestamp(self):
        self.entity_data['timestamp_launcher'] = time.time()

    def update_report_timestamp(self):
        self.entity_data['timestamp_report'] = time.time()

    def update_category(self, category_id):
        self.entity_data['categoryID'] = category_id

    def update_platform(self, platform):
        self.entity_data['platform'] = platform

    #
    # Python data model: lists and dictionaries are mutable. It means the can be changed if passed as
    # parameters of functions. However, items can not be replaced by new objects!
    # Notably, numbers, strings and tuples are immutable. Dictionaries and lists are mutable.
    #
    # See http://stackoverflow.com/questions/986006/how-do-i-pass-a-variable-by-reference
    # See https://docs.python.org/2/reference/datamodel.html
    #
    # Function asumes that the NFO file already exists.
    #
    def import_nfo_file(self, nfo_file_path):
        # --- Get NFO file name ---
        log_debug('launcher.import_nfo_file() Importing launcher NFO "{0}"'.format(nfo_file_path.getOriginalPath()))

        # --- Import data ---
        if nfo_file_path.exists():
            # >> Read NFO file data
            try:
                item_nfo = nfo_file_path.readAllUnicode()
                item_nfo = item_nfo.replace('\r', '').replace('\n', '')
            except:
                kodi_notify_warn('Exception reading NFO file {0}'.format(nfo_file_path.getOriginalPath()))
                log_error("launcher.import_nfo_file() Exception reading NFO file '{0}'".format(nfo_file_path.getOriginalPath()))
                return False
            # log_debug("fs_import_launcher_NFO() item_nfo '{0}'".format(item_nfo))
        else:
            kodi_notify_warn('NFO file not found {0}'.format(nfo_file_path.getBase()))
            log_info("launcher.import_nfo_file() NFO file not found '{0}'".format(nfo_file_path.getOriginalPath()))
            return False

        # Find data
        item_year      = re.findall('<year>(.*?)</year>',           item_nfo)
        item_genre     = re.findall('<genre>(.*?)</genre>',         item_nfo)
        item_developer = re.findall('<developer>(.*?)</developer>', item_nfo)
        item_rating    = re.findall('<rating>(.*?)</rating>',       item_nfo)
        item_plot      = re.findall('<plot>(.*?)</plot>',           item_nfo)

        # >> Careful about object mutability! This should modify the dictionary
        # >> passed as argument outside this function.
        if item_year:      self.update_releaseyear(text_unescape_XML(item_year[0]))
        if item_genre:     self.update_genre(text_unescape_XML(item_genre[0]))
        if item_developer: self.update_developer(text_unescape_XML(item_developer[0]))
        if item_rating:    self.update_rating(text_unescape_XML(item_rating[0]))
        if item_plot:      self.update_plot(text_unescape_XML(item_plot[0]))

        log_verb("import_nfo_file() Imported '{0}'".format(nfo_file_path.getOriginalPath()))

        return True

    #
    # Standalone launchers:
    #   NFO files are stored in self.settings["launchers_nfo_dir"] if not empty.
    #   If empty, it defaults to DEFAULT_LAUN_NFO_DIR.
    #
    # ROM launchers:
    #   Same as standalone launchers.
    #
    def export_nfo_file(self, nfo_FileName):
        # --- Get NFO file name ---
        log_debug('export_nfo_file() Exporting launcher NFO "{0}"'.format(nfo_FileName.getOriginalPath()))

        # If NFO file does not exist then create them. If it exists, overwrite.
        nfo_content = []
        nfo_content.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        nfo_content.append('<!-- Exported by AEL on {0} -->\n'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
        nfo_content.append('<launcher>\n')
        nfo_content.append(XML_text('year',      self.get_releaseyear()))
        nfo_content.append(XML_text('genre',     self.get_genre()))
        nfo_content.append(XML_text('developer', self.get_developer()))
        nfo_content.append(XML_text('rating',    self.get_rating()))
        nfo_content.append(XML_text('plot',      self.get_plot()))
        nfo_content.append('</launcher>\n')
        full_string = ''.join(nfo_content).encode('utf-8')
        try:
            nfo_FileName.writeAll(full_string)
        except:
            kodi_notify_warn('Exception writing NFO file {0}'.format(nfo_FileName.getPath()))
            log_error("export_nfo_file() Exception writing'{0}'".format(nfo_FileName.getOriginalPath()))
            return False
        log_debug("export_nfo_file() Created '{0}'".format(nfo_FileName.getOriginalPath()))

        return True

    def export_configuration(self, path_to_export, category):
        launcher_fn_str = 'Launcher_' + text_title_to_filename_str(self.get_name()) + '.xml'
        log_debug('launcher.export_configuration() Exporting Launcher configuration')
        log_debug('launcher.export_configuration() Name     "{0}"'.format(self.get_name()))
        log_debug('launcher.export_configuration() ID       {0}'.format(self.get_id()))
        log_debug('launcher.export_configuration() l_fn_str "{0}"'.format(launcher_fn_str))

        if not path_to_export: return

        export_FN = FileNameFactory.create(path_to_export).pjoin(launcher_fn_str)
        if export_FN.exists():
            confirm = kodi_dialog_yesno('Overwrite file {0}?'.format(export_FN.getPath()))
            if not confirm:
                kodi_notify_warn('Export of Launcher XML cancelled')
        
        category_data = category.get_data() if category is not None else {}
        # --- Print error message is something goes wrong writing file ---
        try:
            autoconfig_export_launcher(self.entity_data, export_FN, category_data)
        except AEL_Error as E:
            kodi_notify_warn('{0}'.format(E))
        else:
            kodi_notify('Exported Launcher "{0}" XML config'.format(self.get_name()))
        # >> No need to update categories.xml and timestamps so return now.

    #
    # Creates a new launcher using a wizard of dialogs.
    #
    @abc.abstractmethod
    def _get_builder_wizard(self, wizard):
        return wizard

    def _get_title_from_app_path(self, input, item_key, launcher):

        if input:
            return input

        app = launcher['application']
        appPath = FileNameFactory.create(app)

        title = appPath.getBase_noext()
        title_formatted = title.replace('.' + title.split('.')[-1], '').replace('.', ' ')

        return title_formatted

    def _get_appbrowser_filter(self, item_key, launcher):
        if item_key in launcher:
            application = launcher[item_key]
            if application == 'JAVA':
                return '.jar'

        return '.bat|.exe|.cmd|.lnk' if is_windows() else ''

    #
    # Wizard helper, when a user wants to set a custom value
    # instead of the predefined list items.
    #
    def _user_selected_custom_browsing(self, item_key, launcher):
        return launcher[item_key] == 'BROWSE'
     
# -------------------------------------------------------------------------------------------------
# Abstract base class for launching anything roms or item based.
# This base class has methods to support launching applications with variable input
# arguments or items like roms.
# Inherit from this base class to implement your own specific rom launcher.
# -------------------------------------------------------------------------------------------------
class RomLauncher(Launcher):
    __metaclass__ = abc.ABCMeta

    def __init__(self, launcher_data, settings, executorFactory, romset_repository, statsStrategy, escape_romfile):
        self.roms = {}
        self.romset_repository = romset_repository

        self.escape_romfile = escape_romfile
        self.statsStrategy = statsStrategy

        super(RomLauncher, self).__init__(launcher_data, settings, executorFactory)

    @abc.abstractmethod
    def _selectApplicationToUse(self):
        return True

    @abc.abstractmethod
    def _selectArgumentsToUse(self):
        return True

    @abc.abstractmethod
    def _selectRomFileToUse(self):
        return True

    # ~~~~ Argument substitution ~~~~~
    def _parseArguments(self):
        log_info('RomLauncher() raw arguments   "{0}"'.format(self.arguments))

        # Application based arguments replacements
        if self.application and isinstance(self.application, FileName):
            apppath = self.application.getDir()

            log_info('RomLauncher() application  "{0}"'.format(self.application.getPath()))
            log_info('RomLauncher() appbase      "{0}"'.format(self.application.getBase()))
            log_info('RomLauncher() apppath      "{0}"'.format(apppath))

            self.arguments = self.arguments.replace('$apppath$', apppath)
            self.arguments = self.arguments.replace('$appbase$', self.application.getBase())

        # ROM based arguments replacements
        if self.selected_rom_file:
            # --- Escape quotes and double quotes in ROMFileName ---
            # >> This maybe useful to Android users with complex command line arguments
            if self.escape_romfile:
                log_info("RomLauncher() Escaping ROMFileName ' and \"")
                self.selected_rom_file.escapeQuotes()

            rompath       = self.selected_rom_file.getDir()
            rombase       = self.selected_rom_file.getBase()
            rombase_noext = self.selected_rom_file.getBase_noext()

            log_info('RomLauncher() romfile      "{0}"'.format(self.selected_rom_file.getPath()))
            log_info('RomLauncher() rompath      "{0}"'.format(rompath))
            log_info('RomLauncher() rombase      "{0}"'.format(rombase))
            log_info('RomLauncher() rombasenoext "{0}"'.format(rombase_noext))

            self.arguments = self.arguments.replace('$rom$', self.selected_rom_file.getPath())
            self.arguments = self.arguments.replace('$romfile$', self.selected_rom_file.getPath())
            self.arguments = self.arguments.replace('$rompath$', rompath)
            self.arguments = self.arguments.replace('$rombase$', rombase)
            self.arguments = self.arguments.replace('$rombasenoext$', rombase_noext)

            # >> Legacy names for argument substitution
            self.arguments = self.arguments.replace('%rom%', self.selected_rom_file.getPath())
            self.arguments = self.arguments.replace('%ROM%', self.selected_rom_file.getPath())

        category_id = self.get_category_id()
        if category_id is None:
            category_id = ''

        # Default arguments replacements
        self.arguments = self.arguments.replace('$categoryID$', category_id)
        self.arguments = self.arguments.replace('$launcherID$', self.entity_data['id'])
        self.arguments = self.arguments.replace('$romID$', self.rom.get_id())
        self.arguments = self.arguments.replace('$romtitle$', self.title)

        # automatic substitution of rom values
        for rom_key, rom_value in self.rom.get_data().iteritems():
            if isinstance(rom_value, basestring):
                self.arguments = self.arguments.replace('${}$'.format(rom_key), rom_value)        

        # automatic substitution of launcher values
        for launcher_key, launcher_value in self.entity_data.iteritems():
            if isinstance(launcher_value, basestring):
                self.arguments = self.arguments.replace('${}$'.format(launcher_key), launcher_value)

        log_info('RomLauncher() final arguments "{0}"'.format(self.arguments))

    def launch(self):
        self.title  = self.rom.get_name()
        self.selected_rom_file = None

        applicationIsSet    = self._selectApplicationToUse()
        argumentsAreSet     = self._selectArgumentsToUse()
        romIsSelected       = self._selectRomFileToUse()

        if not applicationIsSet or not argumentsAreSet or not romIsSelected:
            return

        self._parseArguments()

        if self.statsStrategy is not None:
            self.statsStrategy.update_launched_rom_stats(self.rom)       
            self.save_rom(self.rom)

        super(RomLauncher, self).launch()
        pass

    def supports_launching_roms(self):
        return True  

    def supports_parent_clone_roms(self):
        return False

    def load_roms(self):
        self.roms = self.romset_repository.find_by_launcher(self)

    def select_rom(self, rom_id):
        if not self.has_roms():
            self.load_roms()

        if self.roms is None:
            log_error('Unable to load romset')
            return None

        if not rom_id in self.roms:
            log_error('RomID {0} not found in romset'.format(rom_id))
            return None

        self.rom = self.roms[rom_id]
        return self.rom

    def has_roms(self):
        return self.roms is not None and len(self.roms) > 0

    def has_rom(self, rom_id):
        if not self.has_roms():
            self.load_roms()

        return rom_id in self.roms

    def get_number_of_roms(self):
        return self.entity_data['num_roms']

    def actual_amount_of_roms(self):
        if not self.has_roms():
            self.load_roms()
        num_roms = len(self.roms) if self.roms else 0
        return num_roms

    def get_roms(self):
        if not self.has_roms():
            self.load_roms()

        return self.roms.values() if self.roms else None
    
    def get_rom_ids(self):
        if not self.has_roms():
            self.load_roms()

        return self.roms.keys() if self.roms else None

    def update_rom_set(self, roms):
        if not isinstance(roms,dict):
            roms = dict((rom.get_id(), rom) for rom in roms)

        self.romset_repository.save_rom_set(self, roms)
        self.roms = roms

    def save_current_roms(self):
        self.romset_repository.save_rom_set(self, self.roms)

    def save_rom(self, rom):
        if not self.has_roms():
            self.load_roms()

        self.roms[rom.get_id()] = rom
        self.romset_repository.save_rom_set(self, self.roms)

    def delete_rom_set(self):
        self.romset_repository.delete_all_by_launcher(self)

    def reset_parent_and_clone_roms(self):
        self.romset_repository.delete_by_launcher(self, ROMSET_CPARENT)
        self.romset_repository.delete_by_launcher(self, ROMSET_PCLONE)
        self.romset_repository.delete_by_launcher(self, ROMSET_PARENTS)

    def remove_rom(self, rom_id):
        if not self.has_roms():
            self.load_roms()

        self.roms.pop(rom_id)
        self.romset_repository.save_rom_set(self, self.roms)

    # -------------------------------------------------------------------------------------------------
    # Favourite ROM creation/management
    # -------------------------------------------------------------------------------------------------
    #
    # Creates a new Favourite ROM dictionary from parent ROM and Launcher.
    #
    # No-Intro Missing ROMs are not allowed in Favourites or Virtual Launchers.
    # fav_status = ['OK', 'Unlinked ROM', 'Unlinked Launcher', 'Broken'] default 'OK'
    #  'OK'                ROM filename exists and launcher exists and ROM id exists
    #  'Unlinked ROM'      ROM filename exists but ROM ID in launcher does not
    #  'Unlinked Launcher' ROM filename exists but Launcher ID not found
    #                      Note that if the launcher does not exists implies ROM ID does not exist.
    #                      If launcher doesn't exist ROM JSON cannot be loaded.
    #  'Broken'            ROM filename does not exist. ROM is unplayable
    #
    def convert_rom_to_favourite(self, rom_id):
        rom = self.select_rom(rom_id)
        # >> Copy original rom     
        # todo: Should we make a FavouriteRom class inheriting Rom?
        favourite = rom.copy()

        # Delete nointro_status field from ROM. Make sure this is done in the copy to be
        # returned to avoid chaning the function parameters (dictionaries are mutable!)
        # See http://stackoverflow.com/questions/5844672/delete-an-element-from-a-dictionary
        # NOTE keep it!
        # del favourite['nointro_status']

        # >> Copy parent launcher fields into Favourite ROM
        favourite.set_custom_attribute('launcherID',            self.get_id())
        favourite.set_custom_attribute('platform',              self.get_platform())
        favourite.set_custom_attribute('application',           self.get_custom_attribute('application'))
        favourite.set_custom_attribute('args',                  self.get_custom_attribute('args'))
        favourite.set_custom_attribute('args_extra',            self.get_custom_attribute('args_extra'))
        favourite.set_custom_attribute('rompath',               self.get_rom_path().getOriginalPath())
        favourite.set_custom_attribute('romext',                self.get_custom_attribute('romext'))
        favourite.set_custom_attribute('toggle_window',         self.is_in_windowed_mode())
        favourite.set_custom_attribute('non_blocking',          self.is_non_blocking())
        favourite.set_custom_attribute('roms_default_icon',     self.get_custom_attribute('roms_default_icon'))
        favourite.set_custom_attribute('roms_default_fanart',   self.get_custom_attribute('roms_default_fanart'))
        favourite.set_custom_attribute('roms_default_banner',   self.get_custom_attribute('roms_default_banner'))
        favourite.set_custom_attribute('roms_default_poster',   self.get_custom_attribute('roms_default_poster'))
        favourite.set_custom_attribute('roms_default_clearlogo',self.get_custom_attribute('roms_default_clearlogo'))

        # >> Favourite ROM unique fields
        # >> Favourite ROMs in "Most played ROMs" DB also have 'launch_count' field.
        favourite.set_favourite_status('OK')

        return favourite

    def get_edit_options(self):
        finished_str = 'Finished' if self.entity_data['finished'] == True else 'Unfinished'   

        options = collections.OrderedDict()
        options['EDIT_METADATA']        = 'Edit Metadata ...'
        options['EDIT_ASSETS']          = 'Edit Assets/Artwork ...'
        options['SET_DEFAULT_ASSETS']   = 'Choose default Assets/Artwork ...'
        options['CHANGE_CATEGORY']      = 'Change Category'
        options['LAUNCHER_STATUS']      = 'Launcher status: {}'.format(finished_str)
        options['MANAGE_ROMS']          = 'Manage ROMs ...'
        options['AUDIT_ROMS']           = 'Audit ROMs / Launcher view mode ...'
        options['ADVANCED_MODS']        = 'Advanced Modifications ...'
        options['EXPORT_LAUNCHER']      = 'Export Launcher XML configuration ...'
        options['DELETE_LAUNCHER']      = 'Delete Launcher'

        return options

    # Returns the dialog options to choose from when managing the roms.
    def get_manage_roms_options(self):
        options = collections.OrderedDict()
        options['SET_ROMS_DEFAULT_ARTWORK'] = 'Choose ROMs default artwork ...'
        options['SET_ROMS_ASSET_DIRS']      = 'Manage ROMs asset directories ...'
        options['SCAN_LOCAL_ARTWORK']       = 'Scan ROMs local artwork'
        options['SCRAPE_LOCAL_ARTWORK']     = 'Scrape ROMs local artwork'
        options['REMOVE_DEAD_ROMS']         = 'Remove dead/missing ROMs'
        options['IMPORT_ROMS']              = 'Import ROMs metadata from NFO files'
        options['EXPORT_ROMS']              = 'Export ROMs metadata to NFO files'
        options['DELETE_ROMS_NFO']          = 'Delete ROMs NFO files'
        options['CLEAR_ROMS']               = 'Clear ROMs from launcher'

        return options

    def get_audit_roms_options(self):
        display_mode_str        = self.entity_data['launcher_display_mode']
        no_intro_display_mode  = self.entity_data['nointro_display_mode']

        options = collections.OrderedDict()
        options['CHANGE_DISPLAY_MODE']      = 'Change launcher display mode (now {0}) ...'.format(display_mode_str)

        if self.has_nointro_xml():
            nointro_xml_file = self.entity_data['nointro_xml_file']
            options['DELETE_NO_INTRO']      = 'Delete No-Intro/Redump DAT: {0}'.format(nointro_xml_file)
        else:
            options['ADD_NO_INTRO']         = 'Add No-Intro/Redump XML DAT ...'
        
        options['CREATE_PARENTCLONE_DAT']   = 'Create Parent/Clone DAT based on ROM filenames'
        options['CHANGE_DISPLAY_ROMS']      = 'Display ROMs (now {0}) ...'.format(no_intro_display_mode)
        options['UPDATE_ROM_AUDIT']         = 'Update ROM audit'

        return options

    def get_rom_assets(self):
        assets = {}

        assets[ASSET_BANNER]     = self.entity_data['s_banner']      if self.entity_data['s_banner']     else ''
        assets[ASSET_ICON]       = self.entity_data['s_icon']        if self.entity_data['s_icon']       else ''
        assets[ASSET_FANART]     = self.entity_data['s_fanart']      if self.entity_data['s_fanart']     else ''
        assets[ASSET_POSTER]     = self.entity_data['s_poster']      if self.entity_data['s_poster']     else ''
        assets[ASSET_CLEARLOGO]  = self.entity_data['s_clearlogo']   if self.entity_data['s_clearlogo']  else ''
        assets[ASSET_CONTROLLER] = self.entity_data['s_controller']  if self.entity_data['s_controller'] else ''
        assets[ASSET_TRAILER]    = self.entity_data['s_trailer']     if self.entity_data['s_trailer']    else ''

        return assets

    def get_rom_asset_default(self, asset_info):
        return self.entity_data[asset_info.rom_default_key] if asset_info.rom_default_key in self.entity_data else None

    def get_rom_asset_defaults(self):
        default_assets = {}
        default_assets[ASSET_BANNER]     = ASSET_KEYS_TO_CONSTANTS[self.entity_data['roms_default_banner']]    if self.entity_data['roms_default_banner']     else ''
        default_assets[ASSET_ICON]       = ASSET_KEYS_TO_CONSTANTS[self.entity_data['roms_default_icon']]      if self.entity_data['roms_default_icon']       else ''
        default_assets[ASSET_FANART]     = ASSET_KEYS_TO_CONSTANTS[self.entity_data['roms_default_fanart']]    if self.entity_data['roms_default_fanart']     else ''
        default_assets[ASSET_POSTER]     = ASSET_KEYS_TO_CONSTANTS[self.entity_data['roms_default_poster']]    if self.entity_data['roms_default_poster']     else ''
        default_assets[ASSET_CLEARLOGO]  = ASSET_KEYS_TO_CONSTANTS[self.entity_data['roms_default_clearlogo']] if self.entity_data['roms_default_clearlogo']  else ''
        
        return default_assets

    def get_duplicated_asset_dirs(self):
        duplicated_bool_list   = [False] * len(ROM_ASSET_LIST)
        duplicated_name_list   = []

        # >> Check for duplicated asset paths
        for i, asset_i in enumerate(ROM_ASSET_LIST[:-1]):
            A_i = assets_get_info_scheme(asset_i)
            for j, asset_j in enumerate(ROM_ASSET_LIST[i+1:]):
                A_j = assets_get_info_scheme(asset_j)
                # >> Exclude unconfigured assets (empty strings).
                if not self.entity_data[A_i.path_key] or not self.entity_data[A_j.path_key]: continue
                # log_debug('asset_get_duplicated_asset_list() Checking {0:<9} vs {1:<9}'.format(A_i.name, A_j.name))
                if self.entity_data[A_i.path_key] == self.entity_data[A_j.path_key]:
                    duplicated_bool_list[i] = True
                    duplicated_name_list.append('{0} and {1}'.format(A_i.name, A_j.name))
                    log_info('asset_get_duplicated_asset_list() DUPLICATED {0} and {1}'.format(A_i.name, A_j.name))

        return duplicated_name_list

    def set_default_rom_asset(self, asset_kind, mapped_to_kind):
        self.entity_data[asset_kind.rom_default_key] = mapped_to_kind.key

    def get_asset_path(self, asset_info):
        if not asset_info:
            return None

        return self._get_value_as_filename(asset_info.path_key)

    def set_asset_path(self, asset_info, path):
        log_debug('Setting "{}" to {}'.format(asset_info.path_key, path))
        self.entity_data[asset_info.path_key] = path

    def get_rom_path(self):
        return self._get_value_as_filename('rompath')

    def change_rom_path(self, path):
        self.entity_data['rompath'] = path

    def get_rom_asset_path(self):
        return self._get_value_as_filename('ROM_asset_path')

    def get_roms_base(self):
        return self.entity_data['roms_base_noext'] if 'roms_base_noext' in self.entity_data else None

    def update_roms_base(self, roms_base_noext):
        self.entity_data['roms_base_noext'] = roms_base_noext

    def get_roms_xml_file(self):
        return self.entity_data['roms_xml_file']
    
    def set_roms_xml_file(self, xml_file):
        self.entity_data['roms_xml_file'] = xml_file

    def clear_roms(self):
        self.entity_data['num_roms'] = 0
        self.roms = {}
        self.romset_repository.delete_all_by_launcher(self)

    def get_display_mode(self):
        return self.entity_data['launcher_display_mode'] if 'launcher_display_mode' in self.entity_data else LAUNCHER_DMODE_FLAT

    def change_display_mode(self, mode):
        if mode == LAUNCHER_DMODE_PCLONE or mode == LAUNCHER_DMODE_1G1R:
            # >> Check if user configured a No-Intro DAT. If not configured  or file does
            # >> not exists refuse to switch to PClone view and force normal mode.
            if not self.has_nointro_xml():
                log_info('RomsLauncher.change_display_mode() No-Intro DAT not configured.')
                log_info('RomsLauncher.change_display_mode() Forcing Flat view mode.')
                mode = LAUNCHER_DMODE_FLAT
            else:
                nointro_xml_file_FName = self.get_nointro_xml_filepath()
                if not nointro_xml_file_FName.exists():
                    log_info('RomsLauncher.change_display_mode() No-Intro DAT not found.')
                    log_info('RomsLauncher.change_display_mode() Forcing Flat view mode.')
                    kodi_dialog_OK('No-Intro DAT cannot be found. PClone or 1G1R view mode cannot be set.')
                    mode = LAUNCHER_DMODE_FLAT

        self.entity_data['launcher_display_mode'] = mode
        log_debug('launcher_display_mode = {0}'.format(mode))
        return mode

    def get_nointro_display_mode(self):
        return self.entity_data['nointro_display_mode'] if 'nointro_display_mode' in self.entity_data else LAUNCHER_DMODE_FLAT

    def change_nointro_display_mode(self, mode):
        self.entity_data['nointro_display_mode'] = mode
        log_info('Launcher nointro display mode changed to "{0}"'.format(self.entity_data['nointro_display_mode']))
        return mode

    def has_nointro_xml(self):
        return self.entity_data['nointro_xml_file']

    def get_nointro_xml_filepath(self):
        return self._get_value_as_filename('nointro_xml_file')

    def set_nointro_xml_file(self, path):
        self.entity_data['nointro_xml_file'] = path

    def reset_nointro_xmldata(self):
        if self.entity_data['nointro_xml_file']:
            log_info('Deleting XML DAT file and forcing launcher to Normal view mode.')
            self.entity_data['nointro_xml_file'] = ''

    def set_audit_stats(self, num_of_roms, num_audit_parents, num_audit_clones, num_audit_have, num_audit_miss, num_audit_unknown):
        self.set_number_of_roms(get_number_of_roms)
        self.entity_data['num_parents'] = num_audit_parents
        self.entity_data['num_clones']  = num_audit_clones
        self.entity_data['num_have']    = num_audit_have
        self.entity_data['num_miss']    = num_audit_miss
        self.entity_data['num_unknown'] = num_audit_unknown

    def set_number_of_roms(self, num_of_roms = -1):
        if num_of_roms == -1:
            num_of_roms = self.actual_amount_of_roms()

        self.entity_data['num_roms'] = num_of_roms

    def supports_multidisc(self):
        return self.entity_data['multidisc']

    def set_multidisc_support(self, supports_multidisc):
        self.entity_data['multidisc'] = supports_multidisc
        return self.supports_multidisc()

    def _get_extensions_from_app_path(self, input, item_key ,launcher):
        if input:
            return input

        app = launcher['application']
        appPath = FileNameFactory.create(app)

        extensions = emudata_get_program_extensions(appPath.getBase())
        return extensions

    def _get_arguments_from_application_path(self, input, item_key, launcher):
        if input:
            return input

        app = launcher['application']
        appPath = FileNameFactory.create(app)

        default_arguments = emudata_get_program_arguments(appPath.getBase())
        return default_arguments

    def _get_value_from_rompath(self, input, item_key, launcher):
        if input:
            return input

        romPath = launcher['rompath']
        return romPath

    def _get_value_from_assetpath(self, input, item_key, launcher):
        if input:
            return input

        romPath = FileNameFactory.create(launcher['assets_path'])
        romPath = romPath.pjoin('games')

        return romPath.getOriginalPath()

# -------------------------------------------------------------------------------------------------
# Standalone application launcher
# -------------------------------------------------------------------------------------------------
class ApplicationLauncher(Launcher):
    def launch(self):
        self.title              = self.entity_data['m_name']
        self.application        = FileNameFactory.create(self.entity_data['application'])
        self.arguments          = self.entity_data['args']       

        # --- Check for errors and abort if errors found ---
        if not self.application.exists():
            log_error('Launching app not found "{0}"'.format(self.application.getPath()))
            kodi_notify_warn('App {0} not found.'.format(self.application.getOriginalPath()))
            return
        
        # ~~~ Argument substitution ~~~
        log_info('ApplicationLauncher() raw arguments   "{0}"'.format(self.arguments))
        self.arguments = self.arguments.replace('$apppath%' , self.application.getDir())
        log_info('ApplicationLauncher() final arguments "{0}"'.format(self.arguments))

        super(ApplicationLauncher, self).launch()
        pass

    def supports_launching_roms(self):
        return False
    
    def get_launcher_type(self):
        return LAUNCHER_STANDALONE
    
    def get_launcher_type_name(self):        
        return "Standalone launcher"
         
    def change_application(self):

        current_application = self.entity_data['application']
        selected_application = xbmcgui.Dialog().browse(1, 'Select the launcher application', 'files',
                                                      self._get_appbrowser_filter('application', self.entity_data), 
                                                      False, False, current_application).decode('utf-8')

        if selected_application is None or selected_application == current_application:
            return False

        self.entity_data['application'] = selected_application
        return True

    def change_arguments(self, args):
        self.entity_data['args'] = args
        
    def get_args(self):
        return self.entity_data['args']
    
    def get_additional_argument(self, index):
        args = self.get_all_additional_arguments()
        return args[index]

    def get_all_additional_arguments(self):
        return self.entity_data['args_extra']

    def add_additional_argument(self, arg):

        if not self.entity_data['args_extra']:
            self.entity_data['args_extra'] = []

        self.entity_data['args_extra'].append(arg)
        log_debug('launcher.add_additional_argument() Appending extra_args to launcher {0}'.format(self.get_id()))
        
    def set_additional_argument(self, index, arg):
        if not self.entity_data['args_extra']:
            self.entity_data['args_extra'] = []

        self.entity_data['args_extra'][index] = arg
        log_debug('launcher.set_additional_argument() Edited args_extra[{0}] to "{1}"'.format(index, self.entity_data['args_extra'][index]))

    def remove_additional_argument(self, index):
        del self.entity_data['args_extra'][index]
        log_debug("launcher.remove_additional_argument() Deleted launcher['args_extra'][{0}]".format(index))
        
    def get_edit_options(self):

        options = collections.OrderedDict()
        options['EDIT_METADATA']      = 'Edit Metadata ...'
        options['EDIT_ASSETS']        = 'Edit Assets/Artwork ...'
        options['SET_DEFAULT_ASSETS'] = 'Choose default Assets/Artwork ...'
        options['CHANGE_CATEGORY']    = 'Change Category'
        options['LAUNCHER_STATUS']    = 'Launcher status: {0}'.format(self.get_state())
        options['ADVANCED_MODS']      = 'Advanced Modifications ...'
        options['EXPORT_LAUNCHER']    = 'Export Launcher XML configuration ...'
        options['DELETE_LAUNCHER']    = 'Delete Launcher'

        return options

    def get_advanced_modification_options(self):
        
        toggle_window_str = 'ON' if self.entity_data['toggle_window'] else 'OFF'
        non_blocking_str  = 'ON' if self.entity_data['non_blocking'] else 'OFF'

        options = super(ApplicationLauncher, self).get_advanced_modification_options()
        options['CHANGE_APPLICATION']   = "Change Application: '{0}'".format(self.entity_data['application'])
        options['MODIFY_ARGS']          = "Modify Arguments: '{0}'".format(self.entity_data['args'])
        options['ADDITIONAL_ARGS']      = "Modify aditional arguments ..."
        options['TOGGLE_WINDOWED']      = "Toggle Kodi into windowed mode (now {0})".format(toggle_window_str)
        options['TOGGLE_NONBLOCKING']   = "Non-blocking launcher (now {0})".format(non_blocking_str)

        return options

    #
    # Creates a new launcher using a wizard of dialogs.
    #
    def _get_builder_wizard(self, wizard):
        
        wizard = FileBrowseWizardDialog('application', 'Select the launcher application', 1, self._get_appbrowser_filter, wizard)
        wizard = DummyWizardDialog('args', '', wizard)
        wizard = KeyboardWizardDialog('args', 'Application arguments', wizard)
        wizard = DummyWizardDialog('m_name', '', wizard, self._get_title_from_app_path)
        wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, self._get_title_from_app_path)
        wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
            
        return wizard
    
# -------------------------------------------------------------------------------------------------
# Kodi favorites launcher
# -------------------------------------------------------------------------------------------------
class KodiLauncher(Launcher):
            
    def launch(self):

        self.title              = self.entity_data['m_name']
        self.application        = FileNameFactory.create('xbmc.exe')
        self.arguments          = self.entity_data['application']       
        
        super(KodiLauncher, self).launch()
        pass
    
    def supports_launching_roms(self):
        return False
    
    def get_launcher_type(self):
        return LAUNCHER_FAVOURITES
    
    def get_launcher_type_name(self):        
        return "Kodi favourite launcher"
    
    def change_application(self):

        current_application = self.entity_data['application']
        
        dialog = DictionaryDialog()
        selected_application = dialog.select('Select the favourite', self._get_kodi_favourites(), current_application)

        if selected_application is None or selected_application == current_application:
            return False

        self.entity_data['application'] = selected_application
        self.entity_data['original_favname'] = self._get_title_from_selected_favourite(selected_application, 'original_favname', self.entity_data)
        return True

    def get_edit_options(self):

        options = collections.OrderedDict()
        options['EDIT_METADATA']      = 'Edit Metadata ...'
        options['EDIT_ASSETS']        = 'Edit Assets/Artwork ...'
        options['SET_DEFAULT_ASSETS'] = 'Choose default Assets/Artwork ...'
        options['CHANGE_CATEGORY']    = 'Change Category'
        options['LAUNCHER_STATUS']    = 'Launcher status: {0}'.format(self.get_state())
        options['ADVANCED_MODS']      = 'Advanced Modifications ...'
        options['EXPORT_LAUNCHER']    = 'Export Launcher XML configuration ...'
        options['DELETE_LAUNCHER']    = 'Delete Launcher'

        return options
    
    def get_advanced_modification_options(self):
        
        toggle_window_str = 'ON' if self.entity_data['toggle_window'] else 'OFF'
        non_blocking_str  = 'ON' if self.entity_data['non_blocking'] else 'OFF'

        org_favname = self.entity_data['original_favname'] if 'original_favname' in self.entity_data else 'unknown'

        options = super(KodiLauncher, self).get_advanced_modification_options()
        options['CHANGE_APPLICATION']   = "Change favourite: '{0}'".format(org_favname)
        options['TOGGLE_WINDOWED']      = "Toggle Kodi into windowed mode (now {0})".format(toggle_window_str)
        options['TOGGLE_NONBLOCKING']   = "Non-blocking launcher (now {0})".format(non_blocking_str)

        return options
    
    #
    # Creates a new launcher using a wizard of dialogs.
    #
    def _get_builder_wizard(self, wizard):
        
        wizard = DictionarySelectionWizardDialog('application', 'Select the favourite', self._get_kodi_favourites(), wizard)
        wizard = DummyWizardDialog('s_icon', '', wizard, self._get_icon_from_selected_favourite)
        wizard = DummyWizardDialog('original_favname', '', wizard, self._get_title_from_selected_favourite)
        wizard = DummyWizardDialog('m_name', '', wizard, self._get_title_from_selected_favourite)
        wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard)
        wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
            
        return wizard
    
    def _get_kodi_favourites(self):

        favourites = kodi_read_favourites()
        fav_options = {}

        for key in favourites:
            fav_options[key] = favourites[key][0]

        return fav_options

    def _get_icon_from_selected_favourite(self, input, item_key, launcher):

        fav_action = launcher['application']
        favourites = kodi_read_favourites()

        for key in favourites:
            if fav_action == key:
                return favourites[key][1]

        return 'DefaultProgram.png'

    def _get_title_from_selected_favourite(self, input, item_key, launcher):
    
        fav_action = launcher['application']
        favourites = kodi_read_favourites()

        for key in favourites:
            if fav_action == key:
                return favourites[key][0]

        return _get_title_from_app_path(input, launcher)
   
# -------------------------------------------------------------------------------------------------
# Collection Launcher
# ------------------------------------------------------------------------------------------------- 
class CollectionLauncher(RomLauncher):
    def __init__(self, launcher_data, settings, romset_repository):
        super(CollectionLauncher, self).__init__(launcher_data, settings, None, romset_repository, None, False)

    def launch(self):
        pass

    def supports_launching_roms(self):
        return True

    def get_launcher_type(self):
        return LAUNCHER_COLLECTION

    def get_launcher_type_name(self):
        return "Collection launcher"

    def has_nointro_xml(self):
        return False

    def _selectApplicationToUse(self):
        return False

    def _selectArgumentsToUse(self):
        return False

    def _selectRomFileToUse(self):
        return False

    def get_edit_options(self):
        options = collections.OrderedDict()
        return options

    def get_advanced_modification_options(self):
        options = collections.OrderedDict()
        return options

    def _get_builder_wizard(self, wizard):
        return wizard

# -------------------------------------------------------------------------------------------------
# Virtual Launcher
# Virtual launchers are rom launchers which contain multiple roms from different launchers.
# ------------------------------------------------------------------------------------------------- 
class VirtualLauncher(RomLauncher):
    def __init__(self, launcher_data, settings, romset_repository):
        super(VirtualLauncher, self).__init__(launcher_data, settings, None, romset_repository, None, False)

    def launch(self):
        pass

    def supports_launching_roms(self):
        return True

    def get_launcher_type(self):
        return LAUNCHER_VIRTUAL

    def get_launcher_type_name(self):
        return "Virtual launcher"

    def has_nointro_xml(self):
        return False

    def _selectApplicationToUse(self):
        return False

    def _selectArgumentsToUse(self):
        return False

    def _selectRomFileToUse(self):
        return False

    def get_edit_options(self):
        options = collections.OrderedDict()

        return options

    def get_advanced_modification_options(self):
        options = collections.OrderedDict()

        return options

    def _get_builder_wizard(self, wizard):
        return wizard

# -------------------------------------------------------------------------------------------------
# Standard rom launcher where user can fully customize all settings.
# The standard rom launcher also supports pclone/parent roms.
# -------------------------------------------------------------------------------------------------
class StandardRomLauncher(RomLauncher):
    def get_launcher_type(self):
        return LAUNCHER_ROM

    def get_launcher_type_name(self):
        return "ROM launcher"

    def supports_parent_clone_roms(self):
        return True

    def get_roms_filtered(self):
        if not self.has_roms():
            self.load_roms()

        filtered_roms = []
        view_mode     = self.get_display_mode()
        dp_mode       = self.get_nointro_display_mode()
        pclone_index  = self.get_pclone_indices()

        dp_modes_for_have    = [NOINTRO_DMODE_HAVE, NOINTRO_DMODE_HAVE_UNK, NOINTRO_DMODE_HAVE_MISS]
        dp_modes_for_miss    = [NOINTRO_DMODE_HAVE_MISS, NOINTRO_DMODE_MISS, NOINTRO_DMODE_MISS_UNK]
        dp_modes_for_unknown = [NOINTRO_DMODE_HAVE_UNK, NOINTRO_DMODE_MISS_UNK, NOINTRO_DMODE_UNK]

        for rom_id in self.roms:
            rom = self.roms[rom_id]
            nointro_status = rom.get_nointro_status()

            # >> Filter ROM
            # >> Always include a parent ROM regardless of filters in 'Parent/Clone mode'
            # >> and '1G1R mode' launcher_display_mode if it has 1 or more clones.
            if not view_mode == LAUNCHER_DMODE_FLAT and len(pclone_index[rom_id]):
                filtered_roms.append(rom)

            elif nointro_status == NOINTRO_STATUS_HAVE and dp_mode in dp_mode_for_have:
                filtered_roms.append(rom)

            elif nointro_status == NOINTRO_STATUS_MISS and dp_mode in dp_modes_for_miss:
                filtered_roms.append(rom)

            elif nointro_status == NOINTRO_STATUS_UNKNOWN and dp_mode in dp_modes_for_unknown:
                filtered_roms.append(rom)

            # >> Always copy roms with unknown status (NOINTRO_STATUS_NONE)
            else:
                filtered_roms.append(rom)

        return filtered_roms

    def change_application(self):
        current_application = self.entity_data['application']
        selected_application = xbmcgui.Dialog().browse(1, 'Select the launcher application', 'files',
                                                      self._get_appbrowser_filter('application', self.entity_data), 
                                                      False, False, current_application).decode('utf-8')

        if selected_application is None or selected_application == current_application:
            return False

        self.entity_data['application'] = selected_application
        return True

    def change_arguments(self, args):
        self.entity_data['args'] = args

    def get_args(self):
        return self.entity_data['args']

    def get_additional_argument(self, index):
        args = self.get_all_additional_arguments()
        return args[index]

    def get_all_additional_arguments(self):
        return self.entity_data['args_extra']

    def add_additional_argument(self, arg):

        if not self.entity_data['args_extra']:
            self.entity_data['args_extra'] = []

        self.entity_data['args_extra'].append(arg)
        log_debug('launcher.add_additional_argument() Appending extra_args to launcher {0}'.format(self.get_id()))

    def set_additional_argument(self, index, arg):
        if not self.entity_data['args_extra']:
            self.entity_data['args_extra'] = []

        self.entity_data['args_extra'][index] = arg
        log_debug('launcher.set_additional_argument() Edited args_extra[{0}] to "{1}"'.format(index, self.entity_data['args_extra'][index]))

    def remove_additional_argument(self, index):
        del self.entity_data['args_extra'][index]
        log_debug("launcher.remove_additional_argument() Deleted launcher['args_extra'][{0}]".format(index))

    def get_rom_extensions_combined(self):
        return self.entity_data['romext']

    def get_rom_extensions(self):

        if not 'romext' in self.entity_data:
            return []

        return self.entity_data['romext'].split("|")

    def change_rom_extensions(self, ext):
        self.entity_data['romext'] = ext

    def get_parent_roms(self):
        return self.romset_repository.find_by_launcher(self, LAUNCHER_DMODE_PCLONE)

    def get_pclone_indices(self):
        return self.romset_repository.find_index_file_by_launcher(self, ROMSET_PCLONE)

    def get_parent_indices(self):
        return self.romset_repository.find_index_file_by_launcher(self, ROMSET_CPARENT)

    def update_parent_rom_set(self, roms):
        if not isinstance(roms,dict):
            roms = dict((rom.get_id(), rom) for rom in roms)

        self.romset_repository.save_rom_set(self, roms, LAUNCHER_DMODE_PCLONE)
        roms = roms

    def get_advanced_modification_options(self):
        toggle_window_str = 'ON' if self.entity_data['toggle_window'] else 'OFF'
        non_blocking_str  = 'ON' if self.entity_data['non_blocking'] else 'OFF'
        multidisc_str     = 'ON' if self.entity_data['multidisc'] else 'OFF'

        options = super(StandardRomLauncher, self).get_advanced_modification_options()
        options['CHANGE_APPLICATION']   = "Change Application: '{0}'".format(self.entity_data['application'])
        options['MODIFY_ARGS'] = "Modify Arguments: '{0}'".format(self.entity_data['args'])
        options['ADDITIONAL_ARGS'] = "Modify aditional arguments ..."
        options['CHANGE_ROMPATH'] = "Change ROM path: '{0}'".format(self.entity_data['rompath'])
        options['CHANGE_ROMEXT'] = "Modify ROM extensions: '{0}'".format(self.entity_data['romext'])
        options['TOGGLE_WINDOWED'] = "Toggle Kodi into windowed mode (now {0})".format(toggle_window_str)
        options['TOGGLE_NONBLOCKING'] = "Non-blocking launcher (now {0})".format(non_blocking_str)
        options['TOGGLE_MULTIDISC'] = "Multidisc ROM support (now {0})".format(multidisc_str)

        return options

    def _selectApplicationToUse(self):
        if self.rom.has_alternative_application():
            log_info('StandardRomLauncher() Using ROM altapp')
            self.application = FileNameFactory.create(self.rom.get_alternative_application())
        else:
            self.application = FileNameFactory.create(self.entity_data['application'])

        # --- Check for errors and abort if found --- todo: CHECK
        if not self.application.exists():
            log_error('StandardRomLauncher._selectApplicationToUse(): Launching app not found "{0}"'.format(self.application.getPath()))
            kodi_notify_warn('Launching app not found {0}'.format(self.application.getOriginalPath()))
            return False

        return True

    def _selectArgumentsToUse(self):
        if self.rom.has_alternative_arguments():
            log_info('StandardRomLauncher() Using ROM altarg')
            self.arguments = self.rom.get_alternative_arguments()
        elif self.entity_data['args_extra']:
             # >> Ask user what arguments to launch application
            log_info('StandardRomLauncher() Using Launcher args_extra')
            launcher_args = self.entity_data['args']
            arg_list = [self.entity_data_args] + self.entity_data['args_extra']
            dialog = xbmcgui.Dialog()
            dselect_ret = dialog.select('Select launcher arguments', arg_list)
            
            if dselect_ret < 0: 
                return False
            
            log_info('StandardRomLauncher() User chose args index {0} ({1})'.format(dselect_ret, arg_list[dselect_ret]))
            self.arguments = arg_list[dselect_ret]
        else:
            self.arguments = self.entity_data['args']

        return True

    def _selectRomFileToUse(self):
        if not self.rom.has_multiple_disks():
            self.selected_rom_file = self.rom.get_file()
            return True

        disks = self.rom.get_disks()
        log_info('StandardRomLauncher._selectRomFileToUse() Multidisc ROM set detected')
        dialog = xbmcgui.Dialog()
        dselect_ret = dialog.select('Select ROM to launch in multidisc set', disks)
        if dselect_ret < 0:
           return False

        selected_rom_base = disks[dselect_ret]
        log_info('StandardRomLauncher._selectRomFileToUse() Selected ROM "{0}"'.format(selected_rom_base))

        ROM_temp = self.rom.get_file()
        ROM_dir = FileNameFactory.create(ROM_temp.getDir())
        ROMFileName = ROM_dir.pjoin(selected_rom_base)

        log_info('StandardRomLauncher._selectRomFileToUse() ROMFileName OP "{0}"'.format(ROMFileName.getOriginalPath()))
        log_info('StandardRomLauncher._selectRomFileToUse() ROMFileName  P "{0}"'.format(ROMFileName.getPath()))

        if not ROMFileName.exists():
            log_error('ROM not found "{0}"'.format(ROMFileName.getPath()))
            kodi_notify_warn('ROM not found "{0}"'.format(ROMFileName.getOriginalPath()))
            return False

        self.selected_rom_file = ROMFileName
        return True

    #
    # Creates a new launcher using a wizard of dialogs.
    #
    def _get_builder_wizard(self, wizard):
        wizard = FileBrowseWizardDialog('application', 'Select the launcher application', 1, self._get_appbrowser_filter, wizard) 
        wizard = FileBrowseWizardDialog('rompath', 'Select the ROMs path', 0, '', wizard)
        wizard = DummyWizardDialog('romext', '', wizard, self._get_extensions_from_app_path)
        wizard = KeyboardWizardDialog('romext','Set files extensions, use "|" as separator. (e.g lnk|cbr)', wizard)
        wizard = DummyWizardDialog('args', '', wizard, self._get_arguments_from_application_path)
        wizard = KeyboardWizardDialog('args', 'Application arguments', wizard)
        wizard = DummyWizardDialog('m_name', '', wizard, self._get_title_from_app_path)
        wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, self._get_title_from_app_path)
        wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
        wizard = DummyWizardDialog('assets_path', '', wizard, self._get_value_from_rompath)
        wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard) 

        return wizard

# -------------------------------------------------------------------------------------------------
# Launcher for .lnk files (windows)
# -------------------------------------------------------------------------------------------------
class LnkLauncher(StandardRomLauncher):
    def get_launcher_type(self):
        return LAUNCHER_LNK

    def get_launcher_type_name(self):
        return "LNK launcher"

    def get_edit_options(self):
        options = super(LnkLauncher, self).get_edit_options()
        del options['AUDIT_ROMS']

        return options

    def get_advanced_modification_options(self):
        options = super(LnkLauncher, self).get_advanced_modification_options()
        del options['CHANGE_APPLICATION']
        del options['MODIFY_ARGS']
        del options['ADDITIONAL_ARGS']
        del options['CHANGE_ROMEXT']
        del options['TOGGLE_MULTIDISC']

        return options

    #
    # Creates a new launcher using a wizard of dialogs.
    #
    def _get_builder_wizard(self, wizard):
        wizard = FileBrowseWizardDialog('rompath', 'Select the LNKs path', 0, '', wizard)
        wizard = DummyWizardDialog('romext', 'lnk', wizard)
        wizard = DummyWizardDialog('args', '%rom%', wizard)
        wizard = DummyWizardDialog('m_name', '', wizard, self._get_title_from_app_path)
        wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, self._get_title_from_app_path)
        wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
        wizard = DummyWizardDialog('assets_path', '', wizard, self._get_value_from_rompath)
        wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard) 

        return wizard

# --- Execute Kodi Retroplayer if launcher configured to do so ---
# See https://github.com/Wintermute0110/plugin.program.advanced.emulator.launcher/issues/33
# See https://forum.kodi.tv/showthread.php?tid=295463&pid=2620489#pid2620489
# -------------------------------------------------------------------------------------------------
class RetroplayerLauncher(StandardRomLauncher):
    def launch(self):
        log_info('RetroplayerLauncher() Executing ROM with Kodi Retroplayer ...')
        self.title = self.rom.get_name()
        self._selectApplicationToUse()

        ROMFileName = self._selectRomFileToUse()

        # >> Create listitem object
        label_str = ROMFileName.getBase()
        listitem = xbmcgui.ListItem(label = label_str, label2 = label_str)
        # >> Listitem metadata
        # >> How to fill gameclient = string (game.libretro.fceumm) ???
        genre_list = list(rom['m_genre'])
        listitem.setInfo('game', {'title'    : label_str,     'platform'  : 'Test platform',
                                    'genres'   : genre_list,    'developer' : rom['m_developer'],
                                    'overview' : rom['m_plot'], 'year'      : rom['m_year'] })
        log_info('RetroplayerLauncher() application.getOriginalPath() "{0}"'.format(application.getOriginalPath()))
        log_info('RetroplayerLauncher() ROMFileName.getOriginalPath() "{0}"'.format(ROMFileName.getOriginalPath()))
        log_info('RetroplayerLauncher() label_str                     "{0}"'.format(label_str))

        # --- User notification ---
        if self.settings['display_launcher_notify']:
            kodi_notify('Launching "{0}" with Retroplayer'.format(self.title))

        log_verb('RetroplayerLauncher() Calling xbmc.Player().play() ...')
        xbmc.Player().play(ROMFileName.getOriginalPath(), listitem)
        log_verb('RetroplayerLauncher() Calling xbmc.Player().play() returned. Leaving function.')
        pass
    
    def get_launcher_type(self):
        return LAUNCHER_RETROPLAYER
    
    def get_launcher_type_name(self):        
        return "Retroplayer launcher"
    
    def get_advanced_modification_options(self):
        
        toggle_window_str = 'ON' if self.entity_data['toggle_window'] else 'OFF'
        non_blocking_str  = 'ON' if self.entity_data['non_blocking'] else 'OFF'
        multidisc_str     = 'ON' if self.entity_data['multidisc'] else 'OFF'
        
        options = super(StandardRomLauncher, self).get_advanced_modification_options()
        options['CHANGE_ROMPATH'] = "Change ROM path: '{0}'".format(self.entity_data['rompath'])
        options['CHANGE_ROMEXT'] = "Modify ROM extensions: '{0}'".format(self.entity_data['romext'])
        options['TOGGLE_WINDOWED'] = "Toggle Kodi into windowed mode (now {0})".format(toggle_window_str)
        options['TOGGLE_NONBLOCKING'] = "Non-blocking launcher (now {0})".format(non_blocking_str)
        options['TOGGLE_MULTIDISC'] = "Multidisc ROM support (now {0})".format(multidisc_str)
        
        return options

    #
    # Creates a new launcher using a wizard of dialogs.
    #
    def _get_builder_wizard(self, wizard):
        
        wizard = DummyWizardDialog('application', RETROPLAYER_LAUNCHER_APP_NAME, wizard)
        wizard = FileBrowseWizardDialog('rompath', 'Select the ROMs path', 0, '', wizard)
        wizard = DummyWizardDialog('romext', '', wizard, self._get_extensions_from_app_path)
        wizard = KeyboardWizardDialog('romext','Set files extensions, use "|" as separator. (e.g lnk|cbr)', wizard)
        wizard = DummyWizardDialog('args', '%rom%', wizard)
        wizard = DummyWizardDialog('m_name', '', wizard, self._get_title_from_app_path)
        wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, self._get_title_from_app_path)
        wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
        wizard = DummyWizardDialog('assets_path', '', wizard, self._get_value_from_rompath)
        wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard) 
            
        return wizard
    
# -------------------------------------------------------------------------------------------------
# Read RetroarchLauncher.md
# -------------------------------------------------------------------------------------------------
class RetroarchLauncher(StandardRomLauncher):
    
    def get_launcher_type(self):
        return LAUNCHER_RETROARCH
    
    def get_launcher_type_name(self):        
        return "Retroarch launcher"
    
    def change_application(self):

        current_application = self.entity_data['application']
        selected_application = xbmcgui.Dialog().browse(0, 'Select the Retroarch path', 'files',
                                                      '', False, False, current_application).decode('utf-8')

        if selected_application is None or selected_application == current_application:
            return False

        self.entity_data['application'] = selected_application
        return True

    def get_advanced_modification_options(self):
        
        toggle_window_str = 'ON' if self.entity_data['toggle_window'] else 'OFF'
        non_blocking_str  = 'ON' if self.entity_data['non_blocking'] else 'OFF'
        multidisc_str     = 'ON' if self.entity_data['multidisc'] else 'OFF'
        
        options = super(StandardRomLauncher, self).get_advanced_modification_options()
        options['CHANGE_APPLICATION']   = "Change Retroarch path: '{0}'".format(self.entity_data['application'])
        options['MODIFY_ARGS'] = "Modify Arguments: '{0}'".format(self.entity_data['args'])
        options['ADDITIONAL_ARGS'] = "Modify aditional arguments ..."
        options['CHANGE_ROMPATH'] = "Change ROM path: '{0}'".format(self.entity_data['rompath'])
        options['CHANGE_ROMEXT'] = "Modify ROM extensions: '{0}'".format(self.entity_data['romext'])
        options['TOGGLE_WINDOWED'] = "Toggle Kodi into windowed mode (now {0})".format(toggle_window_str)
        options['TOGGLE_NONBLOCKING'] = "Non-blocking launcher (now {0})".format(non_blocking_str)
        options['TOGGLE_MULTIDISC'] = "Multidisc ROM support (now {0})".format(multidisc_str)
        
        return options

    def _selectApplicationToUse(self):
        
        if is_windows():
            self.application = FileNameFactory.create(self.entity_data['application'])
            self.application = self.application.append('retroarch.exe')  
            return True

        if is_android():
            self.application = FileNameFactory.create('/system/bin/am')
            return True

        #todo other os
        self.application = ''
        return False

    def _selectArgumentsToUse(self):
        
        if is_windows() or is_linux():            
            self.arguments =  '-L "$retro_core$" '
            self.arguments += '-c "$retro_config$" '
            self.arguments += '"$rom$"'
            self.arguments += self.entity_data['args']
            return True

        if is_android():

            self.arguments =  'start --user 0 -a android.intent.action.MAIN -c android.intent.category.LAUNCHER '
            self.arguments += '-n com.retroarch/.browser.retroactivity.RetroActivityFuture '
            self.arguments += '-e ROM \'$rom$\' '
            self.arguments += '-e LIBRETRO $retro_core$ '
            self.arguments += '-e CONFIGFILE $retro_config$ '
            self.arguments += self.entity_data['args'] if 'args' in self.entity_data else ''
            return True

        #todo other os
        return False
    
    #
    # Creates a new launcher using a wizard of dialogs.
    #
    def _get_builder_wizard(self, wizard):
                
        wizard = DummyWizardDialog('application', self._get_retroarch_app_folder(self.settings), wizard)
        wizard = FileBrowseWizardDialog('application', 'Select the Retroarch path', 0, '', wizard) 
        wizard = DictionarySelectionWizardDialog('retro_config', 'Select the configuration', self._get_available_retroarch_configurations, wizard)
        wizard = FileBrowseWizardDialog('retro_config', 'Select the configuration', 0, '', wizard, None, self._user_selected_custom_browsing) 
        wizard = DictionarySelectionWizardDialog('retro_core_info', 'Select the core', self._get_available_retroarch_cores, wizard, self._load_selected_core_info)
        wizard = KeyboardWizardDialog('retro_core_info', 'Enter path to core file', wizard, self._load_selected_core_info, self._user_selected_custom_browsing)
        wizard = FileBrowseWizardDialog('rompath', 'Select the ROMs path', 0, '', wizard) 
        wizard = KeyboardWizardDialog('romext','Set files extensions, use "|" as separator. (e.g nes|zip)', wizard)
        wizard = DummyWizardDialog('args', self._get_default_retroarch_arguments(), wizard)
        wizard = KeyboardWizardDialog('args', 'Extra application arguments', wizard)
        wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, self._get_title_from_app_path)
        wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
        wizard = DummyWizardDialog('assets_path', '', wizard, self._get_value_from_rompath)
        wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard) 
                    
        return wizard
    
    def _get_retroarch_app_folder(self, settings):
    
        retroarch_folder = FileNameFactory.create(settings['io_retroarch_sys_dir'])      
    
        if retroarch_folder.exists():
            return retroarch_folder.getOriginalPath()

        if is_android():
        
            android_retroarch_folders = [
                '/storage/emulated/0/Android/data/com.retroarch/',
                '/data/data/com.retroarch/',
                '/storage/sdcard0/Android/data/com.retroarch/',
                '/data/user/0/com.retroarch']

        
            for retroach_folder_path in android_retroarch_folders:
                retroarch_folder = FileNameFactory.create(retroach_folder_path)
                if retroarch_folder.exists():
                    return retroarch_folder.getOriginalPath()

        return '/'

    def _get_available_retroarch_configurations(self, item_key, launcher):
    
        configs = collections.OrderedDict()
        configs['BROWSE'] = 'Browse for configuration'

        retroarch_folders = []
        retroarch_folders.append(FileNameFactory.create(launcher['application']))

        if is_android():
            retroarch_folders.append(FileNameFactory.create('/storage/emulated/0/Android/data/com.retroarch/'))
            retroarch_folders.append(FileNameFactory.create('/data/data/com.retroarch/'))
            retroarch_folders.append(FileNameFactory.create('/storage/sdcard0/Android/data/com.retroarch/'))
            retroarch_folders.append(FileNameFactory.create('/data/user/0/com.retroarch/'))
        
        for retroarch_folder in retroarch_folders:
            log_debug("get_available_retroarch_configurations() scanning path '{0}'".format(retroarch_folder.getOriginalPath()))
            files = retroarch_folder.recursiveScanFilesInPathAsFileNameObjects('*.cfg')
        
            if len(files) < 1:
                continue

            for file in files:
                log_debug("get_available_retroarch_configurations() adding config file '{0}'".format(file.getOriginalPath()))
                
                configs[file.getOriginalPath()] = file.getBase_noext()

            return configs

        return configs

    def _get_available_retroarch_cores(self, item_key, launcher):
    
        cores = collections.OrderedDict()
        cores['BROWSE'] = 'Manual enter path to core'
        cores_ext = '*.*'

        if is_windows():
            cores_ext = '*.dll'
        else:
            cores_ext = '*.so'

        config_file     = FileNameFactory.create(launcher['retro_config'])
        parent_dir      = config_file.getDirAsFileName()
        configuration   = config_file.readPropertyFile()    
        info_folder     = self._create_path_from_retroarch_setting(configuration['libretro_info_path'], parent_dir)
        cores_folder    = self._create_path_from_retroarch_setting(configuration['libretro_directory'], parent_dir)
        
        log_debug("get_available_retroarch_cores() scanning path '{0}'".format(cores_folder.getOriginalPath()))

        if not info_folder.exists():
            log_warning('Retroarch info folder not found {}'.format(info_folder.getOriginalPath()))
            return cores
    
        if not cores_folder.exists():
            log_warning('Retroarch cores folder not found {}'.format(cores_folder.getOriginalPath()))
            return cores

        files = cores_folder.scanFilesInPathAsFileNameObjects(cores_ext)
        for file in files:
                
            log_debug("get_available_retroarch_cores() adding core '{0}'".format(file.getOriginalPath()))    
            info_file = self._switch_core_to_info_file(file, info_folder)

            if not info_file.exists():
                log_warning('get_available_retroarch_cores() Cannot find "{}". Skipping core "{}"'.format(info_file.getOriginalPath(), file.getBase()))
                continue

            log_debug("get_available_retroarch_cores() using info '{0}'".format(info_file.getOriginalPath()))    
            core_info = info_file.readPropertyFile()
            cores[info_file.getOriginalPath()] = core_info['display_name']

        return cores

    def _load_selected_core_info(self, input, item_key, launcher):

        if input == 'BROWSE':
            return input
    
        if is_windows():
            cores_ext = 'dll'
        else:
            cores_ext = 'so'

        if input.endswith(cores_ext):
            core_file = FileNameFactory.create(input)
            launcher['retro_core']  = core_file.getOriginalPath()
            return input

        config_file     = FileNameFactory.create(launcher['retro_config'])
        parent_dir      = config_file.getDirAsFileName()
        configuration   = config_file.readPropertyFile()    
        cores_folder    = self._create_path_from_retroarch_setting(configuration['libretro_directory'], parent_dir)
        info_file       = FileNameFactory.create(input)
        
        if not cores_folder.exists():
            log_warning('Retroarch cores folder not found {}'.format(cores_folder.getOriginalPath()))
            kodi_notify_error('Retroarch cores folder not found {}'.format(cores_folder.getOriginalPath()))
            return ''

        core_file = self._switch_info_to_core_file(info_file, cores_folder, cores_ext)
        core_info = info_file.readPropertyFile()

        launcher[item_key]      = info_file.getOriginalPath()
        launcher['retro_core']  = core_file.getOriginalPath()
        launcher['romext']      = core_info['supported_extensions']
        launcher['platform']    = core_info['systemname']
        launcher['m_developer'] = core_info['manufacturer']
        launcher['m_name']      = core_info['systemname']

        return input

    def _get_default_retroarch_arguments(self):

        args = ''
        if is_android():
            args += '-e IME com.android.inputmethod.latin/.LatinIME -e REFRESH 60'

        return args
    
    def _create_path_from_retroarch_setting(self, path_from_setting, parent_dir):

        if not path_from_setting.endswith('\\') and not path_from_setting.endswith('/'):
            path_from_setting = path_from_setting + parent_dir.path_separator()

        if path_from_setting.startswith(':\\'):
            path_from_setting = path_from_setting[2:]
            return parent_dir.pjoin(path_from_setting)
        else:
            folder = FileNameFactory.create(path_from_setting)
            if '/data/user/0/' in folder.getOriginalPath():
                alternative_folder = foldexr.getOriginalPath()
                alternative_folder = alternative_folder.replace('/data/user/0/', '/data/data/')
                folder = FileNameFactory.create(alternative_folder)

            return folder

    def _switch_core_to_info_file(self, core_file, info_folder):
    
        info_file = core_file.switchExtension('info')
   
        if is_android():
            info_file = info_folder.pjoin(info_file.getBase().replace('_android.', '.'))
        else:
            info_file = info_folder.pjoin(info_file.getBase())

        return info_file

    def _switch_info_to_core_file(self, info_file, cores_folder, cores_ext):
    
        core_file = info_file.switchExtension(cores_ext)

        if is_android():
            core_file = cores_folder.pjoin(core_file.getBase().replace('.', '_android.'))
        else:
            core_file = cores_folder.pjoin(core_file.getBase())

        return core_file
    
# -------------------------------------------------------------------------------------------------
# Launcher to use with a local Steam application and account.
# -------------------------------------------------------------------------------------------------
class SteamLauncher(RomLauncher):

    def __init__(self, launcher_data, settings, executorFactory, romset_repository, statsStrategy):
        super(SteamLauncher, self).__init__(launcher_data, settings, executorFactory, romset_repository, statsStrategy, False)
    
    def get_launcher_type(self):
        return LAUNCHER_STEAM
    
    def get_launcher_type_name(self):        
        return "Steam launcher"
    
    def get_steam_id(self):
        return self.entity_data['steamid']

    def get_edit_options(self):
        
        options = super(SteamLauncher, self).get_edit_options()
        del options['AUDIT_ROMS']

        return options

    def get_advanced_modification_options(self):
        
        toggle_window_str = 'ON' if self.entity_data['toggle_window'] else 'OFF'
        non_blocking_str  = 'ON' if self.entity_data['non_blocking'] else 'OFF'
        
        options = super(SteamLauncher, self).get_advanced_modification_options()
        options['TOGGLE_WINDOWED'] = "Toggle Kodi into windowed mode (now {0})".format(toggle_window_str)
        options['TOGGLE_NONBLOCKING'] = "Non-blocking launcher (now {0})".format(non_blocking_str)
        
        return options
    
    def _selectApplicationToUse(self):
        self.application = FileNameFactory.create('steam://rungameid/')
        return True

    def _selectArgumentsToUse(self):        
        self.arguments = '$steamid$'
        return True

    def _selectRomFileToUse(self):
        steam_id = self.rom.get_custom_attribute('steamid', '')
        log_info('SteamLauncher._selectRomFileToUse() ROM ID {0}: @{1}"'.format(steam_id, self.title))
        return True
    
       #def launch(self):
       #    
       #    self.title  = self.rom['m_name']
       #    
       #    url = 'steam://rungameid/'
       #
       #    self.application = FileNameFactory.create('steam://rungameid/')
       #    self.arguments = str(self.rom['steamid'])
       #
       #    log_info('SteamLauncher() ROM ID {0}: @{1}"'.format(self.rom['steamid'], self.rom['m_name']))
       #    self.statsStrategy.updateRecentlyPlayedRom(self.rom)       
       #    
       #    super(SteamLauncher, self).launch()
       #    pass    
    
    def _get_builder_wizard(self, wizard):
        
        wizard = DummyWizardDialog('application', 'Steam', wizard)
        wizard = KeyboardWizardDialog('steamid','Steam ID', wizard)
        wizard = DummyWizardDialog('m_name', 'Steam', wizard)
        wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, self._get_title_from_app_path)
        wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
        wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard)
        wizard = DummyWizardDialog('rompath', '', wizard, self._get_value_from_assetpath)         
                    
        return wizard
    
    def _get_value_from_assetpath(self, input, item_key, launcher):

        if input:
            return input

        romPath = FileNameFactory.create(launcher['assets_path'])
        romPath = romPath.pjoin('games')

        return romPath.getOriginalPath()
 
# -------------------------------------------------------------------------------------------------
# Launcher to use with Nvidia Gamestream servers.
# -------------------------------------------------------------------------------------------------
class NvidiaGameStreamLauncher(RomLauncher):

    def __init__(self, launcher_data, settings, executorFactory, romset_repository, statsStrategy):

        super(NvidiaGameStreamLauncher, self).__init__(launcher_data, settings, executorFactory, romset_repository, statsStrategy, False)

    def get_launcher_type(self):
        return LAUNCHER_NVGAMESTREAM
    
    def get_launcher_type_name(self):        
        return "Nvidia GameStream launcher"

    def get_server(self):
        return self.entity_data['server']

    def get_certificates_path(self):
        return self._get_value_as_filename('certificates_path')

    def get_edit_options(self):

        options = super(NvidiaGameStreamLauncher, self).get_edit_options()
        del options['AUDIT_ROMS']

        return options

    def get_advanced_modification_options(self):
        
        toggle_window_str = 'ON' if self.entity_data['toggle_window'] else 'OFF'
        non_blocking_str  = 'ON' if self.entity_data['non_blocking'] else 'OFF'
        
        options = super(SteamLauncher, self).get_advanced_modification_options()
        options['TOGGLE_WINDOWED'] = "Toggle Kodi into windowed mode (now {0})".format(toggle_window_str)
        options['TOGGLE_NONBLOCKING'] = "Non-blocking launcher (now {0})".format(non_blocking_str)
        
    def _selectApplicationToUse(self):
        
        streamClient = self.entity_data['application']
        
        # java application selected (moonlight-pc)
        if '.jar' in streamClient:
            self.application = FileNameFactory.create(os.getenv("JAVA_HOME"))
            if is_windows():
                self.application = self.application.pjoin('bin\\java.exe')
            else:
                self.application = self.application.pjoin('bin/java')

            return True

        if is_windows():
            self.application = FileNameFactory.create(streamClient)
            return True

        if is_android():
            self.application = FileNameFactory.create('/system/bin/am')
            return True

        return True

    def _selectArgumentsToUse(self):
        
        streamClient = self.entity_data['application']
            
        # java application selected (moonlight-pc)
        if '.jar' in streamClient:
            self.arguments =  '-jar "$application$" '
            self.arguments += '-host $server$ '
            self.arguments += '-fs '
            self.arguments += '-app "$gamestream_name$" '
            self.arguments += self.entity_data['args']
            return True

        if is_android():

            if streamClient == 'NVIDIA':
                self.arguments =  'start --user 0 -a android.intent.action.VIEW '
                self.arguments += '-n com.nvidia.tegrazone3/com.nvidia.grid.UnifiedLaunchActivity '
                self.arguments += '-d nvidia://stream/target/2/$streamid$'
                return True

            if streamClient == 'MOONLIGHT':
                self.arguments =  'start --user 0 -a android.intent.action.MAIN '
                self.arguments += '-c android.intent.category.LAUNCHER ' 
                self.arguments += '-n com.limelight/.Game '
                self.arguments += '-e Host $server$ '
                self.arguments += '-e AppId $streamid$ '
                self.arguments += '-e AppName "$gamestream_name$" '
                self.arguments += '-e PcName "$server_hostname$" '
                self.arguments += '-e UUID $server_id$ '
                self.arguments += '-e UniqueId {} '.format(misc_generate_random_SID())

                return True
        
        # else
        self.arguments = self.entity_data['args']
        return True 
  
    def _selectRomFileToUse(self):
        return True
    
    def get_advanced_modification_options(self):
        
        toggle_window_str = 'ON' if self.entity_data['toggle_window'] else 'OFF'
        non_blocking_str  = 'ON' if self.entity_data['non_blocking'] else 'OFF'
        
        options = super(NvidiaGameStreamLauncher, self).get_advanced_modification_options()
        options['TOGGLE_WINDOWED'] = "Toggle Kodi into windowed mode (now {0})".format(toggle_window_str)
        options['TOGGLE_NONBLOCKING'] = "Non-blocking launcher (now {0})".format(non_blocking_str)
        
        return options
    

    #
    # Creates a new launcher using a wizard of dialogs.
    #
    def _get_builder_wizard(self, wizard):
        
        info_txt = 'To pair with your Geforce Experience Computer we need to make use of valid certificates. '
        info_txt += 'Unfortunately at this moment we cannot create these certificates directly from within Kodi.\n'
        info_txt += 'Please read the wiki for details how to create them before you go further.'

        wizard = FormattedMessageWizardDialog('certificates_path', 'Pairing with Gamestream PC', info_txt, wizard)
        wizard = DictionarySelectionWizardDialog('application', 'Select the client', {'NVIDIA': 'Nvidia', 'MOONLIGHT': 'Moonlight'}, wizard, self._check_if_selected_gamestream_client_exists, lambda pk,p: is_android())
        wizard = DictionarySelectionWizardDialog('application', 'Select the client', {'JAVA': 'Moonlight-PC (java)', 'EXE': 'Moonlight-Chrome (not supported yet)'}, wizard, None, lambda pk,p: not is_android())
        wizard = FileBrowseWizardDialog('application', 'Select the Gamestream client jar', 1, self._get_appbrowser_filter, wizard, None, lambda pk,p: not is_android())
        wizard = KeyboardWizardDialog('args', 'Additional arguments', wizard, None, lambda pk,p: not is_android())
        wizard = InputWizardDialog('server', 'Gamestream Server', xbmcgui.INPUT_IPADDRESS, wizard, self._validate_gamestream_server_connection)
        wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, self._get_title_from_app_path)
        wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard)
        wizard = DummyWizardDialog('rompath', '', wizard, self._get_value_from_assetpath)   
        # Pairing with pin code will be postponed untill crypto and certificate support in kodi
        # wizard = DummyWizardDialog('pincode', None, wizard, generatePairPinCode)
        wizard = DummyWizardDialog('certificates_path', None, wizard, self._try_to_resolve_path_to_nvidia_certificates)
        wizard = FileBrowseWizardDialog('certificates_path', 'Select the path with valid certificates', 0, '', wizard, self._validate_nvidia_certificates) 
        wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)       
                    
        return wizard

    def _generatePairPinCode(self, input, item_key, launcher):
    
        return gamestreamServer(None, None).generatePincode()

    def _check_if_selected_gamestream_client_exists(self, input, item_key, launcher):

        if input == 'NVIDIA':
            nvidiaDataFolder = FileNameFactory.create('/data/data/com.nvidia.tegrazone3/')
            nvidiaAppFolder = FileNameFactory.create('/storage/emulated/0/Android/data/com.nvidia.tegrazone3/')
            if not nvidiaAppFolder.exists() and not nvidiaDataFolder.exists():
                kodi_notify_warn('Could not find Nvidia Gamestream client. Make sure it\'s installed.')

        if input == 'MOONLIGHT':
            moonlightDataFolder = FileNameFactory.create('/data/data/com.limelight/')
            moonlightAppFolder = FileNameFactory.create('/storage/emulated/0/Android/data/com.limelight/')
            if not moonlightAppFolder.exists() and not moonlightDataFolder.exists():
                kodi_notify_warn('Could not find Moonlight Gamestream client. Make sure it\'s installed.')
        
        return input

    def _try_to_resolve_path_to_nvidia_certificates(self, input, item_key, launcher):
    
        path = GameStreamServer.try_to_resolve_path_to_nvidia_certificates()
        return path

    def _validate_nvidia_certificates(self, input, item_key, launcher):

        certificates_path = FileNameFactory.create(input)
        gs = GameStreamServer(input, certificates_path)
        if not gs.validate_certificates():
            kodi_notify_warn('Could not find certificates to validate. Make sure you already paired with the server with the Shield or Moonlight applications.')

        return certificates_path.getOriginalPath()

    def _validate_gamestream_server_connection(self, input, item_key, launcher):

        gs = GameStreamServer(input, None)
        if not gs.connect():
            kodi_notify_warn('Could not connect to gamestream server')

        launcher['server_id'] = gs.get_uniqueid()
        launcher['server_hostname'] = gs.get_hostname()

        log_debug('validate_gamestream_server_connection() Found correct gamestream server with id "{}" and hostname "{}"'.format(launcher['server_id'],launcher['server_hostname']))

        return input

# #################################################################################################
# #################################################################################################
# Executors
# #################################################################################################
# #################################################################################################
class ExecutorFactory():
    def __init__(self, settings, g_PATHS):
        self.settings = settings
        self.logFile = g_PATHS.LAUNCHER_REPORT_FILE_PATH

    def create_from_pathstring(self, application_string):
        app = FileNameFactory.create(application_string)
        return self.create(app)

    def create(self, application):
        if application.getBase().lower().replace('.exe' , '') == 'xbmc' \
            or 'xbmc-fav-' in application.getOriginalPath() or 'xbmc-sea-' in application.getOriginalPath():
            return XbmcExecutor(self.logFile)

        if re.search('.*://.*', application.getOriginalPath()):
            return WebBrowserExecutor(self.logFile)
        
        if is_windows():

            if application.getExt().lower() == '.bat' or application.getExt().lower() == '.cmd' :
                return WindowsBatchFileExecutor(self.logFile, self.settings['show_batch_window'])
            
            # >> Standalone launcher where application is a LNK file
            if application.getExt().lower() == '.lnk': 
                return WindowsLnkFileExecutor(self.logFile)

            return WindowsExecutor(self.logFile, self.settings['windows_cd_apppath'], self.settings['windows_close_fds'])

        if is_android():
            return AndroidExecutor()

        if is_linux():
            return LinuxExecutor(self.logFile, self.settings['lirc_state'])
        
        if is_osx():
            return OSXExecutor(self.logFile)

        kodi_notify_warn('Cannot determine the running platform')
        return None

class Executor():
    __metaclass__ = abc.ABCMeta

    def __init__(self, logFile):
        self.logFile = logFile

    @abc.abstractmethod
    def execute(self, application, arguments, non_blocking):
        pass

class XbmcExecutor(Executor):
    # --- Execute Kodi built-in function under certain conditions ---
    def execute(self, application, arguments, non_blocking):

        xbmc.executebuiltin('XBMC.{0}'.format(arguments))
        pass
    
# >> Linux
# >> New in 0.9.7: always close all file descriptions except 0, 1 and 2 on the child
# >> process. This is to avoid Kodi opens sockets be inherited by the child process. A
# >> wrapper script may terminate Kodi using JSON RPC and if file descriptors are not
# >> closed Kodi will complain that the remote interfacte cannot be initialised. I believe
# >> the cause is that the socket is kept open by the wrapper script.
class LinuxExecutor(Executor):
    def __init__(self, logFile, lirc_state):
        self.lirc_state = lirc_state
        
        super(LinuxExecutor, self).__init__(logFile)

    def execute(self, application, arguments, non_blocking):
        import subprocess
        import shlex

        if self.lirc_state:
           xbmc.executebuiltin('LIRC.stop')

        arg_list  = shlex.split(arguments, posix = True)
        command = [application.getPath()] + arg_list

        # >> Old way of launching child process. os.system() is deprecated and should not
        # >> be used anymore.
        # os.system('"{0}" {1}'.format(application, arguments).encode('utf-8'))

         # >> New way of launching, uses subproces module. Also, save child process stdout.
        if non_blocking:
            # >> In a non-blocking launch stdout/stderr of child process cannot be recorded.
            log_info('LinuxExecutor: Launching non-blocking process subprocess.Popen()')
            p = subprocess.Popen(command, close_fds = True)
        else:
            with open(self.logFile.getPath(), 'w') as f:
                retcode = subprocess.call(command, stdout = f, stderr = subprocess.STDOUT, close_fds = True)
            log_info('LinuxExecutor: Process retcode = {0}'.format(retcode))
            if self.lirc_state:
                xbmc.executebuiltin('LIRC.start')

        pass

class AndroidExecutor(Executor):
    def __init__(self):
        super(AndroidExecutor, self).__init__(None)

    def execute(self, application, arguments, non_blocking):
        retcode = os.system("{0} {1}".format(application.getPath(), arguments).encode('utf-8'))

        log_info('AndroidExecutor: Process retcode = {0}'.format(retcode))
        pass

class OSXExecutor(Executor):
    def execute(self, application, arguments, non_blocking):
        import subprocess
        import shlex
        
        arg_list  = shlex.split(arguments, posix = True)
        command = [application.getPath()] + arg_list
        
        # >> Old way
        # os.system('"{0}" {1}'.format(application, arguments).encode('utf-8'))
            
        # >> New way.
        with open(self.logFile.getPath(), 'w') as f:
            retcode = subprocess.call(command, stdout = f, stderr = subprocess.STDOUT)

        log_info('OSXExecutor: Process retcode = {0}'.format(retcode))

        pass

class WindowsLnkFileExecutor(Executor):
    def execute(self, application, arguments, non_blocking):
                
        log_debug('Executor (Windows) Launching LNK application')
        # os.system('start "AEL" /b "{0}"'.format(application).encode('utf-8'))
        retcode = subprocess.call('start "AEL" /b "{0}"'.format(application.getPath()).encode('utf-8'), shell = True)
        log_info('Executor (Windows) LNK app retcode = {0}'.format(retcode))
        pass

# >> CMD/BAT files in Windows
class WindowsBatchFileExecutor(Executor):
    def __init__(self, logFile, show_batch_window):
        self.show_batch_window = show_batch_window

        super(WindowsBatchFileExecutor, self).__init__(logFile)

    def execute(self, application, arguments, non_blocking):
        import subprocess
        import shlex

        arg_list  = shlex.split(arguments, posix = True)
        command = [application.getPath()] + arg_list
        apppath = application.getDir()
        
        # --- Workaround to run UNC paths in Windows ---
        # >> Retroarch now support ROMs in UNC paths (Samba remotes)
        new_command = list(command)
        for i, _ in enumerate(command):
            if command[i][0] == '\\':
                new_command[i] = '\\' + command[i]
                log_debug('Executor (Windows BatchFile): Before arg #{0} = "{1}"'.format(i, command[i]))
                log_debug('Executor (Windows BatchFile): Now    arg #{0} = "{1}"'.format(i, new_command[i]))
        command = list(new_command)
        log_debug('Executor (Windows BatchFile): command = {0}'.format(command))
        
        log_debug('Executor (Windows BatchFile) Launching BAT application')
        log_debug('Executor (Windows BatchFile) Ignoring setting windows_cd_apppath')
        log_debug('Executor (Windows BatchFile) Ignoring setting windows_close_fds')
        log_debug('Executor (Windows BatchFile) show_batch_window = {0}'.format(self.show_batch_window))
        info = subprocess.STARTUPINFO()
        info.dwFlags = 1
        info.wShowWindow = 5 if self.show_batch_window else 0
        retcode = subprocess.call(command, cwd = apppath.encode('utf-8'), close_fds = True, startupinfo = info)
        log_info('Executor (Windows BatchFile) Process BAR retcode = {0}'.format(retcode))

        pass

class WindowsExecutor(Executor):
    def __init__(self, logFile, cd_apppath, close_fds):
        self.windows_cd_apppath = cd_apppath
        self.windows_close_fds  = close_fds

        super(WindowsExecutor, self).__init__(logFile)

    # >> Windoze
    # NOTE subprocess24_hack.py was hacked to always set CreateProcess() bInheritHandles to 0.
    # bInheritHandles [in] If this parameter TRUE, each inheritable handle in the calling 
    # process is inherited by the new process. If the parameter is FALSE, the handles are not 
    # inherited. Note that inherited handles have the same value and access rights as the original handles.
    # See https://msdn.microsoft.com/en-us/library/windows/desktop/ms682425(v=vs.85).aspx
    #
    # Same behaviour can be achieved in current version of subprocess with close_fds.
    # If close_fds is true, all file descriptors except 0, 1 and 2 will be closed before the 
    # child process is executed. (Unix only). Or, on Windows, if close_fds is true then no handles 
    # will be inherited by the child process. Note that on Windows, you cannot set close_fds to 
    # true and also redirect the standard handles by setting stdin, stdout or stderr.
    #
    # If I keep old launcher behaviour in Windows (close_fds = True) then program output cannot
    # be redirected to a file.
    #
    def execute(self, application, arguments, non_blocking):
        import subprocess
        import shlex
        
        arg_list  = shlex.split(arguments, posix = True)
        command = [application.getPath()] + arg_list
        apppath = application.getDir()
        
        # --- Workaround to run UNC paths in Windows ---
        # >> Retroarch now support ROMs in UNC paths (Samba remotes)
        new_command = list(command)
        for i, _ in enumerate(command):
            if command[i][0] == '\\':
                new_command[i] = '\\' + command[i]
                log_debug('WindowsExecutor: Before arg #{0} = "{1}"'.format(i, command[i]))
                log_debug('WindowsExecutor: Now    arg #{0} = "{1}"'.format(i, new_command[i]))
        command = list(new_command)
        log_debug('WindowsExecutor: command = {0}'.format(command))

        # >> cwd = apppath.encode('utf-8') fails if application path has Unicode on Windows
        # >> A workaraound is to use cwd = apppath.encode(sys.getfilesystemencoding()) --> DOES NOT WORK
        # >> For the moment AEL cannot launch executables on Windows having Unicode paths.
        log_debug('Executor (Windows) Launching regular application')
        log_debug('Executor (Windows) windows_cd_apppath = {0}'.format(self.windows_cd_apppath))
        log_debug('Executor (Windows) windows_close_fds  = {0}'.format(self.windows_close_fds))

        # >> Note that on Windows, you cannot set close_fds to true and also redirect the 
        # >> standard handles by setting stdin, stdout or stderr.
        if self.windows_cd_apppath and self.windows_close_fds:
            retcode = subprocess.call(command, cwd = apppath.encode('utf-8'), close_fds = True)
        elif self.windows_cd_apppath and not self.windows_close_fds:
            with open(self.logFile.getPath(), 'w') as f:
                retcode = subprocess.call(command, cwd = apppath.encode('utf-8'), close_fds = False,
                                            stdout = f, stderr = subprocess.STDOUT)
        elif not self.windows_cd_apppath and self.windows_close_fds:
            retcode = subprocess.call(command, close_fds = True)
        elif not self.windows_cd_apppath and not self.windows_close_fds:
            with open(self.logFile.getPath(), 'w') as f:
                retcode = subprocess.call(command, close_fds = False, stdout = f, stderr = subprocess.STDOUT)
        else:
            raise Exception('Logical error')
        
        log_info('Executor (Windows) Process retcode = {0}'.format(retcode))
           
        pass

class WebBrowserExecutor(Executor):
    def execute(self, application, arguments, non_blocking):
        import webbrowser
        
        command = application.getOriginalPath() + arguments
        log_debug('WebBrowserExecutor.execute() Launching URL: {0}'.format(command))
        webbrowser.open(command)

        pass

# #################################################################################################
# #################################################################################################
# Gamestream
# #################################################################################################
# #################################################################################################

class GameStreamServer(object):
    def __init__(self, host, certificates_path):
        self.host = host
        self.unique_id = random.getrandbits(16)

        if certificates_path:
            self.certificates_path = certificates_path
            self.certificate_file_path = self.certificates_path.pjoin('nvidia.crt')
            self.certificate_key_file_path = self.certificates_path.pjoin('nvidia.key')
        else:
            self.certificates_path = FileNameFactory.create('')
            self.certificate_file_path = FileNameFactory.create('')
            self.certificate_key_file_path = FileNameFactory.create('')

        log_debug('GameStreamServer() Using certificate key file {}'.format(self.certificate_key_file_path.getOriginalPath()))
        log_debug('GameStreamServer() Using certificate file {}'.format(self.certificate_file_path.getOriginalPath()))

        self.pem_cert_data = None
        self.key_cert_data = None

    def _perform_server_request(self, end_point,  useHttps=True, parameters = None):
        if useHttps:
            url = "https://{0}:47984/{1}?uniqueid={2}&uuid={3}".format(self.host, end_point, self.unique_id, uuid.uuid4().hex)
        else:
            url = "http://{0}:47989/{1}?uniqueid={2}&uuid={3}".format(self.host, end_point, self.unique_id, uuid.uuid4().hex)

        if parameters:
            for key, value in parameters.iteritems():
                url = url + "&{0}={1}".format(key, value)

        handler = HTTPSClientAuthHandler(self.certificate_key_file_path.getOriginalPath(), self.certificate_file_path.getOriginalPath())
        page_data = net_get_URL_using_handler(url, handler)
    
        if page_data is None:
            return None

        root = ET.fromstring(page_data)
        #log_debug(ET.tostring(root,encoding='utf8',method='xml'))
        return root

    def connect(self):
        log_debug('Connecting to gamestream server {}'.format(self.host))
        self.server_info = self._perform_server_request("serverinfo")
        
        if not self.is_connected():
            self.server_info = self._perform_server_request("serverinfo", False)
        
        return self.is_connected()

    def is_connected(self):
        if self.server_info is None:
            log_debug('No succesfull connection to the server has been made')
            return False

        if self.server_info.find('state') is None:
            log_debug('Server state {0}'.format(self.server_info.attrib['status_code']))
        else:
            log_debug('Server state {0}'.format(self.server_info.find('state').text))

        return self.server_info.attrib['status_code'] == '200'

    def get_server_version(self):

        appVersion = self.server_info.find('appversion')
        return VersionNumber(appVersion.text)
    
    def get_uniqueid(self):

        uniqueid = self.server_info.find('uniqueid').text
        return uniqueid
    
    def get_hostname(self):

        hostname = self.server_info.find('hostname').text
        return hostname

    def generatePincode(self):

        i1 = random.randint(1, 9)
        i2 = random.randint(1, 9)
        i3 = random.randint(1, 9)
        i4 = random.randint(1, 9)
    
        return '{0}{1}{2}{3}'.format(i1, i2, i3, i4)

    def is_paired(self):

        if not self.is_connected():
            log_warning('Connect first')
            return False

        pairStatus = self.server_info.find('PairStatus')
        return pairStatus.text == '1'

    def pairServer(self, pincode):
        from utils_cryptography import *

        if not self.is_connected():
            log_warning('Connect first')
            return False

        version = self.get_server_version()
        log_info("Pairing with server generation: {0}".format(version.getFullString()))

        majorVersion = version.getMajor()
        if majorVersion >= 7:
			# Gen 7+ uses SHA-256 hashing
            hashAlgorithm = HashAlgorithm(256)
        else:
            # Prior to Gen 7, SHA-1 is used
            hashAlgorithm = HashAlgorithm(1)

        log_debug('Pin {0}'.format(pincode))
        
        # Generate a salt for hashing the PIN
        salt = randomBytes(16)
        # Combine the salt and pin
        saltAndPin = salt + bytearray(pincode, 'utf-8')

        # Create an AES key from them
        aes_cypher = AESCipher(saltAndPin, hashAlgorithm)

        # get certificates ready
        log_debug('Getting local certificate files')
        client_certificate      = self.getCertificateBytes()
        client_key_certificate  = self.getCertificateKeyBytes()
        certificate_signature   = getCertificateSignature(client_certificate)
        
        # Start pairing with server
        log_debug('Start pairing with server')
        pairing_result = self._perform_server_request('pair', False, {
            'devicename': 'ael', 
            'updateState': 1, 
            'phrase': 'getservercert', 
            'salt': binascii.hexlify(salt),
            'clientcert': binascii.hexlify(client_certificate)
            })

        if pairing_result is None:
            log_error('Failed to pair with server. No XML received.')
            return False

        isPaired = pairing_result.find('paired').text
        if isPaired != '1':
            log_error('Failed to pair with server. Server returned failed state.')
            return False

        server_cert_data = pairing_result.find('plaincert').text
        if server_cert_data is None:
            log_error('Failed to pair with server. A different pairing session might be in progress.')
            return False
        
        # Generate a random challenge and encrypt it with our AES key
        challenge = randomBytes(16)
        encrypted_challenge = aes_cypher.encryptToHex(challenge)
        
        # Send the encrypted challenge to the server
        log_debug('Sending encrypted challenge to the server')
        pairing_challenge_result = self._perform_server_request('pair', False, {
            'devicename': 'ael', 
            'updateState': 1, 
            'clientchallenge': encrypted_challenge })
        
        if pairing_challenge_result is None:
            log_error('Failed to pair with server. No XML received.')
            return False

        isPaired = pairing_challenge_result.find('paired').text
        if isPaired != '1':
            log_error('Failed to pair with server. Server returned failed state.')
            self._perform_server_request('unpair', False)
            return False
        
		# Decode the server's response and subsequent challenge
        log_debug('Decoding server\'s response and challenge response')
        server_challenge_hex = pairing_challenge_result.find('challengeresponse').text
        server_challenge_bytes = bytearray.fromhex(server_challenge_hex)
        server_challenge_decrypted = aes_cypher.decrypt(server_challenge_bytes)
        
        server_challenge_firstbytes = server_challenge_decrypted[:hashAlgorithm.digest_size()]
        server_challenge_lastbytes  = server_challenge_decrypted[hashAlgorithm.digest_size():hashAlgorithm.digest_size()+16]

        # Using another 16 bytes secret, compute a challenge response hash using the secret, our cert sig, and the challenge
        client_secret               = randomBytes(16)
        challenge_response          = server_challenge_lastbytes + certificate_signature + client_secret
        challenge_response_hashed   = hashAlgorithm.hash(challenge_response)
        challenge_response_encrypted= aes_cypher.encryptToHex(challenge_response_hashed)
        
        # Send the challenge response to the server
        log_debug('Sending the challenge response to the server')
        pairing_secret_response = self._perform_server_request('pair', False, {
            'devicename': 'ael', 
            'updateState': 1, 
            'serverchallengeresp': challenge_response_encrypted })
        
        if pairing_secret_response is None:
            log_error('Failed to pair with server. No XML received.')
            return False

        isPaired = pairing_secret_response.find('paired').text
        if isPaired != '1':
            log_error('Failed to pair with server. Server returned failed state.')
            self._perform_server_request('unpair', False)
            return False
        
        # Get the server's signed secret
        log_debug('Verifiying server signature')
        server_secret_response  = bytearray.fromhex(pairing_secret_response.find('pairingsecret').text)
        server_secret           = server_secret_response[:16]
        server_signature        = server_secret_response[16:272]
        
        server_cert = server_cert_data.decode('hex')
        is_verified = verify_signature(str(server_secret), server_signature, server_cert)

        if not is_verified:
            # Looks like a MITM, Cancel the pairing process
            log_error('Failed to verify signature. (MITM warning)')
            self._perform_server_request('unpair', False)
            return False

        # Ensure the server challenge matched what we expected (aka the PIN was correct)
        log_debug('Confirming PIN with entered value')
        server_cert_signature       = getCertificateSignature(server_cert)
        server_secret_combination   = challenge + server_cert_signature + server_secret
        server_secret_hashed        = hashAlgorithm.hash(server_secret_combination)
        
        if server_secret_hashed != server_challenge_firstbytes:
            # Probably got the wrong PIN
            log_error("Wrong PIN entered")
            self._perform_server_request('unpair', False)
            return False

        log_debug('Pin is confirmed')

        # Send the server our signed secret
        log_debug('Sending server our signed secret')
        signed_client_secret = sign_data(client_secret, client_key_certificate)
        client_pairing_secret = client_secret + signed_client_secret

        client_pairing_secret_response = self._perform_server_request('pair', False, {
            'devicename': 'ael', 
            'updateState': 1, 
            'clientpairingsecret':  binascii.hexlify(client_pairing_secret)})
        
        isPaired = client_pairing_secret_response.find('paired').text
        if isPaired != '1':
            log_error('Failed to pair with server. Server returned failed state.')
            self._perform_server_request('unpair', False)
            return False
        
        # Do the initial challenge over https
        log_debug('Initial challenge again')
        pair_challenge_response = self._perform_server_request('pair', True, {
            'devicename': 'ael', 
            'updateState': 1, 
            'phrase':  'pairchallenge'})
        
        isPaired = pair_challenge_response.find('paired').text
        if isPaired != '1':
            log_error('Failed to pair with server. Server returned failed state.')
            self._perform_server_request('unpair', False)
            return False

        return True

    def getApps(self):
        
        apps_response = self._perform_server_request('applist', True)
        appnodes = apps_response.findall('App')
        
        apps = []
        for appnode in appnodes:
            
            app = {}
            for appnode_attr in appnode:
                if len(list(appnode_attr)) > 1:
                    continue
                
                xml_text = appnode_attr.text if appnode_attr.text is not None else ''
                xml_text = text_unescape_XML(xml_text)
                xml_tag  = appnode_attr.tag
           
                app[xml_tag] = xml_text

            apps.append(app)

        return apps


    def getCertificateBytes(self):
        from utils_cryptography import *
        
        if self.pem_cert_data:
            return self.pem_cert_data

        if not self.certificate_file_path.exists():
            log_info('Client certificate file does not exist. Creating')
            create_self_signed_cert("NVIDIA GameStream Client", self.certificate_file_path, self.certificate_key_file_path)

        log_info('Loading client certificate data from {0}'.format(self.certificate_file_path.getOriginalPath()))
        self.pem_cert_data = self.certificate_file_path.readAll()

        return self.pem_cert_data
    
    def getCertificateKeyBytes(self):
        from utils_cryptography import *
        
        if self.key_cert_data:
            return self.key_cert_data

        if not self.certificate_key_file_path.exists():
            log_info('Client certificate file does not exist. Creating')
            create_self_signed_cert("NVIDIA GameStream Client", self.certificate_file_path, self.certificate_key_file_path)
        
        log_info('Loading client certificate data from {0}'.format(self.certificate_key_file_path.getOriginalPath()))
        self.key_cert_data = self.certificate_key_file_path.readAll()
        
        return self.key_cert_data
    
    def validate_certificates(self):
        
        if self.certificate_file_path.exists() and self.certificate_key_file_path.exists():
            log_debug('validate_certificates(): Certificate files exist. Done')
            return True

        certificate_files = self.certificates_path.scanFilesInPathAsFileNameObjects('*.crt')
        key_files = self.certificates_path.scanFilesInPathAsFileNameObjects('*.key')

        if len(certificate_files) < 1:
            log_warning('validate_certificates(): No .crt files found at given location.')
            return False

        if not self.certificate_file_path.exists():
            log_debug('validate_certificates(): Copying .crt file to nvidia.crt')
            certificate_files[0].copy(self.certificate_file_path)

        if len(key_files) < 1:
            log_warning('validate_certificates(): No .key files found at given location.')
            return False

        if not self.certificate_key_file_path.exists():
            log_debug('validate_certificates(): Copying .key file to nvidia.key')
            key_files[0].copy(certificate_key_file_path)

        return True

    @staticmethod
    def try_to_resolve_path_to_nvidia_certificates():

        home = expanduser("~")
        homePath = FileNameFactory.create(home)

        possiblePath = homePath.pjoin('Moonlight/')
        if possiblePath.exists():
            return possiblePath.getOriginalPath()

        possiblePath = homePath.pjoin('Limelight/')
        if possiblePath.exists():
            return possiblePath.getOriginalPath()
         
        return homePath.getOriginalPath()

# #################################################################################################
# #################################################################################################
# ROMsets
# #################################################################################################
# #################################################################################################

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# OBSOLETE FILE
# Will be removed soon.
class RomSetFactory():
    def __init__(self, pluginDataDir):
        self.ROMS_DIR                   = pluginDataDir.pjoin('db_ROMs')
        self.FAV_JSON_FILE_PATH         = pluginDataDir.pjoin('favourites.json')
        self.RECENT_PLAYED_FILE_PATH    = pluginDataDir.pjoin('history.json')
        self.MOST_PLAYED_FILE_PATH      = pluginDataDir.pjoin('most_played.json')
        self.COLLECTIONS_FILE_PATH      = pluginDataDir.pjoin('collections.xml')
        self.COLLECTIONS_DIR            = pluginDataDir.pjoin('db_Collections')
        self.VIRTUAL_CAT_TITLE_DIR      = pluginDataDir.pjoin('db_title')
        self.VIRTUAL_CAT_YEARS_DIR      = pluginDataDir.pjoin('db_years')
        self.VIRTUAL_CAT_GENRE_DIR      = pluginDataDir.pjoin('db_genre')
        self.VIRTUAL_CAT_DEVELOPER_DIR  = pluginDataDir.pjoin('db_developer')
        self.VIRTUAL_CAT_CATEGORY_DIR   = pluginDataDir.pjoin('db_category')
        self.VIRTUAL_CAT_NPLAYERS_DIR   = pluginDataDir.pjoin('db_nplayers')
        self.VIRTUAL_CAT_ESRB_DIR       = pluginDataDir.pjoin('db_esrb')
        self.VIRTUAL_CAT_RATING_DIR     = pluginDataDir.pjoin('db_rating')

        if not self.ROMS_DIR.exists():                  self.ROMS_DIR.makedirs()
        if not self.VIRTUAL_CAT_TITLE_DIR.exists():     self.VIRTUAL_CAT_TITLE_DIR.makedirs()
        if not self.VIRTUAL_CAT_YEARS_DIR.exists():     self.VIRTUAL_CAT_YEARS_DIR.makedirs()
        if not self.VIRTUAL_CAT_GENRE_DIR.exists():     self.VIRTUAL_CAT_GENRE_DIR.makedirs()
        if not self.VIRTUAL_CAT_DEVELOPER_DIR.exists(): self.VIRTUAL_CAT_DEVELOPER_DIR.makedirs()
        if not self.VIRTUAL_CAT_CATEGORY_DIR.exists():  self.VIRTUAL_CAT_CATEGORY_DIR.makedirs()
        if not self.VIRTUAL_CAT_NPLAYERS_DIR.exists():  self.VIRTUAL_CAT_NPLAYERS_DIR.makedirs()
        if not self.VIRTUAL_CAT_ESRB_DIR.exists():      self.VIRTUAL_CAT_ESRB_DIR.makedirs()
        if not self.VIRTUAL_CAT_RATING_DIR.exists():    self.VIRTUAL_CAT_RATING_DIR.makedirs()
        if not self.COLLECTIONS_DIR.exists():           self.COLLECTIONS_DIR.makedirs()

    def create(self, categoryID, launcher_data):
        
        launcherID = launcher_data['id']
        log_debug('romsetfactory.create(): categoryID={0}'.format(categoryID))
        log_debug('romsetfactory.create(): launcherID={0}'.format(launcherID))
        
        description = self.createDescription(categoryID)

        # --- ROM in Favourites ---
        if categoryID == VCATEGORY_FAVOURITES_ID and launcherID == VLAUNCHER_FAVOURITES_ID:
            return FavouritesRomSet(self.FAV_JSON_FILE_PATH, launcher_data, description)
                
        # --- ROM in Most played ROMs ---
        elif categoryID == VCATEGORY_MOST_PLAYED_ID and launcherID == VLAUNCHER_MOST_PLAYED_ID:
            return FavouritesRomSet(self.MOST_PLAYED_FILE_PATH, launcher_data, description)

        # --- ROM in Recently played ROMs list ---
        elif categoryID == VCATEGORY_RECENT_ID and launcherID == VLAUNCHER_RECENT_ID:
            return RecentlyPlayedRomSet(self.RECENT_PLAYED_FILE_PATH, launcher_data, description)

        # --- ROM in Collection ---
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            return CollectionRomSet(self.COLLECTIONS_FILE_PATH, launcher_data, self.COLLECTIONS_DIR, launcherID, description)

        # --- ROM in Virtual Launcher ---
        elif categoryID == VCATEGORY_TITLE_ID:
            log_info('RomSetFactory() loading ROM set Title Virtual Launcher ...')
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_TITLE_DIR, launcher_data, launcherID, description)
        elif categoryID == VCATEGORY_YEARS_ID:
            log_info('RomSetFactory() loading ROM set Years Virtual Launcher ...')
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_YEARS_DIR, launcher_data, launcherID, description)
        elif categoryID == VCATEGORY_GENRE_ID:
            log_info('RomSetFactory() loading ROM set Genre Virtual Launcher ...')
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_GENRE_DIR, launcher_data, launcherID, description)
        elif categoryID == VCATEGORY_DEVELOPER_ID:
            log_info('RomSetFactory() loading ROM set Studio Virtual Launcher ...')
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_DEVELOPER_DIR, launcher_data, launcherID, description)
        elif categoryID == VCATEGORY_NPLAYERS_ID:
            log_info('RomSetFactory() loading ROM set NPlayers Virtual Launcher ...')
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_NPLAYERS_DIR, launcher_data, launcherID, description)
        elif categoryID == VCATEGORY_ESRB_ID:
            log_info('RomSetFactory() loading ROM set ESRB Virtual Launcher ...')
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_ESRB_DIR, launcher_data, launcherID, description)
        elif categoryID == VCATEGORY_RATING_ID:
            log_info('RomSetFactory() loading ROM set Rating Virtual Launcher ...')
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_RATING_DIR, launcher_data, launcherID, description)
        elif categoryID == VCATEGORY_CATEGORY_ID:
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_CATEGORY_DIR, launcher_data, launcherID, description)
          
        elif categoryID == VCATEGORY_PCLONES_ID \
            and 'launcher_display_mode' in launcher_data \
            and launcher_data['launcher_display_mode'] != LAUNCHER_DMODE_FLAT:
            return PcloneRomSet(self.ROMS_DIR, launcher_data, description)
        
        log_info('RomSetFactory() loading standard romset...')
        return StandardRomSet(self.ROMS_DIR, launcher_data, description)

    def createDescription(self, categoryID):
        if categoryID == VCATEGORY_FAVOURITES_ID:
            return RomSetDescription('Favourite', 'Browse favourites')
        elif categoryID == VCATEGORY_MOST_PLAYED_ID:
            return RomSetDescription('Most Played ROM', 'Browse most played')
        elif categoryID == VCATEGORY_RECENT_ID:
            return RomSetDescription('Recently played ROM', 'Browse by recently played')
        elif categoryID == VCATEGORY_TITLE_ID:
            return RomSetDescription('Virtual Launcher Title', 'Browse by Title')
        elif categoryID == VCATEGORY_YEARS_ID:
            return RomSetDescription('Virtual Launcher Years', 'Browse by Year')
        elif categoryID == VCATEGORY_GENRE_ID:
            return RomSetDescription('Virtual Launcher Genre', 'Browse by Genre')
        elif categoryID == VCATEGORY_DEVELOPER_ID:
            return RomSetDescription('Virtual Launcher Studio','Browse by Studio')
        elif categoryID == VCATEGORY_NPLAYERS_ID:
            return RomSetDescription('Virtual Launcher NPlayers', 'Browse by Number of Players')
        elif categoryID == VCATEGORY_ESRB_ID:
            return RomSetDescription('Virtual Launcher ESRB', 'Browse by ESRB Rating')
        elif categoryID == VCATEGORY_RATING_ID:
            return RomSetDescription('Virtual Launcher Rating', 'Browse by User Rating')
        elif categoryID == VCATEGORY_CATEGORY_ID:
            return RomSetDescription('Virtual Launcher Category', 'Browse by Category')

       #if virtual_categoryID == VCATEGORY_TITLE_ID:
       #    vcategory_db_filename = VCAT_TITLE_FILE_PATH
       #    vcategory_name        = 'Browse by Title'
       #elif virtual_categoryID == VCATEGORY_YEARS_ID:
       #    vcategory_db_filename = VCAT_YEARS_FILE_PATH
       #    vcategory_name        = 'Browse by Year'
       #elif virtual_categoryID == VCATEGORY_GENRE_ID:
       #    vcategory_db_filename = VCAT_GENRE_FILE_PATH
       #    vcategory_name        = 'Browse by Genre'
       #elif virtual_categoryID == VCATEGORY_STUDIO_ID:
       #    vcategory_db_filename = VCAT_STUDIO_FILE_PATH
       #    vcategory_name        = 'Browse by Studio'
       #elif virtual_categoryID == VCATEGORY_NPLAYERS_ID:
       #    vcategory_db_filename = VCAT_NPLAYERS_FILE_PATH
       #    vcategory_name        = 'Browse by Number of Players'
       #elif virtual_categoryID == VCATEGORY_ESRB_ID:
       #    vcategory_db_filename = VCAT_ESRB_FILE_PATH
       #    vcategory_name        = 'Browse by ESRB Rating'
       #elif virtual_categoryID == VCATEGORY_RATING_ID:
       #    vcategory_db_filename = VCAT_RATING_FILE_PATH
       #    vcategory_name        = 'Browse by User Rating'
       #elif virtual_categoryID == VCATEGORY_CATEGORY_ID:
       #    vcategory_db_filename = VCAT_CATEGORY_FILE_PATH
       #    vcategory_name        = 'Browse by Category'

        return None

class RomSetDescription():
    def __init__(self, title, description, isRegularLauncher = False):
        
        self.title = title
        self.description = description

        self.isRegularLauncher = isRegularLauncher

class RomSet():
    __metaclass__ = abc.ABCMeta

    def __init__(self, romsDir, launcher, description):
        self.romsDir = romsDir
        self.launcher = launcher
        
        self.description = description

    @abc.abstractmethod
    def romSetFileExists(self):
        return False

    @abc.abstractmethod
    def loadRoms(self):
        return {}
    
    @abc.abstractmethod
    def loadRomsAsList(self):
        return []

    @abc.abstractmethod
    def loadRom(self, romId):
        return None

    @abc.abstractmethod
    def saveRoms(self, roms):
        pass

    @abc.abstractmethod
    def clear(self):
        pass

class StandardRomSet(RomSet):
    def __init__(self, romsDir, launcher, description):
        self.roms_base_noext = launcher['roms_base_noext'] if launcher is not None and 'roms_base_noext' in launcher else None
        self.view_mode = launcher['launcher_display_mode'] if launcher is not None and 'launcher_display_mode' in launcher else None

        if self.roms_base_noext is None:
            self.repositoryFile = romsDir
        elif self.view_mode == LAUNCHER_DMODE_FLAT:
            self.repositoryFile = romsDir.pjoin(self.roms_base_noext + '.json')
        else:
            self.repositoryFile = romsDir.pjoin(self.roms_base_noext + '_parents.json')

        super(StandardRomSet, self).__init__(romsDir, launcher, description)

    def romSetFileExists(self):
        return self.repositoryFile.exists()

    def loadRoms(self):

        if not self.romSetFileExists():
            log_warning('Launcher "{0}" JSON not found.'.format(self.roms_base_noext))
            return None

        log_info('StandardRomSet() Loading ROMs in Launcher ...')
        # was disk_IO.fs_load_ROMs_JSON()
        roms = {}
        # --- Parse using json module ---
        # >> On Github issue #8 a user had an empty JSON file for ROMs. This raises
        #    exception exceptions.ValueError and launcher cannot be deleted. Deal
        #    with this exception so at least launcher can be rescanned.
        log_verb('StandardRomSet.loadRoms() FILE  {0}'.format(self.repositoryFile.getOriginalPath()))
        try:
            roms = self.repositoryFile.readJson()
        except ValueError:
            statinfo = roms_json_file.stat()
            log_error('StandardRomSet.loadRoms() ValueError exception in json.load() function')
            log_error('StandardRomSet.loadRoms() Dir  {0}'.format(self.repositoryFile.getOriginalPath()))
            log_error('StandardRomSet.loadRoms() Size {0}'.format(statinfo.st_size))

        return roms

    def loadRomsAsList(self):
        roms_dict = self.loadRoms()

        if roms_dict is None:
            return None

        roms = []
        for key in roms_dict:
            roms.append(roms_dict[key])

        return roms

    def loadRom(self, romId):
        roms = self.loadRoms()

        if roms is None:
            log_error("StandardRomSet(): Could not load roms")
            return None

        romData = roms[romId]
        
        if romData is None:
            log_warning("StandardRomSet(): Rom with ID '{0}' not found".format(romId))
            return None

        return romData

    def saveRoms(self, roms):
        fs_write_ROMs_JSON(self.romsDir, self.launcher, roms)
        pass

    def clear(self):
        fs_unlink_ROMs_database(self.romsDir, self.launcher)

class PcloneRomSet(StandardRomSet):
    def __init__(self, romsDir, launcher, description):
        super(PcloneRomSet, self).__init__(romsDir, launcher, description)
        
        self.roms_base_noext = launcher['roms_base_noext'] if launcher is not None and 'roms_base_noext' in launcher else None
        self.repositoryFile = self.romsDir.pjoin(self.roms_base_noext + '_index_PClone.json')

class FavouritesRomSet(StandardRomSet):
    def loadRoms(self):
        log_info('FavouritesRomSet() Loading ROMs in Favourites ...')
        roms = fs_load_Favourites_JSON(self.repositoryFile)
        return roms

    def saveRoms(self, roms):
        log_info('FavouritesRomSet() Saving Favourites ROMs ...')
        fs_write_Favourites_JSON(self.repositoryFile, roms)

class VirtualLauncherRomSet(StandardRomSet):
    def __init__(self, romsDir, launcher, launcherID, description):
        self.launcherID = launcherID
        super(VirtualLauncherRomSet, self).__init__(romsDir, launcher, description)

    def romSetFileExists(self):
        hashed_db_filename = self.romsDir.pjoin(self.launcherID + '.json')
        return hashed_db_filename.exists()

    def loadRoms(self):
        if not self.romSetFileExists():
            log_warning('VirtualCategory "{0}" JSON not found.'.format(self.launcherID))
            return None

        log_info('VirtualCategoryRomSet() Loading ROMs in Virtual Launcher ...')
        roms = fs_load_VCategory_ROMs_JSON(self.romsDir, self.launcherID)
        return roms

    def saveRoms(self, roms):
        fs_write_Favourites_JSON(self.romsDir, roms)
        pass

class RecentlyPlayedRomSet(RomSet):
    def romSetFileExists(self):
        return self.romsDir.exists()

    def loadRoms(self):
        log_info('RecentlyPlayedRomSet() Loading ROMs in Recently Played ROMs ...')
        romsList = self.loadRomsAsList()

        roms = collections.OrderedDict()
        for rom in romsList:
            roms[rom['id']] = rom
            
        return roms

    def loadRomsAsList(self):
        roms = fs_load_Collection_ROMs_JSON(self.romsDir)
        return roms

    def loadRom(self, romId):
        roms = self.loadRomsAsList()

        if roms is None:
            log_error("RecentlyPlayedRomSet(): Could not load roms")
            return None
        
        current_ROM_position = fs_collection_ROM_index_by_romID(romId, roms)
        if current_ROM_position < 0:
            kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
            return None
            
        romData = roms[current_ROM_position]
        
        if romData is None:
            log_warning("RecentlyPlayedRomSet(): Rom with ID '{0}' not found".format(romId))
            return None

        return romData

    def saveRoms(self, roms):
        fs_write_Collection_ROMs_JSON(self.romsDir, roms)
        pass

    def clear(self):
        pass

class CollectionRomSet(RomSet):
    def __init__(self, romsDir, launcher, collection_dir, launcherID, description):
        self.collection_dir = collection_dir
        self.launcherID = launcherID
        super(CollectionRomSet, self).__init__(romsDir, launcher, description)

    def romSetFileExists(self):
        (collections, update_timestamp) = fs_load_Collection_index_XML(self.romsDir)
        collection = collections[self.launcherID]

        roms_json_file = self.romsDir.pjoin(collection['roms_base_noext'] + '.json')
        return roms_json_file.exists()

    def loadRomsAsList(self):
        (collections, update_timestamp) = fs_load_Collection_index_XML(self.romsDir)
        collection = collections[self.launcherID]
        roms_json_file = self.collection_dir.pjoin(collection['roms_base_noext'] + '.json')
        romsList = fs_load_Collection_ROMs_JSON(roms_json_file)
        return romsList
    
    # NOTE ROMs in a collection are stored as a list and ROMs in Favourites are stored as
    #      a dictionary. Convert the Collection list into an ordered dictionary and then
    #      converted back the ordered dictionary into a list before saving the collection.
    def loadRoms(self):
        log_info('CollectionRomSet() Loading ROMs in Collection ...')

        romsList = self.loadRomsAsList()
        
        roms = collections.OrderedDict()
        for rom in romsList:
            roms[rom['id']] = rom
            
        return roms

    def loadRom(self, romId):
        roms = self.loadRomsAsList()

        if roms is None:
            log_error("CollectionRomSet(): Could not load roms")
            return None

        current_ROM_position = fs_collection_ROM_index_by_romID(romId, roms)
        if current_ROM_position < 0:
            kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
            return
            
        romData = roms[current_ROM_position]
        
        if romData is None:
            log_warning("CollectionRomSet(): Rom with ID '{0}' not found".format(romId))
            return None

        return romData

    def saveRoms(self, roms):
        # >> Convert back the OrderedDict into a list and save Collection
        collection_rom_list = []
        for key in roms:
            collection_rom_list.append(roms[key])

        json_file_path = self.romsDir.pjoin(collection['roms_base_noext'] + '.json')
        fs_write_Collection_ROMs_JSON(json_file_path, collection_rom_list)

    def clear(self):
        pass
