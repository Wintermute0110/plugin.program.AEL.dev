# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (ROM management)
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

from ael import constants, settings
from ael.utils import kodi, text, io

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals, editors
from resources.lib.repositories import ROMsRepository, ROMCollectionRepository, UnitOfWork
from resources.lib.domain import g_assetFactory

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# ROM context menu.
# -------------------------------------------------------------------------------------------------

# --- Main menu command ---
@AppMediator.register('EDIT_ROM')
def cmd_edit_rom(args):
    logger.debug('EDIT_ROM: cmd_edit_rom() BEGIN')
    rom_id:str = args['rom_id'] if 'rom_id' in args else None
    
    if rom_id is None:
        logger.warning('cmd_edit_rom(): No ROM id supplied.')
        kodi.notify_warn("Invalid parameters supplied.")
        return
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)

    options = collections.OrderedDict()
    options['ROM_EDIT_METADATA']       = 'Edit Metadata ...'
    options['ROM_EDIT_ASSETS']         = 'Edit Assets/Artwork ...'
    options['EDIT_ROM_STATUS']         = 'ROM status: {0}'.format(rom.get_finished_str())
    options['DELETE_ROM']              = 'Delete ROM'
    options['SCRAPE_ROM']              = 'Scrape ROM'

    s = 'Edit ROM "{}"'.format(rom.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_ROM: cmd_edit_rom() Selected None. Closing context menu')
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('EDIT_ROM: cmd_edit_rom() Selected {}'.format(selected_option))
    AppMediator.sync_cmd(selected_option, args)
    
# --- Submenu commands ---
@AppMediator.register('ROM_EDIT_METADATA')
def cmd_rom_metadata(args):
    rom_id:str = args['rom_id'] if 'rom_id' in args else None
    selected_option = None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
    plot_str      = text.limit_string(rom.get_plot(), constants.PLOT_STR_MAXSIZE)
    rating        = rom.get_rating() if rom.get_rating() != -1 else 'not rated'
    NFO_FileName  = rom.get_nfo_file()
    NFO_found_str = 'NFO found' if NFO_FileName and NFO_FileName.exists() else 'NFO not found'

    options = collections.OrderedDict()
    options['ROM_EDIT_METADATA_TITLE']       = "Edit Title: '{}'".format(rom.get_name())
    options['ROM_EDIT_METADATA_RELEASEYEAR'] = "Edit Release Year: {}".format(rom.get_releaseyear())
    options['ROM_EDIT_METADATA_GENRE']       = "Edit Genre: '{}'".format(rom.get_genre())
    options['ROM_EDIT_METADATA_DEVELOPER']   = "Edit Developer: '{}'".format(rom.get_developer())
    options['ROM_EDIT_METADATA_NPLAYERS']    = "Edit NPlayers: '{}'".format(rom.get_number_of_players())
    options['ROM_EDIT_METADATA_ESRB']        = "Edit ESRB rating: '{}'".format(rom.get_esrb_rating())
    options['ROM_EDIT_METADATA_RATING']      = "Edit Rating: '{}'".format(rating)
    options['ROM_EDIT_METADATA_PLOT']        = "Edit Plot: '{}'".format(plot_str)
    options['ROM_EDIT_METADATA_BOXSIZE']     = "Edit Box Size: '{}'".format(rom.get_box_sizing())
    options['ROM_LOAD_PLOT']                 = "Load Plot from TXT file ..."
    options['ROM_IMPORT_NFO_FILE_DEFAULT']   = 'Import NFO file (default {})'.format(NFO_found_str)
    options['ROM_IMPORT_NFO_FILE_BROWSE']    = 'Import NFO file (browse NFO file) ...'
    options['ROM_SAVE_NFO_FILE_DEFAULT']     = 'Save NFO file (default location)'
    options['SCRAPE_ROM_METADATA']           = 'Scrape Metadata'

    s = 'Edit ROM "{0}" metadata'.format(rom.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Return recursively to parent menu.
        logger.debug('cmd_rom_metadata(EDIT_METADATA) Selected NONE')
        AppMediator.sync_cmd('EDIT_ROM', args)
        return

    # >> Execute edit metadata atomic subcommand.
    # >> Then, execute recursively this submenu again.
    logger.debug('cmd_rom_metadata(EDIT_METADATA) Selected {0}'.format(selected_option))
    AppMediator.sync_cmd(selected_option, args)
    
@AppMediator.register('ROM_EDIT_ASSETS')
def cmd_rom_assets(args):
    rom_id:str = args['rom_id'] if 'rom_id' in args else None
    preselected_option = args['selected_asset'] if 'selected_asset' in args else None    
       
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        romcollection_repository = ROMCollectionRepository(uow)
        rom_romcollections = romcollection_repository.find_romcollections_by_rom(rom_id)
        rom_collection_ids = [collection.get_id() for collection in rom_romcollections]
                
        selected_asset_to_edit = editors.edit_object_assets(rom, preselected_option)
        if selected_asset_to_edit is None:
            AppMediator.sync_cmd('EDIT_ROM', args)
            return
        
        if selected_asset_to_edit == editors.SCRAPE_CMD:
            AppMediator.sync_cmd(editors.SCRAPE_CMD, args)
            return
        
        asset = g_assetFactory.get_asset_info(selected_asset_to_edit)    
        # >> Execute edit asset menu subcommand. Then, execute recursively this submenu again.
        # >> The menu dialog is instantiated again so it reflects the changes just edited.
        # >> If edit_asset() returns a command other than scrape or None changes were made.
        cmd = editors.edit_asset(rom, asset)
        if cmd is not None:
            if cmd == 'SCRAPE_ASSET':
                args['selected_asset'] = asset.id
                AppMediator.sync_cmd('SCRAPE_ROM_ASSET', args)
                return
            
            repository.update_rom(rom)
            uow.commit()
            for romcollection_id in rom_collection_ids:
                AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection_id})   

    AppMediator.sync_cmd('ROM_EDIT_ASSETS', {'rom_id': rom_id, 'selected_asset': asset.id})    

# --- Atomic commands ---
@AppMediator.register('ROM_EDIT_METADATA_TITLE')
def cmd_rom_metadata_title(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None  
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        if editors.edit_field_by_str(rom, 'Title', rom.get_name, rom.set_name):
            repository.update_rom(rom)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
            AppMediator.async_cmd('RENDER_VCATEGORY_VIEW', {'vcategory_id': constants.VCATEGORY_TITLE_ID})
            
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)

@AppMediator.register('ROM_EDIT_METADATA_ESRB')
def cmd_rom_metadata_platform(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None  
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)

        if editors.edit_field_by_list(rom, 'ESRB rating', constants.ESRB_LIST,
                                    rom.get_esrb_rating, rom.set_esrb_rating):
            repository.update_rom(rom)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
            AppMediator.async_cmd('RENDER_VCATEGORY_VIEW', {'vcategory_id': constants.VCATEGORY_ESRB_ID})
                
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)

@AppMediator.register('ROM_EDIT_METADATA_RELEASEYEAR')
def cmd_rom_metadata_releaseyear(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None   
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        if editors.edit_field_by_str(rom, 'Release Year', rom.get_releaseyear, rom.set_releaseyear):
            repository.update_rom(rom)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
            AppMediator.async_cmd('RENDER_VCATEGORY_VIEW', {'vcategory_id': constants.VCATEGORY_YEARS_ID})
            
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)

@AppMediator.register('ROM_EDIT_METADATA_GENRE')
def cmd_rom_metadata_genre(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None 
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        if editors.edit_field_by_str(rom, 'Genre', rom.get_genre, rom.set_genre):
            repository.update_rom(rom)
            uow.commit()            
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
            AppMediator.async_cmd('RENDER_VCATEGORY_VIEW', {'vcategory_id': constants.VCATEGORY_GENRE_ID})
                    
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)
    
@AppMediator.register('ROM_EDIT_METADATA_DEVELOPER')
def cmd_rom_metadata_developer(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        if editors.edit_field_by_str(rom, 'Developer', rom.get_developer, rom.set_developer):
            repository.update_rom(rom)
            uow.commit()    
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
            AppMediator.async_cmd('RENDER_VCATEGORY_VIEW', {'vcategory_id': constants.VCATEGORY_DEVELOPER_ID})
            
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)

@AppMediator.register('ROM_EDIT_METADATA_NPLAYERS')
def cmd_rom_metadata_nplayers(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        menu_list = ['Not set', 'Manual entry'] + constants.NPLAYERS_LIST
        selected_option = kodi.ListDialog().select('Edit ROM NPlayers', menu_list)
        
        if selected_option is None or selected_option < 0:
            AppMediator.sync_cmd('ROM_EDIT_METADATA', args)
            return

        if selected_option == 0:
            rom.set_number_of_players('')
    
        if selected_option == 1:
            # >> Manual entry. Open a text entry dialog.
            if not editors.edit_field_by_str(rom, 'NPlayers', rom.get_number_of_players, rom.set_number_of_players):
                AppMediator.sync_cmd('ROM_EDIT_METADATA', args)
                return

        if selected_option > 1:
            list_idx = selected_option - 2
            rom.set_number_of_players(constants.NPLAYERS_LIST[list_idx]) 
                
        repository.update_rom(rom)
        uow.commit()    
        AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
        AppMediator.async_cmd('RENDER_VCATEGORY_VIEW', {'vcategory_id': constants.VCATEGORY_NPLAYERS_ID})
        kodi.notify('Changed ROM NPlayers')
        
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)

@AppMediator.register('ROM_EDIT_METADATA_RATING')
def cmd_rom_metadata_rating(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None   
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        if editors.edit_rating(rom, rom.get_rating, rom.set_rating):
            repository.update_rom(rom)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
            AppMediator.async_cmd('RENDER_VCATEGORY_VIEW', {'vcategory_id': constants.VCATEGORY_RATING_ID})
            
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)

@AppMediator.register('ROM_EDIT_METADATA_PLOT')
def cmd_rom_metadata_plot(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None  
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        if editors.edit_field_by_str(rom, 'Plot', rom.get_plot, rom.set_plot):
            repository.update_rom(rom)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)
    
@AppMediator.register('ROM_EDIT_METADATA_BOXSIZE')
def cmd_rom_metadata_boxsize(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None  
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)

        if editors.edit_field_by_list(rom, 'Default box size', constants.BOX_SIZES,
                                    rom.get_box_sizing, rom.set_box_sizing):
            repository.update_rom(rom)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})        
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)

@AppMediator.register('ROM_LOAD_PLOT')
def cmd_rom_load_plot(args):    
    rom_id = args['rom_id'] if 'rom_id' in args else None
    
    plot_file = kodi.browse(text='Select description file (TXT|DAT)', mask='.txt|.dat')
    logger.debug('cmd_rom_load_plot() Dialog().browse returned "{0}"'.format(plot_file))
    if not plot_file: return
    plot_FileName = io.FileName(plot_file)
    if not plot_FileName.exists(): return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        file_data = editors.import_TXT_file(plot_FileName)
        rom.set_plot(file_data)
        
        repository.update_rom(rom)
        uow.commit()
        kodi.notify('Imported ROM Plot')
        AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
    
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)
    
# --- Import ROM metadata from NFO file (default location) ---
@AppMediator.register('ROM_IMPORT_NFO_FILE_DEFAULT')
def cmd_rom_import_nfo_file(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        NFO_file = rom.get_nfo_file()
        
        if not NFO_file:
            kodi.dialog_OK('No NFO file available')
            return
        
        if rom.update_with_nfo_file(NFO_file):
            repository.update_rom(rom)
            uow.commit()
            kodi.notify('Imported ROMCollection NFO file {0}'.format(NFO_file.getPath()))
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
            AppMediator.async_cmd('RENDER_VCATEGORY_VIEWS')
    
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)

@AppMediator.register('ROM_IMPORT_NFO_FILE_BROWSE')
def cmd_rom_browse_import_nfo_file(args):    
    rom_id = args['rom_id'] if 'rom_id' in args else None
    
    NFO_file = kodi.browse(text='Select NFO description file', mask='.nfo')
    logger.debug('cmd_rom_browse_import_nfo_file() Dialog().browse returned "{0}"'.format(NFO_file))
    if not NFO_file: return
    NFO_FileName = io.FileName(NFO_file)
    if not NFO_FileName.exists(): return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        if rom.update_with_nfo_file(NFO_FileName):
            repository.update_rom(rom)
            uow.commit()
            kodi.notify('Imported ROMCollection NFO file {0}'.format(NFO_FileName.getPath()))
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
            AppMediator.async_cmd('RENDER_VCATEGORY_VIEWS')
    
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)

@AppMediator.register('ROM_SAVE_NFO_FILE_DEFAULT')
def cmd_rom_save_nfo_file(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
    NFO_FileName = rom.get_nfo_file()
    # >> Returns False if exception happened. If an Exception happened function notifies
    # >> user, so display nothing to not overwrite error notification.
    try:
        rom.export_to_NFO_file(NFO_FileName)
    except:
        kodi.notify_warn('Exception writing NFO file {0}'.format(NFO_FileName.getPath()))
        logger.error("cmd_rom_save_nfo_file() Exception writing'{0}'".format(NFO_FileName.getPath()))
    else:
        logger.debug("cmd_rom_save_nfo_file() Created '{0}'".format(NFO_FileName.getPath()))
        kodi.notify('Exported ROMCollection NFO file {0}'.format(NFO_FileName.getPath()))
    
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)

# --- Atomic commands - ASSETS ---