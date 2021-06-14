#!/usr/bin/python3 -B
# -*- coding: utf-8 -*-

# List media types (asset/artwork types or kinds) for ScreenScraper.
# Currently this file is not working, I did some changes in SS object but
# didn't update this file.

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

# --- Settings -----------------------------------------------------------------------------------
use_cached_ScreenScraper_get_gameInfo = False

# --- main ---------------------------------------------------------------------------------------
if use_cached_ScreenScraper_get_gameInfo:
    filename = 'assets/ScreenScraper_get_gameInfo.json'
    print('Loading file "{}"'.format(filename))
    with io.open(filename, 'rt', encoding = 'utf-8') as file:
        json_str = file.read()
    json_data = json.loads(json_str)
else:
    set_log_level(LOG_DEBUG)
    # --- Create scraper object ---
    scraper_obj = ScreenScraper(common.settings)
    scraper_obj.set_verbose_mode(False)
    scraper_obj.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))
    scraper_obj.set_debug_checksums(True,
        '414FA339', '9db5682a4d778ca2cb79580bdb67083f',
        '48c98f7e5a6e736d790ab740dfc3f51a61abe2b5', 123456)
    st_dic = kodi_new_status_dic()
    # --- Get candidates ---
    search_term, rombase, platform = common.games['metroid']
    # search_term, rombase, platform = common.games['mworld']
    # search_term, rombase, platform = common.games['sonic_megadrive']
    # search_term, rombase, platform = common.games['sonic_genesis'] # Aliased platform
    rom_FN = FileName(rombase)
    rom_checksums_FN = FileName(rombase)
    candidate_list = scraper_obj.get_candidates(search_term, rom_FN, rom_checksums_FN, platform, st_dic)
    # --- Get jeu_dic and dump asset data ---
    json_data = scraper_obj.get_gameInfos_dic(candidate_list[0], st_dic = st_dic)
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
print('\n'.join(text_render_table(table)))
