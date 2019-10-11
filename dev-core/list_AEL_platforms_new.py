#!/usr/bin/python
# -*- coding: utf-8 -*-

# List AEL platforms using the new engine object-based.
# Included scrapers: TheGamesDB, MobyGames, ScreenScraper.
# GameFAQs scraper is not used for now (not API available).

# AEL long name       | AEL short name | AEL compact name |
# Sega Master System  | sega-sms       | sms

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
from resources.utils import *
from resources.platforms import *

# --- functions ----------------------------------------------------------------------------------
def write_txt_file(filename, text):
    with open(filename, 'w') as text_file:
        text_file.write(text)

# --- configuration ------------------------------------------------------------------------------
fname_txt = 'data/AEL_platform_list_new.txt'
fname_csv = 'data/AEL_platform_list_new.csv'

# --- main ---------------------------------------------------------------------------------------
sl = []
sl.append('Number of AEL platforms {}'.format(len(AEL_platforms)))
sl.append('')
table_str = [
    ['left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left'],
    ['AEL long name', 'AEL short name', 'AEL compact name',
     'Alias of', 'DAT',
     'TheGamesDB', 'MobyGames', 'ScreenScraper', 'GameFAQs'],
]
for p_obj in AEL_platforms:
    # pprint.pprint(p_obj.long_name)
    # pprint.pprint(p_obj)

    table_str.append([
        p_obj.long_name, p_obj.short_name, p_obj.compact_name,
        unicode(p_obj.aliasof), unicode(p_obj.DAT),
        unicode(p_obj.TGDB_plat), unicode(p_obj.MG_plat), unicode(p_obj.SS_plat), unicode(p_obj.GF_plat)
    ])
# pprint.pprint(table_str)
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
