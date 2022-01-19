# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Commands (reporting)
#
# Copyright (c) Wintermute0110 <wintermute0110@gmail.com> / Chrisism <crizizz@gmail.com>
# 
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
from __future__ import division

import logging

from akl.utils import kodi, text

from resources.lib.commands.mediator import AppMediator

from resources.lib.repositories import CategoryRepository, ROMCollectionRepository, UnitOfWork
from resources.lib import globals

logger = logging.getLogger(__name__)

@AppMediator.register('GLOBAL_ROM_STATS')
def cmd_report_global_rom_stats(args):    
    window_title = 'Global ROM statistics'
    sl = []
    # sl.append('[COLOR violet]Launcher ROM report.[/COLOR]')
    # sl.append('')

    # --- Table header ---
    table_str = [
        ['left', 'left', 'left'],
        ['Category', 'Collection', 'ROMs'],
    ]

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        category_repository       = CategoryRepository(uow)
        romcollections_repository = ROMCollectionRepository(uow)  
        
        categories       = [*category_repository.find_all_categories()]      
        collection_count = romcollections_repository.count_collections()
        
        # Traverse categories and sort alphabetically.
        logger.debug(f'Number of categories {len(categories)}')
        logger.debug(f'Number of collections {collection_count}')
    
        for category in categories:
            # Get collection of this category alphabetically sorted.
            collections_by_category = romcollections_repository.find_romcollections_by_parent(category.get_id())
            # Render list of launchers for this category.
            for collection in collections_by_category:
                table_str.append([category.get_name(), collection.get_name(), str(collection.num_roms())])
                
        # Traverse categoryless launchers.
        root_collections = romcollections_repository.find_root_romcollections()
        for collection in root_collections:
            table_str.append(['', collection.get_name(), str(collection.num_roms())])

    # Generate table and print report
    # logger.debug(unicode(table_str))
    sl.extend(text.render_table_str(table_str))
    kodi.display_text_window_mono(window_title, '\n'.join(sl))