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

# --- XML stuff ---
# ~~~ cElementTree sometimes fails to parse XML in Kodi's Python interpreter... I don't know why
# import xml.etree.cElementTree as ET

# ~~~ Using ElementTree seems to solve the problem
import xml.etree.ElementTree as ET

# --- Kodi stuff ---
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

# --- AEL packages ---
from constants import *
from utils import *
from utils_kodi import *
from disk_IO import *
from assets import *

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
def autoconfig_get_default_import_category():
    l = {
        'name' : '',
        'genre' : '',
        'rating' : '',
        'plot' : '',
        'asset_prefix' : ''
    }

    return l

def autoconfig_get_default_import_launcher():
    l = {
        'name' : '',
        'category' : 'root_category',
        'year' : '',
        'genre' : '',
        'developer' : '',
        'rating' : '',
        'plot' : '',
        'platform' : 'Unknown',
        'application' : '',
        'args' : '',
        'args_extra' : [],
        'asset_prefix' : '',
        'ROM_path' : '',
        'ROM_ext' : '',
        'ROM_asset_path' : ''
    }

    return l

def autoconfig_search_all_by_name(i_launcher, categories, launchers):
    cat_name = i_launcher['category']
    laun_name = i_launcher['name']
    s_category = None
    if cat_name == VCATEGORY_ADDONROOT_ID:
        s_category = VCATEGORY_ADDONROOT_ID
    else:
        for categoryID in categories:
            category = categories[categoryID]
            if cat_name == category['m_name']:
                s_category = category['id']
                break

    # >> If the category was found then search the launcher inside that category.
    if s_category:
        s_launcher = None
        for launcherID, launcher in launchers.iteritems():
            if s_category != launcher['categoryID']: continue
            if laun_name == launcher['m_name']:
                s_launcher = launcher['id']
                break
    # >> If the category was not found then launcher does not exist.
    else:
        s_launcher = None

    return (s_category, s_launcher)

def autoconfig_search_category_by_name(i_category, categories):
    cat_name = i_category['name']
    s_category = None
    if cat_name == VCATEGORY_ADDONROOT_ID:
        s_category = VCATEGORY_ADDONROOT_ID
    else:
        for categoryID in categories:
            if cat_name == categories[categoryID]['m_name']:
                s_category = categories[categoryID]['id']
                break

    return s_category

# def autoconfig_search_launcher_by_name(launcher_name):
#     s_launcher = None
#     for launcherID in self.launchers:
#         launcher = self.launchers[launcherID]
#         if launcher_name == launcher['m_name']:
#             s_launcher = launcher['id']
#             return s_launcher
# 
#     return s_launcher

def autoconfig_import_launchers(CATEGORIES_FILE_PATH, categories, launchers, import_FN):
    # >> Load XML file. Fill missing XML tags with sensible defaults.
    __debug_xml_parser = True
    log_verb('autoconfig_import_launchers() Loading {0}'.format(import_FN.getOriginalPath()))
    try:
        xml_tree = ET.parse(import_FN.getPath())
    except ET.ParseError as e:
        log_error('(ParseError) Exception parsing XML categories.xml')
        log_error('(ParseError) {0}'.format(str(e)))
        kodi_dialog_OK('(ParseError) Exception reading categories.xml. '
                       'Maybe XML file is corrupt or contains invalid characters.')
        return
    xml_root = xml_tree.getroot()

    # >> Process tags in XML configuration file
    imported_categories_list = []
    imported_launchers_list = []
    for root_element in xml_root:
        if __debug_xml_parser: log_debug('>>> Root child tag <{0}>'.format(root_element.tag))

        if root_element.tag == 'category':
            category_temp = autoconfig_get_default_import_category()
            for root_child in root_element:
                # >> By default read strings
                xml_text = root_child.text if root_child.text is not None else ''
                xml_text = text_unescape_XML(xml_text)
                xml_tag  = root_child.tag
                if __debug_xml_parser: log_debug('>>> "{0:<11s}" --> "{1}"'.format(xml_tag, xml_text))
                category_temp[xml_tag] = xml_text
            # --- Add category to categories dictionary ---
            log_debug('Adding category "{0}" to import list'.format(category_temp['name']))
            imported_categories_list.append(category_temp)
        elif root_element.tag == 'launcher':
            launcher_temp = autoconfig_get_default_import_launcher()
            for root_child in root_element:
                # >> By default read strings
                xml_text = root_child.text if root_child.text is not None else ''
                xml_text = text_unescape_XML(xml_text)
                xml_tag  = root_child.tag
                if __debug_xml_parser: log_debug('>>> "{0:<11s}" --> "{1}"'.format(xml_tag, xml_text))

                # >> Transform list datatype. Only add to the list if string is non empty.
                if xml_tag == 'args_extra' and xml_text: launcher_temp[xml_tag].append(xml_text)
                else:                                    launcher_temp[xml_tag] = xml_text
            # --- Add launcher to categories dictionary ---
            log_debug('Adding launcher "{0}" to import list'.format(launcher_temp['name']))
            imported_launchers_list.append(launcher_temp)
        else:
            log_warning('Unrecognised root tag <{0}>'.format(root_element.tag))

    # >> Traverse category import list and import all launchers found in XML file.
    for i_category in imported_categories_list:
        log_info('Processing Category "{0}"'.format(i_category['name']))

        # >> Search category/launcher database to check if imported launcher/category exist.
        s_categoryID = autoconfig_search_category_by_name(i_category, categories)
        log_debug('s_category = "{0}"'.format(s_categoryID))

        # --- Options ---
        # A) Category not found. Create new category.
        # B) Category found. Edit existing category.
        if not s_categoryID:
            # >> Create category AND launcher and import.
            # >> NOTE root_addon category is always found in autoconfig_search_all_by_name()
            log_debug('Case A) Category not found. Create new category.')
            category = fs_new_category()
            categoryID = misc_generate_random_SID()
            category['id'] = categoryID
            category['m_name'] = i_category['name']
            categories[categoryID] = category
            log_debug('New Category "{0}" (ID {1})'.format(i_category['name'], categoryID))

            # >> Import launcher. Only import fields that are not empty strings.
            autoconfig_import_category(categories, categoryID, i_category, import_FN)
        else:
            # >> Category exists (by name). Overwrite?
            log_debug('Case B) Category found. Edit existing category.')
            ret = kodi_dialog_yesno('Category "{0}" found in AEL database. Overwrite?'.format(i_category['name']))
            if ret < 1: continue

            # >> Import launcher. Only import fields that are not empty strings.
            autoconfig_import_category(categories, s_categoryID, i_category, import_FN)

    # >> Traverse launcher import list and import all launchers found in XML file.
    # A) Match categories by name. If multiple categories with same name pick the first one.
    # B) If category does not exist create a new one.
    # C) Launchers are matched by name. If launcher name not found then create a new launcherID.
    for i_launcher in imported_launchers_list:
        log_info('Processing Launcher "{0}"'.format(i_launcher['name']))
        log_info('      with Category "{0}"'.format(i_launcher['category']))
        
        # >> Search category/launcher database to check if imported launcher/category exist.
        (s_categoryID, s_launcherID) = autoconfig_search_all_by_name(i_launcher, categories, launchers)
        log_debug('s_launcher = "{0}"'.format(s_launcherID))
        log_debug('s_category = "{0}"'.format(s_categoryID))

        # --- Options ---
        # NOTE If category not found then create a new one for this imported launcher
        # A) Category not found. This implies launcher not found.
        # B) Category found and Launcher not found.
        # C) Category found and Launcher found.
        if not s_categoryID:
            # >> Create category AND launcher and import.
            # >> NOTE root_addon category is always found in autoconfig_search_all_by_name()
            log_debug('Case A) Category not found. This implies launcher not found.')
            category = fs_new_category()
            categoryID = misc_generate_random_SID()
            category['id'] = categoryID
            category['m_name'] = i_launcher['category']
            categories[categoryID] = category
            log_debug('New Category "{0}" (ID {1})'.format(i_launcher['category'], categoryID))

            # >> Create new launcher inside newly created category and import launcher.
            launcherID = misc_generate_random_SID()
            launcherdata = fs_new_launcher()
            launcherdata['id'] = launcherID
            launcherdata['categoryID'] = categoryID
            launcherdata['timestamp_launcher'] = time.time()
            launchers[launcherID] = launcherdata
            log_debug('New Launcher "{0}" (ID {1})'.format(i_launcher['name'], launcherID))

            # >> Import launcher. Only import fields that are not empty strings.
            # >> Function edits self.launchers dictionary using first argument key
            autoconfig_import_launcher(launchers, launcherID, i_launcher, import_FN)

        elif s_categoryID and not s_launcherID:
            # >> Create new launcher inside existing category and import launcher.
            log_debug('Case B) Category found and Launcher not found.')
            launcherID = misc_generate_random_SID()
            launcherdata = fs_new_launcher()
            launcherdata['id'] = launcherID
            launcherdata['categoryID'] = s_categoryID
            launcherdata['timestamp_launcher'] = time.time()
            launchers[launcherID] = launcherdata
            log_debug('New Launcher "{0}" (ID {1})'.format(i_launcher['name'], launcherID))

            # >> Import launcher. Only import fields that are not empty strings.
            autoconfig_import_launcher(launchers, launcherID, i_launcher, import_FN)

        else:
            # >> Both category and launcher exists (by name). Overwrite?
            log_debug('Case C) Category and Launcher found.')
            cat_name = i_launcher['category'] if i_launcher['category'] != VCATEGORY_ADDONROOT_ID else 'Root Category'
            ret = kodi_dialog_yesno('Launcher {0} in Category {1} '.format(i_launcher['name'], cat_name) +
                                    'found in AEL database. Overwrite?')
            if ret < 1: continue

            # >> Import launcher. Only import fields that are not empty strings.
            autoconfig_import_launcher(launchers, s_launcherID, i_launcher, import_FN)

    # --- Save Categories/Launchers, update timestamp and notify user ---
    fs_write_catfile(CATEGORIES_FILE_PATH, categories, launchers)
    kodi_refresh_container()
    kodi_notify('Finished importing Categories/Launchers')

#
# Imports/edits a category.
#
def autoconfig_import_category(categories, categoryID, i_category, import_FN):
    log_debug('autoconfig_import_category() categoryID = {0}'.format(categoryID))

    # --- Category metadata ---
    if i_category['name']:
        categories[categoryID]['m_name'] = i_category['name']
        log_debug('Imported m_name   = "{0}"'.format(i_category['name']))
        
    if i_category['genre']:
        categories[categoryID]['m_genre'] = i_category['genre']
        log_debug('Imported m_genre  = "{0}"'.format(i_category['genre']))
        
    if i_category['rating']:
        categories[categoryID]['m_rating'] = i_category['rating']
        log_debug('Imported m_rating = "{0}"'.format(i_category['rating']))
        
    if i_category['plot']:
        categories[categoryID]['m_plot'] = i_category['plot']
        log_debug('Imported m_plot   = "{0}"'.format(i_category['plot']))

    # --- Category assets/artwork ---
    if i_category['asset_prefix']:
        asset_prefix = i_category['asset_prefix']
        log_debug('Importing category assets with prefix "{0}"'.format(asset_prefix))
        # log_debug('import_FN "{0}"'.format(import_FN.getPath()))

        # >> Get a list of all files in the XML config file directory.
        # >> This list has filenames withouth path.
        file_list = sorted(os.listdir(import_FN.getDir()))
        # log_debug('--- File list ---')
        # for file in file_list: log_debug('--- "{0}"'.format(file))

        # >> Traverse list of category assets and search for image files for each asset
        for cat_asset in CATEGORY_ASSET_LIST:
            # >> Bypass trailers now
            if cat_asset == ASSET_TRAILER: continue

            # >> Look for assets
            AInfo = assets_get_info_scheme(cat_asset)
            log_debug('>> Asset "{0}"'.format(AInfo.name))
            asset_file_list = autoconfig_search_asset_file_list(asset_prefix, AInfo, import_FN, file_list)
            if not asset_file_list: continue
            listitems_list = []
            listitems_asset_paths = []

            # >> Current image if found
            current_FN = FileName(categories[categoryID][AInfo.key])
            if current_FN.exists():
                asset_listitem = xbmcgui.ListItem(label = 'Current image', label2 = current_FN.getPath())
                asset_listitem.setArt({'icon' : current_FN.getPath()})
                listitems_list.append(asset_listitem)
                listitems_asset_paths.append(current_FN.getPath())
            # >> Images found in XML configuration
            for asset_file_name in asset_file_list:
                log_debug('asset_file_name "{0}"'.format(asset_file_name))
                asset_FN = FileName(asset_file_name)
                asset_listitem = xbmcgui.ListItem(label = asset_FN.getBase(), label2 = asset_file_name)
                asset_listitem.setArt({'icon' : asset_file_name})
                listitems_list.append(asset_listitem)
                listitems_asset_paths.append(asset_FN.getPath())
            # >> No image
            asset_listitem = xbmcgui.ListItem(label = 'No image')
            asset_listitem.setArt({'icon' : 'DefaultAddonNone.png'})
            listitems_list.append(asset_listitem)
            listitems_asset_paths.append('')

            title_str = 'Category "{0}". Choose {1} file'.format(i_category['name'], AInfo.name)
            ret_idx = xbmcgui.Dialog().select(title_str, list = listitems_list, useDetails = True)
            if ret_idx < 0: return

            # >> Set asset field
            categories[categoryID][AInfo.key] = listitems_asset_paths[ret_idx]
            log_verb('Set category image "{0}" = "{1}"'.format(AInfo.key, listitems_asset_paths[ret_idx]))

#
# Never change i_launcher['id'] or i_launcher['categoryID'] in this function.
#
def autoconfig_import_launcher(launchers, s_launcherID, i_launcher, import_FN):
    log_debug('autoconfig_import_category() s_launcherID = {0}'.format(s_launcherID))

    # --- Launcher metadata ---
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

    # --- Launcher assets/artwork ---
    # >> Have a look at autoconfig_import_category() for a reference implementation.
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

#
# Search for asset files and return a list of found asset files.
# Get a non-recursive list of all files on the directory the XML configuration file is. Then,
# scan this list for asset matching.
#
# Search patterns (<> is mandatory, [] is optional):
#
#   A) <asset_path_prefix>_<icon|fanart|banner|poster|clearlogo>[_Comment].<asset_extensions>
#   B) <asset_path_prefix>_<icon|fanart|banner|poster|clearlogo>_N[_Comment].<asset_extensions>
#   C) <asset_path_prefix>_<icon|fanart|banner|poster|clearlogo>_NN[_Comment].<asset_extensions>
#
# N is a number [0-9]
#
def autoconfig_search_asset_file_list(asset_prefix, AInfo, import_FN, file_list):
    # log_debug('autoconfig_search_asset_file_list() BEGIN asset infix "{0}"'.format(AInfo.fname_infix))

    asset_dir_FN = FileName(import_FN.getDir())
    # log_debug('asset_dir_FN "{0}"'.format(asset_dir_FN.getPath()))

    # >> Traverse list of filenames (no paths)
    filename_noext = asset_prefix + '_' + AInfo.fname_infix
    # log_debug('filename_noext "{0}"'.format(filename_noext))
    img_ext_regexp = asset_get_regexp_extension_list(IMAGE_EXTENSIONS)
    # log_debug('img_ext_regexp "{0}"'.format(img_ext_regexp))
    pattern = '({0})([\w]*?)\.{1}'.format(filename_noext, img_ext_regexp)
    # log_debug('Pattern "{0}"'.format(pattern))
    
    # --- Search for files in case A, B and C ---
    asset_file_list = []
    for file in file_list:
        # log_debug('Testing "{0}"'.format(file))
        m = re.match(pattern, file)
        if m:
            # log_debug('MATCH   "{0}"'.format(m.group(0)))
            asset_full_path = asset_dir_FN.pjoin(file)
            # log_verb('Adding  "{0}"'.format(asset_full_path.getPath()))
            asset_file_list.append(asset_full_path.getPath())
    # log_debug('autoconfig_search_asset_file_list() END')

    return asset_file_list
