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
        repository      = AelAddonRepository(uow)     
        roms_repository = ROMsRepository(uow)   
        
        addons          = repository.find_all_scrapers()
        rom             = roms_repository.find_rom(rom_id)
        
        # --- Make a menu list of available metadata scrapers ---
        options =  {}
        for addon in addons:
            #if addon.supports_metadata()
            options[addon] = addon.get_name()
                        
        selected_addon:AelAddon = kodi.OrdDictionaryDialog().select('Scrape ROM metadata', options)
        if selected_addon is None:
            # >> Exits context menu
            logger.debug('ROM_SCRAPE_METADATA: cmd_scrape_rom_metadata() Selected None. Closing context menu')
            AppMediator.sync_cmd('ROM_EDIT_METADATA', args)
            return
    
    # >> Execute scraper
    logger.debug('ROM_SCRAPE_METADATA: cmd_scrape_rom_metadata() Selected scraper#{}'.format(selected_addon.get_name()))
       
    scraper_settings = ScraperSettings()
    #scraper_settings.metadata_scraper_ID     = selected_option
    scraper_settings.scrape_metadata_policy  = constants.SCRAPE_POLICY_SCRAPE_ONLY
    scraper_settings.search_term_mode        = constants.SCRAPE_MANUAL
    scraper_settings.game_selection_mode     = constants.SCRAPE_MANUAL
    scraper_settings.scrape_assets_policy    = constants.SCRAPE_ACTION_NONE
    
    selected_scraper = ScraperAddon(selected_addon, scraper_settings)
        
    kodi.run_script(
        selected_scraper.addon.get_addon_id(),
        selected_scraper.get_scrape_command(rom))
    
    # pdialog             = KodiProgressDialog()
    # ROM_file            = rom.get_file()
    # scraping_strategy   = g_ScraperFactory.create_scraper(launcher, pdialog, scraper_settings)
    
    # msg = 'Scraping {0}...'.format(ROM_file.getBaseNoExt())
    # pdialog.startProgress(msg)
    # log_debug(msg)  
    # try:
    #     scraping_strategy.scanner_process_ROM(rom, ROM_file)
    # except Exception as ex:
    #     log_error('(Exception) Object type "{}"'.format(type(ex)))
    #     log_error('(Exception) Message "{}"'.format(str(ex)))
    #     log_warning('Could not scrape "{}"'.format(ROM_file.getBaseNoExt()))
    #     kodi_notify_error('Could not scrape ROM')
    #     pdialog.endProgress()
    #     return
    
    # launcher.save_ROM(rom)
    # pdialog.endProgress()
    # kodi_notify('Done scraping ROM metadata')
    
    