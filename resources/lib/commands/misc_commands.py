# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Commands (miscellaneous)
#
# Copyright (c) Wintermute0110 <wintermute0110@gmail.com> / Chrisism <crizizz@gmail.com>
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
from __future__ import division

import logging
import typing

from datetime import datetime
from xml.etree import cElementTree as ET
from xml.dom import minidom

from akl.utils import kodi, io
from akl import constants

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import UnitOfWork, AelAddonRepository, CategoryRepository, ROMCollectionRepository, XmlConfigurationRepository
from resources.lib.domain import Category, ROMCollection, AelAddon

logger = logging.getLogger(__name__)
@AppMediator.register('IMPORT_LAUNCHERS')
def cmd_execute_import_launchers(args):
    file_list = kodi.browse(text='Select XML category/launcher configuration file',mask='.xml', multiple=True)

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        addon_repository      = AelAddonRepository(uow)
        available_launchers   = [*addon_repository.find_all_launchers()]
        
        categories_repository = CategoryRepository(uow)
        existing_categories   = [*categories_repository.find_all_categories()]

        romcollections_repository    = ROMCollectionRepository(uow)
        existing_romcollections      = [*romcollections_repository.find_all_romcollections()]

        available_launcher_ids      = { a.get_addon_id() : a for a in available_launchers }
        existing_category_ids       = map(lambda c: c.get_id(), existing_categories)
        existing_romcollection_ids  = map(lambda r: r.get_id(), existing_romcollections)

        categories_to_insert:typing.List[Category]  = []
        categories_to_update:typing.List[Category]  = []
        romcollections_to_insert:typing.List[ROMCollection] = []
        romcollections_to_update:typing.List[ROMCollection] = []

        # >> Process file by file
        for xml_file in file_list:
            logger.debug(f'cmd_execute_import_launchers() Importing "{xml_file}"')
            import_FN = io.FileName(xml_file)
            if not import_FN.exists(): continue

            xml_file_repository  = XmlConfigurationRepository(import_FN)
            categories_to_import = xml_file_repository.get_categories()
            launchers_to_import  = xml_file_repository.get_launchers()

            for category_to_import in categories_to_import:
                if category_to_import.get_id() in existing_category_ids:
                     # >> Category exists (by name). Overwrite?
                    logger.debug('Category found. Edit existing category.')
                    if kodi.dialog_yesno(f'Category "{category_to_import.get_name()}" found in AKL database. Overwrite?'):
                        categories_to_update.append(category_to_import)
                else:
                    categories_to_insert.append(category_to_import)

            for launcher_to_import in launchers_to_import:
                _apply_addon_launcher_for_legacy_launcher(launcher_to_import, available_launcher_ids)                
                if launcher_to_import.get_id() in existing_romcollection_ids:
                     # >> Romset exists (by name). Overwrite?
                    logger.debug('ROMCollection found. Edit existing ROMCollection.')
                    if kodi.dialog_yesno(f'ROMCollection "{launcher_to_import.get_name()}" found in AKL database. Overwrite?'):
                        romcollections_to_update.append(launcher_to_import)
                else:
                    romcollections_to_insert.append(launcher_to_import)

        for category_to_insert in categories_to_insert:
            categories_repository.insert_category(category_to_insert)
            existing_categories.append(category_to_insert)

        for category_to_update in categories_to_update:
            categories_repository.update_category(category_to_update)
            
        for romcollection_to_insert in romcollections_to_insert:
            parent_id = romcollection_to_insert.get_custom_attribute('parent_id')
            parent_obj = next((c for c in existing_categories if c.get_id() == parent_id), None)
            romcollections_repository.insert_romcollection(romcollection_to_insert, parent_obj)
            existing_romcollections.append(romcollection_to_insert)

        for romcollection_to_update in romcollections_to_update:
            romcollections_repository.update_romcollection(romcollection_to_update)

        uow.commit()

    AppMediator.async_cmd('RENDER_VIEWS')
    kodi.notify('Finished importing Categories/Launchers')

# Export AKL launcher configuration.
# Export all Categories and Launchers.
@AppMediator.register('EXPORT_TO_LEGACY_XML')
def cmd_export_to_xml(args):
    logger.debug('_command_exec_utils_export_launchers() Exporting Category/Launcher XML configuration')

    # --- Ask path to export XML configuration ---
    dir_path = kodi.dialog_get_directory('Select XML export directory')
    if not dir_path: return

    # --- If XML exists then warn user about overwriting it ---
    export_FN = io.FileName(dir_path).pjoin('AKL_configuration.xml')
    if export_FN.exists():
        ret = kodi.dialog_yesno('AKL_configuration.xml found in the selected directory. Overwrite?')
        if not ret:
            kodi.notify_warn('Category/Launcher XML exporting cancelled')
            return

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        categories_repository     = CategoryRepository(uow)        
        romcollections_repository = ROMCollectionRepository(uow)
        
        existing_categories     = [*categories_repository.find_all_categories()]
        existing_romcollections = [*romcollections_repository.find_all_romcollections()]
    
        # --- Export stuff ---
        try:
            # --- XML header ---
            root = ET.Element('advanced_emulator_launcher_configuration')
            #comment = ET.Comment(f'<!-- Exported by AKL on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} -->')
            #root.insert(1, comment)
            # --- Export Categories ---
            # Data which is not string must be converted to string
            for category in sorted(existing_categories, key = lambda c : c.get_name()):
                logger.debug(f'cmd_export_to_xml() Category "{category.get_name()}" (ID "{category.get_id()}")')
                category_xml = ET.SubElement(root, 'category')
                ET.SubElement(category_xml,'name').text = category.get_name()
                ET.SubElement(category_xml,'year').text = category.get_releaseyear()
                ET.SubElement(category_xml,'genre').text = category.get_genre()
                ET.SubElement(category_xml,'developer').text = category.get_developer()
                ET.SubElement(category_xml,'rating').text = category.get_rating()
                ET.SubElement(category_xml,'plot').text = category.get_plot()
                ET.SubElement(category_xml,'Asset_Prefix').text = category.get_custom_attribute('Asset_Prefix')
                for asset in category.get_assets():
                    ET.SubElement(category_xml,asset.get_asset_info().key).text = asset.get_path()
            
            # --- Export Launchers and add XML tail ---
            # Data which is not string must be converted to string
            for collection in sorted(existing_romcollections, key = lambda rc : rc.get_name()):
                category_id = collection.get_parent_id()
                category = next((c for c in existing_categories if c.get_id() == category_id), None)
                if category:
                    category_name = category.get_name()
                else:
                    category_name = constants.VCATEGORY_ADDONROOT_ID

                logger.debug(f'cmd_export_to_xml() Launcher "{collection.get_name()}" (ID "{collection.get_id()}")')
                # Check if all artwork paths share the same ROM_asset_path. Unless the user has
                # customised the ROM artwork paths this should be the case.
                # A) This function checks if all path_* share a common root directory. If so
                #    this function returns that common directory as an Unicode string. In this
                #    case AKL will write the tag <ROM_asset_path> only.
                # B) If path_* do not share a common root directory this function returns '' and then
                #    AKL writes all <path_*> tags in the XML file.

                # Export Launcher
                launcher_xml = ET.SubElement(root, 'launcher')
                ET.SubElement(launcher_xml, 'name').text = collection.get_name()
                ET.SubElement(launcher_xml, 'category').text = category_name
                ET.SubElement(launcher_xml, 'year').text = collection.get_releaseyear()
                ET.SubElement(launcher_xml, 'genre').text = collection.get_genre()
                ET.SubElement(launcher_xml, 'developer').text = collection.get_developer()
                ET.SubElement(launcher_xml, 'rating').text = collection.get_rating()
                ET.SubElement(launcher_xml, 'plot').text = collection.get_plot()
                ET.SubElement(launcher_xml, 'platform').text = collection.get_platform()
                
                launcher = collection.get_default_launcher()
                if launcher:
                    for key, value in launcher.get_settings().items():
                        ET.SubElement(launcher_xml, key, value)
                
                scanners = collection.get_scanners()
                scanner_data = scanners[0].get_settings() if scanners and len(scanners) > 0 else {}
                ET.SubElement(launcher_xml, 'ROM_path').text = scanner_data['rompath'] if 'rompath' in scanner_data else ''
                ET.SubElement(launcher_xml, 'ROM_ext').text = scanner_data['romext'] if 'romext' in scanner_data else ''
                
                ET.SubElement(launcher_xml,'Asset_Prefix').text = collection.get_custom_attribute('Asset_Prefix')
                for path in collection.get_asset_paths():
                    ET.SubElement(launcher_xml, path.get_asset_info().path_key).text = path.get_path()

                for asset in collection.get_assets():
                    ET.SubElement(launcher_xml,asset.get_asset_info().key).text = asset.get_path()

            result_xml = ET.tostring(root, 'utf-8')
            parsed_xml = minidom.parseString(result_xml)
            export_FN.saveStrToFile(parsed_xml.toprettyxml(indent="  "))
        except constants.AddonError as ex:
            kodi.notify_warn('{}'.format(ex))
        else:
            kodi.notify('Exported AKL Categories and Collections to XML configuration')

@AppMediator.register('RESET_DATABASE')
def cmd_execute_reset_db(args):
    if not kodi.dialog_yesno('Are you sure you want to reset the database?'):
        return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    uow.reset_database(globals.g_PATHS.DATABASE_SCHEMA_PATH)

    AppMediator.async_cmd('CLEANUP_VIEWS')
    AppMediator.async_cmd('RENDER_VIEWS')
    AppMediator.async_cmd('SCAN_FOR_ADDONS')
    kodi.notify('Finished resetting the database')

@AppMediator.register('CHECK_DUPLICATE_ASSET_DIRS')
def cmd_check_duplicate_asset_dirs(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)

    # >> Check for duplicate paths and warn user.
    duplicated_name_list = romcollection.get_duplicated_asset_dirs()
    if duplicated_name_list:
        duplicated_asset_srt = ', '.join(duplicated_name_list)
        kodi.dialog_OK('Duplicated asset directories: {0}. '.format(duplicated_asset_srt) +
                        'AKL will refuse to add/edit ROMs if there are duplicate asset directories.')

def _apply_addon_launcher_for_legacy_launcher(collection: ROMCollection, available_addons: typing.Dict[str, AelAddon]):
    launcher_type = collection.get_custom_attribute('type')
    logger.debug(f'Migrating launcher of type "{launcher_type}" for romcollection {collection.get_name()}')
    
    if launcher_type is None:
        # 1.9x version
        launcher_addon  = available_addons['script.akl.defaults'] if 'script.akl.defaults' in available_addons else None
        if launcher_addon is None: 
            logger.warning(f'Could not find launcher addon supporting type "{launcher_type}"') 
            return
        non_blocking = collection.get_custom_attribute('non_blocking')
        settings = { 
            'application': collection.get_custom_attribute('application'), 
            'args': collection.get_custom_attribute('args')
        }
        collection.add_launcher(launcher_addon, settings, non_blocking, True)
        return
    
    if launcher_type == constants.OBJ_LAUNCHER_STANDALONE:
        launcher_addon =  available_addons['script.akl.defaults'] if 'script.akl.defaults' in available_addons else None
        if launcher_addon is None: 
            logger.warning(f'Could not find launcher addon supporting type "{launcher_type}"') 
            return
        non_blocking = collection.get_custom_attribute('non_blocking')
        settings = { 
            'application': collection.get_custom_attribute('application'), 
            'args': collection.get_custom_attribute('args')
        }
        collection.add_launcher(launcher_addon, settings, non_blocking, True)
        return
    
    if launcher_type == constants.OBJ_LAUNCHER_ROM or launcher_type == 'ROM':
        launcher_addon =  available_addons['script.akl.defaults'] if 'script.akl.defaults' in available_addons else None
        if launcher_addon is None: 
            logger.warning('Could not find launcher addon supporting type "{}"'.format(launcher_type)) 
            return
        non_blocking = collection.get_custom_attribute('non_blocking')
        settings = { 
            'application': collection.get_custom_attribute('application'), 
            'args': collection.get_custom_attribute('args')
        }
        collection.add_launcher(launcher_addon, settings, non_blocking, True)
        return
    
    if launcher_type == constants.OBJ_LAUNCHER_RETROPLAYER:
        launcher_addon =  available_addons[constants.RETROPLAYER_LAUNCHER_APP_NAME] if constants.RETROPLAYER_LAUNCHER_APP_NAME in available_addons else None
        if launcher_addon is None: 
            logger.warning(f'Could not find launcher addon supporting type "{launcher_type}"') 
            return
        non_blocking = collection.get_custom_attribute('non_blocking')
        settings = { 
            'application': collection.get_custom_attribute('application'), 
            'args': collection.get_custom_attribute('args')
        }
        collection.add_launcher(launcher_addon, settings, non_blocking, True)
        return
    
    if launcher_type == constants.OBJ_LAUNCHER_RETROARCH:
        launcher_addon =  available_addons['script.akl.retroarchlauncher'] if 'script.akl.retroarchlauncher' in available_addons else None
        if launcher_addon is None: 
            logger.warning(f'Could not find launcher addon supporting type "{launcher_type}"') 
            return
        non_blocking = collection.get_custom_attribute('non_blocking')
        settings = { 
            'application': collection.get_custom_attribute('application'), 
            'args': collection.get_custom_attribute('args'), 
            'retro_config': collection.get_custom_attribute('retro_config'), 
            'retro_core': collection.get_custom_attribute('retro_core'), 
            'retro_core_info': collection.get_custom_attribute('retro_core_info')  
        }
        collection.add_launcher(launcher_addon, settings, non_blocking, True)
        return
    
    if launcher_type == constants.OBJ_LAUNCHER_NVGAMESTREAM:
        launcher_addon =  available_addons['script.akl.nvgamestream'] if 'script.akl.nvgamestream' in available_addons else None 
        if launcher_addon is None: 
            logger.warning(f'Could not find launcher addon supporting type "{launcher_type}"') 
            return
        non_blocking = collection.get_custom_attribute('non_blocking')
        settings = { 
            'application': collection.get_custom_attribute('application'),
            'args': collection.get_custom_attribute('args'), 
            'certificates_path': collection.get_custom_attribute('certificates_path'), 
            'server': collection.get_custom_attribute('server'), 
            'server_hostname': collection.get_custom_attribute('server_hostname'), 
            'server_id': collection.get_custom_attribute('server_id'), 
            'server_uuid': collection.get_custom_attribute('server_uuid')  
        }
        collection.add_launcher(launcher_addon, settings, non_blocking, True)
        return
    
    if launcher_type == constants.OBJ_LAUNCHER_STEAM:
        launcher_addon =  available_addons['script.akl.steam'] if 'script.akl.steam' in available_addons else None  
        if launcher_addon is None: 
            logger.warning(f'Could not find launcher addon supporting type "{launcher_type}"') 
            return
        non_blocking = collection.get_custom_attribute('non_blocking')
        settings = { 
            'args': collection.get_custom_attribute('args') 
        }
        collection.add_launcher(launcher_addon, settings, non_blocking, True)