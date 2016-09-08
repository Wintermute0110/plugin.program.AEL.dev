#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Test AEL asset scraper
#

# --- Python standard library ---
from __future__ import unicode_literals
import sys, os

# --- AEL modules ---
if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scrap import *
from utils import *
from assets import *

# --- Scrapers to test ----------------------------------------------------------------------------
TEST_THEGAMESDB = True
TEST_GAMEFAQS   = False

# --- main ----------------------------------------------------------------------------------------
print_scraper_list(scrapers_asset)

if TEST_THEGAMESDB:
    print('\n*** Online TheGamesDB *********************************************')
    GamesDB = asset_TheGamesDB()

    # results = GamesDB.get_search('Castlevania', '', 'Nintendo SNES')
    # results = GamesDB.get_search('Metroid', '', 'Nintendo SNES')
    # results = GamesDB.get_search('Zelda', '', 'Nintendo SNES')
    results = GamesDB.get_search('Super Mario World', '', 'Nintendo SNES')
    # results = GamesDB.get_search('Street Fighter', '', 'Nintendo SNES', '')

    # --- Print list of games found ---
    print_games_search(results)

    # --- Print list of assets found ---
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

if TEST_GAMEFAQS:
    print('\n*** Online GameFAQs *********************************************')
    GameFAQs = asset_GameFAQs()

    results = GameFAQs.get_search('Castlevania', '', 'Nintendo SNES')
    # results = GameFAQs.get_search('Metroid', '', 'Nintendo SNES')

    # --- Print list of fames found ---
    print_games_search(results)

    # --- Print list of assets found ---
    print_game_image_list(GameFAQs, results, ASSET_TITLE)
    print_game_image_list(GameFAQs, results, ASSET_SNAP)

