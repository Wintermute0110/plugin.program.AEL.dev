from abc import ABCMeta, abstractmethod

import os

# --- Kodi stuff ---
import xbmc

# --- Modules/packages in this plugin ---
from constants import *
from disk_IO import *
from utils import *
from utils_kodi import *

class RomSetFactory():
    
    def __init__(self, pluginDataDir):

        self.ROMS_DIR                 = pluginDataDir.join('db_ROMs')
        self.FAV_JSON_FILE_PATH       = pluginDataDir.join('favourites.json')
        self.RECENT_PLAYED_FILE_PATH  = pluginDataDir.join('history.json')
        self.MOST_PLAYED_FILE_PATH    = pluginDataDir.join('most_played.json')
        self.COLLECTIONS_FILE_PATH    = pluginDataDir.join('collections.xml')
        self.COLLECTIONS_DIR          = pluginDataDir.join('db_Collections')
        self.VIRTUAL_CAT_TITLE_DIR    = pluginDataDir.join('db_title')
        self.VIRTUAL_CAT_YEARS_DIR    = pluginDataDir.join('db_years')
        self.VIRTUAL_CAT_GENRE_DIR    = pluginDataDir.join('db_genre')
        self.VIRTUAL_CAT_STUDIO_DIR   = pluginDataDir.join('db_studio')
        self.VIRTUAL_CAT_CATEGORY_DIR = pluginDataDir.join('db_category')

    def create(self, launcherID, categoryID, rom_base_noext = None):
        
        # --- ROM in Favourites ---
        if categoryID == VCATEGORY_FAVOURITES_ID and launcherID == VLAUNCHER_FAVOURITES_ID:
            return FavouritesRomSet(self.FAV_JSON_FILE_PATH)
        
        # --- ROM in Most played ROMs ---
        elif categoryID == VCATEGORY_MOST_PLAYED_ID and launcherID == VLAUNCHER_MOST_PLAYED_ID:
            return FavouritesRomSet(self.MOST_PLAYED_FILE_PATH)

        # --- ROM in Recently played ROMs list ---
        elif categoryID == VCATEGORY_RECENT_ID and launcherID == VLAUNCHER_RECENT_ID:
            return RecentlyPlayedRomSet(self.RECENT_PLAYED_FILE_PATH)

        # --- ROM in Collection ---
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            return CollectionRomSet(self.COLLECTIONS_FILE_PATH, self.COLLECTIONS_DIR, launcherID)

        # --- ROM in Virtual Launcher ---
        elif categoryID == VCATEGORY_TITLE_ID:
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_TITLE_DIR, launcherID)
        elif categoryID == VCATEGORY_YEARS_ID:
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_YEARS_DIR, launcherID)
        elif categoryID == VCATEGORY_GENRE_ID:
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_GENRE_DIR, launcherID)
        elif categoryID == VCATEGORY_STUDIO_ID:
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_STUDIO_DIR, launcherID)
        elif categoryID == VCATEGORY_CATEGORY_ID:
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_CATEGORY_DIR, launcherID)
            
        return StandardRomSet(self.ROMS_DIR, rom_base_noext)

class RomSet():
    __metaclass__ = ABCMeta
    
    def __init__(self, romsDir):
        self.romsDir = romsDir
    
    @abstractmethod
    def loadRoms(self):
        return None
    
    @abstractmethod
    def loadRom(self, romId):
        return None

class StandardRomSet(RomSet):
    
    def __init__(self, romsDir, roms_base_noext):
        
        self.roms_base_noext = roms_base_noext
        super(StandardRomSet, self).__init__(romsDir)

    def loadRoms(self):
        
        log_info('StandardRomSet() Loading ROM in Launcher ...')
        roms = fs_load_ROMs_JSON(self.romsDir, self.roms_base_noext)
        return roms

    def loadRom(self, romId):
        
        roms = self.loadRoms()

        if roms is None:
            log_error("StandardRomSet(): Could not load roms")
            return None

        romData = roms[romId]
        
        if romData is None:
            log_warning("StandardRomSet(): Rom with ID '{0}' not found".format(romID))
            return None

        return romData

class FavouritesRomSet(StandardRomSet):

    def __init__(self, romsDir):
        super(FavouritesRomSet, self).__init__(romsDir, None)

    def loadRoms(self):
        log_info('FavouritesRomSet() Loading ROMs in Favourites ...')
        roms = fs_load_Favourites_JSON(self.romsDir)
        return roms


class VirtualLauncherRomSet(StandardRomSet):
    
    def __init__(self, romsDir, launcherID):

        self.launcherID = launcherID
        super(VirtualLauncherRomSet, self).__init__(romsDir, None)

    def loadRoms(self):
        log_info('VirtualCategoryRomSet() Loading ROMs in Virtual Launcher ...')
        roms = fs_load_VCategory_ROMs_JSON(self.romsDir, self.launcherID)
        return roms

class RecentlyPlayedRomSet(RomSet):
    
    def loadRoms(self):
        log_info('RecentlyPlayedRomSet() Loading ROMs in Recently Played ROMs ...')
        roms = fs_load_Collection_ROMs_JSON(self.romsDir)
        return roms
    
    def loadRom(self, romId):
        
        roms = self.loadRoms()

        if roms is None:
            log_error("RecentlyPlayedRomSet(): Could not load roms")
            return None
        
        current_ROM_position = fs_collection_ROM_index_by_romID(romId, roms)
        if current_ROM_position < 0:
            kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
            return None
            
        romData = roms[current_ROM_position]
        
        if romData is None:
            log_warning("RecentlyPlayedRomSet(): Rom with ID '{0}' not found".format(romId))
            return None

        return romData

class CollectionRomSet(RomSet):
    
    def __init__(self, romsDir, collection_dir, launcherID):

        self.collection_dir = collection_dir
        self.launcherID = launcherID
        super(CollectionRomSet, self).__init__(romsDir)

    def loadRoms(self):
        log_info('CollectionRomSet() Loading ROMs in Collection ...')

        (collections, update_timestamp) = fs_load_Collection_index_XML(self.romsDir)
        collection = collections[launcherID]
        roms_json_file = self.collection_dir.join(collection['roms_base_noext'] + '.json')
        roms = fs_load_Collection_ROMs_JSON(roms_json_file)

        return roms
    
    def loadRom(self, romId):
        
        roms = self.loadRoms()

        current_ROM_position = fs_collection_ROM_index_by_romID(romId, roms)
        if current_ROM_position < 0:
            kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
            return
            
        romData = roms[current_ROM_position]
        
        if romData is None:
            log_warning("CollectionRomSet(): Rom with ID '{0}' not found".format(romId))
            return None

        return romData