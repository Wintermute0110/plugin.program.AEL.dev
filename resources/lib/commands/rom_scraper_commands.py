# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (ROM scraper management)
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
import json

from ael import constants
from ael.utils import kodi
from ael.scrapers import ScraperSettings

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import UnitOfWork, AelAddonRepository, ROMsRepository
from resources.lib.domain import AelAddon, ScraperAddon, ROM

logger = logging.getLogger(__name__)

@AppMediator.register('ROM_SCRAPE_METADATA')
def cmd_scrape_rom_metadata(args):
    rom_id:str = args['rom_id'] if 'rom_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        roms_repository = ROMsRepository(uow)
        rom             = roms_repository.find_rom(rom_id)   
    
        selected_addon = _select_scraper(uow, 'Scrape ROM metadata', metadata_scrapers=True)
        if selected_addon is None:
            # >> Exits context menu
            logger.debug('ROM_SCRAPE_METADATA: cmd_scrape_rom_metadata() Selected None. Closing context menu')
            AppMediator.sync_cmd('ROM_EDIT_METADATA', args)
            return

    # >> Execute scraper
    logger.debug('ROM_SCRAPE_METADATA: cmd_scrape_rom_metadata() Selected scraper#{}'.format(selected_addon.get_name()))
       
    scraper_settings = ScraperSettings()
    scraper_settings.scrape_metadata_policy  = constants.SCRAPE_POLICY_SCRAPE_ONLY
    scraper_settings.search_term_mode        = constants.SCRAPE_MANUAL
    scraper_settings.game_selection_mode     = constants.SCRAPE_MANUAL
    scraper_settings.scrape_assets_policy    = constants.SCRAPE_ACTION_NONE
    
    selected_scraper = ScraperAddon(selected_addon, scraper_settings)
        
    kodi.run_script(
        selected_scraper.addon.get_addon_id(),
        selected_scraper.get_scrape_command(rom))
    
@AppMediator.register('RESCRAPE_ROM_ASSETS')
def cmd_scrape_rom_assets(args):
    rom_id:str = args['rom_id'] if 'rom_id' in args else None
   
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        roms_repository = ROMsRepository(uow)
        rom             = roms_repository.find_rom(rom_id)   
    
        selected_addon = _select_scraper(uow, 'Scrape ROM assets', asset_scrapers=True)
        if selected_addon is None:
            # >> Exits context menu
            logger.debug('cmd_scrape_rom_assets() Selected None. Closing context menu')
            AppMediator.sync_cmd('ROM_EDIT_ASSETS', args)
            return
    
    # >> Execute scraper
    logger.debug('cmd_scrape_rom_assets() Selected scraper#{}'.format(selected_addon.get_name()))
       
    scraper_settings = ScraperSettings()
    scraper_settings.scrape_metadata_policy  = constants.SCRAPE_POLICY_SCRAPE_ONLY
    scraper_settings.search_term_mode        = constants.SCRAPE_MANUAL
    scraper_settings.game_selection_mode     = constants.SCRAPE_MANUAL
    scraper_settings.scrape_assets_policy    = constants.SCRAPE_ACTION_NONE
    
    selected_scraper = ScraperAddon(selected_addon, scraper_settings)
        
    kodi.run_script(
        selected_scraper.addon.get_addon_id(),
        selected_scraper.get_scrape_command(rom))
        
def _select_scraper(uow:UnitOfWork, title: str, metadata_scrapers=False, asset_scrapers=False) -> AelAddon:
    selected_addon = None    
    repository  = AelAddonRepository(uow)    
    addons      = repository.find_all_scrapers()
    
    # --- Make a menu list of available metadata scrapers ---
    options =  {}
    for addon in addons:
        options[addon] = addon.get_name()
                    
    selected_addon:AelAddon = kodi.OrdDictionaryDialog().select(title, options)
    return selected_addon