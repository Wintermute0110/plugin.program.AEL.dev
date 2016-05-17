#!/usr/bin/python
#
# Test AEL fanart scraper
#

# Python standard library
import sys, os

# Import scrapers
if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scrap import *
from utils import *

# --- Scrapers to test ----------------------------------------------------------------------------
TEST_OFFLINE    = True
TEST_THEGAMESDB = False
TEST_GAMEFAQS   = False

# --- main --------------------------------------------------------------------
# Print name of all scrapers
print('Short name  Fancy Name')
print('----------  ---------------------------------')
for scraper in scrapers_fanart:
    print('{:10s}  {:}'.format(scraper.name.rjust(10), scraper.fancy_name))
