# --- Python standard library ---
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod
import re, urllib, urllib2, json

# --- Kodi stuff ---
import xbmc, xbmcgui

# --- Modules/packages in this plugin ---
from constants import *
from assets import *
from scrap import *
from romsets import *
from scrapers import *
from reporting import *

from disk_IO import *
from utils import *
from utils_kodi import *
from filename import *

class RomScannersFactory():

    def __init__(self, settings, reports_dir, addon_dir):
        
        self.settings = settings
        self.reports_dir = reports_dir
        self.addon_dir = addon_dir

    def create(self, launcher, romset, scrapers):

        launcherType = launcher['type'] if 'type' in launcher else LAUNCHER_ROM
        log_info('RomScannersFactory: Creating romscanner for {}'.format(launcherType))

        if launcherType == LAUNCHER_STANDALONE:
            return NullScanner(launcher, self.settings)
        
        if launcherType == LAUNCHER_STEAM:
            return SteamScanner(self.reports_dir, self.addon_dir, launcher, romset, self.settings, scrapers)

        if launcherType == LAUNCHER_NVGAMESTREAM:
            return NvidiaStreamScanner(self.reports_dir, self.addon_dir, launcher, romset, self.settings, scrapers)
                
        return RomFolderScanner(self.reports_dir, self.addon_dir, launcher, romset, self.settings, scrapers)


class ScannerStrategy(ProgressDialogStrategy):
    __metaclass__ = ABCMeta
    
    def __init__(self, launcher, settings):
        self.launcher = launcher
        self.settings = settings

        super(ScannerStrategy, self).__init__()

    #
    # Scans for new roms based on the type of launcher.
    #
    @abstractmethod
    def scan(self):
        return {}

    #
    # Cleans up ROM collection.
    # Remove Remove dead/missing ROMs ROMs
    #
    @abstractmethod
    def cleanup(self):
        return {}

class NullScanner(ScannerStrategy):
    
    def scan(self):
        return {}

    def cleanup(self):
        return {}

class RomScannerStrategy(ScannerStrategy):
    __metaclass__ = ABCMeta
      
    def __init__(self, reports_dir, addon_dir, launcher, romset, settings, scrapers):
        
        self.reports_dir = reports_dir
        self.addon_dir = addon_dir
        self.romset = romset
        
        self.scrapers = scrapers

        super(RomScannerStrategy, self).__init__(launcher, settings)

    def scan(self):
        
        # --- Open ROM scanner report file ---
        launcher_report = FileReporter(self.reports_dir, self.launcher, LogReporter(self.launcher))
        launcher_report.open('RomScanner() Starting ROM scanner')

        # >> Check if there is an XML for this launcher. If so, load it.
        # >> If file does not exist or is empty then return an empty dictionary.
        launcher_report.write('Loading launcher ROMs ...')
        roms = self.romset.loadRoms()
        if roms is None:
            roms = {}
        
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
        for new_rom in new_roms:
            roms[new_rom['id']] = new_rom

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
        
        launcher_report = LogReporter(self.launcher)
        launcher_report.open('RomScanner() Starting Dead ROM cleaning')

        roms = self.romset.loadRoms()
        if roms is None:
            launcher_report.close()
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
    @abstractmethod
    def _getCandidates(self, launcher_report):
        return []

    # --- Remove dead entries -----------------------------------------------------------------
    @abstractmethod
    def _removeDeadRoms(self, candidates, roms):
        return 0

    # ~~~ Now go processing item by item ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @abstractmethod
    def _processFoundItems(self, items, roms, launcher_report):
        return []

class RomFolderScanner(RomScannerStrategy):
       
    # ~~~ Scan for new files (*.*) and put them in a list ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def _getCandidates(self, launcher_report):
        
        kodi_busydialog_ON()
        
        files = []
        launcher_path = FileNameFactory.create(self.launcher['rompath'])
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
            
        for key in sorted(roms.iterkeys()):
            log_debug('Searching {0}'.format(roms[key]['filename']))
            self._updateProgress(i * 100 / num_roms)
            i += 1
            fileName = FileNameFactory.create(roms[key]['filename'])
            if not fileName.exists():
                log_debug('Not found')
                log_debug('Deleting from DB {0}'.format(roms[key]['filename']))
                del roms[key]
                num_removed_roms += 1
            
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
        
        allowedExtensions = self.launcher['romext'].split("|")
        launcher_multidisc = self.launcher['multidisc']

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
                    temp_FN = FileNameFactory.create(new_rom['filename'])
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
                    MultiDisc_rom['disks'].append(MDSet.discName)
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
            for rom_id in roms:
                rpath = roms[rom_id]['filename'] 
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
            romdata             = fs_new_rom()
            romdata['id']       = misc_generate_random_SID()
            romdata['filename'] = ROM.getOriginalPath()
               
            searchTerm = text_format_ROM_name_for_scraping(ROM.getBase_noext())

            if self.scrapers:
                for scraper in self.scrapers:
                    self._updateProgressMessage(file_text, 'Scraping {0}...'.format(scraper.getName()))
                    scraper.scrape(searchTerm, ROM, romdata)
            
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
                romdata['disks'].append(MDSet.discName)
            
            new_roms.append(romdata)
            
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
        steamid = self.launcher['steamid']
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

        for key in sorted(roms.iterkeys()):
            rom = roms[key]
            romSteamId = rom['steamid']
            
            log_debug('Searching {0}'.format(romSteamId))
            self._updateProgress(i * 100 / num_roms)
            i += 1

            if romSteamId not in steamGameIds:
                log_debug('Not found. Deleting from DB {0}'.format(rom['m_name']))
                del roms[key]
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
        steamIdsAlreadyInCollection = set(roms[key]['steamid'] for key in roms)
        
        for steamGame in items:
            
            steamId = steamGame['appid']
            log_debug('Searching {} with #{}'.format(steamGame['name'], steamId))

            self._updateProgress(num_items_checked * 100 / num_games, steamGame['name'])
            
            if steamId not in steamIdsAlreadyInCollection:
                
                log_debug('========== Processing Steam game ==========')
                launcher_report.write('>>> title: {0}'.format(steamGame['name']))
                launcher_report.write('>>> ID: {0}'.format(steamGame['appid']))
        
                log_debug('Not found. Item {0} is new'.format(steamGame['name']))

                launcher_path = FileNameFactory.create(self.launcher['rompath'])
                romPath = launcher_path.pjoin('{0}.rom'.format(steamGame['appid']))

                # ~~~~~ Process new ROM and add to the list ~~~~~
                # --- Create new rom dictionary ---
                # >> Database always stores the original (non transformed/manipulated) path
                romdata  = fs_new_rom()
                romdata['id']           = misc_generate_random_SID()
                romdata['filename']     = romPath.getOriginalPath()
                romdata['steamid']      = steamGame['appid']
                romdata['steam_name']   = steamGame['name'] # so that we always have the original name
                romdata['m_name']       = steamGame['name']

                searchTerm = steamGame['name']
                
                if self.scrapers:
                    for scraper in self.scrapers:
                        self._updateProgressMessage(steamGame['name'], 'Scraping {0}...'.format(scraper.getName()))
                        scraper.scrape(searchTerm, romPath, romdata)
            
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
            
                new_roms.append(romdata)
                            
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
        from gamestream import *

        log_debug('Reading Nvidia GameStream server')
        self._startProgressPhase('Advanced Emulator Launcher', 'Reading Nvidia GameStream server...')

        server_host = self.launcher['server']
        assets_path = FileName(self.launcher['assets_path'])

        streamServer = GameStreamServer(server_host, assets_path)
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

        for key in sorted(roms.iterkeys()):
            rom = roms[key]
            romStreamId = rom['streamid']
            
            log_debug('Searching {0}'.format(romStreamId))
            self._updateProgress(i * 100 / num_roms)
            i += 1

            if romStreamId not in streamIds:
                log_debug('Not found. Deleting from DB {0}'.format(rom['m_name']))
                del roms[key]
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
        streamIdsAlreadyInCollection = set(roms[key]['streamid'] for key in roms)
        
        for streamableGame in items:
            
            streamId = streamableGame['ID']
            log_debug('Searching {} with #{}'.format(streamableGame['AppTitle'], streamId))

            self._updateProgress(num_items_checked * 100 / num_games, streamableGame['AppTitle'])
            
            if streamId not in streamIdsAlreadyInCollection:
                
                log_debug('========== Processing Nvidia Gamestream game ==========')
                launcher_report.write('>>> title: {0}'.format(streamableGame['AppTitle']))
                launcher_report.write('>>> ID: {0}'.format(streamableGame['ID']))
        
                log_debug('Not found. Item {0} is new'.format(streamableGame['AppTitle']))

                launcher_path = FileName(self.launcher['rompath'])
                romPath = launcher_path.pjoin('{0}.rom'.format(streamableGame['ID']))

                # ~~~~~ Process new ROM and add to the list ~~~~~
                # --- Create new rom dictionary ---
                # >> Database always stores the original (non transformed/manipulated) path
                romdata  = fs_new_rom()
                romdata['id']               = misc_generate_random_SID()
                romdata['filename']         = romPath.getOriginalPath()
                romdata['streamid']         = streamableGame['ID']
                romdata['gamestream_name']  = streamableGame['AppTitle'] # so that we always have the original name
                romdata['m_name']           = streamableGame['AppTitle']

                searchTerm = streamableGame['AppTitle']
                
                if self.scrapers:
                    for scraper in self.scrapers:
                        self._updateProgressMessage(streamableGame['name'], 'Scraping {0}...'.format(scraper.getName()))
                        scraper.scrape(searchTerm, romPath, romdata)
            
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
            
                new_roms.append(romdata)
                            
                # ~~~ Check if user pressed the cancel button ~~~
                if self._isProgressCanceled():
                    self._endProgressPhase()
                    kodi_dialog_OK('Stopping ROM scanning. No changes have been made.')
                    log_info('User pressed Cancel button when scanning ROMs. ROM scanning stopped.')
                    return None
            
                num_items_checked += 1

        self._endProgressPhase()    
        return new_roms  