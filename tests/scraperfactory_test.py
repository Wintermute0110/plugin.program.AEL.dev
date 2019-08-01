import unittest, mock, os, sys

from mock import *
from mock import ANY
from tests.fakes import *
import xml.etree.ElementTree as ET

from resources.utils import *
from resources.scrap import *
from resources.objects import *
from resources.constants import *

class Test_scraperfactorytests(unittest.TestCase):
    
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

    def read_file_xml(self, path):
        data = self.read_file(path)
        root = ET.fromstring(data)
        return root

    def test_with_no_actual_scraperpaths_set_only_the_cleantitlescraper_will_be_loaded(self):
        
        # arrange
        settings = {}
        settings['scan_metadata_policy'] = 0
        settings['scan_asset_policy'] = 0
        settings['metadata_scraper_mode'] = 0
        settings['asset_scraper_mode'] = 0        
        settings['scan_clean_tags'] = True
        settings['escape_romfile'] = False
        settings['scraper_thegamesdb_apikey'] = '1234ABCDEFG'
        settings['scraper_mobygames_apikey'] = '1234ABCDEFG'
        settings['scraper_screenscraper_apikey'] = '1234ABCDEFG'
        settings['scraper_screenscraper_dev_id'] = '1234'
        settings['scraper_screenscraper_dev_pass'] = '1234'
        settings['scraper_screenscraper_AEL_softname'] = 'ael'
           
        paths = Fake_Paths('\\fake\\')
        paths.ROMS_DIR = FakeFile('')
        launcher = StandardRomLauncher(paths, settings, None, None, None, None, None)
        
        target = ScraperFactory(paths, settings)

        expected = 'CleanTitleScraper'

        # act
        actual = target.create_scanner(launcher)
        actual_name = actual.metadata_scraper.__class__.__name__

        # assert
        self.assertIsNotNone(actual)
        self.assertEqual(expected, actual_name)

    @patch('resources.scrap.misc_add_file_cache')
    def test_with_one_scraperpaths_set_two_scrapers_will_be_loaded_and_one_is_a_localfiles_scraper(self, mock_cache):
        
        # arrange
        settings = {}
        settings['scan_metadata_policy'] = 0
        settings['scan_asset_policy'] = 1
        settings['metadata_scraper_mode'] = 0
        settings['asset_scraper_mode'] = 0
        settings['scan_clean_tags'] = True
        settings['escape_romfile'] = False

        settings['scraper_title'] = 1 # TheGamesDB
        settings['scraper_thegamesdb_apikey'] = '1234ABCDEFG'
        settings['scraper_mobygames_apikey'] = '1234ABCDEFG'
        settings['scraper_screenscraper_apikey'] = '1234ABCDEFG'
        settings['scraper_screenscraper_dev_id'] = '1234'
        settings['scraper_screenscraper_dev_pass'] = '1234'
        settings['scraper_screenscraper_AEL_softname'] = 'ael'
        
        paths = Fake_Paths('\\fake\\')
        paths.ROMS_DIR = FakeFile('')
        launcher = StandardRomLauncher(paths, settings, None, None, None, None, None)
        
        launcher.set_platform('nintendo')
        launcher.set_custom_attribute('path_title', '//abc/a/b/c')
        
        target = ScraperFactory(paths, settings)
        expected = 'LocalAssetScraper'

        # act
        actual = target.create_scanner(launcher)
        actuals = actual.asset_scrapers
        
        # assert
        self.assertIsNotNone(actuals)
        self.assertEqual(2, len(actuals))
        
        actual_name = actuals[1].__class__.__name__
        self.assertEqual(expected, actual_name)

    def test_when_using_online_metadata_the_correct_scraper_will_be_loaded(self):
        
        # arrange
        settings = {}
        settings['scan_metadata_policy'] = 3 # OnlineScraper only
        settings['scan_asset_policy'] = 0
        settings['metadata_scraper_mode'] = 1
        settings['asset_scraper_mode'] = 0
        settings['scan_clean_tags'] = True
        settings['scan_ignore_scrap_title'] = False
        settings['scraper_metadata'] = 0 # NullScraper
        settings['escape_romfile'] = False
        settings['scraper_thegamesdb_apikey'] = '1234ABCDEFG'
        settings['scraper_mobygames_apikey'] = '1234ABCDEFG'
        settings['scraper_screenscraper_apikey'] = '1234ABCDEFG'
        settings['scraper_screenscraper_dev_id'] = '1234'
        settings['scraper_screenscraper_dev_pass'] = '1234'
        settings['scraper_screenscraper_AEL_softname'] = 'ael'
        
        paths = Fake_Paths('\\fake\\')
        paths.ROMS_DIR = FakeFile('')
        launcher = StandardRomLauncher(paths, settings, None, None, None, None, None)
        
        launcher.set_platform('nintendo')
        
        target = ScraperFactory(paths, settings)
        expected = 'OnlineMetadataScraper'

        # act
        strategy = target.create_scanner(launcher)
        actual = strategy.metadata_scraper

        # assert
        self.assertIsNotNone(actual)
        
        actual_name = actual.__class__.__name__
        self.assertEqual(expected, actual_name)

    def test_when_using_local_nfo_metadata_the_correct_scraper_will_be_loaded(self):
        
        # arrange
        settings = {}
        settings['scan_metadata_policy'] = 2 # NFO with Online as decorator
        settings['scan_asset_policy'] = 0
        settings['metadata_scraper_mode'] = 1
        settings['asset_scraper_mode'] = 0
        settings['scan_clean_tags'] = True
        settings['scan_ignore_scrap_title'] = False
        settings['scraper_metadata'] = 0 # NullScraper
        settings['escape_romfile'] = False
        settings['scraper_thegamesdb_apikey'] = '1234ABCDEFG'
        settings['scraper_mobygames_apikey'] = '1234ABCDEFG'
        settings['scraper_screenscraper_apikey'] = '1234ABCDEFG'
        settings['scraper_screenscraper_dev_id'] = '1234'
        settings['scraper_screenscraper_dev_pass'] = '1234'
        settings['scraper_screenscraper_AEL_softname'] = 'ael'
        
        paths = Fake_Paths('\\fake\\')
        paths.ROMS_DIR = FakeFile('')
        launcher = StandardRomLauncher(paths, settings, None, None, None, None, None)
        
        launcher.set_platform('dummy')
        
        target = ScraperFactory(paths, settings)
        expected = 'NfoScraper'

        # act
        strategy = target.create_scanner(launcher)
        actual = strategy.metadata_scraper

        # assert
        self.assertIsNotNone(actual)
        
        actual_name = actual.__class__.__name__
        self.assertEqual(expected, actual_name)
     
if __name__ == '__main__':
    unittest.main()
