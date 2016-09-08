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

# --- Print list of all scrapers currently in AEL ---
print_scraper_list(scrapers_metadata)

# --- main ----------------------------------------------------------------------------------------
print('*** Arcade Database *********************************************')
ArcadeDB = metadata_ArcadeDB()

# results = ArcadeDB.get_search('', 'dino', 'MAME')
results = ArcadeDB.get_search('', 'aliens', 'MAME')
# results = ArcadeDB.get_search('', 'spang', 'MAME')
# results = ArcadeDB.get_search('', 'toki', 'MAME')
# results = ArcadeDB.get_search('', 'asdfg', 'MAME') # Fake game to produce a not found error

# --- Print list of fames found ---
print_games_search(results)
print_game_metadata(ArcadeDB, results)
