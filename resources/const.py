# -*- coding: utf-8 -*-

# Copyright (c) 2016-2022 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# Advanced Emulator/MAME Launcher constants and globals.
# This module has no external dependencies.
# This module does no use print() or log functions.

# --- Transitional code from Python 2 to Python 3 ---
# See https://github.com/benjaminp/six/blob/master/six.py
import sys
ADDON_RUNNING_PYTHON_2 = sys.version_info[0] == 2
ADDON_RUNNING_PYTHON_3 = sys.version_info[0] == 3
if ADDON_RUNNING_PYTHON_3:
    text_type = str
    binary_type = bytes
elif ADDON_RUNNING_PYTHON_2:
    text_type = unicode
    binary_type = str
else:
    raise TypeError('Unknown Python runtime version')

# --- Determine interpreter running platform ---
# Cache all possible platform values in global variables for maximum speed.
# See http://stackoverflow.com/questions/446209/possible-values-from-sys-platform
cached_sys_platform = sys.platform
def _aux_is_android():
    if not cached_sys_platform.startswith('linux'): return False
    return 'ANDROID_ROOT' in os.environ or 'ANDROID_DATA' in os.environ or 'XBMC_ANDROID_APK' in os.environ

is_windows_bool = cached_sys_platform == 'win32' or cached_sys_platform == 'win64' or cached_sys_platform == 'cygwin'
is_osx_bool = cached_sys_platform.startswith('darwin')
is_android_bool = _aux_is_android()
is_linux_bool = cached_sys_platform.startswith('linux') and not is_android_bool

def is_windows(): return is_windows_bool
def is_osx(): return is_osx_bool
def is_android(): return is_android_bool
def is_linux(): return is_linux_bool

# ------------------------------------------------------------------------------------------------
# Addon options and tuneables.
# ------------------------------------------------------------------------------------------------
# Compact, smaller size, non-human readable JSON. False forces human-readable JSON for development.
# In AEL speed is not as critical so False is OK.
# In AML this must be True when releasing.
OPTION_COMPACT_JSON = False

# Use less memory when writing big JSON files, but writing is slower.
# In AEL this can be False when releasing.
# In AML it must be True when releasing.
OPTION_LOWMEM_WRITE_JSON = False

# The addon name in the GUI. Title of Kodi dialogs (yesno, progress, etc.) and used also in log functions.
ADDON_LONG_NAME = 'Advanced Emulator Launcher'
ADDON_SHORT_NAME = 'AEL'

# These parameters are used in utils_write_JSON_file() when pprint is True or
# OPTION_COMPACT_JSON is False. Otherwise non-human readable, compact JSON is written.
# pprint = True function parameter overrides option OPTION_COMPACT_JSON.
# More compact JSON files (less blanks) load faster because file size is smaller.
JSON_INDENT = 1
JSON_SEP = (', ', ': ')

# ------------------------------------------------------------------------------------------------
# CUSTOM/DEBUG/TEST settings
# ------------------------------------------------------------------------------------------------
# An integer number incremented whenever there is a change in the ROM storage format.
# This enables easy migrations, at least in theory.
AEL_STORAGE_FORMAT = 1

# ------------------------------------------------------------------------------------------------
# This is to ease printing colors in Kodi.
# ------------------------------------------------------------------------------------------------
KC_RED        = '[COLOR red]'
KC_ORANGE     = '[COLOR orange]'
KC_GREEN      = '[COLOR green]'
KC_YELLOW     = '[COLOR yellow]'
KC_VIOLET     = '[COLOR violet]'
KC_BLUEVIOLET = '[COLOR blueviolet]'
KC_END        = '[/COLOR]'

# ------------------------------------------------------------------------------------------------
# Image file constants.
# ------------------------------------------------------------------------------------------------
# Supported image files in:
# 1. misc_identify_image_id_by_contents()
# 2. misc_identify_image_id_by_ext()
IMAGE_PNG_ID     = 'PNG'
IMAGE_JPEG_ID    = 'JPEG'
IMAGE_GIF_ID     = 'GIF'
IMAGE_BMP_ID     = 'BMP'
IMAGE_TIFF_ID    = 'TIFF'
IMAGE_UKNOWN_ID  = 'Image unknown'
IMAGE_CORRUPT_ID = 'Image corrupt'

IMAGE_IDS = [
    IMAGE_PNG_ID,
    IMAGE_JPEG_ID,
    IMAGE_GIF_ID,
    IMAGE_BMP_ID,
    IMAGE_TIFF_ID,
]

IMAGE_EXTENSIONS = {
    IMAGE_PNG_ID  : ['png'],
    IMAGE_JPEG_ID : ['jpg', 'jpeg'],
    IMAGE_GIF_ID  : ['gif'],
    IMAGE_BMP_ID  : ['bmp'],
    IMAGE_TIFF_ID : ['tif', 'tiff'],
}

# Image file magic numbers. All at file offset 0.
# See https://en.wikipedia.org/wiki/List_of_file_signatures
# b prefix is a byte string in both Python 2 and 3.
IMAGE_MAGIC_DIC = {
    IMAGE_PNG_ID  : [ b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A' ],
    IMAGE_JPEG_ID : [
        b'\xFF\xD8\xFF\xDB',
        b'\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46\x00\x01',
        b'\xFF\xD8\xFF\xEE',
        b'\xFF\xD8\xFF\xE1',
    ],
    IMAGE_GIF_ID  : [
        b'\x47\x49\x46\x38\x37\x61',
        b'\x47\x49\x46\x38\x39\x61',
    ],
    IMAGE_BMP_ID  : [ b'\x42\x4D' ],
    IMAGE_TIFF_ID : [
        b'\x49\x49\x2A\x00',
        b'\x4D\x4D\x00\x2A',
    ]
}

# ------------------------------------------------------------------------------------------------
# Addon constants
# ------------------------------------------------------------------------------------------------
# --- Misc "constants" ---
PLOT_STR_MAXSIZE = 40
RETROPLAYER_LAUNCHER_APP_NAME = 'retroplayer_launcher_app'
LNK_LAUNCHER_APP_NAME = 'lnk_launcher_app'

# Special Category/Launcher IDs.
CATEGORY_ADDONROOT_ID = 'root_category' # This is an actual category, not a virtual one.

# Favourites, Most Played and Recently Played belong to VCATEGORY_SPECIAL_ID category.
# However, having an empty category in URLs for these virtual launchers is OK.
VCATEGORY_SPECIAL_ID = 'vcategory_special'
VCATEGORY_ROM_COLLECTION_ID = 'vcategory_rom_collection'
VCATEGORY_BROWSE_BY_TITLE_ID = 'vcategory_browse_by_title'
VCATEGORY_BROWSE_BY_YEARS_ID = 'vcategory_browse_by_year'
VCATEGORY_BROWSE_BY_GENRE_ID = 'vcategory_browse_by_genre'
VCATEGORY_BROWSE_BY_DEVELOPER_ID = 'vcategory_browse_by_developer'
VCATEGORY_BROWSE_BY_NPLAYERS_ID = 'vcategory_browse_by_nplayer'
VCATEGORY_BROWSE_BY_ESRB_ID = 'vcategory_browse_by_esrb'
VCATEGORY_BROWSE_BY_RATING_ID = 'vcategory_browse_by_rating'
VCATEGORY_BROWSE_BY_CATEGORY_ID = 'vcategory_browse_by_category'
VCATEGORY_AOS_ID = 'vcategory_ael_offline_scraper'

VCATEGORY_BROWSE_BY_ID_LIST = [
    VCATEGORY_BROWSE_BY_TITLE_ID,
    VCATEGORY_BROWSE_BY_YEARS_ID,
    VCATEGORY_BROWSE_BY_GENRE_ID,
    VCATEGORY_BROWSE_BY_DEVELOPER_ID,
    VCATEGORY_BROWSE_BY_NPLAYERS_ID,
    VCATEGORY_BROWSE_BY_ESRB_ID,
    VCATEGORY_BROWSE_BY_RATING_ID,
    VCATEGORY_BROWSE_BY_CATEGORY_ID,
]

VCATEGORY_ID_LIST = [
    VCATEGORY_SPECIAL_ID,
    VCATEGORY_ROM_COLLECTION_ID,
    VCATEGORY_AOS_ID,
] + VCATEGORY_BROWSE_BY_ID_LIST

VLAUNCHER_FAVOURITES_ID = 'vlauncher_favourites'
VLAUNCHER_RECENT_ID = 'vlauncher_recent'
VLAUNCHER_MOST_PLAYED_ID = 'vlauncher_most_played'
VLAUNCHER_ID_LIST = [
    VLAUNCHER_FAVOURITES_ID,
    VLAUNCHER_RECENT_ID,
    VLAUNCHER_MOST_PLAYED_ID,
]

# --- Content type property to be used by skins ---
AEL_CONTENT_WINDOW_ID          = 10000
AEL_CONTENT_LABEL              = 'AEL_Content'
AEL_CONTENT_VALUE_LAUNCHERS    = 'launchers'
AEL_CONTENT_VALUE_ROMS         = 'roms'
AEL_CONTENT_VALUE_CATEGORY     = 'category'
AEL_CONTENT_VALUE_STD_LAUNCHER = 'std_launcher'
AEL_CONTENT_VALUE_ROM_LAUNCHER = 'rom_launcher'
AEL_CONTENT_VALUE_ROM          = 'rom'
AEL_CONTENT_VALUE_NONE         = ''

AEL_LAUNCHER_NAME_LABEL        = 'AEL_Launch_Name'
AEL_LAUNCHER_ICON_LABEL        = 'AEL_Launch_Icon'
AEL_LAUNCHER_CLEARLOGO_LABEL   = 'AEL_Launch_Clearlogo'

# Value is the number of items inside a launcher.
AEL_NUMITEMS_LABEL             = 'AEL_NumItems'

# --- ROM flags used by skins to display status icons ---
AEL_INFAV_BOOL_LABEL                 = 'AEL_InFav'
AEL_INFAV_BOOL_VALUE_TRUE            = 'InFav_True'
AEL_INFAV_BOOL_VALUE_FALSE           = 'InFav_False'
AEL_MULTIDISC_BOOL_LABEL             = 'AEL_MultiDisc'
AEL_MULTIDISC_BOOL_VALUE_TRUE        = 'MultiDisc_True'
AEL_MULTIDISC_BOOL_VALUE_FALSE       = 'MultiDisc_False'
AEL_FAV_STAT_LABEL                   = 'AEL_Fav_stat'
AEL_FAV_STAT_VALUE_OK                = 'Fav_OK'
AEL_FAV_STAT_VALUE_UNLINKED_ROM      = 'Fav_UnlinkedROM'
AEL_FAV_STAT_VALUE_UNLINKED_LAUNCHER = 'Fav_UnlinkedLauncher'
AEL_FAV_STAT_VALUE_BROKEN            = 'Fav_Broken'
AEL_FAV_STAT_VALUE_NONE              = 'Fav_None'
AEL_NOINTRO_STAT_LABEL               = 'AEL_NoIntro_stat'
AEL_NOINTRO_STAT_VALUE_HAVE          = 'NoIntro_Have'
AEL_NOINTRO_STAT_VALUE_MISS          = 'NoIntro_Miss'
AEL_NOINTRO_STAT_VALUE_UNKNOWN       = 'NoIntro_Unknown'
AEL_NOINTRO_STAT_VALUE_EXTRA         = 'NoIntro_Extra'
AEL_NOINTRO_STAT_VALUE_NONE          = 'NoIntro_None'
AEL_PCLONE_STAT_LABEL                = 'AEL_PClone_stat'
AEL_PCLONE_STAT_VALUE_PARENT         = 'PClone_Parent'
AEL_PCLONE_STAT_VALUE_CLONE          = 'PClone_Clone'
AEL_PCLONE_STAT_VALUE_NONE           = 'PClone_None'

# --- ID of the fake ROM parent of all Unknown ROMs ---
UNKNOWN_ROMS_PARENT_ID = 'Unknown_ROMs_Parent'

# --- Audit reports ---
AUDIT_REPORT_ALL = 'AUDIT_REPORT_ALL'
AUDIT_REPORT_NOINTRO = 'AUDIT_REPORT_NOINTRO'
AUDIT_REPORT_REDUMP = 'AUDIT_REPORT_REDUMP'

# ------------------------------------------------------------------------------------------------
# Metadata
# ------------------------------------------------------------------------------------------------
# launcher['audit_state'] values default AUDIT_STATE_OFF
AUDIT_STATE_ON  = 'Audit ON'
AUDIT_STATE_OFF = 'Audit OFF'
AUDIT_STATE_LIST = [
    AUDIT_STATE_ON,
    AUDIT_STATE_OFF,
]

# launcher['audit_display_mode'] values default NOINTRO_DMODE_ALL
AUDIT_DMODE_ALL       = 'All ROMs'
AUDIT_DMODE_HAVE      = 'Have ROMs'
AUDIT_DMODE_HAVE_UNK  = 'Have or Unknown ROMs'
AUDIT_DMODE_HAVE_MISS = 'Have or Missing ROMs'
AUDIT_DMODE_MISS      = 'Missing ROMs'
AUDIT_DMODE_MISS_UNK  = 'Missing or Unknown ROMs'
AUDIT_DMODE_UNK       = 'Unknown ROMs'
AUDIT_DMODE_LIST = [
    AUDIT_DMODE_ALL,
    AUDIT_DMODE_HAVE,
    AUDIT_DMODE_HAVE_UNK,
    AUDIT_DMODE_HAVE_MISS,
    AUDIT_DMODE_MISS,
    AUDIT_DMODE_MISS_UNK,
    AUDIT_DMODE_UNK,
]

# launcher['launcher_display_mode'] values default LAUNCHER_DMODE_FLAT
LAUNCHER_DMODE_FLAT   = 'Flat mode'
LAUNCHER_DMODE_PCLONE = 'Parent/Clone mode'
LAUNCHER_DMODE_LIST = [
    LAUNCHER_DMODE_FLAT,
    LAUNCHER_DMODE_PCLONE,
]

# rom['nointro_status'] values default AUDIT_STATUS_NONE
AUDIT_STATUS_HAVE    = 'Have'
AUDIT_STATUS_MISS    = 'Miss'
AUDIT_STATUS_UNKNOWN = 'Unknown'
AUDIT_STATUS_EXTRA   = 'Extra'
AUDIT_STATUS_NONE    = 'None'
AUDIT_STATUS_LIST = [
    AUDIT_STATUS_HAVE,
    AUDIT_STATUS_MISS,
    AUDIT_STATUS_UNKNOWN,
    AUDIT_STATUS_EXTRA,
    AUDIT_STATUS_NONE,
]

# rom['pclone_status'] values default PCLONE_STATUS_NONE
PCLONE_STATUS_PARENT = 'Parent'
PCLONE_STATUS_CLONE  = 'Clone'
PCLONE_STATUS_NONE   = 'None'
PCLONE_STATUS_LIST = [
    PCLONE_STATUS_PARENT,
    PCLONE_STATUS_CLONE,
    PCLONE_STATUS_NONE,
]

# m_esrb string ESRB_LIST default ESRB_PENDING
ESRB_PENDING     = 'RP (Rating Pending)'
ESRB_EARLY       = 'EC (Early Childhood)'
ESRB_EVERYONE    = 'E (Everyone)'
ESRB_EVERYONE_10 = 'E10+ (Everyone 10+)'
ESRB_TEEN        = 'T (Teen)'
ESRB_MATURE      = 'M (Mature)'
ESRB_ADULTS_ONLY = 'AO (Adults Only)'
ESRB_LIST = [
    ESRB_PENDING,
    ESRB_EARLY,
    ESRB_EVERYONE,
    ESRB_EVERYONE_10,
    ESRB_TEEN,
    ESRB_MATURE,
    ESRB_ADULTS_ONLY,
]

# m_nplayers values default ''
NP_NOT_SET = ''
NP_1P      = '1P'
NP_2P_SIM  = '2P sim'
NP_2P_ALT  = '2P alt'
NP_3P_SIM  = '3P sim'
NP_3P_ALT  = '3P alt'
NP_4P_SIM  = '4P sim'
NP_4P_ALT  = '4P alt'
NP_6P_SIM  = '6P sim'
NP_6P_ALT  = '6P alt'
NP_8P_SIM  = '8P sim'
NP_8P_ALT  = '8P alt'
NPLAYERS_LIST = [
    NP_1P,
    NP_2P_SIM,
    NP_2P_ALT,
    NP_3P_SIM,
    NP_3P_ALT,
    NP_4P_SIM,
    NP_4P_ALT,
    NP_6P_SIM,
    NP_6P_ALT,
    NP_8P_SIM,
    NP_8P_ALT,
]

# Use unique string as IDs.
META_TITLE_ID     = 'title'
META_YEAR_ID      = 'year'
META_GENRE_ID     = 'genre'
META_DEVELOPER_ID = 'developer'
META_NPLAYERS_ID  = 'nplayers'
META_ESRB_ID      = 'esrb'
META_RATING_ID    = 'rating'
META_PLOT_ID      = 'plot'

DEFAULT_META_TITLE     = ''
DEFAULT_META_YEAR      = ''
DEFAULT_META_GENRE     = ''
DEFAULT_META_DEVELOPER = ''
DEFAULT_META_NPLAYERS  = ''
DEFAULT_META_ESRB      = ESRB_PENDING
DEFAULT_META_RATING    = ''
DEFAULT_META_PLOT      = ''

# ------------------------------------------------------------------------------------------------
# Assets
# ------------------------------------------------------------------------------------------------
# --- Object types for rendering and database storage ---
OBJECT_CATEGORY_ID   = 1
OBJECT_COLLECTION_ID = 2
OBJECT_LAUNCHER_ID   = 3
OBJECT_ROM_ID        = 4

OBJECT_LIST = [
    OBJECT_CATEGORY_ID,
    OBJECT_COLLECTION_ID,
    OBJECT_LAUNCHER_ID,
    OBJECT_ROM_ID,
]

# --- Kodi standard artwork types. Mappable to any other artwork type including itself ---
# Use unique string as IDs. Then, if asset order changes the IDs are the same.
ASSET_ICON_ID       = 'icon'
ASSET_FANART_ID     = 'fanart'
ASSET_CLEARLOGO_ID  = 'clearlogo'
ASSET_POSTER_ID     = 'poster'
ASSET_BANNER_ID     = 'banner' # Marquee in MAME
ASSET_TRAILER_ID    = 'trailer'

# --- AEL artwork types ---
# What about supporting BOXSPINE and composite box (fron, spine and back in one image).
ASSET_TITLE_ID      = 'title'
ASSET_SNAP_ID       = 'snap'
ASSET_BOXFRONT_ID   = 'boxfront'  # Cabinet in MAME
ASSET_BOXBACK_ID    = 'boxback'   # CPanel in MAME
ASSET_3DBOX_ID      = '3dbox'
ASSET_CARTRIDGE_ID  = 'cartridge' # PCB in MAME
ASSET_FLYER_ID      = 'flyer'
ASSET_MAP_ID        = 'map'
ASSET_MANUAL_ID     = 'manual'
ASSET_CONTROLLER_ID = 'controller'

# The order of this list must match order in select dialogs in the GUI, or bad things will happen.
CATEGORY_ASSET_ID_LIST = [
    ASSET_ICON_ID,
    ASSET_FANART_ID,
    ASSET_BANNER_ID,
    ASSET_CLEARLOGO_ID,
    ASSET_POSTER_ID,
    ASSET_TRAILER_ID,
]
COLLECTION_ASSET_ID_LIST = CATEGORY_ASSET_ID_LIST

LAUNCHER_ASSET_ID_LIST = [
    ASSET_ICON_ID,
    ASSET_FANART_ID,
    ASSET_BANNER_ID,
    ASSET_CLEARLOGO_ID,
    ASSET_POSTER_ID,
    ASSET_CONTROLLER_ID,
    ASSET_TRAILER_ID,
]

ROM_ASSET_ID_LIST = [
    ASSET_FANART_ID,
    ASSET_BANNER_ID,
    ASSET_CLEARLOGO_ID,
    ASSET_TITLE_ID,
    ASSET_SNAP_ID,
    ASSET_BOXFRONT_ID,
    ASSET_BOXBACK_ID,
    ASSET_3DBOX_ID,
    ASSET_CARTRIDGE_ID,
    ASSET_FLYER_ID,
    ASSET_MAP_ID,
    ASSET_MANUAL_ID,
    ASSET_TRAILER_ID,
]

OBJECT_ASSETS = {
    OBJECT_CATEGORY_ID : CATEGORY_ASSET_ID_LIST,
    OBJECT_COLLECTION_ID : COLLECTION_ASSET_ID_LIST,
    OBJECT_LAUNCHER_ID : LAUNCHER_ASSET_ID_LIST,
    OBJECT_ROM_ID : ROM_ASSET_ID_LIST,
}

# List of assets that can be mapped to other assets.
DEFAULTABLE_ASSET_ID_LIST = [
    ASSET_ICON_ID,
    ASSET_FANART_ID,
    ASSET_BANNER_ID,
    ASSET_POSTER_ID,
    ASSET_CLEARLOGO_ID,
]

# List of assets that can be mapped to a defaultable asset for Categories.
MAPPABLE_CATEGORY_ASSET_ID_LIST = [
    ASSET_ICON_ID,
    ASSET_FANART_ID,
    ASSET_BANNER_ID,
    ASSET_POSTER_ID,
    ASSET_CLEARLOGO_ID,
]

# List of assets that can be mapped to a defaultable asset for Launchers.
MAPPABLE_LAUNCHER_ASSET_ID_LIST = [
    ASSET_ICON_ID,
    ASSET_FANART_ID,
    ASSET_BANNER_ID,
    ASSET_POSTER_ID,
    ASSET_CLEARLOGO_ID,
    ASSET_CONTROLLER_ID,
]

# List of assets that can be mapped to a defaultable asset for ROMs.
MAPPABLE_ROMS_ASSET_ID_LIST = [
    ASSET_TITLE_ID,
    ASSET_SNAP_ID,
    ASSET_BOXFRONT_ID,
    ASSET_BOXBACK_ID,
    ASSET_CARTRIDGE_ID,
    ASSET_FANART_ID,
    ASSET_BANNER_ID,
    ASSET_CLEARLOGO_ID,
    ASSET_FLYER_ID,
    ASSET_MAP_ID,
]

# --- Addon will search these file extensions for assets ---
# Check http://kodi.wiki/view/advancedsettings.xml#videoextensions
IMAGE_EXTENSION_LIST   = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tif', 'tiff']
MANUAL_EXTENSION_LIST  = ['pdf', 'cbz', 'cbr']
TRAILER_EXTENSION_LIST = ['mov', 'divx', 'xvid', 'wmv', 'avi', 'mpg', 'mpeg', 'mp4', 'mkv', 'avc']

# --- Scrapers -----------------------------------------------------------------------------------
# --- Options ---
# Use True only for development.
SCRAPER_CACHE_HUMAN_JSON = True

# --- IDs ---
SCRAPER_NULL_ID          = 10
SCRAPER_AEL_OFFLINE_ID   = 20
SCRAPER_THEGAMESDB_ID    = 30
SCRAPER_MOBYGAMES_ID     = 40
SCRAPER_SCREENSCRAPER_ID = 50
SCRAPER_GAMEFAQS_ID      = 60 # Disabled at the moment.
SCRAPER_ARCADEDB_ID      = 70
SCRAPER_LIBRETRO_ID      = 80 # Not coded yet.

# List of enabled scrapers. If a scraper ID is in this list then a unique scraper object
# will be instantiated and cached in the global ScraperFactory object.
# To disable an scraper just remove it from this list.
SCRAPER_LIST = [
    SCRAPER_NULL_ID,
    SCRAPER_AEL_OFFLINE_ID,
    SCRAPER_THEGAMESDB_ID,
    SCRAPER_MOBYGAMES_ID,
    SCRAPER_SCREENSCRAPER_ID,
    SCRAPER_ARCADEDB_ID,
]

# Make sure this matches the scraper list in settings.xml or bad things will happen.
SCRAP_METADATA_SETTINGS_LIST = [
    SCRAPER_AEL_OFFLINE_ID,
    SCRAPER_THEGAMESDB_ID,
    SCRAPER_SCREENSCRAPER_ID,
    SCRAPER_MOBYGAMES_ID,
]

SCRAP_ASSET_SETTINGS_LIST = [
    SCRAPER_THEGAMESDB_ID,
    SCRAPER_SCREENSCRAPER_ID,
    SCRAPER_MOBYGAMES_ID,
]

SCRAP_METADATA_MAME_SETTINGS_LIST = [
    SCRAPER_AEL_OFFLINE_ID,
    SCRAPER_ARCADEDB_ID,
    SCRAPER_THEGAMESDB_ID,
    SCRAPER_SCREENSCRAPER_ID,
    SCRAPER_MOBYGAMES_ID,
]

SCRAP_ASSET_MAME_SETTINGS_LIST = [
    SCRAPER_ARCADEDB_ID,
    SCRAPER_THEGAMESDB_ID,
    SCRAPER_SCREENSCRAPER_ID,
    SCRAPER_MOBYGAMES_ID,
]
