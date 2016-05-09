#!/usr/bin/python
#
# Test AEL metadata scraper
#

# Import scrapers
import scrap

# --- main --------------------------------------------------------------------

# Create offline scraper object
scrap_nointro = scrap.metadata_NoIntro()

# --- Test scraper ---
scrap_nointro.initialise_scraper('Sega 32X')
scrap_nointro.get_metadata('Sonic')
scrap_nointro.get_metadata('doom')

# --- Another system can be loaded to replace the current one ---
scrap_nointro.initialise_scraper('Nintendo SNES')
scrap_nointro.get_metadata('mario')
scrap_nointro.get_metadata('castle')


# Test MAME offline scraper
scrap_mame = scrap.metadata_MAME()
scrap_mame.initialise_scraper()

scrap_mame.get_metadata('dino')
scrap_mame.get_metadata('aliens')
scrap_mame.get_metadata('spang')
scrap_mame.get_metadata('tokia')
scrap_mame.get_metadata('asdfg')
