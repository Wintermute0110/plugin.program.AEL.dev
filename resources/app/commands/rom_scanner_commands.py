# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (romset scanner management)
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

from ael.utils import kodi

from resources.app.commands.mediator import AppMediator
from resources.app import globals
from resources.app.repositories import UnitOfWork, ROMSetRepository, ROMsRepository, AelAddonRepository
from resources.app.domain import ROM, ROMSetScanner, AelAddon

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# ROM Scanners management.
# -------------------------------------------------------------------------------------------------

# --- Submenu menu command ---
@AppMediator.register('EDIT_ROMSET_SCANNERS')
def cmd_manage_romset_scanners(args):
    logger.debug('EDIT_ROMSET_SCANNERS: cmd_manage_romset_scanners() SHOW MENU')
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)
        
    options = collections.OrderedDict()
    options['ADD_SCANNER']      = 'Add new scanner'
    options['EDIT_SCANNER']     = 'Edit scanner'
    options['REMOVE_SCANNER']   = 'Remove scanner'
        
    s = 'Manage ROM scanners for "{}"'.format(romset.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_ROMSET_SCANNERS: cmd_manage_romset_scanners() Selected None. Closing context menu')
        AppMediator.async_cmd('EDIT_ROMSET', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('EDIT_ROMSET_SCANNERS: cmd_manage_romset_scanners() Selected {}'.format(selected_option))
    AppMediator.async_cmd(selected_option, args)

# --- Sub commands ---
@AppMediator.register('ADD_SCANNER')
def cmd_add_romset_scanner(args):
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    
    options = collections.OrderedDict()
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository        = AelAddonRepository(uow)
        romset_repository = ROMSetRepository(uow)
        
        addons = repository.find_all_scanners()
        romset = romset_repository.find_romset(romset_id)
        default_launcher = romset.get_default_launcher()
        
        for addon in addons:
            options[addon] = addon.get_name()
    
    s = 'Choose scanner to associate'
    selected_option:AelAddon = kodi.OrdDictionaryDialog().select(s, options)
    
    if selected_option is None:
        # >> Exits context menu
        logger.debug('ADD_SCANNER: cmd_add_romset_scanner() Selected None. Closing context menu')
        AppMediator.async_cmd('EDIT_ROMSET_SCANNERS', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('ADD_SCANNER: cmd_add_romset_scanner() Selected {}'.format(selected_option.get_id()))
    
    args = {}
    args['romset_id'] = romset_id
    if default_launcher: args['launcher'] = default_launcher.get_settings_str()
    
    kodi.execute_uri(selected_option.get_configure_uri(), args)  

@AppMediator.register('EDIT_SCANNER')
def cmd_edit_romset_scanners(args):
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romset_repository = ROMSetRepository(uow)        
        romset = romset_repository.find_romset(romset_id)
        default_launcher = romset.get_default_launcher()
    
    scanners = romset.get_scanners()
    if len(scanners) == 0:
        kodi.notify('No scanners configured for this romset!')
        AppMediator.async_cmd('EDIT_ROMSET_SCANNERS', args)
        return
    
    options = collections.OrderedDict()
    for scanner in scanners:
        options[scanner] = scanner.get_name()
    
    s = 'Choose scanner to edit'
    selected_option:ROMSetScanner = kodi.OrdDictionaryDialog().select(s, options)
    
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_SCANNER: cmd_edit_romset_scanners() Selected None. Closing context menu')
        AppMediator.async_cmd('EDIT_ROMSET_SCANNERS', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('EDIT_SCANNER: cmd_edit_romset_scanners() Selected {}'.format(selected_option.get_id()))
    
    args = {}
    args['romset_id'] = romset_id
    args['scanner_id'] = selected_option.get_id()
    args['settings'] = selected_option.get_settings_str()
    if default_launcher: args['launcher'] = default_launcher.get_settings_str()
    
    kodi.execute_uri(selected_option.addon.get_configure_uri(), args)
       
@AppMediator.register('REMOVE_SCANNER')
def cmd_remove_romset_scanner(args):
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romset_repository = ROMSetRepository(uow)        
        romset = romset_repository.find_romset(romset_id)
    
        scanners = romset.get_scanners()
        if len(scanners) == 0:
            kodi.notify('No scanners configured for this romset!')
            AppMediator.async_cmd('EDIT_ROMSET_SCANNERS', args)
            return
        
        options = collections.OrderedDict()
        for scanner in scanners:
            options[scanner] = scanner.get_name()
        
        s = 'Choose scanner to remove'
        selected_option:ROMSetScanner = kodi.OrdDictionaryDialog().select(s, options)
        
        if selected_option is None:
            # >> Exits context menu
            logger.debug('REMOVE_SCANNER: cmd_remove_romset_scanner() Selected None. Closing context menu')
            AppMediator.async_cmd('EDIT_ROMSET_SCANNERS', args)
            return
        
        # >> Execute subcommand. May be atomic, maybe a submenu.
        logger.debug('REMOVE_SCANNER: cmd_remove_romset_scanner() Selected {}'.format(selected_option.get_id()))
        if not kodi.dialog_yesno('Are you sure to delete ROM scanner "{}"'.format(selected_option.get_name())):
            logger.debug('REMOVE_SCANNER: cmd_remove_romset_scanner() Cancelled operation.')
            AppMediator.async_cmd('EDIT_ROMSET_SCANNERS', args)
            return
        
        romset_repository.remove_scanner(romset.get_id(), selected_option.get_id())
        logger.info('REMOVE_SCANNER: cmd_remove_romset_scanner() Removed scanner#{}'.format(selected_option.get_id()))
        uow.commit()
    
    AppMediator.async_cmd('EDIT_ROMSET_SCANNERS', args) 
  
# -------------------------------------------------------------------------------------------------
# ROMSet scanner specific configuration.
# -------------------------------------------------------------------------------------------------      
@AppMediator.register('SET_SCANNER_SETTINGS')
def cmd_set_scanner_settings(args):
    romset_id:str   = args['romset_id'] if 'romset_id' in args else None
    scanner_id:str  = args['scanner_id'] if 'scanner_id' in args else None
    addon_id:str    = args['addon_id'] if 'addon_id' in args else None
    settings        = args['settings'] if 'settings' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        addon_repository = AelAddonRepository(uow)
        romset_repository = ROMSetRepository(uow)
        
        addon = addon_repository.find_by_addon_id(addon_id)
        romset = romset_repository.find_romset(romset_id)
        
        if scanner_id is None:
            romset.add_scanner(addon, settings)
        else: 
            scanner = romset.get_scanner(scanner_id)
            scanner.set_settings(settings)
            
        romset_repository.update_romset(romset)
        uow.commit()
    
    kodi.notify('Configured ROM scanner {}'.format(addon.get_name()))
    AppMediator.async_cmd('EDIT_ROMSET', {'romset_id': romset_id})
 
# -------------------------------------------------------------------------------------------------
# ROMSet Scanner executing
# -------------------------------------------------------------------------------------------------
@AppMediator.register('SCAN_ROMS')
def cmd_execute_rom_scanner(args):
    romset_id:str = args['romset_id'] if 'romset_id' in args else None

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romset_repository = ROMSetRepository(uow)
        romset = romset_repository.find_romset(romset_id)

    scanners = romset.get_scanners()
    if scanners is None or len(scanners) == 0:
        kodi.notify_warn('No ROM scanners configured.')
        return

    selected_scanner = scanners[0]
    if len(scanners) > 1:
        scanner_options = collections.OrderedDict()
        for scanner in scanners:
            scanner_options[scanner] = scanner.get_name()
        dialog = kodi.OrdDictionaryDialog()
        selected_scanner = dialog.select('Choose ROM scanner', scanner_options)

    logger.info('SCAN_ROMS: selected scanner "{}"'.format(selected_scanner.get_name()))

    kodi.execute_uri(selected_scanner.addon.get_execute_uri(), {
        'romset_id': romset.get_id(),
        'scanner_id': selected_scanner.get_id(),
        'settings': selected_scanner.get_settings_str()
    })
    
@AppMediator.register('STORE_SCANNED_ROMS')
def cmd_store_scanned_roms(args):
    romset_id:str   = args['romset_id'] if 'romset_id' in args else None
    scanner_id:str  = args['scanner_id'] if 'scanner_id' in args else None
    roms:list       = args['roms'] if 'roms' in args else None
    
    if roms is None:
        return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romset_repository = ROMSetRepository(uow)
        rom_repository    = ROMsRepository(uow)
        
        romset = romset_repository.find_romset(romset_id)
        
        for rom_data in roms:
            rom_obj = ROM(rom_data)
            rom_obj.scanned_with(scanner_id)
            rom_repository.insert_rom(rom_obj)
            romset_repository.add_rom_to_romset(romset.get_id(), rom_obj.get_id())
        uow.commit()
    
    kodi.notify('Stored scanned ROMS in ROMs Collection {}'.format(romset.get_name()))
    
    AppMediator.async_cmd('RENDER_ROMSET_VIEW', {'romset_id': romset_id})
    AppMediator.async_cmd('RENDER_VIEW', {'category_id': romset.get_parent_id()})  
    AppMediator.async_cmd('EDIT_ROMSET', {'romset_id': romset_id})