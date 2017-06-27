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

# --- Python standar library ---
from __future__ import unicode_literals

# --- Import AEL modules ---
import sys, os
if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from disk_IO import *

# --- Configuration -------------------------------------------------------------------------------
input_filename  = 'favourites-v0.json'
output_filename = 'favourites-v1.json'

# --- Main ----------------------------------------------------------------------------------------
print('Reading {0}...'.format(input_filename))
old_roms = fs_load_Favourites_JSON(input_filename)

new_roms = {}
for rom_id in old_roms:
    old_rom = old_roms[rom_id]
    new_rom = {}

    new_rom['altapp']      = old_rom['altapp']
    new_rom['altarg']      = old_rom['altarg']
    new_rom['application'] = old_rom['application']
    new_rom['args']        = old_rom['args']
    new_rom['fav_status']  = old_rom['fav_status']
    new_rom['filename']    = old_rom['filename']
    new_rom['finished']    = old_rom['finished']    
    new_rom['id']          = old_rom['id']
    new_rom['launcherID']  = old_rom['launcherID']

    new_rom['m_genre']     = old_rom['genre']
    new_rom['m_name']      = old_rom['name']
    new_rom['m_plot']      = old_rom['plot']
    new_rom['m_rating']    = ''     
    new_rom['m_studio']    = old_rom['studio']
    new_rom['m_year']      = old_rom['year']
     
    new_rom['minimize']       = old_rom['minimize']
    new_rom['nointro_status'] = old_rom['nointro_status']
    new_rom['platform']       = old_rom['platform']
    new_rom['romext']         = old_rom['romext']
    new_rom['rompath']        = old_rom['rompath']
     
    new_rom['roms_default_banner']    = 's_banner'
    new_rom['roms_default_clearlogo'] = 's_clearlogo'
    new_rom['roms_default_fanart']    = 's_fanart'
    new_rom['roms_default_poster']    = 's_flyer'
    new_rom['roms_default_thumb']     = 's_title'

    new_rom['s_banner']    = ''
    new_rom['s_boxback']   = ''
    new_rom['s_boxfront']  = ''
    new_rom['s_cartridge'] = ''
    new_rom['s_clearlogo'] = ''
    new_rom['s_fanart']    = old_rom['fanart']
    new_rom['s_flyer']     = ''
    new_rom['s_manual']    = ''
    new_rom['s_map']       = ''
    new_rom['s_snap']      = ''
    new_rom['s_title']     = old_rom['thumb']
    new_rom['s_trailer']   = ''

    new_roms[rom_id] = new_rom

print('Writing {0}...'.format(output_filename))
fs_write_Favourites_JSON(output_filename, new_roms)
print('Done!')

