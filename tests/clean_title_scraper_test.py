import unittest, mock, os, sys, re

from mock import *
from mock import ANY
from fakes import FakeFile, FakeScraper
import xml.etree.ElementTree as ET

from resources.utils import *
from resources.net_IO import *
from resources.scrap import *
from resources.objects import *
from resources.constants import *        
        
class Test_clean_title_scraper(unittest.TestCase):
    
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


    def get_test_settings(self):
        settings = {}
        settings['scan_metadata_policy'] = 3 # OnlineScraper only
        settings['scan_asset_policy'] = 0
        settings['metadata_scraper_mode'] = 1
        settings['asset_scraper_mode'] = 1
        settings['scan_clean_tags'] = True
        settings['scan_ignore_scrap_title'] = False
        settings['scraper_metadata'] = 0 # NullScraper
        settings['mobygames_apikey'] = 'abc123'
        settings['escape_romfile'] = False

        return settings

    def test_scraping_metadata_for_game(self):
        
        # arrange
        settings = self.get_test_settings()
        fakeBase = 'castlevania [ROM] (test) v2'                
        target = CleanTitle(settings)
                
        # act
        candidates = target.get_candidates('castlevania x', fakeBase, 'Nintendo NES')
        actual = target.get_metadata(candidates[0])
                
        # assert
        self.assertTrue(actual)
        self.assertEqual(u'castlevania v2', actual['title'])
        print(actual)
        
    def test_scraping_assets_for_game(self):

        # arrange
        settings = self.get_test_settings()
        fakeBase = 'castlevania'
        
        assets_to_scrape = [
            g_assetFactory.get_asset_info(ASSET_BOXFRONT_ID), 
            g_assetFactory.get_asset_info(ASSET_BOXBACK_ID), 
            g_assetFactory.get_asset_info(ASSET_SNAP_ID)]
        
        target = CleanTitle(settings)

        # act
        candidates = target.get_candidates('castlevania x', fakeBase, 'Nintendo NES')        
        actuals = []
        for asset_to_scrape in assets_to_scrape:
            an_actual = target.get_assets(candidates[0], asset_to_scrape)
            actuals.append(an_actual)
                
        # assert
        for actual in actuals:
            self.assertFalse(actual)
        