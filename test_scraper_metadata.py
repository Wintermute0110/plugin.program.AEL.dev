#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Test AEL metadata scraper
#

# Python standard library
import sys

# Import scrapers
from resources.scrap import *

def print_metadata(metadata):
    print('Title    "{}"'.format(metadata['title']))
    print('Genre    "{}"'.format(metadata['genre']))
    print('Release  "{}"'.format(metadata['release']))
    print('Studio   "{}"'.format(metadata['studio']))
    print('Plot     "{}"'.format(metadata['plot']))
    
# --- main --------------------------------------------------------------------
# Print name of all scrapers
print('Short name        Fancy Name')
print('----------------  ---------------------------------')
for scraper in scrapers_metadata:
    print('{:10s}  {:}'.format(scraper.name.rjust(16), scraper.fancy_name))

print('\n--- Offline scraper ---------------------------------------------------')
offline = metadata_Offline()

# First time a platform is used XML database is loaded and cached for subsequent
# calls until object is destroyed or platform is changed.
results = offline.get_games_search('', 'Sega 32X', 'Sonic')
# offline.get_games_search('', 'Sega 32X', 'doom')

# Another system can be loaded to replace the current one at any time
# offline.get_games_search('mario', 'Nintendo SNES')
# offline.get_games_search('castle', 'Nintendo SNES')

# Test MAME offline scraper
# offline.get_games_search('dino', 'MAME')
# offline.get_games_search('aliens', 'MAME')
# offline.get_games_search('spang', 'MAME')
# offline.get_games_search('tokia', 'MAME')
# offline.get_games_search('asdfg', 'MAME')

if results:
    print('Found {} games'.format(len(results)))
    metadata = offline.get_game_metadata(results[0])
    print_metadata(metadata)
else:
    print('No results found.')

print('\n--- Online TheGamesDB -------------------------------------------------')
# It seems that TheGamesDB does and OR search with all keywords introduced.
# It will show results even if the game title contains just one of thekeywords.
GamesDB = metadata_TheGamesDB()

# results = GamesDB.get_games_search('Castlevania', 'Nintendo SNES')
# results = GamesDB.get_games_search('Metroid', 'Nintendo SNES')
# results = GamesDB.get_games_search('Zelda', 'Nintendo SNES')
# results = GamesDB.get_games_search('Super Mario World', 'Nintendo SNES')
results = GamesDB.get_games_search('street fighter', 'Nintendo SNES', '')

if results:
    print('Found {} games'.format(len(results)))
    metadata = GamesDB.get_game_metadata(results[0])
    print_metadata(metadata)
else:
    print('No results found.')

print('\n--- Online GameFAQs ---------------------------------------------------')
GameFAQs = metadata_GameFAQs()

# results = GameFAQs.get_games_search('Castlevania', 'Nintendo SNES')
# results = GameFAQs.get_games_search('Metroid', 'Nintendo SNES')
# results = GameFAQs.get_games_search('Zelda', 'Nintendo SNES')
# results = GameFAQs.get_games_search('Super Mario World', 'Nintendo SNES')
results = GameFAQs.get_games_search('super street fighter', 'Nintendo SNES')

if results:
    print('Found {} games'.format(len(results)))
    metadata = GameFAQs.get_game_metadata(results[0])
    print_metadata(metadata)
else:
    print('No results found.')

# --- Online arcadeHITS ------------------------------------------------------

# --- Online MobyGames ------------------------------------------------------
