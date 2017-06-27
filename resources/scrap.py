# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher scraping engine
#

# Copyright (c) 2016-2017 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# --- Python standard library ---
from __future__ import unicode_literals

# -------------------------------------------------------------------------------------------------
# We support online an offline scrapers.
# Note that this module does not depend on Kodi stuff at all, and can be
# called externally from console Python scripts for testing of the scrapers.
# -------------------------------------------------------------------------------------------------

# --- "GLOBALS" -----------------------------------------------------------------------------------
DEBUG_SCRAPERS = 1

#--------------------------------------------------------------------------------------------------
# Base class for all scrapers
#--------------------------------------------------------------------------------------------------
class Scraper:
    # Short name to refer to object in code
    name = ''

    # This function is called when the user wants to search a whole list of games.
    #   search_string   Online scrapers use this
    #   rom_base_noext  Offline scrapers and online MAME require the unmodified ROM name
    #   platform        AEL platform name. Will be translated to scraper internal name
    #
    # Returns:
    #   results = [game, game, ... ]
    #   game = {
    #       'id' : str,             String that allows to obtain the game URL (ID number) or the URL itself.
    #       'display_name' : str,   Scraped name of the ROM/Launcher/Game.
    #       ...
    #   }
    #   game dictionary may have more fields depending on the scraper (which are not used outside that scraper)
    def get_search(self, search_string, rom_base_noext, platform):
        raise NotImplementedError('Subclass must implement get_search() abstract method')

# -------------------------------------------------------------------------------------------------
# Metadata scrapers base class
# All scrapers (offline or online) must implement the abstract methods.
# -------------------------------------------------------------------------------------------------
def new_gamedata_dic():
    gamedata = {
        'title'    : '',
        'year'     : '',
        'genre'    : '',
        'studio'   : '',
        'nplayers' : '',
        'esrb'     : '',
        'plot'     : ''
    }

    return gamedata

class Scraper_Metadata(Scraper):
    # Offline scrapers need to know plugin installation directory.
    # For offline scrapers just pass.
    def set_addon_dir(self, plugin_dir):
        raise NotImplementedError('Subclass must implement set_addon_dir() abstract method')

    # This is called after get_games_search() to get metadata of a particular ROM.
    # game is a dictionary from the dictionary list returned by get_game_search()
    # get_game_search() is usually common code for the online scrapers.
    #
    # Mandatory fields returned:
    #   gamedata dictionary created by new_gamedata_dic()
    def get_metadata(self, game):
        raise NotImplementedError('Subclass must implement get_metadata() abstract method')

# --- Asset scrapers ------------------------------------------------------------------------------
# All asset scrapers are online scrapers.
# -------------------------------------------------------------------------------------------------
class Scraper_Asset(Scraper):
    # If scraper needs additional configuration then call this function.
    def set_options(self, region, imgsize):
        raise NotImplementedError('Subclass must implement set_options() abstract method')

    # Returns True if scraper supports the asset, False otherwise.
    def supports_asset(self, asset_kind):
        raise NotImplementedError('Subclass must implement supports_asset() abstract method')
        
    # Obtain a set of images of the given kind, based on a previous search with get_search()
    #
    # Returns:
    #   images = [image_dic, image_dic, ... ]
    #   image_dic = {
    #       'name' : str,   Name of the image (e.g., 'Boxfront 1')
    #       'id'   : str,   String that allows to obtain the game URL (ID number) or the URL itself.
    #       'URL'  : str    URL of a thumb to display the image. Some websites have small size
    #                           images for preview. It could be the URL of the full size image itself.
    #       ...    : ...    Scrapers may add additional fields for image_dic dictionary if needed.
    #   }
    def get_images(self, game, asset_kind):
        raise NotImplementedError('Subclass must implement get_images() abstract method')

    # Resolves the full size image URL. id is the string returned by get_images()
    # Returns:
    #   (URL,            Full URL of the full size image.
    #    img_extension)  Extension of the image.
    def resolve_image_URL(self, image_dic):
        raise NotImplementedError('Subclass must implement resolve_image_URL() abstract method')

#--------------------------------------------------------------------------------------------------
# Instantiate scraper objects
#--------------------------------------------------------------------------------------------------
from scrap_metadata import *
from scrap_asset import *

# This is the official list of supported scrapers. This list MUST match the settings configuration 
# in settings.xml or bad things will happen.
scrapers_metadata = [
    metadata_Offline(),
    metadata_TheGamesDB(),
    metadata_GameFAQs(),
    metadata_MobyGames(),
    metadata_ArcadeDB()
]

scrapers_asset = [
    asset_TheGamesDB(),
    asset_GameFAQs(),
    asset_MobyGames(),
    asset_ArcadeDB()
]
