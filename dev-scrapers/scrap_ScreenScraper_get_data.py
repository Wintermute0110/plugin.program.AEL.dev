#!/usr/bin/python3 -B
# -*- coding: utf-8 -*-

# Plumbing command to retrieve data from ScreenScraper.
# Data in JSON format will be saved in ./assets/ subdirectory.

# --- Import AEL modules ---
import os
import sys
if __name__ == "__main__" and __package__ is None:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print('Adding to sys.path {}'.format(path))
    sys.path.append(path)
from resources.utils import *
from resources.scrap import *
import common

# --- Python standard library ---
import pprint

# --- main ----------------------------------------------------------------------------------------
set_log_level(LOG_DEBUG)

# --- Create scraper object ---
scraper_obj = ScreenScraper(common.settings)
scraper_obj.set_verbose_mode(False)
scraper_obj.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))
st_dic = kodi_new_status_dic()

# --- Get ROM types ---
online_data = scraper_obj.debug_get_user_info(dict.copy(st_dic))
# userlevelsListe.php fails because invalid JSON returned. It's not prioritary at all, however.
# online_data = scraper_obj.debug_get_user_levels(dict.copy(st_dic))
online_data = scraper_obj.debug_get_support_types(dict.copy(st_dic))
online_data = scraper_obj.debug_get_ROM_types(dict.copy(st_dic))
online_data = scraper_obj.debug_get_genres(dict.copy(st_dic))
online_data = scraper_obj.debug_get_regions(dict.copy(st_dic))
online_data = scraper_obj.debug_get_languages(dict.copy(st_dic))
online_data = scraper_obj.debug_get_clasifications(dict.copy(st_dic))
online_data = scraper_obj.debug_get_platforms(dict.copy(st_dic))
# pprint.pprint(online_data)
