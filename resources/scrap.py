# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher scraping engine
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

# -----------------------------------------------------------------------------
# We support online an offline scrapers.
# Note that this module does not depend on Kodi stuff at all, and can be
# called externally from console Python scripts for testing of the scrapers.
# -----------------------------------------------------------------------------

# --- "GLOBALS" ---------------------------------------------------------------
DEBUG_SCRAPERS = 1

#------------------------------------------------------------------------------
# Implement scrapers using polymorphism instead of using Angelscry 
# exec('import ...') hack.
#------------------------------------------------------------------------------
# Base class for all scrapers
# A) Offline or online
# B) Metadata, Thumb, Fanart
class Scraper:
    name = ''        # Short name to refer to object in code
    fancy_name = ''  # Fancy name for GUI and logs

    # This function is called when the user wants to search a whole list of games.
    #   search_string   Online scrapers use this
    #   platform        AEL platform name. Will be translated to scraper internal name
    #   rom_base_noext  Offline scrapers and online MAME require the unmodified ROM name
    #
    # Returns:
    #   results = [game, game, ... ]
    #   game = { 'id' : str,             String that allows to calculate the game URL, 
    #                                    or the URL itself
    #            'display_name' : str,
    #             ... }
    #
    #   game dictionary may have more fields depending on the scraper (which are 
    #   not used outside that scraper)
    def get_games_search(self, search_string, rom_base_noext, platform):
        raise NotImplementedError("Subclass must implement get_games_search() abstract method")

# -----------------------------------------------------------------------------
# Metadata scrapers base class
# All scrapers (offline or online) must implement the abstract methods.
# Metadata scrapers are for ROMs and standalone launchers (games)
# Metadata for machines (consoles, computers) should be different, I guess...
class Scraper_Metadata(Scraper):
    # Offline scrapers need to know plugin installation directory.
    # For offline scrapers just pass.
    def set_plugin_inst_dir(self, plugin_dir):
        raise NotImplementedError("Subclass must implement set_plugin_inst_dir() abstract method")

    # This is called after get_games_search() to get metadata of a particular ROM.
    # game is a dictionary from the dictionary list returned by get_game_search()
    # get_game_search() is usually common code for the online scrapers.
    #
    # Mandatory fields returned:
    #   gamedata = {'title'  : '', 'genre'  : '', 'year'   : '', 
    #               'studio' : '', 'plot'   : '' }
    def get_game_metadata(self, game):
        raise NotImplementedError("Subclass must implement get_game_metadata() abstract method")

# --- Thumb scrapers ----------------------------------------------------------
# All thumb scrapers are online scrapers. If user has a local image then he
# can setup manually using other parts of the GUI.
class Scraper_Thumb(Scraper):
    # This function is called when the user wants to search a whole list of
    # thumbs. Note that gamesys is AEL official system name, and must be
    # translated to the scraper system name, which may be different.
    # Example: AEL name 'Sega MegaDrive' -> Scraper name 'Sega Genesis'
    #
    # Returns:
    #   images = [image, image, ... ]
    #   image = {'name' : str         Name of the image (e.g., 'Boxfront 1')
    #            'URL'  : str}        URL to download image
    #            'id'  : str}         
    #
    def get_game_image_list(self, game):
        raise NotImplementedError("Subclass must implement get_game_image_list() abstract method") 

# --- Fanart scrapers ----------------------------------------------------------
# All fanart scrapers are online scrapers. If user has a local image then he
# can setup manually using other parts of the GUI.
class Scraper_Fanart(Scraper):
    def get_game_image_list(self, game):
        raise NotImplementedError("Subclass must implement get_game_image_list() abstract method") 

#------------------------------------------------------------------------------
# Instantiate scraper objects
#------------------------------------------------------------------------------
from scrap_metadata import *
from scrap_thumb import *
from scrap_fanart import *

#
# This is the official list of supported scrapers. This list MUST match the
# settings configuration in settings.xml or bad things will happen.
#
scrapers_metadata = [ metadata_NULL(), metadata_Offline(), metadata_TheGamesDB(), metadata_GameFAQs() ]
scrapers_thumb    = [ thumb_NULL(), thumb_TheGamesDB(), thumb_GameFAQs() ]
scrapers_fanart   = [ fanart_NULL(), fanart_TheGamesDB(), fanart_GameFAQs() ]
