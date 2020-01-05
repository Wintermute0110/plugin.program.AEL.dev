#!/usr/bin/python
# -*- coding: utf-8 -*-

# List Libretro BIOS list.

# --- Python standard library ---
from __future__ import unicode_literals
import copy
import json
import os
import pprint
import sys

# --- AEL modules ---
if __name__ == "__main__" and __package__ is None:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print('Adding to sys.path {0}'.format(path))
    sys.path.append(path)
from resources.utils import *
# from resources.platforms import *

# --- functions ----------------------------------------------------------------------------------
def write_txt_file(filename, text):
    with open(filename, 'w') as text_file:
        text_file.write(text)

# To export CSV all commas from string must be removed.
def remove_commas(s):
    return s.replace(',', '_')

# --- configuration ------------------------------------------------------------------------------
json_fname = 'data/Libretro_info.json'
fname_core_BIOS_txt = 'data/Libretro_core_BIOS_list.txt'
fname_core_BIOS_csv = 'data/Libretro_core_BIOS_list.csv'
fname_BIOS_core_txt = 'data/Libretro_BIOS_core_list.txt'
fname_BIOS_core_csv = 'data/Libretro_BIOS_core_list.csv'

# --- main ---------------------------------------------------------------------------------------
# --- Open JSON with data ---
with open(json_fname, 'r') as json_file:
    json_data = json.load(json_file)

# --- For each core list BIOSes of that core -----------------------------------------------------
table_str = [
    ['left', 'left', 'left', 'left', 'left'],
    ['corename', 'BIOS path', 'MD5', 'desc', 'req'],
]
num_BIOS = 0
for key in sorted(json_data, key = lambda x: json_data[x]['corename'].lower(), reverse = False):
    # Special case. It is an error in the file name.
    if key == 'info/pcsx_rearmed_libretro_neon.info':
        corename = 'pcsx_rearmed_neon'
    else:
        m = re.search('^info/([-_\w]+)_libretro.info$', key)
        if not m: raise ValueError(key)
        corename = m.group(1)
    for BIOS_dic in json_data[key]['BIOS']:
        table_str.append([
            corename, BIOS_dic['path'], BIOS_dic['md5'][0:8],
            remove_commas(BIOS_dic['desc']), str(not BIOS_dic['opt']),
        ])
        num_BIOS += 1
table_long_str_list = text_render_table(table_str)
text_long_str = '\n'.join(table_long_str_list)
print(text_long_str)
print('There are {} BIOSes'.format(num_BIOS))

# Output file in TXT and CSV format
print('\nWriting file "{}"'.format(fname_core_BIOS_txt))
write_txt_file(fname_core_BIOS_txt, text_long_str)
print('Writing file "{}"'.format(fname_core_BIOS_csv))
text_csv = '\n'.join(text_render_table_CSV(table_str))
write_txt_file(fname_core_BIOS_csv, text_csv)

# --- For each BIOS list cores that use that BIOS ------------------------------------------------
# --- Traverse list of cores and build a unique list of BIOSes ---
# Unique list of BIOS names or paths.
BIOS_list = []
for key in json_data:
    for BIOS_dic in json_data[key]['BIOS']:
        if BIOS_dic['path'] not in BIOS_list: BIOS_list.append(BIOS_dic['path'])

# Make a list of dictionaries.
BIOS_data = []
for BIOS_name in sorted(BIOS_list, key = lambda s: s.lower(), reverse = False):
    core_list = []
    for key in json_data:
        # Get core name from INFO file name.
        # Special case. It is an error in the file name.
        if key == 'info/pcsx_rearmed_libretro_neon.info':
            corename = 'pcsx_rearmed_neon'
        else:
            m = re.search('^info/([-_\w]+)_libretro.info$', key)
            if not m: raise ValueError(key)
            corename = m.group(1)
        # Check if this core uses the BIOS.
        for BIOS_dic in json_data[key]['BIOS']:
            if BIOS_name != BIOS_dic['path']: continue
            core_list.append({
                'corename' : corename,
                'opt' : BIOS_dic['opt'],
                'desc' : BIOS_dic['desc'],
                'md5' : BIOS_dic['md5'],
            })
    BIOS_data.append({
        'path' : BIOS_name,
        'core_list' : core_list
    })

# For every BIOS check that the description and MD5 files are the same.
print('\nChecking BIOS database consistency...')
flag_warnings_found = False
for BIOS_dic in BIOS_data:
    num_iter = 0
    for core_dic in BIOS_dic['core_list']:
        if num_iter == 0:
            desc_str = core_dic['desc']
            md5_str = core_dic['md5']
            first_corename = core_dic['corename']
        else:
            if desc_str != core_dic['desc']:
                print('WARNING BIOS {}, wrong description in core {} compared with {}'.format(
                    BIOS_dic['path'], core_dic['corename'], first_corename))
                flag_warnings_found = True
            if md5_str != core_dic['md5']:
                print('WARNING BIOS {}, wrong MD5 in core {} compared with {}'.format(
                    BIOS_dic['path'], core_dic['corename'], first_corename))
                flag_warnings_found = True
        num_iter += 1
if flag_warnings_found:
    print('Warnings found. Stopping.')
    # sys.exit(0)

# Generate table and CSV file.
table_str = [
    ['left', 'left', 'left', 'left', 'left'],
    ['BIOS path', 'MD5', 'desc', 'req', 'corename'],
]
for BIOS_dic in BIOS_data:
    # Short by corename
    counter = 0
    for B_dic in sorted(BIOS_dic['core_list'], key = lambda x: x['corename']):
        if counter == 0:
            table_str.append([
                BIOS_dic['path'], B_dic['md5'][0:8], remove_commas(B_dic['desc']), 
                str(not B_dic['opt']), B_dic['corename'],
            ])
        else:
            table_str.append([
                ' ', ' ', ' ', str(not B_dic['opt']), B_dic['corename']
            ])
        counter += 1
table_long_str_list = text_render_table(table_str)
text_long_str = '\n'.join(table_long_str_list)
print(text_long_str)

# Output file in TXT and CSV format
print('\nWriting file "{}"'.format(fname_BIOS_core_txt))
write_txt_file(fname_BIOS_core_txt, text_long_str)
print('Writing file "{}"'.format(fname_BIOS_core_csv))
text_csv = '\n'.join(text_render_table_CSV(table_str))
write_txt_file(fname_BIOS_core_csv, text_csv)

# Generate BIOS_core list into AEL data directory.
dest_fname = '../data/Libretro_BIOS_cores.json'
print('\nCreating file "{}"'.format(dest_fname))
with open(dest_fname, 'w') as outfile:
    outfile.write(json.dumps(BIOS_data, sort_keys = True, indent = 4))

# Warn user if problems found.
if flag_warnings_found:
    print('\nWARNING Warnings found when checking database consistency.')
