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
# This dictionary has the AEL "official" game system list.
# -----------------------------------------------------------------------------
# >> When possible user No-Intro DAT-o-MATIC names
# >> Fallback to Wikipedia
#
AEL_platform_list = [
    # Arcade
    'MAME',
    # Atari
    'Atari 5200',
    'Atari 7800',
    'Atari Jaguar',
    'Atari Lynx',
    'Atari ST',
    # NEC
    'NEC PC Engine/TurboGrafx 16',
    'NEC PC Super Grafx',
    # Nintendo
    'Nintendo GameBoy',
    'Nintendo GameBoy Advance',
    'Nintendo GameBoy Color',
    'Nintendo GameCube',
    'Nintendo 64',
    'Nintendo DS',
    'Nintendo NES',
    'Nintendo SNES',
    'Nintendo Wii',
    # Sega
    'Sega 32X',
    'Sega Game Gear',
    'Sega Master System/Mark III',
    'Sega MegaDrive/Genesis',
    'Sega MegaCD',
    'Sega Saturn',
    'Sega Dreamcast',
    # SONY
    'Sony PlayStation',
    'Sony PlayStation 2',
    'Sony PlayStation Portable',
    # SNK
    'SNK Neo-Geo Pocket',
    'SNK Neo-Geo Pocket Color',
    # Unknown
    'Unknown'
]

# -----------------------------------------------------------------------------
# Translation of AEL oficial gamesys (platform) name to scraper particular name
# -----------------------------------------------------------------------------
platform_AEL_to_Offline_GameDBInfo_XML = {
    'MAME'                        : 'resources/data/GameDBInfo/MAME.xml',
    'Nintendo GameBoy'            : 'resources/data/GameDBInfo/Nintendo Game Boy.xml',
    'Nintendo GameBoy Advance'    : 'resources/data/GameDBInfo/Nintendo Game Boy Advance.xml',
    'Nintendo GameBoy Color'      : 'resources/data/GameDBInfo/Nintendo Game Boy Color.xml',
    'Nintendo GameCube'           : 'resources/data/GameDBInfo/Nintendo GameCube.xml',
    'Nintendo 64'                 : 'resources/data/GameDBInfo/Nintendo 64.xml',
    'Nintendo DS'                 : '',
    'Nintendo NES'                : 'resources/data/GameDBInfo/Nintendo Entertainment System.xml',
    'Nintendo SNES'               : 'resources/data/GameDBInfo/Super Nintendo Entertainment System.xml',
    'Nintendo Wii'                : '',
    'Sega 32X'                    : 'resources/data/GameDBInfo/Sega 32x.xml',
    'Sega Game Gear'              : 'resources/data/GameDBInfo/Sega Game Gear.xml',
    'Sega Master System/Mark III' : 'resources/data/GameDBInfo/Sega Master System.xml',
    'Sega MegaDrive/Genesis'      : '',
    'Sega MegaCD'                 : 'resources/data/GameDBInfo/Sega CD.xml',
    'Sega Saturn'                 : 'resources/data/GameDBInfo/Sega Saturn.xml',
    'Sega Dreamcast'              : 'resources/data/GameDBInfo/Sega Dreamcast.xml',
    'Sony PlayStation'            : 'resources/data/GameDBInfo/Sony PlayStation.xml',
    'Sony PlayStation 2'          : 'resources/data/GameDBInfo/Sony Playstation 2.xml',
    'Sony PlayStation Portable'   : 'resources/data/GameDBInfo/Sony PSP.xml',
    'Unknown'                     : ''
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
