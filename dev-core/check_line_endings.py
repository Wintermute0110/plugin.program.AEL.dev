#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright (c) 2021 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# Checks for text end of line endings in a directory recursively.
# Default directory name is '..'.
# $ ./check_line_endings.py directory_name

# --- Addon modules ---
import os
import sys
if __name__ == "__main__" and __package__ is None:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print('Adding to sys.path "{}"'.format(path))
    sys.path.append(path)
# from resources.utils import *

# --- Python standard library ---
import codecs
import re

# --- configuration ------------------------------------------------------------------------------
TEXT_EXTENSION_SET = {
    '.css',
    '.csv',
    '.dtd',
    '.info',
    '.json',
    '.md',
    '.old',
    '.po',
    '.py',
    '.sh',
    '.txt',
    '.xml',
    '.xsp',
    '.yml',
}

BIN_EXTENSION_SET = {
    '.jpg',
    '.otf',
    '.png',
    '.pyc',
    '.pyo',
    '.svg',
    '.ttf',
}

CRED = '\033[31m'
CYELLOW = '\033[33m'
CEND = '\033[39m'

# --- functions ----------------------------------------------------------------------------------
# Line ending can be "\r\n" (Windows), "\n" (Unix), "\r" (Mac OS pre-OS X).
# Returns a tuple (unix_count, windows_count)
def count_line_endings(filename):
    unix_count = 0
    windows_count = 0
    text_bytes = open(filename, 'rb').read()
    windows_match_list = re.findall(b'\r\n', text_bytes)
    unix_match_list = re.findall(b'[^\r]\n', text_bytes)
    windows_count = len(windows_match_list)
    unix_count = len(unix_match_list)

    return (unix_count, windows_count)

# --- main ---------------------------------------------------------------------------------------
print('sys.argv {}'.format(sys.argv))
directory = '..' if len(sys.argv) < 2 else sys.argv[1]
print('Scanning directory "{}"'.format(directory))
windows_file_list = []
BOM_file_list = []
for root, dirs, files in os.walk(directory, topdown = True):
    # Ignore .git directories
    if root.find('.git') >= 0:
        # print('{}skipping directory{} {}'.format(CRED, CEND, root))
        continue
    if root.find('pdfrw') >= 0:
        print('{}skipping directory{} {}'.format(CRED, CEND, root))
        continue
    print('directory "{}"'.format(root))
    # for dir_s in dirs: print(' dir "{}"'.format(dir_s))
    for file_s in files:
        filename = os.path.join(root, file_s)
        filename_root, filename_ext = os.path.splitext(filename)
        if filename_ext == '':
            print('{}empty extension in file{} "{}"'.format(CYELLOW, CEND, filename))
        elif filename_ext in TEXT_EXTENSION_SET:
            unix_count, windows_count = count_line_endings(filename)
            if unix_count > 0 and windows_count == 0:
                print('UNIX line ending "{}"'.format(filename))
            elif unix_count == 0 and windows_count > 0:
                print('Windows line ending "{}"'.format(filename))
                windows_file_list.append(filename)
            elif unix_count == 0 and windows_count == 0:
                print('No line endings "{}"'.format(filename))
            else:
                print('Mixed line endings "{}"'.format(filename))
                print('unix_count {}, windows_count {}'.format(unix_count, windows_count))
                print('Exit')
                sys.exit(1)

            # Check if files has BOM
            header_data = open(filename, 'rb').read(16)
            if header_data.startswith(codecs.BOM_UTF8):
                print('{}BOM{} "{}"'.format(CRED, CEND, filename))
                BOM_file_list.append(filename)

        elif filename_ext in BIN_EXTENSION_SET:
            print('{}skipping binary file{} "{}"'.format(CYELLOW, CEND, filename))
        else:
            print('ERROR: Unknown file extension "{}" for file "{}"'.format(filename_ext, filename))
            sys.exit(1)

# Print files with Windows line endings.
print('\n--- List of files with Windows line endings ---')
if len(windows_file_list) > 0:
    for f in windows_file_list: print(f)
else:
    print('Found no Windows line endings in text files. Good.')

print('\n--- List of files with BOM ---')
if len(BOM_file_list) > 0:
    for f in BOM_file_list: print(f)
else:
    print('Found no BOM in text files. Good.')

sys.exit(0)
