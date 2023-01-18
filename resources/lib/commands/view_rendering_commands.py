# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Commands (Precompiling the view data)
#
# Copyright (c) Chrisism <crizizz@gmail.com>
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

from akl import constants, settings
from akl.utils import kodi

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import UnitOfWork, CategoryRepository, ROMCollectionRepository, ROMsRepository, ViewRepository

from resources.lib.domain import ROM, ROMCollection, Category
from resources.lib.domain import VirtualCollectionFactory, VirtualCategoryFactory

logger = logging.getLogger(__name__)


@AppMediator.register('RENDER_VIEWS')
def cmd_render_views_data(args):
    kodi.notify('Rendering all views')
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        categories_repository = CategoryRepository(uow)
        romcollections_repository = ROMCollectionRepository(uow)
        roms_repository = ROMsRepository(uow)
        views_repository = ViewRepository(globals.g_PATHS)
        
        _render_root_view(categories_repository, romcollections_repository, roms_repository, views_repository, render_sub_views=True)
        
    kodi.notify('All views rendered')
    kodi.refresh_container()


@AppMediator.register('RENDER_CATEGORY_VIEW')
def cmd_render_view_data(args):
    kodi.notify('Rendering views')
    category_id = args['category_id'] if 'category_id' in args else None
    render_recursive = args['render_recursive'] if 'render_recursive' in args else False
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        categories_repository = CategoryRepository(uow)
        romcollections_repository = ROMCollectionRepository(uow)
        roms_repository = ROMsRepository(uow)
        views_repository = ViewRepository(globals.g_PATHS)
                
        if category_id is None or category_id == constants.VCATEGORY_ADDONROOT_ID:
            _render_root_view(categories_repository, romcollections_repository, roms_repository, views_repository, render_recursive)
        else:
            category = categories_repository.find_category(category_id)
            _render_category_view(category, categories_repository, romcollections_repository, roms_repository, views_repository)
        
    kodi.notify('Selected views rendered')
    kodi.refresh_container()

@AppMediator.register('RENDER_VIRTUAL_VIEWS')
def cmd_render_virtual_views(args):
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        categories_repository     = CategoryRepository(uow)
        romcollections_repository = ROMCollectionRepository(uow)
        roms_repository           = ROMsRepository(uow)
        views_repository          = ViewRepository(globals.g_PATHS)              
        
        # cleanup first
        views_repository.cleanup_all_virtual_category_views()
                
        root_vcategory = VirtualCategoryFactory.create(constants.VCATEGORY_ROOT_ID)
        logger.debug('Processing root virtual category')
        _render_category_view(root_vcategory, categories_repository, romcollections_repository, 
                                roms_repository, views_repository, True)  

        for vcollection_id in constants.VCOLLECTIONS:
            vcollection = VirtualCollectionFactory.create(vcollection_id)
            logger.debug(f'Processing virtual collection "{vcollection.get_name()}"')
            collection_view_data = _render_romcollection_view(vcollection, roms_repository)
            views_repository.store_view(vcollection.get_id(), vcollection.get_type(), collection_view_data)        
        
        for vcategory_id in constants.VCATEGORIES:
            vcategory = VirtualCategoryFactory.create(vcategory_id)
                        
            kodi.notify(f'Rendering virtual category "{vcategory.get_name()}"')
            _render_category_view(vcategory, categories_repository, romcollections_repository, roms_repository, views_repository)
   
    kodi.notify('Virtual views rendered')
    kodi.refresh_container()

@AppMediator.register('RENDER_VCATEGORY_VIEWS')
def cmd_render_vcategory(args):
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        categories_repository     = CategoryRepository(uow)
        romcollections_repository = ROMCollectionRepository(uow)
        roms_repository           = ROMsRepository(uow)
        views_repository          = ViewRepository(globals.g_PATHS)              
        
        # cleanup first
        views_repository.cleanup_all_virtual_category_views()
        
        for vcategory_id in constants.VCATEGORIES:
            vcategory = VirtualCategoryFactory.create(vcategory_id)
                        
            kodi.notify(f'Rendering virtual category "{vcategory.get_name()}"')
            _render_category_view(vcategory, categories_repository, romcollections_repository, roms_repository, views_repository)
        
            kodi.notify(f'{vcategory.get_name()} view rendered')
    kodi.refresh_container()
    
@AppMediator.register('RENDER_VCATEGORY_VIEW')
def cmd_render_vcategory(args):
    vcategory_id = args['vcategory_id'] if 'vcategory_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        categories_repository     = CategoryRepository(uow)
        romcollections_repository = ROMCollectionRepository(uow)
        roms_repository           = ROMsRepository(uow)
        views_repository          = ViewRepository(globals.g_PATHS)  
        
        vcategory = VirtualCategoryFactory.create(vcategory_id)
        
        if vcategory is None:
            kodi.notify_warn(f"Cannot find virtual category '{vcategory_id}'")
            return
        
        # cleanup first
        views_repository.cleanup_virtual_category_views(vcategory.get_id())
        
        kodi.notify(f'Rendering virtual category "{vcategory.get_name()}"')
        _render_category_view(vcategory, categories_repository, romcollections_repository, roms_repository, views_repository)
    
        kodi.notify('{} view rendered'.format(vcategory.get_name()))
    kodi.refresh_container()

@AppMediator.register('RENDER_ROMCOLLECTION_VIEW')
def cmd_render_romcollection_view_data(args):
    kodi.notify('Rendering romcollection views')
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romcollections_repository = ROMCollectionRepository(uow)
        roms_repository           = ROMsRepository(uow)
        views_repository          = ViewRepository(globals.g_PATHS)
             
        romcollection = romcollections_repository.find_romcollection(romcollection_id)    
        collection_view_data = _render_romcollection_view(romcollection, roms_repository)
        views_repository.store_view(romcollection.get_id(), romcollection.get_type(), collection_view_data)  
    
    kodi.notify('Selected views rendered')
    kodi.refresh_container()


@AppMediator.register('RENDER_VCOLLECTION_VIEW')
def cmd_render_vcollection(args):
    vcollection_id = args['vcollection_id'] if 'vcollection_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        roms_repository = ROMsRepository(uow)
        views_repository = ViewRepository(globals.g_PATHS)
        
        vcollection = VirtualCollectionFactory.create(vcollection_id)
                
        kodi.notify(f'Rendering virtual collection "{vcollection.get_name()}"')
        collection_view_data = _render_romcollection_view(vcollection, roms_repository)
        views_repository.store_view(vcollection.get_id(), vcollection.get_type(), collection_view_data)  
    
        kodi.notify('{} view rendered'.format(vcollection.get_name()))
    kodi.refresh_container()


@AppMediator.register('RENDER_ROM_VIEWS')
def cmd_render_rom_views(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        roms_repository           = ROMsRepository(uow)
        romcollections_repository = ROMCollectionRepository(uow)
        views_repository          = ViewRepository(globals.g_PATHS)

        rom_obj = roms_repository.find_rom(rom_id)     
        kodi.notify(f'Rendering all views containing ROM#{rom_obj.get_rom_identifier()}')

        romcollections = romcollections_repository.find_romcollections_by_rom(rom_id)
        for romcollection in romcollections:
            collection_view_data = _render_romcollection_view(romcollection, roms_repository)
            views_repository.store_view(romcollection.get_id(), romcollection.get_type(), collection_view_data)
    
        for vcollection_id in constants.VCOLLECTIONS:
            vcollection = VirtualCollectionFactory.create(vcollection_id)
            collection_view_data = _render_romcollection_view(vcollection, roms_repository)
            views_repository.store_view(vcollection.get_id(), vcollection.get_type(), collection_view_data)   
    
    kodi.notify('Views rendered')
    kodi.refresh_container()
    
@AppMediator.register('CLEANUP_VIEWS')
def cmd_cleanup_views(args):    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        categories_repository      = CategoryRepository(uow)
        romcollections_repository  = ROMCollectionRepository(uow)
        views_repository           = ViewRepository(globals.g_PATHS)
        
        categories = categories_repository.find_all_categories()
        romcollections = romcollections_repository.find_all_romcollections()
        
        category_ids = list(c.get_id() for c in categories)
        romcollection_ids = list(r.get_id() for r in romcollections)
       
        views_repository.cleanup_views(category_ids + romcollection_ids)

def cmd_render_virtual_collection(vcategory_id: str, collection_value: str) -> dict:
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    viewdata = None
    with uow:
        roms_repository = ROMsRepository(uow)
        
        vcollection = VirtualCollectionFactory.create_by_category(vcategory_id, collection_value)
        viewdata = _render_romcollection_view(vcollection, roms_repository)
    return viewdata


# -------------------------------------------------------------------------------------------------
# Rendering of views (containers)
# -------------------------------------------------------------------------------------------------
def _render_root_view(categories_repository: CategoryRepository, romcollections_repository: ROMCollectionRepository,
                      roms_repository: ROMsRepository, views_repository: ViewRepository,
                      render_sub_views=False):
    
    root_categories = categories_repository.find_root_categories()
    root_romcollections = romcollections_repository.find_root_romcollections()
    root_roms = roms_repository.find_root_roms()

    root_data = {
        'id': constants.VCATEGORY_ADDONROOT_ID,
        'name': 'Root',
        'obj_type': constants.OBJ_CATEGORY,
        'items': []
    }
    root_items = []
    for root_category in root_categories:
        logger.debug(f'Processing category "{root_category.get_name()}"')
        root_items.append(_render_category_listitem(root_category))
        if render_sub_views:
            _render_category_view(root_category, categories_repository, romcollections_repository, 
                                  roms_repository, views_repository, render_sub_views)

    for root_romcollection in root_romcollections:
        logger.debug(f'Processing romcollection "{root_romcollection.get_name()}"')
        root_items.append(_render_romcollection_listitem(root_romcollection))
        if render_sub_views:
            collection_view_data = _render_romcollection_view(root_romcollection, roms_repository)
            views_repository.store_view(root_romcollection.get_id(), root_romcollection.get_type(), collection_view_data)

    for rom in root_roms:
        try:
            root_items.append(render_rom_listitem(rom))
        except Exception:
            logger.exception(f"Exception while rendering list item ROM '{rom.get_name()}'")                  

    root_vcategory = VirtualCategoryFactory.create(constants.VCATEGORY_ROOT_ID)
    logger.debug('Processing root virtual category')
    root_items.append(_render_category_listitem(root_vcategory))
    if render_sub_views:
        _render_category_view(root_vcategory, categories_repository, romcollections_repository,
                              roms_repository, views_repository, render_sub_views)

    for vcollection_id in constants.VCOLLECTIONS:
        vcollection = VirtualCollectionFactory.create(vcollection_id)
        logger.debug(f'Processing virtual collection "{vcollection.get_name()}"')
        root_items.append(_render_romcollection_listitem(vcollection))
        collection_view_data = _render_romcollection_view(vcollection, roms_repository)
        views_repository.store_view(vcollection.get_id(), vcollection.get_type(), collection_view_data)

    logger.debug('Storing {} items in root view.'.format(len(root_items)))
    root_data['items'] = root_items
    views_repository.store_root_view(root_data)


def _render_category_view(category_obj: Category, categories_repository: CategoryRepository,
                          romcollections_repository: ROMCollectionRepository, roms_repository: ROMsRepository,
                          views_repository: ViewRepository, render_sub_views=False):
    
    sub_categories = categories_repository.find_categories_by_parent(category_obj.get_id())
    romcollections = romcollections_repository.find_romcollections_by_parent(category_obj.get_id())
    roms = roms_repository.find_roms_by_category(category_obj)
    
    view_data = {
        'id': category_obj.get_id(),
        'parent_id': category_obj.get_parent_id(),
        'name': category_obj.get_name(),
        'obj_type': category_obj.get_type(),
        'items': []
    }
    view_items = []
    for sub_category in sub_categories:
        if sub_category is None:
            continue
        logger.debug(f'Processing category "{sub_category.get_name()}", part of "{category_obj.get_name()}"')
        view_items.append(_render_category_listitem(sub_category))
        if render_sub_views:
            _render_category_view(sub_category, categories_repository, romcollections_repository, roms_repository,
                                  views_repository, render_sub_views)
    
    for romcollection in romcollections:
        logger.debug(f"Processing romcollection '{romcollection.get_name()}'")
        try:
            view_items.append(_render_romcollection_listitem(romcollection))
        except Exception:
            logger.exception(f"Exception while rendering list item ROM Collection '{romcollection.get_name()}'")
            kodi.notify_error(f"Failed to process ROM collection {romcollection.get_name()}")
        if render_sub_views and not category_obj.get_type() == constants.OBJ_CATEGORY_VIRTUAL:
            collection_view_data = _render_romcollection_view(romcollection, roms_repository)
            views_repository.store_view(romcollection.get_id(), romcollection.get_type(), collection_view_data)

    for rom in roms:
        try:
            view_items.append(render_rom_listitem(rom))
        except Exception:
            logger.exception(f"Exception while rendering list item ROM '{rom.get_name()}'")
                  
    logger.debug(f'Storing {len(view_items)} items for category "{category_obj.get_name()}" view.')
    view_data['items'] = view_items
    views_repository.store_view(category_obj.get_id(), category_obj.get_type(), view_data)  


def _render_romcollection_view(romcollection_obj: ROMCollection, roms_repository: ROMsRepository) -> dict:
    roms = roms_repository.find_roms_by_romcollection(romcollection_obj)
    view_data = {
        'id': romcollection_obj.get_id(),
        'parent_id': romcollection_obj.get_parent_id(),
        'name': romcollection_obj.get_name(),
        'properties': {
            'platform': romcollection_obj.get_platform(),
            'boxsize': romcollection_obj.get_box_sizing()
        },
        'obj_type': romcollection_obj.get_type(),
        'items': []
    }
    view_items = []
    for rom in roms:
        try:
            rom.apply_romcollection_asset_mapping(romcollection_obj)
            view_items.append(render_rom_listitem(rom))
        except Exception:
            logger.exception(f'Exception while rendering list item ROM "{rom.get_name()}"')
        
    logger.debug(f'Found {len(view_items)} items for romcollection "{romcollection_obj.get_name()}" view.')
    view_data['items'] = view_items
    return view_data


# -------------------------------------------------------------------------------------------------
# Rendering of list items per view
# -------------------------------------------------------------------------------------------------
def _render_category_listitem(category_obj: Category) -> dict:
    # --- Do not render row if category finished ---
    if category_obj.is_finished() and \
            (category_obj.get_type() in constants.OBJ_VIRTUAL_TYPES or settings.getSettingAsBool('display_hide_finished')): 
        return

    category_name = category_obj.get_name()
    ICON_OVERLAY = 5 if category_obj.is_finished() else 4
    assets = category_obj.get_view_assets()

    url_prefix = 'category'
    if category_obj.get_type() == constants.OBJ_CATEGORY_VIRTUAL:
        url_prefix = 'category/virtual'
        
    return { 
        'id': category_obj.get_id(),
        'name': category_name,
        'url': globals.router.url_for_path('{}/{}'.format(url_prefix, category_obj.get_id())),
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
            constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_CATEGORY,
            'obj_type': category_obj.get_type(),
            'num_romcollections': category_obj.num_romcollections() 
        }
    }


def _render_romcollection_listitem(romcollection_obj: ROMCollection) -> dict:
    # --- Do not render row if romcollection finished ---
    if romcollection_obj.is_finished() and \
            (romcollection_obj.get_type() in constants.OBJ_VIRTUAL_TYPES or settings.getSettingAsBool('display_hide_finished')): 
        return

    romcollection_name = romcollection_obj.get_name()
    ICON_OVERLAY = 5 if romcollection_obj.is_finished() else 4
    assets = romcollection_obj.get_view_assets()

    if romcollection_obj.get_type() == constants.OBJ_COLLECTION_VIRTUAL:
        if romcollection_obj.get_parent_id() is None:
           url = globals.router.url_for_path(f'collection/virtual/{romcollection_obj.get_id()}')
        else:
            collection_value = romcollection_obj.get_custom_attribute("collection_value")
            url = globals.router.url_for_path(f'collection/virtual/{romcollection_obj.get_parent_id()}/items?value={collection_value}')
    else:
        url = globals.router.url_for_path(f'collection/{romcollection_obj.get_id()}')

    return { 
        'id': romcollection_obj.get_id(),
        'name': romcollection_name,
        'url': url,
        'is_folder': True,
        'type': 'video',
        'info': {
            'title': romcollection_name,
            'year': romcollection_obj.get_releaseyear(),
            'genre': romcollection_obj.get_genre(),
            'studio': romcollection_obj.get_developer(),
            'rating': romcollection_obj.get_rating(),
            'plot': romcollection_obj.get_plot(),
            'trailer': romcollection_obj.get_trailer(),
            'overlay': ICON_OVERLAY
        },
        'art': assets,
        'properties': { 
            constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_ROMCOLLECTION,
            'platform': romcollection_obj.get_platform(),
            'boxsize': romcollection_obj.get_box_sizing(),
            'obj_type': romcollection_obj.get_type()
        }
    }

    # --- AKL Collections special category ---
    #if not settings.getSettingAsBool('display_hide_collections'): render_vcategory_collections_row()
    # --- AKL Virtual Categories ---
    #if not settings.getSettingAsBool('display_hide_vlaunchers'): render_vcategory_Browse_by_row()
    # --- Browse Offline Scraper database ---
    #if not settings.getSettingAsBool('display_hide_AKL_scraper'): render_vcategory_AKL_offline_scraper_row()
    #if not settings.getSettingAsBool('display_hide_LB_scraper'):  render_vcategory_LB_offline_scraper_row()


def render_rom_listitem(rom_obj: ROM) -> dict:
    # --- Do not render row if romcollection finished ---
    if rom_obj.is_finished() and settings.getSettingAsBool('display_hide_finished'):
        return

    ICON_OVERLAY = 5 if rom_obj.is_finished() else 4
    assets = rom_obj.get_view_assets()

    # --- Default values for flags ---
    AKL_InFav_bool_value = constants.AKL_INFAV_BOOL_VALUE_FALSE
    AKL_MultiDisc_bool_value = constants.AKL_MULTIDISC_BOOL_VALUE_FALSE
    AKL_Fav_stat_value = constants.AKL_FAV_STAT_VALUE_NONE
    AKL_NoIntro_stat_value = constants.AKL_NOINTRO_STAT_VALUE_NONE
    AKL_PClone_stat_value = constants.AKL_PCLONE_STAT_VALUE_NONE

    rom_status = rom_obj.get_rom_status()
    if rom_status == 'OK':
        AKL_Fav_stat_value = constants.AKL_FAV_STAT_VALUE_OK
    elif rom_status == 'Unlinked ROM':
        AKL_Fav_stat_value = constants.AKL_FAV_STAT_VALUE_UNLINKED_ROM
    elif rom_status == 'Unlinked Launcher':
        AKL_Fav_stat_value = constants.AKL_FAV_STAT_VALUE_UNLINKED_LAUNCHER
    elif rom_status == 'Broken':
        AKL_Fav_stat_value = constants.AKL_FAV_STAT_VALUE_BROKEN
    else:
        AKL_Fav_stat_value = constants.AKL_FAV_STAT_VALUE_NONE

    # --- NoIntro status flag ---
    nstat = rom_obj.get_nointro_status()
    if nstat == constants.AUDIT_STATUS_HAVE:
        AKL_NoIntro_stat_value = constants.AKL_NOINTRO_STAT_VALUE_HAVE
    elif nstat == constants.AUDIT_STATUS_MISS:
        AKL_NoIntro_stat_value = constants.AKL_NOINTRO_STAT_VALUE_MISS
    elif nstat == constants.AUDIT_STATUS_UNKNOWN:
        AKL_NoIntro_stat_value = constants.AKL_NOINTRO_STAT_VALUE_UNKNOWN
    elif nstat == constants.AUDIT_STATUS_NONE:
        AKL_NoIntro_stat_value = constants.AKL_NOINTRO_STAT_VALUE_NONE

    # --- Mark clone ROMs ---
    pclone_status = rom_obj.get_pclone_status()
    if pclone_status == constants.PCLONE_STATUS_PARENT:
        AKL_PClone_stat_value = constants.AKL_PCLONE_STAT_VALUE_PARENT
    elif pclone_status == constants.PCLONE_STATUS_CLONE:
        AKL_PClone_stat_value = constants.AKL_PCLONE_STAT_VALUE_CLONE
    
    rom_in_fav = rom_obj.is_favourite()
    if rom_in_fav:
        AKL_InFav_bool_value = constants.AKL_INFAV_BOOL_VALUE_TRUE

    # --- Set common flags to all launchers---
    if rom_obj.has_multiple_disks():
        AKL_MultiDisc_bool_value = constants.AKL_MULTIDISC_BOOL_VALUE_TRUE

    list_name = rom_obj.get_name()
    sub_label = rom_obj.get_rom_identifier()
    if list_name is None or list_name == '':
        list_name = sub_label
    if list_name == sub_label:
        sub_label = None

    if settings.getSettingAsBool("display_execute_rom_by_default"):
        item_url = globals.router.url_for_path(f'execute/rom/{rom_obj.get_id()}')
    else:
        item_url = globals.router.url_for_path(f'rom/view/{rom_obj.get_id()}')

    return {
        'id': rom_obj.get_id(),
        'name': list_name,
        'name2': sub_label,
        'url': item_url,
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': rom_obj.get_name(),
            'year': rom_obj.get_releaseyear(),
            'genre': rom_obj.get_genre(),
            'studio': rom_obj.get_developer(),
            'rating': rom_obj.get_rating(),
            'plot': rom_obj.get_plot(),
            'trailer': rom_obj.get_trailer(),
            'overlay': ICON_OVERLAY
        },
        'art': assets,
        'properties': {
            'entityid': rom_obj.get_id(),
            'platform': rom_obj.get_platform(),
            'nplayers': rom_obj.get_number_of_players(),
            'nplayers_online': rom_obj.get_number_of_players_online(),
            'esrb': rom_obj.get_esrb_rating(),
            'pegi': rom_obj.get_pegi_rating(),
            'boxsize': rom_obj.get_box_sizing(),
            'tags': ','.join(rom_obj.get_tags()),
            'obj_type': constants.OBJ_ROM,
            # --- ROM flags (Skins will use these flags to render icons) ---
            constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_ROM,
            constants.AKL_INFAV_BOOL_LABEL: AKL_InFav_bool_value,
            constants.AKL_MULTIDISC_BOOL_LABEL: AKL_MultiDisc_bool_value,
            constants.AKL_FAV_STAT_LABEL: AKL_Fav_stat_value,
            constants.AKL_NOINTRO_STAT_LABEL: AKL_NoIntro_stat_value,
            constants.AKL_PCLONE_STAT_LABEL: AKL_PClone_stat_value
        }
    }
