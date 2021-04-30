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

# Checks Python files for unnecessary blanks.
# If there are unneeded blanks a new file is created without the blanks. Hence,
# blanks can be easily removed with git diff.

# --- Addon modules ---
import os
import sys
if __name__ == "__main__" and __package__ is None:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print('Adding to sys.path "{}"'.format(path))
    sys.path.append(path)
# from resources.utils import *

# --- Python standard library ---
import re

# --- configuration ------------------------------------------------------------------------------
TEXT_EXTENSION_SET = {
    '.py',
}

CRED = '\033[31m'
CYELLOW = '\033[33m'
CMAGENTA = '\033[35m'
CEND = '\033[39m'

# --- functions ----------------------------------------------------------------------------------
# Line ending can be "\r\n" (Windows), "\n" (Unix), "\r" (Mac OS pre-OS X).
# Returns a tuple (unix_count, windows_count)
def check_file_for_blanks(filename):
    filename_root, filename_ext = os.path.splitext(filename)
    if filename_root.endswith('-new'):
        print('{}Skipping file{} {}'.format(CMAGENTA, CEND, filename))
        return
    f = open(filename, 'rt')
    line_list = f.readlines()
    f.close()

    linec = 0
    out_line_list = []
    num_A_cases = 0
    num_B_cases = 0
    for l in line_list:
        linec += 1
        # Check blank lines with spaces, for example
        # \s\s\s\s\n
        m = re.search(r'^( +)\n', l)
        if m:
            # print('Match A found on line {} file {}'.format(linec, filename))
            num_A_cases += 1
            out_line_list.append('\n')
            continue

        # Check blank characters at the end of the line
        m = re.search(r'^(.+[^ ])( +)$', l)
        if m:
            # print('Match B found on line {} file {}'.format(linec, filename))
            num_B_cases += 1
            out_line_list.append(m.group(1) + '\n')
            continue

        # Add line as it is.
        out_line_list.append(l)

    num_cases = num_A_cases + num_B_cases
    if num_cases:
        filename_new = filename_root + '-new' + filename_ext
        print('{}Creating file{} {}'.format(CYELLOW, CEND, filename_new))
        f = open(filename_new, 'wt')
        f.writelines(out_line_list)
        f.close()

# --- main ---------------------------------------------------------------------------------------
print('sys.argv {}'.format(sys.argv))
directory = '..' if len(sys.argv) < 2 else sys.argv[1]
print('Scanning directory "{}"'.format(directory))
windows_file_list = []
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
        if filename_ext == '.py':
            check_file_for_blanks(filename)
