#!/usr/bin/python
# -*- coding: utf-8 -*-
# Updates the ROM count in the Offline Scraper

# Copyright (c) 2016-2017 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# --- Python standard library ---
from __future__ import unicode_literals
import sys

# --- AEL modules ---
from resources.utils import *
from resources.disk_IO import *
from resources.rom_audit import *
from resources.scrap_info import *

# --- Constants -----------------------------------------------------------------------------------
CURRENT_DIR = FileName('./')
GAMEDB_DIR = FileName('./GameDBInfo/')
GAMEDB_JSON_BASE_NOEXT = 'GameDB_info'

# --- main() --------------------------------------------------------------------------------------
set_log_level(LOG_DEBUG)
gamedb_info_dic = {}
for platform in AEL_platform_list:
    # print('Processing platform "{0}"'.format(platform))

    # >> Open XML file and count ROMs
    xml_file = CURRENT_DIR.pjoin(platform_AEL_to_Offline_GameDBInfo_XML[platform]).getPath()
    games = audit_load_OfflineScraper_XML(xml_file)

    # >> Count ROMs and add to dictionary
    platform_info = {'numROMs' : 0 }
    platform_info['numROMs'] = len(games)
    gamedb_info_dic[platform] = platform_info
    # print('numROMs = {0}'.format(platform_info['numROMs']))
# >> Save JSON with ROM count
fs_write_JSON_file(GAMEDB_DIR, GAMEDB_JSON_BASE_NOEXT, gamedb_info_dic)
sys.exit(0)
