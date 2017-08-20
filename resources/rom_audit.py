# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher
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
import xml.etree.ElementTree as ET

# --- Modules/packages in this plugin ---
from utils import *
from utils_kodi import *

# -------------------------------------------------------------------------------------------------
# Data structures
# -------------------------------------------------------------------------------------------------
# DTD "http://www.logiqx.com/Dats/datafile.dtd"
def audit_new_rom_logiqx(): 
    rom = {
        'name'         : '',
        'cloneof'      : '',
        'year'         : '',
        'manufacturer' : ''
    }

    return rom

# HyperList doesn't include Plot
def audit_new_rom_HyperList(): 
    rom = {
        'name'         : '',
        'description'  : '',
        'cloneof'      : '',
        'crc'          : '',
        'manufacturer' : '',
        'year'         : '',
        'genre'        : '',
        'rating'       : '',
        'enabled'      : ''
    }

    return rom

def audit_new_rom_GameDB():
    rom = {
        'name'         : '',
        'description'  : '',
        'year'         : '',
        'rating'       : '',
        'manufacturer' : '',
        'genre'        : '',
        'player'       : '',
        'story'        : ''
    }

    return rom

# Manufacturer is Publisher
def audit_new_rom_AEL_Offline(): 
    rom = {
        'name'         : '',
        'description'  : '',
        'cloneof'      : '',
        'source'       : '',
        'status'       : '',
        'year'         : '',
        'genre'        : '',
        'manufacturer' : '',
        'nplayers'     : '',
        'rating'       : '',
        'plot'         : ''
    }

    return rom

def audit_new_LB_game():
    g = {
        'Name'              : '',
        'ReleaseYear'       : '',
        'Overview'          : '',
        'MaxPlayers'        : '',
        'Cooperative'       : '',
        'VideoURL'          : '',
        'DatabaseID'        : '',
        'CommunityRating'   : '',
        'Platform'          : '',
        'Genres'            : '',
        'Publisher'         : '',
        'Developer'         : '',
        'ReleaseDate'       : '',
        'ESRB'              : '',
        'WikipediaURL'      : '',
        'DOS'               : '',
        'StartupFile'       : '',
        'StartupMD5'        : '',
        'SetupFile'         : '',
        'SetupMD5'          : '',
        'StartupParameters' : '',
    }

    return g

def audit_new_LB_platform():
    g = {
        'Name'           : '',
        'Emulated'       : '',
        'ReleaseDate'    : '',
        'Developer'      : '',
        'Manufacturer'   : '',
        'Cpu'            : '',
        'Memory'         : '',
        'Graphics'       : '',
        'Sound'          : '',
        'Display'        : '',
        'Media'          : '',
        'MaxControllers' : '',
        'Notes'          : '',
        'Category'       : '',
        'UseMameFiles'   : '',
    }

    return g

def audit_new_LB_gameImage():
    g = {
        'DatabaseID' : '',
        'FileName'   : '',
        'Type'       : '',
        'CRC32'      : '',
        'Region'     : '',
    }

    return g

def audit_load_LB_metadata_XML(filename_FN, games_dic, platforms_dic, gameimages_dic):
    if not filename_FN.exists():
        log_error("Cannot load file '{0}'".format(xml_file))
        return

    # --- Parse using cElementTree ---
    log_verb('audit_load_LB_metadata_XML() Loading "{0}"'.format(filename_FN.getPath()))
    try:
        xml_tree = ET.parse(filename_FN.getPath())
    except ET.ParseError, e:
        log_error('(ParseError) Exception parsing XML categories.xml')
        log_error('(ParseError) {0}'.format(str(e)))
        return
    xml_root = xml_tree.getroot()
    for xml_element in xml_root:
        if xml_element.tag == 'Game':
            game = audit_new_LB_game()
            for xml_child in xml_element:
                xml_tag  = xml_child.tag
                xml_text = xml_child.text if xml_child.text is not None else ''
                if xml_tag not in game:
                    log_info('Unknown <Game> child tag <{0}>'.format(xml_tag))
                    return
                game[xml_tag] = text_unescape_XML(xml_text)
            games_dic[game['Name']] = game
        elif xml_element.tag == 'Platform':
            platform = audit_new_LB_platform()
            for xml_child in xml_element:
                xml_tag  = xml_child.tag
                xml_text = xml_child.text if xml_child.text is not None else ''
                if xml_tag not in platform:
                    log_info('Unknown <Platform> child tag <{0}>'.format(xml_tag))
                    return
                platform[xml_tag] = text_unescape_XML(xml_text)
            platforms_dic[platform['Name']] = platform
        elif xml_element.tag == 'PlatformAlternateName':
            pass
        elif xml_element.tag == 'Emulator':
            pass
        elif xml_element.tag == 'EmulatorPlatform':
            pass
        elif xml_element.tag == 'GameAlternateName':
            pass
        elif xml_element.tag == 'GameImage':
            game_image = audit_new_LB_gameImage()
            for xml_child in xml_element:
                xml_tag  = xml_child.tag
                xml_text = xml_child.text if xml_child.text is not None else ''
                if xml_tag not in game_image:
                    log_info('Unknown <GameImage> child tag <{0}>'.format(xml_tag))
                    return
                game_image[xml_tag] = text_unescape_XML(xml_text)
            gameimages_dic[game_image['FileName']] = game_image
        else:
            log_info('Unknwon main tag <{0}>'.format(xml_element.tag))
            return
    log_verb('audit_load_LB_metadata_XML() Loaded {0} games ({1} bytes)'.format(len(games_dic), sys.getsizeof(games_dic)))
    log_verb('audit_load_LB_metadata_XML() Loaded {0} platforms'.format(len(platforms_dic)))
    log_verb('audit_load_LB_metadata_XML() Loaded {0} game images'.format(len(gameimages_dic)))

# -------------------------------------------------------------------------------------------------
# Functions
# -------------------------------------------------------------------------------------------------
#
# Loads offline scraper information XML file.
#
def audit_load_OfflineScraper_XML(xml_file):
    __debug_xml_parser = 0
    games = {}

    # --- Check that file exists ---
    if not os.path.isfile(xml_file):
        log_error("Cannot load file '{0}'".format(xml_file))
        return games

    # --- Parse using cElementTree ---
    log_verb('audit_load_OfflineScraper_XML() Loading "{0}"'.format(xml_file))
    try:
        xml_tree = ET.parse(xml_file)
    except ET.ParseError, e:
        log_error('(ParseError) Exception parsing XML categories.xml')
        log_error('(ParseError) {0}'.format(str(e)))
        return games
    xml_root = xml_tree.getroot()
    for game_element in xml_root:
        if __debug_xml_parser:
            log_debug('=== Root child tag "{0}" ==='.format(game_element.tag))

        if game_element.tag == 'game':
            # Default values
            game = audit_new_rom_logiqx()

            # ROM name is an attribute of <game>
            game['name'] = game_element.attrib['name']
            if __debug_xml_parser: log_debug('Game name = "{0}"'.format(game['name']))

            # Parse child tags of category
            for game_child in game_element:
                # By default read strings
                xml_text = game_child.text if game_child.text is not None else ''
                xml_text = text_unescape_XML(xml_text)
                xml_tag  = game_child.tag
                if __debug_xml_parser: log_debug('Tag "{0}" --> "{1}"'.format(xml_tag, xml_text))
                game[xml_tag] = xml_text
            key = game['name']
            games[key] = game

    return games

#
# Loads a No-Intro Parent-Clone XML DAT file. Creates a data structure like
# roms_nointro = {
#   'rom_name_A' : { 'name' : 'rom_name_A', 'cloneof' : '' | 'rom_name_parent},
#   'rom_name_B' : { 'name' : 'rom_name_B', 'cloneof' : '' | 'rom_name_parent},
# }
#
def audit_load_NoIntro_XML_file(xml_FN):
    nointro_roms = {}

    # --- If file does not exist return empty dictionary ---
    if not xml_FN.exists():
        log_error('Does not exists "{0}"'.format(xml_FN.getPath()))
        return nointro_roms

    # --- Parse using cElementTree ---
    log_verb('Loading XML "{0}"'.format(xml_FN.getOriginalPath()))
    try:
        xml_tree = ET.parse(xml_FN.getPath())
    except ET.ParseError as e:
        log_error('(ParseError) Exception parsing XML categories.xml')
        log_error('(ParseError) {0}'.format(str(e)))
        return nointro_roms
    except IOError as e:
        log_error('(IOError) {0}'.format(str(e)))
        return nointro_roms
    xml_root = xml_tree.getroot()
    for root_element in xml_root:
        if root_element.tag == 'game':
            nointro_rom = audit_new_rom_logiqx()
            rom_name = root_element.attrib['name']
            nointro_rom['name'] = rom_name
            if 'cloneof' in root_element.attrib:
                nointro_rom['cloneof'] = root_element.attrib['cloneof']
            nointro_roms[rom_name] = nointro_rom

    return nointro_roms

def audit_load_GameDB_XML(xml_FN):
    __debug_xml_parser = 0
    games = {}

    # --- Check that file exists and load ---
    if not xml_FN.exists():
        log_error('Does not exists "{0}"'.format(xml_FN.getPath()))
        return games
    log_verb('Loading XML "{0}"'.format(xml_FN.getPath()))
    try:
        xml_tree = ET.parse(xml_FN.getPath())
    except ET.ParseError as e:
        log_error('(ParseError) Exception parsing XML categories.xml')
        log_error('(ParseError) {0}'.format(str(e)))
        return games
    xml_root = xml_tree.getroot()
    for game_element in xml_root:
        if __debug_xml_parser:
            log_debug('=== Root child tag "{0}" ==='.format(game_element.tag))

        if game_element.tag == 'game':
            # Default values
            game = audit_new_rom_GameDB()

            # ROM name is an attribute of <game>
            game['name'] = game_element.attrib['name']
            if __debug_xml_parser: log_debug('Game name = "{0}"'.format(game['name']))

            # Parse child tags of category
            for game_child in game_element:
                # By default read strings
                xml_text = game_child.text if game_child.text is not None else ''
                xml_text = text_unescape_XML(xml_text)
                xml_tag  = game_child.tag
                if __debug_xml_parser: log_debug('Tag "{0}" --> "{1}"'.format(xml_tag, xml_text))
                game[xml_tag] = xml_text
            key = game['name']
            games[key] = game

    return games

def audit_load_Tempest_INI(file_FN):
    games = {}
    # Read_status FSM values
    #   0 -> Looking for '[game_name]' tag
    #   1 -> Reading fields fiel_name=field_value
    read_status = 0
    __debug_INI_parser = False

    # --- Check that file exists ---
    if not file_FN.exists():
        log_error('Does not exists "{0}"'.format(file_FN.getPath()))
        return games
    log_verb('Loading XML "{0}"'.format(file_FN.getPath()))
    try:
        f = open(file_FN.getPath(), 'rt')
    except IOError:
        log_info('audit_load_Tempest_INI() IOError opening "{0}"'.format(filename))
        return {}
    for file_line in f:
        stripped_line = file_line.strip().decode(errors = 'replace')
        if __debug_INI_parser: print('Line "' + stripped_line + '"')
        if read_status == 0:
            m = re.search(r'\[([^\]]+)\]', stripped_line)
            if m:
                game = audit_new_rom_GameDB()
                game_key     = m.group(1)
                game['name'] = m.group(1)
                if __debug_INI_parser: print('Found game [{0}]'.format(game['name']))
                read_status = 1
        elif read_status == 1:
            line_list = stripped_line.split("=")
            if len(line_list) == 1:
                read_status = 0
                games[game_key] = game
                if __debug_INI_parser: print('Added game key "{0}"'.format(game_key))
            else:
                if __debug_INI_parser: print('Line list -> ' + str(line_list))
                field_name = line_list[0]
                field_value = line_list[1]
                if   field_name == 'Publisher':   game['manufacturer'] = field_value
                elif field_name == 'Developer':   game['dev'] = field_value
                elif field_name == 'Released':    game['year'] = field_value
                elif field_name == 'Systems':     pass
                elif field_name == 'Genre':       game['genre'] = field_value
                elif field_name == 'Perspective': pass
                elif field_name == 'Score':       game['score'] = field_value
                elif field_name == 'Controls':    pass
                elif field_name == 'Players':     game['player'] = field_value
                elif field_name == 'Esrb':        game['rating'] = field_value
                elif field_name == 'Url':         pass
                elif field_name == 'Description': game['story'] = field_value
                elif field_name == 'Goodname':    pass
                elif field_name == 'NoIntro':     pass
                elif field_name == 'Tosec':       pass
                else:
                    raise NameError
        else:
            raise CriticalError('Unknown read_status FSM value')
    f.close()
    log_info('audit_load_Tempest_INI() Number of games {0}'.format(len(games)))

    return games

def audit_load_HyperList_XML(xml_FN):
    __debug_xml_parser = 0
    games = {}

    # --- Check that file exists and load ---
    if not xml_FN.exists():
        log_error('Does not exists "{0}"'.format(xml_FN.getPath()))
        return games
    log_verb('Loading XML "{0}"'.format(xml_FN.getPath()))
    try:
        xml_tree = ET.parse(xml_FN.getPath())
    except ET.ParseError as e:
        log_error('(ParseError) Exception parsing XML categories.xml')
        log_error('(ParseError) {0}'.format(str(e)))
        return games
    except IOError as e:
        log_error('(IOError) {0}'.format(str(e)))
        return games
    xml_root = xml_tree.getroot()
    for game_element in xml_root:
        if __debug_xml_parser:
            log_debug('=== Root child tag "{0}" ==='.format(game_element.tag))

        if game_element.tag == 'game':
            # Default values
            game = audit_new_rom_HyperList()

            # ROM name is an attribute of <game>
            game['name'] = game_element.attrib['name']
            if __debug_xml_parser: log_debug('Game name = "{0}"'.format(game['name']))

            # Parse child tags of category
            for game_child in game_element:
                # By default read strings
                xml_text = game_child.text if game_child.text is not None else ''
                xml_text = text_unescape_XML(xml_text)
                xml_tag  = game_child.tag
                if __debug_xml_parser: log_debug('Tag "{0}" --> "{1}"'.format(xml_tag, xml_text))
                game[xml_tag] = xml_text
            key = game['name']
            games[key] = game

    return games

def audit_make_NoIntro_PClone_dic(nointro_dic):
    log_info('Making PClone dictionary ...')
    main_pclone_dic = {}
    for machine_name in nointro_dic:
        machine = nointro_dic[machine_name]
        if machine['cloneof']:
            parent_name = machine['cloneof']
            # >> If parent already in main_pclone_dic then add clone to parent list.
            # >> If parent not there, then add parent first and then add clone.
            if parent_name not in main_pclone_dic: main_pclone_dic[parent_name] = []
            main_pclone_dic[parent_name].append(machine_name)
        else:
            # >> Machine is a parent. Add to main_pclone_dic if not already there.
            if machine_name not in main_pclone_dic: main_pclone_dic[machine_name] = []

    return main_pclone_dic

def audit_make_NoIntro_Parents_dic(nointro_dic):
    log_info('Making Parents dictionary ...')
    main_pclone_dic = {}
    main_clone_to_parent_dic = {}
    for machine_name in nointro_dic:
        machine = nointro_dic[machine_name]
        if machine['cloneof']:
            parent_name = machine['cloneof']
            main_clone_to_parent_dic[machine_name] = parent_name            

    return main_clone_to_parent_dic

# -------------------------------------------------------------------------------------------------
# Retroarch System directory BIOS audit
# -------------------------------------------------------------------------------------------------
# See https://github.com/libretro/libretro-database/blob/master/dat/BIOS.dat
# See https://github.com/libretro/libretro-database/blob/master/dat/BIOS%20-%20Non-Merged.dat
Libretro_BIOS_list = [
    # --- Atari 5200 ---
    {'filename' : '5200.rom', size : 2048, 'md5': '281f20ea4320404ec820fb7ec0693b38', 'mandatory' : True },

    # --- Atari 7800 ---
    {'filename' : '7800 BIOS (E).rom', size : 16384, 'md5': '397bb566584be7b9764e7a68974c4263', 'mandatory' : True },
    {'filename' : '7800 BIOS (U).rom', size : 4096, 'md5': '0763f1ffb006ddbe32e52d497ee848ae', 'mandatory' : True },

    # --- Sony PlayStation ---
    {'filename' : 'scph5500.bin', size : 524288, 'md5': '8dd7d5296a650fac7319bce665a6a53c', 'mandatory' : True },
    {'filename' : 'scph5501.bin', size : 524288, 'md5': '490f666e1afb15b7362b406ed1cea246', 'mandatory' : True },
    {'filename' : 'scph5502.bin', size : 524288, 'md5': '32736f17079d0b2b7024407c39bd3050', 'mandatory' : True },

    # --- Sony PlayStation Portable ---
    {'filename' : 'ppge_atlas.zim', size : 784968, 'md5': 'a93fc411c1ce7d001a2a812643c70085', 'mandatory' : True },
]
