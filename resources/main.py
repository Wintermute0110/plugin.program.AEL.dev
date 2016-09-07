# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher main script file
#

# Copyright (c) 2016 Wintermute0110 <wintermute0110@gmail.com>
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

# Addon programming conventions,
# 1) A function with a underline _function() belongs to the Main object, even if not defined in the
#    main body.

# --- Python standard library ---
from __future__ import unicode_literals
import sys, os, shutil, fnmatch, string, time
import re, urllib, urllib2, urlparse, socket, exceptions, hashlib
import subprocess

# --- Kodi stuff ---
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

# --- Modules/packages in this plugin ---
import subprocess_hack
from disk_IO import *
from net_IO import *
from utils import *
from utils_kodi import *
from scrap import *
from assets import *

# --- Addon object (used to access settings) ---
__addon_obj__     = xbmcaddon.Addon()
__addon_id__      = __addon_obj__.getAddonInfo('id').decode('utf-8')
__addon_name__    = __addon_obj__.getAddonInfo('name').decode('utf-8')
__addon_version__ = __addon_obj__.getAddonInfo('version').decode('utf-8')
__addon_author__  = __addon_obj__.getAddonInfo('author').decode('utf-8')
__addon_profile__ = __addon_obj__.getAddonInfo('profile').decode('utf-8')
__addon_type__    = __addon_obj__.getAddonInfo('type').decode('utf-8')

# --- Addon paths and constant definition ---
# _FILE_PATH is a filename
# _DIR is a directory (with trailing /)
PLUGIN_DATA_DIR       = xbmc.translatePath(os.path.join('special://profile/addon_data', __addon_id__)).decode('utf-8')
BASE_DIR              = xbmc.translatePath(os.path.join('special://', 'profile')).decode('utf-8')
HOME_DIR              = xbmc.translatePath(os.path.join('special://', 'home')).decode('utf-8')
KODI_FAV_FILE_PATH    = xbmc.translatePath('special://profile/favourites.xml').decode('utf-8')
ADDONS_DIR            = xbmc.translatePath(os.path.join(HOME_DIR, 'addons')).decode('utf-8')
CURRENT_ADDON_DIR     = xbmc.translatePath(os.path.join(ADDONS_DIR, __addon_id__)).decode('utf-8')
ICON_IMG_FILE_PATH    = os.path.join(CURRENT_ADDON_DIR, 'icon.png').decode('utf-8')
CATEGORIES_FILE_PATH  = os.path.join(PLUGIN_DATA_DIR, 'categories.xml').decode('utf-8')
FAV_JSON_FILE_PATH    = os.path.join(PLUGIN_DATA_DIR, 'favourites.json').decode('utf-8')
COLLECTIONS_FILE_PATH = os.path.join(PLUGIN_DATA_DIR, 'collections.xml').decode('utf-8')
VCAT_TITLE_FILE_PATH  = os.path.join(PLUGIN_DATA_DIR, 'vcat_title.xml').decode('utf-8')
VCAT_YEARS_FILE_PATH  = os.path.join(PLUGIN_DATA_DIR, 'vcat_years.xml').decode('utf-8')
VCAT_GENRE_FILE_PATH  = os.path.join(PLUGIN_DATA_DIR, 'vcat_genre.xml').decode('utf-8')
VCAT_STUDIO_FILE_PATH = os.path.join(PLUGIN_DATA_DIR, 'vcat_studio.xml').decode('utf-8')
LAUNCH_LOG_FILE_PATH  = os.path.join(PLUGIN_DATA_DIR, 'launcher.log').decode('utf-8')

# --- Artwork and NFO for Categories and Launchers ---
DEFAULT_CAT_ASSET_DIR  = os.path.join(PLUGIN_DATA_DIR, 'asset-categories').decode('utf-8')
DEFAULT_COL_ASSET_DIR  = os.path.join(PLUGIN_DATA_DIR, 'asset-collections').decode('utf-8')
DEFAULT_LAUN_ASSET_DIR = os.path.join(PLUGIN_DATA_DIR, 'asset-launchers').decode('utf-8')
DEFAULT_FAV_ASSET_DIR  = os.path.join(PLUGIN_DATA_DIR, 'asset-favourites').decode('utf-8')
VIRTUAL_CAT_TITLE_DIR  = os.path.join(PLUGIN_DATA_DIR, 'db_title').decode('utf-8')
VIRTUAL_CAT_YEARS_DIR  = os.path.join(PLUGIN_DATA_DIR, 'db_years').decode('utf-8')
VIRTUAL_CAT_GENRE_DIR  = os.path.join(PLUGIN_DATA_DIR, 'db_genre').decode('utf-8')
VIRTUAL_CAT_STUDIO_DIR = os.path.join(PLUGIN_DATA_DIR, 'db_studio').decode('utf-8')
ROMS_DIR               = os.path.join(PLUGIN_DATA_DIR, 'db_ROMs').decode('utf-8')
COLLECTIONS_DIR        = os.path.join(PLUGIN_DATA_DIR, 'db_Collections').decode('utf-8')
REPORTS_DIR            = os.path.join(PLUGIN_DATA_DIR, 'reports').decode('utf-8')

# --- Misc "constants" ---
KIND_CATEGORY            = 1
KIND_COLLECTION          = 2
KIND_LAUNCHER            = 3
KIND_ROM                 = 4
DESCRIPTION_MAXSIZE      = 40
VCATEGORY_FAVOURITES_ID  = 'vcat_favourites'
VCATEGORY_COLLECTIONS_ID = 'vcat_collections'
VCATEGORY_TITLE_ID       = 'vcat_title'
VCATEGORY_YEARS_ID       = 'vcat_years'
VCATEGORY_GENRE_ID       = 'vcat_genre'
VCATEGORY_STUDIO_ID      = 'vcat_studio'
VLAUNCHER_FAVOURITES_ID  = 'vlauncher_favourites'

# --- Main code ---
class Main:
    update_timestamp = 0.0
    settings         = {}
    categories       = {}
    launchers        = {}
    roms             = {}
    scraper_metadata = None
    scraper_asset    = None

    #
    # This is the plugin entry point.
    #
    def run_plugin(self):
        # --- Initialise log system ---
        # Force DEBUG log level for development.
        # Place it before setting loading so settings can be dumped during debugging.
        # set_log_level(LOG_DEBUG)

        # --- Fill in settings dictionary using __addon_obj__.getSetting() ---
        self._get_settings()
        set_log_level(self.settings['log_level'])

        # --- Some debug stuff for development ---
        log_debug('---------- Called AEL addon.py Main() constructor ----------')
        log_debug('sys.platform = "{0}"'.format(sys.platform))
        log_debug('Python version ' + sys.version.replace('\n', ''))
        # log_debug('__addon_name__    {0}'.format(__addon_name__))
        # log_debug('__addon_id__      {0}'.format(__addon_id__))
        log_debug('__addon_version__ {0}'.format(__addon_version__))
        # log_debug('__addon_author__  {0}'.format(__addon_author__))
        # log_debug('__addon_profile__ {0}'.format(__addon_profile__))
        # log_debug('__addon_type__    {0}'.format(__addon_type__))
        for i in range(len(sys.argv)):
            log_debug('sys.argv[{0}] = "{1}"'.format(i, sys.argv[i]))
        # log_debug('PLUGIN_DATA_DIR   "{0}"'.format(PLUGIN_DATA_DIR))
        # log_debug('CURRENT_ADDON_DIR "{0}"'.format(CURRENT_ADDON_DIR))

        # --- Addon data paths creation ---
        if not os.path.isdir(PLUGIN_DATA_DIR):        os.makedirs(PLUGIN_DATA_DIR)
        if not os.path.isdir(DEFAULT_CAT_ASSET_DIR):  os.makedirs(DEFAULT_CAT_ASSET_DIR)
        if not os.path.isdir(DEFAULT_COL_ASSET_DIR):  os.makedirs(DEFAULT_COL_ASSET_DIR)
        if not os.path.isdir(DEFAULT_LAUN_ASSET_DIR): os.makedirs(DEFAULT_LAUN_ASSET_DIR)
        if not os.path.isdir(DEFAULT_FAV_ASSET_DIR):  os.makedirs(DEFAULT_FAV_ASSET_DIR)
        if not os.path.isdir(VIRTUAL_CAT_TITLE_DIR):  os.makedirs(VIRTUAL_CAT_TITLE_DIR)
        if not os.path.isdir(VIRTUAL_CAT_YEARS_DIR):  os.makedirs(VIRTUAL_CAT_YEARS_DIR)
        if not os.path.isdir(VIRTUAL_CAT_GENRE_DIR):  os.makedirs(VIRTUAL_CAT_GENRE_DIR)
        if not os.path.isdir(VIRTUAL_CAT_STUDIO_DIR): os.makedirs(VIRTUAL_CAT_STUDIO_DIR)
        if not os.path.isdir(ROMS_DIR):               os.makedirs(ROMS_DIR)
        if not os.path.isdir(COLLECTIONS_DIR):        os.makedirs(COLLECTIONS_DIR)
        if not os.path.isdir(REPORTS_DIR):            os.makedirs(REPORTS_DIR)

        # ~~~~~ Process URL ~~~~~
        self.base_url = sys.argv[0]
        self.addon_handle = int(sys.argv[1])
        args = urlparse.parse_qs(sys.argv[2][1:])
        log_debug('args = {0}'.format(args))
        # Interestingly, if plugin is called as type executable then args is empty.
        # However, if plugin is called as type video then Kodi adds the following
        # even for the first call: 'content_type': ['video']
        self.content_type = args['content_type'] if 'content_type' in args else None
        log_debug('content_type = {0}'.format(self.content_type))

        # --- Addon first-time initialisation ---
        # When the addon is installed and the file categories.xml does not exist, just
        # create an empty one with a default launcher.
        if not os.path.isfile(CATEGORIES_FILE_PATH):
            kodi_dialog_OK('It looks it is the first time you run Advanced Emulator Launcher! ' +
                           'A default categories.xml has been created. You can now customise it to your needs.')
            self._cat_create_default()
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

        # --- Load categories.xml and fill categories and launchers dictionaries ---
        (self.update_timestamp, self.categories, self.launchers) = fs_load_catfile(CATEGORIES_FILE_PATH)

        # If no com parameter display categories. Display categories listbox (addon root directory)
        if 'com' not in args:
            self._command_render_categories()
            log_debug('Advanced Emulator Launcher exit (addon root)')
            return

        # There is a command to process
        # For some reason args['com'] is a list, so get first element of the list (a string)
        command = args['com'][0]
        if command == 'SHOW_ALL_CATEGORIES':
            self._command_render_all_categories()
        elif command == 'ADD_CATEGORY':
            self._command_add_new_category()
        elif command == 'EDIT_CATEGORY':
            self._command_edit_category(args['catID'][0])
        elif command == 'SHOW_FAVOURITES':
            self._command_render_favourites()
        elif command == 'SHOW_VIRTUAL_CATEGORY':
            self._command_render_virtual_category(args['catID'][0])
        elif command == 'SHOW_COLLECTIONS':
            self._command_render_collections()
        elif command == 'SHOW_COLLECTION_ROMS':
            self._command_render_collection_ROMs(args['catID'][0], args['launID'][0])
        elif command == 'ADD_COLLECTION':
            self._command_add_collection()
        elif command == 'EDIT_COLLECTION':
            self._command_edit_collection(args['catID'][0], args['launID'][0])
        elif command == 'DELETE_COLLECTION':
            self._command_delete_collection(args['catID'][0], args['launID'][0])
        elif command == 'MOVE_COL_ROM_UP':
            self._command_move_collection_rom_up(args['catID'][0], args['launID'][0], args['romID'][0])
        elif command == 'MOVE_COL_ROM_DOWN':
            self._command_move_collection_rom_down(args['catID'][0], args['launID'][0], args['romID'][0])
        elif command == 'SHOW_LAUNCHERS':
            self._command_render_launchers(args['catID'][0])
        elif command == 'SHOW_ALL_LAUNCHERS':
            self._command_render_all_launchers()
        elif command == 'ADD_LAUNCHER':
            self._command_add_new_launcher(args['catID'][0])
        elif command == 'EDIT_LAUNCHER':
            self._command_edit_launcher(args['catID'][0], args['launID'][0])
        # User clicked on a launcher. For standalone launchers run the executable.
        # For emulator launchers show roms.
        elif command == 'SHOW_ROMS':
            launcherID = args['launID'][0]
            # >> Virtual launcher in virtual category (title/year/genre/studio), favourite ROMs or Collection
            if launcherID not in self.launchers:
                log_debug('SHOW_ROMS | Virtual launcher = {0}'.format(args['catID'][0]))
                log_debug('SHOW_ROMS | Calling _command_render_virtual_launcher_roms()')
                self._command_render_virtual_launcher_roms(args['catID'][0], args['launID'][0])
            elif self.launchers[launcherID]['rompath'] == '':
                log_debug('SHOW_ROMS | Launcher rompath is empty. Assuming launcher is standalone.')
                log_debug('SHOW_ROMS | Calling _command_run_standalone_launcher()')
                self._command_run_standalone_launcher(args['catID'][0], args['launID'][0])
            else:
                log_debug('SHOW_ROMS | Calling _command_render_roms()')
                self._command_render_roms(args['catID'][0], args['launID'][0])
        elif command == 'ADD_ROMS':
            self._command_add_roms(args['launID'][0])
        # Edit ROM from launcher or Favourites
        elif command == 'EDIT_ROM':
            self._command_edit_rom(args['catID'][0], args['launID'][0], args['romID'][0])
        # Delete ROM for launcher or Favourites
        elif command == 'DELETE_ROM':
             self._command_remove_rom(args['catID'][0], args['launID'][0], args['romID'][0])
        elif command == 'LAUNCH_ROM':
            self._command_run_rom(args['catID'][0], args['launID'][0], args['romID'][0])
        elif command == 'ADD_TO_FAV':
            self._command_add_to_favourites(args['catID'][0], args['launID'][0], args['romID'][0])
        elif command == 'ADD_TO_COLLECTION':
            self._command_add_ROM_to_collection(args['catID'][0], args['launID'][0], args['romID'][0])          
        elif command == 'MANAGE_FAV':
            self._command_manage_favourites(args['catID'][0], args['launID'][0], args['romID'][0])
        # This command is issued when user clicks on "Search" on the context menu of a launcher
        # in the launchers view, or context menu inside a launcher. User is asked to enter the
        # search string and the field to search (name, category, etc.)
        elif command == 'SEARCH_LAUNCHER':
            self._command_search_launcher(args['catID'][0], args['launID'][0])
        elif command == 'EXEC_SEARCH_LAUNCHER':
            self._command_execute_search_launcher(args['catID'][0], args['launID'][0],
                                                  args['search_type'][0], args['search_string'][0])
        # >> Shows info about categories/launchers/ROMs and reports
        elif command == 'VIEW_ROM':
            self._command_view_ROM(args['catID'][0], args['launID'][0], args['romID'][0])
        elif command == 'VIEW_LAUNCHER':
            self._command_view_Launcher(args['catID'][0], args['launID'][0])
        elif command == 'VIEW_CATEGORY':
            self._command_view_Category(args['catID'][0])
        elif command == 'VIEW_LAUNCHER_REPORT':
            self._command_view_Launcher_Report(args['catID'][0], args['launID'][0])
        # >> Update virtual categories databases
        elif command == 'UPDATE_VIRTUAL_CATEGORY':
            self._command_update_virtual_category_db(args['catID'][0])
        elif command == 'UPDATE_ALL_VCATEGORIES':
            self._command_update_virtual_category_db_all()
        elif command == 'IMPORT_AL_LAUNCHERS':
            self._command_import_legacy_AL()
        else:
            kodi_dialog_OK('Unknown command {0}'.format(args['com'][0]) )

        log_debug('Advanced Emulator Launcher exit')

    #
    # Get Addon Settings
    #
    def _get_settings(self):
        # Get the users preference settings
        self.settings = {}

        # --- ROM Scanner settings ---
        self.settings['scan_recursive']          = True if __addon_obj__.getSetting('scan_recursive') == 'true' else False
        self.settings['scan_ignore_bios']        = True if __addon_obj__.getSetting('scan_ignore_bios') == 'true' else False
        self.settings['scan_metadata_policy']    = int(__addon_obj__.getSetting('scan_metadata_policy'))
        self.settings['scan_asset_policy']       = int(__addon_obj__.getSetting('scan_asset_policy'))
        self.settings['scan_ignore_scrap_title'] = True if __addon_obj__.getSetting('scan_ignore_scrap_title') == 'true' else False
        self.settings['scan_clean_tags']         = True if __addon_obj__.getSetting('scan_clean_tags') == 'true' else False

        # --- ROM scraping ---
        self.settings['metadata_scraper']        = int(__addon_obj__.getSetting('metadata_scraper'))
        self.settings['asset_scraper']           = int(__addon_obj__.getSetting('asset_scraper'))

        self.settings['metadata_scraper_mode']   = int(__addon_obj__.getSetting('metadata_scraper_mode'))
        self.settings['asset_scraper_mode']      = int(__addon_obj__.getSetting('asset_scraper_mode'))

        # --- Scrapers ---
        self.settings['scraper_region']          = int(__addon_obj__.getSetting('scraper_region'))
        self.settings['scraper_thumb_size']      = int(__addon_obj__.getSetting('scraper_thumb_size'))
        self.settings['scraper_fanart_size']     = int(__addon_obj__.getSetting('scraper_fanart_size'))
        self.settings['scraper_image_type']      = int(__addon_obj__.getSetting('scraper_image_type'))
        self.settings['scraper_fanart_order']    = int(__addon_obj__.getSetting('scraper_fanart_order'))

        # --- Display ---
        self.settings['display_launcher_notify'] = True if __addon_obj__.getSetting('display_launcher_notify') == 'true' else False
        self.settings['display_hide_finished']   = True if __addon_obj__.getSetting('display_hide_finished') == 'true' else False
        self.settings['display_hide_title']      = True if __addon_obj__.getSetting('display_hide_title') == 'true' else False
        self.settings['display_hide_year']       = True if __addon_obj__.getSetting('display_hide_year') == 'true' else False
        self.settings['display_hide_genre']      = True if __addon_obj__.getSetting('display_hide_genre') == 'true' else False
        self.settings['display_hide_studio']     = True if __addon_obj__.getSetting('display_hide_studio') == 'true' else False

        # --- Paths ---
        self.settings['categories_asset_dir']    = __addon_obj__.getSetting('categories_asset_dir').decode('utf-8')
        self.settings['launchers_asset_dir']     = __addon_obj__.getSetting('launchers_asset_dir').decode('utf-8')
        self.settings['favourites_asset_dir']    = __addon_obj__.getSetting('favourites_asset_dir').decode('utf-8')
        self.settings['collections_asset_dir']   = __addon_obj__.getSetting('collections_asset_dir').decode('utf-8')

        # --- Advanced ---
        self.settings['media_state']             = int(__addon_obj__.getSetting('media_state'))
        self.settings['lirc_state']              = True if __addon_obj__.getSetting('lirc_state') == 'true' else False
        self.settings['start_tempo']             = int(round(float(__addon_obj__.getSetting('start_tempo'))))
        self.settings['escape_romfile']          = True if __addon_obj__.getSetting('escape_romfile') == 'true' else False
        self.settings['log_level']               = int(__addon_obj__.getSetting('log_level'))
        self.settings['show_batch_window']       = True if __addon_obj__.getSetting('show_batch_window') == 'true' else False

        # >> Check if user changed default artwork paths for categories/launchers. If not, set defaults.
        if self.settings['categories_asset_dir']  == '': self.settings['categories_asset_dir']  = DEFAULT_CAT_ASSET_DIR
        if self.settings['launchers_asset_dir']   == '': self.settings['launchers_asset_dir']   = DEFAULT_LAUN_ASSET_DIR
        if self.settings['favourites_asset_dir']  == '': self.settings['favourites_asset_dir']  = DEFAULT_FAV_ASSET_DIR
        if self.settings['collections_asset_dir'] == '': self.settings['collections_asset_dir'] = DEFAULT_COL_ASSET_DIR

        # --- Dump settings for DEBUG ---
        # log_debug('Settings dump BEGIN')
        # for key in sorted(self.settings):
        #     log_debug('{0} --> {1:10s} {2}'.format(key.rjust(21), str(self.settings[key]), type(self.settings[key])))
        # log_debug('Settings dump END')

    #
    # Load scrapers based on the user settings.
    # Pass settings to the scraper objects based on user preferences.
    # Scrapers are loaded when needed, no always at main() as before. This will make the plugin
    # a little bit faster.
    #
    def _load_metadata_scraper(self):
        # Scraper objects are created and inserted into a list. This list order matches
        # exactly the number returned by the settings. If scrapers are changed make sure the
        # list in scrapers.py and in settings.xml have same values!
        self.scraper_metadata = scrapers_metadata[self.settings['metadata_scraper']]
        log_verb('_load_metadata_scraper() Loaded metadata scraper {0}'.format(self.scraper_metadata.name))

        # Initialise metadata scraper plugin installation dir, for offline scrapers
        self.scraper_metadata.set_addon_dir(CURRENT_ADDON_DIR)

    def _load_asset_scraper(self):
        self.scraper_asset = scrapers_asset[self.settings['asset_scraper']]
        log_verb('_load_asset_scraper() Loaded asset scraper {0}'.format(self.scraper_asset.name))

        # Initialise options of the thumb scraper
        region = self.settings['scraper_region']
        thumb_imgsize = self.settings['scraper_thumb_size']
        self.scraper_asset.set_options(region, thumb_imgsize)

    #
    # Set content type and sorting methods
    #
    def _misc_set_content_type(self):
        # >> Experiment to try to increase the number of views the addon supports. I do not know why
        # >> programs does not support all views movies do.
        # xbmcplugin.setContent(handle = self.addon_handle, content = 'movies')
        pass

    def _misc_set_content_and_all_sorting_methods(self):
        self._misc_set_content_type()

        # >> Adds a sorting method for the media list.
        # >> This must be called only if self.addon_handle > 0, otherwise Kodi will complain in the log.
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_STUDIO)
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_GENRE)
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)

    def _command_add_new_category(self):
        dialog = xbmcgui.Dialog()
        keyboard = xbmc.Keyboard('', 'New Category Name')
        keyboard.doModal()
        if not keyboard.isConfirmed(): return

        category = fs_new_category()
        categoryID = misc_generate_random_SID()
        category['id']     = categoryID
        category['m_name'] = keyboard.getText().decode('utf-8')
        self.categories[categoryID] = category
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
        kodi_notify('Category {0} created'.format(category['m_name']))
        kodi_refresh_container()

    def _command_edit_category(self, categoryID):
        # --- Load scrapers ---
        self._load_metadata_scraper()
        self._load_asset_scraper()

        # --- Shows a select box with the options to edit ---
        dialog = xbmcgui.Dialog()
        finished_display = 'Status: Finished' if self.categories[categoryID]['finished'] == True else 'Status: Unfinished'
        type = dialog.select('Select action for category {0}'.format(self.categories[categoryID]['m_name']),
                             ['Edit Metadata...', 'Edit Assets/Artwork...', 'Choose default Assets/Artwork...',
                              finished_display, 'Delete Category'])

        # --- Edit category metadata ---
        if type == 0:
            plot_str = text_limit_string(self.categories[categoryID]['m_plot'], DESCRIPTION_MAXSIZE)
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Edit Category Metadata',
                                  ['Import metadata from NFO (automatic)',
                                   'Import metadata from NFO (browse NFO)...',
                                   "Edit Title: '{0}'".format(self.categories[categoryID]['m_name']),
                                   "Edit Genre: '{0}'".format(self.categories[categoryID]['m_genre']),
                                   "Edit Rating: '{0}'".format(self.categories[categoryID]['m_rating']),
                                   "Edit Plot: '{0}'".format(plot_str),
                                   'Save metadata to NFO file'])
            # --- Import launcher metadata from NFO file (automatic) ---
            if type2 == 0:
                # >> Get NFO file name for launcher
                NFO_file = fs_get_category_NFO_name(self.settings, self.categories[categoryID])

                # >> Launcher is edited using Python passing by assigment
                # >> Returns True if changes were made
                if not fs_import_category_NFO(NFO_file, self.categories, categoryID): return

            # --- Browse for NFO file ---
            elif type2 == 1:
                # >> Get launcher NFO file
                # No-Intro reading of files: use Unicode string for '.dat|.xml'. However, | belongs to ASCII...
                NFO_file = xbmcgui.Dialog().browse(1, 'Select description file (NFO)', 'files', '.nfo', False, False).decode('utf-8')
                if not os.path.isfile(NFO_file): return

                # >> Launcher is edited using Python passing by assigment
                # >> Returns True if changes were made
                if not fs_import_category_NFO(NFO_file, self.categories, categoryID): return

            # --- Edition of the category name ---
            elif type2 == 2:
                keyboard = xbmc.Keyboard(self.categories[categoryID]['m_name'], 'Edit Title')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    title = keyboard.getText().decode('utf-8')
                    if title == '':
                        title = self.categories[categoryID]['m_name']
                    self.categories[categoryID]['m_name'] = title.rstrip()
                else:
                    kodi_dialog_OK("Category name '{0}' not changed".format(self.categories[categoryID]['m_name']))
                    return

            # --- Edition of the category genre ---
            elif type2 == 3:
                keyboard = xbmc.Keyboard(self.categories[categoryID]['m_genre'], 'Edit Genre')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    self.categories[categoryID]['m_genre'] = keyboard.getText().decode('utf-8')
                else:
                    kodi_dialog_OK("Category genre '{0}' not changed".format(self.categories[categoryID]['m_genre']))
                    return

            # --- Edition of the category rating ---
            elif type2 == 4:
                rating = dialog.select('Edit Category Rating',
                                      ['Not set',  'Rating 0', 'Rating 1', 'Rating 2', 'Rating 3', 'Rating 4',
                                       'Rating 5', 'Rating 6', 'Rating 7', 'Rating 8', 'Rating 9', 'Rating 10'])
                # >> Rating not set, empty string
                if rating == 0:
                    self.categories[categoryID]['m_rating'] = ''
                elif rating >= 1 and rating <= 11:
                    self.categories[categoryID]['m_rating'] = '{0}'.format(rating - 1)
                elif rating < 0:
                    kodi_dialog_OK("Category rating '{0}' not changed".format(self.categories[categoryID]['m_rating']))
                    return

            # --- Edition of the plot (description) ---
            elif type2 == 5:
                keyboard = xbmc.Keyboard(self.categories[categoryID]['m_plot'], 'Edit Plot')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    self.categories[categoryID]['m_plot'] = keyboard.getText()
                else:
                    kodi_dialog_OK("Category plot '{0}' not changed".format(self.categories[categoryID]['m_plot']))
                    return

            # --- Import category description ---
            # elif type2 == 3:
            #     text_file = xbmcgui.Dialog().browse(1, 'Select description file (TXT|DAT)', 'files', '.txt|.dat', False, False)
            #     if os.path.isfile(text_file):
            #         file_data = self._gui_import_TXT_file(text_file)
            #         if file_data != '':
            #             self.categories[categoryID]["description"] = file_data
            #         else:
            #             return
            #     else:
            #         desc_str = text_limit_string(self.categories[categoryID]['description'], DESCRIPTION_MAXSIZE)
            #         kodi_dialog_OK("Category description '{0}' not changed".format(desc_str))
            #         return

            # --- Export launcher metadata to NFO file ---
            elif type2 == 6:
                NFO_file = fs_get_category_NFO_name(self.settings, self.categories[categoryID])
                fs_export_category_NFO(NFO_file, self.categories[categoryID])
                # >> No need to save launchers
                return

            # >> User canceled select dialog
            elif type2 < 0:
                return

        # --- Edit Category Asstes/Artwork ---
        elif type == 1:
            category = self.categories[categoryID]
            status_thumb_str   = 'HAVE' if category['s_thumb']   else 'MISSING'
            status_fanart_str  = 'HAVE' if category['s_fanart']  else 'MISSING'
            status_banner_str  = 'HAVE' if category['s_banner']  else 'MISSING'
            status_flyer_str   = 'HAVE' if category['s_flyer']   else 'MISSING'
            status_trailer_str = 'HAVE' if category['s_trailer'] else 'MISSING'
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Edit Category Assets/Artwork',
                                  ["Edit Thumbnail ({0})...".format(status_thumb_str),
                                   "Edit Fanart ({0})...".format(status_fanart_str),
                                   "Edit Banner ({0})...".format(status_banner_str),
                                   "Edit Flyer ({0})...".format(status_flyer_str),
                                   "Edit Trailer ({0})...".format(status_trailer_str)])

            # --- Edit Assets ---
            # >> _gui_edit_asset() returns True if image was changed
            # >> Category is changed using Python passign by assigment
            # >> If this function returns False no changes were made. No need to save categories XML and 
            # >> update container.
            if type2 == 0:
                if not self._gui_edit_asset(KIND_CATEGORY, ASSET_THUMB, category): return
            elif type2 == 1:
                if not self._gui_edit_asset(KIND_CATEGORY, ASSET_FANART, category): return
            elif type2 == 2:
                if not self._gui_edit_asset(KIND_CATEGORY, ASSET_BANNER, category): return
            elif type2 == 3:
                if not self._gui_edit_asset(KIND_CATEGORY, ASSET_FLYER, category): return
            elif type2 == 4:
                if not self._gui_edit_asset(KIND_CATEGORY, ASSET_TRAILER, category): return
            # >> User canceled select dialog
            elif type2 < 0: return

        # --- Choose default thumb/fanart ---
        elif type == 2:
            category        = self.categories[categoryID]
            asset_thumb     = assets_get_asset_name_str(category['default_thumb'])
            asset_fanart    = assets_get_asset_name_str(category['default_fanart'])
            asset_banner    = assets_get_asset_name_str(category['default_banner'])
            asset_poster    = assets_get_asset_name_str(category['default_poster'])
            asset_clearlogo = assets_get_asset_name_str(category['default_clearlogo'])
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Edit Category Assets/Artwork',
                                  ['Choose asset for Thumb (currently {0})'.format(asset_thumb), 
                                   'Choose asset for Fanart (currently {0})'.format(asset_fanart),
                                   'Choose asset for Banner (currently {0})'.format(asset_banner),
                                   'Choose asset for Poster (currently {0})'.format(asset_poster),
                                   'Choose asset for Clearlogo (currently {0})'.format(asset_clearlogo)])

            if type2 == 0:
                dialog = xbmcgui.Dialog()
                type3 = dialog.select('Choose default Asset for Thumb', DEFAULT_CATEGORY_ASSET_LIST)
                if type3 < 0: return
                assets_choose_category_artwork(category, 'default_thumb', type3)

            elif type2 == 1:
                dialog = xbmcgui.Dialog()
                type3 = dialog.select('Choose default Asset for Fanart', DEFAULT_CATEGORY_ASSET_LIST)
                if type3 < 0: return
                assets_choose_category_artwork(category, 'default_fanart', type3)

            elif type2 == 2:
                dialog = xbmcgui.Dialog()
                type3 = dialog.select('Choose default Asset for Banner', DEFAULT_CATEGORY_ASSET_LIST)
                if type3 < 0: return
                assets_choose_category_artwork(category, 'default_banner', type3)

            elif type2 == 3:
                dialog = xbmcgui.Dialog()
                type3 = dialog.select('Choose default Asset for Poster', DEFAULT_CATEGORY_ASSET_LIST)
                if type3 < 0: return
                assets_choose_category_artwork(category, 'default_poster', type3)

            elif type2 == 4:
                dialog = xbmcgui.Dialog()
                type3 = dialog.select('Choose default Asset for Clearlogo', DEFAULT_CATEGORY_ASSET_LIST)
                if type3 < 0: return
                assets_choose_category_artwork(category, 'default_clearlogo', type3)

            # >> User canceled select dialog
            elif type2 < 0: return

        # --- Category status ---
        elif type == 3:
            finished = self.categories[categoryID]['finished']
            finished = False if finished else True
            finished_display = 'Finished' if finished == True else 'Unfinished'
            self.categories[categoryID]['finished'] = finished
            kodi_dialog_OK('Category "{0}" status is now {1}'.format(self.categories[categoryID]['m_name'], finished_display))

        # --- Remove category. Also removes launchers in that category ---
        elif type == 4:
            launcherID_list = []
            category_name = self.categories[categoryID]['m_name']
            for launcherID in sorted(self.launchers.iterkeys()):
                if self.launchers[launcherID]['id'] == categoryID:
                    launcherID_list.append(launcherID)

            if len(launcherID_list) > 0:
                ret = kodi_dialog_yesno('Category "{0}" contains {1} launchers. '.format(category_name, len(launcherID_list)) +
                                        'Deleting it will also delete related launchers. ' +
                                        'Are you sure you want to delete "{0}"?'.format(category_name))
                if not ret: return
                log_info('Deleting category "{0}" id {1}'.format(category_name, categoryID))
                # Delete launchers and ROM XML associated with them
                for launcherID in launcherID_list:
                    log_info('Deleting linked launcher "{0}" id {1}'.format(self.launchers[launcherID]['m_name'], launcherID))
                    # >> Delete information XML file
                    roms_xml_file = fs_get_ROMs_XML_file_path(ROMS_DIR, self.launchers[launcherID]['roms_base_noext'])
                    if os.path.isfile(roms_xml_file):
                        log_info('Deleting ROMs XML  "{0}"'.format(roms_xml_file))
                        os.remove(roms_xml_file)
                    # >> Delete ROMs JSON file
                    roms_json_file = fs_get_ROMs_JSON_file_path(ROMS_DIR, self.launchers[launcherID]['roms_base_noext'])
                    if os.path.isfile(roms_json_file):
                        log_info('Deleting ROMs JSON "{0}"'.format(roms_json_file))
                        os.remove(roms_json_file)
                    self.launchers.pop(launcherID)
                # Delete category and make sure True is returned.
                self.categories.pop(categoryID)
            else:
                ret = kodi_dialog_yesno('Category "{0}" contains {1} launchers. '.format(category_name, len(launcherID_list)) +
                                        'Are you sure you want to delete "{0}"?'.format(category_name))
                if not ret: return
                log_info('Deleting category "{0}" id {1}'.format(category_name, categoryID))
                log_info('Category has no launchers, so no launchers to delete.')
                self.categories.pop(categoryID)

        # >> User pressed cancel or close dialog
        elif type < 0: return

        # >> If this point is reached then changes to metadata/images were made.
        # >> Save categories and update container contents so user sees those changes inmediately.
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
        kodi_refresh_container()

    def _command_add_new_launcher(self, categoryID):
        # If categoryID not found return to plugin root window.
        if categoryID not in self.categories:
            kodi_notify_warn('Category ID not found.')
            return

        # Show "Create New Launcher" dialog
        dialog = xbmcgui.Dialog()
        type = dialog.select('Create New Launcher',
                             ['Files launcher (game emulator)', 'Standalone launcher (normal executable)'])
        log_info('_command_add_new_launcher() New launcher type = {0}'.format(type))
        filter = '.bat|.exe|.cmd|.lnk' if sys.platform == 'win32' else ''

        # 'Files launcher (game emulator)'
        if type == 0:
            app = xbmcgui.Dialog().browse(1, 'Select the launcher application', 'files', filter).decode('utf-8')
            if not app: return

            roms_path = xbmcgui.Dialog().browse(0, 'Select the ROMs path', 'files', '').decode('utf-8')
            if not roms_path: return

            extensions = emudata_get_program_extensions(os.path.basename(app))
            extkey = xbmc.Keyboard(extensions, 'Set files extensions, use "|" as separator. (e.g lnk|cbr)')
            extkey.doModal()
            if not extkey.isConfirmed(): return
            ext = extkey.getText().decode('utf-8')

            default_arguments = emudata_get_program_arguments(os.path.basename(app))
            argkeyboard = xbmc.Keyboard(default_arguments, 'Application arguments')
            argkeyboard.doModal()
            if not argkeyboard.isConfirmed(): return
            args = argkeyboard.getText().decode('utf-8')

            title = os.path.basename(app)
            keyboard = xbmc.Keyboard(title.replace('.' + title.split('.')[-1], '').replace('.', ' '), 'Set the title of the launcher')
            keyboard.doModal()
            if not keyboard.isConfirmed(): return
            title = keyboard.getText().decode('utf-8')
            if title == '':
                title = os.path.basename(app)
                title = title.replace('.' + title.split('.')[-1], '').replace('.', ' ')

            # --- Selection of the launcher plaform from official AEL names ---
            dialog = xbmcgui.Dialog()
            sel_platform = dialog.select('Select the platform', AEL_platform_list)
            if sel_platform < 0: return
            launcher_platform = AEL_platform_list[sel_platform]

            # --- Select assets path ---
            # A) User chooses one and only one assets path
            # B) If this path is different from the ROM path then asset naming scheme 1 is used.
            # B) If this path is the same as the ROM path then asset naming scheme 2 is used.
            assets_path = xbmcgui.Dialog().browse(0, 'Select assets (artwork) path', 'files', '', False, False, roms_path).decode('utf-8')
            if not assets_path: return

            # --- Create launcher object data, add to dictionary and write XML file ---
            # Choose launcher ROM XML filename. There may be launchers with same name in different categories, or 
            # even launcher with the same name in the same category.
            launcherID      = misc_generate_random_SID()
            category_name   = self.categories[categoryID]['m_name']
            roms_base_noext = fs_get_ROMs_basename(category_name, title, launcherID)

            # --- Create new launcher. categories.xml is save at the end of this function ---
            launcherdata = fs_new_launcher()
            launcherdata['id']                 = launcherID
            launcherdata['m_name']             = title
            launcherdata['platform']           = launcher_platform
            launcherdata['categoryID']         = categoryID
            launcherdata['application']        = app
            launcherdata['args']               = args
            launcherdata['rompath']            = roms_path
            launcherdata['romext']             = ext
            launcherdata['roms_base_noext']    = roms_base_noext
            launcherdata['timestamp_launcher'] = time.time()
            # >> Create asset directories. Function detects if we are using naming scheme 1 or 2.
            # >> launcher is edited using Python passing by assignment.
            assets_init_asset_dir(assets_path, launcherdata)
            self.launchers[launcherID] = launcherdata
            kodi_notify('ROM launcher {0} created.'.format(title))

        # 'Standalone launcher (normal executable)'
        elif type == 1:
            app = xbmcgui.Dialog().browse(1, 'Select the launcher application', "files", filter).decode('utf-8')
            if not app: return

            argument = ''
            argkeyboard = xbmc.Keyboard(argument, 'Application arguments')
            argkeyboard.doModal()
            args = argkeyboard.getText().decode('utf-8')

            title = os.path.basename(app)
            title_formatted = title.replace('.' + title.split('.')[-1], '').replace('.', ' ')
            keyboard = xbmc.Keyboard(title_formatted, 'Set the title of the launcher')
            keyboard.doModal()
            title = keyboard.getText().decode('utf-8')
            if not title:
                title = os.path.basename(app)
                title = title.replace('.' + title.split('.')[-1], '').replace('.', ' ')

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
            launcherdata['categoryID']         = categoryID
            launcherdata['application']        = app
            launcherdata['args']               = args
            launcherdata['timestamp_launcher'] = time.time()
            self.launchers[launcherID] = launcherdata
            kodi_notify('Standalone launcher {0} created.'.format(title))

        # >> If this point is reached then changes to metadata/images were made.
        # >> Save categories and update container contents so user sees those changes inmediately.
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
        kodi_refresh_container()

    def _command_edit_launcher(self, categoryID, launcherID):
        # --- Load scrapers ---
        self._load_metadata_scraper()
        self._load_asset_scraper()

        # --- Shows a select box with the options to edit ---
        dialog = xbmcgui.Dialog()
        finished_display = 'Status : Finished' if self.launchers[launcherID]['finished'] == True else 'Status : Unfinished'
        category_name = self.categories[self.launchers[launcherID]['categoryID']]['m_name']
        if self.launchers[launcherID]['rompath'] == '':
            type = dialog.select('Select action for launcher {0}'.format(self.launchers[launcherID]['m_name']),
                                 ['Edit Metadata...', 'Edit Assets/Artwork...', 'Choose default Assets/Artwork...',
                                  'Change Category: {0}'.format(category_name), finished_display, 
                                  'Advanced Modifications...', 'Delete Launcher'])
        else:
            type = dialog.select('Select action for launcher {0}'.format(self.launchers[launcherID]['m_name']),
                                 ['Edit Metadata...', 'Edit Assets/Artwork...', 'Choose default Assets/Artwork...',
                                  'Change Category: {0}'.format(category_name), finished_display, 
                                  'Manage ROM List...', 'Manage ROM Asset directories...',
                                  'Advanced Modifications...', 'Delete Launcher'])

        # --- Edition of the launcher metadata ---
        type_nb = 0
        if type == type_nb:
            dialog = xbmcgui.Dialog()
            desc_str = text_limit_string(self.launchers[launcherID]['m_plot'], DESCRIPTION_MAXSIZE)
            type2 = dialog.select('Edit Launcher Metadata',
                                  ['Scrape from {0}...'.format(self.scraper_metadata.fancy_name),
                                   'Import metadata from NFO (automatic)',
                                   'Import metadata from NFO (browse NFO)...',
                                   "Edit Title: '{0}'".format(self.launchers[launcherID]['m_name']),
                                   "Edit Platform: {0}".format(self.launchers[launcherID]['platform']),
                                   "Edit Release Year: '{0}'".format(self.launchers[launcherID]['m_year']),
                                   "Edit Genre: '{0}'".format(self.launchers[launcherID]['m_genre']),
                                   "Edit Studio: '{0}'".format(self.launchers[launcherID]['m_studio']),
                                   "Edit Rating: '{0}'".format(self.launchers[launcherID]['m_rating']),
                                   "Edit Plot: '{0}'".format(desc_str),
                                   'Save metadata to NFO file'])
            # --- Scrape launcher metadata ---
            if type2 == 0:
                if not self._gui_scrap_launcher_metadata(launcherID): return

            # --- Import launcher metadata from NFO file (automatic) ---
            elif type2 == 1:
                # >> Get NFO file name for launcher
                NFO_file = fs_get_launcher_NFO_name(self.settings, self.launchers[launcherID])
                
                # >> Launcher is edited using Python passing by assigment
                # >> Returns True if changes were made
                if not fs_import_launcher_NFO(NFO_file, self.launchers, launcherID): return

            # --- Browse for NFO file ---
            elif type2 == 2:
                # >> Get launcher NFO file
                # No-Intro reading of files: use Unicode string for '.dat|.xml'. However, | belongs to ASCII...
                NFO_file = xbmcgui.Dialog().browse(1, 'Select description file (NFO)', 'files', '.nfo', False, False).decode('utf-8')
                if not os.path.isfile(NFO_file): return
                
                # >> Launcher is edited using Python passing by assigment
                # >> Returns True if changes were made
                if not fs_import_launcher_NFO(NFO_file, self.launchers, launcherID): return

            # --- Edition of the launcher name ---
            elif type2 == 3:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]['m_name'], 'Edit title')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                title = keyboard.getText().decode('utf-8')
                if title == '':
                    title = self.launchers[launcherID]['m_name']
                self.launchers[launcherID]['m_name'] = title.rstrip()

            # --- Selection of the launcher platform from AEL "official" list ---
            elif type2 == 4:
                dialog = xbmcgui.Dialog()
                sel_platform = dialog.select('Select the platform', AEL_platform_list)
                if sel_platform < 0: return
                self.launchers[launcherID]['platform'] = AEL_platform_list[sel_platform]

            # --- Edition of the launcher release date (year) ---
            elif type2 == 5:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]['m_year'], 'Edit release year')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                self.launchers[launcherID]['m_year'] = keyboard.getText().decode('utf-8')

            # --- Edition of the launcher genre ---
            elif type2 == 6:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]['m_genre'], 'Edit genre')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                self.launchers[launcherID]['m_genre'] = keyboard.getText().decode('utf-8')

            # --- Edition of the launcher studio ---
            elif type2 == 7:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]['m_studio'], 'Edit studio')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                self.launchers[launcherID]['m_studio'] = keyboard.getText().decode('utf-8')

            # --- Edition of the launcher rating ---
            elif type2 == 8:
                rating = dialog.select('Edit Launcher Rating',
                                      ['Not set',  'Rating 0', 'Rating 1', 'Rating 2', 'Rating 3', 'Rating 4',
                                       'Rating 5', 'Rating 6', 'Rating 7', 'Rating 8', 'Rating 9', 'Rating 10'])
                # >> Rating not set, empty string
                if rating == 0:
                    self.launchers[launcherID]['m_rating'] = ''
                elif rating >= 1 and rating <= 11:
                    self.launchers[launcherID]['m_rating'] = '{0}'.format(rating - 1)
                elif rating < 0:
                    kodi_dialog_OK("Launcher rating '{0}' not changed".format(self.launchers[launcherID]['m_rating']))
                    return

            # --- Edit launcher description (plot) ---
            elif type2 == 9:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]['m_plot'], 'Edit plot')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                self.launchers[launcherID]['m_plot'] = keyboard.getText().decode('utf-8')

            # --- Import of the launcher descripion (plot) ---
            # elif type2 == 8:
            #     text_file = xbmcgui.Dialog().browse(1, 'Select description file (TXT|DAT)', 'files', '.txt|.dat', False, False).decode('utf-8')
            #     if os.path.isfile(text_file) == True:
            #         file_data = self._gui_import_TXT_file(text_file)
            #         self.launchers[launcherID]['plot'] = file_data
            #     else:
            #         desc_str = text_limit_string(self.launchers[launcherID]['plot'], DESCRIPTION_MAXSIZE)
            #         kodi_dialog_OK("Launcher plot '{0}' not changed".format(desc_str))
            #         return

            # --- Export launcher metadata to NFO file ---
            elif type2 == 10:
                NFO_file = fs_get_launcher_NFO_name(self.settings, self.launchers[launcherID])
                fs_export_launcher_NFO(NFO_file, self.launchers[launcherID])
                # >> No need to save launchers
                return

            # >> User canceled select dialog
            elif type2 < 0:
                return

        # --- Edit Launcher Assets/Artwork ---
        type_nb = type_nb + 1
        if type == type_nb:
            launcher = self.launchers[launcherID]
            status_thumb_str   = 'HAVE' if launcher['s_thumb'] else 'MISSING'
            status_fanart_str  = 'HAVE' if launcher['s_fanart'] else 'MISSING'
            status_banner_str  = 'HAVE' if launcher['s_banner'] else 'MISSING'
            status_flyer_str   = 'HAVE' if launcher['s_flyer'] else 'MISSING'
            status_trailer_str = 'HAVE' if launcher['s_trailer'] else 'MISSING'
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Edit Launcher Assets/Artwork',
                                  ["Edit Thumbnail ({0})...".format(status_thumb_str),
                                   "Edit Fanart ({0})...".format(status_fanart_str),
                                   "Edit Banner ({0})...".format(status_banner_str),
                                   "Edit Flyer ({0})...".format(status_flyer_str),
                                   "Edit Trailer ({0})...".format(status_trailer_str)])

            # --- Edit Assets ---
            # >> _gui_edit_asset() returns True if image was changed
            # >> Launcher is changed using Python passign by assigment
            if type2 == 0:
                if not self._gui_edit_asset(KIND_LAUNCHER, ASSET_THUMB, launcher): return
            elif type2 == 1:
                if not self._gui_edit_asset(KIND_LAUNCHER, ASSET_FANART, launcher): return
            elif type2 == 2:
                if not self._gui_edit_asset(KIND_LAUNCHER, ASSET_BANNER, launcher): return
            elif type2 == 3:
                if not self._gui_edit_asset(KIND_LAUNCHER, ASSET_FLYER, launcher): return
            elif type2 == 4:
                if not self._gui_edit_asset(KIND_LAUNCHER, ASSET_TRAILER, launcher): return
            # >> User canceled select dialog
            elif type2 < 0: return

        # --- Choose default thumb/fanart ---
        type_nb = type_nb + 1
        if type == type_nb:
            launcher        = self.categories[categoryID]
            asset_thumb     = assets_get_asset_name_str(launcher['default_thumb'])
            asset_fanart    = assets_get_asset_name_str(launcher['default_fanart'])
            asset_banner    = assets_get_asset_name_str(launcher['default_banner'])
            asset_poster    = assets_get_asset_name_str(launcher['default_poster'])
            asset_clearlogo = assets_get_asset_name_str(launcher['default_clearlogo'])
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Edit Category Assets/Artwork',
                                  ['Choose asset for Thumb (currently {0})'.format(asset_thumb), 
                                   'Choose asset for Fanart (currently {0})'.format(asset_fanart),
                                   'Choose asset for Banner (currently {0})'.format(asset_banner),
                                   'Choose asset for Poster (currently {0})'.format(asset_poster),
                                   'Choose asset for Clearlogo (currently {0})'.format(asset_clearlogo)])

            if type2 == 0:
                dialog = xbmcgui.Dialog()
                type3 = dialog.select('Choose default Asset for Thumb', DEFAULT_CATEGORY_ASSET_LIST)
                if type3 < 0: return
                assets_choose_category_artwork(launcher, 'default_thumb', type3)

            elif type2 == 1:
                dialog = xbmcgui.Dialog()
                type3 = dialog.select('Choose default Asset for Fanart', DEFAULT_CATEGORY_ASSET_LIST)
                if type3 < 0: return
                assets_choose_category_artwork(launcher, 'default_fanart', type3)

            elif type2 == 2:
                dialog = xbmcgui.Dialog()
                type3 = dialog.select('Choose default Asset for Banner', DEFAULT_CATEGORY_ASSET_LIST)
                if type3 < 0: return
                assets_choose_category_artwork(launcher, 'default_banner', type3)

            elif type2 == 3:
                dialog = xbmcgui.Dialog()
                type3 = dialog.select('Choose default Asset for Poster', DEFAULT_CATEGORY_ASSET_LIST)
                if type3 < 0: return
                assets_choose_category_artwork(launcher, 'default_poster', type3)

            elif type2 == 4:
                dialog = xbmcgui.Dialog()
                type3 = dialog.select('Choose default Asset for Clearlogo', DEFAULT_CATEGORY_ASSET_LIST)
                if type3 < 0: return
                assets_choose_category_artwork(launcher, 'default_clearlogo', type3)

            # >> User canceled select dialog
            elif type2 < 0: return

        # --- Change launcher's Category ---
        type_nb = type_nb + 1
        if type == type_nb:
            # >> Category of the launcher we are editing now
            old_categoryID = self.launchers[launcherID]['categoryID']

            # If only one Category there is nothing to change
            if len(self.categories) == 1:
                kodi_dialog_OK('There is only one category. Nothing to change.')
                return
            dialog = xbmcgui.Dialog()
            categories_id = []
            categories_name = []
            for key in self.categories:
                categories_id.append(self.categories[key]['id'])
                categories_name.append(self.categories[key]['m_name'])
            selected_cat = dialog.select('Select the category', categories_name)
            if selected_cat < 0: return
            self.launchers[launcherID]['categoryID'] = categories_id[selected_cat]
            
            # >> If the former category is empty after editing (no launchers) then replace category window 
            # >> with addon root.
            num_launchers_old_cat = 0
            for laun_id, launcher in self.launchers.iteritems():
                if launcher['categoryID'] == old_categoryID: num_launchers_old_cat += 1
            log_debug('_command_edit_launcher() num_launchers_old_cat = {0}'.format(num_launchers_old_cat))
            if not num_launchers_old_cat:
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
                log_debug('_command_edit_launcher() Replacing launcher window with root')
                log_debug('_command_edit_launcher() base_url = "{0}"'.format(self.base_url))
                # For some reason this does not work... Kodi ignores ReplaceWindow() and does not
                # go to the addon root (display of categories).
                xbmc.executebuiltin('ReplaceWindow(Programs,{0})'.format(self.base_url))
                return

        # --- Launcher status (finished [bool]) ---
        type_nb = type_nb + 1
        if type == type_nb:
            finished = self.launchers[launcherID]['finished']
            finished = False if finished else True
            finished_display = 'Finished' if finished == True else 'Unfinished'
            self.launchers[launcherID]['finished'] = finished
            kodi_dialog_OK('Launcher "{0}" status is now {1}'.format(self.launchers[launcherID]['m_name'], finished_display))

        # --- Launcher's Manage ROMs menu option ---
        # ONLY for ROM launchers, not for standalone launchers
        if self.launchers[launcherID]['rompath'] != '':
            type_nb = type_nb + 1
            if type == type_nb:
                dialog = xbmcgui.Dialog()
                launcher = self.launchers[launcherID]
                has_NoIntro_DAT = True if launcher['nointro_xml_file'] else False
                if has_NoIntro_DAT:
                    nointro_xml_file = launcher['nointro_xml_file']
                    add_delete_NoIntro_str = 'Delete No-Intro DAT: {0}'.format(nointro_xml_file)
                else:
                    add_delete_NoIntro_str = 'Add No-Intro XML DAT...'
                type2 = dialog.select('Manage Items List',
                                      ['Rescan local assets/artwork',
                                       'Choose ROMs default Assets/Artwork...',
                                       add_delete_NoIntro_str, 
                                       'Audit ROMs using No-Intro XML PClone DAT',
                                       'Clear No-Intro audit status',
                                       'Remove missing/dead ROMs',                                       
                                       'Import ROMs metadata from NFO files',
                                       'Export ROMs metadata to NFO files',
                                       'Clear ROMs from launcher' ])

                # --- Rescan local assets/artwork ---
                if type2 == 0:
                    log_info('_command_edit_launcher() Rescanning local assets...')
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

                    # >> Traverse ROM list and check local asset/artwork
                    roms_base_noext = self.launchers[launcherID]['roms_base_noext']
                    roms = fs_load_ROMs(ROMS_DIR, roms_base_noext)
                    for rom_id in roms:
                        rom = roms[rom_id]
                        log_info('Checking ROM "{0}"'.format(rom['filename']))
                        for i, asset in enumerate(ROM_ASSET_LIST):
                            A = assets_get_info_scheme(asset)
                            if not enabled_asset_list[i]: continue
                            ROM = misc_split_path(rom['filename'])
                            asset_path_noext = os.path.join(launcher[A.path_key], ROM.base_noext)
                            local_asset = misc_look_for_file(asset_path_noext, A.exts)
                            if local_asset:
                                log_verb('Found   {0:<10} "{1}"'.format(A.name, local_asset))
                                rom[A.key] = local_asset
                            else:
                                log_verb('Missing {0:<10}'.format(A.name))

                    # ~~~ Save ROMs XML file ~~~
                    # >> Also save categories/launchers to update timestamp
                    self.launchers[launcherID]['timestamp_launcher'] = time.time()
                    fs_write_ROMs(ROMS_DIR, roms_base_noext, roms, self.launchers[launcherID])
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
                    return

                # --- Choose default ROMs assets ---
                elif type2 == 1:
                    launcher        = self.launchers[launcherID]
                    asset_thumb     = assets_get_asset_name_str(launcher['roms_default_thumb'])
                    asset_fanart    = assets_get_asset_name_str(launcher['roms_default_fanart'])
                    asset_banner    = assets_get_asset_name_str(launcher['roms_default_banner'])
                    asset_poster    = assets_get_asset_name_str(launcher['roms_default_poster'])
                    asset_clearlogo = assets_get_asset_name_str(launcher['roms_default_clearlogo'])
                    dialog = xbmcgui.Dialog()
                    type3 = dialog.select('Edit ROMs default Assets/Artwork',
                                          ['Choose asset for Thumb (currently {0})'.format(asset_thumb), 
                                           'Choose asset for Fanart (currently {0})'.format(asset_fanart),
                                           'Choose asset for Banner (currently {0})'.format(asset_banner),
                                           'Choose asset for Poster (currently {0})'.format(asset_poster),
                                           'Choose asset for Clearlogo (currently {0})'.format(asset_clearlogo)])

                    if type3 == 0:
                        type_s = xbmcgui.Dialog().select('Choose default Asset for Thumb', DEFAULT_ROM_ASSET_LIST)
                        if type_s < 0: return
                        assets_choose_category_ROM(launcher, 'roms_default_thumb', type_s)
                    elif type3 == 1:
                        type_s = xbmcgui.Dialog().select('Choose default Asset for Fanart', DEFAULT_ROM_ASSET_LIST)
                        if type_s < 0: return
                        assets_choose_category_ROM(launcher, 'roms_default_fanart', type_s)
                    elif type3 == 2:
                        type_s = xbmcgui.Dialog().select('Choose default Asset for Banner', DEFAULT_ROM_ASSET_LIST)
                        if type_s < 0: return
                        assets_choose_category_ROM(launcher, 'roms_default_banner', type_s)
                    elif type3 == 3:
                        type_s = xbmcgui.Dialog().select('Choose default Asset for Poster', DEFAULT_ROM_ASSET_LIST)
                        if type_s < 0: return
                        assets_choose_category_ROM(launcher, 'roms_default_poster', type_s)
                    elif type3 == 4:
                        type_s = xbmcgui.Dialog().select('Choose default Asset for Clearlogo', DEFAULT_ROM_ASSET_LIST)
                        if type_s < 0: return
                        assets_choose_category_ROM(launcher, 'roms_default_clearlogo', type_s)
                    # >> User canceled select dialog
                    elif type3 < 0: return

                # --- Add/Delete No-Intro XML parent-clone DAT ---
                elif type2 == 2:
                    if has_NoIntro_DAT:
                        dialog = xbmcgui.Dialog()
                        ret = dialog.yesno('Advanced Emulator Launcher', 'Delete No-Intro DAT file?')
                        if not ret: return
                        self.launchers[launcherID]['nointro_xml_file'] = ''
                        kodi_dialog_OK('Rescan your ROMs to remove No-Intro tags.')
                    else:
                        # Browse for No-Intro file
                        # BUG For some reason *.dat files are not shown on the dialog, but XML files are OK!!!
                        dialog = xbmcgui.Dialog()
                        dat_file = dialog.browse(type = 1, heading = 'Select No-Intro XML DAT (XML|DAT)', 
                                                 s_shares = 'files', mask = '.xml|.dat', 
                                                 useThumbs = False, treatAsFolder = False).decode('utf-8')
                        if not os.path.isfile(dat_file): return
                        self.launchers[launcherID]['nointro_xml_file'] = dat_file
                        kodi_dialog_OK('DAT file successfully added. Audit your ROMs to update No-Intro status.')

                # --- Audit ROMs with No-Intro DAT ---
                # >> This code is similar to the one in the ROM scanner _roms_import_roms()
                elif type2 == 3:
                    # Check if No-Intro XML DAT exists
                    if not has_NoIntro_DAT:
                        kodi_dialog_OK('No-Intro XML DAT not configured. Add one before ROM audit.')
                        return

                    # --- Load ROMs for this launcher ---
                    roms_base_noext = self.launchers[launcherID]['roms_base_noext']
                    roms = fs_load_ROMs(ROMS_DIR, roms_base_noext)

                    # --- Load No-Intro DAT and audit ROMs ---
                    log_info('Auditing ROMs using No-Intro DAT {0}'.format(nointro_xml_file))

                    # --- Update No-Intro status for ROMs ---
                    # Note that roms dictionary is updated using Python pass by assigment.
                    # See http://stackoverflow.com/questions/986006/how-do-i-pass-a-variable-by-reference
                    (num_have, num_miss, num_unknown) = self._roms_update_NoIntro_status(roms, nointro_xml_file)

                    # --- Report ---
                    log_info('***** No-Intro audit finished. Report ******')
                    log_info('No-Intro Have ROMs    {0:6d}'.format(num_have))
                    log_info('No-Intro Miss ROMs    {0:6d}'.format(num_miss))
                    log_info('No-Intro Unknown ROMs {0:6d}'.format(num_unknown))
                    kodi_notify('Audit finished. Have {0}/Miss {1}/Unknown {2}'.format(num_have, num_miss, num_unknown))

                    # ~~~ Save ROMs XML file ~~~
                    # >> Also save categories/launchers to update timestamp
                    self.launchers[launcherID]['timestamp_launcher'] = time.time()
                    fs_write_ROMs(ROMS_DIR, roms_base_noext, roms, self.launchers[launcherID])
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
                    return

                # --- Reset audit status ---
                elif type2 == 4:
                    # --- Load ROMs for this launcher ---
                    roms_base_noext = self.launchers[launcherID]['roms_base_noext']
                    roms = fs_load_ROMs(ROMS_DIR, roms_base_noext)
                    
                    self._roms_reset_NoIntro_status(roms)
                    kodi_notify('No-Intro status reset')

                    # ~~~ Save ROMs XML file ~~~
                    # >> Also save categories/launchers to update timestamp
                    self.launchers[launcherID]['timestamp_launcher'] = time.time()
                    fs_write_ROMs(ROMS_DIR, roms_base_noext, roms, self.launchers[launcherID])
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
                    return

                # --- Remove dead ROMs ---
                elif type2 == 5:
                    ret = kodi_dialog_yesno('Are you sure you want to remove missing/dead ROMs?')
                    if not ret: return
                    
                    # --- Load ROMs for this launcher ---
                    roms_base_noext = self.launchers[launcherID]['roms_base_noext']
                    roms = fs_load_ROMs(ROMS_DIR, roms_base_noext)
                    
                    # --- Remove dead ROMs ---
                    num_removed_roms = self._roms_delete_missing_ROMs(roms)
                    kodi_notify('Reset No-Intro status. Removed {0} missing ROMs'.format(num_removed_roms))

                    # ~~~ Save ROMs XML file ~~~
                    # >> Also save categories/launchers to update timestamp
                    self.launchers[launcherID]['timestamp_launcher'] = time.time()
                    fs_write_ROMs(ROMS_DIR, roms_base_noext, roms, self.launchers[launcherID])
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
                    return

                # --- Import Items list form NFO files ---
                elif type2 == 6:
                    # >> Load ROMs, iterate and import NFO files
                    roms_base_noext = self.launchers[launcherID]['roms_base_noext']
                    roms = fs_load_ROMs(ROMS_DIR, roms_base_noext)
                    # >> Iterating dictionaries gives the key.
                    for rom_id in roms:
                        fs_import_ROM_NFO(roms, rom_id, verbose = False)
                    # >> Save ROMs XML file
                    # >> Also save categories/launchers to update timestamp
                    self.launchers[launcherID]['timestamp_launcher'] = time.time()
                    fs_write_ROMs(ROMS_DIR, roms_base_noext, roms, self.launchers[launcherID])
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
                    return

                # --- Export Items list to NFO files ---
                elif type2 == 7:
                    # >> Load ROMs for current launcher, iterate and write NFO files
                    roms = fs_load_ROMs(ROMS_DIR, self.launchers[launcherID]['roms_base_noext'])
                    if not roms: return
                    kodi_busydialog_ON()
                    for rom_id in roms:
                        fs_export_ROM_NFO(roms[rom_id], verbose = False)
                    kodi_busydialog_OFF()
                    # >> No need to save launchers XML / Update container
                    return

                # --- Empty Launcher menu option ---
                elif type2 == 8:
                    self._gui_empty_launcher(launcherID)
                    # _gui_empty_launcher calls ReplaceWindow/Container.Refresh. Return now to avoid the
                    # Container.Refresh at the end of this function and calling the plugin twice.
                    return
                    
                # >> User canceled select dialog
                elif type2 < 0: return

        # --- Manage ROM Asset directories ---
        # ONLY for ROM launchers, not for standalone launchers
        if self.launchers[launcherID]['rompath'] != '':
            type_nb = type_nb + 1
            if type == type_nb:
                launcher = self.launchers[launcherID]
                dialog = xbmcgui.Dialog()
                type2 = dialog.select('ROM Asset directories ',
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

                if type2 == 0:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Titles path', 'files', '', False, False, launcher['path_title']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_title'] = dir_path
                elif type2 == 1:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Snaps path', 'files', '', False, False, launcher['path_snap']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_snap'] = dir_path
                elif type2 == 2:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Fanarts path', 'files', '', False, False, launcher['path_fanart']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_fanart'] = dir_path
                elif type2 == 3:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Banners path', 'files', '', False, False, launcher['path_banner']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_banner'] = dir_path
                elif type2 == 4:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Clearlogos path', 'files', '', False, False, launcher['path_clearlogo']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_clearlogo'] = dir_path
                elif type2 == 5:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Boxfronts path', 'files', '', False, False, launcher['path_boxfront']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_boxfront'] = dir_path
                elif type2 == 6:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Boxbacks path', 'files', '', False, False, launcher['path_boxback']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_boxback'] = dir_path
                elif type2 == 7:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Cartridges path', 'files', '', False, False, launcher['path_cartridge']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_cartridge'] = dir_path
                elif type2 == 8:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Flyers path', 'files', '', False, False, launcher['path_flyer']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_flyer'] = dir_path
                elif type2 == 9:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Maps path', 'files', '', False, False, launcher['path_map']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_map'] = dir_path
                elif type2 == 10:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Manuals path', 'files', '', False, False, launcher['path_manual']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_manual'] = dir_path
                elif type2 == 11:
                    dialog = xbmcgui.Dialog()
                    dir_path = dialog.browse(0, 'Select Trailers path', 'files', '', False, False, launcher['path_trailer']).decode('utf-8')
                    if not dir_path: return
                    self.launchers[launcherID]['path_trailer'] = dir_path
                # >> User canceled select dialog
                elif type2 < 0: return

                # >> Check for duplicate paths and warn user.
                duplicated_name_list = asset_get_duplicated_dir_list(self.launchers[launcherID])
                if duplicated_name_list:
                    duplicated_asset_srt = ', '.join(duplicated_name_list)
                    kodi_dialog_OK('Duplicated asset directories: {0}. '.format(duplicated_asset_srt) +
                                   'AEL will refuse to add/edit ROMs if there are duplicate asset directories.')

        # --- Launcher Advanced Modifications menu option ---
        type_nb = type_nb + 1
        if type == type_nb:
            minimize_str = 'ON' if self.launchers[launcherID]['minimize'] == True else 'OFF'
            filter_str   = '.bat|.exe|.cmd' if sys.platform == 'win32' else ''

            # --- ROMS launcher -------------------------------------------------------------------
            if self.launchers[launcherID]['rompath'] == '':
                type2 = dialog.select('Advanced Launcher Modification',
                                      ["Change Application: '{0}'".format(self.launchers[launcherID]['application']),
                                       "Modify Arguments: '{0}'".format(self.launchers[launcherID]['args']),
                                       "Toggle Kodi into Windowed mode: {0}".format(minimize_str) ])
            # --- Standalone launcher -------------------------------------------------------------
            else:
                type2 = dialog.select('Advanced Launcher Modification',
                                      ["Change Application: '{0}'".format(self.launchers[launcherID]['application']),
                                       "Modify Arguments: '{0}'".format(self.launchers[launcherID]['args']),
                                       "Change ROMs Path: '{0}'".format(self.launchers[launcherID]['rompath']),
                                       "Modify ROM Extensions: '{0}'".format(self.launchers[launcherID]['romext']),
                                       "Toggle Kodi into Windowed mode: {0}".format(minimize_str) ])

            # Launcher application path menu option
            type2_nb = 0
            if type2 == type2_nb:
                app = xbmcgui.Dialog().browse(1, 'Select the launcher application',
                                              'files', '', False, False, self.launchers[launcherID]['application'])
                self.launchers[launcherID]['application'] = app

            # Edition of the launcher arguments
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]['args'], 'Edit application arguments')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                self.launchers[launcherID]['args'] = keyboard.getText().decode('utf-8')

            if self.launchers[launcherID]['rompath'] != '':
                # Launcher roms path menu option
                type2_nb = type2_nb + 1
                if type2 == type2_nb:
                    rom_path = xbmcgui.Dialog().browse(0, 'Select Files path', 'files', '',
                                                       False, False, self.launchers[launcherID]['rompath']).decode('utf-8')
                    self.launchers[launcherID]['rompath'] = rom_path

                # Edition of the launcher rom extensions (only for emulator launcher)
                type2_nb = type2_nb + 1
                if type2 == type2_nb:
                    keyboard = xbmc.Keyboard(self.launchers[launcherID]['romext'],
                                                'Edit ROM extensions, use &quot;|&quot; as separator. (e.g lnk|cbr)')
                    keyboard.doModal()
                    if not keyboard.isConfirmed(): return
                    self.launchers[launcherID]['romext'] = keyboard.getText().decode('utf-8')

            # Launcher minimize state menu option
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                dialog = xbmcgui.Dialog()
                type3 = dialog.select('Toggle Kodi Fullscreen', ['OFF (default)', 'ON'])
                # User canceled select dialog
                if type3 < 0: return
                self.launchers[launcherID]['minimize'] = True if type3 == 1 else False

        # --- Remove Launcher menu option ---
        type_nb = type_nb + 1
        if type == type_nb:
            self._gui_remove_launcher(launcherID)
            # _gui_remove_launcher calls ReplaceWindow/Container.Refresh. Return now to avoid the
            # Container.Refresh at the end of this function and calling the plugin twice.
            return

        # User pressed cancel or close dialog
        if type < 0:
            return

        # >> If this point is reached then changes to metadata/images were made.
        # >> Save categories and update container contents so user sees those changes inmediately.
        # >> Update edited launcher timestamp.
        self.launchers[launcherID]['timestamp_launcher'] = time.time()
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
        kodi_refresh_container()

    #
    # Removes ROMs for a given launcher. Note this function will never be called for standalone launchers.
    #
    def _gui_empty_launcher(self, launcherID):
        roms = fs_load_ROMs(ROMS_DIR, self.launchers[launcherID]['roms_base_noext'])
        num_roms = len(roms)

        # If launcher is empty (no ROMs) do nothing
        if num_roms == 0:
            kodi_dialog_OK('Launcher is empty. Nothing to do.')
            return

        # Confirm user wants to delete ROMs
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno('Advanced Emulator Launcher',
                           "Launcher '{0}' has {1} ROMs. Are you sure you want to delete them " \
                            'from AEL database?'.format(self.launchers[launcherID]['m_name'], num_roms))
        if ret:
            # Just remove ROMs file. Keep the value of roms_base_noext to be reused when user add more ROMs.
            roms_base_noext = self.launchers[launcherID]['roms_base_noext']
            if roms_base_noext == '':
                log_info('Launcher roms_base_noext is empty "". No ROMs XML to remove')
            else:
                roms_file_path = fs_get_ROMs_file_path(ROMS_DIR, roms_base_noext)
                log_info('Removing ROMs XML "{0}"'.format(roms_file_path))
                try:
                    os.remove(roms_file_path)
                except OSError:
                    log_error('_gui_empty_launcher() OSError exception deleting "{0}"'.format(roms_file_path))
                    kodi_notify_warn('OSError exception deleting ROMs database')
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            kodi_refresh_container()

    #
    # Removes a launcher. For ROMs launcher it also removes ROM XML. For standalone launcher there is no
    # files to remove and no ROMs to check.
    #
    def _gui_remove_launcher(self, launcherID):
        rompath = self.launchers[launcherID]['rompath']
        # >> Standalone launcher
        if rompath == '':
            ret = kodi_dialog_yesno('Launcher "{0}" is standalone. '.format(self.launchers[launcherID]['m_name']) +
                                    'Are you sure you want to delete it?')
        # >> ROMs launcher
        else:
            roms = fs_load_ROMs(ROMS_DIR, self.launchers[launcherID]['roms_base_noext'])
            num_roms = len(roms)
            ret = kodi_dialog_yesno('Launcher "{0}" has {1} ROMs '.format(self.launchers[launcherID]['m_name'], num_roms) +
                                    'Are you sure you want to delete it?')
        if not ret: return
    
        # --- Remove XML file and delete launcher object, only if launcher is not empty ---
        roms_base_noext = self.launchers[launcherID]['roms_base_noext']
        if roms_base_noext == '' or rompath == '':
            log_debug('Launcher is empty or standalone. No ROMs XML to remove')
        else:
            roms_file_path = fs_get_ROMs_file_path(ROMS_DIR, roms_base_noext)
            log_debug('Removing ROMs XML "{0}"'.format(roms_file_path))
            try:
                if os.path.isfile(roms_file_path): os.remove(roms_file_path)
            except OSError:
                log_error('_gui_remove_launcher() OSError exception deleting "{0}"'.format(roms_file_path))
                kodi_notify_warn('OSError exception deleting ROMs XML')

        categoryID = self.launchers[launcherID]['categoryID']
        self.launchers.pop(launcherID)
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
        kodi_refresh_container()

    #
    # Add ROMS to launcher
    #
    def _command_add_roms(self, launcher):
        dialog = xbmcgui.Dialog()
        type = dialog.select('Add/Update Items', ['Scan for New Items', 'Manually Add Item'])
        if type == 0:
            self._roms_import_roms(launcher)
        elif type == 1:
            self._roms_add_new_rom(launcher)

    #
    # Former _edit_rom()
    # Note that categoryID = VCATEGORY_FAVOURITES_ID, launcherID = VLAUNCHER_FAVOURITES_ID if we are editing 
    # a ROM in Favourites.
    #
    def _command_edit_rom(self, categoryID, launcherID, romID):
        # --- Load ROMs ---
        if categoryID == VCATEGORY_FAVOURITES_ID:
            roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            kodi_dialog_OK('Not coded yet. Sorry.')
            return
        else:
            roms_base_noext = self.launchers[launcherID]['roms_base_noext']
            roms = fs_load_ROMs(ROMS_DIR, roms_base_noext)

        # --- Load scrapers ---
        self._load_metadata_scraper()
        self._load_asset_scraper()

        # --- Show a dialog with ROM editing options ---
        rom_name = roms[romID]['m_name']
        finished_display = 'Status: Finished' if roms[romID]['finished'] == True else 'Status: Unfinished'
        dialog = xbmcgui.Dialog()
        if categoryID == VCATEGORY_FAVOURITES_ID or categoryID == VCATEGORY_COLLECTIONS_ID:
            type = dialog.select('Edit ROM {0}'.format(rom_name),
                                ['Edit Metadata...', 'Edit Assets/Artwork...',
                                 'Choose default Assets/Artwork...',
                                 finished_display, 'Advanced Modifications...'])
        else:
            type = dialog.select('Edit ROM {0}'.format(rom_name),
                                ['Edit Metadata...', 'Edit Assets/Artwork...',
                                 finished_display, 'Advanced Modifications...'])


        # --- Edit ROM metadata ---
        type_nb = 0
        if type == type_nb:
            dialog = xbmcgui.Dialog()
            desc_str = text_limit_string(roms[romID]['m_plot'], DESCRIPTION_MAXSIZE)
            type2 = dialog.select('Modify ROM metadata',
                                  ['Scrape from {0}...'.format(self.scraper_metadata.fancy_name),
                                   'Import metadata from NFO file',
                                   "Edit Title: '{0}'".format(roms[romID]['m_name']),
                                   "Edit Release Year: '{0}'".format(roms[romID]['m_year']),
                                   "Edit Genre: '{0}'".format(roms[romID]['m_genre']),
                                   "Edit Studio: '{0}'".format(roms[romID]['m_studio']),
                                   "Edit Rating: '{0}'".format(roms[romID]['m_rating']),
                                   "Edit Plot: '{0}'".format(desc_str),
                                   'Load Plot from TXT file ...',
                                   'Save metadata to NFO file'])
            # --- Scrap rom metadata ---
            if type2 == 0:
                # >> If this returns False there were no changes so no need to save ROMs XML.
                if not self._gui_scrap_rom_metadata(roms, romID, launcherID): return

            # --- Import ROM metadata from NFO file ---
            elif type2 == 1:
                if launcherID == VLAUNCHER_FAVOURITES_ID:
                    kodi_dialog_OK('Importing NFO file is not allowed for ROMs in Favourites.')
                    return
                if not fs_import_ROM_NFO(roms, romID): return

            # --- Edit of the rom title ---
            elif type2 == 2:
                keyboard = xbmc.Keyboard(roms[romID]['m_name'], 'Edit title')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                title = keyboard.getText().decode('utf-8')
                if title == '': title = roms[romID]['m_name']
                roms[romID]['m_name'] = title.rstrip()

            # --- Edition of the rom release year ---
            elif type2 == 3:
                keyboard = xbmc.Keyboard(roms[romID]['m_year'], 'Edit release year')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                roms[romID]['m_year'] = keyboard.getText().decode('utf-8')

            # --- Edition of the rom game genre ---
            elif type2 == 4:
                keyboard = xbmc.Keyboard(roms[romID]['m_genre'], 'Edit genre')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                roms[romID]['m_genre'] = keyboard.getText().decode('utf-8')

            # --- Edition of the rom studio ---
            elif type2 == 5:
                keyboard = xbmc.Keyboard(roms[romID]['m_studio'], 'Edit studio')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                roms[romID]['m_studio'] = keyboard.getText().decode('utf-8')

            # --- Edition of the ROM rating ---
            elif type2 == 6:
                rating = dialog.select('Edit ROM Rating',
                                      ['Not set',  'Rating 0', 'Rating 1', 'Rating 2', 'Rating 3', 'Rating 4',
                                       'Rating 5', 'Rating 6', 'Rating 7', 'Rating 8', 'Rating 9', 'Rating 10'])
                # >> Rating not set, empty string
                if rating == 0:
                    roms[romID]['m_rating'] = ''
                elif rating >= 1 and rating <= 11:
                    roms[romID]['m_rating'] = '{0}'.format(rating - 1)
                elif rating < 0:
                    kodi_dialog_OK("ROM rating '{0}' not changed".format(roms[romID]['m_rating']))
                    return

            # --- Edit ROM description (plot) ---
            elif type2 == 7:
                keyboard = xbmc.Keyboard(roms[romID]['m_plot'], 'Edit plot')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                roms[romID]['m_plot'] = keyboard.getText().decode('utf-8')

            # --- Import of the rom game plot from TXT file ---
            elif type2 == 8:
                dialog = xbmcgui.Dialog()
                text_file = dialog.browse(1, 'Select description file (TXT|DAT)', 
                                          'files', '.txt|.dat', False, False).decode('utf-8')
                if os.path.isfile(text_file):
                    file_data = self._gui_import_TXT_file(text_file)
                    roms[romID]['m_plot'] = file_data
                else:
                    desc_str = text_limit_string(roms[romID]['m_plot'], DESCRIPTION_MAXSIZE)
                    kodi_dialog_OK("Launcher plot '{0}' not changed".format(desc_str))
                    return

            # --- Export ROM metadata to NFO file ---
            elif type2 == 9:
                if launcherID == VLAUNCHER_FAVOURITES_ID:
                    kodi_dialog_OK('Exporting NFO file is not allowed for ROMs in Favourites.')
                    return
                fs_export_ROM_NFO(roms[romID])
                # >> No need to save ROMs
                return

            # >> User canceled select dialog
            elif type2 < 0:
                return

        # --- Edit Launcher Assets/Artwork ---
        type_nb = type_nb + 1
        if type == type_nb:
            rom = roms[romID]
            # >> Artwork status
            status_title_str     = '[COLOR green]HAVE[/COLOR]' if rom['s_title'] else 'MISSING'
            status_snap_str      = '[COLOR green]HAVE[/COLOR]' if rom['s_snap'] else 'MISSING'
            status_fanart_str    = '[COLOR green]HAVE[/COLOR]' if rom['s_fanart'] else 'MISSING'
            status_banner_str    = '[COLOR green]HAVE[/COLOR]' if rom['s_banner'] else 'MISSING'
            status_clearlogo_str = '[COLOR green]HAVE[/COLOR]' if rom['s_clearlogo'] else 'MISSING'
            status_boxfront_str  = '[COLOR green]HAVE[/COLOR]' if rom['s_boxfront'] else 'MISSING'
            status_boxback_str   = '[COLOR green]HAVE[/COLOR]' if rom['s_boxback'] else 'MISSING'
            status_cartridge_str = '[COLOR green]HAVE[/COLOR]' if rom['s_cartridge'] else 'MISSING'
            status_flyer_str     = '[COLOR green]HAVE[/COLOR]' if rom['s_flyer'] else 'MISSING'
            status_map_str       = '[COLOR green]HAVE[/COLOR]' if rom['s_map'] else 'MISSING'
            status_manual_str    = '[COLOR green]HAVE[/COLOR]' if rom['s_manual'] else 'MISSING'
            status_trailer_str   = '[COLOR green]HAVE[/COLOR]' if rom['s_trailer'] else 'MISSING'
            # >> Scraper artwork support status
            scraper_obj = self.scraper_asset
            scraper_title_str     = '[COLOR green]OK[/COLOR]' if scraper_obj.supports_asset(ASSET_TITLE) else 'NO'
            scraper_snap_str      = '[COLOR green]OK[/COLOR]' if scraper_obj.supports_asset(ASSET_SNAP) else 'NO'
            scraper_fanart_str    = '[COLOR green]OK[/COLOR]' if scraper_obj.supports_asset(ASSET_FANART) else 'NO'
            scraper_banner_str    = '[COLOR green]OK[/COLOR]' if scraper_obj.supports_asset(ASSET_BANNER) else 'NO'
            scraper_clearlogo_str = '[COLOR green]OK[/COLOR]' if scraper_obj.supports_asset(ASSET_CLEARLOGO) else 'NO'
            scraper_boxfront_str  = '[COLOR green]OK[/COLOR]' if scraper_obj.supports_asset(ASSET_BOXFRONT) else 'NO'
            scraper_boxback_str   = '[COLOR green]OK[/COLOR]' if scraper_obj.supports_asset(ASSET_BOXBACK) else 'NO'
            scraper_cartridge_str = '[COLOR green]OK[/COLOR]' if scraper_obj.supports_asset(ASSET_CARTRIDGE) else 'NO'
            scraper_flyer_str     = '[COLOR green]OK[/COLOR]' if scraper_obj.supports_asset(ASSET_FLYER) else 'NO'
            scraper_map_str       = '[COLOR green]OK[/COLOR]' if scraper_obj.supports_asset(ASSET_MAP) else 'NO'
            scraper_manual_str    = '[COLOR green]OK[/COLOR]' if scraper_obj.supports_asset(ASSET_MANUAL) else 'NO'
            scraper_trailer_str   = '[COLOR green]OK[/COLOR]' if scraper_obj.supports_asset(ASSET_TRAILER) else 'NO'
            # >> Make menu
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Edit Launcher Assets/Artwork',
                                  ["Edit Title <{0}> <Scraper {1}>...".format(status_title_str, scraper_title_str),
                                   "Edit Snap <{0}> <Scraper {1}>...".format(status_snap_str, scraper_snap_str),
                                   "Edit Fanart <{0}> <Scraper {1}>...".format(status_fanart_str, scraper_fanart_str),
                                   "Edit Banner <{0}> <Scraper {1}>...".format(status_banner_str, scraper_banner_str),
                                   "Edit Clearlogo <{0}> <Scraper {1}>...".format(status_clearlogo_str, scraper_clearlogo_str),
                                   "Edit Boxfront <{0}> <Scraper {1}>...".format(status_boxfront_str, scraper_boxfront_str),
                                   "Edit Boxback <{0}> <Scraper {1}>...".format(status_boxback_str, scraper_boxback_str),
                                   "Edit Cartridge <{0}> <Scraper {1}>...".format(status_cartridge_str, scraper_cartridge_str),
                                   "Edit Flyer <{0}> <Scraper {1}>...".format(status_flyer_str, scraper_flyer_str),
                                   "Edit Map <{0}> <Scraper {1}>...".format(status_map_str, scraper_map_str),
                                   "Edit Manual <{0}> <Scraper {1}>...".format(status_manual_str, scraper_manual_str),
                                   "Edit Trailer <{0}> <Scraper {1}>...".format(status_trailer_str, scraper_trailer_str)])
            # --- Edit Assets ---
            # >> _gui_edit_asset() returns True if image was changed
            # >> ROM is changed using Python passign by assigment
            if type2 == 0:
                if not self._gui_edit_asset(KIND_ROM, ASSET_TITLE, rom, categoryID, launcherID): return
            elif type2 == 1:
                if not self._gui_edit_asset(KIND_ROM, ASSET_SNAP, rom, categoryID, launcherID): return
            elif type2 == 2:
                if not self._gui_edit_asset(KIND_ROM, ASSET_FANART, rom, categoryID, launcherID): return
            elif type2 == 3:
                if not self._gui_edit_asset(KIND_ROM, ASSET_BANNER, rom, categoryID, launcherID): return
            elif type2 == 4:
                if not self._gui_edit_asset(KIND_ROM, ASSET_CLEARLOGO, rom, categoryID, launcherID): return
            elif type2 == 5:
                if not self._gui_edit_asset(KIND_ROM, ASSET_BOXFRONT, rom, categoryID, launcherID): return
            elif type2 == 6:
                if not self._gui_edit_asset(KIND_ROM, ASSET_BOXBACK, rom, categoryID, launcherID): return
            elif type2 == 7:
                if not self._gui_edit_asset(KIND_ROM, ASSET_CARTRIDGE, rom, categoryID, launcherID): return
            elif type2 == 8:
                if not self._gui_edit_asset(KIND_ROM, ASSET_FLYER, rom, categoryID, launcherID): return
            elif type2 == 9:
                if not self._gui_edit_asset(KIND_ROM, ASSET_MAP, rom, categoryID, launcherID): return
            elif type2 == 10:
                if not self._gui_edit_asset(KIND_ROM, ASSET_MANUAL, rom, categoryID, launcherID): return
            elif type2 == 11:
                if not self._gui_edit_asset(KIND_ROM, ASSET_TRAILER, rom, categoryID, launcherID): return
            # >> User canceled select dialog
            elif type2 < 0:
                return

        # --- Edit default assets ---
        # >> ONLY for Favourite/Collection ROMs
        if categoryID == VCATEGORY_FAVOURITES_ID or categoryID == VCATEGORY_COLLECTIONS_ID:
            type_nb = type_nb + 1
            if type == type_nb:
                rom = roms[romID]
                asset_thumb     = assets_get_asset_name_str(rom['roms_default_thumb'])
                asset_fanart    = assets_get_asset_name_str(rom['roms_default_fanart'])
                asset_banner    = assets_get_asset_name_str(rom['roms_default_banner'])
                asset_poster    = assets_get_asset_name_str(rom['roms_default_poster'])
                asset_clearlogo = assets_get_asset_name_str(rom['roms_default_clearlogo'])
                dialog = xbmcgui.Dialog()
                type3 = dialog.select('Edit ROMs default Assets/Artwork',
                                      ['Choose asset for Thumb (currently {0})'.format(asset_thumb), 
                                       'Choose asset for Fanart (currently {0})'.format(asset_fanart),
                                       'Choose asset for Banner (currently {0})'.format(asset_banner),
                                       'Choose asset for Poster (currently {0})'.format(asset_poster),
                                       'Choose asset for Clearlogo (currently {0})'.format(asset_clearlogo)])

                if type3 == 0:
                    type_s = xbmcgui.Dialog().select('Choose default Asset for Thumb', DEFAULT_ROM_ASSET_LIST)
                    if type_s < 0: return
                    assets_choose_category_ROM(rom, 'roms_default_thumb', type_s)
                elif type3 == 1:
                    type_s = xbmcgui.Dialog().select('Choose default Asset for Fanart', DEFAULT_ROM_ASSET_LIST)
                    if type_s < 0: return
                    assets_choose_category_ROM(rom, 'roms_default_fanart', type_s)
                elif type3 == 2:
                    type_s = xbmcgui.Dialog().select('Choose default Asset for Banner', DEFAULT_ROM_ASSET_LIST)
                    if type_s < 0: return
                    assets_choose_category_ROM(rom, 'roms_default_banner', type_s)
                elif type3 == 3:
                    type_s = xbmcgui.Dialog().select('Choose default Asset for Poster', DEFAULT_ROM_ASSET_LIST)
                    if type_s < 0: return
                    assets_choose_category_ROM(rom, 'roms_default_poster', type_s)
                elif type3 == 4:
                    type_s = xbmcgui.Dialog().select('Choose default Asset for Clearlogo', DEFAULT_ROM_ASSET_LIST)
                    if type_s < 0: return
                    assets_choose_category_ROM(rom, 'roms_default_clearlogo', type_s)
                # >> User canceled select dialog
                elif type3 < 0: return

        # --- Edit status ---
        type_nb = type_nb + 1
        if type == type_nb:
            finished = roms[romID]['finished']
            finished = False if finished else True
            finished_display = 'Finished' if finished == True else 'Unfinished'
            roms[romID]['finished'] = finished
            kodi_dialog_OK("ROM '{0}' status is now {1}".format(roms[romID]['m_name'], finished_display))

        # --- Advanced Modifications ---
        type_nb = type_nb + 1
        if type == type_nb:
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Advanced ROM Modifications',
                                  ["Change ROM file: '{0}'".format(roms[romID]['filename']),
                                   "Alternative application: '{0}'".format(roms[romID]['altapp']),
                                   "Alternative arguments: '{0}'".format(roms[romID]['altarg']) ])
            # >> Selection of the item file
            if type2 == 0:
                filename = roms[romID]['filename']
                launcher = self.launchers[launcherID]
                romext   = launcher['romext']
                item_file = xbmcgui.Dialog().browse(1, 'Select the file', 'files', '.' + romext.replace('|', '|.'),
                                                    False, False, filename).decode('utf-8')
                if not item_file: return
                roms[romID]['filename'] = item_file
            # >> Alternative launcher application file path
            elif type2 == 1:
                filter_str = '.bat|.exe|.cmd' if sys.platform == 'win32' else ''
                altapp = xbmcgui.Dialog().browse(1, 'Select ROM custom launcher application',
                                                 'files', filter_str, 
                                                 False, False, roms[romID]['altapp']).decode('utf-8')
                # Returns empty browse if dialog was canceled.
                if not altapp: return
                roms[romID]['altapp'] = altapp
            # >> Alternative launcher arguments
            elif type2 == 2:
                keyboard = xbmc.Keyboard(roms[romID]['altarg'], 'Edit ROM custom application arguments')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                roms[romID]['altarg'] = keyboard.getText().decode('utf-8')
            # >> User canceled select dialog
            elif type2 < 0:
                return

        # --- User canceled select dialog ---
        if type < 0: return

        # --- Save ROMs or Favourites ROMs ---
        # Always save if we reach this point of the function
        if launcherID == VLAUNCHER_FAVOURITES_ID:
            fs_write_Favourites_JSON(FAV_JSON_FILE_PATH, roms)
        else:
            # >> Also save categories/launchers to update timestamp
            # >> Also update changed launcher timestamp
            self.launchers[launcherID]['timestamp_launcher'] = _t = time.time()
            roms_base_noext = self.launchers[launcherID]['roms_base_noext']
            fs_write_ROMs(ROMS_DIR, roms_base_noext, roms, self.launchers[launcherID])
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

        # It seems that updating the container does more harm than good... specially when having many ROMs
        # By the way, what is the difference between Container.Refresh() and Container.Update()?
        kodi_refresh_container()

    #
    # Deletes a ROM from a launcher/Favourites/ROM Collection
    #
    def _command_remove_rom(self, categoryID, launcherID, romID):
        if categoryID == VCATEGORY_FAVOURITES_ID and launcherID == VLAUNCHER_FAVOURITES_ID:
            log_info('_command_remove_rom() Deleting ROM from Favourites (id {0})'.format(romID))
            # --- Load Favourite ROMs ---
            roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
            if not roms: return

            # --- Confirm deletion ---
            ret = kodi_dialog_yesno('ROM {0}. '.format(roms[romID]['m_name']) +
                                    'Are you sure you want to delete it from favourites?')
            if not ret: return

            # --- Delete ROM ---
            roms.pop(romID)
            fs_write_Favourites_JSON(FAV_JSON_FILE_PATH, roms)
            kodi_notify('Deleted ROM from Favourites')
            # >> If Favourites is empty then go to addon root, if not refresh
            kodi_refresh_container()
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            log_info('_command_remove_rom() Deleting ROM from Collection (id {0})'.format(romID))
            # --- Load Collection index and roms ---
            (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
            collection = collections[launcherID]
            collection_rom_list = fs_load_Collection_ROMs_JSON(COLLECTIONS_DIR, collection['roms_base_noext'])
            if not collection_rom_list: return

            # >> Find index of ROM to be deleted
            rom_index = -1
            for idx, rom in enumerate(collection_rom_list): 
                if rom['id'] == romID: 
                    rom_index = idx
                    break
            if rom_index < 0: return # ERROR, ROM not found in list

            ret = kodi_dialog_yesno('Collection {0}, '.format(collection['name']) +
                                    'ROM {0}. '.format(collection_rom_list[rom_index]['m_name']) +
                                    'Are you sure you want to delete it from favourites?')
            if not ret: return

            del collection_rom_list[rom_index]
            fs_write_Collection_ROMs_JSON(COLLECTIONS_DIR, collection['roms_base_noext'], collection_rom_list)
            kodi_notify('Deleted ROM from Collection')
            kodi_refresh_container()
        else:
            log_info('_command_remove_rom() Deleting ROM from Launcher (id {0})'.format(romID))
            roms = fs_load_ROMs(ROMS_DIR, self.launchers[launcherID]['roms_base_noext'])
            if not roms: return

            ret = kodi_dialog_yesno('Launcher {0}, '.format(self.launchers[launcherID]['m_name']) +
                                    'ROM {0}. '.format(roms[romID]['m_name']) +
                                    'Are you sure you want to delete it from favourites?')
            if not ret: return

            roms.pop(romID)
            launcher = self.launchers[launcherID]
            roms_base_noext = launcher['roms_base_noext']
            fs_write_ROMs(ROMS_DIR, roms_base_noext, roms, launcher)
            # >> Also save categories/launchers to update main timestamp and launcher timestamp
            self.launchers[launcherID]['timestamp_launcher'] = time.time()
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            kodi_notify('Deleted ROM from launcher')
            kodi_refresh_container()

    #
    # Former _get_categories()
    # Renders the categories (addon root window)
    #
    def _command_render_categories(self):
        # >> Set content type
        self._misc_set_content_and_all_sorting_methods()

        # --- For every category, add it to the listbox. Order alphabetically by name ---
        for key in sorted(self.categories, key= lambda x : self.categories[x]['m_name']):
            self._gui_render_category_row(self.categories[key], key)

        # --- AEL Favourites special category ---
        self._gui_render_category_favourites_row()

        # --- AEL Collections special category ---
        self._gui_render_category_collections_row()

        # --- AEL Virtual Categories ---
        if not self.settings['display_hide_title']:  self._gui_render_virtual_category_row(VCATEGORY_TITLE_ID)
        if not self.settings['display_hide_year']:   self._gui_render_virtual_category_row(VCATEGORY_YEARS_ID)
        if not self.settings['display_hide_genre']:  self._gui_render_virtual_category_row(VCATEGORY_GENRE_ID)
        if not self.settings['display_hide_studio']: self._gui_render_virtual_category_row(VCATEGORY_STUDIO_ID)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Renders all categories withouth Favourites, VLaunchers, etc.
    # This function is called by skins.
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
        if category_dic['finished'] and self.settings['display_hide_finished']:
            return

        # --- Create listitem row ---
        ICON_OVERLAY = 5 if category_dic['finished'] else 4
        listitem = xbmcgui.ListItem(category_dic['m_name'])
        listitem.setInfo('video', {'title'   : category_dic['m_name'],    'genre'   : category_dic['m_genre'],
                                   'plot'    : category_dic['m_plot'],    'rating'  : category_dic['m_rating'],
                                   'trailer' : category_dic['s_trailer'], 'overlay' : ICON_OVERLAY } )

        # --- Set Category artwork ---
        # >> Set thumb/fanart/banner/poster/clearlogo based on user preferences
        thumb_path      = asset_get_default_asset_Category(category_dic, 'default_thumb', 'DefaultFolder.png')
        thumb_fanart    = asset_get_default_asset_Category(category_dic, 'default_fanart')
        thumb_banner    = asset_get_default_asset_Category(category_dic, 'default_banner')
        thumb_poster    = asset_get_default_asset_Category(category_dic, 'default_poster')
        thumb_clearlogo = asset_get_default_asset_Category(category_dic, 'default_clearlogo')
        listitem.setArt({'thumb' : thumb_path, 'fanart' : thumb_fanart, 'banner' : thumb_banner, 
                         'poster' : thumb_poster, 'clearlogo' : thumb_clearlogo })

        # --- Create context menu ---
        # To remove default entries like "Go to root", etc, see http://forum.kodi.tv/showthread.php?tid=227358
        commands = []
        categoryID = category_dic['id']
        commands.append(('View Category data',  self._misc_url_RunPlugin('VIEW_CATEGORY', categoryID), ))
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY'), ))
        commands.append(('Edit Category',       self._misc_url_RunPlugin('EDIT_CATEGORY', categoryID), ))
        commands.append(('Add New Launcher',    self._misc_url_RunPlugin('ADD_LAUNCHER', categoryID), ))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', )) # If using window ID then use "10003"
        commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        # Add Category to Kodi Favourites (do not know how to do it yet)
        # In Krypton "Add to favourites" appears always in the last position of context menu.
        listitem.addContextMenuItems(commands, replaceItems = True)

        # --- Add row ---
        url_str = self._misc_url('SHOW_LAUNCHERS', key)
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url=url_str, listitem=listitem, isFolder=True)

    def _gui_render_category_favourites_row(self):
        # --- Create listitem row ---
        fav_name = '<Favourites>'
        fav_thumb = 'DefaultFolder.png'
        fav_fanart = ''
        fav_banner = ''
        fav_flyer = ''
        listitem = xbmcgui.ListItem(fav_name)
        listitem.setInfo('video', {'title': fav_name,             'genre' : 'AEL Favourites',
                                   'plot' : 'AEL Favourite ROMs', 'overlay' : 4 } )
        listitem.setArt({'thumb' : fav_thumb, 'fanart' : fav_fanart, 'banner' : fav_banner, 'poster' : fav_flyer})

        # --- Create context menu ---
        commands = []
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY'), ))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', ))
        commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        listitem.addContextMenuItems(commands, replaceItems = True)

        # --- Add row ---
        url_str = self._misc_url('SHOW_FAVOURITES')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    def _gui_render_category_collections_row(self):
        collections_name   = '{ROM Collections}'
        collections_thumb  = ''
        collections_fanart = ''
        collections_banner = ''
        collections_flyer  = ''
        collections_label  = 'Title'
        listitem = xbmcgui.ListItem(collections_name)
        listitem.setInfo('video', {'title': collections_name,         'genre' : 'AEL Collections',
                                   'plot' : 'AEL virtual category', 'overlay': 4 } )
        listitem.setArt({'thumb' : collections_thumb, 'fanart' : collections_fanart, 'banner' : collections_banner, 'poster' : collections_flyer})

        commands = []
        commands.append(('Create New Collection', self._misc_url_RunPlugin('ADD_COLLECTION'), ))
        commands.append(('Create New Category',   self._misc_url_RunPlugin('ADD_CATEGORY'), ))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', ))
        commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        listitem.addContextMenuItems(commands, replaceItems = True)

        url_str = self._misc_url('SHOW_COLLECTIONS')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    def _gui_render_virtual_category_row(self, virtual_category_kind):
        if virtual_category_kind == VCATEGORY_TITLE_ID:
            vcategory_name   = '[Browse by Title]'
            vcategory_thumb  = ''
            vcategory_fanart = ''
            vcategory_banner = ''
            vcategory_flyer  = ''
            vcategory_label  = 'Title'
        elif virtual_category_kind == VCATEGORY_YEARS_ID:
            vcategory_name   = '[Browse by Year]'
            vcategory_thumb  = ''
            vcategory_fanart = ''
            vcategory_banner = ''
            vcategory_flyer  = ''
            vcategory_label  = 'Years'
        elif virtual_category_kind == VCATEGORY_GENRE_ID:
            vcategory_name   = '[Browse by Genre]'
            vcategory_thumb  = ''
            vcategory_fanart = ''
            vcategory_banner = ''
            vcategory_flyer  = ''
            vcategory_label  = 'Genre'
        elif virtual_category_kind == VCATEGORY_STUDIO_ID:
            vcategory_name   = '[Browse by Studio]'
            vcategory_thumb  = ''
            vcategory_fanart = ''
            vcategory_banner = ''
            vcategory_flyer  = ''
            vcategory_label  = 'Studio'
        else:
            log_error('_gui_render_virtual_category_row() Wrong virtual_category_kind = {0}'.format(virtual_category_kind))
            kodi_dialog_OK('Wrong virtual_category_kind = {0}'.format(virtual_category_kind))
            return
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name,         'genre' : 'AEL Virtual Launcher',
                                   'plot' : 'AEL virtual category', 'overlay': 4 } )
        listitem.setArt({'thumb' : vcategory_thumb, 'fanart' : vcategory_fanart, 'banner' : vcategory_banner, 'poster' : vcategory_flyer})

        commands = []
        update_vcat_URL     = self._misc_url_RunPlugin('UPDATE_VIRTUAL_CATEGORY', virtual_category_kind)
        update_vcat_all_URL = self._misc_url_RunPlugin('UPDATE_ALL_VCATEGORIES')
        commands.append(('Update {0} database'.format(vcategory_label), update_vcat_URL, ))
        commands.append(('Update all databases'.format(vcategory_label), update_vcat_all_URL, ))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', ))
        commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        listitem.addContextMenuItems(commands, replaceItems = True)

        url_str = self._misc_url('SHOW_VIRTUAL_CATEGORY', virtual_category_kind)
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    #
    # Former  _get_launchers
    # Renders the launcher for a given category
    #
    def _command_render_launchers(self, categoryID):
        # >> Set content type
        self._misc_set_content_and_all_sorting_methods()
    
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
    # Renders all launchers belonging to all categories. This function is called by skins
    #
    def _command_render_all_launchers(self):
        # >> If no launchers render nothing
        if not self.launchers:
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # >> Render all launchers (sort by application? Is not better to sort by name alphabetically?)
        for key in sorted(self.launchers, key = lambda x : self.launchers[x]['application']):
            self._gui_render_launcher_row(self.launchers[key])
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    def _gui_render_launcher_row(self, launcher_dic):
        # --- Do not render row if launcher finished ---
        if launcher_dic['finished'] and self.settings['display_hide_finished']:
            return

        # --- Create listitem row ---
        ICON_OVERLAY = 5 if launcher_dic['finished'] else 4
        listitem = xbmcgui.ListItem(launcher_dic['m_name'])
        listitem.setInfo('video', {'title'   : launcher_dic['m_name'],    'year'    : launcher_dic['m_year'], 
                                   'genre'   : launcher_dic['m_genre'],   'plot'    : launcher_dic['m_plot'],
                                   'studio'  : launcher_dic['m_studio'],  'rating'  : launcher_dic['m_rating'],
                                   'trailer' : launcher_dic['s_trailer'], 'Overlay' : ICON_OVERLAY })
        listitem.setProperty('platform', launcher_dic['platform'])

        # --- Set ListItem artwork ---
        kodi_thumb  = 'DefaultFolder.png' if launcher_dic['rompath'] else 'DefaultProgram.png'
        thumb_path      = asset_get_default_asset_Category(launcher_dic, 'default_thumb', 'DefaultFolder.png')
        thumb_fanart    = asset_get_default_asset_Category(launcher_dic, 'default_fanart')
        thumb_banner    = asset_get_default_asset_Category(launcher_dic, 'default_banner')
        thumb_poster    = asset_get_default_asset_Category(launcher_dic, 'default_poster')
        thumb_clearlogo = asset_get_default_asset_Category(launcher_dic, 'default_clearlogo')
        listitem.setArt({'thumb' : thumb_path, 'fanart' : thumb_fanart, 'banner' : thumb_banner, 
                         'poster' : thumb_poster, 'clearlogo' : thumb_clearlogo })

        # --- Create context menu ---
        commands = []
        launcherID = launcher_dic['id']
        categoryID = launcher_dic['categoryID']
        commands.append(('View Launcher data',   self._misc_url_RunPlugin('VIEW_LAUNCHER', categoryID, launcherID), ))
        commands.append(('View Launcher report', self._misc_url_RunPlugin('VIEW_LAUNCHER_REPORT', categoryID, launcherID), ))
        commands.append(('Create New Launcher',  self._misc_url_RunPlugin('ADD_LAUNCHER', categoryID), ))
        commands.append(('Edit Launcher',        self._misc_url_RunPlugin('EDIT_LAUNCHER', categoryID, launcherID), ))
        # >> ROMs launcher
        if launcher_dic['rompath']:
            commands.append(('Add ROMs', self._misc_url_RunPlugin('ADD_ROMS', categoryID, launcherID), ))
        commands.append(('Search ROMs in Launcher', self._misc_url_RunPlugin('SEARCH_LAUNCHER', categoryID, launcherID), ))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', )) # If using window ID then use "10003"
        commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        listitem.addContextMenuItems(commands, replaceItems = True)

        # --- Add row to ListItem ---
        url_str = self._misc_url('SHOW_ROMS', categoryID, launcherID)
        folder_flag = True if launcher_dic['rompath'] else False
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = folder_flag)

    #
    # Former  _get_roms
    # Renders the roms listbox for a given launcher
    #
    def _command_render_roms(self, categoryID, launcherID):
        if launcherID not in self.launchers:
            log_error('_command_render_roms() Launcher hash not found.')
            kodi_dialog_OK('@_command_render_roms(): Launcher hash not found. Report this bug.')
            return

        # Load ROMs for this launcher and display them
        selectedLauncher = self.launchers[launcherID]
        roms_file_path = fs_get_ROMs_file_path(ROMS_DIR, selectedLauncher['roms_base_noext'])

        # Check if XML file with ROMs exist
        if not os.path.isfile(roms_file_path):
            kodi_notify('Launcher XML/JSON missing. Add items to launcher.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # --- Load ROMs ---
        roms = fs_load_ROMs(ROMS_DIR, selectedLauncher['roms_base_noext'])
        if not roms:
            kodi_notify('Launcher XML/JSON empty. Add items to launcher.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # --- Load favourites ---
        # >> Optimisation: Transform the dictionary keys into a set. Sets are the fastest
        #    when checking if an element exists.
        roms_fav = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
        roms_fav_set = set(roms_fav.keys())

        # >> Set content type
        self._misc_set_content_and_all_sorting_methods()

        # --- Display ROMs ---
        for key in sorted(roms, key = lambda x : roms[x]['filename']):
            self._gui_render_rom_row(categoryID, launcherID, key, roms[key], key in roms_fav_set)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Former  _add_rom()
    # Note that if we are rendering favourites, categoryID = VCATEGORY_FAVOURITES_ID
    # Note that if we are rendering virtual launchers, categoryID = VCATEGORY_*_ID
    #
    def _gui_render_rom_row(self, categoryID, launcherID, romID, rom, rom_is_in_favourites):
        # --- Do not render row if ROM is finished ---
        if rom['finished'] and self.settings['display_hide_finished']:
            return

        # --- Create listitem row ---
        rom_raw_name = rom['m_name']
        if categoryID == VCATEGORY_FAVOURITES_ID:
            kodi_def_thumb  = 'DefaultProgram.png'
            thumb_path      = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_thumb', kodi_def_thumb)
            thumb_fanart    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_fanart')
            thumb_banner    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_banner')
            thumb_poster    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_poster')
            thumb_clearlogo = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_clearlogo')
            platform = rom['platform']

            # >> If we are rendering Favourites then mark fav_status            
            if   rom['fav_status'] == 'OK':                rom_name = '{0} [COLOR green][OK][/COLOR]'.format(rom_raw_name)
            elif rom['fav_status'] == 'Unlinked ROM':      rom_name = '{0} [COLOR yellow][Unlinked ROM][/COLOR]'.format(rom_raw_name)
            elif rom['fav_status'] == 'Unlinked Launcher': rom_name = '{0} [COLOR yellow][Unlinked Launcher][/COLOR]'.format(rom_raw_name)
            elif rom['fav_status'] == 'Broken':            rom_name = '{0} [COLOR red][Broken][/COLOR]'.format(rom_raw_name)
            else:                                          rom_name = rom_raw_name
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            kodi_def_thumb  = 'DefaultProgram.png'
            thumb_path      = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_thumb', kodi_def_thumb)
            thumb_fanart    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_fanart')
            thumb_banner    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_banner')
            thumb_poster    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_poster')
            thumb_clearlogo = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_clearlogo')
            platform = rom['platform']
            rom_name = rom_raw_name
        # If rendering a virtual launcher mark nothing
        elif categoryID == VCATEGORY_TITLE_ID or categoryID == VCATEGORY_YEARS_ID or \
             categoryID == VCATEGORY_GENRE_ID or categoryID == VCATEGORY_STUDIO_ID:
            kodi_def_thumb  = 'DefaultProgram.png'
            thumb_path      = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_thumb', kodi_def_thumb)
            thumb_fanart    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_fanart')
            thumb_banner    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_banner')
            thumb_poster    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_poster')
            thumb_clearlogo = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_clearlogo')
            platform = rom['platform']
            if   rom['nointro_status'] == 'Have':    rom_name = '{0} [COLOR green][Have][/COLOR]'.format(rom_raw_name)
            elif rom['nointro_status'] == 'Miss':    rom_name = '{0} [COLOR red][Miss][/COLOR]'.format(rom_raw_name)
            elif rom['nointro_status'] == 'Unknown': rom_name = '{0} [COLOR yellow][Unknown][/COLOR]'.format(rom_raw_name)
            else:                                    rom_name = rom_raw_name
            if rom_is_in_favourites: rom_name += ' [COLOR violet][Fav][/COLOR]'
        # >> If rendering a normal launcher OR virtual launcher then mark nointro_status and rom_is_in_favourites
        else:
            # >> If ROM has no fanart then use launcher fanart
            launcher = self.launchers[launcherID]
            kodi_def_thumb  = 'DefaultProgram.png'
            kodi_def_fanart = launcher['s_fanart']
            thumb_path      = asset_get_default_asset_Launcher_ROM(rom, launcher, 'roms_default_thumb', kodi_def_thumb)
            thumb_fanart    = asset_get_default_asset_Launcher_ROM(rom, launcher, 'roms_default_fanart', kodi_def_fanart)
            thumb_banner    = asset_get_default_asset_Launcher_ROM(rom, launcher, 'roms_default_banner')
            thumb_poster    = asset_get_default_asset_Launcher_ROM(rom, launcher, 'roms_default_poster')
            thumb_clearlogo = asset_get_default_asset_Launcher_ROM(rom, launcher, 'roms_default_clearlogo')
            platform = launcher['platform']

            # >> Mark No-Intro status
            if   rom['nointro_status'] == 'Have':    rom_name = '{0} [COLOR green][Have][/COLOR]'.format(rom_raw_name)
            elif rom['nointro_status'] == 'Miss':    rom_name = '{0} [COLOR red][Miss][/COLOR]'.format(rom_raw_name)
            elif rom['nointro_status'] == 'Unknown': rom_name = '{0} [COLOR yellow][Unknown][/COLOR]'.format(rom_raw_name)
            else:                                    rom_name = rom_raw_name

            # >> If listing regular launcher and rom is in favourites, mark it
            if rom_is_in_favourites:
                # --- Workaround so the alphabetical order is not lost ---
                # log_debug('gui_render_rom_row() ROM is in favourites {0}'.format(rom_name))
                # NOTE Missing ROMs must never be in favourites... However, mark them to help catching bugs.
                # rom_name = '[COLOR violet]{0} [Fav][/COLOR]'.format(rom['m_name'])
                # rom_name = '{0} [COLOR violet][Fav][/COLOR]'.format(rom['m_name'])
                rom_name += ' [COLOR violet][Fav][/COLOR]'

        # --- Add ROM to lisitem ---
        ICON_OVERLAY = 5 if rom['finished'] else 4
        listitem = xbmcgui.ListItem(rom_name)

        # Interesting... if text formatting labels are set in xbmcgui.ListItem() do not work. However, if
        # labels are set as Title in setInfo(), then they work but the alphabetical order is lost!
        # I solved this alphabetical ordering issue by placing a coloured tag [Fav] at the and of the ROM name
        # instead of changing the whole row colour.
        listitem.setInfo('video', {'title'   : rom_name,         'year'    : rom['m_year'],
                                   'genre'   : rom['m_genre'],   'plot'    : rom['m_plot'],
                                   'studio'  : rom['m_studio'],  'rating'  : rom['m_rating'],
                                   'trailer' : rom['s_trailer'], 'overlay' : ICON_OVERLAY })
        listitem.setProperty('platform', platform)

        # --- Set ROM artwork ---
        # >> AEL custom artwork fields
        listitem.setArt({'title'     : rom['s_title'],     'snap'    : rom['s_snap'],
                         'boxfront'  : rom['s_boxfront'],  'boxback' : rom['s_boxback'], 
                         'cartridge' : rom['s_cartridge'], 'map'     : rom['s_map'] })

        # >> Kodi official artwork fields
        listitem.setArt({'thumb'  : thumb_path,   'fanart' : thumb_fanart,
                         'banner' : thumb_banner, 'poster' : thumb_poster, 'clearlogo' : thumb_clearlogo })

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

        # --- Create context menu ---
        commands = []
        if categoryID == VCATEGORY_FAVOURITES_ID:
            commands.append(('View Favourite ROM data',    self._misc_url_RunPlugin('VIEW_ROM',        VCATEGORY_FAVOURITES_ID, VLAUNCHER_FAVOURITES_ID, romID), ))
            commands.append(('Manage Favourite ROMs',      self._misc_url_RunPlugin('MANAGE_FAV',      VCATEGORY_FAVOURITES_ID, VLAUNCHER_FAVOURITES_ID, romID), ))
            commands.append(('Edit ROM in Favourites',     self._misc_url_RunPlugin('EDIT_ROM',        VCATEGORY_FAVOURITES_ID, VLAUNCHER_FAVOURITES_ID, romID), ))
            commands.append(('Delete ROM from Favourites', self._misc_url_RunPlugin('DELETE_ROM',      VCATEGORY_FAVOURITES_ID, VLAUNCHER_FAVOURITES_ID, romID), ))
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            commands.append(('View Collection ROM data',   self._misc_url_RunPlugin('VIEW_ROM',          VCATEGORY_COLLECTIONS_ID, launcherID, romID), ))
            commands.append(('Move ROM up',                self._misc_url_RunPlugin('MOVE_COL_ROM_UP',   VCATEGORY_COLLECTIONS_ID, launcherID, romID), ))
            commands.append(('Move ROM down',              self._misc_url_RunPlugin('MOVE_COL_ROM_DOWN', VCATEGORY_COLLECTIONS_ID, launcherID, romID), ))
            commands.append(('Edit ROM in Collection',     self._misc_url_RunPlugin('EDIT_ROM',          VCATEGORY_COLLECTIONS_ID, launcherID, romID), ))
            commands.append(('Delete ROM from Collection', self._misc_url_RunPlugin('DELETE_ROM',        VCATEGORY_COLLECTIONS_ID, launcherID, romID), ))
        elif categoryID == VCATEGORY_TITLE_ID or categoryID == VCATEGORY_YEARS_ID or \
             categoryID == VCATEGORY_GENRE_ID or categoryID == VCATEGORY_STUDIO_ID:
            commands.append(('View Virtual Launcher ROM data', self._misc_url_RunPlugin('VIEW_ROM', categoryID, launcherID, romID), ))
            commands.append(('Add ROM to AEL Favourites',      self._misc_url_RunPlugin('ADD_TO_FAV', categoryID, launcherID, romID), ))
        else:
            commands.append(('View ROM data',             self._misc_url_RunPlugin('VIEW_ROM', categoryID, launcherID, romID), ))
            commands.append(('Edit ROM',                  self._misc_url_RunPlugin('EDIT_ROM', categoryID, launcherID, romID), ))
            commands.append(('Search ROMs in Launcher',   self._misc_url_RunPlugin('SEARCH_LAUNCHER', categoryID, launcherID), ))
            commands.append(('Add ROM to AEL Favourites', self._misc_url_RunPlugin('ADD_TO_FAV', categoryID, launcherID, romID), ))
            commands.append(('Add ROM to Collection',     self._misc_url_RunPlugin('ADD_TO_COLLECTION', categoryID, launcherID, romID), ))
            commands.append(('Delete ROM',                self._misc_url_RunPlugin('DELETE_ROM', categoryID, launcherID, romID), ))
        # commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', )) # If using window ID then use "10003"
        # commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        listitem.addContextMenuItems(commands, replaceItems = True)

        # --- Add row ---
        # URLs must be different depending on the content type. If not, lot of 
        # WARNING: CreateLoader - unsupported protocol(plugin) in the log. See http://forum.kodi.tv/showthread.php?tid=187954
        url_str = self._misc_url('LAUNCH_ROM', categoryID, launcherID, romID)
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
        self._misc_set_content_and_all_sorting_methods()
        
        # --- Load Favourite ROMs ---
        roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
        if not roms:
            kodi_notify('Favourites is empty. Add ROMs to Favourites first.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # --- Display Favourites ---
        for key in sorted(roms, key= lambda x : roms[x]['filename']):
            self._gui_render_rom_row(VCATEGORY_FAVOURITES_ID, VLAUNCHER_FAVOURITES_ID, key, roms[key], False)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Render launchers in virtual categories: title, year, genre, studio
    #
    def _command_render_virtual_category(self, virtual_categoryID):
        # >> Content type and sorting method
        self._misc_set_content_type()
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)

        
        # --- Load virtual launchers in this category ---
        if virtual_categoryID == VCATEGORY_TITLE_ID:
            vcategory_db_filename = VCAT_TITLE_FILE_PATH
            vcategory_name = 'Browse by Title'
        elif virtual_categoryID == VCATEGORY_YEARS_ID:
            vcategory_db_filename = VCAT_YEARS_FILE_PATH
            vcategory_name = 'Browse by Year'
        elif virtual_categoryID == VCATEGORY_GENRE_ID:
            vcategory_db_filename = VCAT_GENRE_FILE_PATH
            vcategory_name = 'Browse by Genre'
        elif virtual_categoryID == VCATEGORY_STUDIO_ID:
            vcategory_db_filename = VCAT_STUDIO_FILE_PATH
            vcategory_name = 'Browse by Studio'
        else:
            log_error('_command_render_virtual_category() Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
            kodi_dialog_OK('Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
            return

        # --- If the virtual category has no launchers then render nothing ---
        # >> Also, tell the user to update the virtual launcher database
        if not os.path.isfile(vcategory_db_filename):
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
                                       'label'    : 'Label text',
                                       'plot'     : 'Plot text',    'Studio'    : 'Studio text',
                                       'genre'    : 'Genre text',   'Premiered' : 'Premiered text',
                                       'year'     : 'Year text',
                                       'overlay'  : 4} )
            # Set ListItem artwork
            listitem.setArt({'icon': 'DefaultFolder.png'})
            # --- Create context menu ---
            commands = []
            # launcherID = launcher_dic['id']
            # categoryID = launcher_dic['categoryID']
            # commands.append(('Create New Launcher', self._misc_url_RunPlugin('ADD_LAUNCHER', categoryID), ))
            # commands.append(('Edit Launcher', self._misc_url_RunPlugin('EDIT_LAUNCHER', categoryID, launcherID), ))
            # >> ROMs launcher
            # if not launcher_dic['rompath'] == '':
            #     commands.append(('Add ROMs', self._misc_url_RunPlugin('ADD_ROMS', categoryID, launcherID), ))
            # commands.append(('Search ROMs in Launcher', self._misc_url_RunPlugin('SEARCH_LAUNCHER', categoryID, launcherID), ))
            # >> Add Launcher URL to Kodi Favourites (do not know how to do it yet)
            commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', ))
            commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
            listitem.addContextMenuItems(commands, replaceItems = True)

            url_str = self._misc_url('SHOW_ROMS', virtual_categoryID, vlauncher_id)
            xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Renders ROMs in a virtual launcher.
    #
    def _command_render_virtual_launcher_roms(self, virtual_categoryID, virtual_launcherID):
        # >> Content type and sorting method
        self._misc_set_content_and_all_sorting_methods()

        # --- Load virtual launchers in this category ---
        if virtual_categoryID == VCATEGORY_TITLE_ID:
            vcategory_db_dir = VIRTUAL_CAT_TITLE_DIR
        elif virtual_categoryID == VCATEGORY_YEARS_ID:
            vcategory_db_dir = VIRTUAL_CAT_YEARS_DIR
        elif virtual_categoryID == VCATEGORY_GENRE_ID:
            vcategory_db_dir = VIRTUAL_CAT_GENRE_DIR
        elif virtual_categoryID == VCATEGORY_STUDIO_ID:
            vcategory_db_dir = VIRTUAL_CAT_STUDIO_DIR
        else:
            log_error('_command_render_virtual_launcher_roms() Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
            kodi_dialog_OK('Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
            return

        # --- Load Virtual Launcher DB ---
        hashed_db_filename = os.path.join(vcategory_db_dir, virtual_launcherID + '.json')
        if not os.path.isfile(hashed_db_filename):
            kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
            return
        roms = fs_load_VCategory_ROMs_JSON(vcategory_db_dir, virtual_launcherID)
        if not roms:
            kodi_notify('Virtual category ROMs XML empty. Add items to favourites first.')
            return

        # --- Load favourites ---
        # >> Optimisation: Transform the dictionary keys into a set. Sets are the fastest
        #    when checking if an element exists.
        roms_fav = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
        roms_fav_set = set(roms_fav.keys())

        # --- Display Favourites ---
        for key in sorted(roms, key= lambda x : roms[x]['filename']):
            self._gui_render_rom_row(virtual_categoryID, virtual_launcherID, key, roms[key], key in roms_fav_set)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Adds ROM to favourites
    #
    def _command_add_to_favourites(self, categoryID, launcherID, romID):
        # >> ROM in Virtual Launcher
        if categoryID == VCATEGORY_TITLE_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_TITLE_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        elif categoryID == VCATEGORY_YEARS_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_YEARS_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        elif categoryID == VCATEGORY_GENRE_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_GENRE_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        elif categoryID == VCATEGORY_STUDIO_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_STUDIO_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        # >> ROMs in standard launcher
        else:
            launcher = self.launchers[launcherID]
            roms = fs_load_ROMs(ROMS_DIR, launcher['roms_base_noext'])

        # >> Sanity check
        if not roms:
            kodi_dialog_OK('Empty roms launcher in _command_add_to_favourites(). This is a bug, please report it.')
            return

        # --- Load favourites ---
        roms_fav = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)

        # DEBUG
        log_verb('Adding ROM to Favourites')
        log_verb('romID  {0}'.format(romID))
        log_verb('m_name {0}'.format(roms[romID]['m_name']))

        # Check if ROM already in favourites an warn user if so
        if romID in roms_fav:
            log_verb('Already in favourites')
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher',
                               'ROM {0} is already on AEL Favourites. Overwrite it?'.format(roms[romID]['m_name']))
            if not ret:
                log_verb('User does not want to overwrite. Exiting.')
                return
        # Confirm if rom should be added
        else:
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher',
                                'ROM {0}. Add this ROM to AEL Favourites?'.format(roms[romID]['m_name']))
            if not ret:
                log_verb('User does not confirm addition. Exiting.')
                return

        # --- Add ROM to favourites ROMs and save to disk ---
        roms_fav[romID] = fs_get_Favourite_from_ROM(roms[romID], launcher)
        # >> If thumb is empty then use launcher thum. / If fanart is empty then use launcher fanart.
        # if roms_fav[romID]['thumb']  == '': roms_fav[romID]['thumb']  = launcher['thumb']
        # if roms_fav[romID]['fanart'] == '': roms_fav[romID]['fanart'] = launcher['fanart']
        fs_write_Favourites_JSON(FAV_JSON_FILE_PATH, roms_fav)
        kodi_refresh_container()

    #
    # Manage Favourite ROMs. Similar to Edit ROM/Edit Launcher
    # Will be displayed on Favourite ROMs context menu only.
    #
    def _command_manage_favourites(self, categoryID, launcherID, romID):
        # --- Load Favourite ROMs ---
        roms_fav = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
        name = roms_fav[romID]['m_name']

        # --- Show selection dialog ---
        dialog = xbmcgui.Dialog()
        type = dialog.select('Manage Favourite ROM {0}'.format(name),
                            ['Check all Favourite ROMs', 
                             'Repair all Unlinked ROMs', 
                             'Choose another parent ROM for Favourite ROM...'])

        # --- Check Favourite ROMs ---
        if type == 0:
            kodi_notify('Checking Favourite ROMs...')
            self._fav_check_favourites(roms_fav)

        # --- Repair Unliked Favourite ROMs ---
        elif type == 1:
            # 1) Traverse list of Favourites.
            # 2) If romID not found in launcher, then search for a ROM with same filename.
            # 3) If found, then replace romID in Favourites with romID of found ROM. Do not
            #    copy any metadata because user maybe customised Favourite ROM.
            kodi_notify('Repairing Unlinked Favourite ROMs...')
            # >> Refreshing Favourite status will locate Unlinked ROMs!
            self._fav_check_favourites(roms_fav)
            for rom_fav_ID in roms_fav:
                if roms_fav[rom_fav_ID]['fav_status'] != 'Unlinked ROM': continue
                fav_name = roms_fav[rom_fav_ID]['m_name']
                log_debug('_command_manage_favourites() Relinking Unlinked ROM Fav {0}'.format(fav_name))

                # >> Get ROMs of launcher
                launcher_id = roms_fav[rom_fav_ID]['launcherID']
                launcher_roms = fs_load_ROMs(ROMS_DIR, self.launchers[launcher_id]['roms_base_noext'])
                
                # >> Is there a ROM with same filename as the Favourite?
                filename_found = False
                for rom_id in launcher_roms:
                    if launcher_roms[rom_id]['filename'] == roms_fav[rom_fav_ID]['filename']:
                        filename_found = True
                        new_rom_fav_ID = rom_id
                        break

                # >> Relink Favourite ROM
                if filename_found:
                    log_debug('_command_manage_favourites() Relinked to {0}'.format(new_rom_fav_ID))
                    # >> Remove old Favourite before inserting new one!
                    rom_temp = roms_fav[rom_fav_ID]
                    roms_fav.pop(rom_fav_ID)
                    rom_temp['id']         = new_rom_fav_ID
                    rom_temp['launcherID'] = launcher_id
                    rom_temp['fav_status'] = 'OK'
                    roms_fav[new_rom_fav_ID] = rom_temp
                else:
                    log_debug('_command_manage_favourites() Filename in launcher not found! This is a BUG.')

        # --- Choose another parent ROM for Favourite ---
        elif type == 2:
            # STEP 1: select new launcher.
            launcher_IDs = []
            launcher_names = []
            for launcher_id in self.launchers:
                # >> ONLY SHOW ROMs LAUNCHERS, NOT STANDALONE LAUNCHERS!!!
                if self.launchers[launcher_id]['rompath'] == '': continue
                launcher_IDs.append(launcher_id)
                launcher_names.append(self.launchers[launcher_id]['m_name'])
                
            # Order alphabetically both lists
            sorted_idx = [i[0] for i in sorted(enumerate(launcher_names), key=lambda x:x[1])]
            launcher_IDs   = [launcher_IDs[i] for i in sorted_idx]
            launcher_names = [launcher_names[i] for i in sorted_idx]
            dialog = xbmcgui.Dialog()
            selected_launcher = dialog.select('New launcher for {0}'.format(roms_fav[romID]['m_name']), launcher_names)
            if selected_launcher < 0: return
                
            # STEP 2: select ROMs in that launcher.
            launcher_id = launcher_IDs[selected_launcher]
            launcher_roms = fs_load_ROMs(ROMS_DIR, self.launchers[launcher_id]['roms_base_noext'])
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
            selected_rom = dialog.select('New ROM for Favourite {0}'.format(roms_fav[romID]['m_name']), roms_names)
            if selected_rom < 0 : return

            # Do the relinking and save favourites.
            launcher_rom_id = roms_IDs[selected_rom]
            current_rom = launcher_roms[launcher_rom_id]
            # Check that the selected ROM ID is not already in Favourites
            if launcher_rom_id in roms_fav:
                kodi_dialog_OK('Selected ROM already in Favourites. Exiting.')
                return
            # Delete current Favourite
            roms_fav.pop(romID)
            # Copy parent ROM data files into favourite.
            # Overwrite everything in Favourite ROM
            launcher = self.launchers[launcher_id]
            roms_fav[launcher_rom_id] = fs_get_Favourite_from_ROM(current_rom, launcher)
            # If missing thumb/fanart then use launcher's
            if roms_fav[launcher_rom_id]['thumb']  == '': roms_fav[launcher_rom_id]['thumb']  = launcher['thumb']
            if roms_fav[launcher_rom_id]['fanart'] == '': roms_fav[launcher_rom_id]['fanart'] = launcher['fanart']

        # --- User cancelled dialog ---
        elif type < 0:
            return
        
        # --- If we reach this point save favourites and refresh container ---
        fs_write_Favourites_JSON(FAV_JSON_FILE_PATH, roms_fav)
        kodi_refresh_container()

    #
    # Check ROMs in favourites and set fav_status field.
    # roms_fav edited by passing by assigment, dictionaries are mutable.
    #
    def _fav_check_favourites(self, roms_fav):
        # Reset fav_status filed for all favourites
        log_debug('_fav_check_favourites() STEP 0: Reset status')
        for rom_fav_ID in roms_fav:
            roms_fav[rom_fav_ID]['fav_status'] = 'OK'

        # STEP 1: Find Favourites with missing launchers
        log_debug('_fav_check_favourites() STEP 1: Search unlinked Launchers')
        for rom_fav_ID in roms_fav:
            if roms_fav[rom_fav_ID]['launcherID'] not in self.launchers:
                log_verb('Fav ROM "{0}" Unlinked Launcher because launcherID not in self.launchers'.format(roms_fav[rom_fav_ID]['m_name']))
                roms_fav[rom_fav_ID]['fav_status'] = 'Unlinked Launcher'

        # STEP 2: Find missing ROM ID
        # >> Get a list of launchers Favourite ROMs belong
        log_debug('_fav_check_favourites() STEP 2: Search unlinked ROMs')
        launchers_fav = set()
        for rom_fav_ID in roms_fav: launchers_fav.add(roms_fav[rom_fav_ID]['launcherID'])

        # >> Traverse list of launchers. For each launcher, load ROMs it and check all favourite ROMs that belong to
        # >> that launcher.
        for launcher_id in launchers_fav:
            # >> If Favourite does not have launcher skip it. It has been marked as 'Unlinked Launcher'
            # >> in step 1.
            if launcher_id not in self.launchers: continue

            # >> Load launcher ROMs
            roms = fs_load_ROMs(ROMS_DIR, self.launchers[launcher_id]['roms_base_noext'])

            # Traverse all favourites and check them if belong to this launcher.
            # This should be efficient because traversing favourites is cheap but loading ROMs is expensive.
            for rom_fav_ID in roms_fav:
                if roms_fav[rom_fav_ID]['launcherID'] == launcher_id:
                    # Check if ROM ID exists
                    if roms_fav[rom_fav_ID]['id'] not in roms:
                        log_verb('Fav ROM "{0}" Unlinked ROM because romID not in launcher ROMs'.format(roms_fav[rom_fav_ID]['m_name']))
                        roms_fav[rom_fav_ID]['fav_status'] = 'Unlinked ROM'

        # STEP 3: Check if file exists. Even if the ROM ID is not there because user
        # deleted ROM or launcher, the file may still be there.
        log_debug('_fav_check_favourites() STEP 3: Search broken ROMs')
        for rom_fav_ID in roms_fav:
            if not os.path.isfile(roms_fav[rom_fav_ID]['filename']):
                log_verb('Fav ROM "{0}" broken because filename does not exist'.format(roms_fav[rom_fav_ID]['m_name']))
                roms_fav[rom_fav_ID]['fav_status'] = 'Broken'

    #
    # Renders a listview with all collections
    #
    def _command_render_collections(self):
        # >> Content type and sorting method
        self._misc_set_content_type()
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)

        # --- Load collection index ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)

        # --- If the virtual category has no launchers then render nothing ---
        if not collections:
            kodi_notify('No collections in database. Add a collection first.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # --- Render collections as categories ---
        for collection_id in collections:
            collection = collections[collection_id]
            collection_name = collection['name']
            listitem = xbmcgui.ListItem(collection_name)
            listitem.setInfo('video', {'Title'    : 'Title text',
                                       'Label'    : 'Label text',
                                       'Plot'     : 'Plot text',    'Studio'    : 'Studio text',
                                       'Genre'    : 'Genre text',   'Premiered' : 'Premiered text',
                                       'Year'     : 'Year text',    'Writer'    : 'Writer text',
                                       'Trailer'  : 'Trailer text', 'Director'  : 'Director text',
                                       'overlay'  : 4})
            listitem.setArt({'icon': 'DefaultFolder.png'})

            # --- Create context menu ---
            commands = []
            commands.append(('Create New Collection', self._misc_url_RunPlugin('ADD_COLLECTION'), ))
            commands.append(('Edit Collection', self._misc_url_RunPlugin('EDIT_COLLECTION', VCATEGORY_COLLECTIONS_ID, collection_id), ))
            commands.append(('Delete Collection', self._misc_url_RunPlugin('DELETE_COLLECTION', VCATEGORY_COLLECTIONS_ID, collection_id), ))
            commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', ))
            commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
            listitem.addContextMenuItems(commands, replaceItems = True)

            # >> Use ROMs renderer to display collection ROMs
            url_str = self._misc_url('SHOW_COLLECTION_ROMS', VCATEGORY_COLLECTIONS_ID, collection_id)
            xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    def _command_render_collection_ROMs(self, categoryID, launcherID):
        # --- Load Collection index and ROMs ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
        collection = collections[launcherID]
        collection_rom_list = fs_load_Collection_ROMs_JSON(COLLECTIONS_DIR, collection['roms_base_noext'])
        if not collection_rom_list:
            kodi_notify('Collection is empty. Add ROMs to this collection first.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # --- Display Collection ---
        for rom in collection_rom_list:
            self._gui_render_rom_row(categoryID, launcherID, rom['id'], rom, False)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Adds a new collection
    #
    def _command_add_collection(self):
        # --- Load collection index ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)

        # --- Get new collection name ---
        dialog = xbmcgui.Dialog()
        keyboard = xbmc.Keyboard('', 'New Collection name')
        keyboard.doModal()
        if not keyboard.isConfirmed(): return
        
        # --- Add new collection to database ---
        collection = fs_new_collection()
        collection_name      = keyboard.getText()
        collection_id_md5    = hashlib.md5(collection_name.encode('utf-8'))
        collection_UUID      = collection_id_md5.hexdigest()
        collection_base_name = fs_get_collection_ROMs_basename(collection_name, collection_UUID)
        collection['id']              = collection_UUID
        collection['name']            = collection_name
        collection['roms_base_noext'] = collection_base_name
        collections[collection_UUID]  = collection
        log_debug('_command_add_collection() id              "{0}"'.format(collection['id']))
        log_debug('_command_add_collection() name            "{0}"'.format(collection['name']))
        log_debug('_command_add_collection() roms_base_noext "{0}"'.format(collection['roms_base_noext']))
        kodi_dialog_OK("Created new Collection named '{0}'.".format(collection_name))

        # --- Save collections XML database ---
        fs_write_Collection_index_XML(COLLECTIONS_FILE_PATH, collections)

    #
    # Edits collection artwork
    #
    def _command_edit_collection(self, categoryID, launcherID):
        # --- Load collection index ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
        collection = collections[launcherID]

        # --- Shows a select box with the options to edit ---
        dialog = xbmcgui.Dialog()
        type = dialog.select('Select action for Collection {0}'.format(collection['name']),
                             ['Edit Collection name', 
                              'Edit Assets/Artwork...', 
                              'Choose default Assets/Artwork...'])

        # --- Change collection name ---
        if type == 0:
            keyboard = xbmc.Keyboard(collection['name'], 'Edit Collection name')
            keyboard.doModal()
            if keyboard.isConfirmed():
                collection['name'] = keyboard.getText().decode('utf-8')
            else:
                kodi_dialog_OK("Collection '{0}' name not changed".format(collection['name']))
                return

        # --- Edit artwork ---
        elif type == 1:
            status_thumb_str   = 'HAVE' if collection['s_thumb']   else 'MISSING'
            status_fanart_str  = 'HAVE' if collection['s_fanart']  else 'MISSING'
            status_banner_str  = 'HAVE' if collection['s_banner']  else 'MISSING'
            status_flyer_str   = 'HAVE' if collection['s_flyer']   else 'MISSING'
            status_trailer_str = 'HAVE' if collection['s_trailer'] else 'MISSING'
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Edit Category Assets/Artwork',
                                  ["Edit Thumbnail ({0})...".format(status_thumb_str),
                                   "Edit Fanart ({0})...".format(status_fanart_str),
                                   "Edit Banner ({0})...".format(status_banner_str),
                                   "Edit Flyer ({0})...".format(status_flyer_str),
                                   "Edit Trailer ({0})...".format(status_trailer_str)])

            # --- Edit Assets ---
            # >> _gui_edit_asset() returns True if image was changed
            # >> Category is changed using Python passign by assigment
            # >> If this function returns False no changes were made. No need to save categories XML and 
            # >> update container.
            if type2 == 0:
                if not self._gui_edit_asset(KIND_COLLECTION, ASSET_THUMB, collection): return
            elif type2 == 1:
                if not self._gui_edit_asset(KIND_COLLECTION, ASSET_FANART, collection): return
            elif type2 == 2:
                if not self._gui_edit_asset(KIND_COLLECTION, ASSET_BANNER, collection): return
            elif type2 == 3:
                if not self._gui_edit_asset(KIND_COLLECTION, ASSET_FLYER, collection): return
            elif type2 == 4:
                if not self._gui_edit_asset(KIND_COLLECTION, ASSET_TRAILER, collection): return
            # >> User canceled select dialog
            elif type2 < 0: return


        # --- Change default artwork ---
        elif type == 2:
            asset_thumb     = assets_get_asset_name_str(collection['default_thumb'])
            asset_fanart    = assets_get_asset_name_str(collection['default_fanart'])
            asset_banner    = assets_get_asset_name_str(collection['default_banner'])
            asset_poster    = assets_get_asset_name_str(collection['default_poster'])
            asset_clearlogo = assets_get_asset_name_str(collection['default_clearlogo'])
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Edit Category Assets/Artwork',
                                  ['Choose asset for Thumb (currently {0})'.format(asset_thumb), 
                                   'Choose asset for Fanart (currently {0})'.format(asset_fanart),
                                   'Choose asset for Banner (currently {0})'.format(asset_banner),
                                   'Choose asset for Poster (currently {0})'.format(asset_poster),
                                   'Choose asset for Clearlogo (currently {0})'.format(asset_clearlogo)])

            if type2 == 0:
                type3 = xbmcgui.Dialog().select('Choose default Asset for Thumb', DEFAULT_CATEGORY_ASSET_LIST)
                if type3 < 0: return
                assets_choose_category_artwork(collection, 'default_thumb', type3)

            elif type2 == 1:
                type3 = xbmcgui.Dialog().select('Choose default Asset for Fanart', DEFAULT_CATEGORY_ASSET_LIST)
                if type3 < 0: return
                assets_choose_category_artwork(collection, 'default_fanart', type3)

            elif type2 == 2:
                type3 = xbmcgui.Dialog().select('Choose default Asset for Banner', DEFAULT_CATEGORY_ASSET_LIST)
                if type3 < 0: return
                assets_choose_category_artwork(collection, 'default_banner', type3)

            elif type2 == 3:
                type3 = xbmcgui.Dialog().select('Choose default Asset for Poster', DEFAULT_CATEGORY_ASSET_LIST)
                if type3 < 0: return
                assets_choose_category_artwork(collection, 'default_poster', type3)

            elif type2 == 4:
                type3 = xbmcgui.Dialog().select('Choose default Asset for Clearlogo', DEFAULT_CATEGORY_ASSET_LIST)
                if type3 < 0: return
                assets_choose_category_artwork(collection, 'default_clearlogo', type3)

        # >> User cancel dialog
        elif type < 0: return

        # --- Save collection index and refresh view ---
        fs_write_Collection_index_XML(COLLECTIONS_FILE_PATH, collections)
        kodi_refresh_container()

    #
    # Deletes a collection and associated ROMs.
    #
    def _command_delete_collection(self, categoryID, launcherID):
        # --- Load collection index and ROMs ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
        collection = collections[launcherID]
        collection_rom_list = fs_load_Collection_ROMs_JSON(COLLECTIONS_DIR, collection['roms_base_noext'])

        # --- Confirm deletion ---
        num_roms = len(collection_rom_list)
        
        ret = kodi_dialog_yesno('Collection {0} has {1} ROMs. '.format(collection['name'], num_roms) +
                                'Are you sure you want to delete it?')
        if not ret: return
    
        # --- Remove JSON file and delete collection object ---
        collection_file_path = os.path.join(COLLECTIONS_DIR, collection['roms_base_noext'] + '.json')
        log_debug('Removing Collection JSON "{0}"'.format(collection_file_path))
        try:
            if os.path.isfile(collection_file_path):
                os.remove(collection_file_path)
        except OSError:
            log_error('_gui_remove_launcher() (OSError) exception deleting "{0}"'.format(collection_file_path))
            kodi_notify_warn('OSError exception deleting collection JSON')
        collections.pop(launcherID)
        fs_write_Collection_index_XML(COLLECTIONS_FILE_PATH, collections)
        kodi_refresh_container()

    #
    # This function is called from a context menu and so self.addon_handle = -1. In this case, it is
    # not necessary to call xbmcplugin.endOfDirectory() if function fails because we are not rendering
    # a ListItem.
    #
    def _command_move_collection_rom_up(self, categoryID, launcherID, romID):
        # --- Load Collection ROMs ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
        collection = collections[launcherID]
        collection_rom_list = fs_load_Collection_ROMs_JSON(COLLECTIONS_DIR, collection['roms_base_noext'])
        num_roms = len(collection_rom_list)
        if not collection_rom_list:
            kodi_notify('Collection is empty. Add ROMs to this collection first.')
            return

        # >> Get position of current ROM in the list
        current_ROM_position = -1;
        for i, rom in enumerate(collection_rom_list):
            if romID == rom['id']:
                current_ROM_position = i
                break
        if current_ROM_position < 0:
            kodi_notify_warn('ROM not found in list. This is a bug!')
            return
        log_verb('_command_move_collection_rom_up() Collection {0} ({1})'.format(collection['name'], collection['id']))
        log_verb('_command_move_collection_rom_up() Collection has {0} ROMs'.format(num_roms))
        log_verb('_command_move_collection_rom_up() Moving ROM in position {0} up'.format(current_ROM_position))

        # >> If ROM is first of the list do nothing
        if current_ROM_position == 0:
            kodi_dialog_OK('ROM is in first position of the Collection. Cannot be moved up.')
            return

        # >> Reorder list
        original_order = range(num_roms)
        new_order = original_order
        new_order[current_ROM_position - 1] = current_ROM_position
        new_order[current_ROM_position]     = current_ROM_position - 1
        reordered_rom_list = [collection_rom_list[i] for i in new_order]

        # >> Save reordered collection ROMs
        fs_write_Collection_ROMs_JSON(COLLECTIONS_DIR, collection['roms_base_noext'], reordered_rom_list)
        kodi_refresh_container()
            
    def _command_move_collection_rom_down(self, categoryID, launcherID, romID):
        # --- Load Collection ROMs ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
        collection = collections[launcherID]
        collection_rom_list = fs_load_Collection_ROMs_JSON(COLLECTIONS_DIR, collection['roms_base_noext'])
        num_roms = len(collection_rom_list)
        if not collection_rom_list:
            kodi_notify('Collection is empty. Add ROMs to this collection first.')
            return

        # >> Get position of current ROM in the list
        current_ROM_position = -1;
        for i, rom in enumerate(collection_rom_list):
            if romID == rom['id']:
                current_ROM_position = i
                break
        if current_ROM_position < 0:
            kodi_notify_warn('ROM not found in list. This is a bug!')
            return
        log_verb('_command_move_collection_rom_down() Collection {0} ({1})'.format(collection['name'], collection['id']))
        log_verb('_command_move_collection_rom_down() Collection has {0} ROMs'.format(num_roms))
        log_verb('_command_move_collection_rom_down() Moving ROM in position {0} down'.format(current_ROM_position))

        # >> If ROM is last of the list do nothing
        if current_ROM_position == num_roms - 1:
            kodi_dialog_OK('ROM is in last position of the Collection. Cannot be moved down.')
            return

        # >> Reorder list
        original_order = range(num_roms)
        new_order = original_order
        new_order[current_ROM_position]     = current_ROM_position + 1
        new_order[current_ROM_position + 1] = current_ROM_position
        reordered_rom_list = [collection_rom_list[i] for i in new_order]

        # >> Save reordered collection ROMs
        fs_write_Collection_ROMs_JSON(COLLECTIONS_DIR, collection['roms_base_noext'], reordered_rom_list)
        kodi_refresh_container()
        
    def _command_add_ROM_to_collection(self, categoryID, launcherID, romID):
        # >> ROM in Virtual Launcher
        if categoryID == VCATEGORY_TITLE_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_TITLE_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        elif categoryID == VCATEGORY_YEARS_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_YEARS_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        elif categoryID == VCATEGORY_GENRE_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_GENRE_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        elif categoryID == VCATEGORY_STUDIO_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_STUDIO_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        # >> ROMs in standard launcher
        else:
            launcher = self.launchers[launcherID]
            roms = fs_load_ROMs(ROMS_DIR, launcher['roms_base_noext'])

        # >> Sanity check
        if not roms:
            kodi_dialog_OK('Empty roms launcher in _command_add_to_favourites(). This is a bug, please report it.')
            return

        # --- Load Collection index ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)

        # --- If no collections so long and thanks for all the fish ---
        if not collections:
            kodi_dialog_OK('You have no Collections! Create a collection first before adding ROMs.')
            return

        # --- Ask user which Collection wants to add the ROM to ---
        dialog = xbmcgui.Dialog()
        collections_id = []
        collections_name = []
        for key in collections:
            collections_id.append(collections[key]['id'])
            collections_name.append(collections[key]['name'])
        selected_idx = dialog.select('Select the collection', collections_name)
        if selected_idx < 0: return
        collectionID = collections_id[selected_idx]

        # --- Load Collection ROMs ---
        collection = collections[collectionID]
        collection_rom_list = fs_load_Collection_ROMs_JSON(COLLECTIONS_DIR, collection['roms_base_noext'])
        log_info('Adding ROM to Collection')
        log_info('Collection {0}'.format(collection['name']))
        log_info('romID      {0}'.format(romID))
        log_info('ROM m_name {0}'.format(roms[romID]['m_name']))

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
                               'ROM {0} is already on Collection {1}. Overwrite it?'.format(roms[romID]['m_name'], collection['name']))
            if not ret:
                log_verb('User does not want to overwrite. Exiting.')
                return
        # >> Confirm if rom should be added
        else:
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher',
                               "ROM '{0}'. Add this ROM to Collection '{1}'?".format(roms[romID]['m_name'], collection['name']))
            if not ret:
                log_verb('User does not confirm addition. Exiting.')
                return

        # --- Add ROM to favourites ROMs and save to disk ---
        # >> Add ROM to the last position in the collection
        collection_rom = fs_get_Favourite_from_ROM(roms[romID], launcher)
        collection_rom_list.append(collection_rom)
        fs_write_Collection_ROMs_JSON(COLLECTIONS_DIR, collection['roms_base_noext'], collection_rom_list)
        kodi_refresh_container()

    #
    # Search ROMs in launcher
    #
    def _command_search_launcher(self, categoryID, launcherID):
        # --- Load ROMs ---
        if launcherID == VLAUNCHER_FAVOURITES_ID:
            roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
            if not roms:
                kodi_notify('Favourites XML empty. Add items to Favourites')
                return
        else:
            if not os.path.isfile(self.launchers[launcherID]['roms_xml_file']):
                kodi_notify('Launcher XML missing. Add items to launcher')
                return
            roms = fs_load_ROMs(ROMS_DIR, self.launchers[launcherID]['roms_base_noext'])
            if not roms:
                kodi_notify('Launcher XML empty. Add items to launcher')
                return

        # Ask user what category to search
        dialog = xbmcgui.Dialog()
        type = dialog.select('Search items...',
                            ['By Title', 'By Release Year', 'By Studio', 'By Genre'])

        # Search by Title
        type_nb = 0
        if type == type_nb:
            keyboard = xbmc.Keyboard('', 'Enter the file title to search...')
            keyboard.doModal()
            if keyboard.isConfirmed():
                search_string = keyboard.getText()
                # If we are displaying a category (showing its launchers) then search should not replace the window,
                # so when the user presses back button (BACKSPACE in keyboard) returned to the launchers again.
                # Pressing the back button is the same as chosing ".." in the listitem.
                # In AL all searches were global, and user was returned to the addon root window always after pressing
                # back (that's why AL replaces the current window with the search window). This make no sense in AEL
                # for launcher searches and may annoy the user.
                url = self._misc_url_search('EXEC_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_TITLE', search_string)
                # log_debug('URL = {0}'.format(url))
                # xbmc.executebuiltin('ReplaceWindow(Programs,{0})'.format(url))
                xbmc.executebuiltin('ActivateWindow(Programs,{0})'.format(url))

                # Using ActivateWindow with return address seems to have no effect. Note that dialogs
                # are called with handle -1, and that seems to cause trouble. ActivateWindow does
                # not honour the url_return.
                # url_return = self._misc_url('SHOW_ROMS', categoryID, launcherID)
                # url_return = self._misc_url('SHOW_LAUNCHERS', categoryID)
                # log_debug('URL RETURN = {0}'.format(url_return))
                # xbmc.executebuiltin('ActivateWindow(Programs,{0},{1})'.format(url, url_return))

                # Does not work --> WARNING: Attempt to use invalid handle -1
                # xbmc.executebuiltin('RunPlugin({0})'.format(url))

                # Does not work
                # xbmc.executebuiltin('RunAddon({0})'.format(url))

        # Search by Release Date
        type_nb = type_nb + 1
        if type == type_nb:
            searched_list = self._search_launcher_field('year', roms)
            dialog = xbmcgui.Dialog()
            selected_value = dialog.select('Select a Release year ...', searched_list)
            if selected_value >= 0:
                search_string = searched_list[selected_value]
                url = self._misc_url_search('EXEC_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_YEAR', search_string)
                # xbmc.executebuiltin('ReplaceWindow(Programs,{0})'.format(url))
                xbmc.executebuiltin('ActivateWindow(Programs,{0})'.format(url))

        # Search by System Platform
        # Note that search by platform does not make sense when searching a launcher because all items have
        # the same platform! It only makes sense for global searches... which AEL does not.
        # I keep this AL old code for reference, though.
        # type_nb = type_nb + 1
        # if type == type_nb:
        #     search = []
        #     search = _search_category(self, "platform")
        #     dialog = xbmcgui.Dialog()
        #     selected = dialog.select('Select a Platform...', search)
        #     if not selected == -1:
        #         xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s/%s)" % (self.base_url, search[selected], SEARCH_PLATFORM_COMMAND))

        # Search by Studio
        type_nb = type_nb + 1
        if type == type_nb:
            searched_list = self._search_launcher_field('studio', roms)
            dialog = xbmcgui.Dialog()
            selected_value = dialog.select('Select a Studio ...', searched_list)
            if selected_value >= 0:
                search_string = searched_list[selected_value]
                url = self._misc_url_search('EXEC_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_STUDIO', search_string)
                # xbmc.executebuiltin('ReplaceWindow(Programs,{0})'.format(url))
                xbmc.executebuiltin('ActivateWindow(Programs,{0})'.format(url))

        # Search by Genre
        type_nb = type_nb + 1
        if type == type_nb:
            searched_list = self._search_launcher_field('genre', roms)
            dialog = xbmcgui.Dialog()
            selected_value = dialog.select('Select a Genre ...', searched_list)
            if selected_value >= 0:
                search_string = searched_list[selected_value]
                url = self._misc_url_search('EXEC_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_GENRE', search_string)
                # xbmc.executebuiltin('ReplaceWindow(Programs,{0})'.format(url))
                xbmc.executebuiltin('ActivateWindow(Programs,{0})'.format(url))

    def _search_launcher_field(self, search_dic_field, roms):
        # Maybe this can be optimized a bit to make the search faster...
        search = []
        for keyr in sorted(roms.iterkeys()):
            if roms[keyr][search_dic_field] == '':
                search.append('[ Not Set ]')
            else:
                search.append(roms[keyr][search_dic_field])
        # Search will have a lot of repeated entries, so converting them to a set makes them unique
        search = list(set(search))
        search.sort()

        return search

    def _command_execute_search_launcher(self, categoryID, launcherID, search_type, search_string):
        if   search_type == 'SEARCH_TITLE'  : rom_search_field = 'm_name'
        elif search_type == 'SEARCH_YEAR'   : rom_search_field = 'm_year'
        elif search_type == 'SEARCH_STUDIO' : rom_search_field = 'm_studio'
        elif search_type == 'SEARCH_GENRE'  : rom_search_field = 'm_genre'

        # --- Load ROMs ---
        if launcherID == VLAUNCHER_FAVOURITES_ID:
            rom_is_in_favourites = True
            roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
            if not roms:
                kodi_notify('Favourites XML empty. Add items to Favourites')
                return
        else:
            rom_is_in_favourites = False
            if not os.path.isfile(self.launchers[launcherID]['roms_xml_file']):
                kodi_notify('Launcher XML missing. Add items to launcher')
                return
            roms = fs_load_ROMs(ROMS_DIR, self.launchers[launcherID]['roms_base_noext'])
            if not roms:
                kodi_notify('Launcher XML empty. Add items to launcher')
                return

        # Go through rom list and search for user input
        rl = {}
        notset = ('[ Not Set ]')
        text = search_string.lower()
        empty = notset.lower()
        for keyr in roms:
            rom = roms[keyr][rom_search_field].lower()
            if rom == '' and text == empty:
                rl[keyr] = roms[keyr]

            if rom_search_field == 'm_name':
                if not rom.find(text) == -1:
                    rl[keyr] = roms[keyr]
            else:
                if rom == text:
                    rl[keyr] = roms[keyr]

        # Print the list sorted (if there is anything to print)
        if not rl:
            kodi_dialog_OK('Search returned no results')
        for key in sorted(rl.iterkeys()):
            self._gui_render_rom_row(categoryID, launcherID, key, rl[key], rom_is_in_favourites)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Show raw information about ROMs
    # Idea taken from script.logviewer
    #
    def _command_view_ROM(self, categoryID, launcherID, romID):
        # --- Read ROMs ---
        regular_launcher = True
        if categoryID == VCATEGORY_FAVOURITES_ID:
            log_info('_command_view_ROM() Viewing ROM in Favourites...')
            roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
            rom = roms[romID]
            window_title = 'Favourite ROM data'
            regular_launcher = False
            vlauncher_label = 'Favourite'

        elif categoryID == VCATEGORY_TITLE_ID:
            log_info('_command_view_ROM() Viewing ROM in Virtual Launcher Title...')
            hashed_db_filename = os.path.join(VIRTUAL_CAT_TITLE_DIR, launcherID + '.json')
            if not os.path.isfile(hashed_db_filename):
                log_error('_command_view_ROM() Cannot find file "{0}"'.format(hashed_db_filename))
                kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
                return
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_TITLE_DIR, launcherID)
            rom = roms[romID]
            window_title = 'Virtual Launcher Title ROM data'
            regular_launcher = False
            vlauncher_label = 'Virtual Launcher Title'

        elif categoryID == VCATEGORY_YEARS_ID:
            log_info('_command_view_ROM() Viewing ROM in Virtual Launcher Year...')
            hashed_db_filename = os.path.join(VIRTUAL_CAT_YEARS_DIR, launcherID + '.json')
            if not os.path.isfile(hashed_db_filename):
                log_error('_command_view_ROM() Cannot find file "{0}"'.format(hashed_db_filename))
                kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
                return
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_YEARS_DIR, launcherID)
            rom = roms[romID]
            window_title = 'Virtual Launcher Year ROM data'
            regular_launcher = False
            vlauncher_label = 'Virtual Launcher Year'

        elif categoryID == VCATEGORY_GENRE_ID:
            log_info('_command_view_ROM() Viewing ROM in Virtual Launcher Genre...')
            hashed_db_filename = os.path.join(VIRTUAL_CAT_GENRE_DIR, launcherID + '.json')
            if not os.path.isfile(hashed_db_filename):
                log_error('_command_view_ROM() Cannot find file "{0}"'.format(hashed_db_filename))
                kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
                return
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_GENRE_DIR, launcherID)
            rom = roms[romID]
            window_title = 'Virtual Launcher Genre ROM data'
            regular_launcher = False
            vlauncher_label = 'Virtual Launcher Genre'

        elif categoryID == VCATEGORY_STUDIO_ID:
            log_info('_command_view_ROM() Viewing ROM in Virtual Launcher Studio...')
            hashed_db_filename = os.path.join(VIRTUAL_CAT_STUDIO_DIR, launcherID + '.json')
            if not os.path.isfile(hashed_db_filename):
                log_error('_command_view_ROM() Cannot find file "{0}"'.format(hashed_db_filename))
                kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
                return
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_STUDIO_DIR, launcherID)
            rom = roms[romID]
            window_title = 'Virtual Launcher Studio ROM data'
            regular_launcher = False
            vlauncher_label = 'Virtual Launcher Studio'

        # --- ROM in Collection ---
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            log_info('_command_view_ROM() Viewing ROM in Collection...')
            (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
            collection = collections[launcherID]
            collection_rom_list = fs_load_Collection_ROMs_JSON(COLLECTIONS_DIR, collection['roms_base_noext'])
            # >> Locate ROM in Collection
            rom = {}
            for rom_temp in collection_rom_list:
                if romID == rom_temp['id']:
                    rom = rom_temp
                    break
            window_title = '{0} Collection ROM data'.format(collection['name'])
            regular_launcher = False
            vlauncher_label = 'Collection'

        # --- ROM in regular launcher ---
        else:
            log_info('_command_view_ROM() Viewing ROM in Launcher...')
            # Check launcher is OK
            if launcherID not in self.launchers:
                kodi_dialog_OK('launcherID not found in self.launchers')
                return
            category = self.categories[categoryID]
            launcher = self.launchers[launcherID]
            roms = fs_load_ROMs(ROMS_DIR, launcher['roms_base_noext'])
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
            info_text += self._misc_print_string_Category(category)
        else:
            info_text += '\n[COLOR orange]{0} ROM additional information[/COLOR]\n'.format(vlauncher_label)
            info_text += self._misc_print_string_ROM_additional(rom)

        # --- Show information window ---
        try:
            xbmc.executebuiltin('ActivateWindow(10147)')
            window = xbmcgui.Window(10147)
            xbmc.sleep(100)
            window.getControl(1).setLabel(window_title)
            window.getControl(5).setText(info_text)
        except:
            log_error('_command_view_ROM() Exception rendering INFO window')

    #
    # Only called for regular launchers
    #
    def _command_view_Launcher(self, categoryID, launcherID):
        # --- Grab info ---
        window_title = 'Launcher data'
        category = self.categories[categoryID]
        launcher = self.launchers[launcherID]

        # --- Make info string ---
        info_text  = '\n[COLOR orange]Launcher information[/COLOR]\n'
        info_text += self._misc_print_string_Launcher(launcher)
        info_text += '\n[COLOR orange]Category information[/COLOR]\n'
        info_text += self._misc_print_string_Category(category)

        # --- Show information window ---
        try:
            xbmc.executebuiltin('ActivateWindow(10147)')
            window = xbmcgui.Window(10147)
            xbmc.sleep(100)
            window.getControl(1).setLabel(window_title)
            window.getControl(5).setText(info_text)
        except:
            log_error('_command_view_Launcher() Exception rendering INFO window')

    #
    # Only called for regular categories
    #
    def _command_view_Category(self, categoryID):
        # --- Grab info ---
        window_title = 'Category data'
        category = self.categories[categoryID]

        # --- Make info string ---
        info_text  = '\n[COLOR orange]Category information[/COLOR]\n'
        info_text += self._misc_print_string_Category(category)

        # --- Show information window ---
        try:
            xbmc.executebuiltin('ActivateWindow(10147)')
            window = xbmcgui.Window(10147)
            xbmc.sleep(100)
            window.getControl(1).setLabel(window_title)
            window.getControl(5).setText(info_text)
        except:
            log_error('_command_view_Category() Exception rendering INFO window')

    def _misc_print_string_ROM(self, rom):
        info_text  = ''
        info_text += "[COLOR violet]id[/COLOR]: '{0}'\n".format(rom['id'])
        info_text += "[COLOR violet]m_name[/COLOR]: '{0}'\n".format(rom['m_name'])
        info_text += "[COLOR violet]m_year[/COLOR]: '{0}'\n".format(rom['m_year'])
        info_text += "[COLOR violet]m_genre[/COLOR]: '{0}'\n".format(rom['m_genre'])
        info_text += "[COLOR violet]m_plot[/COLOR]: '{0}'\n".format(rom['m_plot'])
        info_text += "[COLOR violet]m_studio[/COLOR]: '{0}'\n".format(rom['m_studio'])
        info_text += "[COLOR violet]m_rating[/COLOR]: '{0}'\n".format(rom['m_rating'])

        info_text += "[COLOR violet]filename[/COLOR]: '{0}'\n".format(rom['filename'])
        info_text += "[COLOR violet]altapp[/COLOR]: '{0}'\n".format(rom['altapp'])
        info_text += "[COLOR violet]altarg[/COLOR]: '{0}'\n".format(rom['altarg'])
        info_text += "[COLOR skyblue]finished[/COLOR]: {0}\n".format(rom['finished'])
        info_text += "[COLOR violet]nointro_status[/COLOR]: '{0}'\n".format(rom['nointro_status'])

        info_text += "[COLOR violet]s_title[/COLOR]: '{0}'\n".format(rom['s_title'])
        info_text += "[COLOR violet]s_snap[/COLOR]: '{0}'\n".format(rom['s_snap'])
        info_text += "[COLOR violet]s_fanart[/COLOR]: '{0}'\n".format(rom['s_fanart'])
        info_text += "[COLOR violet]s_banner[/COLOR]: '{0}'\n".format(rom['s_banner'])
        info_text += "[COLOR violet]s_clearlogo[/COLOR]: '{0}'\n".format(rom['s_clearlogo'])
        info_text += "[COLOR violet]s_boxfront[/COLOR]: '{0}'\n".format(rom['s_boxfront'])
        info_text += "[COLOR violet]s_boxback[/COLOR]: '{0}'\n".format(rom['s_boxback'])
        info_text += "[COLOR violet]s_cartridge[/COLOR]: '{0}'\n".format(rom['s_cartridge'])
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
        info_text += "[COLOR violet]rompath[/COLOR]: '{0}'\n".format(rom['rompath'])
        info_text += "[COLOR violet]romext[/COLOR]: '{0}'\n".format(rom['romext'])
        info_text += "[COLOR skyblue]minimize[/COLOR]: {0}\n".format(rom['minimize'])
        info_text += "[COLOR violet]fav_status[/COLOR]: '{0}'\n".format(rom['fav_status'])
        info_text += "[COLOR violet]roms_default_thumb[/COLOR]: '{0}'\n".format(rom['roms_default_thumb'])
        info_text += "[COLOR violet]roms_default_fanart[/COLOR]: '{0}'\n".format(rom['roms_default_fanart'])
        info_text += "[COLOR violet]roms_default_banner[/COLOR]: '{0}'\n".format(rom['roms_default_banner'])
        info_text += "[COLOR violet]roms_default_poster[/COLOR]: '{0}'\n".format(rom['roms_default_poster'])
        info_text += "[COLOR violet]roms_default_clearlogo[/COLOR]: '{0}'\n".format(rom['roms_default_clearlogo'])

        return info_text

    def _misc_print_string_Launcher(self, launcher):
        info_text  = ''
        info_text += "[COLOR violet]id[/COLOR]: '{0}'\n".format(launcher['id'])
        info_text += "[COLOR violet]m_name[/COLOR]: '{0}'\n".format(launcher['m_name'])
        info_text += "[COLOR violet]m_year[/COLOR]: '{0}'\n".format(launcher['m_year'])
        info_text += "[COLOR violet]m_genre[/COLOR]: '{0}'\n".format(launcher['m_genre'])
        info_text += "[COLOR violet]m_studio[/COLOR]: '{0}'\n".format(launcher['m_studio'])
        info_text += "[COLOR violet]m_rating[/COLOR]: '{0}'\n".format(launcher['m_rating'])
        info_text += "[COLOR violet]m_plot[/COLOR]: '{0}'\n".format(launcher['m_plot'])

        info_text += "[COLOR violet]platform[/COLOR]: '{0}'\n".format(launcher['platform'])
        info_text += "[COLOR violet]categoryID[/COLOR]: '{0}'\n".format(launcher['categoryID'])
        info_text += "[COLOR violet]application[/COLOR]: '{0}'\n".format(launcher['application'])
        info_text += "[COLOR violet]args[/COLOR]: '{0}'\n".format(launcher['args'])
        info_text += "[COLOR violet]rompath[/COLOR]: '{0}'\n".format(launcher['rompath'])
        info_text += "[COLOR violet]romext[/COLOR]: '{0}'\n".format(launcher['romext'])
        info_text += "[COLOR skyblue]finished[/COLOR]: {0}\n".format(launcher['finished'])
        info_text += "[COLOR skyblue]minimize[/COLOR]: {0}\n".format(launcher['minimize'])
        info_text += "[COLOR violet]roms_base_noext[/COLOR]: '{0}'\n".format(launcher['roms_base_noext'])
        info_text += "[COLOR violet]nointro_xml_file[/COLOR]: '{0}'\n".format(launcher['nointro_xml_file'])
        info_text += "[COLOR skyblue]timestamp_launcher[/COLOR]: {0}\n".format(launcher['timestamp_launcher'])
        info_text += "[COLOR skyblue]timestamp_report[/COLOR]: {0}\n".format(launcher['timestamp_report'])

        info_text += "[COLOR violet]default_thumb[/COLOR]: '{0}'\n".format(launcher['default_thumb'])
        info_text += "[COLOR violet]default_fanart[/COLOR]: '{0}'\n".format(launcher['default_fanart'])
        info_text += "[COLOR violet]default_banner[/COLOR]: '{0}'\n".format(launcher['default_banner'])
        info_text += "[COLOR violet]default_poster[/COLOR]: '{0}'\n".format(launcher['default_poster'])
        info_text += "[COLOR violet]default_clearlogo[/COLOR]: '{0}'\n".format(launcher['default_clearlogo'])
        info_text += "[COLOR violet]roms_default_thumb[/COLOR]: '{0}'\n".format(launcher['roms_default_thumb'])
        info_text += "[COLOR violet]roms_default_fanart[/COLOR]: '{0}'\n".format(launcher['roms_default_fanart'])
        info_text += "[COLOR violet]roms_default_banner[/COLOR]: '{0}'\n".format(launcher['roms_default_banner'])
        info_text += "[COLOR violet]roms_default_poster[/COLOR]: '{0}'\n".format(launcher['roms_default_poster'])
        info_text += "[COLOR violet]roms_default_clearlogo[/COLOR]: '{0}'\n".format(launcher['roms_default_clearlogo'])

        info_text += "[COLOR violet]s_thumb[/COLOR]: '{0}'\n".format(launcher['s_thumb'])
        info_text += "[COLOR violet]s_fanart[/COLOR]: '{0}'\n".format(launcher['s_fanart'])
        info_text += "[COLOR violet]s_banner[/COLOR]: '{0}'\n".format(launcher['s_banner'])
        info_text += "[COLOR violet]s_flyer[/COLOR]: '{0}'\n".format(launcher['s_flyer'])
        info_text += "[COLOR violet]s_trailer[/COLOR]: '{0}'\n".format(launcher['s_trailer'])

        info_text += "[COLOR violet]path_title[/COLOR]: '{0}'\n".format(launcher['path_title'])
        info_text += "[COLOR violet]path_snap[/COLOR]: '{0}'\n".format(launcher['path_snap'])
        info_text += "[COLOR violet]path_fanart[/COLOR]: '{0}'\n".format(launcher['path_fanart'])
        info_text += "[COLOR violet]path_banner[/COLOR]: '{0}'\n".format(launcher['path_banner'])
        info_text += "[COLOR violet]path_clearlogo[/COLOR]: '{0}'\n".format(launcher['path_clearlogo'])
        info_text += "[COLOR violet]path_boxfront[/COLOR]: '{0}'\n".format(launcher['path_boxfront'])
        info_text += "[COLOR violet]path_boxback[/COLOR]: '{0}'\n".format(launcher['path_boxback'])
        info_text += "[COLOR violet]path_cartridge[/COLOR]: '{0}'\n".format(launcher['path_cartridge'])
        info_text += "[COLOR violet]path_flyer[/COLOR]: '{0}'\n".format(launcher['path_flyer'])
        info_text += "[COLOR violet]path_map[/COLOR]: '{0}'\n".format(launcher['path_map'])
        info_text += "[COLOR violet]path_manual[/COLOR]: '{0}'\n".format(launcher['path_manual'])
        info_text += "[COLOR violet]path_trailer[/COLOR]: '{0}'\n".format(launcher['path_trailer'])

        return info_text

    def _misc_print_string_Category(self, category):
        info_text  = ''
        info_text += "[COLOR violet]id[/COLOR]: '{0}'\n".format(category['id'])
        info_text += "[COLOR violet]m_name[/COLOR]: '{0}'\n".format(category['m_name'])
        info_text += "[COLOR violet]m_genre[/COLOR]: '{0}'\n".format(category['m_genre'])
        info_text += "[COLOR violet]m_plot[/COLOR]: '{0}'\n".format(category['m_plot'])
        info_text += "[COLOR violet]m_rating[/COLOR]: '{0}'\n".format(category['m_rating'])
        info_text += "[COLOR skyblue]finished[/COLOR]: {0}\n".format(category['finished'])        
        info_text += "[COLOR violet]default_thumb[/COLOR]: '{0}'\n".format(category['default_thumb'])
        info_text += "[COLOR violet]default_fanart[/COLOR]: '{0}'\n".format(category['default_fanart'])
        info_text += "[COLOR violet]default_banner[/COLOR]: '{0}'\n".format(category['default_banner'])
        info_text += "[COLOR violet]default_poster[/COLOR]: '{0}'\n".format(category['default_poster'])
        info_text += "[COLOR violet]default_clearlogo[/COLOR]: '{0}'\n".format(category['default_clearlogo'])
        info_text += "[COLOR violet]s_thumb[/COLOR]: '{0}'\n".format(category['s_thumb'])
        info_text += "[COLOR violet]s_fanart[/COLOR]: '{0}'\n".format(category['s_fanart'])
        info_text += "[COLOR violet]s_banner[/COLOR]: '{0}'\n".format(category['s_banner'])
        info_text += "[COLOR violet]s_flyer[/COLOR]: '{0}'\n".format(category['s_flyer'])
        info_text += "[COLOR violet]s_trailer[/COLOR]: '{0}'\n".format(category['s_trailer'])

        return info_text

    def _command_view_Launcher_Report(self, categoryID, launcherID):
        # --- Standalone launchers do not have reports! ---
        category = self.categories[categoryID]
        launcher = self.launchers[launcherID]
        if not launcher['rompath']:
            kodi_notify_warn('Cannot create report for standalone launcher.')
            return

        # --- Get report filename ---
        roms_base_noext = fs_get_ROMs_basename(category['m_name'], launcher['m_name'], launcherID)
        report_file_name = os.path.join(REPORTS_DIR, roms_base_noext + '.txt')
        window_title = 'Launcher {0} Report'.format(launcher['m_name'])
        log_verb('_command_view_Launcher_Report() Dir  "{0}"'.format(REPORTS_DIR))
        log_verb('_command_view_Launcher_Report() File "{0}"'.format(roms_base_noext + '.txt'))

        # --- If no ROMs in launcher do nothing ---
        launcher = self.launchers[launcherID]
        roms = fs_load_ROMs(ROMS_DIR, launcher['roms_base_noext'])
        if not roms:
            kodi_notify_warn('No ROMs in launcher. Report not created.')
            return

        # --- If report doesn't exists create it automatically ---
        if not os.path.isfile(report_file_name):
            kodi_dialog_OK('Report file not found. Will be generated now.')
            self._roms_create_launcher_report(categoryID, launcherID, roms)
            xbmc.sleep(250)
            # >> Update report timestamp
            self.launchers[launcherID]['timestamp_report'] = time.time()
            # >> Save Categories/Launchers
            # >> DO NOT update the timestamp of categories/launchers of report will always be obsolete!!!
            # >> Keep same timestamp as before.
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers, self.update_timestamp)
        
        # --- If report timestamp is older than launchers last modification, recreate it ---
        if self.launchers[launcherID]['timestamp_report'] <= self.launchers[launcherID]['timestamp_launcher']:
            kodi_dialog_OK('Report is outdated. Will be regenerated now.')
            self._roms_create_launcher_report(categoryID, launcherID, roms)
            xbmc.sleep(250)
            self.launchers[launcherID]['timestamp_report'] = time.time()
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers, self.update_timestamp)

        # --- Read report file ---
        try:
            file = open(report_file_name, 'r')
            info_text = file.read()
            file.close()
        except:
            log_error('_command_view_Launcher_Report() Exception reading report TXT file')

        # --- Eye candy ---
        info_text = info_text.replace('<Launcher Information>', '[COLOR orange]<Launcher Information>[/COLOR]')
        info_text = info_text.replace('<Metadata Information>', '[COLOR orange]<Metadata Information>[/COLOR]')
        info_text = info_text.replace('<Artwork Information>', '[COLOR orange]<Artwork Information>[/COLOR]')

        # --- Show information window ---
        try:
            xbmc.executebuiltin('ActivateWindow(10147)')
            window = xbmcgui.Window(10147)
            xbmc.sleep(100)
            window.getControl(1).setLabel(window_title)
            window.getControl(5).setText(info_text)
        except:
            log_error('_command_view_Launcher_Report() Exception rendering INFO window')

    #
    # Updated all virtual categories DB
    #
    def _command_update_virtual_category_db_all(self):
        # --- Sanity checks ---
        if len(self.launchers) == 0:
            kodi_dialog_OK('You do not have any ROM Launcher. Add a ROM Launcher first.')
            return

        # --- Update all virtual launchers ---
        self._command_update_virtual_category_db(VCATEGORY_TITLE_ID)
        self._command_update_virtual_category_db(VCATEGORY_YEARS_ID)
        self._command_update_virtual_category_db(VCATEGORY_GENRE_ID)
        self._command_update_virtual_category_db(VCATEGORY_STUDIO_ID)
        kodi_notify('All virtual categories updated')

    #
    # Makes a virtual category database
    #
    def _command_update_virtual_category_db(self, virtual_categoryID):
        # --- Customise function depending on virtual category ---
        if virtual_categoryID == VCATEGORY_TITLE_ID:
            log_info('_command_update_virtual_category_db() Updating Titles DB')
            vcategory_db_directory = VIRTUAL_CAT_TITLE_DIR
            vcategory_db_filename  = VCAT_TITLE_FILE_PATH
            vcategory_field_name   = 'm_name'
            vcategory_name         = 'Name'
        elif virtual_categoryID == VCATEGORY_YEARS_ID:
            log_info('_command_update_virtual_category_db() Updating Years DB')
            vcategory_db_directory = VIRTUAL_CAT_YEARS_DIR
            vcategory_db_filename  = VCAT_YEARS_FILE_PATH
            vcategory_field_name   = 'm_year'
            vcategory_name         = 'Year'
        elif virtual_categoryID == VCATEGORY_GENRE_ID:
            log_info('_command_update_virtual_category_db() Updating Genres DB')
            vcategory_db_directory = VIRTUAL_CAT_GENRE_DIR
            vcategory_db_filename  = VCAT_GENRE_FILE_PATH
            vcategory_field_name   = 'm_genre'
            vcategory_name         = 'Genre'
        elif virtual_categoryID == VCATEGORY_STUDIO_ID:
            log_info('_command_update_virtual_category_db() Updating Studios DB')
            vcategory_db_directory = VIRTUAL_CAT_STUDIO_DIR
            vcategory_db_filename  = VCAT_STUDIO_FILE_PATH
            vcategory_field_name   = 'm_studio'
            vcategory_name         = 'Studio'
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
        for the_file in os.listdir(vcategory_db_directory):
            filename, file_extension = os.path.splitext(the_file)
            if file_extension.lower() != '.xml' and file_extension.lower() != '.json':
                # >> There should be only XMLs or JSON in this directory
                log_error('_command_update_virtual_category_db() Found non XML/JSON file "{0}"'.format(the_file))
                log_error('_command_update_virtual_category_db() Skipping it from deletion')
                continue
            file_path = os.path.join(vcategory_db_directory, the_file)
            log_verb('_command_update_virtual_category_db() Deleting "{0}"'.format(file_path))
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                log_error('_command_update_virtual_category_db() Excepcion deleting hashed DB XMLs')
                log_error('_command_update_virtual_category_db() {0}'.format(e))
                return

        # --- Progress dialog ---
        # >> Important to avoid multithread execution of the plugin and race conditions
        pDialog = xbmcgui.DialogProgress()
        pDialog_canceled = False

        # --- Make a big dictionary will all the ROMs ---
        # TODO It would be nice to have a progress dialog here...
        log_verb('_command_update_virtual_category_db() Creating list of all ROMs in all Launchers')
        all_roms = {}
        num_launchers = len(self.launchers)
        i = 0
        pDialog.create('Advanced Emulator Launcher', 'Making ROM list...')
        for launcher_id in self.launchers:
            # >> Update dialog
            pDialog.update(i * 100 / num_launchers)
            i += 1

            # >> Get current launcher
            launcher = self.launchers[launcher_id]

            # >> If launcher is standalone skip
            if launcher['rompath'] == '': continue

            # >> Open launcher and add roms to the big list
            roms = fs_load_ROMs(ROMS_DIR, launcher['roms_base_noext'])

            # >> Add additional fields to ROM to make a Favourites ROM
            # >> Virtual categories/launchers are like Favourite ROMs that cannot be edited.
            # >> NOTE roms is updated by assigment, dictionaries are mutable
            fav_roms = {}
            for rom_id in roms:
                fav_rom = fs_get_Favourite_from_ROM(roms[rom_id], launcher)
                fav_roms[rom_id] = fav_rom

            # >> Update dictionary
            all_roms.update(fav_roms)
        pDialog.update(i * 100 / num_launchers)
        pDialog.close()

        # --- Create a dictionary that with key the virtual category and value a dictionay of roms 
        #     belonging to that virtual category ---
        # TODO It would be nice to have a progress dialog here...
        log_verb('_command_update_virtual_category_db() Creating hashed database')
        virtual_launchers = {}
        for rom_id in all_roms:
            rom = all_roms[rom_id]
            if virtual_categoryID == VCATEGORY_TITLE_ID:
                vcategory_key = rom['m_name'][0].upper()
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
        pDialog.create('Advanced Emulator Launcher', 'Writing {0} VLaunchers hashed database...'.format(vcategory_name))
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
        pDialog.update(i * 100 / num_vlaunchers)
        pDialog.close()

        # --- Write virtual launchers XML file ---
        # >> This file is small, no progress dialog
        log_verb('_command_update_virtual_category_db() Writing virtual category XML index')
        fs_write_VCategory_XML(vcategory_db_filename, vcategory_launchers)

    #
    # Import legacy Advanced Launcher launchers.xml
    #
    def _command_import_legacy_AL(self):
        # >> Confirm action with user
        ret = kodi_dialog_yesno('Are you sure you want to import Advanced Launcher launchers.xml?')
        if not ret: return
    
        kodi_notify('Importing AL launchers.xml...')
        AL_DATA_DIR = xbmc.translatePath(os.path.join('special://profile/addon_data',
                                                      'plugin.program.advanced.launcher')).decode('utf-8')
        LAUNCHERS_FILE_PATH = os.path.join(AL_DATA_DIR, 'launchers.xml').decode('utf-8')
        FIXED_LAUNCHERS_FILE_PATH = os.path.join(PLUGIN_DATA_DIR, 'fixed_launchers.xml').decode('utf-8')

        # >> Check that launchers.xml exist
        if not os.path.isfile(LAUNCHERS_FILE_PATH):
            log_error("_command_import_legacy_AL() Cannot find '{0}'".format(LAUNCHERS_FILE_PATH))
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
        for AL_category_key in AL_categories:
            num_categories += 1
            AL_category = AL_categories[AL_category_key]
            category = fs_new_category()
            # >> Do translation
            category['id']       = default_SID if AL_category['id'] == 'default' else AL_category['id']
            category['m_name']   = AL_category['name']
            category['m_genre']  = AL_category['genre']
            category['m_plot']   = AL_category['plot']
            category['s_thumb']  = AL_category['thumb']
            category['s_fanart'] = AL_category['fanart']
            category['finished'] = False if AL_category['finished'] == 'false' else True
            self.categories[category['id']] = category

        for AL_launcher_key in AL_launchers:
            num_launchers += 1
            AL_launcher = AL_launchers[AL_launcher_key]
            launcher = fs_new_launcher()
            # >> Do translation
            launcher['id']           = AL_launcher['id']
            launcher['m_name']       = AL_launcher['name']
            launcher['m_year']       = AL_launcher['release']
            launcher['m_genre']      = AL_launcher['genre']
            launcher['m_studio']     = AL_launcher['studio']
            launcher['m_plot']       = AL_launcher['plot']
            # >> 'gamesys' ignored, set to unknown to avoid trouble with scrapers
            # launcher['platform']    = AL_launcher['gamesys']
            launcher['platform']     = 'Unknown'            
            launcher['categoryID']   = default_SID if AL_launcher['category'] == 'default' else AL_launcher['category']
            launcher['application']  = AL_launcher['application']
            launcher['args']         = AL_launcher['args']
            launcher['rompath']      = AL_launcher['rompath']
            launcher['romext']       = AL_launcher['romext']
            launcher['finished']     = False if AL_launcher['finished'] == 'false' else True
            launcher['minimize']     = False if AL_launcher['minimize'] == 'false' else True
            # >> 'lnk' ignored, always active in AEL
            launcher['s_thumb']      = AL_launcher['thumb']
            launcher['s_fanart']     = AL_launcher['fanart']
            launcher['path_title']   = AL_launcher['thumbpath']
            launcher['path_fanart']  = AL_launcher['fanartpath']
            launcher['path_trailer'] = AL_launcher['trailerpath']

            # --- Import ROMs if ROMs launcher ---
            AL_roms = AL_launcher['roms']
            if AL_roms:
                roms = {}
                category_name = self.categories[launcher['categoryID']]['m_name']
                roms_base_noext = fs_get_ROMs_basename(category_name, launcher['m_name'], launcher['id'])
                launcher['roms_base_noext'] = roms_base_noext
                for AL_rom_ID in AL_roms:
                    num_ROMs += 1
                    AL_rom = AL_roms[AL_rom_ID]
                    rom = fs_new_rom()
                    # >> Do translation
                    rom['id']        = AL_rom['id']
                    rom['m_name']    = AL_rom['name']
                    rom['m_year']    = AL_rom['release']
                    rom['m_genre']   = AL_rom['genre']
                    rom['m_studio']  = AL_rom['studio']
                    rom['m_plot']    = AL_rom['plot']
                    rom['filename']  = AL_rom['filename']
                    rom['altapp']    = AL_rom['altapp']
                    rom['altarg']    = AL_rom['altarg']
                    rom['finished']  = False if AL_rom['finished'] == 'false' else True
                    rom['s_title']   = AL_rom['thumb']
                    rom['s_fanart']  = AL_rom['fanart']
                    rom['s_trailer'] = AL_rom['trailer']

                    # >> Add to ROM dictionary
                    roms[rom['id']] = rom

                # >> Save ROMs XML
                fs_write_ROMs(ROMS_DIR, roms_base_noext, roms, launcher)
            else:
                launcher['roms_xml_file'] = ''
            # >> Add launcher to AEL launchers
            launcher['timestamp_launcher'] = time.time()
            self.launchers[launcher['id']] = launcher

        # >> Save AEL categories.xml
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

        # --- Show some information to user ---
        kodi_dialog_OK('Imported {0} Category/s, {1} Launcher/s '.format(num_categories, num_launchers) +
                       'and {0} ROM/s.'.format(num_ROMs))
        kodi_refresh_container()

    #
    # Launchs a standalone application.
    #
    def _command_run_standalone_launcher(self, categoryID, launcherID):
        # --- Check launcher is OK ---
        if launcherID not in self.launchers:
            kodi_dialog_OK('launcherID not found in self.launchers')
            return
        launcher = self.launchers[launcherID]
        minimize_flag = launcher['minimize']

        # --- Execute Kodi built-in function under certain conditions ---
        apppath = os.path.dirname(launcher['application'])
        if os.path.basename(launcher['application']).lower().replace('.exe' , '') == 'xbmc'  or \
           'xbmc-fav-' in launcher['application'] or 'xbmc-sea-' in launcher['application']:
            xbmc.executebuiltin('XBMC.%s' % launcher['args'])
            return

        # ~~~~~ External application ~~~~~
        application = launcher['application']
        app_basename = os.path.basename(launcher['application'])
        arguments = launcher['args'].replace('%apppath%' , apppath).replace('%APPPATH%' , apppath)
        app_ext = launcher['application'].split('.')[-1]
        log_info('_run_standalone_launcher() categoryID   = {0}'.format(categoryID))
        log_info('_run_standalone_launcher() launcherID   = {0}'.format(launcherID))
        log_info('_run_standalone_launcher() application  = "{0}"'.format(application))
        log_info('_run_standalone_launcher() apppath      = "{0}"'.format(apppath))
        log_info('_run_standalone_launcher() app_basename = "{0}"'.format(app_basename))
        log_info('_run_standalone_launcher() arguments    = "{0}"'.format(arguments))
        log_info('_run_standalone_launcher() app_ext      = "{0}"'.format(app_ext))

        # --- Check for errors and abort if errors found ---
        if not os.path.exists(application):
            log_error('Launching app not found "{0}"'.format(application))
            kodi_notify_warn('App {0} not found.'.format(application))
            return

        # ~~~~~ Execute external application ~~~~~
        kodi_was_playing_flag = self._run_before_execution(app_basename, minimize_flag)
        self._run_process(application, arguments, apppath, app_ext)
        self._run_after_execution(kodi_was_playing_flag, minimize_flag)

    #
    # Launchs a ROM
    #
    def _command_run_rom(self, categoryID, launcherID, romID):
        # --- ROM in Favourites ---
        if categoryID == VCATEGORY_FAVOURITES_ID and launcherID == VLAUNCHER_FAVOURITES_ID:
            log_info('_command_run_rom() Launching ROM in Favourites...')
            roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
            rom  = roms[romID]
            application   = rom['application'] if rom['altapp'] == '' else rom['altapp']
            arguments     = rom['args'] if rom['altarg'] == '' else rom['altarg']
            minimize_flag = rom['minimize']
            romext        = rom['romext']
        # --- ROM in Collection ---
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            log_info('_command_run_rom() Launching ROM in Collection...')
            (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
            collection = collections[launcherID]
            collection_rom_list = fs_load_Collection_ROMs_JSON(COLLECTIONS_DIR, collection['roms_base_noext'])
            current_ROM_position = -1;
            for idx, rom in enumerate(collection_rom_list):
                if romID == rom['id']:
                    current_ROM_position = idx
                    break
            if current_ROM_position < 0:
                kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
                return
            application   = rom['application'] if rom['altapp'] == '' else rom['altapp']
            arguments     = rom['args'] if rom['altarg'] == '' else rom['altarg']
            minimize_flag = rom['minimize']
            romext        = rom['romext']
        # --- ROM in Virtual Launcher ---
        elif categoryID == VCATEGORY_TITLE_ID:
            log_info('_command_run_rom() Launching ROM in Title Virtual Launcher...')
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_TITLE_DIR, launcherID)
            rom  = roms[romID]
            application   = rom['application'] if rom['altapp'] == '' else rom['altapp']
            arguments     = rom['args'] if rom['altarg'] == '' else rom['altarg']
            minimize_flag = rom['minimize']
            romext        = rom['romext']
        elif categoryID == VCATEGORY_YEARS_ID:
            log_info('_command_run_rom() Launching ROM in Year Virtual Launcher...')
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_YEARS_DIR, launcherID)
            rom  = roms[romID]
            application   = rom['application'] if rom['altapp'] == '' else rom['altapp']
            arguments     = rom['args'] if rom['altarg'] == '' else rom['altarg']
            minimize_flag = rom['minimize']
            romext        = rom['romext']
        elif categoryID == VCATEGORY_GENRE_ID:
            log_info('_command_run_rom() Launching ROM in Gender Virtual Launcher...')
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_GENRE_DIR, launcherID)
            rom  = roms[romID]
            application   = rom['application'] if rom['altapp'] == '' else rom['altapp']
            arguments     = rom['args'] if rom['altarg'] == '' else rom['altarg']
            minimize_flag = rom['minimize']
            romext        = rom['romext']
        elif categoryID == VCATEGORY_STUDIO_ID:
            log_info('_command_run_rom() Launching ROM in Studio Virtual Launcher...')
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_STUDIO_DIR, launcherID)
            rom  = roms[romID]
            application   = rom['application'] if rom['altapp'] == '' else rom['altapp']
            arguments     = rom['args'] if rom['altarg'] == '' else rom['altarg']
            minimize_flag = rom['minimize']
            romext        = rom['romext']
        # --- ROM in launcher ---
        else:
            log_info('_command_run_rom() Launching ROM in Launcher...')
            # --- Check launcher is OK and load ROMs ---
            if launcherID not in self.launchers:
                kodi_dialog_OK('launcherID not found in self.launchers')
                return
            launcher = self.launchers[launcherID]
            roms = fs_load_ROMs(ROMS_DIR, launcher['roms_base_noext'])
            # --- Check ROM is in XML data just read ---
            if romID not in roms:
                kodi_dialog_OK('romID not in roms dictionary')
                return
            rom = roms[romID]
            application   = launcher['application'] if rom['altapp'] == '' else rom['altapp']
            arguments     = launcher['args'] if rom['altarg'] == '' else rom['altarg']
            minimize_flag = launcher['minimize']
            romext        = launcher['romext']

        # ~~~~~ Launch ROM ~~~~~
        apppath     = os.path.dirname(application)
        ROM         = misc_split_path(rom['filename'])
        romfile     = ROM.path
        rompath     = ROM.dirname
        rombasename = ROM.base
        log_info('_command_run_rom() categoryID  = {0}'.format(categoryID))
        log_info('_command_run_rom() launcherID  = {0}'.format(launcherID))
        log_info('_command_run_rom() romID       = {0}'.format(romID))
        log_info('_command_run_rom() application = "{0}"'.format(application))
        log_info('_command_run_rom() apppath     = "{0}"'.format(apppath))
        log_info('_command_run_rom() romfile     = "{0}"'.format(romfile))
        log_info('_command_run_rom() rompath     = "{0}"'.format(rompath))
        log_info('_command_run_rom() rombasename = "{0}"'.format(rombasename))
        log_info('_command_run_rom() romext      = "{0}"'.format(romext))

        # --- Check for errors and abort if found ---
        if not os.path.exists(application):
            log_error('Launching app not found "{0}"'.format(application))
            kodi_notify_warn('Launching app not found {0}'.format(application))
            return

        if not os.path.exists(romfile):
            log_error('ROM not found "{0}"'.format(romfile))
            kodi_notify_warn('ROM not found {0}'.format(romfile))
            return

        # --- Escape quotes and double quotes in romfile ---
        # >> This maybe useful to Android users with complex command line arguments
        if self.settings['escape_romfile']:
            log_info("_command_run_rom() Escaping romfile ' and \"")
            romfile = romfile.replace("'", "\\'")
            romfile = romfile.replace("\"", "\\\"")

        # ~~~~ Argument substitution ~~~~~
        arguments = arguments.replace('%rom%',         romfile).replace('%ROM%',             romfile)
        arguments = arguments.replace('%rombasename%', rombasename).replace('%ROMBASENAME%', rombasename)
        arguments = arguments.replace('%apppath%',     apppath).replace('%APPPATH%',         apppath)
        arguments = arguments.replace('%rompath%',     rompath).replace('%ROMPATH%',         rompath)
        arguments = arguments.replace('%romtitle%',    rom['m_name']).replace('%ROMTITLE%',  rom['m_name'])
        log_info('_command_run_rom() arguments   = "{0}"'.format(arguments))

        # Execute Kodi internal function (RetroPlayer?)
        if os.path.basename(application).lower().replace('.exe', '') == 'xbmc':
            xbmc.executebuiltin('XBMC.' + arguments)
            return

        # ~~~~~ Execute external application ~~~~~
        kodi_was_playing_flag = self._run_before_execution(rombasename, minimize_flag)
        self._run_process(application, arguments, apppath, romext)
        self._run_after_execution(kodi_was_playing_flag, minimize_flag)

    #
    # Launchs a process
    # For standalone launchers rom_romext is the extension of the application (only used in Windoze)
    #
    def _run_process(self, application, arguments, apppath, romext):
        # >> Determine platform and launch application
        # >> See http://stackoverflow.com/questions/446209/possible-values-from-sys-platform

        # >> Windoze
        if sys.platform == 'win32':
            if romext == 'lnk':
                os.system('start "" "{0}"'.format(arguments).encode('utf-8'))
            else:
                info = None
                app_ext = application.split('.')[-1]
                log_debug('_run_process() (Windows) app_ext = "{0}"'.format(app_ext))
                log_debug('_run_process() (Windows) apppath = "{0}"'.format(apppath))
                # >> cwd = apppath.encode('utf-8') fails if application path has Unicode on Windows
                # >> Workaraound is to use cwd = apppath.encode(sys.getfilesystemencoding()) --> DOES NOT WORK
                # >> For the moment AEL cannot launch executables on Windows having Unicode paths.
                if app_ext == 'bat' or app_ext == 'BAT':
                    info = subprocess_hack.STARTUPINFO()
                    info.dwFlags = 1
                    if self.settings['show_batch']: info.wShowWindow = 5
                    else:                           info.wShowWindow = 0
                pr = subprocess_hack.Popen(r'{0} {1}'.format(application, arguments).encode('utf-8'),
                                           cwd = apppath.encode('utf-8'),
                                           startupinfo = info)
                pr.wait()

        # >> Linux and Android
        elif sys.platform.startswith('linux'):
            if self.settings['lirc_state']: xbmc.executebuiltin('LIRC.stop')

            # >> Old way of launching child process
            os.system('"{0}" {1}'.format(application, arguments).encode('utf-8'))

            # >> New way of launching, uses subproces module. Also, save child process stdout.
            # if arguments:
            #     if arguments[0] == '"' and arguments[-1] == '"': arguments = arguments[1:-1]
            #     with open(LAUNCH_LOG_FILE_PATH, 'w') as f:
            #         subprocess.call([application, arguments], stdout = f, stderr = f)
            #         f.close()
            # else:
            #     with open(LAUNCH_LOG_FILE_PATH, 'w') as f:
            #         subprocess.call(application, stdout = f, stderr = f)
            #         f.close()

            if self.settings['lirc_state']: xbmc.executebuiltin('LIRC.start')

        # >> OS X
        elif sys.platform.startswith('darwin'):
            os.system('"{0}" {1}'.format(application, arguments).encode('utf-8'))

        else:
            kodi_notify_warn('Cannot determine the running platform')

    #
    # These two functions do things like stopping music before lunch, toggling full screen, etc.
    #
    def _run_before_execution(self, rombasename, minimize_flag):
        # --- Stop/Pause Kodi mediaplayer if requested in settings ---
        kodi_was_playing_flag = False
        # id="media_state" default="0" values="Stop|Pause|Let Play"
        media_state = self.settings['media_state']
        media_state_str = ['Stop', 'Pause', 'Let Play'][media_state]
        log_verb('_run_before_execution() media_state is "{0}" ({1})'.format(media_state_str, media_state))
        if media_state != 2 and xbmc.Player().isPlaying():
            kodi_was_playing_flag = True
            if media_state == 0:
                log_verb('_run_before_execution() Calling xbmc.Player().stop()')
                xbmc.Player().stop()
            elif media_state == 1:
                log_verb('_run_before_execution() Calling xbmc.Player().pause()')
                xbmc.Player().pause()
            xbmc.sleep(self.settings['start_tempo'] + 100)

            # >> Don't know what this code does exactly... Maybe compatibility with old versions of Kodi?
            # try:
            #     log_verb('_run_before_execution() Calling xbmc.audioSuspend()')
            #     xbmc.audioSuspend()
            # except:
            #     log_verb('_run_before_execution() EXCEPCION calling xbmc.audioSuspend()')

        # --- Minimize Kodi if requested ---
        if minimize_flag:
            log_verb('_run_before_execution() Toggling Kodi fullscreen')
            kodi_toogle_fullscreen()
        else:
            log_verb('_run_before_execution() Toggling Kodi fullscreen DEACTIVATED in Launcher')

        if self.settings['display_launcher_notify']:
            kodi_notify('Launching {0}'.format(rombasename))

        # >> Disable navigation sounds?
        try:
            log_verb('_run_before_execution() Calling xbmc.enableNavSounds(False)')
            xbmc.enableNavSounds(False)
        except:
            log_verb('_run_before_execution() EXCEPCION calling xbmc.enableNavSounds(False)')

        # >> Pause Kodi execution some time
        start_tempo_ms = self.settings['start_tempo']
        log_verb('_run_before_execution() Pausing {0} ms'.format(start_tempo_ms))
        xbmc.sleep(start_tempo_ms)

        return kodi_was_playing_flag

    def _run_after_execution(self, kodi_was_playing_flag, minimize_flag):
        # >> Stop Kodi some time
        start_tempo_ms = self.settings['start_tempo']
        log_verb('_run_after_execution() Pausing {0} ms'.format(start_tempo_ms))
        xbmc.sleep(start_tempo_ms)

        try:
            log_verb('_run_after_execution() Calling xbmc.enableNavSounds(True)')
            xbmc.enableNavSounds(True)
        except:
            log_verb('_run_after_execution() EXCEPCION calling xbmc.enableNavSounds(True)')

        if minimize_flag:
            log_verb('_run_after_execution() Toggling Kodi fullscreen')
            kodi_toogle_fullscreen()
        else:
            log_verb('_run_after_execution() Toggling Kodi fullscreen DEACTIVATED in Launcher')

        # --- Resume Kodi playing if it was stop/paused ---
        media_state = self.settings['media_state']
        media_state_str = ['Stop', 'Pause', 'Let Play'][media_state]
        log_verb('_run_after_execution() media_state is "{0}" ({1})'.format(media_state_str, media_state))
        log_verb('_run_after_execution() kodi_was_playing_flag is {0}'.format(kodi_was_playing_flag))
        if media_state != 2 and kodi_was_playing_flag:
            # Calling xmbc.audioResume() takes a loong time (2/4 secs) if audio was not properly suspended!
            # Also produces this in Kodi's log:
            # WARNING: CActiveAE::StateMachine - signal: 0 from port: OutputControlPort not handled for state: 7
            #   ERROR: ActiveAE::Resume - failed to init
            #
            # I will deactivate this and also in _run_before_execution() and see what happens.
            # try:
            #     log_verb('_run_after_execution() Calling xbmc.audioResume()')
            #     xbmc.audioResume()
            # except:
            #     log_verb('_run_after_execution() EXCEPCION calling xbmc.audioResume()')

            # >> If Kodi was paused then resume playing media.
            if media_state == 1:
                log_verb('_run_after_execution() Pausing {0} ms'.format(start_tempo_ms + 100))
                xbmc.sleep(start_tempo_ms + 100)
                log_verb('_run_after_execution() Calling xbmc.Player().play()')
                xbmc.Player().play()
        log_debug('_run_after_execution() function ENDS')

    #
    # Creates a Launcher report having:
    #  1) Launcher statistics
    #  2) Report of ROM metadata
    #  3) Report of ROM artwork
    #  4) If No-Intro file, then No-Intro audit information.
    #
    def _roms_create_launcher_report(self, categoryID, launcherID, roms):
        ROM_NAME_LENGHT = 50

        # >> Report file name
        category = self.categories[categoryID]
        launcher = self.launchers[launcherID]
        roms_base_noext = fs_get_ROMs_basename(category['m_name'], launcher['m_name'], launcherID)
        report_file_name = os.path.join(REPORTS_DIR, roms_base_noext + '.txt')
        log_verb('_roms_create_launcher_report() Report filename "{0}"'.format(report_file_name))
        kodi_notify('Creating Launcher report...')

        # >> Step 1: Launcher main statistics
        num_roms = len(roms)

        # >> Step 2: ROM metadata and fanart
        missing_m_year      = missing_m_genre = missing_m_studio = missing_m_rating = 0
        missing_m_plot      = 0
        missing_s_title     = missing_s_snap     = missing_s_fanart  = missing_s_banner    = 0
        missing_s_clearlogo = missing_s_boxfront = missing_s_boxback = missing_s_cartridge = 0
        missing_s_flyer     = missing_s_map      = missing_s_manual  = missing_s_trailer   = 0
        check_list = []
        for rom_id in sorted(roms, key = lambda x : roms[x]['m_name']):
            rom = roms[rom_id]
            rom_info = {}
            rom_info['m_name'] = rom['m_name']
            # >> Metadata
            if rom['m_year']:   rom_info['m_year']   = 'YES'
            else:               rom_info['m_year']   = '---'; missing_m_year += 1
            if rom['m_genre']:  rom_info['m_genre']  = 'YES'
            else:               rom_info['m_genre']  = '---'; missing_m_genre += 1
            if rom['m_studio']: rom_info['m_studio'] = 'YES'
            else:               rom_info['m_studio'] = '---'; missing_m_studio += 1
            if rom['m_rating']: rom_info['m_rating'] = 'YES'
            else:               rom_info['m_rating'] = '---'; missing_m_rating += 1
            if rom['m_plot']:   rom_info['m_plot']   = 'YES'
            else:               rom_info['m_plot']   = '---'; missing_m_plot += 1
            # >> Assets
            if rom['s_title']:     rom_info['s_title']     = 'Y'
            else:                  rom_info['s_title']     = '-'; missing_s_title += 1
            if rom['s_snap']:      rom_info['s_snap']      = 'Y'
            else:                  rom_info['s_snap']      = '-'; missing_s_snap += 1
            if rom['s_fanart']:    rom_info['s_fanart']    = 'Y'
            else:                  rom_info['s_fanart']    = '-'; missing_s_fanart += 1
            if rom['s_banner']:    rom_info['s_banner']    = 'Y'
            else:                  rom_info['s_banner']    = '-'; missing_s_banner += 1
            if rom['s_clearlogo']: rom_info['s_clearlogo'] = 'Y'
            else:                  rom_info['s_clearlogo'] = '-'; missing_s_clearlogo += 1
            if rom['s_boxfront']:  rom_info['s_boxfront']  = 'Y'
            else:                  rom_info['s_boxfront']  = '-'; missing_s_boxfront += 1
            if rom['s_boxback']:   rom_info['s_boxback']   = 'Y'
            else:                  rom_info['s_boxback']   = '-'; missing_s_boxback += 1
            if rom['s_cartridge']: rom_info['s_cartridge'] = 'Y'
            else:                  rom_info['s_cartridge'] = '-'; missing_s_cartridge += 1
            if rom['s_flyer']:     rom_info['s_flyer']     = 'Y'
            else:                  rom_info['s_flyer']     = '-'; missing_s_flyer += 1
            if rom['s_map']:       rom_info['s_map']       = 'Y'
            else:                  rom_info['s_map']       = '-'; missing_s_map += 1
            if rom['s_manual']:    rom_info['s_manual']    = 'Y'
            else:                  rom_info['s_manual']    = '-'; missing_s_manual += 1
            if rom['s_trailer']:   rom_info['s_trailer']   = 'Y'
            else:                  rom_info['s_trailer']   = '-'; missing_s_trailer += 1
            # >> Add to list
            check_list.append(rom_info)

        # >> Step 4: No-Intro audit

        # >> Step 5: Make report
        str_list = []
        str_list.append('<Launcher Information>\n')
        str_list.append('Launcher name       {0}\n'.format(launcher['m_name']))
        str_list.append('Number of ROMs      {0}\n'.format(num_roms))
        # >> Metadata
        str_list.append('ROMs with Year      {0} ({1} missing)\n'.format(num_roms - missing_m_year,   missing_m_year))
        str_list.append('ROMs with Genre     {0} ({1} missing)\n'.format(num_roms - missing_m_genre,  missing_m_genre))
        str_list.append('ROMs with Studio    {0} ({1} missing)\n'.format(num_roms - missing_m_studio, missing_m_studio))
        str_list.append('ROMs with Rating    {0} ({1} missing)\n'.format(num_roms - missing_m_rating, missing_m_rating))
        str_list.append('ROMs with Plot      {0} ({1} missing)\n'.format(num_roms - missing_m_plot,   missing_m_plot))
        # >> Assets
        str_list.append('ROMs with Title     {0} ({1} missing)\n'.format(num_roms - missing_s_title,     missing_s_title))
        str_list.append('ROMS with Snap      {0} ({1} missing)\n'.format(num_roms - missing_s_snap,      missing_s_snap))
        str_list.append('ROMs with Fanart    {0} ({1} missing)\n'.format(num_roms - missing_s_fanart,    missing_s_fanart))
        str_list.append('ROMS with Banner    {0} ({1} missing)\n'.format(num_roms - missing_s_banner,    missing_s_banner))
        str_list.append('ROMs with Clearlogo {0} ({1} missing)\n'.format(num_roms - missing_s_clearlogo, missing_s_clearlogo))
        str_list.append('ROMS with Boxfront  {0} ({1} missing)\n'.format(num_roms - missing_s_boxfront,  missing_s_boxfront))
        str_list.append('ROMs with Boxback   {0} ({1} missing)\n'.format(num_roms - missing_s_boxback,   missing_s_boxback))
        str_list.append('ROMS with Cartridge {0} ({1} missing)\n'.format(num_roms - missing_s_cartridge, missing_s_cartridge))
        str_list.append('ROMs with Flyer     {0} ({1} missing)\n'.format(num_roms - missing_s_flyer,     missing_s_flyer))
        str_list.append('ROMS with Map       {0} ({1} missing)\n'.format(num_roms - missing_s_map,       missing_s_map))
        str_list.append('ROMs with Manual    {0} ({1} missing)\n'.format(num_roms - missing_s_manual,    missing_s_manual))
        str_list.append('ROMS with Trailer   {0} ({1} missing)\n'.format(num_roms - missing_s_trailer,   missing_s_trailer))

        str_list.append('\n<Metadata Information>\n')
        str_list.append('{0} Year Genre Studio Rating Plot\n'.format('Name'.ljust(ROM_NAME_LENGHT)))
        str_list.append('{0}\n'.format('-' * 80))
        for m in check_list:
            # >> Limit ROM name string length
            name_str = text_limit_string(m['m_name'], ROM_NAME_LENGHT)
            str_list.append('{0} {1}  {2}   {3}    {4}    {5}\n'.format(
                            name_str.ljust(ROM_NAME_LENGHT), 
                            m['m_year'], m['m_genre'], m['m_studio'],
                            m['m_rating'], m['m_plot']))

        str_list.append('\n<Asset/Artwork Information>\n')
        str_list.append('{0} Tit Snap Fan Ban Clr Boxf Boxb Cart Fly Map Man Tra\n'.format('Name'.ljust(ROM_NAME_LENGHT)))
        str_list.append('{0}\n'.format('-' * 102))
        for m in check_list:
            # >> Limit ROM name string length
            name_str = text_limit_string(m['m_name'], ROM_NAME_LENGHT)
            str_list.append('{0} {1}   {2}    {3}   {4}   {5}   {6}    {7}    {8}    {9}   {10}   {11}   {12}\n'.format(
                            name_str.ljust(ROM_NAME_LENGHT), 
                            m['s_title'],     m['s_snap'],     m['s_fanart'],  m['s_banner'],
                            m['s_clearlogo'], m['s_boxfront'], m['s_boxback'], m['s_cartridge'],
                            m['s_flyer'],     m['s_map'],      m['s_manual'],  m['s_trailer']))

        # >> Step 6: Join string and write TXT file
        try:
            full_string = ''.join(str_list).encode('utf-8')
            file = open(report_file_name, 'w')
            file.write(full_string)
            file.close()
        except OSError:
            log_error('Cannot write Launcher Report file (OSError)')
            kodi_notify_warn('Cannot write Launcher Report (OSError)')
        except IOError:
            log_error('Cannot write categories.xml file (IOError)')
            kodi_notify_warn('Cannot write Launcher Report (IOError)')

    #
    # Deletes missing ROMs
    #
    def _roms_delete_missing_ROMs(self, roms):
        num_removed_roms = 0
        num_roms = len(roms)
        log_info('_roms_delete_missing_ROMs() Launcher DB contain {0} items'.format(num_roms))
        if num_roms > 0:
            log_verb('_roms_delete_missing_ROMs() Starting dead items scan')
            for rom_id in sorted(roms.iterkeys()):
                name = roms[rom_id]['m_name']
                filename = roms[rom_id]['filename']
                log_debug('_roms_delete_missing_ROMs() Testing {0}'.format(name))

                # Remove missing ROMs
                if not os.path.isfile(filename):
                    log_debug('_roms_delete_missing_ROMs() Delete {0} item entry'.format(name))
                    del roms[rom_id]
                    num_removed_roms += 1
                    continue
            if num_removed_roms > 0:
                log_info('_roms_delete_missing_ROMs() {0} dead ROMs removed successfully'.format(num_removed_roms))
            else:
                log_info('_roms_delete_missing_ROMs() No dead ROMs found.')
        else:
            log_info('_roms_delete_missing_ROMs() Launcher is empty. No dead ROM check.')

        return num_removed_roms

    #
    # Reset the No-Intro status
    # 1) Remove all ROMs which does not exist.
    # 2) Set status of remaining ROMs to nointro_status = 'None'
    #
    def _roms_reset_NoIntro_status(self, roms):
        num_roms = len(roms)
        log_info('_roms_reset_NoIntro_status() Launcher DB contain {0} items'.format(num_roms))
        if num_roms > 0:
            log_verb('_roms_reset_NoIntro_status() Starting dead items scan')
            for rom_id in sorted(roms.iterkeys()):
                roms[rom_id]['nointro_status'] = 'None'
        else:
            log_info('_roms_reset_NoIntro_status() Launcher is empty. No dead ROM check.')

    #
    # Helper function to update ROMs No-Intro status if user configured a No-Intro DAT file.
    # Dictionaries are mutable, so roms can be changed because passed by assigment.
    #
    def _roms_update_NoIntro_status(self, roms, nointro_xml_file):
        # --- Reset the No-Intro status ---
        self._roms_reset_NoIntro_status(roms)

        # --- Check if DAT file exists ---
        if not os.path.isfile(nointro_xml_file):
            log_warn('_roms_update_NoIntro_status Not found {0}'.format(nointro_xml_file))
            return (0, 0, 0)

        # --- Load No-Intro DAT ---
        roms_nointro = fs_load_NoIntro_XML_file(nointro_xml_file)

        # --- Check for errors ---
        if not roms_nointro:
            log_warn('_roms_update_NoIntro_status Error loading {0}'.format(nointro_xml_file))
            return (0, 0, 0)

        # Put ROM names in a set. Set is the fastes Python container for searching
        # elements (implements hashed search).
        roms_nointro_set = set(roms_nointro.keys())
        roms_set = set()
        for rom_id in roms:
            roms_set.add(roms[rom_id]['m_name'])

        # Traverse ROMs and check they are in the DAT
        num_have = num_miss = num_unknown = 0
        for rom_id in roms:
            if roms[rom_id]['m_name'] in roms_nointro_set:
                roms[rom_id]['nointro_status'] = 'Have'
                num_have += 1
            else:
                roms[rom_id]['nointro_status'] = 'Unknown'
                num_unknown += 1

        # Mark dead ROMs as missing
        for rom_id in roms:
            name     = roms[rom_id]['m_name']
            filename = roms[rom_id]['filename']
            log_debug('_roms_update_NoIntro_status() Testing {0}'.format(name))
            if not os.path.isfile(filename):
                log_debug('_roms_update_NoIntro_status() Not found {0}'.format(name))
                roms[rom_id]['nointro_status'] = 'Miss'

        # Now add missing ROMs. Traverse the nointro set and add the ROM if it's not there.
        for nointro_rom in roms_nointro_set:
            if nointro_rom not in roms_set:
                # Add new "fake" missing ROM. This ROM cannot be launched!
                rom = fs_new_rom()
                rom_id = misc_generate_random_SID()
                rom['id'] = rom_id
                rom['m_name'] = nointro_rom
                rom['nointro_status'] = 'Miss'
                roms[rom_id] = rom
                num_miss += 1

        # Return statistics
        return (num_have, num_miss, num_unknown)

    #
    # Manually add a new ROM instead of a recursive scan.
    #   A) User chooses a ROM file
    #   B) Title is formatted. No metadata scraping.
    #   C) Thumb and fanart are searched locally only.
    # Later user can edit this ROM if he wants.
    #
    def _roms_add_new_rom(self, launcherID):
        # --- Grab launcher information ---
        launcher = self.launchers[launcherID]
        romext   = launcher['romext']
        rompath  = launcher['rompath']
        log_verb('_roms_add_new_rom() launcher name "{0}"'.format(launcher['m_name']))

        # --- Load ROMs for this launcher ---
        roms = fs_load_ROMs(ROMS_DIR, launcher['roms_base_noext'])

        # --- Choose ROM file ---
        dialog = xbmcgui.Dialog()
        extensions = '.' + romext.replace('|', '|.')
        romfile = dialog.browse(1, 'Select the ROM file', 'files', extensions, False, False, rompath).decode('utf-8')
        if not romfile: return
        log_verb('_roms_add_new_rom() romfile "{0}"'.format(romfile))

        # --- Format title ---
        scan_clean_tags = self.settings['scan_clean_tags']
        ROM = misc_split_path(romfile)
        romname = text_ROM_title_format(ROM.base_noext, scan_clean_tags)

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
        local_asset_list = assets_search_local_assets(launcher, ROM, enabled_asset_list)

        # --- Create ROM data structure ---
        romdata = fs_new_rom()
        romdata['id']          = misc_generate_random_SID()
        romdata['filename']    = ROM.path
        romdata['m_name']      = romname
        for index, asset_kind in enumerate(ROM_ASSET_LIST):
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

        # ~~~ Save ROMs XML file ~~~
        # >> Also save categories/launchers to update timestamp
        launcher['timestamp_launcher'] = time.time()
        fs_write_ROMs(ROMS_DIR, launcher['roms_base_noext'], roms, launcher)
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

    #
    # ROM scanner. Called when user chooses "Add items" -> "Scan items"
    # Note that actually this command is "Add/Update" ROMs.
    #
    def _roms_import_roms(self, launcherID):
        log_debug('========== _roms_import_roms() BEGIN ==========')

        # --- Get information from launcher ---
        selectedLauncher = self.launchers[launcherID]
        launcher_app     = selectedLauncher['application']
        launcher_path    = selectedLauncher['rompath']
        launcher_exts    = selectedLauncher['romext']
        log_debug('Launcher "{0}" selected'.format(selectedLauncher['m_name']))
        log_debug('launcher_app  = {0}'.format(launcher_app))
        log_debug('launcher_path = {0}'.format(launcher_path))
        log_debug('launcher_exts = {0}'.format(launcher_exts))
        log_debug('platform      = {0}'.format(selectedLauncher['platform']))

        # Check if there is an XML for this launcher. If so, load it.
        # If file does not exist or is empty then return an empty dictionary.
        roms = fs_load_ROMs(ROMS_DIR, selectedLauncher['roms_base_noext'])
        num_roms = len(roms)

        # --- Load metadata/asset scrapers ---
        self._load_metadata_scraper()
        self._load_asset_scraper()

        # ~~~ Check asset dirs and disable scanning for unset dirs ~~~
        (self.enabled_asset_list, unconfigured_name_list) = asset_get_configured_dir_list(selectedLauncher)
        if unconfigured_name_list:
            unconfigure_asset_srt = ', '.join(unconfigured_name_list)
            kodi_dialog_OK('Assets directories not set: {0}. '.format(unconfigure_asset_srt) +
                           'Asset scanner will be disabled for this/those.')

        # ~~~ Ensure there is no duplicate asset dirs ~~~
        # >> Cancel scanning if duplicates found
        duplicated_name_list = asset_get_duplicated_dir_list(selectedLauncher)
        if duplicated_name_list:
            duplicated_asset_srt = ', '.join(duplicated_name_list)
            log_info('Duplicated asset dirs: {0}'.format(duplicated_asset_srt))
            kodi_dialog_OK('Duplicated asset directories: {0}. '.format(duplicated_asset_srt) +
                           'Change asset directories before continuing.')
            return
        else:
            log_info('No duplicated asset dirs found')

        # --- Progress dialog ---
        # Put in in object variables so it can be access in helper functions.
        self.pDialog = xbmcgui.DialogProgress()
        self.pDialog_canceled = False

        # ~~~~~ Remove dead entries ~~~~~
        num_removed_roms = 0
        log_info('Launcher ROM database contain {0} items'.format(len(roms)))
        if num_roms > 0:
            log_debug('Starting dead items scan')
            i = 0
            self.pDialog.create('Advanced Emulator Launcher - Scanning ROMs',
                                'Checking for dead entries...', "Path '{0}'".format(launcher_path))
            for key in sorted(roms.iterkeys()):
                log_debug('Searching {0}'.format(roms[key]['filename']))
                self.pDialog.update(i * 100 / num_roms)
                i += 1
                if not os.path.isfile(roms[key]['filename']):
                    log_debug('Not found')
                    log_debug('Delete {0} item entry'.format(roms[key]['filename']))
                    del roms[key]
                    num_removed_roms += 1
            self.pDialog.close()
            if num_removed_roms > 0:
                kodi_notify('{0} dead ROMs removed successfully'.format(num_removed_roms))
                log_info('{0} dead ROMs removed successfully'.format(num_removed_roms))
            else:
                log_info('No dead ROMs found')
        else:
            log_info('Launcher is empty. No dead ROM check.')

        # ~~~ Scan for new files (*.*) and put them in a list ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        kodi_notify('Scanning files...')
        kodi_busydialog_ON()
        log_info('Scanning files in {0}'.format(launcher_path))
        files = []
        if self.settings['scan_recursive']:
            log_info('Recursive scan activated')
            for root, dirs, filess in os.walk(launcher_path):
                for filename in fnmatch.filter(filess, '*.*'):
                    files.append(os.path.join(root, filename))
        else:
            log_info('Recursive scan not activated')
            filesname = os.listdir(launcher_path)
            for filename in filesname:
                files.append(os.path.join(launcher_path, filename))
        kodi_busydialog_OFF()
        num_files = len(files)
        log_info('Found {0} files'.format(num_files))

        # ~~~ Now go processing file by file ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.pDialog.create('AEL - Scanning ROMs', 'Scanning {0}'.format(launcher_path))
        log_debug('==================== Processing ROMs ====================')
        num_new_roms = 0
        num_files_checked = 0
        for f_path in files:
            # --- Get all file name combinations ---
            ROM = misc_split_path(f_path)
            log_debug('========== Processing File ==========')
            log_debug('ROM.path       "{0}"'.format(ROM.path))
            # log_debug('ROM.path_noext "{0}"'.format(ROM.path_noext))
            # log_debug('ROM.base       "{0}"'.format(ROM.base))
            # log_debug('ROM.dirname    "{0}"'.format(ROM.dirname))
            # log_debug('ROM.base_noext "{0}"'.format(ROM.base_noext))
            # log_debug('ROM.ext        "{0}"'.format(ROM.ext))

            # ~~~ Update progress dialog ~~~
            self.progress_number = num_files_checked * 100 / num_files
            self.file_text       = 'ROM {0}'.format(ROM.base)
            activity_text        = 'Checking if has ROM extension...'
            self.pDialog.update(self.progress_number, self.file_text, activity_text)
            num_files_checked += 1

            # ~~~ Find ROM file ~~~
            # The recursive scan has scanned all file. Check if this file matches some of the extensions
            # for ROMs. If not, skip this file and go for next one in the list.
            processROM = False
            for ext in launcher_exts.split("|"):
                # Check if filename matchs extension
                if ROM.ext == '.' + ext:
                    log_debug("Expected '{0}' extension detected".format(ext))
                    processROM = True
            # If file does not match any of the ROM extensions skip it
            if not processROM:
                continue

            # Check that ROM is not already in the list of ROMs
            repeatedROM = False
            for rom_id in roms:
                if roms[rom_id]['filename'] == f_path:
                    log_debug('File already into launcher list')
                    repeatedROM = True
            # If file already in ROM list skip it
            if repeatedROM:
                continue

            # --- Ignore BIOS ROMs ---
            # Name of bios is: '[BIOS] Rom name example.zip'
            if self.settings['scan_ignore_bios']:
                BIOS_re = re.findall('\[BIOS\]', ROM.base)
                if len(BIOS_re) > 0:
                    log_info("BIOS detected. Skipping ROM '{0}'".format(ROM.path))
                    continue

            # ~~~~~ Process new ROM and add to the list ~~~~~
            romdata     = self._roms_process_scanned_ROM(launcherID, ROM)
            romID       = romdata['id']
            roms[romID] = romdata
            num_new_roms += 1

            # ~~~ Check if user pressed the cancel button ~~~
            if self.pDialog.iscanceled() or self.pDialog_canceled:
                self.pDialog.close()
                kodi_dialog_OK('Stopping ROM scanning. No changes have been made.')
                log_info('User pressed Cancel button when scanning ROMs')
                log_info('ROM scanning stopped')
                return
        self.pDialog.close()
        log_info('***** ROM scanner finished. Report ******')
        log_info('Removed dead ROMs {0:6d}'.format(num_removed_roms))
        log_info('Files checked     {0:6d}'.format(num_files_checked))
        log_info('New added ROMs    {0:6d}'.format(num_new_roms))

        if len(roms) == 0:
            kodi_dialog_OK('No ROMs found! Make sure launcher directory and file extensions are correct.')
            return

        if num_new_roms == 0:
            kodi_dialog_OK('Launcher has {0} ROMs and no new ROMs have been added.'.format(len(roms)))

        # --- If we have a No-Intro XML then audit roms after scanning ----------------------------
        # >> NOTE disable No-Intro auditing in scanner. User can do the audit in the Edit Launcher menu.
        # if selectedLauncher['nointro_xml_file'] != '':
        #     nointro_xml_file = selectedLauncher['nointro_xml_file']
        #     log_info('Auditing ROMs using No-Intro DAT {0}'.format(nointro_xml_file))

        #     # --- Update No-Intro status for ROMs ---
        #     # Note that roms dictionary is updated using Python pass by assigment.
        #     # See http://stackoverflow.com/questions/986006/how-do-i-pass-a-variable-by-reference
        #     (num_have, num_miss, num_unknown) = self._roms_update_NoIntro_status(roms, nointro_xml_file)

        #     # Report
        #     log_info('***** No-Intro audit finished. Report ******')
        #     log_info('No-Intro Have ROMs    {0:6d}'.format(num_have))
        #     log_info('No-Intro Miss ROMs    {0:6d}'.format(num_miss))
        #     log_info('No-Intro Unknown ROMs {0:6d}'.format(num_unknown))
        # else:
        #     log_info('No No-Intro DAT configured. No auditing ROMs.')

        # ~~~ Save ROMs XML file ~~~
        # >> Also save categories/launchers to update timestamp
        fs_write_ROMs(ROMS_DIR, selectedLauncher['roms_base_noext'], roms, selectedLauncher)
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

        # ~~~ Notify user ~~~
        kodi_notify('Added {0} new ROMs'.format(num_new_roms))
        log_debug('========== _roms_import_roms() END ==========')
        kodi_refresh_container()

    def _roms_process_scanned_ROM(self, launcherID, ROM):
        # --- "Constants" ---
        META_TITLE_ONLY = 100
        META_NFO_FILE   = 200
        META_SCRAPER    = 300

        # --- Create new rom dictionary ---
        launcher = self.launchers[launcherID]
        platform = launcher['platform']
        romdata  = fs_new_rom()
        romdata['id'] = misc_generate_random_SID()
        romdata['filename'] = ROM.path

        # ~~~~~ Scrape game metadata information ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # >> Test if NFO file exists
        nfo_file_path = ROM.path_noext + ".nfo"
        log_debug('Testing NFO file "{0}"'.format(nfo_file_path))
        found_NFO_file = True if os.path.isfile(nfo_file_path) else False

        # >> Determine metadata action based on policy
        # >> scan_metadata_policy -> values="None|NFO Files|NFO Files + Scrapers|Scrapers"
        scan_metadata_policy       = self.settings['scan_metadata_policy']
        scan_clean_tags            = self.settings['scan_clean_tags']
        scan_ignore_scrapped_title = self.settings['scan_ignore_scrap_title']
        metadata_action = META_TITLE_ONLY
        if scan_metadata_policy == 0:
            log_verb('Metadata policy: No NFO reading, no scraper. Only cleaning ROM name.')
            metadata_action = META_TITLE_ONLY
        elif scan_metadata_policy == 1:
            log_verb('Metadata policy: Read NFO file only | Scraper OFF')
            metadata_action = META_NFO_FILE
        elif scan_metadata_policy == 2 and found_NFO_file:
            log_verb('Metadata policy: Read NFO file ON, if not NFO then Scraper ON')
            log_verb('Metadata policy: NFO file found | Scraper OFF')
            metadata_action = META_NFO_FILE
        elif scan_metadata_policy == 2 and not found_NFO_file:
            log_verb('Metadata policy: Read NFO file ON, if not NFO then Scraper ON')
            log_verb('Metadata policy: NFO file not found | Scraper ON')
            metadata_action = META_SCRAPER
        elif scan_metadata_policy == 3:
            log_verb('Metadata policy: Read NFO file OFF | Scraper ON')
            log_verb('Metadata policy: Forced scraper ON')
            metadata_action = META_SCRAPER
        else:
            log_error('Invalid scan_metadata_policy value = {0}'.format(scan_metadata_policy))

        # >> Do metadata action based on policy
        if metadata_action == META_TITLE_ONLY:
            scraper_text = 'Formatting ROM name.'
            self.pDialog.update(self.progress_number, self.file_text, scraper_text)
            romdata['m_name'] = text_ROM_title_format(ROM.base_noext, scan_clean_tags)
        elif metadata_action == META_NFO_FILE:
            nfo_file_path = ROM.path_noext + ".nfo"
            scraper_text = 'Reading NFO file {0}'.format(nfo_file_path)
            self.pDialog.update(self.progress_number, self.file_text, scraper_text)
            log_debug('Trying NFO file "{0}"'.format(nfo_file_path))
            if os.path.isfile(nfo_file_path):
                log_debug('NFO file found. Reading it')
                nfo_dic = fs_load_NFO_file_scanner(nfo_file_path)
                # NOTE <platform> is chosen by AEL, never read from NFO files
                romdata['m_name']   = nfo_dic['title']     # <title>
                romdata['m_year']   = nfo_dic['year']      # <year>
                romdata['m_genre']  = nfo_dic['genre']     # <genre>
                romdata['m_studio'] = nfo_dic['publisher'] # <publisher>
                romdata['m_plot']   = nfo_dic['plot']      # <plot>
            else:
                log_debug('NFO file not found. Only cleaning ROM name.')
                romdata['m_name'] = text_ROM_title_format(ROM.base_noext, scan_clean_tags)
        elif metadata_action == META_SCRAPER:
            scraper_text = 'Scraping metadata with {0}. Searching for matching games...'.format(self.scraper_metadata.fancy_name)
            self.pDialog.update(self.progress_number, self.file_text, scraper_text)

            # --- Do a search and get a list of games ---
            rom_name_scraping = text_clean_ROM_name_for_scraping(ROM.base_noext)
            results = self.scraper_metadata.get_search(rom_name_scraping, ROM.base_noext, platform)
            log_debug('Metadata scraper found {0} result/s'.format(len(results)))
            if results:
                # id="metadata_scraper_mode" values="Semi-automatic|Automatic"
                if self.settings['metadata_scraper_mode'] == 0:
                    log_debug('Metadata semi-automatic scraping')
                    # Close progress dialog (and check it was not canceled)
                    if self.pDialog.iscanceled(): self.pDialog_canceled = True
                    self.pDialog.close()

                    # Display corresponding game list found so user choses
                    dialog = xbmcgui.Dialog()
                    rom_name_list = []
                    for game in results: rom_name_list.append(game['display_name'])
                    selectgame = dialog.select('Select game for ROM {0}'.format(ROM.base_noext), rom_name_list)
                    if selectgame < 0: selectgame = 0

                    # Open progress dialog again
                    self.pDialog.create('Advanced Emulator Launcher - Scanning ROMs')
                elif self.settings['metadata_scraper_mode'] == 1:
                    log_debug('Metadata automatic scraping. Selecting first result.')
                    selectgame = 0
                else:
                    log_error('Invalid metadata_scraper_mode {0}'.format(self.settings['metadata_scraper_mode']))
                    selectgame = 0
                scraper_text = 'Scraping metadata with {0}. Game selected. Getting metadata...'.format(self.scraper_metadata.fancy_name)
                self.pDialog.update(self.progress_number, self.file_text, scraper_text)
                    
                # --- Grab metadata for selected game ---
                gamedata = self.scraper_metadata.get_metadata(results[selectgame])

                # --- Put metadata into ROM dictionary ---
                if scan_ignore_scrapped_title:
                    # Ignore scraped title
                    romdata['m_name'] = text_ROM_title_format(ROM.base_noext, scan_clean_tags)
                    log_debug("User wants to ignore scraper name. Setting name to '{0}'".format(romdata['m_name']))
                else:
                    # Use scraped title
                    romdata['m_name'] = gamedata['title']
                    log_debug("User wants scrapped name. Setting name to '{0}'".format(romdata['m_name']))
                romdata['m_year']   = gamedata['year']
                romdata['m_genre']  = gamedata['genre']
                romdata['m_studio'] = gamedata['studio']
                romdata['m_plot']   = gamedata['plot']
            else:
                log_verb('Metadata scraper found no games after searching. Only cleaning ROM name.')
                romdata['m_name'] = text_ROM_title_format(ROM.base_noext, scan_clean_tags)
        else:
            log_error('Invalid metadata_action value = {0}'.format(metadata_action))

        # ~~~~~ Search for local artwork/assets ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        local_asset_list = assets_search_local_assets(launcher, ROM, self.enabled_asset_list)

        # ~~~ Asset scraping ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # settings.xml -> id="scan_asset_policy" default="0" values="Local Assets|Local Assets + Scrapers|Scrapers only"
        scan_asset_policy = self.settings['scan_asset_policy']
        if scan_asset_policy == 0:
            log_verb('Asset policy: local images only | Scraper OFF')
            for i, asset_kind in enumerate(ROM_ASSET_LIST):
                A = assets_get_info_scheme(asset_kind)
                romdata[A.key] = local_asset_list[i]

        elif scan_asset_policy == 1:
            log_verb('Asset policy: if not Local Image then Scraper ON')
            # selected_title = self._roms_process_asset_policy_2(ASSET_TITLE, local_title, ROM, launcher)
            for i, asset_kind in enumerate(ROM_ASSET_LIST):
                A = assets_get_info_scheme(asset_kind)
                if not self.enabled_asset_list[i]: 
                    romdata[A.key] = ''
                    log_verb('Skipped {0} (dir not configured)'.format(A.name))
                    continue
                if local_asset_list[i]:
                    log_verb('Asset policy: local {0} FOUND | Scraper OFF'.format(A.name))
                    romdata[A.key] = local_asset_list[i]
                else:
                    log_verb('Asset policy: local {0} NOT found | Scraper ON'.format(A.name))
                    romdata[A.key] = self._roms_scrap_asset(asset_kind, local_asset_list[i], ROM, launcher)

        elif scan_asset_policy == 2:
            log_verb('Asset policy: scraper will overwrite local assets | Scraper ON')
            # selected_title = self._roms_scrap_asset(ASSET_TITLE, local_title, ROM, launcher)
            for i, asset_kind in enumerate(ROM_ASSET_LIST):
                A = assets_get_info_scheme(asset_kind)
                if not self.enabled_asset_list[i]: 
                    romdata[A.key] = ''
                    log_verb('Skipped {0} (dir not configured)'.format(A.name))
                    continue
                log_verb('Asset policy: local {0} NOT found | Scraper ON'.format(A.name))
                romdata[A.key] = self._roms_scrap_asset(asset_kind, local_asset_list[i], ROM, launcher)

        log_verb('Set Title     file "{0}"'.format(romdata['s_title']))
        log_verb('Set Snap      file "{0}"'.format(romdata['s_snap']))
        log_verb('Set Fanart    file "{0}"'.format(romdata['s_fanart']))
        log_verb('Set Banner    file "{0}"'.format(romdata['s_banner']))
        log_verb('Set Clearlogo file "{0}"'.format(romdata['s_clearlogo']))
        log_verb('Set Boxfront  file "{0}"'.format(romdata['s_boxfront']))
        log_verb('Set Boxback   file "{0}"'.format(romdata['s_boxback']))
        log_verb('Set Cartridge file "{0}"'.format(romdata['s_cartridge']))
        log_verb('Set Flyer     file "{0}"'.format(romdata['s_flyer']))
        log_verb('Set Map       file "{0}"'.format(romdata['s_map']))
        log_verb('Set Manual    file "{0}"'.format(romdata['s_manual']))
        log_verb('Set Trailer   file "{0}"'.format(romdata['s_trailer']))
        
        return romdata

    #
    # Returns a valid filename of the downloaded scrapped image, filename of local image
    # or empty string if scraper finds nothing or download failed.
    #
    def _roms_scrap_asset(self, asset_kind, local_asset_path, ROM, launcher):
        # >> By default always use local image in case scraper fails
        ret_asset_path = local_asset_path

        # --- Cutomise function depending of image_king ---
        A = assets_get_info_scheme(asset_kind)
        asset_directory  = launcher[A.path_key]
        asset_path_noext = assets_get_path_noext_DIR(A, asset_directory, ROM.base_noext)
        scraper_obj = self.scraper_asset
        platform = launcher['platform']

        # --- Updated progress dialog ---
        file_text = 'ROM {0}'.format(ROM.base)
        scraper_text = 'Scraping {0} with {1}. Searching for matching games...'.format(A.name, scraper_obj.name)
        self.pDialog.update(self.progress_number, self.file_text, scraper_text)
        log_verb('_roms_scrap_asset() Scraping {0} with {1}'.format(A.name, scraper_obj.name))
        log_debug('_roms_scrap_asset() local_asset_path "{0}"'.format(local_asset_path))
        log_debug('_roms_scrap_asset() asset_path_noext "{0}"'.format(asset_path_noext))

        # --- Call scraper and get a list of games ---
        rom_name_scraping = text_clean_ROM_name_for_scraping(ROM.base_noext)
        results = scraper_obj.get_search(rom_name_scraping, ROM.base_noext, platform)
        log_debug('{0} scraper found {1} result/s'.format(A.name, len(results)))
        if not results:
            log_debug('{0} scraper did not found any game'.format(A.name))
            return ret_asset_path

        # --- Choose game to download image ---
        # settings.xml: id="asset_scraper_mode"  default="0" values="Semi-automatic|Automatic"
        scraping_mode = self.settings['asset_scraper_mode']
        if scraping_mode == 0:
            log_debug('{0} semi-automatic scraping. User chooses.'.format(A.name))
            # Close progress dialog (and check it was not canceled)
            if self.pDialog.iscanceled(): self.pDialog_canceled = True
            self.pDialog.close()

            # Display corresponding game list found so user choses
            dialog = xbmcgui.Dialog()
            rom_name_list = []
            for game in results:
                rom_name_list.append(game['display_name'])
            selectgame = dialog.select('Select game for ROM {0}'.format(ROM.base_noext), rom_name_list)
            if selectgame < 0: selectgame = 0

            # Open progress dialog again
            self.pDialog.create('Advanced Emulator Launcher - Scanning ROMs')
        elif scraping_mode == 1:
            log_debug('{0} automatic scraping. Selecting first result.'.format(A.name))
            selectgame = 0
        else:
            log_error('{0} invalid thumb_mode {1}'.format(A.name, scraping_mode))
            selectgame = 0
        scraper_text = 'Scraping {0} with {1}. Game selected. Getting list of images...'.format(A.name, scraper_obj.name)
        self.pDialog.update(self.progress_number, self.file_text, scraper_text)

        # --- Grab list of images for the selected game ---
        image_list = scraper_obj.get_images(results[selectgame], asset_kind)
        log_verb('{0} scraper returned {1} images'.format(A.name, len(image_list)))
        if not image_list:
            log_debug('{0} scraper get_images() returned no images.'.format(A.name))
            return ret_asset_path

        # --- Semi-automatic scraping (user choses an image from a list) ---
        if scraping_mode == 0:
            # Close progress dialog before opening image chosing dialog
            if self.pDialog.iscanceled(): self.pDialog_canceled = True
            self.pDialog.close()

            # If there is a local image add it to the list and show it to the user
            if os.path.isfile(local_image):
                image_list.insert(0, {'name' : 'Current local image', 'URL' : local_image, 'disp_URL' : local_image} )

            # Returns a list of dictionaries {'name', 'URL', 'disp_URL'}
            image_url = gui_show_image_select(image_list)
            log_debug('{0} dialog returned image_url "{1}"'.format(A.name, image_url))
            if image_url == '': image_url = image_list[0]['URL']

            # Reopen progress dialog
            scraper_text = 'Scraping {0} with {1}. Downloading image...'.format(A.name, scraper_obj.name)
            self.pDialog.create('Advanced Emulator Launcher - Scanning ROMs')
            self.pDialog.update(self.progress_number, self.file_text, scraper_text)
        # --- Automatic scraping. Pick first image. ---
        else:
            # Pick first image in automatic mode
            image_url = image_list[0]['URL']

        # If user chose the local image don't download anything
        if image_url != local_asset_path:
            # ~~~ Download scraped image ~~~
            # Get Tumb/Fanart name with no extension, then get URL image extension
            # and make full thumb path. If extension cannot be determined
            # from URL defaul to '.jpg'
            img_ext    = text_get_image_URL_extension(image_url) # Includes front dot -> .jpg
            log_debug('img_ext "{0}"'.format(img_ext))
            image_path = asset_path_noext + img_ext

            # ~~~ Download image ~~~
            log_verb('Downloading URL  "{0}"'.format(image_url))
            log_verb('Into local file  "{0}"'.format(image_path))
            try:
                net_download_img(image_url, image_path)
            except socket.timeout:
                kodi_notify_warn('Cannot download {0} image (Timeout)'.format(image_name))

            # ~~~ Update Kodi cache with downloaded image ~~~
            # Recache only if local image is in the Kodi cache, this function takes care of that.
            kodi_update_image_cache(image_path)

            # --- Return value is downloaded image ---
            ret_asset_path = image_path
        else:
            log_debug('{0} scraper: user chose local image "{1}"'.format(image_name, image_url))
            ret_asset_path = image_url

        # --- Returned value ---
        return ret_asset_path

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
    def _gui_scrap_rom_metadata(self, roms, romID, launcherID):
        # --- Grab ROM info and metadata scraper settings ---
        # >> ROM in favourites
        if launcherID == VLAUNCHER_FAVOURITES_ID:
            platform = roms[romID]['platform']
        else:
            launcher = self.launchers[launcherID]
            platform = launcher['platform']
        f_path   = roms[romID]['filename']
        rom_name = roms[romID]['m_name']
        ROM      = misc_split_path(f_path)
        scan_clean_tags            = self.settings['scan_clean_tags']
        scan_ignore_scrapped_title = self.settings['scan_ignore_scrap_title']
        log_info('_gui_scrap_rom_metadata() ROM "{0}"'.format(rom_name))

        # --- Ask user to enter ROM metadata search string ---
        keyboard = xbmc.Keyboard(rom_name, 'Enter the ROM search string...')
        keyboard.doModal()
        if not keyboard.isConfirmed(): return False
        search_string = keyboard.getText()

        # --- Do a search and get a list of games ---
        # >> Prevent race conditions
        kodi_busydialog_ON()
        results = self.scraper_metadata.get_search(search_string, ROM.base_noext, platform)
        kodi_busydialog_OFF()
        log_verb('_gui_scrap_rom_metadata() Metadata scraper found {0} result/s'.format(len(results)))
        if not results:
            kodi_notify_warn('Scraper found no matches')
            return False
            
        # --- Display corresponding game list found so user choses ---
        dialog = xbmcgui.Dialog()
        rom_name_list = []
        for game in results:
            rom_name_list.append(game['display_name'])
        selectgame = dialog.select('Select game for ROM {0}'.format(rom_name), rom_name_list)
        if selectgame < 0: return False
        log_verb('_gui_scrap_rom_metadata() User chose game "{0}"'.format(rom_name_list[selectgame]))

        # --- Grab metadata for selected game ---
        # >> Prevent race conditions
        kodi_busydialog_ON()
        gamedata = self.scraper_metadata.get_metadata(results[selectgame])
        kodi_busydialog_OFF()
        if not gamedata:
            kodi_notify_warn('Cannot download game metadata.')
            return False

        # --- Put metadata into ROM dictionary ---
        # >> Ignore scraped title
        if scan_ignore_scrapped_title:
            roms[romID]['m_name'] = text_ROM_title_format(ROM.base_noext, scan_clean_tags)
            log_debug("User wants to ignore scraper name. Setting name to '{0}'".format(roms[romID]['m_name']))
        # >> Use scraped title
        else:
            roms[romID]['m_name'] = gamedata['title']
            log_debug("User wants scrapped name. Setting name to '{0}'".format(roms[romID]['m_name']))
        roms[romID]['m_year']   = gamedata['year']
        roms[romID]['m_genre']  = gamedata['genre']
        roms[romID]['m_studio'] = gamedata['studio']
        roms[romID]['m_plot']   = gamedata['plot']

        # >> Changes were made
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
    def _gui_scrap_launcher_metadata(self, launcherID):
        launcher = self.launchers[launcherID]
        platform = launcher['platform']
        
        # Edition of the launcher name
        keyboard = xbmc.Keyboard(self.launchers[launcherID]['m_name'], 'Enter the launcher search string ...')
        keyboard.doModal()
        if not keyboard.isConfirmed(): return False
        search_string = keyboard.getText()

        # Scrap and get a list of matches
        kodi_busydialog_ON()
        results = self.scraper_metadata.get_search(search_string, '', platform)
        kodi_busydialog_OFF()
        log_debug('_gui_scrap_launcher_metadata() Metadata scraper found {0} result/s'.format(len(results)))
        if not results:
            kodi_notify_warn('Scraper found no matches')
            return False

        # Display corresponding game list found so user choses
        dialog = xbmcgui.Dialog()
        rom_name_list = []
        for game in results:
            rom_name_list.append(game['display_name'])
        selectgame = dialog.select('Select game for ROM {0}'.format(rom_name), rom_name_list)
        if selectgame < 0: return False

        # --- Grab metadata for selected game ---
        # >> Prevent race conditions
        kodi_busydialog_ON()
        gamedata = self.scraper_metadata.get_metadata(results[selectgame])
        kodi_busydialog_OFF()
        if not gamedata:
            kodi_notify_warn('Cannot download game metadata.')
            return False

        # --- Put metadata into launcher dictionary ---
        # >> Scraper should not change launcher title
        self.launchers[launcherID]['m_year']   = gamedata['year']
        self.launchers[launcherID]['m_genre']  = gamedata['genre']
        self.launchers[launcherID]['m_studio'] = gamedata['studio']
        self.launchers[launcherID]['m_plot']   = gamedata['plot']

        # >> Changes were made
        return True

    #
    # Edit category/launcher/rom asset.
    #
    # NOTE Scrapers are loaded by the _command_edit_* functions (caller of this function).
    # NOTE When editing ROMs optional parameter launcher_dic is required.
    # NOTE Caller is responsible for saving the Categories/Launchers/ROMs.
    # NOTE if image is changed container should be updated so the user sees new image instantly.
    # NOTE object_dic is edited by assigment.
    # NOTE A ROM in Favourites has categoryID = VCATEGORY_FAVOURITES_ID.
    #      a ROM in a collection categoryID = VCATEGORY_COLLECTIONS_ID.
    #
    # Returns:
    #   True   Changes made. Categories/Launchers/ROMs must be saved and container updated
    #   False  No changes were made. No necessary to refresh container
    #
    def _gui_edit_asset(self, object_kind, asset_kind, object_dic, categoryID = '', launcherID = ''):
        # --- Get asset object information ---
        # Select/Import require: object_name, A, asset_path_noext
        #
        # Scraper additionaly requires: current_asset_path, scraper_obj, platform, rom_base_noext
        #
        if object_kind == KIND_CATEGORY:
            # --- Grab asset information for editing ---
            object_name = 'Category'
            A = assets_get_info_scheme(asset_kind)
            asset_directory = self.settings['categories_asset_dir']
            asset_path_noext = assets_get_path_noext_SUFIX(A, asset_directory, object_dic['m_name'])
            log_info('_gui_edit_asset() Editing Category "{0}"'.format(A.name))
            log_info('_gui_edit_asset() id {0}'.format(object_dic['id']))
            log_debug('_gui_edit_asset() asset_directory  "{0}"'.format(asset_directory))
            log_debug('_gui_edit_asset() asset_path_noext "{0}"'.format(asset_path_noext))
            if not asset_directory:
                kodi_dialog_OK('Directory to store Category artwork not configured. '
                               'Configure it before you can edit artwork.')
                return False

        elif object_kind == KIND_COLLECTION:
            # --- Grab asset information for editing ---
            object_name = 'Collection'
            A = assets_get_info_scheme(asset_kind)
            asset_directory = self.settings['collections_asset_dir']
            asset_path_noext = assets_get_path_noext_SUFIX(A, asset_directory, object_dic['name'])
            log_info('_gui_edit_asset() Editing Collection "{0}"'.format(A.name))
            log_info('_gui_edit_asset() id {0}'.format(object_dic['id']))
            log_debug('_gui_edit_asset() asset_directory  "{0}"'.format(asset_directory))
            log_debug('_gui_edit_asset() asset_path_noext "{0}"'.format(asset_path_noext))
            if not asset_directory:
                kodi_dialog_OK('Directory to store Collection artwork not configured. '
                               'Configure it before you can edit artwork.')
                return False

        elif object_kind == KIND_LAUNCHER:
            # --- Grab asset information for editing ---
            object_name = 'Launcher'
            A = assets_get_info_scheme(asset_kind)
            asset_directory = self.settings['launchers_asset_dir']
            asset_path_noext = assets_get_path_noext_SUFIX(A, asset_directory, object_dic['m_name'])
            log_info('_gui_edit_asset() Editing Launcher "{0}"'.format(A.name))
            log_info('_gui_edit_asset() id {0}'.format(object_dic['id']))
            log_debug('_gui_edit_asset() asset_directory  "{0}"'.format(asset_directory))
            log_debug('_gui_edit_asset() asset_path_noext "{0}"'.format(asset_path_noext))
            if not asset_directory:
                kodi_dialog_OK('Directory to store Launcher artwork not configured. '
                               'Configure it before you can edit artwork.')
                return False

        elif object_kind == KIND_ROM:
            # --- Grab asset information for editing ---
            object_name = 'ROM'
            ROM = misc_split_path(object_dic['filename'])
            A   = assets_get_info_scheme(asset_kind)
            if categoryID == VCATEGORY_FAVOURITES_ID:
                log_info('_gui_edit_asset() ROM is in Favourites')
                asset_directory = self.settings['favourites_asset_dir']
                platform        = object_dic['platform']
                asset_path_noext = assets_get_path_noext_SUFIX(A, asset_directory, ROM.base_noext)
            else:
                log_info('_gui_edit_asset() ROM is in Launcher (id {0})'.format(launcherID))
                launcher        = self.launchers[launcherID]
                asset_directory = launcher[A.path_key]
                platform        = launcher['platform']
                asset_path_noext = assets_get_path_noext_DIR(A, asset_directory, ROM.base_noext)
            current_asset_path = object_dic[A.key]
            scraper_obj = self.scraper_asset
            rom_base_noext = ROM.base_noext
            log_info('_gui_edit_asset() Editing ROM {0}'.format(A.name))
            log_info('_gui_edit_asset() id {0}'.format(object_dic['id']))
            log_debug('_gui_edit_asset() asset_directory    "{0}"'.format(asset_directory))
            log_debug('_gui_edit_asset() asset_path_noext   "{0}"'.format(asset_path_noext))
            log_debug('_gui_edit_asset() current_asset_path "{0}"'.format(current_asset_path))            
            log_debug('_gui_edit_asset() scraper            "{0}"'.format(scraper_obj.name))
            log_debug('_gui_edit_asset() platform           "{0}"'.format(platform))
            log_debug('_gui_edit_asset() rom_base_noext     "{0}"'.format(rom_base_noext))

            # --- Do not edit asset if asset directory not configured ---            
            if not asset_directory:
                kodi_dialog_OK('Directory to store {0} not configured. '.format(A.name) + \
                               'Configure it before you can edit artwork.')
                return False

        else:
            log_error('_gui_edit_asset() Unknown object_kind = {0}'.format(object_kind))
            kodi_notify_warn("Unknown object_kind '{0}'".format(object_kind))
            return False

        # --- Only enable scraper if support the asset ---
        scraper_enabled = False
        if scraper_obj.supports_asset(asset_kind):
            scraper_enabled = True
            log_verb('Scraper {0} support scraping {1}'.format(scraper_obj.name, A.name))
        else:
            log_verb('Scraper {0} does not support scraping {1}'.format(scraper_obj.name, A.name))
            log_verb('Scraper DISABLED')

        # --- Show image editing options ---
        # >> Scrape only supported for ROMs (for the moment)
        dialog = xbmcgui.Dialog()
        if object_kind == KIND_ROM and scraper_enabled:
            type2 = dialog.select('Change {0} {1}'.format(A.name, A.kind_str),
                                 ['Select local {0}'.format(A.kind_str, A.kind_str),
                                  'Import local {0} (copy and rename)'.format(A.kind_str),
                                  'Scrape {0} from {1}'.format(A.name, scraper_obj.name)])
        else:
            type2 = dialog.select('Change {0} {1}'.format(A.name, A.kind_str),
                                 ['Select local {0}'.format(A.kind_str, A.kind_str),
                                  'Import local {0} (copy and rename)'.format(A.kind_str)])

        # --- Link to a local image ---
        if type2 == 0:
            image_dir = ''
            if object_dic[A.key] != '':
                F = misc_split_path(object_dic[A.key])
                image_dir = F.dirname
            log_debug('_gui_edit_asset() Initial path "{0}"'.format(image_dir))
            # >> ShowAndGetFile dialog
            dialog = xbmcgui.Dialog()
            if asset_kind == ASSET_MANUAL or asset_kind == ASSET_TRAILER:
                image_file = dialog.browse(1, 'Select {0} {1}'.format(A.name, A.kind_str), 'files',
                                           A.exts_dialog, True, False, image_dir)

            # >> ShowAndGetImage dialog
            else:
                image_file = dialog.browse(2, 'Select {0} {1}'.format(A.name, A.kind_str), 'files',
                                           A.exts_dialog, True, False, image_dir)
            if not image_file or not os.path.isfile(image_file): return False

            # --- Update object by assigment. XML/JSON will be save by parent ---
            object_dic[A.key] = image_file
            kodi_notify('{0} has been updated'.format(A.name))
            log_info('_gui_edit_asset() Linked {0} {1} "{2}"'.format(object_name, A.name, image_file))

            # --- Update Kodi image cache ---
            kodi_update_image_cache(image_file)

        # --- Import an image ---
        # >> Copy and rename a local image into asset directory
        elif type2 == 1:
            image_dir = ''
            if object_dic[A.key] != '':
                F = misc_split_path(object_dic[A.key])
                image_dir = F.dirname
            log_debug('_gui_edit_asset() Initial path "{0}"'.format(image_dir))
            image_file = xbmcgui.Dialog().browse(2, 'Select {0} image'.format(A.name), 'files',
                                                 A.exts_dialog, True, False, image_dir)
            if not image_file or not os.path.isfile(image_file): return False

            # Determine image extension and dest filename
            F = misc_split_path(image_file)
            dest_path = A.path_noext + F.ext
            log_debug('_gui_edit_asset() image_file   "{0}"'.format(image_file))
            log_debug('_gui_edit_asset() img_ext      "{0}"'.format(F.ext))
            log_debug('_gui_edit_asset() dest_path    "{0}"'.format(dest_path))

            # Copy image file
            if image_file == dest_path:
                log_info('_gui_edit_asset() image_file and dest_path are the same. Returning')
                return False
            try:
                fs_encoding = get_fs_encoding()
                shutil.copy(image_file.decode(fs_encoding, 'ignore') , dest_path.decode(fs_encoding, 'ignore'))
            except OSError:
                log_error('_gui_edit_asset() OSError exception copying image')
                kodi_notify_warn('OSError exception copying image')
                return False
            except IOError:
                log_error('_gui_edit_asset() IOError exception copying image')
                kodi_notify_warn('IOError exception copying image')
                return False

            # Update object by assigment. XML will be save by parent
            object_dic[A.key] = dest_path
            kodi_notify('{0} has been updated'.format(A.name))
            log_info('_gui_edit_asset() Copied file  "{0}"'.format(image_file))
            log_info('_gui_edit_asset() Into         "{0}"'.format(dest_path))
            log_info('_gui_edit_asset() Selected {0} {1} "{2}"'.format(object_name, A.name, dest_path))

            # --- Update Kodi image cache ---
            kodi_update_image_cache(dest_path)

        # --- Manual scrape and choose from a list of images ---
        # >> Copy asset scrape code into here and remove function _gui_scrap_image_semiautomatic()
        elif type2 == 2:
            # --- Ask user to edit the image search string ---
            keyboard = xbmc.Keyboard(object_dic['m_name'], 'Enter the string to search for...')
            keyboard.doModal()
            if not keyboard.isConfirmed(): return False
            search_string = keyboard.getText().decode('utf-8')

            # --- Call scraper and get a list of games ---
            # IMPORTANT Setting Kodi busy notification prevents the user to control the UI when a dialog with handler -1
            #           has been called and nothing is displayed.
            #           THIS PREVENTS THE RACE CONDITIONS THAT CAUSE TROUBLE IN ADVANCED LAUNCHER!!!
            kodi_busydialog_ON()
            results = scraper_obj.get_search(search_string, rom_base_noext, platform)
            kodi_busydialog_OFF()
            log_debug('{0} scraper found {1} result/s'.format(A.name, len(results)))
            if not results:
                kodi_dialog_OK('Scraper found no matches.')
                log_debug('{0} scraper did not found any game'.format(A.name))
                return False

            # --- Choose game to download image ---
            # Display corresponding game list found so user choses
            dialog = xbmcgui.Dialog()
            rom_name_list = []
            for game in results:
                rom_name_list.append(game['display_name'])
            selectgame = dialog.select('Select game for {0}'.format(search_string), rom_name_list)
            if selectgame < 0: return False

            # --- Grab list of images for the selected game ---
            # >> Prevent race conditions
            kodi_busydialog_ON()
            image_list = scraper_obj.get_images(results[selectgame], asset_kind)
            kodi_busydialog_OFF()
            log_verb('{0} scraper returned {1} images'.format(A.name, len(image_list)))
            if not image_list:
                kodi_dialog_OK('Scraper found no images.')
                return False

            # --- Always do semi-automatic scraping when editing images ---
            # If there is a local image add it to the list and show it to the user
            if os.path.isfile(current_asset_path):
                image_list.insert(0, {'name' : 'Current local image', 
                                      'URL' : current_asset_path, 'disp_URL' : current_asset_path })

            # Returns a list of dictionaries {'name', 'URL', 'disp_URL'}
            image_url = gui_show_image_select(image_list)
            log_debug('{0} dialog returned image_url "{1}"'.format(A.name, image_url))
            if image_url == '': image_url = image_list[0]['URL']

            # --- If user chose the local image don't download anything ---
            if image_url != current_asset_path:
                # ~~~ Download scraped image ~~~
                # Get Tumb/Fanart name with no extension, then get URL image extension
                # and make full thumb path. If extension cannot be determined
                # from URL defaul to '.jpg'
                img_ext          = text_get_image_URL_extension(image_url) # Includes front dot -> .jpg
                image_local_path = asset_path_noext + img_ext

                # ~~~ Download image ~~~
                log_debug('asset_path_noext "{0}"'.format(asset_path_noext))
                log_debug('img_ext          "{0}"'.format(img_ext))
                log_verb('Downloading URL  "{0}"'.format(image_url))
                log_verb('Into local file  "{0}"'.format(image_local_path))
                # >> Prevent race conditions
                kodi_busydialog_ON()
                try:
                    net_download_img(image_url, image_local_path)
                except socket.timeout:
                    kodi_notify_warn('Cannot download {0} image (Timeout)'.format(image_name))
                kodi_busydialog_OFF()

                # ~~~ Update Kodi cache with downloaded image ~~~
                # Recache only if local image is in the Kodi cache, this function takes care of that.
                kodi_update_image_cache(image_local_path)
            else:
                log_debug('Scraper: user chose local image "{1}"'.format(current_asset_path))
                return False

            # --- Edit using Python pass by assigment ---
            # >> Caller is responsible to save Categories/Launchers/ROMs
            object_dic[A.key] = image_local_path

        # --- User canceled select box ---
        elif type2 < 0:
            return False

        # >> If we reach this point, changes were made.
        # >> Categories/Launchers/ROMs must be saved, container must be refreshed.
        return True

    #
    # Creates default categories data struct.
    # CAREFUL deletes current categories!
    #
    def _cat_create_default(self):
        # The key in the categories dictionary is an MD5 hash generate with current time plus some random number.
        # This will make it unique and different for every category created.
        category = fs_new_category()
        category_key = misc_generate_random_SID()
        category['id']      = category_key
        category['m_name']  = 'Emulators'
        category['m_genre'] = 'Emulators'
        category['m_plot']  = 'Initial AEL category.'
        # category['m_rating'] = '10'
        self.categories = {}
        self.categories[category_key] = category

    #
    # Checks if the category is empty (no launchers defined)
    #
    def _cat_is_empty(self, categoryID):
        empty_category = True
        for cat in self.launchers.iterkeys():
            if self.launchers[cat]['categoryID'] == categoryID:
                empty_category = False

        return empty_category

    #
    # Reads a text file with category/launcher description. Checks file size to avoid importing binary files!
    #
    def _gui_import_TXT_file(text_file):
        # Warn user in case he chose a binary file or a very big one. Avoid categories.xml corruption.
        log_debug('_gui_import_TXT_file() Importing plot from "{0}"'.format(text_file))
        statinfo = os.stat(text_file)
        file_size = statinfo.st_size
        log_debug('_gui_import_TXT_file() File size is {0}'.format(file_size))
        if file_size > 16384:
            ret = kodi_dialog_yesno('File "{0}" has {1} bytes and it is very big.'.format(text_file, file_size) +
                                    'Are you sure this is the correct file?')
            if not ret: return ''

        # Import file
        log_debug('_gui_import_TXT_file() Importing description from "{0}"'.format(text_file))
        text_plot = open(text_file, 'rt')
        file_data = text_plot.read()
        text_plot.close()

        return file_data

    #
    # A set of functions to help making plugin URLs
    # NOTE probably this can be implemented in a more elegant way with optinal arguments...
    #
    def _misc_url_RunPlugin(self, command, categoryID = None, launcherID = None, romID = None):
        if romID is not None:
            return 'XBMC.RunPlugin({0}?com={1}&catID={2}&launID={3}&romID={4})'.format(self.base_url, command, categoryID, launcherID, romID)
        elif launcherID is not None:
            return 'XBMC.RunPlugin({0}?com={1}&catID={2}&launID={3})'.format(self.base_url, command, categoryID, launcherID)
        elif categoryID is not None:
            return 'XBMC.RunPlugin({0}?com={1}&catID={2})'.format(self.base_url, command, categoryID)

        return 'XBMC.RunPlugin({0}?com={1})'.format(self.base_url, command)

    def _misc_url(self, command, categoryID = None, launcherID = None, romID = None):
        if romID is not None:
            return '{0}?com={1}&catID={2}&launID={3}&romID={4}'.format(self.base_url, command, categoryID, launcherID, romID)
        elif launcherID is not None:
            return '{0}?com={1}&catID={2}&launID={3}'.format(self.base_url, command, categoryID, launcherID)
        elif categoryID is not None:
            return '{0}?com={1}&catID={2}'.format(self.base_url, command, categoryID)

        return '{0}?com={1}'.format(self.base_url, command)

    def _misc_url_search(self, command, categoryID, launcherID, search_type, search_string):
        return '{0}?com={1}&catID={2}&launID={3}&search_type={4}&search_string={5}'.format(
            self.base_url, command, categoryID, launcherID, search_type, search_string)

# -------------------------------------------------------------------------------------------------
# Custom class dialog for an image selection window
# -------------------------------------------------------------------------------------------------
# NOTE Found another example of a custom listitem dialog in the Favourites script
#      ~/.kodi/addons/script.favourites
#
# Release - Image Resource selection script (NOTE is a script, not an addon!)
# See http://forum.kodi.tv/showthread.php?tid=239558
# See https://github.com/ronie/script.image.resource.select/blob/master/default.py
#
# >> From DialogSelect.xml in Confluence (Kodi Krypton taken from Github master)
# >> https://github.com/xbmc/skin.confluence/blob/master/720p/DialogSelect.xml
# >> Controls 5 and 7 are grouped
#
# <control type="label"  id="1"> | <description>header label</description>      | Window title on top
# control 2 does not exist
# <control type="list"   id="3"> |                                              | Another container which I don't understand...
# <control type="label"  id="4"> | <description>No Settings Label</description>
# <control type="button" id="5"> | <description>Manual button</description>     | OK button
# <control type="list"   id="6"> |                                              | Listbox
# <control type="button" id="7"> | <description>Cancel button</description>     | New Krypton cancel button
#
class ImgSelectDialog(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)

        # >> Custom stuff
        self.listing = kwargs.get('listing')
        self.selected_url = ''

    def onInit(self):
        self.container = self.getControl(6)
        # >> Disables movement left-right in image listbox
        self.container.controlLeft(self.container)
        self.container.controlRight(self.container)

        # >> NOTE The mysterious control 7 is new in Kodi Krypton!
        # >> See http://forum.kodi.tv/showthread.php?tid=250936&pid=2246458#pid2246458
        # self.cancel = self.getControl(7) # Produces an error "RuntimeError: Non-Existent Control 7"
        # self.cancel.setLabel('Ajo')

        # >> Another container which I don't understand...
        self.getControl(3).setVisible(False)
        # >> Window title on top
        self.getControl(1).setLabel('Choose item')
        # >> OK button
        self.button = self.getControl(5)
        self.button.setVisible(False)
        # self.button.setLabel('Ar')

        # >> Add items to list
        listitems = []
        for index, item in enumerate(self.listing):
            name_str = item['name']
            URL_str  = item['disp_URL']
            listitem = xbmcgui.ListItem(label=name_str, label2=URL_str)
            listitem.setArt({'icon': 'DefaultAddonImages.png', 'thumb': URL_str})
            listitems.append(listitem)
        self.container.addItems(listitems)
        self.setFocus(self.container)

    def onAction(self, action):
        if action.getId() in (9, 10, 92, 216, 247, 257, 275, 61467, 61448):
            self.close()

    def onClick(self, controlID):
        if controlID == 6:
            # self.selected_url = self.container.getSelectedItem().getLabel2()
            num = self.container.getSelectedPosition()
            self.selected_url = self.listing[num]['URL']
            xbmc.sleep(100)
            self.close()

        elif controlID == 5:
            # xbmc.executebuiltin('ActivateWindow(AddonBrowser, addons://repository.xbmc.org/kodi.resource.images/,return)')
            xbmc.sleep(100)
            self.close()

        elif controlID == 7:
            self.close()

    def onFocus(self, controlID):
        pass

def gui_show_image_select(img_list):
    # The xml file needs to be part of your addon, or included in the skin you use.
    # Yes, DialogSelect.xml is defined in Confluence here
    # https://github.com/xbmc/skin.confluence/blob/master/720p/DialogSelect.xml
    w = ImgSelectDialog('DialogSelect.xml', BASE_DIR, listing = img_list)

    # Execute dialog
    w.doModal()
    selected_url = w.selected_url
    del w

    return selected_url

