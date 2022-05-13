#!/usr/bin/python3 -B
# -*- coding: utf-8 -*-

# Get all ScreenScraper platform IDs and outputs JSON and CSV files.

# --- Import AEL modules ---
import os
import sys
if __name__ == "__main__" and __package__ is None:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print('Adding to sys.path {}'.format(path))
    sys.path.append(path)
import resources.const as const
import resources.log as log
import resources.misc as misc
import resources.utils as utils
import resources.kodi as kodi
import resources.scrap as scrap
import common

# --- Python standard library ---
import io
import pprint

# --- configuration ------------------------------------------------------------------------------
txt_fname = 'data/ScreenScraper_platforms.txt'
csv_fname = 'data/ScreenScraper_platforms.csv'

# --- main ---------------------------------------------------------------------------------------
log.set_log_level(log.LOG_DEBUG)
st = kodi.new_status_dic()

# --- Create scraper object ---
scraper = scrap.ScreenScraper(common.settings)
scraper.set_verbose_mode(False)
scraper.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))

# --- Get platforms ---
# Call to this function will write file 'assets/ScreenScraper_get_platforms.json'
json_data = scraper.debug_get_platforms(st)
common.abort_on_error(st)
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
            str(p_dic['id']), p_name, p_dic['type'], p_dic['romtype'], p_dic['supporttype']])
    except UnicodeEncodeError as ex:
        print('Exception UnicodeEncodeError')
        print('ID {}'.format(platform['id']))
        sys.exit(0)
table_str_list = misc.render_table(table_str)
sl.extend(table_str_list)
text_str = '\n'.join(sl)
print('\n'.join(table_str_list))

# --- Output file in TXT format ---
print('Writing file "{}"'.format(txt_fname))
with io.open(txt_fname, 'wt', encoding = 'utf-8') as file:
    file.write(text_str)

# --- Output file in CSV format ---
text_csv_slist = misc.render_table_CSV(table_str)
text_csv = '\n'.join(text_csv_slist)
print('Writing file "{}"'.format(csv_fname))
with io.open(csv_fname, 'wt', encoding = 'utf-8') as file:
    file.write(text_csv)
