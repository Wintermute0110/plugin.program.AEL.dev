# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (romset roms management)
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

from resources.app.commands.mediator import AppMediator
from resources.app import globals
from resources.app.repositories import UnitOfWork, ROMSetRepository, ROMsRepository, ROMsJsonFileRepository
from resources.app.domain import ROM, AssetInfo, g_assetFactory

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# ROMSet ROM management.
# -------------------------------------------------------------------------------------------------

# --- Submenu menu command ---
@AppMediator.register('ROMSET_MANAGE_ROMS')
def cmd_manage_roms(args):
    logger.debug('ROMSET_MANAGE_ROMS: cmd_manage_roms() SHOW MENU')
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    
    if romset_id is None:
        logger.warn('cmd_manage_roms(): No romset id supplied.')
        kodi.notify_warn("Invalid parameters supplied.")
        return
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)

    options = collections.OrderedDict()
    options['SET_ROMS_DEFAULT_ARTWORK']  = 'Choose ROMs default artwork ...'
    options['SET_ROMS_ASSET_DIRS']       = 'Manage ROMs asset directories ...'
    if romset.has_scanners(): 
        options['SCAN_ROMS']             = 'Scan for new ROMs'
        options['EDIT_ROMSET_SCANNERS']  = 'Configure ROM scanners'
    else: options['ADD_SCANNER']         = 'Add new ROM scanner' 
    options['IMPORT_ROMS']               = 'Import ROMs (files/metadata)'
    options['EXPORT_ROMS']               = 'Export ROMs metadata to NFO files'
    options['SCRAPE_ROMS']               = 'Scrape ROMs'
    options['REMOVE_DEAD_ROMS']          = 'Remove dead/missing ROMs'
    options['DELETE_ROMS_NFO']           = 'Delete ROMs NFO files'
    options['CLEAR_ROMS']                = 'Clear ROMs from ROMSet'

    s = 'Manage ROM Collection "{}" ROMs'.format(romset.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('ROMSET_MANAGE_ROMS: cmd_manage_roms() Selected None. Closing context menu')
        kodi.event(command='EDIT_ROMSET', data=args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('ROMSET_MANAGE_ROMS: cmd_manage_roms() Selected {}'.format(selected_option))
    kodi.event(command=selected_option, data=args)

# --- Choose default ROMs assets/artwork ---
@AppMediator.register('SET_ROMS_DEFAULT_ARTWORK')
def cmd_set_roms_default_artwork(args):
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    
    # if not launcher.supports_launching_roms():
    #     kodi.dialog_OK(
    #         'm_subcommand_set_roms_default_artwork() ' +
    #         'Launcher "{0}" is not a ROM launcher.'.format(launcher.__class__.__name__) +
    #         'This is a bug, please report it.')
    #     return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)

        # --- Build Dialog.select() list ---
        default_assets_list = romset.get_ROM_mappable_asset_list()
        options = collections.OrderedDict()
        for default_asset_info in default_assets_list:
            # >> Label is the string 'Choose asset for XXXX (currently YYYYY)'
            mapped_asset_key = romset.get_mapped_ROM_asset_key(default_asset_info)
            mapped_asset_info = g_assetFactory.get_asset_info_by_key(mapped_asset_key)
            # --- Append to list of ListItems ---
            options[default_asset_info] = 'Choose asset for {0} (currently {1})'.format(default_asset_info.name, mapped_asset_info.name)
        
        dialog = kodi.OrdDictionaryDialog()
        selected_asset_info = dialog.select('Edit ROMs default Assets/Artwork', options)
        
        if selected_asset_info is None:
            # >> Return to parent menu.
            logger.debug('cmd_set_roms_default_artwork() Main selected NONE. Returning to parent menu.')
            kodi.event(command='ROMSET_MANAGE_ROMS', data=args)
            return
        
        logger.debug('cmd_set_roms_default_artwork() Main select() returned {0}'.format(selected_asset_info.name))    
        mapped_asset_key    = romset.get_mapped_ROM_asset_key(selected_asset_info)
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
            romset.get_object_name(), selected_asset_info.name)
        new_selected_asset_info = dialog.select(dialog_title_str, options, mapped_asset_info)
    
        if new_selected_asset_info is None:
            # >> Return to this method recursively to previous menu.
            logger.debug('cmd_set_roms_default_artwork() Mapable selected NONE. Returning to previous menu.')
            kodi.event(command='ROMSET_MANAGE_ROMS', data=args)
            return   
        
        logger.debug('cmd_set_roms_default_artwork() Mapable selected {0}.'.format(new_selected_asset_info.name))
        romset.set_mapped_ROM_asset_key(selected_asset_info, new_selected_asset_info)
        kodi.notify('{0} {1} mapped to {2}'.format(
            romset.get_object_name(), selected_asset_info.name, new_selected_asset_info.name
        ))
        
        repository.update_romset(romset)
        uow.commit()
        kodi.event(command='RENDER_ROMSET_VIEW', data={'romset_id': romset.get_id()})
        kodi.event(command='RENDER_VIEW', data={'category_id': romset.get_parent_id()})     

    kodi.event(command='SET_ROMS_DEFAULT_ARTWORK', data={'romset_id': romset.get_id(), 'selected_asset': selected_asset_info.id})         

@AppMediator.register('SET_ROMS_ASSET_DIRS')
def cmd_set_rom_asset_dirs(args):
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    
    list_items = {}
    assets = g_assetFactory.get_all()

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)

        # --- Scrape ROMs artwork ---
        # >> Mimic what the ROM scanner does. Use same settings as the ROM scanner.
        # >> Like the ROM scanner, only scrape artwork not found locally.
        # elif type2 == 3:
        #     kodi_dialog_OK('WIP feature not coded yet, sorry.')
        #     return

        for asset_info in assets:
            path = romset.get_asset_path(asset_info)
            if path:
                list_items[asset_info] = "Change {0} path: '{1}'".format(asset_info.plural, path.getPath())

        dialog = kodi.OrdDictionaryDialog()
        selected_asset: AssetInfo = dialog.select('ROM Asset directories ', list_items)

        if selected_asset is None:
            kodi.event(command='ROMSET_MANAGE_ROMS', data=args)
            return

        selected_asset_path = romset.get_asset_path(selected_asset)
        dir_path = kodi.browse(0, 'Select {} path'.format(selected_asset.plural), 'files', '', False, False, selected_asset_path.getPath()).decode('utf-8')
        if not dir_path or dir_path == selected_asset_path.getPath():  
            kodi.event(command='SET_ROMS_ASSET_DIRS', data=args)
            return
                
        romset.set_asset_path(selected_asset, dir_path)
        repository.update_romset(romset)
        uow.commit()
                
    # >> Check for duplicate paths and warn user.
    kodi.event(command='CHECK_DUPLICATE_ASSET_DIRS', data=args)

    kodi.notify('Changed rom asset dir for {0} to {1}'.format(selected_asset.name, dir_path))
    kodi.event(command='SET_ROMS_ASSET_DIRS', data=args)
    
@AppMediator.register('IMPORT_ROMS')
def cmd_import_roms(args):
    logger.debug('IMPORT_ROMS: cmd_import_roms() SHOW MENU')
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
        
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)

    options = collections.OrderedDict()
    options['IMPORT_ROMS_NFO']      = 'Import ROMs metadata from NFO files'
    options['IMPORT_ROMS_JSON']     = 'Import ROMs data from JSON files'

    s = 'Import ROMs in ROMSet "{}"'.format(romset.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('IMPORT_ROMS: cmd_import_roms() Selected None. Closing context menu')
        kodi.event(command='ROMSET_MANAGE_ROMS', data=args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('IMPORT_ROMS: cmd_import_roms() Selected {}'.format(selected_option))
    kodi.event(command=selected_option, data=args)
    
# --- Import ROM metadata from NFO files ---
@AppMediator.register('IMPORT_ROMS_NFO')
def cmd_import_roms_nfo(args):
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
        
    # >> Load ROMs, iterate and import NFO files
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        roms = repository.find_roms_by_romset(romset_id)
    
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
    kodi.event(command='IMPORT_ROMS', data=args)
    
# --- Import ROM metadata from json config file ---
@AppMediator.register('IMPORT_ROMS_JSON')
def cmd_import_roms_json(args):
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    file_list = kodi.browse(1, 'Select ROMs JSON file', 'files', '.json', True)

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository        = ROMsRepository(uow)
        romset_repository = ROMSetRepository(uow) 
        
        romset              = romset_repository.find_romset(romset_id)
        existing_roms       = [*repository.find_roms_by_romset(romset_id)]
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
                    logger.debug('')
                    roms_to_insert.append(imported_rom)
                        
        for rom_to_insert in roms_to_insert:
            repository.insert_rom(rom_to_insert, romset)
            romset_repository.add_rom_to_romset(romset.get_id(), rom_to_insert.get_id())

        for rom_to_update in roms_to_update:
            repository.update_rom(rom_to_update)
            
        uow.commit()

    kodi.event(command='RENDER_ROMSET_VIEW', data={'romset_id': romset_id})
    kodi.event(command='RENDER_VIEW', data={'category_id': romset.get_parent_id()})  
    kodi.notify('Finished importing ROMS')
