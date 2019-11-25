#!/usr/bin/python
# -*- coding: utf-8 -*-

# List Libretro info stuff.

# --- Python standard library ---
from __future__ import unicode_literals
import copy
import json
import os
import pprint
import sys

# --- AEL modules ---
if __name__ == "__main__" and __package__ is None:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print('Adding to sys.path {0}'.format(path))
    sys.path.append(path)
from resources.utils import *
# from resources.platforms import *

# --- functions ----------------------------------------------------------------------------------
def write_txt_file(filename, text):
    with open(filename, 'w') as text_file:
        text_file.write(text)

# To export CSV all commas from string must be removed.
def remove_commas(s):
    return s.replace(',', '_')

# --- configuration ------------------------------------------------------------------------------
json_fname = 'data/Libretro_info.json'
fname_longname_txt = 'data/Libretro_list_longname.txt'
fname_longname_csv = 'data/Libretro_list_longname.csv'
fname_shortname_txt = 'data/Libretro_list_category.txt'
fname_shortname_csv = 'data/Libretro_list_category.csv'

# --- main ---------------------------------------------------------------------------------------
with open(json_fname, 'r') as json_file:
    json_data = json.load(json_file)

# Short alphabetically by corename
table_str = [
    ['left', 'left', 'left', 'left', 'left', 'left', 'left'],
    ['corename', 'categories', 'display_name', 'firmware_count', 'systemid', 'systemname', 'supports_no_game'],
]
for key in sorted(json_data, key = lambda x: json_data[x]['corename'].lower(), reverse = False):
    idata = json_data[key]
    table_str.append([
        remove_commas(idata['corename']), remove_commas(idata['categories']),
        remove_commas(idata['display_name']), remove_commas(idata['firmware_count']),
        remove_commas(idata['systemid']), remove_commas(idata['systemname']),
        remove_commas(idata['supports_no_game']),
    ])
table_long_str_list = text_render_table_str(table_str)
text_long_str = '\n'.join(table_long_str_list)
print(text_long_str)

# Write TXT/CSV files
print('\nWriting file "{}"'.format(fname_longname_txt))
write_txt_file(fname_longname_txt, text_long_str)
print('Writing file "{}"'.format(fname_longname_csv))
text_csv = '\n'.join(text_render_table_CSV_slist(table_str))
write_txt_file(fname_longname_csv, text_csv)

# Short alphabetically by categories and then corename
table_str = [
    ['left', 'left', 'left', 'left', 'left', 'left', 'left'],
    ['corename', 'categories', 'display_name', 'firmware_count', 'systemid', 'systemname', 'supports_no_game'],
]
for key in sorted(json_data,
    key = lambda x: (json_data[x]['categories'].lower(), json_data[x]['corename'].lower()), reverse = False):
    idata = json_data[key]
    table_str.append([
        remove_commas(idata['corename']), remove_commas(idata['categories']),
        remove_commas(idata['display_name']), remove_commas(idata['firmware_count']),
        remove_commas(idata['systemid']), remove_commas(idata['systemname']),
        remove_commas(idata['supports_no_game']),
    ])
table_short_str_list = text_render_table_str(table_str)
text_short_str = '\n'.join(table_short_str_list)

# Write TXT/CSV files
print('\nWriting file "{}"'.format(fname_shortname_txt))
write_txt_file(fname_shortname_txt, text_short_str)
print('Writing file "{}"'.format(fname_shortname_csv))
text_csv = '\n'.join(text_render_table_CSV_slist(table_str))
write_txt_file(fname_shortname_csv, text_csv)
