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

# --- Main imports ---
import sys, os, shutil, fnmatch, string
import re, urllib, urllib2, urlparse, socket, exceptions, hashlib

# --- Kodi stuff ---
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

# --- Modules/packages in this plugin ---
import subprocess_hack
from disk_IO import *
from net_IO import *
from utils import *
from utils_kodi import *
from scrap import *

# --- Addon object (used to access settings) ---
addon_obj      = xbmcaddon.Addon()
__addon_id__   = addon_obj.getAddonInfo('id')
__addon_name__ = addon_obj.getAddonInfo('name')
__version__    = addon_obj.getAddonInfo('version')
__author__     = addon_obj.getAddonInfo('author')
__profile__    = addon_obj.getAddonInfo('profile')
__type__       = addon_obj.getAddonInfo('type')

# --- Addon paths and constant definition ---
# _FILE_PATH is a filename | _DIR is a directory (with trailing /)
PLUGIN_DATA_DIR       = xbmc.translatePath(os.path.join('special://profile/addon_data', __addon_id__)).decode('utf-8')
BASE_DIR              = xbmc.translatePath(os.path.join('special://', 'profile')).decode('utf-8')
HOME_DIR              = xbmc.translatePath(os.path.join('special://', 'home')).decode('utf-8')
KODI_FAV_FILE_PATH    = xbmc.translatePath('special://profile/favourites.xml').decode('utf-8')
ADDONS_DIR            = xbmc.translatePath(os.path.join(HOME_DIR, 'addons')).decode('utf-8')
CURRENT_ADDON_DIR     = xbmc.translatePath(os.path.join(ADDONS_DIR, __addon_id__)).decode('utf-8')
ICON_IMG_FILE_PATH    = os.path.join(CURRENT_ADDON_DIR, 'icon.png').decode('utf-8')
CATEGORIES_FILE_PATH  = os.path.join(PLUGIN_DATA_DIR, 'categories.xml').decode('utf-8')
FAV_XML_FILE_PATH     = os.path.join(PLUGIN_DATA_DIR, 'favourites.xml').decode('utf-8')
FAV_JSON_FILE_PATH    = os.path.join(PLUGIN_DATA_DIR, 'favourites.json').decode('utf-8')
VCAT_TITLE_FILE_PATH  = os.path.join(PLUGIN_DATA_DIR, 'vcat_title.xml').decode('utf-8')
VCAT_YEARS_FILE_PATH  = os.path.join(PLUGIN_DATA_DIR, 'vcat_years.xml').decode('utf-8')
VCAT_GENRE_FILE_PATH  = os.path.join(PLUGIN_DATA_DIR, 'vcat_genre.xml').decode('utf-8')
VCAT_STUDIO_FILE_PATH = os.path.join(PLUGIN_DATA_DIR, 'vcat_studio.xml').decode('utf-8')

# Artwork and NFO for Categories and Launchers
DEFAULT_CAT_THUMB_DIR   = os.path.join(PLUGIN_DATA_DIR, 'category-thumbs').decode('utf-8')
DEFAULT_CAT_FANART_DIR  = os.path.join(PLUGIN_DATA_DIR, 'category-fanarts').decode('utf-8')
DEFAULT_CAT_NFO_DIR     = os.path.join(PLUGIN_DATA_DIR, 'category-nfos').decode('utf-8')
DEFAULT_LAUN_THUMB_DIR  = os.path.join(PLUGIN_DATA_DIR, 'launcher-thumbs').decode('utf-8')
DEFAULT_LAUN_FANART_DIR = os.path.join(PLUGIN_DATA_DIR, 'launcher-fanarts').decode('utf-8')
DEFAULT_LAUN_NFO_DIR    = os.path.join(PLUGIN_DATA_DIR, 'launcher-nfos').decode('utf-8')
DEFAULT_FAV_THUMB_DIR   = os.path.join(PLUGIN_DATA_DIR, 'favourite-thumbs').decode('utf-8')
DEFAULT_FAV_FANART_DIR  = os.path.join(PLUGIN_DATA_DIR, 'favourite-fanarts').decode('utf-8')
VIRTUAL_CAT_TITLE_DIR   = os.path.join(PLUGIN_DATA_DIR, 'db_title').decode('utf-8')
VIRTUAL_CAT_YEARS_DIR   = os.path.join(PLUGIN_DATA_DIR, 'db_years').decode('utf-8')
VIRTUAL_CAT_GENRE_DIR   = os.path.join(PLUGIN_DATA_DIR, 'db_genre').decode('utf-8')
VIRTUAL_CAT_STUDIO_DIR  = os.path.join(PLUGIN_DATA_DIR, 'db_studio').decode('utf-8')
ROMS_DIR                = os.path.join(PLUGIN_DATA_DIR, 'ROMs').decode('utf-8')

# Misc "constants"
KIND_CATEGORY       = 0
KIND_LAUNCHER       = 1
KIND_ROM            = 2
IMAGE_THUMB         = 100
IMAGE_FANART        = 200
DESCRIPTION_MAXSIZE = 40
IMG_EXTS            = [u'png', u'jpg', u'gif', u'jpeg', u'bmp', u'PNG', u'JPG', u'GIF', u'JPEG', u'BMP']
VCATEGORY_FAV_ID    = 'vcat_fav'
VCATEGORY_TITLE_ID  = 'vcat_title'
VCATEGORY_YEARS_ID  = 'vcat_years'
VCATEGORY_GENRE_ID  = 'vcat_genre'
VCATEGORY_STUDIO_ID = 'vcat_studio'
VLAUNCHER_FAV_ID    = 'vlauncher_fav'

# --- Main code ---
class Main:
    update_timestamp = 0.0
    settings         = {}
    categories       = {}
    launchers        = {}
    roms             = {}
    scraper_metadata = None
    scraper_thumb    = None
    scraper_fanart   = None

    #
    # This is the plugin entry point.
    #
    def run_plugin(self):
        # --- Initialise log system ---
        # Force DEBUG log level for development.
        # Place it before setting loading so settings can be dumped during debugging.
        # set_log_level(LOG_DEBUG)

        # --- Fill in settings dictionary using addon_obj.getSetting() ---
        self._get_settings()
        set_log_level(self.settings['log_level'])

        # --- Some debug stuff for development ---
        log_debug('---------- Called AEL addon.py Main() constructor ----------')
        log_debug(sys.version.replace('\n', ''))
        # log_debug('__addon_name__ {0}'.format(__addon_name__))
        log_debug('__addon_id__   {0}'.format(__addon_id__))
        log_debug('__version__    {0}'.format(__version__))
        # log_debug('__author__     {0}'.format(__author__))
        log_debug('__profile__    {0}'.format(__profile__))
        # log_debug('__type__       {0}'.format(__type__))
        for i in range(len(sys.argv)):
            log_debug('sys.argv[{0}] = "{1}"'.format(i, sys.argv[i]))
        # log_debug('PLUGIN_DATA_DIR      = "{0}"'.format(PLUGIN_DATA_DIR))
        # log_debug('CURRENT_ADDON_DIR    = "{0}"'.format(CURRENT_ADDON_DIR))
        # log_debug('CATEGORIES_FILE_PATH = "{0}"'.format(CATEGORIES_FILE_PATH))
        # log_debug('FAVOURITES_FILE_PATH = "{0}"'.format(FAVOURITES_FILE_PATH))

        # --- Addon data paths creation ---
        if not os.path.isdir(PLUGIN_DATA_DIR):         os.makedirs(PLUGIN_DATA_DIR)
        if not os.path.isdir(DEFAULT_CAT_THUMB_DIR):   os.makedirs(DEFAULT_CAT_THUMB_DIR)
        if not os.path.isdir(DEFAULT_CAT_FANART_DIR):  os.makedirs(DEFAULT_CAT_FANART_DIR)
        if not os.path.isdir(DEFAULT_CAT_NFO_DIR):     os.makedirs(DEFAULT_CAT_NFO_DIR)
        if not os.path.isdir(DEFAULT_LAUN_THUMB_DIR):  os.makedirs(DEFAULT_LAUN_THUMB_DIR)
        if not os.path.isdir(DEFAULT_LAUN_FANART_DIR): os.makedirs(DEFAULT_LAUN_FANART_DIR)
        if not os.path.isdir(DEFAULT_LAUN_NFO_DIR):    os.makedirs(DEFAULT_LAUN_NFO_DIR)
        if not os.path.isdir(DEFAULT_FAV_THUMB_DIR):   os.makedirs(DEFAULT_FAV_THUMB_DIR)
        if not os.path.isdir(DEFAULT_FAV_FANART_DIR):  os.makedirs(DEFAULT_FAV_FANART_DIR)
        if not os.path.isdir(VIRTUAL_CAT_TITLE_DIR):   os.makedirs(VIRTUAL_CAT_TITLE_DIR)
        if not os.path.isdir(VIRTUAL_CAT_YEARS_DIR):   os.makedirs(VIRTUAL_CAT_YEARS_DIR)
        if not os.path.isdir(VIRTUAL_CAT_GENRE_DIR):   os.makedirs(VIRTUAL_CAT_GENRE_DIR)
        if not os.path.isdir(VIRTUAL_CAT_STUDIO_DIR):  os.makedirs(VIRTUAL_CAT_STUDIO_DIR)
        if not os.path.isdir(ROMS_DIR):                os.makedirs(ROMS_DIR)

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

        # --- Set content type and sorting methods ---
        # NOTE This code should be move to _gui_* functions which generate
        #      list. Do not place it here because not all commands of the module
        #      need it!
        # Experiment to try to increase the number of views the addon supports. I do not know why
        # programs does not support all views movies do.
        # xbmcplugin.setContent(handle=self.addon_handle, content = 'movies')

        # Adds a sorting method for the media list.
        if self.addon_handle > 0:
            xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
            xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)
            xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_STUDIO)
            xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_GENRE)
            xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)

        # --- Addon first-time initialisation ---
        # When the addon is installed and the file categories.xml does not exist, just
        # create an empty one with a default launcher.
        if not os.path.isfile(CATEGORIES_FILE_PATH):
            kodi_dialog_OK('Advanced Emulator Launcher',
                           'It looks it is the first time you run Advanced Emulator Launcher! ' +
                           'A default categories.xml has been created. You can now customise it to your needs.')
            self._cat_create_default()
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

        # --- Load categories.xml and fill categories and launchers dictionaries ---
        (self.update_timestamp, self.categories, self.launchers) = fs_load_catfile(CATEGORIES_FILE_PATH)

        # --- Load scrapers ---
        self._load_scrapers()

        # If no com parameter display categories. Display categories listbox (addon root directory)
        if 'com' not in args:
            self._command_render_categories()
            log_debug('AEL exiting after rendering Categories (addon root)')
            return

        # There is a command to process
        # For some reason args['com'] is a list, so get first element of the list (a string)
        command = args['com'][0]
        if command == 'ADD_CATEGORY':
            self._command_add_new_category()
        elif command == 'EDIT_CATEGORY':
            self._command_edit_category(args['catID'][0])
        elif command == 'SHOW_FAVOURITES':
            self._command_render_favourites()
        elif command == 'SHOW_VIRTUAL_CATEGORY':
            self._command_render_virtual_category(args['catID'][0])
        elif command == 'SHOW_LAUNCHERS':
            self._command_render_launchers(args['catID'][0])
        elif command == 'ADD_LAUNCHER':
            self._command_add_new_launcher(args['catID'][0])
        elif command == 'EDIT_LAUNCHER':
            self._command_edit_launcher(args['launID'][0])
        # User clicked on a launcher. For standalone launchers run the executable.
        # For emulator launchers show roms.
        elif command == 'SHOW_ROMS':
            launcherID = args['launID'][0]
            # >> Virtual launcher in virtual category (years/genres/studios)
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
        elif args['com'][0] == 'LAUNCH_ROM':
            self._command_run_rom(args['catID'][0], args['launID'][0], args['romID'][0])
        elif command == 'ADD_TO_FAV':
            self._command_add_to_favourites(args['catID'][0], args['launID'][0], args['romID'][0])
        elif command == 'CHECK_FAV':
            self._command_check_favourites(args['catID'][0], args['launID'][0], args['romID'][0])
        # This command is issued when user clicks on "Search" on the context menu of a launcher
        # in the launchers view, or context menu inside a launcher. User is asked to enter the
        # search string and the field to search (name, category, etc.)
        elif command == 'SEARCH_LAUNCHER':
            self._command_search_launcher(args['catID'][0], args['launID'][0])
        elif command == 'EXEC_SEARCH_LAUNCHER':
            self._command_execute_search_launcher(args['catID'][0], args['launID'][0],
                                                  args['search_type'][0], args['search_string'][0])
        # >> Shows info about categories/launchers/ROMs
        elif command == 'VIEW_ROM':
            self._command_view_ROM(args['catID'][0], args['launID'][0], args['romID'][0])
        # >> Update virtual categories databases
        elif command == 'UPDATE_VIRTUAL_CATEGORY':
            self._command_update_virtual_category_db(args['catID'][0])
        elif command == 'UPDATE_ALL_VCATEGORIES':
            self._command_update_virtual_category_db_all()
        elif command == 'IMPORT_AL_LAUNCHERS':
            self._command_import_legacy_AL()
        else:
            kodi_dialog_OK('Advanced Emulator Launcher - ERROR', 'Unknown command {0}'.format(args['com'][0]) )

        log_debug('Advanced Emulator Launcher exit')

    #
    # Get Addon Settings
    #
    def _get_settings( self ):
        # Get the users preference settings
        self.settings = {}

        # --- Scanner settings ---
        self.settings["scan_recursive"]             = True if addon_obj.getSetting("scan_recursive") == "true" else False
        self.settings["scan_ignore_bios"]           = True if addon_obj.getSetting("scan_ignore_bios") == "true" else False
        self.settings["scan_metadata_policy"]       = int(addon_obj.getSetting("scan_metadata_policy"))
        self.settings["scan_thumb_policy"]          = int(addon_obj.getSetting("scan_thumb_policy"))
        self.settings["scan_fanart_policy"]         = int(addon_obj.getSetting("scan_fanart_policy"))
        self.settings["scan_ignore_scrapped_title"] = True if addon_obj.getSetting("scan_ignore_scrapped_title") == "true" else False
        self.settings["scan_clean_tags"]            = True if addon_obj.getSetting("scan_clean_tags") == "true" else False

        self.settings["metadata_scraper"]       = int(addon_obj.getSetting("metadata_scraper"))
        self.settings["thumb_scraper"]          = int(addon_obj.getSetting("thumb_scraper"))
        self.settings["fanart_scraper"]         = int(addon_obj.getSetting("fanart_scraper"))
        self.settings["metadata_mode"]          = int(addon_obj.getSetting("metadata_mode"))
        self.settings["thumb_mode"]             = int(addon_obj.getSetting("thumb_mode"))
        self.settings["fanart_mode"]            = int(addon_obj.getSetting("fanart_mode"))

        self.settings["scraper_region"]         = int(addon_obj.getSetting("scraper_region"))
        self.settings["scraper_thumb_size"]     = int(addon_obj.getSetting("scraper_thumb_size"))
        self.settings["scraper_fanart_size"]    = int(addon_obj.getSetting("scraper_fanart_size"))
        self.settings["scraper_image_type"]     = int(addon_obj.getSetting("scraper_image_type"))
        self.settings["scraper_fanart_order"]   = int(addon_obj.getSetting("scraper_fanart_order"))

        self.settings["display_launcher_notification"] = True if addon_obj.getSetting("display_launcher_notification") == "true" else False
        self.settings["display_hide_finished"]         = True if addon_obj.getSetting("display_hide_finished") == "true" else False
        self.settings["display_hide_title"]            = True if addon_obj.getSetting("display_hide_title") == "true" else False
        self.settings["display_hide_year"]             = True if addon_obj.getSetting("display_hide_year") == "true" else False
        self.settings["display_hide_genre"]            = True if addon_obj.getSetting("display_hide_genre") == "true" else False
        self.settings["display_hide_studio"]           = True if addon_obj.getSetting("display_hide_studio") == "true" else False

        self.settings["categories_thumb_dir"]  = addon_obj.getSetting("categories_thumb_dir").decode('utf-8')
        self.settings["categories_fanart_dir"] = addon_obj.getSetting("categories_fanart_dir").decode('utf-8')
        self.settings["categories_nfo_dir"]    = addon_obj.getSetting("categories_nfo_dir").decode('utf-8')
        self.settings["launchers_thumb_dir"]   = addon_obj.getSetting("launchers_thumb_dir").decode('utf-8')
        self.settings["launchers_fanart_dir"]  = addon_obj.getSetting("launchers_fanart_dir").decode('utf-8')
        self.settings["launchers_nfo_dir"]     = addon_obj.getSetting("launchers_nfo_dir").decode('utf-8')
        self.settings["favourites_thumb_dir"]  = addon_obj.getSetting("favourites_thumb_dir").decode('utf-8')
        self.settings["favourites_fanart_dir"] = addon_obj.getSetting("favourites_fanart_dir").decode('utf-8')

        self.settings["media_state"]            = int(addon_obj.getSetting("media_state"))
        self.settings["lirc_state"]             = True if addon_obj.getSetting("lirc_state") == "true" else False
        self.settings["start_tempo"]            = int(round(float(addon_obj.getSetting("start_tempo"))))
        self.settings["log_level"]              = int(addon_obj.getSetting("log_level"))
        self.settings["show_batch_window"]      = True if addon_obj.getSetting("show_batch_window") == "true" else False

        # --- Example of how to transform a number into string ---
        # self.settings["game_region"]          = ['World', 'Europe', 'Japan', 'USA'][int(addon_obj.getSetting('game_region'))]

        # Check if user changed default artwork paths for categories/launchers. If not, set defaults.
        if self.settings['categories_thumb_dir']  == '': self.settings['categories_thumb_dir']  = DEFAULT_CAT_THUMB_DIR
        if self.settings['categories_fanart_dir'] == '': self.settings['categories_fanart_dir'] = DEFAULT_CAT_FANART_DIR
        if self.settings['categories_nfo_dir']    == '': self.settings['categories_nfo_dir']    = DEFAULT_CAT_NFO_DIR
        if self.settings['launchers_thumb_dir']   == '': self.settings['launchers_thumb_dir']   = DEFAULT_LAUN_THUMB_DIR
        if self.settings['launchers_fanart_dir']  == '': self.settings['launchers_fanart_dir']  = DEFAULT_LAUN_FANART_DIR
        if self.settings['launchers_nfo_dir']     == '': self.settings['launchers_nfo_dir']     = DEFAULT_LAUN_NFO_DIR
        if self.settings['favourites_thumb_dir']  == '': self.settings['favourites_thumb_dir']  = DEFAULT_FAV_THUMB_DIR
        if self.settings['favourites_fanart_dir'] == '': self.settings['favourites_fanart_dir'] = DEFAULT_FAV_FANART_DIR

        # --- Dump settings for DEBUG ---
        # log_debug('Settings dump BEGIN')
        # for key in sorted(self.settings):
        #     log_debug('{0} --> {1:10s} {2}'.format(key.rjust(21), str(self.settings[key]), type(self.settings[key])))
        # log_debug('Settings dump END')

    #
    # Load scrapers based on the user settings.
    # Pass settings to the scraper objects based on user preferences.
    #
    def _load_scrapers(self):
        # Scraper objects are created and inserted into a list. This list order matches
        # exactly the number returned by the settings. If scrapers are changed make sure the
        # list in scrapers.py and in settings.xml have same values!
        self.scraper_metadata = scrapers_metadata[self.settings["metadata_scraper"]]
        self.scraper_thumb    = scrapers_thumb[self.settings["thumb_scraper"]]
        self.scraper_fanart   = scrapers_fanart[self.settings["fanart_scraper"]]
        log_verb('Loaded metadata scraper  {0}'.format(self.scraper_metadata.name))
        log_verb('Loaded thumb scraper     {0}'.format(self.scraper_thumb.name))
        log_verb('Loaded fanart scraper    {0}'.format(self.scraper_fanart.name))

        # Initialise metadata scraper plugin installation dir, for offline scrapers
        self.scraper_metadata.set_addon_dir(CURRENT_ADDON_DIR)

        # Initialise options of the thumb scraper
        region  = self.settings['scraper_region']
        thumb_imgsize = self.settings['scraper_thumb_size']
        self.scraper_thumb.set_options(region, thumb_imgsize)

        # Initialise options of the fanart scraper
        fanart_imgsize = self.settings['scraper_fanart_size']
        self.scraper_fanart.set_options(region, fanart_imgsize)

    def _command_add_new_category(self):
        dialog = xbmcgui.Dialog()
        keyboard = xbmc.Keyboard('', 'New Category Name')
        keyboard.doModal()
        if not keyboard.isConfirmed():
            return False

        category = fs_new_category()
        categoryID = misc_generate_random_SID()
        category['id']   = categoryID
        category['name'] = keyboard.getText()
        self.categories[categoryID] = category
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
        kodi_notify('Advanced Emulator Launcher', 'Category {0} created'.format(category['name']))
        kodi_refresh_container()

    def _command_edit_category(self, categoryID):
        # Shows a select box with the options to edit
        dialog = xbmcgui.Dialog()
        finished_display = 'Status: Finished' if self.categories[categoryID]['finished'] == True else 'Status: Unfinished'
        type = dialog.select('Select action for category {0}'.format(self.categories[categoryID]['name']),
                             ['Edit Title/Genre/Description...', 'Edit Thumbnail Image...', 'Edit Fanart Image...',
                              finished_display, 'Delete Category'])
        # Edit metadata
        if type == 0:
            desc_str = text_limit_string(self.categories[categoryID]['description'], DESCRIPTION_MAXSIZE)
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Edit Category Metadata',
                                  [u"Edit Title: '{0}'".format(self.categories[categoryID]['name']),
                                   u"Edit Genre: '{0}'".format(self.categories[categoryID]['genre']),
                                   u"Edit Description: '{0}'".format(desc_str),
                                   'Import Description from file...' ])
            # Edition of the category name
            if type2 == 0:
                keyboard = xbmc.Keyboard(self.categories[categoryID]['name'], 'Edit Title')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    title = keyboard.getText()
                    if title == '':
                        title = self.categories[categoryID]['name']
                    self.categories[categoryID]['name'] = title.rstrip()
                else:
                    kodi_dialog_OK('Advanced Emulator Launcher - Information',
                                   "Category name '{0}' not changed".format(self.categories[categoryID]['name']))
                    return
            # Edition of the category genre
            elif type2 == 1:
                keyboard = xbmc.Keyboard(self.categories[categoryID]['genre'], 'Edit Genre')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    self.categories[categoryID]['genre'] = keyboard.getText()
                else:
                    kodi_dialog_OK('Advanced Emulator Launcher - Information',
                                   "Category genre '{0}' not changed".format(self.categories[categoryID]['genre']))
                    return
            # Edition of the plot (description)
            elif type2 == 2:
                keyboard = xbmc.Keyboard(self.categories[categoryID]['description'], 'Edit Description')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    self.categories[categoryID]['description'] = keyboard.getText()
                else:
                    kodi_dialog_OK('Advanced Emulator Launcher - Information',
                                   "Category description '{0}' not changed".format(self.categories[categoryID]['description']))
                    return
            # Import category description
            elif type2 == 3:
                text_file = xbmcgui.Dialog().browse(1, 'Select description file (TXT|DAT)', 'files', '.txt|.dat', False, False)
                if os.path.isfile(text_file):
                    file_data = self._gui_import_TXT_file(text_file)
                    if file_data != '':
                        self.categories[categoryID]["description"] = file_data
                    else:
                        return
                else:
                    desc_str = text_limit_string(self.categories[categoryID]['description'], DESCRIPTION_MAXSIZE)
                    kodi_dialog_OK('Advanced Emulator Launcher - Information',
                                   "Category description '{0}' not changed".format(desc_str))
                    return

        # Edit Thumbnail image
        # If this function returns False no changes were made. No need to save categories XML and update container.
        elif type == 1:
            if not self._gui_edit_category_image(IMAGE_THUMB, categoryID):
                return

        # Launcher Fanart menu option
        elif type == 2:
            if not self._gui_edit_category_image(IMAGE_FANART, categoryID):
                return

        # Category status
        elif type == 3:
            finished = self.categories[categoryID]["finished"]
            finished = False if finished else True
            finished_display = 'Finished' if finished == True else 'Unfinished'
            self.categories[categoryID]["finished"] = finished
            kodi_dialog_OK('Advanced Emulator Launcher',
                           'Category "{0}" status is now {1}'.format(self.categories[categoryID]["name"], finished_display))

        # Remove cateogory
        elif type == 4:
            if not self._gui_remove_category(categoryID):
                return

        # User pressed cancel or close dialog
        elif type < 0:
            return

        # >> If this point is reached then changes to metadata/images were made.
        # >> Save categories and update container contents so user sees those changes inmediately.
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
        kodi_refresh_container()

    #
    # Removes a category. Also removes all launchers in this category!
    # Returns:
    #   True   Changes made, save XML and update container.
    #   False  No changes made.
    #
    def _gui_remove_category(self, categoryID):
        launcherID_list = []
        category_name = self.categories[categoryID]["name"]
        for launcherID in sorted(self.launchers.iterkeys()):
            if self.launchers[launcherID]['categoryID'] == categoryID:
                launcherID_list.append(launcherID)

        dialog = xbmcgui.Dialog()
        if len(launcherID_list) > 0:
            ret = dialog.yesno('Advanced Emulator Launcher',
                               'Category "{0}" contains {1} launchers. '.format(category_name, len(launcherID_list)) +
                               'Deleting it will also delete related launchers. ' +
                               'Are you sure you want to delete "{0}"?'.format(category_name) )
            if ret:
                log_info('Deleting category "{0}" id {1}'.format(category_name, categoryID))
                # Delete launchers and ROM XML associated with them
                for launcherID in launcherID_list:
                    log_info('Deleting linked launcher "{0}" id {1}'.format(self.launchers[launcherID]['name'], launcherID))
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
                return False
        else:
            ret = dialog.yesno('Advanced Emulator Launcher',
                               'Category "{0}" contains {1} launchers. '.format(category_name, len(launcherID_list)) +
                               'Are you sure you want to delete "{0}"?'.format(category_name) )
            if ret:
                log_info('Deleting category "{0}" id {1}'.format(category_name, categoryID))
                log_info('Category has no launchers, so no launchers to delete.')
                self.categories.pop(categoryID)
            else:
                return False

        return True

    def _command_add_new_launcher(self, categoryID):
        # If categoryID not found return to plugin root window.
        if categoryID not in self.categories:
            kodi_notify_warn('Advanced Emulator Launcher', 'Category ID not found.')
            return

        # Show "Create New Launcher" dialog
        dialog = xbmcgui.Dialog()
        type = dialog.select('Create New Launcher',
                             ['Files launcher (game emulator)', 'Standalone launcher (normal executable)'])
        log_info('_command_add_new_launcher() New launcher type = {0}'.format(type))
        filter = '.bat|.exe|.cmd|.lnk' if sys.platform == 'win32' else ''

        # 'Files launcher (game emulator)'
        if type == 0:
            app = xbmcgui.Dialog().browse(1, 'Select the launcher application', "files", filter)
            if not app: return

            files_path = xbmcgui.Dialog().browse(0, 'Select the ROMs path', "files", "")
            if not files_path: return

            extensions = emudata_get_program_extensions(os.path.basename(app))
            extkey = xbmc.Keyboard(extensions, 'Set files extensions, use "|" as separator. (e.g lnk|cbr)')
            extkey.doModal()
            if not extkey.isConfirmed(): return
            ext = extkey.getText()

            default_arguments = emudata_get_program_arguments(os.path.basename(app))
            argkeyboard = xbmc.Keyboard(default_arguments, 'Application arguments')
            argkeyboard.doModal()
            if not argkeyboard.isConfirmed(): return
            args = argkeyboard.getText()

            title = os.path.basename(app)
            keyboard = xbmc.Keyboard(title.replace('.'+title.split('.')[-1],'').replace('.',' '), 'Set the title of the launcher')
            keyboard.doModal()
            title = keyboard.getText()
            if title == "":
                title = os.path.basename(app)
                title = title.replace('.'+title.split('.')[-1],'').replace('.',' ')

            # Selection of the launcher game system
            dialog = xbmcgui.Dialog()
            sel_platform = dialog.select('Select the platform', AEL_platform_list)
            if sel_platform < 0: return
            launcher_platform = AEL_platform_list[sel_platform]

            # Selection of the thumbnails and fanarts path
            thumb_path = xbmcgui.Dialog().browse(0, 'Select Thumbnail path', 'files', '', False, False, files_path)
            fanart_path = xbmcgui.Dialog().browse(0, 'Select Fanart path', 'files', '', False, False, files_path)

            # --- Create launcher object data, add to dictionary and write XML file ---
            thumb_path  = '' if not thumb_path else thumb_path
            fanart_path = '' if not fanart_path else fanart_path

            # Choose launcher ROM XML filename. There may be launchers with same name in different categories, or 
            # even launcher with the same name in the same category.
            launcherID      = misc_generate_random_SID()
            category_name   = self.categories[categoryID]['name']
            roms_base_noext = fs_get_ROMs_basename(category_name, title, launcherID)

            # Create new launchers and save cateogories.xml
            launcherdata = fs_new_launcher()
            launcherdata['id']              = launcherID
            launcherdata['name']            = title
            launcherdata['categoryID']      = categoryID
            launcherdata['application']     = app
            launcherdata['args']            = args
            launcherdata['rompath']         = files_path
            launcherdata['thumbpath']       = thumb_path
            launcherdata['fanartpath']      = fanart_path
            launcherdata['romext']          = ext
            launcherdata['platform']        = launcher_platform
            launcherdata['roms_base_noext'] = roms_base_noext
            self.launchers[launcherID]      = launcherdata
            kodi_notify('Advanced Emulator Launcher', 'ROM launcher {0} created.'.format(title))

        # 'Standalone launcher (normal executable)'
        elif type == 1:
            app = xbmcgui.Dialog().browse(1, 'Select the launcher application', "files", filter)
            if not app: return

            argument = ''
            argkeyboard = xbmc.Keyboard(argument, 'Application arguments')
            argkeyboard.doModal()
            args = argkeyboard.getText()

            title = os.path.basename(app)
            keyboard = xbmc.Keyboard(title.replace('.'+title.split('.')[-1],'').replace('.',' '), 'Set the title of the launcher')
            keyboard.doModal()
            title = keyboard.getText()
            if title == '':
                title = os.path.basename(app)
                title = title.replace('.' + title.split('.')[-1], '').replace('.', ' ')

            # Selection of the launcher game system
            dialog = xbmcgui.Dialog()
            sel_platform = dialog.select('Select the platform', AEL_platform_list)
            if sel_platform < 0: return
            launcher_platform = AEL_platform_list[sel_platform]

            # --- Selection of the thumbnails and fanarts path ---
            thumb_path  = self.settings['launchers_thumb_dir']
            fanart_path = self.settings['launchers_fanart_dir']

            # --- Create launcher object data, add to dictionary and write XML file ---
            if not thumb_path:  thumb_path = ''
            if not fanart_path: fanart_path = ''

            # add launcher to the launchers dictionary (using name as index)
            launcherID = misc_generate_random_SID()
            launcherdata = fs_new_launcher()
            launcherdata['id']          = launcherID
            launcherdata['name']        = title
            launcherdata['categoryID']  = categoryID
            launcherdata['application'] = app
            launcherdata['args']        = args
            launcherdata['thumbpath']   = thumb_path
            launcherdata['fanartpath']  = fanart_path
            launcherdata['platform']    = launcher_platform
            self.launchers[launcherID]  = launcherdata
            kodi_notify('Advanced Emulator Launcher', 'App launcher {0} created.'.format(title))

        # >> If this point is reached then changes to metadata/images were made.
        # >> Save categories and update container contents so user sees those changes inmediately.
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
        kodi_refresh_container()

    def _command_edit_launcher(self, launcherID):
        dialog = xbmcgui.Dialog()
        title = os.path.basename(self.launchers[launcherID]['name'])
        finished_display = 'Status : Finished' if self.launchers[launcherID]["finished"] == True else 'Status : Unfinished'
        category_name = self.categories[self.launchers[launcherID]["categoryID"]]['name']
        if self.launchers[launcherID]['rompath'] == '':
            type = dialog.select('Select Action for launcher %s' % title,
                                 ['Modify Metadata...', 'Change Thumbnail Image...', 'Change Fanart Image...',
                                  'Change Category: {0}'.format(category_name),
                                  finished_display, 'Advanced Modifications...', 'Delete'])
        else:
            type = dialog.select('Select Action for launcher %s' % title,
                                 ['Modify Metadata...', 'Change Thumbnail Image...', 'Change Fanart Image...',
                                  'Change Category: {0}'.format(category_name),
                                  finished_display, 'Manage ROM List...', 'Advanced Modifications...', 'Delete'])

        # --- Edition of the launcher metadata ---
        type_nb = 0
        if type == type_nb:
            dialog = xbmcgui.Dialog()
            desc_str = text_limit_string(self.launchers[launcherID]['plot'], DESCRIPTION_MAXSIZE)
            type2 = dialog.select('Modify Launcher Metadata',
                                  [u'Scrape from {0}...'.format(self.scraper_metadata.fancy_name),
                                   u'Import metadata from NFO file',
                                   u"Edit Title: '{0}'".format(self.launchers[launcherID]['name']),
                                   u"Edit Platform: {0}".format(self.launchers[launcherID]['platform']),
                                   u"Edit Release Year: '{0}'".format(self.launchers[launcherID]['year']),
                                   u"Edit Studio: '{0}'".format(self.launchers[launcherID]['studio']),
                                   u"Edit Genre: '{0}'".format(self.launchers[launcherID]['genre']),
                                   u"Edit Description: '{0}'".format(desc_str),
                                   u'Import Description from file...',
                                   u'Save metadata to NFO file'])
            # Scrape launcher metadata
            if type2 == 0:
                if not self._gui_scrap_launcher_metadata(launcherID): return

            # Import launcher metadata from NFO file
            elif type2 == 1:
                # >> Launcher is edited using Python passing by assigment
                if not fs_import_launcher_NFO(self.settings, self.launchers, launcherID): return

            # Edition of the launcher name
            elif type2 == 2:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]['name'], 'Edit title')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                title = keyboard.getText()
                if title == '':
                    title = self.launchers[launcherID]['name']
                self.launchers[launcherID]['name'] = title.rstrip()

            # Selection of the launcher platform from AEL "official" list
            elif type2 == 3:
                dialog = xbmcgui.Dialog()
                sel_platform = dialog.select('Select the platform', AEL_platform_list)
                if sel_platform < 0: return
                self.launchers[launcherID]['platform'] = AEL_platform_list[sel_platform]

            # Edition of the launcher release date (year)
            elif type2 == 4:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]['year'], 'Edit release year')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                self.launchers[launcherID]["year"] = keyboard.getText()

            # Edition of the launcher studio name
            elif type2 == 5:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["studio"], 'Edit studio')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                self.launchers[launcherID]["studio"] = keyboard.getText()

            # Edition of the launcher genre
            elif type2 == 6:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["genre"], 'Edit genre')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                self.launchers[launcherID]["genre"] = keyboard.getText()

            # Edit launcher description (plot)
            elif type2 == 7:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["plot"], 'Edit descripion')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                self.launchers[launcherID]["plot"] = keyboard.getText()

            # Import of the launcher descripion (plot)
            elif type2 == 8:
                text_file = xbmcgui.Dialog().browse(1, 'Select description file (TXT|DAT)', 'files', '.txt|.dat', False, False)
                if os.path.isfile(text_file) == True:
                    file_data = self._gui_import_TXT_file(text_file)
                    self.launchers[launcherID]["plot"] = file_data
                else:
                    desc_str = text_limit_string(self.launchers[launcherID]["plot"], DESCRIPTION_MAXSIZE)
                    kodi_dialog_OK('Advanced Emulator Launcher - Information',
                                   "Launcher plot '{0}' not changed".format(desc_str))
                    return
            # Export launcher metadata to NFO file
            elif type2 == 9:
                fs_export_launcher_NFO(self.settings, self.launchers[launcherID])
                # >> No need to save launchers
                return

            # >> User canceled select dialog
            elif type2 < 0:
                return

        # Launcher Thumbnail menu option
        type_nb = type_nb + 1
        if type == type_nb:
            # >> Returns True if image was changed
            # >> Launcher is change using Python passign by assigment
            if not self._gui_edit_image(IMAGE_THUMB, KIND_LAUNCHER, self.launchers, launcherID): return

        # Launcher Fanart menu option
        type_nb = type_nb + 1
        if type == type_nb:
            if not self._gui_edit_image(IMAGE_FANART, KIND_LAUNCHER, self.launchers, launcherID): return

        # Change launcher's Category
        type_nb = type_nb + 1
        if type == type_nb:
            # >> Category of the launcher we are editing now
            old_categoryID = self.launchers[launcherID]['categoryID']

            # If only one Category there is nothing to change
            if len(self.categories) == 1:
                kodi_dialog_OK('Advanced Emulator Launcher', 'There is only one category. Nothing to change.')
                return
            dialog = xbmcgui.Dialog()
            categories_id = []
            categories_name = []
            for key in self.categories:
                categories_id.append(self.categories[key]['id'])
                categories_name.append(self.categories[key]['name'])
            selected_cat = dialog.select('Select the category', categories_name)
            if selected_cat < 0: return
            self.launchers[launcherID]['categoryID'] = categories_id[selected_cat]
            
            # >> If the former category is empty after editing (no launchers) then replace category window 
            # >> with addon root
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
            kodi_dialog_OK('Advanced Emulator Launcher',
                           'Launcher "{0}" status is now {1}'.format(self.launchers[launcherID]['name'], finished_display))

        # Launcher's Manage ROMs menu option
        # ONLY for ROM launchers, not for standalone launchers
        if self.launchers[launcherID]['rompath'] != '':
            type_nb = type_nb + 1
            if type == type_nb:
                dialog = xbmcgui.Dialog()
                has_NoIntro_DAT = True if self.launchers[launcherID]['nointro_xml_file'] else False
                if has_NoIntro_DAT:
                    nointro_xml_file = self.launchers[launcherID]['nointro_xml_file']
                    add_delete_NoIntro_str = 'Delete No-Intro DAT: {0}'.format(nointro_xml_file)
                else:
                    add_delete_NoIntro_str = 'Add No-Intro XML DAT...'
                type2 = dialog.select('Manage Items List',
                                      [add_delete_NoIntro_str, 
                                       'Audit ROMs using No-Intro XML PClone DAT',
                                       'Clear No-Intro audit status',
                                       'Remove missing/dead ROMs',
                                       'Import ROMs metadata from NFO files',
                                       'Export ROMs metadata to NFO files',
                                       'Clear ROMs from launcher' ])

                # --- Add/Delete No-Intro XML parent-clone DAT ---
                if type2 == 0:
                    if has_NoIntro_DAT:
                        dialog = xbmcgui.Dialog()
                        ret = dialog.yesno('Advanced Emulator Launcher', 'Delete No-Intro DAT file?')
                        if not ret: return
                        self.launchers[launcherID]['nointro_xml_file'] = u''
                        kodi_dialog_OK('Advanced Emulator Launcher', 'Rescan your ROMs to remove No-Intro tags.')
                    else:
                        # Browse for No-Intro file
                        # BUG For some reason *.dat files are not shown on the dialog, but XML files are OK!!!
                        dat_file = xbmcgui.Dialog().browse(type = 1, heading = u'Select No-Intro XML DAT (XML|DAT)', 
                                                           s_shares = u'files', mask = u'.xml|.dat', useThumbs = False, treatAsFolder = False)
                        if not os.path.isfile(dat_file): return
                        self.launchers[launcherID]['nointro_xml_file'] = dat_file
                        kodi_dialog_OK('Advanced Emulator Launcher', 'DAT file successfully added. Audit your ROMs to update No-Intro status.')

                # --- Audit ROMs with No-Intro DAT ---
                # >> This code is similar to the one in the ROM scanner _roms_import_roms()
                elif type2 == 1:
                    # Check if No-Intro XML DAT exists
                    if not has_NoIntro_DAT:
                        kodi_dialog_OK('Advanced Emulator Launcher', 'No-Intro XML DAT not configured. Add one before ROM audit.')
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
                    kodi_notify('Advanced Emulator Launcher', 
                                'Audit finished. Have {0}/Miss {1}/Unknown {2}'.format(num_have, num_miss, num_unknown))

                    # ~~~ Save ROMs XML file ~~~
                    # >> Also save categories/launchers to update timestamp
                    fs_write_ROMs(ROMS_DIR, roms_base_noext, roms, self.launchers[launcherID])
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
                    return

                # --- Reset audit status ---
                elif type2 == 2:
                    # --- Load ROMs for this launcher ---
                    roms_base_noext = self.launchers[launcherID]['roms_base_noext']
                    roms = fs_load_ROMs(ROMS_DIR, roms_base_noext)
                    
                    self._roms_reset_NoIntro_status(roms)
                    kodi_notify('Advanced Emulator Launcher', 'No-Intro status reset')

                    # ~~~ Save ROMs XML file ~~~
                    # >> Also save categories/launchers to update timestamp
                    fs_write_ROMs(ROMS_DIR, roms_base_noext, roms, self.launchers[launcherID])
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
                    return

                # --- Remove dead ROMs ---
                elif type2 == 3:
                    ret = kodi_dialog_yesno('Advanced Emulator Launcher',
                                            'Are you sure you want to remove missing/dead ROMs?')
                    if not ret: return
                    
                    # --- Load ROMs for this launcher ---
                    roms_base_noext = self.launchers[launcherID]['roms_base_noext']
                    roms = fs_load_ROMs(ROMS_DIR, roms_base_noext)
                    
                    # --- Remove dead ROMs ---
                    num_removed_roms = self._roms_delete_missing_ROMs(roms)
                    kodi_notify('Advanced Emulator Launcher', 'Reset No-Intro status. Removed {0} missing ROMs'.format(num_removed_roms))

                    # ~~~ Save ROMs XML file ~~~
                    # >> Also save categories/launchers to update timestamp
                    fs_write_ROMs(ROMS_DIR, roms_base_noext, roms, self.launchers[launcherID])
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
                    return

                # --- Import Items list form NFO files ---
                elif type2 == 4:
                    # >> Load ROMs, iterate and import NFO files
                    roms_base_noext = self.launchers[launcherID]['roms_base_noext']
                    roms = fs_load_ROMs(ROMS_DIR, roms_base_noext)
                    # >> Iterating dictionaries gives the key.
                    for rom_id in roms:
                        fs_import_ROM_NFO(roms, rom_id, verbose = False)
                    # >> Save ROMs XML file
                    # >> Also save categories/launchers to update timestamp
                    fs_write_ROMs(ROMS_DIR, roms_base_noext, roms, self.launchers[launcherID])
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
                    return

                # --- Export Items list to NFO files ---
                elif type2 == 5:
                    # >> Load ROMs for current launcher, iterate and write NFO files
                    roms = fs_load_ROMs(ROMS_DIR, self.launchers[launcherID]['roms_base_noext'])
                    if not roms: return
                    # >> Iterating dictionaries gives the key.
                    kodi_busydialog_ON()
                    for rom_id in roms:
                        fs_export_ROM_NFO(roms[rom_id], verbose = False)
                    kodi_busydialog_OFF()
                    # >> No need to save launchers XML / Update container
                    return

                # --- Empty Launcher menu option ---
                elif type2 == 6:
                    self._gui_empty_launcher(launcherID)
                    # _gui_empty_launcher calls ReplaceWindow/Container.Refresh. Return now to avoid the
                    # Container.Refresh at the end of this function and calling the plugin twice.
                    return

                elif type2 < 0:
                    # >> User canceled select dialog
                    return

        # --- Launcher Advanced Modifications menu option ---
        type_nb = type_nb + 1
        if type == type_nb:
            minimize_str = 'ON' if self.launchers[launcherID]['minimize'] == True else 'OFF'
            filter_str   = '.bat|.exe|.cmd' if sys.platform == 'win32' else ''

            # --- ROMS launcher -------------------------------------------------------------------
            if self.launchers[launcherID]['rompath'] == '':
                type2 = dialog.select('Advanced Modifications',
                                      [u"Change Application: '{0}'".format(self.launchers[launcherID]['application']),
                                       u"Modify Arguments: '{0}'".format(self.launchers[launcherID]['args']),
                                       u"Change Thumbs Path: '{0}'".format(self.launchers[launcherID]['thumbpath']),
                                       u"Change Fanarts Path: '{0}'".format(self.launchers[launcherID]['fanartpath']),
                                       u"Change Trailer file: '{0}'".format(self.launchers[launcherID]['trailerpath']),
                                       u"Change Extra-fanarts Path: '{0}'".format(self.launchers[launcherID]['custompath']),
                                       u"Toggle Kodi into Windowed mode: '{0}'".format(minimize_str) ])
            # --- Standalone launcher -------------------------------------------------------------
            else:
                type2 = dialog.select('Advanced Modifications',
                                      [u"Change Application: '{0}'".format(self.launchers[launcherID]['application']),
                                       u"Modify Arguments: '{0}'".format(self.launchers[launcherID]['args']),
                                       u"Change ROMs Path: '{0}'".format(self.launchers[launcherID]['rompath']),
                                       u"Modify ROM Extensions: '{0}'".format(self.launchers[launcherID]['romext']),
                                       u"Change Thumbs Path: '{0}'".format(self.launchers[launcherID]['thumbpath']),
                                       u"Change Fanarts Path: '{0}'".format(self.launchers[launcherID]['fanartpath']),
                                       u"Change Trailer file: '{0}'".format(self.launchers[launcherID]['trailerpath']),
                                       u"Change Extra-fanarts Path: '{0}'".format(self.launchers[launcherID]['custompath']),
                                       u"Toggle Kodi into Windowed mode: '{0}'".format(minimize_str) ])

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
                self.launchers[launcherID]['args'] = keyboard.getText()

            if self.launchers[launcherID]['rompath'] != '':
                # Launcher roms path menu option
                type2_nb = type2_nb + 1
                if type2 == type2_nb:
                    rom_path = xbmcgui.Dialog().browse(0, 'Select Files path', 'files', '',
                                                       False, False, self.launchers[launcherID]['rompath'])
                    self.launchers[launcherID]['rompath'] = rom_path

                # Edition of the launcher rom extensions (only for emulator launcher)
                type2_nb = type2_nb + 1
                if type2 == type2_nb:
                    keyboard = xbmc.Keyboard(self.launchers[launcherID]['romext'],
                                                'Edit ROM extensions, use &quot;|&quot; as separator. (e.g lnk|cbr)')
                    keyboard.doModal()
                    if not keyboard.isConfirmed(): return
                    self.launchers[launcherID]['romext'] = keyboard.getText()

            # Launcher thumbnails path menu option
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                thumb_path = xbmcgui.Dialog().browse(0, 'Select Thumbnails path', 'files', '',
                                                     False, False, self.launchers[launcherID]["thumbpath"])
                self.launchers[launcherID]['thumbpath'] = thumb_path

            # Launcher fanarts path menu option
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                fanart_path = xbmcgui.Dialog().browse(0, 'Select Fanarts path', 'files', '',
                                                      False, False, self.launchers[launcherID]['fanartpath'])
                self.launchers[launcherID]['fanartpath'] = fanart_path

            # Launcher trailer file menu option
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                fanart_path = xbmcgui.Dialog().browse(1, 'Select Trailer file', 'files',
                                                      '.mp4|.mpg|.avi|.wmv|.mkv|.flv', False, False,
                                                      self.launchers[launcherID]["trailerpath"])
                self.launchers[launcherID]['trailerpath'] = fanart_path

            # Launcher custom path menu option
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                fanart_path = xbmcgui.Dialog().browse(0, 'Select Extra-fanarts path', 'files', '', False, False,
                                                      self.launchers[launcherID]['custompath'])
                self.launchers[launcherID]['custompath'] = fanart_path

            # Launcher minimize state menu option
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                dialog = xbmcgui.Dialog()
                type3 = dialog.select('Toggle Kodi Fullscreen', ['OFF (default)', 'ON'])
                self.launchers[launcherID]['minimize'] = True if type3 == 1 else False

        # Remove Launcher menu option
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
            kodi_dialog_OK('Advanced Emulator Launcher',
                           'Launcher is empty. Nothing to do.')
            return

        # Confirm user wants to delete ROMs
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno('Advanced Emulator Launcher',
                           u"Launcher '{0}' has {1} ROMs. Are you sure you want to delete them " \
                            'from AEL database?'.format(self.launchers[launcherID]['name'], num_roms))
        if ret:
            # Just remove ROMs file. Keep the value of roms_base_noext to be reused when user add more ROMs.
            roms_base_noext = self.launchers[launcherID]['roms_base_noext']
            if roms_base_noext == '':
                log_info('Launcher roms_base_noext is empty "". No ROMs XML to remove')
            else:
                roms_file_path = fs_get_ROMs_file_path(ROMS_DIR, roms_base_noext)
                log_info(u'Removing ROMs XML "{0}"'.format(roms_file_path))
                try:
                    os.remove(roms_file_path)
                except OSError:
                    log_error(u'_gui_empty_launcher() OSError exception deleting "{0}"'.format(roms_file_path))
                    kodi_notify_warn('Advanced Emulator Launcher', 'OSError exception deleting ROMs database')
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            kodi_refresh_container()

    #
    # Removes a launcher. For ROMs launcher it also removes ROM XML. For standalone launcher there is no
    # files to remove and no ROMs to check.
    #
    def _gui_remove_launcher(self, launcherID):
        rompath = self.launchers[launcherID]['rompath']
        # Standalone launcher
        if rompath == '':
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher',
                               'Launcher "{0}" is standalone.'.format(self.launchers[launcherID]['name']),
                               'Are you sure you want to delete it?')
        # ROMs launcher
        else:
            roms = fs_load_ROMs(ROMS_DIR, self.launchers[launcherID]['roms_base_noext'])
            num_roms = len(roms)
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher',
                               'Launcher "{0}" has {1} ROMs'.format(self.launchers[launcherID]['name'], num_roms),
                               'Are you sure you want to delete it?')
        if ret:
            # Remove XML file and delete launcher object, only if launcher is not empty
            roms_base_noext = self.launchers[launcherID]['roms_base_noext']
            if roms_base_noext == '' or rompath == '':
                log_debug('Launcher is empty or standalone. No ROMs XML to remove')
            else:
                roms_file_path = fs_get_ROMs_file_path(ROMS_DIR, roms_base_noext)
                log_debug('Removing ROMs XML "{0}"'.format(roms_file_path))
                try:
                    os.remove(roms_file_path)
                except OSError:
                    log_error('_gui_remove_launcher() OSError exception deleting "{0}"'.format(roms_file_path))
                    kodi_notify_warn('Advanced Emulator Launcher', 'OSError exception deleting ROMs XML')

            categoryID = self.launchers[launcherID]['categoryID']
            self.launchers.pop(launcherID)
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            if self._cat_is_empty(categoryID):
                log_error('_gui_remove_launcher() Launcher category empty. Replacing Window')
                xbmc.executebuiltin('ReplaceWindow(Programs,%s)'.format(self.base_url))
            else:
                log_error('_gui_remove_launcher() Launcher category not empty. Container.Refresh()')
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
    # Note that categoryID = launcherID = '0' if we are editing a ROM in Favourites
    #
    def _command_edit_rom(self, categoryID, launcherID, romID):
        # --- Load ROMs ---
        if launcherID == VLAUNCHER_FAV_ID:
            # roms = fs_load_Favourites_XML(FAV_XML_FILE_PATH)
            roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
        else:
            roms_base_noext = self.launchers[launcherID]['roms_base_noext']
            roms = fs_load_ROMs(ROMS_DIR, roms_base_noext)

        # --- Show a dialog with ROM editing options ---
        title = roms[romID]['name']
        finished_display = 'Status: Finished' if roms[romID]['finished'] == True else 'Status: Unfinished'
        dialog = xbmcgui.Dialog()
        if launcherID == VLAUNCHER_FAV_ID:
            type = dialog.select('Edit Favourite ROM %s' % title,
                                ['Edit Metadata...', 'Change Thumbnail Image...', 'Change Fanart Image...',
                                finished_display, 'Advanced Modifications...',
                                'Choose another favourite parent ROM...'])
        else:
            type = dialog.select('Edit ROM %s' % title,
                                ['Edit Metadata...', 'Change Thumbnail Image...', 'Change Fanart Image...',
                                finished_display, 'Advanced Modifications...'])

        # --- Edit ROM metadata ---
        if type == 0:
            dialog = xbmcgui.Dialog()
            desc_str = text_limit_string(roms[romID]['plot'], DESCRIPTION_MAXSIZE)
            type2 = dialog.select('Modify ROM metadata',
                                  ['Scrape from {0}...'.format(self.scraper_metadata.fancy_name),
                                   'Import metadata from NFO file',
                                   "Edit Title: '{0}'".format(roms[romID]['name']),
                                   "Edit Release Year: '{0}'".format(roms[romID]['year']),
                                   "Edit Studio: '{0}'".format(roms[romID]['studio']),
                                   "Edit Genre: '{0}'".format(roms[romID]['genre']),
                                   "Edit Plot: '{0}'".format(desc_str),
                                   'Load Plot from TXT file ...',
                                   'Save metadata to NFO file'])
            # --- Scrap rom metadata ---
            if type2 == 0:
                # >> If this returns False there were no changes so no need to save ROMs XML.
                if not self._gui_scrap_rom_metadata(roms, romID, launcherID): return

            # Import ROM metadata from NFO file
            elif type2 == 1:
                if launcherID == VLAUNCHER_FAV_ID:
                    kodi_dialog_OK('Advanced Emulator Launcher',
                                   'Importing NFO file is not allowed for ROMs in Favourites.')
                    return
                if not fs_import_ROM_NFO(roms, romID): return

            # Edit of the rom title
            elif type2 == 2:
                keyboard = xbmc.Keyboard(roms[romID]["name"], 'Edit title')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                title = keyboard.getText()
                if title == "":
                    title = roms[romID]["name"]
                roms[romID]["name"] = title.rstrip()

            # Edition of the rom release year
            elif type2 == 3:
                keyboard = xbmc.Keyboard(roms[romID]["year"], 'Edit release year')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                roms[romID]["year"] = keyboard.getText()

            # Edition of the rom studio name
            elif type2 == 4:
                keyboard = xbmc.Keyboard(roms[romID]["studio"], 'Edit studio')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                roms[romID]["studio"] = keyboard.getText()

            # Edition of the rom game genre
            elif type2 == 5:
                keyboard = xbmc.Keyboard(roms[romID]["genre"], 'Edit genre')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                roms[romID]["genre"] = keyboard.getText()

            # Edit ROM description (plot)
            elif type2 == 6:
                keyboard = xbmc.Keyboard(roms[romID]['plot'], 'Edit plot')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                roms[romID]['plot'] = keyboard.getText()

            # Import of the rom game plot from TXT file
            elif type2 == 7:
                text_file = xbmcgui.Dialog().browse(1, 'Select description file (TXT|DAT)', "files", ".txt|.dat", False, False)
                if os.path.isfile(text_file):
                    file_data = self._gui_import_TXT_file(text_file)
                    roms[romID]['plot'] = file_data
                else:
                    desc_str = text_limit_string(roms[romID]["plot"], DESCRIPTION_MAXSIZE)
                    kodi_dialog_OK('Advanced Emulator Launcher - Information',
                                   "Launcher plot '{0}' not changed".format(desc_str))
                    return

            # Export ROM metadata to NFO file
            elif type2 == 8:
                if launcherID == VLAUNCHER_FAV_ID:
                    kodi_dialog_OK('Advanced Emulator Launcher',
                                   'Exporting NFO file is not allowed for ROMs in Favourites.')
                    return
                fs_export_ROM_NFO(roms[romID])
                # >> No need to save ROMs
                return

            # >> User canceled select dialog
            elif type2 < 0:
                return

        # Edit ROM thumb and fanart
        elif type == 1:
            # >> Returns True if image was changed
            # >> Launcher is change using Python passign by assigment
            if not self._gui_edit_image(IMAGE_THUMB, KIND_ROM, roms, romID, launcherID): return

        elif type == 2:
            if not self._gui_edit_image(IMAGE_FANART, KIND_ROM, roms, romID, launcherID): return

        # Edit status
        elif type == 3:
            finished = roms[romID]['finished']
            finished = False if finished else True
            finished_display = 'Finished' if finished == True else 'Unfinished'
            roms[romID]['finished'] = finished
            kodi_dialog_OK('Advanced Emulator Launcher Information',
                           'ROM "{0}" status is now {1}'.format(roms[romID]["name"], finished_display))

        # Advanced Modifications
        elif type == 4:
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Advanced Modifications',
                                  ['Change File : %s' % roms[romID]["filename"],
                                   'Alternative application : %s' % roms[romID]["altapp"],
                                   'Alternative arguments : %s' % roms[romID]["altarg"],
                                   'Change Trailer file : %s' % roms[romID]["trailer"],
                                   'Change Extra-fanarts Path : %s' % roms[romID]["custom"]])
            # Selection of the item file
            if type2 == 0:
                filename = roms[romID]['filename']
                romext   = roms[romID]['romext']
                item_file = xbmcgui.Dialog().browse(1, 'Select the file', 'files', "." + romext.replace("|", "|."),
                                                    False, False, filename)
                roms[romID]['filename'] = item_file
            # Custom launcher application file path
            elif type2 == 1:
                altapp = roms[romID]['altapp']
                filter_str = '.bat|.exe|.cmd' if sys.platform == "win32" else ''
                app = xbmcgui.Dialog().browse(1, 'Select ROM custom launcher application',
                                              "files", filter_str, False, False, altapp)
                # Returns empty browse if dialog was canceled.
                if not app: return
                roms[romID]["altapp"] = app
            # Custom launcher arguments
            elif type2 == 2:
                keyboard = xbmc.Keyboard(roms[romID]["altarg"], 'Edit ROM custom application arguments')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                roms[romID]["altarg"] = keyboard.getText()
            # Selection of the rom trailer file
            elif type2 == 3:
                trailer = xbmcgui.Dialog().browse(1, 'Select ROM Trailer file',
                                                  "files", ".mp4|.mpg|.avi|.wmv|.mkv|.flv",
                                                  False, False, roms[romID]["trailer"])
                if not app: return
                roms[romID]["trailer"] = trailer
            # Selection of the rom customs path
            elif type2 == 4:
                custom = xbmcgui.Dialog().browse(0, 'Select ROM Extra-fanarts path', "files", "",
                                                 False, False, roms[romID]["custom"])
                if not custom: return
                roms[romID]["custom"] = custom

            # >> User canceled select dialog
            elif type2 < 0:
                return

        # Link favourite ROM to a new parent ROM
        # ONLY IN FAVOURITE ROM EDITING
        elif type == 5:
            # STEP 1: select new launcher.
            launcher_IDs = []
            launcher_names = []
            for launcher_id in self.launchers:
                launcher_IDs.append(launcher_id)
                launcher_names.append(self.launchers[launcher_id]['name'])
                
            # Order alphabetically both lists
            sorted_idx = [i[0] for i in sorted(enumerate(launcher_names), key=lambda x:x[1])]
            launcher_IDs   = [launcher_IDs[i] for i in sorted_idx]
            launcher_names = [launcher_names[i] for i in sorted_idx]
            dialog = xbmcgui.Dialog()
            selected_launcher = dialog.select('New launcher for {0}'.format(roms[romID]['name']), launcher_names)
            if not selected_launcher == -1:
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
                    roms_names.append(launcher_roms[rom_id]['name'])
                sorted_idx = [i[0] for i in sorted(enumerate(roms_names), key=lambda x:x[1])]
                roms_IDs   = [roms_IDs[i] for i in sorted_idx]
                roms_names = [roms_names[i] for i in sorted_idx]
                selected_rom = dialog.select('New ROM for {0}'.format(roms[romID]['name']), roms_names)
                # Do the relinking and save favourites.
                if not selected_rom == -1:
                    launcher_rom_id = roms_IDs[selected_rom]
                    current_rom = launcher_roms[launcher_rom_id]
                    # Check that the selected ROM ID is not already in Favourites
                    if launcher_rom_id in roms:
                        kodi_dialog_OK('Advanced Emulator Launcher', 'Selected ROM already in Favourites. Exiting.')
                        return
                    # Delete current Favourite
                    roms.pop(romID)
                    # Copy parent ROM data files into favourite.
                    # Overwrite everything in Favourite ROM
                    roms[launcher_rom_id] = current_rom
                    roms[launcher_rom_id]['launcherID']  = self.launchers[launcher_id]['id']
                    roms[launcher_rom_id]['platform']    = self.launchers[launcher_id]['platform']
                    roms[launcher_rom_id]['application'] = self.launchers[launcher_id]['application']
                    roms[launcher_rom_id]['args']        = self.launchers[launcher_id]['args']
                    roms[launcher_rom_id]['rompath']     = self.launchers[launcher_id]['rompath']
                    roms[launcher_rom_id]['romext']      = self.launchers[launcher_id]['romext']
                    roms[launcher_rom_id]['fav_status']  = 'OK'
                    # If missing thumb/fanart then use launcher's
                    if roms[launcher_rom_id]['thumb']  == '': roms[launcher_rom_id]['thumb']  = self.launchers[launcher_id]['thumb']
                    if roms[launcher_rom_id]['fanart'] == '': roms[launcher_rom_id]['fanart'] = self.launchers[launcher_id]['fanart']

        # User canceled select dialog
        elif type < 0:
            return

        # --- Save ROMs or Favourites ROMs ---
        # Always save if we reach this point of the function
        if launcherID == VLAUNCHER_FAV_ID:
            # fs_write_Favourites_XML(FAV_XML_FILE_PATH, roms)
            fs_write_Favourites_JSON(FAV_JSON_FILE_PATH, roms)
        else:
            # >> Also save categories/launchers to update timestamp
            launcher = self.launchers[launcherID]
            roms_base_noext = self.launchers[launcherID]['roms_base_noext']
            fs_write_ROMs(ROMS_DIR, roms_base_noext, roms, self.launchers[launcherID])
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

        # It seems that updating the container does more harm than good... specially when having many ROMs
        # By the way, what is the difference between Container.Refresh() and Container.Update()?
        kodi_refresh_container()

    #
    # Deletes a ROM from a launcher.
    # If categoryID = launcherID = '0' then delete from Favourites
    #
    def _command_remove_rom(self, categoryID, launcherID, romID):
        if launcherID == VLAUNCHER_FAV_ID:
            # Load Favourite ROMs
            # roms = fs_load_Favourites_XML(FAV_XML_FILE_PATH)
            roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
            if not roms:
                return

            # Confirm deletion
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher - Delete from Favourites',
                               'ROM: {0}'.format(roms[romID]['name']),
                               'Are you sure you want to delete it from favourites?')
            if ret:
                roms.pop(romID)
                # fs_write_Favourites_XML(FAV_XML_FILE_PATH, roms)
                fs_write_Favourites_JSON(FAV_JSON_FILE_PATH, roms)
                kodi_notify('Advanced Emulator Launcher', 'Deleted ROM from Favourites')
                # If Favourites is empty then go to addon root, if not refresh
                if len(roms) == 0:
                    # For some reason ReplaceWindow() does not work...
                    xbmc.executebuiltin('ReplaceWindow(Programs,{0})'.format(self.base_url))
                else:
                    kodi_refresh_container()
        else:
            # --- Load ROMs ---
            roms = fs_load_ROMs(ROMS_DIR, self.launchers[launcherID]['roms_base_noext'])
            if not roms:
                return

            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher - Delete from Favourites',
                               'Launcher: {0}'.format(self.launchers[launcherID]['name']),
                               'ROM: {0}'.format(roms[romID]['name']),
                               'Are you sure you want to delete it from launcher?')
            if ret:
                roms.pop(romID)
                launcher = self.launchers[launcherID]
                # >> Also save categories/launchers to update timestamp
                roms_base_noext = launcher['roms_base_noext']
                fs_write_ROMs(ROMS_DIR, roms_base_noext, roms, launcher)
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
                kodi_notify('Advanced Emulator Launcher', 'Deleted ROM from launcher')
                # If launcher is empty then go to addon root, if not refresh
                if len(roms) == 0:
                    xbmc.executebuiltin('ReplaceWindow(Programs,{0})'.format(self.base_url))
                else:
                    kodi_refresh_container()

    #
    # Former _get_categories()
    # Renders the categories (addon root window)
    #
    def _command_render_categories(self):
        # For every category, add it to the listbox. Order alphabetically by name
        for key in sorted(self.categories, key= lambda x : self.categories[x]['name']):
            self._gui_render_category_row(self.categories[key], key)
        # --- AEL Favourites special category ---
        self._gui_render_category_favourites_row()
        if not self.settings['display_hide_title']:  self._gui_render_virtual_category_row(VCATEGORY_TITLE_ID)
        if not self.settings['display_hide_year']:   self._gui_render_virtual_category_row(VCATEGORY_YEARS_ID)
        if not self.settings['display_hide_genre']:  self._gui_render_virtual_category_row(VCATEGORY_GENRE_ID)
        if not self.settings['display_hide_studio']: self._gui_render_virtual_category_row(VCATEGORY_STUDIO_ID)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded=True, cacheToDisc=False )

    def _gui_render_category_row(self, category_dic, key):
        # --- Do not render row if category finished ---
        if category_dic['finished'] and self.settings['display_hide_finished']:
            return

        # --- Create listitem row ---
        icon = 'DefaultFolder.png'
        if category_dic['thumb'] != '':
            listitem = xbmcgui.ListItem(category_dic['name'], iconImage=icon, thumbnailImage=category_dic['thumb'] )
        else:
            listitem = xbmcgui.ListItem(category_dic['name'], iconImage=icon )
        if category_dic['finished'] == False: ICON_OVERLAY = 6
        else:                                 ICON_OVERLAY = 7
        listitem.setProperty('fanart_image', category_dic['fanart'])
        listitem.setInfo('video', {'Title': category_dic['name'],        'Genre' : category_dic['genre'],
                                   'Plot' : category_dic['description'], 'overlay': ICON_OVERLAY } )

        # --- Create context menu ---
        # To remove default entries like "Go to root", etc, see http://forum.kodi.tv/showthread.php?tid=227358
        commands = []
        categoryID = category_dic['id']
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY'), ))
        commands.append(('Edit Category',       self._misc_url_RunPlugin('EDIT_CATEGORY', categoryID), ))
        commands.append(('Add New Launcher',    self._misc_url_RunPlugin('ADD_LAUNCHER', categoryID), ))
        # Add Category to Kodi Favourites (do not know how to do it yet)
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', )) # If using window ID then use "10003"
        commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        listitem.addContextMenuItems(commands, replaceItems=True)

        # --- Add row ---
        url_str = self._misc_url('SHOW_LAUNCHERS', key)
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url=url_str, listitem=listitem, isFolder=True)

    def _gui_render_category_favourites_row(self):
        # --- Create listitem row ---
        fav_name = '<Favourites>'
        fav_thumb = ''
        fav_fanart = ''
        icon = 'DefaultFolder.png'
        listitem = xbmcgui.ListItem(fav_name, iconImage=icon, thumbnailImage=fav_thumb)
        listitem.setProperty('fanart_image', fav_fanart)
        listitem.setInfo('video', { 'Title': fav_name,             'Genre' : 'All',
                                    'Plot' : 'AEL Favourite ROMs', 'overlay': 7 } )

        # --- Create context menu ---
        commands = []
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY'), ))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', ))
        commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        listitem.addContextMenuItems(commands, replaceItems=True)

        # --- Add row ---
        url_str = self._misc_url('SHOW_FAVOURITES')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url=url_str, listitem=listitem, isFolder=True)

    def _gui_render_virtual_category_row(self, virtual_category_kind):
        if virtual_category_kind == VCATEGORY_TITLE_ID:
            vcategory_name   = '[Browse by Title]'
            vcategory_thumb  = ''
            vcategory_fanart = ''
            vcategory_label  = 'Title'
        elif virtual_category_kind == VCATEGORY_YEARS_ID:
            vcategory_name   = '[Browse by Year]'
            vcategory_thumb  = ''
            vcategory_fanart = ''
            vcategory_label  = 'Years'
        elif virtual_category_kind == VCATEGORY_GENRE_ID:
            vcategory_name   = '[Browse by Genre]'
            vcategory_thumb  = ''
            vcategory_fanart = ''
            vcategory_label  = 'Genre'
        elif virtual_category_kind == VCATEGORY_STUDIO_ID:
            vcategory_name   = '[Browse by Studio]'
            vcategory_thumb  = ''
            vcategory_fanart = ''
            vcategory_label  = 'Studio'
        else:
            log_error('_gui_render_virtual_category_row() Wrong virtual_category_kind = {0}'.format(virtual_category_kind))
            kodi_dialog_OK('AEL', 'Wrong virtual_category_kind = {0}'.format(virtual_category_kind))
            return
        icon = 'DefaultFolder.png'
        listitem = xbmcgui.ListItem(vcategory_name, iconImage=icon, thumbnailImage=vcategory_thumb)
        listitem.setProperty('fanart_image', vcategory_fanart)
        listitem.setInfo('video', { 'Title': vcategory_name,         'Genre' : 'All',
                                    'Plot' : 'AEL virtual category', 'overlay': 7 } )

        commands = []
        update_vcat_URL     = self._misc_url_RunPlugin('UPDATE_VIRTUAL_CATEGORY', virtual_category_kind)
        update_vcat_all_URL = self._misc_url_RunPlugin('UPDATE_ALL_VCATEGORIES')
        commands.append(('Update {0} database'.format(vcategory_label), update_vcat_URL, ))
        commands.append(('Update all databases'.format(vcategory_label), update_vcat_all_URL, ))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', ))
        commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        listitem.addContextMenuItems(commands, replaceItems=True)

        url_str = self._misc_url('SHOW_VIRTUAL_CATEGORY', virtual_category_kind)
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url=url_str, listitem=listitem, isFolder=True)

    #
    # Former  _get_launchers
    # Renders the launcher for a given category
    #
    def _command_render_launchers(self, categoryID):
        # --- If the category has no launchers then render nothing ---
        launcher_IDs = []
        for launcher_id in self.launchers:
            if self.launchers[launcher_id]['categoryID'] == categoryID: launcher_IDs.append(launcher_id)
        if not launcher_IDs:
            category_name = self.categories[categoryID]['name']
            kodi_notify('Advanced Emulator Launcher', 'Category {0} has no launchers. Add launchers first'.format(category_name))
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
            return

        # Render launcher rows of this launcher
        for key in sorted(self.launchers, key = lambda x : self.launchers[x]["application"]):
            if self.launchers[key]['categoryID'] == categoryID:
                self._gui_render_launcher_row(self.launchers[key])
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded=True, cacheToDisc=False )

    def _gui_render_launcher_row(self, launcher_dic):
        # --- Do not render row if launcher finished ---
        if launcher_dic['finished'] and self.settings['display_hide_finished']:
            return

        # --- Create listitem row ---
        if launcher_dic['rompath'] == '': # Executable launcher
            folder = False
            icon = 'DefaultProgram.png'
        else:                             # Files launcher
            folder = True
            icon = 'DefaultFolder.png'
        if launcher_dic['thumb']:
            listitem = xbmcgui.ListItem( launcher_dic['name'], iconImage=icon, thumbnailImage=launcher_dic['thumb'] )
        else:
            listitem = xbmcgui.ListItem( launcher_dic['name'], iconImage=icon )
        if launcher_dic['finished'] != True: ICON_OVERLAY = 6
        else:                                ICON_OVERLAY = 7
        listitem.setProperty('fanart_image', launcher_dic['fanart'])
        listitem.setInfo("video", {"Title"    : launcher_dic['name'],    "Label"     : os.path.basename(launcher_dic['rompath']),
                                   "Plot"     : launcher_dic['plot'],    "Studio"    : launcher_dic['studio'],
                                   "Genre"    : launcher_dic['genre'],   "Premiered" : launcher_dic['year'],
                                   "Year"     : launcher_dic['year'],    "Writer"    : launcher_dic['platform'],
                                   "Trailer"  : os.path.join(launcher_dic['trailerpath']),
                                   "Director" : os.path.join(launcher_dic['custompath']),
                                   "overlay"  : ICON_OVERLAY })

        # --- Create context menu ---
        commands = []
        launcherID = launcher_dic['id']
        categoryID = launcher_dic['categoryID']
        commands.append(('Create New Launcher', self._misc_url_RunPlugin('ADD_LAUNCHER', categoryID), ))
        commands.append(('Edit Launcher', self._misc_url_RunPlugin('EDIT_LAUNCHER', categoryID, launcherID), ))
        # ROMs launcher
        if not launcher_dic['rompath'] == '':
            commands.append(('Add ROMs', self._misc_url_RunPlugin('ADD_ROMS', categoryID, launcherID), ))
        commands.append(('Search ROMs in Launcher', self._misc_url_RunPlugin('SEARCH_LAUNCHER', categoryID, launcherID), ))
        # Add Launcher URL to Kodi Favourites (do not know how to do it yet)
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', )) # If using window ID then use "10003"
        commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        listitem.addContextMenuItems(commands, replaceItems=True)

        # --- Add row ---
        url_str = self._misc_url('SHOW_ROMS', categoryID, launcherID)
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url=url_str, listitem=listitem, isFolder=folder)

    #
    # Former  _get_roms
    # Renders the roms listbox for a given launcher
    #
    def _command_render_roms(self, categoryID, launcherID):
        if launcherID not in self.launchers:
            log_error('_command_render_roms() Launcher hash not found.')
            kodi_dialog_OK('Advanced Emulator Launcher - ERROR', 'Launcher hash not found.', '@_command_render_roms()')
            return

        # Load ROMs for this launcher and display them
        selectedLauncher = self.launchers[launcherID]
        roms_file_path = fs_get_ROMs_file_path(ROMS_DIR, selectedLauncher['roms_base_noext'])

        # Check if XML file with ROMs exist
        if not os.path.isfile(roms_file_path):
            kodi_notify('Advanced Emulator Launcher', 'Launcher XML missing. Add items to launcher.')
            kodi_refresh_container()
            return

        # --- Load ROMs ---
        roms = fs_load_ROMs(ROMS_DIR, selectedLauncher['roms_base_noext'])
        if not roms:
            kodi_notify('Advanced Emulator Launcher', 'Launcher XML empty. Add items to launcher.')
            kodi_refresh_container()
            return

        # Load favourites
        # roms_fav = fs_load_Favourites_XML(FAV_XML_FILE_PATH)
        roms_fav = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)

        # --- Display ROMs ---
        # Optimization Currently roms_fav is a dictionary, which is very fast when testing for element existence
        #              because it is hashed. However, set() is the fastest. If user has a lot of favourites
        #              there could be a small performance gain.
        for key in sorted(roms, key = lambda x : roms[x]['filename']):
            self._gui_render_rom_row(categoryID, launcherID, key, roms[key], key in roms_fav)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Former  _add_rom()
    # Note that if we are rendering favourites, categoryID = launcherID = '0'.
    #
    def _gui_render_rom_row(self, categoryID, launcherID, romID, rom, rom_is_in_favourites):
        # --- Do not render row if ROM is finished ---
        if rom['finished'] and self.settings['display_hide_finished']:
            return

        # --- Create listitem row ---
        icon = "DefaultProgram.png"
        # icon = "DefaultVideo.png"

        # If we are rendering Favourites then mark fav_status
        defined_fanart = u''
        platform = u''
        if categoryID == VCATEGORY_FAV_ID:
            defined_fanart = rom['fanart']
            platform = rom['platform']
            if rom['fav_status'] == 'OK':
                rom_name = '{0} [COLOR green][OK][/COLOR]'.format(rom['name'])
            elif rom['fav_status'] == 'Unlinked':
                rom_name = '{0} [COLOR yellow][Unlinked][/COLOR]'.format(rom['name'])
            elif rom['fav_status'] == 'Broken':
                rom_name = '{0} [COLOR red][Broken][/COLOR]'.format(rom['name'])
            else:
                rom_name = rom['name']
        # If rendering a virtual launcher mark nothing
        elif categoryID == VCATEGORY_TITLE_ID or categoryID == VCATEGORY_YEARS_ID or \
             categoryID == VCATEGORY_GENRE_ID or categoryID == VCATEGORY_STUDIO_ID:
            defined_fanart = rom['fanart']
            platform = rom['platform']
            rom_name = rom['name']
        # If rendering a normal launcher then mark nointro_status and rom_is_in_favourites
        else:
            # >> If ROM has no fanart then use launcher fanart
            defined_fanart = rom['fanart'] if rom['fanart'] != '' else self.launchers[launcherID]['fanart']
            platform = self.launchers[launcherID]['platform']
            # Mark No-Intro status
            if rom['nointro_status'] == 'Have':
                rom_name = '{0} [COLOR green][Have][/COLOR]'.format(rom['name'])
            elif rom['nointro_status'] == 'Miss':
                rom_name = '{0} [COLOR red][Miss][/COLOR]'.format(rom['name'])
            elif rom['nointro_status'] == 'Unknown':
                rom_name = '{0} [COLOR yellow][Unknown][/COLOR]'.format(rom['name'])
            else:
                rom_name = rom['name']

            # If listing regular launcher and rom is in favourites, mark it
            if rom_is_in_favourites:
                # log_debug('gui_render_rom_row() ROM is in favourites {0}'.format(rom_name))

                # --- Workaround so the alphabetical order is not lost ---
                # NOTE Missing ROMs must never be in favourites... However, mark them to help catching bugs.
                # rom_name = '[COLOR violet]{0} [Fav][/COLOR]'.format(rom['name'])
                # rom_name = '{0} [COLOR violet][Fav][/COLOR]'.format(rom['name'])
                rom_name += ' [COLOR violet][Fav][/COLOR]'
        
        # --- Add ROM to lisitem ---
        if rom['thumb']:
            listitem = xbmcgui.ListItem(rom['name'], rom['name'], iconImage=icon, thumbnailImage=rom['thumb'])
        else:
            listitem = xbmcgui.ListItem(rom['name'], rom['name'], iconImage=icon)
        if rom['finished'] is not True: ICON_OVERLAY = 6
        else:                           ICON_OVERLAY = 7
        listitem.setProperty('fanart_image', defined_fanart)

        # Interesting... if text formatting labels are set in xbmcgui.ListItem() do not work. However, if
        # labels are set as Title in setInfo(), then they work but the alphabetical order is lost!
        # I solved this alphabetical ordering issue by placing a coloured tag [Fav] at the and of the ROM name
        # instead of changing the whole row colour.
        listitem.setInfo("video", {"Title"   : rom_name,                     "Label"     : 'test label',
                                   "Plot"    : rom['plot'],                  "Studio"    : rom['studio'],
                                   "Genre"   : rom['genre'],                 "Premiered" : rom['year'],
                                   "Year"    : rom['year'],                  "Writer"    : platform,
                                   "Trailer" : os.path.join(rom['trailer']), "Director"  : os.path.join(rom['custom']),
                                   "overlay" : ICON_OVERLAY })

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
        if categoryID == VCATEGORY_FAV_ID:
            commands.append(('View Favourite ROM data', self._misc_url_RunPlugin('VIEW_ROM', VCATEGORY_FAV_ID, VLAUNCHER_FAV_ID, romID), ))
            commands.append(('Check Favourite ROMs', self._misc_url_RunPlugin('CHECK_FAV', VCATEGORY_FAV_ID, VLAUNCHER_FAV_ID, romID), ))
            commands.append(('Edit ROM in Favourites', self._misc_url_RunPlugin('EDIT_ROM', VCATEGORY_FAV_ID, VLAUNCHER_FAV_ID, romID), ))
            commands.append(('Search Favourites', self._misc_url_RunPlugin('SEARCH_LAUNCHER', VCATEGORY_FAV_ID, VLAUNCHER_FAV_ID), ))
            commands.append(('Delete ROM from Favourites', self._misc_url_RunPlugin('DELETE_ROM', VCATEGORY_FAV_ID, VLAUNCHER_FAV_ID, romID), ))
        elif categoryID == VCATEGORY_TITLE_ID or categoryID == VCATEGORY_YEARS_ID or \
             categoryID == VCATEGORY_GENRE_ID or categoryID == VCATEGORY_STUDIO_ID:
            commands.append(('View Virtual Launcher ROM data', self._misc_url_RunPlugin('VIEW_ROM', categoryID, launcherID, romID), ))
        else:
            commands.append(('View ROM data', self._misc_url_RunPlugin('VIEW_ROM', categoryID, launcherID, romID), ))
            commands.append(('Edit ROM', self._misc_url_RunPlugin('EDIT_ROM', categoryID, launcherID, romID), ))
            commands.append(('Search ROMs in Launcher', self._misc_url_RunPlugin('SEARCH_LAUNCHER', categoryID, launcherID), ))
            commands.append(('Add ROM to AEL Favourites', self._misc_url_RunPlugin('ADD_TO_FAV', categoryID, launcherID, romID), ))
            commands.append(('Delete ROM', self._misc_url_RunPlugin('DELETE_ROM', categoryID, launcherID, romID), ))
        # Add ROM URL to Kodi Favourites (do not know how to do it yet) (maybe not will be used)
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', )) # If using window ID then use "10003"
        commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        listitem.addContextMenuItems(commands, replaceItems = True)

        # --- Add row ---
        # URLs must be different depending on the content type. If not, lot of 
        # WARNING: CreateLoader - unsupported protocol(plugin) in the log. See http://forum.kodi.tv/showthread.php?tid=187954
        # if self._content_type == 'video':
        #     url_str = self._misc_url('LAUNCH_ROM', categoryID, launcherID, romID)
        # else:
        url_str = self._misc_url('LAUNCH_ROM', categoryID, launcherID, romID)
        xbmcplugin.addDirectoryItem(handle=self.addon_handle, url=url_str, listitem=listitem, isFolder=False)

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
        # --- Load favourites ---
        # roms_fav = fs_load_Favourites_XML(FAV_XML_FILE_PATH)
        roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
        if not roms:
            kodi_notify('Advanced Emulator Launcher', 'Favourites XML empty. Add items to favourites first')
            return

        # --- Display Favourites ---
        for key in sorted(roms, key= lambda x : roms[x]['filename']):
            self._gui_render_rom_row(VCATEGORY_FAV_ID, VLAUNCHER_FAV_ID, key, roms[key], False)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Render launchers in virtual categories: title, year, genre, studio
    #
    def _command_render_virtual_category(self, virtual_categoryID):
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
            kodi_dialog_OK('AEL', 'Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
            return

        # --- If the virtual category has no launchers then render nothing ---
        # >> Also, tell the user to update the virtual launcher database
        if not os.path.isfile(vcategory_db_filename):
            kodi_dialog_OK('Advanced Emulator Launcher',
                           '{0} database not found. '.format(vcategory_name) +
                           'Update the virtual category database first.')
            return

        # --- Load Virtual launchers XML file ---
        (VLauncher_timestamp, vcategory_launchers) = fs_load_VCategory_XML(vcategory_db_filename)

        # --- Check timestamps and warn user if database should be regenerated ---
        if VLauncher_timestamp < self.update_timestamp:
            kodi_dialog_OK('Advanced Emulator Launcher',
                           'Categories/Launchers/ROMs were modified. Virtual category database should be updated!')

        # --- Render virtual launchers rows ---
        icon = 'DefaultFolder.png'
        for vlauncher_id in vcategory_launchers:
            vlauncher = vcategory_launchers[vlauncher_id]
            vlauncher_name = vlauncher['name'] + '  ({0} ROM/s)'.format(vlauncher['rom_count'])
            # listitem = xbmcgui.ListItem( launcher_dic['name'], iconImage=icon, thumbnailImage=launcher_dic['thumb'] )
            listitem = xbmcgui.ListItem(vlauncher_name, iconImage = icon)
            # listitem.setProperty('fanart_image', launcher_dic['fanart'])
            listitem.setInfo('video', {"Title"    : 'Title text',
                                       "Label"    : 'Label text',
                                       "Plot"     : 'Plot text',  "Studio"    : 'Studio text',
                                       "Genre"    : 'Genre text', "Premiered" : 'Premiered text',
                                       "Year"     : 'Year text',  "Writer"    : 'Writer text',
                                       "Trailer"  : 'Trailer text',
                                       "Director" : 'Director text',
                                       "overlay"  : 7} )

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
            listitem.addContextMenuItems(commands, replaceItems=True)

            url_str = self._misc_url('SHOW_ROMS', virtual_categoryID, vlauncher_id)
            xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Renders ROMs in a virtual launcher.
    #
    def _command_render_virtual_launcher_roms(self, virtual_categoryID, virtual_launcherID):
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
            kodi_dialog_OK('AEL', 'Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
            return

        # --- Load Virtual Launcher DB ---
        hashed_db_filename = os.path.join(vcategory_db_dir, virtual_launcherID + '.json')
        if not os.path.isfile(hashed_db_filename):
            kodi_dialog_OK('AEL', 'Virtual launcher XML/JSON file not found.')
            return
        roms = fs_load_VCategory_ROMs_JSON(vcategory_db_dir, virtual_launcherID)
        if not roms:
            kodi_notify('Advanced Emulator Launcher', 'Virtual category ROMs XML empty. Add items to favourites first')
            return

        # --- Display Favourites ---
        for key in sorted(roms, key= lambda x : roms[x]['filename']):
            self._gui_render_rom_row(virtual_categoryID, virtual_launcherID, key, roms[key], False)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Adds ROM to favourites
    #
    def _command_add_to_favourites(self, categoryID, launcherID, romID):
        # Load ROMs in launcher
        launcher = self.launchers[launcherID]
        roms = fs_load_ROMs(ROMS_DIR, launcher['roms_base_noext'])
        if not roms:
            kodi_dialog_OK('Advanced Emulator Launcher',
                               'Empty roms launcher in _command_add_to_favourites()',
                               'This is a bug, please report it.')

        # Load favourites
        # roms_fav = fs_load_Favourites_XML(FAV_XML_FILE_PATH)
        roms_fav = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)

        # DEBUG
        log_verb('Adding ROM to Favourites')
        log_verb('romID {0}'.format(romID))
        log_verb('name  {0}'.format(roms[romID]['name']))

        # Check if ROM already in favourites an warn user if so
        if romID in roms_fav:
            log_verb('Already in favourites')
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher',
                               'ROM: {0}'.format(roms[romID]["name"]),
                               'is already on AEL Favourites.', 'Overwrite it?')
            if not ret:
                log_verb('User does not want to overwrite. Exiting.')
                return
        # Confirm if rom should be added
        else:
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher',
                                'ROM: {0}'.format(roms[romID]["name"]),
                                'Add this ROM to AEL Favourites?')
            if not ret:
                log_verb('User does not confirm addition. Exiting.')
                return

        # Add ROM to favourites ROMs and save to disk
        # If thumb is empty then use launcher thum.
        # If fanart is empty then use launcher fanart.
        roms_fav[romID] = fs_get_Favourite_from_ROM(roms[romID], self.launchers[launcherID])
        if roms_fav[romID]['thumb']  == '': roms_fav[romID]['thumb']  = self.launchers[launcherID]['thumb']
        if roms_fav[romID]['fanart'] == '': roms_fav[romID]['fanart'] = self.launchers[launcherID]['fanart']
        # fs_write_Favourites_XML(FAV_XML_FILE_PATH, roms_fav)
        fs_write_Favourites_JSON(FAV_JSON_FILE_PATH, roms_fav)
        kodi_refresh_container()

    #
    # Check ROMs in favourites and set fav_status field.
    # Note that categoryID = launcherID = '0'
    #
    def _command_check_favourites(self, categoryID, launcherID, romID):
        # Load Favourite ROMs
        # roms_fav = fs_load_Favourites_XML(FAV_XML_FILE_PATH)
        roms_fav = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)

        # Reset fav_status filed for all favourites
        log_debug('_command_check_favourites() STEP 0')
        for rom_fav_ID in roms_fav:
            roms_fav[rom_fav_ID]['fav_status'] = 'OK'

        # STEP 1: Find missing launchers
        log_debug('_command_check_favourites() STEP 1')
        for rom_fav_ID in roms_fav:
            if roms_fav[rom_fav_ID]['launcherID'] not in self.launchers:
                log_info('Fav ROM "{0}" unlinked because launcherID not in launchers'.format(roms_fav[rom_fav_ID]['name']))
                roms_fav[rom_fav_ID]['fav_status'] = 'Unlinked'

        # STEP 2: Find missing ROM ID
        # Get a list of launchers Favourite ROMs belong
        log_debug('_command_check_favourites() STEP 2')
        launchers_fav = set()
        for rom_fav_ID in roms_fav: launchers_fav.add(roms_fav[rom_fav_ID]['launcherID'])

        # Traverse list of launchers. For each launcher, load ROMs it and check all favourite ROMs that belong to
        # that launcher.
        for launcher_id in launchers_fav:
            # Load launcher ROMs
            roms = fs_load_ROMs(ROMS_DIR, self.launchers[launcher_id]['roms_base_noext'])

            # Traverse all favourites and check them if belong to this launcher.
            # This should be efficient because traversing favourites is cheap but loading ROMs is expensive.
            for rom_fav_ID in roms_fav:
                if roms_fav[rom_fav_ID]['launcherID'] == launcher_id:
                    # Check if ROM ID exists
                    if roms_fav[rom_fav_ID]['id'] not in roms:
                        log_info('Fav ROM "{0}" unlinked because romID not in launcher ROMs'.format(roms_fav[rom_fav_ID]['name']))
                        roms_fav[rom_fav_ID]['fav_status'] = 'Unlinked'

        # STEP 3: Check if file exists. Even if the ROM ID is not there because user
        # deleted ROM or launcher, the file may still be there.
        log_debug('_command_check_favourites() STEP 3')
        for rom_fav_ID in roms_fav:
            if not os.path.isfile(roms_fav[rom_fav_ID]['filename']):
                log_info('Fav ROM "{0}" broken because filename does not exist'.format(roms_fav[rom_fav_ID]['name']))
                roms_fav[rom_fav_ID]['fav_status'] = 'Broken'

        # Save favourite ROMs
        # fs_write_Favourites_XML(FAV_XML_FILE_PATH, roms_fav)
        fs_write_Favourites_JSON(FAV_JSON_FILE_PATH, roms_fav)

        # Update container to show changes in Favourites flags. If not, user has to exit Favourites and enter again.
        kodi_refresh_container()

    #
    # Search ROMs in launcher
    #
    def _command_search_launcher(self, categoryID, launcherID):
        # --- Load ROMs ---
        if launcherID == VLAUNCHER_FAV_ID:
            # roms = fs_load_Favourites_XML(FAV_XML_FILE_PATH)
            roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
            if not roms:
                kodi_notify('Advanced Emulator Launcher', 'Favourites XML empty. Add items to Favourites')
                return
        else:
            if not os.path.isfile(self.launchers[launcherID]['roms_xml_file']):
                kodi_notify('Advanced Emulator Launcher', 'Launcher XML missing. Add items to launcher')
                return
            roms = fs_load_ROMs(ROMS_DIR, self.launchers[launcherID]['roms_base_noext'])
            if not roms:
                kodi_notify('Advanced Emulator Launcher', 'Launcher XML empty. Add items to launcher')
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
        if   search_type == 'SEARCH_TITLE'  : rom_search_field = 'name'
        elif search_type == 'SEARCH_YEAR'   : rom_search_field = 'year'
        elif search_type == 'SEARCH_STUDIO' : rom_search_field = 'studio'
        elif search_type == 'SEARCH_GENRE'  : rom_search_field = 'genre'

        # --- Load ROMs ---
        if launcherID == VLAUNCHER_FAV_ID:
            rom_is_in_favourites = True
            # roms = fs_load_Favourites_XML(FAV_XML_FILE_PATH)
            roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
            if not roms:
                kodi_notify('Advanced Emulator Launcher', 'Favourites XML empty. Add items to Favourites')
                return
        else:
            rom_is_in_favourites = False
            if not os.path.isfile(self.launchers[launcherID]['roms_xml_file']):
                kodi_notify('Advanced Emulator Launcher', 'Launcher XML missing. Add items to launcher')
                return
            roms = fs_load_ROMs(ROMS_DIR, self.launchers[launcherID]['roms_base_noext'])
            if not roms:
                kodi_notify('Advanced Emulator Launcher', 'Launcher XML empty. Add items to launcher')
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

            if rom_search_field == 'name':
                if not rom.find(text) == -1:
                    rl[keyr] = roms[keyr]
            else:
                if rom == text:
                    rl[keyr] = roms[keyr]

        # Print the list sorted (if there is anything to print)
        if not rl:
            kodi_dialog_OK('Advaned Emulator Launcher', 'Search returned no results')
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
        if categoryID == VCATEGORY_FAV_ID:
            log_info('_command_view_ROM() Viewing ROM in Favourites...')
            # roms = fs_load_Favourites_XML(FAV_XML_FILE_PATH)
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
                kodi_dialog_OK('AEL', 'Virtual launcher XML/JSON file not found.')
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
                kodi_dialog_OK('AEL', 'Virtual launcher XML/JSON file not found.')
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
                kodi_dialog_OK('AEL', 'Virtual launcher XML/JSON file not found.')
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
                kodi_dialog_OK('AEL', 'Virtual launcher XML/JSON file not found.')
                return
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_STUDIO_DIR, launcherID)
            rom = roms[romID]
            window_title = 'Virtual Launcher Studio ROM data'
            regular_launcher = False
            vlauncher_label = 'Virtual Launcher Studio'

        # ROM in regular launcher
        else:
            log_info('_command_view_ROM() Viewing ROM in Launcher...')
            # Check launcher is OK
            if launcherID not in self.launchers:
                kodi_dialog_OK('ERROR', 'launcherID not found in self.launchers')
                return
            category = self.categories[categoryID]
            launcher = self.launchers[launcherID]
            roms = fs_load_ROMs(ROMS_DIR, launcher['roms_base_noext'])
            rom = roms[romID]
            window_title = 'Launcher ROM data'

        # --- Make information string ---
        info_text  = u'[COLOR orange]ROM information[/COLOR]\n'
        info_text += u"[COLOR violet]id[/COLOR]: '{0}'\n".format(rom['id'])
        info_text += u"[COLOR violet]name[/COLOR]: '{0}'\n".format(rom['name'])
        info_text += u"[COLOR violet]filename[/COLOR]: '{0}'\n".format(rom['filename'])
        info_text += u"[COLOR violet]thumb[/COLOR]: '{0}'\n".format(rom['thumb'])
        info_text += u"[COLOR violet]fanart[/COLOR]: '{0}'\n".format(rom['fanart'])
        info_text += u"[COLOR violet]trailer[/COLOR]: '{0}'\n".format(rom['trailer'])
        info_text += u"[COLOR violet]custom[/COLOR]: '{0}'\n".format(rom['custom'])
        info_text += u"[COLOR violet]genre[/COLOR]: '{0}'\n".format(rom['genre'])
        info_text += u"[COLOR violet]year[/COLOR]: '{0}'\n".format(rom['year'])
        info_text += u"[COLOR violet]studio[/COLOR]: '{0}'\n".format(rom['studio'])
        info_text += u"[COLOR violet]plot[/COLOR]: '{0}'\n".format(rom['plot'])
        info_text += u"[COLOR violet]altapp[/COLOR]: '{0}'\n".format(rom['altapp'])
        info_text += u"[COLOR violet]altarg[/COLOR]: '{0}'\n".format(rom['altarg'])
        info_text += u"[COLOR skyblue]finished[/COLOR]: {0}\n".format(rom['finished'])
        info_text += u"[COLOR violet]nointro_status[/COLOR]: '{0}'\n".format(rom['nointro_status'])

        # --- Display category/launcher information ---
        if not regular_launcher:
            info_text += u'\n[COLOR orange]{0} ROM additional information[/COLOR]\n'.format(vlauncher_label)
            info_text += u"[COLOR violet]launcherID[/COLOR]: '{0}'\n".format(rom['launcherID'])
            info_text += u"[COLOR violet]platform[/COLOR]: '{0}'\n".format(rom['platform'])
            info_text += u"[COLOR violet]application[/COLOR]: '{0}'\n".format(rom['application'])
            info_text += u"[COLOR violet]args[/COLOR]: '{0}'\n".format(rom['args'])
            info_text += u"[COLOR violet]rompath[/COLOR]: '{0}'\n".format(rom['rompath'])
            info_text += u"[COLOR violet]romext[/COLOR]: '{0}'\n".format(rom['romext'])
            info_text += u"[COLOR skyblue]minimize[/COLOR]: {0}\n".format(rom['minimize'])
            info_text += u"[COLOR violet]fav_status[/COLOR]: '{0}'\n".format(rom['fav_status'])
        else:
            info_text += u'\n[COLOR orange]Launcher information[/COLOR]\n'
            info_text += u"[COLOR violet]id[/COLOR]: '{0}'\n".format(launcher['id'])
            info_text += u"[COLOR violet]name[/COLOR]: '{0}'\n".format(launcher['name'])
            info_text += u"[COLOR violet]categoryID[/COLOR]: '{0}'\n".format(launcher['categoryID'])
            info_text += u"[COLOR violet]platform[/COLOR]: '{0}'\n".format(launcher['platform'])
            info_text += u"[COLOR violet]application[/COLOR]: '{0}'\n".format(launcher['application'])
            info_text += u"[COLOR violet]args[/COLOR]: '{0}'\n".format(launcher['args'])
            info_text += u"[COLOR violet]rompath[/COLOR]: '{0}'\n".format(launcher['rompath'])
            info_text += u"[COLOR violet]romext[/COLOR]: '{0}'\n".format(launcher['romext'])
            info_text += u"[COLOR violet]thumbpath[/COLOR]: '{0}'\n".format(launcher['thumbpath'])
            info_text += u"[COLOR violet]fanartpath[/COLOR]: '{0}'\n".format(launcher['fanartpath'])
            info_text += u"[COLOR violet]trailerpath[/COLOR]: '{0}'\n".format(launcher['trailerpath'])
            info_text += u"[COLOR violet]custompath[/COLOR]: '{0}'\n".format(launcher['custompath'])
            info_text += u"[COLOR violet]thumb[/COLOR]: '{0}'\n".format(launcher['thumb'])
            info_text += u"[COLOR violet]fanart[/COLOR]: '{0}'\n".format(launcher['fanart'])
            info_text += u"[COLOR violet]genre[/COLOR]: '{0}'\n".format(launcher['genre'])
            info_text += u"[COLOR violet]year[/COLOR]: '{0}'\n".format(launcher['year'])
            info_text += u"[COLOR violet]studio[/COLOR]: '{0}'\n".format(launcher['studio'])
            info_text += u"[COLOR violet]plot[/COLOR]: '{0}'\n".format(launcher['plot'])
            info_text += u"[COLOR skyblue]finished[/COLOR]: {0}\n".format(launcher['finished'])
            info_text += u"[COLOR skyblue]minimize[/COLOR]: {0}\n".format(launcher['minimize'])
            info_text += u"[COLOR violet]roms_base_noext[/COLOR]: '{0}'\n".format(launcher['roms_base_noext'])
            info_text += u"[COLOR violet]nointro_xml_file[/COLOR]: '{0}'\n".format(launcher['nointro_xml_file'])

            info_text += u'\n[COLOR orange]Category information[/COLOR]\n'
            info_text += u"[COLOR violet]id[/COLOR]: '{0}'\n".format(category['id'])
            info_text += u"[COLOR violet]name[/COLOR]: '{0}'\n".format(category['name'])
            info_text += u"[COLOR violet]thumb[/COLOR]: '{0}'\n".format(category['thumb'])
            info_text += u"[COLOR violet]fanart[/COLOR]: '{0}'\n".format(category['fanart'])
            info_text += u"[COLOR violet]genre[/COLOR]: '{0}'\n".format(category['genre'])
            info_text += u"[COLOR violet]description[/COLOR]: '{0}'\n".format(category['description'])
            info_text += u"[COLOR skyblue]finished[/COLOR]: {0}\n".format(category['finished'])

        # --- Show information window ---
        try:
            xbmc.executebuiltin('ActivateWindow(10147)')
            window = xbmcgui.Window(10147)
            xbmc.sleep(100)
            window.getControl(1).setLabel(window_title)
            window.getControl(5).setText(info_text)
        except:
            pass

    #
    # Updated all virtual categories DB
    #
    def _command_update_virtual_category_db_all(self):
        self._command_update_virtual_category_db(VCATEGORY_TITLE_ID)
        self._command_update_virtual_category_db(VCATEGORY_YEARS_ID)
        self._command_update_virtual_category_db(VCATEGORY_GENRE_ID)
        self._command_update_virtual_category_db(VCATEGORY_STUDIO_ID)
        kodi_notify('Advanced Emulator Launcher', 'All virtual categories updated')

    #
    # Makes a virtual category database
    #
    def _command_update_virtual_category_db(self, virtual_categoryID):
        # --- Customise function depending on virtual category ---
        if virtual_categoryID == VCATEGORY_TITLE_ID:
            log_info('_command_update_virtual_category_db() Updating Titles DB')
            vcategory_db_directory = VIRTUAL_CAT_TITLE_DIR
            vcategory_db_filename  = VCAT_TITLE_FILE_PATH
            vcategory_field_name   = 'name'
        elif virtual_categoryID == VCATEGORY_YEARS_ID:
            log_info('_command_update_virtual_category_db() Updating Years DB')
            vcategory_db_directory = VIRTUAL_CAT_YEARS_DIR
            vcategory_db_filename  = VCAT_YEARS_FILE_PATH
            vcategory_field_name   = 'year'
        elif virtual_categoryID == VCATEGORY_GENRE_ID:
            log_info('_command_update_virtual_category_db() Updating Genres DB')
            vcategory_db_directory = VIRTUAL_CAT_GENRE_DIR
            vcategory_db_filename  = VCAT_GENRE_FILE_PATH
            vcategory_field_name   = 'genre'
        elif virtual_categoryID == VCATEGORY_STUDIO_ID:
            log_info('_command_update_virtual_category_db() Updating Studios DB')
            vcategory_db_directory = VIRTUAL_CAT_STUDIO_DIR
            vcategory_db_filename  = VCAT_STUDIO_FILE_PATH
            vcategory_field_name   = 'studio'
        else:
            log_error('_command_update_virtual_category_db() Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
            kodi_dialog_OK('AEL', 'Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
            return

        # Sanity checks
        if len(self.launchers) == 0:
            kodi_dialog_OK('Advanced Emulator Launcher',
                           'You do not have yet any Launchers. Add a ROMs Launcher first.')
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
        pDialog.create('Advanced Emulator Launcher - Scanning ROMs', 'Making ROM list...')
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
            for rom_id in roms:
                rom = roms[rom_id]
                rom['launcherID']  = launcher['id']
                rom['platform']    = launcher['platform']
                rom['application'] = launcher['application']
                rom['args']        = launcher['args']
                rom['rompath']     = launcher['rompath']
                rom['romext']      = launcher['romext']
                rom['minimize']    = launcher['minimize']
                rom['fav_status']  = 'OK'

            # >> Update dictionary
            all_roms.update(roms)
        pDialog.update(i * 100 / num_launchers)
        pDialog.close()

        # --- Create a dictionary that with key the virtual category and value a dictionay of roms 
        #     belonging to that virtual category ---
        # TODO It would be nice to have a progress dialog here...
        log_verb(u'_command_update_virtual_category_db() Creating hashed database')
        virtual_launchers = {}
        for rom_id in all_roms:
            rom = all_roms[rom_id]
            if virtual_categoryID == VCATEGORY_TITLE_ID:
                vcategory_key = rom['name'][0].upper()
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
        log_verb(u'_command_update_virtual_category_db() Writing hashed database XMLs')
        vcategory_launchers = {}
        num_vlaunchers = len(virtual_launchers)
        i = 0
        pDialog.create('Advanced Emulator Launcher - Scanning ROMs', 'Writing VLauncher hashed database...')
        for vlauncher_id in virtual_launchers:
            # >> Update progress dialog
            pDialog.update(i * 100 / num_vlaunchers)
            i += 1

            # >> Create VLauncher UUID
            vlauncher_id_md5   = hashlib.md5(vlauncher_id.encode('utf-8'))
            hashed_db_UUID     = vlauncher_id_md5.hexdigest()
            log_debug(u'_command_update_virtual_category_db() vlauncher_id       "{0}"'.format(vlauncher_id))
            log_debug(u'_command_update_virtual_category_db() hashed_db_UUID     "{0}"'.format(hashed_db_UUID))

            # >> Virtual launcher ROMs are like Favourite ROMs. They contain all required fields to launch
            # >> the ROM, and also share filesystem I/O functions with Favourite ROMs.
            vlauncher_roms = virtual_launchers[vlauncher_id]
            log_debug(u'_command_update_virtual_category_db() Number of ROMs = {0}'.format(len(vlauncher_roms)))
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
        log_verb('_command_update_virtual_category_db() Writing virtual cateogory XML index')
        fs_write_VCategory_XML(vcategory_db_filename, vcategory_launchers)

    #
    # Import legacy Advanced Launcher launchers.xml
    #
    def _command_import_legacy_AL(self):
        # >> Confirm action with user
        ret = kodi_dialog_yesno('Advanced Emulator Launcher', 
                                'Are you sure you want to import Advanced Launcher launchers.xml?')
        if not ret: return
    
        kodi_notify('Advanced Emulator Launcher', 'Importing AL launchers.xml...')
        AL_DATA_DIR = xbmc.translatePath(os.path.join('special://profile/addon_data',
                                                      'plugin.program.advanced.launcher')).decode('utf-8')
        LAUNCHERS_FILE_PATH  = os.path.join(AL_DATA_DIR, 'launchers.xml').decode('utf-8')

        # >> Check that launchers.xml exist
        if not os.path.isfile(LAUNCHERS_FILE_PATH):
            log_error("_command_import_legacy_AL() Cannot find '{0}'".format(LAUNCHERS_FILE_PATH))
            kodi_dialog_OK('Advanced Emulator Launcher', 'launchers.xml not found!')
            return

        # >> Read launchers.xml
        AL_categories = {}
        AL_launchers = {}
        kodi_busydialog_ON()
        fs_load_legacy_AL_launchers(LAUNCHERS_FILE_PATH, AL_categories, AL_launchers)
        kodi_busydialog_OFF()

        # >> Sanity checks

        # >> Traverse AL data and create categories/launchers/ROMs
        num_categories = 0
        num_launchers = 0
        num_ROMs = 0
        default_SID = ''
        for AL_category_key in AL_categories:
            num_categories += 1
            AL_category = AL_categories[AL_category_key]
            category = fs_new_category()
            # >> Do translation
            if AL_category['id'] == 'default':
                category['id'] = misc_generate_random_SID()
                default_SID = category['id']
            else:
                category['id'] = AL_category['id']
            category['name']        = AL_category['name']
            category['thumb']       = AL_category['thumb']
            category['fanart']      = AL_category['fanart']
            category['genre']       = AL_category['genre']
            category['description'] = AL_category['plot']
            category['finished']    = False if AL_category['finished'] == 'false' else True
            self.categories[category['id']] = category

        for AL_launcher_key in AL_launchers:
            num_launchers += 1
            AL_launcher = AL_launchers[AL_launcher_key]
            launcher = fs_new_launcher()
            # >> Do translation
            launcher['id']   = AL_launcher['id']
            launcher['name'] = AL_launcher['name']
            if AL_launcher['category'] == 'default':
                launcher['categoryID'] = default_SID
            else:
                launcher['categoryID'] = AL_launcher['category']
            launcher['application'] = AL_launcher['application']
            launcher['args']        = AL_launcher['args']
            launcher['rompath']     = AL_launcher['rompath']
            launcher['thumbpath']   = AL_launcher['thumbpath']
            launcher['fanartpath']  = AL_launcher['fanartpath']
            launcher['trailerpath'] = AL_launcher['trailerpath']
            launcher['custompath']  = AL_launcher['custompath']
            launcher['romext']      = AL_launcher['romext']
            # >> 'gamesys' ignored, set to unknown to avoid trouble with scrapers
            # launcher['platform']    = AL_launcher['gamesys']
            launcher['platform']    = 'Unknown'            
            launcher['thumb']       = AL_launcher['thumb']
            launcher['fanart']      = AL_launcher['fanart']
            launcher['genre']       = AL_launcher['genre']
            launcher['year']        = AL_launcher['release']
            launcher['studio']      = AL_launcher['studio']
            launcher['plot']        = AL_launcher['plot']
            launcher['finished']    = False if AL_launcher['finished'] == 'false' else True
            launcher['minimize']    = False if AL_launcher['minimize'] == 'false' else True
            # >> 'lnk' ignored, always active in AEL

            # --- Import ROMs if ROMs launcher ---
            AL_roms = AL_launcher['roms']
            if AL_roms:
                roms = {}
                category_name = self.categories[launcher['categoryID']]['name']
                roms_base_noext = fs_get_ROMs_basename(category_name, launcher['name'], launcher['id'])
                launcher['roms_base_noext'] = roms_base_noext
                for AL_rom_ID in AL_roms:
                    num_ROMs += 1
                    AL_rom = AL_roms[AL_rom_ID]
                    rom = fs_new_rom()
                    # >> Do translation
                    rom['id']       = AL_rom['id']
                    rom['name']     = AL_rom['name']
                    rom['filename'] = AL_rom['filename']
                    rom['thumb']    = AL_rom['thumb']
                    rom['fanart']   = AL_rom['fanart']
                    rom['trailer']  = AL_rom['trailer']
                    rom['custom']   = AL_rom['custom']
                    rom['genre']    = AL_rom['genre']
                    rom['year']     = AL_rom['release']
                    rom['studio']   = AL_rom['studio']
                    rom['plot']     = AL_rom['plot']
                    rom['finished'] = False if AL_rom['finished'] == 'false' else True
                    rom['altapp']   = AL_rom['altapp']
                    rom['altarg']   = AL_rom['altarg']
                    # >> Add to ROM dictionary
                    roms[rom['id']] = rom

                # >> Save ROMs XML
                fs_write_ROMs(ROMS_DIR, roms_base_noext, roms, launcher)
            else:
                launcher['roms_xml_file'] = ''
            # >> Add launcher to AEL launchers
            self.launchers[launcher['id']] = launcher

        # >> Save AEL categories.xml
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

        # --- Show some information to user ---
        kodi_dialog_OK('Advanced Emulator Launcher',
                       'Imported {0} Category/s, {1} Launcher/s '.format(num_categories, num_launchers) +
                       'and {0} ROM/s.'.format(num_ROMs))
        kodi_refresh_container()

    #
    # Launchs an application
    #
    def _command_run_standalone_launcher(self, categoryID, launcherID):
        # Check launcher is OK
        if launcherID not in self.launchers:
            kodi_dialog_OK('ERROR', 'launcherID not found in self.launchers')
            return
        launcher = self.launchers[launcherID]

        # Kodi built-in???
        # xbmc-fav- and xbmc-sea are Angelscry's hacks to implement launchers from favourites
        # and launchers from searchers. For example, to run a launcher created from search
        # results,
        # app = "xbmc-sea-%s" % launcherid
        # args = 'ActivateWindow(10001,"%s")' % launcher_query
        apppath = os.path.dirname(launcher['application'])
        if os.path.basename(launcher['application']).lower().replace('.exe' , '') == 'xbmc'  or \
           'xbmc-fav-' in launcher['application'] or 'xbmc-sea-' in launcher['application']:
            xbmc.executebuiltin('XBMC.%s' % launcher['args'])
            return

        # ~~~~~ External application ~~~~~
        application = launcher['application']
        application_basename = os.path.basename(launcher['application'])
        if not os.path.exists(apppath):
            kodi_notify_warn('Advanced Emulator Launcher',
                             'App {0} not found.'.format(apppath))
            return
        arguments = launcher['args'].replace('%apppath%' , apppath).replace('%APPPATH%' , apppath)
        log_info('_run_standalone_launcher() apppath              = "{0}"'.format(apppath))
        log_info('_run_standalone_launcher() application          = "{0}"'.format(application))
        log_info('_run_standalone_launcher() application_basename = "{0}"'.format(application_basename))
        log_info('_run_standalone_launcher() arguments            = "{0}"'.format(arguments))

        # Do stuff before execution
        self._run_before_execution(launcher, application_basename)

        # Execute
        if sys.platform == 'win32':
            if launcher['application'].split('.')[-1] == 'lnk':
                os.system("start \"\" \"%s\"" % (application))
            else:
                if application.split('.')[-1] == 'bat':
                    info = subprocess_hack.STARTUPINFO()
                    info.dwFlags = 1
                    if self.settings['show_batch_window']:
                        info.wShowWindow = 5
                    else:
                        info.wShowWindow = 0
                else:
                    info = None
                startproc = subprocess_hack.Popen(r'%s %s' % (application, arguments), cwd=apppath, startupinfo=info)
                startproc.wait()
        elif sys.platform.startswith('linux'):
            if self.settings['lirc_state']: xbmc.executebuiltin('LIRC.stop')
            os.system("\"%s\" %s " % (application, arguments))
            if self.settings['lirc_state']: xbmc.executebuiltin('LIRC.start')
        elif sys.platform.startswith('darwin'):
            os.system("\"%s\" %s " % (application, arguments))
        else:
            kodi_notify_warn('Advanced Emulator Launcher', 'Cannot determine the running platform')

        # Do stuff after execution
        self._run_after_execution(launcher)

    #
    # Launchs a ROM
    #
    def _command_run_rom(self, categoryID, launcherID, romID):
        # ROM in Favourites
        if launcherID == VLAUNCHER_FAV_ID:
            log_info('_command_run_rom() Launching ROM in Favourites...')
            # roms = fs_load_Favourites_XML(FAV_XML_FILE_PATH)
            roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
            rom = roms[romID]
            application = rom['application'] if rom['altapp'] == '' else rom['altapp']
            arguments   = rom['args'] if rom['altarg'] == '' else rom['altarg']
            minimize_flag = rom['minimize']
            rom_romext = rom['romext']

        # ROM in launcher
        else:
            log_info('_command_run_rom() Launching ROM in Launcher...')
            # Check launcher is OK
            if launcherID not in self.launchers:
                kodi_dialog_OK('ERROR', 'launcherID not found in self.launchers')
                return
            launcher = self.launchers[launcherID]

            # Load ROMs
            roms = fs_load_ROMs(ROMS_DIR, launcher['roms_base_noext'])

            # Check ROM is in XML data just read
            if romID not in roms:
                kodi_dialog_OK('ERROR', 'romID not in roms dictionary')
                return
            rom = roms[romID]
            application = launcher['application'] if rom['altapp'] == '' else rom['altapp']
            arguments = launcher['args'] if rom['altarg'] == '' else rom['altarg']
            minimize_flag = launcher['minimize']
            rom_romext = launcher['romext']

        # Launch ROM
        apppath     = os.path.dirname(application)
        ROM         = misc_split_path(rom['filename'])
        romfile     = ROM.path
        rompath     = ROM.dirname
        rombasename = ROM.base
        log_info('_command_run_rom() application = "{0}"'.format(application))
        log_info('_command_run_rom() apppath     = "{0}"'.format(apppath))
        log_info('_command_run_rom() romfile     = "{0}"'.format(romfile))
        log_info('_command_run_rom() rompath     = "{0}"'.format(rompath))
        log_info('_command_run_rom() rombasename = "{0}"'.format(rombasename))

        # --- Check for errors and abort if found ---
        if not os.path.exists(application):
            log_error('Launching app not found "{0}"'.format(application))
            kodi_notify_warn('Advanced Emulator Launcher', 'Launching app not found {0}'.format(application))
            return

        if not os.path.exists(romfile):
            log_error('ROM not found "{0}"'.format(romfile))
            kodi_notify_warn('Advanced Emulator Launcher', 'ROM not found {0}'.format(romfile))
            return

        # ~~~~ Argument substitution ~~~~~
        arguments = arguments.replace("%rom%",         romfile).replace("%ROM%",             romfile)
        arguments = arguments.replace("%rombasename%", rombasename).replace("%ROMBASENAME%", rombasename)
        arguments = arguments.replace("%apppath%",     apppath).replace("%APPPATH%",         apppath)
        arguments = arguments.replace("%rompath%",     rompath).replace("%ROMPATH%",         rompath)
        arguments = arguments.replace("%romtitle%",    rom['name']).replace("%ROMTITLE%",    rom['name'])
        log_info('_command_run_rom() arguments   = "{0}"'.format(arguments))

        # Execute Kodi internal function (RetroPlayer?)
        if os.path.basename(application).lower().replace('.exe', '') == 'xbmc':
            xbmc.executebuiltin('XBMC.' + arguments)
            return

        # ~~~~~ Execute external application ~~~~~
        # Do stuff before execution
        self._run_before_execution(rombasename, minimize_flag)

        # Determine platform and launch application
        if sys.platform == 'win32':
            if rom_romext == 'lnk':
                os.system("start \"\" \"%s\"" % (arguments))
            else:
                if application.split(".")[-1] == "bat":
                    info = subprocess_hack.STARTUPINFO()
                    info.dwFlags = 1
                    if self.settings["show_batch"]:
                        info.wShowWindow = 5
                    else:
                        info.wShowWindow = 0
                else:
                    info = None
                startproc = subprocess_hack.Popen(r'%s %s' % (application, arguments), cwd=apppath, startupinfo=info)
                startproc.wait()
        elif sys.platform.startswith('linux'):
            if self.settings['lirc_state']: xbmc.executebuiltin('LIRC.stop')
            os.system("\"%s\" %s " % (application, arguments))
            if self.settings['lirc_state']: xbmc.executebuiltin('LIRC.start')
        # Android??? OSX???
        elif sys.platform.startswith('darwin'):
            os.system("\"%s\" %s " % (application, arguments))
        else:
            kodi_notify_warn('Advanced Emulator Launcher', 'Cannot determine the running platform')

        # Do stuff after application execution
        self._run_after_execution(minimize_flag)

    #
    # These two functions do things like stopping music before lunch, toggling full screen, etc.
    #
    def _run_before_execution(self, rombasename, minimize_flag):
        if self.settings['media_state'] != "2" :
            if xbmc.Player().isPlaying():
                if self.settings['media_state'] == "0":
                    xbmc.Player().stop()
                if self.settings['media_state'] == "1":
                    xbmc.Player().pause()
                xbmc.sleep(self.settings['start_tempo'] + 100)
                try:
                    xbmc.audioSuspend()
                except:
                    pass

        if minimize_flag:
            kodi_toogle_fullscreen()

        if self.settings['display_launcher_notification']:
            kodi_notify('Advanced Emulator Launcher', 'Launching {0}'.format(rombasename))

        try:
            xbmc.enableNavSounds(False)
        except:
            pass
        
        # >> Stop Kodi some time
        xbmc.sleep(self.settings['start_tempo'])

    def _run_after_execution(self, minimize_flag):
        # >> Stop Kodi some time
        xbmc.sleep(self.settings['start_tempo'])

        try:
            xbmc.enableNavSounds(True)
        except:
            pass

        if minimize_flag:
            kodi_toogle_fullscreen()

        if self.settings['media_state'] != "2":
            try:
                xbmc.audioResume()
            except:
                pass
            if self.settings['media_state'] == "1":
                xbmc.sleep(self.settings['start_tempo'] + 100)
                xbmc.Player().play()

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
                name = roms[rom_id]['name']
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
            roms_set.add(roms[rom_id]['name'])

        # Traverse ROMs and check they are in the DAT
        num_have = num_miss = num_unknown = 0
        for rom_id in roms:
            if roms[rom_id]['name'] in roms_nointro_set:
                roms[rom_id]['nointro_status'] = 'Have'
                num_have += 1
            else:
                roms[rom_id]['nointro_status'] = 'Unknown'
                num_unknown += 1

        # Mark dead ROMs as missing
        for rom_id in roms:
            name     = roms[rom_id]['name']
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
                rom['name'] = nointro_rom
                rom['nointro_status'] = 'Miss'
                roms[rom_id] = rom
                num_miss += 1

        # Return statistics
        return (num_have, num_miss, num_unknown)

    #
    # Manually add a new ROM instead of a recursive scan.
    #   A) User chooses a ROM file
    #   B) Title is formatted. No metadata scrapping.
    #   C) Thumb and fanart are searched locally only.
    # Later user can edit this ROM if he wants.
    #
    def _roms_add_new_rom(self, launcherID):
        # --- Grab launcher information ---
        launcher    = self.launchers[launcherID]
        application = launcher['application']
        romext      = launcher['romext']
        rompath     = launcher['rompath']

        # --- Load ROMs for this launcher ---
        roms = fs_load_ROMs(ROMS_DIR, launcher['roms_base_noext'])
        if not roms: return

        # --- Choose ROM file ---
        dialog = xbmcgui.Dialog()
        extensions = "." + romext.replace('|', '|.')
        romfile = dialog.browse(1, 'Select the ROM file', 'files', extensions, False, False, rompath)
        if not romfile: return

        # --- Format title ---
        scan_clean_tags       = self.settings['scan_clean_tags']
        ROM = misc_split_path(romfile)
        romname = text_ROM_title_format(ROM.base_noext, scan_clean_tags)

        # --- Search for local Thumb/Fanart ---
        thumb_path_noext  = misc_get_thumb_path_noext(selectedLauncher, ROM)
        fanart_path_noext = misc_get_fanart_path_noext(selectedLauncher, ROM)
        local_thumb  = misc_look_for_image(thumb_path_noext, IMG_EXTS)
        local_fanart = misc_look_for_image(fanart_path_noext, IMG_EXTS)
        log_verb('Local images set Thumb  "{0}"'.format(local_thumb))
        log_verb('Local images set Fanart "{0}"'.format(local_fanart))

        # --- Create ROM data structure ---
        romdata = fs_new_rom()
        romID   = misc_generate_random_SID()
        romdata['id']       = romID
        romdata['filename'] = ROM.path
        romdata['name']     = romname
        romdata['thumb']    = local_thumb,
        romdata['fanart']   = local_fanart,
        roms[romID] = romdata

        # ~~~ Save ROMs XML file ~~~
        # >> Also save categories/launchers to update timestamp
        fs_write_ROMs(ROMS_DIR, launcher['roms_base_noext'], roms, launcher)
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

    #
    # ROM scanner. Called when user chooses "Add items" -> "Scan items"
    # Note that actually this command is "Add/Update" ROMs.
    #
    def _roms_import_roms(self, launcherID):
        log_debug('_roms_import_roms() ========== BEGIN ==========')

        # Get game system, thumbnails and fanarts paths from launcher
        selectedLauncher = self.launchers[launcherID]
        launcher_app     = selectedLauncher['application']
        launcher_path    = selectedLauncher['rompath']
        launcher_exts    = selectedLauncher['romext']
        log_debug('Launcher "{0}" selected'.format(selectedLauncher['name']))
        log_debug('launcher_app  = {0}'.format(launcher_app))
        log_debug('launcher_path = {0}'.format(launcher_path))
        log_debug('launcher_exts = {0}'.format(launcher_exts))
        log_debug('platform      = {0}'.format(selectedLauncher['platform']))

        # Check if there is an XML for this launcher. If so, load it.
        # If file does not exist or is empty then return an empty dictionary.
        roms = fs_load_ROMs(ROMS_DIR, selectedLauncher['roms_base_noext'])
        num_roms = len(roms)

        # --- Progress dialog ---
        # Put in in object variables so it can be access in helper functions.
        self.pDialog = xbmcgui.DialogProgress()
        self.pDialog_canceled = False

        # ~~~~~ Remove dead entries ~~~~~
        num_removed_roms = 0
        log_debug('Launcher list contain %s items' % len(roms))
        if num_roms > 0:
            log_debug('Starting dead items scan')
            i = 0
            self.pDialog.create('Advanced Emulator Launcher - Scanning ROMs',
                                'Checking for dead entries...', "Path '{0}'".format(launcher_path))
            for key in sorted(roms.iterkeys()):
                log_debug('Searching {0}'.format(roms[key]['filename']))
                self.pDialog.update(i * 100 / num_roms)
                i += 1
                if not os.path.isfile(roms[key]["filename"]):
                    log_debug('Not found')
                    log_debug('Delete {0} item entry'.format(roms[key]['filename']))
                    del roms[key]
                    num_removed_roms += 1
            self.pDialog.close()
            if num_removed_roms > 0:
                kodi_notify('Advanced Emulator Launcher', '{0} dead ROMs removed successfully'.format(num_removed_roms))
                log_info('{0} dead ROMs removed successfully'.format(num_removed_roms))
            else:
                log_info('No dead ROMs found.')
        else:
            log_info('Launcher is empty. No dead ROM check.')

        # ~~~ Scan for new files (*.*) and put them in a list ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        kodi_notify('Advanced Emulator Launcher', 'Scanning files...')
        kodi_busydialog_ON()
        log_info('Scanning files in {0}'.format(launcher_path))
        files = []
        if self.settings["scan_recursive"]:
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
        log_debug('========== Processing ROMs ==========')
        num_new_roms = 0
        num_files_checked = 0
        for f_path in files:
            # --- Get all file name combinations ---
            ROM = misc_split_path(f_path)
            log_debug('*** Processing File ***')
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
                    log_debug("Expected '%s' extension detected" % ext)
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
                kodi_dialog_OK('Advanced Emulator Launcher', 'Stopping ROM scanning. No changes have been made.')
                log_info('User pressed Cancel button when scanning ROMs')
                log_info('ROM scanning stopped')
                return
        self.pDialog.close()
        log_info('***** ROM scanner finished. Report ******')
        log_info('Removed dead ROMs {0:6d}'.format(num_removed_roms))
        log_info('Files checked     {0:6d}'.format(num_files_checked))
        log_info('New added ROMs    {0:6d}'.format(num_new_roms))

        if len(roms) == 0:
            kodi_dialog_OK('Advanced Emulator Launcher',
                           'No ROMs found! Make sure launcher directory and file extensions are correct.')
            return

        if num_new_roms == 0:
            kodi_dialog_OK('Advanced Emulator Launcher',
                           'Launcher has {0} ROMs and no new ROMs have been added.'.format(len(roms)))

        # --- If we have a No-Intro XML then audit roms after scanning ----------------------------
        if selectedLauncher['nointro_xml_file'] != '':
            nointro_xml_file = selectedLauncher['nointro_xml_file']
            log_info('Auditing ROMs using No-Intro DAT {0}'.format(nointro_xml_file))

            # --- Update No-Intro status for ROMs ---
            # Note that roms dictionary is updated using Python pass by assigment.
            # See http://stackoverflow.com/questions/986006/how-do-i-pass-a-variable-by-reference
            (num_have, num_miss, num_unknown) = self._roms_update_NoIntro_status(roms, nointro_xml_file)

            # Report
            log_info('***** No-Intro audit finished. Report ******')
            log_info('No-Intro Have ROMs    {0:6d}'.format(num_have))
            log_info('No-Intro Miss ROMs    {0:6d}'.format(num_miss))
            log_info('No-Intro Unknown ROMs {0:6d}'.format(num_unknown))
        else:
            log_info('No No-Intro DAT configured. No auditing ROMs.')

        # ~~~ Save ROMs XML file ~~~
        # >> Also save categories/launchers to update timestamp
        fs_write_ROMs(ROMS_DIR, selectedLauncher['roms_base_noext'], roms, selectedLauncher)
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

        # ~~~ Notify user ~~~
        kodi_notify('Advanced Emulator Launcher', 'Added {0} new ROMs'.format(num_new_roms))
        log_debug('_roms_import_roms() ========== END ==========')
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
        scan_ignore_scrapped_title = self.settings['scan_ignore_scrapped_title']
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
            romdata['name'] = text_ROM_title_format(ROM.base_noext, scan_clean_tags)
        elif metadata_action == META_NFO_FILE:
            nfo_file_path = ROM.path_noext + ".nfo"
            scraper_text = 'Reading NFO file {0}'.format(nfo_file_path)
            self.pDialog.update(self.progress_number, self.file_text, scraper_text)
            log_debug('Trying NFO file "{0}"'.format(nfo_file_path))
            if os.path.isfile(nfo_file_path):
                log_debug('NFO file found. Reading it')
                nfo_dic = fs_load_NFO_file_scanner(nfo_file_path)
                # NOTE <platform> is chosen by AEL, never read from NFO files
                romdata['name']   = nfo_dic['title']     # <title>
                romdata['genre']  = nfo_dic['genre']     # <genre>
                romdata['year']   = nfo_dic['year']      # <year>
                romdata['studio'] = nfo_dic['publisher'] # <publisher>
                romdata['plot']   = nfo_dic['plot']      # <plot>
            else:
                log_debug('NFO file not found. Only cleaning ROM name.')
                romdata['name'] = text_ROM_title_format(ROM.base_noext, scan_clean_tags)
        elif metadata_action == META_SCRAPER:
            scraper_text = 'Scraping metadata with {0}. Searching for matching games...'.format(self.scraper_metadata.fancy_name)
            self.pDialog.update(self.progress_number, self.file_text, scraper_text)

            # --- Do a search and get a list of games ---
            rom_name_scrapping = text_clean_ROM_name_for_scrapping(ROM.base_noext)
            results = self.scraper_metadata.get_search(rom_name_scrapping, ROM.base_noext, platform)
            log_debug('Metadata scraper found {0} result/s'.format(len(results)))
            if results:
                # id="metadata_mode" values="Semi-automatic|Automatic"
                if self.settings['metadata_mode'] == 0:
                    log_debug('Metadata semi-automatic scraping')
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
                elif self.settings['metadata_mode'] == 1:
                    log_debug('Metadata automatic scraping. Selecting first result.')
                    selectgame = 0
                else:
                    log_error('Invalid metadata_mode {0}'.format(self.settings['metadata_mode']))
                    selectgame = 0
                scraper_text = 'Scraping metadata with {0}. Game selected. Getting metadata...'.format(self.scraper_metadata.fancy_name)
                self.pDialog.update(self.progress_number, self.file_text, scraper_text)
                    
                # --- Grab metadata for selected game ---
                gamedata = self.scraper_metadata.get_metadata(results[selectgame])

                # --- Put metadata into ROM dictionary ---
                if scan_ignore_scrapped_title:
                    # Ignore scraped title
                    romdata['name'] = text_ROM_title_format(ROM.base_noext, scan_clean_tags)
                    log_debug("User wants to ignore scraper name. Setting name to '{0}'".format(romdata['name']))
                else:
                    # Use scraped title
                    romdata['name'] = gamedata['title']
                    log_debug("User wants scrapped name. Setting name to '{0}'".format(romdata['name']))
                romdata['genre']  = gamedata['genre']
                romdata['year']   = gamedata['year']
                romdata['studio'] = gamedata['studio']
                romdata['plot']   = gamedata['plot']
            else:
                log_verb('Metadata scraper found no games after searching. Only cleaning ROM name.')
                romdata['name'] = text_ROM_title_format(ROM.base_noext, scan_clean_tags)
        else:
            log_error('Invalid metadata_action value = {0}'.format(metadata_action))

        # ~~~~~ Search for local artwork ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # If thumbs/fanart have the same path, then assign names
        #   (f_base_noext)_thumb,
        #   (f_base_noext)_fanart
        # Otherwise, thumb/fanart name is same as ROM, but different extension.
        # If no local artwork is found them names are empty strings ''
        thumb_path  = launcher['thumbpath']
        fanart_path = launcher['fanartpath']
        thumb_path_noext  = misc_get_thumb_path_noext(thumb_path, fanart_path, ROM.base_noext)
        fanart_path_noext = misc_get_fanart_path_noext(thumb_path, fanart_path, ROM.base_noext)
        # log_debug('thumb_path_noext  = "{0}"'.format(thumb_path_noext))
        # log_debug('fanart_path_noext = "{0}"'.format(fanart_path_noext))

        # --- Look for local artwork ---
        local_thumb  = misc_look_for_image(thumb_path_noext, IMG_EXTS)
        local_fanart = misc_look_for_image(fanart_path_noext, IMG_EXTS)
        log_verb('Local image scanner found Thumb  "{0}"'.format(local_thumb))
        log_verb('Local image scanner found Fanart "{0}"'.format(local_fanart))

        # ~~~ Thumb scraping ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # settings.xml -> id="scan_thumb_policy" default="0" values="Local Images|Local Images + Scrapers|Scrapers"
        scan_thumb_policy = self.settings["scan_thumb_policy"]
        if scan_thumb_policy == 0:
            log_verb('Thumb policy: local images only | Scraper OFF')
            selected_thumb = local_thumb
        elif scan_thumb_policy == 1 and local_thumb == '':
            log_verb('Thumb policy: if not Local Image then Scraper ON')
            log_verb('Thumb policy: local thumb NOT found | Scraper ON')
            selected_thumb = self._roms_scrap_image(IMAGE_THUMB, 'Thumb', local_thumb, launcherID, ROM)
        elif scan_thumb_policy == 1 and local_thumb != '':
            log_verb('Thumb policy: if not Local Image then Scraper ON')
            log_verb('Thumb policy: local thumb FOUND | Scraper OFF')
            selected_thumb = local_thumb
        elif scan_thumb_policy == 2:
            log_verb('Thumb policy: scraper will overwrite local thumb | Scraper ON')
            selected_thumb = self._roms_scrap_image(IMAGE_THUMB, 'Thumb', local_thumb, launcherID, ROM)
        romdata['thumb'] = selected_thumb
        log_verb('Set Thumb to file "{0}"'.format(romdata['thumb']))

        # ~~~ Fanart scraping ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Fanart scraping policy has same values as Thumb. If not, bad things will happen.
        # settings.xml -> id="scan_fanart_policy" default="0" values="Local Images|Local Images + Scrapers|Scrapers"
        scan_fanart_policy = self.settings["scan_fanart_policy"]
        if scan_fanart_policy == 0:
            log_verb('Fanart policy: local images only | Scraper OFF')
            selected_fanart = local_fanart
        elif scan_fanart_policy == 1 and local_fanart == '':
            log_verb('Fanart policy: if not Local Image then Scraper ON')
            log_verb('Fanart policy: local fanart not found | Scraper ON')
            selected_fanart = self._roms_scrap_image(IMAGE_FANART, 'Fanart', local_fanart, launcherID, ROM)
        elif scan_fanart_policy == 1 and local_fanart != '':
            log_verb('Fanart policy: if not Local Image then Scraper ON')
            log_verb('Fanart policy: local fanart found | Scraper OFF')
            selected_fanart = local_fanart
        elif scan_fanart_policy == 2:
            log_verb('Fanart policy: scraper will overwrite local fanart | Scraper ON')
            selected_fanart = self._roms_scrap_image(IMAGE_FANART, 'Fanart', local_fanart, launcherID, ROM)
        romdata['fanart'] = selected_fanart
        log_verb('Set Fanart to file "{0}"'.format(romdata['fanart']))

        # --- Return romdata dictionary ---
        return romdata

    #
    # Returns a valid filename of the downloaded scrapped image, filename of local image
    # or empty string if scraper finds nothing or download failed.
    #
    def _roms_scrap_image(self, image_kind, image_name, local_image, launcherID, ROM):
        # By default always use local image in case scraper fails
        ret_imagepath = local_image

        # --- Cutomise function depending of image_king ---
        launcher = self.launchers[launcherID]
        platform = launcher['platform']
        if image_kind == IMAGE_THUMB:
            scraping_mode    = self.settings['thumb_mode']
            scraper_obj      = self.scraper_thumb
            scraper_name     = self.scraper_thumb.name
            thumb_dir        = launcher['thumbpath']
            fanart_dir       = launcher['fanartpath']
            image_path_noext = misc_get_thumb_path_noext(thumb_dir, fanart_dir, ROM.base_noext)
        elif image_kind == IMAGE_THUMB:
            scraping_mode    = self.settings['fanart_mode']
            scraper_obj      = self.scraper_fanart
            scraper_name     = self.scraper_fanart.name
            thumb_dir        = launcher['thumbpath']
            fanart_dir       = launcher['fanartpath']
            image_path_noext = misc_get_fanart_path_noext(thumb_dir, fanart_dir, ROM.base_noext)
        else:
            kodi_notify_warn('Advanced Emulator Launcher', 'Wrong image_kind = {0}'.format(image_kind))
            log_error('_roms_scrap_image() Wrong image_kind = {0}'.format(image_kind))
            return ret_imagepath

        # --- Updated progress dialog ---
        file_text = 'ROM {0}'.format(ROM.base)
        scraper_text = 'Scraping {0} with {1}. Searching for matching games...'.format(image_name, scraper_name)
        self.pDialog.update(self.progress_number, self.file_text, scraper_text)
        log_verb('Scraping {0} with {1}'.format(image_name, scraper_name))

        # --- Call scraper and get a list of games ---
        rom_name_scrapping = text_clean_ROM_name_for_scrapping(ROM.base_noext)
        results = scraper_obj.get_search(rom_name_scrapping, ROM.base_noext, platform)
        log_debug('{0} scraper found {1} result/s'.format(image_name, len(results)))
        if not results:
            log_debug('{0} scraper did not found any game'.format(image_name))
            return ret_imagepath

        # --- Choose game to download image ---
        # settings.xml: id="thumb_mode"  default="0" values="Semi-automatic|Automatic"
        # settings.xml: id="fanart_mode" default="0" values="Semi-automatic|Automatic"
        if scraping_mode == 0:
            log_debug('{0} semi-automatic scraping. User chooses.'.format(image_name))
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
            log_debug('{0} automatic scraping. Selecting first result.'.format(image_name))
            selectgame = 0
        else:
            log_error('{0} invalid thumb_mode {1}'.format(image_name, scraping_mode))
            selectgame = 0
        scraper_text = 'Scraping {0} with {1}. Game selected. Getting list of images...'.format(image_name, scraper_name)
        self.pDialog.update(self.progress_number, self.file_text, scraper_text)

        # --- Grab list of images for the selected game ---
        image_list = scraper_obj.get_images(results[selectgame])
        log_verb('{0} scraper returned {1} images'.format(image_name, len(image_list)))
        if not image_list:
            log_debug('{0} scraper get_images() returned no images.'.format(image_name))
            return ret_imagepath

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
            log_debug('{0} dialog returned image_url "{1}"'.format(image_name, image_url))
            if image_url == '': image_url = image_list[0]['URL']

            # Reopen progress dialog
            scraper_text = 'Scraping {0} with {1}. Downloading image...'.format(image_name, scraper_name)
            self.pDialog.create('Advanced Emulator Launcher - Scanning ROMs')
            self.pDialog.update(self.progress_number, self.file_text, scraper_text)
        # --- Automatic scraping. Pick first image. ---
        else:
            # Pick first image in automatic mode
            image_url = image_list[0]['URL']

        # If user chose the local image don't download anything
        if image_url != local_image:
            # ~~~ Download scraped image ~~~
            # Get Tumb/Fanart name with no extension, then get URL image extension
            # and make full thumb path. If extension cannot be determined
            # from URL defaul to '.jpg'
            img_ext    = text_get_image_URL_extension(image_url) # Includes front dot -> .jpg
            image_path = image_path_noext + img_ext

            # ~~~ Download image ~~~
            log_debug('image_path_noext "{0}"'.format(image_path_noext))
            log_debug('img_ext          "{0}"'.format(img_ext))
            log_verb('Downloading URL  "{0}"'.format(image_url))
            log_verb('Into local file  "{0}"'.format(image_path))
            try:
                net_download_img(image_url, image_path)
            except socket.timeout:
                kodi_notify_warn('Advanced Emulator Launcher',
                                 'Cannot download {0} image (Timeout)'.format(image_name))

            # ~~~ Update Kodi cache with downloaded image ~~~
            # Recache only if local image is in the Kodi cache, this function takes care of that.
            kodi_update_image_cache(image_path)

            # --- Return value is downloaded image ---
            ret_imagepath = image_path
        else:
            log_debug('{0} scraper: user chose local image "{1}"'.format(image_name, image_url))
            ret_imagepath = image_url

        # --- Returned value ---
        return ret_imagepath

    # ---------------------------------------------------------------------------------------------
    # Launcher/ROM Thumb/Fanart image semiautomatic scrapers.
    # Function is here because structure is very similar to scanner _roms_scrap_image(). User is
    # presented with a list of scrapped images and chooses the best one.
    # Called when editing a Launcher/ROM Thumb/Fanart from context menu.
    #
    # objects_dic is changed using Python pass by assigment
    # Caller is responsible for saving edited launcher/ROM
    # Be aware that maybe launcherID = '0' if editing a ROM in Favourites
    #
    # Returns:
    #   True   Changes were made to objects_dic. Caller must save XML/refresh container
    #   False  No changes were made
    # ---------------------------------------------------------------------------------------------
    def _gui_scrap_image_semiautomatic(self, image_kind, objects_kind, objects_dic, objectID, launcherID):
        # _gui_edit_image() already has checked for errors in parameters.

        # --- Configure function depending of image kind ---
        # Customise function depending of object to edit
        if image_kind == IMAGE_THUMB:
            scraper_obj = self.scraper_thumb
            image_key   = 'thumb'
            image_name  = 'Thumb'
            if objects_kind == KIND_LAUNCHER:
                platform = objects_dic[objectID]['platform']
                kind_name = 'Launcher'
                launchers_thumb_dir  = self.settings['launchers_thumb_dir']
                launchers_fanart_dir = self.settings['launchers_fanart_dir']
                dest_basename = objects_dic[objectID]['name']
                rom_base_noext = '' # Used by offline scrapers only
                image_path_noext = misc_get_thumb_path_noext(launchers_thumb_dir, launchers_fanart_dir, dest_basename)
            elif objects_kind == KIND_ROM:
                kind_name = 'ROM'
                # ROM in favourites
                if launcherID == VLAUNCHER_FAV_ID:
                    thumb_dir  = self.settings['favourites_thumb_dir']
                    fanart_dir = self.settings['favourites_fanart_dir']
                    platform   = objects_dic[objectID]['platform']
                # ROM in launcher
                else:
                    thumb_dir  = self.launchers[launcherID]['thumbpath']
                    fanart_dir = self.launchers[launcherID]['fanartpath']
                    platform   = self.launchers[launcherID]['platform']
                ROM = misc_split_path(objects_dic[objectID]['filename'])
                rom_base_noext = ROM.base_noext # Used by offline scrapers only
                image_path_noext = misc_get_thumb_path_noext(thumb_dir, fanart_dir, ROM.base_noext)                
        elif image_kind == IMAGE_FANART:
            scraper_obj = self.scraper_fanart
            image_key   = 'fanart'
            image_name  = 'Fanart'
            if objects_kind == KIND_LAUNCHER:
                platform = objects_dic[objectID]['platform']
                kind_name = 'Launcher'
                launchers_thumb_dir  = self.settings['launchers_thumb_dir']
                launchers_fanart_dir = self.settings['launchers_fanart_dir']
                dest_basename = objects_dic[objectID]['name']
                rom_base_noext = '' # Used by offline scrapers only
                image_path_noext = misc_get_fanart_path_noext(launchers_thumb_dir, launchers_fanart_dir, dest_basename)
            elif objects_kind == KIND_ROM:
                kind_name = 'ROM'
                # ROM in favourites
                if launcherID == VLAUNCHER_FAV_ID:
                    thumb_dir  = self.settings['favourites_thumb_dir']
                    fanart_dir = self.settings['favourites_fanart_dir']
                    platform   = objects_dic[objectID]['platform']
                # ROM in launcher
                else:
                    thumb_dir  = self.launchers[launcherID]['thumbpath']
                    fanart_dir = self.launchers[launcherID]['fanartpath']
                    platform   = self.launchers[launcherID]['platform']
                ROM = misc_split_path(objects_dic[objectID]['filename'])
                rom_base_noext = ROM.base_noext # Used by offline scrapers only
                image_path_noext = misc_get_fanart_path_noext(thumb_dir, fanart_dir, ROM.base_noext)                
        log_debug('_gui_scrap_image_semiautomatic() Editing {0} {1}'.format(kind_name, image_name))
        local_image = misc_look_for_image(image_path_noext, IMG_EXTS)

        # --- Ask user to edit the image search string ---
        keyboard = xbmc.Keyboard(objects_dic[objectID]['name'], 'Enter the string to search for...')
        keyboard.doModal()
        if not keyboard.isConfirmed(): return False
        search_string = keyboard.getText()

        # --- Call scraper and get a list of games ---
        # IMPORTANT Setting Kodi busy notification prevents the user to control the UI when a dialog with handler -1
        #           has been called and nothing is displayed.
        #           THIS PREVENTS THE RACE CONDITIONS THAT CAUSE TROUBLE IN ADVANCED LAUNCHER!!!
        kodi_busydialog_ON()
        results = scraper_obj.get_search(search_string, rom_base_noext, platform)
        kodi_busydialog_OFF()
        log_debug('{0} scraper found {1} result/s'.format(image_name, len(results)))
        if not results:
            kodi_dialog_OK('Advanced Emulator Launcher', 'Scraper found no matches.')
            log_debug('{0} scraper did not found any game'.format(image_name))
            return False

        # --- Choose game to download image ---
        # Display corresponding game list found so user choses
        dialog = xbmcgui.Dialog()
        rom_name_list = []
        for game in results:
            rom_name_list.append(game['display_name'])
        selectgame = dialog.select('Select game for {0}'.format(search_string), rom_name_list)
        if selectgame < 0:
            # >> User canceled select dialog
            return False

        # --- Grab list of images for the selected game ---
        # >> Prevent race conditions
        kodi_busydialog_ON()
        image_list = scraper_obj.get_images(results[selectgame])
        kodi_busydialog_OFF()
        log_verb('{0} scraper returned {1} images'.format(image_name, len(image_list)))
        if not image_list:
            kodi_dialog_OK('Advanced Emulator Launcher', 'Scraper found no images.')
            return False

        # --- Always do semi-automatic scraping when editing images ---
        # If there is a local image add it to the list and show it to the user
        if os.path.isfile(local_image):
            image_list.insert(0, {'name' : 'Current local image', 'URL' : local_image, 'disp_URL' : local_image} )

        # Returns a list of dictionaries {'name', 'URL', 'disp_URL'}
        image_url = gui_show_image_select(image_list)
        log_debug('{0} dialog returned image_url "{1}"'.format(image_name, image_url))
        if image_url == '': image_url = image_list[0]['URL']

        # --- If user chose the local image don't download anything ---
        if image_url != local_image:
            # ~~~ Download scraped image ~~~
            # Get Tumb/Fanart name with no extension, then get URL image extension
            # and make full thumb path. If extension cannot be determined
            # from URL defaul to '.jpg'
            img_ext    = text_get_image_URL_extension(image_url) # Includes front dot -> .jpg
            image_path = image_path_noext + img_ext

            # ~~~ Download image ~~~
            log_debug('image_path_noext "{0}"'.format(image_path_noext))
            log_debug('img_ext          "{0}"'.format(img_ext))
            log_verb('Downloading URL  "{0}"'.format(image_url))
            log_verb('Into local file  "{0}"'.format(image_path))
            # >> Prevent race conditions
            kodi_busydialog_ON()
            try:
                net_download_img(image_url, image_path)
            except socket.timeout:
                kodi_notify_warn('Advanced Emulator Launcher',
                                 'Cannot download {0} image (Timeout)'.format(image_name))
            kodi_busydialog_OFF()

            # ~~~ Update Kodi cache with downloaded image ~~~
            # Recache only if local image is in the Kodi cache, this function takes care of that.
            kodi_update_image_cache(image_path)
        else:
            log_debug('{0} scraper: user chose local image "{1}"'.format(image_name, local_image))
            # >> If current image is same as found local image then there is nothing to update
            if objects_dic[objectID][image_key] == local_image: 
                log_debug('Local image already in object. Returning False')
                return False
            image_path = local_image

        # --- Edit using Python pass by assigment ---
        # >> Caller is responsible to save launchers/ROMs
        objects_dic[objectID][image_key] = image_path

        return True

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
        if launcherID == VLAUNCHER_FAV_ID:
            platform = roms[romID]['platform']
        else:
            launcher = self.launchers[launcherID]
            platform = launcher['platform']
        f_path   = roms[romID]['filename']
        rom_name = roms[romID]['name']
        ROM      = misc_split_path(f_path)
        scan_clean_tags            = self.settings['scan_clean_tags']
        scan_ignore_scrapped_title = self.settings['scan_ignore_scrapped_title']

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
        log_debug('_gui_scrap_rom_metadata() Metadata scraper found {0} result/s'.format(len(results)))
        if not results:
            kodi_notify_warn('Advanced Emulator Launcher', 'Scraper found no matches')
            return False
            
        # Display corresponding game list found so user choses
        dialog = xbmcgui.Dialog()
        rom_name_list = []
        for game in results:
            rom_name_list.append(game['display_name'])
        selectgame = dialog.select('Select game for ROM {0}'.format(rom_name), rom_name_list)
        if selectgame < 0: 
            # >> User canceled select dialog
            return False

        # --- Grab metadata for selected game ---
        # >> Prevent race conditions
        kodi_busydialog_ON()
        gamedata = self.scraper_metadata.get_metadata(results[selectgame])
        kodi_busydialog_OFF()
        if not gamedata:
            kodi_notify_warn('Advanced Emulator Launcher', 'Cannot download game metadata.')
            return False

        # --- Put metadata into ROM dictionary ---
        # >> Ignore scraped title
        if scan_ignore_scrapped_title:
            roms[romID]['name'] = text_ROM_title_format(ROM.base_noext, scan_clean_tags)
            log_debug("User wants to ignore scraper name. Setting name to '{0}'".format(roms[romID]['name']))
        # >> Use scraped title
        else:
            roms[romID]['name'] = gamedata['title']
            log_debug("User wants scrapped name. Setting name to '{0}'".format(roms[romID]['name']))
        roms[romID]['genre']  = gamedata['genre']
        roms[romID]['year']   = gamedata['year']
        roms[romID]['studio'] = gamedata['studio']
        roms[romID]['plot']   = gamedata['plot']

        # >> Changes were made
        kodi_notify('Advanced Emulator Launcher', 'ROM metadata updated')
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
        keyboard = xbmc.Keyboard(self.launchers[launcherID]['name'], 'Enter the launcher search string ...')
        keyboard.doModal()
        if not keyboard.isConfirmed(): return False
        search_string = keyboard.getText()

        # Scrap and get a list of matches
        kodi_busydialog_ON()
        results = self.scraper_metadata.get_search(search_string, '', platform)
        kodi_busydialog_OFF()
        log_debug('_gui_scrap_launcher_metadata() Metadata scraper found {0} result/s'.format(len(results)))
        if not results:
            kodi_notify_warn('Advanced Emulator Launcher', 'Scraper found no matches')
            return False

        # Display corresponding game list found so user choses
        dialog = xbmcgui.Dialog()
        rom_name_list = []
        for game in results:
            rom_name_list.append(game['display_name'])
        selectgame = dialog.select('Select game for ROM {0}'.format(rom_name), rom_name_list)
        if selectgame < 0: 
            return False

        # --- Grab metadata for selected game ---
        # >> Prevent race conditions
        kodi_busydialog_ON()
        gamedata = self.scraper_metadata.get_metadata(results[selectgame])
        kodi_busydialog_OFF()
        if not gamedata:
            kodi_notify_warn('Advanced Emulator Launcher', 'Cannot download game metadata.')
            return False

        # --- Put metadata into launcher dictionary ---
        # >> Scraper should not change launcher title
        self.launchers[launcherID]['genre']  = gamedata['genre']
        self.launchers[launcherID]['year']   = gamedata['year']
        self.launchers[launcherID]['studio'] = gamedata['studio']
        self.launchers[launcherID]['plot']   = gamedata['plot']

        # >> Changes were made
        return True

    #
    # Edit launcher/rom thumbnail/fanart. Note that categories have another function because
    # image scraping is not allowed for categores.
    #
    # NOTE When editing ROMs optional parameter launcherID is required.
    # NOTE Caller is responsible for saving the Launchers/ROMs
    # NOTE if image is changed container should be updated so the user sees new image instantly
    # NOTE objects_dic is edited by assigment
    # NOTE a ROM in Favourites has launcherID = '0'
    #
    # Returns:
    #   True   Launchers/ROMs must be saved and container updated
    #   False  No changes were made. No necessary to refresh container
    #
    def _gui_edit_image(self, image_kind, objects_kind, objects_dic, objectID, launcherID=''):
        # Check for errors
        if image_kind != IMAGE_THUMB and image_kind != IMAGE_FANART:
            log_error('_gui_edit_image() Unknown image_kind = {0}'.format(image_kind))
            kodi_notify_warn('Advanced Emulator Launcher', 'Unknown image_kind = {0}'.format(image_kind))
            return False
        if objects_kind != KIND_LAUNCHER and objects_kind != KIND_ROM:
            log_error('_gui_edit_image() Unknown objects_kind = {0}'.format(objects_kind))
            kodi_notify_warn('Advanced Emulator Launcher', 'Unknown objects_kind = {0}'.format(objects_kind))
            return False

        # Customise function depending of object to edit
        if image_kind == IMAGE_THUMB:
            scraper_obj = self.scraper_thumb
            image_key   = 'thumb'
            image_name  = 'Thumb'
            if objects_kind == KIND_LAUNCHER:
                kind_name = 'Launcher'
                launchers_thumb_dir  = self.settings['launchers_thumb_dir']
                launchers_fanart_dir = self.settings['launchers_fanart_dir']
                dest_basename   = objects_dic[objectID]['name']
                dest_path_noext = misc_get_thumb_path_noext(launchers_thumb_dir, launchers_fanart_dir, dest_basename)
            elif objects_kind == KIND_ROM:
                kind_name = 'ROM'
                # Thumb of a ROM in Favourites
                if launcherID == VLAUNCHER_FAV_ID:
                    thumb_dir  = self.settings['favourites_thumb_dir']
                    fanart_dir = self.settings['favourites_fanart_dir']
                # Thumb of a ROM in a Launcher
                else:
                    thumb_dir  = self.launchers[launcherID]['thumbpath']
                    fanart_dir = self.launchers[launcherID]['fanartpath']
                ROM = misc_split_path(objects_dic[objectID]['filename'])
                dest_path_noext = misc_get_thumb_path_noext(thumb_dir, fanart_dir, ROM.base_noext)
        elif image_kind == IMAGE_FANART:
            scraper_obj = self.scraper_fanart
            image_key   = 'fanart'
            image_name  = 'Fanart'
            if objects_kind == KIND_LAUNCHER:
                kind_name = 'Launcher'
                launchers_thumb_dir  = self.settings['launchers_thumb_dir']
                launchers_fanart_dir = self.settings['launchers_fanart_dir']
                dest_basename   = objects_dic[objectID]['name']
                dest_path_noext = misc_get_fanart_path_noext(launchers_thumb_dir, launchers_fanart_dir, dest_basename)
            elif objects_kind == KIND_ROM:
                kind_name = 'ROM'
                # Fanart in a ROM in Favourites
                if launcherID == VLAUNCHER_FAV_ID:
                    thumb_dir  = self.settings['favourites_thumb_dir']
                    fanart_dir = self.settings['favourites_fanart_dir']
                # Fanart of a ROM in a Launcher
                else:
                    thumb_dir  = self.launchers[launcherID]['thumbpath']
                    fanart_dir = self.launchers[launcherID]['fanartpath']
                ROM = misc_split_path(objects_dic[objectID]['filename'])
                dest_path_noext = misc_get_fanart_path_noext(thumb_dir, fanart_dir, ROM.base_noext)
        log_debug('_gui_edit_image() Editing {0} {1}'.format(kind_name, image_name))

        # Show image editing options
        dialog = xbmcgui.Dialog()
        type2 = dialog.select('Change Thumbnail Image',
                             ['Select Local Image',
                              'Import Local Image (Copy and Rename)',
                              'Scrape Image from {0}'.format(scraper_obj.fancy_name) ])
        # Link to an image
        if type2 == 0:
            if objects_dic[objectID][image_key] != '':
                F = misc_split_path(objects_dic[objectID][image_key])
                image_dir = F.dirname
            else:
                image_dir = ''
            log_debug('_gui_edit_image() Initial path "{0}"'.format(image_dir))
            image_file = xbmcgui.Dialog().browse(2, 'Select {0} image'.format(image_name),
                                                 'files', '.jpg|.jpeg|.gif|.png', True, False, image_dir)
            if not image_file or not os.path.isfile(image_file): return False

            # Update object by assigment. XML will be save by parent
            objects_dic[objectID][image_key] = image_file
            kodi_notify('Advanced Emulator Launcher', '{0} has been updated'.format(image_name))
            log_debug('_gui_edit_image() Object is {0} with ID = {1}'.format(kind_name, objectID))
            log_info('Selected {0} {1} "{2}"'.format(kind_name, image_name, image_file))

            # --- Update Kodi image cache ---
            kodi_update_image_cache(image_file)

        # Import an image
        elif type2 == 1:
            if objects_dic[objectID][image_key] != '':
                F = misc_split_path(objects_dic[objectID][image_key])
                image_dir = F.dirname
            else:
                image_dir = ''
            log_debug('_gui_edit_image() Initial path "{0}"'.format(image_dir))
            image_file = xbmcgui.Dialog().browse(2, 'Select {0} image'.format(image_name),
                                                 'files', '.jpg|.jpeg|.gif|.png', True, False, image_dir)
            if not image_file or not os.path.isfile(image_file): return False

            # Determine image extension and dest filename
            F = misc_split_path(image_file)
            dest_path = dest_path_noext + F.ext
            log_debug('_gui_edit_image() image_file    = "{0}"'.format(image_file))
            log_debug('_gui_edit_image() img_ext       = "{0}"'.format(F.ext))
            log_debug('_gui_edit_image() dest_path     = "{0}"'.format(dest_path))

            # Copy image file
            if image_file == dest_path:
                log_info('image_file and dest_path are the same. Returning')
                return False
            try:
                fs_encoding = get_fs_encoding()
                shutil.copy(image_file.decode(fs_encoding, 'ignore') , dest_path.decode(fs_encoding, 'ignore'))
            except OSError:
                kodi_notify_warn('Advanced Emulator Launcher', 'OSError when copying image')

            # Update object by assigment. XML will be save by parent
            objects_dic[objectID][image_key] = dest_path
            kodi_notify('Advanced Emulator Launcher', '{0} has been updated'.format(image_name))
            log_debug('_gui_edit_image() Object is {0} with ID = {1}'.format(kind_name, objectID))
            log_info('Copied image "{0}"'.format(image_file))
            log_info('Into         "{0}"'.format(dest_path))
            log_info('Selected {0} {1} "{2}"'.format(kind_name, image_name, dest_path))

            # --- Update Kodi image cache ---
            kodi_update_image_cache(dest_path)

        # Manual scrape and choose from a list of images
        elif type2 == 2:
            return self._gui_scrap_image_semiautomatic(image_kind, objects_kind, objects_dic, objectID, launcherID)

        # User canceled select box
        elif type2 < 0:
            return False

        # If we reach this point, changes were made. Launchers/ROMs must be saved, container must be refreshed.
        return True

    #
    # Edit category thumb/fanart.
    #
    # NOTE For some reason option 'Import Local Image (Copy and Rename)' does not work well. I have checked
    #      the copied filename is OK but Kodi refuses to display the image...
    #      Even more suprisingly, if later 'Select Local Image' is used and the file copied before to categories
    #      artwork path is chosen then it works!
    #
    # Returns:
    #   True   Changes were made.
    #   False  No changes made.
    #
    def _gui_edit_category_image(self, image_kind, categoryID):
        # Make this function as generic as possible to share code with launcher/rom thumb/fanart editing.
        if image_kind == IMAGE_THUMB:
            objects_dic  = self.categories
            objectID     = categoryID
            image_key    = 'thumb'
            image_name   = 'Thumb'
            # If user set same path for thumb/fanart then a suffix must be added
            categories_thumb_dir  = self.settings['categories_thumb_dir']
            categories_fanart_dir = self.settings['categories_fanart_dir']
            dest_basename   = objects_dic[objectID]['name']
            dest_path_noext = misc_get_thumb_path_noext(categories_thumb_dir, categories_fanart_dir, dest_basename)
        elif image_kind == IMAGE_FANART:
            objects_dic  = self.categories
            objectID     = categoryID
            image_key    = 'fanart'
            image_name   = 'Fanart'
            categories_thumb_dir  = self.settings['categories_thumb_dir']
            categories_fanart_dir = self.settings['categories_fanart_dir']
            dest_basename   = objects_dic[objectID]['name']
            dest_path_noext = misc_get_fanart_path_noext(categories_thumb_dir, categories_fanart_dir, dest_basename)
        else:
            log_error('_gui_edit_category_image() Unknown image_kind = {0}'.format(image_kind))
            kodi_notify_warn('Advanced Emulator Launcher', 'Unknown image_kind = {0}'.format(image_kind))
            return False
        log_debug('_gui_edit_category_image() Editing {0}'.format(image_name))

        # Show image editing options
        dialog = xbmcgui.Dialog()
        type2 = dialog.select('Change Thumbnail Image',
                             ['Select Local Image',
                              'Import Local Image (Copy and Rename)'])
        # Link to an image
        if type2 == 0:
            if objects_dic[objectID][image_key] != '':
                F = misc_split_path(objects_dic[objectID][image_key])
                image_dir = F.dirname
            else:
                image_dir = ''
            log_debug('_gui_edit_category_image() Initial path "{0}"'.format(image_dir))
            image_file = xbmcgui.Dialog().browse(2, 'Select {0} image'.format(image_name),
                                                 'files', '.jpg|.jpeg|.gif|.png', True, False, image_dir)
            if not image_file or not os.path.isfile(image_file): return False

            # Update object by assigment. XML will be save by parent
            objects_dic[objectID][image_key] = image_file
            kodi_notify('Advanced Emulator Launcher', '{0} has been updated'.format(image_name))
            log_debug('_gui_edit_category_image() Object is {0} with ID = {1}'.format('Category', objectID))
            log_info('Selected {0} "{1}"'.format(image_name, image_file))

            # --- Update Kodi image cache ---
            kodi_update_image_cache(image_file)

        # Import an image
        elif type2 == 1:
            if objects_dic[objectID][image_key] != '':
                F = misc_split_path(objects_dic[objectID][image_key])
                image_dir = F.dirname
            else:
                image_dir = ''
            log_debug('_gui_edit_category_image() Initial path "{0}"'.format(image_dir))
            image_file = xbmcgui.Dialog().browse(2, 'Select {0} image'.format(image_name),
                                                 'files', ".jpg|.jpeg|.gif|.png", True, False, image_dir)
            if not image_file or not os.path.isfile(image_file): return False

            # Determine image extension and dest filename
            F = misc_split_path(image_file)
            dest_path = dest_path_noext + F.ext
            log_debug('_gui_edit_category_image() image_file    = "{0}"'.format(image_file))
            log_debug('_gui_edit_category_image() img_ext       = "{0}"'.format(F.ext))
            log_debug('_gui_edit_category_image() dest_path     = "{0}"'.format(dest_path))

            # Copy image file, but never over itself
            if image_file == dest_path: 
                log_info('image_file and dest_path are the same. Returning')
                return False
            try:
                fs_encoding = get_fs_encoding()
                shutil.copy(image_file.decode(fs_encoding, 'ignore') , dest_path.decode(fs_encoding, 'ignore'))
            except OSError:
                kodi_notify_warn('Advanced Emulator Launcher', 'OSError when copying image')

            # Update object and save XML
            objects_dic[objectID][image_key] = dest_path
            kodi_notify('Advanced Emulator Launcher', '{0} has been updated'.format(image_name))
            log_debug('_gui_edit_category_image() Object is {0} with ID = {1}'.format('Category', objectID))
            log_info('Copied image "{0}"'.format(image_file))
            log_info('Into         "{0}"'.format(dest_path))
            log_info('Selected {0} "{1}"'.format(image_name, dest_path))

            # --- Update Kodi image cache ---
            kodi_update_image_cache(dest_path)

        # User canceled select box
        elif type2 < 0:
            return False

        return True

    #
    # Creates default categories data struct.
    # CAREFUL deletes current categories!
    #
    def _cat_create_default(self):
        # The key in the categories dictionary is an MD5 hash generate with current time plus some random number.
        # This will make it unique and different for every category created.
        category = fs_new_category()
        category['name'] = 'Emulators'
        category_key = misc_generate_random_SID()
        category['id'] = category_key
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
            ret = kodi_dialog_yesno('Advanced Emulator Launcher',
                                    'File "{0}" has {1} bytes and it is very big.'.format(text_file, file_size) +
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
            listitem = xbmcgui.ListItem(label=name_str, label2=URL_str, iconImage='DefaultAddonImages.png', thumbnailImage=URL_str)
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

# >> From DialogSelect.xml in Confluence (Kodi Krypton taken from Github master)
# >> Controls 5 and 7 are grouped
# <control type="label"  id="1"> | <description>header label</description>      | Window title on top
# control 2 does not exist
# <control type="list"   id="3"> |                                              | Another container which I don't understand...
# <control type="label"  id="4"> | <description>No Settings Label</description>
# <control type="button" id="5"> | <description>Manual button</description>     | OK button
# <control type="list"   id="6"> |                                              | Listbox
# <control type="button" id="7"> | <description>Cancel button</description>     | New Krypton cancel button
class ImgSelectDialog_Old(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        xbmc.executebuiltin("Skin.Reset(AnimeWindowXMLDialogClose)")
        xbmc.executebuiltin("Skin.SetBool(AnimeWindowXMLDialogClose)")

        # This is the list of lists returned by the scraper.
        # In case of TheGamesDB each sublist is: [ URL, URL, 'Cover covername' ]
        # First element is always the current image: [ rom["thumb"], rom["thumb"], 'Current image' ]
        self.listing = kwargs.get( "listing" )
        self.selected_url = ''

    # I guess this is executed at the beginning
    def onInit(self):
        try:
            self.img_list = self.getControl(6)
            # Prevents moving to the cancel button. Note that the cancel button does not show
            # on Cirrus Extended.
            self.img_list.controlLeft(self.img_list)
            self.img_list.controlRight(self.img_list)
            self.getControl(3).setVisible(False)
        except:
            print_exc()
            self.img_list = self.getControl(3)

        self.getControl(5).setVisible(False) # Upper button on the left (OK button)
        # self.getControl(7).setVisible(False) # Lower button on the left (Cancel)
        # self.getControl(1).setVisible(False) # Window title

        for index, item in enumerate(self.listing):
            listitem = xbmcgui.ListItem(item[2]) # string image name
            listitem.setIconImage(item[1])       # Image URL (http://)
            listitem.setLabel2(item[0])          # Image URL (http://)
            self.img_list.addItem(listitem)

        self.setFocus(self.img_list)

    def onAction(self, action):
        # Close the script
        if action == 10:
            self.close()

    def onClick(self, controlID):
        # Action sur la liste
        if controlID == 6 or controlID == 3:
            # Renvoie l'item selectionne
            num = self.img_list.getSelectedPosition()
            self.selected_url = self.img_list.getSelectedItem().getLabel2()
            self.close()

    def onFocus(self, controlID):
        pass

def gui_show_image_select(img_list):
    # The xml file needs to be part of your addon, or included in the skin you use.
    # Yes, DialogSelect.xml is defined in Confluence here
    # https://github.com/xbmc/skin.confluence/blob/master/720p/DialogSelect.xml
    # w = ImgSelectDialog("DialogSelect.xml", BASE_DIR, listing = img_list)

    # See comments above.
    w = ImgSelectDialog('DialogSelect.xml', BASE_DIR, listing = img_list)

    # Execute dialog
    w.doModal()
    selected_url = w.selected_url
    del w

    return selected_url
