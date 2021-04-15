# -*- coding: utf-8 -*-

# Advanced Emulator Launcher main script file

# Copyright (c) 2016-2019 Wintermute0110 <wintermute0110@gmail.com>
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

# --- Python standard library ---
import sys, os, shutil, fnmatch, string, time, traceback, zlib
import re, urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse, urllib.parse, socket, hashlib, shlex
from collections import OrderedDict

# --- Kodi stuff ---
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

# --- Modules/packages in this plugin ---
from .constants import *
from .utils import *
from .utils_kodi import *
from .disk_IO import *
from .net_IO import *
from .assets import *
from .rom_audit import *
from .scrap import *
from .autoconfig import *

# --- Addon object (used to access settings) ---
__addon_obj__     = xbmcaddon.Addon()
__addon_id__      = __addon_obj__.getAddonInfo('id')
__addon_name__    = __addon_obj__.getAddonInfo('name')
__addon_version__ = __addon_obj__.getAddonInfo('version')
__addon_author__  = __addon_obj__.getAddonInfo('author')
__addon_profile__ = __addon_obj__.getAddonInfo('profile')
__addon_type__    = __addon_obj__.getAddonInfo('type')

# --- Addon paths and constant definition ---
# _PATH is a filename | _DIR is a directory name (with trailing /).
class AEL_Paths:
    def __init__(self):
        # --- Base paths ---
        self.HOME_DIR         = FileName('special://home')
        self.PROFILE_DIR      = FileName('special://profile')
        self.ADDONS_DATA_DIR  = FileName('special://profile/addon_data')
        self.ADDON_DATA_DIR   = self.ADDONS_DATA_DIR.pjoin(__addon_id__)
        self.ADDONS_CODE_DIR  = self.HOME_DIR.pjoin('addons')
        self.ADDON_CODE_DIR   = self.ADDONS_CODE_DIR.pjoin(__addon_id__)
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
        self.LAUNCH_LOG_FILE_PATH      = self.ADDON_DATA_DIR.pjoin('launcher.log')
        self.RECENT_PLAYED_FILE_PATH   = self.ADDON_DATA_DIR.pjoin('history.json')
        self.MOST_PLAYED_FILE_PATH     = self.ADDON_DATA_DIR.pjoin('most_played.json')

        # Reports
        self.BIOS_REPORT_FILE_PATH = self.ADDON_DATA_DIR.pjoin('report_BIOS.txt')
        self.LAUNCHER_REPORT_FILE_PATH = self.ADDON_DATA_DIR.pjoin('report_Launchers.txt')
        self.ROM_SYNC_REPORT_FILE_PATH = self.ADDON_DATA_DIR.pjoin('report_ROM_sync_status.txt')
        self.ROM_ART_INTEGRITY_REPORT_FILE_PATH = self.ADDON_DATA_DIR.pjoin('report_ROM_artwork_integrity.txt')

        # --- Offline scraper databases ---
        self.GAMEDB_INFO_DIR           = self.ADDON_CODE_DIR.pjoin('data-AOS')
        self.GAMEDB_JSON_BASE_NOEXT    = 'AOS_GameDB_info'
        # self.LAUNCHBOX_INFO_DIR        = self.ADDON_CODE_DIR.pjoin('LaunchBox')
        # self.LAUNCHBOX_JSON_BASE_NOEXT = 'LaunchBox_info'

        # --- Online scraper on-disk cache ---
        self.SCRAPER_CACHE_DIR = self.ADDON_DATA_DIR.pjoin('ScraperCache')

        # --- Artwork and NFO for Categories and Launchers ---
        self.DEFAULT_CAT_ASSET_DIR     = self.ADDON_DATA_DIR.pjoin('asset-categories')
        self.DEFAULT_COL_ASSET_DIR     = self.ADDON_DATA_DIR.pjoin('asset-collections')
        self.DEFAULT_LAUN_ASSET_DIR    = self.ADDON_DATA_DIR.pjoin('asset-launchers')
        self.DEFAULT_FAV_ASSET_DIR     = self.ADDON_DATA_DIR.pjoin('asset-favourites')
        self.VIRTUAL_CAT_TITLE_DIR     = self.ADDON_DATA_DIR.pjoin('db_title')
        self.VIRTUAL_CAT_YEARS_DIR     = self.ADDON_DATA_DIR.pjoin('db_year')
        self.VIRTUAL_CAT_GENRE_DIR     = self.ADDON_DATA_DIR.pjoin('db_genre')
        self.VIRTUAL_CAT_DEVELOPER_DIR = self.ADDON_DATA_DIR.pjoin('db_developer')
        self.VIRTUAL_CAT_NPLAYERS_DIR  = self.ADDON_DATA_DIR.pjoin('db_nplayer')
        self.VIRTUAL_CAT_ESRB_DIR      = self.ADDON_DATA_DIR.pjoin('db_esrb')
        self.VIRTUAL_CAT_RATING_DIR    = self.ADDON_DATA_DIR.pjoin('db_rating')
        self.VIRTUAL_CAT_CATEGORY_DIR  = self.ADDON_DATA_DIR.pjoin('db_category')
        self.ROMS_DIR                  = self.ADDON_DATA_DIR.pjoin('db_ROMs')
        self.COLLECTIONS_DIR           = self.ADDON_DATA_DIR.pjoin('db_Collections')
        self.REPORTS_DIR               = self.ADDON_DATA_DIR.pjoin('reports')

# --- Global variables ---
g_PATHS = AEL_Paths()

#
# Make AEL to run only 1 single instance
# See http://forum.kodi.tv/showthread.php?tid=310697
#
monitor           = xbmc.Monitor()
main_window       = xbmcgui.Window(10000)
AEL_LOCK_PROPNAME = 'AEL_instance_lock'
AEL_LOCK_VALUE    = 'True'

# Audit reports constants
AUDIT_REPORT_ALL = 'AUDIT_REPORT_ALL'
AUDIT_REPORT_NOINTRO = 'AUDIT_REPORT_NOINTRO'
AUDIT_REPORT_REDUMP = 'AUDIT_REPORT_REDUMP'

class SingleInstance:
    def __enter__(self):
        # --- If property is True then another instance of AEL is running ---
        if main_window.getProperty(AEL_LOCK_PROPNAME) == AEL_LOCK_VALUE:
            log_warning('SingleInstance::__enter__() Lock in use. Aborting AEL execution')
            # >> Apparently this message pulls the focus out of the launcher app. Disable it.
            # >> Has not effect. Kodi steals the focus from the launched app even if not message.
            kodi_dialog_OK('Another instance of AEL is running! Wait until the scraper finishes '
                           'or close the launched application before launching a new one and try '
                           'again.')
            raise SystemExit
        if monitor.abortRequested():
            log_info('monitor.abortRequested() is True. Exiting plugin ...')
            raise SystemExit

        # --- Acquire lock for this instance ---
        log_debug('SingleInstance::__enter__() Lock not in use. Setting lock')
        main_window.setProperty(AEL_LOCK_PROPNAME, AEL_LOCK_VALUE)
        return True

    def __exit__(self, type, value, traceback):
        # --- Print information about exception if any ---
        # >> If type == value == tracebak == None no exception happened
        if type:
            log_error('SingleInstance::__exit__() Unhandled excepcion in protected code')

        # --- Release lock even if an exception happened ---
        log_debug('SingleInstance::__exit__() Releasing lock')
        main_window.setProperty(AEL_LOCK_PROPNAME, '')

#
# Main code
#
class Main:
    # ---------------------------------------------------------------------------------------------
    # This is the plugin entry point.
    # ---------------------------------------------------------------------------------------------
    def run_plugin(self):
        # --- Initialise log system ---
        # Force DEBUG log level for development.
        # Place it before settings loading so settings can be dumped during debugging.
        #set_log_level(LOG_DEBUG)

        # --- Fill in settings dictionary using __addon_obj__.getSetting() ---
        self._get_settings()
        #set_log_level(self.settings['log_level'])
        set_log_level(LOG_DEBUG)

        # --- Some debug stuff for development ---
        log_debug('---------- Called AEL Main::run_plugin() constructor ----------')
        log_debug('sys.platform   "{}"'.format(sys.platform))
        # log_debug('WindowId       "{}"'.format(xbmcgui.getCurrentWindowId()))
        # log_debug('WindowName     "{}"'.format(xbmc.getInfoLabel('Window.Property(xmlfile)')))
        log_debug('Python version "' + sys.version.replace('\n', '') + '"')
        # log_debug('__a_name__     "{0}"'.format(__addon_name__))
        log_debug('__a_id__       "{}"'.format(__addon_id__))
        log_debug('__a_version__  "{}"'.format(__addon_version__))
        # log_debug('__a_author__   "{}"'.format(__addon_author__))
        # log_debug('__a_profile__  "{}"'.format(__addon_profile__))
        # log_debug('__a_type__     "{}"'.format(__addon_type__))
        for i in range(len(sys.argv)): log_debug('sys.argv[{}] "{}"'.format(i, sys.argv[i]))
        # log_debug('PLUGIN_DATA_DIR OP "{}"'.format(g_PATHS.PLUGIN_DATA_DIR.getOriginalPath()))
        # log_debug('PLUGIN_DATA_DIR  P "{}"'.format(g_PATHS.PLUGIN_DATA_DIR.getPath()))
        # log_debug('ADDON_CODE_DIR OP "{}"'.format(g_PATHS.ADDON_CODE_DIR.getOriginalPath()))
        # log_debug('ADDON_CODE_DIR  P "{}"'.format(g_PATHS.ADDON_CODE_DIR.getPath()))

        # --- Get DEBUG information for the log --
        if self.settings['log_level'] == LOG_DEBUG:
            json_rpc_start = time.time()

            # Properties: Kodi name and version
            p_dic = {'properties' : ['name', 'version']}
            response_props = kodi_jsonrpc_dict('Application.GetProperties', p_dic)
            # Skin in use
            p_dic = {'setting' : 'lookandfeel.skin'}
            response_skin = kodi_jsonrpc_dict('Settings.GetSettingValue', p_dic)

            # Print time consumed by JSON RPC calls
            json_rpc_end = time.time()
            # log_debug('JSON RPC time {0:.3f} ms'.format((json_rpc_end - json_rpc_start) * 1000))

            # Parse returned JSON and nice print.
            r_name = response_props['name']
            r_major = response_props['version']['major']
            r_minor = response_props['version']['minor']
            r_revision = response_props['version']['revision']
            r_tag = response_props['version']['tag']
            r_skin = response_skin['value']
            log_debug('JSON version "{}" "{}" "{}" "{}" "{}"'.format(
                r_name, r_major, r_minor, r_revision, r_tag))
            log_debug('JSON skin    "{}"'.format(r_skin))

            # --- Save all Kodi settings into a file for DEBUG ---
            # c_str = ('{"id" : 1, "jsonrpc" : "2.0",'
            #          ' "method" : "Settings.GetSettings",'
            #          ' "params" : {"level":"expert"}}')
            # response = xbmc.executeJSONRPC(c_str)
            # log_debug('JSON      "{}"'.format(c_str))
            # log_debug('Response  "{}"'.format(response))

        # Kiosk mode for skins.
        # Do not change context menus with listitem.addContextMenuItems() in Kiosk mode.
        # In other words, change the CM if Kiosk mode is disabled.
        self.g_kiosk_mode_disabled = xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")

        # --- Addon data paths creation ---
        if not g_PATHS.ADDON_DATA_DIR.exists():            g_PATHS.ADDON_DATA_DIR.makedirs()
        if not g_PATHS.SCRAPER_CACHE_DIR.exists():         g_PATHS.SCRAPER_CACHE_DIR.makedirs()
        if not g_PATHS.DEFAULT_CAT_ASSET_DIR.exists():     g_PATHS.DEFAULT_CAT_ASSET_DIR.makedirs()
        if not g_PATHS.DEFAULT_COL_ASSET_DIR.exists():     g_PATHS.DEFAULT_COL_ASSET_DIR.makedirs()
        if not g_PATHS.DEFAULT_LAUN_ASSET_DIR.exists():    g_PATHS.DEFAULT_LAUN_ASSET_DIR.makedirs()
        if not g_PATHS.DEFAULT_FAV_ASSET_DIR.exists():     g_PATHS.DEFAULT_FAV_ASSET_DIR.makedirs()
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

        # --- Process URL ---
        self.base_url     = sys.argv[0]
        self.addon_handle = int(sys.argv[1])
        args              = urllib.parse.parse_qs(sys.argv[2][1:])
        # log_debug('args = {0}'.format(args))
        # >> Interestingly, if plugin is called as type executable then args is empty.
        # >> However, if plugin is called as type video then Kodi adds the following
        # >> even for the first call: 'content_type': ['video']
        self.content_type = args['content_type'] if 'content_type' in args else None
        # log_debug('content_type = {0}'.format(self.content_type))

        # --- Addon first-time initialisation ---
        # >> When the addon is installed and the file categories.xml does not exist, just
        #    create an empty one with a default launcher.
        # >> NOTE Not needed anymore. Skins using shortcuts and/or widgets will call AEL concurrently
        #         and AEL should return an empty list with no GUI warnings or dialogs.
        # if not CATEGORIES_FILE_PATH.exists():
        #     kodi_dialog_OK('It looks it is the first time you run Advanced Emulator Launcher! ' +
        #                    'A default categories.xml has been created. You can now customise it to your needs.')
        #     self._cat_create_default()
        #     fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

        # --- Load categories.xml and fill categories and launchers dictionaries ---
        self.categories = {}
        self.launchers = {}
        self.update_timestamp = fs_load_catfile(g_PATHS.CATEGORIES_FILE_PATH, self.categories, self.launchers)

        # --- Get addon command ---
        command = args['com'][0] if 'com' in args else 'SHOW_ADDON_ROOT'
        log_debug('command = "{0}"'.format(command))

        # --- Commands that do not modify the databases are allowed to run concurrently ---
        concurrent_command_set = {
            'SHOW_ADDON_ROOT',
            'SHOW_VCATEGORIES_ROOT',
            'SHOW_AEL_OFFLINE_LAUNCHERS_ROOT',
            'SHOW_LB_OFFLINE_LAUNCHERS_ROOT',
            'SHOW_FAVOURITES',
            'SHOW_VIRTUAL_CATEGORY',
            'SHOW_RECENTLY_PLAYED',
            'SHOW_MOST_PLAYED',
            'SHOW_UTILITIES_VLAUNCHERS',
            'SHOW_GLOBALREPORTS_VLAUNCHERS',
            'SHOW_COLLECTIONS',
            'SHOW_COLLECTION_ROMS',
            'SHOW_LAUNCHERS',
            'SHOW_ROMS',
            'SHOW_VLAUNCHER_ROMS',
            'SHOW_AEL_SCRAPER_ROMS',
            'SHOW_LB_SCRAPER_ROMS',
            'EXEC_SHOW_CLONE_ROMS',
            'SHOW_CLONE_ROMS',
            'SHOW_ALL_CATEGORIES',
            'SHOW_ALL_LAUNCHERS',
            'SHOW_ALL_ROMS',
            'BUILD_GAMES_MENU',
        }
        if command in concurrent_command_set:
            self.run_concurrent(command, args)
        else:
            # Ensure AEL only runs one instance at a time
            with SingleInstance():
                self.run_protected(command, args)
        log_debug('Advanced Emulator Launcher run_plugin() exit')

    #
    # This function may run concurrently
    #
    def run_concurrent(self, command, args):
        log_debug('Advanced Emulator Launcher run_concurrent() BEGIN')

        # --- Name says it all ---
        if command == 'SHOW_ADDON_ROOT':
            self._command_render_root_window()

        # --- Render launchers stuff ---
        elif command == 'SHOW_VCATEGORIES_ROOT':
            self._gui_render_vcategories_root()
        elif command == 'SHOW_AEL_OFFLINE_LAUNCHERS_ROOT':
            self._gui_render_AEL_scraper_launchers()
        elif command == 'SHOW_LB_OFFLINE_LAUNCHERS_ROOT':
            self._gui_render_LB_scraper_launchers()
        elif command == 'SHOW_FAVOURITES':
            self._command_render_favourites()
        elif command == 'SHOW_VIRTUAL_CATEGORY':
            self._command_render_virtual_category(args['catID'][0])
        elif command == 'SHOW_RECENTLY_PLAYED':
            self._command_render_recently_played()
        elif command == 'SHOW_MOST_PLAYED':
            self._command_render_most_played()
        elif command == 'SHOW_UTILITIES_VLAUNCHERS':
            self._gui_render_Utilities_vlaunchers()
        elif command == 'SHOW_GLOBALREPORTS_VLAUNCHERS':
            self._gui_render_GlobalReports_vlaunchers()

        elif command == 'SHOW_COLLECTIONS':
            self._command_render_collections()
        elif command == 'SHOW_COLLECTION_ROMS':
            self._command_render_collection_ROMs(args['catID'][0], args['launID'][0])
        elif command == 'SHOW_LAUNCHERS':
            self._command_render_launchers(args['catID'][0])

        # --- Show ROMs in launcher/virtual launcher ---
        elif command == 'SHOW_ROMS':
            self._command_render_roms(args['catID'][0], args['launID'][0])
        elif command == 'SHOW_VLAUNCHER_ROMS':
            self._command_render_virtual_launcher_roms(args['catID'][0], args['launID'][0])
        elif command == 'SHOW_AEL_SCRAPER_ROMS':
            self._command_render_AEL_scraper_roms(args['catID'][0])
        elif command == 'SHOW_LB_SCRAPER_ROMS':
            self._command_render_LB_scraper_roms(args['catID'][0])
        # Auxiliar command to render clone ROM list from context menu in Parent/Clone mode.
        elif command == 'EXEC_SHOW_CLONE_ROMS':
            url = self._misc_url('SHOW_CLONE_ROMS', args['catID'][0], args['launID'][0], args['romID'][0])
            xbmc.executebuiltin('Container.Update({0})'.format(url))
        elif command == 'SHOW_CLONE_ROMS':
            self._command_render_clone_roms(args['catID'][0], args['launID'][0], args['romID'][0])

        # --- Skin commands ---
        # This commands render Categories/Launcher/ROMs and are used by skins to build shortcuts.
        # Do not render virtual launchers.
        # NOTE Renamed this to follow a scheme like in AML, _skin_zxczxcxzc()
        elif command == 'SHOW_ALL_CATEGORIES':
            self._command_render_all_categories()
        elif command == 'SHOW_ALL_LAUNCHERS':
            self._command_render_all_launchers()
        elif command == 'SHOW_ALL_ROMS':
            self._command_render_all_ROMs()

        # >> Command to build/fill the menu with categories or launcher using skinshortcuts
        elif command == 'BUILD_GAMES_MENU':
            self._command_buildMenu()

        # >> Unknown command
        else:
            kodi_dialog_OK('Unknown command {0}'.format(args['com'][0]) )
        log_debug('Advanced Emulator Launcher run_concurrent() END')

    #
    # This function is guaranteed to run with no concurrency.
    #
    def run_protected(self, command, args):
        log_debug('Advanced Emulator Launcher run_protected() BEGIN')

        # --- Category management ---
        if command == 'ADD_CATEGORY':
            self._command_add_new_category()
        elif command == 'EDIT_CATEGORY':
            self._command_edit_category(args['catID'][0])

        # --- Launcher management ---
        elif command == 'ADD_LAUNCHER':
            self._command_add_new_launcher(args['catID'][0])
        elif command == 'ADD_LAUNCHER_ROOT':
            self._command_add_new_launcher(VCATEGORY_ADDONROOT_ID)
        elif command == 'EDIT_LAUNCHER':
            self._command_edit_launcher(args['catID'][0], args['launID'][0])

        # --- ROM management ---
        elif command == 'SCAN_ROMS':
            self._roms_import_roms(args['launID'][0])
        elif command == 'EDIT_ROM':
            self._command_edit_rom(args['catID'][0], args['launID'][0], args['romID'][0])

        # --- Launch ROM or standalone launcher ---
        elif command == 'LAUNCH_ROM':
            self._command_run_rom(args['catID'][0], args['launID'][0], args['romID'][0])
        elif command == 'LAUNCH_STANDALONE':
            self._command_run_standalone_launcher(args['catID'][0], args['launID'][0])

        # --- Favourite/ROM Collection management ---
        elif command == 'ADD_TO_FAV':
            self._command_add_to_favourites(args['catID'][0], args['launID'][0], args['romID'][0])
        elif command == 'ADD_TO_COLLECTION':
            self._command_add_ROM_to_collection(args['catID'][0], args['launID'][0], args['romID'][0])
        elif command == 'ADD_COLLECTION':
            self._command_add_collection()
        elif command == 'EDIT_COLLECTION':
            self._command_edit_collection(args['catID'][0], args['launID'][0])
        elif command == 'DELETE_COLLECTION':
            self._command_delete_collection(args['catID'][0], args['launID'][0])

        elif command == 'IMPORT_COLLECTION':
            self._command_import_collection()
        elif command == 'EXPORT_COLLECTION':
            self._command_export_collection(args['catID'][0], args['launID'][0])

        # Manages Favourites and ROM Collections.
        elif command == 'MANAGE_FAV':
            self._command_manage_favourites(args['catID'][0], args['launID'][0], args['romID'][0])

        elif command == 'MANAGE_RECENT_PLAYED':
            rom_ID  = args['romID'][0] if 'romID'  in args else ''
            self._command_manage_recently_played(rom_ID)

        elif command == 'MANAGE_MOST_PLAYED':
            rom_ID  = args['romID'][0] if 'romID'  in args else ''
            self._command_manage_most_played(rom_ID)

        # --- Searches ---
        # This command is issued when user clicks on "Search" on the context menu of a launcher
        # in the launchers view, or context menu inside a launcher. User is asked to enter the
        # search string and the field to search (name, category, etc.). Then, EXEC_SEARCH_LAUNCHER
        # command is called.
        elif command == 'SEARCH_LAUNCHER':
            self._command_search_launcher(args['catID'][0], args['launID'][0])
        elif command == 'EXECUTE_SEARCH_LAUNCHER':
            # >> Deal with empty search strings
            if 'search_string' not in args: args['search_string'] = [ '' ]
            self._command_execute_search_launcher(
                args['catID'][0], args['launID'][0],
                args['search_type'][0], args['search_string'][0])

        # >> Shows info about categories/launchers/ROMs and reports
        elif command == 'VIEW':
            catID  = args['catID'][0]                              # >> Mandatory
            launID = args['launID'][0] if 'launID' in args else '' # >> Optional
            romID  = args['romID'][0] if 'romID'  in args else ''  # >> Optional
            self._command_view_menu(catID, launID, romID)
        elif command == 'VIEW_OS_ROM':
            self._command_view_offline_scraper_rom(args['catID'][0], args['launID'][0], args['romID'][0])

        # >> Update virtual categories databases
        elif command == 'UPDATE_VIRTUAL_CATEGORY':
            self._command_update_virtual_category_db(args['catID'][0])
        elif command == 'UPDATE_ALL_VCATEGORIES':
            self._command_update_virtual_category_db_all()

        # Commands called from Utilities menu.
        elif command == 'EXECUTE_UTILS_IMPORT_LAUNCHERS': self._command_exec_utils_import_launchers()
        elif command == 'EXECUTE_UTILS_EXPORT_LAUNCHERS': self._command_exec_utils_export_launchers()

        elif command == 'EXECUTE_UTILS_CHECK_DATABASE': self._command_exec_utils_check_database()
        elif command == 'EXECUTE_UTILS_CHECK_LAUNCHERS': self._command_exec_utils_check_launchers()
        elif command == 'EXECUTE_UTILS_CHECK_LAUNCHER_SYNC_STATUS': self._command_exec_utils_check_launcher_sync_status()
        elif command == 'EXECUTE_UTILS_CHECK_ARTWORK_INTEGRITY': self._command_exec_utils_check_artwork_integrity()
        elif command == 'EXECUTE_UTILS_CHECK_ROM_ARTWORK_INTEGRITY': self._command_exec_utils_check_ROM_artwork_integrity()
        elif command == 'EXECUTE_UTILS_DELETE_REDUNDANT_ARTWORK': self._command_exec_utils_delete_redundant_artwork()
        elif command == 'EXECUTE_UTILS_DELETE_ROM_REDUNDANT_ARTWORK': self._command_exec_utils_delete_ROM_redundant_artwork()
        elif command == 'EXECUTE_UTILS_SHOW_DETECTED_DATS': self._command_exec_utils_show_DATs()
        elif command == 'EXECUTE_UTILS_CHECK_RETRO_LAUNCHERS': self._command_exec_utils_check_retro_launchers()
        elif command == 'EXECUTE_UTILS_CHECK_RETRO_BIOS': self._command_exec_utils_check_retro_BIOS()

        elif command == 'EXECUTE_UTILS_TGDB_CHECK': self._command_exec_utils_TGDB_check()
        elif command == 'EXECUTE_UTILS_MOBYGAMES_CHECK': self._command_exec_utils_MobyGames_check()
        elif command == 'EXECUTE_UTILS_SCREENSCRAPER_CHECK': self._command_exec_utils_ScreenScraper_check()
        elif command == 'EXECUTE_UTILS_ARCADEDB_CHECK': self._command_exec_utils_ArcadeDB_check()

        # Commands called from Global Reports menu.
        elif command == 'EXECUTE_GLOBAL_ROM_STATS': self._command_exec_global_rom_stats()
        elif command == 'EXECUTE_GLOBAL_AUDIT_STATS_ALL':
            self._command_exec_global_audit_stats(AUDIT_REPORT_ALL)
        elif command == 'EXECUTE_GLOBAL_AUDIT_STATS_NOINTRO':
            self._command_exec_global_audit_stats(AUDIT_REPORT_NOINTRO)
        elif command == 'EXECUTE_GLOBAL_AUDIT_STATS_REDUMP':
            self._command_exec_global_audit_stats(AUDIT_REPORT_REDUMP)

        # Unknown command
        else:
            kodi_dialog_OK('Unknown command {0}'.format(args['com'][0]) )
        log_debug('Advanced Emulator Launcher run_protected() END')

    #
    # Get Addon Settings
    #
    def _get_settings(self):
        # Get the users preference settings
        o = __addon_obj__
        self.settings = {}

        # --- ROM Scanner settings ---
        self.settings['scan_recursive']          = True if o.getSetting('scan_recursive') == 'true' else False
        self.settings['scan_ignore_bios']        = True if o.getSetting('scan_ignore_bios') == 'true' else False
        self.settings['scan_ignore_scrap_title'] = True if o.getSetting('scan_ignore_scrap_title') == 'true' else False
        self.settings['scan_clean_tags']         = True if o.getSetting('scan_clean_tags') == 'true' else False
        self.settings['scan_update_NFO_files']   = True if o.getSetting('scan_update_NFO_files') == 'true' else False

        # --- ROM scraping ---
        # Scanner settings
        self.settings['scan_metadata_policy'] = int(o.getSetting('scan_metadata_policy'))
        self.settings['scan_asset_policy']    = int(o.getSetting('scan_asset_policy'))
        self.settings['game_selection_mode']  = int(o.getSetting('game_selection_mode'))
        self.settings['asset_selection_mode'] = int(o.getSetting('asset_selection_mode'))
        # Scanner scrapers
        self.settings['scraper_metadata']      = int(o.getSetting('scraper_metadata'))
        self.settings['scraper_asset']         = int(o.getSetting('scraper_asset'))
        self.settings['scraper_metadata_MAME'] = int(o.getSetting('scraper_metadata_MAME'))
        self.settings['scraper_asset_MAME']    = int(o.getSetting('scraper_asset_MAME'))

        # --- Misc settings ---
        self.settings['scraper_mobygames_apikey']     = o.getSetting('scraper_mobygames_apikey')
        self.settings['scraper_screenscraper_ssid']   = o.getSetting('scraper_screenscraper_ssid')
        self.settings['scraper_screenscraper_sspass'] = o.getSetting('scraper_screenscraper_sspass')

        self.settings['scraper_screenscraper_region']   = int(o.getSetting('scraper_screenscraper_region'))
        self.settings['scraper_screenscraper_language'] = int(o.getSetting('scraper_screenscraper_language'))

        self.settings['io_retroarch_sys_dir']        = o.getSetting('io_retroarch_sys_dir')
        self.settings['io_retroarch_only_mandatory'] = True if o.getSetting('io_retroarch_only_mandatory') == 'true' else False

        # --- ROM audit ---
        self.settings['audit_unknown_roms']         = int(o.getSetting('audit_unknown_roms'))
        self.settings['audit_pclone_assets']        = True if o.getSetting('audit_pclone_assets') == 'true' else False
        self.settings['audit_nointro_dir']          = o.getSetting('audit_nointro_dir')
        self.settings['audit_redump_dir']           = o.getSetting('audit_redump_dir')

        # self.settings['audit_1G1R_first_region']     = int(o.getSetting('audit_1G1R_first_region'))
        # self.settings['audit_1G1R_second_region']   = int(o.getSetting('audit_1G1R_second_region'))
        # self.settings['audit_1G1R_third_region']   = int(o.getSetting('audit_1G1R_third_region'))

        # --- Display ---
        self.settings['display_category_mode']    = int(o.getSetting('display_category_mode'))
        self.settings['display_launcher_notify']  = True if o.getSetting('display_launcher_notify') == 'true' else False
        self.settings['display_hide_finished']    = True if o.getSetting('display_hide_finished') == 'true' else False
        self.settings['display_launcher_roms']    = True if o.getSetting('display_launcher_roms') == 'true' else False

        self.settings['display_rom_in_fav']       = True if o.getSetting('display_rom_in_fav') == 'true' else False
        self.settings['display_nointro_stat']     = True if o.getSetting('display_nointro_stat') == 'true' else False
        self.settings['display_fav_status']       = True if o.getSetting('display_fav_status') == 'true' else False

        self.settings['display_hide_favs']        = True if o.getSetting('display_hide_favs') == 'true' else False
        self.settings['display_hide_collections'] = True if o.getSetting('display_hide_collections') == 'true' else False
        self.settings['display_hide_vlaunchers']  = True if o.getSetting('display_hide_vlaunchers') == 'true' else False
        self.settings['display_hide_AEL_scraper'] = True if o.getSetting('display_hide_AEL_scraper') == 'true' else False
        self.settings['display_hide_recent']      = True if o.getSetting('display_hide_recent') == 'true' else False
        self.settings['display_hide_mostplayed']  = True if o.getSetting('display_hide_mostplayed') == 'true' else False
        self.settings['display_hide_utilities']   = True if o.getSetting('display_hide_utilities') == 'true' else False
        self.settings['display_hide_g_reports']   = True if o.getSetting('display_hide_g_reports') == 'true' else False

        # --- Paths ---
        self.settings['categories_asset_dir']     = o.getSetting('categories_asset_dir')
        self.settings['launchers_asset_dir']      = o.getSetting('launchers_asset_dir')
        self.settings['favourites_asset_dir']     = o.getSetting('favourites_asset_dir')
        self.settings['collections_asset_dir']    = o.getSetting('collections_asset_dir')

        # --- Advanced ---
        self.settings['media_state_action'] = int(o.getSetting('media_state_action'))
        self.settings['delay_tempo'] = int(round(float(o.getSetting('delay_tempo'))))
        self.settings['suspend_audio_engine'] = True if o.getSetting('suspend_audio_engine') == 'true' else False
        self.settings['suspend_screensaver'] = True if o.getSetting('suspend_screensaver') == 'true' else False
        # self.settings['suspend_joystick_engine'] = True if o.getSetting('suspend_joystick_engine') == 'true' else False
        self.settings['escape_romfile'] = True if o.getSetting('escape_romfile') == 'true' else False
        self.settings['lirc_state'] = True if o.getSetting('lirc_state') == 'true' else False
        self.settings['show_batch_window'] = True if o.getSetting('show_batch_window') == 'true' else False
        self.settings['windows_close_fds'] = True if o.getSetting('windows_close_fds') == 'true' else False
        self.settings['windows_cd_apppath'] = True if o.getSetting('windows_cd_apppath') == 'true' else False
        self.settings['log_level'] = int(o.getSetting('log_level'))

        # Check if user changed default artwork paths for categories/launchers. If not, set defaults.
        if self.settings['categories_asset_dir'] == '':
            self.settings['categories_asset_dir'] = g_PATHS.DEFAULT_CAT_ASSET_DIR.getOriginalPath()
        if self.settings['launchers_asset_dir'] == '':
            self.settings['launchers_asset_dir'] = g_PATHS.DEFAULT_LAUN_ASSET_DIR.getOriginalPath()
        if self.settings['favourites_asset_dir'] == '':
            self.settings['favourites_asset_dir'] = g_PATHS.DEFAULT_FAV_ASSET_DIR.getOriginalPath()
        if self.settings['collections_asset_dir'] == '':
            self.settings['collections_asset_dir'] = g_PATHS.DEFAULT_COL_ASSET_DIR.getOriginalPath()

        # Settings required by the scrapers (they are not really settings).
        self.settings['scraper_screenscraper_AEL_softname'] = 'AEL_{}'.format(__addon_version__)
        self.settings['scraper_aeloffline_addon_code_dir'] = g_PATHS.ADDON_CODE_DIR.getPath()
        self.settings['scraper_cache_dir'] = g_PATHS.SCRAPER_CACHE_DIR.getPath()

        # --- Dump settings for DEBUG ---
        # log_debug('Settings dump BEGIN')
        # for key in sorted(self.settings):
        #     log_debug('{0} --> {1:10s} {2}'.format(key.rjust(21), str(self.settings[key]), type(self.settings[key])))
        # log_debug('Settings dump END')

    #
    # Set Sorting methods
    #
    def _misc_set_default_sorting_method(self):
        # >> This must be called only if self.addon_handle > 0, otherwise Kodi will complain in the log.
        if self.addon_handle < 0: return
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)

    def _misc_set_all_sorting_methods(self):
        # >> This must be called only if self.addon_handle > 0, otherwise Kodi will complain in the log.
        if self.addon_handle < 0: return
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_STUDIO)
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_GENRE)
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)

    #
    # Set the AEL content type. It is a Window property used by skins to know if AEL is rendering
    # a Window that has categories/launchers or ROMs.
    #
    def _misc_set_AEL_Content(self, AEL_Content_Value):
        if AEL_Content_Value == AEL_CONTENT_VALUE_LAUNCHERS:
            log_debug('_misc_set_AEL_Content() Setting Window({0}) '.format(AEL_CONTENT_WINDOW_ID) +
                      'property "{0}" = "{1}"'.format(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_LAUNCHERS))
            xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_LAUNCHERS)
        elif AEL_Content_Value == AEL_CONTENT_VALUE_ROMS:
            log_debug('_misc_set_AEL_Content() Setting Window({0}) '.format(AEL_CONTENT_WINDOW_ID) +
                      'property "{0}" = "{1}"'.format(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROMS))
            xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROMS)
        elif AEL_Content_Value == AEL_CONTENT_VALUE_NONE:
            log_debug('_misc_set_AEL_Content() Setting Window({0}) '.format(AEL_CONTENT_WINDOW_ID) +
                      'property "{0}" = "{1}"'.format(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_NONE))
            xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_NONE)
        else:
            log_error('_misc_set_AEL_Content() Invalid AEL_Content_Value "{0}"'.format(AEL_Content_Value))

    def _misc_set_AEL_Launcher_Content(self, launcher_dic):
        kodi_thumb     = 'DefaultFolder.png' if launcher_dic['rompath'] else 'DefaultProgram.png'
        icon_path      = asset_get_default_asset_Category(launcher_dic, 'default_icon', kodi_thumb)
        clearlogo_path = asset_get_default_asset_Category(launcher_dic, 'default_clearlogo')
        xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_LAUNCHER_NAME_LABEL, launcher_dic['m_name'])
        xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_LAUNCHER_ICON_LABEL, icon_path)
        xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_LAUNCHER_CLEARLOGO_LABEL, clearlogo_path)

    def _misc_clear_AEL_Launcher_Content(self):
        xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_LAUNCHER_NAME_LABEL, '')
        xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_LAUNCHER_ICON_LABEL, '')
        xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_LAUNCHER_CLEARLOGO_LABEL, '')

    def _command_add_new_category(self):
        dialog = xbmcgui.Dialog()
        keyboard = xbmc.Keyboard('', 'New Category Name')
        keyboard.doModal()
        if not keyboard.isConfirmed(): return

        category = fs_new_category()
        categoryID = misc_generate_random_SID()
        category['id']     = categoryID
        category['m_name'] = keyboard.getText()
        self.categories[categoryID] = category
        fs_write_catfile(g_PATHS.CATEGORIES_FILE_PATH, self.categories, self.launchers)
        kodi_notify('Category {0} created'.format(category['m_name']))
        kodi_refresh_container()

    def _command_edit_category(self, categoryID):
        # --- Shows a select box with the options to edit ---
        dialog = xbmcgui.Dialog()
        finished_str = 'Finished' if self.categories[categoryID]['finished'] == True else 'Unfinished'
        type = dialog.select('Select action for Category {0}'.format(self.categories[categoryID]['m_name']),
                             ['Edit Metadata ...',
                              'Edit Assets/Artwork ...',
                              'Choose default Assets/Artwork ...',
                              'Category status: {0}'.format(finished_str),
                              'Export Category XML configuration ...',
                              'Delete Category'])
        if type < 0: return

        # --- Edit category metadata ---
        if type == 0:
            NFO_FileName = fs_get_category_NFO_name(self.settings, self.categories[categoryID])
            NFO_str = 'NFO found' if NFO_FileName.exists() else 'NFO not found'
            plot_str = text_limit_string(self.categories[categoryID]['m_plot'], PLOT_STR_MAXSIZE)
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Edit Category Metadata',
                                  ["Edit Title: '{0}'".format(self.categories[categoryID]['m_name']),
                                   "Edit Release Year: '{0}'".format(self.categories[categoryID]['m_year']),
                                   "Edit Genre: '{0}'".format(self.categories[categoryID]['m_genre']),
                                   "Edit Developer: '{0}'".format(self.categories[categoryID]['m_developer']),
                                   "Edit Rating: '{0}'".format(self.categories[categoryID]['m_rating']),
                                   "Edit Plot: '{0}'".format(plot_str),
                                   'Import NFO file (default, {0})'.format(NFO_str),
                                   'Import NFO file (browse NFO file) ...',
                                   'Save NFO file (default location)'])
            if type2 < 0: return

            # --- Edition of the category name ---
            if type2 == 0:
                keyboard = xbmc.Keyboard(self.categories[categoryID]['m_name'], 'Edit Title')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                title = keyboard.getText()
                if title == '': title = self.categories[categoryID]['m_name']
                new_title_str = title.strip()
                self.categories[categoryID]['m_name'] = new_title_str
                kodi_notify('Category Title is now {0}'.format(new_title_str))

            # --- Edition of the category release date (year) ---
            elif type2 == 1:
                old_year_str = self.categories[categoryID]['m_year']
                keyboard = xbmc.Keyboard(old_year_str, 'Edit Category release year')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                new_year_str = keyboard.getText()
                if old_year_str == new_year_str:
                    kodi_notify('Category Year not changed')
                    return
                self.categories[categoryID]['m_year'] = new_year_str
                kodi_notify('Category Year is now {0}'.format(new_year_str))

            # --- Edition of the category genre ---
            elif type2 == 2:
                keyboard = xbmc.Keyboard(self.categories[categoryID]['m_genre'], 'Edit Genre')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                new_genre_str = keyboard.getText()
                self.categories[categoryID]['m_genre'] = new_genre_str
                kodi_notify('Category Genre is now {0}'.format(new_genre_str))

            # --- Edition of the category developer ---
            elif type2 == 3:
                old_developer_str = self.categories[categoryID]['m_developer']
                keyboard = xbmc.Keyboard(old_developer_str, 'Edit developer')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                new_developer_str = keyboard.getText()
                if old_developer_str == new_developer_str:
                    kodi_notify('Category Developer not changed')
                    return
                self.categories[categoryID]['m_developer'] = new_developer_str
                kodi_notify('Category Developer is now {0}'.format(new_developer_str))

            # --- Edition of the category rating ---
            elif type2 == 4:
                rating = dialog.select('Edit Category Rating',
                                      ['Not set',  'Rating 0', 'Rating 1', 'Rating 2', 'Rating 3', 'Rating 4',
                                       'Rating 5', 'Rating 6', 'Rating 7', 'Rating 8', 'Rating 9', 'Rating 10'])
                # >> Rating not set, empty string
                if rating == 0:
                    self.categories[categoryID]['m_rating'] = ''
                    kodi_notify('Category Rating changed to Not Set')
                elif rating >= 1 and rating <= 11:
                    self.categories[categoryID]['m_rating'] = '{0}'.format(rating - 1)
                    kodi_notify('Category Rating is now {0}'.format(self.categories[categoryID]['m_rating']))
                elif rating < 0:
                    kodi_notify('Category rating not changed')
                    return

            # --- Edition of the plot (description) ---
            elif type2 == 5:
                old_plot_str = self.categories[categoryID]['m_plot']
                keyboard = xbmc.Keyboard(self.categories[categoryID]['m_plot'], 'Edit Plot')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                new_plot_str = keyboard.getText()
                if old_plot_str == new_plot_str:
                    kodi_notify('Category Plot not changed')
                    return
                self.categories[categoryID]['m_plot'] = new_plot_str
                kodi_notify('Launcher Plot is now "{0}"'.format(new_plot_str))

            # --- Import category metadata from NFO file (automatic) ---
            elif type2 == 6:
                # >> Returns True if changes were made
                NFO_file = fs_get_category_NFO_name(self.settings, self.categories[categoryID])
                if not fs_import_category_NFO(NFO_file, self.categories, categoryID): return
                kodi_notify('Imported Category NFO file {0}'.format(NFO_FileName.getPath()))

            # --- Browse for category NFO file ---
            elif type2 == 7:
                NFO_file = xbmcgui.Dialog().browse(1, 'Select NFO description file', 'files', '.nfo', False, False)
                log_debug('_command_edit_category() Dialog().browse returned "{0}"'.format(NFO_file))
                if not NFO_file: return
                NFO_FileName = FileName(NFO_file)
                if not NFO_FileName.exists(): return
                # >> Returns True if changes were made
                if not fs_import_category_NFO(NFO_FileName, self.categories, categoryID): return
                kodi_notify('Imported Category NFO file {0}'.format(NFO_FileName.getPath()))

            # --- Export category metadata to NFO file ---
            elif type2 == 8:
                NFO_FileName = fs_get_category_NFO_name(self.settings, self.categories[categoryID])
                # >> Returns False if exception happened. If an Exception happened function notifies
                # >> user, so display nothing to not overwrite error notification.
                if not fs_export_category_NFO(NFO_FileName, self.categories[categoryID]): return
                # >> No need to save categories/launchers
                kodi_notify('Exported Category NFO file {0}'.format(NFO_FileName.getPath()))
                return

        # --- Edit Category Assets/Artwork ---
        # >> New in Kodi Krypton: use new xbmcgui.Dialog().select() and get rid of ImgSelectDialog()
        #    class. Get rid of al calls to gui_show_image_select().
        elif type == 1:
            category = self.categories[categoryID]

            # >> Lisitem elements and label2
            label2_icon      = category['s_icon']      if category['s_icon']      else 'Not set'
            label2_fanart    = category['s_fanart']    if category['s_fanart']    else 'Not set'
            label2_banner    = category['s_banner']    if category['s_banner']    else 'Not set'
            label2_clearlogo = category['s_clearlogo'] if category['s_clearlogo'] else 'Not set'
            label2_poster    = category['s_poster']    if category['s_poster']    else 'Not set'
            label2_trailer   = category['s_trailer']   if category['s_trailer']   else 'Not set'

            icon_listitem      = xbmcgui.ListItem(label = 'Edit Icon ...',      label2 = label2_icon)
            fanart_listitem    = xbmcgui.ListItem(label = 'Edit Fanart ...',    label2 = label2_fanart)
            banner_listitem    = xbmcgui.ListItem(label = 'Edit Banner ...',    label2 = label2_banner)
            clearlogo_listitem = xbmcgui.ListItem(label = 'Edit Clearlogo ...', label2 = label2_clearlogo)
            poster_listitem    = xbmcgui.ListItem(label = 'Edit Poster ...',    label2 = label2_poster)
            trailer_listitem   = xbmcgui.ListItem(label = 'Edit Trailer ...',   label2 = label2_trailer)

            # >> Set lisitem artwork with setArt
            img_icon         = category['s_icon']      if category['s_icon']      else 'DefaultAddonNone.png'
            img_fanart       = category['s_fanart']    if category['s_fanart']    else 'DefaultAddonNone.png'
            img_banner       = category['s_banner']    if category['s_banner']    else 'DefaultAddonNone.png'
            img_clearlogo    = category['s_clearlogo'] if category['s_clearlogo'] else 'DefaultAddonNone.png'
            img_poster       = category['s_poster']    if category['s_poster']    else 'DefaultAddonNone.png'
            img_trailer      = 'DefaultAddonVideo.png' if category['s_trailer']   else 'DefaultAddonNone.png'
            icon_listitem.setArt({'icon' : img_icon})
            fanart_listitem.setArt({'icon' : img_fanart})
            banner_listitem.setArt({'icon' : img_banner})
            clearlogo_listitem.setArt({'icon' : img_clearlogo})
            poster_listitem.setArt({'icon' : img_poster})
            trailer_listitem.setArt({'icon' : img_trailer})

            # >> Execute select dialog
            listitems = [
                icon_listitem,
                fanart_listitem,
                banner_listitem,
                clearlogo_listitem,
                poster_listitem,
                trailer_listitem
            ]
            type2 = dialog.select('Edit Category Assets/Artwork', list = listitems, useDetails = True)
            if type2 < 0: return

            # --- Edit Assets ---
            # >> If this function returns False no changes were made. No need to save categories XML
            # >> and update container.
            asset_list = CATEGORY_ASSET_ID_LIST
            asset_kind = asset_list[type2]
            if not self._gui_edit_asset(KIND_CATEGORY, asset_kind, category): return

        # --- Choose Category default icon/fanart/banner/poster/clearlogo ---
        elif type == 2:
            category = self.categories[categoryID]
            # >> Label1 and label2
            asset_icon_str      = assets_get_asset_name_str(category['default_icon'])
            asset_fanart_str    = assets_get_asset_name_str(category['default_fanart'])
            asset_banner_str    = assets_get_asset_name_str(category['default_banner'])
            asset_poster_str    = assets_get_asset_name_str(category['default_poster'])
            asset_clearlogo_str = assets_get_asset_name_str(category['default_clearlogo'])
            label2_icon         = category[category['default_icon']]      if category[category['default_icon']]      else 'Not set'
            label2_fanart       = category[category['default_fanart']]    if category[category['default_fanart']]    else 'Not set'
            label2_banner       = category[category['default_banner']]    if category[category['default_banner']]    else 'Not set'
            label2_poster       = category[category['default_poster']]    if category[category['default_poster']]    else 'Not set'
            label2_clearlogo    = category[category['default_clearlogo']] if category[category['default_clearlogo']] else 'Not set'
            icon_listitem       = xbmcgui.ListItem(label = 'Choose asset for Icon (currently {0})'.format(asset_icon_str),
                                                   label2 = label2_icon)
            fanart_listitem     = xbmcgui.ListItem(label = 'Choose asset for Fanart (currently {0})'.format(asset_fanart_str),
                                                   label2 = label2_fanart)
            banner_listitem     = xbmcgui.ListItem(label = 'Choose asset for Banner (currently {0})'.format(asset_banner_str),
                                                   label2 = label2_banner)
            poster_listitem     = xbmcgui.ListItem(label = 'Choose asset for Poster (currently {0})'.format(asset_poster_str),
                                                   label2 = label2_poster)
            clearlogo_listitem  = xbmcgui.ListItem(label = 'Choose asset for Clearlogo (currently {0})'.format(asset_clearlogo_str),
                                                   label2 = label2_clearlogo)

            # >> Asset image
            img_icon            = category[category['default_icon']]      if category[category['default_icon']]      else 'DefaultAddonNone.png'
            img_fanart          = category[category['default_fanart']]    if category[category['default_fanart']]    else 'DefaultAddonNone.png'
            img_banner          = category[category['default_banner']]    if category[category['default_banner']]    else 'DefaultAddonNone.png'
            img_poster          = category[category['default_poster']]    if category[category['default_poster']]    else 'DefaultAddonNone.png'
            img_clearlogo       = category[category['default_clearlogo']] if category[category['default_clearlogo']] else 'DefaultAddonNone.png'
            icon_listitem.setArt({'icon' : img_icon})
            fanart_listitem.setArt({'icon' : img_fanart})
            banner_listitem.setArt({'icon' : img_banner})
            poster_listitem.setArt({'icon' : img_poster})
            clearlogo_listitem.setArt({'icon' : img_clearlogo})

            # >> Execute select dialog
            listitems = [icon_listitem, fanart_listitem, banner_listitem, poster_listitem, clearlogo_listitem]
            type2 = dialog.select('Edit Category default Assets/Artwork', list = listitems, useDetails = True)
            if type2 < 0: return

            # >> Build ListItem of assets that can be mapped.
            Category_asset_ListItem_list = [
                xbmcgui.ListItem(label = 'Icon',      label2 = category['s_icon'] if category['s_icon'] else 'Not set'),
                xbmcgui.ListItem(label = 'Fanart',    label2 = category['s_fanart'] if category['s_fanart'] else 'Not set'),
                xbmcgui.ListItem(label = 'Banner',    label2 = category['s_banner'] if category['s_banner'] else 'Not set'),
                xbmcgui.ListItem(label = 'Poster',    label2 = category['s_poster'] if category['s_poster'] else 'Not set'),
                xbmcgui.ListItem(label = 'Clearlogo', label2 = category['s_clearlogo'] if category['s_clearlogo'] else 'Not set'),
            ]
            Category_asset_ListItem_list[0].setArt({'icon' : category['s_icon'] if category['s_icon'] else 'DefaultAddonNone.png'})
            Category_asset_ListItem_list[1].setArt({'icon' : category['s_fanart'] if category['s_fanart'] else 'DefaultAddonNone.png'})
            Category_asset_ListItem_list[2].setArt({'icon' : category['s_banner'] if category['s_banner'] else 'DefaultAddonNone.png'})
            Category_asset_ListItem_list[3].setArt({'icon' : category['s_poster'] if category['s_poster'] else 'DefaultAddonNone.png'})
            Category_asset_ListItem_list[4].setArt({'icon' : category['s_clearlogo'] if category['s_clearlogo'] else 'DefaultAddonNone.png'})

            # >> Krypton feature: User preselected item in select() dialog.
            if type2 == 0:
                p_idx = assets_get_Category_mapped_asset_idx(category, 'default_icon')
                type_s = dialog.select('Choose Category default asset for Icon',
                                       list = Category_asset_ListItem_list, useDetails = True, preselect = p_idx)
                if type_s < 0: return
                assets_choose_Category_mapped_artwork(category, 'default_icon', type_s)
                asset_name = assets_get_asset_name_str(category['default_icon'])
                kodi_notify('Category Icon mapped to {0}'.format(asset_name))
            elif type2 == 1:
                p_idx = assets_get_Category_mapped_asset_idx(category, 'default_fanart')
                type_s = dialog.select('Choose Category default asset for Fanart',
                                       list = Category_asset_ListItem_list, useDetails = True, preselect = p_idx)
                if type_s < 0: return
                assets_choose_Category_mapped_artwork(category, 'default_fanart', type_s)
                asset_name = assets_get_asset_name_str(category['default_fanart'])
                kodi_notify('Category Fanart mapped to {0}'.format(asset_name))
            elif type2 == 2:
                p_idx = assets_get_Category_mapped_asset_idx(category, 'default_banner')
                type_s = dialog.select('Choose Category default asset for Banner',
                                       list = Category_asset_ListItem_list, useDetails = True, preselect = p_idx)
                if type_s < 0: return
                assets_choose_Category_mapped_artwork(category, 'default_banner', type_s)
                asset_name = assets_get_asset_name_str(category['default_banner'])
                kodi_notify('Category Banner mapped to {0}'.format(asset_name))
            elif type2 == 3:
                p_idx = assets_get_Category_mapped_asset_idx(category, 'default_poster')
                type_s = dialog.select('Choose Category default asset for Poster',
                                       list = Category_asset_ListItem_list, useDetails = True, preselect = p_idx)
                if type_s < 0: return
                assets_choose_Category_mapped_artwork(category, 'default_poster', type_s)
                asset_name = assets_get_asset_name_str(category['default_poster'])
                kodi_notify('Category Poster mapped to {0}'.format(asset_name))
            elif type2 == 4:
                p_idx = assets_get_Category_mapped_asset_idx(category, 'default_clearlogo')
                type_s = dialog.select('Choose Category default asset for Clearlogo',
                                       list = Category_asset_ListItem_list, useDetails = True, preselect = p_idx)
                if type_s < 0: return
                assets_choose_Category_mapped_artwork(category, 'default_clearlogo', type_s)
                asset_name = assets_get_asset_name_str(category['default_clearlogo'])
                kodi_notify('Category Clearlogo mapped to {0}'.format(asset_name))

        # --- Category Status (Finished or unfinished) ---
        elif type == 3:
            finished = self.categories[categoryID]['finished']
            finished = False if finished else True
            finished_display = 'Finished' if finished == True else 'Unfinished'
            self.categories[categoryID]['finished'] = finished
            kodi_dialog_OK('Category "{0}" status is now {1}'.format(self.categories[categoryID]['m_name'], finished_display))

        # --- Export Launcher XML configuration ---
        elif type == 4:
            category = self.categories[categoryID]
            category_fn_str = 'Category_' + text_title_to_filename_str(category['m_name']) + '.xml'
            log_debug('_command_edit_category() Exporting Category configuration')
            log_debug('_command_edit_category() Name     "{0}"'.format(category['m_name']))
            log_debug('_command_edit_category() ID       {0}'.format(category['id']))
            log_debug('_command_edit_category() l_fn_str "{0}"'.format(category_fn_str))

            # --- Ask user for a path to export the launcher configuration ---
            dir_path = xbmcgui.Dialog().browse(0, 'Select directory to export XML', 'files',
                                               '', False, False)
            if not dir_path: return

            # --- If XML exists then warn user about overwriting it ---
            export_FN = FileName(dir_path).pjoin(category_fn_str)
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
                autoconfig_export_category(category, export_FN)
            except AddonError as ex:
                kodi_notify_warn('{0}'.format(ex))
            else:
                kodi_notify('Exported Category "{0}" XML config'.format(category['m_name']))
            # >> No need to update categories.xml and timestamps so return now.
            return

        # --- Remove category. Also removes launchers in that category ---
        elif type == 5:
            launcherID_list = []
            category_name = self.categories[categoryID]['m_name']
            for launcherID in sorted(self.launchers.keys()):
                if self.launchers[launcherID]['categoryID'] == categoryID:
                    launcherID_list.append(launcherID)

            if len(launcherID_list) > 0:
                ret = kodi_dialog_yesno('Category "{0}" contains {1} launchers. '.format(category_name, len(launcherID_list)) +
                                        'Deleting it will also delete related launchers. ' +
                                        'Are you sure you want to delete "{0}"?'.format(category_name))
                if not ret: return
                log_info('Deleting category "{0}" id {1}'.format(category_name, categoryID))
                # >> Delete launchers and ROM JSON/XML files associated with them
                for launcherID in launcherID_list:
                    log_info('Deleting linked launcher "{0}" id {1}'.format(self.launchers[launcherID]['m_name'], launcherID))
                    fs_unlink_ROMs_database(g_PATHS.ROMS_DIR, self.launchers[launcherID])
                    self.launchers.pop(launcherID)
                # >> Delete category from database.
                self.categories.pop(categoryID)
            else:
                ret = kodi_dialog_yesno('Category "{0}" contains no launchers. '.format(category_name) +
                                        'Are you sure you want to delete "{0}"?'.format(category_name))
                if not ret: return
                log_info('Deleting category "{0}" id {1}'.format(category_name, categoryID))
                log_info('Category has no launchers, so no launchers to delete.')
                self.categories.pop(categoryID)
            kodi_notify('Deleted category {0}'.format(category_name))

        # If this point is reached then changes to metadata/images were made.
        # Save categories and update container contents so user sees those changes inmediately.
        fs_write_catfile(g_PATHS.CATEGORIES_FILE_PATH, self.categories, self.launchers)
        kodi_refresh_container()

    def _command_add_new_launcher(self, categoryID):
        LAUNCHER_STANDALONE  = 1
        LAUNCHER_ROM         = 2
        LAUNCHER_RETROPLAYER = 3
        LAUNCHER_LNK         = 4

        # >> If categoryID not found user is creating a new launcher using the context menu
        # >> of a launcher in addon root.
        if categoryID not in self.categories:
            log_info('Category ID not found. Creating laucher in addon root.')
            launcher_categoryID = VCATEGORY_ADDONROOT_ID
        else:
            # --- Ask user if launcher is created on selected category or on root menu ---
            category_name = self.categories[categoryID]['m_name']
            dialog = xbmcgui.Dialog()
            type = dialog.select('Choose Launcher category',
                                ['Create Launcher in "{0}" category'.format(category_name),
                                 'Create Launcher in addon root'])
            if type < 0:
                return
            elif type == 0:
                launcher_categoryID = categoryID
            elif type == 1:
                launcher_categoryID = VCATEGORY_ADDONROOT_ID
            else:
                kodi_notify_warn('_command_add_new_launcher() Wring type value. Report this bug.')
                return

        # --- Show "Create New Launcher" dialog ---
        dialog = xbmcgui.Dialog()
        if sys.platform == 'win32':
            type = dialog.select('Create New Launcher',
                                 ['Standalone launcher (Game/Application)',
                                  'ROM launcher (Emulator)',
                                  'ROM launcher (Kodi Retroplayer)',
                                  'LNK launcher (Windows only)'])
        else:
            type = dialog.select('Create New Launcher',
                                 ['Standalone launcher (Game/Application)',
                                  'ROM launcher (Emulator)',
                                  'ROM launcher (Kodi Retroplayer)',])
        if type < 0: return

        # --- Select type of new launcher ---
        filter = '.bat|.exe|.cmd|.lnk' if sys.platform == 'win32' else ''
        if   type == 0: launcher_type = LAUNCHER_STANDALONE
        elif type == 1: launcher_type = LAUNCHER_ROM
        elif type == 2: launcher_type = LAUNCHER_RETROPLAYER
        elif type == 3: launcher_type = LAUNCHER_LNK
        else:
            kodi_dialog_OK('Error creating launcher (type = {0}). This is a bug, pleas report it.'.format(type))
            return
        log_info('_command_add_new_launcher() New launcher (launcher_type = {0})'.format(launcher_type))

        # --- Standalone launcher ---
        if launcher_type == LAUNCHER_STANDALONE:
            app = xbmcgui.Dialog().browse(1, 'Select the launcher application', "files", filter)
            if not app: return
            appPath = FileName(app)

            argument = ''
            argkeyboard = xbmc.Keyboard(argument, 'Application arguments')
            argkeyboard.doModal()
            args = argkeyboard.getText()

            title = appPath.getBase_noext()
            title_formatted = title.replace('.' + title.split('.')[-1], '').replace('.', ' ')
            keyboard = xbmc.Keyboard(title_formatted, 'Set the title of the launcher')
            keyboard.doModal()
            title = keyboard.getText()
            if not title:
                title = appPath.getBase_noext()

            # >> Selection of the launcher game system
            dialog = xbmcgui.Dialog()
            sel_platform = dialog.select('Select the platform', AEL_platform_list)
            if sel_platform < 0: return
            launcher_platform = AEL_platform_list[sel_platform]

            # >> Add launcher to the launchers dictionary (using name as index)
            launcherID   = misc_generate_random_SID()
            launcherdata = fs_new_launcher()
            launcherdata['id']                 = launcherID
            launcherdata['m_name']             = title
            launcherdata['platform']           = launcher_platform
            launcherdata['categoryID']         = launcher_categoryID
            launcherdata['application']        = appPath.getOriginalPath()
            launcherdata['args']               = args
            launcherdata['timestamp_launcher'] = time.time()
            self.launchers[launcherID] = launcherdata
            kodi_notify('Created standalone launcher {0}'.format(title))

        #
        # 1) ROM Launcher
        # 2) Retroplayer launcher
        # 3) LNK launcher (Windows only)
        #
        else:
            # --- Launcher application ---
            if launcher_type == LAUNCHER_ROM:
                app = xbmcgui.Dialog().browse(1, 'Select the launcher application', 'files', filter)
                if not app: return
            elif launcher_type == LAUNCHER_RETROPLAYER:
                app = RETROPLAYER_LAUNCHER_APP_NAME
            elif launcher_type == LAUNCHER_LNK:
                app = LNK_LAUNCHER_APP_NAME
            app_FName = FileName(app)

            # --- ROM path ---
            if launcher_type == LAUNCHER_ROM or launcher_type == LAUNCHER_RETROPLAYER:
                roms_path = xbmcgui.Dialog().browse(0, 'Select the ROMs path', 'files', '')
            elif launcher_type == LAUNCHER_LNK:
                roms_path = xbmcgui.Dialog().browse(0, 'Select the LNKs path', 'files', '')
            if not roms_path: return
            roms_path_FName   = FileName(roms_path)

            # --- ROM extensions ---
            if launcher_type == LAUNCHER_ROM or launcher_type == LAUNCHER_RETROPLAYER:
                extensions = emudata_get_program_extensions(app_FName.getBase())
                extkey = xbmc.Keyboard(extensions, 'Set files extensions, use "|" as separator. (e.g lnk|cbr)')
                extkey.doModal()
                if not extkey.isConfirmed(): return
                ext = extkey.getText()
            elif launcher_type == LAUNCHER_LNK:
                ext = 'lnk'

            # --- Launcher arguments ---
            if launcher_type == LAUNCHER_ROM:
                default_arguments = emudata_get_program_arguments(app_FName.getBase())
                argkeyboard = xbmc.Keyboard(default_arguments, 'Application arguments')
                argkeyboard.doModal()
                if not argkeyboard.isConfirmed(): return
                args = argkeyboard.getText()
            elif launcher_type == LAUNCHER_RETROPLAYER or launcher_type == LAUNCHER_LNK:
                args = '%rom%'

            # --- Launcher title/name ---
            title = app_FName.getBase()
            fixed_title = title.replace('.' + title.split('.')[-1], '').replace('.', ' ')
            initial_title = fixed_title if type == 1 else ''
            keyboard = xbmc.Keyboard(initial_title, 'Set the title of the launcher')
            keyboard.doModal()
            if not keyboard.isConfirmed(): return
            title = keyboard.getText()
            if title == '': title = '[ Not set ]'

            # --- Selection of the launcher plaform from official AEL platform names ---
            dialog = xbmcgui.Dialog()
            sel_platform = dialog.select('Select the platform', AEL_platform_list)
            if sel_platform < 0: return
            launcher_platform = AEL_platform_list[sel_platform]

            # --- Select asset path ---
            # A) User chooses one and only one assets path
            # B) If this path is different from the ROM path then asset naming scheme 1 is used.
            # B) If this path is the same as the ROM path then asset naming scheme 2 is used.
            assets_path = xbmcgui.Dialog().browse(0, 'Select asset/artwork directory', 'files', '', False, False, roms_path)
            if not assets_path: return
            assets_path_FName = FileName(assets_path)

            # --- Create launcher object data, add to dictionary and write XML file ---
            # Choose launcher ROM XML filename. There may be launchers with same name in different categories, or
            # even launcher with the same name in the same category.
            launcherID      = misc_generate_random_SID()
            category_name   = self.categories[categoryID]['m_name'] if categoryID in self.categories else VCATEGORY_ADDONROOT_ID
            roms_base_noext = fs_get_ROMs_basename(category_name, title, launcherID)

            # --- Create new launcher. categories.xml is save at the end of this function ---
            # NOTE than in the database original paths are always stored.
            launcherdata = fs_new_launcher()
            launcherdata['id']                 = launcherID
            launcherdata['m_name']             = title
            launcherdata['platform']           = launcher_platform
            launcherdata['categoryID']         = launcher_categoryID
            launcherdata['application']        = app_FName.getOriginalPath()
            launcherdata['args']               = args
            launcherdata['rompath']            = roms_path_FName.getOriginalPath()
            launcherdata['romext']             = ext
            launcherdata['roms_base_noext']    = roms_base_noext
            launcherdata['timestamp_launcher'] = time.time()

            # >> Create asset directories. Function detects if we are using naming scheme 1 or 2.
            # >> launcher is edited using Python passing by assignment.
            assets_init_asset_dir(assets_path_FName, launcherdata)
            self.launchers[launcherID] = launcherdata

            # >> Notify user
            if   launcher_type == LAUNCHER_ROM:         kodi_notify('Created ROM launcher {0}'.format(title))
            elif launcher_type == LAUNCHER_RETROPLAYER: kodi_notify('Created Retroplayer launcher {0}'.format(title))
            elif launcher_type == LAUNCHER_LNK:         kodi_notify('Created LNK launcher {0}'.format(title))

        # >> If this point is reached then changes to metadata/images were made.
        # >> Save categories and update container contents so user sees those changes inmediately.
        fs_write_catfile(g_PATHS.CATEGORIES_FILE_PATH, self.categories, self.launchers)
        kodi_refresh_container()

    def _command_edit_launcher(self, categoryID, launcherID):
        # --- Shows a select box with the options to edit ---
        dialog = xbmcgui.Dialog()
        finished_str = 'Finished' if self.launchers[launcherID]['finished'] == True else 'Unfinished'
        if self.launchers[launcherID]['categoryID'] == VCATEGORY_ADDONROOT_ID:
            category_name = 'Addon root (no category)'
        else:
            category_name = self.categories[self.launchers[launcherID]['categoryID']]['m_name']
        if self.launchers[launcherID]['rompath'] == '':
            type = dialog.select(
                'Select action for Launcher {0}'.format(self.launchers[launcherID]['m_name']), [
                'Edit Metadata ...',
                'Edit Assets/Artwork ...',
                'Choose default Assets/Artwork ...',
                'Change Category: {0}'.format(category_name),
                'Launcher status: {0}'.format(finished_str),
                'Advanced Modifications ...',
                'Export Launcher XML configuration ...',
                'Delete Launcher',
            ])
        else:
            type = dialog.select(
                'Select action for launcher {0}'.format(self.launchers[launcherID]['m_name']), [
                'Edit Metadata ...',
                'Edit Assets/Artwork ...',
                'Choose default Assets/Artwork ...',
                'Change Category: {0}'.format(category_name),
                'Launcher status: {0}'.format(finished_str),
                'Manage ROMs ...',
                'Audit ROMs / Launcher view mode ...',
                'Advanced Modifications ...',
                'Export Launcher XML configuration ...',
                'Delete Launcher'
              ])
        if type < 0: return

        # --- Edition of the launcher metadata ---
        type_nb = 0
        if type == type_nb:
            # --- Make a menu list of available metadata scrapers ---
            g_scrap_factory = ScraperFactory(g_PATHS, self.settings)
            scraper_menu_list = g_scrap_factory.get_metadata_scraper_menu_list()

            # --- Metadata edit dialog ---
            NFO_FileName = fs_get_launcher_NFO_name(self.settings, self.launchers[launcherID])
            NFO_found_str = 'NFO found' if NFO_FileName.exists() else 'NFO not found'
            plot_str = text_limit_string(self.launchers[launcherID]['m_plot'], PLOT_STR_MAXSIZE)
            common_menu_list = [
                "Edit Title: '{0}'".format(self.launchers[launcherID]['m_name']),
                "Edit Platform: {0}".format(self.launchers[launcherID]['platform']),
                "Edit Release Year: '{0}'".format(self.launchers[launcherID]['m_year']),
                "Edit Genre: '{0}'".format(self.launchers[launcherID]['m_genre']),
                "Edit Developer: '{0}'".format(self.launchers[launcherID]['m_developer']),
                "Edit Rating: '{0}'".format(self.launchers[launcherID]['m_rating']),
                "Edit Plot: '{0}'".format(plot_str),
                'Import NFO file (default, {0})'.format(NFO_found_str),
                'Import NFO file (browse NFO file) ...',
                'Save NFO file (default location)',
            ]
            dialog = xbmcgui.Dialog()
            # For now disable scraping for all launcher, including standalone launchers.
            # ROM_launcher = True if self.launchers[launcherID]['rompath'] else False
            # if ROM_launcher:
            #     type2 = dialog.select('Edit Launcher Metadata', common_menu_list)
            # else:
            #     type2 = dialog.select('Edit Launcher Metadata', common_menu_list + scraper_menu_list)
            type2 = dialog.select('Edit Launcher Metadata', common_menu_list)
            if type2 < 0: return

            # --- Edition of the launcher name ---
            if type2 == 0:
                launcher = self.launchers[launcherID]
                keyboard = xbmc.Keyboard(launcher['m_name'], 'Edit title')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                title = keyboard.getText()
                if title == '': title = launcher['m_name']
                old_launcher_name = launcher['m_name']
                new_launcher_name = title.rstrip()
                log_debug('_command_edit_launcher() Edit Title: old_launcher_name "{0}"'.format(old_launcher_name))
                log_debug('_command_edit_launcher() Edit Title: new_launcher_name "{0}"'.format(new_launcher_name))
                if old_launcher_name == new_launcher_name:
                    kodi_notify('Launcher Title not changed')
                    return

                # --- Rename ROMs XML/JSON file (if it exists) and change launcher ---
                old_roms_base_noext = launcher['roms_base_noext']
                categoryID = launcher['categoryID']
                category_name = self.categories[categoryID]['m_name'] if categoryID in self.categories else VCATEGORY_ADDONROOT_ID
                new_roms_base_noext = fs_get_ROMs_basename(category_name, new_launcher_name, launcherID)
                fs_rename_ROMs_database(g_PATHS.ROMS_DIR, old_roms_base_noext, new_roms_base_noext)
                launcher['m_name'] = new_launcher_name
                launcher['roms_base_noext'] = new_roms_base_noext
                kodi_notify('Launcher Title is now {0}'.format(new_launcher_name))

            # --- Selection of the launcher platform from AEL "official" list ---
            elif type2 == 1:
                p_idx = get_AEL_platform_index(self.launchers[launcherID]['platform'])
                sel_platform = xbmcgui.Dialog().select('Select the platform', AEL_platform_list, preselect = p_idx)
                if sel_platform < 0: return
                if p_idx == sel_platform:
                    kodi_notify('Launcher Platform not changed')
                    return
                self.launchers[launcherID]['platform'] = AEL_platform_list[sel_platform]
                kodi_notify('Launcher Platform is now {0}'.format(AEL_platform_list[sel_platform]))

            # --- Edition of the launcher release date (year) ---
            elif type2 == 2:
                old_year_str = self.launchers[launcherID]['m_year']
                keyboard = xbmc.Keyboard(old_year_str, 'Edit Launcher release year')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                new_year_str = keyboard.getText()
                if old_year_str == new_year_str:
                    kodi_notify('Launcher Year not changed')
                    return
                self.launchers[launcherID]['m_year'] = new_year_str
                kodi_notify('Launcher Year is now {0}'.format(new_year_str))

            # --- Edition of the launcher genre ---
            elif type2 == 3:
                old_genre_str = self.launchers[launcherID]['m_genre']
                keyboard = xbmc.Keyboard(old_genre_str, 'Edit genre')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                new_genre_str = keyboard.getText()
                if old_genre_str == new_genre_str:
                    kodi_notify('Launcher Genre not changed')
                    return
                self.launchers[launcherID]['m_genre'] = new_genre_str
                kodi_notify('Launcher Genre is now {0}'.format(new_genre_str))

            # --- Edition of the launcher developer ---
            elif type2 == 4:
                old_developer_str = self.launchers[launcherID]['m_developer']
                keyboard = xbmc.Keyboard(old_developer_str, 'Edit developer')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                new_developer_str = keyboard.getText()
                if old_developer_str == new_developer_str:
                    kodi_notify('Launcher Developer not changed')
                    return
                self.launchers[launcherID]['m_developer'] = new_developer_str
                kodi_notify('Launcher Developer is now {0}'.format(new_developer_str))

            # --- Edition of the launcher rating ---
            elif type2 == 5:
                rating = dialog.select('Edit Launcher Rating', [
                    'Not set',  'Rating 0', 'Rating 1', 'Rating 2', 'Rating 3', 'Rating 4',
                    'Rating 5', 'Rating 6', 'Rating 7', 'Rating 8', 'Rating 9', 'Rating 10'])
                if rating == 0:
                    self.launchers[launcherID]['m_rating'] = ''
                    kodi_notify('Launcher Rating changed to Not Set')
                elif rating >= 1 and rating <= 11:
                    self.launchers[launcherID]['m_rating'] = '{0}'.format(rating - 1)
                    kodi_notify('Launcher Rating is now {0}'.format(self.launchers[launcherID]['m_rating']))
                elif rating < 0:
                    kodi_notify('Launcher Rating not changed')
                    return

            # --- Edit launcher description (plot) ---
            elif type2 == 6:
                old_plot_str = self.launchers[launcherID]['m_plot']
                keyboard = xbmc.Keyboard(old_plot_str, 'Edit plot')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                new_plot_str = keyboard.getText()
                if old_plot_str == new_plot_str:
                    kodi_notify('Launcher Plot not changed')
                    return
                self.launchers[launcherID]['m_plot'] = new_plot_str
                kodi_notify('Launcher Plot is now "{0}"'.format(new_plot_str))

            # --- Import launcher metadata from NFO file (default location) ---
            elif type2 == 7:
                # >> Get NFO file name for launcher
                # >> Launcher is edited using Python passing by assigment
                # >> Returns True if changes were made
                NFO_file = fs_get_launcher_NFO_name(self.settings, self.launchers[launcherID])
                if not fs_import_launcher_NFO(NFO_file, self.launchers, launcherID): return
                kodi_notify('Imported Launcher NFO file {0}'.format(NFO_FileName.getPath()))

            # --- Browse for NFO file ---
            elif type2 == 8:
                NFO_file = xbmcgui.Dialog().browse(1, 'Select Launcher NFO file', 'files', '.nfo', False, False)
                if not NFO_file: return
                NFO_FileName = FileName(NFO_file)
                if not NFO_FileName.exists(): return
                # >> Launcher is edited using Python passing by assigment
                # >> Returns True if changes were made
                if not fs_import_launcher_NFO(NFO_FileName, self.launchers, launcherID): return
                kodi_notify('Imported Launcher NFO file {0}'.format(NFO_FileName.getPath()))

            # --- Export launcher metadata to NFO file ---
            elif type2 == 9:
                NFO_FileName = fs_get_launcher_NFO_name(self.settings, self.launchers[launcherID])
                if not fs_export_launcher_NFO(NFO_FileName, self.launchers[launcherID]): return
                kodi_notify('Exported Launcher NFO file {0}'.format(NFO_FileName.getPath()))
                # >> No need to save launchers so return
                return

            # --- Scrape launcher metadata ---
            elif type2 >= 10:
                # --- Use the scraper chosen by user ---
                scraper_index = type2 - len(common_menu_list)
                scraper_ID = g_scrap_factory.get_metadata_scraper_ID_from_menu_idx(scraper_index)
                scrap_strategy = g_scrap_factory.create_CM_metadata(scraper_ID)

                # --- Grab data ---
                object_dic = self.launchers[launcherID]
                platform = self.launchers[launcherID]['platform']
                data_dic = {
                    'rom_base_noext' : self.launchers[launcherID]['m_name'],
                    'platform' : platform,
                }

                # --- Scrape! ---
                # If this returns False there were no changes so no need to save database.
                op_dic = scrap_strategy.scrap_CM_metadata_Launcher(object_dic, data_dic)
                kodi_display_user_message(op_dic)
                if not op_dic['status']: return

        # --- Edit Launcher Assets/Artwork ---
        type_nb = type_nb + 1
        if type == type_nb:
            launcher = self.launchers[launcherID]

            # >> Create ListItems and label2
            label2_icon       = launcher['s_icon']       if launcher['s_icon']      else 'Not set'
            label2_fanart     = launcher['s_fanart']     if launcher['s_fanart']    else 'Not set'
            label2_banner     = launcher['s_banner']     if launcher['s_banner']    else 'Not set'
            label2_clearlogo  = launcher['s_clearlogo']  if launcher['s_clearlogo'] else 'Not set'
            label2_poster     = launcher['s_poster']     if launcher['s_poster']     else 'Not set'
            label2_controller = launcher['s_controller'] if launcher['s_controller'] else 'Not set'
            label2_trailer    = launcher['s_trailer']    if launcher['s_trailer']   else 'Not set'
            icon_listitem       = xbmcgui.ListItem(label = 'Edit Icon ...', label2 = label2_icon)
            fanart_listitem     = xbmcgui.ListItem(label = 'Edit Fanart ...', label2 = label2_fanart)
            banner_listitem     = xbmcgui.ListItem(label = 'Edit Banner ...', label2 = label2_banner)
            clearlogo_listitem  = xbmcgui.ListItem(label = 'Edit Clearlogo ...', label2 = label2_clearlogo)
            poster_listitem     = xbmcgui.ListItem(label = 'Edit Poster ...', label2 = label2_poster)
            controller_listitem = xbmcgui.ListItem(label = 'Edit Controller ...', label2 = label2_controller)
            trailer_listitem    = xbmcgui.ListItem(label = 'Edit Trailer ...', label2 = label2_trailer)

            # >> Set artwork with setArt()
            img_icon       = launcher['s_icon']       if launcher['s_icon']     else 'DefaultAddonNone.png'
            img_fanart     = launcher['s_fanart']     if launcher['s_fanart']    else 'DefaultAddonNone.png'
            img_banner     = launcher['s_banner']     if launcher['s_banner']    else 'DefaultAddonNone.png'
            img_clearlogo  = launcher['s_clearlogo']  if launcher['s_clearlogo'] else 'DefaultAddonNone.png'
            img_poster     = launcher['s_poster']     if launcher['s_poster']     else 'DefaultAddonNone.png'
            img_controller = launcher['s_controller'] if launcher['s_controller'] else 'DefaultAddonNone.png'
            img_trailer    = 'DefaultAddonVideo.png'  if launcher['s_trailer']   else 'DefaultAddonNone.png'
            icon_listitem.setArt({'icon' : img_icon})
            fanart_listitem.setArt({'icon' : img_fanart})
            banner_listitem.setArt({'icon' : img_banner})
            clearlogo_listitem.setArt({'icon' : img_clearlogo})
            poster_listitem.setArt({'icon' : img_poster})
            controller_listitem.setArt({'icon' : img_controller})
            trailer_listitem.setArt({'icon' : img_trailer})

            # >> Execute select dialog
            listitems = [
                icon_listitem,
                fanart_listitem,
                banner_listitem,
                clearlogo_listitem,
                poster_listitem,
                controller_listitem,
                trailer_listitem
            ]
            type2 = dialog.select('Edit Launcher Assets/Artwork', list = listitems, useDetails = True)
            if type2 < 0: return

            # --- Edit Assets ---
            # If this function returns False no changes were made. No need to save categories
            # XML and update container.
            asset_kind = LAUNCHER_ASSET_ID_LIST[type2]
            if not self._gui_edit_asset(KIND_LAUNCHER, asset_kind, launcher): return

        # --- Choose Launcher default icon/fanart/banner/poster/clearlogo ---
        type_nb = type_nb + 1
        if type == type_nb:
            launcher = self.launchers[launcherID]
            # >> Label1 an label2
            asset_icon_str      = assets_get_asset_name_str(launcher['default_icon'])
            asset_fanart_str    = assets_get_asset_name_str(launcher['default_fanart'])
            asset_banner_str    = assets_get_asset_name_str(launcher['default_banner'])
            asset_clearlogo_str = assets_get_asset_name_str(launcher['default_clearlogo'])
            asset_poster_str    = assets_get_asset_name_str(launcher['default_poster'])
            label2_icon         = launcher[launcher['default_icon']]      if launcher[launcher['default_icon']]      else 'Not set'
            label2_fanart       = launcher[launcher['default_fanart']]    if launcher[launcher['default_fanart']]    else 'Not set'
            label2_banner       = launcher[launcher['default_banner']]    if launcher[launcher['default_banner']]    else 'Not set'
            label2_clearlogo    = launcher[launcher['default_clearlogo']] if launcher[launcher['default_clearlogo']] else 'Not set'
            label2_poster       = launcher[launcher['default_poster']]    if launcher[launcher['default_poster']]    else 'Not set'
            icon_listitem       = xbmcgui.ListItem(
                label = 'Choose asset for Icon (currently {0})'.format(asset_icon_str), label2 = label2_icon)
            fanart_listitem     = xbmcgui.ListItem(
                label = 'Choose asset for Fanart (currently {0})'.format(asset_fanart_str), label2 = label2_fanart)
            banner_listitem     = xbmcgui.ListItem(
                label = 'Choose asset for Banner (currently {0})'.format(asset_banner_str), label2 = label2_banner)
            clearlogo_listitem  = xbmcgui.ListItem(
                label = 'Choose asset for Clearlogo (currently {0})'.format(asset_clearlogo_str), label2 = label2_clearlogo)
            poster_listitem     = xbmcgui.ListItem(
                label = 'Choose asset for Poster (currently {0})'.format(asset_poster_str), label2 = label2_poster)

            # >> Asset image
            img_icon            = launcher[launcher['default_icon']]      if launcher[launcher['default_icon']]      else 'DefaultAddonNone.png'
            img_fanart          = launcher[launcher['default_fanart']]    if launcher[launcher['default_fanart']]    else 'DefaultAddonNone.png'
            img_banner          = launcher[launcher['default_banner']]    if launcher[launcher['default_banner']]    else 'DefaultAddonNone.png'
            img_clearlogo       = launcher[launcher['default_clearlogo']] if launcher[launcher['default_clearlogo']] else 'DefaultAddonNone.png'
            img_poster          = launcher[launcher['default_poster']]    if launcher[launcher['default_poster']]    else 'DefaultAddonNone.png'

            icon_listitem.setArt({'icon' : img_icon})
            fanart_listitem.setArt({'icon' : img_fanart})
            banner_listitem.setArt({'icon' : img_banner})
            clearlogo_listitem.setArt({'icon' : img_clearlogo})
            poster_listitem.setArt({'icon' : img_poster})

            # >> Execute select dialog
            listitems = [
                icon_listitem,
                fanart_listitem,
                banner_listitem,
                clearlogo_listitem,
                poster_listitem,
            ]
            type2 = dialog.select('Edit Launcher default Assets/Artwork', list = listitems, useDetails = True)
            if type2 < 0: return

            # >> Build ListItem of assets that can be mapped.
            Launcher_asset_ListItem_list = [
                xbmcgui.ListItem(label = 'Icon',       label2 = launcher['s_icon'] if launcher['s_icon'] else 'Not set'),
                xbmcgui.ListItem(label = 'Fanart',     label2 = launcher['s_fanart'] if launcher['s_fanart'] else 'Not set'),
                xbmcgui.ListItem(label = 'Banner',     label2 = launcher['s_banner'] if launcher['s_banner'] else 'Not set'),
                xbmcgui.ListItem(label = 'Clearlogo',  label2 = launcher['s_clearlogo'] if launcher['s_clearlogo'] else 'Not set'),
                xbmcgui.ListItem(label = 'Poster',     label2 = launcher['s_poster'] if launcher['s_poster'] else 'Not set'),
                xbmcgui.ListItem(label = 'Controller', label2 = launcher['s_controller'] if launcher['s_controller'] else 'Not set'),
            ]
            Launcher_asset_ListItem_list[0].setArt({'icon' : launcher['s_icon'] if launcher['s_icon'] else 'DefaultAddonNone.png'})
            Launcher_asset_ListItem_list[1].setArt({'icon' : launcher['s_fanart'] if launcher['s_fanart'] else 'DefaultAddonNone.png'})
            Launcher_asset_ListItem_list[2].setArt({'icon' : launcher['s_banner'] if launcher['s_banner'] else 'DefaultAddonNone.png'})
            Launcher_asset_ListItem_list[3].setArt({'icon' : launcher['s_clearlogo'] if launcher['s_clearlogo'] else 'DefaultAddonNone.png'})
            Launcher_asset_ListItem_list[4].setArt({'icon' : launcher['s_poster'] if launcher['s_poster'] else 'DefaultAddonNone.png'})
            Launcher_asset_ListItem_list[5].setArt({'icon' : launcher['s_controller'] if launcher['s_controller'] else 'DefaultAddonNone.png'})

            # >> Krypton feature: User preselected item in select() dialog.
            if type2 == 0:
                p_idx = assets_get_Launcher_mapped_asset_idx(launcher, 'default_icon')
                type_s = dialog.select(
                    'Choose Launcher default asset for Icon',
                    list = Launcher_asset_ListItem_list, useDetails = True, preselect = p_idx)
                if type_s < 0: return
                assets_choose_Launcher_mapped_artwork(launcher, 'default_icon', type_s)
                asset_name = assets_get_asset_name_str(launcher['default_icon'])
                kodi_notify('Launcher Icon mapped to {0}'.format(asset_name))
            elif type2 == 1:
                p_idx = assets_get_Launcher_mapped_asset_idx(launcher, 'default_fanart')
                type_s = dialog.select(
                    'Choose default asset for Fanart',
                    list = Launcher_asset_ListItem_list, useDetails = True, preselect = p_idx)
                if type_s < 0: return
                assets_choose_Launcher_mapped_artwork(launcher, 'default_fanart', type_s)
                asset_name = assets_get_asset_name_str(launcher['default_fanart'])
                kodi_notify('Launcher Fanart mapped to {0}'.format(asset_name))
            elif type2 == 2:
                p_idx = assets_get_Launcher_mapped_asset_idx(launcher, 'default_banner')
                type_s = dialog.select(
                    'Choose default asset for Banner',
                    list = Launcher_asset_ListItem_list, useDetails = True, preselect = p_idx)
                if type_s < 0: return
                assets_choose_Launcher_mapped_artwork(launcher, 'default_banner', type_s)
                asset_name = assets_get_asset_name_str(launcher['default_banner'])
                kodi_notify('Launcher Banner mapped to {0}'.format(asset_name))
            elif type2 == 3:
                p_idx = assets_get_Launcher_mapped_asset_idx(launcher, 'default_clearlogo')
                type_s = dialog.select(
                    'Choose default asset for Clearlogo',
                    list = Launcher_asset_ListItem_list, useDetails = True, preselect = p_idx)
                if type_s < 0: return
                assets_choose_Launcher_mapped_artwork(launcher, 'default_clearlogo', type_s)
                asset_name = assets_get_asset_name_str(launcher['default_clearlogo'])
                kodi_notify('Launcher Clearlogo mapped to {0}'.format(asset_name))
            elif type2 == 4:
                p_idx = assets_get_Launcher_mapped_asset_idx(launcher, 'default_poster')
                type_s = dialog.select(
                    'Choose default asset for Poster',
                    list = Launcher_asset_ListItem_list, useDetails = True, preselect = p_idx)
                if type_s < 0: return
                assets_choose_Launcher_mapped_artwork(launcher, 'default_poster', type_s)
                asset_name = assets_get_asset_name_str(launcher['default_poster'])
                kodi_notify('Launcher Poster mapped to {0}'.format(asset_name))

        # --- Change launcher's Category ---
        type_nb = type_nb + 1
        if type == type_nb:
            current_category_ID = self.launchers[launcherID]['categoryID']

            # >> If no Categories there is nothing to change
            if len(self.categories) == 0:
                kodi_dialog_OK('There is no Categories. Nothing to change.')
                return
            dialog = xbmcgui.Dialog()
            # Add special root cateogory at the beginning
            categories_id   = [VCATEGORY_ADDONROOT_ID]
            categories_name = ['Addon root (no category)']
            for key in self.categories:
                categories_id.append(self.categories[key]['id'])
                categories_name.append(self.categories[key]['m_name'])
            selected_cat = dialog.select('Select the category', categories_name)
            if selected_cat < 0: return
            new_categoryID = categories_id[selected_cat]
            self.launchers[launcherID]['categoryID'] = new_categoryID
            log_debug('_command_edit_launcher() current category   ID "{0}"'.format(current_category_ID))
            log_debug('_command_edit_launcher() new     category   ID "{0}"'.format(new_categoryID))
            log_debug('_command_edit_launcher() new     category name "{0}"'.format(categories_name[selected_cat]))

            # >> Save categories/launchers
            self.launchers[launcherID]['timestamp_launcher'] = time.time()
            fs_write_catfile(g_PATHS.CATEGORIES_FILE_PATH, self.categories, self.launchers)

            # >> Display new category where launcher has moved
            # For some reason ReplaceWindow() does not work, bu Container.Update() does.
            # See http://forum.kodi.tv/showthread.php?tid=293844
            if new_categoryID == VCATEGORY_ADDONROOT_ID:
                plugin_url = self.base_url
            else:
                plugin_url = '{0}?com=SHOW_LAUNCHERS&amp;catID={1}'.format(self.base_url, new_categoryID)
            exec_str = 'Container.Update({0},replace)'.format(plugin_url)
            log_debug('_command_edit_launcher() Plugin URL     "{0}"'.format(plugin_url))
            log_debug('_command_edit_launcher() Executebuiltin "{0}"'.format(exec_str))
            xbmc.executebuiltin(exec_str)
            kodi_notify('Launcher new Category is {0}'.format(categories_name[selected_cat]))
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
                type2 = dialog.select('Manage ROMs', [
                    'Choose ROMs default artwork ...',
                    'Manage ROMs asset directories ...',
                    'Rescan ROMs local artwork',
                    'Scrape ROMs artwork',
                    'Remove dead/missing ROMs',
                    'Import ROMs metadata from NFO files',
                    'Export ROMs metadata to NFO files',
                    'Delete ROMs NFO files',
                    'Clear ROMs from launcher',
                ])
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
                        dir_path = dialog.browse(0, 'Select Titles path', 'files', '', False, False, launcher['path_title'])
                        if not dir_path: return
                        self.launchers[launcherID]['path_title'] = dir_path
                    elif type3 == 1:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Snaps path', 'files', '', False, False, launcher['path_snap'])
                        if not dir_path: return
                        self.launchers[launcherID]['path_snap'] = dir_path
                    elif type3 == 2:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Fanarts path', 'files', '', False, False, launcher['path_fanart'])
                        if not dir_path: return
                        self.launchers[launcherID]['path_fanart'] = dir_path
                    elif type3 == 3:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Banners path', 'files', '', False, False, launcher['path_banner'])
                        if not dir_path: return
                        self.launchers[launcherID]['path_banner'] = dir_path
                    elif type3 == 4:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Clearlogos path', 'files', '', False, False, launcher['path_clearlogo'])
                        if not dir_path: return
                        self.launchers[launcherID]['path_clearlogo'] = dir_path
                    elif type3 == 5:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Boxfronts path', 'files', '', False, False, launcher['path_boxfront'])
                        if not dir_path: return
                        self.launchers[launcherID]['path_boxfront'] = dir_path
                    elif type3 == 6:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Boxbacks path', 'files', '', False, False, launcher['path_boxback'])
                        if not dir_path: return
                        self.launchers[launcherID]['path_boxback'] = dir_path
                    elif type3 == 7:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Cartridges path', 'files', '', False, False, launcher['path_cartridge'])
                        if not dir_path: return
                        self.launchers[launcherID]['path_cartridge'] = dir_path
                    elif type3 == 8:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Flyers path', 'files', '', False, False, launcher['path_flyer'])
                        if not dir_path: return
                        self.launchers[launcherID]['path_flyer'] = dir_path
                    elif type3 == 9:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Maps path', 'files', '', False, False, launcher['path_map'])
                        if not dir_path: return
                        self.launchers[launcherID]['path_map'] = dir_path
                    elif type3 == 10:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Manuals path', 'files', '', False, False, launcher['path_manual'])
                        if not dir_path: return
                        self.launchers[launcherID]['path_manual'] = dir_path
                    elif type3 == 11:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Trailers path', 'files', '', False, False, launcher['path_trailer'])
                        if not dir_path: return
                        self.launchers[launcherID]['path_trailer'] = dir_path
                    # >> User canceled select dialog
                    elif type3 < 0: return

                    # >> Check for duplicate paths and warn user.
                    duplicated_name_list = asset_get_duplicated_dir_list(self.launchers[launcherID])
                    if duplicated_name_list:
                        duplicated_asset_srt = ', '.join(duplicated_name_list)
                        kodi_dialog_OK(
                            'Duplicated asset directories: {0}. '.format(duplicated_asset_srt) +
                            'AEL will refuse to add/edit ROMs if there are duplicate asset directories.')

                # --- Rescan ROMs local artwork ---
                # A) First, local assets are searched for every ROM based on the filename.
                # B) Next, missing assets are searched in the Parent/Clone group using the files
                #    found in the previous step. This is much faster than searching for files again.
                elif type2 == 2:
                    log_info('_command_edit_launcher() Rescanning local assets ...')
                    launcher = self.launchers[launcherID]

                    # --- Ensure there is no duplicate asset dirs ---
                    # Cancel scanning if duplicates found
                    duplicated_name_list = asset_get_duplicated_dir_list(launcher)
                    if duplicated_name_list:
                        duplicated_asset_srt = ', '.join(duplicated_name_list)
                        log_info('Duplicated asset dirs: {0}'.format(duplicated_asset_srt))
                        kodi_dialog_OK(
                            'Duplicated asset directories: {0}. '.format(duplicated_asset_srt) +
                            'Change asset directories before continuing.')
                        return
                    else:
                        log_info('No duplicated asset dirs found')

                    # --- Check asset dirs and disable scanning for unset dirs ---
                    enabled_asset_list = asset_get_enabled_asset_list(launcher)
                    unconfigured_name_list = asset_get_unconfigured_name_list(enabled_asset_list)
                    if unconfigured_name_list:
                        unconfigure_asset_srt = ', '.join(unconfigured_name_list)
                        kodi_dialog_OK(
                            'Assets directories not set: {0}. '.format(unconfigure_asset_srt) +
                            'Asset scanner will be disabled for this/those.')

                    # --- Create a cache of assets ---
                    pdialog = KodiProgressDialog()
                    pdialog.startProgress('Scanning files in asset directories ...', len(ROM_ASSET_ID_LIST))
                    for i, asset_kind in enumerate(ROM_ASSET_ID_LIST):
                        pdialog.updateProgress(i)
                        AInfo = assets_get_info_scheme(asset_kind)
                        misc_add_file_cache(launcher[AInfo.path_key])
                    pdialog.endProgress()

                    # --- Traverse ROM list and check local asset/artwork ---
                    roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, launcher)
                    item_counter = 0
                    pdialog.startProgress('Searching for local assets/artwork...', len(roms))
                    for rom_id in roms:
                        # --- Update progress dialog ---
                        pdialog.updateProgress(item_counter)
                        item_counter += 1

                        # --- Search assets for current ROM ---
                        rom = roms[rom_id]
                        ROMFile = FileName(rom['filename'])
                        rom_basename_noext = ROMFile.getBase_noext()
                        log_verb('Checking ROM "{0}" (ID {1})'.format(ROMFile.getBase(), rom_id))

                        # --- Search assets ---
                        for i, asset in enumerate(ROM_ASSET_ID_LIST):
                            AInfo = assets_get_info_scheme(asset)
                            # log_debug('Search  {0}'.format(AInfo.name))
                            if not enabled_asset_list[i]: continue
                            # >> Only look for local asset if current file do not exists. This avoid
                            # >> clearing user-customised assets. Also, first check if the field
                            # >> is defined (which is very quick) to avoid an extra filesystem
                            # >> exist check() for missing images.
                            if rom[AInfo.key]:
                                # >> However, if the artwork is a substitution from the PClone group
                                # >> and the user updated the artwork collection for this ROM the
                                # >> new image will not be picked with the current implementation ...
                                #
                                # >> How to differentiate substituted PClone artwork from user
                                # >> manually customised artwork???
                                # >> If directory is different it is definitely customised.
                                # >> If directory is the same and the basename is from a ROM in the
                                # >> PClone group it is very likely it is substituted.
                                current_asset_FN = FileName(rom[AInfo.key])
                                if current_asset_FN.exists():
                                    log_debug('Local {0:<9} "{1}"'.format(AInfo.name, current_asset_FN.getPath()))
                                    continue
                            # >> Old implementation (slow). Using FileName().exists() to check many
                            # >> files becames really slow.
                            # asset_dir = FileName(launcher[AInfo.path_key])
                            # local_asset = misc_look_for_file(asset_dir, rom_basename_noext, AInfo.exts)
                            # >> New implementation using a cache.
                            local_asset = misc_search_file_cache(launcher[AInfo.path_key], rom_basename_noext, AInfo.exts)
                            if local_asset:
                                rom[AInfo.key] = local_asset.getOriginalPath()
                                log_debug('Found {0:<9} "{1}"'.format(AInfo.name, local_asset.getPath()))
                            else:
                                rom[AInfo.key] = ''
                                log_debug('Miss  {0:<9}'.format(AInfo.name))
                    pdialog.endProgress()

                    # --- Crete Parent/Clone dictionaries ---
                    # --- Traverse ROM list and check assets in the PClone group ---
                    # This is only available if a No-Intro/Redump DAT is configured. If not, warn the user.
                    if self.settings['audit_pclone_assets'] and launcher['audit_state'] == AUDIT_STATE_OFF:
                        log_info('Use assets in the Parent/Clone group is ON. No-Intro/Redump DAT not done.')
                        kodi_dialog_OK('No-Intro/Redump DAT not done and audit_pclone_assets is True. ' +
                                       'Cancelling looking for assets in the Parent/Clone group.')
                    elif self.settings['audit_pclone_assets'] and launcher['audit_state'] == AUDIT_STATE_ON:
                        log_info('Use assets in the Parent/Clone group is ON. Loading Parent/Clone dictionaries.')
                        roms_pclone_index = fs_load_JSON_file(g_PATHS.ROMS_DIR, launcher['roms_base_noext'] + '_index_PClone')
                        clone_parent_dic  = fs_load_JSON_file(g_PATHS.ROMS_DIR, launcher['roms_base_noext'] + '_index_CParent')
                        item_counter = 0
                        pdialog.startProgress('Searching for assets/artwork in the Parent/Clone group...', len(roms))
                        for rom_id in roms:
                            # --- Update progress dialog ---
                            pdialog.updateProgress(item_counter)
                            item_counter += 1

                            # --- Search assets for current ROM ---
                            rom = roms[rom_id]
                            ROMFile = FileName(rom['filename'])
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
                            for i, asset in enumerate(ROM_ASSET_ID_LIST):
                                AInfo = assets_get_info_scheme(asset)
                                # log_debug('Search  {0}'.format(AInfo.name))
                                if not enabled_asset_list[i]: continue
                                asset_DB_file = rom[AInfo.key]
                                # >> Only search for asset in the PClone group if asset is missing
                                # >> from current ROM.
                                if not asset_DB_file:
                                    # log_debug('Search  {0} in PClone set'.format(AInfo.name))
                                    for set_rom_id in pclone_set_id_list:
                                        # ROMFile_t = FileName(roms[set_rom_id]['filename'])
                                        # log_debug('PClone group ROM "{0}" (ID) {1})'.format(ROMFile_t.getBase(), set_rom_id))
                                        asset_DB_file_t = roms[set_rom_id][AInfo.key]
                                        if asset_DB_file_t:
                                            rom[AInfo.key] = asset_DB_file_t
                                            log_debug('Found {0:<9} "{1}"'.format(AInfo.name, asset_DB_file_t))
                                            # >> Stop as soon as one asset is found in the group.
                                            break
                                    # >> The else statement is executed when the loop has exhausted iterating the list.
                                    else:
                                        log_debug('Miss  {0:<9}'.format(AInfo.name))
                                else:
                                    log_debug('Has   {0:<9}'.format(AInfo.name))
                        pdialog.endProgress()

                    # --- Update assets on _parents.json ---
                    # Here only assets s_* are changed. I think it is not necessary to audit ROMs again.
                    pdialog.startProgress('Saving ROM JSON database ...')
                    if launcher['audit_state'] == AUDIT_STATE_ON:
                        log_verb('Updating artwork on parent JSON database.')
                        parents_roms_base_noext = launcher['roms_base_noext'] + '_parents'
                        parent_roms = fs_load_JSON_file(g_PATHS.ROMS_DIR, parents_roms_base_noext)
                        pdialog.updateProgress(25)
                        for parent_rom_id in parent_roms:
                            parent_roms[parent_rom_id]['s_banner']    = roms[parent_rom_id]['s_banner']
                            parent_roms[parent_rom_id]['s_boxback']   = roms[parent_rom_id]['s_boxback']
                            parent_roms[parent_rom_id]['s_boxfront']  = roms[parent_rom_id]['s_boxfront']
                            parent_roms[parent_rom_id]['s_cartridge'] = roms[parent_rom_id]['s_cartridge']
                            parent_roms[parent_rom_id]['s_clearlogo'] = roms[parent_rom_id]['s_clearlogo']
                            parent_roms[parent_rom_id]['s_fanart']    = roms[parent_rom_id]['s_fanart']
                            parent_roms[parent_rom_id]['s_flyer']     = roms[parent_rom_id]['s_flyer']
                            parent_roms[parent_rom_id]['s_manual']    = roms[parent_rom_id]['s_manual']
                            parent_roms[parent_rom_id]['s_map']       = roms[parent_rom_id]['s_map']
                            parent_roms[parent_rom_id]['s_snap']      = roms[parent_rom_id]['s_snap']
                            parent_roms[parent_rom_id]['s_title']     = roms[parent_rom_id]['s_title']
                            parent_roms[parent_rom_id]['s_trailer']   = roms[parent_rom_id]['s_trailer']
                        fs_write_JSON_file(g_PATHS.ROMS_DIR, parents_roms_base_noext, parent_roms)

                    # --- Save ROMs XML file ---
                    pdialog.updateProgress(50)
                    fs_write_ROMs_JSON(g_PATHS.ROMS_DIR, launcher, roms)
                    pdialog.endProgress()
                    kodi_notify('Rescaning of ROMs local artwork finished')

                # --- Scrape ROMs artwork ---
                # Mimic what the ROM scanner does. Use same settings as the ROM scanner.
                # Like the ROM scanner, only scrape artwork not found locally.
                elif type2 == 3:
                    log_info('_command_edit_launcher() Rescraping local assets ...')
                    launcher = self.launchers[launcherID]
                    pdialog_verbose = True
                    pdialog = KodiProgressDialog()

                    # --- Load metadata/asset scrapers ---
                    g_scraper_factory = ScraperFactory(g_PATHS, self.settings)
                    scraper_strategy = g_scraper_factory.create_scanner(launcher)
                    scraper_strategy.scanner_set_progress_dialog(pdialog, pdialog_verbose)
                    scraper_strategy.scanner_check_before_scraping()

                    # --- Ensure there is no duplicate asset dirs ---
                    duplicated_name_list = asset_get_duplicated_dir_list(launcher)
                    if duplicated_name_list:
                        duplicated_asset_srt = ', '.join(duplicated_name_list)
                        log_info('Duplicated asset dirs: {0}'.format(duplicated_asset_srt))
                        kodi_dialog_OK(
                            'Duplicated asset directories: {0}. '.format(duplicated_asset_srt) +
                            'Change asset directories before continuing.')
                        return
                    else:
                        log_info('No duplicated asset dirs found')

                    # --- Check asset dirs and disable scanning for unset dirs ---
                    scraper_strategy.scanner_check_launcher_unset_asset_dirs()
                    if scraper_strategy.unconfigured_name_list:
                        unconfigured_asset_srt = ', '.join(scraper_strategy.unconfigured_name_list)
                        kodi_dialog_OK(
                            'Assets directories not set: {0}. '.format(unconfigured_asset_srt) +
                            'Asset scanner will be disabled for this/those.')

                    # --- Prepare ScannerStrategy variables ---
                    enabled_asset_list = scraper_strategy.enabled_asset_list
                    asset_scraper_name = scraper_strategy.asset_scraper_name
                    asset_scraper_obj  = scraper_strategy.asset_scraper_obj

                    # --- Create a cache of current assets on disk ---
                    log_info('Scanning and caching files in asset directories ...')
                    pdialog.startProgress('Scanning files in asset directories ...', len(ROM_ASSET_ID_LIST))
                    for i, asset_kind in enumerate(ROM_ASSET_ID_LIST):
                        pdialog.updateProgress(i)
                        AInfo = assets_get_info_scheme(asset_kind)
                        misc_add_file_cache(launcher[AInfo.path_key])
                    pdialog.endProgress()

                    # --- Traverse ROM list and check local asset/artwork ---
                    roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, launcher)
                    item_counter = 0
                    pdialog.startProgress('Scraping assets...', len(roms))
                    for rom_id in roms:
                        # --- Update progress dialog ---
                        pdialog.updateProgress(item_counter)
                        item_counter += 1

                        # --- Search for local artwork/assets ---
                        rom = roms[rom_id]
                        ROMFile = FileName(rom['filename'])
                        log_debug('***** Checking ROM "{0}" (ID {1})'.format(ROMFile.getBase(), rom_id))
                        local_asset_list = assets_search_local_cached_assets(launcher, ROMFile, enabled_asset_list)
                        asset_action_list = [ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET] * len(ROM_ASSET_ID_LIST)

                        # --- Process asset by asset ---
                        for i, asset_ID in enumerate(ROM_ASSET_ID_LIST):
                            # --- Determine if asset must be scraped or not ---
                            AInfo = assets_get_info_scheme(asset_ID)
                            if not enabled_asset_list[i]:
                                log_debug('Skipping {0} (dir not configured).'.format(AInfo.name))
                                asset_action_list[i] = ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET
                            elif local_asset_list[i]:
                                log_debug('Local {0} FOUND'.format(AInfo.name))
                                asset_action_list[i] = ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET
                            elif asset_scraper_obj.supports_asset_ID(asset_ID):
                                # Scrape only if scraper supports asset.
                                log_debug('Local {0} NOT found. Scraping.'.format(AInfo.name))
                                asset_action_list[i] = ScrapeStrategy.ACTION_ASSET_SCRAPER
                            else:
                                log_debug('Local {0} NOT found. No scraper support.'.format(AInfo.name))
                                asset_action_list[i] = ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET

                        # --- If any asset is going to be scraped then get candidate game ---
                        temp_asset_list = [x == ScrapeStrategy.ACTION_ASSET_SCRAPER for x in asset_action_list]
                        if any(temp_asset_list):
                            log_debug('Getting asset candidate game.')
                            # What if status_dic reports and error here? It is ignored?
                            status_dic = kodi_new_status_dic('No error')
                            # This is a workaround! It will fail for multidisc ROMs.
                            # See proper implementation in _roms_import_roms()
                            ROM_checksums = ROMFile
                            candidate_asset = scraper_strategy._scanner_get_candidate(
                                rom, ROMFile, ROM_checksums, asset_scraper_obj, asset_scraper_name, status_dic)
                            scraper_strategy.candidate_asset = candidate_asset
                        else:
                            log_debug('Setting candidate game to None.')
                            scraper_strategy.candidate_asset = None

                        # --- Process asset by asset actions ---
                        for i, asset_ID in enumerate(ROM_ASSET_ID_LIST):
                            AInfo = assets_get_info_scheme(asset_ID)
                            if asset_action_list[i] == ScrapeStrategy.ACTION_ASSET_LOCAL_ASSET:
                                log_debug('Using local asset for {}'.format(AInfo.name))
                                rom[AInfo.key] = local_asset_list[i]
                            elif asset_action_list[i] == ScrapeStrategy.ACTION_ASSET_SCRAPER:
                                rom[AInfo.key] = scraper_strategy._scanner_scrap_ROM_asset(
                                    asset_ID, local_asset_list[i], ROMFile)
                            else:
                                raise ValueError('Asset {} index {} ID {} unknown action {}'.format(
                                    AInfo.name, i, asset_ID, asset_action_list[i]))

                        # --- Check if user pressed the cancel button ---
                        if pdialog.isCanceled():
                            pdialog.endProgress()
                            kodi_dialog_OK('Stopping ROM artwork scraping.')
                            log_info('User pressed Cancel button when scraping ROMs.')
                            break
                    else:
                        pdialog.endProgress()

                    # --- Flush scraper disk caches ---
                    pdialog.startProgress('Flushing scraper disk caches...')
                    g_scraper_factory.destroy_scanner()
                    pdialog.endProgress()

                    # --- Save ROMs XML file ---
                    pdialog.startProgress('Saving ROM JSON database ...')
                    fs_write_ROMs_JSON(g_PATHS.ROMS_DIR, launcher, roms)
                    pdialog.endProgress()
                    kodi_notify('Rescaning of ROMs local artwork finished')

                # --- Remove Remove dead/missing ROMs ROMs ---
                elif type2 == 4:
                    if self.launchers[launcherID]['audit_state'] == AUDIT_STATE_ON:
                        ret = kodi_dialog_yesno(
                            'This launcher has an ROM Audit done. Removing '
                            'dead ROMs will disable the ROM Audit. '
                            'Are you sure you want to remove missing/dead ROMs?')
                    else:
                        ret = kodi_dialog_yesno('Are you sure you want to remove missing/dead ROMs?')
                    if not ret: return

                    # --- Load ROMs for this launcher ---
                    roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, self.launchers[launcherID])

                    # --- Remove dead ROMs ---
                    num_removed_roms = self._roms_delete_missing_ROMs(roms)

                    # --- If there is a No-Intro XML DAT configured remove it ---
                    if self.launchers[launcherID]['audit_state'] == AUDIT_STATE_ON:
                        log_info('Cancelling ROM Audit and forcing launcher to Normal view mode.')
                        self._roms_reset_NoIntro_status(self.launchers[launcherID], roms)
                        self.launchers[launcherID]['launcher_display_mode'] = LAUNCHER_DMODE_FLAT

                    # --- Save ROMs XML file ---
                    pDialog = xbmcgui.DialogProgress()
                    pDialog.startProgress('Saving ROM JSON database ...')
                    fs_write_ROMs_JSON(g_PATHS.ROMS_DIR, self.launchers[launcherID], roms)
                    pdialog.endProgress()
                    self.launchers[launcherID]['num_roms'] = len(roms)
                    kodi_notify('Removed {0} dead ROMs'.format(num_removed_roms))

                # --- Import ROM metadata from NFO files ---
                elif type2 == 5:
                    # >> Load ROMs, iterate and import NFO files
                    roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, self.launchers[launcherID])
                    num_read_NFO_files = 0
                    for rom_id in roms:
                        if fs_import_ROM_NFO(roms, rom_id, verbose = False): num_read_NFO_files += 1
                    # >> Save ROMs XML file / Launcher/timestamp saved at the end of function
                    pDialog = xbmcgui.DialogProgress()
                    pDialog.create('Advanced Emulator Launcher', 'Saving ROM JSON database ...')
                    fs_write_ROMs_JSON(g_PATHS.ROMS_DIR, self.launchers[launcherID], roms)
                    pDialog.update(100)
                    pDialog.close()
                    kodi_notify('Imported {0} NFO files'.format(num_read_NFO_files))

                # --- Export ROM metadata to NFO files ---
                elif type2 == 6:
                    # Load ROMs for current launcher, iterate and write NFO files
                    roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, self.launchers[launcherID])
                    if not roms: return
                    num_nfo_files = 0
                    for rom_id in roms:
                        # >> Skip No-Intro Added ROMs
                        if not roms[rom_id]['filename']: continue
                        fs_export_ROM_NFO(roms[rom_id], verbose = False)
                        num_nfo_files += 1
                    # No need to save launchers XML / Update container
                    kodi_notify('Created {0} NFO files'.format(num_nfo_files))
                    return

                # --- Delete ROMs metadata NFO files ---
                elif type2 == 7:
                    # --- Get list of NFO files ---
                    ROMPath_FileName = FileName(self.launchers[launcherID]['rompath'])
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
                        FileName(file).unlink()

                    # >> No need to save launchers XML / Update container
                    kodi_notify('Deleted {0} NFO files'.format(len(nfo_scanned_files)))
                    return

                # --- Clear ROMs from launcher ---
                elif type2 == 8:
                    roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, self.launchers[launcherID])
                    num_roms = len(roms)

                    # If launcher is empty (no ROMs) do nothing
                    if num_roms == 0:
                        kodi_dialog_OK('Launcher has no ROMs. Nothing to do.')
                        return

                    # Confirm user wants to delete ROMs
                    dialog = xbmcgui.Dialog()
                    ret = dialog.yesno('Advanced Emulator Launcher',
                                       "Launcher '{0}' has {1} ROMs. Are you sure you want to delete them "
                                       "from AEL database?".format(self.launchers[launcherID]['m_name'], num_roms))
                    if not ret: return

                    # Set ROM Audit to OFF.
                    if self.launchers[launcherID]['audit_state'] == AUDIT_STATE_ON:
                        log_info('Setting audit_state = AUDIT_STATE_OFF')
                        self.launchers[launcherID]['audit_state'] = AUDIT_STATE_OFF

                    # Just remove ROMs database files. Keep the value of roms_base_noext to be reused
                    # when user add more ROMs.
                    fs_unlink_ROMs_database(g_PATHS.ROMS_DIR, self.launchers[launcherID])
                    self.launchers[launcherID]['num_roms'] = 0
                    kodi_notify('Cleared ROMs from launcher database')

        # --- Audit ROMs / Launcher view mode ---
        # ONLY for ROM launchers, not for standalone launchers.
        #
        # New No-Intro/Redump DAT file management:
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
        if self.launchers[launcherID]['rompath'] != '':
            type_nb = type_nb + 1
            if type == type_nb:
                dialog = xbmcgui.Dialog()
                launcher = self.launchers[launcherID]
                has_custom_DAT = True if launcher['audit_custom_dat_file'] else False
                if has_custom_DAT:
                    add_delete_DAT_str = 'Delete custom DAT: {0}'.format(launcher['audit_custom_dat_file'])
                else:
                    add_delete_DAT_str = 'Add custom XML DAT ...'
                display_mode_str = launcher['launcher_display_mode']
                type2 = dialog.select('Audit ROMs / Launcher view mode', [
                    'Launcher display mode (now {0}) ...'.format(display_mode_str),
                    'Audit display filter (now {0}) ...'.format(launcher['audit_display_mode']),
                    'Audit Launcher ROMs',
                    'Undo ROM audit (remove missing ROMs)',
                    add_delete_DAT_str,
                ])
                if type2 < 0: return

                # --- Launcher display mode (Normal or PClone) ---
                if type2 == 0:
                    launcher = self.launchers[launcherID]
                    # Krypton feature: preselect the current item.
                    # NOTE Preselect must be called with named parameter, otherwise it does not work well.
                    try:
                        p_idx = LAUNCHER_DMODE_LIST.index(launcher['launcher_display_mode'])
                    except ValueError:
                        p_idx = 0
                    log_debug('p_idx = "{0}"'.format(p_idx))
                    type_temp = dialog.select('Launcher display mode', LAUNCHER_DMODE_LIST, preselect = p_idx)
                    if type_temp < 0: return

                    # LAUNCHER_DMODE_FLAT
                    if type_temp == 0:
                        launcher['launcher_display_mode'] = LAUNCHER_DMODE_FLAT
                        log_debug('launcher_display_mode = {}'.format(launcher['launcher_display_mode']))
                        kodi_notify('Launcher view mode set to {}'.format(LAUNCHER_DMODE_FLAT))
                    # LAUNCHER_DMODE_PCLONE = 1
                    elif type_temp == 1:
                        # Currently LAUNCHER_DMODE_FLAT requires that ROM Audit is done.
                        if launcher['audit_state'] == AUDIT_STATE_OFF:
                            log_info('_command_edit_launcher() audit_state is OFF')
                            log_info('_command_edit_launcher() Forcing Flat view mode.')
                            kodi_dialog_OK('ROM Audit not done. PClone view mode cannot be set.')
                            launcher['launcher_display_mode'] = LAUNCHER_DMODE_FLAT
                            kodi_notify('Launcher view mode set to {}'.format(LAUNCHER_DMODE_FLAT))
                        else:
                            launcher['launcher_display_mode'] = LAUNCHER_DMODE_PCLONE
                            log_debug('launcher_display_mode = {}'.format(launcher['launcher_display_mode']))
                            kodi_notify('Launcher view mode set to {}'.format(LAUNCHER_DMODE_PCLONE))

                # --- Audit display filter ---
                elif type2 == 1:
                    launcher = self.launchers[launcherID]
                    # If no DAT configured exit.
                    if launcher['audit_display_mode'] == AUDIT_STATE_OFF:
                        kodi_dialog_OK('ROM audit is OFF. '
                            'Audit this launcher before changing this setting.')
                        return

                    # In Krypton preselect the current item.
                    try:
                        p_idx = AUDIT_DMODE_LIST.index(launcher['audit_display_mode'])
                    except ValueError:
                        p_idx = 0
                    log_debug('p_idx = "{0}"'.format(p_idx))
                    type_temp = dialog.select('Launcher audit display filter',
                        AUDIT_DMODE_LIST, preselect = p_idx)
                    if type_temp < 0: return
                    launcher['audit_display_mode'] = AUDIT_DMODE_LIST[type_temp]
                    log_info('Launcher audit display mode changed to "{0}"'.format(launcher['audit_display_mode']))
                    kodi_notify('Display ROMs changed to "{0}"'.format(launcher['audit_display_mode']))

                # --- Audit Launcher ROMs ---
                # 1) If the user configured a custom DAT file use that file.
                # 2) If not, select a DAT file automatically.
                elif type2 == 2:
                    log_debug('Submenu "Audit Launcher ROMs" Starting...')
                    launcher = self.launchers[launcherID]
                    nointro_xml_FN = self._roms_set_NoIntro_DAT(launcher)
                    # Error printed with a OK dialog inside this function.
                    if nointro_xml_FN is None: return
                    log_debug('Using DAT "{}"'.format(nointro_xml_FN.getPath()))
                    # _roms_update_NoIntro_status() updates both launcher and roms dictionaries.
                    # categories.xml saved at the end of the funcion.
                    roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, launcher)
                    if not self._roms_update_NoIntro_status(launcher, roms, nointro_xml_FN):
                        kodi_notify_warn('Error auditing ROMs')
                        return
                    pDialog = xbmcgui.DialogProgress()
                    pDialog.create('Advanced Emulator Launcher', 'Saving ROM JSON database...')
                    fs_write_ROMs_JSON(g_PATHS.ROMS_DIR, launcher, roms)
                    pDialog.update(100)
                    pDialog.close()
                    kodi_notify('Have {} / Miss {} / Unknown {}'.format(
                        self.audit_have, self.audit_miss, self.audit_unknown))

                # --- Undo ROM audit (remove missing ROMs) ---
                elif type2 == 3:
                    # --- Remove No-Intro status and delete missing/dead ROMs to revert launcher to normal ---
                    # _roms_reset_NoIntro_status() does not save ROMs JSON/XML.
                    roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, self.launchers[launcherID])
                    self._roms_reset_NoIntro_status(self.launchers[launcherID], roms)
                    self.launchers[launcherID]['launcher_display_mode'] = LAUNCHER_DMODE_FLAT
                    # categories.xml saved at the end of the function.
                    fs_write_ROMs_JSON(g_PATHS.ROMS_DIR, self.launchers[launcherID], roms)
                    kodi_notify('Removed missing ROMs')

                # --- Add/Delete No-Intro XML parent-clone DAT ---
                elif type2 == 4 and has_custom_DAT:
                    dialog = xbmcgui.Dialog()
                    ret = dialog.yesno('Advanced Emulator Launcher',
                        'Delete No-Intro/Redump XML DAT file?')
                    if not ret: return
                    self.launchers[launcherID]['audit_custom_dat_file'] = ''
                    kodi_notify('Removed custom XML DAT file')

                elif type2 == 4 and not has_custom_DAT:
                    # --- Browse for No-Intro file ---
                    # BUG For some reason *.dat files are not shown on the dialog, but XML files are OK!!!
                    # Fixed in Krypton Beta 6 http://forum.kodi.tv/showthread.php?tid=298161
                    dialog = xbmcgui.Dialog()
                    dat_file = dialog.browse(1, 'Select No-Intro XML DAT (XML|DAT)',
                        'files', '.dat|.xml')
                    if not FileName(dat_file).exists(): return
                    self.launchers[launcherID]['audit_custom_dat_file'] = dat_file
                    kodi_notify_warn('Added custom XML DAT file')

        # --- Launcher Advanced Modifications menu option ---
        type_nb = type_nb + 1
        if type == type_nb:
            toggle_window_str = 'ON' if self.launchers[launcherID]['toggle_window'] else 'OFF'
            non_blocking_str = 'ON' if self.launchers[launcherID]['non_blocking'] else 'OFF'
            multidisc_str = 'ON' if self.launchers[launcherID]['multidisc'] else 'OFF'
            filter_str   = '.bat|.exe|.cmd' if sys.platform == 'win32' else ''
            if self.launchers[launcherID]['application'] == RETROPLAYER_LAUNCHER_APP_NAME:
                launcher_str = 'Kodi Retroplayer'
            elif self.launchers[launcherID]['application'] == LNK_LAUNCHER_APP_NAME:
                launcher_str = 'LNK Launcher'
            else:
                launcher_str = "'{0}'".format(self.launchers[launcherID]['application'])

            # --- Standalone launcher -------------------------------------------------------------
            if self.launchers[launcherID]['rompath'] == '':
                type2 = dialog.select('Launcher Advanced Modifications',
                                      ["Change Application: {0}".format(launcher_str),
                                       "Modify Arguments: '{0}'".format(self.launchers[launcherID]['args']),
                                       "Modify Aditional arguments ...",
                                       "Toggle Kodi into windowed mode (now {0})".format(toggle_window_str),
                                       "Non-blocking launcher (now {0})".format(non_blocking_str)])
            # --- ROMS launcher -------------------------------------------------------------------
            else:
                type2 = dialog.select('Launcher Advanced Modifications',
                                      ["Change Application: {0}".format(launcher_str),
                                       "Modify Arguments: '{0}'".format(self.launchers[launcherID]['args']),
                                       "Aditional arguments ...",
                                       "Change ROM path: '{0}'".format(self.launchers[launcherID]['rompath']),
                                       "Modify ROM extensions: '{0}'".format(self.launchers[launcherID]['romext']),
                                       "Toggle Kodi into windowed mode (now {0})".format(toggle_window_str),
                                       "Non-blocking launcher (now {0})".format(non_blocking_str),
                                       "Multidisc ROM support (now {0})".format(multidisc_str)])

            # --- Launcher application path menu option ---
            type2_nb = 0
            if type2 == type2_nb:
                # >> Choose launching mechanism
                LAUNCHER_ROM         = 1
                LAUNCHER_RETROPLAYER = 2
                LAUNCHER_LNK         = 3
                if sys.platform == 'win32':
                    answer = dialog.select('Choose launcher mechanism',
                                          ['Use Kodi Retroplayer',
                                           'Use Windows LNK launcher',
                                           'Choose launching application'])
                    if answer < 0: return
                    if   answer == 0: launcher_type = LAUNCHER_RETROPLAYER
                    elif answer == 1: launcher_type = LAUNCHER_LNK
                    elif answer == 2: launcher_type = LAUNCHER_ROM
                else:
                    answer = kodi_dialog_yesno('Use Kodi Retroplayer in this launcher? '
                                               'Answer NO to choose a new launching application.')
                    if answer: launcher_type = LAUNCHER_RETROPLAYER
                    else:      launcher_type = LAUNCHER_ROM

                # >> Choose launching application
                if launcher_type == LAUNCHER_RETROPLAYER:
                    self.launchers[launcherID]['application'] = RETROPLAYER_LAUNCHER_APP_NAME
                    kodi_notify('Launcher app is Retroplayer')
                elif launcher_type == LAUNCHER_LNK:
                    self.launchers[launcherID]['application'] = LNK_LAUNCHER_APP_NAME
                    kodi_notify('Launcher app is Windows LNK launcher')
                elif launcher_type == LAUNCHER_ROM:
                    app = xbmcgui.Dialog().browse(1, 'Select the launcher application', 'files', '',
                                                  False, False, self.launchers[launcherID]['application'])
                    if not app: return
                    self.launchers[launcherID]['application'] = app
                    kodi_notify('Changed launcher application')

            # --- Edition of the launcher arguments ---
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]['args'], 'Edit application arguments')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                self.launchers[launcherID]['args'] = keyboard.getText()
                kodi_notify('Changed launcher arguments')

            # --- Launcher Additional arguments ---
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                launcher = self.launchers[launcherID]
                additional_args_list = []
                for extra_arg in launcher['args_extra']:
                    additional_args_list.append("Modify '{0}'".format(extra_arg))
                type_aux = dialog.select('Launcher additional arguments',
                                         ['Add new additional arguments ...'] + additional_args_list)
                if type_aux < 0: return

                # >> Add new additional arguments
                if type_aux == 0:
                    keyboard = xbmc.Keyboard('', 'Edit launcher additional arguments')
                    keyboard.doModal()
                    if not keyboard.isConfirmed(): return
                    launcher['args_extra'].append(keyboard.getText())
                    log_debug('_command_edit_launcher() Appending extra_args to launcher {0}'.format(launcherID))
                    kodi_notify('Added additional arguments in position {0}'.format(len(launcher['args_extra'])))
                elif type_aux >= 1:
                    arg_index = type_aux - 1
                    type_aux_2 = dialog.select('Modify extra arguments {0}'.format(type_aux),
                                               ["Edit '{0}' ...".format(launcher['args_extra'][arg_index]),
                                                'Delete extra arguments'])
                    if type_aux_2 < 0: return

                    if type_aux_2 == 0:
                        keyboard = xbmc.Keyboard(launcher['args_extra'][arg_index], 'Edit application arguments')
                        keyboard.doModal()
                        if not keyboard.isConfirmed(): return
                        launcher['args_extra'][arg_index] = keyboard.getText()
                        log_debug('_command_edit_launcher() Edited args_extra[{0}] to "{1}"'.format(arg_index, launcher['args_extra'][arg_index]))
                        kodi_notify('Changed launcher extra arguments {0}'.format(type_aux))
                    elif type_aux_2 == 1:
                        ret = kodi_dialog_yesno('Are you sure you want to delete Launcher additional arguments {0}?'.format(type_aux))
                        if not ret: return
                        del launcher['args_extra'][arg_index]
                        log_debug("_command_edit_launcher() Deleted launcher['args_extra'][{0}]".format(arg_index))
                        kodi_notify('Changed launcher extra arguments {0}'.format(type_aux))

            if self.launchers[launcherID]['rompath'] != '':
                # --- Launcher ROM path menu option (Only ROM launchers) ---
                type2_nb = type2_nb + 1
                if type2 == type2_nb:
                    rom_path = dialog.browse(0, 'Select Files path', 'files', '',
                                             False, False, self.launchers[launcherID]['rompath'])
                    self.launchers[launcherID]['rompath'] = rom_path
                    kodi_notify('Changed ROM path')

                # --- Edition of the launcher ROM extension (Only ROM launchers) ---
                type2_nb = type2_nb + 1
                if type2 == type2_nb:
                    keyboard = xbmc.Keyboard(self.launchers[launcherID]['romext'],
                                             'Edit ROM extensions, use "|" as separator. (e.g lnk|cbr)')
                    keyboard.doModal()
                    if not keyboard.isConfirmed(): return
                    self.launchers[launcherID]['romext'] = keyboard.getText()
                    kodi_notify('Changed ROM extensions')

            # --- Minimise Kodi window flag ---
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                p_idx = 1 if self.launchers[launcherID]['toggle_window'] else 0
                type3 = dialog.select('Toggle Kodi into windowed mode', ['OFF (default)', 'ON'], preselect = p_idx)
                if type3 < 0: return
                self.launchers[launcherID]['toggle_window'] = True if type3 == 1 else False
                minimise_str = 'ON' if self.launchers[launcherID]['toggle_window'] else 'OFF'
                kodi_notify('Toggle Kodi into windowed mode {0}'.format(minimise_str))

            # --- Non-blocking launcher flag ---
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                p_idx = 1 if self.launchers[launcherID]['non_blocking'] else 0
                type3 = dialog.select('Non-blocking launcher', ['OFF (default)', 'ON'], preselect = p_idx)
                if type3 < 0: return
                self.launchers[launcherID]['non_blocking'] = True if type3 == 1 else False
                non_blocking_str = 'ON' if self.launchers[launcherID]['non_blocking'] else 'OFF'
                kodi_notify('Launcher Non-blocking is now {0}'.format(non_blocking_str))

            # --- Multidisc ROM support (Only ROM launchers) ---
            if self.launchers[launcherID]['rompath'] != '':
                type2_nb = type2_nb + 1
                if type2 == type2_nb:
                    p_idx = 1 if self.launchers[launcherID]['multidisc'] else 0
                    type3 = dialog.select('Non-blocking launcher', ['OFF', 'ON (default)'], preselect = p_idx)
                    if type3 < 0: return
                    self.launchers[launcherID]['multidisc'] = True if type3 == 1 else False
                    multidisc_str = 'ON' if self.launchers[launcherID]['multidisc'] else 'OFF'
                    kodi_notify('Launcher Multidisc support is now {0}'.format(multidisc_str))

        # --- Export Launcher XML configuration ---
        type_nb = type_nb + 1
        if type == type_nb:
            launcher = self.launchers[launcherID]
            launcher_fn_str = 'Launcher_' + text_title_to_filename_str(launcher['m_name']) + '.xml'
            log_debug('_command_edit_launcher() Exporting Launcher configuration')
            log_debug('_command_edit_launcher() Name     "{0}"'.format(launcher['m_name']))
            log_debug('_command_edit_launcher() ID       {0}'.format(launcher['id']))
            log_debug('_command_edit_launcher() l_fn_str "{0}"'.format(launcher_fn_str))

            # >> Ask user for a path to export the launcher configuration
            dir_path = xbmcgui.Dialog().browse(0, 'Select XML export directory', 'files',
                                               '', False, False)
            if not dir_path: return
            export_FN = FileName(dir_path).pjoin(launcher_fn_str)
            if export_FN.exists():
                ret = kodi_dialog_yesno('Overwrite file {0}?'.format(export_FN.getPath()))
                if not ret:
                    kodi_notify_warn('Export of Launcher XML cancelled')
                    return

            # --- Print error message is something goes wrong writing file ---
            try:
                autoconfig_export_launcher(launcher, export_FN, self.categories)
            except AddonError as E:
                kodi_notify_warn('{0}'.format(E))
            else:
                kodi_notify('Exported Launcher "{0}" XML config'.format(launcher['m_name']))
            # >> No need to update categories.xml and timestamps so return now.
            return

        # --- Remove Launcher menu option ---
        type_nb = type_nb + 1
        if type == type_nb:
            rompath = self.launchers[launcherID]['rompath']
            launcher_name = self.launchers[launcherID]['m_name']
            # >> Standalone launcher
            if rompath == '':
                ret = kodi_dialog_yesno('Launcher "{0}" is standalone. '.format(launcher_name) +
                                        'Are you sure you want to delete it?')
            # >> ROMs launcher
            else:
                roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, self.launchers[launcherID])
                num_roms = len(roms)
                ret = kodi_dialog_yesno('Launcher "{0}" has {1} ROMs. '.format(launcher_name, num_roms) +
                                        'Are you sure you want to delete it?')
            if not ret: return

            # >> Remove JSON/XML file if exist
            # >> Remove launcher from database. Categories.xml will be saved at the end of function
            fs_unlink_ROMs_database(g_PATHS.ROMS_DIR, self.launchers[launcherID])
            self.launchers.pop(launcherID)
            kodi_notify('Deleted Launcher {0}'.format(launcher_name))

        # User pressed cancel or close dialog
        if type < 0: return

        # >> If this point is reached then changes to launcher metadata/assets were made.
        # >> Save categories and update container contents so user sees those changes inmediately.
        # NOTE Update edited launcher timestamp only if launcher was not deleted!
        if launcherID in self.launchers: self.launchers[launcherID]['timestamp_launcher'] = time.time()
        fs_write_catfile(g_PATHS.CATEGORIES_FILE_PATH, self.categories, self.launchers)
        kodi_refresh_container()

    # Add ROMS to launcher
    # DEPRECATED function, not used anymore.
    def _command_add_roms(self, launcher):
        dialog = xbmcgui.Dialog()
        type = dialog.select('Add/Update ROMs to Launcher', ['Scan for New ROMs', 'Manually Add ROM'])
        if type == 0:
            self._roms_import_roms(launcher)
        elif type == 1:
            self._roms_add_new_rom(launcher)

    # Former _edit_rom()
    # Note that categoryID = VCATEGORY_FAVOURITES_ID, launcherID = VLAUNCHER_FAVOURITES_ID if we are editing
    # a ROM in Favourites.
    def _command_edit_rom(self, categoryID, launcherID, romID):
        # --- ---
        if romID == UNKNOWN_ROMS_PARENT_ID:
            kodi_dialog_OK('You cannot edit this ROM!')
            return

        # --- Load ROMs ---
        if categoryID == VCATEGORY_FAVOURITES_ID:
            log_debug('_command_edit_rom() Editing Favourite ROM')
            roms = fs_load_Favourites_JSON(g_PATHS.FAV_JSON_FILE_PATH)
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            log_debug('_command_edit_rom() Editing Collection ROM')
            (collections, update_timestamp) = fs_load_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH)
            collection = collections[launcherID]

            roms_json_file = g_PATHS.COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
            collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
            # NOTE ROMs in a collection are stored as a list and ROMs in Favourites are stored as
            #      a dictionary. Convert the Collection list into an ordered dictionary and then
            #      converted back the ordered dictionary into a list before saving the collection.
            roms = OrderedDict()
            for collection_rom in collection_rom_list:
                roms[collection_rom['id']] = collection_rom
        else:
            log_debug('_command_edit_rom() Editing ROM in Launcher')
            launcher = self.launchers[launcherID]
            roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, launcher)

        # --- Show a dialog with ROM editing options ---
        rom_name = roms[romID]['m_name']
        finished_display = 'Status: Finished' if roms[romID]['finished'] == True else 'Status: Unfinished'
        dialog = xbmcgui.Dialog()
        if categoryID == VCATEGORY_FAVOURITES_ID:
            type = dialog.select('Edit ROM {0}'.format(rom_name),
                                ['Edit Metadata ...', 'Edit Assets/Artwork ...', finished_display,
                                 'Advanced Modifications ...',
                                 'Delete Favourite ROM',
                                 'Manage Favourite ROM object ...'])
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            type = dialog.select('Edit ROM {0}'.format(rom_name),
                                ['Edit Metadata ...', 'Edit Assets/Artwork ...', finished_display,
                                 'Advanced Modifications ...',
                                 'Delete Collection ROM',
                                 'Manage Collection ROM object ...',
                                 'Manage Collection ROM position ...'])
        else:
            type = dialog.select('Edit ROM {0}'.format(rom_name),
                                ['Edit Metadata ...', 'Edit Assets/Artwork ...', finished_display,
                                 'Advanced Modifications ...',
                                 'Delete ROM'])
        if type < 0: return

        # --- Edit ROM metadata ---
        if type == 0:
            # --- Make a menu list of available metadata scrapers ---
            g_scrap_factory = ScraperFactory(g_PATHS, self.settings)
            scraper_menu_list = g_scrap_factory.get_metadata_scraper_menu_list()

            # --- Metadata edit dialog ---
            NFO_FileName = fs_get_ROM_NFO_name(roms[romID])
            NFO_found_str = 'NFO found' if NFO_FileName.exists() else 'NFO not found'
            plot_str = text_limit_string(roms[romID]['m_plot'], PLOT_STR_MAXSIZE)
            common_menu_list = [
                "Edit Title: '{0}'".format(roms[romID]['m_name']),
                "Edit Release Year: '{0}'".format(roms[romID]['m_year']),
                "Edit Genre: '{0}'".format(roms[romID]['m_genre']),
                "Edit Developer: '{0}'".format(roms[romID]['m_developer']),
                "Edit NPlayers: '{0}'".format(roms[romID]['m_nplayers']),
                "Edit ESRB rating: '{0}'".format(roms[romID]['m_esrb']),
                "Edit Rating: '{0}'".format(roms[romID]['m_rating']),
                "Edit Plot: '{0}'".format(plot_str),
                'Load Plot from TXT file ...',
                'Import NFO file ({0})'.format(NFO_found_str),
                'Save NFO file',
            ]
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Modify ROM metadata', common_menu_list + scraper_menu_list)
            if type2 < 0: return

            # --- Edit of the rom title ---
            if type2 == 0:
                keyboard = xbmc.Keyboard(roms[romID]['m_name'], 'Edit Title')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                title = keyboard.getText()
                if title == '': title = roms[romID]['m_name']
                roms[romID]['m_name'] = title
                kodi_notify('Changed ROM Title')

            # --- Edition of the rom release year ---
            elif type2 == 1:
                keyboard = xbmc.Keyboard(roms[romID]['m_year'], 'Edit Release Year')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                roms[romID]['m_year'] = keyboard.getText()
                kodi_notify('Changed ROM Release Year')

            # --- Edition of the rom game genre ---
            elif type2 == 2:
                keyboard = xbmc.Keyboard(roms[romID]['m_genre'], 'Edit genre')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                roms[romID]['m_genre'] = keyboard.getText()
                kodi_notify('Changed ROM Genre')

            # --- Edition of the rom developer ---
            elif type2 == 3:
                keyboard = xbmc.Keyboard(roms[romID]['m_developer'], 'Edit developer')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                roms[romID]['m_developer'] = keyboard.getText()
                kodi_notify('Changed ROM Developer')

            # --- Edition of launcher NPlayers ---
            elif type2 == 4:
                # >> Show a dialog select with the most used NPlayer entries, and have one option
                # >> for manual entry.
                menu_list = ['Not set', 'Manual entry'] + NPLAYERS_LIST
                np_idx = dialog.select('Edit Launcher NPlayers', menu_list)
                if np_idx < 0: return

                if np_idx == 0:
                    roms[romID]['m_nplayers'] = ''
                    kodi_notify('Launcher NPlayers change to Not Set')
                elif np_idx == 1:
                    # >> Manual entry. Open a text entry dialog.
                    keyboard = xbmc.Keyboard(roms[romID]['m_nplayers'], 'Edit NPlayers')
                    keyboard.doModal()
                    if not keyboard.isConfirmed(): return
                    roms[romID]['m_nplayers'] = keyboard.getText()
                    kodi_notify('Changed Launcher NPlayers')
                else:
                    list_idx = np_idx - 2
                    roms[romID]['m_nplayers'] = NPLAYERS_LIST[list_idx]
                    kodi_notify('Changed Launcher NPlayers')

            # --- Edition of launcher ESRB rating ---
            elif type2 == 5:
                # >> Show a dialog select with the available ratings
                # >> Kodi Krypton: preselect current rating in select list
                esrb_index = dialog.select('Edit Launcher ESRB rating', ESRB_LIST)
                if esrb_index < 0: return
                roms[romID]['m_esrb'] = ESRB_LIST[esrb_index]
                kodi_notify('Changed Launcher ESRB rating')

            # --- Edition of the ROM rating ---
            elif type2 == 6:
                rating = dialog.select('Edit ROM Rating',
                                      ['Not set',  'Rating 0', 'Rating 1', 'Rating 2', 'Rating 3', 'Rating 4',
                                       'Rating 5', 'Rating 6', 'Rating 7', 'Rating 8', 'Rating 9', 'Rating 10'])
                # >> Rating not set, empty string
                if rating == 0:
                    roms[romID]['m_rating'] = ''
                    kodi_notify('Changed ROM Rating to Not Set')
                elif rating >= 1 and rating <= 11:
                    roms[romID]['m_rating'] = '{0}'.format(rating - 1)
                    kodi_notify('Changed ROM Rating to {0}'.format(roms[romID]['m_rating']))
                elif rating < 0:
                    kodi_dialog_OK("ROM rating '{0}' not changed".format(roms[romID]['m_rating']))
                    return

            # --- Edit ROM description (plot) ---
            elif type2 == 7:
                keyboard = xbmc.Keyboard(roms[romID]['m_plot'], 'Edit plot')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                roms[romID]['m_plot'] = keyboard.getText()
                kodi_notify('Changed ROM Plot')

            # --- Import of the rom game plot from TXT file ---
            elif type2 == 8:
                dialog = xbmcgui.Dialog()
                text_file = dialog.browse(1, 'Select description file (TXT|DAT)',
                                          'files', '.txt|.dat', False, False)
                text_file_path = FileName(text_file)
                if text_file_path.exists():
                    file_data = self._gui_import_TXT_file(text_file_path)
                    roms[romID]['m_plot'] = file_data
                    kodi_notify('Imported ROM Plot')
                else:
                    desc_str = text_limit_string(roms[romID]['m_plot'], PLOT_STR_MAXSIZE)
                    kodi_dialog_OK("Launcher plot '{0}' not changed".format(desc_str))
                    return

            # --- Import ROM metadata from NFO file ---
            elif type2 == 9:
                if launcherID == VLAUNCHER_FAVOURITES_ID:
                    kodi_dialog_OK('Importing NFO file is not allowed for ROMs in Favourites.')
                    return
                if not fs_import_ROM_NFO(roms, romID): return

            # --- Export ROM metadata to NFO file ---
            elif type2 == 10:
                if launcherID == VLAUNCHER_FAVOURITES_ID:
                    kodi_dialog_OK('Exporting NFO file is not allowed for ROMs in Favourites.')
                    return
                fs_export_ROM_NFO(roms[romID])
                return # No need to save ROMs

            # --- Scrap ROM metadata ---
            elif type2 >= 11:
                # --- Use the scraper chosen by user ---
                scraper_index = type2 - len(common_menu_list)
                scraper_ID = g_scrap_factory.get_metadata_scraper_ID_from_menu_idx(scraper_index)

                # --- Grab data ---
                object_dic = roms[romID]
                ROM = FileName(roms[romID]['filename'])
                if categoryID == VCATEGORY_FAVOURITES_ID or categoryID == VCATEGORY_COLLECTIONS_ID:
                    platform = roms[romID]['platform']
                else:
                    platform = self.launchers[launcherID]['platform']
                if roms[romID]['disks']:
                    # Multidisc ROM. Take first file of the set.
                    ROM_checksums_FN = FileName(ROM.getDir()).pjoin(roms[romID]['disks'][0])
                else:
                    ROM_checksums_FN = ROM
                data_dic = {
                    'rom_FN' : ROM,
                    'rom_checksums_FN' : ROM_checksums_FN,
                    'platform' : platform,
                }

                # --- Scrape! ---
                # If status_dic['status'] is False then some error happened. Do not save
                # the database and return immediately.
                # Scraper caches are flushed. An error here could mean that no metadata
                # was found, however the cache can have valid data for the candidates.
                # Remember to flush caches after scraping.
                scrap_strategy = g_scrap_factory.create_CM_metadata(scraper_ID)
                status_dic = scrap_strategy.scrap_CM_metadata_ROM(object_dic, data_dic)
                g_scrap_factory.destroy_CM()
                kodi_display_user_message(status_dic)
                if not status_dic['status']: return

        # --- Edit ROMs Assets/Artwork ---
        elif type == 1:
            rom = roms[romID]

            # >> Build asset image list for dialog
            label2_fanart    = rom['s_fanart']    if rom['s_fanart']    else 'Not set'
            label2_banner    = rom['s_banner']    if rom['s_banner']    else 'Not set'
            label2_clearlogo = rom['s_clearlogo'] if rom['s_clearlogo'] else 'Not set'
            label2_title     = rom['s_title']     if rom['s_title']     else 'Not set'
            label2_snap      = rom['s_snap']      if rom['s_snap']      else 'Not set'
            label2_boxfront  = rom['s_boxfront']  if rom['s_boxfront']  else 'Not set'
            label2_boxback   = rom['s_boxback']   if rom['s_boxback']   else 'Not set'
            label2_3dbox     = rom['s_3dbox']     if rom['s_3dbox']     else 'Not set'
            label2_cartridge = rom['s_cartridge'] if rom['s_cartridge'] else 'Not set'
            label2_flyer     = rom['s_flyer']     if rom['s_flyer']     else 'Not set'
            label2_map       = rom['s_map']       if rom['s_map']       else 'Not set'
            label2_manual    = rom['s_manual']    if rom['s_manual']    else 'Not set'
            label2_trailer   = rom['s_trailer']   if rom['s_trailer']   else 'Not set'

            img_fanart       = rom['s_fanart']          if rom['s_fanart']    else 'DefaultAddonNone.png'
            img_banner       = rom['s_banner']          if rom['s_banner']    else 'DefaultAddonNone.png'
            img_clearlogo    = rom['s_clearlogo']       if rom['s_clearlogo'] else 'DefaultAddonNone.png'
            img_title        = rom['s_title']           if rom['s_title']     else 'DefaultAddonNone.png'
            img_snap         = rom['s_snap']            if rom['s_snap']      else 'DefaultAddonNone.png'
            img_boxfront     = rom['s_boxfront']        if rom['s_boxfront']  else 'DefaultAddonNone.png'
            img_boxback      = rom['s_boxback']         if rom['s_boxback']   else 'DefaultAddonNone.png'
            img_3dbox        = rom['s_3dbox']           if rom['s_3dbox']     else 'DefaultAddonNone.png'
            img_cartridge    = rom['s_cartridge']       if rom['s_cartridge'] else 'DefaultAddonNone.png'
            img_flyer        = rom['s_flyer']           if rom['s_flyer']     else 'DefaultAddonNone.png'
            img_map          = rom['s_map']             if rom['s_map']       else 'DefaultAddonNone.png'
            img_manual       = 'DefaultAddonImages.png' if rom['s_manual']    else 'DefaultAddonNone.png'
            img_trailer      = 'DefaultAddonVideo.png'  if rom['s_trailer']   else 'DefaultAddonNone.png'

            # >> Create ListItem objects for select dialog
            fanart_listitem    = xbmcgui.ListItem(label = 'Edit Fanart ...',             label2 = label2_fanart)
            banner_listitem    = xbmcgui.ListItem(label = 'Edit Banner / Marquee ...',   label2 = label2_banner)
            clearlogo_listitem = xbmcgui.ListItem(label = 'Edit Clearlogo ...',          label2 = label2_clearlogo)
            title_listitem     = xbmcgui.ListItem(label = 'Edit Title ...',              label2 = label2_title)
            snap_listitem      = xbmcgui.ListItem(label = 'Edit Snap ...',               label2 = label2_snap)
            boxfront_listitem  = xbmcgui.ListItem(label = 'Edit Boxfront / Cabinet ...', label2 = label2_boxfront)
            boxback_listitem   = xbmcgui.ListItem(label = 'Edit Boxback / CPanel ...',   label2 = label2_boxback)
            tdbox_listitem     = xbmcgui.ListItem(label = 'Edit 3D Box ...',             label2 = label2_3dbox)
            cartridge_listitem = xbmcgui.ListItem(label = 'Edit Cartridge / PCB ...',    label2 = label2_cartridge)
            flyer_listitem     = xbmcgui.ListItem(label = 'Edit Flyer ...',              label2 = label2_flyer)
            map_listitem       = xbmcgui.ListItem(label = 'Edit Map ...',                label2 = label2_map)
            manual_listitem    = xbmcgui.ListItem(label = 'Edit Manual ...',             label2 = label2_manual)
            trailer_listitem   = xbmcgui.ListItem(label = 'Edit Trailer ...',            label2 = label2_trailer)

            fanart_listitem.setArt({'icon' : img_fanart})
            banner_listitem.setArt({'icon' : img_banner})
            clearlogo_listitem.setArt({'icon' : img_clearlogo})
            title_listitem.setArt({'icon' : img_title})
            snap_listitem.setArt({'icon' : img_snap})
            boxfront_listitem.setArt({'icon' : img_boxfront})
            boxback_listitem.setArt({'icon' : img_boxback})
            tdbox_listitem.setArt({'icon' : img_3dbox})
            cartridge_listitem.setArt({'icon' : img_cartridge})
            flyer_listitem.setArt({'icon' : img_flyer})
            map_listitem.setArt({'icon' : img_map})
            manual_listitem.setArt({'icon' : img_manual})
            trailer_listitem.setArt({'icon' : img_trailer})

            # --- Execute select dialog ---
            # Make sure this follows the same order as ROM_ASSET_ID_LIST
            listitems = [
                fanart_listitem,
                banner_listitem,
                clearlogo_listitem,
                title_listitem,
                snap_listitem,
                boxfront_listitem,
                boxback_listitem,
                tdbox_listitem,
                cartridge_listitem,
                flyer_listitem,
                map_listitem,
                manual_listitem,
                trailer_listitem,
            ]
            type2 = dialog.select('Edit ROM Assets/Artwork', list = listitems, useDetails = True)
            if type2 < 0: return

            # --- Edit Assets ---
            # If this function returns False no changes were made. No need to save categories XML
            # and update container.
            asset_kind = ROM_ASSET_ID_LIST[type2]
            if not self._gui_edit_asset(KIND_ROM, asset_kind, rom, categoryID, launcherID): return

        # --- Edit status ---
        elif type == 2:
            finished = roms[romID]['finished']
            finished = False if finished else True
            finished_display = 'Finished' if finished == True else 'Unfinished'
            roms[romID]['finished'] = finished
            kodi_dialog_OK("ROM '{0}' status is now {1}".format(roms[romID]['m_name'], finished_display))

        # --- Advanced ROM Modifications ---
        elif type == 3:
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Advanced ROM Modifications', [
                "Change ROM file: '{0}'".format(roms[romID]['filename']),
                "Alternative application: '{0}'".format(roms[romID]['altapp']),
                "Alternative arguments: '{0}'".format(roms[romID]['altarg']),
            ])
            if type2 < 0: return

            # >> Change ROM file
            if type2 == 0:
                # >> Abort if multidisc ROM
                if roms[romID]['disks']:
                    kodi_dialog_OK('Edition of multidisc ROMs not supported yet.')
                    return
                filename = roms[romID]['filename']
                launcher = self.launchers[launcherID]
                romext   = launcher['romext']
                item_file = xbmcgui.Dialog().browse(1, 'Select the file', 'files', '.' + romext.replace('|', '|.'),
                                                    False, False, filename)
                if not item_file: return
                roms[romID]['filename'] = item_file
            # >> Alternative launcher application file path
            elif type2 == 1:
                filter_str = '.bat|.exe|.cmd' if sys.platform == 'win32' else ''
                altapp = xbmcgui.Dialog().browse(1, 'Select ROM custom launcher application',
                                                 'files', filter_str,
                                                 False, False, roms[romID]['altapp'])
                # Returns empty browse if dialog was canceled.
                if not altapp: return
                roms[romID]['altapp'] = altapp
            # >> Alternative launcher arguments
            elif type2 == 2:
                keyboard = xbmc.Keyboard(roms[romID]['altarg'], 'Edit ROM custom application arguments')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                roms[romID]['altarg'] = keyboard.getText()

        # --- Delete ROM ---
        elif type == 4:
            is_Normal_Launcher = True
            if categoryID == VCATEGORY_FAVOURITES_ID and launcherID == VLAUNCHER_FAVOURITES_ID:
                log_info('_command_remove_rom() Deleting ROM from Favourites (id {0})'.format(romID))
                msg_str = 'Are you sure you want to delete it from Favourites?'
                is_Normal_Launcher = False
            elif categoryID == VCATEGORY_COLLECTIONS_ID:
                log_info('_command_remove_rom() Deleting ROM from Collection (id {0})'.format(romID))
                msg_str = 'Are you sure you want to delete it from Collection "{0}"?'.format(collection['m_name'])
                is_Normal_Launcher = False
            else:
                if launcher['audit_state'] == AUDIT_STATE_ON and \
                    roms[romID]['nointro_status'] == NOINTRO_STATUS_MISS:
                    kodi_dialog_OK(
                        'You are trying to remove a Missing ROM. You cannot delete '
                        'a ROM that does not exist! If you want to get rid of all missing '
                        'ROMs then delete the XML DAT file.')
                    return
                else:
                    log_info('_command_remove_rom() Deleting ROM from Launcher (id {0})'.format(romID))
                    msg_str = 'Are you sure you want to delete it from Launcher "{0}"?'.format(launcher['m_name'])

            # --- Confirm deletion ---
            rom_name = roms[romID]['m_name']
            ret = kodi_dialog_yesno('ROM "{0}". '.format(rom_name) + msg_str)
            if not ret: return
            roms.pop(romID)

            # --- If there is a No-Intro XML configured audit ROMs ---
            if is_Normal_Launcher and launcher['audit_state'] == AUDIT_STATE_ON:
                log_info('No-Intro/Redump DAT configured. Starting ROM audit ...')
                nointro_xml_FN = self._roms_set_NoIntro_DAT(launcher)
                if not self._roms_update_NoIntro_status(launcher, roms, nointro_xml_FN):
                    kodi_notify_warn('Error auditing ROMs. XML DAT file unset.')

            # --- Notify user ---
            kodi_notify('Deleted ROM {0}'.format(rom_name))

        # --- Manage Favourite/Collection ROM object (ONLY for Favourite/Collection ROMs) ---
        elif type == 5:
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Manage ROM object', [
                'Choose another parent ROM (launcher info only) ...', # 0
                'Choose another parent ROM (update all) ...',         # 1
                'Copy launcher info from parent ROM',                 # 2
                'Copy metadata from parent ROM',                      # 3
                'Copy assets/artwork from parent ROM',                # 4
                'Copy all from parent ROM',                           # 5
                'Manage default Assets/Artwork ...'])
            if type2 < 0: return

            # --- Choose another parent ROM ---
            if type2 == 0 or type2 == 1:
                # --- STEP 1: select new launcher ---
                launcher_IDs = []
                launcher_names = []
                for launcher_id in self.launchers:
                    # >> ONLY SHOW ROMs LAUNCHERS, NOT STANDALONE LAUNCHERS!!!
                    if self.launchers[launcher_id]['rompath'] == '': continue
                    launcher_IDs.append(launcher_id)
                    launcher_names.append(self.launchers[launcher_id]['m_name'])

                # >> Order alphabetically both lists
                sorted_idx = [i[0] for i in sorted(enumerate(launcher_names), key=lambda x:x[1])]
                launcher_IDs   = [launcher_IDs[i] for i in sorted_idx]
                launcher_names = [launcher_names[i] for i in sorted_idx]
                dialog = xbmcgui.Dialog()
                selected_launcher = dialog.select('New launcher for {0}'.format(roms[romID]['m_name']), launcher_names)
                if selected_launcher < 0: return

                # --- STEP 2: select ROMs in that launcher ---
                launcher_id   = launcher_IDs[selected_launcher]
                launcher_roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, self.launchers[launcher_id])
                if not launcher_roms: return
                roms_IDs = []
                roms_names = []
                for rom_id in launcher_roms:
                    # ROMs with nointro_status = 'Miss' are invalid! Do not add to the list
                    if launcher_roms[rom_id]['nointro_status'] == 'Miss': continue
                    roms_IDs.append(rom_id)
                    roms_names.append(launcher_roms[rom_id]['m_name'])
                sorted_idx = [i[0] for i in sorted(enumerate(roms_names), key=lambda x:x[1])]
                roms_IDs   = [roms_IDs[i] for i in sorted_idx]
                roms_names = [roms_names[i] for i in sorted_idx]
                selected_rom = dialog.select('New ROM for Favourite {0}'.format(roms[romID]['m_name']), roms_names)
                if selected_rom < 0 : return

                # >> Collect ROM object.
                old_fav_rom_ID  = romID
                new_fav_rom_ID  = roms_IDs[selected_rom]
                old_fav_rom     = roms[romID]
                parent_rom      = launcher_roms[new_fav_rom_ID]
                parent_launcher = self.launchers[launcher_id]

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
                    old_fav_position = list(roms.keys()).index(old_fav_rom_ID)
                    dic_index = 0
                    new_roms_orderded_dict = roms.__class__()
                    for key, value in list(roms.items()):
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
                if fav_launcher_id not in self.launchers:
                    kodi_dialog_OK('Parent Launcher not found. '
                                   'Relink this ROM before copying stuff from parent.')
                    return
                parent_launcher = self.launchers[fav_launcher_id]
                launcher_roms   = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, parent_launcher)
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

                # >> Notify user
                if categoryID == VCATEGORY_FAVOURITES_ID:    kodi_notify('Updated Favourite ROM {0}'.format(info_str))
                elif categoryID == VCATEGORY_COLLECTIONS_ID: kodi_notify('Updated Collection ROM {0}'.format(info_str))

            # --- Choose default Favourite/Collection assets/artwork ---
            elif type2 == 6:
                rom = roms[romID]

                # >> Label1 an label2
                asset_icon_str      = assets_get_asset_name_str(rom['roms_default_icon'])
                asset_fanart_str    = assets_get_asset_name_str(rom['roms_default_fanart'])
                asset_banner_str    = assets_get_asset_name_str(rom['roms_default_banner'])
                asset_poster_str    = assets_get_asset_name_str(rom['roms_default_poster'])
                asset_clearlogo_str = assets_get_asset_name_str(rom['roms_default_clearlogo'])

                label2_thumb        = rom[rom['roms_default_icon']]     if rom[rom['roms_default_icon']]     else 'Not set'
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
                img_icon            = rom[rom['roms_default_icon']]     if rom[rom['roms_default_icon']]     else 'DefaultAddonNone.png'
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
                    assets_choose_category_ROM(rom, 'roms_default_icon', type_s)
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
        elif type == 6:
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
                current_ROM_position = list(roms.keys()).index(romID)
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
                new_order = list(range(num_roms))
                # >> Delete current element
                del new_order[current_ROM_position]
                # >> Insert current element at selected position
                new_order.insert(new_pos_index, current_ROM_position)
                log_verb('_command_edit_rom() old_order = {0}'.format(str(list(range(num_roms)))))
                log_verb('_command_edit_rom() new_order = {0}'.format(str(new_order)))

                # >> Reorder ROMs
                new_roms = OrderedDict()
                for order_idx in new_order:
                    key_value_tuple = list(roms.items())[order_idx]
                    new_roms.update({key_value_tuple[0] : key_value_tuple[1]})
                roms = new_roms

            # --- Move Collection ROM up ---
            elif type2 == 1:
                if not roms:
                    kodi_notify('Collection is empty. Add ROMs to this collection first.')
                    return

                # >> Get position of current ROM in the list
                num_roms = len(roms)
                current_ROM_position = list(roms.keys()).index(romID)
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
                new_order                           = list(range(num_roms))
                new_order[current_ROM_position - 1] = current_ROM_position
                new_order[current_ROM_position]     = current_ROM_position - 1
                new_roms = OrderedDict()
                # >> http://stackoverflow.com/questions/10058140/accessing-items-in-a-ordereddict
                for order_idx in new_order:
                    key_value_tuple = list(roms.items())[order_idx]
                    new_roms.update({key_value_tuple[0] : key_value_tuple[1]})
                roms = new_roms

            # --- Move Collection ROM down ---
            elif type2 == 2:
                if not roms:
                    kodi_notify('Collection is empty. Add ROMs to this collection first.')
                    return

                # >> Get position of current ROM in the list
                num_roms = len(roms)
                current_ROM_position = list(roms.keys()).index(romID)
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
                new_order                           = list(range(num_roms))
                new_order[current_ROM_position]     = current_ROM_position + 1
                new_order[current_ROM_position + 1] = current_ROM_position
                new_roms = OrderedDict()
                # >> http://stackoverflow.com/questions/10058140/accessing-items-in-a-ordereddict
                for order_idx in new_order:
                    key_value_tuple = list(roms.items())[order_idx]
                    new_roms.update({key_value_tuple[0] : key_value_tuple[1]})
                roms = new_roms

        # --- Save ROMs or Favourites ROMs or Collection ROMs ---
        # >> Always save if we reach this point of the function
        if launcherID == VLAUNCHER_FAVOURITES_ID:
            fs_write_Favourites_JSON(g_PATHS.FAV_JSON_FILE_PATH, roms)
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            # >> Convert back the OrderedDict into a list and save Collection
            collection_rom_list = []
            for key in roms:
                collection_rom_list.append(roms[key])

            json_file_path = g_PATHS.COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
            fs_write_Collection_ROMs_JSON(json_file_path, collection_rom_list)
        else:
            # >> Save categories/launchers to update timestamp
            #    Also update changed launcher timestamp
            self.launchers[launcherID]['num_roms'] = len(roms)
            self.launchers[launcherID]['timestamp_launcher'] = _t = time.time()
            pDialog = xbmcgui.DialogProgress()
            pDialog.create('Advanced Emulator Launcher', 'Saving ROM JSON database ...')
            pDialog.update(10)
            fs_write_ROMs_JSON(g_PATHS.ROMS_DIR, self.launchers[launcherID], roms)
            pDialog.update(90)
            fs_write_catfile(g_PATHS.CATEGORIES_FILE_PATH, self.categories, self.launchers)
            pDialog.update(100)

            # If launcher is audited then synchronise the edit ROM in the list of parents.
            if launcher['audit_state'] == AUDIT_STATE_ON:
                log_verb('Updating ROM in Parents JSON')
                parents_roms_base_noext = launcher['roms_base_noext'] + '_parents'
                pDialog.update(25, 'Loading Parents JSON ...')
                parent_roms = fs_load_JSON_file(g_PATHS.ROMS_DIR, parents_roms_base_noext)
                # >> Only edit if ROM is in parent list
                if romID in parent_roms:
                    log_verb('romID in Parent JSON. Updating ...')
                    parent_roms[romID] = roms[romID]
                pDialog.update(10, 'Saving Parents JSON ...')
                fs_write_JSON_file(g_PATHS.ROMS_DIR, parents_roms_base_noext, parent_roms)
                pDialog.update(100)
            pDialog.close()

        # It seems that updating the container does more harm than good... specially when having many ROMs
        # By the way, what is the difference between Container.Refresh() and Container.Update()?
        kodi_refresh_container()

    # ---------------------------------------------------------------------------------------------
    # Categories LisItem rendering
    # ---------------------------------------------------------------------------------------------
    #
    # Renders the addon Root window.
    #
    def _command_render_root_window(self):
        log_debug('Advanced Emulator Launcher _command_render_root_window() BEGIN')

        self._misc_set_all_sorting_methods()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)
        self._misc_clear_AEL_Launcher_Content()

        # --- Render categories in classic mode or in flat mode ---
        # This code must never fail. If categories.xml cannot be read because an upgrade
        # is necessary the user must be able to go to the "Utilities" menu.
        # <setting id="display_category_mode" values="Standard|Flat"/>
        if self.settings['display_category_mode'] == 0:
            # For every category, add it to the listbox. Order alphabetically by name.
            for cat_id in sorted(self.categories, key = lambda x : self.categories[x]['m_name']):
                self._gui_render_category_row(self.categories[cat_id], cat_id)
        else:
            # Traverse categories and sort alphabetically.
            for cat_id in sorted(self.categories, key = lambda x : self.categories[x]['m_name']):
                # Get launchers in this category alphabetically sorted.
                launcher_list = []
                for launcher_id in sorted(self.launchers, key = lambda x : self.launchers[x]['m_name']):
                    launcher = self.launchers[launcher_id]
                    if launcher['categoryID'] == cat_id: launcher_list.append(launcher)
                # Render list of launchers for this category.
                cat_name = self.categories[cat_id]['m_name']
                for launcher in launcher_list:
                    launcher_name = '[COLOR thistle]{0}[/COLOR] - {1}'.format(cat_name, launcher['m_name'])
                    self._gui_render_launcher_row(launcher, launcher_name)

        # --- Render categoryless launchers. Order alphabetically by name ---
        catless_launchers = {}
        for launcher_id, launcher in self.launchers.items():
            if launcher['categoryID'] == VCATEGORY_ADDONROOT_ID:
                catless_launchers[launcher_id] = launcher
        for launcher_id in sorted(catless_launchers, key = lambda x : catless_launchers[x]['m_name']):
            self._gui_render_launcher_row(catless_launchers[launcher_id])

        # --- AEL Favourites special category ---
        if not self.settings['display_hide_favs']:
            self._gui_render_category_favourites_row()

        # --- AEL Collections special category ---
        if not self.settings['display_hide_collections']:
            self._gui_render_category_collections_row()

        # --- AEL Virtual Categories ---
        if not self.settings['display_hide_vlaunchers']:
            self._gui_render_virtual_category_root_row()

        # --- Browse Offline Scraper database ---
        if not self.settings['display_hide_AEL_scraper']:
            self._gui_render_category_AEL_offline_scraper_row()
        # LaunchBox scraper not used any more
        # if not self.settings['display_hide_LB_scraper']:
        #     self._gui_render_category_LB_offline_scraper_row()

        # --- Recently played and most played ROMs ---
        if not self.settings['display_hide_recent']: self._gui_render_category_recently_played_row()
        if not self.settings['display_hide_mostplayed']: self._gui_render_category_most_played_row()
        if not self.settings['display_hide_utilities']: self._gui_render_Utilities_root()
        if not self.settings['display_hide_g_reports']: self._gui_render_GlobalReports_root()

        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

        log_debug('Advanced Emulator Launcher _command_render_root_window() END')

    #
    # Renders all categories without Favourites, Collections, virtual categories, etc.
    # This function is called by skins to build shortcuts menu.
    #
    def _command_render_all_categories(self):
        # >> If no categories render nothing
        if not self.categories:
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # >> For every category, add it to the listbox. Order alphabetically by name
        for key in sorted(self.categories, key = lambda x : self.categories[x]['m_name']):
            self._gui_render_category_row(self.categories[key], key)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    def _gui_render_category_row(self, category_dic, key):
        # --- Do not render row if category finished ---
        if category_dic['finished'] and self.settings['display_hide_finished']: return

        # --- Create listitem row ---
        ICON_OVERLAY = 5 if category_dic['finished'] else 4
        listitem = xbmcgui.ListItem(category_dic['m_name'])
        if category_dic['m_year']:
            listitem.setInfo('video', {'title'   : category_dic['m_name'],    'year'    : category_dic['m_year'],
                                       'genre'   : category_dic['m_genre'],   'studio'  : category_dic['m_developer'],
                                       'rating'  : category_dic['m_rating'],  'plot'    : category_dic['m_plot'],
                                       'trailer' : category_dic['s_trailer'], 'overlay' : ICON_OVERLAY })
        else:
            listitem.setInfo('video', {'title'   : category_dic['m_name'],
                                       'genre'   : category_dic['m_genre'],   'studio'  : category_dic['m_developer'],
                                       'rating'  : category_dic['m_rating'],  'plot'    : category_dic['m_plot'],
                                       'trailer' : category_dic['s_trailer'], 'overlay' : ICON_OVERLAY })
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_CATEGORY)

        # --- Set Category artwork ---
        # >> Set thumb/fanart/banner/poster/clearlogo based on user preferences
        icon_path      = asset_get_default_asset_Category(category_dic, 'default_icon', 'DefaultFolder.png')
        fanart_path    = asset_get_default_asset_Category(category_dic, 'default_fanart')
        banner_path    = asset_get_default_asset_Category(category_dic, 'default_banner')
        poster_path    = asset_get_default_asset_Category(category_dic, 'default_poster')
        clearlogo_path = asset_get_default_asset_Category(category_dic, 'default_clearlogo')
        listitem.setArt({'icon'   : icon_path,   'fanart' : fanart_path,
                         'banner' : banner_path, 'poster' : poster_path, 'clearlogo' : clearlogo_path})

        # --- Create context menu ---
        # To remove default entries like "Go to root", etc, see http://forum.kodi.tv/showthread.php?tid=227358
        commands = []
        categoryID = category_dic['id']
        commands.append(('View Category data', self._misc_url_RunPlugin('VIEW', categoryID)))
        commands.append(('Edit Category', self._misc_url_RunPlugin('EDIT_CATEGORY', categoryID)))
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY')))
        commands.append(('Add New Launcher', self._misc_url_RunPlugin('ADD_LAUNCHER', categoryID)))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', )) # If using window ID then use "10003"
        commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        # In Krypton "Add to favourites" appears always in the last position of context menu.

        if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
            listitem.addContextMenuItems(commands, replaceItems = True)

        # --- Add row ---
        url_str = self._misc_url('SHOW_LAUNCHERS', key)
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url=url_str, listitem=listitem, isFolder=True)

    def _gui_render_category_favourites_row(self):
        # fav_icon   = 'DefaultFolder.png'

        # --- Create listitem row ---
        vcategory_name   = '[COLOR silver]Favourites[/COLOR]'
        vcategory_plot   = 'Browse AEL Favourite ROMs.'
        vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Favourites_icon.png').getPath()
        vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
        vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Favourites_poster.png').getPath()
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay' : 4 })
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)

        # --- Create context menu ---
        commands = []
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY')))
        commands.append(('Add New Launcher', self._misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
        commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
            listitem.addContextMenuItems(commands, replaceItems = True)

        # --- Add row ---
        url_str = self._misc_url('SHOW_FAVOURITES')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    def _gui_render_category_collections_row(self):
        vcategory_name   = '[COLOR lightblue]ROM Collections[/COLOR]'
        vcategory_plot   = 'Browse the user defined ROM Collections'
        vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/ROM_Collections_icon.png').getPath()
        vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
        vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/ROM_Collections_poster.png').getPath()
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay' : 4 })
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_CATEGORY)

        commands = []
        commands.append(('Create New Collection', self._misc_url_RunPlugin('ADD_COLLECTION')))
        commands.append(('Import Collection', self._misc_url_RunPlugin('IMPORT_COLLECTION')))
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY')))
        commands.append(('Add New Launcher', self._misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
        commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
            listitem.addContextMenuItems(commands, replaceItems = True)

        url_str = self._misc_url('SHOW_COLLECTIONS')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    def _gui_render_virtual_category_root_row(self):
        vcategory_name   = '[COLOR violet]Browse by ...[/COLOR]'
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
        update_vcat_all_URL = self._misc_url_RunPlugin('UPDATE_ALL_VCATEGORIES')
        commands.append(('Update all databases'.format(vcategory_label), update_vcat_all_URL))
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY')))
        commands.append(('Add New Launcher', self._misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
        commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
            listitem.addContextMenuItems(commands, replaceItems = True)

        url_str = self._misc_url('SHOW_VCATEGORIES_ROOT')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    def _gui_render_category_AEL_offline_scraper_row(self):
        vcategory_name   = '[COLOR violet]Browse AEL Offline Scraper[/COLOR]'
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
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY')))
        commands.append(('Add New Launcher', self._misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
        commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
            listitem.addContextMenuItems(commands, replaceItems = True)

        url_str = self._misc_url('SHOW_AEL_OFFLINE_LAUNCHERS_ROOT')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    def _gui_render_category_LB_offline_scraper_row(self):
        vcategory_name   = '[COLOR violet]Browse LaunchBox Offline Scraper[/COLOR]'
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
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY')))
        commands.append(('Add New Launcher', self._misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
        commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
            listitem.addContextMenuItems(commands, replaceItems = True)

        url_str = self._misc_url('SHOW_LB_OFFLINE_LAUNCHERS_ROOT')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    def _gui_render_category_recently_played_row(self):
        vcategory_name   = '[COLOR thistle]Recently played ROMs[/COLOR]'
        vcategory_plot   = 'Browse the ROMs you played recently'
        vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Recently_played_icon.png').getPath()
        vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
        vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Recently_played_poster.png').getPath()
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)

        commands = []
        commands.append(('Manage Recently Played', self._misc_url_RunPlugin('MANAGE_RECENT_PLAYED')))
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY')))
        commands.append(('Add New Launcher', self._misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
        commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
            listitem.addContextMenuItems(commands, replaceItems = True)

        url_str = self._misc_url('SHOW_RECENTLY_PLAYED')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    def _gui_render_category_most_played_row(self):
        vcategory_name   = '[COLOR thistle]Most played ROMs[/COLOR]'
        vcategory_plot   = 'Browse the ROMs you play most'
        vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Most_played_icon.png').getPath()
        vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
        vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Most_played_poster.png').getPath()
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)

        commands = []
        commands.append(('Manage Most Played', self._misc_url_RunPlugin('MANAGE_MOST_PLAYED')))
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY')))
        commands.append(('Add New Launcher', self._misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
        commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
            listitem.addContextMenuItems(commands, replaceItems = True)

        url_str = self._misc_url('SHOW_MOST_PLAYED')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    def _gui_render_Utilities_root(self):
        vcategory_name   = '[COLOR sandybrown]Utilities[/COLOR]'
        vcategory_plot   = 'A set of useful [COLOR orange]Utilities[/COLOR].'
        vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Utilities_icon.png').getPath()
        vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
        vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Utilities_poster.png').getPath()

        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_CATEGORY)

        commands = []
        commands.append(('Open Kodi file manager', 'ActivateWindow(filemanager)'))
        commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
            listitem.addContextMenuItems(commands)

        url_str = self._misc_url('SHOW_UTILITIES_VLAUNCHERS')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    def _gui_render_GlobalReports_root(self):
        vcategory_name   = '[COLOR salmon]Global Reports[/COLOR]'
        vcategory_plot   = 'Generate and view [COLOR orange]Global Reports[/COLOR].'
        vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Global_Reports_icon.png').getPath()
        vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
        vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Global_Reports_poster.png').getPath()

        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_CATEGORY)

        commands = []
        commands.append(('Open Kodi file manager', 'ActivateWindow(filemanager)'))
        commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
            listitem.addContextMenuItems(commands)

        url_str = self._misc_url('SHOW_GLOBALREPORTS_VLAUNCHERS')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    # ---------------------------------------------------------------------------------------------
    # Virtual categories [Browse by ...]
    # ---------------------------------------------------------------------------------------------
    def _gui_render_vcategories_root(self):
        self._misc_set_all_sorting_methods()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)
        self._misc_clear_AEL_Launcher_Content()
        self._gui_render_virtual_category_row(VCATEGORY_TITLE_ID)
        self._gui_render_virtual_category_row(VCATEGORY_YEARS_ID)
        self._gui_render_virtual_category_row(VCATEGORY_GENRE_ID)
        self._gui_render_virtual_category_row(VCATEGORY_DEVELOPER_ID)
        self._gui_render_virtual_category_row(VCATEGORY_NPLAYERS_ID)
        self._gui_render_virtual_category_row(VCATEGORY_ESRB_ID)
        self._gui_render_virtual_category_row(VCATEGORY_RATING_ID)
        self._gui_render_virtual_category_row(VCATEGORY_CATEGORY_ID)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    def _gui_render_virtual_category_row(self, virtual_category_kind):
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
        update_vcat_URL = self._misc_url_RunPlugin('UPDATE_VIRTUAL_CATEGORY', virtual_category_kind)
        update_vcat_all_URL = self._misc_url_RunPlugin('UPDATE_ALL_VCATEGORIES')
        commands.append(('Update {0} database'.format(vcategory_label), update_vcat_URL))
        commands.append(('Update all databases', update_vcat_all_URL))
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY')))
        commands.append(('Add New Launcher',    self._misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
        commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
            listitem.addContextMenuItems(commands, replaceItems = True)

        url_str = self._misc_url('SHOW_VIRTUAL_CATEGORY', virtual_category_kind)
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    def _gui_render_AEL_scraper_launchers(self):
        self._misc_set_default_sorting_method()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)
        self._misc_clear_AEL_Launcher_Content()

        # Open info dictionary and render platform rows.
        data_dir_FN = g_PATHS.ADDON_CODE_DIR.pjoin('data')
        gamedb_info_dic = fs_load_JSON_file(data_dir_FN, g_PATHS.GAMEDB_JSON_BASE_NOEXT)
        for pobj in AEL_platforms:
            if pobj.long_name == PLATFORM_UNKNOWN_LONG: continue
            self._gui_render_AEL_scraper_launchers_row(pobj, gamedb_info_dic)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    def _gui_render_AEL_scraper_launchers_row(self, pobj, gamedb_info_dic):
        if pobj.aliasof:
            pobj_parent = AEL_platforms[get_AEL_platform_index(pobj.aliasof)]
            plot_text = 'Browse ' + KC_ORANGE + pobj.long_name + KC_END + ' ROMs ' + \
                'in AEL Offline Scraper database. ' + \
                KC_ORANGE + pobj.long_name + KC_END + ' is an alias of ' + \
                KC_VIOLET + pobj_parent.long_name + KC_END + '.'
            # User ROMs of parent.
            num_ROMs = gamedb_info_dic[pobj_parent.long_name]['numROMs']
        else:
            plot_text = 'Browse ' + KC_ORANGE + pobj.long_name + KC_END + ' ROMs ' + \
                'in AEL Offline Scraper database. '
            num_ROMs = gamedb_info_dic[pobj.long_name]['numROMs']

        # Build ListItem object.
        title_str = pobj.long_name
        if num_ROMs > 0:
            title_str += ' [COLOR orange]({} ROMs)[/COLOR]'.format(num_ROMs)
        else:
            title_str += ' [COLOR red][Not available][/COLOR]'
        vlauncher_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_AEL_Offline_icon.png').getPath()
        vlauncher_fanart = g_PATHS.FANART_FILE_PATH.getPath()
        vlauncher_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_AEL_Offline_poster.png').getPath()

        listitem = xbmcgui.ListItem(title_str)
        listitem.setInfo('video', {'title' : title_str, 'plot' : plot_text, 'overlay' : 4 })
        listitem.setArt({'icon' : vlauncher_icon, 'fanart' : vlauncher_fanart, 'poster' : vlauncher_poster})
        # Set platform property to render platform icon on skins.
        listitem.setProperty('platform', pobj.long_name)
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)

        if self.g_kiosk_mode_disabled:
            commands = [
                ('Kodi File Manager', 'ActivateWindow(filemanager)'),
                ('AEL addon settings', 'Addon.OpenSettings({})'.format(__addon_id__)),
            ]
            listitem.addContextMenuItems(commands, replaceItems = True)

        # User the original platform here, otherwise the list goes to the parent
        # platform instead of the aliased platform when user goes back in the list.
        url_str = self._misc_url('SHOW_AEL_SCRAPER_ROMS', pobj.long_name)
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    def _gui_render_LB_scraper_launchers(self):
        self._misc_set_default_sorting_method()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)
        self._misc_clear_AEL_Launcher_Content()

        # >> Open info dictionary
        gamedb_info_dic = fs_load_JSON_file(g_PATHS.LAUNCHBOX_INFO_DIR, g_PATHS.LAUNCHBOX_JSON_BASE_NOEXT)

        # >> Loop the list of platforms and render a virtual launcher for each platform that
        # >> has a valid XML database.
        for platform in AEL_platform_list:
            # >> Do not show Unknown platform
            if platform == 'Unknown': continue
            db_suffix = platform_AEL_to_LB_XML[platform]
            self._gui_render_LB_scraper_launchers_row(platform, gamedb_info_dic[platform], db_suffix)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    def _gui_render_LB_scraper_launchers_row(self, platform, platform_info, db_suffix):
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
        if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
            listitem.addContextMenuItems(commands, replaceItems = True)

        url_str = self._misc_url('SHOW_LB_SCRAPER_ROMS', platform)
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    def _gui_render_Utilities_vlaunchers(self):
        # --- Common context menu for all VLaunchers ---
        commands = [
            ('Kodi File Manager', 'ActivateWindow(filemanager)'),
            ('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)),
        ]

        # --- Common artwork for all Utilities VLaunchers ---
        vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Utilities_icon.png').getPath()
        vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
        vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Utilities_poster.png').getPath()

        # <setting label="Import category/launcher configuration ..."
        #  action="RunPlugin(plugin://plugin.program.advanced.emulator.launcher/?com=IMPORT_LAUNCHERS)"/>
        vcategory_name = 'Import category/launcher XML configuration file'
        vcategory_plot = (
            'Imports XML files having AEL categories and/or launcher configuration.')
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
        if xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)"):
            listitem.addContextMenuItems(commands)
        url_str = self._misc_url('EXECUTE_UTILS_IMPORT_LAUNCHERS')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

        # <setting label="Export category/launcher configuration ..."
        #  action="RunPlugin(plugin://plugin.program.advanced.emulator.launcher/?com=EXPORT_LAUNCHERS)"/>
        vcategory_name = 'Export category/launcher XML configuration file'
        vcategory_plot = (
            'Exports all AEL categories and launchers into an XML configuration file. '
            'You can later reimport this XML file.')
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
        if xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)"):
            listitem.addContextMenuItems(commands)
        url_str = self._misc_url('EXECUTE_UTILS_EXPORT_LAUNCHERS')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

        # <setting label="Check/Update all databases ..."
        #  action="RunPlugin(plugin://plugin.program.advanced.emulator.launcher/?com=CHECK_DATABASE)"/>
        vcategory_name = 'Check/Update all databases'
        vcategory_plot = ('Checks and updates all AEL databases. Always use this tool '
            'after upgrading AEL from a previous version if the plugins crashes.')
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
        if xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)"):
            listitem.addContextMenuItems(commands)
        url_str = self._misc_url('EXECUTE_UTILS_CHECK_DATABASE')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

        # <setting label="Check Launchers ..."
        #  action="RunPlugin(plugin://plugin.program.advanced.emulator.launcher/?com=CHECK_LAUNCHERS)"/>
        vcategory_name = 'Check Launchers'
        vcategory_plot = ('Check all Launchers for missing executables, missing artwork, '
            'wrong platform names, ROM path existence, etc.')
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
        if xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)"):
            listitem.addContextMenuItems(commands)
        url_str = self._misc_url('EXECUTE_UTILS_CHECK_LAUNCHERS')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

        vcategory_name = 'Check Launcher ROMs sync status'
        vcategory_plot = ('For all ROM Launchers, check if all the ROMs in the ROM path are in AEL '
            'database. If any Launcher is out of sync because you were changing your ROM files, use '
            'the [COLOR=orange]ROM Scanner[/COLOR] to add and scrape the missing ROMs and remove '
            'any dead ROMs.')
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
        if xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)"):
            listitem.addContextMenuItems(commands)
        url_str = self._misc_url('EXECUTE_UTILS_CHECK_LAUNCHER_SYNC_STATUS')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

        # vcategory_name = 'Check artwork image integrity'
        # vcategory_plot = ('Scans existing [COLOR=orange]artwork images[/COLOR] in Launchers, Favourites '
        #     'and ROM Collections and verifies that the images have correct extension '
        #     'and size is greater than 0. You can delete corrupted images to be rescraped later.')
        # listitem = xbmcgui.ListItem(vcategory_name)
        # listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        # listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        # listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
        # if xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)"):
        #     listitem.addContextMenuItems(commands)
        # url_str = self._misc_url('EXECUTE_UTILS_CHECK_ARTWORK_INTEGRITY')
        # xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

        vcategory_name = 'Check ROMs artwork image integrity'
        vcategory_plot = ('Scans existing [COLOR=orange]ROMs artwork images[/COLOR] in ROM Launchers '
            'and verifies that the images have correct extension '
            'and size is greater than 0. You can delete corrupted images to be rescraped later.')
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
        if xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)"):
            listitem.addContextMenuItems(commands)
        url_str = self._misc_url('EXECUTE_UTILS_CHECK_ROM_ARTWORK_INTEGRITY')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

        # vcategory_name = 'Delete redundant artwork'
        # vcategory_plot = ('Scans all Launchers, Favourites and Collections and finds redundant '
        #     'or unused artwork. You may delete this unneeded images.')
        # listitem = xbmcgui.ListItem(vcategory_name)
        # listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        # listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        # listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
        # if xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)"):
        #     listitem.addContextMenuItems(commands)
        # url_str = self._misc_url('EXECUTE_UTILS_DELETE_REDUNDANT_ARTWORK')
        # xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

        vcategory_name = 'Delete ROMs redundant artwork'
        vcategory_plot = ('Scans all ROM Launchers and finds '
            '[COLOR orange]redundant ROMs artwork[/COLOR]. You may delete this unneeded images.')
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
        if xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)"):
            listitem.addContextMenuItems(commands)
        url_str = self._misc_url('EXECUTE_UTILS_DELETE_ROM_REDUNDANT_ARTWORK')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

        vcategory_name = 'Show detected No-Intro/Redump DATs'
        vcategory_plot = ('Display the auto-detected No-Intro/Redump DATs that will be used for the '
            'ROM audit. You have to configure the DAT directories in '
            '[COLOR orange]AEL addon settings[/COLOR], [COLOR=orange]ROM Audit[/COLOR] tab.')
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
        if xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)"):
            listitem.addContextMenuItems(commands)
        url_str = self._misc_url('EXECUTE_UTILS_SHOW_DETECTED_DATS')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

        vcategory_name = 'Check Retroarch launchers'
        vcategory_plot = ('Check [COLOR orange]Retroarch ROM launchers[/COLOR] for missing '
            'Libretro cores set with [COLOR=orange]argument -L[/COLOR]. '
            'This only works in Linux and Windows platforms.')
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
        if xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)"):
            listitem.addContextMenuItems(commands)
        url_str = self._misc_url('EXECUTE_UTILS_CHECK_RETRO_LAUNCHERS')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

        # <setting label="Check Retroarch BIOSes ..."
        #  action="RunPlugin(plugin://plugin.program.advanced.emulator.launcher/?com=CHECK_RETRO_BIOS)"/>
        vcategory_name = 'Check Retroarch BIOSes'
        vcategory_plot = ('Check [COLOR orange]Retroarch BIOSes[/COLOR]. You need to configure the '
            'Libretro system directory in [COLOR orange]AEL addon settings[/COLOR], '
            '[COLOR orange]Misc settings[/COLOR] tab. The setting '
            '[COLOR orange]Only check mandatory BIOSes[/COLOR] affects this report.')
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
        if xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)"):
            listitem.addContextMenuItems(commands)
        url_str = self._misc_url('EXECUTE_UTILS_CHECK_RETRO_BIOS')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

        # Importing AL configuration is not supported any more. It will cause a lot of trouble
        # because AL and AEL have diverged too much.
        # <setting label="Import AL launchers.xml ..."
        #  action="RunPlugin(plugin://plugin.program.advanced.emulator.launcher/?com=IMPORT_AL_LAUNCHERS)"/>

        # --- Check TheGamesDB scraper ---
        vcategory_name = 'Check TheGamesDB scraper'
        vcategory_plot = ('Connect to TheGamesDB and check if it is working and your monthly allowance.')
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
        if xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)"):
            listitem.addContextMenuItems(commands)
        url_str = self._misc_url('EXECUTE_UTILS_TGDB_CHECK')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

        # --- Check MobyGames scraper ---
        vcategory_name = 'Check MobyGames scraper'
        vcategory_plot = ('Connect to MobyGames and check if it works.')
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
        if xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)"):
            listitem.addContextMenuItems(commands)
        url_str = self._misc_url('EXECUTE_UTILS_MOBYGAMES_CHECK')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

        # --- Check ScreenScraper scraper ---
        vcategory_name = 'Check ScreenScraper scraper'
        vcategory_plot = ('Connect to ScreenScraper and check if it works.')
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
        if xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)"):
            listitem.addContextMenuItems(commands)
        url_str = self._misc_url('EXECUTE_UTILS_SCREENSCRAPER_CHECK')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

        # --- Check ArcadeDB scraper ---
        vcategory_name = 'Check Arcade DB scraper'
        vcategory_plot = ('Connect to Arcade DB and check if it works.')
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
        if xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)"):
            listitem.addContextMenuItems(commands)
        url_str = self._misc_url('EXECUTE_UTILS_ARCADEDB_CHECK')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

        # --- End of directory ---
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    def _gui_render_GlobalReports_vlaunchers(self):
        # --- Common context menu for all VLaunchers ---
        commands = []
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
        commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))

        # --- Common artwork for all VLaunchers ---
        vcategory_icon   = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Global_Reports_icon.png').getPath()
        vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
        vcategory_poster = g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Global_Reports_poster.png').getPath()

        # --- Global ROM statistics ---
        vcategory_name   = 'Global ROM statistics'
        vcategory_plot   = ('Shows a report of all ROM Launchers with number of ROMs.')
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
        if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
            listitem.addContextMenuItems(commands)
        url_str = self._misc_url('EXECUTE_GLOBAL_ROM_STATS')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

        # --- Global ROM Audit statistics ---
        vcategory_name   = 'Global ROM Audit statistics (All)'
        vcategory_plot   = (
            'Shows a report of all audited ROM Launchers, with Have, Miss and Unknown '
            'statistics.')
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
        if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
            listitem.addContextMenuItems(commands)
        url_str = self._misc_url('EXECUTE_GLOBAL_AUDIT_STATS_ALL')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

        vcategory_name   = 'Global ROM Audit statistics (No-Intro only)'
        vcategory_plot   = (
            'Shows a report of all audited ROM Launchers, with Have, Miss and Unknown '
            'statistics. Only No-Intro platforms (cartridge-based) are reported.')
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
        if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
            listitem.addContextMenuItems(commands)
        url_str = self._misc_url('EXECUTE_GLOBAL_AUDIT_STATS_NOINTRO')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

        vcategory_name   = 'Global ROM Audit statistics (Redump only)'
        vcategory_plot   = (
            'Shows a report of all audited ROM Launchers, with Have, Miss and Unknown '
            'statistics. Only Redump platforms (optical-based) are reported.')
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
        listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster})
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM_LAUNCHER)
        if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
            listitem.addContextMenuItems(commands)
        url_str = self._misc_url('EXECUTE_GLOBAL_AUDIT_STATS_REDUMP')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

        # --- End of directory ---
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    # ---------------------------------------------------------------------------------------------
    # Launcher LisItem rendering
    # ---------------------------------------------------------------------------------------------
    #
    # Renders the launchers for a given category
    #
    def _command_render_launchers(self, categoryID):
        # >> Set content type
        self._misc_set_all_sorting_methods()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)
        self._misc_clear_AEL_Launcher_Content()

        # --- If the category has no launchers then render nothing ---
        launcher_IDs = []
        for launcher_id in self.launchers:
            if self.launchers[launcher_id]['categoryID'] == categoryID: launcher_IDs.append(launcher_id)
        if not launcher_IDs:
            category_name = self.categories[categoryID]['m_name']
            kodi_notify('Category {0} has no launchers. Add launchers first.'.format(category_name))
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
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # >> Render launcher rows of this launcher
        for key in sorted(self.launchers, key = lambda x : self.launchers[x]['m_name']):
            if self.launchers[key]['categoryID'] == categoryID:
                self._gui_render_launcher_row(self.launchers[key])
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Renders all launchers belonging to all categories.
    # This function is called by skins to create shortcuts.
    #
    def _command_render_all_launchers(self):
        # >> If no launchers render nothing
        if not self.launchers:
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # >> Render all launchers
        for key in sorted(self.launchers, key = lambda x : self.launchers[x]['m_name']):
            self._gui_render_launcher_row(self.launchers[key])
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    def _gui_render_launcher_row(self, launcher_dic, launcher_raw_name = None):
        # --- Do not render row if launcher finished ---
        if launcher_dic['finished'] and self.settings['display_hide_finished']:
            return

        # --- Launcher tags ---
        # >> Do not plot ROM count on standalone launchers! Launcher is standalone if rompath = ''
        if launcher_raw_name is None: launcher_raw_name = launcher_dic['m_name']
        if self.settings['display_launcher_roms']:
            if launcher_dic['rompath']:
                # Audited ROM launcher.
                if launcher_dic['audit_state'] == AUDIT_STATE_ON:
                    if launcher_dic['launcher_display_mode'] == LAUNCHER_DMODE_FLAT:
                        num_have    = launcher_dic['num_have']
                        num_miss    = launcher_dic['num_miss']
                        num_unknown = launcher_dic['num_unknown']
                        launcher_name = '{} [COLOR orange]({} Have / {} Miss / {} Unk)[/COLOR]'.format(
                            launcher_raw_name, num_have, num_miss, num_unknown)
                    elif launcher_dic['launcher_display_mode'] == LAUNCHER_DMODE_PCLONE:
                        num_parents = launcher_dic['num_parents']
                        num_clones  = launcher_dic['num_clones']
                        launcher_name = '{} [COLOR orange]({} Parents / {} Clones)[/COLOR]'.format(
                            launcher_raw_name, num_parents, num_clones)
                    else:
                        launcher_name = '{} [COLOR red](ERROR)[/COLOR]'.format(launcher_raw_name)
                # Non-audited ROM launcher.
                else:
                    num_roms = launcher_dic['num_roms']
                    if num_roms == 0:
                        launcher_name = '{} [COLOR orange](No ROMs)[/COLOR]'.format(launcher_raw_name)
                    elif num_roms == 1:
                        launcher_name = '{} [COLOR orange]({} ROM)[/COLOR]'.format(launcher_raw_name, num_roms)
                    else:
                        launcher_name = '{} [COLOR orange]({} ROMs)[/COLOR]'.format(launcher_raw_name, num_roms)
            else:
                launcher_name = '{} [COLOR chocolate](Std)[/COLOR]'.format(launcher_raw_name)
        else:
            launcher_name = launcher_raw_name

        # --- Create listitem row ---
        ICON_OVERLAY = 5 if launcher_dic['finished'] else 4
        listitem = xbmcgui.ListItem(launcher_name)
        # >> BUG in Jarvis/Krypton skins. If 'year' is set to empty string a 0 is displayed on the
        # >>     skin. If year is not set then the correct icon is shown.
        if launcher_dic['m_year']:
            listitem.setInfo('video', {
                'title'   : launcher_name,             'year'    : launcher_dic['m_year'],
                'genre'   : launcher_dic['m_genre'],   'studio'  : launcher_dic['m_developer'],
                'rating'  : launcher_dic['m_rating'],  'plot'    : launcher_dic['m_plot'],
                'trailer' : launcher_dic['s_trailer'], 'overlay' : ICON_OVERLAY })
        else:
            listitem.setInfo('video', {
                'title'   : launcher_name,
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
        commands.append(('View Launcher', self._misc_url_RunPlugin('VIEW', categoryID, launcherID)))
        commands.append(('Edit Launcher', self._misc_url_RunPlugin('EDIT_LAUNCHER', categoryID, launcherID)))
        # >> ONLY for ROM launchers
        if launcher_dic['rompath']:
            commands.append(('Scan ROMs', self._misc_url_RunPlugin('SCAN_ROMS', categoryID, launcherID)))
        commands.append(('Search ROMs in Launcher', self._misc_url_RunPlugin('SEARCH_LAUNCHER', categoryID, launcherID)))
        commands.append(('Add New Launcher', self._misc_url_RunPlugin('ADD_LAUNCHER', categoryID)))
        # >> Launchers in addon root should be able to create a new category
        if categoryID == VCATEGORY_ADDONROOT_ID:
                commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY')))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
        commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
            listitem.addContextMenuItems(commands, replaceItems = True)

        # --- Add Launcher row to ListItem ---
        if launcher_dic['rompath']:
            url_str = self._misc_url('SHOW_ROMS', categoryID, launcherID)
            folder_flag = True
        else:
            url_str = self._misc_url('LAUNCH_STANDALONE', categoryID, launcherID)
            folder_flag = False
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = folder_flag)

    # ---------------------------------------------------------------------------------------------
    # ROM LisItem rendering
    # ---------------------------------------------------------------------------------------------
    #
    # Render clone ROMs. romID is the parent ROM.
    # This is only called in Parent/Clone display modes.
    #
    def _command_render_clone_roms(self, categoryID, launcherID, romID):
        # --- Set content type and sorting methods ---
        self._misc_set_all_sorting_methods()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)
        self._misc_clear_AEL_Launcher_Content()

        # --- Check for errors ---
        if launcherID not in self.launchers:
            log_error('_command_render_clone_roms() Launcher ID not found in self.launchers')
            kodi_dialog_OK('_command_render_clone_roms(): Launcher ID not found in self.launchers. Report this bug.')
            return
        selectedLauncher = self.launchers[launcherID]
        view_mode = selectedLauncher['launcher_display_mode']

        # --- Load ROMs for this launcher ---
        roms_json_FN = g_PATHS.ROMS_DIR.pjoin(selectedLauncher['roms_base_noext'] + '.json')
        if not roms_json_FN.exists():
            kodi_notify('Launcher JSON database not found. Add ROMs to launcher.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return
        all_roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, selectedLauncher)
        if not all_roms:
            kodi_notify('Launcher JSON database empty. Add ROMs to launcher.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # --- Load parent/clone index ---
        index_base_noext = selectedLauncher['roms_base_noext'] + '_index_PClone'
        index_json_FN = g_PATHS.ROMS_DIR.pjoin(index_base_noext + '.json')
        if not index_json_FN.exists():
            kodi_notify('Parent list JSON database not found.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return
        pclone_index = fs_load_JSON_file(g_PATHS.ROMS_DIR, index_base_noext)
        if not pclone_index:
            kodi_notify('Parent list JSON database is empty.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # --- Build parent and clones dictionary of ROMs ---
        roms = {}
        # >> Add parent ROM except if the parent if the fake paren ROM
        if romID != UNKNOWN_ROMS_PARENT_ID: roms[romID] = all_roms[romID]
        # >> Add clones, if any
        for rom_id in pclone_index[romID]: roms[rom_id] = all_roms[rom_id]
        log_verb('_command_render_clone_roms() Parent ID {0}'.format(romID))
        log_verb('_command_render_clone_roms() Number of clone ROMs = {0}'.format(len(roms)))
        # for key in roms:
        #     log_debug('key   = {0}'.format(key))
        #     log_debug('value = {0}'.format(roms[key]))

        # --- ROM display filter ---
        dp_mode = selectedLauncher['audit_display_mode']
        if selectedLauncher['audit_state'] == AUDIT_STATE_ON and dp_mode != AUDIT_DMODE_ALL:
            filtered_roms = {}
            for rom_id in roms:
                rom = roms[rom_id]
                if rom['nointro_status'] == AUDIT_STATUS_HAVE:
                    if dp_mode == AUDIT_DMODE_HAVE or \
                       dp_mode == AUDIT_DMODE_HAVE_UNK or \
                       dp_mode == AUDIT_DMODE_HAVE_MISS:
                        filtered_roms[rom_id] = rom
                elif rom['nointro_status'] == AUDIT_STATUS_MISS:
                    if dp_mode == AUDIT_DMODE_HAVE_MISS or \
                       dp_mode == AUDIT_DMODE_MISS or \
                       dp_mode == AUDIT_DMODE_MISS_UNK:
                        filtered_roms[rom_id] = rom
                elif rom['nointro_status'] == AUDIT_STATUS_UNKNOWN:
                    if dp_mode == AUDIT_DMODE_HAVE_UNK or \
                       dp_mode == AUDIT_DMODE_MISS_UNK or \
                       dp_mode == AUDIT_DMODE_UNK:
                        filtered_roms[rom_id] = rom
                else:
                    # Always copy roms with unknown status (NOINTRO_STATUS_NONE)
                    filtered_roms[rom_id] = rom
            roms = filtered_roms
            if not roms:
                kodi_notify('No ROMs to show with current filtering settings.')
                xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
                return

        # --- Render ROMs ---
        roms_fav = fs_load_Favourites_JSON(g_PATHS.FAV_JSON_FILE_PATH)
        roms_fav_set = set(roms_fav.keys())
        for key in sorted(roms, key = lambda x : roms[x]['m_name']):
            self._gui_render_rom_row(categoryID, launcherID, roms[key], key in roms_fav_set, view_mode, False)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Renders the ROMs listbox for a given standard launcher or the Parent ROMs of a PClone launcher.
    #
    def _command_render_roms(self, categoryID, launcherID):
        # --- Check for errors ---
        if launcherID not in self.launchers:
            log_error('_command_render_roms() Launcher ID not found in self.launchers')
            kodi_dialog_OK('_command_render_roms(): Launcher ID not found in self.launchers. Report this bug.')
            return
        selectedLauncher = self.launchers[launcherID]
        view_mode = selectedLauncher['launcher_display_mode']

        # --- Set content type and sorting methods ---
        self._misc_set_all_sorting_methods()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)
        self._misc_set_AEL_Launcher_Content(selectedLauncher)

        # --- Render in Flat mode (all ROMs) or Parent/Clone mode---
        loading_ticks_start = time.time()
        if view_mode == LAUNCHER_DMODE_FLAT:
            # --- Load ROMs for this launcher ---
            roms_json_FN = g_PATHS.ROMS_DIR.pjoin(selectedLauncher['roms_base_noext'] + '.json')
            if not roms_json_FN.exists():
                kodi_notify('Launcher JSON database not found. Add ROMs to launcher.')
                xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
                return
            roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, selectedLauncher)
            if not roms:
                kodi_notify('Launcher JSON database empty. Add ROMs to launcher.')
                xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
                return
        else:
            # --- Load parent ROMs ---
            parent_roms_base_noext = selectedLauncher['roms_base_noext'] + '_parents'
            parents_FN = g_PATHS.ROMS_DIR.pjoin(parent_roms_base_noext + '.json')
            if not parents_FN.exists():
                kodi_notify('Parent ROMs JSON not found.')
                xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
                return
            roms = fs_load_JSON_file(g_PATHS.ROMS_DIR, parent_roms_base_noext)
            if not roms:
                kodi_notify('Parent ROMs JSON is empty.')
                xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
                return

            # --- Load parent/clone index ---
            index_base_noext = selectedLauncher['roms_base_noext'] + '_index_PClone'
            index_FN = g_PATHS.ROMS_DIR.pjoin(index_base_noext + '.json')
            if not index_FN.exists():
                kodi_notify('PClone index JSON not found.')
                xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
                return
            pclone_index = fs_load_JSON_file(g_PATHS.ROMS_DIR, index_base_noext)
            if not pclone_index:
                kodi_notify('PClone index dict is empty.')
                xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
                return

        # --- ROM display filter ---
        dp_mode = selectedLauncher['audit_display_mode']
        if selectedLauncher['audit_state'] == AUDIT_STATE_ON and dp_mode != AUDIT_DMODE_ALL:
            filtered_roms = {}
            for rom_id in roms:
                rom = roms[rom_id]
                # >> Always include a parent ROM regardless of filters in 'Parent/Clone mode'
                # >> launcher_display_mode if it has 1 or more clones.
                if not selectedLauncher['launcher_display_mode'] == LAUNCHER_DMODE_FLAT and len(pclone_index[rom_id]):
                    filtered_roms[rom_id] = rom
                    continue
                # >> Filter ROM
                if rom['nointro_status'] == AUDIT_STATUS_HAVE:
                    if dp_mode == AUDIT_DMODE_HAVE or \
                       dp_mode == AUDIT_DMODE_HAVE_UNK or \
                       dp_mode == AUDIT_DMODE_HAVE_MISS:
                        filtered_roms[rom_id] = rom
                elif rom['nointro_status'] == AUDIT_STATUS_MISS:
                    if dp_mode == AUDIT_DMODE_HAVE_MISS or \
                       dp_mode == AUDIT_DMODE_MISS or \
                       dp_mode == AUDIT_DMODE_MISS_UNK:
                        filtered_roms[rom_id] = rom
                elif rom['nointro_status'] == AUDIT_STATUS_UNKNOWN:
                    if dp_mode == AUDIT_DMODE_HAVE_UNK or \
                       dp_mode == AUDIT_DMODE_MISS_UNK or \
                       dp_mode == AUDIT_DMODE_UNK:
                        filtered_roms[rom_id] = rom
                # >> Always copy roms with unknown status (NOINTRO_STATUS_NONE)
                else:
                    filtered_roms[rom_id] = rom
            roms = filtered_roms
            if not roms:
                kodi_notify('No ROMs to show with current filtering settings.')
                xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
                return

        # --- Load favourites ---
        # >> Optimisation: Transform the dictionary keys into a set. Sets are the fastest
        #    when checking if an element exists.
        roms_fav = fs_load_Favourites_JSON(g_PATHS.FAV_JSON_FILE_PATH)
        roms_fav_set = set(roms_fav.keys())

        # --- Display ROMs ---
        loading_ticks_end = time.time()
        rendering_ticks_start = time.time()
        if view_mode == LAUNCHER_DMODE_FLAT:
            for key in sorted(roms, key = lambda x : roms[x]['m_name']):
                self._gui_render_rom_row(categoryID, launcherID, roms[key], key in roms_fav_set, view_mode, False)
        else:
            for key in sorted(roms, key = lambda x : roms[x]['m_name']):
                num_clones = len(pclone_index[key])
                self._gui_render_rom_row(categoryID, launcherID, roms[key], key in roms_fav_set, view_mode, True, num_clones)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
        rendering_ticks_end = time.time()

        # --- DEBUG Data loading/rendering statistics ---
        log_debug('Loading seconds   {0}'.format(loading_ticks_end - loading_ticks_start))
        log_debug('Rendering seconds {0}'.format(rendering_ticks_end - rendering_ticks_start))

    #
    # Former _add_rom()
    # Note that if we are rendering favourites, categoryID = VCATEGORY_FAVOURITES_ID
    # Note that if we are rendering virtual launchers, categoryID = VCATEGORY_*_ID
    #
    def _gui_render_rom_row(self, categoryID, launcherID, rom,
                            rom_in_fav = False, view_mode = LAUNCHER_DMODE_FLAT,
                            is_parent_launcher = False, num_clones = 0):
        # --- Do not render row if ROM is finished ---
        if rom['finished'] and self.settings['display_hide_finished']: return

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
            if self.settings['display_fav_status']:
                if   rom['fav_status'] == 'OK':                rom_name = '{} [COLOR green][OK][/COLOR]'.format(rom_raw_name)
                elif rom['fav_status'] == 'Unlinked ROM':      rom_name = '{} [COLOR yellow][Unlinked ROM][/COLOR]'.format(rom_raw_name)
                elif rom['fav_status'] == 'Unlinked Launcher': rom_name = '{} [COLOR yellow][Unlinked Launcher][/COLOR]'.format(rom_raw_name)
                elif rom['fav_status'] == 'Broken':            rom_name = '{} [COLOR red][Broken][/COLOR]'.format(rom_raw_name)
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
            if self.settings['display_fav_status']:
                if   rom['fav_status'] == 'OK':                rom_name = '{} [COLOR green][OK][/COLOR]'.format(rom_raw_name)
                elif rom['fav_status'] == 'Unlinked ROM':      rom_name = '{} [COLOR yellow][Unlinked ROM][/COLOR]'.format(rom_raw_name)
                elif rom['fav_status'] == 'Unlinked Launcher': rom_name = '{} [COLOR yellow][Unlinked Launcher][/COLOR]'.format(rom_raw_name)
                elif rom['fav_status'] == 'Broken':            rom_name = '{} [COLOR red][Broken][/COLOR]'.format(rom_raw_name)
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
            platform       = rom['platform']
            rom_name = rom_raw_name
        elif categoryID == VCATEGORY_MOST_PLAYED_ID:
            icon_path      = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_icon', 'DefaultProgram.png')
            fanart_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_fanart')
            banner_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_banner')
            poster_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_poster')
            clearlogo_path = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_clearlogo')
            platform       = rom['platform']
            # >> Render number of number the ROM has been launched
            if rom['launch_count'] == 1:
                rom_name = '{} [COLOR orange][{} time][/COLOR]'.format(rom_raw_name, rom['launch_count'])
            else:
                rom_name = '{} [COLOR orange][{} times][/COLOR]'.format(rom_raw_name, rom['launch_count'])
        elif categoryID == VCATEGORY_TITLE_ID    or categoryID == VCATEGORY_YEARS_ID or \
             categoryID == VCATEGORY_GENRE_ID    or categoryID == VCATEGORY_DEVELOPER_ID or \
             categoryID == VCATEGORY_NPLAYERS_ID or categoryID == VCATEGORY_ESRB_ID or \
             categoryID == VCATEGORY_RATING_ID   or categoryID == VCATEGORY_CATEGORY_ID:
            icon_path      = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_icon', 'DefaultProgram.png')
            fanart_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_fanart')
            banner_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_banner')
            poster_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_poster')
            clearlogo_path = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_clearlogo')
            platform       = rom['platform']

            # --- NoIntro status flag ---
            nstat = rom['nointro_status']
            if self.settings['display_nointro_stat']:
                if   nstat == AUDIT_STATUS_HAVE:    rom_name = '{} [COLOR green][Have][/COLOR]'.format(rom_raw_name)
                elif nstat == AUDIT_STATUS_MISS:    rom_name = '{} [COLOR magenta][Miss][/COLOR]'.format(rom_raw_name)
                elif nstat == AUDIT_STATUS_UNKNOWN: rom_name = '{} [COLOR yellow][Unknown][/COLOR]'.format(rom_raw_name)
                elif nstat == AUDIT_STATUS_EXTRA:   rom_name = '{} [COLOR limegreen][Extra][/COLOR]'.format(rom_raw_name)
                elif nstat == AUDIT_STATUS_NONE:    rom_name = rom_raw_name
                else:                               rom_name = '{} [COLOR red][Status error][/COLOR]'.format(rom_raw_name)
            else:
                rom_name = rom_raw_name
            if   nstat == AUDIT_STATUS_HAVE:    AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_HAVE
            elif nstat == AUDIT_STATUS_MISS:    AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_MISS
            elif nstat == AUDIT_STATUS_UNKNOWN: AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_UNKNOWN
            elif nstat == AUDIT_STATUS_EXTRA:   AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_EXTRA
            elif nstat == AUDIT_STATUS_NONE:    AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_NONE

            # --- In Favourites ROM flag ---
            if self.settings['display_rom_in_fav'] and rom_in_fav: rom_name += ' [COLOR violet][Fav][/COLOR]'
            if rom_in_fav: AEL_InFav_bool_value = AEL_INFAV_BOOL_VALUE_TRUE
        # --- Standard launcher ---
        else:
            # >> If ROM has no fanart then use launcher fanart
            launcher = self.launchers[launcherID]
            kodi_def_icon = launcher['s_icon'] if launcher['s_icon'] else 'DefaultProgram.png'
            icon_path      = asset_get_default_asset_Launcher_ROM(rom, launcher, 'roms_default_icon', kodi_def_icon)
            fanart_path    = asset_get_default_asset_Launcher_ROM(rom, launcher, 'roms_default_fanart', launcher['s_fanart'])
            banner_path    = asset_get_default_asset_Launcher_ROM(rom, launcher, 'roms_default_banner')
            poster_path    = asset_get_default_asset_Launcher_ROM(rom, launcher, 'roms_default_poster')
            clearlogo_path = asset_get_default_asset_Launcher_ROM(rom, launcher, 'roms_default_clearlogo')
            platform = launcher['platform']

            # --- parent_launcher is True when rendering Parent ROMs in Parent/Clone view mode ---
            nstat = rom['nointro_status']
            if self.settings['display_nointro_stat']:
                if   nstat == AUDIT_STATUS_HAVE:    rom_name = '{} [COLOR green][Have][/COLOR]'.format(rom_raw_name)
                elif nstat == AUDIT_STATUS_MISS:    rom_name = '{} [COLOR magenta][Miss][/COLOR]'.format(rom_raw_name)
                elif nstat == AUDIT_STATUS_UNKNOWN: rom_name = '{} [COLOR yellow][Unknown][/COLOR]'.format(rom_raw_name)
                elif nstat == AUDIT_STATUS_EXTRA:   rom_name = '{} [COLOR limegreen][Extra][/COLOR]'.format(rom_raw_name)
                elif nstat == AUDIT_STATUS_NONE:    rom_name = rom_raw_name
                else:                               rom_name = '{} [COLOR red][Status error][/COLOR]'.format(rom_raw_name)
            else:
                rom_name = rom_raw_name
            if is_parent_launcher and num_clones > 0:
                rom_name += ' [COLOR orange][{0} clones][/COLOR]'.format(num_clones)
            if   nstat == AUDIT_STATUS_HAVE:    AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_HAVE
            elif nstat == AUDIT_STATUS_MISS:    AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_MISS
            elif nstat == AUDIT_STATUS_UNKNOWN: AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_UNKNOWN
            elif nstat == AUDIT_STATUS_EXTRA:   AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_EXTRA
            elif nstat == AUDIT_STATUS_NONE:    AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_NONE
            # --- Mark clone ROMs ---
            pclone_status = rom['pclone_status']
            if pclone_status == PCLONE_STATUS_CLONE: rom_name += ' [COLOR orange][Clo][/COLOR]'
            if   pclone_status == PCLONE_STATUS_PARENT: AEL_PClone_stat_value = AEL_PCLONE_STAT_VALUE_PARENT
            elif pclone_status == PCLONE_STATUS_CLONE:  AEL_PClone_stat_value = AEL_PCLONE_STAT_VALUE_CLONE
            # --- In Favourites ROM flag ---
            if self.settings['display_rom_in_fav'] and rom_in_fav: rom_name += ' [COLOR violet][Fav][/COLOR]'
            if rom_in_fav: AEL_InFav_bool_value = AEL_INFAV_BOOL_VALUE_TRUE

        # --- Set common flags to all launchers---
        if rom['disks']: AEL_MultiDisc_bool_value = AEL_MULTIDISC_BOOL_VALUE_TRUE

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
                                       'trailer' : rom['s_trailer'], 'overlay' : ICON_OVERLAY,
                                       'path'    : rom['filename'] })
        else:
            listitem.setInfo('video', {'title'   : rom_name,
                                       'genre'   : rom['m_genre'],   'studio'  : rom['m_developer'],
                                       'rating'  : rom['m_rating'],  'plot'    : rom['m_plot'],
                                       'trailer' : rom['s_trailer'], 'overlay' : ICON_OVERLAY,
                                       'path'    : rom['filename'] })
        listitem.setProperty('nplayers', rom['m_nplayers'])
        listitem.setProperty('esrb', rom['m_esrb'])
        listitem.setProperty('platform', platform)
        listitem.setProperty('filename', rom['filename'])
        listitem.setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROM)

        # --- Set ROM artwork ---
        # AEL custom artwork fields
        listitem.setArt({'title'    : rom['s_title'],    'snap'      : rom['s_snap'],
                         'boxfront' : rom['s_boxfront'], 'boxback'   : rom['s_boxback'],
                         '3dbox'    : rom['s_3dbox'],    'cartridge' : rom['s_cartridge'],
                         'flyer'    : rom['s_flyer'],    'map'       : rom['s_map'] })

        #  Kodi official artwork fields
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
            commands.append(('View Favourite ROM',         self._misc_url_RunPlugin('VIEW',              categoryID, launcherID, romID)))
            commands.append(('Edit ROM in Favourites',     self._misc_url_RunPlugin('EDIT_ROM',          categoryID, launcherID, romID)))
            commands.append(('Add ROM to Collection',      self._misc_url_RunPlugin('ADD_TO_COLLECTION', categoryID, launcherID, romID)))
            commands.append(('Search ROMs in Favourites',  self._misc_url_RunPlugin('SEARCH_LAUNCHER',   categoryID, launcherID)))
            commands.append(('Manage Favourite ROMs',      self._misc_url_RunPlugin('MANAGE_FAV',        categoryID, launcherID, romID)))
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            commands.append(('View Collection ROM',        self._misc_url_RunPlugin('VIEW',              categoryID, launcherID, romID)))
            commands.append(('Edit ROM in Collection',     self._misc_url_RunPlugin('EDIT_ROM',          categoryID, launcherID, romID)))
            commands.append(('Add ROM to AEL Favourites',  self._misc_url_RunPlugin('ADD_TO_FAV',        categoryID, launcherID, romID)))
            commands.append(('Search ROMs in Collection',  self._misc_url_RunPlugin('SEARCH_LAUNCHER',   categoryID, launcherID)))
            commands.append(('Manage Collection ROMs',     self._misc_url_RunPlugin('MANAGE_FAV',        categoryID, launcherID, romID)))

        elif categoryID == VCATEGORY_RECENT_ID:
            commands.append(('View ROM data', self._misc_url_RunPlugin('VIEW', categoryID, launcherID, romID)))
            commands.append(('Manage Recently Played', self._misc_url_RunPlugin('MANAGE_RECENT_PLAYED', categoryID, launcherID, romID)))

        elif categoryID == VCATEGORY_MOST_PLAYED_ID:
            commands.append(('View ROM data', self._misc_url_RunPlugin('VIEW', categoryID, launcherID, romID)))
            commands.append(('Manage Most Played', self._misc_url_RunPlugin('MANAGE_MOST_PLAYED', categoryID, launcherID, romID)))

        elif categoryID == VCATEGORY_TITLE_ID    or categoryID == VCATEGORY_YEARS_ID  or \
             categoryID == VCATEGORY_GENRE_ID    or categoryID == VCATEGORY_DEVELOPER_ID or \
             categoryID == VCATEGORY_NPLAYERS_ID or categoryID == VCATEGORY_ESRB_ID   or \
             categoryID == VCATEGORY_RATING_ID   or categoryID == VCATEGORY_CATEGORY_ID:
            commands.append(('View ROM data',                   self._misc_url_RunPlugin('VIEW',              categoryID, launcherID, romID)))
            commands.append(('Add ROM to AEL Favourites',       self._misc_url_RunPlugin('ADD_TO_FAV',        categoryID, launcherID, romID)))
            commands.append(('Add ROM to Collection',           self._misc_url_RunPlugin('ADD_TO_COLLECTION', categoryID, launcherID, romID)))
            commands.append(('Search ROMs in Virtual Launcher', self._misc_url_RunPlugin('SEARCH_LAUNCHER',   categoryID, launcherID)))
        else:
            commands.append(('View ROM/Launcher', self._misc_url_RunPlugin('VIEW', categoryID, launcherID, romID)))
            if is_parent_launcher and num_clones > 0:
                commands.append(('Show clones', self._misc_url_RunPlugin('EXEC_SHOW_CLONE_ROMS', categoryID, launcherID, romID)))
            commands.append(('Edit ROM',                  self._misc_url_RunPlugin('EDIT_ROM',          categoryID, launcherID, romID)))
            commands.append(('Add ROM to AEL Favourites', self._misc_url_RunPlugin('ADD_TO_FAV',        categoryID, launcherID, romID)))
            commands.append(('Add ROM to Collection',     self._misc_url_RunPlugin('ADD_TO_COLLECTION', categoryID, launcherID, romID)))
            commands.append(('Search ROMs in Launcher',   self._misc_url_RunPlugin('SEARCH_LAUNCHER',   categoryID, launcherID)))
            commands.append(('Edit Launcher',             self._misc_url_RunPlugin('EDIT_LAUNCHER',     categoryID, launcherID)))
        commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
            listitem.addContextMenuItems(commands, replaceItems = True)

        # --- Add row ---
        # URLs must be different depending on the content type. If not Kodi log will be filled with:
        # WARNING: CreateLoader - unsupported protocol(plugin) in the log. See http://forum.kodi.tv/showthread.php?tid=187954
        # if is_parent_launcher and num_clones > 0 and view_mode == LAUNCHER_DMODE_PCLONE:
        #     url_str = self._misc_url('SHOW_CLONE_ROMS', categoryID, launcherID, romID)
        #     xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)
        # else:
        #     url_str = self._misc_url('LAUNCH_ROM', categoryID, launcherID, romID)
        #     xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)
        url_str = self._misc_url('LAUNCH_ROM', categoryID, launcherID, romID)
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

    def _gui_render_AEL_scraper_rom_row(self, platform, game):
        # --- Add ROM to lisitem ---
        kodi_def_thumb = 'DefaultProgram.png'
        ICON_OVERLAY = 4
        listitem = xbmcgui.ListItem(game['title'])

        listitem.setInfo('video', {
            'title'   : game['title'],     'year'    : game['year'],
            'genre'   : game['genre'],     'plot'    : game['plot'],
            'studio'  : game['developer'], 'overlay' : ICON_OVERLAY,
        })
        listitem.setProperty('nplayers', game['nplayers'])
        listitem.setProperty('esrb', game['rating'])
        listitem.setProperty('platform', platform)

        # --- Set ROM artwork ---
        listitem.setArt({'icon' : kodi_def_thumb})

        # --- Create context menu ---
        commands = []
        commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
            listitem.addContextMenuItems(commands, replaceItems = True)

        # --- Add row ---
        # When user clicks on a ROM show the raw database entry
        url_str = self._misc_url('VIEW_OS_ROM', 'AEL', platform, game['ROM'])
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

    def _gui_render_LB_scraper_rom_row(self, platform, game):
        # --- Add ROM to lisitem ---
        kodi_def_thumb = 'DefaultProgram.png'
        ICON_OVERLAY = 4
        listitem = xbmcgui.ListItem(game['Name'])

        listitem.setInfo('video', {
            'title'   : game['Name'],      'year'    : game['ReleaseYear'],
            'genre'   : game['Genres'],    'plot'    : game['Overview'],
            'studio'  : game['Publisher'], 'overlay' : ICON_OVERLAY,
        })
        listitem.setProperty('nplayers', game['MaxPlayers'])
        listitem.setProperty('esrb', game['ESRB'])
        listitem.setProperty('platform', platform)

        # --- Set ROM artwork ---
        listitem.setArt({'icon' : kodi_def_thumb})

        # --- Create context menu ---
        commands = []
        commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
            listitem.addContextMenuItems(commands, replaceItems = True)

        # --- Add row ---
        # When user clicks on a ROM show the raw database entry
        url_str = self._misc_url('VIEW_OS_ROM', 'LaunchBox', platform, game['name'])
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

    #
    # Renders the special category favourites, which is actually very similar to a ROM launcher
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
    def _command_render_favourites(self):
        # >> Content type and sorting method
        self._misc_set_all_sorting_methods()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)
        self._misc_clear_AEL_Launcher_Content()

        # --- Load Favourite ROMs ---
        roms = fs_load_Favourites_JSON(g_PATHS.FAV_JSON_FILE_PATH)
        if not roms:
            kodi_notify('Favourites is empty. Add ROMs to Favourites first.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # --- Display Favourites ---
        for key in sorted(roms, key= lambda x : roms[x]['m_name']):
            self._gui_render_rom_row(VCATEGORY_FAVOURITES_ID, VLAUNCHER_FAVOURITES_ID, roms[key])
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    # ---------------------------------------------------------------------------------------------
    # Virtual Launcher LisItem rendering
    # ---------------------------------------------------------------------------------------------
    #
    # Render virtual launchers inside a virtual category: Title, year, Genre, Studio, Category
    #
    def _command_render_virtual_category(self, virtual_categoryID):
        log_error('_command_render_virtual_category() Starting ...')
        # >> Kodi sorting methods
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_SIZE)
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)
        self._misc_clear_AEL_Launcher_Content()

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
            log_error('_command_render_virtual_category() Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
            kodi_dialog_OK('Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
            return

        # --- If the virtual category has no launchers then render nothing ---
        # >> Also, tell the user to update the virtual launcher database
        if not vcategory_db_filename.exists():
            kodi_dialog_OK('{0} database not found. '.format(vcategory_name) +
                           'Update the virtual category database first.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
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
            commands.append(('Search ROMs in Virtual Launcher', self._misc_url_RunPlugin('SEARCH_LAUNCHER', virtual_categoryID, vlauncher_id)))
            commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', ))
            commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
            if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
                listitem.addContextMenuItems(commands, replaceItems = True)

            url_str = self._misc_url('SHOW_VLAUNCHER_ROMS', virtual_categoryID, vlauncher_id)
            xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Renders ROMs in a virtual launcher.
    #
    def _command_render_virtual_launcher_roms(self, virtual_categoryID, virtual_launcherID):
        log_error('_command_render_virtual_launcher_roms() Starting ...')
        # >> Content type and sorting method
        self._misc_set_all_sorting_methods()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)

        # --- Load virtual launchers in this category ---
        if   virtual_categoryID == VCATEGORY_TITLE_ID:     vcategory_db_dir = g_PATHS.VIRTUAL_CAT_TITLE_DIR
        elif virtual_categoryID == VCATEGORY_YEARS_ID:     vcategory_db_dir = g_PATHS.VIRTUAL_CAT_YEARS_DIR
        elif virtual_categoryID == VCATEGORY_GENRE_ID:     vcategory_db_dir = g_PATHS.VIRTUAL_CAT_GENRE_DIR
        elif virtual_categoryID == VCATEGORY_DEVELOPER_ID: vcategory_db_dir = g_PATHS.VIRTUAL_CAT_DEVELOPER_DIR
        elif virtual_categoryID == VCATEGORY_NPLAYERS_ID:  vcategory_db_dir = g_PATHS.VIRTUAL_CAT_NPLAYERS_DIR
        elif virtual_categoryID == VCATEGORY_ESRB_ID:      vcategory_db_dir = g_PATHS.VIRTUAL_CAT_ESRB_DIR
        elif virtual_categoryID == VCATEGORY_RATING_ID:    vcategory_db_dir = g_PATHS.VIRTUAL_CAT_RATING_DIR
        elif virtual_categoryID == VCATEGORY_CATEGORY_ID:  vcategory_db_dir = g_PATHS.VIRTUAL_CAT_CATEGORY_DIR
        else:
            log_error('_command_render_virtual_launcher_roms() Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
            kodi_dialog_OK('Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
            return

        # --- Load Virtual Launcher DB ---
        hashed_db_filename = vcategory_db_dir.pjoin(virtual_launcherID + '.json')
        if not hashed_db_filename.exists():
            kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
            return
        roms = fs_load_VCategory_ROMs_JSON(vcategory_db_dir, virtual_launcherID)
        if not roms:
            kodi_notify('Virtual category ROMs XML empty. Add items to favourites first.')
            return

        # --- Load favourites ---
        # >> Optimisation: Transform the dictionary keys into a set. Sets are the fastest
        #    when checking if an element exists.
        roms_fav = fs_load_Favourites_JSON(g_PATHS.FAV_JSON_FILE_PATH)
        roms_fav_set = set(roms_fav.keys())

        # --- Display Favourites ---
        for key in sorted(roms, key= lambda x : roms[x]['m_name']):
            self._gui_render_rom_row(virtual_categoryID, virtual_launcherID, roms[key], key in roms_fav_set)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Renders ROMs in a AEL offline Scraper virtual launcher (aka platform)
    #
    def _command_render_AEL_scraper_roms(self, platform):
        log_debug('_command_render_AEL_scraper_roms() platform "{}"'.format(platform))
        pobj = AEL_platforms[get_AEL_platform_index(platform)]
        if pobj.aliasof:
            log_debug('_command_view_offline_scraper_rom() aliasof "{}"'.format(pobj.aliasof))
            pobj_parent = AEL_platforms[get_AEL_platform_index(pobj.aliasof)]
            db_platform = pobj_parent.long_name
        else:
            db_platform = pobj.long_name
        log_debug('_command_view_offline_scraper_rom() db_platform "{}"'.format(db_platform))

        # Content type and sorting method
        self._misc_set_all_sorting_methods()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)

        # If XML DB not available tell user and leave
        xml_path_FN = g_PATHS.GAMEDB_INFO_DIR.pjoin(db_platform + '.xml')
        log_debug('xml_path_FN OP {}'.format(xml_path_FN.getOriginalPath()))
        log_debug('xml_path_FN  P {}'.format(xml_path_FN.getPath()))
        if not xml_path_FN.exists():
            kodi_notify_warn('{} database not available yet.'.format(db_platform))
            # kodi_refresh_container()
            return

        # --- Load offline scraper XML file ---
        loading_ticks_start = time.time()
        games = audit_load_OfflineScraper_XML(xml_path_FN.getPath())
        loading_ticks_end = time.time()

        # --- Display offline scraper ROMs ---
        rendering_ticks_start = time.time()
        for key in sorted(games, key= lambda x : games[x]['ROM']):
            self._gui_render_AEL_scraper_rom_row(platform, games[key])
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
        rendering_ticks_end = time.time()

        # --- DEBUG Data loading/rendering statistics ---
        log_debug('Loading seconds   {}'.format(loading_ticks_end - loading_ticks_start))
        log_debug('Rendering seconds {}'.format(rendering_ticks_end - rendering_ticks_start))

    #
    # Renders ROMs in a LaunchBox offline Scraper virtual launcher (aka platform)
    #
    def _command_render_LB_scraper_roms(self, platform):
        log_debug('_command_render_LB_scraper_roms() platform = "{}"'.format(platform))
        # >> Content type and sorting method
        self._misc_set_all_sorting_methods()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)

        # >> If XML DB not available tell user and leave
        xml_file = platform_AEL_to_LB_XML[platform]
        if not xml_file:
            kodi_notify_warn('{} database not available yet.'.format(platform))
            # kodi_refresh_container()
            return

        # --- Load offline scraper XML file ---
        loading_ticks_start = time.time()
        xml_path_FN = g_PATHS.ADDON_CODE_DIR.pjoin(xml_file)
        log_debug('xml_path_FN OP {}'.format(xml_path_FN.getOriginalPath()))
        log_debug('xml_path_FN  P {}'.format(xml_path_FN.getPath()))
        games = audit_load_OfflineScraper_XML(xml_path_FN.getPath())

        # --- Display offline scraper ROMs ---
        loading_ticks_end = time.time()
        rendering_ticks_start = time.time()
        for key in sorted(games, key= lambda x : games[x]['name']):
            self._gui_render_LB_scraper_rom_row(platform, games[key])
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
        rendering_ticks_end = time.time()

        # --- DEBUG Data loading/rendering statistics ---
        log_debug('Loading seconds   {}'.format(loading_ticks_end - loading_ticks_start))
        log_debug('Rendering seconds {}'.format(rendering_ticks_end - rendering_ticks_start))

    #
    # Render the Recently played and Most Played virtual launchers.
    #
    def _command_render_recently_played(self):
        # >> Content type and sorting method
        self._misc_set_default_sorting_method()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)

        # --- Load Recently Played favourite ROM list and create and OrderedDict ---
        rom_list = fs_load_Collection_ROMs_JSON(g_PATHS.RECENT_PLAYED_FILE_PATH)
        if not rom_list:
            kodi_notify('Recently played list is empty. Play some ROMs first!')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # --- Display recently player ROM list ---
        for rom in rom_list:
            self._gui_render_rom_row(VCATEGORY_RECENT_ID, VLAUNCHER_RECENT_ID, rom)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    def _command_render_most_played(self):
        # >> Content type and sorting method
        self._misc_set_default_sorting_method()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)

        # --- Load Most Played favourite ROMs ---
        roms = fs_load_Favourites_JSON(g_PATHS.MOST_PLAYED_FILE_PATH)
        if not roms:
            kodi_notify('Most played ROMs list is empty. Play some ROMs first!.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # --- Display most played ROMs, order by number of launchs ---
        for key in sorted(roms, key = lambda x : roms[x]['launch_count'], reverse = True):
            self._gui_render_rom_row(VCATEGORY_MOST_PLAYED_ID, VLAUNCHER_MOST_PLAYED_ID, roms[key])
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Render all ROMs
    # This command is called by skins. Not advisable to use it if there are many ROMs...
    #
    def _command_render_all_ROMs(self):
        # --- Make a dictionary having all ROMs in all Launchers ---
        log_debug('_command_render_all_ROMs() Creating list of all ROMs in all Launchers')
        all_roms = {}
        for launcher_id in self.launchers:
            launcher = self.launchers[launcher_id]
            # If launcher is standalone skip
            if not launcher['rompath']: continue
            roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, launcher)
            temp_roms = {}
            for rom_id in roms:
                temp_rom = roms[rom_id].copy()
                temp_rom['launcher_id'] = launcher_id
                temp_rom['category_id'] = launcher['categoryID']
                temp_roms[rom_id] = temp_rom
            all_roms.update(temp_roms)

        # --- Load favourites ---
        roms_fav = fs_load_Favourites_JSON(g_PATHS.FAV_JSON_FILE_PATH)
        roms_fav_set = set(roms_fav.keys())

        # --- Set content type and sorting methods ---
        self._misc_set_default_sorting_method()

        # --- Render ROMs ---
        for rom_id in sorted(all_roms, key = lambda x : all_roms[x]['m_name']):
            self._gui_render_rom_row(
                all_roms[rom_id]['category_id'], all_roms[rom_id]['launcher_id'],
                all_roms[rom_id], rom_id in roms_fav_set)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Adds ROM to favourites
    #
    def _command_add_to_favourites(self, categoryID, launcherID, romID):
        # ROM in Virtual Launcher
        # TODO if ROM in virtual launcher is not correctly linked, for example, if launcher
        #      does not currently exists, AEL will crash. Unlinked launcher/Broken ROMs
        #      must be detected and rejected to be added to Favourites.
        if categoryID == VCATEGORY_TITLE_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_TITLE_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        elif categoryID == VCATEGORY_YEARS_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_YEARS_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        elif categoryID == VCATEGORY_GENRE_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_GENRE_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        elif categoryID == VCATEGORY_DEVELOPER_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_DEVELOPER_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        elif categoryID == VCATEGORY_CATEGORY_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_CATEGORY_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        # ROM in ROM Collection
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            collections, update_tstamp = fs_load_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH)
            roms_json_file = g_PATHS.COLLECTIONS_DIR.pjoin(collections[launcherID]['roms_base_noext'] + '.json')
            rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
            roms = OrderedDict()
            for crom in rom_list: roms[crom['id']] = crom
            launcher = self.launchers[roms[romID]['launcherID']]
        # ROM in standard launcher
        else:
            launcher = self.launchers[launcherID]
            roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, launcher)

        # Sanity check
        if not roms:
            kodi_dialog_OK('Empty roms launcher in _command_add_to_favourites(). This is a bug, please report it.')
            return

        # --- Load favourites ---
        roms_fav = fs_load_Favourites_JSON(g_PATHS.FAV_JSON_FILE_PATH)

        # --- DEBUG info ---
        log_verb('_command_add_to_favourites() Adding ROM to Favourites')
        log_verb('_command_add_to_favourites() romID  {}'.format(romID))
        log_verb('_command_add_to_favourites() m_name {}'.format(roms[romID]['m_name']))

        # Check if ROM already in favourites an warn user if so
        if romID in roms_fav:
            log_verb('Already in favourites')
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher',
                               'ROM {} is already on AEL Favourites. Overwrite it?'.format(roms[romID]['m_name']))
            if not ret:
                log_verb('User does not want to overwrite. Exiting.')
                return
        # Confirm if rom should be added
        else:
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher',
                                'ROM {}. Add this ROM to AEL Favourites?'.format(roms[romID]['m_name']))
            if not ret:
                log_verb('User does not confirm addition. Exiting.')
                return

        # --- Add ROM to favourites ROMs and save to disk ---
        roms_fav[romID] = fs_get_Favourite_from_ROM(roms[romID], launcher)
        # >> If thumb is empty then use launcher thum. / If fanart is empty then use launcher fanart.
        # if roms_fav[romID]['thumb']  == '': roms_fav[romID]['thumb']  = launcher['thumb']
        # if roms_fav[romID]['fanart'] == '': roms_fav[romID]['fanart'] = launcher['fanart']
        fs_write_Favourites_JSON(g_PATHS.FAV_JSON_FILE_PATH, roms_fav)
        kodi_notify('ROM {} added to Favourites'.format(roms[romID]['m_name']))
        kodi_refresh_container()

    #
    # Manage Favourite/Collection ROMs as a whole.
    #
    def _command_manage_favourites(self, categoryID, launcherID, romID):
        # --- Load ROMs ---
        if categoryID == VCATEGORY_FAVOURITES_ID:
            log_debug('_command_manage_favourites() Managing Favourite ROMs')
            roms_fav = fs_load_Favourites_JSON(g_PATHS.FAV_JSON_FILE_PATH)
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            log_debug('_command_manage_favourites() Managing Collection ROMs')
            (collections, update_timestamp) = fs_load_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH)
            collection = collections[launcherID]
            roms_json_file = g_PATHS.COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
            collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
            # NOTE ROMs in a collection are stored as a list and ROMs in Favourites are stored as
            #      a dictionary. Convert the Collection list into an ordered dictionary and then
            #      converted back the ordered dictionary into a list before saving the collection.
            roms_fav = OrderedDict()
            for collection_rom in collection_rom_list:
                roms_fav[collection_rom['id']] = collection_rom
        else:
            kodi_dialog_OK(
                '_command_manage_favourites() should be called for Favourites or Collections. '
                'This is a bug, please report it.')
            return

        # --- Show selection dialog ---
        dialog = xbmcgui.Dialog()
        if categoryID == VCATEGORY_FAVOURITES_ID:
            type = dialog.select('Manage Favourite ROMs', [
                'Check Favourite ROMs',
                'Repair Unlinked Launcher/Broken ROMs (by filename)',
                'Repair Unlinked Launcher/Broken ROMs (by basename)',
                'Repair Unlinked ROMs',
            ])
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            type = dialog.select('Manage Collection ROMs', [
                'Check Collection ROMs',
                'Repair Unlinked Launcher/Broken ROMs (by filename)',
                'Repair Unlinked Launcher/Broken ROMs (by basename)',
                'Repair Unlinked ROMs',
                'Sort Collection ROMs alphabetically',
            ])

        # --- Check Favourite ROMs ---
        if type == 0:
            # >> This function opens a progress window to notify activity
            self._fav_check_favourites(roms_fav)

            # --- Print a report of issues found ---
            if categoryID == VCATEGORY_FAVOURITES_ID:
                kodi_dialog_OK(
                    'You have {} ROMs in Favourites. '.format(self.num_fav_roms) +
                    '{} Unlinked Launcher, '.format(self.num_fav_ulauncher) +
                    '{} Unliked ROM and '.format(self.num_fav_urom) +
                    '{} Broken.'.format(self.num_fav_broken))
            elif categoryID == VCATEGORY_COLLECTIONS_ID:
                kodi_dialog_OK(
                    'You have {} ROMs in Collection "{}". '.format(self.num_fav_roms, collection['m_name']) +
                    '{} Unlinked Launcher, '.format(self.num_fav_ulauncher) +
                    '{} Unliked ROM and '.format(self.num_fav_urom) +
                    '{} are Broken.'.format(self.num_fav_broken))

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
            for rom_fav_ID in roms_fav:
                pDialog.update(i * 100 / num_progress_items)
                if pDialog.iscanceled():
                    pDialog.close()
                    kodi_dialog_OK('Repair cancelled. No changes has been done.')
                    return
                i += 1

                # >> Only process Unlinked Launcher ROMs
                if roms_fav[rom_fav_ID]['fav_status'] == 'OK': continue
                if roms_fav[rom_fav_ID]['fav_status'] == 'Unlinked ROM': continue
                fav_name = roms_fav[rom_fav_ID]['m_name']
                num_broken_ROMs += 1
                log_info('_command_manage_favourites() Repairing Fav ROM "{0}"'.format(fav_name))
                log_info('_command_manage_favourites() Fav ROM status "{0}"'.format(roms_fav[rom_fav_ID]['fav_status']))

                # >> Traverse all launchers and find rom by filename or base name
                ROM_FN_FAV = FileName(roms_fav[rom_fav_ID]['filename'])
                filename_found = False
                for launcher_id in self.launchers:
                    # >> Load launcher ROMs
                    roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, self.launchers[launcher_id])
                    for rom_id in roms:
                        ROM_FN = FileName(roms[rom_id]['filename'])
                        fav_name = roms_fav[rom_fav_ID]['m_name']
                        if type == 1 and roms_fav[rom_fav_ID]['filename'] == roms[rom_id]['filename']:
                            log_info('_command_manage_favourites() Favourite {0} matched by filename!'.format(fav_name))
                            log_info('_command_manage_favourites() Launcher {0}'.format(launcher_id))
                            log_info('_command_manage_favourites() ROM {0}'.format(rom_id))
                        elif type == 2 and ROM_FN_FAV.getBase() == ROM_FN.getBase():
                            log_info('_command_manage_favourites() Favourite {0} matched by basename!'.format(fav_name))
                            log_info('_command_manage_favourites() Launcher {0}'.format(launcher_id))
                            log_info('_command_manage_favourites() ROM {0}'.format(rom_id))
                        else:
                            continue
                        # >> Match found. Break all for loops inmediately.
                        filename_found      = True
                        new_fav_rom_ID      = rom_id
                        new_fav_rom_laun_ID = launcher_id
                        break
                    if filename_found: break

                # >> Add ROM to the list of ROMs to be repaired.
                if filename_found:
                    rom_repair = {}
                    rom_repair['old_fav_rom_ID']      = rom_fav_ID
                    rom_repair['new_fav_rom_ID']      = new_fav_rom_ID
                    rom_repair['new_fav_rom_laun_ID'] = new_fav_rom_laun_ID
                    rom_repair['old_fav_rom']         = roms_fav[rom_fav_ID]
                    rom_repair['parent_rom']          = roms[new_fav_rom_ID]
                    rom_repair['parent_launcher']     = self.launchers[new_fav_rom_laun_ID]
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
                log_debug('_command_manage_favourites() Name          {0}'.format(old_fav_rom['m_name']))
                log_debug('_command_manage_favourites() New ROM       {0}'.format(new_fav_rom_ID))
                log_debug('_command_manage_favourites() New Launcher  {0}'.format(new_fav_rom_laun_ID))

                # >> Relink Favourite ROM. Removed old Favourite before inserting new one.
                new_fav_rom = fs_repair_Favourite_ROM(repair_mode, old_fav_rom, parent_rom, parent_launcher)
                roms_fav = misc_replace_fav(roms_fav, old_fav_rom_ID, new_fav_rom['id'], new_fav_rom)
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
            repair_mode = dialog.select(
                'How to repair ROMs?', [
                'Relink and update launcher info',
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
                launcher_roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, self.launchers[launcher_id])

                # >> Is there a ROM with same basename (including extension) as the Favourite ROM?
                filename_found = False
                ROM_FAV_FN = FileName(rom_fav['filename'])
                for rom_id in launcher_roms:
                    ROM_FN = FileName(launcher_roms[rom_id]['filename'])
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
                    rom_repair['parent_launcher']     = self.launchers[launcher_id]
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

                # Relink Favourite ROM. Removed old Favourite before inserting new one.
                new_fav_rom = fs_repair_Favourite_ROM(repair_mode, old_fav_rom, parent_rom, parent_launcher)
                roms_fav = misc_replace_fav(roms_fav, old_fav_rom_ID, new_fav_rom['id'], new_fav_rom)
                num_repaired_ROMs += 1
            log_debug('_command_manage_favourites() Repaired {0} ROMs'.format(num_repaired_ROMs))

            # >> Show info to user
            kodi_dialog_OK(
                'Found {} Unlinked ROMs. '.format(num_unlinked_ROMs) +
                'Of those, {} were repaired.'.format(num_repaired_ROMs))

        # --- Short collection ROMs alphabetically ---
        # https://docs.python.org/3/howto/sorting.html
        # https://stackoverflow.com/questions/3382352/equivalent-of-numpy-argsort-in-basic-python/3383106
        elif type == 4:
            log_debug('Sorting Collecion ROMs alphabetically...')
            col_rom_list = [roms_fav[key] for key in roms_fav]
            name_list = [rom['m_name'] for rom in col_rom_list]
            sorted_idx_list = [i for (v, i) in sorted((v.lower(), i) for (i, v) in enumerate(name_list))]
            new_roms_fav = OrderedDict()
            for idx in sorted_idx_list:
                rom = col_rom_list[idx]
                new_roms_fav[rom['id']] = rom
                # log_debug('Index {:03d} ROM "{}"'.format(idx, rom['m_name']))
            roms_fav = new_roms_fav

        # --- User cancelled dialog ---
        elif type < 0: return

        # --- If we reach this point save favourites and refresh container ---
        if categoryID == VCATEGORY_FAVOURITES_ID:
            fs_write_Favourites_JSON(g_PATHS.FAV_JSON_FILE_PATH, roms_fav)
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            # Convert back the OrderedDict into a list and save Collection
            collection_rom_list = [roms_fav[key] for key in roms_fav]
            json_file = g_PATHS.COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
            fs_write_Collection_ROMs_JSON(json_file, collection_rom_list)
        kodi_refresh_container()

    #
    # Check ROMs in favourites and set fav_status field.
    # roms_fav edited by passing by assigment, dictionaries are mutable.
    #
    def _fav_check_favourites(self, roms_fav):
        # --- Statistics ---
        self.num_fav_roms = len(roms_fav)
        self.num_fav_ulauncher = 0
        self.num_fav_urom      = 0
        self.num_fav_broken    = 0

        # --- Reset fav_status filed for all favourites ---
        log_debug('_fav_check_favourites() STEP 0: Reset status')
        for rom_fav_ID in roms_fav:
            roms_fav[rom_fav_ID]['fav_status'] = 'OK'

        # --- Progress dialog ---
        # >> Important to avoid multithread execution of the plugin and race conditions
        pDialog = xbmcgui.DialogProgress()

        # STEP 1: Find Favourites with missing launchers
        log_debug('_fav_check_favourites() STEP 1: Search unlinked Launchers')
        num_progress_items = len(roms_fav)
        i = 0
        pDialog.create('Advanced Emulator Launcher', 'Checking Favourite ROMs. Step 1 of 3 ...')
        for rom_fav_ID in roms_fav:
            pDialog.update(i * 100 / num_progress_items)
            i += 1
            if roms_fav[rom_fav_ID]['launcherID'] not in self.launchers:
                log_verb('Fav ROM "{0}" Unlinked Launcher because launcherID not in self.launchers'.format(roms_fav[rom_fav_ID]['m_name']))
                roms_fav[rom_fav_ID]['fav_status'] = 'Unlinked Launcher'
                self.num_fav_ulauncher += 1
        pDialog.update(i * 100 / num_progress_items)
        pDialog.close()

        # STEP 2: Find missing ROM ID
        # Get a list of launchers Favourite ROMs belong.
        log_debug('_fav_check_favourites() STEP 2: Search unlinked ROMs')
        launchers_fav = set()
        for rom_fav_ID in roms_fav: launchers_fav.add(roms_fav[rom_fav_ID]['launcherID'])

        # Traverse list of launchers. For each launcher, load ROMs it and check all favourite ROMs
        # that belong to that launcher.
        num_progress_items = len(launchers_fav)
        i = 0
        pDialog.create('Advanced Emulator Launcher', 'Checking Favourite ROMs. Step 2 of 3...')
        for launcher_id in launchers_fav:
            pDialog.update(i * 100 / num_progress_items)
            i += 1

            # >> If Favourite does not have launcher skip it. It has been marked as 'Unlinked Launcher'
            # >> in step 1.
            if launcher_id not in self.launchers: continue

            # >> Load launcher ROMs
            roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, self.launchers[launcher_id])

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
            romFile = FileName(roms_fav[rom_fav_ID]['filename'])
            if not romFile.exists():
                log_verb('Fav ROM "{0}" broken because filename does not exist'.format(roms_fav[rom_fav_ID]['m_name']))
                roms_fav[rom_fav_ID]['fav_status'] = 'Broken'
                self.num_fav_broken += 1
        pDialog.update(i * 100 / num_progress_items)
        pDialog.close()

    # Recently Played ROMs are stored in a list of ROM dictionaries.
    def _command_manage_recently_played(self, rom_ID):
        VIEW_ROOT_MENU   = 100
        VIEW_INSIDE_MENU = 200

        ACTION_DELETE_MACHINE = 100
        ACTION_DELETE_MISSING = 200
        ACTION_DELETE_ALL     = 300

        menus_dic = {
            VIEW_ROOT_MENU : [
                ('Delete missing machines from Recently Played', ACTION_DELETE_MISSING),
                ('Delete all machines from Recently Played', ACTION_DELETE_ALL),
            ],
            VIEW_INSIDE_MENU : [
                ('Delete machine from Recently Played', ACTION_DELETE_MACHINE),
                ('Delete missing machines from Recently Played', ACTION_DELETE_MISSING),
                ('Delete all machines from Recently Played', ACTION_DELETE_ALL),
            ],
        }

        # --- Determine view type ---
        log_debug('_command_manage_most_played() BEGIN...')
        log_debug('rom_ID "{0}"'.format(rom_ID))
        if rom_ID:
            view_type = VIEW_INSIDE_MENU
        else:
            view_type = VIEW_ROOT_MENU
        log_debug('view_type {0}'.format(view_type))

        # --- Build menu base on view_type (Polymorphic menu, determine action) ---
        d_list = [menu[0] for menu in menus_dic[view_type]]
        selected_value = xbmcgui.Dialog().select('Manage Recently Played ROMs', d_list)
        if selected_value < 0: return
        action = menus_dic[view_type][selected_value][1]
        log_debug('action {0}'.format(action))

        # --- Execute actions ---
        if action == ACTION_DELETE_MACHINE:
            log_debug('_command_manage_most_played() ACTION_DELETE_MACHINE')

            # --- Load ROMs ---
            rom_list = fs_load_Collection_ROMs_JSON(g_PATHS.RECENT_PLAYED_FILE_PATH)
            roms = OrderedDict()
            for rom in rom_list: roms[rom['id']] = rom
            if not roms:
                kodi_notify('Recently Played ROMs list is empty. Play some ROMs first!.')
                return

            # --- Confirm deletion ---
            rom_name = roms[rom_ID]['m_name']
            msg_str = 'Are you sure you want to delete it from Recently Played ROMs?'
            ret = kodi_dialog_yesno('ROM "{0}". '.format(rom_name) + msg_str)
            if not ret: return
            roms.pop(rom_ID)

            # --- Save ROMs and notify user ---
            # Convert from OrderedDict to list.
            rom_list = [roms[key] for key in roms]
            fs_write_Collection_ROMs_JSON(g_PATHS.RECENT_PLAYED_FILE_PATH, rom_list)
            kodi_notify('Deleted ROM {0}'.format(rom_name))
            kodi_refresh_container()

        elif action == ACTION_DELETE_ALL:
            log_debug('_command_manage_most_played() ACTION_DELETE_ALL')

            # --- Confirm deletion ---
            msg_str = 'Are you sure you want to delete all Recently Played ROMs?'
            ret = kodi_dialog_yesno(msg_str)
            if not ret: return

            # --- Save ROMs and notify user ---
            fs_write_Collection_ROMs_JSON(g_PATHS.RECENT_PLAYED_FILE_PATH, [])
            kodi_notify('Deleted all Recently Played ROMs')
            kodi_refresh_container()

        elif action == ACTION_DELETE_MISSING:
            log_debug('_command_manage_most_played() ACTION_DELETE_MISSING')

            # --- Load ROMs ---
            rom_list = fs_load_Collection_ROMs_JSON(g_PATHS.RECENT_PLAYED_FILE_PATH)
            roms = OrderedDict()
            for rom in rom_list: roms[rom['id']] = rom
            if not roms:
                kodi_notify('Recently Played ROMs list is empty. Play some ROMs first!.')
                return

            # --- Traverse ROMs and check if they exist in Launcher ---
            # Naive, slow implementation. I will improve it when I had time.
            # Dictionaries cannot be modified while being iterated. Make a list of keys
            # to be deleted later.
            pDialog = KodiProgressDialog()
            pDialog.startProgress('Delete missing Recently Played ROMs', len(roms))
            ROM_counter = 0
            delete_key_list = []
            for rom_ID in roms:
                pDialog.updateProgress(ROM_counter)
                ROM_counter += 1

                # STEP 1: Delete Favourite with missing Launcher.
                launcher_id = roms[rom_ID]['launcherID']
                if launcher_id not in self.launchers:
                    log_debug('ROM title {} ID {}'.format(roms[rom_ID]['m_name'], rom_ID))
                    log_debug('launcherID {} not found in Launchers.'.format(roms[rom_ID]['launcherID']))
                    log_debug('Deleting ROM from Recently Played ROMs')
                    delete_key_list.append(rom_ID)
                    continue

                # STEP 2: Delete Favourite if ROM ID cannot be found in Launcher.
                launcher_roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, self.launchers[launcher_id])
                if rom_ID not in launcher_roms:
                    log_debug('ROM title {} ID {}'.format(roms[rom_ID]['m_name'], rom_ID))
                    log_debug('rom_ID {} not found in launcher ROMs.'.format(rom_ID))
                    log_debug('Deleting ROM from Recently Played ROMs')
                    delete_key_list.append(rom_ID)
                    continue
            pDialog.endProgress()
            log_debug('len(delete_key_list) = {}'.format(len(delete_key_list)))
            for key in delete_key_list: del roms[key]

            # --- Save ROMs and notify user ---
            # Convert from OrderedDict to list.
            rom_list = [roms[key] for key in roms]
            fs_write_Collection_ROMs_JSON(g_PATHS.RECENT_PLAYED_FILE_PATH, rom_list)
            if len(delete_key_list) == 0:
                kodi_notify('No Recently Played ROMs deleted')
            else:
                kodi_notify('Deleted {} Recently Played ROMs'.format(len(delete_key_list)))
            kodi_refresh_container()

        else:
            t = 'Wrong action = {}. This is a bug, please report it.'.format(action)
            log_error(t)
            kodi_dialog_OK(t)

    # Most played ROMs are stored in a dictionary, key ROM ID and value ROM dictionary.
    def _command_manage_most_played(self, rom_ID):
        VIEW_ROOT_MENU   = 100
        VIEW_INSIDE_MENU = 200

        ACTION_DELETE_MACHINE = 100
        ACTION_DELETE_MISSING = 200
        ACTION_DELETE_ALL     = 300

        menus_dic = {
            VIEW_ROOT_MENU : [
                ('Delete missing machines from Most Played', ACTION_DELETE_MISSING),
                ('Delete all machines from Most Played', ACTION_DELETE_ALL),
            ],
            VIEW_INSIDE_MENU : [
                ('Delete machine from Most Played', ACTION_DELETE_MACHINE),
                ('Delete missing machines from Most Played', ACTION_DELETE_MISSING),
                ('Delete all machines from Most Played', ACTION_DELETE_ALL),
            ],
        }

        # --- Determine view type ---
        log_debug('_command_manage_most_played() BEGIN...')
        log_debug('rom_ID "{0}"'.format(rom_ID))
        if rom_ID:
            view_type = VIEW_INSIDE_MENU
        else:
            view_type = VIEW_ROOT_MENU
        log_debug('view_type {0}'.format(view_type))

        # --- Build menu base on view_type (Polymorphic menu, determine action) ---
        d_list = [menu[0] for menu in menus_dic[view_type]]
        selected_value = xbmcgui.Dialog().select('Manage Most Played ROMs', d_list)
        if selected_value < 0: return
        action = menus_dic[view_type][selected_value][1]
        log_debug('action {0}'.format(action))

        # --- Execute actions ---
        if action == ACTION_DELETE_MACHINE:
            log_debug('_command_manage_most_played() ACTION_DELETE_MACHINE')

            # --- Load ROMs ---
            roms = fs_load_Favourites_JSON(g_PATHS.MOST_PLAYED_FILE_PATH)
            if not roms:
                kodi_notify('Most Played ROMs list is empty. Play some ROMs first!.')
                return

            # --- Confirm deletion ---
            rom_name = roms[rom_ID]['m_name']
            msg_str = 'Are you sure you want to delete it from Most Played ROMs?'
            ret = kodi_dialog_yesno('ROM "{0}". '.format(rom_name) + msg_str)
            if not ret: return
            roms.pop(rom_ID)

            # --- Save ROMs and notify user ---
            fs_write_Favourites_JSON(g_PATHS.MOST_PLAYED_FILE_PATH, roms)
            kodi_notify('Deleted ROM {0}'.format(rom_name))
            kodi_refresh_container()

        elif action == ACTION_DELETE_ALL:
            log_debug('_command_manage_most_played() ACTION_DELETE_ALL')

            # --- Confirm deletion ---
            msg_str = 'Are you sure you want to delete all Most Played ROMs?'
            ret = kodi_dialog_yesno(msg_str)
            if not ret: return

            # --- Save ROMs and notify user ---
            fs_write_Favourites_JSON(g_PATHS.MOST_PLAYED_FILE_PATH, {})
            kodi_notify('Deleted all Most Played ROMs')
            kodi_refresh_container()

        elif action == ACTION_DELETE_MISSING:
            log_debug('_command_manage_most_played() ACTION_DELETE_MISSING')

            # --- Load ROMs ---
            roms = fs_load_Favourites_JSON(g_PATHS.MOST_PLAYED_FILE_PATH)
            if not roms:
                kodi_notify('Most Played ROMs list is empty. Play some ROMs first!.')
                return

            # --- Traverse ROMs and check if they exist in Launcher ---
            # Naive, slow implementation. I will improve it when I had time.
            # Dictionaries cannot be modified while being iterated. Make a list of keys
            # to be deleted later.
            pDialog = KodiProgressDialog()
            pDialog.startProgress('Delete missing Most Played ROMs', len(roms))
            ROM_counter = 0
            delete_key_list = []
            for rom_ID in roms:
                pDialog.updateProgress(ROM_counter)
                ROM_counter += 1

                # STEP 1: Delete Favourite with missing Launcher.
                launcher_id = roms[rom_ID]['launcherID']
                if launcher_id not in self.launchers:
                    log_debug('ROM title {} ID {}'.format(roms[rom_ID]['m_name'], rom_ID))
                    log_debug('launcherID {} not found in Launchers.'.format(roms[rom_ID]['launcherID']))
                    log_debug('Deleting ROM from Most Played ROMs')
                    delete_key_list.append(rom_ID)
                    continue

                # STEP 2: Delete Favourite if ROM ID cannot be found in Launcher.
                launcher_roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, self.launchers[launcher_id])
                if rom_ID not in launcher_roms:
                    log_debug('ROM title {} ID {}'.format(roms[rom_ID]['m_name'], rom_ID))
                    log_debug('rom_ID {} not found in launcher ROMs.'.format(rom_ID))
                    log_debug('Deleting ROM from Most Played ROMs')
                    delete_key_list.append(rom_ID)
                    continue
            pDialog.endProgress()
            log_debug('len(delete_key_list) = {}'.format(len(delete_key_list)))
            for key in delete_key_list: del roms[key]

            # --- Save ROMs and notify user ---
            fs_write_Favourites_JSON(g_PATHS.MOST_PLAYED_FILE_PATH, roms)
            if len(delete_key_list) == 0:
                kodi_notify('No Most Played ROMs deleted')
            else:
                kodi_notify('Deleted {} Most Played ROMs'.format(len(delete_key_list)))
            kodi_refresh_container()

        else:
            t = 'Wrong action = {}. This is a bug, please report it.'.format(action)
            log_error(t)
            kodi_dialog_OK(t)

    #
    # Renders a listview with all collections
    #
    def _command_render_collections(self):
        # >> Kodi sorting method
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)

        # --- Load collection index ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH)

        # --- If the virtual category has no launchers then render nothing ---
        if not collections:
            kodi_notify('No collections in database. Add a collection first.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
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

            # --- Create context menu ---
            commands = []
            commands.append(('View ROM Collection data', self._misc_url_RunPlugin('VIEW', VCATEGORY_COLLECTIONS_ID, collection_id)))
            commands.append(('Export Collection',        self._misc_url_RunPlugin('EXPORT_COLLECTION', VCATEGORY_COLLECTIONS_ID, collection_id)))
            commands.append(('Edit Collection',          self._misc_url_RunPlugin('EDIT_COLLECTION', VCATEGORY_COLLECTIONS_ID, collection_id)))
            commands.append(('Delete Collection',        self._misc_url_RunPlugin('DELETE_COLLECTION', VCATEGORY_COLLECTIONS_ID, collection_id), ))
            commands.append(('Create New Collection',    self._misc_url_RunPlugin('ADD_COLLECTION')))
            commands.append(('Import Collection',        self._misc_url_RunPlugin('IMPORT_COLLECTION')))
            commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
            commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
            if (xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)")):
                listitem.addContextMenuItems(commands, replaceItems = True)

            # >> Use ROMs renderer to display collection ROMs
            url_str = self._misc_url('SHOW_COLLECTION_ROMS', VCATEGORY_COLLECTIONS_ID, collection_id)
            xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    def _command_render_collection_ROMs(self, categoryID, launcherID):
        self._misc_set_default_sorting_method()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)

        # --- Load Collection index and ROMs ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH)
        collection = collections[launcherID]
        roms_json_file = g_PATHS.COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
        collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
        if not collection_rom_list:
            kodi_notify('Collection is empty. Add ROMs to this collection first.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # --- Display Collection ---
        for rom in collection_rom_list:
            self._gui_render_rom_row(categoryID, launcherID, rom)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Adds a new collection
    #
    def _command_add_collection(self):
        # --- Load collection index ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH)

        # --- Get new collection name ---
        dialog = xbmcgui.Dialog()
        keyboard = xbmc.Keyboard('', 'New Collection name')
        keyboard.doModal()
        if not keyboard.isConfirmed(): return

        # --- Add new collection to database ---
        collection           = fs_new_collection()
        collection_name      = keyboard.getText()
        collection_id_md5    = hashlib.md5(collection_name)
        collection_UUID      = collection_id_md5.hexdigest()
        collection_base_name = fs_get_collection_ROMs_basename(collection_name, collection_UUID)
        collection['id']              = collection_UUID
        collection['m_name']          = collection_name
        collection['roms_base_noext'] = collection_base_name
        collections[collection_UUID]  = collection
        log_debug('_command_add_collection() id              "{0}"'.format(collection['id']))
        log_debug('_command_add_collection() m_name          "{0}"'.format(collection['m_name']))
        log_debug('_command_add_collection() roms_base_noext "{0}"'.format(collection['roms_base_noext']))

        # --- Save collections XML database ---
        fs_write_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH, collections)
        kodi_refresh_container()
        kodi_notify('Created ROM Collection "{0}"'.format(collection_name))

    #
    # Edits collection artwork
    #
    def _command_edit_collection(self, categoryID, launcherID):
        # --- Load collection index ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH)
        collection = collections[launcherID]

        # --- Shows a select box with the options to edit ---
        dialog = xbmcgui.Dialog()
        type = dialog.select('Select action for ROM Collection {0}'.format(collection['m_name']),
                            ['Edit Metadata ...', 'Edit Assets/Artwork ...',
                             'Choose default Assets/Artwork ...'])
        # >> User cancelled select dialog
        if type < 0: return

        # --- Edit category metadata ---
        if type == 0:
            NFO_FileName = fs_get_collection_NFO_name(self.settings, collection)
            NFO_str = 'NFO found' if NFO_FileName.exists() else 'NFO not found'
            plot_str = text_limit_string(collection['m_plot'], PLOT_STR_MAXSIZE)
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Edit Category Metadata',
                                  ["Edit Title: '{0}'".format(collection['m_name']),
                                   "Edit Genre: '{0}'".format(collection['m_genre']),
                                   "Edit Rating: '{0}'".format(collection['m_rating']),
                                   "Edit Plot: '{0}'".format(plot_str),
                                   'Import NFO file (default, {0})'.format(NFO_str),
                                   'Import NFO file (browse NFO file) ...',
                                   'Save NFO file (default location)'])
            if type2 < 0: return

            # --- Edition of the collection name ---
            if type2 == 0:
                keyboard = xbmc.Keyboard(collection['m_name'], 'Edit Title')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                title = keyboard.getText()
                if title == '': title = collection['m_name']
                collection['m_name'] = title.rstrip()
                kodi_notify('Changed Collection Title')

            # --- Edition of the collection genre ---
            elif type2 == 1:
                keyboard = xbmc.Keyboard(collection['m_genre'], 'Edit Genre')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                collection['m_genre'] = keyboard.getText()
                kodi_notify('Changed Collection Genre')

            # --- Edition of the collection rating ---
            elif type2 == 2:
                rating = dialog.select('Edit Collection Rating',
                                      ['Not set',  'Rating 0', 'Rating 1', 'Rating 2', 'Rating 3', 'Rating 4',
                                       'Rating 5', 'Rating 6', 'Rating 7', 'Rating 8', 'Rating 9', 'Rating 10'])
                # >> Rating not set, empty string
                if rating == 0:
                    collection['m_rating'] = ''
                elif rating >= 1 and rating <= 11:
                    collection['m_rating'] = '{0}'.format(rating - 1)
                elif rating < 0:
                    kodi_dialog_OK("Collection rating '{0}' not changed".format(collection['m_rating']))
                    return

            # --- Edition of the plot (description) ---
            elif type2 == 3:
                keyboard = xbmc.Keyboard(collection['m_plot'], 'Edit Plot')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                collection['m_plot'] = keyboard.getText()
                kodi_notify('Changed Collection Plot')

            # --- Import collection metadata from NFO file (automatic) ---
            elif type2 == 4:
                # >> Returns True if changes were made
                NFO_FileName = fs_get_collection_NFO_name(self.settings, collection)
                if not fs_import_collection_NFO(NFO_FileName, collections, launcherID): return
                kodi_notify('Imported Collection NFO file {0}'.format(NFO_FileName.getPath()))

            # --- Browse for collection NFO file ---
            elif type2 == 5:
                NFO_file = xbmcgui.Dialog().browse(1, 'Select NFO description file', 'files', '.nfo', False, False)
                log_debug('_command_edit_category() Dialog().browse returned "{0}"'.format(NFO_file))
                if not NFO_file: return
                NFO_FileName = FileName(NFO_file)
                if not NFO_FileName.exists(): return
                # >> Returns True if changes were made
                if not fs_import_collection_NFO(NFO_FileName, collections, launcherID): return
                kodi_notify('Imported Collection NFO file {0}'.format(NFO_FileName.getPath()))

            # --- Export collection metadata to NFO file ---
            elif type2 == 6:
                NFO_FileName = fs_get_collection_NFO_name(self.settings, collection)
                # >> Returns False if exception happened. If an Exception happened function notifies
                # >> user, so display nothing to not overwrite error notification.
                if not fs_export_collection_NFO(NFO_FileName, collection): return
                # >> No need to save categories/launchers
                kodi_notify('Exported Collection NFO file {0}'.format(NFO_FileName.getPath()))
                return

        # --- Edit artwork ---
        elif type == 1:
            # >> Create label2 and image ListItem fields
            label2_icon      = collection['s_icon']      if collection['s_icon']      else 'Not set'
            label2_fanart    = collection['s_fanart']    if collection['s_fanart']    else 'Not set'
            label2_banner    = collection['s_banner']    if collection['s_banner']    else 'Not set'
            label2_poster    = collection['s_poster']    if collection['s_poster']    else 'Not set'
            label2_clearlogo = collection['s_clearlogo'] if collection['s_clearlogo'] else 'Not set'
            label2_trailer   = collection['s_trailer']   if collection['s_trailer']   else 'Not set'
            img_icon         = collection['s_icon']      if collection['s_icon']      else 'DefaultAddonNone.png'
            img_fanart       = collection['s_fanart']    if collection['s_fanart']    else 'DefaultAddonNone.png'
            img_banner       = collection['s_banner']    if collection['s_banner']    else 'DefaultAddonNone.png'
            img_poster       = collection['s_poster']    if collection['s_poster']    else 'DefaultAddonNone.png'
            img_clearlogo    = collection['s_clearlogo'] if collection['s_clearlogo'] else 'DefaultAddonNone.png'
            img_trailer      = 'DefaultAddonVideo.png'   if collection['s_trailer']   else 'DefaultAddonNone.png'

            # >> Create ListItem objects for select dialog
            icon_listitem      = xbmcgui.ListItem(label = 'Edit Icon ...',      label2 = label2_icon)
            fanart_listitem    = xbmcgui.ListItem(label = 'Edit Fanart ...',    label2 = label2_fanart)
            banner_listitem    = xbmcgui.ListItem(label = 'Edit Banner ...',    label2 = label2_banner)
            poster_listitem    = xbmcgui.ListItem(label = 'Edit Poster ...',    label2 = label2_poster)
            clearlogo_listitem = xbmcgui.ListItem(label = 'Edit Clearlogo ...', label2 = label2_clearlogo)
            trailer_listitem   = xbmcgui.ListItem(label = 'Edit Trailer ...',   label2 = label2_trailer)
            icon_listitem.setArt({'icon' : img_icon})
            fanart_listitem.setArt({'icon' : img_fanart})
            banner_listitem.setArt({'icon' : img_banner})
            poster_listitem.setArt({'icon' : img_poster})
            clearlogo_listitem.setArt({'icon' : img_clearlogo})
            trailer_listitem.setArt({'icon' : img_trailer})

            # >> Execute select dialog
            listitems = [icon_listitem, fanart_listitem, banner_listitem, poster_listitem,
                         clearlogo_listitem, trailer_listitem]
            type2 = dialog.select('Edit Collection Assets/Artwork', list = listitems, useDetails = True)
            if type2 < 0: return
            asset_list = [ASSET_ICON_ID, ASSET_FANART_ID, ASSET_BANNER_ID, ASSET_POSTER_ID, ASSET_CLEARLOGO_ID, ASSET_TRAILER_ID]
            asset_kind = asset_list[type2]
            if not self._gui_edit_asset(KIND_COLLECTION, asset_kind, collection): return

        # --- Choose default Collection assets/artwork ---
        elif type == 2:
            # >> Label1 an label2
            asset_icon_str      = assets_get_asset_name_str(collection['default_icon'])
            asset_fanart_str    = assets_get_asset_name_str(collection['default_fanart'])
            asset_banner_str    = assets_get_asset_name_str(collection['default_banner'])
            asset_poster_str    = assets_get_asset_name_str(collection['default_poster'])
            asset_clearlogo_str = assets_get_asset_name_str(collection['default_clearlogo'])
            label2_icon         = collection[collection['default_icon']]      if collection[collection['default_icon']]      else 'Not set'
            label2_fanart       = collection[collection['default_fanart']]    if collection[collection['default_fanart']]    else 'Not set'
            label2_banner       = collection[collection['default_banner']]    if collection[collection['default_banner']]    else 'Not set'
            label2_poster       = collection[collection['default_poster']]    if collection[collection['default_poster']]    else 'Not set'
            label2_clearlogo    = collection[collection['default_clearlogo']] if collection[collection['default_clearlogo']] else 'Not set'
            icon_listitem       = xbmcgui.ListItem(label = 'Choose asset for Icon (currently {0})'.format(asset_icon_str),
                                                   label2 = label2_icon)
            fanart_listitem     = xbmcgui.ListItem(label = 'Choose asset for Fanart (currently {0})'.format(asset_fanart_str),
                                                   label2 = label2_fanart)
            banner_listitem     = xbmcgui.ListItem(label = 'Choose asset for Banner (currently {0})'.format(asset_banner_str),
                                                   label2 = label2_banner)
            poster_listitem     = xbmcgui.ListItem(label = 'Choose asset for Poster (currently {0})'.format(asset_poster_str),
                                                   label2 = label2_poster)
            clearlogo_listitem  = xbmcgui.ListItem(label = 'Choose asset for Clearlogo (currently {0})'.format(asset_clearlogo_str),
                                                   label2 = label2_clearlogo)

            # >> Asset image
            img_icon            = collection[collection['default_icon']]      if collection[collection['default_icon']]      else 'DefaultAddonNone.png'
            img_fanart          = collection[collection['default_fanart']]    if collection[collection['default_fanart']]    else 'DefaultAddonNone.png'
            img_banner          = collection[collection['default_banner']]    if collection[collection['default_banner']]    else 'DefaultAddonNone.png'
            img_poster          = collection[collection['default_poster']]    if collection[collection['default_poster']]    else 'DefaultAddonNone.png'
            img_clearlogo       = collection[collection['default_clearlogo']] if collection[collection['default_clearlogo']] else 'DefaultAddonNone.png'
            icon_listitem.setArt({'icon' : img_icon})
            fanart_listitem.setArt({'icon' : img_fanart})
            banner_listitem.setArt({'icon' : img_banner})
            poster_listitem.setArt({'icon' : img_poster})
            clearlogo_listitem.setArt({'icon' : img_clearlogo})

            # >> Execute select dialog
            listitems = [icon_listitem, fanart_listitem, banner_listitem, poster_listitem, clearlogo_listitem]
            type2 = dialog.select('Edit Collection default Assets/Artwork', list = listitems, useDetails = True)
            if type2 < 0: return

            # >> Build ListItem of assets that can be mapped.
            Category_ListItem_list = [
                xbmcgui.ListItem(label = 'Icon',      label2 = collection['s_icon'] if collection['s_icon'] else 'Not set'),
                xbmcgui.ListItem(label = 'Fanart',    label2 = collection['s_fanart'] if collection['s_fanart'] else 'Not set'),
                xbmcgui.ListItem(label = 'Banner',    label2 = collection['s_banner'] if collection['s_banner'] else 'Not set'),
                xbmcgui.ListItem(label = 'Poster',    label2 = collection['s_poster'] if collection['s_poster'] else 'Not set'),
                xbmcgui.ListItem(label = 'Clearlogo', label2 = collection['s_clearlogo'] if collection['s_clearlogo'] else 'Not set'),
            ]
            Category_ListItem_list[0].setArt({'icon' : collection['s_icon'] if collection['s_icon'] else 'DefaultAddonNone.png'})
            Category_ListItem_list[1].setArt({'icon' : collection['s_fanart'] if collection['s_fanart'] else 'DefaultAddonNone.png'})
            Category_ListItem_list[2].setArt({'icon' : collection['s_banner'] if collection['s_banner'] else 'DefaultAddonNone.png'})
            Category_ListItem_list[3].setArt({'icon' : collection['s_poster'] if collection['s_poster'] else 'DefaultAddonNone.png'})
            Category_ListItem_list[4].setArt({'icon' : collection['s_clearlogo'] if collection['s_clearlogo'] else 'DefaultAddonNone.png'})

            # >> Krypton feature: User preselected item in select() dialog.
            if type2 == 0:
                p_idx = assets_get_Category_mapped_asset_idx(collection, 'default_icon')
                type_s = dialog.select('Choose Collection default asset for Icon',
                                       list = Category_ListItem_list, useDetails = True, preselect = p_idx)
                if type_s < 0: return
                assets_choose_Category_mapped_artwork(collection, 'default_icon', type_s)
                asset_name = assets_get_asset_name_str(collection['default_icon'])
                kodi_notify('ROM Collection Icon mapped to {0}'.format(asset_name))
            elif type2 == 1:
                p_idx = assets_get_Category_mapped_asset_idx(collection, 'default_fanart')
                type_s = dialog.select('Choose Collection default asset for Fanart',
                                       list = Category_ListItem_list, useDetails = True, preselect = p_idx)
                if type_s < 0: return
                assets_choose_Category_mapped_artwork(collection, 'default_fanart', type_s)
                asset_name = assets_get_asset_name_str(collection['default_fanart'])
                kodi_notify('ROM Collection Fanart mapped to {0}'.format(asset_name))
            elif type2 == 2:
                p_idx = assets_get_Category_mapped_asset_idx(collection, 'default_banner')
                type_s = dialog.select('Choose Collection default asset for Banner',
                                       list = Category_ListItem_list, useDetails = True, preselect = p_idx)
                if type_s < 0: return
                assets_choose_Category_mapped_artwork(collection, 'default_banner', type_s)
                asset_name = assets_get_asset_name_str(collection['default_banner'])
                kodi_notify('ROM Collection Banner mapped to {0}'.format(asset_name))
            elif type2 == 3:
                p_idx = assets_get_Category_mapped_asset_idx(collection, 'default_poster')
                type_s = dialog.select('Choose Collection default asset for Poster',
                                       list = Category_ListItem_list, useDetails = True, preselect = p_idx)
                if type_s < 0: return
                assets_choose_Category_mapped_artwork(collection, 'default_poster', type_s)
                asset_name = assets_get_asset_name_str(collection['default_poster'])
                kodi_notify('ROM Collection Poster mapped to {0}'.format(asset_name))
            elif type2 == 4:
                p_idx = assets_get_Category_mapped_asset_idx(collection, 'default_clearlogo')
                type_s = dialog.select('Choose Collection default asset for Clearlogo',
                                       list = Category_ListItem_list, useDetails = True, preselect = p_idx)
                if type_s < 0: return
                assets_choose_Category_mapped_artwork(collection, 'default_clearlogo', type_s)
                asset_name = assets_get_asset_name_str(collection['default_clearlogo'])
                kodi_notify('ROM Collection Clearlogo mapped to {0}'.format(asset_name))

        # --- Save collection index and refresh view ---
        fs_write_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH, collections)
        kodi_refresh_container()

    #
    # Deletes a collection and associated ROMs.
    #
    def _command_delete_collection(self, categoryID, launcherID):
        # --- Load collection index and ROMs ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH)
        collection = collections[launcherID]
        roms_json_file = g_PATHS.COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
        collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)

        # --- Confirm deletion ---
        num_roms = len(collection_rom_list)
        collection_name = collection['m_name']
        ret = kodi_dialog_yesno('Collection "{}" has {} ROMs. '.format(collection_name, num_roms) +
                                'Are you sure you want to delete it?')
        if not ret: return

        # --- Remove JSON file and delete collection object ---
        collection_file_path = g_PATHS.COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
        log_debug('Removing Collection JSON "{}"'.format(collection_file_path.getOriginalPath()))
        try:
            if collection_file_path.exists(): collection_file_path.unlink()
        except OSError:
            log_error('_gui_remove_launcher() (OSError) exception deleting "{}"'.format(collection_file_path.getOriginalPath()))
            kodi_notify_warn('OSError exception deleting collection JSON')
        collections.pop(launcherID)
        fs_write_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH, collections)
        kodi_refresh_container()
        kodi_notify('Deleted ROM Collection "{}"'.format(collection_name))

        # TODO Remove assets in the collections asset directory.

    #
    # Imports a ROM Collection.
    #
    def _command_import_collection(self):
        # --- Choose collection to import ---
        dialog = xbmcgui.Dialog()
        collection_file_str = dialog.browse(1, 'Select the ROM Collection file',
            'files', '.json', False, False)
        if not collection_file_str: return

        # --- Load ROM Collection file ---
        i_collection_FN = FileName(collection_file_str)
        i_control_dic, i_collection, i_rom_list = fs_import_ROM_collection(i_collection_FN)
        if not i_collection:
            kodi_dialog_OK('Error reading Collection JSON file. JSON file corrupted or wrong.')
            return
        if not i_rom_list:
            kodi_dialog_OK('Collection is empty.')
            return
        if i_control_dic['control'] != 'Advanced Emulator Launcher Collection ROMs':
            kodi_dialog_OK('JSON file is not an AEL ROM Collection file.')
            return

        # --- Load collection indices ---
        collections, update_timestamp = fs_load_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH)

        # --- If collectionID already on index warn the user ---
        if i_collection['id'] in collections:
            log_info('_command_import_collection() Collection {} already in AEL'.format(i_collection['m_name']))
            ret = kodi_dialog_yesno('A Collection with same ID exists. Overwrite?')
            if not ret: return

        # --- Regenrate roms_base_noext field ---
        collection_base_name = fs_get_collection_ROMs_basename(i_collection['m_name'], i_collection['id'])
        i_collection['roms_base_noext'] = collection_base_name
        log_debug('_command_import_collection() roms_base_noext "{}"'.format(i_collection['roms_base_noext']))

        # --- Import assets ---
        collections_asset_dir_FN = FileName(self.settings['collections_asset_dir'])

        # --- Import Collection assets ---
        # When importing assets copy them to the Collection assets dir set in AEL addon settings.
        log_info('_command_import_collection() Importing ROM Collection assets ...')
        in_dir_FN = FileName(i_collection_FN.getDir())
        for asset_kind in CATEGORY_ASSET_ID_LIST:
            # Test if assets exists before copy.
            AInfo = assets_get_info_scheme(asset_kind)
            if not i_collection[AInfo.key]:
                log_debug('{:<9s} undefined (empty str)'.format(AInfo.name))
                continue
            in_asset_FN = in_dir_FN.pjoin(i_collection[AInfo.key])
            log_debug('{:<9s} path "{}"'.format(AInfo.name, in_asset_FN.getPath()))
            if not in_asset_FN.exists():
                # Asset not found. Make sure asset is unset in imported Collection.
                i_collection[AInfo.key] = ''
                log_debug('{:<9s} NOT found in imported asset dictionary'.format(AInfo.name))
                continue
            log_debug('{:<9s} found in imported asset dictionary'.format(AInfo.name))

            # Copy Collection asset from input directory to Collections asset directory.
            new_asset_basename = i_collection['m_name'] + '_' + AInfo.fname_infix + in_asset_FN.getExt()
            new_asset_FN = collections_asset_dir_FN.pjoin(new_asset_basename)
            log_debug('{:<9s} COPY "{}"'.format(AInfo.name, in_asset_FN.getPath()))
            log_debug('{:<9s}   TO "{}"'.format(AInfo.name, new_asset_FN.getPath()))
            try:
                source_path = in_asset_FN.getPath().decode(get_fs_encoding(), 'ignore')
                dest_path = new_asset_FN.getPath().decode(get_fs_encoding(), 'ignore')
                shutil.copy(source_path, dest_path)
            except OSError:
                log_error('fs_export_ROM_collection_assets() OSError exception copying image')
                kodi_notify_warn('OSError exception copying image')
                return
            except IOError:
                log_error('fs_export_ROM_collection_assets() IOError exception copying image')
                kodi_notify_warn('IOError exception copying image')
                return

            # Update imported asset filename in database.
            log_debug('{:<9s} collection[{}] is "{}"'.format(
                AInfo.name, AInfo.key, new_asset_FN.getOriginalPath()))
            i_collection[AInfo.key] = new_asset_FN.getOriginalPath()

        # --- Import ROM assets ---
        log_info('_command_import_collection() Importing ROM assets ...')
        for rom in i_rom_list:
            log_debug('_command_import_collection() ROM "{}"'.format(rom['m_name']))
            log_debug('ROM platform "{}"'.format(rom['platform']))
            for asset_kind in ROM_ASSET_ID_LIST:
                # Test if assets exists before copy.
                AInfo = assets_get_info_scheme(asset_kind)
                if not rom[AInfo.key]:
                    log_debug('{:<9s} undefined (empty str)'.format(AInfo.name))
                    continue
                in_asset_FN = in_dir_FN.pjoin(rom[AInfo.key])
                log_debug('{:<9s} path "{}"'.format(AInfo.name, in_asset_FN.getPath()))
                if not in_asset_FN.exists():
                    # Asset not found. Make sure asset is unset in imported Collection.
                    i_collection[AInfo.key] = ''
                    log_debug('{:<9s} NOT found in imported asset dictionary'.format(AInfo.name))
                    continue
                log_debug('{:<9s} found in imported asset dictionary'.format(AInfo.name))

                # Copy ROM Collection asset from input directory to Collections asset directory.
                ROM_FileName = FileName(rom['filename'])
                new_asset_basename = assets_get_collection_asset_basename(
                    AInfo, ROM_FileName.getBase_noext(), rom['platform'], in_asset_FN.getExt())
                new_asset_FN = collections_asset_dir_FN.pjoin(new_asset_basename)
                log_debug('{:<9s} COPY "{}"'.format(AInfo.name, in_asset_FN.getPath()))
                log_debug('{:<9s}   TO "{}"'.format(AInfo.name, new_asset_FN.getPath()))
                try:
                    source_path = in_asset_FN.getPath().decode(get_fs_encoding(), 'ignore')
                    dest_path = new_asset_FN.getPath().decode(get_fs_encoding(), 'ignore')
                    shutil.copy(source_path, dest_path)
                except OSError:
                    log_error('fs_export_ROM_collection_assets() OSError exception copying image')
                    kodi_notify_warn('OSError exception copying image')
                    return
                except IOError:
                    log_error('fs_export_ROM_collection_assets() IOError exception copying image')
                    kodi_notify_warn('IOError exception copying image')
                    return

                # Update asset info in database
                log_debug('{:<9s} rom[{}] is "{}"'.format(
                    AInfo.name, AInfo.key, new_asset_FN.getOriginalPath()))
                rom[AInfo.key] = new_asset_FN.getOriginalPath()
        log_debug('_command_import_collection() Finished importing assets')

        # --- Add imported collection to database ---
        collections[i_collection['id']] = i_collection
        log_info('_command_import_collection() Imported Collection "{}" (id {})'.format(
            i_collection['m_name'], i_collection['id']))

        # --- Write ROM Collection databases ---
        fs_write_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH, collections)
        fs_write_Collection_ROMs_JSON(g_PATHS.COLLECTIONS_DIR.pjoin(
            collection_base_name + '.json'), i_rom_list)
        kodi_dialog_OK('Imported ROM Collection "{}" metadata and assets.'.format(
            i_collection['m_name']))
        kodi_refresh_container()

    #
    # Exports a ROM Collection
    #
    def _command_export_collection(self, categoryID, launcherID):
        collections_asset_dir_FN = FileName(self.settings['collections_asset_dir'])

        # --- Choose output directory ---
        dialog = xbmcgui.Dialog()
        output_dir = dialog.browse(3, 'Select Collection output directory', 'files')
        if not output_dir: return
        out_dir_FN = FileName(output_dir)

        # --- Load collection ROMs ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH)
        collection = collections[launcherID]
        roms_json_file = g_PATHS.COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
        rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
        if not rom_list:
            kodi_notify('Collection is empty. Add ROMs to this collection first.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # --- Export collection metadata and assets ---
        output_FileName = out_dir_FN.pjoin(collection['m_name'] + '.json')
        fs_export_ROM_collection(output_FileName, collection, rom_list)
        fs_export_ROM_collection_assets(out_dir_FN, collection, rom_list, collections_asset_dir_FN)

        # --- User info ---
        kodi_notify('Exported ROM Collection {} metadata and assets.'.format(collection['m_name']))

    def _command_add_ROM_to_collection(self, categoryID, launcherID, romID):
        # ROM in Favourites
        if categoryID == VCATEGORY_FAVOURITES_ID:
            roms = fs_load_Favourites_JSON(g_PATHS.FAV_JSON_FILE_PATH)
            new_collection_rom = roms[romID]
        # ROM in Virtual Launcher
        elif categoryID == VCATEGORY_TITLE_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_TITLE_DIR, launcherID)
            new_collection_rom = roms[romID]
        elif categoryID == VCATEGORY_YEARS_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_YEARS_DIR, launcherID)
            new_collection_rom = roms[romID]
        elif categoryID == VCATEGORY_GENRE_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_GENRE_DIR, launcherID)
            new_collection_rom = roms[romID]
        elif categoryID == VCATEGORY_DEVELOPER_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_DEVELOPER_DIR, launcherID)
            new_collection_rom = roms[romID]
        elif categoryID == VCATEGORY_NPLAYERS_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_NPLAYERS_DIR, launcherID)
            new_collection_rom = roms[romID]
        elif categoryID == VCATEGORY_ESRB_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_ESRB_DIR, launcherID)
            new_collection_rom = roms[romID]
        elif categoryID == VCATEGORY_RATING_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_RATING_DIR, launcherID)
            new_collection_rom = roms[romID]
        elif categoryID == VCATEGORY_CATEGORY_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_CATEGORY_DIR, launcherID)
            new_collection_rom = roms[romID]
        else:
            # >> ROMs in standard launcher
            launcher = self.launchers[launcherID]
            roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, launcher)
            new_collection_rom = fs_get_Favourite_from_ROM(roms[romID], launcher)

        # --- Load Collection index ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH)

        # --- If no collections so long and thanks for all the fish ---
        if not collections:
            kodi_dialog_OK('You have no Collections! Create a collection first before adding ROMs.')
            return

        # --- Ask user which Collection wants to add the ROM to ---
        dialog = xbmcgui.Dialog()
        collections_id = []
        collections_name = []
        for key in sorted(collections, key = lambda x : collections[x]['m_name']):
            collections_id.append(collections[key]['id'])
            collections_name.append(collections[key]['m_name'])
        selected_idx = dialog.select('Select the collection', collections_name)
        if selected_idx < 0: return
        collectionID = collections_id[selected_idx]

        # --- Load Collection ROMs ---
        collection = collections[collectionID]
        roms_json_file = g_PATHS.COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
        collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
        log_info('Adding ROM to Collection')
        log_info('Collection {}'.format(collection['m_name']))
        log_info('     romID {}'.format(romID))
        log_info('ROM m_name {}'.format(roms[romID]['m_name']))

        # >> Check if ROM already in this collection an warn user if so
        rom_already_in_collection = False
        for rom in collection_rom_list:
            if romID == rom['id']:
                rom_already_in_collection = True
                break
        if rom_already_in_collection:
            log_info('ROM already in collection')
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher',
                               'ROM {0} is already on Collection {1}. Overwrite it?'.format(roms[romID]['m_name'], collection['m_name']))
            if not ret:
                log_verb('User does not want to overwrite. Exiting.')
                return
        # >> Confirm if rom should be added
        else:
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher',
                               "ROM '{0}'. Add this ROM to Collection '{1}'?".format(roms[romID]['m_name'], collection['m_name']))
            if not ret:
                log_verb('User does not confirm addition. Exiting.')
                return

        # --- Add ROM to favourites ROMs and save to disk ---
        # >> Add ROM to the last position in the collection
        collection_rom_list.append(new_collection_rom)
        collection_json_FN = g_PATHS.COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
        fs_write_Collection_ROMs_JSON(collection_json_FN, collection_rom_list)
        kodi_refresh_container()
        kodi_notify('Added ROM to Collection "{0}"'.format(collection['m_name']))

    #
    # Search ROMs in launcher
    #
    def _command_search_launcher(self, categoryID, launcherID):
        log_debug('_command_search_launcher() categoryID {0}'.format(categoryID))
        log_debug('_command_search_launcher() launcherID {0}'.format(launcherID))

        # --- Load ROMs ---
        if categoryID == VCATEGORY_FAVOURITES_ID:
            roms = fs_load_Favourites_JSON(g_PATHS.FAV_JSON_FILE_PATH)
        elif categoryID == VCATEGORY_TITLE_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_TITLE_DIR, launcherID)
        elif categoryID == VCATEGORY_YEARS_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_YEARS_DIR, launcherID)
        elif categoryID == VCATEGORY_GENRE_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_GENRE_DIR, launcherID)
        elif categoryID == VCATEGORY_DEVELOPER_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_DEVELOPER_DIR, launcherID)
        elif categoryID == VCATEGORY_CATEGORY_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_CATEGORY_DIR, launcherID)
        else:
            rom_file_path = g_PATHS.ROMS_DIR.pjoin(self.launchers[launcherID]['roms_base_noext'] + '.json')
            log_debug('_command_search_launcher() rom_file_path "{0}"'.format(rom_file_path.getOriginalPath()))
            if not rom_file_path.exists():
                kodi_notify('Launcher JSON not found. Add ROMs to Launcher')
                return
            roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, self.launchers[launcherID])

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
            search_string = keyboard.getText()
            url = self._misc_url_search('EXECUTE_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_TITLE', search_string)

        # --- Search by Release Date ---
        type_nb = type_nb + 1
        if type == type_nb:
            searched_list = self._search_launcher_field('m_year', roms)
            dialog = xbmcgui.Dialog()
            selected_value = dialog.select('Select a release year ...', searched_list)
            if selected_value < 0: return
            search_string = searched_list[selected_value]
            url = self._misc_url_search('EXECUTE_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_YEAR', search_string)

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
            url = self._misc_url_search('EXECUTE_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_GENRE', search_string)

        # --- Search by Studio ---
        type_nb = type_nb + 1
        if type == type_nb:
            searched_list = self._search_launcher_field('m_studio', roms)
            dialog = xbmcgui.Dialog()
            selected_value = dialog.select('Select a Studio ...', searched_list)
            if selected_value < 0: return
            search_string = searched_list[selected_value]
            url = self._misc_url_search('EXECUTE_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_STUDIO', search_string)

        # --- Search by Rating ---
        type_nb = type_nb + 1
        if type == type_nb:
            searched_list = self._search_launcher_field('m_rating', roms)
            dialog = xbmcgui.Dialog()
            selected_value = dialog.select('Select a Rating ...', searched_list)
            if selected_value < 0: return
            search_string = searched_list[selected_value]
            url = self._misc_url_search('EXECUTE_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_RATING', search_string)

        # --- Replace current window by search window ---
        # When user press Back in search window it returns to the original window (either showing
        # launcher in a cateogory or displaying ROMs in a launcher/virtual launcher).
        #
        # NOTE ActivateWindow() / RunPlugin() / RunAddon() seem not to work here
        log_debug('_command_search_launcher() Container.Update URL {0}'.format(url))
        xbmc.executebuiltin('Container.Update({0})'.format(url))

    #
    # Auxiliar function used in Launcher searches.
    #
    def _search_launcher_field(self, search_dic_field, roms):
        # Maybe this can be optimized a bit to make the search faster...
        search = []
        for keyr in sorted(roms.keys()):
            if roms[keyr][search_dic_field] == '':
                search.append('[ Not Set ]')
            else:
                search.append(roms[keyr][search_dic_field])
        # Search may have a lot of repeated entries. Converting them to a set makes them unique.
        search = list(set(search))
        search.sort()

        return search

    def _command_execute_search_launcher(self, categoryID, launcherID, search_type, search_string):
        if   search_type == 'SEARCH_TITLE'  : rom_search_field = 'm_name'
        elif search_type == 'SEARCH_YEAR'   : rom_search_field = 'm_year'
        elif search_type == 'SEARCH_STUDIO' : rom_search_field = 'm_studio'
        elif search_type == 'SEARCH_GENRE'  : rom_search_field = 'm_genre'
        elif search_type == 'SEARCH_RATING' : rom_search_field = 'm_rating'
        else: return

        # --- Load Launcher ROMs ---
        if categoryID == VCATEGORY_FAVOURITES_ID:
            roms = fs_load_Favourites_JSON(g_PATHS.FAV_JSON_FILE_PATH)
        elif categoryID == VCATEGORY_TITLE_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_TITLE_DIR, launcherID)
        elif categoryID == VCATEGORY_YEARS_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_YEARS_DIR, launcherID)
        elif categoryID == VCATEGORY_GENRE_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_GENRE_DIR, launcherID)
        elif categoryID == VCATEGORY_DEVELOPER_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_DEVELOPER_DIR, launcherID)
        elif categoryID == VCATEGORY_CATEGORY_ID:
            roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_CATEGORY_DIR, launcherID)
        else:
            rom_file_path = g_PATHS.ROMS_DIR.pjoin(self.launchers[launcherID]['roms_base_noext'] + '.json')
            if not rom_file_path.exists():
                kodi_notify('Launcher JSON not found. Add ROMs to Launcher')
                return
            roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, self.launchers[launcherID])

        # --- Empty ROM dictionary / Loading error ---
        if not roms:
            kodi_notify('Launcher JSON is empty. Add ROMs to Launcher')
            return

        # --- Go through rom list and search for user input ---
        rl = {}
        notset = ('[ Not Set ]')
        text = search_string.lower()
        empty = notset.lower()
        for keyr in roms:
            rom_field_str = roms[keyr][rom_search_field].lower()
            if rom_field_str == '' and text == empty: rl[keyr] = roms[keyr]

            if rom_search_field == 'm_name':
                if not rom_field_str.find(text) == -1:
                    rl[keyr] = roms[keyr]
            else:
                if rom_field_str == text:
                    rl[keyr] = roms[keyr]

        # --- Render ROMs ---
        self._misc_set_all_sorting_methods()
        if not rl:
            kodi_dialog_OK('Search returned no results')
        for key in sorted(rl.keys()):
            self._gui_render_rom_row(categoryID, launcherID, rl[key])
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # View all kinds of information
    #
    def _command_view_menu(self, categoryID, launcherID, romID):
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
            size_stdout = stat_stdout.st_size
            STD_status = '{0} bytes'.format(size_stdout)
        else:
            STD_status = 'not found'
        if view_type == VIEW_LAUNCHER or view_type == VIEW_ROM_LAUNCHER:
            launcher = self.launchers[launcherID]
            launcher_report_FN = g_PATHS.REPORTS_DIR.pjoin(launcher['roms_base_noext'] + '_report.txt')
            if launcher_report_FN.exists():
                stat_stdout = launcher_report_FN.stat()
                size_stdout = stat_stdout.st_size
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
                'View ROM data',
                'View ROM manual',
                'View ROM map',
                'View Launcher statistics',
                'View Launcher metadata/audit report',
                'View Launcher assets report',
                'View Launcher scanner report ({0})'.format(Report_status),
                'View last execution output ({0})'.format(STD_status),
            ]
        elif view_type == VIEW_ROM_VLAUNCHER:
            # >> ROM in Favourites or Virtual Launcher (no launcher report)
            d_list = [
                'View ROM data',
                'View ROM manual',
                'View ROM map',
                'View last execution output ({0})'.format(STD_status),
            ]
        elif view_type == VIEW_ROM_COLLECTION:
            d_list = [
                'View ROM data',
                'View ROM manual',
                'View ROM map',
                'View last execution output ({0})'.format(STD_status),
            ]
        else:
            kodi_dialog_OK(
                'Wrong view_type = {0}. This is a bug, please report it.'.format(view_type))
            return
        selected_value = xbmcgui.Dialog().select('View', d_list)
        if selected_value < 0: return

        # --- Polymorphic menu. Determine action to do. ---
        if view_type == VIEW_CATEGORY:
            if   selected_value == 0: action = ACTION_VIEW_CATEGORY
            elif selected_value == 1: action = ACTION_VIEW_EXEC_OUTPUT
            else:
                kodi_dialog_OK(
                    'view_type == VIEW_CATEGORY and selected_value = {0}. '.format(selected_value) +
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
                kodi_dialog_OK(
                    'view_type == VIEW_LAUNCHER and selected_value = {0}. '.format(selected_value) +
                    'This is a bug, please report it.')
                return
        elif view_type == VIEW_COLLECTION:
            if   selected_value == 0: action = ACTION_VIEW_COLLECTION
            elif selected_value == 1: action = ACTION_VIEW_EXEC_OUTPUT
            else:
                kodi_dialog_OK(
                    'view_type == VIEW_COLLECTION and selected_value = {0}. '.format(selected_value) +
                    'This is a bug, please report it.')
                return
        elif view_type == VIEW_ROM_LAUNCHER:
            if   selected_value == 0: action = ACTION_VIEW_ROM
            elif selected_value == 1: action = ACTION_VIEW_MANUAL
            elif selected_value == 2: action = ACTION_VIEW_MAP
            elif selected_value == 3: action = ACTION_VIEW_LAUNCHER_STATS
            elif selected_value == 4: action = ACTION_VIEW_LAUNCHER_METADATA
            elif selected_value == 5: action = ACTION_VIEW_LAUNCHER_ASSETS
            elif selected_value == 6: action = ACTION_VIEW_LAUNCHER_SCANNER
            elif selected_value == 7: action = ACTION_VIEW_EXEC_OUTPUT
            else:
                kodi_dialog_OK(
                    'view_type == VIEW_ROM_LAUNCHER and selected_value = {0}. '.format(selected_value) +
                    'This is a bug, please report it.')
                return
        elif view_type == VIEW_ROM_VLAUNCHER:
            if   selected_value == 0: action = ACTION_VIEW_ROM
            elif selected_value == 1: action = ACTION_VIEW_MANUAL
            elif selected_value == 2: action = ACTION_VIEW_MAP
            elif selected_value == 3: action = ACTION_VIEW_EXEC_OUTPUT
            else:
                kodi_dialog_OK(
                    'view_type == VIEW_ROM_VLAUNCHER and selected_value = {0}. '.format(selected_value) +
                    'This is a bug, please report it.')
                return
        elif view_type == VIEW_ROM_COLLECTION:
            if   selected_value == 2: action = ACTION_VIEW_ROM
            elif selected_value == 0: action = ACTION_VIEW_MANUAL
            elif selected_value == 1: action = ACTION_VIEW_MAP
            elif selected_value == 3: action = ACTION_VIEW_EXEC_OUTPUT
            else:
                kodi_dialog_OK(
                    'view_type == VIEW_ROM_COLLECTION and selected_value = {0}. '.format(selected_value) +
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
            if view_type == VIEW_CATEGORY:
                window_title = 'Category data'
                category = self.categories[categoryID]
                info_text  = '[COLOR orange]Category information[/COLOR]\n'
                info_text += self._misc_print_string_Category(category)
            elif view_type == VIEW_LAUNCHER:
                window_title = 'Launcher data'
                if categoryID == VCATEGORY_ADDONROOT_ID: category = None
                else:                                    category = self.categories[categoryID]
                launcher = self.launchers[launcherID]
                info_text  = '[COLOR orange]Launcher information[/COLOR]\n'
                info_text += self._misc_print_string_Launcher(launcher)
                if category:
                    info_text += '\n[COLOR orange]Category information[/COLOR]\n'
                    info_text += self._misc_print_string_Category(category)
            elif view_type == VIEW_COLLECTION:
                window_title = 'ROM Collection data'
                (collections, update_timestamp) = fs_load_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH)
                collection = collections[launcherID]
                info_text = '[COLOR orange]ROM Collection information[/COLOR]\n'
                info_text += self._misc_print_string_Collection(collection)
            else:
                # --- Read ROMs ---
                regular_launcher = True
                if categoryID == VCATEGORY_FAVOURITES_ID:
                    log_info('_command_view_menu() Viewing ROM in Favourites ...')
                    roms = fs_load_Favourites_JSON(g_PATHS.FAV_JSON_FILE_PATH)
                    rom = roms[romID]
                    window_title = 'Favourite ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Favourite'

                elif categoryID == VCATEGORY_MOST_PLAYED_ID:
                    log_info('_command_view_menu() Viewing ROM in Most played ROMs list ...')
                    most_played_roms = fs_load_Favourites_JSON(g_PATHS.MOST_PLAYED_FILE_PATH)
                    rom = most_played_roms[romID]
                    window_title = 'Most Played ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Most Played ROM'

                elif categoryID == VCATEGORY_RECENT_ID:
                    log_info('_command_view_menu() Viewing ROM in Recently played ROMs ...')
                    recent_roms_list = fs_load_Collection_ROMs_JSON(g_PATHS.RECENT_PLAYED_FILE_PATH)
                    current_ROM_position = fs_collection_ROM_index_by_romID(romID, recent_roms_list)
                    if current_ROM_position < 0:
                        kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
                        return
                    rom = recent_roms_list[current_ROM_position]
                    window_title = 'Recently played ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Recently played ROM'

                elif categoryID == VCATEGORY_TITLE_ID:
                    log_info('_command_view_menu() Viewing ROM in Title Virtual Launcher ...')
                    hashed_db_filename = g_PATHS.VIRTUAL_CAT_TITLE_DIR.pjoin(launcherID + '.json')
                    if not hashed_db_filename.exists():
                        log_error('_command_view_menu() Cannot find file "{0}"'.format(hashed_db_filename.getPath()))
                        kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
                        return
                    roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_TITLE_DIR, launcherID)
                    rom = roms[romID]
                    window_title = 'Virtual Launcher Title ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Virtual Launcher Title'

                elif categoryID == VCATEGORY_YEARS_ID:
                    log_info('_command_view_menu() Viewing ROM in Year Virtual Launcher ...')
                    hashed_db_filename = g_PATHS.VIRTUAL_CAT_YEARS_DIR.pjoin(launcherID + '.json')
                    if not hashed_db_filename.exists():
                        log_error('_command_view_menu() Cannot find file "{0}"'.format(hashed_db_filename.getPath()))
                        kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
                        return
                    roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_YEARS_DIR, launcherID)
                    rom = roms[romID]
                    window_title = 'Virtual Launcher Year ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Virtual Launcher Year'

                elif categoryID == VCATEGORY_GENRE_ID:
                    log_info('_command_view_menu() Viewing ROM in Genre Virtual Launcher ...')
                    hashed_db_filename = g_PATHS.VIRTUAL_CAT_GENRE_DIR.pjoin(launcherID + '.json')
                    if not hashed_db_filename.exists():
                        log_error('_command_view_menu() Cannot find file "{0}"'.format(hashed_db_filename.getPath()))
                        kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
                        return
                    roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_GENRE_DIR, launcherID)
                    rom = roms[romID]
                    window_title = 'Virtual Launcher Genre ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Virtual Launcher Genre'

                elif categoryID == VCATEGORY_DEVELOPER_ID:
                    log_info('_command_view_menu() Viewing ROM in Developer Virtual Launcher ...')
                    hashed_db_filename = g_PATHS.VIRTUAL_CAT_DEVELOPER_DIR.pjoin(launcherID + '.json')
                    if not hashed_db_filename.exists():
                        log_error('_command_view_menu() Cannot find file "{0}"'.format(hashed_db_filename.getPath()))
                        kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
                        return
                    roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_DEVELOPER_DIR, launcherID)
                    rom = roms[romID]
                    window_title = 'Virtual Launcher Studio ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Virtual Launcher Studio'

                elif categoryID == VCATEGORY_NPLAYERS_ID:
                    log_info('_command_view_menu() Viewing ROM in NPlayers Virtual Launcher ...')
                    hashed_db_filename = g_PATHS.VIRTUAL_CAT_NPLAYERS_DIR.pjoin(launcherID + '.json')
                    if not hashed_db_filename.exists():
                        log_error('_command_view_menu() Cannot find file "{0}"'.format(hashed_db_filename.getPath()))
                        kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
                        return
                    roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_NPLAYERS_DIR, launcherID)
                    rom = roms[romID]
                    window_title = 'Virtual Launcher NPlayer ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Virtual Launcher NPlayer'

                elif categoryID == VCATEGORY_ESRB_ID:
                    log_info('_command_view_menu() Viewing ROM in ESRB Launcher ...')
                    hashed_db_filename = g_PATHS.VIRTUAL_CAT_ESRB_DIR.pjoin(launcherID + '.json')
                    if not hashed_db_filename.exists():
                        log_error('_command_view_menu() Cannot find file "{0}"'.format(hashed_db_filename.getPath()))
                        kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
                        return
                    roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_ESRB_DIR, launcherID)
                    rom = roms[romID]
                    window_title = 'Virtual Launcher ESRB ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Virtual Launcher ESRB'

                elif categoryID == VCATEGORY_RATING_ID:
                    log_info('_command_view_menu() Viewing ROM in Rating Launcher ...')
                    hashed_db_filename = g_PATHS.VIRTUAL_CAT_RATING_DIR.pjoin(launcherID + '.json')
                    if not hashed_db_filename.exists():
                        log_error('_command_view_menu() Cannot find file "{0}"'.format(hashed_db_filename.getPath()))
                        kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
                        return
                    roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_RATING_DIR, launcherID)
                    rom = roms[romID]
                    window_title = 'Virtual Launcher Rating ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Virtual Launcher Rating'

                elif categoryID == VCATEGORY_CATEGORY_ID:
                    log_info('_command_view_menu() Viewing ROM in Category Virtual Launcher ...')
                    hashed_db_filename = g_PATHS.VIRTUAL_CAT_CATEGORY_DIR.pjoin(launcherID + '.json')
                    if not hashed_db_filename.exists():
                        log_error('_command_view_menu() Cannot find file "{0}"'.format(hashed_db_filename.getPath()))
                        kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
                        return
                    roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_CATEGORY_DIR, launcherID)
                    rom = roms[romID]
                    window_title = 'Virtual Launcher Category ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Virtual Launcher Category'

                # --- ROM in Collection ---
                elif categoryID == VCATEGORY_COLLECTIONS_ID:
                    log_info('_command_view_menu() Viewing ROM in Collection ...')
                    (collections, update_timestamp) = fs_load_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH)
                    collection = collections[launcherID]
                    roms_json_file = g_PATHS.COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
                    collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
                    current_ROM_position = fs_collection_ROM_index_by_romID(romID, collection_rom_list)
                    if current_ROM_position < 0:
                        kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
                        return
                    rom = collection_rom_list[current_ROM_position]
                    window_title = '{0} Collection ROM data'.format(collection['m_name'])
                    regular_launcher = False
                    vlauncher_label = 'Collection'

                # --- ROM in regular launcher ---
                else:
                    log_info('_command_view_menu() Viewing ROM in Launcher ...')
                    if romID == UNKNOWN_ROMS_PARENT_ID:
                        kodi_dialog_OK('You cannot view this ROM!')
                        return
                    # >> Check launcher is OK
                    if launcherID not in self.launchers:
                        kodi_dialog_OK('launcherID not found in self.launchers')
                        return
                    launcher_in_category = False if categoryID == VCATEGORY_ADDONROOT_ID else True
                    if launcher_in_category: category = self.categories[categoryID]
                    launcher = self.launchers[launcherID]
                    roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, launcher)
                    rom = roms[romID]
                    window_title = 'Launcher ROM data'

                # --- Make information string ---
                info_text  = '[COLOR orange]ROM information[/COLOR]\n'
                info_text += self._misc_print_string_ROM(rom)

                # --- Display category/launcher information ---
                if regular_launcher:
                    info_text += '\n[COLOR orange]Launcher information[/COLOR]\n'
                    info_text += self._misc_print_string_Launcher(launcher)
                    info_text += '\n[COLOR orange]Category information[/COLOR]\n'
                    if launcher_in_category:
                        info_text += self._misc_print_string_Category(category)
                    else:
                        info_text += 'No Category (Launcher in addon root)'
                else:
                    info_text += '\n[COLOR orange]{0} ROM additional information[/COLOR]\n'.format(vlauncher_label)
                    info_text += self._misc_print_string_ROM_additional(rom)

            # --- Show information window ---
            log_debug('Setting Window(10000) Property "FontWidth" = "monospaced"')
            xbmcgui.Window(10000).setProperty('FontWidth', 'monospaced')
            dialog = xbmcgui.Dialog()
            dialog.textviewer(window_title, info_text)
            log_debug('Setting Window(10000) Property "FontWidth" = "proportional"')
            xbmcgui.Window(10000).setProperty('FontWidth', 'proportional')

        # --- Launcher statistical reports ---
        elif action == ACTION_VIEW_LAUNCHER_STATS or \
             action == ACTION_VIEW_LAUNCHER_METADATA or \
             action == ACTION_VIEW_LAUNCHER_ASSETS:
            # --- Standalone launchers do not have reports! ---
            if categoryID in self.categories: category_name = self.categories[categoryID]['m_name']
            else:                             category_name = VCATEGORY_ADDONROOT_ID
            launcher = self.launchers[launcherID]
            if not launcher['rompath']:
                kodi_notify_warn('Cannot create report for standalone launcher')
                return
            # --- If no ROMs in launcher do nothing ---
            launcher = self.launchers[launcherID]
            roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, launcher)
            if not roms:
                kodi_notify_warn('No ROMs in launcher. Report not created')
                return
            # --- Regenerate reports if don't exist or are outdated ---
            self._roms_regenerate_launcher_reports(categoryID, launcherID, roms)

            # --- Get report filename ---
            roms_base_noext  = fs_get_ROMs_basename(category_name, launcher['m_name'], launcherID)
            report_stats_FN  = g_PATHS.REPORTS_DIR.pjoin(roms_base_noext + '_stats.txt')
            report_meta_FN   = g_PATHS.REPORTS_DIR.pjoin(roms_base_noext + '_metadata.txt')
            report_assets_FN = g_PATHS.REPORTS_DIR.pjoin(roms_base_noext + '_assets.txt')
            log_verb('_command_view_menu() Stats  OP "{0}"'.format(report_stats_FN.getOriginalPath()))
            log_verb('_command_view_menu() Meta   OP "{0}"'.format(report_meta_FN.getOriginalPath()))
            log_verb('_command_view_menu() Assets OP "{0}"'.format(report_assets_FN.getOriginalPath()))

            # --- Read report file ---
            try:
                if action == ACTION_VIEW_LAUNCHER_STATS:
                    window_title = 'Launcher "{0}" Statistics Report'.format(launcher['m_name'])
                    file = open(report_stats_FN.getPath(), 'r')
                    info_text = file.read()
                    file.close()
                elif action == ACTION_VIEW_LAUNCHER_METADATA:
                    window_title = 'Launcher "{0}" Metadata Report'.format(launcher['m_name'])
                    file = open(report_meta_FN.getPath(), 'r')
                    info_text = file.read()
                    file.close()
                elif action == ACTION_VIEW_LAUNCHER_ASSETS:
                    window_title = 'Launcher "{0}" Asset Report'.format(launcher['m_name'])
                    file = open(report_assets_FN.getPath(), 'r')
                    info_text = file.read()
                    file.close()
            except IOError:
                log_error('_command_view_menu() (IOError) Exception reading report TXT file')
                window_title = 'Error'
                info_text = '[COLOR red]Exception reading report TXT file.[/COLOR]'
            info_text = info_text.replace('<No-Intro Audit Statistics>', '[COLOR orange]<No-Intro Audit Statistics>[/COLOR]')
            info_text = info_text.replace('<Metadata statistics>', '[COLOR orange]<Metadata statistics>[/COLOR]')
            info_text = info_text.replace('<Asset statistics>', '[COLOR orange]<Asset statistics>[/COLOR]')

            # --- Show information window ---
            log_debug('Setting Window(10000) Property "FontWidth" = "monospaced"')
            xbmcgui.Window(10000).setProperty('FontWidth', 'monospaced')
            dialog = xbmcgui.Dialog()
            dialog.textviewer(window_title, info_text)
            log_debug('Setting Window(10000) Property "FontWidth" = "proportional"')
            xbmcgui.Window(10000).setProperty('FontWidth', 'proportional')

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
            log_debug('Setting Window(10000) Property "FontWidth" = "monospaced"')
            xbmcgui.Window(10000).setProperty('FontWidth', 'monospaced')
            dialog = xbmcgui.Dialog()
            dialog.textviewer(window_title, info_text)
            log_debug('Setting Window(10000) Property "FontWidth" = "proportional"')
            xbmcgui.Window(10000).setProperty('FontWidth', 'proportional')

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
                roms = fs_load_Favourites_JSON(g_PATHS.FAV_JSON_FILE_PATH)
                rom = roms[romID]
            elif categoryID == VCATEGORY_MOST_PLAYED_ID:
                most_played_roms = fs_load_Favourites_JSON(g_PATHS.MOST_PLAYED_FILE_PATH)
                rom = most_played_roms[romID]
            elif categoryID == VCATEGORY_RECENT_ID:
                recent_roms_list = fs_load_Collection_ROMs_JSON(g_PATHS.RECENT_PLAYED_FILE_PATH)
                current_ROM_position = fs_collection_ROM_index_by_romID(romID, recent_roms_list)
                if current_ROM_position < 0:
                    kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
                    return
                rom = recent_roms_list[current_ROM_position]
            elif categoryID == VCATEGORY_COLLECTIONS_ID:
                (collections, update_timestamp) = fs_load_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH)
                collection = collections[launcherID]
                roms_json_file = g_PATHS.COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
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
                launcher = self.launchers[launcherID]
                roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, launcher)
                rom = roms[romID]

            # >> Show map image
            s_map = rom['s_map']
            if not s_map:
                kodi_dialog_OK('Map image file not set for ROM "{0}"'.format(rom['m_name']))
                return
            map_FN = FileName(s_map)
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
            with open(g_PATHS.LAUNCH_LOG_FILE_PATH.getPath(), 'r') as myfile:
                log_debug('_command_view_menu() Reading launcher.log ...')
                info_text = myfile.read()

            # --- Show information window ---
            window_title = 'Launcher last execution stdout'
            log_debug('Setting Window(10000) Property "FontWidth" = "monospaced"')
            xbmcgui.Window(10000).setProperty('FontWidth', 'monospaced')
            xbmcgui.Dialog().textviewer(window_title, info_text)
            log_debug('Setting Window(10000) Property "FontWidth" = "proportional"')
            xbmcgui.Window(10000).setProperty('FontWidth', 'proportional')

        else:
            kodi_dialog_OK('Wrong action == {0}. This is a bug, please report it.'.format(action))

    def _misc_print_string_ROM(self, rom):
        info_text  = ''
        info_text += "[COLOR violet]id[/COLOR]: '{0}'\n".format(rom['id'])
        # >> Metadata
        info_text += "[COLOR violet]m_name[/COLOR]: '{0}'\n".format(rom['m_name'])
        info_text += "[COLOR violet]m_year[/COLOR]: '{0}'\n".format(rom['m_year'])
        info_text += "[COLOR violet]m_genre[/COLOR]: '{0}'\n".format(rom['m_genre'])
        info_text += "[COLOR violet]m_developer[/COLOR]: '{0}'\n".format(rom['m_developer'])
        info_text += "[COLOR violet]m_nplayers[/COLOR]: '{0}'\n".format(rom['m_nplayers'])
        info_text += "[COLOR violet]m_esrb[/COLOR]: '{0}'\n".format(rom['m_esrb'])
        info_text += "[COLOR violet]m_rating[/COLOR]: '{0}'\n".format(rom['m_rating'])
        info_text += "[COLOR violet]m_plot[/COLOR]: '{0}'\n".format(rom['m_plot'])
        # >> Info
        info_text += "[COLOR violet]filename[/COLOR]: '{0}'\n".format(rom['filename'])
        info_text += "[COLOR skyblue]disks[/COLOR]: {0}\n".format(rom['disks'])
        info_text += "[COLOR violet]altapp[/COLOR]: '{0}'\n".format(rom['altapp'])
        info_text += "[COLOR violet]altarg[/COLOR]: '{0}'\n".format(rom['altarg'])
        info_text += "[COLOR skyblue]finished[/COLOR]: {0}\n".format(rom['finished'])
        info_text += "[COLOR violet]nointro_status[/COLOR]: '{0}'\n".format(rom['nointro_status'])
        info_text += "[COLOR violet]pclone_status[/COLOR]: '{0}'\n".format(rom['pclone_status'])
        info_text += "[COLOR violet]cloneof[/COLOR]: '{0}'\n".format(rom['cloneof'])
        info_text += "[COLOR skyblue]i_extra_ROM[/COLOR]: {0}\n".format(rom['i_extra_ROM'])
        # >> Assets/artwork
        info_text += "[COLOR violet]s_3dbox[/COLOR]: '{0}'\n".format(rom['s_3dbox'])
        info_text += "[COLOR violet]s_title[/COLOR]: '{0}'\n".format(rom['s_title'])
        info_text += "[COLOR violet]s_snap[/COLOR]: '{0}'\n".format(rom['s_snap'])
        info_text += "[COLOR violet]s_boxfront[/COLOR]: '{0}'\n".format(rom['s_boxfront'])
        info_text += "[COLOR violet]s_boxback[/COLOR]: '{0}'\n".format(rom['s_boxback'])
        info_text += "[COLOR violet]s_cartridge[/COLOR]: '{0}'\n".format(rom['s_cartridge'])
        info_text += "[COLOR violet]s_fanart[/COLOR]: '{0}'\n".format(rom['s_fanart'])
        info_text += "[COLOR violet]s_banner[/COLOR]: '{0}'\n".format(rom['s_banner'])
        info_text += "[COLOR violet]s_clearlogo[/COLOR]: '{0}'\n".format(rom['s_clearlogo'])
        info_text += "[COLOR violet]s_flyer[/COLOR]: '{0}'\n".format(rom['s_flyer'])
        info_text += "[COLOR violet]s_map[/COLOR]: '{0}'\n".format(rom['s_map'])
        info_text += "[COLOR violet]s_manual[/COLOR]: '{0}'\n".format(rom['s_manual'])
        info_text += "[COLOR violet]s_trailer[/COLOR]: '{0}'\n".format(rom['s_trailer'])

        return info_text

    def _misc_print_string_ROM_additional(self, rom):
        info_text  = ''
        info_text += "[COLOR violet]launcherID[/COLOR]: '{0}'\n".format(rom['launcherID'])
        info_text += "[COLOR violet]platform[/COLOR]: '{0}'\n".format(rom['platform'])
        info_text += "[COLOR violet]application[/COLOR]: '{0}'\n".format(rom['application'])
        info_text += "[COLOR violet]args[/COLOR]: '{0}'\n".format(rom['args'])
        info_text += "[COLOR skyblue]args_extra[/COLOR]: {0}\n".format(rom['args_extra'])
        info_text += "[COLOR violet]rompath[/COLOR]: '{0}'\n".format(rom['rompath'])
        info_text += "[COLOR violet]romext[/COLOR]: '{0}'\n".format(rom['romext'])
        info_text += "[COLOR skyblue]toggle_window[/COLOR]: {0}\n".format(rom['toggle_window'])
        info_text += "[COLOR skyblue]non_blocking[/COLOR]: {0}\n".format(rom['non_blocking'])
        info_text += "[COLOR violet]roms_default_icon[/COLOR]: '{0}'\n".format(rom['roms_default_icon'])
        info_text += "[COLOR violet]roms_default_fanart[/COLOR]: '{0}'\n".format(rom['roms_default_fanart'])
        info_text += "[COLOR violet]roms_default_banner[/COLOR]: '{0}'\n".format(rom['roms_default_banner'])
        info_text += "[COLOR violet]roms_default_poster[/COLOR]: '{0}'\n".format(rom['roms_default_poster'])
        info_text += "[COLOR violet]roms_default_clearlogo[/COLOR]: '{0}'\n".format(rom['roms_default_clearlogo'])

        # >> Favourite ROMs unique fields.
        info_text += "[COLOR violet]fav_status[/COLOR]: '{0}'\n".format(rom['fav_status'])
        # >> 'launch_count' only in Favourite ROMs in "Most played ROMs"
        if 'launch_count' in rom:
            info_text += "[COLOR skyblue]launch_count[/COLOR]: {0}\n".format(rom['launch_count'])

        return info_text

    def _misc_print_string_Launcher(self, launcher):
        info_text  = ''
        info_text += "[COLOR violet]id[/COLOR]: '{0}'\n".format(launcher['id'])
        info_text += "[COLOR violet]m_name[/COLOR]: '{0}'\n".format(launcher['m_name'])
        info_text += "[COLOR violet]m_year[/COLOR]: '{0}'\n".format(launcher['m_year'])
        info_text += "[COLOR violet]m_genre[/COLOR]: '{0}'\n".format(launcher['m_genre'])
        info_text += "[COLOR violet]m_developer[/COLOR]: '{0}'\n".format(launcher['m_developer'])
        info_text += "[COLOR violet]m_rating[/COLOR]: '{0}'\n".format(launcher['m_rating'])
        info_text += "[COLOR violet]m_plot[/COLOR]: '{0}'\n".format(launcher['m_plot'])

        info_text += "[COLOR violet]platform[/COLOR]: '{0}'\n".format(launcher['platform'])
        info_text += "[COLOR violet]categoryID[/COLOR]: '{0}'\n".format(launcher['categoryID'])
        info_text += "[COLOR violet]application[/COLOR]: '{0}'\n".format(launcher['application'])
        info_text += "[COLOR violet]args[/COLOR]: '{0}'\n".format(launcher['args'])
        info_text += "[COLOR skyblue]args_extra[/COLOR]: {0}\n".format(launcher['args_extra'])
        info_text += "[COLOR violet]rompath[/COLOR]: '{0}'\n".format(launcher['rompath'])
        info_text += "[COLOR violet]romextrapath[/COLOR]: '{0}'\n".format(launcher['romextrapath'])
        info_text += "[COLOR violet]romext[/COLOR]: '{0}'\n".format(launcher['romext'])
        # Bool settings
        info_text += "[COLOR skyblue]finished[/COLOR]: {0}\n".format(launcher['finished'])
        info_text += "[COLOR skyblue]toggle_window[/COLOR]: {0}\n".format(launcher['toggle_window'])
        info_text += "[COLOR skyblue]non_blocking[/COLOR]: {0}\n".format(launcher['non_blocking'])
        info_text += "[COLOR skyblue]multidisc[/COLOR]: {0}\n".format(launcher['multidisc'])
        # Strings
        info_text += "[COLOR violet]roms_base_noext[/COLOR]: '{0}'\n".format(launcher['roms_base_noext'])
        info_text += "[COLOR violet]audit_state[/COLOR]: '{0}'\n".format(launcher['audit_state'])
        info_text += "[COLOR violet]audit_auto_dat_file[/COLOR]: '{0}'\n".format(launcher['audit_auto_dat_file'])
        info_text += "[COLOR violet]audit_custom_dat_file[/COLOR]: '{0}'\n".format(launcher['audit_custom_dat_file'])
        info_text += "[COLOR violet]audit_display_mode[/COLOR]: '{0}'\n".format(launcher['audit_display_mode'])
        info_text += "[COLOR violet]launcher_display_mode[/COLOR]: '{0}'\n".format(launcher['launcher_display_mode'])
        # Integers/Floats
        info_text += "[COLOR skyblue]num_roms[/COLOR]: {0}\n".format(launcher['num_roms'])
        info_text += "[COLOR skyblue]num_parents[/COLOR]: {0}\n".format(launcher['num_parents'])
        info_text += "[COLOR skyblue]num_clones[/COLOR]: {0}\n".format(launcher['num_clones'])
        info_text += "[COLOR skyblue]num_have[/COLOR]: {0}\n".format(launcher['num_have'])
        info_text += "[COLOR skyblue]num_miss[/COLOR]: {0}\n".format(launcher['num_miss'])
        info_text += "[COLOR skyblue]num_unknown[/COLOR]: {0}\n".format(launcher['num_unknown'])
        info_text += "[COLOR skyblue]num_extra[/COLOR]: {0}\n".format(launcher['num_extra'])
        info_text += "[COLOR skyblue]timestamp_launcher[/COLOR]: {0}\n".format(launcher['timestamp_launcher'])
        info_text += "[COLOR skyblue]timestamp_report[/COLOR]: {0}\n".format(launcher['timestamp_report'])

        info_text += "[COLOR violet]default_icon[/COLOR]: '{0}'\n".format(launcher['default_icon'])
        info_text += "[COLOR violet]default_fanart[/COLOR]: '{0}'\n".format(launcher['default_fanart'])
        info_text += "[COLOR violet]default_banner[/COLOR]: '{0}'\n".format(launcher['default_banner'])
        info_text += "[COLOR violet]default_poster[/COLOR]: '{0}'\n".format(launcher['default_poster'])
        info_text += "[COLOR violet]default_clearlogo[/COLOR]: '{0}'\n".format(launcher['default_clearlogo'])
        info_text += "[COLOR violet]default_controller[/COLOR]: '{0}'\n".format(launcher['default_controller'])
        info_text += "[COLOR violet]Asset_Prefix[/COLOR]: '{0}'\n".format(launcher['Asset_Prefix'])
        info_text += "[COLOR violet]s_icon[/COLOR]: '{0}'\n".format(launcher['s_icon'])
        info_text += "[COLOR violet]s_fanart[/COLOR]: '{0}'\n".format(launcher['s_fanart'])
        info_text += "[COLOR violet]s_banner[/COLOR]: '{0}'\n".format(launcher['s_banner'])
        info_text += "[COLOR violet]s_poster[/COLOR]: '{0}'\n".format(launcher['s_poster'])
        info_text += "[COLOR violet]s_clearlogo[/COLOR]: '{0}'\n".format(launcher['s_clearlogo'])
        info_text += "[COLOR violet]s_controller[/COLOR]: '{0}'\n".format(launcher['s_controller'])
        info_text += "[COLOR violet]s_trailer[/COLOR]: '{0}'\n".format(launcher['s_trailer'])

        info_text += "[COLOR violet]roms_default_icon[/COLOR]: '{0}'\n".format(launcher['roms_default_icon'])
        info_text += "[COLOR violet]roms_default_fanart[/COLOR]: '{0}'\n".format(launcher['roms_default_fanart'])
        info_text += "[COLOR violet]roms_default_banner[/COLOR]: '{0}'\n".format(launcher['roms_default_banner'])
        info_text += "[COLOR violet]roms_default_poster[/COLOR]: '{0}'\n".format(launcher['roms_default_poster'])
        info_text += "[COLOR violet]roms_default_clearlogo[/COLOR]: '{0}'\n".format(launcher['roms_default_clearlogo'])
        info_text += "[COLOR violet]ROM_asset_path[/COLOR]: '{0}'\n".format(launcher['ROM_asset_path'])
        info_text += "[COLOR violet]path_3dbox[/COLOR]: '{0}'\n".format(launcher['path_3dbox'])
        info_text += "[COLOR violet]path_title[/COLOR]: '{0}'\n".format(launcher['path_title'])
        info_text += "[COLOR violet]path_snap[/COLOR]: '{0}'\n".format(launcher['path_snap'])
        info_text += "[COLOR violet]path_boxfront[/COLOR]: '{0}'\n".format(launcher['path_boxfront'])
        info_text += "[COLOR violet]path_boxback[/COLOR]: '{0}'\n".format(launcher['path_boxback'])
        info_text += "[COLOR violet]path_cartridge[/COLOR]: '{0}'\n".format(launcher['path_cartridge'])
        info_text += "[COLOR violet]path_fanart[/COLOR]: '{0}'\n".format(launcher['path_fanart'])
        info_text += "[COLOR violet]path_banner[/COLOR]: '{0}'\n".format(launcher['path_banner'])
        info_text += "[COLOR violet]path_clearlogo[/COLOR]: '{0}'\n".format(launcher['path_clearlogo'])
        info_text += "[COLOR violet]path_flyer[/COLOR]: '{0}'\n".format(launcher['path_flyer'])
        info_text += "[COLOR violet]path_map[/COLOR]: '{0}'\n".format(launcher['path_map'])
        info_text += "[COLOR violet]path_manual[/COLOR]: '{0}'\n".format(launcher['path_manual'])
        info_text += "[COLOR violet]path_trailer[/COLOR]: '{0}'\n".format(launcher['path_trailer'])

        return info_text

    def _misc_print_string_Category(self, category):
        info_text  = ''
        info_text += "[COLOR violet]id[/COLOR]: '{0}'\n".format(category['id'])
        info_text += "[COLOR violet]m_name[/COLOR]: '{0}'\n".format(category['m_name'])
        info_text += "[COLOR violet]m_year[/COLOR]: '{0}'\n".format(category['m_year'])
        info_text += "[COLOR violet]m_genre[/COLOR]: '{0}'\n".format(category['m_genre'])
        info_text += "[COLOR violet]m_developer[/COLOR]: '{0}'\n".format(category['m_developer'])
        info_text += "[COLOR violet]m_rating[/COLOR]: '{0}'\n".format(category['m_rating'])
        info_text += "[COLOR violet]m_plot[/COLOR]: '{0}'\n".format(category['m_plot'])
        info_text += "[COLOR skyblue]finished[/COLOR]: {0}\n".format(category['finished'])
        info_text += "[COLOR violet]default_icon[/COLOR]: '{0}'\n".format(category['default_icon'])
        info_text += "[COLOR violet]default_fanart[/COLOR]: '{0}'\n".format(category['default_fanart'])
        info_text += "[COLOR violet]default_banner[/COLOR]: '{0}'\n".format(category['default_banner'])
        info_text += "[COLOR violet]default_poster[/COLOR]: '{0}'\n".format(category['default_poster'])
        info_text += "[COLOR violet]default_clearlogo[/COLOR]: '{0}'\n".format(category['default_clearlogo'])
        info_text += "[COLOR violet]Asset_Prefix[/COLOR]: '{0}'\n".format(category['Asset_Prefix'])
        info_text += "[COLOR violet]s_icon[/COLOR]: '{0}'\n".format(category['s_icon'])
        info_text += "[COLOR violet]s_fanart[/COLOR]: '{0}'\n".format(category['s_fanart'])
        info_text += "[COLOR violet]s_banner[/COLOR]: '{0}'\n".format(category['s_banner'])
        info_text += "[COLOR violet]s_poster[/COLOR]: '{0}'\n".format(category['s_poster'])
        info_text += "[COLOR violet]s_clearlogo[/COLOR]: '{0}'\n".format(category['s_clearlogo'])
        info_text += "[COLOR violet]s_trailer[/COLOR]: '{0}'\n".format(category['s_trailer'])

        return info_text

    def _misc_print_string_Collection(self, collection):
        info_text  = ''
        info_text += "[COLOR violet]id[/COLOR]: '{0}'\n".format(collection['id'])
        info_text += "[COLOR violet]m_name[/COLOR]: '{0}'\n".format(collection['m_name'])
        info_text += "[COLOR violet]m_genre[/COLOR]: '{0}'\n".format(collection['m_genre'])
        info_text += "[COLOR violet]m_rating[/COLOR]: '{0}'\n".format(collection['m_rating'])
        info_text += "[COLOR violet]m_plot[/COLOR]: '{0}'\n".format(collection['m_plot'])
        info_text += "[COLOR violet]roms_base_noext[/COLOR]: {0}\n".format(collection['roms_base_noext'])
        info_text += "[COLOR violet]default_icon[/COLOR]: '{0}'\n".format(collection['default_icon'])
        info_text += "[COLOR violet]default_fanart[/COLOR]: '{0}'\n".format(collection['default_fanart'])
        info_text += "[COLOR violet]default_banner[/COLOR]: '{0}'\n".format(collection['default_banner'])
        info_text += "[COLOR violet]default_poster[/COLOR]: '{0}'\n".format(collection['default_poster'])
        info_text += "[COLOR violet]default_clearlogo[/COLOR]: '{0}'\n".format(collection['default_clearlogo'])
        info_text += "[COLOR violet]s_icon[/COLOR]: '{0}'\n".format(collection['s_icon'])
        info_text += "[COLOR violet]s_fanart[/COLOR]: '{0}'\n".format(collection['s_fanart'])
        info_text += "[COLOR violet]s_banner[/COLOR]: '{0}'\n".format(collection['s_banner'])
        info_text += "[COLOR violet]s_poster[/COLOR]: '{0}'\n".format(collection['s_poster'])
        info_text += "[COLOR violet]s_clearlogo[/COLOR]: '{0}'\n".format(collection['s_clearlogo'])
        info_text += "[COLOR violet]s_trailer[/COLOR]: '{0}'\n".format(collection['s_trailer'])

        return info_text

    def _command_view_offline_scraper_rom(self, scraper, platform, game_name):
        log_debug('_command_view_offline_scraper_rom() scraper   "{}"'.format(scraper))
        log_debug('_command_view_offline_scraper_rom() platform  "{}"'.format(platform))
        log_debug('_command_view_offline_scraper_rom() game_name "{}"'.format(game_name))
        pobj = AEL_platforms[get_AEL_platform_index(platform)]
        if pobj.aliasof:
            log_debug('_command_view_offline_scraper_rom() aliasof "{}"'.format(pobj.aliasof))
            pobj_parent = AEL_platforms[get_AEL_platform_index(pobj.aliasof)]
            db_platform = pobj_parent.long_name
        else:
            db_platform = pobj.long_name
        log_debug('_command_view_offline_scraper_rom() db_platform "{}"'.format(db_platform))

        # --- Load Offline Scraper database ---
        # --- Load offline scraper XML file ---
        loading_ticks_start = time.time()
        if scraper == 'AEL':
            xml_path_FN = g_PATHS.GAMEDB_INFO_DIR.pjoin(db_platform + '.xml')
            log_debug('Loading AEL XML {}'.format(xml_path_FN.getPath()))
            pDialog = KodiProgressDialog()
            pDialog.startProgress('Loading AEL Offline Scraper {} XML database...'.format(db_platform))
            games = audit_load_OfflineScraper_XML(xml_path_FN.getPath())
            pDialog.endProgress()

            game = games[game_name]
            info_text  = '[COLOR orange]ROM information[/COLOR]\n'
            info_text += "[COLOR violet]ROM basename[/COLOR]: '{}'\n".format(game_name)
            info_text += "[COLOR violet]platform[/COLOR]: '{}'\n".format(platform)
            if pobj.aliasof:
                info_text += "[COLOR violet]alias of[/COLOR]: '{}'\n".format(pobj_parent.long_name)
            info_text += '\n[COLOR orange]Metadata[/COLOR]\n'

            # Old Offline Scraper
            # info_text += "[COLOR violet]description[/COLOR]: '{}'\n".format(game['description'])
            # info_text += "[COLOR violet]year[/COLOR]: '{}'\n".format(game['year'])
            # info_text += "[COLOR violet]rating[/COLOR]: '{}'\n".format(game['rating'])
            # info_text += "[COLOR violet]manufacturer[/COLOR]: '{}'\n".format(game['manufacturer'])
            # info_text += "[COLOR violet]dev[/COLOR]: '{}'\n".format(game['dev'])
            # info_text += "[COLOR violet]genre[/COLOR]: '{}'\n".format(game['genre'])
            # info_text += "[COLOR violet]score[/COLOR]: '{}'\n".format(game['score'])
            # info_text += "[COLOR violet]player[/COLOR]: '{}'\n".format(game['player'])
            # info_text += "[COLOR violet]story[/COLOR]: '{}'\n".format(game['story'])
            # info_text += "[COLOR violet]enabled[/COLOR]: '{}'\n".format(game['enabled'])
            # info_text += "[COLOR violet]crc[/COLOR]: '{}'\n".format(game['crc'])
            # info_text += "[COLOR violet]cloneof[/COLOR]: '{}'\n".format(game['cloneof'])

            # V1 Offline Scraper
            info_text += "[COLOR violet]title[/COLOR]: '{}'\n".format(game['title'])
            info_text += "[COLOR violet]year[/COLOR]: '{}'\n".format(game['year'])
            info_text += "[COLOR violet]genre[/COLOR]: '{}'\n".format(game['genre'])
            info_text += "[COLOR violet]developer[/COLOR]: '{}'\n".format(game['developer'])
            info_text += "[COLOR violet]publisher[/COLOR]: '{}'\n".format(game['publisher'])
            info_text += "[COLOR violet]rating[/COLOR]: '{}'\n".format(game['rating'])
            info_text += "[COLOR violet]nplayers[/COLOR]: '{}'\n".format(game['nplayers'])
            info_text += "[COLOR violet]score[/COLOR]: '{}'\n".format(game['score'])
            info_text += "[COLOR violet]plot[/COLOR]: '{}'\n".format(game['plot'])

        elif scraper == 'LaunchBox':
            xml_file = platform_AEL_to_LB_XML[platform]
            xml_path = os.path.join(g_PATHS.ADDON_CODE_DIR.getPath(), xml_file)
            # log_debug('xml_file = {}'.format(xml_file))
            log_debug('Loading LaunchBox XML {}'.format(xml_path))
            games = audit_load_OfflineScraper_XML(xml_path)
            game = games[game_name]
            # log_debug(unicode(game))

            info_text  = '[COLOR orange]ROM information[/COLOR]\n'
            info_text += "[COLOR violet]game_name[/COLOR]: '{}'\n".format(game_name)
            info_text += "[COLOR violet]platform[/COLOR]: '{}'\n".format(platform)
            info_text += '\n[COLOR orange]Metadata[/COLOR]\n'
            info_text += "[COLOR violet]Name[/COLOR]: '{}'\n".format(game['Name'])
            info_text += "[COLOR violet]ReleaseYear[/COLOR]: '{}'\n".format(game['ReleaseYear'])
            info_text += "[COLOR violet]Overview[/COLOR]: '{}'\n".format(game['Overview'])
            info_text += "[COLOR violet]MaxPlayers[/COLOR]: '{}'\n".format(game['MaxPlayers'])
            info_text += "[COLOR violet]Cooperative[/COLOR]: '{}'\n".format(game['Cooperative'])
            info_text += "[COLOR violet]VideoURL[/COLOR]: '{}'\n".format(game['VideoURL'])
            info_text += "[COLOR violet]DatabaseID[/COLOR]: '{}'\n".format(game['DatabaseID'])
            info_text += "[COLOR violet]CommunityRating[/COLOR]: '{}'\n".format(game['CommunityRating'])
            info_text += "[COLOR violet]Platform[/COLOR]: '{}'\n".format(game['Platform'])
            info_text += "[COLOR violet]Genres[/COLOR]: '{}'\n".format(game['Genres'])
            info_text += "[COLOR violet]Publisher[/COLOR]: '{}'\n".format(game['Publisher'])
            info_text += "[COLOR violet]Developer[/COLOR]: '{}'\n".format(game['Developer'])
        else:
            kodi_dialog_OK('Wrong scraper name {}'.format(scraper))
            return

        # --- Show information window ---
        window_title = 'Offline Scraper ROM information'
        log_debug('Setting Window(10000) Property "FontWidth" = "monospaced"')
        xbmcgui.Window(10000).setProperty('FontWidth', 'monospaced')
        dialog = xbmcgui.Dialog()
        dialog.textviewer(window_title, info_text)
        log_debug('Setting Window(10000) Property "FontWidth" = "proportional"')
        xbmcgui.Window(10000).setProperty('FontWidth', 'proportional')

    #
    # Updated all virtual categories DB
    #
    def _command_update_virtual_category_db_all(self):
        # --- Sanity checks ---
        if len(self.launchers) == 0:
            kodi_dialog_OK('You do not have any ROM Launcher. Add a ROM Launcher first.')
            return

        # --- Make a big dictionary will all the ROMs ---
        # Pass all_roms dictionary to the catalg create functions so this has not to be
        # recomputed for every virtual launcher.
        log_verb('_command_update_virtual_category_db_all() Creating list of all ROMs in all Launchers')
        all_roms = {}
        num_launchers = len(self.launchers)
        i = 0
        pDialog = xbmcgui.DialogProgress()
        pDialog_canceled = False
        pDialog.create('Advanced Emulator Launcher', 'Making ROM list ...')
        for launcher_id in self.launchers:
            # >> Update dialog
            pDialog.update(i * 100 / num_launchers)
            i += 1

            # >> Get current launcher
            launcher = self.launchers[launcher_id]
            categoryID = launcher['categoryID']
            if categoryID in self.categories:
                category_name = self.categories[categoryID]['m_name']
            elif categoryID == VCATEGORY_ADDONROOT_ID:
                category_name = 'Root category'
            else:
                log_error('_command_update_virtual_category_db_all() Wrong categoryID = {0}'.format(categoryID))
                kodi_dialog_OK('Wrong categoryID = {0}. Report this bug please.'.format(categoryID))
                return

            # >> If launcher is standalone skip
            if launcher['rompath'] == '': continue

            # >> Open launcher and add roms to the big list
            roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, launcher)

            # >> Add additional fields to ROM to make a Favourites ROM
            # >> Virtual categories/launchers are like Favourite ROMs that cannot be edited.
            # >> NOTE roms is updated by assigment, dictionaries are mutable
            fav_roms = {}
            for rom_id in roms:
                fav_rom = fs_get_Favourite_from_ROM(roms[rom_id], launcher)
                # >> Add the category this ROM belongs to.
                fav_rom['category_name'] = category_name
                fav_roms[rom_id] = fav_rom

            # >> Update dictionary
            all_roms.update(fav_roms)
        pDialog.update(100)
        pDialog.close()

        # --- Update all virtual launchers ---
        self._command_update_virtual_category_db(VCATEGORY_TITLE_ID, all_roms)
        self._command_update_virtual_category_db(VCATEGORY_YEARS_ID, all_roms)
        self._command_update_virtual_category_db(VCATEGORY_GENRE_ID, all_roms)
        self._command_update_virtual_category_db(VCATEGORY_DEVELOPER_ID, all_roms)
        self._command_update_virtual_category_db(VCATEGORY_NPLAYERS_ID, all_roms)
        self._command_update_virtual_category_db(VCATEGORY_ESRB_ID, all_roms)
        self._command_update_virtual_category_db(VCATEGORY_RATING_ID, all_roms)
        self._command_update_virtual_category_db(VCATEGORY_CATEGORY_ID, all_roms)
        kodi_notify('All virtual categories updated')

    #
    # Makes a virtual category database
    #
    def _command_update_virtual_category_db(self, virtual_categoryID, all_roms_external = None):
        # --- Customise function depending on virtual category ---
        if virtual_categoryID == VCATEGORY_TITLE_ID:
            log_info('_command_update_virtual_category_db() Updating Title DB')
            vcategory_db_directory = g_PATHS.VIRTUAL_CAT_TITLE_DIR
            vcategory_db_filename  = g_PATHS.VCAT_TITLE_FILE_PATH
            vcategory_field_name   = 'm_name'
            vcategory_name         = 'Titles'
        elif virtual_categoryID == VCATEGORY_YEARS_ID:
            log_info('_command_update_virtual_category_db() Updating Year DB')
            vcategory_db_directory = g_PATHS.VIRTUAL_CAT_YEARS_DIR
            vcategory_db_filename  = g_PATHS.VCAT_YEARS_FILE_PATH
            vcategory_field_name   = 'm_year'
            vcategory_name         = 'Years'
        elif virtual_categoryID == VCATEGORY_GENRE_ID:
            log_info('_command_update_virtual_category_db() Updating Genre DB')
            vcategory_db_directory = g_PATHS.VIRTUAL_CAT_GENRE_DIR
            vcategory_db_filename  = g_PATHS.VCAT_GENRE_FILE_PATH
            vcategory_field_name   = 'm_genre'
            vcategory_name         = 'Genres'
        elif virtual_categoryID == VCATEGORY_DEVELOPER_ID:
            log_info('_command_update_virtual_category_db() Updating Developer DB')
            vcategory_db_directory = g_PATHS.VIRTUAL_CAT_DEVELOPER_DIR
            vcategory_db_filename  = g_PATHS.VCAT_DEVELOPER_FILE_PATH
            vcategory_field_name   = 'm_developer'
            vcategory_name         = 'Developers'
        elif virtual_categoryID == VCATEGORY_NPLAYERS_ID:
            log_info('_command_update_virtual_category_db() Updating NPlayer DB')
            vcategory_db_directory = g_PATHS.VIRTUAL_CAT_NPLAYERS_DIR
            vcategory_db_filename  = g_PATHS.VCAT_NPLAYERS_FILE_PATH
            vcategory_field_name   = 'm_nplayers'
            vcategory_name         = 'NPlayers'
        elif virtual_categoryID == VCATEGORY_ESRB_ID:
            log_info('_command_update_virtual_category_db() Updating ESRB DB')
            vcategory_db_directory = g_PATHS.VIRTUAL_CAT_ESRB_DIR
            vcategory_db_filename  = g_PATHS.VCAT_ESRB_FILE_PATH
            vcategory_field_name   = 'm_esrb'
            vcategory_name         = 'ESRB'
        elif virtual_categoryID == VCATEGORY_RATING_ID:
            log_info('_command_update_virtual_category_db() Updating Rating DB')
            vcategory_db_directory = g_PATHS.VIRTUAL_CAT_RATING_DIR
            vcategory_db_filename  = g_PATHS.VCAT_RATING_FILE_PATH
            vcategory_field_name   = 'm_rating'
            vcategory_name         = 'Rating'
        elif virtual_categoryID == VCATEGORY_CATEGORY_ID:
            log_info('_command_update_virtual_category_db() Updating Category DB')
            vcategory_db_directory = g_PATHS.VIRTUAL_CAT_CATEGORY_DIR
            vcategory_db_filename  = g_PATHS.VCAT_CATEGORY_FILE_PATH
            vcategory_field_name   = ''
            vcategory_name         = 'Categories'
        else:
            log_error('_command_update_virtual_category_db() Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
            kodi_dialog_OK('Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
            return

        # --- Sanity checks ---
        if len(self.launchers) == 0:
            kodi_dialog_OK('You do not have any ROM Launcher. Add a ROM Launcher first.')
            return

        # --- Delete previous hashed database XMLs ---
        log_info('_command_update_virtual_category_db() Cleaning hashed database old XMLs')
        for the_file in vcategory_db_directory.scanFilesInPathAsPaths('*.*'):
            file_extension = the_file.getExt()
            if file_extension.lower() != '.xml' and file_extension.lower() != '.json':
                # >> There should be only XMLs or JSON in this directory
                log_error('_command_update_virtual_category_db() Non XML/JSON file "{0}"'.format(the_file.getPath()))
                log_error('_command_update_virtual_category_db() Skipping it from deletion')
                continue
            log_verb('_command_update_virtual_category_db() Deleting "{0}"'.format(the_file.getPath()))
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
            num_launchers = len(self.launchers)
            i = 0
            pDialog.create('Advanced Emulator Launcher', 'Making ROM list ...')
            for launcher_id in self.launchers:
                # >> Update dialog
                pDialog.update(i * 100 / num_launchers)
                i += 1

                # >> Get current launcher
                launcher = self.launchers[launcher_id]
                categoryID = launcher['categoryID']
                if categoryID in self.categories:
                    category_name = self.categories[categoryID]['m_name']
                elif categoryID == VCATEGORY_ADDONROOT_ID:
                    category_name = 'Root category'
                else:
                    log_error('_command_update_virtual_category_db() Wrong categoryID = {0}'.format(categoryID))
                    kodi_dialog_OK('Wrong categoryID = {0}. Report this bug please.'.format(categoryID))
                    return

                # >> If launcher is standalone skip
                if launcher['rompath'] == '': continue

                # >> Open launcher and add roms to the big list
                roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, launcher)

                # >> Add additional fields to ROM to make a Favourites ROM
                # >> Virtual categories/launchers are like Favourite ROMs that cannot be edited.
                # >> NOTE roms is updated by assigment, dictionaries are mutable
                fav_roms = {}
                for rom_id in roms:
                    fav_rom = fs_get_Favourite_from_ROM(roms[rom_id], launcher)
                    # >> Add the category this ROM belongs to.
                    fav_rom['category_name'] = category_name
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
                vcategory_key = rom['m_name'][0].upper()
            elif virtual_categoryID == VCATEGORY_CATEGORY_ID:
                vcategory_key = rom['category_name']
            else:
                vcategory_key = rom[vcategory_field_name]
            # >> '' is a special case
            if vcategory_key == '': vcategory_key = '[ Not set ]'
            if vcategory_key in virtual_launchers:
                virtual_launchers[vcategory_key][rom['id']] = rom
            else:
                virtual_launchers[vcategory_key] = {rom['id'] : rom}

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
            vlauncher_id_md5   = hashlib.md5(vlauncher_id)
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
    def _command_run_standalone_launcher(self, categoryID, launcherID):
        # --- Check launcher is OK ---
        if launcherID not in self.launchers:
            kodi_dialog_OK('launcherID not found in self.launchers')
            return
        launcher = self.launchers[launcherID]
        minimize_flag = launcher['toggle_window']

        # --- Execute Kodi built-in function under certain conditions ---
        application = FileName(launcher['application'])
        if application.getBase().lower().replace('.exe' , '') == 'xbmc'  or \
           'xbmc-fav-' in launcher['application'] or 'xbmc-sea-' in launcher['application']:
            xbmc.executebuiltin('XBMC.{0}'.format(launcher['args']))
            return

        # ~~~~~ External application ~~~~~
        app_basename   = application.getBase()
        app_ext        = application.getExt()
        arguments      = launcher['args']
        launcher_title = launcher['m_name']
        log_info('_run_standalone_launcher() categoryID {0}'.format(categoryID))
        log_info('_run_standalone_launcher() launcherID {0}'.format(launcherID))
        log_info('_run_standalone_launcher() application   "{0}"'.format(application.getPath()))
        log_info('_run_standalone_launcher() apppath       "{0}"'.format(application.getDir()))
        log_info('_run_standalone_launcher() app_basename  "{0}"'.format(app_basename))
        log_info('_run_standalone_launcher() app_ext       "{0}"'.format(app_ext))
        log_info('_run_standalone_launcher() launcher name "{0}"'.format(launcher_title))

        # ~~~ Argument substitution ~~~
        log_info('_run_standalone_launcher() raw arguments   "{0}"'.format(arguments))
        arguments = arguments.replace('$apppath%' , application.getDir())
        log_info('_run_standalone_launcher() final arguments "{0}"'.format(arguments))

        # --- Check for errors and abort if errors found ---
        if not application.exists():
            log_error('Launching app not found "{0}"'.format(application.getPath()))
            kodi_notify_warn('App {0} not found.'.format(application.getOriginalPath()))
            return

        # ~~~~~ Execute external application ~~~~~
        non_blocking_flag = False
        self._run_before_execution(launcher_title, minimize_flag)
        self._run_process(application.getPath(), arguments, application.getDir(), app_ext, non_blocking_flag)
        self._run_after_execution(minimize_flag)

    #
    # Launchs a ROM
    # NOTE args_extre maybe present or not in Favourite ROM. In newer version of AEL always present.
    #
    def _command_run_rom(self, categoryID, launcherID, romID):
        # --- ROM in Favourites ---
        if categoryID == VCATEGORY_FAVOURITES_ID and launcherID == VLAUNCHER_FAVOURITES_ID:
            log_info('_command_run_rom() Launching ROM in Favourites ...')
            roms = fs_load_Favourites_JSON(g_PATHS.FAV_JSON_FILE_PATH)
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
            recent_roms_list = fs_load_Collection_ROMs_JSON(g_PATHS.RECENT_PLAYED_FILE_PATH)
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
            most_played_roms = fs_load_Favourites_JSON(g_PATHS.MOST_PLAYED_FILE_PATH)
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
            (collections, update_timestamp) = fs_load_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH)
            collection = collections[launcherID]
            roms_json_file = g_PATHS.COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
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
                roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_TITLE_DIR, launcherID)
            elif categoryID == VCATEGORY_YEARS_ID:
                log_info('_command_run_rom() Launching ROM in Year Virtual Launcher ...')
                roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_YEARS_DIR, launcherID)
            elif categoryID == VCATEGORY_GENRE_ID:
                log_info('_command_run_rom() Launching ROM in Gender Virtual Launcher ...')
                roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_GENRE_DIR, launcherID)
            elif categoryID == VCATEGORY_DEVELOPER_ID:
                log_info('_command_run_rom() Launching ROM in Developer Virtual Launcher ...')
                roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_DEVELOPER_DIR, launcherID)
            elif categoryID == VCATEGORY_CATEGORY_ID:
                log_info('_command_run_rom() Launching ROM in Category Virtual Launcher ...')
                roms = fs_load_VCategory_ROMs_JSON(g_PATHS.VIRTUAL_CAT_CATEGORY_DIR, launcherID)

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
            roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, launcher)
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
        if self.settings['escape_romfile']:
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
        recent_roms_list = fs_load_Collection_ROMs_JSON(g_PATHS.RECENT_PLAYED_FILE_PATH)
        recent_roms_list = [rom for rom in recent_roms_list if rom['id'] != recent_rom['id']]
        recent_roms_list.insert(0, recent_rom)
        if len(recent_roms_list) > MAX_RECENT_PLAYED_ROMS:
            log_debug('_command_run_rom() len(recent_roms_list) = {0}'.format(len(recent_roms_list)))
            log_debug('_command_run_rom() Trimming list to {0} ROMs'.format(MAX_RECENT_PLAYED_ROMS))
            temp_list        = recent_roms_list[:MAX_RECENT_PLAYED_ROMS]
            recent_roms_list = temp_list
        fs_write_Collection_ROMs_JSON(g_PATHS.RECENT_PLAYED_FILE_PATH, recent_roms_list)

        # --- Compute most played ROM statistics ---
        most_played_roms = fs_load_Favourites_JSON(g_PATHS.MOST_PLAYED_FILE_PATH)
        if recent_rom['id'] in most_played_roms:
            rom_id = recent_rom['id']
            most_played_roms[rom_id]['launch_count'] += 1
        else:
            # >> Add field launch_count to recent_rom to count how many times have been launched.
            recent_rom['launch_count'] = 1
            most_played_roms[recent_rom['id']] = recent_rom
        fs_write_Favourites_JSON(g_PATHS.MOST_PLAYED_FILE_PATH, most_played_roms)

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
            if self.settings['display_launcher_notify']:
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
    def _run_process(self, application, arguments, apppath, romext, non_blocking_flag):
        import shlex
        import subprocess

        # >> Determine platform and launch application
        # >> See http://stackoverflow.com/questions/446209/possible-values-from-sys-platform

        # >> Decompose arguments to call subprocess module
        arg_list = shlex.split(arguments, posix = True)
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
                # os.system('start "AEL" /b "{0}"'.format(application))
                retcode = subprocess.call('start "AEL" /b "{0}"'.format(application), shell = True)
                log_info('_run_process() (Windows) LNK app retcode = {0}'.format(retcode))

            # >> ROM launcher where ROMs are LNK files
            elif romext == 'lnk' or romext == 'LNK':
                log_debug('_run_process() (Windows) Launching LNK ROM')
                # os.system('start "AEL" /b "{0}"'.format(arguments))
                retcode = subprocess.call('start "AEL" /b "{0}"'.format(arguments), shell = True)
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
                log_debug('_run_process() (Windows) show_batch_window = {0}'.format(self.settings['show_batch_window']))
                info = subprocess.STARTUPINFO()
                info.dwFlags = 1
                info.wShowWindow = 5 if self.settings['show_batch_window'] else 0
                retcode = subprocess.call(exec_list, cwd = apppath, close_fds = True, startupinfo = info)
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

                # >> cwd = apppath fails if application path has Unicode on Windows
                # >> A workaraound is to use cwd = apppath.encode(sys.getfilesystemencoding()) --> DOES NOT WORK
                # >> For the moment AEL cannot launch executables on Windows having Unicode paths.
                windows_cd_apppath = self.settings['windows_cd_apppath']
                windows_close_fds  = self.settings['windows_close_fds']
                log_debug('_run_process() (Windows) Launching regular application')
                log_debug('_run_process() (Windows) windows_cd_apppath = {0}'.format(windows_cd_apppath))
                log_debug('_run_process() (Windows) windows_close_fds  = {0}'.format(windows_close_fds))
                # >>  Note that on Windows, you cannot set close_fds to true and also redirect the
                # >> standard handles by setting stdin, stdout or stderr.
                if windows_cd_apppath and windows_close_fds:
                    retcode = subprocess.call(exec_list, cwd = apppath, close_fds = True)
                elif windows_cd_apppath and not windows_close_fds:
                    with open(g_PATHS.LAUNCH_LOG_FILE_PATH.getPath(), 'w') as f:
                        retcode = subprocess.call(exec_list, cwd = apppath, close_fds = False,
                                                  stdout = f, stderr = subprocess.STDOUT)
                elif not windows_cd_apppath and windows_close_fds:
                    retcode = subprocess.call(exec_list, close_fds = True)
                elif not windows_cd_apppath and not windows_close_fds:
                    with open(g_PATHS.LAUNCH_LOG_FILE_PATH.getPath(), 'w') as f:
                        retcode = subprocess.call(exec_list, close_fds = False,
                                                  stdout = f, stderr = subprocess.STDOUT)
                else:
                    raise Exception('Logical error')
                log_info('_run_process() (Windows) Process retcode = {0}'.format(retcode))

        # Android
        elif is_android():

            retcode = os.system("{0} {1}".format(application, arguments))
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
            # os.system('"{0}" {1}'.format(application, arguments))

            # >> New way of launching, uses subproces module. Also, save child process stdout.
            if non_blocking_flag:
                # >> In a non-blocking launch stdout/stderr of child process cannot be recorded.
                log_info('_run_process() (Linux) Launching non-blocking process subprocess.Popen()')
                p = subprocess.Popen(exec_list, close_fds = True)
            else:
                if self.settings['lirc_state']: xbmc.executebuiltin('LIRC.stop')
                log_info('_run_process() (Linux) Launching blocking process subprocess.call()')
                with open(g_PATHS.LAUNCH_LOG_FILE_PATH.getPath(), 'w') as f:
                    retcode = subprocess.call(exec_list, stdout = f, stderr = subprocess.STDOUT, close_fds = True)
                log_info('_run_process() Process retcode = {0}'.format(retcode))
                if self.settings['lirc_state']: xbmc.executebuiltin('LIRC.start')

        # >> OS X
        elif sys.platform.startswith('darwin'):
            # >> Old way
            # os.system('"{0}" {1}'.format(application, arguments))

            # >> New way.
            with open(g_PATHS.LAUNCH_LOG_FILE_PATH.getPath(), 'w') as f:
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
    def _run_before_execution(self, rom_title, toggle_screen_flag):
        # --- User notification ---
        if self.settings['display_launcher_notify']:
            kodi_notify('Launching {0}'.format(rom_title))

        # --- Stop/Pause Kodi mediaplayer if requested in settings ---
        self.kodi_was_playing = False
        # id="media_state_action" default="0" values="Stop|Pause|Let Play"
        media_state_action = self.settings['media_state_action']
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
        if self.settings['suspend_audio_engine']:
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
        # if self.settings['suspend_joystick_engine']:
            # log_verb('_run_before_execution() Suspending Kodi joystick engine')
            # >> Research. Get the value of the setting first
            # >> Apparently input.enablejoystick is not supported on Kodi Krypton anymore.
            # c_str = ('{"id" : 1, "jsonrpc" : "2.0",'
            #          ' "method" : "Settings.GetSettingValue",'
            #          ' "params" : {"setting":"input.enablejoystick"}}')
            # response = xbmc.executeJSONRPC(c_str)
            # log_debug('JSON      ''{0}'''.format(c_str))
            # log_debug('Response  ''{0}'''.format(response))

            # c_str = ('{"id" : 1, "jsonrpc" : "2.0",'
            #          ' "method" : "Settings.SetSettingValue",'
            #          ' "params" : {"setting" : "input.enablejoystick", "value" : false} }')
            # response = xbmc.executeJSONRPC(c_str)
            # log_debug('JSON      ''{0}'''.format(c_str))
            # log_debug('Response  ''{0}'''.format(response))
            # self.kodi_joystick_suspended = True

            # log_error('_run_before_execution() Suspending Kodi joystick engine not supported on Kodi Krypton!')
        # else:
            # log_verb('_run_before_execution() DO NOT suspend Kodi joystick engine')

        # --- Toggle Kodi windowed/fullscreen if requested ---
        if toggle_screen_flag:
            log_verb('_run_before_execution() Toggling Kodi fullscreen')
            kodi_toogle_fullscreen()
        else:
            log_verb('_run_before_execution() Toggling Kodi fullscreen DEACTIVATED in Launcher')

        # Disable screensaver
        if self.settings['suspend_screensaver']:
            kodi_disable_screensaver()
        else:
            screensaver_mode = kodi_get_screensaver_mode()
            log_debug('_run_before_execution() Screensaver status "{}"'.format(screensaver_mode))

        # --- Pause Kodi execution some time ---
        delay_tempo_ms = self.settings['delay_tempo']
        log_verb('_run_before_execution() Pausing {} ms'.format(delay_tempo_ms))
        xbmc.sleep(delay_tempo_ms)
        log_debug('_run_before_execution() function ENDS')

    def _run_after_execution(self, toggle_screen_flag):
        # --- Stop Kodi some time ---
        delay_tempo_ms = self.settings['delay_tempo']
        log_verb('_run_after_execution() Pausing {0} ms'.format(delay_tempo_ms))
        xbmc.sleep(delay_tempo_ms)

        # --- Toggle Kodi windowed/fullscreen if requested ---
        if toggle_screen_flag:
            log_verb('_run_after_execution() Toggling Kodi fullscreen')
            kodi_toogle_fullscreen()
        else:
            log_verb('_run_after_execution() Toggling Kodi fullscreen DEACTIVATED in Launcher')

        # --- Resume audio engine if it was suspended ---
        # Calling xmbc.audioResume() takes a loong time (2/4 secs) if audio was not properly suspended!
        # Also produces this in Kodi's log:
        # WARNING: CActiveAE::StateMachine - signal: 0 from port: OutputControlPort not handled for state: 7
        #   ERROR: ActiveAE::Resume - failed to init
        if self.kodi_audio_suspended:
            log_verb('_run_after_execution() Kodi audio engine was suspended before launching')
            log_verb('_run_after_execution() Resuming Kodi audio engine')
            xbmc.audioResume()
            xbmc.enableNavSounds(True)
            xbmc.sleep(100)
        else:
            log_verb('_run_after_execution() DO NOT resume Kodi audio engine')

        # --- Resume joystick engine if it was suspended ---
        if self.kodi_joystick_suspended:
            log_verb('_run_after_execution() Kodi joystick engine was suspended before launching')
            log_verb('_run_after_execution() Resuming Kodi joystick engine')
            # response = xbmc.executeJSONRPC(c_str)
            # log_debug('JSON      ''{0}'''.format(c_str))
            # log_debug('Response  ''{0}'''.format(response))
            log_verb('_run_before_execution() Not supported on Kodi Krypton!')
        else:
            log_verb('_run_after_execution() DO NOT resume Kodi joystick engine')

        # Restore screensaver status.
        if self.settings['suspend_screensaver']:
            kodi_restore_screensaver()
        else:
            screensaver_mode = kodi_get_screensaver_mode()
            log_debug('_run_after_execution() Screensaver status "{}"'.format(screensaver_mode))

        # --- Resume Kodi playing if it was paused. If it was stopped, keep it stopped. ---
        media_state_action = self.settings['media_state_action']
        media_state_str = ['Stop', 'Pause', 'Let Play'][media_state_action]
        log_verb('_run_after_execution() media_state_action is "{0}" ({1})'.format(media_state_str, media_state_action))
        log_verb('_run_after_execution() self.kodi_was_playing is {0}'.format(self.kodi_was_playing))
        if self.kodi_was_playing and media_state_action == 1:
            log_verb('_run_after_execution() Calling xbmc.Player().play()')
            xbmc.Player().play()
        log_debug('_run_after_execution() function ENDS')

    #
    # Check if Launcher reports must be created/regenrated
    #
    def _roms_regenerate_launcher_reports(self, categoryID, launcherID, roms):
        # --- Get report filename ---
        if categoryID in self.categories: category_name = self.categories[categoryID]['m_name']
        else:                             category_name = VCATEGORY_ADDONROOT_ID
        roms_base_noext  = fs_get_ROMs_basename(category_name, self.launchers[launcherID]['m_name'], launcherID)
        report_stats_FN  = g_PATHS.REPORTS_DIR.pjoin(roms_base_noext + '_stats.txt')
        log_verb('_command_view_menu() Stats  OP "{0}"'.format(report_stats_FN.getOriginalPath()))

        # --- If report doesn't exists create it automatically ---
        log_debug('_command_view_Launcher_Report() Testing report file "{0}"'.format(report_stats_FN.getPath()))
        if not report_stats_FN.exists():
            kodi_dialog_OK('Report file not found. Will be generated now.')
            self._roms_create_launcher_reports(categoryID, launcherID, roms)
            # >> Update report timestamp
            self.launchers[launcherID]['timestamp_report'] = time.time()
            # >> Save Categories/Launchers
            # >> DO NOT update the timestamp of categories/launchers of report will always be obsolete!!!
            # >> Keep same timestamp as before.
            fs_write_catfile(g_PATHS.CATEGORIES_FILE_PATH, self.categories, self.launchers, self.update_timestamp)

        # --- If report timestamp is older than launchers last modification, recreate it ---
        if self.launchers[launcherID]['timestamp_report'] <= self.launchers[launcherID]['timestamp_launcher']:
            kodi_dialog_OK('Report is outdated. Will be regenerated now.')
            self._roms_create_launcher_reports(categoryID, launcherID, roms)
            self.launchers[launcherID]['timestamp_report'] = time.time()
            fs_write_catfile(g_PATHS.CATEGORIES_FILE_PATH, self.categories, self.launchers, self.update_timestamp)

    #
    # Creates a Launcher report having:
    #  1) Launcher statistics
    #  2) Report of ROM metadata
    #  3) Report of ROM artwork
    #  4) If No-Intro file, then No-Intro audit information.
    #
    def _roms_create_launcher_reports(self, categoryID, launcherID, roms):
        ROM_NAME_LENGHT = 50

        # >> Report file name
        if categoryID in self.categories: category_name = self.categories[categoryID]['m_name']
        else:                             category_name = VCATEGORY_ADDONROOT_ID
        launcher = self.launchers[launcherID]
        roms_base_noext  = fs_get_ROMs_basename(category_name, launcher['m_name'], launcherID)
        report_stats_FN  = g_PATHS.REPORTS_DIR.pjoin(roms_base_noext + '_stats.txt')
        report_meta_FN   = g_PATHS.REPORTS_DIR.pjoin(roms_base_noext + '_metadata.txt')
        report_assets_FN = g_PATHS.REPORTS_DIR.pjoin(roms_base_noext + '_assets.txt')
        log_verb('_roms_create_launcher_reports() Stats  OP "{0}"'.format(report_stats_FN.getOriginalPath()))
        log_verb('_roms_create_launcher_reports() Meta   OP "{0}"'.format(report_meta_FN.getOriginalPath()))
        log_verb('_roms_create_launcher_reports() Assets OP "{0}"'.format(report_assets_FN.getOriginalPath()))
        roms_base_noext = fs_get_ROMs_basename(category_name, launcher['m_name'], launcherID)
        report_file_name = g_PATHS.REPORTS_DIR.pjoin(roms_base_noext + '.txt')
        log_verb('_roms_create_launcher_reports() Report filename "{0}"'.format(report_file_name.getOriginalPath()))

        # >> Step 1: Build report data
        num_roms = len(roms)
        missing_m_year      = missing_m_genre    = missing_m_developer = missing_m_nplayers  = 0
        missing_m_esrb      = missing_m_rating   = missing_m_plot      = 0
        missing_s_title     = missing_s_snap     = missing_s_fanart    = missing_s_banner    = 0
        missing_s_clearlogo = missing_s_boxfront = missing_s_boxback   = missing_s_cartridge = 0
        missing_s_flyer     = missing_s_map      = missing_s_manual    = missing_s_trailer   = 0
        audit_none = audit_have = audit_miss = audit_unknown = 0
        audit_num_parents = audit_num_clones = 0
        check_list = []
        path_title_P = FileName(launcher['path_title']).getPath()
        path_snap_P = FileName(launcher['path_snap']).getPath()
        path_boxfront_P = FileName(launcher['path_boxfront']).getPath()
        path_boxback_P = FileName(launcher['path_boxback']).getPath()
        path_cartridge_P = FileName(launcher['path_cartridge']).getPath()
        for rom_id in sorted(roms, key = lambda x : roms[x]['m_name']):
            rom = roms[rom_id]
            rom_info = {}
            rom_info['m_name'] = rom['m_name']
            rom_info['m_nointro_status'] = rom['nointro_status']
            rom_info['m_pclone_status'] = rom['pclone_status']
            # --- Metadata ---
            if rom['m_year']:                 rom_info['m_year']      = 'YES'
            else:                             rom_info['m_year']      = '---'; missing_m_year += 1
            if rom['m_genre']:                rom_info['m_genre']     = 'YES'
            else:                             rom_info['m_genre']     = '---'; missing_m_genre += 1
            if rom['m_developer']:            rom_info['m_developer'] = 'YES'
            else:                             rom_info['m_developer'] = '---'; missing_m_developer += 1
            if rom['m_nplayers']:             rom_info['m_nplayers']  = 'YES'
            else:                             rom_info['m_nplayers']  = '---'; missing_m_nplayers += 1
            if rom['m_esrb'] == ESRB_PENDING: rom_info['m_esrb']      = '---'; missing_m_esrb += 1
            else:                             rom_info['m_studio']    = 'YES'
            if rom['m_rating']:               rom_info['m_rating']    = 'YES'
            else:                             rom_info['m_rating']    = '---'; missing_m_rating += 1
            if rom['m_plot']:                 rom_info['m_plot']      = 'YES'
            else:                             rom_info['m_plot']      = '---'; missing_m_plot += 1
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
            romfile_FN = FileName(rom['filename'])
            romfile_getBase_noext = romfile_FN.getBase_noext()
            if rom['s_title']:
                rom_info['s_title'] = self._aux_get_info(FileName(rom['s_title']), path_title_P, romfile_getBase_noext)
            else:
                rom_info['s_title'] = '-'
                missing_s_title += 1
            if rom['s_snap']:
                rom_info['s_snap'] = self._aux_get_info(FileName(rom['s_snap']), path_snap_P, romfile_getBase_noext)
            else:
                rom_info['s_snap'] = '-'
                missing_s_snap += 1
            if rom['s_boxfront']:
                rom_info['s_boxfront'] = self._aux_get_info(FileName(rom['s_boxfront']), path_boxfront_P, romfile_getBase_noext)
            else:
                rom_info['s_boxfront'] = '-'
                missing_s_boxfront += 1
            if rom['s_boxback']:
                rom_info['s_boxback'] = self._aux_get_info(FileName(rom['s_boxback']), path_boxback_P, romfile_getBase_noext)
            else:
                rom_info['s_boxback'] = '-'
                missing_s_boxback += 1
            if rom['s_cartridge']:
                rom_info['s_cartridge'] = self._aux_get_info(FileName(rom['s_cartridge']), path_cartridge_P, romfile_getBase_noext)
            else:
                rom_info['s_cartridge'] = '-'
                missing_s_cartridge += 1
            if rom['s_fanart']:    rom_info['s_fanart']    = 'Y'
            else:                  rom_info['s_fanart']    = '-'; missing_s_fanart += 1
            if rom['s_banner']:    rom_info['s_banner']    = 'Y'
            else:                  rom_info['s_banner']    = '-'; missing_s_banner += 1
            if rom['s_clearlogo']: rom_info['s_clearlogo'] = 'Y'
            else:                  rom_info['s_clearlogo'] = '-'; missing_s_clearlogo += 1
            if rom['s_flyer']:     rom_info['s_flyer']     = 'Y'
            else:                  rom_info['s_flyer']     = '-'; missing_s_flyer += 1
            if rom['s_map']:       rom_info['s_map']       = 'Y'
            else:                  rom_info['s_map']       = '-'; missing_s_map += 1
            if rom['s_manual']:    rom_info['s_manual']    = 'Y'
            else:                  rom_info['s_manual']    = '-'; missing_s_manual += 1
            if rom['s_trailer']:   rom_info['s_trailer']   = 'Y'
            else:                  rom_info['s_trailer']   = '-'; missing_s_trailer += 1
            # --- ROM audit ---
            if   rom['nointro_status'] == AUDIT_STATUS_NONE:    audit_none += 1
            elif rom['nointro_status'] == AUDIT_STATUS_HAVE:    audit_have += 1
            elif rom['nointro_status'] == AUDIT_STATUS_MISS:    audit_miss += 1
            elif rom['nointro_status'] == AUDIT_STATUS_UNKNOWN: audit_unknown += 1
            else:
                log_error('Unknown audit status {0}.'.format(rom['nointro_status']))
                kodi_dialog_OK('Unknown audit status {0}. This is a bug, please report it.'.format(rom['nointro_status']))
                return
            if   rom['pclone_status'] == PCLONE_STATUS_PARENT: audit_num_parents += 1
            elif rom['pclone_status'] == PCLONE_STATUS_CLONE:  audit_num_clones += 1
            elif rom['pclone_status'] == PCLONE_STATUS_NONE:   pass
            else:
                log_error('Unknown pclone status {0}.'.format(rom['pclone_status']))
                kodi_dialog_OK('Unknown pclone status {0}. This is a bug, please report it.'.format(rom['pclone_status']))
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

        have_s_title = num_roms - missing_s_title
        have_s_snap = num_roms - missing_s_snap
        have_s_boxfront = num_roms - missing_s_boxfront
        have_s_boxback = num_roms - missing_s_boxback
        have_s_cartridge = num_roms - missing_s_cartridge
        have_s_fanart = num_roms - missing_s_fanart
        have_s_banner = num_roms - missing_s_banner
        have_s_clearlogo = num_roms - missing_s_clearlogo
        have_s_flyer = num_roms - missing_s_flyer
        have_s_map = num_roms - missing_s_map
        have_s_manual = num_roms - missing_s_manual
        have_s_trailer = num_roms - missing_s_trailer

        have_s_title_pcent = float(have_s_title*100) / num_roms
        have_s_snap_pcent = float(have_s_snap*100) / num_roms
        have_s_boxfront_pcent = float(have_s_boxfront*100) / num_roms
        have_s_boxback_pcent = float(have_s_boxback*100) / num_roms
        have_s_cartridge_pcent = float(have_s_cartridge*100) / num_roms
        have_s_fanart_pcent = float(have_s_fanart*100) / num_roms
        have_s_banner_pcent = float(have_s_banner*100) / num_roms
        have_s_clearlogo_pcent = float(have_s_clearlogo*100) / num_roms
        have_s_flyer_pcent = float(have_s_flyer*100) / num_roms
        have_s_map_pcent = float(have_s_map*100) / num_roms
        have_s_manual_pcent = float(have_s_manual*100) / num_roms
        have_s_trailer_pcent = float(have_s_trailer*100) / num_roms

        miss_s_title_pcent = float(missing_s_title*100) / num_roms
        miss_s_snap_pcent = float(missing_s_snap*100) / num_roms
        miss_s_boxfront_pcent = float(missing_s_boxfront*100) / num_roms
        miss_s_boxback_pcent = float(missing_s_boxback*100) / num_roms
        miss_s_cartridge_pcent = float(missing_s_cartridge*100) / num_roms
        miss_s_fanart_pcent = float(missing_s_fanart*100) / num_roms
        miss_s_banner_pcent = float(missing_s_banner*100) / num_roms
        miss_s_clearlogo_pcent = float(missing_s_clearlogo*100) / num_roms
        miss_s_flyer_pcent = float(missing_s_flyer*100) / num_roms
        miss_s_map_pcent = float(missing_s_map*100) / num_roms
        miss_s_manual_pcent = float(missing_s_manual*100) / num_roms
        miss_s_trailer_pcent = float(missing_s_trailer*100) / num_roms

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
        str_list.append('Title     {0:5d} have / {1:5d} miss  ({2:5.1f}%, {3:5.1f}%)\n'.format(
            have_s_title, missing_s_title, have_s_title_pcent, miss_s_title_pcent))
        str_list.append('Snap      {0:5d} have / {1:5d} miss  ({2:5.1f}%, {3:5.1f}%)\n'.format(
            have_s_snap, missing_s_snap, have_s_snap_pcent, miss_s_snap_pcent))
        str_list.append('Boxfront  {0:5d} have / {1:5d} miss  ({2:5.1f}%, {3:5.1f}%)\n'.format(
            have_s_boxfront, missing_s_boxfront, have_s_boxfront_pcent, miss_s_boxfront_pcent))
        str_list.append('Boxback   {0:5d} have / {1:5d} miss  ({2:5.1f}%, {3:5.1f}%)\n'.format(
            have_s_boxback, missing_s_boxback, have_s_boxback_pcent, miss_s_boxback_pcent))
        str_list.append('Cartridge {0:5d} have / {1:5d} miss  ({2:5.1f}%, {3:5.1f}%)\n'.format(
            have_s_cartridge, missing_s_cartridge, have_s_cartridge_pcent, miss_s_cartridge_pcent))
        str_list.append('Fanart    {0:5d} have / {1:5d} miss  ({2:5.1f}%, {3:5.1f}%)\n'.format(
            have_s_fanart, missing_s_fanart, have_s_fanart_pcent, miss_s_fanart_pcent))
        str_list.append('Banner    {0:5d} have / {1:5d} miss  ({2:5.1f}%, {3:5.1f}%)\n'.format(
            have_s_banner, missing_s_banner, have_s_banner_pcent, miss_s_banner_pcent))
        str_list.append('Clearlogo {0:5d} have / {1:5d} miss  ({2:5.1f}%, {3:5.1f}%)\n'.format(
            have_s_clearlogo, missing_s_clearlogo, have_s_clearlogo_pcent, miss_s_clearlogo_pcent))
        str_list.append('Flyer     {0:5d} have / {1:5d} miss  ({2:5.1f}%, {3:5.1f}%)\n'.format(
            have_s_flyer, missing_s_flyer, have_s_flyer_pcent, miss_s_flyer_pcent))
        str_list.append('Map       {0:5d} have / {1:5d} miss  ({2:5.1f}%, {3:5.1f}%)\n'.format(
            have_s_map, missing_s_map, have_s_map_pcent, miss_s_map_pcent))
        str_list.append('Manual    {0:5d} have / {1:5d} miss  ({2:5.1f}%, {3:5.1f}%)\n'.format(
            have_s_manual, missing_s_manual, have_s_manual_pcent, miss_s_manual_pcent))
        str_list.append('Trailer   {0:5d} have / {1:5d} miss  ({2:5.1f}%, {3:5.1f}%)\n'.format(
            have_s_trailer, missing_s_trailer, have_s_trailer_pcent, miss_s_trailer_pcent))

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
        str_asset_list.append('{} Tit Sna Fan Ban Clr Bxf Bxb Car Fly Map Man Tra\n'.format('Name'.ljust(ROM_NAME_LENGHT)))
        str_asset_list.append('{}\n'.format('-' * 98))
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
            full_string = ''.join(str_list)
            file = open(report_stats_FN.getPath(), 'w')
            file.write(full_string)
            file.close()

            # >> Metadata report
            full_string = ''.join(str_meta_list)
            file = open(report_meta_FN.getPath(), 'w')
            file.write(full_string)
            file.close()

            # >> Asset report
            full_string = ''.join(str_asset_list)
            file = open(report_assets_FN.getPath(), 'w')
            file.write(full_string)
            file.close()
        except OSError:
            log_error('Cannot write Launcher Report file (OSError)')
            kodi_notify_warn('Cannot write Launcher Report (OSError)')
        except IOError:
            log_error('Cannot write categories.xml file (IOError)')
            kodi_notify_warn('Cannot write Launcher Report (IOError)')


    def _aux_get_info(self, asset_FN, path_asset_P, romfile_getBase_noext):
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

    # Chooses a No-Intro/Redump DAT.
    # Return FileName object if a valid DAT was found.
    # Return None if error (DAT file not found).
    def _roms_set_NoIntro_DAT(self, launcher):
        has_custom_DAT = True if launcher['audit_custom_dat_file'] else False
        if has_custom_DAT:
            log_debug('Using user-provided custom DAT file.')
            nointro_xml_FN = FileName(launcher['audit_custom_dat_file'])
        else:
            log_debug('Trying to autolocating DAT file...')
            # --- Auto search for a DAT file ---
            NOINTRO_PATH_FN = FileName(self.settings['audit_nointro_dir'])
            if not NOINTRO_PATH_FN.exists():
                kodi_dialog_OK('No-Intro DAT directory not found. '
                    'Please set it up in AEL addon settings.')
                return None
            REDUMP_PATH_FN = FileName(self.settings['audit_redump_dir'])
            if not REDUMP_PATH_FN.exists():
                kodi_dialog_OK('No-Intro DAT directory not found. '
                    'Please set it up in AEL addon settings.')
                return None
            NOINTRO_DAT_list = NOINTRO_PATH_FN.scanFilesInPath('*.dat')
            REDUMP_DAT_list = REDUMP_PATH_FN.scanFilesInPath('*.dat')
            # Locate platform object.
            if launcher['platform'] in platform_long_to_index_dic:
                p_index = platform_long_to_index_dic[launcher['platform']]
                platform = AEL_platforms[p_index]
            else:
                kodi_dialog_OK(
                    'Unknown platform "{}". '.format(launcher['platform']) +
                    'ROM Audit cancelled.')
                return None
            # Autolocate DAT file
            if platform.DAT == DAT_NOINTRO:
                log_debug('Autolocating No-Intro DAT')
                fname = misc_look_for_NoIntro_DAT(platform, NOINTRO_DAT_list)
                if fname:
                    launcher['audit_auto_dat_file'] = fname
                    nointro_xml_FN = FileName(fname)
                else:
                    kodi_dialog_OK('No-Intro DAT cannot be auto detected.')
                    return None
            elif platform.DAT == DAT_REDUMP:
                log_debug('Autolocating Redump DAT')
                fname = misc_look_for_Redump_DAT(platform, REDUMP_DAT_list)
                if fname:
                    launcher['audit_auto_dat_file'] = fname
                    nointro_xml_FN = FileName(fname)
                else:
                    kodi_dialog_OK('Redump DAT cannot be auto detected.')
                    return None
            else:
                log_warning('platform.DAT {} unknown'.format(platform.DAT))
                return None

        return nointro_xml_FN

    # Deletes missing ROMs, probably added by the ROM Audit.
    def _roms_delete_missing_ROMs(self, roms):
        num_removed_roms = 0
        num_roms = len(roms)
        log_info('_roms_delete_missing_ROMs() Launcher has {} ROMs'.format(num_roms))
        if num_roms == 0:
            log_info('_roms_delete_missing_ROMs() Launcher is empty. No dead ROM check.')
            return num_removed_roms
        log_verb('_roms_delete_missing_ROMs() Starting dead items scan')
        for rom_id in sorted(roms.keys()):
            if not roms[rom_id]['filename']:
                # log_debug('_roms_delete_missing_ROMs() Skip "{}"'.format(roms[rom_id]['m_name']))
                continue
            ROMFileName = FileName(roms[rom_id]['filename'])
            # log_debug('_roms_delete_missing_ROMs() Test "{}"'.format(ROMFileName.getBase()))
            # --- Remove missing ROMs ---
            if not ROMFileName.exists():
                # log_debug('_roms_delete_missing_ROMs() RM   "{}"'.format(ROMFileName.getBase()))
                del roms[rom_id]
                num_removed_roms += 1
        if num_removed_roms > 0:
            log_info('_roms_delete_missing_ROMs() {} dead ROMs removed successfully'.format(
                num_removed_roms))
        else:
            log_info('_roms_delete_missing_ROMs() No dead ROMs found.')

        return num_removed_roms

    # Resets the No-Intro status
    # 1) Remove all ROMs which does not exist.
    # 2) Set status of remaining ROMs to nointro_status = AUDIT_STATUS_NONE
    # Both launcher and roms dictionaries edited by reference.
    def _roms_reset_NoIntro_status(self, launcher, roms):
        log_info('_roms_reset_NoIntro_status() Launcher has {0} ROMs'.format(len(roms)))
        if len(roms) < 1: return

        # Step 1) Delete missing/dead ROMs
        num_removed_roms = self._roms_delete_missing_ROMs(roms)
        log_info('_roms_reset_NoIntro_status() Removed {} dead/missing ROMs'.format(num_removed_roms))

        # Step 2) Set Audit status to AUDIT_STATUS_NONE and
        #         set PClone status to PCLONE_STATUS_NONE
        log_info('_roms_reset_NoIntro_status() Resetting No-Intro status of all ROMs to None')
        for rom_id in sorted(roms.keys()):
            roms[rom_id]['nointro_status'] = AUDIT_STATUS_NONE
            roms[rom_id]['pclone_status']  = PCLONE_STATUS_NONE
        log_info('_roms_reset_NoIntro_status() Now launcher has {} ROMs'.format(len(roms)))

        # Step 3) Delete PClone index and Parent ROM list.
        roms_base_noext = launcher['roms_base_noext']
        CParent_roms_base_noext = roms_base_noext + '_index_CParent'
        PClone_roms_base_noext  = roms_base_noext + '_index_PClone'
        parents_roms_base_noext = roms_base_noext + '_parents'
        CParent_FN = g_PATHS.ROMS_DIR.pjoin(CParent_roms_base_noext + '.json')
        PClone_FN  = g_PATHS.ROMS_DIR.pjoin(PClone_roms_base_noext + '.json')
        parents_FN = g_PATHS.ROMS_DIR.pjoin(parents_roms_base_noext + '.json')
        if CParent_FN.exists():
            log_info('_roms_reset_NoIntro_status() Deleting {}'.format(CParent_FN.getPath()))
            CParent_FN.unlink()
        if PClone_FN.exists():
            log_info('_roms_reset_NoIntro_status() Deleting {}'.format(PClone_FN.getPath()))
            PClone_FN.unlink()
        if parents_FN.exists():
            log_info('_roms_reset_NoIntro_status() Deleting {}'.format(parents_FN.getPath()))
            parents_FN.unlink()

        # Step 4) Update launcher statistics and status.
        launcher['num_roms']    = len(roms)
        launcher['num_parents'] = 0
        launcher['num_clones']  = 0
        launcher['num_have']    = 0
        launcher['num_miss']    = 0
        launcher['num_unknown'] = 0
        launcher['audit_state'] = AUDIT_STATE_OFF

    # Helper function to update ROMs No-Intro status if user configured a No-Intro DAT file.
    # Dictionaries are mutable, so roms can be changed because passed by assigment.
    # This function also creates the Parent/Clone indices:
    #   1) ADDON_DATA_DIR/db_ROMs/roms_base_noext_PClone_index.json
    #   2) ADDON_DATA_DIR/db_ROMs/roms_base_noext_parents.json
    #
    # A) If there are Unkown ROMs, a fake rom with name [Unknown ROMs] and
    #    id UNKNOWN_ROMS_PARENT_ID is created. This fake ROM is the parent of all Unknown ROMs.
    #    This fake ROM is added to roms_base_noext_parents.json database.
    #    This fake ROM is not present in the main JSON ROM database.
    #
    # Both launcher and roms dictionaries updated by reference.
    #
    # Returns:
    #   True  -> ROM audit was OK
    #   False -> There was a problem with the audit.
    def _roms_update_NoIntro_status(self, launcher, roms, DAT_FN):
        __debug_progress_dialogs = False
        __debug_time_step = 0.0005

        # --- Reset the No-Intro status and removed No-Intro missing ROMs ---
        audit_have = audit_miss = audit_unknown = audit_extra = 0
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Advanced Emulator Launcher', 'Deleting Missing/Dead ROMs and clearing flags ...')
        self._roms_reset_NoIntro_status(launcher, roms)
        pDialog.update(100)
        if __debug_progress_dialogs: time.sleep(0.5)

        # --- Check if DAT file exists ---
        if not DAT_FN.exists():
            log_warning('_roms_update_NoIntro_status() Not found {}'.format(DAT_FN.getPath()))
            return False
        pDialog.update(0, 'Loading No-Intro/Redump XML DAT file ...')
        roms_nointro = audit_load_NoIntro_XML_file(DAT_FN)
        pDialog.update(100)
        if __debug_progress_dialogs: time.sleep(0.5)
        if not roms_nointro:
            log_warning('_roms_update_NoIntro_status() Error loading {}'.format(DAT_FN.getPath()))
            return False

        # --- Remove BIOSes from No-Intro ROMs ---
        if self.settings['scan_ignore_bios']:
            log_info('_roms_update_NoIntro_status() Removing BIOSes from No-Intro ROMs ...')
            pDialog.update(0, 'Removing BIOSes from No-Intro ROMs ...')
            num_items = len(roms_nointro)
            item_counter = 0
            filtered_roms_nointro = {}
            for rom_id in roms_nointro:
                rom = roms_nointro[rom_id]
                BIOS_str_list = re.findall('\[BIOS\]', rom['name'])
                if not BIOS_str_list:
                    filtered_roms_nointro[rom_id] = rom
                else:
                    log_debug('_roms_update_NoIntro_status() Removed BIOS "{}"'.format(rom['name']))
                item_counter += 1
                pDialog.update((item_counter*100)/num_items)
                if __debug_progress_dialogs: time.sleep(__debug_time_step)
            roms_nointro = filtered_roms_nointro
            pDialog.update(100)
        else:
            log_info('_roms_update_NoIntro_status() User wants to include BIOSes.')

        # --- Put No-Intro ROM names in a set ---
        # >> Set is the fastest Python container for searching elements (implements hashed search).
        # >> No-Intro names include tags
        pDialog.update(0, 'Creating No-Intro and ROM sets ...')
        roms_nointro_set = set(roms_nointro.keys())
        roms_set = set()
        for rom_id in roms:
            # >> Use the ROM basename.
            ROMFileName = FileName(roms[rom_id]['filename'])
            roms_set.add(ROMFileName.getBase_noext())
        pDialog.update(100)
        if __debug_progress_dialogs: time.sleep(0.5)

        # --- Traverse Launcher ROMs and check if they are in the No-Intro ROMs list ---
        pDialog.update(0, 'Audit Step 1/4: Checking Have and Unknown ROMs ...')
        num_items = len(roms)
        item_counter = 0
        for rom_id in roms:
            ROMFileName = FileName(roms[rom_id]['filename'])
            if roms[rom_id]['i_extra_ROM']:
                roms[rom_id]['nointro_status'] = AUDIT_STATUS_EXTRA
                audit_extra += 1
                # log_debug('_roms_update_NoIntro_status() EXTRA   "{}"'.format(ROMFileName.getBase_noext()))
            elif ROMFileName.getBase_noext() in roms_nointro_set:
                roms[rom_id]['nointro_status'] = AUDIT_STATUS_HAVE
                audit_have += 1
                # log_debug('_roms_update_NoIntro_status() HAVE    "{}"'.format(ROMFileName.getBase_noext()))
            else:
                roms[rom_id]['nointro_status'] = AUDIT_STATUS_UNKNOWN
                audit_unknown += 1
                # log_debug('_roms_update_NoIntro_status() UNKNOWN "{}"'.format(ROMFileName.getBase_noext()))
            item_counter += 1
            pDialog.update((item_counter*100)/num_items)
            if __debug_progress_dialogs: time.sleep(__debug_time_step)
        pDialog.update(100)

        # --- Mark Launcher dead ROMs as Missing ---
        pDialog.update(0, 'Audit Step 2/4: Checking Missing ROMs ...')
        num_items = len(roms)
        item_counter = 0
        for rom_id in roms:
            ROMFileName = FileName(roms[rom_id]['filename'])
            if not ROMFileName.exists():
                roms[rom_id]['nointro_status'] = AUDIT_STATUS_MISS
                audit_miss += 1
                # log_debug('_roms_update_NoIntro_status() MISSING "{0}"'.format(ROMFileName.getBase_noext()))
            item_counter += 1
            pDialog.update((item_counter*100)/num_items)
            if __debug_progress_dialogs: time.sleep(__debug_time_step)
        pDialog.update(100)

        # --- Now add Missing ROMs to Launcher ---
        # Traverse the No-Intro set and add the No-Intro ROM if it's not in the Launcher
        # Added/Missing ROMs have their own romID.
        pDialog.update(0, 'Audit Step 3/4: Adding Missing ROMs ...')
        num_items = len(roms_nointro_set)
        item_counter = 0
        ROMPath = FileName(launcher['rompath'])
        for nointro_rom in sorted(roms_nointro_set):
            # log_debug('_roms_update_NoIntro_status() Checking "{0}"'.format(nointro_rom))
            if nointro_rom not in roms_set:
                # Add new "fake" missing ROM. This ROM cannot be launched!
                # Added ROMs have special extension .nointro
                rom = fs_new_rom()
                rom_id                = misc_generate_random_SID()
                rom['id']             = rom_id
                rom['filename']       = ROMPath.pjoin(nointro_rom + '.nointro').getOriginalPath()
                rom['m_name']         = nointro_rom
                rom['nointro_status'] = AUDIT_STATUS_MISS
                roms[rom_id] = rom
                audit_miss += 1
                # log_debug('_roms_update_NoIntro_status() ADDED   "{0}"'.format(rom['m_name']))
                # log_debug('_roms_update_NoIntro_status()    OP   "{0}"'.format(rom['filename']))
            item_counter += 1
            pDialog.update((item_counter*100)/num_items)
            if __debug_progress_dialogs: time.sleep(__debug_time_step)
        pDialog.update(100)

        # --- Detect if the DAT file has PClone information or not ---
        dat_pclone_dic = audit_make_NoIntro_PClone_dic(roms_nointro)
        num_dat_clones = 0
        for parent_name in dat_pclone_dic: num_dat_clones += len(dat_pclone_dic[parent_name])
        log_verb('No-Intro/Redump DAT has {0} clone ROMs'.format(num_dat_clones))

        # --- Generate main pclone dictionary ---
        # >> audit_unknown_roms is an int of list = ['Parents', 'Clones']
        # log_debug("settings['audit_unknown_roms'] = {0}".format(self.settings['audit_unknown_roms']))
        unknown_ROMs_are_parents = True if self.settings['audit_unknown_roms'] == 0 else False
        log_debug('unknown_ROMs_are_parents = {0}'.format(unknown_ROMs_are_parents))
        # if num_dat_clones == 0 and self.settings['audit_create_pclone_groups']:
        #     # --- If DAT has no PClone information and user want then generate filename-based PClone groups ---
        #     # >> This feature is taken from NARS (NARS Advanced ROM Sorting)
        #     log_verb('Generating filename-based Parent/Clone groups')
        #     pDialog.update(0, 'Building filename-based Parent/Clone index ...')
        #     roms_pclone_index = audit_generate_filename_PClone_index(roms, roms_nointro, unknown_ROMs_are_parents)
        #     pDialog.update(100)
        #     if __debug_progress_dialogs: time.sleep(0.5)
        # else:
        #     # --- Make a DAT-based Parent/Clone index ---
        #     # >> Here we build a roms_pclone_index with info from the DAT file. 2 issues:
        #     # >> A) Redump DATs do not have cloneof information.
        #     # >> B) Also, it is at this point where a region custom parent may be chosen instead of
        #     # >>    the default one.
        #     log_verb('Generating DAT-based Parent/Clone groups')
        #     pDialog.update(0, 'Building DAT-based Parent/Clone index ...')
        #     roms_pclone_index = audit_generate_DAT_PClone_index(roms, roms_nointro, unknown_ROMs_are_parents)
        #     pDialog.update(100)
        #     if __debug_progress_dialogs: time.sleep(0.5)

        # --- Make a DAT-based Parent/Clone index ---
        # >> For 0.9.7 only use the DAT to make the PClone groups. In 0.9.8 decouple the audit
        # >> code from the PClone generation code.
        log_verb('Generating DAT-based Parent/Clone groups')
        pDialog.update(0, 'Building DAT-based Parent/Clone index ...')
        roms_pclone_index = audit_generate_DAT_PClone_index(roms, roms_nointro, unknown_ROMs_are_parents)
        pDialog.update(100)
        if __debug_progress_dialogs: time.sleep(0.5)

        # --- Make a Clone/Parent index ---
        # >> This is made exclusively from the Parent/Clone index
        pDialog.update(0, 'Building Clone/Parent index ...')
        clone_parent_dic = {}
        for parent_id in roms_pclone_index:
            for clone_id in roms_pclone_index[parent_id]:
                clone_parent_dic[clone_id] = parent_id
        pDialog.update(100)
        if __debug_progress_dialogs: time.sleep(0.5)

        # --- Set ROMs pclone_status flag and update launcher statistics ---
        pDialog.update(0, 'Audit Step 4/4: Setting Parent/Clone status and cloneof fields...')
        num_items = len(roms)
        item_counter = 0
        audit_parents = audit_clones = 0
        for rom_id in roms:
            if rom_id in roms_pclone_index:
                roms[rom_id]['pclone_status'] = PCLONE_STATUS_PARENT
                audit_parents += 1
            else:
                roms[rom_id]['cloneof'] = clone_parent_dic[rom_id]
                roms[rom_id]['pclone_status'] = PCLONE_STATUS_CLONE
                audit_clones += 1
            item_counter += 1
            pDialog.update((item_counter*100)/num_items)
            if __debug_progress_dialogs: time.sleep(__debug_time_step)
        pDialog.update(100)
        launcher['num_roms']    = len(roms)
        launcher['num_parents'] = audit_parents
        launcher['num_clones']  = audit_clones
        launcher['num_have']    = audit_have
        launcher['num_miss']    = audit_miss
        launcher['num_unknown'] = audit_unknown
        launcher['num_extra']   = audit_extra
        launcher['audit_state'] = AUDIT_STATE_ON

        # --- Make a Parent only ROM list and save JSON ---
        # This is to speed up rendering of launchers in Parent/Clone display mode.
        pDialog.update(0, 'Building Parent/Clone index and Parent dictionary ...')
        parent_roms = audit_generate_parent_ROMs_dic(roms, roms_pclone_index)
        pDialog.update(100)
        if __debug_progress_dialogs: time.sleep(0.5)

        # --- Save JSON databases ---
        pDialog.update(0, 'Saving NO-Intro/Redump JSON databases ...')
        fs_write_JSON_file(g_PATHS.ROMS_DIR, launcher['roms_base_noext'] + '_index_PClone', roms_pclone_index)
        pDialog.update(30)
        fs_write_JSON_file(g_PATHS.ROMS_DIR, launcher['roms_base_noext'] + '_index_CParent', clone_parent_dic)
        pDialog.update(60)
        fs_write_JSON_file(g_PATHS.ROMS_DIR, launcher['roms_base_noext'] + '_parents', parent_roms)
        pDialog.update(100)
        pDialog.close()

        # --- Update launcher number of ROMs ---
        self.audit_have    = audit_have
        self.audit_miss    = audit_miss
        self.audit_unknown = audit_unknown
        self.audit_extra   = audit_extra
        self.audit_total   = len(roms)
        self.audit_parents = audit_parents
        self.audit_clones  = audit_clones

        # --- Report ---
        log_info('********** No-Intro/Redump audit finished. Report ***********')
        log_info('Have ROMs    {:6d}'.format(self.audit_have))
        log_info('Miss ROMs    {:6d}'.format(self.audit_miss))
        log_info('Unknown ROMs {:6d}'.format(self.audit_unknown))
        log_info('Extra ROMs   {:6d}'.format(self.audit_extra))
        log_info('Total ROMs   {:6d}'.format(self.audit_total))
        log_info('Parent ROMs  {:6d}'.format(self.audit_parents))
        log_info('Clone ROMs   {:6d}'.format(self.audit_clones))

        return True

    # DEPRCATED FUNCTION. Not used anymore and will be removed soon.
    #
    # Manually add a new ROM instead of a recursive scan.
    #   A) User chooses a ROM file
    #   B) Title is formatted. No metadata scraping.
    #   C) Thumb and fanart are searched locally only.
    # Later user can edit this ROM if he wants.
    def _roms_add_new_rom(self, launcherID):
        # --- Grab launcher information ---
        launcher = self.launchers[launcherID]
        romext   = launcher['romext']
        rompath  = launcher['rompath']
        log_verb('_roms_add_new_rom() launcher name "{0}"'.format(launcher['m_name']))

        # --- Load ROMs for this launcher ---
        roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, launcher)

        # --- Choose ROM file ---
        dialog = xbmcgui.Dialog()
        extensions = '.' + romext.replace('|', '|.')
        romfile = dialog.browse(1, 'Select the ROM file', 'files', extensions, False, False, rompath)
        if not romfile: return
        log_verb('_roms_add_new_rom() romfile "{0}"'.format(romfile))

        # --- Format title ---
        scan_clean_tags = self.settings['scan_clean_tags']
        ROMFile = FileName(romfile)
        rom_name = text_format_ROM_title(ROMFile.getBase_noext(), scan_clean_tags)

        # ~~~ Check asset dirs and disable scanning for unset dirs ~~~
        # >> Do not warn about unconfigured dirs here
        (enabled_asset_list, unconfigured_name_list) = asset_get_configured_dir_list(launcher)

        # ~~~ Ensure there is no duplicate asset dirs ~~~
        duplicated_name_list = asset_get_duplicated_dir_list(launcher)
        if duplicated_name_list:
            duplicated_asset_srt = ', '.join(duplicated_name_list)
            log_debug('_roms_add_new_rom() Duplicated asset dirs: {0}'.format(duplicated_asset_srt))
            kodi_dialog_OK('Duplicated asset directories: {0}. '.format(duplicated_asset_srt) +
                           'Change asset directories before continuing.')
            return
        else:
            log_debug('_roms_add_new_rom() No duplicated asset dirs found')

        # ~~~ Search for local artwork/assets ~~~
        local_asset_list = assets_search_local_assets(launcher, ROMFile, enabled_asset_list)

        # --- Create ROM data structure ---
        romdata = fs_new_rom()
        romdata['id']          = misc_generate_random_SID()
        romdata['filename']    = ROMFile.getOriginalPath()
        romdata['m_name']      = rom_name
        for index, asset_kind in enumerate(ROM_ASSET_ID_LIST):
            A = assets_get_info_scheme(asset_kind)
            romdata[A.key] = local_asset_list[index]
        roms[romdata['id']] = romdata
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
        if launcher['audit_state'] == AUDIT_STATE_ON:
            log_info('ROM Audit is ON. Refreshing ROM audit ...')
            nointro_xml_FN = self._roms_set_NoIntro_DAT(launcher)
            if not self._roms_update_NoIntro_status(launcher, roms, nointro_xml_FN):
                kodi_dialog_OK('Error auditing ROMs. XML DAT file unset.')
        else:
            log_info('ROM Audit if OFF. Do not refresh ROM Audit.')

        # ~~~ Save ROMs XML file ~~~
        # Also save categories/launchers to update timestamp.
        launcher['num_roms'] = len(roms)
        launcher['timestamp_launcher'] = time.time()
        fs_write_ROMs_JSON(g_PATHS.ROMS_DIR, launcher, roms)
        fs_write_catfile(g_PATHS.CATEGORIES_FILE_PATH, self.categories, self.launchers)
        kodi_refresh_container()
        kodi_notify('Added ROM. Launcher has now {} ROMs'.format(len(roms)))

    #
    # ROM scanner. Called when user chooses Launcher CM, "Add ROMs" -> "Scan for new ROMs"
    #
    def _roms_import_roms(self, launcherID):
        log_debug('========== _roms_import_roms() BEGIN ==================================================')

        # --- Get information from launcher ---
        launcher           = self.launchers[launcherID]
        rom_path           = FileName(launcher['rompath'])
        launcher_exts      = launcher['romext']
        rom_extra_path     = FileName(launcher['romextrapath'])
        launcher_multidisc = launcher['multidisc']
        log_info('_roms_import_roms() Starting ROM scanner ...')
        log_info('Launcher name  "{}"'.format(launcher['m_name']))
        log_info('Launcher ID    "{}"'.format(launcher['id']))
        log_info('ROM path       "{}"'.format(rom_path.getPath()))
        log_info('ROM exts       "{}"'.format(launcher_exts))
        log_info('ROM extra path "{}"'.format(rom_extra_path.getPath()))
        log_info('Platform       "{}"'.format(launcher['platform']))
        log_info('Multidisc      {}'.format(launcher_multidisc))

        # --- Open ROM scanner report file ---
        launcher_report_FN = g_PATHS.REPORTS_DIR.pjoin(launcher['roms_base_noext'] + '_report.txt')
        log_info('Report file OP "{}"'.format(launcher_report_FN.getOriginalPath()))
        log_info('Report file  P "{}"'.format(launcher_report_FN.getPath()))
        report_fobj = open(launcher_report_FN.getPath(), "w")
        report_fobj.write('*** Starting ROM scanner ... ***\n'.format())
        report_fobj.write('Launcher name  "{}"\n'.format(launcher['m_name']))
        report_fobj.write('Launcher ID    "{}"\n'.format(launcher['id']))
        report_fobj.write('ROM path       "{}"\n'.format(rom_path.getPath()))
        report_fobj.write('ROM ext        "{}"\n'.format(launcher_exts))
        report_fobj.write('ROM extra path "{}"\n'.format(rom_extra_path.getPath()))
        report_fobj.write('Platform       "{}"\n'.format(launcher['platform']))

        # Check if there is an XML for this launcher. If so, load it.
        # If file does not exist or is empty then return an empty dictionary.
        report_fobj.write('Loading launcher ROMs ...\n')
        roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, launcher)
        num_roms = len(roms)
        report_fobj.write('{} ROMs currently in database\n'.format(num_roms))
        log_info('Launcher ROM database contain {} items'.format(num_roms))

        # --- Progress dialog ---
        pdialog_verbose = True
        pdialog = KodiProgressDialog()

        # --- Load metadata/asset scrapers --------------------------------------------------------
        g_scraper_factory = ScraperFactory(g_PATHS, self.settings)
        scraper_strategy = g_scraper_factory.create_scanner(launcher)
        scraper_strategy.scanner_set_progress_dialog(pdialog, pdialog_verbose)
        # Check if scraper is ready for operation. Otherwise disable it internally.
        scraper_strategy.scanner_check_before_scraping()

        # Create ROMFilter object. Loads filter databases for MAME.
        romfilter = FilterROM(g_PATHS, self.settings, launcher['platform'])

        # --- Assets/artwork stuff ----------------------------------------------------------------
        # Ensure there is no duplicate asset dirs. Abort scanning of assets if duplicate dirs found.
        log_debug('Checking for duplicated artwork directories...')
        duplicated_name_list = asset_get_duplicated_dir_list(launcher)
        if duplicated_name_list:
            duplicated_asset_srt = ', '.join(duplicated_name_list)
            log_info('Duplicated asset dirs: {}'.format(duplicated_asset_srt))
            kodi_dialog_OK('Duplicated asset directories: {}. '.format(duplicated_asset_srt) +
                           'Change asset directories before continuing.')
            return
        else:
            log_info('No duplicated asset dirs found')

        # --- Check asset dirs and disable scanning for unset dirs ---
        log_debug('Checking for unset artwork directories...')
        scraper_strategy.scanner_check_launcher_unset_asset_dirs()
        if scraper_strategy.unconfigured_name_list:
            unconfigured_asset_srt = ', '.join(scraper_strategy.unconfigured_name_list)
            kodi_dialog_OK(
                'Assets directories not set: {}. '.format(unconfigured_asset_srt) +
                'Asset scanner will be disabled for this/those.')

        # --- Create a cache of assets ---
        # misc_add_file_cache() creates a set with all files in a given directory.
        # That set is stored in a function internal cache associated with the path.
        # Files in the cache can be searched with misc_search_file_cache()
        log_info('Scanning and caching files in asset directories...')
        pdialog.startProgress('Scanning files in asset directories...', len(ROM_ASSET_ID_LIST))
        for i, asset_kind in enumerate(ROM_ASSET_ID_LIST):
            pdialog.updateProgress(i)
            AInfo = assets_get_info_scheme(asset_kind)
            misc_add_file_cache(launcher[AInfo.path_key])
        pdialog.endProgress()

        # --- Remove dead ROM entries ------------------------------------------------------------
        log_info('Removing dead ROMs...'.format())
        report_fobj.write('Removing dead ROMs ...\n')
        num_removed_roms = 0
        if num_roms > 0:
            pdialog.startProgress('Checking for dead ROMs ...', num_roms)
            i = 0
            for key in sorted(roms.keys()):
                pdialog.updateProgress(i)
                i += 1
                log_debug('Searching {0}'.format(roms[key]['filename']))
                fileName = FileName(roms[key]['filename'])
                if not fileName.exists():
                    log_debug('Deleting from DB {0}'.format(roms[key]['filename']))
                    del roms[key]
                    num_removed_roms += 1
            pdialog.endProgress()
            if num_removed_roms > 0:
                kodi_notify('{0} dead ROMs removed successfully'.format(num_removed_roms))
                log_info('{0} dead ROMs removed successfully'.format(num_removed_roms))
            else:
                log_info('No dead ROMs found')
        else:
            log_info('Launcher is empty. No dead ROM check.')

        # --- Scan all files in ROM path (mask *.*) and put them in a list -----------------------
        pdialog.startProgress('Scanning and caching files in ROM path ...')
        files = []
        log_info('Scanning files in {}'.format(rom_path.getPath()))
        report_fobj.write('Scanning files ...\n')
        report_fobj.write('Directory {}\n'.format(rom_path.getPath()))
        if self.settings['scan_recursive']:
            log_info('Recursive scan activated')
            files = rom_path.recursiveScanFilesInPath('*.*')
        else:
            log_info('Recursive scan not activated')
            files = rom_path.scanFilesInPath('*.*')
        log_info('File scanner found {} files'.format(len(files)))
        report_fobj.write('File scanner found {} files\n'.format(len(files)))
        pdialog.endProgress()

        # --- Scan all files in extra ROM path ---------------------------------------------------
        extra_files = []
        if launcher['romextrapath']:
            log_info('Scanning files in extra ROM path.')
            pdialog.startProgress('Scanning and caching files in extra ROM path ...')
            log_info('Scanning files in {}'.format(rom_extra_path.getPath()))
            report_fobj.write('Scanning files ...\n')
            report_fobj.write('Directory {}\n'.format(rom_extra_path.getPath()))
            if self.settings['scan_recursive']:
                log_info('Recursive scan activated')
                extra_files = rom_extra_path.recursiveScanFilesInPath('*.*')
            else:
                log_info('Recursive scan not activated')
                extra_files = rom_extra_path.scanFilesInPath('*.*')
            log_info('File scanner found {} files'.format(len(extra_files)))
            report_fobj.write('File scanner found {} files\n'.format(len(extra_files)))
            pdialog.endProgress()
        else:
            log_info('Extra ROM path empty. Skipping scanning.')

        # --- Prepare list of files to be processed ----------------------------------------------
        # List has tuples (filename, extra_ROM_flag). List already sorted alphabetically.
        file_list = []
        for f_path in sorted(files): file_list.append((f_path, False))
        for f_path in sorted(extra_files): file_list.append((f_path, True))

        # --- Now go processing file by file -----------------------------------------------------
        pdialog.startProgress('Processing ROMs...', len(file_list))
        log_info('============================== Processing ROMs ===============================')
        report_fobj.write('Processing files ...\n')
        num_new_roms = 0
        num_files_checked = 0
        for f_path, extra_ROM_flag in file_list:
            # --- Get all file name combinations ---
            ROM = FileName(f_path)
            log_debug('------------------------------ Processing cached file -------------------')
            log_debug('ROM.getPath()         "{}"'.format(ROM.getPath()))
            log_debug('ROM.getOriginalPath() "{}"'.format(ROM.getOriginalPath()))
            # log_debug('ROM.getPath_noext()   "{}"'.format(ROM.getPath_noext()))
            # log_debug('ROM.getDir()          "{}"'.format(ROM.getDir()))
            # log_debug('ROM.getBase()         "{}"'.format(ROM.getBase()))
            # log_debug('ROM.getBase_noext()   "{}"'.format(ROM.getBase_noext()))
            # log_debug('ROM.getExt()          "{}"'.format(ROM.getExt()))
            report_fobj.write('>>> {}\n'.format(ROM.getPath()))

            # Update progress dialog.
            file_text = 'ROM [COLOR orange]{}[/COLOR]'.format(ROM.getBase())
            if not pdialog_verbose:
                pdialog.updateProgress(num_files_checked, file_text)
            else:
                pdialog.updateProgress(num_files_checked, file_text, 'Checking if has ROM extension...')
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

            # --- Check if ROM belongs to a multidisc set ---
            MultiDiscInROMs = False
            MDSet = text_get_multidisc_info(ROM)
            if MDSet.isMultiDisc and launcher_multidisc:
                log_debug('ROM belongs to a multidisc set.')
                log_debug('isMultiDisc "{0}"'.format(MDSet.isMultiDisc))
                log_debug('setName     "{0}"'.format(MDSet.setName))
                log_debug('discName    "{0}"'.format(MDSet.discName))
                log_debug('extension   "{0}"'.format(MDSet.extension))
                log_debug('order       "{0}"'.format(MDSet.order))
                report_fobj.write('  ROM belongs to a multidisc set.\n')

                # >> Check if the set is already in launcher ROMs.
                MultiDisc_rom_id = None
                for rom_id, rom_dic in roms.items():
                    temp_FN = FileName(rom_dic['filename'])
                    if temp_FN.getBase() == MDSet.setName:
                        MultiDiscInROMs  = True
                        MultiDisc_rom_id = rom_id
                        break
                log_debug('MultiDiscInROMs is {0}'.format(MultiDiscInROMs))

                # >> If the set is not in the ROMs then this ROM is the first of the set.
                # >> Add the set
                if not MultiDiscInROMs:
                    log_debug('First ROM in the multidisc set.')
                    # Manipulate ROM so filename is the name of the set.
                    ROM_original = ROM
                    ROM_dir = FileName(ROM.getDir())
                    ROM_temp = ROM_dir.pjoin(MDSet.setName)
                    log_debug('ROM_temp OP "{0}"'.format(ROM_temp.getOriginalPath()))
                    log_debug('ROM_temp  P "{0}"'.format(ROM_temp.getPath()))
                    log_debug('ROM_original OP "{0}"'.format(ROM_original.getOriginalPath()))
                    log_debug('ROM_original  P "{0}"'.format(ROM_original.getPath()))
                    ROM = ROM_temp
                # >> If set already in ROMs, just add this disk into the set disks field.
                else:
                    log_debug('Adding additional disk "{0}" to set'.format(MDSet.discName))
                    roms[MultiDisc_rom_id]['disks'].append(MDSet.discName)
                    # >> Reorder disks like Disk 1, Disk 2, ...

                    # >> Process next file
                    log_debug('Processing next file ...')
                    continue
            elif MDSet.isMultiDisc and not launcher_multidisc:
                log_debug('ROM belongs to a multidisc set but Multidisc support is disabled.')
                report_fobj.write('  ROM belongs to a multidisc set but Multidisc support is disabled.\n')
            else:
                log_debug('ROM does not belong to a multidisc set.')
                report_fobj.write('  ROM does not belong to a multidisc set.\n')

            # --- If ROM already in DB then skip it ---
            # Linear search is slow but I don't care for now.
            ROM_in_launcher_DB = False
            for rom_id in roms:
                if roms[rom_id]['filename'] == f_path:
                    ROM_in_launcher_DB = True
                    break
            if ROM_in_launcher_DB:
                log_debug('File already into launcher ROM list. Skipping file.')
                report_fobj.write('  File already into launcher ROM list. Skipping file.\n')
                continue
            else:
                log_debug('File not in launcher ROM list. Processing it ...')
                report_fobj.write('  File not in launcher ROM list. Processing it ...\n')

            # --- Ignore BIOS ROMs ---
            if romfilter.ROM_is_filtered(ROM.getBaseNoExt()):
                log_debug('ROM filtered. Skipping ROM processing.')
                continue

            # --- Create new ROM and process metadata and assets ---------------------------------
            romdata = fs_new_rom()
            romdata['id'] = misc_generate_random_SID()
            romdata['filename'] = ROM.getOriginalPath()
            romdata['i_extra_ROM'] = extra_ROM_flag
            ROM_checksums = ROM_original if MDSet.isMultiDisc and launcher_multidisc else ROM
            scraper_strategy.scanner_process_ROM_begin(romdata, ROM, ROM_checksums)
            scraper_strategy.scanner_process_ROM_metadata(romdata, ROM)
            scraper_strategy.scanner_process_ROM_assets(romdata, ROM)

            # --- Add ROM to database ------------------------------------------------------------
            roms[romdata['id']] = romdata
            num_new_roms += 1

            # --- This was the first ROM in a multidisc set ---
            if launcher_multidisc and MDSet.isMultiDisc and not MultiDiscInROMs:
                log_info('Adding to ROMs dic first disk "{0}"'.format(MDSet.discName))
                roms[romdata['id']]['disks'].append(MDSet.discName)

            # --- Check if user pressed the cancel button ---
            if pdialog.isCanceled():
                pdialog.endProgress()
                kodi_dialog_OK('Stopping ROM scanning. No changes have been made.')
                log_info('User pressed Cancel button when scanning ROMs. ROM scanning stopped.')
                # Flush scraper disk caches.
                g_scraper_factory.destroy_scanner(pdialog)
                return
        pdialog.endProgress()
        # Flush scraper disk caches.
        g_scraper_factory.destroy_scanner(pdialog)

        # --- Scanner report ---
        log_info('******************** ROM scanner finished. Report ********************')
        log_info('Removed dead ROMs {0:6d}'.format(num_removed_roms))
        log_info('Files checked     {0:6d}'.format(num_files_checked))
        log_info('New added ROMs    {0:6d}'.format(num_new_roms))
        report_fobj.write('******************** ROM scanner finished ********************\n')
        report_fobj.write('Removed dead ROMs {0:6d}\n'.format(num_removed_roms))
        report_fobj.write('Files checked     {0:6d}\n'.format(num_files_checked))
        report_fobj.write('New added ROMs    {0:6d}\n'.format(num_new_roms))

        if not roms:
            report_fobj.write('WARNING The ROM scanner found no ROMs. Launcher is empty.\n')
            report_fobj.close()
            kodi_dialog_OK((
                'The scanner found no ROMs! Make sure launcher directory and file '
                'extensions are correct.'))
            return

        # --- If we have a No-Intro XML then audit roms after scanning ----------------------------
        if launcher['audit_state'] == AUDIT_STATE_ON:
            log_info('No-Intro/Redump is ON. Starting ROM audit ...')
            report_fobj.write('No-Intro/Redump DAT configured. Starting ROM audit ...\n')
            nointro_xml_FN = self._roms_set_NoIntro_DAT(launcher)
            # Error printed with a OK dialog inside this function.
            if nointro_xml_FN is not None:
                log_debug('Using DAT "{}"'.format(nointro_xml_FN.getPath()))
                if self._roms_update_NoIntro_status(launcher, roms, nointro_xml_FN):
                    fs_write_ROMs_JSON(g_PATHS.ROMS_DIR, self.launchers[launcherID], roms)
                    kodi_notify(
                        'ROM scanner and audit finished. '
                        'Have {} / Miss {} / Unknown {}'.format(self.audit_have, self.audit_miss, self.audit_unknown))
                    # _roms_update_NoIntro_status() already prints and audit report on Kodi log
                    report_fobj.write('********** No-Intro/Redump audit finished. Report ***********\n')
                    report_fobj.write('Have ROMs    {0:6d}\n'.format(self.audit_have))
                    report_fobj.write('Miss ROMs    {0:6d}\n'.format(self.audit_miss))
                    report_fobj.write('Unknown ROMs {0:6d}\n'.format(self.audit_unknown))
                    report_fobj.write('Total ROMs   {0:6d}\n'.format(self.audit_total))
                    report_fobj.write('Parent ROMs  {0:6d}\n'.format(self.audit_parents))
                    report_fobj.write('Clone ROMs   {0:6d}\n'.format(self.audit_clones))
                else:
                    kodi_notify_warn('Error auditing ROMs')
            else:
                log_error('Error finding No-Intro/Redump DAT file.')
                log_error('Audit not done.')
                kodi_notify_warn('Error finding No-Intro/Redump DAT file')
        else:
            log_info('ROM Audit state is OFF. Do not audit ROMs.')
            report_fobj.write('ROM Audit state is OFF. Do not audit ROMs.\n')
            if num_new_roms == 0:
                kodi_notify('Added no new ROMs. Launcher has {} ROMs'.format(len(roms)))
            else:
                kodi_notify('Added {} new ROMs'.format(num_new_roms))

        # --- Close ROM scanner report file ---
        report_fobj.write('*** END of the ROM scanner report ***\n')
        report_fobj.close()

        # ~~~ Save ROMs XML file ~~~
        # Also save categories/launchers to update timestamp.
        # Update Launcher timestamp to update VLaunchers and reports.
        self.launchers[launcherID]['num_roms'] = len(roms)
        self.launchers[launcherID]['timestamp_launcher'] = time.time()
        pdialog.startProgress('Saving ROM JSON database ...', 100)
        fs_write_catfile(g_PATHS.CATEGORIES_FILE_PATH, self.categories, self.launchers)
        pdialog.updateProgress(25)
        fs_write_ROMs_JSON(g_PATHS.ROMS_DIR, launcher, roms)
        pdialog.endProgress()
        kodi_refresh_container()

    #
    # Edit category/launcher/rom asset.
    #
    # When editing ROMs optional parameter launcher_dic is required.
    # Caller is responsible for saving the Categories/Launchers/ROMs.
    # If image is changed container should be updated so the user sees new image instantly.
    # object_dic is edited by assigment.
    # A ROM in Favourites has categoryID = VCATEGORY_FAVOURITES_ID.
    # A ROM in a collection categoryID = VCATEGORY_COLLECTIONS_ID.
    #
    # --- Returns ---
    # True   Changes made. Categories/Launchers/ROMs must be saved and container updated
    # False  No changes were made. No necessary to refresh container
    #
    def _gui_edit_asset(self, object_kind, asset_ID, object_dic, categoryID = '', launcherID = ''):
        # --- Get asset object information ---
        AInfo = assets_get_info_scheme(asset_ID)
        if object_kind == KIND_CATEGORY:
            # --- Grab asset information for editing ---
            object_name = 'Category'
            asset_directory = FileName(self.settings['categories_asset_dir'])
            asset_path_noext = assets_get_path_noext_SUFIX(
                AInfo, asset_directory, object_dic['m_name'], object_dic['id'])
            log_info('_gui_edit_asset() Editing Category "{0}"'.format(AInfo.name))
            log_info('_gui_edit_asset() ID {0}'.format(object_dic['id']))
            log_debug('_gui_edit_asset() asset_directory  "{0}"'.format(asset_directory.getOriginalPath()))
            log_debug('_gui_edit_asset() asset_path_noext "{0}"'.format(asset_path_noext.getOriginalPath()))
            if not asset_directory.isdir():
                kodi_dialog_OK('Directory to store Category artwork not configured or not found. '
                               'Configure it before you can edit artwork.')
                return False

        elif object_kind == KIND_COLLECTION:
            # --- Grab asset information for editing ---
            object_name = 'Collection'
            asset_directory = FileName(self.settings['collections_asset_dir'])
            asset_path_noext = assets_get_path_noext_SUFIX(
                AInfo, asset_directory, object_dic['m_name'], object_dic['id'])
            log_info('_gui_edit_asset() Editing Collection "{}"'.format(AInfo.name))
            log_info('_gui_edit_asset() ID {}'.format(object_dic['id']))
            log_debug('_gui_edit_asset() asset_directory  "{}"'.format(asset_directory.getOriginalPath()))
            log_debug('_gui_edit_asset() asset_path_noext "{}"'.format(asset_path_noext.getOriginalPath()))
            if not asset_directory.isdir():
                kodi_dialog_OK('Directory to store Collection artwork not configured or not found. '
                               'Configure it before you can edit artwork.')
                return False

        elif object_kind == KIND_LAUNCHER:
            # --- Grab asset information for editing ---
            object_name = 'Launcher'
            asset_directory = FileName(self.settings['launchers_asset_dir'])
            asset_path_noext = assets_get_path_noext_SUFIX(
                AInfo, asset_directory, object_dic['m_name'], object_dic['id'])
            log_info('_gui_edit_asset() Editing Launcher "{0}"'.format(AInfo.name))
            log_info('_gui_edit_asset() ID {0}'.format(object_dic['id']))
            log_debug('_gui_edit_asset() asset_directory  "{0}"'.format(asset_directory.getOriginalPath()))
            log_debug('_gui_edit_asset() asset_path_noext "{0}"'.format(asset_path_noext.getOriginalPath()))
            if not asset_directory.isdir():
                kodi_dialog_OK('Directory to store Launcher artwork not configured or not found. '
                               'Configure it before you can edit artwork.')
                return False

        elif object_kind == KIND_ROM:
            # --- Grab asset information for editing ---
            object_name = 'ROM'
            ROMfile = FileName(object_dic['filename'])
            if object_dic['disks']:
                ROM_checksums_FN = FileName(ROMfile.getDir()).pjoin(object_dic['disks'][0])
            else:
                ROM_checksums_FN = ROMfile
            if categoryID == VCATEGORY_FAVOURITES_ID:
                log_info('_gui_edit_asset() ROM is in Favourites')
                asset_directory  = FileName(self.settings['favourites_asset_dir'])
                platform         = object_dic['platform']
                asset_path_noext = assets_get_path_noext_SUFIX(
                    AInfo, asset_directory, ROMfile.getBase_noext(), object_dic['id'])
            elif categoryID == VCATEGORY_COLLECTIONS_ID:
                log_info('_gui_edit_asset() ROM is in Collection')
                asset_directory  = FileName(self.settings['collections_asset_dir'])
                platform = object_dic['platform']
                new_asset_basename = assets_get_collection_asset_basename(
                    AInfo, ROMfile.getBase_noext(), platform, '.png')
                new_asset_basename_FN = FileName(new_asset_basename)
                asset_path_noext = asset_directory.pjoin(new_asset_basename_FN.getBase_noext())
            else:
                log_info('_gui_edit_asset() ROM is in Launcher id {0}'.format(launcherID))
                launcher         = self.launchers[launcherID]
                asset_directory  = FileName(launcher[AInfo.path_key])
                platform         = launcher['platform']
                asset_path_noext = assets_get_path_noext_DIR(AInfo, asset_directory, ROMfile)
            current_asset_FN = FileName(object_dic[AInfo.key])
            log_info('_gui_edit_asset() Editing ROM {0}'.format(AInfo.name))
            log_info('_gui_edit_asset() ROM ID {0}'.format(object_dic['id']))
            log_debug('_gui_edit_asset() asset_directory  "{0}"'.format(asset_directory.getOriginalPath()))
            log_debug('_gui_edit_asset() asset_path_noext "{0}"'.format(asset_path_noext.getOriginalPath()))
            log_debug('_gui_edit_asset() current_asset_FN "{0}"'.format(current_asset_FN.getOriginalPath()))
            log_debug('_gui_edit_asset() platform         "{0}"'.format(platform))

            # --- Do not edit asset if asset directory not configured ---
            if not asset_directory.isdir():
                kodi_dialog_OK(
                    'Directory to store {0} not configured or not found. '.format(AInfo.name) + \
                    'Configure it before you can edit artwork.')
                return False

        else:
            log_error('_gui_edit_asset() Unknown object_kind = {0}'.format(object_kind))
            kodi_notify_warn("Unknown object_kind '{0}'".format(object_kind))
            return False

        # --- Only enable scraper if support the asset ---
        # Scrapers only loaded if editing a ROM.
        if object_kind == KIND_ROM:
            g_scrap_factory = ScraperFactory(g_PATHS, self.settings)
            scraper_menu_list = g_scrap_factory.get_asset_scraper_menu_list(asset_ID)
        else:
            scraper_menu_list = []

        # --- Show image editing options ---
        # Scrapers only supported for ROMs (for the moment)
        dialog = xbmcgui.Dialog()
        common_menu_list = [
            'Select local {0}'.format(AInfo.kind_str),
            'Import local {0} (copy and rename)'.format(AInfo.kind_str),
            'Unset artwork/asset',
        ]
        type2 = dialog.select(
            'Change {0} {1}'.format(AInfo.name, AInfo.kind_str),
            common_menu_list + scraper_menu_list)
        if type2 < 0: return False

        # --- Link to a local image ---
        if type2 == 0:
            image_dir = FileName(object_dic[AInfo.key]).getDir() if object_dic[AInfo.key] else ''

            log_debug('_gui_edit_asset() Initial path "{0}"'.format(image_dir))
            # >> ShowAndGetFile dialog
            dialog = xbmcgui.Dialog()
            if asset_ID == ASSET_MANUAL_ID or asset_ID == ASSET_TRAILER_ID:
                image_file = dialog.browse(1, 'Select {0} {1}'.format(AInfo.name, AInfo.kind_str), 'files',
                                           AInfo.exts_dialog, True, False, image_dir)
            # >> ShowAndGetImage dialog
            else:
                image_file = dialog.browse(2, 'Select {0} {1}'.format(AInfo.name, AInfo.kind_str), 'files',
                                           AInfo.exts_dialog, True, False, image_dir)
            if not image_file: return False
            image_file_path = FileName(image_file)
            if not image_file or not image_file_path.exists(): return False

            # --- Update object by assigment. XML/JSON will be save by parent ---
            log_debug('_gui_edit_asset() AInfo.key "{0}"'.format(AInfo.key))
            object_dic[AInfo.key] = image_file_path.getOriginalPath()
            kodi_notify('{0} {1} has been updated'.format(object_name, AInfo.name))
            log_info('_gui_edit_asset() Linked {0} {1} "{2}"'.format(
                object_name, AInfo.name, image_file_path.getOriginalPath()))

            # --- Update Kodi image cache ---
            kodi_update_image_cache(image_file_path.getOriginalPath())

        # --- Import an image ---
        # Copy and rename a local image into asset directory.
        elif type2 == 1:
            # If assets exists start file dialog from current asset directory
            image_dir = ''
            if object_dic[AInfo.key]: image_dir = FileName(object_dic[AInfo.key]).getDir()
            log_debug('_gui_edit_asset() Initial path "{0}"'.format(image_dir))
            image_file = xbmcgui.Dialog().browse(2, 'Select {0} image'.format(AInfo.name), 'files',
                                                 AInfo.exts_dialog, True, False, image_dir)
            image_FileName = FileName(image_file)
            if not image_FileName.exists(): return False

            # >> Determine image extension and dest filename. Check for errors.
            dest_path_FileName = asset_path_noext.append(image_FileName.getExt())
            log_debug('_gui_edit_asset() image_file   "{0}"'.format(image_FileName.getOriginalPath()))
            log_debug('_gui_edit_asset() img_ext      "{0}"'.format(image_FileName.getExt()))
            log_debug('_gui_edit_asset() dest_path    "{0}"'.format(dest_path_FileName.getOriginalPath()))
            if image_FileName.getPath() == dest_path_FileName.getPath():
                log_info('_gui_edit_asset() image_FileName and dest_path_FileName are the same. Returning.')
                kodi_notify_warn('image_FileName and dest_path_FileName are the same. Returning')
                return False

            # --- Copy image file ---
            try:
                fs_encoding = get_fs_encoding()
                shutil.copy(image_FileName.getPath().decode(fs_encoding), dest_path_FileName.getPath().decode(fs_encoding))
            except OSError:
                log_error('_gui_edit_asset() OSError exception copying image')
                kodi_notify_warn('OSError exception copying image')
                return False
            except IOError:
                log_error('_gui_edit_asset() IOError exception copying image')
                kodi_notify_warn('IOError exception copying image')
                return False

            # >> Update object by assigment. XML will be save by parent.
            # >> Always store original/raw paths in database.
            object_dic[AInfo.key] = dest_path_FileName.getOriginalPath()
            kodi_notify('{0} {1} has been updated'.format(object_name, AInfo.name))
            log_info('_gui_edit_asset() Copied file  "{0}"'.format(image_FileName.getOriginalPath()))
            log_info('_gui_edit_asset() Into         "{0}"'.format(dest_path_FileName.getOriginalPath()))
            log_info('_gui_edit_asset() Selected {0} {1} "{2}"'.format(object_name, AInfo.name, dest_path_FileName.getOriginalPath()))

            # --- Update Kodi image cache ---
            kodi_update_image_cache(dest_path_FileName.getOriginalPath())

        # --- Unset asset ---
        elif type2 == 2:
            object_dic[AInfo.key] = ''
            kodi_notify('{0} {1} has been unset'.format(object_name, AInfo.name))
            log_info('_gui_edit_asset() Unset {0} {1}'.format(object_name, AInfo.name))

        # --- Manual scrape and choose from a list of images ---
        elif type2 >= 3:
            # --- Create ScrapeFactory object ---
            scraper_index = type2 - len(common_menu_list)
            log_debug('_gui_edit_asset() Scraper index {0}'.format(scraper_index))
            scraper_ID = g_scrap_factory.get_asset_scraper_ID_from_menu_idx(scraper_index)

            # --- Scrape! ---
            data_dic = {
                'rom_FN' : ROMfile,
                'rom_checksums_FN' : ROM_checksums_FN,
                'platform' : platform,
                'current_asset_FN' : current_asset_FN,
                'asset_path_noext' : asset_path_noext,
            }
            # If this returns False there were no changes so no need to save ROMs JSON.
            # Scraper disk caches are flushed (written to disk) even if there is a message
            # to be printed here. A message here is that no images were found, however the
            # caches (internal, etc.) may have valid data.
            scraper_strategy = g_scrap_factory.create_CM_asset(scraper_ID)
            status_dic = scraper_strategy.scrap_CM_asset(object_dic, asset_ID, data_dic)
            # Flush caches.
            pDialog = KodiProgressDialog()
            pDialog.startProgress('Flushing scraper disk caches...')
            g_scrap_factory.destroy_CM()
            pDialog.endProgress()
            kodi_display_user_message(status_dic)
            if not status_dic['status']: return False

        # If we reach this point, changes were made.
        # Categories/Launchers/ROMs must be saved, container must be refreshed.
        return True

    #
    # Creates default categories data struct.
    # CAREFUL deletes current categories!
    #
    def _cat_create_default(self):
        # The key in the categories dictionary is an MD5 hash generate with current time plus some
        # random number. This will make it unique and different for every category created.
        category = fs_new_category()
        category_key = misc_generate_random_SID()
        category['id']      = category_key
        category['m_name']  = 'Emulators'
        category['m_genre'] = 'Emulators'
        category['m_plot']  = 'Initial AEL category.'
        self.categories = {}
        self.launchers = {}
        self.categories[category_key] = category

    #
    # Checks if the category is empty (no launchers defined)
    # Returns True if the category is empty. Returns False if non-empty
    def _cat_is_empty(self, categoryID):
        for launcherID in self.launchers.keys():
            if self.launchers[launcherID]['categoryID'] == categoryID: return False

        return True

    #
    # Reads a text file with category/launcher plot.
    # Checks file size to avoid importing binary files!
    #
    def _gui_import_TXT_file(text_file):
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
        text_plot = open(text_file.getPath(), 'rt')
        file_data = text_plot.read()
        text_plot.close()

        return file_data

    def _command_exec_utils_import_launchers(self):
        # If enableMultiple = True this function always returns a list of strings in UTF-8
        file_list = xbmcgui.Dialog().browse(
            1, 'Select XML category/launcher configuration file', 'files', '.xml', enableMultiple = True)
        # Process file by file
        for xml_file in file_list:
            xml_file_unicode = xml_file
            log_debug('_command_exec_utils_import_launchers() Importing "{0}"'.format(xml_file_unicode))
            import_FN = FileName(xml_file_unicode)
            if not import_FN.exists(): continue
            # >> This function edits self.categories, self.launchers dictionaries
            autoconfig_import_launchers(g_PATHS.CATEGORIES_FILE_PATH, g_PATHS.ROMS_DIR,
                self.categories, self.launchers, import_FN)

        # --- Save Categories/Launchers, update timestamp and notify user ---
        fs_write_catfile(g_PATHS.CATEGORIES_FILE_PATH, self.categories, self.launchers)
        kodi_refresh_container()
        kodi_notify('Finished importing Categories/Launchers')

    #
    # Export AEL launcher configuration.
    #
    def _command_exec_utils_export_launchers(self):
        log_debug('_command_exec_utils_export_launchers() Exporting Category/Launcher XML configuration')

        # --- Ask path to export XML configuration ---
        dir_path = xbmcgui.Dialog().browse(
            0, 'Select XML export directory', 'files', '', False, False)
        if not dir_path: return

        # --- If XML exists then warn user about overwriting it ---
        export_FN = FileName(dir_path).pjoin('AEL_configuration.xml')
        if export_FN.exists():
            ret = kodi_dialog_yesno('AEL_configuration.xml found in the selected directory. Overwrite?')
            if not ret:
                kodi_notify_warn('Category/Launcher XML exporting cancelled')
                return

        # --- Export stuff ---
        try:
            autoconfig_export_all(self.categories, self.launchers, export_FN)
        except AddonError as ex:
            kodi_notify_warn('{0}'.format(ex))
        else:
            kodi_notify('Exported AEL Categories and Launchers XML configuration')

    #
    # Checks all databases and updates to newer version if possible
    #
    def _command_exec_utils_check_database(self):
        log_debug('_command_exec_utils_check_database() Beginning ....')
        pDialog = xbmcgui.DialogProgress()
        pDialog_canceled = False

        # >> Open Categories/Launchers XML.
        #    XML should be updated automatically on load.
        pDialog.create('Advanced Emulator Launcher', 'Checking Categories/Launchers ...')
        self.categories = {}
        self.launchers = {}
        self.update_timestamp = fs_load_catfile(g_PATHS.CATEGORIES_FILE_PATH, self.categories, self.launchers)

        # >> Traverse and fix Categories.
        for category_id in self.categories:
            category = self.categories[category_id]
            # >> Fix s_thumb -> s_icon renaming
            if category['default_icon'] == 's_thumb':      category['default_icon'] = 's_icon'
            if category['default_fanart'] == 's_thumb':    category['default_fanart'] = 's_icon'
            if category['default_banner'] == 's_thumb':    category['default_banner'] = 's_icon'
            if category['default_poster'] == 's_thumb':    category['default_poster'] = 's_icon'
            if category['default_clearlogo'] == 's_thumb': category['default_clearlogo'] = 's_icon'

            # >> Fix s_flyer -> s_poster renaming
            if category['default_icon'] == 's_flyer':      category['default_icon'] = 's_poster'
            if category['default_fanart'] == 's_flyer':    category['default_fanart'] = 's_poster'
            if category['default_banner'] == 's_flyer':    category['default_banner'] = 's_poster'
            if category['default_poster'] == 's_flyer':    category['default_poster'] = 's_poster'
            if category['default_clearlogo'] == 's_flyer': category['default_clearlogo'] = 's_poster'

        # Traverse and fix Launchers.
        for launcher_id in self.launchers:
            launcher = self.launchers[launcher_id]
            # Fix s_thumb -> s_icon renaming
            if launcher['default_icon'] == 's_thumb':       launcher['default_icon'] = 's_icon'
            if launcher['default_fanart'] == 's_thumb':     launcher['default_fanart'] = 's_icon'
            if launcher['default_banner'] == 's_thumb':     launcher['default_banner'] = 's_icon'
            if launcher['default_poster'] == 's_thumb':     launcher['default_poster'] = 's_icon'
            if launcher['default_clearlogo'] == 's_thumb':  launcher['default_clearlogo'] = 's_icon'
            if launcher['default_controller'] == 's_thumb': launcher['default_controller'] = 's_icon'
            # Fix s_flyer -> s_poster renaming
            if launcher['default_icon'] == 's_flyer':       launcher['default_icon'] = 's_poster'
            if launcher['default_fanart'] == 's_flyer':     launcher['default_fanart'] = 's_poster'
            if launcher['default_banner'] == 's_flyer':     launcher['default_banner'] = 's_poster'
            if launcher['default_poster'] == 's_flyer':     launcher['default_poster'] = 's_poster'
            if launcher['default_clearlogo'] == 's_flyer':  launcher['default_clearlogo'] = 's_poster'
            if launcher['default_controller'] == 's_flyer': launcher['default_controller'] = 's_poster'
        # Save categories.xml to update timestamp.
        fs_write_catfile(g_PATHS.CATEGORIES_FILE_PATH, self.categories, self.launchers)
        pDialog.update(100)

        # >> Traverse all launchers. Load ROMs and check every ROMs.
        pDialog.update(0, 'Checking Launcher ROMs ...')
        num_launchers = len(self.launchers)
        processed_launchers = 0
        for launcher_id in self.launchers:
            log_debug('_command_edit_rom() Checking Launcher "{0}"'.format(self.launchers[launcher_id]['m_name']))
            # --- Load standard ROM database ---
            roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, self.launchers[launcher_id])
            for rom_id in roms: self._misc_fix_rom_object(roms[rom_id])
            fs_write_ROMs_JSON(g_PATHS.ROMS_DIR, self.launchers[launcher_id], roms)

            # --- If exists, load Parent ROM database ---
            parents_roms_base_noext = self.launchers[launcher_id]['roms_base_noext'] + '_parents'
            parents_FN = g_PATHS.ROMS_DIR.pjoin(parents_roms_base_noext + '.json')
            if parents_FN.exists():
                roms = fs_load_JSON_file(g_PATHS.ROMS_DIR, parents_roms_base_noext)
                for rom_id in roms: self._misc_fix_rom_object(roms[rom_id])
                fs_write_JSON_file(g_PATHS.ROMS_DIR, parents_roms_base_noext, roms)

            # This updates timestamps and forces regeneration of Virtual Launchers.
            self.launchers[launcher_id]['timestamp_launcher'] = time.time()

            # Update dialog
            processed_launchers += 1
            update_number = int((processed_launchers * 100) / num_launchers)
            pDialog.update(update_number)
        # >> Save categories.xml because launcher timestamps changed
        fs_write_catfile(g_PATHS.CATEGORIES_FILE_PATH, self.categories, self.launchers)
        pDialog.update(100)

        # >> Load Favourite ROMs and update JSON
        pDialog.update(0, 'Checking Favourite ROMs ...')
        roms_fav = fs_load_Favourites_JSON(g_PATHS.FAV_JSON_FILE_PATH)
        num_fav_roms = len(roms_fav)
        processed_fav_roms = 0
        for rom_id in roms_fav:
            # >> Get ROM object
            rom = roms_fav[rom_id]
            self._misc_fix_Favourite_rom_object(rom)
            # >> Update dialog
            processed_fav_roms += 1
            update_number = (float(processed_fav_roms) / float(num_fav_roms)) * 100
            pDialog.update(int(update_number))
        fs_write_Favourites_JSON(g_PATHS.FAV_JSON_FILE_PATH, roms_fav)
        pDialog.update(100)

        # >> Traverse every ROM Collection database and check/update Favourite ROMs.
        (collections, update_timestamp) = fs_load_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH)
        pDialog.update(0, 'Checking Collection ROMs ...')
        num_collections = len(collections)
        processed_collections = 0
        for collection_id in collections:
            collection = collections[collection_id]
            # >> Fix collection
            if 'default_thumb' in collection:
                collection['default_icon'] = collection['default_thumb']
                collection.pop('default_thumb')
            if 's_thumb' in collection:
                collection['s_icon'] = collection['s_thumb']
                collection.pop('s_thumb')
            if 's_flyer' in collection:
                collection['s_poster'] = collection['s_flyer']
                collection.pop('s_flyer')
            # >> Fix s_thumb -> s_icon renaming
            if collection['default_icon'] == 's_thumb':      collection['default_icon'] = 's_icon'
            if collection['default_fanart'] == 's_thumb':    collection['default_fanart'] = 's_icon'
            if collection['default_banner'] == 's_thumb':    collection['default_banner'] = 's_icon'
            if collection['default_poster'] == 's_thumb':    collection['default_poster'] = 's_icon'
            if collection['default_clearlogo'] == 's_thumb': collection['default_clearlogo'] = 's_icon'
            # >> Fix s_flyer -> s_poster renaming
            if collection['default_icon'] == 's_flyer':      collection['default_icon'] = 's_poster'
            if collection['default_fanart'] == 's_flyer':    collection['default_fanart'] = 's_poster'
            if collection['default_banner'] == 's_flyer':    collection['default_banner'] = 's_poster'
            if collection['default_poster'] == 's_flyer':    collection['default_poster'] = 's_poster'
            if collection['default_clearlogo'] == 's_flyer': collection['default_clearlogo'] = 's_poster'

            # >> Fix collection ROMs
            roms_json_file = g_PATHS.COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
            collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
            for rom in collection_rom_list: self._misc_fix_Favourite_rom_object(rom)
            fs_write_Collection_ROMs_JSON(roms_json_file, collection_rom_list)
            # >> Update progress dialog
            processed_collections += 1
            update_number = (float(processed_collections) / float(num_collections)) * 100
            pDialog.update(int(update_number))
        # >> Save ROM Collection index
        fs_write_Collection_index_XML(g_PATHS.COLLECTIONS_FILE_PATH, collections)
        pDialog.update(100)

        # >> Load Most Played ROMs and check/update.
        pDialog.update(0, 'Checking Most Played ROMs ...')
        most_played_roms = fs_load_Favourites_JSON(g_PATHS.MOST_PLAYED_FILE_PATH)
        for rom_id in most_played_roms:
            rom = most_played_roms[rom_id]
            self._misc_fix_Favourite_rom_object(rom)
        fs_write_Favourites_JSON(g_PATHS.MOST_PLAYED_FILE_PATH, most_played_roms)
        pDialog.update(100)

        # >> Load Recently Played ROMs and check/update.
        pDialog.update(0, 'Checking Recently Played ROMs ...')
        recent_roms_list = fs_load_Collection_ROMs_JSON(g_PATHS.RECENT_PLAYED_FILE_PATH)
        for rom in recent_roms_list: self._misc_fix_Favourite_rom_object(rom)
        fs_write_Collection_ROMs_JSON(g_PATHS.RECENT_PLAYED_FILE_PATH, recent_roms_list)
        pDialog.update(100)
        pDialog.close()

        # >> So long and thanks for all the fish.
        kodi_notify('All databases checked')
        log_debug('_command_check_database() Exiting')

    #
    # ROM dictionary is edited by Python passing by assigment
    #
    def _misc_fix_rom_object(self, rom):
        # Add new fields if not present
        if 'm_nplayers'    not in rom: rom['m_nplayers']    = ''
        if 'm_esrb'        not in rom: rom['m_esrb']        = ESRB_PENDING
        if 'disks'         not in rom: rom['disks']         = []
        if 'pclone_status' not in rom: rom['pclone_status'] = PCLONE_STATUS_NONE
        if 'cloneof'       not in rom: rom['cloneof']       = ''
        if 's_3dbox'       not in rom: rom['s_3dbox']       = ''
        if 'i_extra_ROM'   not in rom: rom['i_extra_ROM']   = False
        # Delete unwanted/obsolete stuff
        if 'nointro_isClone' in rom: rom.pop('nointro_isClone')
        # DB field renamings
        if 'm_studio' in rom:
            rom['m_developer'] = rom['m_studio']
            rom.pop('m_studio')

    def _misc_fix_Favourite_rom_object(self, rom):
        # Fix standard ROM fields
        self._misc_fix_rom_object(rom)

        # Favourite ROMs additional stuff
        if 'args_extra' not in rom: rom['args_extra'] = []
        if 'non_blocking' not in rom: rom['non_blocking'] = False
        if 'roms_default_thumb' in rom:
            rom['roms_default_icon'] = rom['roms_default_thumb']
            rom.pop('roms_default_thumb')
        if 'minimize' in rom:
            rom['toggle_window'] = rom['minimize']
            rom.pop('minimize')

    def _command_exec_utils_check_launchers(self):
        log_info('_command_exec_utils_check_launchers() Checking all Launchers configuration ...')

        main_str_list = []
        main_str_list.append('Number of launchers: {0}\n\n'.format(len(self.launchers)))
        for launcher_id in sorted(self.launchers, key = lambda x : self.launchers[x]['m_name']):
            launcher = self.launchers[launcher_id]
            l_str = []
            main_str_list.append('[COLOR orange]Launcher "{0}"[/COLOR]\n'.format(launcher['m_name']))

            # >> Check that platform is on AEL official platform list
            platform = launcher['platform']
            if platform not in platform_long_to_index_dic:
                l_str.append('Unrecognised platform "{0}"\n'.format(platform))

            # >> Check that category exists
            categoryID = launcher['categoryID']
            if categoryID != VCATEGORY_ADDONROOT_ID and categoryID not in self.categories:
                l_str.append('Category not found (unlinked launcher)\n')

            # >> Check that application exists
            app_FN = FileName(launcher['application'])
            if not app_FN.exists():
                l_str.append('Application "{0}" not found\n'.format(app_FN.getPath()))

            # >> Check that rompath exists if rompath is not empty
            # >> Empty rompath means standalone launcher
            rompath = launcher['rompath']
            rompath_FN = FileName(rompath)
            if rompath and not rompath_FN.exists():
                l_str.append('ROM path "{0}" not found\n'.format(rompath_FN.getPath()))

            # Check that DAT file exists if not empty
            audit_custom_dat_file = launcher['audit_custom_dat_file']
            audit_custom_dat_FN = FileName(audit_custom_dat_file)
            if audit_custom_dat_file and not audit_custom_dat_FN.exists():
                l_str.append('Custom DAT file "{}" not found\n'.format(audit_custom_dat_FN.getPath()))

            # audit_auto_dat_file = launcher['audit_auto_dat_file']
            # audit_auto_dat_FN = FileName(audit_auto_dat_file)
            # if audit_auto_dat_file and not audit_auto_dat_FN.exists():
            #     l_str.append('Custom DAT file "{}" not found\n'.format(audit_auto_dat_FN.getPath()))

            # >> Test that artwork files exist if not empty (s_* fields)
            self._aux_check_for_file(l_str, 's_icon', launcher)
            self._aux_check_for_file(l_str, 's_fanart', launcher)
            self._aux_check_for_file(l_str, 's_banner', launcher)
            self._aux_check_for_file(l_str, 's_poster', launcher)
            self._aux_check_for_file(l_str, 's_clearlogo', launcher)
            self._aux_check_for_file(l_str, 's_controller', launcher)
            self._aux_check_for_file(l_str, 's_trailer', launcher)

            # >> Test that ROM_asset_path exists if not empty
            ROM_asset_path = launcher['ROM_asset_path']
            ROM_asset_path_FN = FileName(ROM_asset_path)
            if ROM_asset_path and not ROM_asset_path_FN.exists():
                l_str.append('ROM_asset_path "{0}" not found\n'.format(ROM_asset_path_FN.getPath()))

            # >> Test that ROM asset paths exist if not empty (path_* fields)
            self._aux_check_for_file(l_str, 'path_3dbox', launcher)
            self._aux_check_for_file(l_str, 'path_title', launcher)
            self._aux_check_for_file(l_str, 'path_snap', launcher)
            self._aux_check_for_file(l_str, 'path_boxfront', launcher)
            self._aux_check_for_file(l_str, 'path_boxback', launcher)
            self._aux_check_for_file(l_str, 'path_cartridge', launcher)
            self._aux_check_for_file(l_str, 'path_fanart', launcher)
            self._aux_check_for_file(l_str, 'path_banner', launcher)
            self._aux_check_for_file(l_str, 'path_clearlogo', launcher)
            self._aux_check_for_file(l_str, 'path_flyer', launcher)
            self._aux_check_for_file(l_str, 'path_map', launcher)
            self._aux_check_for_file(l_str, 'path_manual', launcher)
            self._aux_check_for_file(l_str, 'path_trailer', launcher)

            # >> Check for duplicate asset paths

            # >> If l_str is empty is because no problems were found.
            if l_str:
                main_str_list.extend(l_str)
            else:
                main_str_list.append('No problems found\n')
            main_str_list.append('\n')

        # Stats report
        log_info('Writing report file "{0}"'.format(g_PATHS.LAUNCHER_REPORT_FILE_PATH.getPath()))
        full_string = ''.join(main_str_list)
        file = open(g_PATHS.LAUNCHER_REPORT_FILE_PATH.getPath(), 'w')
        file.write(full_string)
        file.close()
        kodi_display_text_window_mono('Launchers report', full_string)

    def _aux_check_for_file(self, str_list, dic_key_name, launcher):
        path = launcher[dic_key_name]
        path_FN = FileName(path)
        if path and not path_FN.exists():
            problems_found = True
            str_list.append('{0} "{1}" not found\n'.format(dic_key_name, path_FN.getPath()))

    # For every ROM launcher scans the ROM path and check 1) if there are dead ROMs and 2) if
    # there are ROM files not in AEL database. If either 1) or 2) is true launcher must be
    # updated with the ROM scanner.
    def _command_exec_utils_check_launcher_sync_status(self):
        log_debug('_command_exec_utils_check_launcher_sync_status() Checking ROM Launcher sync status...')
        pdialog = KodiProgressDialog()
        num_launchers = len(self.launchers)
        main_slist = []
        short_slist = [
            ['left', 'left'],
        ]
        detailed_slist = []
        pdialog.startProgress('Checking ROM sync status', num_launchers)
        processed_launchers = 0
        for launcher_id in sorted(self.launchers, key = lambda x : self.launchers[x]['m_name']):
            pdialog.updateProgress(processed_launchers)
            processed_launchers += 1
            launcher = self.launchers[launcher_id]
            # Skip non-ROM launcher.
            if not launcher['rompath']: continue
            log_debug('Checking ROM Launcher "{}"'.format(launcher['m_name']))
            detailed_slist.append('[COLOR orange]Launcher "{0}"[/COLOR]'.format(launcher['m_name']))
            # Load ROMs.
            pdialog.updateMessage2('Loading ROMs...')
            roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, launcher)
            num_roms = len(roms)
            R_str = 'ROM' if num_roms == 1 else 'ROMs'
            log_debug('Launcher has {} DB {}'.format(num_roms, R_str))
            detailed_slist.append('Launcher has {} DB {}'.format(num_roms, R_str))
            # For now skip multidisc ROMs until multidisc support is fixed. I think for
            # every ROM in the multidisc set there should be a normal ROM not displayed
            # in listings, and then the special multidisc ROM that points to the ROMs
            # in the set.
            has_multidisc_ROMs = False
            for rom_id in roms:
                if roms[rom_id]['disks']:
                    has_multidisc_ROMs = True
                    break
            if has_multidisc_ROMs:
                log_debug('Launcher has multidisc ROMs. Skipping launcher')
                detailed_slist.append('Launcher has multidisc ROMs.')
                detailed_slist.append('[COLOR yellow]Skipping launcher[/COLOR]')
                continue
            # Get real ROMs (remove Missing, Multidisc, etc., ROMs).
            # Remove ROM Audit Missing ROMs (fake ROMs).
            real_roms = {}
            for rom_id in roms:
                if roms[rom_id]['nointro_status'] == AUDIT_STATUS_MISS: continue
                real_roms[rom_id] = roms[rom_id]
            num_real_roms = len(real_roms)
            R_str = 'ROM' if num_real_roms == 1 else 'ROMs'
            log_debug('Launcher has {} real {}'.format(num_real_roms, R_str))
            detailed_slist.append('Launcher has {} real {}'.format(num_real_roms, R_str))
            # If Launcher is empty there is nothing to do.
            if num_real_roms < 1:
                log_debug('Launcher is empty')
                detailed_slist.append('Launcher is empty')
                detailed_slist.append('[COLOR yellow]Skipping launcher[/COLOR]')
                continue
            # Make a dictionary for fast indexing.
            romfiles_dic = {real_roms[rom_id]['filename'] : rom_id for rom_id in real_roms}

            # Scan files in rompath directory.
            pdialog.updateMessage2('Scanning files in ROM paths...')
            launcher_path = FileName(launcher['rompath'])
            log_debug('Scanning files in {}'.format(launcher_path.getPath()))
            if self.settings['scan_recursive']:
                log_debug('Recursive scan activated')
                files = launcher_path.recursiveScanFilesInPath('*.*')
            else:
                log_debug('Recursive scan not activated')
                files = launcher_path.scanFilesInPath('*.*')
            num_files = len(files)
            f_str = 'file' if num_files == 1 else 'files'
            log_debug('File scanner found {} files'.format(num_files, f_str))
            detailed_slist.append('File scanner found {} files'.format(num_files, f_str))

            # Check for dead ROMs (ROMs in AEL DB not on disk).
            pdialog.updateMessage2('Checking dead ROMs...')
            log_debug('Checking for dead ROMs...')
            num_dead_roms = 0
            for rom_id in real_roms:
                fileName = FileName(real_roms[rom_id]['filename'])
                if not fileName.exists(): num_dead_roms += 1
            if num_dead_roms > 0:
                R_str = 'ROM' if num_dead_roms == 1 else 'ROMs'
                detailed_slist.append('Found {} dead {}'.format(num_dead_roms, R_str))
            else:
                detailed_slist.append('No dead ROMs found')

            # Check for unsynced ROMs (ROMS on disk not in AEL DB).
            pdialog.updateMessage2('Checking unsynced ROMs...')
            log_debug('Checking for unsynced ROMs...')
            num_unsynced_roms = 0
            for f_path in sorted(files):
                ROM_FN = FileName(f_path)
                processROM = False
                for ext in launcher['romext'].split("|"):
                    if ROM_FN.getExt() == '.' + ext: processROM = True
                if not processROM: continue
                # Ignore BIOS ROMs, like the ROM Scanner does.
                if self.settings['scan_ignore_bios']:
                    BIOS_re = re.findall('\[BIOS\]', ROM_FN.getBase())
                    if len(BIOS_re) > 0:
                        log_debug('BIOS detected. Skipping ROM "{}"'.format(ROM_FN.getBase()))
                        continue
                ROM_in_launcher_DB = True if f_path in romfiles_dic else False
                if not ROM_in_launcher_DB: num_unsynced_roms += 1
            if num_unsynced_roms > 0:
                R_str = 'ROM' if num_unsynced_roms == 1 else 'ROMs'
                detailed_slist.append('Found {} unsynced {}'.format(num_unsynced_roms, R_str))
            else:
                detailed_slist.append('No unsynced ROMs found')
            update_launcher_flag = True if num_dead_roms > 0 or num_unsynced_roms > 0 else False
            if update_launcher_flag:
                short_slist.append([launcher['m_name'], '[COLOR red]Update launcher[/COLOR]'])
                detailed_slist.append('[COLOR red]Launcher should be updated[/COLOR]')
            else:
                short_slist.append([launcher['m_name'], '[COLOR green]Launcher OK[/COLOR]'])
                detailed_slist.append('[COLOR green]Launcher OK[/COLOR]')
            detailed_slist.append('')
        pdialog.endProgress()

        # Generate, save and display report.
        log_info('Writing report file "{}"'.format(g_PATHS.ROM_SYNC_REPORT_FILE_PATH.getPath()))
        pdialog.startProgress('Saving report')
        main_slist.append('*** Summary ***')
        main_slist.append('There are {} ROM launchers.'.format(num_launchers))
        main_slist.append('')
        main_slist.extend(text_render_table_NO_HEADER(short_slist, trim_Kodi_colours = True))
        main_slist.append('')
        main_slist.append('*** Detailed report ***')
        main_slist.extend(detailed_slist)
        full_string = '\n'.join(main_slist)
        file = open(g_PATHS.ROM_SYNC_REPORT_FILE_PATH.getPath(), 'w')
        file.write(full_string)
        file.close()
        pdialog.endProgress()
        kodi_display_text_window_mono('ROM sync status report', full_string)

    def _command_exec_utils_check_artwork_integrity(self):
        kodi_dialog_OK('EXECUTE_UTILS_CHECK_ARTWORK_INTEGRITY not implemented yet.')

    def _command_exec_utils_check_ROM_artwork_integrity(self):
        log_debug('_command_exec_utils_check_ROM_artwork_integrity() Beginning...')
        pdialog = KodiProgressDialog()
        num_launchers = len(self.launchers)
        main_slist = []
        detailed_slist = []
        sum_table_slist = [
            ['left', 'right', 'right', 'right', 'right'],
            ['Launcher', 'ROMs', 'Images', 'Missing', 'Problematic'],
        ]
        pdialog.startProgress('Checking ROM artwork integrity...', num_launchers)
        processed_launchers = 0
        total_images = 0
        missing_images = 0
        processed_images = 0
        problematic_images = 0
        for launcher_id in sorted(self.launchers, key = lambda x : self.launchers[x]['m_name']):
            pdialog.updateProgress(processed_launchers)
            processed_launchers += 1
            launcher = self.launchers[launcher_id]
            # Skip non-ROM launcher.
            if not launcher['rompath']: continue
            log_debug('Checking ROM Launcher "{}"...'.format(launcher['m_name']))
            detailed_slist.append(KC_ORANGE + 'Launcher "{}"'.format(launcher['m_name']) + KC_END)
            # Load ROMs.
            pdialog.updateMessage2('Loading ROMs')
            roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, launcher)
            num_roms = len(roms)
            R_str = 'ROM' if num_roms == 1 else 'ROMs'
            log_debug('Launcher has {} DB {}'.format(num_roms, R_str))
            detailed_slist.append('Launcher has {} DB {}'.format(num_roms, R_str))
            # If Launcher is empty there is nothing to do.
            if num_roms < 1:
                log_debug('Launcher is empty')
                detailed_slist.append('Launcher is empty')
                detailed_slist.append(KC_YELLOW + 'Skipping launcher' + KC_END)
                continue

            # Traverse all ROMs in Launcher.
            # For every asset check the artwork file.
            # First check if the image has the correct extension.
            problems_detected = False
            launcher_images = 0
            launcher_missing_images = 0
            launcher_problematic_images = 0
            pdialog.updateMessage2('Checking image files')
            for rom_id in roms:
                rom = roms[rom_id]
                # detailed_slist.append('\nProcessing ROM {}'.format(rom['filename']))
                for asset_id in ROM_ASSET_ID_LIST:
                    A = assets_get_info_scheme(asset_id)
                    asset_fname = rom[A.key]
                    # detailed_slist.append('\nProcessing asset {}'.format(A.name))
                    # Skip empty assets
                    if not asset_fname: continue
                    # Skip manuals and trailers
                    if asset_id == ASSET_MANUAL_ID: continue
                    if asset_id == ASSET_TRAILER_ID: continue
                    launcher_images += 1
                    total_images += 1
                    # If asset file does not exits that's an error.
                    if not os.path.exists(asset_fname):
                        detailed_slist.append('Not found {}'.format(asset_fname))
                        launcher_missing_images += 1
                        missing_images += 1
                        problems_detected = True
                        continue
                    # Process asset
                    processed_images += 1
                    asset_root, asset_ext = os.path.splitext(asset_fname)
                    asset_ext = asset_ext[1:] # Remove leading dot '.png' -> 'png'
                    img_id_ext = misc_identify_image_id_by_ext(asset_fname)
                    img_id_real = misc_identify_image_id_by_contents(asset_fname)
                    # detailed_slist.append('img_id_ext "{}" | img_id_real "{}"'.format(img_id_ext, img_id_real))
                    # Unrecognised or corrupted image.
                    if img_id_ext == IMAGE_UKNOWN_ID:
                        detailed_slist.append('Unrecognised extension {}'.format(asset_fname))
                        problems_detected = True
                        problematic_images += 1
                        launcher_problematic_images += 1
                        continue
                    # Corrupted image.
                    if img_id_real == IMAGE_CORRUPT_ID:
                        detailed_slist.append('Corrupted {}'.format(asset_fname))
                        problems_detected = True
                        problematic_images += 1
                        launcher_problematic_images += 1
                        continue
                    # Unrecognised or corrupted image.
                    if img_id_real == IMAGE_UKNOWN_ID:
                        detailed_slist.append('Bin unrecog or corrupted {}'.format(asset_fname))
                        problems_detected = True
                        problematic_images += 1
                        launcher_problematic_images += 1
                        continue
                    # At this point the image is recognised but has wrong extension
                    if img_id_ext != img_id_real:
                        detailed_slist.append('Wrong extension ({}) {}'.format(
                            IMAGE_EXTENSIONS[img_id_real][0], asset_fname))
                        problems_detected = True
                        problematic_images += 1
                        launcher_problematic_images += 1
                        continue
                # On big setups this can take forever. Allow the user to cancel.
                if pdialog.isCanceled(): break
            else:
                # only executed if the inner loop did NOT break
                sum_table_slist.append([
                    launcher['m_name'], '{:,d}'.format(num_roms), '{:,d}'.format(launcher_images),
                    '{:,d}'.format(launcher_missing_images), '{:,d}'.format(launcher_problematic_images),
                ])
                detailed_slist.append('Number of images    {:6,d}'.format(launcher_images))
                detailed_slist.append('Missing images      {:6,d}'.format(launcher_missing_images))
                detailed_slist.append('Problematic images  {:6,d}'.format(launcher_problematic_images))
                if problems_detected:
                    detailed_slist.append(KC_RED + 'Launcher should be updated' + KC_END)
                else:
                    detailed_slist.append(KC_GREEN + 'Launcher OK' + KC_END)
                detailed_slist.append('')
                continue
            # only executed if the inner loop DID break
            detailed_slist.append('Interrupted by user (pDialog cancelled).')
            break
        pdialog.endProgress()

        # Generate, save and display report.
        log_info('Writing report file "{}"'.format(g_PATHS.ROM_ART_INTEGRITY_REPORT_FILE_PATH.getPath()))
        pdialog.startProgress('Saving report')
        main_slist.append('*** Summary ***')
        main_slist.append('There are {:,} ROM launchers.'.format(num_launchers))
        main_slist.append('Total images        {:7,d}'.format(total_images))
        main_slist.append('Missing images      {:7,d}'.format(missing_images))
        main_slist.append('Processed images    {:7,d}'.format(processed_images))
        main_slist.append('Problematic images  {:7,d}'.format(problematic_images))
        main_slist.append('')
        main_slist.extend(text_render_table(sum_table_slist))
        main_slist.append('')
        main_slist.append('*** Detailed report ***')
        main_slist.extend(detailed_slist)
        full_string = '\n'.join(main_slist)
        file = open(g_PATHS.ROM_ART_INTEGRITY_REPORT_FILE_PATH.getPath(), 'w')
        file.write(full_string)
        file.close()
        pdialog.endProgress()
        kodi_display_text_window_mono('ROM artwork integrity report', full_string)

    def _command_exec_utils_delete_redundant_artwork(self):
        kodi_dialog_OK('EXECUTE_UTILS_DELETE_REDUNDANT_ARTWORK not implemented yet.')

    def _command_exec_utils_delete_ROM_redundant_artwork(self):
        kodi_dialog_OK('EXECUTE_UTILS_DELETE_ROM_REDUNDANT_ARTWORK not implemented yet.')
        return

        log_info('_command_exec_utils_delete_ROM_redundant_artwork() Beginning...')
        pdialog = KodiProgressDialog()
        num_launchers = len(self.launchers)
        main_slist = []
        detailed_slist = []
        pdialog.startProgress('Checking ROM sync status', num_launchers)
        processed_launchers = 0
        for launcher_id in sorted(self.launchers, key = lambda x : self.launchers[x]['m_name']):
            pdialog.updateProgress(processed_launchers)
            processed_launchers += 1
            launcher = self.launchers[launcher_id]
            # Skip non-ROM launcher.
            if not launcher['rompath']: continue
            log_debug('Checking ROM Launcher "{}"'.format(launcher['m_name']))
            detailed_slist.append('[COLOR orange]Launcher "{0}"[/COLOR]'.format(launcher['m_name']))
            # Load ROMs.
            pdialog.updateMessage2('Loading ROMs...')
            roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, launcher)
            num_roms = len(roms)
            R_str = 'ROM' if num_roms == 1 else 'ROMs'
            log_debug('Launcher has {} DB {}'.format(num_roms, R_str))
            detailed_slist.append('Launcher has {} DB {}'.format(num_roms, R_str))
            # For now skip multidisc ROMs until multidisc support is fixed. I think for
            # every ROM in the multidisc set there should be a normal ROM not displayed
            # in listings, and then the special multidisc ROM that points to the ROMs
            # in the set.
            has_multidisc_ROMs = False
            for rom_id in roms:
                if roms[rom_id]['disks']:
                    has_multidisc_ROMs = True
                    break
            if has_multidisc_ROMs:
                log_debug('Launcher has multidisc ROMs. Skipping launcher')
                detailed_slist.append('Launcher has multidisc ROMs.')
                detailed_slist.append('[COLOR yellow]Skipping launcher[/COLOR]')
                continue
            # Get real ROMs (remove Missing, Multidisc, etc., ROMs).
            # Remove ROM Audit Missing ROMs (fake ROMs).
            real_roms = {}
            for rom_id in roms:
                if roms[rom_id]['nointro_status'] == AUDIT_STATUS_MISS: continue
                real_roms[rom_id] = roms[rom_id]
            num_real_roms = len(real_roms)
            R_str = 'ROM' if num_real_roms == 1 else 'ROMs'
            log_debug('Launcher has {} real {}'.format(num_real_roms, R_str))
            detailed_slist.append('Launcher has {} real {}'.format(num_real_roms, R_str))
            # If Launcher is empty there is nothing to do.
            if num_real_roms < 1:
                log_debug('Launcher is empty')
                detailed_slist.append('Launcher is empty')
                detailed_slist.append('[COLOR yellow]Skipping launcher[/COLOR]')
                continue
            # Make a dictionary for fast indexing.
            # romfiles_dic = {real_roms[rom_id]['filename'] : rom_id for rom_id in real_roms}

            # Process all asset directories one by one.


            # Complete detailed report.
            detailed_slist.append('')
        pdialog.endProgress()

        # Generate, save and display report.
        log_info('Writing report file "{0}"'.format(g_PATHS.ROM_SYNC_REPORT_FILE_PATH.getPath()))
        pdialog.startProgress('Saving report')
        main_slist.append('*** Summary ***')
        main_slist.append('There are {} ROM launchers.'.format(num_launchers))
        main_slist.append('')
        # main_slist.extend(text_render_table_NO_HEADER(short_slist, trim_Kodi_colours = True))
        # main_slist.append('')
        main_slist.append('*** Detailed report ***')
        main_slist.extend(detailed_slist)
        full_string = '\n'.join(main_slist)
        file = open(g_PATHS.ROM_SYNC_REPORT_FILE_PATH.getPath(), 'w')
        file.write(full_string)
        file.close()
        pdialog.endProgress()
        kodi_display_text_window_mono('ROM redundant artwork report', full_string)

    # Shows a report of the auto-detected No-Intro/Redump DAT files.
    # This simplifies a lot the ROM Audit of launchers and other things like the
    # Offline Scraper database generation.
    def _command_exec_utils_show_DATs(self):
        log_debug('_command_exec_utils_show_DATs() Starting...')
        DAT_STRING_LIMIT_CHARS = 80

        # --- Get files in No-Intro and Redump DAT directories ---
        NOINTRO_PATH_FN = FileName(self.settings['audit_nointro_dir'])
        if not NOINTRO_PATH_FN.exists():
            kodi_dialog_OK('No-Intro DAT directory not found. '
                'Please set it up in AEL addon settings.')
            return
        REDUMP_PATH_FN = FileName(self.settings['audit_redump_dir'])
        if not REDUMP_PATH_FN.exists():
            kodi_dialog_OK('No-Intro DAT directory not found. '
                'Please set it up in AEL addon settings.')
            return

        # --- Table header ---
        table_str = [
            ['left', 'left', 'left'],
            ['Platform', 'DAT type', 'DAT file'],
        ]

        # --- Scan files in DAT dirs ---
        NOINTRO_DAT_list = NOINTRO_PATH_FN.scanFilesInPath('*.dat')
        REDUMP_DAT_list = REDUMP_PATH_FN.scanFilesInPath('*.dat')
        # Some debug code
        # for fname in NOINTRO_DAT_list: log_debug(fname)

        # --- Autodetect files ---
        # 1) Traverse all platforms.
        # 2) Autodetect DATs for No-Intro or Redump platforms only.
        # AEL_platforms_t = AEL_platforms[0:4]
        for platform in AEL_platforms:
            if platform.DAT == DAT_NOINTRO:
                fname = misc_look_for_NoIntro_DAT(platform, NOINTRO_DAT_list)
                if fname:
                    DAT_str = FileName(fname).getBase()
                    DAT_str = text_limit_string(DAT_str, DAT_STRING_LIMIT_CHARS)
                    # DAT_str = '[COLOR=orange]' + DAT_str + '[/COLOR]'
                else:
                    DAT_str = '[COLOR=yellow]No-Intro DAT not found[/COLOR]'
                table_str.append([platform.compact_name, platform.DAT, DAT_str])
            elif platform.DAT == DAT_REDUMP:
                fname = misc_look_for_Redump_DAT(platform, REDUMP_DAT_list)
                if fname:
                    DAT_str = FileName(fname).getBase()
                    DAT_str = text_limit_string(DAT_str, DAT_STRING_LIMIT_CHARS)
                    # DAT_str = '[COLOR=orange]' + DAT_str + '[/COLOR]'
                else:
                    DAT_str = '[COLOR=yellow]Redump DAT not found[/COLOR]'
                table_str.append([platform.compact_name, platform.DAT, DAT_str])

        # Print report
        slist = []
        slist.extend(text_render_table(table_str))
        full_string = '\n'.join(slist)
        kodi_display_text_window_mono('No-Intro/Redump DAT files report', full_string)

    def _command_exec_utils_check_retro_launchers(self):
        log_debug('_command_exec_utils_check_retro_launchers() Starting...')
        slist = []

        # Resolve category IDs to names
        for launcher_id in self.launchers:
            category_id = self.launchers[launcher_id]['categoryID']
            if category_id == 'root_category':
                self.launchers[launcher_id]['category'] = 'No category'
            else:
                self.launchers[launcher_id]['category'] = self.categories[category_id]['m_name']

        # Traverse list of launchers. If launcher uses Retroarch then check the
        # arguments and check that the core pointed with argument -L exists.
        # Sort launcher by category and then name.
        num_retro_launchers = 0
        for launcher_id in sorted(self.launchers,
            key = lambda x: (self.launchers[x]['category'], self.launchers[x]['m_name'])):
            launcher = self.launchers[launcher_id]
            m_name = launcher['m_name']
            # Skip Standalone Launchers
            if not launcher['rompath']:
                log_debug('Skipping launcher "{}"'.format(m_name))
                continue
            log_debug('Checking launcher "{}"'.format(m_name))
            application = launcher['application']
            arguments_list = [launcher['args']]
            arguments_list.extend(launcher['args_extra'])
            if not application.lower().find('retroarch'):
                log_debug('Not a Retroarch launcher "{}"'.format(application))
                continue
            clist = []
            flag_retroarch_launcher = False
            for index, arg_str in enumerate(arguments_list):
                arg_list = shlex.split(arg_str, posix = True)
                log_debug('[index {}] arg_str "{}"'.format(index, arg_str))
                log_debug('[index {}] arg_list {}'.format(index, arg_list))
                for i, arg in enumerate(arg_list):
                    if arg != '-L': continue
                    flag_retroarch_launcher = True
                    num_retro_launchers += 1
                    core_FN = FileName(arg_list[i+1])
                    if core_FN.exists():
                        s = '[COLOR=green]Found[/COLOR] core "{}"\n'.format(core_FN.getPath())
                    else:
                        s = '[COLOR=red]Missing[/COLOR] core "{}"\n'.format(core_FN.getPath())
                    log_debug(s)
                    clist.append(s)
                    break
            # Build report
            if flag_retroarch_launcher:
                slist.append('Category [COLOR orange]{}[/COLOR] - Launcher [COLOR orange]{}[/COLOR]\n'.format(
                    self.launchers[launcher_id]['category'], m_name))
                slist.extend(clist)
                slist.append('\n')
        # Print report
        if num_retro_launchers > 0:
            full_string = ''.join(slist)
            kodi_display_text_window_mono('Retroarch launchers report', full_string)
        else:
            kodi_display_text_window_mono('Retroarch launchers report',
                'No Retroarch launchers found.')

    def _command_exec_utils_check_retro_BIOS(self):
        log_debug('_command_exec_utils_check_retro_BIOS() Checking Retroarch BIOSes ...')
        check_only_mandatory = self.settings['io_retroarch_only_mandatory']
        log_debug('_command_exec_utils_check_retro_BIOS() check_only_mandatory = {0}'.format(check_only_mandatory))

        # >> If Retroarch System dir not configured or found abort.
        sys_dir_FN = FileName(self.settings['io_retroarch_sys_dir'])
        if not sys_dir_FN.exists():
            kodi_dialog_OK('Retroarch System directory not found. Please configure it.')
            return

        # >> Progress dialog
        pDialog = xbmcgui.DialogProgress()
        pDialog_canceled = False
        pDialog.create('Advanced Emulator Launcher', 'Checking Retroarch BIOSes ...')
        num_BIOS = len(Libretro_BIOS_list)
        file_count = 0

        # Algorithm:
        # 1) Traverse list of BIOS. For every BIOS:
        # 2) Check if file exists. If not exists -> missing BIOS.
        # 3) If BIOS exists check file size.
        # 3) If BIOS exists check MD5
        # 4) Unknwon files in Retroarch System dir are ignored and non-reported.
        # 5) Write results into a report TXT file.
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

        # Stats report
        log_info('Writing report file "{0}"'.format(g_PATHS.BIOS_REPORT_FILE_PATH.getPath()))
        full_string = ''.join(str_list)
        file = open(g_PATHS.BIOS_REPORT_FILE_PATH.getPath(), 'w')
        file.write(full_string)
        file.close()

        # Display report TXT file.
        kodi_display_text_window_mono('Retroarch BIOS report', full_string)

    # Use TGDB scraper to get the monthly allowance and report to the user.
    # TGDB API docs https://api.thegamesdb.net/
    def _command_exec_utils_TGDB_check(self):
        # --- Get scraper object and retrieve information ---
        # Treat any error message returned by the scraper as an OK dialog.
        status_dic = kodi_new_status_dic('No error')
        g_scraper_factory = ScraperFactory(g_PATHS, self.settings)
        TGDB = g_scraper_factory.get_scraper_object(SCRAPER_THEGAMESDB_ID)
        TGDB.check_before_scraping(status_dic)
        if not status_dic['status']:
            kodi_dialog_OK(status_dic['msg'])
            return

        # To check the scraper monthly allowance, get the list of platforms as JSON. This JSON
        # data contains the monthly allowance.
        pdialog = KodiProgressDialog()
        pdialog.startProgress('Retrieving info from TheGamesDB...', 100)
        json_data = TGDB.debug_get_genres(status_dic)
        pdialog.endProgress()
        if not status_dic['status']:
            kodi_dialog_OK(status_dic['msg'])
            return
        extra_allowance = json_data['extra_allowance']
        remaining_monthly_allowance = json_data['remaining_monthly_allowance']
        allowance_refresh_timer = json_data['allowance_refresh_timer']
        allowance_refresh_timer_str = str(datetime.timedelta(seconds = allowance_refresh_timer))

        # --- Print and display report ---
        window_title = 'TheGamesDB scraper information'
        sl = []
        sl.append('extra_allowance              {}'.format(extra_allowance))
        sl.append('remaining_monthly_allowance  {}'.format(remaining_monthly_allowance))
        sl.append('allowance_refresh_timer      {}'.format(allowance_refresh_timer))
        sl.append('allowance_refresh_timer_str  {}'.format(allowance_refresh_timer_str))
        sl.append('')
        sl.append('TGDB scraper seems to be working OK.')
        kodi_display_text_window_mono(window_title, '\n'.join(sl))

    # MobyGames API docs https://www.mobygames.com/info/api
    # Currently there is no way to check the MobyGames allowance.
    def _command_exec_utils_MobyGames_check(self):
        # --- Get scraper object and retrieve information ---
        # Treat any error message returned by the scraper as an OK dialog.
        status_dic = kodi_new_status_dic('No error')
        g_scraper_factory = ScraperFactory(g_PATHS, self.settings)
        MobyGames = g_scraper_factory.get_scraper_object(SCRAPER_MOBYGAMES_ID)
        MobyGames.check_before_scraping(status_dic)
        if not status_dic['status']:
            kodi_dialog_OK(status_dic['msg'])
            return

        # TTBOMK, there is no way to know the current limits of MobyGames scraper.
        # Just get the list of platforms and report to the user.
        pdialog = KodiProgressDialog()
        pdialog.startProgress('Retrieving info from MobyGames...', 100)
        json_data = MobyGames.debug_get_platforms(status_dic)
        pdialog.endProgress()
        if not status_dic['status']:
            kodi_dialog_OK(status_dic['msg'])
            return

        # --- Print and display report ---
        window_title = 'MobyGames scraper information'
        sl = []
        sl.append('The API allowance of MobyGames cannot be currently checked.')
        sl.append('')
        sl.append('MobyGames has {} platforms.'.format(len(json_data['platforms'])))
        sl.append('')
        sl.append('MobyGames scraper seems to be working OK.')
        kodi_display_text_window_mono(window_title, '\n'.join(sl))

    # ScreenScraper API docs https://www.screenscraper.fr/webapi.php
    def _command_exec_utils_ScreenScraper_check(self):
        # --- Get scraper object and retrieve information ---
        # Treat any error message returned by the scraper as an OK dialog.
        status_dic = kodi_new_status_dic('No error')
        g_scraper_factory = ScraperFactory(g_PATHS, self.settings)
        ScreenScraper = g_scraper_factory.get_scraper_object(SCRAPER_SCREENSCRAPER_ID)
        ScreenScraper.check_before_scraping(status_dic)
        if not status_dic['status']:
            kodi_dialog_OK(status_dic['msg'])
            return

        # Get ScreenScraper user information
        pdialog = KodiProgressDialog()
        pdialog.startProgress('Retrieving info from ScreenScraper...', 100)
        json_data = ScreenScraper.debug_get_user_info(status_dic)
        pdialog.endProgress()
        if not status_dic['status']:
            kodi_dialog_OK(status_dic['msg'])
            return

        # --- Print and display report ---
        header = json_data['header']
        serveurs = json_data['response']['serveurs']
        ssuser = json_data['response']['ssuser']
        window_title = 'ScreenScraper scraper information'
        sl = []
        sl.append('APIversion           {}'.format(header['APIversion']))
        sl.append('dateTime             {}'.format(header['dateTime']))
        sl.append('cpu1 load            {}%'.format(serveurs['cpu1']))
        sl.append('cpu2 load            {}%'.format(serveurs['cpu2']))
        sl.append('nbscrapeurs          {}'.format(serveurs['nbscrapeurs']))
        sl.append('')
        sl.append('id                   {}'.format(ssuser['id']))
        sl.append('niveau               {}'.format(ssuser['niveau']))
        sl.append('maxthreads           {}'.format(ssuser['maxthreads']))
        sl.append('maxdownloadspeed     {}'.format(ssuser['maxdownloadspeed']))
        sl.append('requeststoday        {}'.format(ssuser['requeststoday']))
        sl.append('requestskotoday      {}'.format(ssuser['requestskotoday']))
        sl.append('maxrequestspermin    {}'.format(ssuser['maxrequestspermin']))
        sl.append('maxrequestsperday    {}'.format(ssuser['maxrequestsperday']))
        sl.append('maxrequestskoperday  {}'.format(ssuser['maxrequestskoperday']))
        sl.append('visites              {}'.format(ssuser['visites']))
        sl.append('datedernierevisite   {}'.format(ssuser['datedernierevisite']))
        sl.append('favregion            {}'.format(ssuser['favregion']))
        sl.append('')
        sl.append('ScreenScraper scraper seems to be working OK.')
        kodi_display_text_window_mono(window_title, '\n'.join(sl))

    # Retrieve an example game to test if ArcadeDB works.
    # TTBOMK there are not API retrictions at the moment (August 2019).
    def _command_exec_utils_ArcadeDB_check(self):
        status_dic = kodi_new_status_dic('No error')
        g_scraper_factory = ScraperFactory(g_PATHS, self.settings)
        ArcadeDB = g_scraper_factory.get_scraper_object(SCRAPER_ARCADEDB_ID)
        ArcadeDB.check_before_scraping(status_dic)
        if not status_dic['status']:
            kodi_dialog_OK(status_dic['msg'])
            return

        search_str = 'atetris'
        rom_FN = FileName('atetris.zip')
        rom_checksums_FN = FileName('atetris.zip')
        platform = 'MAME'

        pdialog = KodiProgressDialog()
        pdialog.startProgress('Retrieving info from ArcadeDB...', 100)
        ArcadeDB.check_candidates_cache(rom_FN, platform)
        ArcadeDB.clear_cache(rom_FN, platform)
        candidates = ArcadeDB.get_candidates(search_str, rom_FN, rom_checksums_FN, platform, status_dic)
        pdialog.endProgress()
        if not status_dic['status']:
            kodi_dialog_OK(status_dic['msg'])
            return
        if len(candidates) != 1:
            kodi_dialog_OK('There is a problem with ArcadeDB scraper.')
            return
        json_response_dic = ArcadeDB.debug_get_QUERY_MAME_dic(candidates[0])

        # --- Print and display report ---
        num_games = len(json_response_dic['result'])
        window_title = 'ArcadeDB scraper information'
        sl = []
        sl.append('num_games      {}'.format(num_games))
        sl.append('game_name      {}'.format(json_response_dic['result'][0]['game_name']))
        sl.append('title          {}'.format(json_response_dic['result'][0]['title']))
        sl.append('emulator_name  {}'.format(json_response_dic['result'][0]['emulator_name']))
        if num_games == 1:
            sl.append('')
            sl.append('ArcadeDB scraper seems to be working OK.')
            sl.append('Remember this scraper only works with platform MAME.')
            sl.append('It will only return valid data for MAME games.')
        kodi_display_text_window_mono(window_title, '\n'.join(sl))

    def _command_exec_global_rom_stats(self):
        log_debug('_command_exec_global_rom_stats() BEGIN')
        window_title = 'Global ROM statistics'
        sl = []
        # sl.append('[COLOR violet]Launcher ROM report.[/COLOR]')
        # sl.append('')

        # --- Table header ---
        table_str = [
            ['left', 'left', 'left'],
            ['Category', 'Launcher', 'ROMs'],
        ]

        # Traverse categories and sort alphabetically.
        log_debug('Number of categories {0}'.format(len(self.categories)))
        log_debug('Number of launchers {0}'.format(len(self.launchers)))
        for cat_id in sorted(self.categories, key = lambda x : self.categories[x]['m_name']):
            # Get launchers of this category alphabetically sorted.
            launcher_list = []
            for launcher_id in sorted(self.launchers, key = lambda x : self.launchers[x]['m_name']):
                launcher = self.launchers[launcher_id]
                # Skip Standalone Launchers
                if not launcher['rompath']: continue
                if launcher['categoryID'] == cat_id: launcher_list.append(launcher)
            # Render list of launchers for this category.
            cat_name = self.categories[cat_id]['m_name']
            for launcher in launcher_list:
                table_str.append([cat_name, launcher['m_name'], str(launcher['num_roms'])])
        # Traverse categoryless launchers.
        catless_launchers = {}
        for launcher_id, launcher in self.launchers.items():
            if launcher['categoryID'] == VCATEGORY_ADDONROOT_ID:
                catless_launchers[launcher_id] = launcher
        for launcher_id in sorted(catless_launchers, key = lambda x : catless_launchers[x]['m_name']):
            launcher = self.launchers[launcher_id]
            # Skip Standalone Launchers
            if not launcher['rompath']: continue
            table_str.append(['', launcher['m_name'], str(launcher['num_roms'])])

        # Generate table and print report
        # log_debug(unicode(table_str))
        sl.extend(text_render_table(table_str))
        kodi_display_text_window_mono(window_title, '\n'.join(sl))

    # TODO Add a table columnd to tell user if the DAT is automatic or custom.
    def _command_exec_global_audit_stats(self, report_type):
        log_debug('_command_exec_global_audit_stats() Report type {}'.format(report_type))
        window_title = 'Global ROM Audit statistics'
        sl = []

        # --- Table header ---
        # Table cell padding: left, right
        table_str = [
            ['left', 'left', 'left', 'left', 'left', 'left', 'left', 'left'],
            ['Category', 'Launcher', 'Platform', 'Type', 'ROMs', 'Have', 'Miss', 'Unknown'],
        ]

        # Traverse categories and sort alphabetically.
        log_debug('Number of categories {0}'.format(len(self.categories)))
        log_debug('Number of launchers {0}'.format(len(self.launchers)))
        for cat_id in sorted(self.categories, key = lambda x : self.categories[x]['m_name']):
            # Get launchers of this category alphabetically sorted.
            launcher_list = []
            for launcher_id in sorted(self.launchers, key = lambda x : self.launchers[x]['m_name']):
                launcher = self.launchers[launcher_id]
                # Skip Standalone Launchers and Launcher with no ROM Audit.
                if not launcher['rompath']: continue
                if launcher['audit_state'] == AUDIT_STATE_OFF: continue
                if launcher['categoryID'] == cat_id: launcher_list.append(launcher)
            # Render list of launchers for this category.
            cat_name = self.categories[cat_id]['m_name']
            for launcher in launcher_list:
                p_index = get_AEL_platform_index(launcher['platform'])
                p_obj = AEL_platforms[p_index]
                # Skip launchers depending on user settings.
                if report_type == AUDIT_REPORT_NOINTRO and p_obj.DAT != DAT_NOINTRO: continue
                if report_type == AUDIT_REPORT_REDUMP and p_obj.DAT != DAT_REDUMP: continue
                table_str.append([
                    cat_name, launcher['m_name'], p_obj.compact_name, p_obj.DAT,
                    str(launcher['num_roms']), str(launcher['num_have']),
                    str(launcher['num_miss']), str(launcher['num_unknown']),
                ])
        # Traverse categoryless launchers.
        catless_launchers = {}
        for launcher_id, launcher in self.launchers.items():
            if launcher['categoryID'] == VCATEGORY_ADDONROOT_ID:
                catless_launchers[launcher_id] = launcher
        for launcher_id in sorted(catless_launchers, key = lambda x : catless_launchers[x]['m_name']):
            launcher = self.launchers[launcher_id]
            # Skip Standalone Launchers
            if not launcher['rompath']: continue

            p_index = get_AEL_platform_index(launcher['platform'])
            p_obj = AEL_platforms[p_index]
            # Skip launchers depending on user settings.
            if report_type == AUDIT_REPORT_NOINTRO and p_obj.DAT != DAT_NOINTRO: continue
            if report_type == AUDIT_REPORT_REDUMP and p_obj.DAT != DAT_REDUMP: continue
            table_str.append([
                ' ', launcher['m_name'], p_obj.compact_name, p_obj.DAT,
                str(launcher['num_roms']), str(launcher['num_have']),
                str(launcher['num_miss']), str(launcher['num_unknown']),
            ])

        # Generate table and print report
        # log_debug(unicode(table_str))
        sl.extend(text_render_table(table_str))
        kodi_display_text_window_mono(window_title, '\n'.join(sl))

    # A set of functions to help making plugin URLs
    # NOTE probably this can be implemented in a more elegant way with optinal arguments...
    def _misc_url_RunPlugin(self, command, categoryID = None, launcherID = None, romID = None):
        log_debug('Advanced Emulator Launcher _misc_url_RunPlugin() BEGIN')

        if romID is not None:
            return 'RunPlugin({0}?com={1}&catID={2}&launID={3}&romID={4})'.format(
                self.base_url, command, categoryID, launcherID, romID)
        elif launcherID is not None:
            return 'RunPlugin({0}?com={1}&catID={2}&launID={3})'.format(
                self.base_url, command, categoryID, launcherID)
        elif categoryID is not None:
            return 'RunPlugin({0}?com={1}&catID={2})'.format(
                self.base_url, command, categoryID)

        return 'RunPlugin({0}?com={1})'.format(self.base_url, command)

    def _misc_url(self, command, categoryID = None, launcherID = None, romID = None):
        if romID is not None:
            return '{0}?com={1}&catID={2}&launID={3}&romID={4}'.format(
                self.base_url, command, categoryID, launcherID, romID)
        elif launcherID is not None:
            return '{0}?com={1}&catID={2}&launID={3}'.format(
                self.base_url, command, categoryID, launcherID)
        elif categoryID is not None:
            return '{0}?com={1}&catID={2}'.format(self.base_url, command, categoryID)

        return '{0}?com={1}'.format(self.base_url, command)

    def _misc_url_search(self, command, categoryID, launcherID, search_type, search_string):
        return '{0}?com={1}&catID={2}&launID={3}&search_type={4}&search_string={5}'.format(
            self.base_url, command, categoryID, launcherID, search_type, search_string)

    def _command_buildMenu(self):
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
            path = FileName(skinshortcutsAddon.getAddonInfo('path'))

            libPath = path.pjoin('resources', 'lib')
            sys.path.append(libPath.getPath())

            unidecodeModule = xbmcaddon.Addon('script.module.unidecode')
            libPath = FileName(unidecodeModule.getAddonInfo('path'))
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
            for key in sorted(self.categories, key = lambda x : self.categories[x]['m_name']):
                category_dic = self.categories[key]
                name = category_dic['m_name']
                url_str =  "ActivateWindow(Programs,\"%s\",return)" % self._misc_url('SHOW_LAUNCHERS', key)
                fanart = asset_get_default_asset_Category(category_dic, 'default_fanart')
                thumb = asset_get_default_asset_Category(category_dic, 'default_thumb', 'DefaultFolder.png')

                log_debug('_command_buildMenu() Adding Category "{0}"'.format(name))
                listitem = self._buildMenuItem(key, name, url_str, thumb, fanart, count, ui)
                selectedMenuItems.append(listitem)

        if typeOfContent == 1:
            for key in sorted(self.launchers, key = lambda x : self.launchers[x]['application']):
                launcher_dic = self.launchers[key]
                name = launcher_dic['m_name']
                launcherID = launcher_dic['id']
                categoryID = launcher_dic['categoryID']
                url_str =  "ActivateWindow(Programs,\"%s\",return)" % self._misc_url('SHOW_ROMS', categoryID, launcherID)
                fanart = asset_get_default_asset_Category(launcher_dic, 'default_fanart')
                thumb = asset_get_default_asset_Category(launcher_dic, 'default_thumb', 'DefaultFolder.png')

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

    def _buildMenuItem(self, key, name, action, thumb, fanart, count, ui):

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
