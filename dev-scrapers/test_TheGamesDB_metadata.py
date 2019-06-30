#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Test AEL TheGamesDB metadata scraper.
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

# --- Test data -----------------------------------------------------------------------------------
games = {
    'metroid' : ('Metroid', 'Metroid', 'Nintendo SNES'),
    'mworld' : ('Super Mario World', 'Super Mario World', 'Nintendo SNES'),
    'sonic' : ('Sonic The Hedgehog', 'Sonic The Hedgehog (USA, Europe)', 'Sega MegaDrive'),
}

# --- main ----------------------------------------------------------------------------------------
print('*** TheGamesDB search *********************************************************************')
set_log_level(LOG_DEBUG) # >> LOG_INFO, LOG_VERB, LOG_DEBUG

# --- Create scraper object ---
settings = {
    # Make sure this is the Public key.
    'scraper_thegamesdb_apikey' : '828be1fb8f3182d055f1aed1f7d4da8bd4ebc160c3260eae8ee57ea823b42415',
}
scraper_obj = TheGamesDB(settings)
scraper_obj.set_verbose_mode(False)
scraper_obj.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))

# --- Get candidates ---
# Cases with unknown platform must be tested as well.
# candidate_list = scraper_obj.get_candidates(*games['metroid'])
# candidate_list = scraper_obj.get_candidates(*games['mworld'])
candidate_list = scraper_obj.get_candidates(*games['sonic'])

# --- Print search results ---
# pprint.pprint(candidate_list)
print_candidate_list(candidate_list)
if not candidate_list:
    print('No candidates found.')
    sys.exit(0)

# --- Print metadata of first candidate ---
print('*** MobyGames game metadata ***************************************************************')
metadata = scraper_obj.get_metadata(candidate_list[0])
# pprint.pprint(metadata)
print_game_metadata(metadata)
