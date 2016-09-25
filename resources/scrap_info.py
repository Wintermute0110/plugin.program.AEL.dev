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

# --- Python standard library ---
from __future__ import unicode_literals

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
    'Atari 2600',
    'Atari 5200',
    'Atari 7800',
    'Atari Jaguar',
    'Atari Lynx',
    'Atari ST',
    # NEC
    'NEC PC Engine/TurboGrafx 16',
    'NEC PC SuperGrafx',
    'NEC PC-FX',
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
    'Atari 2600'                  : '',
    'Atari 5200'                  : '',
    'Atari 7800'                  : '',
    'Atari Jaguar'                : '',
    'Atari Lynx'                  : '',
    'Atari ST'                    : '',
    'NEC PC Engine/TurboGrafx 16' : '',
    'NEC PC SuperGrafx'           : '',
    'NEC PC-FX'                   : '',
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
    'SNK Neo-Geo Pocket'          : '',
    'SNK Neo-Geo Pocket Color'    : '',
    'Unknown'                     : ''
}

#
# Get platform strings from the links in http://thegamesdb.net/platforms/
#
platform_AEL_to_TheGamesDB_dic = {
    'MAME'                        : 'arcade',
    'Atari 2600'                  : 'atari-2600',
    'Atari 5200'                  : 'atari-5200',
    'Atari 7800'                  : 'atari-7800',
    'Atari Jaguar'                : 'atari-jaguar',
    'Atari Lynx'                  : 'atari-lynx',
    'Atari ST'                    : 'atari-st',
    'NEC PC Engine/TurboGrafx 16' : 'turbografx-16', # Also turbo-grafx-cd
    'NEC PC SuperGrafx'           : 'turbografx-16',
    'NEC PC-FX'                   : 'pcfx',
    'Nintendo GameBoy'            : 'nintendo-gameboy',
    'Nintendo GameBoy Advance'    : 'nintendo-gameboy-advance',
    'Nintendo GameBoy Color'      : 'nintendo-gameboy-color',
    'Nintendo GameCube'           : 'nintendo-gamecube',
    'Nintendo 64'                 : 'nintendo-64',
    'Nintendo DS'                 : 'nintendo-ds',
    'Nintendo NES'                : 'nintendo-entertainment-system-nes',
    'Nintendo SNES'               : 'super-nintendo-snes',
    'Nintendo Wii'                : 'nintendo-wii',
    'Sega 32X'                    : 'sega-32x',
    'Sega Game Gear'              : 'sega-game-gear',
    'Sega Master System/Mark III' : 'sega-master-system',
    'Sega MegaDrive/Genesis'      : 'sega-genesis',
    'Sega MegaCD'                 : 'sega-cd',
    'Sega Saturn'                 : 'sega-saturn',
    'Sega Dreamcast'              : 'sega-dreamcast',
    'Sony PlayStation'            : 'sony-playstation',
    'Sony PlayStation 2'          : 'sony-playstation-2',
    'Sony PlayStation Portable'   : 'sony-psp',
    'SNK Neo-Geo Pocket'          : 'neo-geo-pocket',
    'SNK Neo-Geo Pocket Color'    : 'neo-geo-pocket-color'
}

# Platform '0' means all platforms
platform_AEL_to_GameFAQs_dic = {
    'MAME'                        : '2',   # <option label="Arcade Games" value="2">Arcade Games</option>
    'Atari 2600'                  : '6',   # <option label="Atari 2600" value="6">Atari 2600</option>
    'Atari 5200'                  : '20',  # <option label="Atari 5200" value="20">Atari 5200</option>
    'Atari 7800'                  : '51',  # <option label="Atari 7800" value="51">Atari 7800</option>
    'Atari Jaguar'                : '72',  # <option label="Jaguar" value="72">Jaguar</option>
                                           # <option label="Jaguar CD" value="82">Jaguar CD</option>
    'Atari Lynx'                  : '58',  # <option label="Lynx" value="58">Lynx</option>
    'Atari ST'                    : '38',  # <option label="Atari ST" value="38">Atari ST</option>
    'NEC PC Engine/TurboGrafx 16' : '53',  # <option label="TurboGrafx-16" value="53">TurboGrafx-16</option>
                                           # <option label="Turbo CD" value="56">Turbo CD</option>
    'NEC PC SuperGrafx'           : '53',  # Didn't found SuperGrafx on GameFAQs
    'NEC PC-FX'                   : '79',  # <option label="PC-FX" value="79" selected="selected">PC-FX</option>
    'Nintendo GameBoy'            : '59',  # <option label="Game Boy" value="59">Game Boy</option>
    'Nintendo GameBoy Advance'    : '91',  # <option label="Game Boy Advance" value="91">Game Boy Advance</option>
    'Nintendo GameBoy Color'      : '57',  # <option label="Game Boy Color" value="57">Game Boy Color</option>
    'Nintendo GameCube'           : '99',  # <option label="GameCube" value="99">GameCube</option>
    'Nintendo 64'                 : '84',  # <option label="Nintendo 64" value="84">Nintendo 64</option>
    'Nintendo DS'                 : '108', # <option label="DS" value="108">DS</option>
    'Nintendo NES'                : '41',  # <option label="NES" value="41">NES</option>
    'Nintendo SNES'               : '63',  # <option label="Super Nintendo" value="63">Super Nintendo</option>
    'Nintendo Wii'                : '114', # <option label="Wii" value="114">Wii</option>
    'Sega 32X'                    : '74',  # <option label="Sega 32X" value="74">Sega 32X</option>
    'Sega Game Gear'              : '62',  # <option label="GameGear" value="62">GameGear</option>
    'Sega Master System/Mark III' : '49',  # <option label="Sega Master System" value="49">Sega Master System</option>
    'Sega MegaDrive/Genesis'      : '54',  # <option label="Genesis" value="54">Genesis</option>
    'Sega MegaCD'                 : '65',  # <option label="Sega CD" value="65">Sega CD</option>
    'Sega Saturn'                 : '76',  # <option label="Saturn" value="76">Saturn</option>
    'Sega Dreamcast'              : '67',  # <option label="Dreamcast" value="67">Dreamcast</option>
    'Sony PlayStation'            : '78',  # <option label="PlayStation" value="78">PlayStation</option>
    'Sony PlayStation 2'          : '94',  # <option label="PlayStation 2" value="94">PlayStation 2</option>
    'Sony PlayStation Portable'   : '109', # <option label="PSP" value="109">PSP</option>
    'SNK Neo-Geo Pocket'          : '0',   #  Not found in GameFAQs
    'SNK Neo-Geo Pocket Color'    : '89'   # <option label="NeoGeo Pocket Color" value="89">NeoGeo Pocket Color</option>
}

platform_AEL_to_MobyGames_dic = {
    'MAME'                        : '143', # <option value="143">Arcade</option>
    'Atari 2600'                  : '28',  # <option value="28">Atari 2600</option>
    'Atari 5200'                  : '33',  # <option value="33">Atari 5200</option>
    'Atari 7800'                  : '34',  # <option value="34">Atari 7800</option>
    'Atari Jaguar'                : '17',  # <option value="17">Jaguar</option>
    'Atari Lynx'                  : '18',  # <option value="18">Lynx</option>
    'Atari ST'                    : '24',  # <option value="24">Atari ST</option>
    'NEC PC Engine/TurboGrafx 16' : '40',  # <option value="40">TurboGrafx-16</option>
                                           # <option value="45">TurboGrafx CD</option>
    'NEC PC SuperGrafx'           : '127', # <option value="127">SuperGrafx</option>
    'NEC PC-FX'                   : '59',  # <option value="59">PC-FX</option>
    'Nintendo GameBoy'            : '10',  # <option value="10">Game Boy</option>
    'Nintendo GameBoy Advance'    : '12',  # <option value="12">Game Boy Advance</option>
    'Nintendo GameBoy Color'      : '11',  # <option value="11">Game Boy Color</option>
    'Nintendo GameCube'           : '14',  # <option value="14">GameCube</option>
    'Nintendo 64'                 : '9',   # <option value="9">Nintendo 64</option>
    'Nintendo DS'                 : '44',  # <option value="44">Nintendo DS</option>
    'Nintendo NES'                : '22',  # <option value="22">NES</option>
    'Nintendo SNES'               : '15',  # <option value="15">SNES</option>
    'Nintendo Wii'                : '82',  # <option value="82">Wii</option>
    'Sega 32X'                    : '21',  # <option value="21">SEGA 32X</option>
    'Sega Game Gear'              : '25',  # <option value="25">Game Gear</option>
    'Sega Master System/Mark III' : '26',  # <option value="26">SEGA Master System</option>
    'Sega MegaDrive/Genesis'      : '16',  # <option value="16">Genesis</option>
    'Sega MegaCD'                 : '20',  # <option value="20">SEGA CD</option>
    'Sega Saturn'                 : '23',  # <option value="23">SEGA Saturn</option>
    'Sega Dreamcast'              : '8',   # <option value="8">Dreamcast</option>
    'Sony PlayStation'            : '6',   # <option value="6">PlayStation</option>
    'Sony PlayStation 2'          : '7',   # <option value="7">PlayStation 2</option>
    'Sony PlayStation Portable'   : '46',  # <option value="46">PSP</option>
    'SNK Neo-Geo Pocket'          : '52',  # <option value="52">Neo Geo Pocket</option>
    'SNK Neo-Geo Pocket Color'    : '53',  # <option value="53">Neo Geo Pocket Color</option>
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

def AEL_platform_to_MobyGames(platform_AEL):
    platform_MobyGames = ''
    try:
        platform_MobyGames = platform_AEL_to_MobyGames_dic[platform_AEL]
    except:
        platform_MobyGames = ''
        
    return platform_MobyGames
