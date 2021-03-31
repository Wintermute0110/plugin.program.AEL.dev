#!/usr/bin/python -B
# -*- coding: utf-8 -*-

#
# Clean URLs in JSON data for dumping.
# Uses assets/ScreenScraper_get_gameInfo.json for testing.
#

# --- Python standard library ---
from collections import OrderedDict
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
input_fname = 'assets/ScreenScraper_gameInfo.json'
output_fname = 'assets/ScreenScraper_gameInfo_clean.json'

# --- main ---------------------------------------------------------------------------------------
# --- Load JSON data ---
print('Loading file "{}"'.format(input_fname))
f = open(input_fname, 'r')
json_str = f.read()
f.close()
json_data = json.loads(json_str)

set_log_level(LOG_DEBUG)
scraper_obj = ScreenScraper(common.settings)
scraper_obj.set_verbose_mode(False)
scraper_obj.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))
status_dic = kodi_new_status_dic('Scraper test was OK')

# json_data dictionary/list is modified by assigment.
scraper_obj._clean_JSON_for_dumping(json_data)

json_str = json.dumps(json_data, indent = 4, separators = (', ', ' : '))
log_debug('Dumping file "{0}"'.format(output_fname))
file_obj = open(output_fname, 'w')
file_obj.write(json_str.encode('utf-8'))
file_obj.close()
