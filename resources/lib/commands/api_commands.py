# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (API actions)
##
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# Commands executed by the webservice API
#

# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import logging

from ael.utils import kodi
from ael.api import ROMObj

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import UnitOfWork, AelAddonRepository, ROMCollectionRepository, ROMsRepository
from resources.lib.domain import ROM

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# ROMCollection API commands
# -------------------------------------------------------------------------------------------------      
def cmd_set_launcher_args(args) -> bool:
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    launcher_id:str      = args['ael_addon_id'] if 'ael_addon_id' in args else None
    addon_id:str         = args['addon_id'] if 'addon_id' in args else None
    launcher_settings    = args['settings'] if 'settings' in args else None
        
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        addon_repository = AelAddonRepository(uow)
        romcollection_repository = ROMCollectionRepository(uow)
        
        addon = addon_repository.find_by_addon_id(addon_id)
        romcollection = romcollection_repository.find_romcollection(romcollection_id)
        
        if launcher_id is None:
            romcollection.add_launcher(addon, launcher_settings, True)
        else: 
            launcher = romcollection.get_launcher(launcher_id)
            launcher.set_settings(launcher_settings)
            
        romcollection_repository.update_romcollection(romcollection)
        uow.commit()
    
    kodi.notify('Configured launcher {}'.format(addon.get_name()))
    AppMediator.async_cmd('EDIT_ROMCOLLECTION', {'romcollection_id': romcollection_id})
    return True

# -------------------------------------------------------------------------------------------------
# ROMCollection scanner API commands
# -------------------------------------------------------------------------------------------------
def cmd_set_scanner_settings(args) -> bool:
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    scanner_id:str       = args['ael_addon_id'] if 'ael_addon_id' in args else None
    addon_id:str         = args['addon_id'] if 'addon_id' in args else None
    settings             = args['settings'] if 'settings' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        addon_repository = AelAddonRepository(uow)
        romcollection_repository = ROMCollectionRepository(uow)
        
        addon = addon_repository.find_by_addon_id(addon_id)
        romcollection = romcollection_repository.find_romcollection(romcollection_id)
        
        if scanner_id is None:
            romcollection.add_scanner(addon, settings)
        else: 
            scanner = romcollection.get_scanner(scanner_id)
            scanner.set_settings(settings)
            
        romcollection_repository.update_romcollection(romcollection)
        uow.commit()
    
    kodi.notify('Configured ROM scanner {}'.format(addon.get_name()))
    AppMediator.async_cmd('EDIT_ROMCOLLECTION', {'romcollection_id': romcollection_id})
    return True

def cmd_store_scanned_roms(args) -> bool:
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    scanner_id:str       = args['ael_addon_id'] if 'ael_addon_id' in args else None
    roms:list            = args['roms'] if 'roms' in args else None
    
    if roms is None:
        return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romcollection_repository = ROMCollectionRepository(uow)
        rom_repository           = ROMsRepository(uow)
        
        romcollection = romcollection_repository.find_romcollection(romcollection_id)
        existing_roms = rom_repository.find_roms_by_romcollection(romcollection_id)
        
        existing_roms_by_id = { rom.get_id(): rom for rom in existing_roms }

        for rom_data in roms:
            api_rom_obj = ROMObj(rom_data)
            rom_obj = existing_roms_by_id[api_rom_obj.get_id()]

            rom_obj.scanned_with(scanner_id)
            rom_repository.insert_rom(rom_obj)
            romcollection_repository.add_rom_to_romcollection(romcollection.get_id(), rom_obj.get_id())
        uow.commit()
    
    kodi.notify('Stored scanned ROMS in ROMs Collection {}'.format(romcollection.get_name()))
    
    AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection_id})
    AppMediator.async_cmd('RENDER_VIEW', {'category_id': romcollection.get_parent_id()})  
    AppMediator.async_cmd('EDIT_ROMCOLLECTION', {'romcollection_id': romcollection_id})