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
        launcherID = '1234'
        launchers = {}
        launchers[launcherID] = {}
        launchers[launcherID]['roms_base_noext'] = 'c:/abc'
        
        # act
        romset = target.create(launcherID, None, launchers)
        actual = romset.__class__.__name__

        # assert
        expected = 'StandardRomSet'
        self.assertEqual(actual, expected)  

    def test_when_loading_roms_from_favourites_it_returns_the_correct_romset_type(self):
        
        # arrange
        mockPath = FileName('mock')
        target = RomSetFactory(mockPath)
        categoryID = VCATEGORY_FAVOURITES_ID
        launcherID = VLAUNCHER_FAVOURITES_ID
        launchers = {}
        launchers[launcherID] =  {}
        launchers[launcherID]['roms_base_noext'] = 'c:/abc'

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
        categoryID = VCATEGORY_MOST_PLAYED_ID
        launcherID = VLAUNCHER_MOST_PLAYED_ID
        launchers = {}        
        launchers[launcherID] = {}
        launchers[launcherID]['roms_base_noext'] = 'c:/abc'

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
       
        categoryID = VCATEGORY_RECENT_ID
        launcherID = VLAUNCHER_RECENT_ID
        launchers = {}
        launchers[launcherID] =  {}

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
        
        categoryID = VCATEGORY_COLLECTIONS_ID
        launcherID = 'TestID'
        launchers = {}
        launchers[launcherID] =  {}

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
        
        categoryIDs = [VCATEGORY_TITLE_ID, VCATEGORY_YEARS_ID, VCATEGORY_GENRE_ID, VCATEGORY_DEVELOPER_ID, VCATEGORY_CATEGORY_ID]
        launcherID = 'TestID'
        expected = 'VirtualLauncherRomSet'
        launchers = {}
        launchers[launcherID] = {}
        launchers[launcherID]['roms_base_noext'] = 'c:/abc'

        # act
        for categoryID in categoryIDs:
            romset = target.create(launcherID, categoryID, launchers)
            actual = romset.__class__.__name__
            
            # assert
            self.assertEqual(actual, expected)

    def test_when_loading_pclone_collection_it_will_return_the_correct_romset_type(self):
        
        # arrange
        mockPath = FileName('mock')
        target = RomSetFactory(mockPath)

        categoryID = VCATEGORY_PCLONES_ID
        launcherID = 'ut1'
        launchers = {}
        launchers[launcherID] = {}
        launchers[launcherID]['roms_base_noext'] = 'test'
        launchers[launcherID]['launcher_display_mode'] = LAUNCHER_DMODE_PCLONE
        
        # act
        romset = target.create(launcherID, categoryID, launchers)
        actual = romset.__class__.__name__

        # assert
        expected = 'PcloneRomSet'
        self.assertEqual(actual, expected)

if __name__ == '__main__':
    unittest.main()
