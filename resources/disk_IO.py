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

# --- Pyhton standard library
from __future__ import unicode_literals
import json
import io
import codecs
import time
import os
import sys
import fnmatch
import string
import base64

# --- XML stuff ---
# ~~~ cElementTree sometimes fails to parse XML in Kodi's Python interpreter... I don't know why
# import xml.etree.cElementTree as ET

# ~~~ Using ElementTree seems to solve the problem
import xml.etree.ElementTree as ET

# --- Kodi stuff ---
import xbmc

# --- AEL packages ---
from utils import *
# >> Avoid circular dependencies. assets.py imports disk_IO.py.
# from assets import *
from utils_kodi import *

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
# These three functions create a new data structure for the given object
# and (very importantly) fill the correct default values). These must match
# what is written/read from/to the XML files.
#
# Tag name in the XML is the same as in the data dictionary.
def fs_new_category():
    c = {'id' : '',
         'm_name' : '',
         'm_genre' : '',
         'm_rating' : '',
         'm_plot' : '',
         'finished' : False,
         'default_thumb' : 's_thumb',
         'default_fanart' : 's_fanart',
         'default_banner' : 's_banner',
         'default_poster' : 's_flyer',
         's_thumb' : '',
         's_fanart' : '',
         's_banner' : '',
         's_flyer' : '',
         's_trailer' : ''
         }

    return c

def fs_new_launcher():
    l = {'id' : '',
         'm_name' : '',
         'm_year' : '',
         'm_genre' : '',
         'm_studio' : '',
         'm_rating' : '',
         'm_plot' : '',
         'platform' : '',
         'categoryID' : '',
         'application' : '',
         'args' : '',
         'rompath' : '',
         'romext' : '',
         'finished': False,
         'minimize' : False,
         'roms_base_noext' : '',
         'nointro_xml_file' : '',
         'pclone_launcher' : False,
         'timestamp_launcher' : 0.0,
         'timestamp_report' : 0.0,
         'default_thumb' : 's_thumb',
         'default_fanart' : 's_fanart',
         'default_banner' : 's_banner',
         'default_poster' : 's_flyer',
         'roms_default_thumb' : 's_boxfront',
         'roms_default_fanart' : 's_fanart',
         'roms_default_banner' : 's_banner',
         'roms_default_poster' : 's_flyer',
         'roms_default_clearlogo' : 's_clearlogo',
         's_thumb' : '',
         's_fanart' : '',
         's_banner' : '',
         's_flyer' : '',
         's_trailer' : '',
         'path_title' : '',
         'path_snap' : '',
         'path_fanart' : '',
         'path_banner' : '',
         'path_clearlogo' : '',
         'path_boxfront' : '',
         'path_boxback' : '',
         'path_cartridge' : '',
         'path_flyer' : '',
         'path_map' : '',
         'path_manual' : '',
         'path_trailer' : ''
    }

    return l

# Mandatory variables in XML:
# id              string MD5 hash
# name            string ROM name
# finished        bool ['True', 'False'] default 'False'
# nointro_status  string ['Have', 'Miss', 'Unknown', 'None'] default 'None'
def fs_new_rom():
    r = {'id' : '',
         'm_name' : '',
         'm_year' : '',
         'm_genre' : '',
         'm_studio' : '',
         'm_rating' : '',
         'm_plot' : '',
         'filename' : '',
         'altapp' : '',
         'altarg' : '',
         'finished' : False,
         'nointro_status' : 'None',
         's_title' : '',
         's_snap' : '',
         's_fanart' : '',
         's_banner' : '',
         's_clearlogo' : '',
         's_boxfront' : '',
         's_boxback' : '',
         's_cartridge' : '',
         's_flyer' : '',
         's_map' : '',
         's_manual' : '',
         's_trailer' : ''
    }

    return r

def fs_new_collection():
    c = {'id' : '',
         'm_name' : '',
         'm_genre' : '',
         'm_rating' : '',
         'm_plot' : '',
         'roms_base_noext' : '',
         'default_thumb' : 's_thumb',
         'default_fanart' : 's_fanart',
         'default_banner' : 's_banner',
         'default_poster' : 's_flyer',
         's_thumb' : '',
         's_fanart' : '',
         's_banner' : '',
         's_flyer' : '',
         's_trailer' : ''
    }

    return c

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
    favourite['rompath']                = launcher['rompath']
    favourite['romext']                 = launcher['romext']
    favourite['minimize']               = launcher['minimize']
    favourite['roms_default_thumb']     = launcher['roms_default_thumb']
    favourite['roms_default_fanart']    = launcher['roms_default_fanart']
    favourite['roms_default_banner']    = launcher['roms_default_banner']
    favourite['roms_default_poster']    = launcher['roms_default_poster']
    favourite['roms_default_clearlogo'] = launcher['roms_default_clearlogo']

    # >> Favourite ROM unique fields
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
    dest_rom['platform']    = source_launcher['platform']
    dest_rom['application'] = source_launcher['application']
    dest_rom['args']        = source_launcher['args']
    dest_rom['rompath']     = source_launcher['rompath']
    dest_rom['romext']      = source_launcher['romext']
    dest_rom['minimize']    = source_launcher['minimize']

def fs_aux_copy_ROM_metadata(source_rom, dest_rom):
    dest_rom['m_name']         = source_rom['m_name']
    dest_rom['m_year']         = source_rom['m_year']
    dest_rom['m_genre']        = source_rom['m_genre']
    dest_rom['m_studio']       = source_rom['m_studio']
    dest_rom['m_rating']       = source_rom['m_rating']
    dest_rom['m_plot']         = source_rom['m_plot']
    dest_rom['altapp']         = source_rom['altapp']
    dest_rom['altarg']         = source_rom['altarg']
    dest_rom['finished']       = source_rom['finished']
    dest_rom['nointro_status'] = source_rom['nointro_status']

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
    dest_rom['roms_default_thumb']     = source_launcher['roms_default_thumb']
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
# Filesystem very low-level utilities
# -------------------------------------------------------------------------------------------------
#
# Writes a XML text tag line, indented 2 spaces (root sub-child)
# Both tag_name and tag_text must be Unicode strings.
# Returns an Unicode string.
#
def XML_text(tag_name, tag_text):
    tag_text = text_escape_XML(tag_text)
    line     = '  <{0}>{1}</{2}>\n'.format(tag_name, tag_text, tag_name)

    return line

#
# See https://docs.python.org/2/library/sys.html#sys.getfilesystemencoding
#
def get_fs_encoding():
    return sys.getfilesystemencoding()

# -------------------------------------------------------------------------------------------------
# Categories/Launchers
# -------------------------------------------------------------------------------------------------
#
# Write to disk categories.xml
#
def fs_write_catfile(categories_file, categories, launchers, update_timestamp = 0.0):
    log_verb('fs_write_catfile() Writing {0}'.format(categories_file.getOriginalPath()))

    # Original Angelscry method for generating the XML was to grow a string, like this
    # xml_content = 'test'
    # xml_content += 'more test'
    # However, this method is very slow because string has to be reallocated every time is grown.
    # It is much faster to create a list of string and them join them!
    # See https://waymoot.org/home/python_string/
    try:
        str_list = []
        str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        str_list.append('<advanced_emulator_launcher version="{0}">\n'.format(AEL_STORAGE_FORMAT))

        # --- Control information ---
        # >> time.time() returns a float. Usually precision is much better than a second, but not always.
        # >> See https://docs.python.org/2/library/time.html#time.time
        # NOTE When updating reports timestamp of categories/launchers must not be modified.
        if not update_timestamp: _t = time.time()
        else:                    _t = update_timestamp

        # >> Write a timestamp when file is created. This enables the Virtual Launchers to know if
        # >> it's time for an update.
        str_list.append('<control>\n')
        str_list.append(XML_text('update_timestamp', unicode(_t)))
        str_list.append('</control>\n')

        # --- Create Categories XML list ---
        for categoryID in sorted(categories, key = lambda x : categories[x]['m_name']):
            category = categories[categoryID]
            # Data which is not string must be converted to string
            # XML_text() returns Unicode strings that will be encoded to UTF-8 later.
            str_list.append('<category>\n')
            str_list.append(XML_text('id', categoryID))
            str_list.append(XML_text('m_name', category['m_name']))
            str_list.append(XML_text('m_genre', category['m_genre']))
            str_list.append(XML_text('m_plot', category['m_plot']))
            str_list.append(XML_text('m_rating', category['m_rating']))
            str_list.append(XML_text('finished', unicode(category['finished'])))
            str_list.append(XML_text('default_thumb', category['default_thumb']))
            str_list.append(XML_text('default_fanart', category['default_fanart']))
            str_list.append(XML_text('default_banner', category['default_banner']))
            str_list.append(XML_text('default_poster', category['default_poster']))
            str_list.append(XML_text('s_thumb', category['s_thumb']))
            str_list.append(XML_text('s_fanart', category['s_fanart']))
            str_list.append(XML_text('s_banner', category['s_banner']))
            str_list.append(XML_text('s_flyer', category['s_flyer']))
            str_list.append(XML_text('s_trailer', category['s_trailer']))
            str_list.append('</category>\n')

        # --- Write launchers ---
        for launcherID in sorted(launchers, key = lambda x : launchers[x]['m_name']):
            # Data which is not string must be converted to string
            launcher = launchers[launcherID]
            str_list.append('<launcher>\n')
            str_list.append(XML_text('id', launcherID))
            str_list.append(XML_text('m_name', launcher['m_name']))
            str_list.append(XML_text('m_year', launcher['m_year']))
            str_list.append(XML_text('m_genre', launcher['m_genre']))
            str_list.append(XML_text('m_studio', launcher['m_studio']))
            str_list.append(XML_text('m_plot', launcher['m_plot']))
            str_list.append(XML_text('m_rating', launcher['m_rating']))
            str_list.append(XML_text('platform', launcher['platform']))
            str_list.append(XML_text('categoryID', launcher['categoryID']))
            str_list.append(XML_text('application', launcher['application']))
            str_list.append(XML_text('args', launcher['args']))
            str_list.append(XML_text('rompath', launcher['rompath']))
            str_list.append(XML_text('romext', launcher['romext']))
            str_list.append(XML_text('finished', unicode(launcher['finished'])))
            str_list.append(XML_text('minimize', unicode(launcher['minimize'])))
            str_list.append(XML_text('roms_base_noext', launcher['roms_base_noext']))
            str_list.append(XML_text('nointro_xml_file', launcher['nointro_xml_file']))
            str_list.append(XML_text('pclone_launcher', unicode(launcher['pclone_launcher'])))
            str_list.append(XML_text('timestamp_launcher', unicode(launcher['timestamp_launcher'])))
            str_list.append(XML_text('timestamp_report', unicode(launcher['timestamp_report'])))
            str_list.append(XML_text('default_thumb', launcher['default_thumb']))
            str_list.append(XML_text('default_fanart', launcher['default_fanart']))
            str_list.append(XML_text('default_banner', launcher['default_banner']))
            str_list.append(XML_text('default_poster', launcher['default_poster']))
            str_list.append(XML_text('roms_default_thumb', launcher['roms_default_thumb']))
            str_list.append(XML_text('roms_default_fanart', launcher['roms_default_fanart']))
            str_list.append(XML_text('roms_default_banner', launcher['roms_default_banner']))
            str_list.append(XML_text('roms_default_poster', launcher['roms_default_poster']))
            str_list.append(XML_text('roms_default_clearlogo', launcher['roms_default_clearlogo']))
            str_list.append(XML_text('s_thumb', launcher['s_thumb']))
            str_list.append(XML_text('s_fanart', launcher['s_fanart']))
            str_list.append(XML_text('s_banner', launcher['s_banner']))
            str_list.append(XML_text('s_flyer', launcher['s_flyer']))
            str_list.append(XML_text('s_trailer', launcher['s_trailer']))
            str_list.append(XML_text('path_title', launcher['path_title']))
            str_list.append(XML_text('path_snap', launcher['path_snap']))
            str_list.append(XML_text('path_fanart', launcher['path_fanart']))
            str_list.append(XML_text('path_banner', launcher['path_banner']))
            str_list.append(XML_text('path_clearlogo', launcher['path_clearlogo']))
            str_list.append(XML_text('path_boxfront', launcher['path_boxfront']))
            str_list.append(XML_text('path_boxback', launcher['path_boxback']))
            str_list.append(XML_text('path_cartridge', launcher['path_cartridge']))
            str_list.append(XML_text('path_flyer', launcher['path_flyer']))
            str_list.append(XML_text('path_map', launcher['path_map']))
            str_list.append(XML_text('path_manual', launcher['path_manual']))
            str_list.append(XML_text('path_trailer', launcher['path_trailer']))
            str_list.append('</launcher>\n')
        # End of file
        str_list.append('</advanced_emulator_launcher>\n')

        # Strings in the list are Unicode. Encode to UTF-8
        # Join string, and save categories.xml file
        full_string = ''.join(str_list).encode('utf-8')
        file_obj = open(categories_file.getPath(), 'w')
        file_obj.write(full_string)
        file_obj.close()
    except OSError:
        log_error('(OSError) Cannot write categories.xml file')
        kodi_notify_warn('(OSError) Cannot write categories.xml file')
    except IOError:
        log_error('(IOError) Cannot write categories.xml file')
        kodi_notify_warn('(IOError) Cannot write categories.xml file')

#
# Loads categories.xml from disk and fills dictionary self.categories
#
def fs_load_catfile(categories_file):
    __debug_xml_parser = 0
    update_timestamp = 0.0
    categories = {}
    launchers = {}

    # --- Parse using cElementTree ---
    # If there are issues in the XML file (for example, invalid XML chars) ET.parse will fail
    log_verb('fs_load_catfile() Loading {0}'.format(categories_file.getOriginalPath()))
    try:
        xml_tree = ET.parse(categories_file.getPath())
    except ET.ParseError, e:
        log_error('(ParseError) Exception parsing XML categories.xml')
        log_error('(ParseError) {0}'.format(str(e)))
        kodi_dialog_OK('(ParseError) Exception reading categories.xml. '
                       'Maybe XML file is corrupt or contains invalid characters.')
        return (update_timestamp, categories, launchers)
    xml_root = xml_tree.getroot()
    for category_element in xml_root:
        if __debug_xml_parser: log_debug('Root child {0}'.format(category_element.tag))

        if category_element.tag == 'control':
            for control_child in category_element:
                if control_child.tag == 'update_timestamp':
                    # >> Convert Unicode to float
                    update_timestamp = float(control_child.text)

        elif category_element.tag == 'category':
            # Default values
            category = fs_new_category()

            # Parse child tags of category
            for category_child in category_element:
                # By default read strings
                xml_text = category_child.text if category_child.text is not None else ''
                xml_text = text_unescape_XML(xml_text)
                xml_tag  = category_child.tag
                if __debug_xml_parser: log_debug('{0} --> {1}'.format(xml_tag, xml_text))
                # Internal data is always stored as Unicode. ElementTree already outputs Unicode.
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

                # Transform Bool datatype
                if xml_tag == 'finished' or xml_tag == 'minimize' or xml_tag == 'pclone_launcher':
                    xml_bool = True if xml_text == 'True' else False
                    launcher[xml_tag] = xml_bool
                # Transform Float datatype
                elif xml_tag == 'timestamp_launcher' or xml_tag == 'timestamp_report':
                    xml_float = float(xml_text)
                    launcher[xml_tag] = xml_float

            # Add launcher to categories dictionary
            launchers[launcher['id']] = launcher

    return (update_timestamp, categories, launchers)

# -------------------------------------------------------------------------------------------------
# Generic JSON loader/writer
# -------------------------------------------------------------------------------------------------
# Look at the ROMs JSON code for reference/comments to these functions.
def fs_write_JSON_file(file_dir, file_base_noext, data):
    # >> Get file names
    json_file = file_dir.getSubPath(file_base_noext + '.json')
    log_verb('fs_write_JSON_file() Dir  {0}'.format(file_dir.getOriginalPath()))
    log_verb('fs_write_JSON_file() JSON {0}'.format(file_base_noext + '.json'))

    try:
        with io.open(json_file.getPath(), 'w', encoding = 'utf-8') as file:
            json_data = json.dumps(data, ensure_ascii = False, sort_keys = True, 
                                   indent = JSON_indent, separators = JSON_separators)
            file.write(unicode(json_data))
            file.close()
    except OSError:
        kodi_notify_warn('(OSError) Cannot write {0} file'.format(json_file.getPath()))
    except IOError:
        kodi_notify_warn('(IOError) Cannot write {0} file'.format(json_file.getPath()))

def fs_load_JSON_file(file_dir, file_base_noext):
    data = {}

    # --- If file does not exist return empty dictionary ---
    json_file = file_dir.getSubPath(file_base_noext + '.json')
    if not json_file.exists(): return data

    # --- Parse using json module ---
    log_verb('fs_load_JSON_file() Dir  {0}'.format(file_dir.getOriginalPath()))
    log_verb('fs_load_JSON_file() JSON {0}'.format(file_base_noext + '.json'))
    with open(json_file.getPath()) as file:
        try:
            data = json.load(file)
        except ValueError:
            statinfo = json_file.stat()
            log_error('fs_load_JSON_file() ValueError exception in json.load() function')
            log_error('fs_load_JSON_file() Dir  {0}'.format(file_dir.getPath()))
            log_error('fs_load_JSON_file() File {0}'.format(file_base_noext + '.json'))
            log_error('fs_load_JSON_file() Size {0}'.format(statinfo.st_size))
        file.close()

    return data

# -------------------------------------------------------------------------------------------------
# Standard ROMs
# -------------------------------------------------------------------------------------------------
# >> Use XML or JSON transparently
def fs_write_ROMs(roms_dir, roms_base_noext, roms, launcher):
    # fs_write_ROMs_XML(roms_dir, roms_base_noext, roms, launcher)
    fs_write_ROMs_JSON(roms_dir, roms_base_noext, roms, launcher)

def fs_load_ROMs(roms_dir, roms_base_noext):
    # roms = fs_load_ROMs_XML(roms_dir, roms_base_noext)
    roms = fs_load_ROMs_JSON(roms_dir, roms_base_noext)

    return roms

#
# Return ROMs file name. Changes extension depeding if we use XML or JSON.
# JSON ROM writer creates 2 files: one JSON with main DB and one small XML with associated
# launcher info. When removing launchers both the JSON and XML files must be removed.
#
def fs_get_ROMs_XML_file_path(roms_dir, roms_base_noext):
    roms_file_path = roms_dir.getSubPath(roms_base_noext + '.xml')

    return roms_file_path

def fs_get_ROMs_JSON_file_path(roms_dir, roms_base_noext):
    roms_file_path = roms_dir.getSubPath(roms_base_noext + '.json')

    return roms_file_path

#
# This returns XML or JSON depending of what used to store main ROM DB.
# Currently plugin stores launcher ROMs as JSON because is faster than XML.
#
def fs_get_ROMs_file_path(roms_dir, roms_base_noext):
    roms_file_path = roms_dir.getSubPath(roms_base_noext + '.json')

    return roms_file_path

#
# Write to disk launcher ROMs XML database (OBSOLETE FUNCTION)
#
def fs_write_ROMs_XML(roms_dir, roms_base_noext, roms, launcher):
    # >> Get filename
    roms_xml_file = os.path.join(roms_dir, roms_base_noext + '.xml')
    log_debug('fs_write_ROMs_XML() Saving XML file {0}'.format(roms_xml_file))

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
        str_list.append(XML_text('romID', launcher['romID']))
        str_list.append(XML_text('m_name', launcher['m_name']))
        str_list.append(XML_text('categoryID', launcher['categoryID']))
        str_list.append(XML_text('platform', launcher['platform']))
        str_list.append(XML_text('rompath', launcher['rompath']))
        str_list.append(XML_text('romext', launcher['romext']))
        str_list.append('</launcher>\n')

        # --- Create list of ROMs ---
        # Size optimization: only write in the XML fields which are not ''. This
        # will save A LOT of disk space and reduce loading times (at a cost of
        # some writing time, but writing is much less frequent than reading).
        for romID in sorted(roms, key = lambda x : roms[x]['name']):
            # Data which is not string must be converted to string
            rom = roms[romID]
            str_list.append('<rom>\n')
            str_list.append(XML_text('romID', romID))
            str_list.append(XML_text('m_name', rom['m_name']))
            if rom['m_year']:         str_list.append(XML_text('m_year', rom['m_year']))
            if rom['m_genre']:        str_list.append(XML_text('m_genre', rom['m_genre']))
            if rom['m_plot']:         str_list.append(XML_text('m_plot', rom['m_plot']))
            if rom['m_studio']:       str_list.append(XML_text('m_studio', rom['m_studio']))
            if rom['m_rating']:       str_list.append(XML_text('m_rating', rom['m_rating']))
            if rom['filename']:       str_list.append(XML_text('filename', rom['filename']))
            if rom['altapp']:         str_list.append(XML_text('altapp', rom['altapp']))
            if rom['altarg']:         str_list.append(XML_text('altarg', rom['altarg']))
            str_list.append(XML_text('finished', unicode(rom['finished'])))
            str_list.append(XML_text('nointro_status', rom['nointro_status']))
            if rom['default_thumb']:  str_list.append(XML_text('default_thumb', rom['default_thumb']))
            if rom['default_fanart']: str_list.append(XML_text('default_fanart', rom['default_fanart']))
            if rom['s_title']:        str_list.append(XML_text('s_title', rom['s_title']))
            if rom['s_snap']:         str_list.append(XML_text('s_snap', rom['s_snap']))
            if rom['s_fanart']:       str_list.append(XML_text('s_fanart', rom['s_fanart']))
            if rom['s_banner']:       str_list.append(XML_text('s_banner', rom['s_banner']))
            if rom['s_clearlogo']:    str_list.append(XML_text('s_clearlogo', rom['s_clearlogo']))
            if rom['s_boxfront']:     str_list.append(XML_text('s_boxfront', rom['s_boxfront']))
            if rom['s_boxback']:      str_list.append(XML_text('s_boxback', rom['s_boxback']))
            if rom['s_cartridge']:    str_list.append(XML_text('s_cartridge', rom['s_cartridge']))
            if rom['s_flyer']:        str_list.append(XML_text('s_flyer', rom['s_flyer']))
            if rom['s_map']:          str_list.append(XML_text('s_map', rom['s_map']))
            if rom['s_manual']:       str_list.append(XML_text('s_manual', rom['s_manual']))
            if rom['s_trailer']:      str_list.append(XML_text('s_trailer', rom['s_trailer']))
            str_list.append('</rom>\n')
        # End of file
        str_list.append('</advanced_emulator_launcher_ROMs>\n')

        # --- Join string and save categories.xml file ---
        full_string = ''.join(str_list).encode('utf-8')
        file_obj = open(roms_xml_file, 'w')
        file_obj.write(full_string)
        file_obj.close()
    except OSError:
        kodi_notify_warn('(OSError) Cannot write {0} file'.format(roms_xml_file))
        log_error('fs_write_ROMs_XML() (OSerror) Cannot write file "{0}"'.format(roms_xml_file))
    except IOError:
        kodi_notify_warn('(IOError) Cannot write {0} file'.format(roms_xml_file))
        log_error('fs_write_ROMs_XML() (IOError) Cannot write file "{0}"'.format(roms_xml_file))

    # --- We are not busy anymore ---
    kodi_busydialog_OFF()

#
# Loads a launcher XML with the ROMs (OBSOLETE FUNCTION)
#
def fs_load_ROMs_XML(roms_dir, roms_base_noext):
    __debug_xml_parser = 0
    roms = {}

    # --- If file does not exist return empty dictionary ---
    roms_xml_file = os.path.join(roms_dir, roms_base_noext + '.xml')
    if not os.path.isfile(roms_xml_file): return roms

    # --- Notify we are busy doing things ---
    kodi_busydialog_ON()

    # --- Parse using cElementTree ---
    log_debug('fs_load_ROMs_XML() Loading XML file {0}'.format(roms_xml_file))
    # If XML has errors (invalid characters, etc.) this will rais exception 'err'
    try:
        xml_tree = ET.parse(roms_xml_file)
    except ET.ParseError, e:
        log_error('(ParseError) Exception parsing XML categories.xml')
        log_error('(ParseError) {0}'.format(str(e)))
        return roms
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

def fs_write_ROMs_JSON(roms_dir, roms_base_noext, roms, launcher):
    # >> Get file names
    roms_json_file = roms_dir.getSubPath(roms_base_noext + '.json')
    roms_xml_file  = roms_dir.getSubPath(roms_base_noext + '.xml')
    log_verb('fs_write_ROMs_JSON() Dir  {0}'.format(roms_dir.getOriginalPath()))
    log_verb('fs_write_ROMs_JSON() JSON {0}'.format(roms_base_noext + '.json'))
    log_verb('fs_write_ROMs_JSON() XML  {0}'.format(roms_base_noext + '.xml'))

    # >> JSON files cannot have comments. Write an auxiliar NFO file with same prefix
    # >> to store launcher information for a set of ROMs
    try:
        str_list = []
        str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        str_list.append('<advanced_emulator_launcher_ROMs version="{0}">\n'.format(AEL_STORAGE_FORMAT))

        # Print some information in the XML so the user can now which launcher created it.
        # Note that this is ignored when reading the file.
        str_list.append('<launcher>\n')
        str_list.append(XML_text('id', launcher['id']))
        str_list.append(XML_text('m_name', launcher['m_name']))
        str_list.append(XML_text('categoryID', launcher['categoryID']))
        str_list.append(XML_text('platform', launcher['platform']))
        str_list.append(XML_text('rompath', launcher['rompath']))
        str_list.append(XML_text('romext', launcher['romext']))
        str_list.append('</launcher>\n')
        str_list.append('</advanced_emulator_launcher_ROMs>\n')

        full_string = ''.join(str_list).encode('utf-8')
        file_obj = open(roms_xml_file.getPath(), 'w')
        file_obj.write(full_string)
        file_obj.close()
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
        with io.open(roms_json_file.getPath(), 'w', encoding = 'utf-8') as file:
            # >> json_unicode is either str or unicode
            # >> See https://docs.python.org/2.7/library/json.html#json.dumps
            json_data = json.dumps(roms, ensure_ascii = False, sort_keys = True,
                                   indent = JSON_indent, separators = JSON_separators)
            # unicode(json_data) auto-decodes data to unicode if str
            file.write(unicode(json_data))
            file.close()
    except OSError:
        kodi_notify_warn('(OSError) Cannot write {0} file'.format(roms_json_file.getPath()))
    except IOError:
        kodi_notify_warn('(IOError) Cannot write {0} file'.format(roms_json_file.getPath()))

#
# Loads an JSON file containing the Virtual Launcher ROMs
#
def fs_load_ROMs_JSON(roms_dir, roms_base_noext):
    roms = {}

    # --- If file does not exist return empty dictionary ---
    roms_json_file = roms_dir.getSubPath(roms_base_noext + '.json')
    if not roms_json_file.exists(): return roms

    # --- Parse using json module ---
    # >> On Github issue #8 a user had an empty JSON file for ROMs. This raises
    #    exception exceptions.ValueError and launcher cannot be deleted. Deal
    #    with this exception so at least launcher can be rescanned.
    log_verb('fs_load_ROMs_JSON() Dir  {0}'.format(roms_dir.getOriginalPath()))
    log_verb('fs_load_ROMs_JSON() JSON {0}'.format(roms_base_noext + '.json'))
    with open(roms_json_file.getPath().decode('utf-8')) as file:
        try:
            roms = json.load(file)
        except ValueError:
            statinfo = roms_json_file.stat()
            log_error('fs_load_ROMs_JSON() ValueError exception in json.load() function')
            log_error('fs_load_ROMs_JSON() Dir  {0}'.format(roms_dir.getPath()))
            log_error('fs_load_ROMs_JSON() File {0}'.format(roms_base_noext + '.json'))
            log_error('fs_load_ROMs_JSON() Size {0}'.format(statinfo.st_size))
        file.close()

    return roms

# -------------------------------------------------------------------------------------------------
# Favourite ROMs
# -------------------------------------------------------------------------------------------------
#
# Save Favourites JSON file
#
def fs_write_Favourites_JSON(roms_json_file, roms):
    log_info('fs_write_Favourites_JSON() File {0}'.format(roms_json_file.getOriginalPath()))

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
        with io.open(roms_json_file.getPath(), 'w', encoding='utf-8') as file:
            json_data = json.dumps(raw_data, ensure_ascii = False, sort_keys = True, 
                                   indent = JSON_indent, separators = JSON_separators)
            file.write(unicode(json_data))
            file.close()
    except OSError:
        kodi_notify_warn('(OSError) Cannot write {0} file'.format(roms_json_file.getPath()))
    except IOError:
        kodi_notify_warn('(IOError) Cannot write {0} file'.format(roms_json_file.getPath()))

#
# Loads an JSON file containing the Favourite ROMs
#
def fs_load_Favourites_JSON(roms_json_file):
    # --- If file does not exist return empty dictionary ---
    log_verb('fs_load_Favourites_JSON() File {0}'.format(roms_json_file.getOriginalPath()))
    if not roms_json_file.exists(): 
        return {}

    # --- Parse JSON ---
    with open(roms_json_file.getPath()) as file:    
        try:
            raw_data = json.load(file)
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
    log_info('fs_write_Collection_index_XML() File {0}'.format(collections_xml_file.getOriginalPath()))
    try:
        str_list = []
        str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        str_list.append('<advanced_emulator_launcher_Collection_index version="{0}">\n'.format(AEL_STORAGE_FORMAT))

        # --- Control information ---
        _t = time.time()
        str_list.append('<control>\n')
        str_list.append(XML_text('update_timestamp', unicode(_t)))
        str_list.append('</control>\n')

        # --- Virtual Launchers ---
        for collection_id in sorted(collections, key = lambda x : collections[x]['m_name']):
            collection = collections[collection_id]
            str_list.append('<Collection>\n')
            str_list.append(XML_text('id', collection['id']))
            str_list.append(XML_text('m_name', collection['m_name']))
            str_list.append(XML_text('m_genre', collection['m_genre']))
            str_list.append(XML_text('m_rating', collection['m_rating']))
            str_list.append(XML_text('m_plot', collection['m_plot']))
            str_list.append(XML_text('roms_base_noext', collection['roms_base_noext']))
            str_list.append(XML_text('default_thumb', collection['default_thumb']))
            str_list.append(XML_text('default_fanart', collection['default_fanart']))
            str_list.append(XML_text('default_banner', collection['default_banner']))
            str_list.append(XML_text('default_poster', collection['default_poster']))
            str_list.append(XML_text('s_thumb', collection['s_thumb']))
            str_list.append(XML_text('s_fanart', collection['s_fanart']))
            str_list.append(XML_text('s_banner', collection['s_banner']))
            str_list.append(XML_text('s_flyer', collection['s_flyer']))
            str_list.append(XML_text('s_trailer', collection['s_trailer']))
            str_list.append('</Collection>\n')
        str_list.append('</advanced_emulator_launcher_Collection_index>\n')
        full_string = ''.join(str_list).encode('utf-8')
        file_obj = open(collections_xml_file.getPath(), 'w')
        file_obj.write(full_string)
        file_obj.close()
    except OSError:
        kodi_notify_warn('(OSError) Cannot write {0} file'.format(collections_xml_file.getPath()))
    except IOError:
        kodi_notify_warn('(IOError) Cannot write {0} file'.format(collections_xml_file.getPath()))

def fs_load_Collection_index_XML(collections_xml_file):
    __debug_xml_parser = 0
    update_timestamp = 0.0
    collections = {}

    # --- If file does not exist return empty dictionary ---
    if not collections_xml_file.exists(): return (collections, update_timestamp)

    # --- Parse using cElementTree ---
    log_verb('fs_load_Collection_index_XML() Loading {0}'.format(collections_xml_file.getOriginalPath()))
    try:
        xml_tree = ET.parse(collections_xml_file.getPath())
    except ET.ParseError, e:
        log_error('(ParseError) Exception parsing XML categories.xml')
        log_error('(ParseError) {0}'.format(str(e)))
        return roms
    xml_root = xml_tree.getroot()
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
                xml_text = rom_child.text if rom_child.text is not None else ''
                xml_text = text_unescape_XML(xml_text)
                xml_tag  = rom_child.tag
                if __debug_xml_parser: log_debug('{0} --> {1}'.format(xml_tag, xml_text))
                collection[xml_tag] = xml_text
            collections[collection['id']] = collection

    return (collections, update_timestamp)

def fs_write_Collection_ROMs_JSON(roms_json_file, roms):
    log_verb('fs_write_Collection_ROMs_JSON() {0}'.format(roms_json_file.getOriginalPath()))

    control_dic = {
        'control' : 'Advanced Emulator Launcher Collection ROMs',
        'version' : AEL_STORAGE_FORMAT
    }
    raw_data = []
    raw_data.append(control_dic)
    raw_data.append(roms)

    try:
        with io.open(roms_json_file.getPath(), 'w', encoding = 'utf-8') as file:
            json_data = json.dumps(raw_data, ensure_ascii = False, sort_keys = True, 
                                   indent = JSON_indent, separators = JSON_separators)
            file.write(unicode(json_data))
            file.close()
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
    log_verb('fs_load_Collection_ROMs_JSON() {0}'.format(roms_json_file.getOriginalPath()))

    with open(roms_json_file.getPath()) as file:    
        try:
            raw_data = json.load(file)
        except ValueError:
            statinfo = roms_json_file.stat()
            log_error('fs_load_Collection_ROMs_JSON() ValueError exception in json.load() function')
            log_error('fs_load_Collection_ROMs_JSON() File {0}'.format(roms_json_file.getOriginalPath()))
            log_error('fs_load_Collection_ROMs_JSON() Size {0}'.format(statinfo.st_size))
            return []

    # --- Extract roms from JSON data structe and ensure version is correct ---
    control_str = raw_data[0]['control']
    version_int = raw_data[0]['version']
    roms        = raw_data[1]

    return roms

def fs_export_ROM_collection(output_filename, collection, collection_rom_list):
    log_info('fs_export_ROM_collection() File {0}'.format(output_filename.getOriginalPath()))
    
    control_dic = {
        'control' : 'Advanced Emulator Launcher Collection ROMs',
        'version' : AEL_STORAGE_FORMAT
    }
    collection_dic = {
        'id'             : collection['id'],
        'm_name'         : collection['m_name'],
        'm_genre'        : collection['m_genre'],
        'm_rating'       : collection['m_rating'],
        'm_plot'         : collection['m_plot'],
        'default_thumb'  : collection['default_thumb'],
        'default_fanart' : collection['default_fanart'],
        'default_banner' : collection['default_banner'],
        'default_poster' : collection['default_poster'],
        's_thumb'        : collection['s_thumb'],
        's_fanart'       : collection['s_fanart'],
        's_banner'       : collection['s_banner'],
        's_flyer'        : collection['s_flyer'],
        's_trailer'      : collection['s_trailer']
    }
    raw_data = []
    raw_data.append(control_dic)
    raw_data.append(collection_dic)
    raw_data.append(collection_rom_list)

    # >> Produce nicely formatted JSON when exporting
    try:
        with io.open(output_filename.getPath(), 'w', encoding = 'utf-8') as file:
            json_data = json.dumps(raw_data, ensure_ascii = False, sort_keys = True, 
                                   indent = 2, separators = (', ', ' : '))
            file.write(unicode(json_data))
            file.close()
    except OSError:
        kodi_notify_warn('(OSError) Cannot write {0} file'.format(output_filename.getPath()))
    except IOError:
        kodi_notify_warn('(IOError) Cannot write {0} file'.format(output_filename.getPath()))

#
# Export collection assets. Use base64 encoding to store binary files in JSON.
#
def fs_export_ROM_collection_assets(output_filename, collection, collection_rom_list, collections_asset_dir):
    log_info('fs_export_ROM_collection_assets() File {0}'.format(output_filename.getOriginalPath()))

    control_dic = {
        'control' : 'Advanced Emulator Launcher Collection ROM assets',
        'version' : AEL_STORAGE_FORMAT
    }

    # --- Export Collection assets ---
    assets_dic = {}
    log_debug('fs_export_ROM_collection_assets() Exporting Collecion assets')
    for asset_kind in [ASSET_THUMB, ASSET_FANART, ASSET_BANNER, ASSET_FLYER, ASSET_TRAILER]:
        A = assets_get_info_scheme(asset_kind)
        asset_filename = collection[A.key]
        asset_F = misc_split_path(asset_filename)
        if not asset_filename:
            log_debug('{0:<9s} not set'.format(A.name))
            continue
        elif asset_F.dirname == collections_asset_dir:
            log_debug('{0:<9s} Adding to assets dictionary with key "{1}"'.format(A.name, asset_F.base_noext))
            with open(asset_filename, mode = 'rb') as file: # b is important -> binary
                fileData = file.read()
            fileData_base64 = base64.b64encode(fileData)
            statinfo = os.stat(asset_filename)
            file_size = statinfo.st_size
            a_dic = {'basename' : asset_F.base, 'filesize' : file_size, 'data' : fileData_base64}
            assets_dic[asset_F.base_noext] = a_dic
        else:
            log_error('{0:<9s} in parent ROM directory! This is not supposed to happen!'.format(A.name))

    # --- Export ROMs assets ---
    # key -> basename : value { 'filesize' : int, 'data' : string }
    for rom_item in collection_rom_list:
        log_debug('fs_export_ROM_collection_assets() ROM "{0}"'.format(rom_item['m_name']))
        for asset_kind in ROM_ASSET_LIST:
            A = assets_get_info_scheme(asset_kind)
            asset_filename = rom_item[A.key]
            asset_F = misc_split_path(asset_filename)
            if not asset_filename:
                log_debug('{0:<9s} not set'.format(A.name))
                continue
            elif asset_F.dirname == collections_asset_dir:
                log_debug('{0:<9s} Adding to assets dictionary with key "{1}"'.format(A.name, asset_F.base_noext))
                # >> Read image binary data and encode
                with open(asset_filename, mode = 'rb') as file: # b is important -> binary
                    fileData = file.read()
                fileData_base64 = base64.b64encode(fileData)
                # >> Get file size
                statinfo = os.stat(asset_filename)
                file_size = statinfo.st_size
                # >> Make data dictionary and append to list
                a_dic = {'basename' : asset_F.base, 'filesize' : file_size, 'data' : fileData_base64}
                assets_dic[asset_F.base_noext] = a_dic
            else:
                log_error('{0:<9s} in parent ROM directory! This is not supposed to happen!'.format(A.name))

    raw_data = []
    raw_data.append(control_dic)
    raw_data.append(assets_dic)

    # >> Produce nicely formatted JSON when exporting
    try:
        with io.open(output_filename.getPath(), 'w', encoding = 'utf-8') as file:
            json_data = json.dumps(raw_data, ensure_ascii = False, sort_keys = True,
                                   indent = 2, separators = (', ', ' : '))
            file.write(unicode(json_data))
            file.close()
    except OSError:
        kodi_notify_warn('(OSError) Cannot write {0} file'.format(output_filename.getPath()))
    except IOError:
        kodi_notify_warn('(IOError) Cannot write {0} file'.format(output_filename.getPath()))

#
# See fs_export_ROM_collection() function.
# Returns a tuple (control_dic, collection_dic, collection_rom_list)
#
def fs_import_ROM_collection(input_filename):
    if not os.path.isfile(input_filename): return ({}, {}, [])

    # --- Parse using JSON ---
    log_info('fs_import_ROM_collection() Loading {0}'.format(input_filename))

    with open(input_filename) as file:
        try:
            raw_data = json.load(file)
        except ValueError:
            statinfo = os.stat(input_filename)
            log_error('fs_import_ROM_collection() ValueError exception in json.load() function')
            log_error('fs_import_ROM_collection() File {0}'.format(input_filename))
            log_error('fs_import_ROM_collection() Size {0}'.format(statinfo.st_size))
            return ({}, {}, [])

    # --- Extract roms from JSON data structe and ensure version is correct ---
    control_dic         = raw_data[0]
    collection_dic      = raw_data[1]
    collection_rom_list = raw_data[2]
    control_str         = control_dic['control']
    version_int         = control_dic['version']

    return (control_dic, collection_dic, collection_rom_list)

def fs_import_ROM_collection_assets(input_filename):
    if not input_filename.exists(): return ({}, {}, [])

    # --- Parse using JSON ---
    log_info('fs_import_ROM_collection_assets() Loading {0}'.format(input_filename.getOriginalPath()))

    with open(input_filename.getPath()) as file:
        try:
            raw_data = json.load(file)
        except ValueError:
            statinfo = os.stat(input_filename)
            log_error('fs_import_ROM_collection_assets() ValueError exception in json.load() function')
            log_error('fs_import_ROM_collection_assets() File {0}'.format(input_filename.getPath()))
            log_error('fs_import_ROM_collection_assets() Size {0}'.format(statinfo.st_size))
            return ({}, {}, [])

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
    log_info('fs_write_VCategory_XML() Saving XML file {0}'.format(roms_xml_file.getOriginalPath()))
    try:
        str_list = []
        str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        str_list.append('<advanced_emulator_launcher_Virtual_Category_index version="{0}">\n'.format(AEL_STORAGE_FORMAT))

        # --- Control information ---
        _t = time.time()
        str_list.append('<control>\n')
        str_list.append(XML_text('update_timestamp', unicode(_t)))
        str_list.append('</control>\n')

        # --- Virtual Launchers ---
        for romID in sorted(roms, key = lambda x : roms[x]['name']):
            rom = roms[romID]
            str_list.append('<VLauncher>\n')
            str_list.append(XML_text('id', romID))
            str_list.append(XML_text('name', rom['name']))
            str_list.append(XML_text('rom_count', rom['rom_count']))
            str_list.append(XML_text('roms_base_noext', rom['roms_base_noext']))
            str_list.append('</VLauncher>\n')
        str_list.append('</advanced_emulator_launcher_Virtual_Category_index>\n')
        full_string = ''.join(str_list).encode('utf-8')
        file_obj = open(roms_xml_file.getPath(), 'w')
        file_obj.write(full_string)
        file_obj.close()
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
    log_verb('fs_load_VCategory_XML() Loading XML file {0}'.format(roms_xml_file.getOriginalPath()))
    try:
        xml_tree = ET.parse(roms_xml_file.getPath())
    except ET.ParseError, e:
        log_error('(ParseError) Exception parsing XML categories.xml')
        log_error('(ParseError) {0}'.format(str(e)))
        return roms
    xml_root = xml_tree.getroot()
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
                xml_text = rom_child.text if rom_child.text is not None else ''
                xml_text = text_unescape_XML(xml_text)
                xml_tag  = rom_child.tag
                if __debug_xml_parser: log_debug('{0} --> {1}'.format(xml_tag, xml_text))
                VLauncher[xml_tag] = xml_text
            VLaunchers[VLauncher['id']] = VLauncher

    return (update_timestamp, VLaunchers)

#
# Write virtual category ROMs
#
def fs_write_VCategory_ROMs_JSON(roms_dir, roms_base_noext, roms):
    roms_json_file = roms_dir.getSubPath(roms_base_noext + '.json')
    log_verb('fs_write_VCategory_ROMs_JSON() Saving JSON file {0}'.format(roms_json_file.getOriginalPath()))
    try:
        with io.open(roms_json_file.getPath(), 'w', encoding = 'utf-8') as file:
            json_data = json.dumps(roms, ensure_ascii = False, sort_keys = True, 
                                   indent = JSON_indent, separators = JSON_separators)
            file.write(unicode(json_data))
            file.close()
    except OSError:
        kodi_notify_warn('(OSError) Cannot write {0} file'.format(roms_json_file.getPath()))
    except IOError:
        kodi_notify_warn('(IOError) Cannot write {0} file'.format(roms_json_file.getPath()))

#
# Loads an JSON file containing the Virtual Launcher ROMs
#
def fs_load_VCategory_ROMs_JSON(roms_dir, roms_base_noext):
    # --- If file does not exist return empty dictionary ---
    roms_json_file = roms_dir.getSubPath(roms_base_noext + '.json')
    if not roms_json_file.exists(): return {}

    # --- Parse using cElementTree ---
    log_verb('fs_load_VCategory_ROMs_JSON() Loading JSON file {0}'.format(roms_json_file.getOriginalPath()))
    with open(roms_json_file.getPath()) as file:    
        try:
            roms = json.load(file)
        except ValueError:
            statinfo = roms_json_file.stat()
            log_error('fs_load_VCategory_ROMs_JSON() ValueError exception in json.load() function')
            log_error('fs_load_VCategory_ROMs_JSON() Dir  {0}'.format(roms_dir.getPath()))
            log_error('fs_load_VCategory_ROMs_JSON() File {0}'.format(roms_base_noext + '.json'))
            log_error('fs_load_VCategory_ROMs_JSON() Size {0}'.format(statinfo.st_size))
            return {}

    return roms

# -------------------------------------------------------------------------------------------------
# No-Intro and Offline scrapers
# -------------------------------------------------------------------------------------------------
#
# Loads a No-Intro Parent-Clone XML DAT file. Creates a data structure like
# roms_nointro = {
#   'rom_name_A' : { 'name' : 'rom_name_A', 'cloneof' : '' | 'rom_name_parent},
#   'rom_name_B' : { 'name' : 'rom_name_B', 'cloneof' : '' | 'rom_name_parent},
# }
#
def fs_load_NoIntro_XML_file(roms_xml_file):
    # --- If file does not exist return empty dictionary ---
    if not roms_xml_file.exists(): return {}

    # --- Parse using cElementTree ---
    log_verb('fs_load_NoIntro_XML_file() Loading XML file {0}'.format(roms_xml_file.getOriginalPath()))
    nointro_roms = {}
    try:
        xml_tree = ET.parse(roms_xml_file.getPath())
    except ET.ParseError, e:
        log_error('(ParseError) Exception parsing XML categories.xml')
        log_error('(ParseError) {0}'.format(str(e)))
        return roms
    xml_root = xml_tree.getroot()
    for root_element in xml_root:
        if root_element.tag == 'game':
            nointro_rom = {'name' : '', 'cloneof' : ''}
            rom_name = root_element.attrib['name']
            nointro_rom['name'] = rom_name
            if 'cloneof' in root_element.attrib:
                nointro_rom['cloneof'] = root_element.attrib['cloneof']
            nointro_roms[rom_name] = nointro_rom

    return nointro_roms

#
# Creates a Parent/Clone dictionary.
#
# roms_pclone_index = {
#   'parent_id_1'  : ['clone_id_1', 'clone_id_2', 'clone_id_3'],
#   'parent_id_2'  : ['clone_id_1', 'clone_id_2', 'clone_id_3'],
#    ... ,
#   'Unknown ROMs' : ['unknown_id_1', 'unknown_id_2', 'unknown_id_3']
# }
#
def fs_generate_PClone_index(roms, roms_nointro):
    # roms_pclone_index_by_name = {}
    roms_pclone_index_by_id = {}

    # --- Create a dictionary to convert ROM names into IDs ---
    names_to_ids_dic = {}
    for rom_id in roms:
        rom = roms[rom_id]
        if rom['nointro_status'] == 'Miss':
            rom_name = rom['m_name']
        else:
            F = misc_split_path(rom['filename'])
            rom_name = F.base_noext
        # log_debug('{0} --> {1}'.format(rom_name, rom_id))
        # log_debug('{0}'.format(rom))
        names_to_ids_dic[rom_name] = rom_id

    # --- Build PClone dictionary using ROM base_noext names ---
    for rom_id in roms:
        rom = roms[rom_id]
        F = misc_split_path(rom['filename'])
        # log_debug('rom_id {0}'.format(rom_id))
        # log_debug('  nointro_status   "{0}"'.format(rom['nointro_status']))
        # log_debug('  filename         "{0}"'.format(rom['filename']))
        # log_debug('  F.base_noext     "{0}"'.format(F.base_noext))

        if rom['nointro_status'] == 'Unknown':
            clone_id = rom['id']
            if 'Unknown ROMs' not in roms_pclone_index_by_id:
                roms_pclone_index_by_id['Unknown ROMs'] = []
                roms_pclone_index_by_id['Unknown ROMs'].append(clone_id)
            else:
                roms_pclone_index_by_id['Unknown ROMs'].append(clone_id)
        # If status is Have or Miss then ROM is guaranteed to be in the No-Intro file, so
        # Parent/Clone data is available.
        else:
            if rom['nointro_status'] == 'Miss': rom_nointro_name = rom['m_name']
            else:                               rom_nointro_name = F.base_noext
            # log_debug('  rom_nointro_name "{0}"'.format(rom_nointro_name))
            nointro_rom = roms_nointro[rom_nointro_name]

            # >> ROM is a parent
            if nointro_rom['cloneof'] == '':
                parent_id = rom['id']
                if parent_id not in roms_pclone_index_by_id:
                    roms_pclone_index_by_id[parent_id] = []
            # >> ROM is a clone
            else:
                parent_name = nointro_rom['cloneof']
                parent_id = names_to_ids_dic[parent_name]
                clone_id = rom['id']
                if parent_id in roms_pclone_index_by_id:
                    roms_pclone_index_by_id[parent_id].append(clone_id)
                else:
                    roms_pclone_index_by_id[parent_id] = []
                    roms_pclone_index_by_id[parent_id].append(clone_id)

    return roms_pclone_index_by_id

#
# parent_roms = { AEL ROM dictionary having parents only }
#
def fs_generate_parent_ROMs(roms, roms_pclone_index):
    parent_roms = {}

    for rom_id in roms_pclone_index:
        if rom_id == 'Unknown ROMs':
            parent_roms[rom_id] = {
                'id' : 'Unknown ROMs',
                'm_name' : '[Unknown ROMs]',
                'finished' : False,
                'nointro_status' : 'Have',
                'm_year' : '2016', 'm_genre' : 'Special genre', 'm_plot' : '',
                'm_studio' : 'Various', 'm_rating' : '',
                's_title' : '', 's_snap' : '', 's_boxfront' : '', 's_boxback' : '',
                's_cartridge' : '', 's_map' : '', 's_trailer' : '',
                'num_clones_str' : unicode(len(roms_pclone_index[rom_id]))
            }
        else:
            parent_roms[rom_id] = roms[rom_id]
            parent_roms[rom_id]['num_clones_str'] = unicode(len(roms_pclone_index[rom_id]))

    return parent_roms

#
# Loads offline scraper information XML file.
#
def fs_load_GameInfo_XML(xml_file):
    __debug_xml_parser = 0
    games = {}

    # --- Check that file exists ---
    if not os.path.isfile(xml_file):
        log_error("Cannot load file '{0}'".format(xml_file))
        return games

    # --- Parse using cElementTree ---
    log_verb('fs_load_GameInfo_XML() Loading "{0}"'.format(xml_file))
    try:
        xml_tree = ET.parse(xml_file)
    except ET.ParseError, e:
        log_error('(ParseError) Exception parsing XML categories.xml')
        log_error('(ParseError) {0}'.format(str(e)))
        return roms
    xml_root = xml_tree.getroot()
    for game_element in xml_root:
        if __debug_xml_parser:
            log_debug('=== Root child tag "{0}" ==='.format(game_element.tag))

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
                if __debug_xml_parser: log_debug('Tag "{0}" --> "{1}"'.format(xml_tag, xml_text))
                game[xml_tag] = xml_text
            key = game['name']
            games[key] = game

    return games

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
    log_info('fs_fix_launchers_xml() Input  {0}'.format(launchers_xml_path.getOriginalPath()))
    log_info('fs_fix_launchers_xml() Output {0}'.format(sanitized_xml_path.getOriginalPath()))
    with open(launchers_xml_path.getPath()) as f_in:
        lines = f_in.readlines()
    f_out = open(sanitized_xml_path.getPath(), 'w')
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
        f_out.write(line.encode('utf-8'))
        line_counter += 1
    f_out.close()
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
    log_info('fs_load_legacy_AL_launchers() Loading "{0}"'.format(AL_launchers_filepath.getOriginalPath()))
    try:
        xml_tree = ET.parse(AL_launchers_filepath.getPath())
    except ET.ParseError, e:
        log_error('ParseError exception parsing XML categories.xml')
        log_error('ParseError: {0}'.format(str(e)))
        kodi_notify_warn('ParseError exception reading launchers.xml')
        return
    xml_root = xml_tree.getroot()

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
                            'minimize'    : 'false',
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
# When called from "Edit ROM" --> "Edit Metadata" --> "Import metadata from NFO file" function should
# be verbose and print notifications.
# However, this function is also used to export launcher ROMs in bulk in
# "Edit Launcher" --> "Manage ROM List" --> "Export ROMs metadata to NFO files". In that case, function
# must not be verbose because it can be called thousands of times for big ROM sets!
#
def fs_export_ROM_NFO(rom, verbose = True):
    F = misc_split_path(rom['filename'])
    nfo_file_path  = F.path_noext + '.nfo'
    log_debug('fs_export_ROM_NFO() Exporting "{0}"'.format(nfo_file_path))

    # Always overwrite NFO files.
    nfo_content = []
    nfo_content.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
    nfo_content.append('<game>\n')
    nfo_content.append(XML_text('title',     rom['m_name']))
    nfo_content.append(XML_text('year',      rom['m_year']))
    nfo_content.append(XML_text('genre',     rom['m_genre']))
    nfo_content.append(XML_text('publisher', rom['m_studio']))
    nfo_content.append(XML_text('rating',    rom['m_rating']))
    nfo_content.append(XML_text('plot',      rom['m_plot']))
    nfo_content.append('</game>\n')
    full_string = ''.join(nfo_content).encode('utf-8')
    try:
        usock = open(nfo_file_path, 'w')
        usock.write(full_string)
        usock.close()
    except:
        if verbose:
            kodi_notify_warn('Error writing {0}'.format(nfo_file_path))
        log_error("fs_export_ROM_NFO() Exception writing '{0}'".format(nfo_file_path))
        return
    if verbose:
        kodi_notify('Created NFO file {0}'.format(nfo_file_path))

    return

#
# Reads an NFO file with ROM information.
# Modifies roms dictionary even outside this function. See comments in fs_import_launcher_NFO()
# See comments in fs_export_ROM_NFO() about verbosity.
# About reading files in Unicode http://stackoverflow.com/questions/147741/character-reading-from-file-in-python
#
def fs_import_ROM_NFO(roms, romID, verbose = True):
    F = misc_split_path(roms[romID]['filename'])
    nfo_file_path = F.path_noext + '.nfo'
    log_debug('fs_export_ROM_NFO() Loading "{0}"'.format(nfo_file_path))

    # --- Import data ---
    if os.path.isfile(nfo_file_path):
        # >> Read file, put in a string and remove line endings.
        # >> We assume NFO files are UTF-8. Decode data to Unicode.
        # file = open(nfo_file_path, 'rt')
        file = codecs.open(nfo_file_path, 'r', 'utf-8')
        nfo_str = file.read().replace('\r', '').replace('\n', '')
        file.close()

        # Search for items
        item_title     = re.findall('<title>(.*?)</title>', nfo_str)
        item_year      = re.findall('<year>(.*?)</year>', nfo_str)
        item_genre     = re.findall('<genre>(.*?)</genre>', nfo_str)
        item_publisher = re.findall('<publisher>(.*?)</publisher>', nfo_str)
        item_rating    = re.findall('<rating>(.*?)</rating>', nfo_str)
        item_plot      = re.findall('<plot>(.*?)</plot>', nfo_str)

        if len(item_title) > 0:     roms[romID]['m_name']   = text_unescape_XML(item_title[0])
        if len(item_year) > 0:      roms[romID]['m_year']   = text_unescape_XML(item_year[0])
        if len(item_genre) > 0:     roms[romID]['m_genre']  = text_unescape_XML(item_genre[0])
        if len(item_publisher) > 0: roms[romID]['m_studio'] = text_unescape_XML(item_publisher[0])
        if len(item_rating) > 0:    roms[romID]['m_rating'] = text_unescape_XML(item_rating[0])
        if len(item_plot) > 0:      roms[romID]['m_plot']   = text_unescape_XML(item_plot[0])

        if verbose:
            kodi_notify('Imported {0}'.format(nfo_file_path))
    else:
        if verbose:
            kodi_notify_warn('NFO file not found {0}'.format(nfo_file_path))
        log_debug("fs_import_ROM_NFO() NFO file not found '{0}'".format(nfo_file_path))
        return False

    return True

#
# This file is called by the ROM scanner to read a ROM info file automatically.
# NFO file existence is checked before calling this function, so NFO file must always exist.
#
def fs_load_NFO_file_scanner(nfo_file_path):
    nfo_dic = {'title' : '', 'year' : '', 'genre' : '', 'publisher' : '', 'rating' : '', 'plot' : '' }

    # >> Read file, put in a string and remove line endings
    file = codecs.open(nfo_file_path.getPath(), 'r', 'utf-8')
    nfo_str = file.read().replace('\r', '').replace('\n', '')
    file.close()

    # Search for items
    item_title     = re.findall('<title>(.*?)</title>', nfo_str)
    item_year      = re.findall('<year>(.*?)</year>', nfo_str)
    item_genre     = re.findall('<genre>(.*?)</genre>', nfo_str)
    item_publisher = re.findall('<publisher>(.*?)</publisher>', nfo_str)
    item_rating    = re.findall('<rating>(.*?)</rating>', nfo_str)
    item_plot      = re.findall('<plot>(.*?)</plot>', nfo_str)

    if len(item_title) > 0:     nfo_dic['title']     = text_unescape_XML(item_title[0])
    if len(item_year) > 0:      nfo_dic['year']      = text_unescape_XML(item_year[0])
    if len(item_genre) > 0:     nfo_dic['genre']     = text_unescape_XML(item_genre[0])
    if len(item_publisher) > 0: nfo_dic['publisher'] = text_unescape_XML(item_publisher[0])
    if len(item_rating) > 0:    nfo_dic['rating']    = text_unescape_XML(item_rating[0])
    if len(item_plot) > 0:      nfo_dic['plot']      = text_unescape_XML(item_plot[0])

    return nfo_dic

#
# Standalone launchers:
#   NFO files are stored in self.settings["launchers_nfo_dir"] if not empty.
#   If empty, it defaults to DEFAULT_LAUN_NFO_DIR.
#
# ROM launchers:
#   Same as standalone launchers.
#
def fs_export_launcher_NFO(nfo_file_path, launcher):
    # --- Get NFO file name ---
    log_debug('fs_export_launcher_NFO() Exporting launcher NFO "{0}"'.format(nfo_file_path))

    # If NFO file does not exist then create them. If it exists, overwrite.
    nfo_content = []
    nfo_content.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
    nfo_content.append('<launcher>\n')
    nfo_content.append(XML_text('year',      launcher['m_year']))
    nfo_content.append(XML_text('genre',     launcher['m_genre']))
    nfo_content.append(XML_text('publisher', launcher['m_studio']))
    nfo_content.append(XML_text('rating',    launcher['m_rating']))
    nfo_content.append(XML_text('plot',      launcher['m_plot']))
    nfo_content.append('</launcher>\n')
    full_string = ''.join(nfo_content).encode('utf-8')
    try:
        f = open(nfo_file_path, 'w')
        f.write(full_string)
        f.close()
    except:
        kodi_notify_warn('Exception writing NFO file {0}'.format(os.path.basename(nfo_file_path)))
        log_error("fs_export_launcher_NFO() Exception writing'{0}'".format(nfo_file_path))
        return False

    kodi_notify('Created NFO file {0}'.format(os.path.basename(nfo_file_path)))
    log_debug("fs_export_launcher_NFO() Created '{0}'".format(nfo_file_path))

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
#
def fs_import_launcher_NFO(nfo_file_path, launchers, launcherID):
    # --- Get NFO file name ---
    log_debug('fs_import_launcher_NFO() Importing launcher NFO "{0}"'.format(nfo_file_path))

    # --- Import data ---
    if os.path.isfile(nfo_file_path):
        # >> Read NFO file data
        try:
            file = codecs.open(nfo_file_path, 'r', 'utf-8')
            item_nfo = file.read().replace('\r', '').replace('\n', '')
            file.close()
        except:
            kodi_notify_warn('Exception reading NFO file {0}'.format(os.path.basename(nfo_file_path)))
            log_error("fs_import_launcher_NFO() Exception reading NFO file '{0}'".format(nfo_file_path))
            return False
        # log_debug("fs_import_launcher_NFO() item_nfo '{0}'".format(item_nfo))
    else:
        kodi_notify_warn('NFO file not found {0}'.format(os.path.basename(nfo_file_path)))
        log_info("fs_import_launcher_NFO() NFO file not found '{0}'".format(nfo_file_path))
        return False

    # Find data
    item_year      = re.findall('<year>(.*?)</year>',           item_nfo)
    item_genre     = re.findall('<genre>(.*?)</genre>',         item_nfo)
    item_publisher = re.findall('<publisher>(.*?)</publisher>', item_nfo)
    item_rating    = re.findall('<rating>(.*?)</rating>',       item_nfo)
    item_plot      = re.findall('<plot>(.*?)</plot>',           item_nfo)
    # log_debug("fs_import_launcher_NFO() item_year      '{0}'".format(item_year[0]))
    # log_debug("fs_import_launcher_NFO() item_publisher '{0}'".format(item_publisher[0]))
    # log_debug("fs_import_launcher_NFO() item_genre     '{0}'".format(item_genre[0]))
    # log_debug("fs_import_launcher_NFO() item_plot      '{0}'".format(item_plot[0]))

    # >> Careful about object mutability! This should modify the dictionary
    # >> passed as argument outside this function.
    if item_year:      launchers[launcherID]['m_year']   = text_unescape_XML(item_year[0])
    if item_genre:     launchers[launcherID]['m_genre']  = text_unescape_XML(item_genre[0])
    if item_publisher: launchers[launcherID]['m_studio'] = text_unescape_XML(item_publisher[0])
    if item_rating:    launchers[launcherID]['m_rating'] = text_unescape_XML(item_rating[0])
    if item_plot:      launchers[launcherID]['m_plot']   = text_unescape_XML(item_plot[0])

    kodi_notify('Imported {0}'.format(os.path.basename(nfo_file_path)))
    log_verb("fs_import_launcher_NFO() Imported '{0}'".format(nfo_file_path))

    return True

def fs_get_launcher_NFO_name(settings, launcher):
    launcher_name = launcher['m_name']
    nfo_dir = settings['launchers_asset_dir']
    nfo_file_path = os.path.join(nfo_dir, launcher_name + '.nfo')
    log_debug("fs_get_launcher_NFO_name() nfo_file_path = '{0}'".format(nfo_file_path))

    return nfo_file_path

#
# Look at the launcher NFO files for a reference implementation.
# Categories NFO files only have genre and plot.
#
def fs_export_category_NFO(nfo_file_path, category):
    # --- Get NFO file name ---
    log_debug('fs_export_category_NFO() Exporting launcher NFO "{0}"'.format(nfo_file_path))

    # If NFO file does not exist then create them. If it exists, overwrite.
    nfo_content = []
    nfo_content.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
    nfo_content.append('<category>\n')
    nfo_content.append(XML_text('genre',  category['m_genre']))
    nfo_content.append(XML_text('rating', category['m_rating']))
    nfo_content.append(XML_text('plot',   category['m_plot']))
    nfo_content.append('</category>\n')
    full_string = ''.join(nfo_content).encode('utf-8')
    try:
        f = open(nfo_file_path, 'w')
        f.write(full_string)
        f.close()
    except:
        kodi_notify_warn('Exception writing NFO file {0}'.format(os.path.basename(nfo_file_path)))
        log_error("fs_export_category_NFO() Exception writing'{0}'".format(nfo_file_path))
        return False
    kodi_notify('Created NFO file {0}'.format(os.path.basename(os.path.basename(nfo_file_path))))
    log_debug("fs_export_category_NFO() Created '{0}'".format(nfo_file_path))

    return True

def fs_import_category_NFO(nfo_file_path, categories, categoryID):
    # --- Get NFO file name ---
    log_debug('fs_import_category_NFO() Importing launcher NFO "{0}"'.format(nfo_file_path))

    # --- Import data ---
    if os.path.isfile(nfo_file_path):
        try:
            file = codecs.open(nfo_file_path, 'r', 'utf-8')
            item_nfo = file.read().replace('\r', '').replace('\n', '')
            file.close()
        except:
            kodi_notify_warn('Exception reading NFO file {0}'.format(os.path.basename(nfo_file_path)))
            log_error("fs_import_category_NFO() Exception reading NFO file '{0}'".format(nfo_file_path))
            return False
    else:
        kodi_notify_warn('NFO file not found {0}'.format(os.path.basename(nfo_file_path)))
        log_error("fs_import_category_NFO() NFO file not found '{0}'".format(nfo_file_path))
        return False

    item_genre  = re.findall('<genre>(.*?)</genre>', item_nfo)
    item_rating = re.findall('<rating>(.*?)</rating>', item_nfo)
    item_plot   = re.findall('<plot>(.*?)</plot>',   item_nfo)

    if item_genre:  categories[categoryID]['m_genre']  = text_unescape_XML(item_genre[0])
    if item_rating: categories[categoryID]['m_rating'] = text_unescape_XML(item_rating[0])
    if item_plot:   categories[categoryID]['m_plot']   = text_unescape_XML(item_plot[0])

    kodi_notify('Imported {0}'.format(os.path.basename(nfo_file_path)))
    log_verb("fs_import_category_NFO() Imported '{0}'".format(nfo_file_path))

    return True

def fs_get_category_NFO_name(settings, category):
    category_name = category['m_name']
    nfo_dir = settings['categories_asset_dir']
    nfo_file_path = os.path.join(nfo_dir, category_name + '.nfo')
    log_debug("fs_get_category_NFO_name() nfo_file_path = '{0}'".format(nfo_file_path))

    return nfo_file_path

#
# Collection NFO files. Same as Cateogory NFO files.
#
def fs_export_collection_NFO(nfo_file_path, collection):
    # --- Get NFO file name ---
    log_debug('fs_export_collection_NFO() Exporting launcher NFO "{0}"'.format(nfo_file_path.getPath()))

    # If NFO file does not exist then create them. If it exists, overwrite.
    nfo_content = []
    nfo_content.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
    nfo_content.append('<collection>\n')
    nfo_content.append(XML_text('genre',  collection['m_genre']))
    nfo_content.append(XML_text('rating', collection['m_rating']))
    nfo_content.append(XML_text('plot',   collection['m_plot']))
    nfo_content.append('</collection>\n')
    full_string = ''.join(nfo_content).encode('utf-8')
    try:
        f = open(nfo_file_path.getPath(), 'w')
        f.write(full_string)
        f.close()
    except:
        kodi_notify_warn('Exception writing NFO file {0}'.format(nfo_file_path.getName()))
        log_error("fs_export_collection_NFO() Exception writing'{0}'".format(nfo_file_path.getPath()))
        return False
    kodi_notify('Created NFO file {0}'.format(os.path.basename(nfo_file_path.getName())))
    log_debug("fs_export_collection_NFO() Created '{0}'".format(nfo_file_path.getPath()))

    return True

def fs_import_collection_NFO(nfo_file_path, collections, launcherID):
    # --- Get NFO file name ---
    log_debug('fs_import_collection_NFO() Importing launcher NFO "{0}"'.format(nfo_file_path.getOriginalPath()))

    # --- Import data ---
    if os.path.isfile(nfo_file_path.getPath()):
        try:
            file = codecs.open(nfo_file_path.getPath(), 'r', 'utf-8')
            item_nfo = file.read().replace('\r', '').replace('\n', '')
            file.close()
        except:
            kodi_notify_warn('Exception reading NFO file {0}'.format(nfo_file_path.getName()))
            log_error("fs_import_collection_NFO() Exception reading NFO file '{0}'".format(nfo_file_path.getPath()))
            return False
    else:
        kodi_notify_warn('NFO file not found {0}'.format(os.path.basename(nfo_file_path.getOriginalPath())))
        log_error("fs_import_collection_NFO() NFO file not found '{0}'".format(nfo_file_path.getPath()))
        return False

    item_genre  = re.findall('<genre>(.*?)</genre>', item_nfo)
    item_rating = re.findall('<rating>(.*?)</rating>', item_nfo)
    item_plot   = re.findall('<plot>(.*?)</plot>',   item_nfo)

    if item_genre:  collections[launcherID]['m_genre']  = text_unescape_XML(item_genre[0])
    if item_rating: collections[launcherID]['m_rating'] = text_unescape_XML(item_rating[0])
    if item_plot:   collections[launcherID]['m_plot']   = text_unescape_XML(item_plot[0])

    kodi_notify('Imported {0}'.format(os.path.basename(nfo_file_path.getOriginalPath())))
    log_verb("fs_import_collection_NFO() Imported '{0}'".format(nfo_file_path.getOriginalPath()))

    return True

def fs_get_collection_NFO_name(settings, collection):
    collection_name = collection['m_name']
    nfo_dir = settings['collections_asset_dir']
    nfo_file_path = os.path.join(nfo_dir, collection_name + '.nfo')
    log_debug("fs_get_collection_NFO_name() nfo_file_path = '{0}'".format(nfo_file_path))

    return nfo_file_path

# -------------------------------------------------------------------------------------------------
# Filesystem helper class
# This class always takes and returns Unicode string paths. Decoding to UTF-8 must be done in
# caller code.
# A) Transform paths like smb://server/directory/ into \\server\directory\
# B) Use xbmc.translatePath() for paths starting with special://
# -------------------------------------------------------------------------------------------------
class FileName:
    # pathString must be a Unicode string object
    def __init__(self, pathString):
        self.originalPath = pathString
        self.path         = pathString
        
        # --- Path transformation ---
        if self.originalPath.lower().startswith('smb:'):
            self.path = self.path.replace('smb:', '')
            self.path = self.path.replace('SMB:', '')
            self.path = self.path.replace('//', '\\\\')
            self.path = self.path.replace('/', '\\')

        elif self.originalPath.lower().startswith('special:'):
            self.path = xbmc.translatePath(self.path)

    def join(self, arg):
        self.path         = os.path.join(self.path, arg)
        self.originalPath = os.path.join(self.originalPath, arg)

    def getSubPath(self, *args):
        child = FileName(self.originalPath)
        for arg in args:
            child.join(arg)

        return child

    # See http://blog.teamtreehouse.com/operator-overloading-python
    # other is a FileName object. other originalPath is expected to be a subdirectory (path
    # transformation not required)
    def __add__(self, other):
        current_path = self.originalPath
        if type(other) is FileName:  other_path = other.originalPath
        elif type(other) is unicode: other_path = other
        elif type(other) is str:     other_path = other.decode('utf-8')
        else: raise NameError('Unknown type for overloaded + in FileName object')
        new_path = os.path.join(current_path, other_path)
        child    = FileName(new_path)

        return child

    def escapeQuotes(self):
        self.path = self.path.replace("'", "\\'")
        self.path = self.path.replace('"', '\\"')

    # ---------------------------------------------------------------------------------------------
    # Decomposes a file name path or directory into its constituents
    #   FileName.getPath()            Full path                                     /home/Wintermute/Sonic.zip
    #   FileName.getPath_noext()      Full path with no extension                   /home/Wintermute/Sonic
    #   FileName.getDirname()         Directory name of file. Does not end in '/'   /home/Wintermute
    #   FileName.getBasename()        File name with no path                        Sonic.zip
    #   FileName.getBasename_noext()  File name with no path and no extension       Sonic
    #   FileName.getExt()             File extension                                .zip
    # ---------------------------------------------------------------------------------------------
    def getPath(self):
        return self.path

    def getOriginalPath(self):
        return self.originalPath

    def getPath_noext(self):
        root, ext = os.path.splitext(self.path)

        return root

    def getDirname(self):
        return os.path.dirname(self.path)

    def getBasename(self):
        return os.path.basename(self.path)

    def getBasename_noext(self):
        basename  = os.path.basename(self.path)
        root, ext = os.path.splitext(basename)
        
        return root

    def getFileExtension(self):
        root, ext = os.path.splitext(self.path)
        
        return ext

    # ---------------------------------------------------------------------------------------------
    # Scanner functions
    # ---------------------------------------------------------------------------------------------
    def scanFilesInPath(self, mask):
        files = []
        filenames = os.listdir(self.path)
        for filename in fnmatch.filter(filenames, mask):
            files.append(os.path.join(self.path, filename))

        return files

    def scanFilesInPathAsPaths(self, mask):
        files = []
        filenames = os.listdir(self.path)
        for filename in fnmatch.filter(filenames, mask):
            files.append(Path(os.path.join(self.path, filename)))

        return files

    def recursiveScanFilesInPath(self, mask):
        files = []
        for root, dirs, foundfiles in os.walk(self.path):
            for filename in fnmatch.filter(foundfiles, mask):
                files.append(os.path.join(root, filename))

        return files

    # ---------------------------------------------------------------------------------------------
    # Filesystem functions
    # ---------------------------------------------------------------------------------------------
    def stat(self):
        return os.stat(self.path)

    def exists(self):
        return os.path.exists(self.path)

    def isdir(self):
        return os.path.isdir(self.path)
        
    def isfile(self):
        return os.path.isfile(self.path)

    def makedirs(self):
        if not os.path.exists(self.path): 
            os.makedirs(self.path)

    def remove(self):
        os.remove(self.path)

    def unlink(self):
        os.unlink(self.path)

    def rename(self, to):
        os.rename(self.path, to.getPath())
