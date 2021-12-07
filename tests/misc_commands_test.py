import sys
import unittest, os
from unittest.mock import patch, MagicMock, Mock

import logging

import tests.fake_routing
import tests.fakes

module = type(sys)('routing')
module.Plugin = tests.fake_routing.Plugin
sys.modules['routing'] = module

from resources.lib.commands import misc_commands as target
from resources.lib import globals

from resources.lib.domain import AelAddon, Category, ROMCollection

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s %(module)s %(levelname)s: %(message)s',
                datefmt = '%m/%d/%Y %I:%M:%S %p', level = logging.INFO)

class Test_Misc_Commands(unittest.TestCase):
    
    ROOT_DIR = ''
    TEST_DIR = ''
    TEST_ASSETS_DIR = ''

    @classmethod
    def setUpClass(cls):        
        cls.TEST_DIR = os.path.dirname(os.path.abspath(__file__))
        cls.ROOT_DIR = os.path.abspath(os.path.join(cls.TEST_DIR, os.pardir))
        cls.TEST_ASSETS_DIR = os.path.abspath(os.path.join(cls.TEST_DIR,'assets/'))
                
        logger.info('ROOT DIR: {}'.format(cls.ROOT_DIR))
        logger.info('TEST DIR: {}'.format(cls.TEST_DIR))
        logger.info('TEST ASSETS DIR: {}'.format(cls.TEST_ASSETS_DIR))
        logger.info('---------------------------------------------------------------------------')  
        
        globals.g_PATHS = globals.AKL_Paths('plugin.tests')
        #globals.g_PATHS.DATABASE_FILE_PATH = dbPath

    @patch('resources.lib.commands.misc_commands.UnitOfWork', autospec=True)
    @patch('resources.lib.commands.misc_commands.AelAddonRepository.find_all_launchers', autospec=True)
    @patch('resources.lib.commands.misc_commands.ROMCollectionRepository.insert_romcollection', autospec=True)
    @patch('resources.lib.commands.misc_commands.AppMediator', autospec=True)
    @patch('resources.lib.commands.misc_commands.kodi.browse')
    def test_when_importing_launchers_from_xml_it_will_store_the_correct_amount_with_each_category(self,
        browse: MagicMock, 
        mediator: MagicMock,
        insert_mock: MagicMock,
        launchers_mock: MagicMock,
        repo: MagicMock):
                
        # arrange
        xml_path = self.TEST_ASSETS_DIR + "\\ms_categories.xml"
        browse.return_value = [xml_path]
        
        launchers_mock.return_value = [
            AelAddon({ 'id': 'ABC', 'addon_id': 'script.akl.defaults', 'name': 'TEST1' }),
            AelAddon({ 'id': 'DEF', 'addon_id': 'script.akl.retroarchlauncher', 'name': 'TEST2' })
        ]

        expected = 5
        expected_category_id = 'c20f56e7c2242b03e8133c512303ec63'

        # act
        target.cmd_execute_import_launchers(None)
        
        # assert
        method_calls = insert_mock.call_args_list
        self.assertIsNotNone(method_calls)
        
        actual = 0
        for index, args in enumerate(method_calls):
            collection:ROMCollection = args[0][1]
            category:Category = args[0][2]
            actual_category_id = category.get_id() if category else None
            logger.info("Collection#{} in Category#{}".format(collection.get_id(), actual_category_id))
            if actual_category_id == expected_category_id : actual = actual+1
        
        self.assertEqual(actual, expected)

        
    # def test_when_finding_categories_it_will_give_the_correct_result(self):
        
    #     # arrange
    #     xml_path = FakeFile(self.TEST_ASSETS_DIR + "\\ms_categories.xml")
    #     context = XmlDataContext(xml_path)
    #     target = CategoryRepository(context)

    #     expected = 7

    #     # act
    #     actual = target.find_all()
        
    #     # assert
    #     self.assertIsNotNone(actual)
    #     self.assertEqual(len(actual), expected)
        
    # def test_when_finding_one_specific_category_it_will_give_the_correct_result(self):
        
    #     # arrange
    #     xml_path = StandardFileName(self.TEST_ASSETS_DIR + "\\ms_categories.xml")
    #     context = XmlDataContext(xml_path)
    #     target = CategoryRepository(context)

    #     cat_id = 'c20f56e7c2242b03e8133c512303ec63'
    #     expected = 'Sega'

    #     # act
    #     actual = target.find(cat_id)
        
    #     # assert
    #     self.assertIsNotNone(actual)
    #     self.assertEqual(actual.get_name(), expected)

    # def test_when_listing_categories_it_will_give_correct_results(self):
        
    #     # arrange
    #     settings = self._get_test_settings()
        
    #     xml_path = FileName(self.TEST_ASSETS_DIR+ "\\ms_categories.xml")
    #     paths = Fake_Paths('\\fake\\')
    #     paths.CATEGORIES_FILE_PATH = xml_path
        
    #     target = ObjectRepository(paths, settings)
        
    #     expected = 7

    #     # act
    #     actual = target.find_category_all()
        
    #     # assert
    #     self.assertIsNotNone(actual)
    #     self.assertEqual(len(actual), expected)

    # @patch('resources.objects.FileName', side_effect = FileName)
    # def test_when_reading_rom_files_it_will_get_the_correct_collection(self, mock_file):

    #     # arrange
    #     settings = self._get_test_settings()
        
    #     rom_dir = FileName(self.TEST_ASSETS_DIR)
    #     paths = Fake_Paths('\\fake\\')
    #     paths.ROMS_DIR = rom_dir
        
    #     target = ROMCollectionRepository(paths, settings)
    #     launcher_data = { 'id': 'abc', 'roms_base_noext': 'roms_Sega_32X_518519' }
    #     launcher = StandardRomLauncher(paths, settings, launcher_data, None, None, target, None)
        
    #     expected = 35

    #     # act
    #     actual = target.load_ROMs(launcher)
        
    #     # assert
    #     self.assertIsNotNone(actual)
    #     self.assertEqual(len(actual), expected)
        
    # @patch('resources.objects.FileName', side_effect = FileName)
    # def test_when_reading_favourites_rom_files_it_will_get_the_correct_values(self, mock_file):

    #     # arrange
    #     settings = self._get_test_settings()
        
    #     rom_dir = FileName(self.TEST_ASSETS_DIR)
    #     paths = Fake_Paths('\\fake\\')
    #     paths.ROMS_DIR = rom_dir
        
    #     target = ROMCollectionRepository(paths, settings)
    #     launcher_data = { 'id': 'abc', 'roms_base_noext': 'favourites' }
    #     launcher = StandardRomLauncher(paths, settings, launcher_data, None, None, target, None)
        
    #     expected = 6

    #     # act
    #     actual = target.load_ROMs(launcher)
        
    #     # assert
    #     self.assertIsNotNone(actual)
    #     self.assertEqual(len(actual), expected)

    # def test_storing_roms_will_create_a_file_with_correct_contents(self):
        
    #     # arrange
    #     settings = self._get_test_settings()
        
    #     rom_dir = FakeFile(self.TEST_ASSETS_DIR)
    #     paths = Fake_Paths('\\fake\\')
    #     paths.ROMS_DIR = rom_dir
        
    #     target = ROMCollectionRepository(paths, settings)
    #     launcher_data = { 'id': 'abc', 'roms_base_noext': 'testcase' }
    #     launcher = StandardRomLauncher(paths, settings, launcher_data, None, None, target, None)
        
    #     roms = {}
    #     roms['1234'] = ROM()
    #     roms['9998'] = ROM()
    #     roms['7845'] = ROM()
        
    #     # act
    #     target.save_rom_set(launcher, roms)
                
    #     # assert
    #     print(rom_dir.getFakeContent())
