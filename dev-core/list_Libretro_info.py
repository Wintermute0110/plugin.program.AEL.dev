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

# --- configuration ------------------------------------------------------------------------------
json_fname = 'data/Libretro_info.json'
fname_longname_txt = 'data/Libretro_longname.txt'
fname_longname_csv = 'data/Libretro_longname.csv'
fname_shortname_txt = 'data/Libretro_shortname.txt'
fname_shortname_csv = 'data/Libretro_shortname.csv'

# --- main ---------------------------------------------------------------------------------------
with open(json_fname, 'r') as json_file:
    json_data = json.load(json_file)
table_str = [
    ['left', 'left', 'left', 'left', 'left', 'left', 'left'],
    ['corename', 'categories', 'display_name', 'firmware_count', 'systemid', 'systemname', 'supports_no_game'],
]
table_long_str = copy.deepcopy(table_str)
for key in sorted(json_data, key = lambda x: json_data[x]['corename'].lower(), reverse = False):
    idata = json_data[key]
    table_long_str.append([
        idata['corename'], idata['categories'], idata['display_name'],
        idata['firmware_count'], idata['systemid'], idata['systemname'],
        idata['supports_no_game'],
    ])
table_long_str_list = text_render_table_str(table_long_str)
text_long_str = '\n'.join(table_long_str_list)
print(text_long_str)

table_short_str = copy.deepcopy(table_str)
for key in sorted(json_data, key = lambda x: (json_data[x]['categories'].lower(), json_data[x]['corename'].lower()), reverse = False):
    idata = json_data[key]
    table_short_str.append([
        idata['corename'], idata['categories'], idata['display_name'],
        idata['firmware_count'], idata['systemid'], idata['systemname'],
        idata['supports_no_game'],
    ])
table_short_str_list = text_render_table_str(table_short_str)
text_short_str = '\n'.join(table_short_str_list)

# --- Output file in TXT and CSV format ---
print('\nWriting file "{}"'.format(fname_longname_txt))
write_txt_file(fname_longname_txt, text_long_str)
print('Writing file "{}"'.format(fname_longname_csv))
text_csv = '\n'.join(text_render_table_CSV_slist(table_long_str))
write_txt_file(fname_longname_csv, text_csv)

print('\nWriting file "{}"'.format(fname_shortname_txt))
write_txt_file(fname_shortname_txt, text_short_str)
print('Writing file "{}"'.format(fname_shortname_csv))
text_csv = '\n'.join(text_render_table_CSV_slist(table_short_str))
write_txt_file(fname_shortname_csv, text_csv)
