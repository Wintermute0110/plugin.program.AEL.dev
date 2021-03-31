# -*- coding: utf-8 -*-

#
# Common data to test the scrapers.
#
import sys

settings = {
    # --- AEL Offline ---
    'scraper_aeloffline_addon_code_dir' : '',

    # --- MobyGames ---
    'scraper_mobygames_apikey' : '', # NEVER COMMIT THIS PASSWORD

    # --- ScreenScraper ---
    'scraper_screenscraper_ssid' : 'Wintermute0110',
    'scraper_screenscraper_sspass' : '', # NEVER COMMIT THIS PASSWORD
    'scraper_screenscraper_AEL_softname' : 'AEL_0.9.8',
    'scraper_screenscraper_region' : 0, # Default World
    'scraper_screenscraper_language' : 0, # Default English

    # --- All scrapers ---
    'scraper_cache_dir' : './cache/'
}

# --- Test data -----------------------------------------------------------------------------------
games = {
    # Console games
    'metroid'                : ('Metroid', 'Metroid.zip', 'Nintendo SNES'),
    'mworld'                 : ('Super Mario World', 'Super Mario World.zip', 'Nintendo SNES'),
    'sonic_megaDrive'        : ('Sonic the Hedgehog', 'Sonic the Hedgehog (USA, Europe).zip', 'Sega Mega Drive'),
    'sonic_genesis'          : ('Sonic the Hedgehog', 'Sonic the Hedgehog (USA, Europe).zip', 'Sega Genesis'),
    'chakan'                 : ('Chakan', 'Chakan (USA, Europe).zip', 'Sega MegaDrive'),
    'ff7'                    : ('Final Fantasy VII', 'Final Fantasy VII (USA) (Disc 1).iso', 'Sony PlayStation'),
    'console_wrong_title'    : ('Console invalid game', 'mjhyewqr.zip', 'Sega MegaDrive'),
    'console_wrong_platform' : ('Sonic the Hedgehog', 'Sonic the Hedgehog (USA, Europe).zip', 'mjhyewqr'),

    # MAME games
    'atetris'             : ('Tetris (set 1)', 'atetris.zip', 'MAME'),
    'mslug'               : ('Metal Slug - Super Vehicle-001', 'mslug.zip', 'MAME'),
    'dino'                : ('Cadillacs and Dinosaurs (World 930201)', 'dino.zip', 'MAME'),
    'MAME_wrong_title'    : ('MAME invalid game', 'mjhyewqr.zip', 'MAME'),
    'MAME_wrong_platform' : ('Tetris (set 1)', 'atetris.zip', 'mjhyewqr'),
}

def handle_get_candidates(candidate_list, status_dic):
    if not status_dic['status']:
        print('Status error "{}"'.format(status_dic['msg']))
        sys.exit(0)
    if candidate_list is None:
        print('Error/exception in get_candidates(). Exiting.')
        sys.exit(0)
    if not candidate_list:
        print('No candidates found. Exiting.')
        sys.exit(0)
