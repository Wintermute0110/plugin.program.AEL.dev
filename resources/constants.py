# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher platform constants.
#

# This file has contants that define the addon behaviour. 
# This module has no external dependencies.
#

# Copyright (c) 2016-2019 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# --- Python standard library ---
from __future__ import unicode_literals

# -------------------------------------------------------------------------------------------------
# A universal addon error reporting exception
# This exception is raised to report errors in the GUI.
# Unhandled exceptions must not raise AddonError() so the addon crashes and the traceback is
# printed in the Kodi log file.
# -------------------------------------------------------------------------------------------------
# Top-level GUI code looks like this
# try:
#     autoconfig_export_category(category, export_FN)
# except AddonError as E:
#     kodi_notify_warn('{0}'.format(E))
# else:
#     kodi_notify('Exported Category "{0}" XML config'.format(category['m_name']))
#
# Low-level code looks like this
# def autoconfig_export_category(category, export_FN):
#     try:
#         do_something_that_may_fail()
#     except OSError:
#         log_error('(OSError) Cannot write {0} file'.format(export_FN.getBase()))
#         # Message to be printed in the GUI
#         raise AddonError('Error writing file (OSError)')
#
class AddonError(Exception):
    def __init__(self, err_str): self.err_str = err_str
    def __str__(self): return self.err_str

# -------------------------------------------------------------------------------------------------
# Addon constants
# -------------------------------------------------------------------------------------------------
# --- Misc "constants" ---
PLOT_STR_MAXSIZE = 40
RETROPLAYER_LAUNCHER_APP_NAME = 'retroplayer_launcher_app'
LNK_LAUNCHER_APP_NAME         = 'lnk_launcher_app'

# --- Log level constants -------------------------------------------------------------------------
LOG_ERROR   = 0
LOG_WARNING = 1
LOG_INFO    = 2
LOG_VERB    = 3
LOG_DEBUG   = 4

# --- Kind of assets (for edit context menus and scrapers) ---
KIND_ASSET_CATEGORY   = 1
KIND_ASSET_COLLECTION = 2
KIND_ASSET_LAUNCHER   = 3
KIND_ASSET_ROM        = 4

# --- Special Cateogry/Launcher IDs ---
VCATEGORY_ADDONROOT_ID      = 'root_category'
VCATEGORY_FAVOURITES_ID     = 'vcategory_favourites'
VCATEGORY_COLLECTIONS_ID    = 'vcategory_collections'
VCATEGORY_RECENT_ID         = 'vcategory_recent'
VCATEGORY_MOST_PLAYED_ID    = 'vcategory_most_played'
VCATEGORY_TITLE_ID          = 'vcategory_title'
VCATEGORY_YEARS_ID          = 'vcategory_year'
VCATEGORY_GENRE_ID          = 'vcategory_genre'
VCATEGORY_DEVELOPER_ID      = 'vcategory_developer'
VCATEGORY_NPLAYERS_ID       = 'vcategory_nplayer'
VCATEGORY_ESRB_ID           = 'vcategory_esrb'
VCATEGORY_RATING_ID         = 'vcategory_rating'
VCATEGORY_CATEGORY_ID       = 'vcategory_category'
VCATEGORY_OFFSCRAPER_AEL_ID = 'vcategory_offline_scraper'
VCATEGORY_OFFSCRAPER_LB_ID  = 'vcategory_offline_scraper'

# Do we need this?
VCATEGORY_PCLONES_ID        = 'vcat_pclone'

VLAUNCHER_FAVOURITES_ID     = 'vlauncher_favourites'
VLAUNCHER_RECENT_ID         = 'vlauncher_recent'
VLAUNCHER_MOST_PLAYED_ID    = 'vlauncher_most_played'

# --- AEL OBJECT TYPES ---
OBJ_CATEGORY                 = 'CATEGORY'
OBJ_CATEGORY_VIRTUAL         = 'VIRTUAL_CATEGORY'
OBJ_LAUNCHER_STANDALONE      = 'STANDALONE_LAUNCHER'
OBJ_LAUNCHER_COLLECTION      = 'COLLECTION_LAUNCHER'
OBJ_LAUNCHER_VIRTUAL         = 'VIRTUAL_LAUNCHER'
OBJ_LAUNCHER_ROM             = 'ROM_LAUNCHER'
OBJ_LAUNCHER_RETROPLAYER     = 'RETROPLAYER_LAUNCHER'
OBJ_LAUNCHER_RETROARCH       = 'RETROARCH_LAUNCHER'
OBJ_LAUNCHER_LNK             = 'WINLNK_LAUNCHER'
OBJ_LAUNCHER_STEAM           = 'STEAM_LAUNCHER'
OBJ_LAUNCHER_NVGAMESTREAM    = 'NVIDIASTREAM_LAUNCHER'
OBJ_LAUNCHER_KODI_FAVOURITES = 'KODIFAVOURITES_LAUNCHER'
OBJ_ROM                      = 'ROM'
OBJ_FAVOURITE_ROM            = 'FAVOURITE_ROM'

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

# >> Value is the number of items inside a launcher.
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
AEL_NOINTRO_STAT_VALUE_NONE          = 'NoIntro_None'
AEL_PCLONE_STAT_LABEL                = 'AEL_PClone_stat'
AEL_PCLONE_STAT_VALUE_PARENT         = 'PClone_Parent'
AEL_PCLONE_STAT_VALUE_CLONE          = 'PClone_Clone'
AEL_PCLONE_STAT_VALUE_NONE           = 'PClone_None'

# --- ID of the fake ROM parent of all Unknown ROMs ---
UNKNOWN_ROMS_PARENT_ID = 'Unknown_ROMs_Parent'

# launcher['display_filter'] default value NOINTRO_DMODE_ALL
NOINTRO_DMODE_ALL       = 'All ROMs'
NOINTRO_DMODE_HAVE      = 'Have ROMs'
NOINTRO_DMODE_HAVE_UNK  = 'Have or Unknown ROMs'
NOINTRO_DMODE_HAVE_MISS = 'Have or Missing ROMs'
NOINTRO_DMODE_MISS      = 'Missing ROMs'
NOINTRO_DMODE_MISS_UNK  = 'Missing or Unknown ROMs'
NOINTRO_DMODE_UNK       = 'Unknown ROMs'
NOINTRO_DMODE_LIST = [
    NOINTRO_DMODE_ALL,
    NOINTRO_DMODE_HAVE,
    NOINTRO_DMODE_HAVE_UNK, 
    NOINTRO_DMODE_HAVE_MISS,
    NOINTRO_DMODE_MISS,
    NOINTRO_DMODE_MISS_UNK,
    NOINTRO_DMODE_UNK
]

# launcher['display_mode'] default value LAUNCHER_DMODE_FLAT
LAUNCHER_DMODE_FLAT   = 'Flat mode'
LAUNCHER_DMODE_PCLONE = 'Parent/Clone mode'
LAUNCHER_DMODE_1G1R   = '1G1R mode'
LAUNCHER_DMODE_LIST = [
    LAUNCHER_DMODE_FLAT,
    LAUNCHER_DMODE_PCLONE,
    LAUNCHER_DMODE_1G1R
]

# Mandatory variables in XML:
# launcher['nointro_status'] default value NOINTRO_STATUS_NONE
NOINTRO_STATUS_HAVE    = 'Have'
NOINTRO_STATUS_MISS    = 'Miss'
NOINTRO_STATUS_UNKNOWN = 'Unknown'
NOINTRO_STATUS_NONE    = 'None'
NOINTRO_STATUS_LIST = [
    NOINTRO_STATUS_HAVE,
    NOINTRO_STATUS_MISS,
    NOINTRO_STATUS_UNKNOWN,
    NOINTRO_STATUS_NONE
]

PCLONE_STATUS_PARENT = 'Parent'
PCLONE_STATUS_CLONE  = 'Clone'
PCLONE_STATUS_NONE   = 'None'
PCLONE_STATUS_LIST = [
    PCLONE_STATUS_PARENT,
    PCLONE_STATUS_CLONE,
    PCLONE_STATUS_NONE
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
    ESRB_MATURE, ESRB_ADULTS_ONLY
]

# m_nplayers values default ''
NP_1P     = '1P'
NP_2P_SIM = '2P sim'
NP_2P_ALT = '2P alt'
NP_3P_SIM = '3P sim'
NP_3P_ALT = '3P alt'
NP_4P_SIM = '4P sim'
NP_4P_ALT = '4P alt'
NP_6P_SIM = '6P sim'
NP_6P_ALT = '6P alt'
NP_8P_SIM = '8P sim'
NP_8P_ALT = '8P alt'
NPLAYERS_LIST = [NP_1P, NP_2P_SIM, NP_2P_ALT, NP_3P_SIM, NP_3P_ALT, NP_4P_SIM, NP_4P_ALT, 
                        NP_6P_SIM, NP_6P_ALT, NP_8P_SIM, NP_8P_ALT]

# -------------------------------------------------------------------------------------------------
# Assets
# -------------------------------------------------------------------------------------------------
# ROMs have FLYER, Categories/Launchers/Collections have POSTER
ASSET_ICON_ID       = 100
ASSET_FANART_ID     = 200
ASSET_BANNER_ID     = 300
ASSET_POSTER_ID     = 400
ASSET_CLEARLOGO_ID  = 500
ASSET_CONTROLLER_ID = 600
ASSET_TRAILER_ID    = 700
ASSET_TITLE_ID      = 800
ASSET_SNAP_ID       = 900
ASSET_BOXFRONT_ID   = 1000
ASSET_BOXBACK_ID    = 1100
ASSET_CARTRIDGE_ID  = 1200
ASSET_FLYER_ID      = 1300
ASSET_3DBOX_ID      = 1400
ASSET_MAP_ID        = 1500
ASSET_MANUAL_ID     = 1600

#
# The order of this list must match order in dialog.select() in the GUI, or bad things will happen.
#
CATEGORY_ASSET_ID_LIST = [
    ASSET_ICON_ID,   ASSET_FANART_ID,    ASSET_BANNER_ID,
    ASSET_POSTER_ID, ASSET_CLEARLOGO_ID, ASSET_TRAILER_ID,
]

LAUNCHER_ASSET_ID_LIST = [
    ASSET_ICON_ID,      ASSET_FANART_ID,     ASSET_BANNER_ID, ASSET_POSTER_ID,
    ASSET_CLEARLOGO_ID, ASSET_CONTROLLER_ID, ASSET_TRAILER_ID,
]

ROM_ASSET_ID_LIST = [
    ASSET_TITLE_ID,     ASSET_SNAP_ID,   ASSET_BOXFRONT_ID, ASSET_BOXBACK_ID,
    ASSET_CARTRIDGE_ID, ASSET_FANART_ID, ASSET_BANNER_ID,   ASSET_CLEARLOGO_ID,
    ASSET_FLYER_ID,     ASSET_3DBOX_ID,  ASSET_MAP_ID,    ASSET_MANUAL_ID,   ASSET_TRAILER_ID
]

#
# List of assets that can be mapped to other assets.
#
DEFAULTABLE_ASSET_ID_LIST = [
    ASSET_ICON_ID, ASSET_FANART_ID, ASSET_BANNER_ID, ASSET_POSTER_ID, ASSET_CLEARLOGO_ID
]

#
# List of assets that can be mapped to a defaultable asset for Categories.
#
MAPPABLE_CATEGORY_ASSET_ID_LIST = [
    ASSET_ICON_ID, ASSET_FANART_ID, ASSET_BANNER_ID, ASSET_POSTER_ID, ASSET_CLEARLOGO_ID
]

#
# List of assets that can be mapped to a defaultable asset for Launchers.
#
MAPPABLE_LAUNCHER_ASSET_ID_LIST = [
    ASSET_ICON_ID, ASSET_FANART_ID, ASSET_BANNER_ID, ASSET_POSTER_ID, ASSET_CLEARLOGO_ID, ASSET_CONTROLLER_ID
]

#
# List of assets that can be mapped to a defaultable asset for ROMs.
#
MAPPABLE_ROMS_ASSET_ID_LIST = [
    ASSET_TITLE_ID,     ASSET_SNAP_ID,   ASSET_BOXFRONT_ID, ASSET_BOXBACK_ID,
    ASSET_CARTRIDGE_ID, ASSET_FANART_ID, ASSET_BANNER_ID,   ASSET_CLEARLOGO_ID,
    ASSET_FLYER_ID,     ASSET_MAP_ID
]

# --- Addon will search these file extensions for assets ---
# >> Check http://kodi.wiki/view/advancedsettings.xml#videoextensions
IMAGE_EXTENSION_LIST   = ['png', 'jpg', 'gif', 'bmp']
MANUAL_EXTENSION_LIST  = ['pdf', 'cbz', 'cbr']
TRAILER_EXTENSION_LIST = ['mov', 'divx', 'xvid', 'wmv', 'avi', 'mpg', 'mpeg', 'mp4', 'mkv', 'avc']
