# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.


"""
    Plugin for Launching an applications
"""

# -*- coding: UTF-8 -*
import sys, os, fnmatch, time, datetime, math, random, shutil
import re, urllib, urllib2, subprocess_hack, socket, exceptions
from traceback import print_exc
from operator import itemgetter

import xbmc, xbmcgui, xbmcplugin
from xbmcaddon import Addon

import subprocess_hack
from user_agent import getUserAgent
from file_item import Thumbnails
from xml.dom.minidom import parse

# Dharma compatibility (import md5)
try:
    import hashlib
except:
    import md5

# Addon paths definition
PLUGIN_DATA_PATH = xbmc.translatePath(os.path.join("special://profile/addon_data","plugin.program.advanced.launcher"))
BASE_PATH = xbmc.translatePath(os.path.join("special://","profile"))
HOME_PATH = xbmc.translatePath(os.path.join("special://","home"))
FAVOURITES_PATH = xbmc.translatePath( 'special://profile/favourites.xml' )
ADDONS_PATH = xbmc.translatePath(os.path.join(HOME_PATH,"addons"))
CURRENT_ADDON_PATH = xbmc.translatePath(os.path.join(ADDONS_PATH,"plugin.program.advanced.launcher"))
BASE_CURRENT_SOURCE_PATH = os.path.join(PLUGIN_DATA_PATH,"launchers.xml")
TEMP_CURRENT_SOURCE_PATH = os.path.join(PLUGIN_DATA_PATH,"launchers.tmp")
MERGED_SOURCE_PATH = os.path.join(PLUGIN_DATA_PATH,"merged-launchers.xml")
DEFAULT_THUMB_PATH = os.path.join(PLUGIN_DATA_PATH,"thumbs")
DEFAULT_FANART_PATH = os.path.join(PLUGIN_DATA_PATH,"fanarts")
DEFAULT_NFO_PATH = os.path.join(PLUGIN_DATA_PATH,"nfos")
DEFAULT_BACKUP_PATH = os.path.join(PLUGIN_DATA_PATH,"backups")
SHORTCUT_FILE = os.path.join(PLUGIN_DATA_PATH,"shortcut.cut")
ICON_IMG_FILE = os.path.join(CURRENT_ADDON_PATH,"icon.png")

# Addon paths creation
if not os.path.exists(DEFAULT_THUMB_PATH): os.makedirs(DEFAULT_THUMB_PATH)
if not os.path.exists(DEFAULT_FANART_PATH): os.makedirs(DEFAULT_FANART_PATH)
if not os.path.exists(DEFAULT_NFO_PATH): os.makedirs(DEFAULT_NFO_PATH)
if not os.path.exists(DEFAULT_BACKUP_PATH): os.makedirs(DEFAULT_BACKUP_PATH)
if not os.path.isdir(PLUGIN_DATA_PATH): os.makedirs(PLUGIN_DATA_PATH)

# Addon commands
REMOVE_COMMAND = "%%REMOVE%%"
BACKUP_COMMAND = "%%BACKUP%%"
APPEND_COMMAND = "%%APPEND%%"
FILE_MANAGER_COMMAND = "%%FILEMANAGER%%"
ADD_COMMAND = "%%ADD%%"
EDIT_COMMAND = "%%EDIT%%"
COMMAND_ARGS_SEPARATOR = "^^"
GET_INFO = "%%GET_INFO%%"
GET_THUMB = "%%GET_THUMB%%"
GET_FANART = "%%GET_FANART%%"
SEARCH_COMMAND = "%%SEARCH%%"
SEARCH_ITEM_COMMAND = "%%SEARCH_ITEM%%"
SEARCH_DATE_COMMAND = "%%SEARCH_DATE%%"
SEARCH_PLATFORM_COMMAND = "%%SEARCH_PLATFORM%%"
SEARCH_STUDIO_COMMAND = "%%SEARCH_STUDIO%%"
SEARCH_GENRE_COMMAND = "%%SEARCH_GENRE%%"
SCAN_NEW_ITEM_COMMAND = "%%SCAN_NEW_ITEM%%"

# Locales parameters
__settings__ = Addon( id="plugin.program.advanced.launcher" )
__lang__ = __settings__.getLocalizedString

def __language__(string):
    return __lang__(string).encode('utf-8','ignore')

# Main code

class Main:
    launchers = {}
    categories = {}

    def __init__( self, *args, **kwargs ):
        # store an handle pointer
        self._handle = int(sys.argv[ 1 ])
        self._path = sys.argv[ 0 ]

        # get users preference
        self._get_settings()

        # Load launchers
        self._load_launchers(self.get_xml_source(BASE_CURRENT_SOURCE_PATH))

        # get users scrapers preference
        self._get_scrapers()

        # get emulators preference
        exec "import resources.lib.emulators as _emulators_data"
        self._get_program_arguments = _emulators_data._get_program_arguments
        self._get_program_extensions = _emulators_data._get_program_extensions
        self._get_mame_title = _emulators_data._get_mame_title
        self._test_bios_file = _emulators_data._test_bios_file

        self._print_log(__language__( 30700 ))

        # if a commmand is passed as parameter
        param = sys.argv[ 2 ].replace("%2f","/")

        if ( self._handle > 0 ):
            xbmcplugin.addSortMethod(handle=self._handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
            xbmcplugin.addSortMethod(handle=self._handle, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)
            xbmcplugin.addSortMethod(handle=self._handle, sortMethod=xbmcplugin.SORT_METHOD_STUDIO)
            xbmcplugin.addSortMethod(handle=self._handle, sortMethod=xbmcplugin.SORT_METHOD_GENRE)
            xbmcplugin.addSortMethod(handle=self._handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)

        # If parameters are passed...
        if param:
            param = param[1:]
            command = param.split(COMMAND_ARGS_SEPARATOR)
            command_part = command[0].split("/")

            # check the action needed
            if ( len(command_part) == 4 ):
                category = command_part[0]
                launcher = command_part[1]
                rom = command_part[2]
                action = command_part[3]

                if (action == SEARCH_COMMAND):
                    self._find_roms(False)
                if (action == REMOVE_COMMAND):
                    self._remove_rom(launcher, rom)
                elif (action == EDIT_COMMAND):
                    self._edit_rom(launcher, rom)
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
                if (rom == REMOVE_COMMAND):
                    self._remove_launcher(launcher)
                elif (rom == EDIT_COMMAND):
                    self._edit_launcher(launcher)
                elif (rom == GET_INFO):
                    self._scrap_launcher(launcher)
                elif (rom == GET_THUMB):
                    self._scrap_thumb_launcher(launcher)
                elif (rom == GET_FANART):
                    self._scrap_fanart_launcher(launcher)
                elif (category == SCAN_NEW_ITEM_COMMAND):
					self._import_roms(launcher, addRoms = False)
                elif (rom == ADD_COMMAND):
                    self._add_roms(launcher)
                else:
                    self._run_rom(launcher, rom)

            if ( len(command_part) == 2 ):
                category = command_part[0]
                launcher = command_part[1]

                if (launcher == SEARCH_COMMAND):
                    self._find_roms(False)
                elif (launcher == FILE_MANAGER_COMMAND):
                    self._file_manager()
                elif (launcher == EDIT_COMMAND):
                    self._edit_category(category)
                elif (launcher == GET_INFO):
                    self._modify_category(category)
                    xbmc.executebuiltin("Container.Refresh")
                elif (launcher == GET_THUMB):
                    self._scrap_thumb_category(category)
                elif (launcher == GET_FANART):
                    self._scrap_fanart_category(category)
                elif (launcher == ADD_COMMAND):
                    self._add_new_launcher(category)
                    
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

                else:
                    if (self.launchers[launcher]["rompath"] == ""):
                        self._run_launcher(launcher)
                    else:
                        self._get_roms(launcher)

            if ( len(command_part) == 1 ):
                category = command_part[0]
                self._print_log(__language__( 30740 ) % category)

                if (category == SCAN_NEW_ITEM_COMMAND):
					self._find_roms(False)
                if (category == SEARCH_COMMAND):
                    self._find_roms(False)
                elif (category == FILE_MANAGER_COMMAND):
                    self._file_manager()
                elif (category == ADD_COMMAND):
                    self._add_new_category()
                elif (category == BACKUP_COMMAND):
                    self._print_log(__language__( 30185 ))
                    backup_file = xbmcgui.Dialog().browse(1,__language__( 30186 ),"files",".xml", False, False, os.path.join(DEFAULT_BACKUP_PATH+"/"))
                    if (os.path.isfile(backup_file)):
                        self._load_launchers(self.get_xml_source(backup_file))
                elif (category == APPEND_COMMAND):
                    self._print_log(__language__( 30185 ))
                    append_file = xbmcgui.Dialog().browse(1,__language__( 30191 ),"files",".xml", False, False, os.path.join(PLUGIN_DATA_PATH+"/"))
                    if (os.path.isfile(append_file)):
                        self._append_launchers(append_file)
                elif ( self._empty_cat(category) ):
                    self._add_new_launcher(category)
                else:
                    self._get_launchers(category)

        else:
            self._print_log(__language__( 30739 ))
            if (len(self.categories) == 0):
                if (len(self.launchers) == 0):
                    self._add_new_launcher('default')
                else:
                    categorydata = {}
                    categorydata["name"] = 'Default'
                    self.categories['default'] = categorydata
                    self._save_launchers()
                    self._get_launchers('default')
            else:
                if (self.settings[ "open_default_cat" ] ):
                    self._get_launchers('default')
                else:
                    self._get_categories()

    def _empty_cat(self, categoryID):
        empty_category = True
        for cat in self.launchers.iterkeys():
            if ( self.launchers[cat]['category'] == categoryID ):
                empty_category = False
        return empty_category

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

    def _edit_rom(self, launcher, rom):
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

    def _add_roms(self, launcher):
        dialog = xbmcgui.Dialog()
        type = dialog.select(__language__( 30106 ), [__language__( 30105 ),__language__( 30320 )])
        if (type == 0 ):
            self._import_roms(launcher)
        if (type == 1 ):
            self._add_new_rom(launcher)
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

    def _edit_category(self, categoryID):
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

    def _edit_launcher(self, launcherID):
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

    def _run_launcher(self, launcherID):
        if (self.launchers.has_key(launcherID)):
            launcher = self.launchers[launcherID]
            apppath = os.path.dirname(launcher["application"])
            if ( os.path.basename(launcher["application"]).lower().replace(".exe" , "") == "xbmc" ) or ("xbmc-fav-" in launcher["application"]) or ("xbmc-sea-" in launcher["application"]):
                xbmc.executebuiltin('XBMC.%s' % launcher["args"])
            else:
                if ( os.path.exists(apppath) ) :
                    arguments = launcher["args"].replace("%apppath%" , apppath).replace("%APPPATH%" , apppath)
                    if ( self.settings[ "media_state" ] != "2" ):
                        if ( xbmc.Player().isPlaying() ):
                            if ( self.settings[ "media_state" ] == "0" ):
                                xbmc.Player().stop()
                            if ( self.settings[ "media_state" ] == "1" ):
                                xbmc.Player().pause()
                            xbmc.sleep(self.settings[ "start_tempo" ]+100)
                            try:
                                xbmc.audioSuspend()
                            except:
                                pass
                    if (launcher["minimize"] == "true"):
                        _toogle_fullscreen()
                    if ( self.settings[ "launcher_notification" ] ):
                        xbmc_notify(__language__( 30000 ), __language__( 30034 ) % launcher["name"],3000)
                    try:
                        xbmc.enableNavSounds(False)                                 
                    except:
                        pass
                    xbmc.sleep(self.settings[ "start_tempo" ])
                    if (os.environ.get( "OS", "xbox" ) == "xbox"):
                        xbmc.executebuiltin('XBMC.Runxbe(' + launcher["application"] + ')')
                    else:
                        if (sys.platform == 'win32'):
                            if ( launcher["application"].split(".")[-1] == "lnk" ):
                                os.system("start \"\" \"%s\"" % (launcher["application"]))
                            else:
                                if ( launcher["application"].split(".")[-1] == "bat" ):
                                    info = subprocess_hack.STARTUPINFO()
                                    info.dwFlags = 1
                                    if ( self.settings[ "show_batch" ] ):
                                        info.wShowWindow = 5
                                    else:
                                        info.wShowWindow = 0
                                else:
                                    info = None
                                startproc = subprocess_hack.Popen(r'%s %s' % (launcher["application"], arguments), cwd=apppath, startupinfo=info)
                                startproc.wait()
                        elif (sys.platform.startswith('linux')):
                            if ( self.settings[ "lirc_state" ] ):
                                xbmc.executebuiltin('LIRC.stop')
                            os.system("\"%s\" %s " % (launcher["application"], arguments))
                            if ( self.settings[ "lirc_state" ] ):
                                xbmc.executebuiltin('LIRC.start')
                        elif (sys.platform.startswith('darwin')):
                            os.system("\"%s\" %s " % (launcher["application"], arguments))
                        else:
                            xbmc_notify(__language__( 30000 )+" - "+__language__( 30612 ), __language__( 30609 ),3000)
                    xbmc.sleep(self.settings[ "start_tempo" ])
                    if (launcher["minimize"] == "true"):
                        _toogle_fullscreen()
                    try:
                        xbmc.enableNavSounds(True)                            
                    except:
                        pass
                    if ( self.settings[ "media_state" ] != "2" ):
                        try:
                            xbmc.audioResume()
                        except:
                            pass
                        if ( self.settings[ "media_state" ] == "1" ):
                            xbmc.sleep(self.settings[ "start_tempo" ]+100)
                            xbmc.Player().play()
                else:
                    xbmc_notify(__language__( 30000 )+" - "+__language__( 30612 ), __language__( 30611 ) % os.path.basename(launcher["application"]),3000)

    def _get_settings( self ):
        # get the users preference settings
        self.settings = {}
        self.settings[ "datas_method" ] = __settings__.getSetting( "datas_method" )
        self.settings[ "thumbs_method" ] = __settings__.getSetting( "thumbs_method" )
        self.settings[ "fanarts_method" ] = __settings__.getSetting( "fanarts_method" )
        self.settings[ "scrap_info" ] = __settings__.getSetting( "scrap_info" )
        self.settings[ "scrap_thumbs" ] = __settings__.getSetting( "scrap_thumbs" )
        self.settings[ "scrap_fanarts" ] = __settings__.getSetting( "scrap_fanarts" )
        self.settings[ "select_fanarts" ] = __settings__.getSetting( "select_fanarts" )
        self.settings[ "overwrite_thumbs" ] = ( __settings__.getSetting( "overwrite_thumbs" ) == "true" )
        self.settings[ "overwrite_fanarts" ] = ( __settings__.getSetting( "overwrite_fanarts" ) == "true" )
        self.settings[ "clean_title" ] = ( __settings__.getSetting( "clean_title" ) == "true" )
        self.settings[ "ignore_bios" ] = ( __settings__.getSetting( "ignore_bios" ) == "true" )
        self.settings[ "ignore_title" ] = ( __settings__.getSetting( "ignore_title" ) == "true" )
        self.settings[ "title_formating" ] = ( __settings__.getSetting( "title_formating" ) == "true" )
        self.settings[ "datas_scraper" ] = __settings__.getSetting( "datas_scraper" )
        self.settings[ "thumbs_scraper" ] = __settings__.getSetting( "thumbs_scraper" )
        self.settings[ "fanarts_scraper" ] = __settings__.getSetting( "fanarts_scraper" )
        self.settings[ "game_region" ] = ['All','EU','JP','US'][int(__settings__.getSetting('game_region'))]
        self.settings[ "display_game_region" ] = [__language__( 30136 ),__language__( 30144 ),__language__( 30145 ),__language__( 30146 )][int(__settings__.getSetting('game_region'))]
        self.settings[ "thumb_image_size" ] = ['','icon','small','medium','large','xlarge','xxlarge','huge'][int(__settings__.getSetting('thumb_image_size'))]
        self.settings[ "thumb_image_size_display" ] = [__language__( 30136 ),__language__( 30137 ),__language__( 30138 ),__language__( 30139 ),__language__( 30140 ),__language__( 30141 ),__language__( 30142 ),__language__( 30143 )][int(__settings__.getSetting('thumb_image_size'))]
        self.settings[ "fanart_image_size" ] = ['','icon','small','medium','large','xlarge','xxlarge','huge'][int(__settings__.getSetting('fanart_image_size'))]
        self.settings[ "fanart_image_size_display" ] = [__language__( 30136 ),__language__( 30137 ),__language__( 30138 ),__language__( 30139 ),__language__( 30140 ),__language__( 30141 ),__language__( 30142 ),__language__( 30143 )][int(__settings__.getSetting('fanart_image_size'))]
        self.settings[ "launcher_thumb_path" ] = __settings__.getSetting( "launcher_thumb_path" )
        self.settings[ "launcher_fanart_path" ] = __settings__.getSetting( "launcher_fanart_path" )
        self.settings[ "launcher_nfo_path" ] = __settings__.getSetting( "launcher_nfo_path" )
        self.settings[ "media_state" ] = __settings__.getSetting( "media_state" )
        self.settings[ "show_batch" ] = ( __settings__.getSetting( "show_batch" ) == "true" )
        self.settings[ "recursive_scan" ] = ( __settings__.getSetting( "recursive_scan" ) == "true" )
        self.settings[ "launcher_notification" ] = ( __settings__.getSetting( "launcher_notification" ) == "true" )
        self.settings[ "lirc_state" ] = ( __settings__.getSetting( "lirc_state" ) == "true" )
        self.settings[ "hide_finished" ] = ( __settings__.getSetting( "hide_finished" ) == "true" )
        self.settings[ "snap_flyer" ] = __settings__.getSetting( "snap_flyer" )
        self.settings[ "start_tempo" ] = int(round(float(__settings__.getSetting( "start_tempo" ))))
        self.settings[ "auto_backup" ] = ( __settings__.getSetting( "auto_backup" ) == "true" )
        self.settings[ "nb_backup_files" ] = int(round(float(__settings__.getSetting( "nb_backup_files" ))))
        self.settings[ "show_log" ] = ( __settings__.getSetting( "show_log" ) == "true" )
        self.settings[ "hide_default_cat" ] = ( __settings__.getSetting( "hide_default_cat" ) == "true" )
        self.settings[ "open_default_cat" ] = ( __settings__.getSetting( "open_default_cat" ) == "true" )

    def _print_log(self,string):
        if (self.settings[ "show_log" ]):
            print __language__( 30744 )+": "+string

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

    def _run_rom(self, launcherID, romName):
        if (self.launchers.has_key(launcherID)):
            launcher = self.launchers[launcherID]
            if (launcher["roms"].has_key(romName)):
                rom = self.launchers[launcherID]["roms"][romName]
                romfile = os.path.basename(rom["filename"])
                if ( rom["altapp"] != "" ):
                    application = rom["altapp"]
                else:
                    application = launcher["application"]
                apppath = os.path.dirname(application)
                rompath = os.path.dirname(rom["filename"])
                romname = os.path.splitext(romfile)[0]
    
                if ( os.path.exists(apppath) ) :
                    if ( os.path.exists(rompath) ) :
                        files = []
                        filesnames = []
                        ext3s = ['.cd1', '-cd1', '_cd1', ' cd1']
                        for ext3 in ext3s:
                            cleanromname = re.sub('(\[.*?\]|\{.*?\}|\(.*?\))', '', romname)
                            if ( cleanromname.lower().find(ext3) > -1 ):
                                temprompath = os.path.dirname(rom["filename"])
                                try:
                                    filesnames = os.listdir(temprompath)
                                except:
                                    xbmc_notify(__language__( 30000 )+" - "+__language__( 30612 ), __language__( 30610 ),3000)
                                namestem = cleanromname[:-len(ext3)]

                                for filesname in filesnames:
                                    altname=re.findall('\{.*?\}',filesname)
                                    searchname = re.sub('(\[.*?\]|\{.*?\}|\(.*?\))', '', filesname)
                                    if searchname[0:len(namestem)] == namestem and searchname[len(namestem):len(namestem)+len(ext3) - 1]  == ext3[:-1]:
                                        for romext in launcher["romext"].split("|"):
                                            if searchname[-len(romext):].lower() == romext.lower() :
                                                Discnum = searchname[(len(namestem)+len(ext3)-1):searchname.rfind(".")]
                                                try:
                                                    int(Discnum)
                                                    if not altname:
                                                        files.append([Discnum, xbmc.getLocalizedString(427)+" "+Discnum, os.path.join(os.path.dirname(rom["filename"]),filesname)])
                                                    else:
                                                        files.append([Discnum, altname[0][1:-1], os.path.join(os.path.dirname(rom["filename"]),filesname)])
                                                except:
                                                    pass
                                if len(files) > 0:
                                    files.sort(key=lambda x: int(x[0]))
                                    discs = []
                                    for file in files:
                                        discs.append(file[1])
                                    dialog = xbmcgui.Dialog()
                                    type3 = dialog.select("%s:" % __language__( 30035 ), discs)
                                    if type3 > -1 :
                                        myresult = files[type3]
                                        rom["filename"] = myresult[2]
                                        romfile = os.path.basename(rom["filename"])
                                        rompath = os.path.dirname(rom["filename"])
                                        romname = os.path.splitext(romfile)[0]
                                    else:
                                        return ""

                        if ( rom["altarg"] != "" ):
                            arguments = rom["altarg"]
                        else:
                            arguments = launcher["args"]
                        arguments = arguments.replace("%rom%" , rom["filename"]).replace("%ROM%" , rom["filename"])
                        arguments = arguments.replace("%romfile%" , romfile).replace("%ROMFILE%" , romfile)
                        arguments = arguments.replace("%romname%" , romname).replace("%ROMNAME%" , romname)
                        arguments = arguments.replace("%rombasename%" , base_filename(romname)).replace("%ROMBASENAME%" , base_filename(romname))
                        arguments = arguments.replace("%apppath%" , apppath).replace("%APPPATH%" , apppath)
                        arguments = arguments.replace("%rompath%" , rompath).replace("%ROMPATH%" , rompath)
                        arguments = arguments.replace("%romtitle%" , rom["name"]).replace("%ROMTITLE%" , rom["name"])
                        arguments = arguments.replace("%romspath%" , launcher["rompath"]).replace("%ROMSPATH%" , launcher["rompath"])

                        self._print_log(__language__( 30742 ) % application) 
                        self._print_log(__language__( 30743 ) % arguments) 
                        if ( os.path.basename(application).lower().replace(".exe" , "") == "xbmc" ):
                            xbmc.executebuiltin('XBMC.' + arguments)
                        else:
                            if ( self.settings[ "media_state" ] != "2" ):
                                if ( xbmc.Player().isPlaying() ):
                                    if ( self.settings[ "media_state" ] == "0" ):
                                        xbmc.Player().stop()
                                    if ( self.settings[ "media_state" ] == "1" ):
                                        xbmc.Player().pause()
                                    xbmc.sleep(self.settings[ "start_tempo" ]+100)
                                    try:
                                        xbmc.audioSuspend()
                                    except:
                                        pass
                            if (launcher["minimize"] == "true"):
                                _toogle_fullscreen()
                            if ( self.settings[ "launcher_notification" ] ):
                                xbmc_notify(__language__( 30000 ), __language__( 30034 ) % rom["name"],3000)
                            try:
                                xbmc.enableNavSounds(False)                                 
                            except:
                                pass
                            xbmc.sleep(self.settings[ "start_tempo" ])
                            if (os.environ.get( "OS", "xbox" ) == "xbox"):
                                f=open(SHORTCUT_FILE, "wb")
                                f.write("<shortcut>\n")
                                f.write("    <path>" + application + "</path>\n")
                                f.write("    <custom>\n")
                                f.write("       <game>" + rom["filename"] + "</game>\n")
                                f.write("    </custom>\n")
                                f.write("</shortcut>\n")
                                f.close()
                                xbmc.executebuiltin('XBMC.Runxbe(' + SHORTCUT_FILE + ')')
                            else:
                                if (sys.platform == 'win32'):
                                    if ( launcher["lnk"] == "true" ) and ( launcher["romext"] == "lnk" ):
                                        os.system("start \"\" \"%s\"" % (arguments))
                                    else:
                                        if ( application.split(".")[-1] == "bat" ):
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
                                elif (sys.platform.startswith('linux')):
                                    if ( self.settings[ "lirc_state" ] ):
                                        xbmc.executebuiltin('LIRC.stop')
                                    os.system("\"%s\" %s " % (application, arguments))
                                    if ( self.settings[ "lirc_state" ] ):
                                        xbmc.executebuiltin('LIRC.start')
                                elif (sys.platform.startswith('darwin')):
                                    os.system("\"%s\" %s " % (application, arguments))
                                else:
                                    xbmc_notify(__language__( 30000 )+" - "+__language__( 30612 ), __language__( 30609 ),3000)
                            xbmc.sleep(self.settings[ "start_tempo" ])
                            try:
                                xbmc.enableNavSounds(True)                            
                            except:
                                pass
                            if (launcher["minimize"] == "true"):
                                _toogle_fullscreen()
                            if ( self.settings[ "media_state" ] != "2" ):
                                try:
                                    xbmc.audioResume()
                                except:
                                    pass
                                if ( self.settings[ "media_state" ] == "1" ):
                                    xbmc.sleep(self.settings[ "start_tempo" ]+100)
                                    xbmc.Player().play()
                    else:
                        xbmc_notify(__language__( 30000 )+" - "+__language__( 30612 ), __language__( 30611 ) % os.path.basename(rom["filename"]),3000)
                else:
                    xbmc_notify(__language__( 30000 )+" - "+__language__( 30612 ), __language__( 30611 ) % os.path.basename(launcher["application"]),3000)

    def get_xml_source( self, xmlpath ):
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
        self._print_log(__language__( 30746 )) 
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
            xml_content = "<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\"?>\n<advanced_launcher version=\"1.0\">\n\t<categories>\n"
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
        self._print_log(__language__( 30747 )) 
        # clean, save and return the xml string
        xmlSource = xmlSource.replace("&amp;", "&").replace('\r','').replace('\n','').replace('\t','')
        # Get categories list from XML source
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
        # Get launchers list from XML source
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

    def _get_categories( self ):
        for key in sorted(self.categories, key= lambda x : self.categories[x]["name"]):
            if ( not self.settings[ "hide_default_cat" ] or self.categories[key]['id'] != "default" ):
                self._add_category(self.categories[key]["name"], self.categories[key]["thumb"], self.categories[key]["fanart"], self.categories[key]["genre"], self.categories[key]["plot"], self.categories[key]["finished"], len(self.categories), key)
        xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=True, cacheToDisc=False )

    def _get_launchers( self, categoryID ):
        for key in sorted(self.launchers, key= lambda x : self.launchers[x]["application"]):
            if ( self.launchers[key]["category"] == categoryID ) :
                self._add_launcher(self.launchers[key]["name"], self.launchers[key]["category"], self.launchers[key]["application"], self.launchers[key]["rompath"], self.launchers[key]["thumbpath"], self.launchers[key]["fanartpath"], self.launchers[key]["trailerpath"], self.launchers[key]["custompath"], self.launchers[key]["romext"], self.launchers[key]["gamesys"], self.launchers[key]["thumb"], self.launchers[key]["fanart"], self.launchers[key]["genre"], self.launchers[key]["release"], self.launchers[key]["studio"], self.launchers[key]["plot"], self.launchers[key]["finished"], self.launchers[key]["lnk"], self.launchers[key]["minimize"], self.launchers[key]["roms"], len(self.launchers), key)
        xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=True, cacheToDisc=False )

    def _get_roms( self, launcherID ):
        if (self.launchers.has_key(launcherID)):
            selectedLauncher = self.launchers[launcherID]
            roms = selectedLauncher["roms"]
            if ( len(roms) != 0 ):
                for key in sorted(roms, key= lambda x : roms[x]["filename"]):
                    if (roms[key]["fanart"] ==""):
                        defined_fanart = selectedLauncher["fanart"]
                    else:
                        defined_fanart = roms[key]["fanart"]
                    self._add_rom(launcherID, roms[key]["name"], roms[key]["filename"], roms[key]["gamesys"], roms[key]["thumb"], defined_fanart, roms[key]["trailer"], roms[key]["custom"], roms[key]["genre"], roms[key]["release"], roms[key]["studio"], roms[key]["plot"], roms[key]["finished"], roms[key]["altapp"], roms[key]["altarg"], len(roms), key, False, "")
                xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=True, cacheToDisc=False )
            else:
                xbmc_notify(__language__( 30000 ), __language__( 30349 ),3000)

    def _report_hook( self, count, blocksize, totalsize ):
         percent = int( float( count * blocksize * 100) / totalsize )
         msg1 = __language__( 30033 )  % ( os.path.split( self.url )[ 1 ], )
         pDialog.update( percent, msg1 )
         if ( pDialog.iscanceled() ): raise

    def _import_roms(self, launcherID, addRoms = False):
        dialog = xbmcgui.Dialog()
        romsCount = 0
        filesCount = 0
        skipCount = 0
        selectedLauncher = self.launchers[launcherID]
        pDialog = xbmcgui.DialogProgress()
        app = selectedLauncher["application"]
        path = selectedLauncher["rompath"]
        exts = selectedLauncher["romext"]
        roms = selectedLauncher["roms"]
        self._print_log(__language__( 30701 ) % selectedLauncher["name"]) 
        self._print_log(__language__( 30105 )) 
        # Get game system, thumbnails and fanarts paths from launcher
        thumb_path = selectedLauncher["thumbpath"]
        fanart_path = selectedLauncher["fanartpath"]
        trailer_path = selectedLauncher["trailerpath"]
        custom_path = selectedLauncher["custompath"]
        gamesys = selectedLauncher["gamesys"]

        #remove dead entries
        if (len(roms) > 0):
            self._print_log(__language__( 30717 ) % len(roms))
            self._print_log(__language__( 30718 ))
            i = 0
            removedRoms = 0
            ret = pDialog.create(__language__( 30000 ), __language__( 30501 ) % (path))

            for key in sorted(roms.iterkeys()):
                self._print_log(__language__( 30719 ) % roms[key]["filename"] )
                pDialog.update(i * 100 / len(roms))
                i += 1
                if (not os.path.isfile(roms[key]["filename"])):
                    self._print_log(__language__( 30716 ))
                    self._print_log(__language__( 30720 ) % roms[key]["filename"] )
                    del roms[key]
                    removedRoms += 1
                else:
                    self._print_log(__language__( 30715 ))

            pDialog.close()
            if not (removedRoms == 0):
                self._print_log(__language__( 30502 ) % removedRoms)
                xbmc_notify(__language__( 30000 ), __language__( 30502 ) % removedRoms,3000)
            else:
                self._print_log(__language__( 30721 ))
                
        else:
            self._print_log(__language__( 30722 ))

        self._print_log(__language__( 30014 ) % path)
        ret = pDialog.create(__language__( 30000 ), __language__( 30014 ) % path)

        files = []
        if ( self.settings[ "recursive_scan" ] ):
            self._print_log(__language__( 30723 ))
            for root, dirs, filess in os.walk(path):
                for filename in fnmatch.filter(filess, '*.*'):
                    files.append(os.path.join(root, filename))
        else:
            self._print_log(__language__( 30724 ))
            filesname = os.listdir(path)
            for filename in filesname:
                files.append(os.path.join(path, filename))

        for fullname in files:
            f = os.path.basename(fullname)
            thumb = ""
            fanart = ""
            if ( self.settings[ "datas_method" ] == "0" ):
                import_text = __language__( 30062 ) % (f.replace("."+f.split(".")[-1],""))
            if ( self.settings[ "datas_method" ] == "1" ):
                import_text = __language__( 30061 ) % (f.replace("."+f.split(".")[-1],""),__language__( 30167 ))
            if ( self.settings[ "datas_method" ] == "2" ):
                import_text = __language__( 30061 ) % (f.replace("."+f.split(".")[-1],""),self.settings[ "datas_scraper" ].encode('utf-8','ignore'))
            if ( self.settings[ "datas_method" ] == "3" ):
                import_text = __language__( 30084 ) % (f.replace("."+f.split(".")[-1],""),self.settings[ "datas_scraper" ].encode('utf-8','ignore'))
            pDialog.update(filesCount * 100 / len(files), import_text)
            self._print_log(__language__( 30725 ) % fullname)
            for ext in exts.split("|"):
                romadded = False
                if f.upper().endswith("." + ext.upper()):
                    self._print_log(__language__( 30726 ) % ext.upper()) 
                    foundromfile = False
                    for g in roms:
                        if ( roms[g]["filename"] == fullname ):
                            self._print_log(__language__( 30727 )) 
                            foundromfile = True
                    ext3s = ['.cd', '-cd', '_cd', ' cd']
                    for ext3 in ext3s:
                       for nums in range(2, 9):
                           if ( f.lower().find(ext3 + str(nums)) > 0 ):
                               self._print_log(__language__( 30728 )) 
                               foundromfile = True
                    # Ignore MAME bios roms
                    romname = f[:-len(ext)-1]
                    romname = romname.replace('.',' ')
                    if ( app.lower().find('mame') > 0 ) or ( self.settings[ "thumbs_scraper" ] == 'arcadeHITS' ):
                        if ( self.settings["ignore_bios"] ):
                            if ( self._test_bios_file(romname)):
                                self._print_log(__language__( 30729 )) 
                                foundromfile = True
                    if ( foundromfile == False ):
                        self._print_log(__language__( 30730 )) 
                        # prepare rom object data
                        romdata = {}
                        results = []
                        # Romname conversion if MAME
                        if ( app.lower().find('mame') > 0 ) or ( self.settings[ "thumbs_scraper" ] == 'arcadeHITS' ):
                            romname = self._get_mame_title(romname)
                        # Clean multi-cd Title Name
                        ext3s = ['.cd1', '-cd1', '_cd1', ' cd1']
                        for ext3 in ext3s:
                            if ( romname.lower().find(ext3) > 0 ):
                               romname = romname[:-len(ext3)]
                        romdata["filename"] = fullname
                        romdata["gamesys"] = gamesys
                        romdata["trailer"] = ""
                        romdata["custom"] = custom_path
                        romdata["genre"] = ""
                        romdata["release"] = ""
                        romdata["studio"] = ""
                        romdata["plot"] = ""
                        romdata["finished"] = "false"
                        romdata["altapp"] = ""
                        romdata["altarg"] = ""

                        self._print_log(import_text) 
                        self._print_log(__language__( 30732 ) % romname) 
                        # Search game title from scrapers
                        
                        # Scrap from NFO files
                        if ( self.settings[ "datas_method" ] == "1" ) or ( self.settings[ "datas_method" ] == "3" ) :
                            nfo_file=os.path.splitext(romdata["filename"])[0]+".nfo"
                            self._print_log(__language__( 30719 ) % nfo_file) 
                            if (os.path.isfile(nfo_file)):
                                found_nfo = 1
                                self._print_log(__language__( 30715 )) 
                                self._print_log(__language__( 30733 ) % nfo_file) 
                                ff = open(nfo_file, 'r')
                                item_nfo = ff.read().replace('\r','').replace('\n','')
                                item_title = re.findall( "<title>(.*?)</title>", item_nfo )
                                item_platform = re.findall( "<platform>(.*?)</platform>", item_nfo )
                                item_year = re.findall( "<year>(.*?)</year>", item_nfo )
                                item_publisher = re.findall( "<publisher>(.*?)</publisher>", item_nfo )
                                item_genre = re.findall( "<genre>(.*?)</genre>", item_nfo )
                                item_plot = re.findall( "<plot>(.*?)</plot>", item_nfo )
                                if len(item_title) > 0 : romdata["name"] = item_title[0].rstrip()
                                romdata["gamesys"] = romdata["gamesys"]
                                if len(item_year) > 0 :  romdata["release"] = item_year[0]
                                if len(item_publisher) > 0 : romdata["studio"] = item_publisher[0]
                                if len(item_genre) > 0 : romdata["genre"] = item_genre[0]
                                if len(item_plot) > 0 : romdata["plot"] = item_plot[0].replace('&quot;','"')
                                ff.close()
                            else:
                                found_nfo = 0
                                self._print_log(__language__( 30726 )) 
                                romdata["name"] = title_format(self,romname)
                                self._print_log(__language__( 30734 ))
                                 
                        # Scrap from www database
                        if ( self.settings[ "datas_method" ] == "2" ) or ((self.settings[ "datas_method" ] == "3") and (found_nfo == 0)) :
                            romdata["name"] = clean_filename(romname)
                            if ( app.lower().find('mame') > 0 ) or ( self.settings[ "datas_scraper" ] == 'arcadeHITS' ):
                                self._print_log(__language__( 30735 )) 
                                results = self._get_first_game(f[:-len(ext)-1],gamesys)
                                selectgame = 0
                            else:
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
                                    progress_display = romname + ": " +__language__( 30503 )
                            else:
                                romdata["name"] = title_format(self,romname)
                                progress_display = romname + ": " +__language__( 30503 )

                        # No scrap
                        if ( self.settings[ "datas_method" ] == "0" ):
                            self._print_log(__language__( 30738 )) 
                            romdata["name"] = title_format(self,romname)

                        # Search if thumbnails and fanarts already exist
                        self._print_log(__language__( 30704 ) % fullname )
                        if ( thumb_path == fanart_path ):
                            self._print_log(__language__( 30705 ))
                        else:
                            self._print_log(__language__( 30706 ))
                        if ( thumb_path == path ):
                            self._print_log(__language__( 30707 ))
                        else:
                            self._print_log(__language__( 30708 ))
                        if ( fanart_path == path ):
                            self._print_log(__language__( 30709 ))
                        else:
                            self._print_log(__language__( 30710 ))
                            
                        ext2s = ['png', 'jpg', 'gif', 'jpeg', 'bmp', 'PNG', 'JPG', 'GIF', 'JPEG', 'BMP']
                        for ext2 in ext2s:
                            if ( thumb_path == fanart_path ):
                                if ( thumb_path == path ):
                                    test_thumb = fullname.replace('.'+ext, '_thumb.'+ext2)
                                else:
                                    test_thumb = os.path.join(thumb_path, f.replace('.'+ext, '_thumb.'+ext2))
                                if ( fanart_path == path ):
                                    test_fanart = fullname.replace('.'+ext, '_fanart.'+ext2)
                                else:
                                    test_fanart = os.path.join(fanart_path, f.replace('.'+ext, '_fanart.'+ext2))
                            else:
                                if ( thumb_path == path ):
                                    test_thumb = fullname.replace('.'+ext, '.'+ext2)
                                else:
                                    test_thumb = os.path.join(thumb_path, f.replace('.'+ext, '.'+ext2))
                                if ( fanart_path == path ):
                                    test_fanart = fullname.replace('.'+ext, '.'+ext2)
                                else:
                                    test_fanart = os.path.join(fanart_path, f.replace('.'+ext, '.'+ext2))
                            self._print_log(__language__( 30711 ) % test_thumb)
                            if ( os.path.isfile(test_thumb) ):
                                thumb = test_thumb
                                self._print_log(__language__( 30715 ))
                            else:
                                self._print_log(__language__( 30716 ))
                            self._print_log(__language__( 30712 ) % test_fanart)
                            if ( os.path.isfile(test_fanart) ):
                                fanart = test_fanart
                                self._print_log(__language__( 30715 ))
                            else:
                                self._print_log(__language__( 30716 ))

                        self._print_log(__language__( 30713 ) % thumb)
                        self._print_log(__language__( 30714 ) % fanart)

                        title = os.path.basename(romdata["filename"]).split(".")[0]
                        
                        if ( self.settings[ "thumbs_method" ] == "2" ):
                            # If overwrite is activated or thumb file not exist
                            if ( self.settings[ "overwrite_thumbs"] ) or ( thumb == "" ):
                                pDialog.update(filesCount * 100 / len(files), __language__( 30065 ) % (f.replace("."+f.split(".")[-1],""),self.settings[ "thumbs_scraper" ].encode('utf-8','ignore')))
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
                                if ( app.lower().find('mame') > 0 ) or ( self.settings[ "thumbs_scraper" ] == 'arcadeHITS' ):
                                    covers = self._get_thumbnails_list(romdata["gamesys"],title,self.settings[ "game_region" ],self.settings[ "thumb_image_size" ])
                                else:
                                    covers = self._get_thumbnails_list(romdata["gamesys"],romdata["name"],self.settings[ "game_region" ],self.settings[ "thumb_image_size" ])
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
                                            pDialog.update(filesCount * 100 / len(files), __language__( 30061 ) % (f.replace("."+f.split(".")[-1],""),self.settings[ "datas_scraper" ].encode('utf-8','ignore')))
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
                        else :
                            if ( self.settings[ "thumbs_method" ] == "0" ):
                                romdata["thumb"] = ""
                            else:
                                pDialog.update(filesCount * 100 / len(files), __language__( 30065 ) % (f.replace("."+f.split(".")[-1],""),__language__( 30172 )))
                                romdata["thumb"] = thumb

                        if ( self.settings[ "fanarts_method" ] == "2" ):
                            # If overwrite activated or fanart file not exist
                            if ( self.settings[ "overwrite_fanarts"] ) or ( fanart == "" ):
                                pDialog.update(filesCount * 100 / len(files), __language__( 30071 ) % (f.replace("."+f.split(".")[-1],""),self.settings[ "fanarts_scraper" ].encode('utf-8','ignore')))
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
                                            pDialog.update(filesCount * 100 / len(files), __language__( 30061 ) % (f.replace("."+f.split(".")[-1],""),self.settings[ "datas_scraper" ].encode('utf-8','ignore')))
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
                        else :
                            if ( self.settings[ "fanarts_method" ] == "0" ):
                                romdata["fanart"] = ""
                            else:
                                pDialog.update(filesCount * 100 / len(files), __language__( 30071 ) % (f.replace("."+f.split(".")[-1],""),__language__( 30172 )))
                                romdata["fanart"] = fanart

                        # add rom to the roms list (using name as index)
                        romid = _get_SID()
                        roms[romid] = romdata
                        romsCount = romsCount + 1

                        if (addRoms):
                            self._add_rom(launcherID, romdata["name"], romdata["filename"], romdata["gamesys"], romdata["thumb"], romdata["fanart"], romdata["trailer"], romdata["custom"], romdata["genre"], romdata["release"], romdata["studio"], romdata["plot"], romdata["finished"], romdata["altapp"], romdata["altarg"], len(files), key, False, "")
                            romadded = True
            if not romadded:
                self._print_log(__language__( 30731 )) 
                skipCount = skipCount + 1

            filesCount = filesCount + 1
            self._save_launchers()

        if ( self.settings[ "scrap_info" ] != "0" ):
            pDialog.close()

        if (skipCount == 0):
            xbmc_notify(__language__( 30000 ), __language__( 30015 ) % (romsCount) + " " + __language__( 30050 ),3000)
            xbmc.executebuiltin("XBMC.ReloadSkin()")
        else:
            xbmc_notify(__language__( 30000 ), __language__( 30016 ) % (romsCount, skipCount) + " " + __language__( 30050 ),3000)

    def _add_category(self, name, thumb, fanart, genre, plot, finished, total, key):
        commands = []
        commands.append((__language__( 30512 ), "XBMC.RunPlugin(%s?%s)" % (self._path, SEARCH_COMMAND) , ))
        commands.append((__language__( 30051 ), "XBMC.RunPlugin(%s?%s)" % (self._path, FILE_MANAGER_COMMAND) , ))
        commands.append((__language__( 30111 ), "XBMC.RunPlugin(%s?%s)" % (self._path, ADD_COMMAND) , ))
        if (not self.categories[key]['id'] == "default" ):
            commands.append(( __language__( 30110 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, key, EDIT_COMMAND) , ))
        folder = True
        icon = "DefaultFolder.png"
        if (thumb):
            listitem = xbmcgui.ListItem( name, iconImage=icon, thumbnailImage=thumb )
        else:
            listitem = xbmcgui.ListItem( name, iconImage=icon )
        commands.append(( __language__( 30194 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, key, ADD_COMMAND) , ))
        if ( finished != "true" ):
            ICON_OVERLAY = 6
        else:
            ICON_OVERLAY = 7
        listitem.setProperty("fanart_image", fanart)
        listitem.setInfo( "video", { "Title": name, "Genre" : genre, "Plot" : plot, "overlay": ICON_OVERLAY } )
        listitem.addContextMenuItems( commands )
        if ( finished != "true" ) or ( self.settings[ "hide_finished" ] == False) :
            xbmcplugin.addDirectoryItem( handle=int( self._handle ), url="%s?%s"  % (self._path, key), listitem=listitem, isFolder=True)

    def _add_launcher(self, name, category, cmd, path, thumbpath, fanartpath, trailerpath, custompath, ext, gamesys, thumb, fanart, genre, release, studio, plot, finished, lnk, minimize, roms, total, key) :
        if (int(xbmc.getInfoLabel("System.BuildVersion")[0:2]) < 12 ):
            # Dharma / Eden compatible
            display_date_format = "Date"
        else:
            # Frodo & + compatible
            display_date_format = "Year"
        commands = []
        commands.append((__language__( 30512 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, category, SEARCH_COMMAND) , ))
        commands.append((__language__( 30051 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, category, FILE_MANAGER_COMMAND) , ))
        commands.append((__language__( 30101 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, category, ADD_COMMAND) , ))
        commands.append(( __language__( 30109 ), "XBMC.RunPlugin(%s?%s/%s/%s)" % (self._path, category, key, EDIT_COMMAND) , ))

        if (path == ""):
            folder = False
            icon = "DefaultProgram.png"
        else:
            folder = True
            icon = "DefaultFolder.png"
            commands.append((__language__( 30106 ), "XBMC.RunPlugin(%s?%s/%s/%s)" % (self._path, category, key, ADD_COMMAND) , ))

        if (thumb):
            listitem = xbmcgui.ListItem( name, iconImage=icon, thumbnailImage=thumb )
        else:
            listitem = xbmcgui.ListItem( name, iconImage=icon )

        filename = os.path.splitext(cmd)
        if ( finished != "true" ):
            ICON_OVERLAY = 6
        else:
            ICON_OVERLAY = 7
        listitem.setProperty("fanart_image", fanart)
        listitem.setInfo( "video", { "Title": name, "Label": os.path.basename(cmd), "Plot" : plot , "Studio" : studio , "Genre" : genre , "Premiered" : release  , display_date_format : release  , "Writer" : gamesys , "Trailer" : os.path.join(trailerpath), "Director" : os.path.join(custompath), "overlay": ICON_OVERLAY } )
        listitem.addContextMenuItems( commands )
        if ( finished != "true" ) or ( self.settings[ "hide_finished" ] == False) :
            xbmcplugin.addDirectoryItem( handle=int( self._handle ), url="%s?%s/%s"  % (self._path, category, key), listitem=listitem, isFolder=folder)

    def _add_rom( self, launcherID, name, cmd , romgamesys, thumb, romfanart, romtrailer, romcustom, romgenre, romrelease, romstudio, romplot, finished, altapp, altarg, total, key, search, search_url):
        if (int(xbmc.getInfoLabel("System.BuildVersion")[0:2]) < 12 ):
            # Dharma / Eden compatible
            display_date_format = "Date"
        else:
            # Frodo & + compatible
            display_date_format = "Year"
        filename = os.path.splitext(cmd)
        icon = "DefaultProgram.png"
        if (thumb):
            listitem = xbmcgui.ListItem( name, iconImage=icon, thumbnailImage=thumb)
        else:
            listitem = xbmcgui.ListItem( name, iconImage=icon)
        if ( finished != "true" ):
            ICON_OVERLAY = 6
        else:
            ICON_OVERLAY = 7
        listitem.setProperty("fanart_image", romfanart)
        listitem.setInfo( "video", { "Title": name, "Label": os.path.basename(cmd), "Plot" : romplot, "Studio" : romstudio, "Genre" : romgenre, "Premiered" : romrelease  , display_date_format : romrelease, "Writer" : romgamesys, "Trailer" : os.path.join(romtrailer), "Director" : os.path.join(romcustom), "overlay": ICON_OVERLAY } )

        commands = []
        commands.append((__language__( 30512 ), "XBMC.RunPlugin(%s?%s/%s/%s)" % (self._path, self.launchers[launcherID]["category"], launcherID, SEARCH_COMMAND) , ))
        commands.append(( __language__( 30107 ), "XBMC.RunPlugin(%s?%s/%s/%s/%s)" % (self._path, self.launchers[launcherID]["category"], launcherID, key, EDIT_COMMAND) , ))
        if search :
            commands.append((__language__( 30513 ), "XBMC.RunPlugin(%s?%s/%s/%s)" % (self._path, self.launchers[launcherID]["category"], launcherID, SEARCH_COMMAND) , ))
        listitem.addContextMenuItems( commands )
        if ( finished != "true" ) or ( self.settings[ "hide_finished" ] == False) :
            xbmcplugin.addDirectoryItem( handle=int( self._handle ), url="%s?%s/%s/%s"  % (self._path, self.launchers[launcherID]["category"], launcherID, key), listitem=listitem, isFolder=False)

    def _add_new_rom ( self , launcherID) :
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
                romdata = {"name":romname,"filename":romfile,"gamesys":launcher["gamesys"],"thumb":romthumb,"fanart":romfanart,"custom":launcher["custompath"],"trailer":"","genre":"","release":"","studio":"","plot":"","finished":"false","altapp":"","altarg":""}
                # add rom to the roms list (using name as index)
                romid = _get_SID()
                roms[romid] = romdata
                xbmc_notify(__language__( 30000 ), __language__( 30019 ) + " " + __language__( 30050 ),3000)
        self._save_launchers()

    def _add_new_category ( self ) :
        dialog = xbmcgui.Dialog()
        keyboard = xbmc.Keyboard("", __language__( 30112 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            categorydata = {"name":keyboard.getText(),"thumb":"","fanart":"","genre":"","plot":"","finished":"false"}
            categoryid = _get_SID()
            self.categories[categoryid] = categorydata
            self._save_launchers()
            xbmc.executebuiltin("Container.Refresh")
            xbmc_notify(__language__( 30000 ), __language__( 30113 ) % categorydata["name"],3000)
            return True
        else:
            return False

    def _add_new_launcher ( self, categoryID ) :
        if ( self.categories.has_key(categoryID) ):
            dialog = xbmcgui.Dialog()
            type = dialog.select(__language__( 30101 ), [__language__( 30021 ), __language__( 30022 ), __language__( 30026 ), __language__( 30027 ),__language__( 30051 )])
            if (os.environ.get( "OS", "xbox" ) == "xbox"):
                filter = ".xbe|.cut"
            else:
                if (sys.platform == "win32"):
                    filter = ".bat|.exe|.cmd|.lnk"
                else:
                    filter = ""

            if (type == 0):
                app = xbmcgui.Dialog().browse(1,__language__( 30023 ),"files",filter)
                if (app):
                    argument = ""
                    argkeyboard = xbmc.Keyboard(argument, __language__( 30024 ))
                    argkeyboard.doModal()
                    args = argkeyboard.getText()
                    title = os.path.basename(app)
                    keyboard = xbmc.Keyboard(title.replace('.'+title.split('.')[-1],'').replace('.',' '), __language__( 30025 ))
                    keyboard.doModal()
                    title = keyboard.getText()
                    if ( title == "" ):
                        title = os.path.basename(app)
                        title = title.replace('.'+title.split('.')[-1],'').replace('.',' ')
                    # Selection of the launcher game system
                    dialog = xbmcgui.Dialog()
                    platforms = _get_game_system_list()
                    gamesystem = dialog.select(__language__( 30077 ), platforms)
                    # Selection of the thumbnails and fanarts path
                    if ( self.settings[ "launcher_thumb_path" ] == "" ):
                        thumb_path = xbmcgui.Dialog().browse(0,__language__( 30059 ),"files","", False, False)
                    else:
                        thumb_path = self.settings[ "launcher_thumb_path" ]
                    if ( self.settings[ "launcher_fanart_path" ] == "" ):
                        fanart_path = xbmcgui.Dialog().browse(0,__language__( 30060 ),"files","", False, False)
                    else:
                        fanart_path = self.settings[ "launcher_fanart_path" ]
                    # create launcher object data
                    if not (thumb_path):
                        thumb_path = ""
                    if not (fanart_path):
                        fanart_path = ""
                    if (not gamesystem == -1 ):
                        launcher_gamesys = platforms[gamesystem]
                    else:
                        launcher_gamesys = ""
                    if (sys.platform == "win32"):
                        launcher_lnk = "true"
                    else:
                        launcher_lnk = ""
                    launcherdata = {"name":title, "category":categoryID, "application":app, "args":args, "rompath":"", "thumbpath":thumb_path, "fanartpath":fanart_path, "custompath":"", "trailerpath":"", "romext":"", "gamesys":launcher_gamesys, "thumb":"", "fanart":"", "genre":"", "release":"", "studio":"", "plot":"", "finished":"false", "lnk":launcher_lnk, "minimize":"false", "roms":{}}
                    # add launcher to the launchers list (using name as index)
                    launcherid = _get_SID()
                    self.launchers[launcherid] = launcherdata
                    self._save_launchers()
                    xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self._path,categoryID))
                    return True

            if (type == 1):
                app = xbmcgui.Dialog().browse(1,__language__( 30023 ),"files",filter)
                if (app):
                    path = xbmcgui.Dialog().browse(0,__language__( 30058 ),"files", "", False, False)
                    if (path):
                        extensions = self._get_program_extensions(os.path.basename(app))
                        extkey = xbmc.Keyboard(extensions, __language__( 30028 ))
                        extkey.doModal()
                        if (extkey.isConfirmed()):
                            ext = extkey.getText()
                            argument = self._get_program_arguments(os.path.basename(app))
                            argkeyboard = xbmc.Keyboard(argument, __language__( 30024 ))
                            argkeyboard.doModal()
                            args = argkeyboard.getText()
                            title = os.path.basename(app)
                            keyboard = xbmc.Keyboard(title.replace('.'+title.split('.')[-1],'').replace('.',' '), __language__( 30025 ))
                            keyboard.doModal()
                            title = keyboard.getText()
                            if ( title == "" ):
                                title = os.path.basename(app)
                                title = title.replace('.'+title.split('.')[-1],'').replace('.',' ')
                            # Selection of the launcher game system
                            dialog = xbmcgui.Dialog()
                            platforms = _get_game_system_list()
                            gamesystem = dialog.select(__language__( 30077 ), platforms)
                            # Selection of the thumbnails and fanarts path
                            thumb_path = xbmcgui.Dialog().browse(0,__language__( 30059 ),"files","", False, False, os.path.join(path))
                            fanart_path = xbmcgui.Dialog().browse(0,__language__( 30060 ),"files","", False, False, os.path.join(path))
                            # create launcher object data
                            if not (thumb_path):
                                thumb_path = ""
                            if not (fanart_path):
                                fanart_path = ""
                            if (not gamesystem == -1 ):
                                launcher_gamesys = platforms[gamesystem]
                            else:
                                launcher_gamesys = ""
                            if (sys.platform == "win32"):
                                launcher_lnk = "true"
                            else:
                                launcher_lnk = ""
                            launcherdata = {"name":title, "category":categoryID, "application":app, "args":args, "rompath":path, "thumbpath":thumb_path, "fanartpath":fanart_path, "custompath":"", "trailerpath":"", "romext":ext, "gamesys":launcher_gamesys, "thumb":"", "fanart":"", "genre":"", "release":"", "studio":"", "plot":"", "finished":"false", "lnk":launcher_lnk, "minimize":"false", "roms":{}}
                            # add launcher to the launchers list (using name as index)
                            launcherid = _get_SID()
                            self.launchers[launcherid] = launcherdata
                            self._save_launchers()
                            xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self._path,categoryID))
                            return True
            if (type == 2):
                try:
                    launcher_query, query = self._find_roms(True)
                except:
                    return False
                if (launcher_query):
                    launcherid = _get_SID()
                    app = "xbmc-sea-%s" % launcherid
                    args = 'ActivateWindow(10001,"%s")' % launcher_query
                    title = os.path.basename(query)
                    keyboard = xbmc.Keyboard(title.replace('.'+title.split('.')[-1],'').replace('.',' '), __language__( 30025 ))
                    keyboard.doModal()
                    title = keyboard.getText()
                    if ( title == "" ):
                        title = os.path.basename(launcher_query)
                    launcherdata = {"name":title, "category":categoryID, "application":app, "args":args, "rompath":"", "thumbpath":DEFAULT_THUMB_PATH, "fanartpath":DEFAULT_FANART_PATH, "custompath":"", "trailerpath":"", "romext":"", "gamesys":"xbmc", "thumb":"", "fanart":"", "genre":"", "release":"", "studio":"", "plot":"", "finished":"false", "lnk":"", "minimize":"false", "roms":{}}
                    # add launcher to the launchers list (using name as index)
                    launcherid = _get_SID()
                    self.launchers[launcherid] = launcherdata
                    self._save_launchers()
                    xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self._path,categoryID))
                    return True

            if (type == 3):
                favourites, fav_nanes = _get_favourites_list()
                favourite_url = dialog.select(__language__( 30115 ), fav_nanes)
                if ( favourite_url != -1):
                    launcherid = _get_SID()
                    app = "xbmc-fav-%s" % launcherid
                    args = favourites[favourite_url][0]
                    title = os.path.basename(favourites[favourite_url][2])
                    keyboard = xbmc.Keyboard(title.replace('.'+title.split('.')[-1],'').replace('.',' '), __language__( 30025 ))
                    keyboard.doModal()
                    title = keyboard.getText()
                    if ( title == "" ):
                        title = os.path.basename(favourites[favourite_url][2])
                    if (favourites[favourite_url][1] != ""):
                        thumb = favourites[favourite_url][1]
                    else:
                        thumb = ""
                    launcherdata = {"name":title, "category":categoryID, "application":app, "args":args, "rompath":"", "thumbpath":DEFAULT_THUMB_PATH, "fanartpath":DEFAULT_FANART_PATH, "custompath":"", "trailerpath":"", "romext":"", "gamesys":"xbmc", "thumb":thumb, "fanart":"", "genre":"", "release":"", "studio":"", "plot":"", "finished":"false", "lnk":"", "minimize":"false", "roms":{}}
                    # add launcher to the launchers list (using name as index)
                    launcherid = _get_SID()
                    self.launchers[launcherid] = launcherdata
                    self._save_launchers()
                    xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self._path,categoryID))
                    return True

            if (type == 4):
                self._file_manager()

        else:
            xbmc_notify(__language__( 30000 )+" - "+__language__( 30612 ), __language__( 30613 ),3000)
            xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._path))
            return False
            

    def _file_manager( self ):
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

def xbmc_notify(title,text,time):
    xbmc.executebuiltin("XBMC.Notification(%s,%s,%s,%s)" % (title,text,time,ICON_IMG_FILE))
    
def get_encoding():
    try:
        return sys.getfilesystemencoding()
    except (UnicodeEncodeError, UnicodeDecodeError):
        return "utf-8"

def _update_cache(file_path):
    cached_thumb = Thumbnails().get_cached_covers_thumb( file_path ).replace("tbn" , os.path.splitext(file_path)[-1][1:4])
    try:
        shutil.copy2( file_path.decode(get_encoding(),'ignore'), cached_thumb.decode(get_encoding(),'ignore') )
    except OSError:
        xbmc_notify(__language__( 30000 )+" - "+__language__( 30612 ), __language__( 30608 ),3000)
    xbmc.executebuiltin("XBMC.ReloadSkin()")

def title_format(self,title):
    if ( self.settings[ "clean_title" ] ):
       title = re.sub('\[.*?\]', '', title)
       title = re.sub('\(.*?\)', '', title)
       title = re.sub('\{.*?\}', '', title)
    new_title = title.rstrip()
    if ( self.settings[ "title_formating" ] ):
        if (title.startswith("The ")): new_title = title.replace("The ","",1)+", The"
        if (title.startswith("A ")): new_title = title.replace("A ","",1)+", A"
        if (title.startswith("An ")): new_title = title.replace("An ","",1)+", An"
    else:
        if (title.endswith(", The")): new_title = "The "+"".join(title.rsplit(", The",1))
        if (title.endswith(", A")): new_title = "A "+"".join(title.rsplit(", A",1))
        if (title.endswith(", An")): new_title = "An "+"".join(title.rsplit(", An",1))
    return new_title

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

def _toogle_fullscreen():
    try:
        # Dharma / Eden compatible
        xbmc.executehttpapi("Action(199)")
    except:
        # Frodo & + compatible
        xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Input.ExecuteAction","params":{"action":"togglefullscreen"},"id":"1"}')

def _get_SID():
    t1 = time.time()
    t2 = t1 + random.getrandbits(32)
    try: 
        # Eden & + compatible
        base = hashlib.md5( str(t1 +t2) )
    except:
        # Dharma compatible
        base = md5.new( str(t1 +t2) )
    sid = base.hexdigest()
    return sid

def _get_game_system_list():
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

def _get_favourites_list():
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

def _search_category(self,category):
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

def _find_category_roms( self, search, category ):
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
