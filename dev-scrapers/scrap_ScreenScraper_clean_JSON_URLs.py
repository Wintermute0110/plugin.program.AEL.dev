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
import resources.const as const
import resources.log as log
import resources.misc as misc
import resources.utils as utils
import resources.kodi as kodi
import resources.scrap as scrap
import common

# --- Python standard library ---
import collections
import io
import json
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

log.set_log_level(log.LOG_DEBUG)
scraper = scrap.ScreenScraper(common.settings)
scraper.set_verbose_mode(False)
scraper.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))

# json_data dictionary/list is modified by assigment.
scraper._clean_JSON_for_dumping(json_data)

json_str = json.dumps(json_data, indent = 4, separators = (', ', ' : '))
log.debug('Dumping file "{}"'.format(output_fname))
with io.open(output_fname, 'wt', encoding = 'utf-8') as file:
    file.write(json_str)
