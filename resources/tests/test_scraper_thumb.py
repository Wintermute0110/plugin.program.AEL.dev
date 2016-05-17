#!/usr/bin/python
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
TEST_OFFLINE    = True
TEST_THEGAMESDB = False
TEST_GAMEFAQS   = False

# --- main ----------------------------------------------------------------------------------------
# Print name of all scrapers
print('Short name  Fancy Name')
print('----------  ---------------------------------')
for scraper in scrapers_thumb:
    print('{:10s}  {:}'.format(scraper.name.rjust(10), scraper.fancy_name))
print('')

# --- Test TheGamesDB scraper -------------------------------------------------




print('\n--- Online TheGamesDB -------------------------------------------------')
GamesDB = thumb_TheGamesDB()

# results = GamesDB.get_games_search('Castlevania', 'Nintendo SNES')
# results = GamesDB.get_games_search('Metroid', 'Nintendo SNES')
# results = GamesDB.get_games_search('Zelda', 'Nintendo SNES')
# results = GamesDB.get_games_search('Super Mario World', 'Nintendo SNES')
results = GamesDB.get_games_search('street fighter', 'Nintendo SNES', '')


if results:
    print('Found {} games'.format(len(results)))
    metadata = GamesDB.get_game_image_list(results[0])
    print(metadata)
else:
    print('No results found.')
