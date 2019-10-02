#!/usr/bin/python
# -*- coding: utf-8 -*-

# List AEL platforms using the old engine non-object-based.
# Included scrapers: TheGamesDB, MobyGames, ScreenScraper.
# GameFAQs scraper is not used for now (not API available).

# --- Python standard library ---
from __future__ import unicode_literals
import os
import sys

# --- AEL modules ---
if __name__ == "__main__" and __package__ is None:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print('Adding to sys.path {0}'.format(path))
    sys.path.append(path)
from resources.utils import *
from resources.platforms import *

# --- functions ----------------------------------------------------------------------------------
def write_txt_file(filename, text):
    with open(filename, 'w') as text_file:
        text_file.write(text)

# --- configuration ------------------------------------------------------------------------------
fname_txt = 'data/AEL_platform_list_old.txt'
fname_csv = 'data/AEL_platform_list_old.csv'

# --- main ---------------------------------------------------------------------------------------
sl = []
sl.append('Number of AEL platforms {}'.format(len(AEL_platform_list)))
sl.append('')
table_str = [
    ['left', 'left', 'left', 'left', 'left'],
    ['AEL name', 'TheGamesDB', 'MobyGames', 'ScreenScraper', 'GameFAQs'],
]
for AEL_plat in AEL_platform_list:
    TGDB_plat = AEL_platform_to_TheGamesDB(AEL_plat)
    MobyGames_plat = AEL_platform_to_MobyGames(AEL_plat)
    ScreenScraper_plat = AEL_platform_to_ScreenScraper(AEL_plat)
    GameFAQs_plat = AEL_platform_to_GameFAQs(AEL_plat)
    table_str.append([
        unicode(AEL_plat),
        unicode(TGDB_plat), unicode(MobyGames_plat),
        unicode(ScreenScraper_plat), unicode(GameFAQs_plat),
    ])
table_str_list = text_render_table_str(table_str)
sl.extend(table_str_list)
text_str = '\n'.join(sl)
print(text_str)

# --- Output file in TXT format ---
print('\nWriting file "{}"'.format(fname_txt))
write_txt_file(fname_txt, text_str)

# --- Output file in CSV format ---
text_csv = '\n'.join(text_render_table_CSV_slist(table_str))
print('Writing file "{}"'.format(fname_csv))
write_txt_file(fname_csv, text_csv)
