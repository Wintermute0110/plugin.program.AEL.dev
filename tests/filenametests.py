import unittest
from resources.utils import *
from resources.utils_kodi import *
from resources.disk_IO import *
from resources.scrap import *
from resources.scrap_common import *
from resources.scrap_asset import *
from resources.scrap_metadata import *
from resources.launchers import *

import resources.rom_audit

class Test_filenametests(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        set_use_print(True)

    def test_isdir_works_with_directories_with_an_endslash(self):
        testFile = FileName('smb://192.168.0.5/Media6/Roms/SNK/')
        
        print("Original path: {0}".format(testFile.getOriginalPath()))
        print("Path: {0}".format(testFile.getPath()))
        print("IsDir: {0}".format(testFile.isdir()))
        print("IsFile: {0}".format(testFile.isfile()))
        self.assertTrue(testFile.isdir())

    def test_isdir_works_with_directories_without_an_endslash(self):
        testFile = FileName('smb://192.168.0.5/Media6/Roms/SNK')
        
        print("Original path: {0}".format(testFile.getOriginalPath()))
        print("Path: {0}".format(testFile.getPath()))
        print("IsDir: {0}".format(testFile.isdir()))
        print("IsFile: {0}".format(testFile.isfile()))
        self.assertTrue(testFile.isdir())
        
    def test_isfile_returns_false_if_its_a_dir(self):
        testFile = FileName('smb://192.168.0.5/Media6/Roms/SNK')
        
        print("Original path: {0}".format(testFile.getOriginalPath()))
        print("Path: {0}".format(testFile.getPath()))
        print("IsFile: {0}".format(testFile.isfile()))
        print("IsDir: {0}".format(testFile.isdir()))
        self.assertFalse(testFile.isfile())
    
    @unittest.skip("needs to be checked")
    def test_isfile_returns_true_if_its_an_actual_file_path(self):
        testFile = FileName("C:\Projects\Kodi\AEL\package.json")
        
        print("Original path: {0}".format(testFile.getOriginalPath()))
        print("Path: {0}".format(testFile.getPath()))
        print("IsFile: {0}".format(testFile.isfile()))
        print("IsDir: {0}".format(testFile.isdir()))
        self.assertTrue(testFile.isfile())
        
class Test_scrape(unittest.TestCase):
    
    @unittest.skip("no bashing of site")
    def test_arcade_scraping_should_work_correctly(self):
        
        game = {'id': 'http://adb.arcadeitalia.net/dettaglio_mame.php?lang=en&game_name=kof2000', 'title' : 'kof2000'}
        
        scraper = metadata_ArcadeDB()
        actual = scraper.get_metadata(game)

        self.assertIsNotNone(actual)
        
if __name__ == '__main__':
    unittest.main()
