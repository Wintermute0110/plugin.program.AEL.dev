# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (romcollection scanner management)
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

from ael import constants
from ael.utils import kodi, io

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import UnitOfWork, ROMCollectionRepository, ROMsRepository, AelAddonRepository
from resources.lib.domain import ROM, ROMCollectionScanner, AelAddon

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# ROM Scanners management.
# -------------------------------------------------------------------------------------------------

# --- Submenu menu command ---
@AppMediator.register('EDIT_ROMCOLLECTION_SCANNERS')
def cmd_manage_romcollection_scanners(args):
    logger.debug('EDIT_ROMCOLLECTION_SCANNERS: cmd_manage_romcollection_scanners() SHOW MENU')
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
    options = collections.OrderedDict()
    options['ADD_SCANNER']      = 'Add new scanner'
    options['EDIT_SCANNER']     = 'Edit scanner'
    options['REMOVE_SCANNER']   = 'Remove scanner'
        
    s = 'Manage ROM scanners for "{}"'.format(romcollection.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_ROMCOLLECTION_SCANNERS: cmd_manage_romcollection_scanners() Selected None. Closing context menu')
        AppMediator.async_cmd('EDIT_ROMCOLLECTION', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('EDIT_ROMCOLLECTION_SCANNERS: cmd_manage_romcollection_scanners() Selected {}'.format(selected_option))
    AppMediator.async_cmd(selected_option, args)

# --- Sub commands ---
@AppMediator.register('ADD_SCANNER')
def cmd_add_romcollection_scanner(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    options = collections.OrderedDict()
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository        = AelAddonRepository(uow)
        romcollection_repository = ROMCollectionRepository(uow)
        
        addons = repository.find_all_scanners()
        romcollection = romcollection_repository.find_romcollection(romcollection_id)
        default_launcher = romcollection.get_default_launcher()
        
        for addon in addons:
            options[addon] = addon.get_name()
    
    s = 'Choose scanner to associate'
    selected_option:AelAddon = kodi.OrdDictionaryDialog().select(s, options)
    
    if selected_option is None:
        # >> Exits context menu
        logger.debug('ADD_SCANNER: cmd_add_romcollection_scanner() Selected None. Closing context menu')
        AppMediator.async_cmd('EDIT_ROMCOLLECTION_SCANNERS', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('ADD_SCANNER: cmd_add_romcollection_scanner() Selected {}'.format(selected_option.get_id()))
    
    scanner_addon = ROMCollectionScanner(selected_option, {})
    kodi.run_script(
        selected_option.get_addon_id(), 
        scanner_addon.get_configure_command(romcollection))

@AppMediator.register('EDIT_SCANNER')
def cmd_edit_romcollection_scanners(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romcollection_repository = ROMCollectionRepository(uow)        
        romcollection = romcollection_repository.find_romcollection(romcollection_id)
        default_launcher = romcollection.get_default_launcher()
    
    scanners = romcollection.get_scanners()
    if len(scanners) == 0:
        kodi.notify('No scanners configured for this romcollection!')
        AppMediator.async_cmd('EDIT_ROMCOLLECTION_SCANNERS', args)
        return
    
    options = collections.OrderedDict()
    for scanner in scanners:
        options[scanner] = scanner.get_name()
    
    s = 'Choose scanner to edit'
    selected_option:ROMCollectionScanner = kodi.OrdDictionaryDialog().select(s, options)
    
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_SCANNER: cmd_edit_romcollection_scanners() Selected None. Closing context menu')
        AppMediator.async_cmd('EDIT_ROMCOLLECTION_SCANNERS', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('EDIT_SCANNER: cmd_edit_romcollection_scanners() Selected {}'.format(selected_option.get_id()))
    
    kodi.run_script(
        selected_option.addon.get_addon_id(),
        selected_option.get_configure_command(romcollection))  
       
@AppMediator.register('REMOVE_SCANNER')
def cmd_remove_romcollection_scanner(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romcollection_repository = ROMCollectionRepository(uow)        
        romcollection = romcollection_repository.find_romcollection(romcollection_id)
    
        scanners = romcollection.get_scanners()
        if len(scanners) == 0:
            kodi.notify('No scanners configured for this romcollection!')
            AppMediator.async_cmd('EDIT_ROMCOLLECTION_SCANNERS', args)
            return
        
        options = collections.OrderedDict()
        for scanner in scanners:
            options[scanner] = scanner.get_name()
        
        s = 'Choose scanner to remove'
        selected_option:ROMCollectionScanner = kodi.OrdDictionaryDialog().select(s, options)
        
        if selected_option is None:
            # >> Exits context menu
            logger.debug('REMOVE_SCANNER: cmd_remove_romcollection_scanner() Selected None. Closing context menu')
            AppMediator.async_cmd('EDIT_ROMCOLLECTION_SCANNERS', args)
            return
        
        # >> Execute subcommand. May be atomic, maybe a submenu.
        logger.debug('REMOVE_SCANNER: cmd_remove_romcollection_scanner() Selected {}'.format(selected_option.get_id()))
        if not kodi.dialog_yesno('Are you sure to delete ROM scanner "{}"'.format(selected_option.get_name())):
            logger.debug('REMOVE_SCANNER: cmd_remove_romcollection_scanner() Cancelled operation.')
            AppMediator.async_cmd('EDIT_ROMCOLLECTION_SCANNERS', args)
            return
        
        romcollection_repository.remove_scanner(romcollection.get_id(), selected_option.get_id())
        logger.info('REMOVE_SCANNER: cmd_remove_romcollection_scanner() Removed scanner#{}'.format(selected_option.get_id()))
        uow.commit()
    
    AppMediator.async_cmd('EDIT_ROMCOLLECTION_SCANNERS', args) 
  
# -------------------------------------------------------------------------------------------------
# ROMCollection Scanner executing
# -------------------------------------------------------------------------------------------------
@AppMediator.register('SCAN_ROMS')
def cmd_execute_rom_scanner(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romcollection_repository = ROMCollectionRepository(uow)
        romcollection = romcollection_repository.find_romcollection(romcollection_id)

    scanners = romcollection.get_scanners()
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

    kodi.run_script(
        selected_scanner.addon.get_addon_id(),
        selected_scanner.get_scan_command(romcollection))
    
@AppMediator.register('STORE_SCANNED_ROMS')
def cmd_store_scanned_roms(args):
    romcollection_id:str   = args['romcollection_id'] if 'romcollection_id' in args else None
    scanner_id:str  = args['scanner_id'] if 'scanner_id' in args else None
    roms:list       = args['roms'] if 'roms' in args else None
    
    if roms is None:
        return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romcollection_repository = ROMCollectionRepository(uow)
        rom_repository    = ROMsRepository(uow)
        
        romcollection = romcollection_repository.find_romcollection(romcollection_id)
        
        for rom_data in roms:
            rom_obj = ROM(rom_data)
            rom_obj.scanned_with(scanner_id)
            rom_repository.insert_rom(rom_obj)
            romcollection_repository.add_rom_to_romcollection(romcollection.get_id(), rom_obj.get_id())
        uow.commit()
    
    kodi.notify('Stored scanned ROMS in ROMs Collection {}'.format(romcollection.get_name()))
    
    AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection_id})
    AppMediator.async_cmd('RENDER_VIEW', {'category_id': romcollection.get_parent_id()})  
    AppMediator.async_cmd('EDIT_ROMCOLLECTION', {'romcollection_id': romcollection_id})