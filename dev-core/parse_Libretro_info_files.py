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
    for keyword in INFO_KEYWORDS: 
        if keyword == 'notes':
            json_data[f][keyword] = []
        else:
            json_data[f][keyword] = ''

    # --- First pass ---
    # Read file line by line.
    print('\nFirst pass "{}"'.format(f))
    fp = open(f, 'r')
    for line in fp:
        line = line.strip().decode('utf-8')
        if line == '': continue
        if line[0] == '#': continue
        # print("Line '{}'".format(line))

        # Parse lines 'firmware0_desc = "panafz1.bin (Panasonic FZ-1 BIOS)" '
        m = re.search('^firmware(\d+)_(\w+)\s+=\s+"(.*)"$$', line)
        if m:
            print('Match A: "{}" "{}" "{}". Skipping.'.format(m.group(1), m.group(2), m.group(3)))
            continue

        # Parse lines 'display_name = "Atari - 5200 (Atari800)"'
        m = re.search('^([\w]+)\s+=\s+"(.*)"$', line)
        if m:
            print('Match B: "{}" "{}"'.format(m.group(1), m.group(2)))
            keyword, value = m.group(1), m.group(2)
            # Standard keyword
            if keyword not in INFO_KEYWORDS:
                print("Line '{}'".format(line))
                raise ValueError(keyword)
            if keyword == 'notes':
                json_data[f][keyword].append(value)
            else:
                json_data[f][keyword] = value
            continue

        # Parse lines 'firmware_count = 1'
        m = re.search('^([\w]+)\s+=\s+(\d*)$', line)
        if m:
            print('Match C: "{}" "{}"'.format(m.group(1), m.group(2)))
            keyword, number = m.group(1), m.group(2)
            json_data[f][keyword] = number
            continue

        # If we reach this point there is an error in the info file.
        raise ValueError(line)
    fp.close()

    # --- Second pass ---
    # Create list of BIOSes
    BIOS_list = []
    if json_data[f]['firmware_count']:
        num_BIOSes = int(json_data[f]['firmware_count'])
    else:
        print('firmware_count not defined. Core has no BIOSes')
        json_data[f]['BIOS'] = BIOS_list
        continue
    print('Core has {} BIOSes'.format(num_BIOSes))
    for i in range(num_BIOSes):
        BIOS_list.append({'desc' : '', 'path' : '', 'opt'  : '', 'md5'  : ''})
    # pprint.pprint(BIOS_list)

    print('\nSecond pass "{}"'.format(f))
    fp = open(f, 'r')
    for line in fp:
        line = line.strip().decode('utf-8')
        if line == '': continue
        if line[0] == '#': continue

        # Parse lines 'firmware0_desc = "panafz1.bin (Panasonic FZ-1 BIOS)" '
        m = re.search('^firmware(\d+)_(\w+)\s+=\s+"(.*)"$$', line)
        if m:
            print('Match A: "{}" "{}" "{}"'.format(m.group(1), m.group(2), m.group(3)))
            b_index_str, keyword_str, value_str = m.group(1), m.group(2), m.group(3)
            b_index = int(b_index_str)
            BIOS_list[b_index][keyword_str] = value_str
    fp.close()
    json_data[f]['BIOS'] = BIOS_list

# Save output JSON.
with open(json_fname, 'w') as outfile:
    outfile.write(json.dumps(json_data, sort_keys = True, indent = 4))
