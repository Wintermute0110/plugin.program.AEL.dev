#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Test AEL metadata scraper
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

# --- print scraped results -----------------------------------------------------------------------
# PUT functions to print things returned by Scraper object (which are common to all scrapers)
# into util.py, to be resused by all scraper tests.
def print_games_search(results, scraperObj):
    id_length = 60
    name_length = 70
    genre_length = 20
    studio_length = 20
    plot_length = 40
    print('*** Found {} games ***'.format(len(results)))
    for game in results:
        display_name = text_limit_string(game['display_name'], name_length)
        id           = text_limit_string(game['id'], id_length)
        print("'{}' '{}'".format(display_name.ljust(name_length), id.ljust(id_length)))
    
    # --- Get metadata of first game ---
    if results:
        metadata = scraperObj.get_game_metadata(results[0])

        title  = text_limit_string(metadata['title'], name_length)
        genre  = text_limit_string(metadata['genre'], genre_length)
        year   =                   metadata['year']
        studio = text_limit_string(metadata['studio'], studio_length)
        plot   = text_limit_string(metadata['plot'], plot_length)
        print('*** Displaying metadata for {} ***'.format(title))
        print("'{}' '{}' '{}' '{}' '{}'".format(title.ljust(name_length), genre.ljust(genre_length), 
                                                year.ljust(4), studio.ljust(studio_length), plot.ljust(plot_length)))

# --- main ----------------------------------------------------------------------------------------
# Print name of all scrapers
print('Short name        Fancy Name')
print('----------------  ---------------------------------')
for scraper in scrapers_metadata:
    print('{:10s}  {:}'.format(scraper.name.rjust(16), scraper.fancy_name))


if TEST_OFFLINE:
    print('\n--- Offline scraper -----------------------------------------------')
    Offline = metadata_Offline()
    Offline.set_plugin_inst_dir('/home/mendi/.kodi/addons/plugin.program.advanced.emulator.launcher/')

    # First time a platform is used XML database is loaded and cached for subsequent
    # calls until object is destroyed or platform is changed.
    results = Offline.get_games_search('super mario world', '', 'Nintendo SNES')
    # results = Offline.get_games_search('castle', '', 'Nintendo SNES')

    # Test MAME offline scraper
    # results = Offline.get_games_search('dino', 'dino', 'MAME')
    # results = Offline.get_games_search('aliens', 'MAME', 'aliens')
    # results = Offline.get_games_search('spang', 'MAME')
    # results = Offline.get_games_search('tokia', 'MAME')
    # results = Offline.get_games_search('asdfg', 'MAME')

    # --- Print list of fames found ---
    print_games_search(results, Offline)


if TEST_THEGAMESDB:
    print('\n--- Online TheGamesDB ---------------------------------------------')
    # It seems that TheGamesDB does and OR search with all keywords introduced.
    # It will show results even if the game title contains just one of thekeywords.
    GamesDB = metadata_TheGamesDB()

    # results = GamesDB.get_games_search('Castlevania', 'Nintendo SNES')
    # results = GamesDB.get_games_search('Metroid', 'Nintendo SNES')
    # results = GamesDB.get_games_search('Zelda', 'Nintendo SNES')
    # results = GamesDB.get_games_search('Super Mario World', 'Nintendo SNES')
    results = GamesDB.get_games_search('super street fighter', '', 'Nintendo SNES')

    # --- Print list of fames found ---
    print_games_search(results, GamesDB)


if TEST_GAMEFAQS:
    print('\n--- Online GameFAQs -----------------------------------------------')
    GameFAQs = metadata_GameFAQs()

    # results = GameFAQs.get_games_search('Castlevania', 'Nintendo SNES')
    # results = GameFAQs.get_games_search('Metroid', 'Nintendo SNES')
    # results = GameFAQs.get_games_search('Zelda', 'Nintendo SNES')
    # results = GameFAQs.get_games_search('Super Mario World', 'Nintendo SNES')
    results = GameFAQs.get_games_search('super street fighter', '', 'Nintendo SNES')

    # --- Print list of fames found ---
    print_games_search(results, GameFAQs)
