#
# Advanced Emulator Launcher scraping engine
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

# Load replacements for functions that depend on Kodi modules.
# This enables running this module in standard Python for testing scrapers.
try:
  import kodi
except:
  from standalone import *

# Python standard library
import xml.etree.ElementTree as ET 
import re

#
# Loads ...
#
def fs_load_GameInfo_XML(xml_file):
    __debug_xml_parser = 0
    games = {}

    # --- Parse using cElementTree ---
    log_verb('fs_load_GameInfo_XML() Loading "{0}"'.format(xml_file))
    xml_tree = ET.parse(xml_file)
    xml_root = xml_tree.getroot()
    for game_element in xml_root:
        if __debug_xml_parser: 
            log_debug('=== Root child tag "{0}" ==='.format(game_element.tag))

        if game_element.tag == 'game':
            # Default values
            game = {
                'name'    : '', 'description'  : '', 'year'   : '',
                'rating'  : '', 'manufacturer' : '', 'dev'    : '', 
                'genre'   : '', 'score'        : '', 'player' : '', 
                'story'   : '', 'enabled'      : '', 'crc'    : '', 
                'cloneof' : '' }

            # ROM name is an attribute of <game>
            game['name'] = game_element.attrib['name']
            if __debug_xml_parser: log_debug('Game name = "{0}"'.format(game['name']))

            # Parse child tags of category
            for game_child in game_element:
                # By default read strings
                xml_text = game_child.text if game_child.text is not None else ''
                xml_tag  = game_child.tag

                # Solve Unicode problems
                # See http://stackoverflow.com/questions/3224268/python-unicode-encode-error
                # See https://pythonhosted.org/kitchen/unicode-frustrations.html
                # See http://stackoverflow.com/questions/2508847/convert-or-strip-out-illegal-unicode-characters
                # print('Before type of xml_text is ' + str(type(xml_text)))
                if type(xml_text) == unicode:
                    xml_text = xml_text.encode('ascii', errors = 'replace')
                # print('After type of xml_text is ' + str(type(xml_text)))

                # Put data into memory
                if __debug_xml_parser: log_debug('Tag "{0}" --> "{1}"'.format(xml_tag, xml_text))
                game[xml_tag] = xml_text

            # Add game to games dictionary
            key = game['name']
            games[key] = game

    return games

#=#############################################################################
# Miscellaneous emulator and gamesys (platforms) supported.
#=#############################################################################
def emudata_get_program_arguments( app ):
    # Based on the app. name, retrieve the default arguments for the app.
    app = app.lower()
    applications = {
        'mame'        : '"%rom%"',
        'mednafen'    : '-fs 1 "%rom%"',
        'mupen64plus' : '--nogui --noask --noosd --fullscreen "%rom%"',
        'nestopia'    : '"%rom%"',
        'xbmc'        : 'PlayMedia(%rom%)',
        'retroarch'   : '-L /path/to/core "%rom%"',
        'yabause'     : '-a -f -i "%rom%"',
    }
    for application, arguments in applications.iteritems():
        if app.find(application) >= 0:
            return arguments

    return '"%rom%"'

def emudata_get_program_extensions( app ):
    # Based on the app. name, retrieve the recognized extension of the app.
    app = app.lower()
    applications = {
        'mame'       : 'zip|7z',
        'mednafen'   : 'zip|cue|iso',
        'mupen64plus': 'z64|zip|n64',
        'nestopia'   : 'nes|zip',
        'retroarch'  : 'zip|cue|iso',
        'yabause'    : 'cue',
    }
    for application, extensions in applications.iteritems():
        if app.find(application) >= 0:
            return extensions

    return ""

#
# This dictionary hast the game system list as key, and the JSON file with
# offline scraping information as value. File location is relative to
# this file location, CURRENT_ADDON_DIR/resources/.
#
offline_scrapers_dic = {
    "MAME"             : 'scraper_data/MAME.xml', 
    "Sega 32X"         : 'scraper_data/Sega 32x.xml',
    "Nintendo SNES"    : 'scraper_data/Super Nintendo Entertainment System.xml'
}

def emudata_game_system_list():
    game_list = []
    
    for key in sorted(offline_scrapers_dic):
        game_list.append(key)

    return game_list

#=#############################################################################
# Implement scrapers using polymorphism instead of using Angelscry 
# exec('import ...') hack.
#=#############################################################################
# --- Metadata scrapers -------------------------------------------------------
class Scraper_Metadata:
    # Offline XML data will be cached here (from disk)
    games = {}

    # Abstract method, defined by convention only
    def get_fancy_name(self):
        raise NotImplementedError("Subclass must implement get_fancy_name() abstract method")

    # Load XML information for this scraper and keep it cached.
    def initialise_scraper(self, gamesys):
        xml_file = offline_scrapers_dic[gamesys]
        self.games = fs_load_GameInfo_XML(xml_file)

    def get_metadata(self):
        raise NotImplementedError("Subclass must implement get_metadata() abstract method")

class metadata_NULL(Scraper_Metadata):
    def get_fancy_name(self):
        return 'NULL Metadata scraper'

class metadata_MAME(Scraper_Metadata):
    def get_fancy_name(self):
        return 'MAME Metadata offline scraper'

    def initialise_scraper(self):
        Scraper_Metadata.initialise_scraper(self, 'MAME')

    # In MAME machines, the rom_name is exactly the key of the dictionary.
    def get_metadata(self, rom_name):
        __debug_get_metadata = 0
        log_verb('Searching for "{0}" in game name'.format(rom_name))

        if rom_name in self.games:
            print(' name         = "{0}"'.format(self.games[rom_name]['name']))
            print(' description  = "{0}"'.format(self.games[rom_name]['description']))
            print(' year         = "{0}"'.format(self.games[rom_name]['year']))
            print(' manufacturer = "{0}"'.format(self.games[rom_name]['manufacturer']))
        else:
            log_verb('Not found')

        return None

#
# Offline scraper using XML files for ROMs in No-Intro name format.
#
class metadata_NoIntro(Scraper_Metadata):
    def get_fancy_name(self):
        return 'No-Intro Metadata offline scraper'
        
    # Search in-memory database and return metadata.  
    def get_metadata(self, rom_name):
        __debug_get_metadata = 0
        log_verb('Searching for "{0}" in game name'.format(rom_name))

        regexp = '.*{0}.*'.format(rom_name.lower())
        p = re.compile(regexp)
        log_debug('Search regexp "{0}"'.format(regexp))
        for key in self.games:
          # Make search case insensitive.
          name_str = self.games[key]['name'].lower()
          if __debug_get_metadata: log_debug('Test string "{0}"'.format(name_str))
          match = p.match(name_str)
          if match:
            print(' name        = "{0}"'.format(self.games[key]['name']))
            print(' description = "{0}"'.format(self.games[key]['description']))
            print(' year        = "{0}"'.format(self.games[key]['year']))

        return None

# --- Thumb scrapers ----------------------------------------------------------
class Scraper_Thumb:
    # Abstract method, defined by convention only
    def get_fancy_name(self):
        raise NotImplementedError("Subclass must implement get_fancy_name() abstract method")

class thumb_NULL(Scraper_Thumb):
    def get_fancy_name(self):
        return 'NULL Thumb scraper'

# --- Fanart scrapers ----------------------------------------------------------
class Scraper_Fanart:
    # Abstract method, defined by convention only
    def get_fancy_name(self):
        raise NotImplementedError("Subclass must implement get_fancy_name() abstract method")

class fanart_NULL(Scraper_Fanart):
    def get_fancy_name(self):
        return 'NULL Fanart scraper'

# --- Misc --------------------------------------------------------------------
#
# Instantiate scraper objects. This list must match the one in Kodi settings.
#
scrapers_metadata = [metadata_NULL(), metadata_MAME(), metadata_NoIntro()]
scrapers_thumb    = [thumb_NULL()]
scrapers_fanart   = [fanart_NULL()]

#
# Returns a Scraper_Metadata object based on scraper name
#
def get_scraper_metadata(scraper_name):
    scraper = scrapers_metadata[0]

    for obj in scrapers_metadata:
        if obj.name == scraper_name:
            scraper = obj
            break
    
    return scraper

def get_scraper_thumb(scraper_name):
    scraper = scrapers_thumb[0]

    for obj in scrapers_thumb:
        if obj.name == scraper_name:
            scraper = obj
            break
    
    return scraper

def get_scraper_fanart(scraper_name):
    scraper = scrapers_fanart[0]

    for obj in scrapers_fanart:
        if obj.name == scraper_name:
            scraper = obj
            break
    
    return scraper
