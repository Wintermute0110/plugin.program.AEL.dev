#!/usr/bin/python
# -*- coding: utf-8 -*-
# Convert Favourites XML to JSON
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

# Import AEL stuff
import sys, os
if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from disk_IO import *

# --- Configuration -------------------------------------------------------------------------------
input_filename  = 'favourites.xml'
output_filename = 'favourites.json'

# --- Main ----------------------------------------------------------------------------------------
print('Reading {0}...'.format(input_filename))
roms = fs_load_Favourites_XML(input_filename)
print('Writing {0}...'.format(output_filename))
fs_write_Favourites_JSON(output_filename, roms)
print('Done!')
