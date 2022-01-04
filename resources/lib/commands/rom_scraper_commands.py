# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Commands (ROM scraper management)
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
import collections

from akl import constants
from akl.utils import kodi
from akl.scrapers import ScraperSettings

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import UnitOfWork, AelAddonRepository, ROMsRepository, ROMCollectionRepository
from resources.lib.domain import ROMCollection, ScraperAddon, g_assetFactory

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# Start scraping
# -------------------------------------------------------------------------------------------------
@AppMediator.register('SCRAPE_ROMS')
def cmd_scrape_romcollection(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        collection_repository = ROMCollectionRepository(uow)
        collection            = collection_repository.find_romcollection(romcollection_id)   
    
        scraper_settings:ScraperSettings = ScraperSettings.from_addon_settings()
        
        dialog_title    = f'Scrape collection "{collection.get_name()}" ROMs'
        selected_addon  = _select_scraper(uow, dialog_title, scraper_settings)
        if selected_addon is None:
            # >> Exits context menu
            logger.debug('SCRAPE_ROMS: cmd_scrape_romcollection() Selected None. Closing context menu')
            AppMediator.sync_cmd('ROMCOLLECTION_MANAGE_ROMS', args)
            return 

        scraper_settings.asset_IDs_to_scrape    = selected_addon.get_supported_assets()
        scraper_settings.metadata_IDs_to_scrape = selected_addon.get_supported_metadata()

        logger.debug(f'cmd_scrape_romcollection() Selected scraper#{selected_addon.get_name()}')
        args['scraper_settings']            = scraper_settings
        args['scraper_id']                  = selected_addon.addon.get_id()
        args['scraper_supported_metadata']  = selected_addon.get_supported_metadata()
        args['scraper_supported_assets']    = selected_addon.get_supported_assets()
        
    AppMediator.sync_cmd('SCRAPE_ROMS_WITH_SETTINGS', args)

# Scrape ROM - Select scraper to use    
@AppMediator.register('SCRAPE_ROM')
def cmd_scrape_rom(args):
    rom_id:str = args['rom_id'] if 'rom_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        roms_repository = ROMsRepository(uow)
        rom             = roms_repository.find_rom(rom_id) 
         
        scraper_settings:ScraperSettings = ScraperSettings.from_addon_settings()
        
        dialog_title    = f'Scrape ROM "{rom.get_name()}"'
        selected_addon  = _select_scraper(uow, dialog_title, scraper_settings)
        if selected_addon is None:
            # >> Exits context menu
            logger.debug('SCRAPE_ROM: cmd_scrape_rom() Selected None. Closing context menu')
            AppMediator.sync_cmd('EDIT_ROM', args)
            return 

        scraper_settings.asset_IDs_to_scrape    = selected_addon.get_supported_assets()
        scraper_settings.metadata_IDs_to_scrape = selected_addon.get_supported_metadata()

        logger.debug('cmd_scrape_rom() Selected scraper#{}'.format(selected_addon.get_name()))
        args['scraper_settings']            = scraper_settings
        args['scraper_id']                  = selected_addon.addon.get_id()
        args['scraper_supported_metadata']  = selected_addon.get_supported_metadata()
        args['scraper_supported_assets']    = selected_addon.get_supported_assets()
        
    AppMediator.sync_cmd('SCRAPE_ROM_WITH_SETTINGS', args)

@AppMediator.register('SCRAPE_ROMS_WITH_SETTINGS')
def cmd_scrape_roms_in_romcollection(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    scraper_id:str = args['scraper_id'] if 'scraper_id' in args else None
    scraper_settings:ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        addon_repository      = AelAddonRepository(uow)
        collection_repository = ROMCollectionRepository(uow)
        
        collection            = collection_repository.find_romcollection(romcollection_id)
        addon                 = addon_repository.find(scraper_id)
        selected_addon        = ScraperAddon(addon, scraper_settings)
        
        assets_to_scrape    = g_assetFactory.get_asset_list_by_IDs(scraper_settings.asset_IDs_to_scrape)
        metadata_to_scrape  = [constants.METADATA_DESCRIPTIONS[meta_id] for meta_id in scraper_settings.metadata_IDs_to_scrape]

        options = collections.OrderedDict()        
        options['SCRAPER_METADATA_POLICY']      = 'Metadata scan policy: "{}"'.format(kodi.translate(scraper_settings.scrape_metadata_policy))
        options['SCRAPER_ASSET_POLICY']         = 'Asset scan policy: "{}"'.format(kodi.translate(scraper_settings.scrape_assets_policy))
        options['SCRAPER_GAME_SELECTION_MODE']  = 'Game selection mode: "{}"'.format(kodi.translate(scraper_settings.game_selection_mode))
        options['SCRAPER_ASSET_SELECTION_MODE'] = 'Asset selection mode: "{}"'.format(kodi.translate(scraper_settings.asset_selection_mode))
        options['SCRAPER_META_TO_SCRAPE']       = 'Metadata to scrape: "{}"'.format(', '.join(metadata_to_scrape))
        options['SCRAPER_ASSETS_TO_SCRAPE']     = 'Assets to scrape: "{}"'.format(', '.join([a.plural for a in assets_to_scrape]))
        options['SCRAPER_OVERWRITE_MODE']       = 'Overwrite existing files: "{}"'.format('Yes' if scraper_settings.overwrite_existing else 'No')
        options['SCRAPER_IGNORE_TITLES_MODE']   = 'Ignore scraped titles: "{}"'.format('Yes' if scraper_settings.ignore_scrap_title else 'No')
        options['SCRAPE']                       = 'Scrape'
        
        dialog_title    = f'Scrape collection "{collection.get_name()}" ROMs with "{selected_addon.get_name()}"'
        selected_option = kodi.OrdDictionaryDialog().select(dialog_title, options, preselect='SCRAPE')
        if selected_option is None:
            logger.debug('cmd_scrape_roms_in_romcollection() Selected None. Closing context menu')
            del args['scraper_settings']
            AppMediator.sync_cmd('SCRAPE_ROMS', args)
            return
        
        if selected_option is not 'SCRAPE':
            args['ret_cmd'] = 'SCRAPE_ROMS_WITH_SETTINGS'
            AppMediator.sync_cmd(selected_option, args)
            return

        _check_collection_unset_asset_dirs(collection, scraper_settings)

    selected_addon.set_scraper_settings(scraper_settings)
    kodi.run_script(
        selected_addon.addon.get_addon_id(),
        selected_addon.get_scrape_command_for_collection(collection))

# Scrape ROM - Apply settings and run scrape action
@AppMediator.register('SCRAPE_ROM_WITH_SETTINGS')
def cmd_scrape_rom_with_settings(args):
    rom_id:str = args['rom_id'] if 'rom_id' in args else None
    scraper_id:str = args['scraper_id'] if 'scraper_id' in args else None
    scraper_settings:ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        addon_repository = AelAddonRepository(uow)
        roms_repository  = ROMsRepository(uow)
        
        rom              = roms_repository.find_rom(rom_id)   
        addon            = addon_repository.find(scraper_id)
        selected_addon   = ScraperAddon(addon, scraper_settings)
        
        assets_to_scrape    = g_assetFactory.get_asset_list_by_IDs(scraper_settings.asset_IDs_to_scrape)
        metadata_to_scrape  = [constants.METADATA_DESCRIPTIONS[meta_id] for meta_id in scraper_settings.metadata_IDs_to_scrape]

        options = collections.OrderedDict()        
        options['SCRAPER_METADATA_POLICY']      = 'Metadata scan policy: "{}"'.format(kodi.translate(scraper_settings.scrape_metadata_policy))
        options['SCRAPER_ASSET_POLICY']         = 'Asset scan policy: "{}"'.format(kodi.translate(scraper_settings.scrape_assets_policy))
        options['SCRAPER_GAME_SELECTION_MODE']  = 'Game selection mode: "{}"'.format(kodi.translate(scraper_settings.game_selection_mode))
        options['SCRAPER_ASSET_SELECTION_MODE'] = 'Asset selection mode: "{}"'.format(kodi.translate(scraper_settings.asset_selection_mode))
        options['SCRAPER_META_TO_SCRAPE']       = 'Metadata to scrape: "{}"'.format(', '.join(metadata_to_scrape))
        options['SCRAPER_ASSETS_TO_SCRAPE']     = 'Assets to scrape: "{}"'.format(', '.join([a.plural for a in assets_to_scrape]))
        options['SCRAPER_OVERWRITE_MODE']       = 'Overwrite existing files: "{}"'.format('Yes' if scraper_settings.overwrite_existing else 'No')
        options['SCRAPER_IGNORE_TITLES_MODE']   = 'Ignore scraped titles: "{}"'.format('Yes' if scraper_settings.ignore_scrap_title else 'No')
        options['SCRAPE']                       = 'Scrape'
        
        s = f'Scrape ROM "{rom.get_name()}" with "{selected_addon.get_name()}'
        selected_option = kodi.OrdDictionaryDialog().select(s, options, preselect='SCRAPE')
        if selected_option is None:
            logger.debug('cmd_scrape_rom_with_settings() Selected None. Closing context menu')
            del args['scraper_settings']
            AppMediator.sync_cmd('SCRAPE_ROM', args)
            return
        
        if selected_option != 'SCRAPE':
            args['ret_cmd'] = 'SCRAPE_ROM_WITH_SETTINGS'
            AppMediator.sync_cmd(selected_option, args)
            return

        # >> Execute scraper
        selected_addon.set_scraper_settings(scraper_settings)    
        kodi.run_script(
            selected_addon.addon.get_addon_id(),
            selected_addon.get_scrape_command(rom))

@AppMediator.register('SCRAPE_ROM_METADATA')
def cmd_scrape_rom_metadata(args):
    rom_id:str = args['rom_id'] if 'rom_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        roms_repository = ROMsRepository(uow)
        rom             = roms_repository.find_rom(rom_id)   
        
        scraper_settings = ScraperSettings().from_addon_settings()
        scraper_settings.scrape_metadata_policy  = constants.SCRAPE_POLICY_SCRAPE_ONLY
        scraper_settings.scrape_assets_policy    = constants.SCRAPE_ACTION_NONE
        scraper_settings.search_term_mode        = constants.SCRAPE_MANUAL
        scraper_settings.game_selection_mode     = constants.SCRAPE_MANUAL
        
        selected_addon = _select_scraper(uow, 'Scrape ROM metadata', scraper_settings)
        if selected_addon is None:
            # >> Exits context menu
            logger.debug('SCRAPE_ROM_METADATA: cmd_scrape_rom_metadata() Selected None. Closing context menu')
            AppMediator.sync_cmd('ROM_EDIT_METADATA', args)
            return

        logger.debug(f'SCRAPE_ROM_METADATA: cmd_scrape_rom_metadata() Selected scraper#{selected_addon.get_name()}')
        scraper_settings.metadata_IDs_to_scrape = selected_addon.get_supported_metadata()
    
        options = collections.OrderedDict()
        for metadata_id in constants.METADATA_IDS:
            if selected_addon.is_metadata_supported(metadata_id):
                options[metadata_id] = constants.METADATA_DESCRIPTIONS[metadata_id]
        
        selected_options = kodi.MultiSelectDialog().select('Metadata to scrape', options, preselected=scraper_settings.metadata_IDs_to_scrape)
            
        if selected_options is not None:
            scraper_settings.metadata_IDs_to_scrape = selected_options 

    # >> Execute scraper
    selected_addon.set_scraper_settings(scraper_settings)
    kodi.run_script(
        selected_addon.addon.get_addon_id(),
        selected_addon.get_scrape_command(rom))
    
@AppMediator.register('SCRAPE_ROM_ASSET')
def cmd_scrape_rom_asset(args):
    rom_id:str = args['rom_id'] if 'rom_id' in args else None
    asset_id:str = args['selected_asset'] if 'selected_asset' in args else None
    
    asset_to_scrape = g_assetFactory.get_asset_info(asset_id)
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        roms_repository = ROMsRepository(uow)
        rom             = roms_repository.find_rom(rom_id)   
        
        scraper_settings = ScraperSettings()
        scraper_settings.scrape_assets_policy    = constants.SCRAPE_POLICY_SCRAPE_ONLY
        scraper_settings.scrape_metadata_policy  = constants.SCRAPE_ACTION_NONE
        scraper_settings.search_term_mode        = constants.SCRAPE_MANUAL
        scraper_settings.game_selection_mode     = constants.SCRAPE_MANUAL
        scraper_settings.asset_selection_mode    = constants.SCRAPE_MANUAL
        scraper_settings.asset_IDs_to_scrape     = [asset_id]
        scraper_settings.overwrite_existing      = True
        
        selected_addon = _select_scraper(uow, 'Scrape ROM {} asset'.format(asset_to_scrape.name), scraper_settings)
        if selected_addon is None:
            # >> Exits context menu
            logger.debug('SCRAPE_ROM_ASSET: cmd_scrape_rom_asset() Selected None. Closing context menu')
            AppMediator.sync_cmd('ROM_EDIT_ASSETS', args)
            return

    # >> Execute scraper
    logger.debug('SCRAPE_ROM_ASSET: cmd_scrape_rom_asset() Selected scraper#{}'.format(selected_addon.get_name()))
    
    kodi.run_script(
        selected_addon.addon.get_addon_id(),
        selected_addon.get_scrape_command(rom))    
    
@AppMediator.register('SCRAPE_ROM_ASSETS')
def cmd_scrape_rom_assets(args):
    rom_id:str = args['rom_id'] if 'rom_id' in args else None
   
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        roms_repository = ROMsRepository(uow)
        rom             = roms_repository.find_rom(rom_id)   
    
        scraper_settings = ScraperSettings.from_addon_settings()
        scraper_settings.scrape_assets_policy    = constants.SCRAPE_POLICY_SCRAPE_ONLY
        scraper_settings.scrape_metadata_policy  = constants.SCRAPE_ACTION_NONE
        scraper_settings.search_term_mode        = constants.SCRAPE_MANUAL
        scraper_settings.asset_selection_mode    = constants.SCRAPE_MANUAL
    
        selected_addon = _select_scraper(uow, 'Scrape ROM assets', scraper_settings)
        if selected_addon is None:
            # >> Exits context menu
            logger.debug('cmd_scrape_rom_assets() Selected None. Closing context menu')
            AppMediator.sync_cmd('ROM_EDIT_ASSETS', args)
            return

        logger.debug('cmd_scrape_rom_assets() Selected scraper#{}'.format(selected_addon.get_name()))
        scraper_settings.asset_IDs_to_scrape = selected_addon.get_supported_assets()
    
        asset_options = g_assetFactory.get_all()
        options = collections.OrderedDict()
        for asset_option in asset_options:
            if selected_addon.is_asset_supported(asset_option):
                options[asset_option.id] = asset_option.name
        
        selected_options = kodi.MultiSelectDialog().select('Assets to scrape', options, preselected=scraper_settings.asset_IDs_to_scrape)
    
        if selected_options is not None:
            scraper_settings.asset_IDs_to_scrape = selected_options 

        scraper_settings.overwrite_existing = kodi.dialog_yesno('Overwrite existing assets settings?')
    
    selected_addon.set_scraper_settings(scraper_settings)
    # >> Execute scraper    
    kodi.run_script(
        selected_addon.addon.get_addon_id(),
        selected_addon.get_scrape_command(rom))

# -------------------------------------------------------------------------------------------------
# Scraper settings configuration
# -------------------------------------------------------------------------------------------------
@AppMediator.register('SCRAPER_METADATA_POLICY')
def cmd_configure_scraper_metadata_policy(args):    
    scraper_settings:ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()
    
    options = collections.OrderedDict()
    options[constants.SCRAPE_ACTION_NONE]             = kodi.translate(constants.SCRAPE_ACTION_NONE)
    options[constants.SCRAPE_POLICY_TITLE_ONLY]       = kodi.translate(constants.SCRAPE_POLICY_TITLE_ONLY)
    options[constants.SCRAPE_POLICY_LOCAL_AND_SCRAPE] = kodi.translate(constants.SCRAPE_POLICY_LOCAL_AND_SCRAPE)
    options[constants.SCRAPE_POLICY_SCRAPE_ONLY]      = kodi.translate(constants.SCRAPE_POLICY_SCRAPE_ONLY)
    
    s = 'Metadata scan policy "{}"'.format(kodi.translate(scraper_settings.scrape_metadata_policy))
    selected_option = kodi.OrdDictionaryDialog().select(s, options, preselect=scraper_settings.scrape_metadata_policy)
    
    if selected_option is None:
        AppMediator.sync_cmd(args['ret_cmd'], args)
        return
    
    scraper_settings.scrape_metadata_policy = selected_option
    args['scraper_settings'] = scraper_settings
    AppMediator.sync_cmd(args['ret_cmd'], args)
    return
    
@AppMediator.register('SCRAPER_ASSET_POLICY')
def cmd_configure_scraper_asset_policy(args):  
    scraper_settings:ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()
      
    options = collections.OrderedDict()
    options[constants.SCRAPE_ACTION_NONE]             = kodi.translate(constants.SCRAPE_ACTION_NONE)
    options[constants.SCRAPE_POLICY_LOCAL_ONLY]       = kodi.translate(constants.SCRAPE_POLICY_LOCAL_ONLY)
    options[constants.SCRAPE_POLICY_LOCAL_AND_SCRAPE] = kodi.translate(constants.SCRAPE_POLICY_LOCAL_AND_SCRAPE)
    options[constants.SCRAPE_POLICY_SCRAPE_ONLY]      = kodi.translate(constants.SCRAPE_POLICY_SCRAPE_ONLY)
    
    s = 'Asset scan policy "{}"'.format(kodi.translate(scraper_settings.scrape_assets_policy))
    selected_option = kodi.OrdDictionaryDialog().select(s, options, preselect=scraper_settings.scrape_assets_policy)
    
    if selected_option is None:
        AppMediator.sync_cmd(args['ret_cmd'], args)
        return
    
    scraper_settings.scrape_assets_policy = selected_option
    args['scraper_settings'] = scraper_settings
    AppMediator.sync_cmd(args['ret_cmd'], args)
    
@AppMediator.register('SCRAPER_GAME_SELECTION_MODE')
def cmd_configure_scraper_game_selection_mode(args):
    scraper_settings:ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()
    
    options = collections.OrderedDict()
    options[constants.SCRAPE_MANUAL]    = kodi.translate(constants.SCRAPE_MANUAL)
    options[constants.SCRAPE_AUTOMATIC] = kodi.translate(constants.SCRAPE_AUTOMATIC)
    s = 'Game selection mode "{}"'.format(kodi.translate(scraper_settings.game_selection_mode))
    selected_option = kodi.OrdDictionaryDialog().select(s, options, preselect=scraper_settings.game_selection_mode)
    
    if selected_option is None:
        AppMediator.sync_cmd(args['ret_cmd'], args)
        return
    
    scraper_settings.game_selection_mode = selected_option  
    args['scraper_settings'] = scraper_settings
    AppMediator.sync_cmd(args['ret_cmd'], args)
    return

@AppMediator.register('SCRAPER_ASSET_SELECTION_MODE')
def cmd_configure_scraper_asset_selection_mode(args):  
    scraper_settings:ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()
      
    options = collections.OrderedDict()
    options[constants.SCRAPE_MANUAL]    = kodi.translate(constants.SCRAPE_MANUAL)
    options[constants.SCRAPE_AUTOMATIC] = kodi.translate(constants.SCRAPE_AUTOMATIC)
    s = 'Game selection mode "{}"'.format(kodi.translate(scraper_settings.asset_selection_mode))
    selected_option = kodi.OrdDictionaryDialog().select(s, options, preselect=scraper_settings.asset_selection_mode)
    
    if selected_option is None:
        AppMediator.sync_cmd(args['ret_cmd'], args)
        return
    
    scraper_settings.asset_selection_mode = selected_option  
    args['scraper_settings'] = scraper_settings
    AppMediator.sync_cmd(args['ret_cmd'], args)
    return

@AppMediator.register('SCRAPER_META_TO_SCRAPE')
def cmd_configure_scraper_metadata_to_scrape(args):  
    scraper_settings:ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()
    scraper_supported_metadata:list  = args['scraper_supported_metadata'] if 'scraper_supported_metadata' in args else []

    options = collections.OrderedDict()
    for metadata_id in constants.METADATA_IDS:
        if scraper_supported_metadata is None or metadata_id in scraper_supported_metadata:
            options[metadata_id] = constants.METADATA_DESCRIPTIONS[metadata_id]
    
    selected_options = kodi.MultiSelectDialog().select('Metadata to scrape', options, preselected=scraper_settings.metadata_IDs_to_scrape)
    
    if selected_options is None:
        AppMediator.sync_cmd(args['ret_cmd'], args)
        return
    
    scraper_settings.metadata_IDs_to_scrape = selected_options  
    args['scraper_settings'] = scraper_settings
    AppMediator.sync_cmd(args['ret_cmd'], args)
    return

@AppMediator.register('SCRAPER_ASSETS_TO_SCRAPE')
def cmd_configure_scraper_assets_to_scrape(args):  
    scraper_settings:ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()
    supported_assets:list            = args['scraper_supported_assets'] if 'scraper_supported_assets' in args else []

    asset_options = g_assetFactory.get_all()
    options = collections.OrderedDict()
    for asset_option in asset_options:
        if supported_assets is None or asset_option.id in supported_assets:
            options[asset_option.id] = asset_option.name
    
    selected_options = kodi.MultiSelectDialog().select('Assets to scrape', options, preselected=scraper_settings.asset_IDs_to_scrape)
    
    if selected_options is None:
        AppMediator.sync_cmd(args['ret_cmd'], args)
        return
    
    scraper_settings.asset_IDs_to_scrape = selected_options  
    args['scraper_settings'] = scraper_settings
    AppMediator.sync_cmd(args['ret_cmd'], args)
    return

@AppMediator.register('SCRAPER_OVERWRITE_MODE')
def cmd_configure_scraper_overwrite_mode(args):  
    scraper_settings:ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()
    scraper_settings.overwrite_existing = not scraper_settings.overwrite_existing
    args['scraper_settings'] = scraper_settings
    AppMediator.sync_cmd(args['ret_cmd'], args)
    
@AppMediator.register('SCRAPER_IGNORE_TITLES_MODE')
def cmd_configure_scraper_ignore_mode(args):  
    scraper_settings:ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()
    scraper_settings.ignore_scrap_title = not scraper_settings.ignore_scrap_title
    args['scraper_settings'] = scraper_settings
    AppMediator.sync_cmd(args['ret_cmd'], args)     
    
def _select_scraper(uow:UnitOfWork, title: str, scraper_settings: ScraperSettings) -> ScraperAddon:
    selected_addon  = None    
    repository      = AelAddonRepository(uow)    
    addons          = repository.find_all_scrapers()
    
    # --- Make a menu list of available metadata scrapers ---
    options =  {}
    for addon in addons:
        scraper_addon = ScraperAddon(addon, scraper_settings)
        if scraper_addon.settings_are_applicable():
            options[scraper_addon] = addon.get_name()
                    
    selected_addon:ScraperAddon = kodi.OrdDictionaryDialog().select(title, options)
    return selected_addon

def _check_collection_unset_asset_dirs(romcollection: ROMCollection, scraper_settings:ScraperSettings) -> bool:
    logger.debug('_check_launcher_unset_asset_dirs() BEGIN ...')
    
    unconfigured_name_list = []
    enabled_asset_list = []
    for asset_id in scraper_settings.asset_IDs_to_scrape:
        rom_asset = g_assetFactory.get_asset_info(asset_id)
        asset_path = romcollection.get_asset_path(rom_asset, False)
        
        if asset_path is None:
            logger.debug('Directory not set. Asset "{}" will be disabled'.format(rom_asset))
            unconfigured_name_list.append(rom_asset.name)
        else:
            enabled_asset_list.append(rom_asset.id)
    
    scraper_settings.asset_IDs_to_scrape = enabled_asset_list
    if unconfigured_name_list:
        unconfigured_asset_srt = ', '.join(unconfigured_name_list)
        msg = 'Assets directories not set: {0}. '.format(unconfigured_asset_srt)
        msg = msg + 'Asset scanner will be disabled for this/those.'                                
        logger.debug(msg)
        kodi.dialog_OK(msg)
        return False
    return True