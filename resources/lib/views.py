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

# Location of functions within code:
# 1. Functions in views.py have vw_ prefix.
# 2. Functions accessible by routes have vw_route prefix
#
# Views.py contains all methods accessible by URL commands (using routes/paths)
# triggered from Kodi. The methods will only perform operations to render and visualize
# the list items in the containers.
# AEL follows a (sortof) CQRS architecture, meaning that all actions to gather the items 
# or to perform commands are delegated to the queries.py file and different **_commands.py 
# files. Query methods are called directly and the Command methods are called through
# sending notifications to the AEL service (Monitor).
#
# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division
import sys
import logging

# --- Kodi stuff ---
import xbmc
import xbmcgui
import xbmcplugin

from resources.lib.globals import *
from resources.lib.constants import *
from resources.lib.repositories import *
from resources.lib.settings import *
from resources.lib.viewqueries import *

from resources.lib.utils import kodi

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------------------------
# This is the plugin entry point.
# ---------------------------------------------------------------------------------------------
def run_plugin(addon_argv):
    # --- Initialise log system ---
    # >> Force DEBUG log level for development.
    # >> Place it before settings loading so settings can be dumped during debugging.
    # set_log_level(LOG_DEBUG)

    # --- Some debug stuff for development ---
    logger.debug('------------ Called Advanced Emulator Launcher run_plugin(addon_argv) ------------')
    logger.debug('addon.id         "{}"'.format(addon_id))
    logger.debug('addon.version    "{}"'.format(addon_version))
    for i in range(len(sys.argv)): logger.debug('sys.argv[{}] "{}"'.format(i, sys.argv[i]))

    # --- Bootstrap object instances --- 
    g_bootstrap_instances()
    router.run()
    logger.debug('Advanced Emulator Launcher run_plugin() exit')

# -------------------------------------------------------------------------------------------------
# LisItem rendering
# -------------------------------------------------------------------------------------------------
@router.route('/')
def vw_route_render_root():
    list_items_data = qry_get_root_items()
    context_items = build_context_menu_items(is_category=True)

    render_list_items(list_items_data, context_items)
    xbmcplugin.endOfDirectory(handle = router.handle, succeeded = True, cacheToDisc = False)

@router.route('/collection/<collection_id>')
def vw_route_render_collection(collection_id):
    list_items_data = g_ViewRepository.find_items(collection_id)
    
    render_list_items(list_items_data)
    xbmcplugin.endOfDirectory(handle = router.handle, succeeded = True, cacheToDisc = False)

# -------------------------------------------------------------------------------------------------
# Utilities and Global reports
# -------------------------------------------------------------------------------------------------
@router.route('/utilities')
def vw_route_render_utilities_vlaunchers():
    list_items_data = qry_get_utilities_items()
    context_items = build_context_menu_items()

    render_list_items(list_items_data, context_items)
    xbmcplugin.endOfDirectory(handle = router.handle, succeeded = True, cacheToDisc = False)

@router.route('/utilities/import_launchers')
def vw_route_import_launchers():
    kodi.event(method='import_launchers')

@router.route('/utilities/rebuild_views')
def vw_rebuild_views():
    kodi.event(method='RENDER_VIEWS')

@router.route('EXECUTE')
def vw_route_execute_rom(rom_id):
    pass

# -------------------------------------------------------------------------------------------------
# UI render methods
# -------------------------------------------------------------------------------------------------
#
#
# Renders all categories without Favourites, Collections, virtual categories, etc.
#
def render_list_items(list_items_data, context_items = []):
    vw_misc_set_all_sorting_methods()
    vw_misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)
    vw_misc_clear_AEL_Launcher_Content()

    for list_item_data in list_items_data:
        
        name        = list_item_data['name']
        url_str     = list_item_data['url']
        folder_flag = list_item_data['is_folder'] 
        item_type   = list_item_data['type']

        list_item = xbmcgui.ListItem(name)
        list_item.setInfo(item_type, list_item_data['info'])
        list_item.setArt(list_item_data['art'])
        list_item.setProperties(list_item_data['properties'])

        if xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)"):
            list_item.addContextMenuItems(context_items)

        xbmcplugin.addDirectoryItem(handle = router.handle, url = url_str, listitem = list_item, isFolder = folder_flag)

def build_context_menu_items(is_category = False):
    # --- Create context menu ---
    commands = []
    is_category: commands.append(('Add new Collection', router.url_for('ADD_LAUNCHER_ROOT')))
    is_category: commands.append(('Add new Category', router.url_for('ADD_CATEGORY')))
    commands.append(('Open Kodi file manager', 'ActivateWindow(filemanager)'))
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(addon_id)))

    return commands

# -------------------------------------------------------------------------------------------------
# UI helper methods
# -------------------------------------------------------------------------------------------------
#
#
#
def vw_misc_set_all_sorting_methods():
    # >> This must be called only if router.handle > 0, otherwise Kodi will complain in the log.
    if router.handle < 0: return
    xbmcplugin.addSortMethod(handle = router.handle, sortMethod = xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
    xbmcplugin.addSortMethod(handle = router.handle, sortMethod = xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(handle = router.handle, sortMethod = xbmcplugin.SORT_METHOD_STUDIO)
    xbmcplugin.addSortMethod(handle = router.handle, sortMethod = xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(handle = router.handle, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)

#
# Set the AEL content type.
# It is a Window(10000) property used by skins to know if AEL is rendering
# a Window that has categories/launchers or ROMs.
#
def vw_misc_set_AEL_Content(AEL_Content_Value):
    if AEL_Content_Value == AEL_CONTENT_VALUE_LAUNCHERS:
        logger.debug('vw_misc_set_AEL_Content() Setting Window({0}) '.format(AEL_CONTENT_WINDOW_ID) +
                  'property "{0}" = "{1}"'.format(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_LAUNCHERS))
        xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_LAUNCHERS)
    elif AEL_Content_Value == AEL_CONTENT_VALUE_ROMS:
        logger.debug('vw_misc_set_AEL_Content() Setting Window({0}) '.format(AEL_CONTENT_WINDOW_ID) +
                  'property "{0}" = "{1}"'.format(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROMS))
        xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROMS)
    elif AEL_Content_Value == AEL_CONTENT_VALUE_NONE:
        logger.debug('vw_misc_set_AEL_Content() Setting Window({0}) '.format(AEL_CONTENT_WINDOW_ID) +
                  'property "{0}" = "{1}"'.format(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_NONE))
        xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_NONE)
    else:
        logger.error('vw_misc_set_AEL_Content() Invalid AEL_Content_Value "{0}"'.format(AEL_Content_Value))

def vw_misc_clear_AEL_Launcher_Content():
    xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_LAUNCHER_NAME_LABEL, '')
    xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_LAUNCHER_ICON_LABEL, '')
    xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_LAUNCHER_CLEARLOGO_LABEL, '')
    xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_LAUNCHER_PLATFORM_LABEL, '')
    xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_LAUNCHER_BOXSIZE_LABEL, '')
    