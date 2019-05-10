# -*- coding: utf-8 -*-
# Advanced Emulator Launcher filesystem I/O functions
#

# Copyright (c) 2016-2018 Wintermute0110 <wintermute0110@gmail.com>
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

# --- Pyhton standard library
from __future__ import unicode_literals
from __future__ import division
import json
import io
import codecs
import time
import os
import sys
import string
import base64
import pprint
import errno

# --- XML stuff ---
# ~~~ cElementTree sometimes fails to parse XML in Kodi's Python interpreter... I don't know why
# import xml.etree.cElementTree as ET

# ~~~ Using ElementTree seems to solve the problem
import xml.etree.ElementTree as ET
import xml.dom.minidom

# --- AEL packages ---
from resources.constants import *
from resources.utils import *

# --- AEL ROM storage version format ---
# >> An integer number incremented whenever there is a change in the ROM storage format.
# >> This will allow easy migrations.
AEL_STORAGE_FORMAT = 1

# --- Configure JSON writer ---
# NOTE More compact JSON files (less blanks) load faster because size is smaller.
JSON_indent     = 1
JSON_separators = (',', ':')

# -------------------------------------------------------------------------------------------------
# Data model used in the plugin
# Internally all string in the data model are Unicode. They will be encoded to
# UTF-8 when writing files.
# -------------------------------------------------------------------------------------------------
# These three functions create a new data structure for the given object and (very importantly) 
# fill the correct default values). These must match what is written/read from/to the XML files.
# Tag name in the XML is the same as in the data dictionary.
#
def fs_new_category():
    return {
        'id' : '',
        'type': OBJ_CATEGORY,
        'm_name' : '',
        'm_year' : '',
        'm_genre' : '',
        'm_developer' : '',
        'm_rating' : '',
        'm_plot' : '',
        'finished' : False,
        'default_icon' : 's_icon',
        'default_fanart' : 's_fanart',
        'default_banner' : 's_banner',
        'default_poster' : 's_poster',
        'default_clearlogo' : 's_clearlogo',
        'Asset_Prefix' : '',
        's_icon' : '',
        's_fanart' : '',
        's_banner' : '',
        's_poster' : '',
        's_clearlogo' : '',
        's_trailer' : ''
    }

def fs_new_launcher():
    return {
        'id' : '',
        'type': '',
        'm_name' : '',
        'm_year' : '',
        'm_genre' : '',
        'm_developer' : '',
        'm_rating' : '',
        'm_plot' : '',
        'platform' : '',
        'categoryID' : '',
        'application' : '',
        'args' : '',
        'args_extra' : [],
        'rompath' : '',
        'romext' : '',
        'finished': False,
        'toggle_window' : False, # Former 'minimize'
        'non_blocking' : False,
        'multidisc' : True,
        'roms_base_noext' : '',
        'nointro_xml_file' : '',
        'nointro_display_mode' : NOINTRO_DMODE_ALL,
        'launcher_display_mode' : LAUNCHER_DMODE_FLAT,
        'num_roms' : 0,
        'num_parents' : 0,
        'num_clones' : 0,
        'num_have' : 0,
        'num_miss' : 0,
        'num_unknown' : 0,
        'timestamp_launcher' : 0.0,
        'timestamp_report' : 0.0,
        'default_icon' : 's_icon',
        'default_fanart' : 's_fanart',
        'default_banner' : 's_banner',
        'default_poster' : 's_poster',
        'default_clearlogo' : 's_clearlogo',
        'default_controller' : 's_controller',
        'Asset_Prefix' : '',
        's_icon' : '',
        's_fanart' : '',
        's_banner' : '',
        's_poster' : '',
        's_clearlogo' : '',
        's_controller' : '',
        's_trailer' : '',
        'roms_default_icon' : 's_boxfront',
        'roms_default_fanart' : 's_fanart',
        'roms_default_banner' : 's_banner',
        'roms_default_poster' : 's_flyer',
        'roms_default_clearlogo' : 's_clearlogo',
        'ROM_asset_path' : '',
        'path_title' : '',
        'path_snap' : '',
        'path_boxfront' : '',
        'path_boxback' : '',
        'path_cartridge' : '',
        'path_fanart' : '',
        'path_banner' : '',
        'path_clearlogo' : '',
        'path_flyer' : '',
        'path_map' : '',
        'path_manual' : '',
        'path_trailer' : ''
    }

def fs_new_collection():
    return {
        'id' : '',
        'type': OBJ_LAUNCHER_COLLECTION,
        'm_name' : '',
        'm_genre' : '',
        'm_rating' : '',
        'm_plot' : '',
        'roms_base_noext' : '',
        'default_icon' : 's_icon',
        'default_fanart' : 's_fanart',
        'default_banner' : 's_banner',
        'default_poster' : 's_poster',
        'default_clearlogo' : 's_clearlogo',
        's_icon' : '',
        's_fanart' : '',
        's_banner' : '',
        's_poster' : '',
        's_clearlogo' : '',
        's_trailer' : ''
    }

def fs_new_rom():
    return {
        'id' : '',
        'type': OBJ_ROM,
        'm_name' : '',
        'm_year' : '',
        'm_genre' : '',
        'm_developer' : '',
        'm_nplayers' : '',
        'm_esrb' : ESRB_PENDING,
        'm_rating' : '',
        'm_plot' : '',
        'filename' : '',
        'disks' : [],
        'altapp' : '',
        'altarg' : '',
        'finished' : False,
        'nointro_status' : NOINTRO_STATUS_NONE,
        'pclone_status' : PCLONE_STATUS_NONE,
        'cloneof' : '',
        's_title' : '',
        's_snap' : '',
        's_boxfront' : '',
        's_boxback' : '',
        's_cartridge' : '',
        's_fanart' : '',
        's_banner' : '',
        's_clearlogo' : '',
        's_flyer' : '',
        's_map' : '',
        's_manual' : '',
        's_trailer' : ''
    }

# -------------------------------------------------------------------------------------------------
# Favourite ROM creation/management
# -------------------------------------------------------------------------------------------------
#
# Creates a new Favourite ROM dictionary from parent ROM and Launcher.
#
# No-Intro Missing ROMs are not allowed in Favourites or Virtual Launchers.
# fav_status = ['OK', 'Unlinked ROM', 'Unlinked Launcher', 'Broken'] default 'OK'
#  'OK'                ROM filename exists and launcher exists and ROM id exists
#  'Unlinked ROM'      ROM filename exists but ROM ID in launcher does not
#  'Unlinked Launcher' ROM filename exists but Launcher ID not found
#                      Note that if the launcher does not exists implies ROM ID does not exist.
#                      If launcher doesn't exist ROM JSON cannot be loaded.
#  'Broken'            ROM filename does not exist. ROM is unplayable
#
def fs_get_Favourite_from_ROM(rom, launcher):
    # >> Copy dictionary object
    favourite = dict(rom)

    # Delete nointro_status field from ROM. Make sure this is done in the copy to be
    # returned to avoid chaning the function parameters (dictionaries are mutable!)
    # See http://stackoverflow.com/questions/5844672/delete-an-element-from-a-dictionary
    # NOTE keep it!
    # del favourite['nointro_status']

    # >> Copy parent launcher fields into Favourite ROM
    favourite['launcherID']             = launcher['id']
    favourite['platform']               = launcher['platform']
    favourite['application']            = launcher['application']
    favourite['args']                   = launcher['args']
    favourite['args_extra']             = launcher['args_extra']
    favourite['rompath']                = launcher['rompath']
    favourite['romext']                 = launcher['romext']
    favourite['toggle_window']          = launcher['toggle_window']
    favourite['non_blocking']           = launcher['non_blocking']
    favourite['roms_default_icon']      = launcher['roms_default_icon']
    favourite['roms_default_fanart']    = launcher['roms_default_fanart']
    favourite['roms_default_banner']    = launcher['roms_default_banner']
    favourite['roms_default_poster']    = launcher['roms_default_poster']
    favourite['roms_default_clearlogo'] = launcher['roms_default_clearlogo']

    # >> Favourite ROM unique fields
    # >> Favourite ROMs in "Most played ROMs" DB also have 'launch_count' field.
    favourite['fav_status'] = 'OK'

    return favourite

#
# Creates a new Favourite ROM from old Favourite, parent ROM and parent Launcher. This function is
# used when repairing/relinking a Favourite/Collection ROM.
#
# Repair mode (integer):
#   0) Relink and update launcher info
#   1) Relink and update metadata
#   2) Relink and update artwork
#   3) Relink and update everything
#
def fs_repair_Favourite_ROM(repair_mode, old_fav_rom, parent_rom, parent_launcher):
    new_fav_rom = dict(old_fav_rom)

    # --- Step 0 is always done in any Favourite/Collection repair ---
    log_info('fs_repair_Favourite_ROM() Relinking ROM and launcher (common stuff)')
    log_info('fs_repair_Favourite_ROM() Old ROM name "{0}"'.format(old_fav_rom['m_name']))
    log_info('fs_repair_Favourite_ROM() New ROM name "{0}"'.format(parent_rom['m_name']))
    log_info('fs_repair_Favourite_ROM() New launcher "{0}"'.format(parent_launcher['m_name']))

    # >> Main stuff
    fs_aux_copy_ROM_main_stuff(parent_launcher, parent_rom, new_fav_rom)

    # >> Launcher stuff
    fs_aux_copy_ROM_launcher_info(parent_launcher, new_fav_rom)

    # --- Metadata ---
    if repair_mode == 1:
        log_debug('fs_repair_Favourite_ROM() Relinking Metadata')
        fs_aux_copy_ROM_metadata(parent_rom, new_fav_rom)
    # --- Artwork ---
    elif repair_mode == 2:
        log_debug('fs_repair_Favourite_ROM() Relinking Artwork')
        fs_aux_copy_ROM_artwork(parent_launcher, parent_rom, new_fav_rom)
    # --- Metadata and artwork ---
    elif repair_mode == 3:
        log_debug('fs_repair_Favourite_ROM() Relinking Metadata and Artwork')
        fs_aux_copy_ROM_metadata(parent_rom, new_fav_rom)
        fs_aux_copy_ROM_artwork(parent_launcher, parent_rom, new_fav_rom)

    return new_fav_rom

def fs_aux_copy_ROM_main_stuff(source_launcher, source_rom, dest_rom):
    dest_rom['id']          = source_rom['id']
    dest_rom['launcherID']  = source_launcher['id']
    dest_rom['filename']    = source_rom['filename']
    dest_rom['fav_status']  = 'OK'

def fs_aux_copy_ROM_launcher_info(source_launcher, dest_rom):
    dest_rom['platform']      = source_launcher['platform']
    dest_rom['application']   = source_launcher['application']
    dest_rom['args']          = source_launcher['args']
    dest_rom['args_extra']    = source_launcher['args_extra']
    dest_rom['rompath']       = source_launcher['rompath']
    dest_rom['romext']        = source_launcher['romext']
    dest_rom['toggle_window'] = source_launcher['toggle_window']
    dest_rom['non_blocking']  = source_launcher['non_blocking']

def fs_aux_copy_ROM_metadata(source_rom, dest_rom):
    dest_rom['m_name']         = source_rom['m_name']
    dest_rom['m_year']         = source_rom['m_year']
    dest_rom['m_genre']        = source_rom['m_genre']
    dest_rom['m_developer']    = source_rom['m_developer']
    dest_rom['m_nplayers']     = source_rom['m_nplayers']
    dest_rom['m_esrb']         = source_rom['m_esrb']
    dest_rom['m_rating']       = source_rom['m_rating']
    dest_rom['m_plot']         = source_rom['m_plot']
    dest_rom['altapp']         = source_rom['altapp']
    dest_rom['altarg']         = source_rom['altarg']
    dest_rom['finished']       = source_rom['finished']
    dest_rom['nointro_status'] = source_rom['nointro_status']
    dest_rom['pclone_status']  = source_rom['pclone_status']
    dest_rom['cloneof']        = source_rom['cloneof']

def fs_aux_copy_ROM_artwork(source_launcher, source_rom, dest_rom):
    dest_rom['s_title']     = source_rom['s_title']
    dest_rom['s_snap']      = source_rom['s_snap']
    dest_rom['s_fanart']    = source_rom['s_fanart']
    dest_rom['s_banner']    = source_rom['s_banner']
    dest_rom['s_clearlogo'] = source_rom['s_clearlogo']
    dest_rom['s_boxfront']  = source_rom['s_boxfront']
    dest_rom['s_boxback']   = source_rom['s_boxback']
    dest_rom['s_cartridge'] = source_rom['s_cartridge']
    dest_rom['s_flyer']     = source_rom['s_flyer']
    dest_rom['s_map']       = source_rom['s_map']
    dest_rom['s_manual']    = source_rom['s_manual']
    dest_rom['s_trailer']   = source_rom['s_trailer']
    dest_rom['roms_default_icon']      = source_launcher['roms_default_icon']
    dest_rom['roms_default_fanart']    = source_launcher['roms_default_fanart']
    dest_rom['roms_default_banner']    = source_launcher['roms_default_banner']
    dest_rom['roms_default_poster']    = source_launcher['roms_default_poster']
    dest_rom['roms_default_clearlogo'] = source_launcher['roms_default_clearlogo']

# -------------------------------------------------------------------------------------------------
# ROM storage file names
# -------------------------------------------------------------------------------------------------
def fs_get_ROMs_basename(category_name, launcher_name, launcherID):
    clean_cat_name = ''.join([i if i in string.printable else '_' for i in category_name]).replace(' ', '_')
    clean_launch_title = ''.join([i if i in string.printable else '_' for i in launcher_name]).replace(' ', '_')
    roms_base_noext = 'roms_' + clean_cat_name + '_' + clean_launch_title + '_' + launcherID[0:6]
    log_verb('fs_get_ROMs_basename() roms_base_noext "{0}"'.format(roms_base_noext))

    return roms_base_noext

def fs_get_collection_ROMs_basename(collection_name, collectionID):
    clean_collection_name = ''.join([i if i in string.printable else '_' for i in collection_name]).replace(' ', '_')
    roms_base_noext = clean_collection_name + '_' + collectionID[0:6]
    log_verb('fs_get_collection_ROMs_basename() roms_base_noext "{0}"'.format(roms_base_noext))

    return roms_base_noext

# -------------------------------------------------------------------------------------------------
# Categories/Launchers
# -------------------------------------------------------------------------------------------------
#
# Write to disk categories.xml
#
def fs_write_catfile(categories_FN, header_dic, categories, launchers):
    log_verb('fs_write_catfile() Writing {0}'.format(categories_FN.getPath()))

    # Original Angelscry method for generating the XML was to grow a string, like this
    # xml_content = 'test'
    # xml_content += 'more test'
    # However, this method is very slow because string has to be reallocated every time is grown.
    # It is much faster to create a list of string and them join them!
    # See https://waymoot.org/home/python_string/
    str_list = []
    str_list.append('<?xml version="1.0" encoding="utf-8" ?>\n')
    str_list.append('<advanced_emulator_launcher>\n')

    # >> Write a timestamp when file is created. This enables the Virtual Launchers to know if
    # >> it's time for an update.
    str_list.append('<control>\n')
    str_list.append(text_XML_line('database_version', unicode(header_dic['database_version'])))
    str_list.append(text_XML_line('update_timestamp', unicode(header_dic['update_timestamp'])))
    str_list.append('</control>\n')

    # --- Create Categories XML list ---
    for categoryID in sorted(categories, key = lambda x : categories[x]['m_name']):
        category = categories[categoryID]
        # Data which is not string must be converted to string
        # text_XML_line() returns Unicode strings that will be encoded to UTF-8 later.
        str_list.append('<category>\n')
        str_list.append(text_XML_line('id', categoryID))
        str_list.append(text_XML_line('type', category['type']))
        str_list.append(text_XML_line('m_name', category['m_name']))
        str_list.append(text_XML_line('m_year', category['m_year']))
        str_list.append(text_XML_line('m_genre', category['m_genre']))
        str_list.append(text_XML_line('m_developer', category['m_developer']))
        str_list.append(text_XML_line('m_rating', category['m_rating']))
        str_list.append(text_XML_line('m_plot', category['m_plot']))
        str_list.append(text_XML_line('finished', unicode(category['finished'])))
        str_list.append(text_XML_line('default_icon', category['default_icon']))
        str_list.append(text_XML_line('default_fanart', category['default_fanart']))
        str_list.append(text_XML_line('default_banner', category['default_banner']))
        str_list.append(text_XML_line('default_poster', category['default_poster']))
        str_list.append(text_XML_line('default_clearlogo', category['default_clearlogo']))
        str_list.append(text_XML_line('Asset_Prefix', category['Asset_Prefix']))
        str_list.append(text_XML_line('s_icon', category['s_icon']))
        str_list.append(text_XML_line('s_fanart', category['s_fanart']))
        str_list.append(text_XML_line('s_banner', category['s_banner']))
        str_list.append(text_XML_line('s_poster', category['s_poster']))
        str_list.append(text_XML_line('s_clearlogo', category['s_clearlogo']))
        str_list.append(text_XML_line('s_trailer', category['s_trailer']))
        str_list.append('</category>\n')

    # --- Write launchers ---
    # Data which is not string must be converted to string
    for launcherID in sorted(launchers, key = lambda x : launchers[x]['m_name']):
        launcher = launchers[launcherID]
        str_list.append('<launcher>\n')
        str_list.append(text_XML_line('id', launcherID))
        str_list.append(text_XML_line('type', launcher['type']))
        str_list.append(text_XML_line('m_name', launcher['m_name']))
        str_list.append(text_XML_line('m_year', launcher['m_year']))
        str_list.append(text_XML_line('m_genre', launcher['m_genre']))
        str_list.append(text_XML_line('m_developer', launcher['m_developer']))
        str_list.append(text_XML_line('m_rating', launcher['m_rating']))
        str_list.append(text_XML_line('m_plot', launcher['m_plot']))
        str_list.append(text_XML_line('platform', launcher['platform']))
        str_list.append(text_XML_line('categoryID', launcher['categoryID']))
        str_list.append(text_XML_line('application', launcher['application']))
        str_list.append(text_XML_line('args', launcher['args']))
        # >> To simulate a list with XML allow multiple XML tags.
        if 'args_extra' in launcher:
            for extra_arg in launcher['args_extra']:
                str_list.append(text_XML_line('args_extra', extra_arg))
        str_list.append(text_XML_line('rompath', launcher['rompath']))
        str_list.append(text_XML_line('romext', launcher['romext']))
        str_list.append(text_XML_line('finished', unicode(launcher['finished'])))
        str_list.append(text_XML_line('toggle_window', unicode(launcher['toggle_window'])))
        str_list.append(text_XML_line('non_blocking', unicode(launcher['non_blocking'])))
        str_list.append(text_XML_line('multidisc', unicode(launcher['multidisc'])))
        str_list.append(text_XML_line('roms_base_noext', launcher['roms_base_noext']))
        str_list.append(text_XML_line('nointro_xml_file', launcher['nointro_xml_file']))
        str_list.append(text_XML_line('nointro_display_mode', launcher['nointro_display_mode']))
        str_list.append(text_XML_line('launcher_display_mode', unicode(launcher['launcher_display_mode'])))
        str_list.append(text_XML_line('num_roms', unicode(launcher['num_roms'])))
        str_list.append(text_XML_line('num_parents', unicode(launcher['num_parents'])))
        str_list.append(text_XML_line('num_clones', unicode(launcher['num_clones'])))
        str_list.append(text_XML_line('num_have', unicode(launcher['num_have'])))
        str_list.append(text_XML_line('num_miss', unicode(launcher['num_miss'])))
        str_list.append(text_XML_line('num_unknown', unicode(launcher['num_unknown'])))
        str_list.append(text_XML_line('timestamp_launcher', unicode(launcher['timestamp_launcher'])))
        str_list.append(text_XML_line('timestamp_report', unicode(launcher['timestamp_report'])))
        # >> Launcher artwork
        str_list.append(text_XML_line('default_icon', launcher['default_icon']))
        str_list.append(text_XML_line('default_fanart', launcher['default_fanart']))
        str_list.append(text_XML_line('default_banner', launcher['default_banner']))
        str_list.append(text_XML_line('default_poster', launcher['default_poster']))
        str_list.append(text_XML_line('default_clearlogo', launcher['default_clearlogo']))
        str_list.append(text_XML_line('default_controller', launcher['default_controller']))
        str_list.append(text_XML_line('Asset_Prefix', launcher['Asset_Prefix']))
        str_list.append(text_XML_line('s_icon', launcher['s_icon']))
        str_list.append(text_XML_line('s_fanart', launcher['s_fanart']))
        str_list.append(text_XML_line('s_banner', launcher['s_banner']))
        str_list.append(text_XML_line('s_poster', launcher['s_poster']))
        str_list.append(text_XML_line('s_clearlogo', launcher['s_clearlogo']))
        str_list.append(text_XML_line('s_controller', launcher['s_controller']))
        str_list.append(text_XML_line('s_trailer', launcher['s_trailer']))
        # >> ROMs artwork
        str_list.append(text_XML_line('roms_default_icon', launcher['roms_default_icon']))
        str_list.append(text_XML_line('roms_default_fanart', launcher['roms_default_fanart']))
        str_list.append(text_XML_line('roms_default_banner', launcher['roms_default_banner']))
        str_list.append(text_XML_line('roms_default_poster', launcher['roms_default_poster']))
        str_list.append(text_XML_line('roms_default_clearlogo', launcher['roms_default_clearlogo']))
        str_list.append(text_XML_line('ROM_asset_path', launcher['ROM_asset_path']))
        str_list.append(text_XML_line('path_title', launcher['path_title']))
        str_list.append(text_XML_line('path_snap', launcher['path_snap']))
        str_list.append(text_XML_line('path_boxfront', launcher['path_boxfront']))
        str_list.append(text_XML_line('path_boxback', launcher['path_boxback']))
        str_list.append(text_XML_line('path_cartridge', launcher['path_cartridge']))
        str_list.append(text_XML_line('path_fanart', launcher['path_fanart']))
        str_list.append(text_XML_line('path_banner', launcher['path_banner']))
        str_list.append(text_XML_line('path_clearlogo', launcher['path_clearlogo']))
        str_list.append(text_XML_line('path_flyer', launcher['path_flyer']))
        str_list.append(text_XML_line('path_map', launcher['path_map']))
        str_list.append(text_XML_line('path_manual', launcher['path_manual']))
        str_list.append(text_XML_line('path_trailer', launcher['path_trailer']))
        str_list.append('</launcher>\n')
    # End of file
    str_list.append('</advanced_emulator_launcher>\n')

    # Strings in the list are Unicode. Encode to UTF-8.
    # Join string, and save categories.xml file.
    # Exceptions are catched inside FileName objects.
    categories_FN.saveStrToFile(''.join(str_list).encode('utf-8'))

#
# Loads categories.xml from disk and fills dictionary self.categories
#
def fs_load_catfile(categories_FN, header_dic, categories, launchers):
    __debug_xml_parser = 0

    # --- Create data structures ---
    header_dic['database_version'] = '0.0.0'
    header_dic['update_timestamp'] = 0.0
    update_timestamp = header_dic['update_timestamp']
    
    # --- Parse using cElementTree ---
    # >> If there are issues in the XML file (for example, invalid XML chars) ET.parse will fail
    log_verb('fs_load_catfile() Loading {0}'.format(categories_FN.getPath()))
    try:
        xml_root = fs_get_XML_root_from_str(categories_FN.loadFileToStr())
    except IOError as e:
        log_debug('fs_load_catfile() (IOError) errno = {0}'.format(e.errno))
        # log_debug(unicode(errno.errorcode))
        # >> No such file or directory
        if e.errno == errno.ENOENT:
            log_error('fs_load_catfile() (IOError) No such file or directory.')
        else:
            log_error('fs_load_catfile() (IOError) Unhandled errno value.')
        log_error('fs_load_catfile() (IOError) Return empty categories and launchers dictionaries.')
        return update_timestamp
    except ET.ParseError as e:
        log_error('fs_load_catfile() (ParseError) Exception parsing XML categories.xml')
        log_error('fs_load_catfile() (ParseError) {0}'.format(str(e)))
        kodi_dialog_OK('(ParseError) Exception reading categories.xml. '
                       'Maybe XML file is corrupt or contains invalid characters.')
        return update_timestamp

    for category_element in xml_root:
        if __debug_xml_parser: log_debug('Root child {0}'.format(category_element.tag))

        if category_element.tag == 'control':
            for control_child in category_element:
                if control_child.tag == 'update_timestamp':
                    # >> Convert Unicode to float
                    header_dic['update_timestamp'] = float(control_child.text)

        elif category_element.tag == 'category':
            # Default values
            category = fs_new_category()

            # Parse child tags of category
            for category_child in category_element:
                # By default read strings
                text_XML_line = category_child.text if category_child.text is not None else ''
                text_XML_line = text_unescape_XML(text_XML_line)
                xml_tag  = category_child.tag
                if __debug_xml_parser: log_debug('{0} --> {1}'.format(xml_tag, text_XML_line))

                # Now transform data depending on tag name
                if xml_tag == 'finished':
                    category[xml_tag] = True if text_XML_line == 'True' else False
                else:
                    # Internal data is always stored as Unicode. ElementTree already outputs Unicode.
                    category[xml_tag] = text_XML_line
            # --- Add category to categories dictionary ---
            categories[category['id']] = category

        elif category_element.tag == 'launcher':
            # Default values
            launcher = fs_new_launcher()

            # Parse child tags of category
            for category_child in category_element:
                # >> By default read strings
                text_XML_line = category_child.text if category_child.text is not None else ''
                text_XML_line = text_unescape_XML(text_XML_line)
                xml_tag  = category_child.tag
                if __debug_xml_parser: log_debug('{0} --> {1}'.format(xml_tag, text_XML_line))

                # >> Transform list() datatype
                if xml_tag == 'args_extra':
                    launcher[xml_tag].append(text_XML_line)
                # >> Transform Bool datatype
                elif (xml_tag == 'finished'
                   or xml_tag == 'toggle_window'
                   or xml_tag == 'non_blocking'
                   or xml_tag == 'multidisc'):
                    launcher[xml_tag] = True if text_XML_line == 'True' else False
                # >> Transform Int datatype
                elif (xml_tag == 'num_roms'
                   or xml_tag == 'num_parents'
                   or xml_tag == 'num_clones'
                   or xml_tag == 'num_have'
                   or xml_tag == 'num_miss'
                   or xml_tag == 'num_unknown'):
                    launcher[xml_tag] = int(text_XML_line)
                # >> Transform Float datatype
                elif (xml_tag == 'timestamp_launcher'
                   or xml_tag == 'timestamp_report'):
                    launcher[xml_tag] = float(text_XML_line)
                else:
                    launcher[xml_tag] = text_XML_line
            # --- Add launcher to categories dictionary ---
            launchers[launcher['id']] = launcher
    # log_verb('fs_load_catfile() Loaded {0} categories'.format(len(categories)))
    # log_verb('fs_load_catfile() Loaded {0} launchers'.format(len(launchers)))

# -------------------------------------------------------------------------------------------------
# Generic file writer
# str_list is a list of Unicode strings that will be joined and written to a file encoded in UTF-8.
# -------------------------------------------------------------------------------------------------
def fs_write_str_list_to_file(str_list, export_FN):
    log_verb('fs_write_str_list_to_file() Exporting "{0}"'.format(export_FN.getPath()))
    try:
        full_string = ''.join(str_list).encode('utf-8')
        file_obj = open(export_FN.getPath(), 'w')
        file_obj.write(full_string)
        file_obj.close()
    except OSError:
        log_error('(OSError) exception in fs_write_str_list_to_file()')
        log_error('Cannot write {0} file'.format(export_FN.getBase()))
        raise AddonException('(OSError) Cannot write {0} file'.format(export_FN.getBase()))
    except IOError:
        log_error('(IOError) exception in fs_write_str_list_to_file()')
        log_error('Cannot write {0} file'.format(export_FN.getBase()))
        raise AddonException('(IOError) Cannot write {0} file'.format(export_FN.getBase()))

# -------------------------------------------------------------------------------------------------
# Generic XML load/writer.
# -------------------------------------------------------------------------------------------------
def fs_get_XML_root_from_str(data_str):
    root = None
    try:
        root = ET.fromstring(data_str)
    except ET.ParseError as e:
        log_error('fs_load_XML_root_from_str() (ParseError) Exception parsing XML categories.xml')
        log_error('fs_load_XML_root_from_str() (ParseError) {0}'.format(str(e)))
        kodi_dialog_OK('(XML ParseError) Exception reading categories.xml. '
                       'Maybe XML file is corrupt or contains invalid characters.')

    return root

#
# Return a pretty-printed XML string for the Element.
# See https://stackoverflow.com/questions/17402323/use-xml-etree-elementtree-to-print-nicely-formatted-xml-files/17402424
#
def fs_get_str_from_XML_root(xml_root):
    rough_string = ET.tostring(xml_root, 'utf-8')
    reparsed = xml.dom.minidom.parseString(rough_string)
    data_str = reparsed.toprettyxml(indent = "  ")

    return data_str

# -------------------------------------------------------------------------------------------------
# Generic JSON loader/writer
# -------------------------------------------------------------------------------------------------
# Look at the ROMs JSON code for reference/comments to these functions.
def fs_write_JSON_file(file_dir, file_base_noext, data):
    # >> Get file names
    json_file = file_dir.pjoin(file_base_noext + '.json')
    log_verb('fs_write_JSON_file() Dir  {0}'.format(file_dir.getPath()))
    log_verb('fs_write_JSON_file() JSON {0}'.format(file_base_noext + '.json'))

    try:
        json_data = json.dumps(data, ensure_ascii = False, sort_keys = True, 
                                indent = JSON_indent, separators = JSON_separators)
        json_file.writeAll(unicode(json_data).encode("utf-8"))
    except OSError:
        kodi_notify_warn('(OSError) Cannot write {0} file'.format(json_file.getPath()))
    except IOError:
        kodi_notify_warn('(IOError) Cannot write {0} file'.format(json_file.getPath()))

def fs_load_JSON_file(file_dir, file_base_noext):
    data = {}

    # --- If file does not exist return empty dictionary ---
    json_file = file_dir.pjoin(file_base_noext + '.json')
    if not json_file.exists(): return data

    # --- Parse using json module ---
    log_verb('fs_load_JSON_file() Dir  {0}'.format(file_dir.getPath()))
    log_verb('fs_load_JSON_file() JSON {0}'.format(file_base_noext + '.json'))
   
    try:
        data = json_file.readJson()
    except ValueError:
        statinfo = json_file.stat()
        log_error('fs_load_JSON_file() ValueError exception in json.load() function')
        log_error('fs_load_JSON_file() Dir  {0}'.format(file_dir.getPath()))
        log_error('fs_load_JSON_file() File {0}'.format(file_base_noext + '.json'))
        log_error('fs_load_JSON_file() Size {0}'.format(statinfo.st_size))

    return data

# -------------------------------------------------------------------------------------------------
# Standard ROM databases
# -------------------------------------------------------------------------------------------------
#
# <roms_base_noext>.json
# <roms_base_noext>.xml
# <roms_base_noext>_index_CParent.json
# <roms_base_noext>_index_PClone.json
# <roms_base_noext>_parents.json
# <roms_base_noext>_DAT.json
#
# DEPRECATED - using RomSetRepository for this
def fs_unlink_ROMs_database(roms_dir_FN, launcher):
    roms_base_noext = launcher['roms_base_noext']

    # >> Delete ROMs JSON file
    roms_json_FN = roms_dir_FN.pjoin(roms_base_noext + '.json')
    if roms_json_FN.exists():
        log_info('Deleting ROMs JSON    "{0}"'.format(roms_json_FN.getPath()))
        roms_json_FN.unlink()

    # >> Delete ROMs info XML file
    roms_xml_FN = roms_dir_FN.pjoin(roms_base_noext + '.xml')
    if roms_xml_FN.exists():
        log_info('Deleting ROMs XML     "{0}"'.format(roms_xml_FN.getPath()))
        roms_xml_FN.unlink()

    # >> Delete No-Intro/Redump stuff if exist
    roms_index_CParent_FN = roms_dir_FN.pjoin(roms_base_noext + '_index_CParent.json')
    if roms_index_CParent_FN.exists():
        log_info('Deleting CParent JSON "{0}"'.format(roms_index_CParent_FN.getPath()))
        roms_index_CParent_FN.unlink()

    roms_index_PClone_FN = roms_dir_FN.pjoin(roms_base_noext + '_index_PClone.json')
    if roms_index_PClone_FN.exists():
        log_info('Deleting PClone JSON  "{0}"'.format(roms_index_PClone_FN.getPath()))
        roms_index_PClone_FN.unlink()

    roms_parents_FN = roms_dir_FN.pjoin(roms_base_noext + '_parents.json')
    if roms_parents_FN.exists():
        log_info('Deleting parents JSON "{0}"'.format(roms_parents_FN.getPath()))
        roms_parents_FN.unlink()

    roms_DAT_FN = roms_dir_FN.pjoin(roms_base_noext + '_DAT.json')
    if roms_DAT_FN.exists():
        log_info('Deleting DAT JSON     "{0}"'.format(roms_DAT_FN.getPath()))
        roms_DAT_FN.unlink()

def fs_rename_ROMs_database(roms_dir_FN, old_roms_base_noext, new_roms_base_noext):
    # >> Only rename if base names are different
    log_debug('fs_rename_ROMs_database() old_roms_base_noext "{0}"'.format(old_roms_base_noext))
    log_debug('fs_rename_ROMs_database() new_roms_base_noext "{0}"'.format(new_roms_base_noext))
    if old_roms_base_noext == new_roms_base_noext:
        log_debug('fs_rename_ROMs_database() Exiting because old and new names are equal')
        return

    old_roms_json_FN          = roms_dir_FN.pjoin(old_roms_base_noext + '.json')
    old_roms_xml_FN           = roms_dir_FN.pjoin(old_roms_base_noext + '.xml')
    old_roms_index_CParent_FN = roms_dir_FN.pjoin(old_roms_base_noext + '_index_CParent.json')
    old_roms_index_PClone_FN  = roms_dir_FN.pjoin(old_roms_base_noext + '_index_PClone.json')
    old_roms_parents_FN       = roms_dir_FN.pjoin(old_roms_base_noext + '_parents.json')
    old_roms_DAT_FN           = roms_dir_FN.pjoin(old_roms_base_noext + '_DAT.json')

    new_roms_json_FN          = roms_dir_FN.pjoin(new_roms_base_noext + '.json')
    new_roms_xml_FN           = roms_dir_FN.pjoin(new_roms_base_noext + '.xml')
    new_roms_index_CParent_FN = roms_dir_FN.pjoin(new_roms_base_noext + '_index_CParent.json')
    new_roms_index_PClone_FN  = roms_dir_FN.pjoin(new_roms_base_noext + '_index_PClone.json')
    new_roms_parents_FN       = roms_dir_FN.pjoin(new_roms_base_noext + '_parents.json')
    new_roms_DAT_FN           = roms_dir_FN.pjoin(new_roms_base_noext + '_DAT.json')

    # >> Only rename files if originals found.
    if old_roms_json_FN.exists():
        old_roms_json_FN.rename(new_roms_json_FN)
        log_debug('RENAMED OP {0}'.format(old_roms_json_FN.getPath()))
        log_debug('   into OP {0}'.format(new_roms_json_FN.getPath()))

    if old_roms_xml_FN.exists():
        old_roms_xml_FN.rename(new_roms_xml_FN)
        log_debug('RENAMED OP {0}'.format(old_roms_xml_FN.getPath()))
        log_debug('   into OP {0}'.format(new_roms_xml_FN.getPath()))

    if old_roms_index_CParent_FN.exists():
        old_roms_index_CParent_FN.rename(new_roms_index_CParent_FN)
        log_debug('RENAMED OP {0}'.format(old_roms_index_CParent_FN.getPath()))
        log_debug('   into OP {0}'.format(new_roms_index_CParent_FN.getPath()))

    if old_roms_index_PClone_FN.exists():
        old_roms_index_PClone_FN.rename(new_roms_index_PClone_FN)
        log_debug('RENAMED OP {0}'.format(old_roms_index_PClone_FN.getPath()))
        log_debug('   into OP {0}'.format(new_roms_index_PClone_FN.getPath()))

    if old_roms_parents_FN.exists():
        old_roms_parents_FN.rename(new_roms_parents_FN)
        log_debug('RENAMED OP {0}'.format(old_roms_parents_FN.getPath()))
        log_debug('   into OP {0}'.format(new_roms_parents_FN.getPath()))

    if old_roms_DAT_FN.exists():
        old_roms_DAT_FN.rename(new_roms_DAT_FN)
        log_debug('RENAMED OP {0}'.format(old_roms_DAT_FN.getPath()))
        log_debug('   into OP {0}'.format(new_roms_DAT_FN.getPath()))

def fs_write_ROMs_JSON(roms_dir_FN, launcher, roms):
    # >> Get file names
    roms_base_noext = launcher['roms_base_noext']
    roms_json_file = roms_dir_FN.pjoin(roms_base_noext + '.json')
    roms_xml_file  = roms_dir_FN.pjoin(roms_base_noext + '.xml')
    log_verb('fs_write_ROMs_JSON() Dir  {0}'.format(roms_dir_FN.getPath()))
    log_verb('fs_write_ROMs_JSON() JSON {0}'.format(roms_json_file.getPath()))
    log_verb('fs_write_ROMs_JSON() XML  {0}'.format(roms_xml_file.getPath()))

    # >> JSON files cannot have comments. Write an auxiliar NFO file with same prefix
    # >> to store launcher information for a set of ROMs
    try:
        str_list = []
        str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        str_list.append('<advanced_emulator_launcher_ROMs version="{0}">\n'.format(AEL_STORAGE_FORMAT))

        # Print some information in the XML so the user can now which launcher created it.
        # Note that this is ignored when reading the file.
        str_list.append('<launcher>\n')
        str_list.append(text_XML_line('id', launcher['id']))
        str_list.append(text_XML_line('m_name', launcher['m_name']))
        str_list.append(text_XML_line('categoryID', launcher['categoryID']))
        str_list.append(text_XML_line('platform', launcher['platform']))
        str_list.append(text_XML_line('rompath', launcher['rompath']))
        str_list.append(text_XML_line('romext', launcher['romext']))
        str_list.append('</launcher>\n')
        str_list.append('</advanced_emulator_launcher_ROMs>\n')

        full_string = ''.join(str_list).encode('utf-8')
        roms_xml_file.writeAll(full_string)
    except OSError:
        kodi_notify_warn('(OSError) Cannot write {0} file'.format(roms_xml_file.getPath()))
        log_error('fs_write_ROMs_JSON() (OSerror) Cannot write file "{0}"'.format(roms_xml_file.getPath()))
    except IOError:
        kodi_notify_warn('(IOError) Cannot write {0} file'.format(roms_xml_file.getPath()))
        log_error('fs_write_ROMs_JSON() (IOError) Cannot write file "{0}"'.format(roms_xml_file.getPath()))

    # >> Write ROMs JSON dictionary.
    # >> Do note that there is a bug in the json module where the ensure_ascii=False flag can produce
    # >> a mix of unicode and str objects.
    # >> See http://stackoverflow.com/questions/18337407/saving-utf-8-texts-in-json-dumps-as-utf8-not-as-u-escape-sequence
    try:

        # >> json_unicode is either str or unicode
        # >> See https://docs.python.org/2.7/library/json.html#json.dumps
        # unicode(json_data) auto-decodes data to unicode if str
        json_data = json.dumps(roms, ensure_ascii = False, sort_keys = True,
                                indent = JSON_indent, separators = JSON_separators)

        roms_json_file.writeAll(unicode(json_data).encode("utf-8"))
    except OSError:
        kodi_notify_warn('(OSError) Cannot write {0} file'.format(roms_json_file.getPath()))
        log_error('fs_write_ROMs_JSON() (OSError) Cannot write {0} file'.format(roms_json_file.getPath()))
    except IOError:
        kodi_notify_warn('(IOError) Cannot write {0} file'.format(roms_json_file.getPath()))
        log_error('fs_write_ROMs_JSON() (IOError) Cannot write {0} file'.format(roms_json_file.getPath()))

#
# Loads an JSON file containing the Virtual Launcher ROMs
#
def fs_load_ROMs_JSON(roms_dir_FN, launcher):
    roms = {}

    # --- If file does not exist return empty dictionary ---
    roms_base_noext = launcher['roms_base_noext']
    roms_json_file = roms_dir_FN.pjoin(roms_base_noext + '.json')
    if not roms_json_file.exists(): return roms

    # --- Parse using json module ---
    # >> On Github issue #8 a user had an empty JSON file for ROMs. This raises
    #    exception exceptions.ValueError and launcher cannot be deleted. Deal
    #    with this exception so at least launcher can be rescanned.
    log_verb('fs_load_ROMs_JSON() Dir  {0}'.format(roms_dir_FN.getPath()))
    log_verb('fs_load_ROMs_JSON() JSON {0}'.format(roms_base_noext + '.json'))
    try:
        roms = roms_json_file.readJson()
    except ValueError:
        statinfo = roms_json_file.stat()
        log_error('fs_load_ROMs_JSON() ValueError exception in json.load() function')
        log_error('fs_load_ROMs_JSON() Dir  {0}'.format(roms_dir_FN.getPath()))
        log_error('fs_load_ROMs_JSON() File {0}'.format(roms_base_noext + '.json'))
        log_error('fs_load_ROMs_JSON() Size {0}'.format(statinfo.st_size))

    return roms

# -------------------------------------------------------------------------------------------------
# Favourite ROMs
# -------------------------------------------------------------------------------------------------
#
# Save Favourites JSON file
#
def fs_write_Favourites_JSON(roms_json_file, roms):
    log_info('fs_write_Favourites_JSON() File {0}'.format(roms_json_file.getPath()))

    # --- Create JSON data structure, including version number ---
    control_dic = {
        'control' : 'Advanced Emulator Launcher Favourite ROMs',
        'version' : AEL_STORAGE_FORMAT
    }
    raw_data = []
    raw_data.append(control_dic)
    raw_data.append(roms)

    # --- Write JSON file ---
    try:
        roms_json_file.writeJson(raw_data)
    except OSError:
        kodi_notify_warn('(OSError) Cannot write {0} file'.format(roms_json_file.getPath()))
    except IOError:
        kodi_notify_warn('(IOError) Cannot write {0} file'.format(roms_json_file.getPath()))

#
# Loads an JSON file containing the Favourite ROMs
#
def fs_load_Favourites_JSON(roms_json_file):
    # --- If file does not exist return empty dictionary ---
    log_verb('fs_load_Favourites_JSON() File {0}'.format(roms_json_file.getPath()))
    if not roms_json_file.exists(): 
        return {}

    # --- Parse JSON ---  
    try:
        raw_data = roms_json_file.readJson()
    except ValueError:
        statinfo = roms_json_file.stat()
        log_error('fs_load_Favourites_JSON() ValueError exception in json.load() function')
        log_error('fs_load_Favourites_JSON() File {0}'.format(roms_json_file.getPath()))
        log_error('fs_load_Favourites_JSON() Size {0}'.format(statinfo.st_size))
        return {}

    # --- Extract roms from JSON data structe and ensure version is correct ---
    control_str = raw_data[0]['control']
    version_int = raw_data[0]['version']
    roms        = raw_data[1]

    return roms

# -------------------------------------------------------------------------------------------------
# ROM Collections
# -------------------------------------------------------------------------------------------------
def fs_write_Collection_index_XML(collections_xml_file, collections):
    log_info('fs_write_Collection_index_XML() File {0}'.format(collections_xml_file.getPath()))
    try:
        str_list = []
        str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        str_list.append('<advanced_emulator_launcher_Collection_index version="{0}">\n'.format(AEL_STORAGE_FORMAT))

        # --- Control information ---
        _t = time.time()
        str_list.append('<control>\n')
        str_list.append(text_XML_line('update_timestamp', unicode(_t)))
        str_list.append('</control>\n')

        # --- Virtual Launchers ---
        for collection_id in sorted(collections, key = lambda x : collections[x]['m_name']):
            collection = collections[collection_id]
            str_list.append('<Collection>\n')
            str_list.append(text_XML_line('id', collection['id']))
            str_list.append(text_XML_line('m_name', collection['m_name']))
            str_list.append(text_XML_line('m_genre', collection['m_genre']))
            str_list.append(text_XML_line('m_rating', collection['m_rating']))
            str_list.append(text_XML_line('m_plot', collection['m_plot']))
            str_list.append(text_XML_line('roms_base_noext', collection['roms_base_noext']))
            str_list.append(text_XML_line('default_icon', collection['default_icon']))
            str_list.append(text_XML_line('default_fanart', collection['default_fanart']))
            str_list.append(text_XML_line('default_banner', collection['default_banner']))
            str_list.append(text_XML_line('default_poster', collection['default_poster']))
            str_list.append(text_XML_line('default_clearlogo', collection['default_clearlogo']))
            str_list.append(text_XML_line('s_icon', collection['s_icon']))
            str_list.append(text_XML_line('s_fanart', collection['s_fanart']))
            str_list.append(text_XML_line('s_banner', collection['s_banner']))
            str_list.append(text_XML_line('s_poster', collection['s_poster']))
            str_list.append(text_XML_line('s_clearlogo', collection['s_clearlogo']))
            str_list.append(text_XML_line('s_trailer', collection['s_trailer']))
            str_list.append('</Collection>\n')
        str_list.append('</advanced_emulator_launcher_Collection_index>\n')
        full_string = ''.join(str_list).encode('utf-8')
        collections_xml_file.writeAll(full_string)
    except OSError:
        kodi_notify_warn('(OSError) Cannot write {0} file'.format(collections_xml_file.getPath()))
    except IOError:
        kodi_notify_warn('(IOError) Cannot write {0} file'.format(collections_xml_file.getPath()))

def fs_load_Collection_index_XML(collections_xml_FN):
    __debug_xml_parser = 0
    update_timestamp = 0.0
    collections = {}

    # --- If file does not exist return empty dictionary ---
    if not collections_xml_FN.exists(): return (collections, update_timestamp)

    # --- Parse using XML ---
    log_verb('fs_load_Collection_index_XML() Loading {0}'.format(collections_xml_FN.getPath()))
    xml_file_str = collections_xml_FN.loadFileToStr()
    try:
        xml_root = fs_get_XML_root_from_str(xml_file_str)
    # NOTE generic exception must be used here. Do not use ElementTree exceptions because
    # fs_get_XML_root_from_str() can use other library than ElementTree.
    except ET.ParseError as e:
        log_error('(ParseError) Exception parsing XML categories.xml')
        log_error('(ParseError) {0}'.format(str(e)))
        return (collections, update_timestamp)

    for root_element in xml_root:
        if __debug_xml_parser: log_debug('Root child {0}'.format(root_element.tag))

        if root_element.tag == 'control':
            for control_child in root_element:
                if control_child.tag == 'update_timestamp':
                    update_timestamp = float(control_child.text) # Convert Unicode to float

        elif root_element.tag == 'Collection':
            collection = fs_new_collection()
            for rom_child in root_element:
                # >> By default read strings
                text_XML_line = rom_child.text if rom_child.text is not None else ''
                text_XML_line = text_unescape_XML(text_XML_line)
                xml_tag  = rom_child.tag
                if __debug_xml_parser: log_debug('{0} --> {1}'.format(xml_tag, text_XML_line))
                collection[xml_tag] = text_XML_line
            collections[collection['id']] = collection

    return (collections, update_timestamp)

def fs_write_Collection_ROMs_JSON(roms_json_file, roms):
    log_verb('fs_write_Collection_ROMs_JSON() File {0}'.format(roms_json_file.getPath()))

    control_dic = {
        'control' : 'Advanced Emulator Launcher Collection ROMs',
        'version' : AEL_STORAGE_FORMAT
    }
    raw_data = []
    raw_data.append(control_dic)
    raw_data.append(roms)

    try:
        roms_json_file.writeJson(raw_data)
    except OSError:
        kodi_notify_warn('(OSError) Cannot write {0} file'.format(roms_json_file.getPath()))
    except IOError:
        kodi_notify_warn('(IOError) Cannot write {0} file'.format(roms_json_file.getPath()))

#
# Loads an JSON file containing the Virtual Launcher ROMs
# WARNING Collection ROMs are a list, not a dictionary
#
def fs_load_Collection_ROMs_JSON(roms_json_file):
    # --- If file does not exist return empty list ---
    if not roms_json_file.exists():
        return []

    # --- Parse using JSON ---
    log_verb('fs_load_Collection_ROMs_JSON() {0}'.format(roms_json_file.getPath()))
        
    try:
        raw_data = roms_json_file.readJson()
    except ValueError:
        statinfo = roms_json_file.stat()
        log_error('fs_load_Collection_ROMs_JSON() ValueError exception in json.load() function')
        log_error('fs_load_Collection_ROMs_JSON() File {0}'.format(roms_json_file.getPath()))
        log_error('fs_load_Collection_ROMs_JSON() Size {0}'.format(statinfo.st_size))
        return []
    
    # --- Extract roms from JSON data structe and ensure version is correct ---
    control_str = raw_data[0]['control']
    version_int = raw_data[0]['version']
    roms        = raw_data[1]

    return roms

def fs_export_ROM_collection(output_filename, collection, collection_rom_list):
    log_info('fs_export_ROM_collection() File {0}'.format(output_filename.getPath()))
    
    control_dic = {
        'control' : 'Advanced Emulator Launcher Collection ROMs',
        'version' : AEL_STORAGE_FORMAT
    }
    collection_dic = {
        'id'                : collection['id'],
        'm_name'            : collection['m_name'],
        'm_genre'           : collection['m_genre'],
        'm_rating'          : collection['m_rating'],
        'm_plot'            : collection['m_plot'],
        'default_icon'      : collection['default_icon'],
        'default_fanart'    : collection['default_fanart'],
        'default_banner'    : collection['default_banner'],
        'default_poster'    : collection['default_poster'],
        'default_clearlogo' : collection['default_clearlogo'],
        's_icon'            : collection['s_icon'],
        's_fanart'          : collection['s_fanart'],
        's_banner'          : collection['s_banner'],
        's_poster'          : collection['s_poster'],
        's_clearlogo'       : collection['s_clearlogo'],
        's_trailer'         : collection['s_trailer']
    }
    raw_data = []
    raw_data.append(control_dic)
    raw_data.append(collection_dic)
    raw_data.append(collection_rom_list)

    # >> Produce nicely formatted JSON when exporting
    try:
        output_filename.writeJson(raw_data, 2,  (', ', ' : '))
    except OSError:
        kodi_notify_warn('(OSError) Cannot write {0} file'.format(output_filename.getPath()))
    except IOError:
        kodi_notify_warn('(IOError) Cannot write {0} file'.format(output_filename.getPath()))

#
# Export collection assets. Use base64 encoding to store binary files in JSON.
# output_FileName          -> Unicode string
# collection               -> dictionary
# collection_rom_list      -> list of dictionaries
# collections_asset_dir_FN -> FileName object of self.settings['collections_asset_dir']
#
def fs_export_ROM_collection_assets(output_FileName, collection, collection_rom_list, collections_asset_dir_FN):
    log_info('fs_export_ROM_collection_assets() File {0}'.format(output_FileName.getPath()))

    control_dic = {
        'control' : 'Advanced Emulator Launcher Collection ROM assets',
        'version' : AEL_STORAGE_FORMAT
    }

    # --- Export Collection assets ---
    assets_dic = {}
    log_debug('fs_export_ROM_collection_assets() Exporting Collecion assets')
    for asset_kind in CATEGORY_ASSET_ID_LIST:
        AInfo    = assets_get_info_scheme(asset_kind)
        asset_FN = FileName.create(collection[AInfo.key])
        if not collection[AInfo.key]:
            log_debug('{0:<9s} not set'.format(AInfo.name))
            continue
        elif not asset_FN.exists():
            log_error('{0:<9s} not found "{1}"'.format(AInfo.name, asset_FN.getPath()))
            log_error('{0:<9s} ignoring'.format(AInfo.name))
            continue
        elif asset_FN.getDir() != collections_asset_dir_FN.getPath():
            log_error('{0:<9s} not in ROM Collection asset dir! This is not supposed to happen!'.format(AInfo.name))
            continue
        # >> Read image binary data and encode
        log_debug('{0:<9s} Adding to assets dictionary with key "{1}"'.format(AInfo.name, asset_FN.getBase_noext()))
        with open(asset_FN.getPath(), mode = 'rb') as file: # b is important -> binary
            fileData = file.read()
            fileData_base64 = base64.b64encode(fileData)
            statinfo = asset_FN.stat()
            file_size = statinfo.st_size
            a_dic = {'basename' : asset_FN.getBase(), 'filesize' : file_size, 'data' : fileData_base64}
            assets_dic[asset_FN.getBase_noext()] = a_dic

    # --- Export ROM assets ---
    # key -> basename : value { 'filesize' : int, 'data' : string }
    log_debug('fs_export_ROM_collection_assets() Exporting ROM assets')
    for rom_item in collection_rom_list:
        log_debug('fs_export_ROM_collection_assets() ROM "{0}"'.format(rom_item['m_name']))
        for asset_kind in ROM_ASSET_LIST:
            AInfo    = assets_get_info_scheme(asset_kind)
            asset_FN = FileNameFactory.create(rom_item[AInfo.key])
            if not rom_item[AInfo.key]:
                log_debug('{0:<9s} not set'.format(AInfo.name))
                continue
            elif not asset_FN.exists():
                log_error('{0:<9s} not found "{1}"'.format(AInfo.name, asset_FN.getPath()))
                log_error('{0:<9s} ignoring'.format(AInfo.name))
                continue
            elif asset_FN.getDir() != collections_asset_dir_FN.getPath():
                log_error('{0:<9s} not in ROM Collection asset dir! This is not supposed to happen!'.format(AInfo.name))
                continue
            # >> Read image binary data and encode
            log_debug('{0:<9s} Adding to assets dictionary with key "{1}"'.format(AInfo.name, asset_FN.getBase_noext()))
            with open(asset_FN.getPath(), mode = 'rb') as file: # b is important -> binary
                fileData = file.read()
            fileData_base64 = base64.b64encode(fileData)
            statinfo = asset_FN.stat()
            file_size = statinfo.st_size
            a_dic = {'basename' : asset_FN.getBase(), 'filesize' : file_size, 'data' : fileData_base64}
            assets_dic[asset_FN.getBase_noext()] = a_dic
            log_error('{0:<9s} exported/encoded'.format(AInfo.name))

    raw_data = []
    raw_data.append(control_dic)
    raw_data.append(assets_dic)

    # >> Produce nicely formatted JSON when exporting
    try:
        output_FileName.writeJson(raw_data, 2, (', ', ' : '))
    except OSError:
        kodi_notify_warn('(OSError) Cannot write {0} file'.format(output_FileName.getPath()))
    except IOError:
        kodi_notify_warn('(IOError) Cannot write {0} file'.format(output_FileName.getPath()))

#
# See fs_export_ROM_collection() function.
# Returns a tuple (control_dic, collection_dic, collection_rom_list)
#
def fs_import_ROM_collection(input_FileName):
    default_return = ({}, {}, [])

    # --- Parse using JSON ---
    log_info('fs_import_ROM_collection() Loading {0}'.format(input_FileName.getPath()))
    if not input_FileName.exists(): return default_return

    try:
        raw_data = input_FileName.readJson()
    except ValueError:
        statinfo = input_FileName.stat()
        log_error('fs_import_ROM_collection() ValueError exception in json.load() function')
        log_error('fs_import_ROM_collection() File {0}'.format(input_FileName.getPath()))
        log_error('fs_import_ROM_collection() Size {0}'.format(statinfo.st_size))
        return default_return

    # --- Extract roms from JSON data structe and ensure version is correct ---
    try:
        control_dic         = raw_data[0]
        collection_dic      = raw_data[1]
        collection_rom_list = raw_data[2]
        control_str         = control_dic['control']
        version_int         = control_dic['version']
    except:
        log_error('fs_import_ROM_collection() Exception unpacking ROM Collection data')
        log_error('fs_import_ROM_collection() Empty ROM Collection returned')
        return default_return

    return (control_dic, collection_dic, collection_rom_list)

#
# Returns a tuple (control_dic, assets_dic)
#
def fs_import_ROM_collection_assets(input_FileName):
    default_return = ({}, {})
    if not input_FileName.exists(): return default_return

    # --- Parse using JSON ---
    log_info('fs_import_ROM_collection_assets() Loading {0}'.format(input_FileName.getPath()))

    try:
        raw_data = input_FileName.readJson()
    except ValueError:
        statinfo = input_FileName.stat()
        log_error('fs_import_ROM_collection_assets() ValueError exception in json.load() function')
        log_error('fs_import_ROM_collection_assets() File {0}'.format(input_FileName.getPath()))
        log_error('fs_import_ROM_collection_assets() Size {0}'.format(statinfo.st_size))
        return default_return

    # --- Extract roms from JSON data structe and ensure version is correct ---
    control_dic = raw_data[0]
    assets_dic  = raw_data[1]
    control_str = control_dic['control']
    version_int = control_dic['version']

    return (control_dic, assets_dic)

#
# Returns:
# -1    ROM not found in list
# >= 0  ROM index in list
#
def fs_collection_ROM_index_by_romID(romID, collection_rom_list):
    current_ROM_position = -1
    for idx, rom in enumerate(collection_rom_list):
        if romID == rom['id']:
            current_ROM_position = idx
            break

    return current_ROM_position

# -------------------------------------------------------------------------------------------------
# Virtual Categories
# -------------------------------------------------------------------------------------------------
def fs_write_VCategory_XML(roms_xml_file, roms):
    log_info('fs_write_VCategory_XML() Saving XML file {0}'.format(roms_xml_file.getPath()))
    try:
        str_list = []
        str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        str_list.append('<advanced_emulator_launcher_Virtual_Category_index version="{0}">\n'.format(AEL_STORAGE_FORMAT))

        # --- Control information ---
        _t = time.time()
        str_list.append('<control>\n')
        str_list.append(text_XML_line('update_timestamp', unicode(_t)))
        str_list.append('</control>\n')

        # --- Virtual Launchers ---
        for romID in sorted(roms, key = lambda x : roms[x]['name']):
            rom = roms[romID]
            str_list.append('<VLauncher>\n')
            str_list.append(text_XML_line('id', romID))
            str_list.append(text_XML_line('name', rom['name']))
            str_list.append(text_XML_line('rom_count', rom['rom_count']))
            str_list.append(text_XML_line('roms_base_noext', rom['roms_base_noext']))
            str_list.append('</VLauncher>\n')
        str_list.append('</advanced_emulator_launcher_Virtual_Category_index>\n')
        full_string = ''.join(str_list).encode('utf-8')
        roms_xml_file.writeAll(full_string)
    except OSError:
        kodi_notify_warn('(OSError) Cannot write {0} file'.format(roms_xml_file.getPath()))
    except IOError:
        kodi_notify_warn('(IOError) Cannot write {0} file'.format(roms_xml_file.getPath()))

#
# Loads an XML file containing Virtual Launcher indices
# It is basically the same as ROMs, but with some more fields to store launching application data.
#
def fs_load_VCategory_XML(roms_xml_file):
    __debug_xml_parser = 0
    update_timestamp = 0.0
    VLaunchers = {}

    # --- If file does not exist return empty dictionary ---
    if not roms_xml_file.exists(): return (update_timestamp, VLaunchers)

    # --- Parse using cElementTree ---
    log_verb('fs_load_VCategory_XML() Loading XML file {0}'.format(roms_xml_file.getPath()))
    try:
        xml_root = roms_xml_file.readXml()
    except ET.ParseError as e:
        log_error('(ParseError) Exception parsing XML categories.xml')
        log_error('(ParseError) {0}'.format(str(e)))
        return (update_timestamp, VLaunchers)

    for root_element in xml_root:
        if __debug_xml_parser: log_debug('Root child {0}'.format(root_element.tag))

        if root_element.tag == 'control':
            for control_child in root_element:
                if control_child.tag == 'update_timestamp':
                    # >> Convert Unicode to float
                    update_timestamp = float(control_child.text)

        elif root_element.tag == 'VLauncher':
            # Default values
            VLauncher = {'id' : '', 'name' : '', 'rom_count' : '', 'roms_base_noext' : ''}
            for rom_child in root_element:
                # By default read strings
                text_XML_line = rom_child.text if rom_child.text is not None else ''
                text_XML_line = text_unescape_XML(text_XML_line)
                xml_tag  = rom_child.tag
                if __debug_xml_parser: log_debug('{0} --> {1}'.format(xml_tag, text_XML_line))
                VLauncher[xml_tag] = text_XML_line
            VLaunchers[VLauncher['id']] = VLauncher

    return (update_timestamp, VLaunchers)

#
# Write virtual category ROMs
#
def fs_write_VCategory_ROMs_JSON(roms_dir, roms_base_noext, roms):
    roms_json_file = roms_dir.pjoin(roms_base_noext + '.json')
    log_verb('fs_write_VCategory_ROMs_JSON() Saving JSON file {0}'.format(roms_json_file.getPath()))
    try:
        roms_json_file.writeJson(roms)
    except OSError:
        kodi_notify_warn('(OSError) Cannot write {0} file'.format(roms_json_file.getPath()))
    except IOError:
        kodi_notify_warn('(IOError) Cannot write {0} file'.format(roms_json_file.getPath()))

#
# Loads an JSON file containing the Virtual Launcher ROMs
#
def fs_load_VCategory_ROMs_JSON(roms_dir, roms_base_noext):
    # --- If file does not exist return empty dictionary ---
    roms_json_file = roms_dir.pjoin(roms_base_noext + '.json')
    if not roms_json_file.exists(): return {}

    # --- Parse using cElementTree ---
    log_verb('fs_load_VCategory_ROMs_JSON() Loading JSON file {0}'.format(roms_json_file.getPath()))
    try:
        roms = roms_json_file.readJson()
    except ValueError:
        statinfo = roms_json_file.stat()
        log_error('fs_load_VCategory_ROMs_JSON() ValueError exception in json.load() function')
        log_error('fs_load_VCategory_ROMs_JSON() Dir  {0}'.format(roms_dir.getPath()))
        log_error('fs_load_VCategory_ROMs_JSON() File {0}'.format(roms_base_noext + '.json'))
        log_error('fs_load_VCategory_ROMs_JSON() Size {0}'.format(statinfo.st_size))
        return {}

    return roms

# -------------------------------------------------------------------------------------------------
# Fixes launchers.xml invalid XML characters, if present.
# Both argument filenames must be Unicode strings.
# See tools/read_AL_launchers_XML.py for details of this function/
# -------------------------------------------------------------------------------------------------
def fs_fix_launchers_xml(launchers_xml_path, sanitized_xml_path):
    #
    # A) Read launcher.xml line by line
    # B) Substitute offending/unescaped XML characters
    # C) Write sanitized output XML
    #
    log_info('fs_fix_launchers_xml() Sanitizing AL launchers.xml...')
    log_info('fs_fix_launchers_xml() Input  {0}'.format(launchers_xml_path.getPath()))
    log_info('fs_fix_launchers_xml() Output {0}'.format(sanitized_xml_path.getPath()))
    with open(launchers_xml_path.getPath()) as f_in:
        lines = f_in.readlines()
    sanitized_xml_path.open('w')
    p = re.compile(r'^(\s+)<(.+?)>(.+)</\2>(\s+)')
    line_counter = 1
    for line in lines:
        # >> line is str, convert to Unicode
        line = line.decode('utf-8')

        # >> Filter lines of type \t\t<tag>text</tag>\n
        m = p.match(line)

        if m:
            start_blanks = m.group(1)
            tag          = m.group(2)
            string       = m.group(3)
            end_blanks   = m.group(4)

            # >> Escape standard XML characters
            # >> Escape common HTML stuff
            # >> &#xA; is line feed
            string = string.replace('&', '&amp;')      # Must be done first
            string = string.replace('<br>', '&#xA;')
            string = string.replace('<br />', '&#xA;')
            string = string.replace('"', '&quot;')
            string = string.replace("'", '&apos;')
            string = string.replace('<', '&lt;')
            string = string.replace('>', '&gt;')

            line = '{0}<{1}>{2}</{3}>{4}'.format(start_blanks, tag, string, tag, end_blanks)
            # log_debug('New line   "{0}"'.format(line.rstrip()))

        # >> Write line
        sanitized_xml_path.write(line.encode('utf-8'))
        line_counter += 1
    sanitized_xml_path.close()
    log_info('fs_fix_launchers_xml() Processed {0} XML lines'.format(line_counter))

# -------------------------------------------------------------------------------------------------
# Legacy AL launchers.xml parser
#
# Some users have made their own tools to generate launchers.xml. Ensure that all fields in official
# AL source are inisialised with correct default value.
# Look in resources/lib/launcher_plugin.py -> Main::_load_launchers()
# -------------------------------------------------------------------------------------------------
def fs_load_legacy_AL_launchers(AL_launchers_filepath, categories, launchers):
    __debug_xml_parser = True

    # --- Parse using ElementTree ---
    log_info('fs_load_legacy_AL_launchers() Loading "{0}"'.format(AL_launchers_filepath.getPath()))
    try:
        xml_root = AL_launchers_filepath.readXml()
    except ET.ParseError as e:
        log_error('ParseError exception parsing XML categories.xml')
        log_error('ParseError: {0}'.format(str(e)))
        kodi_notify_warn('ParseError exception reading launchers.xml')
        return

    for root_element in xml_root:
        log_debug('=== Root child tag "{0}" ==='.format(root_element.tag))
        if root_element.tag == 'categories':
            for category_element in root_element:
                log_debug('New Category')
                # >> Initialise correct default values
                category = {'id'       : '',
                            'name'     : '',
                            'thumb'    : '',
                            'fanart'   : '',
                            'genre'    : '',
                            'plot'     : '',
                            'finished' : 'false' }
                for category_child in category_element:
                    if category_child.tag == 'name': log_debug('Category name "{0}"'.format(category_child.text))
                    # >> ElementTree makes text = None if it's '' in the XML. Correct that
                    if category_child.text == None: category_child.text = ''
                    # >> Some fields have different dictionary key and XML tag!!!
                    # >> Translate accordingly
                    if category_child.tag == 'description': category_child.tag = 'plot'
                    category[category_child.tag] = category_child.text
                categories[category['id']] = category

        elif root_element.tag == 'launchers':
            for launcher_element in root_element:
                log_debug('New Launcher')
                # >> Initialise correct default values
                launcher = {'id'          : '',
                            'name'        : '',
                            'category'    : '',
                            'application' : '',
                            'args'        : '',
                            'rompath'     : '',
                            'thumbpath'   : '',
                            'fanartpath'  : '',
                            'trailerpath' : '',
                            'custompath'  : '',
                            'romext'      : '',
                            'gamesys'     : '',
                            'thumb'       : '',
                            'fanart'      : '',
                            'genre'       : '',
                            'release'     : '',
                            'studio'      : '',
                            'plot'        : '',
                            'finished'    : 'false',
                            'toggle_window' : 'false',
                            'lnk'         : 'false',
                            'roms'        : {} }
                for launcher_child in launcher_element:
                    if launcher_child.tag == 'name': log_debug('Launcher name "{0}"'.format(launcher_child.text))
                    if launcher_child.tag != 'roms':
                        # >> ElementTree makes text = None if it's '' in the XML. Correct that
                        if launcher_child.text == None: launcher_child.text = ''
                        # >> Some fields have different dictionary key and XML tag!!!
                        # >> Translate accordingly
                        if   launcher_child.tag == 'platform':     launcher_child.tag = 'gamesys'
                        elif launcher_child.tag == 'publisher':    launcher_child.tag = 'studio'
                        elif launcher_child.tag == 'launcherplot': launcher_child.tag = 'plot'
                        launcher[launcher_child.tag] = launcher_child.text
                    else:
                        roms = {}
                        roms_element = launcher_child
                        for rom_element in roms_element:
                            # >> Defaul AL ROM values
                            rom = {'id'       : '',
                                   'name'     : '',
                                   'filename' : '',
                                   'thumb'    : '',
                                   'fanart'   : '',
                                   'trailer'  : '',
                                   'custom'   : '',
                                   'genre'    : '',
                                   'release'  : '',
                                   'studio'   : '',
                                   'plot'     : '',
                                   'finished' : 'false',
                                   'altapp'   : '',
                                   'altarg'   : '' }
                            for rom_child in rom_element:
                                # >> ElementTree makes text = None if it's '' in the XML. Correct that
                                if rom_child.text == None: rom_child.text = ''
                                # >> Some fields have different dictionary key and XML tag!!!
                                # >> Translate accordingly
                                if   rom_child.tag == 'publisher': rom_child.tag = 'studio'
                                elif rom_child.tag == 'gameplot':  rom_child.tag = 'plot'
                                rom[rom_child.tag] = rom_child.text
                            roms[rom['id']] = rom
                        launcher['roms'] = roms
                launchers[launcher['id']] = launcher
                log_debug('Launcher has {0} ROMs'.format(len(launcher['roms'])))

# -------------------------------------------------------------------------------------------------
# NFO files
# -------------------------------------------------------------------------------------------------
#
# When called from "Edit ROM" --> "Edit Metadata" --> "Import metadata from NFO file" function
# should be verbose and print notifications.
# However, this function is also used to export launcher ROMs in bulk in
# "Edit Launcher" --> "Manage ROM List" --> "Export ROMs metadata to NFO files". In that case,
# function must not be verbose because it can be called thousands of times for big ROM sets!
#
def fs_export_ROM_NFO(rom, verbose = True):
    # >> Skip No-Intro Added ROMs. rom['filename'] will be empty.
    if not rom['filename']: return
    ROMFileName = FileNameFactory.create(rom['filename'])
    nfo_file_path = ROMFileName.switchExtension('.nfo')
    log_debug('fs_export_ROM_NFO() Exporting "{0}"'.format(nfo_file_path.getPath()))

    # Always overwrite NFO files.
    nfo_content = []
    nfo_content.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
    nfo_content.append('<!-- Exported by AEL on {0} -->\n'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
    nfo_content.append('<game>\n')
    nfo_content.append(text_XML_line('title',     rom['m_name']))
    nfo_content.append(text_XML_line('year',      rom['m_year']))
    nfo_content.append(text_XML_line('genre',     rom['m_genre']))
    nfo_content.append(text_XML_line('developer', rom['m_developer']))
    nfo_content.append(text_XML_line('nplayers',  rom['m_nplayers']))
    nfo_content.append(text_XML_line('esrb',      rom['m_esrb']))
    nfo_content.append(text_XML_line('rating',    rom['m_rating']))
    nfo_content.append(text_XML_line('plot',      rom['m_plot']))
    nfo_content.append('</game>\n')
    full_string = ''.join(nfo_content).encode('utf-8')
    try:
        nfo_folder = nfo_file_path.getDirAsFileName()
        nfo_folder.makedirs()

        nfo_file_path.writeAll(full_string)
    except:
        if verbose:
            kodi_notify_warn('Error writing {0}'.format(nfo_file_path.getPath()))
        log_error("fs_export_ROM_NFO() Exception writing '{0}'".format(nfo_file_path.getPath()))
        return
    if verbose:
        kodi_notify('Created NFO file {0}'.format(nfo_file_path.getPath()))

    return

#
# Reads an NFO file with ROM information.
# Modifies roms dictionary even outside this function. See comments in fs_import_launcher_NFO()
# See comments in fs_export_ROM_NFO() about verbosity.
# About reading files in Unicode http://stackoverflow.com/questions/147741/character-reading-from-file-in-python
#
# DEPRECATED METHOD - Not called anymore
def fs_import_ROM_NFO(roms, romID, verbose = True):
    ROMFileName = FileNameFactory.create(roms[romID]['filename'])
    nfo_file_path = ROMFileName.switchExtension('.nfo')
    log_debug('fs_import_ROM_NFO() Loading "{0}"'.format(nfo_file_path.getPath()))

    # --- Import data ---
    if ROMFileName.exists():
        # >> Read file, put in a string and remove line endings.
        # >> We assume NFO files are UTF-8. Decode data to Unicode.
        # file = open(nfo_file_path, 'rt')
        nfo_str = nfo_file_path.readAllUnicode()
        nfo_str = nfo_str.replace('\r', '').replace('\n', '')

        # Search for metadata tags. Regular expression is non-greedy.
        # See https://docs.python.org/2/library/re.html#re.findall
        # If RE has no groups it returns a list of strings with the matches.
        # If RE has groups then it returns a list of groups.
        item_title     = re.findall('<title>(.*?)</title>', nfo_str)
        item_year      = re.findall('<year>(.*?)</year>', nfo_str)
        item_genre     = re.findall('<genre>(.*?)</genre>', nfo_str)
        item_developer = re.findall('<developer>(.*?)</developer>', nfo_str)
        item_nplayers  = re.findall('<nplayers>(.*?)</nplayers>', nfo_str)
        item_esrb      = re.findall('<esrb>(.*?)</esrb>', nfo_str)
        item_rating    = re.findall('<rating>(.*?)</rating>', nfo_str)
        item_plot      = re.findall('<plot>(.*?)</plot>', nfo_str)

        # >> Future work: ESRB and maybe nplayer fields must be sanitized.
        if len(item_title) > 0:     roms[romID]['m_name']      = text_unescape_XML(item_title[0])
        if len(item_year) > 0:      roms[romID]['m_year']      = text_unescape_XML(item_year[0])
        if len(item_genre) > 0:     roms[romID]['m_genre']     = text_unescape_XML(item_genre[0])
        if len(item_developer) > 0: roms[romID]['m_developer'] = text_unescape_XML(item_developer[0])
        if len(item_nplayers) > 0:  roms[romID]['m_nplayers']  = text_unescape_XML(item_nplayers[0])
        if len(item_esrb) > 0:      roms[romID]['m_esrb']      = text_unescape_XML(item_esrb[0])
        if len(item_rating) > 0:    roms[romID]['m_rating']    = text_unescape_XML(item_rating[0])
        if len(item_plot) > 0:      roms[romID]['m_plot']      = text_unescape_XML(item_plot[0])

        if verbose:
            kodi_notify('Imported {0}'.format(nfo_file_path.getPath()))
    else:
        if verbose:
            kodi_notify_warn('NFO file not found {0}'.format(nfo_file_path.getPath()))
        log_debug("fs_import_ROM_NFO() NFO file not found '{0}'".format(nfo_file_path.getPath()))
        return False

    return True

#
# This file is called by the ROM scanner to read a ROM info file automatically.
# NFO file existence is checked before calling this function, so NFO file must always exist.
#
def fs_import_ROM_NFO_file_scanner(nfo_file_path):
    nfo_dic = {
        'title' : '', 'year' : '', 'genre' : '', 'developer' : '',
        'nplayers' : '', 'esrb' : '', 'rating' : '', 'plot' : ''
    }

    # >> Read file, put in a string and remove line endings
    nfo_str = nfo_file_path.readAllUnicode()
    nfo_str = nfo_str.replace('\r', '').replace('\n', '')

    # Search for items
    item_title     = re.findall('<title>(.*?)</title>', nfo_str)
    item_year      = re.findall('<year>(.*?)</year>', nfo_str)
    item_genre     = re.findall('<genre>(.*?)</genre>', nfo_str)
    item_developer = re.findall('<developer>(.*?)</developer>', nfo_str)
    item_nplayers  = re.findall('<nplayers>(.*?)</nplayers>', nfo_str)
    item_esrb      = re.findall('<esrb>(.*?)</esrb>', nfo_str)
    item_rating    = re.findall('<rating>(.*?)</rating>', nfo_str)
    item_plot      = re.findall('<plot>(.*?)</plot>', nfo_str)

    # >> Future work: ESRB and maybe nplayer fields must be sanitized.
    if len(item_title) > 0:     nfo_dic['title']     = text_unescape_XML(item_title[0])
    if len(item_year) > 0:      nfo_dic['year']      = text_unescape_XML(item_year[0])
    if len(item_genre) > 0:     nfo_dic['genre']     = text_unescape_XML(item_genre[0])
    if len(item_developer) > 0: nfo_dic['developer'] = text_unescape_XML(item_developer[0])
    if len(item_nplayers) > 0:  nfo_dic['nplayers']  = text_unescape_XML(item_nplayers[0])
    if len(item_esrb) > 0:      nfo_dic['esrb']      = text_unescape_XML(item_esrb[0])
    if len(item_rating) > 0:    nfo_dic['rating']    = text_unescape_XML(item_rating[0])
    if len(item_plot) > 0:      nfo_dic['plot']      = text_unescape_XML(item_plot[0])

    return nfo_dic

#
# Returns a FileName object
#
def fs_get_ROM_NFO_name(rom):
    ROMFileName = FileNameFactory.create(rom['filename'])
    nfo_file_path = FileNameFactory.create(ROMFileName.getPath_noext() + '.nfo')
    log_debug("fs_get_ROM_NFO_name() nfo_file_path = '{0}'".format(nfo_file_path.getPath()))

    return nfo_file_path

#
# Standalone launchers:
#   NFO files are stored in self.settings["launchers_nfo_dir"] if not empty.
#   If empty, it defaults to DEFAULT_LAUN_NFO_DIR.
#
# ROM launchers:
#   Same as standalone launchers.
#
def fs_export_launcher_NFO(nfo_FileName, launcher):
    # --- Get NFO file name ---
    log_debug('fs_export_launcher_NFO() Exporting launcher NFO "{0}"'.format(nfo_FileName.getPath()))

    # If NFO file does not exist then create them. If it exists, overwrite.
    nfo_content = []
    nfo_content.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
    nfo_content.append('<!-- Exported by AEL on {0} -->\n'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
    nfo_content.append('<launcher>\n')
    nfo_content.append(text_XML_line('year',      launcher['m_year']))
    nfo_content.append(text_XML_line('genre',     launcher['m_genre']))
    nfo_content.append(text_XML_line('developer', launcher['m_developer']))
    nfo_content.append(text_XML_line('rating',    launcher['m_rating']))
    nfo_content.append(text_XML_line('plot',      launcher['m_plot']))
    nfo_content.append('</launcher>\n')
    full_string = ''.join(nfo_content).encode('utf-8')
    try:
        nfo_FileName.writeAll(full_string)
    except:
        kodi_notify_warn('Exception writing NFO file {0}'.format(nfo_FileName.getPath()))
        log_error("fs_export_launcher_NFO() Exception writing'{0}'".format(nfo_FileName.getPath()))
        return False
    log_debug("fs_export_launcher_NFO() Created '{0}'".format(nfo_FileName.getPath()))

    return True

#
# Python data model: lists and dictionaries are mutable. It means the can be changed if passed as
# parameters of functions. However, items can not be replaced by new objects!
# Notably, numbers, strings and tuples are immutable. Dictionaries and lists are mutable.
#
# See http://stackoverflow.com/questions/986006/how-do-i-pass-a-variable-by-reference
# See https://docs.python.org/2/reference/datamodel.html
#
# Function asumes that the NFO file already exists.
# - moved to launcher
#def fs_import_launcher_NFO(nfo_FileName, launchers, launcherID):
#    # --- Get NFO file name ---
#    log_debug('fs_import_launcher_NFO() Importing launcher NFO "{0}"'.format(nfo_FileName.getPath()))
#
#    # --- Import data ---
#    if nfo_FileName.exists():
#        # >> Read NFO file data
#        try:
#            item_nfo = nfo_FileName.readAllUnicode()
#            item_nfo = item_nfo.replace('\r', '').replace('\n', '')
#        except:
#            kodi_notify_warn('Exception reading NFO file {0}'.format(nfo_FileName.getPath()))
#            log_error("fs_import_launcher_NFO() Exception reading NFO file '{0}'".format(nfo_FileName.getPath()))
#            return False
#        # log_debug("fs_import_launcher_NFO() item_nfo '{0}'".format(item_nfo))
#    else:
#        kodi_notify_warn('NFO file not found {0}'.format(nfo_FileName.getBase()))
#        log_info("fs_import_launcher_NFO() NFO file not found '{0}'".format(nfo_FileName.getPath()))
#        return False
#
#    # Find data
#    item_year      = re.findall('<year>(.*?)</year>',           item_nfo)
#    item_genre     = re.findall('<genre>(.*?)</genre>',         item_nfo)
#    item_developer = re.findall('<developer>(.*?)</developer>', item_nfo)
#    item_rating    = re.findall('<rating>(.*?)</rating>',       item_nfo)
#    item_plot      = re.findall('<plot>(.*?)</plot>',           item_nfo)
#
#    # >> Careful about object mutability! This should modify the dictionary
#    # >> passed as argument outside this function.
#    if item_year:      launchers[launcherID]['m_year']      = text_unescape_XML(item_year[0])
#    if item_genre:     launchers[launcherID]['m_genre']     = text_unescape_XML(item_genre[0])
#    if item_developer: launchers[launcherID]['m_developer'] = text_unescape_XML(item_developer[0])
#    if item_rating:    launchers[launcherID]['m_rating']    = text_unescape_XML(item_rating[0])
#    if item_plot:      launchers[launcherID]['m_plot']      = text_unescape_XML(item_plot[0])
#
#    log_verb("fs_import_launcher_NFO() Imported '{0}'".format(nfo_FileName.getPath()))
#
#    return True

#
# Used by autoconfig_import_launcher(). Returns a dictionary with the Launcher NFO file information.
# If there is any error return a dictionary with empty information.
#
def fs_read_launcher_NFO(nfo_FileName):
    launcher_dic = {'year' : '', 'genre' : '', 'developer' : '', 'rating' : '', 'plot' : ''}

    # --- Get NFO file name ---
    log_debug('fs_read_launcher_NFO() Importing launcher NFO "{0}"'.format(nfo_FileName.getPath()))

    # --- Import data ---
    if nfo_FileName.exists():
        # >> Read NFO file data
        try:
            item_nfo = nfo_FileName.readAllUnicode()
            item_nfo = item_nfo.replace('\r', '').replace('\n', '')
        except:
            kodi_notify_warn('Exception reading NFO file {0}'.format(nfo_FileName.getBase()))
            log_error("fs_read_launcher_NFO() Exception reading NFO file '{0}'".format(nfo_FileName.getPath()))
            return launcher_dic
    else:
        kodi_notify_warn('NFO file not found {0}'.format(nfo_FileName.getBase()))
        log_info("fs_read_launcher_NFO() NFO file not found '{0}'".format(nfo_FileName.getPath()))
        return launcher_dic

    # Find data
    item_year      = re.findall('<year>(.*?)</year>',           item_nfo)
    item_genre     = re.findall('<genre>(.*?)</genre>',         item_nfo)
    item_developer = re.findall('<developer>(.*?)</developer>', item_nfo)
    item_rating    = re.findall('<rating>(.*?)</rating>',       item_nfo)
    item_plot      = re.findall('<plot>(.*?)</plot>',           item_nfo)

    if item_year:      launcher_dic['year']      = text_unescape_XML(item_year[0])
    if item_genre:     launcher_dic['genre']     = text_unescape_XML(item_genre[0])
    if item_developer: launcher_dic['developer'] = text_unescape_XML(item_developer[0])
    if item_rating:    launcher_dic['rating']    = text_unescape_XML(item_rating[0])
    if item_plot:      launcher_dic['plot']      = text_unescape_XML(item_plot[0])

    log_verb("fs_read_launcher_NFO() Read '{0}'".format(nfo_FileName.getPath()))

    return launcher_dic

#
# Returns a FileName object
#
def fs_get_launcher_NFO_name(settings, launcher):
    launcher_name = launcher['m_name']
    nfo_dir = FileName(settings['launchers_asset_dir'], isdir = True)
    nfo_file_path = nfo_dir.pjoin(launcher_name + '.nfo')
    log_debug("fs_get_launcher_NFO_name() nfo_file_path = '{0}'".format(nfo_file_path.getPath()))

    return nfo_file_path

#
# Look at the Launcher NFO files for a reference implementation.
#
def fs_export_category_NFO(nfo_FileName, category):
    # --- Get NFO file name ---
    log_debug('fs_export_category_NFO() Exporting launcher NFO "{0}"'.format(nfo_FileName.getPath()))

    # If NFO file does not exist then create them. If it exists, overwrite.
    nfo_content = []
    nfo_content.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
    nfo_content.append('<!-- Exported by AEL on {0} -->\n'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
    nfo_content.append('<category>\n')
    nfo_content.append(text_XML_line('year',      category['m_year']))
    nfo_content.append(text_XML_line('genre',     category['m_genre'])) 
    nfo_content.append(text_XML_line('developer', category['m_developer']))
    nfo_content.append(text_XML_line('rating',    category['m_rating']))
    nfo_content.append(text_XML_line('plot',      category['m_plot']))
    nfo_content.append('</category>\n')
    full_string = ''.join(nfo_content).encode('utf-8')
    try:
        nfo_FileName.writeAll(full_string)
    except:
        kodi_notify_warn('Exception writing NFO file {0}'.format(nfo_FileName.getPath()))
        log_error("fs_export_category_NFO() Exception writing'{0}'".format(nfo_FileName.getPath()))
        return False
    log_debug("fs_export_category_NFO() Created '{0}'".format(nfo_FileName.getPath()))

    return True

def fs_import_category_NFO(nfo_FileName, category_data):
    # --- Get NFO file name ---
    log_debug('fs_import_category_NFO() Importing launcher NFO "{0}"'.format(nfo_FileName.getPath()))

    # --- Import data ---
    if nfo_FileName.exists():
        try:
            item_nfo = nfo_FileName.loadFileToStr()
            item_nfo = item_nfo.replace('\r', '').replace('\n', '')
        except:
            kodi_notify_warn('Exception reading NFO file {0}'.format(nfo_FileName.getPath()))
            log_error("fs_import_category_NFO() Exception reading NFO file '{0}'".format(nfo_FileName.getPath()))
            return False
    else:
        kodi_notify_warn('NFO file not found {0}'.format(nfo_FileName.getBase()))
        log_error("fs_import_category_NFO() NFO file not found '{0}'".format(nfo_FileName.getPath()))
        return False

    item_year      = re.findall('<year>(.*?)</year>',           item_nfo)
    item_genre     = re.findall('<genre>(.*?)</genre>',         item_nfo)
    item_developer = re.findall('<developer>(.*?)</developer>', item_nfo)
    item_rating    = re.findall('<rating>(.*?)</rating>',       item_nfo)
    item_plot      = re.findall('<plot>(.*?)</plot>',           item_nfo)

    if item_year:      category_data['m_year']      = text_unescape_XML(item_year[0])
    if item_genre:     category_data['m_genre']  = text_unescape_XML(item_genre[0])
    if item_developer: category_data['m_developer'] = text_unescape_XML(item_developer[0])
    if item_rating:    category_data['m_rating'] = text_unescape_XML(item_rating[0])
    if item_plot:      category_data['m_plot']   = text_unescape_XML(item_plot[0])

    log_verb("fs_import_category_NFO() Imported '{0}'".format(nfo_FileName.getPath()))

    return True

#
# Returns a FileName object
#
def fs_get_category_NFO_name(settings, category):
    category_name = category['m_name']
    nfo_dir = FileName(settings['categories_asset_dir'], isdir = True)
    nfo_file_path = nfo_dir.pjoin(category_name + '.nfo')
    log_debug("fs_get_category_NFO_name() nfo_file_path = '{0}'".format(nfo_file_path.getPath()))

    return nfo_file_path

#
# Collection NFO files. Same as Cateogory NFO files.
#
def fs_export_collection_NFO(nfo_FileName, collection):
    # --- Get NFO file name ---
    log_debug('fs_export_collection_NFO() Exporting launcher NFO "{0}"'.format(nfo_FileName.getPath()))

    # If NFO file does not exist then create them. If it exists, overwrite.
    nfo_content = []
    nfo_content.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
    nfo_content.append('<!-- Exported by AEL on {0} -->\n'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
    nfo_content.append('<collection>\n')
    nfo_content.append(text_XML_line('genre',  collection['m_genre']))
    nfo_content.append(text_XML_line('rating', collection['m_rating']))
    nfo_content.append(text_XML_line('plot',   collection['m_plot']))
    nfo_content.append('</collection>\n')
    full_string = ''.join(nfo_content).encode('utf-8')
    try:
        nfo_FileName.writeAll(full_string)
    except:
        kodi_notify_warn('Exception writing NFO file {0}'.format(nfo_FileName.getName()))
        log_error("fs_export_collection_NFO() Exception writing'{0}'".format(nfo_FileName.getPath()))
        return False
    log_debug("fs_export_collection_NFO() Created '{0}'".format(nfo_FileName.getPath()))

    return True

def fs_import_collection_NFO(nfo_FileName, collections, launcherID):
    # --- Get NFO file name ---
    log_debug('fs_import_collection_NFO() Importing launcher NFO "{0}"'.format(nfo_FileName.getPath()))

    # --- Import data ---
    if nfo_FileName.exists():
        try:
            item_nfo = nfo_FileName.loadFileToStr()
            item_nfo = item_nfo.replace('\r', '').replace('\n', '')
        except:
            kodi_notify_warn('Exception reading NFO file {0}'.format(nfo_FileName.getName()))
            log_error("fs_import_collection_NFO() Exception reading NFO file '{0}'".format(nfo_FileName.getPath()))
            return False
    else:
        kodi_notify_warn('NFO file not found {0}'.format(nfo_FileName.getBase()))
        log_error("fs_import_collection_NFO() NFO file not found '{0}'".format(nfo_FileName.getPath()))
        return False

    item_genre  = re.findall('<genre>(.*?)</genre>', item_nfo)
    item_rating = re.findall('<rating>(.*?)</rating>', item_nfo)
    item_plot   = re.findall('<plot>(.*?)</plot>',   item_nfo)

    if item_genre:  collections[launcherID]['m_genre']  = text_unescape_XML(item_genre[0])
    if item_rating: collections[launcherID]['m_rating'] = text_unescape_XML(item_rating[0])
    if item_plot:   collections[launcherID]['m_plot']   = text_unescape_XML(item_plot[0])

    log_verb("fs_import_collection_NFO() Imported '{0}'".format(nfo_FileName.getPath()))

    return True

def fs_get_collection_NFO_name(settings, collection):
    collection_name = collection['m_name']
    nfo_dir = FileName(settings['collections_asset_dir'], isdir = True)
    nfo_file_path = nfo_dir.pjoin(collection_name + '.nfo')
    log_debug("fs_get_collection_NFO_name() nfo_file_path = '{0}'".format(nfo_file_path.getPath()))

    return nfo_file_path
