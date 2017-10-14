from abc import ABCMeta, abstractmethod

import os
from collections import OrderedDict

# --- Kodi stuff ---
import xbmc

# --- Modules/packages in this plugin ---
from constants import *
from disk_IO import *
from utils import *
from utils_kodi import *

class RomSetFactory():
    
    def __init__(self, pluginDataDir):

        self.ROMS_DIR                   = pluginDataDir.pjoin('db_ROMs')
        self.FAV_JSON_FILE_PATH         = pluginDataDir.pjoin('favourites.json')
        self.RECENT_PLAYED_FILE_PATH    = pluginDataDir.pjoin('history.json')
        self.MOST_PLAYED_FILE_PATH      = pluginDataDir.pjoin('most_played.json')
        self.COLLECTIONS_FILE_PATH      = pluginDataDir.pjoin('collections.xml')
        self.COLLECTIONS_DIR            = pluginDataDir.pjoin('db_Collections')
        self.VIRTUAL_CAT_TITLE_DIR      = pluginDataDir.pjoin('db_title')
        self.VIRTUAL_CAT_YEARS_DIR      = pluginDataDir.pjoin('db_years')
        self.VIRTUAL_CAT_GENRE_DIR      = pluginDataDir.pjoin('db_genre')
        self.VIRTUAL_CAT_DEVELOPER_DIR  = pluginDataDir.pjoin('db_developer')
        self.VIRTUAL_CAT_CATEGORY_DIR   = pluginDataDir.pjoin('db_category')
        self.VIRTUAL_CAT_NPLAYERS_DIR   = pluginDataDir.pjoin('db_nplayers')
        self.VIRTUAL_CAT_ESRB_DIR       = pluginDataDir.pjoin('db_esrb')
        self.VIRTUAL_CAT_RATING_DIR     = pluginDataDir.pjoin('db_rating')

        if not self.ROMS_DIR.exists():                  self.ROMS_DIR.makedirs()
        if not self.VIRTUAL_CAT_TITLE_DIR.exists():     self.VIRTUAL_CAT_TITLE_DIR.makedirs()
        if not self.VIRTUAL_CAT_YEARS_DIR.exists():     self.VIRTUAL_CAT_YEARS_DIR.makedirs()
        if not self.VIRTUAL_CAT_GENRE_DIR.exists():     self.VIRTUAL_CAT_GENRE_DIR.makedirs()
        if not self.VIRTUAL_CAT_DEVELOPER_DIR.exists(): self.VIRTUAL_CAT_DEVELOPER_DIR.makedirs()
        if not self.VIRTUAL_CAT_CATEGORY_DIR.exists():  self.VIRTUAL_CAT_CATEGORY_DIR.makedirs()
        if not self.VIRTUAL_CAT_NPLAYERS_DIR.exists():  self.VIRTUAL_CAT_NPLAYERS_DIR.makedirs()
        if not self.VIRTUAL_CAT_ESRB_DIR.exists():      self.VIRTUAL_CAT_ESRB_DIR.makedirs()
        if not self.VIRTUAL_CAT_RATING_DIR.exists():    self.VIRTUAL_CAT_RATING_DIR.makedirs()
        if not self.COLLECTIONS_DIR.exists():           self.COLLECTIONS_DIR.makedirs()

    def create(self, categoryID, launcherID, launchers):
        
        log_debug('romsetfactory.create(): categoryID={0}'.format(categoryID))
        log_debug('romsetfactory.create(): launcherID={0}'.format(launcherID))
        
        launcher = None
        if launcherID in launchers:
            launcher = launchers[launcherID]
        else:
            log_warning('romsetfactory.create(): Launcher "{0}" not found in launchers'.format(launcherID))

        description = self.createDescription(categoryID)

        # --- ROM in Favourites ---
        if categoryID == VCATEGORY_FAVOURITES_ID and launcherID == VLAUNCHER_FAVOURITES_ID:
            return FavouritesRomSet(self.FAV_JSON_FILE_PATH, launcher, description)
                
        # --- ROM in Most played ROMs ---
        elif categoryID == VCATEGORY_MOST_PLAYED_ID and launcherID == VLAUNCHER_MOST_PLAYED_ID:
            return FavouritesRomSet(self.MOST_PLAYED_FILE_PATH, launcher, description)

        # --- ROM in Recently played ROMs list ---
        elif categoryID == VCATEGORY_RECENT_ID and launcherID == VLAUNCHER_RECENT_ID:
            return RecentlyPlayedRomSet(self.RECENT_PLAYED_FILE_PATH, launcher, description)

        # --- ROM in Collection ---
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            return CollectionRomSet(self.COLLECTIONS_FILE_PATH, launcher, self.COLLECTIONS_DIR, launcherID, description)

        # --- ROM in Virtual Launcher ---
        elif categoryID == VCATEGORY_TITLE_ID:
            log_info('RomSetFactory() loading ROM set Title Virtual Launcher ...')
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_TITLE_DIR, launcher, launcherID, description)
        elif categoryID == VCATEGORY_YEARS_ID:
            log_info('RomSetFactory() loading ROM set Years Virtual Launcher ...')
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_YEARS_DIR, launcher, launcherID, description)
        elif categoryID == VCATEGORY_GENRE_ID:
            log_info('RomSetFactory() loading ROM set Genre Virtual Launcher ...')
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_GENRE_DIR, launcher, launcherID, description)
        elif categoryID == VCATEGORY_DEVELOPER_ID:
            log_info('RomSetFactory() loading ROM set Studio Virtual Launcher ...')
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_DEVELOPER_DIR, launcher, launcherID, description)
        elif categoryID == VCATEGORY_NPLAYERS_ID:
            log_info('RomSetFactory() loading ROM set NPlayers Virtual Launcher ...')
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_NPLAYERS_DIR, launcher, launcherID, description)
        elif categoryID == VCATEGORY_ESRB_ID:
            log_info('RomSetFactory() loading ROM set ESRB Virtual Launcher ...')
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_ESRB_DIR, launcher, launcherID, description)
        elif categoryID == VCATEGORY_RATING_ID:
            log_info('RomSetFactory() loading ROM set Rating Virtual Launcher ...')
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_RATING_DIR, launcher, launcherID, description)
        elif categoryID == VCATEGORY_CATEGORY_ID:
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_CATEGORY_DIR, launcher, launcherID, description)
          
        elif categoryID == VCATEGORY_PCLONES_ID \
            and 'launcher_display_mode' in launcher \
            and launcher['launcher_display_mode'] != LAUNCHER_DMODE_FLAT:
            return PcloneRomSet(self.ROMS_DIR, launcher, description)
        
        log_info('RomSetFactory() loading standard romset...')
        return StandardRomSet(self.ROMS_DIR, launcher, description)

    def createDescription(self, categoryID):
         
        if categoryID == VCATEGORY_FAVOURITES_ID:
            return RomSetDescription('Favourite', 'Browse favourites')
        elif categoryID == VCATEGORY_MOST_PLAYED_ID:
            return RomSetDescription('Most Played ROM', 'Browse most played')
        elif categoryID == VCATEGORY_RECENT_ID:
            return RomSetDescription('Recently played ROM', 'Browse by recently played')
        elif categoryID == VCATEGORY_TITLE_ID:
            return RomSetDescription('Virtual Launcher Title', 'Browse by Title')
        elif categoryID == VCATEGORY_YEARS_ID:
            return RomSetDescription('Virtual Launcher Years', 'Browse by Year')
        elif categoryID == VCATEGORY_GENRE_ID:
            return RomSetDescription('Virtual Launcher Genre', 'Browse by Genre')
        elif categoryID == VCATEGORY_DEVELOPER_ID:
            return RomSetDescription('Virtual Launcher Studio','Browse by Studio')
        elif categoryID == VCATEGORY_NPLAYERS_ID:
            return RomSetDescription('Virtual Launcher NPlayers', 'Browse by Number of Players')
        elif categoryID == VCATEGORY_ESRB_ID:
            return RomSetDescription('Virtual Launcher ESRB', 'Browse by ESRB Rating')
        elif categoryID == VCATEGORY_RATING_ID:
            return RomSetDescription('Virtual Launcher Rating', 'Browse by User Rating')
        elif categoryID == VCATEGORY_CATEGORY_ID:
            return RomSetDescription('Virtual Launcher Category', 'Browse by Category')

        
       #if virtual_categoryID == VCATEGORY_TITLE_ID:
       #    vcategory_db_filename = VCAT_TITLE_FILE_PATH
       #    vcategory_name        = 'Browse by Title'
       #elif virtual_categoryID == VCATEGORY_YEARS_ID:
       #    vcategory_db_filename = VCAT_YEARS_FILE_PATH
       #    vcategory_name        = 'Browse by Year'
       #elif virtual_categoryID == VCATEGORY_GENRE_ID:
       #    vcategory_db_filename = VCAT_GENRE_FILE_PATH
       #    vcategory_name        = 'Browse by Genre'
       #elif virtual_categoryID == VCATEGORY_STUDIO_ID:
       #    vcategory_db_filename = VCAT_STUDIO_FILE_PATH
       #    vcategory_name        = 'Browse by Studio'
       #elif virtual_categoryID == VCATEGORY_NPLAYERS_ID:
       #    vcategory_db_filename = VCAT_NPLAYERS_FILE_PATH
       #    vcategory_name        = 'Browse by Number of Players'
       #elif virtual_categoryID == VCATEGORY_ESRB_ID:
       #    vcategory_db_filename = VCAT_ESRB_FILE_PATH
       #    vcategory_name        = 'Browse by ESRB Rating'
       #elif virtual_categoryID == VCATEGORY_RATING_ID:
       #    vcategory_db_filename = VCAT_RATING_FILE_PATH
       #    vcategory_name        = 'Browse by User Rating'
       #elif virtual_categoryID == VCATEGORY_CATEGORY_ID:
       #    vcategory_db_filename = VCAT_CATEGORY_FILE_PATH
       #    vcategory_name        = 'Browse by Category'

        return None

class RomSetDescription():

    def __init__(self, title, description, isRegularLauncher = False):
        
        self.title = title
        self.description = description

        self.isRegularLauncher = isRegularLauncher

class RomSet():
    __metaclass__ = ABCMeta
    
    def __init__(self, romsDir, launcher, description):
        self.romsDir = romsDir
        self.launcher = launcher
        
        self.description = description
        
    @abstractmethod
    def romSetFileExists(self):
        return False

    @abstractmethod
    def loadRoms(self):
        return {}
    
    @abstractmethod
    def loadRomsAsList(self):
        return []

    @abstractmethod
    def loadRom(self, romId):
        return None

    @abstractmethod
    def saveRoms(self, roms):
        pass
    
class StandardRomSet(RomSet):
    
    def __init__(self, romsDir, launcher, description):
        
        self.roms_base_noext = launcher['roms_base_noext'] if launcher is not None and 'roms_base_noext' in launcher else None
        self.view_mode = launcher['launcher_display_mode'] if launcher is not None and 'launcher_display_mode' in launcher else None

        if self.roms_base_noext is None:
            self.repositoryFile = romsDir
        elif self.view_mode == LAUNCHER_DMODE_FLAT:
            self.repositoryFile = romsDir.pjoin(self.roms_base_noext + '.json')
        else:
            self.repositoryFile = romsDir.pjoin(self.roms_base_noext + '_parents.json')

        super(StandardRomSet, self).__init__(romsDir, launcher, description)

    def romSetFileExists(self):
        return self.repositoryFile.exists()

    def loadRoms(self):

        if not self.romSetFileExists():
            log_warning('Launcher "{0}" JSON not found.'.format(self.roms_base_noext))
            return None

        log_info('StandardRomSet() Loading ROMs in Launcher ...')
        # was disk_IO.fs_load_ROMs_JSON()
        roms = {}
        # --- Parse using json module ---
        # >> On Github issue #8 a user had an empty JSON file for ROMs. This raises
        #    exception exceptions.ValueError and launcher cannot be deleted. Deal
        #    with this exception so at least launcher can be rescanned.
        log_verb('StandardRomSet.loadRoms() FILE  {0}'.format(self.repositoryFile.getOriginalPath()))
        try:
            roms = self.repositoryFile.readJson()
        except ValueError:
            statinfo = roms_json_file.stat()
            log_error('StandardRomSet.loadRoms() ValueError exception in json.load() function')
            log_error('StandardRomSet.loadRoms() Dir  {0}'.format(self.repositoryFile.getOriginalPath()))
            log_error('StandardRomSet.loadRoms() Size {0}'.format(statinfo.st_size))

        return roms

    def loadRomsAsList(self):
        roms_dict = self.loadRoms()
        roms = []
        for key in roms_dict:
            roms.append(roms_dict[key])

        return roms

    def loadRom(self, romId):
        
        roms = self.loadRoms()

        if roms is None:
            log_error("StandardRomSet(): Could not load roms")
            return None

        romData = roms[romId]
        
        if romData is None:
            log_warning("StandardRomSet(): Rom with ID '{0}' not found".format(romId))
            return None

        return romData

    def saveRoms(self, roms):
        fs_write_ROMs_JSON(self.repositoryFile, self.launcher, roms)
        pass

class PcloneRomSet(StandardRomSet):

    def __init__(self, romsDir, launcher, description):

        super(PcloneRomSet, self).__init__(romsDir, launcher, description)
        
        self.roms_base_noext = launcher['roms_base_noext'] if launcher is not None and 'roms_base_noext' in launcher else None
        self.repositoryFile = self.romsDir.pjoin(self.roms_base_noext + '_index_PClone.json')

class FavouritesRomSet(StandardRomSet):
    
    def loadRoms(self):
        log_info('FavouritesRomSet() Loading ROMs in Favourites ...')
        roms = fs_load_Favourites_JSON(self.repositoryFile)
        return roms

    def saveRoms(self, roms):
        log_info('FavouritesRomSet() Saving Favourites ROMs ...')
        fs_write_Favourites_JSON(self.repositoryFile, roms)

class VirtualLauncherRomSet(StandardRomSet):
    
    def __init__(self, romsDir, launcher, launcherID, description):

        self.launcherID = launcherID
        super(VirtualLauncherRomSet, self).__init__(romsDir, launcher, description)

    def romSetFileExists(self):
        hashed_db_filename = self.romsDir.pjoin(self.launcherID + '.json')
        return hashed_db_filename.exists()

    def loadRoms(self):

        if not self.romSetFileExists():
            log_warning('VirtualCategory "{0}" JSON not found.'.format(self.launcherID))
            return None

        log_info('VirtualCategoryRomSet() Loading ROMs in Virtual Launcher ...')
        roms = fs_load_VCategory_ROMs_JSON(self.romsDir, self.launcherID)
        return roms

    def saveRoms(self, roms):
        fs_write_Favourites_JSON(self.romsDir, roms)
        pass

class RecentlyPlayedRomSet(RomSet):
    
    def romSetFileExists(self):
        return self.romsDir.exists()
    
    def loadRoms(self):
        log_info('RecentlyPlayedRomSet() Loading ROMs in Recently Played ROMs ...')
        romsList = self.loadRomsAsList()
        
        roms = OrderedDict()
        for rom in romsList:
            roms[rom['id']] = rom
            
        return roms
    
    def loadRomsAsList(self):
        roms = fs_load_Collection_ROMs_JSON(self.romsDir)
        return roms

    def loadRom(self, romId):
        
        roms = self.loadRomsAsList()

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

    
    def saveRoms(self, roms):
        fs_write_Collection_ROMs_JSON(self.romsDir, roms)
        pass

class CollectionRomSet(RomSet):
    
    def __init__(self, romsDir, launcher, collection_dir, launcherID, description):

        self.collection_dir = collection_dir
        self.launcherID = launcherID
        super(CollectionRomSet, self).__init__(romsDir, launcher, description)

    def romSetFileExists(self):
        (collections, update_timestamp) = fs_load_Collection_index_XML(self.romsDir)
        collection = collections[self.launcherID]

        roms_json_file = self.romsDir.pjoin(collection['roms_base_noext'] + '.json')
        return roms_json_file.exists()
    
    def loadRomsAsList(self):
        (collections, update_timestamp) = fs_load_Collection_index_XML(self.romsDir)
        collection = collections[self.launcherID]
        roms_json_file = self.collection_dir.pjoin(collection['roms_base_noext'] + '.json')
        romsList = fs_load_Collection_ROMs_JSON(roms_json_file)
        return romsList

    # NOTE ROMs in a collection are stored as a list and ROMs in Favourites are stored as
    #      a dictionary. Convert the Collection list into an ordered dictionary and then
    #      converted back the ordered dictionary into a list before saving the collection.
    def loadRoms(self):
        log_info('CollectionRomSet() Loading ROMs in Collection ...')

        romsList = self.loadRomsAsList()
        
        roms = OrderedDict()
        for rom in romsList:
            roms[rom['id']] = rom
            
        return roms
    
    def loadRom(self, romId):
        
        roms = self.loadRomsAsList()

        if roms is None:
            log_error("CollectionRomSet(): Could not load roms")
            return None

        current_ROM_position = fs_collection_ROM_index_by_romID(romId, roms)
        if current_ROM_position < 0:
            kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
            return
            
        romData = roms[current_ROM_position]
        
        if romData is None:
            log_warning("CollectionRomSet(): Rom with ID '{0}' not found".format(romId))
            return None

        return romData

    def saveRoms(self, roms):
        
        # >> Convert back the OrderedDict into a list and save Collection
        collection_rom_list = []
        for key in roms:
            collection_rom_list.append(roms[key])

        json_file_path = self.romsDir.pjoin(collection['roms_base_noext'] + '.json')
        fs_write_Collection_ROMs_JSON(json_file_path, collection_rom_list)