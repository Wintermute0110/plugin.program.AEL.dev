# -*- coding: utf-8 -*-
# Advanced Emulator Launcher asset (artwork) related stuff
#

# Copyright (c) 2016 Wintermute0110 <wintermute0110@gmail.com>
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
try:
    from utils_kodi import *
except:
    from utils_kodi_standalone import *

# --- Define "constants" ---
ASSET_TITLE     = 100
ASSET_SNAP      = 200
ASSET_FANART    = 300
ASSET_BANNER    = 400
ASSET_CLEARLOGO = 500
ASSET_BOXFRONT  = 600
ASSET_BOXBACK   = 700
ASSET_CARTRIDGE = 800
ASSET_FLYER     = 900
ASSET_MAP       = 1000
ASSET_MANUAL    = 1100
ASSET_TRAILER   = 1200
ASSET_THUMB     = 1300 # Only used in Categories/Launchers

#
# The order of this list must match order in dialog.select() in the GUI, or bad things will happen.
#
CATEGORY_ASSET_LIST = [
    ASSET_THUMB, ASSET_FANART, ASSET_BANNER, ASSET_FLYER, ASSET_TRAILER
]

ROM_ASSET_LIST = [
    ASSET_TITLE,     ASSET_SNAP,
    ASSET_FANART,    ASSET_BANNER,
    ASSET_CLEARLOGO, ASSET_BOXFRONT,
    ASSET_BOXBACK,   ASSET_CARTRIDGE,
    ASSET_FLYER,     ASSET_MAP,
    ASSET_MANUAL,    ASSET_TRAILER
]

# --- Plugin will search these file extensions for assets ---
IMAGE_EXTS          = [u'png', u'jpg', u'gif', u'jpeg', u'bmp', u'PNG', u'JPG', u'GIF', u'JPEG', u'BMP']
MANUAL_EXTS         = [u'pdf', u'PDF']
TRAILER_EXTS        = [u'mpg', u'mpeg', u'avi', u'MPG', u'MPEG', u'AVI']
IMAGE_EXTS_DIALOG   = u'.png|.jpg|.gif|.jpeg|.bmp'
MANUAL_EXTS_DIALOG  = u'.pdf'
TRAILER_EXTS_DIALOG = u'.mpg|.mpeg|.avi'

# -------------------------------------------------------------------------------------------------
# Asset functions
# -------------------------------------------------------------------------------------------------
# Creates path for assets (artwork) and automatically fills in the path_ fields in the launcher
# struct.
# 
def assets_init_asset_dir(asset_path, launcher):
    rom_path = launcher['rompath']
    log_verb('assets_init_asset_dir() rom_path   "{0}"'.format(rom_path))
    log_verb('assets_init_asset_dir() asset_path "{0}"'.format(asset_path))

    # Asset path is different from ROM path. Use naming sheme 1.
    if asset_path != rom_path:
        log_verb('assets_init_asset_dir() Using naming scheme 1')

        # >> Fill in launcher fields
        launcher['path_title']     = os.path.join(asset_path, 'titles').decode('utf-8')        
        launcher['path_snap']      = os.path.join(asset_path, 'snaps').decode('utf-8')
        launcher['path_fanart']    = os.path.join(asset_path, 'fanarts').decode('utf-8')
        launcher['path_banner']    = os.path.join(asset_path, 'banners').decode('utf-8')
        launcher['path_clearlogo'] = os.path.join(asset_path, 'clearlogos').decode('utf-8')
        launcher['path_boxfront']  = os.path.join(asset_path, 'boxfront').decode('utf-8')
        launcher['path_boxback']   = os.path.join(asset_path, 'boxback').decode('utf-8')
        launcher['path_cartridge'] = os.path.join(asset_path, 'cartridges').decode('utf-8')
        launcher['path_flyer']     = os.path.join(asset_path, 'flyers').decode('utf-8')
        launcher['path_map']       = os.path.join(asset_path, 'maps').decode('utf-8')
        launcher['path_manual']    = os.path.join(asset_path, 'manuals').decode('utf-8')
        launcher['path_trailer']   = os.path.join(asset_path, 'trailers').decode('utf-8')

        # >> Create asset directories
        assets_safe_create_dir(launcher['path_title'])
        assets_safe_create_dir(launcher['path_snap'])
        assets_safe_create_dir(launcher['path_fanart'])
        assets_safe_create_dir(launcher['path_banner'])
        assets_safe_create_dir(launcher['path_clearlogo'])        
        assets_safe_create_dir(launcher['path_boxfront'])
        assets_safe_create_dir(launcher['path_boxback'])
        assets_safe_create_dir(launcher['path_cartridge'])
        assets_safe_create_dir(launcher['path_flyer'])
        assets_safe_create_dir(launcher['path_map'])
        assets_safe_create_dir(launcher['path_manual'])
        assets_safe_create_dir(launcher['path_trailer'])

    # Asset path is same as ROM path. Use naming sheme 2.
    else:
        log_verb('assets_init_asset_dir() Using naming scheme 2')

def assets_safe_create_dir(directory):
    log_debug('assets_safe_create_dir() Creating dir "{0}"'.format(directory))
    if not os.path.exists(directory): 
        os.makedirs(directory)

#
# Get artwork user configured to be used as thumb/fanart/
#
def asset_get_default_asset_Category(object_dic, object_key, default_asset = ''):
    conf_asset_key = object_dic[object_key]
    thumb_path     = object_dic[conf_asset_key] if object_dic[conf_asset_key] else default_asset

    return thumb_path

def asset_get_default_asset_Launcher_ROM(rom, launcher, object_key, default_asset = ''):
    conf_asset_key = launcher[object_key]
    thumb_path     = rom[conf_asset_key] if rom[conf_asset_key] else default_asset

    return thumb_path

#
# Gets a human readable name string for the default fallback thumb
#
def assets_get_asset_name_str(default_asset):
    asset_name_str = u''

    if   default_asset == 's_title':     asset_name_str = u'Title'
    elif default_asset == 's_snap':      asset_name_str = u'Snap'
    elif default_asset == 's_fanart':    asset_name_str = u'Fanart'
    elif default_asset == 's_banner':    asset_name_str = u'Banner'
    elif default_asset == 's_clearlogo': asset_name_str = u'Clearlogo'
    elif default_asset == 's_boxfront':  asset_name_str = u'Boxfront'
    elif default_asset == 's_boxback':   asset_name_str = u'Boxback'
    elif default_asset == 's_cartridge': asset_name_str = u'Cartridge'
    elif default_asset == 's_flyer':     asset_name_str = u'Flyer'
    elif default_asset == 's_map':       asset_name_str = u'Map'
    elif default_asset == 's_manual':    asset_name_str = u'Manual'
    elif default_asset == 's_trailer':   asset_name_str = u'Trailer'
    elif default_asset == 's_thumb':     asset_name_str = u'Thumb'
    else:
        kodi_notify_warn('Wrong asset key {0}'.format(default_asset))
        log_error('assets_get_asset_name_str() Wrong default_thumb {0}'.format(default_asset))
    
    return asset_name_str


DEFAULT_CATEGORY_ASSET_LIST = ['Thumbnail', 'Fanart', 'Banner', 'Flyer']

def assets_choose_category_artwork(dict_object, key, index):
    if   index == 0: dict_object[key] = 's_thumb'
    elif index == 1: dict_object[key] = 's_fanart'
    elif index == 2: dict_object[key] = 's_banner'
    elif index == 3: dict_object[key] = 's_flyer'

DEFAULT_ROM_ASSET_LIST = ['Title', 'Snap', 'Fanart', 'Banner', 'Clearlogo', 'Boxfront', 
                          'Boxback', 'Cartridge', 'Flyer', 'Map']

def assets_choose_category_ROM(dict_object, key, index):
    if   index == 0: dict_object[key] = 's_title'
    elif index == 1: dict_object[key] = 's_snap'
    elif index == 2: dict_object[key] = 's_fanart'
    elif index == 3: dict_object[key] = 's_banner'
    elif index == 4: dict_object[key] = 's_clearlogo'
    elif index == 5: dict_object[key] = 's_boxfront'
    elif index == 6: dict_object[key] = 's_boxback'
    elif index == 7: dict_object[key] = 's_cartridge'
    elif index == 8: dict_object[key] = 's_flyer'
    elif index == 9: dict_object[key] = 's_map'

# -------------------------------------------------------------------------------------------------
# Gets all required information about an asset: path, name, etc.
# Returns an object with all the information
# -------------------------------------------------------------------------------------------------
class AssetInfo:
    kind        = 0
    key         = ''
    name        = ''
    kind_str    = ''
    exts        = []
    exts_dialog = []
    path_key    = ''

def assets_get_info_scheme(asset_kind):
    A = AssetInfo()

    if asset_kind == ASSET_TITLE:
        A.kind        = ASSET_TITLE
        A.key         = 's_title'
        A.name        = 'Title'
        A.kind_str    = 'image'
        A.exts        = IMAGE_EXTS
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_key    = 'path_title'
    elif asset_kind == ASSET_SNAP:
        A.kind        = ASSET_SNAP
        A.key         = 's_snap'
        A.name        = 'Snap'
        A.kind_str    = 'image'
        A.exts        = IMAGE_EXTS
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_key    = 'path_snap'
    elif asset_kind == ASSET_FANART:
        A.kind        = ASSET_FANART
        A.key         = 's_fanart'
        A.name        = 'Fanart'
        A.kind_str    = 'image'
        A.exts        = IMAGE_EXTS
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_key    = 'path_fanart'
    elif asset_kind == ASSET_BANNER:
        A.kind        = ASSET_BANNER
        A.key         = 's_banner'
        A.name        = 'Banner'
        A.kind_str    = 'image'
        A.exts        = IMAGE_EXTS
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_key    = 'path_banner'
    elif asset_kind == ASSET_CLEARLOGO:
        A.kind        = ASSET_CLEARLOGO
        A.key         = 's_clearlogo'
        A.name        = 'Clearlogo'
        A.kind_str    = 'image'
        A.exts        = IMAGE_EXTS
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_key    = 'path_clearlogo'
    elif asset_kind == ASSET_BOXFRONT:
        A.kind        = ASSET_BOXFRONT
        A.key        = 's_boxfront'
        A.name       = 'Boxfront'
        A.kind_str   = 'image'
        A.exts        = IMAGE_EXTS
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_key    = 'path_boxfront'
    elif asset_kind == ASSET_BOXBACK:
        A.kind        = ASSET_BOXBACK
        A.key         = 's_boxback'
        A.name        = 'Boxback'
        A.kind_str    = 'image'
        A.exts        = IMAGE_EXTS
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_key    = 'path_boxback'
    elif asset_kind == ASSET_CARTRIDGE:
        A.kind        = ASSET_CARTRIDGE
        A.key         = 's_cartridge'
        A.name        = 'Cartridge'
        A.kind_str    = 'image'
        A.exts        = IMAGE_EXTS
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_key    = 'path_cartridge'
    elif asset_kind == ASSET_FLYER:
        A.kind        = ASSET_FLYER
        A.key         = 's_flyer'
        A.name        = 'Flyer'
        A.kind_str    = 'image'
        A.exts        = IMAGE_EXTS
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_key    = 'path_flyer'
    elif asset_kind == ASSET_MAP:
        A.kind        = ASSET_MAP
        A.key         = 's_map'
        A.name        = 'Map'
        A.kind_str    = 'image'
        A.exts        = IMAGE_EXTS
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_key    = 'path_map'
    elif asset_kind == ASSET_MANUAL:
        A.kind        = ASSET_MANUAL
        A.key         = 's_manual'
        A.name        = 'Manual'
        A.kind_str    = 'manual'
        A.exts        = MANUAL_EXTS
        A.exts_dialog = MANUAL_EXTS_DIALOG
        A.path_key    = 'path_manual'
    elif asset_kind == ASSET_TRAILER:
        A.kind        = ASSET_TRAILER
        A.key         = 's_trailer'
        A.name        = 'Trailer'
        A.kind_str    = 'video'
        A.exts        = TRAILER_EXTS
        A.exts_dialog = TRAILER_EXTS_DIALOG
        A.path_key    = 'path_trailer'
    elif asset_kind == ASSET_THUMB:
        A.kind        = ASSET_THUMB
        A.key         = 's_thumb'
        A.name        = 'Thumb'
        A.kind_str    = 'image'
        A.exts        = IMAGE_EXTS
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_key    = 'path_thumb'
    else:
        log_error('assets_get_info_scheme_A() Wrong asset_kind = {0}'.format(asset_kind))

    # --- Ultra DEBUG ---
    # log_debug('assets_get_info_scheme() asset_kind    {0}'.format(asset_kind))
    # log_debug('assets_get_info_scheme() A.key         {0}'.format(A.key))
    # log_debug('assets_get_info_scheme() A.name        {0}'.format(A.name))
    # log_debug('assets_get_info_scheme() A.base_noext  {0}'.format(A.base_noext))
    # log_debug('assets_get_info_scheme() A.kind_str    {0}'.format(A.kind_str))
    # log_debug('assets_get_info_scheme() A.exts_dialog {0}'.format(A.exts_dialog))
    # log_debug('assets_get_info_scheme() A.path_noext  {0}'.format(A.path_noext))

    return A

#
# Scheme A uses different directories for artwork and no sufixes.
#
def assets_get_path_noext_DIR(Asset, asset_path, asset_base_noext):
    # >> Returns asset/artwork path_noext
    return os.path.join(asset_path, asset_base_noext)

#
# Scheme B uses suffixes for artwork. All artwork are stored in the same directory
#
def assets_get_path_noext_SUFIX(Asset, asset_path, asset_base_noext):
    # >> Returns asset/artwork path_noext
    asset_path_noext = ''
    
    if   Asset.kind == ASSET_TITLE:     asset_path_noext = os.path.join(asset_path, asset_base_noext + '_title')
    elif Asset.kind == ASSET_SNAP:      asset_path_noext = os.path.join(asset_path, asset_base_noext + '_snap')
    elif Asset.kind == ASSET_FANART:    asset_path_noext = os.path.join(asset_path, asset_base_noext + '_fanart')
    elif Asset.kind == ASSET_BANNER:    asset_path_noext = os.path.join(asset_path, asset_base_noext + '_banner')
    elif Asset.kind == ASSET_CLEARLOGO: asset_path_noext = os.path.join(asset_path, asset_base_noext + '_clearlogo')
    elif Asset.kind == ASSET_BOXFRONT:  asset_path_noext = os.path.join(asset_path, asset_base_noext + '_boxfront')
    elif Asset.kind == ASSET_BOXBACK:   asset_path_noext = os.path.join(asset_path, asset_base_noext + '_boxback')
    elif Asset.kind == ASSET_CARTRIDGE: asset_path_noext = os.path.join(asset_path, asset_base_noext + '_cartridge')
    elif Asset.kind == ASSET_FLYER:     asset_path_noext = os.path.join(asset_path, asset_base_noext + '_flyer')
    elif Asset.kind == ASSET_MAP:       asset_path_noext = os.path.join(asset_path, asset_base_noext + '_map')
    elif Asset.kind == ASSET_MANUAL:    asset_path_noext = os.path.join(asset_path, asset_base_noext + '_manual')
    elif Asset.kind == ASSET_TRAILER:   asset_path_noext = os.path.join(asset_path, asset_base_noext + '_trailer')
    elif Asset.kind == ASSET_THUMB:     asset_path_noext = os.path.join(asset_path, asset_base_noext + '_thumb')
    else:
        log_error('assets_get_info_scheme_B() Wrong asset kind = {0}'.format(Asset.kind))

    return asset_path_noext

