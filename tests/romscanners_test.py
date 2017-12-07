import unittest

import mock
from mock import *
from fakes import *

from resources.romscanners import *
from resources.romsets import *
from resources.constants import *
from resources.utils_kodi import *

class Test_romscannerstests(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        set_use_print(True)
        set_log_level(LOG_DEBUG)

    def read_file(self, path):
        with open(path, 'r') as f:
            return f.read()

    def test_creating_new_scanner_gives_no_exceptions(self):
        
        # arrange
        settings = {}
        launcher = {}
        launcher['type'] = LAUNCHER_ROM
        launcher['platform'] = 'nintendo'
        romset = {}

        target = RomScannersFactory(settings, '', '')

        # act
        actual = target.create(launcher, romset, None)

        # assert
        self.assertIsNotNone(actual)

    def test_when_creating_scanner_for_standalone_launcher_it_will_be_correct_type(self):
        
        # arrange
        settings = {}
        launcher = {}
        launcher['type'] = LAUNCHER_STANDALONE
        launcher['platform'] = 'nintendo'
        romset = {}

        expected = "NullScanner"

        target = RomScannersFactory(settings, '', '')

        # act
        scanner = target.create(launcher, romset, None)
        actual = scanner.__class__.__name__

        # assert
        self.assertEqual(actual, expected)
        
    def test_when_creating_scanner_for_rom_launcher_it_will_be_correct_type(self):
        
        # arrange
        settings = {}
        launcher = {}
        launcher['type'] = LAUNCHER_ROM
        launcher['platform'] = 'nintendo'
        romset = {}

        expected = "RomFolderScanner"

        target = RomScannersFactory(settings, '', '')

        # act
        scanner = target.create(launcher, romset, None)
        actual = scanner.__class__.__name__

        # assert
        self.assertEqual(actual, expected)

    # Moved to scrapers      
    #def test_when_creating_scanner_for_rom_launcher_for_mame_platform_it_will_be_correct_type(self):
    #    
    #    # arrange
    #    settings = {}
    #    launcher = {}
    #    launcher['type'] = LAUNCHER_ROM
    #    launcher['platform'] = 'MAME'
    #    romset = {}
    #
    #    expected = "MameRomFolderScanner"
    #
    #    target = RomScannersFactory(settings, '', '')
    #
    #    # act
    #    scanner = target.create(launcher, romset, None)
    #    actual = scanner.__class__.__name__
    #
    #    # assert
    #    self.assertEqual(actual, expected)
    
    def _getFakeSettings(self):
        
        settings = {}
        settings['scraper_metadata'] = 0
        settings['scraper_title'] = 0
        settings['scraper_snap'] = 0
        settings['scraper_boxfront'] = 0
        settings['scraper_boxback'] = 0
        settings['scraper_cart'] = 0
        settings['scraper_fanart'] = 0
        settings['scraper_banner'] = 0
        settings['scraper_clearlogo'] = 0
        settings['scan_recursive'] = True
        settings['scan_ignore_bios'] = True
        
        return settings

    def _getFakeLauncherMetaData(self, type, platform, ext):
        
        launcher = {}
        launcher['type'] = type
        launcher['id'] = 'abc123def'
        launcher['m_name'] = 'test launcher'
        launcher['platform'] = platform
        launcher['rompath'] = '//fake/folder/'
        launcher['romext'] = ext
        launcher['roms_base_noext'] = 'roms_test_launcher'
        launcher['multidisc'] = False

        launcher['path_title'] = '//fake_title/'
        launcher['path_snap'] = '//fake_snap/'
        launcher['path_boxfront'] = '//fake_boxf/'
        launcher['path_boxback'] = '//fake_boxb/'
        launcher['path_cartridge'] = '//fake_cart/'
        launcher['path_fanart'] = '//fake_fan/'
        launcher['path_banner'] = '//fake_banner/'
        launcher['path_clearlogo'] = '//fake_clear/'
        launcher['path_flyer'] = '//fake_flyer/'
        launcher['path_map'] = '//fake_map/'
        launcher['path_manual'] = '//fake_manual/'
        launcher['path_manual'] = '//fake_manual/'
        launcher['path_trailer'] = '//fake_trailer/'

        return launcher

    @patch('resources.utils_kodi.xbmcgui.DialogProgress.iscanceled')
    @patch('resources.utils.FileName.recursiveScanFilesInPath')
    def test_when_scanning_with_a_normal_rom_scanner_it_will_go_without_exceptions(self, recursive_scan_mock, progress_canceled_mock):
        
        # arrange
        fake_files = [
           '//fake/folder/myfile.dot',
           '//fake/folder/donkey_kong.zip', 
           '//fake/folder/tetris.zip', 
           '//fake/folder/thumbs.db',
           '//fake/folder/duckhunt.zip']

        recursive_scan_mock.return_value = fake_files
        progress_canceled_mock.return_value = False

        settings = self._getFakeSettings()
        scraped_rom = {}
        scraped_rom['m_name'] = 'FakeScrapedRom'
        scrapers = [FakeScraper(scraped_rom)]
        
        launcher = self._getFakeLauncherMetaData(LAUNCHER_ROM, 'Nintendo', 'zip')
        launcher['nointro_xml_file'] = None

        roms = {}
        romset = FakeRomSet(None, roms)

        report_dir = FakeFile('//fake_reports/')
        addon_dir = FileName('//fake_addon/')
        
        target = RomFolderScanner(report_dir, addon_dir, launcher, romset, settings, scrapers)
        
        # act
        target.scan()

        # assert
        print report_dir.getFakeContent()
        pass
    
    @patch('resources.utils.FileName.exists', autospec=True)
    @patch('resources.utils_kodi.xbmcgui.DialogProgress.iscanceled')
    @patch('resources.utils.FileName.recursiveScanFilesInPath')
    def test_when_scanning_with_a_normal_rom_scanner_dead_roms_will_be_removed(self, recursive_scan_mock, progress_canceled_mock, file_exists_mock):
        
        # arrange
        fake_files = [
           '//fake/folder/myfile.dot',
           '//fake/folder/donkey_kong.zip', 
           '//fake/folder/tetris.zip']

        recursive_scan_mock.return_value = fake_files
        progress_canceled_mock.return_value = False
        file_exists_mock.side_effect = lambda f: f.getOriginalPath().startswith('//fake/')

        settings = self._getFakeSettings()
        scraped_rom = {}
        scraped_rom['m_name'] = 'FakeScrapedRom'
        scrapers = [FakeScraper(scraped_rom)]
        
        launcher = self._getFakeLauncherMetaData(LAUNCHER_ROM, 'Nintendo', 'zip')
        launcher['nointro_xml_file'] = None

        roms = {}
        roms['1']= {}
        roms['1']['m_name'] = 'this-one-will-be-deleted'
        roms['1']['filename'] = '//not-existing/byebye.zip'
        roms['2']= {}
        roms['2']['m_name'] = 'this-one-will-be-deleted-too'
        roms['2']['filename'] =  '//not-existing/byebye.zip'
        roms['3']= {}
        roms['3']['m_name'] = 'Rocket League'
        roms['3']['filename'] =  '//fake/folder/rocket.zip'
        roms['4']= {}
        roms['4']['m_name'] = 'this-one-will-be-deleted-again'
        roms['4']['filename'] = '//not-existing/byebye.zip'
        romset = FakeRomSet(None, roms)

        report_dir = FakeFile('//fake_reports/')
        addon_dir = FileName('//fake_addon/')
        
        target = RomFolderScanner(report_dir, addon_dir, launcher, romset, settings, scrapers)
        
        expectedRomCount = 3

        # act
        actualRoms = target.scan()

        # assert
        self.assertIsNotNone(actualRoms)
        actualRomCount = len(actualRoms)

        self.assertEqual(expectedRomCount, actualRomCount)
        print report_dir.getFakeContent()
           
    @patch('resources.utils.FileName.exists', autospec=True)
    @patch('resources.utils_kodi.xbmcgui.DialogProgress.iscanceled')
    @patch('resources.utils.FileName.recursiveScanFilesInPath')
    def test_when_scanning_with_a_normal_rom_scanner_multidiscs_will_be_put_together(self, recursive_scan_mock, progress_canceled_mock, file_exists_mock):
        
        # arrange
        fake_files = [
           '//fake/folder/zekda.zip',
           '//fake/folder/donkey kong (Disc 1 of 2).zip', 
           '//fake/folder/donkey kong (Disc 2 of 2).zip', 
           '//fake/folder/tetris.zip']

        recursive_scan_mock.return_value = fake_files
        progress_canceled_mock.return_value = False
        file_exists_mock.side_effect = lambda f: f.getOriginalPath().startswith('//fake/')

        settings = self._getFakeSettings()
        scrapers = [FakeScraper(None)]
        
        launcher = self._getFakeLauncherMetaData(LAUNCHER_ROM, 'Nintendo', 'zip')
        launcher['nointro_xml_file'] = None        
        launcher['multidisc'] = True

        roms = {}
        roms['1']= {}
        roms['1']['m_name'] = 'Rocket League'
        roms['1']['filename'] =  '//fake/folder/rocket.zip'
        romset = FakeRomSet(None, roms)

        report_dir = FakeFile('//fake_reports/')
        addon_dir = FileName('//fake_addon/')
        
        target = RomFolderScanner(report_dir, addon_dir, launcher, romset, settings, scrapers)
        
        expectedRomCount = 4

        # act
        actualRoms = target.scan()

        # assert
        self.assertIsNotNone(actualRoms)
        actualRomCount = len(actualRoms)

        i=0
        for x, rom in actualRoms.iteritems():
            i+=1
            print '- {} ------------------------'.format(i)
            for key, value in rom.iteritems():
                print '[{}] {}'.format(key, value)

        self.assertEqual(expectedRomCount, actualRomCount)
    
    @patch('resources.utils.FileName.exists', autospec=True)
    @patch('resources.utils_kodi.xbmcgui.DialogProgress.iscanceled')
    @patch('resources.utils.FileName.recursiveScanFilesInPath')
    def test_when_scanning_with_a_normal_rom_scanner_existing_items_wont_end_up_double(self, recursive_scan_mock, progress_canceled_mock, file_exists_mock):
        
        # arrange
        fake_files = [
           '//fake/folder/zelda.zip',
           '//fake/folder/donkey kong.zip', 
           '//fake/folder/tetris.zip']

        recursive_scan_mock.return_value = fake_files
        progress_canceled_mock.return_value = False
        file_exists_mock.side_effect = lambda f: f.getOriginalPath().startswith('//fake/')

        settings = self._getFakeSettings()
        scrapers = [FakeScraper(None)]
        
        launcher = self._getFakeLauncherMetaData(LAUNCHER_ROM, 'Nintendo', 'zip')
        launcher['nointro_xml_file'] = None

        roms = {}
        roms['1']= {}
        roms['1']['m_name'] = 'Rocket League'
        roms['1']['filename'] =  '//fake/folder/rocket.zip'
        roms['2']= {}
        roms['2']['m_name'] = 'Zelda'
        roms['2']['filename'] =  '//fake/folder/zelda.zip'
        roms['3']= {}
        roms['3']['m_name'] = 'Tetris'
        roms['3']['filename'] =  '//fake/folder/tetris.zip'
        romset = FakeRomSet(None, roms)

        report_dir = FakeFile('//fake_reports/')
        addon_dir = FileName('//fake_addon/')
        
        target = RomFolderScanner(report_dir, addon_dir, launcher, romset, settings, scrapers)
        
        expectedRomCount = 4

        # act
        actualRoms = target.scan()

        # assert
        self.assertIsNotNone(actualRoms)
        actualRomCount = len(actualRoms)

        i=0
        for x, rom in actualRoms.iteritems():
            i+=1
            print '- {} ------------------------'.format(i)
            for key, value in rom.iteritems():
                print '[{}] {}'.format(key, value)

        self.assertEqual(expectedRomCount, actualRomCount)
        
    @patch('resources.utils.FileName.exists', autospec=True)
    @patch('resources.utils_kodi.xbmcgui.DialogProgress.iscanceled')
    @patch('resources.utils.FileName.recursiveScanFilesInPath')
    def test_when_scanning_with_a_normal_rom_scanner_and_bios_roms_must_be_skipped_they_wont_be_added(self, recursive_scan_mock, progress_canceled_mock, file_exists_mock):
        
        # arrange
        fake_files = [
           '//fake/folder/zelda.zip',
           '//fake/folder/donkey kong.zip', 
           '//fake/folder/[BIOS] dinkytoy.zip', 
           '//fake/folder/tetris.zip']

        recursive_scan_mock.return_value = fake_files
        progress_canceled_mock.return_value = False
        file_exists_mock.side_effect = lambda f: f.getOriginalPath().startswith('//fake/')

        settings = self._getFakeSettings()
        scrapers = [FakeScraper(None)]
        
        launcher = self._getFakeLauncherMetaData(LAUNCHER_ROM, 'Nintendo', 'zip')
        launcher['nointro_xml_file'] = None

        roms = {}
        romset = FakeRomSet(None, roms)

        report_dir = FakeFile('//fake_reports/')
        addon_dir = FileName('//fake_addon/')
        
        target = RomFolderScanner(report_dir, addon_dir, launcher, romset, settings, scrapers)
        
        expectedRomCount = 3

        # act
        actualRoms = target.scan()

        # assert
        self.assertIsNotNone(actualRoms)
        actualRomCount = len(actualRoms)

        i=0
        for x, rom in actualRoms.iteritems():
            i+=1
            print '- {} ------------------------'.format(i)
            for key, value in rom.iteritems():
                print '[{}] {}'.format(key, value)

        self.assertEqual(expectedRomCount, actualRomCount)
        
    @patch('resources.utils_kodi.xbmcgui.DialogProgress.iscanceled')
    @patch('resources.romscanners.net_get_URL_original')
    def test_when_scanning_your_steam_account_not_existing_dead_roms_will_be_correctly_removed(self, mock_urlopen, progress_canceled_mock):

        # arrange
        test_file_dir = os.path.dirname(os.path.abspath(__file__))
        mock_urlopen.return_value = self.read_file(test_file_dir + "\\steamresponse.json")
        
        progress_canceled_mock.return_value = False

        settings = self._getFakeSettings()
        settings['steam-api-key'] = 'ABC123' #'BA1B6D6926F84920F8035F95B9B3E824'
        
        scraped_rom = {}
        scraped_rom['m_name'] = 'FakeScrapedRom'
        scrapers = [FakeScraper(scraped_rom)]

        report_dir = FakeFile('//fake_reports/')
        addon_dir = FileName('//fake_addon/')
        
        launcher = self._getFakeLauncherMetaData(LAUNCHER_STEAM, 'Microsoft Windows', '')
        launcher['nointro_xml_file'] = None
        launcher['steamid'] = '09090909' #'76561198405030123' 
        
        roms = {}
        roms['1']= {}
        roms['1']['m_name'] = 'this-one-will-be-deleted'
        roms['1']['steamid'] = 99999
        roms['2']= {}
        roms['2']['m_name'] = 'this-one-will-be-deleted-too'
        roms['2']['steamid'] = 777888444
        roms['3']= {}
        roms['3']['m_name'] = 'Rocket League'
        roms['3']['steamid'] = 252950
        roms['4']= {}
        roms['4']['m_name'] = 'this-one-will-be-deleted-again'
        roms['4']['steamid'] = 663434
        romset = FakeRomSet(None, roms)
        
        target = SteamScanner(report_dir, addon_dir, launcher, romset, settings, scrapers)
        expectedRomCount = 5

        # act
        actualRoms = target.scan()

        # assert
        self.assertIsNotNone(actualRoms)
        actualRomCount = len(actualRoms)

        self.assertEqual(expectedRomCount, actualRomCount)

if __name__ == '__main__':    
    unittest.main()
