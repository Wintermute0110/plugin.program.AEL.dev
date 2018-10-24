import unittest, mock, os, sys, re

from mock import *
from mock import ANY
from fakes import *
import xml.etree.ElementTree as ET

from resources.utils import *
from resources.utils_kodi import *
from resources.net_IO import *
from resources.scrapers import *
from resources.scrap import *
from resources.scrap_metadata import *
from resources.assets import *
from resources.filename import *
        
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
        set_use_print(True)
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

        return settings

    # add actual mobygames apikey above and comment out patch attributes to do live tests
    @patch('resources.scrapers.net_get_URL_as_json', side_effect = mocked_gamesdb)
    @patch('resources.scrapers.net_download_img')
    @patch('resources.scrapers.kodi_update_image_cache')
    def test_scraping_for_game(self, mock_cache, mock_img_downloader, mock_json_downloader):

        # arrange
        settings = self.get_test_settings()
        asset_factory = AssetInfoFactory.create()

        assets_to_scrape = [
            asset_factory.get_asset_info(ASSET_BOXFRONT), 
            asset_factory.get_asset_info(ASSET_BOXBACK), 
            asset_factory.get_asset_info(ASSET_SNAP)]

        launcher = StandardRomLauncher(None, settings, None, None, None, False)
        launcher.update_platform('Nintendo NES')
        launcher.set_asset_path(asset_factory.get_asset_info(ASSET_BOXFRONT),'/my/nice/assets/front/')
        launcher.set_asset_path(asset_factory.get_asset_info(ASSET_BOXBACK),'/my/nice/assets/back/')
        launcher.set_asset_path(asset_factory.get_asset_info(ASSET_SNAP),'/my/nice/assets/snaps/')
        
        rom = Rom({'id': 1234})
        fakeRomPath = FakeFile('/my/nice/roms/castlevania.zip')

        target = MobyGamesScraper(settings, launcher, True, assets_to_scrape)

        # act
        actual = target.scrape('castlevania', fakeRomPath, rom)
                
        # assert
        self.assertTrue(actual)
        self.assertEqual(u'Castlevania', rom.get_name())
        print rom
