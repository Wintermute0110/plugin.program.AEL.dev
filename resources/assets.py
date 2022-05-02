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

# Advanced Emulator Launcher asset (artwork) related stuff.

# --- Modules/packages in this plugin ---
import resources.const as const
import resources.platforms as platforms
import resources.log as log
import resources.utils as utils

# --- Python standard library ---
import collections
import os

# Get extensions to search for files
# Input : ['png', 'jpg']
# Output: ['png', 'jpg', 'PNG', 'JPG']
def get_filesearch_extension_list(exts):
    ext_list = list(exts)
    for ext in exts:
        ext_list.append(ext.upper())
    return ext_list

# Gets extensions to be used in Kodi file dialog.
# Input : ['png', 'jpg']
# Output: '.png|.jpg'
def get_dialog_extension_list(exts):
    ext_string = ''
    for ext in exts:
        ext_string += '.' + ext + '|'
    # Remove trailing '|' character
    ext_string = ext_string[:-1]
    return ext_string

# Gets extensions to be used in regular expressions.
# Input : ['png', 'jpg']
# Output: '(png|jpg)'
def get_regexp_extension_list(exts):
    ext_string = ''
    for ext in exts:
        ext_string += ext + '|'
    # Remove trailing '|' character
    ext_string = ext_string[:-1]
    return '(' + ext_string + ')'

# -------------------------------------------------------------------------------------------------
# Asset functions
# -------------------------------------------------------------------------------------------------
def get_default_artwork_dir(asset_ID, launcher):
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
def init_asset_dir(assets_path_FName, launcher):
    log.debug('init_asset_dir() asset_path "{}"'.format(assets_path_FName.getPath()))

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

# Create asset path and assign it to Launcher dictionary.
def parse_asset_dir(launcher, assets_path_FName, key, pathName):
    subPath = assets_path_FName.pjoin(pathName)
    launcher[key] = subPath.getOriginalPath()
    log.debug('parse_asset_dir() Creating dir "{}"'.format(subPath.getPath()))
    subPath.makedirs()

# Get artwork user configured to be used as icon/fanart/... for Categories/Launchers
def get_default_asset_Category(object_dic, object_key, default_asset = ''):
    conf_asset_key = object_dic[object_key]
    asset_path = object_dic[conf_asset_key] if object_dic[conf_asset_key] else default_asset
    return asset_path

# Same for ROMs
def get_default_asset_Launcher_ROM(rom, launcher, object_key, default_asset = ''):
    conf_asset_key = launcher[object_key]
    asset_path = rom[conf_asset_key] if rom[conf_asset_key] else default_asset
    return asset_path

# Gets a human readable name string for the asset field name.
def get_asset_name_str(default_asset):
    asset_name_str = ''

    # ROMs
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
    # Categories/Launchers
    elif default_asset == 's_icon':       asset_name_str = 'Icon'
    elif default_asset == 's_poster':     asset_name_str = 'Poster'
    elif default_asset == 's_controller': asset_name_str = 'Controller'
    else:
        kodi_notify_warn('Wrong asset key {}'.format(default_asset))
        log.error('get_asset_name_str() Wrong default_thumb {}'.format(default_asset))

    return asset_name_str

# This must match the order of the list Category_asset_ListItem_list in _command_edit_category()
def choose_Category_mapped_artwork(dict_object, key, index):
    if   index == 0: dict_object[key] = 's_icon'
    elif index == 1: dict_object[key] = 's_fanart'
    elif index == 2: dict_object[key] = 's_banner'
    elif index == 3: dict_object[key] = 's_poster'
    elif index == 4: dict_object[key] = 's_clearlogo'

# This must match the order of the list Category_asset_ListItem_list in _command_edit_category()
def get_Category_mapped_asset_idx(dict_object, key):
    if   dict_object[key] == 's_icon':       index = 0
    elif dict_object[key] == 's_fanart':     index = 1
    elif dict_object[key] == 's_banner':     index = 2
    elif dict_object[key] == 's_poster':     index = 3
    elif dict_object[key] == 's_clearlogo':  index = 4
    else:                                    index = 0
    return index

# This must match the order of the list Launcher_asset_ListItem_list in _command_edit_launcher()
def choose_Launcher_mapped_artwork(dict_object, key, index):
    if   index == 0: dict_object[key] = 's_icon'
    elif index == 1: dict_object[key] = 's_fanart'
    elif index == 2: dict_object[key] = 's_banner'
    elif index == 3: dict_object[key] = 's_poster'
    elif index == 4: dict_object[key] = 's_clearlogo'
    elif index == 5: dict_object[key] = 's_controller'

# This must match the order of the list Launcher_asset_ListItem_list in _command_edit_launcher()
def get_Launcher_mapped_asset_idx(dict_object, key):
    if   dict_object[key] == 's_icon':       index = 0
    elif dict_object[key] == 's_fanart':     index = 1
    elif dict_object[key] == 's_banner':     index = 2
    elif dict_object[key] == 's_poster':     index = 3
    elif dict_object[key] == 's_clearlogo':  index = 4
    elif dict_object[key] == 's_controller': index = 5
    else:                                    index = 0
    return index

# This must match the order of the list ROM_asset_str_list in _command_edit_launcher()
def choose_ROM_mapped_artwork(dict_object, key, index):
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

# This must match the order of the list ROM_asset_str_list in _command_edit_launcher()
def get_ROM_mapped_asset_idx(dict_object, key):
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

# Scheme DIR uses different directories for artwork and no sufixes.
#
# Assets    -> Assets info object
# AssetPath -> FileName object
# ROM       -> ROM name FileName object
#
# Returns a FileName object
def get_path_noext_DIR(Asset, AssetPath, ROM):
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
def get_path_noext_SUFIX(Asset, AssetPath, asset_base_noext, objectID = '000'):
    asset_path_noext_FileName = utils.FileName('')
    objectID_str = '_' + objectID[0:3]

    if Asset.id == const.ASSET_ICON_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_icon')
    elif Asset.id == const.ASSET_FANART_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_fanart')
    elif Asset.id == const.ASSET_BANNER_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_banner')
    elif Asset.id == const.ASSET_POSTER_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_poster')
    elif Asset.id == const.ASSET_CLEARLOGO_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_clearlogo')
    elif Asset.id == const.ASSET_CONTROLLER_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_controller')
    elif Asset.id == const.ASSET_TRAILER_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_trailer')
    elif Asset.id == const.ASSET_TITLE_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_title')
    elif Asset.id == const.ASSET_SNAP_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_snap')
    elif Asset.id == const.ASSET_BOXFRONT_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_boxfront')
    elif Asset.id == const.ASSET_BOXBACK_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_boxback')
    elif Asset.id == const.ASSET_3DBOX_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_3dbox')
    elif Asset.id == const.ASSET_CARTRIDGE_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_cartridge')
    elif Asset.id == const.ASSET_FLYER_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_flyer')
    elif Asset.id == const.ASSET_MAP_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_map')
    elif Asset.id == const.ASSET_MANUAL_ID:
        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_manual')
    else:
        raise KodiAddonError('assets_get_path_noext_SUFIX() Wrong asset id = {}'.format(Asset.id))

    return asset_path_noext_FileName

# Get the asset path noext. Used in ScrapeStrategy.scrap_CM_asset_all()
# Returns a FileName object.
def get_ROM_path_noext(object_dic, data_dic, asset_ID):
    # Unpack data in data_dic
    ROM_FN = data_dic['ROM_FN']
    platform = data_dic['platform']
    categoryID = data_dic['categoryID']
    launcherID = data_dic['launcherID']
    settings = data_dic['settings']
    launchers = data_dic['launchers']

    # Misc data
    asset_info = assets_get_info_scheme(asset_ID)

    # Compute asset_path_noext_FN and return.
    if categoryID == VCATEGORY_FAVOURITES_ID:
        asset_dir_FN = FileName(settings['favourites_asset_dir'])
        asset_path_noext_FN = assets_get_path_noext_SUFIX(asset_info, asset_dir_FN, ROM_FN.getBaseNoExt(), object_dic['id'])
    elif categoryID == VCATEGORY_COLLECTIONS_ID:
        asset_dir_FN = FileName(settings['collections_asset_dir'])
        temp_str = assets_get_collection_asset_basename(asset_info, ROM_FN.getBaseNoExt(), platform, '.png')
        asset_path_noext_FN = asset_dir_FN.pjoin(FileName(temp_str).getBaseNoExt())
    else:
        asset_dir_FN = FileName(launchers[launcherID][asset_info.path_key])
        asset_path_noext_FN = assets_get_path_noext_DIR(asset_info, asset_dir_FN, ROM_FN)
    # log.debug('assets_get_ROM_path_noext() Return {}'.format(asset_path_noext_FN.getPath()))
    return asset_path_noext_FN

# Returns the basename of a collection asset as a FileName object.
# Example: 'Super Mario Bros_nes_title.png'
#
# TODO Make basename_noext safe (remove forbidden characters). It is the title of the
#      object, not necessarily a filename.
#
# Returns a Unicode string
def get_collection_asset_basename(AInfo, basename_noext, platform, ext):
    pindex = get_AEL_platform_index(platform)
    platform_compact_name = AEL_platforms[pindex].compact_name
    return basename_noext + '_' + platform_compact_name + '_' + AInfo.fname_infix + ext

# Get a list of enabled assets.
#
# Returns tuple:
# configured_bool_list    List of boolean values. It has all assets defined in ROM_ASSET_ID_LIST
def get_enabled_asset_list(launcher):
    configured_bool_list = [False] * len(ROM_ASSET_ID_LIST)

    # Check if asset paths are configured or not
    for i, asset in enumerate(ROM_ASSET_ID_LIST):
        A = assets_get_info_scheme(asset)
        configured_bool_list[i] = True if launcher[A.path_key] else False
        if not configured_bool_list[i]:
            log.debug('asset_get_enabled_asset_list() {:<9} path unconfigured'.format(A.name))
        else:
            log.debug('asset_get_enabled_asset_list() {:<9} path configured'.format(A.name))
    return configured_bool_list

# unconfigured_name_list  List of disabled asset names
def get_unconfigured_name_list(configured_bool_list):
    unconfigured_name_list = []
    for i, asset in enumerate(ROM_ASSET_ID_LIST):
        A = assets_get_info_scheme(asset)
        if not configured_bool_list[i]:
            unconfigured_name_list.append(A.name)
    return unconfigured_name_list

# Get a list of assets with duplicated paths. Refuse to do anything if duplicated paths found.
def get_duplicated_dir_list(launcher):
    duplicated_bool_list = [False] * len(ROM_ASSET_ID_LIST)
    duplicated_name_list = []
    # Check for duplicated asset paths
    for i, asset_i in enumerate(ROM_ASSET_ID_LIST[:-1]):
        A_i = get_info_scheme(asset_i)
        for j, asset_j in enumerate(ROM_ASSET_ID_LIST[i+1:]):
            A_j = get_info_scheme(asset_j)
            # Exclude unconfigured assets (empty strings).
            if not launcher[A_i.path_key] or not launcher[A_j.path_key]: continue
            # log.debug('asset_get_duplicated_asset_list() Checking {0:<9} vs {1:<9}'.format(A_i.name, A_j.name))
            if launcher[A_i.path_key] == launcher[A_j.path_key]:
                duplicated_bool_list[i] = True
                duplicated_name_list.append('{} and {}'.format(A_i.name, A_j.name))
                log.info('asset_get_duplicated_asset_list() DUPLICATED {} and {}'.format(A_i.name, A_j.name))
    return duplicated_name_list

# Search for local assets and place found files into a list.
# Returned list all has assets as defined in ROM_ASSET_ID_LIST.
# This function is used in the ROM Scanner.
#
# launcher               -> launcher dictionary
# ROMFile                -> FileName object
# enabled_ROM_ASSET_ID_LIST -> list of booleans
def search_local_cached_assets(launcher, ROMFile, enabled_ROM_ASSET_ID_LIST):
    log.debug('assets_search_local_cached_assets() Searching for ROM local assets...')
    local_asset_list = [''] * len(ROM_ASSET_ID_LIST)
    rom_basename_noext = ROMFile.getBaseNoExt()
    for i, asset_kind in enumerate(ROM_ASSET_ID_LIST):
        AInfo = assets_get_info_scheme(asset_kind)
        if not enabled_ROM_ASSET_ID_LIST[i]:
            log.debug('Disabled {:<9}'.format(AInfo.name))
            continue
        local_asset = utils_file_cache_search(launcher[AInfo.path_key], rom_basename_noext, AInfo.exts)
        if local_asset:
            local_asset_list[i] = local_asset.getOriginalPath()
            log.debug('Found    {:<9} "{}"'.format(AInfo.name, local_asset_list[i]))
        else:
            local_asset_list[i] = ''
            log.debug('Missing  {:<9}'.format(AInfo.name))

    return local_asset_list

# Search for local assets and put found files into a list.
# This function is used in _roms_add_new_rom() where there is no need for a file cache.
def assets_search_local_assets(launcher, ROMFile, enabled_ROM_ASSET_ID_LIST):
    log.debug('assets_search_local_assets() Searching for ROM local assets...')
    local_asset_list = [''] * len(ROM_ASSET_ID_LIST)
    for i, asset_kind in enumerate(ROM_ASSET_ID_LIST):
        AInfo = assets_get_info_scheme(asset_kind)
        if not enabled_ROM_ASSET_ID_LIST[i]:
            log.debug('assets_search_local_assets() Disabled {:<9}'.format(AInfo.name))
            continue
        asset_path = FileName(launcher[AInfo.path_key])
        local_asset = utils_look_for_file(asset_path, ROMFile.getBaseNoExt(), AInfo.exts)

        if local_asset:
            local_asset_list[i] = local_asset.getOriginalPath()
            log.debug('assets_search_local_assets() Found    {:<9} "{}"'.format(AInfo.name, local_asset_list[i]))
        else:
            local_asset_list[i] = ''
            log.debug('assets_search_local_assets() Missing  {:<9}'.format(AInfo.name))

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
    log.debug('assets_get_ROM_asset_path() path_first_asset_FN OP "{}"'.format(path_first_asset_FN.getOriginalPath()))
    log.debug('assets_get_ROM_asset_path() path_first_asset_FN Base "{}"'.format(path_first_asset_FN.getBase()))
    log.debug('assets_get_ROM_asset_path() ROM_asset_path_FN Dir "{}"'.format(ROM_asset_path_FN.getDir()))
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

# ------------------------------------------------------------------------------------------------
# Gets all required information about an object: category, launcher, ROM, etc.
# ------------------------------------------------------------------------------------------------
class ObjectInfo:
    def __init__(self):
        self.id              = 0
        self.name            = ''
        self.name_plural     = ''

a_category = ObjectInfo()
a_category.id          = const.OBJECT_CATEGORY_ID
a_category.name        = 'Category'
a_category.name_plural = 'Categories'

a_collection = ObjectInfo()
a_collection.id          = const.OBJECT_COLLECTION_ID
a_collection.name        = 'Collection'
a_collection.name_plural = 'Collections'

a_launcher = ObjectInfo()
a_launcher.id          = const.OBJECT_LAUNCHER_ID
a_launcher.name        = 'Launcher'
a_launcher.name_plural = 'Launchers'

a_ROM = ObjectInfo()
a_ROM.id          = const.OBJECT_ROM_ID
a_ROM.name        = 'ROM'
a_ROM.name_plural = 'ROMs'

OBJECT_INFO_DICT = {
    const.OBJECT_CATEGORY_ID   : a_category,
    const.OBJECT_COLLECTION_ID : a_collection,
    const.OBJECT_LAUNCHER_ID   : a_launcher,
    const.OBJECT_ROM_ID        : a_ROM,
}

# ------------------------------------------------------------------------------------------------
# Gets all required information about an asset: path, name, etc.
# Returns an object with all the information
# ------------------------------------------------------------------------------------------------
class AssetInfo:
    def __init__(self):
        self.id              = 0
        self.key             = ''
        self.default_key     = ''
        self.rom_default_key = ''
        self.name            = ''
        self.name_plural     = ''
        self.fname_infix     = '' # Used only when searching assets when importing XML
        self.kind_str        = ''
        self.exts            = []
        self.exts_dialog     = []
        self.path_key        = ''

    def get_description(self): return self.name

    def __eq__(self, other): return isinstance(other, AssetInfo) and self.id == other.id

    def __hash__(self): return self.id.__hash__()

# --- Static list of asset information objects ---------------------------------------------------
cached_filesearch_extension_list = get_filesearch_extension_list(const.IMAGE_EXTENSION_LIST)
cached_dialog_extension_list = get_dialog_extension_list(const.IMAGE_EXTENSION_LIST)

a_icon = AssetInfo()
a_icon.id              = const.ASSET_ICON_ID
a_icon.key             = 's_icon'
a_icon.default_key     = 'default_icon'
a_icon.rom_default_key = 'roms_default_icon'
a_icon.name            = 'Icon'
a_icon.name_plural     = 'Icons'
a_icon.fname_infix     = 'icon'
a_icon.kind_str        = 'image'
a_icon.exts            = cached_filesearch_extension_list
a_icon.exts_dialog     = cached_dialog_extension_list
a_icon.path_key        = 'path_icon'

a_fanart = AssetInfo()
a_fanart.id              = const.ASSET_FANART_ID
a_fanart.key             = 's_fanart'
a_fanart.default_key     = 'default_fanart'
a_fanart.rom_default_key = 'roms_default_fanart'
a_fanart.name            = 'Fanart'
a_fanart.plural          = 'Fanarts'
a_fanart.fname_infix     = 'fanart'
a_fanart.kind_str        = 'image'
a_fanart.exts            = cached_filesearch_extension_list
a_fanart.exts_dialog     = cached_dialog_extension_list
a_fanart.path_key        = 'path_fanart'

a_banner = AssetInfo()
a_banner.id                = const.ASSET_BANNER_ID
a_banner.key               = 's_banner'
a_banner.default_key       = 'default_banner'
a_banner.rom_default_key   = 'roms_default_banner'
a_banner.name              = 'Banner'
a_banner.description       = 'Banner / Marquee'
a_banner.plural            = 'Banners'
a_banner.fname_infix       = 'banner'
a_banner.kind_str          = 'image'
a_banner.exts              = cached_filesearch_extension_list
a_banner.exts_dialog       = cached_dialog_extension_list
a_banner.path_key          = 'path_banner'

a_poster = AssetInfo()        
a_poster.id                = const.ASSET_POSTER_ID
a_poster.key               = 's_poster'
a_poster.default_key       = 'default_poster'
a_poster.rom_default_key   = 'roms_default_poster'
a_poster.name              = 'Poster'
a_poster.plural            = 'Posters'
a_poster.fname_infix       = 'poster'
a_poster.kind_str          = 'image'
a_poster.exts              = cached_filesearch_extension_list
a_poster.exts_dialog       = cached_dialog_extension_list
a_poster.path_key          = 'path_poster'

a_clearlogo = AssetInfo()
a_clearlogo.id              = const.ASSET_CLEARLOGO_ID
a_clearlogo.key             = 's_clearlogo'
a_clearlogo.default_key     = 'default_clearlogo'
a_clearlogo.rom_default_key = 'roms_default_clearlogo'
a_clearlogo.name            = 'Clearlogo'
a_clearlogo.plural          = 'Clearlogos'
a_clearlogo.fname_infix     = 'clearlogo'
a_clearlogo.kind_str        = 'image'
a_clearlogo.exts            = cached_filesearch_extension_list
a_clearlogo.exts_dialog     = cached_dialog_extension_list
a_clearlogo.path_key        = 'path_clearlogo'

a_controller = AssetInfo()
a_controller.id             = const.ASSET_CONTROLLER_ID
a_controller.key            = 's_controller'
a_controller.name           = 'Controller'
a_controller.plural         = 'Controllers'
a_controller.fname_infix    = 'controller'
a_controller.kind_str       = 'image'
a_controller.exts           = cached_filesearch_extension_list
a_controller.exts_dialog    = cached_dialog_extension_list
a_controller.path_key       = 'path_controller'

a_trailer = AssetInfo()
a_trailer.id                = const.ASSET_TRAILER_ID
a_trailer.key               = 's_trailer'
a_trailer.name              = 'Trailer'
a_trailer.plural            = 'Trailers'
a_trailer.fname_infix       = 'trailer'
a_trailer.kind_str          = 'video'
a_trailer.exts              = get_filesearch_extension_list(const.TRAILER_EXTENSION_LIST)
a_trailer.exts_dialog       = get_dialog_extension_list(const.TRAILER_EXTENSION_LIST)
a_trailer.path_key          = 'path_trailer'

a_title = AssetInfo()
a_title.id                  = const.ASSET_TITLE_ID
a_title.key                 = 's_title'
a_title.name                = 'Title'
a_title.plural              = 'Titles'
a_title.fname_infix         = 'title'
a_title.kind_str            = 'image'
a_title.exts                = cached_filesearch_extension_list
a_title.exts_dialog         = cached_dialog_extension_list
a_title.path_key            = 'path_title'

a_snap = AssetInfo()
a_snap.id                   = const.ASSET_SNAP_ID
a_snap.key                  = 's_snap'
a_snap.name                 = 'Snap'
a_snap.plural               = 'Snaps'
a_snap.fname_infix          = 'snap'
a_snap.kind_str             = 'image'
a_snap.exts                 = cached_filesearch_extension_list
a_snap.exts_dialog          = cached_dialog_extension_list
a_snap.path_key             = 'path_snap'

a_boxfront = AssetInfo()
a_boxfront.id               = const.ASSET_BOXFRONT_ID
a_boxfront.key              = 's_boxfront'
a_boxfront.name             = 'Boxfront'
a_boxfront.description      = 'Boxfront / Cabinet'
a_boxfront.plural           = 'Boxfronts'
a_boxfront.fname_infix      = 'boxfront'
a_boxfront.kind_str         = 'image'
a_boxfront.exts             = cached_filesearch_extension_list
a_boxfront.exts_dialog      = cached_dialog_extension_list
a_boxfront.path_key         = 'path_boxfront'

a_boxback = AssetInfo()
a_boxback.id                = const.ASSET_BOXBACK_ID
a_boxback.key               = 's_boxback'
a_boxback.name              = 'Boxback'
a_boxback.description       = 'Boxback / CPanel'
a_boxback.plural            = 'Boxbacks'
a_boxback.fname_infix       = 'boxback'
a_boxback.kind_str          = 'image'
a_boxback.exts              = cached_filesearch_extension_list
a_boxback.exts_dialog       = cached_dialog_extension_list
a_boxback.path_key          = 'path_boxback'

a_cartridge = AssetInfo()
a_cartridge.id              = const.ASSET_CARTRIDGE_ID
a_cartridge.key             = 's_cartridge'
a_cartridge.name            = 'Cartridge'
a_cartridge.description     = 'Cartridge / PCB'
a_cartridge.plural          = 'Cartridges'
a_cartridge.fname_infix     = 'cartridge'
a_cartridge.kind_str        = 'image'
a_cartridge.exts            = cached_filesearch_extension_list
a_cartridge.exts_dialog     = cached_dialog_extension_list
a_cartridge.path_key        = 'path_cartridge'

a_flyer = AssetInfo()
a_flyer.id                  = const.ASSET_FLYER_ID
a_flyer.key                 = 's_flyer'
a_flyer.name                = 'Flyer'
a_flyer.plural              = 'Flyers'
a_flyer.fname_infix         = 'flyer'
a_flyer.kind_str            = 'image'
a_flyer.fname_infix         = 'poster'
a_flyer.exts                = cached_filesearch_extension_list
a_flyer.exts_dialog         = cached_dialog_extension_list
a_flyer.path_key            = 'path_flyer'

a_map = AssetInfo()
a_map.id                    = const.ASSET_MAP_ID
a_map.key                   = 's_map'
a_map.name                  = 'Map'
a_map.plural                = 'Maps'
a_map.fname_infix           = 'map'
a_map.kind_str              = 'image'
a_map.exts                  = cached_filesearch_extension_list
a_map.exts_dialog           = cached_dialog_extension_list
a_map.path_key              = 'path_map'

a_manual = AssetInfo()
a_manual.id                 = const.ASSET_MANUAL_ID
a_manual.key                = 's_manual'
a_manual.name               = 'Manual'
a_manual.plural             = 'Manuals'
a_manual.fname_infix        = 'manual'
a_manual.kind_str           = 'manual'
a_manual.exts               = get_filesearch_extension_list(const.MANUAL_EXTENSION_LIST)
a_manual.exts_dialog        = get_dialog_extension_list(const.MANUAL_EXTENSION_LIST)
a_manual.path_key           = 'path_manual'

# Get AssetInfo object by asset ID.
ASSET_INFO_DICT = {
    const.ASSET_ICON_ID       : a_icon,
    const.ASSET_FANART_ID     : a_fanart,
    const.ASSET_BANNER_ID     : a_banner,
    const.ASSET_POSTER_ID     : a_poster,
    const.ASSET_CLEARLOGO_ID  : a_clearlogo,
    const.ASSET_CONTROLLER_ID : a_controller,
    const.ASSET_TRAILER_ID    : a_trailer,
    const.ASSET_TITLE_ID      : a_title,
    const.ASSET_SNAP_ID       : a_snap,
    const.ASSET_BOXFRONT_ID   : a_boxfront,
    const.ASSET_BOXBACK_ID    : a_boxback,
    const.ASSET_CARTRIDGE_ID  : a_cartridge,
    const.ASSET_FLYER_ID      : a_flyer,
    const.ASSET_MAP_ID        : a_map,
    const.ASSET_MANUAL_ID     : a_manual,
}

# Get AssetInfo object by database key.
ASSET_INFO_KEY_DICT = {
    's_icon'       : a_icon,
    's_fanart'     : a_fanart,
    's_banner'     : a_banner,
    's_poster'     : a_poster,
    's_clearlogo'  : a_clearlogo,
    's_controller' : a_controller,
    's_trailer'    : a_trailer,
    's_title'      : a_title,
    's_snap'       : a_snap,
    's_boxfront'   : a_boxfront,
    's_boxback'    : a_boxback,
    's_cartridge'  : a_cartridge,
    's_flyer'      : a_flyer,
    's_map'        : a_map,
    's_manual'     : a_manual,
}

# ------------------------------------------------------------------------------------------------
# Class to interact with the asset engine.
# Only static methods.
# Put all the small functions in this file here.
# ------------------------------------------------------------------------------------------------
class Factory(object):
    # List with all asset object, in random order.
    @staticmethod
    def get_all(): return list(ASSET_INFO_DICT.values())

    # @staticmethod
    # def get_asset_info(self, asset_kind):
    #     asset_info = asset_infos.get(asset_kind, None)
    #     if asset_info is None:
    #         log_error('get_asset_info() Wrong asset_kind = {}'.format(asset_kind))
    #         return AssetInfo()
    #     return asset_info

    # todo: use 1 type of identifier not number constants and name strings ('s_icon')
    # @staticmethod
    # def get_asset_info_by_namekey(self, name_key):
    #     if name_key == '': return None
    #     kind = ASSET_KEYS_TO_CONSTANTS[name_key]
    #     return self.get_asset_info(kind)

    # List of object assets.
    @staticmethod
    def get_object_asset_list(object_ID):
        try:
            return const.OBJECT_ASSETS[object_ID]
        except:
            raise TypeError

    # IDs is a list of asset IDs (or an iterable that returns an asset ID).
    # Returns a list of AssetInfo objects.
    @staticmethod
    def get_asset_list_by_IDs(IDs): return [ASSET_INFO_DICT[asset_ID] for asset_ID in IDs]

    # Returns an ordered dictionary with all the object assets, ready to be edited.
    # This is used in the "Edit xxxxxx" context menus.
    # Keys are AssetInfo objects.
    # Values are the current file for the asset as Unicode string or '' if the asset is not set.
    @staticmethod
    def get_assets_odict(object_ID, edict):
        asset_list = Factory.get_object_asset_list(object_ID)
        asset_odict = collections.OrderedDict()
        for asset_ID in asset_list:
            asset_info = ASSET_INFO_DICT[asset_ID]
            asset_fname_str = edict[asset_info.key] if edict[asset_info.key] else ''
            asset_odict[asset_info] = asset_fname_str
        return asset_odict
