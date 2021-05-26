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
from resources.lib.utils import kodi, editors

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

@AppMediator.register('EDIT_CATEGORY')
def cmd_edit_category(args):    
    logger.debug('EDIT_CATEGORY: cmd_edit_category() BEGIN')
    category_id = args['category_id'] if 'category_id' in args else None
    
    if category_id is None:
        logger.warn('cmd_add_category(): No category id supplied.')
        kodi.notify_warn("Invalid parameters supplied.")
        return
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        
        options = collections.OrderedDict()
        options['CATEGORY_EDIT_METADATA']       = 'Edit Metadata ...'
        options['CATEGORY_EDIT_ASSETS']         = 'Edit Assets/Artwork ...'
        options['CATEGORY_EDIT_DEFAULT_ASSETS'] = 'Choose default Assets/Artwork ...'
        options['CATEGORY_STATUS']              = 'Category status: {0}'.format(category.get_finished_str())
        options['EXPORT_CATEGORY_XML']          = 'Export Category XML configuration ...'
        options['DELETE_CATEGORY']              = 'Delete Category'
        
        s = 'Select action for Category "{0}"'.format(category.get_name())
        selected_option = kodi.OrdDictionaryDialog().select(s, options)    
    
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_CATEGORY: cmd_edit_category() Selected None. Closing context menu')
        return

    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('EDIT_CATEGORY_MENU: cmd_edit_category() Selected {}'.format(selected_option))
    kodi.event(method=selected_option, data=args)
    
@AppMediator.register('CATEGORY_EDIT_METADATA')
def cmd_edit_metadata_category(args):    
    logger.debug('CATEGORY_EDIT_METADATA: cmd_edit_metadata_category() BEGIN')
    category_id = args['category_id'] if 'category_id' in args else None
    selected_option = None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        
        NFO_FileName  = category.get_NFO_name()
        NFO_found_str = 'NFO found' if NFO_FileName.exists() else 'NFO not found'
        plot_str      = text.limit_string(category.get_plot(), PLOT_STR_MAXSIZE)

        options = collections.OrderedDict()
        options['CATEGORY_EDIT_METADATA_TITLE']       = "Edit Title: '{}'".format(category.get_name())
        options['CATEGORY_EDIT_METADATA_RELEASEYEAR'] = "Edit Release Year: '{}'".format(category.get_releaseyear())
        options['CATEGORY_EDIT_METADATA_GENRE']       = "Edit Genre: '{}'".format(category.get_genre())
        options['CATEGORY_EDIT_METADATA_DEVELOPER']   = "Edit Developer: '{}'".format(category.get_developer())
        options['CATEGORY_EDIT_METADATA_RATING']      = "Edit Rating: '{}'".format(category.get_rating())
        options['CATEGORY_EDIT_METADATA_PLOT']        = "Edit Plot: '{}'".format(plot_str)
        options['CATEGORY_IMPORT_NFO_FILE']           = 'Import NFO file (default, {})'.format(NFO_found_str)
        options['CATEGORY_IMPORT_NFO_FILE_BROWSE']    = 'Import NFO file (browse NFO file) ...'
        options['CATEGORY_SAVE_NFO_FILE']             = 'Save NFO file (default location)'
            
        s = 'Edit Category "{}" metadata'.format(category.get_name())
        selected_option = kodi.OrdDictionaryDialog().select(s, options)
        
    if selected_option is None:
        # >> Return recursively to parent menu.
        logger.debug('CATEGORY_EDIT_METADATA: cmd_edit_metadata_category() Selected NONE')
        kodi.event(method='EDIT_CATEGORY', data=args)
        return
    
    # >> Execute category edit metadata atomic subcommand.
    logger.debug('CATEGORY_EDIT_METADATA: cmd_edit_metadata_category() Selected {0}'.format(selected_option))
    kodi.event(method=selected_option, data=args)

# -------------------------------------------------------------------------------------------------
# Category context menu atomic commands.
# Only Category context menu functions have debug statemets. This debug messages are to
# debug the context menu recursive logic.
# -------------------------------------------------------------------------------------------------
# --- Atomic commands ---
@AppMediator.register('CATEGORY_EDIT_METADATA_TITLE')
def cmd_category_metadata_title(args):
    category_id = args['category_id'] if 'category_id' in args else None    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        
        is_changed = editors.edit_field_by_str(category, 'Title', category.get_name, category.set_name)
        if is_changed:
            repository.update_category(category)
            uow.commit()
    kodi.event(method='CATEGORY_EDIT_METADATA', data=args)
    
@AppMediator.register('CATEGORY_EDIT_METADATA_RELEASEYEAR')
def cmd_category_metadata_releaseyear(args):
    category_id = args['category_id'] if 'category_id' in args else None    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        
        is_changed = editors.edit_field_by_str(category, 'Release Year', category.get_releaseyear, category.set_releaseyear)
        if is_changed:
            repository.update_category(category)
            uow.commit()
    kodi.event(method='CATEGORY_EDIT_METADATA', data=args)


@AppMediator.register('CATEGORY_EDIT_METADATA_GENRE')
def cmd_category_metadata_genre(args):
    category_id = args['category_id'] if 'category_id' in args else None    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        
        is_changed = editors.edit_field_by_str(category, 'Genre', category.get_genre, category.set_genre)
        if is_changed:
            repository.update_category(category)
            uow.commit()
    kodi.event(method='CATEGORY_EDIT_METADATA', data=args)
    
@AppMediator.register('CATEGORY_EDIT_METADATA_DEVELOPER')
def cmd_category_metadata_developer(args):
    category_id = args['category_id'] if 'category_id' in args else None    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        
        is_changed = editors.edit_field_by_str(category, 'Developer', category.get_developer, category.set_developer)
        if is_changed:
            repository.update_category(category)
            uow.commit()
    kodi.event(method='CATEGORY_EDIT_METADATA', data=args)

@AppMediator.register('CATEGORY_EDIT_METADATA_RATING')
def cmd_category_metadata_rating(args):
    category_id = args['category_id'] if 'category_id' in args else None    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        
        is_changed = editors.edit_rating(category, category.get_rating, category.set_rating)
        if is_changed:
            repository.update_category(category)
            uow.commit()
    kodi.event(method='CATEGORY_EDIT_METADATA', data=args)

@AppMediator.register('CATEGORY_EDIT_METADATA_PLOT')
def cmd_category_metadata_plot(args):
    category_id = args['category_id'] if 'category_id' in args else None    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        
        is_changed = editors.edit_field_by_str(category, 'Plot', category.get_plot, category.set_plot)
        if is_changed:
            repository.update_category(category)
            uow.commit()
    kodi.event(method='CATEGORY_EDIT_METADATA', data=args)

@AppMediator.register('CATEGORY_IMPORT_NFO_FILE_DEFAULT')
def cmd_category_import_nfo_file(args):
    category_id = args['category_id'] if 'category_id' in args else None    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        NFO_file = category.get_NFO_name()
        
        if category.import_NFO_file(NFO_file):
            repository.update_category(category)
            uow.commit()
            kodi.notify('Imported Category NFO file {0}'.format(NFO_file.getPath()))
    
    kodi.event(method='CATEGORY_EDIT_METADATA', data=args)

@AppMediator.register('CATEGORY_IMPORT_NFO_FILE_BROWSE')
def cmd_category_browse_import_nfo_file(args):    
    category_id = args['category_id'] if 'category_id' in args else None
    
    NFO_file = kodi.browse(1, 'Select NFO description file', 'files', '.nfo', False)
    logger.debug('cmd_category_browse_import_nfo_file() Dialog().browse returned "{0}"'.format(NFO_file))
    if not NFO_file: return
    NFO_FileName = FileName(NFO_file)
    if not NFO_FileName.exists(): return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        
        if category.import_NFO_file(NFO_FileName):
            repository.update_category(category)
            uow.commit()
            kodi.notify('Imported Category NFO file {0}'.format(NFO_FileName.getPath()))  
    
    kodi.event(method='CATEGORY_EDIT_METADATA', data=args)

@AppMediator.register('CATEGORY_SAVE_NFO_FILE_DEFAULT')
def cmd_category_save_nfo_file(args):
    category_id = args['category_id'] if 'category_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        
    NFO_FileName = category.get_NFO_name()
    # >> Returns False if exception happened. If an Exception happened function notifies
    # >> user, so display nothing to not overwrite error notification.
    try:
        category.export_to_NFO_file(NFO_FileName)
    except:
        kodi.notify_warn('Exception writing NFO file {0}'.format(NFO_FileName.getPath()))
        logger.error("cmd_category_save_nfo_file() Exception writing'{0}'".format(NFO_FileName.getPath()))
    else:
        logger.debug("cmd_category_save_nfo_file() Created '{0}'".format(NFO_FileName.getPath()))
        kodi.notify('Exported Category NFO file {0}'.format(NFO_FileName.getPath()))
    
    kodi.event(method='CATEGORY_EDIT_METADATA', data=args)

@AppMediator.register('CATEGORY_EXPORT_CATEGORY_XML')
# --- Export Category XML configuration ---
def cmd_category_export_xml(args):
    category_id = args['category_id'] if 'category_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    category = None
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
    
    category_fn_str = 'Category_' + text.str_to_filename_str(category.get_name()) + '.xml'
    logger.debug('cmd_export_category_xml() Exporting Category configuration')
    logger.debug('cmd_export_category_xml() Name     "{0}"'.format(category.get_name()))
    logger.debug('cmd_export_category_xml() ID       {0}'.format(category.get_id()))
    logger.debug('cmd_export_category_xml() l_fn_str "{0}"'.format(category_fn_str))

    # --- Ask user for a path to export the launcher configuration ---
    dir_path = kodi.browse(0, 'Select directory to export XML', 'files', '', False)
    if not dir_path: 
        kodi.event(method='CATEGORY_EDIT_METADATA', data=args)
        return

    # --- If XML exists then warn user about overwriting it ---
    export_FN = FileName(dir_path).pjoin(category_fn_str)
    if export_FN.exists():
        ret = kodi.dialog_yesno('Overwrite file {0}?'.format(export_FN.getPath()))
        if not ret:
            kodi.notify_warn('Export of Category XML cancelled')
            kodi.event(method='CATEGORY_EDIT_METADATA', data=args)
            return

    # >> If everything goes all right when exporting then the else clause is executed.
    # >> If there is an error/exception then the exception handler prints a warning message
    # >> inside the function autoconfig_export_category() and the sucess message is never
    # >> printed. This is the standard way of handling error messages in AEL code.
    try:
        category.export_to_file(export_FN)
    except AddonError as E:
        kodi.notify_warn('{0}'.format(E))
    else:
        kodi.notify('Exported Category "{0}" XML config'.format(category.get_name()))
    
    kodi.event(method='CATEGORY_EDIT_METADATA', data=args)