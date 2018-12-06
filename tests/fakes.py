from abc import ABCMeta, abstractmethod

from resources.objects import *
from resources.utils import *
from resources.scrap import *

class FakeRomSetRepository(ROMSetRepository):
    
    def __init__(self, roms):
        self.roms = roms
    
    def find_by_launcher(self, launcher):
        return self.roms
    
    def save_rom_set(self, launcher, roms):
        self.roms = roms

    def delete_all_by_launcher(self, launcher):
        self.roms = {}      

class FakeExecutor(ExecutorABC):
    
    def getActualApplication(self):
        return self.actualApplication

    def getActualArguments(self):
        return self.actualArgs

    def execute(self, application, arguments, non_blocking):
        self.actualApplication = application
        self.actualArgs = arguments
        pass    

class FakeClass():

    def FakeMethod(self, value, key, launcher):
        self.value = value

class FakeFile(KodiFileName):
    
    def __init__(self, pathString):
        self.fakeContent  = ''
        self.originalPath = pathString
        self.path         = pathString

    def setFakeContent(self, content):
        self.fakeContent = content

    def getFakeContent(self):
        return self.fakeContent
    
    def readAllUnicode(self, encoding='utf-8'):
        contents = self.fakeContent
        return unicode(contents, encoding)

    def write(self, bytes):
       self.fakeContent = self.fakeContent + bytes
      
    def writeAll(self, bytes, flags='w'):
       self.fakeContent = self.fakeContent + bytes
       
    def pjoin(self, *args):
        return self

    def switchExtension(self, targetExt):
        switched_fake = super(FakeFile, self).switchExtension(targetExt)
        switched_fake.setFakeContent(self.fakeContent)
        return switched_fake

    #backwards compatiblity
    def __create__(self, path):
        return FakeFile(path)

class Fake_Paths:
    def __init__(self, fake_base, fake_addon_id = 'ael-tests'):

        # --- Base paths ---
        self.ADDONS_DATA_DIR  = FileName(fake_base, isdir = True)
        self.ADDON_DATA_DIR   = self.ADDONS_DATA_DIR.pjoin(fake_addon_id, isdir = True)
        self.PROFILE_DIR      = self.ADDONS_DATA_DIR.pjoin('profile', isdir = True)
        self.HOME_DIR         = self.ADDONS_DATA_DIR.pjoin('home', isdir = True)
        self.ADDONS_DIR       = self.HOME_DIR.pjoin('addons', isdir = True)
        self.ADDON_CODE_DIR   = self.ADDONS_DIR.pjoin(fake_addon_id, isdir = True)
        self.ICON_FILE_PATH   = self.ADDON_CODE_DIR.pjoin('media/icon.png')
        self.FANART_FILE_PATH = self.ADDON_CODE_DIR.pjoin('media/fanart.jpg')

        # --- Databases and reports ---
        self.CATEGORIES_FILE_PATH      = self.ADDON_DATA_DIR.pjoin('categories.xml')
        self.FAV_JSON_FILE_PATH        = self.ADDON_DATA_DIR.pjoin('favourites.json')
        self.COLLECTIONS_FILE_PATH     = self.ADDON_DATA_DIR.pjoin('collections.xml')
        self.VCAT_TITLE_FILE_PATH      = self.ADDON_DATA_DIR.pjoin('vcat_title.xml')
        self.VCAT_YEARS_FILE_PATH      = self.ADDON_DATA_DIR.pjoin('vcat_years.xml')
        self.VCAT_GENRE_FILE_PATH      = self.ADDON_DATA_DIR.pjoin('vcat_genre.xml')
        self.VCAT_DEVELOPER_FILE_PATH  = self.ADDON_DATA_DIR.pjoin('vcat_developers.xml')
        self.VCAT_NPLAYERS_FILE_PATH   = self.ADDON_DATA_DIR.pjoin('vcat_nplayers.xml')
        self.VCAT_ESRB_FILE_PATH       = self.ADDON_DATA_DIR.pjoin('vcat_esrb.xml')
        self.VCAT_RATING_FILE_PATH     = self.ADDON_DATA_DIR.pjoin('vcat_rating.xml')
        self.VCAT_CATEGORY_FILE_PATH   = self.ADDON_DATA_DIR.pjoin('vcat_category.xml')
        # Launcher app stdout/stderr file
        self.LAUNCH_LOG_FILE_PATH      = self.ADDON_DATA_DIR.pjoin('launcher.log')
        self.RECENT_PLAYED_FILE_PATH   = self.ADDON_DATA_DIR.pjoin('history.json')
        self.MOST_PLAYED_FILE_PATH     = self.ADDON_DATA_DIR.pjoin('most_played.json')
        self.BIOS_REPORT_FILE_PATH     = self.ADDON_DATA_DIR.pjoin('report_BIOS.txt')
        self.LAUNCHER_REPORT_FILE_PATH = self.ADDON_DATA_DIR.pjoin('report_Launchers.txt')

        # --- Offline scraper databases ---
        self.GAMEDB_INFO_DIR           = self.ADDON_CODE_DIR.pjoin('GameDBInfo', isdir = True)
        self.GAMEDB_JSON_BASE_NOEXT    = 'GameDB_info'
        self.LAUNCHBOX_INFO_DIR        = self.ADDON_CODE_DIR.pjoin('LaunchBox', isdir = True)
        self.LAUNCHBOX_JSON_BASE_NOEXT = 'LaunchBox_info'

        # --- Artwork and NFO for Categories and Launchers ---
        self.CATEGORIES_ASSET_DIR      = self.ADDON_DATA_DIR.pjoin('asset-categories', isdir = True)
        self.COLLECTIONS_ASSET_DIR     = self.ADDON_DATA_DIR.pjoin('asset-collections', isdir = True)
        self.LAUNCHERS_ASSET_DIR       = self.ADDON_DATA_DIR.pjoin('asset-launchers', isdir = True)
        self.FAVOURITES_ASSET_DIR      = self.ADDON_DATA_DIR.pjoin('asset-favourites', isdir = True)
        self.VIRTUAL_CAT_TITLE_DIR     = self.ADDON_DATA_DIR.pjoin('db_title', isdir = True)
        self.VIRTUAL_CAT_YEARS_DIR     = self.ADDON_DATA_DIR.pjoin('db_year', isdir = True)
        self.VIRTUAL_CAT_GENRE_DIR     = self.ADDON_DATA_DIR.pjoin('db_genre', isdir = True)
        self.VIRTUAL_CAT_DEVELOPER_DIR = self.ADDON_DATA_DIR.pjoin('db_developer', isdir = True)
        self.VIRTUAL_CAT_NPLAYERS_DIR  = self.ADDON_DATA_DIR.pjoin('db_nplayer', isdir = True)
        self.VIRTUAL_CAT_ESRB_DIR      = self.ADDON_DATA_DIR.pjoin('db_esrb', isdir = True)
        self.VIRTUAL_CAT_RATING_DIR    = self.ADDON_DATA_DIR.pjoin('db_rating', isdir = True)
        self.VIRTUAL_CAT_CATEGORY_DIR  = self.ADDON_DATA_DIR.pjoin('db_category', isdir = True)
        self.ROMS_DIR                  = self.ADDON_DATA_DIR.pjoin('db_ROMs', isdir = True)
        self.COLLECTIONS_DIR           = self.ADDON_DATA_DIR.pjoin('db_Collections', isdir = True)
        self.REPORTS_DIR               = self.ADDON_DATA_DIR.pjoin('reports', isdir = True)

class FakeScraper(Scraper):
    
    def __init__(self, settings, launcher, rom_data_to_apply = None):
        self.rom_data_to_apply = rom_data_to_apply
        scraper_settings = ScraperSettings(1,1,False,True)
        super(FakeScraper, self).__init__(scraper_settings, launcher, True, []) 

    def getName(self):
        return 'FakeScraper'

    def _get_candidates(self, searchTerm, romPath, rom):
        return ['fake']

    def _load_metadata(self, candidate, romPath, rom):
        if self.rom_data_to_apply :
            self.gamedata['title']      = self.rom_data_to_apply['m_name'] if 'm_name' in self.rom_data_to_apply else ''
            self.gamedata['year']      = self.rom_data_to_apply['m_year'] if 'm_year' in self.rom_data_to_apply else ''   
            self.gamedata['genre']     = self.rom_data_to_apply['m_genre'] if 'm_genre' in self.rom_data_to_apply else ''
            self.gamedata['developer'] = self.rom_data_to_apply['m_developer']if 'm_developer' in self.rom_data_to_apply else ''
            self.gamedata['plot']      = self.rom_data_to_apply['m_plot'] if 'm_plot' in self.rom_data_to_apply else ''
        else:
            self.gamedata['title'] = romPath.getBase_noext()

    
    def _load_assets(self, candidate, romPath, rom):
        pass
        