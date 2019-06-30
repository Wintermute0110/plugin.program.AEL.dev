#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Get all ScreenScraper ROM types.
#

# --- Python standard library ---
from __future__ import unicode_literals
import os
import pprint
import sys

# --- AEL modules ---
if __name__ == "__main__" and __package__ is None:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print('Adding to sys.path {0}'.format(path))
    sys.path.append(path)
from resources.scrap import *
from resources.utils import *

# --- main ----------------------------------------------------------------------------------------
 # LOG_INFO, LOG_VERB, LOG_DEBUG
set_log_level(LOG_DEBUG)

# --- Create scraper object ---
# NEVER PUBLISH THIS INFO
settings = {
    'scraper_screenscraper_apikey' : '',
    'scraper_screenscraper_dev_id' : '',
    'scraper_screenscraper_dev_pass' : '',
    'AEL_softname' : 'AEL_0.9.8',
}
scraper_obj = ScreenScraper_V1(settings)
scraper_obj.set_verbose_mode(False)
scraper_obj.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))

# --- Get ROM types ---
online_data = scraper_obj.get_ROM_types()
online_data = scraper_obj.get_ROM_types()
pprint.pprint(online_data)
