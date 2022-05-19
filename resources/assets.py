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
    for ext in exts: ext_list.append(ext.upper())
    return ext_list

# Gets extensions to be used in Kodi file dialog.
# Input : ['png', 'jpg']
# Output: '.png|.jpg'
def get_dialog_extension_list(exts):
    ext_string = ''
    for ext in exts: ext_string += '.' + ext + '|'
    # Remove trailing '|' character
    ext_string = ext_string[:-1]
    return ext_string

# Gets extensions to be used in regular expressions.
# Input : ['png', 'jpg']
# Output: '(png|jpg)'
def get_regexp_extension_list(exts):
    ext_string = ''
    for ext in exts: ext_string += ext + '|'
    # Remove trailing '|' character
    ext_string = ext_string[:-1]
    return '(' + ext_string + ')'

# -------------------------------------------------------------------------------------------------
# Asset functions
# -------------------------------------------------------------------------------------------------
# Creates path for assets (artwork) and automatically fills in the path_ fields in the launcher struct.
# Used at launcher creation time (wizard and XML configuration import).
def init_asset_dir(assets_path_FName, launcher):
    log.debug('init_asset_dir() asset_path "{}"'.format(assets_path_FName.getPath()))

    # --- Fill in launcher fields and create asset directories ---
    if launcher['platform'] == 'MAME':
        create_asset_dir(launcher, assets_path_FName, 'path_fanart', 'fanarts')
        create_asset_dir(launcher, assets_path_FName, 'path_banner', 'marquees')
        create_asset_dir(launcher, assets_path_FName, 'path_clearlogo', 'clearlogos')
        create_asset_dir(launcher, assets_path_FName, 'path_title', 'titles')
        create_asset_dir(launcher, assets_path_FName, 'path_snap', 'snaps')
        create_asset_dir(launcher, assets_path_FName, 'path_boxfront', 'cabinets')
        create_asset_dir(launcher, assets_path_FName, 'path_boxback', 'cpanels')
        create_asset_dir(launcher, assets_path_FName, 'path_3dbox', '3dboxes')
        create_asset_dir(launcher, assets_path_FName, 'path_cartridge', 'PCBs')
        create_asset_dir(launcher, assets_path_FName, 'path_flyer', 'flyers')
        create_asset_dir(launcher, assets_path_FName, 'path_map', 'maps')
        create_asset_dir(launcher, assets_path_FName, 'path_manual', 'manuals')
        create_asset_dir(launcher, assets_path_FName, 'path_trailer', 'trailers')
    else:
        create_asset_dir(launcher, assets_path_FName, 'path_fanart', 'fanarts')
        create_asset_dir(launcher, assets_path_FName, 'path_banner', 'banners')
        create_asset_dir(launcher, assets_path_FName, 'path_clearlogo', 'clearlogos')
        create_asset_dir(launcher, assets_path_FName, 'path_title', 'titles')
        create_asset_dir(launcher, assets_path_FName, 'path_snap', 'snaps')
        create_asset_dir(launcher, assets_path_FName, 'path_boxfront', 'boxfronts')
        create_asset_dir(launcher, assets_path_FName, 'path_boxback', 'boxbacks')
        create_asset_dir(launcher, assets_path_FName, 'path_3dbox', '3dboxes')
        create_asset_dir(launcher, assets_path_FName, 'path_cartridge', 'cartridges')
        create_asset_dir(launcher, assets_path_FName, 'path_flyer', 'flyers')
        create_asset_dir(launcher, assets_path_FName, 'path_map', 'maps')
        create_asset_dir(launcher, assets_path_FName, 'path_manual', 'manuals')
        create_asset_dir(launcher, assets_path_FName, 'path_trailer', 'trailers')

# Create asset directory and assign it to Launcher dictionary.
def create_asset_dir(launcher, assets_path_FName, key, pathName):
    subPath = assets_path_FName.pjoin(pathName)
    launcher[key] = subPath.getOriginalPath()
    log.debug('parse_asset_dir() Creating dir "{}"'.format(subPath.getPath()))
    subPath.makedirs()

# Get artwork user configured to be used as icon/fanart/... for Categories/Launchers
# Used when rendering Categories/Launchers.
def get_default_asset_Category(object_dic, object_key, default_asset = ''):
    conf_asset_key = object_dic[object_key]
    return object_dic[conf_asset_key] if object_dic[conf_asset_key] else default_asset

# Same for ROMs
def get_default_asset_Launcher_ROM(rom, launcher, object_key, default_asset = ''):
    conf_asset_key = launcher[object_key]
    return rom[conf_asset_key] if rom[conf_asset_key] else default_asset

# Scheme DIR uses different directories for artwork and no sufixes.
#
# Assets    -> Assets info object
# AssetPath -> FileName object
# ROM       -> ROM name FileName object
#
# Returns a FileName object
def get_path_noext_DIR(Asset, AssetPath, ROM): return AssetPath.pjoin(ROM.getBaseNoExt())

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
    for i, asset_ID in enumerate(ROM_ASSET_ID_LIST):
        AInfo = assets_get_info_scheme(asset_ID)
        # If asset path is unconfigured consider it as common so a default path will
        # be created when importing.
        if not launcher[AInfo.path_key]:
            duplicated_bool_list[i] = True
            continue
        # If asset path is not the standard one force return of ''.
        current_path_FN = utils.FileName(launcher[AInfo.path_key])
        # default_dir = assets_get_default_artwork_dir(AInfo.ID, launcher)
        # default_dir = AInfo.subdir_MAME if launcher['platform'] == 'MAME' else AInfo.subdir
        default_dir = AInfo.subdir_MAME if platforms.is_arcade_launcher(launcher) else AInfo.subdir
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
        self.name            = ''
        self.name_plural     = ''
        # Asset subdirectory name. Only used for ROMs?
        self.subdir          = ''
        # Asset subdirectory name for MAME (Arcade) platform. Only used for ROMs?
        self.subdir_MAME     = ''
        self.fname_infix     = '' # Used only when searching assets when importing XML
        self.type_str        = '' # Image, Video, etc.
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
a_icon.name            = 'Icon'
a_icon.name_plural     = 'Icons'
a_icon.subdir          = 'icons'
a_icon.subdir_MAME     = 'icons'
a_icon.fname_infix     = 'icon'
a_icon.type_str        = 'image'
a_icon.exts            = cached_filesearch_extension_list
a_icon.exts_dialog     = cached_dialog_extension_list
a_icon.path_key        = 'path_icon'

a_fanart = AssetInfo()
a_fanart.id              = const.ASSET_FANART_ID
a_fanart.key             = 's_fanart'
a_fanart.name            = 'Fanart'
a_fanart.name_plural     = 'Fanarts'
a_fanart.subdir          = 'fanarts'
a_fanart.subdir_MAME     = 'fanarts'
a_fanart.fname_infix     = 'fanart'
a_fanart.type_str        = 'image'
a_fanart.exts            = cached_filesearch_extension_list
a_fanart.exts_dialog     = cached_dialog_extension_list
a_fanart.path_key        = 'path_fanart'

a_banner = AssetInfo()
a_banner.id              = const.ASSET_BANNER_ID
a_banner.key             = 's_banner'
a_banner.name            = 'Banner / Marquee'
a_banner.name_plural     = 'Banners / Marquees'
a_banner.subdir          = 'banners'
a_banner.subdir_MAME     = 'marquees'
a_banner.fname_infix     = 'banner'
a_banner.type_str        = 'image'
a_banner.exts            = cached_filesearch_extension_list
a_banner.exts_dialog     = cached_dialog_extension_list
a_banner.path_key        = 'path_banner'

a_poster = AssetInfo()        
a_poster.id              = const.ASSET_POSTER_ID
a_poster.key             = 's_poster'
a_poster.name            = 'Poster / Flyer'
a_poster.name_plural     = 'Posters / Flyers'
a_poster.subdir          = 'posters'
a_poster.subdir_MAME     = 'flyers'
a_poster.fname_infix     = 'poster'
a_poster.type_str        = 'image'
a_poster.exts            = cached_filesearch_extension_list
a_poster.exts_dialog     = cached_dialog_extension_list
a_poster.path_key        = 'path_poster'

a_clearlogo = AssetInfo()
a_clearlogo.id              = const.ASSET_CLEARLOGO_ID
a_clearlogo.key             = 's_clearlogo'
a_clearlogo.name            = 'Clearlogo'
a_clearlogo.name_plural     = 'Clearlogos'
a_clearlogo.subdir          = 'clearlogos'
a_clearlogo.subdir_MAME     = 'clearlogos'
a_clearlogo.fname_infix     = 'clearlogo'
a_clearlogo.type_str        = 'image'
a_clearlogo.exts            = cached_filesearch_extension_list
a_clearlogo.exts_dialog     = cached_dialog_extension_list
a_clearlogo.path_key        = 'path_clearlogo'

a_controller = AssetInfo()
a_controller.id          = const.ASSET_CONTROLLER_ID
a_controller.key         = 's_controller'
a_controller.name        = 'Controller'
a_controller.name_plural = 'Controllers'
a_controller.subdir      = 'controllers'
a_controller.subdir_MAME = 'controllers'
a_controller.fname_infix = 'controller'
a_controller.type_str    = 'image'
a_controller.exts        = cached_filesearch_extension_list
a_controller.exts_dialog = cached_dialog_extension_list
a_controller.path_key    = 'path_controller'

a_trailer = AssetInfo()
a_trailer.id          = const.ASSET_TRAILER_ID
a_trailer.key         = 's_trailer'
a_trailer.name        = 'Trailer'
a_trailer.name_plural = 'Trailers'
a_trailer.subdir      = 'trailers'
a_trailer.subdir_MAME = 'trailers'
a_trailer.fname_infix = 'trailer'
a_trailer.type_str    = 'video'
a_trailer.exts        = get_filesearch_extension_list(const.TRAILER_EXTENSION_LIST)
a_trailer.exts_dialog = get_dialog_extension_list(const.TRAILER_EXTENSION_LIST)
a_trailer.path_key    = 'path_trailer'

a_title = AssetInfo()
a_title.id          = const.ASSET_TITLE_ID
a_title.key         = 's_title'
a_title.name        = 'Title'
a_title.name_plural = 'Titles'
a_title.subdir      = 'titles'
a_title.subdir_MAME = 'titles'
a_title.fname_infix = 'title'
a_title.type_str    = 'image'
a_title.exts        = cached_filesearch_extension_list
a_title.exts_dialog = cached_dialog_extension_list
a_title.path_key    = 'path_title'

a_snap = AssetInfo()
a_snap.id          = const.ASSET_SNAP_ID
a_snap.key         = 's_snap'
a_snap.name        = 'Snap'
a_snap.name_plural = 'Snaps'
a_snap.subdir      = 'snaps'
a_snap.subdir_MAME = 'snaps'
a_snap.fname_infix = 'snap'
a_snap.type_str    = 'image'
a_snap.exts        = cached_filesearch_extension_list
a_snap.exts_dialog = cached_dialog_extension_list
a_snap.path_key    = 'path_snap'

a_boxfront = AssetInfo()
a_boxfront.id          = const.ASSET_BOXFRONT_ID
a_boxfront.key         = 's_boxfront'
a_boxfront.name        = 'Boxfront / Cabinet'
a_boxfront.name_plural = 'Boxfronts / Cabinets'
a_boxfront.subdir      = 'boxfronts'
a_boxfront.subdir_MAME = 'cabinets'
a_boxfront.fname_infix = 'boxfront'
a_boxfront.type_str    = 'image'
a_boxfront.exts        = cached_filesearch_extension_list
a_boxfront.exts_dialog = cached_dialog_extension_list
a_boxfront.path_key    = 'path_boxfront'

a_boxback = AssetInfo()
a_boxback.id          = const.ASSET_BOXBACK_ID
a_boxback.key         = 's_boxback'
a_boxback.name        = 'Boxback / CPanel'
a_boxback.name_plural = 'Boxbacks / CPanels'
a_boxback.subdir      = 'boxbacks'
a_boxback.subdir_MAME = 'cpanels'
a_boxback.fname_infix = 'boxback'
a_boxback.type_str    = 'image'
a_boxback.exts        = cached_filesearch_extension_list
a_boxback.exts_dialog = cached_dialog_extension_list
a_boxback.path_key    = 'path_boxback'

a_3dbox = AssetInfo()
a_3dbox.id          = const.ASSET_3DBOX_ID
a_3dbox.key         = 's_3dbox'
a_3dbox.name        = '3D Box'
a_3dbox.name_plural = '3D Boxes'
a_3dbox.subdir      = '3dboxes'
a_3dbox.subdir_MAME = '3dboxes'
a_3dbox.fname_infix = '3dbox'
a_3dbox.type_str    = 'image'
a_3dbox.exts        = cached_filesearch_extension_list
a_3dbox.exts_dialog = cached_dialog_extension_list
a_3dbox.path_key    = 'path_3dbox'

a_cartridge = AssetInfo()
a_cartridge.id          = const.ASSET_CARTRIDGE_ID
a_cartridge.key         = 's_cartridge'
a_cartridge.name        = 'Cartridge / PCB'
a_cartridge.name_plural = 'Cartridges / PCBs'
a_cartridge.subdir      = 'cartridges'
a_cartridge.subdir_MAME = 'PCBs'
a_cartridge.fname_infix = 'cartridge'
a_cartridge.type_str    = 'image'
a_cartridge.exts        = cached_filesearch_extension_list
a_cartridge.exts_dialog = cached_dialog_extension_list
a_cartridge.path_key    = 'path_cartridge'

a_flyer = AssetInfo()
a_flyer.id          = const.ASSET_FLYER_ID
a_flyer.key         = 's_flyer'
a_flyer.name        = 'Flyer'
a_flyer.name_plural = 'Flyers'
a_flyer.subdir      = 'flyers'
a_flyer.subdir_MAME = 'flyers'
a_flyer.fname_infix = 'flyer'
a_flyer.type_str    = 'image'
a_flyer.fname_infix = 'poster'
a_flyer.exts        = cached_filesearch_extension_list
a_flyer.exts_dialog = cached_dialog_extension_list
a_flyer.path_key    = 'path_flyer'

a_map = AssetInfo()
a_map.id          = const.ASSET_MAP_ID
a_map.key         = 's_map'
a_map.name        = 'Map'
a_map.name_plural = 'Maps'
a_map.subdir      = 'maps'
a_map.subdir_MAME = 'maps'
a_map.fname_infix = 'map'
a_map.type_str    = 'image'
a_map.exts        = cached_filesearch_extension_list
a_map.exts_dialog = cached_dialog_extension_list
a_map.path_key    = 'path_map'

a_manual = AssetInfo()
a_manual.id          = const.ASSET_MANUAL_ID
a_manual.key         = 's_manual'
a_manual.name        = 'Manual'
a_manual.name_plural = 'Manuals'
a_manual.subdir      = 'manuals'
a_manual.subdir_MAME = 'manuals'
a_manual.fname_infix = 'manual'
a_manual.type_str    = 'manual'
a_manual.exts        = get_filesearch_extension_list(const.MANUAL_EXTENSION_LIST)
a_manual.exts_dialog = get_dialog_extension_list(const.MANUAL_EXTENSION_LIST)
a_manual.path_key    = 'path_manual'

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
    const.ASSET_3DBOX_ID      : a_3dbox,
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
    's_3dbox'      : a_3dbox,
    's_cartridge'  : a_cartridge,
    's_flyer'      : a_flyer,
    's_map'        : a_map,
    's_manual'     : a_manual,
}

# IDs is a list of asset IDs (or an iterable that returns an asset ID).
# Returns a list of AssetInfo objects.
def get_asset_info_list_from_IDs(IDs):
    try:
        return [ASSET_INFO_DICT[asset_ID] for asset_ID in IDs]
    except:
        raise TypeError

# Returns an ordered dictionary with all the object assets, ready to be edited.
# This is used in the "Edit Category/Launcher/ROM" context menus.
# Dictionary keys are AssetInfo objects.
# Dictionary values are the current file for the asset as string or '' if the asset is not set.
def get_assets_odict(object_ID, edict):
    asset_odict = collections.OrderedDict()
    for asset_ID in const.OBJECT_ASSETS[object_ID]:
        asset_info = ASSET_INFO_DICT[asset_ID]
        asset_fname_str = edict[asset_info.key] if edict[asset_info.key] else ''
        asset_odict[asset_info] = asset_fname_str
    return asset_odict

# Given an object dict, object database dictionary and AssetInfo object, obtain the asset
# data like name and filename. Used in mgui_edit_asset() and ...
# --- Parameters ---
# Write me.
# --- Return ---
# Returns a dictionary afn (Asset FileName) with the following fields:
# afn['name'] = 'Category'
# afn['asset_dir'] = FileName object.
# afn['asset_path_noext'] = FileName object.
def get_asset_info(cfg, object_ID, edict, AInfo):
    afn = {
        'name' : '',
        'asset_dir' : '',
        'asset_path_noext' : '',
    }

    if object_ID == const.OBJECT_CATEGORY_ID:
        afn['name'] = 'Category'
        afn['asset_dir'] = utils.FileName(cfg.settings['categories_asset_dir'])
        afn['asset_path_noext'] = get_path_noext_SUFIX(AInfo, afn['asset_dir'], edict['m_name'], edict['id'])
        log.info('get_asset_info() Category "{}"'.format(AInfo.name))
        log.info('get_asset_info() Category ID {}'.format(edict['id']))

    elif object_ID == const.OBJECT_COLLECTION_ID:
        afn['name'] = 'ROM Collection'
        afn['asset_dir'] = utils.FileName(cfg.settings['collections_asset_dir'])
        afn['asset_path_noext'] = get_path_noext_SUFIX(AInfo, afn['asset_dir'], edict['m_name'], edict['id'])
        log.info('get_asset_info() Collection "{}"'.format(AInfo.name))
        log.info('get_asset_info() Collection ID {}'.format(edict['id']))

    elif object_ID == const.OBJECT_LAUNCHER_ID:
        afn['name'] = 'Launcher'
        afn['asset_dir'] = utils.FileName(cfg.settings['launchers_asset_dir'])
        afn['asset_path_noext'] = get_path_noext_SUFIX(AInfo, afn['asset_dir'], edict['m_name'], edict['id'])
        log.info('get_asset_info() Launcher "{}"'.format(AInfo.name))
        log.info('get_asset_info() Launcher ID {}'.format(edict['id']))

    # [TODO] How to handle this for ROMs? Do we need categoryID/launcherID or can we create more object_IDs?
    elif object_ID == const.OBJECT_ROM_ID and categoryID == VCATEGORY_FAVOURITES_ID:
        log.info('get_asset_info() ROM is in Favourites')
        afn['name'] = 'ROM'
        ROM_FN = utils.FileName(edict['filename'])
        platform = object_dic['platform']
        asset_dir_FN = utils.FileName(cfg.settings['favourites_asset_dir'])
        asset_path_noext_FN = get_path_noext_SUFIX(AInfo, asset_dir_FN, ROM_FN.getBaseNoExt(), object_dic['id'])
        log.info('get_asset_info() ROM "{}"'.format(AInfo.name))
        log.info('get_asset_info() ROM ID {}'.format(object_dic['id']))
        log.debug('get_asset_info() platform "{}"'.format(platform))

    elif object_ID == const.OBJECT_ROM_ID and categoryID == VCATEGORY_COLLECTIONS_ID:
        log.info('get_asset_info() ROM is in Collection')
        afn['name'] = 'ROM'
        ROM_FN = utils.FileName(edict['filename'])
        platform = object_dic['platform']
        asset_dir_FN = utils.FileName(cfg.settings['collections_asset_dir'])
        new_asset_basename = get_collection_asset_basename(AInfo, ROM_FN.getBaseNoExt(), platform, '.png')
        new_asset_basename_FN = utils.FileName(new_asset_basename)
        asset_path_noext_FN = asset_dir_FN.pjoin(new_asset_basename_FN.getBaseNoExt())
        log.info('get_asset_info() ROM "{}"'.format(AInfo.name))
        log.info('get_asset_info() ROM ID {}'.format(object_dic['id']))
        log.debug('get_asset_info() platform "{}"'.format(platform))

    elif object_ID == const.OBJECT_ROM_ID:
        log.info('get_asset_info() ROM is in Launcher id {}'.format(launcherID))
        afn['name'] = 'ROM'
        ROM_FN = utils.FileName(edict['filename'])
        launcher = cfg.launchers[launcherID]
        platform = launcher['platform']
        asset_dir_FN = utils.FileName(launcher[AInfo.path_key])
        asset_path_noext_FN = get_path_noext_DIR(AInfo, asset_dir_FN, ROM_FN)
        log.info('get_asset_info() ROM "{}"'.format(AInfo.name))
        log.info('get_asset_info() ROM ID {}'.format(object_dic['id']))
        log.debug('get_asset_info() platform "{}"'.format(platform))

    else:
        log.error('get_asset_info() Unknown object_ID = {}'.format(object_ID))
        kodi.notify_warn("Unknown object_ID '{}'".format(object_ID))
        raise TypeError

    return afn

# Given an asset filename string get the asset filename.
# This function is used in "Edit Category/Launcher/ROM" context menus, ...
def get_listitem_asset_filename(asset_filename_str):
    if asset_filename_str:
        item_path = utils.FileName(asset_filename_str)
        if item_path.isVideoFile():
            item_img = 'DefaultAddonVideo.png'
        elif item_path.isManual():
            item_img = 'DefaultAddonInfoProvider.png'
        else:
            item_img = asset_filename_str
    else:
        item_img = 'DefaultAddonNone.png'
    return item_img
