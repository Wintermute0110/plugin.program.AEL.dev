import unittest, mock, os, sys
from mock import *
from fakes import *

from resources.launchers import *

from resources.utils import *
from resources.disk_IO import *
from resources.utils_kodi import *

from resources.constants import *

class Test_LauncherRepository(unittest.TestCase):
    
    ROOT_DIR = ''
    TEST_DIR = ''
    TEST_ASSETS_DIR = ''

    @classmethod
    def setUpClass(cls):
        set_use_print(True)
        set_log_level(LOG_DEBUG)
        
        cls.TEST_DIR = os.path.dirname(os.path.abspath(__file__))
        cls.ROOT_DIR = os.path.abspath(os.path.join(cls.TEST_DIR, os.pardir))
        cls.TEST_ASSETS_DIR = os.path.abspath(os.path.join(cls.TEST_DIR,'assets/'))
                
        print 'ROOT DIR: {}'.format(cls.ROOT_DIR)
        print 'TEST DIR: {}'.format(cls.TEST_DIR)
        print 'TEST ASSETS DIR: {}'.format(cls.TEST_ASSETS_DIR)
        print '---------------------------------------------------------------------------'
        
    def test_when_finding_launchers_by_category_it_will_give_the_correct_result(self):
        
        # arrange
        xml_path = StandardFileName(self.TEST_ASSETS_DIR + "\\ms_categories.xml")
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
        xml_path = StandardFileName(self.TEST_ASSETS_DIR + "\\ms_categories.xml")
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
        xml_path = StandardFileName(self.TEST_ASSETS_DIR + "\\ms_categories.xml")
        context = XmlDataContext(xml_path)
        target = CategoryRepository(context)
        
        expected = 7

        # act
        actual = target.get_simple_list()
        
        # assert
        self.assertIsNotNone(actual)
        self.assertEqual(len(actual), expected)

    def test_when_reading_rom_files_it_will_get_the_correct_collection(self):

        # arrange
        p = StandardFileName(self.TEST_ASSETS_DIR)
        
        target = RomSetRepository(p)
        l = { 'id': 'abc', 'roms_base_noext': 'roms_Sega_32X_518519' }
        launcher = StandardRomLauncher(l, None, None, None, None, False)
        
        expected = 35

        # act
        actual = target.find_by_launcher(launcher)
        
        # assert
        self.assertIsNotNone(actual)
        self.assertEqual(len(actual), expected)
        
    def test_when_reading_favourites_rom_files_it_will_get_the_correct_values(self):

        # arrange
        p = StandardFileName(self.TEST_ASSETS_DIR)
        
        target = RomSetRepository(p)
        l = { 'id': 'abc', 'roms_base_noext': 'favourites' }
        launcher = StandardRomLauncher(l, None, None, None, None, False)
        
        expected = 6

        # act
        actual = target.find_by_launcher(launcher)
        
        # assert
        self.assertIsNotNone(actual)
        self.assertEqual(len(actual), expected)

    def test_storing_roms_will_create_a_file_with_correct_contents(self):
        
        # arrange
        fake = FakeFile(self.TEST_ASSETS_DIR)
        
        target = RomSetRepository(fake)
        l = { 'id': 'abc', 'roms_base_noext': 'testcase' }
        launcher = StandardRomLauncher(l, None, None, None, None, False)

        roms = {}
        roms['1234'] = Rom()
        roms['9998'] = Rom()
        roms['7845'] = Rom()
        
        # act
        target.save_rom_set(launcher, roms)
                
        # assert
        print fake.getFakeContent()
