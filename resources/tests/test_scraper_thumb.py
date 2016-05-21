#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Test AEL thumb scraper
#

# Python standard library
import sys, os

# Import scrapers
if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scrap import *
from utils import *

# --- Scrapers to test ----------------------------------------------------------------------------
TEST_THEGAMESDB = True
TEST_GAMEFAQS   = False

# --- main ----------------------------------------------------------------------------------------
# --- Print name of all scrapers ---
print('Short name        Fancy Name')
print('----------------  ---------------------------------')
for scraper in scrapers_thumb:
    print('{:10s}  {:}'.format(scraper.name.rjust(16), scraper.fancy_name))

# --- Test TheGamesDB scraper -------------------------------------------------
if TEST_THEGAMESDB:
    print('\n*** Online TheGamesDB *********************************************')
    GamesDB = thumb_TheGamesDB()

    # results = GamesDB.get_games_search('Castlevania', 'Nintendo SNES')
    results = GamesDB.get_games_search('metroid', 'Nintendo SNES')
    # results = GamesDB.get_games_search('Zelda', 'Nintendo SNES')
    # results = GamesDB.get_games_search('Super Mario World', 'Nintendo SNES')
    # results = GamesDB.get_games_search('street fighter', 'Nintendo SNES', '')

    # --- Print list of fames found ---
    print_games_search(results)
    print_game_image_list(results, GamesDB)

# --- Test GameFAQs scraper ---------------------------------------------------
if TEST_GAMEFAQS:
    print('\n*** Online GameFAQs *********************************************')
    GameFAQs = thumb_GameFAQs()

    results = GameFAQs.get_games_search('Castlevania', 'Nintendo SNES')
    # results = GameFAQs.get_games_search('Metroid', 'Nintendo SNES')

    # --- Print list of fames found ---
    print_games_search(results)
    print_game_image_list(results, GameFAQs)
