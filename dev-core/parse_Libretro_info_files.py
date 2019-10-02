#!/usr/bin/python
# -*- coding: utf-8 -*-

# Reads all Libretro INFO files, parses them and puts information into a JSON file.

# --- Python standard library ---
from __future__ import unicode_literals
import os
import sys

# --- AEL modules ---
if __name__ == "__main__" and __package__ is None:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print('Adding to sys.path {0}'.format(path))
    sys.path.append(path)
# from resources.utils import *
# from resources.platforms import *

# --- functions ----------------------------------------------------------------------------------

# --- configuration ------------------------------------------------------------------------------
fname_output = 'data/Libretro_info.json'

# --- main ---------------------------------------------------------------------------------------
INFO_KEYWORDS = [
    'display_name',
    'authors',
    'supported_extensions',
    'corename',
    'manufacturer',
    'categories',
    'systemname',
    'systemid',
    'database',
    'license',
    'permissions',
    'display_version',
    'supports_no_game',
    'firmware_count',
    'notes',
    'required_hw_api',
]

INFO_KEYWORDS_SPECIAL = [
    'firmwareN_desc', # N is a number.
    'firmwareN_path', # N is a number.
    'firmwareN_opt', # N is a number.
]

# --- Get list of info files. Ignore 00_example_libretro.info ---
