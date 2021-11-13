# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (romcollection roms management)
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
import collections
import typing

from ael import constants
from ael.utils import kodi, io

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import UnitOfWork, ROMCollectionRepository, ROMsRepository, ROMsJsonFileRepository
from resources.lib.domain import ROM, AssetInfo, g_assetFactory

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# ROMCollection ROM management.
# -------------------------------------------------------------------------------------------------

# --- Submenu menu command ---
@AppMediator.register('ROMCOLLECTION_MANAGE_ROMS')
def cmd_manage_roms(args):
    logger.debug('ROMCOLLECTION_MANAGE_ROMS: cmd_manage_roms() SHOW MENU')
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    if romcollection_id is None:
        logger.warning('cmd_manage_roms(): No romcollection id supplied.')
        kodi.notify_warn("Invalid parameters supplied.")
        return
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)

    has_roms = romcollection.has_roms()

    options = collections.OrderedDict()
    options['SET_ROMS_DEFAULT_ARTWORK']  = 'Choose ROMs default artwork ...'
    options['SET_ROMS_ASSET_DIRS']       = 'Manage ROMs asset directories ...'
    
    if romcollection.has_scanners(): 
        options['SCAN_ROMS']                    = 'Scan for new ROMs'
        options['REMOVE_DEAD_ROMS']             = 'Remove dead/missing ROMs'
        options['EDIT_ROMCOLLECTION_SCANNERS']  = 'Configure ROM scanners'
    else: options['ADD_SCANNER']                = 'Add new ROM scanner' 
    
    options['IMPORT_ROMS']               = 'Import ROMs (files/metadata)'
    if has_roms:
        options['EXPORT_ROMS']           = 'Export ROMs metadata to NFO files'
        options['SCRAPE_ROMS']           = 'Scrape ROMs'
        options['DELETE_ROMS_NFO']       = 'Delete ROMs NFO files'
        options['CLEAR_ROMS']            = 'Clear ROMs from ROMCollection'

    s = 'Manage ROM Collection "{}" ROMs'.format(romcollection.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('ROMCOLLECTION_MANAGE_ROMS: cmd_manage_roms() Selected None. Closing context menu')
        if 'scraper_settings' in args: del args['scraper_settings']
        AppMediator.async_cmd('EDIT_ROMCOLLECTION', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('ROMCOLLECTION_MANAGE_ROMS: cmd_manage_roms() Selected {}'.format(selected_option))
    AppMediator.async_cmd(selected_option, args)

# --- Choose default ROMs assets/artwork ---
@AppMediator.register('SET_ROMS_DEFAULT_ARTWORK')
def cmd_set_roms_default_artwork(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    # if not launcher.supports_launching_roms():
    #     kodi.dialog_OK(
    #         'm_subcommand_set_roms_default_artwork() ' +
    #         'Launcher "{0}" is not a ROM launcher.'.format(launcher.__class__.__name__) +
    #         'This is a bug, please report it.')
    #     return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)

        # --- Build Dialog.select() list ---
        default_assets_list = romcollection.get_ROM_mappable_asset_list()
        options = collections.OrderedDict()
        for default_asset_info in default_assets_list:
            # >> Label is the string 'Choose asset for XXXX (currently YYYYY)'
            mapped_asset_key = romcollection.get_mapped_ROM_asset_key(default_asset_info)
            mapped_asset_info = g_assetFactory.get_asset_info_by_key(mapped_asset_key)
            # --- Append to list of ListItems ---
            options[default_asset_info] = 'Choose asset for {0} (currently {1})'.format(default_asset_info.name, mapped_asset_info.name)
        
        dialog = kodi.OrdDictionaryDialog()
        selected_asset_info = dialog.select('Edit ROMs default Assets/Artwork', options)
        
        if selected_asset_info is None:
            # >> Return to parent menu.
            logger.debug('cmd_set_roms_default_artwork() Main selected NONE. Returning to parent menu.')
            AppMediator.async_cmd('ROMCOLLECTION_MANAGE_ROMS', args)
            return
        
        logger.debug('cmd_set_roms_default_artwork() Main select() returned {0}'.format(selected_asset_info.name))    
        mapped_asset_key    = romcollection.get_mapped_ROM_asset_key(selected_asset_info)
        mapped_asset_info   = g_assetFactory.get_asset_info_by_key(mapped_asset_key)
        mappable_asset_list = g_assetFactory.get_asset_list_by_IDs(constants.ROM_ASSET_ID_LIST, 'image')
        logger.debug('cmd_set_roms_default_artwork() {0} currently is mapped to {1}'.format(selected_asset_info.name, mapped_asset_info.name))
            
        # --- Create ListItems ---
        options = collections.OrderedDict()
        for mappable_asset_info in mappable_asset_list:
            # >> Label is the asset name (Icon, Fanart, etc.)
            options[mappable_asset_info] = mappable_asset_info.name

        dialog = kodi.OrdDictionaryDialog()
        dialog_title_str = 'Edit {0} {1} mapped asset'.format(
            romcollection.get_object_name(), selected_asset_info.name)
        new_selected_asset_info = dialog.select(dialog_title_str, options, mapped_asset_info)
    
        if new_selected_asset_info is None:
            # >> Return to this method recursively to previous menu.
            logger.debug('cmd_set_roms_default_artwork() Mapable selected NONE. Returning to previous menu.')
            AppMediator.async_cmd('ROMCOLLECTION_MANAGE_ROMS', args)
            return   
        
        logger.debug('cmd_set_roms_default_artwork() Mapable selected {0}.'.format(new_selected_asset_info.name))
        romcollection.set_mapped_ROM_asset_key(selected_asset_info, new_selected_asset_info)
        kodi.notify('{0} {1} mapped to {2}'.format(
            romcollection.get_object_name(), selected_asset_info.name, new_selected_asset_info.name
        ))
        
        repository.update_romcollection(romcollection)
        uow.commit()
        AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
        AppMediator.async_cmd('RENDER_VIEW', {'category_id': romcollection.get_parent_id()})     

    AppMediator.async_cmd('SET_ROMS_DEFAULT_ARTWORK', {'romcollection_id': romcollection.get_id(), 'selected_asset': selected_asset_info.id})         

@AppMediator.register('SET_ROMS_ASSET_DIRS')
def cmd_set_rom_asset_dirs(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    list_items = collections.OrderedDict()
    assets = g_assetFactory.get_assets_for_type(constants.KIND_ASSET_ROM)

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
        root_path = romcollection.get_assets_root_path()
        list_items[AssetInfo()] = "Change root assets path: '{}'".format(root_path.getPath() if root_path else 'Undefined')
        for asset_info in assets:
            path = romcollection.get_asset_path(asset_info)
            if path: list_items[asset_info] = "Change {} path: '{}'".format(asset_info.plural, path.getPath())

        dialog = kodi.OrdDictionaryDialog()
        selected_asset: AssetInfo = dialog.select('ROM Asset directories ', list_items)

        if selected_asset is None:
            AppMediator.sync_cmd('ROMCOLLECTION_MANAGE_ROMS', args)
            return

        # rootpath?
        if selected_asset.id == '':
            dir_path = kodi.browse(type=0, text='Select root assets path', preselected_path=root_path.getPath() if root_path else None)
            if not dir_path or (root_path is not None and dir_path == root_path.getPath()):  
                AppMediator.sync_cmd('SET_ROMS_ASSET_DIRS', args)
                return
            
            root_path = io.FileName(dir_path)
            apply_to_all = kodi.dialog_yesno('Apply new path to all current asset paths?')
            romcollection.set_assets_root_path(root_path, constants.ROM_ASSET_ID_LIST, create_default_subdirectories=apply_to_all)            
        else:
            selected_asset_path = romcollection.get_asset_path(selected_asset)
            dir_path = kodi.browse(type=0, text='Select {} path'.format(selected_asset.plural), preselected_path=selected_asset_path.getPath())
            if not dir_path or dir_path == selected_asset_path.getPath():  
                AppMediator.sync_cmd('SET_ROMS_ASSET_DIRS', args)
                return
            romcollection.set_asset_path(selected_asset, dir_path)
            
        repository.update_romcollection(romcollection)
        uow.commit()
                
    # >> Check for duplicate paths and warn user.
    AppMediator.async_cmd('CHECK_DUPLICATE_ASSET_DIRS', args)

    kodi.notify('Changed rom asset dir for {0} to {1}'.format(selected_asset.name, dir_path))
    AppMediator.sync_cmd('SET_ROMS_ASSET_DIRS', args)
    
@AppMediator.register('IMPORT_ROMS')
def cmd_import_roms(args):
    logger.debug('IMPORT_ROMS: cmd_import_roms() SHOW MENU')
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
        
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)

    options = collections.OrderedDict()
    options['IMPORT_ROMS_NFO']      = 'Import ROMs metadata from NFO files'
    options['IMPORT_ROMS_JSON']     = 'Import ROMs data from JSON files'

    s = 'Import ROMs in ROMCollection "{}"'.format(romcollection.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('IMPORT_ROMS: cmd_import_roms() Selected None. Closing context menu')
        AppMediator.async_cmd('ROMCOLLECTION_MANAGE_ROMS', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('IMPORT_ROMS: cmd_import_roms() Selected {}'.format(selected_option))
    AppMediator.async_cmd(selected_option, args)
    
# --- Import ROM metadata from NFO files ---
@AppMediator.register('IMPORT_ROMS_NFO')
def cmd_import_roms_nfo(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
        
    # >> Load ROMs, iterate and import NFO files
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository            = ROMsRepository(uow)
        collection_repository = ROMCollectionRepository(uow)

        collection = collection_repository.find_romcollection(romcollection_id)
        roms = repository.find_roms_by_romcollection(collection)
    
        pDialog = kodi.ProgressDialog()
        pDialog.startProgress('Processing NFO files', num_steps=len(roms))
        num_read_NFO_files = 0

        step = 0
        for rom in roms:
            step = step + 1
            nfo_filepath = rom.get_nfo_file()
            pDialog.updateProgress(step)
            if rom.update_with_nfo_file(nfo_filepath, verbose = False):
                num_read_NFO_files += 1
                repository.update_rom(rom)
                
        # >> Save ROMs XML file / Launcher/timestamp saved at the end of function
        pDialog.updateProgress(len(roms), 'Saving ROM JSON database ...')
        uow.commit()
        pDialog.close()
        
    kodi.notify('Imported {0} NFO files'.format(num_read_NFO_files))
    AppMediator.async_cmd('IMPORT_ROMS', args)
    
# --- Import ROM metadata from json config file ---
@AppMediator.register('IMPORT_ROMS_JSON')
def cmd_import_roms_json(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    file_list = kodi.browse(text='Select ROMs JSON file',mask='.json',multiple=True)

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository        = ROMsRepository(uow)
        romcollection_repository = ROMCollectionRepository(uow) 
        
        romcollection       = romcollection_repository.find_romcollection(romcollection_id)
        existing_roms       = [*repository.find_roms_by_romcollection(romcollection)]
        existing_rom_ids    = map(lambda r: r.get_id(), existing_roms)
        existing_rom_names  = map(lambda r: r.get_name(), existing_roms)

        roms_to_insert:typing.List[ROM]  = []
        roms_to_update:typing.List[ROM]  = []

        # >> Process file by file
        for json_file in file_list:
            logger.debug('cmd_import_roms_json() Importing "{0}"'.format(json_file))
            import_FN = io.FileName(json_file)
            if not import_FN.exists(): continue

            json_file_repository  = ROMsJsonFileRepository(import_FN)
            imported_roms = json_file_repository.load_ROMs()
            logger.debug("cmd_import_roms_json() Loaded {} roms".format(len(imported_roms)))
    
            for imported_rom in imported_roms:
                if imported_rom.get_id() in existing_rom_ids:
                     # >> ROM exists (by id). Overwrite?
                    logger.debug('ROM found. Edit existing category.')
                    if kodi.dialog_yesno('ROM "{}" found in AEL database. Overwrite?'.format(imported_rom.get_name())):
                        roms_to_update.append(imported_rom)
                elif imported_rom.get_name() in existing_rom_names:
                     # >> ROM exists (by name). Overwrite?
                    logger.debug('ROM found. Edit existing category.')
                    if kodi.dialog_yesno('ROM "{}" found in AEL database. Overwrite?'.format(imported_rom.get_name())):
                        roms_to_update.append(imported_rom)
                else:
                    logger.debug('Add new ROM {}'.format(imported_rom.get_name()))
                    imported_rom.set_platform(romcollection.get_platform())
                    roms_to_insert.append(imported_rom)
                        
        for rom_to_insert in roms_to_insert:
            repository.insert_rom(rom_to_insert)
            romcollection_repository.add_rom_to_romcollection(romcollection.get_id(), rom_to_insert.get_id())

        for rom_to_update in roms_to_update:
            repository.update_rom(rom_to_update)
            
        uow.commit()

    AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection_id})
    AppMediator.async_cmd('RENDER_VIEW', {'category_id': romcollection.get_parent_id()})  
    kodi.notify('Finished importing ROMS')

# --- Empty Launcher ROMs ---
@AppMediator.register('CLEAR_ROMS')
def cmd_clear_roms(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        collection_repository   = ROMCollectionRepository(uow)
        roms_repository         = ROMsRepository(uow)
        
        romcollection = collection_repository.find_romcollection(romcollection_id)
        roms          = roms_repository.find_roms_by_romcollection(romcollection)
        
        # If collection is empty (no ROMs) do nothing
        num_roms = len([*roms])
        if num_roms == 0:
            kodi.dialog_OK('Collection has no ROMs. Nothing to do.')
            return

        # Confirm user wants to delete ROMs    
        ret = kodi.dialog_yesno("Collection '{0}' has {1} ROMs. Are you sure you want to clear them "
                                "from this collection?".format(romcollection.get_name(), num_roms))
        if not ret: return

        # --- If there is a No-Intro XML DAT configured remove it ---
        # TODO fix
        # romcollection.reset_nointro_xmldata()

        # Confirm if the user wants to remove the ROMs also when linked to other collections.
        delete_completely = kodi.dialog_yesno("Delete the ROMs completely from the AEL database and not collection only?")
        if not delete_completely: 
            collection_repository.remove_all_roms_in_launcher(romcollection_id)
        else:
            roms_repository.delete_roms_by_romcollection(romcollection_id)        
        uow.commit()
        
    AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection_id})
    AppMediator.async_cmd('RENDER_VIEW', {'category_id': romcollection.get_parent_id()})  
    kodi.notify('Cleared ROMs from collection')
