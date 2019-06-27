#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Test AEL Mobybgames metadata scraper.
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
print('*** MobyGames search **********************************************************************')
set_log_level(LOG_DEBUG) # >> LOG_INFO, LOG_VERB, LOG_DEBUG

# --- Create scraper object ---
settings = {
    'scraper_mobygames_apikey' : '', # Do not forget to set the API key.
}
scraper_obj = MobyGames(settings)
scraper_obj.set_verbose_mode(False)
scraper_obj.set_debug_file_dump(True, os.path.dirname(__file__))

# --- Get candidates ---
# Cases with unknown platform must be tested as well.
candidate_list = scraper_obj.get_candidates(*games['metroid'])
# candidate_list = scraper_obj.get_candidates(*games['mworld'])
# candidate_list = scraper_obj.get_candidates(*games['sonic'])

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
