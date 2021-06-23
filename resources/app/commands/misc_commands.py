# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (miscellaneous)
#
# Copyright (c) 2016-2018 Wintermute0110 <wintermute0110@gmail.com>
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

from resources.lib.repositories import *
from resources.app.commands.mediator import AppMediator

from resources.lib.settings import *
from resources.lib.constants import *
from resources.lib import globals
from resources.lib.utils import kodi
from resources.lib.utils import io

logger = logging.getLogger(__name__)
@AppMediator.register('IMPORT_LAUNCHERS')
def cmd_execute_import_launchers(args):
    file_list = kodi.browse(1, 'Select XML category/launcher configuration file',
                                'files', '.xml', True)

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        addon_repository      = AelAddonRepository(uow)
        available_addons      = addon_repository.find_all()
        
        categories_repository = CategoryRepository(uow)
        existing_categories   = [*categories_repository.find_all_categories()]

        romsets_repository    = ROMSetRepository(uow)
        existing_romsets      = [*romsets_repository.find_all_romsets()]

        available_addon_ids   = { a.get_addon_id() : a for a in available_addons }
        existing_category_ids = map(lambda c: c.get_id(), existing_categories)
        existing_romset_ids   = map(lambda r: r.get_id(), existing_romsets)

        categories_to_insert:typing.List[Category]  = []
        categories_to_update:typing.List[Category]  = []
        romsets_to_insert:typing.List[ROMSet]       = []
        romsets_to_update:typing.List[ROMSet]       = []

        # >> Process file by file
        for xml_file in file_list:
            logger.debug('cmd_execute_import_launchers() Importing "{0}"'.format(xml_file))
            import_FN = io.FileName(xml_file)
            if not import_FN.exists(): continue

            xml_file_repository  = XmlConfigurationRepository(import_FN)
            categories_to_import = xml_file_repository.get_categories()
            launchers_to_import  = xml_file_repository.get_launchers()

            for category_to_import in categories_to_import:
                if category_to_import.get_id() in existing_category_ids:
                     # >> Category exists (by name). Overwrite?
                    logger.debug('Category found. Edit existing category.')
                    if kodi.dialog_yesno('Category "{}" found in AEL database. Overwrite?'.format(category_to_import.get_name())):
                        categories_to_update.append(category_to_import)
                else:
                    categories_to_insert.append(category_to_import)

            for launcher_to_import in launchers_to_import:
                _apply_addon_launcher_for_legacy_launcher(launcher_to_import, available_addon_ids)                
                if launcher_to_import.get_id() in existing_romset_ids:
                     # >> Romset exists (by name). Overwrite?
                    logger.debug('ROMSet found. Edit existing ROMSet.')
                    if kodi.dialog_yesno('ROMSet "{}" found in AEL database. Overwrite?'.format(launcher_to_import.get_name())):
                        romsets_to_update.append(launcher_to_import)
                else:
                    romsets_to_insert.append(launcher_to_import)

        for category_to_insert in categories_to_insert:
            categories_repository.insert_category(category_to_insert)
            existing_categories.append(category_to_insert)

        for category_to_update in categories_to_update:
            categories_repository.update_category(category_to_update)
            
        for romset_to_insert in romsets_to_insert:
            parent_id = romset_to_insert.get_custom_attribute('parent_id')
            parent_obj = next((c for c in existing_categories if c.get_id() == parent_id), None)
            romsets_repository.insert_romset(romset_to_insert, parent_obj)
            existing_romsets.append(romset_to_insert)

        for romset_to_update in romsets_to_update:
            romsets_repository.update_romset(romset_to_update)

        uow.commit()

    kodi.event(command='RENDER_VIEWS')
    kodi.notify('Finished importing Categories/Launchers')

@AppMediator.register('RESET_DATABASE')
def cmd_execute_reset_db(args):
    if not kodi.dialog_yesno('Are you sure you want to reset the database?'):
        return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    uow.reset_database(globals.g_PATHS.DATABASE_SCHEMA_PATH)

    kodi.event(command='CLEANUP_VIEWS')
    kodi.event(command='RENDER_VIEWS')
    kodi.notify('Finished resetting the database')

@AppMediator.register('CHECK_DUPLICATE_ASSET_DIRS')
def cmd_check_duplicate_asset_dirs(args):
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)

    # >> Check for duplicate paths and warn user.
    duplicated_name_list = romset.get_duplicated_asset_dirs()
    if duplicated_name_list:
        duplicated_asset_srt = ', '.join(duplicated_name_list)
        kodi.dialog_OK('Duplicated asset directories: {0}. '.format(duplicated_asset_srt) +
                        'AEL will refuse to add/edit ROMs if there are duplicate asset directories.')

def _apply_addon_launcher_for_legacy_launcher(launcher_data: ROMSet, available_addons: typing.Dict[str, AelAddon]):
    
    launcher_type = launcher_data.get_custom_attribute('type')
    logger.debug('Migrating launcher of type "{}" for romset {}'.format(launcher_type, launcher_data.get_name()))
    
    if launcher_type is None:
        # 1.9x version
        launcher_addon  = available_addons['plugin.program.AEL.AppLauncher'] if 'plugin.program.AEL.AppLauncher' in available_addons else None
        if launcher_addon is None: 
            logger.warn('Could not find launcher supporting type "{}"'.format(launcher_type)) 
            return
        application     = launcher_data.get_custom_attribute('application')
        args            = launcher_data.get_custom_attribute('args')
        non_blocking    = launcher_data.get_custom_attribute('non_blocking')
        #'args_extra': launcher_data.get_custom_attribute('args_extra')
        settings = { 'application': application, 'args': args }
        launcher_data.add_launcher(launcher_addon, settings, non_blocking, True)
        return
    
    if launcher_type == OBJ_LAUNCHER_STANDALONE:
        launcher_addon =  available_addons['plugin.program.AEL.AppLauncher'] if 'plugin.program.AEL.AppLauncher' in available_addons else None
        if launcher_addon is None: 
            logger.warn('Could not find launcher supporting type "{}"'.format(launcher_type)) 
            return
        application     = launcher_data.get_custom_attribute('application')
        args            = launcher_data.get_custom_attribute('args')
        non_blocking    = launcher_data.get_custom_attribute('non_blocking')
        #'args_extra': launcher_data.get_custom_attribute('args_extra')
        settings = { 'application': application, 'args': args }
        launcher_data.add_launcher(launcher_addon, settings, non_blocking, True)
        return
    
    if launcher_type == OBJ_LAUNCHER_ROM:
        launcher_addon =  available_addons['plugin.program.AEL.AppLauncher'] if 'plugin.program.AEL.AppLauncher' in available_addons else None
        if launcher_addon is None: 
            logger.warn('Could not find launcher supporting type "{}"'.format(launcher_type)) 
            return
        application     = launcher_data.get_custom_attribute('application')
        args            = launcher_data.get_custom_attribute('args')
        non_blocking    = launcher_data.get_custom_attribute('non_blocking')
        #'args_extra': launcher_data.get_custom_attribute('args_extra')
        settings = { 'application': application, 'args': args }
        launcher_data.add_launcher(launcher_addon, settings, non_blocking, True)
        return
    
    if launcher_type == OBJ_LAUNCHER_RETROPLAYER:
        launcher_addon =  available_addons['plugin.program.AEL.RetroplayerLauncher'] if 'plugin.program.AEL.RetroplayerLauncher' in available_addons else None
        if launcher_addon is None: 
            logger.warn('Could not find launcher supporting type "{}"'.format(launcher_type)) 
            return
        application     = launcher_data.get_custom_attribute('application')
        args            = launcher_data.get_custom_attribute('args')
        non_blocking    = launcher_data.get_custom_attribute('non_blocking')
        #'args_extra': launcher_data.get_custom_attribute('args_extra')
        settings = { 'application': application, 'args': args }
        launcher_data.add_launcher(launcher_addon, settings, non_blocking, True)
        return
    
    if launcher_type == OBJ_LAUNCHER_RETROARCH:
        launcher_addon =  available_addons['plugin.program.AEL.RetroarchLauncher'] if 'plugin.program.AEL.RetroarchLauncher' in available_addons else None
        if launcher_addon is None: 
            logger.warn('Could not find launcher supporting type "{}"'.format(launcher_type)) 
            return
        application     = launcher_data.get_custom_attribute('application')
        args            = launcher_data.get_custom_attribute('args')
        non_blocking    = launcher_data.get_custom_attribute('non_blocking')
        #'args_extra': launcher_data.get_custom_attribute('args_extra')
        settings = { 'application': application, 'args': args }
        launcher_data.add_launcher(launcher_addon, settings, non_blocking, True)
        return
    
    if launcher_type == OBJ_LAUNCHER_NVGAMESTREAM:
        launcher_addon =  available_addons['plugin.program.AEL.GamestreamLauncher'] if 'plugin.program.AEL.GamestreamLauncher' in available_addons else None 
        if launcher_addon is None: 
            logger.warn('Could not find launcher supporting type "{}"'.format(launcher_type)) 
            return
        application     = launcher_data.get_custom_attribute('application')
        args            = launcher_data.get_custom_attribute('args')
        non_blocking    = launcher_data.get_custom_attribute('non_blocking')
        #'args_extra': launcher_data.get_custom_attribute('args_extra')
        settings = { 'application': application, 'args': args }
        launcher_data.add_launcher(launcher_addon, settings, non_blocking, True)
        return
    
    if launcher_type == OBJ_LAUNCHER_STEAM:
        launcher_addon =  available_addons['plugin.program.AEL.SteamLauncher'] if 'plugin.program.AEL.SteamLauncher' in available_addons else None  
        if launcher_addon is None: 
            logger.warn('Could not find launcher supporting type "{}"'.format(launcher_type)) 
            return
        application     = launcher_data.get_custom_attribute('application')
        args            = launcher_data.get_custom_attribute('args')
        non_blocking    = launcher_data.get_custom_attribute('non_blocking')
        #'args_extra': launcher_data.get_custom_attribute('args_extra')
        settings = { 'application': application, 'args': args }
        launcher_data.add_launcher(launcher_addon, settings, non_blocking, True)