#!/usr/bin/python -B
# -*- coding: utf-8 -*-

# Copied from master branch (old file mobygames_scraper_test.py).
# I will try to understand how the new scraper engine coded by Chrisism works.

# Unit Testing Framework
# https://docs.python.org/2.7/library/unittest.html
# https://docs.python.org/2.7/library/unittest.html#test-cases
# https://docs.python.org/3/library/unittest.mock.html
#
# mock module is part of the unittest module in Python 3. In Python 2 there is a package in PyPI.
#
# Unit tests are class methods that begin with test_
#
# Difference between @classmethod and @staticmethod
# https://stackoverflow.com/questions/136097/what-is-the-difference-between-staticmethod-and-classmethod
#
# unittest.mock.patch decorator
# https://docs.python.org/3/library/unittest.mock.html
# The patch decorators are used for patching objects only within the scope of the function
# they decorate. The patch() decorator / context manager makes it easy to mock classes or 
# objects in a module under test. The object you specify will be replaced with a mock (or 
# other object) during the test and restored when the test ends

# --- Python standard library ---
# import fakes
# import mock
import os
import re
import sys
import unittest
# from unittest.mock import patch
import xml.etree.ElementTree

# from mock import *
# from mock import ANY
# from fakes import *

# --- Add current directory to sys.path ---
if __name__ == "__main__" and __package__ is None:
    path = os.path.abspath(os.path.dirname(__file__))
    print('Adding to sys.path {0}'.format(path))
    sys.path.append(path)
import mock
from mock import patch

# --- Import AEL modules ---
if __name__ == "__main__" and __package__ is None:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print('Adding to sys.path {0}'.format(path))
    sys.path.append(path)
from resources.utils import *
from resources.net_IO import *
from resources.scrap import *

def read_file_as_json(path):
    with open(path, 'r') as f:
        file_data = f.read()
    return json.loads(file_data, encoding = 'utf-8')

class TestLauncher(object):
    def set_platform(self, platform): self.platform = platform
    def get_platform(self): return self.platform

class TestROM(object):
    def get_path(self): return FileName('/test/rom/filename.zip')

    def set_ID(self, ID): self.ID = ID
    def get_ID(self): return self.ID

class Test_mobygames_scraper(unittest.TestCase):
    ROOT_DIR = ''
    TEST_DIR = ''
    TEST_ASSETS_DIR = ''

    @classmethod
    def setUpClass(cls):
        print('BEGIN Test_mobygames_scraper::setUpClass()')
        set_log_level(LOG_DEBUG)
        cls.TEST_DIR = os.path.dirname(os.path.abspath(__file__))
        cls.ROOT_DIR = os.path.abspath(os.path.join(cls.TEST_DIR, os.pardir))
        cls.TEST_ASSETS_DIR = os.path.abspath(os.path.join(cls.TEST_DIR, 'assets/'))
        print('ROOT DIR        {}'.format(cls.ROOT_DIR))
        print('TEST DIR        {}'.format(cls.TEST_DIR))
        print('TEST ASSETS DIR {}'.format(cls.TEST_ASSETS_DIR))
        print('END Test_mobygames_scraper::setUpClass()')

    def mocked_gamesdb(url):
        print('BEGIN Test_mobygames_scraper::mocked_gamesdb()')
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

        print('reading mocked data from file: {}'.format(mocked_json_file))

        return read_file_as_json(mocked_json_file)

    # Creates a test AEL settings dictionary.
    def get_test_settings(self):
        # print('BEGIN Test_mobygames_scraper::get_test_settings()')
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

    @patch('resources.net_IO.net_get_URL_as_json', side_effect = mocked_gamesdb)
    def test_scraping_metadata_for_game(self, mock_json_downloader):
        """
        First test. Test metadata scraping.
        """
        print('BEGIN Test_mobygames_scraper::test_scraping_metadata_for_game()')

        # --- Arrange ---
        settings = self.get_test_settings()
        launcher = TestLauncher()
        launcher.set_platform('Nintendo NES')
        rom = TestROM()
        rom.set_ID(1234)

        # Create scraper object.
        target = MobyGamesScraper(settings, launcher)

        # --- Act ---
        actual = target.scrape_metadata('castlevania', rom)

        # --- Assert ---
        self.assertTrue(actual)
        self.assertEqual('Castlevania', rom.get_name())
        print(rom)

    # add actual mobygames apikey above and comment out patch attributes to do live tests
    @patch('resources.net_IO.net_get_URL_as_json', side_effect = mocked_gamesdb)
    @patch('resources.net_IO.net_download_img')
    def disabled_test_scraping_assets_for_game(self, mock_img_downloader, mock_json_downloader):
        print('BEGIN Test_mobygames_scraper::test_scraping_assets_for_game()')
        # arrange
        settings = self.get_test_settings()
        assets_to_scrape = [
            g_assetFactory.get_asset_info(ASSET_BOXFRONT_ID),
            g_assetFactory.get_asset_info(ASSET_BOXBACK_ID),
            g_assetFactory.get_asset_info(ASSET_SNAP_ID),
        ]

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
        print(rom)

if __name__ == '__main__':
    print('Calling unittest.main()')
    unittest.main()
