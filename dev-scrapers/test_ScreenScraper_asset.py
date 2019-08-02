#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Test AEL ScreenScraper asset scraper.
# This testing file is intended for scraper development and file dumping.
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

# --- main ---------------------------------------------------------------------------------------
print('*** ScreenScraper search ****************************************************************')
set_log_level(LOG_DEBUG)

# --- Create scraper object ---
scraper_obj = ScreenScraper_V1(common.settings)
scraper_obj.set_verbose_mode(False)
scraper_obj.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))

# --- Get candidates ---
# candidate_list = scraper_obj.get_candidates(*common.games['metroid'])
# candidate_list = scraper_obj.get_candidates(*common.games['mworld'])
candidate_list = scraper_obj.get_candidates(*common.games['sonic'])
# candidate_list = scraper_obj.get_candidates(*common.games['chakan'])

# --- Print search results ---
# pprint.pprint(candidate_list)
print_candidate_list(candidate_list)
if not candidate_list:
    print('No candidates found.')
    sys.exit(0)

# --- Print list of assets found -----------------------------------------------------------------
print('*** ScreenScraper game images ***********************************************************')
candidate = candidate_list[0]
print_game_assets(scraper_obj.get_assets(candidate, ASSET_TITLE_ID))
print_game_assets(scraper_obj.get_assets(candidate, ASSET_SNAP_ID))
print_game_assets(scraper_obj.get_assets(candidate, ASSET_BOXFRONT_ID))
print_game_assets(scraper_obj.get_assets(candidate, ASSET_BOXBACK_ID))
print_game_assets(scraper_obj.get_assets(candidate, ASSET_3DBOX_ID))
print_game_assets(scraper_obj.get_assets(candidate, ASSET_CARTRIDGE_ID))
print_game_assets(scraper_obj.get_assets(candidate, ASSET_FANART_ID))
print_game_assets(scraper_obj.get_assets(candidate, ASSET_CLEARLOGO_ID))
# print_game_assets(scraper_obj.get_assets(candidate, ASSET_MAP_ID))
# print_game_assets(scraper_obj.get_assets(candidate, ASSET_MANUAL_ID))
# print_game_assets(scraper_obj.get_assets(candidate, ASSET_TRAILER_ID))
