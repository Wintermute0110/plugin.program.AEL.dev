# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (Precompiling the view data)
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

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals, settings
from resources.lib.repositories import *

logger = logging.getLogger(__name__)

@AppMediator.register('RENDER_VIEWS')
def cmd_render_view_data(args):
    kodi.notify('Rendering all views')
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        categories_repository = CategoryRepository(uow)
        root_categories = categories_repository.find_root_categories()

        root_data = []
        for root_category in root_categories:
            logger.debug('Processing category "{}"'.format(root_category.get_name()))
            root_data.append(_render_category_view(root_category))
            _process_category_into_container(root_category, categories_repository)

        logger.debug('Storing {} categories in root view.'.format(len(root_data)))
        globals.g_ViewRepository.store_root_view(root_data)
        uow.commit()

    kodi.notify('All views rendered')
    kodi.refresh_container()

def _process_category_into_container(category_obj: Category, categories_repository: CategoryRepository):
    sub_categories = categories_repository.find_categories_by_parent(category_obj.get_id())
    # launchers
    view_data = []
    for sub_category in sub_categories:
        logger.debug('Processing category "{}", part of "{}"'.format(sub_category.get_name(), category_obj.get_name()))
        view_data.append(_render_category_view(sub_category))
        _process_category_into_container(sub_category, categories_repository)
    
    logger.debug('Storing {} categories for category "{}" view.'.format(len(view_data), category_obj.get_name()))
    globals.g_ViewRepository.store_view(category_obj.get_id(), view_data)

def _render_category_view(category_obj: Category):
    # --- Do not render row if category finished ---
    if category_obj.is_finished() and settings.getSettingAsBool('display_hide_finished'): return

    category_name = category_obj.get_name()
    ICON_OVERLAY = 5 if category_obj.is_finished() else 4
    assets = category_obj.get_mapped_assets()

    return { 
        'name': category_name,
        'url': globals.router.url_for_path('collection/{}'.format(category_obj.get_id())),
        'is_folder': True,
        'type': 'video',
        'info': {
            'title'   : category_name,              'year'    : category_obj.get_releaseyear(),
            'genre'   : category_obj.get_genre(),   'studio'  : category_obj.get_developer(),
            'rating'  : category_obj.get_rating(),  'plot'    : category_obj.get_plot(),
            'trailer' : category_obj.get_trailer(), 'overlay' : ICON_OVERLAY
        },
        'art': assets,
        'properties': { 
            AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_CATEGORY,
            'num_romsets': category_obj.num_romsets() 
        }
    }