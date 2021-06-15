#!/usr/bin/python3 -B
# -*- coding: utf-8 -*-

# Get all MobyGames platform IDs and outputs JSON and CSV files.

# --- Import AEL modules ---
import os
import sys
if __name__ == "__main__" and __package__ is None:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print('Adding to sys.path {}'.format(path))
    sys.path.append(path)
from resources.utils import *
from resources.scrap import *
import common

# --- Python standard library ---
import pprint

# --- configuration ------------------------------------------------------------------------------
txt_fname = 'data/MobyGames_platforms.txt'
csv_fname = 'data/MobyGames_platforms.csv'

# --- main ---------------------------------------------------------------------------------------
set_log_level(LOG_DEBUG)

# --- Create scraper object ---
scraper_obj = MobyGames(common.settings)
scraper_obj.set_verbose_mode(False)
scraper_obj.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))
st_dic = kodi_new_status_dic()

# --- Get platforms ---
# Call to this function will write file 'assets/MobyGames_get_platforms.json'
json_data = scraper_obj.debug_get_platforms(st_dic)
common.abort_on_error(st_dic)
platform_list = json_data['platforms']
platform_dic = {p_dic['platform_name'] : p_dic['platform_id'] for p_dic in platform_list}
# pprint.pprint(platform_list)

# --- Print list ---
sl = []
sl.append('Number of MobyGames platforms {}'.format(len(platform_list)))
sl.append('')
table_str = [
    ['left', 'left'],
    ['ID', 'Name'],
]
for pname in sorted(platform_dic, reverse = False):
    try:
        table_str.append([str(platform_dic[pname]), str(pname)])
    except UnicodeEncodeError as ex:
        print('Exception UnicodeEncodeError')
        print('ID {}'.format(platform['id']))
        sys.exit(0)
table_str_list = text_render_table(table_str)
sl.extend(table_str_list)
text_str = '\n'.join(sl)
print('\n'.join(table_str_list))

# --- Output file in TXT format ---
print('\nWriting file "{}"'.format(txt_fname))
with io.open(txt_fname, 'wt', encoding = 'utf-8') as file:
    file.write(text_str)

# --- Output file in CSV format ---
text_csv_slist = text_render_table_CSV(table_str)
text_csv = '\n'.join(text_csv_slist)
print('Writing file "{}"'.format(csv_fname))
with io.open(csv_fname, 'wt', encoding = 'utf-8') as file:
    file.write(text_csv)
