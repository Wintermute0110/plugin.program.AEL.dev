#!/usr/bin/python
# -*- coding: utf-8 -*-

# Reads all Libretro INFO files, parses them and puts information into a JSON file.

# --- Python standard library ---
import glob
import json
import os
import pprint
import re
import shutil
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

        # Parse lines like 'firmware0_desc = "panafz1.bin (Panasonic FZ-1 BIOS)" '
        m = re.search('^firmware(\d+)_(\w+)\s+=\s+"(.*)"$$', line)
        if m:
            print('Match A: "{}" "{}" "{}". Skipping.'.format(m.group(1), m.group(2), m.group(3)))
            continue

        # Parse lines like 'display_name = "Atari - 5200 (Atari800)"'
        m = re.search('^([\w]+)\s+=\s+"(.*)"$', line)
        if m:
            print('Match B: "{}" "{}"'.format(m.group(1), m.group(2)))
            keyword, value = m.group(1), m.group(2)
            # Standard keyword
            if keyword not in INFO_KEYWORDS:
                print("Line '{}'".format(line))
                raise ValueError(keyword)
            if keyword == 'notes':
                if value.find('|') >= 0:
                    print('Splitting notes string into multiline string')
                    n_lines = value.split('|')
                    pprint.pprint(n_lines)
                    json_data[f][keyword].extend(n_lines)
                else:
                    json_data[f][keyword].append(value)
            elif keyword == 'supports_no_game':
                if value not in {'true', 'false'}:
                    raise TypeError('Unknown supports_no_game = {}'.format(value))
                json_data[f][keyword] = True if value == 'true' else False
            else:
                json_data[f][keyword] = value
            continue

        # Parse lines like 'firmware_count = 1'
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

    # Second pass parses the firmware lists.
    print('\nSecond pass "{}"'.format(f))
    fp = open(f, 'r')
    for line in fp:
        line = line.strip().decode('utf-8')
        if line == '': continue
        if line[0] == '#': continue

        # Parse lines like:
        # 'firmware0_desc = "panafz1.bin (Panasonic FZ-1 BIOS)"'
        # 'firmware0_path = "panafz1.bin"'
        # 'firmware0_opt = "true"'
        m = re.search('^firmware(\d+)_(\w+)\s+=\s+"(.*)"$$', line)
        if m:
            print('Match A: "{}" "{}" "{}"'.format(m.group(1), m.group(2), m.group(3)))
            b_index_str, keyword_str, value_str = m.group(1), m.group(2), m.group(3)
            b_index = int(b_index_str)
            if keyword_str == 'opt':
                if value_str not in {'true', 'false'}:
                    raise TypeError('Unknown firmwareX_opt = {}'.format(value_str))
                BIOS_list[b_index][keyword_str] = True if value_str == 'true' else False
            else:
                BIOS_list[b_index][keyword_str] = value_str
    fp.close()
    json_data[f]['BIOS'] = BIOS_list

    # Third pass searches for firmware MD5
    print('\nThird pass "{}"'.format(f))
    for BIOS_dic in json_data[f]['BIOS']:
        print('Looking MD5 for firmware "{}"'.format(BIOS_dic['path']))
        for note_line in json_data[f]['notes']:
            # Parse lines like '(!) panafz1.bin (md5): f47264dd47fe30f73ab3c010015c155b'
            m = re.search('^\(!\) (.*) \(md5\): ([0-9A-Fa-f]+)$', note_line)
            if not m: continue
            print('Match A: "{}" "{}"'.format(m.group(1), m.group(2)))
            f_path, f_MD5 = m.group(1), m.group(2)
            if BIOS_dic['path'] == f_path:
                print('Firmware {} matched with MD5 hash'.format(BIOS_dic['path']))
                BIOS_dic['md5'] = f_MD5
                break
                
# Save output JSON.
print('\nSaving file "{}"'.format(json_fname))
with open(json_fname, 'w') as outfile:
    outfile.write(json.dumps(json_data, sort_keys = True, indent = 4))

# Copy file to AEL data directory.
dest_fname = '../data/Libretro_info.json'
print('Saving file "{}"'.format(dest_fname))
shutil.copy(json_fname, dest_fname)
