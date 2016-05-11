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
import sys, os, shutil, fnmatch, string
import re, urllib, urllib2, urlparse, socket, exceptions

# --- Kodi stuff ---
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

# --- Modules/packages in this plugin ---
import resources.subprocess_hack
from resources.disk_IO import *
from resources.net_IO import *
from resources.utils import *
from resources.scrap import *

# --- Addon object (used to access settings) ---
addon_obj      = xbmcaddon.Addon()
__addon_id__   = addon_obj.getAddonInfo('id')
__addon_name__ = addon_obj.getAddonInfo('name')
__version__    = addon_obj.getAddonInfo('version')
__author__     = addon_obj.getAddonInfo('author')
__profile__    = addon_obj.getAddonInfo('profile')
__type__       = addon_obj.getAddonInfo('type')

# --- Addon paths and constants definition ---
# _FILE_PATH is a filename | _DIR is a directory (with trailing /)
PLUGIN_DATA_DIR      = xbmc.translatePath(os.path.join('special://profile/addon_data', 'plugin.program.advanced.emulator.launcher'))
BASE_DIR             = xbmc.translatePath(os.path.join('special://', 'profile'))
HOME_DIR             = xbmc.translatePath(os.path.join('special://', 'home'))
KODI_FAV_FILE_PATH   = xbmc.translatePath( 'special://profile/favourites.xml' )
ADDONS_DIR           = xbmc.translatePath(os.path.join(HOME_DIR, 'addons'))
CURRENT_ADDON_DIR    = xbmc.translatePath(os.path.join(ADDONS_DIR, 'plugin.program.advanced.emulator.launcher'))
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

# --- Initialise log system ---
# Synchronise this with user's preferences in Kodi when loading Kodi settings.
# Anyway, default to this level if settings are not loaded for some reason.
set_log_level(LOG_DEBUG)

# --- Main code ---
class Main:
    settings   = {}
    categories = {}
    launchers  = {}
    roms       = {}
    scraper_metadata = None
    scraper_thumb    = None
    scraper_fanart   = None

    def __init__(self, *args, **kwargs):
        # --- Fill in settings dictionary using addon_obj.getSetting() ---
        self._get_settings()

        # --- Some debug stuff for development ---
        log_debug('---------- Called AEL addon.py Main() constructor ----------')
        # log_debug(sys.version)
        log_debug('__addon_id__   {}'.format(__addon_id__))
        log_debug('__addon_name__ {}'.format(__addon_name__))
        log_debug('__version__    {}'.format(__version__))
        log_debug('__author__     {}'.format(__author__))
        log_debug('__profile__    {}'.format(__profile__))
        log_debug('__type__       {}'.format(__type__))
        for i in range(len(sys.argv)):
            log_debug('sys.argv[{0}] = "{1}"'.format(i, sys.argv[i]))
        # log_debug('CATEGORIES_FILE_PATH = "{}"'.format(CATEGORIES_FILE_PATH))
        # log_debug('FAVOURITES_FILE_PATH = "{}"'.format(FAVOURITES_FILE_PATH))

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

        # ~~~~~ Process URL commands ~~~~~
        # Interestingly, if plugin is called as type executable then args is empty.
        # However, if plugin is called as type video then Kodi adds the following
        # even for the first call: 'content_type': ['video']
        self._content_type = args['content_type'] if 'content_type' in args else None
        log_debug('content_type = {}'.format(self._content_type))

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

        # --- WORKAROUND ---
        # When the addon is installed and the file categories.xml does not exist, just
        # create an empty one with a default launcher. Later on, when I am more familiar
        # with the addon add a welcome wizard or something similar.
        #
        # Create a default categories.xml file if does not exist yet (plugin just installed)
        if not os.path.isfile(CATEGORIES_FILE_PATH):
            log_kodi_dialog_OK('Advanced Emulator Launcher',
                               'It looks it is the first time you run AEL!',
                               'Creating a default categories.xml')
            self._cat_create_default()
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

        # Load categories.xml and fill categories and launchers dictionaries.
        (self.categories, self.launchers) = fs_load_catfile(CATEGORIES_FILE_PATH)

        # --- Load scrapers ---
        self._load_scrapers()

        # If no com parameter display categories. Display categories listbox (addon root directory)
        if 'com' not in args:
            log_debug('AEL Root Folder >> Categories list <<')
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
            log_kodi_dialog_OK('ERROR', 'DELETE_CATEGORY not implemented yet')

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
            log_kodi_dialog_OK('ERROR', 'DELETE_LAUNCHER not implemented yet')
            # if (rom == REMOVE_COMMAND):
            #    self._remove_launcher(launcher)

        elif command == 'SHOW_ROMS':
            launcherID = args['launID'][0]
            # User clicked on a launcher. For executable launchers run the executable.
            # For emulator launchers show roms.
            if self.launchers[launcherID]["rompath"] == '':
                log_debug('SHOW_ROMS | Launcher rompath is empty. Assuming launcher is standalone.')
                log_debug('SHOW_ROMS | Calling _run_launcher()')
                self._run_standalone_launcher(args['catID'][0], args['launID'][0])
            else:
                log_debug('SHOW_ROMS | Calling _gui_render_roms()')
                self._gui_render_roms(args['catID'][0], args['launID'][0])

        elif command == 'ADD_ROMS':
            self._command_add_roms(args['launID'][0])

        elif command == 'EDIT_ROM':
            self._command_edit_rom(args['catID'][0], args['launID'][0], args['romID'][0])

        elif command == 'DELETE_ROM':
             self._command_remove_rom(args['catID'][0], args['launID'][0], args['romID'][0])

        elif args['com'][0] == 'LAUNCH_ROM':
            self._run_rom(args['catID'][0], args['launID'][0], args['romID'][0])

        elif command == 'ADD_TO_FAV':
            self._command_add_to_favourites(args['catID'][0], args['launID'][0], args['romID'][0])

        elif command == 'DELETE_FROM_FAV':
            kodi_dialog_OK('AEL', 'Implement me!')
            # self._command_add_to_favourites(args['catID'][0], args['launID'][0], args['romID'][0])

        # This command is issued when user clicks on "Search" on the context menu of a launcher
        # in the launchers view, or context menu inside a launcher. User is asked to enter the
        # search string and the field to search (name, category, etc.)
        elif command == 'SEARCH_LAUNCHER':
            self._command_search_launcher(args['catID'][0], args['launID'][0])

        elif command == 'EXEC_SEARCH_LAUNCHER':
            self._command_execute_search_launcher(args['catID'][0], args['launID'][0], 
                                                  args['search_type'][0], args['search_string'][0])

        else:
            log_kodi_dialog_OK('Advanced Emulator Launcher - ERROR', 'Unknown command {0}'.format(args['com'][0]) )            

    #
    # Get Addon Settings
    #
    def _get_settings( self ):
        # Get the users preference settings
        self.settings = {}
        
        # Scanner settings
        self.settings["scan_recursive"]         = True if addon_obj.getSetting("scan_recursive") == "true" else False
        self.settings["scan_ignore_title"]      = True if addon_obj.getSetting("scan_ignore_title") == "true" else False
        self.settings["scan_clean_tags"]        = True if addon_obj.getSetting("scan_clean_tags") == "true" else False
        self.settings["scan_title_formatting"]  = True if addon_obj.getSetting("scan_title_formatting") == "true" else False
        self.settings["scan_ignore_bios"]       = True if addon_obj.getSetting("scan_ignore_bios") == "true" else False
        
        self.settings["scan_metadata_policy"]   = int(addon_obj.getSetting("scan_metadata_policy"))
        self.settings["scan_thumb_policy"]      = int(addon_obj.getSetting("scan_thumb_policy"))
        self.settings["scan_fanart_policy"]     = int(addon_obj.getSetting("scan_fanart_policy"))
        self.settings["metadata_scraper"]       = int(addon_obj.getSetting("metadata_scraper"))
        self.settings["thumb_scraper"]          = int(addon_obj.getSetting("thumb_scraper"))
        self.settings["fanart_scraper"]         = int(addon_obj.getSetting("fanart_scraper"))
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
        
        # self.settings["game_region"]          = ['World', 'Europe', 'Japan', 'USA'][int(addon_obj.getSetting('game_region'))]

        # --- Dump settings for DEBUG ---
        log_debug('Settings dump BEGIN')
        for key in sorted(self.settings):
            log_debug('{} --> {:10s} {:}'.format(key.rjust(21), str(self.settings[key]), type(self.settings[key])))
        log_debug('Settings dump END')


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


    # Creates default categories data struct
    # CAREFUL deletes current categories!
    # From _load_launchers
    # Else create the default category
    # self.categories["default"] = {"id":"default", "name":"Default", "thumb":"", "fanart":"", "genre":"", "plot":"", "finished":"false"}
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
        category['id'] = category_key
        self.categories = {}
        self.categories[category_key] = category

    #
    # Checks if the category is empty (no launchers defined)
    #
    def _cat_is_empty(self, categoryID):
        empty_category = True
        for cat in self.launchers.iterkeys():
            if self.launchers[cat]['category'] == categoryID:
                empty_category = False

        return empty_category

    # -------------------------------------------------------------------------
    # Image semiautomatic scrapers
    # User is presented with a list of scrapped images and chooses the best one.
    # -------------------------------------------------------------------------
    def _gui_scrap_image_semiautomatic(self, object_kind, objects, objectID, artwork_path):
        keyboard = xbmc.Keyboard(objects[objectID]["name"], 'Enter the file title to search...')
        keyboard.doModal()
        if not keyboard.isConfirmed():
            return
        

        log_kodi_notify('Advanced Emulator Launcher', 
                        'Importing ROM %s thumb from %s' % (objects[objectID]["name"], 
                                                           (self.settings[ "thumbs_scraper" ]).encode('utf-8', 'ignore')), 300000)

        # Call scraper and get a list of images
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        region   = self.settings["game_region"]
        img_size = self.settings[ "thumb_image_size" ]
        covers   = self.scraper_thumb.get_image_list(search_str, objects[objectID]["gamesys"], region, img_size)
        xbmc.executebuiltin("Dialog.Close(busydialog)")

        if not covers:
            log_kodi_dialog_OK('Advanced Emulator Launcher', 'No thumb found for %s' % (objects[objectID]["name"]))
            return

        # Show a Window with the current image and the found images so the
        # user can chose. It is like a Dialog.select but intead of text
        # there is an image on each row of the select control.
        nb_images = len(covers)
        log_kodi_notify('Advanced Emulator Launcher', '%s thumbs for %s' % (nb_images, objects[objectID]["name"]))
        covers.insert(0, (objects[objectID]["thumb"], objects[objectID]["thumb"], 'Current image'))
        self.image_url = gui_show_image_select(covers)

        # No image selected
        if not self.image_url:
            return
        # User chose same image as it was
        if self.image_url == objects[objectID]["thumb"]:
            return
        # Call scraper again to get resolved URL.
        # Note that new AEL scrapers do not need this.
        img_url = self._get_thumbnail(self.image_url)
        if img_url == '':
            log_kodi_notify('Advanced Emulator Launcher', 'No thumb found for %s' % (objects[objectID]["name"]))
            return

        # Get image extenstion
        img_ext = os.path.splitext(img_url)[-1][0:4]
        if img_ext == '':
            return

        # Get filename where we should place the image
        filename = objects[objectID]["filename"]
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
        log_kodi_notify('Advanced Emulator Launcher', 'Downloading thumb...', 300000)

        # Download selected image
        try:
            download_img(img_url, file_path)
            
            req = urllib2.Request(img_url)
            req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
            f = open(file_path, 'wb')
            f.write(urllib2.urlopen(req).read())
            f.close()

            if objects[objectID]["thumb"] != "":
                _update_cache(file_path)

            objects[objectID]["thumb"] = file_path
            self._save_launchers()
            log_kodi_notify('Advanced Emulator Launcher', 'Thumb has been updated')
        except socket.timeout:
            log_kodi_notify('Advanced Emulator Launcher', 'Cannot download image (Timeout)')
        except exceptions.IOError:
            log_kodi_notify('Advanced Emulator Launcher', 'Filesystem error (IOError)')
        
        
        
        xbmc.executebuiltin("Container.Update")
        
    # ---------------------------------------------------------------------------------------------
    # Metadata scrapers
    # ---------------------------------------------------------------------------------------------
    def _gui_scrap_rom_metadata(self, launcher, rom):
        # Edition of the rom name
        title = os.path.basename(roms[romID]["filename"]).split(".")[0]
        if self.launchers[launcher]["application"].lower().find('mame') > 0 or \
           self.settings[ "datas_scraper" ] == 'arcadeHITS':
            keyboard = xbmc.Keyboard(title, 'Enter the MAME item filename to search...')
        else:
            keyboard = xbmc.Keyboard(roms[romID]["name"], 'Enter the file title to search...')
        keyboard.doModal()
        if keyboard.isConfirmed():
            self._scrap_rom_algo(launcher, rom, keyboard.getText())

            # Search game title
            results,display = self._get_games_list(title)
            if display:
                # Display corresponding game list found
                dialog = xbmcgui.Dialog()
                # Game selection
                selectgame = dialog.select('Select a item from %s' % ( self.settings[ "datas_scraper" ] ), display)
                if (not selectgame == -1):
                    if ( self.settings[ "ignore_title" ] ):
                        roms[romID]["name"] = title_format(self,title)
                    else:
                        roms[romID]["name"] = title_format(self,results[selectgame]["title"])
                    gamedata = self._get_game_data(results[selectgame]["id"])
                    roms[romID]["genre"] = gamedata["genre"]
                    roms[romID]["release"] = gamedata["release"]
                    roms[romID]["studio"] = gamedata["studio"]
                    roms[romID]["plot"] = gamedata["plot"]
            else:
                log_kodi_notify('Advanced Emulator Launcher', 'No data found')

            self._save_launchers()
        xbmc.executebuiltin("Container.Update")

    #
    # Scrap standalone launcher (typically a game) metadata
    #
    def _gui_scrap_launcher_metadata(self, launcherID):
        # Edition of the launcher name
        keyboard = xbmc.Keyboard(self.launchers[launcherID]["name"], 'Enter the launcher search string ...')
        keyboard.doModal()
        if keyboard.isConfirmed():
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
                    self.launchers[launcherID]["genre"]   = gamedata["genre"]
                    self.launchers[launcherID]["release"] = gamedata["release"]
                    self.launchers[launcherID]["studio"]  = gamedata["studio"]
                    self.launchers[launcherID]["plot"]    = gamedata["plot"]
            else:
                log_kodi_notify('Advanced Emulator Launcher', 'No data found')

            # Save XML data to disk
            self._save_launchers()
        xbmc.executebuiltin("Container.Update")

    #
    # Edit category/launcher/rom thumbnail/fanart.
    #
    # NOTE Interestingly, if thumb/fanart are linked from outside ~/.kodi, Kodi automatically reloads
    #      the image cache. That is the case when a local image is selected.
    #      However, if an image is imported and copied to ~/.kodi/userdata/etc., then Kodi image
    #      cache is not updated any more!
    #
    def _gui_edit_image(self, image_kind, objects_kind, objects, objectID):
        dialog = xbmcgui.Dialog()

        # Semiautomatic image scrapping
        type2 = dialog.select('Change Thumbnail Image', 
                                ['Select Local Image',
                                 'Import Local Image (Copy and Rename)',
                                 'Scrape Image from {0}'.format(self.scraper_thumb.fancy_name) ])
        # Link to an image
        if type2 == 0:
            imagepath = artwork_path if object_dic["thumb"] == "" else object_dic["thumb"]
            image = xbmcgui.Dialog().browse(2, 'Select thumbnail image', "files", ".jpg|.jpeg|.gif|.png", 
                                            True, False, os.path.join(imagepath))
            if not image or not os.path.isfile(image):
                return

            # Update object and save XML
            if object_kind == KIND_CATEGORY:
                log_debug('_gui_edit_thumbnail() Object is categoryID = {0}'.format(object_dic['id']))
                self.categories[object_dic['id']]["thumb"] = image
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            elif object_kind == KIND_LAUNCHER:
                log_debug('_gui_edit_thumbnail() Object is launcherID = {0}'.format(object_dic['id']))
                self.launchers[object_dic['id']]["thumb"] = image
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            elif object_kind == KIND_ROM:
                log_debug('_gui_edit_thumbnail() Object is romID = {0}'.format(object_dic['id']))
                self.roms[object_dic['id']]["thumb"] = image
                fs_write_ROM_XML_file(rom_xml_file, roms, launcher)
            log_kodi_notify('AEL', 'Thumb has been updated')
            log_info('Selected Thumb image "{0}"'.format(image))

            # --- Update Kodi image cache ---
            # if object_dic["thumb"] != "":
            #     update_kodi_image_cache(image)

        # Import an image
        elif type2 == 1:
            imagepath = artwork_path if object_dic["thumb"] == "" else object_dic["thumb"]
            image = xbmcgui.Dialog().browse(2, 'Select thumbnail image', "files", ".jpg|.jpeg|.gif|.png",
                                            True, False, os.path.join(imagepath))
            if not image or not os.path.isfile(image):
                return

            img_ext = os.path.splitext(image)[-1][0:4]
            log_debug('_gui_edit_thumbnail() image   = "{0}"'.format(image))
            log_debug('_gui_edit_thumbnail() img_ext = "{0}"'.format(img_ext))
            if img_ext == '':
                log_kodi_notify_warn('AEL', 'Cannot determine image file extension')
                return

            object_name = object_dic['name']
            file_basename = object_name
            file_path = os.path.join(artwork_path, os.path.basename(object_name) + '_thumb' + img_ext)
            log_debug('_gui_edit_thumbnail() object_name   = "{0}"'.format(object_name))
            log_debug('_gui_edit_thumbnail() file_basename = "{0}"'.format(file_basename))
            log_debug('_gui_edit_thumbnail() file_path     = "{0}"'.format(file_path))

            # If user press ESC in the file browser dialog the the same file used as initial file is chosen.
            # In that case do nothing and return.
            if image == file_path:
                return
            try:
                shutil.copy2(image.decode(get_encoding(), 'ignore') , file_path.decode(get_encoding(), 'ignore'))
            except OSError:
                log_kodi_notify_warn('AEL', 'OSError when copying image')

            # Update object and save XML
            if object_kind == KIND_CATEGORY:
                log_debug('_gui_edit_thumbnail() Object is categoryID = {0}'.format(object_dic['id']))
                self.categories[object_dic['id']]["thumb"] = file_path
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            elif object_kind == KIND_LAUNCHER:
                log_debug('_gui_edit_thumbnail() Object is launcherID = {0}'.format(object_dic['id']))
                self.launchers[object_dic['id']]["thumb"] = file_path
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            elif object_kind == KIND_ROM:
                log_debug('_gui_edit_thumbnail() Object is romID = {0}'.format(object_dic['id']))
                self.roms[object_dic['id']]["thumb"] = file_path
                fs_write_ROM_XML_file()
            log_kodi_notify('AEL', 'Thumb has been updated')
            log_info('Copied Thumb image   "{0}"'.format(image))
            log_info('Into                 "{0}"'.format(file_path))
            log_info('Selected Thumb image "{0}"'.format(file_path))

            # --- Update Kodi image cache ---
            # Cases some problems at the moment...
            # if object_dic["thumb"] != "":
            #     update_kodi_image_cache(image)

        # Manual scrape a list of images
        elif type2 == 2:
            self._scrap_thumb_rom(object_kind, objects, objectID, artwork_path)

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
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
        else:
            ret = dialog.yesno('AEL',
                               'Category "%s" contains %s launchers.' % (self.categories[categoryID]["name"], len(launcher_list)),
                               'Are you sure you want to delete "%s" ?' % self.categories[categoryID]["name"])
            if ret:
                self.categories.pop(categoryID)
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
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
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            else:
                log_kodi_dialog_OK('AEL Information', 
                                   'Category name "{0}" not changed.'.format(self.categories[categoryID]["name"]))
        # Edition of the category genre
        elif type2 == 1:
            keyboard = xbmc.Keyboard(self.categories[categoryID]["genre"], 'Edit Genre')
            keyboard.doModal()
            if keyboard.isConfirmed():
                self.categories[categoryID]["genre"] = keyboard.getText()
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            else:
                log_kodi_dialog_OK('AEL Information', 
                                   'Category genre "{0}" not changed.'.format(self.categories[categoryID]["genre"]))
        # Edition of the plot (description)
        elif type2 == 2:
            keyboard = xbmc.Keyboard(self.categories[categoryID]["description"], 'Edit Description')
            keyboard.doModal()
            if keyboard.isConfirmed():
                self.categories[categoryID]["description"] = keyboard.getText()
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            else:
                log_kodi_dialog_OK('AEL Information', 
                                   'Category plot "{0}" not changed.'.format(self.categories[categoryID]["description"]))
        # Import category description
        elif type2 == 3:
            text_file = xbmcgui.Dialog().browse(1, 'Select description file (txt|dat)', "files", ".txt|.dat", False, False)
            if os.path.isfile(text_file) == True:
                text_plot = open(text_file, 'rt')
                self.categories[categoryID]["description"] = text_plot.read()
                text_plot.close()
                fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            else:
                log_kodi_dialog_OK('AEL Information', 
                                   'Category plot "{0}" not changed.'.format(self.categories[categoryID]["description"]))

    def _command_edit_category(self, categoryID):
        # Shows a select box with the options to edit
        dialog = xbmcgui.Dialog()
        finished_display = 'Status: Finished' if self.categories[categoryID]["finished"] == True else 'Status: Unfinished'
        type = dialog.select('Select action for category {0}'.format(self.categories[categoryID]["name"]), 
                             ['Edit Title/Genre/Description', 'Edit Thumbnail image', 'Edit Fanart image', 
                              finished_display, 'Delete category'])
        # Edit metadata
        if type == 0:
            self._gui_edit_category_metadata(categoryID)

        # Edit Thumbnail image
        elif type == 1:
            self._gui_edit_thumbnail(KIND_CATEGORY, self.categories[categoryID], DEFAULT_THUMB_DIR)

        # Launcher Fanart menu option
        elif type == 2:
            self._gui_edit_fanart(KIND_CATEGORY, self.categories[categoryID], DEFAULT_FANART_DIR)

        # Category status
        elif type == 3:
            finished = self.categories[categoryID]["finished"]
            finished = False if finished else True
            finished_display = 'Finished' if finished == True else 'Unfinished'
            self.categories[categoryID]["finished"] = finished
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            log_kodi_dialog_OK('AEL Information', 
                               'Category "{0}" status is now {1}'.format(self.categories[categoryID]["name"], finished_display))
        elif type == 4:
            self._gui_remove_category(categoryID)

        elif type == -1:
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

        # Return to the category directory
        xbmc.executebuiltin("Container.Refresh")

    def _command_add_new_category(self):
        dialog = xbmcgui.Dialog()
        keyboard = xbmc.Keyboard("", 'New Category Name')
        keyboard.doModal()
        if not keyboard.isConfirmed():
            return False

        categoryID = misc_generate_random_SID()
        categorydata = {"id" : categoryID, "name" : keyboard.getText(), 
                        "thumb" : "", "fanart" : "", "genre" : "", "description" : "", "finished" : False}
        self.categories[categoryID] = categorydata
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
        xbmc.executebuiltin("Container.Refresh")
        log_kodi_notify('AEL' , 'Category {0} created'.format(categorydata["name"]), 3000)

        return True

    #
    # Removes ROMs for a given launcher. Note this function will never be called for standalone launchers.
    #
    def _gui_empty_launcher(self, launcherID):
        roms = fs_load_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'])
        num_roms = len(roms)
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno('Advanced Emulator Launcher', 
                           'Launcher "{0}" has {1} ROMs'.format(self.launchers[launcherID]["name"], num_roms),
                           'Are you sure you want to delete it?')
        if ret:
            # Just remove XML file and set roms_xml_file to ''
            roms_xml_file = self.launchers[launcherID]["roms_xml_file"]
            if roms_xml_file == '' or rompath == '':
                log_debug('Launcher is empty. No ROMs XML to remove')
            else:
                log_debug('Removing ROMs XML "{0}"'.format(roms_xml_file))
                try:
                    os.remove(roms_xml_file)
                except OSError:
                    log_error('_gui_empty_launcher() OSError exception deleting "{0}"'.format(roms_xml_file))
                    log_kodi_notify_warning('AEL', 'OSError exception deleting ROMs XML')
            self.launchers[launcherID]["roms_xml_file"] = ''
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            xbmc.executebuiltin("Container.Update")

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
                    log_kodi_notify_warning('AEL', 'OSError exception deleting ROMs XML')
            categoryID = self.launchers[launcherID]["category"]
            self.launchers.pop(launcherID)
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            if self._cat_is_empty(categoryID):
                xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self.base_url))
            else:
                xbmc.executebuiltin("Container.Update")

    def _command_edit_launcher(self, launcherID):
        dialog = xbmcgui.Dialog()
        title = os.path.basename(self.launchers[launcherID]["name"])
        finished_display = 'Status : Finished' if self.launchers[launcherID]["finished"] == True else 'Status : Unfinished'

        if self.launchers[launcherID]["rompath"] == "":
            type = dialog.select('Select Action for %s' % title, 
                                 ['Modify Metadata ...', 'Change Thumbnail Image ...', 'Change Fanart Image ...', 
                                  'Change Category: %s' % self.categories[self.launchers[launcherID]["category"]]['name'],
                                  finished_display, 'Advanced Modifications ...', 'Delete'])
        else:
            type = dialog.select('Select Action for %s' % title, 
                                 ['Modify Metadata ...', 'Change Thumbnail Image ...', 'Change Fanart Image ...',
                                  'Change Category: %s' % self.categories[self.launchers[launcherID]["category"]]['name'],
                                  finished_display, 'Manage ROM List ...', 'Advanced Modifications ...', 'Delete'])

        # Edition of the launcher metadata
        type_nb = 0
        if type == type_nb:
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Modify Launcher Metadata',
                                  ['Scrape from {0}'.format(self.scraper_metadata.get_fancy_name()),
                                   'Edit Title: %s' % self.launchers[launcherID]["name"],
                                   'Edit Platform: %s' % self.launchers[launcherID]["gamesys"],
                                   'Edit Release Date: %s' % self.launchers[launcherID]["release"],
                                   'Edit Studio: %s' % self.launchers[launcherID]["studio"],
                                   'Edit Genre: %s' % self.launchers[launcherID]["genre"],
                                   'Edit Description: %s' % self.launchers[launcherID]["plot"][0:20],
                                   'Import Description from TXT file ...',
                                   'Import metadata from NFO file ...', 'Save metadata to NFO file'])
            # Edition of the launcher name
            if type2 == 0:
                log_kodi_dialog_OK('AEL', 'Online scraping not supported yet. Sorry.')
                return
                # self._scrap_launcher_metadata(launcherID)
            # Edition of the launcher name
            elif type2 == 1:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["name"], 'Edit title')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    title = keyboard.getText()
                    if title == "" :
                        title = self.launchers[launcherID]["name"]
                    self.launchers[launcherID]["name"] = title.rstrip()
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            # Selection of the launcher game system
            elif type2 == 2:
                dialog = xbmcgui.Dialog()
                platforms = emudata_game_system_list()
                gamesystem = dialog.select('Select the platform', platforms)
                if not gamesystem == -1:
                    self.launchers[launcherID]["gamesys"] = platforms[gamesystem]
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            # Edition of the launcher release date (year)
            elif type2 == 3:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["release"], 'Edit release year')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    self.launchers[launcherID]["release"] = keyboard.getText()
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            # Edition of the launcher studio name
            elif type2 == 4:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["studio"], 'Edit studio')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    self.launchers[launcherID]["studio"] = keyboard.getText()
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            # Edition of the launcher genre
            elif type2 == 5:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["genre"], 'Edit genre')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    self.launchers[launcherID]["genre"] = keyboard.getText()
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

            # Edit launcher description (plot)
            elif type2 == 6:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["plot"], 'Edit descripion')
                keyboard.doModal()
                if keyboard.isConfirmed():
                    self.launchers[launcherID]["plot"] = keyboard.getText()
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

            # Import of the launcher descripion (plot)
            elif type2 == 7:
                text_file = xbmcgui.Dialog().browse(1, 'Select description file (TXT|DAT)', "files", ".txt|.dat", 
                                                    False, False, self.launchers[launcherID]["application"])
                if os.path.isfile(text_file) == True:
                    text_plot = open(text_file, 'r')
                    str = text_plot.read()
                    text_plot.close()
                    self.launchers[launcherID]["plot"] = str
                    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

            # Import launcher from NFO file
            elif type2 == 8:
                log_kodi_dialog_OK('AEL', 'Not implemented yet!')
                # self._import_launcher_nfo(launcherID)
                
            # Export launcher to NFO file
            elif type2 == 9:
                log_kodi_dialog_OK('AEL', 'Not implemented yet!')
                # self._export_launcher_nfo(launcherID)

        # Launcher Thumbnail menu option
        type_nb = type_nb + 1
        if type == type_nb:
            self._gui_edit_thumbnail(KIND_LAUNCHER, self.launchers[launcherID], DEFAULT_THUMB_DIR)

        # Launcher Fanart menu option
        type_nb = type_nb + 1
        if type == type_nb:
            self._gui_edit_fanart(KIND_LAUNCHER, self.launchers[launcherID], DEFAULT_FANART_DIR)

        # Change launcher's category
        type_nb = type_nb + 1
        if type == type_nb:
            current_category = self.launchers[launcherID]["category"]
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

        # Launcher status (finished [bool])
        type_nb = type_nb + 1
        if type == type_nb:
            finished = self.launchers[launcherID]["finished"]
            finished = False if finished else True
            finished_display = 'Finished' if finished == True else 'Unfinished'
            self.launchers[launcherID]["finished"] = finished
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            log_kodi_dialog_OK('AEL Information', 
                               'Launcher "{0}" status is now {1}'.format(self.launchers[launcherID]["name"], finished_display))

        # Launcher's Manage ROMs menu option
        # ONLY for ROM launchers, not for standalone launchers
        if self.launchers[launcherID]["rompath"] != "":
            type_nb = type_nb + 1
            if type == type_nb:
                dialog = xbmcgui.Dialog()
                hasNoIntro_file = True if self.launchers[launcherID]["nointro_xml_file"] else False
                if not hasNoIntro_file:
                    type2 = dialog.select('Manage Items List', 
                                          ['Add No-Intro XML DAT',
                                           'Import ROMs metadata from NFO files',
                                           'Export ROMs metadata to NFO files', 
                                           'Clear ROMs from launcher' ])
                else:
                    nointro_xml_file = self.launchers[launcherID]["nointro_xml_file"]
                    type2 = dialog.select('Manage Items List',
                                         ['Delete No-Intro DAT: {}'.format(nointro_xml_file),
                                          'Import ROMs metadata from NFO files',
                                          'Export ROMs metadata to NFO files', 
                                          'Clear ROMs from launcher' ])
                # Add/Delete No-Intro XML parent-clone DAT
                if type2 == 0:
                    if hasNoIntro_file:
                        dialog = xbmcgui.Dialog()
                        ret = dialog.yesno('AEL', 'Delete No-Intro DAT file?')
                        if ret:
                            self.launchers[launcherID]["nointro_xml_file"] = ''
                            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
                            log_kodi_dialog_OK('AEL', 'Rescan your ROMs to remove No-Intro tags.')
                    else:
                        # Browse for No-Intro file
                        # BUG For some reason *.dat files are not shown on the dialog, but XML files are OK!!!
                        dat_file = xbmcgui.Dialog().browse(1, 'Select No-Intro XML DAT (XML|DAT)', 'files', '.dat|.xml')
                        if os.path.isfile(dat_file) == True:
                            self.launchers[launcherID]["nointro_xml_file"] = dat_file
                            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
                            log_kodi_dialog_OK('AEL', 'DAT file successfully added. Rescan your ROMs to audit them.')

                # Import Items list form NFO files
                elif type2 == 1:
                    # Load ROMs, iterate and import NFO files
                    roms = fs_load_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'])
                    for rom in roms:
                        fs_import_rom_nfo(launcherID, rom)

                    # Write ROMs XML to disk
                    
                # Export Items list to NFO files
                elif type2 == 2:
                    # Load ROMs, iterate and write NFO files
                    roms = fs_load_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'])
                    for rom in roms:
                        fs_export_rom_nfo(launcherID, rom)

                # Empty Launcher menu option
                elif type2 == 3:
                    self._gui_empty_launcher(launcherID)

        # Launcher Advanced menu option
        type_nb = type_nb + 1
        if type == type_nb:
            lnk_str = 'ON' if self.launchers[launcherID]["lnk"] == True else 'OFF'
            minimize_str = 'ON' if self.launchers[launcherID]["minimize"] == True else 'OFF'
            filter_str = ".bat|.exe|.cmd" if sys.platform == "win32" else ''

            # --- ROMS launcher -------------------------------------------------------------------
            if self.launchers[launcherID]["rompath"] != "" and sys.platform == 'win32':
                type2 = dialog.select('Advanced Modifications', 
                                      ['Change Application : %s' % self.launchers[launcherID]["application"],
                                       'Modify Arguments : %s' % self.launchers[launcherID]["args"],
                                       'Change Items Path : %s' % self.launchers[launcherID]["rompath"],
                                       'Modify Items Extensions : %s' % self.launchers[launcherID]["romext"],
                                       'Change Thumbs Path : %s' % self.launchers[launcherID]["thumbpath"],
                                       'Change Fanarts Path : %s' % self.launchers[launcherID]["fanartpath"],
                                       'Change Trailer file : %s' % self.launchers[launcherID]["trailerpath"],
                                       'Change Extra-fanarts Path : %s' % self.launchers[launcherID]["custompath"],
                                       'Toggle Kodi into Windowed mode : %s' % minimize_str,
                                       'Shortcuts (.lnk) support : %s' % lnk_str])
            elif self.launchers[launcherID]["rompath"] != "" and not sys.platform == 'win32':
                type2 = dialog.select('Advanced Modifications', 
                                      ['Change Application : %s' % self.launchers[launcherID]["application"],
                                       'Modify Arguments : %s' % self.launchers[launcherID]["args"],
                                       'Change Items Path : %s' % self.launchers[launcherID]["rompath"],
                                       'Modify Items Extensions : %s' % self.launchers[launcherID]["romext"],
                                       'Change Thumbs Path : %s' % self.launchers[launcherID]["thumbpath"],
                                       'Change Fanarts Path : %s' % self.launchers[launcherID]["fanartpath"],
                                       'Change Trailer file : %s' % self.launchers[launcherID]["trailerpath"],
                                       'Change Extra-fanarts Path : %s' % self.launchers[launcherID]["custompath"],
                                       'Toggle Kodi into Windowed mode : %s' % minimize_str])

            # --- Standalone launcher -------------------------------------------------------------
            elif self.launchers[launcherID]["rompath"] == "" and sys.platform == 'win32':
                type2 = dialog.select('Advanced Modifications', 
                                      ['Change Application : %s' % self.launchers[launcherID]["application"],
                                       'Modify Arguments : %s' % self.launchers[launcherID]["args"],
                                       'Change Thumbs Path : %s' % self.launchers[launcherID]["thumbpath"],
                                       'Change Fanarts Path : %s' % self.launchers[launcherID]["fanartpath"],
                                       'Change Trailer file : %s' % self.launchers[launcherID]["trailerpath"],
                                       'Change Extra-fanarts Path : %s' % self.launchers[launcherID]["custompath"],
                                       'Toggle Kodi into Windowed mode : %s' % minimize_str,
                                       'Shortcuts (.lnk) support : %s' % lnk_str])
            else:
                type2 = dialog.select('Advanced Modifications', 
                                      ['Change Application : %s' % self.launchers[launcherID]["application"],
                                       'Modify Arguments : %s' % self.launchers[launcherID]["args"],
                                       'Change Thumbs Path : %s' % self.launchers[launcherID]["thumbpath"],
                                       'Change Fanarts Path : %s' % self.launchers[launcherID]["fanartpath"],
                                       'Change Trailer file : %s' % self.launchers[launcherID]["trailerpath"],
                                       'Change Extra-fanarts Path : %s' % self.launchers[launcherID]["custompath"],
                                       'Toggle Kodi into Windowed mode : %s' % minimize_str])

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

        if type == -1:
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

        # Return to the launcher directory
        xbmc.executebuiltin("Container.Refresh")

    def _command_add_new_launcher(self, categoryID):
        
        # If categoryID not found return to plugin root window.
        if categoryID not in self.categories:
            log_kodi_notify('Advanced Launcher - Error', 'Target category not found.' , 3000)
            xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self.base_url))

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
            if not app: return False

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
            if not gamesystem == -1:    launcher_gamesys = platforms[gamesystem]
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
                "roms_xml_file" : '', 'nointro_xml_file' : '' }
            self.launchers[launcherID] = launcherdata
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self.base_url, categoryID))

            return True

        # 'Files launcher (e.g. game emulator)'
        elif type == 1:
            app = xbmcgui.Dialog().browse(1, 'Select the launcher application', "files", filter)
            if not app: return False
            
            files_path = xbmcgui.Dialog().browse(0, 'Select Files path', "files", "")
            if not files_path: return False

            extensions = emudata_get_program_extensions(os.path.basename(app))
            extkey = xbmc.Keyboard(extensions, 'Set files extensions, use "|" as separator. (e.g lnk|cbr)')
            extkey.doModal()
            if not extkey.isConfirmed(): return False
            ext = extkey.getText()

            argument = emudata_get_program_arguments(os.path.basename(app))
            argkeyboard = xbmc.Keyboard(argument, 'Application arguments')
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
            platforms = emudata_game_system_list()
            gamesystem = dialog.select('Select the platform', platforms)

            # Selection of the thumbnails and fanarts path
            thumb_path = xbmcgui.Dialog().browse(0, 'Select Thumbnails path', "files", "", False, False, files_path)
            fanart_path = xbmcgui.Dialog().browse(0, 'Select Fanarts path', "files", "", False, False, files_path)

            # --- Create launcher object data, add to dictionary and write XML file ---
            thumb_path  = "" if not thumb_path else thumb_path
            fanart_path = "" if not fanart_path else fanart_path
            if not gamesystem == -1:    launcher_gamesys = platforms[gamesystem]
            else:                       launcher_gamesys = ""
            launcher_lnk = True if sys.platform == "win32" else False
            launcherID = misc_generate_random_SID()
            category_name = self.categories[categoryID]['name']
            clean_cat_name = ''.join([i if i in string.printable else '_' for i in category_name])
            clean_launch_title = ''.join([i if i in string.printable else '_' for i in title])
            roms_xml_file = 'roms_' + clean_cat_name + '_' + clean_launch_title + '_' + launcherID[0:8] + '.xml'
            roms_xml_file_path = os.path.join(PLUGIN_DATA_DIR, roms_xml_file)
            self._print_log('Chosen roms_xml_file      = "{0}"'.format(roms_xml_file))
            self._print_log('Chosen roms_xml_file_path = "{0}"'.format(roms_xml_file_path))
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
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self.base_url, categoryID))

            return True

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
            log_kodi_notify('AEL', 'Launching {0}'.format(name_str), 5000)

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
            log_kodi_dialog_OK('ERROR', 'launcherID not found in launcherID')
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
            log_kodi_notify('AEL - ERROR', 
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
            log_kodi_notify('AEL - ERROR', 'Cannot determine the running platform', 10000)

        # Do stuff after execution
        self._run_after_execution(launcher)

    #
    # Launchs a ROM
    #
    def _run_rom(self, categoryID, launcherID, romID):
        # Check launcher is OK
        if launcherID not in self.launchers:
            log_kodi_dialog_OK('ERROR', 'launcherID not found in launcherID')
            return
        launcher = self.launchers[launcherID]
        
        # Load ROMs
        roms = fs_load_ROM_XML_file(launcher['roms_xml_file'])

        # Check ROM is XML data just read
        if romID not in roms:
            log_kodi_dialog_OK('ERROR', 'romID not in roms_dic')
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
            log_kodi_notify("AEL - ERROR", 'File %s not found.' % apppath, 10000)
            return
        if os.path.exists(romfile):
            log_kodi_notify("AEL - ERROR", 'File %s not found.' % romfile, 10000)
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
            log_kodi_notify('AEL - ERROR', 'Cannot determine the running platform', 10000)

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
    def _gui_render_categories( self ):
        # For every category, add it to the listbox
        # Order alphabetically by name
        for key in sorted(self.categories, key= lambda x : self.categories[x]["name"]):
            self._gui_render_category_row(self.categories[key], key)
        # AEL Favourites special category
        self._gui_render_category_favourites()
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded=True, cacheToDisc=False )

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
        commands.append(('Search ROMs in Launcher', self._misc_url_RunPlugin('SEARCH_LAUNCHER', categoryID, launcherID), ))
        # Add Launcher URL to Kodi Favourites (do not know how to do it yet)
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', )) # If using window ID then use "10003" 
        commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        listitem.addContextMenuItems(commands, replaceItems=True)

        # --- Add row ---
        url_str = self._misc_url('SHOW_ROMS', launcher_dic['category'], key)
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url=url_str, listitem=listitem, isFolder=folder)

    #
    # Former  _get_launchers
    # Renders the launcher for a given category
    #
    def _gui_render_launchers( self, categoryID ):
        for key in sorted(self.launchers, key= lambda x : self.launchers[x]["application"]):
            if self.launchers[key]["category"] == categoryID:
                self._gui_render_launcher_row(self.launchers[key], key)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded=True, cacheToDisc=False )

    #
    # Former  _add_rom
    # Note that if we are rendering favourites, categoryID = launcherID = '0'.
    def _gui_render_rom_row( self, categoryID, launcherID, romID, rom, rom_is_in_favourites):
        # --- Create listitem row ---
        icon = "DefaultProgram.png"
        # icon = "DefaultVideo.png"

        # If listing regular launcher and rom is in favourites, mark it
        if rom_is_in_favourites:
            # rom_name = '[B]{0}[/B]'.format(rom['name']) # Does not work in Confluence
            # rom_name = '[I]{0}[/I]'.format(rom['name']) # Does not work in Confluence
            # rom_name = '[COLOR red]{0}[/COLOR]'.format(rom['name']) # Does not work in Confluence
            # rom_name = '[COLOR violet]{0}[/COLOR]'.format(rom['name']) # Does not work in Confluence
            
            # --- Workaround so the alphabetical order is not lost ---
            rom_name = '{0} [COLOR violet][Fav][/COLOR]'.format(rom['name']) # Does not work in Confluence
            # log_debug('gui_render_rom_row() ROM is in favourites {}'.format(rom_name))
        else:
            try:
                if rom['nointro_status'] == 'Have':
                    rom_name = '{0} [COLOR green][Have][/COLOR]'.format(rom['name'])
                elif rom['nointro_status'] == 'Miss':
                    rom_name = '{0} [COLOR red][Miss][/COLOR]'.format(rom['name'])
                elif rom['nointro_status'] == 'Unknown':
                    rom_name = '{0} [COLOR yellow][Unknown][/COLOR]'.format(rom['name'])
                else:
                    rom_name = rom['name']
            except:
                rom_name = rom['name']

        # Add ROM to lisitem
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
        listitem.setInfo("video", { "Title"   : rom_name,    "Label"     : 'test label', 
                                    "Plot"    : rom['plot'],    "Studio"    : rom['studio'], 
                                    "Genre"   : rom['genre'],   "Premiered" : rom['release'], 
                                    'Year'    : rom['release'], "Writer"    : rom['gamesys'], 
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
            log_warning('AEL ERROR', 'Launcher hash not found.', '@_gui_render_roms()')
            log_kodi_dialog_OK('AEL ERROR', 'Launcher hash not found.', '@_gui_render_roms()')
            return

        # Load ROMs for this launcher and display them
        selectedLauncher = self.launchers[launcherID]
        roms_xml_file = selectedLauncher["roms_xml_file"]

        # Check if XML file with ROMs exist
        if not os.path.isfile(roms_xml_file):
            log_kodi_notify('Advanced Emulator Launcher', 'Launcher XML missing. Add items to launcher.', 10000)
            xbmc.executebuiltin("Container.Update")
            return

        # Load ROMs
        roms = fs_load_ROM_XML_file(roms_xml_file)
        if not roms:
            log_kodi_notify('Advanced Emulator Launcher', 'Launcher XML empty. Add items to launcher.', 10000)
            return

        # Load favourites
        roms_fav = fs_load_Favourites_XML_file(FAVOURITES_FILE_PATH)

        # Display ROMs
        for key in sorted(roms, key= lambda x : roms[x]["filename"]):
            self._gui_render_rom_row(categoryID, launcherID, key, roms[key], key in roms_fav)
        xbmcplugin.endOfDirectory( handle = self.addon_handle, succeeded=True, cacheToDisc=False )

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
            log_kodi_notify('Advanced Emulator Launcher', 'Favourites XML empty. Add items to favourites first', 5000)
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
            log_kodi_dialog_OK('Advanced Emulator Launcher',
                               'Empty roms launcher in _command_add_to_favourites()',
                               'This is a bug, please report it.')

        # Load favourites
        roms_fav = fs_load_Favourites_XML_file(FAVOURITES_FILE_PATH)
        
        # DEBUG
        log_verb('Adding ROM to Favourites')
        log_verb('romID {:}'.format(romID))
        log_verb('name  {:}'.format(roms[romID]['name']))

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
        roms_fav[romID]['application'] = self.launchers[launcherID]['application']
        roms_fav[romID]['args']        = self.launchers[launcherID]['args']
        roms_fav[romID]['launcherID']  = self.launchers[launcherID]['id']
        if roms_fav[romID]['thumb']  == '': roms_fav[romID]['thumb']  = self.launchers[launcherID]['thumb']
        if roms_fav[romID]['fanart'] == '': roms_fav[romID]['fanart'] = self.launchers[launcherID]['fanart']

        # Save favourites
        fs_write_Favourites_XML_file(FAVOURITES_FILE_PATH, roms_fav)

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
                log_kodi_notify('AEL', 'Deleted ROM from Favourites')
                # If Favourites is empty then go to root, if not refresh
                if len(roms) == 0:
                    xbmc.executebuiltin('ReplaceWindow(Programs,{0})'.format(self.base_url))
                else:
                    xbmc.executebuiltin('Container.Update({0})'.format(self._misc_url('SHOW_FAVOURITES')))
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
                log_kodi_notify('AEL', 'Deleted ROM from launcher')
                # If launcher is empty then go to root, if not refresh
                if len(roms) == 0:
                    xbmc.executebuiltin('ReplaceWindow(Programs,{0})'.format(self.base_url))
                else:
                    xbmc.executebuiltin('Container.Update({0})'.format(self._misc_url('SHOW_ROMS', categoryID, launcherID)))

    #
    # Former _edit_rom()
    # Note that categoryID = launcherID = '0' if we are editing a ROM in Favourites
    def _command_edit_rom(self, categoryID, launcherID, romID):
        # Load ROMs
        rom_xml_path = self.launchers[launcherID]["roms_xml_file"]
        roms = fs_load_ROM_XML_file(rom_xml_path)
    
        #
        title = roms[romID]["name"]
        finished_display = 'Status: Finished' if roms[romID]["finished"] == True else 'Status: Unfinished'
        dialog = xbmcgui.Dialog()
        type = dialog.select('Select Action for %s' % title, 
                             ['Edit Metadata ...',
                              'Change Thumbnail Image ...', 'Change Fanart Image...',
                              finished_display,
                              'Advanced Modifications ...', 'Delete ROM'])
        # Edit ROM metadata
        if type == 0:
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Modify Item Infos', 
                                  ['Scrap from %s' % self.settings[ "datas_scraper" ],
                                   'Import metadata from NFO file',
                                   'Edit Title : %s' % roms[romID]["name"],
                                   'Edit Release Date : %s' % roms[romID]["release"],
                                   'Edit Studio : %s' % roms[romID]["studio"],
                                   'Edit Genre : %s' % roms[romID]["genre"],
                                   'Edit Description : %s ...' % roms[romID]["plot"][0:20],
                                   'Save metadata to NFO file'])
            # Scrap rom Infos
            if type2 == 0:
                self._gui_scrap_rom_metadata(launcherID, romID)
            elif type2 == 1:
                self._import_rom_nfo(launcher, rom)
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
            # Edition of the rom release date
            elif type2 == 3:
                keyboard = xbmc.Keyboard(roms[romID]["release"], 'Edit release year')
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    roms[romID]["release"] = keyboard.getText()
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
                text_file = xbmcgui.Dialog().browse(1, 'Select description file. (e.g txt|dat)', "files", ".txt|.dat", False, False)
                if os.path.isfile(text_file):
                    text_plot = open(text_file)
                    string_plot = text_plot.read()
                    text_plot.close()
                    roms[romID]["plot"] = string_plot.replace('&quot;','"')
                    fs_write_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'], roms, self.launchers[launcherID])
            elif type2 == 7:
                self._export_rom_nfo(launcher,rom)

        # Edit thumb and fanart
        elif type == 1:
            self._gui_edit_thumbnail(KIND_ROM, roms, romID, self.launchers[launcherID]['thumbpath'])

        elif type == 2:
            self._gui_edit_fanart(KIND_ROM, roms, self.launchers[launcherID]['fanartpath'])

        # Edit status
        elif type == 3:
            finished = roms[romID]["finished"]
            finished = False if finished else True
            finished_display = 'Finished' if finished == True else 'Unfinished'
            roms[romID]["finished"] = finished
            fs_write_ROM_XML_file(self.launchers[launcherID]['roms_xml_file'], roms, self.launchers[launcherID])
            log_kodi_dialog_OK('AEL Information', 
                               'ROM "{}" status is now {}'.format(roms[romID]["name"], finished_display))

        # Advanced Modifications
        if type == 4:
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

        # Delete ROM
        elif type == 5:
            self._command_remove_rom(categoryID, launcherID, romID)

        # Return to the launcher directory
        xbmc.executebuiltin("Container.Refresh")

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
    # ROM scanner. Called when user chooses "Add items" -> "Scan items"
    # Note that actually this command is "Add/Update" ROMs.
    #
    def _roms_import_roms(self, launcherID):
        log_debug('_roms_import_roms() BEGIN')

        dialog = xbmcgui.Dialog()
        pDialog = xbmcgui.DialogProgress()
        # Get game system, thumbnails and fanarts paths from launcher
        selectedLauncher = self.launchers[launcherID]
        launch_app          = selectedLauncher["application"]
        launch_path         = selectedLauncher["rompath"]
        launch_exts         = selectedLauncher["romext"]
        log_debug('Launcher "%s" selected' % selectedLauncher["name"]) 
        log_debug('launch_app  = {0}'.format(launch_app)) 
        log_debug('launch_path = {0}'.format(launch_path)) 
        log_debug('launch_exts = {0}'.format(launch_exts)) 

        # Check if there is an XML for this launcher. If so, load it.
        # If file does not exist or is empty then return an empty dictionary.
        rom_xml_path = selectedLauncher["roms_xml_file"]
        roms = fs_load_ROM_XML_file(rom_xml_path)

        # ~~~~~ Remove dead entries ~~~~~
        if len(roms) > 0:
            log_debug('Launcher list contain %s items' % len(roms))
            log_debug('Starting dead items scan')
            i = 0
            removedRoms = 0
            ret = pDialog.create('Advanced Emulator Launcher', 
                                 'Checking for dead entries',
                                 'Path: %s...' % (launch_path))
            for key in sorted(roms.iterkeys()):
                log_debug('Searching %s' % roms[key]["filename"] )
                pDialog.update(i * 100 / len(roms))
                i += 1
                if (not os.path.isfile(roms[key]["filename"])):
                    log_debug('Not found')
                    log_debug('Delete %s item entry' % roms[key]["filename"] )
                    del roms[key]
                    removedRoms += 1
                else:
                    log_debug('Found')

            pDialog.close()
            if not (removedRoms == 0):
                log_info('%s entries removed successfully' % removedRoms)
                log_kodi_notify('AEL', '%s entries removed successfully' % removedRoms)
            else:
                log_info('No dead item entry')
        else:
            log_info('Launcher is empty')

        # ~~~ Scan for new files (*.*) and put them in a list ~~~
        log_kodi_notify('AEL', 'Scanning files...')
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        log_info('Scanning files in {0}'.format(launch_path))
        files = []
        if self.settings["scan_recursive"]:
            log_info('Recursive scan activated')
            for root, dirs, filess in os.walk(launch_path):
                for filename in fnmatch.filter(filess, '*.*'):
                    files.append(os.path.join(root, filename))
        else:
            log_info('Recursive scan not activated')
            filesname = os.listdir(launch_path)
            for filename in filesname:
                files.append(os.path.join(launch_path, filename))
        xbmc.executebuiltin("Dialog.Close(busydialog)")
        log_info('Found {0} files'.format(len(files)))

        # ~~~ Now go processing file by file ~~~
        ret = pDialog.create('AEL - Importing ROMs', 'Importing files from {0}'.format(launch_path))
        log_debug('======= Processing ROMs ======')
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
            log_debug('*** Processing File ***')
            log_debug('f_path       = "{0}"'.format(f_path))
            log_debug('f_path_noext = "{0}"'.format(f_path_noext))
            log_debug('f_base       = "{0}"'.format(f_base))
            log_debug('f_base_noext = "{0}"'.format(f_base_noext))
            log_debug('f_ext        = "{0}"'.format(f_ext))

            # ~~~ Update progress dialog ~~~
            file_text = 'File {0}'.format(f_base)
            metadata_scraper_text = self.scraper_metadata.name
            pDialog.update(filesCount * 100 / len(files), file_text, metadata_scraper_text)

            # ~~~ Find ROM file ~~~
            # The recursive scan has scanned all file. Check if this file matches some of the extensions
            # for ROMs. If not, skip this file and go for next one in the list.
            processROM = False
            for ext in launch_exts.split("|"):
                # Check if filename matchs extension
                if f_ext == '.' + ext:
                    log_debug('Expected %s extension detected' % ext) 
                    processROM = True
            # If file does not match any of the ROM extensions skip it
            if not processROM:
                continue

            # Check that ROM is not already in the list of ROMs
            repeatedROM = False
            for g in roms:
                if roms[g]["filename"] == f_path:
                    log_debug('File already into launcher list') 
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

        if len(roms) == 0:
            log_kodi_dialog_OK('AEL', 'No ROMs found! Make sure launcher directory and file extensions are correct.')
            xbmc.executebuiltin('Container.Update()')
            return

        # --- If we have a No-Intro XML then audit roms ---
        if selectedLauncher['nointro_xml_file'] != '':
            log_info('Auditing ROMs using No-Intro DAT {}'.format(selectedLauncher['nointro_xml_file']))
            
            # Load DAT
            roms_nointro = fs_load_NoIntro_XML_file(selectedLauncher['nointro_xml_file'])
            
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
                    rom = {'id' : '', 'name' : '', "filename" : '', "gamesys" : '', "thumb" : '', "fanart" : '',
                           "trailer" : '', "custom" : '', "genre" : '', "release" : '', "studio" : '',
                           "plot" : '', "altapp" : '', "altarg" : '', "finished" : False, 'nointro_status' : 'None' }
                    romID = misc_generate_random_SID()
                    rom['id'] = romID
                    rom['name'] = nointro_rom
                    rom['nointro_status'] = 'Miss'
                    roms[romID] = rom
                    num_miss += 1

            log_info('Have    {:6d}'.format(num_have))
            log_info('Miss    {:6d}'.format(num_miss))
            log_info('Unknown {:6d}'.format(num_unknown))

        # ~~~ Save launchers ~~~
        fs_write_ROM_XML_file(rom_xml_path, roms, self.launchers[launcherID])

        # ~~~ Notify user ~~~
        log_kodi_notify('Advanced Emulator Launcher', '%s files imported' % (romsCount))
        
        # xbmc.executebuiltin("XBMC.ReloadSkin()")
        xbmc.executebuiltin('Container.Update()')

    def _roms_process_scanned_ROM(self, selectedLauncher, f_path, f_path_noext, f_base, f_base_noext, f_ext):
        # Grab info
        launch_gamesys = selectedLauncher["gamesys"]

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
        romdata["altapp"]   = ''
        romdata["altarg"]   = ''
        romdata["finished"] = False
        romdata['nointro_status'] = 'None'

        # ~~~~~ Scrape game metadata information ~~~~~
        # From now force NFO files scraper
        self.settings[ "datas_method" ] = "0"
        
        # No metadata scrap
        if self.settings[ "datas_method" ] == "0":
            log_debug('Scraping disabled')
            # romdata["name"] = self._text_ROM_title_format(f_base_noext)
            romdata["name"] = f_base_noext
        else:
            # Scrap metadata from NFO files
            found_NFO_file = False
            if self.settings[ "datas_method" ] == "1" or self.settings[ "datas_method" ] == "3":
                nfo_file_path = os.path.join(f_path_noext, ".nfo")
                log_debug('Trying NFO file "{0}"...'.format(nfo_file_path))
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
                    log_debug('Only update item name')
                    romdata['name'] = _text_ROM_title_format(self, romname)

            # Scrap metadata from www database
            if self.settings[ "datas_method" ] == "2" or (self.settings[ "datas_method" ] == "3" and found_NFO_file == False):
                romdata["name"] = clean_filename(romname)
                if ( self.settings[ "scrap_info" ] == "1" ):
                    log_debug('Info automatic scraping') 
                    results = self._get_first_game(romdata["name"],gamesys)
                    selectgame = 0
                else:
                    log_debug('Info semi-automatic scraping') 
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
        log_debug('Searching local tumb/fanart')

        if thumb_path == fanart_path:
            log_debug('Thumbs/Fanarts have the same path')
            tumb_path_noext   = os.path.join(thumb_path, f_base_noext + '_thumb')
            fanart_path_noext = os.path.join(fanart_path, f_base_noext + '_fanart')
        else:
            log_debug('Thumbs/Fanarts into different folders')
            tumb_path_noext   = os.path.join(thumb_path, f_base_noext)
            fanart_path_noext = os.path.join(fanart_path, f_base_noext)
        log_debug('tumb_path_noext   = "{0}"'.format(tumb_path_noext))
        log_debug('fanart_path_noext = "{0}"'.format(fanart_path_noext))

        # Search for local artwork
        thumb = ''
        fanart = ''
        ext2s = ['png', 'jpg', 'gif', 'jpeg', 'bmp', 'PNG', 'JPG', 'GIF', 'JPEG', 'BMP']
        # Thumbs first
        for ext2 in ext2s:
            test_img = tumb_path_noext + '.' + ext2
            log_debug('Testing Thumb  "{0}"'.format(test_img))
            if os.path.isfile(test_img):
                thumb = test_img
                log_debug('Found Thumb    "{0}"'.format(test_img))
                break

        # Fanart second
        for ext2 in ext2s:
            test_img = fanart_path_noext + '.' + ext2
            log_debug('Testing Fanart "{0}"'.format(test_img))
            if os.path.isfile(test_img):
                fanart = test_img
                log_debug('Found Fanart   "{0}"'.format(test_img))
                break

        # Add to ROM dictionary
        romdata["thumb"]  = thumb
        romdata["fanart"] = fanart
        log_debug('Set Thumb  = "{0}"'.format(thumb))
        log_debug('Set Fanart = "{0}"'.format(fanart))

        # Deactivate Thumb scraping
        if None:
            if self.settings[ "thumbs_method" ] == "2":
                # If overwrite is activated or thumb file not exist
                if self.settings[ "overwrite_thumbs"] or thumb == "":
                    pDialog.update(filesCount * 100 / len(files), 
                                'Importing %s thumb from %s' % (f.replace("."+f.split(".")[-1],""), 
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
                                log_kodi_notify('Advanced Emulator Launcher'+" - "+__language__( 30612 ), __language__( 30604 ),3000)
                            except exceptions.IOError:
                                log_kodi_notify('Advanced Emulator Launcher'+" - "+__language__( 30612 ), __language__( 30605 ),3000)
                        else:
                            if ( not os.path.isfile(thumb) ) & ( os.path.isfile(cached_thumb) ):
                                os.remove(cached_thumb)
                romdata["thumb"] = thumb
            else:
                if self.settings[ "thumbs_method" ] == "0":
                    romdata["thumb"] = ""
                else:
                    pDialog.update(filesCount * 100 / len(files), 
                                'Importing %s thumb from %s' % (f.replace("."+f.split(".")[-1],""), __language__( 30172 )))
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
                                log_kodi_notify('Advanced Emulator Launcher'+" - "+__language__( 30612 ), __language__( 30606 ),3000)
                            except exceptions.IOError:
                                log_kodi_notify('Advanced Emulator Launcher'+" - "+__language__( 30612 ), __language__( 30607 ),3000)
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
    def _roms_add_new_rom (self, launcherID):
        log_kodi_dialog_OK('AEL', 'Not implemented yet')
        return

        dialog = xbmcgui.Dialog()
        launcher = self.launchers[launcherID]
        app = launcher["application"]
        ext = launcher["romext"]
        roms = launcher["roms"]
        rompath = launcher["rompath"]
        romfile = dialog.browse(1, __language__( 30017 ),"files", "."+ext.replace("|","|."), False, False, rompath)
        if romfile:
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
                log_kodi_notify('AEL', 'Edit Launcher' + " " + 'Re-Enter this directory to see the changes')
        self._save_launchers()

    #
    # Search ROMs in launcher
    #
    def _command_search_launcher(self, categoryID, launcherID):
        # Check that the launcher has items
        if not os.path.isfile(self.launchers[launcherID]["roms_xml_file"]):
            log_kodi_notify('Advanced Emulator Launcher', 'Launcher XML missing. Add items to launcher')
            xbmc.executebuiltin("Container.Update")
            return
        roms = fs_load_ROM_XML_file(self.launchers[launcherID]["roms_xml_file"])
        if not roms:
            log_kodi_notify('Advanced Emulator Launcher', 'Launcher XML empty. Add items to launcher')
            return

        # Ask user what category to search
        dialog = xbmcgui.Dialog()
        type = dialog.select('Search items...', 
                             ['[B]By Title[/B]',
                              '[I]By Release Date[/I]',
                              '[COLOR yellow]By Studio[/COLOR]',
                              '[COLOR green]By Genre[/COLOR]'])

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
            searched_list = self._search_launcher_category(launcherID, "release", roms)
            dialog = xbmcgui.Dialog()
            selected_value = dialog.select('Select a Release date ...', searched_list)
            if selected_value >= 0:
                search_string = searched_list[selected_value]
                url = self._misc_url_search('EXEC_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_RELEASE', search_string)
                xbmc.executebuiltin("ReplaceWindow(Programs,{0})".format(url))

        # Search by System Platform
        # Note that search by platform does not make sense when searching a launcher because all items have
        # the same platform! It only makes sense for global searches... which AEL does not.
        # I keep this AL old code for reference, though.
        # type_nb = type_nb + 1
        # if type == type_nb:
        #     search = []
        #     search = _search_category(self, "gamesys")
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
        elif search_type == 'SEARCH_RELEASE': rom_search_field = 'release'
        elif search_type == 'SEARCH_STUDIO' : rom_search_field = 'studio'
        elif search_type == 'SEARCH_GENRE'  : rom_search_field = 'genre'

        # Load ROMs
        # Check that the launcher has items
        if not os.path.isfile(self.launchers[launcherID]["roms_xml_file"]):
            log_kodi_notify('Advanced Emulator Launcher', 'Launcher XML missing. Add items to launcher')
            xbmc.executebuiltin("Container.Update")
            return
        roms = fs_load_ROM_XML_file(self.launchers[launcherID]["roms_xml_file"])
        if not roms:
            log_kodi_notify('Advanced Emulator Launcher', 'Launcher XML empty. Add items to launcher')
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
            log_kodi_dialog_OK('Advaned Emulator Launcher', 'Search produced no results')
        for key in sorted(rl.iterkeys()):
            self._gui_render_rom_row(categoryID, launcherID, key, rl[key])
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded=True, cacheToDisc=False)

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

        # self.listing = kwargs.get('listing')
        # self.type = kwargs.get('category')
        # self.property = kwargs.get('string')
        
        self.listing = kwargs.get( "listing" )
        self.selected_url = ''

    def onInit(self):
        self.container = self.getControl(6)
        self.container.controlLeft(self.container)  # Disables movement left-right in image listbox
        self.container.controlRight(self.container)

        # self.cancel = self.getControl(7) # Produces an error "RuntimeError: Non-Existent Control 7"
        # self.cancel.setLabel('Ajo')

        self.getControl(3).setVisible(False) # Another container which I don't understand...
        
        self.getControl(1).setLabel('Choose item') # Window title on top

        self.button = self.getControl(5) # OK button
        self.button.setVisible(False)        
        # self.button.setLabel('Ar')
        
        # Add items to list
        # listitem = xbmcgui.ListItem(label='Example', iconImage='DefaultAddon.png')
        # self.container.addItem(listitem)
        listitems = []
        for index, item in enumerate(self.listing):
            listitem = xbmcgui.ListItem(label=item[2], label2=item[1], iconImage='DefaultAddonImages.png', thumbnailImage=item[0])
            listitems.append(listitem)
        self.container.addItems(listitems)
        self.setFocus(self.container)

    def onAction(self, action):
        if action.getId() in (9, 10, 92, 216, 247, 257, 275, 61467, 61448):
            self.close()

    def onClick(self, controlID):
        if controlID == 6:
            # num = self.container.getSelectedPosition()
            self.selected_url = self.container.getSelectedItem().getLabel2()
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

# From DialogSelect.xml in Confluence
# Controls 5 and 7 are grouped
# <control type="label" id="1">  | <description>header label</description>
# 2 does not exist
# <control type="list" id="3">
# <control type="label" id="4">  | <description>No Settings Label</description>
# <control type="button" id="5"> | <description>Manual button</description>
# <control type="list" id="6">
# <control type="button" id="7"> | <description>Cancel button</description>
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

# -------------------------------------------------------------------------------------------------
# Hacks
# -------------------------------------------------------------------------------------------------
# --- Test the image selector class ---
# if __name__ == "__main__":
#     covers = []
#     covers.append(['http://www.captainwilliams.co.uk/sega/32x/images/32xsolo.jpg',
#                    'http://www.captainwilliams.co.uk/sega/32x/images/32xsolo.jpg',
#                    'Sega 32 X'])
#     image_url = gui_show_image_select(covers)

# -------------------------------------------------------------------------------------------------
# main()
# -------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    Main()
