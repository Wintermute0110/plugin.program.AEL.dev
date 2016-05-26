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
import re, urllib, urllib2, urlparse, socket, exceptions

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
PLUGIN_DATA_DIR      = xbmc.translatePath(os.path.join('special://profile/addon_data', __addon_id__))
BASE_DIR             = xbmc.translatePath(os.path.join('special://', 'profile'))
HOME_DIR             = xbmc.translatePath(os.path.join('special://', 'home'))
KODI_FAV_FILE_PATH   = xbmc.translatePath('special://profile/favourites.xml')
ADDONS_DIR           = xbmc.translatePath(os.path.join(HOME_DIR, 'addons'))
CURRENT_ADDON_DIR    = xbmc.translatePath(os.path.join(ADDONS_DIR, __addon_id__))
ICON_IMG_FILE_PATH   = os.path.join(CURRENT_ADDON_DIR, 'icon.png')
CATEGORIES_FILE_PATH = os.path.join(PLUGIN_DATA_DIR, 'categories.xml')
FAVOURITES_FILE_PATH = os.path.join(PLUGIN_DATA_DIR, 'favourites.xml')
# Artwork and NFO for Categories and Launchers
DEFAULT_THUMB_DIR    = os.path.join(PLUGIN_DATA_DIR, 'thumbs')
DEFAULT_FANART_DIR   = os.path.join(PLUGIN_DATA_DIR, 'fanarts')
DEFAULT_NFO_DIR      = os.path.join(PLUGIN_DATA_DIR, 'nfos')
KIND_CATEGORY        = 0
KIND_LAUNCHER        = 1
KIND_ROM             = 2
IMAGE_THUMB          = 100
IMAGE_FANART         = 200
DESCRIPTION_MAXSIZE  = 40
IMG_EXTS             = ['png', 'jpg', 'gif', 'jpeg', 'bmp', 'PNG', 'JPG', 'GIF', 'JPEG', 'BMP']

# --- Main code ---
class Main:
    settings   = {}
    categories = {}
    launchers  = {}
    roms       = {}
    scraper_metadata = None
    scraper_thumb    = None
    scraper_fanart   = None

    #
    # This is the plugin entry point.
    #
    def run_plugin(self):
        # --- Initialise log system ---
        # DEBUG log level for development. Place it before setting loading so settings can be
        # dumped during debugging.
        set_log_level(LOG_DEBUG)

        # --- Fill in settings dictionary using addon_obj.getSetting() ---
        self._get_settings()
        # set_log_level(self.settings['log_level'])

        # --- Some debug stuff for development ---
        log_debug('---------- Called AEL addon.py Main() constructor ----------')
        # log_debug(sys.version)
        # log_debug('__addon_name__ {}'.format(__addon_name__))
        log_debug('__addon_id__   {}'.format(__addon_id__))
        log_debug('__version__    {}'.format(__version__))
        # log_debug('__author__     {}'.format(__author__))
        log_debug('__profile__    {}'.format(__profile__))
        # log_debug('__type__       {}'.format(__type__))
        for i in range(len(sys.argv)):
            log_debug('sys.argv[{0}] = "{1}"'.format(i, sys.argv[i]))
        # log_debug('PLUGIN_DATA_DIR      = "{}"'.format(PLUGIN_DATA_DIR))
        # log_debug('CURRENT_ADDON_DIR    = "{}"'.format(CURRENT_ADDON_DIR))
        # log_debug('CATEGORIES_FILE_PATH = "{}"'.format(CATEGORIES_FILE_PATH))
        # log_debug('FAVOURITES_FILE_PATH = "{}"'.format(FAVOURITES_FILE_PATH))

        # --- Addon data paths creation ---
        if not os.path.isdir(PLUGIN_DATA_DIR):    os.makedirs(PLUGIN_DATA_DIR)
        if not os.path.isdir(DEFAULT_THUMB_DIR):  os.makedirs(DEFAULT_THUMB_DIR)
        if not os.path.isdir(DEFAULT_FANART_DIR): os.makedirs(DEFAULT_FANART_DIR)
        if not os.path.isdir(DEFAULT_NFO_DIR):    os.makedirs(DEFAULT_NFO_DIR)

        # ~~~~~ Process URL ~~~~~
        self.base_url = sys.argv[0]
        self.addon_handle = int(sys.argv[1])
        args = urlparse.parse_qs(sys.argv[2][1:])
        log_debug('args = {0}'.format(args))
        # Interestingly, if plugin is called as type executable then args is empty.
        # However, if plugin is called as type video then Kodi adds the following
        # even for the first call: 'content_type': ['video']
        self.content_type = args['content_type'] if 'content_type' in args else None
        log_debug('content_type = {}'.format(self.content_type))

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
        # create an empty one with a default launcher. Later on, when I am more familiar
        # with the addon add a welcome wizard or something similar.
        #
        # Create a default categories.xml file if does not exist yet (plugin just installed)
        if not os.path.isfile(CATEGORIES_FILE_PATH):
            kodi_dialog_OK('Advanced Emulator Launcher',
                           'It looks it is the first time you run Advanced Emulator Launcher! ' +
                           'A default categories.xml has been created. You can now customise it to your needs.')
            self._cat_create_default()
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

        # --- Load categories.xml and fill categories and launchers dictionaries ---
        (self.categories, self.launchers) = fs_load_catfile(CATEGORIES_FILE_PATH)

        # --- Load scrapers ---
        self._load_scrapers()

        # If no com parameter display categories. Display categories listbox (addon root directory)
        if 'com' not in args:
            self._gui_render_categories()
            log_debug('AEL exiting after rendering Categories (addon root)')
            return

        # There is a command to process
        # For some reason args['com'] is a list, so get first element of the list (a string)
        command = args['com'][0]
        if command == 'ADD_CATEGORY':
            self._command_add_new_category()
        elif command == 'EDIT_CATEGORY':
            self._command_edit_category(args['catID'][0])
        elif command == 'DELETE_CATEGORY':
            kodi_dialog_OK('ERROR', 'DELETE_CATEGORY not implemented yet')
        elif command == 'SHOW_FAVOURITES':
            self._command_show_favourites()
        elif command == 'SHOW_LAUNCHERS':
            self._gui_render_launchers(args['catID'][0])
        elif command == 'ADD_LAUNCHER':
            self._command_add_new_launcher(args['catID'][0])
        elif command == 'EDIT_LAUNCHER':
            self._command_edit_launcher(args['launID'][0])
        elif command == 'DELETE_LAUNCHER':
            kodi_dialog_OK('ERROR', 'DELETE_LAUNCHER not implemented yet')
        # User clicked on a launcher. For standalone launchers run the executable.
        # For emulator launchers show roms.
        elif command == 'SHOW_ROMS':
            launcherID = args['launID'][0]
            if self.launchers[launcherID]["rompath"] == '':
                log_debug('SHOW_ROMS | Launcher rompath is empty. Assuming launcher is standalone.')
                log_debug('SHOW_ROMS | Calling _run_launcher()')
                self._run_standalone_launcher(args['catID'][0], args['launID'][0])
            else:
                log_debug('SHOW_ROMS | Calling _gui_render_roms()')
                self._gui_render_roms(args['catID'][0], args['launID'][0])
        elif command == 'ADD_ROMS':
            self._command_add_roms(args['launID'][0])
        # Edit ROM from launcher or Favourites
        elif command == 'EDIT_ROM':
            self._command_edit_rom(args['catID'][0], args['launID'][0], args['romID'][0])
        # Delete ROM for launcher or Favourites
        elif command == 'DELETE_ROM':
             self._command_remove_rom(args['catID'][0], args['launID'][0], args['romID'][0])
        elif args['com'][0] == 'LAUNCH_ROM':
            self._run_rom(args['catID'][0], args['launID'][0], args['romID'][0])
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
        self.settings["scan_recursive"]         = True if addon_obj.getSetting("scan_recursive") == "true" else False
        self.settings["scan_ignore_bios"]       = True if addon_obj.getSetting("scan_ignore_bios") == "true" else False
        self.settings["scan_metadata_policy"]   = int(addon_obj.getSetting("scan_metadata_policy"))
        self.settings["scan_thumb_policy"]      = int(addon_obj.getSetting("scan_thumb_policy"))
        self.settings["scan_fanart_policy"]     = int(addon_obj.getSetting("scan_fanart_policy"))
        self.settings["scan_ignore_title"]      = True if addon_obj.getSetting("scan_ignore_title") == "true" else False
        self.settings["scan_clean_tags"]        = True if addon_obj.getSetting("scan_clean_tags") == "true" else False
        self.settings["scan_title_formatting"]  = True if addon_obj.getSetting("scan_title_formatting") == "true" else False
        
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
        
        self.settings["hide_finished"]          = True if addon_obj.getSetting("hide_finished") == "true" else False
        self.settings["launcher_notification"]  = True if addon_obj.getSetting("launcher_notification") == "true" else False
        self.settings["launcher_thumb_path"]    = addon_obj.getSetting("launcher_thumb_path")
        self.settings["launcher_fanart_path"]   = addon_obj.getSetting("launcher_fanart_path")
        self.settings["launcher_nfo_path"]      = addon_obj.getSetting("launcher_nfo_path")
        
        self.settings["media_state"]            = int(addon_obj.getSetting("media_state"))
        self.settings["lirc_state"]             = True if addon_obj.getSetting("lirc_state") == "true" else False
        self.settings["start_tempo"]            = int(round(float(addon_obj.getSetting("start_tempo"))))
        self.settings["log_level"]              = int(addon_obj.getSetting("log_level"))
        self.settings["show_batch_window"]      = True if addon_obj.getSetting("show_batch_window") == "true" else False
        
        # --- Example of how to transform a number into string ---
        # self.settings["game_region"]          = ['World', 'Europe', 'Japan', 'USA'][int(addon_obj.getSetting('game_region'))]

        # --- Dump settings for DEBUG ---
        # log_debug('Settings dump BEGIN')
        # for key in sorted(self.settings):
        #     log_debug('{} --> {:10s} {:}'.format(key.rjust(21), str(self.settings[key]), type(self.settings[key])))
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
        log_verb('Loaded metadata scraper  {}'.format(self.scraper_metadata.name))
        log_verb('Loaded thumb scraper     {}'.format(self.scraper_thumb.name))
        log_verb('Loaded fanart scraper    {}'.format(self.scraper_fanart.name))

        # Initialise metadata scraper plugin installation dir, for offline scrapers
        self.scraper_metadata.set_addon_dir(CURRENT_ADDON_DIR)

        # Initialise options of the thumb scraper
        region  = self.settings['scraper_region']
        thumb_imgsize = self.settings['scraper_thumb_size']
        self.scraper_thumb.set_options(region, thumb_imgsize)

        # Initialise options of the fanart scraper
        fanart_imgsize = self.settings['scraper_fanart_size']
        self.scraper_fanart.set_options(region, fanart_imgsize)

    # Creates default categories data struct
    # CAREFUL deletes current categories!
    # From _load_launchers
    # Else create the default category
    # self.categories["default"] = {"id":"default", "name":"Default", "thumb":"", "fanart":"", "genre":"", "plot":"", "finished":"false"}
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
    # Edit launcher/rom thumbnail/fanart. Note that categories have another function because
    # image scraping is not allowed for categores.
    #
    # NOTE When editing ROMs optinal parameter launcherID is required.
    # NOTE Caller is responsible for saving the Launchers/ROMs
    # NOTE if image is changed container should be updated so the user sees new image instantly
    # NOTE objects_dic is edited by assigment
    #
    # Returns:
    #   True   Launchers/ROMs must be saved and container updated
    #   False  No changes were made. No necessary to refresh container
    #
    def _gui_edit_image(self, image_kind, objects_kind, objects_dic, objectID, launcherID=''):
        # Check for errors
        if image_kind != IMAGE_THUMB and image_kind != IMAGE_FANART:
            log_error('_gui_edit_image() Unknown image_kind = {}'.format(image_kind))
            kodi_notify_warn('Advanced Emulator Launcher', 'Unknown image_kind = {}'.format(image_kind))
            return False
        if objects_kind != KIND_LAUNCHER and objects_kind != KIND_ROM:
            log_error('_gui_edit_image() Unknown objects_kind = {}'.format(objects_kind))
            kodi_notify_warn('Advanced Emulator Launcher', 'Unknown objects_kind = {}'.format(objects_kind))
            return False

        # Customise function depending of object to edit
        if image_kind == IMAGE_THUMB:
            image_key   = 'thumb'
            image_name  = 'Thumb'
            if objects_kind == KIND_LAUNCHER:
                object_name = 'Launcher'
                artwork_path = objects_dic[objectID]['thumbpath']
            elif objects_kind == KIND_ROM:
                object_name = 'ROM'
                # thumbpath/fanartpath are in the launcher data structure
                artwork_path = self.launchers[launcherID]['thumbpath']
        elif image_kind == IMAGE_FANART:
            image_key   = 'fanart'
            image_name  = 'Fanart'
            if objects_kind == KIND_LAUNCHER:
                object_name = 'Launcher'
                artwork_path = objects_dic[objectID]['fanartpath']
            elif objects_kind == KIND_ROM:
                object_name = 'ROM'
                artwork_path = self.launchers[launcherID]['fanartpath']
        log_debug('_gui_edit_image() Editing {} {}'.format(object_name, image_name))        

        # Show image editing options
        dialog = xbmcgui.Dialog()
        type2 = dialog.select('Change Thumbnail Image', 
                             ['Select Local Image',
                              'Import Local Image (Copy and Rename)',
                              'Scrape Image from {}'.format(self.scraper_thumb.fancy_name) ])
        # Link to an image
        if type2 == 0:
            image_dir = artwork_path if objects_dic[objectID][image_key] == '' else objects_dic[objectID][image_key]
            log_debug('_gui_edit_image() Initial path "{}"'.format(image_dir))
            image_file = xbmcgui.Dialog().browse(2, 'Select {} image'.format(image_name),
                                                 'files', '.jpg|.jpeg|.gif|.png', True, False, image_dir)
            if not image_file or not os.path.isfile(image_file): return False

            # --- Update object and save XML ---
            log_debug('_gui_edit_image() Object is {} with ID = {}'.format(object_name, objectID))
            if objects_kind == KIND_LAUNCHER:
                self.launchers[objectID][image_key] = image_file
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            elif objects_kind == KIND_ROM:
                objects_dic[objectID][image_key] = image_file
                launcher = self.launchers[launcherID]
                roms_xml_file = launcher['roms_xml_file']
                fs_write_ROM_XML_file(roms_xml_file, objects_dic, launcher)
            kodi_notify('Advanced Emulator Launcher', '{} has been updated'.format(image_name))
            log_info('Selected {} "{}"'.format(image_name, image_file))

            # --- Update Kodi image cache ---
            kodi_update_image_cache(image_file)

        # Import an image
        elif type2 == 1:
            image_dir = artwork_path if objects_dic[objectID][image_key] == '' else objects_dic[objectID][image_key]
            log_debug('_gui_edit_image() Initial path "{}"'.format(image_dir))
            image_file = xbmcgui.Dialog().browse(2, 'Select {} image'.format(image_name),
                                                 'files', '.jpg|.jpeg|.gif|.png', True, False, image_dir)
            if not image_file or not os.path.isfile(image_file): return False

            # Determine image extension and dest filename
            F = misc_split_path(image_file)
            dest_basename = objects_dic[objectID]['name']
            dest_path = os.path.join(artwork_path, dest_basename + '_' + image_key + F.ext)
            log_debug('_gui_edit_image() image_file    = "{0}"'.format(image_file))
            log_debug('_gui_edit_image() img_ext       = "{0}"'.format(F.ext))
            log_debug('_gui_edit_image() dest_basename = "{0}"'.format(dest_basename))
            log_debug('_gui_edit_image() dest_path     = "{0}"'.format(dest_path))

            # Copy image file
            if image_file == dest_path: 
                log_info('image_file and dest_path are the same. Returning')
                return
            try:
                fs_encoding = get_fs_encoding()
                shutil.copy(image_file.decode(fs_encoding, 'ignore') , dest_path.decode(fs_encoding, 'ignore'))
            except OSError:
                kodi_notify_warn('Advanced Emulator Launcher', 'OSError when copying image')

            # --- Update object and save XML ---
            log_debug('_gui_edit_image() Object is {} with ID = {}'.format(object_name, objectID))
            if objects_kind == KIND_LAUNCHER:
                self.launchers[objectID][image_key] = dest_path
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            elif objects_kind == KIND_ROM:
                objects_dic[objectID][image_key] = dest_path
                launcher = self.launchers[launcherID]
                roms_xml_file = launcher['roms_xml_file']
                fs_write_ROM_XML_file(roms_xml_file, objects_dic, launcher)
            kodi_notify('Advanced Emulator Launcher', '{} has been updated'.format(image_name))
            log_info('Copied image "{}"'.format(image_file))
            log_info('Into         "{}"'.format(dest_path))
            log_info('Selected {} "{}"'.format(image_name, dest_path))

            # --- Update Kodi image cache ---
            kodi_update_image_cache(dest_path)

        # Manual scrape and choose from a list of images
        elif type2 == 2:
            return self._gui_scrap_image_semiautomatic(image_kind, objects_kind, objects_dic, objectID, launcherID)

        # If we reach this point, changes were made. Launchers/ROMs must be saved, container must be refreshed.
        return True

    #
    # Edit category thumb/fanart.
    #
    # NOTE For some reason option 'Import Local Image (Copy and Rename)' does not work. I have checked
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
            objects_dic = self.categories
            objectID    = categoryID
            image_key   = 'thumb'
            image_name  = 'Thumb'
            if self.settings['launcher_thumb_path'] == '': artwork_path = DEFAULT_THUMB_DIR
            else:                                          artwork_path = self.settings['launcher_thumb_path']
        elif image_kind == IMAGE_FANART:
            objects_dic = self.categories
            objectID    = categoryID
            image_key   = 'fanart'
            image_name  = 'Fanart'
            if self.settings['launcher_fanart_path'] == '': artwork_path = DEFAULT_FANART_DIR
            else:                                           artwork_path = self.settings['launcher_fanart_path']
        else:
            log_error('_gui_edit_category_image() Unknown image_kind = {}'.format(image_kind))
            kodi_notify_warn('Advanced Emulator Launcher', 'Unknown image_kind = {}'.format(image_kind))
            return
        log_debug('_gui_edit_category_image() Editing {}'.format(image_name))

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
            log_debug('_gui_edit_category_image() Initial path "{}"'.format(image_dir))
            image_file = xbmcgui.Dialog().browse(2, 'Select {} image'.format(image_name),
                                                 'files', '.jpg|.jpeg|.gif|.png', True, False, image_dir)
            if not image_file or not os.path.isfile(image_file): return False

            # Update object and save XML
            log_debug('_gui_edit_category_image() Object is {} with ID = {}'.format('Category', objectID))
            objects_dic[objectID][image_key] = image_file
            kodi_notify('Advanced Emulator Launcher', '{} has been updated'.format(image_name))
            log_info('Selected {} "{}"'.format(image_name, image_file))

            # --- Update Kodi image cache ---
            kodi_update_image_cache(image_file)

        # Import an image
        elif type2 == 1:
            if objects_dic[objectID][image_key] != '':
                F = misc_split_path(objects_dic[objectID][image_key])
                image_dir = F.dirname
            else:
                image_dir = ''
            log_debug('_gui_edit_category_image() Initial path "{}"'.format(image_dir))
            image_file = xbmcgui.Dialog().browse(2, 'Select {} image'.format(image_name), 
                                                 "files", ".jpg|.jpeg|.gif|.png", True, False, image_dir)
            if not image_file or not os.path.isfile(image_file): return False

            # Determine image extension and dest filename
            F = misc_split_path(image_file)
            dest_basename = objects_dic[objectID]['name']
            dest_path = os.path.join(artwork_path, dest_basename + '_' + image_key + F.ext)
            log_debug('_gui_edit_category_image() image_file    = "{0}"'.format(image_file))
            log_debug('_gui_edit_category_image() img_ext       = "{0}"'.format(F.ext))
            log_debug('_gui_edit_category_image() dest_basename = "{0}"'.format(dest_basename))
            log_debug('_gui_edit_category_image() dest_path     = "{0}"'.format(dest_path))

            # Copy image file
            if image_file == dest_path: 
                log_info('image_file and dest_path are the same. Returning')
                return
            try:
                fs_encoding = get_fs_encoding()
                shutil.copy(image_file.decode(fs_encoding, 'ignore') , dest_path.decode(fs_encoding, 'ignore'))
            except OSError:
                kodi_notify_warn('Advanced Emulator Launcher', 'OSError when copying image')

            # Update object and save XML
            log_debug('_gui_edit_category_image() Object is {} with ID = {}'.format('Category', objectID))
            objects_dic[objectID][image_key] = dest_path
            kodi_notify('Advanced Emulator Launcher', '{} has been updated'.format(image_name))
            log_info('Copied image "{}"'.format(image_file))
            log_info('Into         "{}"'.format(dest_path))
            log_info('Selected {} "{}"'.format(image_name, dest_path))

            # --- Update Kodi image cache ---
            kodi_update_image_cache(dest_path)

        return True

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
                               'Category "{}" contains {} launchers. '.format(category_name, len(launcherID_list)) +
                               'Deleting it will also delete related launchers. ' +
                               'Are you sure you want to delete "{}"?'.format(category_name) )
            if ret:
                log_info('Deleting category "{}" id {}'.format(category_name, categoryID))
                # Delete launchers and ROM XML associated with them
                for launcherID in launcherID_list:
                    log_info('Deleting linked launcher "{}" id {}'.format(self.launchers[launcherID]['name'], launcherID))
                    roms_xml_file = self.launchers[launcherID]['roms_xml_file']
                    if os.path.isfile(roms_xml_file):
                        log_info('Deleting ROMs XML "{}"'.format(roms_xml_file))
                        os.remove(roms_xml_file)
                    self.launchers.pop(launcherID)
                # Delete category and make sure True is returned.
                self.categories.pop(categoryID)
            else:
                return False
        else:
            ret = dialog.yesno('Advanced Emulator Launcher',
                               'Category "{}" contains {} launchers. '.format(category_name, len(launcherID_list)) +
                               'Are you sure you want to delete "{}"?'.format(category_name) )
            if ret:
                log_info('Deleting category "{}" id {}'.format(category_name, categoryID))
                log_info('Category has no launchers, so no launchers to delete.')
                self.categories.pop(categoryID)
            else:
                return False
        
        return True

    #
    # Reads a text file with category/launcher description. Checks file size to avoid importing binary files!
    #
    def _gui_import_TXT_file(text_file):
        # Warn user in case he chose a binary file or a very big one. Avoid categories.xml corruption.
        log_debug('_gui_import_TXT_file() Importing plot from "{}"'.format(text_file))
        statinfo = os.stat(text_file)
        file_size = statinfo.st_size
        log_debug('_gui_import_TXT_file() File size is {}'.format(file_size))
        if file_size > 16384:
            ret = kodi_dialog_yesno('Advanced Emulator Launcher',
                                    'File "{}" has {} bytes and it is very big.'.format(text_file, file_size) + 
                                    'Are you sure this is the correct file?')
            if not ret: return ''

        # Import file
        log_debug('_gui_import_TXT_file() Importing description from "{}"'.format(text_file))
        text_plot = open(text_file, 'rt')
        file_data = text_plot.read()
        text_plot.close()

        return file_data

    def _command_edit_category(self, categoryID):
        # Shows a select box with the options to edit
        dialog = xbmcgui.Dialog()
        finished_display = 'Status: Finished' if self.categories[categoryID]["finished"] == True else 'Status: Unfinished'
        type = dialog.select('Select action for category {}'.format(self.categories[categoryID]["name"]), 
                             ['Edit Title/Genre/Description...', 'Edit Thumbnail Image...', 'Edit Fanart Image...', 
                              finished_display, 'Delete Category'])
        # Edit metadata
        if type == 0:
            desc_str = text_limit_string(self.categories[categoryID]["description"], DESCRIPTION_MAXSIZE)
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Edit Category Metadata', 
                                  ["Edit Title: '{}'".format(self.categories[categoryID]["name"]),
                                   "Edit Genre: '{}'".format(self.categories[categoryID]["genre"]),
                                   "Edit Description: '{}'".format(desc_str),
                                   'Import Description from file...' ])
            # Edition of the category name
            if type2 == 0:
                keyboard = xbmc.Keyboard(self.categories[categoryID]["name"], 'Edit Title')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    title = keyboard.getText()
                    if title == "":
                        title = self.categories[categoryID]["name"]
                    self.categories[categoryID]["name"] = title.rstrip()
                else:
                    kodi_dialog_OK('Advanced Emulator Launcher - Information', 
                                   "Category name '{}' not changed".format(self.categories[categoryID]["name"]))
                    return
            # Edition of the category genre
            elif type2 == 1:
                keyboard = xbmc.Keyboard(self.categories[categoryID]["genre"], 'Edit Genre')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    self.categories[categoryID]["genre"] = keyboard.getText()
                else:
                    kodi_dialog_OK('Advanced Emulator Launcher - Information', 
                                   "Category genre '{}' not changed".format(self.categories[categoryID]["genre"]))
                    return
            # Edition of the plot (description)
            elif type2 == 2:
                keyboard = xbmc.Keyboard(self.categories[categoryID]["description"], 'Edit Description')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    self.categories[categoryID]["description"] = keyboard.getText()
                else:
                    kodi_dialog_OK('Advanced Emulator Launcher - Information', 
                                   "Category description '{}' not changed".format(self.categories[categoryID]["description"]))
                    return
            # Import category description
            elif type2 == 3:
                text_file = xbmcgui.Dialog().browse(1, 'Select description file (TXT|DAT)', "files", ".txt|.dat", False, False)
                if os.path.isfile(text_file):
                    file_data = self._gui_import_TXT_file(text_file)
                    if file_data != '':
                        self.categories[categoryID]["description"] = file_data
                    else:
                        return
                else:
                    desc_str = text_limit_string(self.categories[categoryID]['description'], DESCRIPTION_MAXSIZE)
                    kodi_dialog_OK('Advanced Emulator Launcher - Information', 
                                "Category description '{}' not changed".format(desc_str))
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
        xbmc.executebuiltin('Container.Refresh')

    def _command_add_new_category(self):
        dialog = xbmcgui.Dialog()
        keyboard = xbmc.Keyboard("", 'New Category Name')
        keyboard.doModal()
        if not keyboard.isConfirmed():
            return False

        category = fs_new_category()
        categoryID = misc_generate_random_SID()
        category["id"]   = categoryID, 
        category["name"] = keyboard.getText()
        self.categories[categoryID] = category
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
        kodi_notify('Advanced Emulator Launcher', 'Category {0} created'.format(category["name"]))
        xbmc.executebuiltin('Container.Refresh')

    #
    # Removes ROMs for a given launcher. Note this function will never be called for standalone launchers.
    #
    def _gui_empty_launcher(self, launcherID):
        roms = fs_load_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'])
        num_roms = len(roms)
        
        # If launcher is empty (no ROMs) do nothing
        if num_roms == 0:
            kodi_dialog_OK('Advanced Emulator Launcher', 
                           'Launcher is empty. Nothing to do.')
            return

        # Confirm user wants to delete ROMs
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno('Advanced Emulator Launcher', 
                           "Launcher '{}' has {} ROMs".format(self.launchers[launcherID]["name"], num_roms),
                           'Are you sure you want to delete it?')
        if ret:
            # Just remove XML file. Keep the value of roms_xml_file to be reused when user add more ROMs.
            # Note that if the file is not found fs_load_ROM_XML_file() will return an empty dictionary.
            roms_xml_file = self.launchers[launcherID]["roms_xml_file"]
            if roms_xml_file == '':
                log_debug('Launcher roms_xml_file = "". No ROMs XML to remove')
            else:
                log_debug('Removing ROMs XML "{0}"'.format(roms_xml_file))
                try:
                    os.remove(roms_xml_file)
                except OSError:
                    log_error('_gui_empty_launcher() OSError exception deleting "{0}"'.format(roms_xml_file))
                    kodi_notify_warn('Advanced Emulator Launcher', 'OSError exception deleting ROMs XML')
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            xbmc.executebuiltin('Container.Refresh')

    #
    # Removes a launcher. For ROMs launcher it also removes ROM XML. For standalone launcher there is no
    # files to remove and no ROMs to check.
    #
    def _gui_remove_launcher(self, launcherID):
        rompath = self.launchers[launcherID]["rompath"]
        # Standalone launcher
        if rompath == '':
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher', 
                               'Launcher "{0}" is standalone.'.format(self.launchers[launcherID]["name"]),
                               'Are you sure you want to delete it?')
        # ROMs launcher
        else:
            roms = fs_load_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'])
            num_roms = len(roms)
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher', 
                               'Launcher "{0}" has {1} ROMs'.format(self.launchers[launcherID]["name"], num_roms),
                               'Are you sure you want to delete it?')
        if ret:
            # Remove XML file and delete launcher object, only if launcher is not empty
            roms_xml_file = self.launchers[launcherID]["roms_xml_file"]
            if roms_xml_file == '' or rompath == '':
                log_debug('Launcher is empty or standalone. No ROMs XML to remove')
            else:
                log_debug('Removing ROMs XML "{0}"'.format(roms_xml_file))
                try:
                    os.remove(roms_xml_file)
                except OSError:
                    log_error('_gui_remove_launcher() OSError exception deleting "{0}"'.format(roms_xml_file))
                    kodi_notify_warn('Advanced Emulator Launcher', 'OSError exception deleting ROMs XML')
            categoryID = self.launchers[launcherID]["categoryID"]
            self.launchers.pop(launcherID)
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            if self._cat_is_empty(categoryID):
                log_error('_gui_remove_launcher() Launcher category empty. Replacing Window')
                xbmc.executebuiltin('ReplaceWindow(Programs,%s)'.format(self.base_url))
            else:
                log_error('_gui_remove_launcher() Launcher category not empty. Container.Refresh()')
                xbmc.executebuiltin('Container.Refresh')

    def _command_edit_launcher(self, launcherID):
        dialog = xbmcgui.Dialog()
        title = os.path.basename(self.launchers[launcherID]["name"])
        finished_display = 'Status : Finished' if self.launchers[launcherID]["finished"] == True else 'Status : Unfinished'
        category_name = self.categories[self.launchers[launcherID]["categoryID"]]['name']
        if self.launchers[launcherID]["rompath"] == "":
            type = dialog.select('Select Action for launcher %s' % title, 
                                 ['Modify Metadata...', 'Change Thumbnail Image...', 'Change Fanart Image...', 
                                  'Change Category: {}'.format(category_name),
                                  finished_display, 'Advanced Modifications..', 'Delete'])
        else:
            type = dialog.select('Select Action for launcher %s' % title, 
                                 ['Modify Metadata...', 'Change Thumbnail Image...', 'Change Fanart Image...',
                                  'Change Category: {}'.format(category_name),
                                  finished_display, 'Manage ROM List...', 'Advanced Modifications...', 'Delete'])

        # --- Edition of the launcher metadata ---
        type_nb = 0
        if type == type_nb:
            dialog = xbmcgui.Dialog()
            desc_str = text_limit_string(self.launchers[launcherID]["plot"], DESCRIPTION_MAXSIZE)
            type2 = dialog.select('Modify Launcher Metadata',
                                  ['Scrape from {}'.format(self.scraper_metadata.fancy_name),
                                   'Import metadata from NFO file...',
                                   "Edit Title: '{}'".format(self.launchers[launcherID]["name"]),
                                   "Edit Platform: {}".format(self.launchers[launcherID]["platform"]),
                                   "Edit Release Year: '{}'".format(self.launchers[launcherID]["year"]),
                                   "Edit Studio: '{}'".format(self.launchers[launcherID]["studio"]),
                                   "Edit Genre: '{}'".format(self.launchers[launcherID]["genre"]),
                                   "Edit Description: '{}'".format(desc_str),
                                   'Import Description from file...',
                                   'Save metadata to NFO file'])
            # Scrape launcher metadata
            if type2 == 0:
                self._gui_scrap_launcher_metadata(launcherID)
            # Import launcher metadata from NFO file
            elif type2 == 1:
                info_str = fs_import_launcher_nfo(self.settings, self.launchers, launcherID)
                kodi_notify('Advanced Emulator Launcher', info_str)
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            # Edition of the launcher name
            elif type2 == 2:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["name"], 'Edit title')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    title = keyboard.getText()
                    if title == "" :
                        title = self.launchers[launcherID]["name"]
                    self.launchers[launcherID]["name"] = title.rstrip()
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            # Selection of the launcher game system
            elif type2 == 3:
                dialog = xbmcgui.Dialog()
                platforms = emudata_platform_list()
                sel_platform = dialog.select('Select the platform', platforms)
                if not sel_platform == -1:
                    self.launchers[launcherID]["platform"] = platforms[sel_platform]
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            # Edition of the launcher release date (year)
            elif type2 == 4:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["year"], 'Edit release year')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    self.launchers[launcherID]["year"] = keyboard.getText()
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            # Edition of the launcher studio name
            elif type2 == 5:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["studio"], 'Edit studio')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    self.launchers[launcherID]["studio"] = keyboard.getText()
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            # Edition of the launcher genre
            elif type2 == 6:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["genre"], 'Edit genre')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    self.launchers[launcherID]["genre"] = keyboard.getText()
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

            # Edit launcher description (plot)
            elif type2 == 7:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["plot"], 'Edit descripion')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    self.launchers[launcherID]["plot"] = keyboard.getText()
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

            # Import of the launcher descripion (plot)
            elif type2 == 8:
                text_file = xbmcgui.Dialog().browse(1, 'Select description file (TXT|DAT)', "files", ".txt|.dat", False, False)
                if os.path.isfile(text_file) == True:
                    file_data = self._gui_import_TXT_file(text_file)
                    if file_data != '':
                        self.launchers[launcherID]["plot"] = file_data
                        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
                else:
                    desc_str = text_limit_string(self.launchers[launcherID]["plot"], DESCRIPTION_MAXSIZE)
                    kodi_dialog_OK('Advanced Emulator Launcher - Information', 
                                   "Launcher plot '{}' not changed".format(desc_str))
            # Export launcher metadata to NFO file
            elif type2 == 9:
                info_str = fs_export_launcher_nfo(self.settings, self.launchers[launcherID])
                kodi_notify('Advanced Emulator Launcher', info_str)

        # Launcher Thumbnail menu option
        type_nb = type_nb + 1
        if type == type_nb:            
            self._gui_edit_image(IMAGE_THUMB, KIND_LAUNCHER, self.launchers, launcherID)

        # Launcher Fanart menu option
        type_nb = type_nb + 1
        if type == type_nb:
            self._gui_edit_image(IMAGE_FANART, KIND_LAUNCHER, self.launchers, launcherID)

        # Change launcher's category
        type_nb = type_nb + 1
        if type == type_nb:
            current_category = self.launchers[launcherID]['category']
            dialog = xbmcgui.Dialog()
            categories_id = []
            categories_name = []
            for key in self.categories:
                categories_id.append(self.categories[key]['id'])
                categories_name.append(self.categories[key]['name'])
            selected_cat = dialog.select('Select the category', categories_name)
            if not selected_cat == -1:
                self.launchers[launcherID]["category"] = categories_id[selected_cat]
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
                xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self.base_url, categories_id[selected_cat]))

        # --- Launcher status (finished [bool]) ---
        type_nb = type_nb + 1
        if type == type_nb:
            finished = self.launchers[launcherID]['finished']
            finished = False if finished else True
            finished_display = 'Finished' if finished == True else 'Unfinished'
            self.launchers[launcherID]['finished'] = finished
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
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
                    add_delete_NoIntro_str = 'Delete No-Intro DAT: {}'.format(nointro_xml_file)
                else:
                    add_delete_NoIntro_str = 'Add No-Intro XML DAT'
                type2 = dialog.select('Manage Items List', 
                                      [add_delete_NoIntro_str, 'Audit ROMs using No-Intro DAT'
                                       'Import ROMs metadata from NFO files',
                                       'Export ROMs metadata to NFO files', 
                                       'Clear ROMs from launcher' ])

                # --- Add/Delete No-Intro XML parent-clone DAT ---
                if type2 == 0:
                    if has_NoIntro_DAT:
                        dialog = xbmcgui.Dialog()
                        ret = dialog.yesno('Advanced Emulator Launcher', 'Delete No-Intro DAT file?')
                        if ret:
                            self.launchers[launcherID]["nointro_xml_file"] = ''
                            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
                            kodi_dialog_OK('Advanced Emulator Launcher', 'Rescan your ROMs to remove No-Intro tags.')
                    else:
                        # Browse for No-Intro file
                        # BUG For some reason *.dat files are not shown on the dialog, but XML files are OK!!!
                        dat_file = xbmcgui.Dialog().browse(1, 'Select No-Intro XML DAT (XML|DAT)', 'files', '.dat|.xml')
                        if os.path.isfile(dat_file) == True:
                            self.launchers[launcherID]["nointro_xml_file"] = dat_file
                            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
                            kodi_dialog_OK('Advanced Emulator Launcher', 'DAT file successfully added. Rescan your ROMs to audit them.')

                # --- Audit ROMs with No-Intro DAT ---
                # >> This code is similar to the one in the ROM scanner _roms_import_roms()
                elif type2 == 1:
                    # Check if No-Intro XML DAT exists
                    if not has_NoIntro_DAT:
                        kodi_dialog_OK('Advanced Emulator Launcher', 'No-Intro XML DAT not configured. Add one before ROM audit.')
                        return

                    # --- Load ROMs for this launcher ---
                    roms_xml_file = self.launchers[launcherID]['roms_xml_file']
                    roms = fs_load_ROM_XML_file(roms_xml_file)
                    
                    # --- Load No-Intro DAT and audit ROMs ---
                    log_info('Auditing ROMs using No-Intro DAT {}'.format(nointro_xml_file))

                    # --- Update No-Intro status for ROMs ---
                    # Note that roms dictionary is updated using Python pass by assigment.
                    # See http://stackoverflow.com/questions/986006/how-do-i-pass-a-variable-by-reference
                    (num_have, num_miss, num_unknown) = self._roms_update_NoIntro_status(roms, nointro_xml_file)

                    # Report
                    log_info('***** No-Intro audit finished. Report ******')
                    log_info('No-Intro Have ROMs    {:6d}'.format(num_have))
                    log_info('No-Intro Miss ROMs    {:6d}'.format(num_miss))
                    log_info('No-Intro Unknown ROMs {:6d}'.format(num_unknown))

                    # ~~~ Save ROMs XML file ~~~
                    fs_write_ROM_XML_file(roms_xml_file, roms, self.launchers[launcherID])

                # --- Import Items list form NFO files ---
                elif type2 == 2:
                    # >> Load ROMs, iterate and import NFO files
                    roms_xml_file = self.launchers[launcherID]['roms_xml_file']
                    roms = fs_load_ROM_XML_file(roms_xml_file)
                    for rom in roms:
                        fs_import_rom_nfo(launcherID, rom)
                    # >> Save ROMs XML file
                    fs_write_ROM_XML_file(roms_xml_file, roms, self.launchers[launcherID])

                # --- Export Items list to NFO files ---
                elif type2 == 3:
                    # >> Load ROMs, iterate and write NFO files
                    roms = fs_load_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'])
                    for rom in roms:
                        fs_export_rom_nfo(launcherID, rom)

                # --- Empty Launcher menu option ---
                elif type2 == 4:
                    self._gui_empty_launcher(launcherID)
                    # _gui_empty_launcher calls ReplaceWindow/Container.Refresh. Return now to avoid the
                    # Container.Refresh at the end of this function and calling the plugin twice.
                    return

        # --- Launcher Advanced modifications menu option ---
        type_nb = type_nb + 1
        if type == type_nb:
            lnk_str = 'ON' if self.launchers[launcherID]["lnk"] == True else 'OFF'
            minimize_str = 'ON' if self.launchers[launcherID]["minimize"] == True else 'OFF'
            filter_str = ".bat|.exe|.cmd" if sys.platform == "win32" else ''

            # --- ROMS launcher -------------------------------------------------------------------
            if self.launchers[launcherID]["rompath"] != "" and sys.platform == 'win32':
                type2 = dialog.select('Advanced Modifications', 
                                      ['Change Application: %s' % self.launchers[launcherID]["application"],
                                       'Modify Arguments: %s' % self.launchers[launcherID]["args"],
                                       'Change Items Path: %s' % self.launchers[launcherID]["rompath"],
                                       'Modify Items Extensions: %s' % self.launchers[launcherID]["romext"],
                                       'Change Thumbs Path: %s' % self.launchers[launcherID]["thumbpath"],
                                       'Change Fanarts Path: %s' % self.launchers[launcherID]["fanartpath"],
                                       'Change Trailer file: %s' % self.launchers[launcherID]["trailerpath"],
                                       'Change Extra-fanarts Path: %s' % self.launchers[launcherID]["custompath"],
                                       'Toggle Kodi into Windowed mode: %s' % minimize_str,
                                       'Shortcuts (.lnk) support: %s' % lnk_str])
            elif self.launchers[launcherID]["rompath"] != "" and not sys.platform == 'win32':
                type2 = dialog.select('Advanced Modifications', 
                                      ['Change Application: %s' % self.launchers[launcherID]["application"],
                                       'Modify Arguments: %s' % self.launchers[launcherID]["args"],
                                       'Change Items Path: %s' % self.launchers[launcherID]["rompath"],
                                       'Modify Items Extensions: %s' % self.launchers[launcherID]["romext"],
                                       'Change Thumbs Path: %s' % self.launchers[launcherID]["thumbpath"],
                                       'Change Fanarts Path: %s' % self.launchers[launcherID]["fanartpath"],
                                       'Change Trailer file: %s' % self.launchers[launcherID]["trailerpath"],
                                       'Change Extra-fanarts Path: %s' % self.launchers[launcherID]["custompath"],
                                       'Toggle Kodi into Windowed mode: %s' % minimize_str])

            # --- Standalone launcher -------------------------------------------------------------
            elif self.launchers[launcherID]["rompath"] == "" and sys.platform == 'win32':
                type2 = dialog.select('Advanced Modifications', 
                                      ['Change Application: %s' % self.launchers[launcherID]["application"],
                                       'Modify Arguments: %s' % self.launchers[launcherID]["args"],
                                       'Change Thumbs Path: %s' % self.launchers[launcherID]["thumbpath"],
                                       'Change Fanarts Path: %s' % self.launchers[launcherID]["fanartpath"],
                                       'Change Trailer file: %s' % self.launchers[launcherID]["trailerpath"],
                                       'Change Extra-fanarts Path: %s' % self.launchers[launcherID]["custompath"],
                                       'Toggle Kodi into Windowed mode: %s' % minimize_str,
                                       'Shortcuts (.lnk) support: %s' % lnk_str])
            else:
                type2 = dialog.select('Advanced Modifications', 
                                      ['Change Application: %s' % self.launchers[launcherID]["application"],
                                       'Modify Arguments: %s' % self.launchers[launcherID]["args"],
                                       'Change Thumbs Path: %s' % self.launchers[launcherID]["thumbpath"],
                                       'Change Fanarts Path: %s' % self.launchers[launcherID]["fanartpath"],
                                       'Change Trailer file: %s' % self.launchers[launcherID]["trailerpath"],
                                       'Change Extra-fanarts Path: %s' % self.launchers[launcherID]["custompath"],
                                       'Toggle Kodi into Windowed mode: %s' % minimize_str])

            # Launcher application path menu option
            type2_nb = 0
            if type2 == type2_nb:
                app = xbmcgui.Dialog().browse(1, 'Select the launcher application',
                                              "files","", False, False, self.launchers[launcherID]["application"])
                self.launchers[launcherID]["application"] = app
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

            # Edition of the launcher arguments
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["args"], 'Edit application arguments')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    self.launchers[launcherID]["args"] = keyboard.getText()
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

            if self.launchers[launcherID]["rompath"] != "":
                # Launcher roms path menu option
                type2_nb = type2_nb + 1
                if type2 == type2_nb:
                    rom_path = xbmcgui.Dialog().browse(0, 'Select Files path', "files", "", 
                                                       False, False, self.launchers[launcherID]["rompath"])
                    self.launchers[launcherID]["rompath"] = rom_path
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

                # Edition of the launcher rom extensions (only for emulator launcher)
                type2_nb = type2_nb +1
                if type2 == type2_nb:
                    if not self.launchers[launcherID]["rompath"] == "":
                        keyboard = xbmc.Keyboard(self.launchers[launcherID]["romext"], 
                                                 'Edit files extensions, use &quot;|&quot; as separator. (e.g lnk|cbr)')
                        keyboard.doModal()
                        if keyboard.isConfirmed():
                            self.launchers[launcherID]["romext"] = keyboard.getText()
                            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

            # Launcher thumbnails path menu option
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                thumb_path = xbmcgui.Dialog().browse(0, 'Select Thumbnails path', "files", "", 
                                                     False, False, self.launchers[launcherID]["thumbpath"])
                self.launchers[launcherID]["thumbpath"] = thumb_path
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

            # Launcher fanarts path menu option
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                fanart_path = xbmcgui.Dialog().browse(0, 'Select Fanarts path', "files", "", 
                                                      False, False, self.launchers[launcherID]["fanartpath"])
                self.launchers[launcherID]["fanartpath"] = fanart_path
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

            # Launcher trailer file menu option
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                fanart_path = xbmcgui.Dialog().browse(1, 'Select Trailer file', "files", 
                                                      ".mp4|.mpg|.avi|.wmv|.mkv|.flv", False, False, 
                                                      self.launchers[launcherID]["trailerpath"])
                self.launchers[launcherID]["trailerpath"] = fanart_path
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

            # Launcher custom path menu option
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                fanart_path = xbmcgui.Dialog().browse(0, 'Select Extra-fanarts path', "files", "", False, False, 
                                                      self.launchers[launcherID]["custompath"])
                self.launchers[launcherID]["custompath"] = fanart_path
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

            # Launcher minimize state menu option
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                dialog = xbmcgui.Dialog()
                type3 = dialog.select('Toggle Kodi Fullscreen', ["%s (%s)" % ('OFF', 'default'), "%s" % ('ON')])
                self.launchers[launcherID]["minimize"] = True if type3 == 1 else False
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

            # Launcher internal lnk option
            if sys.platform == 'win32':
                type2_nb = type2_nb + 1
                if type2 == type2_nb:
                    dialog = xbmcgui.Dialog()
                    type3 = dialog.select('Shortcuts (.lnk) support', 
                                          ["%s (%s)" % ('ON','default'), 
                                           "%s (%s)" % ('OFF','experienced users')])
                    self.launchers[launcherID]["lnk"] = False if type3 == 1 else True
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

        # Remove Launcher menu option
        type_nb = type_nb + 1
        if type == type_nb:
            self._gui_remove_launcher(launcherID)
            # _gui_remove_launcher calls ReplaceWindow/Container.Refresh. Return now to avoid the
            # Container.Refresh at the end of this function and calling the plugin twice.
            return

        if type == -1:
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

        # Return to the launcher directory
        xbmc.executebuiltin('Container.Refresh')

    def _command_add_new_launcher(self, categoryID):
        # If categoryID not found return to plugin root window.
        if categoryID not in self.categories:
            kodi_notify('Advanced Emulator Launcher - Error', 'Target category not found.')
            xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self.base_url))
            return
        
        # Show "Create New Launcher" dialog
        dialog = xbmcgui.Dialog()
        type = dialog.select('Create New Launcher', 
                             ['Standalone launcher (normal executable)', 'Files launcher (game emulator)'])
        log_info('_command_add_new_launcher() New launcher type = {}'.format(type))
        if sys.platform == 'win32': filter = '.bat|.exe|.cmd|.lnk'
        else:                       filter = ''

        # 'Standalone launcher (normal executable)'
        if type == 0:
            app = xbmcgui.Dialog().browse(1, 'Select the launcher application', "files", filter)
            if not app: return False

            argument = ''
            argkeyboard = xbmc.Keyboard(argument, 'Application arguments')
            argkeyboard.doModal()
            args = argkeyboard.getText()

            title = os.path.basename(app)
            keyboard = xbmc.Keyboard(title.replace('.'+title.split('.')[-1],'').replace('.',' '), 'Set the title of the launcher')
            keyboard.doModal()
            title = keyboard.getText()
            if title == "" :
                title = os.path.basename(app)
                title = title.replace('.' + title.split('.')[-1], '').replace('.', ' ')

            # Selection of the launcher game system
            dialog = xbmcgui.Dialog()
            platforms = emudata_platform_list()
            sel_platform = dialog.select('Select the platform', platforms)

            # Selection of the thumbnails and fanarts path
            if self.settings['launcher_thumb_path'] == '':
                thumb_path = xbmcgui.Dialog().browse(0, 'Select Thumbnails path', "files", "", False, False)
            else:
                thumb_path = self.settings['launcher_thumb_path']
            if self.settings['launcher_fanart_path'] == '':
                fanart_path = xbmcgui.Dialog().browse(0, 'Select Fanarts path', "files", "", False, False)
            else:
                fanart_path = self.settings['launcher_fanart_path']

            # --- Create launcher object data, add to dictionary and write XML file ---
            if not thumb_path:  thumb_path = ''
            if not fanart_path: fanart_path = ''
            if not sel_platform == -1:  launcher_platform = platforms[sel_platform]
            else:                       launcher_platform = "Unknown"
            if sys.platform == "win32": launcher_lnk = True
            else:                       launcher_lnk = False
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
            launcherdata['lnk']         = launcher_lnk
            self.launchers[launcherID]  = launcherdata
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self.base_url, categoryID))

        # 'Files launcher (game emulator)'
        elif type == 1:
            app = xbmcgui.Dialog().browse(1, 'Select the launcher application', "files", filter)
            if not app: return False
            
            files_path = xbmcgui.Dialog().browse(0, 'Select the ROMs path', "files", "")
            if not files_path: return False

            extensions = emudata_get_program_extensions(os.path.basename(app))
            extkey = xbmc.Keyboard(extensions, 'Set files extensions, use "|" as separator. (e.g lnk|cbr)')
            extkey.doModal()
            if not extkey.isConfirmed(): return False
            ext = extkey.getText()

            default_arguments = emudata_get_program_arguments(os.path.basename(app))
            argkeyboard = xbmc.Keyboard(default_arguments, 'Application arguments')
            argkeyboard.doModal()
            if not argkeyboard.isConfirmed(): return False
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
            platforms = emudata_platform_list()
            sel_platform = dialog.select('Select the platform', platforms)

            # Selection of the thumbnails and fanarts path
            thumb_path = xbmcgui.Dialog().browse(0, 'Select Thumbnail path', "files", "", False, False, files_path)
            fanart_path = xbmcgui.Dialog().browse(0, 'Select Fanart path', "files", "", False, False, files_path)

            # --- Create launcher object data, add to dictionary and write XML file ---
            thumb_path  = "" if not thumb_path else thumb_path
            fanart_path = "" if not fanart_path else fanart_path
            if not sel_platform == -1:  launcher_platform = platforms[sel_platform]
            else:                       launcher_platform = "Unknown"
            launcher_lnk = True if sys.platform == "win32" else False
            
            # Choose launcher ROM XML filename. There may be launchers with
            # same name in different categories, or even launcher with the
            # same name in the same category.
            launcherID = misc_generate_random_SID()
            category_name = self.categories[categoryID]['name']
            clean_cat_name = ''.join([i if i in string.printable else '_' for i in category_name])
            clean_launch_title = ''.join([i if i in string.printable else '_' for i in title])
            clean_launch_title = clean_launch_title.replace(' ', '_')
            roms_xml_file_base = 'roms_' + clean_cat_name + '_' + clean_launch_title + '_' + launcherID[0:5] + '.xml'
            roms_xml_file_path = os.path.join(PLUGIN_DATA_DIR, roms_xml_file_base)
            log_info('Chosen roms_xml_file_base  "{0}"'.format(roms_xml_file_base))
            log_info('Chosen roms_xml_file_path  "{0}"'.format(roms_xml_file_path))

            # Create new launchers and save cateogories.xml
            launcherdata = fs_new_launcher()
            launcherdata['id']            = launcherID
            launcherdata['name']          = title
            launcherdata['categoryID']    = categoryID
            launcherdata['application']   = app
            launcherdata['args']          = args
            launcherdata['rompath']       = files_path
            launcherdata['thumbpath']     = thumb_path
            launcherdata['fanartpath']    = fanart_path
            launcherdata['romext']        = ext
            launcherdata['platform']      = launcher_platform
            launcherdata['lnk']           = launcher_lnk
            launcherdata['roms_xml_file'] = roms_xml_file_path
            self.launchers[launcherID] = launcherdata
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            kodi_notify('Advanced Emulator Launcher', 
                        'ROM launcher {} created.'.format(title))

            # This causes trouble...
            # xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self.base_url, categoryID))
            # Just update container contents
            xbmc.executebuiltin('Container.Refresh')

    #
    # These two functions do things like stopping music before lunch, toggling full screen, etc.
    #
    def _run_before_execution(self, launcher, name_str):
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
        if launcher["minimize"] == "true":
            _toogle_fullscreen()

        if self.settings['launcher_notification']:
            kodi_notify('Advanced Emulator Launcher', 'Launching {0}'.format(name_str), 5000)

        try:
            xbmc.enableNavSounds(False)                                 
        except:
            pass
        xbmc.sleep(self.settings['start_tempo'])

    def _run_after_execution(self, launcher):
        xbmc.sleep(self.settings[ "start_tempo" ])
        try:
            xbmc.enableNavSounds(True)                            
        except:
            pass

        if launcher["minimize"] == "true":
            _toogle_fullscreen()

        if self.settings['media_state'] != "2":
            try:
                xbmc.audioResume()
            except:
                pass
            if self.settings['media_state'] == "1":
                xbmc.sleep(self.settings['start_tempo'] + 100)
                xbmc.Player().play()

    #
    # Launchs an application
    #
    def _run_standalone_launcher(self, categoryID, launcherID):
        # Check launcher is OK
        if launcherID not in self.launchers:
            kodi_dialog_OK('ERROR', 'launcherID not found in launcherID')
            return
        launcher = self.launchers[launcherID]

        # Kodi built-in???
        # xbmc-fav- and xbmc-sea are Angelscry's hacks to implement launchers from favourites
        # and launchers from searchers. For example, to run a launcher created from search
        # results,
        # app = "xbmc-sea-%s" % launcherid
        # args = 'ActivateWindow(10001,"%s")' % launcher_query
        apppath = os.path.dirname(launcher["application"])
        if os.path.basename(launcher["application"]).lower().replace(".exe" , "") == "xbmc"  or \
           "xbmc-fav-" in launcher["application"] or "xbmc-sea-" in launcher["application"]:
            xbmc.executebuiltin('XBMC.%s' % launcher["args"])
            return

        # ~~~~~ External application ~~~~~
        application = launcher["application"]
        application_basename = os.path.basename(launcher["application"])
        if not os.path.exists(apppath):
            kodi_notify_warn('Advanced Emulator Launcher', 
                             'File {0} not found.'.format(application_basename))
            return
        arguments = launcher["args"].replace("%apppath%" , apppath).replace("%APPPATH%" , apppath)
        self._print_log('_run_standalone_launcher() apppath              = "{0}"'.format(apppath))
        self._print_log('_run_standalone_launcher() application          = "{0}"'.format(application))
        self._print_log('_run_standalone_launcher() application_basename = "{0}"'.format(application_basename))
        self._print_log('_run_standalone_launcher() arguments            = "{0}"'.format(arguments))
        
        # Do stuff before execution
        self._run_before_execution(launcher, application_basename)

        # Execute
        if sys.platform == 'win32':
            if launcher["application"].split(".")[-1] == "lnk":
                os.system("start \"\" \"%s\"" % (application))
            else:
                if application.split(".")[-1] == "bat":
                    info = subprocess_hack.STARTUPINFO()
                    info.dwFlags = 1
                    if ( self.settings[ "show_batch" ] ):
                        info.wShowWindow = 5
                    else:
                        info.wShowWindow = 0
                else:
                    info = None
                startproc = subprocess_hack.Popen(r'%s %s' % (application, arguments), cwd=apppath, startupinfo=info)
                startproc.wait()
        elif sys.platform.startswith('linux'):
            if self.settings[ "lirc_state" ]: xbmc.executebuiltin('LIRC.stop')
            os.system("\"%s\" %s " % (application, arguments))
            if self.settings[ "lirc_state" ]: xbmc.executebuiltin('LIRC.start')
        elif sys.platform.startswith('darwin'):
            os.system("\"%s\" %s " % (application, arguments))
        else:
            kodi_notify_warn('Advanced Emulator Launcher', 'Cannot determine the running platform')

        # Do stuff after execution
        self._run_after_execution(launcher)

    #
    # Launchs a ROM
    #
    def _run_rom(self, categoryID, launcherID, romID):
        # Check launcher is OK
        if launcherID not in self.launchers:
            kodi_dialog_OK('ERROR', 'launcherID not found in launcherID')
            return
        launcher = self.launchers[launcherID]
        
        # Load ROMs
        roms = fs_load_ROM_XML_file(launcher['roms_xml_file'])

        # Check ROM is XML data just read
        if romID not in roms:
            kodi_dialog_OK('ERROR', 'romID not in roms_dic')
            return
            
        # Launch ROM
        rom = roms[romID]
        if rom["altapp"] != "": application = rom["altapp"]
        else:                   application = launcher["application"]
        apppath = os.path.dirname(application)
        romfile = os.path.basename(rom["filename"])
        rompath = os.path.dirname(rom["filename"])
        romname = os.path.splitext(romfile)[0]
        self._print_log('_run_rom() application = "{0}"'.format(application))
        self._print_log('_run_rom() apppath     = "{0}"'.format(apppath))
        self._print_log('_run_rom() romfile     = "{0}"'.format(romfile))
        self._print_log('_run_rom() rompath     = "{0}"'.format(rompath))
        self._print_log('_run_rom() romname     = "{0}"'.format(romname))

        # Check that app exists and ROM file exists
        if not os.path.exists(apppath):
            kodi_notify_warn("Advanced Emulator Launcher", 'File %s not found.' % apppath, 10000)
            return
        if os.path.exists(romfile):
            kodi_notify_warn("Advanced Emulator Launcher", 'File %s not found.' % romfile, 10000)
            return

        # ~~~~ Argument substitution ~~~~~
        if rom["altarg"] != "": arguments = rom["altarg"]
        else:                   arguments = launcher["args"]
        arguments = arguments.replace("%rom%", rom["filename"]).replace("%ROM%", rom["filename"])
        arguments = arguments.replace("%romfile%", romfile).replace("%ROMFILE%", romfile)
        arguments = arguments.replace("%romname%", romname).replace("%ROMNAME%", romname)
        arguments = arguments.replace("%rombasename%", base_filename(romname)).replace("%ROMBASENAME%", base_filename(romname))
        arguments = arguments.replace("%apppath%", apppath).replace("%APPPATH%", apppath)
        arguments = arguments.replace("%rompath%", rompath).replace("%ROMPATH%", rompath)
        arguments = arguments.replace("%romtitle%", rom["name"]).replace("%ROMTITLE%", rom["name"])
        arguments = arguments.replace("%romspath%", rompath).replace("%ROMSPATH%", rompath)
        self._print_log('_run_rom() arguments   = "{0}"'.format(arguments))

        # Execute Kodi internal function (RetroPlayer?)
        if os.path.basename(application).lower().replace(".exe" , "") == "xbmc":
            xbmc.executebuiltin('XBMC.' + arguments)
            return

        # ~~~~~ Execute external application ~~~~~
        # Do stuff before execution
        self._run_before_execution(launcher, romname)

        # Determine platform and launch application
        if sys.platform == 'win32':
            if launcher["lnk"] == "true" and launcher["romext"] == "lnk":
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
            if self.settings["lirc_state"]: xbmc.executebuiltin('LIRC.stop')
            os.system("\"%s\" %s " % (application, arguments))
            if self.settings["lirc_state"]: xbmc.executebuiltin('LIRC.start')
        # Android???
        elif sys.platform.startswith('darwin'):
            os.system("\"%s\" %s " % (application, arguments))
        else:
            kodi_notify_warn('Advanced Emulator Launcher', 'Cannot determine the running platform', 10000)

        # Do stuff after application execution
        self._run_after_execution(launcher)

    def _gui_render_category_row(self, category_dic, key):
        # --- Create listitem row ---
        icon = "DefaultFolder.png"        
        if category_dic['thumb'] != '':
            listitem = xbmcgui.ListItem(category_dic['name'], iconImage=icon, thumbnailImage=category_dic['thumb'] )
        else:
            listitem = xbmcgui.ListItem(category_dic['name'], iconImage=icon )
        if category_dic['finished'] == False: ICON_OVERLAY = 6
        else:                                 ICON_OVERLAY = 7
        listitem.setProperty("fanart_image", category_dic['fanart'])
        # log_debug('_gui_render_category_row() Category {} fanart "{}"'.format(category_dic['name'], category_dic['fanart']))
        listitem.setInfo("video", { "Title": category_dic['name'], "Genre" : category_dic['genre'], 
                                    "Plot" : category_dic['description'], "overlay": ICON_OVERLAY } )

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
        # if ( finished != "true" ) or ( self.settings[ "hide_finished" ] == False) :
        url_str = self._misc_url('SHOW_LAUNCHERS', key)
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url=url_str, listitem=listitem, isFolder=True)

    def _gui_render_category_favourites(self):
        # --- Create listitem row ---
        fav_name = '<Favourites>'
        fav_thumb = ''
        fav_fanart = ''
        icon = "DefaultFolder.png"        
        listitem = xbmcgui.ListItem(fav_name, iconImage=icon, thumbnailImage=fav_thumb)
        listitem.setProperty("fanart_image", fav_fanart)
        listitem.setInfo("video", { "Title": fav_name, "Genre" : 'All', 
                                    "Plot" : 'AEL favourite ROMs', "overlay": 7 } )
        
        # --- Create context menu ---
        commands = []
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY'), ))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', ))
        commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        listitem.addContextMenuItems(commands, replaceItems=True)

        # --- Add row ---
        url_str = self._misc_url('SHOW_FAVOURITES')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url=url_str, listitem=listitem, isFolder=True)

    # 
    # Former _get_categories()
    # Renders the categories (addon root window)
    #
    def _gui_render_categories(self):
        # For every category, add it to the listbox. Order alphabetically by name
        for key in sorted(self.categories, key= lambda x : self.categories[x]["name"]):
            self._gui_render_category_row(self.categories[key], key)
        # AEL Favourites special category
        self._gui_render_category_favourites()
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded=True, cacheToDisc=False )

    def _gui_render_launcher_row(self, launcher_dic):
        # --- Create listitem row ---
        commands = []
        if launcher_dic['rompath'] == '': # Executable launcher
            folder = False
            icon = "DefaultProgram.png"
        else:                             # Files launcher
            folder = True
            icon = "DefaultFolder.png"
        if launcher_dic['thumb']:
            listitem = xbmcgui.ListItem( launcher_dic['name'], iconImage=icon, thumbnailImage=launcher_dic['thumb'] )
        else:
            listitem = xbmcgui.ListItem( launcher_dic['name'], iconImage=icon )
        if launcher_dic['finished'] != True: ICON_OVERLAY = 6
        else:                                ICON_OVERLAY = 7
        listitem.setProperty("fanart_image", launcher_dic['fanart'])
        listitem.setInfo("video", {"Title"    : launcher_dic['name'],    "Label"     : os.path.basename(launcher_dic['rompath']),
                                   "Plot"     : launcher_dic['plot'],    "Studio"    : launcher_dic['studio'],
                                   "Genre"    : launcher_dic['genre'],   "Premiered" : launcher_dic['year'],
                                   "Year"     : launcher_dic['year'],    "Writer"    : launcher_dic['platform'],
                                   "Trailer"  : os.path.join(launcher_dic['trailerpath']),
                                   "Director" : os.path.join(launcher_dic['custompath']), 
                                   "overlay"  : ICON_OVERLAY } )

        # --- Create context menu ---
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
    # Former  _get_launchers
    # Renders the launcher for a given category
    #
    def _gui_render_launchers(self, categoryID):
        # If the category has no launchers then render nothing.
        launcher_IDs = []
        for launcher_id in self.launchers:
            if self.launchers[launcher_id]["categoryID"] == categoryID: launcher_IDs.append(launcher_id)
        if not launcher_IDs:
            category_name = self.categories[categoryID]['name']
            kodi_notify('Advanced Emulator Launcher', 'Category {} has no launchers. Add launchers first'.format(category_name))
            # NOTE If we return at this point Kodi produces and error: 
            # ERROR: GetDirectory - Error getting plugin://plugin.program.advanced.emulator.launcher/?catID=8...f&com=SHOW_LAUNCHERS
            # ERROR: CGUIMediaWindow::GetDirectory(plugin://plugin.program.advanced.emulator.launcher/?catID=8...2f&com=SHOW_LAUNCHERS) failed
            # How to avoid that? Rendering the categories again? If I call _gui_render_categories() it does not work well, categories
            # are displayed in wrong alphabetical order and if go back is pressed the categories are rendered again (instead of 
            # exiting the addon).
            # What about replacewindow? I also get the error, still not clear why...
            # self._gui_render_categories()
            # xbmc.executebuiltin('ReplaceWindow(Programs,{0})'.format(self.base_url))            
            return

        # Render launcher rows of this category
        for key in sorted(self.launchers, key = lambda x : self.launchers[x]["application"]):
            if self.launchers[key]["categoryID"] == categoryID:
                self._gui_render_launcher_row(self.launchers[key])
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded=True, cacheToDisc=False )

    #
    # Former  _add_rom
    # Note that if we are rendering favourites, categoryID = launcherID = '0'.
    def _gui_render_rom_row( self, categoryID, launcherID, romID, rom, rom_is_in_favourites):
        # --- Create listitem row ---
        icon = "DefaultProgram.png"
        # icon = "DefaultVideo.png"

        # If we are rendering favourites mark fav_status
        if launcherID == '0':
            if rom['fav_status'] == 'OK':
                rom_name = '{} [COLOR green][OK][/COLOR]'.format(rom['name'])
            elif rom['fav_status'] == 'Unlinked':
                rom_name = '{} [COLOR yellow][Unlinked][/COLOR]'.format(rom['name'])
            elif rom['fav_status'] == 'Broken':
                rom_name = '{} [COLOR red][Broken][/COLOR]'.format(rom['name'])
            else:
                rom_name = rom['name']
        # We are rendering ROMs in a normal launcher
        else:
            # Mark No-Intro status
            if rom['nointro_status'] == 'Have':
                rom_name = '{} [COLOR green][Have][/COLOR]'.format(rom['name'])
            elif rom['nointro_status'] == 'Miss':
                rom_name = '{} [COLOR red][Miss][/COLOR]'.format(rom['name'])
            elif rom['nointro_status'] == 'Unknown':
                rom_name = '{} [COLOR yellow][Unknown][/COLOR]'.format(rom['name'])
            else:
                rom_name = rom['name']

            # If listing regular launcher and rom is in favourites, mark it
            if rom_is_in_favourites:
                log_debug('gui_render_rom_row() ROM is in favourites {}'.format(rom_name))

                # --- Workaround so the alphabetical order is not lost ---
                # NOTE Missing ROMs must never be in favourites... However, mark them to help catching bugs.
                # rom_name = '[COLOR violet]{} [Fav][/COLOR]'.format(rom['name'])
                # rom_name = '{} [COLOR violet][Fav][/COLOR]'.format(rom['name'])
                rom_name += ' [COLOR violet][Fav][/COLOR]'

        # --- Add ROM to lisitem ---
        if rom['thumb']: 
            listitem = xbmcgui.ListItem(rom['name'], rom['name'], iconImage=icon, thumbnailImage=rom['thumb'])
        else:            
            listitem = xbmcgui.ListItem(rom['name'], rom['name'], iconImage=icon)

        # If ROM has no fanart then use launcher fanart
        if launcherID == '0':
            defined_fanart = rom["fanart"]
        else:
            defined_fanart = rom["fanart"] if rom["fanart"] != '' else self.launchers[launcherID]["fanart"]
        if rom['finished'] is not True: ICON_OVERLAY = 6
        else:                           ICON_OVERLAY = 7
        listitem.setProperty("fanart_image", defined_fanart)
        
        # Interesting... if text formatting labels are set in xbmcgui.ListItem() do not work. However, if
        # labels are set as Title in setInfo(), then they work but the alphabetical order is lost!
        # I solved this alphabetical ordering issue by placing a coloured tag [Fav] at the and of the ROM name
        # instead of changing the whole row colour.
        if launcherID == '0':
            platform = rom['platform']
        else:
            platform = self.launchers[launcherID]['platform']
        listitem.setInfo("video", {"Title"   : rom_name,       "Label"     : 'test label', 
                                   "Plot"    : rom['plot'],    "Studio"    : rom['studio'], 
                                   "Genre"   : rom['genre'],   "Premiered" : rom['year'], 
                                   "Year"    : rom['year'],    "Writer"    : platform, 
                                   "Trailer" : 'test trailer', "Director"  : 'test director', 
                                   "overlay" : ICON_OVERLAY } )

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
        if launcherID == '0':
            commands.append(('Check Favourite ROMs', self._misc_url_RunPlugin('CHECK_FAV', '0', '0', romID), ))
            commands.append(('Edit ROM in Favourites', self._misc_url_RunPlugin('EDIT_ROM', '0', '0', romID), ))
            commands.append(('Search Favourites', self._misc_url_RunPlugin('SEARCH_LAUNCHER', '0', '0'), ))
            commands.append(('Delete ROM from Favourites', self._misc_url_RunPlugin('DELETE_ROM', '0', '0', romID), ))
        else:
            commands.append(('Edit ROM', self._misc_url_RunPlugin('EDIT_ROM', categoryID, launcherID, romID), ))
            commands.append(('Search ROMs in Launcher', self._misc_url_RunPlugin('SEARCH_LAUNCHER', categoryID, launcherID), ))
            commands.append(('Add ROM to AEL Favourites', self._misc_url_RunPlugin('ADD_TO_FAV', categoryID, launcherID, romID), )) 
            commands.append(('Delete ROM', self._misc_url_RunPlugin('DELETE_ROM', categoryID, launcherID, romID), ))
        # Add ROM URL to Kodi Favourites (do not know how to do it yet) (maybe not will be used)
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', )) # If using window ID then use "10003" 
        commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        listitem.addContextMenuItems(commands, replaceItems=True)

        # --- Add row ---
        # if finished != "true" or self.settings[ "hide_finished" ] == False:
        # URLs must be different depending on the content type. If not, lot of WARNING: CreateLoader - unsupported protocol(plugin)
        # in the log. See http://forum.kodi.tv/showthread.php?tid=187954
        # if self._content_type == 'video':
        #     url_str = self._misc_url('LAUNCH_ROM', categoryID, launcherID, romID)
        # else:
        url_str = self._misc_url('LAUNCH_ROM', categoryID, launcherID, romID)
        xbmcplugin.addDirectoryItem(handle=self.addon_handle, url=url_str, listitem=listitem, isFolder=False)

    #
    # Former  _get_roms
    # Renders the roms listbox for a given launcher
    #
    def _gui_render_roms(self, categoryID, launcherID):
        if launcherID not in self.launchers:
            log_error('_gui_render_roms() Launcher hash not found.')
            kodi_dialog_OK('Advanced Emulator Launcher - ERROR', 'Launcher hash not found.', '@_gui_render_roms()')
            return

        # Load ROMs for this launcher and display them
        selectedLauncher = self.launchers[launcherID]
        roms_xml_file = selectedLauncher['roms_xml_file']

        # Check if XML file with ROMs exist
        if not os.path.isfile(roms_xml_file):
            kodi_notify('Advanced Emulator Launcher', 'Launcher XML missing. Add items to launcher.')
            xbmc.executebuiltin("Container.Refresh")
            return

        # Load ROMs
        roms = fs_load_ROM_XML_file(roms_xml_file)
        if not roms:
            kodi_notify('Advanced Emulator Launcher', 'Launcher XML empty. Add items to launcher.')
            return

        # Load favourites
        roms_fav = fs_load_Favourites_XML_file(FAVOURITES_FILE_PATH)

        # --- Display ROMs ---
        # Optimization Currently roms_fav is a dictionary, which is very fast when testing for element existence
        #              because it is hashed. However, set() is the fastest. If user has a lot of favourites
        #              there could be a small performance gain.
        for key in sorted(roms, key= lambda x : roms[x]["filename"]):
            self._gui_render_rom_row(categoryID, launcherID, key, roms[key], key in roms_fav)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded=True, cacheToDisc=False)

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
    def _command_show_favourites(self):
        # Load favourites
        roms = fs_load_Favourites_XML_file(FAVOURITES_FILE_PATH)
        if not roms:
            kodi_notify('Advanced Emulator Launcher', 'Favourites XML empty. Add items to favourites first', 5000)
            return

        # Display Favourites
        for key in sorted(roms, key= lambda x : roms[x]["filename"]):
            self._gui_render_rom_row('0', '0', key, roms[key], False)
        xbmcplugin.endOfDirectory( handle = self.addon_handle, succeeded=True, cacheToDisc=False )

    #
    # Adds ROM to favourites
    #
    def _command_add_to_favourites(self, categoryID, launcherID, romID):
        # Load ROMs in launcher
        launcher = self.launchers[launcherID]
        roms_xml_file = launcher["roms_xml_file"]
        roms = fs_load_ROM_XML_file(roms_xml_file)
        if not roms:
            kodi_dialog_OK('Advanced Emulator Launcher',
                               'Empty roms launcher in _command_add_to_favourites()',
                               'This is a bug, please report it.')

        # Load favourites
        roms_fav = fs_load_Favourites_XML_file(FAVOURITES_FILE_PATH)
        
        # DEBUG
        log_verb('Adding ROM to Favourites')
        log_verb('romID {}'.format(romID))
        log_verb('name  {}'.format(roms[romID]['name']))

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
        roms_fav[romID] = roms[romID]
        roms_fav[romID]['launcherID']  = self.launchers[launcherID]['id']
        roms_fav[romID]['platform']    = self.launchers[launcherID]['platform']
        roms_fav[romID]['application'] = self.launchers[launcherID]['application']
        roms_fav[romID]['args']        = self.launchers[launcherID]['args']
        roms_fav[romID]['rompath']     = self.launchers[launcherID]['rompath']
        roms_fav[romID]['romext']      = self.launchers[launcherID]['romext']
        roms_fav[romID]['fav_status']  = 'OK'
        if roms_fav[romID]['thumb']  == '': roms_fav[romID]['thumb']  = self.launchers[launcherID]['thumb']
        if roms_fav[romID]['fanart'] == '': roms_fav[romID]['fanart'] = self.launchers[launcherID]['fanart']
        fs_write_Favourites_XML_file(FAVOURITES_FILE_PATH, roms_fav)

    #
    # Check ROMs in favourites and set fav_status field.
    # Note that categoryID = launcherID = '0'
    #
    def _command_check_favourites(self, categoryID, launcherID, romID):
        # Load Favourite ROMs
        roms_fav = fs_load_Favourites_XML_file(FAVOURITES_FILE_PATH)
        
        # Reset fav_status filed for all favourites
        log_debug('_command_check_favourites() STEP 0')
        for rom_fav_ID in roms_fav:
            roms_fav[rom_fav_ID]['fav_status'] = 'OK'
        
        # STEP 1: Find missing launchers
        log_debug('_command_check_favourites() STEP 1')
        for rom_fav_ID in roms_fav:
            if roms_fav[rom_fav_ID]['launcherID'] not in self.launchers:
                log_info('Fav ROM "{}" unlinked because launcherID not in launchers'.format(roms_fav[rom_fav_ID]['name']))
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
            rom_xml_path = self.launchers[launcher_id]["roms_xml_file"]
            roms = fs_load_ROM_XML_file(rom_xml_path)

            # Traverse all favourites and check them if belong to this launcher.
            # This should be efficient because traversing favourites is cheap but loading ROMs is expensive.
            for rom_fav_ID in roms_fav:
                if roms_fav[rom_fav_ID]['launcherID'] == launcher_id:
                    # Check if ROM ID exists
                    if roms_fav[rom_fav_ID]['id'] not in roms:
                        log_info('Fav ROM "{}" unlinked because romID not in launcher ROMs'.format(roms_fav[rom_fav_ID]['name']))
                        roms_fav[rom_fav_ID]['fav_status'] = 'Unlinked'

        # STEP 3: Check if file exists. Even if the ROM ID is not there because user 
        # deleted ROM or launcher, the file may still be there.
        log_debug('_command_check_favourites() STEP 3')
        for rom_fav_ID in roms_fav:
            if not os.path.isfile(roms_fav[rom_fav_ID]['filename']):
                log_info('Fav ROM "{}" broken because filename does not exist'.format(roms_fav[rom_fav_ID]['name']))
                roms_fav[rom_fav_ID]['fav_status'] = 'Broken'

        # Save favourite ROMs
        fs_write_Favourites_XML_file(FAVOURITES_FILE_PATH, roms_fav)

        # Update container to show changes in Favourites flags. If not, user has to exit Favourites and enter again.
        xbmc.executebuiltin('Container.Refresh')

    #
    # Deletes a ROM from a launcher.
    # If categoryID = launcherID = '0' then delete from Favourites
    #
    def _command_remove_rom(self, categoryID, launcherID, romID):
        if launcherID == '0':
            # Load Favourite ROMs
            roms = fs_load_Favourites_XML_file(FAVOURITES_FILE_PATH)
            if not roms:
                return

            # Confirm deletion
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher - Delete from Favourites', 
                               'ROM: {0}'.format(roms[romID]['name']),
                               'Are you sure you want to delete it from favourites?')
            if ret:
                roms.pop(romID)
                fs_write_Favourites_XML_file(FAVOURITES_FILE_PATH, roms)
                kodi_notify('Advanced Emulator Launcher', 'Deleted ROM from Favourites')
                # If Favourites is empty then go to root, if not refresh
                if len(roms) == 0:
                    xbmc.executebuiltin('ReplaceWindow(Programs,{})'.format(self.base_url))
                else:
                    xbmc.executebuiltin('Container.Refresh')
        else:
            # Load ROMs
            roms = fs_load_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'])
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
                fs_write_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'], roms, launcher)
                kodi_notify('Advanced Emulator Launcher', 'Deleted ROM from launcher')
                # If launcher is empty then go to root, if not refresh
                if len(roms) == 0:
                    xbmc.executebuiltin('ReplaceWindow(Programs,{})'.format(self.base_url))
                else:
                    xbmc.executebuiltin('Container.Refresh')

    #
    # Former _edit_rom()
    # Note that categoryID = launcherID = '0' if we are editing a ROM in Favourites
    #
    def _command_edit_rom(self, categoryID, launcherID, romID):
        # --- Load ROMs ---
        if launcherID == '0':
            roms = fs_load_Favourites_XML_file(FAVOURITES_FILE_PATH)
        else:
            roms_xml_file = self.launchers[launcherID]['roms_xml_file']
            roms = fs_load_ROM_XML_file(roms_xml_file)
    
        # --- Show a dialog with ROM editing options ---
        title = roms[romID]['name']
        finished_display = 'Status: Finished' if roms[romID]['finished'] == True else 'Status: Unfinished'
        dialog = xbmcgui.Dialog()
        if launcherID == '0':
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
                                  ['Scrape from {}'.format(self.scraper_metadata.fancy_name),
                                   'Import metadata from NFO file...',
                                   "Edit Title: '{}'".format(roms[romID]['name']),
                                   "Edit Release Year: '{}'".format(roms[romID]['year']),
                                   "Edit Studio: '{}'".format(roms[romID]['studio']),
                                   "Edit Genre: '{}'".format(roms[romID]['genre']),
                                   "Edit Description: '{}'".format(desc_str),
                                   'Load Description from file ...',
                                   'Save metadata to NFO file'])
            # --- Scrap rom metadata ---
            if type2 == 0:
                self._gui_scrap_rom_metadata(roms, romID, launcherID)
            # Import ROM metadata from NFO file
            elif type2 == 1:
                fs_import_ROM_NFO(launcher, roms, romID)
                info_str = fs_import_launcher_nfo(self.launchers[launcherID], roms, romID)
                kodi_notify('Advanced Emulator Launcher', info_str)
                fs_write_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'], roms, self.launchers[launcherID])
            # Edition of the rom title
            elif type2 == 2:
                keyboard = xbmc.Keyboard(roms[romID]["name"], 'Edit title')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    title = keyboard.getText()
                    if title == "":
                        title = roms[romID]["name"]
                    roms[romID]["name"] = title.rstrip()
                    fs_write_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'], roms, self.launchers[launcherID])
            # Edition of the rom release year
            elif type2 == 3:
                keyboard = xbmc.Keyboard(roms[romID]["year"], 'Edit release year')
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    roms[romID]["year"] = keyboard.getText()
                    fs_write_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'], roms, self.launchers[launcherID])
            # Edition of the rom studio name
            elif type2 == 4:
                keyboard = xbmc.Keyboard(roms[romID]["studio"], 'Edit studio')
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    roms[romID]["studio"] = keyboard.getText()
                    fs_write_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'], roms, self.launchers[launcherID])
            # Edition of the rom game genre
            elif type2 == 5:
                keyboard = xbmc.Keyboard(roms[romID]["genre"], 'Edit genre')
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    roms[romID]["genre"] = keyboard.getText()
                    fs_write_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'], roms, self.launchers[launcherID])
            # Import of the rom game plot
            elif type2 == 6:
                text_file = xbmcgui.Dialog().browse(1, 'Select description file (TXT|DAT)', "files", ".txt|.dat", False, False)
                if os.path.isfile(text_file):
                    text_plot = open(text_file)
                    string_plot = text_plot.read()
                    text_plot.close()
                    roms[romID]["plot"] = string_plot.replace('&quot;','"')
                    fs_write_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'], roms, self.launchers[launcherID])
            # Export ROM metadata to NFO file
            elif type2 == 7:
                info_str = fs_export_ROM_NFO(self.launchers[launcherID], roms[romID])
                kodi_notify('Advanced Emulator Launcher', info_str)

        # Edit thumb and fanart
        elif type == 1:
            self._gui_edit_image(IMAGE_THUMB, KIND_ROM, roms, romID, launcherID)

        elif type == 2:
            self._gui_edit_image(IMAGE_FANART, KIND_ROM, roms, romID, launcherID)

        # Edit status
        elif type == 3:
            finished = roms[romID]["finished"]
            finished = False if finished else True
            finished_display = 'Finished' if finished == True else 'Unfinished'
            roms[romID]["finished"] = finished
            fs_write_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'], roms, self.launchers[launcherID])
            kodi_dialog_OK('Advanced Emulator Launcher Information', 
                           'ROM "{}" status is now {}'.format(roms[romID]["name"], finished_display))

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
                filename = roms[romID]["filename"]
                romext   = roms[romID]["romext"]
                item_file = xbmcgui.Dialog().browse(1, 'Select the file', "files", "." + romext.replace("|", "|."), 
                                                    False, False, filename)
                roms[romID]["filename"] = item_file
                fs_write_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'], roms, self.launchers[launcherID])
            # Custom launcher application file path
            elif type2 == 1:
                altapp = roms[romID]["altapp"]
                filter_str = ".bat|.exe|.cmd" if sys.platform == "win32" else ''
                app = xbmcgui.Dialog().browse(1, 'Select ROM custom launcher application',
                                              "files", filter_str, False, False, altapp)
                # Returns empty tuple if dialog was canceled.
                if not app: return
                roms[romID]["altapp"] = app
                fs_write_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'], roms, self.launchers[launcherID])
            # Custom launcher arguments
            elif type2 == 2:
                keyboard = xbmc.Keyboard(roms[romID]["altarg"], 'Edit ROM custom application arguments')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    roms[romID]["altarg"] = keyboard.getText()
                    fs_write_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'], roms, self.launchers[launcherID])
            # Selection of the rom trailer file
            elif type2 == 3:
                trailer = xbmcgui.Dialog().browse(1, 'Select ROM Trailer file', 
                                                  "files",".mp4|.mpg|.avi|.wmv|.mkv|.flv", 
                                                  False, False, roms[romID]["trailer"])
                if not app: return
                roms[romID]["trailer"] = trailer
                fs_write_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'], roms, self.launchers[launcherID])
            # Selection of the rom customs path
            elif type2 == 4:
                custom = xbmcgui.Dialog().browse(0, 'Select ROM Extra-fanarts path', "files", "", 
                                                 False, False, roms[romID]["custom"])
                roms[romID]["custom"] = custom
                fs_write_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'], roms, self.launchers[launcherID])

        # Link this favourite ROM to a new parent ROM
        # ONLY IN FAVOURITE ROM EDITING
        elif type == 5:
            # STEP 1: select new launcher.
            launcher_IDs = []
            launcher_names = []
            for launcherID in self.launchers: 
                launcher_IDs.append(launcherID)
                launcher_names.append(self.launchers[launcherID]['name'])
            # Order alphabetically both lists
            sorted_idx = [i[0] for i in sorted(enumerate(launcher_names), key=lambda x:x[1])]
            launcher_IDs   = [launcher_IDs[i] for i in sorted_idx]
            launcher_names = [launcher_names[i] for i in sorted_idx]
            dialog = xbmcgui.Dialog()
            selected_launcher = dialog.select('New launcher for {}'.format(roms[romID]['name']), launcher_names)
            if not selected_launcher == -1:
                # STEP 2: select ROMs in that launcher.
                launcher_id = launcher_IDs[selected_launcher]
                rom_xml_path = self.launchers[launcher_id]["roms_xml_file"]
                launcher_roms = fs_load_ROM_XML_file(rom_xml_path)
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
                selected_rom = dialog.select('New ROM for {}'.format(roms[romID]['name']), roms_names)
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
                    if roms[launcher_rom_id]['thumb']  == '': roms[launcher_rom_id]['thumb']  = self.launchers[launcher_id]['thumb']
                    if roms[launcher_rom_id]['fanart'] == '': roms[launcher_rom_id]['fanart'] = self.launchers[launcher_id]['fanart']
                    # Save favourites
                    fs_write_Favourites_XML_file(FAVOURITES_FILE_PATH, roms)

        # --- Save ROMs ---
        if launcherID == '0':
            fs_write_Favourites_XML_file(FAVOURITES_FILE_PATH, roms)
        else:
            launcher = self.launchers[launcherID]
            fs_write_ROM_XML_file(roms_xml_file, roms, launcher)

        # It seems that updating the container does more harm than good... specially when having many ROMs
        # By the way, what is the difference between Container.Refresh() and Container.Update()
        # xbmc.executebuiltin("Container.Refresh")

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
    # ROM scanner. Called when user chooses "Add items" -> "Scan items"
    # Note that actually this command is "Add/Update" ROMs.
    #
    def _roms_import_roms(self, launcherID):
        log_debug('_roms_import_roms() ========== BEGIN ==========')
        
        # Get game system, thumbnails and fanarts paths from launcher
        selectedLauncher = self.launchers[launcherID]
        launcher_app     = selectedLauncher["application"]
        launcher_path    = selectedLauncher["rompath"]
        launcher_exts    = selectedLauncher["romext"]
        log_debug('Launcher "{}" selected'.format(selectedLauncher["name"])) 
        log_debug('launcher_app  = {}'.format(launcher_app)) 
        log_debug('launcher_path = {}'.format(launcher_path)) 
        log_debug('launcher_exts = {}'.format(launcher_exts))
        log_debug('platform      = {}'.format(selectedLauncher["platform"]))

        # Check if there is an XML for this launcher. If so, load it.
        # If file does not exist or is empty then return an empty dictionary.
        roms_xml_file = selectedLauncher['roms_xml_file']
        roms = fs_load_ROM_XML_file(roms_xml_file)
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
                                'Checking for dead entries...', "Path '{}'".format(launcher_path))
            for key in sorted(roms.iterkeys()):
                log_debug('Searching {}'.format(roms[key]['filename']))
                self.pDialog.update(i * 100 / num_roms)
                i += 1
                if not os.path.isfile(roms[key]["filename"]):
                    log_debug('Not found')
                    log_debug('Delete {} item entry'.format(roms[key]['filename']))
                    del roms[key]
                    num_removed_roms += 1
            self.pDialog.close()
            if num_removed_roms > 0:
                kodi_notify('Advanced Emulator Launcher', '{} dead ROMs removed successfully'.format(num_removed_roms))
                log_info('{} dead ROMs removed successfully'.format(num_removed_roms))
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
        log_info('Found {} files'.format(num_files))

        # ~~~ Now go processing file by file ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.pDialog.create('AEL - Scanning ROMs', 'Scanning {}'.format(launcher_path))
        log_debug('========== Processing ROMs ==========')
        num_new_roms = 0
        num_files_checked = 0
        for f_path in files:
            # --- Get all file name combinations ---
            ROM = misc_split_path(f_path)
            log_debug('*** Processing File ***')
            log_debug('ROM.path       "{}"'.format(ROM.path))
            # log_debug('ROM.path_noext "{}"'.format(ROM.path_noext))
            # log_debug('ROM.base       "{}"'.format(ROM.base))
            # log_debug('ROM.dirname    "{}"'.format(ROM.dirname))
            # log_debug('ROM.base_noext "{}"'.format(ROM.base_noext))
            # log_debug('ROM.ext        "{}"'.format(ROM.ext))

            # ~~~ Update progress dialog ~~~
            self.progress_number = num_files_checked * 100 / num_files
            self.file_text       = 'ROM {}'.format(ROM.base)
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
                if roms[rom_id]["filename"] == f_path:
                    log_debug('File already into launcher list') 
                    repeatedROM = True
            # If file already in ROM list skip it
            if repeatedROM:
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
        log_info('Removed dead ROMs {:6d}'.format(num_removed_roms))
        log_info('Files checked     {:6d}'.format(num_files_checked))
        log_info('New added ROMs    {:6d}'.format(num_new_roms))

        if len(roms) == 0:
            kodi_dialog_OK('Advanced Emulator Launcher', 
                           'No ROMs found! Make sure launcher directory and file extensions are correct.')
            return

        if num_new_roms == 0:
            kodi_dialog_OK('Advanced Emulator Launcher', 
                           'Launcher has {} ROMs and no new ROMs have been added.'.format(len(roms)))

        # --- If we have a No-Intro XML then audit roms after scanning ----------------------------
        if selectedLauncher['nointro_xml_file'] != '':
            nointro_xml_file = selectedLauncher['nointro_xml_file']
            log_info('Auditing ROMs using No-Intro DAT {}'.format(nointro_xml_file))

            # --- Update No-Intro status for ROMs ---
            # Note that roms dictionary is updated using Python pass by assigment.
            # See http://stackoverflow.com/questions/986006/how-do-i-pass-a-variable-by-reference
            (num_have, num_miss, num_unknown) = self._roms_update_NoIntro_status(roms, nointro_xml_file)

            # Report
            log_info('***** No-Intro audit finished. Report ******')
            log_info('No-Intro Have ROMs    {:6d}'.format(num_have))
            log_info('No-Intro Miss ROMs    {:6d}'.format(num_miss))
            log_info('No-Intro Unknown ROMs {:6d}'.format(num_unknown))
        else:
            log_info('No No-Intro DAT configured. No auditing ROMs.')

        # ~~~ Save ROMs XML file ~~~
        fs_write_ROM_XML_file(roms_xml_file, roms, self.launchers[launcherID])

        # ~~~ Notify user ~~~
        kodi_notify('Advanced Emulator Launcher', '{} new added ROMs'.format(num_new_roms))
        log_debug('_roms_import_roms() ========== END ==========')

        # --- Seems this is not needed ---
        # xbmc.executebuiltin('Container.Refresh')

    #
    # Helper function to update ROMs No-Intro status if user configured a No-Intro
    # DAT file.
    # Dictionaries are mutable, so roms can be changed because passed by assigment.
    #
    def _roms_update_NoIntro_status(roms, nointro_xml_file):
        # --- Check if DAT file exists ---
        if not os.path.isfile(nointro_xml_file):
            log_warn('_roms_update_NoIntro_status Not found {}'.format(nointro_xml_file))
            return (0, 0, 0)
        
        # --- Load No-Intro DAT ---
        roms_nointro = fs_load_NoIntro_XML_file(nointro_xml_file)
        
        # --- Check for errors ---
        if not roms_nointro:
            log_warn('_roms_update_NoIntro_status Error loading {}'.format(nointro_xml_file))
            return (0, 0, 0)

        # Put ROM names in a set. Set is the fastes Python container for searching 
        # elements (implements hashed search).
        roms_nointro_set = set(roms_nointro.keys())
        roms_set = set()
        for romID in roms:
            roms_set.add(roms[romID]['name'])
        
        # Traverse ROMs and check they are in the DAT
        num_have = num_miss = num_unknown = 0
        for romID in roms:
            if roms[romID]['name'] in roms_nointro_set:
                roms[romID]['nointro_status'] = 'Have'
                num_have += 1
            else:
                roms[romID]['nointro_status'] = 'Unknown'
                num_unknown += 1

        # Now add missing ROMs. Traverse the nointro set and add the ROM if it's not there.
        for nointro_rom in roms_nointro_set:
            if nointro_rom not in roms_set:
                # Add new "fake" missing ROM. This ROM cannot be launched!
                rom = fs_new_rom()
                romID = misc_generate_random_SID()
                rom['id'] = romID
                rom['name'] = nointro_rom
                rom['nointro_status'] = 'Miss'
                roms[romID] = rom
                num_miss += 1

        # Return statistics
        return (num_have, num_miss, num_unknown)
        
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
        # --- Update progress dialog ---
        metadata_scraper_text = 'Scraping metadata with {}'.format(self.scraper_metadata.name)
        self.pDialog.update(self.progress_number, self.file_text, metadata_scraper_text)

        # >> Test if NFO file exists
        nfo_file_path = ROM.path_noext + ".nfo"
        log_debug('Testing NFO file "{}"'.format(nfo_file_path))
        found_NFO_file = True if os.path.isfile(nfo_file_path) else False
        
        # >> Determine metadata action based on policy
        # >> scan_metadata_policy -> values="None|NFO Files|NFO Files + Scrapers|Scrapers"
        scan_metadata_policy  = self.settings['scan_metadata_policy']
        scan_clean_tags       = self.settings['scan_clean_tags']
        scan_title_formatting = self.settings['scan_title_formatting']
        scan_ignore_title     = self.settings['scan_ignore_title']
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
            log_error('Invalid scan_metadata_policy value = {}'.format(scan_metadata_policy))
            
        # >> Do metadata action based on policy
        if metadata_action == META_TITLE_ONLY:
            romdata['name'] = text_ROM_title_format(ROM.base_noext, scan_clean_tags, scan_title_formatting)
        elif metadata_action == META_NFO_FILE:
            nfo_file_path = ROM.path_noext + ".nfo"
            log_debug('Trying NFO file "{}"'.format(nfo_file_path))
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
                romdata['name'] = text_ROM_title_format(ROM.base_noext, scan_clean_tags, scan_title_formatting)
        elif metadata_action == META_SCRAPER:
            # --- Do a search and get a list of games ---
            rom_name_scrapping = text_clean_ROM_name_for_scrapping(ROM.base_noext)
            results = self.scraper_metadata.get_search(rom_name_scrapping, ROM.base_noext, platform)
            log_debug('Metadata scraper found {} result/s'.format(len(results)))
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
                    selectgame = dialog.select('Select game for ROM {}'.format(ROM.base_noext), rom_name_list)
                    if selectgame < 0: selectgame = 0

                    # Open progress dialog again
                    self.pDialog.create('Advanced Emulator Launcher - Scanning ROMs')
                    self.pDialog.update(self.progress_number, self.file_text, metadata_scraper_text)
                elif self.settings['metadata_mode'] == 1:
                    log_debug('Metadata automatic scraping. Selecting first result.') 
                    selectgame = 0
                else:
                    log_error('Invalid metadata_mode {}'.format(self.settings['metadata_mode'])) 
                    selectgame = 0

                # --- Grab metadata for selected game ---
                gamedata = self.scraper_metadata.get_metadata(results[selectgame])

                # --- Put metadata into ROM dictionary ---
                if scan_ignore_title:
                    # Ignore scraped title
                    romdata['name'] = text_ROM_title_format(ROM.base_noext, scan_clean_tags, scan_title_formatting)
                    log_debug("User wants to ignore scraper name. Setting name to '{}'".format(romdata['name']))
                else:
                    # Use scraped title
                    romdata['name'] = gamedata['title']
                    log_debug("User wants scrapped name. Setting name to '{}'".format(romdata['name']))
                romdata['genre']  = gamedata['genre']
                romdata['year']   = gamedata['year']
                romdata['studio'] = gamedata['studio']
                romdata['plot']   = gamedata['plot']
            else:
                log_verb('Metadata scraper found no games after searching. Only cleaning ROM name.')
                romdata['name'] = text_ROM_title_format(ROM.base_noext, scan_clean_tags, scan_title_formatting)
        else:
            log_error('Invalid metadata_action value = {}'.format(metadata_action))
        
        # ~~~~~ Search for local artwork ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # If thumbs/fanart have the same path, then assign names 
        #   (f_base_noext)_thumb, 
        #   (f_base_noext)_fanart
        # Otherwise, thumb/fanart name is same as ROM, but different extension.
        # If no local artwork is found them names are empty strings ''
        thumb_path_noext  = misc_get_thumb_path_noext(launcher, ROM)
        fanart_path_noext = misc_get_fanart_path_noext(launcher, ROM)
        # log_debug('thumb_path_noext  = "{}"'.format(thumb_path_noext))
        # log_debug('fanart_path_noext = "{}"'.format(fanart_path_noext))
        
        # --- Look for local artwork ---
        local_thumb  = misc_look_for_image(thumb_path_noext, IMG_EXTS)
        local_fanart = misc_look_for_image(fanart_path_noext, IMG_EXTS)
        log_verb('Local image scanner found Thumb  "{}"'.format(local_thumb))
        log_verb('Local image scanner found Fanart "{}"'.format(local_fanart))

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
        log_verb('Set Thumb to file "{}"'.format(romdata['thumb']))

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
        log_verb('Set Fanart to file "{}"'.format(romdata['fanart']))

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
            image_path_noext = misc_get_thumb_path_noext(launcher, ROM)
        elif image_kind == IMAGE_THUMB:
            scraping_mode    = self.settings['fanart_mode']
            scraper_obj      = self.scraper_fanart
            scraper_name     = self.scraper_fanart.name
            image_path_noext = misc_get_fanart_path_noext(launcher, ROM)
        else:
            kodi_notify_warn('Advanced Emulator Launcher', 'Wrong image_kind = {}'.format(image_kind))
            log_error('_roms_scrap_image() Wrong image_kind = {}'.format(image_kind))
            return ret_imagepath

        # --- Updated progress dialog ---
        file_text = 'ROM {}'.format(ROM.base)
        scraper_text = 'Scraping {} with {}. Searching for matching games...'.format(image_name, scraper_name)
        self.pDialog.update(self.progress_number, self.file_text, scraper_text)
        log_verb('Scraping {} with {}'.format(image_name, scraper_name))

        # --- Call scraper and get a list of games ---
        rom_name_scrapping = text_clean_ROM_name_for_scrapping(ROM.base_noext)
        results = scraper_obj.get_search(rom_name_scrapping, ROM.base_noext, platform)
        log_debug('{} scraper found {} result/s'.format(image_name, len(results)))
        if not results:
            log_debug('{} scraper did not found any game'.format(image_name))
            return ret_imagepath

        # --- Choose game to download image ---
        # settings.xml: id="thumb_mode"  default="0" values="Semi-automatic|Automatic"
        # settings.xml: id="fanart_mode" default="0" values="Semi-automatic|Automatic"
        if scraping_mode == 0:
            log_debug('{} semi-automatic scraping. User chooses.'.format(image_name))
            # Close progress dialog (and check it was not canceled)
            if self.pDialog.iscanceled(): self.pDialog_canceled = True
            self.pDialog.close()

            # Display corresponding game list found so user choses
            dialog = xbmcgui.Dialog()
            rom_name_list = []
            for game in results:
                rom_name_list.append(game['display_name'])
            selectgame = dialog.select('Select game for ROM {}'.format(ROM.base_noext), rom_name_list)
            if selectgame < 0: selectgame = 0

            # Open progress dialog again
            scraper_text = 'Scraping {} with {}. Game selected. Getting list of images...'.format(image_name, scraper_name)
            self.pDialog.create('Advanced Emulator Launcher - Scanning ROMs')
            self.pDialog.update(self.progress_number, self.file_text, scraper_text)
        elif scraping_mode == 1:
            log_debug('{} automatic scraping. Selecting first result.'.format(image_name)) 
            selectgame = 0
        else:
            log_error('{} invalid thumb_mode {}'.format(image_name, scraping_mode)) 
            selectgame = 0

        # --- Grab list of images for the selected game ---
        image_list = scraper_obj.get_images(results[selectgame])
        log_verb('{} scraper returned {} images'.format(image_name, len(image_list)))
        if not image_list:
            log_debug('{} scraper get_images() returned no images.'.format(image_name))
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
            log_debug('{} dialog returned image_url "{}"'.format(image_name, image_url))
            if image_url == '': image_url = image_list[0]['URL']

            # Reopen progress dialog
            scraper_text = 'Scraping {} with {}. Downloading image...'.format(image_name, scraper_name)
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
            log_debug('image_path_noext "{}"'.format(image_path_noext))
            log_debug('img_ext          "{}"'.format(img_ext))
            log_verb('Downloading URL  "{}"'.format(image_url))
            log_verb('Into local file  "{}"'.format(image_path))
            try:
                net_download_img(image_url, image_path)
            except socket.timeout:
                kodi_notify_warn('Advanced Emulator Launcher', 
                                 'Cannot download {} image (Timeout)'.format(image_name))

            # ~~~ Update Kodi cache with downloaded image ~~~
            # Recache only if local image is in the Kodi cache, this function takes care of that.
            kodi_update_image_cache(image_path)
            
            # --- Return value is downloaded image ---
            ret_imagepath = image_path
        else:
            log_debug('{} scraper: user chose local image "{}"'.format(image_name, image_url))
            ret_imagepath = image_url

        # --- Returned value ---
        return ret_imagepath

    # ---------------------------------------------------------------------------------------------
    # Launcher/ROM Thumb/Fanart image semiautomatic scrapers. 
    # Function is here because structure is very similar to scanner _roms_scrap_image(). User is 
    # presented with a list of scrapped images and chooses the best one.
    # Called when editing a Launcher/ROM from context menu.
    #
    # objects_dic is changed using Python pass by assigment
    # Caller is responsible for saving edited launcher/ROM
    # Be aware that maybe launcherID = '0' if editing a ROM in Favourites
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
                object_name = 'Launcher'
                artwork_path = objects_dic[objectID]['thumbpath']
                local_image = 0
                kodi_dialog_OK('AEL', 'Implement me')
            elif objects_kind == KIND_ROM:
                object_name = 'ROM'
                launcher = self.launchers[launcherID]
                ROM = misc_split_path(objects_dic[objectID]['filename'])
                image_path_noext = misc_get_thumb_path_noext(launcher, ROM)
                local_image = misc_look_for_image(image_path_noext, IMG_EXTS)
                platform = self.launchers[launcherID]['platform']
        elif image_kind == IMAGE_FANART:
            scraper_obj = self.scraper_fanart
            image_key   = 'fanart'
            image_name  = 'Fanart'
            if objects_kind == KIND_LAUNCHER:
                object_name = 'Launcher'
                artwork_path = objects_dic[objectID]['fanartpath']
                local_image = 0
                kodi_dialog_OK('AEL', 'Implement me')
            elif objects_kind == KIND_ROM:
                object_name = 'ROM'
                launcher = self.launchers[launcherID]
                ROM = misc_split_path(objects_dic[objectID]['filename'])
                image_path_noext = misc_get_fanart_path_noext(launcher, ROM)
                local_image = misc_look_for_image(image_path_noext, IMG_EXTS)
                platform = self.launchers[launcherID]['platform']
        log_debug('_gui_scrap_image_semiautomatic() Editing {} {}'.format(object_name, image_name))        

        # --- Ask user to edit the image search string ---
        keyboard = xbmc.Keyboard(objects_dic[objectID]['name'], 'Enter the string to search for...')
        keyboard.doModal()
        if not keyboard.isConfirmed(): return
        search_string = keyboard.getText()

        # --- Call scraper and get a list of games ---
        kodi_busydialog_ON()
        results = scraper_obj.get_search(search_string, ROM.base_noext, platform)
        kodi_busydialog_OFF()
        log_debug('{} scraper found {} result/s'.format(image_name, len(results)))
        if not results:
            log_debug('{} scraper did not found any game'.format(image_name))
            return

        # --- Choose game to download image ---
        # Display corresponding game list found so user choses
        dialog = xbmcgui.Dialog()
        rom_name_list = []
        for game in results:
            rom_name_list.append(game['display_name'])
        selectgame = dialog.select('Select game for ROM {}'.format(ROM.base_noext), rom_name_list)
        if selectgame < 0: selectgame = 0

        # --- Grab list of images for the selected game ---
        image_list = scraper_obj.get_images(results[selectgame])
        log_verb('{} scraper returned {} images'.format(image_name, len(image_list)))
        if not image_list:
            log_debug('{} scraper get_images() returned no images.'.format(image_name))
            return ret_imagepath

        # --- Always do semi-automatic scraping when editing images ---
        # If there is a local image add it to the list and show it to the user
        if os.path.isfile(local_image):
            image_list.insert(0, {'name' : 'Current local image', 'URL' : local_image, 'disp_URL' : local_image} ) 

        # Returns a list of dictionaries {'name', 'URL', 'disp_URL'}
        image_url = gui_show_image_select(image_list)
        log_debug('{} dialog returned image_url "{}"'.format(image_name, image_url))
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
            log_debug('image_path_noext "{}"'.format(image_path_noext))
            log_debug('img_ext          "{}"'.format(img_ext))
            log_verb('Downloading URL  "{}"'.format(image_url))
            log_verb('Into local file  "{}"'.format(image_path))
            try:
                net_download_img(image_url, image_path)
            except socket.timeout:
                kodi_notify_warn('Advanced Emulator Launcher', 
                                 'Cannot download {} image (Timeout)'.format(image_name))

            # ~~~ Update Kodi cache with downloaded image ~~~
            # Recache only if local image is in the Kodi cache, this function takes care of that.
            kodi_update_image_cache(image_path)
            
            # --- Return value is downloaded image ---
            ret_imagepath = image_path
        else:
            log_debug('{} scraper: user chose local image "{}"'.format(image_name, image_url))
            ret_imagepath = image_url

        # --- Edit using Python pass by assigment ---
        # >> Caller is responsible to save launchers/ROMs
        objects_dic[objectID][image_key] = ret_imagepath

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
    def _gui_scrap_rom_metadata(self, roms, romID, launcherID):
        # --- Grab ROM info and metadata scraper settings ---
        launcher = self.launchers[launcherID]
        platform = launcher['platform']
        f_path   = roms[romID]['filename']
        rom_name = roms[romID]['name']
        ROM      = misc_split_path(f_path)
        scan_clean_tags       = self.settings['scan_clean_tags']
        scan_title_formatting = self.settings['scan_title_formatting']
        scan_ignore_title     = self.settings['scan_ignore_title']

        # --- Ask user to enter ROM metadata search string ---
        keyboard = xbmc.Keyboard(rom_name, 'Enter the ROM search string...')
        keyboard.doModal()
        if not keyboard.isConfirmed(): return
        
        # --- Do a search and get a list of games ---
        rom_name_scrapping = text_clean_ROM_name_for_scrapping(ROM.base_noext)
        results = self.scraper_metadata.get_search(rom_name_scrapping, ROM.base_noext, platform)
        log_debug('Metadata scraper found {} result/s'.format(len(results)))
        if results:
            # Display corresponding game list found so user choses
            dialog = xbmcgui.Dialog()
            rom_name_list = []
            for game in results:
                rom_name_list.append(game['display_name'])
            selectgame = dialog.select('Select game for ROM {}'.format(rom_name), rom_name_list)
            if selectgame < 0: selectgame = 0

            # --- Grab metadata for selected game ---
            gamedata = self.scraper_metadata.get_metadata(results[selectgame])

            # --- Put metadata into ROM dictionary ---
            if scan_ignore_title:
                # >> Ignore scraped title
                roms[romID]['name'] = text_ROM_title_format(ROM.base_noext, scan_clean_tags, scan_title_formatting)
                log_debug("User wants to ignore scraper name. Setting name to '{}'".format(roms[romID]['name']))
            else:
                # >> Use scraped title
                roms[romID]['name'] = gamedata['title']
                log_debug("User wants scrapped name. Setting name to '{}'".format(roms[romID]['name']))
            roms[romID]['genre']  = gamedata['genre']
            roms[romID]['year']   = gamedata['year']
            roms[romID]['studio'] = gamedata['studio']
            roms[romID]['plot']   = gamedata['plot']

            # ROMs are saved in caller function
        else:
            kodi_notify('Advanced Emulator Launcher', 'No ROM metadata data found')

    #
    # Called when editing a launcher by _command_edit_launcher()
    # Scrap standalone launcher (typically a game) metadata
    # Called when editing a launcher...
    # Always do semi-automatic scraping when editing ROMs/Launchers
    #
    def _gui_scrap_launcher_metadata(self, launcherID):
        # Edition of the launcher name
        keyboard = xbmc.Keyboard(self.launchers[launcherID]["name"], 'Enter the launcher search string ...')
        keyboard.doModal()
        if not keyboard.isConfirmed(): return

        title = keyboard.getText()

        # Scrap and get a list of matches
        results, display = self._get_games_list(title)

        if display:
            # Display corresponding game list found
            dialog = xbmcgui.Dialog()

            # Game selection
            selectgame = dialog.select('Select a item from %s' % ( self.settings[ "datas_scraper" ] ), display)
            if not selectgame == -1:
                if self.settings[ "ignore_title" ]:
                    self.launchers[launcherID]["name"] = title_format(self,self.launchers[launcherID]["name"])
                else:
                    self.launchers[launcherID]["name"] = title_format(self,results[selectgame]["title"])

                # User made a decision. Get full metadata
                gamedata = self._get_game_data(results[selectgame]["id"])
                self.launchers[launcherID]["genre"]  = gamedata["genre"]
                self.launchers[launcherID]["year"]   = gamedata["year"]
                self.launchers[launcherID]["studio"] = gamedata["studio"]
                self.launchers[launcherID]["plot"]   = gamedata["plot"]
        else:
            kodi_notify('Advanced Emulator Launcher', 'No data found')

        # Save launchers XML
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

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
        roms_xml_file = launcher['roms_xml_file']
        roms = fs_load_ROM_XML_file(roms_xml_file)
        if not roms: return

        # --- Choose ROM file ---
        dialog = xbmcgui.Dialog()
        extensions = "." + romext.replace('|', '|.')
        romfile = dialog.browse(1, 'Select the ROM file', 'files', extensions, False, False, rompath)
        if not romfile: return

        # --- Format title ---
        scan_clean_tags       = self.settings['scan_clean_tags']
        scan_title_formatting = self.settings['scan_title_formatting']
        ROM = misc_split_path(romfile)
        romname = text_ROM_title_format(ROM.base_noext, scan_clean_tags, scan_title_formatting)
        
        # --- Search for local Thumb/Fanart ---
        thumb_path_noext  = misc_get_thumb_path_noext(selectedLauncher, ROM)
        fanart_path_noext = misc_get_fanart_path_noext(selectedLauncher, ROM)
        local_thumb  = misc_look_for_image(thumb_path_noext, IMG_EXTS)
        local_fanart = misc_look_for_image(fanart_path_noext, IMG_EXTS)
        log_verb('Local images set Thumb  "{}"'.format(local_thumb))
        log_verb('Local images set Fanart "{}"'.format(local_fanart))

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
        fs_write_ROM_XML_file(roms_xml_file, roms, launcher)

    #
    # Search ROMs in launcher
    #
    def _command_search_launcher(self, categoryID, launcherID):
        # Check that the launcher has items
        if not os.path.isfile(self.launchers[launcherID]["roms_xml_file"]):
            kodi_notify('Advanced Emulator Launcher', 'Launcher XML missing. Add items to launcher')
            xbmc.executebuiltin("Container.Refresh")
            return
        roms = fs_load_ROM_XML_file(self.launchers[launcherID]["roms_xml_file"])
        if not roms:
            kodi_notify('Advanced Emulator Launcher', 'Launcher XML empty. Add items to launcher')
            return

        # Ask user what category to search
        dialog = xbmcgui.Dialog()
        type = dialog.select('Search items...', 
                             ['By Title',
                              'By Release Year',
                              'By Studio',
                              'By Genre'])

        # Search by Title
        type_nb = 0
        if type == type_nb:
            keyboard = xbmc.Keyboard("", 'Enter the file title to search...')
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
                xbmc.executebuiltin("ReplaceWindow(Programs,{0})".format(url))
                
                # Using ActivateWindow with return address seems to have no effect. Note that dialogs
                # are called with handle -1, and that seems to cause trouble. ActivateWindow does
                # not honour the url_return.
                # url_return = self._misc_url('SHOW_ROMS', categoryID, launcherID)
                # url_return = self._misc_url('SHOW_LAUNCHERS', categoryID)
                # log_debug('URL RETURN = {0}'.format(url_return))
                # xbmc.executebuiltin("ActivateWindow(Programs,{0},{1})".format(url, url_return))
                
                # Does not work
                # xbmc.executebuiltin("RunPlugin({0})".format(url))
                
                # Does not work
                # xbmc.executebuiltin("RunAddon({0})".format(url))
                
        # Search by Release Date
        type_nb = type_nb + 1
        if type == type_nb:
            searched_list = self._search_launcher_category(launcherID, "year", roms)
            dialog = xbmcgui.Dialog()
            selected_value = dialog.select('Select a Release year ...', searched_list)
            if selected_value >= 0:
                search_string = searched_list[selected_value]
                url = self._misc_url_search('EXEC_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_YEAR', search_string)
                xbmc.executebuiltin("ReplaceWindow(Programs,{0})".format(url))

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
            searched_list = self._search_launcher_category(launcherID, "studio", roms)
            dialog = xbmcgui.Dialog()
            selected_value = dialog.select('Select a Studio ...', searched_list)
            if selected_value >= 0:
                search_string = searched_list[selected_value]
                url = self._misc_url_search('EXEC_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_STUDIO', search_string)
                xbmc.executebuiltin("ReplaceWindow(Programs,{0})".format(url))

        # Search by Genre
        type_nb = type_nb + 1
        if type == type_nb:
            searched_list = self._search_launcher_category(launcherID, "genre", roms)
            dialog = xbmcgui.Dialog()
            selected_value = dialog.select('Select a Genre ...', searched_list)
            if selected_value >= 0:
                search_string = searched_list[selected_value]
                url = self._misc_url_search('EXEC_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_GENRE', search_string)
                xbmc.executebuiltin("ReplaceWindow(Programs,{0})".format(url))

    def _search_launcher_category(self, launcherID, search_dic_field, roms):
        # Maybe this can be optimized a bit to make the search faster...
        search = []
        for keyr in sorted(roms.iterkeys()):
            if roms[keyr][search_dic_field] == "":
                search.append("[ %s ]" % 'Not Set')
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

        # Load ROMs
        # Check that the launcher has items
        if not os.path.isfile(self.launchers[launcherID]["roms_xml_file"]):
            kodi_notify('Advanced Emulator Launcher', 'Launcher XML missing. Add items to launcher')
            xbmc.executebuiltin("Container.Refresh")
            return
        roms = fs_load_ROM_XML_file(self.launchers[launcherID]["roms_xml_file"])
        if not roms:
            kodi_notify('Advanced Emulator Launcher', 'Launcher XML empty. Add items to launcher')
            return

        # Go through rom list and search for user input
        rl = {}
        notset = ("[ %s ]" % 'Not Set')
        text = search_string.lower()
        empty = notset.lower()
        for keyr in roms:
            rom = roms[keyr][rom_search_field].lower()
            if rom == "" and text == empty:
                rl[keyr] = roms[keyr]

            if rom_search_field == 'name':
                if not rom.find(text) == -1:
                    rl[keyr] = roms[keyr]
            else:
                if rom == text:
                    rl[keyr] = roms[keyr]

        # Print the list sorted (if there is anything to print)
        if not rl:
            kodi_dialog_OK('Advaned Emulator Launcher', 'Search produced no results')
        for key in sorted(rl.iterkeys()):
            self._gui_render_rom_row(categoryID, launcherID, key, rl[key])
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

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
