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
import typing

from ael import constants, settings
from ael.utils import kodi

from resources.app.commands.mediator import AppMediator
from resources.app import globals
from resources.app.repositories import UnitOfWork, CategoryRepository, ROMSetRepository, ROMsRepository, ViewRepository
from resources.app.domain import ROM, ROMSet, Category, VirtualCollection, VirtualCollectionFactory

logger = logging.getLogger(__name__)

@AppMediator.register('RENDER_VIEWS')
def cmd_render_views_data(args):
    kodi.notify('Rendering all views')
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        categories_repository   = CategoryRepository(uow)
        romsets_repository      = ROMSetRepository(uow)
        roms_repository         = ROMsRepository(uow)
        views_repository        = ViewRepository(globals.g_PATHS)
        
        _render_root_view(categories_repository, romsets_repository, roms_repository, views_repository, render_sub_views=True)
        
    kodi.notify('All views rendered')
    kodi.refresh_container()

@AppMediator.register('RENDER_VIEW')
def cmd_render_view_data(args):
    kodi.notify('Rendering views')
    category_id = args['category_id'] if 'category_id' in args else None
    render_recursive = args['render_recursive'] if 'render_recursive' in args else False
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        categories_repository   = CategoryRepository(uow)
        romsets_repository      = ROMSetRepository(uow)
        roms_repository         = ROMsRepository(uow)
        views_repository        = ViewRepository(globals.g_PATHS)
                
        if category_id is None or category_id == constants.VCATEGORY_ADDONROOT_ID:
            _render_root_view(categories_repository, romsets_repository, roms_repository, views_repository, render_recursive)
        else:
            category = categories_repository.find_category(category_id)
            _render_category_view(category, categories_repository, romsets_repository, roms_repository, views_repository)
        
    kodi.notify('Selected views rendered')
    kodi.refresh_container()

@AppMediator.register('RENDER_ROMSET_VIEW')
def cmd_render_romset_view_data(args):
    kodi.notify('Rendering romset views')
    romset_id = args['romset_id'] if 'romset_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romsets_repository = ROMSetRepository(uow)
        roms_repository    = ROMsRepository(uow)
        views_repository   = ViewRepository(globals.g_PATHS)
             
        romset = romsets_repository.find_romset(romset_id)
        _render_romset_view(romset, roms_repository, views_repository)
    
    kodi.notify('Selected views rendered')
    kodi.refresh_container()

@AppMediator.register('RENDER_VCOLLECTION_VIEW')
def cmd_render_vcollection(args):
    vcollection_id = args['vcollection_id'] if 'vcollection_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        roms_repository    = ROMsRepository(uow)
        romsets_repository = ROMSetRepository(uow)
        views_repository   = ViewRepository(globals.g_PATHS)
        
        vcollection = VirtualCollectionFactory.create(vcollection_id)
        
        kodi.notify('Rendering virtual collection "{}"'.format(vcollection.get_name()))
        _render_vcollection_view(vcollection, romsets_repository, roms_repository, views_repository)
    
        kodi.notify('{} view rendered'.format(vcollection.get_name()))
    kodi.refresh_container()
    
@AppMediator.register('CLEANUP_VIEWS')
def cmd_cleanup_views(args):    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        categories_repository   = CategoryRepository(uow)
        romsets_repository      = ROMSetRepository(uow)
        
        categories = categories_repository.find_all_categories()
        romsets = romsets_repository.find_all_romsets()
        
        category_ids = list(c.get_id() for c in categories)
        romset_ids = list(r.get_id() for r in romsets)
        
        view_files = globals.g_PATHS.COLLECTIONS_DIR.scanFilesInPath('collection_*.json')
        for view_file in view_files:
            view_id = view_file.getBaseNoExt().replace('collection_', '')
            if not view_id in category_ids and not view_id in romset_ids:
                logger.info('Removing files for collection "{}"'.format(view_id))
                view_file.unlink()
         
def _render_root_view(categories_repository: CategoryRepository, romsets_repository: ROMSetRepository, 
                      roms_repository: ROMsRepository, views_repository: ViewRepository, 
                      render_sub_views = False):
    
    root_categories = categories_repository.find_root_categories()
    root_romsets = romsets_repository.find_root_romsets()
        
    root_data = {
        'id': constants.VCATEGORY_ADDONROOT_ID,
        'name': 'Root',
        'obj_type': constants.OBJ_CATEGORY,
        'items': []
    }
    root_items = []
    for root_category in root_categories:
        logger.debug('Processing category "{}"'.format(root_category.get_name()))
        root_items.append(_render_category_listitem(root_category))
        if render_sub_views:
            _render_category_view(root_category, categories_repository, romsets_repository, 
                                  roms_repository, views_repository, render_sub_views)

    for root_romset in root_romsets:
        logger.debug('Processing romset "{}"'.format(root_romset.get_name()))
        root_items.append(_render_romset_listitem(root_romset))
        if render_sub_views:
            _render_romset_view(root_romset, roms_repository, views_repository)

    for vcollection_id in constants.VCOLLECTIONS:
        vcollection = VirtualCollectionFactory.create(vcollection_id)
        logger.debug('Processing virtual collection "{}"'.format(vcollection.get_name()))
        root_items.append(_render_vcollection_listitem(vcollection))
        if render_sub_views:
            _render_vcollection_view(vcollection, romsets_repository, roms_repository, views_repository)        

    logger.debug('Storing {} items in root view.'.format(len(root_items)))
    root_data['items'] = root_items
    views_repository.store_root_view(root_data)
        
def _render_category_view(category_obj: Category, categories_repository: CategoryRepository, 
                         romsets_repository: ROMSetRepository, roms_repository: ROMsRepository,
                         views_repository: ViewRepository, render_sub_views = False):
    
    sub_categories = categories_repository.find_categories_by_parent(category_obj.get_id())
    romsets = romsets_repository.find_romsets_by_parent(category_obj.get_id())
    
    view_data = {
        'id': category_obj.get_id(),
        'name': category_obj.get_name(),
        'obj_type': constants.OBJ_CATEGORY,
        'items': []
    }
    view_items = []
    for sub_category in sub_categories:
        logger.debug('Processing category "{}", part of "{}"'.format(sub_category.get_name(), category_obj.get_name()))
        view_items.append(_render_category_listitem(sub_category))
        if render_sub_views:
            _render_category_view(sub_category, categories_repository, romsets_repository, roms_repository, 
                                  views_repository, render_sub_views)
    
    for romset in romsets:
        logger.debug('Processing romset "{}"'.format(romset.get_name()))
        try:
            view_items.append(_render_romset_listitem(romset))
        except Exception as ex:
            logger.error('Exception while rendering list item ROM Collection "{}"'.format(romset.get_name()), exc_info=ex)
            kodi.notify_error("Failed to process ROM collection {}".format(romset.get_name()))
        if render_sub_views:
            _render_romset_view(romset, roms_repository, views_repository)
        
    logger.debug('Storing {} items for category "{}" view.'.format(len(view_items), category_obj.get_name()))
    view_data['items'] = view_items
    views_repository.store_view(category_obj.get_id(), view_data)

def _render_romset_view(romset_obj: ROMSet, roms_repository: ROMsRepository, views_repository: ViewRepository):
    
    roms = roms_repository.find_roms_by_romset(romset_obj.get_id())
    
    view_data = {
        'id': romset_obj.get_id(),
        'name': romset_obj.get_name(),
        'obj_type': constants.OBJ_ROMSET,
        'items': []
    }
    view_items = []
    for rom in roms:
        try:
            rom.apply_romset_asset_mapping(romset_obj)
            view_items.append(_render_rom_listitem(rom))
        except Exception as ex:
            logger.error('Exception while rendering list item ROM "{}"'.format(rom.get_name()), exc_info=ex)
        
    logger.debug('Storing {} items for romset "{}" view.'.format(len(view_items), romset_obj.get_name()))
    view_data['items'] = view_items
    views_repository.store_view(romset_obj.get_id(), view_data)

def _render_vcollection_view(vcollection: VirtualCollection, romsets_repository: ROMSetRepository, 
                                roms_repository: ROMsRepository, views_repository: ViewRepository):
    
    logger.info('Rendering virtual collection "{}"'.format(vcollection.get_name()))
    roms = roms_repository.find_roms_by_virtual_collection(vcollection.get_id())
        
    view_data = {
        'id': vcollection.get_id(),
        'name': vcollection.get_name(),
        'obj_type': constants.OBJ_COLLECTION_VIRTUAL,
        'items': []
    }
    view_items = []
    for rom in roms:
        try:
            view_items.append(_render_rom_listitem(rom))
        except Exception as ex:
            logger.error('Exception while rendering list item ROM "{}"'.format(rom.get_name()), exc_info=ex)
        
    logger.debug('Storing {} items for virtual collection "{}" view.'.format(len(view_items), vcollection.get_name()))
    view_data['items'] = view_items
    views_repository.store_view(vcollection.get_id(), view_data)

def _render_category_listitem(category_obj: Category):
    # --- Do not render row if category finished ---
    if category_obj.is_finished() and settings.getSettingAsBool('display_hide_finished'): return

    category_name = category_obj.get_name()
    ICON_OVERLAY = 5 if category_obj.is_finished() else 4
    assets = category_obj.get_view_assets()

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
            constants.AEL_CONTENT_LABEL: constants.AEL_CONTENT_VALUE_CATEGORY,
            'obj_type': constants.OBJ_CATEGORY,
            'num_romsets': category_obj.num_romsets() 
        }
    }
 
def _render_romset_listitem(romset_obj: ROMSet):
    # --- Do not render row if romset finished ---
    if romset_obj.is_finished() and settings.getSettingAsBool('display_hide_finished'): return

    romset_name = romset_obj.get_name()
    ICON_OVERLAY = 5 if romset_obj.is_finished() else 4
    assets = romset_obj.get_view_assets()

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
            constants.AEL_CONTENT_LABEL: constants.AEL_CONTENT_VALUE_LAUNCHERS,
            'platform': romset_obj.get_platform(),
            'boxsize': romset_obj.get_box_sizing(),
            'obj_type': constants.OBJ_ROMSET
        }
    }

def _render_rom_listitem(rom_obj: ROM):
    # --- Do not render row if romset finished ---
    if rom_obj.is_finished() and settings.getSettingAsBool('display_hide_finished'): return

    ICON_OVERLAY = 5 if rom_obj.is_finished() else 4
    assets = rom_obj.get_view_assets()

    # --- Default values for flags ---
    AEL_InFav_bool_value     = constants.AEL_INFAV_BOOL_VALUE_FALSE
    AEL_MultiDisc_bool_value = constants.AEL_MULTIDISC_BOOL_VALUE_FALSE
    AEL_Fav_stat_value       = constants.AEL_FAV_STAT_VALUE_NONE
    AEL_NoIntro_stat_value   = constants.AEL_NOINTRO_STAT_VALUE_NONE
    AEL_PClone_stat_value    = constants.AEL_PCLONE_STAT_VALUE_NONE

    rom_status      = rom_obj.get_rom_status()
    if   rom_status == 'OK':                AEL_Fav_stat_value = constants.AEL_FAV_STAT_VALUE_OK
    elif rom_status == 'Unlinked ROM':      AEL_Fav_stat_value = constants.AEL_FAV_STAT_VALUE_UNLINKED_ROM
    elif rom_status == 'Unlinked Launcher': AEL_Fav_stat_value = constants.AEL_FAV_STAT_VALUE_UNLINKED_LAUNCHER
    elif rom_status == 'Broken':            AEL_Fav_stat_value = constants.AEL_FAV_STAT_VALUE_BROKEN
    else:                                   AEL_Fav_stat_value = constants.AEL_FAV_STAT_VALUE_NONE

    # --- NoIntro status flag ---
    nstat = rom_obj.get_nointro_status()
    if   nstat == constants.AUDIT_STATUS_HAVE:    AEL_NoIntro_stat_value = constants.AEL_NOINTRO_STAT_VALUE_HAVE
    elif nstat == constants.AUDIT_STATUS_MISS:    AEL_NoIntro_stat_value = constants.AEL_NOINTRO_STAT_VALUE_MISS
    elif nstat == constants.AUDIT_STATUS_UNKNOWN: AEL_NoIntro_stat_value = constants.AEL_NOINTRO_STAT_VALUE_UNKNOWN
    elif nstat == constants.AUDIT_STATUS_NONE:    AEL_NoIntro_stat_value = constants.AEL_NOINTRO_STAT_VALUE_NONE

    # --- Mark clone ROMs ---
    pclone_status = rom_obj.get_pclone_status()
    if   pclone_status == constants.PCLONE_STATUS_PARENT: AEL_PClone_stat_value = constants.AEL_PCLONE_STAT_VALUE_PARENT
    elif pclone_status == constants.PCLONE_STATUS_CLONE:  AEL_PClone_stat_value = constants.AEL_PCLONE_STAT_VALUE_CLONE
    
    rom_in_fav = rom_obj.is_favourite()
    if rom_in_fav: AEL_InFav_bool_value = constants.AEL_INFAV_BOOL_VALUE_TRUE

     # --- Set common flags to all launchers---
    if rom_obj.has_multiple_disks(): AEL_MultiDisc_bool_value = constants.AEL_MULTIDISC_BOOL_VALUE_TRUE

    list_name = rom_obj.get_name()
    if list_name is None or list_name == '':
        rom_file = rom_obj.get_file()
        list_name = rom_file.getBaseNoExt()

    return { 
        'id': rom_obj.get_id(),
        'name': list_name,
        'url': globals.router.url_for_path('execute/rom/{}'.format(rom_obj.get_id())),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title'   : rom_obj.get_name(),    'year'    : rom_obj.get_releaseyear(),
            'genre'   : rom_obj.get_genre(),   'studio'  : rom_obj.get_developer(),
            'rating'  : rom_obj.get_rating(),  'plot'    : rom_obj.get_plot(),
            'trailer' : rom_obj.get_trailer(), 'overlay' : ICON_OVERLAY
        },
        'art': assets,
        'properties': { 
            'platform': rom_obj.get_platform(),
            'nplayers': rom_obj.get_number_of_players(),
            'esrb':     rom_obj.get_esrb_rating(),
            'boxsize':  rom_obj.get_box_sizing(),
            'obj_type': constants.OBJ_ROM,
            # --- ROM flags (Skins will use these flags to render icons) ---
            constants.AEL_CONTENT_LABEL:        constants.AEL_CONTENT_VALUE_ROM,
            constants.AEL_INFAV_BOOL_LABEL:     AEL_InFav_bool_value,
            constants.AEL_MULTIDISC_BOOL_LABEL: AEL_MultiDisc_bool_value,
            constants.AEL_FAV_STAT_LABEL:       AEL_Fav_stat_value,
            constants.AEL_NOINTRO_STAT_LABEL:   AEL_NoIntro_stat_value,
            constants.AEL_PCLONE_STAT_LABEL:    AEL_PClone_stat_value
        }
    }
    
def _render_vcollection_listitem(vcollection: VirtualCollection):
    # --- Do not render row if vcollection is marked as finished ---
    if vcollection.is_finished(): return

    collection_name = vcollection.get_name()
    assets = vcollection.get_view_assets()

    return { 
        'id': vcollection.get_id(),
        'name': collection_name,
        'url': globals.router.url_for_path('collection/{}'.format(vcollection.get_id())),
        'is_folder': True,
        'type': 'video',
        'info': {
            'title'   : collection_name,             
            'plot'    : vcollection.get_plot(),
            'overlay' : 4
        },
        'art': assets,
        'properties': { 
            constants.AEL_CONTENT_LABEL: constants.AEL_CONTENT_VALUE_ROMSET,
            'obj_type': constants.OBJ_COLLECTION_VIRTUAL
        }
    }
 
    # --- AEL Collections special category ---
    #if not settings.getSettingAsBool('display_hide_collections'): render_vcategory_collections_row()
    # --- AEL Virtual Categories ---
    #if not settings.getSettingAsBool('display_hide_vlaunchers'): render_vcategory_Browse_by_row()
    # --- Browse Offline Scraper database ---
    #if not settings.getSettingAsBool('display_hide_AEL_scraper'): render_vcategory_AEL_offline_scraper_row()
    #if not settings.getSettingAsBool('display_hide_LB_scraper'):  render_vcategory_LB_offline_scraper_row()