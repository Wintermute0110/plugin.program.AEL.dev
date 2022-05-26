# -*- coding: utf-8 -*-

# Copyright (c) 2016-2022 Wintermute0110 <wintermute0110@gmail.com>
# Portions (c) 2010-2015 Angelscry and others
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# Advanced Emulator Launcher filesystem I/O functions.

# --- Addon modules ---
import resources.const as const
import resources.misc as misc
import resources.log as log
import resources.utils as utils
import resources.kodi as kodi
import resources.assets as assets
import resources.audit as audit
import resources.platforms as platforms

# --- Python standard library ---
import collections
import copy
import os
import string
import sys
import time

# -------------------------------------------------------------------------------------------------
# Data model used in the plugin
# Internally all string in the data model are Unicode. They will be encoded to
# UTF-8 when writing files.
# -------------------------------------------------------------------------------------------------
# These three functions create a new data structure for the given object and (very importantly)
# fill the correct default values). These must match what is written/read from/to the XML files.
# Tag name in the XML is the same as in the data dictionary.
def new_category():
    return {
        'id' : '',
        'm_name' : '',
        'm_year' : '',
        'm_genre' : '',
        'm_developer' : '',
        'm_rating' : '',
        'm_plot' : '',
        'finished' : False,
        'default_icon' : 's_icon',
        'default_fanart' : 's_fanart',
        'default_banner' : 's_banner',
        'default_poster' : 's_poster',
        'default_clearlogo' : 's_clearlogo',
        'Asset_Prefix' : '',
        's_icon' : '',
        's_fanart' : '',
        's_banner' : '',
        's_poster' : '',
        's_clearlogo' : '',
        's_trailer' : ''
    }

def new_launcher():
    return {
        'id' : '',
        'm_name' : '',
        'm_year' : '',
        'm_genre' : '',
        'm_developer' : '',
        'm_rating' : '',
        'm_plot' : '',
        'platform' : '',
        'categoryID' : '',
        'application' : '',
        'args' : '',
        'args_extra' : [],
        'rompath' : '',
        'romext' : '',
        'romextrapath' : '',
        'finished': False,
        'toggle_window' : False, # Former 'minimize'
        'non_blocking' : False,
        'multidisc' : True,
        'roms_base_noext' : '',
        'audit_state' : const.AUDIT_STATE_OFF,
        'audit_auto_dat_file' : '',
        'audit_custom_dat_file' : '',
        'audit_display_mode' : const.AUDIT_DMODE_ALL,
        'launcher_display_mode' : const.LAUNCHER_DMODE_FLAT,
        'num_roms' : 0,
        'num_parents' : 0,
        'num_clones' : 0,
        'num_have' : 0,
        'num_miss' : 0,
        'num_unknown' : 0,
        'num_extra' : 0,
        'timestamp_launcher' : 0.0,
        'timestamp_report' : 0.0,
        'default_icon' : 's_icon',
        'default_fanart' : 's_fanart',
        'default_banner' : 's_banner',
        'default_poster' : 's_poster',
        'default_clearlogo' : 's_clearlogo',
        'default_controller' : 's_controller',
        'Asset_Prefix' : '',
        's_icon' : '',
        's_fanart' : '',
        's_banner' : '',
        's_poster' : '',
        's_clearlogo' : '',
        's_controller' : '',
        's_trailer' : '',
        'roms_default_icon' : 's_boxfront',
        'roms_default_fanart' : 's_fanart',
        'roms_default_banner' : 's_banner',
        'roms_default_poster' : 's_flyer',
        'roms_default_clearlogo' : 's_clearlogo',
        'ROM_asset_path' : '',
        'path_3dbox' : '',
        'path_title' : '',
        'path_snap' : '',
        'path_boxfront' : '',
        'path_boxback' : '',
        'path_cartridge' : '',
        'path_fanart' : '',
        'path_banner' : '',
        'path_clearlogo' : '',
        'path_flyer' : '',
        'path_map' : '',
        'path_manual' : '',
        'path_trailer' : ''
    }

def new_rom():
    return {
        'id' : '',
        'm_name' : '',
        'm_year' : '',
        'm_genre' : '',
        'm_developer' : '',
        'm_nplayers' : '',
        'm_esrb' : const.ESRB_PENDING,
        'm_rating' : '',
        'm_plot' : '',
        'filename' : '',
        'disks' : [],
        'altapp' : '',
        'altarg' : '',
        'finished' : False,
        'nointro_status' : const.AUDIT_STATUS_NONE,
        'pclone_status' : const.PCLONE_STATUS_NONE,
        'cloneof' : '',
        'i_extra_ROM' : False,
        's_3dbox' : '',
        's_title' : '',
        's_snap' : '',
        's_boxfront' : '',
        's_boxback' : '',
        's_cartridge' : '',
        's_fanart' : '',
        's_banner' : '',
        's_clearlogo' : '',
        's_flyer' : '',
        's_map' : '',
        's_manual' : '',
        's_trailer' : ''
    }

def new_collection():
    return {
        'id' : '',
        'm_name' : '',
        'm_genre' : '',
        'm_rating' : '',
        'm_plot' : '',
        'roms_base_noext' : '',
        'default_icon' : 's_icon',
        'default_fanart' : 's_fanart',
        'default_banner' : 's_banner',
        'default_poster' : 's_poster',
        'default_clearlogo' : 's_clearlogo',
        's_icon' : '',
        's_fanart' : '',
        's_banner' : '',
        's_poster' : '',
        's_clearlogo' : '',
        's_trailer' : ''
    }

# * These functions have the data model to render object in Kodi.
# * There are 4 kinds of objects that AEL can render: simple, categories, launchers and ROMs.
#   This includes real categories/launchers/ROMs or virtual ones.
# * These functions are here for reference. For performance reasons may not be used, specially
#   when rendering ROMs. In other words, the data structures are created on the fly but follow
#   this data model.
#
# --- Example of use ---
# obj = db_new_render_category()
# li = xbmcgui.ListItem(obj['name'])
# li.setInfo('video', obj['info'])
# li.setArt(obj['art'])
# li.setProperties(obj['props'])
# li.addContextMenuItems(obj['context'])
# xbmcplugin.addDirectoryItem(addon_handle, obj['URL'], li, True)
def new_render_simple_category():
    return {
        'name' : '',
        'display_setting_hide' : False,
        'info' : {
            'title' : '',
            'plot' : '',
            'overlay': kodi.KODI_ICON_OVERLAY_UNWATCHED,
        },
        'art' : {
            'icon' : '',
            'fanart' : '',
            'poster' : '',
        },
        'props' : {},
        'context' : [],
        'URL' : '',
    }

def new_render_category(): pass

def new_render_launcher(): pass

def new_render_ROM(): pass

# -------------------------------------------------------------------------------------------------
# Favourite ROM creation/management
# -------------------------------------------------------------------------------------------------
#
# Creates a new Favourite ROM dictionary from parent ROM and Launcher.
#
# No-Intro Missing ROMs are not allowed in Favourites or Virtual Launchers.
# fav_status = ['OK', 'Unlinked ROM', 'Unlinked Launcher', 'Broken'] default 'OK'
#  'OK'                ROM filename exists and launcher exists and ROM id exists
#  'Unlinked ROM'      ROM filename exists but ROM ID in launcher does not
#  'Unlinked Launcher' ROM filename exists but Launcher ID not found
#                      Note that if the launcher does not exists implies ROM ID does not exist.
#                      If launcher doesn't exist ROM JSON cannot be loaded.
#  'Broken'            ROM filename does not exist. ROM is unplayable
#
def get_Favourite_from_ROM(rom, launcher):
    # Copy dictionary object
    favourite = dict(rom)

    # Delete nointro_status field from ROM. Make sure this is done in the copy to be
    # returned to avoid chaning the function parameters (dictionaries are mutable!)
    # See http://stackoverflow.com/questions/5844672/delete-an-element-from-a-dictionary
    # NOTE keep it!
    # del favourite['nointro_status']

    # Copy parent launcher fields into Favourite ROM
    favourite['launcherID']             = launcher['id']
    favourite['platform']               = launcher['platform']
    favourite['application']            = launcher['application']
    favourite['args']                   = launcher['args']
    favourite['args_extra']             = launcher['args_extra']
    favourite['rompath']                = launcher['rompath']
    favourite['romext']                 = launcher['romext']
    favourite['toggle_window']          = launcher['toggle_window']
    favourite['non_blocking']           = launcher['non_blocking']
    favourite['roms_default_icon']      = launcher['roms_default_icon']
    favourite['roms_default_fanart']    = launcher['roms_default_fanart']
    favourite['roms_default_banner']    = launcher['roms_default_banner']
    favourite['roms_default_poster']    = launcher['roms_default_poster']
    favourite['roms_default_clearlogo'] = launcher['roms_default_clearlogo']

    # Favourite ROM unique fields
    # Favourite ROMs in "Most played ROMs" DB also have 'launch_count' field.
    favourite['fav_status'] = 'OK'
    return favourite

# Creates a new Favourite ROM from old Favourite, parent ROM and parent Launcher. This function is
# used when repairing/relinking a Favourite/Collection ROM.
#
# Repair mode (integer):
#   0) Relink and update launcher info
#   1) Relink and update metadata
#   2) Relink and update artwork
#   3) Relink and update everything
def repair_Favourite_ROM(repair_mode, old_fav_rom, parent_rom, parent_launcher):
    new_fav_rom = dict(old_fav_rom)

    # --- Step 0 is always done in any Favourite/Collection repair ---
    log.info('repair_Favourite_ROM() Relinking ROM and launcher (common stuff)')
    log.info('repair_Favourite_ROM() Old ROM name "{}"'.format(old_fav_rom['m_name']))
    log.info('repair_Favourite_ROM() New ROM name "{}"'.format(parent_rom['m_name']))
    log.info('repair_Favourite_ROM() New launcher "{}"'.format(parent_launcher['m_name']))
    fs_aux_copy_ROM_main_stuff(parent_launcher, parent_rom, new_fav_rom)
    fs_aux_copy_ROM_launcher_info(parent_launcher, new_fav_rom)

    # --- Metadata ---
    if repair_mode == 1:
        log.debug('fs_repair_Favourite_ROM() Relinking Metadata')
        fs_aux_copy_ROM_metadata(parent_rom, new_fav_rom)
    # --- Artwork ---
    elif repair_mode == 2:
        log.debug('fs_repair_Favourite_ROM() Relinking Artwork')
        fs_aux_copy_ROM_artwork(parent_launcher, parent_rom, new_fav_rom)
    # --- Metadata and artwork ---
    elif repair_mode == 3:
        log.debug('fs_repair_Favourite_ROM() Relinking Metadata and Artwork')
        fs_aux_copy_ROM_metadata(parent_rom, new_fav_rom)
        fs_aux_copy_ROM_artwork(parent_launcher, parent_rom, new_fav_rom)
    return new_fav_rom

def aux_copy_ROM_main_stuff(source_launcher, source_rom, dest_rom):
    dest_rom['id']          = source_rom['id']
    dest_rom['launcherID']  = source_launcher['id']
    dest_rom['filename']    = source_rom['filename']
    dest_rom['fav_status']  = 'OK'

def aux_copy_ROM_launcher_info(source_launcher, dest_rom):
    dest_rom['platform']      = source_launcher['platform']
    dest_rom['application']   = source_launcher['application']
    dest_rom['args']          = source_launcher['args']
    dest_rom['args_extra']    = source_launcher['args_extra']
    dest_rom['rompath']       = source_launcher['rompath']
    dest_rom['romext']        = source_launcher['romext']
    dest_rom['toggle_window'] = source_launcher['toggle_window']
    dest_rom['non_blocking']  = source_launcher['non_blocking']

def aux_copy_ROM_metadata(source_rom, dest_rom):
    dest_rom['m_name']         = source_rom['m_name']
    dest_rom['m_year']         = source_rom['m_year']
    dest_rom['m_genre']        = source_rom['m_genre']
    dest_rom['m_developer']    = source_rom['m_developer']
    dest_rom['m_nplayers']     = source_rom['m_nplayers']
    dest_rom['m_esrb']         = source_rom['m_esrb']
    dest_rom['m_rating']       = source_rom['m_rating']
    dest_rom['m_plot']         = source_rom['m_plot']
    dest_rom['altapp']         = source_rom['altapp']
    dest_rom['altarg']         = source_rom['altarg']
    dest_rom['finished']       = source_rom['finished']
    dest_rom['nointro_status'] = source_rom['nointro_status']
    dest_rom['pclone_status']  = source_rom['pclone_status']
    dest_rom['cloneof']        = source_rom['cloneof']

def aux_copy_ROM_artwork(source_launcher, source_rom, dest_rom):
    # TODO Replace this with a for loop and use the contant definitions in constants.py
    dest_rom['s_3dbox']     = source_rom['s_3dbox']
    dest_rom['s_title']     = source_rom['s_title']
    dest_rom['s_snap']      = source_rom['s_snap']
    dest_rom['s_fanart']    = source_rom['s_fanart']
    dest_rom['s_banner']    = source_rom['s_banner']
    dest_rom['s_clearlogo'] = source_rom['s_clearlogo']
    dest_rom['s_boxfront']  = source_rom['s_boxfront']
    dest_rom['s_boxback']   = source_rom['s_boxback']
    dest_rom['s_cartridge'] = source_rom['s_cartridge']
    dest_rom['s_flyer']     = source_rom['s_flyer']
    dest_rom['s_map']       = source_rom['s_map']
    dest_rom['s_manual']    = source_rom['s_manual']
    dest_rom['s_trailer']   = source_rom['s_trailer']
    dest_rom['roms_default_icon']      = source_launcher['roms_default_icon']
    dest_rom['roms_default_fanart']    = source_launcher['roms_default_fanart']
    dest_rom['roms_default_banner']    = source_launcher['roms_default_banner']
    dest_rom['roms_default_poster']    = source_launcher['roms_default_poster']
    dest_rom['roms_default_clearlogo'] = source_launcher['roms_default_clearlogo']

# ------------------------------------------------------------------------------------------------
# ROM storage file names
# ------------------------------------------------------------------------------------------------
def get_ROMs_basename(category_name, launcher_name, launcherID):
    clean_cat_name = ''.join([i if i in string.printable else '_' for i in category_name]).replace(' ', '_')
    clean_launch_title = ''.join([i if i in string.printable else '_' for i in launcher_name]).replace(' ', '_')
    roms_base_noext = 'roms_' + clean_cat_name + '_' + clean_launch_title + '_' + launcherID[0:6]
    log.debug('get_ROMs_basename() roms_base_noext "{}"'.format(roms_base_noext))
    return roms_base_noext

def get_collection_ROMs_basename(collection_name, collectionID):
    clean_collection_name = ''.join([i if i in string.printable else '_' for i in collection_name]).replace(' ', '_')
    roms_base_noext = clean_collection_name + '_' + collectionID[0:6]
    log.debug('get_collection_ROMs_basename() roms_base_noext "{}"'.format(roms_base_noext))
    return roms_base_noext

# ------------------------------------------------------------------------------------------------
# ROM database high-level IO functions
# ------------------------------------------------------------------------------------------------
# Caches to store virtual launcher indices.
collections_index = {}
vlaunchers_index = {}
for vlauncher_ID in const.VCATEGORY_BROWSE_BY_ID_LIST: vlaunchers_index[vlauncher_ID] = {}

def clear_vlauncher_index_cache():
    global collections_index
    global vlaunchers_index

    collections_index = {}
    for vlauncher_ID in const.VCATEGORY_BROWSE_BY_ID_LIST: vlaunchers_index[vlauncher_ID] = {}

# * This function must be called first to update cfg object fields that will be 
#   used by other functions.
# * Include here all possible launcher information needed anywhere in the addon.
# * For virtual launchers this function preloads the catalog.
# * This function loads virtual launcher indice files and caches it.
# * To force a reload of the cache set the cache to an empty object.
def get_launcher_info(cfg, st, categoryID, launcherID):
    global collections_index
    global vlaunchers_index

    log.debug('get_launcher_info() categoryID "{}" / launcherID "{}"'.format(categoryID, launcherID))
    cfg.launcher_is_vlauncher = launcherID in const.VLAUNCHER_ID_LIST
    cfg.launcher_is_vcategory = categoryID in const.VCATEGORY_ID_LIST
    cfg.launcher_is_browse_by = categoryID in const.VCATEGORY_BROWSE_BY_ID_LIST
    cfg.launcher_is_standard = not cfg.launcher_is_vlauncher and not cfg.launcher_is_vcategory
    cfg.launcher_is_virtual = not cfg.launcher_is_standard

    if cfg.launcher_is_standard:
        launcher = cfg.launchers[launcherID]
        roms_base_noext = launcher['roms_base_noext']
        cfg.roms_FN = cfg.ROMS_DIR.pjoin(roms_base_noext + '.json')
        cfg.parents_FN = cfg.ROMS_DIR.pjoin(roms_base_noext + '_parents.json')
        cfg.index_FN = cfg.ROMS_DIR.pjoin(roms_base_noext + '_index_PClone.json')
        cfg.window_title = 'Launcher ROM data' # Used in command_view_menu()
        cfg.launcher_label = 'Launcher ROM' # Used in command_view_menu()

    elif cfg.launcher_is_vlauncher and launcherID == const.VLAUNCHER_FAVOURITES_ID:
        cfg.roms_FN = cfg.FAV_JSON_FILE_PATH
        cfg.window_title = 'Favourite ROM data'
        cfg.launcher_label = 'Favourite'

    elif cfg.launcher_is_vlauncher and launcherID == const.VLAUNCHER_RECENT_ID:
        cfg.roms_FN = cfg.RECENT_PLAYED_FILE_PATH
        cfg.window_title = 'Recently played ROM data'
        cfg.launcher_label = 'Recently played ROM'

    elif cfg.launcher_is_vlauncher and launcherID == const.VLAUNCHER_MOST_PLAYED_ID:
        cfg.roms_FN = cfg.MOST_PLAYED_FILE_PATH
        cfg.window_title = 'Most Played ROM data'
        cfg.launcher_label = 'Most Played ROM'

    elif cfg.launcher_is_vcategory and categoryID == const.VCATEGORY_ROM_COLLECTION_ID:
        # Load Collection index and cache it.
        if not collections_index:
            log.debug('ROM Collection cache miss. Loading ROM Collection index.')
            collections_index = load_Collection_index_XML(cfg.COLLECTIONS_FILE_PATH)
        else:
            log.debug('ROM Collection cache hit.')
        cfg.COL_index = collections_index

        # Collection database filename and Metadata.
        collection = cfg.COL_index['collections'][launcherID]
        cfg.roms_FN = cfg.COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
        cfg.window_title = 'Collection ROM data'
        cfg.launcher_label = 'Collection'

    elif cfg.launcher_is_vcategory and categoryID == const.VCATEGORY_BROWSE_BY_TITLE_ID:
        # Load Virtual Launcher index file and cache it.
        cfg.vcategory_index_FN = cfg.VCAT_TITLE_FILE_PATH
        # if not cfg.vcategory_index_FN.exists():
        #     kodi.dialog_OK('Database not found. Update the virtual category database first.')
        if not vlaunchers_index[const.VCATEGORY_BROWSE_BY_TITLE_ID]:
            log.debug('get_launcher_info() VLauncher Title cache miss. Loading VLauncher index.')
            vlaunchers_index[const.VCATEGORY_BROWSE_BY_TITLE_ID] = load_VCategory_XML(cfg.vcategory_index_FN)
        else:
            log.debug('get_launcher_info() VLauncher Title cache hit.')
        cfg.VL_index = vlaunchers_index[const.VCATEGORY_BROWSE_BY_TITLE_ID]
        cfg.outdated_vlauncher_flag = True if cfg.VL_index['timestamp'] < cfg.update_timestamp else False

        # Virtual launcher metadata.
        cfg.window_title = 'Virtual Launcher Title ROM data'
        cfg.launcher_label = 'Virtual Launcher Title'
        cfg.vcategory_field_name = 'm_name'
        cfg.vcategory_name = 'Titles'

    elif cfg.launcher_is_vcategory and categoryID == const.VCATEGORY_BROWSE_BY_YEARS_ID:
        # Load Virtual Launcher index file and cache it.
        cfg.vcategory_index_FN = cfg.VCAT_YEARS_FILE_PATH        
        if not vlaunchers_index[const.VCATEGORY_BROWSE_BY_YEARS_ID]:
            log.debug('get_launcher_info() VLauncher Years cache miss. Loading VLauncher index.')
            vlaunchers_index[const.VCATEGORY_BROWSE_BY_YEARS_ID] = load_VCategory_XML(cfg.vcategory_index_FN)
        else:
            log.debug('get_launcher_info() VLauncher Years cache hit.')
        cfg.VL_index = vlaunchers_index[const.VCATEGORY_BROWSE_BY_YEARS_ID]
        cfg.outdated_vlauncher_flag = True if cfg.VL_index['timestamp'] < cfg.update_timestamp else False

        # Virtual launcher metadata.
        cfg.window_title = 'Virtual Launcher Year ROM data'
        cfg.launcher_label = 'Virtual Launcher Year'
        cfg.vcategory_field_name = 'm_year'
        cfg.vcategory_name = 'Years'

    elif cfg.launcher_is_vcategory and categoryID == const.VCATEGORY_BROWSE_BY_GENRE_ID:
        # Load Virtual Launcher index file and cache it.
        cfg.vcategory_index_FN = cfg.VCAT_GENRE_FILE_PATH
        if not vlaunchers_index[const.VCATEGORY_BROWSE_BY_GENRE_ID]:
            log.debug('get_launcher_info() VLauncher Genres cache miss. Loading VLauncher index.')
            vlaunchers_index[const.VCATEGORY_BROWSE_BY_GENRE_ID] = load_VCategory_XML(cfg.vcategory_index_FN)
        else:
            log.debug('get_launcher_info() VLauncher Genres cache hit.')
        cfg.VL_index = vlaunchers_index[const.VCATEGORY_BROWSE_BY_GENRE_ID]
        cfg.outdated_vlauncher_flag = True if cfg.VL_index['timestamp'] < cfg.update_timestamp else False

        # Virtual launcher metadata.
        cfg.window_title = 'Virtual Launcher Genre ROM data'
        cfg.launcher_label = 'Virtual Launcher Genre'
        cfg.vcategory_field_name = 'm_genre'
        cfg.vcategory_name = 'Genres'

    elif cfg.launcher_is_vcategory and categoryID == const.VCATEGORY_BROWSE_BY_DEVELOPER_ID:
        # Load Virtual Launcher index file and cache it.
        cfg.vcategory_index_FN = cfg.VCAT_DEVELOPER_FILE_PATH
        if not vlaunchers_index[const.VCATEGORY_BROWSE_BY_DEVELOPER_ID]:
            log.debug('get_launcher_info() VLauncher Developers cache miss. Loading VLauncher index.')
            vlaunchers_index[const.VCATEGORY_BROWSE_BY_DEVELOPER_ID] = load_VCategory_XML(cfg.vcategory_index_FN)
        else:
            log.debug('get_launcher_info() VLauncher Developers cache hit.')
        cfg.VL_index = vlaunchers_index[const.VCATEGORY_BROWSE_BY_DEVELOPER_ID]
        cfg.outdated_vlauncher_flag = True if cfg.VL_index['timestamp'] < cfg.update_timestamp else False

        # Virtual launcher metadata.
        cfg.window_title = 'Virtual Launcher Studio ROM data'
        cfg.launcher_label = 'Virtual Launcher Studio'
        cfg.vcategory_field_name = 'm_developer'
        cfg.vcategory_name = 'Developers'

    elif cfg.launcher_is_vcategory and categoryID == const.VCATEGORY_BROWSE_BY_NPLAYERS_ID:
        # Load Virtual Launcher index file and cache it.
        cfg.vcategory_index_FN = cfg.VCAT_NPLAYERS_FILE_PATH
        if not vlaunchers_index[const.VCATEGORY_BROWSE_BY_NPLAYERS_ID]:
            log.debug('get_launcher_info() VLauncher NPlayers cache miss. Loading VLauncher index.')
            vlaunchers_index[const.VCATEGORY_BROWSE_BY_NPLAYERS_ID] = load_VCategory_XML(cfg.vcategory_index_FN)
        else:
            log.debug('get_launcher_info() VLauncher NPlayers cache hit.')
        cfg.VL_index = vlaunchers_index[const.VCATEGORY_BROWSE_BY_NPLAYERS_ID]
        cfg.outdated_vlauncher_flag = True if cfg.VL_index['timestamp'] < cfg.update_timestamp else False

        # Virtual launcher metadata.
        cfg.window_title = 'Virtual Launcher NPlayer ROM data'
        cfg.launcher_label = 'Virtual Launcher NPlayer'
        cfg.vcategory_field_name = 'm_nplayers'
        cfg.vcategory_name = 'NPlayers'

    elif cfg.launcher_is_vcategory and categoryID == const.VCATEGORY_BROWSE_BY_ESRB_ID:
        # Load Virtual Launcher index file and cache it.
        cfg.vcategory_index_FN = cfg.VCAT_ESRB_FILE_PATH
        if not vlaunchers_index[const.VCATEGORY_BROWSE_BY_ESRB_ID]:
            log.debug('get_launcher_info() VLauncher ESRB cache miss. Loading VLauncher index.')
            vlaunchers_index[const.VCATEGORY_BROWSE_BY_ESRB_ID] = load_VCategory_XML(cfg.vcategory_index_FN)
        else:
            log.debug('get_launcher_info() VLauncher ESRB cache hit.')
        cfg.VL_index = vlaunchers_index[const.VCATEGORY_BROWSE_BY_ESRB_ID]
        cfg.outdated_vlauncher_flag = True if cfg.VL_index['timestamp'] < cfg.update_timestamp else False

        # Virtual launcher metadata.
        cfg.window_title = 'Virtual Launcher ESRB ROM data'
        cfg.launcher_label = 'Virtual Launcher ESRB'
        cfg.vcategory_field_name = 'm_esrb'
        cfg.vcategory_name = 'ESRB'

    elif cfg.launcher_is_vcategory and categoryID == const.VCATEGORY_BROWSE_BY_RATING_ID:
        # Load Virtual Launcher index file and cache it.
        cfg.vcategory_index_FN = cfg.VCAT_RATING_FILE_PATH
        if not vlaunchers_index[const.VCATEGORY_BROWSE_BY_RATING_ID]:
            log.debug('get_launcher_info() VLauncher Rating cache miss. Loading VLauncher index.')
            vlaunchers_index[const.VCATEGORY_BROWSE_BY_RATING_ID] = load_VCategory_XML(cfg.vcategory_index_FN)
        else:
            log.debug('get_launcher_info() VLauncher Rating cache hit.')
        cfg.VL_index = vlaunchers_index[const.VCATEGORY_BROWSE_BY_RATING_ID]
        cfg.outdated_vlauncher_flag = True if cfg.VL_index['timestamp'] < cfg.update_timestamp else False

        # Virtual launcher metadata.
        cfg.window_title = 'Virtual Launcher Rating ROM data'
        cfg.launcher_label = 'Virtual Launcher Rating'
        cfg.vcategory_field_name = 'm_rating'
        cfg.vcategory_name = 'Rating'

    elif cfg.launcher_is_vcategory and categoryID == const.VCATEGORY_BROWSE_BY_CATEGORY_ID:
        # Load Virtual Launcher index file and cache it.
        cfg.vcategory_index_FN = cfg.VCAT_CATEGORY_FILE_PATH
        if not vlaunchers_index[const.VCATEGORY_BROWSE_BY_CATEGORY_ID]:
            log.debug('get_launcher_info() VLauncher Categories cache miss. Loading VLauncher index.')
            vlaunchers_index[const.VCATEGORY_BROWSE_BY_CATEGORY_ID] = load_VCategory_XML(cfg.vcategory_index_FN)
        else:
            log.debug('get_launcher_info() VLauncher Categories cache hit.')
        cfg.VL_index = vlaunchers_index[const.VCATEGORY_BROWSE_BY_CATEGORY_ID]
        cfg.outdated_vlauncher_flag = True if cfg.VL_index['timestamp'] < cfg.update_timestamp else False

        # Virtual launcher metadata.
        cfg.window_title = 'Virtual Launcher Category ROM data'
        cfg.launcher_label = 'Virtual Launcher Category'
        cfg.vcategory_field_name = ''
        cfg.vcategory_name = 'Categories'

    elif cfg.launcher_is_vcategory and categoryID == const.VCATEGORY_AOS_ID:
        platform = launcherID
        log.debug('db_load_ROMs() platform "{}"'.format(platform))
        pobj = platforms.AEL_platforms[platforms.get_AEL_platform_index(platform)]
        if pobj.aliasof:
            log.debug('db_load_ROMs() aliasof "{}"'.format(pobj.aliasof))
            pobj_parent = AEL_platforms[get_AEL_platform_index(pobj.aliasof)]
            db_platform = pobj_parent.long_name
        else:
            db_platform = pobj.long_name
        xml_FN = cfg.GAMEDB_INFO_DIR.pjoin(db_platform + '.xml')
        log.debug('xml_FN OP {}'.format(xml_FN.getOriginalPath()))
        log.debug('xml_FN  P {}'.format(xml_FN.getPath()))
        cfg.roms_FN = xml_FN

    else:
        raise TypeError
    # log.debug('get_launcher_info() roms "{}"'.format(ret['roms'].getPath()))

# For actual ROM Launchers returns the database launcher dictionary.
# For virtual ROM Launchers returns create a launcher dictionary on-the-fly. NOTE: this is not
# possible! For example, every Favourite ROM has a different launching data!
# How to solve this issue? Is this function really useful?
#
# For now, this function is only valid for actual ROM launchers and will fail for virtual launchers.
def get_launcher(cfg, st_dic, launcherID):
    # Actual ROM Launcher
    if cfg.launcher_is_standard:
        if launcherID not in cfg.launchers:
            log.error('Launcher ID not found in cfg.launchers')
            kodi.dialog_OK('Launcher ID not found in cfg.launchers. Report this bug.')
            return
        launcher = cfg.launchers[launcherID]
        return launcher
    else:
        raise TypeError

# Gets launcher dictionary from ROM dictionary.
# If ROM is a normal ROM gets launcher dictionary from cfg.launchers
# If ROM is a Favourite ROM then use launcherID field in rom dictionary.
def get_launcher_from_ROM(cfg, st_dic, rom): pass

# Load ROMs databases and places them in cfg.roms dictionary.
# * In most cases cfg.roms is a dictionary of dictionaries.
#   In some cases () cfg.roms is an OrderedDictionary.
# * If load_pclone_ROMs_flag is True then PClone ROMs are also loaded.
def load_ROMs(cfg, st_dic, categoryID, launcherID, load_pclone_ROMs_flag = False):
    log.debug('load_ROMs() categoryID "{}" | launcherID "{}"'.format(categoryID, launcherID))
    # Actual ROM Launcher ------------------------------------------------------------------------
    if cfg.launcher_is_standard:
        if not cfg.roms_FN.exists():
            kodi_set_st_notify(st_dic, 'Launcher JSON database not found. Add ROMs to launcher.')
            return
        cfg.roms = utils.load_JSON_file(cfg.roms_FN.getPath())
        if not cfg.roms:
            kodi_set_st_notify(st_dic, 'Launcher JSON database empty. Add ROMs to launcher.')
            return
        if not load_pclone_ROMs_flag: return

        # Load parent ROMs.
        if not cfg.parents_FN.exists():
            kodi_set_st_notify(st_dic, 'Parent ROMs JSON not found.')
            return
        cfg.roms_parent = utils.load_JSON_file(cfg.parents_FN.getPath())
        if not cfg.roms_parent:
            kodi_set_st_notify(st_dic, 'Parent ROMs JSON is empty.')
            return

        # Load parent/clone index.
        if not cfg.index_FN.exists():
            kodi_set_st_notify(st_dic, 'PClone index JSON not found.')
            return
        cfg.pclone_index = utils.load_JSON_file(cfg.index_FN.getPath())
        if not cfg.pclone_index:
            kodi_set_st_notify(st_dic, 'PClone index dict is empty.')
            return

    # Virtual launchers --------------------------------------------------------------------------
    elif cfg.launcher_is_vlauncher and launcherID == const.VLAUNCHER_FAVOURITES_ID:
        # Transform list of dictionaries into an OrderedDict
        raw_data = utils.load_JSON_file(cfg.roms_FN.getPath())
        cfg.roms = raw_data[1] if raw_data else {}
        if not cfg.roms:
            kodi_set_st_notify(st_dic, 'Favourites is empty. Add ROMs to Favourites first.')
            return
        # Extract roms from JSON data structure and ensure version is correct.
        cfg.control_str = raw_data[0]['control']
        cfg.version_int = raw_data[0]['version']

    elif cfg.launcher_is_vlauncher and launcherID == const.VLAUNCHER_RECENT_ID:
        # Collection ROMs are a list od dictionaries, not a dictionary as usual in other DBs.
        # Transform list of dictionaries into an OrderedDict to keep the order.
        raw_data = utils.load_JSON_file(cfg.roms_FN.getPath())
        cfg.roms = collections.OrderedDict()
        for r in raw_data[1]: cfg.roms[r['id']] = r
        if not cfg.roms:
            kodi_set_st_notify(st_dic, 'Recently played list is empty. Play some ROMs first!')
            return
        cfg.control_str = raw_data[0]['control']
        cfg.version_int = raw_data[0]['version']

    elif cfg.launcher_is_vlauncher and launcherID == const.VLAUNCHER_MOST_PLAYED_ID:
        raw_data = utils.load_JSON_file(cfg.roms_FN.getPath())
        cfg.roms = raw_data[1] if raw_data else {}
        if not cfg.roms:
            kodi_set_st_notify(st_dic, 'Most played ROMs list is empty. Play some ROMs first!.')
            return
        # Extract roms from JSON data structe and ensure version is correct.
        cfg.control_str = raw_data[0]['control']
        cfg.version_int = raw_data[0]['version']

    elif cfg.launcher_is_vcategory and categoryID == const.VCATEGORY_ROM_COLLECTION_ID:
        # Collection ROMs are a list, not a dictionary as usual in other DBs.
        # Convert the list to an OrderedDict() to keep the order.
        raw_data = utils.load_JSON_file(cfg.roms_FN.getPath())
        cfg.roms = collections.OrderedDict()
        for r in raw_data[1]: cfg.roms[r['id']] = r
        if not cfg.roms:
            kodi.set_st_notify(st_dic, 'Collection is empty. Add ROMs to this collection first.')
            return
        else:
            cfg.control_str = raw_data[0]['control']
            cfg.version_int = raw_data[0]['version']

    elif cfg.launcher_is_browse_by:
        vlauncher_FN = cfg.VIRTUAL_ROMS_DIR.pjoin('{}_{}.json'.format(cfg.vcategory_name, launcherID))
        if not vlauncher_FN.exists():
            kodi.dialog_OK('Virtual launcher JSON file not found.')
            return
        cfg.roms = utils.load_JSON_file(vlauncher_FN.getPath())
        if not cfg.roms:
            kodi.notify('Virtual category ROMs JSON empty.')
            return

    elif cfg.launcher_is_vcategory and categoryID == const.VCATEGORY_AOS_ID:
        if not cfg.roms_FN.exists():
            kodi_set_st_nwarn(st_dic, '{} database not available yet.'.format(db_platform))
            return
        # [TODO] Move function contents here.
        cfg.roms = audit.load_OfflineScraper_XML(cfg.roms_FN.getPath())

    else:
        raise RuntimeError

# This function never fails.
def load_ROMs_Favourite_set(cfg):
    # Transform the dictionary keys into a set. Sets are faster when checking if an element exists.
    raw_data = utils.load_JSON_file(cfg.FAV_JSON_FILE_PATH.getPath())
    roms_fav = raw_data[1] if raw_data else {}
    if not cfg.roms:
        cfg.roms_fav_set = set()
        return
    cfg.roms_fav_set = set(roms_fav.keys())

# [TODO] xxxxxx
def save_vlauncher_index(cfg, st, categoryID, launcherID):
    log.debug('save_vlauncher_index() categoryID "{}" | launcherID "{}"'.format(categoryID, launcherID))
    if cfg.launcher_is_standard:
        log.debug('save_vlauncher_index() Nothing to do')

    elif cfg.launcher_is_vcategory and categoryID == const.VCATEGORY_ROM_COLLECTION_ID:
        write_Collection_index_XML(cfg.COLLECTIONS_FILE_PATH, cfg.collections_index['collections'])

    else:
        raise RuntimeError

# Old code from main.command_edit_rom()
def save_ROMs(cfg, st, categoryID, launcherID):
    log.debug('save_ROMs() categoryID "{}" | launcherID "{}"'.format(categoryID, launcherID))
    # Actual ROM Launcher ------------------------------------------------------------------------
    if cfg.launcher_is_standard:
        # Save categories/launchers to update main timestamp.
        # Also update changed launcher timestamp.
        cfg.launchers[launcherID]['num_roms'] = len(roms)
        cfg.launchers[launcherID]['timestamp_launcher'] = _t = time.time()
        pDialog = KodiProgressDialog()
        pDialog.startProgress('Saving ROM JSON database...')
        # Move code of this function here?
        write_ROMs_JSON(cfg.ROMS_DIR, cfg.launchers[launcherID], roms)
        pDialog.updateProgress(90)
        write_catfile(cfg.CATEGORIES_FILE_PATH, cfg.categories, cfg.launchers)
        pDialog.endProgress()

        # If launcher is audited then synchronise the edit ROM in the list of parents.
        if launcher['audit_state'] == AUDIT_STATE_ON:
            log.debug('Updating ROM in Parents JSON')
            pDialog.startProgress('Loading Parents JSON...')
            json_FN = g_PATHS.ROMS_DIR.pjoin(launcher['roms_base_noext'] + '_parents.json')
            parent_roms = utils.load_JSON_file(json_FN.getPath())
            # Only edit if ROM is in parent list
            if romID in parent_roms:
                log.debug('romID in Parent JSON. Updating...')
                parent_roms[romID] = roms[romID]
            pDialog.updateProgress(10, 'Saving Parents JSON...')
            utils.write_JSON_file(g_PATHS.ROMS_DIR, parents_roms_base_noext, parent_roms)
            pDialog.endProgress()

    # Virtual launchers --------------------------------------------------------------------------
    elif cfg.launcher_is_vlauncher and launcherID == const.VLAUNCHER_FAVOURITES_ID:
        control_dic = {
            'control' : 'Advanced Emulator Launcher Favourite ROMs',
            'version' : const.AEL_STORAGE_FORMAT,
        }
        utils.write_JSON_file(cfg.FAV_JSON_FILE_PATH.getPath(), [control_dic, cfg.roms])

    elif cfg.launcher_is_vcategory and categoryID == const.VCATEGORY_ROM_COLLECTION_ID:
        # Convert back the OrderedDict into a list and save Collection
        collection_rom_list = [cfg.roms[key] for key in cfg.roms]
        json_file_path = cfg.COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
        # write_Collection_ROMs_JSON(json_file_path, collection_rom_list)
        control_dic = {
            'control' : 'Advanced Emulator Launcher Collection ROMs',
            'version' : AEL_STORAGE_FORMAT,
        }
        utils.write_JSON_file(json_file_path.getPath(), [control_dic, roms])

    else:
        raise RuntimeError

# ------------------------------------------------------------------------------------------------
# Categories/Launchers
# ------------------------------------------------------------------------------------------------
# Write to disk categories.xml
def write_catfile(categories_file, categories, launchers, update_timestamp = 0.0):
    log.debug('write_catfile() Writing {}'.format(categories_file.getOriginalPath()))

    # Original Angelscry method for generating the XML was to grow a string, like this
    # xml_content = 'test'
    # xml_content += 'more test'
    # However, this method is very slow because string has to be reallocated every time is grown.
    # It is much faster to create a list of string and them join them!
    # See https://waymoot.org/home/python_string/
    sl = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<advanced_emulator_launcher version="{}">'.format(const.AEL_STORAGE_FORMAT),
    ]

    # --- Control information ---
    # time.time() returns a float. Usually precision is much better than a second, but not always.
    # See https://docs.python.org/2/library/time.html#time.time
    # NOTE When updating reports timestamp of categories/launchers must not be modified.
    _t = time.time() if not update_timestamp else update_timestamp

    # Write a timestamp when file is created. This enables the Virtual Launchers to know if
    # it's time for an update.
    sl.append('<control>')
    sl.append(misc.XML('update_timestamp', const.text_type(_t)))
    sl.append('</control>')

    # --- Create Categories XML list ---
    for categoryID in sorted(categories, key = lambda x : categories[x]['m_name']):
        category = categories[categoryID]
        # Data which is not string must be converted to string
        # misc.XML() returns Unicode strings that will be encoded to UTF-8 later.
        sl.append('<category>')
        sl.append(misc.XML('id', categoryID))
        sl.append(misc.XML('m_name', category['m_name']))
        sl.append(misc.XML('m_year', category['m_year']))
        sl.append(misc.XML('m_genre', category['m_genre']))
        sl.append(misc.XML('m_developer', category['m_developer']))
        sl.append(misc.XML('m_rating', category['m_rating']))
        sl.append(misc.XML('m_plot', category['m_plot']))
        sl.append(misc.XML('finished', const.text_type(category['finished'])))
        sl.append(misc.XML('default_icon', category['default_icon']))
        sl.append(misc.XML('default_fanart', category['default_fanart']))
        sl.append(misc.XML('default_banner', category['default_banner']))
        sl.append(misc.XML('default_poster', category['default_poster']))
        sl.append(misc.XML('default_clearlogo', category['default_clearlogo']))
        sl.append(misc.XML('Asset_Prefix', category['Asset_Prefix']))
        sl.append(misc.XML('s_icon', category['s_icon']))
        sl.append(misc.XML('s_fanart', category['s_fanart']))
        sl.append(misc.XML('s_banner', category['s_banner']))
        sl.append(misc.XML('s_poster', category['s_poster']))
        sl.append(misc.XML('s_clearlogo', category['s_clearlogo']))
        sl.append(misc.XML('s_trailer', category['s_trailer']))
        sl.append('</category>')

    # --- Write launchers ---
    for launcherID in sorted(launchers, key = lambda x : launchers[x]['m_name']):
        # Data which is not string must be converted to string
        launcher = launchers[launcherID]
        sl.append('<launcher>')
        sl.append(misc.XML('id', launcherID))
        sl.append(misc.XML('m_name', launcher['m_name']))
        sl.append(misc.XML('m_year', launcher['m_year']))
        sl.append(misc.XML('m_genre', launcher['m_genre']))
        sl.append(misc.XML('m_developer', launcher['m_developer']))
        sl.append(misc.XML('m_rating', launcher['m_rating']))
        sl.append(misc.XML('m_plot', launcher['m_plot']))
        sl.append(misc.XML('platform', launcher['platform']))
        sl.append(misc.XML('categoryID', launcher['categoryID']))
        sl.append(misc.XML('application', launcher['application']))
        sl.append(misc.XML('args', launcher['args']))
        # To simulate a list with XML allow multiple XML tags.
        if 'args_extra' in launcher:
            for extra_arg in launcher['args_extra']: sl.append(misc.XML('args_extra', extra_arg))
        sl.append(misc.XML('rompath', launcher['rompath']))
        sl.append(misc.XML('romext', launcher['romext']))
        sl.append(misc.XML('romextrapath', launcher['romextrapath']))
        sl.append(misc.XML('finished', const.text_type(launcher['finished'])))
        sl.append(misc.XML('toggle_window', const.text_type(launcher['toggle_window'])))
        sl.append(misc.XML('non_blocking', const.text_type(launcher['non_blocking'])))
        sl.append(misc.XML('multidisc', const.text_type(launcher['multidisc'])))
        sl.append(misc.XML('roms_base_noext', launcher['roms_base_noext']))
        sl.append(misc.XML('audit_state', launcher['audit_state']))
        sl.append(misc.XML('audit_auto_dat_file', launcher['audit_auto_dat_file']))
        sl.append(misc.XML('audit_custom_dat_file', launcher['audit_custom_dat_file']))
        sl.append(misc.XML('audit_display_mode', launcher['audit_display_mode']))
        sl.append(misc.XML('launcher_display_mode', const.text_type(launcher['launcher_display_mode'])))
        sl.append(misc.XML('num_roms', const.text_type(launcher['num_roms'])))
        sl.append(misc.XML('num_parents', const.text_type(launcher['num_parents'])))
        sl.append(misc.XML('num_clones', const.text_type(launcher['num_clones'])))
        sl.append(misc.XML('num_have', const.text_type(launcher['num_have'])))
        sl.append(misc.XML('num_miss', const.text_type(launcher['num_miss'])))
        sl.append(misc.XML('num_unknown', const.text_type(launcher['num_unknown'])))
        sl.append(misc.XML('num_extra', const.text_type(launcher['num_extra'])))
        sl.append(misc.XML('timestamp_launcher', const.text_type(launcher['timestamp_launcher'])))
        sl.append(misc.XML('timestamp_report', const.text_type(launcher['timestamp_report'])))
        # Launcher artwork
        sl.append(misc.XML('default_icon', launcher['default_icon']))
        sl.append(misc.XML('default_fanart', launcher['default_fanart']))
        sl.append(misc.XML('default_banner', launcher['default_banner']))
        sl.append(misc.XML('default_poster', launcher['default_poster']))
        sl.append(misc.XML('default_clearlogo', launcher['default_clearlogo']))
        sl.append(misc.XML('default_controller', launcher['default_controller']))
        sl.append(misc.XML('Asset_Prefix', launcher['Asset_Prefix']))
        sl.append(misc.XML('s_icon', launcher['s_icon']))
        sl.append(misc.XML('s_fanart', launcher['s_fanart']))
        sl.append(misc.XML('s_banner', launcher['s_banner']))
        sl.append(misc.XML('s_poster', launcher['s_poster']))
        sl.append(misc.XML('s_clearlogo', launcher['s_clearlogo']))
        sl.append(misc.XML('s_controller', launcher['s_controller']))
        sl.append(misc.XML('s_trailer', launcher['s_trailer']))
        # ROMs artwork
        sl.append(misc.XML('roms_default_icon', launcher['roms_default_icon']))
        sl.append(misc.XML('roms_default_fanart', launcher['roms_default_fanart']))
        sl.append(misc.XML('roms_default_banner', launcher['roms_default_banner']))
        sl.append(misc.XML('roms_default_poster', launcher['roms_default_poster']))
        sl.append(misc.XML('roms_default_clearlogo', launcher['roms_default_clearlogo']))
        sl.append(misc.XML('ROM_asset_path', launcher['ROM_asset_path']))
        sl.append(misc.XML('path_3dbox', launcher['path_3dbox']))
        sl.append(misc.XML('path_title', launcher['path_title']))
        sl.append(misc.XML('path_snap', launcher['path_snap']))
        sl.append(misc.XML('path_boxfront', launcher['path_boxfront']))
        sl.append(misc.XML('path_boxback', launcher['path_boxback']))
        sl.append(misc.XML('path_cartridge', launcher['path_cartridge']))
        sl.append(misc.XML('path_fanart', launcher['path_fanart']))
        sl.append(misc.XML('path_banner', launcher['path_banner']))
        sl.append(misc.XML('path_clearlogo', launcher['path_clearlogo']))
        sl.append(misc.XML('path_flyer', launcher['path_flyer']))
        sl.append(misc.XML('path_map', launcher['path_map']))
        sl.append(misc.XML('path_manual', launcher['path_manual']))
        sl.append(misc.XML('path_trailer', launcher['path_trailer']))
        sl.append('</launcher>')
    sl.append('</advanced_emulator_launcher>')
    utils.write_slist_to_file(categories_file.getPath(), sl)

# Loads categories.xml from disk and fills dictionary self.categories.
# Returns the update_timestamp of the XML file.
# If IO error then returns None.
def load_catfile(categories_file, categories, launchers):
    __debug_xml_parser = 0

    xml_tree = utils.load_XML_to_ET(categories_file.getPath())
    if not xml_tree: return None
    xml_root = xml_tree.getroot()
    for category_element in xml_root:
        if __debug_xml_parser: log.debug('Root child {}'.format(category_element.tag))

        if category_element.tag == 'control':
            for control_child in category_element:
                if control_child.tag == 'update_timestamp':
                    update_timestamp = float(control_child.text)

        elif category_element.tag == 'category':
            # Default values
            category = new_category()

            # Parse child tags of category
            for category_child in category_element:
                # By default read strings
                text_XML = category_child.text if category_child.text is not None else ''
                text_XML = misc.unescape_XML(text_XML)
                xml_tag  = category_child.tag
                if __debug_xml_parser: log.debug('{} --> {}'.format(xml_tag, text_XML))

                # Now transform data depending on tag name
                if xml_tag == 'finished':
                    category[xml_tag] = True if text_XML == 'True' else False
                else:
                    # Internal data is always stored as Unicode. ElementTree already outputs Unicode.
                    category[xml_tag] = text_XML
            categories[category['id']] = category

        elif category_element.tag == 'launcher':
            # Default values
            launcher = new_launcher()

            # Parse child tags of category
            for category_child in category_element:
                # By default read strings
                text_XML = category_child.text if category_child.text is not None else ''
                text_XML = misc.unescape_XML(text_XML)
                xml_tag  = category_child.tag
                if __debug_xml_parser: log.debug('{} --> {}'.format(xml_tag, text_XML))

                if xml_tag == 'args_extra':
                    # Transform list() datatype
                    launcher[xml_tag].append(text_XML)
                elif xml_tag == 'finished' or xml_tag == 'toggle_window' or xml_tag == 'non_blocking' or \
                     xml_tag == 'multidisc':
                    # Transform Bool datatype
                    launcher[xml_tag] = True if text_XML == 'True' else False
                elif xml_tag == 'num_roms' or xml_tag == 'num_parents' or \
                     xml_tag == 'num_clones' or xml_tag == 'num_have' or \
                     xml_tag == 'num_miss' or xml_tag == 'num_unknown' or \
                     xml_tag == 'num_extra':
                    # Transform Int datatype
                    launcher[xml_tag] = int(text_XML)
                elif xml_tag == 'timestamp_launcher' or xml_tag == 'timestamp_report':
                    # Transform Float datatype
                    launcher[xml_tag] = float(text_XML)
                else:
                    launcher[xml_tag] = text_XML
            launchers[launcher['id']] = launcher
    # log.debug('fs_load_catfile() Loaded {} categories'.format(len(categories)))
    # log.debug('fs_load_catfile() Loaded {} launchers'.format(len(launchers)))
    return update_timestamp

# -------------------------------------------------------------------------------------------------
# Standard ROM databases
# -------------------------------------------------------------------------------------------------
# <roms_base_noext>.json
# <roms_base_noext>.xml
# <roms_base_noext>_index_CParent.json
# <roms_base_noext>_index_PClone.json
# <roms_base_noext>_parents.json
# <roms_base_noext>_DAT.json
def unlink_ROMs_database(roms_dir_FN, launcher):
    roms_base_noext = launcher['roms_base_noext']

    # Delete ROMs JSON file
    roms_json_FN = roms_dir_FN.pjoin(roms_base_noext + '.json')
    if roms_json_FN.exists():
        log.info('Deleting ROMs JSON    "{}"'.format(roms_json_FN.getOriginalPath()))
        roms_json_FN.unlink()

    # Delete ROMs info XML file
    roms_xml_FN = roms_dir_FN.pjoin(roms_base_noext + '.xml')
    if roms_xml_FN.exists():
        log.info('Deleting ROMs XML     "{}"'.format(roms_xml_FN.getOriginalPath()))
        roms_xml_FN.unlink()

    # Delete No-Intro/Redump stuff if exist
    roms_index_CParent_FN = roms_dir_FN.pjoin(roms_base_noext + '_index_CParent.json')
    if roms_index_CParent_FN.exists():
        log.info('Deleting CParent JSON "{}"'.format(roms_index_CParent_FN.getOriginalPath()))
        roms_index_CParent_FN.unlink()

    roms_index_PClone_FN = roms_dir_FN.pjoin(roms_base_noext + '_index_PClone.json')
    if roms_index_PClone_FN.exists():
        log.info('Deleting PClone JSON  "{}"'.format(roms_index_PClone_FN.getOriginalPath()))
        roms_index_PClone_FN.unlink()

    roms_parents_FN = roms_dir_FN.pjoin(roms_base_noext + '_parents.json')
    if roms_parents_FN.exists():
        log.info('Deleting parents JSON "{}"'.format(roms_parents_FN.getOriginalPath()))
        roms_parents_FN.unlink()

    roms_DAT_FN = roms_dir_FN.pjoin(roms_base_noext + '_DAT.json')
    if roms_DAT_FN.exists():
        log.info('Deleting DAT JSON     "{}"'.format(roms_DAT_FN.getOriginalPath()))
        roms_DAT_FN.unlink()

def rename_ROMs_database(roms_dir_FN, old_roms_base_noext, new_roms_base_noext):
    # Only rename if base names are different
    log.debug('rename_ROMs_database() old_roms_base_noext "{}"'.format(old_roms_base_noext))
    log.debug('rename_ROMs_database() new_roms_base_noext "{}"'.format(new_roms_base_noext))
    if old_roms_base_noext == new_roms_base_noext:
        log.debug('rename_ROMs_database() Exiting because old and new names are equal')
        return

    old_roms_json_FN          = roms_dir_FN.pjoin(old_roms_base_noext + '.json')
    old_roms_xml_FN           = roms_dir_FN.pjoin(old_roms_base_noext + '.xml')
    old_roms_index_CParent_FN = roms_dir_FN.pjoin(old_roms_base_noext + '_index_CParent.json')
    old_roms_index_PClone_FN  = roms_dir_FN.pjoin(old_roms_base_noext + '_index_PClone.json')
    old_roms_parents_FN       = roms_dir_FN.pjoin(old_roms_base_noext + '_parents.json')
    old_roms_DAT_FN           = roms_dir_FN.pjoin(old_roms_base_noext + '_DAT.json')

    new_roms_json_FN          = roms_dir_FN.pjoin(new_roms_base_noext + '.json')
    new_roms_xml_FN           = roms_dir_FN.pjoin(new_roms_base_noext + '.xml')
    new_roms_index_CParent_FN = roms_dir_FN.pjoin(new_roms_base_noext + '_index_CParent.json')
    new_roms_index_PClone_FN  = roms_dir_FN.pjoin(new_roms_base_noext + '_index_PClone.json')
    new_roms_parents_FN       = roms_dir_FN.pjoin(new_roms_base_noext + '_parents.json')
    new_roms_DAT_FN           = roms_dir_FN.pjoin(new_roms_base_noext + '_DAT.json')

    # Only rename files if originals found.
    if old_roms_json_FN.exists():
        old_roms_json_FN.rename(new_roms_json_FN)
        log.debug('RENAMED OP {}'.format(old_roms_json_FN.getOriginalPath()))
        log.debug('   into OP {}'.format(new_roms_json_FN.getOriginalPath()))

    if old_roms_xml_FN.exists():
        old_roms_xml_FN.rename(new_roms_xml_FN)
        log.debug('RENAMED OP {}'.format(old_roms_xml_FN.getOriginalPath()))
        log.debug('   into OP {}'.format(new_roms_xml_FN.getOriginalPath()))

    if old_roms_index_CParent_FN.exists():
        old_roms_index_CParent_FN.rename(new_roms_index_CParent_FN)
        log.debug('RENAMED OP {}'.format(old_roms_index_CParent_FN.getOriginalPath()))
        log.debug('   into OP {}'.format(new_roms_index_CParent_FN.getOriginalPath()))

    if old_roms_index_PClone_FN.exists():
        old_roms_index_PClone_FN.rename(new_roms_index_PClone_FN)
        log.debug('RENAMED OP {}'.format(old_roms_index_PClone_FN.getOriginalPath()))
        log.debug('   into OP {}'.format(new_roms_index_PClone_FN.getOriginalPath()))

    if old_roms_parents_FN.exists():
        old_roms_parents_FN.rename(new_roms_parents_FN)
        log.debug('RENAMED OP {}'.format(old_roms_parents_FN.getOriginalPath()))
        log.debug('   into OP {}'.format(new_roms_parents_FN.getOriginalPath()))

    if old_roms_DAT_FN.exists():
        old_roms_DAT_FN.rename(new_roms_DAT_FN)
        log.debug('RENAMED OP {}'.format(old_roms_DAT_FN.getOriginalPath()))
        log.debug('   into OP {}'.format(new_roms_DAT_FN.getOriginalPath()))

def write_ROMs_JSON(roms_dir_FN, launcher, roms):
    # Get file names
    roms_base_noext = launcher['roms_base_noext']
    roms_json_file = roms_dir_FN.pjoin(roms_base_noext + '.json')
    roms_xml_file  = roms_dir_FN.pjoin(roms_base_noext + '.xml')
    log.debug('write_ROMs_JSON()  Dir {}'.format(roms_dir_FN.getOriginalPath()))
    log.debug('write_ROMs_JSON() JSON {}'.format(roms_base_noext + '.json'))
    log.debug('write_ROMs_JSON()  XML {}'.format(roms_base_noext + '.xml'))

    # JSON files cannot have comments. Write an auxiliar NFO file with same prefix
    # to store launcher information for a set of ROMs
    #
    # Print some information in the XML so the user can now which launcher created it.
    # Note that this is ignored when reading the file.
    sl = []
    sl.append('<?xml version="1.0" encoding="utf-8"?>')
    sl.append('<advanced_emulator_launcher_ROMs version="{}">'.format(AEL_STORAGE_FORMAT))
    sl.append('<launcher>')
    sl.append(misc.XML('id', launcher['id']))
    sl.append(misc.XML('m_name', launcher['m_name']))
    sl.append(misc.XML('categoryID', launcher['categoryID']))
    sl.append(misc.XML('platform', launcher['platform']))
    sl.append(misc.XML('rompath', launcher['rompath']))
    sl.append(misc.XML('romext', launcher['romext']))
    sl.append('</launcher>')
    sl.append('</advanced_emulator_launcher_ROMs>')

    #  Write ROMs XML info file and JSON database file.
    utils.write_slist_to_file(roms_xml_file.getPath(), sl)
    utils.write_JSON_file(roms_json_file.getPath(), roms)

# ------------------------------------------------------------------------------------------------
# ROM Collections
# ------------------------------------------------------------------------------------------------
def write_Collection_index_XML(xml_FN, collections):
    log.info('write_Collection_index_XML() File {}'.format(xml_FN.getOriginalPath()))
    sl = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<advanced_emulator_launcher_Collection_index version="{}">'.format(const.AEL_STORAGE_FORMAT),
        '<control>',
        misc.XML('update_timestamp', const.text_type(time.time())),
        '</control>',
    ]
    for collection_id in sorted(collections, key = lambda x : collections[x]['m_name']):
        collection = collections[collection_id]
        sl.append('<Collection>')
        sl.append(misc.XML('id', collection['id']))
        sl.append(misc.XML('m_name', collection['m_name']))
        sl.append(misc.XML('m_genre', collection['m_genre']))
        sl.append(misc.XML('m_rating', collection['m_rating']))
        sl.append(misc.XML('m_plot', collection['m_plot']))
        sl.append(misc.XML('roms_base_noext', collection['roms_base_noext']))
        sl.append(misc.XML('default_icon', collection['default_icon']))
        sl.append(misc.XML('default_fanart', collection['default_fanart']))
        sl.append(misc.XML('default_banner', collection['default_banner']))
        sl.append(misc.XML('default_poster', collection['default_poster']))
        sl.append(misc.XML('default_clearlogo', collection['default_clearlogo']))
        sl.append(misc.XML('s_icon', collection['s_icon']))
        sl.append(misc.XML('s_fanart', collection['s_fanart']))
        sl.append(misc.XML('s_banner', collection['s_banner']))
        sl.append(misc.XML('s_poster', collection['s_poster']))
        sl.append(misc.XML('s_clearlogo', collection['s_clearlogo']))
        sl.append(misc.XML('s_trailer', collection['s_trailer']))
        sl.append('</Collection>')
    sl.append('</advanced_emulator_launcher_Collection_index>')
    utils.write_slist_to_file(xml_FN.getPath(), sl)

def load_Collection_index_XML(xml_FN):
    log.debug('load_Collection_index_XML() Loading XML file {}'.format(xml_FN.getOriginalPath()))
    __debug_xml_parser = False
    ret = {'timestamp' : 0.0, 'collections' : {}}
    xml_tree = utils.load_XML_to_ET(xml_FN.getPath())
    if not xml_tree: return ret
    xml_root = xml_tree.getroot()
    for root_element in xml_root:
        if __debug_xml_parser: log.debug('Root child {}'.format(root_element.tag))
        if root_element.tag == 'control':
            for control_child in root_element:
                if control_child.tag == 'update_timestamp':
                    ret['timestamp'] = float(control_child.text)
        elif root_element.tag == 'Collection':
            collection = new_collection()
            for rom_child in root_element:
                # By default read Unicode strings.
                text_XML = rom_child.text if rom_child.text is not None else ''
                text_XML = misc.unescape_XML(text_XML)
                xml_tag  = rom_child.tag
                if __debug_xml_parser: log.debug('{} --> {}'.format(xml_tag, text_XML))
                collection[xml_tag] = text_XML
            ret['collections'][collection['id']] = collection
    return ret

# Exports a collection in human-readable JSON.
# Filenames of artwork/assets must be converted to relative paths, see
# comments in fs_export_ROM_collection_assets()
def export_ROM_collection(output_filename, collection, rom_list):
    log.info('export_ROM_collection() File {}'.format(output_filename.getOriginalPath()))

    ex_collection_dic = copy.deepcopy(collection)
    for asset_kind in COLLECTION_ASSET_ID_LIST:
        AInfo = assets_get_info_scheme(asset_kind)
        if not ex_collection_dic[AInfo.key]: continue
        # Change filename of asset.
        asset_FN = FileName(ex_collection_dic[AInfo.key])
        new_asset_path = collection['m_name'] + '_' + AInfo.fname_infix + asset_FN.getExt()
        ex_collection_dic[AInfo.key] = new_asset_path

    ex_rom_list = copy.deepcopy(rom_list)
    for rom in ex_rom_list:
        for asset_kind in ROM_ASSET_ID_LIST:
            AInfo = assets_get_info_scheme(asset_kind)
            if not rom[AInfo.key]: continue
            # Change filename of asset.
            asset_FN = FileName(rom[AInfo.key])
            ROM_FileName = FileName(rom['filename'])
            new_asset_basename = assets_get_collection_asset_basename(
                AInfo, ROM_FileName.getBaseNoExt(), rom['platform'], asset_FN.getExt())
            rom[AInfo.key] = collection['m_name'] + ' assets' + '/' + new_asset_basename

    # Produce nicely formatted JSON when exporting
    control_dic = {
        'control' : 'Advanced Emulator Launcher Collection ROMs',
        'version' : AEL_STORAGE_FORMAT
    }
    raw_data = [control_dic, ex_collection_dic, ex_rom_list]
    utils_write_JSON_file(output_filename.getPath(), raw_data, pprint = True)

# Export collection assets.
#
# In the JSON metadata file always use relative paths for assets, for example:
#
# {
#    "s_fanart" : "Chrono Trigger_fanart.jpg",  -- Collection artwork
#    "s_icon" : "Chrono Trigger_icon.png",
# },
# [
#   {
#     "s_fanart" : "Chrono Trigger/Chrono Trigger_snes_fanart.jpg", -- Collection ROM artwork
#     "s_icon" : "Chrono Trigger/Chrono Trigger_snes_icon.png",
#   },
# ]
#
# The user may place additional artwork that will be scanned when importing the collection.
#
# /output/dir/Collection Name_icon.png   -- Reserved for exporting.
# /output/dir/Collection Name_icon1.png  -- Additional scanner artwork when importing.
# /output/dir/Collection Name_icon2.png  -- Only one piece of artwork imported, user chooses.
#
# The exported layout looks like this:
#
# /output/dir/Collection Name.json                              -- Collection metadata
# /output/dir/Collection Name_icon.png                          -- Collection assets.
# /output/dir/Collection Name_fanart.png
# /output/dir/Collection Name/ROM Name_platform_cname_icon.png  -- Collection ROM assets
# /output/dir/Collection Name/ROM Name_platform_cname_icon.png
#
# Parameters:
#   out_dir_FN    FileName object
#   collection    dictionary
#   rom_list      list of dictionaries
#   asset_dir_FN  FileName object default self.settings['collections_asset_dir']
def export_ROM_collection_assets(out_dir_FN, collection, rom_list, asset_dir_FN):
    log.info('export_ROM_collection_assets() Dir {}'.format(out_dir_FN.getOriginalPath()))

    # --- Export Collection own assets ---
    assets_dic = {}
    log.debug('export_ROM_collection_assets() Exporting Collecion assets')
    for asset_kind in COLLECTION_ASSET_ID_LIST:
        AInfo = assets_get_info_scheme(asset_kind)
        asset_FN = FileName(collection[AInfo.key])
        if not collection[AInfo.key]:
            log.debug('{:<9s} not set'.format(AInfo.name))
            continue
        elif not asset_FN.exists():
            log.debug('{:<9s} not found "{}"'.format(AInfo.name, asset_FN.getPath()))
            log.debug('{:<9s} ignoring'.format(AInfo.name))
            continue
        # Copy asset file to output dir with new filename.
        asset_ext = asset_FN.getExt()
        new_asset_FN = out_dir_FN.pjoin(collection['m_name'] + '_' + AInfo.fname_infix + asset_ext)
        # log.debug('{:<9s} OP COPY "{}"'.format(AInfo.name, asset_FN.getOriginalPath()))
        # log.debug('{:<9s} OP   TO "{}"'.format(AInfo.name, new_asset_FN.getOriginalPath()))
        log.debug('{:<9s} P  COPY "{}"'.format(AInfo.name, asset_FN.getPath()))
        log.debug('{:<9s} P    TO "{}"'.format(AInfo.name, new_asset_FN.getPath()))
        try:
            source_path = asset_FN.getPath().decode(get_fs_encoding(), 'ignore')
            dest_path = new_asset_FN.getPath().decode(get_fs_encoding(), 'ignore')
            shutil.copy(source_path, dest_path)
        except OSError:
            log.error('export_ROM_collection_assets() OSError exception copying image')
            kodi.notify_warn('OSError exception copying image')
            return
        except IOError:
            log.error('export_ROM_collection_assets() IOError exception copying image')
            kodi.notify_warn('IOError exception copying image')
            return

    # --- Export Collection ROM assets ---
    # Create output dir if it does not exits.
    ROM_out_dir_FN = out_dir_FN.pjoin(collection['m_name'] + ' assets')
    if not ROM_out_dir_FN.exists():
        log.debug('Creating dir "{}"'.format(ROM_out_dir_FN.getPath()))
        ROM_out_dir_FN.makedirs()

    # Traverse ROMs and export (copy) assets.
    log.debug('export_ROM_collection_assets() Exporting ROM assets')
    # log.debug('Directory {}'.format(ROM_out_dir_FN.getDir()))
    for rom in rom_list:
        log.debug('export_ROM_collection_assets() ROM "{}"'.format(rom['m_name']))
        for asset_kind in ROM_ASSET_ID_LIST:
            AInfo = assets_get_info_scheme(asset_kind)
            asset_FN = FileName(rom[AInfo.key])
            if not rom[AInfo.key]:
                log.debug('{:<9s} not set'.format(AInfo.name))
                continue
            elif not asset_FN.exists():
                log.debug('{:<9s} not found "{}"'.format(AInfo.name, asset_FN.getPath()))
                log.debug('{:<9s} ignoring'.format(AInfo.name))
                continue
            # Copy asset file to output dir with new filename.
            ROM_FileName = FileName(rom['filename'])
            new_asset_basename = assets_get_collection_asset_basename(
                AInfo, ROM_FileName.getBaseNoExt(), rom['platform'], asset_FN.getExt())
            new_asset_FN = ROM_out_dir_FN.pjoin(new_asset_basename)
            # log.debug('{:<9s} OP COPY "{}"'.format(AInfo.name, asset_FN.getOriginalPath()))
            # log.debug('{:<9s} OP   TO "{}"'.format(AInfo.name, new_asset_FN.getOriginalPath()))
            log.debug('{:<9s} COPY "{}"'.format(AInfo.name, asset_FN.getPath()))
            log.debug('{:<9s}   TO "{}"'.format(AInfo.name, new_asset_FN.getPath()))
            try:
                utils_copy_file(asset_FN.getPath(), new_asset_FN.getPath())
            except OSError:
                log.error('export_ROM_collection_assets() OSError exception copying image')
                kodi.notify_warn('OSError exception copying image')
                return
            except IOError:
                log.error('export_ROM_collection_assets() IOError exception copying image')
                kodi.notify_warn('IOError exception copying image')
                return

# See fs_export_ROM_collection() function.
# Returns a tuple (control_dic, collection_dic, rom_list)
def import_ROM_collection(input_FileName):
    default_return = ({}, {}, [])

    log.info('import_ROM_collection() Loading {}'.format(input_FileName.getOriginalPath()))
    raw_data = utils.load_JSON_file(input_FileName.getPath())
    if not raw_data: return default_return
    try:
        control_dic    = raw_data[0]
        collection_dic = raw_data[1]
        rom_list       = raw_data[2]
        control_str    = control_dic['control']
        version_int    = control_dic['version']
    except:
        log.error('import_ROM_collection() Exception unpacking ROM Collection data')
        log.error('import_ROM_collection() Empty ROM Collection returned')
        return default_return

    return (control_dic, collection_dic, rom_list)

# Returns a tuple (control_dic, assets_dic)
def import_ROM_collection_assets(input_FileName):
    default_return = ({}, {})

    log.info('import_ROM_collection_assets() Loading {}'.format(input_FileName.getOriginalPath()))
    raw_data = utils.load_JSON_file(input_FileName.getPath())
    if not raw_data: return default_return
    control_dic = raw_data[0]
    assets_dic  = raw_data[1]
    control_str = control_dic['control']
    version_int = control_dic['version']
    return (control_dic, assets_dic)

# Slow implementation that uses a linear search.
# Returns:
# -1    ROM not found in list
# >= 0  ROM index in list
def collection_ROM_index_by_romID(romID, collection_rom_list):
    current_ROM_position = -1
    for idx, rom in enumerate(collection_rom_list):
        if romID == rom['id']:
            current_ROM_position = idx
            break
    return current_ROM_position

# -------------------------------------------------------------------------------------------------
# Virtual Categories
# -------------------------------------------------------------------------------------------------
def write_VCategory_XML(roms_xml_file, roms):
    log.info('write_VCategory_XML() Saving XML {}'.format(roms_xml_file.getOriginalPath()))
    sl = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<advanced_emulator_launcher_Virtual_Category_index version="{}">'.format(const.AEL_STORAGE_FORMAT),
        '<control>',
        misc.XML('update_timestamp', const.text_type(time.time())),
        '</control>',
    ]
    for romID in sorted(roms, key = lambda x : roms[x]['name']):
        rom = roms[romID]
        sl.append('<VLauncher>')
        sl.append(misc.XML('id', romID))
        sl.append(misc.XML('name', rom['name']))
        sl.append(misc.XML('rom_count', rom['rom_count']))
        sl.append(misc.XML('roms_base_noext', rom['roms_base_noext']))
        sl.append('</VLauncher>')
    sl.append('</advanced_emulator_launcher_Virtual_Category_index>')
    utils.write_slist_to_file(roms_xml_file.getPath(), sl)

# Loads an XML file containing Virtual Launcher indices
# It is basically the same as ROMs, but with some more fields to store launching application data.
def load_VCategory_XML(roms_xml_file):
    __debug_xml_parser = 0
    ret = {'timestamp' : 0.0, 'vlaunchers' : {}}
    log.debug('load_VCategory_XML() Loading XML file {}'.format(roms_xml_file.getOriginalPath()))
    xml_tree = utils.load_XML_to_ET(roms_xml_file.getPath())
    if not xml_tree: return ret
    xml_root = xml_tree.getroot()
    for root_element in xml_root:
        if __debug_xml_parser: log.debug('Root child {}'.format(root_element.tag))
        if root_element.tag == 'control':
            for control_child in root_element:
                if control_child.tag == 'update_timestamp':
                    ret['timestamp'] = float(control_child.text)
        elif root_element.tag == 'VLauncher':
            # Default values
            VLauncher = {'id' : '', 'name' : '', 'rom_count' : '', 'roms_base_noext' : ''}
            for rom_child in root_element:
                # By default read strings
                text_XML = rom_child.text if rom_child.text is not None else ''
                text_XML = misc.unescape_XML(text_XML)
                xml_tag  = rom_child.tag
                if __debug_xml_parser: log.debug('{} --> {}'.format(xml_tag, text_XML))
                VLauncher[xml_tag] = text_XML
            ret['vlaunchers'][VLauncher['id']] = VLauncher
    return ret

# -------------------------------------------------------------------------------------------------
# NFO files
# -------------------------------------------------------------------------------------------------
# [TODO] Finish this function.
def get_NFO_FileName(cfg, obj_ID, obj_dic):
    if obj_ID == const.OBJECT_CATEGORY_ID:
        category_name = obj_dic['m_name']
        nfo_dir = cfg.settings['categories_asset_dir']
        return utils.FileName(os.path.join(nfo_dir, category_name + '.nfo'))
    elif obj_ID == const.OBJECT_COLLECTION_ID:
        collection_name = obj_dic['m_name']
        nfo_dir = cfg.settings['collections_asset_dir']
        return utils.FileName(os.path.join(nfo_dir, collection_name + '.nfo'))
    elif obj_ID == const.OBJECT_LAUNCHER_ID:
        launcher_name = obj_dic['m_name']
        nfo_dir = cfg.settings['launchers_asset_dir']
        return utils.FileName(os.path.join(nfo_dir, launcher_name + '.nfo'))
    elif obj_ID == const.OBJECT_ROM_ID:
        ROM_FN = utils.FileName(obj_dic['filename'])
        return utils.FileName(ROM_FN.getPathNoExt() + '.nfo')
    else:
        raise RuntimeError

# Updates a dictionary with the contents of a XML tag.
# Dictionary field is updated by reference.
# Regular expressions are greedy by default.
# If RE has no groups it returns a list of strings with the matches.
# If RE has groups then it returns a list of groups.
# See https://docs.python.org/2/library/re.html#re.findall
#
# Example: mydic[mydic_field_name] = contents of tag <xml_tag_name> as a string
def update_dic_with_NFO_str(nfo_str, xml_tag_name, mydic, mydic_field_name):
    # log.debug('update_dic_with_NFO_str() nfo_str "{}"'.format(nfo_str))
    # log.debug('update_dic_with_NFO_str() xml_tag_name "{}"'.format(xml_tag_name))
    # log.debug('update_dic_with_NFO_str() mydic_field_name "{}"'.format(mydic_field_name))
    regex_str = '<{}>(.*?)</{}>'.format(xml_tag_name, xml_tag_name)
    findall_slist = re.findall(regex_str, nfo_str)
    if len(findall_slist) < 1: return
    findall_str = findall_slist[0].strip()
    unescaped_XML_str = text_unescape_XML(findall_str)
    mydic[mydic_field_name] = unescaped_XML_str

# When called from "Edit ROM" --> "Edit Metadata" --> "Import metadata from NFO file" function
# should be verbose and print notifications.
# However, this function is also used to export launcher ROMs in bulk in
# "Edit Launcher" --> "Manage ROM List" --> "Export ROMs metadata to NFO files". In that case,
# function must not be verbose because it can be called thousands of times for big ROM sets!
# Returns True if success, False if error (IO exception or file not written).
def export_ROM_NFO(rom, verbose = True):
    # Skip No-Intro Added ROMs. rom['filename'] will be empty.
    if not rom['filename']: return False
    ROM_FN = FileName(rom['filename'])
    nfo_file_path = ROM_FN.getPathNoExt() + '.nfo'
    log.debug('export_ROM_NFO() Exporting "{}"'.format(nfo_file_path))

    # Always overwrite NFO files.
    nfo_content = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<!-- Exported by AEL on {} -->'.format(time.strftime("%Y-%m-%d %H:%M:%S")),
        '<game>',
        misc.XML('title', rom['m_name']),
        misc.XML('year', rom['m_year']),
        misc.XML('genre', rom['m_genre']),
        misc.XML('developer', rom['m_developer']),
        misc.XML('nplayers', rom['m_nplayers']),
        misc.XML('esrb', rom['m_esrb']),
        misc.XML('rating', rom['m_rating']),
        misc.XML('plot', rom['m_plot']),
        '</game>\n',
    ]
    # TODO: report error if exception is produced here.
    utils.write_slist_to_file(nfo_file_path, nfo_content)
    if verbose:
        kodi_notify('Created NFO file {}'.format(nfo_file_path))
    return True

# Reads an NFO file with ROM information.
# Modifies roms dictionary even outside this function. See comments in fs_import_launcher_NFO()
# Returns True if success, False if error (IO exception).
def import_ROM_NFO(roms, romID, verbose = True):
    nfo_dic = roms[romID]
    ROMFileName = FileName(roms[romID]['filename'])
    nfo_file_path = ROMFileName.getPathNoExt() + '.nfo'
    log.debug('import_ROM_NFO() Loading "{}"'.format(nfo_file_path))

    # Check if file exists.
    if not os.path.isfile(nfo_file_path):
        if verbose:
            kodi.notify_warn('NFO file not found {}'.format(nfo_file_path))
        log.debug("import_ROM_NFO() NFO file not found '{}'".format(nfo_file_path))
        return False

    # Read file, put in a string and remove all line endings.
    # We assume NFO files are UTF-8. Decode data to Unicode.
    #
    # Future work: ESRB and maybe nplayers fields must be sanitized.
    nfo_str = utils_load_file_to_str(nfo_file_path).replace('\r', '').replace('\n', '')

    # Read XML tags in the NFO single-line string and edit fields in the ROM dictionary.
    update_dic_with_NFO_str(nfo_str, 'title', nfo_dic, 'm_name')
    update_dic_with_NFO_str(nfo_str, 'year', nfo_dic, 'm_year')
    update_dic_with_NFO_str(nfo_str, 'genre', nfo_dic, 'm_genre')
    update_dic_with_NFO_str(nfo_str, 'developer', nfo_dic, 'm_developer')
    update_dic_with_NFO_str(nfo_str, 'nplayers', nfo_dic, 'm_nplayers')
    update_dic_with_NFO_str(nfo_str, 'esrb', nfo_dic, 'm_esrb')
    update_dic_with_NFO_str(nfo_str, 'rating', nfo_dic, 'm_rating')
    update_dic_with_NFO_str(nfo_str, 'plot', nfo_dic, 'm_plot')

    if verbose:
        kodi_notify('Imported {}'.format(nfo_file_path))
    return True

# This file is called by the ROM scanner to read a ROM NFO file automatically.
# NFO file existence is checked before calling this function, so NFO file must always exist.
def import_ROM_NFO_file_scanner(NFO_FN):
    nfo_dic = {
        'title' : '',
        'year' : '',
        'genre' : '',
        'developer' : '',
        'nplayers' : '',
        'esrb' : '',
        'rating' : '',
        'plot' : '',
    }

    # Read file, put in a string and remove line endings to get a single-line string.
    nfo_str = utils_load_file_to_str(NFO_FN.getPath()).replace('\r', '').replace('\n', '')

    # Read XML tags in the NFO single-line string and edit fields in the ROM dictionary.
    update_dic_with_NFO_str(nfo_str, 'title', nfo_dic, 'title')
    update_dic_with_NFO_str(nfo_str, 'year', nfo_dic, 'year')
    update_dic_with_NFO_str(nfo_str, 'genre', nfo_dic, 'genre')
    update_dic_with_NFO_str(nfo_str, 'developer', nfo_dic, 'developer')
    update_dic_with_NFO_str(nfo_str, 'nplayers', nfo_dic, 'nplayers')
    update_dic_with_NFO_str(nfo_str, 'esrb', nfo_dic, 'esrb')
    update_dic_with_NFO_str(nfo_str, 'rating', nfo_dic, 'rating')
    update_dic_with_NFO_str(nfo_str, 'plot', nfo_dic, 'plot')

    return nfo_dic

# Standalone launchers: NFO files are stored in self.settings["launchers_nfo_dir"] if not empty.
# If empty, it defaults to DEFAULT_LAUN_NFO_DIR.
# ROM launchers: Same as standalone launchers.
# Notifies errors in Kodi GUI. Success is notified in the caller.
# Returns True if success, False if error (IO exception).
def export_launcher_NFO(nfo_FN, launcher):
    log.debug('export_launcher_NFO() Exporting launcher NFO "{}"'.format(nfo_FN.getPath()))

    # If NFO file does not exist then create them. If it exists, overwrite.
    nfo_slist = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<!-- Exported by AEL on {} -->'.format(time.strftime("%Y-%m-%d %H:%M:%S")),
        '<launcher>',
        misc.XML('year', launcher['m_year']),
        misc.XML('genre', launcher['m_genre']),
        misc.XML('developer', launcher['m_developer']),
        misc.XML('rating', launcher['m_rating']),
        misc.XML('plot', launcher['m_plot']),
        '</launcher>\n', # End file in newline
    ]
    # TODO: correctly catch and report errors here.
    utils.write_slist_to_file(nfo_FN.getPath(), nfo_slist)
    return True

# Launcher dictionary is edited by Python passing by reference.
# Notifies errors in Kodi GUI. Success is notified in the caller.
# Returns True if dictionary edited, False otherwise.
def import_launcher_NFO(nfo_FN, launchers, launcherID):
    nfo_dic = launchers[launcherID]

    log.debug('import_launcher_NFO() Importing "{}"'.format(nfo_FN.getPath()))
    if not os.path.isfile(nfo_FN.getPath()):
        kodi.notify_warn('NFO file not found {}'.format(os.path.basename(nfo_FN.getPath())))
        log.info("import_launcher_NFO() NFO file not found '{}'".format(nfo_FN.getPath()))
        return False

    # Read file, put in a single-line string and remove all line endings.
    nfo_str = utils_load_file_to_str(nfo_FN.getPath()).replace('\r', '').replace('\n', '')
    update_dic_with_NFO_str(nfo_str, 'year', nfo_dic, 'm_year')
    update_dic_with_NFO_str(nfo_str, 'genre', nfo_dic, 'm_genre')
    update_dic_with_NFO_str(nfo_str, 'developer', nfo_dic, 'm_developer')
    update_dic_with_NFO_str(nfo_str, 'rating', nfo_dic, 'm_rating')
    update_dic_with_NFO_str(nfo_str, 'plot', nfo_dic, 'm_plot')
    return True

# Used by autoconfig_import_launcher(). Returns a dictionary with the Launcher NFO file information.
# If there is any error return a dictionary with empty information.
def read_launcher_NFO(nfo_FN):
    nfo_dic = {
        'year' : '',
        'genre' : '',
        'developer' : '',
        'rating' : '',
        'plot' : '',
    }

    log.debug('read_launcher_NFO() Importing "{}"'.format(nfo_FN.getPath()))
    if not os.path.isfile(nfo_FN.getPath()):
        kodi.notify_warn('NFO file not found {}'.format(os.path.basename(nfo_FN.getPath())))
        log.info('read_launcher_NFO() NFO file not found "{}"'.format(nfo_FN.getPath()))
        return nfo_dic

    # Read file, put it in a single-line string by removing all line endings.
    nfo_str = utils_load_file_to_str(nfo_FN.getPath()).replace('\r', '').replace('\n', '')
    update_dic_with_NFO_str(nfo_str, 'year', nfo_dic, 'year')
    update_dic_with_NFO_str(nfo_str, 'genre', nfo_dic, 'genre')
    update_dic_with_NFO_str(nfo_str, 'developer', nfo_dic, 'developer')
    update_dic_with_NFO_str(nfo_str, 'rating', nfo_dic, 'rating')
    update_dic_with_NFO_str(nfo_str, 'plot', nfo_dic, 'plot')
    return nfo_dic

# Look at the Launcher NFO files for a reference implementation.
def export_category_NFO(NFO_FN, category):
    log.debug('export_category_NFO() Exporting "{}"'.format(NFO_FN.getPath()))
    # If NFO file does not exist then create them. If it exists, overwrite.
    nfo_slist = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<!-- Exported by AEL on {} -->'.format(time.strftime("%Y-%m-%d %H:%M:%S")),
        '<category>',
        misc.XML('year', category['m_year']),
        misc.XML('genre', category['m_genre']),
        misc.XML('developer', category['m_developer']),
        misc.XML('rating', category['m_rating']),
        misc.XML('plot', category['m_plot']),
        '</category>\n', # End file in newline
    ]
    utils.write_slist_to_file(NFO_FN.getPath(), nfo_slist)
    return True

def import_category_NFO(NFO_FN, edict):
    log.debug('import_category_NFO() Importing "{}"'.format(NFO_FN.getPath()))
    if not NFO_FN.isfile():
        kodi.notify_warn('NFO file not found {}'.format(os.path.basename(NFO_FN.getPath())))
        log.error('import_category_NFO() Not found "{}"'.format(NFO_FN.getPath()))
        return False
    nfo_str = utils_load_file_to_str(NFO_FN.getPath()).replace('\r', '').replace('\n', '')
    update_dic_with_NFO_str(nfo_str, 'year', edict, 'm_year')
    update_dic_with_NFO_str(nfo_str, 'genre', edict, 'm_genre')
    update_dic_with_NFO_str(nfo_str, 'developer', edict, 'm_developer')
    update_dic_with_NFO_str(nfo_str, 'rating', edict, 'm_rating')
    update_dic_with_NFO_str(nfo_str, 'plot', edict, 'm_plot')
    return True

# Collection NFO files. Same as Category NFO files.
def export_collection_NFO(nfo_FileName, collection):
    log.debug('export_collection_NFO() Exporting "{}"'.format(nfo_FileName.getPath()))

    # If NFO file does not exist then create them. If it exists, overwrite.
    nfo_slist = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<!-- Exported by AEL on {} -->'.format(time.strftime("%Y-%m-%d %H:%M:%S")),
        '<collection>',
        misc.XML('genre', collection['m_genre']),
        misc.XML('rating', collection['m_rating']),
        misc.XML('plot', collection['m_plot']),
        '</collection>\n', # End file in newline
    ]
    utils.write_slist_to_file(nfo_FileName.getPath(), nfo_slist)
    return True

# Notifies errors in Kodi GUI. Success is notified in the caller.
# Returns True if dictionary edited, False otherwise.
def import_collection_NFO(nfo_FN, collections, launcherID):
    log.debug('import_collection_NFO() Importing "{}"'.format(nfo_FN.getPath()))
    if not nfo_FN.isfile():
        kodi.notify_warn('NFO file not found {}'.format(os.path.basename(nfo_FN.getOriginalPath())))
        log.error("import_collection_NFO() Not found '{}'".format(nfo_FN.getPath()))
        return False

    nfo_str = utils_load_file_to_str(nfo_FN.getPath()).replace('\r', '').replace('\n', '')
    update_dic_with_NFO_str(nfo_str, 'genre', nfo_dic, 'm_genre')
    update_dic_with_NFO_str(nfo_str, 'rating', nfo_dic, 'm_rating')
    update_dic_with_NFO_str(nfo_str, 'plot', nfo_dic, 'm_plot')
    return True
