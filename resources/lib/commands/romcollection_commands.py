# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (romcollection management)
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

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals, editors
from resources.lib.repositories import UnitOfWork, CategoryRepository, ROMCollectionRepository
from resources.lib.domain import Category, ROMCollection, g_assetFactory

logger = logging.getLogger(__name__)

@AppMediator.register('ADD_ROMCOLLECTION')
def cmd_add_collection(args):
    logger.debug('cmd_add_collection() BEGIN')
    parent_id = args['category_id'] if 'category_id' in args else None
    grand_parent_id = args['parent_category_id'] if 'parent_category_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository              = CategoryRepository(uow)
        parent_category         = repository.find_category(parent_id) if parent_id is not None else None
        grand_parent_category  =  repository.find_category(grand_parent_id) if grand_parent_id is not None else None
        
        if grand_parent_category is not None:
            options_dialog = kodi.ListDialog()
            selected_option = options_dialog.select('Add ROM collection in?',[parent_category.get_name(), grand_parent_category.get_name()])
            if selected_option is None: return
            if selected_option > 0: parent_category = grand_parent_category
    
        wizard = kodi.WizardDialog_Selection(None, 'platform', 'Select the platform', platforms.AEL_platform_list)
        wizard = kodi.WizardDialog_Dummy(wizard, 'm_name', '', _get_name_from_platform)
        wizard = kodi.WizardDialog_Keyboard(wizard, 'm_name', 'Set the title of the launcher')
        wizard = kodi.WizardDialog_FileBrowse(wizard, 'assets_path', 'Select asset/artwork directory',0, '')
        
        romcollection = ROMCollection()
        entity_data = romcollection.get_data_dic()
        entity_data = wizard.runWizard(entity_data)
        if entity_data is None: return
        
        romcollection.import_data_dic(entity_data)
                
        # --- Determine box size based on platform --
        platform = platforms.get_AEL_platform(entity_data['platform'])
        romcollection.set_box_sizing(platform.default_box_size)
        
        romcollection_repository = ROMCollectionRepository(uow)
        romcollection_repository.insert_romcollection(romcollection, parent_category)
        uow.commit()
        
        kodi.notify('ROM Collection {0} created'.format(romcollection.get_name()))
        AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
        AppMediator.async_cmd('RENDER_VIEW', {'category_id': parent_category.get_id()})   
    
def _get_name_from_platform(input, item_key, entity_data):
    title = entity_data['platform']
    return title

# -------------------------------------------------------------------------------------------------
# ROMCollection context menu.
# -------------------------------------------------------------------------------------------------

# --- Main menu command ---
@AppMediator.register('EDIT_ROMCOLLECTION')
def cmd_edit_romcollection(args):

    logger.debug('EDIT_ROMCOLLECTION: cmd_edit_romcollection() BEGIN')
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    if romcollection_id is None:
        logger.warn('cmd_edit_romcollection(): No romcollection id supplied.')
        kodi.notify_warn("Invalid parameters supplied.")
        return
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)

        cat_repository = CategoryRepository(uow)
        parent_id = romcollection.get_parent_id()
        category = cat_repository.find_category(romcollection.get_parent_id()) if parent_id is None else None 
        category_name = 'None' if category is None else category.get_name()

    options = collections.OrderedDict()
    options['ROMCOLLECTION_EDIT_METADATA']       = 'Edit Metadata ...'
    options['ROMCOLLECTION_EDIT_ASSETS']         = 'Edit Assets/Artwork ...'
    options['ROMCOLLECTION_EDIT_DEFAULT_ASSETS'] = 'Choose default Assets/Artwork ...'
    if romcollection.has_launchers():
        options['EDIT_ROMCOLLECTION_LAUNCHERS']  = 'Manage associated launchers'
    else: options['ADD_LAUNCHER']         = 'Add new launcher'    
    options['ROMCOLLECTION_MANAGE_ROMS']         = 'Manage ROMs ...'
    options['EDIT_ROMCOLLECTION_CATEGORY']       = "Change Category: '{0}'".format(category_name)
    options['EDIT_ROMCOLLECTION_STATUS']         = 'ROM Collection status: {0}'.format(romcollection.get_finished_str())
    options['EXPORT_ROMCOLLECTION']              = 'Export ROM Collection XML configuration ...'
    options['DELETE_ROMCOLLECTION']              = 'Delete ROM Collection'

    s = 'Select action for ROM Collection "{}"'.format(romcollection.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_ROMCOLLECTION: cmd_edit_romcollection() Selected None. Closing context menu')
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('EDIT_ROMCOLLECTION: cmd_edit_romcollection() Selected {}'.format(selected_option))
    AppMediator.sync_cmd(selected_option, {
        'romcollection_id': romcollection_id, 'category_id': romcollection.get_parent_id()
    })

# --- Submenu commands ---
@AppMediator.register('ROMCOLLECTION_EDIT_METADATA')
def cmd_romcollection_metadata(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None
    selected_option = None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)

    plot_str = text.limit_string(romcollection.get_plot(), constants.PLOT_STR_MAXSIZE)
    rating = romcollection.get_rating() if romcollection.get_rating() != -1 else 'not rated'
    NFO_FileName = romcollection.get_NFO_name()
    NFO_found_str = 'NFO found' if NFO_FileName.exists() else 'NFO not found'

    options = collections.OrderedDict()
    options['ROMCOLLECTION_EDIT_METADATA_TITLE']       = "Edit Title: '{0}'".format(romcollection.get_name())
    options['ROMCOLLECTION_EDIT_METADATA_PLATFORM']    = "Edit Platform: {}".format(romcollection.get_platform())
    options['ROMCOLLECTION_EDIT_METADATA_RELEASEYEAR'] = "Edit Release Year:: {}".format(romcollection.get_releaseyear())
    options['ROMCOLLECTION_EDIT_METADATA_GENRE']       = "Edit Genre: '{0}'".format(romcollection.get_genre())
    options['ROMCOLLECTION_EDIT_METADATA_DEVELOPER']   = "Edit Developer: '{}'".format(romcollection.get_developer())
    options['ROMCOLLECTION_EDIT_METADATA_RATING']      = "Edit Rating: '{0}'".format(rating)
    options['ROMCOLLECTION_EDIT_METADATA_PLOT']        = "Edit Plot: '{0}'".format(plot_str)
    options['ROMCOLLECTION_EDIT_METADATA_BOXSIZE']     = "Edit Box Size: '{}'".format(romcollection.get_box_sizing())
    options['ROMCOLLECTION_IMPORT_NFO_FILE_DEFAULT']   = 'Import NFO file (default {0})'.format(NFO_found_str)
    options['ROMCOLLECTION_IMPORT_NFO_FILE_BROWSE']    = 'Import NFO file (browse NFO file) ...'
    options['ROMCOLLECTION_SAVE_NFO_FILE_DEFAULT']     = 'Save NFO file (default location)'

    s = 'Edit Launcher "{0}" metadata'.format(romcollection.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Return recursively to parent menu.
        logger.debug('cmd_romcollection_metadata(EDIT_METADATA) Selected NONE')
        AppMediator.sync_cmd('EDIT_ROMCOLLECTION', args)
        return

    # >> Execute launcher edit metadata atomic subcommand.
    # >> Then, execute recursively this submenu again.
    logger.debug('cmd_romcollection_metadata(EDIT_METADATA) Selected {0}'.format(selected_option))
    AppMediator.sync_cmd(selected_option, args)

@AppMediator.register('ROMCOLLECTION_EDIT_ASSETS')
def cmd_romcollection_edit_assets(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None
    preselected_option = args['selected_asset'] if 'selected_asset' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
        selected_asset_to_edit = editors.edit_object_assets(romcollection, preselected_option)
        if selected_asset_to_edit is None:
            AppMediator.sync_cmd('EDIT_ROMCOLLECTION', args)
            return
        
        if selected_asset_to_edit == editors.SCRAPE_CMD:
            AppMediator.async_cmd(editors.SCRAPE_CMD, args)
            return
        #    globals.run_command(scrape_cmd, rom=obj_instance)
        #    edit_object_assets(obj_instance, selected_option)
        #    return True
        
        asset = g_assetFactory.get_asset_info(selected_asset_to_edit)
        # >> Execute edit asset menu subcommand. Then, execute recursively this submenu again.
        # >> The menu dialog is instantiated again so it reflects the changes just edited.
        # >> If edit_asset() returns True changes were made.
        if editors.edit_asset(romcollection, asset):
            repository.update_romcollection(romcollection)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romcollection.get_parent_id()})     

    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_ASSETS', {'romcollection_id': romcollection.get_id(), 'selected_asset': asset.id})         

@AppMediator.register('ROMCOLLECTION_EDIT_DEFAULT_ASSETS')
def cmd_romcollection_edit_default_assets(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None
    preselected_option = args['selected_asset'] if 'selected_asset' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
        selected_asset_to_edit = editors.edit_object_default_assets(romcollection, preselected_option)
        if selected_asset_to_edit is None:
            AppMediator.sync_cmd('EDIT_ROMCOLLECTION', args)
            return

        if editors.edit_default_asset(romcollection, selected_asset_to_edit):
            repository.update_romcollection(romcollection)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romcollection.get_parent_id()})     

    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_DEFAULT_ASSETS', {'romcollection_id': romcollection.get_id(), 'selected_asset': selected_asset_to_edit.id})         
    
@AppMediator.register('EDIT_ROMCOLLECTION_STATUS')
def cmd_romcollection_status(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        romcollection.change_finished_status()
        kodi.dialog_OK('ROMCollection "{}" status is now {}'.format(romcollection.get_name(), romcollection.get_finished_str()))
        repository.update_romcollection(romcollection)
        uow.commit()
        
    AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
    AppMediator.async_cmd('RENDER_VIEW', {'category_id': romcollection.get_parent_id()})     
    AppMediator.sync_cmd('EDIT_ROMCOLLECTION', args)
    
#
# Remove ROMCollection
#
@AppMediator.register('DELETE_ROMCOLLECTION')
def cmd_romcollection_delete(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        romcollection_name = romcollection.get_name()
        
        if romcollection.num_roms() > 0:
            question = 'ROMCollection "{0}" has {1} ROMs. '.format(romcollection_name, romcollection.num_roms()) + \
                        'Are you sure you want to delete it?'
        else:
            question = 'Are you sure you want to delete "{}"?'.format(romcollection_name)
    
        ret = kodi.dialog_yesno(question)
        if not ret: return
            
        logger.info('Deleting romcollection "{}" ID {}'.format(romcollection_name, romcollection.get_id()))
        repository.delete_romcollection(romcollection.get_id())
        uow.commit()
        
    kodi.notify('Deleted romcollection {0}'.format(romcollection_name))
    AppMediator.async_cmd('RENDER_VIEW', {'category_id': romcollection.get_parent_id()})            
    AppMediator.async_cmd('CLEANUP_VIEWS')
    AppMediator.sync_cmd('EDIT_ROMCOLLECTION', args)

# --- Atomic commands ---
# --- Edition of the launcher name ---
@AppMediator.register('ROMCOLLECTION_EDIT_METADATA_TITLE')
def cmd_romcollection_metadata_title(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None  
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
        if editors.edit_field_by_str(romcollection, 'Title', romcollection.get_name, romcollection.set_name):
            repository.update_romcollection(romcollection)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romcollection.get_parent_id()})            
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)

@AppMediator.register('ROMCOLLECTION_EDIT_METADATA_PLATFORM')
def cmd_romcollection_metadata_platform(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None  
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)

        if editors.edit_field_by_list(romcollection, 'Platform', platforms.AEL_platform_list,
                                    romcollection.get_platform, romcollection.set_platform):
            repository.update_romcollection(romcollection)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romcollection.get_parent_id()})            
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)

@AppMediator.register('ROMCOLLECTION_EDIT_METADATA_RELEASEYEAR')
def cmd_romcollection_metadata_releaseyear(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None   
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
        if editors.edit_field_by_str(romcollection, 'Release Year', romcollection.get_releaseyear, romcollection.set_releaseyear):
            repository.update_romcollection(romcollection)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romcollection.get_parent_id()})
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)

@AppMediator.register('ROMCOLLECTION_EDIT_METADATA_GENRE')
def cmd_romcollection_metadata_genre(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None 
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
        if editors.edit_field_by_str(romcollection, 'Genre', romcollection.get_genre, romcollection.set_genre):
            repository.update_romcollection(romcollection)
            uow.commit()            
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romcollection.get_parent_id()})            
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)
    
@AppMediator.register('ROMCOLLECTION_EDIT_METADATA_DEVELOPER')
def cmd_romcollection_metadata_developer(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
        if editors.edit_field_by_str(romcollection, 'Developer', romcollection.get_developer, romcollection.set_developer):
            repository.update_romcollection(romcollection)
            uow.commit()    
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romcollection.get_parent_id()})
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)

@AppMediator.register('ROMCOLLECTION_EDIT_METADATA_RATING')
def cmd_romcollection_metadata_rating(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None   
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
        if editors.edit_rating(romcollection, romcollection.get_rating, romcollection.set_rating):
            repository.update_romcollection(romcollection)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romcollection.get_parent_id()})
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)

@AppMediator.register('ROMCOLLECTION_EDIT_METADATA_PLOT')
def cmd_romcollection_metadata_plot(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None  
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
        if editors.edit_field_by_str(romcollection, 'Plot', romcollection.get_plot, romcollection.set_plot):
            repository.update_romcollection(romcollection)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romcollection.get_parent_id()})
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)
    
@AppMediator.register('ROMCOLLECTION_EDIT_METADATA_BOXSIZE')
def cmd_romcollection_metadata_boxsize(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None  
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)

        if editors.edit_field_by_list(romcollection, 'Default box size', constants.BOX_SIZES,
                                    romcollection.get_box_sizing, romcollection.set_box_sizing):
            repository.update_romcollection(romcollection)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romcollection.get_parent_id()})            
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)

# --- Import launcher metadata from NFO file (default location) ---
@AppMediator.register('ROMCOLLECTION_IMPORT_NFO_FILE_DEFAULT')
def cmd_romcollection_import_nfo_file(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        NFO_file = romcollection.get_NFO_name()
        
        if romcollection.import_NFO_file(NFO_file):
            repository.update_romcollection(romcollection)
            uow.commit()
            kodi.notify('Imported ROMCollection NFO file {0}'.format(NFO_file.getPath()))
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romcollection.get_parent_id()})
    
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)

@AppMediator.register('ROMCOLLECTION_IMPORT_NFO_FILE_BROWSE')
def cmd_romcollection_browse_import_nfo_file(args):    
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None
    
    NFO_file = kodi.browse(text='Select NFO description file', mask='.nfo')
    logger.debug('cmd_romcollection_browse_import_nfo_file() Dialog().browse returned "{0}"'.format(NFO_file))
    if not NFO_file: return
    NFO_FileName = io.FileName(NFO_file)
    if not NFO_FileName.exists(): return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
        if romcollection.import_NFO_file(NFO_FileName):
            repository.update_romcollection(romcollection)
            uow.commit()
            kodi.notify('Imported ROMCollection NFO file {0}'.format(NFO_FileName.getPath()))
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_VIEW', {'category_id': romcollection.get_parent_id()})
    
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)

@AppMediator.register('ROMCOLLECTION_SAVE_NFO_FILE_DEFAULT')
def cmd_romcollection_save_nfo_file(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
    NFO_FileName = romcollection.get_NFO_name()
    # >> Returns False if exception happened. If an Exception happened function notifies
    # >> user, so display nothing to not overwrite error notification.
    try:
        romcollection.export_to_NFO_file(NFO_FileName)
    except:
        kodi.notify_warn('Exception writing NFO file {0}'.format(NFO_FileName.getPath()))
        logger.error("cmd_romcollection_save_nfo_file() Exception writing'{0}'".format(NFO_FileName.getPath()))
    else:
        logger.debug("cmd_romcollection_save_nfo_file() Created '{0}'".format(NFO_FileName.getPath()))
        kodi.notify('Exported ROMCollection NFO file {0}'.format(NFO_FileName.getPath()))
    
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)

@AppMediator.register('ROMCOLLECTION_EXPORT_ROMCOLLECTION_XML')
# --- Export Category XML configuration ---
def cmd_romcollection_export_xml(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
    
    romcollection_fn_str = 'Romset_' + text.str_to_filename_str(romcollection.get_name()) + '.xml'
    logger.debug('cmd_romcollection_export_xml() Exporting ROMCollection configuration')
    logger.debug('cmd_romcollection_export_xml() Name     "{0}"'.format(romcollection.get_name()))
    logger.debug('cmd_romcollection_export_xml() ID       {0}'.format(romcollection.get_id()))
    logger.debug('cmd_romcollection_export_xml() l_fn_str "{0}"'.format(romcollection_fn_str))

    # --- Ask user for a path to export the launcher configuration ---
    dir_path = kodi.browse(type=0, text='Select directory to export XML')
    if not dir_path: 
        AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)
        return

    # --- If XML exists then warn user about overwriting it ---
    export_FN = io.FileName(dir_path).pjoin(romcollection_fn_str)
    if export_FN.exists():
        ret = kodi.dialog_yesno('Overwrite file {0}?'.format(export_FN.getPath()))
        if not ret:
            kodi.notify_warn('Export of ROMCollection XML cancelled')
            AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)
            return

    # >> If everything goes all right when exporting then the else clause is executed.
    # >> If there is an error/exception then the exception handler prints a warning message
    # >> inside the function autoconfig_export_category() and the sucess message is never
    # >> printed. This is the standard way of handling error messages in AEL code.
    try:
        romcollection.export_to_file(export_FN)
    except constants.AddonError as E:
        kodi.notify_warn('{0}'.format(E))
    else:
        kodi.notify('Exported ROMCollection "{0}" XML config'.format(romcollection.get_name()))
    
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)