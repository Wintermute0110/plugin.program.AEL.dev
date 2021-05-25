# -*- coding: utf-8 -*-

#
# Common data to test the scrapers.
#
from __future__ import unicode_literals
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
    'sonic_megadrive'        : ('Sonic the Hedgehog', 'Sonic the Hedgehog (USA, Europe).zip', 'Sega Mega Drive'),
    # Genesis is an aliased name for Mega Drive
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

# These must be replaced with the table-making functions.
# TODO Move this code to dev-scrapers/common.py

# Candidates
NAME_L      = 65
SCORE_L     = 5
ID_L        = 55
PLATFORM_L  = 20
SPLATFORM_L = 20
URL_L       = 70

# Metadata
TITLE_L     = 50
YEAR_L      = 4
GENRE_L     = 20
DEVELOPER_L = 10
NPLAYERS_L  = 10
ESRB_L      = 20
PLOT_L      = 70

# Assets
ASSET_ID_L        = 10
ASSET_NAME_L      = 60
ASSET_URL_THUMB_L = 100

# PUT functions to print things returned by Scraper object (which are common to all scrapers)
# into util.py, to be resused by all scraper tests.
def print_candidate_list(results):
    p_str = "{} {} {} {} {}"
    print('Found {} candidate/s'.format(len(results)))
    print(p_str.format(
        'Display name'.ljust(NAME_L), 'Score'.ljust(SCORE_L),
        'Id'.ljust(ID_L), 'Platform'.ljust(PLATFORM_L), 'SPlatform'.ljust(SPLATFORM_L)))
    print(p_str.format(
        '-'*NAME_L, '-'*SCORE_L, '-'*ID_L, '-'*PLATFORM_L, '-'*SPLATFORM_L))
    for game in results:
        display_name = text_limit_string(game['display_name'], NAME_L)
        score = text_limit_string(text_type(game['order']), SCORE_L)
        id = text_limit_string(text_type(game['id']), ID_L)
        platform = text_limit_string(text_type(game['platform']), PLATFORM_L)
        splatform = text_limit_string(text_type(game['scraper_platform']), SPLATFORM_L)
        print(p_str.format(
            display_name.ljust(NAME_L), score.ljust(SCORE_L), id.ljust(ID_L),
            platform.ljust(PLATFORM_L), splatform.ljust(SPLATFORM_L)))
    print('')

def print_game_metadata(metadata):
    title     = text_limit_string(metadata['title'], TITLE_L)
    year      = metadata['year']
    genre     = text_limit_string(metadata['genre'], GENRE_L)
    developer = text_limit_string(metadata['developer'], DEVELOPER_L)
    nplayers  = text_limit_string(metadata['nplayers'], NPLAYERS_L)
    esrb      = text_limit_string(metadata['esrb'], ESRB_L)
    plot      = text_limit_string(metadata['plot'], PLOT_L)

    p_str = "{} {} {} {} {} {} {}"
    print('Displaying metadata for title "{}"'.format(title))
    print(p_str.format(
        'Title'.ljust(TITLE_L), 'Year'.ljust(YEAR_L), 'Genre'.ljust(GENRE_L),
        'Developer'.ljust(DEVELOPER_L), 'NPlayers'.ljust(NPLAYERS_L), 'ESRB'.ljust(ESRB_L),
        'Plot'.ljust(PLOT_L)))
    print(p_str.format(
        '-'*TITLE_L, '-'*YEAR_L, '-'*GENRE_L, '-'*DEVELOPER_L, '-'*NPLAYERS_L, '-'*ESRB_L, '-'*PLOT_L))
    print(p_str.format(
        title.ljust(TITLE_L), year.ljust(YEAR_L), genre.ljust(GENRE_L), developer.ljust(DEVELOPER_L),
        nplayers.ljust(NPLAYERS_L), esrb.ljust(ESRB_L), plot.ljust(PLOT_L) ))
    print('')

def print_game_assets(image_list):
    # print('Found {} image/s'.format(len(image_list)))
    p_str = "{} {} {}"
    print(p_str.format(
        'Asset ID'.ljust(ASSET_ID_L), 'Name'.ljust(ASSET_NAME_L),
        'URL thumb'.ljust(ASSET_URL_THUMB_L)))
    print(p_str.format('-'*ASSET_ID_L, '-'*ASSET_NAME_L, '-'*ASSET_URL_THUMB_L))
    for image in image_list:
        id           = text_limit_string(text_type(image['asset_ID']), ASSET_ID_L)
        display_name = text_limit_string(image['display_name'], ASSET_NAME_L)
        url_thumb    = text_limit_string(image['url_thumb'], ASSET_URL_THUMB_L)
        print(p_str.format(
            id.ljust(ASSET_ID_L), display_name.ljust(ASSET_NAME_L),
            url_thumb.ljust(ASSET_URL_THUMB_L)))
    print('')
