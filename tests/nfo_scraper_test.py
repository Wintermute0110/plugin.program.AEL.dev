import unittest, mock, os, sys, re

from mock import *
from mock import ANY
from tests.fakes import FakeFile
import xml.etree.ElementTree as ET

from resources.net_IO import *
from resources.scrap import *
from resources.utils import FileName
from resources.objects import StandardRomLauncher
from resources.constants import *
        
FileName = FakeFile

class Test_nfo_scraper(unittest.TestCase):
    
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
        
        launcher = StandardRomLauncher(None, settings, None, None, None, None, None)
        launcher.set_platform('Nintendo SNES')
        
        rom = ROM({'id': 1234})
        fakeRomPath = FakeFile(Test_nfo_scraper.TEST_ASSETS_DIR + '\\dr_mario.zip')
        with open(Test_nfo_scraper.TEST_ASSETS_DIR + "\\dr_mario.nfo", 'r') as f:
            fakeRomPath.setFakeContent(f.read())

        target = NfoScraper(settings, launcher)

        # act
        actual = target.scrape_metadata('doctor mario', fakeRomPath, rom)
                
        # assert
        self.assertTrue(actual)
        self.assertEqual(u'Dr. Mario', rom.get_name())
        self.assertEqual(u'Puzzle', rom.get_genre())
        print(rom)

    def test_scraping_assets_for_game(self):

        # arrange
        settings = self.get_test_settings()
        
        assets_to_scrape = [
            g_assetFactory.get_asset_info(ASSET_BOXFRONT_ID), 
            g_assetFactory.get_asset_info(ASSET_BOXBACK_ID), 
            g_assetFactory.get_asset_info(ASSET_SNAP_ID)]
        
        launcher = StandardRomLauncher(None, settings, None, None, None, None, None)
        launcher.set_platform('Nintendo SNES')
        launcher.set_asset_path(g_assetFactory.get_asset_info(ASSET_BOXFRONT_ID),'/my/nice/assets/front/')
        launcher.set_asset_path(g_assetFactory.get_asset_info(ASSET_BOXBACK_ID),'/my/nice/assets/back/')
        launcher.set_asset_path(g_assetFactory.get_asset_info(ASSET_SNAP_ID),'/my/nice/assets/snaps/')
        
        rom = ROM({'id': 1234})
        fakeRomPath = FakeFile('/my/nice/roms/castlevania.zip')
        
        target = NfoScraper(settings, launcher)

        # act
        actuals = []
        for asset_to_scrape in assets_to_scrape:
            an_actual = target.scrape_asset('castlevania', asset_to_scrape, fakeRomPath, rom)
            actuals.append(an_actual)
                
        # assert
        for actual in actuals:
            self.assertFalse(actual)
        
        print(rom)