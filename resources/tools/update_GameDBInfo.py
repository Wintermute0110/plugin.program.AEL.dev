#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Updated GameDBInfo XML (copies them to correct place).
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

import sys
import os
import shutil

# --- Import scrapers ---
if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scrap import *
from utils import *


# --- Main ----------------------------------------------------------------------------------------
curr_dir = os.getcwd()
print('Current directory is "{}"'.format(curr_dir))
addon_dir = curr_dir.replace('/resources/tools', '/')
print('Addon directory is "{}"'.format(addon_dir))

# Traverse list of platforms
for platform in AEL_platform_list:
    if platform in platform_AEL_to_Offline_GameDBInfo_XML:
        print('platform "{}" in Offline_GameDBInfo'.format(platform))
        
        # Check if source file exists
        dest_dir_raw = platform_AEL_to_Offline_GameDBInfo_XML[platform]
        file_name = dest_dir_raw.replace('resources/data/GameDBInfo/', '')
        source_file = addon_dir + 'resources/tools/Game-database-info/xml files/' + file_name
        dest_file = addon_dir + 'resources/data/GameDBInfo/' + file_name
        # print('dest_dir_raw "{}'.format(dest_dir_raw))
        # print('file_name    "{}'.format(file_name))
        print('source_file  "{}'.format(source_file))
        print('dest_file    "{}'.format(dest_file))

        # Skip MAME.xml
        if file_name == 'MAME.xml': continue

        # Skip invalid files
        if file_name == '': continue

        # Copy to destination
        shutil.copy(source_file, dest_file)

    else:
        print('platform "{}" not in Offline_GameDBInfo'.format(platform))
