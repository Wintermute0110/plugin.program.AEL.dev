import unittest, mock, os, sys

from mock import *
from mock import ANY
from fakes import *
import xml.etree.ElementTree as ET

from resources.utils import *
from resources.net_IO import *
from resources.scrap import *
from resources.objects import *
from resources.constants import *        
        
def read_file(path):
    with open(path, 'r') as f:
        return f.read()


class Test_gamefaq_scraper(unittest.TestCase):
    
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

    def mocked_gamesfaq(url, params = None):

        mocked_html_file = '';

        if '/search' in url:
            mocked_html_file = Test_gamefaq_scraper.TEST_ASSETS_DIR + "\\gamesfaq_search.html"
            
        elif '/578318-castlevania/images/21' in url:
            mocked_html_file = Test_gamefaq_scraper.TEST_ASSETS_DIR + "\\gamesfaq_castlevania_snap.html"
            
        elif '/578318-castlevania/images/135454' in url:
            mocked_html_file = Test_gamefaq_scraper.TEST_ASSETS_DIR + "\\gamesfaq_castlevania_boxfront.html"

        elif '/578318-castlevania/images' in url:
            mocked_html_file = Test_gamefaq_scraper.TEST_ASSETS_DIR + "\\gamesfaq_castlevania_images.html"
            
        elif '/578318-castlevania' in url:
            mocked_html_file = Test_gamefaq_scraper.TEST_ASSETS_DIR + "\\gamesfaq_castlevania.html"

        elif '.jpg' in url:
            print 'reading fake image file'
            return read_file(Test_gamesdb_scraper.TEST_ASSETS_DIR + "\\test.jpg")

        if mocked_html_file == '':
            return net_get_URL_oneline(url)

        print 'reading mocked data from file: {}'.format(mocked_html_file)
        return read_file(mocked_html_file)

    def get_test_settings(self):
        settings = {}
        settings['scan_metadata_policy'] = 3 # OnlineScraper only
        settings['scan_asset_policy'] = 0
        settings['metadata_scraper_mode'] = 1
        settings['asset_scraper_mode'] = 1
        settings['scan_clean_tags'] = True
        settings['scan_ignore_scrap_title'] = False
        settings['scraper_metadata'] = 0 # NullScraper
        settings['thegamesdb_apikey'] = 'abc123'
        settings['escape_romfile'] = False

        return settings


    @patch('resources.scrap.net_get_URL_oneline', side_effect = mocked_gamesfaq)
    @patch('resources.scrap.net_post_URL_original', side_effect = mocked_gamesfaq)
    def test_scraping_metadata_for_game(self, mock_htmlpost_downloader, mock_html_downloader):
        
        # arrange
        settings = self.get_test_settings()
        
        launcher = StandardRomLauncher(None, settings, None, None, None, None, None)
        launcher.set_platform('Nintendo NES')
    
        rom = ROM({'id': 1234})
        fakeRomPath = FakeFile('/my/nice/roms/castlevania.zip')

        target = GameFaqScraper(settings, launcher)

        # act
        actual = target.scrape_metadata('castlevania', fakeRomPath, rom)
                
        # assert
        self.assertTrue(actual)
        self.assertEqual(u'Castlevania', rom.get_name())
        print rom        

    @patch('resources.scrap.net_get_URL_oneline', side_effect = mocked_gamesfaq)
    @patch('resources.scrap.net_post_URL_original', side_effect = mocked_gamesfaq)
    @patch('resources.scrap.net_download_img')
    def test_scraping_assets_for_game(self, mock_img_downloader, mock_htmlpost_downloader, mock_html_downloader):

        # arrange
        settings = self.get_test_settings()
        
        assets_to_scrape = [g_assetFactory.get_asset_info(ASSET_BOXFRONT_ID), g_assetFactory.get_asset_info(ASSET_SNAP_ID)]
        
        launcher = StandardRomLauncher(None, settings, None, None, None, None, None)
        launcher.set_platform('Nintendo NES')
        launcher.set_asset_path(g_assetFactory.get_asset_info(ASSET_BOXFRONT_ID),'/my/nice/assets/fronts/')
        launcher.set_asset_path(g_assetFactory.get_asset_info(ASSET_SNAP_ID),'/my/nice/assets/snaps/')
        
        rom = ROM({'id': 1234})
        fakeRomPath = FakeFile('/my/nice/roms/castlevania.zip')
        
        target = GameFaqScraper(settings, launcher)

        # act
        actuals = []
        for asset_to_scrape in assets_to_scrape:
            an_actual = target.scrape_asset('castlevania', asset_to_scrape, fakeRomPath, rom)
            actuals.append(an_actual)
                
        # assert
        for actual in actuals:
            self.assertTrue(actual)
        
        print rom
