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
print('*** Online GameFAQs *********************************************')
GameFAQs = metadata_GameFAQs()

# results = GameFAQs.get_search('Castlevania', 'Nintendo SNES')
# results = GameFAQs.get_search('Metroid', 'Nintendo SNES')
# results = GameFAQs.get_search('Zelda', 'Nintendo SNES')
# results = GameFAQs.get_search('Super Mario World', 'Nintendo SNES')
results = GameFAQs.get_search('super street fighter', '', 'Nintendo SNES')

# --- Print list of fames found ---
print_games_search(results)
print_game_metadata(GameFAQs, results)
