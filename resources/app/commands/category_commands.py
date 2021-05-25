# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (category management)
#
# Copyright (c) 2016-2018 Wintermute0110 <wintermute0110@gmail.com>
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

from resources.app.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import *
from resources.lib.utils import kodi
from xbmcgui import ACTION_CHAPTER_OR_BIG_STEP_FORWARD

logger = logging.getLogger(__name__)

@AppMediator.register('ADD_CATEGORY')
def cmd_add_category(args):
    logger.debug('cmd_add_category() BEGIN')
    parent_id = args['category_id'] if 'category_id' in args else None
    
    # --- Get new Category name ---
    name = kodi.dialog_keyboard('New Category Name')
    if name is None: return
    
    category = Category()
    category.set_name(name)
    
    # --- Save Category ---
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        parent_category = repository.find_category(parent_id) if parent_id is not None else None
        repository.save_category(category, parent_category)
        uow.commit()
        
    kodi.notify('Category {0} created'.format(category.get_name()))
    kodi.event(method='RENDER_VIEW', data=args)
    kodi.event(method='RENDER_VIEW', data={'category_id': category.get_id()})
    
    
        
