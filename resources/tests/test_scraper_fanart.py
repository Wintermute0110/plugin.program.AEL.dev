#!/usr/bin/python
#
# Test AEL fanart scraper
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
TEST_GAMEFAQS   = True

# --- main ----------------------------------------------------------------------------------------
print_scraper_list(scrapers_fanart)

if TEST_THEGAMESDB:
    print('\n*** Online TheGamesDB *********************************************')
    GamesDB = fanart_TheGamesDB()

    results = GamesDB.get_search('Castlevania', '', 'Nintendo SNES')
    # results = GamesDB.get_search('metroid', '', 'Nintendo SNES')
    # results = GamesDB.get_search('Zelda', '', 'Nintendo SNES')
    # results = GamesDB.get_search('Super Mario World', '', 'Nintendo SNES')
    # results = GamesDB.get_search('street fighter', '', 'Nintendo SNES', '')

    # --- Print list of fames found ---
    print_games_search(results)
    print_game_image_list(results, GamesDB)

if TEST_GAMEFAQS:
    print('\n*** Online GameFAQs *********************************************')
    GameFAQs = fanart_GameFAQs()

    # results = GameFAQs.get_search('Castlevania', '', 'Nintendo SNES')
    results = GameFAQs.get_search('Metroid', '', 'Nintendo SNES')

    # --- Print list of fames found ---
    print_games_search(results)
    print_game_image_list(results, GameFAQs)
