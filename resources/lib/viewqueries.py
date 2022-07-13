# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: UI query implementations. Getting data for the UI
#

# Copyright (c) Wintermute0110 <wintermute0110@gmail.com> / Chrisism <crizizz@gmail.com>
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
from urllib.parse import urlencode

# AKL modules
from akl import constants, settings
from akl.utils import kodi

from resources.lib import globals
from resources.lib.commands.mediator import AppMediator
from resources.lib.commands import view_rendering_commands
from resources.lib.repositories import ViewRepository, UnitOfWork, ROMCollectionRepository, ROMsRepository
from resources.lib.domain import VirtualCollectionFactory

logger = logging.getLogger(__name__)
#

# Root view items
#
def qry_get_root_items():
    views_repository = ViewRepository(globals.g_PATHS)
    container = views_repository.find_root_items()
    
    if container is None:
        container = {
            'id': '',
            'name': 'root',
            'obj_type': constants.OBJ_CATEGORY,
            'items': []
        }
        kodi.notify('Building initial views')
        AppMediator.async_cmd('RENDER_VIEWS')
    
    listitem_fanart = globals.g_PATHS.FANART_FILE_PATH.getPath()
    
    if not settings.getSettingAsBool('display_hide_utilities'): 
        listitem_name   = 'Utilities'
        container['items'].append({
            'name': listitem_name,
            'url': globals.router.url_for_path('utilities'),
            'is_folder': True,
            'type': 'video',
            'info': {
                'title': listitem_name,
                'plot': 'Execute several [COLOR orange]Utilities[/COLOR].',
                'overlay': 4
            },
            'art': { 
                'fanart' : listitem_fanart, 
                'icon' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Utilities_icon.png').getPath(),
                'poster': globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Utilities_poster.png').getPath() 
            },
            'properties': { constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_CATEGORY, 'obj_type': constants.OBJ_NONE }
        })
        
    if not settings.getSettingAsBool('display_hide_g_reports'): 
        listitem_name   = 'Global Reports'
        container['items'].append({
            'name': listitem_name,
            'url': globals.router.url_for_path('globalreports'), #SHOW_GLOBALREPORTS_VLAUNCHERS'
            'is_folder': True,
            'type': 'video',
            'info': {
                'title': listitem_name,
                'plot': 'Generate and view [COLOR orange]Global Reports[/COLOR].',
                'overlay': 4
            },
            'art': { 
                'fanart' : listitem_fanart, 
                'icon' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Global_Reports_icon.png').getPath(),
                'poster': globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Global_Reports_poster.png').getPath() 
            },
            'properties': { constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_CATEGORY, 'obj_type': constants.OBJ_NONE }
        })
    
    return container

#
# View pre-rendered items.
#
def qry_get_view_items(view_id: str, is_virtual_view=False):
    views_repository = ViewRepository(globals.g_PATHS)
    container = views_repository.find_items(view_id, is_virtual_view)
    return container

#
# View database unrendered items.
#
def qry_get_database_view_items(category_id: str, collection_value: str):
    return view_rendering_commands.cmd_render_virtual_collection(category_id, collection_value)

#
# Utilities items
#
def qry_get_utilities_items():
    # --- Common artwork for all Utilities VLaunchers ---
    listitem_icon   = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Utilities_icon.png').getPath()
    listitem_fanart = globals.g_PATHS.FANART_FILE_PATH.getPath()
    listitem_poster = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Utilities_poster.png').getPath()
    
    container = {
        'id': '',
        'name': 'utilities',
        'obj_type': constants.OBJ_NONE,
        'items': []
    }

    # Deprecated commands:
    # EXECUTE_UTILS_CHECK_LAUNCHER_SYNC_STATUS -> todo: execute per collection, add report command to scanners
    # EXECUTE_UTILS_CHECK_DATABASE -> Substituted by db constraints and migration scripts.

    container['items'].append({
        'name': 'Reset database',
        'url': globals.router.url_for_path('execute/command/reset_database'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Reset database',
            'plot': 'Reset the AKL database. You will loose all data.',
            'overlay': 4
        },
        'art': { 'icon' : listitem_icon, 'fanart' : listitem_fanart, 'poster' : listitem_poster  },
        'properties': { constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
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
        'art': { 'icon' : listitem_icon, 'fanart' : listitem_fanart, 'poster' : listitem_poster  },
        'properties': { constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    container['items'].append({
        'name': 'Rebuild virtual views',
        'url': globals.router.url_for_path('execute/command/render_virtual_views'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Rebuild virtual views',
            'plot': 'Rebuild all the virtual categories and collections in the container',
            'overlay': 4
        },
        'art': { 'icon' : listitem_icon, 'fanart' : listitem_fanart, 'poster' : listitem_poster  },
        'properties': { constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    container['items'].append({
        'name': 'Scan for plugin-addons',
        'url': globals.router.url_for_path('execute/command/scan_for_addons'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Scan for plugin-addons',
            'plot': 'Scan for addons that can be used by AKL (launchers, scrapers etc.)',
            'overlay': 4
        },
        'art': { 'icon' : listitem_icon, 'fanart' : listitem_fanart, 'poster' : listitem_poster  },
        'properties': { constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    container['items'].append({
        'name': 'Manage ROM tags',
        'url': globals.router.url_for_path('execute/command/manage_rom_tags'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Manage ROM tags',
            'plot': 'Manage existing/available tags for ROMs',
            'overlay': 4
        },
        'art': { 'icon' : listitem_icon, 'fanart' : listitem_fanart, 'poster' : listitem_poster  },
        'properties': { constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
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
        'art': { 'icon' : listitem_icon, 'fanart' : listitem_fanart, 'poster' : listitem_poster  },
        'properties': { constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    container['items'].append({
        'name': 'Export category/rom collection XML configuration file',
        'url': globals.router.url_for_path('execute/command/export_to_legacy_xml'), 
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Export category/rom collection XML configuration file',
            'plot': (
                'Exports all AKL categories and collections into an XML configuration file. '
                'You can later reimport this XML file.'),
            'overlay': 4
        },
        'art': { 'icon' : listitem_icon, 'fanart' : listitem_fanart, 'poster' : listitem_poster  },
        'properties': { constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    container['items'].append({
        'name': 'Check collections',
        'url': globals.router.url_for_path('execute/command/check_collections'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Check collections',
            'plot':  ('Check all collections for missing launchers or scanners, missing artwork, '
                    'wrong platform names, asset path existence, etc.'),
            'overlay': 4
        },
        'art': { 'icon' : listitem_icon, 'fanart' : listitem_fanart, 'poster' : listitem_poster  },
        'properties': { constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    container['items'].append({
        'name': 'Check ROMs artwork image integrity',
        'url': globals.router.url_for_path('execute/command/check_rom_artwork_integrity'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Check ROMs artwork image integrity',
            'plot': ('Scans existing [COLOR=orange]ROMs artwork images[/COLOR] in ROM Collections '
                    'and verifies that the images have correct extension '
                    'and size is greater than 0. You can delete corrupted images to be rescraped later.'),
            'overlay': 4
        },
        'art': { 'icon' : listitem_icon, 'fanart' : listitem_fanart, 'poster' : listitem_poster  },
        'properties': { constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    container['items'].append({
        'name': 'Delete ROMs redundant artwork',
        'url': globals.router.url_for_path('execute/command/delete_redundant_rom_artwork'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Delete ROMs redundant artwork',
            'plot': ('Scans all ROM collections and finds '
                    '[COLOR orange]redundant ROMs artwork[/COLOR]. You may delete these unneeded images.'),
            'overlay': 4
        },
        'art': { 'icon' : listitem_icon, 'fanart' : listitem_fanart, 'poster' : listitem_poster  },
        'properties': { constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    container['items'].append({
        'name': 'Show detected No-Intro/Redump DATs',
        'url': globals.router.url_for_path('execute/command/EXECUTE_UTILS_SHOW_DETECTED_DATS'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Show detected No-Intro/Redump DATs',
            'plot': ('Display the auto-detected No-Intro/Redump DATs that will be used for the '
                    'ROM audit. You have to configure the DAT directories in '
                    '[COLOR orange]AKL addon settings[/COLOR], [COLOR=orange]ROM Audit[/COLOR] tab.'),
            'overlay': 4
        },
        'art': { 'icon' : listitem_icon, 'fanart' : listitem_fanart, 'poster' : listitem_poster  },
        'properties': { constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    
    return container

#
# Global Reports items
#
def qry_get_globalreport_items():
     # --- Common artwork for all Utilities VLaunchers ---
    listitem_icon   = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Global_Reports_icon.png').getPath()
    listitem_fanart = globals.g_PATHS.FANART_FILE_PATH.getPath()
    listitem_poster = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Global_Reports_poster.png').getPath()
    
    container = {
        'id': '',
        'name': 'globalreports',
        'obj_type': constants.OBJ_NONE,
        'items': []
    }

    # --- Global ROM statistics ---
    container['items'].append({
        'name': 'Global ROM statistics',
        'url': globals.router.url_for_path('execute/command/global_rom_stats'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Global ROM statistics',
            'plot': 'Shows a report of all ROM collections with number of ROMs.',
            'overlay': 4
        },
        'art': { 'icon' : listitem_icon, 'fanart' : listitem_fanart, 'poster' : listitem_poster  },
        'properties': { constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    
    # --- Global ROM Audit statistics  ---
    container['items'].append({
        'name': 'Global ROM Audit statistics (All)',
        'url': globals.router.url_for_path('execute/command/EXECUTE_GLOBAL_AUDIT_STATS_ALL'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Global ROM Audit statistics (All)',
            'plot': ('Shows a report of all audited ROM collections, with Have, Miss and Unknown '
                    'statistics.'),
            'overlay': 4
        },
        'art': { 'icon' : listitem_icon, 'fanart' : listitem_fanart, 'poster' : listitem_poster  },
        'properties': { constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    
    container['items'].append({
        'name': 'Global ROM Audit statistics (No-Intro only)',
        'url': globals.router.url_for_path('execute/command/EXECUTE_GLOBAL_AUDIT_STATS_NOINTRO'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Global ROM Audit statistics (No-Intro only)',
            'plot': ('Shows a report of all audited ROM Launchers, with Have, Miss and Unknown '
                    'statistics. Only No-Intro platforms (cartridge-based) are reported.'),
            'overlay': 4
        },
        'art': { 'icon' : listitem_icon, 'fanart' : listitem_fanart, 'poster' : listitem_poster  },
        'properties': { constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    
    container['items'].append({
        'name': 'Global ROM Audit statistics (Redump only)',
        'url': globals.router.url_for_path('execute/command/EXECUTE_GLOBAL_AUDIT_STATS_REDUMP'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Global ROM Audit statistics (Redump only)',
            'plot': ('Shows a report of all audited ROM Launchers, with Have, Miss and Unknown '
                    'statistics. Only Redump platforms (optical-based) are reported.'),
            'overlay': 4
        },
        'art': { 'icon' : listitem_icon, 'fanart' : listitem_fanart, 'poster' : listitem_poster  },
        'properties': { constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    return container

#
# Default context menu items for the whole container.
#
def qry_container_context_menu_items(container_data) -> typing.List[typing.Tuple[str,str]]:
    if container_data is None:
        return []
    # --- Create context menu items to be applied to each item in this container ---
    container_type     = container_data['obj_type'] if 'obj_type' in container_data else constants.OBJ_NONE
    container_name     = container_data['name'] if 'name' in container_data else 'Unknown'
    container_id       = container_data['id'] if 'id' in container_data else ''
    container_parentid = container_data['parent_id'] if 'parent_id' in container_data else ''
    
    is_category: bool           = container_type == constants.OBJ_CATEGORY
    is_romcollection: bool      = container_type == constants.OBJ_ROMCOLLECTION
    is_virtual_category: bool   = container_type == constants.OBJ_CATEGORY_VIRTUAL
    is_virtual_collection: bool = container_type == constants.OBJ_COLLECTION_VIRTUAL
    is_root: bool               = container_data['id'] == ''
    
    commands = []
    if is_category: 
        commands.append(('Rebuild {} view'.format(container_name),
                        _context_menu_url_for('execute/command/render_view',{'category_id':container_id})))    
    if is_romcollection:
        commands.append(('Search ROM in collection', _context_menu_url_for(f'/collection/{container_id}/search')))
        commands.append(('Rebuild {} view'.format(container_name),
                         _context_menu_url_for('execute/command/render_romcollection_view', {'romcollection_id':container_id})))    
    if is_virtual_category and not is_root:
        commands.append(('Rebuild {} view'.format(container_name),
                        _context_menu_url_for('execute/command/render_vcategory_view',{'vcategory_id':container_id})))
    if is_virtual_collection:
        commands.append(('Rebuild {} view'.format(container_name),
                        _context_menu_url_for('execute/command/render_vcategory_view',{'vcategory_id':container_parentid})))    
    
    commands.append(('Rebuild all views', _context_menu_url_for('execute/command/render_views')))
    commands.append(('Open Kodi file manager', 'ActivateWindow(filemanager)'))
    commands.append(('AKL addon settings', 'Addon.OpenSettings({0})'.format(globals.addon_id)))

    return commands

#
# ListItem specific context menu items.
#
def qry_listitem_context_menu_items(list_item_data, container_data)-> typing.List[typing.Tuple[str,str]]:
    if container_data is None or list_item_data is None:
        return []
    # --- Create context menu items only applicable on this item ---
    properties   = list_item_data['properties'] if 'properties' in list_item_data else {}
    item_type    = properties['obj_type'] if 'obj_type' in properties else constants.OBJ_NONE
    item_name    = list_item_data['name'] if 'name' in list_item_data else 'Unknown'
    item_id      = list_item_data['id'] if 'id' in list_item_data else ''
    
    container_id    = container_data['id'] if 'id' in container_data else constants.VCATEGORY_ADDONROOT_ID
    container_type  = container_data['obj_type'] if 'obj_type' in container_data else constants.OBJ_NONE
    if container_id == '': container_id = constants.VCATEGORY_ADDONROOT_ID
    
    container_is_category: bool = container_type == constants.OBJ_CATEGORY
    
    is_category: bool           = item_type == constants.OBJ_CATEGORY
    is_romcollection: bool      = item_type == constants.OBJ_ROMCOLLECTION
    is_virtual_category: bool   = item_type == constants.OBJ_CATEGORY_VIRTUAL
    is_virtual_collection: bool = item_type == constants.OBJ_COLLECTION_VIRTUAL
    is_rom: bool                = item_type == constants.OBJ_ROM
    
    commands = []
    if is_rom: 
        commands.append(('View ROM', _context_menu_url_for(f'/rom/{item_id}/view')))
        commands.append(('Edit ROM', _context_menu_url_for(f'/rom/edit/{item_id}')))
        commands.append(('Link ROM in other collection', _context_menu_url_for('/execute/command/link_rom',{'rom_id':item_id})))
        commands.append(('Add ROM to AKL Favourites', _context_menu_url_for('/execute/command/add_rom_to_favourites',{'rom_id':item_id})))
    if is_category: 
        commands.append(('View Category', _context_menu_url_for(f'/categories/view/{item_id}')))
        commands.append(('Edit Category', _context_menu_url_for(f'/categories/edit/{item_id}')))
        commands.append(('Add new Category',_context_menu_url_for(f'/categories/add/{item_id}/in/{container_id}')))
        commands.append(('Add new ROM Collection', _context_menu_url_for(f'/romcollection/add/{item_id}/in/{container_id}')))
        
    if is_romcollection: 
        commands.append(('View ROM Collection', _context_menu_url_for(f'/romcollection/view/{item_id}')))
        commands.append(('Edit ROM Collection', _context_menu_url_for(f'/romcollection/edit/{item_id}')))
    
    if not is_category and container_is_category:
        commands.append(('Add new Category',_context_menu_url_for(f'/categories/add/{container_id}')))
        commands.append(('Add new ROM Collection', _context_menu_url_for(f'/romcollection/add/{container_id}')))
    
    if is_virtual_category:
        commands.append((f'Rebuild {item_name} view', _context_menu_url_for('execute/command/render_vcategory_view',{'vcategory_id':item_id})))
        
    return commands

def _context_menu_url_for(url: str, params: dict = None) -> str:
    if params is not None:
        url = '{}?{}'.format(url, urlencode(params))
    url = globals.router.url_for_path(url)
    return 'RunPlugin({})'.format(url)