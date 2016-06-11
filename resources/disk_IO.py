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
import json
import io
import codecs, time

# --- AEL packages ---
from utils import *
try:
    from utils_kodi import *
except:
    from utils_kodi_standalone import *

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
    c = {'id'     : u'', 'name'  : u'', 'thumb'       : u'', 
         'fanart' : u'', 'genre' : u'', 'description' : u'', 
         'finished' : False}

    return c

def fs_new_launcher():
    l = {'id' : u'',              'name' : u'',       'categoryID' : u'',  'platform' : u'',
         'application' : u'',     'args' : u'',       'rompath' : u'',     'romext' : u'',
         'thumbpath' : u'',       'fanartpath' : u'', 'trailerpath' : u'', 'custompath' : u'',
         'thumb' : u'',           'fanart' : u'',     'genre' : u'',       'year' : u'', 
         'studio' : u'',          'plot' : u'',
         'finished': False,       'minimize' : False,
         'roms_base_noext' : u'', 'nointro_xml_file' : u'', u'report_timestamp' : 0.0 }

    return l

# Mandatory variables in XML:
# id              string MD5 hash
# name            string ROM name
# finished        bool ['True', 'False'] default 'False'
# nointro_status  string ['Have', 'Miss', 'Unknown', 'None'] default 'None'
def fs_new_rom():
    r = {'id' : u'',         'name' : u'',   'filename' : u'',
         'thumb' : u'',      'fanart' : u'', 'trailer' : u'',  'custom' : u'',
         'genre' : u'',      'year' : u'',   'studio' : u'',   'plot' : u'',
         'altapp' : u'',     'altarg' : u'',
         'finished' : False, 'nointro_status' : 'None' }

    return r

#
# DO NOT USE THIS FUNCTION TO CREATE FAVOURITES. USE fs_new_favourite_rom() INSTEAD.
#
# fav_status = ['OK', 'Unlinked ROM', 'Unlinked Launcher', 'Broken'] default 'OK'
# 'OK'                ROM filename exists and launcher exists and ROM id exists
# 'Unlinked ROM'      ROM filename exists but ROM ID in launcher does not
# 'Unlinked Launcher' ROM filename exists but Launcher ID not found
#                     Note that if the launcher does not exists implies ROM ID does not exist. If launcher
#                     doesn't exist ROM JSON cannot be loaded.
# 'Broken'            ROM filename does not exist. ROM is unplayable
def fs_new_favourite_rom():
    r = {'id' : u'',          'name' : u'',   'filename' : u'',
         'thumb' : u'',       'fanart' : u'', 'trailer' : u'', 'custom' : u'',
         'genre' : u'',       'year' : u'',   'studio' : u'',  'plot' : u'',
         'altapp' : u'',      'altarg' : u'',
         'finished' : False,  'nointro_status' : 'None',
         'launcherID' : u'',  'platform' : u'',
         'application' : u'', 'args' : u'', 'rompath' : '', 'romext' : '',
         'minimize' : False,  'fav_status' : u'OK' }

    return r

#
# Note that Virtual Launchers ROMs use the Favourite ROMs data model.
# Missing ROMs are not allowed in Favourites or Virtual Launchers.
#
def fs_get_Favourite_from_ROM(rom, launcher):
    # >> Copy dictionary object
    favourite = dict(rom)

    # Delete nointro_status field from ROM. Make sure this is done in the copy to be
    # returned to avoid chaning the function parameters (dictionaries are mutable!)
    # See http://stackoverflow.com/questions/5844672/delete-an-element-from-a-dictionary
    # NOTE keep it!
    # del favourite['nointro_status']
    
    # >> Copy launcher stuff
    favourite['launcherID']  = launcher['id']
    favourite['platform']    = launcher['platform']
    favourite['application'] = launcher['application']
    favourite['args']        = launcher['args']
    favourite['rompath']     = launcher['rompath']
    favourite['romext']      = launcher['romext']
    favourite['minimize']    = launcher['minimize']
    favourite['fav_status']  = u'OK'

    return favourite

def fs_get_ROMs_basename(category_name, launcher_name, launcherID):
    clean_cat_name = ''.join([i if i in string.printable else '_' for i in category_name])
    clean_launch_title = ''.join([i if i in string.printable else '_' for i in launcher_name])
    clean_launch_title = clean_launch_title.replace(' ', '_')
    roms_base_noext = 'roms_' + clean_cat_name + '_' + clean_launch_title + '_' + launcherID[0:6]
    log_info('fs_get_ROMs_basename() roms_base_noext "{0}"'.format(roms_base_noext))

    return roms_base_noext

# -------------------------------------------------------------------------------------------------
# Filesystem very low-level utilities
# -------------------------------------------------------------------------------------------------
#
# Writes a XML text tag line, indented 2 spaces (root sub-child)
# Both tag_name and tag_text must be Unicode strings. Data will be encoded to UFT-8.
# Returns an UTF-8 encoded string.
#
def XML_text(tag_name, tag_text):
    tag_text = text_escape_XML(tag_text)
    try:
        line = '  <{0}>{1}</{2}>\n'.format(tag_name.encode('utf-8'), tag_text.encode('utf-8'), tag_name.encode('utf-8'))
    except UnicodeEncodeError:
        log_error('XML_text() Exception UnicodeEncodeError tag_text "{0}"'.format(tag_text.encode('utf-8', 'replace')))
        line = '  <{0}>{1}</{2}>\n'.format(tag_name.encode('utf-8'), tag_text.encode('utf-8', 'replace'), tag_name.encode('utf-8'))

    return line

#
# See https://docs.python.org/2/library/sys.html#sys.getfilesystemencoding
#
def get_fs_encoding():
    try:
        return sys.getfilesystemencoding()
    except UnicodeEncodeError, UnicodeDecodeError:
        return 'utf-8'

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
        str_list.append('<advanced_emulator_launcher version="1.0">\n')

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
        for categoryID in sorted(categories, key = lambda x : categories[x]['name']):
            category = categories[categoryID]
            # Data which is not string must be converted to string
            # XML text returns UFT-8 encoded strings. Dictionary strings are in Unicode!
            str_list.append('<category>\n')
            str_list.append(XML_text('id', categoryID))
            str_list.append(XML_text('name', category['name']))
            str_list.append(XML_text('thumb', category['thumb']))
            str_list.append(XML_text('fanart', category['fanart']))
            str_list.append(XML_text('genre', category['genre']))
            str_list.append(XML_text('description', category['description']))
            str_list.append(XML_text('finished', unicode(category['finished'])))
            str_list.append('</category>\n')

        # --- Write launchers ---
        for launcherID in sorted(launchers, key = lambda x : launchers[x]['name']):
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
            str_list.append(XML_text('finished', unicode(launcher['finished'])))
            str_list.append(XML_text('minimize', unicode(launcher['minimize'])))
            str_list.append(XML_text('roms_base_noext', launcher['roms_base_noext']))
            str_list.append(XML_text('nointro_xml_file', launcher['nointro_xml_file']))
            str_list.append(XML_text('report_timestamp', unicode(launcher['report_timestamp'])))
            str_list.append('</launcher>\n')
        # End of file
        str_list.append('</advanced_emulator_launcher>\n')

        # Strings in the list are encoded in UTF-8, ready to be written on disk.
        # Join string, and save categories.xml file
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
    update_timestamp = 0.0
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
                elif xml_tag == 'report_timestamp':
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
# Write to disk launcher ROMs XML database.
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
        str_list.append(XML_text('id', launcher['id']))
        str_list.append(XML_text('name', launcher['name']))
        str_list.append(XML_text('categoryID', launcher['categoryID']))
        str_list.append(XML_text('platform', launcher['platform']))
        str_list.append(XML_text('rompath', launcher['rompath']))
        str_list.append(XML_text('thumbpath', launcher['thumbpath']))
        str_list.append(XML_text('fanartpath', launcher['fanartpath']))
        str_list.append('</launcher>\n')

        # --- Create list of ROMs ---
        # Size optimization: only write in the XML fields which are not ''. This
        # will save A LOT of disk space and reduce loading times (at a cost of
        # some writing time, but writing is much less frequent than reading).
        for romID in sorted(roms, key = lambda x : roms[x]['name']):
            # Data which is not string must be converted to string
            rom = roms[romID]
            str_list.append('<rom>\n')
            str_list.append(XML_text('id', romID))
            str_list.append(XML_text('name', rom['name']))
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
            str_list.append(XML_text('finished', unicode(rom['finished'])))
            str_list.append(XML_text('nointro_status', rom['nointro_status']))
            str_list.append('</rom>\n')
        # End of file
        str_list.append('</advanced_emulator_launcher_ROMs>\n')

        # --- Join string and save categories.xml file ---
        full_string = ''.join(str_list)
        file_obj = open(roms_xml_file, 'wt' )
        file_obj.write(full_string)
        file_obj.close()
    except OSError:
        log_kodi_notify_warn('Advanced Emulator Launcher - Error', 'Cannot write {0} file (OSError)'.format(roms_xml_file))
        log_error('fs_write_ROMs_XML() (OSerror) Cannot write file "{0}"'.format(roms_xml_file))
    except IOError:
        log_kodi_notify_warn('Advanced Emulator Launcher - Error', 'Cannot write {0} file (IOError)'.format(roms_xml_file))
        log_error('fs_write_ROMs_XML() (IOError) Cannot write file "{0}"'.format(roms_xml_file))

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
    if not os.path.isfile(roms_xml_file):
        return {}

    # --- Notify we are busy doing things ---
    kodi_busydialog_ON()

    # --- Parse using cElementTree ---
    log_verb('fs_load_ROMs_XML() Loading XML file {0}'.format(roms_xml_file))
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
        str_list.append('</advanced_emulator_launcher_ROMs>\n')

        full_string = ''.join(str_list)
        file_obj = open(roms_xml_file, 'wt' )
        file_obj.write(full_string)
        file_obj.close()
    except OSError:
        log_kodi_notify_warn('Advanced Emulator Launcher - Error', 'Cannot write {0} file (OSError)'.format(roms_xml_file))
        log_error('fs_write_ROMs_JSON() (OSerror) Cannot write file "{0}"'.format(roms_xml_file))
    except IOError:
        log_kodi_notify_warn('Advanced Emulator Launcher - Error', 'Cannot write {0} file (IOError)'.format(roms_xml_file))
        log_error('fs_write_ROMs_JSON() (IOError) Cannot write file "{0}"'.format(roms_xml_file))

    # >> Write ROMs JSON dictionary.
    try:
        with io.open(roms_json_file, 'wt', encoding='utf-8') as file:
          file.write(unicode(json.dumps(roms, ensure_ascii = False, sort_keys = True, indent = 2, separators = (',', ': '))))
    except OSError:
        gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write {0} file (OSError)'.format(roms_json_file))
    except IOError:
        gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write {0} file (IOError)'.format(roms_json_file))

#
# Loads an JSON file containing the Virtual Launcher ROMs
#
def fs_load_ROMs_JSON(roms_dir, roms_base_noext):
    roms = {}

    # --- If file does not exist return empty dictionary ---
    roms_json_file = os.path.join(roms_dir, roms_base_noext + '.json')
    if not os.path.isfile(roms_json_file):
        return {}

    # --- Parse using json module ---
    log_verb('fs_load_ROMs_JSON() Loading JSON file {0}'.format(roms_json_file))
    with open(roms_json_file) as file:    
        roms = json.load(file)

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
        str_list.append('<advanced_emulator_launcher_Favourites version="1.0">\n')
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
def fs_load_Favourites_XML(roms_xml_file):
    __debug_xml_parser = 0
    roms = {}

    # --- If file does not exist return empty dictionary ---
    if not os.path.isfile(roms_xml_file):
        return {}

    # --- Parse using cElementTree ---
    log_verb('fs_load_Favourites_XML() Loading XML file {0}'.format(roms_xml_file))
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
        with io.open(roms_json_file, 'wt', encoding='utf-8') as file:
          file.write(unicode(json.dumps(roms, ensure_ascii = False, sort_keys = True, indent = 2, separators = (',', ': '))))
    except OSError:
        gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write {0} file (OSError)'.format(roms_json_file))
    except IOError:
        gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write {0} file (IOError)'.format(roms_json_file))

#
# Loads an JSON file containing the Favourite ROMs
#
def fs_load_Favourites_JSON(roms_json_file):
    roms = {}

    # --- If file does not exist return empty dictionary ---
    if not os.path.isfile(roms_json_file):
        return {}

    # --- Parse using cElementTree ---
    log_verb('fs_load_Favourites_JSON() Loading JSON file {0}'.format(roms_json_file))
    with open(roms_json_file) as file:    
        roms = json.load(file)

    return roms

# -------------------------------------------------------------------------------------------------
# Virtual Categories
# -------------------------------------------------------------------------------------------------
def fs_write_VCategory_XML(roms_xml_file, roms):
    log_info('fs_write_VCategory_XML() Saving XML file {0}'.format(roms_xml_file))
    try:
        str_list = []
        str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        str_list.append('<advanced_emulator_launcher_Virtual_Category version="1.0">\n')

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
        str_list.append('</advanced_emulator_launcher_Virtual_Category>\n')
        full_string = ''.join(str_list)
        file_obj = open(roms_xml_file, 'wt' )
        file_obj.write(full_string)
        file_obj.close()
    except OSError:
        gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write {0} file (OSError)'.format(roms_xml_file))
    except IOError:
        gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write {0} file (IOError)'.format(roms_xml_file))

#
# Loads an XML file containing Virtual Launcher indices
# It is basically the same as ROMs, but with some more fields to store launching application data.
#
def fs_load_VCategory_XML(roms_xml_file):
    __debug_xml_parser = 0
    update_timestamp = 0.0
    VLaunchers = {}

    # --- If file does not exist return empty dictionary ---
    if not os.path.isfile(roms_xml_file):
        return {}

    # --- Parse using cElementTree ---
    log_verb('fs_load_VCategory_XML() Loading XML file {0}'.format(roms_xml_file))
    xml_tree = ET.parse(roms_xml_file)
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
    log_info('fs_write_VCategory_ROMs_JSON() Saving JSON file {0}'.format(roms_json_file))
    try:
        with io.open(roms_json_file, 'wt', encoding='utf-8') as file:
          file.write(unicode(json.dumps(roms, ensure_ascii = False, sort_keys = True, indent = 2, separators = (',', ': '))))
    except OSError:
        gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write {0} file (OSError)'.format(roms_json_file))
    except IOError:
        gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write {0} file (IOError)'.format(roms_json_file))

#
# Loads an JSON file containing the Virtual Launcher ROMs
#
def fs_load_VCategory_ROMs_JSON(roms_dir, roms_base_noext):
    roms = {}

    # --- If file does not exist return empty dictionary ---
    roms_json_file = os.path.join(roms_dir, roms_base_noext + '.json')
    if not os.path.isfile(roms_json_file):
        return {}

    # --- Parse using cElementTree ---
    log_verb('fs_load_VCategory_ROMs_JSON() Loading JSON file {0}'.format(roms_json_file))
    with open(roms_json_file) as file:    
        roms = json.load(file)

    return roms

# -------------------------------------------------------------------------------------------------
# No-Intro and Offline scrapers
# -------------------------------------------------------------------------------------------------
#
# Loads a No-Intro Parent-Clone XML DAT file
#
def fs_load_NoIntro_XML_file(roms_xml_file):
    # --- If file does not exist return empty dictionary ---
    if not os.path.isfile(roms_xml_file):
        return {}

    # --- Parse using cElementTree ---
    log_verb('fs_load_NoIntro_XML_file() Loading XML file {0}'.format(roms_xml_file))
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
        log_error("Cannot load file '{0}'".format(xml_file))
        return games

    # --- Parse using cElementTree ---
    log_verb('fs_load_GameInfo_XML() Loading "{0}"'.format(xml_file))
    xml_tree = ET.parse(xml_file)
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
    xml_tree = ET.parse(AL_launchers_filepath)
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
    nfo_content.append(XML_text('title',     rom['name']))
    nfo_content.append(XML_text('year',      rom['year']))
    nfo_content.append(XML_text('publisher', rom['studio']))
    nfo_content.append(XML_text('genre',     rom['genre']))
    nfo_content.append(XML_text('plot',      rom['plot']))
    nfo_content.append('</game>\n')
    full_string = ''.join(nfo_content)
    try:
        usock = open(nfo_file_path, 'wt')
        usock.write(full_string)
        usock.close()
    except:
        if verbose:
            kodi_notify_warn('Advanced Emulator Launcher',
                             'Error writing {0}'.format(nfo_file_path))
        log_error("fs_export_ROM_NFO() Exception writing '{0}'".format(nfo_file_path))
        return
    if verbose:
        kodi_notify('Advanced Emulator Launcher',
                    'Created NFO file {0}'.format(nfo_file_path))

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
        file = codecs.open(nfo_file_path, 'rt', 'utf-8')
        nfo_str = file.read().replace('\r', '').replace('\n', '')
        file.close()

        # Search for items
        item_title     = re.findall('<title>(.*?)</title>', nfo_str)
        item_year      = re.findall('<year>(.*?)</year>', nfo_str)
        item_publisher = re.findall('<publisher>(.*?)</publisher>', nfo_str)
        item_genre     = re.findall('<genre>(.*?)</genre>', nfo_str)
        item_plot      = re.findall('<plot>(.*?)</plot>', nfo_str)

        if len(item_title) > 0:     roms[romID]['title']     = text_unescape_XML(item_title[0])
        if len(item_year) > 0:      roms[romID]['year']      = text_unescape_XML(item_year[0])
        if len(item_publisher) > 0: roms[romID]['publisher'] = text_unescape_XML(item_publisher[0])
        if len(item_genre) > 0:     roms[romID]['genre']     = text_unescape_XML(item_genre[0])
        if len(item_plot) > 0:      roms[romID]['plot']      = text_unescape_XML(item_plot[0])

        if verbose:
            kodi_notify('Advanced Emulator Launcher',
                        'Imported {0}'.format(nfo_file_path))
    else:
        if verbose:
            kodi_notify_warn('Advanced Emulator Launcher',
                             'NFO file not found {0}'.format(nfo_file_path))
        log_debug("fs_import_ROM_NFO() NFO file not found '{0}'".format(nfo_file_path))
        return False

    return True

#
# This file is called by the ROM scanner to read a ROM info file automatically.
# NFO file existence is checked before calling this function, so NFO file must always exist.
#
def fs_load_NFO_file_scanner(nfo_file_path):
    nfo_dic = {'title' : '', 'platform' : '', 'year' : '', 'publisher' : '',
               'genre' : '', 'plot' : '' }

    # >> Read file, put in a string and remove line endings
    file = codecs.open(nfo_file_path, 'rt', 'utf-8')
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
#
# ROM launchers:
#   Same as standalone launchers.
#
def fs_export_launcher_NFO(settings, launcher):
    # --- Get NFO file name ---
    log_debug('fs_export_launcher_NFO() Exporting launcher NFO file.')
    nfo_file_path = fs_get_launcher_NFO_name(settings, launcher)

    # If NFO file does not exist then create them. If it exists, overwrite.
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
    try:
        f = open(nfo_file_path, 'wt')
        f.write(full_string)
        f.close()
    except:
        kodi_notify_warn('Advanced Emulator Launcher',
                         'Exception writing NFO file {0}'.format(os.path.basename(nfo_file_path)))
        log_error("fs_export_launcher_NFO() Exception writing'{0}'".format(nfo_file_path))
        return False

    kodi_notify('Advanced Emulator Launcher',
                'Created NFO file {0}'.format(os.path.basename(nfo_file_path)))
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
def fs_import_launcher_NFO(settings, launchers, launcherID):
    # --- Get NFO file name ---
    log_debug('fs_import_launcher_NFO() Importing launcher NFO file.')
    nfo_file_path = fs_get_launcher_NFO_name(settings, launchers[launcherID])

    # --- Import data ---
    if os.path.isfile(nfo_file_path):
        # >> Read NFO file data
        file = codecs.open(nfo_file_path, 'rt', 'utf-8')
        item_nfo = file.read().replace('\r','').replace('\n','')
        file.close()

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

        kodi_notify('Advanced Emulator Launcher',
                    'Imported {0}'.format(nfo_file_path))
        log_debug("fs_import_launcher_NFO() Imported '{0}'".format(nfo_file_path))
    else:
        kodi_notify_warn('Advanced Emulator Launcher',
                         'NFO file not found {0}'.format(nfo_file_path))
        log_debug("fs_import_launcher_NFO() NFO file not found '{0}'".format(nfo_file_path))
        return False

    return True

def fs_get_launcher_NFO_name(settings, launcher):
    launcher_name = launcher['name']
    nfo_dir = settings['launchers_nfo_dir']
    nfo_file_path = os.path.join(nfo_dir, launcher_name + u'.nfo')
    log_debug("fs_get_launcher_NFO_name() nfo_file_path = '{0}'".format(nfo_file_path))

    return nfo_file_path
