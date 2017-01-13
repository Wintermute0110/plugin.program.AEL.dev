# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher scraping engine
#

# Copyright (c) 2016-2017 Wintermute0110 <wintermute0110@gmail.com>
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
    # --- MAME/Arcade ---
    'MAME',
    # --- Atari ---
    'Atari 2600',
    'Atari 5200',
    'Atari 7800',
    'Atari Jaguar',
    'Atari Lynx',
    'Atari ST',
    # --- Coleco ---
    'Colecovision',
    # --- Commodore ---
    'Commodore 64',
    'Commodore Amiga',
    'Commodore Plus-4',
    'Commodore VIC-20',
    # --- Magnavox ---
    'Magnavox Odyssey2',
    # --- Microsoft ---
    'Microsoft MSX',
    'Microsoft MSX 2',
    'Microsoft MS-DOS',
    'Microsoft Windows',
    'Microsoft Xbox',
    'Microsoft Xbox 360',
    # --- NEC ---
    'NEC PC Engine/TurboGrafx 16',
    'NEC PC SuperGrafx',
    'NEC PC-FX',
    # --- Nintendo ---
    'Nintendo Famicom Disk System',
    'Nintendo GameBoy',
    'Nintendo GameBoy Advance',
    'Nintendo GameBoy Color',
    'Nintendo GameCube',
    'Nintendo 3DS',
    'Nintendo 64',
    'Nintendo DS',
    'Nintendo DSi',
    'Nintendo NES',
    'Nintendo SNES',
    'Nintendo Virtual Boy',
    'Nintendo Wii',
    # --- Sega ---
    'Sega 32X',
    'Sega Game Gear',
    'Sega Master System/Mark III',
    'Sega MegaCD',
    'Sega MegaDrive/Genesis',
    'Sega PICO',
    'Sega SG-1000',
    'Sega Saturn',
    'Sega Dreamcast',
    # --- Sinclair ---
    'Sinclair ZX Spectrum',
    # --- SNK ---
    'SNK Neo-Geo Pocket',
    'SNK Neo-Geo Pocket Color',
    # --- SONY ---
    'Sony PlayStation',
    'Sony PlayStation 2',
    'Sony PlayStation Portable',
    # --- Unknown ---
    'Unknown'
]

# -----------------------------------------------------------------------------
# Translation of AEL oficial gamesys (platform) name to scraper particular name
# -----------------------------------------------------------------------------
#
# GameDBInfo XML are compatible with HyperSpin Hyperlist XML files.
#
platform_AEL_to_Offline_GameDBInfo_XML = {
    'MAME'                        : 'resources/data/GameDBInfo/MAME.xml',
    'Atari 2600'                  : '',
    'Atari 5200'                  : '',
    'Atari 7800'                  : '',
    'Atari Jaguar'                : '',
    'Atari Lynx'                  : '',
    'Atari ST'                    : '',
    'Colecovision'                : '',
    'Commodore 64'                : '',
    'Commodore Amiga'             : '',
    'Commodore Plus-4'            : '',
    'Commodore VIC-20'            : '',
    'Magnavox Odyssey2'           : '',
    'Microsoft MSX'               : '',
    'Microsoft MSX 2'             : '',
    'Microsoft MS-DOS'            : '',
    'Microsoft Windows'           : '',
    'Microsoft Xbox'              : '',
    'Microsoft Xbox 360'          : '',
    'NEC PC Engine/TurboGrafx 16' : '',
    'NEC PC SuperGrafx'           : '',
    'NEC PC-FX'                   : '',    
    'Nintendo Famicom Disk System': '',
    'Nintendo GameBoy'            : 'resources/data/GameDBInfo/Nintendo Game Boy.xml',
    'Nintendo GameBoy Advance'    : 'resources/data/GameDBInfo/Nintendo Game Boy Advance.xml',
    'Nintendo GameBoy Color'      : 'resources/data/GameDBInfo/Nintendo Game Boy Color.xml',
    'Nintendo GameCube'           : 'resources/data/GameDBInfo/Nintendo GameCube.xml',
    'Nintendo 3DS'                : '',
    'Nintendo 64'                 : 'resources/data/GameDBInfo/Nintendo 64.xml',
    'Nintendo DS'                 : '',
    'Nintendo DSi'                : '',
    'Nintendo NES'                : 'resources/data/GameDBInfo/Nintendo Entertainment System.xml',
    'Nintendo SNES'               : 'resources/data/GameDBInfo/Super Nintendo Entertainment System.xml',
    'Nintendo Virtual Boy'        : '',
    'Nintendo Wii'                : '',
    'Sega 32X'                    : 'resources/data/GameDBInfo/Sega 32x.xml',
    'Sega Game Gear'              : 'resources/data/GameDBInfo/Sega Game Gear.xml',
    'Sega Master System/Mark III' : 'resources/data/GameDBInfo/Sega Master System.xml',
    'Sega MegaCD'                 : 'resources/data/GameDBInfo/Sega CD.xml',
    'Sega MegaDrive/Genesis'      : '',
    'Sega PICO'                   : '',
    'Sega SG-1000'                : '',
    'Sega Saturn'                 : 'resources/data/GameDBInfo/Sega Saturn.xml',
    'Sega Dreamcast'              : 'resources/data/GameDBInfo/Sega Dreamcast.xml',
    'Sinclair ZX Spectrum'        : '',
    'SNK Neo-Geo Pocket'          : '',
    'SNK Neo-Geo Pocket Color'    : '',
    'Sony PlayStation'            : 'resources/data/GameDBInfo/Sony PlayStation.xml',
    'Sony PlayStation 2'          : 'resources/data/GameDBInfo/Sony Playstation 2.xml',
    'Sony PlayStation Portable'   : 'resources/data/GameDBInfo/Sony PSP.xml',
    'Unknown'                     : ''
}

#
# Get platform list from http://thegamesdb.net/api/GetPlatformsList.php
# Platform name is inside <name> tag. Spaces must be converted into '+'.
#
platform_AEL_to_TheGamesDB_dic = {
    'MAME'                        : 'Arcade',
    'Atari 2600'                  : 'Atari 2600',
    'Atari 5200'                  : 'Atari 5200',
    'Atari 7800'                  : 'Atari 7800',
    'Atari Jaguar'                : 'Atari Jaguar', # Also 'Atari Jaguar CD'
    'Atari Lynx'                  : 'Atari Lynx',
    'Atari ST'                    : 'Atari ST',
    'Colecovision'                : 'Colecovision',
    'Commodore 64'                : 'Commodore 64',
    'Commodore Amiga'             : 'Amiga',
    'Commodore Plus-4'            : '', #  Not found in TheGamesDB
    'Commodore VIC-20'            : 'Commodore VIC-20',
    'Magnavox Odyssey2'           : 'Magnavox Odyssey 2',
    'Microsoft MSX'               : 'MSX',
    'Microsoft MSX 2'             : 'MSX',
    'Microsoft MS-DOS'            : 'PC',
    'Microsoft Windows'           : 'PC',
    'Microsoft Xbox'              : 'Microsoft Xbox',
    'Microsoft Xbox 360'          : 'Microsoft Xbox 360',
    'NEC PC Engine/TurboGrafx 16' : 'TurboGrafx 16', # Also TurboGrafx CD
    'NEC PC SuperGrafx'           : 'TurboGrafx 16',
    'NEC PC-FX'                   : 'PC-FX',
    'Nintendo Famicom Disk System': 'Famicom Disk System',
    'Nintendo GameBoy'            : 'Nintendo Game Boy',
    'Nintendo GameBoy Advance'    : 'Nintendo Gameboy Advance',
    'Nintendo GameBoy Color'      : 'Nintendo Gameboy Color',
    'Nintendo GameCube'           : 'Nintendo GameCube',
    'Nintendo 3DS'                : 'Nintendo 3DS',
    'Nintendo 64'                 : 'Nintendo 64',
    'Nintendo DS'                 : 'Nintendo DS',
    'Nintendo DSi'                : 'Nintendo DS', # Not found in TheGamesDB
    'Nintendo NES'                : 'Nintendo Entertainment System (NES)',
    'Nintendo SNES'               : 'Super Nintendo (SNES)',
    'Nintendo Virtual Boy'        : 'Nintendo Virtual Boy',
    'Nintendo Wii'                : 'Nintendo Wii',
    'Sega 32X'                    : 'Sega 32X',
    'Sega Game Gear'              : 'Sega Game Gear',
    'Sega Master System/Mark III' : 'Sega Master System',
    'Sega MegaCD'                 : 'Sega CD',    
    'Sega MegaDrive/Genesis'      : 'Sega Genesis',
    'Sega PICO'                   : 'Sega Pico',
    'Sega SG-1000'                : 'SEGA SG-1000',
    'Sega Saturn'                 : 'Sega Saturn',
    'Sega Dreamcast'              : 'Sega Dreamcast',
    'Sinclair ZX Spectrum'        : 'Sinclair ZX Spectrum',
    'SNK Neo-Geo Pocket'          : 'Neo Geo Pocket',
    'SNK Neo-Geo Pocket Color'    : 'Neo Geo Pocket Color',
    'Sony PlayStation'            : 'Sony Playstation',
    'Sony PlayStation 2'          : 'Sony Playstation 2',
    'Sony PlayStation Portable'   : 'Sony PSP',
}

#
# Platform '0' means all platforms
# Get platform names from https://www.gamefaqs.com/search?game=ar
#
platform_AEL_to_GameFAQs_dic = {
    'MAME'                        : '2',   # <option label="Arcade Games" value="2">Arcade Games</option>
    'Atari 2600'                  : '6',   # <option label="Atari 2600" value="6">Atari 2600</option>
    'Atari 5200'                  : '20',  # <option label="Atari 5200" value="20">Atari 5200</option>
    'Atari 7800'                  : '51',  # <option label="Atari 7800" value="51">Atari 7800</option>
    'Atari Jaguar'                : '72',  # <option label="Jaguar" value="72">Jaguar</option>
                                           # <option label="Jaguar CD" value="82">Jaguar CD</option>
    'Atari Lynx'                  : '58',  # <option label="Lynx" value="58">Lynx</option>
    'Atari ST'                    : '38',  # <option label="Atari ST" value="38">Atari ST</option>
    'Colecovision'                : '29',  # <option label="Colecovision" value="29">Colecovision</option>
    'Commodore 64'                : '24',  # <option label="Commodore 64" value="24">Commodore 64</option>
    'Commodore Amiga'             : '39',  # <option label="Amiga" value="39">Amiga</option>
    'Commodore Plus-4'            : '0',   # Not found in GameFAQs
    'Commodore VIC-20'            : '11',  # <option label="VIC-20" value="11">VIC-20</option>
    'Magnavox Odyssey2'           : '9',   # <option label="Odyssey^2" value="9">Odyssey^2</option>
    'Microsoft MSX'               : '40',  # <option label="MSX" value="40">MSX</option>
    'Microsoft MSX 2'             : '40',
    'Microsoft MS-DOS'            : '19',  # <option label="PC" value="19">PC</option>
    'Microsoft Windows'           : '19',  # <option label="PC" value="19">PC</option>
    'Microsoft Xbox'              : '98',  # <option label="Xbox" value="98">Xbox</option>
    'Microsoft Xbox 360'          : '111', # <option label="Xbox 360" value="111">Xbox 360</option>
    'NEC PC Engine/TurboGrafx 16' : '53',  # <option label="TurboGrafx-16" value="53">TurboGrafx-16</option>
                                           # <option label="Turbo CD" value="56">Turbo CD</option>
    'NEC PC SuperGrafx'           : '53',  # Didn't found SuperGrafx on GameFAQs
    'NEC PC-FX'                   : '79',  # <option label="PC-FX" value="79" selected="selected">PC-FX</option>
    'Nintendo Famicom Disk System': '47',  # <option label="Famicom Disk System" value="47">Famicom Disk System</option>
    'Nintendo GameBoy'            : '59',  # <option label="Game Boy" value="59">Game Boy</option>
    'Nintendo GameBoy Advance'    : '91',  # <option label="Game Boy Advance" value="91">Game Boy Advance</option>
    'Nintendo GameBoy Color'      : '57',  # <option label="Game Boy Color" value="57">Game Boy Color</option>
    'Nintendo GameCube'           : '99',  # <option label="GameCube" value="99">GameCube</option>
    'Nintendo 3DS'                : '116', # <option label="3DS" value="116">3DS</option>
    'Nintendo 64'                 : '84',  # <option label="Nintendo 64" value="84">Nintendo 64</option>
    'Nintendo DS'                 : '108', # <option label="DS" value="108">DS</option>
    'Nintendo DSi'                : '108', # Not found in GameFAQs
    'Nintendo NES'                : '41',  # <option label="NES" value="41">NES</option>
    'Nintendo SNES'               : '63',  # <option label="Super Nintendo" value="63">Super Nintendo</option>
    'Nintendo Virtual Boy'        : '83',  # <option label="Virtual Boy" value="83">Virtual Boy</option>
    'Nintendo Wii'                : '114', # <option label="Wii" value="114">Wii</option>
    'Sega 32X'                    : '74',  # <option label="Sega 32X" value="74">Sega 32X</option>
    'Sega Game Gear'              : '62',  # <option label="GameGear" value="62">GameGear</option>
    'Sega Master System/Mark III' : '49',  # <option label="Sega Master System" value="49">Sega Master System</option>
    'Sega MegaCD'                 : '65',  # <option label="Sega CD" value="65">Sega CD</option>
    'Sega MegaDrive/Genesis'      : '54',  # <option label="Genesis" value="54">Genesis</option>
    'Sega PICO'                   : '0',   #  Not found in GameFAQs
    'Sega SG-1000'                : '43',  # <option label="SG-1000" value="43">SG-1000</option>
    'Sega Saturn'                 : '76',  # <option label="Saturn" value="76">Saturn</option>
    'Sega Dreamcast'              : '67',  # <option label="Dreamcast" value="67">Dreamcast</option>
    'Sinclair ZX Spectrum'        : '35',  # <option label="Sinclair ZX81/Spectrum" value="35">Sinclair ZX81/Spectrum</option>
    'SNK Neo-Geo Pocket'          : '0',   # Not found in GameFAQs
    'SNK Neo-Geo Pocket Color'    : '89',  # <option label="NeoGeo Pocket Color" value="89">NeoGeo Pocket Color</option>
    'Sony PlayStation'            : '78',  # <option label="PlayStation" value="78">PlayStation</option>
    'Sony PlayStation 2'          : '94',  # <option label="PlayStation 2" value="94">PlayStation 2</option>
    'Sony PlayStation Portable'   : '109', # <option label="PSP" value="109">PSP</option>
}

#
# Get platform names from http://www.mobygames.com/search/quick?q=ar
#
platform_AEL_to_MobyGames_dic = {
    'MAME'                        : '143', # <option value="143">Arcade</option>
    'Atari 2600'                  : '28',  # <option value="28">Atari 2600</option>
    'Atari 5200'                  : '33',  # <option value="33">Atari 5200</option>
    'Atari 7800'                  : '34',  # <option value="34">Atari 7800</option>
    'Atari Jaguar'                : '17',  # <option value="17">Jaguar</option>
    'Atari Lynx'                  : '18',  # <option value="18">Lynx</option>
    'Atari ST'                    : '24',  # <option value="24">Atari ST</option>
    'Colecovision'                : '29',  # <option value="29">ColecoVision</option>
    'Commodore 64'                : '27',  # <option value="27">Commodore 64</option>
    'Commodore Amiga'             : '19',  # <option value="19">Amiga</option>
    'Commodore Plus-4'            : '115', # <option value="115">Commodore 16, Plus/4</option>
    'Commodore VIC-20'            : '43',  # <option value="43">VIC-20</option>
    'Magnavox Odyssey2'           : '78',  # <option value="78">Odyssey 2</option>
    'Microsoft MSX'               : '57',  # <option value="57">MSX</option>
    'Microsoft MSX 2'             : '57',
    'Microsoft MS-DOS'            : '2',   # <option value="2">DOS</option>
    'Microsoft Windows'           : '3',   # <option value="3">Windows</option>
                                           # <option value="5">Windows 3.x</option>
    'Microsoft Xbox'              : '13',  # <option value="13">Xbox</option>
    'Microsoft Xbox 360'          : '69',  # <option value="69">Xbox 360</option>
    'NEC PC Engine/TurboGrafx 16' : '40',  # <option value="40">TurboGrafx-16</option>
                                           # <option value="45">TurboGrafx CD</option>
    'NEC PC SuperGrafx'           : '127', # <option value="127">SuperGrafx</option>
    'NEC PC-FX'                   : '59',  # <option value="59">PC-FX</option>
    'Nintendo Famicom Disk System': '22',  # Does not exist in MobyGames
    'Nintendo GameBoy'            : '10',  # <option value="10">Game Boy</option>
    'Nintendo GameBoy Advance'    : '12',  # <option value="12">Game Boy Advance</option>
    'Nintendo GameBoy Color'      : '11',  # <option value="11">Game Boy Color</option>
    'Nintendo GameCube'           : '14',  # <option value="14">GameCube</option>
    'Nintendo 3DS'                : '101', # <option value="101">Nintendo 3DS</option>
    'Nintendo 64'                 : '9',   # <option value="9">Nintendo 64</option>
    'Nintendo DS'                 : '44',  # <option value="44">Nintendo DS</option>
    'Nintendo DSi'                : '87',  # <option value="87">Nintendo DSi</option>
    'Nintendo NES'                : '22',  # <option value="22">NES</option>
    'Nintendo SNES'               : '15',  # <option value="15">SNES</option>
    'Nintendo Virtual Boy'        : '38',  # <option value="38">Virtual Boy</option>
    'Nintendo Wii'                : '82',  # <option value="82">Wii</option>
    'Sega 32X'                    : '21',  # <option value="21">SEGA 32X</option>
    'Sega Game Gear'              : '25',  # <option value="25">Game Gear</option>
    'Sega Master System/Mark III' : '26',  # <option value="26">SEGA Master System</option>
    'Sega MegaCD'                 : '20',  # <option value="20">SEGA CD</option>
    'Sega MegaDrive/Genesis'      : '16',  # <option value="16">Genesis</option>
    'Sega PICO'                   : '103', # <option value="103">SEGA Pico</option>
    'Sega SG-1000'                : '114', # <option value="114">SG-1000</option>
    'Sega Saturn'                 : '23',  # <option value="23">SEGA Saturn</option>
    'Sega Dreamcast'              : '8',   # <option value="8">Dreamcast</option>
    'Sinclair ZX Spectrum'        : '41',  # <option value="41">ZX Spectrum</option>
    'SNK Neo-Geo Pocket'          : '52',  # <option value="52">Neo Geo Pocket</option>
    'SNK Neo-Geo Pocket Color'    : '53',  # <option value="53">Neo Geo Pocket Color</option>
    'Sony PlayStation'            : '6',   # <option value="6">PlayStation</option>
    'Sony PlayStation 2'          : '7',   # <option value="7">PlayStation 2</option>
    'Sony PlayStation Portable'   : '46',  # <option value="46">PSP</option>
}

def AEL_platform_to_TheGamesDB(platform_AEL):
    try:    platform_TheGamesDB = platform_AEL_to_TheGamesDB_dic[platform_AEL]
    except: platform_TheGamesDB = ''
        
    return platform_TheGamesDB

def AEL_platform_to_GameFAQs(AEL_gamesys):
    try:    platform_GameFAQs = platform_AEL_to_GameFAQs_dic[AEL_gamesys]
    except: platform_GameFAQs = '0' # Platform '0' means all platforms

    return platform_GameFAQs

def AEL_platform_to_MobyGames(platform_AEL):
    try:    platform_MobyGames = platform_AEL_to_MobyGames_dic[platform_AEL]
    except: platform_MobyGames = ''
        
    return platform_MobyGames
