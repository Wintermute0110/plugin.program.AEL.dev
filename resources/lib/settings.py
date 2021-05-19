# -*- coding: utf-8 -*-
import xbmcaddon
from resources.lib.utils.io import FileName

# read settings
__addon__ = xbmcaddon.Addon()

def showSettings():
    __addon__.openSettings()


def getSetting(setting):
    return __addon__.getSetting(setting).strip()


def setSetting(setting, value):
    __addon__.setSetting(setting, str(value))


def getSettingAsBool(setting):
    return getSetting(setting).lower() == "true"


def getSettingAsFloat(setting):
    try:
        return float(getSetting(setting))
    except ValueError:
        return 0


def getSettingAsInt(setting):
    try:
        return int(getSettingAsFloat(setting))
    except ValueError:
        return 0

# --- Addon paths and constant definition ---
# _PATH is a filename | _DIR is a directory.
class AEL_Paths(object):
    def __init__(self, addon_id):
        # --- Base paths ---
        self.HOME_DIR         = FileName('special://home')
        self.PROFILE_DIR      = FileName('special://profile')
        self.ADDONS_DATA_DIR  = FileName('special://profile/addon_data')
        self.DATABASE_DIR     = FileName('special://database')
        self.ADDON_DATA_DIR   = self.ADDONS_DATA_DIR.pjoin(addon_id)
        self.ADDONS_CODE_DIR  = self.HOME_DIR.pjoin('addons')
        self.ADDON_CODE_DIR   = self.ADDONS_CODE_DIR.pjoin(addon_id)
        self.ICON_FILE_PATH   = self.ADDON_CODE_DIR.pjoin('media/icon.png')
        self.FANART_FILE_PATH = self.ADDON_CODE_DIR.pjoin('media/fanart.jpg')
        self.DATABASE_SCHEMA_PATH = self.ADDON_CODE_DIR.pjoin('resources/schema.sql')

        # -- Root data file
        self.ROOT_PATH        = self.ADDON_DATA_DIR.pjoin('root.json')
        
        # --- Databases and reports ---
        self.CATEGORIES_FILE_PATH      = self.ADDON_DATA_DIR.pjoin('categories.xml')
        self.CONTAINERS_FILE_PATH      = self.ADDON_DATA_DIR.pjoin('containers.json')
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
        self.LAUNCH_LOG_FILE_PATH      = self.ADDON_DATA_DIR.pjoin('launcher.log')
        self.RECENT_PLAYED_FILE_PATH   = self.ADDON_DATA_DIR.pjoin('history.json')
        self.MOST_PLAYED_FILE_PATH     = self.ADDON_DATA_DIR.pjoin('most_played.json')
        self.DATABASE_FILE_PATH        = self.DATABASE_DIR.pjoin('ael.db')

        # Reports
        self.BIOS_REPORT_FILE_PATH = self.ADDON_DATA_DIR.pjoin('report_BIOS.txt')
        self.LAUNCHER_REPORT_FILE_PATH = self.ADDON_DATA_DIR.pjoin('report_Launchers.txt')
        self.ROM_SYNC_REPORT_FILE_PATH = self.ADDON_DATA_DIR.pjoin('report_ROM_sync_status.txt')
        self.ROM_ART_INTEGRITY_REPORT_FILE_PATH = self.ADDON_DATA_DIR.pjoin('report_ROM_artwork_integrity.txt')

        # --- Offline scraper databases ---
        self.GAMEDB_INFO_DIR           = self.ADDON_CODE_DIR.pjoin('data-AOS')
        self.GAMEDB_JSON_BASE_NOEXT    = 'AOS_GameDB_info'
        # self.LAUNCHBOX_INFO_DIR        = self.ADDON_CODE_DIR.pjoin('LaunchBox')
        # self.LAUNCHBOX_JSON_BASE_NOEXT = 'LaunchBox_info'

        # --- Online scraper on-disk cache ---
        self.SCRAPER_CACHE_DIR = self.ADDON_DATA_DIR.pjoin('ScraperCache')

        # --- Artwork and NFO for Categories and Launchers ---
        self.DEFAULT_CAT_ASSET_DIR     = self.ADDON_DATA_DIR.pjoin('asset-categories')
        self.DEFAULT_COL_ASSET_DIR     = self.ADDON_DATA_DIR.pjoin('asset-collections')
        self.DEFAULT_LAUN_ASSET_DIR    = self.ADDON_DATA_DIR.pjoin('asset-launchers')
        self.DEFAULT_FAV_ASSET_DIR     = self.ADDON_DATA_DIR.pjoin('asset-favourites')
        self.VIRTUAL_CAT_TITLE_DIR     = self.ADDON_DATA_DIR.pjoin('db_title')
        self.VIRTUAL_CAT_YEARS_DIR     = self.ADDON_DATA_DIR.pjoin('db_year')
        self.VIRTUAL_CAT_GENRE_DIR     = self.ADDON_DATA_DIR.pjoin('db_genre')
        self.VIRTUAL_CAT_DEVELOPER_DIR = self.ADDON_DATA_DIR.pjoin('db_developer')
        self.VIRTUAL_CAT_NPLAYERS_DIR  = self.ADDON_DATA_DIR.pjoin('db_nplayer')
        self.VIRTUAL_CAT_ESRB_DIR      = self.ADDON_DATA_DIR.pjoin('db_esrb')
        self.VIRTUAL_CAT_RATING_DIR    = self.ADDON_DATA_DIR.pjoin('db_rating')
        self.VIRTUAL_CAT_CATEGORY_DIR  = self.ADDON_DATA_DIR.pjoin('db_category')
        self.ROMS_DIR                  = self.ADDON_DATA_DIR.pjoin('db_ROMs')
        self.COLLECTIONS_DIR           = self.ADDON_DATA_DIR.pjoin('db_Collections')
        self.REPORTS_DIR               = self.ADDON_DATA_DIR.pjoin('reports')

    def build(self):
        # --- Addon data paths creation ---
        if not self.ADDON_DATA_DIR.exists():            self.ADDON_DATA_DIR.makedirs()
        if not self.SCRAPER_CACHE_DIR.exists():         self.SCRAPER_CACHE_DIR.makedirs()
        if not self.DEFAULT_CAT_ASSET_DIR.exists():     self.DEFAULT_CAT_ASSET_DIR.makedirs()
        if not self.DEFAULT_COL_ASSET_DIR.exists():     self.DEFAULT_COL_ASSET_DIR.makedirs()
        if not self.DEFAULT_LAUN_ASSET_DIR.exists():    self.DEFAULT_LAUN_ASSET_DIR.makedirs()
        if not self.DEFAULT_FAV_ASSET_DIR.exists():     self.DEFAULT_FAV_ASSET_DIR.makedirs()
        if not self.VIRTUAL_CAT_TITLE_DIR.exists():     self.VIRTUAL_CAT_TITLE_DIR.makedirs()
        if not self.VIRTUAL_CAT_YEARS_DIR.exists():     self.VIRTUAL_CAT_YEARS_DIR.makedirs()
        if not self.VIRTUAL_CAT_GENRE_DIR.exists():     self.VIRTUAL_CAT_GENRE_DIR.makedirs()
        if not self.VIRTUAL_CAT_DEVELOPER_DIR.exists(): self.VIRTUAL_CAT_DEVELOPER_DIR.makedirs()
        if not self.VIRTUAL_CAT_NPLAYERS_DIR.exists():  self.VIRTUAL_CAT_NPLAYERS_DIR.makedirs()
        if not self.VIRTUAL_CAT_ESRB_DIR.exists():      self.VIRTUAL_CAT_ESRB_DIR.makedirs()
        if not self.VIRTUAL_CAT_RATING_DIR.exists():    self.VIRTUAL_CAT_RATING_DIR.makedirs()
        if not self.VIRTUAL_CAT_CATEGORY_DIR.exists():  self.VIRTUAL_CAT_CATEGORY_DIR.makedirs()
        if not self.ROMS_DIR.exists():                  self.ROMS_DIR.makedirs()
        if not self.COLLECTIONS_DIR.exists():           self.COLLECTIONS_DIR.makedirs()
        if not self.REPORTS_DIR.exists():               self.REPORTS_DIR.makedirs()

        return self