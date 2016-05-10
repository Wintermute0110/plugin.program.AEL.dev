#!/usr/bin/python
#
# Test AEL metadata scraper
#

# Python standard library
import sys

# Import scrapers
from scrap import *

# --- main --------------------------------------------------------------------
# Print name of all scrapers
print('Short name  Fancy Name')
print('----------  ---------------------------------')
for scraper in scrapers_metadata:
    print('{:10s}  {:}'.format(scraper.name.rjust(10), scraper.fancy_name))
sys.exit(0)

# Create offline scraper object
nointro = scrap.metadata_NoIntro()

# --- Test scraper ---
nointro.initialise_scraper('Sega 32X')
nointro.get_metadata('Sonic')
nointro.get_metadata('doom')

# Another system can be loaded to replace the current one
nointro.initialise_scraper('Nintendo SNES')
nointro.get_metadata('mario')
nointro.get_metadata('castle')


# Test MAME offline scraper
mame = scrap.metadata_MAME()
mame.initialise_scraper()

mame.get_metadata('dino')
mame.get_metadata('aliens')
mame.get_metadata('spang')
mame.get_metadata('tokia')
mame.get_metadata('asdfg')

# Test TheGamesDB online scraper
GamesDB = scrap.metadata_TheGamesDB()
