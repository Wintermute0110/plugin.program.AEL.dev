#!/usr/bin/python3 -B
# -*- coding: utf-8 -*-

# Get all TGDB platform IDs and outputs JSON and CSV files.

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
txt_fname = 'data/TGDB_platforms.txt'
csv_fname = 'data/TGDB_platforms.csv'

# --- main ---------------------------------------------------------------------------------------
set_log_level(LOG_DEBUG)
st_dic = kodi_new_status_dic()

# --- Create scraper object ---
scraper_obj = TheGamesDB(common.settings)
scraper_obj.set_verbose_mode(False)
scraper_obj.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))

# --- Get platforms ---
# Call to this function will write file 'assets/TGDB_get_platforms.json'
json_data = scraper_obj.debug_get_platforms(st_dic)
common.abort_on_error(st_dic)
platforms_dic = json_data['data']['platforms']
pname_dic = {platforms_dic[platform]['name'] : platform for platform in platforms_dic}
# pprint.pprint(platforms_dic)

# --- Print list ---
sl = []
sl.append('Number of TGDB platforms {}'.format(len(platforms_dic)))
sl.append('')
table_str = [
    ['left', 'left', 'left'],
    ['ID', 'Name', 'Short name'],
]
for pname in sorted(pname_dic, reverse = False):
    platform = platforms_dic[pname_dic[pname]]
    # print('{0} {1} {2}'.format(platform['id'], platform['name'], platform['alias']))
    try:
        table_str.append([
            str(platform['id']),
            str(platform['name']),
            str(platform['alias'])
        ])
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
