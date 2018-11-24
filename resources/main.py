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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# Location of functions within code:
# 1. Functions in main.py have m_ prefix.
# 2. Functions in assets.py have asset_ prefix.
#
# n. General objects are in objects.py.

# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division
import abc
import collections
import datetime
import exceptions
import fnmatch
import hashlib
import importlib
import os
import re
import shutil
import socket
import string
import sys
import time
import traceback
import urllib
import urllib2
import urlparse

# --- Python standard library named imports ---
from distutils.version import LooseVersion

# --- Kodi stuff ---
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

# --- Modules/packages in this addon ---
# Addon module dependencies:
#                        scrap_*
#                        net_IO      platforms     constants
#   main <-- objects <-- disk_IO <-- assets    <-- utils
#
from constants import *
from utils import *
from audit import *
from autoconfig import *
from disk_IO import *
from net_IO import *
from objects import *
from report import *
from scrap import *

# --- Addon object (used to access settings) ---
__addon__         = xbmcaddon.Addon()
__addon_id__      = __addon__.getAddonInfo('id').decode('utf-8')
__addon_name__    = __addon__.getAddonInfo('name').decode('utf-8')
__addon_version__ = __addon__.getAddonInfo('version').decode('utf-8')
__addon_author__  = __addon__.getAddonInfo('author').decode('utf-8')
__addon_profile__ = __addon__.getAddonInfo('profile').decode('utf-8')
__addon_type__    = __addon__.getAddonInfo('type').decode('utf-8')

# --- Addon paths and constant definition ---
# _PATH is a filename | _DIR is a directory.
class AEL_Paths:
    def __init__(self):
        # --- Base paths ---
        self.ADDONS_DATA_DIR  = FileName('special://profile/addon_data', isdir = True)
        self.ADDON_DATA_DIR   = self.ADDONS_DATA_DIR.pjoin(__addon_id__, isdir = True)
        self.PROFILE_DIR      = FileName('special://profile', isdir = True)
        self.HOME_DIR         = FileName('special://home', isdir = True)
        self.ADDONS_DIR       = self.HOME_DIR.pjoin('addons', isdir = True)
        self.ADDON_CODE_DIR   = self.ADDONS_DIR.pjoin(__addon_id__, isdir = True)
        self.ICON_FILE_PATH   = self.ADDON_CODE_DIR.pjoin('media/icon.png')
        self.FANART_FILE_PATH = self.ADDON_CODE_DIR.pjoin('media/fanart.jpg')

        # --- Databases and reports ---
        self.CATEGORIES_FILE_PATH      = self.ADDON_DATA_DIR.pjoin('categories.xml')
        self.FAV_JSON_FILE_PATH        = self.ADDON_DATA_DIR.pjoin('favourites.json')
        self.COLLECTIONS_FILE_PATH     = self.ADDON_DATA_DIR.pjoin('collections.xml')
        self.VCAT_TITLE_FILE_PATH      = self.ADDON_DATA_DIR.pjoin('vcat_title.xml')
        self.VCAT_YEARS_FILE_PATH      = self.ADDON_DATA_DIR.pjoin('vcat_years.xml')
        self.VCAT_GENRE_FILE_PATH      = self.ADDON_DATA_DIR.pjoin('vcat_genre.xml')
        self.VCAT_DEVELOPER_FILE_PATH  = self.ADDON_DATA_DIR.pjoin('vcat_developers.xml')
        self.VCAT_NPLAYERS_FILE_PATH   = self.ADDON_DATA_DIR.pjoin('vcat_nplayers.xml')
        self.VCAT_ESRB_FILE_PATH       = self.ADDON_DATA_DIR.pjoin('vcat_esrb.xml')
        self.VCAT_RATING_FILE_PATH     = self.ADDON_DATA_DIR.pjoin('vcat_rating.xml')
        self.VCAT_CATEGORY_FILE_PATH   = self.ADDON_DATA_DIR.pjoin('vcat_category.xml')
        # Launcher app stdout/stderr file
        self.LAUNCH_LOG_FILE_PATH      = self.ADDON_DATA_DIR.pjoin('launcher.log')
        self.RECENT_PLAYED_FILE_PATH   = self.ADDON_DATA_DIR.pjoin('history.json')
        self.MOST_PLAYED_FILE_PATH     = self.ADDON_DATA_DIR.pjoin('most_played.json')
        self.BIOS_REPORT_FILE_PATH     = self.ADDON_DATA_DIR.pjoin('report_BIOS.txt')
        self.LAUNCHER_REPORT_FILE_PATH = self.ADDON_DATA_DIR.pjoin('report_Launchers.txt')

        # --- Offline scraper databases ---
        self.GAMEDB_INFO_DIR           = self.ADDON_CODE_DIR.pjoin('GameDBInfo', isdir = True)
        self.GAMEDB_JSON_BASE_NOEXT    = 'GameDB_info'
        self.LAUNCHBOX_INFO_DIR        = self.ADDON_CODE_DIR.pjoin('LaunchBox', isdir = True)
        self.LAUNCHBOX_JSON_BASE_NOEXT = 'LaunchBox_info'

        # --- Artwork and NFO for Categories and Launchers ---
        self.CATEGORIES_ASSET_DIR      = self.ADDON_DATA_DIR.pjoin('asset-categories', isdir = True)
        self.COLLECTIONS_ASSET_DIR     = self.ADDON_DATA_DIR.pjoin('asset-collections', isdir = True)
        self.LAUNCHERS_ASSET_DIR       = self.ADDON_DATA_DIR.pjoin('asset-launchers', isdir = True)
        self.FAVOURITES_ASSET_DIR      = self.ADDON_DATA_DIR.pjoin('asset-favourites', isdir = True)
        self.VIRTUAL_CAT_TITLE_DIR     = self.ADDON_DATA_DIR.pjoin('db_title', isdir = True)
        self.VIRTUAL_CAT_YEARS_DIR     = self.ADDON_DATA_DIR.pjoin('db_year', isdir = True)
        self.VIRTUAL_CAT_GENRE_DIR     = self.ADDON_DATA_DIR.pjoin('db_genre', isdir = True)
        self.VIRTUAL_CAT_DEVELOPER_DIR = self.ADDON_DATA_DIR.pjoin('db_developer', isdir = True)
        self.VIRTUAL_CAT_NPLAYERS_DIR  = self.ADDON_DATA_DIR.pjoin('db_nplayer', isdir = True)
        self.VIRTUAL_CAT_ESRB_DIR      = self.ADDON_DATA_DIR.pjoin('db_esrb', isdir = True)
        self.VIRTUAL_CAT_RATING_DIR    = self.ADDON_DATA_DIR.pjoin('db_rating', isdir = True)
        self.VIRTUAL_CAT_CATEGORY_DIR  = self.ADDON_DATA_DIR.pjoin('db_category', isdir = True)
        self.ROMS_DIR                  = self.ADDON_DATA_DIR.pjoin('db_ROMs', isdir = True)
        self.COLLECTIONS_DIR           = self.ADDON_DATA_DIR.pjoin('db_Collections', isdir = True)
        self.REPORTS_DIR               = self.ADDON_DATA_DIR.pjoin('reports', isdir = True)

# --- Global variables ---
g_PATHS = AEL_Paths()
g_settings = {}
g_base_url = ''
g_addon_handle = 0
g_content_type = ''
g_time_str = unicode(datetime.datetime.now())

# --- Global objects ---
g_ScraperFactory = None
g_ROMScannerFactory = None
g_ExecutorFactory = None
g_ObjectRepository = None
g_ObjectFactory = None

# -------------------------------------------------------------------------------------------------
# Make AEL to run only 1 single instance
# See http://forum.kodi.tv/showthread.php?tid=310697
# -------------------------------------------------------------------------------------------------
g_monitor = xbmc.Monitor()
g_main_window = xbmcgui.Window(10000)
AEL_LOCK_PROPNAME = 'AEL_instance_lock'
AEL_LOCK_VALUE    = 'True'
class SingleInstance:
    def __enter__(self):
        # --- If property is True then another instance of AEL is running ---
        if g_main_window.getProperty(AEL_LOCK_PROPNAME) == AEL_LOCK_VALUE:
            log_warning('SingleInstance::__enter__() Lock in use. Aborting AEL execution')
            # >> Apparently this message pulls the focus out of the launcher app. Disable it.
            # >> Has not effect. Kodi steals the focus from the launched app even if not message.
            kodi_dialog_OK('Another instance of AEL is running! Wait until the scraper finishes '
                           'or close the launched application before launching a new one and try '
                           'again.')
            raise SystemExit
        if g_monitor.abortRequested(): 
            log_info('g_monitor.abortRequested() is True. Exiting plugin ...')
            raise SystemExit

        # --- Acquire lock for this instance ---
        log_debug('SingleInstance::__enter__() Lock not in use. Setting lock')
        g_main_window.setProperty(AEL_LOCK_PROPNAME, AEL_LOCK_VALUE)
        return True

    def __exit__(self, type, value, traceback):
        # --- Print information about exception if any ---
        # >> If type == value == tracebak == None no exception happened
        if type:
            log_error('SingleInstance::__exit__() Unhandled excepcion in protected code')

        # --- Release lock even if an exception happened ---
        log_debug('SingleInstance::__exit__() Releasing lock')
        g_main_window.setProperty(AEL_LOCK_PROPNAME, '')

# ---------------------------------------------------------------------------------------------
# This is the plugin entry point.
# ---------------------------------------------------------------------------------------------
def run_plugin(addon_argv):
    global g_base_url
    global g_addon_handle
    global g_content_type

    # --- Initialise log system ---
    # >> Force DEBUG log level for development.
    # >> Place it before settings loading so settings can be dumped during debugging.
    # set_log_level(LOG_DEBUG)

    # --- Fill in settings dictionary using __addon_obj__.getSetting() ---
    m_get_settings()
    set_log_level(g_settings['log_level'])

    # --- Some debug stuff for development ---
    log_debug('------------ Called Advanced Emulator Launcher run_plugin(addon_argv) ------------')
    log_debug('sys.platform   "{0}"'.format(sys.platform))
    # log_debug('WindowId       "{0}"'.format(xbmcgui.getCurrentWindowId()))
    # log_debug('WindowName     "{0}"'.format(xbmc.getInfoLabel('Window.Property(xmlfile)')))
    log_debug('Python version "' + sys.version.replace('\n', '') + '"')
    # log_debug('__a_name__     "{0}"'.format(__addon_name__))
    # log_debug('__a_id__       "{0}"'.format(__addon_id__))
    log_debug('__a_version__  "{0}"'.format(__addon_version__))
    # log_debug('__a_author__   "{0}"'.format(__addon_author__))
    # log_debug('__a_profile__  "{0}"'.format(__addon_profile__))
    # log_debug('__a_type__     "{0}"'.format(__addon_type__))
    for i in range(len(sys.argv)): log_debug('sys.argv[{0}] "{1}"'.format(i, sys.argv[i]))
    # log_debug('ADDON_DATA_DIR OP "{0}"'.format(ADDON_DATA_DIR.getOriginalPath()))
    # log_debug('ADDON_DATA_DIR  P "{0}"'.format(ADDON_DATA_DIR.getPath()))
    # log_debug('g_PATHS.ADDON_CODE_DIR OP "{0}"'.format(g_PATHS.ADDON_CODE_DIR.getOriginalPath()))
    # log_debug('g_PATHS.ADDON_CODE_DIR  P "{0}"'.format(g_PATHS.ADDON_CODE_DIR.getPath()))

    # --- Get DEBUG information for the log --
    if g_settings['log_level'] == LOG_DEBUG:
        # >> JSON-RPC queries <<
        json_rpc_start = time.time()
        getprops_dic = kodi_jsonrpc_query('Application.GetProperties', '{ "properties" : ["name", "version"] }')
        getskin_dic  = kodi_jsonrpc_query('Settings.GetSettingValue',  '{ "setting" : "lookandfeel.skin" }')
        json_rpc_end = time.time()
        # log_debug('JSON RPC time {0:.3f} ms'.format((json_rpc_end - json_rpc_start) * 1000))

        # >> Parse returned JSON and nice print <<
        r_name     = getprops_dic['name']
        r_major    = getprops_dic['version']['major']
        r_minor    = getprops_dic['version']['minor']
        r_revision = getprops_dic['version']['revision']
        r_tag      = getprops_dic['version']['tag']
        log_debug('Kodi version "{0}" "{1}" "{2}" "{3}" "{4}"'.format(r_name, r_major, r_minor, r_revision, r_tag))
        log_debug('Kodi skin    "{0}"'.format(getskin_dic['value']))

    # --- Addon data paths creation ---
    if not g_PATHS.ADDON_DATA_DIR.exists():            g_PATHS.ADDON_DATA_DIR.makedirs()
    if not g_PATHS.CATEGORIES_ASSET_DIR.exists():      g_PATHS.CATEGORIES_ASSET_DIR.makedirs()
    if not g_PATHS.COLLECTIONS_ASSET_DIR.exists():     g_PATHS.COLLECTIONS_ASSET_DIR.makedirs()
    if not g_PATHS.LAUNCHERS_ASSET_DIR.exists():       g_PATHS.LAUNCHERS_ASSET_DIR.makedirs()
    if not g_PATHS.FAVOURITES_ASSET_DIR.exists():      g_PATHS.FAVOURITES_ASSET_DIR.makedirs()
    if not g_PATHS.VIRTUAL_CAT_TITLE_DIR.exists():     g_PATHS.VIRTUAL_CAT_TITLE_DIR.makedirs()
    if not g_PATHS.VIRTUAL_CAT_YEARS_DIR.exists():     g_PATHS.VIRTUAL_CAT_YEARS_DIR.makedirs()
    if not g_PATHS.VIRTUAL_CAT_GENRE_DIR.exists():     g_PATHS.VIRTUAL_CAT_GENRE_DIR.makedirs()
    if not g_PATHS.VIRTUAL_CAT_DEVELOPER_DIR.exists(): g_PATHS.VIRTUAL_CAT_DEVELOPER_DIR.makedirs()
    if not g_PATHS.VIRTUAL_CAT_NPLAYERS_DIR.exists():  g_PATHS.VIRTUAL_CAT_NPLAYERS_DIR.makedirs()
    if not g_PATHS.VIRTUAL_CAT_ESRB_DIR.exists():      g_PATHS.VIRTUAL_CAT_ESRB_DIR.makedirs()
    if not g_PATHS.VIRTUAL_CAT_RATING_DIR.exists():    g_PATHS.VIRTUAL_CAT_RATING_DIR.makedirs()
    if not g_PATHS.VIRTUAL_CAT_CATEGORY_DIR.exists():  g_PATHS.VIRTUAL_CAT_CATEGORY_DIR.makedirs()
    if not g_PATHS.ROMS_DIR.exists():                  g_PATHS.ROMS_DIR.makedirs()
    if not g_PATHS.COLLECTIONS_DIR.exists():           g_PATHS.COLLECTIONS_DIR.makedirs()
    if not g_PATHS.REPORTS_DIR.exists():               g_PATHS.REPORTS_DIR.makedirs()

    # --- Handle migrations ---
    current_version = LooseVersion(__addon_version__)
    str_version = g_settings['migrated_version']
    if not str_version or str_version == '': str_version = '0.0.0'
    try:
        last_migrated_to_version = LooseVersion(str_version)
    except:
        last_migrated_to_version = LooseVersion('0.0.0')
    log_debug('current_version           {0}'.format(current_version))
    log_debug('str_version               {0}'.format(str_version))
    log_debug('last_migrated_to_version  {0}'.format(last_migrated_to_version))

    # WARNING Right now concentrate on stabilising AEL code. Once AEL works well again then
    #         think about the migration from 0.9.7 to 0.10.0.
    # if current_version > last_migrated_to_version:
    #     log_info('Execute migrations')
    #     m_execute_migrations(last_migrated_to_version)

    # --- Process URL ---
    g_base_url = addon_argv[0]
    g_addon_handle = int(addon_argv[1])
    args = urlparse.parse_qs(addon_argv[2][1:])
    # log_debug('args = {0}'.format(args))
    # >> Interestingly, if plugin is called as type executable/program then content_type is empty.
    # >> However, if plugin is called as type video then Kodi adds the following
    # >> even for the first call: 'content_type': ['video']
    g_content_type = args['content_type'] if 'content_type' in args else None
    # log_debug('content_type = {0}'.format(g_content_type))

    # --- Addon first-time initialisation ---
    # When the addon is installed and the file categories.xml does not exist, just
    # create an empty one with a default launcher.
    # NOTE Not needed anymore. Skins using shortcuts and/or widgets will call AEL concurrently
    #      and AEL should return an empty list with no GUI warnings or dialogs.

    # --- Bootstrap object instances --- 
    m_bootstrap_instances()

    # --- Get addon command ---
    command = args['com'][0] if 'com' in args else 'SHOW_ADDON_ROOT'
    log_debug('run_plugin() Processing command = "{0}"'.format(command))

    # --- Commands that do not modify the databases are allowed to run concurrently ---
    if command == 'SHOW_ADDON_ROOT' or \
       command == 'SHOW_VCATEGORIES_ROOT' or \
       command == 'SHOW_AEL_OFFLINE_LAUNCHERS_ROOT' or \
       command == 'SHOW_LB_OFFLINE_LAUNCHERS_ROOT' or \
       command == 'SHOW_FAVOURITES' or \
       command == 'SHOW_VIRTUAL_CATEGORY' or \
       command == 'SHOW_RECENTLY_PLAYED' or \
       command == 'SHOW_MOST_PLAYED' or \
       command == 'SHOW_UTILITIES_VLAUNCHERS' or \
       command == 'SHOW_GLOBALREPORTS_VLAUNCHERS' or \
       command == 'SHOW_COLLECTIONS' or \
       command == 'SHOW_COLLECTION_ROMS' or \
       command == 'SHOW_LAUNCHERS' or \
       command == 'SHOW_ROMS' or \
       command == 'SHOW_VLAUNCHER_ROMS' or \
       command == 'SHOW_AEL_SCRAPER_ROMS' or \
       command == 'SHOW_LB_SCRAPER_ROMS' or \
       command == 'EXEC_SHOW_CLONE_ROMS' or \
       command == 'SHOW_CLONE_ROMS' or \
       command == 'SHOW_ALL_CATEGORIES' or \
       command == 'SHOW_ALL_LAUNCHERS' or \
       command == 'SHOW_ALL_ROMS' or \
       command == 'BUILD_GAMES_MENU':
        m_run_concurrent(command, args)
    # --- Rest of commants are only allowed to run on a single instance ---
    # >> This is very important to avoid file corruption, happening when two instances of
    # >> AEL write to the same file at the same time.
    else:
        with SingleInstance():
            m_run_protected(command, args)
    log_debug('Advanced Emulator Launcher run_plugin() exit')

#
# Bootstrap factory object instances.
#
def m_bootstrap_instances():
    # >> Grant write access to global variables
    global g_ScraperFactory
    global g_ROMScannerFactory
    global g_ExecutorFactory
    global g_ObjectRepository
    global g_ObjectFactory

    # --- Utility objects ---
    g_ScraperFactory = ScraperFactory(g_PATHS, g_settings)
    g_ROMScannerFactory = RomScannersFactory(g_PATHS, g_settings)
    g_ExecutorFactory = ExecutorFactory(g_PATHS, g_settings)

    # --- Creates any type of AEL object: Category, Launcher, Collection, ROM ---
    # AELObjectFactory creates empty objects not linked to the database or objects linked
    # to the database.
    g_ObjectRepository = ObjectRepository(g_PATHS, g_settings)
    g_ObjectFactory = AELObjectFactory(g_PATHS, g_settings, g_ObjectRepository, g_ExecutorFactory)

#
# This function may run concurrently
#
def m_run_concurrent(command, args):
    log_debug('Advanced Emulator Launcher run_concurrent() BEGIN')

    # --- Name says it all ---
    if command == 'SHOW_ADDON_ROOT':
        m_command_render_root()

    # --- Render launchers stuff ---
    elif command == 'SHOW_VCATEGORIES_ROOT':
        m_gui_render_Browse_by_vlaunchers()
    elif command == 'SHOW_AEL_OFFLINE_LAUNCHERS_ROOT':
        m_gui_render_AEL_scraper_vlaunchers()
    elif command == 'SHOW_LB_OFFLINE_LAUNCHERS_ROOT':
        m_gui_render_LB_scraper_vlaunchers()
    elif command == 'SHOW_VIRTUAL_CATEGORY':
        m_command_render_virtual_category(args['catID'][0])
    elif command == 'SHOW_RECENTLY_PLAYED':
        m_command_render_recently_played()
    elif command == 'SHOW_MOST_PLAYED':
        m_command_render_most_played()

    elif command == 'SHOW_UTILITIES_VLAUNCHERS':     m_gui_render_Utilities_vlaunchers()
    elif command == 'SHOW_GLOBALREPORTS_VLAUNCHERS': m_gui_render_GlobalReports_vlaunchers()

    elif command == 'SHOW_COLLECTIONS':
        m_command_render_Collections()
    elif command == 'SHOW_LAUNCHERS':
        m_command_render_launchers(args['catID'][0])

    # --- Show ROMs in launcher/virtual launcher ---
    elif command == 'SHOW_ROMS':
        m_command_render_roms(args['catID'][0], args['launID'][0])
    # >> Auxiliar command to render clone ROM list from context menu in 1G1R mode.
    elif command == 'EXEC_SHOW_CLONE_ROMS':
        url = m_misc_url('SHOW_CLONE_ROMS', args['catID'][0], args['launID'][0], args['romID'][0])
        xbmc.executebuiltin('Container.Update({0})'.format(url))
    elif command == 'SHOW_CLONE_ROMS':
        m_command_render_clone_roms(args['catID'][0], args['launID'][0], args['romID'][0])

    elif command == 'SHOW_FAVOURITES':
        m_command_render_favourite_roms()

    elif command == 'SHOW_VLAUNCHER_ROMS':
        m_command_render_Browse_by_roms(args['catID'][0], args['launID'][0])
    elif command == 'SHOW_COLLECTION_ROMS':
        m_command_render_Collection_roms(args['catID'][0], args['launID'][0])
    elif command == 'SHOW_AEL_SCRAPER_ROMS':
        m_command_render_AEL_scraper_roms(args['catID'][0])
    elif command == 'SHOW_LB_SCRAPER_ROMS':
        m_command_render_LB_scraper_roms(args['catID'][0])

    # --- Skin commands ---
    # >> This commands render Categories/Launcher/ROMs and are used by skins to build shortcuts.
    # >> Do not render virtual launchers.
    elif command == 'SHOW_ALL_CATEGORIES': m_command_render_all_categories()
    elif command == 'SHOW_ALL_LAUNCHERS':  m_command_render_all_launchers()
    elif command == 'SHOW_ALL_ROMS':       m_command_render_all_ROMs()

    # >> Command to build/fill the menu with categories or launcher using skinshortcuts
    elif command == 'BUILD_GAMES_MENU': m_command_buildMenu()

    # >> Unknown command
    else:
        kodi_dialog_OK('Unknown command {0}'.format(args['com'][0]) )
    log_debug('Advanced Emulator Launcher run_concurrent() END')

#
# This function is guaranteed to run with no concurrency.
#
def m_run_protected(command, args):
    log_debug('Advanced Emulator Launcher m_run_protected() BEGIN')

    # --- Category management ---
    if command == 'ADD_CATEGORY':
        m_command_add_new_category()
    elif command == 'EDIT_CATEGORY':
        m_command_edit_category(args['catID'][0])

    # --- Launcher management ---
    elif command == 'ADD_LAUNCHER':
        m_command_add_new_launcher(args['catID'][0])
    elif command == 'ADD_LAUNCHER_ROOT':
        m_command_add_new_launcher(VCATEGORY_ADDONROOT_ID)
    elif command == 'EDIT_LAUNCHER':
        m_command_edit_launcher(args['catID'][0], args['launID'][0])

    # --- ROM management ---
    # >> Add/Edit/Delete ROMs in launcher, Favourites or ROM Collections <<
    elif command == 'ADD_ROMS':
        m_command_add_roms(args['launID'][0])
    elif command == 'EDIT_ROM':
        m_command_edit_rom(args['catID'][0], args['launID'][0], args['romID'][0])

    # --- Launch ROM or standalone launcher ---
    elif command == 'LAUNCH_ROM':
        m_command_run_rom(args['catID'][0], args['launID'][0], args['romID'][0])
    elif command == 'LAUNCH_STANDALONE':
        m_command_run_standalone_launcher(args['catID'][0], args['launID'][0])

    # --- Favourite/ROM Collection management ---
    elif command == 'ADD_TO_FAV':
        m_command_add_to_favourites(args['catID'][0], args['launID'][0], args['romID'][0])
    elif command == 'ADD_TO_COLLECTION':
        m_command_add_ROM_to_collection(args['catID'][0], args['launID'][0], args['romID'][0])
    elif command == 'ADD_COLLECTION':
        m_command_add_collection()
    elif command == 'EDIT_COLLECTION':
        m_command_edit_collection(args['catID'][0], args['launID'][0])
    elif command == 'DELETE_COLLECTION':
        m_command_delete_collection(args['catID'][0], args['launID'][0])
    elif command == 'IMPORT_COLLECTION':
        m_command_import_collection()
    elif command == 'EXPORT_COLLECTION':
        m_command_export_collection(args['catID'][0], args['launID'][0])
    elif command == 'MANAGE_FAV':
        m_command_manage_favourites(args['catID'][0], args['launID'][0], args['romID'][0])

    # --- Searches ---
    # This command is issued when user clicks on "Search" on the context menu of a launcher
    # in the launchers view, or context menu inside a launcher. User is asked to enter the
    # search string and the field to search (name, category, etc.). Then, EXEC_SEARCH_LAUNCHER
    # command is called.
    elif command == 'SEARCH_LAUNCHER':
        m_command_search_launcher(args['catID'][0], args['launID'][0])
    elif command == 'EXECUTE_SEARCH_LAUNCHER':
        # >> Deal with empty search strings
        if 'search_string' not in args: args['search_string'] = [ '' ]
        m_command_execute_search_launcher(args['catID'][0], args['launID'][0],
                                          args['search_type'][0], args['search_string'][0])

    # >> Shows info about categories/launchers/ROMs and reports from dynamic Context menu.
    elif command == 'VIEW':
        launID = args['launID'][0] if 'launID' in args else '' # >> Optional
        romID  = args['romID'][0]  if 'romID'  in args else '' # >> Optional
        m_command_view_menu(args['catID'][0], launID, romID)

    # Text dialog to show Offline Scraper ROM database entry.
    elif command == 'VIEW_OS_ROM':
        m_command_view_offline_scraper_rom(args['catID'][0], args['launID'][0], args['romID'][0])

    # >> Update virtual categories databases
    elif command == 'UPDATE_VIRTUAL_CATEGORY': m_command_update_Browse_By_db(args['catID'][0])
    elif command == 'UPDATE_ALL_VCATEGORIES':  m_command_update_Browse_By_db_all()

    # >> Commands called from AEL addon settings only
    elif command == 'EXECUTE_IMPORT_LAUNCHERS':    m_command_exec_import_launchers()
    elif command == 'EXECUTE_EXPORT_LAUNCHERS':    m_command_exec_export_launchers()
    elif command == 'EXECUTE_IMPORT_AL_LAUNCHERS': m_command_exec_import_legacy_AL()

    # >> Commands called from addon settings window and Utilities menu.
    elif command == 'EXECUTE_CHECK_DATABASES': m_command_exec_check_database()

    # >> Commands called from Utilities menu.
    elif command == 'EXECUTE_CHECK_LAUNCHERS':         m_command_exec_check_launchers()
    elif command == 'EXECUTE_CHECK_MISSING_ASSETS':    m_command_exec_check_missing_assets()
    elif command == 'EXECUTE_CHECK_RETROARCH_CORES':   m_command_exec_check_Retroarch_cores()
    elif command == 'EXECUTE_CHECK_RETROARCH_BIOS':    m_command_exec_check_Retroarch_BIOS()
    elif command == 'EXECUTE_CHECK_RETROPLAYER_CORES': m_command_exec_check_Retroplayer_cores()
    elif command == 'EXECUTE_CHECK_RETROPLAYER_BIOS':  m_command_exec_check_Retroplayer_BIOS()

    # >> Commands called from Global Reports menu.
    elif command == 'EXECUTE_GLOBAL_ROM_STATS':   m_command_exec_global_rom_stats()
    elif command == 'EXECUTE_GLOBAL_AUDIT_STATS': m_command_exec_global_audit_stats()

    # >> Unknown command
    else:
        kodi_dialog_OK('Unknown command {0}'.format(args['com'][0]) )
    log_debug('Advanced Emulator Launcher run_protected() END')

#
# Get Addon Settings
#
def m_get_settings():
    global g_settings
    o = __addon__

    # --- ROM Scanner settings tab ---
    g_settings['scan_recursive']           = True if o.getSetting('scan_recursive') == 'true' else False
    g_settings['scan_ignore_bios']         = True if o.getSetting('scan_ignore_bios') == 'true' else False
    g_settings['scan_update_NFO_files']    = True if o.getSetting('scan_update_NFO_files') == 'true' else False
    g_settings['scan_ignore_scrap_title']  = True if o.getSetting('scan_ignore_scrap_title') == 'true' else False
    g_settings['scan_clean_tags']          = True if o.getSetting('scan_clean_tags') == 'true' else False
    g_settings['scan_metadata_policy']     = int(o.getSetting('scan_metadata_policy'))
    g_settings['scan_asset_policy']        = int(o.getSetting('scan_asset_policy'))
    g_settings['metadata_scraper_mode']    = int(o.getSetting('metadata_scraper_mode'))
    g_settings['asset_scraper_mode']       = int(o.getSetting('asset_scraper_mode'))
    g_settings['steam-api-key']            = o.getSetting('steam-api-key')

    # --- ROM scraping tab ---
    g_settings['scraper_metadata']       = int(o.getSetting('scraper_metadata'))
    g_settings['scraper_metadata_MAME']  = int(o.getSetting('scraper_metadata_MAME'))

    g_settings['scraper_title']          = int(o.getSetting('scraper_title'))
    g_settings['scraper_snap']           = int(o.getSetting('scraper_snap'))
    g_settings['scraper_boxfront']       = int(o.getSetting('scraper_boxfront'))
    g_settings['scraper_boxback']        = int(o.getSetting('scraper_boxback'))
    g_settings['scraper_cart']           = int(o.getSetting('scraper_cart'))
    g_settings['scraper_fanart']         = int(o.getSetting('scraper_fanart'))
    g_settings['scraper_banner']         = int(o.getSetting('scraper_banner'))
    g_settings['scraper_clearlogo']      = int(o.getSetting('scraper_clearlogo'))

    g_settings['scraper_title_MAME']     = int(o.getSetting('scraper_title_MAME'))
    g_settings['scraper_snap_MAME']      = int(o.getSetting('scraper_snap_MAME'))
    g_settings['scraper_cabinet_MAME']   = int(o.getSetting('scraper_cabinet_MAME'))
    g_settings['scraper_cpanel_MAME']    = int(o.getSetting('scraper_cpanel_MAME'))
    g_settings['scraper_pcb_MAME']       = int(o.getSetting('scraper_pcb_MAME'))
    g_settings['scraper_fanart_MAME']    = int(o.getSetting('scraper_fanart_MAME'))
    g_settings['scraper_marquee_MAME']   = int(o.getSetting('scraper_marquee_MAME'))
    g_settings['scraper_clearlogo_MAME'] = int(o.getSetting('scraper_clearlogo_MAME'))
    g_settings['scraper_flyer_MAME']     = int(o.getSetting('scraper_flyer_MAME'))

    # todo: change to use actual key from settings
    g_settings['thegamesdb_apikey']      = '<ACTUAL_API_KEY>'
    g_settings['mobygames_apikey']       = '<ACTUAL_API_KEY>'

    # --- ROM audit ---
    g_settings['audit_unknown_roms']         = int(o.getSetting('audit_unknown_roms'))
    # self.settings['audit_create_pclone_groups'] = True if o.getSetting('audit_create_pclone_groups') == 'true' else False
    g_settings['audit_pclone_assets']        = True if o.getSetting('audit_pclone_assets') == 'true' else False
    # self.settings['audit_1G1R_main_region']     = int(o.getSetting('audit_1G1R_main_region'))
    # self.settings['audit_1G1R_second_region']   = int(o.getSetting('audit_1G1R_second_region'))

    # --- Scrapers tab ---
    # g_settings['scraper_region']           = int(o.getSetting('scraper_region'))
    # g_settings['scraper_thumb_size']       = int(o.getSetting('scraper_thumb_size'))
    # g_settings['scraper_fanart_size']      = int(o.getSetting('scraper_fanart_size'))
    # g_settings['scraper_image_type']       = int(o.getSetting('scraper_image_type'))
    # g_settings['scraper_fanart_order']     = int(o.getSetting('scraper_fanart_order'))

    # --- Display tab ---
    g_settings['display_category_mode']    = int(o.getSetting('display_category_mode'))
    g_settings['display_launcher_notify']  = True if o.getSetting('display_launcher_notify') == 'true' else False
    g_settings['display_hide_finished']    = True if o.getSetting('display_hide_finished') == 'true' else False
    g_settings['display_launcher_roms']    = True if o.getSetting('display_launcher_roms') == 'true' else False

    g_settings['display_rom_in_fav']       = True if o.getSetting('display_rom_in_fav') == 'true' else False
    g_settings['display_nointro_stat']     = True if o.getSetting('display_nointro_stat') == 'true' else False
    g_settings['display_fav_status']       = True if o.getSetting('display_fav_status') == 'true' else False

    g_settings['display_hide_favs']        = True if o.getSetting('display_hide_favs') == 'true' else False
    g_settings['display_hide_collections'] = True if o.getSetting('display_hide_collections') == 'true' else False
    g_settings['display_hide_vlaunchers']  = True if o.getSetting('display_hide_vlaunchers') == 'true' else False
    g_settings['display_hide_AEL_scraper'] = True if o.getSetting('display_hide_AEL_scraper') == 'true' else False
    g_settings['display_hide_LB_scraper']  = True if o.getSetting('display_hide_LB_scraper') == 'true' else False
    g_settings['display_hide_recent']      = True if o.getSetting('display_hide_recent') == 'true' else False
    g_settings['display_hide_mostplayed']  = True if o.getSetting('display_hide_mostplayed') == 'true' else False

    # --- Paths tab ---
    g_settings['categories_asset_dir']     = o.getSetting('categories_asset_dir').decode('utf-8')
    g_settings['launchers_asset_dir']      = o.getSetting('launchers_asset_dir').decode('utf-8')
    g_settings['favourites_asset_dir']     = o.getSetting('favourites_asset_dir').decode('utf-8')
    g_settings['collections_asset_dir']    = o.getSetting('collections_asset_dir').decode('utf-8')

    # --- I/O tab ---
    g_settings['io_retroarch_only_mandatory'] = True if o.getSetting('io_retroarch_only_mandatory') == 'true' else False
    g_settings['io_retroarch_sys_dir']        = o.getSetting('io_retroarch_sys_dir').decode('utf-8')

    # --- Advanced tab ---
    g_settings['media_state_action']       = int(o.getSetting('media_state_action'))
    g_settings['delay_tempo']              = int(round(float(o.getSetting('delay_tempo'))))
    g_settings['suspend_audio_engine']     = True if o.getSetting('suspend_audio_engine') == 'true' else False
    # g_settings['suspend_joystick_engine']  = True if o.getSetting('suspend_joystick_engine') == 'true' else False
    g_settings['escape_romfile']           = True if o.getSetting('escape_romfile') == 'true' else False
    g_settings['lirc_state']               = True if o.getSetting('lirc_state') == 'true' else False
    g_settings['show_batch_window']        = True if o.getSetting('show_batch_window') == 'true' else False
    g_settings['windows_close_fds']        = True if o.getSetting('windows_close_fds') == 'true' else False
    g_settings['windows_cd_apppath']       = True if o.getSetting('windows_cd_apppath') == 'true' else False
    g_settings['log_level']                = int(o.getSetting('log_level'))
    g_settings['migrated_version']         = o.getSetting('migrated_version')

    # >> Check if user changed default artwork paths for categories/launchers.
    # >> If not, set sensible defaults.
    if g_settings['categories_asset_dir']  == '':
        g_settings['categories_asset_dir'] = g_PATHS.CATEGORIES_ASSET_DIR.getPath()
    if g_settings['collections_asset_dir'] == '':
        g_settings['collections_asset_dir'] = g_PATHS.COLLECTIONS_ASSET_DIR.getPath()
    if g_settings['launchers_asset_dir']   == '':
        g_settings['launchers_asset_dir'] = g_PATHS.LAUNCHERS_ASSET_DIR.getPath()
    if g_settings['favourites_asset_dir']  == '':
        g_settings['favourites_asset_dir'] = g_PATHS.FAVOURITES_ASSET_DIR.getPath()

    # --- Dump settings for DEBUG ---
    # log_debug('Settings dump BEGIN')
    # for key in sorted(g_settings):
    #     log_debug('{0} --> {1:10s} {2}'.format(key.rjust(21), str(g_settings[key]), type(g_settings[key])))
    # log_debug('Settings dump END')

#
# Set Sorting methods
#
def m_misc_set_default_sorting_method():
    # >> This must be called only if g_addon_handle > 0, otherwise Kodi will complain in the log.
    if g_addon_handle < 0: return
    xbmcplugin.addSortMethod(handle = g_addon_handle, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)

def m_misc_set_all_sorting_methods():
    # >> This must be called only if g_addon_handle > 0, otherwise Kodi will complain in the log.
    if g_addon_handle < 0: return
    xbmcplugin.addSortMethod(handle = g_addon_handle, sortMethod = xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
    xbmcplugin.addSortMethod(handle = g_addon_handle, sortMethod = xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(handle = g_addon_handle, sortMethod = xbmcplugin.SORT_METHOD_STUDIO)
    xbmcplugin.addSortMethod(handle = g_addon_handle, sortMethod = xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(handle = g_addon_handle, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)

#
# Set the AEL content type.
# It is a Window(10000) property used by skins to know if AEL is rendering
# a Window that has categories/launchers or ROMs.
#
def m_misc_set_AEL_Content(AEL_Content_Value):
    if AEL_Content_Value == AEL_CONTENT_VALUE_LAUNCHERS:
        log_debug('m_misc_set_AEL_Content() Setting Window({0}) '.format(AEL_CONTENT_WINDOW_ID) +
                  'property "{0}" = "{1}"'.format(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_LAUNCHERS))
        xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_LAUNCHERS)
    elif AEL_Content_Value == AEL_CONTENT_VALUE_ROMS:
        log_debug('m_misc_set_AEL_Content() Setting Window({0}) '.format(AEL_CONTENT_WINDOW_ID) +
                  'property "{0}" = "{1}"'.format(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROMS))
        xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROMS)
    elif AEL_Content_Value == AEL_CONTENT_VALUE_NONE:
        log_debug('m_misc_set_AEL_Content() Setting Window({0}) '.format(AEL_CONTENT_WINDOW_ID) +
                  'property "{0}" = "{1}"'.format(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_NONE))
        xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_NONE)
    else:
        log_error('m_misc_set_AEL_Content() Invalid AEL_Content_Value "{0}"'.format(AEL_Content_Value))

#
# When rendering ROMs set some Window(10000) properties so the skin knows:
#   1. Title of the launcher.
#   2. Icon of the launcher.
#   3. Clearlogo of the launcher.
#
def m_misc_set_AEL_Launcher_Content(launcher_dic):
    kodi_thumb     = 'DefaultFolder.png' if launcher_dic['rompath'] else 'DefaultProgram.png'
    icon_path      = asset_get_default_asset_Category(launcher_dic, 'default_icon', kodi_thumb)
    clearlogo_path = asset_get_default_asset_Category(launcher_dic, 'default_clearlogo')
    xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_LAUNCHER_NAME_LABEL, launcher_dic['m_name'])
    xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_LAUNCHER_ICON_LABEL, icon_path)
    xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_LAUNCHER_CLEARLOGO_LABEL, clearlogo_path)

def m_misc_clear_AEL_Launcher_Content():
    xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_LAUNCHER_NAME_LABEL, '')
    xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_LAUNCHER_ICON_LABEL, '')
    xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_LAUNCHER_CLEARLOGO_LABEL, '')

# -------------------------------------------------------------------------------------------------
# Context menu commands
# -------------------------------------------------------------------------------------------------
def m_command_add_new_category():
    log_debug('m_command_add_new_category() BEGIN')

    # --- Get new Category name ---
    keyboard = xbmc.Keyboard('', 'New Category Name')
    keyboard.doModal()
    if not keyboard.isConfirmed(): return

    # --- Save Category ---
    category = g_ObjectFactory.create_new(OBJ_CATEGORY)
    category.set_name(keyboard.getText().decode('utf-8'))
    category.save_to_disk()
    kodi_notify('Category {0} created'.format(category.get_name()))
    kodi_refresh_container()

def m_command_edit_category(category_id):
    log_debug('m_command_edit_category() category_id = {0}'.format(category_id))
    category = g_ObjectFactory.find_category(category_id)
    m_run_category_sub_command('EDIT_CATEGORY', category)
    kodi_refresh_container()

#
# Creates a new Launcher.
#
def m_command_add_new_launcher(category_id):
    category = g_ObjectFactory.find_category(category_id)
    if category_id == VCATEGORY_ADDONROOT_ID:
        log_info('Creating laucher in addon root.')
        selected_category_id = VCATEGORY_ADDONROOT_ID
    else:
        # --- Ask user if Launcher is created on the selected Category or on root menu ---
        options = collections.OrderedDict()
        options[category_id] = 'Create Launcher in "{0}" category'.format(category.get_name())
        options[VCATEGORY_ADDONROOT_ID] = 'Create Launcher in root window (no Category)'
        selected_category_id = KodiOrdDictionaryDialog().select('Choose Launcher Category', options)
        if selected_category_id is None: return

    # --- Show "Create New Launcher" dialog ---
    options = g_ObjectFactory.get_launcher_types_odict()
    launcher_type = KodiOrdDictionaryDialog().select('Create New Launcher', options)
    if launcher_type is None: return None
    log_info('m_command_add_new_launcher() New launcher (launcher_type = {0})'.format(launcher_type))
    launcher = g_ObjectFactory.create_new(launcher_type)

    # Executes the "Add new Launcher" wizard dialog. The wizard fills in the launcher.entity_data
    # dictionary with the required fields. After that, it creates the Launcher asset paths if
    # supported by the Launcher. If the user cancels the dialog then False is returned and the
    # launcher is not created.
    selected_category = g_ObjectFactory.find_category(selected_category_id)
    if not launcher.build(selected_category): return

    # Notify user, save categories.xml and update container contents so user sees the new
    # launcher inmmediately.
    launcher.save_to_disk()
    kodi_notify('Created {0} {1}'.format(launcher.get_object_name(), launcher.get_name()))
    kodi_refresh_container()

# Edits a Launcher.
def m_command_edit_launcher(category_id, launcher_id):
    log_debug('m_command_edit_launcher() category_id = {0}'.format(category_id))
    log_debug('m_command_edit_launcher() launcher_id = {0}'.format(launcher_id))
    launcher = g_ObjectFactory.find_launcher(category_id, launcher_id)
    m_run_launcher_sub_command('EDIT_LAUNCHER', launcher)
    kodi_refresh_container()

def m_command_add_rom_to_collection(categoryID, launcherID, romID):
    # >> ROMs in standard launcher
    launcher = g_LauncherRepository.find(launcherID)
    rom = launcher.select_rom(romID)

    if rom.is_virtual_rom():
        # >> ROM in Virtual Launcher
        actual_launcher_id = rom.get_launcher_id()
        launcher = g_LauncherRepository.find(actual_launcher_id)

    # --- Load Collection index ---
    collections = self.collection_repository.find_all()

    # --- If no collections so long and thanks for all the fish ---
    if not collections:
        kodi_dialog_OK('You have no Collections! Create a collection first before adding ROMs.')
        return

    # --- Ask user which Collection wants to add the ROM to ---
    dialog = DictionaryDialog()
    collection_options = OrderedDict()
    for collection in sorted(collections, key = lambda c : c.get_name()):
        collection_options[collection.get_id()] = collection.get_name()

    selected_id = dialog.select('Select the collection', collection_options)
    if selected_id is None: return
    
    # --- Load Collection ROMs ---
    collection = self.collection_repository.find(selected_id)

    log_info('Adding ROM to Collection')
    log_info('Collection {0}'.format(collection.get_name()))
    log_info('romID      {0}'.format(romID))
    log_info('ROM m_name {0}'.format(rom.get_name()))

    # >> Check if ROM already in this collection an warn user if so
    rom_already_in_collection = collection.has_rom(romID)

    if rom_already_in_collection:
        log_info('ROM already in collection')
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno('Advanced Emulator Launcher',
                           'ROM {0} is already on Collection {1}. Overwrite it?'.format(rom.get_name(), collection.get_name()))
        if not ret:
            log_verb('User does not want to overwrite. Exiting.')
            return
    # >> Confirm if rom should be added
    else:
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno('Advanced Emulator Launcher',
                           "ROM '{0}'. Add this ROM to Collection '{1}'?".format(rom.get_name(), collection.get_name()))
        if not ret:
            log_verb('User does not confirm addition. Exiting.')
            return

    # --- Add ROM to favourites ROMs and save to disk ---
    # >> Add ROM to the last position in the collection --> todo
    collection.save_rom(rom)
    kodi_refresh_container()
    kodi_notify('Added ROM to Collection "{0}"'.format(collection.get_name()))

#
# Adds a new ROM Collection.
# Collections assets are same as Categories.
#
def m_command_add_collection():
    log_debug('m_command_add_collection() BEGIN')

    # --- Get new Collection name ---
    keyboard = xbmc.Keyboard('', 'New ROM Collection name')
    keyboard.doModal()
    if not keyboard.isConfirmed(): return

    # --- Save Collection ---
    collection = g_LauncherFactory.create_new(LAUNCHER_COLLECTION)
    collection.set_name(keyboard.getText().decode('utf-8'))
    g_collectionRepository.save(collection)
    kodi_notify('Created ROM Collection {0}'.format(collection.get_name()))
    kodi_refresh_container()

#
# Edits a Collection
# categoryID is always "vcategory_collections"
#
def m_command_edit_collection(category_id, launcher_id):
    # NEW CODE STYLE
    collection = g_collectionRepository.find(launcher_id)
    m_run_collection_sub_command('EDIT_COLLECTION', collection)
    kodi_refresh_container()

#
# Add ROMS to launcher.
#
def m_command_add_roms(launcher_id):
    # NOTE Addition of single ROMs is deprecated. Only use the ROM scanner.
    #      Keep this old code for reference.
    # type = xbmcgui.Dialog().select(
    #     'Add/Update ROMs to Launcher', ['Scan for New ROMs', 'Manually Add ROM']
    # )
    # if type == 0:
    #     m_roms_import_roms(launcher_id)
    # elif type == 1:
    #     m_roms_add_new_rom(launcher_id)

    # --- Call the ROM scanner ---
    m_roms_import_roms(launcher_id)

#
# Note that categoryID = VCATEGORY_FAVOURITES_ID, launcherID = VLAUNCHER_FAVOURITES_ID if we are editing
# a ROM in Favourites.
#
def m_command_edit_rom(categoryID, launcherID, romID):
    if romID == UNKNOWN_ROMS_PARENT_ID:
        kodi_dialog_OK('You cannot edit this ROM!')
        return

    category = self.category_repository.find(categoryID)
    launcher = g_LauncherRepository.find(launcherID)

    # --- Load ROMs ---
    rom = launcher.select_rom(romID)

    # --- Show a dialog with ROM editing options ---
    rom_options = rom.get_edit_options(categoryID)
    dialog = DictionaryDialog()
    selected_option = dialog.select('Edit ROM {0}'.format(rom.get_name()), rom_options)
    
    if selected_option is None:
        log_debug('_command_edit_rom(): No selected option')
        kodi_refresh_container()
        return

    log_debug('_command_edit_rom(): Selected option = {0}'.format(selected_option))
    if type(selected_option) is tuple:
        selected_option = selected_option[0]
        log_debug('_command_edit_rom(): Selected option = {0}'.format(selected_option))

    self.run_sub_command(selected_option, None, launcher, rom)

#
# Adds ROM to favourites
#
def m_command_add_rom_to_favourites(categoryID, launcherID, romID):
    # >> ROMs in standard launcher
    launcher = g_LauncherRepository.find(launcherID)
    rom = launcher.select_rom(romID)

    # >> Sanity check
    if not rom:
        kodi_dialog_OK('Empty roms launcher in _command_add_to_favourites(). This is a bug, please report it.')
        return

    if launcher.get_launcher_type() == LAUNCHER_VIRTUAL:
        actual_launcher_id = rom.get_launcher_id()
        launcher = g_LauncherRepository.find(actual_launcher_id)

    # --- Load favourites ---
    favlauncher = g_LauncherRepository.find(VLAUNCHER_FAVOURITES_ID)
    roms_fav = favlauncher.get_roms()

    # --- DEBUG info ---
    log_verb('_command_add_to_favourites() Adding ROM to Favourites')
    log_verb('_command_add_to_favourites() romID  {0}'.format(romID))
    log_verb('_command_add_to_favourites() m_name {0}'.format(rom.get_name()))

    # Check if ROM already in favourites an warn user if so
    if favlauncher.has_rom(romID):
        log_verb('Already in favourites')
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno('Advanced Emulator Launcher',
                           'ROM {0} is already on AEL Favourites. Overwrite it?'.format(rom.get_name()))
        if not ret:
            log_verb('User does not want to overwrite. Exiting.')
            return
    # Confirm if rom should be added
    else:
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno('Advanced Emulator Launcher',
                            'ROM {0}. Add this ROM to AEL Favourites?'.format(rom.get_name()))
        if not ret:
            log_verb('User does not confirm addition. Exiting.')
            return
        
    # --- Add ROM to favourites ROMs and save to disk ---
    fav_rom = launcher.convert_rom_to_favourite(romID)
    favlauncher.save_rom(fav_rom)

    kodi_notify('ROM {0} added to Favourites'.format(fav_rom.get_name()))
    kodi_refresh_container()

#
# Manage Favourite/Collection ROMs as a whole.
#
def m_command_edit_rom_favourite(categoryID, launcherID, romID):
    # --- Load ROMs ---
    if categoryID == VCATEGORY_FAVOURITES_ID:
        log_debug('_command_manage_favourites() Managing Favourite ROMs')
        fav_launcher = g_LauncherRepository.find(VLAUNCHER_FAVOURITES_ID)
        roms_fav = fav_launcher.get_roms()
    elif categoryID == VCATEGORY_COLLECTIONS_ID:
        log_debug('_command_manage_favourites() Managing Collection ROMs')
        collection = self.collcollection_repository.find(launcherID)
        roms_fav = collection.get_roms()
    else:
        kodi_dialog_OK('_command_manage_favourites() should be called for Favourites or Collections. '
                       'This is a bug, please report it.')
        return

    # --- Show selection dialog ---
    dialog = xbmcgui.Dialog()
    if categoryID == VCATEGORY_FAVOURITES_ID:
        type = dialog.select('Manage Favourite ROMs',
                            ['Check Favourite ROMs',
                             'Repair Unlinked Launcher/Broken ROMs (by filename)',
                             'Repair Unlinked Launcher/Broken ROMs (by basename)',
                             'Repair Unlinked ROMs'])
    elif categoryID == VCATEGORY_COLLECTIONS_ID:
        type = dialog.select('Manage Collection ROMs',
                            ['Check Collection ROMs',
                             'Repair Unlinked Launcher/Broken ROMs (by filename)',
                             'Repair Unlinked Launcher/Broken ROMs (by basename)',
                             'Repair Unlinked ROMs'])

    # --- Check Favourite ROMs ---
    if type == 0:
        # >> This function opens a progress window to notify activity
        self._fav_check_favourites(roms_fav)

        # --- Print a report of issues found ---
        if categoryID == VCATEGORY_FAVOURITES_ID:
            kodi_dialog_OK('You have {0} ROMs in Favourites. '.format(self.num_fav_roms) +
                           '{0} Unlinked Launcher, '.format(self.num_fav_ulauncher) +
                           '{0} Unliked ROM and '.format(self.num_fav_urom) +
                           '{0} Broken.'.format(self.num_fav_broken))
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            kodi_dialog_OK('You have {0} ROMs in Collection "{1}". '.format(self.num_fav_roms, collection.get_name()) +
                           '{0} Unlinked Launcher, '.format(self.num_fav_ulauncher) +
                           '{0} Unliked ROM and '.format(self.num_fav_urom) +
                           '{0} are Broken.'.format(self.num_fav_broken))

    # --- Repair all Unlinked Launcher/Broken ROMs ---
    # type == 1 --> Repair by filename match
    # type == 2 --> Repair by ROM basename match
    elif type == 1 or type == 2:
        # 1) Traverse list of Favourites.
        # 2) For each favourite traverse all Launchers.
        # 3) Search for a ROM with same filename or same rom_base.
        #    If found, then replace romID in Favourites with romID of found ROM. Do not copy
        #    any metadata because user maybe customised the Favourite ROM.
        log_info('Repairing Unlinked Launcher/Broken ROMs (type = {0}) ...'.format(type))

        # --- Ask user about how to repair the Fav ROMs ---
        dialog = xbmcgui.Dialog()
        repair_mode = dialog.select('How to repair ROMs?',
                                    ['Relink and update launcher info',
                                     'Relink and update metadata',
                                     'Relink and update artwork',
                                     'Relink and update everything'])
        if repair_mode < 0: return
        log_verb('_command_manage_favourites() Repair mode {0}'.format(repair_mode))

        # >> Refreshing Favourite status will locate Unlinked/Broken ROMs.
        self._fav_check_favourites(roms_fav)

        # >> Repair Unlinked Launcher/Broken ROMs, Step 1
        # NOTE Dictionaries cannot change size when iterating them. Make a list of found ROMs
        #      and repair broken Favourites on a second pass
        pDialog = xbmcgui.DialogProgress()
        xbmc.sleep(100)
        num_progress_items = len(roms_fav)
        i = 0
        pDialog.create('Advanced Emulator Launcher', 'Repairing Unlinked Launcher/Broken ROMs ...')
        repair_rom_list = []
        num_broken_ROMs = 0
        for rom_fav in roms_fav:
            pDialog.update(i * 100 / num_progress_items)
            if pDialog.iscanceled():
                pDialog.close()
                kodi_dialog_OK('Repair cancelled. No changes has been done.')
                return
            i += 1

            # >> Only process Unlinked Launcher ROMs
            fav_status = rom_fav.get_favourite_status()
            if fav_status == 'OK': continue
            if fav_status == 'Unlinked ROM': continue

            fav_name = rom_fav.get_name()
            num_broken_ROMs += 1
            log_info('_command_manage_favourites() Repairing Fav ROM "{0}"'.format(fav_name))
            log_info('_command_manage_favourites() Fav ROM status "{0}"'.format(fav_status))

            # >> Traverse all launchers and find rom by filename or base name
            ROM_FN_FAV      = rom_fav.get_file()
            filename_found  = False
            parent_rom      = None

            launchers = g_LauncherRepository.find_all()
            for launcher in launchers:
                # >> Load launcher ROMs
                roms = launcher.get_roms()
                for rom in roms:
                    ROM_FN = rom.get_file()
                    if type == 1 and ROM_FN == ROM_FN_FAV:
                        log_info('_command_manage_favourites() Favourite {0} matched by filename!'.format(fav_name))
                        log_info('_command_manage_favourites() Launcher {0}'.format(launcher.get_id()))
                        log_info('_command_manage_favourites() ROM {0}'.format(rom.get_id()))
                    elif type == 2 and ROM_FN_FAV.getBase().lower() == ROM_FN.getBase().lower():
                        log_info('_command_manage_favourites() Favourite {0} matched by basename!'.format(fav_name))
                        log_info('_command_manage_favourites() Launcher {0}'.format(launcher.get_id()))
                        log_info('_command_manage_favourites() ROM {0}'.format(rom_id))
                    else:
                        continue
                    # >> Match found. Break all for loops inmediately.
                    filename_found      = True
                    new_fav_rom_ID      = rom.get_id()
                    new_fav_rom_laun_ID = launcher.get_id()
                    parent_rom          = rom
                    break
                if filename_found: 
                    break

            # >> Add ROM to the list of ROMs to be repaired.
            if filename_found:
                parent_launcher = g_LauncherRepository.find(new_fav_rom_laun_ID)

                rom_repair = {}
                rom_repair['old_fav_rom_ID']      = rom_fav_ID
                rom_repair['new_fav_rom_ID']      = new_fav_rom_ID
                rom_repair['new_fav_rom_laun_ID'] = new_fav_rom_laun_ID
                rom_repair['old_fav_rom']         = rom_fav
                rom_repair['parent_rom']          = parent_rom
                rom_repair['parent_launcher']     = parent_launcher.get_data()
                repair_rom_list.append(rom_repair)
            else:
                log_verb('_command_manage_favourites() ROM {0} filename not found in any launcher'.format(fav_name))
        log_info('_command_manage_favourites() Step 1 found {0} unlinked launcher/broken ROMs'.format(num_broken_ROMs))
        log_info('_command_manage_favourites() Step 1 found {0} ROMs to be repaired'.format(len(repair_rom_list)))
        pDialog.update(i * 100 / num_progress_items)
        pDialog.close()

        # >> Pass 2. Repair Favourites. Changes roms_fav dictionary.
        # >> Step 2 is very fast, so no progress dialog.
        num_repaired_ROMs = 0
        for rom_repair in repair_rom_list:
            old_fav_rom_ID      = rom_repair['old_fav_rom_ID']
            new_fav_rom_ID      = rom_repair['new_fav_rom_ID']
            new_fav_rom_laun_ID = rom_repair['new_fav_rom_laun_ID']
            old_fav_rom         = rom_repair['old_fav_rom']
            parent_rom          = rom_repair['parent_rom']
            parent_launcher     = rom_repair['parent_launcher']
            log_debug('_command_manage_favourites() Repairing ROM {0}'.format(old_fav_rom_ID))
            log_debug('_command_manage_favourites() Name          {0}'.format(old_fav_rom.get_name()))
            log_debug('_command_manage_favourites() New ROM       {0}'.format(new_fav_rom_ID))
            log_debug('_command_manage_favourites() New Launcher  {0}'.format(new_fav_rom_laun_ID))

            # >> Relink Favourite ROM. Removed old Favourite before inserting new one.
            new_fav_rom = fs_repair_Favourite_ROM(repair_mode, old_fav_rom, parent_rom, parent_launcher)
            roms_fav.remove(old_fav_rom)
            roms_fav.append(new_fav_rom)
            num_repaired_ROMs += 1
        log_debug('_command_manage_favourites() Repaired {0} ROMs'.format(num_repaired_ROMs))

        # >> Show info to user
        if type == 1:
            kodi_dialog_OK('Found {0} Unlinked Launcher/Broken ROMs. '.format(num_broken_ROMs) +
                           'Of those, {0} were repaired by filename match.'.format(num_repaired_ROMs))
        elif type == 2:
            kodi_dialog_OK('Found {0} Unlinked Launcher/Broken ROMs. '.format(num_broken_ROMs) +
                           'Of those, {0} were repaired by rombase match.'.format(num_repaired_ROMs))
        else:
            log_error('_command_manage_favourites() type = {0} unknown value!'.format(type))
            kodi_dialog_OK('Unknown type = {0}. This is a bug, please report it.'.format(type))
            return

    # --- Repair Unliked ROMs ---
    elif type == 3:
        # 1) Traverse list of Favourites.
        # 2) If romID not found in launcher, then search for a ROM with same basename.
        log_info('Repairing Repair Unliked ROMs (type = {0}) ...'.format(type))

        # --- Ask user about how to repair the Fav ROMs ---
        dialog = xbmcgui.Dialog()
        repair_mode = dialog.select('How to repair ROMs?',
                                    ['Relink and update launcher info',
                                     'Relink and update metadata',
                                     'Relink and update artwork',
                                     'Relink and update everything'])
        if repair_mode < 0: return
        log_verb('_command_manage_favourites() Repair mode {0}'.format(repair_mode))

        # >> Refreshing Favourite status will locate Unlinked ROMs.
        self._fav_check_favourites(roms_fav)

        # >> Repair Unlinked ROMs
        pDialog = xbmcgui.DialogProgress()
        num_progress_items = len(roms_fav)
        i = 0
        pDialog.create('Advanced Emulator Launcher', 'Repairing Unlinked Favourite ROMs...')
        repair_rom_list = []
        num_unlinked_ROMs = 0
        for rom_fav_ID in roms_fav:
            pDialog.update(i * 100 / num_progress_items)
            i += 1

            # >> Only process Unlinked ROMs
            rom_fav = roms_fav[rom_fav_ID]
            if rom_fav['fav_status'] != 'Unlinked ROM': continue
            num_unlinked_ROMs += 1
            fav_name = roms_fav[rom_fav_ID]['m_name']
            log_info('_command_manage_favourites() Repairing Fav ROM "{0}"'.format(fav_name))
            log_info('_command_manage_favourites() Fav ROM status "{0}"'.format(rom_fav['fav_status']))

            # >> Get ROMs of launcher
            launcher_id   = rom_fav['launcherID']
            launcher      = g_LauncherRepository.find(launcher_id)
            launcher_roms = fs_load_ROMs_JSON(ROMS_DIR, launcher.get_data())

            # >> Is there a ROM with same basename (including extension) as the Favourite ROM?
            filename_found = False
            ROM_FAV_FN = FileNameFactory.create(rom_fav['filename'])
            for rom_id in launcher_roms:
                ROM_FN = FileNameFactory.create(launcher_roms[rom_id]['filename'])
                if ROM_FAV_FN.getBase() == ROM_FN.getBase():
                    filename_found = True
                    new_fav_rom_ID = rom_id
                    break

            # >> Add ROM to the list of ROMs to be repaired. A dictionary cannot change when
            # >> it's being iterated! An Excepcion will be raised if so.
            if filename_found:
                log_debug('_command_manage_favourites() Relinked to {0}'.format(new_fav_rom_ID))
                rom_repair = {}
                rom_repair['old_fav_rom_ID']      = rom_fav_ID
                rom_repair['new_fav_rom_ID']      = new_fav_rom_ID
                rom_repair['new_fav_rom_laun_ID'] = launcher_id
                rom_repair['old_fav_rom']         = roms_fav[rom_fav_ID]
                rom_repair['parent_rom']          = launcher_roms[new_fav_rom_ID]
                rom_repair['parent_launcher']     = launcher.get_data()
                repair_rom_list.append(rom_repair)
            else:
                log_debug('_command_manage_favourites() Filename in launcher not found')
        pDialog.update(i * 100 / num_progress_items)
        pDialog.close()

        # >> Pass 2. Repair Favourites. Changes roms_fav dictionary.
        # >> Step 2 is very fast, so no progress dialog.
        num_repaired_ROMs = 0
        for rom_repair in repair_rom_list:
            old_fav_rom_ID      = rom_repair['old_fav_rom_ID']
            new_fav_rom_ID      = rom_repair['new_fav_rom_ID']
            new_fav_rom_laun_ID = rom_repair['new_fav_rom_laun_ID']
            old_fav_rom         = rom_repair['old_fav_rom']
            parent_rom          = rom_repair['parent_rom']
            parent_launcher     = rom_repair['parent_launcher']
            log_debug('_command_manage_favourites() Repairing ROM {0}'.format(old_fav_rom_ID))
            log_debug('_command_manage_favourites()  New ROM      {0}'.format(new_fav_rom_ID))
            log_debug('_command_manage_favourites()  New Launcher {0}'.format(new_fav_rom_laun_ID))

            # >> Relink Favourite ROM. Removed old Favourite before inserting new one.
            new_fav_rom = fs_repair_Favourite_ROM(repair_mode, old_fav_rom, parent_rom, parent_launcher)
            roms_fav.pop(old_fav_rom_ID)
            roms_fav[new_fav_rom['id']] = new_fav_rom
            num_repaired_ROMs += 1
        log_debug('_command_manage_favourites() Repaired {0} ROMs'.format(num_repaired_ROMs))

        # >> Show info to user
        kodi_dialog_OK('Found {0} Unlinked ROMs. '.format(num_unlinked_ROMs) +
                       'Of those, {0} were repaired.'.format(num_repaired_ROMs))

    # --- User cancelled dialog ---
    elif type < 0:
        return

    # --- If we reach this point save favourites and refresh container ---
    if categoryID == VCATEGORY_FAVOURITES_ID:
        fs_write_Favourites_JSON(FAV_JSON_FILE_PATH, roms_fav)
    elif categoryID == VCATEGORY_COLLECTIONS_ID:
        # >> Convert back the OrderedDict into a list and save Collection
        collection_rom_list = []
        for key in roms_fav:
            collection_rom_list.append(roms_fav[key])
        json_file = COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
        fs_write_Collection_ROMs_JSON(json_file, collection_rom_list)
    kodi_refresh_container()

#
# Renders the context menu "Edit Category"
# Note that category object could be a Standard Category or a ROM Collection.
# Recursive submenu logic is in this function.
# This function calls m_subcommand_* functions only for atomic operations (no submenus).
#
def m_run_category_sub_command(command, category):
    log_debug('m_run_category_sub_command({0}) BEGIN'.format(command))

    # --- Main menu command ---
    if command == 'EDIT_CATEGORY':
        options = category.get_main_edit_options()
        s = 'Select action for Category "{0}"'.format(category.get_name())
        selected_option = KodiOrdDictionaryDialog().select(s, options)
        if selected_option is None:
            # >> Exits context menu
            log_debug('m_run_category_sub_command(EDIT_CATEGORY) Selected None. Closing context menu')
        else:
            # >> Execute subcommand. May be atomic, maybe a submenu.
            # >> If submenu returns False is means the context menu must be closed now.
            log_debug('m_run_category_sub_command(EDIT_CATEGORY) Selected {0}'.format(selected_option))
            if m_run_category_sub_command(selected_option, category):
                m_run_category_sub_command('EDIT_CATEGORY', category)
            else:
                log_debug('m_run_category_sub_command(EDIT_CATEGORY) m_run_category_sub_command returned False')
                log_debug('m_run_category_sub_command(EDIT_CATEGORY) Closing context menu')

    # --- Submenu command ---
    elif command == 'EDIT_METADATA':
        options = category.get_metadata_edit_options()
        s = 'Edit Category "{0}" metadata'.format(category.get_name())
        selected_option = KodiOrdDictionaryDialog().select(s, options)
        if selected_option is None:
            # >> Return recursively to parent menu.
            log_debug('m_run_category_sub_command(EDIT_METADATA) Selected NONE')
        else:
            # >> Execute category edit metadata atomic subcommand.
            # >> Then, execute recursively this submenu again.
            # >> The parent menu dialog is instantiated again so it reflects the changes just edited.
            log_debug('m_run_category_sub_command(EDIT_METADATA) Selected {0}'.format(selected_option))
            m_run_category_sub_command(selected_option, category)
            m_run_category_sub_command('EDIT_METADATA', category)

    # --- Atomic commands ---
    # NOTE integrate subcommands using generic editing functions.
    elif command == 'EDIT_METADATA_TITLE':
        m_gui_edit_metadata_str(category, 'Title', category.get_name, category.set_name)

    elif command == 'EDIT_METADATA_RELEASEYEAR':
        m_gui_edit_metadata_str(category, 'Release Rear', category.get_releaseyear, category.set_releaseyear)

    elif command == 'EDIT_METADATA_GENRE':
        m_gui_edit_metadata_str(category, 'Genre', category.get_genre, category.set_genre)

    elif command == 'EDIT_METADATA_DEVELOPER':
        m_gui_edit_metadata_str(category, 'Developer', category.get_developer, category.set_developer)

    elif command == 'EDIT_METADATA_RATING':
        m_gui_edit_rating(category, category.get_rating, category.set_rating)

    elif command == 'EDIT_METADATA_PLOT':
        m_gui_edit_metadata_str(category, 'Plot', category.get_plot, category.set_plot)

    elif command == 'IMPORT_NFO_FILE_DEFAULT':
        m_subcommand_edit_category_nfo_import_default(category)

    elif command == 'IMPORT_NFO_FILE_BROWSE':
        m_subcommand_edit_category_nfo_import_browse(category)

    elif command == 'SAVE_NFO_FILE_DEFAULT':
        m_subcommand_edit_category_nfo_save_default(category)

    # --- Submenu command ---
    elif command == 'EDIT_ASSETS':
        m_gui_edit_object_assets(category)

    # --- Submenu command ---
    elif command == 'EDIT_DEFAULT_ASSETS':
        m_gui_edit_object_default_assets(category)

    # --- Atomic commands ---
    elif command == 'EDIT_CATEGORY_STATUS':
        category.change_finished_status()
        kodi_dialog_OK('Category "{0}" status is now {1}'.format(category.get_name(), category.get_finished_str()))
        g_MainRepository.save_category(category)

    elif command == 'EXPORT_CATEGORY_XML':
        m_subcommand_export_category_xml(category)

    # Deleting a Category must exit the context menu!
    # If the deletion was sucessful the Category does not exit any more.
    elif command == 'DELETE_CATEGORY':
        if m_subcommand_delete_category(category): return False

    else:
        log_warning('m_run_category_sub_command() Unsupported command "{0}"'.format(command))
        kodi_dialog_OK('m_run_category_sub_command() Unknown command {0}. '.format(command) +
                       'Please report this bug.')

    # Returns True if the parent menu must be shown again.
    # Return False if context menu must be closed.
    log_debug('m_run_category_sub_command({0}) ENDS'.format(command))
    return True

def m_run_launcher_sub_command(command, launcher):
    log_debug('m_run_launcher_sub_command({0}) BEGIN'.format(command))

    # --- Main menu command ---
    if command == 'EDIT_LAUNCHER':
        category = g_ObjectFactory.find_category(launcher.get_category_id())
        options = launcher.get_main_edit_options(category)
        s = 'Select action for Launcher "{0}"'.format(launcher.get_name())
        selected_option = KodiOrdDictionaryDialog().select(s, options)
        if selected_option is None:
            # >> Exits context menu
            log_debug('m_run_launcher_sub_command(EDIT_LAUNCHER) Selected None. Closing context menu')
        else:
            # >> Execute subcommand. May be atomic, maybe a submenu.
            # >> If submenu returns False is means the context menu must be closed now.
            log_debug('m_run_launcher_sub_command(EDIT_LAUNCHER) Selected {0}'.format(selected_option))
            if m_run_launcher_sub_command(selected_option, launcher):
                m_run_launcher_sub_command('EDIT_LAUNCHER', launcher)
            else:
                log_debug('m_run_launcher_sub_command(EDIT_LAUNCHER) m_run_launcher_sub_command returned False')
                log_debug('m_run_launcher_sub_command(EDIT_LAUNCHER) Closing context menu')

    # --- Submenu command ---
    elif command == 'EDIT_METADATA':
        options = launcher.get_metadata_edit_options()

        # >> Make a list of available metadata scrapers
        # todo: make a separate menu item 'Scrape' with after that a list to select instead of
        # merging it now with other options.
        # for scrap_obj in scrapers_metadata:
        #     options['SCRAPE_' + scrap_obj.name] = 'Scrape metadata from {0} ...'.format(scrap_obj.name)
        #     log_verb('Added metadata scraper {0}'.format(scrap_obj.name))

        s = 'Edit Launcher "{0}" metadata'.format(launcher.get_name())
        selected_option = KodiOrdDictionaryDialog().select(s, options)
        if selected_option is None:
            # >> Return recursively to parent menu.
            log_debug('m_run_launcher_sub_command(EDIT_METADATA) Selected NONE')
        else:
            # >> Execute launcher edit metadata atomic subcommand.
            # >> Then, execute recursively this submenu again.
            # >> The parent menu dialog is instantiated again so it reflects the changes just edited.
            log_debug('m_run_launcher_sub_command(EDIT_METADATA) Selected {0}'.format(selected_option))
            m_run_launcher_sub_command(selected_option, launcher)
            m_run_launcher_sub_command('EDIT_METADATA', launcher)

    # --- Atomic commands ---
    # NOTE integrate subcommands using generic editing functions.
    elif command == 'EDIT_METADATA_TITLE':
        m_subcommand_change_launcher_name(launcher)

    elif command == 'EDIT_METADATA_PLATFORM':
        m_gui_edit_metadata_list(launcher, 'Platform', AEL_platform_list,
                                 launcher.get_platform, launcher.set_platform)

    elif command == 'EDIT_METADATA_RELEASEYEAR':
        m_gui_edit_metadata_str(launcher, 'Release Rear', launcher.get_releaseyear, launcher.set_releaseyear)

    elif command == 'EDIT_METADATA_GENRE':
        m_gui_edit_metadata_str(launcher, 'Genre', launcher.get_genre, launcher.set_genre)

    elif command == 'EDIT_METADATA_DEVELOPER':
        m_gui_edit_metadata_str(launcher, 'Developer', launcher.get_developer, launcher.set_developer)

    elif command == 'EDIT_METADATA_RATING':
        m_gui_edit_rating(launcher, launcher.get_rating, launcher.set_rating)

    elif command == 'EDIT_METADATA_PLOT':
        m_gui_edit_metadata_str(launcher, 'Plot', launcher.get_plot, launcher.set_plot)

    elif command == 'IMPORT_NFO_FILE_DEFAULT':
        m_subcommand_edit_launcher_nfo_import_default(launcher)

    elif command == 'IMPORT_NFO_FILE_BROWSE':
        m_subcommand_edit_launcher_nfo_import_browse(launcher)

    elif command == 'SAVE_NFO_FILE_DEFAULT':
        m_subcommand_edit_launcher_nfo_save_default(launcher)

    # --- Submenu command ---
    elif command == 'EDIT_ASSETS':
        m_gui_edit_object_assets(launcher)

    # --- Submenu command ---
    elif command == 'EDIT_DEFAULT_ASSETS':
        m_gui_edit_object_default_assets(launcher)


    elif command == 'EDIT_LAUNCHER_CATEGORY':
        m_subcommand_edit_launcher_category(launcher)

    # --- Atomic commands ---
    elif command == 'EDIT_LAUNCHER_STATUS':
        launcher.change_finished_status()
        kodi_dialog_OK('Launcher "{0}" status is now {1}'.format(
            launcher.get_name(), launcher.get_finished_str()))
        g_MainRepository.save_launcher(launcher)

    # --- Submenu command (Launcher advanced modifications) ---
    elif command == 'LAUNCHER_ADVANCED_MODS':
        options = launcher.get_advanced_modification_options()
        s = 'Launcher "{0}" advanced modifications'.format(launcher.get_name())
        selected_option = KodiOrdDictionaryDialog().select(s, options)
        if selected_option is None:
            log_debug('m_run_launcher_sub_command(LAUNCHER_ADVANCED_MODS) Selected None. Closing context menu')
        else:
            log_debug('m_run_launcher_sub_command(LAUNCHER_ADVANCED_MODS) Selected {0}'.format(selected_option))
            if m_run_launcher_sub_command(selected_option, launcher):
                m_run_launcher_sub_command('LAUNCHER_ADVANCED_MODS', launcher)
            else:
                log_debug('m_run_launcher_sub_command(LAUNCHER_ADVANCED_MODS) m_run_launcher_sub_command returned False')
                log_debug('m_run_launcher_sub_command(LAUNCHER_ADVANCED_MODS) Closing context menu')

    # --- Submenu command (Manage ROMs) ---
    elif command == 'LAUNCHER_MANAGE_ROMS':
        options = launcher.get_manage_roms_options()
        s = 'Manage Launcher "{0}" ROMs'.format(launcher.get_name())
        selected_option = KodiOrdDictionaryDialog().select(s, options)
        if selected_option is None:
            log_debug('m_run_launcher_sub_command(LAUNCHER_MANAGE_ROMS) Selected None. Closing context menu')
        else:
            log_debug('m_run_launcher_sub_command(LAUNCHER_MANAGE_ROMS) Selected {0}'.format(selected_option))
            if m_run_launcher_sub_command(selected_option, launcher):
                m_run_launcher_sub_command('LAUNCHER_MANAGE_ROMS', launcher)
            else:
                log_debug('m_run_launcher_sub_command(LAUNCHER_MANAGE_ROMS) m_run_launcher_sub_command returned False')
                log_debug('m_run_launcher_sub_command(LAUNCHER_MANAGE_ROMS) Closing context menu')

    # --- Submenu command (Audit ROMs / Launcher viewmode) ---
    elif command == 'LAUNCHER_AUDIT_ROMS':
        options = launcher.get_audit_roms_options()
        s = 'Audit ROMs / Launcher view mode'
        selected_option = KodiOrdDictionaryDialog().select(s, options)
        if selected_option is None:
            log_debug('m_run_launcher_sub_command(LAUNCHER_AUDIT_ROMS) Selected None. Closing context menu')
        else:
            log_debug('m_run_launcher_sub_command(LAUNCHER_AUDIT_ROMS) Selected {0}'.format(selected_option))
            if m_run_launcher_sub_command(selected_option, launcher):
                m_run_launcher_sub_command('LAUNCHER_AUDIT_ROMS', launcher)
            else:
                log_debug('m_run_launcher_sub_command(LAUNCHER_AUDIT_ROMS) m_run_launcher_sub_command returned False')
                log_debug('m_run_launcher_sub_command(LAUNCHER_AUDIT_ROMS) Closing context menu')

    elif command == 'EXPORT_LAUNCHER_XML':
        m_subcommand_export_launcher_xml(launcher)

    # Deleting a Launcher must exit the context menu!
    # If the deletion was sucessful the Launcher does not exit any more.
    elif command == 'DELETE_LAUNCHER':
        if m_subcommand_launcher_delete(launcher):
            return False

    else:
        log_warning('m_run_launcher_sub_command() Unsupported command "{0}"'.format(command))
        kodi_dialog_OK('m_run_launcher_sub_command() Unknown command {0}. '.format(command) +
                       'Please report this bug.')

    # Returns True if the parent menu must be shown again.
    # Return False if context menu must be closed.
    log_debug('m_run_launcher_sub_command({0}) ENDS'.format(command))
    return True

#
# Look at m_run_category_sub_command() for a reference implementation.
#
def m_run_collection_sub_command(command, collection):
    log_debug('m_run_collection_sub_command({0}) BEGIN'.format(command))

    # --- Main menu command ---
    if command == 'EDIT_COLLECTION':
        options = collection.get_edit_options()
        s = 'Select action for ROM Collection "{0}"'.format(collection.get_name())
        selected_option = KodiDictionaryDialog().select(s, options)
        if selected_option is None:
            log_debug('m_run_collection_sub_command(EDIT_COLLECTION) Selected None. Closing context menu.')
        else:
            log_debug('m_run_collection_sub_command(EDIT_COLLECTION) Selected {0}'.format(selected_option))
            if m_run_collection_sub_command(selected_option, collection):
                m_run_collection_sub_command('EDIT_COLLECTION', collection)
            else:
                log_debug('m_run_collection_sub_command(EDIT_COLLECTION) m_run_collection_sub_command returned False')
                log_debug('m_run_collection_sub_command(EDIT_COLLECTION) Closing context menu')

    # --- Submenu command ---
    elif command == 'EDIT_METADATA':
        options = collection.get_metadata_edit_options()
        s = 'Edit ROM Collection "{0}" metadata'.format(collection.get_name())
        selected_option = KodiDictionaryDialog().select(s, options)
        if selected_option is None:
            log_debug('m_run_collection_sub_command(EDIT_METADATA) Selected None')
        else:
            log_debug('m_run_collection_sub_command(EDIT_METADATA) Selected {0}'.format(selected_option))
            m_run_collection_sub_command(selected_option, collection)
            m_run_collection_sub_command('EDIT_METADATA', collection)

    # --- Atomic commands ---
    elif command == 'EDIT_METADATA_TITLE':
        if m_gui_edit_metadata_str('ROM Collection', 'Title', collection.get_name, collection.set_name):
            g_CollectionRepository.save(collection)

    elif command == 'EDIT_METADATA_GENRE':
        if m_gui_edit_metadata_str('ROM Collection', 'Genre', collection.get_genre, collection.set_genre):
            g_CollectionRepository.save(collection)

    elif command == 'EDIT_METADATA_RATING':
        if m_gui_edit_rating('ROM Collection', collection.get_rating, collection.set_rating):
            g_CollectionRepository.save(collection)

    elif command == 'EDIT_METADATA_PLOT':
        if m_gui_edit_metadata_str('ROM Collection', 'Plot', collection.get_plot, collection.set_plot):
            g_CollectionRepository.save(collection)

    # Add these commands IMPORT_NFO_FILE_DEFAULT, IMPORT_NFO_FILE_BROWSE, SAVE_NFO_FILE_DEFAULT.
    # Create a generic function for import/export NFO files.

    # --- Submenu command ---
    elif command == 'EDIT_ASSETS':
        m_gui_edit_object_assets(collection)

    # --- Submenu command ---
    elif command == 'EDIT_DEFAULT_ASSETS':
        m_gui_edit_object_default_assets(collection)

    # --- Atomic commands ---
    elif command == 'EXPORT_COLLECTION_XML':
        m_subcommand_export_collection_xml(collection)

    # Deleting a ROM Collection must exit the context menu!
    # If the deletion was sucessful the ROM Collection does not exit any more.
    elif command == 'DELETE_COLLECTION':
        if m_subcommand_delete_collection(collection):
            return False

    else:
        log_warning('m_run_collection_sub_command() Unsupported command "{0}"'.format(command))
        kodi_dialog_OK('m_run_collection_sub_command() Unknown command {0}. '.format(command) +
                       'Please report this bug.')

    # Returns True if the parent menu must be shown again.
    # Return False if context menu must be closed.
    log_debug('m_run_collection_sub_command({0}) ENDS'.format(command))
    return True

def m_run_rom_sub_command(command, rom):
    log_debug('m_run_rom_sub_command({0}) BEGIN'.format(command))
    
    # Returns True if the parent menu must be shown again.
    # Return False if context menu must be closed.
    log_debug('m_run_rom_sub_command({0}) ENDS'.format(command))
    return True

# -------------------------------------------------------------------------------------------------
# Category context menu atomic comands.
# Only Category context menu functions have debug statemets. This debug messages are to
# debug the context menu recursive logic.
# -------------------------------------------------------------------------------------------------
# NOTE Create new generic functions to save/load NFO files.
#      NFO save/load functionality must be in the edited-object methods.
def m_subcommand_category_import_nfo_file(category):
    # >> Returns True if changes were made
    NFO_file = fs_get_category_NFO_name(g_settings, category.get_data())
    if not fs_import_category_NFO(NFO_file, category.get_data()): return
    kodi_notify('Imported Category NFO file {0}'.format(NFO_FileName.getPath()))
    g_CategoryRepository.save(category)

def m_subcommand_category_browse_import_nfo_file(category):
    NFO_file = xbmcgui.Dialog().browse(1, 'Select NFO description file', 'files', '.nfo', False, False).decode('utf-8')
    log_debug('_command_edit_category() Dialog().browse returned "{0}"'.format(NFO_file))
    if not NFO_file: return
    NFO_FileName = FileNameFactory.create(NFO_file)
    if not NFO_FileName.exists(): return
    # >> Returns True if changes were made
    if not fs_import_category_NFO(NFO_FileName, category.get_data()): return
    kodi_notify('Imported Category NFO file {0}'.format(NFO_FileName.getPath()))   
    g_CategoryRepository.save(category)

def m_subcommand_category_save_nfo_file(category):
    NFO_FileName = fs_get_category_NFO_name(g_settings, category.get_data())
    # >> Returns False if exception happened. If an Exception happened function notifies
    # >> user, so display nothing to not overwrite error notification.
    if not fs_export_category_NFO(NFO_FileName, category.get_data()): return
    # >> No need to save categories/launchers
    kodi_notify('Exported Category NFO file {0}'.format(NFO_FileName.getPath()))

# --- Export Category XML configuration ---
def m_subcommand_category_export_xml(category):
    category_data = category.get_data_dic()
    category_fn_str = 'Category_' + text_title_to_filename_str(category.get_name()) + '.xml'
    log_debug('m_subcommand_export_category_xml() Exporting Category configuration')
    log_debug('m_subcommand_export_category_xml() Name     "{0}"'.format(category.get_name()))
    log_debug('m_subcommand_export_category_xml() ID       {0}'.format(category.get_id()))
    log_debug('m_subcommand_export_category_xml() l_fn_str "{0}"'.format(category_fn_str))

    # --- Ask user for a path to export the launcher configuration ---
    dir_path = xbmcgui.Dialog().browse(0, 'Select directory to export XML', 'files', 
                                       '', False, False).decode('utf-8')
    if not dir_path: return

    # --- If XML exists then warn user about overwriting it ---
    export_FN = FileNameFactory.create(dir_path).pjoin(category_fn_str)
    if export_FN.exists():
        ret = kodi_dialog_yesno('Overwrite file {0}?'.format(export_FN.getPath()))
        if not ret:
            kodi_notify_warn('Export of Category XML cancelled')
            return

    # >> If everything goes all right when exporting then the else clause is executed.
    # >> If there is an error/exception then the exception handler prints a warning message
    # >> inside the function autoconfig_export_category() and the sucess message is never
    # >> printed. This is the standard way of handling error messages in AEL code.
    try:
        autoconfig_export_category(category_data, export_FN)
    except AddonError as E:
        kodi_notify_warn('{0}'.format(E))
    else:
        kodi_notify('Exported Category "{0}" XML config'.format(category.get_name()))

#
# Remove category. Also removes launchers in that category
# Returns True if the Category was deleted
# Returns False if the Category was not deleted.
#
def m_subcommand_category_delete(category):
    category_id   = category.get_id()
    category_name = category.get_name()
    launchers     = g_MainRepository.find_launchers_by_category_id(category_id)

    if len(launchers) > 0:
        ret = kodi_dialog_yesno('Category "{0}" has {1} launchers. '.format(category_name, len(launchers)) +
                                'Deleting it will also delete related launchers. ' +
                                'Are you sure you want to delete "{0}"?'.format(category_name))
        if not ret: return False

        # --- Delete launchers and ROM JSON/XML files associated with them ---
        log_info('Deleting category "{0}" ID {1}'.format(category_name, category.get_id()))
        for launcher in launchers:
            log_info('Deleting linked launcher "{0}" ID {1}'.format(launcher.get_name(), launcher.get_id()))
            g_MainRepository.delete_launcher(launcher)
        g_MainRepository.delete_category(category)
    else:
        ret = kodi_dialog_yesno('Category "{0}" has no launchers. '.format(category_name) +
                                'Are you sure you want to delete "{0}"?'.format(category_name))
        if not ret: return False
        log_info('Deleting category "{0}" ID {1}'.format(category_name, category.get_id()))
        log_info('Category has no launchers, so no launchers to delete.')
        g_MainRepository.delete_category(category)
    kodi_notify('Deleted category {0}'.format(category_name))

    return True

# -------------------------------------------------------------------------------------------------
# ROM Collections context menu atomic comands.
# -------------------------------------------------------------------------------------------------




# -------------------------------------------------------------------------------------------------
# Launcher context menu atomic comands.
# -------------------------------------------------------------------------------------------------
#
# --- Edition of the launcher name ---
# Function is required because if the launcher support ROMs the ROM databases must be renamed.
def m_subcommand_launcher_edit_name(launcher):
    current_name = launcher.get_name()
    keyboard = xbmc.Keyboard(current_name, 'Edit title')
    keyboard.doModal()
    if not keyboard.isConfirmed(): return

    title = keyboard.getText().decode('utf-8')
    if not launcher.change_name(title):
        kodi_notify('Launcher Title not changed')
        return

    if launcher.supports_launching_roms():
        raise AddonError('Implement me!')
        # --- Rename ROMs XML/JSON file (if it exists) and change launcher ---
        old_roms_base_noext = launcher.get_roms_base()
        category = self.category_repository.find(launcher.get_category_id())
        category_name = category.get_name()

        new_roms_base_noext = fs_get_ROMs_basename(category_name, title, launcher.get_id())
        fs_rename_ROMs_database(ROMS_DIR, old_roms_base_noext, new_roms_base_noext)

        launcher.update_roms_base(new_roms_base_noext)

    g_LauncherRepository.save(launcher)
    kodi_refresh_container()
    kodi_notify('Launcher Title is now {0}'.format(launcher.get_name()))

# --- Import launcher metadata from NFO file (default location) ---
def m_subcommand_launcher_import_nfo_file(launcher):
    # >> Get NFO file name for launcher
    # >> Launcher is edited using Python passing by assigment
    # >> Returns True if changes were made
    NFO_file = fs_get_launcher_NFO_name(g_settings, launcher.get_data())
    if launcher.import_nfo_file(NFO_file):
        g_LauncherRepository.save(launcher)
        kodi_notify('Imported Launcher NFO file {0}'.format(NFO_file.getPath()))

# --- Browse for NFO file ---
def m_subcommand_launcher_browse_import_nfo_file(launcher):
    NFO_file = xbmcgui.Dialog().browse(1, 'Select Launcher NFO file', 'files', '.nfo', False, False).decode('utf-8')
    if not NFO_file: 
        return

    NFO_FileName = FileNameFactory.create(NFO_file)
    if not NFO_FileName.exists(): 
        return

    # >> Launcher is edited using Python passing by assigment
    # >> Returns True if changes were made
    if launcher.import_nfo_file(NFO_FileName):
        g_LauncherRepository.save(launcher)
        kodi_notify('Imported Launcher NFO file {0}'.format(NFO_FileName.getPath()))

# --- Export launcher metadata to NFO file ---
def m_subcommand_launcher_save_nfo_file(launcher):
    NFO_FileName = fs_get_launcher_NFO_name(g_settings, launcher.get_data())
    if launcher.export_nfo_file(NFO_FileName):
        kodi_notify('Exported Launcher NFO file {0}'.format(NFO_FileName.getPath()))

def m_subcommand_launcher_edit_category(launcher):
    # >> If no Categories there is nothing to change
    if g_MainRepository.num_categories() == 0:
        kodi_dialog_OK('There is no Categories. Nothing to change.')
        return

    # Add special root cateogory at the beginning
    categories_id   = [VCATEGORY_ADDONROOT_ID]
    categories_name = ['Addon root (no Category)']
    category_list = g_MainRepository.get_categories_odict()
    for key in category_list:
        categories_id.append(key)
        categories_name.append(category_list[key])

    selected_cat = xbmcgui.Dialog().select('Select the category', categories_name)
    if selected_cat < 0: return

    current_category_ID = launcher.get_category_id()
    new_category_ID = categories_id[selected_cat]
    launcher.update_category(new_category_ID)
    log_debug('m_subcommand_edit_launcher_category() current category   ID "{0}"'.format(current_category_ID))
    log_debug('m_subcommand_edit_launcher_category() new     category   ID "{0}"'.format(new_category_ID))
    log_debug('m_subcommand_edit_launcher_category() new     category name "{0}"'.format(categories_name[selected_cat]))

    # >> Save cateogries/launchers
    g_MainRepository.save_launcher(launcher)

    # >> Display new category where launcher has moved
    # For some reason ReplaceWindow() does not work, bu Container.Update() does.
    # See http://forum.kodi.tv/showthread.php?tid=293844
    if new_category_ID == VCATEGORY_ADDONROOT_ID:
        plugin_url = self.base_url
    else:
        plugin_url = '{0}?com=SHOW_LAUNCHERS&amp;catID={1}'.format(self.base_url, new_category_ID)
    exec_str = 'Container.Update({0},replace)'.format(plugin_url)
    log_debug('_command_edit_launcher() Plugin URL     "{0}"'.format(plugin_url))
    log_debug('_command_edit_launcher() Executebuiltin "{0}"'.format(exec_str))
    xbmc.executebuiltin(exec_str)
    kodi_notify('Launcher new Category is {0}'.format(categories_name[selected_cat]))
    kodi_refresh_container()

# --- Export Launcher XML configuration ---
def m_subcommand_launcher_export_XML(launcher):

    # >> Ask user for a path to export the launcher configuration
    dir_path = xbmcgui.Dialog().browse(0, 'Select XML export directory', 'files', 
                                        '', False, False).decode('utf-8')
        
    category = self.category_repository.find(launcher.get_category_id())
    launcher.export_configuration(dir_path, category)
    return self._command_edit_launcher(launcher.get_category_id(), launcher.get_id())

# --- Remove Launcher menu option ---
def m_subcommand_launcher_delete(launcher):
    # >> ROMs launcher
    confirmed = False
    if launcher.supports_launching_roms():
        launcher.get_roms()
        num_roms = len(roms)
        confirmed = kodi_dialog_yesno(
            'Launcher "{0}" has {1} ROMs. '.format(launcher.get_name(), num_roms) +
            'Are you sure you want to delete it?')
    # >> Standalone launcher
    else:
        confirmed = kodi_dialog_yesno(
            'Are you sure you want to delete Launcher "{0}" it?'.format(launcher.get_name()))
    if not confirmed: return False

    # ObjectRepository.delete_launcher() also cleans the ROM JSON/XML databases.
    launcher.delete_from_disk(launcher)
    kodi_refresh_container()
    kodi_notify('Deleted Launcher {0}'.format(launcher.get_name()))

    return True

# -------------------------------------------------------------------------------------------------
# ROMs context menu atomic commands.
# -------------------------------------------------------------------------------------------------




















# --- Scrape launcher metadata ---
def m_subcommand_scrape_launcher(launcher, selected_option):
    scraper_obj_name = selected_option.replace('SCRAPE_', '')
    scraper_obj = filter(lambda x: x.name == scraper_obj_name, scrapers_metadata)[0]
    log_debug('_subcommand_scrape_launcher() User chose scraper "{0}"'.format(scraper_obj.name))
    
    # --- Initialise asset scraper ---
    scraper_obj.set_addon_dir(CURRENT_ADDON_DIR.getPath())
    log_debug('_subcommand_scrape_launcher() Initialised scraper "{0}"'.format(scraper_obj.name))
    
    # >> If this returns False there were no changes so no need to save categories.xml
    if self._gui_scrap_launcher_metadata(launcher.get_id(), scraper_obj): 
        g_LauncherRepository.save(launcher)


# --- Audit ROMs / Launcher view mode ---
# NOTE ONLY for ROM launchers, not for standalone launchers
#
# >>> New No-Intro/Redump DAT file management <<<
# A) If the user adds a No-Intro/Redump DAT, ROMs will be audited automatically after addition
#    of the DAT file.
# B) If the DAT file cannot be loaded or the audit cannot be completed, 'xml_dat_file'
#    will be set to ''. Hence, if 'xml_dat_file' is not empty launcher ROMs have been audited.
# C) The audit will be refreshed every time a change is made to the ROMs of the launcher 
#    to keep Parent/Clone database consistency.
# D) There is no option to delete the added Missing ROMs, but the user can choose to display 
#    them or not.
# E) To remove the audit status and revert the launcher back to normal, user must delete the 
#    No-Intro/Redump DAT file.
#
def m_subcommand_audit_roms(launcher):
    # --- Shows a select box with the options to edit ---
    dialog = DictionaryDialog()
    launcher_options = launcher.get_audit_roms_options()
    selected_option = dialog.select('Audit ROMs / Launcher view mode', launcher_options),
    
    if selected_option is None:
        return self._command_edit_launcher(launcher.get_category_id(), launcher.get_id())
    
    log_debug('_subcommand_audit_roms(): Selected option = {0}'.format(selected_option))
    if type(selected_option) is tuple:
        selected_option = selected_option[0]
        log_debug('_subcommand_audit_roms(): Selected option = {0}'.format(selected_option))
                            
    if selected_option is None:
        log_debug('_subcommand_audit_roms(): Selected option = NONE')
        self._command_edit_launcher(launcher.get_category_id(), launcher.get_id())
        return

    self.run_sub_command(selected_option, None, launcher)
    self._subcommand_audit_roms(launcher)

# --- Change launcher view mode (Normal or PClone) ---
# Command: CHANGE_DISPLAY_MODE
def m_subcommand_change_display_mode(launcher):

    # >> Krypton feature: preselect the current item.
    # >> NOTE Preselect must be called with named parameter, otherwise it does not work well.
    display_mode = launcher.get_display_mode()
    modes_list = {key: key for key in LAUNCHER_DMODE_LIST}
    log_debug(display_mode)

    selected_mode = dialog.select('Launcher display mode', modes_list, preselect = display_mode)
    if selected_mode is None or selected_mode == display_mode: 
        return

    actual_mode = launcher.change_display_mode(selected_mode)
    if actual_mode != selected_mode:
        kodi_dialog_OK('No-Intro DAT not configured or cannot be found. PClone or 1G1R view mode cannot be set.')
        return
            
    g_LauncherRepository.save(launcher)
    kodi_notify('Launcher view mode set to {0}'.format(selected_mode))
    return

# --- Delete No-Intro XML parent-clone DAT ---
# Command: DELETE_NO_INTRO
def m_subcommand_delete_no_intro(launcher):
    if not launcher.has_nointro_xml():
        kodi_dialog_OK('No-Intro/Redump XML DAT file not configured.')
        return
                
    ret = xbmcgui.Dialog().yesno('Advanced Emulator Launcher', 'Delete No-Intro/Redump XML DAT file?')
    if not ret: 
        return

    launcher.reset_nointro_xmldata()
    kodi_dialog_OK('No-Intro DAT deleted. No-Intro Missing ROMs will be removed now.')

    # --- Remove No-Intro status and delete missing/dead ROMs to revert launcher to normal ---
    # Note that roms dictionary is updated using Python pass by assigment.
    # _roms_reset_NoIntro_status() does not save ROMs JSON/XML.
    scanner = RomDatFileScanner(g_settings)
    roms = launcher.get_roms()

    scanner.roms_reset_NoIntro_status(launcher, roms)
    launcher.update_rom_set(roms)

    launcher.set_number_of_roms(len(roms))
    g_LauncherRepository.save(launcher)
    kodi_notify('Removed No-Intro/Redump XML DAT file')
    return

# --- Add No-Intro XML parent-clone DAT ---
# Command: ADD_NO_INTRO
def m_subcommand_add_no_intro(launcher):
    # --- Browse for No-Intro file ---
    # BUG For some reason *.dat files are not shown on the dialog, but XML files are OK!!!
    # Fixed in Krypton Beta 6 http://forum.kodi.tv/showthread.php?tid=298161
                    
    dat_file = xbmcgui.Dialog().browse(1, 'Select No-Intro XML DAT (XML|DAT)', 'files', '.dat|.xml').decode('utf-8')
    if not FileNameFactory.create(dat_file).exists(): 
        return
        
    launcher.set_nointro_xml_file(dat_file)
    kodi_dialog_OK('DAT file successfully added. Launcher ROMs will be audited now.')

    # --- Audit ROMs ---
    # Note that roms and launcher dictionaries are updated using Python pass by assigment.
    # _roms_update_NoIntro_status() does not save ROMs JSON/XML.
    scanner = RomDatFileScanner(g_settings)
    roms = launcher.get_roms()

    if scanner.update_roms_NoIntro_status(launcher, roms):
        launcher.update_rom_set(roms)
        kodi_notify('Added No-Intro/Redump XML DAT. '
                    'Have {0} / Miss {1} / Unknown {2}'.format(self.audit_have, self.audit_miss, self.audit_unknown))
    else:
        # >> ERROR when auditing the ROMs. Unset nointro_xml_file
        launcher.reset_nointro_xmldata()
        kodi_notify_warn('Error auditing ROMs. XML DAT file not set.')
        
    launcher.set_number_of_roms(len(roms))
    g_LauncherRepository.save(launcher)
    return

# --- Create Parent/Clone DAT based on ROM filenames ---
# Command: CREATE_PARENTCLONE_DAT
def m_subcommand_create_parentclone_dat(launcher):
    if launcher.has_nointro_xml():
        d = xbmcgui.Dialog()
        ret = d.yesno('Advanced Emulator Launcher',
                        'This Launcher has a DAT file attached. Creating a filename '
                        'based DAT will remove the No-Intro/Redump DAT. Continue?')
        if not ret: 
            return

    # >> Delete No-Intro/Redump DAT and reset ROM audit.
                
    # >> Create an artificial <roms_base_noext>_DAT.json file. Keep launcher
    # >> nointro_xml_file = '' because the artificial DAT is not an official DAT.
    kodi_dialog_OK('Not implemented yet. Sorry.')

# --- Display ROMs ---
# Command: CHANGE_DISPLAY_ROMS
def m_subcommand_change_display_roms(launcher):
    # >> If no DAT configured exit.
    if not launcher.has_nointro_xml():
        kodi_dialog_OK('No-Intro/Redump XML DAT file not configured.')
        return
                   
    # >> Krypton feature: preselect the current item.
    display_mode = launcher.get_nointro_display_mode()
    modes_list = {key: key for key in NOINTRO_DMODE_LIST}

    selected_mode = dialog.select('Roms display mode', modes_list, preselect = display_mode)
    if selected_mode is None: 
        return

    launcher.change_nointro_display_mode(selected_mode)
    g_LauncherRepository.save(launcher)
    kodi_notify('Display ROMs changed to "{0}"'.format(selected_mode))       
    return

# --- Update ROM audit ---
def m_subcommand_update_rom_audit(launcher):
    # >> If no DAT configured exit.
    if not launcher.has_nointro_xml():
        kodi_dialog_OK('No-Intro/Redump XML DAT file not configured.')
        return

    # Note that roms and launcher dictionaries are updated using Python pass by assigment.
    # _roms_update_NoIntro_status() does not save ROMs JSON/XML.
    scanner = RomDatFileScanner(g_settings)
    roms = launcher.get_roms()
    
    if scanner.update_roms_NoIntro_status(launcher, roms):
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Advanced Emulator Launcher', 'Saving ROM JSON database ...')
        launcher.update_rom_set(roms)
        pDialog.update(100)
        pDialog.close()
        kodi_notify('Have {0} / Miss {1} / Unknown {2}'.format(self.audit_have, self.audit_miss, self.audit_unknown))
    else:
        # >> ERROR when auditing the ROMs. Unset nointro_xml_file
        launcher.reset_nointro_xmldata()
        kodi_notify_warn('Error auditing ROMs. XML DAT file unset.')
        return
       
    launcher.set_number_of_roms(len(roms))
    g_LauncherRepository.save(launcher)
    return

# --- Launcher Advanced Modifications menu option ---
def m_subcommand_advanced_modifications(launcher):
    # --- Shows a select box with the options to edit ---
    dialog = DictionaryDialog()
    launcher_options = launcher.get_advanced_modification_options()
    selected_option = dialog.select('Launcher Advanced Modification', launcher_options)
            
    log_debug('_subcommand_advanced_modifications(): Selected option = {0}'.format(selected_option))
    if type(selected_option) is tuple:
        selected_option = selected_option[0]
        log_debug('_subcommand_advanced_modifications(): Selected option = {0}'.format(selected_option))
                
    if selected_option is None:
        log_debug('_subcommand_advanced_modifications(): Selected option = NONE')
        self._command_edit_launcher(launcher.get_category_id(), launcher.get_id())
        return

    self.run_sub_command(selected_option, None, launcher)
    self._subcommand_advanced_modifications(launcher)

# >> Choose launching mechanism. Command: CHANGE_APPLICATION
def m_subcommand_change_launcher_application(launcher):
    if launcher.change_application():
        g_LauncherRepository.save(launcher)
        kodi_notify('Changed launcher application')

    return

# --- Edition of the launcher arguments. Command: MODIFY_ARGS ---
def m_subcommand_modify_launcher_arguments(launcher):
    args = launcher.get_args()
    keyboard = xbmc.Keyboard(args, 'Edit application arguments')
    keyboard.doModal()

    if not keyboard.isConfirmed(): return
    altered_args = keyboard.getText().decode('utf-8')
        
    launcher.change_arguments(altered_args)

    g_LauncherRepository.save(launcher)
    kodi_notify('Changed launcher arguments')

# --- Launcher Additional arguments. Command: ADDITIONAL_ARGS ---
def m_subcommand_change_launcher_additional_arguments(launcher):
    additional_args_list = launcher.get_all_additional_arguments()
    additional_args_list_options = []

    for extra_arg in additional_args_list:
        additional_args_list_options.append("Modify '{0}'".format(extra_arg))

    selected_arg_idx = xbmcgui.Dialog().select('Launcher additional arguments', ['Add new additional arguments ...'] + additional_args_list_options)

    if selected_arg_idx < 0:
        return

    # >> Add new additional arguments
    if selected_arg_idx == 0:
        keyboard = xbmc.Keyboard('', 'Edit launcher additional arguments')
        keyboard.doModal()
        if not keyboard.isConfirmed(): return
        new_argument = keyboard.getText().decode('utf-8')
        launcher.add_additional_argument(new_argument)
            
        g_LauncherRepository.save(launcher)
        kodi_notify('Added additional arguments to launcher {0}'.format(launcher.get_name()))
        return
        
    selected_arg_idx = selected_arg_idx-1
    selected_arg = launcher.get_additional_argument(selected_arg_idx)
    edit_action = xbmcgui.Dialog().select('Modify extra arguments',
                                ["Edit '{0}' ...".format(selected_arg), 
                                'Delete extra arguments'])

    if edit_action < 0: 
        return

    if edit_action == 0:
        keyboard = xbmc.Keyboard(selected_arg, 'Edit application arguments')
        keyboard.doModal()
        if not keyboard.isConfirmed(): return
            
        altered_arg = keyboard.getText().decode('utf-8')
        launcher.set_additional_argument(selected_arg_idx, altered_arg)
            
        g_LauncherRepository.save(launcher)
        kodi_notify('Changed extra arguments in launcher {0}'.format(launcher.get_name()))

    elif edit_action == 1:
        ret = kodi_dialog_yesno('Are you sure you want to delete Launcher additional arguments "{0}"?'.format(selected_arg))
        if not ret: return
        launcher.remove_additional_argument(selected_arg_idx)
            
        g_LauncherRepository.save(launcher)
        kodi_notify('Removed argument from extra arguments in launcher {0}'.format(launcher.get_name()))

    return

# --- Launcher ROM path menu option (Only ROM launchers). Command: CHANGE_ROMPATH ---
def m_subcommand_change_launcher_rompath(launcher):
    if not launcher.supports_launching_roms(): 
        return
        
    current_path = launcher.get_rom_path()
    rom_path = xbmcgui.Dialog().browse(0, 'Select Files path', 'files', '', False, False, current_path.getOriginalPath()).decode('utf-8')
        
    if not rom_path or rom_path == current_path.getOriginalPath():
        return

    launcher.change_rom_path(rom_path)
    g_LauncherRepository.save(launcher)

    kodi_notify('Changed ROM path')
    return

# --- Edition of the launcher ROM extension (Only ROM launchers). Command: CHANGE_ROMEXT ---
def m_subcommand_change_launcher_rom_extensions(launcher):
    if not launcher.supports_launching_roms(): 
        return

    current_ext = launcher.get_rom_extensions_combined()
    keyboard = xbmc.Keyboard(current_ext, 'Edit ROM extensions, use "|" as separator. (e.g lnk|cbr)')
    keyboard.doModal()
        
    if not keyboard.isConfirmed():
        return

    launcher.change_rom_extensions(keyboard.getText().decode('utf-8'))

    g_LauncherRepository.save(launcher)
    kodi_notify('Changed ROM extensions')

# --- Minimise Kodi window flag. Command: TOGGLE_WINDOWED ---
def m_subcommand_toggle_windowed(launcher):
        
    is_windowed = launcher.is_in_windowed_mode()
    p_idx = 1 if is_windowed else 0
    type3 = xbmcgui.Dialog().select('Toggle Kodi into windowed mode', ['OFF (default)', 'ON'], preselect = p_idx)
    if type3 < 0 or type3 == p_idx: return

    is_windowed = launcher.set_windowed_mode(type3 > 0)
    minimise_str = 'ON' if is_windowed else 'OFF'
        
    g_LauncherRepository.save(launcher)
    kodi_notify('Toggle Kodi into windowed mode {0}'.format(minimise_str))

# --- Non-blocking launcher flag. Command: TOGGLE_NONBLOCKING ---_
def m_subcommand_toggle_nonblocking(launcher):
    is_non_blocking = launcher.is_non_blocking()
    p_idx = 1 if is_non_blocking else 0
    type3 = xbmcgui.Dialog().select('Non-blocking launcher', ['OFF (default)', 'ON'], preselect = p_idx)

    if type3 < 0 or type3 == p_idx: return
        
    is_non_blocking = launcher.set_non_blocking(type3 > 0)
    non_blocking_str = 'ON' if is_non_blocking else 'OFF'

    g_LauncherRepository.save(launcher)
    kodi_notify('Launcher Non-blocking is now {0}'.format(non_blocking_str))

# --- Multidisc ROM support (Only ROM launchers) Command: TOGGLE_MULTIDISC ---
def m_subcommand_toggle_multidisc(launcher):
    if not launcher.supports_launching_roms(): 
        return

    supports_multidisc = launcher.supports_multidisc()
    p_idx = 1 if supports_multidisc else 0
    type3 = xbmcgui.Dialog().select('Multidisc support launcher', ['OFF (default)', 'ON'], preselect = p_idx)

    if type3 < 0 or type3 == p_idx: return
        
    supports_multidisc = launcher.set_multidisc_support(type3 > 0)
    multidisc_str = 'ON' if supports_multidisc else 'OFF'
        
    g_LauncherRepository.save(launcher)
    kodi_notify('Launcher Multidisc support is now {0}'.format(multidisc_str))

    return





# --- Scan ROMs local artwork ---
# >> A) First, local assets are searched for every ROM based on the filename.
# >> B) Next, missing assets are searched in the Parent/Clone group using the files
#       found in the previous step. This is much faster than searching for files again.
#
def m_subcommand_scan_local_artwork(launcher):
    log_info('_command_edit_launcher() Rescanning local assets ...')
    launcher_data = launcher.get_data()

    # ~~~ Check asset dirs and disable scanning for unset dirs ~~~
    # todo: move asset_get_configured_dir_list method to launcher object
    (enabled_asset_list, unconfigured_name_list) = asset_get_configured_dir_list(launcher_data)
    if unconfigured_name_list:
        unconfigure_asset_srt = ', '.join(unconfigured_name_list)
        kodi_dialog_OK('Assets directories not set: {0}. '.format(unconfigure_asset_srt) +
                        'Asset scanner will be disabled for this/those.')

    # ~~~ Ensure there is no duplicate asset dirs ~~~
    # >> Cancel scanning if duplicates found
    duplicated_name_list = launcher.get_duplicated_asset_dirs()
    if duplicated_name_list:
        duplicated_asset_srt = ', '.join(duplicated_name_list)
        log_info('Duplicated asset dirs: {0}'.format(duplicated_asset_srt))
        kodi_dialog_OK('Duplicated asset directories: {0}. '.format(duplicated_asset_srt) +
                        'Change asset directories before continuing.')   
        return
    else:
        log_info('No duplicated asset dirs found')

    # --- Create a cache of assets ---
    # >> misc_add_file_cache() creates a set with all files in a given directory.
    # >> That set is stored in a function internal cache associated with the path.
    # >> Files in the cache can be searched with misc_search_file_cache()
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Advanced Emulator Launcher', 'Scanning files in asset directories ...')

    rom_asset_kinds = self.assetFactory.get_asset_kinds_for_roms()

    for i, rom_asset_info in enumerate(rom_asset_kinds):
        asset_path = launcher.get_asset_path(rom_asset_info)
        misc_add_file_cache(asset_path)
        pDialog.update((100*i)/len(rom_asset_kinds))

    pDialog.update(100)
    pDialog.close()

    # --- Traverse ROM list and check local asset/artwork ---
    pDialog.create('Advanced Emulator Launcher', 'Searching for local assets/artwork ...')
                
    roms = launcher.get_roms()

    if roms:
        num_items = len(roms) if roms else 0
        item_counter = 0
        for rom in roms:
            # --- Search assets for current ROM ---
            ROMFile = rom.get_file()
            rom_basename_noext = ROMFile.getBase_noext()
            log_verb('Checking ROM "{0}" (ID {1})'.format(ROMFile.getBase(), rom.get_id()))

            # --- Search assets ---
            for i, AInfo in enumerate(rom_asset_kinds):
                # log_debug('Search  {0}'.format(AInfo.name))
                if not enabled_asset_list[i]: continue
                # >> Only look for local asset if current file do not exists. This avoid
                # >> clearing user-customised assets. Also, first check if the field
                # >> is defined (which is very quick) to avoid an extra filesystem 
                # >> exist check() for missing images.
                if rom.get_asset(AInfo):
                    # >> However, if the artwork is a substitution from the PClone group
                    # >> and the user updated the artwork collection for this ROM the 
                    # >> new image will not be picked with the current implementation ...
                    #
                    # >> How to differentiate substituted PClone artwork from user
                    # >> manually customised artwork???
                    # >> If directory is different it is definitely customised.
                    # >> If directory is the same and the basename is from a ROM in the
                    # >> PClone group it is very likely it is substituted.
                    current_asset_FN = rom.get_asset_file(AInfo)
                    if current_asset_FN.exists():
                        log_debug('Local {0:<9} "{1}"'.format(AInfo.name, current_asset_FN.getPath()))
                        continue
                # >> Old implementation (slow). Using FileNameFactory.create().exists() to check many
                # >> files becames really slow.
                # asset_dir = FileNameFactory.create(launcher[AInfo.path_key])
                # local_asset = misc_look_for_file(asset_dir, rom_basename_noext, AInfo.exts)
                # >> New implementation using a cache.
                asset_path = FileNameFactory.create(launcher_data[AInfo.path_key])
                local_asset = misc_search_file_cache(asset_path, rom_basename_noext, AInfo.exts)
                if local_asset:
                    rom.set_asset(AInfo, local_asset)
                    log_debug('Found {0:<9} "{1}"'.format(AInfo.name, local_asset.getPath()))
                else:
                    rom.clear_asset(AInfo)
                    log_debug('Miss  {0:<9}'.format(AInfo.name))
            # --- Update progress dialog ---
            item_counter += 1
            pDialog.update((item_counter*100)/num_items)
    pDialog.update(100)
    pDialog.close()

    # --- Crete Parent/Clone dictionaries ---
    # --- Traverse ROM list and check assets in the PClone group ---
    # >> This is only available if a No-Intro/Redump DAT is configured. If not, warn the user.
    if g_settings['audit_pclone_assets'] and not launcher.has_nointro_xml():
        log_info('Use assets in the Parent/Clone group is ON. No-Intro/Redump DAT not configured.')
        kodi_dialog_OK('No-Intro/Redump DAT not configured and audit_pclone_assets is True. ' +
                        'Cancelling looking for assets in the Parent/Clone group.')
    elif g_settings['audit_pclone_assets'] and launcher.has_nointro_xml():
        
        log_info('Use assets in the Parent/Clone group is ON. Loading Parent/Clone dictionaries.')
        roms_pclone_index = launcher.get_pclone_indices()
        clone_parent_dic  = launcher.get_parent_indices()

        pDialog.create('Advanced Emulator Launcher', 'Searching for assets/artwork in the Parent/Clone group ...')
        num_items = len(roms)
        item_counter = 0
        for rom in roms:
            # --- Search assets for current ROM ---
            rom_id = rom.get_id()
            ROMFile = rom.get_file()
            rom_basename_noext = ROMFile.getBase_noext()
            log_verb('Checking ROM "{0}" (ID {1})'.format(ROMFile.getBase(), rom_id))

            # --- Make a PClone group list for this ROM ---
            if rom_id in roms_pclone_index:
                parent_id = rom_id
                num_clones = len(roms_pclone_index[rom_id])
                log_debug('ROM is a parent (parent ID {0} / {1} clones)'.format(parent_id, num_clones))
            else:
                parent_id = clone_parent_dic[rom_id]
                log_debug('ROM is a clone (parent ID {0})'.format(parent_id))
            pclone_set_id_list = []
            pclone_set_id_list.append(parent_id)
            pclone_set_id_list += roms_pclone_index[parent_id]
            # >> Remove current ROM from PClone group
            pclone_set_id_list.remove(rom_id)
            # log_debug(unicode(pclone_set_id_list))
            log_debug('PClone group list has {0} ROMs (after stripping current ROM)'.format(len(pclone_set_id_list)))
            if len(pclone_set_id_list) == 0: continue

            # --- Search assets ---
            for i, AInfo in enumerate(rom_asset_kinds):
                # log_debug('Search  {0}'.format(AInfo.name))
                if not enabled_asset_list[i]: continue
                asset_DB_file = rom.get_asset(AInfo)
                # >> Only search for asset in the PClone group if asset is missing
                # >> from current ROM.
                if not asset_DB_file:
                    # log_debug('Search  {0} in PClone set'.format(AInfo.name))
                    for set_rom_id in pclone_set_id_list:
                        # ROMFile_t = FileNameFactory.create(roms[set_rom_id]['filename'])
                        # log_debug('PClone group ROM "{0}" (ID) {1})'.format(ROMFile_t.getBase(), set_rom_id))
                        set_rom = launcher.select_rom(set_rom_id)
                        asset_DB_file_t = set_rom.get_asset_file(AInfo)
                        if asset_DB_file_t:
                            rom.set_asset(AInfo, asset_DB_file_t)
                            log_debug('Found {0:<9} "{1}"'.format(AInfo.name, asset_DB_file_t.getOriginalPath()))
                            # >> Stop as soon as one asset is found in the group.
                            break
                    # >> The else statement is executed when the loop has exhausted iterating the list.
                    else:
                        log_debug('Miss  {0:<9}'.format(AInfo.name))
                else:
                    log_debug('Has   {0:<9}'.format(AInfo.name))
            # >> Update progress dialog
            item_counter += 1
            pDialog.update((item_counter*100)/num_items)
        pDialog.update(100)
        pDialog.close()

    # --- Update assets on _parents.json ---
    # >> Here only assets s_* are changed. I think it is not necessary to audit ROMs again.
    pDialog.create('Advanced Emulator Launcher', 'Saving ROM JSON database ...')
    if launcher.has_nointro_xml():
        log_verb('Updating artwork on parent JSON database.')
        parent_roms = launcher.get_parent_roms()
        pDialog.update(25)
        for parent_rom in parent_roms:
            
            org_rom         = launcher.select_rom(parent_rom.get_id())
            org_rom_data    = org_rom.get_data()
            parent_rom_data = parent_rom.get_data()

            parent_rom_data['s_banner']    = org_rom_data['s_banner']
            parent_rom_data['s_boxback']   = org_rom_data['s_boxback']
            parent_rom_data['s_boxfront']  = org_rom_data['s_boxfront']
            parent_rom_data['s_cartridge'] = org_rom_data['s_cartridge']
            parent_rom_data['s_clearlogo'] = org_rom_data['s_clearlogo']
            parent_rom_data['s_fanart']    = org_rom_data['s_fanart']
            parent_rom_data['s_flyer']     = org_rom_data['s_flyer']
            parent_rom_data['s_manual']    = org_rom_data['s_manual']
            parent_rom_data['s_map']       = org_rom_data['s_map']
            parent_rom_data['s_snap']      = org_rom_data['s_snap']
            parent_rom_data['s_title']     = org_rom_data['s_title']
            parent_rom_data['s_trailer']   = org_rom_data['s_trailer']

        launcher.update_parent_rom_set(parent_roms)

    # --- Initialise asset scraper ---
    # scraper_obj.set_addon_dir(g_PATHS.ADDON_CODE_DIR.getPath())
    # log_debug('_command_edit_launcher() Initialised scraper "{0}"'.format(scraper_obj.name))

    # ~~~ Save ROMs XML file ~~~
    pDialog.update(50)
    launcher.update_rom_set(roms)
    pDialog.update(100)
    pDialog.close()
    kodi_notify('Rescaning of ROMs local artwork finished')

    return

# --- Scrape ROMs local artwork ---
def m_subcommand_scrape_local_artwork(launcher):
    kodi_dialog_OK('Feature not coded yet, sorry.')
    return

# --- Remove Remove dead/missing ROMs ROMs ---
def m_subcommand_remove_dead_roms(launcher):
    if launcher.has_nointro_xml():
        ret = kodi_dialog_yesno('This launcher has an XML DAT configured. Removing '
                                'dead ROMs will disable the DAT file. '
                                'Are you sure you want to remove missing/dead ROMs?')
    else:
        ret = kodi_dialog_yesno('Are you sure you want to remove missing/dead ROMs?')
        
    if not ret: 
        return

    # --- Load ROM scanner for this launcher ---
    romScanner  = self.romscannerFactory.create(launcher, None)
        
    # --- Remove dead ROMs ---
    #num_removed_roms = self._roms_delete_missing_ROMs(roms)
    roms = romScanner.cleanup()
    
    # --- If there is a No-Intro XML DAT configured remove it ---
    if launcher.has_nointro_xml():
        log_info('Deleting XML DAT file and forcing launcher to Normal view mode.')
        launcher.reset_nointro_xmldata()

    # ~~~ Save ROMs XML file ~~~
    # >> Launcher saved at the end of the function / launcher timestamp updated.
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Advanced Emulator Launcher', 'Saving ROM JSON database ...')
    launcher.update_rom_set(roms)
    pDialog.update(100)
    pDialog.close()
    launcher.set_number_of_roms(len(roms))
    return

# --- Import ROM metadata from NFO files ---
def m_subcommand_import_roms(launcher):

    # >> Load ROMs, iterate and import NFO files
    roms = launcher.get_roms()
    num_read_NFO_files = 0

    for rom in roms:
        nfo_filepath = rom.get_nfo_file()
        if rom.update_with_nfo_file(nfo_filepath, verbose = False):
            num_read_NFO_files += 1

    # >> Save ROMs XML file / Launcher/timestamp saved at the end of function
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Advanced Emulator Launcher', 'Saving ROM JSON database ...')
    
    launcher.update_rom_set(roms)

    pDialog.update(100)
    pDialog.close()
    kodi_notify('Imported {0} NFO files'.format(num_read_NFO_files))
    return

# --- Export ROM metadata to NFO files ---
def m_subcommand_export_roms(launcher):
    # >> Load ROMs for current launcher, iterate and write NFO files
    roms = launcher.get_roms()
    if not roms: return
    kodi_busydialog_ON()
    num_nfo_files = 0
    for rom in roms:
        # >> Skip No-Intro Added ROMs
        if not rom.get_filename(): continue
        fs_export_ROM_NFO(rom.get_data(), verbose = False)
        num_nfo_files += 1
    kodi_busydialog_OFF()
    # >> No need to save launchers XML / Update container
    kodi_notify('Created {0} NFO files'.format(num_nfo_files))
    return

# --- Delete ROMs metadata NFO files ---
def m_subcommand_delete_roms_nfo(launcher):
    # --- Get list of NFO files ---
    ROMPath_FileName = launcher.get_rom_path()
    log_verb('_command_edit_launcher() NFO dirname "{0}"'.format(ROMPath_FileName.getPath()))

    nfo_scanned_files = ROMPath_FileName.recursiveScanFilesInPath('*.nfo')
    if len(nfo_scanned_files) > 0:
        log_verb('_command_edit_launcher() Found {0} NFO files.'.format(len(nfo_scanned_files)))
        #for filename in nfo_scanned_files:
        #     log_verb('_command_edit_launcher() Found NFO file "{0}"'.format(filename))
        ret = kodi_dialog_yesno('Found {0} NFO files. Delete them?'.format(len(nfo_scanned_files)))
        if not ret: return
    else:
        kodi_dialog_OK('No NFO files found. Nothing to delete.')
        return

    # --- Delete NFO files ---
    for file in nfo_scanned_files:
        log_verb('_command_edit_launcher() RM "{0}"'.format(file))
        FileNameFactory.create(file).unlink()

    # >> No need to save launchers XML / Update container
    kodi_notify('Deleted {0} NFO files'.format(len(nfo_scanned_files)))
    return

# --- Empty Launcher ROMs ---
def m_subcommand_clear_roms(launcher):
    # If launcher is empty (no ROMs) do nothing
    num_roms = launcher.actual_amount_of_roms()
    if num_roms == 0:
        kodi_dialog_OK('Launcher has no ROMs. Nothing to do.')
        return

    # Confirm user wants to delete ROMs
    dialog = xbmcgui.Dialog()
    ret = dialog.yesno('Advanced Emulator Launcher',
                        "Launcher '{0}' has {1} ROMs. Are you sure you want to delete them "
                        "from AEL database?".format(launcher.get_name(), num_roms))
    if not ret: return

    # --- If there is a No-Intro XML DAT configured remove it ---
    launcher.reset_nointro_xmldata()

    # Just remove ROMs database files. Keep the value of roms_base_noext to be reused 
    # when user add more ROMs.
    launcher.clear_roms()
    kodi_refresh_container()
    kodi_notify('Cleared ROMs from launcher database')
    return

# --- Choose default ROMs assets/artwork ---
def m_subcommand_set_roms_default_artwork(launcher):
    list_items = {}
    assets = self.assetFactory.get_assets_by(DEFAULTABLE_ROM_ASSETLIST)
    mappable_assets = self.assetFactory.get_assets_by(MAPPBLE_ROM_ASSET_LIST)

    for asset_info in assets:
        current_default_key = launcher.get_rom_asset_default(asset_info)
        if current_default_key and current_default_key != '':
            current_default_key = ASSET_KEYS_TO_CONSTANTS[current_default_key]
            current_default = self.assetFactory.get_asset_info(current_default_key)
            list_items[asset_info] = 'Choose asset for {0} (currently {1})'.format(asset_info.name, current_default.name)
        else:
            list_items[asset_info] = 'Choose asset for {0} (currently not set)'.format(asset_info.name)

    dialog = DictionaryDialog()
    selected_asset = dialog.select('Edit ROMs default Assets/Artwork', list_items)
        
    if selected_asset is None:
        return

    # --- Launcher status (finished [bool]) ---
    type_nb = type_nb + 1
    if type == type_nb:
        finished = self.launchers[launcherID]['finished']
        finished = False if finished else True
        finished_display = 'Finished' if finished == True else 'Unfinished'
        self.launchers[launcherID]['finished'] = finished
        kodi_dialog_OK('Launcher "{0}" status is now {1}'.format(self.launchers[launcherID]['m_name'], finished_display))

    # --- Launcher Manage ROMs menu option ---
    # ONLY for ROM launchers, not for standalone launchers
    if self.launchers[launcherID]['rompath'] != '':
        type_nb = type_nb + 1
        if type == type_nb:
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Manage ROMs',
                                  ['Choose ROMs default artwork ...',
                                   'Manage ROMs asset directories ...',
                                   'Rescan ROMs local artwork',
                                   'Scrape ROMs artwork',
                                   'Remove dead/missing ROMs',
                                   'Import ROMs metadata from NFO files',
                                   'Export ROMs metadata to NFO files',
                                   'Delete ROMs NFO files',
                                   'Clear ROMs from launcher' ])
            if type2 < 0: return # User canceled select dialog

            # --- Choose default ROMs assets/artwork ---
            if type2 == 0:
                launcher        = self.launchers[launcherID]
                asset_icon_str      = assets_get_asset_name_str(launcher['roms_default_icon'])
                asset_fanart_str    = assets_get_asset_name_str(launcher['roms_default_fanart'])
                asset_banner_str    = assets_get_asset_name_str(launcher['roms_default_banner'])
                asset_poster_str    = assets_get_asset_name_str(launcher['roms_default_poster'])
                asset_clearlogo_str = assets_get_asset_name_str(launcher['roms_default_clearlogo'])

                # >> Execute select dialog
                dialog = xbmcgui.Dialog()
                type3 = dialog.select('Edit ROMs default Assets/Artwork',
                                      ['Choose asset for Icon (currently {0})'.format(asset_icon_str),
                                       'Choose asset for Fanart (currently {0})'.format(asset_fanart_str),
                                       'Choose asset for Banner (currently {0})'.format(asset_banner_str),
                                       'Choose asset for Poster (currently {0})'.format(asset_poster_str),
                                       'Choose asset for Clearlogo (currently {0})'.format(asset_clearlogo_str)])
                if type3 < 0: return

                # >> Krypton feature: User preselected item in select() dialog.
                ROM_asset_str_list = ['Title', 'Snap', 'Boxfront', 'Boxback', 'Cartridge',
                                      'Fanart', 'Banner', 'Clearlogo', 'Flyer', 'Map']
                if type3 == 0:
                    p_idx = assets_get_ROM_mapped_asset_idx(launcher, 'roms_default_icon')
                    type_s = xbmcgui.Dialog().select('Choose ROMs default asset for Icon',
                                                     ROM_asset_str_list, preselect = p_idx)
                    if type_s < 0: return
                    assets_choose_ROM_mapped_artwork(launcher, 'roms_default_icon', type_s)
                    asset_name = assets_get_asset_name_str(launcher['roms_default_icon'])
                    kodi_notify('ROMs Icon mapped to {0}'.format(asset_name))
                elif type3 == 1:
                    p_idx = assets_get_ROM_mapped_asset_idx(launcher, 'roms_default_fanart')
                    type_s = xbmcgui.Dialog().select('Choose ROMs default asset for Fanart',
                                                     ROM_asset_str_list, preselect = p_idx)
                    if type_s < 0: return
                    assets_choose_ROM_mapped_artwork(launcher, 'roms_default_fanart', type_s)
                    asset_name = assets_get_asset_name_str(launcher['roms_default_fanart'])
                    kodi_notify('ROMs Fanart mapped to {0}'.format(asset_name))
                elif type3 == 2:
                    p_idx = assets_get_ROM_mapped_asset_idx(launcher, 'roms_default_banner')
                    type_s = xbmcgui.Dialog().select('Choose ROMS default asset for Banner',
                                                     ROM_asset_str_list, preselect = p_idx)
                    if type_s < 0: return
                    assets_choose_ROM_mapped_artwork(launcher, 'roms_default_banner', type_s)
                    asset_name = assets_get_asset_name_str(launcher['roms_default_banner'])
                    kodi_notify('ROMs Banner mapped to {0}'.format(asset_name))
                elif type3 == 3:
                    p_idx = assets_get_ROM_mapped_asset_idx(launcher, 'roms_default_poster')
                    type_s = xbmcgui.Dialog().select('Choose ROMS default asset for Poster',
                                                     ROM_asset_str_list, preselect = p_idx)
                    if type_s < 0: return
                    assets_choose_ROM_mapped_artwork(launcher, 'roms_default_poster', type_s)
                    asset_name = assets_get_asset_name_str(launcher['roms_default_poster'])
                    kodi_notify('ROMs Poster mapped to {0}'.format(asset_name))
                elif type3 == 4:
                    p_idx = assets_get_ROM_mapped_asset_idx(launcher, 'roms_default_clearlogo')
                    type_s = xbmcgui.Dialog().select('Choose ROMs default asset for Clearlogo',
                                                     ROM_asset_str_list, preselect = p_idx)
                    if type_s < 0: return
                    assets_choose_ROM_mapped_artwork(launcher, 'roms_default_clearlogo', type_s)
                    asset_name = assets_get_asset_name_str(launcher['roms_default_clearlogo'])
                    kodi_notify('ROMs Clearlogo mapped to {0}'.format(asset_name))

            # --- Manage ROM Asset directories ---
            elif type2 == 1:
                launcher = self.launchers[launcherID]
                dialog = xbmcgui.Dialog()
                type3 = dialog.select('ROM Asset directories ',
                                      ["Change Titles path: '{0}'".format(launcher['path_title']),
                                       "Change Snaps path: '{0}'".format(launcher['path_snap']),
                                       "Change Fanarts path '{0}'".format(launcher['path_fanart']),
                                       "Change Banners path: '{0}'".format(launcher['path_banner']),
                                       "Change Clearlogos path: '{0}'".format(launcher['path_clearlogo']),
                                       "Change Boxfronts path: '{0}'".format(launcher['path_boxfront']),
                                       "Change Boxbacks path: '{0}'".format(launcher['path_boxback']),
                                       "Change Cartridges path: '{0}'".format(launcher['path_cartridge']),
                                       "Change Flyers path: '{0}'".format(launcher['path_flyer']),
                                       "Change Maps path: '{0}'".format(launcher['path_map']),
                                       "Change Manuals path: '{0}'".format(launcher['path_manual']),
                                       "Change Trailers path: '{0}'".format(launcher['path_trailer']) ])

                if type3 == 0:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Titles path', 'files', '', False, False, launcher['path_title']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_title'] = dir_path
                elif type3 == 1:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Snaps path', 'files', '', False, False, launcher['path_snap']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_snap'] = dir_path
                elif type3 == 2:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Fanarts path', 'files', '', False, False, launcher['path_fanart']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_fanart'] = dir_path
                elif type3 == 3:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Banners path', 'files', '', False, False, launcher['path_banner']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_banner'] = dir_path
                elif type3 == 4:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Clearlogos path', 'files', '', False, False, launcher['path_clearlogo']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_clearlogo'] = dir_path
                elif type3 == 5:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Boxfronts path', 'files', '', False, False, launcher['path_boxfront']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_boxfront'] = dir_path
                elif type3 == 6:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Boxbacks path', 'files', '', False, False, launcher['path_boxback']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_boxback'] = dir_path
                elif type3 == 7:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Cartridges path', 'files', '', False, False, launcher['path_cartridge']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_cartridge'] = dir_path
                elif type3 == 8:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Flyers path', 'files', '', False, False, launcher['path_flyer']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_flyer'] = dir_path
                elif type3 == 9:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Maps path', 'files', '', False, False, launcher['path_map']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_map'] = dir_path
                elif type3 == 10:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Manuals path', 'files', '', False, False, launcher['path_manual']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_manual'] = dir_path
                elif type3 == 11:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Trailers path', 'files', '', False, False, launcher['path_trailer']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_trailer'] = dir_path
                # >> User canceled select dialog
                elif type3 < 0: return

                # >> Check for duplicate paths and warn user.
                duplicated_name_list = asset_get_duplicated_dir_list(self.launchers[launcherID])
                if duplicated_name_list:
                    duplicated_asset_srt = ', '.join(duplicated_name_list)
                    kodi_dialog_OK('Duplicated asset directories: {0}. '.format(duplicated_asset_srt) +
                                   'AEL will refuse to add/edit ROMs if there are duplicate asset directories.')

            # --- Rescan ROMs local artwork ---
            # >> A) First, local assets are searched for every ROM based on the filename.
            # >> B) Next, missing assets are searched in the Parent/Clone group using the files
            #       found in the previous step. This is much faster than searching for files again.
            #
            elif type2 == 2:
                log_info('_command_edit_launcher() Rescanning local assets ...')
                launcher = self.launchers[launcherID]

                # ~~~ Check asset dirs and disable scanning for unset dirs ~~~
                (enabled_asset_list, unconfigured_name_list) = asset_get_configured_dir_list(launcher)
                if unconfigured_name_list:
                    unconfigure_asset_srt = ', '.join(unconfigured_name_list)
                    kodi_dialog_OK('Assets directories not set: {0}. '.format(unconfigure_asset_srt) +
                                   'Asset scanner will be disabled for this/those.')

                # ~~~ Ensure there is no duplicate asset dirs ~~~
                # >> Cancel scanning if duplicates found
                duplicated_name_list = asset_get_duplicated_dir_list(launcher)
                if duplicated_name_list:
                    duplicated_asset_srt = ', '.join(duplicated_name_list)
                    log_info('Duplicated asset dirs: {0}'.format(duplicated_asset_srt))
                    kodi_dialog_OK('Duplicated asset directories: {0}. '.format(duplicated_asset_srt) +
                                   'Change asset directories before continuing.')
                    return
                else:
                    log_info('No duplicated asset dirs found')

                # --- Create a cache of assets ---
                # >> misc_add_file_cache() creates a set with all files in a given directory.
                # >> That set is stored in a function internal cache associated with the path.
                # >> Files in the cache can be searched with misc_search_file_cache()
                pDialog = xbmcgui.DialogProgress()
                pDialog.create('Advanced Emulator Launcher', 'Scanning files in asset directories ...')
                for i, asset_kind in enumerate(ROM_ASSET_LIST):
                    AInfo = assets_get_info_scheme(asset_kind)
                    misc_add_file_cache(launcher[AInfo.path_key])
                    pDialog.update((100*i)/len(ROM_ASSET_LIST))
                pDialog.update(100)
                pDialog.close()

    default_key = launcher.get_rom_asset_default(selected_asset)
    default_key = ASSET_KEYS_TO_CONSTANTS[default_key]
    default_kind = None

    # >> Build ListItem of assets that can be mapped.
    mappable_asset_list_items = {}
    for mappable_asset in mappable_assets:
        mappable_asset_list_items[mappable_asset] = mappable_asset.name
        if mappable_asset.kind == default_key:
            default_kind = mappable_asset

    # >> Krypton feature: User preselected item in select() dialog.
    selected_mappable_asset = dialog.select('Choose ROMs default asset for {}'.format(selected_asset.name), mappable_asset_list_items, default_kind)
    if selected_mappable_asset is None or selected_mappable_asset == default_kind:   
        self._subcommand_set_roms_default_artwork(launcher)                
        return
                    
    launcher.set_default_rom_asset(selected_asset, selected_mappable_asset)
    g_LauncherRepository.save(launcher)

    kodi_notify('ROMs {0} mapped to {1}'.format(selected_asset.name, selected_mappable_asset.name))
      
    self._subcommand_set_roms_default_artwork(launcher)
    return

def m_subcommand_set_rom_asset_dirs(launcher):
    list_items = {}
    assets = self.assetFactory.get_all()

    # --- Scrape ROMs artwork ---
    # >> Mimic what the ROM scanner does. Use same settings as the ROM scanner.
    # >> Like the ROM scanner, only scrape artwork not found locally.
    # elif type2 == 3:
    #     kodi_dialog_OK('WIP feature not coded yet, sorry.')
    #     return

    for asset_info in assets:
        path = launcher.get_asset_path(asset_info)
        if path:
            list_items[asset_info] = "Change {0} path: '{1}'".format(asset_info.plural, path.getPath())


    dialog = DictionaryDialog()
    selected_asset = dialog.select('ROM Asset directories ', list_items)

    if selected_asset is None:    
        return

    selected_asset_path = launcher.get_asset_path(selected_asset)
    dialog = xbmcgui.Dialog()
    dir_path = dialog.browse(0, 'Select {0} path'.format(selected_asset.plural), 'files', '', False, False, selected_asset_path.getPath()).decode('utf-8')
    if not dir_path or dir_path == selected_asset_path.getPath():  
        self._subcommand_set_rom_asset_dirs(launcher)
        return
            
    launcher.set_asset_path(selected_asset, dir_path)
    g_LauncherRepository.save(launcher)
            
    # >> Check for duplicate paths and warn user.
    duplicated_name_list = launcher.get_duplicated_asset_dirs()
    if duplicated_name_list:
        duplicated_asset_srt = ', '.join(duplicated_name_list)
        kodi_dialog_OK('Duplicated asset directories: {0}. '.format(duplicated_asset_srt) +
                        'AEL will refuse to add/edit ROMs if there are duplicate asset directories.')

    kodi_notify('Changed rom asset dir for {0} to {1}'.format(selected_asset.name, dir_path))
    self._subcommand_set_rom_asset_dirs(launcher)
    return

# --- Edit status ---
def m_subcommand_change_rom_status(launcher, rom):
    rom.change_finished_status()
    launcher.save_rom(rom)
    kodi_dialog_OK('ROM "{0}" status is now {1}'.format(rom.get_name(), rom.get_state()))

# --- Edit ROM metadata ---
def m_subcommand_edit_rom_metadata(launcher, rom):
    options = rom.get_metadata_edit_options()

    # >> Make a list of available metadata scrapers
    # todo: make a separate menu item 'Scrape' with after that a list to select instead of merging it now with other options.
    for scrap_obj in scrapers_metadata:
        options['SCRAPE_' + scrap_obj.name] = 'Scrape metadata from {0} ...'.format(scrap_obj.name)
        log_verb('Added metadata scraper {0}'.format(scrap_obj.name))

    dialog = DictionaryDialog()
    selected_option = dialog.select('Modify ROM metadata', options)
     
    if selected_option is None:
        log_debug('_subcommand_edit_rom_metadata(): Selected option = NONE')
        return self._command_edit_rom(launcher.get_category_id(), launcher.get_id(), rom.get_id())

    self.run_sub_command(selected_option, None, launcher, rom)
    self._subcommand_edit_rom_metadata(launcher, rom)
    return

# --- Edit of the rom title ---
def m_subcommand_edit_rom_title(launcher, rom):
    if self._text_edit_rom_metadata('Title', rom.get_name, rom.set_name):
        launcher.save_rom(rom)

# --- Edition of the rom release year ---    
def m_subcommand_edit_rom_release_year(launcher, rom):
    if self._text_edit_rom_metadata('Release Year', rom.get_releaseyear, rom.update_releaseyear):
        launcher.save_rom(rom)

# --- Edition of the rom game genre ---
def m_subcommand_edit_rom_genre(launcher, rom):
    if self._text_edit_rom_metadata('genre', rom.get_genre, rom.update_genre):
        launcher.save_rom(rom)

# --- Edition of the rom developer ---
def m_subcommand_edit_rom_developer(launcher, rom):
    if self._text_edit_rom_metadata('developer', rom.get_developer, rom.update_developer):
        launcher.save_rom(rom)

# --- Edition of launcher NPlayers ---
def m_subcommand_edit_rom_number_of_players(launcher, rom):
    # >> Show a dialog select with the most used NPlayer entries, and have one option
    # >> for manual entry.
    dialog = xbmcgui.Dialog()

    menu_list = ['Not set', 'Manual entry'] + NPLAYERS_LIST
    np_idx = dialog.select('Edit ROM NPlayers', menu_list)

    if np_idx < 0:
        return

    if np_idx == 0:
        rom.set_number_of_players('')
        launcher.save_rom(rom)
        kodi_notify('Launcher NPlayers change to Not Set')
        return

    if np_idx == 1:
        # >> Manual entry. Open a text entry dialog.
        
        if self._text_edit_rom_metadata('NPlayers', rom.get_number_of_players, rom.set_number_of_players):
            launcher.save_rom(rom)
        return

    list_idx = np_idx - 2
    rom.set_number_of_players(NPLAYERS_LIST[list_idx])
    launcher.save_rom(rom)
    kodi_notify('Changed Launcher NPlayers')

# --- Edition of launcher ESRB rating ---
def m_subcommand_edit_rom_esrb_rating(launcher, rom):
    # >> Show a dialog select with the available ratings
    # >> Kodi Krypton: preselect current rating in select list        

    if self._list_edit_rom_metadata('ESRB rating', ESRB_LIST, -1, rom.get_esrb_rating, rom.set_esrb_rating):
        launcher.save_rom(rom)

# --- Edition of the ROM rating ---
def m_subcommand_edit_rom_rating(launcher, rom):
    options =  {}
    options[-1] = 'Not set'
    options[0] = 'Rating 0'
    options[1] = 'Rating 1'
    options[2] = 'Rating 2'
    options[3] = 'Rating 3'
    options[4] = 'Rating 4'
    options[5] = 'Rating 5'
    options[6] = 'Rating 6'
    options[7] = 'Rating 7'
    options[8] = 'Rating 8'
    options[9] = 'Rating 9'
    options[10] = 'Rating 10'

    if self._list_edit_rom_metadata('Rating', options, -1, rom.get_rating, rom.update_rating):
        launcher.save_rom(rom)

# --- Edit ROM description (plot) ---
def m_subcommand_edit_rom_description(launcher, rom):
    if self._text_edit_rom_metadata('plot', rom.get_plot, rom.update_plot):
        launcher.save_rom(rom)

# --- Import of the rom game plot from TXT file ---
def m_subcommand_import_rom_plot_from_txt(launcher, rom):
    dialog = xbmcgui.Dialog()
    text_file = dialog.browse(1, 'Select description file (TXT|DAT)', 
                                'files', '.txt|.dat', False, False).decode('utf-8')
    text_file_path = FileNameFactory.create(text_file)
    if text_file_path.exists():
        file_data = self._gui_import_TXT_file(text_file_path)
        rom.set_plot(file_data)
        launcher.save_rom(rom)
        kodi_notify('Imported ROM Plot')
        return
    desc_str = text_limit_string(rom.get_plot(), PLOT_STR_MAXSIZE)
    kodi_dialog_OK("Launcher plot '{0}' not changed".format(desc_str))
    return

# --- Import ROM metadata from NFO file ---
def m_subcommand_import_rom_metadata(launcher, rom):
    if launcher.get_id() == VLAUNCHER_FAVOURITES_ID: 
        kodi_dialog_OK('Importing NFO file is not allowed for ROMs in Favourites.')
        return
        
    nfo_filepath = rom.get_nfo_file()
    if rom.update_with_nfo_file(nfo_filepath):
        launcher.save_rom(rom)
    return

# --- Export ROM metadata to NFO file ---
def m_subcommand_export_rom_metadata(launcher, rom):

    if launcher.get_id() == VLAUNCHER_FAVOURITES_ID:
        kodi_dialog_OK('Exporting NFO file is not allowed for ROMs in Favourites.')
        return

    fs_export_ROM_NFO(rom.get_data())
    return

# --- Scrape ROM metadata ---
def m_subcommand_scrape_rom_metadata(launcher, rom, command):
    scraper_obj_name = command.replace('SCRAPE_', '')
    scraper_obj = filter(lambda x: x.name == scraper_obj_name, scrapers_metadata)[0]
    log_debug('_subcommand_scrape_rom_metadata() User chose scraper "{0}"'.format(scraper_obj.name))
    
    # --- Initialise asset scraper ---
    scraper_obj.set_addon_dir(CURRENT_ADDON_DIR.getPath())
    log_debug('_subcommand_scrape_rom_metadata() Initialised scraper "{0}"'.format(scraper_obj.name))
    
    # >> If this returns False there were no changes so no need to save ROMs JSON.
    if self._gui_scrap_rom_metadata(launcher, rom, scraper_obj): 
        launcher.save_rom(rom)

    return

# --- Edit Launcher Assets/Artwork ---
def m_subcommand_edit_rom_assets(launcher, rom):
    asset_infos = self.assetFactory.get_asset_kinds_for_roms()
    list_items = []

    for asset_info in asset_infos:
        # >> Create ListItems and label2
        has_asset   = rom.has_asset(asset_info)
        label1_text = 'Edit {} ...'.format(asset_info.get_description())
        label2_text = rom.get_asset(asset_info) if has_asset else 'Not set'
        list_item   = xbmcgui.ListItem(label = label1_text, label2 = label2_text)
            
        # >> Set artwork with setArt()
        item_img = 'DefaultAddonNone.png'
        if has_asset:
            item_path = rom.get_asset_file(asset_info)
            if item_path.is_video_file():
                item_img = 'DefaultAddonVideo.png'
            if item_path.is_document():
                item_img = 'DefaultAddonImages.png'
            else:
                item_img = item_path.getOriginalPath()

        list_item.setArt({'icon' : item_img})
        list_items.append(list_item)

    # >> Execute select dialog
    selected_option = xbmcgui.Dialog().select('Edit ROM Assets/Artwork', list = list_items, useDetails = True)
    if selected_option < 0: 
        return self._command_edit_rom(launcher.get_category_id(), launcher.get_id(), rom.get_id())
 
    selected_asset_info = asset_infos[selected_option]
    # --- Edit Assets ---
    # >> If this function returns False no changes were made. No need to save categories
    # >> XML and update container.
    if self._gui_edit_asset(KIND_ROM, selected_asset_info.kind, rom.get_data(), launcher.get_category_id(), launcher.get_id()): 
        launcher.save_rom(rom)

    self._subcommand_edit_rom_assets(launcher, rom)
    return

# --- Advanced ROM Modifications ---
def m_subcommand_advanced_rom_modifications(launcher, rom):
    options = rom.get_advanced_modification_options()

    dialog = DictionaryDialog()
    selected_option = dialog.select('Advanced ROM Modifications', options)
     
    if selected_option is None:
        log_debug('_subcommand_advanced_rom_modifications(): Selected option = NONE')
        self._command_edit_rom(launcher.get_category_id(), launcher.get_id(), rom.get_id())
        return
            
    log_debug('_subcommand_advanced_rom_modifications(): Selected option = {0}'.format(selected_option))
    self.run_sub_command(selected_option, None, launcher, rom)
    self._subcommand_advanced_rom_modifications(launcher, rom)
    return

# >> Change ROM file
def m_subcommand_change_rom_file(launcher, rom):
    # >> Abort if multidisc ROM
    if rom.has_multiple_disks():
        kodi_dialog_OK('Edition of multidisc ROMs not supported yet.')
        return

    filename = rom.get_filename()
    romext   = launcher.get_rom_extensions_combined()
    item_file = xbmcgui.Dialog().browse(1, 'Select the file', 'files', '.' + romext.replace('|', '|.'),
                                        False, False, filename).decode('utf-8')
    if not item_file: return

    item_file_FN = FileFactory.create(item_file)
    rom.set_filename(item_file_FN)
    launcher.save_rom(rom)

# >> Alternative launcher application file path
def m_subcommand_edit_rom_alternative_application(launcher, rom):
    filter_str = '.bat|.exe|.cmd' if is_windows() else ''
    altapp = xbmcgui.Dialog().browse(1, 'Select ROM custom launcher application',
                                        'files', filter_str,
                                        False, False, rom.get_alternative_application()).decode('utf-8')
    # Returns empty browse if dialog was canceled.
    if not altapp: 
        return

    rom.set_alternative_application(altapp)
    launcher.save_rom(rom)

# >> Alternative launcher arguments
def m_subcommand_edit_rom_alternative_arguments(launcher, rom):
    if self._text_edit_rom_metadata('altarg', rom.get_alternative_arguments, rom.set_alternative_arguments):
        launcher.save_rom(rom)

# --- Delete ROM ---
def m_subcommand_delete_rom(launcher, rom):

    if launcher.has_nointro_xml() and rom.get_nointro_status() == NOINTRO_STATUS_MISS:
        kodi_dialog_OK('You are trying to remove a Missing ROM. You cannot delete '
                        'a ROM that does not exist! If you want to get rid of all missing '
                        'ROMs then delete the XML DAT file.')
        return

    log_info('_command_remove_rom() Deleting ROM from {0} (id {1})'.format(launcher.get_name(), rom.get_id()))

    # --- Confirm deletion ---
    msg_str = 'Are you sure you want to delete it from "{0}"?'.format(launcher.get_name())
    ret = kodi_dialog_yesno('ROM "{0}". {1}'.format(rom.get_name(), msg_str))
    if not ret: return

    launcher.remove_rom(rom.get_id())

    # --- If there is a No-Intro XML configured audit ROMs ---
    if launcher.has_nointro_xml():
        log_info('No-Intro/Redump DAT configured. Starting ROM audit ...')
        nointro_xml_FN = launcher.get_nointro_xml_filepath()
        if not self._roms_update_NoIntro_status(launcher.get_data(), roms, nointro_xml_FN):
            launcher.reset_nointro_xmldata()
            kodi_notify_warn('Error auditing ROMs. XML DAT file unset.')

    # --- Notify user ---
    kodi_refresh_container()
    kodi_notify('Deleted ROM {0}'.format(rom.get_name()))

# --- Manage Favourite/Collection ROM object (ONLY for Favourite/Collection ROMs) ---
def m_subcommand_manage_favourite_rom(launcher, rom):
    dialog = xbmcgui.Dialog()
    type2 = dialog.select('Manage ROM object',
                          ['Choose another parent ROM (launcher info only) ...', # 0
                           'Choose another parent ROM (update all) ...',         # 1
                           'Copy launcher info from parent ROM',                # 2
                           'Copy metadata from parent ROM',                     # 3
                           'Copy assets/artwork from parent ROM',               # 4
                           'Copy all from parent ROM',                          # 5
                           'Manage default Assets/Artwork ...'])
    if type2 < 0: return

    # --- Choose another parent ROM ---
    if type2 == 0 or type2 == 1:
        # --- STEP 1: select new launcher ---
        rom_launchers = g_LauncherRepository.find_by_launcher_type(LAUNCHER_ROM)
        # todo: should we support other rom launchers too?

        # >> Order alphabetically both lists
        sorted_rom_launchers = sort(rom_launcher, key = lambda l: l.get_name())
        launcher_names = (l.get_name() for l in rom_launchers)

        dialog = xbmcgui.Dialog()
        selected_launcher_index = dialog.select('New launcher for {0}'.format(rom.get_name()), launcher_names)
        if selected_launcher_index < 0: return

        # --- STEP 2: select ROMs in that launcher ---
        selected_launcher   = sorted_rom_launchers[selected_launcher_index]
        launcher_roms       = selected_launcher.get_roms()
        if not launcher_roms: return
        roms_IDs = []
        roms_names = []
        for launcher_rom in launcher_roms:
            # ROMs with nointro_status = 'Miss' are invalid! Do not add to the list
            nointro_stat = launcher_rom.get_nointro_status()
            if nointro_stat == 'Miss': continue
            roms_IDs.append(rom_id)
            roms_names.append(launcher_roms[rom_id]['m_name'])
        sorted_idx = [i[0] for i in sorted(enumerate(roms_names), key=lambda x:x[1])]
        roms_IDs   = [roms_IDs[i] for i in sorted_idx]
        roms_names = [roms_names[i] for i in sorted_idx]
        selected_rom = dialog.select('New ROM for Favourite {0}'.format(rom.get_name()), roms_names)
        if selected_rom < 0 : return

        # >> Collect ROM object.
        old_fav_rom_ID  = rom.get_id()
        new_fav_rom_ID  = roms_IDs[selected_rom]
        old_fav_rom     = rom.get_name()
        parent_rom      = selected_launcher.select_rom(new_fav_rom_ID)
        parent_launcher = selected_launcher.get_data()

        # >> Check that the selected ROM ID is not already in Favourites
        if new_fav_rom_ID in roms:
            kodi_dialog_OK('Selected ROM already in Favourites. Exiting.')
            return

        # >> Relink Favourite ROM. Removed old Favourite before inserting new one.
        if type2 == 0:
            log_info('_command_edit_ROM() Relinking ROM (launcher info only)')
            new_fav_rom = fs_repair_Favourite_ROM(0, old_fav_rom, parent_rom, parent_launcher)
        elif type2 == 1:
            log_info('_command_edit_ROM() Relinking ROM (update all)')
            new_fav_rom = fs_repair_Favourite_ROM(3, old_fav_rom, parent_rom, parent_launcher)
        else:
            kodi_dialog_OK('Manage ROM object, relink, wrong type2 = {0}. Please report this bug.'.format(type2))
            return
        if categoryID == VCATEGORY_COLLECTIONS_ID:
            # >> Insert the new ROM in a specific position of the OrderedDict.
            old_fav_position = roms.keys().index(old_fav_rom_ID)
            dic_index = 0
            new_roms_orderded_dict = roms.__class__()
            for key, value in roms.items():
                # >> Replace old ROM by new ROM
                if dic_index == old_fav_position: new_roms_orderded_dict[new_fav_rom['id']] = new_fav_rom
                else:                             new_roms_orderded_dict[key] = value
                dic_index += 1
            roms.clear()
            roms.update(new_roms_orderded_dict)
        else:
            roms.pop(old_fav_rom_ID)
            roms[new_fav_rom['id']] = new_fav_rom

        # >> Notify user
        if categoryID == VCATEGORY_FAVOURITES_ID:    kodi_notify('Relinked Favourite ROM')
        elif categoryID == VCATEGORY_COLLECTIONS_ID: kodi_notify('Relinked Collection ROM')

    # --- Copy launcher info from parent ROM ---
    # --- Copy metadata from parent ROM ---
    # --- Copy assets/artwork from parent ROM ---
    # --- Copy all from parent ROM ---
    elif type2 == 2 or type2 == 3 or type2 == 4 or type2 == 5:
        # >> Get launcher and parent ROM
        # >> Check Favourite ROM is linked (parent ROM exists)
        fav_rom         = roms[romID]
        fav_launcher_id = fav_rom['launcherID']
        fav_launcher = g_LauncherRepository.find(fav_launcher_id)

        if fav_launcher is None:
            kodi_dialog_OK('Parent Launcher not found. '
                            'Relink this ROM before copying stuff from parent.')
            return

        parent_launcher = fav_launcher.get_data()
        launcher_roms   = fs_load_ROMs_JSON(ROMS_DIR, parent_launcher)
        if romID not in launcher_roms:
            kodi_dialog_OK('Parent ROM not found in Launcher. '
                            'Relink this ROM before copying stuff from parent.')
            return
        parent_rom = launcher_roms[romID]

        # >> Relink Favourite ROM. Removed old Favourite before inserting new one.
        if type2 == 2:
            info_str = 'launcher info'
            fs_aux_copy_ROM_launcher_info(parent_launcher, fav_rom)
        elif type2 == 3:
            info_str = 'metadata'
            fs_aux_copy_ROM_metadata(parent_rom, fav_rom)
        elif type2 == 4:
            info_str = 'assets/artwork'
            fs_aux_copy_ROM_artwork(parent_launcher, parent_rom, fav_rom)
        elif type2 == 5:
            info_str = 'all info'
            fs_aux_copy_ROM_launcher_info(parent_launcher, fav_rom)
            fs_aux_copy_ROM_metadata(parent_rom, fav_rom)
            fs_aux_copy_ROM_artwork(parent_launcher, parent_rom, fav_rom)
        else:
            kodi_dialog_OK('Manage ROM object, copy info, wrong type2 = {0}. Please report this bug.'.format(type2))
            return

        # --- Scrap ROM metadata ---
        # elif type2 >= 11:
        #    # --- Use the scraper chosen by user ---
        #    scraper_index = type2 - 11
        #    scraper_obj   = scraper_obj_list[scraper_index]
        #    log_debug('_command_edit_rom() Scraper index {0}'.format(scraper_index))
        #    log_debug('_command_edit_rom() User chose scraper "{0}"'.format(scraper_obj.name))

        #    # --- Initialise asset scraper ---
        #    scraper_obj.set_addon_dir(g_PATHS.ADDON_CODE_DIR.getPath())
        #    log_debug('_command_edit_rom() Initialised scraper "{0}"'.format(scraper_obj.name))

        #    # >> If this returns False there were no changes so no need to save ROMs JSON.
        #    if not self._gui_scrap_rom_metadata(categoryID, launcherID, romID, roms, scraper_obj): return

        # >> Notify user
        if categoryID == VCATEGORY_FAVOURITES_ID:    kodi_notify('Updated Favourite ROM {0}'.format(info_str))
        elif categoryID == VCATEGORY_COLLECTIONS_ID: kodi_notify('Updated Collection ROM {0}'.format(info_str))

    # --- Choose default Favourite/Collection assets/artwork ---
    elif type2 == 6:
        rom = roms[romID]

        # >> Label1 an label2
        asset_icon_str     = assets_get_asset_name_str(rom['roms_default_thumb'])
        asset_fanart_str    = assets_get_asset_name_str(rom['roms_default_fanart'])
        asset_banner_str    = assets_get_asset_name_str(rom['roms_default_banner'])
        asset_poster_str    = assets_get_asset_name_str(rom['roms_default_poster'])
        asset_clearlogo_str = assets_get_asset_name_str(rom['roms_default_clearlogo'])
        label2_thumb        = rom[rom['roms_default_thumb']]     if rom[rom['roms_default_thumb']]     else 'Not set'
        label2_fanart       = rom[rom['roms_default_fanart']]    if rom[rom['roms_default_fanart']]    else 'Not set'
        label2_banner       = rom[rom['roms_default_banner']]    if rom[rom['roms_default_banner']]    else 'Not set'
        label2_poster       = rom[rom['roms_default_poster']]    if rom[rom['roms_default_poster']]    else 'Not set'
        label2_clearlogo    = rom[rom['roms_default_clearlogo']] if rom[rom['roms_default_clearlogo']] else 'Not set'
        icon_listitem       = xbmcgui.ListItem(label = 'Choose asset for Icon (currently {0})'.format(asset_icon_str),
                                                label2 = label2_thumb)
        fanart_listitem     = xbmcgui.ListItem(label = 'Choose asset for Fanart (currently {0})'.format(asset_fanart_str),
                                                label2 = label2_fanart)
        banner_listitem     = xbmcgui.ListItem(label = 'Choose asset for Banner (currently {0})'.format(asset_banner_str),
                                                label2 = label2_banner)
        poster_listitem     = xbmcgui.ListItem(label = 'Choose asset for Poster (currently {0})'.format(asset_poster_str),
                                                label2 = label2_poster)
        clearlogo_listitem  = xbmcgui.ListItem(label = 'Choose asset for Clearlogo (currently {0})'.format(asset_clearlogo_str),
                                                label2 = label2_clearlogo)

        # >> Asset image
        img_icon            = rom[rom['roms_default_thumb']]     if rom[rom['roms_default_thumb']]     else 'DefaultAddonNone.png'
        img_fanart          = rom[rom['roms_default_fanart']]    if rom[rom['roms_default_fanart']]    else 'DefaultAddonNone.png'
        img_banner          = rom[rom['roms_default_banner']]    if rom[rom['roms_default_banner']]    else 'DefaultAddonNone.png'
        img_poster          = rom[rom['roms_default_poster']]    if rom[rom['roms_default_poster']]    else 'DefaultAddonNone.png'
        img_clearlogo       = rom[rom['roms_default_clearlogo']] if rom[rom['roms_default_clearlogo']] else 'DefaultAddonNone.png'
        icon_listitem.setArt({'icon' : img_icon})
        fanart_listitem.setArt({'icon' : img_fanart})
        banner_listitem.setArt({'icon' : img_banner})
        poster_listitem.setArt({'icon' : img_poster})
        clearlogo_listitem.setArt({'icon' : img_clearlogo})

        # >> Execute select dialog
        listitems = [icon_listitem, fanart_listitem, banner_listitem,
                        poster_listitem, clearlogo_listitem]
        type3 = dialog.select('Edit ROMs default Assets/Artwork', list = listitems, useDetails = True)
        if type3 < 0: return

        ROMs_asset_ListItem_list = [
            xbmcgui.ListItem(label = 'Title',     label2 = rom['s_title'] if rom['s_title'] else 'Not set'),
            xbmcgui.ListItem(label = 'Snap',      label2 = rom['s_snap'] if rom['s_snap'] else 'Not set'),
            xbmcgui.ListItem(label = 'Fanart',    label2 = rom['s_fanart'] if rom['s_fanart'] else 'Not set'),
            xbmcgui.ListItem(label = 'Banner',    label2 = rom['s_banner'] if rom['s_banner'] else 'Not set'),
            xbmcgui.ListItem(label = 'Clearlogo', label2 = rom['s_clearlogo'] if rom['s_clearlogo'] else 'Not set'),
            xbmcgui.ListItem(label = 'Boxfront',  label2 = rom['s_boxfront'] if rom['s_boxfront'] else 'Not set'),
            xbmcgui.ListItem(label = 'Boxback',   label2 = rom['s_boxback'] if rom['s_boxback'] else 'Not set'),
            xbmcgui.ListItem(label = 'Cartridge', label2 = rom['s_cartridge'] if rom['s_cartridge'] else 'Not set'),
            xbmcgui.ListItem(label = 'Flyer',     label2 = rom['s_flyer'] if rom['s_flyer'] else 'Not set'),
            xbmcgui.ListItem(label = 'Map',       label2 = rom['s_map'] if rom['s_map'] else 'Not set'),
            xbmcgui.ListItem(label = 'Manual',    label2 = rom['s_manual'] if rom['s_manual'] else 'Not set'),
            xbmcgui.ListItem(label = 'Trailer',   label2 = rom['s_trailer'] if rom['s_trailer'] else 'Not set'),
        ]
        ROMs_asset_ListItem_list[0].setArt({'icon' : rom['s_title'] if rom['s_title'] else 'DefaultAddonNone.png'})
        ROMs_asset_ListItem_list[1].setArt({'icon' : rom['s_snap'] if rom['s_snap'] else 'DefaultAddonNone.png'})
        ROMs_asset_ListItem_list[2].setArt({'icon' : rom['s_fanart'] if rom['s_fanart'] else 'DefaultAddonNone.png'})
        ROMs_asset_ListItem_list[3].setArt({'icon' : rom['s_banner'] if rom['s_banner'] else 'DefaultAddonNone.png'})
        ROMs_asset_ListItem_list[4].setArt({'icon' : rom['s_clearlogo'] if rom['s_clearlogo'] else 'DefaultAddonNone.png'})
        ROMs_asset_ListItem_list[5].setArt({'icon' : rom['s_boxfront'] if rom['s_boxfront'] else 'DefaultAddonNone.png'})
        ROMs_asset_ListItem_list[6].setArt({'icon' : rom['s_boxback'] if rom['s_boxback'] else 'DefaultAddonNone.png'})
        ROMs_asset_ListItem_list[7].setArt({'icon' : rom['s_cartridge'] if rom['s_cartridge'] else 'DefaultAddonNone.png'})
        ROMs_asset_ListItem_list[8].setArt({'icon' : rom['s_flyer'] if rom['s_flyer'] else 'DefaultAddonNone.png'})
        ROMs_asset_ListItem_list[9].setArt({'icon' : rom['s_map'] if rom['s_map'] else 'DefaultAddonNone.png'})
        ROMs_asset_ListItem_list[10].setArt({'icon' : rom['s_manual'] if rom['s_manual'] else 'DefaultAddonNone.png'})
        ROMs_asset_ListItem_list[11].setArt({'icon' : rom['s_trailer'] if rom['s_trailer'] else 'DefaultAddonNone.png'})

        if type3 == 0:
            type_s = dialog.select('Choose default Asset for Icon', list = ROMs_asset_ListItem_list, useDetails = True)
            if type_s < 0: return
            assets_choose_category_ROM(rom, 'roms_default_thumb', type_s)
        elif type3 == 1:
            type_s = dialog.select('Choose default Asset for Fanart', list = ROMs_asset_ListItem_list, useDetails = True)
            if type_s < 0: return
            assets_choose_category_ROM(rom, 'roms_default_fanart', type_s)
        elif type3 == 2:
            type_s = dialog.select('Choose default Asset for Banner', list = ROMs_asset_ListItem_list, useDetails = True)
            if type_s < 0: return
            assets_choose_category_ROM(rom, 'roms_default_banner', type_s)
        elif type3 == 3:
            type_s = dialog.select('Choose default Asset for Poster', list = ROMs_asset_ListItem_list, useDetails = True)
            if type_s < 0: return
            assets_choose_category_ROM(rom, 'roms_default_poster', type_s)
        elif type3 == 4:
            type_s = dialog.select('Choose default Asset for Clearlogo', list = ROMs_asset_ListItem_list, useDetails = True)
            if type_s < 0: return
            assets_choose_category_ROM(rom, 'roms_default_clearlogo', type_s)
        # User canceled select dialog
        elif type3 < 0: return

# --- Manage Collection ROM position (ONLY for Favourite/Collection ROMs) ---
def m_subcommand_manage_collection_rom_position(launcher, rom):
    dialog = xbmcgui.Dialog()
    type2 = dialog.select('Manage ROM position',
                            ['Choose Collection ROM order ...',
                            'Move Collection ROM up',
                            'Move Collection ROM down'])
    if type2 < 0: return

    # --- Choose ROM order ---
    if type2 == 0:
        # >> Get position of current ROM in the list
        num_roms = len(roms)
        current_ROM_position = roms.keys().index(romID)
        if current_ROM_position < 0:
            kodi_notify_warn('ROM ID not found in Collection. This is a bug!')
            return
        log_verb('_command_edit_rom() Collection {0} ({1})'.format(collection['m_name'], collection['id']))
        log_verb('_command_edit_rom() Collection has {0} ROMs'.format(num_roms))

        # --- Show a select dialog ---
        rom_menu_list = []
        for key in roms:
            if key == romID: continue
            rom_menu_list.append(roms[key]['m_name'])
        rom_menu_list.append('Last')
        type3 = dialog.select('Choose position for ROM {0}'.format(roms[romID]['m_name']),
                                rom_menu_list)
        if type3 < 0: return
        new_pos_index = type3
        log_verb('_command_edit_rom() new_pos_index = {0}'.format(new_pos_index))

        # --- Reorder Collection OrderedDict ---
        # >> new_oder = [0, 1, ..., num_roms-1]
        new_order = range(num_roms)
        # >> Delete current element
        del new_order[current_ROM_position]
        # >> Insert current element at selected position
        new_order.insert(new_pos_index, current_ROM_position)
        log_verb('_command_edit_rom() old_order = {0}'.format(unicode(range(num_roms))))
        log_verb('_command_edit_rom() new_order = {0}'.format(unicode(new_order)))

        # >> Reorder ROMs
        new_roms = OrderedDict()
        for order_idx in new_order:
            key_value_tuple = roms.items()[order_idx]
            new_roms.update({key_value_tuple[0] : key_value_tuple[1]})
        roms = new_roms

    # --- Move Collection ROM up ---
    elif type2 == 1:
        if not roms:
            kodi_notify('Collection is empty. Add ROMs to this collection first.')
            return

        # >> Get position of current ROM in the list
        num_roms = len(roms)
        current_ROM_position = roms.keys().index(romID)
        if current_ROM_position < 0:
            kodi_notify_warn('ROM ID not found in Collection. This is a bug!')
            return
        log_verb('_command_edit_rom() Collection {0} ({1})'.format(collection['m_name'], collection['id']))
        log_verb('_command_edit_rom() Collection has {0} ROMs'.format(num_roms))
        log_verb('_command_edit_rom() Moving ROM in position {0} up'.format(current_ROM_position))

        # >> If ROM is first of the list do nothing
        if current_ROM_position == 0:
            kodi_dialog_OK('ROM is in first position of the Collection. Cannot be moved up.')
            return

        # >> Reorder OrderedDict
        new_order                           = range(num_roms)
        new_order[current_ROM_position - 1] = current_ROM_position
        new_order[current_ROM_position]     = current_ROM_position - 1
        new_roms = OrderedDict()
        # >> http://stackoverflow.com/questions/10058140/accessing-items-in-a-ordereddict
        for order_idx in new_order:
            key_value_tuple = roms.items()[order_idx]
            new_roms.update({key_value_tuple[0] : key_value_tuple[1]})
        roms = new_roms

    # --- Move Collection ROM down ---
    elif type2 == 2:
        if not roms:
            kodi_notify('Collection is empty. Add ROMs to this collection first.')
            return

        # >> Get position of current ROM in the list
        num_roms = len(roms)
        current_ROM_position = roms.keys().index(romID)
        if current_ROM_position < 0:
            kodi_notify_warn('ROM ID not found in Collection. This is a bug!')
            return
        log_verb('_command_edit_rom() Collection {0} ({1})'.format(collection['m_name'], collection['id']))
        log_verb('_command_edit_rom() Collection has {0} ROMs'.format(num_roms))
        log_verb('_command_edit_rom() Moving ROM in position {0} down'.format(current_ROM_position))

        # >> If ROM is first of the list do nothing
        if current_ROM_position == num_roms - 1:
            kodi_dialog_OK('ROM is in last position of the Collection. Cannot be moved down.')
            return

        # >> Reorder OrderedDict
        new_order                           = range(num_roms)
        new_order[current_ROM_position]     = current_ROM_position + 1
        new_order[current_ROM_position + 1] = current_ROM_position
        new_roms = OrderedDict()
        # >> http://stackoverflow.com/questions/10058140/accessing-items-in-a-ordereddict
        for order_idx in new_order:
            key_value_tuple = roms.items()[order_idx]
            new_roms.update({key_value_tuple[0] : key_value_tuple[1]})
        roms = new_roms

#
# Edits an object field which is a Unicode string.
#
# Example call:
#   m_gui_edit_metadata_str(collection, 'Title', collection.get_title, collection.set_title)
#
def m_gui_edit_metadata_str(obj_instance, metadata_name, get_method, set_method):
    object_name = obj_instance.get_object_name()
    old_value = get_method()
    s = 'Edit {0} "{1}" {2}'.format(object_name, old_value, metadata_name)
    keyboard = xbmc.Keyboard(old_value, s)
    keyboard.doModal()
    if not keyboard.isConfirmed(): return

    new_value = keyboard.getText().decode('utf-8')
    if old_value == new_value:
        kodi_notify('{0} {1} not changed'.format(object_name, metadata_name))
        return
    set_method(new_value)
    obj_instance.save_to_disk()
    kodi_notify('{0} {1} is now {2}'.format(object_name, metadata_name, new_value))

#
# The values of str_list are supposed to be unique.
#
# Example call:
# m_gui_edit_metadata_list('Launcher', 'Platform', AEL_platform_list,
#                          launcher.get_platform, launcher.set_platform)
#
def m_gui_edit_metadata_list(obj_instance, metadata_name, str_list, get_method, set_method):
    object_name = obj_instance.get_object_name()
    old_value = get_method()
    if old_value in str_list:
        preselect_idx = str_list.index(old_value)
    else:
        preselect_idx = 0
    dialog_title = 'Edit {0} {1}'.format(object_name, metadata_name)
    selected = KodiListDialog().select(dialog_title, str_list, preselect_idx)
    if selected is None: return
    new_value = str_list[selected]
    if old_value == new_value:
        kodi_notify('{0} {1} not changed'.format(object_name, metadata_name))
        return

    set_method(new_value)
    obj_instance.save_to_disk()
    kodi_notify('{0} {1} is now {2}'.format(object_name, metadata_name, new_value))


#
# Rating 'Not set' is stored as an empty string.
# Rating from 0 to 10 is stored as a string, '0', '1', ..., '10'
# Returns True if the rating value was changed.
# Returns Flase if the rating value was NOT changed.
# Example call:
#   m_gui_edit_rating('ROM Collection', collection.get_rating, collection.set_rating)
#
def m_gui_edit_rating(obj_instance, get_method, set_method):
    options_list = [
        'Not set',
        'Rating 0', 'Rating 1', 'Rating 2', 'Rating 3', 'Rating 4', 'Rating 5',
        'Rating 6', 'Rating 7', 'Rating 8', 'Rating 9', 'Rating 10'
    ]
    object_name = obj_instance.get_object_name()
    current_rating_str = get_method()
    if not current_rating_str:
        preselected_value = 0
    else:
        preselected_value = int(current_rating_str) + 1
    sel_value = KodiListDialog().select('Select the {0} Rating'.format(object_name),
                                        options_list, preselect_idx = preselected_value)
    if sel_value is None: return
    if sel_value == preselected_value:
        kodi_notify('{0} Rating not changed'.format(object_name))
        return

    if sel_value == 0:
        current_rating_str = ''
    elif sel_value >= 1 and sel_value <= 11:
        current_rating_str = '{0}'.format(sel_value - 1)
    elif sel_value < 0:
        kodi_notify('{0} Rating not changed'.format(object_name))
        return

    set_method(current_rating_str)
    obj_instance.save_to_disk()
    kodi_notify('{0} rating is now {1}'.format(object_name, current_rating_str))


def m_gui_edit_object_assets(obj_instance, pre_select_idx = 0):
    log_debug('m_gui_edit_object_assets() obj_instance {0}'.format(obj_instance.__class__.__name__))
    log_debug('m_gui_edit_object_assets() pre_select_idx {0}'.format(pre_select_idx))

    # --- DEBUG texture cache ---
    # icon_FN = FileName(obj_instance.get_asset_str(asset_infos[ASSET_ICON_ID]))
    # fanart_FN = FileName(obj_instance.get_asset_str(asset_infos[ASSET_FANART_ID]))
    # log_debug('m_gui_edit_object_assets() icon_FN   "{0}"'.format(icon_FN.getPath()))
    # log_debug('m_gui_edit_object_assets() fanart_FN "{0}"'.format(fanart_FN.getPath()))
    # kodi_print_texture_info(icon_FN.getPath())
    # kodi_print_texture_info(fanart_FN.getPath())

    # --- Customize function for each object type ---
    dialog_title_str = 'Edit {0} Assets/Artwork'. format(obj_instance.get_object_name())

    # --- Build Dialog.select list ---
    # >> Use Krypton Dialog().select(useDetails = True) to display label2 on dialog.
    asset_odict = obj_instance.get_assets_odict()
    # dump_object_to_log('asset_odict', asset_odict)
    list_items = []
    # >> List to easily pick the selected AssetInfo() object
    asset_info_list = []
    for asset_info_obj, asset_fname_str in asset_odict.iteritems():
        # --- Create ListItems ---
        # >> Label1 is the asset name (Icon, Fanart, etc.)
        # >> Label2 is the asset filename str as in the database or 'Not set'
        # >> setArt('icon') is the asset picture.
        label1_str = 'Edit {0} ...'.format(asset_info_obj.name)
        label2_stt = asset_fname_str if asset_fname_str else 'Not set'
        list_item = xbmcgui.ListItem(label = label1_str, label2 = label2_stt)
        if asset_fname_str:
            item_path = FileName(asset_fname_str)
            if item_path.isVideoFile(): item_img = 'DefaultAddonVideo.png'
            elif item_path.isManual():  item_img = 'DefaultAddonInfoProvider.png'
            else:                       item_img = asset_fname_str
        else:
            item_img = 'DefaultAddonNone.png'
        list_item.setArt({'icon' : item_img})
        # --- Append to list of ListItems ---
        list_items.append(list_item)
        asset_info_list.append(asset_info_obj)

    # --- Execute select dialog menu logic ---
    # Kodi Krypton bug: if preselect is used then dialog never returns < 0 even if cancel button
    # is pressed. This bug has been solved in Leia.
    # See https://forum.kodi.tv/showthread.php?tid=337011
    if kodi_running_version >= KODI_VERSION_LEIA:
        selected_option = xbmcgui.Dialog().select(
            dialog_title_str, list = list_items, useDetails = True, preselect = pre_select_idx
        )
    else:
        log_debug('Executing code < KODI_VERSION_LEIA to overcome select() bug.')
        selected_option = xbmcgui.Dialog().select(
            dialog_title_str, list = list_items, useDetails = True
        )
    log_debug('m_gui_edit_object_assets() select() returned {0}'.format(selected_option))
    if selected_option < 0:
        # >> Return to parent menu.
        log_debug('m_gui_edit_object_assets() Selected NONE. Returning to parent menu.')
    else:
        # >> Execute edit asset menu subcommand. Then, execute recursively this submenu again.
        # >> The menu dialog is instantiated again so it reflects the changes just edited.
        # >> If m_gui_edit_asset() returns True changes were made.
        if m_gui_edit_asset(obj_instance, asset_info_list[selected_option]):
            g_ObjectRepository.save_object(obj_instance)
        m_gui_edit_object_assets(obj_instance, selected_option)

#
# Edit category/collection/launcher/ROM asset.
# asset_info is a AssetInfo() object instance.
#
# NOTE When editing ROMs optional parameter launcher_dic is required.
# NOTE Caller is responsible for saving the Categories/Launchers/ROMs.
# NOTE If image is changed container should be updated so the user sees new image instantly.
# NOTE obj_instance is edited by assigment.
#
# Returns:
#   True   Changes made. Categories/Launchers/ROMs must be saved and container updated
#   False  No changes were made. No necessary to refresh container
#
def m_gui_edit_asset(obj_instance, asset_info):
    # --- Get asset object information ---
    # Select/Import require: object_name, A, asset_path_noext
    # Scraper additionaly requires: current_asset_path, scraper_obj, platform, rom_base_noext

    # --- New style code ---
    if obj_instance.get_assets_kind() == KIND_ASSET_CATEGORY:
        asset_directory = FileName(g_settings['categories_asset_dir'], isdir = True)
    elif obj_instance.get_assets_kind() == KIND_ASSET_COLLECTION:
        asset_directory = FileName(g_settings['collections_asset_dir'], isdir = True)
    elif obj_instance.get_assets_kind() == KIND_ASSET_LAUNCHER:
        asset_directory = FileName(g_settings['launchers_asset_dir'], isdir = True)
    elif obj_instance.get_assets_kind() == KIND_ASSET_ROM:
        raise AddonError('Implement met')
    else:
        kodi_dialog_OK('Unknown obj_instance.get_assets_kind() {0}. '.format(obj_instance.get_assets_kind()) +
                       'This is a bug, please report it.')
        return False
    asset_path_noext = assets_get_path_noext_SUFIX(asset_info.id, asset_directory,
                                                   obj_instance.get_name(), obj_instance.get_id())
    log_info('m_gui_edit_asset() Editing {0} {1}'.format(obj_instance.get_object_name(), asset_info.name))
    log_info('m_gui_edit_asset() Object ID {0}'.format(obj_instance.get_id()))
    log_debug('m_gui_edit_asset() asset_directory  "{0}"'.format(asset_directory.getPath()))
    log_debug('m_gui_edit_asset() asset_path_noext "{0}"'.format(asset_path_noext.getPath()))
    if not asset_directory.exists():
        log_error('Directory not found "{0}"'.format(asset_directory.getPath()))
        kodi_dialog_OK('Directory to store artwork not found. '
                       'Configure it before you can edit artwork.')
        return False

    # if object_kind == KIND_ASSET_CATEGORY:
        # # --- Grab asset information for editing ---
        # object_name = 'Category'
        # # AInfo = assets_get_info_scheme(asset_kind)
        # asset_directory = FileNameFactory.create(g_settings['categories_asset_dir'])
        # asset_path_noext = assets_get_path_noext_SUFIX(asset_info.id, asset_directory,
                                                       # obj_instance.get_name(), obj_instance.get_id())
        # log_info('m_gui_edit_asset() Editing Category "{0}"'.format(asset_info.name))
        # log_info('m_gui_edit_asset() ID {0}'.format(obj_instance.get_id()))
        # log_debug('m_gui_edit_asset() asset_directory  "{0}"'.format(asset_directory.getOriginalPath()))
        # log_debug('m_gui_edit_asset() asset_path_noext "{0}"'.format(asset_path_noext.getOriginalPath()))
        # if not asset_directory.exists():
            # log_error('Directory not found "{0}"'.format(asset_directory.getPath()))
            # kodi_dialog_OK('Directory to store Category artwork not configured or not found. '
                           # 'Configure it before you can edit artwork.')
            # return False

    # elif object_kind == KIND_ASSET_COLLECTION:
        # # --- Grab asset information for editing ---
        # object_name = 'ROM Collection'
        # # AInfo = assets_get_info_scheme(asset_kind)
        # asset_directory = FileNameFactory.create(g_settings['collections_asset_dir'])
        # asset_path_noext = assets_get_path_noext_SUFIX(AInfo, asset_directory, object_dic['m_name'], object_dic['id'])
        # log_info('m_gui_edit_asset() Editing Collection "{0}"'.format(AInfo.name))
        # log_info('m_gui_edit_asset() ID {0}'.format(object_dic['id']))
        # log_debug('m_gui_edit_asset() asset_directory  "{0}"'.format(asset_directory.getOriginalPath()))
        # log_debug('m_gui_edit_asset() asset_path_noext "{0}"'.format(asset_path_noext.getOriginalPath()))
        # if not asset_directory.exists():
            # kodi_dialog_OK('Directory to store Collection artwork not configured or not found. '
                           # 'Configure it before you can edit artwork.')
            # return False

    # elif object_kind == KIND_ASSET_LAUNCHER:
        # # --- Grab asset information for editing ---
        # object_name = 'Launcher'
        # AInfo = assets_get_info_scheme(asset_kind)
        # asset_directory = FileNameFactory.create(g_settings['launchers_asset_dir'])
        # asset_path_noext = assets_get_path_noext_SUFIX(AInfo, asset_directory, object_dic['m_name'], object_dic['id'])
        # log_info('m_gui_edit_asset() Editing Launcher "{0}"'.format(AInfo.name))
        # log_info('m_gui_edit_asset() ID {0}'.format(object_dic['id']))
        # log_debug('m_gui_edit_asset() asset_directory  "{0}"'.format(asset_directory.getOriginalPath()))
        # log_debug('m_gui_edit_asset() asset_path_noext "{0}"'.format(asset_path_noext.getOriginalPath()))
        # if not asset_directory.exists():
            # kodi_dialog_OK('Directory to store Launcher artwork not configured or not found. '
                           # 'Configure it before you can edit artwork.')
            # return False

    # elif object_kind == KIND_ASSET_ROM:
        # # --- Grab asset information for editing ---
        # object_name = 'ROM'
        # ROMfile = FileNameFactory.create(object_dic['filename'])
        # AInfo   = assets_get_info_scheme(asset_kind)
        # if categoryID == VCATEGORY_FAVOURITES_ID:
            # log_info('m_gui_edit_asset() ROM is in Favourites')
            # asset_directory  = FileNameFactory.create(g_settings['favourites_asset_dir'])
            # platform         = object_dic['platform']
            # asset_path_noext = assets_get_path_noext_SUFIX(AInfo, asset_directory, ROMfile.getBase_noext(), object_dic['id'])
        # elif categoryID == VCATEGORY_COLLECTIONS_ID:
            # log_info('m_gui_edit_asset() ROM is in Collection')
            # asset_directory  = FileNameFactory.create(g_settings['collections_asset_dir'])
            # platform         = object_dic['platform']
            # asset_path_noext = assets_get_path_noext_SUFIX(AInfo, asset_directory, ROMfile.getBase_noext(), object_dic['id'])
        # else:
            # log_info('m_gui_edit_asset() ROM is in Launcher id {0}'.format(launcherID))
            # launcher         = g_LauncherRepository.find(launcherID)
            # asset_directory  = launcher.get_asset_path(AInfo)
            # platform         = launcher.get_platform()
            # asset_path_noext = assets_get_path_noext_DIR(AInfo, asset_directory, ROMfile)

        # current_asset_path = FileNameFactory.create(object_dic[AInfo.key])
        # log_info('m_gui_edit_asset() Editing ROM {0}'.format(AInfo.name))
        # log_info('m_gui_edit_asset() ROM ID {0}'.format(object_dic['id']))
        # log_debug('m_gui_edit_asset() asset_directory    "{0}"'.format(asset_directory.getOriginalPath()))
        # log_debug('m_gui_edit_asset() asset_path_noext   "{0}"'.format(asset_path_noext.getOriginalPath()))
        # log_debug('m_gui_edit_asset() current_asset_path "{0}"'.format(current_asset_path.getOriginalPath()))
        # log_debug('m_gui_edit_asset() platform           "{0}"'.format(platform))

        # # --- Do not edit asset if asset directory not configured ---
        # if not asset_directory.exists():
            # kodi_dialog_OK('Directory to store {0} not configured or not found. '.format(AInfo.name) + \
                           # 'Configure it before you can edit artwork.')
            # return False

    # else:
        # log_error('m_gui_edit_asset() Unknown object_kind = {0}'.format(object_kind))
        # kodi_notify_warn("Unknown object_kind '{0}'".format(object_kind))
        # return False

    # # --- Only enable scraper if support the asset ---
    # # >> Scrapers only loaded if editing a ROM.
    # if object_kind == KIND_ASSET_ROM:
        # scraper_obj_list  = []
        # scraper_menu_list = []
        # for scrap_obj in scrapers_asset:
            # if scrap_obj.supports_asset(asset_kind):
                # scraper_obj_list.append(scrap_obj)
                # scraper_menu_list.append('Scrape {0} from {1}'.format(AInfo.name, scrap_obj.name))
                # log_verb('Scraper {0} supports scraping {1}'.format(scrap_obj.name, AInfo.name))
            # else:
                # log_verb('Scraper {0} does not support scraping {1}'.format(scrap_obj.name, AInfo.name))
                # log_verb('Scraper DISABLED')

    # --- Show image editing options ---
    common_menu_list = ['Link to local {0} image'.format(asset_info.name),
                        'Import local {0} (copy and rename)'.format(asset_info.name),
                        'Unset artwork/asset']
    dialog_title = 'Change {0} {1}'.format(obj_instance.get_name(), asset_info.name)
    if obj_instance.get_assets_kind() == KIND_ASSET_ROM:
        svalue = xbmcgui.Dialog().select(dialog_title, common_menu_list + scraper_menu_list)
    else:
        svalue = xbmcgui.Dialog().select(dialog_title, common_menu_list)
    # >> User canceled select box
    if svalue < 0: return False

    # --- Link to a local image ---
    if svalue == 0:
        current_image_file = obj_instance.get_asset_FN(asset_info)
        current_image_dir = FileName(current_image_file.getDir(), isdir = True)
        log_debug('m_gui_edit_asset() Asset initial dir "{0}"'.format(current_image_dir.getPath()))
        title_str = 'Select {0} {1}'.format(obj_instance.get_object_name(), asset_info.name)
        ext_list = asset_info.exts_dialog
        if asset_info.id == ASSET_MANUAL_ID or asset_info.id == ASSET_TRAILER_ID:
            new_asset_file = kodi_dialog_GetFile(title_str, ext_list, current_image_dir.getPath())
        else:
            new_asset_file = kodi_dialog_GetImage(title_str, ext_list, current_image_dir.getPath())
        if not new_asset_file: return False
        # --- Check if image exists ---
        new_asset_FN = FileName(new_asset_file)
        if not new_asset_FN.exists(): return False

        # --- Update object ---
        obj_instance.set_asset(asset_info, new_asset_FN)
        log_debug('m_gui_edit_asset() Asset key "{0}"'.format(asset_info.key))
        log_debug('m_gui_edit_asset() Linked {0} {1} to "{2}"'.format(
            obj_instance.get_object_name(), asset_info.name, new_asset_FN.getPath())
        )

        # --- Update Kodi image cache ---
        # Addons cannot manipulate Kodi cache. If the timestamp of a file is updated then
        # Kodi must update the cache immediately.
        # kodi_update_image_cache(new_asset_FN)

        # --- Notify user ---
        kodi_notify('{0} {1} has been updated'.format(obj_instance.get_object_name(), asset_info.name))

    # --- Import an image ---
    # >> Copy and rename a local image into asset directory
    elif svalue == 1:
        # >> If assets exists start file dialog from current asset directory
        current_image_file = obj_instance.get_asset_FN(asset_info)
        current_image_dir = FileName(current_image_file.getDir(), isdir = True)
        log_debug('m_gui_edit_asset() current_image_dir  "{0}"'.format(current_image_dir.getPath()))
        log_debug('m_gui_edit_asset() current_image_file "{0}"'.format(current_image_file.getPath()))

        title_str = 'Select {0} {1}'.format(obj_instance.get_object_name(), asset_info.name)
        ext_list = asset_info.exts_dialog
        if asset_info.id == ASSET_MANUAL_ID or asset_info.id == ASSET_TRAILER_ID:
            new_asset_file_str = kodi_dialog_GetFile(title_str, ext_list, current_image_dir.getPath())
        else:
            new_asset_file_str = kodi_dialog_GetImage(title_str, ext_list, current_image_dir.getPath())
        if not new_asset_file_str: return False

        # >> Determine image extension and dest filename. Check for errors.
        new_asset_file = FileName(new_asset_file_str)
        dest_asset_file = asset_path_noext.append(new_asset_file.getExt())
        log_debug('m_gui_edit_asset() new_asset_file     "{0}"'.format(new_asset_file.getPath()))
        log_debug('m_gui_edit_asset() new_asset_file ext "{0}"'.format(new_asset_file.getExt()))
        log_debug('m_gui_edit_asset() dest_asset_file    "{0}"'.format(dest_asset_file.getPath()))
        if new_asset_file.getPath() == dest_asset_file.getPath():
            log_info('m_gui_edit_asset() new_asset_file and dest_asset_file are the same. Returning.')
            kodi_notify_warn('new_asset_file and dest_asset_file are the same. Returning')
            return False

        # --- Kodi image cache ---
        # The Kodi image cache cannot be manipulated by addons directly.
        # If seems that changing the atime and mtime does not force an update of the Kodi cache
        # when a new image is copied over an existing image. Copying a new image into an old
        # one does not change the ctime.
        # SOLUTION if the destination images exists, delete it before copying the new one. the
        #          ctime if the new image will be updated.
        # NOTE deleting the destination image before copying does not work to force a cache
        #      update.
        # if dest_asset_file.exists():
        #     log_debug('m_gui_edit_asset() Deleting image "{0}"'.format(dest_asset_file.getOriginalPath()))
        #     dest_asset_file.unlink()

        # --- Copy image file ---
        try:
            # fs_encoding = get_fs_encoding()
            # shutil.copy(new_asset_file.getPath().decode(fs_encoding), dest_asset_file.getPath().decode(fs_encoding))
            new_asset_file.copy(dest_asset_file)
        except AddonException:
            log_error('m_gui_edit_asset() AddonException exception copying image')
            kodi_notify_warn('AddonException exception copying image')
            return False

        # --- Update object ---
        # >> Always store original/raw paths in database.
        obj_instance.set_asset(asset_info, dest_asset_file)
        log_debug('m_gui_edit_asset() Asset key "{0}"'.format(asset_info.key))
        log_debug('m_gui_edit_asset() Copied file  "{0}"'.format(new_asset_file.getPath()))
        log_debug('m_gui_edit_asset() Into         "{0}"'.format(dest_asset_file.getPath()))
        log_debug('m_gui_edit_asset() Linked {0} {1} to "{2}"'.format(
            obj_instance.get_object_name(), asset_info.name, dest_asset_file.getPath())
        )

        # --- DEBUG code to investigate Kodi image cache ---
        # log_debug('current_image_file atime {0}'.format(time.ctime(os.path.getatime(current_image_file.getPath()))))
        # log_debug('current_image_file mtime {0}'.format(time.ctime(os.path.getmtime(current_image_file.getPath()))))
        # log_debug('current_image_file ctime {0}'.format(time.ctime(os.path.getctime(current_image_file.getPath()))))
        # log_debug('new_asset_file  atime {0}'.format(time.ctime(os.path.getatime(new_asset_file.getPath()))))
        # log_debug('new_asset_file  mtime {0}'.format(time.ctime(os.path.getmtime(new_asset_file.getPath()))))
        # log_debug('new_asset_file  ctime {0}'.format(time.ctime(os.path.getctime(new_asset_file.getPath()))))
        # log_debug('dest_asset_file atime {0}'.format(time.ctime(os.path.getatime(dest_asset_file.getPath()))))
        # log_debug('dest_asset_file mtime {0}'.format(time.ctime(os.path.getmtime(dest_asset_file.getPath()))))
        # log_debug('dest_asset_file ctime {0}'.format(time.ctime(os.path.getctime(dest_asset_file.getPath()))))

        # >> Copying a file updates atime and mtime but not ctime. ctime of the new file is the
        # >> ctime of the old file (tested on Windows).
        # log_debug('m_gui_edit_asset() Updating destination file atime and mtime')
        # os.utime(dest_asset_file.getPath(), (time.time(), time.time()))
        # log_debug('dest_asset_file  atime {0}'.format(time.ctime(os.path.getatime(dest_asset_file.getPath()))))
        # log_debug('dest_asset_file  mtime {0}'.format(time.ctime(os.path.getmtime(dest_asset_file.getPath()))))
        # log_debug('dest_asset_file  ctime {0}'.format(time.ctime(os.path.getctime(dest_asset_file.getPath()))))

        # --- Delete cached image to force a cache update ---
        kodi_delete_cache_texture(dest_asset_file.getPath())
        kodi_print_texture_info(dest_asset_file.getPath())

        # --- Notify user ---
        kodi_notify('{0} {1} has been updated'.format(obj_instance.get_object_name(), asset_info.name))

    # --- Unset asset ---
    elif svalue == 2:
        obj_instance.set_asset(asset_info, FileName(''))
        log_info('m_gui_edit_asset() Unset {0} {1}'.format(obj_instance.get_object_name(), asset_info.name))
        kodi_notify('{0} {1} has been unset'.format(obj_instance.get_object_name(), asset_info.name))

    # --- Manual scrape asset ---
    elif svalue >= 3:
        # --- Use the scraper chosen by user ---
        scraper_index = svalue - 3
        scraper_obj   = scraper_obj_list[scraper_index]
        log_debug('m_gui_edit_asset() Scraper index {0}'.format(scraper_index))
        log_debug('m_gui_edit_asset() User chose scraper "{0}"'.format(scraper_obj.name))

        # --- Initialise asset scraper ---
        # region        = g_settings['scraper_region']
        # thumb_imgsize = g_settings['scraper_thumb_size']
        # scraper_obj.set_options(region, thumb_imgsize)
        # >> Must be like this: scraper_obj.set_options(g_settings)
        # log_debug('m_gui_edit_asset() Initialised scraper "{0}"'.format(scraper_obj.name))

        # --- Ask user to edit the image search string ---
        keyboard = xbmc.Keyboard(object_dic['m_name'], 'Enter the string to search for ...')
        keyboard.doModal()
        if not keyboard.isConfirmed(): return False
        search_string = keyboard.getText().decode('utf-8')

        # --- Call scraper and get a list of games ---
        # IMPORTANT Setting Kodi busy notification prevents the user to control the UI when a dialog with handler -1
        #           has been called and nothing is displayed.
        #           THIS PREVENTS THE RACE CONDITIONS THAT CAUSE TROUBLE IN ADVANCED LAUNCHER!!!
        kodi_busydialog_ON()
        results = scraper_obj.get_search(search_string, ROMfile.getBase_noext(), platform)
        kodi_busydialog_OFF()
        log_debug('{0} scraper found {1} result/s'.format(AInfo.name, len(results)))
        if not results:
            kodi_dialog_OK('Scraper found no matching games.')
            log_debug('{0} scraper did not found any game'.format(AInfo.name))
            return False

        # --- Choose game to download image ---
        if len(results) == 1:
            selectgame = 0
        else:
            # >> Display corresponding game list found so user choses
            rom_name_list = []
            for game in results:
                rom_name_list.append(game['display_name'])
            selectgame = xbmcgui.Dialog().select('Select game for "{0}"'.format(search_string), rom_name_list)
            if selectgame < 0: return False

        # --- Grab list of images for the selected game ---
        # >> Prevent race conditions
        kodi_busydialog_ON()
        image_list = scraper_obj.get_images(results[selectgame], asset_kind)
        kodi_busydialog_OFF()
        log_verb('{0} scraper returned {1} images'.format(AInfo.name, len(image_list)))
        if not image_list:
            kodi_dialog_OK('Scraper found no {0} '.format(AInfo.name) + 
                           'images for game "{0}".'.format(results[selectgame]['display_name']))
            return False

        # --- Always do semi-automatic scraping when editing images ---
        # If there is a local image add it to the list and show it to the user
        if current_asset_path.exists():
            image_list.insert(0, {'name'       : 'Current local image', 
                                  'id'         : current_asset_path.getPath(),
                                  'URL'        : current_asset_path.getPath(),
                                  'asset_kind' : asset_kind})

        # >> Convert list returned by scraper into a list the select window uses
        ListItem_list = []
        for item in image_list:
            listitem_obj = xbmcgui.ListItem(label = item['name'], label2 = item['URL'])
            listitem_obj.setArt({'icon' : item['URL']})
            ListItem_list.append(listitem_obj)
        # >> If there are no items in the list is because there is no current asst and scraper
        # >> found nothing. Return.
        if len(ListItem_list) == 0:
            log_debug('m_gui_edit_asset() ListItem_list is empty. Returning.')
            return False
        # >> If there is only one item in the list do not show select dialog
        elif len(ListItem_list) == 1:
            log_debug('m_gui_edit_asset() ListItem_list has one element. Do not show select dialog.')
            image_selected_index = 0
        else:
            image_selected_index = xbmcgui.Dialog().select('Select image', list = ListItem_list, useDetails = True)
            log_debug('{0} dialog returned index {1}'.format(AInfo.name, image_selected_index))
        # >> User cancelled dialog
        if image_selected_index < 0:
            log_debug('m_gui_edit_asset() User cancelled image select dialog. Returning.')
            return False

        # >> User choose local image
        if image_list[image_selected_index]['URL'] == current_asset_path.getPath():
           log_debug('m_gui_edit_asset() Selected current image "{0}"'.format(current_asset_path.getPath()))
           return False
        else:
            log_debug('m_gui_edit_asset() Downloading selected image ...')
            # >> Resolve asset URL
            kodi_busydialog_ON()
            image_url, image_ext = scraper_obj.resolve_image_URL(image_list[image_selected_index])
            kodi_busydialog_OFF()
            log_debug('Resolved {0} URL "{1}"'.format(AInfo.name, image_url))
            log_debug('URL extension "{0}"'.format(image_ext))
            if not image_url or not image_ext:
                log_error('m_gui_edit_asset() image_url or image_ext empty/not set')
                return False

            # ~~~ Download image ~~~
            image_local_path = asset_path_noext.append(image_ext)
            log_verb('Downloading URL "{0}"'.format(image_url))
            log_verb('Into local file "{0}"'.format(image_local_path.getPath()))

            # >> Prevent race conditions
            try:
                net_download_img(image_url, image_local_path)
            except socket.timeout:
                kodi_notify_warn('Cannot download {0} image (Timeout)'.format(image_name))

            # ~~~ Update Kodi cache with downloaded image ~~~
            # Recache only if local image is in the Kodi cache, this function takes care of that.
            kodi_update_image_cache(image_local_path)

            # --- Notify user ---
            kodi_notify('Downloaded {0} with {1} scraper'.format(AInfo.name, scraper_obj.name))

        # --- Edit using Python pass by assigment ---
        # >> If we reach this point is because an image was downloaded
        # >> Caller is responsible to save Categories/Launchers/ROMs
        object_dic[AInfo.key] = image_local_path.getOriginalPath()

    # >> If we reach this point, changes were made.
    # >> Categories/Launchers/ROMs must be saved, container must be refreshed.
    return True

#
# Generic function to edit the Object default assets for 
# icon/fanart/banner/poster/clearlogo context submenu.
# Argument obj is an object instance of class Category, CollectionLauncher, etc.
#
def m_gui_edit_object_default_assets(obj_instance, pre_select_idx = 0):
    log_debug('m_gui_edit_object_default_assets() obj {0}'.format(obj_instance.__class__.__name__))
    log_debug('m_gui_edit_object_default_assets() pre_select_idx {0}'.format(pre_select_idx))

    # --- Customize function for each object type ---
    if obj_instance.get_assets_kind() == KIND_ASSET_CATEGORY:
        repository_obj = g_MainRepository

    elif obj_instance.get_assets_kind() == KIND_ASSET_COLLECTION:
        repository_obj = g_CollectionRepository

    elif obj_instance.get_assets_kind() == KIND_ASSET_LAUNCHER:
        repository_obj = g_MainRepository

    elif obj_instance.get_assets_kind() == KIND_ASSET_ROM:
        repository_obj = g_MainRepository

    else:
        kodi_dialog_OK(
            'm_gui_edit_object_default_assets() ' +
            'Unknown obj_instance.get_assets_kind() = {0}'.format(obj_instance.get_assets_kind()) +
            'This is a bug, please report it.')
        return
    dialog_title_str = 'Edit {0} default Assets/Artwork'.format(obj_instance.get_object_name())

    # --- Build Dialog.select() list ---
    assets_odict = obj_instance.get_assets_odict()
    default_assets_list = obj_instance.get_default_asset_list()
    list_items = []
    # >> List to easily pick the selected AssetInfo() object
    asset_info_list = []
    for default_asset_info in default_assets_list:
        # >> Label 1 is the string 'Choose asset for XXXX (currently YYYYY)'
        # >> Label 2 is the fname string of the current mapped asset or 'Not set'
        # >> icon is the fname string of the current mapped asset.
        mapped_asset_key = obj_instance.get_mapped_asset_key(default_asset_info)
        mapped_asset_info = ASSET_INFO_KEY_DICT[mapped_asset_key]
        mapped_asset_str = obj_instance.get_asset_str(mapped_asset_info)
        label1_str = 'Choose asset for {0} (currently {1})'.format(default_asset_info.name, mapped_asset_info.name)
        label2_str = mapped_asset_str
        list_item = xbmcgui.ListItem(label = label1_str, label2 = label2_str)
        if mapped_asset_str:
            item_path = FileName(mapped_asset_str)
            if item_path.isVideoFile(): item_img = 'DefaultAddonVideo.png'
            elif item_path.isManual():  item_img = 'DefaultAddonInfoProvider.png'
            else:                       item_img = mapped_asset_str
        else:
            item_img = 'DefaultAddonNone.png'
        list_item.setArt({'icon' : item_img})
        # --- Append to list of ListItems ---
        list_items.append(list_item)
        asset_info_list.append(default_asset_info)

    # --- Execute select dialog menu logic ---
    # Kodi Krypton bug: if preselect is used then dialog never returns < 0 even if cancel button
    # is pressed. This bug has been solved in Leia.
    # See https://forum.kodi.tv/showthread.php?tid=337011
    if kodi_running_version >= KODI_VERSION_LEIA:
        selected_option = xbmcgui.Dialog().select(
            dialog_title_str, list = list_items, useDetails = True, preselect = pre_select_idx
        )
    else:
        log_debug('Executing code < KODI_VERSION_LEIA to overcome select() bug.')
        selected_option = xbmcgui.Dialog().select(
            dialog_title_str, list = list_items, useDetails = True
        )
    log_debug('m_gui_edit_object_default_assets() Main select() returned {0}'.format(selected_option))
    if selected_option < 0:
        # >> Return to parent menu.
        log_debug('m_gui_edit_object_default_assets() Main selected NONE. Returning to parent menu.')
    else:
        # >> Execute edit default asset submenu. Then, execute recursively this submenu again.
        # >> The menu dialog is instantiated again so it reflects the changes just edited.
        log_debug('m_gui_edit_object_default_assets() Executing mappable asset select() dialog.')
        selected_asset_info = asset_info_list[selected_option]
        log_debug('m_gui_edit_object_default_assets() Main selected {0}.'.format(selected_asset_info.name))
        mappable_asset_list = obj_instance.get_mappable_asset_list()
        list_items = []
        asset_info_list = []
        secondary_pre_select_idx = 0
        counter = 0
        for mappable_asset_info in mappable_asset_list:
            # --- Create ListItems ---
            # >> Label1 is the asset name (Icon, Fanart, etc.)
            # >> Label2 is the asset filename str as in the database or 'Not set'
            # >> setArt('icon') is the asset picture.
            mapped_asset_str = obj_instance.get_asset_str(mappable_asset_info)
            label1_str = '{0}'.format(mappable_asset_info.name)
            label2_stt = mapped_asset_str if mapped_asset_str else 'Not set'
            list_item = xbmcgui.ListItem(label = label1_str, label2 = label2_stt)
            if mapped_asset_str:
                item_path = FileName(mapped_asset_str)
                if item_path.isVideoFile(): item_img = 'DefaultAddonVideo.png'
                elif item_path.isManual():  item_img = 'DefaultAddonInfoProvider.png'
                else:                       item_img = mapped_asset_str
            else:
                item_img = 'DefaultAddonNone.png'
            list_item.setArt({'icon' : item_img})
            # --- Append to list of ListItems ---
            list_items.append(list_item)
            asset_info_list.append(mappable_asset_info)
            if mappable_asset_info == selected_asset_info:
                secondary_pre_select_idx = counter
            counter += 1

        # --- Execute select dialog menu logic ---
        # Kodi Krypton bug: if preselect is used then dialog never returns < 0 even if cancel
        # button is pressed. This bug has been solved in Leia.
        # See https://forum.kodi.tv/showthread.php?tid=337011
        dialog_title_str = 'Edit {0} {1} mapped asset'.format(
            obj_instance.get_object_name(), selected_asset_info.name)
        if kodi_running_version >= KODI_VERSION_LEIA:
            secondary_selected_option = xbmcgui.Dialog().select(
                dialog_title_str, list = list_items, useDetails = True, preselect = secondary_pre_select_idx
            )
        else:
            log_debug('Executing code < KODI_VERSION_LEIA to overcome select() bug.')
            secondary_selected_option = xbmcgui.Dialog().select(
                dialog_title_str, list = list_items, useDetails = True
            )
        log_debug('m_gui_edit_object_default_assets() Mapable select() returned {0}'.format(secondary_selected_option))
        if secondary_selected_option < 0:
            # >> Return to parent menu.
            log_debug('m_gui_edit_object_default_assets() Mapable selected NONE. Returning to parent menu.')
        else:
            new_selected_asset_info = asset_info_list[secondary_selected_option]
            log_debug('m_gui_edit_object_default_assets() Mapable selected {0}.'.format(new_selected_asset_info.name))
            obj_instance.set_mapped_asset_key(selected_asset_info, new_selected_asset_info)
            repository_obj.save(obj_instance)
            kodi_notify('{0} {1} mapped to {2}'.format(
                obj_instance.get_object_name(), selected_asset_info.name, new_selected_asset_info.name
            ))
        # --- Execute recursively wheter submenu was canceled or not ---
        m_gui_edit_object_default_assets(obj_instance, selected_option)

# -------------------------------------------------------------------------------------------------
# Render methods
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# Categories LisItem rendering
# -------------------------------------------------------------------------------------------------
#
# Renders the addon Root window. Categories, categoryless launchers, Favourites, etc.
#
def m_command_render_root():
    m_misc_set_all_sorting_methods()
    m_misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)
    m_misc_clear_AEL_Launcher_Content()

    # --- Render categories in classic mode or in flat mode ---
    # <setting id="display_category_mode" values="Standard|Flat"/>
    if g_settings['display_category_mode'] == 0:
        category_list = g_ObjectFactory.find_category_all()
        for category in category_list:
            m_gui_render_category_row(category)
    else:
        category_list = g_ObjectFactory.find_category_all()
        for category in category_list:
            launcher_list = g_ObjectFactory.find_launchers_in_cat(category.get_id())
            # dump_object_to_log(launcher_list)
            for launcher in launcher_list:
                launcher_raw_name = '[COLOR thistle]{0}[/COLOR] - {1}'.format(category.get_name(), launcher.get_name())
                m_gui_render_launcher_row(launcher, launcher_raw_name)

    # --- Render categoryless launchers. Order alphabetically by name ---
    nocat_launcher_list = g_ObjectFactory.find_launchers_in_cat(VCATEGORY_ADDONROOT_ID)
    for launcher in nocat_launcher_list:
        m_gui_render_launcher_row(launcher)

    # --- AEL Favourites virtual launcher ---
    if not g_settings['display_hide_favs']:
        m_gui_render_vlauncher_favourites_row()

    # --- AEL Collections virtual category ---
    if not g_settings['display_hide_collections']:
        m_gui_render_vcategory_collections_row()

    # --- Recently played and most played ROMs virtual launchers ---
    if not g_settings['display_hide_recent']:
        m_gui_render_vlauncher_recently_played_row()
    if not g_settings['display_hide_mostplayed']:
        m_gui_render_vlauncher_most_played_row()

    # --- AEL Virtual Categories ---
    if not g_settings['display_hide_vlaunchers']:
        m_gui_render_vcategory_Browse_by_row()

    # --- Browse Offline Scraper database ---
    if not g_settings['display_hide_AEL_scraper']:
        m_gui_render_vcategory_AEL_offline_scraper_row()
    if not g_settings['display_hide_LB_scraper']:
        m_gui_render_vcategory_LB_offline_scraper_row()

    m_gui_render_Utilities_root()
    m_gui_render_GlobalReports_root()

    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

#
# Renders all categories without Favourites, Collections, virtual categories, etc.
# This function is called by skins to build shortcuts menu.
#
def m_command_render_root_skins():
    categories = g_CategoryRepository.find_all()

    # >> If no categories render nothing
    if not categories:
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # >> For every category, add it to the listbox. Order alphabetically by name
    for category in sorted(categories, key = lambda c : c.get_name()):
        self._gui_render_category_row(category)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

#
# category is a Category object.
#
def m_gui_render_category_row(category):
    # --- Do not render row if category finished ---
    if category.is_finished() and g_settings['display_hide_finished']: return

    category_raw_name = category.get_name()
    num_launchers = category.num_launchers()
    if num_launchers == 0:
        launcher_name = '{0} [COLOR tomato](No launchers)[/COLOR]'.format(category_raw_name)
    elif num_launchers == 1:
        launcher_name = '{0} [COLOR tomato]({1} launcher)[/COLOR]'.format(category_raw_name, num_launchers)
    else:
        launcher_name = '{0} [COLOR tomato]({1} launchers)[/COLOR]'.format(category_raw_name, num_launchers)

    # --- Create listitem row ---
    ICON_OVERLAY = 5 if category.is_finished() else 4
    listitem = xbmcgui.ListItem(launcher_name)
    if category.get_releaseyear():
        listitem.setInfo('video', {
            'title'   : launcher_name,          'year'    : category.get_releaseyear(),
            'genre'   : category.get_genre(),   'studio'  : category.get_developer(),
            'rating'  : category.get_rating(),  'plot'    : category.get_plot(),
            'trailer' : category.get_trailer(), 'overlay' : ICON_OVERLAY
        })
    else:
        listitem.setInfo('video', {
            'title'   : launcher_name,
            'genre'   : category.get_genre(),   'studio'  : category.get_developer(),
            'rating'  : category.get_rating(),  'plot'    : category.get_plot(),
            'trailer' : category.get_trailer(), 'overlay' : ICON_OVERLAY
        })
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_CATEGORY)

    # --- Set Category artwork ---
    category_dic = category.get_data_dic()
    # NOTE Integrate this functions into the Category class.
    icon_path      = asset_get_default_asset_Category(category_dic, 'default_icon', 'DefaultFolder.png')
    fanart_path    = asset_get_default_asset_Category(category_dic, 'default_fanart')
    banner_path    = asset_get_default_asset_Category(category_dic, 'default_banner')
    poster_path    = asset_get_default_asset_Category(category_dic, 'default_poster')
    clearlogo_path = asset_get_default_asset_Category(category_dic, 'default_clearlogo')
    listitem.setArt({'icon'   : icon_path,   'fanart' : fanart_path, 
                     'banner' : banner_path, 'poster' : poster_path, 'clearlogo' : clearlogo_path})

    # --- Create context menu ---
    # To remove default entries like "Go to root", etc, see http://forum.kodi.tv/showthread.php?tid=227358
    # Window FileManager has ID = 10003
    # In Krypton "Add to favourites" appears always in the last position of context menu and cannot
    # be removed.
    commands = []
    categoryID = category.get_id()
    commands.append(('View', m_misc_url_RunPlugin('VIEW', categoryID)))
    commands.append(('Edit/Export Category', m_misc_url_RunPlugin('EDIT_CATEGORY', categoryID)))
    commands.append(('Add new Launcher', m_misc_url_RunPlugin('ADD_LAUNCHER', categoryID)))
    commands.append(('Add new Category', m_misc_url_RunPlugin('ADD_CATEGORY')))
    commands.append(('Open Kodi file manager', 'ActivateWindow(filemanager)'))
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
    listitem.addContextMenuItems(commands)

    # --- Add row ---
    url_str = m_misc_url('SHOW_LAUNCHERS', categoryID)
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder=True)

def m_gui_render_vlauncher_favourites_row():
    # fav_icon   = 'DefaultFolder.png'

    # --- Create listitem row ---
    vcategory_name   = '<Favourites>'
    vcategory_plot   = 'Browse AEL Favourite ROMs'
    vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Favourites_icon.png').getPath()
    vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
    vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Favourites_poster.png').getPath()
    listitem = xbmcgui.ListItem(vcategory_name)
    listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay' : 4 })
    listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)

    # --- Create context menu ---
    commands = []
    commands.append(('Add new Launcher', m_misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
    commands.append(('Add new Category', m_misc_url_RunPlugin('ADD_CATEGORY')))
    commands.append(('Open Kodi file manager', 'ActivateWindow(filemanager)'))
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
    listitem.addContextMenuItems(commands)

    # --- Add row ---
    url_str = m_misc_url('SHOW_FAVOURITES')
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = True)

def m_gui_render_vcategory_collections_row():
    vcategory_name   = '{ROM Collections}'
    vcategory_plot   = 'Browse the user defined ROM Collections'
    vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/ROM_Collections_icon.png').getPath()
    vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
    vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/ROM_Collections_poster.png').getPath()
    listitem = xbmcgui.ListItem(vcategory_name)
    listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay' : 4 })
    listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_CATEGORY)

    commands = []
    commands.append(('Add new ROM Collection', m_misc_url_RunPlugin('ADD_COLLECTION')))
    commands.append(('Import ROM Collection', m_misc_url_RunPlugin('IMPORT_COLLECTION')))
    commands.append(('Add new Launcher', m_misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
    commands.append(('Add new Category', m_misc_url_RunPlugin('ADD_CATEGORY')))
    commands.append(('Open Kodi file manager', 'ActivateWindow(filemanager)'))
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
    listitem.addContextMenuItems(commands)

    url_str = m_misc_url('SHOW_COLLECTIONS')
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = True)

def m_gui_render_vlauncher_recently_played_row():
    vcategory_name   = '[Recently played ROMs]'
    vcategory_plot   = 'Browse the ROMs you played recently'
    vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Recently_played_icon.png').getPath()
    vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
    vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Recently_played_poster.png').getPath()
    listitem = xbmcgui.ListItem(vcategory_name)
    listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
    listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)

    commands = []
    commands.append(('Add new Launcher', m_misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
    commands.append(('Add new Category', m_misc_url_RunPlugin('ADD_CATEGORY')))
    commands.append(('Open Kodi file manager', 'ActivateWindow(filemanager)'))
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
    listitem.addContextMenuItems(commands)

    url_str = m_misc_url('SHOW_RECENTLY_PLAYED')
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = True)

def m_gui_render_vlauncher_most_played_row():
    vcategory_name   = '[Most played ROMs]'
    vcategory_plot   = 'Browse the ROMs you play most'
    vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Most_played_icon.png').getPath()
    vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
    vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Most_played_poster.png').getPath()
    listitem = xbmcgui.ListItem(vcategory_name)
    listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
    listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)

    commands = []
    commands.append(('Add new Launcher', m_misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
    commands.append(('Add new Category', m_misc_url_RunPlugin('ADD_CATEGORY')))
    commands.append(('Open Kodi file manager', 'ActivateWindow(filemanager)'))
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
    listitem.addContextMenuItems(commands)

    url_str = m_misc_url('SHOW_MOST_PLAYED')
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = True)

def m_gui_render_vcategory_Browse_by_row():
    vcategory_name   = '[Browse by ... ]'
    vcategory_label  = 'Browse by ...'
    vcategory_plot   = 'Browse AEL Virtual Launchers'
    vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_icon.png').getPath()
    vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
    vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_poster.png').getPath()
    listitem = xbmcgui.ListItem(vcategory_name)
    listitem.setInfo('video', {'title' : vcategory_name, 'plot' : vcategory_plot, 'overlay' : 4 })
    listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_CATEGORY)

    commands = []
    update_vcat_all_URL = m_misc_url_RunPlugin('UPDATE_ALL_VCATEGORIES')
    commands.append(('Update all databases'.format(vcategory_label), update_vcat_all_URL))
    commands.append(('Add new Launcher', m_misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
    commands.append(('Add new Category', m_misc_url_RunPlugin('ADD_CATEGORY')))
    commands.append(('Open Kodi file manager', 'ActivateWindow(filemanager)'))
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
    listitem.addContextMenuItems(commands)

    url_str = m_misc_url('SHOW_VCATEGORIES_ROOT')
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = True)

def m_gui_render_vcategory_AEL_offline_scraper_row():
    vcategory_name   = '[Browse AEL Offline Scraper]'
    # vcategory_label  = 'Browse Offline Scraper'
    vcategory_plot   = 'Allows you to browse the ROMs in the AEL Offline Scraper database'
    vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_AEL_Offline_icon.png').getPath()
    vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
    vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_AEL_Offline_poster.png').getPath()
    listitem = xbmcgui.ListItem(vcategory_name)
    listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
    listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_CATEGORY)

    commands = []
    commands.append(('Add new Launcher', m_misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
    commands.append(('Add new Category', m_misc_url_RunPlugin('ADD_CATEGORY')))
    commands.append(('Open Kodi file manager', 'ActivateWindow(filemanager)'))
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
    listitem.addContextMenuItems(commands)

    url_str = m_misc_url('SHOW_AEL_OFFLINE_LAUNCHERS_ROOT')
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = True)

def m_gui_render_vcategory_LB_offline_scraper_row():
    vcategory_name   = '[Browse LaunchBox Offline Scraper]'
    vcategory_label  = 'Browse Offline Scraper'
    vcategory_plot   = 'Allows you to browse the ROMs in the LaunchBox Offline Scraper database'
    vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_LaunchBox_Offline_icon.png').getPath()
    vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
    vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_LaunchBox_Offline_poster.png').getPath()
    listitem = xbmcgui.ListItem(vcategory_name)
    listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
    listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_CATEGORY)

    commands = []
    commands.append(('Add new Launcher', m_misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
    commands.append(('Add new Category', m_misc_url_RunPlugin('ADD_CATEGORY')))
    commands.append(('Open Kodi file manager', 'ActivateWindow(filemanager)'))
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
    listitem.addContextMenuItems(commands)

    url_str = m_misc_url('SHOW_LB_OFFLINE_LAUNCHERS_ROOT')
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = True)

def m_gui_render_Utilities_root():
    vcategory_name   = 'Utilities'
    vcategory_plot   = 'Execute several [COLOR orange]Utilities[/COLOR].'
    vcategory_icon   = g_PATHS.ICON_FILE_PATH.getPath()
    vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()

    listitem = xbmcgui.ListItem(vcategory_name)
    listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
    listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart})
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_CATEGORY)

    commands = []
    commands.append(('Add new Launcher', m_misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
    commands.append(('Add new Category', m_misc_url_RunPlugin('ADD_CATEGORY')))
    commands.append(('Open Kodi file manager', 'ActivateWindow(filemanager)'))
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
    listitem.addContextMenuItems(commands)

    url_str = m_misc_url('SHOW_UTILITIES_VLAUNCHERS')
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = True)

def m_gui_render_GlobalReports_root():
    vcategory_name   = 'Global Reports'
    vcategory_plot   = 'Generate and view [COLOR orange]Global Reports[/COLOR].'
    vcategory_icon   = g_PATHS.ICON_FILE_PATH.getPath()
    vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()

    listitem = xbmcgui.ListItem(vcategory_name)
    listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
    listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart})
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_CATEGORY)

    commands = []
    commands.append(('Add new Launcher', m_misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
    commands.append(('Add new Category', m_misc_url_RunPlugin('ADD_CATEGORY')))
    commands.append(('Open Kodi file manager', 'ActivateWindow(filemanager)'))
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
    listitem.addContextMenuItems(commands)

    url_str = m_misc_url('SHOW_GLOBALREPORTS_VLAUNCHERS')
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = True)

# -------------------------------------------------------------------------------------------------
# Virtual categories [Browse by ...]
# -------------------------------------------------------------------------------------------------
def m_gui_render_Browse_by_vlaunchers():
    m_misc_set_all_sorting_methods()
    m_misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)
    m_misc_clear_AEL_Launcher_Content()
    m_gui_render_Browse_by_vlaunchers_row(VCATEGORY_TITLE_ID)
    m_gui_render_Browse_by_vlaunchers_row(VCATEGORY_YEARS_ID)
    m_gui_render_Browse_by_vlaunchers_row(VCATEGORY_GENRE_ID)
    m_gui_render_Browse_by_vlaunchers_row(VCATEGORY_DEVELOPER_ID)
    m_gui_render_Browse_by_vlaunchers_row(VCATEGORY_NPLAYERS_ID)
    m_gui_render_Browse_by_vlaunchers_row(VCATEGORY_ESRB_ID)
    m_gui_render_Browse_by_vlaunchers_row(VCATEGORY_RATING_ID)
    m_gui_render_Browse_by_vlaunchers_row(VCATEGORY_CATEGORY_ID)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def m_gui_render_Browse_by_vlaunchers_row(virtual_category_kind):
    if virtual_category_kind == VCATEGORY_TITLE_ID:
        vcategory_name   = 'Browse ROMs by Title'
        vcategory_label  = 'Title'
        vcategory_plot   = 'Browse virtual launchers in {0} virtual category'.format(vcategory_label)
        vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_Title_icon.png').getPath()
        vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
        vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_Title_poster.png').getPath()
    elif virtual_category_kind == VCATEGORY_YEARS_ID:
        vcategory_name   = 'Browse by Year'
        vcategory_label  = 'Year'
        vcategory_plot   = 'Browse virtual launchers in {0} virtual category'.format(vcategory_label)
        vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_Year_icon.png').getPath()
        vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
        vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_Year_poster.png').getPath()
    elif virtual_category_kind == VCATEGORY_GENRE_ID:
        vcategory_name   = 'Browse by Genre'
        vcategory_label  = 'Genre'
        vcategory_plot   = 'Browse virtual launchers in {0} virtual category'.format(vcategory_label)
        vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_Genre_icon.png').getPath()
        vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
        vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_Genre_poster.png').getPath()
    elif virtual_category_kind == VCATEGORY_DEVELOPER_ID:
        vcategory_name   = 'Browse by Developer'
        vcategory_label  = 'Developer'
        vcategory_plot   = 'Browse virtual launchers in {0} virtual category'.format(vcategory_label)
        vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_Developer_icon.png').getPath()
        vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
        vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_Developer_poster.png').getPath()
    elif virtual_category_kind == VCATEGORY_NPLAYERS_ID:
        vcategory_name   = 'Browse by Number of Players'
        vcategory_label  = 'NPlayers'
        vcategory_plot   = 'Browse virtual launchers in {0} virtual category'.format(vcategory_label)
        vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_NPlayers_icon.png').getPath()
        vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
        vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_NPlayers_poster.png').getPath()
    elif virtual_category_kind == VCATEGORY_ESRB_ID:
        vcategory_name   = 'Browse by ESRB Rating'
        vcategory_label  = 'ESRB'
        vcategory_plot   = 'Browse virtual launchers in {0} virtual category'.format(vcategory_label)
        vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_ESRB_icon.png').getPath()
        vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
        vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_ESRB_poster.png').getPath()
    elif virtual_category_kind == VCATEGORY_RATING_ID:
        vcategory_name   = 'Browse by User Rating'
        vcategory_label  = 'Rating'
        vcategory_plot   = 'Browse virtual launchers in {0} virtual category'.format(vcategory_label)
        vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_User_Rating_icon.png').getPath()
        vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
        vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_User_Rating_poster.png').getPath()
    elif virtual_category_kind == VCATEGORY_CATEGORY_ID:
        vcategory_name   = 'Browse by Category'
        vcategory_label  = 'Category'
        vcategory_plot   = 'Browse virtual launchers in {0} virtual category'.format(vcategory_label)
        vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_Category_icon.png').getPath()
        vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
        vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_Category_poster.png').getPath()
    else:
        log_error('_gui_render_virtual_category_row() Wrong virtual_category_kind = {0}'.format(virtual_category_kind))
        kodi_dialog_OK('Wrong virtual_category_kind = {0}'.format(virtual_category_kind))
        return
    listitem = xbmcgui.ListItem(vcategory_name)
    listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
    listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)

    commands = []
    update_vcat_URL = m_misc_url_RunPlugin('UPDATE_VIRTUAL_CATEGORY', virtual_category_kind)
    update_vcat_all_URL = m_misc_url_RunPlugin('UPDATE_ALL_VCATEGORIES')
    commands.append(('Update {0} database'.format(vcategory_label), update_vcat_URL))
    commands.append(('Update all databases', update_vcat_all_URL))
    commands.append(('Add new Launcher', m_misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
    commands.append(('Add new Category', m_misc_url_RunPlugin('ADD_CATEGORY')))
    commands.append(('Open Kodi file manager', 'ActivateWindow(filemanager)'))
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
    listitem.addContextMenuItems(commands)

    url_str = m_misc_url('SHOW_VIRTUAL_CATEGORY', virtual_category_kind)
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = True)

def m_gui_render_AEL_scraper_vlaunchers():
    m_misc_set_default_sorting_method()
    m_misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)
    m_misc_clear_AEL_Launcher_Content()

    # >> Open info dictionary
    gamedb_info_dic = fs_load_JSON_file(g_PATHS.GAMEDB_INFO_DIR, g_PATHS.GAMEDB_JSON_BASE_NOEXT)

    # >> Loop the list of platforms and render a virtual launcher for each platform that
    # >> has a valid XML database.
    for platform in AEL_platform_list:
        # >> Do not show Unknown platform
        if platform == 'Unknown': continue
        
        if not platform in gamedb_info_dic:
            log_warning('_gui_render_AEL_scraper_launchers: Platform {0} not found in collection'.format(platform))
            continue

        db_suffix = platform_AEL_to_Offline_GameDBInfo_XML[platform]
        m_gui_render_AEL_scraper_vlaunchers_row(platform, gamedb_info_dic[platform], db_suffix)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def m_gui_render_AEL_scraper_vlaunchers_row(platform, platform_info, db_suffix):
    # >> Mark platform whose XML DB is not available
    title_str = platform
    if not db_suffix:
        title_str += ' [COLOR red][Not available][/COLOR]'
    else:
        title_str += ' [COLOR orange]({0} ROMs)[/COLOR]'.format(platform_info['numROMs'])
    plot_text = 'Browse [COLOR orange]{0}[/COLOR] ROMs in AEL Offline Scraper database'.format(platform)
    vlauncher_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_AEL_Offline_icon.png').getPath()
    vlauncher_fanart = g_PATHS.FANART_FILE_PATH.getPath()
    vlauncher_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_AEL_Offline_poster.png').getPath()

    listitem = xbmcgui.ListItem(title_str)
    listitem.setInfo('video', {'title' : title_str, 'plot' : plot_text, 'overlay' : 4 })
    listitem.setArt({'icon' : vlauncher_icon, 'fanart' : vlauncher_fanart, 'poster' : vlauncher_poster})
    # >> Set platform property to render platform icon on skins.
    listitem.setProperty('platform', platform)
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)

    commands = []
    commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
    listitem.addContextMenuItems(commands)

    url_str = m_misc_url('SHOW_AEL_SCRAPER_ROMS', platform)
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = True)

def m_gui_render_LB_scraper_vlaunchers():
    m_misc_set_default_sorting_method()
    m_misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)
    m_misc_clear_AEL_Launcher_Content()

    # >> Open info dictionary
    gamedb_info_dic = fs_load_JSON_file(g_PATHS.LAUNCHBOX_INFO_DIR, g_PATHS.LAUNCHBOX_JSON_BASE_NOEXT)

    # >> Loop the list of platforms and render a virtual launcher for each platform that
    # >> has a valid XML database.
    for platform in AEL_platform_list:
        # >> Do not show Unknown platform
        if platform == 'Unknown': continue

        if not platform in gamedb_info_dic:
            log_warning('_gui_render_LB_scraper_launchers: Platform {0} not found in collection'.format(platform))
            continue

        db_suffix = platform_AEL_to_LB_XML[platform]
        m_gui_render_LB_scraper_vlaunchers_row(platform, gamedb_info_dic[platform], db_suffix)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def m_gui_render_LB_scraper_vlaunchers_row(platform, platform_info, db_suffix):
    # >> Mark platform whose XML DB is not available
    title_str = platform
    if not db_suffix:
        title_str += ' [COLOR red][Not available][/COLOR]'
    else:
        title_str += ' [COLOR orange]({0} ROMs)[/COLOR]'.format(platform_info['numROMs'])
    plot_text = 'Browse [COLOR orange]{0}[/COLOR] ROMs in LaunchBox Offline Scraper database'.format(platform)
    vlauncher_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_LaunchBox_Offline_icon.png').getPath()
    vlauncher_fanart = g_PATHS.FANART_FILE_PATH.getPath()
    vlauncher_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_LaunchBox_Offline_poster.png').getPath()

    listitem = xbmcgui.ListItem(title_str)
    listitem.setInfo('video', {'title' : title_str, 'plot' : plot_text, 'overlay' : 4 })
    listitem.setArt({'icon' : vlauncher_icon, 'fanart' : vlauncher_fanart, 'poster' : vlauncher_poster})
    # >> Set platform property to render platform icon on skins.
    listitem.setProperty('platform', platform)
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)

    commands = []
    commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
    listitem.addContextMenuItems(commands)

    url_str = m_misc_url('SHOW_LB_SCRAPER_ROMS', platform)
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = True)

# -------------------------------------------------------------------------------------------------
# Utilities and Global reports
# -------------------------------------------------------------------------------------------------
def m_gui_render_Utilities_vlaunchers():
    # --- Common context menu for all VLaunchers ---
    commands = []
    commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))

    # --- Check/Update all databases ---
    # This command also available from settings for AEL DB migrations.
    vcategory_name   = 'Check/Update all databases'
    vcategory_plot   = 'Check/Update all databases'
    vcategory_icon   = g_PATHS.ICON_FILE_PATH.getPath()
    vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
    listitem = xbmcgui.ListItem(vcategory_name)
    listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
    listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart})
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
    listitem.addContextMenuItems(commands)
    url_str = m_misc_url('EXECUTE_CHECK_DATABASES')
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = False)

    # --- Check all Launchers ---
    vcategory_name   = 'Check all Launchers'
    vcategory_plot   = 'Check all Launchers'
    vcategory_icon   = g_PATHS.ICON_FILE_PATH.getPath()
    vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
    listitem = xbmcgui.ListItem(vcategory_name)
    listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
    listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart})
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
    listitem.addContextMenuItems(commands)
    url_str = m_misc_url('EXECUTE_CHECK_LAUNCHERS')
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = False)

    # --- Check missing Assets/Artwork ---
    vcategory_name   = 'Check missing Assets/Artwork'
    vcategory_plot   = 'Check missing Assets/Artwork'
    vcategory_icon   = g_PATHS.ICON_FILE_PATH.getPath()
    vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
    listitem = xbmcgui.ListItem(vcategory_name)
    listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
    listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart})
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
    listitem.addContextMenuItems(commands)
    url_str = m_misc_url('EXECUTE_CHECK_MISSING_ASSETS')
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = False)

    # --- Check Retroarch installed cores ---
    vcategory_name   = 'Check Retroarch installed cores'
    vcategory_plot   = 'Check Retroarch installed cores'
    vcategory_icon   = g_PATHS.ICON_FILE_PATH.getPath()
    vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
    listitem = xbmcgui.ListItem(vcategory_name)
    listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
    listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart})
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
    listitem.addContextMenuItems(commands)
    url_str = m_misc_url('EXECUTE_CHECK_RETROARCH_CORES')
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = False)

    # --- Check Retroarch BIOSes ---
    # NOTE One table for mandatory BIOSes and another one for optical ones.
    vcategory_name   = 'Check Retroarch BIOSes'
    vcategory_plot   = 'Check Retroarch BIOSes'
    vcategory_icon   = g_PATHS.ICON_FILE_PATH.getPath()
    vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
    listitem = xbmcgui.ListItem(vcategory_name)
    listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
    listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart})
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
    listitem.addContextMenuItems(commands)
    url_str = m_misc_url('EXECUTE_CHECK_RETROARCH_BIOS')
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = False)

    # --- Check Retroplayer installed cores ---
    vcategory_name   = 'Check Retroplayer installed cores'
    vcategory_plot   = 'Check Retroplayer installed cores'
    vcategory_icon   = g_PATHS.ICON_FILE_PATH.getPath()
    vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
    listitem = xbmcgui.ListItem(vcategory_name)
    listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
    listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart})
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
    listitem.addContextMenuItems(commands)
    url_str = m_misc_url('EXECUTE_CHECK_RETROPLAYER_CORES')
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = False)

    # --- Check Retroarch BIOSes (mandatory only) ---
    vcategory_name   = 'Check Retroplayer BIOSes'
    vcategory_plot   = 'Check Retroplayer BIOSes'
    vcategory_icon   = g_PATHS.ICON_FILE_PATH.getPath()
    vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
    listitem = xbmcgui.ListItem(vcategory_name)
    listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
    listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart})
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
    listitem.addContextMenuItems(commands)
    url_str = m_misc_url('EXECUTE_CHECK_RETROPLAYER_BIOS')
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = False)

    # --- End of directory ---
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def m_gui_render_GlobalReports_vlaunchers():
    # --- Common context menu for all VLaunchers ---
    commands = []
    commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))

    # --- Global ROM statistics ---
    vcategory_name   = 'Global ROM statistics'
    vcategory_plot   = 'Global ROM statistics'
    vcategory_icon   = g_PATHS.ICON_FILE_PATH.getPath()
    vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
    listitem = xbmcgui.ListItem(vcategory_name)
    listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
    listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart})
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
    listitem.addContextMenuItems(commands)
    url_str = m_misc_url('EXECUTE_GLOBAL_ROM_STATS')
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = False)

    # --- Global ROM Audit statistics ---
    vcategory_name   = 'Global ROM Audit statistics'
    vcategory_plot   = 'Global ROM Audit statistics'
    vcategory_icon   = g_PATHS.ICON_FILE_PATH.getPath()
    vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
    listitem = xbmcgui.ListItem(vcategory_name)
    listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
    listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart})
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
    listitem.addContextMenuItems(commands)
    url_str = m_misc_url('EXECUTE_GLOBAL_AUDIT_STATS')
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = False)

    # --- End of directory ---
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

# ---------------------------------------------------------------------------------------------
# Launcher LisItem rendering
# ---------------------------------------------------------------------------------------------
#
# Renders Launchers inside a Category.
#
def m_command_render_launchers(category_id):
    # >> Set content type
    m_misc_set_all_sorting_methods()
    m_misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)
    m_misc_clear_AEL_Launcher_Content()

    category = g_ObjectFactory.find_category(category_id)
    launchers = g_ObjectFactory.find_launchers_in_cat(category_id)

    # --- If the category has no launchers then render nothing ---
    if not launchers or len(launchers) == 0:
        kodi_notify('Category {0} has no launchers. Add launchers first.'.format(category.get_name()))
        # NOTE If we return at this point Kodi produces and error:
        # ERROR: GetDirectory - Error getting plugin://plugin.program.advanced.emulator.launcher/?catID=8...f&com=SHOW_LAUNCHERS
        # ERROR: CGUIMediaWindow::GetDirectory(plugin://plugin.program.advanced.emulator.launcher/?catID=8...2f&com=SHOW_LAUNCHERS) failed
        #
        # How to avoid that? Rendering the categories again? If I call _command_render_categories() it does not work well, categories
        # are displayed in wrong alphabetical order and if go back clicking on .. the categories window is rendered again (instead of
        # exiting the addon).
        # self._command_render_categories()
        #
        # What about replacewindow? I also get the error, still not clear why...
        # xbmc.executebuiltin('ReplaceWindow(Programs,{0})'.format(self.base_url)) # Does not work
        # xbmc.executebuiltin('ReplaceWindow({0})'.format(self.base_url)) # Does not work
        #
        # Container.Refresh does not work either...
        # kodi_refresh_container()
        #
        # SOLUTION: call xbmcplugin.endOfDirectory(). It will create an empty ListItem wiht only '..' entry.
        #           User cannot open a context menu and the only option is to go back to categories display.
        #           No errors in Kodi log!
    else:
        # >> Render launcher rows of this launcher
        for launcher in sorted(launchers, key = lambda l : l.get_name()):
            m_gui_render_launcher_row(launcher)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

#
# Renders all launchers belonging to all categories.
# This function is called by skins to create shortcuts.
#
def m_command_render_all_launchers():
    launchers = g_LauncherRepository.find_all()

    # >> If no launchers render nothing
    if not launchers or len(launchers) == 0:
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # >> Render all launchers
    for launcher in sorted(launchers, key = lambda l : l.get_name()):
        self._gui_render_launcher_row(launcher)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def m_gui_render_launcher_row(launcher, launcher_raw_name = None):
    # --- Do not render row if launcher finished ---
    if launcher.is_finished() and g_settings['display_hide_finished']:
        return

    # --- Launcher tags ---
    # >> Do not plot ROM count on standalone launchers!
    # TODO add type in upgrade process
    if launcher_raw_name is None: launcher_raw_name = launcher.get_name()
    launcher_type = launcher.get_launcher_type()
    if   launcher_type == OBJ_LAUNCHER_STANDALONE:      launcher_desc = 'Std'
    elif launcher_type == OBJ_LAUNCHER_ROM:             launcher_desc = 'ROMs'
    elif launcher_type == OBJ_LAUNCHER_RETROPLAYER:     launcher_desc = 'KRetro'
    elif launcher_type == OBJ_LAUNCHER_RETROARCH:       launcher_desc = 'Retro'
    elif launcher_type == OBJ_LAUNCHER_LNK:             launcher_desc = 'LNKs'
    elif launcher_type == OBJ_LAUNCHER_STEAM:           launcher_desc = 'Steam'
    elif launcher_type == OBJ_LAUNCHER_NVGAMESTREAM:    launcher_desc = 'Strm'
    elif launcher_type == OBJ_LAUNCHER_KODI_FAVOURITES: launcher_desc = 'Fav'
    else:                                               launcher_desc = '???'
    launcher_dic = launcher.get_data_dic()
    if launcher.supports_launching_roms() and g_settings['display_launcher_roms']:
        if launcher_dic['nointro_xml_file']:
            # --- ROM launcher with DAT file ---
            if launcher_dic['launcher_display_mode'] == LAUNCHER_DMODE_FLAT:
                num_have    = launcher_dic['num_have']
                num_miss    = launcher_dic['num_miss']
                num_unknown = launcher_dic['num_unknown']
                launcher_name = '{0} [COLOR orange]({1} Have / {2} Miss / {3} Unk)[/COLOR]'.format(
                    launcher_raw_name, num_have, num_miss, num_unknown)
            elif launcher_dic['launcher_display_mode'] == LAUNCHER_DMODE_PCLONE:
                num_parents = launcher_dic['num_parents']
                num_clones  = launcher_dic['num_clones']
                launcher_name = '{0} [COLOR orange]({1} Par / {2} Clo)[/COLOR]'.format(
                    launcher_raw_name, num_parents, num_clones)
            elif launcher_dic['launcher_display_mode'] == LAUNCHER_DMODE_1G1R:
                num_parents = launcher_dic['num_parents']
                launcher_name = '{0} [COLOR orange]({1} Games)[/COLOR]'.format(launcher_raw_name, num_parents)
            else:
                launcher_name = '{0} [COLOR red](ERROR)[/COLOR]'.format(launcher_raw_name)
        else:
            # --- ROM launcher with no DAT file ---
            num_roms = launcher_dic['num_roms']
            if num_roms == 0:
                launcher_name = '{0} [COLOR orange](No ROMs)[/COLOR]'.format(launcher_raw_name)
            elif num_roms == 1:
                launcher_name = '{0} [COLOR orange]({1} ROM)[/COLOR]'.format(launcher_raw_name, num_roms)
            else:
                launcher_name = '{0} [COLOR orange]({1} ROMs)[/COLOR]'.format(launcher_raw_name, num_roms)
    else:
        launcher_name = '{0} [COLOR chocolate]({1})[/COLOR]'.format(launcher_raw_name, launcher_desc)

    # --- Create listitem row ---
    ICON_OVERLAY = 5 if launcher_dic['finished'] else 4
    listitem = xbmcgui.ListItem(launcher_name)
    # >> BUG in Jarvis/Krypton skins. If 'year' is set to empty string a 0 is displayed on the
    # >>     skin. If year is not set then the correct icon is shown.
    if launcher_dic['m_year']:
        listitem.setInfo('video', {'title'   : launcher_name,             'year'    : launcher_dic['m_year'],
                                   'genre'   : launcher_dic['m_genre'],   'studio'  : launcher_dic['m_developer'],
                                   'rating'  : launcher_dic['m_rating'],  'plot'    : launcher_dic['m_plot'],
                                   'trailer' : launcher_dic['s_trailer'], 'overlay' : ICON_OVERLAY })
    else:
        listitem.setInfo('video', {'title'   : launcher_name,
                                   'genre'   : launcher_dic['m_genre'],   'studio'  : launcher_dic['m_developer'],
                                   'rating'  : launcher_dic['m_rating'],  'plot'    : launcher_dic['m_plot'],
                                   'trailer' : launcher_dic['s_trailer'], 'overlay' : ICON_OVERLAY })
    listitem.setProperty('platform', launcher_dic['platform'])
    if launcher_dic['rompath']:
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
        listitem.setProperty(AEL_NUMITEMS_LABEL, str(launcher_dic['num_roms']))
    else:
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_STD_LAUNCHER)

    # --- Set ListItem artwork ---
    kodi_thumb     = 'DefaultFolder.png' if launcher_dic['rompath'] else 'DefaultProgram.png'
    icon_path      = asset_get_default_asset_Category(launcher_dic, 'default_icon', kodi_thumb)
    fanart_path    = asset_get_default_asset_Category(launcher_dic, 'default_fanart')
    banner_path    = asset_get_default_asset_Category(launcher_dic, 'default_banner')
    poster_path    = asset_get_default_asset_Category(launcher_dic, 'default_poster')
    clearlogo_path = asset_get_default_asset_Category(launcher_dic, 'default_clearlogo')
    listitem.setArt({'icon'   : icon_path,   'fanart' : fanart_path, 'banner' : banner_path,
                     'poster' : poster_path, 'clearlogo' : clearlogo_path,
                     'controller' : launcher_dic['s_controller']})

    # --- Create context menu ---
    # Categories/Launchers/ROMs context menu order
    #  1) View XXXXX
    #  2) Edit XXXXX
    #  3) Add launcher (Categories) | Add ROMs (Launchers)
    #  4) Search XXXX
    #  5) Create new XXXX
    commands = []
    launcherID = launcher_dic['id']
    categoryID = launcher_dic['categoryID']
    
    commands.append(('View', m_misc_url_RunPlugin('VIEW', categoryID, launcherID) ))
    commands.append(('Edit/Export Launcher', m_misc_url_RunPlugin('EDIT_LAUNCHER', categoryID, launcherID) ))
    # >> ONLY for ROM launchers
    if launcher.supports_launching_roms():
        commands.append(('Scan ROMs', m_misc_url_RunPlugin('SCAN_ROMS', categoryID, launcherID) ))
        commands.append(('Search ROMs in Launcher', m_misc_url_RunPlugin('SEARCH_LAUNCHER', categoryID, launcherID) ))
    commands.append(('Add new Launcher', m_misc_url_RunPlugin('ADD_LAUNCHER', categoryID) ))
    # >> Launchers in addon root should be able to create a new category
    if categoryID == VCATEGORY_ADDONROOT_ID:
        commands.append(('Add new Category', m_misc_url_RunPlugin('ADD_CATEGORY')))
    commands.append(('Open Kodi file manager', 'ActivateWindow(filemanager)' ))
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__) ))
    listitem.addContextMenuItems(commands)

    # --- Add Launcher row to ListItem ---
    if launcher_dic['rompath']:
        url_str = m_misc_url('SHOW_ROMS', categoryID, launcherID)
        folder_flag = True
    else:
        url_str = m_misc_url('LAUNCH_STANDALONE', categoryID, launcherID)
        folder_flag = False
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = folder_flag)

# ---------------------------------------------------------------------------------------------
# ROM LisItem rendering
# ---------------------------------------------------------------------------------------------
#
# Render clone ROMs. romID is the parent ROM.
# This is only called in Parent/Clone and 1G1R display modes.
#
def m_command_render_clone_roms(categoryID, launcherID, romID):
    # --- Set content type and sorting methods ---
    m_misc_set_all_sorting_methods()
    m_misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)
    m_misc_clear_AEL_Launcher_Content()
    selectedLauncher = g_LauncherRepository.find(launcherID)

    # --- Check for errors ---
    if selectedLauncher is None:
        log_error('_command_render_clone_roms() Launcher ID not found in launchers')
        kodi_dialog_OK('_command_render_clone_roms(): Launcher ID not found in launchers. Report this bug.')
        return
    
    # --- Load ROMs for this launcher ---
    rom_count = selectedLauncher.actual_amount_of_roms()
    if rom_count == 0:
        kodi_notify('Launcher JSON database empty. Add ROMs to launcher.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # --- Load parent/clone index ---
    pclone_index = selectedLauncher.get_pclone_indices()
    if not pclone_index:
        kodi_notify('Parent list JSON database is empty.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # --- Build parent and clones dictionary of ROMs ---
    roms = []
    # >> Add parent ROM except if the parent if the fake paren ROM
    if romID != UNKNOWN_ROMS_PARENT_ID: 
        parent_rom = selectedLauncher.select_rom(romID)
        roms.append(parent_rom)

    # >> Add clones, if any
    for rom_id in pclone_index[romID]:
        clone_rom = selectedLauncher.select_rom(rom_id)
        roms.append(clone_rom)

    log_verb('_command_render_clone_roms() Parent ID {0}'.format(romID))
    log_verb('_command_render_clone_roms() Number of clone ROMs = {0}'.format(len(roms)))
    # for key in roms:
    #     log_debug('key   = {0}'.format(key))
    #     log_debug('value = {0}'.format(roms[key]))

    # --- ROM display filter ---        
    dp_mode              = selectedLauncher.get_nointro_display_mode()
    dp_modes_for_have    = [NOINTRO_DMODE_HAVE, NOINTRO_DMODE_HAVE_UNK, NOINTRO_DMODE_HAVE_MISS]
    dp_modes_for_miss    = [NOINTRO_DMODE_HAVE_MISS, NOINTRO_DMODE_MISS, NOINTRO_DMODE_MISS_UNK]
    dp_modes_for_unknown = [NOINTRO_DMODE_HAVE_UNK, NOINTRO_DMODE_MISS_UNK, NOINTRO_DMODE_UNK]

    if selectedLauncher.has_nointro_xml() and dp_mode != NOINTRO_DMODE_ALL:
        filtered_roms = []
        for rom in roms:
            nointro_status = rom.get_nointro_status()
        
            if nointro_status == NOINTRO_STATUS_HAVE and dp_mode in dp_mode_for_have:
                filtered_roms.append(rom)

            elif nointro_status == NOINTRO_STATUS_MISS and dp_mode in dp_modes_for_miss:
                filtered_roms.append(rom)

            elif nointro_status == NOINTRO_STATUS_UNKNOWN and dp_mode in dp_modes_for_unknown:
                filtered_roms.append(rom)

            # >> Always copy roms with unknown status (NOINTRO_STATUS_NONE)
            else:
                filtered_roms.append(rom)
        roms = filtered_roms
        if not roms:
            kodi_notify('No ROMs to show with current filtering settings.')
            xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
            return

    # --- Render ROMs ---
    view_mode       = selectedLauncher.get_display_mode()
    fav_launcher    = g_LauncherRepository.find(VLAUNCHER_FAVOURITES_ID)
    roms_fav_set    = set(fav_launcher.get_rom_ids())

    for rom in sorted(roms, key = lambda r : r.get_name()):
        self._gui_render_rom_row(categoryID, launcherID, rom.get_data(), rom.get_id() in roms_fav_set, view_mode, False)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

#
# Renders the ROMs listbox for a given standard launcher or the Parent ROMs of a PClone launcher.
#
def m_command_render_roms(categoryID, launcherID):
    launcher = g_LauncherRepository.find(launcherID)

    # --- Check for errors ---
    if launcher is None:
        log_error('_command_render_roms() Launcher ID not found in launchers repository')
        kodi_dialog_OK('_command_render_roms(): Launcher ID not found in launchers repository. Report this bug.')
        return

    if not launcher.supports_launching_roms():
        log_error('_command_render_roms() Launcher does not support launching roms')
        kodi_dialog_OK('_command_render_roms(): Launcher does not support launching roms. Report this bug.')
        return

    # --- Set content type and sorting methods ---
    m_misc_set_all_sorting_methods()
    m_misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)
    self._misc_set_AEL_Launcher_Content(selectedLauncher)

    # --- Render in Flat mode (all ROMs) or Parent/Clone or 1G1R mode---
    # >> Parent/Clone mode and 1G1R modes are very similar in terms of programming.
    loading_ticks_start = time.time()
    
    launcher.load_roms()
    if not launcher.has_roms():
        kodi_notify('Launcher XML/JSON empty. Add ROMs to launcher.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return
            
    view_mode = launcher.get_display_mode()
    dp_mode   = launcher.get_nointro_display_mode()
    
    # --- ROM display filter ---
    if launcher.has_nointro_xml() and dp_mode != NOINTRO_DMODE_ALL:
        roms = launcher.get_roms_filtered()
        if not roms:
            kodi_notify('No ROMs to show with current filtering settings.')
            xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
            return
    else:
        roms = launcher.get_roms()

    # --- Load favourites ---
    # >> Optimisation: Transform the dictionary keys into a set. Sets are the fastest
    #    when checking if an element exists.
    fav_launcher = g_LauncherRepository.find(VLAUNCHER_FAVOURITES_ID)
    fav_roms = fav_launcher.get_roms()
    fav_rom_ids = set(f.get_id() for f in fav_roms)

    #roms_fav = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
    #roms_fav_set = set(roms_fav.keys())

    # --- Display ROMs ---
    loading_ticks_end = time.time()
    rendering_ticks_start = time.time()
    
    for rom in sorted(roms, key = lambda r : r.get_name()):
        if view_mode == LAUNCHER_DMODE_FLAT:
            self._gui_render_rom_row(categoryID, launcherID, rom.get_data(), rom.get_id() in fav_rom_ids, view_mode, False)
        else:
            num_clones = len(pclone_index[key])
            self._gui_render_rom_row(categoryID, launcherID, rom.get_data(), rom.get_id() in fav_rom_ids, view_mode, True, num_clones)

    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
    rendering_ticks_end = time.time()

    # --- DEBUG Data loading/rendering statistics ---
    log_debug('Loading seconds   {0}'.format(loading_ticks_end - loading_ticks_start))
    log_debug('Rendering seconds {0}'.format(rendering_ticks_end - rendering_ticks_start))

#
# Former _add_rom()
# Note that if we are rendering favourites, categoryID = VCATEGORY_FAVOURITES_ID
# Note that if we are rendering virtual launchers, categoryID = VCATEGORY_*_ID
#
def m_gui_render_rom_row(categoryID, launcherID, rom,
                        rom_in_fav = False, view_mode = LAUNCHER_DMODE_FLAT,
                        is_parent_launcher = False, num_clones = 0):

    # --- Do not render row if ROM is finished ---
    if rom['finished'] and g_settings['display_hide_finished']: return

    # --- Default values for flags ---
    AEL_InFav_bool_value     = AEL_INFAV_BOOL_VALUE_FALSE
    AEL_MultiDisc_bool_value = AEL_MULTIDISC_BOOL_VALUE_FALSE
    AEL_Fav_stat_value       = AEL_FAV_STAT_VALUE_NONE
    AEL_NoIntro_stat_value   = AEL_NOINTRO_STAT_VALUE_NONE
    AEL_PClone_stat_value    = AEL_PCLONE_STAT_VALUE_NONE

    # --- Create listitem row ---
    # NOTE A possible optimization is to compute rom_name, asset paths and flags on the calling 
    #      function. A lot of ifs will be avoided here and that will increase speed.
    rom_raw_name = rom['m_name']
    if categoryID == VCATEGORY_FAVOURITES_ID:
        icon_path      = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_icon', 'DefaultProgram.png')
        fanart_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_fanart')
        banner_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_banner')
        poster_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_poster')
        clearlogo_path = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_clearlogo')
        platform        = rom['platform']

        # --- Favourite status flag ---
        if g_settings['display_fav_status']:
            if   rom['fav_status'] == 'OK':                rom_name = '{0} [COLOR green][OK][/COLOR]'.format(rom_raw_name)
            elif rom['fav_status'] == 'Unlinked ROM':      rom_name = '{0} [COLOR yellow][Unlinked ROM][/COLOR]'.format(rom_raw_name)
            elif rom['fav_status'] == 'Unlinked Launcher': rom_name = '{0} [COLOR yellow][Unlinked Launcher][/COLOR]'.format(rom_raw_name)
            elif rom['fav_status'] == 'Broken':            rom_name = '{0} [COLOR red][Broken][/COLOR]'.format(rom_raw_name)
            else:                                          rom_name = rom_raw_name
        else:
            rom_name = rom_raw_name
        if   rom['fav_status'] == 'OK':                AEL_Fav_stat_value = AEL_FAV_STAT_VALUE_OK
        elif rom['fav_status'] == 'Unlinked ROM':      AEL_Fav_stat_value = AEL_FAV_STAT_VALUE_UNLINKED_ROM
        elif rom['fav_status'] == 'Unlinked Launcher': AEL_Fav_stat_value = AEL_FAV_STAT_VALUE_UNLINKED_LAUNCHER
        elif rom['fav_status'] == 'Broken':            AEL_Fav_stat_value = AEL_FAV_STAT_VALUE_BROKEN
        else:                                          AEL_Fav_stat_value = AEL_FAV_STAT_VALUE_UNKNOWN
    elif categoryID == VCATEGORY_COLLECTIONS_ID:
        icon_path      = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_icon', 'DefaultProgram.png')
        fanart_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_fanart')
        banner_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_banner')
        poster_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_poster')
        clearlogo_path = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_clearlogo')
        platform       = rom['platform']

        # --- Favourite status flag ---
        if g_settings['display_fav_status']:
            if   rom['fav_status'] == 'OK':                rom_name = '{0} [COLOR green][OK][/COLOR]'.format(rom_raw_name)
            elif rom['fav_status'] == 'Unlinked ROM':      rom_name = '{0} [COLOR yellow][Unlinked ROM][/COLOR]'.format(rom_raw_name)
            elif rom['fav_status'] == 'Unlinked Launcher': rom_name = '{0} [COLOR yellow][Unlinked Launcher][/COLOR]'.format(rom_raw_name)
            elif rom['fav_status'] == 'Broken':            rom_name = '{0} [COLOR red][Broken][/COLOR]'.format(rom_raw_name)
            else:                                          rom_name = rom_raw_name
        else:
            rom_name = rom_raw_name
        if   rom['fav_status'] == 'OK':                AEL_Fav_stat_value = AEL_FAV_STAT_VALUE_OK
        elif rom['fav_status'] == 'Unlinked ROM':      AEL_Fav_stat_value = AEL_FAV_STAT_VALUE_UNLINKED_ROM
        elif rom['fav_status'] == 'Unlinked Launcher': AEL_Fav_stat_value = AEL_FAV_STAT_VALUE_UNLINKED_LAUNCHER
        elif rom['fav_status'] == 'Broken':            AEL_Fav_stat_value = AEL_FAV_STAT_VALUE_BROKEN
        else:                                          AEL_Fav_stat_value = AEL_FAV_STAT_VALUE_UNKNOWN
    elif categoryID == VCATEGORY_RECENT_ID:
        icon_path      = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_icon', 'DefaultProgram.png')
        fanart_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_fanart')
        banner_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_banner')
        poster_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_poster')
        clearlogo_path = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_clearlogo')
        platform       =  rom['platform'] if 'platform' in rom else ''
        rom_name = rom_raw_name
    elif categoryID == VCATEGORY_MOST_PLAYED_ID:
        icon_path      = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_icon', 'DefaultProgram.png')
        fanart_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_fanart')
        banner_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_banner')
        poster_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_poster')
        clearlogo_path = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_clearlogo')
        platform       =  rom['platform'] if 'platform' in rom else ''
        # >> Render number of number the ROM has been launched
        if rom['launch_count'] == 1:
            rom_name = '{0} [COLOR orange][{1} time][/COLOR]'.format(rom_raw_name, rom['launch_count'])
        else:
            rom_name = '{0} [COLOR orange][{1} times][/COLOR]'.format(rom_raw_name, rom['launch_count'])
    elif categoryID == VCATEGORY_TITLE_ID    or categoryID == VCATEGORY_YEARS_ID or \
         categoryID == VCATEGORY_GENRE_ID    or categoryID == VCATEGORY_DEVELOPER_ID or \
         categoryID == VCATEGORY_NPLAYERS_ID or categoryID == VCATEGORY_ESRB_ID or \
         categoryID == VCATEGORY_RATING_ID   or categoryID == VCATEGORY_CATEGORY_ID:
        icon_path      = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_icon', 'DefaultProgram.png')
        fanart_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_fanart')
        banner_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_banner')
        poster_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_poster')
        clearlogo_path = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_clearlogo')
        platform       =  rom['platform'] if 'platform' in rom else ''

        # --- NoIntro status flag ---
        nstat = rom['nointro_status']
        if g_settings['display_nointro_stat']:
            if   nstat == NOINTRO_STATUS_HAVE:    rom_name = '{0} [COLOR green][Have][/COLOR]'.format(rom_raw_name)
            elif nstat == NOINTRO_STATUS_MISS:    rom_name = '{0} [COLOR magenta][Miss][/COLOR]'.format(rom_raw_name)
            elif nstat == NOINTRO_STATUS_UNKNOWN: rom_name = '{0} [COLOR yellow][Unknown][/COLOR]'.format(rom_raw_name)
            elif nstat == NOINTRO_STATUS_NONE:    rom_name = rom_raw_name
            else:                                 rom_name = '{0} [COLOR red][Status error][/COLOR]'.format(rom_raw_name)
        else:
            rom_name = rom_raw_name
        if   nstat == NOINTRO_STATUS_HAVE:    AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_HAVE
        elif nstat == NOINTRO_STATUS_MISS:    AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_MISS
        elif nstat == NOINTRO_STATUS_UNKNOWN: AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_UNKNOWN
        elif nstat == NOINTRO_STATUS_NONE:    AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_NONE

        # --- In Favourites ROM flag ---
        if g_settings['display_rom_in_fav'] and rom_in_fav: rom_name += ' [COLOR violet][Fav][/COLOR]'
        if rom_in_fav: AEL_InFav_bool_value = AEL_INFAV_BOOL_VALUE_TRUE
    # --- Standard launcher ---
    else:
        # >> If ROM has no fanart then use launcher fanart
        launcher = g_LauncherRepository.find(launcherID)
        launcher_data  = launcher.get_data()

        kodi_def_icon = launcher_data['s_icon'] if launcher_data['s_icon'] else 'DefaultProgram.png'
        icon_path      = asset_get_default_asset_Launcher_ROM(rom, launcher_data, 'roms_default_icon', kodi_def_icon)
        fanart_path    = asset_get_default_asset_Launcher_ROM(rom, launcher_data, 'roms_default_fanart', launcher_data['s_fanart'])
        banner_path    = asset_get_default_asset_Launcher_ROM(rom, launcher_data, 'roms_default_banner')
        poster_path    = asset_get_default_asset_Launcher_ROM(rom, launcher_data, 'roms_default_poster')
        clearlogo_path = asset_get_default_asset_Launcher_ROM(rom, launcher_data, 'roms_default_clearlogo')
        platform = launcher.get_platform()

        # --- parent_launcher is True when rendering Parent ROMs in Parent/Clone view mode ---
        nstat = rom['nointro_status']
        if g_settings['display_nointro_stat']:
            if   nstat == NOINTRO_STATUS_HAVE:    rom_name = '{0} [COLOR green][Have][/COLOR]'.format(rom_raw_name)
            elif nstat == NOINTRO_STATUS_MISS:    rom_name = '{0} [COLOR magenta][Miss][/COLOR]'.format(rom_raw_name)
            elif nstat == NOINTRO_STATUS_UNKNOWN: rom_name = '{0} [COLOR yellow][Unknown][/COLOR]'.format(rom_raw_name)
            elif nstat == NOINTRO_STATUS_NONE:    rom_name = rom_raw_name
            else:                                 rom_name = '{0} [COLOR red][Status error][/COLOR]'.format(rom_raw_name)
        else:
            rom_name = rom_raw_name
        if is_parent_launcher and num_clones > 0:
            rom_name += ' [COLOR orange][{0} clones][/COLOR]'.format(num_clones)
        if   nstat == NOINTRO_STATUS_HAVE:    AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_HAVE
        elif nstat == NOINTRO_STATUS_MISS:    AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_MISS
        elif nstat == NOINTRO_STATUS_UNKNOWN: AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_UNKNOWN
        elif nstat == NOINTRO_STATUS_NONE:    AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_NONE
        # --- Mark clone ROMs ---
        if 'pclone_status' in rom:
            pclone_status = rom['pclone_status']
        else:
            pclone_status = ''

        if pclone_status == PCLONE_STATUS_CLONE: rom_name += ' [COLOR orange][Clo][/COLOR]'
        if   pclone_status == PCLONE_STATUS_PARENT: AEL_PClone_stat_value = AEL_PCLONE_STAT_VALUE_PARENT
        elif pclone_status == PCLONE_STATUS_CLONE:  AEL_PClone_stat_value = AEL_PCLONE_STAT_VALUE_CLONE
        # --- In Favourites ROM flag ---
        if g_settings['display_rom_in_fav'] and rom_in_fav: rom_name += ' [COLOR violet][Fav][/COLOR]'
        if rom_in_fav: AEL_InFav_bool_value = AEL_INFAV_BOOL_VALUE_TRUE

    # --- Set common flags to all launchers---
    if  'disks' in rom and rom['disks']: AEL_MultiDisc_bool_value = AEL_MULTIDISC_BOOL_VALUE_TRUE

    # --- Add ROM to lisitem ---
    ICON_OVERLAY = 5 if rom['finished'] else 4
    listitem = xbmcgui.ListItem(rom_name)

    # Interesting... if text formatting labels are set in xbmcgui.ListItem() do not work. However, if
    # labels are set as Title in setInfo(), then they work but the alphabetical order is lost!
    # I solved this alphabetical ordering issue by placing a coloured tag [Fav] at the and of the ROM name
    # instead of changing the whole row colour.
    # >> BUG in Jarvis/Krypton skins. If 'year' is set to empty string a 0 is displayed on the
    # >>     skin. If year is not set then the correct icon is shown.
    if rom['m_year']:
        listitem.setInfo('video', {'title'   : rom_name,         'year'    : rom['m_year'],
                                   'genre'   : rom['m_genre'],   'studio'  : rom['m_developer'],
                                   'rating'  : rom['m_rating'],  'plot'    : rom['m_plot'],
                                   'trailer' : rom['s_trailer'], 'overlay' : ICON_OVERLAY })
    else:
        listitem.setInfo('video', {'title'   : rom_name,
                                   'genre'   : rom['m_genre'],   'studio'  : rom['m_developer'],
                                   'rating'  : rom['m_rating'],  'plot'    : rom['m_plot'],
                                   'trailer' : rom['s_trailer'], 'overlay' : ICON_OVERLAY })
    listitem.setProperty('nplayers', rom['m_nplayers'])
    listitem.setProperty('esrb', rom['m_esrb'])
    listitem.setProperty('platform', platform)
    listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM)

    # --- Set ROM artwork ---
    # >> AEL custom artwork fields
    listitem.setArt({'title'     : rom['s_title'],     'snap'    : rom['s_snap'],
                     'boxfront'  : rom['s_boxfront'],  'boxback' : rom['s_boxback'], 
                     'cartridge' : rom['s_cartridge'], 'flyer'   : rom['s_flyer'],
                     'map'       : rom['s_map'] })

    # >> Kodi official artwork fields
    listitem.setArt({'icon'   : icon_path,   'fanart' : fanart_path, 'banner' : banner_path,
                     'poster' : poster_path, 'clearlogo' : clearlogo_path})

    # --- ROM extrafanart ---
    # >> Build extrafanart dictionary
    # extrafanart_dic = {}
    # listitem.setArt(extrafanart_dic)

    # http://forum.kodi.tv/showthread.php?tid=221690&pid=1960874#pid1960874
    # This appears to be a common area of confusion with many addon developers, isPlayable doesn't
    # really mean the item is a playable, it only means Kodi will wait for a call to
    # xbmcplugin.setResolvedUrl and when this is called it will play the item. If you are going
    # to play the item using xbmc.Player().play() then as far as Kodi is concerned it isn't playable.
    #
    # http://forum.kodi.tv/showthread.php?tid=173986&pid=1519987#pid1519987
    # Otherwise the plugin is called back with an invalid handle (sys.arg[1]). It took me a lot of time
    # to figure this out...
    # if self._content_type == 'video':
    # listitem.setProperty('IsPlayable', 'false')
    # log_debug('Item Row IsPlayable false')

    # --- ROM flags (Skins will use these flags to render icons) ---
    listitem.setProperty(AEL_INFAV_BOOL_LABEL,     AEL_InFav_bool_value)
    listitem.setProperty(AEL_MULTIDISC_BOOL_LABEL, AEL_MultiDisc_bool_value)
    listitem.setProperty(AEL_FAV_STAT_LABEL,       AEL_Fav_stat_value)
    listitem.setProperty(AEL_NOINTRO_STAT_LABEL,   AEL_NoIntro_stat_value)
    listitem.setProperty(AEL_PCLONE_STAT_LABEL,    AEL_PClone_stat_value)

    # --- Create context menu ---
    romID = rom['id']
    commands = []
    if categoryID == VCATEGORY_FAVOURITES_ID:
        commands.append(('View Favourite ROM',         m_misc_url_RunPlugin('VIEW',              categoryID, launcherID, romID)))
        commands.append(('Edit ROM in Favourites',     m_misc_url_RunPlugin('EDIT_ROM',          categoryID, launcherID, romID)))
        commands.append(('Add ROM to Collection',      m_misc_url_RunPlugin('ADD_TO_COLLECTION', categoryID, launcherID, romID)))
        commands.append(('Search ROMs in Favourites',  m_misc_url_RunPlugin('SEARCH_LAUNCHER',   categoryID, launcherID)))
        commands.append(('Manage Favourite ROMs',      m_misc_url_RunPlugin('MANAGE_FAV',        categoryID, launcherID, romID)))
    elif categoryID == VCATEGORY_COLLECTIONS_ID:
        commands.append(('View Collection ROM',        m_misc_url_RunPlugin('VIEW',              categoryID, launcherID, romID)))
        commands.append(('Edit ROM in Collection',     m_misc_url_RunPlugin('EDIT_ROM',          categoryID, launcherID, romID)))
        commands.append(('Add ROM to AEL Favourites',  m_misc_url_RunPlugin('ADD_TO_FAV',        categoryID, launcherID, romID)))
        commands.append(('Search ROMs in Collection',  m_misc_url_RunPlugin('SEARCH_LAUNCHER',   categoryID, launcherID)))
        commands.append(('Manage Collection ROMs',     m_misc_url_RunPlugin('MANAGE_FAV',        categoryID, launcherID, romID)))
    elif categoryID == VCATEGORY_RECENT_ID or categoryID == VCATEGORY_MOST_PLAYED_ID:
        commands.append(('View ROM data', m_misc_url_RunPlugin('VIEW', categoryID, launcherID, romID)))
    elif categoryID == VCATEGORY_TITLE_ID    or categoryID == VCATEGORY_YEARS_ID  or \
         categoryID == VCATEGORY_GENRE_ID    or categoryID == VCATEGORY_DEVELOPER_ID or \
         categoryID == VCATEGORY_NPLAYERS_ID or categoryID == VCATEGORY_ESRB_ID   or \
         categoryID == VCATEGORY_RATING_ID   or categoryID == VCATEGORY_CATEGORY_ID:
        commands.append(('View ROM data',                   m_misc_url_RunPlugin('VIEW',              categoryID, launcherID, romID)))
        commands.append(('Add ROM to AEL Favourites',       m_misc_url_RunPlugin('ADD_TO_FAV',        categoryID, launcherID, romID)))
        commands.append(('Add ROM to Collection',           m_misc_url_RunPlugin('ADD_TO_COLLECTION', categoryID, launcherID, romID)))
        commands.append(('Search ROMs in Virtual Launcher', m_misc_url_RunPlugin('SEARCH_LAUNCHER',   categoryID, launcherID)))
    else:
        commands.append(('View ROM/Launcher',         m_misc_url_RunPlugin('VIEW',              categoryID, launcherID, romID)))
        if is_parent_launcher and num_clones > 0 and view_mode == LAUNCHER_DMODE_1G1R:
            commands.append(('Show clones', m_misc_url_RunPlugin('EXEC_SHOW_CLONE_ROMS', categoryID, launcherID, romID)))
        commands.append(('Edit ROM',                  m_misc_url_RunPlugin('EDIT_ROM',          categoryID, launcherID, romID)))
        commands.append(('Add ROM to AEL Favourites', m_misc_url_RunPlugin('ADD_TO_FAV',        categoryID, launcherID, romID)))
        commands.append(('Add ROM to Collection',     m_misc_url_RunPlugin('ADD_TO_COLLECTION', categoryID, launcherID, romID)))
        commands.append(('Search ROMs in Launcher',   m_misc_url_RunPlugin('SEARCH_LAUNCHER',   categoryID, launcherID)))
        commands.append(('Edit Launcher',             m_misc_url_RunPlugin('EDIT_LAUNCHER',     categoryID, launcherID)))
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
    listitem.addContextMenuItems(commands)

    # --- Add row ---
    # URLs must be different depending on the content type. If not Kodi log will be filled with:
    # WARNING: CreateLoader - unsupported protocol(plugin) in the log. See http://forum.kodi.tv/showthread.php?tid=187954
    if is_parent_launcher and num_clones > 0 and view_mode == LAUNCHER_DMODE_PCLONE:
        url_str = m_misc_url('SHOW_CLONE_ROMS', categoryID, launcherID, romID)
        xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = True)
    else:
        url_str = m_misc_url('LAUNCH_ROM', categoryID, launcherID, romID)
        xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = False)

def m_gui_render_AEL_scraper_rom_row(platform, game):
    # --- Add ROM to lisitem ---
    kodi_def_thumb = 'DefaultProgram.png'
    ICON_OVERLAY = 4
    listitem = xbmcgui.ListItem(game['description'])

    listitem.setInfo('video', {'title'   : game['description'],  'year'    : game['year'],
                               'genre'   : game['genre'],        'plot'    : game['story'],
                               'studio'  : game['manufacturer'], 'overlay' : ICON_OVERLAY })
    listitem.setProperty('nplayers', game['player'])
    listitem.setProperty('esrb', game['rating'])
    listitem.setProperty('platform', platform)

    # --- Set ROM artwork ---
    listitem.setArt({'icon' : kodi_def_thumb})

    # --- Create context menu ---
    commands = []
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
    listitem.addContextMenuItems(commands)

    # --- Add row ---
    # When user clicks on a ROM show the raw database entry
    url_str = m_misc_url('VIEW_OS_ROM', 'AEL', platform, game['name'])
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = False)

def m_gui_render_LB_scraper_rom_row(platform, game):
    # --- Add ROM to lisitem ---
    kodi_def_thumb = 'DefaultProgram.png'
    ICON_OVERLAY = 4
    listitem = xbmcgui.ListItem(game['Name'])

    listitem.setInfo('video', {'title'   : game['Name'],      'year'    : game['ReleaseYear'],
                               'genre'   : game['Genres'],    'plot'    : game['Overview'],
                               'studio'  : game['Publisher'], 'overlay' : ICON_OVERLAY })
    listitem.setProperty('nplayers', game['MaxPlayers'])
    listitem.setProperty('esrb', game['ESRB'])
    listitem.setProperty('platform', platform)

    # --- Set ROM artwork ---
    listitem.setArt({'icon' : kodi_def_thumb})

    # --- Create context menu ---
    commands = []
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
    listitem.addContextMenuItems(commands)

    # --- Add row ---
    # When user clicks on a ROM show the raw database entry
    url_str = m_misc_url('VIEW_OS_ROM', 'LaunchBox', platform, game['name'])
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = False)

#
# Renders the special Launcher Favourites ROMs, which is actually very similar to a ROM launcher.
# Note that only ROMs in a launcher can be added to favourites. Thus, no standalone launchers.
# If user deletes launcher or favourite ROMs the ROM in favourites remain.
# Favourites ROM information includes the application launcher and arguments to launch the ROM.
# Basically, once a ROM is added to favourites is becomes kind of a standalone launcher.
# Favourites has categoryID = 0 and launcherID = 0. Thus, other functions can differentiate
# between a standard ROM and a favourite ROM.
#
# What if user changes the favourites Thumb/Fanart??? Where do we store them???
# What about the NFO files of favourite ROMs???
#
# PROBLEM If user rescan ROMs then same ROMs will have different ID. An option to "relink"
#         the favourites with their original ROMs must be provided, provided that the launcher
#         is the same.
# IMPROVEMENT Maybe it could be interesting to be able to export the list of favourites
#             to HTML or something like that.
#
def m_command_render_favourite_roms():
    # >> Content type and sorting method
    m_misc_set_all_sorting_methods()
    m_misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)
    m_misc_clear_AEL_Launcher_Content()

    # --- Load Favourite ROMs ---
    favourites_launcher = g_LauncherRepository.find(VLAUNCHER_FAVOURITES_ID)
    roms = favourites_launcher.get_roms()
    #roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
    if not roms or len(roms) == 0:
        kodi_notify('Favourites is empty. Add ROMs to Favourites first.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # --- Display Favourites ---
    for rom in sorted(roms, key= lambda r : r.get_name()):
        self._gui_render_rom_row(VCATEGORY_FAVOURITES_ID, VLAUNCHER_FAVOURITES_ID, rom.get_data())
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

# ---------------------------------------------------------------------------------------------
# Virtual Launcher LisItem rendering
# ---------------------------------------------------------------------------------------------
#
# Render virtual launchers inside a virtual category "Browse by":
#   Title, Year, Genre, Studio, Category, ...
#
def m_command_render_Browse_by_roms(virtual_categoryID):
    log_error('m_command_render_Browse_by_roms() Starting ...')
    # >> Kodi sorting methods
    xbmcplugin.addSortMethod(handle = g_addon_handle, sortMethod = xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(handle = g_addon_handle, sortMethod = xbmcplugin.SORT_METHOD_SIZE)
    xbmcplugin.addSortMethod(handle = g_addon_handle, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)
    m_misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)
    m_misc_clear_AEL_Launcher_Content()

    # --- Load virtual launchers in this category ---
    if virtual_categoryID == VCATEGORY_TITLE_ID:
        vcategory_db_filename = g_PATHS.VCAT_TITLE_FILE_PATH
        vcategory_name        = 'Browse by Title'
    elif virtual_categoryID == VCATEGORY_YEARS_ID:
        vcategory_db_filename = g_PATHS.VCAT_YEARS_FILE_PATH
        vcategory_name        = 'Browse by Year'
    elif virtual_categoryID == VCATEGORY_GENRE_ID:
        vcategory_db_filename = g_PATHS.VCAT_GENRE_FILE_PATH
        vcategory_name        = 'Browse by Genre'
    elif virtual_categoryID == VCATEGORY_DEVELOPER_ID:
        vcategory_db_filename = g_PATHS.VCAT_DEVELOPER_FILE_PATH
        vcategory_name        = 'Browse by Developer'
    elif virtual_categoryID == VCATEGORY_NPLAYERS_ID:
        vcategory_db_filename = g_PATHS.VCAT_NPLAYERS_FILE_PATH
        vcategory_name        = 'Browse by Number of Players'
    elif virtual_categoryID == VCATEGORY_ESRB_ID:
        vcategory_db_filename = g_PATHS.VCAT_ESRB_FILE_PATH
        vcategory_name        = 'Browse by ESRB Rating'
    elif virtual_categoryID == VCATEGORY_RATING_ID:
        vcategory_db_filename = g_PATHS.VCAT_RATING_FILE_PATH
        vcategory_name        = 'Browse by User Rating'
    elif virtual_categoryID == VCATEGORY_CATEGORY_ID:
        vcategory_db_filename = g_PATHS.VCAT_CATEGORY_FILE_PATH
        vcategory_name        = 'Browse by Category'
    else:
        log_error('m_command_render_Browse_by_roms() Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
        kodi_dialog_OK('Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
        return

    # --- If the virtual category has no launchers then render nothing ---
    # >> Also, tell the user to update the virtual launcher database
    if not vcategory_db_filename.exists():
        kodi_dialog_OK('{0} database not found. '.format(vcategory_name) +
                       'Update the virtual category database first.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # --- Load Virtual launchers XML file ---
    (VLauncher_timestamp, vcategory_launchers) = fs_load_VCategory_XML(vcategory_db_filename)

    # --- Check timestamps and warn user if database should be regenerated ---
    if VLauncher_timestamp < self.update_timestamp:
        kodi_dialog_OK('Categories/Launchers/ROMs were modified. Virtual category database should be updated!')

    # --- Render virtual launchers rows ---
    for vlauncher_id in vcategory_launchers:
        vlauncher = vcategory_launchers[vlauncher_id]
        vlauncher_name = vlauncher['name'] + '  ({0} ROM/s)'.format(vlauncher['rom_count'])
        listitem = xbmcgui.ListItem(vlauncher_name)
        listitem.setInfo('video', {'title'    : 'Title text',
                                   # 'label'    : 'Label text',
                                   # 'plot'     : 'Plot text',
                                   # 'genre'    : 'Genre text',
                                   # 'year'     : 'Year text',
                                   'overlay'  : 4,
                                   'size'     : vlauncher['rom_count'] })
        listitem.setArt({'icon': 'DefaultFolder.png'})

        # --- Create context menu ---
        commands = []
        commands.append(('Search ROMs in Virtual Launcher', m_misc_url_RunPlugin('SEARCH_LAUNCHER', virtual_categoryID, vlauncher_id)))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', ))
        commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        listitem.addContextMenuItems(commands)

        url_str = m_misc_url('SHOW_VLAUNCHER_ROMS', virtual_categoryID, vlauncher_id)
        xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = True)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

#
# Renders ROMs in a virtual launcher.
#
def m_command_render_vlauncher_roms(virtual_categoryID, virtual_launcherID):
    log_error('_command_render_virtual_launcher_roms() Starting ...')
    # >> Content type and sorting method
    m_misc_set_all_sorting_methods()
    m_misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)

    # --- Load virtual launchers in this category ---
    vlauncher - g_LauncherRepository.find(virtual_launcherID)
    roms = vlauncher.get_roms()

    if not roms:
        kodi_notify('Virtual category ROMs XML empty. Add items to favourites first.')
        return

    # --- Load favourites ---
    # >> Optimisation: Transform the dictionary keys into a set. Sets are the fastest
    #    when checking if an element exists.
    favlauncher = g_LauncherRepository.find(VLAUNCHER_FAVOURITES_ID)
    roms_fav = favlauncher.get_roms()
    roms_fav_set = set(favrom.get_id() for favrom in roms_fav)

    # --- Display Favourites ---
    for key in sorted(roms, key= lambda r : rom.get_name()):
        self._gui_render_rom_row(virtual_categoryID, virtual_launcherID, rom.get_data(), rom.get_id() in roms_fav_set)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

#
# Renders ROMs in a AEL offline Scraper virtual launcher (aka platform)
#
def m_command_render_AEL_scraper_roms(platform):
    log_debug('_command_render_AEL_scraper_roms() platform = "{0}"'.format(platform))
    # >> Content type and sorting method
    m_misc_set_all_sorting_methods()
    m_misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)

    # >> If XML DB not available tell user and leave
    xml_file = platform_AEL_to_Offline_GameDBInfo_XML[platform]
    if not xml_file:
        kodi_notify_warn('{0} database not available yet.'.format(platform))
        # kodi_refresh_container()
        return

    # --- Load offline scraper XML file ---
    loading_ticks_start = time.time()
    xml_path_FN = g_PATHS.ADDON_CODE_DIR.pjoin(xml_file)
    log_debug('xml_path_FN OP {0}'.format(xml_path_FN.getOriginalPath()))
    log_debug('xml_path_FN  P {0}'.format(xml_path_FN.getPath()))
    games = audit_load_OfflineScraper_XML(xml_path_FN.getPath())

    # --- Display offline scraper ROMs ---
    loading_ticks_end = time.time()
    rendering_ticks_start = time.time()
    for key in sorted(games, key= lambda x : games[x]['name']):
        self._gui_render_AEL_scraper_rom_row(platform, games[key])
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
    rendering_ticks_end = time.time()

    # --- DEBUG Data loading/rendering statistics ---
    log_debug('Loading seconds   {0}'.format(loading_ticks_end - loading_ticks_start))
    log_debug('Rendering seconds {0}'.format(rendering_ticks_end - rendering_ticks_start))

#
# Renders ROMs in a LaunchBox offline Scraper virtual launcher (aka platform)
#
def m_command_render_LB_scraper_roms(platform):
    log_debug('_command_render_LB_scraper_roms() platform = "{0}"'.format(platform))
    # >> Content type and sorting method
    m_misc_set_all_sorting_methods()
    m_misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)

    # >> If XML DB not available tell user and leave
    xml_file = platform_AEL_to_LB_XML[platform]
    if not xml_file:
        kodi_notify_warn('{0} database not available yet.'.format(platform))
        # kodi_refresh_container()
        return

    # --- Load offline scraper XML file ---
    loading_ticks_start = time.time()
    xml_path_FN = g_PATHS.ADDON_CODE_DIR.pjoin(xml_file)
    log_debug('xml_path_FN OP {0}'.format(xml_path_FN.getOriginalPath()))
    log_debug('xml_path_FN  P {0}'.format(xml_path_FN.getPath()))
    games = audit_load_OfflineScraper_XML(xml_path_FN.getPath())

    # --- Display offline scraper ROMs ---
    loading_ticks_end = time.time()
    rendering_ticks_start = time.time()
    for key in sorted(games, key= lambda x : games[x]['name']):
        self._gui_render_LB_scraper_rom_row(platform, games[key])
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
    rendering_ticks_end = time.time()

    # --- DEBUG Data loading/rendering statistics ---
    log_debug('Loading seconds   {0}'.format(loading_ticks_end - loading_ticks_start))
    log_debug('Rendering seconds {0}'.format(rendering_ticks_end - rendering_ticks_start))

#
# Render the Recently played and Most Played virtual launchers.
#
def m_command_render_recently_played_roms():
    # >> Content type and sorting method
    m_misc_set_default_sorting_method()
    m_misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)

    # --- Load Recently Played favourite ROM list and create and OrderedDict ---
    recent_launcher = g_LauncherRepository.find(VLAUNCHER_RECENT_ID)
    recent_roms = recent_launcher.get_roms()
    
    if not recent_roms or len(recent_roms) == 0:
        kodi_notify('Recently played list is empty. Play some ROMs first!')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # --- Display recently player ROM list ---
    for rom in recent_roms:
        self._gui_render_rom_row(VCATEGORY_RECENT_ID, VLAUNCHER_RECENT_ID, rom.get_data())
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def m_command_render_most_played_roms():
    # >> Content type and sorting method
    m_misc_set_default_sorting_method()
    m_misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)

    # --- Load Most Played favourite ROMs ---
    most_played_launcher = g_LauncherRepository.find(VLAUNCHER_MOST_PLAYED_ID)
    roms = most_played_launcher.get_roms()

    if not roms or len(roms) == 0:
        kodi_notify('Most played ROMs list  is empty. Play some ROMs first!.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # --- Display most played ROMs, order by number of launchs ---
    for rom in sorted(roms, key = lambda rom : rom.get_launch_count(), reverse = True):
        self._gui_render_rom_row(VCATEGORY_MOST_PLAYED_ID, VLAUNCHER_MOST_PLAYED_ID, rom.get_data())

    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

#
# Renders all ROMs in all launchers.
# This command is called by skins. Not advisable to use it if there are many ROMs...
#
def m_command_render_all_roms():
    # --- Make a dictionary having all ROMs in all Launchers ---
    log_debug('_command_render_all_ROMs() Creating list of all ROMs in all Launchers')
    all_roms = {}

    launchers = g_LauncherRepository.find_all()
    for launcher in launchers:

        # If launcher is standalone skip
        if not launcher.supports_launching_roms(): 
            continue

        roms = launcher.get_roms()
        temp_roms = {}
        for rom in roms:
            temp_rom                = rom.copy_of_data()
            temp_rom['launcher_id'] = launcher.get_id()
            temp_rom['category_id'] = launcher.get_category_id()
            temp_roms[rom.get_id()] = temp_rom

        all_roms.update(temp_roms)

    # --- Load favourites ---
    fav_launcher = g_LauncherRepository.find(VLAUNCHER_FAVOURITES_ID)
    roms_fav = fav_launcher.get_roms()
    roms_fav_set = set(rom_fav.get_id() for rom_fav in roms_fav)

    # --- Set content type and sorting methods ---
    m_misc_set_default_sorting_method()

    # --- Render ROMs ---
    for rom_id in sorted(all_roms, key = lambda x : all_roms[x]['m_name']):
        self._gui_render_rom_row(all_roms[rom_id]['category_id'], all_roms[rom_id]['launcher_id'],
                                 all_roms[rom_id], rom_id in roms_fav_set)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

#
# Check ROMs in favourites and set fav_status field.
# roms_fav edited by passing by assigment, dictionaries are mutable.
# 
def m_fav_check_favourites(roms_fav):
    # --- Statistics ---
    self.num_fav_roms = len(roms_fav)
    self.num_fav_ulauncher = 0
    self.num_fav_urom      = 0
    self.num_fav_broken    = 0

    # --- Reset fav_status filed for all favourites ---
    log_debug('_fav_check_favourites() STEP 0: Reset status')
    for rom_fav in roms_fav:
        rom_fav.set_custom_attribute('fav_status', 'OK')

    # --- Progress dialog ---
    # >> Important to avoid multithread execution of the plugin and race conditions
    pDialog = xbmcgui.DialogProgress()
    
    all_launcher_ids = g_LauncherRepository.find_all_ids()

    # STEP 1: Find Favourites with missing launchers
    log_debug('_fav_check_favourites() STEP 1: Search unlinked Launchers')
    num_progress_items = len(roms_fav)
    i = 0
    pDialog.create('Advanced Emulator Launcher', 'Checking Favourite ROMs. Step 1 of 3 ...')
    for rom_fav_ID in roms_fav:
        pDialog.update(i * 100 / num_progress_items)
        i += 1
        if roms_fav[rom_fav_ID]['launcherID'] not in all_launcher_ids:
            log_verb('Fav ROM "{0}" Unlinked Launcher because launcherID not in launchers'.format(roms_fav[rom_fav_ID]['m_name']))
            roms_fav[rom_fav_ID]['fav_status'] = 'Unlinked Launcher'
            self.num_fav_ulauncher += 1
    pDialog.update(i * 100 / num_progress_items)
    pDialog.close()

    # STEP 2: Find missing ROM ID
    # >> Get a list of launchers Favourite ROMs belong
    log_debug('_fav_check_favourites() STEP 2: Search unlinked ROMs')
    launchers_fav = set()
    for rom_fav_ID in roms_fav: launchers_fav.add(roms_fav[rom_fav_ID]['launcherID'])

    # >> Traverse list of launchers. For each launcher, load ROMs it and check all favourite ROMs
    # >> that belong to that launcher.
    num_progress_items = len(launchers_fav)
    i = 0
    pDialog.create('Advanced Emulator Launcher', 'Checking Favourite ROMs. Step 2 of 3...')
    for launcher_id in launchers_fav:
        pDialog.update(i * 100 / num_progress_items)
        i += 1

        # >> If Favourite does not have launcher skip it. It has been marked as 'Unlinked Launcher'
        # >> in step 1.
        if launcher_id not in all_launcher_ids:
           continue

        # >> Load launcher ROMs
        launcher = g_LauncherRepository.find(launcher_id)
        roms = fs_load_ROMs_JSON(ROMS_DIR, launcher.get_data())

        # Traverse all favourites and check them if belong to this launcher.
        # This should be efficient because traversing favourites is cheap but loading ROMs is expensive.
        for rom_fav_ID in roms_fav:
            if roms_fav[rom_fav_ID]['launcherID'] == launcher_id:
                # Check if ROM ID exists
                if roms_fav[rom_fav_ID]['id'] not in roms:
                    log_verb('Fav ROM "{0}" Unlinked ROM because romID not in launcher ROMs'.format(roms_fav[rom_fav_ID]['m_name']))
                    roms_fav[rom_fav_ID]['fav_status'] = 'Unlinked ROM'
                    self.num_fav_urom += 1
    pDialog.update(i * 100 / num_progress_items)
    pDialog.close()

    # STEP 3: Check if file exists. Even if the ROM ID is not there because user
    # deleted ROM or launcher, the file may still be there.
    log_debug('_fav_check_favourites() STEP 3: Search broken ROMs')
    num_progress_items = len(launchers_fav)
    i = 0
    pDialog.create('Advanced Emulator Launcher', 'Checking Favourite ROMs. Step 3 of 3 ...')
    for rom_fav_ID in roms_fav:
        pDialog.update(i * 100 / num_progress_items)
        i += 1
        romFile = FileNameFactory.create(roms_fav[rom_fav_ID]['filename'])
        if not romFile.exists():
            log_verb('Fav ROM "{0}" broken because filename does not exist'.format(roms_fav[rom_fav_ID]['m_name']))
            roms_fav[rom_fav_ID]['fav_status'] = 'Broken'
            self.num_fav_broken += 1
    pDialog.update(i * 100 / num_progress_items)
    pDialog.close()

#
# Renders a listview with all Collections.
# Each Collection is similar to a launcher.
#
def m_command_render_Collections():
    # >> Kodi sorting method
    xbmcplugin.addSortMethod(handle = g_addon_handle, sortMethod = xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(handle = g_addon_handle, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)
    m_misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)

    # --- Load collection index ---
    (collections, update_timestamp) = fs_load_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH)

    # --- If the virtual category has no launchers then render nothing ---
    if not collections:
        kodi_notify('No collections in database. Add a collection first.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # --- Render ROM Collections as Categories ---
    for collection_id in collections:
        # --- Create listitem ---
        collection = collections[collection_id]
        collection_name = collection['m_name']
        listitem = xbmcgui.ListItem(collection_name)
        listitem.setInfo('video', {'title'   : collection['m_name'],    'genre'   : collection['m_genre'],
                                   'plot'    : collection['m_plot'],    'rating'  : collection['m_rating'],
                                   'trailer' : collection['s_trailer'], 'overlay' : 4 })
        icon_path      = asset_get_default_asset_Category(collection, 'default_icon', 'DefaultFolder.png')
        fanart_path    = asset_get_default_asset_Category(collection, 'default_fanart')
        banner_path    = asset_get_default_asset_Category(collection, 'default_banner')
        poster_path    = asset_get_default_asset_Category(collection, 'default_poster')
        clearlogo_path = asset_get_default_asset_Category(collection, 'default_clearlogo')
        listitem.setArt({'icon'   : icon_path,   'fanart' : fanart_path,
                         'banner' : banner_path, 'poster' : poster_path, 'clearlogo' : clearlogo_path})

        # --- Extrafanart ---
        # NOTE This bunch of code is a complete workaround and slow.
        collections_asset_dir = FileName(g_settings['collections_asset_dir'], isdir = True)
        extrafanart_dir = collections_asset_dir.pjoin(collection['m_name'], isdir = True)
        log_debug('m_command_render_Collections() COL dir {0}'.format(collections_asset_dir.getPath()))
        log_debug('m_command_render_Collections() EF  dir {0}'.format(extrafanart_dir.getPath()))
        extrafanart_dic = {}
        for i in range(25):
            # --- PNG ---
            extrafanart_file = extrafanart_dir + 'fanart{0}.png'.format(i)
            log_debug('m_command_render_Collections() test    {0}'.format(extrafanart_file.getPath()))
            if extrafanart_file.exists():
                log_debug('m_command_render_Collections() Adding extrafanart #{0}'.format(i))
                extrafanart_dic['extrafanart{0}'.format(i)] = extrafanart_file.getOriginalPath()
                continue
            # --- JPG ---
            extrafanart_file = extrafanart_dir + 'fanart{0}.jpg'.format(i)
            log_debug('m_command_render_Collections() test    {0}'.format(extrafanart_file.getPath()))
            if extrafanart_file.exists():
                log_debug('m_command_render_Collections() Adding extrafanart #{0}'.format(i))
                extrafanart_dic['extrafanart{0}'.format(i)] = extrafanart_file.getOriginalPath()
                continue
            # >> No extrafanart found, exit loop.
            break
        if extrafanart_dic:
            log_debug('m_command_render_Collections() Extrafanart setArt() "{0}"'.format(unicode(extrafanart_dic)))
            listitem.setArt(extrafanart_dic)

        # --- Create context menu ---
        commands = []
        commands.append(('View Collection data', m_misc_url_RunPlugin('VIEW', VCATEGORY_COLLECTIONS_ID, collection_id)))
        commands.append(('Edit/Export Collection',   m_misc_url_RunPlugin('EDIT_COLLECTION', VCATEGORY_COLLECTIONS_ID, collection_id)))
        commands.append(('Create New Collection',    m_misc_url_RunPlugin('ADD_COLLECTION')))
        commands.append(('Import Collection',        m_misc_url_RunPlugin('IMPORT_COLLECTION')))
        commands.append(('Kodi File Manager',        'ActivateWindow(filemanager)'))
        commands.append(('AEL addon settings',       'Addon.OpenSettings({0})'.format(__addon_id__)))
        listitem.addContextMenuItems(commands)

        # >> Use ROMs renderer to display collection ROMs
        url_str = m_misc_url('SHOW_COLLECTION_ROMS', VCATEGORY_COLLECTIONS_ID, collection_id)
        xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = url_str, listitem = listitem, isFolder = True)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def m_command_render_Collection_roms(categoryID, launcherID):
    m_misc_set_default_sorting_method()
    m_misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)

    # --- Load Collection index and ROMs ---
    (collections, update_timestamp) = fs_load_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH)
    collection = collections[launcherID]
    roms_json_file = g_PATHS.COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
    collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
    if not collection_rom_list:
        kodi_notify('Collection is empty. Add ROMs to this collection first.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # --- Display Collection ROMs ---
    for rom in collection_rom_list:
        self._gui_render_rom_row(categoryID, launcherID, rom)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

#
# Deletes a collection and associated ROMs.
#
def m_command_delete_collection(categoryID, launcherID):
    # --- Load collection index and ROMs ---
    collection = self.collection_repository.findef(launcherID)
    collection_rom_list = collection.get_roms()

    # --- Confirm deletion ---
    num_roms = len(collection_rom_list)
    collection_name = collection.get_name()
    ret = kodi_dialog_yesno('Collection "{0}" has {1} ROMs. '.format(collection_name, num_roms) +
                            'Are you sure you want to delete it?')
    if not ret: return

    # --- Remove JSON file and delete collection object ---
    collection.clear_roms()
    self.collection_repository.delete(collection)

    kodi_refresh_container()
    kodi_notify('Deleted ROM Collection "{0}"'.format(collection_name))

#
# Imports a ROM Collection.
#
def m_command_import_collection():
    # --- Choose collection to import ---
    dialog = xbmcgui.Dialog()
    collection_file_str = dialog.browse(1, 'Select the ROM Collection file', 'files', '.json', False, False).decode('utf-8')
    if not collection_file_str: return

    # --- Load ROM Collection file ---
    collection_FN = FileNameFactory.create(collection_file_str)
    control_dic, collection_dic, collection_rom_list = fs_import_ROM_collection(collection_FN)
    if not collection_dic:
        kodi_dialog_OK('Error reading Collection JSON file. JSON file corrupted or wrong.')
        return
    if not collection_rom_list:
        kodi_dialog_OK('Collection is empty.')
        return
    if control_dic['control'] != 'Advanced Emulator Launcher Collection ROMs':
        kodi_dialog_OK('JSON file is not an AEL ROM Collection file.')
        return

    # --- Check if asset JSON exist. If so, ask the user about importing it. ---
    collection_asset_FN = FileNameFactory.create(collection_FN.getPath_noext() + '_assets.json')
    log_debug('_command_import_collection() collection_asset_FN "{0}"'.format(collection_asset_FN.getPath()))
    import_collection_assets = False
    if collection_asset_FN.exists():
        log_debug('_command_import_collection() Collection asset JSON found')
        ret = kodi_dialog_yesno('Collection asset JSON found. Import collection assets as well?')
        if ret: 
            import_collection_assets = True
            asset_control_dic, assets_dic = fs_import_ROM_collection_assets(collection_asset_FN)
    else:
        log_debug('_command_import_collection() Collection asset JSON NOT found')

    # --- Load collection indices ---
    collections, update_timestamp = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)

    # --- If collectionID already on index warn the user ---
    if collection_dic['id'] in collections:
        log_info('_command_import_collection() Collection {0} already in AEL'.format(collection_dic['m_name']))
        ret = kodi_dialog_yesno('A Collection with same ID exists. Overwrite?')
        if not ret: return

    # --- Regenrate roms_base_noext field ---
    collection_base_name = fs_get_collection_ROMs_basename(collection_dic['m_name'], collection_dic['id'])
    collection_dic['roms_base_noext'] = collection_base_name
    log_debug('_command_import_collection() roms_base_noext "{0}"'.format(collection_dic['roms_base_noext']))

    # --- Also import assets if loaded ---
    if import_collection_assets:
        collections_asset_dir_FN = FileNameFactory.create(g_settings['collections_asset_dir'])

        # --- Import Collection assets ---
        log_info('_command_import_collection() Importing ROM Collection assets ...')
        for asset_kind in CATEGORY_ASSET_LIST:
            # >> Get asset filename with no extension
            AInfo = assets_get_info_scheme(asset_kind)
            asset_noext_FN = assets_get_path_noext_SUFIX(AInfo, collections_asset_dir_FN,
                                                         collection_dic['m_name'], collection_dic['id'])
            log_debug('{0:<9s} base_noext "{1}"'.format(AInfo.name, asset_noext_FN.getBase()))
            if asset_noext_FN.getBase() not in assets_dic:
                # >> Asset not found. Make sure asset is unset in imported Collection.
                collection_dic[AInfo.key] = ''
                log_debug('{0:<9s} NOT found in imported asset dictionary'.format(AInfo.name))
                continue
            log_debug('{0:<9s} found in imported asset dictionary'.format(AInfo.name))
            asset_dic = assets_dic[asset_noext_FN.getBase()]
            new_asset_FN = collections_asset_dir_FN.pjoin(asset_dic['basename'])

            # >> Create asset file
            asset_base64_data = asset_dic['data']
            asset_filesize    = asset_dic['filesize']
            fileData = base64.b64decode(asset_base64_data)
            log_debug('{0:<9s} Creating OP "{1}"'.format(AInfo.name, new_asset_FN.getOriginalPath()))
            log_debug('{0:<9s} Creating P  "{1}"'.format(AInfo.name, new_asset_FN.getPath()))

            new_asset_FN.writeAll(fileData, 'wb') # b is important -> binary
            statinfo = new_asset_FN.stat()
            file_size = statinfo.st_size
            if asset_filesize != file_size:
                # >> File creation/Unpacking error. Make sure asset is unset in imported Collection.
                collection_dic[AInfo.key] = ''
                log_error('{0:<9s} wrong file size {1} (must be {2})'.format(A.name, file_size, asset_filesize))
                return
            else:
                log_debug('{0:<9s} file size OK ({1} bytes)'.format(AInfo.name, asset_filesize))
            # >> Update imported asset filename in database.
            log_debug('{0:<9s} collection[{1}] linked to "{2}"'.format(AInfo.name, AInfo.key, new_asset_FN.getOriginalPath()))
            collection_dic[AInfo.key] = new_asset_FN.getOriginalPath()

        # --- Import ROM assets ---
        log_info('_command_import_collection() Importing ROM assets ...')
        for rom_item in collection_rom_list:
            log_debug('_command_import_collection() ROM "{0}"'.format(rom_item['m_name']))
            for asset_kind in ROM_ASSET_LIST:
                # >> Get assets filename with no extension
                AInfo = assets_get_info_scheme(asset_kind)
                ROM_FN = FileNameFactory.create(rom_item['filename'])                    
                ROM_asset_noext_FN = assets_get_path_noext_SUFIX(AInfo, collections_asset_dir_FN, 
                                                                 ROM_FN.getBase_noext(), rom_item['id'])
                ROM_asset_FN = ROM_asset_noext_FN.append(ROM_asset_noext_FN.getExt())
                log_debug('{0:<9s} base_noext "{1}"'.format(AInfo.name, ROM_asset_FN.getBase_noext()))
                if ROM_asset_FN.getBase_noext() not in assets_dic:
                    # >> Asset not found. Make sure asset is unset in imported Collection.
                    rom_item[AInfo.key] = ''
                    log_debug('{0:<9s} NOT found in imported asset dictionary'.format(AInfo.name))
                    continue
                log_debug('{0:<9s} found in imported asset dictionary'.format(AInfo.name))
                asset_dic = assets_dic[ROM_asset_FN.getBase_noext()]                        
                new_asset_FN = collections_asset_dir_FN.pjoin(asset_dic['basename'])

                # >> Create asset file
                asset_base64_data = asset_dic['data']
                asset_filesize    = asset_dic['filesize']
                fileData = base64.b64decode(asset_base64_data)
                log_debug('{0:<9s} Creating OP "{1}"'.format(AInfo.name, new_asset_FN.getOriginalPath()))
                log_debug('{0:<9s} Creating P  "{1}"'.format(AInfo.name, new_asset_FN.getPath()))
                new_asset_FN.writeAll(fileData, 'wb')
                statinfo = new_asset_FN.stat()
                file_size = statinfo.st_size
                if asset_filesize != file_size:
                    # >> File creation/Unpacking error. Make sure asset is unset in imported Collection.
                    rom_item[AInfo.key] = ''
                    log_error('{0:<9s} wrong file size {1} (must be {2})'.format(AInfo.name, file_size, asset_filesize))
                    return
                else:
                    log_debug('{0:<9s} file size OK ({1} bytes)'.format(AInfo.name, asset_filesize))
                # >> Update asset info in database
                log_debug('{0:<9s} rom_item[{1}] linked to "{2}"'.format(AInfo.name, AInfo.key, new_asset_FN.getOriginalPath()))
                rom_item[AInfo.key] = new_asset_FN.getOriginalPath()
        log_debug('_command_import_collection() Finished importing assets')

    # --- Add imported collection to database ---
    collections[collection_dic['id']] = collection_dic
    log_info('_command_import_collection() Imported Collection "{0}" (id {1})'.format(collection_dic['m_name'], collection_dic['id']))

    # --- Write ROM Collection databases ---
    fs_write_Collection_index_XML(COLLECTIONS_FILE_PATH, collections)
    fs_write_Collection_ROMs_JSON(COLLECTIONS_DIR.pjoin(collection_base_name + '.json'), collection_rom_list)
    if import_collection_assets:
        kodi_dialog_OK("Imported ROM Collection '{0}' metadata and assets.".format(collection_dic['m_name']))
    else:
        kodi_dialog_OK("Imported ROM Collection '{0}' metadata.".format(collection_dic['m_name']))

#
# Exports a ROM Collection
#
def m_command_export_collection(categoryID, launcherID):
    # --- Export database only or database + assets ---
    dialog = xbmcgui.Dialog()
    export_type = dialog.select('Export ROM Collection',
                               ['Export only metadata', 'Export metadata and assets'])
    if export_type < 0: return

    # --- Choose output directory ---
    dialog = xbmcgui.Dialog()
    output_dir = dialog.browse(3, 'Select Collection output directory', 'files').decode('utf-8')
    if not output_dir: return
    output_dir_FileName = FileNameFactory.create(output_dir)

    # --- Load collection ROMs ---
    (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
    collection = collections[launcherID]
    roms_json_file = COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
    collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
    if not collection_rom_list:
        kodi_notify('Collection is empty. Add ROMs to this collection first.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # --- If exporting assets, copy assets from parent into Collection assets directory ---
    # 1) Traverse all collection ROMs.
    # 2) For each ROM, traverse all assets. If assets is in parent ROM directory then copy
    #    to ROM Collections directory.
    # 3) For every asset copied update ROM Collection database.
    if export_type == 1:
        ret = kodi_dialog_yesno('Exporting ROM Collection assets. '
                                'Parent ROM assets will be copied into the ROM Collection '
                                'asset directory before exporting.')
        if not ret:
            kodi_dialog_OK('ROM Collection export cancelled.')
            return

        # --- Copy Collection assets to Collection asset directory ---
        log_info('_command_export_collection() Copying ROM Collection assets ...')
        collections_asset_dir_FN = FileNameFactory.create(g_settings['collections_asset_dir'])
        collection_assets_were_copied = False
        for asset_kind in CATEGORY_ASSET_LIST:
            AInfo = assets_get_info_scheme(asset_kind)
            asset_FileName = FileNameFactory.create(collection[AInfo.key])
            new_asset_noext_FileName = assets_get_path_noext_SUFIX(AInfo, collections_asset_dir_FN,
                                                                   collection['m_name'], collection['id'])
            new_asset_FileName = new_asset_noext_FileName.append(asset_FileName.getExt())
            if not collection[AInfo.key]:
                log_debug('{0:<9s} not set.'.format(AInfo.name))
                continue
            elif asset_FileName.getPath() == new_asset_FileName.getPath():
                log_debug('{0:<9s} in Collection asset dir'.format(AInfo.name))
                continue
            # >> If asset cannot be found then ignore it. Do not touch JSON database.
            elif not asset_FileName.exists():
                log_debug('{0:<9s} not found "{1}"'.format(AInfo.name, asset_FileName.getOriginalPath()))
                log_debug('{0:<9s} ignored'.format(AInfo.name))
                continue
            else:
                log_debug('{0:<9s} in external dir'.format(AInfo.name))
                log_debug('{0:<9s} OP COPY "{1}"'.format(AInfo.name, asset_FileName.getOriginalPath()))
                log_debug('{0:<9s} OP   TO "{1}"'.format(AInfo.name, new_asset_FileName.getOriginalPath()))
                log_debug('{0:<9s} P  COPY "{1}"'.format(AInfo.name, asset_FileName.getPath()))
                log_debug('{0:<9s} P    TO "{1}"'.format(AInfo.name, new_asset_FileName.getPath()))
                try:
                    source_path = asset_FileName.getPath().decode(get_fs_encoding(), 'ignore')
                    dest_path   = new_asset_FileName.getPath().decode(get_fs_encoding(), 'ignore')
                    log_debug('source_path "{0}"'.format(source_path))
                    log_debug('dest_path   "{0}"'.format(dest_path))
                    shutil.copy(source_path, dest_path)
                except OSError:
                    log_error('_command_export_collection() OSError exception copying image')
                    kodi_notify_warn('OSError exception copying image')
                    return
                except IOError:
                    log_error('_command_export_collection() IOError exception copying image')
                    kodi_notify_warn('IOError exception copying image')
                    return

                # >> Asset were copied. Update ROM Collection database.
                collection[AInfo.key] = new_asset_FileName.getOriginalPath()
                collection_assets_were_copied = True

        # --- Copy Collection ROM assets ---
        log_info('_command_export_collection() Copying parent ROM assets into ROM Collections asset directory ...')
        ROM_assets_were_copied = False
        for rom_item in collection_rom_list:
            log_debug('_command_export_collection() ROM "{0}"'.format(rom_item['m_name']))
            for asset_kind in ROM_ASSET_LIST:
                AInfo = assets_get_info_scheme(asset_kind)
                asset_FileName = FileNameFactory.create(rom_item[AInfo.key])
                ROM_FileName = FileNameFactory.create(rom_item['filename'])
                new_asset_noext_FileName = assets_get_path_noext_SUFIX(AInfo, collections_asset_dir_FN, 
                                                                       ROM_FileName.getBase_noext(), rom_item['id'])
                new_asset_FileName = new_asset_noext_FileName.append(asset_FileName.getExt())
                if not rom_item[AInfo.key]:
                    log_debug('{0:<9s} not set.'.format(AInfo.name))
                    continue
                elif asset_FileName.getPath() == new_asset_FileName.getPath():
                    log_debug('{0:<9s} in Collection asset dir'.format(AInfo.name))
                    continue
                # >> If asset cannot be found then ignore it. Do not touch JSON database.
                elif not asset_FileName.exists():
                    log_debug('{0:<9s} not found "{1}"'.format(AInfo.name, asset_FileName.getOriginalPath()))
                    log_debug('{0:<9s} ignored'.format(AInfo.name))
                    continue
                else:
                    # >> Copy asset from parent into ROM Collection asset dir
                    log_debug('{0:<9s} in external dir'.format(AInfo.name))
                    log_debug('{0:<9s} OP COPY "{1}"'.format(AInfo.name, asset_FileName.getOriginalPath()))
                    log_debug('{0:<9s} OP   TO "{1}"'.format(AInfo.name, new_asset_FileName.getOriginalPath()))
                    log_debug('{0:<9s} P  COPY "{1}"'.format(AInfo.name, asset_FileName.getPath()))
                    log_debug('{0:<9s} P    TO "{1}"'.format(AInfo.name, new_asset_FileName.getPath()))
                    try:
                        source_path = asset_FileName.getPath().decode(get_fs_encoding(), 'ignore')
                        dest_path   = new_asset_FileName.getPath().decode(get_fs_encoding(), 'ignore')
                        shutil.copy(source_path, dest_path)
                    except OSError:
                        log_error('_command_export_collection() OSError exception copying image')
                        kodi_notify_warn('OSError exception copying image')
                        return
                    except IOError:
                        log_error('_command_export_collection() IOError exception copying image')
                        kodi_notify_warn('IOError exception copying image')
                        return

                    # >> Asset were copied. Update ROM Collection database.
                    rom_item[AInfo.key] = new_asset_FileName.getOriginalPath()
                    ROM_assets_were_copied = True

        # >> Write ROM Collection DB.
        if collection_assets_were_copied:
            fs_write_Collection_index_XML(COLLECTIONS_FILE_PATH, collections)
            log_info('_command_export_collection() Collection assets were copied. Saving Collection index ...')
        if ROM_assets_were_copied:
            json_file = COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
            fs_write_Collection_ROMs_JSON(json_file, collection_rom_list)
            log_info('_command_export_collection() Collection ROM assets were copied. Saving Collection database ...')

    # --- Export collection metadata (Always) ---
    output_FileName = output_dir_FileName.pjoin(collection['m_name'] + '.json')
    fs_export_ROM_collection(output_FileName, collection, collection_rom_list)

    # --- Export collection assets (Optional) ---
    if export_type == 1:
        output_FileName = output_dir_FileName.pjoin(collection['m_name'] + '_assets.json')
        fs_export_ROM_collection_assets(output_FileName, collection, collection_rom_list, collections_asset_dir_FN)

    # >> User info
    if   export_type == 0:
        kodi_notify('Exported ROM Collection {0} metadata.'.format(collection['m_name']))
    elif export_type == 1:
        kodi_notify('Exported ROM Collection {0} metadata and assets.'.format(collection['m_name']))

#
# Search ROMs in launcher
#
def m_command_search_launcher(categoryID, launcherID):
    log_debug('_command_search_launcher() categoryID {0}'.format(categoryID))
    log_debug('_command_search_launcher() launcherID {0}'.format(launcherID))
    
    launcher = g_LauncherRepository.find(launcherID)
    
    # --- Load ROMs ---
    roms = launcher.get_roms()
    
    # --- Empty ROM dictionary / Loading error ---
    if not roms:
        kodi_notify('Launcher JSON is empty. Add ROMs to Launcher')
        return

    # --- Ask user what field category to search ---
    dialog = xbmcgui.Dialog()
    type = dialog.select('Search ROMs ...', ['By ROM Title', 'By Release Year', 'By Genre', 'By Studio', 'By Rating'])
    if type < 0: return

    # --- Search by ROM Title ---
    type_nb = 0
    if type == type_nb:
        keyboard = xbmc.Keyboard('', 'Enter the ROM Title search string ...')
        keyboard.doModal()
        if not keyboard.isConfirmed(): return
        search_string = keyboard.getText().decode('utf-8')
        url = m_misc_url_search('EXECUTE_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_TITLE', search_string)

    # --- Search by Release Date ---
    type_nb = type_nb + 1
    if type == type_nb:
        searched_list = self._search_launcher_field('m_year', roms)
        dialog = xbmcgui.Dialog()
        selected_value = dialog.select('Select a release year ...', searched_list)
        if selected_value < 0: return
        search_string = searched_list[selected_value]
        url = m_misc_url_search('EXECUTE_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_YEAR', search_string)

    # --- Search by System Platform ---
    # >> Note that search by platform does not make sense when searching a launcher because all items have
    # >> the same platform! It only makes sense for global searches... which AEL does not.
    # >> I keep this AL old code for reference, though.
    # type_nb = type_nb + 1
    # if type == type_nb:
    #     search = []
    #     search = _search_category(self, "platform")
    #     dialog = xbmcgui.Dialog()
    #     selected = dialog.select('Select a Platform...', search)
    #     if not selected == -1:
    #         xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s/%s)" % (self.base_url, search[selected], SEARCH_PLATFORM_COMMAND))

    # --- Search by Genre ---
    type_nb = type_nb + 1
    if type == type_nb:
        searched_list = self._search_launcher_field('m_genre', roms)
        dialog = xbmcgui.Dialog()
        selected_value = dialog.select('Select a Genre ...', searched_list)
        if selected_value < 0: return
        search_string = searched_list[selected_value]
        url = m_misc_url_search('EXECUTE_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_GENRE', search_string)

    # --- Search by Studio ---
    type_nb = type_nb + 1
    if type == type_nb:
        searched_list = self._search_launcher_field('m_developer', roms)
        dialog = xbmcgui.Dialog()
        selected_value = dialog.select('Select a Studio ...', searched_list)
        if selected_value < 0: return
        search_string = searched_list[selected_value]
        url = m_misc_url_search('EXECUTE_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_STUDIO', search_string)

    # --- Search by Rating ---
    type_nb = type_nb + 1
    if type == type_nb:
        searched_list = self._search_launcher_field('m_rating', roms)
        dialog = xbmcgui.Dialog()
        selected_value = dialog.select('Select a Rating ...', searched_list)
        if selected_value < 0: return
        search_string = searched_list[selected_value]
        url = m_misc_url_search('EXECUTE_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_RATING', search_string)

    # --- Replace current window by search window ---
    # When user press Back in search window it returns to the original window (either showing
    # launcher in a cateogory or displaying ROMs in a launcher/virtual launcher).
    #
    # NOTE ActivateWindow() / RunPlugin() / RunAddon() seem not to work here
    log_debug('_command_search_launcher() Container.Update URL {0}'.format(url))
    xbmc.executebuiltin(u'Container.Update({0})'.format(url).encode('utf-8'))

#
# Auxiliar function used in Launcher searches.
#
def m_search_launcher_field(search_dic_field, roms):
    # Maybe this can be optimized a bit to make the search faster...
    search = []
    for rom in roms:
        rom_data = rom.get_data()
        if rom_data[search_dic_field] == '':
            search.append('[ Not Set ]')
        else:
            search.append(rom_data[search_dic_field])
    # Search may have a lot of repeated entries. Converting them to a set makes them unique.
    search = list(set(search))
    search.sort()

    return search

def m_command_execute_search_launcher(categoryID, launcherID, search_type, search_string):
    if   search_type == 'SEARCH_TITLE'  : rom_search_field = 'm_name'
    elif search_type == 'SEARCH_YEAR'   : rom_search_field = 'm_year'
    elif search_type == 'SEARCH_STUDIO' : rom_search_field = 'm_studio'
    elif search_type == 'SEARCH_GENRE'  : rom_search_field = 'm_genre'
    elif search_type == 'SEARCH_RATING' : rom_search_field = 'm_rating'
    else: return

    launcher = g_LauncherRepository.find(launcherID)

    # --- Load Launcher ROMs ---
    roms = launcher.get_roms()

    # --- Empty ROM dictionary / Loading error ---
    if not roms:
        kodi_notify('Launcher JSON is empty. Add ROMs to Launcher')
        return

    # --- Go through rom list and search for user input ---
    rl = {}
    notset = ('[ Not Set ]')
    text = search_string.lower()
    empty = notset.lower()
    for rom in roms:
        rom_data = rom.get_data()
        rom_field_str = rom_data[rom_search_field].lower()
        if rom_field_str == '' and text == empty: rl[rom.get_id()] = rom

        if rom_search_field == 'm_name':
            if not rom_field_str.find(text) == -1:
                rl[rom.get_id()] = rom
        else:
            if rom_field_str == text:
                rl[rom.get_id()] = rom

    # --- Render ROMs ---
    m_misc_set_all_sorting_methods()
    if not rl:
        kodi_dialog_OK('Search returned no results')
    for key in sorted(rl.iterkeys()):
        self._gui_render_rom_row(categoryID, launcherID, rl[key].get_data())
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

#
# View all kinds of information
#
def m_command_view_menu(categoryID, launcherID, romID):
    VIEW_CATEGORY          = 100
    VIEW_LAUNCHER          = 200
    VIEW_COLLECTION        = 300
    VIEW_ROM_LAUNCHER      = 400
    VIEW_ROM_VLAUNCHER     = 500
    VIEW_ROM_COLLECTION    = 500

    ACTION_VIEW_CATEGORY          = 100
    ACTION_VIEW_LAUNCHER          = 200
    ACTION_VIEW_COLLECTION        = 300
    ACTION_VIEW_ROM               = 400
    ACTION_VIEW_LAUNCHER_STATS    = 500
    ACTION_VIEW_LAUNCHER_METADATA = 600
    ACTION_VIEW_LAUNCHER_ASSETS   = 700
    ACTION_VIEW_LAUNCHER_SCANNER  = 800
    ACTION_VIEW_MANUAL            = 900
    ACTION_VIEW_MAP               = 1000
    ACTION_VIEW_EXEC_OUTPUT       = 1100

    # --- Determine if we are in a category, launcher or ROM ---
    log_debug('_command_view_menu() categoryID = {0}'.format(categoryID))
    log_debug('_command_view_menu() launcherID = {0}'.format(launcherID))
    log_debug('_command_view_menu() romID      = {0}'.format(romID))
    if launcherID and romID:
        if categoryID == VCATEGORY_FAVOURITES_ID or \
           categoryID == VCATEGORY_RECENT_ID or \
           categoryID == VCATEGORY_MOST_PLAYED_ID or \
           categoryID == VCATEGORY_TITLE_ID    or categoryID == VCATEGORY_YEARS_ID or \
           categoryID == VCATEGORY_GENRE_ID    or categoryID == VCATEGORY_DEVELOPER_ID or \
           categoryID == VCATEGORY_NPLAYERS_ID or categoryID == VCATEGORY_ESRB_ID or \
           categoryID == VCATEGORY_RATING_ID   or categoryID == VCATEGORY_CATEGORY_ID:
            view_type = VIEW_ROM_VLAUNCHER
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            view_type = VIEW_ROM_COLLECTION
        else:
            view_type = VIEW_ROM_LAUNCHER
    elif launcherID and not romID:
        if categoryID == VCATEGORY_COLLECTIONS_ID:
            view_type = VIEW_COLLECTION
        else:
            view_type = VIEW_LAUNCHER
    else:
        view_type = VIEW_CATEGORY
    log_debug('_command_view_menu() view_type = {0}'.format(view_type))

    # --- Build menu base on view_type ---
    if g_PATHS.LAUNCH_LOG_FILE_PATH.exists():
        stat_stdout = g_PATHS.LAUNCH_LOG_FILE_PATH.stat()
        size_stdout = stat_stdout.st_size()
        STD_status = '{0} bytes'.format(size_stdout)
    else:
        STD_status = 'not found'

    if view_type == VIEW_LAUNCHER:
        Report_status = 'no reporting supported'
   
    if view_type == VIEW_ROM_LAUNCHER:
        
        launcher = g_LauncherRepository.find(launcherID)
        launcher_report_FN = REPORTS_DIR.pjoin(launcher.get_roms_base() + '_report.txt')
        if launcher_report_FN.exists():
            stat_stdout = launcher_report_FN.stat()
            size_stdout = stat_stdout.st_size()
            Report_status = '{0} bytes'.format(size_stdout)
        else:
            Report_status = 'not found'

    if view_type == VIEW_CATEGORY:
        d_list = [
            'View Category data',
            'View last execution output ({0})'.format(STD_status),
        ]
    elif view_type == VIEW_LAUNCHER:
        d_list = [
            'View Launcher data',
            'View Launcher statistics',
            'View Launcher metadata/audit report',
            'View Launcher assets report',
            'View Launcher scanner report ({0})'.format(Report_status),
            'View last execution output ({0})'.format(STD_status),
        ]
    elif view_type == VIEW_COLLECTION:
        d_list = [
            'View Collection data',
            'View last execution output ({0})'.format(STD_status),
        ]
    elif view_type == VIEW_ROM_LAUNCHER:
        d_list = [
            'View ROM manual',
            'View ROM map',
            'View ROM data',
            'View Launcher statistics',
            'View Launcher metadata/audit report',
            'View Launcher assets report',
            'View Launcher scanner report ({0})'.format(Report_status),
            'View last execution output ({0})'.format(STD_status),
        ]
    elif view_type == VIEW_ROM_VLAUNCHER:
        # >> ROM in Favourites or Virtual Launcher (no launcher report)
        d_list = [
            'View ROM manual',
            'View ROM map',
            'View ROM data',
            'View last execution output ({0})'.format(STD_status),
        ]
    elif view_type == VIEW_ROM_COLLECTION:
        d_list = [
            'View ROM manual',
            'View ROM map',
            'View ROM data',
            'View last execution output ({0})'.format(STD_status),
        ]
    else:
        kodi_dialog_OK('Wrong view_type = {0}. This is a bug, please report it.'.format(view_type))
        return
    selected_value = xbmcgui.Dialog().select('View', d_list)
    if selected_value < 0: return

    # --- Polymorphic menu. Determine action to do. ---
    if view_type == VIEW_CATEGORY:
        if   selected_value == 0: action = ACTION_VIEW_CATEGORY
        elif selected_value == 1: action = ACTION_VIEW_EXEC_OUTPUT
        else:
            kodi_dialog_OK('view_type == VIEW_CATEGORY and selected_value = {0}. '.format(selected_value) +
                           'This is a bug, please report it.')
            return
    elif view_type == VIEW_LAUNCHER:
        if   selected_value == 0: action = ACTION_VIEW_LAUNCHER
        elif selected_value == 1: action = ACTION_VIEW_LAUNCHER_STATS
        elif selected_value == 2: action = ACTION_VIEW_LAUNCHER_METADATA
        elif selected_value == 3: action = ACTION_VIEW_LAUNCHER_ASSETS
        elif selected_value == 4: action = ACTION_VIEW_LAUNCHER_SCANNER
        elif selected_value == 5: action = ACTION_VIEW_EXEC_OUTPUT
        else:
            kodi_dialog_OK('view_type == VIEW_LAUNCHER and selected_value = {0}. '.format(selected_value) +
                           'This is a bug, please report it.')
            return
    elif view_type == VIEW_COLLECTION:
        if   selected_value == 0: action = ACTION_VIEW_COLLECTION
        elif selected_value == 1: action = ACTION_VIEW_EXEC_OUTPUT
        else:
            kodi_dialog_OK('view_type == VIEW_COLLECTION and selected_value = {0}. '.format(selected_value) +
                           'This is a bug, please report it.')
            return
    elif view_type == VIEW_ROM_LAUNCHER:
        if   selected_value == 0: action = ACTION_VIEW_MANUAL
        elif selected_value == 1: action = ACTION_VIEW_MAP
        elif selected_value == 2: action = ACTION_VIEW_ROM
        elif selected_value == 3: action = ACTION_VIEW_LAUNCHER_STATS
        elif selected_value == 4: action = ACTION_VIEW_LAUNCHER_METADATA
        elif selected_value == 5: action = ACTION_VIEW_LAUNCHER_ASSETS
        elif selected_value == 6: action = ACTION_VIEW_LAUNCHER_SCANNER
        elif selected_value == 7: action = ACTION_VIEW_EXEC_OUTPUT
        else:
            kodi_dialog_OK('view_type == VIEW_ROM_LAUNCHER and selected_value = {0}. '.format(selected_value) +
                           'This is a bug, please report it.')
            return
    elif view_type == VIEW_ROM_VLAUNCHER:
        if   selected_value == 0: action = ACTION_VIEW_MANUAL
        elif selected_value == 1: action = ACTION_VIEW_MAP
        elif selected_value == 2: action = ACTION_VIEW_ROM
        elif selected_value == 3: action = ACTION_VIEW_EXEC_OUTPUT
        else:
            kodi_dialog_OK('view_type == VIEW_ROM_VLAUNCHER and selected_value = {0}. '.format(selected_value) +
                           'This is a bug, please report it.')
            return
    elif view_type == VIEW_ROM_COLLECTION:
        if   selected_value == 0: action = ACTION_VIEW_MANUAL
        elif selected_value == 1: action = ACTION_VIEW_MAP
        elif selected_value == 2: action = ACTION_VIEW_ROM
        elif selected_value == 3: action = ACTION_VIEW_EXEC_OUTPUT
        else:
            kodi_dialog_OK('view_type == VIEW_ROM_COLLECTION and selected_value = {0}. '.format(selected_value) +
                           'This is a bug, please report it.')
            return
    else:
        kodi_dialog_OK('Wrong view_type == {0}. '.format(view_type) +
                       'This is a bug, please report it.')
        return
    log_debug('_command_view_menu() action = {0}'.format(action))

    # --- Execute action ---
    if action == ACTION_VIEW_CATEGORY or action == ACTION_VIEW_LAUNCHER or \
       action == ACTION_VIEW_COLLECTION or action == ACTION_VIEW_ROM:
        slist = []
        if view_type == VIEW_CATEGORY:
            window_title = 'Category data'
            category = g_ObjectFactory.find_category(categoryID)
            slist.append('[COLOR orange]Category information[/COLOR]')
            report_print_Category(slist, category.get_data_dic())
        elif view_type == VIEW_LAUNCHER:
            window_title = 'Launcher data'
            launcher = g_ObjectFactory.find_launcher(categoryID, launcherID)
            category = g_ObjectFactory.find_category(launcher.get_id())
            slist.append('[COLOR orange]Launcher information[/COLOR]')
            report_print_Launcher(slist, launcher.get_data_dic())
            if category:
                slist.append('')
                slist.append('[COLOR orange]Category information[/COLOR]')
                report_print_Category(slist, category.get_data_dic())
        elif view_type == VIEW_COLLECTION:
            window_title = 'ROM Collection data'
            (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
            collection = collections[launcherID]
            slist.append('[COLOR orange]ROM Collection information[/COLOR]')
            report_print_Collection(slist, collection)
        else:
            # --- Read ROMs ---
            log_info('_command_view_menu() Viewing ROM in {} ...'.format(launcher.get_launcher_type_name()))
            
            if romID == UNKNOWN_ROMS_PARENT_ID:
                kodi_dialog_OK('You cannot view this ROM!')
                return

            # >> Check launcher is OK
            launcher = g_LauncherRepository.find(launcherID)
            if launcher is None:
                kodi_dialog_OK('launcherID not found in launchers')
                return

            launcher_in_category = False if categoryID == VCATEGORY_ADDONROOT_ID else True
            if launcher_in_category: category = self.category_repository.find(categoryID)

            rom = launcher.select_rom(romID)
            window_title = '{} ROM data'.format(launcher.get_launcher_type_name())
            regular_launcher = True
            if launcher.get_launcher_type() == LAUNCHER_VIRTUAL or launcher.get_launcher_type() == LAUNCHER_COLLECTION:
                regular_launcher = False
                vlauncher_label = launcher.get_name()

            if categoryID == VCATEGORY_RECENT_ID:
                log_info('_command_view_menu() Viewing ROM in Recently played ROMs ...')
                recent_roms_list = fs_load_Collection_ROMs_JSON(RECENT_PLAYED_FILE_PATH)
                current_ROM_position = fs_collection_ROM_index_by_romID(romID, recent_roms_list)
                if current_ROM_position < 0:
                    kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
                    return
                rom = recent_roms_list[current_ROM_position]
                window_title = 'Recently played ROM data'
                regular_launcher = False
                vlauncher_label = 'Recently played ROM'

            # --- ROM in Collection ---
            elif categoryID == VCATEGORY_COLLECTIONS_ID:
                log_info('_command_view_menu() Viewing ROM in Collection ...')
                (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
                collection = collections[launcherID]
                roms_json_file = COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
                collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
                current_ROM_position = fs_collection_ROM_index_by_romID(romID, collection_rom_list)
                if current_ROM_position < 0:
                    kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
                    return
                rom = collection_rom_list[current_ROM_position]
                window_title = '{0} Collection ROM data'.format(collection['m_name'])
                regular_launcher = False
                vlauncher_label = 'Collection'

            # --- Make information string ---
            info_text  = '[COLOR orange]ROM information[/COLOR]\n'
            info_text += self._misc_print_string_ROM(rom)

            # --- Display category/launcher information ---
            if regular_launcher:
                info_text += '\n[COLOR orange]Launcher information[/COLOR]\n'
                info_text += self._misc_print_string_Launcher(launcher)
                info_text += '\n[COLOR orange]Category information[/COLOR]\n'
                if launcher_in_category:
                    info_text += self._misc_print_string_Category(category.get_data())
                else:
                    info_text += 'No Category (Launcher in addon root)'
            else:
                info_text += '\n[COLOR orange]{0} ROM additional information[/COLOR]\n'.format(vlauncher_label)
                info_text += self._misc_print_string_ROM_additional(rom)

        # --- Show information window ---
        kodi_display_text_window_mono(window_title, '\n'.join(slist))

    # --- Launcher statistical reports ---
    elif action == ACTION_VIEW_LAUNCHER_STATS or \
         action == ACTION_VIEW_LAUNCHER_METADATA or \
         action == ACTION_VIEW_LAUNCHER_ASSETS:
        
        # --- Standalone launchers do not have reports! ---
        category = self.category_repository.find(categoryID)
        category_name = category.get_name()
        
        launcher = g_LauncherRepository.find(launcherID)

        if not launcher.supports_launching_roms():
            kodi_notify_warn('Cannot create report for standalone launcher')
            return

        # --- If no ROMs in launcher do nothing ---
        roms = launcher.get_roms()

        if not roms:
            kodi_notify_warn('No ROMs in launcher. Report not created')
            return
        # --- Regenerate reports if don't exist or are outdated ---
        self._roms_regenerate_launcher_reports(categoryID, launcherID, roms)

        # --- Get report filename ---
        roms_base_noext  = fs_get_ROMs_basename(category_name, launcher.get_name(), launcherID)
        report_stats_FN  = REPORTS_DIR.pjoin(roms_base_noext + '_stats.txt')
        report_meta_FN   = REPORTS_DIR.pjoin(roms_base_noext + '_metadata.txt')
        report_assets_FN = REPORTS_DIR.pjoin(roms_base_noext + '_assets.txt')
        log_verb('_command_view_menu() Stats  OP "{0}"'.format(report_stats_FN.getOriginalPath()))
        log_verb('_command_view_menu() Meta   OP "{0}"'.format(report_meta_FN.getOriginalPath()))
        log_verb('_command_view_menu() Assets OP "{0}"'.format(report_assets_FN.getOriginalPath()))

        # --- Read report file ---
        try:
            if action == ACTION_VIEW_LAUNCHER_STATS:
                window_title = 'Launcher "{0}" Statistics Report'.format(launcher.get_name())
                info_text = report_stats_FN.readAll()
            elif action == ACTION_VIEW_LAUNCHER_METADATA:
                window_title = 'Launcher "{0}" Metadata Report'.format(launcher.get_name())
                info_text = report_meta_FN.readAll()
            elif action == ACTION_VIEW_LAUNCHER_ASSETS:
                window_title = 'Launcher "{0}" Asset Report'.format(launcher.get_name())
                info_text = report_assets_FN.readAll()
        except IOError:
            log_error('_command_view_menu() (IOError) Exception reading report TXT file')
            window_title = 'Error'
            info_text = '[COLOR red]Exception reading report TXT file.[/COLOR]'
        info_text = info_text.replace('<No-Intro Audit Statistics>', '[COLOR orange]<No-Intro Audit Statistics>[/COLOR]')
        info_text = info_text.replace('<Metadata statistics>', '[COLOR orange]<Metadata statistics>[/COLOR]')
        info_text = info_text.replace('<Asset statistics>', '[COLOR orange]<Asset statistics>[/COLOR]')

        # --- Show information window ---
        kodi_display_text_window_mono(window_title, info_text)

    # --- Launcher ROM scanner report ---
    elif action == ACTION_VIEW_LAUNCHER_SCANNER:
        # --- Ckeck for errors and read file ---
        if not launcher_report_FN.exists():
            kodi_dialog_OK('ROM scanner report not found.')
            return
        info_text = ''
        with open(launcher_report_FN.getPath(), 'r') as myfile:
            info_text = myfile.read()

        # --- Show information window ---
        window_title = 'ROM scanner report'
        kodi_display_text_window_mono(window_title, info_text)

    # --- View ROM Manual ---
    # >> Use Ghostscript like HyperLauncher?
    # >> Or use plugin.image.pdfreader plugin?
    # >> Or ask core developers to incorporate a native PDF reader?
    elif action == ACTION_VIEW_MANUAL:
        kodi_dialog_OK('View ROM manual not implemented yet. Sorry.')

    # --- View ROM Map ---
    elif action == ACTION_VIEW_MAP:
        # >> Load ROMs
        if categoryID == VCATEGORY_FAVOURITES_ID:
            roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
            rom = roms[romID]
        elif categoryID == VCATEGORY_MOST_PLAYED_ID:
            most_played_roms = fs_load_Favourites_JSON(MOST_PLAYED_FILE_PATH)
            rom = most_played_roms[romID]
        elif categoryID == VCATEGORY_RECENT_ID:
            recent_roms_list = fs_load_Collection_ROMs_JSON(RECENT_PLAYED_FILE_PATH)
            current_ROM_position = fs_collection_ROM_index_by_romID(romID, recent_roms_list)
            if current_ROM_position < 0:
                kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
                return
            rom = recent_roms_list[current_ROM_position]
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
            collection = collections[launcherID]
            roms_json_file = COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
            collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
            current_ROM_position = fs_collection_ROM_index_by_romID(romID, collection_rom_list)
            if current_ROM_position < 0:
                kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
                return
            rom = collection_rom_list[current_ROM_position]
        elif categoryID == VCATEGORY_TITLE_ID    or categoryID == VCATEGORY_YEARS_ID or \
             categoryID == VCATEGORY_GENRE_ID    or categoryID == VCATEGORY_DEVELOPER_ID or \
             categoryID == VCATEGORY_NPLAYERS_ID or categoryID == VCATEGORY_ESRB_ID or \
             categoryID == VCATEGORY_RATING_ID   or categoryID == VCATEGORY_CATEGORY_ID:
            kodi_dialog_OK('ROM-loading factory not implemented yet. '
                           'Until then you cannot see maps in Virtual Launchers. '
                           'Sorry.')
            return
        else:
            launcher = g_LauncherRepository.find(launcherID)
            rom = launcher.select_rom(romID)

        # >> Show map image
        map_asset_info = self.assetFactory.get_asset_info(ASSET_MAP)
        map_FN = rom.get_asset_file(map_asset_info)
        if map_FN is None:
            kodi_dialog_OK('Map image file not set for ROM "{0}"'.format(rom.get_name()))
            return

        if not map_FN.exists():
            kodi_dialog_OK('Map image file not found.')
            return
        xbmc.executebuiltin('ShowPicture("{0}")'.format(map_FN.getPath()))

    # --- View last execution output ---
    elif action == ACTION_VIEW_EXEC_OUTPUT:
        log_debug('_command_view_menu() Executing action == ACTION_VIEW_EXEC_OUTPUT')

        # --- Ckeck for errors and read file ---
        if not g_PATHS.LAUNCH_LOG_FILE_PATH.exists():
            kodi_dialog_OK('Log file not found. Try to run the emulator/application.')
            return
        # >> Kodi BUG: if the log file size is 0 (it is empty) then Kodi displays in the
        # >> text window the last displayed text.
        info_text = ''
        with open(g_PATHSLAUNCH_LOG_FILE_PATH.getPath(), 'r') as myfile:
            log_debug('_command_view_menu() Reading launcher.log ...')
            info_text = myfile.read()

        # --- Show information window ---
        window_title = 'Launcher last execution stdout'
        kodi_display_text_window_mono(window_title, info_text)

    else:
        kodi_dialog_OK('Wrong action == {0}. This is a bug, please report it.'.format(action))

def m_command_view_offline_scraper_rom(scraper, platform, game_name):
    log_debug('_command_view_offline_scraper_rom() scraper   "{0}"'.format(scraper))
    log_debug('_command_view_offline_scraper_rom() platform  "{0}"'.format(platform))
    log_debug('_command_view_offline_scraper_rom() game_name "{0}"'.format(game_name))

    # --- Load Offline Scraper database ---
    # --- Load offline scraper XML file ---
    # NOTE Move this code to reports.py
    if scraper == 'AEL':
        xml_file = platform_AEL_to_Offline_GameDBInfo_XML[platform]
        xml_path = CURRENT_ADDON_DIR.pjoin(xml_file)

        # log_debug('xml_file = {0}'.format(xml_file))
        log_debug('Loading AEL XML {0}'.format(xml_path.getOriginalPath()))
        games = audit_load_OfflineScraper_XML(xml_path)
        game = games[game_name]

        # IMPORTANT Move this code to report.py
        info_text  = '[COLOR orange]ROM information[/COLOR]\n'
        info_text += "[COLOR violet]game_name[/COLOR]: '{0}'\n".format(game_name)
        info_text += "[COLOR violet]platform[/COLOR]: '{0}'\n".format(platform)
        info_text += '\n[COLOR orange]Metadata[/COLOR]\n'
        info_text += "[COLOR violet]description[/COLOR]: '{0}'\n".format(game['description'])
        info_text += "[COLOR violet]year[/COLOR]: '{0}'\n".format(game['year'])
        info_text += "[COLOR violet]rating[/COLOR]: '{0}'\n".format(game['rating'])
        info_text += "[COLOR violet]manufacturer[/COLOR]: '{0}'\n".format(game['manufacturer'])
        info_text += "[COLOR violet]dev[/COLOR]: '{0}'\n".format(game['dev'])
        info_text += "[COLOR violet]genre[/COLOR]: '{0}'\n".format(game['genre'])
        info_text += "[COLOR violet]score[/COLOR]: '{0}'\n".format(game['score'])
        info_text += "[COLOR violet]player[/COLOR]: '{0}'\n".format(game['player'])
        info_text += "[COLOR violet]story[/COLOR]: '{0}'\n".format(game['story'])
        info_text += "[COLOR violet]enabled[/COLOR]: '{0}'\n".format(game['enabled'])
        info_text += "[COLOR violet]crc[/COLOR]: '{0}'\n".format(game['crc'])
        info_text += "[COLOR violet]cloneof[/COLOR]: '{0}'\n".format(game['cloneof'])
    elif scraper == 'LaunchBox':
        xml_file = platform_AEL_to_LB_XML[platform]
        xml_path = CURRENT_ADDON_DIR.pjoin(xml_file)

        # log_debug('xml_file = {0}'.format(xml_file))
        log_debug('Loading LaunchBox XML {0}'.format(xml_path.getOriginalPath()))
        games = audit_load_OfflineScraper_XML(xml_path)
        game = games[game_name]
        # log_debug(unicode(game))

        info_text  = '[COLOR orange]ROM information[/COLOR]\n'
        info_text += "[COLOR violet]game_name[/COLOR]: '{0}'\n".format(game_name)
        info_text += "[COLOR violet]platform[/COLOR]: '{0}'\n".format(platform)
        info_text += '\n[COLOR orange]Metadata[/COLOR]\n'
        info_text += "[COLOR violet]Name[/COLOR]: '{0}'\n".format(game['Name'])
        info_text += "[COLOR violet]ReleaseYear[/COLOR]: '{0}'\n".format(game['ReleaseYear'])            
        info_text += "[COLOR violet]Overview[/COLOR]: '{0}'\n".format(game['Overview'])
        info_text += "[COLOR violet]MaxPlayers[/COLOR]: '{0}'\n".format(game['MaxPlayers'])
        info_text += "[COLOR violet]Cooperative[/COLOR]: '{0}'\n".format(game['Cooperative'])
        info_text += "[COLOR violet]VideoURL[/COLOR]: '{0}'\n".format(game['VideoURL'])
        info_text += "[COLOR violet]DatabaseID[/COLOR]: '{0}'\n".format(game['DatabaseID'])
        info_text += "[COLOR violet]CommunityRating[/COLOR]: '{0}'\n".format(game['CommunityRating'])
        info_text += "[COLOR violet]Platform[/COLOR]: '{0}'\n".format(game['Platform'])
        info_text += "[COLOR violet]Genres[/COLOR]: '{0}'\n".format(game['Genres'])
        info_text += "[COLOR violet]Publisher[/COLOR]: '{0}'\n".format(game['Publisher'])
        info_text += "[COLOR violet]Developer[/COLOR]: '{0}'\n".format(game['Developer'])
    else:
        kodi_dialog_OK('Wrong scraper name {0}'.format(scraper))
        return
    kodi_display_text_window_mono(window_title, info_text)

#
# Updated all virtual categories DB
#
def m_command_update_virtual_category_db_all():
    # --- Sanity checks ---
    launchers = g_LauncherRepository.find_all()
    if len(launchers) == 0:
        kodi_dialog_OK('You do not have any ROM Launcher. Add a ROM Launcher first.')
        return

    # --- Make a big dictionary will all the ROMs ---
    # Pass all_roms dictionary to the catalg create functions so this has not to be
    # recomputed for every virtual launcher.
    log_verb('_command_update_virtual_category_db_all() Creating list of all ROMs in all Launchers')
    all_roms = {}
    num_launchers = len(launchers)
    i = 0
    pDialog = xbmcgui.DialogProgress()
    pDialog_canceled = False
    pDialog.create('Advanced Emulator Launcher', 'Making ROM list ...')
    for launcher in launchers:
        # >> Update dialog
        pDialog.update(i * 100 / num_launchers)
        i += 1

        # >> Get current launcher
        categoryID = launcher.get_category_id()
        category = self.category_repository.find(categoryID)

        if category is None:
            log_error('_command_update_virtual_category_db_all() Wrong categoryID = {0}'.format(categoryID))
            kodi_dialog_OK('Wrong categoryID = {0}. Report this bug please.'.format(categoryID))
            return

        # >> If launcher is standalone skip
        if not launcher.supports_launching_roms():
            continue

        # >> Open launcher and add roms to the big list
        rom_ids = launcher.get_rom_ids()

        # >> Add additional fields to ROM to make a Favourites ROM
        # >> Virtual categories/launchers are like Favourite ROMs that cannot be edited.
        # >> NOTE roms is updated by assigment, dictionaries are mutable
        fav_roms = {}
        for rom_id in rom_ids:
            fav_rom = launcher.convert_rom_to_favourite(rom_id)
            # >> Add the category this ROM belongs to.
            fav_rom.set_custom_attribute('category_name', category.get_name())
            fav_roms[rom_id] = fav_rom

        # >> Update dictionary
        all_roms.update(fav_roms)
    pDialog.update(100)
    pDialog.close()

    # --- Update all virtual launchers ---
    m_command_update_virtual_category_db(VCATEGORY_TITLE_ID, all_roms)
    m_command_update_virtual_category_db(VCATEGORY_YEARS_ID, all_roms)
    m_command_update_virtual_category_db(VCATEGORY_GENRE_ID, all_roms)
    m_command_update_virtual_category_db(VCATEGORY_DEVELOPER_ID, all_roms)
    m_command_update_virtual_category_db(VCATEGORY_NPLAYERS_ID, all_roms)
    m_command_update_virtual_category_db(VCATEGORY_ESRB_ID, all_roms)
    m_command_update_virtual_category_db(VCATEGORY_RATING_ID, all_roms)
    m_command_update_virtual_category_db(VCATEGORY_CATEGORY_ID, all_roms)
    kodi_notify('All virtual categories updated')

#
# Makes a virtual category database
#
def m_command_update_virtual_category_db(virtual_categoryID, all_roms_external = None):
    # --- Customise function depending on virtual category ---
    if virtual_categoryID == VCATEGORY_TITLE_ID:
        log_info('_command_update_virtual_category_db() Updating Title DB')
        vcategory_db_directory = VIRTUAL_CAT_TITLE_DIR
        vcategory_db_filename  = VCAT_TITLE_FILE_PATH
        vcategory_field_name   = 'm_name'
        vcategory_name         = 'Titles'
    elif virtual_categoryID == VCATEGORY_YEARS_ID:
        log_info('_command_update_virtual_category_db() Updating Year DB')
        vcategory_db_directory = VIRTUAL_CAT_YEARS_DIR
        vcategory_db_filename  = VCAT_YEARS_FILE_PATH
        vcategory_field_name   = 'm_year'
        vcategory_name         = 'Years'
    elif virtual_categoryID == VCATEGORY_GENRE_ID:
        log_info('_command_update_virtual_category_db() Updating Genre DB')
        vcategory_db_directory = VIRTUAL_CAT_GENRE_DIR
        vcategory_db_filename  = VCAT_GENRE_FILE_PATH
        vcategory_field_name   = 'm_genre'
        vcategory_name         = 'Genres'
    elif virtual_categoryID == VCATEGORY_DEVELOPER_ID:
        log_info('_command_update_virtual_category_db() Updating Developer DB')
        vcategory_db_directory = VIRTUAL_CAT_DEVELOPER_DIR
        vcategory_db_filename  = VCAT_DEVELOPER_FILE_PATH
        vcategory_field_name   = 'm_developer'
        vcategory_name         = 'Developers'
    elif virtual_categoryID == VCATEGORY_NPLAYERS_ID:
        log_info('_command_update_virtual_category_db() Updating NPlayer DB')
        vcategory_db_directory = VIRTUAL_CAT_NPLAYERS_DIR
        vcategory_db_filename  = VCAT_NPLAYERS_FILE_PATH
        vcategory_field_name   = 'm_nplayers'
        vcategory_name         = 'NPlayers'
    elif virtual_categoryID == VCATEGORY_ESRB_ID:
        log_info('_command_update_virtual_category_db() Updating ESRB DB')
        vcategory_db_directory = VIRTUAL_CAT_ESRB_DIR
        vcategory_db_filename  = VCAT_ESRB_FILE_PATH
        vcategory_field_name   = 'm_esrb'
        vcategory_name         = 'ESRB'
    elif virtual_categoryID == VCATEGORY_RATING_ID:
        log_info('_command_update_virtual_category_db() Updating Rating DB')
        vcategory_db_directory = VIRTUAL_CAT_RATING_DIR
        vcategory_db_filename  = VCAT_RATING_FILE_PATH
        vcategory_field_name   = 'm_rating'
        vcategory_name         = 'Rating'
    elif virtual_categoryID == VCATEGORY_CATEGORY_ID:
        log_info('_command_update_virtual_category_db() Updating Category DB')
        vcategory_db_directory = VIRTUAL_CAT_CATEGORY_DIR
        vcategory_db_filename  = VCAT_CATEGORY_FILE_PATH
        vcategory_field_name   = ''
        vcategory_name         = 'Categories'
    else:
        log_error('_command_update_virtual_category_db() Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
        kodi_dialog_OK('Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
        return

    # --- Sanity checks ---
    if g_LauncherRepository.count() == 0:
        kodi_dialog_OK('You do not have any ROM Launcher. Add a ROM Launcher first.')
        return

    # --- Delete previous hashed database XMLs ---
    log_info('_command_update_virtual_category_db() Cleaning hashed database old XMLs')
    for the_file in vcategory_db_directory.scanFilesInPathAsFileNameObjects('*.*'):
        file_extension = the_file.getExt()
        if file_extension.lower() != '.xml' and file_extension.lower() != '.json':
            # >> There should be only XMLs or JSON in this directory
            log_error('_command_update_virtual_category_db() Non XML/JSON file "{0}"'.format(the_file.getOriginalPath()))
            log_error('_command_update_virtual_category_db() Skipping it from deletion')
            continue
        log_verb('_command_update_virtual_category_db() Deleting "{0}"'.format(the_file.getOriginalPath()))
        try:
            if the_file.exists():
                the_file.unlink()
        except Exception as e:
            log_error('_command_update_virtual_category_db() Excepcion deleting hashed DB XMLs')
            log_error('_command_update_virtual_category_db() {0}'.format(e))
            return

    # --- Progress dialog ---
    # >> Important to avoid multithread execution of the plugin and race conditions
    pDialog = xbmcgui.DialogProgress()
    pDialog_canceled = False

    # --- Make a big dictionary will all the ROMs ---
    if all_roms_external:
        log_verb('_command_update_virtual_category_db() Using cached all_roms dictionary')
        all_roms = all_roms_external
    else:
        log_verb('_command_update_virtual_category_db() Creating list of all ROMs in all Launchers')
        all_roms = {}

        launchers = g_LauncherRepository.find_all()
        num_launchers = len(launchers)
        i = 0
        pDialog.create('Advanced Emulator Launcher', 'Making ROM list ...')
        for launcher in launchers:
            # >> Update dialog
            pDialog.update(i * 100 / num_launchers)
            i += 1

            categoryID = launcher.get_category_id()
            category = self.category_repository.find(categoryID)

            if category is None:
                log_error('_command_update_virtual_category_db() Wrong categoryID = {0}'.format(categoryID))
                kodi_dialog_OK('Wrong categoryID = {0}. Report this bug please.'.format(categoryID))
                return

            # >> If launcher is standalone skip
            if not launcher.supports_launching_roms(): 
                continue

            # >> Open launcher and add roms to the big list
            rom_ids = launcher.get_rom_ids()
            
            # >> Add additional fields to ROM to make a Favourites ROM
            # >> Virtual categories/launchers are like Favourite ROMs that cannot be edited.
            # >> NOTE roms is updated by assigment, dictionaries are mutable
            fav_roms = {}
            for rom_id in rom_ids:
                fav_rom = launcher.convert_rom_to_favourite(rom_id)
                # >> Add the category this ROM belongs to.
                fav_rom.set_custom_attribute('category_name', category.get_name())
                fav_roms[rom_id] = fav_rom

            # >> Update dictionary
            all_roms.update(fav_roms)
        pDialog.update(100)
        pDialog.close()

    # --- Create a dictionary with key the virtual category name and value a dictionay of roms
    #     belonging to that virtual category ---
    # TODO It would be nice to have a progress dialog here...
    log_verb('_command_update_virtual_category_db() Creating hashed database')
    virtual_launchers = {}
    for rom_id in all_roms:
        rom = all_roms[rom_id]
        if virtual_categoryID == VCATEGORY_TITLE_ID:
            vcategory_key = rom.get_name()[0].upper()
        elif virtual_categoryID == VCATEGORY_CATEGORY_ID:
            vcategory_key = rom.get_custom_attribute('category_name')
        else:
            vcategory_key = rom.get_custom_attribute(vcategory_field_name)
        # >> '' is a special case
        if vcategory_key == '': vcategory_key = '[ Not set ]'
        if vcategory_key in virtual_launchers:
            virtual_launchers[vcategory_key][rom_id] = rom
        else:
            virtual_launchers[vcategory_key] = {rom_id : rom}

    # --- Write hashed distributed database XML files ---
    # TODO It would be nice to have a progress dialog here...
    log_verb('_command_update_virtual_category_db() Writing hashed database JSON files')
    vcategory_launchers = {}
    num_vlaunchers = len(virtual_launchers)
    i = 0
    pDialog.create('Advanced Emulator Launcher', 'Writing {0} hashed database ...'.format(vcategory_name))
    for vlauncher_id in virtual_launchers:
        # >> Update progress dialog
        pDialog.update(i * 100 / num_vlaunchers)
        i += 1

        # >> Create VLauncher UUID
        vlauncher_id_md5   = hashlib.md5(vlauncher_id.encode('utf-8'))
        hashed_db_UUID     = vlauncher_id_md5.hexdigest()
        log_debug('_command_update_virtual_category_db() vlauncher_id       "{0}"'.format(vlauncher_id))
        log_debug('_command_update_virtual_category_db() hashed_db_UUID     "{0}"'.format(hashed_db_UUID))

        # >> Virtual launcher ROMs are like Favourite ROMs. They contain all required fields to launch
        # >> the ROM, and also share filesystem I/O functions with Favourite ROMs.
        vlauncher_roms = virtual_launchers[vlauncher_id]
        log_debug('_command_update_virtual_category_db() Number of ROMs = {0}'.format(len(vlauncher_roms)))
        fs_write_VCategory_ROMs_JSON(vcategory_db_directory, hashed_db_UUID, vlauncher_roms)

        # >> Create virtual launcher
        vcategory_launchers[hashed_db_UUID] = {'id'              : hashed_db_UUID,
                                               'name'            : vlauncher_id,
                                               'rom_count'       : str(len(vlauncher_roms)),
                                               'roms_base_noext' : hashed_db_UUID }
    pDialog.update(100)
    pDialog.close()

    # --- Write virtual launchers XML file ---
    # >> This file is small, no progress dialog
    log_verb('_command_update_virtual_category_db() Writing virtual category XML index')
    fs_write_VCategory_XML(vcategory_db_filename, vcategory_launchers)

#
# Launchs a standalone application.
#
def m_command_run_standalone_launcher(categoryID, launcherID):
    
    log_info('_command_run_standalone_launcher() Launching Standalone Launcher ...')
    launcher = g_LauncherRepository.find(launcherID)

    # --- Check launcher is OK ---
    if launcher is None:
        kodi_dialog_OK('Could not start launcher. Check the logs')
        return

    launcher.launch()

#
# Launchs a ROM
# NOTE args_extre maybe present or not in Favourite ROM. In newer version of AEL always present.
#
def m_command_run_rom(categoryID, launcherID, romID):
    # --- ROM in Favourites ---
    if categoryID == VCATEGORY_FAVOURITES_ID and launcherID == VLAUNCHER_FAVOURITES_ID:
        log_info('_command_run_rom() Launching ROM in Favourites ...')
        roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
        rom = roms[romID]
        recent_rom = rom
        minimize_flag     = rom['toggle_window']
        non_blocking_flag = rom['non_blocking']
        romext            = rom['romext']
        standard_app      = rom['application']
        standard_args     = rom['args']
        args_extra        = rom['args_extra'] if 'args_extra' in rom else list()
    # --- ROM in Recently played ROMs list ---
    elif categoryID == VCATEGORY_MOST_PLAYED_ID and launcherID == VLAUNCHER_MOST_PLAYED_ID:
        log_info('_command_run_rom() Launching ROM in Recently Played ROMs ...')
        recent_roms_list = fs_load_Collection_ROMs_JSON(RECENT_PLAYED_FILE_PATH)
        current_ROM_position = fs_collection_ROM_index_by_romID(romID, recent_roms_list)
        if current_ROM_position < 0:
            kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
            return
        rom = recent_roms_list[current_ROM_position]
        recent_rom = rom
        minimize_flag     = rom['toggle_window']
        non_blocking_flag = rom['non_blocking']
        romext            = rom['romext']
        standard_app      = rom['application']
        standard_args     = rom['args']
        args_extra        = rom['args_extra'] if 'args_extra' in rom else list()
    # --- ROM in Most played ROMs ---
    elif categoryID == VCATEGORY_RECENT_ID and launcherID == VLAUNCHER_RECENT_ID:
        log_info('_command_run_rom() Launching ROM in Most played ROMs ...')
        most_played_roms = fs_load_Favourites_JSON(MOST_PLAYED_FILE_PATH)
        rom = most_played_roms[romID]
        recent_rom = rom
        minimize_flag     = rom['toggle_window']
        non_blocking_flag = rom['non_blocking']
        romext            = rom['romext']
        standard_app      = rom['application']
        standard_args     = rom['args']
        args_extra        = rom['args_extra'] if 'args_extra' in rom else list()
    # --- ROM in Collection ---
    elif categoryID == VCATEGORY_COLLECTIONS_ID:
        log_info('_command_run_rom() Launching ROM in Collection ...')
        (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
        collection = collections[launcherID]
        roms_json_file = COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
        collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
        current_ROM_position = fs_collection_ROM_index_by_romID(romID, collection_rom_list)
        if current_ROM_position < 0:
            kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
            return
        rom = collection_rom_list[current_ROM_position]
        recent_rom = rom
        minimize_flag     = rom['toggle_window']
        non_blocking_flag = rom['non_blocking']
        romext            = rom['romext']
        standard_app      = rom['application']
        standard_args     = rom['args']
        args_extra        = rom['args_extra'] if 'args_extra' in rom else list()
    # --- ROM in Virtual Launcher ---
    elif categoryID == VCATEGORY_TITLE_ID or categoryID == VCATEGORY_YEARS_ID or \
         categoryID == VCATEGORY_GENRE_ID or categoryID == VCATEGORY_DEVELOPER_ID or \
         categoryID == VCATEGORY_CATEGORY_ID:
        if categoryID == VCATEGORY_TITLE_ID:
            log_info('_command_run_rom() Launching ROM in Virtual Launcher ...')
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_TITLE_DIR, launcherID)
        elif categoryID == VCATEGORY_YEARS_ID:
            log_info('_command_run_rom() Launching ROM in Year Virtual Launcher ...')
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_YEARS_DIR, launcherID)
        elif categoryID == VCATEGORY_GENRE_ID:
            log_info('_command_run_rom() Launching ROM in Gender Virtual Launcher ...')
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_GENRE_DIR, launcherID)
        elif categoryID == VCATEGORY_DEVELOPER_ID:
            log_info('_command_run_rom() Launching ROM in Developer Virtual Launcher ...')
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_DEVELOPER_DIR, launcherID)
        elif categoryID == VCATEGORY_CATEGORY_ID:
            log_info('_command_run_rom() Launching ROM in Category Virtual Launcher ...')
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_CATEGORY_DIR, launcherID)

        rom = roms[romID]
        recent_rom = rom
        minimize_flag     = rom['toggle_window']
        non_blocking_flag = rom['non_blocking']
        romext            = rom['romext']
        standard_app      = rom['application']
        standard_args     = rom['args']
        args_extra        = rom['args_extra'] if 'args_extra' in rom else list()
    # --- ROM in standard ROM launcher ---
    else:
        log_info('_command_run_rom() Launching ROM in Launcher ...')
        # --- Check launcher is OK and load ROMs ---
        if launcherID not in self.launchers:
            kodi_dialog_OK('launcherID not found in self.launchers')
            return
        launcher = self.launchers[launcherID]
        roms = fs_load_ROMs_JSON(ROMS_DIR, launcher)
        # --- Check ROM is in XML data just read ---
        if romID not in roms:
            kodi_dialog_OK('romID not in roms dictionary')
            return
        rom = roms[romID]
        recent_rom = fs_get_Favourite_from_ROM(rom, launcher)
        minimize_flag     = launcher['toggle_window']
        non_blocking_flag = launcher['non_blocking']
        romext            = launcher['romext']
        standard_app      = launcher['application']
        standard_args     = launcher['args']
        args_extra        = launcher['args_extra']

    # ~~~~~ Substitue altapp/altarg or additional arguments ~~~~~
    # >> If ROM has altapp configured, then use altapp/altarg
    # >> If Launcher has args_extra configured then show a dialog to the user to selec the
    # >> arguments to launch ROM.
    if rom['altapp'] or rom['altarg']:
        log_info('_command_run_rom() Using ROM altapp/altarg')
        application = rom['altapp'] if rom['altapp'] else standard_app
        arguments   = rom['altarg'] if rom['altarg'] else standard_args
    elif args_extra:
        # >> Ask user what arguments to launch application
        log_info('_command_run_rom() Using Launcher args_extra')
        arg_list = [standard_args] + args_extra
        dialog = xbmcgui.Dialog()
        dselect_ret = dialog.select('Select launcher arguments', arg_list)
        if dselect_ret < 0: return
        log_info('_command_run_rom() User chose args index {0} ({1})'.format(dselect_ret, arg_list[dselect_ret]))
        application = standard_app
        arguments   = arg_list[dselect_ret]
    else:
        log_info('_command_run_rom() Using Launcher standard arguments')
        application = standard_app
        arguments   = standard_args

    # ~~~ Choose file to launch in multidisc ROM sets ~~~
    if rom['disks']:
        log_info('_command_run_rom() Multidisc ROM set detected')
        dialog = xbmcgui.Dialog()
        dselect_ret = dialog.select('Select ROM to launch in multidisc set', rom['disks'])
        if dselect_ret < 0: return
        selected_rom_base = rom['disks'][dselect_ret]
        log_info('_command_run_rom() Selected ROM "{0}"'.format(selected_rom_base))
        ROM_temp = FileName(rom['filename'])
        ROM_dir = FileName(ROM_temp.getDir())
        ROMFileName = ROM_dir.pjoin(selected_rom_base)
    else:
        log_info('_command_run_rom() Sigle ROM detected (no multidisc)')
        ROMFileName = FileName(rom['filename'])
    log_info('_command_run_rom() ROMFileName OP "{0}"'.format(ROMFileName.getOriginalPath()))
    log_info('_command_run_rom() ROMFileName  P "{0}"'.format(ROMFileName.getPath()))

    # ~~~~~ Launch ROM ~~~~~
    application   = FileName(application)
    apppath       = application.getDir()
    rompath       = ROMFileName.getDir()
    rombase       = ROMFileName.getBase()
    rombase_noext = ROMFileName.getBase_noext()
    romtitle      = rom['m_name']
    log_info('_command_run_rom() categoryID   {0}'.format(categoryID))
    log_info('_command_run_rom() launcherID   {0}'.format(launcherID))
    log_info('_command_run_rom() romID        {0}'.format(romID))
    log_info('_command_run_rom() romfile      "{0}"'.format(ROMFileName.getPath()))
    log_info('_command_run_rom() rompath      "{0}"'.format(rompath))
    log_info('_command_run_rom() rombase      "{0}"'.format(rombase))
    log_info('_command_run_rom() rombasenoext "{0}"'.format(rombase_noext))
    log_info('_command_run_rom() romtitle     "{0}"'.format(romtitle))
    log_info('_command_run_rom() application  "{0}"'.format(application.getPath()))
    log_info('_command_run_rom() apppath      "{0}"'.format(apppath))
    log_info('_command_run_rom() romext       "{0}"'.format(romext))

    # --- Check for errors and abort if found --- todo: CHECK
    if not application.exists() and (
        application.getOriginalPath() != RETROPLAYER_LAUNCHER_APP_NAME and
        application.getOriginalPath() != LNK_LAUNCHER_APP_NAME ):
        log_error('Launching app not found "{0}"'.format(application.getPath()))
        kodi_notify_warn('Launching app not found {0}'.format(application.getOriginalPath()))
        return
    else:
        log_info('Launching app found "{0}"'.format(application.getPath()))

    if not ROMFileName.exists():
        log_error('ROM not found "{0}"'.format(ROMFileName.getPath()))
        kodi_notify_warn('ROM not found "{0}"'.format(ROMFileName.getOriginalPath()))
        return
    else:
        log_info('ROM found "{0}"'.format(ROMFileName.getPath()))

    # --- Escape quotes and double quotes in ROMFileName ---
    # >> This maybe useful to Android users with complex command line arguments
    if g_settings['escape_romfile']:
        log_info("_command_run_rom() Escaping ROMFileName ' and \"")
        ROMFileName.escapeQuotes()

    # ~~~~ Argument substitution ~~~~~
    log_info('_command_run_rom() raw arguments   "{0}"'.format(arguments))
    arguments = arguments.replace('$categoryID$', categoryID)
    arguments = arguments.replace('$launcherID$', launcherID)
    arguments = arguments.replace('$romID$', romID)
    arguments = arguments.replace('$rom$', ROMFileName.getPath())
    arguments = arguments.replace('$romfile$', ROMFileName.getPath())
    arguments = arguments.replace('$rompath$', rompath)
    arguments = arguments.replace('$rombase$', rombase)
    arguments = arguments.replace('$rombasenoext$', rombase_noext)
    arguments = arguments.replace('$romtitle$', romtitle)
    arguments = arguments.replace('$apppath$', apppath)
    # >> Legacy names for argument substitution
    arguments = arguments.replace('%rom%', ROMFileName.getPath())
    arguments = arguments.replace('%ROM%', ROMFileName.getPath())
    log_info('_command_run_rom() final arguments "{0}"'.format(arguments))

    # --- Compute ROM recently played list ---
    MAX_RECENT_PLAYED_ROMS = 100
    recent_roms_list = fs_load_Collection_ROMs_JSON(RECENT_PLAYED_FILE_PATH)
    recent_roms_list = [rom for rom in recent_roms_list if rom['id'] != recent_rom['id']]
    recent_roms_list.insert(0, recent_rom)
    if len(recent_roms_list) > MAX_RECENT_PLAYED_ROMS:
        log_debug('_command_run_rom() len(recent_roms_list) = {0}'.format(len(recent_roms_list)))
        log_debug('_command_run_rom() Trimming list to {0} ROMs'.format(MAX_RECENT_PLAYED_ROMS))
        temp_list        = recent_roms_list[:MAX_RECENT_PLAYED_ROMS]
        recent_roms_list = temp_list
    fs_write_Collection_ROMs_JSON(RECENT_PLAYED_FILE_PATH, recent_roms_list)

    # --- Compute most played ROM statistics ---
    most_played_roms = fs_load_Favourites_JSON(MOST_PLAYED_FILE_PATH)
    if recent_rom['id'] in most_played_roms:
        rom_id = recent_rom['id']
        most_played_roms[rom_id]['launch_count'] += 1
    else:
        # >> Add field launch_count to recent_rom to count how many times have been launched.
        recent_rom['launch_count'] = 1
        most_played_roms[recent_rom['id']] = recent_rom
    fs_write_Favourites_JSON(MOST_PLAYED_FILE_PATH, most_played_roms)

    # --- Execute Kodi Retroplayer if launcher configured to do so ---
    # See https://github.com/Wintermute0110/plugin.program.advanced.emulator.launcher/issues/33
    # See https://forum.kodi.tv/showthread.php?tid=295463&pid=2620489#pid2620489
    if application.getOriginalPath() == RETROPLAYER_LAUNCHER_APP_NAME:
        log_info('_command_run_rom() Executing ROM with Kodi Retroplayer ...')
        # >> Create listitem object
        label_str = ROMFileName.getBase()
        listitem = xbmcgui.ListItem(label = label_str, label2 = label_str)
        # >> Listitem metadata
        # >> How to fill gameclient = string (game.libretro.fceumm) ???
        genre_list = list(rom['m_genre'])
        listitem.setInfo('game', {'title'    : label_str,     'platform'  : 'Test platform',
                                  'genres'   : genre_list,    'developer' : rom['m_developer'],
                                  'overview' : rom['m_plot'], 'year'      : rom['m_year'] })
        log_info('_command_run_rom() application.getOriginalPath() "{0}"'.format(application.getOriginalPath()))
        log_info('_command_run_rom() ROMFileName.getPath()         "{0}"'.format(ROMFileName.getPath()))
        log_info('_command_run_rom() label_str                     "{0}"'.format(label_str))

        # --- User notification ---
        if g_settings['display_launcher_notify']:
            kodi_notify('Launching "{0}" with Retroplayer'.format(romtitle))

        log_verb('_command_run_rom() Calling xbmc.Player().play() ...')
        xbmc.Player().play(ROMFileName.getPath(), listitem)
        log_verb('_command_run_rom() Calling xbmc.Player().play() returned. Leaving function.')
    else:
        log_info('_command_run_rom() Launcher is not Kodi Retroplayer.')
        self._run_before_execution(romtitle, minimize_flag)
        self._run_process(application.getPath(), arguments, apppath, romext, non_blocking_flag)
        self._run_after_execution(minimize_flag)

#
# Launchs a ROM launcher or standalone launcher
# For standalone launchers romext is the extension of the application (only used in Windoze)
#
def m_run_process(application, arguments, apppath, romext, non_blocking_flag):
    import shlex
    import subprocess

    # >> Determine platform and launch application
    # >> See http://stackoverflow.com/questions/446209/possible-values-from-sys-platform

    # >> Decompose arguments to call subprocess module
    arg_list  = shlex.split(arguments, posix = True)
    exec_list = [application] + arg_list
    log_debug('_run_process() arguments = "{0}"'.format(arguments))
    log_debug('_run_process() arg_list  = {0}'.format(arg_list))
    log_debug('_run_process() exec_list = {0}'.format(exec_list))

    # >> Windoze
    # NOTE subprocess24_hack.py was hacked to always set CreateProcess() bInheritHandles to 0.
    # bInheritHandles [in] If this parameter TRUE, each inheritable handle in the calling 
    # process is inherited by the new process. If the parameter is FALSE, the handles are not 
    # inherited. Note that inherited handles have the same value and access rights as the original handles.
    # See https://msdn.microsoft.com/en-us/library/windows/desktop/ms682425(v=vs.85).aspx
    #
    # Same behaviour can be achieved in current version of subprocess with close_fds.
    # If close_fds is true, all file descriptors except 0, 1 and 2 will be closed before the 
    # child process is executed. (Unix only). Or, on Windows, if close_fds is true then no handles 
    # will be inherited by the child process. Note that on Windows, you cannot set close_fds to 
    # true and also redirect the standard handles by setting stdin, stdout or stderr.
    #
    # If I keep old launcher behaviour in Windows (close_fds = True) then program output cannot
    # be redirected to a file.
    #
    if sys.platform == 'win32':
        app_ext = application.split('.')[-1]
        log_debug('_run_process() (Windows) application = "{0}"'.format(application))
        log_debug('_run_process() (Windows) arguments   = "{0}"'.format(arguments))
        log_debug('_run_process() (Windows) apppath     = "{0}"'.format(apppath))
        log_debug('_run_process() (Windows) romext      = "{0}"'.format(romext))
        log_debug('_run_process() (Windows) app_ext     = "{0}"'.format(app_ext))
        # >> Standalone launcher where application is a LNK file
        if app_ext == 'lnk' or app_ext == 'LNK':
            log_debug('_run_process() (Windows) Launching LNK application')
            # os.system('start "AEL" /b "{0}"'.format(application).encode('utf-8'))
            retcode = subprocess.call('start "AEL" /b "{0}"'.format(application).encode('utf-8'), shell = True)
            log_info('_run_process() (Windows) LNK app retcode = {0}'.format(retcode))

        # >> ROM launcher where ROMs are LNK files
        elif romext == 'lnk' or romext == 'LNK':
            log_debug('_run_process() (Windows) Launching LNK ROM')
            # os.system('start "AEL" /b "{0}"'.format(arguments).encode('utf-8'))
            retcode = subprocess.call('start "AEL" /b "{0}"'.format(arguments).encode('utf-8'), shell = True)
            log_info('_run_process() (Windows) LNK ROM retcode = {0}'.format(retcode))

        # >> CMD/BAT files in Windows
        elif app_ext == 'bat' or app_ext == 'BAT' or app_ext == 'cmd' or app_ext == 'CMD':
            # --- Workaround to run UNC paths in Windows ---
            # >> Retroarch now support ROMs in UNC paths (Samba remotes)
            new_exec_list = list(exec_list)
            for i, _ in enumerate(exec_list):
                if exec_list[i][0] == '\\':
                    new_exec_list[i] = '\\' + exec_list[i]
                    log_debug('_run_process() (Windows) Before arg #{0} = "{1}"'.format(i, exec_list[i]))
                    log_debug('_run_process() (Windows) Now    arg #{0} = "{1}"'.format(i, new_exec_list[i]))
            exec_list = list(new_exec_list)
            log_debug('_run_process() (Windows) exec_list = {0}'.format(exec_list))
            log_debug('_run_process() (Windows) Launching BAT application')
            log_debug('_run_process() (Windows) Ignoring setting windows_cd_apppath')
            log_debug('_run_process() (Windows) Ignoring setting windows_close_fds')
            log_debug('_run_process() (Windows) show_batch_window = {0}'.format(g_settings['show_batch_window']))
            info = subprocess.STARTUPINFO()
            info.dwFlags = 1
            info.wShowWindow = 5 if g_settings['show_batch_window'] else 0
            retcode = subprocess.call(exec_list, cwd = apppath.encode('utf-8'), close_fds = True, startupinfo = info)
            log_info('_run_process() (Windows) Process BAR retcode = {0}'.format(retcode))

        else:
            # --- Workaround to run UNC paths in Windows ---
            # >> Retroarch now support ROMs in UNC paths (Samba remotes)
            new_exec_list = list(exec_list)
            for i, _ in enumerate(exec_list):
                if exec_list[i][0] == '\\':
                    new_exec_list[i] = '\\' + exec_list[i]
                    log_debug('_run_process() (Windows) Before arg #{0} = "{1}"'.format(i, exec_list[i]))
                    log_debug('_run_process() (Windows) Now    arg #{0} = "{1}"'.format(i, new_exec_list[i]))
            exec_list = list(new_exec_list)
            log_debug('_run_process() (Windows) exec_list = {0}'.format(exec_list))

            # >> cwd = apppath.encode('utf-8') fails if application path has Unicode on Windows
            # >> A workaraound is to use cwd = apppath.encode(sys.getfilesystemencoding()) --> DOES NOT WORK
            # >> For the moment AEL cannot launch executables on Windows having Unicode paths.
            windows_cd_apppath = g_settings['windows_cd_apppath']
            windows_close_fds  = g_settings['windows_close_fds']
            log_debug('_run_process() (Windows) Launching regular application')
            log_debug('_run_process() (Windows) windows_cd_apppath = {0}'.format(windows_cd_apppath))
            log_debug('_run_process() (Windows) windows_close_fds  = {0}'.format(windows_close_fds))
            # >>  Note that on Windows, you cannot set close_fds to true and also redirect the 
            # >> standard handles by setting stdin, stdout or stderr.
            if windows_cd_apppath and windows_close_fds:
                retcode = subprocess.call(exec_list, cwd = apppath.encode('utf-8'), close_fds = True)
            elif windows_cd_apppath and not windows_close_fds:
                with open(LAUNCH_LOG_FILE_PATH.getPath(), 'w') as f:
                    retcode = subprocess.call(exec_list, cwd = apppath.encode('utf-8'), close_fds = False,
                                              stdout = f, stderr = subprocess.STDOUT)
            elif not windows_cd_apppath and windows_close_fds:
                retcode = subprocess.call(exec_list, close_fds = True)
            elif not windows_cd_apppath and not windows_close_fds:
                with open(LAUNCH_LOG_FILE_PATH.getPath(), 'w') as f:
                    retcode = subprocess.call(exec_list, close_fds = False,
                                              stdout = f, stderr = subprocess.STDOUT)
            else:
                raise Exception('Logical error')
            log_info('_run_process() (Windows) Process retcode = {0}'.format(retcode))

    # Android
    elif is_android():
         
        retcode = os.system("{0} {1}".format(application, arguments).encode('utf-8'))
        log_info('_run_process() Process retcode = {0}'.format(retcode))

    # >> Linux
    # >> New in 0.9.7: always close all file descriptions except 0, 1 and 2 on the child
    # >> process. This is to avoid Kodi opens sockets be inherited by the child process. A
    # >> wrapper script may terminate Kodi using JSON RPC and if file descriptors are not
    # >> closed Kodi will complain that the remote interfacte cannot be initialised. I believe
    # >> the cause is that the socket is kept open by the wrapper script.
    elif sys.platform.startswith('linux'):
        # >> Old way of launching child process. os.system() is deprecated and should not
        # >> be used anymore.
        # os.system('"{0}" {1}'.format(application, arguments).encode('utf-8'))

        # >> New way of launching, uses subproces module. Also, save child process stdout.
        if non_blocking_flag:
            # >> In a non-blocking launch stdout/stderr of child process cannot be recorded.
            log_info('_run_process() (Linux) Launching non-blocking process subprocess.Popen()')
            p = subprocess.Popen(exec_list, close_fds = True)
        else:
            if g_settings['lirc_state']: xbmc.executebuiltin('LIRC.stop')
            log_info('_run_process() (Linux) Launching blocking process subprocess.call()')
            with open(LAUNCH_LOG_FILE_PATH.getPath(), 'w') as f:
                retcode = subprocess.call(exec_list, stdout = f, stderr = subprocess.STDOUT, close_fds = True)
            log_info('_run_process() Process retcode = {0}'.format(retcode))
            if g_settings['lirc_state']: xbmc.executebuiltin('LIRC.start')

    # >> OS X
    elif sys.platform.startswith('darwin'):
        # >> Old way
        # os.system('"{0}" {1}'.format(application, arguments).encode('utf-8'))
        
        # >> New way.
        with open(LAUNCH_LOG_FILE_PATH.getPath(), 'w') as f:
            retcode = subprocess.call(exec_list, stdout = f, stderr = subprocess.STDOUT)
        log_info('_run_process() Process retcode = {0}'.format(retcode))

    else:
        kodi_notify_warn('Cannot determine the running platform')

#
# These two functions do things like stopping music before lunch, toggling full screen, etc.
# Variables set in this function:
# self.kodi_was_playing      True if Kodi player was ON, False otherwise
# self.kodi_audio_suspended  True if Kodi audio suspended before launching
#
def m_run_before_execution(rom_title, toggle_screen_flag):
    # --- User notification ---
    if g_settings['display_launcher_notify']:
        kodi_notify('Launching {0}'.format(rom_title))

    # --- Stop/Pause Kodi mediaplayer if requested in settings ---
    self.kodi_was_playing = False
    # id="media_state_action" default="0" values="Stop|Pause|Let Play"
    media_state_action = g_settings['media_state_action']
    media_state_str = ['Stop', 'Pause', 'Let Play'][media_state_action]
    log_verb('_run_before_execution() media_state_action is "{0}" ({1})'.format(media_state_str, media_state_action))
    if media_state_action == 0 and xbmc.Player().isPlaying():
        log_verb('_run_before_execution() Calling xbmc.Player().stop()')
        xbmc.Player().stop()
        xbmc.sleep(100)
        self.kodi_was_playing = True
    elif media_state_action == 1 and xbmc.Player().isPlaying():
        log_verb('_run_before_execution() Calling xbmc.Player().pause()')
        xbmc.Player().pause()
        xbmc.sleep(100)
        self.kodi_was_playing = True

    # --- Force audio suspend if requested in "Settings" --> "Advanced"
    # >> See http://forum.kodi.tv/showthread.php?tid=164522
    self.kodi_audio_suspended = False
    if g_settings['suspend_audio_engine']:
        log_verb('_run_before_execution() Suspending Kodi audio engine')
        xbmc.audioSuspend()
        xbmc.enableNavSounds(False)
        xbmc.sleep(100)
        self.kodi_audio_suspended = True
    else:
        log_verb('_run_before_execution() DO NOT suspend Kodi audio engine')

    # --- Force joystick suspend if requested in "Settings" --> "Advanced"
    # >> See https://forum.kodi.tv/showthread.php?tid=287826&pid=2627128#pid2627128
    # >> See https://forum.kodi.tv/showthread.php?tid=157499&pid=1722549&highlight=input.enablejoystick#pid1722549
    # >> See https://forum.kodi.tv/showthread.php?tid=313615
    self.kodi_joystick_suspended = False
    # if g_settings['suspend_joystick_engine']:
        # log_verb('_run_before_execution() Suspending Kodi joystick engine')
        # >> Research. Get the value of the setting first
        # >> Apparently input.enablejoystick is not supported on Kodi Krypton anymore.
        # c_str = ('{"id" : 1, "jsonrpc" : "2.0",'
        #          ' "method" : "Settings.GetSettingValue",'
        #          ' "params" : {"setting":"input.enablejoystick"}}')
        # response = xbmc.executeJSONRPC(c_str)
        # log_debug('JSON      ''{0}'''.format(c_str))
        # log_debug('Response  ''{0}'''.format(response))

    log_info('_command_run_rom() Launching ROM in Launcher ...')

    launcher = g_LauncherRepository.find(launcherID)

    # --- Check launcher is OK ---
    if launcher is None:
        kodi_dialog_OK('Could not start launcher. Check the logs')
        return

    rom = launcher.select_rom(romID)
   
    if rom is None:
        kodi_dialog_OK('Could not load rom. Check the logs')
        return
    launcher.launch()

#
# Check if Launcher reports must be created/regenrated
#
def m_roms_regenerate_launcher_reports(categoryID, launcherID, roms):
    category = self.category_repository.find(categoryID)
    launcher = g_LauncherRepository.find(launcherID)

    # --- Get report filename ---
    roms_base_noext  = fs_get_ROMs_basename(category.get_name(), launcher.get_name(), launcherID)
    report_stats_FN  = REPORTS_DIR.pjoin(roms_base_noext + '_stats.txt')
    log_verb('_command_view_menu() Stats  OP "{0}"'.format(report_stats_FN.getOriginalPath()))

    # --- If report doesn't exists create it automatically ---
    log_debug('_command_view_Launcher_Report() Testing report file "{0}"'.format(report_stats_FN.getPath()))
    if not report_stats_FN.exists():
        kodi_dialog_OK('Report file not found. Will be generated now.')
        self._roms_create_launcher_reports(category, launcher, roms)
        
        # >> Update report timestamp
        launcher.update_report_timestamp()

        # >> Save Categories/Launchers
        # >> DO NOT update the timestamp of categories/launchers of report will always be obsolete!!!
        # >> Keep same timestamp as before
        g_LauncherRepository.save(launcher, False)

    # --- If report timestamp is older than launchers last modification, recreate it ---
    if launcher.get_report_timestamp() <= launcher.get_timestamp():
        kodi_dialog_OK('Report is outdated. Will be regenerated now.')
        self._roms_create_launcher_reports(category, launcher, roms)
        
        launcher.update_report_timestamp()
        g_LauncherRepository.save(launcher)

#
# Creates a Launcher report having:
#  1) Launcher statistics
#  2) Report of ROM metadata
#  3) Report of ROM artwork
#  4) If No-Intro file, then No-Intro audit information.
#
def m_roms_create_launcher_reports(category, launcher, roms):
    ROM_NAME_LENGHT = 50

    # >> Report file name
    category_name = category.get_name() if category is not None else VCATEGORY_ADDONROOT_ID

    roms_base_noext  = fs_get_ROMs_basename(category_name, launcher.get_name(), launcher.get_id())
    report_stats_FN  = REPORTS_DIR.pjoin(roms_base_noext + '_stats.txt')
    report_meta_FN   = REPORTS_DIR.pjoin(roms_base_noext + '_metadata.txt')
    report_assets_FN = REPORTS_DIR.pjoin(roms_base_noext + '_assets.txt')
    log_verb('_roms_create_launcher_reports() Stats  OP "{0}"'.format(report_stats_FN.getOriginalPath()))
    log_verb('_roms_create_launcher_reports() Meta   OP "{0}"'.format(report_meta_FN.getOriginalPath()))
    log_verb('_roms_create_launcher_reports() Assets OP "{0}"'.format(report_assets_FN.getOriginalPath()))
    roms_base_noext = fs_get_ROMs_basename(category_name, launcher.get_name(), launcher.get_id())
    report_file_name = REPORTS_DIR.pjoin(roms_base_noext + '.txt')
    log_verb('_roms_create_launcher_reports() Report filename "{0}"'.format(report_file_name.getOriginalPath()))

    # >> Step 1: Build report data
    num_roms = len(roms)
    missing_m_year      = missing_m_genre    = missing_m_developer = missing_m_nplayers  = 0
    missing_m_esrb      = missing_m_rating   = missing_m_plot      = 0
    audit_none = audit_have = audit_miss = audit_unknown = 0
    audit_num_parents = audit_num_clones = 0
    check_list = []
    
    asset_kinds = self.assetFactory.get_asset_kinds_for_roms()
    missing_assets = { asset.key: 0 for (asset) in asset_kinds }

    for rom in sorted(roms, key = lambda r : r.get_name()):
        rom_info = {}
        rom_info['m_name']           = rom.get_name()
        rom_info['m_nointro_status'] = rom.get_nointro_status()
        rom_info['m_pclone_status']  = rom.get_pclone_status()
        # --- Metadata ---
        if rom.get_releaseyear():                 rom_info['m_year']      = 'YES'
        else:                                     rom_info['m_year']      = '---'; missing_m_year += 1
        if rom.get_genre():                       rom_info['m_genre']     = 'YES'
        else:                                     rom_info['m_genre']     = '---'; missing_m_genre += 1
        if rom.get_developer():                   rom_info['m_developer'] = 'YES'
        else:                                     rom_info['m_developer'] = '---'; missing_m_developer += 1
        if rom.get_number_of_players():           rom_info['m_nplayers']  = 'YES'
        else:                                     rom_info['m_nplayers']  = '---'; missing_m_nplayers += 1
        if rom.get_esrb_rating() == ESRB_PENDING: rom_info['m_esrb']      = '---'; missing_m_esrb += 1
        else:                                     rom_info['m_studio']    = 'YES'
        if rom.get_rating():                      rom_info['m_rating']    = 'YES'
        else:                                     rom_info['m_rating']    = '---'; missing_m_rating += 1
        if rom.get_plot():                        rom_info['m_plot']      = 'YES'
        else:                                     rom_info['m_plot']      = '---'; missing_m_plot += 1
        # --- Assets ---
        # >> Y means the asset exists and has the Base_noext of the ROM.
        # >> S means the asset exists and is a PClone group substitution.
        # >> C means the asset exists and is a user customised asset.
        # >> X means the asset exists, getDir() is same but Base_noext() is different
        # path_* and art getDir() different ==> Custom asset (user customised it) C
        # path_* and art getDir() equal and Base_noext() equal ==> Own artwork Y
        # path_* and art getDir() equal and Base_noext() different ==> Maybe S or maybe C => O
        # To differentiate between S and C a test in the PClone group must be done.
        #
        romfile_FN = rom.get_file()
        romfile_getBase_noext = romfile_FN.getBase_noext()

        for asset_kind in asset_kinds:
            if rom.has_asset(asset_kind):
                rom_info[asset_kind.key] = self._aux_get_info(rom.get_asset_file(asset_kind), launcher.get_asset_path(asset_kind).getPath(), romfile_getBase_noext)
            else:
                rom_info[asset_kind.key] = '-'
                missing_assets[asset_kind.key] = missing_assets[asset_kind.key] + 1

        # --- ROM audit ---
        if   rom.get_nointro_status() == NOINTRO_STATUS_NONE:    audit_none += 1
        elif rom.get_nointro_status() == NOINTRO_STATUS_HAVE:    audit_have += 1
        elif rom.get_nointro_status() == NOINTRO_STATUS_MISS:    audit_miss += 1
        elif rom.get_nointro_status() == NOINTRO_STATUS_UNKNOWN: audit_unknown += 1
        else:
            log_error('Unknown audit status {0}.'.format(rom.get_nointro_status()))
            kodi_dialog_OK('Unknown audit status {0}. This is a bug, please report it.'.format(rom.get_nointro_status()))
            return
        if   rom.get_pclone_status() == PCLONE_STATUS_PARENT: audit_num_parents += 1
        elif rom.get_pclone_status() == PCLONE_STATUS_CLONE:  audit_num_clones += 1
        elif rom.get_pclone_status() == PCLONE_STATUS_NONE:   pass
        else:
            log_error('Unknown pclone status {0}.'.format(rom.get_pclone_status()))
            kodi_dialog_OK('Unknown pclone status {0}. This is a bug, please report it.'.format(rom.get_pclone_status()))
            return

        # >> Add to list
        check_list.append(rom_info)

    # >> Math
    have_m_year = num_roms - missing_m_year
    have_m_genre = num_roms - missing_m_genre
    have_m_developer = num_roms - missing_m_developer
    have_m_nplayers = num_roms - missing_m_nplayers
    have_m_esrb = num_roms - missing_m_esrb
    have_m_rating = num_roms - missing_m_rating
    have_m_plot = num_roms - missing_m_plot

    have_s_year_pcent = float(have_m_year*100) / num_roms
    have_s_genre_pcent = float(have_m_genre*100) / num_roms
    have_s_developer_pcent = float(have_m_developer*100) / num_roms
    have_s_nplayers_pcent = float(have_m_nplayers*100) / num_roms
    have_s_esrb_pcent = float(have_m_esrb*100) / num_roms
    have_s_rating_pcent = float(have_m_rating*100) / num_roms
    have_s_plot_pcent = float(have_m_plot*100) / num_roms

    miss_s_year_pcent = float(missing_m_year*100) / num_roms
    miss_s_genre_pcent = float(missing_m_genre*100) / num_roms
    miss_s_developer_pcent = float(missing_m_developer*100) / num_roms
    miss_s_nplayers_pcent = float(missing_m_nplayers*100) / num_roms
    miss_s_esrb_pcent = float(missing_m_esrb*100) / num_roms
    miss_s_rating_pcent = float(missing_m_rating*100) / num_roms
    miss_s_plot_pcent = float(missing_m_plot*100) / num_roms
            
    # --- Step 2: Statistics report ---
    # >> Launcher name printed on window title
    # >> Audit statistics
    str_list = []
    str_list.append('<No-Intro Audit Statistics>\n')
    str_list.append('Number of ROMs   {0:5d}\n'.format(num_roms))
    str_list.append('Not checked ROMs {0:5d}\n'.format(audit_none))
    str_list.append('Have ROMs        {0:5d}\n'.format(audit_have))
    str_list.append('Missing ROMs     {0:5d}\n'.format(audit_miss))
    str_list.append('Unknown ROMs     {0:5d}\n'.format(audit_unknown))
    str_list.append('Parent           {0:5d}\n'.format(audit_num_parents))
    str_list.append('Clones           {0:5d}\n'.format(audit_num_clones))
   
   # >> Metadata
    str_list.append('\n<Metadata statistics>\n')
    str_list.append('Year      {0:5d} have / {1:5d} miss  ({2:5.1f}%, {3:5.1f}%)\n'.format(
        have_m_year, missing_m_year, have_s_year_pcent, miss_s_year_pcent))
    str_list.append('Genre     {0:5d} have / {1:5d} miss  ({2:5.1f}%, {3:5.1f}%)\n'.format(
        have_m_genre, missing_m_genre, have_s_genre_pcent, miss_s_genre_pcent))
    str_list.append('Developer {0:5d} have / {1:5d} miss  ({2:5.1f}%, {3:5.1f}%)\n'.format(
        have_m_developer, missing_m_developer, have_s_developer_pcent, miss_s_developer_pcent))
    str_list.append('NPlayers  {0:5d} have / {1:5d} miss  ({2:5.1f}%, {3:5.1f}%)\n'.format(
        have_m_nplayers, missing_m_nplayers, have_s_nplayers_pcent, miss_s_nplayers_pcent))
    str_list.append('ESRB      {0:5d} have / {1:5d} miss  ({2:5.1f}%, {3:5.1f}%)\n'.format(
        have_m_esrb, missing_m_esrb, have_s_esrb_pcent, miss_s_esrb_pcent))
    str_list.append('Rating    {0:5d} have / {1:5d} miss  ({2:5.1f}%, {3:5.1f}%)\n'.format(
        have_m_rating, missing_m_rating, have_s_rating_pcent, miss_s_rating_pcent))
    str_list.append('Plot      {0:5d} have / {1:5d} miss  ({2:5.1f}%, {3:5.1f}%)\n'.format(
        have_m_plot, missing_m_plot, have_s_plot_pcent, miss_s_plot_pcent))
    
    # >> Assets statistics
    str_list.append('\n<Asset statistics>\n')
    for asset_kind in asset_kinds:
        miss_of_kind        = missing_assets[asset_kind.key]
        miss_of_kind_pcent  = float(miss_of_kind*100) / num_roms
        has_of_kind         = num_roms - miss_of_kind
        has_of_kind_pcent   = float(has_of_kind*100)  / num_roms

        str_list.append('{0}     {1:5d} have / {2:5d} miss  ({3:5.1f}%, {4:5.1f}%)\n'.format(
            asset_kind.name, has_of_kind, miss_of_kind, has_of_kind_pcent, miss_of_kind_pcent))
    
    # >> Step 3: Metadata report
    str_meta_list = []
    str_meta_list.append('{0} Year Genre Developer Rating Plot Audit    PClone\n'.format('Name'.ljust(ROM_NAME_LENGHT)))
    str_meta_list.append('{0}\n'.format('-' * 99))
    for m in check_list:
        # >> Limit ROM name string length
        name_str = text_limit_string(m['m_name'], ROM_NAME_LENGHT)
        str_meta_list.append('{0} {1}  {2}   {3}       {4}    {5}  {6:<7}  {7}\n'.format(
                        name_str.ljust(ROM_NAME_LENGHT),
                        m['m_year'], m['m_genre'], m['m_developer'],
                        m['m_rating'], m['m_plot'], m['m_nointro_status'], m['m_pclone_status']))

    # >> Step 4: Asset report
    str_asset_list = []
    str_asset_list.append('{0} Tit Sna Fan Ban Clr Bxf Bxb Car Fly Map Man Tra\n'.format('Name'.ljust(ROM_NAME_LENGHT)))
    str_asset_list.append('{0}\n'.format('-' * 98))
    for m in check_list:
        # >> Limit ROM name string length
        name_str = text_limit_string(m['m_name'], ROM_NAME_LENGHT)
        str_asset_list.append('{0}  {1}   {2}   {3}   {4}   {5}   {6}   {7}   {8}   {9}   {10}   {11}   {12}\n'.format(
                        name_str.ljust(ROM_NAME_LENGHT),
                        m['s_title'],     m['s_snap'],     m['s_fanart'],  m['s_banner'],
                        m['s_clearlogo'], m['s_boxfront'], m['s_boxback'], m['s_cartridge'],
                        m['s_flyer'],     m['s_map'],      m['s_manual'],  m['s_trailer']))

    # >> Step 5: Join string and write TXT reports
    try:
        # >> Stats report
        full_string = ''.join(str_list).encode('utf-8')
        file = open(report_stats_FN.getPath(), 'w')
        file.write(full_string)
        file.close()

        # >> Metadata report
        full_string = ''.join(str_meta_list).encode('utf-8')
        file = open(report_meta_FN.getPath(), 'w')
        file.write(full_string)
        file.close()

        # >> Asset report
        full_string = ''.join(str_asset_list).encode('utf-8')
        file = open(report_assets_FN.getPath(), 'w')
        file.write(full_string)
        file.close()
    except OSError:
        log_error('Cannot write Launcher Report file (OSError)')
        kodi_notify_warn('Cannot write Launcher Report (OSError)')
    except IOError:
        log_error('Cannot write categories.xml file (IOError)')
        kodi_notify_warn('Cannot write Launcher Report (IOError)')

def m_aux_get_info(asset_FN, path_asset_P, romfile_getBase_noext):
    # log_debug('title_FN.getDir() "{0}"'.format(title_FN.getDir()))
    # log_debug('path_title_P      "{0}"'.format(path_title_P))
    if path_asset_P != asset_FN.getDir():
        ret_str = 'C'
    else:
        if romfile_getBase_noext == asset_FN.getBase_noext():
            ret_str = 'Y'
        else:
            ret_str = 'O'

    return ret_str

#
# Manually add a new ROM instead of a recursive scan.
#   A) User chooses a ROM file
#   B) Title is formatted. No metadata scraping.
#   C) Thumb and fanart are searched locally only.
# Later user can edit this ROM if he wants.
#
def m_roms_add_new_rom(launcherID):
    
    # --- Grab launcher information ---
    launcher = g_LauncherRepository.find(launcherID)
    
    if not launcher.supports_launching_roms():
        kodi_notify_warn('Cannot add new roms if launcher does not support roms.')
        return

    romext   = launcher.get_rom_extensions_combined()
    rompath  = launcher.get_rom_path()
    log_verb('_roms_add_new_rom() launcher name "{0}"'.format(launcher.get_name()))

    # --- Load ROMs for this launcher ---
    roms = launcher.get_roms()

    # --- Choose ROM file ---
    dialog = xbmcgui.Dialog()
    extensions = '.' + romext.replace('|', '|.')
    romfile = dialog.browse(1, 'Select the ROM file', 'files', extensions, False, False, rompath.getPath()).decode('utf-8')
    if not romfile: return
    log_verb('_roms_add_new_rom() romfile "{0}"'.format(romfile))

    # --- Format title ---
    scan_clean_tags = g_settings['scan_clean_tags']
    ROMFile = FileNameFactory.create(romfile)
    rom_name = text_format_ROM_title(ROMFile.getBase_noext(), scan_clean_tags)

    # ~~~ Check asset dirs and disable scanning for unset dirs ~~~
    # >> Do not warn about unconfigured dirs here
    (enabled_asset_list, unconfigured_name_list) = asset_get_configured_dir_list(launcher)

    # ~~~ Ensure there is no duplicate asset dirs ~~~
    duplicated_name_list = asset_get_duplicated_dir_list(launcher.get_data())
    if duplicated_name_list:
        duplicated_asset_srt = ', '.join(duplicated_name_list)
        log_debug('_roms_add_new_rom() Duplicated asset dirs: {0}'.format(duplicated_asset_srt))
        kodi_dialog_OK('Duplicated asset directories: {0}. '.format(duplicated_asset_srt) +
                       'Change asset directories before continuing.')
        return
    else:
        log_debug('_roms_add_new_rom() No duplicated asset dirs found')

    # ~~~ Search for local artwork/assets ~~~
    local_asset_list = assets_search_local_assets(launcher.get_data(), ROMFile, enabled_asset_list)

    # --- Create ROM data structure ---
    rom = Rom()
    rom.set_file(ROMFile)
    rom.set_name(rom_name)

    rom_assets = self.assetFactory.get_asset_kinds_for_roms()
    for index, asset in rom_assets:
        rom.set_asset(asset, local_asset_list[index])

    romdata = rom.get_data()
    log_info('_roms_add_new_rom() Added a new ROM')
    log_info('_roms_add_new_rom() romID       "{0}"'.format(romdata['id']))
    log_info('_roms_add_new_rom() filename    "{0}"'.format(romdata['filename']))
    log_info('_roms_add_new_rom() m_name      "{0}"'.format(romdata['m_name']))
    log_verb('_roms_add_new_rom() s_title     "{0}"'.format(romdata['s_title']))
    log_verb('_roms_add_new_rom() s_snap      "{0}"'.format(romdata['s_snap']))
    log_verb('_roms_add_new_rom() s_fanart    "{0}"'.format(romdata['s_fanart']))
    log_verb('_roms_add_new_rom() s_banner    "{0}"'.format(romdata['s_banner']))
    log_verb('_roms_add_new_rom() s_clearlogo "{0}"'.format(romdata['s_clearlogo']))
    log_verb('_roms_add_new_rom() s_boxfront  "{0}"'.format(romdata['s_boxfront']))
    log_verb('_roms_add_new_rom() s_boxback   "{0}"'.format(romdata['s_boxback']))
    log_verb('_roms_add_new_rom() s_cartridge "{0}"'.format(romdata['s_cartridge']))
    log_verb('_roms_add_new_rom() s_flyer     "{0}"'.format(romdata['s_flyer']))
    log_verb('_roms_add_new_rom() s_map       "{0}"'.format(romdata['s_map']))
    log_verb('_roms_add_new_rom() s_manual    "{0}"'.format(romdata['s_manual']))
    log_verb('_roms_add_new_rom() s_trailer   "{0}"'.format(romdata['s_trailer']))

    # --- If there is a No-Intro XML configured audit ROMs ---
    if launcher.has_nointro_xml():
        log_info('No-Intro/Redump DAT configured. Starting ROM audit ...')
        nointro_xml_FN = launcher.get_nointro_xml_filepath()
        if not self._roms_update_NoIntro_status(launcher.get_data(), roms, nointro_xml_FN):
            launcher.reset_nointro_xmldata()
            kodi_dialog_OK('Error auditing ROMs. XML DAT file unset.')
    else:
        log_info('No No-Intro/Redump DAT configured. Do not audit ROMs.')

    # ~~~ Save ROMs XML file ~~~
    # >> Also save categories/launchers to update timestamp
    self.launcher.save_rom(rom)

    launcher.set_number_of_roms()
    g_LauncherRepository.save(launcher)

    kodi_refresh_container()
    kodi_notify('Added ROM. Launcher has now {0} ROMs'.format(self.launcher.get_number_of_roms()))

#
# ROM scanner. Called when user chooses Launcher CM, "Add ROMs" -> "Scan for new ROMs"
#
def m_roms_import_roms(launcherID):
    log_debug('========== _roms_import_roms() BEGIN ==================================================')

    # --- Get information from launcher ---
    launcher           = self.launchers[launcherID]
    launcher_path      = FileName(launcher['rompath'])
    launcher_exts      = launcher['romext']
    launcher_multidisc = launcher['multidisc']
    log_info('_roms_import_roms() Starting ROM scanner ...')
    log_info('Launcher name "{0}"'.format(launcher['m_name']))
    log_info('launcher ID   "{0}"'.format(launcher['id']))
    log_info('ROM path      "{0}"'.format(launcher_path.getPath()))
    log_info('ROM exts      "{0}"'.format(launcher_exts))
    log_info('Multidisc     {0}'.format(launcher_multidisc))
    log_info('Platform      "{0}"'.format(launcher['platform']))

    # --- Open ROM scanner report file ---
    launcher_report_FN = REPORTS_DIR.pjoin(launcher['roms_base_noext'] + '_report.txt')
    log_info('Report file OP "{0}"'.format(launcher_report_FN.getOriginalPath()))
    log_info('Report file  P "{0}"'.format(launcher_report_FN.getPath()))
    report_fobj = open(launcher_report_FN.getPath(), "w")
    report_fobj.write('*** Starting ROM scanner ... ***\n'.format())
    report_fobj.write('  Launcher name "{0}"\n'.format(launcher['m_name']))
    report_fobj.write('  launcher ID   "{0}"\n'.format(launcher['id']))
    report_fobj.write('  ROM path      "{0}"\n'.format(launcher_path.getPath()))
    report_fobj.write('  ROM ext       "{0}"\n'.format(launcher_exts))
    report_fobj.write('  Platform      "{0}"\n'.format(launcher['platform']))

    # >> Check if there is an XML for this launcher. If so, load it.
    # >> If file does not exist or is empty then return an empty dictionary.
    report_fobj.write('Loading launcher ROMs ...\n')
    roms = fs_load_ROMs_JSON(ROMS_DIR, launcher)
    num_roms = len(roms)
    report_fobj.write('{0} ROMs currently in database\n'.format(num_roms))
    log_info('Launcher ROM database contain {0} items'.format(num_roms))

    # --- Load metadata/asset scrapers --------------------------------------------------------
    # >> Create a dictionary with references to the asset srapers
    self.scraper_dic = {}

    # >> Scrapers for MAME platform are different than rest of the platforms
    if launcher['platform'] == 'MAME':
        # --- Metadata scraper ---
        # Scraper objects are created and inserted into a list. This list order matches
        # exactly the number returned by the settings. If scrapers are changed make sure the
        # list in scrapers.py and in settings.xml have same values!
        self.scraper_data = scrapers_metadata_MAME[g_settings['scraper_metadata_MAME']]
        self.scraper_data.set_addon_dir(g_PATHS.ADDON_CODE_DIR.getPath())
        log_verb('Loaded metadata MAME scraper "{0}"'.format(self.scraper_data.name))

        # --- Asset scrapers ---
        A = assets_get_info_scheme(ASSET_TITLE)
        self.scraper_dic[A.key] = scrapers_title_MAME[g_settings['scraper_title_MAME']]
        log_verb('Loaded {0:<10} MAME scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

        A = assets_get_info_scheme(ASSET_SNAP)
        self.scraper_dic[A.key] = scrapers_snap_MAME[g_settings['scraper_snap_MAME']]
        log_verb('Loaded {0:<10} MAME scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

        # >> Boxfront -> Cabinet
        A = assets_get_info_scheme(ASSET_BOXFRONT)
        self.scraper_dic[A.key] = scrapers_cabinet_MAME[g_settings['scraper_cabinet_MAME']]
        log_verb('Loaded {0:<10} MAME scraper "{1}" (MAME Cabinets)'.format(A.name, self.scraper_dic[A.key].name))

        # >> Boxback -> Control Panel
        A = assets_get_info_scheme(ASSET_BOXBACK)
        self.scraper_dic[A.key] = scrapers_cpanel_MAME[g_settings['scraper_cpanel_MAME']]
        log_verb('Loaded {0:<10} MAME scraper "{1}" (MAME CPanels)'.format(A.name, self.scraper_dic[A.key].name))

        # >> Cartridge -> PCB
        A = assets_get_info_scheme(ASSET_CARTRIDGE)
        self.scraper_dic[A.key] = scrapers_pcb_MAME[g_settings['scraper_pcb_MAME']]
        log_verb('Loaded {0:<10} MAME scraper "{1}" (MAME PCBs)'.format(A.name, self.scraper_dic[A.key].name))

        A = assets_get_info_scheme(ASSET_FANART)
        self.scraper_dic[A.key] = scrapers_fanart_MAME[g_settings['scraper_fanart_MAME']]
        log_verb('Loaded {0:<10} MAME scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

        # >> Banner -> Marquee
        A = assets_get_info_scheme(ASSET_BANNER)
        self.scraper_dic[A.key] = scrapers_marquee_MAME[g_settings['scraper_marquee_MAME']]
        log_verb('Loaded {0:<10} MAME scraper "{1}" (MAME Marquees)'.format(A.name, self.scraper_dic[A.key].name))

        A = assets_get_info_scheme(ASSET_CLEARLOGO)
        self.scraper_dic[A.key] = scrapers_clearlogo_MAME[g_settings['scraper_clearlogo_MAME']]
        log_verb('Loaded {0:<10} MAME scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

        A = assets_get_info_scheme(ASSET_FLYER)
        self.scraper_dic[A.key] = scrapers_flyer_MAME[g_settings['scraper_flyer_MAME']]
        log_verb('Loaded {0:<10} MAME scraper "{1}" (MAME flyers)'.format(A.name, self.scraper_dic[A.key].name))

        # >> Map (not supported yet, use a null scraper)
        A = assets_get_info_scheme(ASSET_MAP)
        self.scraper_dic[A.key] = NULL_obj
        log_verb('Loaded {0:<10} MAME scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

        # >> Manual (not supported yet, use a null scraper)
        A = assets_get_info_scheme(ASSET_MANUAL)
        self.scraper_dic[A.key] = NULL_obj
        log_verb('Loaded {0:<10} MAME scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

        # >> Trailer (not supported yet, use a null scraper)
        A = assets_get_info_scheme(ASSET_TRAILER)
        self.scraper_dic[A.key] = NULL_obj
        log_verb('Loaded {0:<10} MAME scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

    else:
        # --- Metadata scraper ---
        self.scraper_data = scrapers_metadata[g_settings['scraper_metadata']]
        self.scraper_data.set_addon_dir(g_PATHS.ADDON_CODE_DIR.getPath())
        log_verb('Loaded metadata scraper "{0}"'.format(self.scraper_data.name))

        # --- Asset scrapers ---
        A = assets_get_info_scheme(ASSET_TITLE)
        self.scraper_dic[A.key] = scrapers_title[g_settings['scraper_title']]
        log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

        A = assets_get_info_scheme(ASSET_SNAP)
        self.scraper_dic[A.key] = scrapers_snap[g_settings['scraper_snap']]
        log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

        A = assets_get_info_scheme(ASSET_BOXFRONT)
        self.scraper_dic[A.key] = scrapers_boxfront[g_settings['scraper_boxfront']]
        log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

        A = assets_get_info_scheme(ASSET_BOXBACK)
        self.scraper_dic[A.key] = scrapers_boxback[g_settings['scraper_boxback']]
        log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

        A = assets_get_info_scheme(ASSET_CARTRIDGE)
        self.scraper_dic[A.key] = scrapers_cartridge[g_settings['scraper_cart']]
        log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

        A = assets_get_info_scheme(ASSET_FANART)
        self.scraper_dic[A.key] = scrapers_fanart[g_settings['scraper_fanart']]
        log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

        A = assets_get_info_scheme(ASSET_BANNER)
        self.scraper_dic[A.key] = scrapers_banner[g_settings['scraper_banner']]
        log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

        A = assets_get_info_scheme(ASSET_CLEARLOGO)
        self.scraper_dic[A.key] = scrapers_clearlogo[g_settings['scraper_clearlogo']]
        log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

        # >> Flyers only supported by ArcadeDB (for MAME). If platform is not MAME then deactivate
        # >> this scraper.
        A = assets_get_info_scheme(ASSET_FLYER)
        self.scraper_dic[A.key] = NULL_obj
        log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

        # >> Map (not supported yet, use a null scraper)
        A = assets_get_info_scheme(ASSET_MAP)
        self.scraper_dic[A.key] = NULL_obj
        log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

        # >> Manual (not supported yet, use a null scraper)
        A = assets_get_info_scheme(ASSET_MANUAL)
        self.scraper_dic[A.key] = NULL_obj
        log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

        # >> Trailer (not supported yet, use a null scraper)
        A = assets_get_info_scheme(ASSET_TRAILER)
        self.scraper_dic[A.key] = NULL_obj
        log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

    # >> Initialise options of the thumb scraper (NOT SUPPORTED YET)
    # region = g_settings['scraper_region']
    # thumb_imgsize = g_settings['scraper_thumb_size']
    # self.scraper_asset.set_options(region, thumb_imgsize)

    # --- Initialise cache used in _roms_scrap_asset() ---
    # >> This cache is used to store the selected game from the get_search() returned list.
    # >> The idea is that get_search() is used only once for each asset.
    self.scrap_asset_cached_dic = {}

    # --- Assets/artwork stuff ----------------------------------------------------------------
    # ~~~ Check asset dirs and disable scanning for unset dirs ~~~
    log_info('Checking for unset artwork directories ...')
    (self.enabled_asset_list, unconfigured_name_list) = asset_get_configured_dir_list(launcher)
    if unconfigured_name_list:
        unconfigured_asset_srt = ', '.join(unconfigured_name_list)
        kodi_dialog_OK('Assets directories not set: {0}. '.format(unconfigured_asset_srt) +
                       'Asset scanner will be disabled for this/those.')

    # ~~~ Ensure there is no duplicate asset dirs ~~~
    # >> Abort scanning of assets if duplicates found
    log_info('Checking for duplicated artwork directories ...')
    duplicated_name_list = asset_get_duplicated_dir_list(launcher)
    if duplicated_name_list:
        duplicated_asset_srt = ', '.join(duplicated_name_list)
        log_info('Duplicated asset dirs: {0}'.format(duplicated_asset_srt))
        kodi_dialog_OK('Duplicated asset directories: {0}. '.format(duplicated_asset_srt) +
                       'Change asset directories before continuing.')
        return
    else:
        log_info('No duplicated asset dirs found')

    # --- Progress dialog ---
    # >> Put in in object variables so it can be access in helper functions.
    self.pDialog_verbose = True
    self.pDialog_canceled = False
    self.pDialog = xbmcgui.DialogProgress()

    # --- Create a cache of assets ---
    # >> misc_add_file_cache() creates a set with all files in a given directory.
    # >> That set is stored in a function internal cache associated with the path.
    # >> Files in the cache can be searched with misc_search_file_cache()
    log_info('Scanning and caching files in asset directories ...')
    self.pDialog.create('Advanced Emulator Launcher', 'Scanning files in asset directories ...')
    for i, asset_kind in enumerate(ROM_ASSET_LIST):
        AInfo = assets_get_info_scheme(asset_kind)
        misc_add_file_cache(launcher[AInfo.path_key])
        self.pDialog.update((100*i)/len(ROM_ASSET_LIST))
    self.pDialog.update(100)
    self.pDialog.close()

    # --- Remove dead entries -----------------------------------------------------------------
    log_info('Removing dead ROMs ...'.format())
    report_fobj.write('Removing dead ROMs ...\n')
    num_removed_roms = 0
    if num_roms > 0:
        self.pDialog.create('Advanced Emulator Launcher', 'Checking for dead ROMs ...')
        i = 0
        for key in sorted(roms.iterkeys()):
            log_debug('Searching {0}'.format(roms[key]['filename']))
            self.pDialog.update(i * 100 / num_roms)
            i += 1
            fileName = FileName(roms[key]['filename'])
            if not fileName.exists():
                log_debug('Not found')
                log_debug('Deleting from DB {0}'.format(roms[key]['filename']))
                del roms[key]
                num_removed_roms += 1
        self.pDialog.update(i * 100 / num_roms)
        self.pDialog.close()
        if num_removed_roms > 0:
            kodi_notify('{0} dead ROMs removed successfully'.format(num_removed_roms))
            log_info('{0} dead ROMs removed successfully'.format(num_removed_roms))
        else:
            log_info('No dead ROMs found')
    else:
        log_info('Launcher is empty. No dead ROM check.')

    # ~~~ Scan all files in ROMpath (mask *.*) and put them in a list ~~~~~~~~~~~~~~~~~~~~~~~~~
    self.pDialog.create('Advanced Emulator Launcher', 'Scanning and caching files in ROM path ...')
    files = []
    log_info('Scanning files in {0}'.format(launcher_path.getPath()))
    report_fobj.write('Scanning files ...\n')
    report_fobj.write('  Directory {0}\n'.format(launcher_path.getPath()))
    if g_settings['scan_recursive']:
        log_info('Recursive scan activated')
        files = launcher_path.recursiveScanFilesInPath('*.*')
    else:
        log_info('Recursive scan not activated')
        files = launcher_path.scanFilesInPath('*.*')
    num_files = len(files)
    log_info('File scanner found {0} files'.format(num_files))
    report_fobj.write('  File scanner found {0} files\n'.format(num_files))
    self.pDialog.update(100)
    self.pDialog.close()

    # ~~~ Now go processing file by file ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    self.pDialog.create('Advanced Emulator Launcher', 'Scanning {0}'.format(launcher_path))
    log_debug('============================== Processing ROMs ==============================')
    report_fobj.write('Processing files ...\n')
    num_new_roms = 0
    num_files_checked = 0
    for f_path in sorted(files):
        # --- Get all file name combinations ---
        ROM = FileName(f_path)
        log_debug('---------- Processing cached file ----------')
        log_debug('ROM.getPath()         "{0}"'.format(ROM.getPath()))
        log_debug('ROM.getOriginalPath() "{0}"'.format(ROM.getOriginalPath()))
        # log_debug('ROM.getPath_noext()   "{0}"'.format(ROM.getPath_noext()))
        # log_debug('ROM.getDir()          "{0}"'.format(ROM.getDir()))
        # log_debug('ROM.getBase()         "{0}"'.format(ROM.getBase()))
        # log_debug('ROM.getBase_noext()   "{0}"'.format(ROM.getBase_noext()))
        # log_debug('ROM.getExt()          "{0}"'.format(ROM.getExt()))
        report_fobj.write('>>> {0}\n'.format(ROM.getPath()).encode('utf-8'))

        # ~~~ Update progress dialog ~~~
        self.progress_number = num_files_checked * 100 / num_files
        self.file_text = 'ROM {0}'.format(ROM.getBase())
        if not self.pDialog_verbose:
            self.pDialog.update(self.progress_number, self.file_text)
        else:
            activity_text = 'Checking if has ROM extension ...'
            self.pDialog.update(self.progress_number, self.file_text, activity_text)
        num_files_checked += 1

        # --- Check if filename matchs ROM extensions ---
        # The recursive scan has scanned all files. Check if this file matches some of 
        # the ROM extensions. If this file isn't a ROM skip it and go for next one in the list.
        processROM = False
        for ext in launcher_exts.split("|"):
            if ROM.getExt() == '.' + ext:
                log_debug("Expected '{0}' extension detected".format(ext))
                report_fobj.write("  Expected '{0}' extension detected\n".format(ext))
                processROM = True
        if not processROM: 
            log_debug('File has not an expected extension. Skipping file.')
            report_fobj.write('  File has not an expected extension. Skipping file.\n')
            continue

    log_debug('========== _roms_import_roms() BEGIN ==================================================')
    launcher = g_LauncherRepository.find(launcherID)
    
    scrapers   = self.scraperFactory.create(launcher)
    romScanner = self.romscannerFactory.create(launcher, scrapers)

    roms = romScanner.scan()
    
    if roms is None:
        return

    # --- If we have a No-Intro XML then audit roms after scanning ----------------------------
    if launcher.has_nointro_xml():
        self._audit_no_intro_roms(launcher, roms)
    else:
        log_info('No-Intro/Redump DAT not configured. Do not audit ROMs.')

    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Advanced Emulator Launcher', 'Saving ROM JSON database ...')

    # ~~~ Save ROMs XML file ~~~
    # >> Also save categories/launchers to update timestamp.
    # >> Update launcher timestamp to update VLaunchers and reports.
    log_debug('Saving {0} ROMS'.format(len(roms)))
    launcher.update_rom_set(roms)

    pDialog.update(80)
    
    launcher.set_number_of_roms()
    g_LauncherRepository.save(launcher)

    pDialog.update(100)
    pDialog.close()

def m_audit_no_intro_roms(launcher, roms):
    
    log_info('No-Intro/Redump DAT configured. Starting ROM audit ...')
    #roms_base_noext = launcher.get_roms_base()
    #nointro_xml_FN = launcher.get_nointro_xml_filepath()
            
    nointro_scanner = RomDatFileScanner(g_settings)
    roms = launcher.get_roms()

    if nointro_scanner.update_roms_NoIntro_status(launcher, roms):

        launcher.update_rom_set(roms)
        kodi_notify('ROM scanner and audit finished. '
                    'Have {0} / Miss {1} / Unknown {2}'.format(self.audit_have, self.audit_miss, self.audit_unknown))
    else:
        # >> ERROR when auditing the ROMs. Unset nointro_xml_file
        launcher.reset_nointro_xmldata()
        kodi_notify_warn('Error auditing ROMs. XML DAT file unset.')

# ---------------------------------------------------------------------------------------------
# Metadata scrapers
# ---------------------------------------------------------------------------------------------
#
# Called when editing a ROM by _command_edit_rom()
# Always do semi-automatic scraping when editing ROMs/Launchers.
# launcherID = '0' if scraping ROM in Favourites
# roms are editing using Python arguments passed by assignment. Caller is responsible of
# saving the ROMs XML file.
#
# Returns:
#   True   Changes were made.
#   False  Changes not made. No need to save ROMs XML/Update container
#
def m_gui_scrap_rom_metadata(launcher, rom, scraper_obj):
    # --- Grab ROM info and metadata scraper settings ---
    # >> ROM in favourites
    if launcher.get_id() == VLAUNCHER_FAVOURITES_ID or launcher.get_launcher_type() == LAUNCHER_COLLECTION:
        platform = rom.get_custom_attribute('platform')
    else:
        platform = launcher.get_platform()

    ROM      = rom.get_file()
    rom_name = rom.get_name()
    scan_clean_tags            = g_settings['scan_clean_tags']
    scan_ignore_scrapped_title = g_settings['scan_ignore_scrap_title']
    log_info('_gui_scrap_rom_metadata() ROM "{0}"'.format(rom_name))

    # --- Ask user to enter ROM metadata search string ---
    keyboard = xbmc.Keyboard(rom_name, 'Enter the ROM search string ...')
    keyboard.doModal()
    if not keyboard.isConfirmed(): return False
    search_string = keyboard.getText().decode('utf-8')

    # --- Do a search and get a list of games ---
    # >> Prevent race conditions
    kodi_busydialog_ON()
    results = scraper_obj.get_search(search_string, ROM.getBase_noext(), platform)
    kodi_busydialog_OFF()
    log_verb('_gui_scrap_rom_metadata() Metadata scraper found {0} result/s'.format(len(results)))
    if not results:
        kodi_notify('Scraper found no game matches')
        return False

    # --- Display corresponding game list found so user choses ---
    rom_name_list = []
    for game in results: rom_name_list.append(game['display_name'])
    # >> If there is only one item in the list then don't show select dialog
    if len(rom_name_list) == 1:
        selectgame = 0
    else:
        selectgame = xbmcgui.Dialog().select('Select game for ROM {0}'.format(rom_name), rom_name_list)
        if selectgame < 0: return False
    log_verb('_gui_scrap_rom_metadata() User chose game "{0}"'.format(rom_name_list[selectgame]))

    # --- Grab metadata for selected game ---
    # >> Prevent race conditions
    kodi_busydialog_ON()
    gamedata = scraper_obj.get_metadata(results[selectgame])
    kodi_busydialog_OFF()
    if not gamedata:
        kodi_notify_warn('Cannot download game metadata.')
        return False

    # --- Put metadata into ROM dictionary ---
    # >> Ignore scraped title
    scraped_title = ''
    if scan_ignore_scrapped_title:
        scraped_title = text_format_ROM_title(ROM.getBase_noext(), scan_clean_tags)
        log_debug('User wants to ignore scraper name. Setting name to "{0}"'.format(scraped_title))
    # >> Use scraped title
    else:
        scraped_title = gamedata['title']
        log_debug('User wants scrapped name. Setting name to "{0}"'.format(scraped_title))

    rom.set_name(scraped_title)
    rom.update_releaseyear(gamedata['year'])
    rom.update_genre(gamedata['genre'])
    rom.update_developer(gamedata['developer'])
    rom.set_number_of_players(gamedata['nplayers'])
    rom.set_esrb_rating(gamedata['esrb'])
    rom.update_plot(gamedata['plot'])

    # >> Changes were made, return True
    kodi_notify('ROM metadata updated')

    return True

#
# Called when editing a launcher by _command_edit_launcher()
# Note that launcher maybe a ROM launcher or a standalone launcher (game, app)
# Scrap standalone launcher (typically a game) metadata
# Called when editing a launcher...
# Always do semi-automatic scraping when editing ROMs/Launchers
#
# Returns:
#   True   Changes were made.
#   False  Changes not made. No need to save ROMs XML/Update container
#
def m_gui_scrap_launcher_metadata(launcherID, scraper_obj):
    launcher = g_LauncherRepository.find(launcherID)
    launcher_name = launcher.get_name()
    platform = launcher.get_platform()

    # Edition of the launcher name
    keyboard = xbmc.Keyboard(launcher_name, 'Enter the launcher search string ...')
    keyboard.doModal()
    if not keyboard.isConfirmed(): return False
    search_string = keyboard.getText().decode('utf-8')

    # Scrap and get a list of matches
    kodi_busydialog_ON()
    results = scraper_obj.get_search(search_string, '', platform)
    kodi_busydialog_OFF()
    log_debug('_gui_scrap_launcher_metadata() Metadata scraper found {0} result/s'.format(len(results)))
    if not results:
        kodi_notify('Scraper found no matches')
        return False

    # --- Display corresponding game list found so user choses ---
    rom_name_list = []
    for game in results: rom_name_list.append(game['display_name'])
    if len(rom_name_list) == 1:
        selectgame = 0
    else:
        selectgame = xbmcgui.Dialog().select('Select item for Launcher {0}'.format(launcher_name), rom_name_list)
        if selectgame < 0: return False

    # --- Grab metadata for selected game ---
    kodi_busydialog_ON()
    gamedata = scraper_obj.get_metadata(results[selectgame])
    kodi_busydialog_OFF()
    if not gamedata:
        kodi_notify_warn('Cannot download game metadata.')
        return False

    # --- Put metadata into launcher dictionary ---
    # >> Scraper should not change launcher title
    # >> 'nplayers' and 'esrb' ignored for launchers
    launcher.update_release_year(gamedata['year'])
    launcher.update_genre(gamedata['genre'])
    launcher.update_developer(gamedata['developer'])
    launcher.update_plot(gamedata['plot'])

    # >> Changes were made
    return True

#
# Reads a text file with category/launcher plot. 
# Checks file size to avoid importing binary files!
#
def m_gui_import_TXT_file(text_file):
    # Warn user in case he chose a binary file or a very big one. Avoid categories.xml corruption.
    log_debug('_gui_import_TXT_file() Importing plot from "{0}"'.format(text_file.getOriginalPath()))
    statinfo = text_file.stat()
    file_size = statinfo.st_size
    log_debug('_gui_import_TXT_file() File size is {0}'.format(file_size))
    if file_size > 16384:
        ret = kodi_dialog_yesno('File "{0}" has {1} bytes and it is very big.'.format(text_file.getPath(), file_size) +
                                'Are you sure this is the correct file?')
        if not ret: return ''

    # Import file
    log_debug('_gui_import_TXT_file() Importing description from "{0}"'.format(text_file.getOriginalPath()))
    file_data = text_file.readAll()

    return file_data

def m_command_exec_import_launchers():
    # >> If enableMultiple = True this function always returns a list of strings in UTF-8
    file_list = xbmcgui.Dialog().browse(1, 'Select XML category/launcher configuration file',
                                        'files', '.xml', enableMultiple = True)

    # >> Process file by file
    for xml_file in file_list:
        xml_file_unicode = xml_file.decode('utf-8')
        log_debug('m_command_exec_import_launchers() Importing "{0}"'.format(xml_file_unicode))
        import_FN = FileNameFactory.create(xml_file_unicode)
        if not import_FN.exists(): continue

        # >> This function edits self.categories, self.launchers dictionaries
        categories = self.category_repository.find_all()
        launchers = g_LauncherRepository.find_all()

        category_datas = {}
        launcher_datas = {}
        for category in categories:
            category_datas[category.get_id()] = category.get_data()                
        for launcher in launchers:
            launcher_datas[launcher.get_id()] = launcher.get_data()

        autoconfig_import_launchers(CATEGORIES_FILE_PATH, ROMS_DIR, category_datas, launcher_datas, import_FN)

    # --- Save Categories/Launchers, update timestamp and notify user ---
    altered_categories = []
    for category_data in category_datas:
        category = Category(category_data)
        altered_categories.append(category)

    altered_launchers = []
    for launcher_data in launcher_datas:
        launcher = self.launcher_factory.create(launcher_data)
        altered_launchers.append(launcher)

    self.category_repository.save_multiple(altered_categories)
    g_LauncherRepository.save_multiple(altered_launchers)

    kodi_refresh_container()
    kodi_notify('Finished importing Categories/Launchers')

#
# Export AEL launcher configuration
#
def m_command_exec_export_launchers():
    log_debug('m_command_exec_export_launchers() Exporting Category/Launcher XML configuration')

    # --- Ask path to export XML configuration ---
    dir_path = xbmcgui.Dialog().browse(0, 'Select XML export directory', 'files',
                                       '', False, False).decode('utf-8')
    if not dir_path: return

    # --- If XML exists then warn user about overwriting it ---
    export_FN = FileNameFactory.create(dir_path).pjoin('AEL_configuration.xml')
    if export_FN.exists():
        ret = kodi_dialog_yesno('AEL_configuration.xml found in the selected directory. Overwrite?')
        if not ret:
            kodi_notify_warn('Category/Launcher XML exporting cancelled')
            return

    categories = self.category_repository.find_all()
    launchers = g_LauncherRepository.find_all()
    
    category_datas = {}
    launcher_datas = {}
    for category in categories:
        category_datas[category.get_id()] = category.get_data()                
    for launcher in launchers:
        launcher_datas[launcher.get_id()] = launcher.get_data()

    # --- Export stuff ---
    try:
        autoconfig_export_all(category_datas, laucnher_datas, export_FN)
    except AEL_Error as E:
        kodi_notify_warn('{0}'.format(E))
    else:
        kodi_notify('Exported AEL Categories and Launchers XML configuration')

#
# Import legacy Advanced Launcher launchers.xml
# DEPRECATED, will be removed soon.
#
def m_command_exec_import_legacy_AL():
    # >> Confirm action with user
    ret = kodi_dialog_yesno('Are you sure you want to import Advanced Launcher launchers.xml?')
    if not ret: return

    kodi_notify('Importing AL launchers.xml ...')
    AL_DATA_DIR = FileNameFactory.create('special://profile/addon_data/plugin.program.advanced.launcher')
    LAUNCHERS_FILE_PATH = AL_DATA_DIR.pjoin('launchers.xml')
    FIXED_LAUNCHERS_FILE_PATH = ADDON_DATA_DIR.pjoin('fixed_launchers.xml')

    # >> Check that launchers.xml exist
    if not LAUNCHERS_FILE_PATH.exists():
        log_error("m_command_exec_import_legacy_AL() Cannot find '{0}'".format(LAUNCHERS_FILE_PATH.getPath()))
        kodi_dialog_OK('launchers.xml not found! Nothing imported.')
        return

    # >> Try to correct ilegal XML characters in launchers.xml
    # >> Also copies fixed launchers.xml into AEL data directory.
    fs_fix_launchers_xml(LAUNCHERS_FILE_PATH, FIXED_LAUNCHERS_FILE_PATH)

    # >> Read launchers.xml
    AL_categories = {}
    AL_launchers = {}
    kodi_busydialog_ON()
    fs_load_legacy_AL_launchers(FIXED_LAUNCHERS_FILE_PATH, AL_categories, AL_launchers)
    kodi_busydialog_OFF()

    # >> Traverse AL data and create categories/launchers/ROMs
    num_categories = 0
    num_launchers = 0
    num_ROMs = 0
    default_SID = misc_generate_random_SID()

    categories = {}
    for AL_category_key in AL_categories:
        num_categories += 1
        AL_category = AL_categories[AL_category_key]

        category_data = {}
        # >> Do translation
        category_data['id']       = default_SID if AL_category['id'] == 'default' else AL_category['id']
        category_data['m_name']   = AL_category['name']
        category_data['m_genre']  = AL_category['genre']
        category_data['m_plot']   = AL_category['plot']
        category_data['s_thumb']  = AL_category['thumb']
        category_data['s_fanart'] = AL_category['fanart']
        category_data['finished'] = False if AL_category['finished'] == 'false' else True
        
        category = Category() 
        category.import_data(category_data)
        categories[category.get_id()] = category

    launchers = []
    for AL_launcher_key in AL_launchers:
        num_launchers += 1
        AL_launcher = AL_launchers[AL_launcher_key]

        launcher_data = {}
        # >> Do translation
        launcher_data['id']           = AL_launcher['id']
        launcher_data['m_name']       = AL_launcher['name']
        launcher_data['m_year']       = AL_launcher['release']
        launcher_data['m_genre']      = AL_launcher['genre']
        launcher_data['m_studio']     = AL_launcher['studio']
        launcher_data['m_plot']       = AL_launcher['plot']
        # >> 'gamesys' ignored, set to unknown to avoid trouble with scrapers
        # launcher_data['platform']    = AL_launcher['gamesys']
        launcher_data['platform']     = 'Unknown'
        launcher_data['categoryID']   = default_SID if AL_launcher['category'] == 'default' else AL_launcher['category']
        launcher_data['application']  = AL_launcher['application']
        launcher_data['args']         = AL_launcher['args']
        launcher_data['rompath']      = AL_launcher['rompath']
        launcher_data['romext']       = AL_launcher['romext']
        launcher_data['finished']     = False if AL_launcher['finished'] == 'false' else True
        launcher_data['toggle_window'] = False if AL_launcher['minimize'] == 'false' else True
        # >> 'lnk' ignored, always active in AEL
        launcher_data['s_thumb']      = AL_launcher['thumb']
        launcher_data['s_fanart']     = AL_launcher['fanart']
        launcher_data['path_title']   = AL_launcher['thumbpath']
        launcher_data['path_fanart']  = AL_launcher['fanartpath']
        launcher_data['path_trailer'] = AL_launcher['trailerpath']
                   
        launcher_type = LAUNCHER_STANDALONE if launcher_data['rompath'] == '' else LAUNCHER_ROM
        launcher = self.launcher_factory.create_new(launcher_type) 
        launcher.import_data(launcher_data)

        # --- Import ROMs if ROMs launcher ---
        AL_roms = AL_launcher['roms']
        if AL_roms:
            roms = []

            category_id = launcher.get_category_id()
            category = categories[category_id]
            
            roms_base_noext = fs_get_ROMs_basename(category.get_name(), launcher.get_name(), launcher.get_id())
            launcher.update_roms_base(roms_base_noext)
            launcher.set_number_of_roms(len(AL_roms))

            for AL_rom_ID in AL_roms:
                num_ROMs += 1
                AL_rom = AL_roms[AL_rom_ID]
                rom_data = {}
                # >> Do translation
                rom_data['id']        = AL_rom['id']
                rom_data['m_name']    = AL_rom['name']
                rom_data['m_year']    = AL_rom['release']
                rom_data['m_genre']   = AL_rom['genre']
                rom_data['m_studio']  = AL_rom['studio']
                rom_data['m_plot']    = AL_rom['plot']
                rom_data['filename']  = AL_rom['filename']
                rom_data['altapp']    = AL_rom['altapp']
                rom_data['altarg']    = AL_rom['altarg']
                rom_data['finished']  = False if AL_rom['finished'] == 'false' else True
                rom_data['s_title']   = AL_rom['thumb']
                rom_data['s_fanart']  = AL_rom['fanart']
                rom_data['s_trailer'] = AL_rom['trailer']

                # >> Add to ROM dictionary
                rom = Rom(rom_data)
                roms.append(rom)

            # >> Save ROMs XML
            launcher.update_rom_set(launcher)
        else:
            launcher.set_roms_xml_file('')

        # --- Add launcher to AEL launchers ---
        launchers.append(launcher)

    # >> Save AEL categories.xml
    self.category_repository.save_multiple(list(categories.values))
    g_LauncherRepository.save_multiple(launchers)

    # --- Show some information to user ---
    kodi_dialog_OK('Imported {0} Category/s, {1} Launcher/s '.format(num_categories, num_launchers) +
                   'and {0} ROM/s.'.format(num_ROMs))
    kodi_refresh_container()

#
# Checks all databases and tries to update to newer version if possible
#
def m_command_exec_check_database():
    log_debug('m_command_exec_check_database() Beginning ....')
    pDialog = xbmcgui.DialogProgress()
    pDialog_canceled = False

    # >> Open Categories/Launchers XML.
    #    XML should be updated automatically on load.
    pDialog.create('Advanced Emulator Launcher', 'Checking Categories/Launchers ...')

    # >> Traverse and fix Categories.
    categories = g_CategoryRepository.find_all()
    for category in categories:
        category_data = category.get_data_dic()

        # >> Fix s_thumb -> s_icon renaming
        if category_data['default_icon'] == 's_thumb':      category_data['default_icon'] = 's_icon'
        if category_data['default_fanart'] == 's_thumb':    category_data['default_fanart'] = 's_icon'
        if category_data['default_banner'] == 's_thumb':    category_data['default_banner'] = 's_icon'
        if category_data['default_poster'] == 's_thumb':    category_data['default_poster'] = 's_icon'
        if category_data['default_clearlogo'] == 's_thumb': category_data['default_clearlogo'] = 's_icon'

        # >> Fix s_flyer -> s_poster renaming
        if category_data['default_icon'] == 's_flyer':      category_data['default_icon'] = 's_poster'
        if category_data['default_fanart'] == 's_flyer':    category_data['default_fanart'] = 's_poster'
        if category_data['default_banner'] == 's_flyer':    category_data['default_banner'] = 's_poster'
        if category_data['default_poster'] == 's_flyer':    category_data['default_poster'] = 's_poster'
        if category_data['default_clearlogo'] == 's_flyer': category_data['default_clearlogo'] = 's_poster'

    # >> Save categories.xml
    g_CategoryRepository.save_multiple(categories)
    pDialog.update(50)

    launchers = g_LauncherRepository.find_all()
    # >> Traverse and fix Launchers.
    for launcher in launchers:
        launcher_data = launcher.get_data_dic()

        # >> Fix s_thumb -> s_icon renaming
        if launcher_data['default_icon'] == 's_thumb':       launcher_data['default_icon'] = 's_icon'
        if launcher_data['default_fanart'] == 's_thumb':     launcher_data['default_fanart'] = 's_icon'
        if launcher_data['default_banner'] == 's_thumb':     launcher_data['default_banner'] = 's_icon'
        if launcher_data['default_poster'] == 's_thumb':     launcher_data['default_poster'] = 's_icon'
        if launcher_data['default_clearlogo'] == 's_thumb':  launcher_data['default_clearlogo'] = 's_icon'
        if launcher_data['default_controller'] == 's_thumb': launcher_data['default_controller'] = 's_icon'

        # >> Fix s_flyer -> s_poster renaming
        if launcher_data['default_icon'] == 's_flyer':       launcher_data['default_icon'] = 's_poster'
        if launcher_data['default_fanart'] == 's_flyer':     launcher_data['default_fanart'] = 's_poster'
        if launcher_data['default_banner'] == 's_flyer':     launcher_data['default_banner'] = 's_poster'
        if launcher_data['default_poster'] == 's_flyer':     launcher_data['default_poster'] = 's_poster'
        if launcher_data['default_clearlogo'] == 's_flyer':  launcher_data['default_clearlogo'] = 's_poster'
        if launcher_data['default_controller'] == 's_flyer': launcher_data['default_controller'] = 's_poster'
        
    # >> Save categories.xml
    g_LauncherRepository.save_multiple(launchers)
    pDialog.update(100)

    # >> Traverse all launchers. Load ROMs and check every ROMs.
    pDialog.update(0, 'Checking Launcher ROMs ...')
    num_launchers = len(launchers)
    processed_launchers = 0
    for launcher in launchers:
        if not launcher.supports_launching_roms():
            continue

        log_debug('_command_edit_rom() Checking Launcher "{0}"'.format(launcher.get_name()))
        # --- Load standard ROM database ---
        roms = launcher.get_roms()
        for rom in roms: self._misc_fix_rom_object(rom)
        launcher.update_rom_set(roms)

        if launcher.supports_parent_clone_roms():
            # --- If exists, load Parent ROM database ---
            parent_roms = launcher.get_parent_roms()
            for parent_rom in parent_roms: self._misc_fix_rom_object(parent_rom)
            launcher.update_parent_rom_set(parent_roms)

        # >> This updates timestamps and forces regeneration of Virtual Launchers.
        g_LauncherRepository.save(launcher)

        # >> Update dialog
        processed_launchers += 1
        update_number = (processed_launchers * 100) / num_launchers
        # >> Save categories.xml because launcher timestamps changed
        pDialog.update(update_number)
    pDialog.update(100)

    # >> Load Favourite ROMs and update JSON
    pDialog.update(0, 'Checking Favourite ROMs ...')
    fav_launcher = g_LauncherRepository.find(VLAUNCHER_FAVOURITES_ID)
    roms_fav = fav_launcher.get_roms()
    num_fav_roms = len(roms_fav)
    processed_fav_roms = 0
    # >> Get ROM object
    for rom in roms_fav:
        self._misc_fix_Favourite_rom_object(rom)
        # >> Update dialog
        processed_fav_roms += 1
        update_number = (float(processed_fav_roms) / float(num_fav_roms)) * 100 
        pDialog.update(int(update_number))
    fav_launcher.update_rom_set(roms_fav)
    pDialog.update(100)

    # >> Traverse every ROM Collection database and check/update Favourite ROMs.
    collections = g_collectionRepository.find_all()
    pDialog.update(0, 'Checking Collection ROMs ...')
    num_collections = len(collections)
    processed_collections = 0
    for collection_launcher in collections:
        collection_id = collection_launcher.get_id()
        collection_data = collection_launcher.get_data()

        # >> Fix collection
        if 'default_thumb' in collection_data:
            collection_data['default_icon'] = collection_data['default_thumb']
            collection_data.pop('default_thumb')
        if 's_thumb' in collection_data:
            collection_data['s_icon'] = collection_data['s_thumb']
            collection_data.pop('s_thumb')
        if 's_flyer' in collection_data:
            collection_data['s_poster'] = collection_data['s_flyer']
            collection_data.pop('s_flyer')
        # >> Fix s_thumb -> s_icon renaming
        if collection_data['default_icon'] == 's_thumb':      collection_data['default_icon'] = 's_icon'
        if collection_data['default_fanart'] == 's_thumb':    collection_data['default_fanart'] = 's_icon'
        if collection_data['default_banner'] == 's_thumb':    collection_data['default_banner'] = 's_icon'
        if collection_data['default_poster'] == 's_thumb':    collection_data['default_poster'] = 's_icon'
        if collection_data['default_clearlogo'] == 's_thumb': collection_data['default_clearlogo'] = 's_icon'
        # >> Fix s_flyer -> s_poster renaming
        if collection_data['default_icon'] == 's_flyer':      collection_data['default_icon'] = 's_poster'
        if collection_data['default_fanart'] == 's_flyer':    collection_data['default_fanart'] = 's_poster'
        if collection_data['default_banner'] == 's_flyer':    collection_data['default_banner'] = 's_poster'
        if collection_data['default_poster'] == 's_flyer':    collection_data['default_poster'] = 's_poster'
        if collection_data['default_clearlogo'] == 's_flyer': collection_data['default_clearlogo'] = 's_poster'

        # >> Fix collection ROMs
        collection_rom_list = collection_launcher.get_roms()
        for rom in collection_rom_list: self._misc_fix_Favourite_rom_object(rom)
        collection_launcher.update_rom_set(collection_rom_list)
        
        # >> Update progress dialog
        processed_collections += 1
        update_number = (float(processed_collections) / float(num_collections)) * 100 
        pDialog.update(int(update_number))
    # >> Save ROM Collection index
    #fs_write_Collection_index_XML(COLLECTIONS_FILE_PATH, collections)
    g_collectionRepository.save_multiple(collections)
    pDialog.update(100)

    # >> Load Most Played ROMs and check/update.
    pDialog.update(0, 'Checking Most Played ROMs ...')                    
    most_played_launcher = g_LauncherRepository.find(VLAUNCHER_MOST_PLAYED_ID)
    most_played_roms = most_played_launcher.get_roms()
    for rom in most_played_roms:
        self._misc_fix_Favourite_rom_object(rom)
        
    most_played_launcher.update_rom_set(most_played_roms)
    pDialog.update(100)

    # >> Load Recently Played ROMs and check/update.
    pDialog.update(0, 'Checking Recently Played ROMs ...')
    recent_played_launcher = g_LauncherRepository.find(VLAUNCHER_RECENT_ID)
    recent_roms_list = recent_played_launcher.get_roms()

    if recent_roms_list is None:
        log_warning('Recently played romset not loaded')
    else:
        for rom in recent_roms_list: 
            self._misc_fix_Favourite_rom_object(rom)
        recent_played_launcher.update_rom_set(recent_roms_list)

    pDialog.update(100)
    pDialog.close()

    # >> So long and thanks for all the fish.
    kodi_notify('All databases checked')
    log_debug('_command_check_database() Exiting')

#
# ROM dictionary is edited by Python passing by assigment
#
def m_misc_fix_rom_object(rom):
    rom_data = rom.get_data()
    # --- Add new fields if not present ---
    if 'm_nplayers'    not in rom_data: rom_data['m_nplayers']    = ''
    if 'm_esrb'        not in rom_data: rom_data['m_esrb']        = ESRB_PENDING
    if 'disks'         not in rom_data: rom_data['disks']         = []
    if 'pclone_status' not in rom_data: rom_data['pclone_status'] = PCLONE_STATUS_NONE
    if 'cloneof'       not in rom_data: rom_data['cloneof']       = ''
    # --- Delete unwanted/obsolete stuff ---
    if 'nointro_isClone' in rom_data: rom_data.pop('nointro_isClone')
    # --- DB field renamings ---
    if 'm_studio' in rom_data:
        rom_data['m_developer'] = rom_data['m_studio']
        rom_data.pop('m_studio')

def m_misc_fix_Favourite_rom_object(rom):
    # --- Fix standard ROM fields ---
    self._misc_fix_rom_object(rom)
    rom_data = rom.get_data()

    # --- Favourite ROMs additional stuff ---
    if 'args_extra' not in rom_data: rom_data['args_extra'] = []
    if 'non_blocking' not in rom_data: rom_data['non_blocking'] = False
    if 'roms_default_thumb' in rom_data:
        rom_data['roms_default_icon'] = rom_data['roms_default_thumb']
        rom_data.pop('roms_default_thumb')
    if 'minimize' in rom_data:
        rom_data['toggle_window'] = rom_data['minimize']
        rom_data.pop('minimize')

def m_command_exec_check_launchers():
    log_info('m_command_exec_check_launchers() Checking all Launchers configuration ...')

    launchers = g_LauncherRepository.find_all()

    main_str_list = []
    main_str_list.append('Number of launchers: {0}\n\n'.format(len(launchers)))
    for launcher in sorted(launchers, key = lambda l : l.get_name()):
        
        l_str = []
        main_str_list.append('[COLOR orange]Launcher "{0}"[/COLOR]\n'.format(launcher.get_name()))

        # >> Check that platform is on AEL official platform list
        platform = launcher.get_platform()
        if platform not in AEL_platform_list:
            l_str.append('Unrecognised platform "{0}"\n'.format(platform))

        # >> Check that category exists
        category = self.category_repository.find(launcher.get_category_id())
        if category is None:
                l_str.append('Category not found (unlinked launcher)\n')

        # >> Check that application exists
        app_FN = FileNameFactory.create(launcher['application'])
        if not app_FN.exists():
            l_str.append('Application "{0}" not found\n'.format(app_FN.getPath()))
            
        launcher_data = launcher.get_data()
        
        # >> Test that artwork files exist if not empty (s_* fields)
        self._aux_check_for_file(l_str, 's_icon', launcher_data)
        self._aux_check_for_file(l_str, 's_fanart', launcher_data)
        self._aux_check_for_file(l_str, 's_banner', launcher_data)
        self._aux_check_for_file(l_str, 's_poster', launcher_data)
        self._aux_check_for_file(l_str, 's_clearlogo', launcher_data)
        self._aux_check_for_file(l_str, 's_controller', launcher_data)
        self._aux_check_for_file(l_str, 's_trailer', launcher_data)

        # Checks only applicable for RomLaunchers
        if launcher.supports_launching_roms():
            
            # >> Check that rompath exists if rompath is not empty
            # >> Empty rompath means standalone launcher
            rompath = launcher.get_rom_path()
            if not rompath.exists():
                l_str.append('ROM path "{0}" not found\n'.format(rompath.getPath()))

            # >> Check that DAT file exists if not empty
            if launcher.has_nointro_xml():
                nointro_xml_file_FN = launcher.get_nointro_xml_filepath()
                if not nointro_xml_file_FN.exists():
                    l_str.append('DAT file "{0}" not found\n'.format(nointro_xml_file_FN.getPath()))

            # >> Test that ROM_asset_path exists if not empty
            ROM_asset_path = launcher.get_rom_asset_path()
            if not ROM_asset_path.exists():
                l_str.append('ROM_asset_path "{0}" not found\n'.format(ROM_asset_path.getPath()))

            # >> Test that ROM asset paths exist if not empty (path_* fields)
            self._aux_check_for_file(l_str, 'path_title', launcher_data)
            self._aux_check_for_file(l_str, 'path_snap', launcher_data)
            self._aux_check_for_file(l_str, 'path_boxfront', launcher_data)
            self._aux_check_for_file(l_str, 'path_boxback', launcher_data)
            self._aux_check_for_file(l_str, 'path_cartridge', launcher_data)
            self._aux_check_for_file(l_str, 'path_fanart', launcher_data)
            self._aux_check_for_file(l_str, 'path_banner', launcher_data)
            self._aux_check_for_file(l_str, 'path_clearlogo', launcher_data)
            self._aux_check_for_file(l_str, 'path_flyer', launcher_data)
            self._aux_check_for_file(l_str, 'path_map', launcher_data)
            self._aux_check_for_file(l_str, 'path_manual', launcher_data)
            self._aux_check_for_file(l_str, 'path_trailer', launcher_data)

            # >> Check for duplicate asset paths
            

        # >> If l_str is empty is because no problems were found.
        if l_str:
            main_str_list.extend(l_str)
        else:
            main_str_list.append('No problems found\n')
        main_str_list.append('\n')

    # >> Stats report
    log_info('Writing report file "{0}"'.format(g_PATHS.LAUNCHER_REPORT_FILE_PATH.getPath()))
    full_string = ''.join(main_str_list).encode('utf-8')
    file = open(g_PATHS.LAUNCHER_REPORT_FILE_PATH.getPath(), 'w')
    file.write(full_string)
    file.close()

    # >> Display report TXT file
    window_title = 'Launchers report'
    kodi_display_text_window_mono(window_title, full_string)

def m_aux_check_for_file(str_list, dic_key_name, launcher):
    path = launcher[dic_key_name]
    path_FN = FileNameFactory.create(path)
    if path and not path_FN.exists():
        problems_found = True
        str_list.append('{0} "{1}" not found\n'.format(dic_key_name, path_FN.getPath()))

def m_command_exec_check_missing_assets():
    log_debug('m_command_exec_check_missing_assets() BEGIN')
    window_title = 'Check missing assets/artwork'

    slist = []
    slist.append('Sorry, not implemented yet')
    kodi_display_text_window_mono(window_title, '\n'.join(slist))

def m_command_exec_check_Retroarch_cores():
    log_debug('m_command_exec_check_Retroarch_cores() BEGIN')
    window_title = 'Check Retroarch installed cores'

    slist = []
    slist.append('Sorry, not implemented yet')
    kodi_display_text_window_mono(window_title, '\n'.join(slist))

def m_command_exec_check_Retroarch_BIOS():
    log_info('m_command_exec_check_Retroarch_BIOS() Checking Retroarch BIOSes ...')
    check_only_mandatory = g_settings['io_retroarch_only_mandatory']
    log_info('m_command_exec_check_Retroarch_BIOS() check_only_mandatory = {0}'.format(check_only_mandatory))

    # >> If Retroarch System dir not configured or found abort.
    sys_dir_FN = FileNameFactory.create(g_settings['io_retroarch_sys_dir'])
    if not sys_dir_FN.exists():
        kodi_dialog_OK('Retroarch System directory "{0}" not found. '.format(sys_dir_FN.getPath()) +
                       'Please configure it in the addons settings.')
        return

    # >> Progress dialog
    pDialog = xbmcgui.DialogProgress()
    pDialog_canceled = False
    pDialog.create('Advanced Emulator Launcher', 'Checking Retroarch BIOSes ...')
    num_BIOS = len(Libretro_BIOS_list)
    file_count = 0

    # >> Algorithm:
    #    1) Traverse list of BIOS. For every BIOS:
    #    2) Check if file exists. If not exists -> missing BIOS.
    #    3) If BIOS exists check file size.
    #    3) If BIOS exists check MD5
    #    4) Unknwon files in Retroarch System dir are ignored and non-reported.
    #    5) Write results into a report TXT file.
    BIOS_status_dic = {}
    BIOS_status_dic_colour = {}
    for BIOS_dic in Libretro_BIOS_list:
        if check_only_mandatory and not BIOS_dic['mandatory']:
            log_debug('BIOS "{0}" is not mandatory. Skipping check.'.format(BIOS_dic['filename']))
            continue

        BIOS_file_FN = sys_dir_FN.pjoin(BIOS_dic['filename'])
        log_debug('Testing BIOS "{0}"'.format(BIOS_file_FN.getPath()))

        if not BIOS_file_FN.exists():
            log_info('Not found "{0}"'.format(BIOS_file_FN.getPath()))
            BIOS_status_dic[BIOS_dic['filename']] = 'Not found'
            BIOS_status_dic_colour[BIOS_dic['filename']] = '[COLOR orange]Not found[/COLOR]'
            continue

        BIOS_stat = BIOS_file_FN.stat()
        file_size = BIOS_stat.st_size
        if file_size != BIOS_dic['size']:
            log_info('Wrong size "{0}"'.format(BIOS_file_FN.getPath()))
            log_info('It is {0} and must be {1}'.format(file_size, BIOS_dic['size']))
            BIOS_status_dic[BIOS_dic['filename']] = 'Wrong size'
            BIOS_status_dic_colour[BIOS_dic['filename']] = '[COLOR orange]Wrong size[/COLOR]'
            continue

        hash_md5 = hashlib.md5()
        with open(BIOS_file_FN.getPath(), "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        file_MD5 = hash_md5.hexdigest()
        log_debug('MD5 is "{0}"'.format(file_MD5))
        if file_MD5 != BIOS_dic['md5']:
            log_info('Wrong MD5 "{0}"'.format(BIOS_file_FN.getPath()))
            log_info('It is       "{0}"'.format(file_MD5))
            log_info('and must be "{0}"'.format(BIOS_dic['md5']))
            BIOS_status_dic[BIOS_dic['filename']] = 'Wrong MD5'
            BIOS_status_dic_colour[BIOS_dic['filename']] = '[COLOR orange]Wrong MD5[/COLOR]'
            continue
        log_info('BIOS OK "{0}"'.format(BIOS_file_FN.getPath()))
        BIOS_status_dic[BIOS_dic['filename']] = 'OK'
        BIOS_status_dic_colour[BIOS_dic['filename']] = '[COLOR lime]OK[/COLOR]'

        # >> Update progress
        file_count += 1
        update_number = (float(file_count) / float(num_BIOS)) * 100
        pDialog.update(int(update_number))
    pDialog.update(100)
    pDialog.close()

    # >> Output format:
    #    BIOS name             Mandatory  Status      Cores affected 
    #    -------------------------------------------------
    #    5200.rom              YES        OK          ---            
    #    7800 BIOS (E).rom     NO         Wrong MD5   core a name    
    #                                                 core b name    
    #    7800 BIOS (U).rom     YES        OK          ---            
    #
    max_size_BIOS_filename = 0
    for BIOS_dic in Libretro_BIOS_list:
        if len(BIOS_dic['filename']) > max_size_BIOS_filename:
            max_size_BIOS_filename = len(BIOS_dic['filename'])

    max_size_status = 0
    for key in BIOS_status_dic:
        if len(BIOS_status_dic[key]) > max_size_status:
            max_size_status = len(BIOS_status_dic[key])

    str_list = []
    str_list.append('Retroarch system dir "{0}"\n'.format(sys_dir_FN.getPath()))
    if check_only_mandatory:
        str_list.append('Checking only mandatory BIOSes.\n\n')
    else:
        str_list.append('Checking mandatory and optional BIOSes.\n\n')
    bios_str      = '{0}{1}'.format('BIOS name', ' ' * (max_size_BIOS_filename - len('BIOS name')))
    mandatory_str = 'Mandatory'
    status_str    = '{0}{1}'.format('Status', ' ' * (max_size_status - len('Status')))
    cores_str     = 'Cores affected'
    size_total = len(bios_str) + len(mandatory_str) + len(status_str) + len(cores_str) + 6
    str_list.append('{0}  {1}  {2}  {3}\n'.format(bios_str, mandatory_str, status_str, cores_str))
    str_list.append('{0}\n'.format('-' * size_total))

    for BIOS_dic in Libretro_BIOS_list:
        BIOS_filename = BIOS_dic['filename']
        # >> If BIOS was skipped continue loop
        if BIOS_filename not in BIOS_status_dic: continue
        status_text = BIOS_status_dic[BIOS_filename]
        status_text_colour = BIOS_status_dic_colour[BIOS_filename]
        filename_str = '{0}{1}'.format(BIOS_filename, ' ' * (max_size_BIOS_filename - len(BIOS_filename)))
        mandatory_str = 'YES      ' if BIOS_dic['mandatory'] else 'NO       '
        status_str = '{0}{1}'.format(status_text_colour, ' ' * (max_size_status - len(status_text)))
        len_status_str = len('{0}{1}'.format(status_text, ' ' * (max_size_status - len(status_text))))

        # >> Print affected core list
        core_list = BIOS_dic['cores']
        if len(core_list) == 0:
            line_str = '{0}  {1}  {2}\n'.format(filename_str, mandatory_str, status_str)
            str_list.append(line_str)
        else:
            num_spaces = len(filename_str) + 9 + len_status_str + 4
            for i, core_name in enumerate(core_list):
                beautiful_core_name = Retro_core_dic[core_name] if core_name in Retro_core_dic else core_name
                if i == 0:
                    line_str = '{0}  {1}  {2}  {3}\n'.format(filename_str, mandatory_str, status_str, beautiful_core_name)
                    str_list.append(line_str)
                else:
                    line_str = '{0}  {1}\n'.format(' ' * num_spaces, beautiful_core_name)
                    str_list.append(line_str)

    # >> Stats report
    log_info('Writing report file "{0}"'.format(BIOS_REPORT_FILE_PATH.getPath()))
    full_string = ''.join(str_list).encode('utf-8')
    file = open(BIOS_REPORT_FILE_PATH.getPath(), 'w')
    file.write(full_string)
    file.close()

    # >> Display report TXT file.
    window_title = 'Retroarch BIOS report'
    kodi_display_text_window_mono(window_title, full_string)

def m_command_exec_check_Retroplayer_cores():
    log_debug('m_command_exec_check_Retroplayer_cores() BEGIN')
    window_title = 'Check Retroplayer installed cores'

    slist = []
    slist.append('Sorry, not implemented yet')
    kodi_display_text_window_mono(window_title, '\n'.join(slist))

def m_command_exec_check_Retroplayer_BIOS():
    log_debug('m_command_exec_check_Retroplayer_BIOS() BEGIN')
    window_title = 'Check Retroplayer installed BIOSes'

    slist = []
    slist.append('Sorry, not implemented yet')
    kodi_display_text_window_mono(window_title, '\n'.join(slist))

def m_command_exec_global_rom_stats():
    log_debug('m_command_exec_global_rom_stats() BEGIN')
    window_title = 'Global ROM statistics'

    slist = []
    slist.append('Sorry, not implemented yet')
    kodi_display_text_window_mono(window_title, '\n'.join(slist))

def m_command_exec_global_audit_stats():
    log_debug('m_command_exec_global_audit_stats() BEGIN')
    window_title = 'Global ROM Audit statistics'

    slist = []
    slist.append('Sorry, not implemented yet')
    kodi_display_text_window_mono(window_title, '\n'.join(slist))

#
# A set of functions to help making plugin URLs
# NOTE probably this can be implemented in a more elegant way with optinal arguments...
#
def m_misc_url_RunPlugin(command, categoryID = None, launcherID = None, romID = None):
    if romID is not None:
        return 'XBMC.RunPlugin({0}?com={1}&catID={2}&launID={3}&romID={4})'.format(g_base_url, command, categoryID, launcherID, romID)
    elif launcherID is not None:
        return 'XBMC.RunPlugin({0}?com={1}&catID={2}&launID={3})'.format(g_base_url, command, categoryID, launcherID)
    elif categoryID is not None:
        return 'XBMC.RunPlugin({0}?com={1}&catID={2})'.format(g_base_url, command, categoryID)

    return 'XBMC.RunPlugin({0}?com={1})'.format(g_base_url, command)

def m_misc_url(command, categoryID = None, launcherID = None, romID = None):
    if romID is not None:
        return '{0}?com={1}&catID={2}&launID={3}&romID={4}'.format(g_base_url, command, categoryID, launcherID, romID)
    elif launcherID is not None:
        return '{0}?com={1}&catID={2}&launID={3}'.format(g_base_url, command, categoryID, launcherID)
    elif categoryID is not None:
        return '{0}?com={1}&catID={2}'.format(g_base_url, command, categoryID)

    return '{0}?com={1}'.format(g_base_url, command)

def m_misc_url_search(command, categoryID, launcherID, search_type, search_string):
    return '{0}?com={1}&catID={2}&launID={3}&search_type={4}&search_string={5}'.format(
            g_base_url, command, categoryID, launcherID, search_type, search_string
        )

def m_command_buildMenu():
    log_debug('_command_buildMenu() Starting ...')

    hasSkinshortcuts = xbmc.getCondVisibility('System.HasAddon(script.skinshortcuts)') == 1
    if hasSkinshortcuts == False:
        log_warning("Addon skinshortcuts is not installed, cannot build games menu")
        warnAddonMissingDialog = xbmcgui.Dialog()
        warnAddonMissingDialog.notification('Missing addon', 'Addon skinshortcuts is not installed', xbmcgui.NOTIFICATION_WARNING, 5000)
        return

    path = ""
    try:
        skinshortcutsAddon = xbmcaddon.Addon('script.skinshortcuts')
        path = FileNameFactory.create(skinshortcutsAddon.getAddonInfo('path'))

        libPath = path.pjoin('resources', 'lib')
        sys.path.append(libPath.getPath())

        unidecodeModule = xbmcaddon.Addon('script.module.unidecode')
        libPath = FileNameFactory.create(unidecodeModule.getAddonInfo('path'))
        libPath = libPath.pjoin('lib')
        sys.path.append(libPath.getPath())

        sys.modules[ "__main__" ].ADDON    = skinshortcutsAddon
        sys.modules[ "__main__" ].ADDONID  = skinshortcutsAddon.getAddonInfo('id').decode( 'utf-8' )
        sys.modules[ "__main__" ].CWD      = path.getPath()
        sys.modules[ "__main__" ].LANGUAGE = skinshortcutsAddon.getLocalizedString

        import gui, datafunctions

    except Exception as ex:
        log_error("(Exception) Failed to load skinshortcuts addon")
        log_error("(Exception) {0}".format(ex))
        traceback.print_exc()
        warnAddonMissingDialog = xbmcgui.Dialog()
        warnAddonMissingDialog.notification('Failure', 'Could not load skinshortcuts addon', xbmcgui.NOTIFICATION_WARNING, 5000)
        return
    log_debug('_command_buildMenu() Loaded SkinsShortCuts addon')

    startToBuildDialog = xbmcgui.Dialog()
    startToBuild = startToBuildDialog.yesno('Games menu', 'Want to automatically fill the menu?')
    if not startToBuild: return

    menuStore = datafunctions.DataFunctions()
    ui = gui.GUI( "script-skinshortcuts.xml", path, "default", group="mainmenu", defaultGroup=None, nolabels="false", groupname="" )
    ui.currentWindow = xbmcgui.Window()

    mainMenuItems = []
    mainMenuItemLabels = []
    shortcuts = menuStore._get_shortcuts( "mainmenu", defaultGroup =None )
    for shortcut in shortcuts.getroot().findall( "shortcut" ):
        item = ui._parse_shortcut( shortcut )
        mainMenuItemLabels.append(item[1].getLabel())
        mainMenuItems.append(item[1])

    selectMenuToFillDialog = xbmcgui.Dialog()
    selectedMenuIndex = selectMenuToFillDialog.select("Select menu", mainMenuItemLabels)

    selectedMenuItem = mainMenuItems[selectedMenuIndex]

    typeOfContentsDialog = xbmcgui.Dialog()
    typeOfContent = typeOfContentsDialog.select("Select content to create in %s" % selectedMenuItem.getLabel(), ['Categories', 'Launchers'])

    selectedMenuID = selectedMenuItem.getProperty("labelID")
    selectedMenuItems = []

    selectedMenuItemsFromStore = menuStore._get_shortcuts(selectedMenuID, defaultGroup =None )
    amount = len(selectedMenuItemsFromStore.getroot().findall( "shortcut" ))

    if amount < 1:
        selectedDefaultID = selectedMenuItem.getProperty("defaultID")
        selectedMenuItemsFromStore = menuStore._get_shortcuts(selectedDefaultID, defaultGroup =None )

    for shortcut in selectedMenuItemsFromStore.getroot().findall( "shortcut" ):
        item = ui._parse_shortcut( shortcut )
        selectedMenuItems.append(item[1])

    ui.group = selectedMenuID
    count = len(selectedMenuItems)

    if typeOfContent == 0:
        categories = self.category_repository.find_all()
        for category in sorted(categories, key = lambda c : c.get_name()):
            category_dic = category.get_data()
            name = category_dic['m_name']
            url_str =  "ActivateWindow(Programs,\"%s\",return)" % m_misc_url('SHOW_LAUNCHERS', key)
            fanart = asset_get_default_asset_Category(category_dic, 'default_fanart')
            thumb = asset_get_default_asset_Category(category_dic, 'default_thumb', 'DefaultFolder.png')

            log_debug('_command_buildMenu() Adding Category "{0}"'.format(name))
            listitem = self._buildMenuItem(key, name, url_str, thumb, fanart, count, ui)
            selectedMenuItems.append(listitem)

    if typeOfContent == 1:
        launchers = g_LauncherRepository.find_all()
        for launcher in sorted(launchers, key = lambda l : l.get_name()):
            
            name = launcher.get_name()
            launcherID = launcher.get_id()
            categoryID = launcher.get_category_id()
            url_str =  "ActivateWindow(Programs,\"%s\",return)" % m_misc_url('SHOW_ROMS', categoryID, launcherID)
            fanart = asset_get_default_asset_Category(launcher.get_data(), 'default_fanart')
            thumb = asset_get_default_asset_Category(launcher.get_data(), 'default_thumb', 'DefaultFolder.png')

            log_debug('_command_buildMenu() Adding Launcher "{0}"'.format(name))
            listitem = self._buildMenuItem(key, name, url_str, thumb, fanart, count, ui)
            selectedMenuItems.append(listitem)

    ui.changeMade = True
    ui.allListItems = selectedMenuItems
    ui._save_shortcuts()
    ui.close()
    log_info("Saved shortcuts for AEL")
    notifyDialog = xbmcgui.Dialog()
    notifyDialog.notification('Done building', 'The menu is updated with AEL content', xbmcgui.NOTIFICATION_INFO, 5000)
    #xmlfunctions.ADDON = xbmcaddon.Addon('script.skinshortcuts')
    #xmlfunctions.ADDONVERSION = xmlfunctions.ADDON.getAddonInfo('version')
    #xmlfunctions.LANGUAGE = xmlfunctions.ADDON.getLocalizedString
    #xml = XMLFunctions()
    #xml.buildMenu("9000","","0",None,"","0")
    #log_info("Done building menu for AEL")

def m_buildMenuItem(key, name, action, thumb, fanart, count, ui):

    listitem = xbmcgui.ListItem(name)
    listitem.setProperty( "defaultID", key)
    listitem.setProperty( "Path", action )
    listitem.setProperty( "displayPath", action )
    listitem.setProperty( "icon", thumb )
    listitem.setProperty( "skinshortcuts-orderindex", str( count ) )
    listitem.setProperty( "additionalListItemProperties", "[]" )
    ui._add_additional_properties( listitem )
    ui._add_additionalproperty( listitem, "background", fanart )
    ui._add_additionalproperty( listitem, "backgroundName", fanart )

    return listitem

# Executes the migrations which are newer than the last migration version that has run.
# Each migration will be executed in order of version numbering.
#
# The addon setting 'migrated_version' will contain the last version that this environment/machine
# has been migrated to. If not available it will fallback to version 0.0.0
# Once all migrations are executed this field will be updated with the current version number of this
# addon (__addon_version__)
def m_execute_migrations(last_migrated_to_version, to_version = None):
    import migrations
    import migrations.main

    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Advanced Emulator Launcher', 'Performing version upgrade migrations ...')
    pDialog.update(5)

    migrations_folder     = g_PATHS.ADDON_CODE_DIR.pjoin('resources/migrations')
    migration_files       = migrations_folder.scanFilesInPathAsFileNameObjects('*.py')
    applicable_migrations = m_select_applicable_migration_files(migration_files, last_migrated_to_version, to_version)

    num_migrations = len(applicable_migrations)
    i = 1
    for version, migration_file in applicable_migrations.iteritems():
        log_info('Migrating to version {0} using file {1}'.format(version, migration_file.getBase()))
        pDialog.update( (i * 95 // num_migrations) + 5, 'Migrating to version {} ...'.format(version))

        module_namespace = 'migrations.{0}'.format(migration_file.getBase_noext())
        module =__import__(module_namespace, globals(), locals(), ['migrations'])
        migration_class_name = module.MIGRATION_CLASS_NAME
        migration_class = getattr(module, migration_class_name)
        migration = migration_class()
        migration.execute(g_PATHS.ADDON_CODE_DIR, g_PATHS.ADDON_DATA_DIR)

        __addon__.setSetting('migrated_version', version)
        i += 1

    if to_version is None:
        to_version = LooseVersion(__addon_version__)

    __addon__.setSetting('migrated_version', str(to_version))
    pDialog.update(100)
    pDialog.close()
    log_info('Finished migrating. Now set to version {0}'.format(to_version))

# Iterates through the migration files and selects those which
# version number is higher/newer than the last run migration version.
def m_select_applicable_migration_files(migration_files, last_migrated_to_version, to_version):
    applicable_migrations = {}
    for migration_file in migration_files:
        if migration_file.getBase_noext() == '__init__' or migration_file.getBase_noext() == 'main':
            continue

        file_name = migration_file.getBase_noext()
        log_debug('Reading migration file {0}'.format(file_name))
        version_part = file_name.replace('migration_', '').replace('_', '.')
        migration_version = LooseVersion(version_part)

        if migration_version > last_migrated_to_version and (to_version is None or migration_version <= to_version):
            applicable_migrations[version_part] = migration_file

    applicable_migrations = OrderedDict(sorted(applicable_migrations.iteritems(), key=lambda (k,v): LooseVersion(k)))

    return applicable_migrations
