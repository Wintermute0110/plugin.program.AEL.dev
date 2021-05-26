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

from resources.app.commands.mediator import AppMediator
from resources.lib import globals, settings
from resources.lib.repositories import *

logger = logging.getLogger(__name__)

@AppMediator.register('RENDER_VIEWS')
def cmd_render_views_data(args):
    kodi.notify('Rendering all views')
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        categories_repository   = CategoryRepository(uow)
        romsets_repository      = ROMSetRepository(uow)
        views_repository        = ViewRepository(globals.g_PATHS, globals.router)
        _render_root_view(categories_repository, romsets_repository, views_repository, render_sub_views=True)
        
    kodi.notify('All views rendered')
    kodi.refresh_container()

@AppMediator.register('RENDER_VIEW')
def cmd_render_view_data(args):
    kodi.notify('Rendering views')
    category_id = args['category_id'] if 'category_id' in args else None    
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        categories_repository   = CategoryRepository(uow)
        romsets_repository      = ROMSetRepository(uow)
        views_repository        = ViewRepository(globals.g_PATHS, globals.router)
                
        if category_id is None:
            _render_root_view(categories_repository, romsets_repository, views_repository, False)
        else:
            category = categories_repository.find_categories_by_parent(category_id)
            _render_category_view(category, categories_repository, romsets_repository, views_repository)
        
    kodi.notify('Selected views rendered')
    kodi.refresh_container()
   
def _render_root_view(categories_repository: CategoryRepository, romsets_repository: ROMSetRepository, 
                      views_repository: ViewRepository, render_sub_views = False):
    
    root_categories = categories_repository.find_root_categories()
    root_romsets = romsets_repository.find_root_romsets()
        
    root_data = {
        'id': '',
        'name': 'root',
        'obj_type': OBJ_CATEGORY,
        'items': []
    }
    root_items = []
    for root_category in root_categories:
        logger.debug('Processing category "{}"'.format(root_category.get_name()))
        root_items.append(_render_category_listitem(root_category))
        if render_sub_views:
            _render_category_view(root_category, categories_repository, romsets_repository, views_repository)

    for root_romset in root_romsets:
        logger.debug('Processing romset "{}"'.format(root_romset.get_name()))
        root_items.append(_render_romset_listitem(root_romset))

    logger.debug('Storing {} items in root view.'.format(len(root_items)))
    root_data['items'] = root_items
    views_repository.store_root_view(root_data)
        
def _render_category_view(category_obj: Category, categories_repository: CategoryRepository, 
                         romsets_repository: ROMSetRepository, views_repository: ViewRepository,
                         render_sub_views = False):
    
    sub_categories = categories_repository.find_categories_by_parent(category_obj.get_id())
    romsets = romsets_repository.find_romsets_by_parent(category_obj.get_id())
    
    view_data = {
        'id': category_obj.get_id(),
        'name': category_obj.get_name(),
        'obj_type': OBJ_CATEGORY,
        'items': []
    }
    view_items = []
    for sub_category in sub_categories:
        logger.debug('Processing category "{}", part of "{}"'.format(sub_category.get_name(), category_obj.get_name()))
        view_items.append(_render_category_listitem(sub_category))
        if render_sub_views:
            _render_category_view(sub_category, categories_repository)
    
    for romset in romsets:
        logger.debug('Processing romset "{}"'.format(romset.get_name()))
        view_items.append(_render_romset_listitem(romset))
        ## process roms view
        
    logger.debug('Storing {} items for category "{}" view.'.format(len(view_items), category_obj.get_name()))
    view_data['items'] = view_items
    views_repository.store_view(category_obj.get_id(), view_data)

def _render_category_listitem(category_obj: Category):
    # --- Do not render row if category finished ---
    if category_obj.is_finished() and settings.getSettingAsBool('display_hide_finished'): return

    category_name = category_obj.get_name()
    ICON_OVERLAY = 5 if category_obj.is_finished() else 4
    assets = category_obj.get_mapped_assets()

    return { 
        'id': category_obj.get_id(),
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
            'obj_type': OBJ_CATEGORY,
            'num_romsets': category_obj.num_romsets() 
        }
    }
 
def _render_romset_listitem(romset_obj: ROMSet):
    # --- Do not render row if romset finished ---
    if romset_obj.is_finished() and settings.getSettingAsBool('display_hide_finished'): return

    romset_name = romset_obj.get_name()
    ICON_OVERLAY = 5 if romset_obj.is_finished() else 4
    assets = romset_obj.get_mapped_assets()

    return { 
        'id': romset_obj.get_id(),
        'name': romset_name,
        'url': globals.router.url_for_path('collection/{}'.format(romset_obj.get_id())),
        'is_folder': True,
        'type': 'video',
        'info': {
            'title'   : romset_name,              'year'    : romset_obj.get_releaseyear(),
            'genre'   : romset_obj.get_genre(),   'studio'  : romset_obj.get_developer(),
            'rating'  : romset_obj.get_rating(),  'plot'    : romset_obj.get_plot(),
            'trailer' : romset_obj.get_trailer(), 'overlay' : ICON_OVERLAY
        },
        'art': assets,
        'properties': { 
            AEL_CONTENT_LABEL: AEL_CONTENT_VALUE_LAUNCHERS,
            'platform': romset_obj.get_platform(),
            'obj_type': OBJ_ROMSET
            #,'launcher_type': 'ROM'
        }
    }