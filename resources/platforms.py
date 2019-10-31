# -*- coding: utf-8 -*-

# Advanced Emulator Launcher platform and emulator information.

# Copyright (c) 2016-2019 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# --- Python standard library ---
from __future__ import unicode_literals

# -------------------------------------------------------------------------------------------------
# New platform engine
# -------------------------------------------------------------------------------------------------
DAT_MAME     = 'MAME'
DAT_NOINTRO  = 'No-Intro'
DAT_REDUMP   = 'Redump'
DAT_LIBRETRO = 'Libretro'
DAT_NONE     = ''
DEFAULT_PLAT_TGDB          = '0'
DEFAULT_PLAT_MOBYGAMES     = '0'
DEFAULT_PLAT_SCREENSCRAPER = '0'
DEFAULT_PLAT_GAMEFAQS      = '0'
class Platform:
    def __init__(self, name, shortname, compactname, aliasof = None, DAT = None,
        TGDB_plat = None, MG_plat = None, SS_plat = None, GF_plat = None):
        self.long_name    = name
        self.short_name   = shortname
        self.compact_name = compactname
        self.aliasof      = aliasof
        self.DAT          = DAT
        self.TGDB_plat    = TGDB_plat
        self.MG_plat      = MG_plat
        self.SS_plat      = SS_plat
        self.GF_plat      = GF_plat

# * From this list create simplified lists to access platform information.
# * Shorted alphabetically by long name. Alphabetical order is veryfied with script
#   xxxxx.py
# * To be compatible with Retroplayer and Kodi artwork database, anything that can be launched
#   by Retroarch must be a platform, including Doom, CaveStory, etc.
# * Platform is something that has ROMs to launch. Standalone cores do not need a platform,
#   they are Kodi addons with its own artwork. CHECK THIS!
# * Platform names must have filesystem-safe characters.
# * When possible user No-Intro DAT-o-MATIC names. Fallback to Wikipedia names.
# * Unsuported scraper platforms must be set to None. The conversion function will then
#   translate None to the appropiate value for the scraper.
#
# Get TGDB platform list from script scrap_TGDB_list_platforms.py.
# Get MobyGames platform list from script scrap_MobyGames_list_platforms.py.
# Get ScreenScraper platform list from script xxxx.py
# Get GameFAQs platform list from https://www.gamefaqs.com/search_advanced?game=ar
#
# Default values: Platform('', '', '', None, DAT_NONE, None, None, None, None),
#
AEL_platforms = [
    # --- 3DO Interactive Multiplayer ---
    Platform('3DO Interactive Multiplayer', 'console-3do', '3do', None, DAT_REDUMP, '25', '35', '29', '61'),

    # --- Amstrad ---
    Platform('Amstrad CPC', 'computer-cpc', 'cpc', None, DAT_NONE, '4914', '60', '65', '46'),

    # --- Atari ---
    Platform('Atari 2600', 'atari-2600', 'a2600', None, DAT_NOINTRO, '22', '28', '26', '6'),
    Platform('Atari 5200', 'atari-5200', 'a5200', None, DAT_NOINTRO, '26', '33', '40', '20'),
    Platform('Atari 7800', 'atari-7800', 'a7800', None, DAT_NOINTRO, '27', '34', '41', '51'),
    # Atari 8-bit includes: Atari 400, Atari 800, Atari 1200XL, Atari 65XE, Atari 130XE, Atari XEGS
    Platform('Atari 8-bit', 'computer-atari-8bit', 'atari-8bit', None, DAT_NONE, '30', '39', '43', None),
    Platform('Atari Jaguar', 'atari-jaguar', 'jaguar', None, DAT_NOINTRO, '28', '17', '27', '72'),
    Platform('Atari Jaguar CD', 'atari-jaguarcd', 'jaguarcd', None, DAT_REDUMP, '29', '17', '171', '82'),
    Platform('Atari Lynx', 'atari-lynx', 'lynx', None, DAT_NOINTRO, '4924', '18', '28', '58'),
    Platform('Atari ST', 'computer-atari-st', 'atari-st', None, DAT_NONE, '4937', '24', '42', '38'),

    # --- Bandai ---
    Platform('Bandai WonderSwan', 'bandai-wswan', 'wswan', None, DAT_NOINTRO, '4925', '48', '45', '90'),
    Platform('Bandai WonderSwan Color', 'bandai-wswancolor', 'wswancolor', None, DAT_NOINTRO, '4926', '49', '46', '95'),

    Platform('Benesse Pocket Challenge V2', 'console-bpc', 'bpc', None, DAT_NOINTRO, None, None, None, None),

    # --- Casio ---
    Platform('Casio Loopy', 'console-loopy', 'loopy', None, DAT_NOINTRO, None, '124', '98', None),
    Platform('Casio PV-1000', 'console-pv1000', 'pv1000', None, DAT_NOINTRO, '4964', '125', '74', None),

    # --- Coleco ---
    Platform('Coleco Colecovision', 'console-cvision', 'cvision', None, DAT_NOINTRO, '31', '29', '48', '29'),

    # --- Commodore ---
    Platform('Commodore 64', 'computer-c64', 'c64', None, DAT_NONE, '40', '27', '66', '24'),
    Platform('Commodore Amiga', 'computer-amiga', 'amiga', None, DAT_NONE, '4911', '19', '64', '39'),
    # The CD32 is part of a family of Amiga computers and is of similar specification to the Amiga 1200 computer.
    Platform('Commodore CD32', 'console-cd32', 'cd32', None, DAT_REDUMP, '4947', '56', '130', '70'),
    # The CDTV is essentially a Commodore Amiga 500 home computer with a CD-ROM drive and remote control.
    Platform('Commodore CDTV', 'console-cdtv', 'cdtv', None, DAT_REDUMP, None, '83', '129', None),
    # MobyGames "Commodore 16, Plus/4"
    # Not found in GameFAQs.
    Platform('Commodore Plus-4', 'computer-plus4', 'plus4', None, DAT_NONE, None, '115', '99', None),
    Platform('Commodore VIC-20', 'computer-vic20', 'vic20', None, DAT_NONE, '4945', '43', '73', '11'),

    # --- Emerson ---
    Platform('Emerson Arcadia 2001', 'console-arcadia2001', 'arcadia2001', None, DAT_NOINTRO, '4963', '162', '94', None),

    Platform('Entex Adventure Vision', 'console-avision', 'avision', None, DAT_NOINTRO, '4974', '210', '78', None),
    Platform('Epoch Super Cassette Vision', 'console-scvision', 'scvision', None, DAT_NOINTRO, '4966', None, '67', None),

    # --- Fairchild ---
    Platform('Fairchild Channel F', 'console-channelf', 'channelf', None, DAT_NOINTRO, '4928', '76', '80', None),

    # --- Fujitsu ---
    Platform('Fujitsu FM Towns Marty', 'console-fmtmarty', 'fmtmarty', None, DAT_NONE, '4932', '102', '97', '55'),

    Platform('Funtech Super Acan', 'console-superacan', 'superacan', None, DAT_NOINTRO, None, '110', '100', None),
    Platform('GamePark GP32', 'console-gp32', 'gp32', None, DAT_NOINTRO, None, '108', '101', None),

    # --- GCE ---
    Platform('GCE Vectrex', 'console-vectrex', 'vectrex', None, DAT_NONE, '4939', '37', '102', '34'),

    Platform('Hartung Game Master', 'console-gamemaster', 'gamemaster', None, DAT_NOINTRO, None, None, '103', None),
    # The iQue Player is based on the Nintendo 64, but uses system-on-a-chip technology to reduce size.
    # It plays Nintendo 64 games specifically ported to the system. 
    Platform('iQue iQue Player', 'console-ique', 'ique', 'n64', DAT_NOINTRO),
    Platform('Konami Picno', 'console-picno', 'picno', None, DAT_NOINTRO, None, None, None, None),
    Platform('LeapFrog LeapPad', 'console-leappad', 'leappad', None, DAT_NOINTRO, None, None, None, None),
    Platform('LeapFrog Leapster Learning Game System', 'console-llgs', 'llgs', None, DAT_NOINTRO, None, None, None, None),
    Platform('LeapFrog My First LeapPad', 'console-mfleappad', 'mfleappad', None, DAT_NOINTRO, None, None, None, None),

    # --- Libretro ---
    # Use nxengine and not cavestory because in the future there could be nxengine-evo.
    # nxengine is able to launch several versions of the game so it's a ROM launcher.
    Platform('Libretro Cave Story (NX Engine)', 'games-nxengine', 'nxengine', None, DAT_LIBRETRO, None, None, None, None),
    Platform('Libretro ChaiLove', 'games-chailove', 'chailove', None, DAT_LIBRETRO, None, None, None, None),
    Platform('Libretro Doom', 'games-doom', 'doom', None, DAT_LIBRETRO, None, None, None, None),
    Platform('Libretro Doom 3', 'games-doom3', 'doom3', None, DAT_LIBRETRO, None, None, None, None),
    Platform('Libretro EasyRPG', 'games-easyrpg', 'easyrpg', None, DAT_LIBRETRO, None, None, None, None),
    Platform('Libretro Game and Watch', 'games-gw', 'gw', None, DAT_LIBRETRO, None, None, None, None),
    Platform('Libretro Lutro', 'games-lutro', 'lutro', None, DAT_LIBRETRO, None, None, '206', None),
    Platform('Libretro OpenLara', 'games-openlara', 'openlara', None, DAT_LIBRETRO, None, None, None, None),
    Platform('Libretro Quake', 'games-quake', 'quake', None, DAT_LIBRETRO, None, None, None, None),
    Platform('Libretro Quake 2', 'games-quake2', 'quake2', None, DAT_LIBRETRO, None, None, None, None),
    Platform('Libretro Quake 3', 'games-quake3', 'quake3', None, DAT_LIBRETRO, None, None, None, None),
    Platform('Libretro TIC-80', 'games-tic80', 'tic80', None, DAT_LIBRETRO, None, None, '222', None),

    # --- Magnavox ---
    Platform('Magnavox Odyssey2', 'console-odyssey2', 'odyssey2', None, DAT_NOINTRO, '4927', '78', '104', '9'),

    # --- MAME/Arcade ---
    Platform('MAME', 'arcade-mame', 'mame', None, DAT_MAME, '23', '143', '75', '2'),

    # --- Mattel ---
    Platform('Mattel Intellivision', 'console-ivision', 'ivision', None, DAT_NOINTRO, '32', '30', '115', '16'),

    # --- Microsoft ---
    Platform('Microsoft MS-DOS', 'microsoft-msdos', 'msdos', None, DAT_NONE, '1', '2', '135', '19'),
    Platform('Microsoft MSX', 'microsoft-msx', 'msx', None, DAT_NONE, '4929', '57', '113', '40'),
    Platform('Microsoft MSX2', 'microsoft-msx2', 'msx2', None, DAT_NONE, '4929', '57', '116', '40'),
    # MobyGames differentiates Windows = '3' and Windows 3.x = '5'
    Platform('Microsoft Windows', 'microsoft-windows', 'windows', None, DAT_NONE, '1', '3', '136', '19'),
    Platform('Microsoft Xbox', 'microsoft-xbox', 'xbox', None, DAT_NONE, '14', '13', '32', '98'),
    Platform('Microsoft Xbox 360', 'microsoft-xbox360', 'xbox360', None, DAT_NONE, '15', '69', '33', '111'),
    Platform('Microsoft Xbox One', 'microsoft-xboxone', 'xboxone', None, DAT_NONE, '4920', '142', None, '121'),

    # --- NEC ---
    Platform('NEC PC Engine', 'nec-pce', 'pce', None, DAT_NOINTRO, '34', '40', '31', '53'),
    Platform('NEC PC Engine CDROM2', 'nec-pcecd', 'pcecd', None, DAT_REDUMP, '4955', '45', '114', '56'),
    Platform('NEC PC-FX', 'nec-pcfx', 'pcfx', None, DAT_REDUMP, '4930', '59', '72', '79'),
    Platform('NEC PC-FXGA', 'nec-pcfxga', 'pcfxga', 'pcfx'),
    Platform('NEC SuperGrafx', 'nec-sgx', 'sgx', None, DAT_NOINTRO, '34', '127', '105', '53'),
    Platform('NEC TurboGrafx 16', 'nec-tg16', 'tg16', 'pce'),
    Platform('NEC TurboGrafx CD', 'nec-tg16cd', 'tg16cd', 'pcecd'),

    # --- Nintendo ---
    Platform('Nintendo 3DS', 'nintendo-n3ds', 'n3ds', None, DAT_NONE, '4912', '101', '17', '116'),
    Platform('Nintendo 64', 'nintendo-n64', 'n64', None, DAT_NOINTRO, '3', '9', '14', '84'),
    # Nintendo 64DD not found on MobyGames.
    Platform('Nintendo 64DD', 'nintendo-n64dd', 'n64dd', None, DAT_NOINTRO, '3', '9', '122', '92'),
    Platform('Nintendo DS', 'nintendo-nds', 'nds', None, DAT_NONE, '8', '44', '15', '108'),
    Platform('Nintendo DSi', 'nintendo-ndsi', 'ndsi', None, DAT_NONE, '8', '87', '15', '108'),
    Platform('Nintendo e-Reader', 'nintendo-ereader', 'ereader', None, DAT_NOINTRO, None, None, '119', None),
    Platform('Nintendo Famicon', 'nintendo-famicon', 'famicon', 'nes'),
    # FDS not found on MobyGames, make same as NES.
    Platform('Nintendo Famicon Disk System', 'nintendo-fds', 'fds', None, DAT_NOINTRO, '4936', '22', '106', '47'),
    Platform('Nintendo GameBoy', 'nintendo-gb', 'gb', None, DAT_NOINTRO, '4', '10', '9', '59'),
    Platform('Nintendo GameBoy Advance', 'nintendo-gba', 'gba', None, DAT_NOINTRO, '5', '12', '12', '91'),
    Platform('Nintendo GameBoy Color', 'nintendo-gbcolor', 'gbcolor', None, DAT_NOINTRO, '41', '11', '10', '57'),
    Platform('Nintendo GameCube', 'nintendo-gamecube', 'gamecube', None, DAT_REDUMP, '2', '14', '13', '99'),
    Platform('Nintendo NES', 'nintendo-nes', 'nes', None, DAT_NOINTRO, '7', '22', '3', '41'),
    # Pokemon Mini not found in GameFAQs.
    Platform('Nintendo Pokemon Mini', 'nintendo-pokemini', 'pokemini', None, DAT_NOINTRO, '4957', '152', '211', None),
    Platform('Nintendo Satellaview', 'nintendo-satellaview', 'satellaview', None, DAT_NOINTRO, None, None, '107', None),
    Platform('Nintendo SNES', 'nintendo-snes', 'snes', None, DAT_NOINTRO, '6', '15', '4', '63'),
    Platform('Nintendo Sufami Turbo', 'nintendo-sufami', 'sufami', None, DAT_NOINTRO, None, None, '108', None),
    Platform('Nintendo Switch', 'nintendo-switch', 'switch', None, DAT_NONE, '4971', '203', None, '124'),
    Platform('Nintendo Virtual Boy', 'nintendo-vb', 'vb', None, DAT_NOINTRO, '4918', '38', '11', '83'),
    Platform('Nintendo Wii', 'nintendo-wii', 'wii', None, DAT_NONE, '9', '82', '16', '114'),
    Platform('Nintendo Wii U', 'nintendo-wiiu', 'wiiu', None, DAT_NONE, '38', '132', '18', '118'),

    Platform('Ouya Ouya', 'console-ouya', 'ouya', None, DAT_NONE, '4921', '144', None, None),

    # --- Philips ---
    # The Philips Videopac G7000 is the European name of the Magnavox Odyssey².
    Platform('Philips Videopac G7000', 'console-g7000', 'g7000', 'odyssey2'),
    # Alias of g7000 in ScreenScraper. Not found in GameFAQs.
    Platform('Philips Videopac Plus G7400', 'console-g7400', 'g7400', None, DAT_NOINTRO, None, '128', '104', None),

    # --- RCA ---
    Platform('RCA Studio II', 'console-studio2', 'studio2', None, DAT_NOINTRO, '4967', '113', None, None),

    # --- ScummVM ---
    Platform('ScummVM', 'games-scummvm', 'scummvm', None, DAT_NONE, None, None, '123', None),

    # --- Sega ---
    Platform('Sega 32X', 'sega-32x', '32x', None, DAT_NOINTRO, '33', '21', '19', '74'),
    # The Advanced Pico Beena is an upgraded Sega PICO.
    Platform('Sega Beena', 'sega-beena', 'beena', None, DAT_NOINTRO, None, None, None, None),
    Platform('Sega Dreamcast', 'sega-dreamcast', 'dreamcast', None, DAT_REDUMP, '16', '8', '23', '67'),
    Platform('Sega Game Gear', 'sega-gamegear', 'gamegear', None, DAT_NOINTRO, '20', '25', '21', '62'),
    Platform('Sega Genesis', 'sega-genesis', 'genesis', 'megadrive'),
    Platform('Sega Master System', 'sega-sms', 'sms', None, DAT_NOINTRO, '35', '26', '2', '49'),
    Platform('Sega Mega Drive', 'sega-megadrive', 'megadrive', None, DAT_NOINTRO, '36', '16', '1', '54'),
    Platform('Sega MegaCD', 'sega-megacd', 'megacd', None, DAT_REDUMP, '21', '20', '20', '65'),
    Platform('Sega PICO', 'sega-pico', 'pico', None, DAT_NOINTRO, '4958', '103', None, None),
    Platform('Sega Saturn', 'sega-saturn', 'saturn', None, DAT_REDUMP, '17', '23', '22', '76'),
    # The SG-1000 was released in several forms, including the SC-3000 computer and the redesigned SG-1000 II.
    Platform('Sega SC-3000', 'sega-sc3000', 'sc3000', 'sg1000'),
    Platform('Sega SegaCD', 'sega-segacd', 'segacd', 'megacd'),
    Platform('Sega SG-1000', 'sega-sg1000', 'sg1000', None, DAT_NOINTRO, '4949', '114', '109', '43'),

    # --- Sharp ---
    Platform('Sharp X68000', 'computer-x68k', 'x68k', None, DAT_NONE, '4931', '106', '79', '52'),

    # --- Sinclair ---
    Platform('Sinclair ZX Spectrum', 'computer-spectrum', 'spectrum', None, DAT_NONE, '4913', '41', '76', '35'),
    Platform('Sinclair ZX Spectrum Plus 3', 'spectrump3', 'spectrump3', None, DAT_NONE, None, None, None, None),
    # I think the ZX80 and the ZX81 are incompatible computers.
    Platform('Sinclair ZX80', 'computer-zx80', 'zx80', None, DAT_LIBRETRO, None, '118', None, None),
    Platform('Sinclair ZX81', 'computer-zx81', 'zx81', None, DAT_LIBRETRO, None, '119', '77', None),

    # --- SNK ---
    # MobyGames has a platform Neo Geo = '36'
    # ScreenScraper has a platform Neo Geo AES = '142'
    # GameFAQs has a platform NeoGeo = '64'
    Platform('SNK Neo-Geo AES', 'snk-aes', 'aes', 'mame'),
    Platform('SNK Neo-Geo CD', 'snk-neocd', 'neocd', None, DAT_REDUMP, '4956', '54', '70', '68'),
    # ScreenScraper has a platform for Neo Geo MVS = '68'
    Platform('SNK Neo-Geo MVS', 'snk-mvs', 'mvs', 'mame'),
    Platform('SNK Neo-Geo Pocket', 'snk-ngp', 'ngp', None, DAT_NOINTRO, '4922', '52', '25', None),
    Platform('SNK Neo-Geo Pocket Color', 'snk-ngpc', 'ngpc', None, DAT_NOINTRO, '4923', '53', '82', '89'),

    # --- SONY ---
    Platform('Sony PlayStation', 'sony-psx', 'psx', None, DAT_REDUMP, '10', '6', '57', '78'),
    Platform('Sony PlayStation 2', 'sony-ps2', 'ps2', None, DAT_REDUMP, '11', '7', '58', '94'),
    Platform('Sony PlayStation 3', 'sony-ps3', 'ps3', None, DAT_NONE, '12', '81', '59', '113'),
    Platform('Sony PlayStation 4', 'sony-ps4', 'ps4', None, DAT_NONE, '4919', '141', None, '120'),
    Platform('Sony PlayStation Portable', 'sony-psp', 'psp', None, DAT_REDUMP, '13', '46', '61', '109'),
    Platform('Sony PlayStation Vita', 'sony-psvita', 'psvita', None, DAT_NONE, '39', '105', '62', '117'),

    Platform('Tiger Game.com', 'console-tigergame', 'tigergame', None, DAT_NOINTRO, '4940', '50', '121', None),
    Platform('VTech CreatiVision', 'console-creativision', 'creativision', None, DAT_NOINTRO, None, '212', None, None),
    Platform('VTech V.Flash', 'console-vflash', 'vflash', None, DAT_REDUMP, None, '189', None, None),
    Platform('VTech V.Smile', 'console-vsmile', 'vsmile', None, DAT_NOINTRO, None, '42', '120', None),
    Platform('VTech V.Smile Pro', 'console-vsmilepro', 'vsmilepro', 'vflash'),
    Platform('Watara Supervision', 'console-supervision', 'supervision', None, DAT_NOINTRO, '4959', '109', '207', None),
    Platform('Zeebo Zeebo', 'console-zeebo', 'zeebo', None, DAT_NOINTRO, None, '88', None, None),

    # --- Unknown ---
    Platform('Unknown', 'unknown', 'unknown', None, DAT_NONE, None, None, None, None),
]

# --- Add category to platform objects ---
# The category is the first part of the short name.
for p_obj in AEL_platforms:
    p_obj.category = p_obj.short_name.split('-')[0]
# Dictionaries for fast access to the platform information.
platform_short_to_long_dic = {}
platform_compact_to_long_dic = {}
platform_long_to_index_dic = {}
for index, p_obj in enumerate(AEL_platforms):
    platform_short_to_long_dic[p_obj.short_name] = p_obj.long_name
    platform_compact_to_long_dic[p_obj.compact_name] = p_obj.long_name
    platform_long_to_index_dic[p_obj.long_name] = index

#
# Returns the platform numerical index from the platform name. If the platform name is not
# found then returns the index of the 'Unknown' platform
#
def get_AEL_platform_index(platform_name):
    if platform_name in platform_long_to_index_dic:
        return platform_long_to_index_dic[platform_name]
    else:
        return platform_long_to_index_dic['Unknown']

# NOTE must take into account platform aliases.
# '0' means any platform in TGDB and must be returned when there is no platform matching.
def AEL_platform_to_TheGamesDB(platform_AEL):
    if platform_name in platform_long_to_index_dic:
        pobj = AEL_platforms[platform_long_to_index_dic[platform_name]]
    else:
        # Platform not found.
        return DEFAULT_PLAT_TGDB
    # Check if platform is an alias.
    scraper_platform = pobj.TGDB_plat
    if pobj.aliasof is not None and scraper_platform is None:
        # If alias does not have specific platform return platform of parent.
        return AEL_platform_to_TheGamesDB(platform_compact_to_long_dic[pobj.aliasof])
    # If platform is None then return default platform
    if scraper_platform is None:
        return DEFAULT_PLAT_TGDB
    else:
        return scraper_platform

# * MobyGames API cannot be used withouth a valid platform.
# * If '0' is used as the Unknown platform then MobyGames returns an HTTP error
#    "HTTP Error 422: UNPROCESSABLE ENTITY"
# * If '' is used as the Unknwon platform then MobyGames returns and HTTP error
#   "HTTP Error 400: BAD REQUEST"
# * The solution is to use '0' as the unknwon platform. AEL will detect this and
#   will remove the '&platform={}' parameter from the search URL.
def AEL_platform_to_MobyGames(platform_AEL):
    if platform_name in platform_long_to_index_dic:
        pobj = AEL_platforms[platform_long_to_index_dic[platform_name]]
    else:
        return DEFAULT_PLAT_MOBYGAMES
    scraper_platform = pobj.MG_plat
    if pobj.aliasof is not None and scraper_platform is None:
        return AEL_platform_to_MobyGames(platform_compact_to_long_dic[pobj.aliasof])
    if scraper_platform is None:
        return DEFAULT_PLAT_MOBYGAMES
    else:
        return scraper_platform

def AEL_platform_to_ScreenScraper(platform_AEL):
    if platform_name in platform_long_to_index_dic:
        pobj = AEL_platforms[platform_long_to_index_dic[platform_name]]
    else:
        return DEFAULT_PLAT_SCREENSCRAPER
    scraper_platform = pobj.SS_plat
    if pobj.aliasof is not None and scraper_platform is None:
        return AEL_platform_to_ScreenScraper(platform_compact_to_long_dic[pobj.aliasof])
    if scraper_platform is None:
        return DEFAULT_PLAT_SCREENSCRAPER
    else:
        return scraper_platform

# Platform '0' means all platforms in GameFAQs.
def AEL_platform_to_GameFAQs(AEL_gamesys):
    if platform_name in platform_long_to_index_dic:
        pobj = AEL_platforms[platform_long_to_index_dic[platform_name]]
    else:
        return DEFAULT_PLAT_GAMEFAQS
    scraper_platform = pobj.GF_plat
    if pobj.aliasof is not None and scraper_platform is None:
        return AEL_platform_to_GameFAQs(platform_compact_to_long_dic[pobj.aliasof])
    if scraper_platform is None:
        return DEFAULT_PLAT_GAMEFAQS
    else:
        return scraper_platform

# -------------------------------------------------------------------------------------------------
# Translation of AEL oficial gamesys (platform) name to scraper particular name
# -------------------------------------------------------------------------------------------------
# NOTE change the offline scraper so the database name is the same as the platform long name.
platform_AEL_to_Offline_GameDBInfo_XML = {
    '3DO Interactive Multiplayer' : 'GameDBInfo/Panasonic 3DO.xml',

    'Amstrad CPC'                 : '',

    'Atari 2600'                  : 'GameDBInfo/Atari 2600.xml',
    'Atari 5200'                  : 'GameDBInfo/Atari 5200.xml',
    'Atari 7800'                  : 'GameDBInfo/Atari 7800.xml',
    'Atari Jaguar'                : 'GameDBInfo/Atari Jaguar.xml',
    'Atari Jaguar CD'             : 'GameDBInfo/Atari Jaguar CD.xml',
    'Atari Lynx'                  : 'GameDBInfo/Atari Lynx.xml',
    'Atari 8-bit'                 : '',
    'Atari ST'                    : 'GameDBInfo/Atari ST.xml',

    'Bandai WonderSwan'           : '',
    'Bandai WonderSwan Color'     : '',

    'Colecovision'                : 'GameDBInfo/Colecovision.xml',

    'Commodore 64'                : 'GameDBInfo/Commodore 64.xml',
    'Commodore Amiga'             : 'GameDBInfo/Commodore Amiga.xml',
    'Commodore Amiga CD32'        : '',
    'Commodore Plus-4'            : 'GameDBInfo/Commodore Plus-4.xml',
    'Commodore VIC-20'            : 'GameDBInfo/Commodore VIC-20.xml',

    'Emerson Arcadia 2001'        : '',

    'Fairchild Channel F'         : '',

    'Fujitsu FM Towns Marty'      : '',
    
    'GCE Vectrex'                 : '',

    'Magnavox Odyssey2'           : 'GameDBInfo/Magnavox Odyssey2.xml',

    'MAME'                        : 'GameDBInfo/MAME.xml',

    'Mattel Intellivision'        : '',

    'Microsoft MS-DOS'            : 'GameDBInfo/Microsoft MS-DOS.xml',
    'Microsoft MSX'               : '',
    'Microsoft MSX2'              : 'GameDBInfo/Microsoft MSX 2.xml',
    'Microsoft Windows'           : '',
    'Microsoft Xbox'              : '',
    'Microsoft Xbox 360'          : '',
    'Microsoft Xbox One'          : '',

    'NEC PC Engine'               : 'GameDBInfo/NEC PC Engine.xml',
    'NEC PC Engine CDROM2'        : 'GameDBInfo/NEC PC Engine CDROM2.xml',
    'NEC TurboGrafx 16'           : 'GameDBInfo/NEC TurboGrafx 16.xml',
    'NEC TurboGrafx CD'           : 'GameDBInfo/NEC TurboGrafx CD.xml',
    'NEC SuperGrafx'              : 'GameDBInfo/NEC SuperGrafx.xml',
    'NEC PC-FX'                   : 'GameDBInfo/NEC PC-FX.xml',

    'Nintendo 3DS'                : '',
    'Nintendo 64'                 : 'GameDBInfo/Nintendo 64.xml',
    'Nintendo 64DD'               : '',
    'Nintendo DS'                 : 'GameDBInfo/Nintendo DS.xml',
    'Nintendo DSi'                : '',
    'Nintendo Famicom'            : 'GameDBInfo/Nintendo NES.xml',
    'Nintendo Famicom Disk System': 'GameDBInfo/Nintendo Famicom Disk System.xml',
    'Nintendo GameBoy'            : 'GameDBInfo/Nintendo Game Boy.xml',
    'Nintendo GameBoy Advance'    : 'GameDBInfo/Nintendo Game Boy Advance.xml',
    'Nintendo GameBoy Color'      : 'GameDBInfo/Nintendo Game Boy Color.xml',
    'Nintendo GameCube'           : 'GameDBInfo/Nintendo GameCube.xml',
    'Nintendo NES'                : 'GameDBInfo/Nintendo NES.xml',
    'Nintendo Pokemon Mini'       : '',
    'Nintendo SNES'               : 'GameDBInfo/Nintendo SNES.xml',
    'Nintendo Switch'             : '',
    'Nintendo Virtual Boy'        : 'GameDBInfo/Nintendo Virtual Boy.xml',
    'Nintendo Wii'                : 'GameDBInfo/Nintendo Wii.xml',
    'Nintendo Wii U'              : '',

    'Philips Videopac G7000'      : 'GameDBInfo/Magnavox Odyssey2.xml',
    'Philips Videopac Plus G7400' : '',

    'RCA Studio II'               : '',

    'ScummVM'                     : '',

    'Sega 32X'                    : 'GameDBInfo/Sega 32x.xml',
    'Sega Dreamcast'              : 'GameDBInfo/Sega Dreamcast.xml',
    'Sega Game Gear'              : 'GameDBInfo/Sega Game Gear.xml',
    'Sega Genesis'                : 'GameDBInfo/Sega MegaDrive.xml',
    'Sega Master System'          : 'GameDBInfo/Sega Master System.xml',
    'Sega MegaCD'                 : 'GameDBInfo/Sega CD.xml',
    'Sega MegaDrive'              : 'GameDBInfo/Sega MegaDrive.xml',
    'Sega PICO'                   : '',
    'Sega Saturn'                 : 'GameDBInfo/Sega Saturn.xml',
    'Sega SC-3000'                : '',
    'Sega SegaCD'                 : 'GameDBInfo/Sega CD.xml',
    'Sega SG-1000'                : 'GameDBInfo/Sega SG-1000.xml',

    'Sharp X68000'                : '',

    'Sinclair ZX Spectrum'        : 'GameDBInfo/Sinclair ZX Spectrum.xml',

    'SNK Neo-Geo AES'             : '',
    'SNK Neo-Geo CD'              : 'GameDBInfo/SNK Neo-Geo CD.xml',
    'SNK Neo-Geo MVS'             : '',
    'SNK Neo-Geo Pocket'          : 'GameDBInfo/SNK Neo-Geo Pocket.xml',
    'SNK Neo-Geo Pocket Color'    : 'GameDBInfo/SNK Neo-Geo Pocket Color.xml',

    'Sony PlayStation'            : 'GameDBInfo/Sony PlayStation.xml',
    'Sony PlayStation 2'          : 'GameDBInfo/Sony Playstation 2.xml',
    'Sony PlayStation 3'          : '',
    'Sony PlayStation 4'          : '',
    'Sony PlayStation Portable'   : 'GameDBInfo/Sony PlayStation Portable.xml',
    'Sony PlayStation Vita'       : '',

    'Watara Supervision'          : '',

    'Unknown'                     : ''
}

# -------------------------------------------------------------------------------------------------
# Miscellaneous emulator and gamesys (platforms) supported.
# -------------------------------------------------------------------------------------------------
def emudata_get_program_arguments(app):
    # Based on the app. name, retrieve the default arguments for the app.
    applications = {
        'mame'        : '"$rom$"',
        'mednafen'    : '-fs 1 "$rom$"',
        'mupen64plus' : '--nogui --noask --noosd --fullscreen "$rom$"',
        'nestopia'    : '"$rom$"',
        'xbmc'        : 'PlayMedia($rom$)',
        'kodi'        : 'PlayMedia($rom$)',
        'retroarch'   : '-L /path/to/core -f "$rom$"',
        'yabause'     : '-a -f -i "$rom$"',
    }
    for application, arguments in applications.iteritems():
        if app.lower().find(application) >= 0:
            return arguments

    return '"$rom$"'

def emudata_get_program_extensions(app):
    # Based on the app. name, retrieve the recognized extension of the app.
    applications = {
        'mame'       : 'zip|7z',
        'mednafen'   : 'zip|cue',
        'mupen64plus': 'z64|zip|n64',
        'nestopia'   : 'nes|zip',
        'retroarch'  : 'zip|cue',
        'yabause'    : 'cue',
    }
    for application, extensions in applications.iteritems():
        if app.lower().find(application) >= 0:
            return extensions

    return ''
