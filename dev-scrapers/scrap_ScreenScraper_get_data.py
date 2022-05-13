#!/usr/bin/python3 -B
# -*- coding: utf-8 -*-

# Plumbing script to retrieve data from ScreenScraper.
# Data in JSON format will be saved in ./assets/ subdirectory.

# --- Import AEL modules ---
import os
import sys
if __name__ == "__main__" and __package__ is None:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print('Adding to sys.path {}'.format(path))
    sys.path.append(path)
import resources.const as const
import resources.log as log
import resources.misc as misc
import resources.utils as utils
import resources.kodi as kodi
import resources.scrap as scrap
import common

# --- Python standard library ---
import pprint

# --- main ----------------------------------------------------------------------------------------
log.set_log_level(log.LOG_DEBUG)

# --- Create scraper object ---
scraper = scrap.ScreenScraper(common.settings)
scraper.set_verbose_mode(False)
scraper.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))
st = kodi.new_status_dic()

# --- Get ROM types ---
online_data = scraper.debug_get_user_info(dict.copy(st))
# userlevelsListe.php fails because invalid JSON returned. It's not prioritary at all, however.
# online_data = scraper.debug_get_user_levels(dict.copy(st))
online_data = scraper.debug_get_support_types(dict.copy(st))
online_data = scraper.debug_get_ROM_types(dict.copy(st))
online_data = scraper.debug_get_genres(dict.copy(st))
online_data = scraper.debug_get_regions(dict.copy(st))
online_data = scraper.debug_get_languages(dict.copy(st))
online_data = scraper.debug_get_clasifications(dict.copy(st))
online_data = scraper.debug_get_platforms(dict.copy(st))
# pprint.pprint(online_data)
