import unittest
import mock
from mock import *

from resources.utils import *
from resources.disk_IO import *
from resources.romsets import *
from resources.utils_kodi import *
from resources.constants import *

class Test_romsettest(unittest.TestCase):
   
    def test_when_loading_a_normal_rom_list_it_succeeds(self):
        
        # arrange
        mockPath = FileName('mock')
        target = RomSetFactory(mockPath)

        launcherID = 'ut1'
        launchers = {}
        launchers[launcherID] = {}
        launchers[launcherID]['roms_base_noext'] = 'test'
        
        # act
        actual = target.create(launcherID, None, launchers)

        # assert
        self.assertIsNotNone(actual)

    def test_when_loading_a_normal_rom_list_it_returns_the_correct_romset_type(self):
        
        # arrange
        mockPath = FileName('mock')
        target = RomSetFactory(mockPath)
        launchers = {}
        
        # act
        romset = target.create(None, None, launchers)
        actual = romset.__class__.__name__

        # assert
        expected = 'StandardRomSet'
        self.assertEqual(actual, expected)  

    def test_when_loading_roms_from_favourites_it_returns_the_correct_romset_type(self):
        
        # arrange
        mockPath = FileName('mock')
        target = RomSetFactory(mockPath)
        launchers = {}
        categoryID = VCATEGORY_FAVOURITES_ID
        launcherID = VLAUNCHER_FAVOURITES_ID

        # act
        romset = target.create(launcherID, categoryID, launchers)
        actual = romset.__class__.__name__

        # assert
        expected = 'FavouritesRomSet'
        self.assertEqual(actual, expected)

    def test_when_loading_roms_from_most_played_category_it_returns_the_correct_romset_type(self):

        # arrange
        mockPath = FileName('mock')
        target = RomSetFactory(mockPath)
        launchers = {}
        categoryID = VCATEGORY_MOST_PLAYED_ID
        launcherID = VLAUNCHER_MOST_PLAYED_ID

        # act
        romset = target.create(launcherID, categoryID, launchers)
        actual = romset.__class__.__name__

        # assert
        expected = 'FavouritesRomSet'
        self.assertEqual(actual, expected)
        

    def test_when_loading_roms_from_most_played_category_it_returns_the_correct_romset_type(self):

        # arrange
        mockPath = FileName('mock')
        target = RomSetFactory(mockPath)
       
        launchers = {} 
        categoryID = VCATEGORY_RECENT_ID
        launcherID = VLAUNCHER_RECENT_ID

        # act
        romset = target.create(launcherID, categoryID, launchers)
        actual = romset.__class__.__name__

        # assert
        expected = 'RecentlyPlayedRomSet'
        self.assertEqual(actual, expected)

    def test_when_loading_roms_from_a_collection_it_returns_the_correct_romset_type(self):

        # arrange
        mockPath = FileName('mock')
        target = RomSetFactory(mockPath)
        
        launchers = {}
        categoryID = VCATEGORY_COLLECTIONS_ID
        launcherID = 'TestID'

        # act
        romset = target.create(launcherID, categoryID, launchers)
        actual = romset.__class__.__name__

        # assert
        expected = 'CollectionRomSet'
        self.assertEqual(actual, expected)

    def test_when_loading_roms_from_a_category_it_returns_the_correct_romset_type(self):

        # arrange
        mockPath = FileName('mock')
        target = RomSetFactory(mockPath)
        
        categoryIDs = [VCATEGORY_TITLE_ID, VCATEGORY_YEARS_ID, VCATEGORY_GENRE_ID, VCATEGORY_STUDIO_ID, VCATEGORY_CATEGORY_ID]
        launcherID = 'TestID'
        launchers = {}
        expected = 'VirtualLauncherRomSet'

        # act
        for categoryID in categoryIDs:
            romset = target.create(launcherID, categoryID, launchers)
            actual = romset.__class__.__name__
            
            # assert
            self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
