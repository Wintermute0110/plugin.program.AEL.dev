#!/usr/bin/python
#
# Test AEL thumb scraper
#

# Python standard library
import sys

# Import scrapers
from scrap import *

# --- main --------------------------------------------------------------------
# Print name of all scrapers
print('Short name  Fancy Name')
print('----------  ---------------------------------')
for scraper in scrapers_thumb:
    print('{:10s}  {:}'.format(scraper.name.rjust(10), scraper.fancy_name))
print('')

# --- Test TheGamesDB scraper -------------------------------------------------
thegamesDB = scrapers_thumb[1]
print('Testing thumb scraper {}'.format(thegamesDB.name))


# --- Way of calling the scraper:
# --- image_list = thegamesDB.get_image_list(search_string, gamesys, region, imgsize)
#
image_list = thegamesDB.get_image_list('Super Mario World', 'Nintendo SNES', 'World', 'All')
# image_list = thegamesDB.get_image_list('Castlevania', 'Nintendo SNES', 'World', 'All')