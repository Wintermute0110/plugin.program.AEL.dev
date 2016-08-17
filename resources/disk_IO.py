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
    c = {'id' : u'',
         'm_name' : u'',
         'm_genre' : u'',
         'm_rating' : u'',
         'm_plot' : u'',
         'finished' : False,
         'default_thumb' : 's_thumb',
         'default_fanart' : 's_fanart',
         's_thumb' : u'',
         's_fanart' : u'',
         's_banner' : u'',
         's_flyer' : u'',
         's_trailer' : u''
         }

    return c

def fs_new_launcher():
    l = {'id' : u'',
         'm_name' : u'',
         'm_year' : u'', 
         'm_genre' : u'',
         'm_studio' : u'',
         'm_rating' : u'',
         'm_plot' : u'',
         'platform' : u'',
         'categoryID' : u'',
         'application' : u'',
         'args' : u'',
         'rompath' : u'',
         'romext' : u'',
         'finished': False,
         'minimize' : False,
         'roms_base_noext' : u'',
         'nointro_xml_file' : u'',
         'timestamp_launcher' : 0.0,
         'timestamp_report' : 0.0,
         'default_thumb' : 's_thumb',
         'default_fanart' : 's_fanart',
         'roms_default_thumb' : 's_title',
         'roms_default_fanart' : 's_fanart',
         's_thumb' : u'',
         's_fanart' : u'',
         's_banner' : u'',
         's_flyer' : u'',
         's_trailer' : u'',
         'path_title' : u'',
         'path_snap' : u'',
         'path_fanart' : u'',
         'path_banner' : u'',
         'path_clearlogo' : u'',
         'path_boxfront' : u'',
         'path_boxback' : u'',
         'path_cartridge' : u'',
         'path_flyer' : u'',
         'path_map' : u'',
         'path_manual' : u'',
         'path_trailer' : u''
    }

    return l

# Mandatory variables in XML:
# id              string MD5 hash
# name            string ROM name
# finished        bool ['True', 'False'] default 'False'
# nointro_status  string ['Have', 'Miss', 'Unknown', 'None'] default 'None'
def fs_new_rom():
    r = {'id' : u'',
         'm_name' : u'',
         'm_year' : u'',
         'm_genre' : u'',
         'm_studio' : u'',         
         'm_rating' : u'',
         'm_plot' : u'',
         'filename' : u'',
         'altapp' : u'',
         'altarg' : u'',
         'finished' : False,
         'nointro_status' : 'None',
         's_title' : u'',
         's_snap' : u'',
         's_fanart' : u'',
         's_banner' : u'',
         's_clearlogo' : u'',
         's_boxfront' : u'',
         's_boxback' : u'',
         's_cartridge' : u'',
         's_flyer' : u'',
         's_map' : u'',
         's_manual' : u'',
         's_trailer' : u''
    }

    return r

#
# Note that Virtual Launchers ROMs use the Favourite ROMs data model.
# Missing ROMs are not allowed in Favourites or Virtual Launchers.
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
    
    # >> Copy launcher stuff into Favourite ROM
    favourite['launcherID']  = launcher['id']
    favourite['platform']    = launcher['platform']
    favourite['application'] = launcher['application']
    favourite['args']        = launcher['args']
    favourite['rompath']     = launcher['rompath']
    favourite['romext']      = launcher['romext']
    favourite['minimize']    = launcher['minimize']
    
    # >> Favourite ROM unique fields
    favourite['fav_status']  = u'OK'

    return favourite

def fs_get_ROMs_basename(category_name, launcher_name, launcherID):
    clean_cat_name = u''.join([i if i in string.printable else '_' for i in category_name]).replace(' ', '_')
    clean_launch_title = u''.join([i if i in string.printable else '_' for i in launcher_name]).replace(' ', '_')
    roms_base_noext = 'roms_' + clean_cat_name + '_' + clean_launch_title + '_' + launcherID[0:6]
    log_verb('fs_get_ROMs_basename() roms_base_noext "{0}"'.format(roms_base_noext))

    return roms_base_noext

def fs_get_collection_ROMs_basename(collection_name, collectionID):
    clean_collection_name = u''.join([i if i in string.printable else '_' for i in collection_name]).replace(' ', '_')
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
        str_list.append('<advanced_emulator_launcher version="1">\n')

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
            # XML text returns UFT-8 encoded strings. Dictionary strings are in Unicode!
            str_list.append('<category>\n')
            str_list.append(XML_text('id', categoryID))
            str_list.append(XML_text('m_name', category['m_name']))
            str_list.append(XML_text('m_genre', category['m_genre']))
            str_list.append(XML_text('m_plot', category['m_plot']))
            str_list.append(XML_text('m_rating', category['m_rating']))
            str_list.append(XML_text('finished', unicode(category['finished'])))
            str_list.append(XML_text('default_thumb', category['default_thumb']))
            str_list.append(XML_text('default_fanart', category['default_fanart']))
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
            str_list.append(XML_text('timestamp_launcher', unicode(launcher['timestamp_launcher'])))
            str_list.append(XML_text('timestamp_report', unicode(launcher['timestamp_report'])))            
            str_list.append(XML_text('default_thumb', launcher['default_thumb']))
            str_list.append(XML_text('default_fanart', launcher['default_fanart']))
            str_list.append(XML_text('roms_default_thumb', launcher['roms_default_thumb']))
            str_list.append(XML_text('roms_default_fanart', launcher['roms_default_fanart']))
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
        file_obj = open(categories_file, 'w')
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
    log_verb('fs_load_catfile() Loading {0}'.format(categories_file))
    # If there are issues in the XML file ET.parse will fail
    try:
        xml_tree = ET.parse(categories_file)
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

                # Now transform data type depending on tag name
                if xml_tag == 'finished' or xml_tag == 'minimize':
                    xml_bool = True if xml_text == 'True' else False
                    launcher[xml_tag] = xml_bool
                elif xml_tag == 'timestamp_launcher' or xml_tag == 'timestamp_report':
                    xml_float = float(xml_text)
                    launcher[xml_tag] = xml_float

            # Add launcher to categories dictionary
            launchers[launcher['id']] = launcher

    return (update_timestamp, categories, launchers)

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
    roms_file_path = os.path.join(roms_dir, roms_base_noext + u'.xml')

    return roms_file_path

def fs_get_ROMs_JSON_file_path(roms_dir, roms_base_noext):
    roms_file_path = os.path.join(roms_dir, roms_base_noext + u'.json')

    return roms_file_path

#
# This returns XML or JSON depending of what used to store main ROM DB.
# Currently plugin stores launcher ROMs as JSON because is faster than XML.
#
def fs_get_ROMs_file_path(roms_dir, roms_base_noext):
    roms_file_path = os.path.join(roms_dir, roms_base_noext + u'.json')

    return roms_file_path

#
# Write to disk launcher ROMs XML database (OBSOLETE)
#
def fs_write_ROMs_XML(roms_dir, roms_base_noext, roms, launcher):
    # >> Get filename
    roms_xml_file = os.path.join(roms_dir, roms_base_noext + u'.xml')
    log_info('fs_write_ROMs_XML() Saving XML file {0}'.format(roms_xml_file))

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
        kodi_notify_warn(u'(OSError) Cannot write {0} file'.format(roms_xml_file))
        log_error(u'fs_write_ROMs_XML() (OSerror) Cannot write file "{0}"'.format(roms_xml_file))
    except IOError:
        kodi_notify_warn(u'(IOError) Cannot write {0} file'.format(roms_xml_file))
        log_error(u'fs_write_ROMs_XML() (IOError) Cannot write file "{0}"'.format(roms_xml_file))

    # --- We are not busy anymore ---
    kodi_busydialog_OFF()

#
# Loads a launcher XML with the ROMs
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
    log_verb('fs_load_ROMs_XML() Loading XML file {0}'.format(roms_xml_file))
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
    roms_json_file = os.path.join(roms_dir, roms_base_noext + '.json')
    roms_xml_file  = os.path.join(roms_dir, roms_base_noext + '.xml')
    log_info('fs_write_ROMs_JSON() Saving JSON file {0}'.format(roms_json_file))
    log_info('fs_write_ROMs_JSON() Saving XML info  {0}'.format(roms_xml_file))

    # >> JSON files cannot have comments. Write an auxiliar NFO file with same prefix
    # >> to store launcher information for a set of ROMs
    try:
        str_list = []
        str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        str_list.append('<advanced_emulator_launcher_ROMs version="1">\n')

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
        file_obj = open(roms_xml_file, 'w')
        file_obj.write(full_string)
        file_obj.close()
    except OSError:
        kodi_notify_warn(u'(OSError) Cannot write {0} file'.format(roms_xml_file))
        log_error(u'fs_write_ROMs_JSON() (OSerror) Cannot write file "{0}"'.format(roms_xml_file))
    except IOError:
        kodi_notify_warn(u'(IOError) Cannot write {0} file'.format(roms_xml_file))
        log_error(u'fs_write_ROMs_JSON() (IOError) Cannot write file "{0}"'.format(roms_xml_file))

    # >> Write ROMs JSON dictionary.
    # >> See http://stackoverflow.com/questions/18337407/saving-utf-8-texts-in-json-dumps-as-utf8-not-as-u-escape-sequence
    try:
        with io.open(roms_json_file, 'w', encoding = 'utf-8') as file:
            # >> json_unicode is either str or unicode
            # >> See https://docs.python.org/2.7/library/json.html#json.dumps
            json_unicode = json.dumps(roms, ensure_ascii = False, sort_keys = True, 
                                      indent = JSON_indent, separators = JSON_separators)
            file.write(json_unicode.encode('utf-8'))
            file.close()
    except OSError:
        kodi_notify_warn(u'(OSError) Cannot write {0} file'.format(roms_json_file))
    except IOError:
        kodi_notify_warn(u'(IOError) Cannot write {0} file'.format(roms_json_file))

#
# Loads an JSON file containing the Virtual Launcher ROMs
#
def fs_load_ROMs_JSON(roms_dir, roms_base_noext):
    roms = {}

    # --- If file does not exist return empty dictionary ---
    roms_json_file = os.path.join(roms_dir, roms_base_noext + '.json')
    if not os.path.isfile(roms_json_file): return roms

    # --- Parse using json module ---
    # >> On Github issue #8 a user had an empty JSON file for ROMs. This raises
    #    exception exceptions.ValueError and launcher cannot be deleted. Deal
    #    with this exception so at least launcher can be rescanned.
    log_verb('fs_load_ROMs_JSON() Loading JSON file {0}'.format(roms_json_file))
    with open(roms_json_file) as file:
        try:
            roms = json.load(file)
        except ValueError:
            statinfo = os.stat(roms_json_file)
            log_error('fs_load_ROMs_JSON() ValueError exception in json.load() function')
            log_error('fs_load_ROMs_JSON() Dir  {0}'.format(roms_dir))
            log_error('fs_load_ROMs_JSON() File {0}'.format(roms_base_noext + '.json'))
            log_error('fs_load_ROMs_JSON() Size {0}'.format(statinfo.st_size))
        file.close()

    return roms

# -------------------------------------------------------------------------------------------------
# Favourite ROMs
# -------------------------------------------------------------------------------------------------
#
# Write to disk Favourite ROMs in XML
#
def fs_write_Favourites_XML(roms_xml_file, roms):
    log_info('fs_write_Favourites_XML() Saving XML file {0}'.format(roms_xml_file))
    try:
        str_list = []
        str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        str_list.append('<advanced_emulator_launcher_Favourites version="1">\n')
        # Size optimization: only write in the XML fields which are not ''. This
        # will save A LOT of disk space and reduce loading times (at a cost of
        # some writing time, but writing is much less frequent than reading).
        for romID in sorted(roms, key = lambda x : roms[x]["name"]):
            rom = roms[romID]
            str_list.append('<rom>\n')
            str_list.append(XML_text('id', romID))
            str_list.append(XML_text('name', rom['name']))
            if rom['filename']:    str_list.append(XML_text('filename', rom['filename']))
            if rom['thumb']:       str_list.append(XML_text('thumb', rom['thumb']))
            if rom['fanart']:      str_list.append(XML_text('fanart', rom['fanart']))
            if rom['trailer']:     str_list.append(XML_text('trailer', rom['trailer']))
            if rom['custom']:      str_list.append(XML_text('custom', rom['custom']))
            if rom['genre']:       str_list.append(XML_text('genre', rom['genre']))
            if rom['year']:        str_list.append(XML_text('year', rom['year']))
            if rom['studio']:      str_list.append(XML_text('studio', rom['studio']))
            if rom['plot']:        str_list.append(XML_text('plot', rom['plot']))
            if rom['altapp']:      str_list.append(XML_text('altapp', rom['altapp']))
            if rom['altarg']:      str_list.append(XML_text('altarg', rom['altarg']))
            str_list.append(XML_text('finished', unicode(rom['finished'])))
            str_list.append(XML_text('nointro_status', rom['nointro_status']))
            if rom['launcherID']:  str_list.append(XML_text('launcherID', rom['launcherID']))
            if rom['platform']:    str_list.append(XML_text('platform', rom['platform']))
            if rom['application']: str_list.append(XML_text('application', rom['application']))
            if rom['args']:        str_list.append(XML_text('args', rom['args']))
            if rom['rompath']:     str_list.append(XML_text('rompath', rom['rompath']))
            if rom['romext']:      str_list.append(XML_text('romext', rom['romext']))
            str_list.append(XML_text('minimize', unicode(rom['minimize'])))
            str_list.append(XML_text('fav_status', rom['fav_status']))
            str_list.append('</rom>\n')
        str_list.append('</advanced_emulator_launcher_Favourites>\n')
        full_string = ''.join(str_list).encode('utf-8')
        file_obj = open(roms_xml_file, 'w')
        file_obj.write(full_string)
        file_obj.close()
    except OSError:
        kodi_notify('Cannot write {0} file (OSError)'.format(roms_xml_file))
    except IOError:
        kodi_notify('Cannot write {0} file (IOError)'.format(roms_xml_file))

#
# Loads an XML file containing the favourite ROMs
# It is basically the same as ROMs, but with some more fields to store launching application data.
#
def fs_load_Favourites_XML(roms_xml_file):
    __debug_xml_parser = 0
    roms = {}

    # --- If file does not exist return empty dictionary ---
    if not os.path.isfile(roms_xml_file): return roms

    # --- Parse using cElementTree ---
    log_verb('fs_load_Favourites_XML() Loading XML file {0}'.format(roms_xml_file))
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
            rom = fs_new_favourite_rom()
            for rom_child in root_element:
                # By default read strings
                xml_text = rom_child.text if rom_child.text is not None else ''
                xml_text = text_unescape_XML(xml_text)
                xml_tag  = rom_child.tag
                if __debug_xml_parser: log_debug('{0} --> {1}'.format(xml_tag, xml_text))
                rom[xml_tag] = xml_text

                # Now transform data depending on tag name
                if xml_tag == 'finished' or xml_tag == 'minimize':
                    xml_bool = True if xml_text == 'True' else False
                    rom[xml_tag] = xml_bool
                elif xml_tag == 'fav_status':
                    xml_string = xml_text if xml_text in ['OK', 'Unlinked', 'Broken'] else 'OK'
                    rom[xml_tag] = xml_string
            roms[rom['id']] = rom

    return roms

def fs_write_Favourites_JSON(roms_json_file, roms):
    log_info('fs_write_Favourites_JSON() Saving JSON file {0}'.format(roms_json_file))
    try:
        with io.open(roms_json_file, 'w', encoding='utf-8') as file:
            json_unicode = json.dumps(roms, ensure_ascii = False, sort_keys = True, 
                                      indent = JSON_indent, separators = JSON_separators)
            file.write(json_unicode.encode('utf-8'))
            file.close()
    except OSError:
        kodi_notify_warn(u'(OSError) Cannot write {0} file'.format(roms_json_file))
    except IOError:
        kodi_notify_warn(u'(IOError) Cannot write {0} file'.format(roms_json_file))

#
# Loads an JSON file containing the Favourite ROMs
#
def fs_load_Favourites_JSON(roms_json_file):
    roms = {}

    # --- If file does not exist return empty dictionary ---
    if not os.path.isfile(roms_json_file): return roms

    # --- Parse using cElementTree ---
    log_verb('fs_load_Favourites_JSON() Loading JSON file {0}'.format(roms_json_file))
    with open(roms_json_file) as file:    
        try:
            roms = json.load(file)
        except ValueError:
            statinfo = os.stat(roms_json_file)
            log_error('fs_load_Favourites_JSON() ValueError exception in json.load() function')
            log_error('fs_load_Favourites_JSON() File {0}'.format(roms_json_file))
            log_error('fs_load_Favourites_JSON() Size {0}'.format(statinfo.st_size))
        file.close()

    return roms

# -------------------------------------------------------------------------------------------------
# ROM Collections
# -------------------------------------------------------------------------------------------------
def fs_write_Collection_index_XML(collections_xml_file, collections):
    log_info('fs_write_Collection_index_XML() Saving XML file {0}'.format(collections_xml_file))
    try:
        str_list = []
        str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        str_list.append('<advanced_emulator_launcher_Collection_index version="1">\n')

        # --- Control information ---
        _t = time.time()
        str_list.append('<control>\n')
        str_list.append(XML_text('update_timestamp', unicode(_t)))
        str_list.append('</control>\n')

        # --- Virtual Launchers ---
        for collection_id in sorted(collections, key = lambda x : collections[x]['name']):
            collection = collections[collection_id]
            str_list.append('<Collection>\n')
            str_list.append(XML_text('id', collection['id']))
            str_list.append(XML_text('name', collection['name']))
            str_list.append(XML_text('roms_base_noext', collection['roms_base_noext']))
            str_list.append('</Collection>\n')
        str_list.append('</advanced_emulator_launcher_Collection_index>\n')
        full_string = ''.join(str_list).encode('utf-8')
        file_obj = open(collections_xml_file, 'w')
        file_obj.write(full_string)
        file_obj.close()
    except OSError:
        kodi_notify_warn(u'(OSError) Cannot write {0} file'.format(collections_xml_file))
    except IOError:
        kodi_notify_warn(u'(IOError) Cannot write {0} file'.format(collections_xml_file))

def fs_load_Collection_index_XML(collections_xml_file):
    __debug_xml_parser = 0
    update_timestamp = 0.0
    collections = {}

    # --- If file does not exist return empty dictionary ---
    if not os.path.isfile(collections_xml_file): return (collections, update_timestamp)

    # --- Parse using cElementTree ---
    log_verb(u'fs_load_Collection_index_XML() Loading XML file {0}'.format(collections_xml_file))
    try:
        xml_tree = ET.parse(collections_xml_file)
    except ET.ParseError, e:
        log_error('(ParseError) Exception parsing XML categories.xml')
        log_error('(ParseError) {0}'.format(str(e)))
        return roms
    xml_root = xml_tree.getroot()
    for root_element in xml_root:
        if __debug_xml_parser: log_debug(u'Root child {0}'.format(root_element.tag))

        if root_element.tag == 'control':
            for control_child in root_element:
                if control_child.tag == 'update_timestamp':
                    update_timestamp = float(control_child.text) # Convert Unicode to float

        elif root_element.tag == 'Collection':
            collection = { 'id' : u'', 'name' : u'', 'roms_base_noext' : u'' }
            for rom_child in root_element:
                # By default read strings
                xml_text = rom_child.text if rom_child.text is not None else ''
                xml_text = text_unescape_XML(xml_text)
                xml_tag  = rom_child.tag
                if __debug_xml_parser: log_debug('{0} --> {1}'.format(xml_tag, xml_text))
                collection[xml_tag] = xml_text
            collections[collection['id']] = collection

    return (collections, update_timestamp)

def fs_write_Collection_ROMs_JSON(roms_dir, roms_base_noext, roms):
    roms_json_file = os.path.join(roms_dir, roms_base_noext + '.json')
    log_info('fs_write_Collection_ROMs_JSON() Saving JSON file {0}'.format(roms_json_file))
    try:
        with io.open(roms_json_file, 'w', encoding = 'utf-8') as file:
            json_unicode = json.dumps(roms, ensure_ascii = False, sort_keys = True, 
                                      indent = JSON_indent, separators = JSON_separators)
            file.write(json_unicode.encode('utf-8'))
            file.close()
    except OSError:
        kodi_notify_warn(u'(OSError) Cannot write {0} file'.format(roms_json_file))
    except IOError:
        kodi_notify_warn(u'(IOError) Cannot write {0} file'.format(roms_json_file))

#
# Loads an JSON file containing the Virtual Launcher ROMs
#
def fs_load_Collection_ROMs_JSON(roms_dir, roms_base_noext):
    roms = []

    # --- If file does not exist return empty dictionary ---
    roms_json_file = os.path.join(roms_dir, roms_base_noext + '.json')
    if not os.path.isfile(roms_json_file): return roms

    # --- Parse using cElementTree ---
    log_verb('fs_load_Collection_ROMs_JSON() Loading JSON file {0}'.format(roms_json_file))
    with open(roms_json_file) as file:    
        try:
            roms = json.load(file)
        except ValueError:
            statinfo = os.stat(roms_json_file)
            log_error('fs_load_Collection_ROMs_JSON() ValueError exception in json.load() function')
            log_error('fs_load_Collection_ROMs_JSON() Dir  {0}'.format(roms_dir))
            log_error('fs_load_Collection_ROMs_JSON() File {0}'.format(roms_base_noext + '.json'))
            log_error('fs_load_Collection_ROMs_JSON() Size {0}'.format(statinfo.st_size))
        file.close()

    return roms

# -------------------------------------------------------------------------------------------------
# Virtual Categories
# -------------------------------------------------------------------------------------------------
def fs_write_VCategory_XML(roms_xml_file, roms):
    log_info(u'fs_write_VCategory_XML() Saving XML file {0}'.format(roms_xml_file))
    try:
        str_list = []
        str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        str_list.append('<advanced_emulator_launcher_Virtual_Category_index version="1">\n')

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
        file_obj = open(roms_xml_file, 'w')
        file_obj.write(full_string)
        file_obj.close()
    except OSError:
        kodi_notify_warn(u'(OSError) Cannot write {0} file'.format(roms_xml_file))
    except IOError:
        kodi_notify_warn(u'(IOError) Cannot write {0} file'.format(roms_xml_file))

#
# Loads an XML file containing Virtual Launcher indices
# It is basically the same as ROMs, but with some more fields to store launching application data.
#
def fs_load_VCategory_XML(roms_xml_file):
    __debug_xml_parser = 0
    update_timestamp = 0.0
    VLaunchers = {}

    # --- If file does not exist return empty dictionary ---
    if not os.path.isfile(roms_xml_file): return (update_timestamp, VLaunchers)

    # --- Parse using cElementTree ---
    log_verb(u'fs_load_VCategory_XML() Loading XML file {0}'.format(roms_xml_file))
    try:
        xml_tree = ET.parse(roms_xml_file)
    except ET.ParseError, e:
        log_error('(ParseError) Exception parsing XML categories.xml')
        log_error('(ParseError) {0}'.format(str(e)))
        return roms
    xml_root = xml_tree.getroot()
    for root_element in xml_root:
        if __debug_xml_parser: log_debug(u'Root child {0}'.format(root_element.tag))

        if root_element.tag == 'control':
            for control_child in root_element:
                if control_child.tag == 'update_timestamp':
                    # >> Convert Unicode to float
                    update_timestamp = float(control_child.text)

        elif root_element.tag == 'VLauncher':
            # Default values
            VLauncher = {'id' : u'', 'name' : u'', 'rom_count' : u'', 'roms_base_noext' : u''}
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
    roms_json_file = os.path.join(roms_dir, roms_base_noext + '.json')
    log_verb('fs_write_VCategory_ROMs_JSON() Saving JSON file {0}'.format(roms_json_file))
    try:
        with io.open(roms_json_file, 'w', encoding = 'utf-8') as file:
            json_unicode = json.dumps(roms, ensure_ascii = False, sort_keys = True, 
                                      indent = JSON_indent, separators = JSON_separators)
            file.write(json_unicode.encode('utf-8'))
            file.close()
    except OSError:
        kodi_notify_warn(u'(OSError) Cannot write {0} file'.format(roms_json_file))
    except IOError:
        kodi_notify_warn(u'(IOError) Cannot write {0} file'.format(roms_json_file))

#
# Loads an JSON file containing the Virtual Launcher ROMs
#
def fs_load_VCategory_ROMs_JSON(roms_dir, roms_base_noext):
    roms = {}

    # --- If file does not exist return empty dictionary ---
    roms_json_file = os.path.join(roms_dir, roms_base_noext + '.json')
    if not os.path.isfile(roms_json_file): return roms

    # --- Parse using cElementTree ---
    log_verb('fs_load_VCategory_ROMs_JSON() Loading JSON file {0}'.format(roms_json_file))
    with open(roms_json_file) as file:    
        try:
            roms = json.load(file)
        except ValueError:
            statinfo = os.stat(roms_json_file)
            log_error('fs_load_VCategory_ROMs_JSON() ValueError exception in json.load() function')
            log_error('fs_load_VCategory_ROMs_JSON() Dir  {0}'.format(roms_dir))
            log_error('fs_load_VCategory_ROMs_JSON() File {0}'.format(roms_base_noext + '.json'))
            log_error('fs_load_VCategory_ROMs_JSON() Size {0}'.format(statinfo.st_size))
        file.close()

    return roms

# -------------------------------------------------------------------------------------------------
# No-Intro and Offline scrapers
# -------------------------------------------------------------------------------------------------
#
# Loads a No-Intro Parent-Clone XML DAT file
#
def fs_load_NoIntro_XML_file(roms_xml_file):
    # --- If file does not exist return empty dictionary ---
    if not os.path.isfile(roms_xml_file): return {}

    # --- Parse using cElementTree ---
    log_verb('fs_load_NoIntro_XML_file() Loading XML file {0}'.format(roms_xml_file))
    nointro_roms = {}
    try:
        xml_tree = ET.parse(roms_xml_file)
    except ET.ParseError, e:
        log_error('(ParseError) Exception parsing XML categories.xml')
        log_error('(ParseError) {0}'.format(str(e)))
        return roms
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
# Legacy AL launchers.xml parser
#
# Some users have made their own tools to generate launchers.xml. Ensure that all fields in official
# AL source are inisialised with correct default value.
# Look in resources/lib/launcher_plugin.py -> Main::_load_launchers()
# -------------------------------------------------------------------------------------------------
def fs_load_legacy_AL_launchers(AL_launchers_filepath, categories, launchers):
    __debug_xml_parser = True

    # --- Parse using ElementTree ---
    log_verb('fs_load_legacy_AL_launchers() Loading "{0}"'.format(AL_launchers_filepath))
    try:
        xml_tree = ET.parse(AL_launchers_filepath)
    except ET.ParseError, e:
        log_error('(ParseError) Exception parsing XML categories.xml')
        log_error('(ParseError) {0}'.format(str(e)))
        return roms
    xml_root = xml_tree.getroot()

    for root_element in xml_root:
        log_debug('=== Root child tag "{0}" ==='.format(root_element.tag))
        if root_element.tag == 'categories':
            for category_element in root_element:
                log_debug('New Category')
                # >> Initialise correct default values
                category = {'id'       : u'', 
                            'name'     : u'', 
                            'thumb'    : u'', 
                            'fanart'   : u'', 
                            'genre'    : u'', 
                            'plot'     : u'', 
                            'finished' : u'false' }
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
                launcher = {'id'          : u'', 
                            'name'        : u'', 
                            'category'    : u'', 
                            'application' : u'', 
                            'args'        : u'', 
                            'rompath'     : u'', 
                            'thumbpath'   : u'',
                            'fanartpath'  : u'',
                            'trailerpath' : u'',
                            'custompath'  : u'',
                            'romext'      : u'',
                            'gamesys'     : u'',
                            'thumb'       : u'', 
                            'fanart'      : u'',
                            'genre'       : u'',
                            'release'     : u'',
                            'studio'      : u'',
                            'plot'        : u'',
                            'finished'    : u'false',
                            'minimize'    : u'false',
                            'lnk'         : u'false',
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
                            rom = {'id'       : u'', 
                                   'name'     : u'',
                                   'filename' : u'',
                                   'thumb'    : u'',
                                   'fanart'   : u'',
                                   'trailer'  : u'',
                                   'custom'   : u'',
                                   'genre'    : u'',
                                   'release'  : u'',
                                   'studio'   : u'',
                                   'plot'     : u'',
                                   'finished' : u'false',
                                   'altapp'   : u'',
                                   'altarg'   : u'' }
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
            kodi_notify_warn(u'Error writing {0}'.format(nfo_file_path))
        log_error(u"fs_export_ROM_NFO() Exception writing '{0}'".format(nfo_file_path))
        return
    if verbose:
        kodi_notify(u'Created NFO file {0}'.format(nfo_file_path))

    return

#
# Reads an NFO file with ROM information.
# Modifies roms dictionary even outside this function. See comments in fs_import_launcher_NFO()
# See comments in fs_export_ROM_NFO() about verbosity.
# About reading files in Unicode http://stackoverflow.com/questions/147741/character-reading-from-file-in-python
#
def fs_import_ROM_NFO(roms, romID, verbose = True):
    F = misc_split_path(roms[romID]['filename'])
    nfo_file_path = F.path_noext + u'.nfo'
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
            kodi_notify(u'Imported {0}'.format(nfo_file_path))
    else:
        if verbose:
            kodi_notify_warn(u'NFO file not found {0}'.format(nfo_file_path))
        log_debug(u"fs_import_ROM_NFO() NFO file not found '{0}'".format(nfo_file_path))
        return False

    return True

#
# This file is called by the ROM scanner to read a ROM info file automatically.
# NFO file existence is checked before calling this function, so NFO file must always exist.
#
def fs_load_NFO_file_scanner(nfo_file_path):
    nfo_dic = {'title' : '', 'year' : '', 'genre' : '', 'publisher' : '', 'rating' : '', 'plot' : '' }

    # >> Read file, put in a string and remove line endings
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
    log_debug(u'fs_export_launcher_NFO() Exporting launcher NFO "{0}"'.format(nfo_file_path))

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
        kodi_notify_warn(u'Exception writing NFO file {0}'.format(os.path.basename(nfo_file_path)))
        log_error(u"fs_export_launcher_NFO() Exception writing'{0}'".format(nfo_file_path))
        return False

    kodi_notify(u'Created NFO file {0}'.format(os.path.basename(nfo_file_path)))
    log_debug(u"fs_export_launcher_NFO() Created '{0}'".format(nfo_file_path))

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
    log_debug(u'fs_import_launcher_NFO() Importing launcher NFO "{0}"'.format(nfo_file_path))

    # --- Import data ---
    if os.path.isfile(nfo_file_path):
        # >> Read NFO file data
        try:
            file = codecs.open(nfo_file_path, 'r', 'utf-8')
            item_nfo = file.read().replace(u'\r', u'').replace(u'\n', u'')
            file.close()
        except:
            kodi_notify_warn(u'Exception reading NFO file {0}'.format(os.path.basename(nfo_file_path)))
            log_error(u"fs_import_launcher_NFO() Exception reading NFO file '{0}'".format(nfo_file_path))
            return False
        # log_debug(u"fs_import_launcher_NFO() item_nfo '{0}'".format(item_nfo))
    else:
        kodi_notify_warn(u'NFO file not found {0}'.format(os.path.basename(nfo_file_path)))
        log_info(u"fs_import_launcher_NFO() NFO file not found '{0}'".format(nfo_file_path))
        return False

    # Find data
    item_year      = re.findall('<year>(.*?)</year>',           item_nfo)
    item_genre     = re.findall('<genre>(.*?)</genre>',         item_nfo)
    item_publisher = re.findall('<publisher>(.*?)</publisher>', item_nfo)
    item_rating    = re.findall('<rating>(.*?)</rating>',       item_nfo)
    item_plot      = re.findall('<plot>(.*?)</plot>',           item_nfo)
    # log_debug(u"fs_import_launcher_NFO() item_year      '{0}'".format(item_year[0]))
    # log_debug(u"fs_import_launcher_NFO() item_publisher '{0}'".format(item_publisher[0]))
    # log_debug(u"fs_import_launcher_NFO() item_genre     '{0}'".format(item_genre[0]))
    # log_debug(u"fs_import_launcher_NFO() item_plot      '{0}'".format(item_plot[0]))

    # >> Careful about object mutability! This should modify the dictionary
    # >> passed as argument outside this function.
    if item_year:      launchers[launcherID]['m_year']   = text_unescape_XML(item_year[0])
    if item_genre:     launchers[launcherID]['m_genre']  = text_unescape_XML(item_genre[0])
    if item_publisher: launchers[launcherID]['m_studio'] = text_unescape_XML(item_publisher[0])
    if item_rating:    launchers[launcherID]['m_rating'] = text_unescape_XML(item_rating[0])
    if item_plot:      launchers[launcherID]['m_plot']   = text_unescape_XML(item_plot[0])

    kodi_notify(u'Imported {0}'.format(os.path.basename(nfo_file_path)))
    log_verb(u"fs_import_launcher_NFO() Imported '{0}'".format(nfo_file_path))

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
        kodi_notify_warn(u'Exception writing NFO file {0}'.format(os.path.basename(nfo_file_path)))
        log_error(u"fs_export_category_NFO() Exception writing'{0}'".format(nfo_file_path))
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
        kodi_notify_warn(u'NFO file not found {0}'.format(os.path.basename(nfo_file_path)))
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
