import unittest
import mock
from mock import *
from fakes import *
import xml.etree.ElementTree as ET

from resources.utils import *
from resources.utils_kodi import *
from resources.scrapers import *
from resources.scrap import *

class Test_scrapertests(unittest.TestCase):
      
    @classmethod
    def setUpClass(cls):
        set_use_print(True)
        set_log_level(LOG_DEBUG)
    
    def read_file(self, path):
        with open(path, 'r') as f:
            return f.read()

    def read_file_xml(self, path):
        data = self.read_file(path)
        root = ET.fromstring(data)
        return root

    def _get_fake_launcher(self):
        
        launcher = {}
        launcher['platform'] = ''
        launcher['path_title'] = ''
        launcher['path_snap'] = ''
        launcher['path_boxfront'] = ''
        launcher['path_boxback'] = ''
        launcher['path_cartridge'] = ''
        launcher['path_fanart'] = ''
        launcher['path_banner'] = ''
        launcher['path_clearlogo'] = ''
        launcher['path_flyer'] = ''
        launcher['path_map'] = ''
        launcher['path_manual'] = ''
        launcher['path_trailer'] = ''

        return launcher

    def test_with_no_actual_scraperpaths_set_only_the_cleantitlescraper_will_be_loaded(self):
        
        # arrange
        set_use_print(True)
        addon_dir = FileName('')

        settings = {}
        settings['scan_metadata_policy'] = 0
        settings['scan_asset_policy'] = 0
        settings['metadata_scraper_mode'] = 0
        settings['scan_clean_tags'] = True

        launcher = self._get_fake_launcher()
        
        target = ScraperFactory(settings, addon_dir)

        expected = 'CleanTitleScraper'

        # act
        actuals = target.create(launcher)
        actual_name = actuals[0].__class__.__name__

        # assert
        self.assertIsNotNone(actuals)
        self.assertEqual(expected, actual_name)

    def test_with_one_scraperpaths_set_two_scrapers_will_be_loaded_and_one_is_a_localfiles_scraper(self):
        
        # arrange
        set_use_print(True)
        addon_dir = FileName('')

        settings = {}
        settings['scan_metadata_policy'] = 0
        settings['scan_asset_policy'] = 0
        settings['metadata_scraper_mode'] = 0
        settings['scan_clean_tags'] = True

        settings['scraper_title'] = 0 # NullScraper

        launcher = self._get_fake_launcher()
        launcher['path_title'] = '//abc/a/b/c'
        launcher['platform'] = 'nintendo'
        
        target = ScraperFactory(settings, addon_dir)
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
        set_use_print(True)
        addon_dir = FileName('')

        settings = {}
        settings['scan_metadata_policy'] = 3 # OnlineScraper only
        settings['scan_asset_policy'] = 0
        settings['metadata_scraper_mode'] = 1
        settings['scan_clean_tags'] = True
        settings['scan_ignore_scrap_title'] = False
        settings['scraper_metadata'] = 0 # NullScraper

        launcher = self._get_fake_launcher()
        launcher['platform'] = 'nintendo'
        
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
        set_use_print(True)
        addon_dir = FileName('')

        settings = {}
        settings['scan_metadata_policy'] = 2 # NFO with Online as decorator
        settings['scan_asset_policy'] = 0
        settings['metadata_scraper_mode'] = 1
        settings['scan_clean_tags'] = True
        settings['scan_ignore_scrap_title'] = False
        settings['scraper_metadata'] = 0 # NullScraper

        launcher = self._get_fake_launcher()
        launcher['platform'] = 'dummy'
        
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

        rom = {}
        rom['m_name'] = ''

        romPath = FileName('/don/el_juan [DUMMY].zip')

        target = CleanTitleScraper(settings)

        expected = 'el_juan'

        # act
        actual = target.scrape('don_juan', romPath, rom)

        # assert
        self.assertIsNotNone(actual)
        self.assertTrue(actual)

        self.assertEqual(expected, rom['m_name'])
        
    @patch('resources.utils.FileName.readAllUnicode')
    def test_when_scraping_with_nfoscraper_it_will_give_the_correct_result(self, mock_filename):

         # arrange
        test_file_dir = os.path.dirname(os.path.abspath(__file__))
        mock_filename.return_value = unicode(self.read_file(test_file_dir + "\\test-nfo.xml"), "utf-8")

        settings = {}
        settings['scan_clean_tags'] = True
        settings['metadata_scraper_mode'] = 0

        rom = {}
        rom['m_name'] = ''

        romPath = FileName('/don/el_juan [DUMMY].zip')

        target = NfoScraper(settings)

        expected = 'Pitfall: The Mayan Adventure'
        
        # act
        actualResult = target.scrape('don_juan', romPath, rom)

        # assert
        self.assertIsNotNone(actualResult)
        self.assertTrue(actualResult)

        actual = rom['m_name']
        self.assertEqual(actual, expected)
     
    @patch('resources.utils.FileName.readXml')
    def test_when_scraping_online_metadata_it_will_give_the_correct_result(self, mock_xmlreader):
        
        # arrange
        test_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.abspath(os.path.join(test_dir, os.pardir))
        mock_xmlreader.return_value = self.read_file_xml(root_dir + "\\GameDBInfo\\Sega 32x.xml")

        scraper_obj = metadata_Offline()
        scraper_obj.set_addon_dir(root_dir)

        settings = {}
        settings['scan_clean_tags'] = True
        settings['metadata_scraper_mode'] = 0
        settings['scan_ignore_scrap_title'] = False

        rom = {}
        rom['m_name'] = ''
        rom['platform'] = 'Sega 32X'

        romPath = FileName('/roms/Pitfall.zip')

        target = OnlineMetadataScraper(scraper_obj, settings)

        expected = 'Pitfall: The Mayan Adventure'
        
        # act
        actualResult = target.scrape('Pitfall', romPath, rom)

        # assert
        self.assertIsNotNone(actualResult)
        self.assertTrue(actualResult)

        actual = rom['m_name']
        self.assertEqual(actual, expected)



if __name__ == '__main__':
    unittest.main()
