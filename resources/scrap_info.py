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
# Miscellaneous emulator and gamesys (platforms) supported.
# -----------------------------------------------------------------------------
def emudata_get_program_arguments( app ):
    # Based on the app. name, retrieve the default arguments for the app.
    app = app.lower()
    applications = {
        'mame'        : '"%rom%"',
        'mednafen'    : '-fs 1 "%rom%"',
        'mupen64plus' : '--nogui --noask --noosd --fullscreen "%rom%"',
        'nestopia'    : '"%rom%"',
        'xbmc'        : 'PlayMedia(%rom%)',
        'kodi'        : 'PlayMedia(%rom%)',
        'retroarch'   : '-L /path/to/core -f "%rom%"',
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

# -----------------------------------------------------------------------------
# This dictionary has the AEL "official" game system list as key, and the XML file 
# with offline scraping information as value. File location is relative to
# this file location, CURRENT_ADDON_DIR/resources/.
# -----------------------------------------------------------------------------
AEL_platform_list = [
    # Arcade
    'MAME',    
    # NEC
    'NEC PC Engine',
    # Nintendo
    'Nintendo 64',
    'Nintendo DS',
    'Nintendo GameBoy',
    'Nintendo GameBoy Advance',
    'Nintendo GameBoy Color',
    'Nintendo GameCube',
    'Nintendo NES',
    'Nintendo SNES',
    # Sega
    'Sega 32X',
    'Sega Genesis/MegaDrive',
    'Sega Master System',
    'Sega Game Gear',
    'Sega MegaCD',
    'Sega Saturn',
    'Sega Dreamcast',
    # SONY
    'Sony PlayStation',
    'Sony PlayStation 2',
    'Sony PSP',
    # SNK
    'SNK Neo-Geo',
    # Unknown
    'Unknown'
]

# -----------------------------------------------------------------------------
# Translation of AEL oficial gamesys (platform) name to scraper particular name
# -----------------------------------------------------------------------------
platform_AEL_to_Offline_GameDB = {
    'MAME'                     : 'resources/data/GameDB/MAME.xml',
    'NEC PC Engine'            : '',
    'Nintendo 64'              : 'resources/data/GameDB/Super Nintendo Entertainment System.xml',
    'Nintendo DS'              : 'resources/data/GameDB/Super Nintendo Entertainment System.xml',
    'Nintendo NES'             : 'resources/data/GameDB/Super Nintendo Entertainment System.xml',
    'Nintendo GameBoy'         : 'resources/data/GameDB/Super Nintendo Entertainment System.xml',
    'Nintendo GameBoy Advance' : 'resources/data/GameDB/Super Nintendo Entertainment System.xml',
    'Nintendo GameBoy Color'   : 'resources/data/GameDB/Super Nintendo Entertainment System.xml',
    'Nintendo GameCube'        : 'resources/data/GameDB/Super Nintendo Entertainment System.xml',
    'Nintendo SNES'            : 'resources/data/GameDB/Super Nintendo Entertainment System.xml',
    'Sega 32X'                 : 'resources/data/GameDB/Sega 32x.xml',
    'Sega Genesis'             : '',
    'Sega Master System'       : '',
    'Sega Game Gear'           : '',
    'Sega MegaCD'              : '',
    'Sega Saturn'              : '',
    'Sega Deamcast'            : '',
    'Sony PlayStation'         : '',
    'Sony PlayStation 2'       : '',
    'Sony PSP'                 : '',
    'SNK Neo-Geo'              : '',
    'Unknown'                  : ''
}

platform_AEL_to_TheGamesDB_dic = {
    'MAME'          : 'Arcade',
    'Sega Genesis'  : 'Sega Mega Drive',
    'Nintendo SNES' : 'Super Nintendo (SNES)'
}

platform_AEL_to_GameFAQs_dic = {
    'MAME'          : '2',
    'Sega Genesis'  : '54',
    'Nintendo SNES' : '63'
}

def AEL_platform_to_TheGamesDB(platform_AEL):
    platform_TheGamesDB = ''
    try:
        platform_TheGamesDB = platform_AEL_to_TheGamesDB_dic[platform_AEL]
    except:
        platform_TheGamesDB = ''
        
    return platform_TheGamesDB

def AEL_platform_to_GameFAQs(AEL_gamesys):
    platform_GameFAQs = ''
    try:
        platform_GameFAQs = platform_AEL_to_GameFAQs_dic[AEL_gamesys]
    except:
        # Platform '0' means all platforms
        platform_GameFAQs = '0'
        
    return platform_GameFAQs
