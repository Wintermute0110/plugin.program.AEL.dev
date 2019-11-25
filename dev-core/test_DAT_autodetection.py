#!/usr/bin/python -B
# -*- coding: utf-8 -*-

# Test the autodetection of No-Intro and Redump files.

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
from resources.platforms import *
from resources.utils import *

# --- configuration ------------------------------------------------------------------------------
fname_txt  = 'data/test_DAT_autodetection.txt'
fname_csv  = 'data/test_DAT_autodetection.csv'
settings = {
    'audit_nointro_dir' : '/cygdrive/e/AEL-stuff/AEL-DATs-No-Intro/',
    'audit_redump_dir' : '/cygdrive/e/AEL-stuff/AEL-DATs-Redump/',
}

# --- functions ----------------------------------------------------------------------------------
def write_txt_file(filename, text):
    with open(filename, 'w') as text_file:
        text_file.write(text)

# --- main ----------------------------------------------------------------------------------------
NOINTRO_PATH_FN = FileName(settings['audit_nointro_dir'])
if not NOINTRO_PATH_FN.exists():
    print('No-Intro DAT directory not found. Please set it up in AEL addon settings.')
    sys.exit(1)
REDUMP_PATH_FN = FileName(settings['audit_redump_dir'])
if not REDUMP_PATH_FN.exists():
    print('No-Intro DAT directory not found. Please set it up in AEL addon settings.')
    sys.exit(1)

# --- Table header ---
table_str = [
    ['left', 'left', 'left', 'left'],
    ['Platform', 'aliasof', 'DAT type', 'DAT file'],
]

# --- Scan files in DAT dirs ---
NOINTRO_DAT_list = NOINTRO_PATH_FN.scanFilesInPath('*.dat')
REDUMP_DAT_list = REDUMP_PATH_FN.scanFilesInPath('*.dat')
# Some debug code
# for fname in NOINTRO_DAT_list: log_debug(fname)

# --- Autodetect files ---
# 1) Traverse all platforms.
# 2) Autodetect DATs for No-Intro or Redump platforms only.
# AEL_platforms_t = AEL_platforms[0:4]
slist = []
for platform in AEL_platforms:
    if platform.DAT == DAT_NOINTRO:
        fname = misc_look_for_NoIntro_DAT(platform, NOINTRO_DAT_list)
        DAT_str = FileName(fname).getBase() if fname else 'No-Intro DAT not found'
        table_str.append([platform.compact_name, str(platform.aliasof), platform.DAT, DAT_str])
    elif platform.DAT == DAT_REDUMP:
        fname = misc_look_for_Redump_DAT(platform, REDUMP_DAT_list)
        DAT_str = FileName(fname).getBase() if fname else 'Redump DAT not found'
        table_str.append([platform.compact_name, str(platform.aliasof), platform.DAT, DAT_str])

# Print report
slist.extend(text_render_table_str(table_str))
text_str = '\n'.join(slist).encode('utf-8')
print(text_str)
print('\nWriting file "{}"'.format(fname_txt))
write_txt_file(fname_txt, text_str)
text_csv = '\n'.join(text_render_table_CSV_slist(table_str))
print('Writing file "{}"'.format(fname_csv))
write_txt_file(fname_csv, text_csv)
