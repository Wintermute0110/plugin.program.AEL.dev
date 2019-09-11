#!/usr/bin/python
# -*- coding: utf-8 -*-

# Test AEL platform conversion to scraper platform names.
# Included scrapers: TheGamesDB, MobyGames, ScreenScraper.
# GameFAQs scraper is not used for now (not API available).

# AEL long name       | AEL short name | AEL compact name |
# Sega Master System  | sega-sms       | sms

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
from resources.utils import *

# --- main ----------------------------------------------------------------------------------------
if len(sys.argv) < 2:
    print('First argument must be a file name.')
    sys.exit(1)
print('Calculating checksums of "{}"'.format(sys.argv[1]))
checksums = misc_calculate_checksums(sys.argv[1])
pprint.pprint(checksums)
