# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher main script file.
#

# Copyright (c) 2016-2018 Wintermute0110 <wintermute0110@gmail.com>
# Portions (c) 2010-2015 Angelscry
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# Viewqueries.py contains all methods that collect items to be shown
# in the UI containers. It combines custom data from repositories
# with static/predefined data.
# All methods have the prefix 'qry_'.

# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import logging
import typing

from resources.lib import globals
from resources.lib.repositories import ViewRepository
from resources.lib.settings import *
from resources.lib.constants import *

logger = logging.getLogger(__name__)

#
# Root view items
#
def qry_get_root_items():
    views_repository = ViewRepository(globals.g_PATHS, globals.router)
    container = views_repository.find_root_items()
    
    if container is None:
        container = {
            'id': '',
            'name': 'root',
            'obj_type': OBJ_CATEGORY,
            'items': []
        }
    
    vcategory_fanart = globals.g_PATHS.FANART_FILE_PATH.getPath()
    # --- AEL Favourites special category ---
    if not getSettingAsBool('display_hide_favs'): 
        # fav_icon   = 'DefaultFolder.png'
        vcategory_name   = '<Favourites>'
        vcategory_icon   = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Favourites_icon.png').getPath()
        vcategory_poster = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Favourites_poster.png').getPath()
        container['items'].append({
            'name': vcategory_name,
            'url': globals.router.url_for_path('vcategory/favourites'), #SHOW_FAVOURITES
            'is_folder': True,
            'type': 'video',
            'info': {
                'title': vcategory_name,
                'plot': 'Browse AEL Favourite ROMs',
                'overlay': 4
            },
            'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster },
            'properties': { AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_ROM_LAUNCHER, 'obj_type': OBJ_NONE }
        })

    # --- AEL Collections special category ---
    #if not getSettingAsBool('display_hide_collections'): render_vcategory_collections_row()
    # --- AEL Virtual Categories ---
    #if not getSettingAsBool('display_hide_vlaunchers'): render_vcategory_Browse_by_row()
    # --- Browse Offline Scraper database ---
    #if not getSettingAsBool('display_hide_AEL_scraper'): render_vcategory_AEL_offline_scraper_row()
    #if not getSettingAsBool('display_hide_LB_scraper'):  render_vcategory_LB_offline_scraper_row()

    # --- Recently played and most played ROMs ---
    if not getSettingAsBool('display_hide_recent'): 
        vcategory_name   = '[Recently played ROMs]'
        vcategory_icon   = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Recently_played_icon.png').getPath()
        vcategory_poster = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Recently_played_poster.png').getPath()
        container['items'].append({
            'name': vcategory_name,
            'url': globals.router.url_for_path('vcategory/recently_played'), #SHOW_RECENTLY_PLAYED'
            'is_folder': True,
            'type': 'video',
            'info': {
                'title': vcategory_name,
                'plot': 'Browse the ROMs you played recently',
                'overlay': 4
            },
            'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster },
            'properties': { AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_ROM_LAUNCHER, 'obj_type': OBJ_NONE }
        })

    if not getSettingAsBool('display_hide_mostplayed'): 
        vcategory_name   = '[Most played ROMs]'
        vcategory_icon   = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Most_played_icon.png').getPath()
        vcategory_poster = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Most_played_poster.png').getPath()
        container['items'].append({
            'name': vcategory_name,
            'url': globals.router.url_for_path('vcategory/most_played'), #SHOW_MOST_PLAYED
            'is_folder': True,
            'type': 'video',
            'info': {
                'title': vcategory_name,
                'plot': 'Browse the ROMs you play most',
                'overlay': 4
            },
            'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster },
            'properties': { AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_ROM_LAUNCHER, 'obj_type': OBJ_NONE }
        })
        
    if not getSettingAsBool('display_hide_utilities'): 
        vcategory_name   = 'Utilities'
        vcategory_icon   = globals.g_PATHS.ICON_FILE_PATH.getPath()
        vcategory_fanart = globals.g_PATHS.FANART_FILE_PATH.getPath()
        container['items'].append({
            'name': vcategory_name,
            'url': globals.router.url_for_path('utilities'), #SHOW_UTILITIES_VLAUNCHERS
            'is_folder': True,
            'type': 'video',
            'info': {
                'title': vcategory_name,
                'plot': 'Execute several [COLOR orange]Utilities[/COLOR].',
                'overlay': 4
            },
            'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster },
            'properties': { AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_CATEGORY, 'obj_type': OBJ_NONE }
        })
        
    if not getSettingAsBool('display_hide_g_reports'): 
        vcategory_name   = 'Global Reports'
        vcategory_icon   = globals.g_PATHS.ICON_FILE_PATH.getPath()
        vcategory_fanart = globals.g_PATHS.FANART_FILE_PATH.getPath()
        container['items'].append({
            'name': vcategory_name,
            'url': globals.router.url_for_path('globalreports'), #SHOW_GLOBALREPORTS_VLAUNCHERS'
            'is_folder': True,
            'type': 'video',
            'info': {
                'title': vcategory_name,
                'plot': 'Generate and view [COLOR orange]Global Reports[/COLOR].',
                'overlay': 4
            },
            'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster },
            'properties': { AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_CATEGORY, 'obj_type': OBJ_NONE }
        })
    
    return container

#
# Collection items.
#
def qry_get_collection_items(collection_id: str):
    views_repository = ViewRepository(globals.g_PATHS, globals.router)
    container = views_repository.find_items(collection_id)
    return container

#
# Utilities items
#
def qry_get_utilities_items():
    # --- Common artwork for all Utilities VLaunchers ---
    vcategory_icon   = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Utilities_icon.png').getPath()
    vcategory_fanart = globals.g_PATHS.FANART_FILE_PATH.getPath()
    vcategory_poster = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Utilities_poster.png').getPath()
    
    container = {
        'id': '',
        'name': 'utilities',
        'obj_type': OBJ_NONE,
        'items': []
    }

    container['items'].append({
        'name': 'Reset database',
        'url': globals.router.url_for_path('execute/command/reset_database'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Reset database',
            'plot': 'Reset the AEL database. You will loose all data.',
            'overlay': 4
        },
        'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster  },
        'properties': { AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_NONE, 'obj_type': OBJ_NONE }
    })
    container['items'].append({
        'name': 'Rebuild views',
        'url': globals.router.url_for_path('execute/command/render_views'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Rebuild views',
            'plot': 'Rebuild all the container views in the application',
            'overlay': 4
        },
        'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster  },
        'properties': { AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_NONE, 'obj_type': OBJ_NONE }
    })
    container['items'].append({
        'name': 'Scan for plugin-addons',
        'url': globals.router.url_for_path('execute/command/scan_for_addons'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Scan for plugin-addons',
            'plot': 'Scan for addons that can be used by AEL (launchers, scrapers etc.)',
            'overlay': 4
        },
        'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster  },
        'properties': { AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_NONE, 'obj_type': OBJ_NONE }
    })
    container['items'].append({
        'name': 'Import category/launcher XML configuration file',
        'url': globals.router.url_for_path('execute/command/import_launchers'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Import category/launcher XML configuration file',
            'plot': 'Execute several [COLOR orange]Utilities[/COLOR].',
            'overlay': 4
        },
        'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster  },
        'properties': { AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_NONE, 'obj_type': OBJ_NONE }
    })
    container['items'].append({
        'name': 'Export category/launcher XML configuration file',
        'url': globals.router.url_for_path('utilities/export_launchers'), #EXECUTE_UTILS_EXPORT_LAUNCHERS
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Export category/launcher XML configuration file',
            'plot': (
                'Exports all AEL categories and launchers into an XML configuration file. '
                'You can later reimport this XML file.'),
            'overlay': 4
        },
        'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster  },
        'properties': { AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_NONE, 'obj_type': OBJ_NONE }
    })
    container['items'].append({
        'name': 'Check/Update all databases',
        'url': globals.router.url_for_path('EXECUTE_UTILS_CHECK_DATABASE'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Check/Update all databases',
            'plot': (
                'Exports all AEL categories and launchers into an XML configuration file. '
                'You can later reimport this XML file.'),
            'overlay': 4
        },
        'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster  },
        'properties': { AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_NONE, 'obj_type': OBJ_NONE }
    })
    container['items'].append({
        'name': 'Check Launchers',
        'url': globals.router.url_for_path('EXECUTE_UTILS_CHECK_LAUNCHERS'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Check Launchers',
            'plot':  ('Check all Launchers for missing executables, missing artwork, '
                    'wrong platform names, ROM path existence, etc.'),
            'overlay': 4
        },
        'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster  },
        'properties': { AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_NONE, 'obj_type': OBJ_NONE }
    })
    container['items'].append({
        'name': 'Check Launcher ROMs sync status',
        'url': globals.router.url_for_path('EXECUTE_UTILS_CHECK_LAUNCHER_SYNC_STATUS'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Check Launcher ROMs sync status',
            'plot': ('For all ROM Launchers, check if all the ROMs in the ROM path are in AEL '
                    'database. If any Launcher is out of sync because you were changing your ROM files, use '
                    'the [COLOR=orange]ROM Scanner[/COLOR] to add and scrape the missing ROMs and remove '
                    'any dead ROMs.'),
            'overlay': 4
        },
        'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster  },
        'properties': { AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_NONE, 'obj_type': OBJ_NONE }
    })
    container['items'].append({
        'name': 'Check ROMs artwork image integrity',
        'url': globals.router.url_for_path('EXECUTE_UTILS_CHECK_ROM_ARTWORK_INTEGRITY'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Check ROMs artwork image integrity',
            'plot': ('Scans existing [COLOR=orange]ROMs artwork images[/COLOR] in ROM Launchers '
                    'and verifies that the images have correct extension '
                    'and size is greater than 0. You can delete corrupted images to be rescraped later.'),
            'overlay': 4
        },
        'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster  },
        'properties': { AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_NONE, 'obj_type': OBJ_NONE }
    })
    container['items'].append({
        'name': 'Delete ROMs redundant artwork',
        'url': globals.router.url_for_path('EXECUTE_UTILS_DELETE_ROM_REDUNDANT_ARTWORK'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Delete ROMs redundant artwork',
            'plot': ('Scans all ROM Launchers and finds '
                    '[COLOR orange]redundant ROMs artwork[/COLOR]. You may delete this unneeded images.'),
            'overlay': 4
        },
        'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster  },
        'properties': { AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_NONE, 'obj_type': OBJ_NONE }
    })
    
    return container

#
# Virtual category items
#
def qry_get_vcategory_items(self):
    vcategory_fanart = globals.g_PATHS.FANART_FILE_PATH.getPath()
    
    container = {
        'id': '',
        'name': 'virtual categories',
        'obj_type': OBJ_CATEGORY_VIRTUAL,
        'items': []
    }
    
    # --- AEL Favourites special category ---
    if not getSettingAsBool('display_hide_favs'): 
        # fav_icon   = 'DefaultFolder.png'
        vcategory_name   = '<Favourites>'
        vcategory_icon   = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Favourites_icon.png').getPath()
        vcategory_poster = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Favourites_poster.png').getPath()
        container['items'].append({
            'name': vcategory_name,
            'url': globals.router.url_for_path('vcategory/favourites'), #SHOW_FAVOURITES
            'is_folder': True,
            'type': 'video',
            'info': {
                'title': vcategory_name,
                'plot': 'Browse AEL Favourite ROMs',
                'overlay': 4
            },
            'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster },
            'properties': { AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_CATEGORY, 'obj_type': OBJ_NONE }
        })

    # --- AEL Collections special category ---
    #if not getSettingAsBool('display_hide_collections'): render_vcategory_collections_row()
    # --- AEL Virtual Categories ---
    #if not getSettingAsBool('display_hide_vlaunchers'): render_vcategory_Browse_by_row()
    # --- Browse Offline Scraper database ---
    #if not getSettingAsBool('display_hide_AEL_scraper'): render_vcategory_AEL_offline_scraper_row()
    #if not getSettingAsBool('display_hide_LB_scraper'):  render_vcategory_LB_offline_scraper_row()

    # --- Recently played and most played ROMs ---
    if not getSettingAsBool('display_hide_recent'): 
        vcategory_name   = '[Recently played ROMs]'
        vcategory_icon   = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Recently_played_icon.png').getPath()
        vcategory_poster = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Recently_played_poster.png').getPath()
        container['items'].append({
            'name': vcategory_name,
            'url': globals.router.url_for_path('vcategory/recently_played'), #SHOW_RECENTLY_PLAYED'
            'is_folder': True,
            'type': 'video',
            'info': {
                'title': vcategory_name,
                'plot': 'Browse the ROMs you played recently',
                'overlay': 4
            },
            'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster },
            'properties': { AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_ROM_LAUNCHER, 'obj_type': OBJ_NONE }
        })

    if not getSettingAsBool('display_hide_mostplayed'): 
        vcategory_name   = '[Most played ROMs]'
        vcategory_icon   = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Most_played_icon.png').getPath()
        vcategory_poster = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Most_played_poster.png').getPath()
        container['items'].append({
            'name': vcategory_name,
            'url': globals.router.url_for_path('vcategory/most_played'), #SHOW_MOST_PLAYED
            'is_folder': True,
            'type': 'video',
            'info': {
                'title': vcategory_name,
                'plot': 'Browse the ROMs you play most',
                'overlay': 4
            },
            'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster },
            'properties': { AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_ROM_LAUNCHER, 'obj_type': OBJ_NONE }
        })
        
    if not getSettingAsBool('display_hide_utilities'): 
        vcategory_name   = 'Utilities'
        vcategory_icon   = globals.g_PATHS.ICON_FILE_PATH.getPath()
        vcategory_fanart = globals.g_PATHS.FANART_FILE_PATH.getPath()
        container['items'].append({
            'name': vcategory_name,
            'url': globals.router.url_for_path('utilities'), #SHOW_UTILITIES_VLAUNCHERS
            'is_folder': True,
            'type': 'video',
            'info': {
                'title': vcategory_name,
                'plot': 'Execute several [COLOR orange]Utilities[/COLOR].',
                'overlay': 4
            },
            'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster },
            'properties': { AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_ROM_LAUNCHER, 'obj_type': OBJ_NONE }
        })
        
    if not getSettingAsBool('display_hide_g_reports'): 
        vcategory_name   = 'Global Reports'
        vcategory_icon   = globals.g_PATHS.ICON_FILE_PATH.getPath()
        vcategory_fanart = globals.g_PATHS.FANART_FILE_PATH.getPath()
        container['items'].append({
            'name': vcategory_name,
            'url': globals.router.url_for_path('globalreports'), #SHOW_GLOBALREPORTS_VLAUNCHERS'
            'is_folder': True,
            'type': 'video',
            'info': {
                'title': vcategory_name,
                'plot': 'Generate and view [COLOR orange]Global Reports[/COLOR].',
                'overlay': 4
            },
            'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster },
            'properties': { AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_ROM_LAUNCHER, 'obj_type': OBJ_NONE }
        })
        
#
# Default context menu items for the whole container.
#
def qry_container_context_menu_items(container_data) -> typing.List[typing.Tuple[str,str]]:
    if container_data is None:
        return []
    # --- Create context menu items to be applied to each item in this container ---
    container_type    = container_data['obj_type'] if 'obj_type' in container_data else OBJ_NONE
    
    is_category: bool = container_type == OBJ_CATEGORY
    is_romset: bool   = container_type == OBJ_ROMSET
    
    commands = []
    if is_category: 
        commands.append(('Add new Category', _context_menu_url_for('/categories/add/{}'.format(container_data['id']))))
        commands.append(('Add new Collection', _context_menu_url_for('/collections/add/{}'.format(container_data['id']))))
    commands.append(('Open Kodi file manager', 'ActivateWindow(filemanager)'))
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(globals.addon_id)))

    return commands

#
# ListItem specific context menu items.
#
def qry_listitem_context_menu_items(list_item_data, container_data)-> typing.List[typing.Tuple[str,str]]:
    if container_data is None or list_item_data is None:
        return []
    # --- Create context menu items only applicable on this item ---
    properties = list_item_data['properties'] if 'properties' in list_item_data else {}
    item_type  = properties['obj_type'] if 'obj_type' in properties else OBJ_NONE
    
    is_category: bool = item_type == OBJ_CATEGORY 
    is_romset: bool   = item_type == OBJ_ROMSET
    
    commands = []
    if is_category: commands.append(('Edit/Export Category', _context_menu_url_for('/categories/edit/{}'.format(list_item_data['id']))))
    
    return commands

def _context_menu_url_for(url: str) -> str:
    url = globals.router.url_for_path(url)
    return 'XBMC.RunPlugin({})'.format(url)