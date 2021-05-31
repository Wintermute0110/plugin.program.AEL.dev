# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (romset roms management)
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
from resources.lib import constants, globals
from resources.lib import repositories
from resources.lib.repositories import *
from resources.lib.utils import kodi

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# ROMSet ROM management.
# -------------------------------------------------------------------------------------------------

# --- Submenu menu command ---
@AppMediator.register('ROMSET_MANAGE_ROMS')
def cmd_manage_roms(args):
    logger.debug('ROMSET_MANAGE_ROMS: cmd_manage_roms() SHOW MENU')
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    
    if romset_id is None:
        logger.warn('cmd_manage_roms(): No romset id supplied.')
        kodi.notify_warn("Invalid parameters supplied.")
        return
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)

    options = collections.OrderedDict()
    options['SET_ROMS_DEFAULT_ARTWORK']  = 'Choose ROMs default artwork ...'
    options['SET_ROMS_ASSET_DIRS']       = 'Manage ROMs asset directories ...'
    options['SCRAPE_ROMS']               = 'Scrape ROMs'
    options['REMOVE_DEAD_ROMS']          = 'Remove dead/missing ROMs'
    options['IMPORT_ROMS']               = 'Import ROMs metadata from NFO files'
    options['EXPORT_ROMS']               = 'Export ROMs metadata to NFO files'
    options['DELETE_ROMS_NFO']           = 'Delete ROMs NFO files'
    options['CLEAR_ROMS']                = 'Clear ROMs from ROMSet'

    s = 'Manage ROMSet "{}" ROMs'.format(romset.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('ROMSET_MANAGE_ROMS: cmd_manage_roms() Selected None. Closing context menu')
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('ROMSET_MANAGE_ROMS: cmd_manage_roms() Selected {}'.format(selected_option))
    kodi.event(method=selected_option, data=args)

# --- Choose default ROMs assets/artwork ---
@AppMediator.register('SET_ROMS_DEFAULT_ARTWORK')
def cmd_set_roms_default_artwork(args):
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    
    # if not launcher.supports_launching_roms():
    #     kodi.dialog_OK(
    #         'm_subcommand_set_roms_default_artwork() ' +
    #         'Launcher "{0}" is not a ROM launcher.'.format(launcher.__class__.__name__) +
    #         'This is a bug, please report it.')
    #     return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)

        # --- Build Dialog.select() list ---
        default_assets_list = romset.get_ROM_mappable_asset_list()
        options = collections.OrderedDict()
        for default_asset_info in default_assets_list:
            # >> Label is the string 'Choose asset for XXXX (currently YYYYY)'
            mapped_asset_key = romset.get_mapped_ROM_asset_key(default_asset_info)
            mapped_asset_info = g_assetFactory.get_asset_info_by_key(mapped_asset_key)
            # --- Append to list of ListItems ---
            options[default_asset_info] = 'Choose asset for {0} (currently {1})'.format(default_asset_info.name, mapped_asset_info.name)
        
        dialog = kodi.OrdDictionaryDialog()
        selected_asset_info = dialog.select('Edit ROMs default Assets/Artwork', options)
        
        if selected_asset_info is None:
            # >> Return to parent menu.
            logger.debug('cmd_set_roms_default_artwork() Main selected NONE. Returning to parent menu.')
            return
        
        logger.debug('cmd_set_roms_default_artwork() Main select() returned {0}'.format(selected_asset_info.name))    
        mapped_asset_key    = romset.get_mapped_ROM_asset_key(selected_asset_info)
        mapped_asset_info   = g_assetFactory.get_asset_info_by_key(mapped_asset_key)
        mappable_asset_list = g_assetFactory.get_asset_list_by_IDs(ROM_ASSET_ID_LIST, 'image')
        logger.debug('cmd_set_roms_default_artwork() {0} currently is mapped to {1}'.format(selected_asset_info.name, mapped_asset_info.name))
            
        # --- Create ListItems ---
        options = collections.OrderedDict()
        for mappable_asset_info in mappable_asset_list:
            # >> Label is the asset name (Icon, Fanart, etc.)
            options[mappable_asset_info] = mappable_asset_info.name

        dialog = kodi.OrdDictionaryDialog()
        dialog_title_str = 'Edit {0} {1} mapped asset'.format(
            romset.get_object_name(), selected_asset_info.name)
        new_selected_asset_info = dialog.select(dialog_title_str, options, mapped_asset_info)
    
        if new_selected_asset_info is None:
            # >> Return to this method recursively to previous menu.
            logger.debug('cmd_set_roms_default_artwork() Mapable selected NONE. Returning to previous menu.')
            kodi.event(method='ROMSET_MANAGE_ROMS', data=args)
            return   
        
        logger.debug('cmd_set_roms_default_artwork() Mapable selected {0}.'.format(new_selected_asset_info.name))
        romset.set_mapped_ROM_asset_key(selected_asset_info, new_selected_asset_info)
        kodi.notify('{0} {1} mapped to {2}'.format(
            romset.get_object_name(), selected_asset_info.name, new_selected_asset_info.name
        ))
        
        repository.update_romset(romset)
        uow.commit()
        kodi.event(method='RENDER_ROMSET_VIEW', data={'romset_id': romset.get_id()})
        kodi.event(method='RENDER_VIEW', data={'category_id': romset.get_parent_id()})     

    kodi.event(method='SET_ROMS_DEFAULT_ARTWORK', data={'romset_id': romset.get_id(), 'selected_asset': selected_asset_info.id})         

@AppMediator.register('SET_ROMS_ASSET_DIRS')
def cmd_set_rom_asset_dirs(args):
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    
    list_items = {}
    assets = g_assetFactory.get_all()

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)

        # --- Scrape ROMs artwork ---
        # >> Mimic what the ROM scanner does. Use same settings as the ROM scanner.
        # >> Like the ROM scanner, only scrape artwork not found locally.
        # elif type2 == 3:
        #     kodi_dialog_OK('WIP feature not coded yet, sorry.')
        #     return

        for asset_info in assets:
            path = romset.get_asset_path(asset_info)
            if path:
                list_items[asset_info] = "Change {0} path: '{1}'".format(asset_info.plural, path.getPath())

        dialog = kodi.OrdDictionaryDialog()
        selected_asset = dialog.select('ROM Asset directories ', list_items)

        if selected_asset is None:    
            return

        selected_asset_path = launcher.get_asset_path(selected_asset)
        dialog = xbmcgui.Dialog()
        dir_path = dialog.browse(0, 'Select {0} path'.format(selected_asset.plural), 'files', '', False, False, selected_asset_path.getPath()).decode('utf-8')
        if not dir_path or dir_path == selected_asset_path.getPath():  
            self._subcommand_set_rom_asset_dirs(launcher)
            return
                
        launcher.set_asset_path(selected_asset, dir_path)
        g_LauncherRepository.save(launcher)
                
    # >> Check for duplicate paths and warn user.
    duplicated_name_list = launcher.get_duplicated_asset_dirs()
    if duplicated_name_list:
        duplicated_asset_srt = ', '.join(duplicated_name_list)
        kodi_dialog_OK('Duplicated asset directories: {0}. '.format(duplicated_asset_srt) +
                        'AEL will refuse to add/edit ROMs if there are duplicate asset directories.')

    kodi_notify('Changed rom asset dir for {0} to {1}'.format(selected_asset.name, dir_path))
    self._subcommand_set_rom_asset_dirs(launcher)
    return    