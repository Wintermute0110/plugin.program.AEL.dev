#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Test AEL asset scraper
#

# --- Python standard library ---
from __future__ import unicode_literals

# --- AEL modules ---
from AEL.resources.scrap import *
from AEL.resources.utils import *

# --- main ----------------------------------------------------------------------------------------
set_log_level(LOG_DEBUG) # >> LOG_INFO, LOG_VERB, LOG_DEBUG
print_scraper_list(scrapers_asset)

print('*** TheGamesDB search **********************************************************************')
GamesDB = asset_TheGamesDB()

# results = GamesDB.get_search('Castlevania', '', 'Nintendo SNES')
# results = GamesDB.get_search('Metroid', '', 'Nintendo SNES')
# results = GamesDB.get_search('Zelda', '', 'Nintendo SNES')
results = GamesDB.get_search('Super Mario World', '', 'Nintendo SNES')
# results = GamesDB.get_search('Street Fighter', '', 'Nintendo SNES', '')

# --- Print list of games found ---
print_games_search(results)

# --- Print list of assets found ---
print('*** TheGamesDB found images *****************************************************************')
# print_game_image_list(GamesDB, results, ASSET_TITLE)
print_game_image_list(GamesDB, results, ASSET_SNAP)
print_game_image_list(GamesDB, results, ASSET_FANART)
print_game_image_list(GamesDB, results, ASSET_BANNER)
print_game_image_list(GamesDB, results, ASSET_CLEARLOGO)
print_game_image_list(GamesDB, results, ASSET_BOXFRONT)
print_game_image_list(GamesDB, results, ASSET_BOXBACK)
# print_game_image_list(GamesDB, results, ASSET_CARTRIDGE)
# print_game_image_list(GamesDB, results, ASSET_FLYER)
# print_game_image_list(GamesDB, results, ASSET_MAP)
# print_game_image_list(GamesDB, results, ASSET_MANUAL)
# print_game_image_list(GamesDB, results, ASSET_TRAILER)
