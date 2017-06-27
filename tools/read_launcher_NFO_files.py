#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Reads launcher NFO files and print results.
# Useful to check if XML are valid (no invalid characters, etc.)
#

# Copyright (c) 2016 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# --- INSTRUCTIONS --------------------------------------------------------------------------------
#
# -------------------------------------------------------------------------------------------------

# --- Configuration -------------------------------------------------------------------------------
launcher_ROM_dir   = '/home/test/roms/'

# --- Python standard library ---
import xml.etree.ElementTree as ET 
import re
import sys

# NFO files pretty print
def print_NFO_dic(games_nfo_dic):
    length_title     = 60
    length_platform  = 60
    length_year      = 60
    length_publisher = 60
    length_genre     = 60
    length_plot      = 60

    # Print table header
    print("{0} {1} {2} {3} {4} {5}".format('Ar', 'Er', 'Ir', 'Or', 'Ur', 'Ar'))
    print("{0} {1} {2} {3} {4} {5}".format('-'.ljust(name_length), '-'.ljust(id_length), '-'.ljust(name_length),
                                     '-'.ljust(name_length), '-'.ljust(id_length), '-'.ljust(name_length) ))
    # Print table rows
    for game in results:
        display_name = text_limit_string(game['display_name'], name_length)
        id           = text_limit_string(game['id'], id_length)
        print("'{0}' '{1}'".format(display_name.ljust(name_length), id.ljust(id_length)))

# --- main ----------------------------------------------------------------------------------------
# Scan all NFO files in launcher, recursive. Use same functions as in plugin.
# Put read data in a dictionary
files = []
for root, dirs, filess in os.walk(launcher_path):
    for filename in fnmatch.filter(filess, '*.*'):
        files.append(os.path.join(root, filename))

# Pretty print results found
nfo_dic = {'title' : '', 'platform' : '', 'year' : '', 'publisher' : '', 
           'genre' : '', 'plot' : '' }
nfo_dic = fs_load_NFO_file_scanner(nfo_file)
