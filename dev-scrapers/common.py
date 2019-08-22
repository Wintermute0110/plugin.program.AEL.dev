# -*- coding: utf-8 -*-

#
# Common data to test the scrapers.
#

settings = {
    # --- AEL Offline ---
    'scraper_aeloffline_addon_code_dir' : '',

    # --- MobyGames ---
    'scraper_mobygames_apikey' : '', # NEVER COMMIT THIS PASSWORD

    # --- ScreenScraper ---
    'scraper_screenscraper_ssid' : 'Wintermute0110',
    'scraper_screenscraper_sspass' : '',  # NEVER COMMIT THIS PASSWORD
    'scraper_screenscraper_AEL_softname' : 'AEL_0.9.8',
    'scraper_screenscraper_region' : 0, # Default World
    'scraper_screenscraper_language' : 0, # Default English
}

# --- Test data -----------------------------------------------------------------------------------
games = {
    # Console games
    'metroid'                : ('Metroid', 'Metroid', 'Nintendo SNES'),
    'mworld'                 : ('Super Mario World', 'Super Mario World', 'Nintendo SNES'),
    'sonic'                  : ('Sonic the Hedgehog', 'Sonic the Hedgehog (USA, Europe)', 'Sega MegaDrive'),
    'chakan'                 : ('Chakan', 'Chakan (USA, Europe)', 'Sega MegaDrive'),
    'console_wrong_title'    : ('Console invalid game', 'mjhyewqr', 'Sega MegaDrive'),
    'console_wrong_platform' : ('Sonic the Hedgehog', 'Sonic the Hedgehog (USA, Europe)', 'mjhyewqr'),

    # MAME games
    'atetris'             : ('Tetris (set 1)', 'atetris', 'MAME'),
    'mslug'               : ('Metal Slug - Super Vehicle-001', 'mslug', 'MAME'),
    'dino'                : ('Cadillacs and Dinosaurs (World 930201)', 'dino', 'MAME'),
    'MAME_wrong_title'    : ('MAME invalid game', 'mjhyewqr', 'MAME'),
    'MAME_wrong_platform' : ('Tetris (set 1)', 'atetris', 'mjhyewqr'),
}
