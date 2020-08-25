import unittest, mock, os, sys, re

from mock import *
from mock import ANY
from tests.fakes import *
import xml.etree.ElementTree as ET

from resources.utils import *
from resources.net_IO import *
from resources.scrap import *
from resources.objects import *
from resources.constants import *
        
def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def mocked_google(url, url_log=None):

    mocked_html = ''

    if '&tbm=isch' in url:
        mocked_html = os.path.abspath(os.path.join(Test_google_scrapers.TEST_ASSETS_DIR,'google_result.html'))

    if 'youtube.com' in url:
        mocked_html = os.path.abspath(os.path.join(Test_google_scrapers.TEST_ASSETS_DIR,'youtube_result.html'))

    if mocked_html == '':
        return net_get_URL(url, url)

    print('reading mocked data from file: {}'.format(mocked_html))
    return read_file(mocked_html).decode('utf-8'), 200


xbmc.log = print_log

class Test_google_scrapers(unittest.TestCase):
    
    ROOT_DIR = ''
    TEST_DIR = ''
    TEST_ASSETS_DIR = ''

    @classmethod
    def setUpClass(cls):
        set_log_level(LOG_DEBUG)
        
        cls.TEST_DIR = os.path.dirname(os.path.abspath(__file__))
        cls.ROOT_DIR = os.path.abspath(os.path.join(cls.TEST_DIR, os.pardir))
        cls.TEST_ASSETS_DIR = os.path.abspath(os.path.join(cls.TEST_DIR,'assets'))
                
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
        settings['scraper_mobygames_apikey'] = 'abc123'
        settings['escape_romfile'] = False
        settings['scraper_cache_dir'] = self.TEST_ASSETS_DIR

        return settings

    @patch('resources.scrap.net_get_URL', side_effect = mocked_google)
    def test_scraping_assets_for_game(self, mock_url_downloader):

        # arrange
        settings = self.get_test_settings()
        status_dic = {}
        status_dic['status'] = True
        target = GoogleImageSearch(settings)
                
        asset_to_scrape = g_assetFactory.get_asset_info(ASSET_BOXFRONT_ID)
        f = FakeFile('/roms/castlevania.nes')
        platform = 'Nintendo NES'

        # act
        candidates = target.get_candidates('castlevania', f, f, platform, status_dic)
        target.set_candidate(f, platform, candidates[0])

        # act
        actual = target.get_assets(asset_to_scrape, status_dic)
                
        # assert
        self.assertTrue(actual)     
        self.assertEqual(100, len(actual))
        for a in actual:        
            print('{} URL: {}'.format(a['display_name'].encode('utf-8'), a['url'].encode('utf-8') ))

    @patch('resources.scrap.net_get_URL', side_effect = mocked_google)
    def test_scraping_trailer_assets_for_game(self, mock_url_downloader):

        # arrange
        settings = self.get_test_settings()
        status_dic = {}
        status_dic['status'] = True
        target = YouTubeSearch(settings)
        
        asset_to_scrape = g_assetFactory.get_asset_info(ASSET_TRAILER_ID)
        f = FakeFile('/roms/castlevania.nes')
        platform = 'Nintendo NES'

        # act
        candidates = target.get_candidates('castlevania', f, f, platform, status_dic)
        target.set_candidate(f, platform, candidates[0])
        actual = target.get_assets(asset_to_scrape, status_dic)
                
        # assert
        self.assertTrue(actual)     
        self.assertEqual(20, len(actual))
        for a in actual:        
            print('{} URL: {}'.format(a['display_name'].encode('utf-8'), a['url'].encode('utf-8') ))
