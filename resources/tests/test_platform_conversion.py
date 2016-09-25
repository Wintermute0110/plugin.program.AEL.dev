#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Test AEL platforms and scraper platform names
#

# --- Python standard library ---
from __future__ import unicode_literals
import sys, os

# --- AEL modules ---
if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scrap import *

# --- main ----------------------------------------------------------------------------------------
print('{0:<28} {1:<34} {2:<9} {3:<5}'.format('AEL platform', 'TheGamesDB', 'GameFAQs', 'MobyGames'))
print('{0}'.format('-' * 90))
for AEL_plat_name in AEL_platform_list:
    TGDB_plat = AEL_platform_to_TheGamesDB(AEL_plat_name)
    GFAQ_plat = AEL_platform_to_GameFAQs(AEL_plat_name)
    MG_plat   = AEL_platform_to_MobyGames(AEL_plat_name)

    print('{0:<28} {1:<34} {2:<9} {3:<5}'.format(AEL_plat_name, TGDB_plat, GFAQ_plat, MG_plat))
