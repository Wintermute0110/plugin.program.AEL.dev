# -*- coding: utf-8 -*-

#
# Common data to test the scrapers.
#

settings = {
    # --- AEL Offline ---
    'scraper_aeloffline_addon_code_dir' : '',

    # --- MobyGames ---
    'scraper_mobygames_apikey' : '', # NEVER COMMIT THIS PASSWORD

    # --- TheGamesDB ---
    # Make sure this is the Public key.
    'scraper_thegamesdb_apikey' : '828be1fb8f3182d055f1aed1f7d4da8bd4ebc160c3260eae8ee57ea823b42415',

    # --- ScreenScraper ---
    'scraper_screenscraper_ssid' : 'Wintermute0110',
    'scraper_screenscraper_sspass' : '',  # NEVER COMMIT THIS PASSWORD
    'scraper_screenscraper_AEL_softname' : 'AEL_0.9.8',
}

# --- Test data -----------------------------------------------------------------------------------
games = {
    # Console games
    'metroid'         : ('Metroid', 'Metroid', 'Nintendo SNES'),
    'mworld'          : ('Super Mario World', 'Super Mario World', 'Nintendo SNES'),
    'sonic'           : ('Sonic the Hedgehog', 'Sonic the Hedgehog (USA, Europe)', 'Sega MegaDrive'),
    'chakan'          : ('Chakan', 'Chakan (USA, Europe)', 'Sega MegaDrive'),
    'console_invalid' : ('Console invalid game', 'mjhyewqr', 'Sega MegaDrive'),

    # MAME games
    'tetris'          : ('Tetris (set 1)', 'atetris', 'MAME'),
    'mslug'           : ('Metal Slug - Super Vehicle-001', 'mslug', 'MAME'),
    'dino'            : ('Cadillacs and Dinosaurs (World 930201)', 'dino', 'MAME'),
    'MAME_invalid'    : ('MAME invalid game', 'mjhyewqr', 'MAME'),
}
