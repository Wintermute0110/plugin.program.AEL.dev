import unittest, mock, os, sys
from mock import *

from resources.utils import *
from resources.disk_IO import *
from resources.romsets import *
from resources.utils_kodi import *
from resources.constants import *

class Test_romsettest(unittest.TestCase):
       
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

    def test_when_loading_a_normal_rom_list_it_succeeds(self):
        
        # arrange
        mockPath = FileNameFactory.create('mock')
        target = RomSetFactory(mockPath)

        launcherID = 'ut1'
        
        launcher = {}
        launcher['id'] = launcherID
        launcher['roms_base_noext'] = 'test'
        
        # act
        actual = target.create(None, launcher)

        # assert
        self.assertIsNotNone(actual)

    def test_when_loading_a_normal_rom_list_it_returns_the_correct_romset_type(self):
        
        # arrange
        mockPath = FileNameFactory.create('mock')
        target = RomSetFactory(mockPath)
        launcherID = '1234'
        
        launcher = {}
        launcher['id'] = launcherID
        launcher['roms_base_noext'] = 'c:/abc'
                
        # act
        romset = target.create(None, launcher)
        actual = romset.__class__.__name__

        # assert
        expected = 'StandardRomSet'
        self.assertEqual(actual, expected)  

    def test_when_loading_roms_from_favourites_it_returns_the_correct_romset_type(self):
        
        # arrange
        mockPath = FileNameFactory.create('mock')
        target = RomSetFactory(mockPath)
        categoryID = VCATEGORY_FAVOURITES_ID
        launcherID = VLAUNCHER_FAVOURITES_ID
        
        launcher = {}
        launcher['id'] = launcherID
        launcher['roms_base_noext'] = 'c:/abc'
        
        # act
        romset = target.create(categoryID, launcher)
        actual = romset.__class__.__name__

        # assert
        expected = 'FavouritesRomSet'
        self.assertEqual(actual, expected)

    def test_when_loading_roms_from_most_played_category_it_returns_the_correct_romset_type(self):

        # arrange
        mockPath = FileNameFactory.create('mock')
        target = RomSetFactory(mockPath)
        categoryID = VCATEGORY_MOST_PLAYED_ID
        launcherID = VLAUNCHER_MOST_PLAYED_ID
        
        launcher = {}
        launcher['id'] = launcherID
        launcher['roms_base_noext'] = 'c:/abc'
        
        # act
        romset = target.create(categoryID, launcher)
        actual = romset.__class__.__name__

        # assert
        expected = 'FavouritesRomSet'
        self.assertEqual(actual, expected)
        

    def test_when_loading_roms_from_most_played_category_it_returns_the_correct_romset_type(self):

        # arrange
        mockPath = FileNameFactory.create('mock')
        target = RomSetFactory(mockPath)
       
        categoryID = VCATEGORY_RECENT_ID
        launcherID = VLAUNCHER_RECENT_ID
        
        launcher = {}
        launcher['id'] = launcherID
        
        # act
        romset = target.create(categoryID, launcher)
        actual = romset.__class__.__name__

        # assert
        expected = 'RecentlyPlayedRomSet'
        self.assertEqual(actual, expected)

    def test_when_loading_roms_from_a_collection_it_returns_the_correct_romset_type(self):

        # arrange
        mockPath = FileNameFactory.create('mock')
        target = RomSetFactory(mockPath)
        
        categoryID = VCATEGORY_COLLECTIONS_ID
        launcher = {}
        launcher['id'] = 'TestID'

        # act
        romset = target.create(categoryID, launcher)
        actual = romset.__class__.__name__

        # assert
        expected = 'CollectionRomSet'
        self.assertEqual(actual, expected)

    def test_when_loading_roms_from_a_category_it_returns_the_correct_romset_type(self):

        # arrange
        mockPath = FileNameFactory.create('mock')
        target = RomSetFactory(mockPath)
        
        categoryIDs = [VCATEGORY_TITLE_ID, VCATEGORY_YEARS_ID, VCATEGORY_GENRE_ID, VCATEGORY_DEVELOPER_ID, VCATEGORY_CATEGORY_ID]
        launcherID = 'TestID'
        expected = 'VirtualLauncherRomSet'
        
        launcher = {}
        launcher['id'] = launcherID
        launcher['roms_base_noext'] = 'c:/abc'

        # act
        for categoryID in categoryIDs:
            romset = target.create(categoryID, launcher)
            actual = romset.__class__.__name__
            
            # assert
            self.assertEqual(actual, expected)

    def test_when_loading_pclone_collection_it_will_return_the_correct_romset_type(self):
        
        # arrange
        mockPath = FileNameFactory.create('mock')
        target = RomSetFactory(mockPath)

        categoryID = VCATEGORY_PCLONES_ID
        launcherID = 'ut1'
       
        launcher = {}
        launcher['id'] = launcherID
        launcher['roms_base_noext'] = 'c:/abc'
        launcher['launcher_display_mode'] = LAUNCHER_DMODE_PCLONE
        
        # act
        romset = target.create(categoryID, launcher)
        actual = romset.__class__.__name__

        # assert
        expected = 'PcloneRomSet'
        self.assertEqual(actual, expected)

if __name__ == '__main__':
    unittest.main()
