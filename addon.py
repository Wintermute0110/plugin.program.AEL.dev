#
# Advanced Emulator Launcher main script file
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
import sys, os, fnmatch, time, datetime, math, random, shutil, string
import re, urllib, urllib2, urlparse, socket, exceptions, hashlib
from traceback import print_exc
from operator import itemgetter

# --- Kodi stuff ---
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

# --- Modules/packages in this plugin ---
import resources.subprocess_hack
from resources.user_agent import getUserAgent
from resources.file_item import Thumbnails
from resources.emulators import *
from resources.file_IO import *
from resources.utils import *
# from resources.net_IO import *

# --- Plugin constants ---
__plugin__  = "Advanced Emulator Launcher"
__version__ = "0.9.0"
__author__  = "Wintermute0110, Angelscry"
__url__     = "https://github.com/Wintermute0110/plugin.program.advanced.emulator.launcher"
__git_url__ = "https://github.com/Wintermute0110/plugin.program.advanced.emulator.launcher"
__credits__ = "Leo212 CinPoU, JustSomeUser, Zerqent, Zosky, Atsumori"

# --- Addon paths definition ---
# _FILE_PATH is a filename
# _DIR is a directory (with trailing /)
PLUGIN_DATA_DIR      = xbmc.translatePath(os.path.join('special://profile/addon_data', 'plugin.program.advanced.emulator.launcher'))
BASE_DIR             = xbmc.translatePath(os.path.join('special://', 'profile'))
HOME_DIR             = xbmc.translatePath(os.path.join('special://', 'home'))
KODI_FAV_FILE_PATH   = xbmc.translatePath( 'special://profile/favourites.xml' )
ADDONS_DIR           = xbmc.translatePath(os.path.join(HOME_DIR, 'addons'))
CURRENT_ADDON_DIR    = xbmc.translatePath(os.path.join(ADDONS_DIR, 'plugin.program.advanced.emulator.launcher'))
ICON_IMG_FILE_PATH   = os.path.join(CURRENT_ADDON_DIR, 'icon.png')
CATEGORIES_FILE_PATH = os.path.join(PLUGIN_DATA_DIR, 'categories.xml')
FAVOURITES_FILE_PATH = os.path.join(PLUGIN_DATA_DIR, 'favourites.xml')
DEFAULT_THUMB_DIR    = os.path.join(PLUGIN_DATA_DIR, 'thumbs')
DEFAULT_FANART_DIR   = os.path.join(PLUGIN_DATA_DIR, 'fanarts')
DEFAULT_NFO_DIR      = os.path.join(PLUGIN_DATA_DIR, 'nfos')
ADDON_ID             = "plugin.program.advanced.emulator.launcher"

# --- Initialise log system ---
# Synchronise this with user's preferences in Kodi when loading Kodi settings
set_log_level(LOG_DEBUG)

# --- Addon object (used to access settings) ---
addon_obj = xbmcaddon.Addon(id = ADDON_ID)

# --- Main code ---
class Main:
    settings = {}
    launchers = {}
    categories = {}

    def __init__( self, *args, **kwargs ):
        # --- Fill in settings dictionary using addon_obj.getSetting() ---
        self._get_settings()

        # --- Some debug stuff for development ---
        log_debug('---------- Called AEL addon.py Main() constructor ----------')
        # log_debug(sys.version)
        for i in range(len(sys.argv)):
            log_debug('sys.argv[{0}] = "{1}"'.format(i, sys.argv[i]))
        # log_debug('PLUGIN_DATA_DIR      = "{0}"'.format(PLUGIN_DATA_DIR))
        # log_debug('BASE_DIR             = "{0}"'.format(BASE_DIR))
        # log_debug('HOME_DIR             = "{0}"'.format(HOME_DIR))
        # log_debug('FAVOURITES_DIR       = "{0}"'.format(FAVOURITES_DIR))
        # log_debug('ADDONS_DIR           = "{0}"'.format(ADDONS_DIR))
        # log_debug('CURRENT_ADDON_DIR    = "{0}"'.format(CURRENT_ADDON_DIR))
        # log_debug('ICON_IMG_FILE_PATH   = "{0}"'.format(ICON_IMG_FILE_PATH))
        # log_debug('CATEGORIES_FILE_PATH = "{0}"'.format(CATEGORIES_FILE_PATH))
        # log_debug('DEFAULT_THUMB_DIR    = "{0}"'.format(DEFAULT_THUMB_DIR))
        # log_debug('DEFAULT_FANART_DIR   = "{0}"'.format(DEFAULT_FANART_DIR))
        # log_debug('DEFAULT_NFO_DIR      = "{0}"'.format(DEFAULT_NFO_DIR))

        # --- Addon data paths creation ---
        if not os.path.isdir(PLUGIN_DATA_DIR):    os.makedirs(PLUGIN_DATA_DIR)
        if not os.path.isdir(DEFAULT_THUMB_DIR):  os.makedirs(DEFAULT_THUMB_DIR)
        if not os.path.isdir(DEFAULT_FANART_DIR): os.makedirs(DEFAULT_FANART_DIR)
        if not os.path.isdir(DEFAULT_NFO_DIR):    os.makedirs(DEFAULT_NFO_DIR)

        # New Kodi URL code
        self.base_url = sys.argv[0]
        self.addon_handle = int(sys.argv[1])
        args = urlparse.parse_qs(sys.argv[2][1:])
        log_debug('args = {0}'.format(args))

        #
        # Experiment to try to increase the number of views the addon supports
        #
        # xbmcplugin.setContent(handle = self.addon_handle, content = 'movies')

        # Adds a sorting method for the media list.
        if self.addon_handle > 0:
            xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
            xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)
            xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_STUDIO)
            xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_GENRE)
            xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)

        # --- WORKAROUND ---
        # When the addon is installed and the file categories.xml does not exist, just
        # create an empty one with a default launcher. Later on, when I am more familiar
        # with the addon add a welcome wizard or something similar.
        #
        # Create a default categories.xml file if does not exist yet (plugin just installed)
        if not os.path.isfile(CATEGORIES_FILE_PATH):
            gui_kodi_dialog_OK('Advanced Emulator Launcher',
                               'It looks it is the first time you run AEL!',
                               '',
                               'Creating default categories.xml')
            self._cat_create_default()
            self._fs_write_catfile()

        # Load categories.xml and fill categories dictionary
        self._fs_load_catfile()

        # get users scrapers preference
        self._get_scrapers()
    
        # ~~~~~ Process URL commands ~~~~~
        # Interestingly, if plugin is called as type executable then args is empty.
        # However, if plugin is called as type video then Kodi adds the following
        # even for the first call: 'content_type': ['video']
        if 'content_type' in args:
            self._content_type = 'video'
        else:
            self._content_type = 'program'

        # If no com parameter display categories.
        # There are no parameters when the user first runs AEL (ONLY if called as an executable!).
        # Display categories listbox (addon root directory)
        if 'com' not in args:
            self._print_log('Advanced Emulator Launcher root folder > Categories list')
            self._gui_render_categories()
            return

        # There is a command to process
        # For some reason args['com'] is a list, so get first element of the list (a string)
        command = args['com'][0]
        if command == 'ADD_CATEGORY':
            self._command_add_new_category()

        elif command == 'EDIT_CATEGORY':
            self._command_edit_category(args['catID'][0])

        elif command == 'DELETE_CATEGORY':
            gui_kodi_dialog_OK('ERROR', 'DELETE_CATEGORY not implemented yet')

        elif command == 'SHOW_FAVOURITES':
            self._command_show_favourites()

        elif command == 'SHOW_LAUNCHERS':
            self._gui_render_launchers(args['catID'][0])

        elif command == 'ADD_LAUNCHER':
            # elif self._cat_empty_cat(categoryID):
            self._command_add_new_launcher(args['catID'][0])

        elif command == 'EDIT_LAUNCHER':
            self._command_edit_launcher(args['launID'][0])

        elif command == 'DELETE_LAUNCHER':
            gui_kodi_dialog_OK('ERROR', 'DELETE_LAUNCHER not implemented yet')
            # if (rom == REMOVE_COMMAND):
            #    self._remove_launcher(launcher)

        elif command == 'SHOW_ROMS':
            launcherID = args['launID'][0]
            # User clicked on a launcher. For executable launchers run the executable.
            # For emulator launchers show roms.
            if self.launchers[launcherID]["rompath"] == '':
                self._print_log('SHOW_ROMS | Launcher rompath is empty. Assuming launcher is standalone.')
                self._print_log('SHOW_ROMS | Calling _run_launcher()')
                self._run_standalone_launcher(args['catID'][0], args['launID'][0])
            else:
                self._print_log('SHOW_ROMS | Calling _gui_render_roms()')
                self._gui_render_roms(args['catID'][0], args['launID'][0])

        elif command == 'ADD_ROMS':
            self._command_add_roms(args['launID'][0])

        elif command == 'EDIT_ROM':
            self._command_edit_rom(args['catID'][0], args['launID'][0], args['romID'][0])

        elif command == 'DELETE_ROM':
             self._command_remove_rom(args['catID'][0], args['launID'][0], args['romID'][0])

        elif args['com'][0] == 'LAUNCH_ROM':
            self._run_rom(args['catID'][0], args['launID'][0], args['romID'][0])

        elif command == 'ADD_TO_FAVOURITES':
            self._command_add_to_favourites(args['catID'][0], args['launID'][0], args['romID'][0])

        else:
            gui_kodi_dialog_OK('Advanced Emulator Launcher - ERROR', 'Unknown command {0}'.format(args['com'][0]) )            
            return
        
        return

        # Process script parameters
        param = param[1:]
        command = param.split(COMMAND_ARGS_SEPARATOR)
        command_part = command[0].split("/")
        self._print_log('command = {0}'.format(command))
        self._print_log('command_part = {0}'.format(command_part))


        # check the action needed
        if ( len(command_part) == 4 ):
            category = command_part[0]
            launcher = command_part[1]
            rom = command_part[2]
            action = command_part[3]

            if (action == SEARCH_COMMAND):
                self._find_roms(False)

            elif (action == GET_INFO):
                self._scrap_rom(launcher, rom)
            elif (action == GET_THUMB):
                self._scrap_thumb_rom(launcher, rom)
            elif (action == GET_FANART):
                self._scrap_fanart_rom(launcher, rom)

        if ( len(command_part) == 3 ):
            category = command_part[0]
            launcher = command_part[1]
            rom = command_part[2]

            if (rom == SEARCH_COMMAND):
                self._find_roms(False)

            elif (rom == GET_INFO):
                self._scrap_launcher(launcher)
            elif (rom == GET_THUMB):
                self._scrap_thumb_launcher(launcher)
            elif (rom == GET_FANART):
                self._scrap_fanart_launcher(launcher)

        if ( len(command_part) == 2 ):
            category = command_part[0]
            launcher = command_part[1]

            if (launcher == SEARCH_COMMAND):
                self._find_roms(False)

            elif (launcher == GET_INFO):
                self._modify_category(category)
                xbmc.executebuiltin("Container.Refresh")

            elif (launcher == GET_THUMB):
                self._scrap_thumb_category(category)

            elif (launcher == GET_FANART):
                self._scrap_fanart_category(category)
            
            # Search commands
            elif (launcher == SEARCH_ITEM_COMMAND):
                self._find_add_roms(category)
            elif (launcher == SEARCH_DATE_COMMAND):
                self._find_date_add_roms(category)
            elif (launcher == SEARCH_PLATFORM_COMMAND):
                self._find_platform_add_roms(category)
            elif (launcher == SEARCH_STUDIO_COMMAND):
                self._find_studio_add_roms(category)
            elif (launcher == SEARCH_GENRE_COMMAND):
                self._find_genre_add_roms(category)

        # param is of the form "?md5_hash_str"
        # User selected one category in the root folder. Display that category launchers
        if len(command_part) == 1:
            categoryID = command_part[0]
            self._print_log('%s category folder > Launcher list' % categoryID)

            if (categoryID == SCAN_NEW_ITEM_COMMAND):
                self._find_roms(False)

            if (categoryID == SEARCH_COMMAND):
                self._find_roms(False)

    #
    # Creates default categories data struct
    # CAREFUL deletes current categories!
    # From _load_launchers
    # Else create the default category
    # self.categories["default"] = {"id":"default", "name":"Default", "thumb":"", "fanart":"", "genre":"", "plot":"", "finished":"false"}
    #
    def _cat_create_default(self):
        category = {}
        category['name']        = 'Emulators'
        category['thumb']       = ''
        category['fanart']      = ''
        category['genre']       = ''
        category['description'] = ''
        category['finished']    = False

        # The key in the categories dictionary is an MD5 hash generate with current time plus some random number.
        # This will make it unique and different for every category created.
        category_key = misc_generate_random_SID()
        self.categories = {}
        self.categories[category_key] = category

    #
    # Checks if the category is empty (no launchers defined)
    #
    def _cat_empty_cat(self, categoryID):
        empty_category = True
        for cat in self.launchers.iterkeys():
            if self.launchers[cat]['category'] == categoryID:
                empty_category = False

        return empty_category


    #
    # Deletes a ROM from a launcher.
    # If categoryID = launcherID = '0' then delete from Favourites
    #
    def _command_remove_rom(self, categoryID, launcherID, romID):
        if launcherID == '0':
            # Load Favourite ROMs
            roms = self._fs_load_Favourites_XML_file(FAVOURITES_FILE_PATH)
            if not roms:
                return

            # Confirm deletion
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher - Delete from Favourites', 
                               'ROM: {0}'.format(roms[romID]['name']),
                               'Are you sure you want to delete it from favourites?')
            if ret:
                roms.pop(romID)
                self._fs_write_Favourites_XML_file(roms, FAVOURITES_FILE_PATH)
                gui_kodi_notify('AEL', 'Deleted ROM from Favourites')
                # If Favourites is empty then go to root, if not refresh
                if len(roms) == 0:
                    xbmc.executebuiltin('ReplaceWindow(Programs,{0})'.format(self._path))
                else:
                    xbmc.executebuiltin('Container.Update({0})'.format(self._misc_url('SHOW_FAVOURITES')))
        else:
            # Load ROMs
            roms = self._fs_load_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'])
            if not roms:
                return

            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher - Delete from Favourites',
                               'Launcher: {0}'.format(self.launchers[launcherID]['name']),
                               'ROM: {0}'.format(roms[romID]['name']),
                               'Are you sure you want to delete it from launcher?')
            if ret:
                roms.pop(romID)
                self._fs_write_ROM_XML_file(roms, launcherID, self.launchers[launcherID]['roms_xml_file'])
                gui_kodi_notify('AEL', 'Deleted ROM from launcher')
                # If launcher is empty then go to root, if not refresh
                if len(roms) == 0:
                    xbmc.executebuiltin('ReplaceWindow(Programs,{0})'.format(self._path))
                else:
                    xbmc.executebuiltin('Container.Update({0})'.format(self._misc_url('SHOW_ROMS', categoryID, launcherID)))

    #
    # Former _edit_rom()
    # Note that categoryID = launcherID = '0' if we are editing a ROM in Favourites
    def _command_edit_rom(self, categoryID, launcherID, romID):
        gui_kodi_dialog_OK('AEL', 'Editing ROM not implemented yet')
        return

        title = os.path.basename(self.launchers[launcher]["roms"][rom]["name"])
        finished_display = 'Status : Finished' if self.launchers[launcher]["roms"][rom]["finished"] == True else 'Status : Unfinished'
        dialog = xbmcgui.Dialog()
        type = dialog.select('Select Action for %s' % title, 
                             ['Scrape Metadata, Thumbnail and Fanart', 'Modify Metadata',
                              'Change Thumbnail Image', 'Change Fanart Image',
                              finished_display,
                              'Advanced Modifications', 'Delete ROM'])

        if type == 0:
            # Scrap item (infos and images)
            self._full_scrap_rom(launcher,rom)

        if type == 1:
            dialog = xbmcgui.Dialog()

            type2 = dialog.select('Modify Item Infos', 
                                  ['Import from %s' % self.settings[ "datas_scraper" ],
                                   'Import from .nfo file',
                                   'Modify Title : %s' % self.launchers[launcher]["roms"][rom]["name"],
                                   'Modify Release Date : %s' % self.launchers[launcher]["roms"][rom]["release"],
                                   'Modify Studio : %s' % self.launchers[launcher]["roms"][rom]["studio"],
                                   'Modify Genre : %s' % self.launchers[launcher]["roms"][rom]["genre"],
                                   'Modify Description : %s ...' % self.launchers[launcher]["roms"][rom]["plot"][0:20],
                                   'Save to .nfo file'])
            # Scrap rom Infos
            if type2 == 0:
                self._scrap_rom(launcher,rom)
            elif type2 == 1:
                self._import_rom_nfo(launcher,rom)
            elif type2 == 2:
                # Edition of the rom title
                keyboard = xbmc.Keyboard(self.launchers[launcher]["roms"][rom]["name"], 'Edit title')
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    title = keyboard.getText()
                    if ( title == "" ):
                        title = self.launchers[launcher]["roms"][rom]["name"]
                    self.launchers[launcher]["roms"][rom]["name"] = title.rstrip()
                    self._save_launchers()
            elif type2 == 3:
                # Edition of the rom release date
                keyboard = xbmc.Keyboard(self.launchers[launcher]["roms"][rom]["release"], 'Edit release year')
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    self.launchers[launcher]["roms"][rom]["release"] = keyboard.getText()
                    self._save_launchers()
            elif type2 == 4:
                # Edition of the rom studio name
                keyboard = xbmc.Keyboard(self.launchers[launcher]["roms"][rom]["studio"], 'Edit studio')
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    self.launchers[launcher]["roms"][rom]["studio"] = keyboard.getText()
                    self._save_launchers()
            elif type2 == 5:
                # Edition of the rom game genre
                keyboard = xbmc.Keyboard(self.launchers[launcher]["roms"][rom]["genre"], 'Edit genre')
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    self.launchers[launcher]["roms"][rom]["genre"] = keyboard.getText()
                    self._save_launchers()
            elif type2 == 6:
                # Import of the rom game plot
                text_file = xbmcgui.Dialog().browse(1, 'Select description file. (e.g txt|dat)', "files", ".txt|.dat", False, False)
                if (os.path.isfile(text_file)):
                    text_plot = open(text_file)
                    string_plot = text_plot.read()
                    text_plot.close()
                    self.launchers[launcher]["roms"][rom]["plot"] = string_plot.replace('&quot;','"')
                    self._save_launchers()
            elif type2 == 7:
                self._export_rom_nfo(launcher,rom)

        # Edit Thumb
        if type == 2:
            dialog = xbmcgui.Dialog()
            thumb_diag = 'Import Image from %s' % ( self.settings[ "thumbs_scraper" ] )
            if ( self.settings[ "thumbs_scraper" ] == "GameFAQs" ) | ( self.settings[ "thumbs_scraper" ] == "MobyGames" ):
                thumb_diag = 'Import from %s : %s thumbs' % ( self.settings[ "thumbs_scraper" ],self.settings[ "display_game_region" ])
            if ( self.settings[ "thumbs_scraper" ] == "Google" ):
                thumb_diag = 'Import from %s : %s size' % ( self.settings[ "thumbs_scraper" ],self.settings[ "thumb_image_size_display" ].capitalize())
            
            type2 = dialog.select('Change Thumbnail Image', [thumb_diag,'Import Local Image (Copy and Rename)','Select Local Image (Link)'])
            if (type2 == 0 ):
                self._scrap_thumb_rom(launcher,rom)
            if (type2 == 1 ):
                # Import a rom thumbnail image
                image = xbmcgui.Dialog().browse(2,'Select thumbnail image',"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(self.launchers[launcher]["thumbpath"]))
                if (image):
                    if (os.path.isfile(image)):
                        img_ext = os.path.splitext(image)[-1][0:4]
                        if ( img_ext != '' ):
                            filename = self.launchers[launcher]["roms"][rom]["filename"]
                            if (self.launchers[launcher]["thumbpath"] == self.launchers[launcher]["fanartpath"] ):
                                if (self.launchers[launcher]["thumbpath"] == self.launchers[launcher]["rompath"] ):
                                    file_path = filename.replace("."+filename.split(".")[-1], '_thumb'+img_ext)
                                else:
                                    file_path = os.path.join(os.path.dirname(self.launchers[launcher]["thumbpath"]),os.path.basename(filename.replace("."+filename.split(".")[-1], '_thumb'+img_ext)))
                            else:
                                if (self.launchers[launcher]["thumbpath"] == self.launchers[launcher]["rompath"] ):
                                    file_path = filename.replace("."+filename.split(".")[-1], img_ext)
                                else:
                                    file_path = os.path.join(os.path.dirname(self.launchers[launcher]["thumbpath"]),os.path.basename(filename.replace("."+filename.split(".")[-1], img_ext)))
                            if ( image != file_path ):
                                try:
                                    shutil.copy2( image.decode(get_encoding(),'ignore') , file_path.decode(get_encoding(),'ignore') )
                                    if ( self.launchers[launcher]["roms"][rom]["thumb"] != "" ):
                                        _update_cache(file_path)
                                    self.launchers[launcher]["roms"][rom]["thumb"] = file_path
                                    self._save_launchers()
                                    xbmc_notify('Advanced Emulator Launcher', 'Thumb has been updated',3000)
                                except OSError:
                                    xbmc_notify('Advanced Emulator Launcher', 'Impossible to assign thumb for %s' % self.launchers[launcher]["roms"][rom]["name"],3000)

            if (type2 == 2 ):
                # Link to a rom thumbnail image
                if (self.launchers[launcher]["roms"][rom]["thumb"] == ""):
                    imagepath = self.launchers[launcher]["roms"][rom]["filename"]
                else:
                    imagepath = self.launchers[launcher]["roms"][rom]["thumb"]
                image = xbmcgui.Dialog().browse(2,'Select thumbnail image',"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(imagepath))
                if (image):
                    if (os.path.isfile(image)):
                        if ( self.launchers[launcher]["roms"][rom]["thumb"] != "" ):
                            _update_cache(image)
                        self.launchers[launcher]["roms"][rom]["thumb"] = image
                        self._save_launchers()
                        xbmc_notify('Advanced Emulator Launcher', 'Thumb has been updated',3000)

        if (type == 3 ):
            dialog = xbmcgui.Dialog()
            fanart_diag = 'Import Image from %s' % ( self.settings[ "fanarts_scraper" ] )
            if ( self.settings[ "fanarts_scraper" ] == "Google" ):
                fanart_diag = 'Import from %s : %s size' % ( self.settings[ "fanarts_scraper" ],self.settings[ "fanart_image_size_display" ].capitalize())
            type2 = dialog.select('Change Fanart Image', [fanart_diag,'Import Local Image (Copy and Rename)','Select Local Image (Link)'])
            if (type2 == 0 ):
                self._scrap_fanart_rom(launcher,rom)
            if (type2 == 1 ):
                # Import a rom fanart image
                image = xbmcgui.Dialog().browse(2,'Select fanart image',"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(self.launchers[launcher]["fanartpath"]))
                if (image):
                    if (os.path.isfile(image)):
                        img_ext = os.path.splitext(image)[-1][0:4]
                        if ( img_ext != '' ):
                            filename = self.launchers[launcher]["roms"][rom]["filename"]
                            if (self.launchers[launcher]["thumbpath"] == self.launchers[launcher]["fanartpath"] ):
                                if (self.launchers[launcher]["fanartpath"] == self.launchers[launcher]["rompath"] ):
                                    file_path = filename.replace("."+filename.split(".")[-1], '_fanart'+img_ext)
                                else:
                                    file_path = os.path.join(os.path.dirname(self.launchers[launcher]["fanartpath"]),os.path.basename(filename.replace("."+filename.split(".")[-1], '_fanart'+img_ext)))
                            else:
                                if (self.launchers[launcher]["fanartpath"] == self.launchers[launcher]["rompath"] ):
                                    file_path = filename.replace("."+filename.split(".")[-1], img_ext)
                                else:
                                    file_path = os.path.join(os.path.dirname(self.launchers[launcher]["fanartpath"]),os.path.basename(filename.replace("."+filename.split(".")[-1], img_ext)))
                            if ( image != file_path ):
                                try:
                                    shutil.copy2( image.decode(get_encoding(),'ignore') , file_path.decode(get_encoding(),'ignore') )
                                    if ( self.launchers[launcher]["roms"][rom]["fanart"] != "" ):
                                        _update_cache(file_path)
                                    self.launchers[launcher]["roms"][rom]["fanart"] = file_path
                                    self._save_launchers()
                                    xbmc_notify('Advanced Emulator Launcher', 'Fanart has been updated',3000)
                                except OSError:
                                    xbmc_notify('Advanced Emulator Launcher', 'Impossible to assign fanart for %s' % self.launchers[launcher]["roms"][rom]["name"],3000)
            if (type2 == 2 ):
                # Link to a rom fanart image
                if (self.launchers[launcher]["roms"][rom]["fanart"] == ""):
                    imagepath = self.launchers[launcher]["roms"][rom]["filename"]
                else:
                    imagepath = self.launchers[launcher]["roms"][rom]["fanart"]
                image = xbmcgui.Dialog().browse(2,'Select fanart image',"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(imagepath))
                if (image):
                    if (os.path.isfile(image)):
                        if ( self.launchers[launcher]["roms"][rom]["fanart"] != "" ):
                            _update_cache(image)
                        self.launchers[launcher]["roms"][rom]["fanart"] = image
                        self._save_launchers()
                        xbmc_notify('Advanced Emulator Launcher', 'Fanart has been updated',3000)

        if (type == 4 ):
            if (self.launchers[launcher]["roms"][rom]["finished"] != "true"):
                self.launchers[launcher]["roms"][rom]["finished"] = "true"
            else:
                self.launchers[launcher]["roms"][rom]["finished"] = "false"
            self._save_launchers()

        if (type == 5 ):
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Advanced Modifications', ['Change File : %s' % self.launchers[launcher]["roms"][rom]["filename"], __language__( 30347 ) % self.launchers[launcher]["roms"][rom]["altapp"], __language__( 30348 ) % self.launchers[launcher]["roms"][rom]["altarg"], __language__( 30341 ) % self.launchers[launcher]["roms"][rom]["trailer"], __language__( 30331 ) % self.launchers[launcher]["roms"][rom]["custom"]])
            if (type2 == 0 ):
                # Selection of the item file
                item_file = xbmcgui.Dialog().browse(1,__language__( 30017 ),"files","."+self.launchers[launcher]["romext"].replace("|","|."), False, False, self.launchers[launcher]["roms"][rom]["filename"])
                self.launchers[launcher]["roms"][rom]["filename"] = item_file
                self._save_launchers()
            if (type2 == 1 ):
            # Launcher application path menu option
                if (os.environ.get( "OS", "xbox" ) == "xbox"):
                    filter = ".xbe|.cut"
                else:
                    if (sys.platform == "win32"):
                        filter = ".bat|.exe|.cmd|.lnk"
                    else:
                        filter = ""
                app = xbmcgui.Dialog().browse(1,__language__( 30023 ),"files",filter, False, False, self.launchers[launcher]["roms"][rom]["altapp"])
                self.launchers[launcher]["roms"][rom]["altapp"] = app
                self._save_launchers()
            # Edition of the launcher arguments
            if (type2 == 2 ):
                keyboard = xbmc.Keyboard(self.launchers[launcher]["roms"][rom]["altarg"], __language__( 30052 ))
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    self.launchers[launcher]["roms"][rom]["altarg"] = keyboard.getText()
                    self._save_launchers()
            if (type2 == 3 ):
                # Selection of the rom trailer file
                trailer = xbmcgui.Dialog().browse(1,'Select Trailer file',"files",".mp4|.mpg|.avi|.wmv|.mkv|.flv", False, False, self.launchers[launcher]["roms"][rom]["trailer"])
                self.launchers[launcher]["roms"][rom]["trailer"] = trailer
                self._save_launchers()
            if (type2 == 4 ):
                # Selection of the rom customs path
                custom = xbmcgui.Dialog().browse(0,__language__( 30057 ),"files","", False, False, self.launchers[launcher]["roms"][rom]["custom"])
                self.launchers[launcher]["roms"][rom]["custom"] = custom
                self._save_launchers()

        if type == 6:
            self._remove_rom(launcher, rom)

        # Return to the launcher directory
        xbmc.executebuiltin("Container.Refresh")

    def _scrap_thumb_rom_algo(self, launcher, rom, title):
        xbmc_notify('Advanced Emulator Launcher', __language__( 30065 ) % (self.launchers[launcher]["roms"][rom]["name"],(self.settings[ "thumbs_scraper" ]).encode('utf-8','ignore')),300000)
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        covers = self._get_thumbnails_list(self.launchers[launcher]["roms"][rom]["gamesys"],title,self.settings["game_region"],self.settings[ "thumb_image_size" ])
        if covers:
            nb_images = len(covers)
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
            xbmc_notify('Advanced Emulator Launcher', __language__( 30066 ) % (nb_images,self.launchers[launcher]["roms"][rom]["name"]),3000)
            covers.insert(0,(self.launchers[launcher]["roms"][rom]["thumb"],self.launchers[launcher]["roms"][rom]["thumb"],__language__( 30068 )))
            self.image_url = MyDialog(covers)
            if ( self.image_url ):
                if (not self.image_url == self.launchers[launcher]["roms"][rom]["thumb"]):
                    img_url = self._get_thumbnail(self.image_url)
                    if ( img_url != '' ):
                        img_ext = os.path.splitext(img_url)[-1][0:4]
                        if ( img_ext != '' ):
                            filename = self.launchers[launcher]["roms"][rom]["filename"]
                            if (self.launchers[launcher]["thumbpath"] == self.launchers[launcher]["fanartpath"] ):
                                if (self.launchers[launcher]["thumbpath"] == self.launchers[launcher]["rompath"] ):
                                    file_path = filename.replace("."+filename.split(".")[-1], '_thumb'+img_ext)
                                else:
                                    file_path = os.path.join(os.path.dirname(self.launchers[launcher]["thumbpath"]),os.path.basename(filename.replace("."+filename.split(".")[-1], '_thumb'+img_ext)))
                            else:
                                if (self.launchers[launcher]["thumbpath"] == self.launchers[launcher]["rompath"] ):
                                    file_path = filename.replace("."+filename.split(".")[-1], img_ext)
                                else:
                                    file_path = os.path.join(os.path.dirname(self.launchers[launcher]["thumbpath"]),os.path.basename(filename.replace("."+filename.split(".")[-1], img_ext)))
                            xbmc_notify('Advanced Emulator Launcher', __language__( 30069 ),300000)
                            try:
                                download_img(img_url,file_path)
                                req = urllib2.Request(img_url)
                                req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
                                f = open(file_path,'wb')
                                f.write(urllib2.urlopen(req).read())
                                f.close()                                
                                if ( self.launchers[launcher]["roms"][rom]["thumb"] != "" ):
                                    _update_cache(file_path)
                                self.launchers[launcher]["roms"][rom]["thumb"] = file_path
                                self._save_launchers()
                                xbmc_notify('Advanced Emulator Launcher', 'Thumb has been updated',3000)
                            except socket.timeout:
                                xbmc_notify('Advanced Emulator Launcher', __language__( 30081 ),3000)
                            except exceptions.IOError:
                                xbmc_notify('Advanced Emulator Launcher', 'Impossible to assign thumb for %s' % self.launchers[launcher]["roms"][rom]["name"],3000)
                    else:
                        xbmc_notify('Advanced Emulator Launcher', __language__( 30067 ) % (self.launchers[launcher]["roms"][rom]["name"]),3000)
        else:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
            xbmc_notify('Advanced Emulator Launcher', __language__( 30067 ) % (self.launchers[launcher]["roms"][rom]["name"]),3000)

    def _scrap_thumb_rom(self, launcher, rom):
        if ( self.launchers[launcher]["application"].lower().find('mame') > 0 ) or ( self.settings[ "thumbs_scraper" ] == 'arcadeHITS' ):
            title=os.path.basename(self.launchers[launcher]["roms"][rom]["filename"]).split(".")[0]
            keyboard = xbmc.Keyboard(title, __language__( 30079 ))
        else:
            keyboard = xbmc.Keyboard(self.launchers[launcher]["roms"][rom]["name"], __language__( 30036 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            self._scrap_thumb_rom_algo(launcher, rom, keyboard.getText())
        xbmc.executebuiltin("Container.Update")

    def _scrap_thumb_launcher_algo(self, launcherID, title):
        xbmc_notify('Advanced Emulator Launcher', __language__( 30065 ) % (self.launchers[launcherID]["name"],(self.settings[ "thumbs_scraper" ]).encode('utf-8','ignore')),30000)
        covers = self._get_thumbnails_list(self.launchers[launcherID]["gamesys"],title,self.settings["game_region"],self.settings[ "thumb_image_size" ])
        if covers:
            nb_images = len(covers)
            xbmc_notify('Advanced Emulator Launcher', __language__( 30066 ) % (nb_images,self.launchers[launcherID]["name"]),3000)
            covers.insert(0,(self.launchers[launcherID]["thumb"],self.launchers[launcherID]["thumb"],__language__( 30068 )))
            self.image_url = MyDialog(covers)
            if ( self.image_url ):
                if (not self.image_url == self.launchers[launcherID]["thumb"]):
                    img_url = self._get_thumbnail(self.image_url)
                    if ( img_url != '' ):
                        img_ext = os.path.splitext(img_url)[-1][0:4]
                        if ( img_ext != '' ):
                            filename = self.launchers[launcherID]["application"]
                            if ( os.path.join(self.launchers[launcherID]["thumbpath"]) != "" ):
                                file_path = os.path.join(self.launchers[launcherID]["thumbpath"],os.path.basename(self.launchers[launcherID]["application"])+'_thumb'+img_ext)
                            else:
                                if (self.settings[ "launcher_thumb_path" ] == "" ):
                                    self.settings[ "launcher_thumb_path" ] = DEFAULT_THUMB_PATH
                                file_path = os.path.join(self.settings[ "launcher_thumb_path" ],os.path.basename(self.launchers[launcherID]["application"])+'_thumb'+img_ext)
                            xbmc_notify('Advanced Emulator Launcher', __language__( 30069 ),300000)
                            try:
                                download_img(img_url,file_path)
                                if ( self.launchers[launcherID]["thumb"] != "" ):
                                    _update_cache(file_path)
                                self.launchers[launcherID]["thumb"] = file_path
                                self._save_launchers()
                                xbmc_notify('Advanced Emulator Launcher', 'Thumb has been updated',3000)
                            except socket.timeout:
                                xbmc_notify('Advanced Emulator Launcher', __language__( 30081 ),3000)
                            except exceptions.IOError:
                                xbmc_notify('Advanced Emulator Launcher', 'Impossible to assign thumb for %s' % self.launchers[launcherID]["name"],3000)
                    else:
                        xbmc_notify('Advanced Emulator Launcher', __language__( 30067 ) % (self.launchers[launcherID]["name"]),3000)
        else:
            xbmc_notify('Advanced Emulator Launcher', __language__( 30067 ) % (self.launchers[launcherID]["name"]),3000)

    def _scrap_thumb_category_algo(self, categoryID, title):
        xbmc_notify('Advanced Emulator Launcher', __language__( 30065 ) % (self.categories[categoryID]["name"],(self.settings[ "thumbs_scraper" ]).encode('utf-8','ignore')),300000)
        covers = self._get_thumbnails_list("",title,"",self.settings[ "thumb_image_size" ])
        if covers:
            nb_images = len(covers)
            xbmc_notify('Advanced Emulator Launcher', __language__( 30066 ) % (nb_images,self.categories[categoryID]["name"]),3000)
            covers.insert(0,(self.categories[categoryID]["thumb"],self.categories[categoryID]["thumb"],__language__( 30068 )))
            self.image_url = MyDialog(covers)
            if ( self.image_url ):
                if (not self.image_url == self.categories[categoryID]["thumb"]):
                    img_url = self._get_thumbnail(self.image_url)
                    if ( img_url != '' ):
                        img_ext = os.path.splitext(img_url)[-1][0:4]
                        if ( img_ext != '' ):
                            filename = self.categories[categoryID]["name"]
                            file_path = os.path.join(DEFAULT_THUMB_PATH,os.path.basename(self.categories[categoryID]["name"])+'_thumb'+img_ext)
                            xbmc_notify('Advanced Emulator Launcher', __language__( 30069 ),300000)
                            try:
                                download_img(img_url,file_path)
                                if ( self.categories[categoryID]["thumb"] != "" ):
                                    _update_cache(file_path)
                                self.categories[categoryID]["thumb"] = file_path
                                self._save_launchers()
                                xbmc_notify('Advanced Emulator Launcher', 'Thumb has been updated',3000)
                            except socket.timeout:
                                xbmc_notify('Advanced Emulator Launcher', __language__( 30081 ),3000)
                            except exceptions.IOError:
                                xbmc_notify('Advanced Emulator Launcher', 'Impossible to assign thumb for %s' % self.categories[categoryID]["name"],3000)
                    else:
                        xbmc_notify('Advanced Emulator Launcher', __language__( 30067 ) % (self.categories[categoryID]["name"]),3000)
        else:
            xbmc_notify('Advanced Emulator Launcher', __language__( 30067 ) % (self.categories[categoryID]["name"]),3000)

    def _scrap_thumb_launcher(self, launcherID):
        keyboard = xbmc.Keyboard(self.launchers[launcherID]["name"], __language__( 30036 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            self._scrap_thumb_launcher_algo(launcherID, keyboard.getText())
        xbmc.executebuiltin("Container.Update")

    def _scrap_thumb_category(self, categoryID):
        keyboard = xbmc.Keyboard(self.categories[categoryID]["name"], __language__( 30036 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            self._scrap_thumb_category_algo(categoryID, keyboard.getText())
        xbmc.executebuiltin("Container.Update")

    def _scrap_fanart_rom_algo(self, launcher, rom, title):
        xbmc_notify('Advanced Emulator Launcher', __language__( 30071 ) % (self.launchers[launcher]["roms"][rom]["name"],self.settings[ "fanarts_scraper" ].encode('utf-8','ignore')),300000)
        full_fanarts = self._get_fanarts_list(self.launchers[launcher]["roms"][rom]["gamesys"],title,self.settings[ "fanart_image_size" ])
        if full_fanarts:
            nb_images = len(full_fanarts)
            xbmc_notify('Advanced Emulator Launcher', __language__( 30072 ) % (nb_images,self.launchers[launcher]["roms"][rom]["name"]),3000)
            full_fanarts.insert(0,(self.launchers[launcher]["roms"][rom]["fanart"],self.launchers[launcher]["roms"][rom]["fanart"],__language__( 30068 )))
            self.image_url = MyDialog(full_fanarts)
            if ( self.image_url ):
                if (not self.image_url == self.launchers[launcher]["roms"][rom]["fanart"]):
                    img_url = self._get_fanart(self.image_url)
                    if ( img_url != '' ):
                        img_ext = os.path.splitext(img_url)[-1][0:4]
                        if ( img_ext != '' ):
                            filename = self.launchers[launcher]["roms"][rom]["filename"]
                            if (self.launchers[launcher]["fanartpath"] == self.launchers[launcher]["thumbpath"] ):
                                if (self.launchers[launcher]["fanartpath"] == self.launchers[launcher]["rompath"] ):
                                    file_path = filename.replace("."+filename.split(".")[-1], '_fanart'+img_ext)
                                else:
                                    file_path = os.path.join(os.path.dirname(self.launchers[launcher]["fanartpath"]),os.path.basename(filename.replace("."+filename.split(".")[-1], '_fanart'+img_ext)))
                            else:
                                if (self.launchers[launcher]["fanartpath"] == self.launchers[launcher]["rompath"] ):
                                    file_path = filename.replace("."+filename.split(".")[-1], img_ext)
                                else:
                                    file_path = os.path.join(os.path.dirname(self.launchers[launcher]["fanartpath"]),os.path.basename(filename.replace("."+filename.split(".")[-1], img_ext)))
                            xbmc_notify('Advanced Emulator Launcher', __language__( 30074 ),300000)
                            try:
                                download_img(img_url,file_path)
                                if ( self.launchers[launcher]["roms"][rom]["fanart"] != "" ):
                                    _update_cache(file_path)
                                self.launchers[launcher]["roms"][rom]["fanart"] = file_path
                                self._save_launchers()
                                xbmc_notify('Advanced Emulator Launcher', 'Fanart has been updated',3000)
                            except socket.timeout:
                                xbmc_notify('Advanced Emulator Launcher', __language__( 30081 ),3000)
                            except exceptions.IOError:
                                xbmc_notify('Advanced Emulator Launcher', 'Impossible to assign fanart for %s' % self.launchers[launcher]["roms"][rom]["name"],3000)
                    else:
                        xbmc_notify('Advanced Emulator Launcher', __language__( 30073 ) % (self.launchers[launcher]["roms"][rom]["name"]),3000)
        else:
            xbmc_notify('Advanced Emulator Launcher', __language__( 30073 ) % (self.launchers[launcher]["roms"][rom]["name"]),3000)

    def _scrap_fanart_category_algo(self, categoryID, title):
        xbmc_notify('Advanced Emulator Launcher', __language__( 30071 ) % (self.categories[categoryID]["name"],(self.settings[ "fanarts_scraper" ]).encode('utf-8','ignore')),300000)
        covers = self._get_fanarts_list("",title,self.settings[ "fanart_image_size" ])
        if covers:
            nb_images = len(covers)
            xbmc_notify('Advanced Emulator Launcher', __language__( 30072 ) % (nb_images,self.categories[categoryID]["name"]),3000)
            covers.insert(0,(self.categories[categoryID]["fanart"],self.categories[categoryID]["fanart"],__language__( 30068 )))
            self.image_url = MyDialog(covers)
            if ( self.image_url ):
                if (not self.image_url == self.categories[categoryID]["fanart"]):
                    img_url = self._get_fanart(self.image_url)
                    if ( img_url != '' ):
                        img_ext = os.path.splitext(img_url)[-1][0:4]
                        if ( img_ext != '' ):
                            filename = self.categories[categoryID]["name"]
                            file_path = os.path.join(DEFAULT_FANART_PATH,os.path.basename(self.categories[categoryID]["name"])+'_fanart'+img_ext)
                            xbmc_notify('Advanced Emulator Launcher', __language__( 30074 ),300000)
                            try:
                                download_img(img_url,file_path)
                                if ( self.categories[categoryID]["fanart"] != "" ):
                                    _update_cache(file_path)
                                self.categories[categoryID]["fanart"] = file_path
                                self._save_launchers()
                                xbmc_notify('Advanced Emulator Launcher', 'Fanart has been updated',3000)
                            except socket.timeout:
                                xbmc_notify('Advanced Emulator Launcher', __language__( 30081 ),3000)
                            except exceptions.IOError:
                                xbmc_notify('Advanced Emulator Launcher', 'Impossible to assign fanart for %s' % self.categories[categoryID]["name"],3000)
                    else:
                        xbmc_notify('Advanced Emulator Launcher', __language__( 30073 ) % (self.categories[categoryID]["name"]),3000)
        else:
            xbmc_notify('Advanced Emulator Launcher', __language__( 30073 ) % (self.categories[categoryID]["name"]),3000)

    def _scrap_fanart_rom(self, launcher, rom):
        if ( self.launchers[launcher]["application"].lower().find('mame') > 0 ) or ( self.settings[ "fanarts_scraper" ] == 'arcadeHITS' ):
            title=os.path.basename(self.launchers[launcher]["roms"][rom]["filename"]).split(".")[0]
            keyboard = xbmc.Keyboard(title, __language__( 30079 ))
        else:
            keyboard = xbmc.Keyboard(self.launchers[launcher]["roms"][rom]["name"], __language__( 30036 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            self._scrap_fanart_rom_algo(launcher, rom, keyboard.getText())
        xbmc.executebuiltin("Container.Update")

    def _scrap_fanart_launcher_algo(self, launcherID, title):
        xbmc_notify('Advanced Emulator Launcher', __language__( 30071 ) % (self.launchers[launcherID]["name"],(self.settings[ "fanarts_scraper" ]).encode('utf-8','ignore')),300000)
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        covers = self._get_fanarts_list(self.launchers[launcherID]["gamesys"],title,self.settings[ "fanart_image_size" ])
        if covers:
            nb_images = len(covers)
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
            xbmc_notify('Advanced Emulator Launcher', __language__( 30072 ) % (nb_images,self.launchers[launcherID]["name"]),3000)
            covers.insert(0,(self.launchers[launcherID]["fanart"],self.launchers[launcherID]["fanart"],__language__( 30068 )))
            self.image_url = MyDialog(covers)
            if ( self.image_url ):
                if (not self.image_url == self.launchers[launcherID]["fanart"]):
                    img_url = self._get_fanart(self.image_url)
                    if ( img_url != '' ):
                        img_ext = os.path.splitext(img_url)[-1][0:4]
                        if ( img_ext != '' ):
                            filename = self.launchers[launcherID]["application"]
                            if ( os.path.join(self.launchers[launcherID]["fanartpath"]) != "" ):
                                file_path = os.path.join(self.launchers[launcherID]["fanartpath"],os.path.basename(self.launchers[launcherID]["application"])+'_fanart'+img_ext)
                            else:
                                if (self.settings[ "launcher_fanart_path" ] == "" ):
                                    self.settings[ "launcher_fanart_path" ] = DEFAULT_FANART_PATH
                                file_path = os.path.join(self.settings[ "launcher_fanart_path" ],os.path.basename(self.launchers[launcherID]["application"])+'_fanart'+img_ext)
                            xbmc_notify('Advanced Emulator Launcher', __language__( 30074 ),300000)
                            try:
                                download_img(img_url,file_path)
                                if ( self.launchers[launcherID]["fanart"] != "" ):
                                    _update_cache(file_path)
                                self.launchers[launcherID]["fanart"] = file_path
                                self._save_launchers()
                                xbmc_notify('Advanced Emulator Launcher', 'Fanart has been updated',3000)
                            except socket.timeout:
                                xbmc_notify('Advanced Emulator Launcher', __language__( 30081 ),3000)
                            except exceptions.IOError:
                                xbmc_notify('Advanced Emulator Launcher', 'Impossible to assign fanart for %s' % self.launchers[launcherID]["name"],3000)
                    else:
                        xbmc_notify('Advanced Emulator Launcher', __language__( 30073 ) % (self.launchers[launcherID]["name"]),3000)
        else:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
            xbmc_notify('Advanced Emulator Launcher', __language__( 30073 ) % (self.launchers[launcherID]["name"]),3000)

    def _scrap_fanart_launcher(self, launcherID):
        keyboard = xbmc.Keyboard(self.launchers[launcherID]["name"], __language__( 30036 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            self._scrap_fanart_launcher_algo(launcherID, keyboard.getText())
        xbmc.executebuiltin("Container.Update")

    def _scrap_fanart_category(self, categoryID):
        keyboard = xbmc.Keyboard(self.categories[categoryID]["name"], __language__( 30036 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            self._scrap_fanart_category_algo(categoryID, keyboard.getText())
        xbmc.executebuiltin("Container.Update")

    def _scrap_rom_algo(self, launcher, rom, title):
        # Search game title
            results,display = self._get_games_list(title)
            if display:
                # Display corresponding game list found
                dialog = xbmcgui.Dialog()
                # Game selection
                selectgame = dialog.select('Select a item from %s' % ( self.settings[ "datas_scraper" ] ), display)
                if (not selectgame == -1):
                    if ( self.settings[ "ignore_title" ] ):
                        self.launchers[launcher]["roms"][rom]["name"] = title_format(self,title)
                    else:
                        self.launchers[launcher]["roms"][rom]["name"] = title_format(self,results[selectgame]["title"])
                    gamedata = self._get_game_data(results[selectgame]["id"])
                    self.launchers[launcher]["roms"][rom]["genre"] = gamedata["genre"]
                    self.launchers[launcher]["roms"][rom]["release"] = gamedata["release"]
                    self.launchers[launcher]["roms"][rom]["studio"] = gamedata["studio"]
                    self.launchers[launcher]["roms"][rom]["plot"] = gamedata["plot"]
            else:
                xbmc_notify('Advanced Emulator Launcher', __language__( 30076 ),3000)
    
    def _scrap_rom(self, launcher, rom):
        # Edition of the rom name
        title=os.path.basename(self.launchers[launcher]["roms"][rom]["filename"]).split(".")[0]
        if ( self.launchers[launcher]["application"].lower().find('mame') > 0 ) or ( self.settings[ "datas_scraper" ] == 'arcadeHITS' ):
            keyboard = xbmc.Keyboard(title, __language__( 30079 ))
        else:
            keyboard = xbmc.Keyboard(self.launchers[launcher]["roms"][rom]["name"], __language__( 30036 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            self._scrap_rom_algo(launcher, rom, keyboard.getText())
            self._save_launchers()
        xbmc.executebuiltin("Container.Update")

    def _full_scrap_rom(self, launcher, rom):
        # Edition of the rom name
        title=os.path.basename(self.launchers[launcher]["roms"][rom]["filename"]).split(".")[0]
        if ( self.launchers[launcher]["application"].lower().find('mame') > 0 ) or ( self.settings[ "datas_scraper" ] == 'arcadeHITS' ):
            keyboard = xbmc.Keyboard(title, __language__( 30079 ))
        else:
            keyboard = xbmc.Keyboard(self.launchers[launcher]["roms"][rom]["name"], __language__( 30036 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            self._scrap_rom_algo(launcher, rom, keyboard.getText())
            self._scrap_thumb_rom_algo(launcher, rom, keyboard.getText())
            self._scrap_fanart_rom_algo(launcher, rom, keyboard.getText())
            self._save_launchers()
            xbmc.executebuiltin("Container.Update")

    #
    # Add ROMS to launcher
    #
    def _command_add_roms(self, launcher):
        dialog = xbmcgui.Dialog()
        type = dialog.select('Add/Update Items', ['Scan for New Items', 'Manually Add Item'])
        if type == 0:
            self._roms_import_roms(launcher)
        if type == 1:
            self._roms_add_new_rom(launcher)

        # Return to the launcher directory
        xbmc.executebuiltin("Container.Refresh")

    #
    # Removes a category.
    # Also removes all launchers in this category!
    #
    def _gui_remove_category(self, categoryID):
        dialog = xbmcgui.Dialog()
        launcher_list = []
        for launcherID in sorted(self.launchers.iterkeys()):
            if self.launchers[launcherID]['category'] == categoryID:
                launcher_list.append(launcherID)
        if len(launcher_list) > 0:
            ret = dialog.yesno('AEL', 
                               'Category "%s" contains %s launchers.' % (self.categories[categoryID]["name"], len(launcher_list)),
                               'Deleting "%s" will also delete related launchers.' % self.categories[categoryID]["name"],
                               'Are you sure you want to delete "%s" ?' % self.categories[categoryID]["name"])
            if ret:
                for launcherID in launcher_list:
                    self.launchers.pop(launcherID)
                self.categories.pop(categoryID)
                self._fs_write_catfile()
        else:
            ret = dialog.yesno('AEL',
                               'Category "%s" contains %s launchers.' % (self.categories[categoryID]["name"], len(launcher_list)),
                               'Are you sure you want to delete "%s" ?' % self.categories[categoryID]["name"])
            if ret:
                self.categories.pop(categoryID)
                self._fs_write_catfile()
        xbmc.executebuiltin("Container.Update")

    def _gui_edit_category_metadata(self, categoryID):
        dialog = xbmcgui.Dialog()
        type2 = dialog.select('Edit Category Metadata', 
                              ['Edit Title: "%s"' % self.categories[categoryID]["name"],
                               'Edit Genre: "%s"' % self.categories[categoryID]["genre"],
                               'Edit Description: "%s"' % self.categories[categoryID]["description"],
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
                self._fs_write_catfile()
            else:
                gui_kodi_dialog_OK('AEL Information', 
                                   'Category name "{0}" not changed.'.format(self.categories[categoryID]["name"]))
        # Edition of the category genre
        elif type2 == 1:
            keyboard = xbmc.Keyboard(self.categories[categoryID]["genre"], 'Edit Genre')
            keyboard.doModal()
            if keyboard.isConfirmed():
                self.categories[categoryID]["genre"] = keyboard.getText()
                self._fs_write_catfile()
            else:
                gui_kodi_dialog_OK('AEL Information', 
                                   'Category genre "{0}" not changed.'.format(self.categories[categoryID]["genre"]))
        # Edition of the plot (description)
        elif type2 == 2:
            keyboard = xbmc.Keyboard(self.categories[categoryID]["description"], 'Edit Description')
            keyboard.doModal()
            if keyboard.isConfirmed():
                self.categories[categoryID]["description"] = keyboard.getText()
                self._fs_write_catfile()
            else:
                gui_kodi_dialog_OK('AEL Information', 
                                   'Category plot "{0}" not changed.'.format(self.categories[categoryID]["description"]))
        # Import category description
        elif type2 == 3:
            text_file = xbmcgui.Dialog().browse(1, 'Select description file (txt|dat)', "files", ".txt|.dat", False, False)
            if os.path.isfile(text_file) == True:
                text_plot = open(text_file, 'rt')
                self.categories[categoryID]["description"] = text_plot.read()
                text_plot.close()
                self._fs_write_catfile()
            else:
                gui_kodi_dialog_OK('AEL Information', 
                                   'Category plot "{0}" not changed.'.format(self.categories[categoryID]["description"]))

    def _command_edit_category(self, categoryID):
        # Shows a select box with the options to edit
        dialog = xbmcgui.Dialog()
        if self.categories[categoryID]["finished"] == True: finished_display = 'Status: Finished'
        else:                                               finished_display = 'Status: Unfinished'
        type = dialog.select('Select action for category {0}'.format(self.categories[categoryID]["name"]), 
                             ['Edit Title/Genre/Description', 'Edit Thumbnail image', 'Edit Fanart image', 
                              finished_display, 'Delete category'])
        # Edit metadata
        if type == 0:
            self._gui_edit_category_metadata(categoryID)

        # Edit Thumbnail image
        elif type == 1:
            dialog = xbmcgui.Dialog()
            thumb_diag = 'Import Image from %s' % ( self.settings[ "thumbs_scraper" ] )
            if self.settings[ "thumbs_scraper" ] == "Google":
                thumb_diag = 'Import from %s : %s size' % ( self.settings[ "thumbs_scraper" ],
                             self.settings[ "thumb_image_size_display" ].capitalize())
            type2 = dialog.select('Change Thumbnail Image', 
                                  [thumb_diag, 'Import Local Image (Copy and Rename)',
                                   'Select Local Image (Link)'])
            # Scrape thumb
            if type2 == 0:
                self._scrap_thumb_category(categoryID)
            # Import a category thumbnail image
            elif type2 == 1:
                image = xbmcgui.Dialog().browse(2, 'Select thumbnail image', 
                                                "files", ".jpg|.jpeg|.gif|.png", True, False, DEFAULT_THUMB_PATH)
                if not image or not os.path.isfile(image):
                    return
                img_ext = os.path.splitext(image)[-1][0:4]
                if img_ext != '':
                    filename = self.categories[categoryID]["name"]
                    file_path = os.path.join(DEFAULT_THUMB_PATH, os.path.basename(self.categories[categoryID]["name"])+'_thumb'+img_ext)
                    if image != file_path:
                        try:
                            shutil.copy2( image.decode(get_encoding(),'ignore') , file_path.decode(get_encoding(),'ignore') )
                            if ( self.categories[categoryID]["thumb"] != "" ):
                                _update_cache(file_path)
                            self.categories[categoryID]["thumb"] = file_path
                            self._save_launchers()
                            xbmc_notify('AEL', 'Thumb has been updated', 3000)
                        except OSError:
                            xbmc_notify('AEL', 'Impossible to assign thumb for %s' % self.categories[categoryID]["name"], 3000)
            # Link to a category thumbnail image
            elif type2 == 2:
                if self.categories[categoryID]["thumb"] == "":
                    imagepath = DEFAULT_THUMB_PATH
                else:
                    imagepath = self.categories[categoryID]["thumb"]
                image = xbmcgui.Dialog().browse(2, 'Select thumbnail image', 
                                                "files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(imagepath))
                if image:
                    if os.path.isfile(image):
                        if self.categories[categoryID]["thumb"] != "":
                            _update_cache(image)
                        self.categories[categoryID]["thumb"] = image
                        self._save_launchers()
                        xbmc_notify('AEL', 'Thumb has been updated', 3000)

        # Launcher Fanart menu option
        elif type == 2:
            dialog = xbmcgui.Dialog()
            fanart_diag = 'Import Image from %s' % ( self.settings[ "fanarts_scraper" ] )
            if ( self.settings[ "fanarts_scraper" ] == "Google" ):
                fanart_diag = 'Import from %s : %s size' % ( self.settings[ "fanarts_scraper" ],self.settings[ "fanart_image_size_display" ].capitalize())
            type2 = dialog.select('Change Fanart Image', [fanart_diag,'Import Local Image (Copy and Rename)','Select Local Image (Link)'])
            if (type2 == 0 ):
                self._scrap_fanart_category(categoryID)
            if (type2 == 1 ):
                # Import a Category fanart image
                image = xbmcgui.Dialog().browse(2,'Select fanart image',"files",".jpg|.jpeg|.gif|.png", True, False, DEFAULT_FANART_PATH)
                if (image):
                    if (os.path.isfile(image)):
                        img_ext = os.path.splitext(image)[-1][0:4]
                        if ( img_ext != '' ):
                            filename = self.categories[categoryID]["name"]
                            file_path = os.path.join(DEFAULT_FANART_PATH,os.path.basename(self.categories[categoryID]["name"])+'_fanart'+img_ext)
                            if ( image != file_path ):
                                try:
                                    shutil.copy2( image.decode(get_encoding(),'ignore') , file_path.decode(get_encoding(),'ignore') )
                                    if ( self.categories[categoryID]["fanart"] != "" ):
                                        _update_cache(file_path)
                                    self.categories[categoryID]["fanart"] = file_path
                                    self._save_launchers()
                                    xbmc_notify('Advanced Emulator Launcher', 'Fanart has been updated',3000)
                                except OSError:
                                    xbmc_notify('Advanced Emulator Launcher', 'Impossible to assign fanart for %s' % self.categories[categoryID]["name"],3000)
            if (type2 == 2 ):
                # Link to a category fanart image
                if (self.categories[categoryID]["fanart"] == ""):
                    imagepath = DEFAULT_FANART_PATH
                else:
                    imagepath = self.categories[categoryID]["fanart"]
                image = xbmcgui.Dialog().browse(2,'Select fanart image',"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(imagepath))
                if (image):
                    if (os.path.isfile(image)):
                        if ( self.categories[categoryID]["fanart"] != "" ):
                            _update_cache(image)
                        self.categories[categoryID]["fanart"] = image
                        self._save_launchers()
                        xbmc_notify('Advanced Emulator Launcher', 'Fanart has been updated',3000)

        # Category status
        elif type == 3:
            finished = self.categories[categoryID]["finished"]
            finished = False if finished else True
            finished_display = 'Finished' if finished == True else 'Unfinished'
            self.categories[categoryID]["finished"] = finished
            self._fs_write_catfile()
            gui_kodi_dialog_OK('AEL Information', 
                               'Category Status is now {0}'.format(finished_display))
        elif type == 4:
            self._gui_remove_category(categoryID)

        elif type == -1:
            self._fs_write_catfile()

        # Return to the category directory
        xbmc.executebuiltin("Container.Refresh")

    def _gui_empty_launcher(self, launcherID):
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno('Advanced Emulator Launcher', __language__( 30133 ) % self.launchers[launcherID]["name"])
        if (ret):
            self.launchers[launcherID]["roms"].clear()
            self._save_launchers()
            xbmc.executebuiltin("Container.Update")

    def _gui_remove_launcher(self, launcherID):
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno('Advanced Emulator Launcher', __language__( 30010 ) % self.launchers[launcherID]["name"])
        if (ret):
            category = self.launchers[launcherID]["category"]
            self.launchers.pop(launcherID)
            self._save_launchers()
            if ( not self._empty_cat(category) ):
                xbmc.executebuiltin("Container.Update")
            else:
                xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._path))

    def _command_edit_launcher(self, launcherID):
        dialog = xbmcgui.Dialog()
        title = os.path.basename(self.launchers[launcherID]["name"])
        finished_display = 'Status : Finished' if self.launchers[launcherID]["finished"] == True else 'Status : Unfinished'

        if self.launchers[launcherID]["rompath"] == "":
            type = dialog.select('Select Action for %s' % title, 
                                 ['Import Metadata, Thumbnail and Fanart', 'Modify Metadata',
                                  'Change Thumbnail Image', 'Change Fanart Image', 
                                  'Change Category: %s' % self.categories[self.launchers[launcherID]["category"]]['name'],
                                  finished_display, 
                                  'Advanced Modifications', 'Delete'])
        else:
            type = dialog.select('Select Action for %s' % title, 
                                 ['Import Metadata, Thumbnail and Fanart', 'Modify Metadata',
                                  'Change Thumbnail Image', 'Change Fanart Image',
                                  'Change Category: %s' % self.categories[self.launchers[launcherID]["category"]]['name'],
                                  finished_display, 
                                  'Manage Items List', 'Advanced Modifications', 'Delete'])
        type_nb = 0

        # Scrap item (infos and images)
        if type == type_nb:
            self._full_scrap_launcher(launcherID)

        # Edition of the launcher metadata
        type_nb = type_nb + 1
        if type == type_nb:
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Modify Launcher Metadata',
                                  ['Import from %s' % self.settings[ "datas_scraper" ],
                                   'Modify Title : %s' % self.launchers[launcherID]["name"],
                                   'Modify Platform : %s' % self.launchers[launcherID]["gamesys"],
                                   'Modify Release Date : %s' % self.launchers[launcherID]["release"],
                                   'Modify Studio : %s' % self.launchers[launcherID]["studio"],
                                   'Modify Genre : %s' % self.launchers[launcherID]["genre"],
                                   'Modify Description : %s ...' % self.launchers[launcherID]["plot"][0:20],
                                   'Import from .nfo file', 'Save to .nfo file'])
            if type2 == 0:   # Edition of the launcher name
                self._scrap_launcher(launcherID)
            elif type2 == 1: # Edition of the launcher name
                
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["name"], 'Edit title')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    title = keyboard.getText()
                    if title == "" :
                        title = self.launchers[launcherID]["name"]
                    self.launchers[launcherID]["name"] = title.rstrip()
                    self._save_launchers()
            elif type2 == 2: # Selection of the launcher game system
                
                dialog = xbmcgui.Dialog()
                platforms = _get_game_system_list()
                gamesystem = dialog.select('Select the platform', platforms)
                if not gamesystem == -1:
                    self.launchers[launcherID]["gamesys"] = platforms[gamesystem]
                    self._save_launchers()
            elif type2 == 3:
                # Edition of the launcher release date
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["release"], 'Edit release year')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    self.launchers[launcherID]["release"] = keyboard.getText()
                    self._save_launchers()
            elif type2 == 4:
                # Edition of the launcher studio name
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["studio"], 'Edit studio')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    self.launchers[launcherID]["studio"] = keyboard.getText()
                    self._save_launchers()
            elif type2 == 5:
                # Edition of the launcher genre
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["genre"], 'Edit genre')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    self.launchers[launcherID]["genre"] = keyboard.getText()
                    self._save_launchers()
            elif type2 == 6:
                # Import of the launcher plot
                text_file = xbmcgui.Dialog().browse(1,
                                                    'Select description file. (e.g txt|dat)', "files", ".txt|.dat", 
                                                    False, False, self.launchers[launcherID]["application"])
                if os.path.isfile(text_file) == True:
                    text_plot = open(text_file, 'r')
                    self.launchers[launcherID]["plot"] = text_plot.read()
                    text_plot.close()
                    self._save_launchers()
            elif type2 == 7:
                # Edition of the launcher name
                self._import_launcher_nfo(launcherID)
            elif type2 == 8:
                # Edition of the launcher name
                self._export_launcher_nfo(launcherID)

        # Launcher Thumbnail menu option (VERY SIMILAR TO THE CATEGORIES STUFF, HAVE A LOOK THERE)
        type_nb = type_nb+1
        if (type == type_nb ):
            dialog = xbmcgui.Dialog()
            thumb_diag = 'Import Image from %s' % ( self.settings[ "thumbs_scraper" ] )
            if ( self.settings[ "thumbs_scraper" ] == "GameFAQs" ) | ( self.settings[ "thumbs_scraper" ] == "MobyGames" ):
                thumb_diag = 'Import from %s : %s thumbs' % ( self.settings[ "thumbs_scraper" ],self.settings[ "display_game_region" ])
            if ( self.settings[ "thumbs_scraper" ] == "Google" ):
                thumb_diag = 'Import from %s : %s size' % ( self.settings[ "thumbs_scraper" ],self.settings[ "thumb_image_size_display" ])
            type2 = dialog.select('Change Thumbnail Image', [thumb_diag,'Import Local Image (Copy and Rename)','Select Local Image (Link)'])
            if (type2 == 0 ):
                self._scrap_thumb_launcher(launcherID)
            if (type2 == 1 ):
                # Import a Launcher thumbnail image
                image = xbmcgui.Dialog().browse(2,'Select thumbnail image',"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(self.launchers[launcherID]["thumbpath"]))
                if (image):
                    if (os.path.isfile(image)):
                        img_ext = os.path.splitext(image)[-1][0:4]
                        if ( img_ext != '' ):
                            filename = self.launchers[launcherID]["application"]
                            if ( os.path.join(self.launchers[launcherID]["thumbpath"]) != "" ):
                                file_path = os.path.join(self.launchers[launcherID]["thumbpath"],os.path.basename(self.launchers[launcherID]["application"])+'_thumb'+img_ext)
                            else:
                                if (self.settings[ "launcher_thumb_path" ] == "" ):
                                    self.settings[ "launcher_thumb_path" ] = DEFAULT_THUMB_PATH
                                file_path = os.path.join(self.settings[ "launcher_thumb_path" ],os.path.basename(self.launchers[launcherID]["application"])+'_thumb'+img_ext)
                            if ( image != file_path ):
                                try:
                                    shutil.copy2( image.decode(get_encoding(),'ignore') , file_path.decode(get_encoding(),'ignore') )
                                    if ( self.launchers[launcherID]["thumb"] != "" ):
                                        _update_cache(file_path)
                                    self.launchers[launcherID]["thumb"] = file_path
                                    self._save_launchers()
                                    xbmc_notify('Advanced Emulator Launcher', 'Thumb has been updated',3000)
                                except OSError:
                                    xbmc_notify('Advanced Emulator Launcher', 'Impossible to assign thumb for %s' % self.launchers[launcherID]["name"],3000)

            if (type2 == 2 ):
                # Link to a launcher thumbnail image
                if (self.launchers[launcherID]["thumb"] == ""):
                    imagepath = self.launchers[launcherID]["thumbpath"]
                else:
                    imagepath = self.launchers[launcherID]["thumb"]
                image = xbmcgui.Dialog().browse(2,'Select thumbnail image',"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(imagepath))
                if (image):
                    if (os.path.isfile(image)):
                        if ( self.launchers[launcherID]["thumb"] != "" ):
                            _update_cache(image)
                        self.launchers[launcherID]["thumb"] = image
                        self._save_launchers()
                        xbmc_notify('Advanced Emulator Launcher', 'Thumb has been updated',3000)

        # Launcher Fanart menu option
        type_nb = type_nb+1
        if (type == type_nb ):
            dialog = xbmcgui.Dialog()
            fanart_diag = 'Import Image from %s' % ( self.settings[ "fanarts_scraper" ] )
            if ( self.settings[ "fanarts_scraper" ] == "Google" ):
                fanart_diag = 'Import from %s : %s size' % ( self.settings[ "fanarts_scraper" ],self.settings[ "fanart_image_size_display" ].capitalize())
            type2 = dialog.select('Change Fanart Image', [fanart_diag,'Import Local Image (Copy and Rename)','Select Local Image (Link)'])
            if (type2 == 0 ):
                self._scrap_fanart_launcher(launcherID)
            if (type2 == 1 ):
                # Import a Launcher fanart image
                image = xbmcgui.Dialog().browse(2,'Select fanart image',"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(self.launchers[launcherID]["fanartpath"]))
                if (image):
                    if (os.path.isfile(image)):
                        img_ext = os.path.splitext(image)[-1][0:4]
                        if ( img_ext != '' ):
                            filename = self.launchers[launcherID]["application"]
                            if ( os.path.join(self.launchers[launcherID]["fanartpath"]) != "" ):
                                file_path = os.path.join(self.launchers[launcherID]["fanartpath"],os.path.basename(self.launchers[launcherID]["application"])+'_fanart'+img_ext)
                            else:
                                if (self.settings[ "launcher_fanart_path" ] == "" ):
                                    self.settings[ "launcher_fanart_path" ] = DEFAULT_FANART_PATH
                                file_path = os.path.join(self.settings[ "launcher_fanart_path" ],os.path.basename(self.launchers[launcherID]["application"])+'_fanart'+img_ext)
                            if ( image != file_path ):
                                try:
                                    shutil.copy2( image.decode(get_encoding(),'ignore') , file_path.decode(get_encoding(),'ignore') )
                                    if ( self.launchers[launcherID]["fanart"] != "" ):
                                        _update_cache(file_path)
                                    self.launchers[launcherID]["fanart"] = file_path
                                    self._save_launchers()
                                    xbmc_notify('Advanced Emulator Launcher', 'Thumb has been updated',3000)
                                except OSError:
                                    xbmc_notify('Advanced Emulator Launcher', 'Impossible to assign fanart for %s' % self.launchers[launcherID]["name"],3000)
            if (type2 == 2 ):
                # Link to a launcher fanart image
                if (self.launchers[launcherID]["fanart"] == ""):
                    imagepath = self.launchers[launcherID]["fanartpath"]
                else:
                    imagepath = self.launchers[launcherID]["fanart"]
                image = xbmcgui.Dialog().browse(2,'Select fanart image',"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(imagepath))
                if (image):
                    if (os.path.isfile(image)):
                        if ( self.launchers[launcherID]["fanart"] != "" ):
                            _update_cache(image)
                        self.launchers[launcherID]["fanart"] = image
                        self._save_launchers()
                        xbmc_notify('Advanced Emulator Launcher', 'Fanart has been updated',3000)

        # Launcher's change category
        type_nb = type_nb+1
        if type == type_nb:
            current_category = self.launchers[launcherID]["category"]
            dialog = xbmcgui.Dialog()
            categories_id = []
            categories_name = []
            for key in self.categories:
                categories_id.append(self.categories[key]['id'])
                categories_name.append(self.categories[key]['name'])
            selected_cat = dialog.select('Select the category', categories_name)
            if (not selected_cat == -1 ):
                self.launchers[launcherID]["category"] = categories_id[selected_cat]
                self._save_launchers()
                xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self._path, categories_id[selected_cat]))

        # Launcher status
        type_nb = type_nb+1
        if type == type_nb:
            if (self.launchers[launcherID]["finished"] != "true"):
                self.launchers[launcherID]["finished"] = "true"
            else:
                self.launchers[launcherID]["finished"] = "false"
            self._save_launchers()

        # Launcher's Items List menu option
        if self.launchers[launcherID]["rompath"] != "" :
            type_nb = type_nb+1
            if (type == type_nb ):
                dialog = xbmcgui.Dialog()
                type2 = dialog.select(__language__( 30334 ), [__language__( 30335 ),__language__( 30336 ),__language__( 30318 ),])
                # Import Items list form .nfo files
                if (type2 == 0 ):
                    self._import_items_list_nfo(launcherID)
                # Export Items list to .nfo files
                if (type2 == 1 ):
                    self._export_items_list_nfo(launcherID)
                # Empty Launcher menu option
                if (type2 == 2 ):
                    self._empty_launcher(launcherID)

        # Launcher Advanced menu option
        type_nb = type_nb+1
        if type == type_nb:
            if self.launchers[launcherID]["minimize"] == "true":
                minimize_str = __language__( 30204 )
            else:
                minimize_str = __language__( 30205 )
            if self.launchers[launcherID]["lnk"] == "true":
                lnk_str = __language__( 30204 )
            else:
                lnk_str = __language__( 30205 )
            if (os.environ.get( "OS", "xbox" ) == "xbox"):
                filter = ".xbe|.cut"
            else:
                if (sys.platform == "win32"):
                    filter = ".bat|.exe|.cmd"
                else:
                    filter = ""
            if self.launchers[launcherID]["rompath"] != "":
                if (sys.platform == 'win32'):
                    type2 = dialog.select('Advanced Modifications', [__language__( 30327 ) % self.launchers[launcherID]["application"],__language__( 30315 ) % self.launchers[launcherID]["args"],__language__( 30324 ) % self.launchers[launcherID]["rompath"],__language__( 30317 ) % self.launchers[launcherID]["romext"],__language__( 30325 ) % self.launchers[launcherID]["thumbpath"], __language__( 30326 ) % self.launchers[launcherID]["fanartpath"], __language__( 30341 ) % self.launchers[launcherID]["trailerpath"], __language__( 30331 ) % self.launchers[launcherID]["custompath"],__language__( 30329 ) % minimize_str,__language__( 30330 ) % lnk_str])
                else:
                    type2 = dialog.select('Advanced Modifications', [__language__( 30327 ) % self.launchers[launcherID]["application"],__language__( 30315 ) % self.launchers[launcherID]["args"],__language__( 30324 ) % self.launchers[launcherID]["rompath"],__language__( 30317 ) % self.launchers[launcherID]["romext"],__language__( 30325 ) % self.launchers[launcherID]["thumbpath"], __language__( 30326 ) % self.launchers[launcherID]["fanartpath"], __language__( 30341 ) % self.launchers[launcherID]["trailerpath"], __language__( 30331 ) % self.launchers[launcherID]["custompath"],__language__( 30329 ) % minimize_str])
            else:
                if (sys.platform == 'win32'):
                    type2 = dialog.select('Advanced Modifications', [__language__( 30327 ) % self.launchers[launcherID]["application"],__language__( 30315 ) % self.launchers[launcherID]["args"],__language__( 30325 ) % self.launchers[launcherID]["thumbpath"], __language__( 30326 ) % self.launchers[launcherID]["fanartpath"], __language__( 30341 ) % self.launchers[launcherID]["trailerpath"], __language__( 30331 ) % self.launchers[launcherID]["custompath"],__language__( 30329 ) % minimize_str,__language__( 30330 ) % lnk_str])
                else:
                    type2 = dialog.select('Advanced Modifications', [__language__( 30327 ) % self.launchers[launcherID]["application"],__language__( 30315 ) % self.launchers[launcherID]["args"],__language__( 30325 ) % self.launchers[launcherID]["thumbpath"], __language__( 30326 ) % self.launchers[launcherID]["fanartpath"], __language__( 30341 ) % self.launchers[launcherID]["trailerpath"], __language__( 30331 ) % self.launchers[launcherID]["custompath"],__language__( 30329 ) % minimize_str])

            # Launcher application path menu option
            type2_nb = 0
            if type2 == type2_nb:
                app = xbmcgui.Dialog().browse(1,__language__( 30023 ),"files","", False, False, self.launchers[launcherID]["application"])
                self.launchers[launcherID]["application"] = app

            # Edition of the launcher arguments
            type2_nb = type2_nb +1
            if type2 == type2_nb:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["args"], __language__( 30052 ))
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    self.launchers[launcherID]["args"] = keyboard.getText()
                    self._save_launchers()

            if self.launchers[launcherID]["rompath"] != "":
                # Launcher roms path menu option
                type2_nb = type2_nb + 1
                if (type2 == type2_nb ):
                    rom_path = xbmcgui.Dialog().browse(0,__language__( 30058 ),"files", "", False, False, self.launchers[launcherID]["rompath"])
                    self.launchers[launcherID]["rompath"] = rom_path

                # Edition of the launcher rom extensions (only for emulator launcher)
                type2_nb = type2_nb +1
                if (type2 == type2_nb ):
                    if (not self.launchers[launcherID]["rompath"] == ""):
                        keyboard = xbmc.Keyboard(self.launchers[launcherID]["romext"], __language__( 30054 ))
                        keyboard.doModal()
                        if (keyboard.isConfirmed()):
                            self.launchers[launcherID]["romext"] = keyboard.getText()
                            self._save_launchers()

            # Launcher thumbnails path menu option
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                thumb_path = xbmcgui.Dialog().browse(0,__language__( 30059 ),"files","", False, False, self.launchers[launcherID]["thumbpath"])
                self.launchers[launcherID]["thumbpath"] = thumb_path
            # Launcher fanarts path menu option
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                fanart_path = xbmcgui.Dialog().browse(0,__language__( 30060 ),"files","", False, False, self.launchers[launcherID]["fanartpath"])
                self.launchers[launcherID]["fanartpath"] = fanart_path
            # Launcher trailer file menu option
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                fanart_path = xbmcgui.Dialog().browse(1,'Select Trailer file',"files",".mp4|.mpg|.avi|.wmv|.mkv|.flv", False, False, self.launchers[launcherID]["trailerpath"])
                self.launchers[launcherID]["trailerpath"] = fanart_path
            # Launcher custom path menu option
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                fanart_path = xbmcgui.Dialog().browse(0,__language__( 30057 ),"files","", False, False, self.launchers[launcherID]["custompath"])
                self.launchers[launcherID]["custompath"] = fanart_path
            # Launcher minimize state menu option
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                dialog = xbmcgui.Dialog()
                type3 = dialog.select(__language__( 30203 ), ["%s (%s)" % (__language__( 30205 ),__language__( 30201 )), "%s" % (__language__( 30204 ))])
                if (type3 == 1 ):
                    self.launchers[launcherID]["minimize"] = "true"
                else:
                    self.launchers[launcherID]["minimize"] = "false"
            self._save_launchers()
            # Launcher internal lnk option
            if sys.platform == 'win32':
                type2_nb = type2_nb + 1
                if (type2 == type2_nb ):
                    dialog = xbmcgui.Dialog()
                    type3 = dialog.select(__language__( 30206 ), ["%s (%s)" % (__language__( 30204 ),__language__( 30201 )), "%s (%s)" % (__language__( 30205 ),__language__( 30202 ))])
                    if (type3 == 1 ):
                        self.launchers[launcherID]["lnk"] = "false"
                    else:
                        self.launchers[launcherID]["lnk"] = "true"
            self._save_launchers()

        # Remove Launcher menu option
        type_nb = type_nb+1
        if type == type_nb:
            self._remove_launcher(launcherID)

        if type == -1:
            self._save_launchers()

        # Return to the launcher directory
        xbmc.executebuiltin("Container.Refresh")

    def _scrap_launcher_algo(self, launcherID, title):
        # Scrapping launcher name info
        results,display = self._get_games_list(title)
        if display:
            # Display corresponding game list found
            dialog = xbmcgui.Dialog()
            # Game selection
            selectgame = dialog.select('Select a item from %s' % ( self.settings[ "datas_scraper" ] ), display)
            if (not selectgame == -1):
                if ( self.settings[ "ignore_title" ] ):
                    self.launchers[launcherID]["name"] = title_format(self,self.launchers[launcherID]["name"])
                else:
                    self.launchers[launcherID]["name"] = title_format(self,results[selectgame]["title"])
                gamedata = self._get_game_data(results[selectgame]["id"])
                self.launchers[launcherID]["genre"] = gamedata["genre"]
                self.launchers[launcherID]["release"] = gamedata["release"]
                self.launchers[launcherID]["studio"] = gamedata["studio"]
                self.launchers[launcherID]["plot"] = gamedata["plot"]
        else:
            xbmc_notify('Advanced Emulator Launcher', __language__( 30076 ),3000)

    def _scrap_launcher(self, launcherID):
        # Edition of the launcher name
        keyboard = xbmc.Keyboard(self.launchers[launcherID]["name"], __language__( 30036 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            self._scrap_launcher_algo(launcherID, keyboard.getText())
            self._save_launchers()
            xbmc.executebuiltin("Container.Update")

    def _full_scrap_launcher(self, launcherID):
        # Edition of the launcher name
        keyboard = xbmc.Keyboard(self.launchers[launcherID]["name"], __language__( 30036 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            self._scrap_launcher_algo(launcherID, keyboard.getText())
            self._scrap_thumb_launcher_algo(launcherID, keyboard.getText())
            self._scrap_fanart_launcher_algo(launcherID, keyboard.getText())
            self._save_launchers()
            xbmc.executebuiltin("Container.Update")

    def _import_launcher_nfo(self, launcherID):
        if ( len(self.launchers[launcherID]["rompath"]) > 0 ):
            nfo_file = os.path.join(self.launchers[launcherID]["rompath"],os.path.basename(os.path.splitext(self.launchers[launcherID]["application"])[0]+".nfo"))
        else:
            if ( len(self.settings[ "launcher_nfo_path" ]) > 0 ):
                nfo_file = os.path.join(self.settings[ "launcher_nfo_path" ],os.path.basename(os.path.splitext(self.launchers[launcherID]["application"])[0]+".nfo"))
            else:
                nfo_file = xbmcgui.Dialog().browse(1,__language__( 30088 ),"files",".nfo", False, False)
        if (os.path.isfile(nfo_file)):
            f = open(nfo_file, 'r')
            item_nfo = f.read().replace('\r','').replace('\n','')
            item_title = re.findall( "<title>(.*?)</title>", item_nfo )
            item_platform = re.findall( "<platform>(.*?)</platform>", item_nfo )
            item_year = re.findall( "<year>(.*?)</year>", item_nfo )
            item_publisher = re.findall( "<publisher>(.*?)</publisher>", item_nfo )
            item_genre = re.findall( "<genre>(.*?)</genre>", item_nfo )
            item_plot = re.findall( "<plot>(.*?)</plot>", item_nfo )
            self.launchers[launcherID]["name"] = item_title[0].rstrip()
            self.launchers[launcherID]["gamesys"] = item_platform[0]
            self.launchers[launcherID]["release"] = item_year[0]
            self.launchers[launcherID]["studio"] = item_publisher[0]
            self.launchers[launcherID]["genre"] = item_genre[0]
            self.launchers[launcherID]["plot"] = item_plot[0].replace('&quot;','"')
            f.close()
            self._save_launchers()
            xbmc_notify('Advanced Emulator Launcher', __language__( 30083 ) % os.path.basename(nfo_file),3000)
        else:
            xbmc_notify('Advanced Emulator Launcher', __language__( 30082 ) % os.path.basename(nfo_file),3000)

    def _export_items_list_nfo(self, launcherID):
        for rom in self.launchers[launcherID]["roms"].iterkeys():
            self._export_rom_nfo(launcherID, rom)

    def _import_items_list_nfo(self, launcherID):
        for rom in self.launchers[launcherID]["roms"].iterkeys():
            self._import_rom_nfo(launcherID, rom)

    def _get_settings( self ):
        # get the users preference settings
        self.settings = {}
        self.settings["datas_method"]          = addon_obj.getSetting( "datas_method" )
        self.settings["thumbs_method"]         = addon_obj.getSetting( "thumbs_method" )
        self.settings["fanarts_method"]        = addon_obj.getSetting( "fanarts_method" )
        self.settings["scrap_info"]            = addon_obj.getSetting( "scrap_info" )
        self.settings["scrap_thumbs"]          = addon_obj.getSetting( "scrap_thumbs" )
        self.settings["scrap_fanarts"]         = addon_obj.getSetting( "scrap_fanarts" )
        self.settings["select_fanarts"]        = addon_obj.getSetting( "select_fanarts" )
        self.settings["overwrite_thumbs"]      = ( addon_obj.getSetting( "overwrite_thumbs" ) == "true" )
        self.settings["overwrite_fanarts"]     = ( addon_obj.getSetting( "overwrite_fanarts" ) == "true" )
        self.settings["clean_title"]           = ( addon_obj.getSetting( "clean_title" ) == "true" )
        self.settings["ignore_bios"]           = ( addon_obj.getSetting( "ignore_bios" ) == "true" )
        self.settings["ignore_title"]          = ( addon_obj.getSetting( "ignore_title" ) == "true" )
        self.settings["title_formating"]       = ( addon_obj.getSetting( "title_formating" ) == "true" )
        self.settings["datas_scraper"]         = addon_obj.getSetting( "datas_scraper" )
        self.settings["thumbs_scraper"]        = addon_obj.getSetting( "thumbs_scraper" )
        self.settings["fanarts_scraper"]       = addon_obj.getSetting( "fanarts_scraper" )
        self.settings["game_region"]           = ['All','EU','JP','US'][int(addon_obj.getSetting('game_region'))]
        self.settings["launcher_thumb_path"]   = addon_obj.getSetting( "launcher_thumb_path" )
        self.settings["launcher_fanart_path"]  = addon_obj.getSetting( "launcher_fanart_path" )
        self.settings["launcher_nfo_path"]     = addon_obj.getSetting( "launcher_nfo_path" )
        self.settings["media_state"]           = addon_obj.getSetting( "media_state" )
        self.settings["show_batch"]            = ( addon_obj.getSetting( "show_batch" ) == "true" )
        self.settings["recursive_scan"]        = ( addon_obj.getSetting( "recursive_scan" ) == "true" )
        self.settings["launcher_notification"] = ( addon_obj.getSetting( "launcher_notification" ) == "true" )
        self.settings["lirc_state"]            = ( addon_obj.getSetting( "lirc_state" ) == "true" )
        self.settings["hide_finished"]         = ( addon_obj.getSetting( "hide_finished" ) == "true" )
        self.settings["snap_flyer"]            = addon_obj.getSetting( "snap_flyer" )
        self.settings["start_tempo"]           = int(round(float(addon_obj.getSetting( "start_tempo" ))))
        self.settings["auto_backup"]           = ( addon_obj.getSetting( "auto_backup" ) == "true" )
        self.settings["nb_backup_files"]       = int(round(float(addon_obj.getSetting( "nb_backup_files" ))))
        self.settings["show_log"]              = ( addon_obj.getSetting( "show_log" ) == "true" )
        self.settings["hide_default_cat"]      = ( addon_obj.getSetting( "hide_default_cat" ) == "true" )
        self.settings["open_default_cat"]      = ( addon_obj.getSetting( "open_default_cat" ) == "true" )
        self.settings["display_game_region"]   = ['All', 'Europe', 'Japan', 'USA'][int(addon_obj.getSetting('game_region'))]
        self.settings["thumb_image_size"] = \
            ['','icon','small','medium','large','xlarge','xxlarge','huge'][int(addon_obj.getSetting('thumb_image_size'))]
        self.settings["thumb_image_size_display" ] = \
            ['All', 'Icon', 'Small', 'Medium', 'Large', 'XLarge', 'XXLarge', 'Huge'][int(addon_obj.getSetting('thumb_image_size'))]
        self.settings["fanart_image_size" ] = \
            ['All', 'Icon', 'Small', 'Medium', 'Large', 'Xlarge', 'XXlarge', 'Huge'][int(addon_obj.getSetting('fanart_image_size'))]
        self.settings["fanart_image_size_display" ] = \
            ['All', 'Icon', 'Small', 'Medium', 'Large', 'XLarge', 'XXLarge', 'Huge'][int(addon_obj.getSetting('fanart_image_size'))]

        # Temporally activate log
        self.settings["show_log"] = True

    def _get_scrapers( self ):
        # get the users gamedata scrapers preference
        exec "import resources.scrapers.datas.%s.datas_scraper as _data_scraper" % ( self.settings[ "datas_scraper" ] )
        self._get_games_list = _data_scraper._get_games_list
        self._get_game_data = _data_scraper._get_game_data
        self._get_first_game = _data_scraper._get_first_game

        # get the users thumbs scrapers preference
        exec "import resources.scrapers.thumbs.%s.thumbs_scraper as _thumbs_scraper" % ( self.settings[ "thumbs_scraper" ] )
        self._get_thumbnails_list = _thumbs_scraper._get_thumbnails_list
        self._get_thumbnail = _thumbs_scraper._get_thumbnail

        # get the users fanarts scrapers preference
        exec "import resources.scrapers.fanarts.%s.fanarts_scraper as _fanarts_scraper" % ( self.settings[ "fanarts_scraper" ] )
        self._get_fanarts_list = _fanarts_scraper._get_fanarts_list
        self._get_fanart = _fanarts_scraper._get_fanart

    #
    # These two functions do things like stopping music before lunch, toggling full screen, etc.
    #
    def _run_before_execution(self, launcher, name_str):
        if self.settings[ "media_state" ] != "2" :
            if xbmc.Player().isPlaying():
                if self.settings[ "media_state" ] == "0":
                    xbmc.Player().stop()
                if self.settings[ "media_state" ] == "1":
                    xbmc.Player().pause()
                xbmc.sleep(self.settings[ "start_tempo" ] + 100)
                try:
                    xbmc.audioSuspend()
                except:
                    pass
        if launcher["minimize"] == "true":
            _toogle_fullscreen()

        if self.settings[ "launcher_notification" ]:
            gui_kodi_notify('AEL', 'Launching {0}'.format(name_str), 5000)

        try:
            xbmc.enableNavSounds(False)                                 
        except:
            pass
        xbmc.sleep(self.settings[ "start_tempo" ])

    def _run_after_execution(self, launcher):
        xbmc.sleep(self.settings[ "start_tempo" ])
        try:
            xbmc.enableNavSounds(True)                            
        except:
            pass

        if launcher["minimize"] == "true":
            _toogle_fullscreen()

        if self.settings[ "media_state" ] != "2" :
            try:
                xbmc.audioResume()
            except:
                pass
            if ( self.settings[ "media_state" ] == "1" ):
                xbmc.sleep(self.settings[ "start_tempo" ] + 100)
                xbmc.Player().play()

    #
    # Launchs an application
    #
    def _run_standalone_launcher(self, categoryID, launcherID):
        # Check launcher is OK
        if launcherID not in self.launchers:
            gui_kodi_dialog_OK('ERROR', 'launcherID not found in launcherID')
            return
        launcher = self.launchers[launcherID]

        # Kodi built-in???
        apppath = os.path.dirname(launcher["application"])
        if os.path.basename(launcher["application"]).lower().replace(".exe" , "") == "xbmc"  or \
           "xbmc-fav-" in launcher["application"] or "xbmc-sea-" in launcher["application"]:
            xbmc.executebuiltin('XBMC.%s' % launcher["args"])
            return

        # ~~~~~ External application ~~~~~
        application = launcher["application"]
        application_basename = os.path.basename(launcher["application"])
        if not os.path.exists(apppath):
            gui_kodi_notify('AEL - ERROR', 
                            'File {0} not found.'.format(application_basename), 3000)
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
            xbmc_notify('AEL - ERROR', 'Cannot determine the running platform', 10000)

        # Do stuff after execution
        self._run_after_execution(launcher)

    #
    # Launchs a ROM
    #
    def _run_rom(self, categoryID, launcherID, romID):
        # Check launcher is OK
        if launcherID not in self.launchers:
            gui_kodi_dialog_OK('ERROR', 'launcherID not found in launcherID')
            return
        launcher = self.launchers[launcherID]
        
        # Load ROMs
        roms = self._fs_load_ROM_XML_file(launcher['roms_xml_file'])

        # Check ROM is XML data just read
        if romID not in roms:
            gui_kodi_dialog_OK('ERROR', 'romID not in roms_dic')
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
            xbmc_notify("AEL - ERROR", 'File %s not found.' % apppath, 10000)
            return
        if os.path.exists(romfile):
            xbmc_notify("AEL - ERROR", 'File %s not found.' % romfile, 10000)
            return

        # ~~~~ Argument substitution ~~~~~
        if rom["altarg"] != "": arguments = rom["altarg"]
        else:                   arguments = launcher["args"]
        arguments = arguments.replace("%rom%" ,     rom["filename"]).replace("%ROM%" , rom["filename"])
        arguments = arguments.replace("%romfile%" , romfile).replace("%ROMFILE%" , romfile)
        arguments = arguments.replace("%romname%" , romname).replace("%ROMNAME%" , romname)
        arguments = arguments.replace("%rombasename%" , base_filename(romname)).replace("%ROMBASENAME%" , base_filename(romname))
        arguments = arguments.replace("%apppath%" , apppath).replace("%APPPATH%" , apppath)
        arguments = arguments.replace("%rompath%" , rompath).replace("%ROMPATH%" , rompath)
        arguments = arguments.replace("%romtitle%" , rom["name"]).replace("%ROMTITLE%" , rom["name"])
        arguments = arguments.replace("%romspath%" , rompath).replace("%ROMSPATH%" , rompath)
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
                    if self.settings[ "show_batch" ]:
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
        # Android???
        elif sys.platform.startswith('darwin'):
            os.system("\"%s\" %s " % (application, arguments))
        else:
            xbmc_notify('AEL - ERROR', 'Cannot determine the running platform', 10000)

        # Do stuff after application execution
        self._run_after_execution(launcher)

    def _gui_render_category_row(self, category_dic, key):
        # --- Create listitem row ---
        icon = "DefaultFolder.png"        
        if category_dic['thumb'] != '':
            listitem = xbmcgui.ListItem( category_dic['name'], iconImage=icon, thumbnailImage=category_dic['thumb'] )
        else:
            listitem = xbmcgui.ListItem( category_dic['name'], iconImage=icon )
        if category_dic['finished'] == False: ICON_OVERLAY = 6
        else:                                 ICON_OVERLAY = 7
        listitem.setProperty("fanart_image", category_dic['fanart'])
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
        commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(ADDON_ID), ))
        listitem.addContextMenuItems(commands, replaceItems=True)

        # --- Add row ---
        # if ( finished != "true" ) or ( self.settings[ "hide_finished" ] == False) :
        url_str = self._misc_url('SHOW_LAUNCHERS', key)
        xbmcplugin.addDirectoryItem( handle=int( self.addon_handle ), url=url_str, listitem=listitem, isFolder=True)

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
        commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(ADDON_ID), ))
        listitem.addContextMenuItems(commands, replaceItems=True)

        # --- Add row ---
        url_str = self._misc_url('SHOW_FAVOURITES')
        xbmcplugin.addDirectoryItem( handle=int(self.addon_handle), url=url_str, listitem=listitem, isFolder=True)

    # 
    # Former _get_categories()
    # Renders the categories (addon root window)
    #
    def _gui_render_categories( self ):
        # For every category, add it to the listbox
        # Order alphabetically by name
        for key in sorted(self.categories, key= lambda x : self.categories[x]["name"]):
            self._gui_render_category_row(self.categories[key], key)
        # AEL Favourites special category
        self._gui_render_category_favourites()
        xbmcplugin.endOfDirectory( handle = int( self.addon_handle ), succeeded=True, cacheToDisc=False )

    def _gui_render_launcher_row(self, launcher_dic, key):
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
        if launcher_dic['finished'] != True:
            ICON_OVERLAY = 6
        else:
            ICON_OVERLAY = 7
        listitem.setProperty("fanart_image", launcher_dic['fanart'])
        listitem.setInfo( "video", {"Title": launcher_dic['name'], "Label": os.path.basename(launcher_dic['rompath']),
                                    "Plot" : launcher_dic['plot'], "Studio" : launcher_dic['studio'],
                                    "Genre" : launcher_dic['genre'], "Premiered" : launcher_dic['release'],
                                    "Year" : launcher_dic['release'], "Writer" : launcher_dic['gamesys'],
                                    "Trailer" : os.path.join(launcher_dic['trailerpath']),
                                    "Director" : os.path.join(launcher_dic['custompath']), 
                                    "overlay": ICON_OVERLAY } )

        # --- Create context menu ---
        launcherID = launcher_dic['id']
        categoryID = launcher_dic['category']
        commands.append(('Create New Launcher', self._misc_url_RunPlugin('ADD_LAUNCHER', categoryID), ))
        commands.append(('Edit Launcher', self._misc_url_RunPlugin('EDIT_LAUNCHER', categoryID, launcherID), ))
        # ROMs launcher
        if not launcher_dic['rompath'] == '':
            commands.append(('Add ROMs', self._misc_url_RunPlugin('ADD_ROMS', launcher_dic['category'], key), ))
        commands.append(('Search Launcher', self._misc_url_RunPlugin('SEARCH_LAUNCHER'), ))
        # Add Launcher URL to Kodi Favourites (do not know how to do it yet)
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', )) # If using window ID then use "10003" 
        commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(ADDON_ID), ))
        listitem.addContextMenuItems(commands, replaceItems=True)

        # --- Add row ---
        url_str = self._misc_url('SHOW_ROMS', launcher_dic['category'], key)
        xbmcplugin.addDirectoryItem(handle=int( self.addon_handle ), url=url_str, listitem=listitem, isFolder=folder)

    #
    # Former  _get_launchers
    # Renders the launcher for a given category
    #
    def _gui_render_launchers( self, categoryID ):
        for key in sorted(self.launchers, key= lambda x : self.launchers[x]["application"]):
            if self.launchers[key]["category"] == categoryID:
                self._gui_render_launcher_row(self.launchers[key], key)
        xbmcplugin.endOfDirectory( handle=int( self.addon_handle ), succeeded=True, cacheToDisc=False )

    #
    # Former  _add_rom
    # Note that if we are rendering favourites, categoryID = launcherID = '0'.
    def _gui_render_rom_row( self, categoryID, launcherID, romID, rom):
        # --- Create listitem row ---
        icon = "DefaultProgram.png"
        # icon = "DefaultVideo.png"
        if rom['thumb']: listitem = xbmcgui.ListItem(rom['name'], iconImage=icon, thumbnailImage=rom['thumb'])
        else:            listitem = xbmcgui.ListItem(rom['name'], iconImage=icon)
        # If ROM has no fanart then use launcher fanart
        if launcherID == '0':
            defined_fanart = rom["fanart"]
        else:
            defined_fanart = rom["fanart"] if rom["fanart"] != '' else self.launchers[launcherID]["fanart"]
        if rom['finished'] is not True: ICON_OVERLAY = 6
        else:                           ICON_OVERLAY = 7
        listitem.setProperty("fanart_image", defined_fanart)
        listitem.setInfo("video", { "Title": rom['name'], "Label": 'test label', 
                                    "Plot" : rom['plot'], "Studio" : rom['studio'], 
                                    "Genre" : rom['genre'], "Premiered" : rom['release'], 
                                    'Year' : rom['release'], "Writer" : rom['gamesys'], 
                                    "Trailer" : 'test trailer', "Director" : 'test director', 
                                    "overlay": ICON_OVERLAY } )
        if self._content_type == 'video':
            listitem.setProperty('IsPlayable', 'true')

        # --- Create context menu ---
        commands = []
        if launcherID == '0':
            commands.append(('Edit ROM in Favourites', self._misc_url_RunPlugin('EDIT_ROM', '0', '0', romID), ))
            commands.append(('Search Favourites', self._misc_url_RunPlugin('SEARCH_LAUNCHER', '0', '0'), ))
            commands.append(('Delete ROM from Favourites', self._misc_url_RunPlugin('DELETE_ROM', '0', '0', romID), ))
        else:
            commands.append(('Edit ROM', self._misc_url_RunPlugin('EDIT_ROM', categoryID, launcherID, romID), ))
            commands.append(('Search ROMs in Launcher', self._misc_url_RunPlugin('SEARCH_LAUNCHER', categoryID, launcherID), ))
            commands.append(('Add ROM to AEL Favourites', self._misc_url_RunPlugin('ADD_TO_FAVOURITES', categoryID, launcherID, romID), )) 
            commands.append(('Delete ROM', self._misc_url_RunPlugin('DELETE_ROM', categoryID, launcherID, romID), ))
        # Add ROM URL to Kodi Favourites (do not know how to do it yet) (maybe not will be used)
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', )) # If using window ID then use "10003" 
        commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(ADDON_ID), ))
        listitem.addContextMenuItems(commands, replaceItems=True)

        # --- Add row ---
        # if finished != "true" or self.settings[ "hide_finished" ] == False:
        # URLs must be different depending on the content type. If not, lot of WARNING: CreateLoader - unsupported protocol(plugin)
        # in the log. See http://forum.kodi.tv/showthread.php?tid=187954
        if self._content_type == 'video':
            url_str = self._misc_url('LAUNCH_ROM', categoryID, launcherID, romID)
        else:
            url_str = self._misc_url('LAUNCH_ROM', categoryID, launcherID, romID)
        xbmcplugin.addDirectoryItem(handle=int(self.addon_handle), url=url_str, listitem=listitem, isFolder=False)

    #
    # Former  _get_roms
    # Renders the roms listbox for a given launcher
    #
    def _gui_render_roms(self, categoryID, launcherID):

        #xbmcplugin.setContent(handle = self.addon_handle, content = 'movies')

        ## Adds a sorting method for the media list.
        #if self.addon_handle > 0:
            #xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
            #xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)
            #xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_STUDIO)
            #xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_GENRE)
            #xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)

        if launcherID not in self.launchers:
            gui_kodi_dialog_OK('AEL ERROR', 'Launcher hash not found.', '@_gui_render_roms()')
            return
        # Load ROMs for this launcher and display them
        selectedLauncher = self.launchers[launcherID]
        roms_xml_file = selectedLauncher["roms_xml_file"]

        # Check if XML file with ROMs exist
        if not os.path.isfile(roms_xml_file):
            gui_kodi_notify('Advanced Emulator Launcher', 'Launcher XML missing. Add items to launcher.', 10000)
            xbmc.executebuiltin("Container.Update")
            return

        # Load ROMs
        roms = self._fs_load_ROM_XML_file(roms_xml_file)
        if not roms:
            gui_kodi_notify('Advanced Emulator Launcher', 'Launcher XML empty. Add items to launcher.', 10000)
            return

        # Display ROMs
        for key in sorted(roms, key= lambda x : roms[x]["filename"]):
            self._gui_render_rom_row(categoryID, launcherID, key, roms[key])
        xbmcplugin.endOfDirectory( handle=int( self.addon_handle ), succeeded=True, cacheToDisc=False )

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
    def _command_show_favourites(self):
        # Load favourites
        roms = self._fs_load_Favourites_XML_file(FAVOURITES_FILE_PATH)
        if not roms:
            gui_kodi_notify('Advanced Emulator Launcher', 'Favourites XML empty. Add items to favourites first', 5000)
            return

        # Display Favourites
        for key in sorted(roms, key= lambda x : roms[x]["filename"]):
            self._gui_render_rom_row('0', '0', key, roms[key])
        xbmcplugin.endOfDirectory( handle=int( self.addon_handle ), succeeded=True, cacheToDisc=False )

    #
    # Adds ROM to favourites
    #
    def _command_add_to_favourites(self, categoryID, launcherID, romID):
        # Load ROMs in launcher
        launcher = self.launchers[launcherID]
        roms_xml_file = launcher["roms_xml_file"]
        roms = self._fs_load_ROM_XML_file(roms_xml_file)
        if not roms:
            gui_kodi_dialog_OK('Advanced Emulator Launcher',
                               'Empty roms launcher in _command_add_to_favourites()',
                               'This is a bug, please report it.')

        # Load favourites
        roms_fav = self._fs_load_Favourites_XML_file(FAVOURITES_FILE_PATH)
        
        # Check if ROM already in favourites an warn user if so
        if roms[romID]['id'] in roms_fav:
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher', 
                               'ROM: {0}'.format(roms[romID]["name"]),
                               'is already on AEL Favourites.', 'Overwrite it?')
            if not ret: return
        
        # Confirm if rom should be added
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno('Advanced Emulator Launcher', 
                            'ROM: {0}'.format(roms[romID]["name"]),
                            'Add this ROM to AEL Favourites?')
        if not ret: return
        
        # Add ROM to favourites ROMs and save to disk
        # If thumb is empty then use launcher thum.
        # If fanart is empty then use launcher fanart.
        roms_fav[romID] = roms[romID]
        roms_fav[romID]['application'] = self.launchers[launcherID]['application']
        roms_fav[romID]['args']        = self.launchers[launcherID]['args']
        roms_fav[romID]['launcherID']  = self.launchers[launcherID]['id']
        if roms_fav[romID]['thumb']  == '': roms_fav[romID]['thumb']  = self.launchers[launcherID]['thumb']
        if roms_fav[romID]['fanart'] == '': roms_fav[romID]['fanart'] = self.launchers[launcherID]['fanart']

        # Save favourites
        self._fs_write_Favourites_XML_file(roms_fav, FAVOURITES_FILE_PATH)

    #
    # ROM scanner. Called when user chooses "Add items" -> "Scan items"
    # Note that actually this command is "Add/Update" ROMs.
    #
    def _roms_import_roms(self, launcherID):
        self._print_log('_roms_import_roms() BEGIN')

        dialog = xbmcgui.Dialog()
        pDialog = xbmcgui.DialogProgress()
        # Get game system, thumbnails and fanarts paths from launcher
        selectedLauncher = self.launchers[launcherID]
        launch_app          = selectedLauncher["application"]
        launch_path         = selectedLauncher["rompath"]
        launch_exts         = selectedLauncher["romext"]
        self._print_log('Launcher "%s" selected' % selectedLauncher["name"]) 
        self._print_log('launch_app  = {0}'.format(launch_app)) 
        self._print_log('launch_path = {0}'.format(launch_path)) 
        self._print_log('launch_exts = {0}'.format(launch_exts)) 

        # Check if there is an XML for this launcher. If so, load it.
        # If file does not exist or is empty then return an empty dictionary.
        rom_xml_path = selectedLauncher["roms_xml_file"]
        roms = self._fs_load_ROM_XML_file(rom_xml_path)

        # ~~~~~ Remove dead entries ~~~~~
        if len(roms) > 0:
            self._print_log('Launcher list contain %s items' % len(roms))
            self._print_log('Starting dead items scan')
            i = 0
            removedRoms = 0
            ret = pDialog.create('Advanced Emulator Launcher', 
                                 'Checking for dead entries',
                                 'Path: %s...' % (launch_path))
            for key in sorted(roms.iterkeys()):
                self._print_log('Searching %s' % roms[key]["filename"] )
                pDialog.update(i * 100 / len(roms))
                i += 1
                if (not os.path.isfile(roms[key]["filename"])):
                    self._print_log('Not found')
                    self._print_log('Delete %s item entry' % roms[key]["filename"] )
                    del roms[key]
                    removedRoms += 1
                else:
                    self._print_log('Found')

            pDialog.close()
            if not (removedRoms == 0):
                self._print_log('%s entries removed successfully' % removedRoms)
                xbmc_notify('AEL', '%s entries removed successfully' % removedRoms, 3000)
            else:
                self._print_log('No dead item entry')
        else:
            self._print_log('Launcher is empty')

        # ~~~ Scan for new files (*.*) and put them in a list ~~~
        gui_kodi_notify('AEL', 'Scanning files...', 3000)
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        self._print_log('Scanning files in {0}'.format(launch_path))
        files = []
        if self.settings[ "recursive_scan" ]:
            self._print_log('Recursive scan activated')
            for root, dirs, filess in os.walk(launch_path):
                for filename in fnmatch.filter(filess, '*.*'):
                    files.append(os.path.join(root, filename))
        else:
            self._print_log('Recursive scan not activated')
            filesname = os.listdir(launch_path)
            for filename in filesname:
                files.append(os.path.join(launch_path, filename))
        xbmc.executebuiltin("Dialog.Close(busydialog)")
        self._print_log('Found {0} files'.format(len(files)))

        # ~~~ String to inform the user of scrapers used ~~~
        if self.settings[ "datas_method" ] == "0":
            metadata_scraper_text = 'Metadata scraper: None'
        elif self.settings[ "datas_method" ] == "1":
            metadata_scraper_text = 'Metadata scraper: NFO files'
        elif self.settings[ "datas_method" ] == "2":
            metadata_scraper_text = 'Metadata scraper: {0}'.format(self.settings[ "datas_scraper" ].encode('utf-8', 'ignore'))
        elif self.settings[ "datas_method" ] == "3":
            metadata_scraper_text = 'Metadata scraper: NFO files or {0}'.format(self.settings[ "datas_scraper" ].encode('utf-8','ignore'))

        # ~~~ Now go processing file by file ~~~
        ret = pDialog.create('AEL - Importing ROMs', 'Importing files from {0}'.format(launch_path))
        self._print_log('======= Processing ROMs ======')
        romsCount = 0
        filesCount = 0
        # f_path       Full path
        # f_path_noext Full path with no extension
        # f_base       File name with no path
        # f_base_noext File name with no path and no extension
        # f_ext        File extension
        for f_path in files:
            filesCount = filesCount + 1

            # --- Get all file name combinations ---
            (root, ext)  = os.path.splitext(f_path)
            f_path_noext = root
            f_base       = os.path.basename(f_path)
            (root, ext)  = os.path.splitext(f_base)
            f_base_noext = root
            f_ext        = ext
            self._print_log('*** Processing File ***')
            self._print_log('f_path       = "{0}"'.format(f_path))
            self._print_log('f_path_noext = "{0}"'.format(f_path_noext))
            self._print_log('f_base       = "{0}"'.format(f_base))
            self._print_log('f_base_noext = "{0}"'.format(f_base_noext))
            self._print_log('f_ext        = "{0}"'.format(f_ext))

            # ~~~ Update progress dialog ~~~
            file_text = 'File {0}'.format(f_base)
            pDialog.update(filesCount * 100 / len(files), file_text, metadata_scraper_text)

            # ~~~ Find ROM file ~~~
            # The recursive scan has scanned all file. Check if this file matches some of the extensions
            # for ROMs. If not, skip this file and go for next one in the list.
            processROM = False
            for ext in launch_exts.split("|"):
                # Check if filename matchs extension
                if f_ext == '.' + ext:
                    self._print_log('Expected %s extension detected' % ext) 
                    processROM = True
            # If file does not match any of the ROM extensions skip it
            if not processROM:
                continue

            # Check that ROM is not already in the list of ROMs
            repeatedROM = False
            for g in roms:
                if roms[g]["filename"] == f_path:
                    self._print_log('File already into launcher list') 
                    repeatedROM = True
            # If file already in ROM list skip it
            if repeatedROM:
                continue
            
            # ~~~~~ Process new ROM and add to the list ~~~~~
            romdata = self._roms_process_scanned_ROM(selectedLauncher, f_path, f_path_noext, f_base, f_base_noext, f_ext)
            romID = romdata["id"]
            roms[romID] = romdata
            romsCount = romsCount + 1
        pDialog.close()

        # ~~~ Save launchers ~~~
        self._fs_write_ROM_XML_file(roms, launcherID, rom_xml_path)

        # ~~~ Notify user ~~~
        gui_kodi_notify('Advanced Emulator Launcher', '%s files imported' % (romsCount), 3000)
        xbmc.executebuiltin("XBMC.ReloadSkin()")

    def _roms_process_scanned_ROM(self, selectedLauncher, f_path, f_path_noext, f_base, f_base_noext, f_ext):
        # Grab info
        launch_gamesys      = selectedLauncher["gamesys"]

        # Prepare rom object data
        romdata = {}
        romdata["id"]       = misc_generate_random_SID()
        romdata["name"]     = ''
        romdata["filename"] = f_path
        romdata["gamesys"]  = launch_gamesys
        romdata["thumb"]    = ''
        romdata["fanart"]   = ''
        romdata["trailer"]  = ''
        romdata["custom"]   = ''
        romdata["genre"]    = ''
        romdata["release"]  = ''
        romdata["studio"]   = ''
        romdata["plot"]     = ''
        romdata["finished"] = False
        romdata["altapp"]   = ''
        romdata["altarg"]   = ''

        # ~~~~~ Scrape game metadata information ~~~~~
        # From now force NFO files scraper
        self.settings[ "datas_method" ] == "1"
        
        # No metadata scrap
        if self.settings[ "datas_method" ] == "0":
            self._print_log('Scraping disabled') 
            romdata["name"] = self._text_ROM_title_format(f_base_noext)
        else:
            # Scrap metadata from NFO files
            found_NFO_file = False
            if self.settings[ "datas_method" ] == "1" or self.settings[ "datas_method" ] == "3":
                nfo_file_path = os.path.join(f_path_noext, ".nfo")
                self._print_log('Trying NFO file "{0}"...'.format(nfo_file_path))
                if os.path.isfile(nfo_file):
                    found_NFO_file = True
                    nfo_dic = _fs_load_NFO_file(nfo_file_path)
                    romdata['name']    = nfo_dic['title']     # <title>
                    # <platform> is chosen by AEL, not read from NFO files
                    # romdata['gamesys'] = nfo_dic['platform']  # <platform>
                    romdata['release'] = nfo_dic['year']      # <year>
                    romdata['studio']  = nfo_dic['publisher'] # <publisher>
                    romdata['genre']   = nfo_dic['genre']     # <genre>
                    romdata['plot']    = nfo_dic['plot']      # <plot>
                else:
                    found_NFO_file = False
                    self._print_log('Only update item name')
                    romdata['name'] = _text_ROM_title_format(self, romname)

            # Scrap metadata from www database
            if self.settings[ "datas_method" ] == "2" or (self.settings[ "datas_method" ] == "3" and found_NFO_file == False):
                romdata["name"] = clean_filename(romname)
                if ( self.settings[ "scrap_info" ] == "1" ):
                    self._print_log('Info automatic scraping') 
                    results = self._get_first_game(romdata["name"],gamesys)
                    selectgame = 0
                else:
                    self._print_log('Info semi-automatic scraping') 
                    results,display = self._get_games_list(romdata["name"])
                    if display:
                        # Display corresponding game list found
                        dialog = xbmcgui.Dialog()
                        # Game selection
                        selectgame = dialog.select('Select a item from %s' % ( self.settings[ "datas_scraper" ] ), display)
                        if (selectgame == -1):
                            results = []
                if results:
                    foundname = results[selectgame]["title"]
                    if (foundname != ""):
                        if ( self.settings[ "ignore_title" ] ):
                            romdata["name"] = title_format(self,romname)
                        else:
                            romdata["name"] = title_format(self,foundname)

                        # Game other game data
                        gamedata = self._get_game_data(results[selectgame]["id"])
                        romdata["genre"] = gamedata["genre"]
                        romdata["release"] = gamedata["release"]
                        romdata["studio"] = gamedata["studio"]
                        romdata["plot"] = gamedata["plot"]
                        progress_display = romdata["name"] + " (" + romdata["release"] + ")"
                    else:
                        progress_display = romname + ": " + 'not found'
                else:
                    romdata["name"] = title_format(self,romname)
                    progress_display = romname + ": " + 'not found'

        # ~~~~~ Search if thumbnails and fanarts already exist ~~~~~
        # If thumbs/fanart have the same path, then have names like _thumb, _fanart
        # Otherwise, thumb/fanart name is same as ROM, but different extension.
        # f_path, f_path_noext, f_base, f_base_noext, f_ext
        thumb_path   = selectedLauncher["thumbpath"]
        fanart_path  = selectedLauncher["fanartpath"]
        self._print_log('Searching local tumb/fanart')

        if thumb_path == fanart_path:
            self._print_log('Thumbs/Fanarts have the same path')
            tumb_path_noext   = os.path.join(thumb_path, f_base_noext + '_thumb')
            fanart_path_noext = os.path.join(fanart_path, f_base_noext + '_fanart')
        else:
            self._print_log('Thumbs/Fanarts into different folders')
            tumb_path_noext   = os.path.join(thumb_path, f_base_noext)
            fanart_path_noext = os.path.join(fanart_path, f_base_noext)
        self._print_log('tumb_path_noext   = "{0}"'.format(tumb_path_noext))
        self._print_log('fanart_path_noext = "{0}"'.format(fanart_path_noext))

        # Search for local artwork
        thumb = ''
        fanart = ''
        ext2s = ['png', 'jpg', 'gif', 'jpeg', 'bmp', 'PNG', 'JPG', 'GIF', 'JPEG', 'BMP']
        # Thumbs first
        for ext2 in ext2s:
            test_img = tumb_path_noext + '.' + ext2
            self._print_log('Testing Thumb  "{0}"'.format(test_img))
            if os.path.isfile(test_img):
                thumb = test_img
                self._print_log('Found Thumb    "{0}"'.format(test_img))
                break

        # Fanart second
        for ext2 in ext2s:
            test_img = fanart_path_noext + '.' + ext2
            self._print_log('Testing Fanart "{0}"'.format(test_img))
            if os.path.isfile(test_img):
                fanart = test_img
                self._print_log('Found Fanart   "{0}"'.format(test_img))
                break

        # Add to ROM dictionary
        romdata["thumb"]  = thumb
        romdata["fanart"] = fanart
        self._print_log('Set Thumb  = "{0}"'.format(thumb))
        self._print_log('Set Fanart = "{0}"'.format(fanart))

        # Deactivate Thumb scraping
        if None:
            if self.settings[ "thumbs_method" ] == "2":
                # If overwrite is activated or thumb file not exist
                if self.settings[ "overwrite_thumbs"] or thumb == "":
                    pDialog.update(filesCount * 100 / len(files), 
                                __language__( 30065 ) % (f.replace("."+f.split(".")[-1],""), 
                                self.settings[ "thumbs_scraper" ].encode('utf-8','ignore')))
                    img_url=""
                    if (thumb_path == fanart_path):
                        if (thumb_path == path):
                            thumb = fullname.replace("."+f.split(".")[-1], '_thumb.jpg')
                        else:
                            thumb = os.path.join(thumb_path, f.replace("."+f.split(".")[-1], '_thumb.jpg'))
                    else:
                        if (thumb_path == path):
                            thumb = fullname.replace("."+f.split(".")[-1], '.jpg')
                        else:
                            thumb = os.path.join(thumb_path, f.replace("."+f.split(".")[-1], '.jpg'))
                    if app.lower().find('mame') > 0 or self.settings[ "thumbs_scraper" ] == 'arcadeHITS':
                        covers = self._get_thumbnails_list(romdata["gamesys"], 
                                                        title,
                                                        self.settings[ "game_region" ],
                                                        self.settings[ "thumb_image_size" ])
                    else:
                        covers = self._get_thumbnails_list(romdata["gamesys"], 
                                                        romdata["name"],
                                                        self.settings[ "game_region" ],
                                                        self.settings[ "thumb_image_size" ])
                    if covers:
                        if ( self.settings[ "scrap_thumbs" ] == "1" ):
                            if ( self.settings[ "snap_flyer" ] == "1" ) and ( self.settings[ "thumbs_scraper" ] == 'arcadeHITS' ):
                                img_url = self._get_thumbnail(covers[-1][0])
                            else:
                                img_url = self._get_thumbnail(covers[0][0])
                        else:
                            nb_images = len(covers)
                            pDialog.close()
                            self.image_url = MyDialog(covers)
                            if ( self.image_url ):
                                img_url = self._get_thumbnail(self.image_url)
                                ret = pDialog.create('Advanced Emulator Launcher', __language__( 30014 ) % (path))
                                pDialog.update(filesCount * 100 / len(files), 
                                            __language__( 30061 ) % (f.replace("."+f.split(".")[-1],""),
                                            self.settings[ "datas_scraper" ].encode('utf-8','ignore')))
                        cached_thumb = Thumbnails().get_cached_covers_thumb( thumb ).replace("tbn" , "jpg")
                        if ( img_url !='' ):
                            try:
                                download_img(img_url,thumb)
                                shutil.copy2( thumb.decode(get_encoding(),'ignore') , cached_thumb.decode(get_encoding(),'ignore') )
                            except socket.timeout:
                                xbmc_notify('Advanced Emulator Launcher'+" - "+__language__( 30612 ), __language__( 30604 ),3000)
                            except exceptions.IOError:
                                xbmc_notify('Advanced Emulator Launcher'+" - "+__language__( 30612 ), __language__( 30605 ),3000)
                        else:
                            if ( not os.path.isfile(thumb) ) & ( os.path.isfile(cached_thumb) ):
                                os.remove(cached_thumb)
                romdata["thumb"] = thumb
            else:
                if self.settings[ "thumbs_method" ] == "0":
                    romdata["thumb"] = ""
                else:
                    pDialog.update(filesCount * 100 / len(files), 
                                __language__( 30065 ) % (f.replace("."+f.split(".")[-1],""), __language__( 30172 )))
                    romdata["thumb"] = thumb

        # Deactivate Fanart scraping
        if None:
            if ( self.settings[ "fanarts_method" ] == "2" ):
                # If overwrite activated or fanart file not exist
                if ( self.settings[ "overwrite_fanarts"] ) or ( fanart == "" ):
                    pDialog.update(filesCount * 100 / len(files), 
                                __language__( 30071 ) % (f.replace("."+f.split(".")[-1],""),
                                self.settings[ "fanarts_scraper" ].encode('utf-8','ignore')))
                    img_url=""
                    if (fanart_path == thumb_path):
                        if (fanart_path == path):
                            fanart = fullname.replace("."+f.split(".")[-1], '_fanart.jpg')
                        else:
                            fanart = os.path.join(fanart_path, f.replace("."+f.split(".")[-1], '_fanart.jpg'))
                    else:
                        if (fanart_path == path):
                            fanart = fullname.replace("."+f.split(".")[-1], '.jpg')
                        else:
                            fanart = os.path.join(fanart_path, f.replace("."+f.split(".")[-1], '.jpg'))
                    if ( app.lower().find('mame') > 0 ) or ( self.settings[ "fanarts_scraper" ] == 'arcadeHITS' ):
                        covers = self._get_fanarts_list(romdata["gamesys"],title,self.settings[ "fanart_image_size" ])
                    else:
                        covers = self._get_fanarts_list(romdata["gamesys"],romdata["name"],self.settings[ "fanart_image_size" ])
                    if covers:
                        if ( self.settings[ "scrap_fanarts" ] == "1" ):
                            if ( self.settings[ "select_fanarts" ] == "0" ):
                                img_url = self._get_fanart(covers[0][0])
                            if ( self.settings[ "select_fanarts" ] == "1" ):
                                img_url = self._get_fanart(covers[int(round(len(covers)/2))-1][0])
                            if ( self.settings[ "select_fanarts" ] == "2" ):
                                img_url = self._get_fanart(covers[len(covers)-1][0])
                        else:
                            nb_images = len(covers)
                            pDialog.close()
                            self.image_url = MyDialog(covers)
                            if ( self.image_url ):
                                img_url = self._get_fanart(self.image_url)
                                ret = pDialog.create('Advanced Emulator Launcher', __language__( 30014 ) % (path))
                                pDialog.update(filesCount * 100 / len(files), 
                                            __language__( 30061 ) % (f.replace("."+f.split(".")[-1],""),
                                            self.settings[ "datas_scraper" ].encode('utf-8','ignore')))
                        cached_thumb = Thumbnails().get_cached_covers_thumb( fanart ).replace("tbn" , "jpg")
                        if ( img_url !='' ):
                            try:
                                download_img(img_url,fanart)
                                shutil.copy2( fanart.decode(get_encoding(),'ignore') , cached_thumb.decode(get_encoding(),'ignore') )
                            except socket.timeout:
                                xbmc_notify('Advanced Emulator Launcher'+" - "+__language__( 30612 ), __language__( 30606 ),3000)
                            except exceptions.IOError:
                                xbmc_notify('Advanced Emulator Launcher'+" - "+__language__( 30612 ), __language__( 30607 ),3000)
                        else:
                            if ( not os.path.isfile(fanart) ) & ( os.path.isfile(cached_thumb) ):
                                os.remove(cached_thumb)
                romdata["fanart"] = fanart
            else:
                if self.settings[ "fanarts_method" ] == "0":
                    romdata["fanart"] = ""
                else:
                    pDialog.update(filesCount * 100 / len(files), 
                                __language__( 30071 ) % (f.replace("."+f.split(".")[-1],""),
                                __language__( 30172 )))
                    romdata["fanart"] = fanart

        # Return romdata dictionary
        return romdata
    #
    # Manually add a new ROM instead of a recursive scan
    #
    def _roms_add_new_rom ( self , launcherID) :
        dialog = xbmcgui.Dialog()
        launcher = self.launchers[launcherID]
        app = launcher["application"]
        ext = launcher["romext"]
        roms = launcher["roms"]
        rompath = launcher["rompath"]
        romfile = dialog.browse(1, __language__( 30017 ),"files", "."+ext.replace("|","|."), False, False, rompath)
        if (romfile):
            title=os.path.basename(romfile)
            keyboard = xbmc.Keyboard(title.replace('.'+title.split('.')[-1],'').replace('.',' '), __language__( 30018 ))
            keyboard.doModal()
            if (keyboard.isConfirmed()):
                title = keyboard.getText()
                if ( title == "" ):
                    title = os.path.basename(romfile)
                    title = title.replace('.'+title.split('.')[-1],'').replace('.',' ')
                # Romname conversion if MAME
                if ( app.lower().find('mame') > 0 ):
                    romname = self._get_mame_title(title)
                    romname = title_format(self,romname)
                else:
                    romname = title_format(self,title)
                # Search for default thumbnails and fanart images path
                ext2s = ['png', 'jpg', 'gif', 'jpeg', 'bmp', 'PNG', 'JPG', 'GIF', 'JPEG', 'BMP']
                thumb_path = launcher["thumbpath"]
                fanart_path = launcher["fanartpath"]
                romthumb = ""
                romfanart = ""
                f = os.path.basename(romfile)
                for ext2 in ext2s:
                    if (thumb_path == fanart_path) :
                        if (thumb_path == rompath) :
                            if (os.path.isfile(os.path.join(os.path.dirname(romfile), f.replace("."+f.split(".")[-1], '_thumb.'+ext2)))):
                                romthumb = os.path.join(os.path.dirname(romfile), f.replace("."+f.split(".")[-1], '_thumb.'+ext2))
                        else:
                            if (os.path.isfile(os.path.join(thumb_path, f.replace("."+f.split(".")[-1], '_thumb.'+ext2)))):
                                romthumb = os.path.join(thumb_path, f.replace("."+f.split(".")[-1], '_thumb.'+ext2))
                    else:
                        if (thumb_path == "") :
                            romthumb = os.path.join(os.path.dirname(romfile), f.replace("."+f.split(".")[-1], '_thumb.jpg'))
                        else:
                            if (thumb_path == rompath) :
                                if (os.path.isfile(os.path.join(os.path.dirname(romfile), f.replace("."+f.split(".")[-1], '.'+ext2)))):
                                    romthumb = os.path.join(os.path.dirname(romfile), f.replace("."+f.split(".")[-1], '.'+ext2))
                            else:
                                if (os.path.isfile(os.path.join(thumb_path, f.replace("."+f.split(".")[-1], '.'+ext2)))):
                                    romthumb = os.path.join(thumb_path, f.replace("."+f.split(".")[-1], '.'+ext2))

                    if (fanart_path == thumb_path) :
                        if (fanart_path == rompath) :
                            if (os.path.isfile(os.path.join(os.path.dirname(romfile), f.replace("."+f.split(".")[-1], '_fanart.'+ext2)))):
                                romfanart = os.path.join(os.path.dirname(romfile), f.replace("."+f.split(".")[-1], '_fanart.'+ext2))
                        else:
                            if (os.path.isfile(os.path.join(fanart_path, f.replace("."+f.split(".")[-1], '_fanart.'+ext2)))):
                                romfanart = os.path.join(fanart_path, f.replace("."+f.split(".")[-1], '_fanart.'+ext2))
                    else:
                        if (fanart_path == "") :
                            romfanart = os.path.join(os.path.dirname(romfile), f.replace("."+f.split(".")[-1], '_fanart.jpg'))
                        else:
                            if (fanart_path == rompath) :
                                if (os.path.isfile(os.path.join(os.path.dirname(romfile), f.replace("."+f.split(".")[-1], '.'+ext2)))):
                                   romfanart = os.path.join(os.path.dirname(romfile), f.replace("."+f.split(".")[-1], '.'+ext2))
                            else:
                                if (os.path.isfile(os.path.join(fanart_path, f.replace("."+f.split(".")[-1], '.'+ext2)))):
                                    romfanart = os.path.join(fanart_path, f.replace("."+f.split(".")[-1], '.'+ext2))
                romdata = {"name" : romname, "filename" : romfile, "gamesys" : launcher["gamesys"], "thumb" : romthumb, 
                           "fanart" : romfanart, "custom" : launcher["custompath"], "trailer" : "", "genre" : "",
                           "release" : "", "studio" : "", "plot" : "", "finished" : "false", "altapp" : "", "altarg" : "" }
                # add rom to the roms list (using name as index)
                romid = _get_SID()
                roms[romid] = romdata
                xbmc_notify('AEL', 'Edit Launcher' + " " + 'Re-Enter this directory to see the changes', 3000)
        self._save_launchers()

    def _command_add_new_category(self):
        dialog = xbmcgui.Dialog()
        keyboard = xbmc.Keyboard("", 'New Category Name')
        keyboard.doModal()
        if not keyboard.isConfirmed():
            return False

        categoryID = misc_generate_random_SID()
        categorydata = {"id" : categoryID, "name" : keyboard.getText(), 
                        "thumb" : "", "fanart" : "", "genre" : "", "plot" : "", "finished" : False}
        self.categories[categoryID] = categorydata
        self._fs_write_catfile()
        xbmc.executebuiltin("Container.Refresh")
        gui_kodi_notify('AEL' , 'Category {0} created'.format(categorydata["name"]), 3000)

        return True

    def _command_add_new_launcher(self, categoryID):
        
        # If categoryID not found return to plugin root window.
        if categoryID not in self.categories:
            xbmc_notify('Advanced Launcher - Error', 'Target category not found.' , 3000)
            xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._path))

            return False
        
        # Show "Create New Launcher" dialog
        dialog = xbmcgui.Dialog()
        type = dialog.select('Create New Launcher', 
                             ['Standalone launcher (normal executable)', 'Files launcher (game emulator)'])
        xbmc.log('_command_add_new_launcher() type = {0}'.format(type))

        if os.environ.get( "OS", "xbox" ) == "xbox": filter = ".xbe|.cut"
        elif sys.platform == "win32":                filter = ".bat|.exe|.cmd|.lnk"
        else:                                        filter = ""

        # 'Standalone launcher (normal executable)'
        if type == 0:
            app = xbmcgui.Dialog().browse(1, 'Select the launcher application', "files", filter)
            if not app:
                return False

            argument = ""
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
            platforms = emudata_game_system_list()
            gamesystem = dialog.select('Select the platform', platforms)

            # Selection of the thumbnails and fanarts path
            if self.settings[ "launcher_thumb_path" ] == "":
                thumb_path = xbmcgui.Dialog().browse(0, 'Select Thumbnails path', "files", "", False, False)
            else:
                thumb_path = self.settings[ "launcher_thumb_path" ]
            if self.settings[ "launcher_fanart_path" ] == "":
                fanart_path = xbmcgui.Dialog().browse(0, 'Select Fanarts path', "files", "", False, False)
            else:
                fanart_path = self.settings[ "launcher_fanart_path" ]

            # --- Create launcher object data, add to dictionary and write XML file ---
            if not thumb_path:  thumb_path = ""
            if not fanart_path: fanart_path = ""
            if (not gamesystem == -1 ): launcher_gamesys = platforms[gamesystem]
            else:                       launcher_gamesys = ""
            if sys.platform == "win32": launcher_lnk = True
            else:                       launcher_lnk = False
            # add launcher to the launchers dictionary (using name as index)
            launcherID = misc_generate_random_SID()
            launcherdata = {
                "id" : launcherID,
                "name" : title, "category" : categoryID, "application" : app,  "args" : args, 
                "rompath" : "", "thumbpath" : thumb_path, "fanartpath" : fanart_path, 
                "custompath" : "", "trailerpath" : "", "romext" : "", "gamesys" : launcher_gamesys, 
                "thumb" : "", "fanart" : "", "genre" : "", "release" : "", "studio" : "", 
                "plot" : "",  "lnk" : launcher_lnk, 
                "finished": False, "minimize" : False, 
                "roms_xml_file" : '' }
            self.launchers[launcherID] = launcherdata
            self._fs_write_catfile()
            xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self._path, categoryID))

            return True

        # 'Files launcher (e.g. game emulator)'
        elif type == 1:
            app = xbmcgui.Dialog().browse(1, 'Select the launcher application', "files", filter)
            if not app:
                return False
            
            files_path = xbmcgui.Dialog().browse(0, 'Select Files path', "files", "")
            if not files_path:
                return False

            extensions = emudata_get_program_extensions(os.path.basename(app))
            extkey = xbmc.Keyboard(extensions, 'Set files extensions, use "|" as separator. (e.g lnk|cbr)')
            extkey.doModal()
            if not extkey.isConfirmed():
                return False
            ext = extkey.getText()

            argument = emudata_get_program_arguments(os.path.basename(app))
            argkeyboard = xbmc.Keyboard(argument, 'Application arguments')
            argkeyboard.doModal()
            if not argkeyboard.isConfirmed():
                return False
            args = argkeyboard.getText()

            title = os.path.basename(app)
            keyboard = xbmc.Keyboard(title.replace('.'+title.split('.')[-1],'').replace('.',' '), 'Set the title of the launcher')
            keyboard.doModal()
            title = keyboard.getText()
            if ( title == "" ):
                title = os.path.basename(app)
                title = title.replace('.'+title.split('.')[-1],'').replace('.',' ')

            # Selection of the launcher game system
            dialog = xbmcgui.Dialog()
            platforms = emudata_game_system_list()
            gamesystem = dialog.select('Select the platform', platforms)

            # Selection of the thumbnails and fanarts path
            thumb_path = xbmcgui.Dialog().browse(0, 'Select Thumbnails path', "files", "", False, False, files_path)
            fanart_path = xbmcgui.Dialog().browse(0, 'Select Fanarts path', "files", "", False, False, files_path)
            
            # --- Create launcher object data, add to dictionary and write XML file ---
            if not thumb_path:          thumb_path = ""
            if not fanart_path:         fanart_path = ""
            if (not gamesystem == -1 ): launcher_gamesys = platforms[gamesystem]
            else:                       launcher_gamesys = ""
            if sys.platform == "win32": launcher_lnk = True
            else:                       launcher_lnk = False
            launcherID = misc_generate_random_SID()
            category_name = self.categories[categoryID]['name']
            clean_cat_name = ''.join([i if i in string.printable else '_' for i in category_name])
            clean_launch_title = ''.join([i if i in string.printable else '_' for i in title])
            roms_xml_file = 'roms_' + clean_cat_name + '_' + clean_launch_title + '_' + launcherID[0:8] + '.xml'
            roms_xml_file_path = os.path.join(PLUGIN_DATA_DIR, roms_xml_file)
            self._print_log('Chosen roms_xml_file = "{0}"'.format(roms_xml_file))
            self._print_log('Chosen roms_xml_file = "{0}"'.format(roms_xml_file_path))
            launcherdata = {
                "id" : launcherID,
                "name" : title, "category" : categoryID, "application" : app,  "args" : args, 
                "rompath" : files_path, "thumbpath" : thumb_path, "fanartpath" : fanart_path, 
                "custompath" : "", "trailerpath" : "", "romext" : ext, "gamesys" : launcher_gamesys, 
                "thumb" : "", "fanart" : "", "genre" : "", "release" : "", "studio" : "", 
                "plot" : "",  "lnk" : launcher_lnk, 
                "finished": False, "minimize" : False, 
                "roms_xml_file" : '' }
            self.launchers[launcherID] = launcherdata
            self._fs_write_catfile()
            xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self._path, categoryID))

            return True

    def _find_roms( self, is_launcher ):
        dialog = xbmcgui.Dialog()
        type = dialog.select(__language__( 30400 ), [__language__( 30401 ),__language__( 30402 ),__language__( 30403 ),__language__( 30404 ),__language__( 30405 )])
        type_nb = 0

        #Search by Title
        if (type == type_nb ):
            keyboard = xbmc.Keyboard("", __language__( 30036 ))
            keyboard.doModal()
            if (keyboard.isConfirmed()):
                search = keyboard.getText()
                if (is_launcher):
                    return "%s?%s/%s" % (self._path, search, SEARCH_ITEM_COMMAND), search
                else:
                    xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s/%s)" % (self._path, search, SEARCH_ITEM_COMMAND))

        #Search by Release Date
        type_nb = type_nb+1
        if (type == type_nb ):
            search = []
            search = _search_category(self,"release")
            dialog = xbmcgui.Dialog()
            selected = dialog.select(__language__( 30406 ), search)
            if (not selected == -1 ):
                if (is_launcher):
                    return "%s?%s/%s" % (self._path, search[selected], SEARCH_DATE_COMMAND), search[selected]
                else:
                    xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s/%s)" % (self._path, search[selected], SEARCH_DATE_COMMAND))

        #Search by System Platform
        type_nb = type_nb+1
        if (type == type_nb ):
            search = []
            search = _search_category(self,"gamesys")
            dialog = xbmcgui.Dialog()
            selected = dialog.select(__language__( 30407 ), search)
            if (not selected == -1 ):
                if (is_launcher):
                    return "%s?%s/%s" % (self._path, search[selected], SEARCH_PLATFORM_COMMAND), search[selected]
                else:
                    xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s/%s)" % (self._path, search[selected], SEARCH_PLATFORM_COMMAND))

        #Search by Studio
        type_nb = type_nb+1
        if (type == type_nb ):
            search = []
            search = _search_category(self,"studio")
            dialog = xbmcgui.Dialog()
            selected = dialog.select(__language__( 30408 ), search)
            if (not selected == -1 ):
                if (is_launcher):
                    return "%s?%s/%s" % (self._path, search[selected], SEARCH_STUDIO_COMMAND), search[selected]
                else:
                    xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s/%s)" % (self._path, search[selected], SEARCH_STUDIO_COMMAND))

        #Search by Genre
        type_nb = type_nb+1
        if (type == type_nb ):
            search = []
            search = _search_category(self,"genre")
            dialog = xbmcgui.Dialog()
            selected = dialog.select(__language__( 30409 ), search)
            if (not selected == -1 ):
                if (is_launcher):
                    return "%s?%s/%s" % (self._path, search[selected], SEARCH_GENRE_COMMAND), search[selected]
                else:
                    xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s/%s)" % (self._path, search[selected], SEARCH_GENRE_COMMAND))

    def _find_add_roms( self, search ):
        _find_category_roms( self, search, "name" )

    def _find_date_add_roms( self, search ):
        _find_category_roms( self, search, "release" )

    def _find_platform_add_roms( self, search ):
        _find_category_roms( self, search, "gamesys" )

    def _find_studio_add_roms( self, search ):
        _find_category_roms( self, search, "studio" )

    def _find_genre_add_roms( self, search ):
        _find_category_roms( self, search, "genre" )

    def _search_category(self, category):
        search = []
        if (len(self.launchers) > 0):
            for key in sorted(self.launchers.iterkeys()):
                if (len(self.launchers[key]["roms"]) > 0) :
                    for keyr in sorted(self.launchers[key]["roms"].iterkeys()):
                        if ( self.launchers[key]["roms"][keyr][category] == "" ):
                            search.append("[ %s ]" % __language__( 30410 ))
                        else:
                            search.append(self.launchers[key]["roms"][keyr][category])
        search = list(set(search))
        search.sort()
        return search

    def _find_category_roms(self, search, category ):
        #sorted by name
        if category == 'name' : 
            s_cmd = SEARCH_ITEM_COMMAND
        if category == 'release' :
            s_cmd = SEARCH_DATE_COMMAND
        if category == 'gamesys' :
            s_cmd = SEARCH_PLATFORM_COMMAND
        if category == 'studio' :
            s_cmd = SEARCH_STUDIO_COMMAND
        if category == 'genre' :
            s_cmd = SEARCH_GENRE_COMMAND
        s_url = 'plugin://plugin.program.advanced.launcher/?'+search+'/'+s_cmd
        if (len(self.launchers) > 0):
            rl = {}
            for launcherID in sorted(self.launchers.iterkeys()):
                selectedLauncher = self.launchers[launcherID]
                roms = selectedLauncher["roms"]
                notset = ("[ %s ]" % __language__( 30410 ))
                text = search.lower()
                empty = notset.lower()
                if (len(roms) > 0) :
                    #go through rom list and search for user input
                    for keyr in sorted(roms.iterkeys()):
                        rom = roms[keyr][category].lower()
                        if (rom == "") and (text == empty):
                            rl[keyr] = roms[keyr]
                            rl[keyr]["launcherID"] = launcherID
                        if category == 'name':
                            if (not rom.find(text) == -1):
                                rl[keyr] = roms[keyr]
                                rl[keyr]["launcherID"] = launcherID
                        else:
                            if (rom == text):
                                rl[keyr] = roms[keyr]
                                rl[keyr]["launcherID"] = launcherID
        #print the list sorted
        for key in sorted(rl.iterkeys()):
            self._add_rom(rl[key]["launcherID"], rl[key]["name"], rl[key]["filename"], rl[key]["gamesys"], rl[key]["thumb"], rl[key]["fanart"], rl[key]["trailer"], rl[key]["custom"], rl[key]["genre"], rl[key]["release"], rl[key]["studio"], rl[key]["plot"], rl[key]["finished"], rl[key]["altapp"], rl[key]["altarg"], len(rl), key, True, s_url)
        xbmcplugin.endOfDirectory( handle=int( self.addon_handle ), succeeded=True, cacheToDisc=False )

    #
    # NOTE In Python, objects methods can be defined outside the class definition!
    #      See https://docs.python.org/2/tutorial/classes.html#random-remarks
    #
    def _text_ROM_title_format(self, title):
        if self.settings[ "clean_title" ]:
            title = re.sub('\[.*?\]', '', title)
            title = re.sub('\(.*?\)', '', title)
            title = re.sub('\{.*?\}', '', title)
        new_title = title.rstrip()
        
        if self.settings[ "title_formating" ]:
            if (title.startswith("The ")): new_title = title.replace("The ","", 1)+", The"
            if (title.startswith("A ")): new_title = title.replace("A ","", 1)+", A"
            if (title.startswith("An ")): new_title = title.replace("An ","", 1)+", An"
        else:
            if (title.endswith(", The")): new_title = "The "+"".join(title.rsplit(", The", 1))
            if (title.endswith(", A")): new_title = "A "+"".join(title.rsplit(", A", 1))
            if (title.endswith(", An")): new_title = "An "+"".join(title.rsplit(", An", 1))

        return new_title

    #
    # A set of functions to help making plugin URLs
    # NOTE probably this can be implemented in a more elegant way with optinal arguments...
    #
    def _misc_url_RunPlugin(self, command, categoryID = None, launcherID = None, romID = None):
        if romID is not None:
            return 'XBMC.RunPlugin({0}?com={1}&catID={2}&launID={3}&romID={4})'.format(self._path, command, categoryID, launcherID, romID)
        elif launcherID is not None:
            return 'XBMC.RunPlugin({0}?com={1}&catID={2}&launID={3})'.format(self._path, command, categoryID, launcherID)
        elif categoryID is not None:
            return 'XBMC.RunPlugin({0}?com={1}&catID={2})'.format(self._path, command, categoryID)

        return 'XBMC.RunPlugin({0}?com={1})'.format(self._path, command)

    def _misc_url(self, command, categoryID = None, launcherID = None, romID = None):
        if romID is not None:
            return '{0}?com={1}&catID={2}&launID={3}&romID={4}'.format(self._path, command, categoryID, launcherID, romID)
        elif launcherID is not None:
            return '{0}?com={1}&catID={2}&launID={3}'.format(self._path, command, categoryID, launcherID)
        elif categoryID is not None:
            return '{0}?com={1}&catID={2}'.format(self._path, command, categoryID)

        return '{0}?com={1}'.format(self._path, command)

class MainGui( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        xbmcgui.WindowXMLDialog.__init__( self, *args, **kwargs )
        xbmc.executebuiltin( "Skin.Reset(AnimeWindowXMLDialogClose)" )
        xbmc.executebuiltin( "Skin.SetBool(AnimeWindowXMLDialogClose)" )
        self.listing = kwargs.get( "listing" )

    def onInit(self):
        try :
            self.img_list = self.getControl(6)
            self.img_list.controlLeft(self.img_list)
            self.img_list.controlRight(self.img_list)
            self.getControl(3).setVisible(False)
        except :
            print_exc()
            self.img_list = self.getControl(3)

        self.getControl(5).setVisible(False)

        for index, item in enumerate(self.listing):
            listitem = xbmcgui.ListItem( item[2] )
            listitem.setIconImage( item[1] )
            listitem.setLabel2( item[0] )
            
            self.img_list.addItem( listitem )
        self.setFocus(self.img_list)

    def onAction(self, action):
        #Close the script
        if action == 10 :
            self.close()

    def onClick(self, controlID):
        #action sur la liste
        if controlID == 6 or controlID == 3:
            #Renvoie l'item selectionne
            num = self.img_list.getSelectedPosition()
            self.selected_url = self.img_list.getSelectedItem().getLabel2()
            self.close()

    def onFocus(self, controlID):
        pass

def MyDialog(img_list):
    w = MainGui( "DialogSelect.xml", BASE_PATH, listing=img_list )
    w.doModal()
    try:
        return w.selected_url
    except:
        print_exc()
        return False
    del w

def get_encoding():
    try:
        return sys.getfilesystemencoding()
    except (UnicodeEncodeError, UnicodeDecodeError):
        return "utf-8"

def update_cache(file_path):
    cached_thumb = Thumbnails().get_cached_covers_thumb( file_path ).replace("tbn" , os.path.splitext(file_path)[-1][1:4])
    try:
        shutil.copy2( file_path.decode(get_encoding(),'ignore'), cached_thumb.decode(get_encoding(),'ignore') )
    except OSError:
        xbmc_notify('Advanced Emulator Launcher'+" - "+__language__( 30612 ), __language__( 30608 ),3000)
    xbmc.executebuiltin("XBMC.ReloadSkin()")

def download_img(img_url,file_path):
    req = urllib2.Request(img_url)
    req.add_unredirected_header('User-Agent', getUserAgent())
    f = open(file_path,'wb')
    f.write(urllib2.urlopen(req).read())
    f.close()                                

def download_page(url):
    req = urllib2.Request(url)
    req.add_unredirected_header('User-Agent', getUserAgent())
    return urllib2.urlopen(req)

def clean_filename(title):
    title = re.sub('\[.*?\]', '', title)
    title = re.sub('\(.*?\)', '', title)
    title = re.sub('\{.*?\}', '', title)
    title = title.replace('_',' ')
    title = title.replace('-',' ')
    title = title.replace(':',' ')
    title = title.replace('.',' ')
    title = title.rstrip()
    return title

def base_filename(filename):
    filename = re.sub('(\[.*?\]|\(.*?\)|\{.*?\})', '', filename)
    filename = re.sub('(\.|-| |_)cd\d+$', '', filename)
    return filename.rstrip()

def toogle_fullscreen():
    # Frodo & + compatible
    xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Input.ExecuteAction","params":{"action":"togglefullscreen"},"id":"1"}')

#
# Generates a random an unique MD5 hash and returns a string with the hash
#
def misc_generate_random_SID():
    t1 = time.time()
    t2 = t1 + random.getrandbits(32)
    base = hashlib.md5( str(t1 + t2) )
    sid = base.hexdigest()

    return sid

def get_game_system_list():
    platforms = []
    try:
        rootDir = __settings__.getAddonInfo('path')
        if rootDir[-1] == ';':rootDir = rootDir[0:-1]
        resDir = os.path.join(rootDir, 'resources')
        scrapDir = os.path.join(resDir, 'scrapers')
        csvfile = open( os.path.join(scrapDir, 'gamesys'), "rb")
        for line in csvfile.readlines():
            result = line.replace('\n', '').replace('"', '').split(',')
            platforms.append(result[0])
        platforms.sort()
        csvfile.close()
        return platforms
    except:
        return platforms

def get_favourites_list():
    favourites = []
    fav_names = []
    if os.path.isfile( FAVOURITES_PATH ):
        fav_xml = parse( FAVOURITES_PATH )
        fav_doc = fav_xml.documentElement.getElementsByTagName( 'favourite' )
        for count, favourite in enumerate(fav_doc):
            try:
                fav_icon = favourite.attributes[ 'thumb' ].nodeValue
            except:
                fav_icon = "DefaultProgram.png"
            favourites.append((favourite.childNodes[ 0 ].nodeValue.encode('utf8','ignore'), fav_icon.encode('utf8','ignore'), favourite.attributes[ 'name' ].nodeValue.encode('utf8','ignore')))
            fav_names.append(favourite.attributes[ 'name' ].nodeValue.encode('utf8','ignore'))
    return favourites, fav_names

# --- main ----------------------------------------------------------------------------------------
if __name__ == "__main__":
    Main()
