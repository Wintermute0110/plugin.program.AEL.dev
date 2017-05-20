# -*- coding: utf-8 -*-
# Advanced Emulator Launcher filesystem I/O functions
#

# Copyright (c) 2016-2017 Wintermute0110 <wintermute0110@gmail.com>
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
import string
import base64

# --- XML stuff ---
# ~~~ cElementTree sometimes fails to parse XML in Kodi's Python interpreter... I don't know why
# import xml.etree.cElementTree as ET

# ~~~ Using ElementTree seems to solve the problem
import xml.etree.ElementTree as ET

# --- AEL packages ---
from utils import *
from utils_kodi import *
from assets import *

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
         'default_clearlogo' : 's_clearlogo',
         's_thumb' : '',
         's_fanart' : '',
         's_banner' : '',
         's_flyer' : '',
         's_clearlogo' : '',
         's_trailer' : ''
         }

    return c

NOINTRO_DMODE_ALL       = 'All ROMs'
NOINTRO_DMODE_HAVE      = 'Have ROMs'
NOINTRO_DMODE_HAVE_UNK  = 'Have or Unknown ROMs'
NOINTRO_DMODE_HAVE_MISS = 'Have or Missing ROMs'
NOINTRO_DMODE_MISS      = 'Missing ROMs'
NOINTRO_DMODE_MISS_UNK  = 'Missing or Unknown ROMs'
NOINTRO_DMODE_UNK       = 'Unknown ROMs'
NOINTRO_DMODE_LIST      = [NOINTRO_DMODE_ALL, NOINTRO_DMODE_HAVE, NOINTRO_DMODE_HAVE_UNK, 
                           NOINTRO_DMODE_HAVE_MISS, NOINTRO_DMODE_MISS, NOINTRO_DMODE_MISS_UNK,
                           NOINTRO_DMODE_UNK]
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
         'args_extra' : [],
         'rompath' : '',
         'romext' : '',
         'finished': False,
         'minimize' : False,
         'roms_base_noext' : '',
         'nointro_xml_file' : '',
         'nointro_display_mode' : NOINTRO_DMODE_ALL,
         'pclone_launcher' : False,
         'num_roms' : 0,
         'num_parents' : 0,
         'num_clones' : 0,
         'timestamp_launcher' : 0.0,
         'timestamp_report' : 0.0,
         'default_thumb' : 's_thumb',
         'default_fanart' : 's_fanart',
         'default_banner' : 's_banner',
         'default_poster' : 's_flyer',
         'default_clearlogo' : 's_clearlogo',
         'roms_default_thumb' : 's_boxfront',
         'roms_default_fanart' : 's_fanart',
         'roms_default_banner' : 's_banner',
         'roms_default_poster' : 's_flyer',
         'roms_default_clearlogo' : 's_clearlogo',
         's_thumb' : '',
         's_fanart' : '',
         's_banner' : '',
         's_flyer' : '',
         's_clearlogo' : '',
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
# finished        bool default False
# nointro_status  string ['Have', 'Miss', 'Added', 'Unknown', 'None'] default 'None'
NOINTRO_STATUS_HAVE    = 'Have'
NOINTRO_STATUS_MISS    = 'Miss'
NOINTRO_STATUS_UNKNOWN = 'Unknown'
NOINTRO_STATUS_NONE    = 'None'
NOINTRO_STATUS_LIST    = [NOINTRO_STATUS_HAVE, NOINTRO_STATUS_MISS, NOINTRO_STATUS_UNKNOWN, 
                          NOINTRO_STATUS_NONE]

PCLONE_STATUS_PARENT = 'Parent'
PCLONE_STATUS_CLONE  = 'Clone'
PCLONE_STATUS_NONE   = 'None'
PCLONE_STATUS_LIST   = [PCLONE_STATUS_PARENT, PCLONE_STATUS_CLONE, PCLONE_STATUS_NONE]

# m_esrb string ESRB_LIST default ESRB_PENDING
ESRB_PENDING     = 'RP (Rating Pending)'
ESRB_EARLY       = 'EC (Early Childhood)'
ESRB_EVERYONE    = 'E (Everyone)'
ESRB_EVERYONE_10 = 'E10+ (Everyone 10+)'
ESRB_TEEN        = 'T (Teen)'
ESRB_MATURE      = 'M (Mature)'
ESRB_ADULTS_ONLY = 'AO (Adults Only)'
ESRB_LIST        = [ESRB_PENDING, ESRB_EARLY, ESRB_EVERYONE, ESRB_EVERYONE_10, ESRB_TEEN,
                    ESRB_MATURE, ESRB_ADULTS_ONLY]

# m_nplayers default values
NP_1P     = '1P'
NP_2P_SIM = '2P sim'
NP_2P_ALT = '2P alt'
NP_3P_SIM = '3P sim'
NP_3P_ALT = '3P alt'
NP_4P_SIM = '4P sim'
NP_4P_ALT = '4P alt'
NP_6P_SIM = '6P sim'
NP_6P_ALT = '6P alt'
NP_8P_SIM = '8P sim'
NP_8P_ALT = '8P alt'
NPLAYERS_LIST = [NP_1P, NP_2P_SIM, NP_2P_ALT, NP_3P_SIM, NP_3P_ALT, NP_4P_SIM, NP_4P_ALT, 
                        NP_6P_SIM, NP_6P_ALT, NP_8P_SIM, NP_8P_ALT]
def fs_new_rom():
    r = {'id' : '',
         'm_name' : '',
         'm_year' : '',
         'm_genre' : '',
         'm_studio' : '',
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
         'default_clearlogo' : 's_clearlogo',
         's_thumb' : '',
         's_fanart' : '',
         's_banner' : '',
         's_flyer' : '',
         's_clearlogo' : '',
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
    favourite['args_extra']             = launcher['args_extra']
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
    dest_rom['args_extra']  = source_launcher['args_extra']
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
# This function is not needed. It is deprecated and will be removed soon.
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
            str_list.append(XML_text('s_clearlogo', category['s_clearlogo']))
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
            # >> To simulate a list with XML allow multiple XML tags.
            if 'args_extra' in launcher:
                for extra_arg in launcher['args_extra']: str_list.append(XML_text('args_extra', extra_arg))
            str_list.append(XML_text('rompath', launcher['rompath']))
            str_list.append(XML_text('romext', launcher['romext']))
            str_list.append(XML_text('finished', unicode(launcher['finished'])))
            str_list.append(XML_text('minimize', unicode(launcher['minimize'])))
            str_list.append(XML_text('roms_base_noext', launcher['roms_base_noext']))
            str_list.append(XML_text('nointro_xml_file', launcher['nointro_xml_file']))
            str_list.append(XML_text('nointro_display_mode', launcher['nointro_display_mode']))
            str_list.append(XML_text('pclone_launcher', unicode(launcher['pclone_launcher'])))
            str_list.append(XML_text('num_roms', unicode(launcher['num_roms'])))
            str_list.append(XML_text('num_parents', unicode(launcher['num_parents'])))
            str_list.append(XML_text('num_clones', unicode(launcher['num_clones'])))            
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
            str_list.append(XML_text('s_clearlogo', launcher['s_clearlogo']))
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
def fs_load_catfile(categories_file, categories, launchers):
    __debug_xml_parser = 0
    update_timestamp = 0.0

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
        return update_timestamp
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

                # Now transform data depending on tag name
                if xml_tag == 'finished':
                    category[xml_tag] = True if xml_text == 'True' else False
                else:
                    # Internal data is always stored as Unicode. ElementTree already outputs Unicode.
                    category[xml_tag] = xml_text
            # --- Add category to categories dictionary ---
            categories[category['id']] = category

        elif category_element.tag == 'launcher':
            # Default values
            launcher = fs_new_launcher()

            # Parse child tags of category
            for category_child in category_element:
                # >> By default read strings
                xml_text = category_child.text if category_child.text is not None else ''
                xml_text = text_unescape_XML(xml_text)
                xml_tag  = category_child.tag
                if __debug_xml_parser: log_debug('{0} --> {1}'.format(xml_tag, xml_text))

                # >> Transform list() datatype
                if xml_tag == 'args_extra':
                    launcher[xml_tag].append(xml_text)
                # >> Transform Bool datatype
                elif xml_tag == 'finished' or xml_tag == 'minimize' or xml_tag == 'pclone_launcher':
                    launcher[xml_tag] = True if xml_text == 'True' else False
                # >> Transform Int datatype
                elif xml_tag == 'num_roms' or xml_tag == 'num_parents' or xml_tag == 'num_clones':
                    launcher[xml_tag] = int(xml_text)
                # >> Transform Float datatype
                elif xml_tag == 'timestamp_launcher' or xml_tag == 'timestamp_report':
                    launcher[xml_tag] = float(xml_text)
                else:
                    launcher[xml_tag] = xml_text
            # --- Add launcher to categories dictionary ---
            launchers[launcher['id']] = launcher
    # log_verb('fs_load_catfile() Loaded {0} categories'.format(len(categories)))
    # log_verb('fs_load_catfile() Loaded {0} launchers'.format(len(launchers)))

    return update_timestamp

# -------------------------------------------------------------------------------------------------
# Generic JSON loader/writer
# -------------------------------------------------------------------------------------------------
# Look at the ROMs JSON code for reference/comments to these functions.
def fs_write_JSON_file(file_dir, file_base_noext, data):
    # >> Get file names
    json_file = file_dir.pjoin(file_base_noext + '.json')
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
    json_file = file_dir.pjoin(file_base_noext + '.json')
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
#
# Return ROMs database file name.
# NOTE that JSON ROM writer creates 2 files: one JSON with main DB and one small XML with associated
# launcher info. When removing launchers both the JSON and XML files must be removed.
#
def fs_get_ROMs_XML_file_path(roms_dir, roms_base_noext):
    roms_file_path = roms_dir.join(roms_base_noext + '.xml')

    return roms_file_path

def fs_get_ROMs_JSON_file_path(roms_dir, roms_base_noext):
    roms_file_path = roms_dir.join(roms_base_noext + '.json')

    return roms_file_path

def fs_unlink_ROMs_database(roms_dir, roms_base_noext):
    # >> Delete ROMs info XML file
    roms_xml_file = fs_get_ROMs_XML_file_path(roms_dir, roms_base_noext)
    if roms_xml_file.exists():
        log_info('Deleting ROMs XML  "{0}"'.format(roms_xml_file.getOriginalPath()))
        roms_xml_file.unlink()
    # >> Delete ROMs JSON file
    roms_json_file = fs_get_ROMs_JSON_file_path(roms_dir, roms_base_noext)
    if roms_json_file.exists():
        log_info('Deleting ROMs JSON "{0}"'.format(roms_json_file.getOriginalPath()))
        roms_json_file.unlink()

def fs_write_ROMs_JSON(roms_dir, roms_base_noext, roms, launcher):
    # >> Get file names
    roms_json_file = roms_dir.join(roms_base_noext + '.json')
    roms_xml_file  = roms_dir.join(roms_base_noext + '.xml')
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
    roms_json_file = roms_dir.join(roms_base_noext + '.json')
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
    log_verb('fs_write_Collection_ROMs_JSON() File {0}'.format(roms_json_file.getOriginalPath()))

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
# output_FileName          -> Unicode string
# collection               -> dictionary
# collection_rom_list      -> list of dictionaries
# collections_asset_dir_FN -> FileName object of self.settings['collections_asset_dir']
#
def fs_export_ROM_collection_assets(output_FileName, collection, collection_rom_list, collections_asset_dir_FN):
    log_info('fs_export_ROM_collection_assets() File {0}'.format(output_FileName.getOriginalPath()))

    control_dic = {
        'control' : 'Advanced Emulator Launcher Collection ROM assets',
        'version' : AEL_STORAGE_FORMAT
    }

    # --- Export Collection assets ---
    assets_dic = {}
    log_debug('fs_export_ROM_collection_assets() Exporting Collecion assets')
    for asset_kind in [ASSET_THUMB, ASSET_FANART, ASSET_BANNER, ASSET_FLYER, ASSET_TRAILER]:
        AInfo    = assets_get_info_scheme(asset_kind)
        asset_FN = FileName(collection[AInfo.key])
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
            statinfo = os.stat(asset_FN.getPath())
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
            asset_FN = FileName(rom_item[AInfo.key])
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
            statinfo = os.stat(asset_FN.getPath())
            file_size = statinfo.st_size
            a_dic = {'basename' : asset_FN.getBase(), 'filesize' : file_size, 'data' : fileData_base64}
            assets_dic[asset_FN.getBase_noext()] = a_dic
            log_error('{0:<9s} exported/encoded'.format(AInfo.name))

    raw_data = []
    raw_data.append(control_dic)
    raw_data.append(assets_dic)

    # >> Produce nicely formatted JSON when exporting
    try:
        with io.open(output_FileName.getPath(), 'w', encoding = 'utf-8') as file:
            json_data = json.dumps(raw_data, ensure_ascii = False, sort_keys = True,
                                   indent = 2, separators = (', ', ' : '))
            file.write(unicode(json_data))
            file.close()
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
    log_info('fs_import_ROM_collection() Loading {0}'.format(input_FileName.getOriginalPath()))
    if not input_FileName.exists(): return default_return

    with open(input_FileName.getPath()) as file:
        try:
            raw_data = json.load(file)
        except ValueError:
            statinfo = os.stat(input_FileName.getPath())
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
    log_info('fs_import_ROM_collection_assets() Loading {0}'.format(input_FileName.getOriginalPath()))

    with open(input_FileName.getPath()) as file:
        try:
            raw_data = json.load(file)
        except ValueError:
            statinfo = os.stat(input_FileName.getPath())
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
    roms_json_file = roms_dir.join(roms_base_noext + '.json')
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
    roms_json_file = roms_dir.join(roms_base_noext + '.json')
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

# id of the fake ROM parent of all Unknown ROMs
UNKNOWN_ROMS_PARENT_ID = 'Unknown_ROMs_Parent'

#
# Creates and returns Parent/Clone MD5 index dictionary.
# This dictionary will be save in database roms_base_noext_PClone_index.json.
#
# roms_pclone_index = {
#   'parent_id_1'          : ['clone_id_1', 'clone_id_2', 'clone_id_3'],
#   'parent_id_2'          : ['clone_id_1', 'clone_id_2', 'clone_id_3'],
#    ... ,
#   UNKNOWN_ROMS_PARENT_ID : ['unknown_id_1', 'unknown_id_2', 'unknown_id_3']
# }
#
def fs_generate_PClone_index(roms, roms_nointro):
    roms_pclone_index_by_id = {}

    # --- Create a dictionary to convert ROMbase_noext names into IDs ---
    names_to_ids_dic = {}
    for rom_id in roms:
        rom = roms[rom_id]
        ROMFileName = FileName(rom['filename'])
        rom_name = ROMFileName.getBase_noext()
        # log_debug('{0} --> {1}'.format(rom_name, rom_id))
        # log_debug('{0}'.format(rom))
        names_to_ids_dic[rom_name] = rom_id

    # --- Build PClone dictionary using ROM base_noext names ---
    # >> Create fake ROM later because dictionaries cannot be modified when being iterated
    for rom_id in roms:
        rom = roms[rom_id]
        ROMFileName = FileName(rom['filename'])
        rom_nointro_name = ROMFileName.getBase_noext()
        # log_debug('rom_id {0}'.format(rom_id))
        # log_debug('  nointro_status   "{0}"'.format(rom['nointro_status']))
        # log_debug('  filename         "{0}"'.format(rom['filename']))
        # log_debug('  ROM_base_noext   "{0}"'.format(ROMFileName.getBase_noext()))
        # log_debug('  rom_nointro_name "{0}"'.format(rom_nointro_name))

        #  Add Unknown ROMs to their own set.
        if rom['nointro_status'] == NOINTRO_STATUS_UNKNOWN:
            clone_id = rom['id']
            if UNKNOWN_ROMS_PARENT_ID not in roms_pclone_index_by_id:
                roms_pclone_index_by_id[UNKNOWN_ROMS_PARENT_ID] = []
                roms_pclone_index_by_id[UNKNOWN_ROMS_PARENT_ID].append(clone_id)
            else:
                roms_pclone_index_by_id[UNKNOWN_ROMS_PARENT_ID].append(clone_id)
        else:
            nointro_rom = roms_nointro[rom_nointro_name]

            # >> ROM is a parent
            if nointro_rom['cloneof'] == '':
                parent_id = rom['id']
                if parent_id not in roms_pclone_index_by_id:
                    roms_pclone_index_by_id[parent_id] = []
            # >> ROM is a clone
            else:
                parent_name = nointro_rom['cloneof']
                parent_id   = names_to_ids_dic[parent_name]
                clone_id    = rom['id']
                if parent_id in roms_pclone_index_by_id:
                    roms_pclone_index_by_id[parent_id].append(clone_id)
                else:
                    roms_pclone_index_by_id[parent_id] = []
                    roms_pclone_index_by_id[parent_id].append(clone_id)

    return roms_pclone_index_by_id

#
# Returns a dictionary with parent ROMs to be stored in database roms_base_noext_parents.json
# If Unkown ROMs detected, the fake ROM [Unknown ROMs] is added.
#
def fs_generate_parent_ROMs_dic(roms, roms_pclone_index):
    p_roms = {}

    # --- Build parent ROM dictionary ---
    for rom_id in roms_pclone_index:
        # >> roms_pclone_index make contain the fake ROM id. Skip it if so because the fake
        # >> ROM is not in roms dictionary (KeyError exception)
        if rom_id == UNKNOWN_ROMS_PARENT_ID:
            rom = fs_new_rom()
            rom['id']                      = UNKNOWN_ROMS_PARENT_ID
            rom['m_name']                  = '[Unknown ROMs]'
            rom['m_plot']                  = 'Special virtual ROM parent of all Unknown ROMs'
            rom['nointro_status']          = NOINTRO_STATUS_NONE
            p_roms[UNKNOWN_ROMS_PARENT_ID] = rom
        else:
            # >> Make a copy of the dictionary or the original dictionary in ROMs will be modified!
            # >> Clean parent ROM name tags from ROM Name
            p_roms[rom_id] = dict(roms[rom_id])

    return p_roms

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
        return games
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
    # >> Skip No-Intro Added ROMs. rom['filename'] will be empty.
    if not rom['filename']: return
    ROMFileName = FileName(rom['filename'])
    nfo_file_path = ROMFileName.getPath_noext() + '.nfo'
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
    ROMFileName = FileName(roms[romID]['filename'])
    nfo_file_path = ROMFileName.getPath_noext() + '.nfo'
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
def fs_import_NFO_file_scanner(nfo_file_path):
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
def fs_export_launcher_NFO(nfo_FileName, launcher):
    # --- Get NFO file name ---
    log_debug('fs_export_launcher_NFO() Exporting launcher NFO "{0}"'.format(nfo_FileName.getPath()))

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
        f = open(nfo_FileName.getPath(), 'w')
        f.write(full_string)
        f.close()
    except:
        kodi_notify_warn('Exception writing NFO file {0}'.format(os.path.basename(nfo_FileName.getPath())))
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
#
def fs_import_launcher_NFO(nfo_FileName, launchers, launcherID):
    # --- Get NFO file name ---
    log_debug('fs_import_launcher_NFO() Importing launcher NFO "{0}"'.format(nfo_FileName.getPath()))

    # --- Import data ---
    if os.path.isfile(nfo_FileName.getPath()):
        # >> Read NFO file data
        try:
            file = codecs.open(nfo_FileName.getPath(), 'r', 'utf-8')
            item_nfo = file.read().replace('\r', '').replace('\n', '')
            file.close()
        except:
            kodi_notify_warn('Exception reading NFO file {0}'.format(os.path.basename(nfo_FileName.getPath())))
            log_error("fs_import_launcher_NFO() Exception reading NFO file '{0}'".format(nfo_FileName.getPath()))
            return False
        # log_debug("fs_import_launcher_NFO() item_nfo '{0}'".format(item_nfo))
    else:
        kodi_notify_warn('NFO file not found {0}'.format(os.path.basename(nfo_FileName.getPath())))
        log_info("fs_import_launcher_NFO() NFO file not found '{0}'".format(nfo_FileName.getPath()))
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

    log_verb("fs_import_launcher_NFO() Imported '{0}'".format(nfo_FileName.getPath()))

    return True

#
# Returns a FileName object
#
def fs_get_launcher_NFO_name(settings, launcher):
    launcher_name = launcher['m_name']
    nfo_dir = settings['launchers_asset_dir']
    nfo_file_path = FileName(os.path.join(nfo_dir, launcher_name + '.nfo'))
    log_debug("fs_get_launcher_NFO_name() nfo_file_path = '{0}'".format(nfo_file_path.getOriginalPath()))

    return nfo_file_path

#
# Look at the launcher NFO files for a reference implementation.
# Categories NFO files only have genre and plot.
#
def fs_export_category_NFO(nfo_FileName, category):
    # --- Get NFO file name ---
    log_debug('fs_export_category_NFO() Exporting launcher NFO "{0}"'.format(nfo_FileName.getPath()))

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
        f = open(nfo_FileName.getPath(), 'w')
        f.write(full_string)
        f.close()
    except:
        kodi_notify_warn('Exception writing NFO file {0}'.format(os.path.basename(nfo_FileName.getPath())))
        log_error("fs_export_category_NFO() Exception writing'{0}'".format(nfo_FileName.getPath()))
        return False
    log_debug("fs_export_category_NFO() Created '{0}'".format(nfo_FileName.getPath()))

    return True

def fs_import_category_NFO(nfo_FileName, categories, categoryID):
    # --- Get NFO file name ---
    log_debug('fs_import_category_NFO() Importing launcher NFO "{0}"'.format(nfo_FileName.getPath()))

    # --- Import data ---
    if nfo_FileName.isfile():
        try:
            file = codecs.open(nfo_FileName.getPath(), 'r', 'utf-8')
            item_nfo = file.read().replace('\r', '').replace('\n', '')
            file.close()
        except:
            kodi_notify_warn('Exception reading NFO file {0}'.format(os.path.basename(nfo_FileName.getPath())))
            log_error("fs_import_category_NFO() Exception reading NFO file '{0}'".format(nfo_FileName.getPath()))
            return False
    else:
        kodi_notify_warn('NFO file not found {0}'.format(os.path.basename(nfo_FileName.getPath())))
        log_error("fs_import_category_NFO() NFO file not found '{0}'".format(nfo_FileName.getPath()))
        return False

    item_genre  = re.findall('<genre>(.*?)</genre>', item_nfo)
    item_rating = re.findall('<rating>(.*?)</rating>', item_nfo)
    item_plot   = re.findall('<plot>(.*?)</plot>',   item_nfo)

    if item_genre:  categories[categoryID]['m_genre']  = text_unescape_XML(item_genre[0])
    if item_rating: categories[categoryID]['m_rating'] = text_unescape_XML(item_rating[0])
    if item_plot:   categories[categoryID]['m_plot']   = text_unescape_XML(item_plot[0])

    log_verb("fs_import_category_NFO() Imported '{0}'".format(nfo_FileName.getPath()))

    return True

#
# Returns a FileName object
#
def fs_get_category_NFO_name(settings, category):
    category_name = category['m_name']
    nfo_dir = settings['categories_asset_dir']
    nfo_file_path = FileName(os.path.join(nfo_dir, category_name + '.nfo'))
    log_debug("fs_get_category_NFO_name() nfo_file_path = '{0}'".format(nfo_file_path.getOriginalPath()))

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
    nfo_content.append('<collection>\n')
    nfo_content.append(XML_text('genre',  collection['m_genre']))
    nfo_content.append(XML_text('rating', collection['m_rating']))
    nfo_content.append(XML_text('plot',   collection['m_plot']))
    nfo_content.append('</collection>\n')
    full_string = ''.join(nfo_content).encode('utf-8')
    try:
        f = open(nfo_FileName.getPath(), 'w')
        f.write(full_string)
        f.close()
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
    if nfo_FileName.isfile():
        try:
            file = codecs.open(nfo_FileName.getPath(), 'r', 'utf-8')
            item_nfo = file.read().replace('\r', '').replace('\n', '')
            file.close()
        except:
            kodi_notify_warn('Exception reading NFO file {0}'.format(nfo_FileName.getName()))
            log_error("fs_import_collection_NFO() Exception reading NFO file '{0}'".format(nfo_FileName.getPath()))
            return False
    else:
        kodi_notify_warn('NFO file not found {0}'.format(os.path.basename(nfo_FileName.getOriginalPath())))
        log_error("fs_import_collection_NFO() NFO file not found '{0}'".format(nfo_FileName.getPath()))
        return False

    item_genre  = re.findall('<genre>(.*?)</genre>', item_nfo)
    item_rating = re.findall('<rating>(.*?)</rating>', item_nfo)
    item_plot   = re.findall('<plot>(.*?)</plot>',   item_nfo)

    if item_genre:  collections[launcherID]['m_genre']  = text_unescape_XML(item_genre[0])
    if item_rating: collections[launcherID]['m_rating'] = text_unescape_XML(item_rating[0])
    if item_plot:   collections[launcherID]['m_plot']   = text_unescape_XML(item_plot[0])

    log_verb("fs_import_collection_NFO() Imported '{0}'".format(nfo_FileName.getOriginalPath()))

    return True

def fs_get_collection_NFO_name(settings, collection):
    collection_name = collection['m_name']
    nfo_dir = settings['collections_asset_dir']
    nfo_file_path = FileName(os.path.join(nfo_dir, collection_name + '.nfo'))
    log_debug("fs_get_collection_NFO_name() nfo_file_path = '{0}'".format(nfo_file_path.getOriginalPath()))

    return nfo_file_path
