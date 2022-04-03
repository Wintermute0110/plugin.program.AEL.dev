# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Commands (API actions)
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
from akl.scrapers import ScraperSettings

from akl.utils import kodi
from akl.api import ROMObj
from akl import constants

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
    launcher_id:str      = args['akl_addon_id'] if 'akl_addon_id' in args else None
    addon_id:str         = args['addon_id'] if 'addon_id' in args else None
    launcher_settings    = args['settings'] if 'settings' in args else None
        
    metadata_updated = False
        
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        addon_repository = AelAddonRepository(uow)
        romcollection_repository = ROMCollectionRepository(uow)
        
        addon = addon_repository.find_by_addon_id(addon_id, constants.AddonType.LAUNCHER)
        romcollection = romcollection_repository.find_romcollection(romcollection_id)
        
        if launcher_id is None:
            romcollection.add_launcher(addon, launcher_settings, True)
        else: 
            launcher = romcollection.get_launcher(launcher_id)
            launcher.set_settings(launcher_settings)
            
        if 'romcollection' in launcher_settings \
            and kodi.dialog_yesno('Do you want to overwrite collection metadata properties with values from the launcher?'):
            romcollection.import_data_dic(launcher_settings['romcollection'])
            metadata_updated = True
            
        romcollection_repository.update_romcollection(romcollection)
        uow.commit()
    
    kodi.notify('Configured launcher {}'.format(addon.get_name()))
    if metadata_updated: AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})  
    AppMediator.async_cmd('EDIT_ROMCOLLECTION', {'romcollection_id': romcollection_id})
    return True

# -------------------------------------------------------------------------------------------------
# ROMCollection scanner API commands
# -------------------------------------------------------------------------------------------------
def cmd_set_scanner_settings(args) -> bool:
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    scanner_id:str       = args['akl_addon_id'] if 'akl_addon_id' in args else None
    addon_id:str         = args['addon_id'] if 'addon_id' in args else None
    settings:dict        = args['settings'] if 'settings' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        addon_repository = AelAddonRepository(uow)
        romcollection_repository = ROMCollectionRepository(uow)
        
        addon = addon_repository.find_by_addon_id(addon_id, constants.AddonType.SCANNER)
        romcollection = romcollection_repository.find_romcollection(romcollection_id)
        
        if scanner_id is None:
            romcollection.add_scanner(addon, settings)       
        else: 
            scanner = romcollection.get_scanner(scanner_id)
            scanner.set_settings(settings)
            
        romcollection_repository.update_romcollection(romcollection)
        uow.commit()
    
    kodi.notify('Configured ROM scanner {}'.format(addon.get_name()))
    
    if kodi.dialog_yesno('Scan for ROMs now?'):
        AppMediator.async_cmd('SCAN_ROMS', {'romcollection_id': romcollection_id})
    else:
        AppMediator.async_cmd('EDIT_ROMCOLLECTION', {'romcollection_id': romcollection_id})
    return True

def cmd_store_scanned_roms(args) -> bool:
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    scanner_id:str       = args['akl_addon_id'] if 'akl_addon_id' in args else None
    new_roms:list        = args['roms'] if 'roms' in args else None
    
    if new_roms is None:
        return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romcollection_repository = ROMCollectionRepository(uow)
        rom_repository           = ROMsRepository(uow)
        
        romcollection = romcollection_repository.find_romcollection(romcollection_id)
        
        for rom_data in new_roms:
            api_rom_obj = ROMObj(rom_data)
            
            rom_obj = ROM()
            rom_obj.update_with(api_rom_obj, overwrite_existing=True, update_scanned_data=True)
            rom_obj.set_platform(romcollection.get_platform())
            rom_obj.scanned_with(scanner_id)
            rom_obj.apply_romcollection_asset_paths(romcollection)
                                    
            rom_repository.insert_rom(rom_obj)
            romcollection_repository.add_rom_to_romcollection(romcollection.get_id(), rom_obj.get_id())
        uow.commit()
    
    kodi.notify('Stored scanned ROMS in ROMs Collection {}'.format(romcollection.get_name()))
    
    AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection_id})
    AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})  
    AppMediator.async_cmd('RENDER_VCATEGORY_VIEW', {'vcategory_id': constants.VCATEGORY_TITLE_ID})
    AppMediator.async_cmd('EDIT_ROMCOLLECTION', {'romcollection_id': romcollection_id})
    return True

def cmd_remove_roms(args) -> bool:
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    scanner_id:str       = args['akl_addon_id'] if 'akl_addon_id' in args else None
    rom_ids:list         = args['rom_ids'] if 'rom_ids' in args else None
    
    if rom_ids is None:
        return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romcollection_repository = ROMCollectionRepository(uow)
        rom_repository           = ROMsRepository(uow)
        romcollection            = romcollection_repository.find_romcollection(romcollection_id)
        
        for rom_id in rom_ids:
            rom_repository.delete_rom(rom_id)
        uow.commit()
    
    kodi.notify('Removed ROMS from ROMs Collection {}'.format(romcollection.get_name()))
    
    AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection_id})
    AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})  
    AppMediator.async_cmd('RENDER_VCATEGORY_VIEWS')
    AppMediator.async_cmd('EDIT_ROMCOLLECTION', {'romcollection_id': romcollection_id})
    return True

def cmd_store_scraped_roms(args) -> bool:
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    scraper_id:str       = args['akl_addon_id'] if 'akl_addon_id' in args else None
    scraped_roms:list    = args['roms'] if 'roms' in args else None
    settings_dic:dict    = args['applied_settings'] if 'applied_settings' in args else {}
    applied_settings     = ScraperSettings.from_settings_dict(settings_dic)
    
    if scraped_roms is None:
        return
        
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romcollection_repository = ROMCollectionRepository(uow)
        rom_repository           = ROMsRepository(uow)
        
        romcollection = romcollection_repository.find_romcollection(romcollection_id)
        existing_roms = rom_repository.find_roms_by_romcollection(romcollection)
        existing_roms_by_id = { rom.get_id(): rom for rom in existing_roms }

        metadata_is_updated = applied_settings.scrape_metadata_policy != constants.SCRAPE_ACTION_NONE
        assets_are_updated  = applied_settings.scrape_assets_policy != constants.SCRAPE_ACTION_NONE

        metadata_to_update  = applied_settings.metadata_IDs_to_scrape if metadata_is_updated else []
        assets_to_update    = applied_settings.asset_IDs_to_scrape if assets_are_updated else []

        logger.debug('========================== Applied scraper settings ==========================')
        logger.debug('Metadata IDs:         {}'.format(', '.join(applied_settings.metadata_IDs_to_scrape)))
        logger.debug('Asset IDs:            {}'.format(', '.join(applied_settings.asset_IDs_to_scrape)))
        logger.debug('Overwrite existing:   {}'.format('Yes' if applied_settings.overwrite_existing else 'No'))

        for rom_data in scraped_roms:
            api_rom_obj = ROMObj(rom_data)
            
            if api_rom_obj.get_id() not in existing_roms_by_id:
                logger.warning('Scraped ROM {} with ID {} could not be found in collection#{} {}. Will be skipped.'.format(
                    api_rom_obj.get_name(), 
                    api_rom_obj.get_id(),
                    romcollection.get_id(),
                    romcollection.get_name()))
                continue
            
            rom_obj = existing_roms_by_id[api_rom_obj.get_id()]
            rom_obj.update_with(
                api_rom_obj, 
                metadata_to_update, 
                assets_to_update, 
                overwrite_existing=applied_settings.overwrite_existing)
            #rom_obj.scraped_with(scraper_id)
            
            rom_repository.update_rom(rom_obj)
        uow.commit()
    
    kodi.notify('Stored scraped ROMS in ROMs Collection {}'.format(romcollection.get_name()))
    
    AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection_id})
    if metadata_is_updated: AppMediator.async_cmd('RENDER_VCATEGORY_VIEWS')
    AppMediator.async_cmd('EDIT_ROMCOLLECTION', {'romcollection_id': romcollection_id})
    return True

def cmd_store_scraped_single_rom(args) -> bool:
    rom_id:str           = args['rom_id'] if 'rom_id' in args else None
    scraper_id:str       = args['akl_addon_id'] if 'akl_addon_id' in args else None
    scraped_rom_data:dict= args['rom'] if 'rom' in args else None
    settings_dic:dict    = args['applied_settings'] if 'applied_settings' in args else {}
    applied_settings     = ScraperSettings.from_settings_dict(settings_dic)
    
    if scraped_rom_data is None:
        return
        
    scraped_rom = ROMObj(scraped_rom_data)
    rom_collection_ids = []
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romcollection_repository = ROMCollectionRepository(uow)
        rom_repository           = ROMsRepository(uow)
        
        rom_romcollections = romcollection_repository.find_romcollections_by_rom(rom_id)
        rom_collection_ids = [collection.get_id() for collection in rom_romcollections]
        
        rom = rom_repository.find_rom(rom_id)

        metadata_is_updated = applied_settings.scrape_metadata_policy != constants.SCRAPE_ACTION_NONE
        assets_are_updated  = applied_settings.scrape_assets_policy != constants.SCRAPE_ACTION_NONE
        
        metadata_to_update = applied_settings.metadata_IDs_to_scrape if metadata_is_updated else []
        assets_to_update   = applied_settings.asset_IDs_to_scrape if assets_are_updated else []
       
        logger.debug('========================== Applied scraper settings ==========================')
        logger.debug('Metadata IDs:         {}'.format(', '.join(applied_settings.metadata_IDs_to_scrape)))
        logger.debug('Asset IDs:            {}'.format(', '.join(applied_settings.asset_IDs_to_scrape)))
        logger.debug('Overwrite existing:   {}'.format('Yes' if applied_settings.overwrite_existing else 'No'))
        logger.debug('Metadata updated:     {}'.format('Yes' if metadata_is_updated else 'No'))
        logger.debug('Assets updated:       {}'.format('Yes' if assets_are_updated else 'No'))

        rom.update_with(scraped_rom,
            metadata_to_update, 
            assets_to_update, 
            overwrite_existing=applied_settings.overwrite_existing)
        #rom_obj.scraped_with(scraper_id)
        
        rom_repository.update_rom(rom)
        uow.commit()
    
    kodi.notify('Stored scraped ROM {}'.format(rom.get_name()))
    
    for collection_id in rom_collection_ids:
        AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': collection_id})
        
    scraped_meta   = applied_settings.scrape_metadata_policy != constants.SCRAPE_ACTION_NONE
    scraped_assets = applied_settings.scrape_assets_policy != constants.SCRAPE_ACTION_NONE
    
    if metadata_is_updated: 
        AppMediator.async_cmd('RENDER_VCATEGORY_VIEWS')
    
    if scraped_meta and not scraped_assets:
        AppMediator.async_cmd('ROM_EDIT_METADATA', {'rom_id': rom_id})
    elif scraped_assets and not scraped_meta:
        if len(applied_settings.asset_IDs_to_scrape) == 1:
            AppMediator.async_cmd('ROM_EDIT_ASSETS', {'rom_id': rom_id, 'selected_asset': applied_settings.asset_IDs_to_scrape[0]})
        else:
            AppMediator.async_cmd('ROM_EDIT_ASSETS', {'rom_id': rom_id})
    else:
        AppMediator.async_cmd('EDIT_ROM', {'rom_id': rom_id})
        
    return True