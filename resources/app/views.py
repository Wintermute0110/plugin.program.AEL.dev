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
from resources.app.viewqueries import *

from resources.lib.launchers import *
from resources.lib.scanners import *

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
    container = qry_get_root_items()
    container_context_items = qry_container_context_menu_items(container)

    render_list_items(container, container_context_items)
    xbmcplugin.endOfDirectory(handle = router.handle, succeeded = True, cacheToDisc = False)

@router.route('/collection/<collection_id>')
def vw_route_render_collection(collection_id: str):
    container               = qry_get_collection_items(collection_id)
    container_context_items = qry_container_context_menu_items(container)
    container_type          = container['obj_type'] if 'obj_type' in container else OBJ_NONE

    if container is None:
        kodi.notify('Current view is not rendered correctly. Re-render views first.')
    elif len(container['items']) == 0:
        if container_type == OBJ_CATEGORY:
            kodi.notify('Category {} has no items. Add romsets or categories first.'.format(container['name']))
        if container_type == OBJ_ROMSET:
            kodi.notify('ROMSet {} has no items. Add ROMs'.format(container['name']))
    else:
        render_list_items(container, container_context_items)
        
    xbmcplugin.endOfDirectory(handle = router.handle, succeeded = True, cacheToDisc = False)

# -------------------------------------------------------------------------------------------------
# Utilities and Global reports
# -------------------------------------------------------------------------------------------------
@router.route('/utilities')
def vw_route_render_utilities_vlaunchers():
    container = qry_get_utilities_items()
    container_context_items = qry_container_context_menu_items(container)

    render_list_items(container, container_context_items)
    xbmcplugin.endOfDirectory(handle = router.handle, succeeded = True, cacheToDisc = False)

# -------------------------------------------------------------------------------------------------
# Command execution
# -------------------------------------------------------------------------------------------------
@router.route('/execute/command/<cmd>')
def vw_execute_cmd(cmd: str):    
    kodi.event(command=cmd.capitalize(), data=router.args)

@router.route('/categories/view/<category_id>')
def vw_view_category(category_id: str):
    #todo
    pass

@router.route('/categories/add/<category_id>')
def vw_add_category(category_id: str):
    kodi.event(command='ADD_CATEGORY', data={'category_id': category_id})

@router.route('/categories/edit/<category_id>')
def vw_edit_category(category_id: str):
    kodi.event(command='EDIT_CATEGORY', data={'category_id': category_id })

@router.route('/romset/add/<romset_id>')
def vw_add_romset(romset_id: str):
    kodi.event(command='ADD_ROMSET', data={'romset_id': romset_id})

@router.route('/romset/view/<romset_id>')
def vw_view_romset(romset_id: str):
    #todo
    pass

@router.route('/romset/edit/<romset_id>')
def vw_edit_romset(romset_id: str):
    kodi.event(command='EDIT_ROMSET', data={'romset_id': romset_id })

@router.route('/execute/rom/<rom_id>')
def vw_route_execute_rom(rom_id):
    kodi.event(command="EXECUTE_ROM", data={'rom_id': rom_id} )

# -------------------------------------------------------------------------------------------------
# Internal launchers/scanner execution
# -------------------------------------------------------------------------------------------------
@router.route('/launcher/app/configure/')
def vw_configure_app_launcher():
    logger.debug('App Launcher: Configuring ...')

    romset_id:str   = router.args['romset_id'][0] if 'romset_id' in router.args else None
    launcher_id:str = router.args['launcher_id'][0] if 'launcher_id' in router.args else None
    settings:str    = router.args['settings'][0] if 'settings' in router.args else None
    
    launcher_settings = json.loads(settings)    
    launcher = AppLauncher(None, None, launcher_settings)
    if launcher_id is None and launcher.build():
        launcher.store_launcher_settings(romset_id)
        return
    
    if launcher_id is not None and launcher.edit():
        launcher.store_launcher_settings(romset_id, launcher_id)
        return
    
    kodi.notify_warn('Cancelled creating launcher')
    
@router.route('/launcher/app/')
def vw_execute_app_launcher():
    logger.debug('App Launcher: Starting ...')
    launcher_settings   = json.loads(router.args['settings'][0])
    arguments           = router.args['args'][0]

    execution_settings = ExecutionSettings()
    execution_settings.delay_tempo = settings.getSettingAsInt('delay_tempo')
    execution_settings.display_launcher_notify = settings.getSettingAsBool('display_launcher_notify')
    execution_settings.is_non_blocking = True if router.args['is_non_blocking'][0] == 'true' else False
    execution_settings.media_state_action = settings.getSettingAsInt('media_state_action')
    execution_settings.suspend_audio_engine = settings.getSettingAsBool('suspend_audio_engine')
    execution_settings.suspend_screensaver = settings.getSettingAsBool('suspend_screensaver')
            
    executor_factory = get_executor_factory()
    launcher = AppLauncher(executor_factory, execution_settings, launcher_settings)
    launcher.launch(arguments)
    
@router.route('/scanner/folder/configure')
def vw_configure_folder_scanner():
    logger.debug('ROM Folder scanner: Configuring ...')

    romset_id:str               = router.args['romset_id'][0] if 'romset_id' in router.args else None
    scanner_id:str              = router.args['scanner_id'][0] if 'scanner_id' in router.args else None
    settings:str                = router.args['settings'][0] if 'settings' in router.args else None
    def_launcher_settings:str   = router.args['launcher'][0] if 'launcher' in router.args else None
    
    scanner_settings = json.loads(settings) if settings else None
    launcher_settings = json.loads(def_launcher_settings) if def_launcher_settings else None
    
    scanner = RomFolderScanner(
        globals.g_PATHS.REPORTS_DIR, 
        globals.g_PATHS.ADDON_DATA_DIR,
        scanner_settings,
        launcher_settings,
        kodi.ProgressDialog())
    
    if scanner.configure():
        scanner.store_scanner_settings(romset_id, scanner_id)
        return
    
    kodi.notify_warn('Cancelled configuring scanner')

@router.route('/scanner/folder')
def vw_execute_folder_scanner():
    logger.debug('ROM Folder scanner: Starting scan ...')
    romset_id:str   = router.args['romset_id'][0] if 'romset_id' in router.args else None
    scanner_id:str  = router.args['scanner_id'][0] if 'scanner_id' in router.args else None
    settings:str    = router.args['settings'][0] if 'settings' in router.args else None

    scanner_settings = json.loads(settings) if settings else None
    progress_dialog = kodi.ProgressDialog()
        
    scanner = RomFolderScanner(
        globals.g_PATHS.REPORTS_DIR, 
        globals.g_PATHS.ADDON_DATA_DIR,
        scanner_settings,
        None,
        progress_dialog)
    
    roms_scanned = scanner.scan(scanner_id)
    progress_dialog.endProgress()
    
    logger.debug('vw_execute_folder_scanner(): Finished scanning')
    
    if roms_scanned is None:
        logger.info('vw_execute_folder_scanner(): No roms scanned')
        return
        
    logger.info('vw_execute_folder_scanner(): {} roms scanned'.format(len(roms_scanned)))
    scanner.store_scanned_roms(romset_id, scanner_id, roms_scanned)
    kodi.notify('ROMs scanning done')

    
# -------------------------------------------------------------------------------------------------
# UI render methods
# -------------------------------------------------------------------------------------------------
#
#
# Renders all categories without Favourites, Collections, virtual categories, etc.
#
def render_list_items(container_data, container_context_items = []):
    vw_misc_set_all_sorting_methods()
    vw_misc_set_AEL_Content(container_data['obj_type'] if 'obj_type' in container_data else OBJ_NONE)
    vw_misc_clear_AEL_Launcher_Content()

    for list_item_data in container_data['items']:
        
        name        = list_item_data['name']
        url_str     = list_item_data['url']
        folder_flag = list_item_data['is_folder'] 
        item_type   = list_item_data['type']

        list_item = xbmcgui.ListItem(name)
        list_item.setInfo(item_type, list_item_data['info'])
        list_item.setArt(list_item_data['art'])
        list_item.setProperties(list_item_data['properties'])

        if xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)"):
            item_context_items = qry_listitem_context_menu_items(list_item_data, container_data)
            list_item.addContextMenuItems(item_context_items + container_context_items, replaceItems = True)

        xbmcplugin.addDirectoryItem(handle = router.handle, url = url_str, listitem = list_item, isFolder = folder_flag)

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
        
    elif AEL_Content_Value == AEL_CONTENT_VALUE_CATEGORY:
        logger.debug('vw_misc_set_AEL_Content() Setting Window({0}) '.format(AEL_CONTENT_WINDOW_ID) +
                  'property "{0}" = "{1}"'.format(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_CATEGORY))
        xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_CATEGORY)        
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
    