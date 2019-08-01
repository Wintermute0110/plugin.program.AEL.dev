#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# List media types for ScreenScraper.
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

# --- main ----------------------------------------------------------------------------------------
set_log_level(LOG_DEBUG)

# --- Create scraper object ---
scraper_obj = ScreenScraper_V1(common.settings)
scraper_obj.set_verbose_mode(False)
scraper_obj.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))

# --- Get candidates ---
# candidate_list = scraper_obj.get_candidates(*common.games['metroid'])
# candidate_list = scraper_obj.get_candidates(*common.games['mworld'])
candidate_list = scraper_obj.get_candidates(*common.games['sonic'])
# candidate_list = scraper_obj.get_candidates(*common.games['chakan'])

# --- Get jeu_dic and dump asset data ---
gameInfos_dic = scraper_obj.get_gameInfos_dic(candidate_list[0])
medias_dic = gameInfos_dic['response']['jeu']['medias']
table = [
    ['left', 'left'],
    ['Media', 'Type'],
]
for key in sorted(medias_dic.keys()): table.append([str(key), str(type(medias_dic[key]))])
print('\n'.join(text_render_table_str(table)))
