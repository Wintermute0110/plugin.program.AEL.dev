# -*- coding: utf-8 -*-

# Advanced Emulator Launcher scraping engine.
#
# --- Information about scraping ---
# https://github.com/muldjord/skyscraper
# https://github.com/muldjord/skyscraper/blob/master/docs/SCRAPINGMODULES.md

# Copyright (c) 2016-2019 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.


# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import logging
import collections

from resources.lib.utils import kodi, io, text
from resources.lib import constants, settings

logger = logging.getLogger(__name__)

class ScraperSettings(object): 
    
    def __init__(self):
        self.metadata_scraper_ID = constants.SCRAPER_NULL_ID
        self.assets_scraper_ID   = constants.SCRAPER_NULL_ID
        
        self.scrape_metadata_policy = constants.SCRAPE_POLICY_TITLE_ONLY
        self.scrape_assets_policy   = constants.SCRAPE_POLICY_LOCAL_ONLY
        
        self.search_term_mode       = constants.SCRAPE_AUTOMATIC
        self.game_selection_mode    = constants.SCRAPE_AUTOMATIC
        self.asset_selection_mode   = constants.SCRAPE_AUTOMATIC
        
        self.asset_IDs_to_scrape = constants.ROM_ASSET_ID_LIST
        self.overwrite_existing = False
        self.show_info_verbose = False
    
    def build_menu(self):
        options = collections.OrderedDict()        
        options['SC_METADATA_POLICY']      = 'Metadata scan policy: "{}"'.format(kodi.translate(self.scrape_metadata_policy))
        options['SC_ASSET_POLICY']         = 'Asset scan policy: "{}"'.format(kodi.translate(self.scrape_assets_policy))
        options['SC_GAME_SELECTION_MODE']  = 'Game selection mode: "{}"'.format(kodi.translate(self.game_selection_mode))
        options['SC_ASSET_SELECTION_MODE'] = 'Asset selection mode: "{}"'.format(kodi.translate(self.asset_selection_mode))
        options['SC_OVERWRITE_MODE']       = 'Overwrite existing files: "{}"'.format('Yes' if self.overwrite_existing else 'No')
        options['SC_METADATA_SCRAPER']     = 'Metadata scraper: "{}"'.format(kodi.translate(self.metadata_scraper_ID))
        options['SC_ASSET_SCRAPER']        = 'Asset scraper: "{}"'.format(kodi.translate(self.assets_scraper_ID))        
        return options
            
    @staticmethod
    def from_settings(settings, launcher):
        
        scraper_settings = ScraperSettings()        
        platform = launcher.get_platform()
        
        # --- Read addon settings and configure the scrapers selected -----------------------------
        if platform == 'MAME':
            logger.debug('ScraperSettings::from_settings() Platform is MAME.')
            logger.debug('Using MAME scrapers from settings.xml')
            scraper_settings.metadata_scraper_ID = settings['scraper_metadata_MAME']
            scraper_settings.assets_scraper_ID   = settings['scraper_asset_MAME']
        else:
            logger.debug('ScraperSettings.from_settings() Platform is NON-MAME.')
            logger.debug('Using standard scrapers from settings.xml')
            scraper_settings.metadata_scraper_ID = settings['scraper_metadata']
            scraper_settings.assets_scraper_ID   = settings['scraper_asset']
                
        scraper_settings.scrape_metadata_policy = settings['scan_metadata_policy']
        scraper_settings.scrape_assets_policy   = settings['scan_asset_policy']
        scraper_settings.game_selection_mode    = settings['game_selection_mode']
        scraper_settings.asset_selection_mode   = settings['asset_selection_mode']    
        
        return scraper_settings