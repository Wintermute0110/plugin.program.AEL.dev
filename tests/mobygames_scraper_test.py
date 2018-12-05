import unittest, mock, os, sys, re

from mock import *
from mock import ANY
from fakes import *
import xml.etree.ElementTree as ET

from resources.utils import *
from resources.net_IO import *
from resources.scrap import *
from resources.objects import *
        
def read_file(path):
    with open(path, 'r') as f:
        return f.read()
    
def read_file_as_json(path):
    file_data = read_file(path)
    return json.loads(file_data, encoding = 'utf-8')

class Test_mobygames_scraper(unittest.TestCase):
    
    ROOT_DIR = ''
    TEST_DIR = ''
    TEST_ASSETS_DIR = ''

    @classmethod
    def setUpClass(cls):
        set_log_level(LOG_DEBUG)
        
        cls.TEST_DIR = os.path.dirname(os.path.abspath(__file__))
        cls.ROOT_DIR = os.path.abspath(os.path.join(cls.TEST_DIR, os.pardir))
        cls.TEST_ASSETS_DIR = os.path.abspath(os.path.join(cls.TEST_DIR,'assets/'))
                
        print 'ROOT DIR: {}'.format(cls.ROOT_DIR)
        print 'TEST DIR: {}'.format(cls.TEST_DIR)
        print 'TEST ASSETS DIR: {}'.format(cls.TEST_ASSETS_DIR)
        print '---------------------------------------------------------------------------'

    def mocked_gamesdb(url):

        mocked_json_file = '';

        if 'format=brief&title=' in url:
            mocked_json_file = Test_mobygames_scraper.TEST_ASSETS_DIR + "\\mobygames_castlevania_list.json"
    
        if 'screenshots' in url:
            mocked_json_file = Test_mobygames_scraper.TEST_ASSETS_DIR + "\\mobygames_castlevania_screenshots.json"
    
        if 'covers' in url:
            mocked_json_file = Test_mobygames_scraper.TEST_ASSETS_DIR + "\\mobygames_castlevania_covers.json"
                            
        if re.search('/games/(\d*)\?', url):
            mocked_json_file = Test_mobygames_scraper.TEST_ASSETS_DIR + "\\mobygames_castlevania.json"
            
        if mocked_json_file == '':
            return net_get_URL_as_json(url)

        print 'reading mocked data from file: {}'.format(mocked_json_file)
        return read_file_as_json(mocked_json_file)

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

    @patch('resources.scrap.net_get_URL_as_json', side_effect = mocked_gamesdb)
    def test_scraping_metadata_for_game(self, mock_json_downloader):
        
        # arrange
        settings = self.get_test_settings()
        
        launcher = StandardRomLauncher(None, settings, None, None, None, None, None)
        launcher.set_platform('Nintendo NES')
        
        rom = ROM({'id': 1234})
        fakeRomPath = FakeFile('/my/nice/roms/castlevania.zip')

        target = MobyGamesScraper(settings, launcher)

        # act
        actual = target.scrape_metadata('castlevania', fakeRomPath, rom)
                
        # assert
        self.assertTrue(actual)
        self.assertEqual(u'Castlevania', rom.get_name())
        print rom

        
    # add actual mobygames apikey above and comment out patch attributes to do live tests
    @patch('resources.scrap.net_get_URL_as_json', side_effect = mocked_gamesdb)
    @patch('resources.scrap.net_download_img')
    def test_scraping_assets_for_game(self, mock_img_downloader, mock_json_downloader):

        # arrange
        settings = self.get_test_settings()
        
        assets_to_scrape = [
            g_assetFactory.get_asset_info(ASSET_BOXFRONT_ID), 
            g_assetFactory.get_asset_info(ASSET_BOXBACK_ID), 
            g_assetFactory.get_asset_info(ASSET_SNAP_ID)]
        
        launcher = StandardRomLauncher(None, settings, None, None, None, None, None)
        launcher.set_platform('Nintendo NES')
        launcher.set_asset_path(g_assetFactory.get_asset_info(ASSET_BOXFRONT_ID),'/my/nice/assets/front/')
        launcher.set_asset_path(g_assetFactory.get_asset_info(ASSET_BOXBACK_ID),'/my/nice/assets/back/')
        launcher.set_asset_path(g_assetFactory.get_asset_info(ASSET_SNAP_ID),'/my/nice/assets/snaps/')
        
        rom = ROM({'id': 1234})
        fakeRomPath = FakeFile('/my/nice/roms/castlevania.zip')

        target = MobyGamesScraper(settings, launcher)

        # act
        actuals = []
        for asset_to_scrape in assets_to_scrape:
            an_actual = target.scrape_asset('castlevania', asset_to_scrape, fakeRomPath, rom)
            actuals.append(an_actual)
                
        # assert
        for actual in actuals:
            self.assertTrue(actual)
        
        print rom