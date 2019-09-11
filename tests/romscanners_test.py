import unittest, mock, os, sys
from mock import *
from fakes import *

from resources.main import *
from resources.objects import *
from resources.constants import *
from resources.utils import *

class Test_romscannerstests(unittest.TestCase):
    
    ROOT_DIR = ''
    TEST_DIR = ''
    TEST_ASSETS_DIR = ''

    @classmethod
    def setUpClass(cls):
        set_log_level(LOG_DEBUG)
        
        cls.TEST_DIR = os.path.dirname(os.path.abspath(__file__))
        cls.ROOT_DIR = os.path.abspath(os.path.join(cls.TEST_DIR, os.pardir))
        cls.TEST_ASSETS_DIR = os.path.abspath(os.path.join(cls.TEST_DIR,'assets/'))
                
        print('ROOT DIR: {}'.format(cls.ROOT_DIR))
        print('TEST DIR: {}'.format(cls.TEST_DIR))
        print('TEST ASSETS DIR: {}'.format(cls.TEST_ASSETS_DIR))
        print('---------------------------------------------------------------------------')

    def read_file(self, path):
        with open(path, 'r') as f:
            return f.read()

    def test_creating_new_scanner_gives_no_exceptions(self):
        
        # arrange
        settings = {}

        launcher = StandardRomLauncher(None, settings, None, None, None, None, None)
        launcher.set_platform('nintendo')

        target = RomScannersFactory(AEL_Paths(), settings)

        # act
        actual = target.create(launcher, None)

        # assert
        self.assertIsNotNone(actual)

    def test_when_creating_scanner_for_standalone_launcher_it_will_be_correct_type(self):
        
        # arrange
        settings = {}
        
        launcher = StandaloneLauncher(None, settings, None, None, None)
        launcher.set_platform('nintendo')

        expected = "NullScanner"

        target = RomScannersFactory(AEL_Paths(), settings)

        # act
        scanner = target.create(launcher, None)
        actual = scanner.__class__.__name__

        # assert
        self.assertEqual(actual, expected)
        
    def test_when_creating_scanner_for_rom_launcher_it_will_be_correct_type(self):
        
        # arrange
        settings = {}
        
        launcher = StandardRomLauncher(AEL_Paths(), settings, None, None, None, None, None)
        launcher.set_platform('nintendo')

        expected = "RomFolderScanner"

        target = RomScannersFactory(AEL_Paths(), settings)

        # act
        scanner = target.create(launcher, None)
        actual = scanner.__class__.__name__

        # assert
        self.assertEqual(actual, expected)
   
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
        settings['metadata_scraper_mode'] = 1
        settings['asset_scraper_mode'] = 1
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

    @patch('resources.utils.xbmcgui.DialogProgress.iscanceled')
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
        
        roms = {}
        roms_repo = FakeRomSetRepository(roms)

        launcher_data = self._getFakeLauncherMetaData(OBJ_LAUNCHER_ROM, 'Nintendo', 'zip')
        launcher_data['nointro_xml_file'] = None
        launcher = StandardRomLauncher(AEL_Paths(), settings, launcher_data, None, None, roms_repo, None)

        scraped_rom = {}
        scraped_rom['m_name'] = 'FakeScrapedRom'
        scrapers = [FakeScraper(settings, launcher, scraped_rom)]

        report_dir = FakeFile('//fake_reports/')
        addon_dir = FakeFile('//fake_addon/')
        
        target = RomFolderScanner(report_dir, addon_dir, launcher, settings, scrapers)
        
        # act
        target.scan()

        # assert
        print report_dir.getFakeContent()
        pass
    
    @patch('resources.utils.KodiFileName.exists', autospec=True)
    @patch('resources.utils.xbmcgui.DialogProgress.iscanceled')
    @patch('resources.utils.KodiFileName.recursiveScanFilesInPath')
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
                
        roms = {}
        roms['1']= ROM({'id': '1', 'm_name': 'this-one-will-be-deleted', 'filename': '//not-existing/byebye.zip'})
        roms['2']= ROM({'id': '2', 'm_name': 'this-one-will-be-deleted-too', 'filename': '//not-existing/byebye.zip'})
        roms['3']= ROM({'id': '3', 'm_name': 'Rocket League', 'filename': '//fake/folder/rocket.zip'})
        roms['4']= ROM({'id': '4', 'm_name': 'this-one-will-be-deleted-again', 'filename': '//not-existing/byebye.zip'})        
        roms_repo = FakeRomSetRepository(roms)
        
        launcher_data = self._getFakeLauncherMetaData(OBJ_LAUNCHER_ROM, 'Nintendo', 'zip')
        launcher_data['nointro_xml_file'] = None
        launcher = StandardRomLauncher(AEL_Paths(), settings, launcher_data, None, None, roms_repo, None)
        
        scraped_rom = {}
        scraped_rom['m_name'] = 'FakeScrapedRom'
        scrapers = [FakeScraper(settings, launcher, scraped_rom)]

        report_dir = FakeFile('//fake_reports/')
        addon_dir = FakeFile('//fake_addon/')
        
        target = RomFolderScanner(report_dir, addon_dir, launcher, settings, scrapers)
        
        expectedRomCount = 3

        # act
        actualRoms = target.scan()

        # assert
        self.assertIsNotNone(actualRoms)
        actualRomCount = len(actualRoms)

        self.assertEqual(expectedRomCount, actualRomCount)
        print report_dir.getFakeContent()
           
    @patch('resources.utils.KodiFileName.exists', autospec=True)
    @patch('resources.utils.xbmcgui.DialogProgress.iscanceled')
    @patch('resources.utils.KodiFileName.recursiveScanFilesInPath')
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
        
        roms = {}
        roms['1']= ROM({'id': '1', 'm_name': 'Rocket League', 'filename': '//fake/folder/rocket.zip'})
        roms_repo = FakeRomSetRepository(roms)

        launcher_data = self._getFakeLauncherMetaData(OBJ_LAUNCHER_ROM, 'Nintendo', 'zip')
        launcher_data['nointro_xml_file'] = None        
        launcher_data['multidisc'] = True
        launcher = StandardRomLauncher(AEL_Paths(), settings, launcher_data, None, None, roms_repo, None)
        
        scrapers = [FakeScraper(settings, launcher, None)]

        report_dir = FakeFile('//fake_reports/')
        addon_dir = FakeFile('//fake_addon/')
        
        target = RomFolderScanner(report_dir, addon_dir, launcher, settings, scrapers)
        
        expectedRomCount = 4

        # act
        actualRoms = target.scan()

        # assert
        self.assertIsNotNone(actualRoms)
        actualRomCount = len(actualRoms)

        i=0
        for rom in actualRoms:
            i+=1
            print '- {} ------------------------'.format(i)
            for key, value in rom.get_data().iteritems():
                print '[{}] {}'.format(key, value)

        self.assertEqual(expectedRomCount, actualRomCount)
    
    @patch('resources.utils.KodiFileName.exists', autospec=True)
    @patch('resources.utils.xbmcgui.DialogProgress.iscanceled')
    @patch('resources.utils.KodiFileName.recursiveScanFilesInPath')
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
        
        roms = {}
        roms['1']= ROM({'id': '1', 'm_name': 'Rocket League', 'filename': '//fake/folder/rocket.zip'})
        roms['2']= ROM({'id': '2', 'm_name': 'Zelda', 'filename': '//fake/folder/zelda.zip'})        
        roms['3']= ROM({'id': '3', 'm_name': 'Tetris', 'filename': '//fake/folder/tetris.zip'})        
        roms_repo = FakeRomSetRepository(roms)

        launcher_data = self._getFakeLauncherMetaData(OBJ_LAUNCHER_ROM, 'Nintendo', 'zip')
        launcher_data['nointro_xml_file'] = None
        launcher = StandardRomLauncher(AEL_Paths(), settings, launcher_data, None, None, roms_repo, None)
        
        scrapers = [FakeScraper(settings, launcher, None)]

        report_dir = FakeFile('//fake_reports/')
        addon_dir = FakeFile('//fake_addon/')
        
        target = RomFolderScanner(report_dir, addon_dir, launcher, settings, scrapers)
        
        expectedRomCount = 4

        # act
        actualRoms = target.scan()

        # assert
        self.assertIsNotNone(actualRoms)
        actualRomCount = len(actualRoms)

        i=0
        for rom in actualRoms:
            i+=1
            print '- {} ------------------------'.format(i)
            for key, value in rom.get_data().iteritems():
                print '[{}] {}'.format(key, value)

        self.assertEqual(expectedRomCount, actualRomCount)
        
    @patch('resources.utils.KodiFileName.exists', autospec=True)
    @patch('resources.utils.xbmcgui.DialogProgress.iscanceled')
    @patch('resources.utils.KodiFileName.recursiveScanFilesInPath')
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
        roms_repo = FakeRomSetRepository({})
                
        launcher_data = self._getFakeLauncherMetaData(OBJ_LAUNCHER_ROM, 'Nintendo', 'zip')
        launcher_data['nointro_xml_file'] = None
        launcher = StandardRomLauncher(AEL_Paths(), settings, launcher_data, None, None, roms_repo, None)
        
        scrapers = [FakeScraper(settings, launcher, None)]

        report_dir = FakeFile('//fake_reports/')
        addon_dir = FakeFile('//fake_addon/')
        
        target = RomFolderScanner(report_dir, addon_dir, launcher, settings, scrapers)
        
        expectedRomCount = 3

        # act
        actualRoms = target.scan()

        # assert
        self.assertIsNotNone(actualRoms)
        actualRomCount = len(actualRoms)

        i=0
        for rom in actualRoms:
            i+=1
            print '- {} ------------------------'.format(i)
            for key, value in rom.get_data().iteritems():
                print '[{}] {}'.format(key, value)

        self.assertEqual(expectedRomCount, actualRomCount)
        
    @patch('resources.utils.xbmcgui.DialogProgress.iscanceled')
    @patch('resources.objects.net_get_URL_original')
    def test_when_scanning_your_steam_account_not_existing_dead_roms_will_be_correctly_removed(self, mock_urlopen, progress_canceled_mock):

        # arrange
        mock_urlopen.return_value = self.read_file(self.TEST_ASSETS_DIR + "\\steamresponse.json")
        
        progress_canceled_mock.return_value = False

        settings = self._getFakeSettings()
        settings['steam-api-key'] = 'ABC123' #'BA1B6D6926F84920F8035F95B9B3E824'
        
        report_dir = FakeFile('//fake_reports/')
        addon_dir = FakeFile('//fake_addon/')

        roms = {}
        roms['1']= ROM({'id': '1', 'm_name': 'this-one-will-be-deleted', 'steamid': 99999})
        roms['2']= ROM({'id': '2', 'm_name': 'this-one-will-be-deleted-too', 'steamid': 777888444})
        roms['3']= ROM({'id': '3', 'm_name': 'Rocket League', 'steamid': 252950})
        roms['4']= ROM({'id': '4', 'm_name': 'this-one-will-be-deleted-again', 'steamid': 663434})        
        roms_repo = FakeRomSetRepository(roms)

        launcher_data = self._getFakeLauncherMetaData(OBJ_LAUNCHER_STEAM, 'Microsoft Windows', '')
        launcher_data['nointro_xml_file'] = None
        launcher_data['steamid'] = '09090909' #'76561198405030123' 
        launcher = SteamLauncher(launcher_data, settings, None, roms_repo, None)
        
        scraped_rom = {}
        scraped_rom['m_name'] = 'FakeScrapedRom'
        scrapers = [FakeScraper(settings, launcher, scraped_rom)]

        target = SteamScanner(report_dir, addon_dir, launcher, settings, scrapers)
        expectedRomCount = 5

        # act
        actualRoms = target.scan()

        # assert
        self.assertIsNotNone(actualRoms)
        actualRomCount = len(actualRoms)

        self.assertEqual(expectedRomCount, actualRomCount)

if __name__ == '__main__':    
    unittest.main()
