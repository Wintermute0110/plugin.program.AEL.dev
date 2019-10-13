#!/usr/bin/python
# -*- coding: utf-8 -*-

# Reads all Libretro INFO files, parses them and puts information into a JSON file.

# --- Python standard library ---
from __future__ import unicode_literals
import glob
import json
import os
import pprint
import re
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
json_fname = 'data/Libretro_info.json'

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
    'database_match_archive_member',
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

json_data = {}

# --- Get list of info files. Ignore 00_example_libretro.info ---
file_list = [f for f in glob.glob('info/*.info')]
for f in sorted(file_list):
    # Skip some files.
    if f == 'info/00_example_libretro.info': continue
    json_data[f] = {}
    for keyword in INFO_KEYWORDS: json_data[f][keyword] = ''

    # Read file line by line.
    print('\nProcessing "{}"'.format(f))
    fp = open(f, 'r')
    for line in fp:
        line = line.strip().decode('utf-8')
        if line == '': continue
        if line[0] == '#': continue
        # print('Line "{}"'.format(line))

        # Parse line display_name = "Atari - 5200 (Atari800)"
        m = re.search('^([\w]+)\s+=\s+"(.*)"$', line)
        if m:
            print('Match A: "{}" "{}"'.format(m.group(1), m.group(2)))
            keyword, value = m.group(1), m.group(2)
            # Special firmware keywords
            mf = re.search('^firmware(\d+)_(\w+)$', keyword)
            if mf:
                print('Skipping keyword "{}"'.format(keyword))
                continue
            # Standard keyword
            if keyword not in INFO_KEYWORDS: raise ValueError(keyword)
            json_data[f][keyword] = value
            continue

        # Parse line firmware_count = 1
        m = re.search('^([\w]+)\s+=\s+(\d*)$', line)
        if m:
            print('Match A: "{}" "{}"'.format(m.group(1), m.group(2)))
            keyword, number = m.group(1), m.group(2)
            json_data[f][keyword] = number
            continue

        # If we reach this point there is an error in the info file.
        raise ValueError(line)
    fp.close()

# Save output JSON.
with open(json_fname, 'w') as outfile:
    outfile.write(json.dumps(json_data, sort_keys = True, indent = 4))
