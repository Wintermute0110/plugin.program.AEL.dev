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

# -------------------------------------------------------------------------------------------------
# New platform engine
# -------------------------------------------------------------------------------------------------
DAT_MAME     = 'MAME'
DAT_NOINTRO  = 'No-Intro'
DAT_REDUMP   = 'Redump'
DAT_LIBRETRO = 'Libretro'
DAT_NONE     = None
DEFAULT_PLAT_TGDB          =  0
DEFAULT_PLAT_MOBYGAMES     = '0'
DEFAULT_PLAT_SCREENSCRAPER = '0'
DEFAULT_PLAT_GAMEFAQS      = '0'
PLATFORM_MAME_LONG    = 'MAME'
PLATFORM_MAME_SHORT   = 'arcade-mame'
PLATFORM_MAME_COMPACT = 'mame'
PLATFORM_UNKNOWN_LONG    = 'Unknown'
PLATFORM_UNKNOWN_SHORT   = 'unknown'
PLATFORM_UNKNOWN_COMPACT = 'unknown'
class Platform:
    def __init__(self, name, shortname, compactname, aliasof = None,
        TGDB_plat = None, MG_plat = None, SS_plat = None, GF_plat = None,
        DAT = DAT_NONE, DAT_prefix = ''):
        # Autocompleted later with data from the short name.
        # Short names are "category-compact_name"
        self.category     = ''
        self.long_name    = name
        self.short_name   = shortname
        self.compact_name = compactname
        # Always use the compact name when definid aliases. Otherwise bad things will happen.
        self.aliasof      = aliasof
        self.TGDB_plat    = TGDB_plat
        self.MG_plat      = MG_plat
        self.SS_plat      = SS_plat
        self.GF_plat      = GF_plat
        self.DAT          = DAT
        self.DAT_prefix   = DAT_prefix

# * From this list create dictionaries with indices to access platform information.
#
# * Shorted alphabetically by long name. Alphabetical order is veryfied with the script
#   ./dev-core/list_AEL_platforms.py
#
# * To be compatible with Retroplayer and Kodi artwork database, anything that can be launched
#   by Retroarch must be a platform, including Doom, CaveStory, etc.
#
# * Platform is something that has ROMs to launch. Standalone cores do not need a platform,
#   they are Kodi addons with its own artwork. CHECK THIS!
#
# * Platform names must have filesystem-safe characters.
#
# * When possible user No-Intro DAT-o-MATIC names. Fallback to Wikipedia names.
#
# * Unsuported scraper platforms must be set to None. The conversion function will then
#   translate None to the appropiate value for the scraper.
#
# * The Offline Scraper database filenames use the long_name. The platform icons
#   PNG/JPG files also use the platform long_name.
#
# Get TGDB platform list from script ./dev-scrapers/scrap_TGDB_list_platforms.py
# Get MobyGames platform list from script ./dev-scrapers/scrap_MobyGames_list_platforms.py
# Get ScreenScraper platform list from script ./dev-scrapers/scrap_ScreenScraper_list_platforms.py
# Get GameFAQs platform list from https://www.gamefaqs.com/search_advanced?game=ar
#
# Default values: Platform('', '', '', None, None, None, None, None, DAT_NONE, ''),
#
AEL_platforms = [
    # --- 3DO Interactive Multiplayer ---
    Platform('3DO Interactive Multiplayer', 'console-3do', '3do', None, 25, '35', '29', '61',
        DAT_REDUMP, 'Panasonic - 3DO Interactive Multiplayer - Datfile'),

    # --- Amstrad ---
    Platform('Amstrad CPC', 'computer-cpc', 'cpc', None, 4914, '60', '65', '46', DAT_NONE),

    # --- Atari ---
    Platform('Atari 2600', 'atari-a2600', 'a2600', None, 22, '28', '26', '6',
        DAT_NOINTRO, 'Atari - 2600'),
    Platform('Atari 5200', 'atari-a5200', 'a5200', None, 26, '33', '40', '20',
        DAT_NOINTRO, 'Atari - 5200'),
    Platform('Atari 7800', 'atari-a7800', 'a7800', None, 27, '34', '41', '51',
        DAT_NOINTRO, 'Atari - 7800'),
    # Atari 8-bit includes: Atari 400, Atari 800, Atari 1200XL, Atari 65XE, Atari 130XE, Atari XEGS
    Platform('Atari 8-bit', 'computer-atari-8bit', 'atari-8bit', None, 30, '39', '43', None, DAT_NONE),
    # Atari Jaguar No-Intro DATs:
    # *) Atari - Jaguar (J64) (20190518-213240).dat
    # *) Atari - Jaguar (J64) (Parent-Clone) (Parent-Clone) (20190518-213240).dat
    # *) Atari - Jaguar (ROM) (20190518-213240).dat
    Platform('Atari Jaguar', 'atari-jaguar', 'jaguar', None, 28, '17', '27', '72',
        DAT_NOINTRO, 'Atari - Jaguar (J64) (Parent-Clone)'),
    Platform('Atari Jaguar CD', 'atari-jaguarcd', 'jaguarcd', None, 29, '17', '171', '82',
        DAT_REDUMP, 'Atari - Jaguar CD Interactive Multimedia System - Datfile'),
    Platform('Atari Lynx', 'atari-lynx', 'lynx', None, 4924, '18', '28', '58',
        DAT_NOINTRO, 'Atari - Lynx'),
    Platform('Atari ST', 'computer-atari-st', 'atari-st', None, 4937, '24', '42', '38',
        DAT_NOINTRO, 'Atari - ST'),

    # --- Bandai ---
    Platform('Bandai WonderSwan', 'bandai-wswan', 'wswan', None, 4925, '48', '45', '90',
        DAT_NOINTRO, 'Bandai - WonderSwan'),
    Platform('Bandai WonderSwan Color', 'bandai-wswancolor', 'wswancolor', None, 4926, '49', '46', '95',
        DAT_NOINTRO, 'Bandai - WonderSwan Color'),

    Platform('Benesse Pocket Challenge V2', 'console-bpc', 'bpc', None, None, None, None, None,
        DAT_NOINTRO, 'Benesse - Pocket Challenge V2'),

    # --- Casio ---
    Platform('Casio Loopy', 'console-loopy', 'loopy', None, None, '124', '98', None,
        DAT_NOINTRO, 'Casio - Loopy'),
    Platform('Casio PV-1000', 'console-pv1000', 'pv1000', None, 4964, '125', '74', None,
        DAT_NOINTRO, 'Casio - PV-1000'),

    # --- Coleco ---
    Platform('Coleco Colecovision', 'console-cvision', 'cvision', None, 31, '29', '48', '29',
        DAT_NOINTRO, 'Coleco - ColecoVision'),

    # --- Commodore ---
    # The Commodore 16 and the Plus/4 are the same computer, the Plus/4 having more memory
    # and better ROM software. Make the Plus/4 an alias of the Commodore 16.
    # No-Intro has a DAT for the Plus/4 and not for the C16.
    # MobyGames "Commodore 16, Plus/4". Not found in GameFAQs.
    Platform('Commodore 16', 'computer-16', 'c16', None, None, '115', '99', None,
        DAT_NOINTRO, 'Commodore - Plus-4'),
    # Commodore 64 No-Intro DATs:
    # * Commodore - 64 (Parent-Clone) (20151122-035618).dat
    # * Commodore - 64 (PP) (Parent-Clone) (20131204-081826).dat
    # * Commodore - 64 (Tapes) (Parent-Clone) (20180307-232531).dat
    Platform('Commodore 64', 'computer-c64', 'c64', None, 40, '27', '66', '24',
        DAT_NOINTRO, 'Commodore - 64'),
    Platform('Commodore Amiga', 'computer-amiga', 'amiga', None, 4911, '19', '64', '39',
        DAT_NOINTRO, 'Commodore - Amiga'),
    # The CD32 is part of a family of Amiga computers and is of similar specification to the
    # Amiga 1200 computer.
    Platform('Commodore Amiga CD32', 'console-cd32', 'cd32', None, 4947, '56', '130', '70',
        DAT_REDUMP, 'Commodore - Amiga CD32 - Datfile'),
    # The CDTV is essentially a Commodore Amiga 500 home computer with a CD-ROM drive and
    # remote control.
    Platform('Commodore Amiga CDTV', 'console-cdtv', 'cdtv', None, None, '83', '129', None,
        DAT_REDUMP, 'Commodore - Amiga CDTV - Datfile'),
    # The PET is the first computer sold by Commodore.
    Platform('Commodore PET', 'computer-pet', 'pet', None, None, None, None, None),
    # MobyGames "Commodore 16, Plus/4". Not found in GameFAQs.
    Platform('Commodore Plus-4', 'computer-plus4', 'plus4', 'c16'),
    Platform('Commodore VIC-20', 'computer-vic20', 'vic20', None, 4945, '43', '73', '11',
        DAT_NOINTRO, 'Commodore - VIC-20'),

    # --- Emerson ---
    Platform('Emerson Arcadia 2001', 'console-arcadia2001', 'arcadia2001', None, 4963, '162', '94', None,
        DAT_NOINTRO, 'Emerson - Arcadia 2001'),

    Platform('Entex Adventure Vision', 'console-avision', 'avision', None, 4974, '210', '78', None,
        DAT_NOINTRO, 'Entex - Adventure Vision'),
    Platform('Epoch Super Cassette Vision', 'console-scvision', 'scvision', None, 4966, None, '67', None,
        DAT_NOINTRO, 'Epoch - Super Cassette Vision'),

    # --- Fairchild ---
    Platform('Fairchild Channel F', 'console-channelf', 'channelf', None, 4928, '76', '80', None,
        DAT_NOINTRO, 'Fairchild - Channel F'),

    # --- Fujitsu ---
    Platform('Fujitsu FM Towns Marty', 'console-fmtmarty', 'fmtmarty', None, 4932, '102', '97', '55', DAT_NONE),

    Platform('Funtech Super Acan', 'console-superacan', 'superacan', None, None, '110', '100', None,
        DAT_NOINTRO, 'Funtech - Super Acan'),
    Platform('GamePark GP32', 'console-gp32', 'gp32', None, None, '108', '101', None,
        DAT_NOINTRO, 'GamePark - GP32'),

    # --- GCE ---
    Platform('GCE Vectrex', 'console-vectrex', 'vectrex', None, 4939, '37', '102', '34',
        DAT_NOINTRO, 'GCE - Vectrex'),

    Platform('Hartung Game Master', 'console-gamemaster', 'gamemaster', None, None, None, '103', None,
        DAT_NOINTRO, 'Hartung - Game Master'),
    # The iQue Player is based on the Nintendo 64, but uses system-on-a-chip technology to reduce size.
    # It plays Nintendo 64 games specifically ported to the system. 
    # iQue No-Intro DATs:
    # *) iQue - iQue (CDN) (20190927-125114).dat
    # *) iQue - iQue (Decrypted) (20190927-125114)
    # *) iQue - iQue (Decrypted) (Parent-Clone) (Parent-Clone) (20190927-125114)
    Platform('iQue iQue Player', 'console-ique', 'ique', 'n64', None, None, None, None,
        DAT_NOINTRO, 'iQue - iQue (Decrypted) (Parent-Clone)'),
    Platform('Konami Picno', 'console-picno', 'picno', None, None, None, None, None,
        DAT_NOINTRO, 'Konami - Picno'),
    Platform('LeapFrog LeapPad', 'console-leappad', 'leappad', None, None, None, None, None,
        DAT_NOINTRO, 'LeapFrog - LeapPad'),
    Platform('LeapFrog Leapster Learning Game System', 'console-llgs', 'llgs', None, None, None, None, None,
        DAT_NOINTRO, 'LeapFrog - Leapster Learning Game System'),
    Platform('LeapFrog My First LeapPad', 'console-mfleappad', 'mfleappad', None, None, None, None, None,
        DAT_NOINTRO, 'LeapFrog - My First LeapPad'),

    # --- Libretro ---
    # Use nxengine and not cavestory because in the future there could be nxengine-evo.
    # nxengine is able to launch several versions of the game so it's a ROM launcher.
    Platform('Libretro Cave Story (NX Engine)', 'games-nxengine', 'nxengine', None, None, None, None, None, DAT_LIBRETRO),
    Platform('Libretro ChaiLove', 'games-chailove', 'chailove', None, None, None, None, None, DAT_LIBRETRO),
    Platform('Libretro Doom', 'games-doom', 'doom', None, None, None, None, None, DAT_LIBRETRO),
    Platform('Libretro Doom 3', 'games-doom3', 'doom3', None, None, None, None, None, DAT_LIBRETRO),
    Platform('Libretro EasyRPG', 'games-easyrpg', 'easyrpg', None, None, None, None, None, DAT_LIBRETRO),
    Platform('Libretro Game and Watch', 'games-gw', 'gw', None, None, None, None, None, DAT_LIBRETRO),
    Platform('Libretro Lutro', 'games-lutro', 'lutro', None, None, None, '206', None, DAT_LIBRETRO),
    Platform('Libretro OpenLara', 'games-openlara', 'openlara', None, None, None, None, None, DAT_LIBRETRO),
    Platform('Libretro Quake', 'games-quake', 'quake', None, None, None, None, None, DAT_LIBRETRO),
    Platform('Libretro Quake 2', 'games-quake2', 'quake2', None, None, None, None, None, DAT_LIBRETRO),
    Platform('Libretro Quake 3', 'games-quake3', 'quake3', None, None, None, None, None, DAT_LIBRETRO),
    Platform('Libretro TIC-80', 'games-tic80', 'tic80', None, None, None, '222', None, DAT_LIBRETRO),

    # --- Magnavox ---
    Platform('Magnavox Odyssey2', 'console-odyssey2', 'odyssey2', None, 4927, '78', '104', '9',
        DAT_NOINTRO, 'Magnavox - Odyssey2'),

    # --- MAME/Arcade ---
    Platform(PLATFORM_MAME_LONG, PLATFORM_MAME_SHORT, PLATFORM_MAME_COMPACT, None, 23, '143', '75', '2', DAT_MAME),

    # --- Mattel ---
    Platform('Mattel Intellivision', 'console-ivision', 'ivision', None, 32, '30', '115', '16',
        DAT_NOINTRO, 'Mattel - Intellivision'),

    # --- Microsoft ---
    Platform('Microsoft MS-DOS', 'microsoft-msdos', 'msdos', None, 1, '2', '135', '19', DAT_NONE),
    Platform('Microsoft MSX', 'microsoft-msx', 'msx', None, 4929, '57', '113', '40',
        DAT_NOINTRO, 'Microsoft - MSX'),
    Platform('Microsoft MSX2', 'microsoft-msx2', 'msx2', None, 4929, '57', '116', '40',
        DAT_NOINTRO, 'Microsoft - MSX2'),
    # Modern versions of Windows.
    Platform('Microsoft Windows', 'microsoft-windows', 'windows', None, None, None, None, None, DAT_NONE),
    # MobyGames differentiates Windows = '3' and Windows 3.x = '5'
    Platform('Microsoft Windows 3.x', 'microsoft-windows3x', 'windows3x', None, 1, '3', '136', '19', DAT_NONE),
    Platform('Microsoft Xbox', 'microsoft-xbox', 'xbox', None, 14, '13', '32', '98', DAT_NONE),
    Platform('Microsoft Xbox 360', 'microsoft-xbox360', 'xbox360', None, 15, '69', '33', '111', DAT_NONE),
    Platform('Microsoft Xbox One', 'microsoft-xboxone', 'xboxone', None, 4920, '142', None, '121', DAT_NONE),

    # --- NEC ---
    Platform('NEC PC Engine', 'nec-pce', 'pce', None, 34, '40', '31', '53',
        DAT_NOINTRO, 'NEC - PC Engine - TurboGrafx 16'),
    Platform('NEC PC Engine CDROM2', 'nec-pcecd', 'pcecd', None, 4955, '45', '114', '56',
        DAT_REDUMP, 'NEC - PC Engine CD & TurboGrafx CD - Datfile'),
    Platform('NEC PC-FX', 'nec-pcfx', 'pcfx', None, 4930, '59', '72', '79',
        DAT_REDUMP, 'NEC - PC-FX & PC-FXGA - Datfile'),
    Platform('NEC PC-FXGA', 'nec-pcfxga', 'pcfxga', 'pcfx'),
    Platform('NEC SuperGrafx', 'nec-sgx', 'sgx', None, 34, '127', '105', '53',
        DAT_NOINTRO, 'NEC - PC Engine SuperGrafx'),
    Platform('NEC TurboGrafx 16', 'nec-tg16', 'tg16', 'pce'),
    Platform('NEC TurboGrafx CD', 'nec-tg16cd', 'tg16cd', 'pcecd'),

    # --- Nintendo ---
    # No-Intro Nintendo 3DS DAT files:
    # *) Nintendo - Nintendo 3DS (Decrypted) (20191109-080816)
    # *) Nintendo - Nintendo 3DS (Digital) (20190801-212709)
    # *) Nintendo - Nintendo 3DS (Digital) (CDN) (CDN) (20191110-064909)
    # *) Nintendo - Nintendo 3DS (Digital) (CDN) (CDN) (Parent-Clone) (Parent-Clone) (20191110-064909)
    # *) Nintendo - Nintendo 3DS (Digital) (CDN) (CIA) (20191110-064909)
    # *) Nintendo - Nintendo 3DS (Digital) (CDN) (Console) (20191110-064909)
    # *) Nintendo - Nintendo 3DS (Digital) (Parent-Clone) (20190801-212709)
    # *) Nintendo - Nintendo 3DS (Encrypted) (20191109-080816)
    # *) Nintendo - Nintendo 3DS (Encrypted) (Parent-Clone) (Parent-Clone) (20191109-080816)
    Platform('Nintendo 3DS', 'nintendo-n3ds', 'n3ds', None, 4912, '101', '17', '116',
        DAT_NOINTRO, 'Nintendo - Nintendo 3DS (Encrypted) (Parent-Clone)'),
    # No-Intro Nintendo 64 DAT files:
    # *) Nintendo - Nintendo 64 (BigEndian) (20190918-121135)
    # *) Nintendo - Nintendo 64 (BigEndian) (Parent-Clone) (Parent-Clone) (20190918-121135)
    # *) Nintendo - Nintendo 64 (ByteSwapped) (20190918-121135)
    Platform('Nintendo 64', 'nintendo-n64', 'n64', None, 3, '9', '14', '84',
        DAT_NOINTRO, 'Nintendo - Nintendo 64 (BigEndian) (Parent-Clone)'),
    # Nintendo 64DD not found on MobyGames.
    Platform('Nintendo 64DD', 'nintendo-n64dd', 'n64dd', None, 3, '9', '122', '92',
        DAT_NOINTRO, 'Nintendo - Nintendo 64DD'),
    # No-Intro Nintendo DS DAT files:
    # *) Nintendo - Nintendo DS (Decrypted) (20191117-150815)
    # *) Nintendo - Nintendo DS (Decrypted) (Parent-Clone) (Parent-Clone) (20191117-150815)
    # *) Nintendo - Nintendo DS (Download Play) (20190825-082425)
    # *) Nintendo - Nintendo DS (Download Play) (Parent-Clone) (20190825-082425)
    # *) Nintendo - Nintendo DS (Encrypted) (20191117-150815)
    Platform('Nintendo DS', 'nintendo-nds', 'nds', None, 8, '44', '15', '108',
        DAT_NOINTRO, 'Nintendo - Nintendo DS (Decrypted) (Parent-Clone)'),
    # No-Intro Nintendo DSi DAT files:
    # *) Nintendo - Nintendo DSi (Decrypted) (20190503-112150)
    # *) Nintendo - Nintendo DSi (Decrypted) (Parent-Clone) (Parent-Clone) (20190503-112150)
    # *) Nintendo - Nintendo DSi (Digital) (20190813-061824)
    # *) Nintendo - Nintendo DSi (Digital) (Parent-Clone) (20190813-061824)
    # *) Nintendo - Nintendo DSi (Encrypted) (20190503-112150)
    Platform('Nintendo DSi', 'nintendo-ndsi', 'ndsi', None, 8, '87', '15', '108',
        DAT_NOINTRO, 'Nintendo - Nintendo DSi (Decrypted) (Parent-Clone)'),
    Platform('Nintendo e-Reader', 'nintendo-ereader', 'ereader', None, None, None, '119', None,
        DAT_NOINTRO, 'Nintendo - e-Reader'),
    Platform('Nintendo Famicon', 'nintendo-famicon', 'famicon', 'nes'),
    # FDS not found on MobyGames, make same as NES.
    # FDS No-Intro DAT files:
    # *) Nintendo - Family Computer Disk System (FDS) (20191109-080316)
    # *) Nintendo - Family Computer Disk System (FDS) (Parent-Clone) (Parent-Clone) (20191109-080316)
    # *) Nintendo - Family Computer Disk System (FDSStickBIN) (20191109-080316)
    # *) Nintendo - Family Computer Disk System (FDSStickRAW) (20191109-080316)
    # *) Nintendo - Family Computer Disk System (QD) (20191109-080316)
    Platform('Nintendo Famicon Disk System', 'nintendo-fds', 'fds', None, 4936, '22', '106', '47',
        DAT_NOINTRO, 'Nintendo - Family Computer Disk System (FDS) (Parent-Clone)'),
    Platform('Nintendo GameBoy', 'nintendo-gb', 'gb', None, 4, '10', '9', '59',
        DAT_NOINTRO, 'Nintendo - Game Boy'),
    Platform('Nintendo GameBoy Advance', 'nintendo-gba', 'gba', None, 5, '12', '12', '91',
        DAT_NOINTRO, 'Nintendo - Game Boy Advance'),
    Platform('Nintendo GameBoy Color', 'nintendo-gbcolor', 'gbcolor', None, 41, '11', '10', '57',
        DAT_NOINTRO, 'Nintendo - Game Boy Color'),
    Platform('Nintendo GameCube', 'nintendo-gamecube', 'gamecube', None, 2, '14', '13', '99',
        DAT_REDUMP, 'Nintendo - GameCube - Datfile'),
    Platform('Nintendo NES', 'nintendo-nes', 'nes', None, 7, '22', '3', '41',
        DAT_NOINTRO, 'Nintendo - Nintendo Entertainment System'),
    # No-Intro New Nintendo 3DS DAT files:
    # *) Nintendo - New Nintendo 3DS (Decrypted) (20190402-125456)
    # *) Nintendo - New Nintendo 3DS (Digital) (20181009-100544)
    # *) Nintendo - New Nintendo 3DS (Digital) (Parent-Clone) (20181009-100544)
    # *) Nintendo - New Nintendo 3DS (Encrypted) (20190402-125456)
    # *) Nintendo - New Nintendo 3DS (Encrypted) (Parent-Clone) (Parent-Clone) (20190402-125456)
    Platform('Nintendo New Nintendo 3DS', 'nintendo-new3ds', 'new3ds', None, None, None, None, None,
        DAT_NOINTRO, 'Nintendo - New Nintendo 3DS (Encrypted) (Parent-Clone)'),
    # Pokemon Mini not found in GameFAQs.
    Platform('Nintendo Pokemon Mini', 'nintendo-pokemini', 'pokemini', None, 4957, '152', '211', None,
        DAT_NOINTRO, 'Nintendo - Pokemon Mini'),
    Platform('Nintendo Satellaview', 'nintendo-satellaview', 'satellaview', None, None, None, '107', None,
        DAT_NOINTRO, 'Nintendo - Satellaview'),
    Platform('Nintendo SNES', 'nintendo-snes', 'snes', None, 6, '15', '4', '63',
        DAT_NOINTRO, 'Nintendo - Super Nintendo Entertainment System (Combined) (Parent-Clone)'),
    Platform('Nintendo Sufami Turbo', 'nintendo-sufami', 'sufami', None, None, None, '108', None,
        DAT_NOINTRO, 'Nintendo - Sufami Turbo'),
    Platform('Nintendo Switch', 'nintendo-switch', 'switch', None, 4971, '203', None, '124', DAT_NONE),
    Platform('Nintendo Virtual Boy', 'nintendo-vb', 'vb', None, 4918, '38', '11', '83',
        DAT_NOINTRO, 'Nintendo - Virtual Boy'),
    # No-Intro has some DATs for Wii and Wii U with tags Digital, CDN and WAD.
    Platform('Nintendo Wii', 'nintendo-wii', 'wii', None, 9, '82', '16', '114', DAT_NONE),
    Platform('Nintendo Wii U', 'nintendo-wiiu', 'wiiu', None, 38, '132', '18', '118', DAT_NONE),

    Platform('Ouya Ouya', 'console-ouya', 'ouya', None, 4921, '144', None, None,
        DAT_NOINTRO, 'Ouya - Ouya'),

    # --- Philips ---
    # The Philips Videopac G7000 is the European name of the Magnavox Odyssey2.
    Platform('Philips Videopac G7000', 'console-g7000', 'g7000', 'odyssey2'),
    # Alias of g7000 in ScreenScraper. Not found in GameFAQs.
    Platform('Philips Videopac Plus G7400', 'console-g7400', 'g7400', None, None, '128', '104', None,
        DAT_NOINTRO, 'Philips - Videopac+'),

    # --- RCA ---
    Platform('RCA Studio II', 'console-studio2', 'studio2', None, 4967, '113', None, None,
        DAT_NOINTRO, 'RCA - Studio II'),

    # --- ScummVM ---
    Platform('ScummVM', 'games-scummvm', 'scummvm', None, None, None, '123', None, DAT_NONE),

    # --- Sega ---
    Platform('Sega 32X', 'sega-32x', '32x', None, 33, '21', '19', '74',
        DAT_NOINTRO, 'Sega - 32X'),
    # The Advanced Pico Beena is an upgraded Sega PICO.
    Platform('Sega Beena', 'sega-beena', 'beena', None, None, None, None, None,
        DAT_NOINTRO, 'Sega - Beena'),
    Platform('Sega Dreamcast', 'sega-dreamcast', 'dreamcast', None, 16, '8', '23', '67',
        DAT_REDUMP, 'Sega - Dreamcast - Datfile'),
    Platform('Sega Game Gear', 'sega-gamegear', 'gamegear', None, 20, '25', '21', '62',
        DAT_NOINTRO, 'Sega - Game Gear'),
    Platform('Sega Genesis', 'sega-genesis', 'genesis', 'megadrive'),
    Platform('Sega Master System', 'sega-sms', 'sms', None, 35, '26', '2', '49',
        DAT_NOINTRO, 'Sega - Master System - Mark III'),
    Platform('Sega Mega Drive', 'sega-megadrive', 'megadrive', None, 36, '16', '1', '54',
        DAT_NOINTRO, 'Sega - Mega Drive - Genesis'),
    Platform('Sega MegaCD', 'sega-megacd', 'megacd', None, 21, '20', '20', '65',
        DAT_REDUMP, 'Sega - Mega CD & Sega CD - Datfile'),
    Platform('Sega PICO', 'sega-pico', 'pico', None, 4958, '103', None, None,
        DAT_NOINTRO, 'Sega - PICO'),
    Platform('Sega Saturn', 'sega-saturn', 'saturn', None, 17, '23', '22', '76',
        DAT_REDUMP, 'Sega - Saturn - Datfile'),
    # The SG-1000 was released in several forms, including the SC-3000 computer and
    # the redesigned SG-1000 II.
    Platform('Sega SC-3000', 'sega-sc3000', 'sc3000', 'sg1000'),
    Platform('Sega SegaCD', 'sega-segacd', 'segacd', 'megacd'),
    Platform('Sega SG-1000', 'sega-sg1000', 'sg1000', None, 4949, '114', '109', '43',
        DAT_NOINTRO, 'Sega - SG-1000'),

    # --- Sharp ---
    Platform('Sharp X68000', 'computer-x68k', 'x68k', None, 4931, '106', '79', '52', DAT_NONE),

    # --- Sinclair ---
    Platform('Sinclair ZX Spectrum', 'computer-spectrum', 'spectrum', None, 4913, '41', '76', '35', DAT_NONE),
    Platform('Sinclair ZX Spectrum Plus 3', 'computer-spectrump3', 'spectrump3', None, None, None, None, None,
        DAT_NOINTRO, 'Sinclair - ZX Spectrum +3'),
    # I think the ZX80 and the ZX81 are incompatible computers.
    Platform('Sinclair ZX80', 'computer-zx80', 'zx80', None, None, '118', None, None, DAT_LIBRETRO),
    Platform('Sinclair ZX81', 'computer-zx81', 'zx81', None, None, '119', '77', None, DAT_LIBRETRO),

    # --- SNK ---
    # MobyGames has a platform Neo Geo = '36'
    # ScreenScraper has a platform Neo Geo AES = '142'
    # GameFAQs has a platform NeoGeo = '64'
    Platform('SNK Neo-Geo AES', 'snk-aes', 'aes', 'mame'),
    Platform('SNK Neo-Geo CD', 'snk-neocd', 'neocd', None, 4956, '54', '70', '68',
        DAT_REDUMP, 'SNK - Neo Geo CD - Datfile'),
    # ScreenScraper has a platform for Neo Geo MVS = '68'
    Platform('SNK Neo-Geo MVS', 'snk-mvs', 'mvs', 'mame'),
    Platform('SNK Neo-Geo Pocket', 'snk-ngp', 'ngp', None, 4922, '52', '25', None,
        DAT_NOINTRO, 'SNK - Neo Geo Pocket'),
    Platform('SNK Neo-Geo Pocket Color', 'snk-ngpcolor', 'ngpcolor', None, 4923, '53', '82', '89',
        DAT_NOINTRO, 'SNK - Neo Geo Pocket Color'),

    # --- SONY ---
    Platform('Sony PlayStation', 'sony-psx', 'psx', None, 10, '6', '57', '78',
        DAT_REDUMP, 'Sony - PlayStation - Datfile'),
    Platform('Sony PlayStation 2', 'sony-ps2', 'ps2', None, 11, '7', '58', '94',
        DAT_REDUMP, 'Sony - PlayStation 2 - Datfile'),
    Platform('Sony PlayStation 3', 'sony-ps3', 'ps3', None, 12, '81', '59', '113', DAT_NONE),
    Platform('Sony PlayStation 4', 'sony-ps4', 'ps4', None, 4919, '141', None, '120', DAT_NONE),
    # No-Intro has PSP DATs:
    # *) Sony - PlayStation Portable (20191005-125849)
    # *) Sony - PlayStation Portable (Parent-Clone) (20191005-125849)
    # *) Sony - PlayStation Portable (PSN) (Decrypted) (20180929-050404)
    # *) Sony - PlayStation Portable (PSN) (Encrypted) (20190111-145824)
    # *) Sony - PlayStation Portable (PSN) (Encrypted) (Parent-Clone) (20190111-145824)
    # *) Sony - PlayStation Portable (PSX2PSP) (20130318-035538)
    # *) Sony - PlayStation Portable (PSX2PSP) (Parent-Clone) (20130318-035538)
    # *) Sony - PlayStation Portable (UMD Music) (20180911-072923)
    # *) Sony - PlayStation Portable (UMD Music) (Parent-Clone) (20180911-072923)
    # *) Sony - PlayStation Portable (UMD Video) (20191023-221355)
    # *) Sony - PlayStation Portable (UMD Video) (Parent-Clone) (20191023-221355)
    #
    # Should the Redump or No-Intro DAT used for PSP?
    Platform('Sony PlayStation Portable', 'sony-psp', 'psp', None, 13, '46', '61', '109',
        DAT_REDUMP, 'Sony - PlayStation Portable - Datfile'),
    # No-Intro has PS Vita DATs.
    Platform('Sony PlayStation Vita', 'sony-psvita', 'psvita', None, 39, '105', '62', '117', DAT_NONE),

    Platform('Tiger Game.com', 'console-tigergame', 'tigergame', None, 4940, '50', '121', None,
        DAT_NOINTRO, 'Tiger - Game.com'),
    Platform('VTech CreatiVision', 'console-creativision', 'creativision', None, None, '212', None, None,
        DAT_NOINTRO, 'VTech - CreatiVision'),
    Platform('VTech V.Flash', 'console-vflash', 'vflash', None, None, '189', None, None,
        DAT_REDUMP, 'VTech - V.Flash & V.Smile Pro - Datfile'),
    Platform('VTech V.Smile', 'console-vsmile', 'vsmile', None, None, '42', '120', None,
        DAT_NOINTRO, 'VTech - V.Smile'),
    Platform('VTech V.Smile Pro', 'console-vsmilepro', 'vsmilepro', 'vflash'),
    Platform('Watara Supervision', 'console-supervision', 'supervision', None, 4959, '109', '207', None,
        DAT_NOINTRO, 'Watara - Supervision'),
    Platform('Zeebo Zeebo', 'console-zeebo', 'zeebo', None, None, '88', None, None,
        DAT_NOINTRO, 'Zeebo - Zeebo'),

    # --- Unknown ---
    Platform(PLATFORM_UNKNOWN_LONG, PLATFORM_UNKNOWN_SHORT, PLATFORM_UNKNOWN_COMPACT),
]

# --- Add category to platform objects ---
# The category is the first part of the short name.
for p_obj in AEL_platforms:
    p_obj.category = p_obj.short_name.split('-')[0]

# Dictionaries for fast access to the platform information.
# Also, platform long name list for select() dialogs.
platform_long_to_index_dic = {}
platform_short_to_index_dic = {}
platform_compact_to_index_dic = {}
AEL_platform_list = []
for index, p_obj in enumerate(AEL_platforms):
    platform_long_to_index_dic[p_obj.long_name] = index
    platform_short_to_index_dic[p_obj.short_name] = index
    platform_compact_to_index_dic[p_obj.compact_name] = index
    AEL_platform_list.append(p_obj.long_name)

# Returns the platform numerical index from the platform name. If the platform name is not
# found then returns the index of the 'Unknown' platform.
# platform may be a long_name, short_name or compact_name, all platform names are searched
# in an efficient way.
def get_AEL_platform_index(platform) -> int:
    try:
        return platform_long_to_index_dic[platform]
    except KeyError:
        pass
    try:
        return platform_short_to_index_dic[platform]
    except KeyError:
        pass
    try:
        return platform_compact_to_index_dic[platform]
    except KeyError:
        pass

    return platform_long_to_index_dic[PLATFORM_UNKNOWN_LONG]

# NOTE must take into account platform aliases.
# 0 means any platform in TGDB and must be returned when there is no platform matching.
def AEL_platform_to_TheGamesDB(platform_long_name) -> int:
    if platform_long_name in platform_long_to_index_dic:
        pobj = AEL_platforms[platform_long_to_index_dic[platform_long_name]]
    else:
        # Platform not found.
        return DEFAULT_PLAT_TGDB
    scraper_platform = pobj.TGDB_plat
    # Check if platform is an alias.
    # If alias does not have specific platform return platform of parent.
    if pobj.aliasof is not None and scraper_platform is None:
        parent_idx = platform_compact_to_index_dic[pobj.aliasof]
        parent_long_name = AEL_platforms[parent_idx].long_name
        return AEL_platform_to_TheGamesDB(parent_long_name)

    # If platform is None then return default platform
    return DEFAULT_PLAT_TGDB if scraper_platform is None else scraper_platform

# * MobyGames API cannot be used withouth a valid platform.
# * If '0' is used as the Unknown platform then MobyGames returns an HTTP error
#    "HTTP Error 422: UNPROCESSABLE ENTITY"
# * If '' is used as the Unknwon platform then MobyGames returns and HTTP error
#   "HTTP Error 400: BAD REQUEST"
# * The solution is to use '0' as the unknwon platform. AEL will detect this and
#   will remove the '&platform={}' parameter from the search URL.
def AEL_platform_to_MobyGames(platform_long_name):
    if platform_long_name in platform_long_to_index_dic:
        pobj = AEL_platforms[platform_long_to_index_dic[platform_long_name]]
    else:
        return DEFAULT_PLAT_MOBYGAMES
    scraper_platform = pobj.MG_plat
    if pobj.aliasof is not None and scraper_platform is None:
        parent_idx = platform_compact_to_index_dic[pobj.aliasof]
        parent_long_name = AEL_platforms[parent_idx].long_name
        return AEL_platform_to_MobyGames(parent_long_name)

    return DEFAULT_PLAT_MOBYGAMES if scraper_platform is None else scraper_platform

def AEL_platform_to_ScreenScraper(platform_long_name):
    if platform_long_name in platform_long_to_index_dic:
        pobj = AEL_platforms[platform_long_to_index_dic[platform_long_name]]
    else:
        return DEFAULT_PLAT_SCREENSCRAPER
    scraper_platform = pobj.SS_plat
    if pobj.aliasof is not None and scraper_platform is None:
        parent_idx = platform_compact_to_index_dic[pobj.aliasof]
        parent_long_name = AEL_platforms[parent_idx].long_name
        return AEL_platform_to_ScreenScraper(parent_long_name)

    return DEFAULT_PLAT_SCREENSCRAPER if scraper_platform is None else scraper_platform

# Platform '0' means all platforms in GameFAQs.
def AEL_platform_to_GameFAQs(platform_long_name):
    if platform_long_name in platform_long_to_index_dic:
        pobj = AEL_platforms[platform_long_to_index_dic[platform_long_name]]
    else:
        return DEFAULT_PLAT_GAMEFAQS
    scraper_platform = pobj.GF_plat
    if pobj.aliasof is not None and scraper_platform is None:
        parent_idx = platform_compact_to_index_dic[pobj.aliasof]
        parent_long_name = AEL_platforms[parent_idx].long_name
        return AEL_platform_to_GameFAQs(parent_long_name)

    return DEFAULT_PLAT_GAMEFAQS if scraper_platform is None else scraper_platform

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
    for application, arguments in applications.items():
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
    for application, extensions in applications.items():
        if app.lower().find(application) >= 0:
            return extensions

    return ''
