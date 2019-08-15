#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# Plumbing command to retrieve data from ScreenScraper.
# Data in JSON format will be saved in ./assets/ subdirectory.
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
import common

# --- main ----------------------------------------------------------------------------------------
set_log_level(LOG_DEBUG)

# --- Create scraper object ---
scraper_obj = ScreenScraper_V1(common.settings)
scraper_obj.set_verbose_mode(False)
scraper_obj.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))
status_dic = kodi_new_status_dic('Scraper test was OK')

# --- Get ROM types ---
online_data = scraper_obj.get_user_info(status_dic) # Not working at the moment.
# online_data = scraper_obj.get_ROM_types(status_dic) # Not working at the moment.
# online_data = scraper_obj.get_genres_list(status_dic) # Works OK.
# online_data = scraper_obj.get_regions_list(status_dic) # Works OK.
pprint.pprint(online_data)
