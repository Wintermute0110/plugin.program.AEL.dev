# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher XML autoconfiguration stuff.
#

# Copyright (c) 2016-2019 Wintermute0110 <wintermute0110@gmail.com>
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
import time

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
from disk_IO import *
from assets import *
from platforms import *

# -------------------------------------------------------------------------------------------------
# Exports launchers to an XML file.
# Currently categories are not supported.
# -------------------------------------------------------------------------------------------------
#
# Helper function to export a single Category.
#
def autoconfig_export_category_str_list(category, str_list):
    str_list.append('<category>\n')
    str_list.append(XML_text('name', category['m_name']))
    str_list.append(XML_text('year', category['m_year']))
    str_list.append(XML_text('genre', category['m_genre']))
    str_list.append(XML_text('developer', category['m_developer']))
    str_list.append(XML_text('rating', category['m_rating']))
    str_list.append(XML_text('plot', category['m_plot']))
    str_list.append(XML_text('Asset_Prefix', category['Asset_Prefix']))
    str_list.append(XML_text('s_icon', category['s_icon']))
    str_list.append(XML_text('s_fanart', category['s_fanart']))
    str_list.append(XML_text('s_banner', category['s_banner']))
    str_list.append(XML_text('s_poster', category['s_poster']))
    str_list.append(XML_text('s_clearlogo', category['s_clearlogo']))
    str_list.append(XML_text('s_trailer', category['s_trailer']))
    str_list.append('</category>\n')

#
# Helper function to export a single Launcher.
#
def autoconfig_export_launcher_str_list(launcher, category_name, str_list):
    # >> Check if all artwork paths share the same ROM_asset_path. Unless the user has
    # >> customised the ROM artwork paths this should be the case.
    # >> A) This function checks if all path_* share a common root directory. If so
    # >>    this function returns that common directory as an Unicode string. In this
    # >>    case AEL will write the tag <ROM_asset_path> only.
    # >> B) If path_* do not share a common root directory this function returns '' and then
    # >>    AEL writes all <path_*> tags in the XML file.
    ROM_asset_path = assets_get_ROM_asset_path(launcher)
    log_verb('autoconfig_export_all() ROM_asset_path "{0}"'.format(ROM_asset_path))

    # >> Export Launcher
    str_list.append('<launcher>\n')
    str_list.append(XML_text('name', launcher['m_name']))
    str_list.append(XML_text('category', category_name))
    str_list.append(XML_text('year', launcher['m_year']))
    str_list.append(XML_text('genre', launcher['m_genre']))
    str_list.append(XML_text('developer', launcher['m_developer']))
    str_list.append(XML_text('rating', launcher['m_rating']))
    str_list.append(XML_text('plot', launcher['m_plot']))
    str_list.append(XML_text('platform', launcher['platform']))
    str_list.append(XML_text('application', launcher['application']))
    str_list.append(XML_text('args', launcher['args']))
    if launcher['args_extra']:
        for extra_arg in launcher['args_extra']: str_list.append(XML_text('args_extra', extra_arg))
    else:
        str_list.append(XML_text('args_extra', ''))
    str_list.append(XML_text('ROM_path', launcher['rompath']))
    str_list.append(XML_text('ROM_ext', launcher['romext']))
    if ROM_asset_path:
        str_list.append(XML_text('ROM_asset_path', ROM_asset_path))
    else:
        str_list.append(XML_text('path_title', launcher['path_title']))
        str_list.append(XML_text('path_snap', launcher['path_snap']))
        str_list.append(XML_text('path_boxfront', launcher['path_boxfront']))
        str_list.append(XML_text('path_boxback', launcher['path_boxback']))
        str_list.append(XML_text('path_cartridge', launcher['path_cartridge']))
        str_list.append(XML_text('path_fanart', launcher['path_fanart']))
        str_list.append(XML_text('path_banner', launcher['path_banner']))
        str_list.append(XML_text('path_clearlogo', launcher['path_clearlogo']))
        str_list.append(XML_text('path_flyer', launcher['path_flyer']))
        str_list.append(XML_text('path_map', launcher['path_map']))
        str_list.append(XML_text('path_manual', launcher['path_manual']))
        str_list.append(XML_text('path_trailer', launcher['path_trailer']))
    str_list.append(XML_text('Asset_Prefix', launcher['Asset_Prefix']))
    str_list.append(XML_text('s_icon', launcher['s_icon']))
    str_list.append(XML_text('s_fanart', launcher['s_fanart']))
    str_list.append(XML_text('s_banner', launcher['s_banner']))
    str_list.append(XML_text('s_poster', launcher['s_poster']))
    str_list.append(XML_text('s_clearlogo', launcher['s_clearlogo']))
    str_list.append(XML_text('s_controller', launcher['s_controller']))
    str_list.append(XML_text('s_trailer', launcher['s_trailer']))
    str_list.append('</launcher>\n')

#
# Export all Categories and Launchers.
# Check if the output XML file exists (and show a warning dialog if so) is done in caller.
#
def autoconfig_export_all(categories, launchers, export_FN):
    # --- XML header ---
    str_list = []
    str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
    str_list.append('<!-- Exported by AEL on {0} -->\n'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
    str_list.append('<advanced_emulator_launcher_configuration>\n')

    # --- Export Categories ---
    # >> Data which is not string must be converted to string
    for categoryID in sorted(categories, key = lambda x : categories[x]['m_name']):
        category = categories[categoryID]
        log_verb('autoconfig_export_all() Category "{0}" (ID "{1}")'.format(category['m_name'], categoryID))
        autoconfig_export_category_str_list(category, str_list)

    # --- Export Launchers and add XML tail ---
    # >> Data which is not string must be converted to string
    for launcherID in sorted(launchers, key = lambda x : launchers[x]['m_name']):
        launcher = launchers[launcherID]
        if launcher['categoryID'] in categories:
            category_name = categories[launcher['categoryID']]['m_name']
        elif launcher['categoryID'] == VCATEGORY_ADDONROOT_ID:
            category_name = VCATEGORY_ADDONROOT_ID
        else:
            kodi_dialog_OK('Launcher category not found. This is a bug, please report it.')
            return
        log_verb('autoconfig_export_all() Launcher "{0}" (ID "{1}")'.format(launcher['m_name'], launcherID))
        autoconfig_export_launcher_str_list(launcher, category_name, str_list)
    str_list.append('</advanced_emulator_launcher_configuration>\n')

    # >> Export file. Strings in the list are Unicode. Encode to UTF-8 when writing to file.
    fs_write_str_list_to_file(str_list, export_FN)

#
# Export a single Launcher XML configuration.
# Check if the output XML file exists (and show a warning dialog if so) is done in caller.
#
def autoconfig_export_launcher(launcher, export_FN, categories):
    # --- Export single Launcher ---
    launcherID = launcher['id']
    if launcher['categoryID'] in categories:
        category_name = categories[launcher['categoryID']]['m_name']
    elif launcher['categoryID'] == VCATEGORY_ADDONROOT_ID:
        category_name = VCATEGORY_ADDONROOT_ID
    else:
        kodi_dialog_OK('Launcher category not found. This is a bug, please report it.')
        raise AEL_Error('Error exporting Launcher XML configuration')
    log_verb('autoconfig_export_launcher() Launcher "{0}" (ID "{1}")'.format(launcher['m_name'], launcherID))

    # --- Create list of strings ---
    str_list = []
    str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
    str_list.append('<!-- Exported by AEL on {0} -->\n'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
    str_list.append('<advanced_emulator_launcher_configuration>\n')
    autoconfig_export_launcher_str_list(launcher, category_name, str_list)
    str_list.append('</advanced_emulator_launcher_configuration>\n')

    # >> Export file. Strings in the list are Unicode. Encode to UTF-8 when writing to file.
    fs_write_str_list_to_file(str_list, export_FN)

#
# Export a single Category XML configuration.
# Check if the output XML file exists (and show a warning dialog if so) is done in caller.
#
def autoconfig_export_category(category, export_FN):
    # --- Export single Category ---
    log_verb('autoconfig_export_category() Category "{0}" (ID "{1}")'.format(category['m_name'], category['id']))

    # --- Create list of strings ---
    str_list = []
    str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
    str_list.append('<!-- Exported by AEL on {0} -->\n'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
    str_list.append('<advanced_emulator_launcher_configuration>\n')
    autoconfig_export_category_str_list(category, str_list)
    str_list.append('</advanced_emulator_launcher_configuration>\n')

    # >> Export file. Strings in the list are Unicode. Encode to UTF-8 when writing to file.
    fs_write_str_list_to_file(str_list, export_FN)

# -------------------------------------------------------------------------------------------------
# Import AEL launcher configuration
# -------------------------------------------------------------------------------------------------
def autoconfig_get_default_import_category():
    l = {
        'name' : '',
        'year' : '',
        'genre' : '',
        'developer' : '',
        'rating' : '',
        'plot' : '',
        'Asset_Prefix' : '',
        's_icon' : '',
        's_fanart' : '',
        's_banner' : '',
        's_poster' : '',
        's_clearlogo' : '',
        's_trailer' : '',
    }

    return l

def autoconfig_get_default_import_launcher():
    l = {
        'name' : '',
        'category' : 'root_category',
        'Launcher_NFO' : '',
        'year' : '',
        'genre' : '',
        'developer' : '',
        'rating' : '',
        'plot' : '',
        'platform' : 'Unknown',
        'application' : '',
        'args' : '',
        'args_extra' : [],
        'ROM_path' : '',
        'ROM_ext' : '',
        'Options' : '',
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
        'path_trailer' : '',
        'Asset_Prefix' : '',
        's_icon' : '',
        's_fanart' : '',
        's_banner' : '',
        's_poster' : '',
        's_clearlogo' : '',
        's_controller' : '',
        's_trailer' : '',
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

def autoconfig_import_launchers(CATEGORIES_FILE_PATH, ROMS_DIR, categories, launchers, import_FN):
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
            autoconfig_import_launcher(ROMS_DIR, categories, launchers, categoryID, launcherID, i_launcher, import_FN)

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
            autoconfig_import_launcher(ROMS_DIR, categories, launchers, s_categoryID, launcherID, i_launcher, import_FN)

        else:
            # >> Both category and launcher exists (by name). Overwrite?
            log_debug('Case C) Category and Launcher found.')
            cat_name = i_launcher['category'] if i_launcher['category'] != VCATEGORY_ADDONROOT_ID else 'Root Category'
            ret = kodi_dialog_yesno('Launcher "{0}" in Category "{1}" '.format(i_launcher['name'], cat_name) +
                                    'found in AEL database. Overwrite?')
            if ret < 1: continue

            # >> Import launcher. Only import fields that are not empty strings.
            autoconfig_import_launcher(ROMS_DIR, categories, launchers, s_categoryID, s_launcherID, i_launcher, import_FN)

#
# Imports/edits a category with an extenal XML config file.
#
def autoconfig_import_category(categories, categoryID, i_category, import_FN):
    log_debug('autoconfig_import_category() categoryID = {0}'.format(categoryID))

    # --- Category metadata ---
    if i_category['name']:
        categories[categoryID]['m_name'] = i_category['name']
        log_debug('Imported m_name       "{0}"'.format(i_category['name']))

    if i_category['year']:
        categories[categoryID]['m_year'] = i_category['year']
        log_debug('Imported m_year       "{0}"'.format(i_category['year']))

    if i_category['genre']:
        categories[categoryID]['m_genre'] = i_category['genre']
        log_debug('Imported m_genre      "{0}"'.format(i_category['genre']))

    if i_category['developer']:
        categories[categoryID]['m_developer'] = i_category['developer']
        log_debug('Imported m_developer  "{0}"'.format(i_category['developer']))

    if i_category['rating']:
        categories[categoryID]['m_rating'] = i_category['rating']
        log_debug('Imported m_rating =   "{0}"'.format(i_category['rating']))

    if i_category['plot']:
        categories[categoryID]['m_plot'] = i_category['plot']
        log_debug('Imported m_plot       "{0}"'.format(i_category['plot']))

    # --- Category assets/artwork ---
    if i_category['Asset_Prefix']:
        categories[categoryID]['Asset_Prefix'] = i_category['Asset_Prefix']
        log_debug('Imported Asset_Prefix "{0}"'.format(i_category['Asset_Prefix']))
    Asset_Prefix = i_category['Asset_Prefix']
    if Asset_Prefix:
        log_debug('Asset_Prefix non empty. Looking for asset files.')
        (Asset_Prefix_head, Asset_Prefix_tail) = os.path.split(Asset_Prefix)
        log_debug('Effective Asset_Prefix "{0}"'.format(Asset_Prefix))
        log_debug('Asset_Prefix_head      "{0}"'.format(Asset_Prefix_head))
        log_debug('Asset_Prefix_tail      "{0}"'.format(Asset_Prefix_tail))
        if Asset_Prefix_head:
            log_debug('Asset_Prefix head not empty')
            asset_dir_FN = FileName(import_FN.getDir()).pjoin(Asset_Prefix_head)
            norm_asset_dir_FN = FileName(os.path.normpath(asset_dir_FN.getPath()))
            effective_Asset_Prefix = Asset_Prefix_tail
        else:
            log_debug('Asset_Prefix head is empty. Assets in same dir as XML file')
            asset_dir_FN = FileName(import_FN.getDir())
            norm_asset_dir_FN = FileName(os.path.normpath(asset_dir_FN.getPath()))
            effective_Asset_Prefix = Asset_Prefix_tail
        log_debug('import_FN              "{0}"'.format(import_FN.getPath()))
        log_debug('asset_dir_FN           "{0}"'.format(asset_dir_FN.getPath()))
        log_debug('norm_asset_dir_FN      "{0}"'.format(norm_asset_dir_FN.getPath()))
        log_debug('effective_Asset_Prefix "{0}"'.format(effective_Asset_Prefix))

        # >> Get a list of all files in the directory pointed by Asset_Prefix and use this list as
        # >> a file cache. This list has filenames withouth path.
        log_debug('Scanning files in dir "{0}"'.format(norm_asset_dir_FN.getPath()))
        try:
            file_list = sorted(os.listdir(norm_asset_dir_FN.getPath()))
        except WindowsError as E:
            log_error('autoconfig_import_category() (exceptions.WindowsError) exception')
            log_error('Exception message: "{0}"'.format(E))
            kodi_dialog_OK('WindowsError exception. {0}'.format(E))
            kodi_dialog_OK('Scanning assets using the Asset_Prefix tag in '
                           'Category "{0}" will be disabled.'.format(i_category['name']))
            file_list = []
        log_debug('Found {0} files'.format(len(file_list)))
        # log_debug('--- File list ---')
        # for file in file_list: log_debug('--- "{0}"'.format(file))
    else:
        log_debug('Asset_Prefix empty. Not looking for any asset files.')
        norm_asset_dir_FN = None
        effective_Asset_Prefix = ''
        file_list = []

    # >> Traverse list of category assets and search for image files for each asset
    for cat_asset in CATEGORY_ASSET_LIST:
        # >> Bypass trailers now
        if cat_asset == ASSET_TRAILER: continue

        # >> Look for assets using the file list cache.
        AInfo = assets_get_info_scheme(cat_asset)
        log_debug('>> Asset "{0}"'.format(AInfo.name))
        asset_file_list = autoconfig_search_asset_file_list(effective_Asset_Prefix, AInfo, norm_asset_dir_FN, file_list)

        # --- Create image list for selection dialog ---
        listitems_list = []
        listitems_asset_paths = []
        # >> Current image if found
        current_FN = FileName(categories[categoryID][AInfo.key])
        if current_FN.exists():
            asset_listitem = xbmcgui.ListItem(label = 'Current image', label2 = current_FN.getPath())
            asset_listitem.setArt({'icon' : current_FN.getPath()})
            listitems_list.append(asset_listitem)
            listitems_asset_paths.append(current_FN.getPath())
        # >> Image in <s_icon>, <s_fanart>, ... tags if found
        tag_asset_FN = FileName(i_category[AInfo.key])
        if tag_asset_FN.exists():
            asset_listitem = xbmcgui.ListItem(label = 'XML <{0}> image'.format(AInfo.key),
                                              label2 = tag_asset_FN.getPath())
            asset_listitem.setArt({'icon' : tag_asset_FN.getPath()})
            listitems_list.append(asset_listitem)
            listitems_asset_paths.append(tag_asset_FN.getPath())
        # >> Images found in XML configuration via <Asset_Prefix> tag if found
        image_count = 1
        for asset_file_name in asset_file_list:
            log_debug('asset_file_name "{0}"'.format(asset_file_name))
            asset_FN = FileName(asset_file_name)
            asset_listitem = xbmcgui.ListItem(label = '<Asset_Prefix> #{0} "{1}"'.format(image_count, asset_FN.getBase()),
                                              label2 = asset_file_name)
            asset_listitem.setArt({'icon' : asset_file_name})
            listitems_list.append(asset_listitem)
            listitems_asset_paths.append(asset_FN.getPath())
            image_count += 1
        # >> If list is empty at this point no images were found at all.
        if not listitems_list:
            log_debug('listitems_list is empty. Keeping {0} as it was.'.format(AInfo.name))
            continue
        # >> No image
        asset_listitem = xbmcgui.ListItem(label = 'No image')
        asset_listitem.setArt({'icon' : 'DefaultAddonNone.png'})
        listitems_list.append(asset_listitem)
        listitems_asset_paths.append('')

        # >> Show image selection select() dialog
        title_str = 'Category "{0}". Choose {1} ...'.format(i_category['name'], AInfo.name)
        ret_idx = xbmcgui.Dialog().select(title_str, list = listitems_list, useDetails = True)
        if ret_idx < 0: return

        # >> Set asset field
        categories[categoryID][AInfo.key] = listitems_asset_paths[ret_idx]
        log_verb('Set category artwork "{0}" = "{1}"'.format(AInfo.key, listitems_asset_paths[ret_idx]))

#
# Imports/Edits a launcher with an extenal XML config file.
#
def autoconfig_import_launcher(ROMS_DIR, categories, launchers, categoryID, launcherID, i_launcher, import_FN):
    log_debug('autoconfig_import_launcher() categoryID = {0}'.format(categoryID))
    log_debug('autoconfig_import_launcher() launcherID = {0}'.format(launcherID))
    Launcher_NFO_meta = {'year' : '', 'genre' : '', 'developer' : '', 'rating' : '', 'plot' : ''}
    XML_meta          = {'year' : '', 'genre' : '', 'developer' : '', 'rating' : '', 'plot' : ''}

    # --- Launcher metadata ---
    if i_launcher['name']:
        old_launcher_name = launchers[launcherID]['m_name']
        new_launcher_name = i_launcher['name']
        log_debug('old_launcher_name "{0}"'.format(old_launcher_name))
        log_debug('new_launcher_name "{0}"'.format(new_launcher_name))
        launchers[launcherID]['m_name'] = i_launcher['name']
        log_debug('Imported m_name "{0}"'.format(i_launcher['name']))

    # >> Process <Launcher_NFO> before any metadata tag
    if i_launcher['Launcher_NFO']:
        log_debug('Imported Launcher_NFO "{0}"'.format(i_launcher['Launcher_NFO']))
        Launcher_NFO_FN = FileName(import_FN.getDir()).pjoin(i_launcher['Launcher_NFO'])
        Launcher_NFO_meta = fs_read_launcher_NFO(Launcher_NFO_FN)
        log_debug('NFO year      "{0}"'.format(Launcher_NFO_meta['year']))
        log_debug('NFO genre     "{0}"'.format(Launcher_NFO_meta['genre']))
        log_debug('NFO developer "{0}"'.format(Launcher_NFO_meta['developer']))
        log_debug('NFO rating    "{0}"'.format(Launcher_NFO_meta['rating']))
        log_debug('NFO plot      "{0}"'.format(Launcher_NFO_meta['plot']))

    # >> Process XML metadata and put in temporal dictionary
    if i_launcher['year']:
        XML_meta['year'] = i_launcher['year']
        log_debug('XML year      "{0}"'.format(i_launcher['year']))

    if i_launcher['genre']:
        XML_meta['genre'] = i_launcher['genre']
        log_debug('XML genre     "{0}"'.format(i_launcher['genre']))

    if i_launcher['developer']:
        XML_meta['developer'] = i_launcher['developer']
        log_debug('XML developer "{0}"'.format(i_launcher['developer']))

    if i_launcher['rating']:
        XML_meta['rating'] = i_launcher['rating']
        log_debug('XML rating    "{0}"'.format(i_launcher['rating']))

    if i_launcher['plot']:
        XML_meta['plot'] = i_launcher['plot']
        log_debug('XML plot      "{0}"'.format(i_launcher['plot']))

    # >> Process metadata. XML metadata overrides Launcher_NFO metadata, if exists.
    if XML_meta['year']:
        launchers[launcherID]['m_year'] = XML_meta['year']
        log_debug('Imported m_year "{0}"'.format(XML_meta['year']))
    elif Launcher_NFO_meta['year']:
        launchers[launcherID]['m_year'] = Launcher_NFO_meta['year']
        log_debug('Imported m_year "{0}"'.format(Launcher_NFO_meta['year']))

    if XML_meta['genre']:
        launchers[launcherID]['m_genre'] = XML_meta['genre']
        log_debug('Imported m_genre "{0}"'.format(XML_meta['genre']))
    elif Launcher_NFO_meta['genre']:
        launchers[launcherID]['m_genre'] = Launcher_NFO_meta['genre']
        log_debug('Imported m_genre "{0}"'.format(Launcher_NFO_meta['genre']))

    if XML_meta['developer']:
        launchers[launcherID]['m_developer'] = XML_meta['developer']
        log_debug('Imported m_developer "{0}"'.format(XML_meta['developer']))
    elif Launcher_NFO_meta['developer']:
        launchers[launcherID]['m_developer'] = Launcher_NFO_meta['developer']
        log_debug('Imported m_developer "{0}"'.format(Launcher_NFO_meta['developer']))

    if XML_meta['rating']:
        launchers[launcherID]['m_rating'] = XML_meta['rating']
        log_debug('Imported m_rating "{0}"'.format(XML_meta['rating']))
    elif Launcher_NFO_meta['rating']:
        launchers[launcherID]['m_rating'] = Launcher_NFO_meta['rating']
        log_debug('Imported m_rating "{0}"'.format(Launcher_NFO_meta['rating']))

    if XML_meta['plot']:
        launchers[launcherID]['m_plot'] = XML_meta['plot']
        log_debug('Imported m_plot "{0}"'.format(XML_meta['plot']))
    elif Launcher_NFO_meta['plot']:
        launchers[launcherID]['m_plot'] = Launcher_NFO_meta['plot']
        log_debug('Imported m_plot "{0}"'.format(Launcher_NFO_meta['plot']))

    # --- Launcher stuff ---
    # >> If platform cannot be found in the official list then warn user and set it to 'Unknown'
    if i_launcher['platform']:
        platform = i_launcher['platform']
        if i_launcher['platform'] in AEL_platform_list:
            log_debug('Platform name "{0}" recognised'.format(platform))
        else:
            kodi_dialog_OK('Unrecognised platform name "{0}".'.format(platform),
                           title = 'Launcher "{0}"'.format(i_launcher['name']))
            log_debug('Unrecognised platform name "{0}".'.format(platform))
        launchers[launcherID]['platform'] = platform
        log_debug('Imported platform "{0}"'.format(platform))

    # >> If application not found warn user.
    if i_launcher['application']:
        app_FN = FileName(i_launcher['application'])
        if not app_FN.exists():
            log_debug('Application NOT found.')
            kodi_dialog_OK('Application "{0}" not found'.format(app_FN.getPath()),
                           title = 'Launcher "{0}"'.format(i_launcher['name']))
        else:
            log_debug('Application found.')
        launchers[launcherID]['application'] = i_launcher['application']
        log_debug('Imported application "{0}"'.format(i_launcher['application']))

    if i_launcher['args']:
        launchers[launcherID]['args'] = i_launcher['args']
        log_debug('Imported args "{0}"'.format(i_launcher['args']))

    # >> For every args_extra item add one entry to the list
    if i_launcher['args_extra']:
        # >> Reset current args_extra
        launchers[launcherID]['args_extra'] = []
        for args in i_launcher['args_extra']:
            launchers[launcherID]['args_extra'].append(args)
            log_debug('Imported args_extra "{0}"'.format(args))

    # >> Warn user if rompath directory does not exist
    if i_launcher['ROM_path']:
        rompath = FileName(i_launcher['ROM_path'])
        log_debug('ROMpath OP "{0}"'.format(rompath.getOriginalPath()))
        log_debug('ROMpath  P "{0}"'.format(rompath.getPath()))
        if not rompath.exists():
            log_debug('ROMpath NOT found.')
            kodi_dialog_OK('ROM path "{0}" not found'.format(rompath.getPath()),
                           title = 'Launcher "{0}"'.format(i_launcher['name']))
        else:
            log_debug('ROM_path found.')
        launchers[launcherID]['rompath'] = i_launcher['ROM_path']
        log_debug('Imported rompath "{0}"'.format(i_launcher['ROM_path']))

    if i_launcher['ROM_ext']:
        launchers[launcherID]['romext'] = i_launcher['ROM_ext']
        log_debug('Imported romext "{0}"'.format(i_launcher['ROM_ext']))

    # --- Launcher options ---
    if i_launcher['Options']:
        opt_string = unicode(i_launcher['Options']).strip()
        log_debug('Imported Options "{0}"'.format(opt_string))
        # >> Parse options
        raw_opt_list = opt_string.split(',')
        opt_list = [w.strip() for w in raw_opt_list]
        log_debug('Stripped options list {0}'.format(unicode(opt_list)))
        launcher = launchers[launcherID]
        for option in opt_list:
            if option == 'Blocking':
                launcher['non_blocking'] = False
                log_debug('Set launcher non_blocking to {0}'.format(launcher['non_blocking']))
            elif option == 'NonBlocking':
                launcher['non_blocking'] = True
                log_debug('Set launcher non_blocking to {0}'.format(launcher['non_blocking']))

            elif option == 'StaticWindow':
                launcher['minimize'] = False
                log_debug('Set launcher minimize to {0}'.format(launcher['minimize']))
            elif option == 'ToggleWindow':
                launcher['minimize'] = True
                log_debug('Set launcher minimize to {0}'.format(launcher['minimize']))

            elif option == 'Unfinished':
                launcher['finished'] = False
                log_debug('Set launcher finished to {0}'.format(launcher['finished']))
            elif option == 'Finished':
                launcher['finished'] = True
                log_debug('Set launcher finished to {0}'.format(launcher['finished']))

            else:
                kodi_dialog_OK('Unrecognised launcher <Option> "{0}"'.format(option))

    # --- ROM assets path ---
    # >> If ROM_asset_path not found warn the user and tell him if should be created or not.
    if i_launcher['ROM_asset_path']:
        launchers[launcherID]['ROM_asset_path'] = i_launcher['ROM_asset_path']
        log_debug('Imported ROM_asset_path  "{0}"'.format(i_launcher['ROM_asset_path']))
        ROM_asset_path_FN = FileName(i_launcher['ROM_asset_path'])
        log_debug('ROM_asset_path_FN OP "{0}"'.format(ROM_asset_path_FN.getOriginalPath()))
        log_debug('ROM_asset_path_FN  P "{0}"'.format(ROM_asset_path_FN.getPath()))

        # >> Warn user if ROM_asset_path_FN directory does not exist
        if not ROM_asset_path_FN.exists():
            log_debug('Not found ROM_asset_path "{0}"'.format(ROM_asset_path_FN.getPath()))
            ret = kodi_dialog_yesno('ROM asset path "{0}" not found. '.format(ROM_asset_path_FN.getPath()) +
                                    'Create it?', title = 'Launcher "{0}"'.format(i_launcher['name']))
            if ret:
                log_debug('Creating dir "{0}"'.format(ROM_asset_path_FN.getPath()))
                ROM_asset_path_FN.makedirs()
            else:
                log_debug('Do not create "{0}"'.format(ROM_asset_path_FN.getPath()))

        # >> Create asset directories if ROM path exists
        if ROM_asset_path_FN.exists():
            log_debug('ROM_asset_path path found. Creating assets subdirectories.')
            assets_init_asset_dir(ROM_asset_path_FN, launchers[launcherID])
        else:
            log_debug('ROM_asset_path path not found even after asking user to create it or not.')
            log_debug('ROM asset directories left blank or as there were.')

    # --- <path_*> tags override <ROM_asset_path> ---
    # >> This paths will be imported in a raw way, no existance checkings will be done.
    # >> Note that path_* tags will be imported only if they are non-empty.
    if i_launcher['path_title']:
        launchers[launcherID]['path_title'] = i_launcher['path_title']
        log_debug('Imported path_title "{0}"'.format(i_launcher['path_title']))

    if i_launcher['path_snap']:
        launchers[launcherID]['path_snap'] = i_launcher['path_snap']
        log_debug('Imported path_snap "{0}"'.format(i_launcher['path_snap']))

    if i_launcher['path_boxfront']:
        launchers[launcherID]['path_boxfront'] = i_launcher['path_boxfront']
        log_debug('Imported path_boxfront "{0}"'.format(i_launcher['path_boxfront']))

    if i_launcher['path_boxback']:
        launchers[launcherID]['path_boxback'] = i_launcher['path_boxback']
        log_debug('Imported path_boxback "{0}"'.format(i_launcher['path_boxback']))

    if i_launcher['path_cartridge']:
        launchers[launcherID]['path_cartridge'] = i_launcher['path_cartridge']
        log_debug('Imported path_cartridge "{0}"'.format(i_launcher['path_cartridge']))

    if i_launcher['path_fanart']:
        launchers[launcherID]['path_fanart'] = i_launcher['path_fanart']
        log_debug('Imported path_fanart "{0}"'.format(i_launcher['path_fanart']))

    if i_launcher['path_banner']:
        launchers[launcherID]['path_banner'] = i_launcher['path_banner']
        log_debug('Imported path_banner "{0}"'.format(i_launcher['path_banner']))

    if i_launcher['path_clearlogo']:
        launchers[launcherID]['path_clearlogo'] = i_launcher['path_clearlogo']
        log_debug('Imported path_clearlogo "{0}"'.format(i_launcher['path_clearlogo']))

    if i_launcher['path_flyer']:
        launchers[launcherID]['path_flyer'] = i_launcher['path_flyer']
        log_debug('Imported path_flyer "{0}"'.format(i_launcher['path_flyer']))

    if i_launcher['path_map']:
        launchers[launcherID]['path_map'] = i_launcher['path_map']
        log_debug('Imported path_map "{0}"'.format(i_launcher['path_map']))

    if i_launcher['path_manual']:
        launchers[launcherID]['path_manual'] = i_launcher['path_manual']
        log_debug('Imported path_manual "{0}"'.format(i_launcher['path_manual']))

    if i_launcher['path_trailer']:
        launchers[launcherID]['path_trailer'] = i_launcher['path_trailer']
        log_debug('Imported path_trailer "{0}"'.format(i_launcher['path_trailer']))

    # --- Launcher assets/artwork ---
    if i_launcher['Asset_Prefix']:
        launchers[launcherID]['Asset_Prefix'] = i_launcher['Asset_Prefix']
        log_debug('Imported Asset_Prefix "{0}"'.format(i_launcher['Asset_Prefix']))
    Asset_Prefix = i_launcher['Asset_Prefix']
    # >> Look at autoconfig_import_category() for a reference implementation.
    if Asset_Prefix:
        log_debug('Asset_Prefix non empty. Looking for asset files.')
        (Asset_Prefix_head, Asset_Prefix_tail) = os.path.split(Asset_Prefix)
        log_debug('Effective Asset_Prefix "{0}"'.format(Asset_Prefix))
        log_debug('Asset_Prefix_head      "{0}"'.format(Asset_Prefix_head))
        log_debug('Asset_Prefix_tail      "{0}"'.format(Asset_Prefix_tail))
        if Asset_Prefix_head:
            log_debug('Asset_Prefix head not empty')
            asset_dir_FN = FileName(import_FN.getDir()).pjoin(Asset_Prefix_head)
            norm_asset_dir_FN = FileName(os.path.normpath(asset_dir_FN.getPath()))
            effective_Asset_Prefix = Asset_Prefix_tail
        else:
            log_debug('Asset_Prefix head is empty. Assets in same dir as XML file')
            asset_dir_FN = FileName(import_FN.getDir())
            norm_asset_dir_FN = FileName(os.path.normpath(asset_dir_FN.getPath()))
            effective_Asset_Prefix = Asset_Prefix_tail
        log_debug('import_FN              "{0}"'.format(import_FN.getPath()))
        log_debug('asset_dir_FN           "{0}"'.format(asset_dir_FN.getPath()))
        log_debug('norm_asset_dir_FN      "{0}"'.format(norm_asset_dir_FN.getPath()))
        log_debug('effective_Asset_Prefix "{0}"'.format(effective_Asset_Prefix))

        # >> Get a list of all files in the directory pointed by Asset_Prefix and use this list as
        # >> a file cache. This list has filenames withouth path.
        log_debug('Scanning files in dir "{0}"'.format(norm_asset_dir_FN.getPath()))
        file_list = sorted(os.listdir(norm_asset_dir_FN.getPath()))
        log_debug('Found {0} files'.format(len(file_list)))
        # log_debug('--- File list ---')
        # for file in file_list: log_debug('--- "{0}"'.format(file))
    else:
        log_debug('Asset_Prefix empty. Not looking for any asset files.')
        norm_asset_dir_FN = None
        effective_Asset_Prefix = ''
        file_list = []

    # >> Traverse list of category assets and search for image files for each asset
    for laun_asset in LAUNCHER_ASSET_ID_LIST:
        # >> Bypass trailers now
        if laun_asset == ASSET_TRAILER_ID: continue

        # >> Look for assets
        AInfo = assets_get_info_scheme(laun_asset)
        log_debug('>> Asset "{0}"'.format(AInfo.name))
        asset_file_list = autoconfig_search_asset_file_list(effective_Asset_Prefix, AInfo, norm_asset_dir_FN, file_list)
        # --- Create image list for selection dialog ---
        listitems_list = []
        listitems_asset_paths = []
        # >> Current image if found
        current_FN = FileName(launchers[launcherID][AInfo.key])
        if current_FN.exists():
            log_debug('Current asset found "{0}"'.format(current_FN.getPath()))
            asset_listitem = xbmcgui.ListItem(label = 'Current image', label2 = current_FN.getPath())
            asset_listitem.setArt({'icon' : current_FN.getPath()})
            listitems_list.append(asset_listitem)
            listitems_asset_paths.append(current_FN.getPath())
        else:
            log_debug('Current asset NOT found "{0}"'.format(current_FN.getPath()))
        # >> Image in <s_icon>, <s_fanart>, ... tags if found
        tag_asset_FN = FileName(i_launcher[AInfo.key])
        if tag_asset_FN.exists():
            log_debug('<{0}> tag found "{1}"'.format(AInfo.key, tag_asset_FN.getPath()))
            asset_listitem = xbmcgui.ListItem(label = 'XML <{0}> image'.format(AInfo.key),
                                              label2 = tag_asset_FN.getPath())
            asset_listitem.setArt({'icon' : tag_asset_FN.getPath()})
            listitems_list.append(asset_listitem)
            listitems_asset_paths.append(tag_asset_FN.getPath())
        else:
            log_debug('<{0}> tag NOT found "{1}"'.format(AInfo.key, tag_asset_FN.getPath()))
        # >> Images found in XML configuration via <Asset_Prefix> tag
        image_count = 1
        for asset_file_name in asset_file_list:
            log_debug('Asset_Prefix found "{0}"'.format(asset_file_name))
            asset_FN = FileName(asset_file_name)
            asset_listitem = xbmcgui.ListItem(label = '<Asset_Prefix> #{0} "{1}"'.format(image_count, asset_FN.getBase()),
                                              label2 = asset_file_name)
            asset_listitem.setArt({'icon' : asset_file_name})
            listitems_list.append(asset_listitem)
            listitems_asset_paths.append(asset_FN.getPath())
            image_count += 1
        # >> If list is empty at this point no images were found at all.
        if not listitems_list:
            log_debug('listitems_list is empty. Keeping {0} as it was.'.format(AInfo.name))
            continue
        # >> No image
        asset_listitem = xbmcgui.ListItem(label = 'No image')
        asset_listitem.setArt({'icon' : 'DefaultAddonNone.png'})
        listitems_list.append(asset_listitem)
        listitems_asset_paths.append('')

        title_str = 'Launcher "{0}". Choose {1} file'.format(i_launcher['name'], AInfo.name)
        ret_idx = xbmcgui.Dialog().select(title_str, list = listitems_list, useDetails = True)
        if ret_idx < 0: return

        # >> Set asset field
        launchers[launcherID][AInfo.key] = listitems_asset_paths[ret_idx]
        log_verb('Set launcher artwork "{0}" = "{1}"'.format(AInfo.key, listitems_asset_paths[ret_idx]))

    # >> Rename ROMS JSON/XML only if there is a change in filenames.
    #    Regenerate roms_base_noext and rename old one if necessary.
    old_roms_base_noext = launchers[launcherID]['roms_base_noext']
    category_name       = categories[categoryID]['m_name'] if categoryID in categories else VCATEGORY_ADDONROOT_ID
    new_roms_base_noext = fs_get_ROMs_basename(category_name, new_launcher_name, launcherID)
    log_debug('old_roms_base_noext "{0}"'.format(old_roms_base_noext))
    log_debug('new_roms_base_noext "{0}"'.format(new_roms_base_noext))
    if old_roms_base_noext != new_roms_base_noext:
        log_debug('Renaming JSON/XML launcher databases')
        launchers[launcherID]['roms_base_noext'] = new_roms_base_noext
        fs_rename_ROMs_database(ROMS_DIR, old_roms_base_noext, new_roms_base_noext)
    else:
        log_debug('Not renaming ROM databases (old and new names are equal)')

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
# Comment may have spaces
#
def autoconfig_search_asset_file_list(asset_prefix, AInfo, norm_asset_dir_FN, file_list):
    log_debug('autoconfig_search_asset_file_list() BEGIN asset infix "{0}"'.format(AInfo.fname_infix))

    # >> Traverse list of filenames (no paths)
    filename_noext = asset_prefix + '_' + AInfo.fname_infix
    # log_debug('filename_noext "{0}"'.format(filename_noext))
    img_ext_regexp = asset_get_regexp_extension_list(IMAGE_EXTENSION_LIST)
    # log_debug('img_ext_regexp "{0}"'.format(img_ext_regexp))
    pattern = '({0})([ \w]*?)\.{1}'.format(filename_noext, img_ext_regexp)
    log_debug('autoconfig_search_asset_file_list() pattern "{0}"'.format(pattern))

    # --- Search for files in case A, B and C ---
    asset_file_list = []
    for file in file_list:
        # log_debug('Testing "{0}"'.format(file))
        m = re.match(pattern, file)
        if m:
            # log_debug('MATCH   "{0}"'.format(m.group(0)))
            asset_full_path = norm_asset_dir_FN.pjoin(file)
            # log_verb('Adding  "{0}"'.format(asset_full_path.getPath()))
            asset_file_list.append(asset_full_path.getPath())
    # log_debug('autoconfig_search_asset_file_list() END')

    return asset_file_list
