#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Test AEL metadata scraper
#

# --- Python standard library ---
from __future__ import unicode_literals
import sys, os

# --- AEL modules ---
if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scrap import *
from utils import *

# --- Scrapers to test ----------------------------------------------------------------------------
TEST_OFFLINE    = False
TEST_THEGAMESDB = False
TEST_GAMEFAQS   = True

# --- main ----------------------------------------------------------------------------------------
print_scraper_list(scrapers_metadata)

if TEST_OFFLINE:
    print('\n*** Offline scraper ***********************************************')
    Offline = metadata_Offline()
    Offline.set_addon_dir('/home/mendi/.kodi/addons/plugin.program.advanced.emulator.launcher/')
    # Offline.set_addon_dir('/cygdrive/e/Mendi/plugin/')

    # First time a platform is used XML database is loaded and cached for subsequent
    # calls until object is destroyed or platform is changed.
    # results = Offline.get_search('super mario world', 'super mario world', 'Nintendo SNES')
    # results = Offline.get_search('castle', 'castle', 'Nintendo SNES')

    # Test MAME offline scraper
    results = Offline.get_search('dino', 'dino', 'MAME')
    # results = Offline.get_search('aliens', 'aliens', 'MAME')
    # results = Offline.get_search('spang', 'spang', 'MAME')
    # results = Offline.get_search('toki', 'toki', 'MAME')
    # results = Offline.get_search('asdfg', 'asdfg', 'MAME')

    # --- Print list of fames found ---
    print_games_search(results)
    print_game_metadata(results, Offline)

if TEST_THEGAMESDB:
    print('\n*** Online TheGamesDB *********************************************')
    # It seems that TheGamesDB does and OR search with all keywords introduced.
    # It will show results even if the game title contains just one of thekeywords.
    GamesDB = metadata_TheGamesDB()

    # results = GamesDB.get_search('Castlevania', '', 'Nintendo SNES')
    # results = GamesDB.get_search('Metroid', '', 'Nintendo SNES')
    # results = GamesDB.get_search('Zelda', '', 'Nintendo SNES')
    # results = GamesDB.get_search('Super Mario World', '', 'Nintendo SNES')
    results = GamesDB.get_search('super street fighter', '', 'Nintendo SNES')

    # --- Print list of fames found ---
    print_games_search(results)
    print_game_metadata(results, GamesDB)


if TEST_GAMEFAQS:
    print('\n*** Online GameFAQs *********************************************')
    GameFAQs = metadata_GameFAQs()

    # results = GameFAQs.get_search('Castlevania', 'Nintendo SNES')
    # results = GameFAQs.get_search('Metroid', 'Nintendo SNES')
    # results = GameFAQs.get_search('Zelda', 'Nintendo SNES')
    # results = GameFAQs.get_search('Super Mario World', 'Nintendo SNES')
    results = GameFAQs.get_search('super street fighter', '', 'Nintendo SNES')

    # --- Print list of fames found ---
    print_games_search(results)
    print_game_metadata(results, GameFAQs)
