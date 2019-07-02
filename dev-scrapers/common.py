# -*- coding: utf-8 -*-

#
# Common data to test the scrapers.
#

settings = {
    # --- MobyGames ---
    'scraper_mobygames_apikey' : '',  # NEVER COMMIT THIS PASSWORD

    # --- TheGamesDB ---
    # Make sure this is the Public key.
    'scraper_thegamesdb_apikey' : '828be1fb8f3182d055f1aed1f7d4da8bd4ebc160c3260eae8ee57ea823b42415',

    # --- ScreenScraper ---
    'scraper_screenscraper_apikey' : '',
    'scraper_screenscraper_dev_id' : 'Wintermute0110',
    'scraper_screenscraper_dev_pass' : '', # NEVER COMMIT THIS PASSWORD
    'scraper_screenscraper_AEL_softname' : 'AEL_0.9.8',
}

# --- Test data -----------------------------------------------------------------------------------
games = {
    'metroid' : ('Metroid', 'Metroid', 'Nintendo SNES'),
    'mworld' : ('Super Mario World', 'Super Mario World', 'Nintendo SNES'),
    'sonic' : ('Sonic The Hedgehog', 'Sonic The Hedgehog (USA, Europe)', 'Sega MegaDrive'),
    'chakan' : ('Chakan', 'Chakan (USA, Europe)', 'Sega MegaDrive'),
}
