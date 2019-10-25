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
fname_longname_txt  = 'data/AEL_platform_list_longname.txt'
fname_longname_csv  = 'data/AEL_platform_list_longname.csv'
fname_shortname_txt = 'data/AEL_platform_list_shortname.txt'
fname_shortname_csv = 'data/AEL_platform_list_shortname.csv'
fname_category_txt  = 'data/AEL_platform_list_category.txt'
fname_category_csv  = 'data/AEL_platform_list_category.csv'

# --- main ---------------------------------------------------------------------------------------
# --- Check that the platform object list is alphabetically sorted ---
# Unknown platform is special and it's always in last position. Remove from alphabetical check.
p_longname_list = [pobj.long_name for pobj in AEL_platforms[:-1]]
p_longname_list_sorted = sorted(p_longname_list, key = lambda s: s.lower())
table_str = [ ['left', 'left', 'left'], ['Marker', 'Original', 'Sorted'] ]
not_sorted_flag = False
for i in range(len(p_longname_list)):
    a = p_longname_list[i]
    b = p_longname_list_sorted[i]
    if a != b:
        table_str.append([' *** ', a, b])
        not_sorted_flag = True
    else:
        table_str.append(['', a, b])
if not_sorted_flag:
    print('Platforms not sorted alphabetically.')
    print('\n'.join(text_render_table_str(table_str)))
    print('Exiting.')
    sys.exit(1)
print('Platforms sorted alphabetically.')

# --- List platforms sorted by long name ---
table_str = [
    ['left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left'],
    ['AEL long name', 'AEL short name', 'AEL compact name', 'Alias of', 'DAT',
     'TheGamesDB', 'MobyGames', 'ScreenScraper', 'GameFAQs'],
]
for p_obj in AEL_platforms:
    table_str.append([
        p_obj.long_name, p_obj.short_name, p_obj.compact_name,
        unicode(p_obj.aliasof), unicode(p_obj.DAT),
        unicode(p_obj.TGDB_plat), unicode(p_obj.MG_plat), unicode(p_obj.SS_plat), unicode(p_obj.GF_plat)
    ])
header_list = []
header_list.append('Number of AEL platforms {}'.format(len(AEL_platforms)))
header_list.append('')
table_str_list = text_render_table_str(table_str)
header_list.extend(table_str_list)
text_str = '\n'.join(header_list)
print(text_str)
# Output file in TXT and CSV format
print('\nWriting file "{}"'.format(fname_longname_txt))
write_txt_file(fname_longname_txt, text_str)
text_csv = '\n'.join(text_render_table_CSV_slist(table_str))
print('Writing file "{}"'.format(fname_longname_csv))
write_txt_file(fname_longname_csv, text_csv)

# --- List platforms sorted by short name ---
table_str = [
    ['left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left'],
    ['AEL long name', 'AEL short name', 'AEL compact name', 'Alias of', 'DAT',
     'TheGamesDB', 'MobyGames', 'ScreenScraper', 'GameFAQs'],
]
for p_obj in sorted(AEL_platforms, key = lambda x: x.short_name.lower(), reverse = False):
    table_str.append([
        p_obj.long_name, p_obj.short_name, p_obj.compact_name,
        unicode(p_obj.aliasof), unicode(p_obj.DAT),
        unicode(p_obj.TGDB_plat), unicode(p_obj.MG_plat), unicode(p_obj.SS_plat), unicode(p_obj.GF_plat)
    ])
header_list = []
header_list.append('Number of AEL platforms {}'.format(len(AEL_platforms)))
header_list.append('')
table_str_list = text_render_table_str(table_str)
header_list.extend(table_str_list)
text_str = '\n'.join(header_list)
# Output file in TXT and CSV format
print('\nWriting file "{}"'.format(fname_shortname_txt))
write_txt_file(fname_shortname_txt, text_str)
text_csv = '\n'.join(text_render_table_CSV_slist(table_str))
print('Writing file "{}"'.format(fname_shortname_csv))
write_txt_file(fname_shortname_csv, text_csv)

# --- List platforms sorted by category and then long name ---
table_str = [
    ['left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left'],
    ['AEL long name', 'AEL short name', 'AEL compact name', 'Alias of', 'DAT',
     'TheGamesDB', 'MobyGames', 'ScreenScraper', 'GameFAQs'],
]
for p_obj in sorted(AEL_platforms, key = lambda x: (x.category.lower(), x.long_name.lower()), reverse = False):
    table_str.append([
        p_obj.long_name, p_obj.short_name, p_obj.compact_name,
        unicode(p_obj.aliasof), unicode(p_obj.DAT),
        unicode(p_obj.TGDB_plat), unicode(p_obj.MG_plat), unicode(p_obj.SS_plat), unicode(p_obj.GF_plat)
    ])
header_list = []
header_list.append('Number of AEL platforms {}'.format(len(AEL_platforms)))
header_list.append('')
table_str_list = text_render_table_str(table_str)
header_list.extend(table_str_list)
text_str = '\n'.join(header_list)
# Output file in TXT and CSV format
print('\nWriting file "{}"'.format(fname_category_txt))
write_txt_file(fname_category_txt, text_str)
text_csv = '\n'.join(text_render_table_CSV_slist(table_str))
print('Writing file "{}"'.format(fname_category_csv))
write_txt_file(fname_category_csv, text_csv)
