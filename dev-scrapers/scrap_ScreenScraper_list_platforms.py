#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Get all ScreenScraper platform IDs and outputs JSON and CSV files.
#

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
from resources.scrap import *
from resources.utils import *
import common

# --- configuration ------------------------------------------------------------------------------
txt_fname = 'data/ScreenScraper_platforms.txt'
csv_fname = 'data/ScreenScraper_platforms.csv'

# --- main ---------------------------------------------------------------------------------------
set_log_level(LOG_DEBUG)

# --- Create scraper object ---
scraper_obj = ScreenScraper(common.settings)
scraper_obj.set_verbose_mode(False)
scraper_obj.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))
status_dic = kodi_new_status_dic('Scraper test was OK')

# --- Get platforms ---
# Call to this function will write file 'assets/ScreenScraper_get_platforms.json'
json_data = scraper_obj.debug_get_platforms(status_dic)
if not status_dic['status']:
    print('SCRAPER ERROR: "' + status_dic['msg'] + '"')
    sys.exit(0)
# platform_list is a list of dictionaries
platform_list = json_data['response']['systemes']
platform_dic = {p_dic['noms']["nom_eu"] : p_dic for p_dic in platform_list}
# pprint.pprint(platform_list)

# --- Print list ---
sl = []
sl.append('Number of ScreenScraper platforms {}'.format(len(platform_list)))
sl.append('')
table_str = [
    ['left', 'left', 'left', 'left', 'left'],
    ['ID', 'Name', 'Type', 'ROM type', 'Support type'],
]
for p_name in sorted(platform_dic, reverse = False):
    p_dic = platform_dic[p_name]
    try:
        table_str.append([
            unicode(p_dic['id']), p_name, p_dic['type'], p_dic['romtype'], p_dic['supporttype']])
    except UnicodeEncodeError as ex:
        print('Exception UnicodeEncodeError')
        print('ID {0}'.format(platform['id']))
        sys.exit(0)
table_str_list = text_render_table_str(table_str)
sl.extend(table_str_list)
text_str = '\n'.join(sl)
print('\n'.join(table_str_list))

# --- Output file in TXT format ---
print('\nWriting file "{}"'.format(txt_fname))
text_file = open(txt_fname, 'w')
text_file.write(text_str.encode('utf8'))
text_file.close()

# --- Output file in CSV format ---
text_csv_slist = text_render_table_CSV_slist(table_str)
text_csv = '\n'.join(text_csv_slist)
print('Writing file "{}"'.format(csv_fname))
text_file = open(csv_fname, 'w')
text_file.write(text_csv.encode('utf8'))
text_file.close()
