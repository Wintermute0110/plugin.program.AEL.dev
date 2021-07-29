# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (romcollection launcher management)
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
import json

from ael import constants
from ael.utils import kodi

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import UnitOfWork, ROMCollectionRepository, ROMsRepository, AelAddonRepository
from resources.lib.domain import AelAddon, ROMLauncherAddon

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# ROMCollection launcher management.
# -------------------------------------------------------------------------------------------------

# --- Submenu menu command ---
@AppMediator.register('EDIT_ROMCOLLECTION_LAUNCHERS')
def cmd_manage_romcollection_launchers(args):
    logger.debug('EDIT_ROMCOLLECTION_LAUNCHERS: cmd_manage_romcollection_launchers() SHOW MENU')
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
    launchers = romcollection.get_launchers()
    default_launcher = next((l for l in launchers if l.is_default()), launchers[0]) if len(launchers) > 0 else None
    default_launcher_name = default_launcher.get_name() if default_launcher is not None else 'None'
    
    options = collections.OrderedDict()
    options['ADD_LAUNCHER']         = 'Add new launcher'
    options['EDIT_LAUNCHER']        = 'Edit launcher'
    options['REMOVE_LAUNCHER']      = 'Remove launcher'
    options['SET_DEFAULT_LAUNCHER'] = 'Set default launcher: "{}"'.format(default_launcher_name)
        
    s = 'Manage Launchers for "{}"'.format(romcollection.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_ROMCOLLECTION_LAUNCHERS: cmd_manage_romcollection_launchers() Selected None. Closing context menu')
        AppMediator.sync_cmd('EDIT_ROMCOLLECTION', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('EDIT_ROMCOLLECTION_LAUNCHERS: cmd_manage_romcollection_launchers() Selected {}'.format(selected_option))
    AppMediator.sync_cmd(selected_option, args)

# --- Sub commands ---
@AppMediator.register('ADD_LAUNCHER')
def cmd_add_romcollection_launchers(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    options = collections.OrderedDict()
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository        = AelAddonRepository(uow)
        romcollection_repository = ROMCollectionRepository(uow)
        
        addons = repository.find_all_launchers()
        romcollection = romcollection_repository.find_romcollection(romcollection_id)

        for addon in addons:
            options[addon] = addon.get_name()
    
    s = 'Choose launcher to associate'
    selected_option:AelAddon = kodi.OrdDictionaryDialog().select(s, options)
    
    if selected_option is None:
        # >> Exits context menu
        logger.debug('ADD_LAUNCHER: cmd_add_romcollection_launchers() Selected None. Closing context menu')
        AppMediator.sync_cmd('EDIT_ROMCOLLECTION_LAUNCHERS', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('ADD_LAUNCHER: cmd_add_romcollection_launchers() Selected {}'.format(selected_option.get_id()))
    
    kodi.run_script(selected_option.get_addon_id(), {
        '--cmd': 'configure',
        '--type': constants.AddonType.LAUNCHER.name,
        '--romcollection_id': romcollection_id#, 
        #'--settings': '"{}"'.format(json.dumps({'platform': romcollection.get_platform()}))
    })

@AppMediator.register('EDIT_LAUNCHER')
def cmd_edit_romcollection_launchers(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romcollection_repository = ROMCollectionRepository(uow)        
        romcollection = romcollection_repository.find_romcollection(romcollection_id)
    
    launchers = romcollection.get_launchers()
    if len(launchers) == 0:
        kodi.notify('No launchers configured for this romcollection!')
        AppMediator.async_cmd('EDIT_ROMCOLLECTION_LAUNCHERS', args)
        return
    
    options = collections.OrderedDict()
    for launcher in launchers:
        options[launcher] = launcher.get_name()
    
    s = 'Choose launcher to edit'
    selected_option:ROMLauncherAddon = kodi.OrdDictionaryDialog().select(s, options)
    
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_LAUNCHER: cmd_edit_romcollection_launchers() Selected None. Closing context menu')
        AppMediator.async_cmd('EDIT_ROMCOLLECTION_LAUNCHERS', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('EDIT_LAUNCHER: cmd_edit_romcollection_launchers() Selected {}'.format(selected_option.get_id()))
    kodi.run_script(selected_option.addon.get_addon_id(), {
        '--cmd': 'configure',
        '--type': constants.AddonType.LAUNCHER.name,
        '--romcollection_id': romcollection_id, 
        '--launcher_id': selected_option.get_id(),
        '--settings': '"{}"'.format(selected_option.get_settings_str())
    })
       
@AppMediator.register('REMOVE_LAUNCHER')
def cmd_remove_romcollection_launchers(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romcollection_repository = ROMCollectionRepository(uow)        
        romcollection = romcollection_repository.find_romcollection(romcollection_id)
    
        launchers = romcollection.get_launchers()
        if len(launchers) == 0:
            kodi.notify('No launchers configured for this romcollection!')
            AppMediator.sync_cmd('EDIT_ROMCOLLECTION_LAUNCHERS', args)
            return
        
        options = collections.OrderedDict()
        for launcher in launchers:
            options[launcher] = launcher.get_name()
        
        s = 'Choose launcher to remove'
        selected_option:ROMLauncherAddon = kodi.OrdDictionaryDialog().select(s, options)
        
        if selected_option is None:
            # >> Exits context menu
            logger.debug('REMOVE_LAUNCHER: cmd_remove_romcollection_launchers() Selected None. Closing context menu')
            AppMediator.sync_cmd('EDIT_ROMCOLLECTION_LAUNCHERS', args)
            return
        
        # >> Execute subcommand. May be atomic, maybe a submenu.
        logger.debug('REMOVE_LAUNCHER: cmd_remove_romcollection_launchers() Selected {}'.format(selected_option.get_id()))
        if not kodi.dialog_yesno('Are you sure to delete launcher "{}"'.format(selected_option.get_name())):
            logger.debug('REMOVE_LAUNCHER: cmd_remove_romcollection_launchers() Cancelled operation.')
            AppMediator.async_cmd('EDIT_ROMCOLLECTION_LAUNCHERS', args)
            return
        
        romcollection_repository.remove_launcher(romcollection.get_id(), selected_option.get_id())
        logger.info('REMOVE_LAUNCHER: cmd_remove_romcollection_launchers() Removed launcher#{}'.format(selected_option.get_id()))
        uow.commit()
    
    AppMediator.sync_cmd('EDIT_ROMCOLLECTION_LAUNCHERS', args)
    
@AppMediator.register('SET_DEFAULT_LAUNCHER')
def cmd_set_default_romcollection_launchers(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romcollection_repository = ROMCollectionRepository(uow)        
        romcollection = romcollection_repository.find_romcollection(romcollection_id)
    
        launchers = romcollection.get_launchers()
        if len(launchers) == 0:
            kodi.notify('No launchers configured for this romcollection!')
            AppMediator.sync_cmd('EDIT_ROMCOLLECTION_LAUNCHERS', args)
            return
        
        options = collections.OrderedDict()
        for launcher in launchers:
            options[launcher.get_id()] = launcher.get_name()
        
        s = 'Choose launcher to set as default'
        selected_option = kodi.OrdDictionaryDialog().select(s, options)
        
        if selected_option is None:
            # >> Exits context menu
            logger.debug('SET_DEFAULT_LAUNCHER: cmd_set_default_romcollection_launchers() Selected None. Closing context menu')
            AppMediator.sync_cmd('EDIT_ROMCOLLECTION_LAUNCHERS', args)
            return
        
        # >> Execute subcommand. May be atomic, maybe a submenu.
        logger.debug('SET_DEFAULT_LAUNCHER: cmd_set_default_romcollection_launchers() Selected {}'.format(selected_option))
        #@romcollection.set_launcher_as_default(launc)
        romcollection_repository.update_romcollection(romcollection)
        uow.commit()
    
    AppMediator.sync_cmd('EDIT_ROMCOLLECTION_LAUNCHERS', args)
       
# -------------------------------------------------------------------------------------------------
# ROMCollection launcher specific configuration.
# -------------------------------------------------------------------------------------------------      
@AppMediator.register('SET_LAUNCHER_SETTINGS')
def cmd_set_launcher_args(args):
    romcollection_id:str       = args['romcollection_id'] if 'romcollection_id' in args else None
    launcher_id:str     = args['launcher_id'] if 'launcher_id' in args else None
    addon_id:str        = args['addon_id'] if 'addon_id' in args else None
    launcher_settings   = args['settings'] if 'settings' in args else None
    
    #launcher_settings = json.loads(launcher_settings)
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        addon_repository = AelAddonRepository(uow)
        romcollection_repository = ROMCollectionRepository(uow)
        
        addon = addon_repository.find_by_addon_id(addon_id)
        romcollection = romcollection_repository.find_romcollection(romcollection_id)
        
        if launcher_id is None:
            romcollection.add_launcher(addon, launcher_settings, True)
        else: 
            launcher = romcollection.get_launcher(launcher_id)
            launcher.set_settings(launcher_settings)
            
        romcollection_repository.update_romcollection(romcollection)
        uow.commit()
    
    kodi.notify('Configured launcher {}'.format(addon.get_name()))
    AppMediator.async_cmd('EDIT_ROMCOLLECTION', {'romcollection_id': romcollection_id})
 
# -------------------------------------------------------------------------------------------------
# ROMCollection Launcher executing
# -------------------------------------------------------------------------------------------------
@AppMediator.register('EXECUTE_ROM')
def cmd_execute_rom_with_launcher(args):
    rom_id:str      = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        rom_repository = ROMsRepository(uow)
        romcollection_repository = ROMCollectionRepository(uow)

        rom = rom_repository.find_rom(rom_id)
        logger.info('Executing ROM {}'.format(rom.get_name()))
        
        romcollections = romcollection_repository.find_romcollections_by_rom(rom.get_id())
        launchers = rom.get_launchers()
        for romcollection in romcollections: 
            launchers.extend(romcollection.get_launchers())
    
    if launchers is None or len(launchers) == 0:
        logger.warn('No launcher configured for ROM {}'.format(rom.get_name()))
        kodi.notify_warn('No launcher configured.')
        return

    selected_launcher = launchers[0]
    if len(launchers) > 1:
        launcher_options = collections.OrderedDict()
        preselected = None
        for launcher in launchers:
            launcher_options[launcher] = launcher.get_name()
            if launcher.is_default():
                preselected = launcher
        dialog = kodi.OrdDictionaryDialog()
        selected_launcher = dialog.select('Choose launcher', launcher_options,preselect=preselected)

    kodi.run_script(selected_launcher.addon.get_addon_id(), {
        '--cmd': 'execute',
        '--type': constants.AddonType.LAUNCHER.name,
        '--launcher_id': selected_launcher.get_id(),
        '--rom_id': rom.get_id(),
        '--rom_args': '"{}"'.format(json.dumps(rom.get_launcher_args())),
        '--is_non_blocking': str(selected_launcher.is_non_blocking()),
        '--settings': '"{}"'.format(selected_launcher.get_settings_str())
    })
    AppMediator.async_cmd('ROM_WAS_LAUNCHED', args)