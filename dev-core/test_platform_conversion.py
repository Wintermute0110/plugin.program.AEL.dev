#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Test AEL platform conversion to scraper platform names.
# Included scrapers: TheGamesDB, MobyGames, ScreenScraper.
# GameFAQs scraper is not used for now (not API available).

# AEL long name       | AEL short name | AEL compact name |
# Sega Master System  | sega-sms       | sms

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

# --- main ----------------------------------------------------------------------------------------
sl = []
sl.append('Number of AEL platforms {}'.format(len(AEL_platform_list)))
sl.append('')
table_str = [
    ['left', 'left', 'left', 'left', 'left', 'left'],
    ['AEL platform long name', 'AEL short name', 'AEL compact name',
     'TheGamesDB', 'MobyGames', 'ScreenScraper'],
]
for AEL_plat in AEL_platform_list:
    TGDB_plat = AEL_platform_to_TheGamesDB(AEL_plat)
    MobyGames_plat = AEL_platform_to_MobyGames(AEL_plat)
    ScreenScraper_plat = AEL_platform_to_ScreenScraper(AEL_plat)
    table_str.append([
        unicode(AEL_plat), '', '',
        unicode(TGDB_plat), unicode(MobyGames_plat), unicode(ScreenScraper_plat),
    ])
table_str_list = text_render_table_str(table_str)
sl.extend(table_str_list)
text_str = '\n'.join(sl)
print(text_str)

# --- Output file in TXT format ---
fname = 'data/AEL_patform_conversion.txt'
print('\nWriting file "{}"'.format(fname))
text_file = open(fname, 'w')
text_file.write(text_str)
text_file.close()

# --- Output file in CSV format ---
text_csv_slist = text_render_table_CSV_slist(table_str)
text_csv = '\n'.join(text_csv_slist)
fname = 'data/AEL_patform_conversion.csv'
print('Writing file "{}"'.format(fname))
text_file = open(fname, 'w')
text_file.write(text_csv)
text_file.close()
