#
# Advanced Emulator Launcher scrapers
#

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

#
# We support online an offline scrapers.
#

def emudata_get_program_arguments( app ):
    # Based on the app. name, retrieve the default arguments for the app.
    app = app.lower()
    applications = {
        'bsnes': '"%rom%"',
        'chromium': '-kiosk "%rom%"',
        'dosbox': '"%rom%" -fullscreen',
        'epsxe': '-nogui -loadiso "%rom%"',
        'fbas': '-g %romname%',
        'fceux': '"%rom%"',
        'fusion': '"%rom%"',
        'gens': '--fs --quickexit "%rom%"',
        'lxdream': '-f "%rom%"',
        'mame': '"%rom%"',
        'mednafen': '-fs 1 "%rom%"',
        'mess': '-cart "%rom%" -skip_gameinfo -nowindow -nonewui',
        'mupen64plus': '--nogui --noask --noosd --fullscreen "%rom%"',
        'nestopia': '"%rom%"',
        'nullDC': '-config ImageReader:defaultImage="%rom%"',
        'osmose': '-fs "%rom%"',
        'project64': '%rom%',
        'vbam': '--opengl=MODE --fullscreen -f 15 --no-show-speed "%rom%"',
        'visualboyadvance': '"%rom%"',
        'x64': '-fullscreen -autostart "%rom%"',
        'xbmc': 'PlayMedia(%rom%)',
        'yabause': '-a -f -i "%rom%"',
        'zsnes': '-m -s -v 22 "%rom%"',
        'zsnesw': '-m -s -v 41 "%rom%"',
        'explorer.exe': '%rom%',
    }
    for application, arguments in applications.iteritems():
        if (app.find(application) >= 0):
            return arguments

    return '"%rom%"'


def emudata_get_program_extensions( app ):
    # Based on the app. name, retrieve the recognized extension of the app.
    app = app.lower()
    applications = {
        'bsnes': 'zip|smc|sfc',
        'chromium': 'swf',
        'dosbox': 'bat',
        'epsxe': 'iso|bin|cue',
        'fbas': 'zip',
        'fceux': 'nes|zip',
        'fusion': 'zip|bin|sms|gg',
        'gens': 'zip|bin',
        'lxdream': 'cdi|iso|bin',
        'mame': 'zip',
        'mednafen': 'zip|pce|gba|gb|gbc|lnx|ngc|ngp|wsc|ws',
        'mess': 'zip|nes|sms|gg|rom|a78|a52|a26|gb|gbc|gba|int|bin|sg|pce|smc',
        'mupen64plus': 'z64|zip|n64',
        'nestopia': 'nes|zip',
        'nullDC': 'gdi|cdi',
        'osmose': 'zip|sms|gg',
        'project64': 'z64|zip|n64',
        'vbam': 'gba|gb|gbc|zip',
        'visualboyadvance': 'gba|gb|gbc|zip',
        'x64': 'zip|d64|c64',
        'yabause': 'cue',
        'zsnes': 'zip|smc|sfc',
        'explorer.exe': 'lnk',
    }
    for application, extensions in applications.iteritems():
        if (app.find(application) >= 0):
            return extensions

    return ""

#
# This dictionary hast the game system list as key, and the JSON file with
# offline scraping information as value. File location is relative to
# addon installation dir CURRENT_ADDON_DIR
#
offline_scrapers_dic = {
    "MAME"             : 'resources/scrapers/MAME.json', 
    "DOS"              : '',
    "Game Boy"         : 'resources/scrapers/MAME.json',
    "Game Boy Advance" : 'resources/scrapers/MAME.json',
    "Game Boy Color"   : 'resources/scrapers/MAME.json',
    "Nintendo 64"      : 'resources/scrapers/MAME.json',
    "Nintendo DS"      : 'resources/scrapers/MAME.json',
    "Sega CD"          : 'resources/scrapers/MAME.json',
    "Sega Game Gear"   : 'resources/scrapers/MAME.json',
    "Sega Genesis"     : 'resources/scrapers/MAME.json',
    "Sega 32X"         : 'resources/scrapers/MAME.json'
}

def emudata_game_system_list():
    game_list = []
    
    for key in sorted(offline_scrapers_dic):
        game_list.append(key)

    return game_list

###############################################################################
# Implement scrapers using polymorphism instead of using Angelscry exec('import ...') hack.
###############################################################################

# --- Metadata scrapers -------------------------------------------------------
class Scraper_Metadata:
    # Constructor of the class
    def __init__(self, name):
        self.name = name

    # Abstract method, defined by convention only
    def get_fancy_name(self):
        raise NotImplementedError("Subclass must implement get_fancy_name() abstract method")

class metadata_NULL(Scraper_Metadata):
    def get_fancy_name(self):
        return 'NULL Metadata scraper'

class metadata_MAME(Scraper_Metadata):
    def get_fancy_name(self):
        return 'MAME Metadata offline scraper'

class metadata_NoIntro(Scraper_Metadata):
    def get_fancy_name(self):
        return 'No-Intro Metadata offline scraper'

# --- Thumb scrapers ----------------------------------------------------------
class Scraper_Thumb:
    # Constructor of the class
    def __init__(self, name):
        self.name = name

    # Abstract method, defined by convention only
    def get_fancy_name(self):
        raise NotImplementedError("Subclass must implement get_fancy_name() abstract method")

class thumb_NULL(Scraper_Thumb):
    def get_fancy_name(self):
        return 'NULL Thumb scraper'

# --- Fanart scrapers ----------------------------------------------------------
class Scraper_Fanart:
    # Constructor of the class
    def __init__(self, name):
        self.name = name

    # Abstract method, defined by convention only
    def get_fancy_name(self):
        raise NotImplementedError("Subclass must implement get_fancy_name() abstract method")

class fanart_NULL(Scraper_Fanart):
    def get_fancy_name(self):
        return 'NULL Fanart scraper'

# --- Misc --------------------------------------------------------------------
#
# Instantiate scraper objects
#
scrapers_metadata = [metadata_NULL('NULL'), metadata_MAME('MAME'), metadata_NoIntro('NoIntro')]
scrapers_thumb    = [thumb_NULL('NULL')]
scrapers_fanart   = [fanart_NULL('NULL')]

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
