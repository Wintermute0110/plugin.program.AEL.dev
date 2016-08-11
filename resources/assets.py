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
ASSET_CLEARLOGO = 500
ASSET_BOXFRONT  = 600
ASSET_BOXBACK   = 700
ASSET_CARTRIDGE = 800
ASSET_FLYER     = 900
ASSET_MAP       = 1000
ASSET_MANUAL    = 1100
ASSET_TRAILER   = 1200
ASSET_THUMB     = 1300 # Only used in Categories/Launchers

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
        assets_create_dir_or_abort(launcher['path_title'])
        assets_create_dir_or_abort(launcher['path_snap'])
        assets_create_dir_or_abort(launcher['path_fanart'])
        assets_create_dir_or_abort(launcher['path_banner'])
        assets_create_dir_or_abort(launcher['path_clearlogo'])        
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
# Gets asset name for category/launcher.
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
def assets_get_thumb_fallback_str(object_dic):
    default_asset = object_dic['default_thumb']
    asset_name_str = ''

    if   default_asset == 's_title':     asset_name_str = 'Title'
    elif default_asset == 's_snap':      asset_name_str = 'Snap'
    elif default_asset == 's_fanart':    asset_name_str = 'Fanart'
    elif default_asset == 's_banner':    asset_name_str = 'Banner'
    elif default_asset == 's_clearlogo': asset_name_str = 'Clearlogo'
    elif default_asset == 's_boxfront':  asset_name_str = 'Boxfront'
    elif default_asset == 's_boxback':   asset_name_str = 'Boxback'
    elif default_asset == 's_cartridge': asset_name_str = 'Cartridge'
    elif default_asset == 's_flyer':     asset_name_str = 'Flyer'
    elif default_asset == 's_map':       asset_name_str = 'Map'
    elif default_asset == 's_manual':    asset_name_str = 'Manual'
    elif default_asset == 's_trailer':   asset_name_str = 'Trailer'
    elif default_asset == 's_thumb':     asset_name_str = 'Thumb'
    else:
        kodi_notify_warn('Wrong default_thumb {0}'.format(default_asset))
        log_error('assets_get_thumb_fallback_str() Wrong default_thumb {0}'.format(default_asset))
    
    return asset_name_str

def assets_get_fanart_fallback_str(object_dic):
    default_asset = object_dic['default_fanart']
    asset_name_str = ''

    if   default_asset == 's_title':     asset_name_str = 'Title'
    elif default_asset == 's_snap':      asset_name_str = 'Snap'
    elif default_asset == 's_fanart':    asset_name_str = 'Fanart'
    elif default_asset == 's_banner':    asset_name_str = 'Banner'
    elif default_asset == 's_clearlogo': asset_name_str = 'Clearlogo'
    elif default_asset == 's_boxfront':  asset_name_str = 'Boxfront'
    elif default_asset == 's_boxback':   asset_name_str = 'Boxback'
    elif default_asset == 's_cartridge': asset_name_str = 'Cartridge'
    elif default_asset == 's_flyer':     asset_name_str = 'Flyer'
    elif default_asset == 's_map':       asset_name_str = 'Map'
    elif default_asset == 's_manual':    asset_name_str = 'Manual'
    elif default_asset == 's_trailer':   asset_name_str = 'Trailer'
    elif default_asset == 's_thumb':     asset_name_str = 'Thumb'
    else:
        kodi_notify_warn('Wrong default_fanart {0}'.format(default_asset))
        log_error('assets_get_fanart_fallback_str() Wrong default_fanart {0}'.format(default_asset))
    
    return asset_name_str

# -------------------------------------------------------------------------------------------------
# Gets all required information about an asset: path, name, etc.
# Returns an object with all the information
# -------------------------------------------------------------------------------------------------
class AssetInfo:
    key         = u''
    name        = u''
    kind_str    = u''
    exts_dialog = u''
    base_noext  = u''
    path_noext  = u''

#
# Scheme A uses different directories for artwork and no sufixxes.
#
def assets_get_info_scheme_A(asset_kind, asset_base_noext, launcher):
    A = AssetInfo()
    A.base_noext = asset_base_noext

    if asset_kind == ASSET_TITLE:
        A.key         = 's_title'
        A.name        = 'Title'
        A.kind_str    = 'image'
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_noext  = os.path.join(launcher['path_title'], asset_base_noext)
    elif asset_kind == ASSET_SNAP:
        A.key         = 's_snap'
        A.name        = 'Snap'
        A.kind_str    = 'image'
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_noext  = os.path.join(launcher['path_snap'], asset_base_noext)
    elif asset_kind == ASSET_FANART:
        A.key         = 's_fanart'
        A.name        = 'Fanart'
        A.kind_str    = 'image'
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_noext  = os.path.join(launcher['path_fanart'], asset_base_noext)
    elif asset_kind == ASSET_BANNER:
        A.key         = 's_banner'
        A.name        = 'Banner'
        A.kind_str    = 'image'
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_noext  = os.path.join(launcher['path_banner'], asset_base_noext)
    elif asset_kind == ASSET_CLEARLOGO:
        A.key         = 's_clearlogo'
        A.name        = 'Clearlogo'
        A.kind_str    = 'image'
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_noext  = os.path.join(launcher['path_clearlogo'], asset_base_noext)
    elif asset_kind == ASSET_BOXFRONT:
        A.key        = 's_boxfront'
        A.name       = 'Boxfront'
        A.kind_str   = 'image'
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_noext = os.path.join(launcher['path_boxfront'], asset_base_noext)
    elif asset_kind == ASSET_BOXBACK:
        A.key         = 's_boxback'
        A.name        = 'Boxback'
        A.kind_str    = 'image'
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_noext  = os.path.join(launcher['path_boxback'], asset_base_noext)
    elif asset_kind == ASSET_CARTRIDGE:
        A.key         = 's_cartridge'
        A.name        = 'Cartridge'
        A.kind_str    = 'image'
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_noext  = os.path.join(launcher['path_cartridge'], asset_base_noext)
    elif asset_kind == ASSET_FLYER:
        A.key         = 's_flyer'
        A.name        = 'Flyer'
        A.kind_str    = 'image'
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_noext  = os.path.join(launcher['path_flyer'], asset_base_noext)
    elif asset_kind == ASSET_MAP:
        A.key         = 's_map'
        A.name        = 'Title'
        A.kind_str    = 'image'
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_noext  = os.path.join(launcher['path_map'], asset_base_noext)
    elif asset_kind == ASSET_MANUAL:
        A.key         = 's_manual'
        A.name        = 'Manual'
        A.kind_str    = 'manual'
        A.exts_dialog = MANUAL_EXTS_DIALOG
        A.path_noext  = os.path.join(launcher['path_manual'], asset_base_noext)
    elif asset_kind == ASSET_TRAILER:
        A.key         = 's_trailer'
        A.name        = 'Trailer'
        A.kind_str    = 'video'
        A.exts_dialog = TRAILER_EXTS_DIALOG
        A.path_noext  = os.path.join(launcher['path_trailer'], asset_base_noext)
    else:
        log_error('assets_get_info_scheme_A() Wrong asset_kind = {0}'.format(asset_kind))

    # --- Ultra DEBUG ---
    # log_debug('assets_get_info_scheme_A() asset_kind    {0}'.format(asset_kind))
    # log_debug('assets_get_info_scheme_A() A.key         {0}'.format(A.key))
    # log_debug('assets_get_info_scheme_A() A.name        {0}'.format(A.name))
    # log_debug('assets_get_info_scheme_A() A.base_noext  {0}'.format(A.base_noext))
    # log_debug('assets_get_info_scheme_A() A.kind_str    {0}'.format(A.kind_str))
    # log_debug('assets_get_info_scheme_A() A.exts_dialog {0}'.format(A.exts_dialog))
    # log_debug('assets_get_info_scheme_A() A.path_noext  {0}'.format(A.path_noext))

    return A

#
# Scheme B uses suffixes for artwork. All artwork are stored in the same directory
#
def assets_get_info_scheme_B(asset_kind, asset_base_noext, asset_directory):
    A = AssetInfo()
    A.base_noext = asset_base_noext

    if asset_kind == ASSET_THUMB:
        A.key         = 's_thumb'
        A.name        = 'Thumb'
        A.kind_str    = 'image'
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_noext  = os.path.join(asset_directory, asset_base_noext + '_thumb')
    elif asset_kind == ASSET_FANART:
        A.key         = 's_fanart'
        A.name        = 'Fanart'
        A.kind_str    = 'image'
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_noext  = os.path.join(asset_directory, asset_base_noext + '_fanart')
    elif asset_kind == ASSET_BANNER:
        A.key         = 's_banner'
        A.name        = 'Banner'
        A.kind_str    = 'image'
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_noext  = os.path.join(asset_directory, asset_base_noext + '_banner')
    elif asset_kind == ASSET_FLYER:
        A.key         = 's_flyer'
        A.name        = 'Flyer'
        A.kind_str    = 'image'
        A.exts_dialog = IMAGE_EXTS_DIALOG
        A.path_noext  = os.path.join(asset_directory, asset_base_noext + '_flyer')
    elif asset_kind == ASSET_TRAILER:
        A.key         = 's_trailer'
        A.name        = 'Trailer'
        A.kind_str    = 'video'
        A.exts_dialog = TRAILER_EXTS_DIALOG
        A.path_noext  = os.path.join(asset_directory, asset_base_noext + '_trailer')
    else:
        log_error('assets_get_info_scheme_B() Wrong asset_kind = {0}'.format(asset_kind))

    # --- Ultra DEBUG ---
    # log_debug('assets_get_info_scheme_B() asset_kind    {0}'.format(asset_kind))
    # log_debug('assets_get_info_scheme_B() A.key         {0}'.format(A.key))
    # log_debug('assets_get_info_scheme_B() A.name        {0}'.format(A.name))
    # log_debug('assets_get_info_scheme_B() A.base_noext  {0}'.format(A.base_noext))
    # log_debug('assets_get_info_scheme_B() A.kind_str    {0}'.format(A.kind_str))
    # log_debug('assets_get_info_scheme_B() A.exts_dialog {0}'.format(A.exts_dialog))
    # log_debug('assets_get_info_scheme_B() A.path_noext  {0}'.format(A.path_noext))

    return A
