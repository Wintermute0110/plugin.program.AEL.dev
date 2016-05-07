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

# --- XML stuff ---
# ~~~ cElementTree sometimes fails to parse XML in Kodi's Python interpreter... I don't know why
# import xml.etree.cElementTree as ET
# ~~~ Using ElementTree seems to solve the problem
import xml.etree.ElementTree as ET

# --- Kodi stuff ---
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

# --- Modules/packages in this plugin ---
import resources.subprocess_hack
from resources.user_agent import getUserAgent
from resources.file_item import Thumbnails
from resources.emulators import *

# --- Plugin constants ---
__plugin__  = "Advanced Emulator Launcher"
__version__ = "0.9.0"
__author__  = "Wintermute0110, Angelscry"
__url__     = "https://github.com/Wintermute0110/plugin.program.advanced.emulator.launcher"
__git_url__ = "https://github.com/Wintermute0110/plugin.program.advanced.emulator.launcher"
__credits__ = "Leo212 CinPoU, JustSomeUser, Zerqent, Zosky, Atsumori"

# --- Some debug stuff for development ---
xbmc.log('---------- Called AEL addon.py ----------')
# xbmc.log(sys.version)
for i in range(len(sys.argv)):
    xbmc.log('sys.argv[{0}] = "{1}"'.format(i, sys.argv[i]))

# --- Addon paths definition ---
# _FILE_PATH is a filename
# _DIR is a directory (with trailing /)
PLUGIN_DATA_DIR      = xbmc.translatePath(os.path.join("special://profile/addon_data", "plugin.program.advanced.emulator.launcher"))
BASE_DIR             = xbmc.translatePath(os.path.join("special://", "profile"))
HOME_DIR             = xbmc.translatePath(os.path.join("special://", "home"))
FAVOURITES_DIR       = xbmc.translatePath( 'special://profile/favourites.xml' )
ADDONS_DIR           = xbmc.translatePath(os.path.join(HOME_DIR, "addons"))
CURRENT_ADDON_DIR    = xbmc.translatePath(os.path.join(ADDONS_DIR, "plugin.program.advanced.emulator.launcher"))
ICON_IMG_FILE_PATH   = os.path.join(CURRENT_ADDON_DIR, "icon.png")
CATEGORIES_FILE_PATH = os.path.join(PLUGIN_DATA_DIR, "categories.xml")
DEFAULT_THUMB_DIR    = os.path.join(PLUGIN_DATA_DIR, "thumbs") # Old deprecated definition
DEFAULT_FANART_DIR   = os.path.join(PLUGIN_DATA_DIR, "fanarts") # Old deprecated definition
DEFAULT_NFO_DIR      = os.path.join(PLUGIN_DATA_DIR, "nfos") # Old deprecated definition

xbmc.log('PLUGIN_DATA_DIR      = "{0}"'.format(PLUGIN_DATA_DIR))
xbmc.log('BASE_DIR             = "{0}"'.format(BASE_DIR))
xbmc.log('HOME_DIR             = "{0}"'.format(HOME_DIR))
xbmc.log('FAVOURITES_DIR       = "{0}"'.format(FAVOURITES_DIR))
xbmc.log('ADDONS_DIR           = "{0}"'.format(ADDONS_DIR))
xbmc.log('CURRENT_ADDON_DIR    = "{0}"'.format(CURRENT_ADDON_DIR))
xbmc.log('ICON_IMG_FILE_PATH   = "{0}"'.format(ICON_IMG_FILE_PATH))
xbmc.log('CATEGORIES_FILE_PATH = "{0}"'.format(CATEGORIES_FILE_PATH))
xbmc.log('DEFAULT_THUMB_DIR    = "{0}"'.format(DEFAULT_THUMB_DIR))
xbmc.log('DEFAULT_FANART_DIR   = "{0}"'.format(DEFAULT_FANART_DIR))
xbmc.log('DEFAULT_NFO_DIR      = "{0}"'.format(DEFAULT_NFO_DIR))

# --- Addon data paths creation ---
if not os.path.isdir(PLUGIN_DATA_DIR):    os.makedirs(PLUGIN_DATA_DIR)
if not os.path.isdir(DEFAULT_THUMB_DIR):  os.makedirs(DEFAULT_THUMB_DIR)
if not os.path.isdir(DEFAULT_FANART_DIR): os.makedirs(DEFAULT_FANART_DIR)
if not os.path.isdir(DEFAULT_NFO_DIR):    os.makedirs(DEFAULT_NFO_DIR)

# Addon object (used to access settings)
addon_obj = xbmcaddon.Addon( id="plugin.program.advanced.emulator.launcher" )

# --- Main code ---
class Main:
    settings = {}
    launchers = {}
    categories = {}

    def __init__( self, *args, **kwargs ):
        # Fill in settings dictionary using addon_obj.getSetting
        self._get_settings()

        # New Kodi URL code
        self.base_url = sys.argv[0]
        self.addon_handle = int(sys.argv[1])
        args = urlparse.parse_qs(sys.argv[2][1:])
        xbmc.log('args = {0}'.format(args))

        # store an handle pointer (Legacy deprecated code)
        self._path = sys.argv[ 0 ]
        self._handle = int(sys.argv[ 1 ])

        xbmcplugin.setContent(handle = self._handle, content = 'movies')

        # Adds a sorting method for the media list.
        if self._handle > 0:
            xbmcplugin.addSortMethod(handle=self._handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
            xbmcplugin.addSortMethod(handle=self._handle, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)
            xbmcplugin.addSortMethod(handle=self._handle, sortMethod=xbmcplugin.SORT_METHOD_STUDIO)
            xbmcplugin.addSortMethod(handle=self._handle, sortMethod=xbmcplugin.SORT_METHOD_GENRE)
            xbmcplugin.addSortMethod(handle=self._handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)

        # --- WORKAROUND ---
        # When the addon is installed and the file categories.xml does not exist, just
        # create an empty one with a default launcher. Later on, when I am more familiar
        # with the addon add a welcome wizard or something similar.
        #
        # Create a default categories.xml file if does not exist yet (plugin just installed)
        if not os.path.isfile(CATEGORIES_FILE_PATH):
            gui_kodi_dialog_OK('Advanced Emulator Launcher - WARNING', 'Creating default categories.xml')
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
            categoryID = args['catID'][0]
            launcherID = args['launID'][0]
            self._print_log('SHOW_ROMS | categoryID = {0}'.format(categoryID))
            self._print_log('SHOW_ROMS | launcherID = {0}'.format(launcherID))

            # User clicked on a launcher. For executable launchers run the executable.
            # For emulator launchers show roms.
            if self.launchers[launcherID]["rompath"] == '':
                self._print_log('SHOW_ROMS | Launcher rompath is empty. Assuming launcher is standalone.')
                self._print_log('SHOW_ROMS | Calling _run_launcher()')
                self._run_standalone_launcher(categoryID, launcherID)
            else:
                self._print_log('SHOW_ROMS | Calling _gui_render_roms()')
                self._gui_render_roms(categoryID, launcherID)

        elif command == 'ADD_ROMS':
            self._command_add_roms(args['launID'][0])

        elif command == 'EDIT_ROM':
            categoryID = args['catID'][0]
            launcherID = args['launID'][0]
            romID      = args['romID'][0]
            self._command_edit_rom(categoryID, launcherID, romID)

        elif command == 'DELETE_ROM':
            gui_kodi_dialog_OK('ERROR', 'DELETE_ROM not implemented yet')
            # if (action == REMOVE_COMMAND):
            #    self._remove_rom(launcher, rom)

        elif args['com'][0] == 'LAUNCH_ROM':
            categoryID = args['catID'][0]
            launcherID = args['launID'][0]
            romID      = args['romID'][0]
            self._run_rom(categoryID, launcherID, romID)

        # elif (launcher == FILE_MANAGER_COMMAND):
        #    self._file_manager()

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
        category['name']     = 'Games'
        category['thumb']    = ''
        category['fanart']   = ''
        category['genre']    = ''
        category['plot']     = ''
        category['finished'] = False

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
    # Write to disk categories.xml
    #
    def _fs_write_catfile(self):
        self._print_log('_fs_create_default_catfile() Saving categories.xml file')
       
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )

        # Original Angelscry method for generating the XML was to grow a string, like this
        # xml_content = 'test'
        # xml_content += 'more test'
        # However, this method is very slow because string has to be reallocated every time is grown.
        # It is much faster to create a list of string and them join them!
        # See https://waymoot.org/home/python_string/
        try:
            str_list = []
            str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
            str_list.append('<advanced_emulator_launcher version="1.0">\n')

            # Create Categories XML list
            for categoryID in sorted(self.categories, key = lambda x : self.categories[x]["name"]):
                category = self.categories[categoryID]
                # Data which is not string must be converted to string
                str_list.append("<category>\n" +
                                "  <id>"          + categoryID                 + "</id>\n" +
                                "  <name>"        + category["name"]           + "</name>\n" +
                                "  <thumb>"       + category["thumb"]          + "</thumb>\n"
                                "  <fanart>"      + category["fanart"]         + "</fanart>\n" +
                                "  <genre>"       + category["genre"]          + "</genre>\n" +
                                "  <description>" + category["plot"]           + "</description>\n" +
                                "  <finished>"    + str(category["finished"])  + "</finished>\n" +
                                "</category>\n")
            # Write launchers
            for launcherID in sorted(self.launchers, key = lambda x : self.launchers[x]["name"]):
                launcher = self.launchers[launcherID]
                # Data which is not string must be converted to string
                str_list.append("<launcher>\n" +
                                "  <id>"            + launcherID                + "</id>\n" +
                                "  <name>"          + launcher["name"]          + "</name>\n" +
                                "  <category>"      + launcher["category"]      + "</category>\n" +
                                "  <application>"   + launcher["application"]   + "</application>\n"
                                "  <args>"          + launcher["args"]          + "</args>\n" +
                                "  <rompath>"       + launcher["rompath"]       + "</rompath>\n" +
                                "  <thumbpath>"     + launcher["thumbpath"]     + "</thumbpath>\n" +
                                "  <fanartpath>"    + launcher["fanartpath"]    + "</fanartpath>\n" +
                                "  <custompath>"    + launcher["custompath"]    + "</custompath>\n" +
                                "  <trailerpath>"   + launcher["trailerpath"]   + "</trailerpath>\n" +
                                "  <romext>"        + launcher["romext"]        + "</romext>\n" +
                                "  <gamesys>"       + launcher["gamesys"]       + "</gamesys>\n" +
                                "  <thumb>"         + launcher["thumb"]         + "</thumb>\n" +
                                "  <fanart>"        + launcher["fanart"]        + "</fanart>\n" +
                                "  <genre>"         + launcher["genre"]         + "</genre>\n" +
                                "  <release>"       + launcher["release"]       + "</release>\n" +
                                "  <studio>"        + launcher["studio"]        + "</studio>\n" +
                                "  <plot>"          + launcher["plot"]          + "</plot>\n" +
                                "  <lnk>"           + str(launcher["lnk"])      + "</lnk>\n" +
                                "  <finished>"      + str(launcher["finished"]) + "</finished>\n" +
                                "  <minimize>"      + str(launcher["minimize"]) + "</minimize>\n" +
                                "  <roms_xml_file>" + launcher["roms_xml_file"] + "</roms_xml_file>\n" +
                                "</launcher>\n")
            # End of file
            str_list.append('</advanced_emulator_launcher>\n')

            # Join string and escape XML characters
            full_string = ''.join(str_list)
            full_string = self._fs_escape_XML(full_string)

            # Save categories.xml file
            file_obj = open(CATEGORIES_FILE_PATH, 'wt' )
            file_obj.write(full_string)
            file_obj.close()
        except OSError:
            gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write categories.xml file. (OSError)')
        except IOError:
            gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write categories.xml file. (IOError)')

        # --- We are not busy anymore ---
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )

    #
    # Loads categories.xml from disk and fills dictionary self.categories
    #
    def _fs_load_catfile(self):
        __debug_xml_parser = 0
        self.categories = {}
        self.launchers = {}

        # --- Parse using cElementTree ---
        xbmc.log('Parsing {0}'.format(CATEGORIES_FILE_PATH))

        # If file = '' is not used then instead of reading a file CATEGORIES_FILE_PATH is considered a string!!!
        xml_tree = ET.parse(CATEGORIES_FILE_PATH)
        xml_root = xml_tree.getroot()
        for category_element in xml_root:
            if __debug_xml_parser: xbmc.log('Root child {0}'.format(category_element.tag))

            if category_element.tag == 'category':
                # Default values
                category = {'id' : '', 'name' : '', 'thumb' : '', 'fanart' : '', 'genre' : '', 'plot' : '', 'finished' : False}

                # Parse child tags of category
                for category_child in category_element:
                    # By default read strings
                    xml_text = category_child.text if category_child.text is not None else ''
                    xml_tag  = category_child.tag
                    if __debug_xml_parser: xbmc.log('{0} --> {1}'.format(xml_tag, xml_text))
                    category[xml_tag] = xml_text

                    # Now transform data depending on tag name
                    if xml_tag == 'finished':
                        xml_bool = False if xml_text == 'False' else True
                        category[xml_tag] = xml_bool

                # Add category to categories dictionary
                self.categories[category['id']] = category

            elif category_element.tag == 'launcher':
                # Default values
                launcher = {
                    "id" : '',
                    "name" : '', "category" : '', "application" : '',  "args" : '',
                    "rompath" : "", "thumbpath" : '', "fanartpath" : '',
                    "custompath" : "", "trailerpath" : "", "romext" : "", "gamesys" : '',
                    "thumb" : "", "fanart" : "", "genre" : "", "release" : "", "studio" : "",
                    "plot" : "",  "lnk" : False, "finished": False, "minimize" : False,
                    "roms_xml_file" : '' }

                # Parse child tags of category
                for category_child in category_element:
                    # By default read strings
                    xml_text = category_child.text if category_child.text is not None else ''
                    xml_tag  = category_child.tag
                    if __debug_xml_parser: xbmc.log('{0} --> {1}'.format(xml_tag, xml_text))
                    launcher[xml_tag] = xml_text

                    # Now transform data depending on tag name
                    if xml_tag == 'lnk' or xml_tag == 'finished' or xml_tag == 'minimize':
                        xml_bool = True if xml_text == 'True' else False
                        launcher[xml_tag] = xml_bool

                # Add launcher to categories dictionary
                self.launchers[launcher['id']] = launcher

    def _fs_escape_XML(self, str):
        return str.replace('&', '&amp;')

    #
    # Write to disk categories.xml
    #
    def _fs_write_ROM_XML_file(self, roms, launcherID, roms_xml_file):
        self._print_log('_fs_write_ROM_XML_file() Saving XML file {0}'.format(roms_xml_file))
       
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )

        # Original Angelscry method for generating the XML was to grow a string, like this
        # xml_content = 'test'
        # xml_content += 'more test'
        # However, this method is very slow because string has to be reallocated every time is grown.
        # It is much faster to create a list of string and them join them!
        # See https://waymoot.org/home/python_string/
        try:
            str_list = []
            str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
            str_list.append('<advanced_emulator_launcher_ROMs version="1.0">\n')

            # Print some information in the XML so the user can now which launcher created it.
            # Note that this is ignored when reading the file.
            str_list.append('<launcher>\n')
            str_list.append('  <id        >{0}</id>\n'.format(launcherID))
            str_list.append('  <name      >{0}</name>\n'.format(self.launchers[launcherID]['name']))            
            str_list.append('  <category  >{0}</category>\n'.format(self.launchers[launcherID]['category']))
            str_list.append('  <rompath   >{0}</rompath>\n'.format(self.launchers[launcherID]['rompath']))
            str_list.append('  <thumbpath >{0}</thumbpath>\n'.format(self.launchers[launcherID]['thumbpath']))
            str_list.append('  <fanartpath>{0}</fanartpath>\n'.format(self.launchers[launcherID]['fanartpath']))
            str_list.append('</launcher>\n')

            # Create list of ROMs
            for romID in sorted(roms, key = lambda x : roms[x]["name"]):
                rom = roms[romID]
                # Data which is not string must be converted to string
                str_list.append("<rom>\n" +
                                "  <id>"       + romID                + "</id>\n" +
                                "  <name>"     + rom["name"]          + "</name>\n" +
                                "  <filename>" + rom["filename"]      + "</filename>\n" +
                                "  <gamesys>"  + rom["gamesys"]       + "</gamesys>\n" +
                                "  <thumb>"    + rom["thumb"]         + "</thumb>\n" +
                                "  <fanart>"   + rom["fanart"]        + "</fanart>\n" +
                                "  <trailer>"  + rom["trailer"]       + "</trailer>\n" +
                                "  <custom>"   + rom["custom"]        + "</custom>\n" +
                                "  <genre>"    + rom["genre"]         + "</genre>\n" +
                                "  <release>"  + rom["release"]       + "</release>\n" +
                                "  <studio>"   + rom["studio"]        + "</studio>\n" +
                                "  <plot>"     + rom["plot"]          + "</plot>\n" +
                                "  <altapp>"   + rom["altapp"]        + "</altapp>\n" +
                                "  <altarg>"   + rom["altarg"]        + "</altarg>\n" +
                                "  <finished>" + str(rom["finished"]) + "</finished>\n" +
                                "</rom>\n")
            # End of file
            str_list.append('</advanced_emulator_launcher_ROMs>\n')

            # Join string and escape XML characters
            full_string = ''.join(str_list)
            full_string = self._fs_escape_XML(full_string)

            # Save categories.xml file
            file_obj = open(roms_xml_file, 'wt' )
            file_obj.write(full_string)
            file_obj.close()
        except OSError:
            gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write {0} file. (OSError)'.format(roms_xml_file))
        except IOError:
            gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write {0} file. (IOError)'.format(roms_xml_file))

        # --- We are not busy anymore ---
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )

    #
    # Loads a launcher XML with the ROMs
    #
    def _fs_load_ROM_XML_file(self, roms_xml_file):
        __debug_xml_parser = 0
        roms = {}

        # --- If file does not exist return empty dictionary ---
        if not os.path.isfile(roms_xml_file):
            return {}

        # --- Parse using cElementTree ---
        xbmc.log('_fs_load_ROM_XML_file() Loading XML file {0}'.format(roms_xml_file))
        xml_tree = ET.parse(roms_xml_file)
        xml_root = xml_tree.getroot()
        for root_element in xml_root:
            if __debug_xml_parser: xbmc.log('Root child {0}'.format(root_element.tag))

            if root_element.tag == 'rom':
                # Default values
                rom = {'id' : '', 'name' : '', "filename" : '', "gamesys" : '', "thumb" : '', "fanart" : '',
                       "trailer" : '', "custom" : '', "genre" : '', "release" : '', "studio" : '',
                       "plot" : '', "finished" : False, "altapp" : '', "altarg" : '' }
                for rom_child in root_element:
                    # By default read strings
                    xml_text = rom_child.text if rom_child.text is not None else ''
                    xml_tag  = rom_child.tag
                    if __debug_xml_parser: xbmc.log('{0} --> {1}'.format(xml_tag, xml_text))
                    rom[xml_tag] = xml_text
                    
                    # Now transform data depending on tag name
                    if xml_tag == 'finished':
                        xml_bool = True if xml_text == 'True' else False
                        rom[xml_tag] = xml_bool
                roms[rom['id']] = rom

        return roms

    #
    # Reads an NFO file with ROM information and places items in a dictionary.
    #
    def _fs_load_NFO_file(nfo_file):
        self._print_log('_fs_load_NFO_file() Loading "{0}"'.format(nfo_file))
        
        # Read file, put in a string and remove line endings
        ff = open(nfo_file, 'rt')
        nfo_str = ff.read().replace('\r', '').replace('\n', '')
        ff.close()

        # Fill default values
        nfo_dic = {'title' : '', 'platform' : '', 'year' : '', 'publisher' : '', 'genre' : '', 'plot' : ''}

        # Search for items
        item_title     = re.findall( "<title>(.*?)</title>", nfo_str )
        item_platform  = re.findall( "<platform>(.*?)</platform>", nfo_str )
        item_year      = re.findall( "<year>(.*?)</year>", nfo_str )
        item_publisher = re.findall( "<publisher>(.*?)</publisher>", nfo_str )
        item_genre     = re.findall( "<genre>(.*?)</genre>", nfo_str )
        item_plot      = re.findall( "<plot>(.*?)</plot>", nfo_str )

        if len(item_title) > 0:     nfo_dic['title']     = item_title[0]
        if len(item_title) > 0:     nfo_dic['platform']  = item_platform[0]
        if len(item_year) > 0:      nfo_dic['year']      = item_year[0]
        if len(item_publisher) > 0: nfo_dic['publisher'] = item_publisher[0]
        if len(item_genre) > 0:     nfo_dic['genre']     = item_genre[0]
        # Should end of lines deeconded from the XML file???
        # See http://stackoverflow.com/questions/2265966/xml-carriage-return-encoding
        if len(item_plot) > 0:
            plot_str = item_plot[0]
            plot_str.replace('&quot;', '"')
            nfo_dic['plot'] = plot_str

        # DEBUG
        self._print_log(' title     : "{0}"'.format(nfo_dic['title']))
        self._print_log(' platform  : "{0}"'.format(nfo_dic['platform']))
        self._print_log(' year      : "{0}"'.format(nfo_dic['year']))
        self._print_log(' publisher : "{0}"'.format(nfo_dic['publisher']))
        self._print_log(' genre     : "{0}"'.format(nfo_dic['genre']))
        self._print_log(' plot      : "{0}"'.format(nfo_dic['plot']))

        return nfo_dic

    def _remove_rom(self, launcherID, rom):
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(__language__( 30000 ), __language__( 30010 ) % self.launchers[launcherID]["roms"][rom]["name"])
        if (ret):
            self.launchers[launcherID]["roms"].pop(rom)
            self._save_launchers()
            if ( len(self.launchers[launcherID]["roms"]) == 0 ):
                xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._path))
            else:
                xbmc.executebuiltin("Container.Update")

    def _empty_launcher(self, launcherID):
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(__language__( 30000 ), __language__( 30133 ) % self.launchers[launcherID]["name"])
        if (ret):
            self.launchers[launcherID]["roms"].clear()
            self._save_launchers()
            xbmc.executebuiltin("Container.Update")
            
    def _remove_launcher(self, launcherID):
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(__language__( 30000 ), __language__( 30010 ) % self.launchers[launcherID]["name"])
        if (ret):
            category = self.launchers[launcherID]["category"]
            self.launchers.pop(launcherID)
            self._save_launchers()
            if ( not self._empty_cat(category) ):
                xbmc.executebuiltin("Container.Update")
            else:
                xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._path))

    def _remove_category(self, categoryID):
        dialog = xbmcgui.Dialog()
        launcher_list = []
        for launcherID in sorted(self.launchers.iterkeys()):
            if (self.launchers[launcherID]['category'] == categoryID):
                launcher_list.append(launcherID)
        if ( len(launcher_list) > 0 ):
            ret = dialog.yesno(__language__( 30000 ), __language__( 30345 ) % (self.categories[categoryID]["name"],len(launcher_list)), __language__( 30346 ) % self.categories[categoryID]["name"], __language__( 30010 ) % self.categories[categoryID]["name"])
            if (ret):
                for launcherID in launcher_list:
                    self.launchers.pop(launcherID)
                self.categories.pop(categoryID)
                self._save_launchers()
        else:
            ret = dialog.yesno(__language__( 30000 ), __language__( 30010 ) % self.categories[categoryID]["name"])
            if (ret):
                self.categories.pop(categoryID)
                self._save_launchers()
        xbmc.executebuiltin("Container.Update")

    #
    # Former _edit_rom()
    #
    def _command_edit_rom(self, launcher, rom):
        dialog = xbmcgui.Dialog()
        title=os.path.basename(self.launchers[launcher]["roms"][rom]["name"])
        if (self.launchers[launcher]["roms"][rom]["finished"] != "true"):
            finished_display = __language__( 30339 )
        else:
            finished_display = __language__( 30340 )
        type = dialog.select(__language__( 30300 ) % title, [__language__( 30338 ),__language__( 30301 ),__language__( 30302 ),__language__( 30303 ),finished_display,__language__( 30323 ),__language__( 30304 )])

        if (type == 0 ):
            # Scrap item (infos and images)
            self._full_scrap_rom(launcher,rom)

        if (type == 1 ):
            dialog = xbmcgui.Dialog()

            type2 = dialog.select(__language__( 30305 ), [__language__( 30311 ) % self.settings[ "datas_scraper" ],__language__( 30333 ),__language__( 30306 ) % self.launchers[launcher]["roms"][rom]["name"],__language__( 30308 ) % self.launchers[launcher]["roms"][rom]["release"],__language__( 30309 ) % self.launchers[launcher]["roms"][rom]["studio"],__language__( 30310 ) % self.launchers[launcher]["roms"][rom]["genre"],__language__( 30328 ) % self.launchers[launcher]["roms"][rom]["plot"][0:20],__language__( 30316 )])
                # Scrap rom Infos
            if (type2 == 0 ):
                self._scrap_rom(launcher,rom)
            if (type2 == 1 ):
                self._import_rom_nfo(launcher,rom)
            if (type2 == 2 ):
                # Edition of the rom title
                keyboard = xbmc.Keyboard(self.launchers[launcher]["roms"][rom]["name"], __language__( 30037 ))
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    title = keyboard.getText()
                    if ( title == "" ):
                        title = self.launchers[launcher]["roms"][rom]["name"]
                    self.launchers[launcher]["roms"][rom]["name"] = title.rstrip()
                    self._save_launchers()
            if (type2 == 3 ):
                # Edition of the rom release date
                keyboard = xbmc.Keyboard(self.launchers[launcher]["roms"][rom]["release"], __language__( 30038 ))
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    self.launchers[launcher]["roms"][rom]["release"] = keyboard.getText()
                    self._save_launchers()
            if (type2 == 4 ):
                # Edition of the rom studio name
                keyboard = xbmc.Keyboard(self.launchers[launcher]["roms"][rom]["studio"], __language__( 30039 ))
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    self.launchers[launcher]["roms"][rom]["studio"] = keyboard.getText()
                    self._save_launchers()
            if (type2 == 5 ):
                # Edition of the rom game genre
                keyboard = xbmc.Keyboard(self.launchers[launcher]["roms"][rom]["genre"], __language__( 30040 ))
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    self.launchers[launcher]["roms"][rom]["genre"] = keyboard.getText()
                    self._save_launchers()
            if (type2 == 6 ):
                # Import of the rom game plot
                text_file = xbmcgui.Dialog().browse(1,__language__( 30080 ),"files",".txt|.dat", False, False)
                if (os.path.isfile(text_file)):
                    text_plot = open(text_file)
                    string_plot = text_plot.read()
                    text_plot.close()
                    self.launchers[launcher]["roms"][rom]["plot"] = string_plot.replace('&quot;','"')
                    self._save_launchers()
            if (type2 == 7 ):
                self._export_rom_nfo(launcher,rom)

        if (type == 2 ):
            dialog = xbmcgui.Dialog()
            thumb_diag = __language__( 30312 ) % ( self.settings[ "thumbs_scraper" ] )
            if ( self.settings[ "thumbs_scraper" ] == "GameFAQs" ) | ( self.settings[ "thumbs_scraper" ] == "MobyGames" ):
                thumb_diag = __language__( 30321 ) % ( self.settings[ "thumbs_scraper" ],self.settings[ "display_game_region" ])
            if ( self.settings[ "thumbs_scraper" ] == "Google" ):
                thumb_diag = __language__( 30322 ) % ( self.settings[ "thumbs_scraper" ],self.settings[ "thumb_image_size_display" ].capitalize())
            type2 = dialog.select(__language__( 30302 ), [thumb_diag,__language__( 30332 ),__language__( 30313 )])
            if (type2 == 0 ):
                self._scrap_thumb_rom(launcher,rom)
            if (type2 == 1 ):
                # Import a rom thumbnail image
                image = xbmcgui.Dialog().browse(2,__language__( 30041 ),"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(self.launchers[launcher]["thumbpath"]))
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
                                    xbmc_notify(__language__( 30000 ), __language__( 30070 ),3000)
                                except OSError:
                                    xbmc_notify(__language__( 30000 ), __language__( 30063 ) % self.launchers[launcher]["roms"][rom]["name"],3000)

            if (type2 == 2 ):
                # Link to a rom thumbnail image
                if (self.launchers[launcher]["roms"][rom]["thumb"] == ""):
                    imagepath = self.launchers[launcher]["roms"][rom]["filename"]
                else:
                    imagepath = self.launchers[launcher]["roms"][rom]["thumb"]
                image = xbmcgui.Dialog().browse(2,__language__( 30041 ),"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(imagepath))
                if (image):
                    if (os.path.isfile(image)):
                        if ( self.launchers[launcher]["roms"][rom]["thumb"] != "" ):
                            _update_cache(image)
                        self.launchers[launcher]["roms"][rom]["thumb"] = image
                        self._save_launchers()
                        xbmc_notify(__language__( 30000 ), __language__( 30070 ),3000)

        if (type == 3 ):
            dialog = xbmcgui.Dialog()
            fanart_diag = __language__( 30312 ) % ( self.settings[ "fanarts_scraper" ] )
            if ( self.settings[ "fanarts_scraper" ] == "Google" ):
                fanart_diag = __language__( 30322 ) % ( self.settings[ "fanarts_scraper" ],self.settings[ "fanart_image_size_display" ].capitalize())
            type2 = dialog.select(__language__( 30303 ), [fanart_diag,__language__( 30332 ),__language__( 30313 )])
            if (type2 == 0 ):
                self._scrap_fanart_rom(launcher,rom)
            if (type2 == 1 ):
                # Import a rom fanart image
                image = xbmcgui.Dialog().browse(2,__language__( 30042 ),"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(self.launchers[launcher]["fanartpath"]))
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
                                    xbmc_notify(__language__( 30000 ), __language__( 30075 ),3000)
                                except OSError:
                                    xbmc_notify(__language__( 30000 ), __language__( 30064 ) % self.launchers[launcher]["roms"][rom]["name"],3000)
            if (type2 == 2 ):
                # Link to a rom fanart image
                if (self.launchers[launcher]["roms"][rom]["fanart"] == ""):
                    imagepath = self.launchers[launcher]["roms"][rom]["filename"]
                else:
                    imagepath = self.launchers[launcher]["roms"][rom]["fanart"]
                image = xbmcgui.Dialog().browse(2,__language__( 30042 ),"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(imagepath))
                if (image):
                    if (os.path.isfile(image)):
                        if ( self.launchers[launcher]["roms"][rom]["fanart"] != "" ):
                            _update_cache(image)
                        self.launchers[launcher]["roms"][rom]["fanart"] = image
                        self._save_launchers()
                        xbmc_notify(__language__( 30000 ), __language__( 30075 ),3000)

        if (type == 4 ):
            if (self.launchers[launcher]["roms"][rom]["finished"] != "true"):
                self.launchers[launcher]["roms"][rom]["finished"] = "true"
            else:
                self.launchers[launcher]["roms"][rom]["finished"] = "false"
            self._save_launchers()

        if (type == 5 ):
            dialog = xbmcgui.Dialog()
            type2 = dialog.select(__language__( 30323 ), [__language__( 30337 ) % self.launchers[launcher]["roms"][rom]["filename"], __language__( 30347 ) % self.launchers[launcher]["roms"][rom]["altapp"], __language__( 30348 ) % self.launchers[launcher]["roms"][rom]["altarg"], __language__( 30341 ) % self.launchers[launcher]["roms"][rom]["trailer"], __language__( 30331 ) % self.launchers[launcher]["roms"][rom]["custom"]])
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
                trailer = xbmcgui.Dialog().browse(1,__language__( 30090 ),"files",".mp4|.mpg|.avi|.wmv|.mkv|.flv", False, False, self.launchers[launcher]["roms"][rom]["trailer"])
                self.launchers[launcher]["roms"][rom]["trailer"] = trailer
                self._save_launchers()
            if (type2 == 4 ):
                # Selection of the rom customs path
                custom = xbmcgui.Dialog().browse(0,__language__( 30057 ),"files","", False, False, self.launchers[launcher]["roms"][rom]["custom"])
                self.launchers[launcher]["roms"][rom]["custom"] = custom
                self._save_launchers()

        if (type == 6 ):
            self._remove_rom(launcher,rom)

        # Return to the launcher directory
        xbmc.executebuiltin("Container.Refresh")

    def _scrap_thumb_rom_algo(self, launcher, rom, title):
        xbmc_notify(__language__( 30000 ), __language__( 30065 ) % (self.launchers[launcher]["roms"][rom]["name"],(self.settings[ "thumbs_scraper" ]).encode('utf-8','ignore')),300000)
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        covers = self._get_thumbnails_list(self.launchers[launcher]["roms"][rom]["gamesys"],title,self.settings["game_region"],self.settings[ "thumb_image_size" ])
        if covers:
            nb_images = len(covers)
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
            xbmc_notify(__language__( 30000 ), __language__( 30066 ) % (nb_images,self.launchers[launcher]["roms"][rom]["name"]),3000)
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
                            xbmc_notify(__language__( 30000 ), __language__( 30069 ),300000)
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
                                xbmc_notify(__language__( 30000 ), __language__( 30070 ),3000)
                            except socket.timeout:
                                xbmc_notify(__language__( 30000 ), __language__( 30081 ),3000)
                            except exceptions.IOError:
                                xbmc_notify(__language__( 30000 ), __language__( 30063 ) % self.launchers[launcher]["roms"][rom]["name"],3000)
                    else:
                        xbmc_notify(__language__( 30000 ), __language__( 30067 ) % (self.launchers[launcher]["roms"][rom]["name"]),3000)
        else:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
            xbmc_notify(__language__( 30000 ), __language__( 30067 ) % (self.launchers[launcher]["roms"][rom]["name"]),3000)

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
        xbmc_notify(__language__( 30000 ), __language__( 30065 ) % (self.launchers[launcherID]["name"],(self.settings[ "thumbs_scraper" ]).encode('utf-8','ignore')),30000)
        covers = self._get_thumbnails_list(self.launchers[launcherID]["gamesys"],title,self.settings["game_region"],self.settings[ "thumb_image_size" ])
        if covers:
            nb_images = len(covers)
            xbmc_notify(__language__( 30000 ), __language__( 30066 ) % (nb_images,self.launchers[launcherID]["name"]),3000)
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
                            xbmc_notify(__language__( 30000 ), __language__( 30069 ),300000)
                            try:
                                download_img(img_url,file_path)
                                if ( self.launchers[launcherID]["thumb"] != "" ):
                                    _update_cache(file_path)
                                self.launchers[launcherID]["thumb"] = file_path
                                self._save_launchers()
                                xbmc_notify(__language__( 30000 ), __language__( 30070 ),3000)
                            except socket.timeout:
                                xbmc_notify(__language__( 30000 ), __language__( 30081 ),3000)
                            except exceptions.IOError:
                                xbmc_notify(__language__( 30000 ), __language__( 30063 ) % self.launchers[launcherID]["name"],3000)
                    else:
                        xbmc_notify(__language__( 30000 ), __language__( 30067 ) % (self.launchers[launcherID]["name"]),3000)
        else:
            xbmc_notify(__language__( 30000 ), __language__( 30067 ) % (self.launchers[launcherID]["name"]),3000)

    def _scrap_thumb_category_algo(self, categoryID, title):
        xbmc_notify(__language__( 30000 ), __language__( 30065 ) % (self.categories[categoryID]["name"],(self.settings[ "thumbs_scraper" ]).encode('utf-8','ignore')),300000)
        covers = self._get_thumbnails_list("",title,"",self.settings[ "thumb_image_size" ])
        if covers:
            nb_images = len(covers)
            xbmc_notify(__language__( 30000 ), __language__( 30066 ) % (nb_images,self.categories[categoryID]["name"]),3000)
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
                            xbmc_notify(__language__( 30000 ), __language__( 30069 ),300000)
                            try:
                                download_img(img_url,file_path)
                                if ( self.categories[categoryID]["thumb"] != "" ):
                                    _update_cache(file_path)
                                self.categories[categoryID]["thumb"] = file_path
                                self._save_launchers()
                                xbmc_notify(__language__( 30000 ), __language__( 30070 ),3000)
                            except socket.timeout:
                                xbmc_notify(__language__( 30000 ), __language__( 30081 ),3000)
                            except exceptions.IOError:
                                xbmc_notify(__language__( 30000 ), __language__( 30063 ) % self.categories[categoryID]["name"],3000)
                    else:
                        xbmc_notify(__language__( 30000 ), __language__( 30067 ) % (self.categories[categoryID]["name"]),3000)
        else:
            xbmc_notify(__language__( 30000 ), __language__( 30067 ) % (self.categories[categoryID]["name"]),3000)

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
        xbmc_notify(__language__( 30000 ), __language__( 30071 ) % (self.launchers[launcher]["roms"][rom]["name"],self.settings[ "fanarts_scraper" ].encode('utf-8','ignore')),300000)
        full_fanarts = self._get_fanarts_list(self.launchers[launcher]["roms"][rom]["gamesys"],title,self.settings[ "fanart_image_size" ])
        if full_fanarts:
            nb_images = len(full_fanarts)
            xbmc_notify(__language__( 30000 ), __language__( 30072 ) % (nb_images,self.launchers[launcher]["roms"][rom]["name"]),3000)
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
                            xbmc_notify(__language__( 30000 ), __language__( 30074 ),300000)
                            try:
                                download_img(img_url,file_path)
                                if ( self.launchers[launcher]["roms"][rom]["fanart"] != "" ):
                                    _update_cache(file_path)
                                self.launchers[launcher]["roms"][rom]["fanart"] = file_path
                                self._save_launchers()
                                xbmc_notify(__language__( 30000 ), __language__( 30075 ),3000)
                            except socket.timeout:
                                xbmc_notify(__language__( 30000 ), __language__( 30081 ),3000)
                            except exceptions.IOError:
                                xbmc_notify(__language__( 30000 ), __language__( 30064 ) % self.launchers[launcher]["roms"][rom]["name"],3000)
                    else:
                        xbmc_notify(__language__( 30000 ), __language__( 30073 ) % (self.launchers[launcher]["roms"][rom]["name"]),3000)
        else:
            xbmc_notify(__language__( 30000 ), __language__( 30073 ) % (self.launchers[launcher]["roms"][rom]["name"]),3000)

    def _scrap_fanart_category_algo(self, categoryID, title):
        xbmc_notify(__language__( 30000 ), __language__( 30071 ) % (self.categories[categoryID]["name"],(self.settings[ "fanarts_scraper" ]).encode('utf-8','ignore')),300000)
        covers = self._get_fanarts_list("",title,self.settings[ "fanart_image_size" ])
        if covers:
            nb_images = len(covers)
            xbmc_notify(__language__( 30000 ), __language__( 30072 ) % (nb_images,self.categories[categoryID]["name"]),3000)
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
                            xbmc_notify(__language__( 30000 ), __language__( 30074 ),300000)
                            try:
                                download_img(img_url,file_path)
                                if ( self.categories[categoryID]["fanart"] != "" ):
                                    _update_cache(file_path)
                                self.categories[categoryID]["fanart"] = file_path
                                self._save_launchers()
                                xbmc_notify(__language__( 30000 ), __language__( 30075 ),3000)
                            except socket.timeout:
                                xbmc_notify(__language__( 30000 ), __language__( 30081 ),3000)
                            except exceptions.IOError:
                                xbmc_notify(__language__( 30000 ), __language__( 30064 ) % self.categories[categoryID]["name"],3000)
                    else:
                        xbmc_notify(__language__( 30000 ), __language__( 30073 ) % (self.categories[categoryID]["name"]),3000)
        else:
            xbmc_notify(__language__( 30000 ), __language__( 30073 ) % (self.categories[categoryID]["name"]),3000)

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
        xbmc_notify(__language__( 30000 ), __language__( 30071 ) % (self.launchers[launcherID]["name"],(self.settings[ "fanarts_scraper" ]).encode('utf-8','ignore')),300000)
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        covers = self._get_fanarts_list(self.launchers[launcherID]["gamesys"],title,self.settings[ "fanart_image_size" ])
        if covers:
            nb_images = len(covers)
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
            xbmc_notify(__language__( 30000 ), __language__( 30072 ) % (nb_images,self.launchers[launcherID]["name"]),3000)
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
                            xbmc_notify(__language__( 30000 ), __language__( 30074 ),300000)
                            try:
                                download_img(img_url,file_path)
                                if ( self.launchers[launcherID]["fanart"] != "" ):
                                    _update_cache(file_path)
                                self.launchers[launcherID]["fanart"] = file_path
                                self._save_launchers()
                                xbmc_notify(__language__( 30000 ), __language__( 30075 ),3000)
                            except socket.timeout:
                                xbmc_notify(__language__( 30000 ), __language__( 30081 ),3000)
                            except exceptions.IOError:
                                xbmc_notify(__language__( 30000 ), __language__( 30064 ) % self.launchers[launcherID]["name"],3000)
                    else:
                        xbmc_notify(__language__( 30000 ), __language__( 30073 ) % (self.launchers[launcherID]["name"]),3000)
        else:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
            xbmc_notify(__language__( 30000 ), __language__( 30073 ) % (self.launchers[launcherID]["name"]),3000)

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
                selectgame = dialog.select(__language__( 30078 ) % ( self.settings[ "datas_scraper" ] ), display)
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
                xbmc_notify(__language__( 30000 ), __language__( 30076 ),3000)
    
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

    def _import_rom_nfo(self, launcher, rom):
        # Edition of the rom name
        nfo_file=os.path.splitext(self.launchers[launcher]["roms"][rom]["filename"])[0]+".nfo"
        if (os.path.isfile(nfo_file)):
            f = open(nfo_file, 'r')
            item_nfo = f.read().replace('\r','').replace('\n','')
            f.close()
            item_title = re.findall( "<title>(.*?)</title>", item_nfo )
            item_platform = re.findall( "<platform>(.*?)</platform>", item_nfo )
            item_year = re.findall( "<year>(.*?)</year>", item_nfo )
            item_publisher = re.findall( "<publisher>(.*?)</publisher>", item_nfo )
            item_genre = re.findall( "<genre>(.*?)</genre>", item_nfo )
            item_plot = re.findall( "<plot>(.*?)</plot>", item_nfo )
            if len(item_title) > 0 : self.launchers[launcher]["roms"][rom]["name"] = item_title[0].rstrip()
            self.launchers[launcher]["roms"][rom]["gamesys"] = self.launchers[launcher]["gamesys"]
            if len(item_year) > 0 :  self.launchers[launcher]["roms"][rom]["release"] = item_year[0]
            if len(item_publisher) > 0 : self.launchers[launcher]["roms"][rom]["studio"] = item_publisher[0]
            if len(item_genre) > 0 : self.launchers[launcher]["roms"][rom]["genre"] = item_genre[0]
            if len(item_plot) > 0 : self.launchers[launcher]["roms"][rom]["plot"] = item_plot[0].replace('&quot;','"')
            self._save_launchers()
            xbmc_notify(__language__( 30000 ), __language__( 30083 ) % os.path.basename(nfo_file),3000)
        else:
            xbmc_notify(__language__( 30000 ), __language__( 30082 ) % os.path.basename(nfo_file),3000)

    def _export_rom_nfo(self, launcher, rom):
        nfo_file=os.path.splitext(self.launchers[launcher]["roms"][rom]["filename"].decode(get_encoding()))[0]+".nfo"
        if (os.path.isfile(nfo_file)):
            shutil.move( nfo_file, nfo_file+".tmp" )
            destination= open( nfo_file, "w" )
            source= open( nfo_file+".tmp", "r" )
            first_genre=0
            for line in source:
                item_title = re.findall( "<title>(.*?)</title>", line )
                item_platform = re.findall( "<platform>(.*?)</platform>", line )
                item_year = re.findall( "<year>(.*?)</year>", line )
                item_publisher = re.findall( "<publisher>(.*?)</publisher>", line )
                item_genre = re.findall( "<genre>(.*?)</genre>", line )
                item_plot = re.findall( "<plot>(.*?)</plot>", line )
                if len(item_title) > 0 : line = "\t<title>"+self.launchers[launcher]["roms"][rom]["name"]+"</title>\n"
                if len(item_platform) > 0 : line = "\t<platform>"+self.launchers[launcher]["roms"][rom]["gamesys"]+"</platform>\n"
                if len(item_year) > 0 : line = "\t<year>"+self.launchers[launcher]["roms"][rom]["release"]+"</year>\n"
                if len(item_publisher) > 0 : line = "\t<publisher>"+self.launchers[launcher]["roms"][rom]["studio"]+"</publisher>\n"
                if len(item_genre) > 0 :
                    if first_genre == 0 :
                        line = "\t<genre>"+self.launchers[launcher]["roms"][rom]["genre"]+"</genre>\n"
                        first_genre = 1
                if len(item_plot) > 0 : line = "\t<plot>"+self.launchers[launcher]["roms"][rom]["plot"]+"</plot>\n"
                destination.write( line )
            source.close()
            destination.close()
            os.remove(nfo_file+".tmp")
            xbmc_notify(__language__( 30000 ), __language__( 30087 ) % os.path.basename(nfo_file).encode('utf8','ignore'),3000)
        else:
            nfo_content = "<game>\n\t<title>"+self.launchers[launcher]["roms"][rom]["name"]+"</title>\n\t<platform>"+self.launchers[launcher]["roms"][rom]["gamesys"]+"</platform>\n\t<year>"+self.launchers[launcher]["roms"][rom]["release"]+"</year>\n\t<publisher>"+self.launchers[launcher]["roms"][rom]["studio"]+"</publisher>\n\t<genre>"+self.launchers[launcher]["roms"][rom]["genre"]+"</genre>\n\t<plot>"+self.launchers[launcher]["roms"][rom]["plot"]+"</plot>\n</game>\n"
            usock = open( nfo_file, 'w' )
            usock.write(nfo_content)
            usock.close()
            xbmc_notify(__language__( 30000 ), __language__( 30086 ) % os.path.basename(nfo_file).encode('utf8','ignore'),3000)

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

    def _modify_category(self, categoryID):
        dialog = xbmcgui.Dialog()
        type2 = dialog.select(__language__( 30344 ),[__language__( 30306 ) % self.categories[categoryID]["name"],__language__( 30310 ) % self.categories[categoryID]["genre"],__language__( 30328 ) % self.categories[categoryID]["plot"]])
        if (type2 == 0 ):
            # Edition of the category name
            keyboard = xbmc.Keyboard(self.categories[categoryID]["name"], __language__( 30037 ))
            keyboard.doModal()
            if (keyboard.isConfirmed()):
                title = keyboard.getText()
                if ( title == "" ):
                    title = self.categories[categoryID]["name"]
                self.categories[categoryID]["name"] = title.rstrip()
                self._save_launchers()
        if (type2 == 1 ):
            # Edition of the category genre
            keyboard = xbmc.Keyboard(self.categories[categoryID]["genre"], __language__( 30040 ))
            keyboard.doModal()
            if (keyboard.isConfirmed()):
                self.categories[categoryID]["genre"] = keyboard.getText()
                self._save_launchers()
        if (type2 == 2 ):
            # Import category description
            text_file = xbmcgui.Dialog().browse(1,__language__( 30080 ),"files",".txt|.dat", False, False)
            if ( os.path.isfile(text_file) == True ):
                text_plot = open(text_file, 'r')
                self.categories[categoryID]["plot"] = text_plot.read()
                text_plot.close()
                self._save_launchers()

    def _command_edit_category(self, categoryID):
        dialog = xbmcgui.Dialog()
        if (self.categories[categoryID]["finished"] != "true"):
            finished_display = __language__( 30339 )
        else:
            finished_display = __language__( 30340 )
        type = dialog.select(__language__( 30300 ) % self.categories[categoryID]["name"], [__language__( 30301 ),__language__( 30302 ),__language__( 30303 ),finished_display,__language__( 30304 )])
        if (type == 0 ):
            self._modify_category(categoryID)
        # Category Thumb menu option
        if (type == 1 ):
            dialog = xbmcgui.Dialog()
            thumb_diag = __language__( 30312 ) % ( self.settings[ "thumbs_scraper" ] )
            if ( self.settings[ "thumbs_scraper" ] == "Google" ):
                thumb_diag = __language__( 30322 ) % ( self.settings[ "thumbs_scraper" ],self.settings[ "thumb_image_size_display" ].capitalize())
            type2 = dialog.select(__language__( 30302 ), [thumb_diag,__language__( 30332 ),__language__( 30313 )])
            if (type2 == 0 ):
                self._scrap_thumb_category(categoryID)
            if (type2 == 1 ):
                # Import a category thumbnail image
                image = xbmcgui.Dialog().browse(2,__language__( 30041 ),"files",".jpg|.jpeg|.gif|.png", True, False, DEFAULT_THUMB_PATH)
                if (image):
                    if (os.path.isfile(image)):
                        img_ext = os.path.splitext(image)[-1][0:4]
                        if ( img_ext != '' ):
                            filename = self.categories[categoryID]["name"]
                            file_path = os.path.join(DEFAULT_THUMB_PATH,os.path.basename(self.categories[categoryID]["name"])+'_thumb'+img_ext)
                            if ( image != file_path ):
                                try:
                                    shutil.copy2( image.decode(get_encoding(),'ignore') , file_path.decode(get_encoding(),'ignore') )
                                    if ( self.categories[categoryID]["thumb"] != "" ):
                                        _update_cache(file_path)
                                    self.categories[categoryID]["thumb"] = file_path
                                    self._save_launchers()
                                    xbmc_notify(__language__( 30000 ), __language__( 30070 ),3000)
                                except OSError:
                                    xbmc_notify(__language__( 30000 ), __language__( 30063 ) % self.categories[categoryID]["name"],3000)
            if (type2 == 2 ):
                # Link to a category thumbnail image
                if (self.categories[categoryID]["thumb"] == ""):
                    imagepath = DEFAULT_THUMB_PATH
                else:
                    imagepath = self.categories[categoryID]["thumb"]
                image = xbmcgui.Dialog().browse(2,__language__( 30041 ),"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(imagepath))
                if (image):
                    if (os.path.isfile(image)):
                        if ( self.categories[categoryID]["thumb"] != "" ):
                            _update_cache(image)
                        self.categories[categoryID]["thumb"] = image
                        self._save_launchers()
                        xbmc_notify(__language__( 30000 ), __language__( 30070 ),3000)

        # Launcher Fanart menu option
        if (type == 2 ):
            dialog = xbmcgui.Dialog()
            fanart_diag = __language__( 30312 ) % ( self.settings[ "fanarts_scraper" ] )
            if ( self.settings[ "fanarts_scraper" ] == "Google" ):
                fanart_diag = __language__( 30322 ) % ( self.settings[ "fanarts_scraper" ],self.settings[ "fanart_image_size_display" ].capitalize())
            type2 = dialog.select(__language__( 30303 ), [fanart_diag,__language__( 30332 ),__language__( 30313 )])
            if (type2 == 0 ):
                self._scrap_fanart_category(categoryID)
            if (type2 == 1 ):
                # Import a Category fanart image
                image = xbmcgui.Dialog().browse(2,__language__( 30042 ),"files",".jpg|.jpeg|.gif|.png", True, False, DEFAULT_FANART_PATH)
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
                                    xbmc_notify(__language__( 30000 ), __language__( 30075 ),3000)
                                except OSError:
                                    xbmc_notify(__language__( 30000 ), __language__( 30064 ) % self.categories[categoryID]["name"],3000)
            if (type2 == 2 ):
                # Link to a category fanart image
                if (self.categories[categoryID]["fanart"] == ""):
                    imagepath = DEFAULT_FANART_PATH
                else:
                    imagepath = self.categories[categoryID]["fanart"]
                image = xbmcgui.Dialog().browse(2,__language__( 30042 ),"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(imagepath))
                if (image):
                    if (os.path.isfile(image)):
                        if ( self.categories[categoryID]["fanart"] != "" ):
                            _update_cache(image)
                        self.categories[categoryID]["fanart"] = image
                        self._save_launchers()
                        xbmc_notify(__language__( 30000 ), __language__( 30075 ),3000)

        # Category status
        if (type == 3 ):
            if (self.categories[categoryID]["finished"] != "true"):
                self.categories[categoryID]["finished"] = "true"
            else:
                self.categories[categoryID]["finished"] = "false"
            self._save_launchers()

        if (type == 4 ):
            self._remove_category(categoryID)

        if (type == -1 ):
            self._save_launchers()

        # Return to the category directory
        xbmc.executebuiltin("Container.Refresh")

    def _command_edit_launcher(self, launcherID):
        dialog = xbmcgui.Dialog()
        title=os.path.basename(self.launchers[launcherID]["name"])
        if (self.launchers[launcherID]["finished"] != "true"):
            finished_display = __language__( 30339 )
        else:
            finished_display = __language__( 30340 )
        if ( self.launchers[launcherID]["rompath"] == "" ):
            type = dialog.select(__language__( 30300 ) % title, [__language__( 30338 ),__language__( 30301 ),__language__( 30302 ),__language__( 30303 ),__language__( 30342 ) % self.categories[self.launchers[launcherID]["category"]]['name'],finished_display,__language__( 30323 ),__language__( 30304 )])
        else:
            type = dialog.select(__language__( 30300 ) % title, [__language__( 30338 ),__language__( 30301 ),__language__( 30302 ),__language__( 30303 ),__language__( 30342 ) % self.categories[self.launchers[launcherID]["category"]]['name'],finished_display,__language__( 30334 ),__language__( 30323 ),__language__( 30304 )])
        type_nb = 0

        # Scrap item (infos and images)
        if (type == type_nb ):
            self._full_scrap_launcher(launcherID)

        # Edition of the launcher infos
        type_nb = type_nb+1
        if (type == type_nb ):
            dialog = xbmcgui.Dialog()
            type2 = dialog.select(__language__( 30319 ), [__language__( 30311 ) % self.settings[ "datas_scraper" ],__language__( 30306 ) % self.launchers[launcherID]["name"],__language__( 30307 ) % self.launchers[launcherID]["gamesys"],__language__( 30308 ) % self.launchers[launcherID]["release"],__language__( 30309 ) % self.launchers[launcherID]["studio"],__language__( 30310 ) % self.launchers[launcherID]["genre"],__language__( 30328 ) % self.launchers[launcherID]["plot"][0:20],__language__( 30333 ),__language__( 30316 )])
            if (type2 == 0 ):
                # Edition of the launcher name
                self._scrap_launcher(launcherID)
            if (type2 == 1 ):
                # Edition of the launcher name
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["name"], __language__( 30037 ))
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    title = keyboard.getText()
                    if ( title == "" ):
                        title = self.launchers[launcherID]["name"]
                    self.launchers[launcherID]["name"] = title.rstrip()
                    self._save_launchers()
            if (type2 == 2 ):
                # Selection of the launcher game system
                dialog = xbmcgui.Dialog()
                platforms = _get_game_system_list()
                gamesystem = dialog.select(__language__( 30077 ), platforms)
                if (not gamesystem == -1 ):
                    self.launchers[launcherID]["gamesys"] = platforms[gamesystem]
                    self._save_launchers()
            if (type2 == 3 ):
                # Edition of the launcher release date
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["release"], __language__( 30038 ))
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    self.launchers[launcherID]["release"] = keyboard.getText()
                    self._save_launchers()
            if (type2 == 4 ):
                # Edition of the launcher studio name
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["studio"], __language__( 30039 ))
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    self.launchers[launcherID]["studio"] = keyboard.getText()
                    self._save_launchers()
            if (type2 == 5 ):
                # Edition of the launcher genre
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["genre"], __language__( 30040 ))
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    self.launchers[launcherID]["genre"] = keyboard.getText()
                    self._save_launchers()
            if (type2 == 6 ):
                # Import of the launcher plot
                text_file = xbmcgui.Dialog().browse(1,__language__( 30080 ),"files",".txt|.dat", False, False, self.launchers[launcherID]["application"])
                if ( os.path.isfile(text_file) == True ):
                    text_plot = open(text_file, 'r')
                    self.launchers[launcherID]["plot"] = text_plot.read()
                    text_plot.close()
                    self._save_launchers()
            if (type2 == 7 ):
                # Edition of the launcher name
                self._import_launcher_nfo(launcherID)
            if (type2 == 8 ):
                # Edition of the launcher name
                self._export_launcher_nfo(launcherID)

        # Launcher Thumbnail menu option
        type_nb = type_nb+1
        if (type == type_nb ):
            dialog = xbmcgui.Dialog()
            thumb_diag = __language__( 30312 ) % ( self.settings[ "thumbs_scraper" ] )
            if ( self.settings[ "thumbs_scraper" ] == "GameFAQs" ) | ( self.settings[ "thumbs_scraper" ] == "MobyGames" ):
                thumb_diag = __language__( 30321 ) % ( self.settings[ "thumbs_scraper" ],self.settings[ "display_game_region" ])
            if ( self.settings[ "thumbs_scraper" ] == "Google" ):
                thumb_diag = __language__( 30322 ) % ( self.settings[ "thumbs_scraper" ],self.settings[ "thumb_image_size_display" ])
            type2 = dialog.select(__language__( 30302 ), [thumb_diag,__language__( 30332 ),__language__( 30313 )])
            if (type2 == 0 ):
                self._scrap_thumb_launcher(launcherID)
            if (type2 == 1 ):
                # Import a Launcher thumbnail image
                image = xbmcgui.Dialog().browse(2,__language__( 30041 ),"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(self.launchers[launcherID]["thumbpath"]))
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
                                    xbmc_notify(__language__( 30000 ), __language__( 30070 ),3000)
                                except OSError:
                                    xbmc_notify(__language__( 30000 ), __language__( 30063 ) % self.launchers[launcherID]["name"],3000)

            if (type2 == 2 ):
                # Link to a launcher thumbnail image
                if (self.launchers[launcherID]["thumb"] == ""):
                    imagepath = self.launchers[launcherID]["thumbpath"]
                else:
                    imagepath = self.launchers[launcherID]["thumb"]
                image = xbmcgui.Dialog().browse(2,__language__( 30041 ),"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(imagepath))
                if (image):
                    if (os.path.isfile(image)):
                        if ( self.launchers[launcherID]["thumb"] != "" ):
                            _update_cache(image)
                        self.launchers[launcherID]["thumb"] = image
                        self._save_launchers()
                        xbmc_notify(__language__( 30000 ), __language__( 30070 ),3000)

        # Launcher Fanart menu option
        type_nb = type_nb+1
        if (type == type_nb ):
            dialog = xbmcgui.Dialog()
            fanart_diag = __language__( 30312 ) % ( self.settings[ "fanarts_scraper" ] )
            if ( self.settings[ "fanarts_scraper" ] == "Google" ):
                fanart_diag = __language__( 30322 ) % ( self.settings[ "fanarts_scraper" ],self.settings[ "fanart_image_size_display" ].capitalize())
            type2 = dialog.select(__language__( 30303 ), [fanart_diag,__language__( 30332 ),__language__( 30313 )])
            if (type2 == 0 ):
                self._scrap_fanart_launcher(launcherID)
            if (type2 == 1 ):
                # Import a Launcher fanart image
                image = xbmcgui.Dialog().browse(2,__language__( 30042 ),"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(self.launchers[launcherID]["fanartpath"]))
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
                                    xbmc_notify(__language__( 30000 ), __language__( 30070 ),3000)
                                except OSError:
                                    xbmc_notify(__language__( 30000 ), __language__( 30064 ) % self.launchers[launcherID]["name"],3000)
            if (type2 == 2 ):
                # Link to a launcher fanart image
                if (self.launchers[launcherID]["fanart"] == ""):
                    imagepath = self.launchers[launcherID]["fanartpath"]
                else:
                    imagepath = self.launchers[launcherID]["fanart"]
                image = xbmcgui.Dialog().browse(2,__language__( 30042 ),"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(imagepath))
                if (image):
                    if (os.path.isfile(image)):
                        if ( self.launchers[launcherID]["fanart"] != "" ):
                            _update_cache(image)
                        self.launchers[launcherID]["fanart"] = image
                        self._save_launchers()
                        xbmc_notify(__language__( 30000 ), __language__( 30075 ),3000)

        # Launcher's change category
        type_nb = type_nb+1
        if (type == type_nb ):
            current_category = self.launchers[launcherID]["category"]
            dialog = xbmcgui.Dialog()
            categories_id = []
            categories_name = []
            for key in self.categories:
                categories_id.append(self.categories[key]['id'])
                categories_name.append(self.categories[key]['name'])
            selected_cat = dialog.select(__language__( 30114 ), categories_name)
            if (not selected_cat == -1 ):
                self.launchers[launcherID]["category"] = categories_id[selected_cat]
                self._save_launchers()
                xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self._path, categories_id[selected_cat]))

        # Launcher status
        type_nb = type_nb+1
        if (type == type_nb ):
            if (self.launchers[launcherID]["finished"] != "true"):
                self.launchers[launcherID]["finished"] = "true"
            else:
                self.launchers[launcherID]["finished"] = "false"
            self._save_launchers()

        # Launcher's Items List menu option
        if ( self.launchers[launcherID]["rompath"] != "" ):
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
        if (type == type_nb ):
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
            if ( self.launchers[launcherID]["rompath"] != "" ):
                if (sys.platform == 'win32'):
                    type2 = dialog.select(__language__( 30323 ), [__language__( 30327 ) % self.launchers[launcherID]["application"],__language__( 30315 ) % self.launchers[launcherID]["args"],__language__( 30324 ) % self.launchers[launcherID]["rompath"],__language__( 30317 ) % self.launchers[launcherID]["romext"],__language__( 30325 ) % self.launchers[launcherID]["thumbpath"], __language__( 30326 ) % self.launchers[launcherID]["fanartpath"], __language__( 30341 ) % self.launchers[launcherID]["trailerpath"], __language__( 30331 ) % self.launchers[launcherID]["custompath"],__language__( 30329 ) % minimize_str,__language__( 30330 ) % lnk_str])
                else:
                    type2 = dialog.select(__language__( 30323 ), [__language__( 30327 ) % self.launchers[launcherID]["application"],__language__( 30315 ) % self.launchers[launcherID]["args"],__language__( 30324 ) % self.launchers[launcherID]["rompath"],__language__( 30317 ) % self.launchers[launcherID]["romext"],__language__( 30325 ) % self.launchers[launcherID]["thumbpath"], __language__( 30326 ) % self.launchers[launcherID]["fanartpath"], __language__( 30341 ) % self.launchers[launcherID]["trailerpath"], __language__( 30331 ) % self.launchers[launcherID]["custompath"],__language__( 30329 ) % minimize_str])
            else:
                if (sys.platform == 'win32'):
                    type2 = dialog.select(__language__( 30323 ), [__language__( 30327 ) % self.launchers[launcherID]["application"],__language__( 30315 ) % self.launchers[launcherID]["args"],__language__( 30325 ) % self.launchers[launcherID]["thumbpath"], __language__( 30326 ) % self.launchers[launcherID]["fanartpath"], __language__( 30341 ) % self.launchers[launcherID]["trailerpath"], __language__( 30331 ) % self.launchers[launcherID]["custompath"],__language__( 30329 ) % minimize_str,__language__( 30330 ) % lnk_str])
                else:
                    type2 = dialog.select(__language__( 30323 ), [__language__( 30327 ) % self.launchers[launcherID]["application"],__language__( 30315 ) % self.launchers[launcherID]["args"],__language__( 30325 ) % self.launchers[launcherID]["thumbpath"], __language__( 30326 ) % self.launchers[launcherID]["fanartpath"], __language__( 30341 ) % self.launchers[launcherID]["trailerpath"], __language__( 30331 ) % self.launchers[launcherID]["custompath"],__language__( 30329 ) % minimize_str])

            # Launcher application path menu option
            type2_nb = 0
            if (type2 == type2_nb ):
                app = xbmcgui.Dialog().browse(1,__language__( 30023 ),"files","", False, False, self.launchers[launcherID]["application"])
                self.launchers[launcherID]["application"] = app

            # Edition of the launcher arguments
            type2_nb = type2_nb +1
            if (type2 == type2_nb ):
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["args"], __language__( 30052 ))
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    self.launchers[launcherID]["args"] = keyboard.getText()
                    self._save_launchers()

            if ( self.launchers[launcherID]["rompath"] != "" ):
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
            if (type2 == type2_nb ):
                thumb_path = xbmcgui.Dialog().browse(0,__language__( 30059 ),"files","", False, False, self.launchers[launcherID]["thumbpath"])
                self.launchers[launcherID]["thumbpath"] = thumb_path
            # Launcher fanarts path menu option
            type2_nb = type2_nb + 1
            if (type2 == type2_nb ):
                fanart_path = xbmcgui.Dialog().browse(0,__language__( 30060 ),"files","", False, False, self.launchers[launcherID]["fanartpath"])
                self.launchers[launcherID]["fanartpath"] = fanart_path
            # Launcher trailer file menu option
            type2_nb = type2_nb + 1
            if (type2 == type2_nb ):
                fanart_path = xbmcgui.Dialog().browse(1,__language__( 30090 ),"files",".mp4|.mpg|.avi|.wmv|.mkv|.flv", False, False, self.launchers[launcherID]["trailerpath"])
                self.launchers[launcherID]["trailerpath"] = fanart_path
            # Launcher custom path menu option
            type2_nb = type2_nb + 1
            if (type2 == type2_nb ):
                fanart_path = xbmcgui.Dialog().browse(0,__language__( 30057 ),"files","", False, False, self.launchers[launcherID]["custompath"])
                self.launchers[launcherID]["custompath"] = fanart_path
            # Launcher minimize state menu option
            type2_nb = type2_nb + 1
            if (type2 == type2_nb ):
                dialog = xbmcgui.Dialog()
                type3 = dialog.select(__language__( 30203 ), ["%s (%s)" % (__language__( 30205 ),__language__( 30201 )), "%s" % (__language__( 30204 ))])
                if (type3 == 1 ):
                    self.launchers[launcherID]["minimize"] = "true"
                else:
                    self.launchers[launcherID]["minimize"] = "false"
            self._save_launchers()
            # Launcher internal lnk option
            if (sys.platform == 'win32'):
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
        if (type == type_nb ):
            self._remove_launcher(launcherID)

        if (type == -1 ):
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
            selectgame = dialog.select(__language__( 30078 ) % ( self.settings[ "datas_scraper" ] ), display)
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
            xbmc_notify(__language__( 30000 ), __language__( 30076 ),3000)

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
            xbmc_notify(__language__( 30000 ), __language__( 30083 ) % os.path.basename(nfo_file),3000)
        else:
            xbmc_notify(__language__( 30000 ), __language__( 30082 ) % os.path.basename(nfo_file),3000)

    def _export_items_list_nfo(self, launcherID):
        for rom in self.launchers[launcherID]["roms"].iterkeys():
            self._export_rom_nfo(launcherID, rom)

    def _import_items_list_nfo(self, launcherID):
        for rom in self.launchers[launcherID]["roms"].iterkeys():
            self._import_rom_nfo(launcherID, rom)

    def _export_launcher_nfo(self, launcherID):
        if ( len(self.launchers[launcherID]["rompath"]) > 0 ):
            nfo_file = os.path.join(self.launchers[launcherID]["rompath"],os.path.basename(os.path.splitext(self.launchers[launcherID]["application"])[0]+".nfo"))
        else:
            if ( len(self.settings[ "launcher_nfo_path" ]) > 0 ):
                nfo_file = os.path.join(self.settings[ "launcher_nfo_path" ],os.path.basename(os.path.splitext(self.launchers[launcherID]["application"])[0]+".nfo"))
            else:
                nfo_path = xbmcgui.Dialog().browse(0,__language__( 30089 ),"files",".nfo", False, False)
                nfo_file = os.path.join(nfo_path,os.path.basename(os.path.splitext(self.launchers[launcherID]["application"])[0]+".nfo"))
        if (os.path.isfile(nfo_file)):
            shutil.move( nfo_file, nfo_file+".tmp" )
            destination= open( nfo_file, "w" )
            source= open( nfo_file+".tmp", "r" )
            for line in source:
                item_title = re.findall( "<title>(.*?)</title>", line )
                item_platform = re.findall( "<platform>(.*?)</platform>", line )
                item_year = re.findall( "<year>(.*?)</year>", line )
                item_publisher = re.findall( "<publisher>(.*?)</publisher>", line )
                item_genre = re.findall( "<genre>(.*?)</genre>", line )
                item_plot = re.findall( "<plot>(.*?)</plot>", line )
                if len(item_title) > 0 : line = "\t<title>"+self.launchers[launcherID]["name"]+"</title>\n"
                if len(item_platform) > 0 : line = "\t<platform>"+self.launchers[launcherID]["gamesys"]+"</platform>\n"
                if len(item_year) > 0 : line = "\t<year>"+self.launchers[launcherID]["release"]+"</year>\n"
                if len(item_publisher) > 0 : line = "\t<publisher>"+self.launchers[launcherID]["studio"]+"</publisher>\n"
                if len(item_genre) > 0 : line = "\t<genre>"+self.launchers[launcherID]["genre"]+"</genre>\n"
                if len(item_plot) > 0 : line = "\t<plot>"+self.launchers[launcherID]["plot"]+"</plot>\n"
                destination.write( line )
            source.close()
            destination.close()
            os.remove(nfo_file+".tmp")
            xbmc_notify(__language__( 30000 ), __language__( 30087 ) % os.path.basename(nfo_file),3000)
        else:
            nfo_content = "<launcher>\n\t<title>"+self.launchers[launcherID]["name"]+"</title>\n\t<platform>"+self.launchers[launcherID]["gamesys"]+"</platform>\n\t<year>"+self.launchers[launcherID]["release"]+"</year>\n\t<publisher>"+self.launchers[launcherID]["studio"]+"</publisher>\n\t<genre>"+self.launchers[launcherID]["genre"]+"</genre>\n\t<plot>"+self.launchers[launcherID]["plot"]+"</plot>\n</launcher>\n"
            usock = open( nfo_file, 'w' )
            usock.write(nfo_content)
            usock.close()
            xbmc_notify(__language__( 30000 ), __language__( 30086 ) % os.path.basename(nfo_file),3000)

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

    def _print_log(self,string):
        if(self.settings["show_log"]):
            xbmc.log("AEL: " + string)

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

    #
    # Reads a XML text file and return file contents as a string.
    # Do some XML cleaning.
    # If exceptions, return an empty string ""
    #
    def _get_xml_source( self, xmlpath ):
        try:
            usock = open( xmlpath, 'r' )
            # read source
            xmlSource = usock.read()
            # close socket
            usock.close()
            ok = True
        except:
            ok = False

        if ( ok ):
            # Wintermute: this does not make sense... so we replace &amp; with &, then do the opposite,
            # and save the same file again! When this file is called in constructor xmlpath = BASE_CURRENT_SOURCE_PATH!!!
            # clean, save and return the xml string
            xmlSource = xmlSource.replace("&amp;", "&")
            xmlSource = xmlSource.replace("&", "&amp;")
            f = open(BASE_CURRENT_SOURCE_PATH, 'w')
            f.write(xmlSource)
            f.close()
            
            return xmlSource.replace("\n","").replace("\r","")
        else:
            return ""

    def _save_launchers (self):
        self._print_log('Saving launchers.xml file') 
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        
        if ( self.settings[ "auto_backup" ] ):
            # Delete oldest backup file
            fileData = {}
            dirList=os.listdir(DEFAULT_BACKUP_PATH)
            for fname in dirList:
                fileData[fname] = os.stat(os.path.join( DEFAULT_BACKUP_PATH,fname)).st_mtime
            sortedFiles = sorted(fileData.items(), key=itemgetter(1))
            delete = len(sortedFiles) - self.settings[ "nb_backup_files" ] + 1
            for x in range(0, delete):
                os.remove(os.path.join( DEFAULT_BACKUP_PATH,sortedFiles[x][0]))
            # Make a backup of current launchers.xml file
            if ( os.path.isfile(BASE_CURRENT_SOURCE_PATH)):
                try:
                    now = datetime.datetime.now()
                    timestamp = str(now.year)+str(now.month).rjust(2,'0')+str(now.day).rjust(2,'0')+"-"+str(now.hour).rjust(2,'0')+str(now.minute).rjust(2,'0')+str(now.second).rjust(2,'0')+"-"+str(now.microsecond)+"-"
                    BACKUP_CURRENT_SOURCE_PATH = os.path.join( DEFAULT_BACKUP_PATH , timestamp+"launchers.xml" )
                    shutil.copy2(BASE_CURRENT_SOURCE_PATH, BACKUP_CURRENT_SOURCE_PATH)
                except OSError:
                    xbmc_notify(__language__( 30000 )+" - "+__language__( 30612 ), __language__( 30600 ),3000)
        
        try:
            xml_content =  "<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\"?>\n"
            xml_content += "<advanced_launcher version=\"1.0\">\n\t<categories>\n"

            # Create Categories XML list
            for categoryIndex in sorted(self.categories, key= lambda x : self.categories[x]["name"]):
                category = self.categories[categoryIndex]
                xml_content += "\t\t<category>\n\t\t\t<id>"+categoryIndex+"</id>\n\t\t\t<name>"+category["name"]+"</name>\n\t\t\t<thumb>"+category["thumb"]+"</thumb>\n\t\t\t<fanart>"+category["fanart"]+"</fanart>\n\t\t\t<genre>"+category["genre"]+"</genre>\n\t\t\t<description>"+category["plot"]+"</description>\n\t\t\t<finished>"+category["finished"]+"</finished>\n\t\t</category>\n"
            xml_content += "\t</categories>\n\t<launchers>\n"
            
            # Create Launchers XML list
            for launcherIndex in sorted(self.launchers, key= lambda x : self.launchers[x]["name"]):
                launcher = self.launchers[launcherIndex]
                xml_content += "\t\t<launcher>\n\t\t\t<id>"+launcherIndex+"</id>\n\t\t\t<name>"+launcher["name"]+"</name>\n\t\t\t<category>"+launcher["category"]+"</category>\n\t\t\t<application>"+launcher["application"]+"</application>\n\t\t\t<args>"+launcher["args"]+"</args>\n\t\t\t<rompath>"+launcher["rompath"]+"</rompath>\n\t\t\t<thumbpath>"+launcher["thumbpath"]+"</thumbpath>\n\t\t\t<fanartpath>"+launcher["fanartpath"]+"</fanartpath>\n\t\t\t<trailerpath>"+launcher["trailerpath"]+"</trailerpath>\n\t\t\t<custompath>"+launcher["custompath"]+"</custompath>\n\t\t\t<romext>"+launcher["romext"]+"</romext>\n\t\t\t<platform>"+launcher["gamesys"]+"</platform>\n\t\t\t<thumb>"+launcher["thumb"]+"</thumb>\n\t\t\t<fanart>"+launcher["fanart"]+"</fanart>\n\t\t\t<genre>"+launcher["genre"]+"</genre>\n\t\t\t<release>"+launcher["release"]+"</release>\n\t\t\t<publisher>"+launcher["studio"]+"</publisher>\n\t\t\t<launcherplot>"+launcher["plot"]+"</launcherplot>\n\t\t\t<finished>"+launcher["finished"]+"</finished>\n\t\t\t<minimize>"+launcher["minimize"]+"</minimize>\n\t\t\t<lnk>"+launcher["lnk"]+"</lnk>\n\t\t\t<roms>\n"
                # Create Items XML list
                for romIndex in sorted(launcher["roms"], key= lambda x : launcher["roms"][x]["name"]):
                    romdata = launcher["roms"][romIndex]
                    xml_content += "\t\t\t\t<rom>\n\t\t\t\t\t<id>"+romIndex+"</id>\n\t\t\t\t\t<name>"+romdata["name"]+"</name>\n\t\t\t\t\t<filename>"+romdata["filename"]+"</filename>\n\t\t\t\t\t<thumb>"+romdata["thumb"]+"</thumb>\n\t\t\t\t\t<fanart>"+romdata["fanart"]+"</fanart>\n\t\t\t\t\t<trailer>"+romdata["trailer"]+"</trailer>\n\t\t\t\t\t<custom>"+romdata["custom"]+"</custom>\n\t\t\t\t\t<genre>"+romdata["genre"]+"</genre>\n\t\t\t\t\t<release>"+romdata["release"]+"</release>\n\t\t\t\t\t<publisher>"+romdata["studio"]+"</publisher>\n\t\t\t\t\t<gameplot>"+romdata["plot"]+"</gameplot>\n\t\t\t\t\t<finished>"+romdata["finished"]+"</finished>\n\t\t\t\t\t<altapp>"+romdata["altapp"]+"</altapp>\n\t\t\t\t\t<altarg>"+romdata["altarg"]+"</altarg>\n\t\t\t\t</rom>\n"
                xml_content += "\t\t\t</roms>\n\t\t</launcher>\n"
            xml_content += "\t</launchers>\n</advanced_launcher>"

            # Save launchers.tmp file
            usock = open( TEMP_CURRENT_SOURCE_PATH, 'w' )
            usock.write(xml_content)
            usock.close()
            try:
                shutil.copy2(TEMP_CURRENT_SOURCE_PATH, BASE_CURRENT_SOURCE_PATH)
            except OSError:
                xbmc_notify(__language__( 30000 )+" - "+__language__( 30612 ), __language__( 30601 ),3000)
        except OSError:
            xbmc_notify(__language__( 30000 )+" - "+__language__( 30612 ), __language__( 30602 ),3000)
        except IOError:
            xbmc_notify(__language__( 30000 )+" - "+__language__( 30612 ), __language__( 30603 ),3000)
        os.remove(TEMP_CURRENT_SOURCE_PATH)
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )

    def _append_launchers(self, xmlfile):
        destination = open(MERGED_SOURCE_PATH,'wb')
        shutil.copyfileobj(open(xmlfile,'rb'), destination)
        shutil.copyfileobj(open(BASE_CURRENT_SOURCE_PATH,'rb'), destination)
        destination.close()
        shutil.copy2(MERGED_SOURCE_PATH, BASE_CURRENT_SOURCE_PATH)
        os.remove(MERGED_SOURCE_PATH)
        xbmc.executebuiltin("Container.Refresh")

    def _load_launchers(self, xmlSource):
        self._print_log('Loading launchers.xml file')

        # clean, save and return the xml string
        xmlSource = xmlSource.replace("&amp;", "&").replace('\r','').replace('\n','').replace('\t','')
        
        
        # Get categories list from XML source -----------------------------------------------------
        xml_categories = re.findall( "<categories>(.*?)</categories>", xmlSource )
        # If categories exist ()...
        if len(xml_categories) > 0 :
            categories = re.findall( "<category>(.*?)</category>", xml_categories[0] )
            for category in categories:
                categorydata = {}
                category_index = ["id","name","thumb","fanart","genre","plot","finished"]
                values = [re.findall("<id>(.*?)</id>",category), re.findall("<name>(.*?)</name>",category), re.findall("<thumb>(.*?)</thumb>",category), re.findall("<fanart>(.*?)</fanart>",category), re.findall("<genre>(.*?)</genre>",category), re.findall("<description>(.*?)</description>",category), re.findall("<finished>(.*?)</finished>",category)]
                for index, n in enumerate(category_index):
                    try:
                        categorydata[n] = values[index][0]
                    except:
                        categorydata[n] = ""
                self.categories[categorydata["id"]] = categorydata
        # Else create the default category
        else:
            self.categories["default"] = {"id":"default", "name":"Default", "thumb":"", "fanart":"", "genre":"", "plot":"", "finished":"false"}

        # Get launchers list from XML source ------------------------------------------------------
        xml_launchers = re.findall( "<launchers>(.*?)</launchers>", xmlSource )
        # If launchers exist ()...
        if len(xml_launchers) > 0 :
            launchers = re.findall( "<launcher>(.*?)</launcher>", xml_launchers[0] )
            for launcher in launchers:
                launcherdata = {}
                launcher_index = ["id","name","category","application","args","rompath","thumbpath","fanartpath","trailerpath","custompath","romext","gamesys","thumb","fanart","genre","release","studio","plot","finished","minimize","lnk","roms"]        
                values = [re.findall("<id>(.*?)</id>",launcher), re.findall("<name>(.*?)</name>",launcher), re.findall("<category>(.*?)</category>",launcher), re.findall("<application>(.*?)</application>",launcher), re.findall("<args>(.*?)</args>",launcher), re.findall("<rompath>(.*?)</rompath>",launcher), re.findall("<thumbpath>(.*?)</thumbpath>",launcher), re.findall("<fanartpath>(.*?)</fanartpath>",launcher), re.findall("<trailerpath>(.*?)</trailerpath>",launcher), re.findall("<custompath>(.*?)</custompath>",launcher), re.findall("<romext>(.*?)</romext>",launcher), re.findall("<platform>(.*?)</platform>",launcher), re.findall("<thumb>(.*?)</thumb>",launcher), re.findall("<fanart>(.*?)</fanart>",launcher), re.findall("<genre>(.*?)</genre>",launcher), re.findall("<release>(.*?)</release>",launcher), re.findall("<publisher>(.*?)</publisher>",launcher), re.findall("<launcherplot>(.*?)</launcherplot>",launcher), re.findall("<finished>(.*?)</finished>",launcher), re.findall("<minimize>(.*?)</minimize>",launcher), re.findall("<lnk>(.*?)</lnk>",launcher), re.findall("<roms>(.*?)</roms>",launcher)]
                for index, n in enumerate(launcher_index):
                    try:
                        launcherdata[n] = values[index][0]
                    except:
                        launcherdata[n] = ""
                # Fix category to unassigned launcher
                if (launcherdata["category"] == ""):
                    launcherdata["category"] = "default"
                # Get roms list from XML source
                roms = re.findall( "<rom>(.*?)</rom>", launcherdata["roms"] )
                roms_list = {}
                # If roms exist...
                if len(roms) > 0 :
                    for rom in roms:
                        romdata = {}
                        rom_index = ["id","name","filename","thumb","fanart","trailer","custom","genre","release","studio","plot","finished","altapp","altarg"]        
                        r_values = [re.findall("<id>(.*?)</id>",rom), re.findall("<name>(.*?)</name>",rom), re.findall("<filename>(.*?)</filename>",rom), re.findall("<thumb>(.*?)</thumb>",rom), re.findall("<fanart>(.*?)</fanart>",rom), re.findall("<trailer>(.*?)</trailer>",rom), re.findall("<custom>(.*?)</custom>",rom), re.findall("<genre>(.*?)</genre>",rom), re.findall("<release>(.*?)</release>",rom), re.findall("<publisher>(.*?)</publisher>",rom), re.findall("<gameplot>(.*?)</gameplot>",rom), re.findall("<finished>(.*?)</finished>",rom), re.findall("<altapp>(.*?)</altapp>",rom), re.findall("<altarg>(.*?)</altarg>",rom)]
                        for r_index, r_n in enumerate(rom_index):
                            try:
                                romdata[r_n] = r_values[r_index][0]
                            except :
                                romdata[r_n] = ""
                        romdata["gamesys"] = launcherdata["gamesys"]
                        roms_list[romdata["id"]] = romdata
                launcherdata["roms"] = roms_list
                self.launchers[launcherdata["id"]] = launcherdata


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
                                    "Plot" : category_dic['plot'], "overlay": ICON_OVERLAY } )
        
        # --- Create context menu ---
        # To remove default entries like "Go to root", etc, see http://forum.kodi.tv/showthread.php?tid=227358
        commands = []
        categoryID = category_dic['id']
        commands.append(('Edit Category',       self._misc_url_2_RunPlugin('EDIT_CATEGORY', categoryID), ))
        commands.append(('Create New Category', self._misc_url_1_RunPlugin('ADD_CATEGORY'), ))
        commands.append(('Add New Launcher',    self._misc_url_2_RunPlugin('ADD_LAUNCHER', categoryID), ))
        commands.append(('Search',              self._misc_url_1_RunPlugin('SEARCH_COMMAND'), ))
        commands.append(('Manage sources',      self._misc_url_1_RunPlugin('FILE_MANAGER_COMMAND'), ))
        listitem.addContextMenuItems(commands, replaceItems=True)

        # --- Add row ---
        # if ( finished != "true" ) or ( self.settings[ "hide_finished" ] == False) :
        url_str = self._misc_url_2('SHOW_LAUNCHERS', key)
        xbmcplugin.addDirectoryItem( handle=int( self._handle ), url=url_str, listitem=listitem, isFolder=True)

    # 
    # Former _get_categories()
    # Renders the categories (addon root window)
    #
    def _gui_render_categories( self ):
        # For every category, add it to the listbox
        # Order alphabetically by name
        for key in sorted(self.categories, key= lambda x : self.categories[x]["name"]):
            self._gui_render_category_row(self.categories[key], key)
        xbmcplugin.endOfDirectory( handle = int( self._handle ), succeeded=True, cacheToDisc=False )

    def _gui_render_launcher_row(self, launcher_dic, key):
        # --- Create listitem row ---
        commands = []
        if launcher_dic['rompath'] == '': # Executable launcher
            folder = False
            icon = "DefaultProgram.png"
        else:                             # Files launcher
            folder = True
            icon = "DefaultFolder.png"
            commands.append(('Add Items', self._misc_url_3_RunPlugin('ADD_ROMS', launcher_dic['category'], key), ))
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
        commands.append(('Edit Launcher',    self._misc_url_3_RunPlugin('EDIT_LAUNCHER', categoryID, launcherID), ))
        commands.append(('Add New Launcher', self._misc_url_2_RunPlugin('ADD_LAUNCHER', categoryID), ))
        commands.append(('Search',           self._misc_url_1_RunPlugin('SEARCH_COMMAND'), ))
        commands.append(('Manage sources',   self._misc_url_1_RunPlugin('FILE_MANAGER_COMMAND'), ))
        listitem.addContextMenuItems(commands, replaceItems=True)

        # --- Add row ---
        url_str = self._misc_url_3('SHOW_ROMS', launcher_dic['category'], key)
        xbmcplugin.addDirectoryItem(handle=int( self._handle ), url=url_str, listitem=listitem, isFolder=folder)

    #
    # Former  _get_launchers
    # Renders the launcher for a given category
    #
    def _gui_render_launchers( self, categoryID ):
        for key in sorted(self.launchers, key= lambda x : self.launchers[x]["application"]):
            self._print_log('_gui_render_launchers() Iterating {0}'.format(self.launchers[key]['name']))
            if self.launchers[key]["category"] == categoryID:
                self._print_log('_gui_render_launchers() Showing launcher {0}'.format(self.launchers[key]['name']))
                self._gui_render_launcher_row(self.launchers[key], key)
        xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=True, cacheToDisc=False )

    #
    # Former  _add_rom
    #
    def _gui_render_rom_row( self, categoryID, launcherID, romID, rom):
        # --- Create listitem row ---
        icon = "DefaultProgram.png"
        # icon = "DefaultVideo.png"
        if rom['thumb']: listitem = xbmcgui.ListItem(rom['name'], iconImage=icon, thumbnailImage=rom['thumb'])
        else:            listitem = xbmcgui.ListItem(rom['name'], iconImage=icon)

        if rom['finished'] is not True: ICON_OVERLAY = 6
        else:                           ICON_OVERLAY = 7
        listitem.setProperty("fanart_image", rom['fanart'])
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
        commands.append(('Edit ROM', self._misc_url_4_RunPlugin('EDIT_ROM', categoryID, launcherID, romID), ))
        listitem.addContextMenuItems(commands, replaceItems=True)

        # --- Add row ---
        # if finished != "true" or self.settings[ "hide_finished" ] == False:
        # URLs must be different depending on the content type. If not, lot of WARNING: CreateLoader - unsupported protocol(plugin)
        # in the log. See http://forum.kodi.tv/showthread.php?tid=187954
        if self._content_type == 'video':
            url_str = self._misc_url_4('LAUNCH_ROM', categoryID, launcherID, romID)
        else:
            url_str = self._misc_url_4('LAUNCH_ROM', categoryID, launcherID, romID)
        xbmcplugin.addDirectoryItem(handle=int(self._handle), url=url_str, listitem=listitem, isFolder=False)

    #
    # Former  _get_roms
    # Renders the roms listbox for a given launcher
    #
    def _gui_render_roms( self, categoryID, launcherID):

        #xbmcplugin.setContent(handle = self._handle, content = 'movies')

        ## Adds a sorting method for the media list.
        #if self._handle > 0:
            #xbmcplugin.addSortMethod(handle=self._handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
            #xbmcplugin.addSortMethod(handle=self._handle, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)
            #xbmcplugin.addSortMethod(handle=self._handle, sortMethod=xbmcplugin.SORT_METHOD_STUDIO)
            #xbmcplugin.addSortMethod(handle=self._handle, sortMethod=xbmcplugin.SORT_METHOD_GENRE)
            #xbmcplugin.addSortMethod(handle=self._handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)


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
            # If ROM has no fanart then use launcher fanart
            if (roms[key]["fanart"] ==""): defined_fanart = selectedLauncher["fanart"]
            else:                          defined_fanart = roms[key]["fanart"]
            self._gui_render_rom_row(categoryID, launcherID, key, roms[key])
        xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=True, cacheToDisc=False )

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
            
            # Get file name combinations.
            (root, ext)  = os.path.splitext(f_path)
            f_path_noext = root
            f_base       = os.path.basename(f_path)
            (root, ext)  = os.path.splitext(f_base)
            f_base_noext = root
            f_ext        = ext
            self._print_log('*** Processing f_path       = "{0}"'.format(f_path))
            self._print_log('               f_path_noext = "{0}"'.format(f_path_noext))
            self._print_log('               f_base       = "{0}"'.format(f_base))
            self._print_log('               f_base_noext = "{0}"'.format(f_base_noext))
            self._print_log('               f_ext        = "{0}"'.format(f_ext))
            
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
                    self._print_log(__language__( 30736 )) 
                    results = self._get_first_game(romdata["name"],gamesys)
                    selectgame = 0
                else:
                    self._print_log(__language__( 30737 )) 
                    results,display = self._get_games_list(romdata["name"])
                    if display:
                        # Display corresponding game list found
                        dialog = xbmcgui.Dialog()
                        # Game selection
                        selectgame = dialog.select(__language__( 30078 ) % ( self.settings[ "datas_scraper" ] ), display)
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
                                ret = pDialog.create(__language__( 30000 ), __language__( 30014 ) % (path))
                                pDialog.update(filesCount * 100 / len(files), 
                                            __language__( 30061 ) % (f.replace("."+f.split(".")[-1],""),
                                            self.settings[ "datas_scraper" ].encode('utf-8','ignore')))
                        cached_thumb = Thumbnails().get_cached_covers_thumb( thumb ).replace("tbn" , "jpg")
                        if ( img_url !='' ):
                            try:
                                download_img(img_url,thumb)
                                shutil.copy2( thumb.decode(get_encoding(),'ignore') , cached_thumb.decode(get_encoding(),'ignore') )
                            except socket.timeout:
                                xbmc_notify(__language__( 30000 )+" - "+__language__( 30612 ), __language__( 30604 ),3000)
                            except exceptions.IOError:
                                xbmc_notify(__language__( 30000 )+" - "+__language__( 30612 ), __language__( 30605 ),3000)
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
                                ret = pDialog.create(__language__( 30000 ), __language__( 30014 ) % (path))
                                pDialog.update(filesCount * 100 / len(files), 
                                            __language__( 30061 ) % (f.replace("."+f.split(".")[-1],""),
                                            self.settings[ "datas_scraper" ].encode('utf-8','ignore')))
                        cached_thumb = Thumbnails().get_cached_covers_thumb( fanart ).replace("tbn" , "jpg")
                        if ( img_url !='' ):
                            try:
                                download_img(img_url,fanart)
                                shutil.copy2( fanart.decode(get_encoding(),'ignore') , cached_thumb.decode(get_encoding(),'ignore') )
                            except socket.timeout:
                                xbmc_notify(__language__( 30000 )+" - "+__language__( 30612 ), __language__( 30606 ),3000)
                            except exceptions.IOError:
                                xbmc_notify(__language__( 30000 )+" - "+__language__( 30612 ), __language__( 30607 ),3000)
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

    def _command_add_new_category ( self ) :
        dialog = xbmcgui.Dialog()
        keyboard = xbmc.Keyboard("", 'New Category Name')
        keyboard.doModal()
        if not keyboard.isConfirmed():
            return False
        categoryID = misc_generate_random_SID()
        categorydata = {"id" : categoryID, "name" : keyboard.getText(), 
                        "thumb" : "", "fanart" : "", "genre" : "", "plot" : "", "finished" : False}
        self.categories[categoryID] = categorydata
        self._save_launchers()
        xbmc.executebuiltin("Container.Refresh")
        xbmc_notify('Advanced Emulator Launcher' , 'Category %s created' % categorydata["name"], 3000)

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

    def _command_show_file_manager( self ):
        xbmc.executebuiltin("ActivateWindow(filemanager)")

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
        xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=True, cacheToDisc=False )

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
    def _misc_url_4_RunPlugin(self, command, categoryID, launcherID, romID):
        return 'XBMC.RunPlugin({0}?com={1}&catID={2}&launID={3}&romID={4})'.format(self._path, command, categoryID, launcherID, romID)

    def _misc_url_3_RunPlugin(self, command, categoryID, launcherID):
        return 'XBMC.RunPlugin({0}?com={1}&catID={2}&launID={3})'.format(self._path, command, categoryID, launcherID)

    def _misc_url_2_RunPlugin(self, command, categoryID):
        return 'XBMC.RunPlugin({0}?com={1}&catID={2})'.format(self._path, command, categoryID)

    def _misc_url_1_RunPlugin(self, command):
        return 'XBMC.RunPlugin({0}?com={1})'.format(self._path, command)

    def _misc_url_4(self, command, categoryID, launcherID, romID):
        return '{0}?com={1}&catID={2}&launID={3}&romID={4}'.format(self._path, command, categoryID, launcherID, romID)

    def _misc_url_3(self, command, categoryID, launcherID):
        return '{0}?com={1}&catID={2}&launID={3}'.format(self._path, command, categoryID, launcherID)

    def _misc_url_2(self, command, categoryID):
        return '{0}?com={1}&catID={2}'.format(self._path, command, categoryID)

    def _misc_url_1(self, command):
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

#
# Displays a modal dialog with an OK button.
# Dialog can have up to 3 rows of text.
#
def gui_kodi_dialog_OK(title, row1, row2='', row3=''):
    dialog = xbmcgui.Dialog()
    ok = dialog.ok(title, row1, row2, row3)

#
# Displays a small box in the low right corner
#
def gui_kodi_notify(title, text, time=5000):
    xbmc.executebuiltin("XBMC.Notification(%s,%s,%s,%s)" % (title, text, time, ICON_IMG_FILE_PATH))

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
        xbmc_notify(__language__( 30000 )+" - "+__language__( 30612 ), __language__( 30608 ),3000)
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
