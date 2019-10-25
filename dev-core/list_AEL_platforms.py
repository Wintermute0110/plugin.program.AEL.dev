#!/usr/bin/python
# -*- coding: utf-8 -*-

# List AEL platforms using the new engine object-based.
# Included scrapers: TheGamesDB, MobyGames, ScreenScraper.
# GameFAQs scraper is not used for now (not API available).

# AEL long name       | AEL short name | AEL compact name |
# Sega Master System  | sega-sms       | sms

# --- Python standard library ---
from __future__ import unicode_literals
import copy
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
fname_longname_txt = 'data/AEL_platform_list_longname.txt'
fname_longname_csv = 'data/AEL_platform_list_longname.csv'
fname_shortname_txt = 'data/AEL_platform_list_shortname.txt'
fname_shortname_csv = 'data/AEL_platform_list_shortname.csv'

# --- main ---------------------------------------------------------------------------------------
header_list = []
header_list.append('Number of AEL platforms {}'.format(len(AEL_platforms)))
header_list.append('')
table_str = [
    ['left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left'],
    ['AEL long name', 'AEL short name', 'AEL compact name',
     'Alias of', 'DAT',
     'TheGamesDB', 'MobyGames', 'ScreenScraper', 'GameFAQs'],
]
header_long_list = copy.deepcopy(header_list)
header_short_list = copy.deepcopy(header_list)
table_long_str = copy.deepcopy(table_str)
table_short_str = copy.deepcopy(table_str)
for p_name in sorted(platform_long_list, key = lambda x: x.lower()):
    p_obj = AEL_platforms[platform_long_list.index(p_name)]
    table_long_str.append([
        p_obj.long_name, p_obj.short_name, p_obj.compact_name,
        unicode(p_obj.aliasof), unicode(p_obj.DAT),
        unicode(p_obj.TGDB_plat), unicode(p_obj.MG_plat), unicode(p_obj.SS_plat), unicode(p_obj.GF_plat)
    ])
for p_name in sorted(platform_short_list, key = lambda x: x.lower()):
    p_obj = AEL_platforms[platform_short_list.index(p_name)]
    table_short_str.append([
        p_obj.long_name, p_obj.short_name, p_obj.compact_name,
        unicode(p_obj.aliasof), unicode(p_obj.DAT),
        unicode(p_obj.TGDB_plat), unicode(p_obj.MG_plat), unicode(p_obj.SS_plat), unicode(p_obj.GF_plat)
    ])
table_long_str_list = text_render_table_str(table_long_str)
header_long_list.extend(table_long_str_list)
text_long_str = '\n'.join(header_long_list)
print(text_long_str)

table_short_str_list = text_render_table_str(table_short_str)
header_short_list.extend(table_short_str_list)
text_short_str = '\n'.join(header_short_list)

# --- Output file in TXT and CSV format ---
print('\nWriting file "{}"'.format(fname_longname_txt))
write_txt_file(fname_longname_txt, text_long_str)
text_csv = '\n'.join(text_render_table_CSV_slist(table_long_str))
print('Writing file "{}"'.format(fname_longname_csv))
write_txt_file(fname_longname_csv, text_csv)

print('\nWriting file "{}"'.format(fname_shortname_txt))
write_txt_file(fname_shortname_txt, text_short_str)
text_csv = '\n'.join(text_render_table_CSV_slist(table_short_str))
print('Writing file "{}"'.format(fname_shortname_csv))
write_txt_file(fname_shortname_csv, text_csv)
