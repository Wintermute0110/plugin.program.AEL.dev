#!/usr/bin/python3 -B
# -*- coding: utf-8 -*-

# Test AEL MobyGames asset scraper.
# This testing file is intended for scraper development and file dumping.
# For more thorough tests sett the unittest_MobyGames_* scrips.

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

# --- main ---------------------------------------------------------------------------------------
print('\n*** Fetching candidate game list ********************************************************')
set_log_level(LOG_DEBUG)
st_dic = kodi_new_status_dic()

# --- Create scraper object ---
scraper_obj = MobyGames(common.settings)
scraper_obj.set_verbose_mode(False)
scraper_obj.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))

# --- Choose data for testing ---
# search_term, rombase, platform = common.games['metroid']
search_term, rombase, platform = common.games['mworld']
# search_term, rombase, platform = common.games['sonic_megadrive']
# search_term, rombase, platform = common.games['sonic_genesis'] # Aliased platform
# search_term, rombase, platform = common.games['chakan']
# search_term, rombase, platform = common.games['console_wrong_title']
# search_term, rombase, platform = common.games['console_wrong_platform']
# search_term, rombase, platform = common.games['bforever']
# search_term, rombase, platform = common.games['bforever_snes']

# --- Get candidates, print them and set first candidate ---
rom_FN = FileName(rombase)
rom_checksums_FN = FileName(rombase)
if scraper_obj.check_candidates_cache(rom_FN, platform):
    print('>>> Game "{}" "{}" in disk cache.'.format(rom_FN.getBase(), platform))
else:
    print('>>> Game "{}" "{}" not in disk cache.'.format(rom_FN.getBase(), platform))
candidate_list = scraper_obj.get_candidates(search_term, rom_FN, rom_checksums_FN, platform, st_dic)
# pprint.pprint(candidate_list)
common.handle_get_candidates(candidate_list, st_dic)
common.print_candidate_list(candidate_list)
scraper_obj.set_candidate(rom_FN, platform, candidate_list[0])

# --- Print list of assets found -----------------------------------------------------------------
print('\n*** Fetching game assets ****************************************************************')
# --- Get specific assets ---
common.print_game_assets(scraper_obj.get_assets(ASSET_TITLE_ID, st_dic))
common.print_game_assets(scraper_obj.get_assets(ASSET_SNAP_ID, st_dic))
common.print_game_assets(scraper_obj.get_assets(ASSET_BOXFRONT_ID, st_dic))
common.print_game_assets(scraper_obj.get_assets(ASSET_BOXBACK_ID, st_dic))
common.print_game_assets(scraper_obj.get_assets(ASSET_CARTRIDGE_ID, st_dic))

# --- Flush scraper disk cache -------------------------------------------------------------------
scraper_obj.flush_disk_cache()
