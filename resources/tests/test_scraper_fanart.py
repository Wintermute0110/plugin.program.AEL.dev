#!/usr/bin/python
#
# Test AEL fanart scraper
#

# Python standard library
import sys

# Import scrapers
from scrap import *

# --- main --------------------------------------------------------------------
# Print name of all scrapers
print('Short name  Fancy Name')
print('----------  ---------------------------------')
for scraper in scrapers_fanart:
    print('{:10s}  {:}'.format(scraper.name.rjust(10), scraper.fancy_name))
