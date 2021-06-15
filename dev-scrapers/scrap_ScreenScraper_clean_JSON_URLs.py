#!/usr/bin/python3 -B
# -*- coding: utf-8 -*-

# Clean URLs in JSON data for dumping.
# Uses assets/ScreenScraper_get_gameInfo.json for testing.

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
import collections
import pprint

# --- configuration ------------------------------------------------------------------------------
input_fname = 'assets/ScreenScraper_gameInfo.json'
output_fname = 'assets/ScreenScraper_gameInfo_clean.json'

# --- main ---------------------------------------------------------------------------------------
# --- Load JSON data ---
print('Loading file "{}"'.format(input_fname))
with io.open(input_fname, 'rt', encoding = 'utf-8') as file:
    json_str = file.read()
json_data = json.loads(json_str)

set_log_level(LOG_DEBUG)
scraper_obj = ScreenScraper(common.settings)
scraper_obj.set_verbose_mode(False)
scraper_obj.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))

# json_data dictionary/list is modified by assigment.
scraper_obj._clean_JSON_for_dumping(json_data)

json_str = json.dumps(json_data, indent = 4, separators = (', ', ' : '))
log_debug('Dumping file "{}"'.format(output_fname))
with io.open(output_fname, 'wt', encoding = 'utf-8') as file:
    file.write(json_str)
