# -*- coding: utf-8 -*-
# Advanced Emulator Launcher XML autoconfiguration stuff
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
import os

# --- AEL packages ---
from utils import *
from utils_kodi import *

# -------------------------------------------------------------------------------------------------
# Exports launchers to an XML file.
# Currently categories are not supported.
# -------------------------------------------------------------------------------------------------
def autoconfig_export_launchers(export_FN):
    # >> Traverse all launchers and add to the XML file.
    str_list = []
    str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
    str_list.append('<advanced_emulator_launcher_configuration>\n')
    for launcherID in sorted(self.launchers, key = lambda x : self.launchers[x]['m_name']):
        # >> Data which is not string must be converted to string
        launcher = self.launchers[launcherID]
        if launcher['categoryID'] in self.categories:
            category_name = self.categories[launcher['categoryID']]['m_name']
        elif launcher['categoryID'] == VCATEGORY_ADDONROOT_ID:
            category_name = VCATEGORY_ADDONROOT_ID
        else:
            kodi_dialog_OK('Launcher category not found. This is a bug, please report it.')
            return
        log_verb('_command_export_launchers() Launcher "{0}" (ID "{1}")'.format(launcher['m_name'], launcherID))

        # >> WORKAROUND Take titles path and remove trailing subdirectory.
        path_titles = launcher['path_title']
        log_verb('_command_export_launchers() path_titles "{0}"'.format(path_titles))
        (head, tail) = os.path.split(path_titles)
        log_verb('_command_export_launchers() head        "{0}"'.format(head))
        log_verb('_command_export_launchers() tail        "{0}"'.format(tail))
        path_assets = head
        log_verb('_command_export_launchers() path_assets "{0}"'.format(path_assets))

        # >> Export Launcher
        str_list.append('<launcher>\n')
        str_list.append(XML_text('name', launcher['m_name']))
        str_list.append(XML_text('category', category_name))
        str_list.append(XML_text('year', launcher['m_year']))
        str_list.append(XML_text('genre', launcher['m_genre']))
        str_list.append(XML_text('studio', launcher['m_studio']))
        str_list.append(XML_text('rating', launcher['m_rating']))
        str_list.append(XML_text('plot', launcher['m_plot']))
        str_list.append(XML_text('platform', launcher['platform']))
        str_list.append(XML_text('application', launcher['application']))
        str_list.append(XML_text('args', launcher['args']))
        if launcher['args_extra']:
            for extra_arg in launcher['args_extra']: str_list.append(XML_text('args_extra', extra_arg))
        else:
            str_list.append(XML_text('args_extra', ''))
        str_list.append(XML_text('rompath', launcher['rompath']))
        str_list.append(XML_text('romext', launcher['romext']))
        # >> Assets not supported yet. Can be changed with the graphical interface.
        # str_list.append(XML_text('thumb', launcher['s_thumb']))
        # str_list.append(XML_text('fanart', launcher['s_fanart']))
        # str_list.append(XML_text('banner', launcher['s_banner']))
        # str_list.append(XML_text('flyer', launcher['s_flyer']))
        # str_list.append(XML_text('clearlogo', launcher['s_clearlogo']))
        # str_list.append(XML_text('trailer', launcher['s_trailer']))
        # >> path_assets supported
        str_list.append(XML_text('path_assets', path_assets))
        str_list.append('</launcher>\n')
    str_list.append('</advanced_emulator_launcher_configuration>\n')

    # >> Export file
    # >> Strings in the list are Unicode. Encode to UTF-8. Join string, and save categories.xml file
    try:
        full_string = ''.join(str_list).encode('utf-8')
        file_obj = open(export_FN.getPath(), 'w')
        file_obj.write(full_string)
        file_obj.close()
    except OSError:
        log_error('(OSError) Cannot write categories.xml file')
        kodi_notify_warn('(OSError) Cannot write categories.xml file')
        return
    except IOError:
        log_error('(IOError) Cannot write categories.xml file')
        kodi_notify_warn('(IOError) Cannot write categories.xml file')
        return
    log_verb('_command_export_launchers() Exported OP "{0}"'.format(export_FN.getOriginalPath()))
    log_verb('_command_export_launchers() Exported  P "{0}"'.format(export_FN.getPath()))
    kodi_notify('Exported AEL Launchers configuration')

# -------------------------------------------------------------------------------------------------
# Import AEL launcher configuration
# -------------------------------------------------------------------------------------------------
def autoconfig_get_default_import_launcher(self):
    l = {'category' : 'root_category',
         'name' : '',
         'year' : '',
         'genre' : '',
         'studio' : '',
         'rating' : '',
         'plot' : '',
         'platform' : 'Unknown',
         'application' : '',
         'args' : '',
         'args_extra' : [],
         'rompath' : '',
         'romext' : '',
         'thumb' : '',
         'fanart' : '',
         'banner' : '',
         'flyer' : '',
         'clearlogo' : '',
         'trailer' : '',
         'path_assets' : '',
    }

    return l

def _misc_search_category_and_launcher_by_name(self, cat_name, laun_name):
    s_category = None
    if cat_name == VCATEGORY_ADDONROOT_ID:
        s_category = VCATEGORY_ADDONROOT_ID
    else:
        for categoryID in self.categories:
            category = self.categories[categoryID]
            if cat_name == category['m_name']:
                s_category = category['id']
                break

    # >> If the category was found then search the launcher inside that category.
    if s_category:
        s_launcher = None
        for launcherID, launcher in self.launchers.iteritems():
            if s_category != launcher['categoryID']: continue
            if laun_name == launcher['m_name']:
                s_launcher = launcher['id']
                break
    # >> If the category was not found then launcher does not exist.
    else:
        s_launcher = None

    return (s_category, s_launcher)

def _misc_search_launcher_by_name(self, launcher_name):
    s_launcher = None
    for launcherID in self.launchers:
        launcher = self.launchers[launcherID]
        if launcher_name == launcher['m_name']:
            s_launcher = launcher['id']
            return s_launcher

    return s_launcher

def autoconfig_import_launchers(import_FN):
    # >> Load XML file. Fill missing XML tags with sensible defaults.
    __debug_xml_parser = True
    imported_launchers_list = []
    log_verb('_command_import_launchers() Loading {0}'.format(import_FN.getOriginalPath()))
    try:
        xml_tree = ET.parse(import_FN.getPath())
    except ET.ParseError as e:
        log_error('(ParseError) Exception parsing XML categories.xml')
        log_error('(ParseError) {0}'.format(str(e)))
        kodi_dialog_OK('(ParseError) Exception reading categories.xml. '
                       'Maybe XML file is corrupt or contains invalid characters.')
        return
    xml_root = xml_tree.getroot()
    for root_element in xml_root:
        if __debug_xml_parser: log_debug('Root child tag <{0}>'.format(root_element.tag))

        if root_element.tag == 'launcher':
            launcher = self._misc_get_default_import_launcher()
            for root_child in root_element:
                # >> By default read strings
                xml_text = root_child.text if root_child.text is not None else ''
                xml_text = text_unescape_XML(xml_text)
                xml_tag  = root_child.tag
                if __debug_xml_parser: log_debug('"{0:<11s}" --> "{1}"'.format(xml_tag, xml_text))

                # >> Transform list datatype
                if xml_tag == 'args_extra' and xml_text:
                    # >> Only add to the list if string is non empty.
                    launcher[xml_tag].append(xml_text)
                else:
                    launcher[xml_tag] = xml_text
            # --- Add launcher to categories dictionary ---
            log_debug('Adding to list launcher "{0}"'.format(launcher['name']))
            imported_launchers_list.append(launcher)

    # >> Traverse launcher list and import all launchers found in XML file.
    # A) Match categories by name. If multiple categories with same name pick the first one.
    # B) If category does not exist create a new one.
    # C) Launchers are matched by name. If launcher name not found then create a new launcherID.
    for i_launcher in imported_launchers_list:
        log_info('Processing Launcher "{0}"'.format(i_launcher['name']))
        log_info('      with Category "{0}"'.format(i_launcher['category']))
        (s_categoryID, s_launcherID) = self._misc_search_category_and_launcher_by_name(i_launcher['category'], i_launcher['name'])
        log_debug('s_launcher = "{0}"'.format(s_launcherID))
        log_debug('s_category = "{0}"'.format(s_categoryID))
        
        # Options
        # A) Category not found. This implies launcher not found.
        # B) Category found and Launcher not found.
        # C) Category and Launcher found.
        # >> If category not found then create a new one for this imported launcher
        if not s_categoryID:
            # >> Create category AND launcher and import.
            # >> NOTE root_addon category is always found in _misc_search_category_and_launcher_by_name()
            log_debug('Case A) Category not found. This implies launcher not found.')
            category = fs_new_category()
            categoryID = misc_generate_random_SID()
            category['id'] = categoryID
            category['m_name'] = i_launcher['category']
            self.categories[categoryID] = category
            log_debug('New Category "{0}" (ID {1})'.format(i_launcher['category'], categoryID))

            # >> Create new launcher inside newly created category and import launcher.
            launcherID = misc_generate_random_SID()
            launcherdata = fs_new_launcher()
            launcherdata['id'] = launcherID
            launcherdata['categoryID'] = categoryID
            launcherdata['timestamp_launcher'] = time.time()
            self.launchers[launcherID] = launcherdata
            log_debug('New Launcher "{0}" (ID {1})'.format(i_launcher['name'], launcherID))

            # >> Import launcher. Only import fields that are not empty strings.
            # >> Function edits self.launchers dictionary using first argument key
            self._misc_import_launcher(launcherID, i_launcher, i_launcher['category'])

        elif s_categoryID and not s_launcherID:
            # >> Create new launcher inside existing category and import launcher.
            log_debug('Case B) Category found and Launcher not found.')
            launcherID = misc_generate_random_SID()
            launcherdata = fs_new_launcher()
            launcherdata['id'] = launcherID
            launcherdata['categoryID'] = s_categoryID
            launcherdata['timestamp_launcher'] = time.time()
            self.launchers[launcherID] = launcherdata
            log_debug('New Launcher "{0}" (ID {1})'.format(i_launcher['name'], launcherID))

            # >> Import launcher. Only import fields that are not empty strings.
            self._misc_import_launcher(launcherID, i_launcher, i_launcher['category'])

        else:
            # >> Both category and launcher exists (by name). Overwrite?
            log_debug('Case C) Category and Launcher found.')
            cat_name = i_launcher['category'] if i_launcher['category'] != VCATEGORY_ADDONROOT_ID else 'Root Category'
            ret = kodi_dialog_yesno('Launcher {0} in Category {1} '.format(i_launcher['name'], cat_name) +
                                    'found in AEL database. Overwrite?')
            if ret < 1: continue

            # >> Import launcher. Only import fields that are not empty strings.
            self._misc_import_launcher(s_launcherID, i_launcher, i_launcher['category'])

    # >> Save Categories/Launchers
    fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
    kodi_refresh_container()
    if len(imported_launchers_list) == 1:
        kodi_notify('Imported Launcher "{0}" configuration'.format(imported_launchers_list[0]['name']))
    else:
        kodi_notify('Imported {0} Launcher configurations'.format(len(imported_launchers_list)))

#
# Never change i_launcher['id'] or i_launcher['categoryID'] in this function.
#
def _misc_import_launcher(self, s_launcherID, i_launcher, category_name):
    # --- Metadata ---
    if i_launcher['name']:
        old_launcher_name = self.launchers[s_launcherID]['m_name']
        new_launcher_name = i_launcher['name']
        log_debug('old_launcher_name "{0}"'.format(old_launcher_name))
        log_debug('new_launcher_name "{0}"'.format(new_launcher_name))
        self.launchers[s_launcherID]['m_name'] = i_launcher['name']
        log_debug('Imported m_name      = "{0}"'.format(i_launcher['name']))
    if i_launcher['year']:
        self.launchers[s_launcherID]['m_year'] = i_launcher['year']
        log_debug('Imported m_year      = "{0}"'.format(i_launcher['year']))
    if i_launcher['genre']:
        self.launchers[s_launcherID]['m_genre'] = i_launcher['genre']
        log_debug('Imported m_genre     = "{0}"'.format(i_launcher['genre']))
    if i_launcher['studio']:
        self.launchers[s_launcherID]['m_studio'] = i_launcher['studio']
        log_debug('Imported m_studio    = "{0}"'.format(i_launcher['studio']))
    if i_launcher['rating']:
        self.launchers[s_launcherID]['m_rating'] = i_launcher['rating']
        log_debug('Imported m_rating    = "{0}"'.format(i_launcher['rating']))
    if i_launcher['plot']:
        self.launchers[s_launcherID]['m_plot'] = i_launcher['plot']
        log_debug('Imported m_plot      = "{0}"'.format(i_launcher['plot']))

    # --- Launcher stuff ---
    if i_launcher['platform']:
        # >> If platform cannot be found in the official list then set it to Unknown
        if i_launcher['platform'] in AEL_platform_list:
            log_debug('Platform name recognised')
            platform = i_launcher['platform']
        else:
            log_debug('Unrecognised platform name "{0}". Setting to Unknown'.format(i_launcher['platform']))
            platform = 'Unknown'
        self.launchers[s_launcherID]['platform'] = platform
        log_debug('Imported platform    = "{0}"'.format(platform))
    if i_launcher['application']:
        self.launchers[s_launcherID]['application'] = i_launcher['application']
        log_debug('Imported application = "{0}"'.format(i_launcher['application']))
    if i_launcher['args']:
        self.launchers[s_launcherID]['args']        = i_launcher['args']
        log_debug('Imported args        = "{0}"'.format(i_launcher['args']))
    # >> For every args_extra item add one entry to the list
    if i_launcher['args_extra']:
        # >> Reset current args_extra
        self.launchers[s_launcherID]['args_extra'] = []
        for args in i_launcher['args_extra']:
            
            self.launchers[s_launcherID]['args_extra'].append(args)
            log_debug('Imported args_extra  = "{0}"'.format(args))
    if i_launcher['rompath']:
        rompath = FileName(i_launcher['rompath'])
        log_debug('ROMpath OP "{0}"'.format(rompath.getOriginalPath()))
        log_debug('ROMpath  P "{0}"'.format(rompath.getPath()))
        # Warn user if rompath directory does not exist
        if not rompath.exists():
            log_debug('ROMpath not found.')
            kodi_dialog_OK('Launcher "{0}". '.format(i_launcher['name']) +
                           'ROM path "{0}" not found'.format(rompath.getPath()))
        else:
            log_debug('ROMpath found.')
        self.launchers[s_launcherID]['rompath'] = i_launcher['rompath']
        log_debug('Imported rompath     = "{0}"'.format(i_launcher['rompath']))
    if i_launcher['romext']:
        self.launchers[s_launcherID]['romext'] = i_launcher['romext']
        log_debug('Imported romext      = "{0}"'.format(i_launcher['romext']))

    # --- Assets (not supported at the moment) ---
    if i_launcher['path_assets']:
        Path_assets_FN = FileName(i_launcher['path_assets'])
        log_debug('Path_assets_FN OP "{0}"'.format(Path_assets_FN.getOriginalPath()))
        log_debug('Path_assets_FN  P "{0}"'.format(Path_assets_FN.getPath()))

        # >> Warn user if Path_assets_FN directory does not exist
        if not Path_assets_FN.exists():
            log_debug('Asset path not found!')
            kodi_dialog_OK('Launcher "{0}". '.format(i_launcher['name']) +
                           'Assets path "{0}" not found.'.format(Path_assets_FN.getPath()) +
                           'Asset subdirectories will not be created.')
        # >> Create asset directories if ROM path exists
        else:
            log_debug('Asset path found. Creating assets directories.')
            assets_init_asset_dir(Path_assets_FN, self.launchers[s_launcherID])

    # >> Name of launcher has changed.
    #    Regenerate roms_base_noext and rename old one if necessary.
    old_roms_base_noext          = self.launchers[s_launcherID]['roms_base_noext']
    old_roms_file_json           = ROMS_DIR.join(old_roms_base_noext + '.json')
    old_roms_file_xml            = ROMS_DIR.join(old_roms_base_noext + '.xml')
    old_PClone_index_file_json   = ROMS_DIR.join(old_roms_base_noext + '_PClone_index.json')
    old_PClone_parents_file_json = ROMS_DIR.join(old_roms_base_noext + '_PClone_parents.json')
    log_debug('old_roms_base_noext "{0}"'.format(old_roms_base_noext))
    new_roms_base_noext          = fs_get_ROMs_basename(category_name, new_launcher_name, s_launcherID)
    new_roms_file_json           = ROMS_DIR.join(new_roms_base_noext + '.json')
    new_roms_file_xml            = ROMS_DIR.join(new_roms_base_noext + '.xml')
    new_PClone_index_file_json   = ROMS_DIR.join(new_roms_base_noext + '_PClone_index.json')
    new_PClone_parents_file_json = ROMS_DIR.join(new_roms_base_noext + '_PClone_parents.json')
    log_debug('new_roms_base_noext "{0}"'.format(new_roms_base_noext))

    # >> Rename ROMS JSON/XML only if there is a change in filenames.
    if old_roms_base_noext != new_roms_base_noext:
        log_debug('Renaming JSON/XML launcher databases')
        self.launchers[s_launcherID]['roms_base_noext'] = new_roms_base_noext
        # >> Only rename files if originals found.
        if old_roms_file_json.exists():
            old_roms_file_json.rename(new_roms_file_json)
            log_debug('RENAMED {0}'.format(old_roms_file_json.getOriginalPath()))
            log_debug('   into {0}'.format(new_roms_file_json.getOriginalPath()))
        if old_roms_file_xml.exists():
            old_roms_file_xml.rename(new_roms_file_xml)
            log_debug('RENAMED {0}'.format(old_roms_file_xml.getOriginalPath()))
            log_debug('   into {0}'.format(new_roms_file_xml.getOriginalPath()))
        if old_PClone_index_file_json.exists():
            old_PClone_index_file_json.rename(new_PClone_index_file_json)
            log_debug('RENAMED {0}'.format(old_PClone_index_file_json.getOriginalPath()))
            log_debug('   into {0}'.format(new_PClone_index_file_json.getOriginalPath()))
        if old_PClone_parents_file_json.exists():
            old_PClone_parents_file_json.rename(new_PClone_parents_file_json)
            log_debug('RENAMED {0}'.format(old_PClone_parents_file_json.getOriginalPath()))
            log_debug('   into {0}'.format(new_PClone_parents_file_json.getOriginalPath()))
    else:
        log_debug('Not renaming databases (old and new names are equal)')
