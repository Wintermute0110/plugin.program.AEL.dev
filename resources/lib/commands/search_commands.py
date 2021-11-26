# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (search)
#
# Copyright (c) Wintermute0110 <wintermute0110@gmail.com> / Chrisism <crizizz@gmail.com>
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
import collections
from urllib.parse import urlencode

from ael.utils import kodi
from ael import constants

from resources.lib.commands.mediator import AppMediator

from resources.lib.repositories import ROMsRepository, UnitOfWork, ROMCollectionRepository
from resources.lib import globals

logger = logging.getLogger(__name__)

@AppMediator.register('SEARCH')
def cmd_search(args):
    
    options = collections.OrderedDict()
    options['SEARCH_BY_TITLE']       = 'By ROM Title'
    options['SEARCH_BY_RELEASEYEAR'] = 'By Release Year'
    options['SEARCH_BY_GENRE']       = 'By Genre'
    options['SEARCH_BY_DEVELOPER']   = 'By Developer'
    options['SEARCH_BY_RATING']      = 'By Rating'
    
    selected_option = kodi.OrdDictionaryDialog().select('Search ROMs...',options)
    AppMediator.sync_cmd(selected_option, args)

@AppMediator.register('SEARCH_BY_TITLE')
def cmd_search_by_title(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    search_string = kodi.dialog_keyboard('Enter the ROM Title search string...')
    if search_string is None: return None
    
    params = {
        'filter': constants.META_TITLE_ID,
        'term': search_string
    }
    url = globals.router.url_for_path(f'/collection/{romcollection_id}') 
    kodi.update_uri(url, params)

@AppMediator.register('SEARCH_BY_GENRE')
def cmd_search_by_genre(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    _apply_search_query_by_options(romcollection_id, constants.META_GENRE_ID, 'Select a Genre...')
    
@AppMediator.register('SEARCH_BY_RELEASEYEAR')
def cmd_search_by_year(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    _apply_search_query_by_options(romcollection_id, constants.META_YEAR_ID, 'Select a Release year...')

@AppMediator.register('SEARCH_BY_DEVELOPER')
def cmd_search_by_developer(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    _apply_search_query_by_options(romcollection_id, constants.META_DEVELOPER_ID, 'Select a Developer...')
    
@AppMediator.register('SEARCH_BY_RATING')
def cmd_search_by_rating(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    _apply_search_query_by_options(romcollection_id, constants.META_RATING_ID, 'Select a Rating...')

def _apply_search_query_by_options(romcollection_id:str, filter_type:str, dialog_title: str):
    
    search_string = ''
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository            = ROMsRepository(uow)
        collection_repository = ROMCollectionRepository(uow)
        
        romcollection = collection_repository.find_romcollection(romcollection_id)
        filter_values = repository.find_all_filter_values_in_romcollection(romcollection, constants.META_YEAR_ID)
        
        options = []
        options.append('[ Not Set ]')
        options.extend(filter_values)
        
        selected_index = kodi.ListDialog().select(dialog_title, options)
        if selected_index is None: return None
        
        if selected_index == 0: search_string = 'UNDEFINED'
        else: search_string = options[selected_index]
        
    params = {
        'filter': filter_type,
        'term': search_string
    }
            
    url = globals.router.url_for_path(f'/collection/{romcollection_id}')     
    kodi.update_uri(url, params)