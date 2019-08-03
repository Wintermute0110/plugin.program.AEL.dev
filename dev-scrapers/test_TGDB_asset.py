#!/usr/bin/python
# -*- coding: utf-8 -*-

# Test AEL TheGamesDB asset scraper.

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
print('*** Fetching candidate game list ********************************************************')
set_log_level(LOG_DEBUG)

# --- Create scraper object ---
scraper_obj = GameFAQs(common.settings)
scraper_obj.set_verbose_mode(False)
scraper_obj.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))

# --- Get candidates ---
# candidate_list = scraper_obj.get_candidates(*games['metroid'])
# candidate_list = scraper_obj.get_candidates(*games['mworld'])
candidate_list = scraper_obj.get_candidates(*games['sonic'])
# candidate_list = scraper_obj.get_candidates(*games['chakan'])

# --- Print search results ---
# pprint.pprint(candidate_list)
print_candidate_list(candidate_list)
if not candidate_list:
    print('No candidates found.')
    sys.exit(0)
candidate = candidate_list[0]

# --- Print list of assets found -----------------------------------------------------------------
print('*** Fetching game assets ****************************************************************')
# --- Get all assets (TGBD scraper custom function) ---
# assets = scraper_obj.get_assets_all(candidate)
# pprint.pprint(assets)
# print_game_assets(assets)

# --- Get specific assets ---
print_game_assets(scraper_obj.get_assets(candidate, ASSET_TITLE_ID))
print_game_assets(scraper_obj.get_assets(candidate, ASSET_SNAP_ID))
print_game_assets(scraper_obj.get_assets(candidate, ASSET_BOXFRONT_ID))
print_game_assets(scraper_obj.get_assets(candidate, ASSET_BOXBACK_ID))
print_game_assets(scraper_obj.get_assets(candidate, ASSET_CARTRIDGE_ID))
print_game_assets(scraper_obj.get_assets(candidate, ASSET_FANART_ID))
# print_game_assets(scraper_obj.get_assets(candidate, ASSET_BANNER_ID))
# print_game_assets(scraper_obj.get_assets(candidate, ASSET_CLEARLOGO_ID))
# print_game_assets(scraper_obj.get_assets(candidate, ASSET_FLYER_ID))
# print_game_assets(scraper_obj.get_assets(candidate, ASSET_3DBOX_ID))
# print_game_assets(scraper_obj.get_assets(candidate, ASSET_MAP_ID))
# print_game_assets(scraper_obj.get_assets(candidate, ASSET_MANUAL_ID))
# print_game_assets(scraper_obj.get_assets(candidate, ASSET_TRAILER_ID))
