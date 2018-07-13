# -*- coding: utf-8 -*-
# Advanced Emulator Launcher asset (artwork) related stuff
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
import os

# --- AEL packages ---
from utils import *
from utils_kodi import *

# --- Define "constants" ---
ASSET_ICON       = 100
ASSET_FANART     = 200
ASSET_BANNER     = 300
ASSET_POSTER     = 400
ASSET_CLEARLOGO  = 500
ASSET_CONTROLLER = 600
ASSET_TRAILER    = 700
ASSET_TITLE      = 800
ASSET_SNAP       = 900
ASSET_BOXFRONT   = 1000
ASSET_BOXBACK    = 1100
ASSET_CARTRIDGE  = 1200
ASSET_FLYER      = 1300  # ROMs have FLYER, Categories/Launchers/Collections have POSTER
ASSET_MAP        = 1400
ASSET_MANUAL     = 1500

ASSET_NAMES = {}
ASSET_NAMES[ASSET_ICON]       = 'Icon'
ASSET_NAMES[ASSET_FANART]     = 'Fanart'
ASSET_NAMES[ASSET_BANNER]     = 'Banner'
ASSET_NAMES[ASSET_POSTER]     = 'Poster'
ASSET_NAMES[ASSET_CLEARLOGO]  = 'Clearlogo'
ASSET_NAMES[ASSET_CONTROLLER] = 'Controller'
ASSET_NAMES[ASSET_TRAILER]    = 'Trailer'
ASSET_NAMES[ASSET_TITLE]      = 'Title'
ASSET_NAMES[ASSET_SNAP]       = 'Snap'
ASSET_NAMES[ASSET_BOXFRONT]   = 'Boxfront'
ASSET_NAMES[ASSET_BOXBACK]    = 'Boxback'
ASSET_NAMES[ASSET_CARTRIDGE]  = 'Cartridge'
ASSET_NAMES[ASSET_FLYER]      = 'Flyer'
ASSET_NAMES[ASSET_MAP]        = 'Map'
ASSET_NAMES[ASSET_MANUAL]     = 'Manual'

# todo: default assets should use the constant values instead
# of the string names.
ASSET_KEYS_TO_CONSTANTS = {}
ASSET_KEYS_TO_CONSTANTS['s_title']      = ASSET_TITLE
ASSET_KEYS_TO_CONSTANTS['s_snap']       = ASSET_SNAP
ASSET_KEYS_TO_CONSTANTS['s_boxfront']   = ASSET_BOXFRONT
ASSET_KEYS_TO_CONSTANTS['s_boxback']    = ASSET_BOXBACK
ASSET_KEYS_TO_CONSTANTS['s_cartridge']  = ASSET_CARTRIDGE
ASSET_KEYS_TO_CONSTANTS['s_fanart']     = ASSET_FANART
ASSET_KEYS_TO_CONSTANTS['s_banner']     = ASSET_BANNER
ASSET_KEYS_TO_CONSTANTS['s_clearlogo']  = ASSET_CLEARLOGO
ASSET_KEYS_TO_CONSTANTS['s_flyer']      = ASSET_FLYER
ASSET_KEYS_TO_CONSTANTS['s_map']        = ASSET_MAP
ASSET_KEYS_TO_CONSTANTS['s_manual']     = ASSET_MANUAL
ASSET_KEYS_TO_CONSTANTS['s_trailer']    = ASSET_TRAILER
ASSET_KEYS_TO_CONSTANTS['s_icon']       = ASSET_ICON
ASSET_KEYS_TO_CONSTANTS['s_poster']     = ASSET_POSTER
ASSET_KEYS_TO_CONSTANTS['s_controller'] = ASSET_CONTROLLER

ASSET_SETTING_KEYS = {}
ASSET_SETTING_KEYS[ASSET_ICON] = ''
ASSET_SETTING_KEYS[ASSET_FANART] = 'scraper_fanart'
ASSET_SETTING_KEYS[ASSET_BANNER] = 'scraper_banner'
ASSET_SETTING_KEYS[ASSET_POSTER] = ''
ASSET_SETTING_KEYS[ASSET_CLEARLOGO] = 'scraper_clearlogo'
ASSET_SETTING_KEYS[ASSET_CONTROLLER] = ''
ASSET_SETTING_KEYS[ASSET_TRAILER] = ''
ASSET_SETTING_KEYS[ASSET_TITLE] = 'scraper_title'
ASSET_SETTING_KEYS[ASSET_SNAP] = 'scraper_snap'      
ASSET_SETTING_KEYS[ASSET_BOXFRONT] = 'scraper_boxfront'
ASSET_SETTING_KEYS[ASSET_BOXBACK] = 'scraper_boxback'
ASSET_SETTING_KEYS[ASSET_CARTRIDGE] = 'scraper_cart'
ASSET_SETTING_KEYS[ASSET_FLYER] = ''
ASSET_SETTING_KEYS[ASSET_MAP] = ''
ASSET_SETTING_KEYS[ASSET_MANUAL] = ''
    

MAME_ASSET_SETTING_KEYS = {}
MAME_ASSET_SETTING_KEYS[ASSET_ICON] = ''
MAME_ASSET_SETTING_KEYS[ASSET_FANART] = 'scraper_fanart_MAME'
MAME_ASSET_SETTING_KEYS[ASSET_BANNER] = 'scraper_marquee_MAME'
MAME_ASSET_SETTING_KEYS[ASSET_POSTER] = ''
MAME_ASSET_SETTING_KEYS[ASSET_CLEARLOGO] = 'scraper_clearlogo_MAME'
MAME_ASSET_SETTING_KEYS[ASSET_CONTROLLER] = ''
MAME_ASSET_SETTING_KEYS[ASSET_TRAILER] = ''
MAME_ASSET_SETTING_KEYS[ASSET_TITLE] = 'scraper_title_MAME'
MAME_ASSET_SETTING_KEYS[ASSET_SNAP] = 'scraper_snap_MAME'      
MAME_ASSET_SETTING_KEYS[ASSET_BOXFRONT] = 'scraper_cabinet_MAME'
MAME_ASSET_SETTING_KEYS[ASSET_BOXBACK] = 'scraper_cpanel_MAME'
MAME_ASSET_SETTING_KEYS[ASSET_CARTRIDGE] = 'scraper_pcb_MAME'
MAME_ASSET_SETTING_KEYS[ASSET_FLYER] = 'scraper_flyer_MAME'
MAME_ASSET_SETTING_KEYS[ASSET_MAP] = ''
MAME_ASSET_SETTING_KEYS[ASSET_MANUAL] = ''

#
# The order of this list must match order in dialog.select() in the GUI, or bad things will happen.
#
CATEGORY_ASSET_LIST = [
    ASSET_ICON, ASSET_FANART, ASSET_BANNER, ASSET_POSTER, ASSET_CLEARLOGO, ASSET_TRAILER
]

LAUNCHER_ASSET_LIST = [
    ASSET_ICON, ASSET_FANART, ASSET_BANNER, ASSET_POSTER, ASSET_CLEARLOGO, ASSET_CONTROLLER, ASSET_TRAILER
]

ROM_ASSET_LIST = [
    ASSET_TITLE,     ASSET_SNAP,   ASSET_BOXFRONT, ASSET_BOXBACK,
    ASSET_CARTRIDGE, ASSET_FANART, ASSET_BANNER,   ASSET_CLEARLOGO,  
    ASSET_FLYER,     ASSET_MAP,    ASSET_MANUAL,   ASSET_TRAILER
]

# --- Plugin will search these file extensions for assets ---
# >> Check http://kodi.wiki/view/advancedsettings.xml#videoextensions
IMAGE_EXTENSIONS   = ['png', 'jpg', 'gif', 'bmp']
MANUAL_EXTENSIONS  = ['pdf']
TRAILER_EXTENSIONS = ['mov', 'divx', 'xvid', 'wmv', 'avi', 'mpg', 'mpeg', 'mp4', 'mkv', 'avc']

#
# Get extensions to search for files
# Input : ['png', 'jpg']
# Output: ['png', 'jpg', 'PNG', 'JPG']
#
def asset_get_filesearch_extension_list(exts):
    ext_list = list(exts)
    for ext in exts:
        ext_list.append(ext.upper())

    return ext_list

#
# Gets extensions to be used in Kodi file dialog.
# Input : ['png', 'jpg']
# Output: '.png|.jpg'
#
def asset_get_dialog_extension_list(exts):
    ext_string = ''
    for ext in exts:
        ext_string += '.' + ext + '|'
    # >> Remove trailing '|' character
    ext_string = ext_string[:-1]

    return ext_string

#
# Gets extensions to be used in regular expressions.
# Input : ['png', 'jpg']
# Output: '(png|jpg)'
#
def asset_get_regexp_extension_list(exts):
    ext_string = ''
    for ext in exts:
        ext_string += ext + '|'
    # >> Remove trailing '|' character
    ext_string = ext_string[:-1]

    return '(' + ext_string + ')'

# -------------------------------------------------------------------------------------------------
# Asset functions
# -------------------------------------------------------------------------------------------------
# Creates path for assets (artwork) and automatically fills in the path_ fields in the launcher
# struct.
# 
def assets_init_asset_dir(assets_path_FName, launcher):
    log_verb('assets_init_asset_dir() asset_path "{0}"'.format(assets_path_FName.getPath()))

    # --- Fill in launcher fields and create asset directories ---
    if launcher['platform'] == 'MAME':
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_title', 'titles')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_snap', 'snaps')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_boxfront', 'cabinets')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_boxback', 'cpanels')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_cartridge', 'PCBs')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_fanart', 'fanarts')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_banner', 'marquees')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_clearlogo', 'clearlogos')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_flyer', 'flyers')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_map', 'maps')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_manual', 'manuals')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_trailer', 'trailers')
    else:
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_title', 'titles')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_snap', 'snaps')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_boxfront', 'boxfronts')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_boxback', 'boxbacks')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_cartridge', 'cartridges')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_fanart', 'fanarts')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_banner', 'banners')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_clearlogo', 'clearlogos')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_flyer', 'flyers')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_map', 'maps')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_manual', 'manuals')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_trailer', 'trailers')

#
# Create asset path and assign it to Launcher dictionary.
#
def assets_parse_asset_dir(launcher, assets_path_FName, key, pathName):
    subPath       = assets_path_FName.pjoin(pathName)
    launcher[key] = subPath.getOriginalPath()
    log_debug('assets_parse_asset_dir() Creating dir "{0}"'.format(subPath.getPath()))
    subPath.makedirs()

#
# Get artwork user configured to be used as icon/fanart/... for Categories/Launchers
#
def asset_get_default_asset_Category(object_dic, object_key, default_asset = ''):
    conf_asset_key = object_dic[object_key]
    asset_path     = object_dic[conf_asset_key] if conf_asset_key in object_dic and object_dic[conf_asset_key] else default_asset

    return asset_path

#
# Same for ROMs
#
def asset_get_default_asset_Launcher_ROM(rom, launcher, object_key, default_asset = ''):

    if object_key not in launcher:
        return default_asset

    conf_asset_key = launcher[object_key]
    asset_path     = rom[conf_asset_key] if rom[conf_asset_key] else default_asset

    return asset_path

#
# Gets a human readable name string for the asset field name.
#
def assets_get_asset_name_str(default_asset):
    asset_name_str = ''

    # >> ROMs
    if   default_asset == 's_title':     asset_name_str = 'Title'
    elif default_asset == 's_snap':      asset_name_str = 'Snap'
    elif default_asset == 's_boxfront':  asset_name_str = 'Boxfront'
    elif default_asset == 's_boxback':   asset_name_str = 'Boxback'
    elif default_asset == 's_cartridge': asset_name_str = 'Cartridge'
    elif default_asset == 's_fanart':    asset_name_str = 'Fanart'
    elif default_asset == 's_banner':    asset_name_str = 'Banner'
    elif default_asset == 's_clearlogo': asset_name_str = 'Clearlogo'
    elif default_asset == 's_flyer':     asset_name_str = 'Flyer'
    elif default_asset == 's_map':       asset_name_str = 'Map'
    elif default_asset == 's_manual':    asset_name_str = 'Manual'
    elif default_asset == 's_trailer':   asset_name_str = 'Trailer'
    # >> Categories/Launchers
    elif default_asset == 's_icon':       asset_name_str = 'Icon'
    elif default_asset == 's_poster':     asset_name_str = 'Poster'
    elif default_asset == 's_controller': asset_name_str = 'Controller'
    else:
        kodi_notify_warn('Wrong asset key {0}'.format(default_asset))
        log_error('assets_get_asset_name_str() Wrong default_thumb {0}'.format(default_asset))
    
    return asset_name_str

#
# This must match the order of the list Category_asset_ListItem_list in _command_edit_category()
#
def assets_choose_Category_mapped_artwork(dict_object, key, index):
    if   index == 0: dict_object[key] = 's_icon'
    elif index == 1: dict_object[key] = 's_fanart'
    elif index == 2: dict_object[key] = 's_banner'
    elif index == 3: dict_object[key] = 's_poster'
    elif index == 4: dict_object[key] = 's_clearlogo'

#
# This must match the order of the list Category_asset_ListItem_list in _command_edit_category()
#
def assets_get_Category_mapped_asset_idx(dict_object, key):
    if   dict_object[key] == 's_icon':       index = 0
    elif dict_object[key] == 's_fanart':     index = 1
    elif dict_object[key] == 's_banner':     index = 2
    elif dict_object[key] == 's_poster':     index = 3
    elif dict_object[key] == 's_clearlogo':  index = 4
    else:                                    index = 0

    return index

#
# This must match the order of the list Launcher_asset_ListItem_list in _command_edit_launcher()
#
def assets_choose_Launcher_mapped_artwork(dict_object, key, index):
    if   index == 0: dict_object[key] = 's_icon'
    elif index == 1: dict_object[key] = 's_fanart'
    elif index == 2: dict_object[key] = 's_banner'
    elif index == 3: dict_object[key] = 's_poster'
    elif index == 4: dict_object[key] = 's_clearlogo'
    elif index == 5: dict_object[key] = 's_controller'

#
# This must match the order of the list Launcher_asset_ListItem_list in _command_edit_launcher()
#
def assets_get_Launcher_mapped_asset_idx(dict_object, key):
    if   dict_object[key] == 's_icon':       index = 0
    elif dict_object[key] == 's_fanart':     index = 1
    elif dict_object[key] == 's_banner':     index = 2
    elif dict_object[key] == 's_poster':     index = 3
    elif dict_object[key] == 's_clearlogo':  index = 4
    elif dict_object[key] == 's_controller': index = 5
    else:                                    index = 0

    return index

#
# This must match the order of the list ROM_asset_str_list in _command_edit_launcher()
#
def assets_choose_ROM_mapped_artwork(dict_object, key, index):
    if   index == 0: dict_object[key] = 's_title'
    elif index == 1: dict_object[key] = 's_snap'
    elif index == 2: dict_object[key] = 's_boxfront'
    elif index == 3: dict_object[key] = 's_boxback'
    elif index == 4: dict_object[key] = 's_cartridge'
    elif index == 5: dict_object[key] = 's_fanart'
    elif index == 6: dict_object[key] = 's_banner'
    elif index == 7: dict_object[key] = 's_clearlogo'
    elif index == 8: dict_object[key] = 's_flyer'
    elif index == 9: dict_object[key] = 's_map'

#
# This must match the order of the list ROM_asset_str_list in _command_edit_launcher()
#
def assets_get_ROM_mapped_asset_idx(dict_object, key):
    if   dict_object[key] == 's_title':     index = 0
    elif dict_object[key] == 's_snap':      index = 1
    elif dict_object[key] == 's_boxfront':  index = 2
    elif dict_object[key] == 's_boxback':   index = 3
    elif dict_object[key] == 's_cartridge': index = 4
    elif dict_object[key] == 's_fanart':    index = 5
    elif dict_object[key] == 's_banner':    index = 6
    elif dict_object[key] == 's_clearlogo': index = 7
    elif dict_object[key] == 's_flyer':     index = 8
    elif dict_object[key] == 's_map':       index = 9
    else:                                   index = 0

    return index

class AssetInfoFactory: 
    
    def __init__(self):

        a_icon = AssetInfo()
        a_icon.kind             = ASSET_ICON
        a_icon.key              = 's_icon'
        a_icon.default_key      = 'default_icon'
        a_icon.rom_default_key  = 'roms_default_icon'
        a_icon.name             = 'Icon'
        a_icon.plural           = 'Icons'
        a_icon.fname_infix      = 'icon'
        a_icon.kind_str         = 'image'
        a_icon.exts             = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        a_icon.exts_dialog      = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        a_icon.path_key         = 'path_icon'

        a_fanart = AssetInfo()
        a_fanart.kind            = ASSET_FANART
        a_fanart.key             = 's_fanart'
        a_fanart.default_key     = 'default_fanart'
        a_fanart.rom_default_key = 'roms_default_fanart'
        a_fanart.name            = 'Fanart'
        a_fanart.plural          = 'Fanarts'
        a_fanart.fname_infix     = 'fanart'
        a_fanart.kind_str        = 'image'
        a_fanart.exts            = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        a_fanart.exts_dialog     = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        a_fanart.path_key        = 'path_fanart'

        a_banner = AssetInfo()
        a_banner.kind              = ASSET_BANNER
        a_banner.key               = 's_banner'
        a_banner.default_key       = 'default_banner'
        a_banner.rom_default_key   = 'roms_default_banner'
        a_banner.name              = 'Banner'
        a_banner.plural            = 'Banners'
        a_banner.fname_infix       = 'banner'
        a_banner.kind_str          = 'image'
        a_banner.exts              = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        a_banner.exts_dialog       = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        a_banner.path_key          = 'path_banner'
        
        a_poster = AssetInfo()        
        a_poster.kind              = ASSET_POSTER
        a_poster.key               = 's_poster'
        a_poster.default_key       = 'default_poster'
        a_poster.rom_default_key   = 'roms_default_poster'
        a_poster.name              = 'Poster'
        a_poster.plural            = 'Posters'
        a_poster.fname_infix       = 'poster'
        a_poster.kind_str          = 'image'
        a_poster.exts              = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        a_poster.exts_dialog       = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        a_poster.path_key          = 'path_poster'

        a_clearlogo = AssetInfo()
        a_clearlogo.kind            = ASSET_CLEARLOGO
        a_clearlogo.key             = 's_clearlogo'
        a_clearlogo.default_key     = 'default_clearlogo'
        a_clearlogo.rom_default_key = 'roms_default_clearlogo'
        a_clearlogo.name            = 'Clearlogo'
        a_clearlogo.plural          = 'Clearlogos'
        a_clearlogo.fname_infix     = 'clearlogo'
        a_clearlogo.kind_str        = 'image'
        a_clearlogo.exts            = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        a_clearlogo.exts_dialog     = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        a_clearlogo.path_key        = 'path_clearlogo'

        a_controller = AssetInfo()
        a_controller.kind           = ASSET_CONTROLLER
        a_controller.key            = 's_controller'
        a_controller.name           = 'Controller'
        a_controller.plural         = 'Controllers'
        a_controller.fname_infix    = 'controller'
        a_controller.kind_str       = 'image'
        a_controller.exts           = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        a_controller.exts_dialog    = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        a_controller.path_key       = 'path_controller'

        a_trailer = AssetInfo()
        a_trailer.kind        = ASSET_TRAILER
        a_trailer.key         = 's_trailer'
        a_trailer.name        = 'Trailer'
        a_trailer.fname_infix = 'trailer'
        a_trailer.kind_str    = 'video'
        a_trailer.exts        = asset_get_filesearch_extension_list(TRAILER_EXTENSIONS)
        a_trailer.exts_dialog = asset_get_dialog_extension_list(TRAILER_EXTENSIONS)
        a_trailer.path_key    = 'path_trailer'

        a_title = AssetInfo()
        a_title.kind        = ASSET_TITLE
        a_title.key         = 's_title'
        a_title.name        = 'Title'
        a_title.fname_infix = 'title'
        a_title.kind_str    = 'image'
        a_title.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        a_title.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        a_title.path_key    = 'path_title'

        a_snap = AssetInfo()
        a_snap.kind          = ASSET_SNAP
        a_snap.key           = 's_snap'
        a_snap.name          = 'Snap'
        a_snap.fname_infix   = 'snap'
        a_snap.kind_str      = 'image'
        a_snap.exts          = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        a_snap.exts_dialog   = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        a_snap.path_key      = 'path_snap'

        a_boxfront = AssetInfo()
        a_boxfront.kind         = ASSET_BOXFRONT
        a_boxfront.key          = 's_boxfront'
        a_boxfront.name         = 'Boxfront'
        a_boxfront.fname_infix  = 'boxfront'
        a_boxfront.kind_str     = 'image'
        a_boxfront.exts         = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        a_boxfront.exts_dialog  = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        a_boxfront.path_key     = 'path_boxfront'

        a_boxback = AssetInfo()
        a_boxback.kind          = ASSET_BOXBACK
        a_boxback.key           = 's_boxback'
        a_boxback.name          = 'Boxback'
        a_boxback.fname_infix   = 'boxback'
        a_boxback.kind_str      = 'image'
        a_boxback.exts          = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        a_boxback.exts_dialog   = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        a_boxback.path_key      = 'path_boxback'

        a_cartridge = AssetInfo()
        a_cartridge.kind        = ASSET_CARTRIDGE
        a_cartridge.key         = 's_cartridge'
        a_cartridge.name        = 'Cartridge'
        a_cartridge.fname_infix = 'cartridge'
        a_cartridge.kind_str    = 'image'
        a_cartridge.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        a_cartridge.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        a_cartridge.path_key    = 'path_cartridge'

        a_flyer = AssetInfo()
        a_flyer.kind        = ASSET_FLYER
        a_flyer.key         = 's_flyer'
        a_flyer.name        = 'Flyer'
        a_flyer.fname_infix = 'flyer'
        a_flyer.kind_str    = 'image'
        a_flyer.fname_infix = 'poster'
        a_flyer.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        a_flyer.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        a_flyer.path_key    = 'path_flyer'

        a_map = AssetInfo()
        a_map.kind          = ASSET_MAP
        a_map.key           = 's_map'
        a_map.name          = 'Map'
        a_map.fname_infix   = 'map'
        a_map.kind_str      = 'image'
        a_map.exts          = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        a_map.exts_dialog   = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        a_map.path_key      = 'path_map'

        a_manual = AssetInfo()
        a_manual.kind        = ASSET_MANUAL
        a_manual.key         = 's_manual'
        a_manual.name        = 'Manual'
        a_manual.fname_infix = 'manual'
        a_manual.kind_str    = 'manual'
        a_manual.exts        = asset_get_filesearch_extension_list(MANUAL_EXTENSIONS)
        a_manual.exts_dialog = asset_get_dialog_extension_list(MANUAL_EXTENSIONS)
        a_manual.path_key    = 'path_manual'

        self.asset_infos = {}
        self.asset_infos[ASSET_ICON]        = a_icon
        self.asset_infos[ASSET_FANART]      = a_fanart
        self.asset_infos[ASSET_BANNER]      = a_banner
        self.asset_infos[ASSET_POSTER]      = a_poster
        self.asset_infos[ASSET_CLEARLOGO]   = a_clearlogo
        self.asset_infos[ASSET_CONTROLLER]  = a_controller
        self.asset_infos[ASSET_TRAILER]     = a_trailer
        self.asset_infos[ASSET_TITLE]       = a_title
        self.asset_infos[ASSET_SNAP]        = a_snap
        self.asset_infos[ASSET_BOXFRONT]    = a_boxfront
        self.asset_infos[ASSET_BOXBACK]     = a_boxback
        self.asset_infos[ASSET_CARTRIDGE]   = a_cartridge
        self.asset_infos[ASSET_FLYER]       = a_flyer
        self.asset_infos[ASSET_MAP]         = a_map
        self.asset_infos[ASSET_MANUAL]      = a_manual

    def get_all(self):
        return list(self.asset_infos.values())

    def get_asset_kinds_for_roms(self):
        rom_asset_kinds = []
        for rom_asset_kind in ROM_ASSET_LIST:
            rom_asset_kinds.append(self.asset_infos[rom_asset_kind])

        return rom_asset_kinds

    def get_asset_info(self, asset_kind):
        
        asset_info = self.asset_infos.get(asset_kind, None)

        if asset_info is None:
            log_error('assets_get_info_scheme() Wrong asset_kind = {0}'.format(asset_kind))
            return AssetInfo()

        return asset_info

# -------------------------------------------------------------------------------------------------
# Gets all required information about an asset: path, name, etc.
# Returns an object with all the information
# -------------------------------------------------------------------------------------------------
class AssetInfo:
    kind        = 0
    key         = ''
    default_key = ''
    rom_default_key = ''
    name        = ''
    plural      = ''
    fname_infix = '' # Used only when searching assets when importing XML
    kind_str    = ''
    exts        = []
    exts_dialog = []
    path_key    = ''

def assets_get_info_scheme(asset_kind):
    A = AssetInfo()

    if asset_kind == ASSET_ICON:
        A.kind        = ASSET_ICON
        A.key         = 's_icon'
        A.default_key = 'default_icon'
        A.rom_default_key = 'roms_default_icon'
        A.name        = 'Icon'
        A.fname_infix = 'icon'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_icon'

    elif asset_kind == ASSET_FANART:
        A.kind              = ASSET_FANART
        A.key               = 's_fanart'
        A.default_key       = 'default_fanart'
        A.rom_default_key   = 'roms_default_fanart'
        A.name              = 'Fanart'
        A.fname_infix       = 'fanart'
        A.kind_str          = 'image'
        A.exts              = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog       = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key          = 'path_fanart'
    elif asset_kind == ASSET_BANNER:
        A.kind              = ASSET_BANNER
        A.key               = 's_banner'
        A.default_key       = 'default_banner'
        A.rom_default_key   = 'roms_default_banner'
        A.name              = 'Banner'
        A.fname_infix       = 'banner'
        A.kind_str          = 'image'
        A.exts              = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog       = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key          = 'path_banner'
    elif asset_kind == ASSET_POSTER:
        A.kind        = ASSET_POSTER
        A.key         = 's_poster'
        A.default_key = 'default_poster'
        A.rom_default_key = 'roms_default_poster'
        A.name        = 'Poster'
        A.fname_infix = 'poster'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_poster'
    elif asset_kind == ASSET_CLEARLOGO:
        A.kind        = ASSET_CLEARLOGO
        A.key         = 's_clearlogo'
        A.default_key = 'default_clearlogo'
        A.rom_default_key = 'roms_default_clearlogo'
        A.name        = 'Clearlogo'
        A.fname_infix = 'clearlogo'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_clearlogo'
    elif asset_kind == ASSET_CONTROLLER:
        A.kind        = ASSET_CONTROLLER
        A.key         = 's_controller'
        A.name        = 'Controller'
        A.fname_infix = 'controller'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_controller'
    elif asset_kind == ASSET_TRAILER:
        A.kind        = ASSET_TRAILER
        A.key         = 's_trailer'
        A.name        = 'Trailer'
        A.fname_infix = 'trailer'
        A.kind_str    = 'video'
        A.exts        = asset_get_filesearch_extension_list(TRAILER_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(TRAILER_EXTENSIONS)
        A.path_key    = 'path_trailer'
    elif asset_kind == ASSET_TITLE:
        A.kind        = ASSET_TITLE
        A.key         = 's_title'
        A.name        = 'Title'
        A.fname_infix = 'title'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_title'
    elif asset_kind == ASSET_SNAP:
        A.kind        = ASSET_SNAP
        A.key         = 's_snap'
        A.name        = 'Snap'
        A.fname_infix = 'snap'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_snap'
    elif asset_kind == ASSET_BOXFRONT:
        A.kind        = ASSET_BOXFRONT
        A.key         = 's_boxfront'
        A.name        = 'Boxfront'
        A.fname_infix = 'boxfront'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_boxfront'
    elif asset_kind == ASSET_BOXBACK:
        A.kind        = ASSET_BOXBACK
        A.key         = 's_boxback'
        A.name        = 'Boxback'
        A.fname_infix = 'boxback'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_boxback'
    elif asset_kind == ASSET_CARTRIDGE:
        A.kind        = ASSET_CARTRIDGE
        A.key         = 's_cartridge'
        A.name        = 'Cartridge'
        A.fname_infix = 'cartridge'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_cartridge'
    elif asset_kind == ASSET_FLYER:
        A.kind        = ASSET_FLYER
        A.key         = 's_flyer'
        A.name        = 'Flyer'
        A.fname_infix = 'flyer'
        A.kind_str    = 'image'
        A.fname_infix = 'poster'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_flyer'
    elif asset_kind == ASSET_MAP:
        A.kind        = ASSET_MAP
        A.key         = 's_map'
        A.name        = 'Map'
        A.fname_infix = 'map'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_map'
    elif asset_kind == ASSET_MANUAL:
        A.kind        = ASSET_MANUAL
        A.key         = 's_manual'
        A.name        = 'Manual'
        A.fname_infix = 'manual'
        A.kind_str    = 'manual'
        A.exts        = asset_get_filesearch_extension_list(MANUAL_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(MANUAL_EXTENSIONS)
        A.path_key    = 'path_manual'
    else:
        log_error('assets_get_info_scheme() Wrong asset_kind = {0}'.format(asset_kind))

    # --- Ultra DEBUG ---
    # log_debug('assets_get_info_scheme() asset_kind    {0}'.format(asset_kind))
    # log_debug('assets_get_info_scheme() A.key         {0}'.format(A.key))
    # log_debug('assets_get_info_scheme() A.name        {0}'.format(A.name))
    # log_debug('assets_get_info_scheme() A.fname_infix {0}'.format(A.fname_infix))
    # log_debug('assets_get_info_scheme() A.kind_str    {0}'.format(A.kind_str))
    # log_debug('assets_get_info_scheme() A.exts        {0}'.format(A.exts))
    # log_debug('assets_get_info_scheme() A.exts_dialog {0}'.format(A.exts_dialog))
    # log_debug('assets_get_info_scheme() A.path_key    {0}'.format(A.path_key))

    return A

#
# Scheme DIR uses different directories for artwork and no sufixes.
#
# Assets    -> Assets info object
# AssetPath -> FileName object
# ROM       -> ROM name FileName object
#
# Returns a FileName object
#
def assets_get_path_noext_DIR(Asset, AssetPath, ROM):

    return AssetPath + ROM.getBase_noext()

#
# Scheme SUFIX uses suffixes for artwork. All artwork assets are stored in the same directory.
# Name example: "Sonic The Hedgehog (Europe)_a3e_title"
# First 3 characters of the objectID are added to avoid overwriting of images. For example, in the
# Favourites special category there could be ROMs with the same name for different systems.
#
# Assets    -> Assets info object
# AssetPath -> FileName object
# asset_base_noext -> Unicode string
# objectID -> Object MD5 ID fingerprint (Unicode string)
#
# Returns a FileName object
#
def assets_get_path_noext_SUFIX(Asset, AssetPath, asset_base_noext, objectID = '000'):
    # >> Returns asset/artwork path_noext
    asset_path_noext_FileName = FileNameFactory.create('')
    objectID_str = '_' + objectID[0:3]

    if   Asset.kind == ASSET_ICON:       asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_icon')
    elif Asset.kind == ASSET_FANART:     asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_fanart')
    elif Asset.kind == ASSET_BANNER:     asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_banner')
    elif Asset.kind == ASSET_POSTER:     asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_poster')
    elif Asset.kind == ASSET_CLEARLOGO:  asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_clearlogo')
    elif Asset.kind == ASSET_CONTROLLER: asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_controller')
    elif Asset.kind == ASSET_TRAILER:    asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_trailer')
    elif Asset.kind == ASSET_TITLE:      asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_title')
    elif Asset.kind == ASSET_SNAP:       asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_snap')
    elif Asset.kind == ASSET_BOXFRONT:   asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_boxfront')
    elif Asset.kind == ASSET_BOXBACK:    asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_boxback')
    elif Asset.kind == ASSET_CARTRIDGE:  asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_cartridge')
    elif Asset.kind == ASSET_FLYER:      asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_flyer')
    elif Asset.kind == ASSET_MAP:        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_map')
    elif Asset.kind == ASSET_MANUAL:     asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_manual')
    else:
        log_error('assets_get_path_noext_SUFIX() Wrong asset kind = {0}'.format(Asset.kind))

    return asset_path_noext_FileName

#
# Get a list of enabled assets.
#
# Returns tuple:
# configured_bool_list    List of boolean values. It has all assets defined in ROM_ASSET_LIST
# unconfigured_name_list  List of disabled asset names
#
def asset_get_configured_dir_list(launcher):
    configured_bool_list   = [False] * len(ROM_ASSET_LIST)
    unconfigured_name_list = []

    # >> Check if asset paths are configured or not
    for i, asset in enumerate(ROM_ASSET_LIST):
        A = assets_get_info_scheme(asset)
        configured_bool_list[i] = True if launcher[A.path_key] else False
        if not configured_bool_list[i]: 
            unconfigured_name_list.append(A.name)
            log_verb('asset_get_enabled_asset_list() {0:<9} path unconfigured'.format(A.name))
        else:
            log_debug('asset_get_enabled_asset_list() {0:<9} path configured'.format(A.name))

    return (configured_bool_list, unconfigured_name_list)

#
# Get a list of assets with duplicated paths. Refuse to do anything if duplicated paths found.
#
def asset_get_duplicated_dir_list(launcher):
    duplicated_bool_list   = [False] * len(ROM_ASSET_LIST)
    duplicated_name_list   = []

    # >> Check for duplicated asset paths
    for i, asset_i in enumerate(ROM_ASSET_LIST[:-1]):
        A_i = assets_get_info_scheme(asset_i)
        for j, asset_j in enumerate(ROM_ASSET_LIST[i+1:]):
            A_j = assets_get_info_scheme(asset_j)
            # >> Exclude unconfigured assets (empty strings).
            if not launcher[A_i.path_key] or not launcher[A_j.path_key]: continue
            # log_debug('asset_get_duplicated_asset_list() Checking {0:<9} vs {1:<9}'.format(A_i.name, A_j.name))
            if launcher[A_i.path_key] == launcher[A_j.path_key]:
                duplicated_bool_list[i] = True
                duplicated_name_list.append('{0} and {1}'.format(A_i.name, A_j.name))
                log_info('asset_get_duplicated_asset_list() DUPLICATED {0} and {1}'.format(A_i.name, A_j.name))

    return duplicated_name_list

#
# Search for local assets and place found files into a list.
# Returned list all has assets as defined in ROM_ASSET_LIST.
# This function is used in the ROM Scanner.
#
# launcher               -> launcher dictionary
# ROMFile                -> FileName object
# enabled_ROM_asset_list -> list of booleans
#
def assets_search_local_cached_assets(launcher, ROMFile, enabled_ROM_asset_list):
    log_verb('assets_search_local_cached_assets() Searching for ROM local assets...')
    local_asset_list = [''] * len(ROM_ASSET_LIST)
    rom_basename_noext = ROMFile.getBase_noext()
    for i, asset_kind in enumerate(ROM_ASSET_LIST):
        AInfo = assets_get_info_scheme(asset_kind)
        if not enabled_ROM_asset_list[i]:
            log_verb('assets_search_local_cached_assets() Disabled {0:<9}'.format(AInfo.name))
            continue
        local_asset = misc_search_file_cache(launcher[AInfo.path_key], rom_basename_noext, AInfo.exts)

        if local_asset:
            local_asset_list[i] = local_asset.getOriginalPath()
            log_verb('assets_search_local_cached_assets() Found    {0:<9} "{1}"'.format(AInfo.name, local_asset_list[i]))
        else:
            local_asset_list[i] = ''
            log_verb('assets_search_local_cached_assets() Missing  {0:<9}'.format(AInfo.name))

    return local_asset_list


#
# Search for local assets and put found files into a list.
# This function is used in _roms_add_new_rom() where there is no need for a file cache.
#
def assets_search_local_assets(launcher, ROMFile, enabled_ROM_asset_list):
    log_verb('assets_search_local_assets() Searching for ROM local assets...')
    local_asset_list = [''] * len(ROM_ASSET_LIST)
    for i, asset_kind in enumerate(ROM_ASSET_LIST):
        AInfo = assets_get_info_scheme(asset_kind)
        if not enabled_ROM_asset_list[i]:
            log_verb('assets_search_local_assets() Disabled {0:<9}'.format(AInfo.name))
            continue
        asset_path = FileNameFactory.create(launcher[AInfo.path_key])
        local_asset = misc_look_for_file(asset_path, ROMFile.getBase_noext(), AInfo.exts)

        if local_asset:
            local_asset_list[i] = local_asset.getOriginalPath()
            log_verb('assets_search_local_assets() Found    {0:<9} "{1}"'.format(AInfo.name, local_asset_list[i]))
        else:
            local_asset_list[i] = ''
            log_verb('assets_search_local_assets() Missing  {0:<9}'.format(AInfo.name))

    return local_asset_list

#
# A) This function checks if all path_* share a common root directory. If so
#    this function returns that common directory as an Unicode string.
# B) If path_* do not share a common root directory this function returns ''.
#
def assets_get_ROM_asset_path(launcher):
    ROM_asset_path = ''
    duplicated_bool_list = [False] * len(ROM_ASSET_LIST)
    AInfo_first = assets_get_info_scheme(ROM_ASSET_LIST[0])
    path_first_asset_FN = FileNameFactory.create(launcher[AInfo_first.path_key])
    log_debug('assets_get_ROM_asset_path() path_first_asset OP  "{0}"'.format(path_first_asset_FN.getOriginalPath()))
    log_debug('assets_get_ROM_asset_path() path_first_asset Dir "{0}"'.format(path_first_asset_FN.getDir()))
    for i, asset_kind in enumerate(ROM_ASSET_LIST):
        AInfo = assets_get_info_scheme(asset_kind)
        current_path_FN = FileNameFactory.create(launcher[AInfo.path_key])
        if current_path_FN.getDir() == path_first_asset_FN.getDir():
            duplicated_bool_list[i] = True

    return path_first_asset_FN.getDir() if all(duplicated_bool_list) else ''
