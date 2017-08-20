# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher platform constants
#

# Copyright (c) 2016-2017 Wintermute0110 <wintermute0110@gmail.com>
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

# --- Misc "constants" ---
KIND_CATEGORY         = 1
KIND_COLLECTION       = 2
KIND_LAUNCHER         = 3
KIND_ROM              = 4
DESCRIPTION_MAXSIZE   = 40
RETROPLAYER_LAUNCHER_APP_NAME = 'retroplayer_launcher_app'
LNK_LAUNCHER_APP_NAME         = 'lnk_launcher_app'

# --- Special Cateogry/Launcher IDs ---
VCATEGORY_ADDONROOT_ID   = 'root_category'
VCATEGORY_FAVOURITES_ID  = 'vcat_favourites'
VCATEGORY_COLLECTIONS_ID = 'vcat_collections'
VCATEGORY_TITLE_ID       = 'vcat_title'
VCATEGORY_YEARS_ID       = 'vcat_years'
VCATEGORY_GENRE_ID       = 'vcat_genre'
VCATEGORY_STUDIO_ID      = 'vcat_studio'
VCATEGORY_NPLAYERS_ID    = 'vcat_nplayers'
VCATEGORY_ESRB_ID        = 'vcat_esrb'
VCATEGORY_RATING_ID      = 'vcat_rating'
VCATEGORY_CATEGORY_ID    = 'vcat_category'
VCATEGORY_RECENT_ID      = 'vcat_recent'
VCATEGORY_MOST_PLAYED_ID = 'vcat_most_played'
VCATEGORY_OFF_SCRAPER_ID = 'vcat_offline_scraper'
VLAUNCHER_FAVOURITES_ID  = 'vlauncher_favourites'
VLAUNCHER_RECENT_ID      = 'vlauncher_recent'
VLAUNCHER_MOST_PLAYED_ID = 'vlauncher_most_played'

# --- Content type property to be used by skins ---
AEL_CONTENT_WINDOW_ID       = 10000
AEL_CONTENT_LABEL           = 'AEL_Content'
AEL_CONTENT_VALUE_LAUNCHERS = 'launchers'
AEL_CONTENT_VALUE_ROMS      = 'roms'
AEL_CONTENT_VALUE_NONE      = ''

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
