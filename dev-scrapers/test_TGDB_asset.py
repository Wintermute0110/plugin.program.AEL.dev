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
scraper_obj = TheGamesDB(common.settings)
scraper_obj.set_verbose_mode(False)
scraper_obj.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))
status_dic = kodi_new_status_dic('Scraper test was OK')

# --- Choose data for testing ---
# search_term, rombase_noext, platform = common.games['metroid']
# search_term, rombase_noext, platform = common.games['mworld']
# search_term, rombase_noext, platform = common.games['sonic']
search_term, rombase_noext, platform = common.games['chakan']
# search_term, rombase_noext, platform = common.games['console_wrong_title']
# search_term, rombase_noext, platform = common.games['console_wrong_platform']

# --- Get candidates, print them and set first candidate ---
if scraper_obj.check_candidates_cache(rombase_noext, platform):
    print('>>>> Game "{}" "{}" in disk cache.'.format(rombase_noext, platform))
else:
    print('>>>> Game "{}" "{}" not in disk cache.'.format(rombase_noext, platform))
candidate_list = scraper_obj.get_candidates(search_term, rombase_noext, platform, status_dic)
# pprint.pprint(candidate_list)
common.handle_get_candidates(candidate_list, status_dic)
print_candidate_list(candidate_list)
scraper_obj.set_candidate(rombase_noext, platform, candidate_list[0])

# --- Print list of assets found -----------------------------------------------------------------
print('*** Fetching game assets ****************************************************************')
# --- Get all assets (TGBD scraper custom function) ---
# assets = scraper_obj.get_assets_all(candidate)
# pprint.pprint(assets)
# print_game_assets(assets)

# --- Get specific assets ---
print_game_assets(scraper_obj.get_assets(ASSET_FANART_ID, status_dic))
print_game_assets(scraper_obj.get_assets(ASSET_BANNER_ID, status_dic))
print_game_assets(scraper_obj.get_assets(ASSET_CLEARLOGO_ID, status_dic))
print_game_assets(scraper_obj.get_assets(ASSET_SNAP_ID, status_dic))
print_game_assets(scraper_obj.get_assets(ASSET_BOXFRONT_ID, status_dic))
print_game_assets(scraper_obj.get_assets(ASSET_BOXBACK_ID, status_dic))
scraper_obj.flush_disk_cache()
