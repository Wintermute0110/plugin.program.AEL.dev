#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Test AEL metadata scraper
#

# --- Python standard library ---
from __future__ import unicode_literals
import os
import pprint
import sys

# --- AEL modules ---
if __name__ == "__main__" and __package__ is None:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print('Adding to sys.path {0}'.format(path))
    sys.path.append(path)
from resources.scrap import *
from resources.utils import *


# --- Print list of all scrapers currently in AEL ---
# >> LOG_INFO, LOG_VERB, LOG_DEBUG
set_log_level(LOG_DEBUG)

# --- Test data -----------------------------------------------------------------------------------
games = {
    'metroid' : ('Metroid', 'Metroid', 'Nintendo SNES'),
    'mworld' : ('Super Mario World', 'Super Mario World', 'Nintendo SNES'),
    'sonic' : ('Sonic The Hedgehog', 'Sonic The Hedgehog (USA, Europe)', 'Sega MegaDrive'),
}

# --- main ----------------------------------------------------------------------------------------
print('*** MobyGames *********************************************')
# --- Create scraper object ---
# Do not forget to set the API key.
settings = {
    'scraper_mobygames_apikey' : '',
}
MobyGames = MobyGames_Scraper(settings)
MobyGames.set_debug_mode(True, os.path.dirname(__file__))

# --- Get candidates ---
candidate_list = MobyGames.get_candidates(*games['metroid'])
# candidate_list = MobyGames.get_candidates(*games['mworld'])
# candidate_list = MobyGames.get_candidates(*games['sonic'])
# Cases with unknown platform must be tested as well.

# --- Print search results ---
# pprint.pprint(candidate_list)
print_candidate_list(candidate_list)
if not candidate_list:
    print('No candidates found.')
    sys.exit(0)

# --- Print metadata of first candidate ---
metadata = MobyGames.get_metadata(candidate_list[0])
# pprint.pprint(metadata)
print_game_metadata(metadata)
