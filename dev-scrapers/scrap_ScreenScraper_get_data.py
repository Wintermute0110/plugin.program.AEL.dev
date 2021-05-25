#!/usr/bin/python -B
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
scraper_obj = ScreenScraper()
scraper_obj.set_verbose_mode(False)
scraper_obj.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))
status_dic = kodi_new_status_dic('Scraper test was OK')

# --- Get ROM types ---
online_data = scraper_obj.debug_get_user_info(dict.copy(status_dic))
# userlevelsListe.php fails because invalid JSON returned. It's not prioritary at all, however.
# online_data = scraper_obj.debug_get_user_levels(dict.copy(status_dic))
online_data = scraper_obj.debug_get_support_types(dict.copy(status_dic))
online_data = scraper_obj.debug_get_ROM_types(dict.copy(status_dic))
online_data = scraper_obj.debug_get_genres(dict.copy(status_dic))
online_data = scraper_obj.debug_get_regions(dict.copy(status_dic))
online_data = scraper_obj.debug_get_languages(dict.copy(status_dic))
online_data = scraper_obj.debug_get_clasifications(dict.copy(status_dic))
online_data = scraper_obj.debug_get_platforms(dict.copy(status_dic))
# pprint.pprint(online_data)
