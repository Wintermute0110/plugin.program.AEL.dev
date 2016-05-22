# -*- coding: utf-8 -*-
# Advanced Emulator Launcher filesystem I/O functions
#

# Copyright (c) 2016 Wintermute0110 <wintermute0110@gmail.com>
# Portions (c) 2010-2015 Angelscry and others
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# --- XML stuff ---
# ~~~ cElementTree sometimes fails to parse XML in Kodi's Python interpreter... I don't know why
# import xml.etree.cElementTree as ET

# ~~~ Using ElementTree seems to solve the problem
import xml.etree.ElementTree as ET

# --- AEL packages ---
from utils import *
try:
    from utils_kodi import *
except:
    from utils_kodi_standalone import *
 
# -----------------------------------------------------------------------------
# Data model used in the plugin
# -----------------------------------------------------------------------------
# These three functions create a new data structure for the given object
# and (very importantly) fill the correct default values). These must match
# what is written/read from/to the XML files.
#
# Tag name in the XML is the same as in the data dictionary.
def fs_new_category():
    category = {'id' : '', 'name' : '', 'thumb' : '', 'fanart' : '', 'genre' : '', 
                'description' : '', 'finished' : False}

    return category

def fs_new_launcher():
    launcher = {'id' : '', 'name' : '', 'categoryID' : '', 'platform' : '', 
                'application' : '', 'args' : '', 'rompath' : '', 'romext' : '', 
                'thumbpath' : '', 'fanartpath' : '', 'custompath' : '', 'trailerpath' : '', 
                'thumb' : '', 'fanart' : '', 'genre' : '', 'year' : '', 'studio' : '', 'plot' : '',  
                'lnk' : False, 'finished': False, 'minimize' : False,
                'roms_xml_file' : '', 'nointro_xml_file' : '' }

    return launcher

# Mandatory variables in XML:
# id              string MD5 hash
# name            string ROM name
# finished        bool ['True', 'False'] default 'False'
# nointro_status  string ['Have', 'Miss', 'Unknown', 'None'] default 'None'
def fs_new_rom():
    rom = {'id' : '', 'name' : '', 'filename' : '',
           'thumb' : '', 'fanart' : '', 'trailer' : '', 'custom' : '', 
           'genre' : '', 'year' : '', 'studio' : '', 'plot' : '', 
           'altapp' : '', 'altarg' : '', 
           'finished' : False, 'nointro_status' : 'None' }

    return rom

# fav_status = ['OK', 'Unlinked', 'Broken'] default 'OK'
# 'OK'       filename exists and launcher exists and ROM id exists
# 'Unlinked' filename exists but launcher or ROM ID in launcher does not
#            Note that if the launcher does not exists implies ROM ID does not exist
# 'Broken'   filename does not exist. ROM is unplayable
def fs_new_favourite_rom():
    rom = {'id' : '', 'name' : '', 'filename' : '',
           'thumb' : '', 'fanart' : '', 'trailer' : '', 'custom' : '', 
           'genre' : '', 'year' : '', 'studio' : '', 'plot' : '', 
           'altapp' : '', 'altarg' : '',
           'finished' : False, 'nointro_status' : 'None',
           'launcherID' : '', 'platform' : '', 
           'application' : '', 'args' : '', 'rompath' : '', 'romext' : '',
           'fav_status' : 'OK' }

    return rom

# -----------------------------------------------------------------------------
# Filesystem very low-level utilities
# -----------------------------------------------------------------------------
#
# Writes a XML text tag line, indented 2 spaces (root sub-child)
#
def XML_text(tag_name, tag_text):
    tag_text = text_escape_XML(tag_text)
    line = '  <{}>{}</{}>\n'.format(tag_name, tag_text, tag_name)
    
    return line

#
# See https://docs.python.org/2/library/sys.html#sys.getfilesystemencoding
#
def get_fs_encoding():
    try:
        return sys.getfilesystemencoding()
    except UnicodeEncodeError, UnicodeDecodeError:
        return "utf-8"

# -----------------------------------------------------------------------------
# Disk IO functions
# -----------------------------------------------------------------------------
#
# Write to disk categories.xml
#
def fs_write_catfile(categories_file, categories, launchers):
    log_verb('fs_write_catfile() Writing {0}'.format(categories_file))

    # Original Angelscry method for generating the XML was to grow a string, like this
    # xml_content = 'test'
    # xml_content += 'more test'
    # However, this method is very slow because string has to be reallocated every time is grown.
    # It is much faster to create a list of string and them join them!
    # See https://waymoot.org/home/python_string/
    try:
        str_list = []
        str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        str_list.append('<advanced_emulator_launcher version="1.0">\n')

        # --- Create Categories XML list ---
        for categoryID in sorted(categories, key = lambda x : categories[x]["name"]):
            category = categories[categoryID]
            # Data which is not string must be converted to string
            str_list.append('<category>\n')
            str_list.append(XML_text('id', categoryID))
            str_list.append(XML_text('name', category['name']))
            str_list.append(XML_text('thumb', category['thumb']))
            str_list.append(XML_text('fanart', category['fanart']))
            str_list.append(XML_text('genre', category['genre']))
            str_list.append(XML_text('description', category['description']))
            str_list.append(XML_text('finished', str(category['finished'])))
            str_list.append('</category>\n')

        # --- Write launchers ---
        for launcherID in sorted(launchers, key = lambda x : launchers[x]["name"]):
            # Data which is not string must be converted to string
            launcher = launchers[launcherID]
            str_list.append('<launcher>\n')
            str_list.append(XML_text('id', launcherID))
            str_list.append(XML_text('name', launcher['name']))
            str_list.append(XML_text('categoryID', launcher['categoryID']))
            str_list.append(XML_text('platform', launcher['platform']))
            str_list.append(XML_text('application', launcher['application']))
            str_list.append(XML_text('args', launcher['args']))
            str_list.append(XML_text('rompath', launcher['rompath']))
            str_list.append(XML_text('romext', launcher['romext']))
            str_list.append(XML_text('thumbpath', launcher['thumbpath']))
            str_list.append(XML_text('fanartpath', launcher['fanartpath']))
            str_list.append(XML_text('custompath', launcher['custompath']))
            str_list.append(XML_text('trailerpath', launcher['trailerpath']))
            str_list.append(XML_text('thumb', launcher['thumb']))
            str_list.append(XML_text('fanart', launcher['fanart']))
            str_list.append(XML_text('genre', launcher['genre']))
            str_list.append(XML_text('year', launcher['year']))
            str_list.append(XML_text('studio', launcher['studio']))
            str_list.append(XML_text('plot', launcher['plot']))
            str_list.append(XML_text('lnk', str(launcher['lnk'])))
            str_list.append(XML_text('finished', str(launcher['finished'])))
            str_list.append(XML_text('minimize', str(launcher['minimize'])))
            str_list.append(XML_text('roms_xml_file', launcher['roms_xml_file']))
            str_list.append(XML_text('nointro_xml_file', launcher['nointro_xml_file']))
            str_list.append('</launcher>\n')
        # End of file
        str_list.append('</advanced_emulator_launcher>\n')

        # Join string and save categories.xml file
        full_string = ''.join(str_list)
        file_obj = open(categories_file, 'wt' )
        file_obj.write(full_string)
        file_obj.close()
    except OSError:
        log_error('Cannot write categories.xml file (OSError)')
        kodi_notify_warn('AEL Error', 'Cannot write categories.xml file (OSError)')
    except IOError:
        log_error('Cannot write categories.xml file (IOError)')
        kodi_notify_warn('AEL Error', 'Cannot write categories.xml file (IOError)')

#
# Loads categories.xml from disk and fills dictionary self.categories
#
def fs_load_catfile(categories_file):
    __debug_xml_parser = 0
    categories = {}
    launchers = {}

    # --- Parse using cElementTree ---
    log_verb('fs_load_catfile() Loading {0}'.format(categories_file))
    # If there are issues in the XML file ET.parse will fail
    try:
        xml_tree = ET.parse(categories_file)
    except:
        log_error('Error parsing XML categories.xml')
        kodi_dialog_OK('Advanced Emulator Launcher',
                       'Error reading categories.xml. Maybe XML file is corrupt or contains invalid characters.')
        return (categories, launchers)
    xml_root = xml_tree.getroot()
    for category_element in xml_root:
        if __debug_xml_parser: log_debug('Root child {0}'.format(category_element.tag))

        if category_element.tag == 'category':
            # Default values
            category = fs_new_category()

            # Parse child tags of category
            for category_child in category_element:
                # By default read strings
                xml_text = category_child.text if category_child.text is not None else ''
                xml_text = text_unescape_XML(xml_text)
                xml_tag  = category_child.tag
                if __debug_xml_parser: log_debug('{0} --> {1}'.format(xml_tag, xml_text))
                category[xml_tag] = xml_text

                # Now transform data depending on tag name
                if xml_tag == 'finished':
                    xml_bool = False if xml_text == 'False' else True
                    category[xml_tag] = xml_bool

            # Add category to categories dictionary
            categories[category['id']] = category

        elif category_element.tag == 'launcher':
            # Default values
            launcher = fs_new_launcher()

            # Parse child tags of category
            for category_child in category_element:
                # By default read strings
                xml_text = category_child.text if category_child.text is not None else ''
                xml_text = text_unescape_XML(xml_text)
                xml_tag  = category_child.tag
                if __debug_xml_parser: log_debug('{0} --> {1}'.format(xml_tag, xml_text))
                launcher[xml_tag] = xml_text

                # Now transform data depending on tag name
                if xml_tag == 'lnk' or xml_tag == 'finished' or xml_tag == 'minimize':
                    xml_bool = True if xml_text == 'True' else False
                    launcher[xml_tag] = xml_bool

            # Add launcher to categories dictionary
            launchers[launcher['id']] = launcher

    return (categories, launchers)

#
# Write to disk launcher ROMs XML database.
#
def fs_write_ROM_XML_file(roms_xml_file, roms, launcher):
    log_info('fs_write_ROM_XML_file() Saving XML file {0}'.format(roms_xml_file))

    # --- Notify we are busy doing things ---
    kodi_busydialog_ON()

    # Original Angelscry method for generating the XML was to grow a string, like this
    # xml_content = 'test'
    # xml_content += 'more test'
    # However, this method is very slow because string has to be reallocated every time is grown.
    # It is much faster to create a list of string and them join them!
    # See https://waymoot.org/home/python_string/
    try:
        str_list = []
        str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        str_list.append('<advanced_emulator_launcher_ROMs version="1.0">\n')

        # Print some information in the XML so the user can now which launcher created it.
        # Note that this is ignored when reading the file.
        str_list.append('<launcher>\n')
        str_list.append(XML_text('id', launcher['id']))
        str_list.append(XML_text('name', launcher['name']))
        str_list.append(XML_text('categoryID', launcher['categoryID']))
        str_list.append(XML_text('platform', launcher['platform']))
        str_list.append(XML_text('rompath', launcher['rompath']))
        str_list.append(XML_text('thumbpath', launcher['thumbpath']))
        str_list.append(XML_text('fanartpath', launcher['fanartpath']))
        str_list.append('</launcher>\n')

        # Create list of ROMs
        # Size optimization: only write in the XML fields which are not ''. This
        # will save A LOT of disk space and reduce loading times (at a cost of
        # some writing time, but writing is much less frequent than reading).
        for romID in sorted(roms, key = lambda x : roms[x]['name']):
            # Data which is not string must be converted to string
            rom = roms[romID]
            str_list.append('<rom>\n')
            str_list.append(XML_text('id', romID))
            str_list.append(XML_text('name', rom["name"]))
            if rom['filename']: str_list.append(XML_text('filename', rom['filename']))
            if rom['thumb']:    str_list.append(XML_text('thumb', rom['thumb']))
            if rom['fanart']:   str_list.append(XML_text('fanart', rom['fanart']))
            if rom['trailer']:  str_list.append(XML_text('trailer', rom['trailer']))
            if rom['custom']:   str_list.append(XML_text('custom', rom['custom']))
            if rom['genre']:    str_list.append(XML_text('genre', rom['genre']))
            if rom['year']:     str_list.append(XML_text('year', rom['year']))
            if rom['studio']:   str_list.append(XML_text('studio', rom['studio']))
            if rom['plot']:     str_list.append(XML_text('plot', rom['plot']))
            if rom['altapp']:   str_list.append(XML_text('altapp', rom['altapp']))
            if rom['altarg']:   str_list.append(XML_text('altarg', rom['altarg']))
            str_list.append(XML_text('finished', str(rom['finished'])))
            str_list.append(XML_text('nointro_status', rom['nointro_status']))
            str_list.append('</rom>\n')
        # End of file
        str_list.append('</advanced_emulator_launcher_ROMs>\n')

        # Join string and save categories.xml file
        full_string = ''.join(str_list)
        file_obj = open(roms_xml_file, 'wt' )
        file_obj.write(full_string)
        file_obj.close()
    except OSError:
        log_kodi_notify_warn('Advanced Emulator Launcher - Error', 'Cannot write {} file (OSError)'.format(roms_xml_file))
        log_error('fs_write_ROM_XML_file() (OSerror) Cannot write file "{}"'.format(roms_xml_file))
    except IOError:
        log_kodi_notify_warn('Advanced Emulator Launcher - Error', 'Cannot write {} file (IOError)'.format(roms_xml_file))
        log_error('fs_write_ROM_XML_file() (IOError) Cannot write file "{}"'.format(roms_xml_file))

    # --- We are not busy anymore ---
    kodi_busydialog_OFF()

#
# Loads a launcher XML with the ROMs
#
def fs_load_ROM_XML_file(roms_xml_file):
    __debug_xml_parser = 0
    roms = {}

    # --- If file does not exist return empty dictionary ---
    if not os.path.isfile(roms_xml_file):
        return {}

    # --- Notify we are busy doing things ---
    kodi_busydialog_ON()

    # --- Parse using cElementTree ---
    log_verb('fs_load_ROM_XML_file() Loading XML file {0}'.format(roms_xml_file))
    # If XML has errors (invalid characters, etc.) this will rais exception 'err'
    try:
        xml_tree = ET.parse(roms_xml_file)
    except:
        return {}
    xml_root = xml_tree.getroot()
    for root_element in xml_root:
        if __debug_xml_parser: log_debug('Root child {0}'.format(root_element.tag))

        if root_element.tag == 'rom':
            # Default values
            # Everything is a tring except: finished [bool]
            # nointro_status must be ['Have', 'Miss', 'Unknown', 'None']
            rom = fs_new_rom()
            for rom_child in root_element:
                # By default read strings
                xml_text = rom_child.text if rom_child.text is not None else ''
                xml_text = text_unescape_XML(xml_text)
                xml_tag  = rom_child.tag
                if __debug_xml_parser: log_debug('{0} --> {1}'.format(xml_tag, xml_text))
                rom[xml_tag] = xml_text

                # Now transform data type depending on tag name
                if xml_tag == 'finished':
                    xml_bool = True if xml_text == 'True' else False
                    rom[xml_tag] = xml_bool
                elif xml_tag == 'nointro_status':
                    xml_string = xml_text if xml_text in ['Have', 'Miss', 'Unknown', 'None'] else 'None'
                    rom[xml_tag] = xml_string
            roms[rom['id']] = rom
            
    # --- We are not busy anymore ---
    kodi_busydialog_OFF()

    return roms

#
# Write to disk favourites.xml
#
def fs_write_Favourites_XML_file(roms_xml_file, roms):
    log_info('fs_write_Favourites_XML_file() Saving XML file {0}'.format(roms_xml_file))
    try:
        str_list = []
        str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        str_list.append('<advanced_emulator_launcher_Favourites version="1.0">\n')
        for romID in sorted(roms, key = lambda x : roms[x]["name"]):
            rom = roms[romID]
            str_list.append('<rom>\n')
            str_list.append(XML_text('id', romID))
            str_list.append(XML_text('name', rom['name']))
            str_list.append(XML_text('filename', rom['filename']))
            str_list.append(XML_text('thumb', rom['thumb']))
            str_list.append(XML_text('fanart', rom['fanart']))
            str_list.append(XML_text('trailer', rom['trailer']))
            str_list.append(XML_text('custom', rom['custom']))
            str_list.append(XML_text('genre', rom['genre']))
            str_list.append(XML_text('year', rom['year']))
            str_list.append(XML_text('studio', rom['studio']))
            str_list.append(XML_text('plot', rom['plot']))
            str_list.append(XML_text('altapp', rom['altapp']))
            str_list.append(XML_text('altarg', rom['altarg']))
            str_list.append(XML_text('finished', str(rom['finished'])))
            str_list.append(XML_text('nointro_status', rom['nointro_status']))
            str_list.append(XML_text('launcherID', rom['launcherID']))
            str_list.append(XML_text('platform', rom['platform']))
            str_list.append(XML_text('application', rom['application']))
            str_list.append(XML_text('args', rom['args']))
            str_list.append(XML_text('rompath', rom['rompath']))
            str_list.append(XML_text('romext', rom['romext']))
            str_list.append(XML_text('fav_status', rom['fav_status']))
            str_list.append('</rom>\n')
        str_list.append('</advanced_emulator_launcher_Favourites>\n')
        full_string = ''.join(str_list)
        file_obj = open(roms_xml_file, 'wt' )
        file_obj.write(full_string)
        file_obj.close()
    except OSError:
        gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write {0} file (OSError)'.format(roms_xml_file))
    except IOError:
        gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write {0} file (IOError)'.format(roms_xml_file))

#
# Loads an XML file containing the favourite ROMs
# It is basically the same as ROMs, but with some more fields to store launching application data.
#
def fs_load_Favourites_XML_file(roms_xml_file):
    __debug_xml_parser = 0
    roms = {}

    # --- If file does not exist return empty dictionary ---
    if not os.path.isfile(roms_xml_file):
        return {}

    # --- Parse using cElementTree ---
    log_verb('fs_load_Favourites_XML_file() Loading XML file {0}'.format(roms_xml_file))
    xml_tree = ET.parse(roms_xml_file)
    xml_root = xml_tree.getroot()
    for root_element in xml_root:
        if __debug_xml_parser: log_debug('Root child {0}'.format(root_element.tag))

        if root_element.tag == 'rom':
            # Default values
            rom = fs_new_favourite_rom()
            for rom_child in root_element:
                # By default read strings
                xml_text = rom_child.text if rom_child.text is not None else ''
                xml_text = text_unescape_XML(xml_text)
                xml_tag  = rom_child.tag
                if __debug_xml_parser: log_debug('{0} --> {1}'.format(xml_tag, xml_text))
                rom[xml_tag] = xml_text
                
                # Now transform data depending on tag name
                if xml_tag == 'finished':
                    xml_bool = True if xml_text == 'True' else False
                    rom[xml_tag] = xml_bool
                elif xml_tag == 'fav_status':
                    xml_string = xml_text if xml_text in ['OK', 'Unlinked', 'Broken'] else 'OK'
                    rom[xml_tag] = xml_string
            roms[rom['id']] = rom

    return roms
    
def fs_load_NoIntro_XML_file(roms_xml_file):
    # --- If file does not exist return empty dictionary ---
    if not os.path.isfile(roms_xml_file):
        return {}

    # --- Parse using cElementTree ---
    log_verb('fs_load_NoIntro_XML_file() Loading XML file {}'.format(roms_xml_file))
    nointro_roms = {}
    xml_tree = ET.parse(roms_xml_file)
    xml_root = xml_tree.getroot()
    for root_element in xml_root:
        if root_element.tag == 'game':
            rom_name = root_element.attrib['name']
            nointro_rom = {'name' : rom_name}
            nointro_roms[rom_name] = nointro_rom

    return nointro_roms

#
# Loads offline scraper information XML file.
#
def fs_load_GameInfo_XML(xml_file):
    __debug_xml_parser = 0
    games = {}

    # --- Check that file exists ---
    if not os.path.isfile(xml_file):
        log_error("Cannot load file '{}'".format(xml_file))
        return games

    # --- Parse using cElementTree ---
    log_verb('fs_load_GameInfo_XML() Loading "{}"'.format(xml_file))
    xml_tree = ET.parse(xml_file)
    xml_root = xml_tree.getroot()
    for game_element in xml_root:
        if __debug_xml_parser: 
            log_debug('=== Root child tag "{}" ==='.format(game_element.tag))

        if game_element.tag == 'game':
            # Default values
            game = {'name'    : '', 'description'  : '', 'year'   : '',
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
                xml_text = text_unescape_XML(xml_text)
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

# -------------------------------------------------------------------------------------------------
# NFO files
# -------------------------------------------------------------------------------------------------
#
# Returns:
# user_info_str  Information string that can be used for notifications in interactive mode (for example, 
#                when "Edit ROM", or for logging (export all ROMs NFO files)
#
def fs_export_ROM_NFO(launcher, rom):
    F = misc_split_path(rom['filename'])
    nfo_file_path  = F.path_noext + '.nfo'
    log_debug('fs_export_ROM_NFO() Loading "{}"'.format(nfo_file_path))

    # Always overwrite NFO files.
    user_info_str = ''
    log_debug('fs_export_ROM_NFO() NFO file DOES NOT exist. Creating new one.')
    nfo_content = []
    nfo_content.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
    nfo_content.append('<game>\n')
    nfo_content.append(XML_text('title',     rom['name']))
    nfo_content.append(XML_text('platform',  rom['platform']))
    nfo_content.append(XML_text('year',      rom['year']))
    nfo_content.append(XML_text('publisher', rom['studio']))
    nfo_content.append(XML_text('genre',     rom['genre']))
    nfo_content.append(XML_text('plot',      rom['plot']))
    nfo_content.append('</game>\n')
    full_string = ''.join(nfo_content)
    usock = open(nfo_file_path, 'wt')
    usock.write(full_string)
    usock.close()
    user_info_str = 'Created {}'.format(nfo_file_path)
    log_debug("fs_export_ROM_NFO() Created '{}'".format(temp_file_path))

    return user_info_str

#
# Reads an NFO file with ROM information.
# Modifies roms dictionary even outside this function. See comments in fs_import_launcher_NFO()
# This file is called by the gui when user is editing a ROM interactively.
#
def fs_import_ROM_NFO(launcher, roms, romID):
    F = misc_split_path(roms[romID]['filename'])
    nfo_file_path = F.path_noext + '.nfo'
    log_debug('fs_export_ROM_NFO() Loading "{}"'.format(nfo_file_path))
    
    # --- Import data ---
    user_info_str = ''
    if os.path.isfile(nfo_file_path):
        # Read file, put in a string and remove line endings
        file = open(nfo_file_path, 'rt')
        nfo_str = file.read().replace('\r', '').replace('\n', '')
        file.close()

        # Search for items
        item_title     = re.findall('<title>(.*?)</title>', nfo_str)
        item_platform  = re.findall('<platform>(.*?)</platform>', nfo_str)
        item_year      = re.findall('<year>(.*?)</year>', nfo_str)
        item_publisher = re.findall('<publisher>(.*?)</publisher>', nfo_str)
        item_genre     = re.findall('<genre>(.*?)</genre>', nfo_str)
        item_plot      = re.findall('<plot>(.*?)</plot>', nfo_str)

        if len(item_title) > 0:     roms[romID]['title']     = text_unescape_XML(item_title[0])
        if len(item_title) > 0:     roms[romID]['platform']  = text_unescape_XML(item_platform[0])
        if len(item_year) > 0:      roms[romID]['year']      = text_unescape_XML(item_year[0])
        if len(item_publisher) > 0: roms[romID]['publisher'] = text_unescape_XML(item_publisher[0])
        if len(item_genre) > 0:     roms[romID]['genre']     = text_unescape_XML(item_genre[0])
        if len(item_plot) > 0:      roms[romID]['plot']      = text_unescape_XML(item_plot[0])

        user_info_str = 'Imported {}'.format(nfo_file_path)
        log_debug("fs_import_ROM_NFO() Imported '{}'".format(nfo_file_path))
    else:
        user_info_str = 'NFO file not found {}'.format(nfo_file_path)
        log_debug("fs_import_ROM_NFO() NFO file not found '{}'".format(nfo_file_path))

    return user_info_str

#
# This file is called by the ROM scanner to read a ROM info file automatically.
# NFO file existence is checked before calling this function, so NFO file must always exist.
#
def fs_load_NFO_file_scanner(nfo_file_path):
    nfo_dic = {'title' : '', 'platform' : '', 'year' : '', 'publisher' : '', 
               'genre' : '', 'plot' : '' }

    # Read file, put in a string and remove line endings
    file = open(nfo_file_path, 'rt')
    nfo_str = file.read().replace('\r', '').replace('\n', '')
    file.close()

    # Search for items
    item_title     = re.findall('<title>(.*?)</title>', nfo_str)
    item_platform  = re.findall('<platform>(.*?)</platform>', nfo_str)
    item_year      = re.findall('<year>(.*?)</year>', nfo_str)
    item_publisher = re.findall('<publisher>(.*?)</publisher>', nfo_str)
    item_genre     = re.findall('<genre>(.*?)</genre>', nfo_str)
    item_plot      = re.findall('<plot>(.*?)</plot>', nfo_str)

    if len(item_title) > 0:     nfo_dic['title']     = text_unescape_XML(item_title[0])
    if len(item_title) > 0:     nfo_dic['platform']  = text_unescape_XML(item_platform[0])
    if len(item_year) > 0:      nfo_dic['year']      = text_unescape_XML(item_year[0])
    if len(item_publisher) > 0: nfo_dic['publisher'] = text_unescape_XML(item_publisher[0])
    if len(item_genre) > 0:     nfo_dic['genre']     = text_unescape_XML(item_genre[0])
    if len(item_plot) > 0:      nfo_dic['plot']      = text_unescape_XML(item_plot[0])

    return nfo_dic

#
# Standalone launchers:
#   NFO files are stored in self.settings["launcher_thumb_path"] if not empty.
#   If empty, it defaults to DEFAULT_NFO_DIR = os.path.join(PLUGIN_DATA_DIR, 'nfos')
# ROM launchers:
#   Same as standalone launchers.
#
def fs_export_launcher_NFO(settings, launcher):
    # --- Get NFO file name ---
    log_debug('fs_export_launcher_NFO() Exporting launcher NFO file.')
    nfo_file_path, temp_file_path = fs_get_launcher_NFO_names(settings, launcher)

    # If NFO file does not exist then create them. If it exists, overwrite.
    log_debug('fs_export_launcher_NFO() NFO file DOES NOT exist. Creating new one.')
    nfo_content = []
    nfo_content.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
    nfo_content.append('<launcher>\n')
    nfo_content.append(XML_text('title',     launcher['name']))
    nfo_content.append(XML_text('platform',  launcher['platform']))
    nfo_content.append(XML_text('year',      launcher['year']))
    nfo_content.append(XML_text('publisher', launcher['studio']))
    nfo_content.append(XML_text('genre',     launcher['genre']))
    nfo_content.append(XML_text('plot',      launcher['plot']))
    nfo_content.append('</launcher>\n')
    full_string = ''.join(nfo_content)
    usock = open(nfo_file_path, 'wt')
    usock.write(full_string)
    usock.close()
    user_info_str = 'Created %s'.format(os.path.basename(nfo_file_path))
    log_debug("fs_export_launcher_NFO() Created '{}'".format(nfo_file_path))

    return user_info_str

#
# Python data model: lists and dictionaries are mutable. It means the can be changed if passed as
# parameters of functions. However, items can not be replaced by new objects!
# Notably, numbers, strings and tuples are immutable. Dictionaries and lists are mutable.
#
# See http://stackoverflow.com/questions/986006/how-do-i-pass-a-variable-by-reference
# See https://docs.python.org/2/reference/datamodel.html
#
# Function asumes that the NFO file already exists.
#
def fs_import_launcher_NFO(settings, launchers, launcherID):
    # --- Get NFO file name ---
    log_debug('fs_import_launcher_NFO() Importing launcher NFO file.')
    nfo_file_path, _ = fs_get_launcher_NFO_names(settings, self.launchers[launcherID])

    # --- Import data ---
    user_info_str = ''
    if os.path.isfile(nfo_file_path):
        # Read NFO file data
        f = open(nfo_file_path, 'rt')
        item_nfo = f.read().replace('\r','').replace('\n','')
        f.close()
        
        # Find data
        item_title     = re.findall('<title>(.*?)</title>', item_nfo)
        item_platform  = re.findall('<platform>(.*?)</platform>', item_nfo)
        item_year      = re.findall('<year>(.*?)</year>', item_nfo)
        item_publisher = re.findall('<publisher>(.*?)</publisher>', item_nfo)
        item_genre     = re.findall('<genre>(.*?)</genre>', item_nfo)
        item_plot      = re.findall('<plot>(.*?)</plot>', item_nfo)

        # Careful about object mutability! This should modify the dictionary
        # passed as argument outside this function.
        launchers[launcherID]['name']     = text_unescape_XML(item_title[0])
        launchers[launcherID]['platform'] = text_unescape_XML(item_platform[0])
        launchers[launcherID]['year']     = text_unescape_XML(item_year[0])
        launchers[launcherID]['studio']   = text_unescape_XML(item_publisher[0])
        launchers[launcherID]['genre']    = text_unescape_XML(item_genre[0])
        launchers[launcherID]['plot']     = text_unescape_XML(item_plot[0])
        user_info_str = 'Imported {}'.format(nfo_file_path)
        log_debug("fs_import_launcher_NFO() Imported '{}'".format(nfo_file_path))
    else:
        user_info_str = 'NFO file not found {}'.format(nfo_file_path)
        log_debug("fs_import_launcher_NFO() NFO file not found '{}'".format(nfo_file_path))

    return user_info_str

def fs_get_launcher_NFO_names(settings, launcher):
    launcher_name = launcher['name']
    if len(settings['launcher_nfo_path']) > 0:
        nfo_dir = settings['launcher_nfo_path']
        log_debug("fs_get_launcher_NFO_names() Using default launcher_nfo_path = '{}'".format(nfo_dir))
        nfo_file_path = os.path.join(nfo_dir, launcher_name + '.nfo')
    else:
        nfo_dir = settings['launcher_nfo_path']
        log_debug("fs_get_launcher_NFO_names() User set launcher_nfo_path = '{}'".format(nfo_dir))
        nfo_file_path = os.path.join(nfo_dir, launcher_name + '.nfo')
    log_debug("fs_get_launcher_NFO_names() Using nfo_file_path = '{}'".format(nfo_file_path))

    return nfo_file_path, temp_file_path
