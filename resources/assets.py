# -*- coding: utf-8 -*-

# Copyright (c) 2016-2021 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# Advanced Emulator Launcher asset (artwork) related stuff.

# --- Be prepared for the future ---
from __future__ import unicode_literals
from __future__ import division

# --- Modules/packages in this plugin ---
from .constants import *
from .platforms import *
from .utils import *

# --- Python standard library ---
import os

# Get extensions to search for files
# Input : ['png', 'jpg']
# Output: ['png', 'jpg', 'PNG', 'JPG']
def asset_get_filesearch_extension_list(exts):
    ext_list = list(exts)
    for ext in exts:
        ext_list.append(ext.upper())
    return ext_list

# Gets extensions to be used in Kodi file dialog.
# Input : ['png', 'jpg']
# Output: '.png|.jpg'
def asset_get_dialog_extension_list(exts):
    ext_string = ''
    for ext in exts:
        ext_string += '.' + ext + '|'
    # Remove trailing '|' character
    ext_string = ext_string[:-1]
    return ext_string

# Gets extensions to be used in regular expressions.
# Input : ['png', 'jpg']
# Output: '(png|jpg)'
def asset_get_regexp_extension_list(exts):
    ext_string = ''
    for ext in exts:
        ext_string += ext + '|'
    # Remove trailing '|' character
    ext_string = ext_string[:-1]
    return '(' + ext_string + ')'

# -------------------------------------------------------------------------------------------------
# Asset functions
# -------------------------------------------------------------------------------------------------
def assets_get_default_artwork_dir(asset_ID, launcher):
    if launcher['platform'] == 'MAME':
        if   asset_ID == ASSET_FANART_ID: return 'fanarts'
        elif asset_ID == ASSET_BANNER_ID: return 'marquees'
        elif asset_ID == ASSET_CLEARLOGO_ID: return 'clearlogos'
        elif asset_ID == ASSET_TITLE_ID: return 'titles'
        elif asset_ID == ASSET_SNAP_ID: return 'snaps'
        elif asset_ID == ASSET_BOXFRONT_ID: return 'cabinets'
        elif asset_ID == ASSET_BOXBACK_ID: return 'cpanels'
        elif asset_ID == ASSET_3DBOX_ID: return '3dboxes'
        elif asset_ID == ASSET_CARTRIDGE_ID: return 'PCBs'
        elif asset_ID == ASSET_FLYER_ID: return 'flyers'
        elif asset_ID == ASSET_MAP_ID: return 'maps'
        elif asset_ID == ASSET_MANUAL_ID: return 'manuals'
        elif asset_ID == ASSET_TRAILER_ID: return 'trailers'
        else: raise ValueError
    else:
        if   asset_ID == ASSET_FANART_ID: return 'fanarts'
        elif asset_ID == ASSET_BANNER_ID: return 'banners'
        elif asset_ID == ASSET_CLEARLOGO_ID: return 'clearlogos'
        elif asset_ID == ASSET_TITLE_ID: return 'titles'
        elif asset_ID == ASSET_SNAP_ID: return 'snaps'
        elif asset_ID == ASSET_BOXFRONT_ID: return 'boxfronts'
        elif asset_ID == ASSET_BOXBACK_ID: return 'boxbacks'
        elif asset_ID == ASSET_3DBOX_ID: return '3dboxes'
        elif asset_ID == ASSET_CARTRIDGE_ID: return 'cartridges'
        elif asset_ID == ASSET_FLYER_ID: return 'flyers'
        elif asset_ID == ASSET_MAP_ID: return 'maps'
        elif asset_ID == ASSET_MANUAL_ID: return 'manuals'
        elif asset_ID == ASSET_TRAILER_ID: return 'trailers'
        else: raise ValueError

# Creates path for assets (artwork) and automatically fills in the path_ fields in the launcher
# struct.
def assets_init_asset_dir(assets_path_FName, launcher):
    log_debug('assets_init_asset_dir() asset_path "{}"'.format(assets_path_FName.getPath()))

    # --- Fill in launcher fields and create asset directories ---
    if launcher['platform'] == 'MAME':
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_fanart', 'fanarts')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_banner', 'marquees')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_clearlogo', 'clearlogos')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_title', 'titles')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_snap', 'snaps')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_boxfront', 'cabinets')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_boxback', 'cpanels')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_3dbox', '3dboxes')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_cartridge', 'PCBs')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_flyer', 'flyers')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_map', 'maps')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_manual', 'manuals')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_trailer', 'trailers')
    else:
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_fanart', 'fanarts')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_banner', 'banners')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_clearlogo', 'clearlogos')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_title', 'titles')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_snap', 'snaps')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_boxfront', 'boxfronts')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_boxback', 'boxbacks')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_3dbox', '3dboxes')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_cartridge', 'cartridges')
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
    log_debug('assets_parse_asset_dir() Creating dir "{}"'.format(subPath.getPath()))
    subPath.makedirs()

#
# Get artwork user configured to be used as icon/fanart/... for Categories/Launchers
#
def asset_get_default_asset_Category(object_dic, object_key, default_asset = ''):
    conf_asset_key = object_dic[object_key]
    asset_path     = object_dic[conf_asset_key] if object_dic[conf_asset_key] else default_asset

    return asset_path

#
# Same for ROMs
#
def asset_get_default_asset_Launcher_ROM(rom, launcher, object_key, default_asset = ''):
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
        kodi_notify_warn('Wrong asset key {}'.format(default_asset))
        log_error('assets_get_asset_name_str() Wrong default_thumb {}'.format(default_asset))

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

# -------------------------------------------------------------------------------------------------
# Gets all required information about an asset: path, name, etc.
# Returns an object with all the information
# -------------------------------------------------------------------------------------------------
class AssetInfo:
    # Careful! Class variables do not work like C++
    ID          = 0
    key         = ''
    name        = ''
    fname_infix = '' # Used only when searching assets when importing XML
    kind_str    = ''
    exts        = []
    exts_dialog = []
    path_key    = ''

def assets_get_info_scheme(asset_kind):
    A = AssetInfo()

    if asset_kind == ASSET_ICON_ID:
        A.ID          = ASSET_ICON_ID
        A.key         = 's_icon'
        A.name        = 'Icon'
        A.fname_infix = 'icon'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        A.path_key    = 'path_icon'
    elif asset_kind == ASSET_FANART_ID:
        A.ID          = ASSET_FANART_ID
        A.key         = 's_fanart'
        A.name        = 'Fanart'
        A.fname_infix = 'fanart'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        A.path_key    = 'path_fanart'
    elif asset_kind == ASSET_BANNER_ID:
        A.ID          = ASSET_BANNER_ID
        A.key         = 's_banner'
        A.name        = 'Banner'
        A.fname_infix = 'banner'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        A.path_key    = 'path_banner'
    elif asset_kind == ASSET_POSTER_ID:
        A.ID          = ASSET_POSTER_ID
        A.key         = 's_poster'
        A.name        = 'Poster'
        A.fname_infix = 'poster'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        A.path_key    = 'path_poster'
    elif asset_kind == ASSET_CLEARLOGO_ID:
        A.ID          = ASSET_CLEARLOGO_ID
        A.key         = 's_clearlogo'
        A.name        = 'Clearlogo'
        A.fname_infix = 'clearlogo'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        A.path_key    = 'path_clearlogo'
    elif asset_kind == ASSET_CONTROLLER_ID:
        A.ID          = ASSET_CONTROLLER_ID
        A.key         = 's_controller'
        A.name        = 'Controller'
        A.fname_infix = 'controller'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        A.path_key    = 'path_controller'
    elif asset_kind == ASSET_TRAILER_ID:
        A.ID          = ASSET_TRAILER_ID
        A.key         = 's_trailer'
        A.name        = 'Trailer'
        A.fname_infix = 'trailer'
        A.kind_str    = 'video'
        A.exts        = asset_get_filesearch_extension_list(TRAILER_EXTENSION_LIST)
        A.exts_dialog = asset_get_dialog_extension_list(TRAILER_EXTENSION_LIST)
        A.path_key    = 'path_trailer'
    elif asset_kind == ASSET_TITLE_ID:
        A.ID          = ASSET_TITLE_ID
        A.key         = 's_title'
        A.name        = 'Title'
        A.fname_infix = 'title'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        A.path_key    = 'path_title'
    elif asset_kind == ASSET_SNAP_ID:
        A.ID          = ASSET_SNAP_ID
        A.key         = 's_snap'
        A.name        = 'Snap'
        A.fname_infix = 'snap'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        A.path_key    = 'path_snap'
    elif asset_kind == ASSET_BOXFRONT_ID:
        A.ID          = ASSET_BOXFRONT_ID
        A.key         = 's_boxfront'
        A.name        = 'Boxfront'
        A.fname_infix = 'boxfront'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        A.path_key    = 'path_boxfront'
    elif asset_kind == ASSET_BOXBACK_ID:
        A.ID          = ASSET_BOXBACK_ID
        A.key         = 's_boxback'
        A.name        = 'Boxback'
        A.fname_infix = 'boxback'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        A.path_key    = 'path_boxback'
    elif asset_kind == ASSET_CARTRIDGE_ID:
        A.ID          = ASSET_CARTRIDGE_ID
        A.key         = 's_cartridge'
        A.name        = 'Cartridge'
        A.fname_infix = 'cartridge'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        A.path_key    = 'path_cartridge'
    elif asset_kind == ASSET_FLYER_ID:
        A.ID          = ASSET_FLYER_ID
        A.key         = 's_flyer'
        A.name        = 'Flyer'
        A.fname_infix = 'flyer'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        A.path_key    = 'path_flyer'
    elif asset_kind == ASSET_3DBOX_ID:
        A.ID          = ASSET_3DBOX_ID
        A.key         = 's_3dbox'
        A.name        = '3D Box'
        A.fname_infix = '3dbox'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        A.path_key    = 'path_3dbox'
    elif asset_kind == ASSET_MAP_ID:
        A.ID          = ASSET_MAP_ID
        A.key         = 's_map'
        A.name        = 'Map'
        A.fname_infix = 'map'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        A.path_key    = 'path_map'
    elif asset_kind == ASSET_MANUAL_ID:
        A.ID          = ASSET_MANUAL_ID
        A.key         = 's_manual'
        A.name        = 'Manual'
        A.fname_infix = 'manual'
        A.kind_str    = 'manual'
        A.exts        = asset_get_filesearch_extension_list(MANUAL_EXTENSION_LIST)
        A.exts_dialog = asset_get_dialog_extension_list(MANUAL_EXTENSION_LIST)
        A.path_key    = 'path_manual'
    else:
        log_error('assets_get_info_scheme() Wrong asset_kind = {}'.format(asset_kind))

    # --- Ultra DEBUG ---
    # log_debug('assets_get_info_scheme() asset_kind    {}'.format(asset_kind))
    # log_debug('assets_get_info_scheme() A.key         {}'.format(A.key))
    # log_debug('assets_get_info_scheme() A.name        {}'.format(A.name))
    # log_debug('assets_get_info_scheme() A.fname_infix {}'.format(A.fname_infix))
    # log_debug('assets_get_info_scheme() A.kind_str    {}'.format(A.kind_str))
    # log_debug('assets_get_info_scheme() A.exts        {}'.format(A.exts))
    # log_debug('assets_get_info_scheme() A.exts_dialog {}'.format(A.exts_dialog))
    # log_debug('assets_get_info_scheme() A.path_key    {}'.format(A.path_key))

    return A

# Scheme DIR uses different directories for artwork and no sufixes.
#
# Assets    -> Assets info object
# AssetPath -> FileName object
# ROM       -> ROM name FileName object
#
# Returns a FileName object
def assets_get_path_noext_DIR(Asset, AssetPath, ROM):
    return AssetPath.pjoin(ROM.getBaseNoExt())

# Scheme SUFIX uses suffixes for artwork. All artwork assets are stored in the same directory.
# Name example: "Sonic The Hedgehog (Europe)_a3e_title"
# First 3 characters of the objectID are added to avoid overwriting of images. For example, in the
# Favourites special category there could be ROMs with the same name for different systems.
#
# Asset             AssetInfo object
# AssetPath         FileName object
# asset_base_noext  Unicode string
# objectID          Object MD5 ID fingerprint (Unicode string)
#
# Returns asset/artwork path_noext as FileName object.
def assets_get_path_noext_SUFIX(Asset, AssetPath, asset_base_noext, objectID = '000'):
    asset_path_noext_FileName = FileName('')
    objectID_str = '_' + objectID[0:3]

    if Asset.ID == ASSET_ICON_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_icon')
    elif Asset.ID == ASSET_FANART_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_fanart')
    elif Asset.ID == ASSET_BANNER_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_banner')
    elif Asset.ID == ASSET_POSTER_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_poster')
    elif Asset.ID == ASSET_CLEARLOGO_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_clearlogo')
    elif Asset.ID == ASSET_CONTROLLER_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_controller')
    elif Asset.ID == ASSET_TRAILER_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_trailer')
    elif Asset.ID == ASSET_TITLE_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_title')
    elif Asset.ID == ASSET_SNAP_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_snap')
    elif Asset.ID == ASSET_BOXFRONT_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_boxfront')
    elif Asset.ID == ASSET_BOXBACK_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_boxback')
    elif Asset.ID == ASSET_3DBOX_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_3dbox')
    elif Asset.ID == ASSET_CARTRIDGE_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_cartridge')
    elif Asset.ID == ASSET_FLYER_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_flyer')
    elif Asset.ID == ASSET_MAP_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_map')
    elif Asset.ID == ASSET_MANUAL_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_manual')
    else:
        raise KodiAddonError('assets_get_path_noext_SUFIX() Wrong asset ID = {}'.format(Asset.ID))

    return asset_path_noext_FileName

# Returns the basename of a collection asset as a FileName object.
# Example: 'Super Mario Bros_nes_title.png'
#
# TODO Make basename_noext safe (remove forbidden characters). It is the title of the
#      object, not necessarily a filename.
#
# Returns a Unicode string
def assets_get_collection_asset_basename(AInfo, basename_noext, platform, ext):
    pindex = get_AEL_platform_index(platform)
    platform_compact_name = AEL_platforms[pindex].compact_name

    return basename_noext + '_' + platform_compact_name + '_' + AInfo.fname_infix + ext

# Get a list of enabled assets.
#
# Returns tuple:
# configured_bool_list    List of boolean values. It has all assets defined in ROM_ASSET_ID_LIST
def asset_get_enabled_asset_list(launcher):
    configured_bool_list = [False] * len(ROM_ASSET_ID_LIST)

    # Check if asset paths are configured or not
    for i, asset in enumerate(ROM_ASSET_ID_LIST):
        A = assets_get_info_scheme(asset)
        configured_bool_list[i] = True if launcher[A.path_key] else False
        if not configured_bool_list[i]:
            log_debug('asset_get_enabled_asset_list() {:<9} path unconfigured'.format(A.name))
        else:
            log_debug('asset_get_enabled_asset_list() {:<9} path configured'.format(A.name))

    return configured_bool_list

# unconfigured_name_list  List of disabled asset names
def asset_get_unconfigured_name_list(configured_bool_list):
    unconfigured_name_list = []

    for i, asset in enumerate(ROM_ASSET_ID_LIST):
        A = assets_get_info_scheme(asset)
        if not configured_bool_list[i]:
            unconfigured_name_list.append(A.name)

    return unconfigured_name_list

#
# Get a list of assets with duplicated paths. Refuse to do anything if duplicated paths found.
#
def asset_get_duplicated_dir_list(launcher):
    duplicated_bool_list = [False] * len(ROM_ASSET_ID_LIST)
    duplicated_name_list = []

    # Check for duplicated asset paths
    for i, asset_i in enumerate(ROM_ASSET_ID_LIST[:-1]):
        A_i = assets_get_info_scheme(asset_i)
        for j, asset_j in enumerate(ROM_ASSET_ID_LIST[i+1:]):
            A_j = assets_get_info_scheme(asset_j)
            # >> Exclude unconfigured assets (empty strings).
            if not launcher[A_i.path_key] or not launcher[A_j.path_key]: continue
            # log_debug('asset_get_duplicated_asset_list() Checking {0:<9} vs {1:<9}'.format(A_i.name, A_j.name))
            if launcher[A_i.path_key] == launcher[A_j.path_key]:
                duplicated_bool_list[i] = True
                duplicated_name_list.append('{} and {}'.format(A_i.name, A_j.name))
                log_info('asset_get_duplicated_asset_list() DUPLICATED {} and {}'.format(A_i.name, A_j.name))

    return duplicated_name_list

# Search for local assets and place found files into a list.
# Returned list all has assets as defined in ROM_ASSET_ID_LIST.
# This function is used in the ROM Scanner.
#
# launcher               -> launcher dictionary
# ROMFile                -> FileName object
# enabled_ROM_ASSET_ID_LIST -> list of booleans
def assets_search_local_cached_assets(launcher, ROMFile, enabled_ROM_ASSET_ID_LIST):
    log_debug('assets_search_local_cached_assets() Searching for ROM local assets...')
    local_asset_list = [''] * len(ROM_ASSET_ID_LIST)
    rom_basename_noext = ROMFile.getBaseNoExt()
    for i, asset_kind in enumerate(ROM_ASSET_ID_LIST):
        AInfo = assets_get_info_scheme(asset_kind)
        if not enabled_ROM_ASSET_ID_LIST[i]:
            log_debug('Disabled {:<9}'.format(AInfo.name))
            continue
        local_asset = utils_file_cache_search(launcher[AInfo.path_key], rom_basename_noext, AInfo.exts)
        if local_asset:
            local_asset_list[i] = local_asset.getOriginalPath()
            log_debug('Found    {:<9} "{}"'.format(AInfo.name, local_asset_list[i]))
        else:
            local_asset_list[i] = ''
            log_debug('Missing  {:<9}'.format(AInfo.name))

    return local_asset_list

# Search for local assets and put found files into a list.
# This function is used in _roms_add_new_rom() where there is no need for a file cache.
def assets_search_local_assets(launcher, ROMFile, enabled_ROM_ASSET_ID_LIST):
    log_debug('assets_search_local_assets() Searching for ROM local assets...')
    local_asset_list = [''] * len(ROM_ASSET_ID_LIST)
    for i, asset_kind in enumerate(ROM_ASSET_ID_LIST):
        AInfo = assets_get_info_scheme(asset_kind)
        if not enabled_ROM_ASSET_ID_LIST[i]:
            log_debug('assets_search_local_assets() Disabled {:<9}'.format(AInfo.name))
            continue
        asset_path = FileName(launcher[AInfo.path_key])
        local_asset = utils_look_for_file(asset_path, ROMFile.getBaseNoExt(), AInfo.exts)

        if local_asset:
            local_asset_list[i] = local_asset.getOriginalPath()
            log_debug('assets_search_local_assets() Found    {:<9} "{}"'.format(AInfo.name, local_asset_list[i]))
        else:
            local_asset_list[i] = ''
            log_debug('assets_search_local_assets() Missing  {:<9}'.format(AInfo.name))

    return local_asset_list

# A) This function checks if all path_* share a common root directory. If so
#    this function returns that common directory as an Unicode string.
# B) If path_* do not share a common root directory this function returns ''.
# C) If path_* does not use the standard artwork directory this function will also return '',
#    so the exporting of the <path_*> tags will be forced.
def assets_get_ROM_asset_path(launcher):
    ROM_asset_path = ''
    duplicated_bool_list = [False] * len(ROM_ASSET_ID_LIST)
    AInfo_first = assets_get_info_scheme(ROM_ASSET_ID_LIST[0])
    path_first_asset_FN = FileName(launcher[AInfo_first.path_key])
    ROM_asset_path_FN = FileName(path_first_asset_FN.getDir())
    log_debug('assets_get_ROM_asset_path() path_first_asset_FN OP "{}"'.format(path_first_asset_FN.getOriginalPath()))
    log_debug('assets_get_ROM_asset_path() path_first_asset_FN Base "{}"'.format(path_first_asset_FN.getBase()))
    log_debug('assets_get_ROM_asset_path() ROM_asset_path_FN Dir "{}"'.format(ROM_asset_path_FN.getDir()))
    for i, asset_kind in enumerate(ROM_ASSET_ID_LIST):
        AInfo = assets_get_info_scheme(asset_kind)
        # If asset path is unconfigured consider it as common so a default path will
        # be created when importing.
        if not launcher[AInfo.path_key]:
            duplicated_bool_list[i] = True
            continue
        # If asset path is not the standard one force return of ''.
        current_path_FN = FileName(launcher[AInfo.path_key])
        default_dir = assets_get_default_artwork_dir(AInfo.ID, launcher)
        if default_dir != current_path_FN.getBase():
            duplicated_bool_list[i] = False
            continue
        # Check for common path, getDir() subtracts last directory.
        if current_path_FN.getDir() == ROM_asset_path_FN.getOriginalPath():
            duplicated_bool_list[i] = True
    ROM_asset_path_common = all(duplicated_bool_list)

    return ROM_asset_path_FN.getOriginalPath() if ROM_asset_path_common else ''
