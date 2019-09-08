#!/usr/bin/python -B
# -*- coding: utf-8 -*-

# Copied from master branch (old file scraperfactory_test.py).
# I will try to understand how the new scraper engine coded by Chrisism works.
import unittest
import mock
import os
import sys

from mock import *
from mock import ANY
from fakes import *
import xml.etree.ElementTree as ET

from resources.utils import *
from resources.scrap import *
from resources.objects import *

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
                
        print 'ROOT DIR: {}'.format(cls.ROOT_DIR)
        print 'TEST DIR: {}'.format(cls.TEST_DIR)
        print 'TEST ASSETS DIR: {}'.format(cls.TEST_ASSETS_DIR)
        print '---------------------------------------------------------------------------'

    def read_file(self, path):
        with open(path, 'r') as f:
            return f.read()

    def read_file_xml(self, path):
        data = self.read_file(path)
        root = ET.fromstring(data)
        return root

    def test_with_no_actual_scraperpaths_set_only_the_cleantitlescraper_will_be_loaded(self):
        # arrange
        addon_dir = FakeFile('')
        paths = Fake_Paths('//abc')

        settings = {}
        settings['scan_metadata_policy'] = 0
        settings['scan_asset_policy'] = 0
        settings['metadata_scraper_mode'] = 0
        settings['scan_clean_tags'] = True
        settings['escape_romfile'] = False

        launcher = StandardRomLauncher(None, settings, None, None, None, False)
        
        target = ScraperFactory(paths, settings)

        expected = 'CleanTitleScraper'

        # act
        actual = target.create(launcher)
        actual_name = actual.metadata_scraper.__class__.__name__

        # assert
        self.assertIsNotNone(actuals)
        self.assertEqual(expected, actual_name)

    def test_with_one_scraperpaths_set_two_scrapers_will_be_loaded_and_one_is_a_localfiles_scraper(self):
        
        # arrange
        addon_dir = FakeFile('')
        paths = Fake_Paths('//abc')

        settings = {}
        settings['scan_metadata_policy'] = 0
        settings['scan_asset_policy'] = 0
        settings['metadata_scraper_mode'] = 0
        settings['asset_scraper_mode'] = 0
        settings['scan_clean_tags'] = True
        settings['escape_romfile'] = False

        settings['scraper_title'] = 1 # TheGamesDB
        
        launcher = StandardRomLauncher(None, settings, None, None, None, False)
        launcher.update_platform('nintendo')
        launcher.set_custom_attribute('path_title', '//abc/a/b/c')
        
        target = ScraperFactory(paths, settings)
        expected = 'LocalAssetScraper'

        # act
        actuals = target.create(launcher)

        # assert
        self.assertIsNotNone(actuals)
        self.assertEqual(2, len(actuals))
        
        actual_name = actuals[1].__class__.__name__
        self.assertEqual(expected, actual_name)

    def test_when_using_online_metadata_the_correct_scraper_will_be_loaded(self):
        
        # arrange
        paths = Fake_Paths('//abc')

        settings = {}
        settings['scan_metadata_policy'] = 3 # OnlineScraper only
        settings['scan_asset_policy'] = 0
        settings['metadata_scraper_mode'] = 1
        settings['scan_clean_tags'] = True
        settings['scan_ignore_scrap_title'] = False
        settings['scraper_metadata'] = 0 # NullScraper
        settings['escape_romfile'] = False

        launcher = StandardRomLauncher(None, settings, None, None, None, False)
        launcher.update_platform('nintendo')
        
        target = ScraperFactory(settings, addon_dir)
        expected = 'OnlineMetadataScraper'

        # act
        actuals = target.create(launcher)

        # assert
        self.assertIsNotNone(actuals)
        self.assertEqual(1, len(actuals))
        
        actual_name = actuals[0].__class__.__name__
        self.assertEqual(expected, actual_name)

    def test_when_using_local_nfo_metadata_the_correct_scraper_will_be_loaded(self):
        
        # arrange
        paths = Fake_Paths('//abc')

        settings = {}
        settings['scan_metadata_policy'] = 2 # NFO with Online as decorator
        settings['scan_asset_policy'] = 0
        settings['metadata_scraper_mode'] = 1
        settings['scan_clean_tags'] = True
        settings['scan_ignore_scrap_title'] = False
        settings['scraper_metadata'] = 0 # NullScraper
        settings['escape_romfile'] = False

        launcher = StandardRomLauncher(None, settings, None, None, None, False)
        launcher.update_platform('dummy')
        
        target = ScraperFactory(settings, addon_dir)
        expected = 'NfoScraper'

        # act
        actuals = target.create(launcher)

        # assert
        self.assertIsNotNone(actuals)
        self.assertEqual(1, len(actuals))
        
        actual_name = actuals[0].__class__.__name__
        self.assertEqual(expected, actual_name)

    def test_when_scraping_with_cleantitlescraper_it_will_give_the_correct_result(self):

        # arrange
        settings = {}
        settings['scan_clean_tags'] = True
        settings['metadata_scraper_mode'] = 0
        settings['escape_romfile'] = False
        
        launcher = StandardRomLauncher(None, settings, None, None, None, False)
        
        rom = ROM({'id': 1234})
        romPath = FileNameFactory.create('/don/el_juan [DUMMY].zip')

        target = CleanTitleScraper(settings, launcher)

        expected = 'el_juan'

        # act
        actual = target.scrape('don_juan', romPath, rom)

        # assert
        self.assertIsNotNone(actual)
        self.assertTrue(actual)

        self.assertEqual(expected, rom.get_name())
        
    @patch('resources.utils.KodiFileName.readAllUnicode')
    def test_when_scraping_with_nfoscraper_it_will_give_the_correct_result(self, mock_filename):

         # arrange
        mock_filename.return_value = unicode(self.read_file(self.TEST_ASSETS_DIR + "\\test-nfo.xml"), "utf-8")

        settings = {}
        settings['scan_clean_tags'] = True
        settings['metadata_scraper_mode'] = 0
        settings['escape_romfile'] = False
        
        launcher = StandardRomLauncher(None, settings, None, None, None, False)
        launcher.update_platform('Sega 32X')
        
        rom = ROM({'id': 1234})
        romPath = FileNameFactory.create('/don/el_juan [DUMMY].zip')

        target = NfoScraper(settings, launcher)

        expected = 'Pitfall: The Mayan Adventure'
        
        # act
        actualResult = target.scrape('don_juan', romPath, rom)

        # assert
        self.assertIsNotNone(actualResult)
        self.assertTrue(actualResult)

        actual = rom.get_name()
        self.assertEqual(actual, expected)
     
    @patch('resources.utils.KodiFileName.readXml')
    def test_when_scraping_online_metadata_it_will_give_the_correct_result(self, mock_xmlreader):
        
        # arrange
        mock_xmlreader.return_value = self.read_file_xml(self.ROOT_DIR + "\\GameDBInfo\\Sega 32x.xml")

        scraper_obj = metadata_Offline()
        scraper_obj.set_addon_dir(self.ROOT_DIR)

        settings = {}
        settings['scan_clean_tags'] = True
        settings['metadata_scraper_mode'] = 0
        settings['scan_ignore_scrap_title'] = False
        settings['escape_romfile'] = False

        launcher = StandardRomLauncher(None, settings, None, None, None, False)
        launcher.update_platform('Sega 32X')
        
        rom = ROM({'id': 1234})
        romPath = FileNameFactory.create('/roms/Pitfall.zip')

        target = OnlineMetadataScraper(scraper_obj, settings, launcher)

        expected = 'Pitfall: The Mayan Adventure'
        
        # act
        actualResult = target.scrape('Pitfall', romPath, rom)

        # assert
        self.assertIsNotNone(actualResult)
        self.assertTrue(actualResult)

        actual = rom.get_custom_attribute('m_name')
        self.assertEqual(actual, expected)
        
    @patch('resources.scrap.net_download_img')
    @patch('resources.scrap_asset.net_get_URL_oneline')
    @patch('resources.scrap_common.net_get_URL_oneline')
    @unittest.skip('GamesDB deprecated version')
    def test_when_scraping_online_assets_it_will_give_the_correct_result(self, mock_search, mock_singlehit, mock_imgdownload):
        
        # arrange
        mock_search.return_value = self.read_file(self.TEST_ASSETS_DIR + "\\gamesdb_search.xml").replace('\r\n', '').replace('\n', '')
        mock_singlehit.return_value = self.read_file(self.TEST_ASSETS_DIR + "\\gamesdb_singlehit.xml").replace('\r\n', '').replace('\n', '')

        scraper_obj = asset_TheGamesDB()

        settings = {}
        settings['scan_asset_policy'] = 1
        settings['asset_scraper_mode'] = 0
        settings['metadata_scraper_mode'] = 0
        settings['scan_ignore_scrap_title'] = 0
        settings['escape_romfile'] = False
        
        launcher = StandardRomLauncher(None, settings, None, None, None, False)
        launcher.update_platform('Sega 32X')
        launcher.set_custom_attribute('path_title', '/fake/title/')
        
        rom = ROM({'id': 1234})

        romPath = FileNameFactory.create('/roms/Pitfall.zip')
        asset_kind = ASSET_TITLE
        asset_info = assets_get_info_scheme(asset_kind)
        
        target = OnlineAssetScraper(scraper_obj, asset_kind, asset_info, settings, launcher)

        expected = '/fake/title/Pitfall.jpg'
        
        # act
        actualResult = target.scrape('Pitfall', romPath, rom)
        
        # assert
        self.assertIsNotNone(actualResult)
        self.assertTrue(actualResult)
        
        actual = rom.get_custom_attribute('s_title')
        log_verb('Set Title file "{0}"'.format(actual))

        self.assertEqual(actual, expected)

    @patch('resources.scrap.net_download_img')
    @unittest.skip('Actual HTTP call')
    def test_when_scraping_online_assets_for_a_cached_result_it_will_load_that_one(self, mock_imgdownload):
        # arrange
        scraper_obj = asset_TheGamesDB()

        settings = {}
        settings['scan_asset_policy'] = 1
        settings['asset_scraper_mode'] = 0
        settings['metadata_scraper_mode'] = 0
        settings['scan_ignore_scrap_title'] = 0
        settings['escape_romfile'] = False

        launcher = StandardRomLauncher(None, settings, None, None, None, False)
        launcher.update_platform('Sega 32X')
        launcher.set_custom_attribute('path_title','/fake/title/')
        
        rom = ROM({'id': 1234})

        romPath = FileNameFactory.create('/roms/Pitfall.zip')
        asset_kind = ASSET_TITLE_ID
        asset_info = g_assetFactory.get_asset_info(asset_kind)
        
        target = OnlineAssetScraper(scraper_obj, asset_kind, asset_info, settings, launcher)
        
        expectedCandidate = {}
        expectedCandidate['display_name'] = 'Pitfall'
        expectedCandidate['id'] = '12345'

        OnlineAssetScraper.scrap_asset_cached_dic[target.scraper_id] = {
            'ROM_base_noext' : romPath.getBase_noext(),
            'platform' : launcher.get_platform(),
            'game_dic' : expectedCandidate
        }

        expectedUrl = u'http://thegamesdb.net/banners/screenshots/12345-1.jpg'
                
        # act
        actualResult = target.scrape('Pitfall', romPath, rom)
        
        # assert
        self.assertIsNotNone(actualResult)
        self.assertTrue(actualResult)
        mock_imgdownload.assert_called_with(expectedUrl, ANY)
    
    @patch('resources.utils.KodiFileName.scanFilesInPathAsFileNameObjects')
    def test_when_scraping_local_assets_it_will_give_the_correct_result(self, mock_filescan):
        
        # arrange
        mock_filescan.return_value = [FakeFile('x.jpg'),FakeFile('y.jpg'), FakeFile('pitfall.jpg'), FakeFile('donkeykong.jpg')]

        settings = {}
        settings['scan_asset_policy'] = 1
        settings['asset_scraper_mode'] = 0
        settings['metadata_scraper_mode'] = 0
        settings['scan_ignore_scrap_title'] = 0
        settings['escape_romfile'] = False
        
        launcher = StandardRomLauncher(None, settings, None, None, None, False)
        launcher.update_platform('Sega 32X')
        launcher.set_custom_attribute('path_title','/fake/title/')
        
        rom = ROM({'id': 1234})
        romPath = FakeFile('/roms/Pitfall.zip')
        asset_kind = ASSET_TITLE_ID
        asset_info = g_assetFactory.get_asset_info(asset_kind)

        target = LocalAssetScraper(asset_kind, asset_info, settings, launcher)
        expected = '/fake/title/pitfall.jpg'
        
        # act
        actualResult = target.scrape('Pitfall', romPath, rom)
        
        # assert
        self.assertIsNotNone(actualResult)
        self.assertTrue(actualResult)
        
        actual = rom.get_custom_attribute('s_title')
        log_verb('Set Title file "{0}"'.format(actual))

        self.assertEqual(actual, expected)

if __name__ == '__main__':
    unittest.main()
