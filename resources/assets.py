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
ASSET_BOXFRONT  = 500
ASSET_BOXBACK   = 600
ASSET_CARTRIDGE = 700
ASSET_FLYER     = 800
ASSET_MAP       = 900
ASSET_MANUAL    = 1000
ASSET_TRAILER   = 1100
ASSET_THUMB     = 1200 # Only used in Categories/Launchers
ASSET_LOGO      = 1300 # Only used in Categories/Launchers
ASSET_POSTER    = 1400 # Only used in Categories/Launchers

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
        launcher['path_boxfront']  = os.path.join(asset_path, 'boxfront').decode('utf-8')
        launcher['path_boxback']   = os.path.join(asset_path, 'boxback').decode('utf-8')
        launcher['path_cartridge'] = os.path.join(asset_path, 'cartridges').decode('utf-8')
        launcher['path_flyer']     = os.path.join(asset_path, 'flyers').decode('utf-8')
        launcher['path_map']       = os.path.join(asset_path, 'maps').decode('utf-8')
        launcher['path_manual']    = os.path.join(asset_path, 'manuals').decode('utf-8')
        launcher['path_trailer']   = os.path.join(asset_path, 'trailers').decode('utf-8')

        # >> Create asset directories
        assets_create_dir_or_abort(launcher['path_title'])
        assets_create_dir_or_abort(launcher['path_snap'])
        assets_create_dir_or_abort(launcher['path_fanart'])
        assets_create_dir_or_abort(launcher['path_banner'])
        assets_create_dir_or_abort(launcher['path_boxfront'])
        assets_create_dir_or_abort(launcher['path_boxback'])
        assets_create_dir_or_abort(launcher['path_cartridge'])
        assets_create_dir_or_abort(launcher['path_flyer'])
        assets_create_dir_or_abort(launcher['path_map'])
        assets_create_dir_or_abort(launcher['path_manual'])
        assets_create_dir_or_abort(launcher['path_trailer'])

    # Asset path is same as ROM path. Use naming sheme 2.
    else:
        log_verb('assets_init_asset_dir() Using naming scheme 2')

def assets_create_dir_or_abort(directory):
    log_debug('assets_create_dir_or_abort() Creating dir "{0}"'.format(directory))
    if not os.path.exists(directory): 
        os.makedirs(directory)

#
# Gets asset name for category/launcher
# A) Categories/Launchers always use naming scheme 2 (suffixes _thumb, _fanart, ...)
#
def assets_get_category_asset_path_noext(asset_kind, asset_dir, base_noext):
    if asset_kind == ASSET_THUMB:
        path_noext = os.path.join(asset_dir, base_noext + '_thumb')
    else:
        log_error('assets_get_category_asset_path_noext() Wrong asset_kind = {0}'.format(asset_kind))

    return path_noext

#
# Gets a human readable name string for the default fallback thumb
#
def assets_get_thumb_fallback_str(category):
    default_thumb = category['default_thumb']
    thumb_str = ''

    if   default_thumb == 's_thumb':  thumb_str = 'Thumb'
    elif default_thumb == 's_fanart': thumb_str = 'Fanart'
    elif default_thumb == 's_logo':   thumb_str = 'Logo'
    elif default_thumb == 's_poster': thumb_str = 'Poster'
    else:
        kody_nofity_warn('')
        log_error('')
    
    return thumb_str

def assets_get_fanart_fallback_str(category):
    default_thumb = category['default_fanart']
    thumb_str = ''

    if   default_thumb == 's_thumb':  thumb_str = 'Thumb'
    elif default_thumb == 's_fanart': thumb_str = 'Fanart'
    elif default_thumb == 's_logo':   thumb_str = 'Logo'
    elif default_thumb == 's_poster': thumb_str = 'Poster'
    else:
        kody_nofity_warn('')
        log_error('')
    
    return thumb_str
