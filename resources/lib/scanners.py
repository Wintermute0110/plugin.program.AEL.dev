# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Base ROM scanners
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
import logging

# --- AEL packages ---
from resources.lib.utils import io, kodi, text
from resources.lib import globals, report
from resources.lib.constants import *

logger = logging.getLogger(__name__)

# #################################################################################################
# #################################################################################################
# ROM scanners
# #################################################################################################
# #################################################################################################
class ScannerStrategyABC(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, launcher, settings, progress_dialog):
        self.launcher = launcher
        self.settings = settings
        self.progress_dialog = progress_dialog     
        super(ScannerStrategyABC, self).__init__()

    #
    # Configure this scanner.
    #
    @abc.abstractmethod
    def configure(self):
        return {}

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

class NullScanner(ScannerStrategyABC):
    def scan(self):
        return {}

    def cleanup(self):
        return {}

class RomScannerStrategy(ScannerStrategyABC):
    __metaclass__ = abc.ABCMeta

    def __init__(self, reports_dir, addon_dir, launcher, settings, scraping_strategy, progress_dialog):
        
        self.reports_dir = reports_dir
        self.addon_dir = addon_dir
           
        self.scraping_strategy = scraping_strategy

        super(RomScannerStrategy, self).__init__(launcher, settings, progress_dialog)



    def scan(self):
               
        # --- Open ROM scanner report file ---
        launcher_report = report.FileReporter(
            self.reports_dir, 
            self.launcher.get_data_dic(), 
            report.LogReporter(self.launcher.get_data_dic()))
        launcher_report.open('RomScanner() Starting ROM scanner')
        
        # >> Check if there is an XML for this launcher. If so, load it.
        # >> If file does not exist or is empty then return an empty dictionary.
        launcher_report.write('Loading launcher ROMs ...')
        roms = self.launcher.get_roms()

        if roms is None:
            roms = []
        
        num_roms = len(roms)
        launcher_report.write('{} ROMs currently in database'.format(num_roms))
        
        launcher_report.write('Collecting candidates ...')
        candidates = self._getCandidates(launcher_report)
        num_candidates = len(candidates)
        launcher_report.write('{} candidates found'.format(num_candidates))
        
        # --- Scan all files in extra ROM path ---------------------------------------------------
        if self.launcher.has_extra_rompath():
            logger.info('Scanning candidates in extra ROM path.')
            extra_candidates = self._getCandidates(launcher_report, self.launcher.get_extra_rompath())            
            logger.info('{} extra candidate files found'.format(len(extra_candidates)))
        else:
            logger.info('Extra ROM path empty. Skipping scanning.')
            extra_candidates = []

        launcher_report.write('Removing dead ROMs ...')
        num_removed_roms = self._removeDeadRoms(candidates, roms)        

        if num_removed_roms > 0:
            kodi.notify('{0} dead ROMs removed successfully'.format(num_removed_roms))
            logger.info('{0} dead ROMs removed successfully'.format(num_removed_roms))
        else:
            logger.info('No dead ROMs found')
        
        # --- Prepare list of candidates to be processed ----------------------------------------------
        # List has tuples (candidate, extra_ROM_flag). List already sorted alphabetically.
        candidates_combined = []
        for candidate in sorted(candidates): candidates_combined.append((candidate, False))
        for candidate in sorted(extra_candidates): candidates_combined.append((candidate, True))

        new_roms = self._processFoundItems(candidates_combined, roms, launcher_report)
        
        if not new_roms:
            return None

        num_new_roms = len(new_roms)
        roms = roms + new_roms

        launcher_report.write('******************** ROM scanner finished. Report ********************')
        launcher_report.write('Removed dead ROMs   {0:6d}'.format(num_removed_roms))
        launcher_report.write('Files checked       {0:6d}'.format(num_candidates))
        launcher_report.write('Extra files checked {0:6d}'.format(len(extra_candidates)))
        launcher_report.write('New added ROMs      {0:6d}'.format(num_new_roms))
        
        if len(roms) == 0:
            launcher_report.write('WARNING Launcher has no ROMs!')
            launcher_report.close()
            kodi.dialogger.OK('No ROMs found! Make sure launcher directory and file extensions are correct.')
            return None
        
        if num_new_roms == 0:
            kodi.notify('Added no new ROMs. Launcher has {0} ROMs'.format(len(roms)))
        else:
            kodi.notify('Added {0} new ROMs'.format(num_new_roms))

        # --- Close ROM scanner report file ---
        launcher_report.write('*** END of the ROM scanner report ***')
        launcher_report.close()

        return roms

    def cleanup(self):
        launcher_report = report.LogReporter(self.launcher.get_data_dic())
        launcher_report.open('RomScanner() Starting Dead ROM cleaning')
        logger.debug('RomScanner() Starting Dead ROM cleaning')

        roms = self.launcher.get_roms()
        if roms is None:
            launcher_report.close()
            logger.info('RomScanner() No roms available to cleanup')
            return {}
        
        num_roms = len(roms)
        launcher_report.write('{0} ROMs currently in database'.format(num_roms))
        
        launcher_report.write('Collecting candidates ...')
        candidates = self._getCandidates(launcher_report)
        num_candidates = len(candidates)
        logger.info('{0} candidates found'.format(num_candidates))

        launcher_report.write('Removing dead ROMs ...')
        num_removed_roms = self._removeDeadRoms(candidates, roms)        

        if num_removed_roms > 0:
            kodi.notify('{0} dead ROMs removed successfully'.format(num_removed_roms))
            logger.info('{0} dead ROMs removed successfully'.format(num_removed_roms))
        else:
            logger.info('No dead ROMs found')

        launcher_report.close()
        return roms

    # ~~~ Scan for new files (*.*) and put them in a list ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @abc.abstractmethod
    def _getCandidates(self, launcher_report, rom_path = None):
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
    def _getCandidates(self, launcher_report, rom_path = None):
        self.progress_dialog.startProgress('Scanning and caching files in ROM path ...')
        files = []
        
        if rom_path is None: rom_path = self.launcher.get_rom_path()
        launcher_report.write('Scanning files in {}'.format(rom_path.getPath()))

        if self.settings['scan_recursive']:
            logger.info('Recursive scan activated')
            files = rom_path.recursiveScanFilesInPath('*.*')
        else:
            logger.info('Recursive scan not activated')
            files = rom_path.scanFilesInPath('*.*')

        num_files = len(files)
        launcher_report.write('  File scanner found {} files'.format(num_files))
        self.progress_dialog.endProgress()
                
        return files

    # --- Remove dead entries -----------------------------------------------------------------
    def _removeDeadRoms(self, candidates, roms):
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
    def _processFoundItems(self, items, roms, launcher_report):

        num_items = len(items)    
        new_roms = []

        self.progress_dialog.startProgress('Scanning found items', num_items)
        logger.debug('============================== Processing ROMs ==============================')
        launcher_report.write('Processing files ...')
        num_items_checked = 0
        
        allowedExtensions = self.launcher.get_rom_extensions()
        launcher_multidisc = self.launcher.supports_multidisc()

        skip_if_scraping_failed = self.settings['scan_skip_on_scraping_failure']
        for ROM_file, extra_ROM_flag in sorted(items):
            self.progress_dialog.updateProgress(num_items_checked)
            
            # --- Get all file name combinations ---
            launcher_report.write('>>> {0}'.format(ROM_file.getPath()).encode('utf-8'))

            # ~~~ Update progress dialog ~~~
            file_text = 'ROM {0}'.format(ROM_file.getBase())
            self.progress_dialog.updateMessages(file_text, 'Checking if has ROM extension ...')
                        
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
            self.progress_dialog.updateMessages(file_text, 'Checking if ROM belongs to multidisc set..')
                       
            MultiDiscInROMs = False
            MDSet = text.get_multidisc_info(ROM_file)
            if MDSet.isMultiDisc and launcher_multidisc:
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
            elif MDSet.isMultiDisc and not launcher_multidisc:
                launcher_report.write('  ROM belongs to a multidisc set but Multidisc support is disabled.')
            else:
                launcher_report.write('  ROM does not belong to a multidisc set.')
 
            # --- Check that ROM is not already in the list of ROMs ---
            # >> If file already in ROM list skip it
            self.progress_dialog.updateMessages(file_text, 'Checking if ROM is not already in collection...')
            repeatedROM = False
            for rom in roms:
                rpath = rom.get_file() 
                if rpath == ROM_file: 
                    repeatedROM = True
        
            if repeatedROM:
                launcher_report.write('  File already into launcher ROM list. Skipping file.')
                continue
            else:
                launcher_report.write('  File not in launcher ROM list. Processing it ...')

            # --- Ignore BIOS ROMs ---
            # Name of bios is: '[BIOS] Rom name example (Rev A).zip'
            if self.settings['scan_ignore_bios']:
                BIOS_re = re.findall('\[BIOS\]', ROM_file.getBase())
                if len(BIOS_re) > 0:
                    logger.info("BIOS detected. Skipping ROM '{0}'".format(ROM_file.getPath()))
                    continue

            # ~~~~~ Process new ROM and add to the list ~~~~~
            # --- Create new rom dictionary ---
            # >> Database always stores the original (non transformed/manipulated) path
            new_rom = ROM()
            new_rom.set_file(ROM_file)
                        
            if extra_ROM_flag: new_rom.set_as_extra_ROM()
            
            # checksums
            ROM_checksums = ROM_file_original if MDSet.isMultiDisc and launcher_multidisc else ROM_file

            scraping_succeeded = True
            self.progress_dialog.updateMessages(file_text, 'Scraping {0}...'.format(ROM_file.getBaseNoExt()))
            try:
                self.scraping_strategy.scanner_process_ROM(new_rom, ROM_checksums)
            except Exception as ex:
                scraping_succeeded = False        
                logger.error('(Exception) Object type "{}"'.format(type(ex)))
                logger.error('(Exception) Message "{}"'.format(str(ex)))
                logger.warning('Could not scrape "{}"'.format(ROM_file.getBaseNoExt()))
                #logger.debug(traceback.format_exc())
            
            if not scraping_succeeded and skip_if_scraping_failed:
                kodi.display_user_message({
                    'dialog': KODI_MESSAGE_NOTIFY_WARN,
                    'msg': 'Scraping "{}" failed. Skipping.'.format(ROM_file.getBaseNoExt())
                })
            else:
                # --- This was the first ROM in a multidisc set ---
                if launcher_multidisc and MDSet.isMultiDisc and not MultiDiscInROMs:
                    logger.info('Adding to ROMs dic first disk "{0}"'.format(MDSet.discName))
                    new_rom.add_disk(MDSet.discName)
                
                new_roms.append(new_rom)
            
            # ~~~ Check if user pressed the cancel button ~~~
            if self.progress_dialog.isCanceled():
                self.progress_dialog.endProgress()
                kodi.dialogger.OK('Stopping ROM scanning. No changes have been made.')
                logger.info('User pressed Cancel button when scanning ROMs. ROM scanning stopped.')
                return None
            
            num_items_checked += 1
           
        self.progress_dialog.endProgress()
        return new_roms

class SteamScanner(RomScannerStrategy):
    
    # ~~~ Scan for new items not yet in the rom collection ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def _getCandidates(self, launcher_report, rom_path = None):
               
        logger.debug('Reading Steam account')
        self.progress_dialog.startProgress('Reading Steam account...')

        apikey = self.settings['steam-api-key']
        steamid = self.launcher.get_steam_id()
        url = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={}&steamid={}&include_appinfo=1'.format(apikey, steamid)
        
        self.progress_dialog.updateProgress(70)
        body = net_get_URL_original(url)
        self.progress_dialog.updateProgress(80)
        
        steamJson = json.loads(body)
        games = steamJson['response']['games']
        
        self.progress_dialog.endProgress()
        return games

    # --- Remove dead entries -----------------------------------------------------------------
    def _removeDeadRoms(self, candidates, roms):
    
        if roms is None or len(roms) == 0:
            logger.info('Launcher is empty. No dead ROM check.')
            return 0

        logger.debug('Starting dead items scan')
        num_roms = len(roms)
        num_removed_roms = 0
        i = 0
            
        self.progress_dialog.startProgress('Checking for dead ROMs ...', num_roms)
        
        steamGameIds = set(steamGame['appid'] for steamGame in candidates)

        for rom in reversed(roms):
            romSteamId = rom.get_custom_attribute('steamid')
            
            logger.debug('Searching {0}'.format(romSteamId))
            self.progress_dialog.updateProgress(i)
            i += 1

            if romSteamId not in steamGameIds:
                logger.debug('Not found. Deleting from DB: "{0}"'.format(rom.get_name()))
                roms.remove(rom)
                num_removed_roms += 1
            
        self.progress_dialog.endProgress()

        return num_removed_roms

    def _processFoundItems(self, items, roms, launcher_report):
        
        if items is None or len(items) == 0:
            logger.info('No steam games available.')
            return []

        new_roms = []

        num_games = len(items)
        num_items_checked = 0
            
        self.progress_dialog.startProgress('Checking for new ROMs ...', num_games)
        steamIdsAlreadyInCollection = set(rom.get_custom_attribute('steamid') for rom in roms)
        
        for steamGame, extra_ROM_flag in items:
            
            steamId = steamGame['appid']
            logger.debug('Searching {} with #{}'.format(steamGame['name'], steamId))
            self.progress_dialog.updateProgress(num_items_checked, steamGame['name'])
            
            if steamId not in steamIdsAlreadyInCollection:
                
                logger.debug('========== Processing Steam game ==========')
                launcher_report.write('>>> title: {}'.format(steamGame['name']))
                launcher_report.write('>>> ID: {}'.format(steamGame['appid']))
        
                logger.debug('Not found. Item {} is new'.format(steamGame['name']))

                launcher_path = self.launcher.get_rom_path()
                fake_file_name = text.str_to_filename_str(steamGame['name'])
                romPath = launcher_path.pjoin('{0}.rom'.format(fake_file_name))

                # ~~~~~ Process new ROM and add to the list ~~~~~
                # --- Create new rom dictionary ---
                # >> Database always stores the original (non transformed/manipulated) path
                new_rom  = ROM()
                new_rom.set_file(romPath)

                if extra_ROM_flag: new_rom.set_as_extra_ROM()
            
                new_rom.set_custom_attribute('steamid', steamGame['appid'])
                new_rom.set_custom_attribute('steam_name', steamGame['name'])  # so that we always have the original name
                new_rom.set_name(steamGame['name'])
        
                scraping_succeeded = True
                self.progress_dialog.updateMessages(steamGame['name'], 'Scraping {}...'.format(steamGame['name']))
                try:
                    self.scraping_strategy.scanner_process_ROM(new_rom, None)
                except Exception as ex:
                    scraping_succeeded = False        
                    logger.error('(Exception) Object type "{}"'.format(type(ex)))
                    logger.error('(Exception) Message "{}"'.format(str(ex)))
                    logger.warning('Could not scrape "{}"'.format(steamGame['name']))
                    #logger.debug(traceback.format_exc())
                
                if not scraping_succeeded and skip_if_scraping_failed:
                    kodi.display_user_message({
                        'dialog': KODI_MESSAGE_NOTIFY_WARN,
                        'msg': 'Scraping "{}" failed. Skipping.'.format(steamGame['name'])
                    })
                else:
                    new_roms.append(new_rom)
                            
                # ~~~ Check if user pressed the cancel button ~~~
                if self._isProgressCanceled():
                    self.progress_dialog.endProgress()
                    kodi.dialogger.OK('Stopping ROM scanning. No changes have been made.')
                    logger.info('User pressed Cancel button when scanning ROMs. ROM scanning stopped.')
                    return None
            
                num_items_checked += 1

        self.progress_dialog.endProgress()    
        return new_roms

class NvidiaStreamScanner(RomScannerStrategy):

    # ~~~ Scan for new items not yet in the rom collection ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def _getCandidates(self, launcher_report, rom_path = None):
        logger.debug('Reading Nvidia GameStream server')
        self.progress_dialog.startProgress('Reading Nvidia GameStream server...')

        server_host = self.launcher.get_server()
        certificates_path = self.launcher.get_certificates_path()

        streamServer = GameStreamServer(server_host, certificates_path, False)
        connected = streamServer.connect()

        if not connected:
            kodi.notify_error('Unable to connect to gamestream server')
            return None

        self.progress_dialog.updateProgress(50)
        games = streamServer.getApps()
                
        self.progress_dialog.endProgress()
        return games

    # --- Remove dead entries -----------------------------------------------------------------
    def _removeDeadRoms(self, candidates, roms):
    
        if roms is None or len(roms) == 0:
            logger.info('Launcher is empty. No dead ROM check.')
            return 0

        logger.debug('Starting dead items scan')
        num_roms = len(roms)
        num_removed_roms = 0
        i = 0
            
        self.progress_dialog.startProgress('Checking for dead ROMs ...', num_roms)
        
        streamIds = set(streamableGame['ID'] for streamableGame in candidates)

        for rom in reversed(roms):
            romStreamId = rom.get_custom_attribute('streamid')
            
            logger.debug('Searching {0}'.format(romStreamId))
            self.progress_dialog.updateProgress(i)
            i += 1

            if romStreamId not in streamIds:
                logger.debug('Not found. Deleting from DB {0}'.format(rom.get_name()))
                roms.remove(rom)
                num_removed_roms += 1
            
        self.progress_dialog.endProgress()

        return num_removed_roms

    def _processFoundItems(self, items, roms, launcher_report):
        if items is None or len(items) == 0:
            logger.info('No Nvidia Gamestream games available.')
            return []

        new_roms = []

        num_games = len(items)
        num_items_checked = 0
            
        self.progress_dialog.startProgress('Checking for new ROMs ...', num_games)
        streamIdsAlreadyInCollection = set(rom.get_custom_attribute('streamid') for rom in roms)
        skip_if_scraping_failed = self.settings['scan_skip_on_scraping_failure']
        
        for streamableGame, extra_ROM_flag in items:
            
            streamId = streamableGame['ID']
            logger.debug('Searching {} with #{}'.format(streamableGame['AppTitle'], streamId))

            self.progress_dialog.updateProgress(num_items_checked, streamableGame['AppTitle'])
            
            if streamId in streamIdsAlreadyInCollection:
                logger.debug('Game "{}" with #{} already in collection'.format(streamableGame['AppTitle'], streamId))
                continue
                
            logger.debug('========== Processing Nvidia Gamestream game ==========')
            launcher_report.write('>>> title: {0}'.format(streamableGame['AppTitle']))
            launcher_report.write('>>> ID: {0}'.format(streamableGame['ID']))
    
            logger.debug('Not found. Item {0} is new'.format(streamableGame['AppTitle']))

            launcher_path = self.launcher.get_rom_path()
            fake_file_name = text.str_to_filename_str(streamableGame['AppTitle'])
            romPath = launcher_path.pjoin('{0}.rom'.format(fake_file_name))

            # ~~~~~ Process new ROM and add to the list ~~~~~
            # --- Create new rom dictionary ---
            # >> Database always stores the original (non transformed/manipulated) path
            new_rom  = ROM()
            new_rom.set_file(romPath)

            if extra_ROM_flag: new_rom.set_as_extra_ROM()
            
            new_rom.set_custom_attribute('streamid',        streamableGame['ID'])
            new_rom.set_custom_attribute('gamestream_name', streamableGame['AppTitle'])  # so that we always have the original name
            new_rom.set_name(streamableGame['AppTitle'])
            
            scraping_succeeded = True
            self.progress_dialog.updateMessages(streamableGame['AppTitle'], 'Scraping {0}...'.format(streamableGame['AppTitle']))
            try:
                self.scraping_strategy.scanner_process_ROM(new_rom, None)
            except Exception as ex:
                scraping_succeeded = False        
                logger.error('(Exception) Object type "{}"'.format(type(ex)))
                logger.error('(Exception) Message "{}"'.format(str(ex)))
                logger.warning('Could not scrape "{}"'.format(streamableGame['AppTitle']))
                #logger.debug(traceback.format_exc())
            
            if not scraping_succeeded and skip_if_scraping_failed:
                kodi.display_user_message({
                    'dialog': KODI_MESSAGE_NOTIFY_WARN,
                    'msg': 'Scraping "{}" failed. Skipping.'.format(streamableGame['AppTitle'])
                })
            else:
                new_roms.append(new_rom)
                
            # ~~~ Check if user pressed the cancel button ~~~
            if self.progress_dialog.isCanceled():
                self.progress_dialog.endProgress()
                kodi.dialogger.OK('Stopping ROM scanning. No changes have been made.')
                logger.info('User pressed Cancel button when scanning ROMs. ROM scanning stopped.')
                return None
            
            num_items_checked += 1

        self.progress_dialog.endProgress()
        return new_roms
    