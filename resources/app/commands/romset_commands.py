# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (romset management)
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
import collections

from ael import constants, platforms
from ael.utils import kodi, text, io

from resources.app.commands.mediator import AppMediator
from resources.app import globals, editors
from resources.app.repositories import UnitOfWork, CategoryRepository, ROMSetRepository
from resources.app.domain import Category, ROMSet, g_assetFactory

logger = logging.getLogger(__name__)

@AppMediator.register('ADD_ROMSET')
def cmd_add_collection(args):
    logger.debug('cmd_add_collection() BEGIN')
    parent_id = args['category_id'] if 'category_id' in args else None
    grand_parent_id = args['parent_category_id'] if 'parent_category_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository              = CategoryRepository(uow)
        parent_category         = repository.find_category(parent_id) if parent_id is not None else None
        grand_parent_category  =  repository.find_category(grand_parent_id)
        
        if grand_parent_category is not None:
            options_dialog = kodi.ListDialog()
            selected_option = options_dialog.select('Add ROM collection in?',[parent_category.get_name(), grand_parent_category.get_name()])
            if selected_option > 0:
                parent_category = grand_parent_category
    
        wizard = kodi.WizardDialog_Selection(None, 'platform', 'Select the platform', platforms.AEL_platform_list)
        wizard = kodi.WizardDialog_Dummy(wizard, 'm_name', '', _get_name_from_platform)
        wizard = kodi.WizardDialog_Keyboard(wizard, 'm_name', 'Set the title of the launcher')
        wizard = kodi.WizardDialog_FileBrowse(wizard, 'assets_path', 'Select asset/artwork directory',0, '')
        
        romset = ROMSet()
        entity_data = romset.get_data_dic()
        entity_data = wizard.runWizard(entity_data)
        
        romset.import_data_dic(entity_data)
                
        # --- Determine box size based on platform --
        platform = platforms.get_AEL_platform(entity_data['platform'])
        romset.set_box_sizing(platform.default_box_size)
        
        romset_repository = ROMSetRepository(uow)
        romset_repository.insert_romset(romset, parent_category)
        uow.commit()
        
        kodi.notify('ROM Collection {0} created'.format(romset.get_name()))
        AppMediator.async_cmd('RENDER_ROMSET_VIEW', {'romset_id': romset.get_id()})
        AppMediator.async_cmd('RENDER_VIEW', {'category_id': parent_category.get_id()})   
    
def _get_name_from_platform(input, item_key, entity_data):
    title = entity_data['platform']
    return title

# -------------------------------------------------------------------------------------------------
# ROMSet context menu.
# -------------------------------------------------------------------------------------------------

# --- Main menu command ---
@AppMediator.register('EDIT_ROMSET')
def cmd_edit_romset(args):

    logger.debug('EDIT_ROMSET: cmd_edit_romset() BEGIN')
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    
    if romset_id is None:
        logger.warn('cmd_edit_romset(): No romset id supplied.')
        kodi.notify_warn("Invalid parameters supplied.")
        return
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)

        cat_repository = CategoryRepository(uow)
        parent_id = romset.get_parent_id()
        category = cat_repository.find_category(romset.get_parent_id()) if parent_id is None else None 
        category_name = 'None' if category is None else category.get_name()

    options = collections.OrderedDict()
    options['ROMSET_EDIT_METADATA']       = 'Edit Metadata ...'
    options['ROMSET_EDIT_ASSETS']         = 'Edit Assets/Artwork ...'
    options['ROMSET_EDIT_DEFAULT_ASSETS'] = 'Choose default Assets/Artwork ...'
    if romset.has_launchers():
        options['EDIT_ROMSET_LAUNCHERS']  = 'Manage associated launchers'
    else: options['ADD_LAUNCHER']         = 'Add new launcher'    
    options['ROMSET_MANAGE_ROMS']         = 'Manage ROMs ...'
    options['EDIT_ROMSET_CATEGORY']       = "Change Category: '{0}'".format(category_name)
    options['EDIT_ROMSET_STATUS']         = 'ROM Collection status: {0}'.format(romset.get_finished_str())
    options['EXPORT_ROMSET']              = 'Export ROM Collection XML configuration ...'
    options['DELETE_ROMSET']              = 'Delete ROM Collection'

    s = 'Select action for ROM Collection "{}"'.format(romset.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_ROMSET: cmd_edit_romset() Selected None. Closing context menu')
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('EDIT_ROMSET: cmd_edit_romset() Selected {}'.format(selected_option))
    AppMediator.sync_cmd(selected_option, {
        'romset_id': romset_id, 'category_id': romset.get_parent_id()
    })

# --- Submenu commands ---
@AppMediator.register('ROMSET_EDIT_METADATA')
def cmd_romset_metadata(args):
    romset_id = args['romset_id'] if 'romset_id' in args else None
    selected_option = None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)

    plot_str = text.limit_string(romset.get_plot(), constants.PLOT_STR_MAXSIZE)
    rating = romset.get_rating() if romset.get_rating() != -1 else 'not rated'
    NFO_FileName = romset.get_NFO_name()
    NFO_found_str = 'NFO found' if NFO_FileName.exists() else 'NFO not found'

    options = collections.OrderedDict()
    options['ROMSET_EDIT_METADATA_TITLE']     = "Edit Title: '{0}'".format(romset.get_name())
    options['ROMSET_EDIT_METADATA_PLATFORM']  = "Edit Platform: {}".format(romset.get_platform())
    options['ROMSET_EDIT_METADATA_GENRE']     = "Edit Genre: '{0}'".format(romset.get_genre())
    options['ROMSET_EDIT_METADATA_DEVELOPER'] = "Edit Developer: '{}'".format(romset.get_developer())
    options['ROMSET_EDIT_METADATA_RATING']    = "Edit Rating: '{0}'".format(rating)
    options['ROMSET_EDIT_METADATA_PLOT']      = "Edit Plot: '{0}'".format(plot_str)
    options['ROMSET_EDIT_METADATA_BOXSIZE']   = "Edit Box Size: '{}'".format(romset.get_box_sizing())
    options['ROMSET_IMPORT_NFO_FILE_DEFAULT'] = 'Import NFO file (default {0})'.format(NFO_found_str)
    options['ROMSET_IMPORT_NFO_FILE_BROWSE']  = 'Import NFO file (browse NFO file) ...'
    options['ROMSET_SAVE_NFO_FILE_DEFAULT']   = 'Save NFO file (default location)'

    s = 'Edit Launcher "{0}" metadata'.format(romset.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Return recursively to parent menu.
        logger.debug('cmd_romset_metadata(EDIT_METADATA) Selected NONE')
        AppMediator.sync_cmd('EDIT_ROMSET', args)
        return

    # >> Execute launcher edit metadata atomic subcommand.
    # >> Then, execute recursively this submenu again.
    logger.debug('cmd_romset_metadata(EDIT_METADATA) Selected {0}'.format(selected_option))
    AppMediator.sync_cmd(selected_option, args)

@AppMediator.register('ROMSET_EDIT_ASSETS')
def cmd_romset_edit_assets(args):
    romset_id = args['romset_id'] if 'romset_id' in args else None
    preselected_option = args['selected_asset'] if 'selected_asset' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)
        
        selected_asset_to_edit = editors.edit_object_assets(romset, preselected_option)
        if selected_asset_to_edit is None:
            AppMediator.async_cmd('EDIT_ROMSET', args)
            return
        
        asset = g_assetFactory.get_asset_info(selected_asset_to_edit)
        #if selected_asset_to_edit == editors.SCRAPE_CMD:
        #    AppMediator.async_cmd('EDIT_ROMSET_MENU', args)
        #    globals.run_command(scrape_cmd, rom=obj_instance)
        #    edit_object_assets(obj_instance, selected_option)
        #    return True
        
        # >> Execute edit asset menu subcommand. Then, execute recursively this submenu again.
        # >> The menu dialog is instantiated again so it reflects the changes just edited.
        # >> If edit_asset() returns True changes were made.
        if editors.edit_asset(romset, asset):
            repository.update_romset(romset)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMSET_VIEW', {'romset_id': romset.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romset.get_parent_id()})     

    AppMediator.sync_cmd('ROMSET_EDIT_ASSETS', {'romset_id': romset.get_id(), 'selected_asset': asset.id})         

@AppMediator.register('ROMSET_EDIT_DEFAULT_ASSETS')
def cmd_romset_edit_default_assets(args):
    romset_id = args['romset_id'] if 'romset_id' in args else None
    preselected_option = args['selected_asset'] if 'selected_asset' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)
        
        selected_asset_to_edit = editors.edit_object_default_assets(romset, preselected_option)
        if selected_asset_to_edit is None:
            AppMediator.async_cmd('EDIT_ROMSET', args)

        if editors.edit_default_asset(romset, selected_asset_to_edit):
            repository.update_romset(romset)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMSET_VIEW', {'romset_id': romset.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romset.get_parent_id()})     

    AppMediator.async_cmd('ROMSET_EDIT_DEFAULT_ASSETS', {'romset_id': romset.get_id(), 'selected_asset': selected_asset_to_edit.id})         
    
@AppMediator.register('EDIT_ROMSET_STATUS')
def cmd_romset_status(args):
    romset_id = args['romset_id'] if 'romset_id' in args else None    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)
        romset.change_finished_status()
        kodi.dialog_OK('ROMSet "{}" status is now {}'.format(romset.get_name(), romset.get_finished_str()))
        repository.update_romset(romset)
        uow.commit()
        
    AppMediator.async_cmd('RENDER_ROMSET_VIEW', {'romset_id': romset.get_id()})
    AppMediator.async_cmd('RENDER_VIEW', {'category_id': romset.get_parent_id()})     
    AppMediator.async_cmd('EDIT_ROMSET', args)
    
#
# Remove ROMSet
#
@AppMediator.register('DELETE_ROMSET')
def cmd_romset_delete(args):
    romset_id = args['romset_id'] if 'romset_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)
        romset_name = romset.get_name()
        
        if romset.num_roms() > 0:
            question = 'ROMSet "{0}" has {1} ROMs. '.format(romset_name, romset.num_roms()) + \
                        'Are you sure you want to delete it?'
        else:
            question = 'Are you sure you want to delete "{}"?'.format(romset_name)
    
        ret = kodi.dialog_yesno(question)
        if not ret: return
            
        logger.info('Deleting romset "{}" ID {}'.format(romset_name, romset.get_id()))
        repository.delete_romset(romset.get_id())
        uow.commit()
        
    kodi.notify('Deleted romset {0}'.format(romset_name))
    AppMediator.async_cmd('RENDER_VIEW', {'category_id': romset.get_parent_id()})            
    AppMediator.async_cmd('CLEANUP_VIEWS')
    AppMediator.async_cmd('EDIT_ROMSET', args)

# --- Atomic commands ---
# --- Edition of the launcher name ---
@AppMediator.register('ROMSET_EDIT_METADATA_TITLE')
def cmd_romset_metadata_title(args):
    romset_id = args['romset_id'] if 'romset_id' in args else None  
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)
        
        if editors.edit_field_by_str(romset, 'Title', romset.get_name, romset.set_name):
            repository.update_romset(romset)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMSET_VIEW', {'romset_id': romset.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romset.get_parent_id()})            
    AppMediator.async_cmd('ROMSET_EDIT_METADATA', args)

@AppMediator.register('ROMSET_EDIT_METADATA_PLATFORM')
def cmd_romset_metadata_platform(args):
    romset_id = args['romset_id'] if 'romset_id' in args else None  
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)

        if editors.edit_field_by_list(romset, 'Platform', platforms.AEL_platform_list,
                                    romset.get_platform, romset.set_platform):
            repository.update_romset(romset)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMSET_VIEW', {'romset_id': romset.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romset.get_parent_id()})            
    AppMediator.async_cmd('ROMSET_EDIT_METADATA', args)

@AppMediator.register('ROMSET_EDIT_METADATA_RELEASEYEAR')
def cmd_romset_metadata_releaseyear(args):
    romset_id = args['romset_id'] if 'romset_id' in args else None   
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)
        
        if editors.edit_field_by_str(romset, 'Release Year', romset.get_releaseyear, romset.set_releaseyear):
            repository.update_romset(romset)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMSET_VIEW', {'romset_id': romset.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romset.get_parent_id()})
    AppMediator.async_cmd('ROMSET_EDIT_METADATA', args)

@AppMediator.register('ROMSET_EDIT_METADATA_GENRE')
def cmd_romset_metadata_genre(args):
    romset_id = args['romset_id'] if 'romset_id' in args else None 
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)
        
        if editors.edit_field_by_str(romset, 'Genre', romset.get_genre, romset.set_genre):
            repository.update_romset(romset)
            uow.commit()            
            AppMediator.async_cmd('RENDER_ROMSET_VIEW', {'romset_id': romset.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romset.get_parent_id()})            
    AppMediator.async_cmd('ROMSET_EDIT_METADATA', args)
    
@AppMediator.register('ROMSET_EDIT_METADATA_DEVELOPER')
def cmd_romset_metadata_developer(args):
    romset_id = args['romset_id'] if 'romset_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)
        
        if editors.edit_field_by_str(romset, 'Developer', romset.get_developer, romset.set_developer):
            repository.update_romset(romset)
            uow.commit()    
            AppMediator.async_cmd('RENDER_ROMSET_VIEW', {'romset_id': romset.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romset.get_parent_id()})
    AppMediator.async_cmd('ROMSET_EDIT_METADATA', args)

@AppMediator.register('ROMSET_EDIT_METADATA_RATING')
def cmd_romset_metadata_rating(args):
    romset_id = args['romset_id'] if 'romset_id' in args else None   
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)
        
        if editors.edit_rating(romset, romset.get_rating, romset.set_rating):
            repository.update_romset(romset)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMSET_VIEW', {'romset_id': romset.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romset.get_parent_id()})
    AppMediator.async_cmd('ROMSET_EDIT_METADATA', args)

@AppMediator.register('ROMSET_EDIT_METADATA_PLOT')
def cmd_romset_metadata_plot(args):
    romset_id = args['romset_id'] if 'romset_id' in args else None  
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)
        
        if editors.edit_field_by_str(romset, 'Plot', romset.get_plot, romset.set_plot):
            repository.update_romset(romset)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMSET_VIEW', {'romset_id': romset.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romset.get_parent_id()})
    AppMediator.async_cmd('ROMSET_EDIT_METADATA', args)
    
@AppMediator.register('ROMSET_EDIT_METADATA_BOXSIZE')
def cmd_romset_metadata_boxsize(args):
    romset_id = args['romset_id'] if 'romset_id' in args else None  
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)

        if editors.edit_field_by_list(romset, 'Default box size', constants.BOX_SIZES,
                                    romset.get_box_sizing, romset.set_platset_box_sizingform):
            repository.update_romset(romset)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMSET_VIEW', {'romset_id': romset.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romset.get_parent_id()})            
    AppMediator.async_cmd('ROMSET_EDIT_METADATA', args)

# --- Import launcher metadata from NFO file (default location) ---
@AppMediator.register('ROMSET_IMPORT_NFO_FILE_DEFAULT')
def cmd_romset_import_nfo_file(args):
    romset_id = args['romset_id'] if 'romset_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)
        NFO_file = romset.get_NFO_name()
        
        if romset.import_NFO_file(NFO_file):
            repository.update_romset(romset)
            uow.commit()
            kodi.notify('Imported ROMSet NFO file {0}'.format(NFO_file.getPath()))
            AppMediator.async_cmd('RENDER_ROMSET_VIEW', {'romset_id': romset.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romset.get_parent_id()})
    
    AppMediator.async_cmd('ROMSET_EDIT_METADATA', args)

@AppMediator.register('ROMSET_IMPORT_NFO_FILE_BROWSE')
def cmd_romset_browse_import_nfo_file(args):    
    romset_id = args['romset_id'] if 'romset_id' in args else None
    
    NFO_file = kodi.browse(text='Select NFO description file', mask='.nfo')
    logger.debug('cmd_romset_browse_import_nfo_file() Dialog().browse returned "{0}"'.format(NFO_file))
    if not NFO_file: return
    NFO_FileName = io.FileName(NFO_file)
    if not NFO_FileName.exists(): return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)
        
        if romset.import_NFO_file(NFO_FileName):
            repository.update_romset(romset)
            uow.commit()
            kodi.notify('Imported ROMSet NFO file {0}'.format(NFO_FileName.getPath()))
            AppMediator.async_cmd('RENDER_ROMSET_VIEW', {'romset_id': romset.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romset.get_parent_id()})
    
    AppMediator.async_cmd('ROMSET_EDIT_METADATA', args)

@AppMediator.register('ROMSET_SAVE_NFO_FILE_DEFAULT')
def cmd_romset_save_nfo_file(args):
    romset_id = args['romset_id'] if 'romset_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)
        
    NFO_FileName = romset.get_NFO_name()
    # >> Returns False if exception happened. If an Exception happened function notifies
    # >> user, so display nothing to not overwrite error notification.
    try:
        romset.export_to_NFO_file(NFO_FileName)
    except:
        kodi.notify_warn('Exception writing NFO file {0}'.format(NFO_FileName.getPath()))
        logger.error("cmd_romset_save_nfo_file() Exception writing'{0}'".format(NFO_FileName.getPath()))
    else:
        logger.debug("cmd_romset_save_nfo_file() Created '{0}'".format(NFO_FileName.getPath()))
        kodi.notify('Exported ROMSet NFO file {0}'.format(NFO_FileName.getPath()))
    
    AppMediator.async_cmd('ROMSET_EDIT_METADATA', args)

@AppMediator.register('ROMSET_EXPORT_ROMSET_XML')
# --- Export Category XML configuration ---
def cmd_romset_export_xml(args):
    romset_id = args['romset_id'] if 'romset_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    category = None
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)
    
    romset_fn_str = 'Romset_' + text.str_to_filename_str(romset.get_name()) + '.xml'
    logger.debug('cmd_romset_export_xml() Exporting ROMSet configuration')
    logger.debug('cmd_romset_export_xml() Name     "{0}"'.format(romset.get_name()))
    logger.debug('cmd_romset_export_xml() ID       {0}'.format(romset.get_id()))
    logger.debug('cmd_romset_export_xml() l_fn_str "{0}"'.format(romset_fn_str))

    # --- Ask user for a path to export the launcher configuration ---
    dir_path = kodi.browse(type=0, text='Select directory to export XML')
    if not dir_path: 
        AppMediator.async_cmd('ROMSET_EDIT_METADATA', args)
        return

    # --- If XML exists then warn user about overwriting it ---
    export_FN = io.FileName(dir_path).pjoin(romset_fn_str)
    if export_FN.exists():
        ret = kodi.dialog_yesno('Overwrite file {0}?'.format(export_FN.getPath()))
        if not ret:
            kodi.notify_warn('Export of ROMSet XML cancelled')
            AppMediator.async_cmd('ROMSET_EDIT_METADATA', args)
            return

    # >> If everything goes all right when exporting then the else clause is executed.
    # >> If there is an error/exception then the exception handler prints a warning message
    # >> inside the function autoconfig_export_category() and the sucess message is never
    # >> printed. This is the standard way of handling error messages in AEL code.
    try:
        romset.export_to_file(export_FN)
    except constants.AddonError as E:
        kodi.notify_warn('{0}'.format(E))
    else:
        kodi.notify('Exported ROMSet "{0}" XML config'.format(romset.get_name()))
    
    AppMediator.async_cmd('ROMSET_EDIT_METADATA', args)