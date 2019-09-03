#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# List media types (asset/artwork types or kinds) for ScreenScraper.
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

# --- Settings -----------------------------------------------------------------------------------
use_cached_ScreenScraper_get_gameInfo = True

# --- main ---------------------------------------------------------------------------------------
if use_cached_ScreenScraper_get_gameInfo:
    filename = 'assets/ScreenScraper_get_gameInfo.json'
    print('Loading file "{}"'.format(filename))
    f = open(filename, 'r')
    json_str = f.read()
    f.close()
    json_data = json.loads(json_str)
else:
    set_log_level(LOG_DEBUG)
    # --- Create scraper object ---
    scraper_obj = ScreenScraper(common.settings)
    scraper_obj.set_verbose_mode(False)
    scraper_obj.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))
    status_dic = kodi_new_status_dic('Scraper test was OK')
    # --- Get candidates ---
    # candidate_list = scraper_obj.get_candidates(*common.games['metroid'])
    # candidate_list = scraper_obj.get_candidates(*common.games['mworld'])
    candidate_list = scraper_obj.get_candidates(*common.games['sonic'], status_dic = status_dic)
    # candidate_list = scraper_obj.get_candidates(*common.games['chakan'])
    # --- Get jeu_dic and dump asset data ---
    json_data = scraper_obj.get_gameInfos_dic(candidate_list[0], status_dic = status_dic)
# pprint.pprint(json_data)
jeu_dic = json_data['response']['jeu']

# List first level dictionary values
print('\nListing jeu_dic first level dictionary keys')
for key in sorted(jeu_dic): print(key)

# --- Dump asset data ---
medias_list = jeu_dic['medias']
table = [
    ['left', 'left', 'left'],
    ['Type', 'Region', 'Format'],
]
for media_dic in medias_list:
    region = media_dic['region'] if 'region' in media_dic else None
    table.append([
        str(media_dic['type']), str(region), str(media_dic['format'])
    ])
print('\nThere are {} assets'.format(len(medias_list)))
print('\n'.join(text_render_table_str(table)))
