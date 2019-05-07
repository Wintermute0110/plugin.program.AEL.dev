import unittest, mock, os, sys
from mock import *

from resources.objects import *
from resources.disk_IO import *
from resources.constants import *

from tests.fakes import FakeFile, Fake_Paths

class Test_LauncherRepository(unittest.TestCase):
    
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
        
    def _get_test_settings(self):
        
        settings = {}
        settings['lirc_state'] = True
        settings['escape_romfile'] = True
        settings['display_launcher_notify'] = False
        settings['media_state_action'] = 0
        settings['suspend_audio_engine'] = False
        settings['delay_tempo'] = 1
        return settings

    def test_when_finding_launchers_by_category_it_will_give_the_correct_result(self):
        
        # arrange
        xml_path = FakeFile(self.TEST_ASSETS_DIR + "\\ms_categories.xml")
        context = XmlDataContext(xml_path)
        factory = LauncherFactory( {}, None, FakeFile(self.TEST_ASSETS_DIR))
        target = LauncherRepository(context, factory)

        expected = 5
        cat_id = 'c20f56e7c2242b03e8133c512303ec63'

        # act
        actual = target.find_by_category(cat_id)
        
        # assert
        self.assertIsNotNone(actual)
        self.assertEqual(len(actual), expected)

        
    def test_when_finding_categories_it_will_give_the_correct_result(self):
        
        # arrange
        xml_path = FakeFile(self.TEST_ASSETS_DIR + "\\ms_categories.xml")
        context = XmlDataContext(xml_path)
        target = CategoryRepository(context)

        expected = 7

        # act
        actual = target.find_all()
        
        # assert
        self.assertIsNotNone(actual)
        self.assertEqual(len(actual), expected)
        
    def test_when_finding_one_specific_category_it_will_give_the_correct_result(self):
        
        # arrange
        xml_path = StandardFileName(self.TEST_ASSETS_DIR + "\\ms_categories.xml")
        context = XmlDataContext(xml_path)
        target = CategoryRepository(context)

        cat_id = 'c20f56e7c2242b03e8133c512303ec63'
        expected = 'Sega'

        # act
        actual = target.find(cat_id)
        
        # assert
        self.assertIsNotNone(actual)
        self.assertEqual(actual.get_name(), expected)

    def test_when_listing_categories_it_will_give_correct_results(self):
        
        # arrange
        settings = self._get_test_settings()
        
        xml_path = PythonFileName(self.TEST_ASSETS_DIR+ "\\ms_categories.xml")
        paths = Fake_Paths('\\fake\\')
        paths.CATEGORIES_FILE_PATH = xml_path
        
        target = ObjectRepository(paths, settings)
        
        expected = 7

        # act
        actual = target.find_category_all()
        
        # assert
        self.assertIsNotNone(actual)
        self.assertEqual(len(actual), expected)

    @patch('resources.objects.FileName', side_effect = PythonFileName)
    def test_when_reading_rom_files_it_will_get_the_correct_collection(self, mock_file):

        # arrange
        settings = self._get_test_settings()
        
        rom_dir = PythonFileName(self.TEST_ASSETS_DIR)
        paths = Fake_Paths('\\fake\\')
        paths.ROMS_DIR = rom_dir
        
        target = ROMSetRepository(paths, settings)
        launcher_data = { 'id': 'abc', 'roms_base_noext': 'roms_Sega_32X_518519' }
        launcher = StandardRomLauncher(paths, settings, launcher_data, None, None, target, None)
        
        expected = 35

        # act
        actual = target.load_ROMs(launcher)
        
        # assert
        self.assertIsNotNone(actual)
        self.assertEqual(len(actual), expected)
        
    @patch('resources.objects.FileName', side_effect = PythonFileName)
    def test_when_reading_favourites_rom_files_it_will_get_the_correct_values(self, mock_file):

        # arrange
        settings = self._get_test_settings()
        
        rom_dir = PythonFileName(self.TEST_ASSETS_DIR)
        paths = Fake_Paths('\\fake\\')
        paths.ROMS_DIR = rom_dir
        
        target = ROMSetRepository(paths, settings)
        launcher_data = { 'id': 'abc', 'roms_base_noext': 'favourites' }
        launcher = StandardRomLauncher(paths, settings, launcher_data, None, None, target, None)
        
        expected = 6

        # act
        actual = target.load_ROMs(launcher)
        
        # assert
        self.assertIsNotNone(actual)
        self.assertEqual(len(actual), expected)

    def test_storing_roms_will_create_a_file_with_correct_contents(self):
        
        # arrange
        settings = self._get_test_settings()
        
        rom_dir = FakeFile(self.TEST_ASSETS_DIR)
        paths = Fake_Paths('\\fake\\')
        paths.ROMS_DIR = rom_dir
        
        target = ROMSetRepository(paths, settings)
        launcher_data = { 'id': 'abc', 'roms_base_noext': 'testcase' }
        launcher = StandardRomLauncher(paths, settings, launcher_data, None, None, target, None)
        
        roms = {}
        roms['1234'] = ROM()
        roms['9998'] = ROM()
        roms['7845'] = ROM()
        
        # act
        target.save_rom_set(launcher, roms)
                
        # assert
        print(rom_dir.getFakeContent())
