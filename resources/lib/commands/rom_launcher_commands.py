# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Commands (romcollection launcher management)
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

from akl.utils import kodi
from akl import settings, constants

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import UnitOfWork, ROMCollectionRepository, ROMsRepository, AelAddonRepository
from resources.lib.domain import AelAddon, ROMLauncherAddon, ROMLauncherAddonFactory

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# ROMCollection launcher management.
# -------------------------------------------------------------------------------------------------

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

@AppMediator.register('EDIT_ROM_LAUNCHERS')
def cmd_manage_rom_launchers(args):
    logger.debug('EDIT_ROM_LAUNCHERS: cmd_manage_rom_launchers() SHOW MENU')
    rom_id:str = args['rom_id'] if 'rom_id' in args else None
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)        
        rom = repository.find_rom(rom_id)
        
    launchers = rom.get_launchers()
    default_launcher = next((l for l in launchers if l.is_default()), launchers[0]) if len(launchers) > 0 else None
    default_launcher_name = default_launcher.get_name() if default_launcher is not None else 'None'
    
    options = collections.OrderedDict()
    options['ADD_ROM_LAUNCHER']         = 'Add new launcher'
    options['EDIT_ROM_LAUNCHER']        = 'Edit launcher'
    options['REMOVE_ROM_LAUNCHER']      = 'Remove launcher'
    options['SET_DEFAULT_ROM_LAUNCHER'] = f'Set default launcher: "{default_launcher_name}"'
        
    s = f'Manage Launchers for "{rom.get_name()}"'
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('Selected None. Closing context menu')
        AppMediator.sync_cmd('EDIT_ROM', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug(f'Selected {selected_option}')
    AppMediator.sync_cmd(selected_option, args)
    
# --- Sub commands ---
@AppMediator.register('ADD_ROM_LAUNCHER')
def cmd_add_rom_launchers(args):
    rom_id:str = args['rom_id'] if 'rom_id' in args else None
    
    options = collections.OrderedDict()
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository      = AelAddonRepository(uow)
        rom_repository  = ROMsRepository(uow)
        
        addons = repository.find_all_launchers()
        rom = rom_repository.find_rom(rom_id)

        for addon in addons:
            options[addon] = addon.get_name()
    
    s = 'Choose launcher to associate'
    selected_option:AelAddon = kodi.OrdDictionaryDialog().select(s, options)
    
    if selected_option is None:
        # >> Exits context menu
        logger.debug('Selected None. Closing context menu')
        AppMediator.sync_cmd('EDIT_ROM_LAUNCHERS', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug(f'Selected {selected_option.get_id()}')
    
    selected_launcher = ROMLauncherAddonFactory.create(selected_option, {})
    selected_launcher.configure_for_rom(rom)

@AppMediator.register('ADD_LAUNCHER')
def cmd_add_romcollection_launchers(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    options = collections.OrderedDict()
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository               = AelAddonRepository(uow)
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
    
    selected_launcher = ROMLauncherAddonFactory.create(selected_option, {})
    selected_launcher.configure(romcollection)

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
    selected_option.configure(romcollection)
      
@AppMediator.register('EDIT_ROM_LAUNCHER')
def cmd_edit_rom_launcher(args):
    rom_id:str = args['rom_id'] if 'rom_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)        
        rom = repository.find_rom(rom_id)
        
    launchers = rom.get_launchers()
    if len(launchers) == 0:
        kodi.notify('No launchers configured for this ROM!')
        AppMediator.async_cmd('EDIT_ROM_LAUNCHERS', args)
        return
    
    options = collections.OrderedDict()
    for launcher in launchers:
        options[launcher] = launcher.get_name()
    
    s = 'Choose launcher to edit'
    selected_option:ROMLauncherAddon = kodi.OrdDictionaryDialog().select(s, options)
    
    if selected_option is None:
        # >> Exits context menu
        logger.debug('Selected None. Closing context menu')
        AppMediator.async_cmd('EDIT_ROM_LAUNCHERS', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug(f'Selected {selected_option.get_id()}')
    selected_option.configure_for_rom(rom) 
    
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
        logger.info(f'Removed launcher#{selected_option.get_id()}')
        uow.commit()
    
    kodi.notify(f'Removed launcher "{selected_option.get_name()}"')
    AppMediator.sync_cmd('EDIT_ROMCOLLECTION_LAUNCHERS', args)
  
@AppMediator.register('REMOVE_ROM_LAUNCHER')
def cmd_remove_rom_launchers(args):
    rom_id:str = args['rom_id'] if 'rom_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)        
        rom = repository.find_rom(rom_id)
    
        launchers = rom.get_launchers()
        if len(launchers) == 0:
            kodi.notify('No launchers configured for this ROM!')
            AppMediator.sync_cmd('EDIT_ROM_LAUNCHERS', args)
            return
        
        options = collections.OrderedDict()
        for launcher in launchers:
            options[launcher] = launcher.get_name()
        
        s = 'Choose launcher to remove'
        selected_option:ROMLauncherAddon = kodi.OrdDictionaryDialog().select(s, options)
        
        if selected_option is None:
            # >> Exits context menu
            logger.debug('Selected None. Closing context menu')
            AppMediator.sync_cmd('EDIT_ROM_LAUNCHERS', args)
            return
        
        # >> Execute subcommand. May be atomic, maybe a submenu.
        logger.debug(f'Selected {selected_option.get_id()}')
        if not kodi.dialog_yesno(f'Are you sure to delete launcher "{selected_option.get_name()}"'):
            logger.debug('Cancelled operation.')
            AppMediator.async_cmd('EDIT_ROM_LAUNCHERS', args)
            return
        
        repository.remove_launcher(rom.get_id(), selected_option.get_id())
        logger.info(f'Removed launcher#{selected_option.get_id()}')
        uow.commit()
    
    kodi.notify(f'Removed launcher "{selected_option.get_name()}"')
    AppMediator.sync_cmd('EDIT_ROM_LAUNCHERS', args)
      
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
        romcollection.set_launcher_as_default(selected_option)
        romcollection_repository.update_romcollection(romcollection)
        uow.commit()
    
    AppMediator.sync_cmd('EDIT_ROMCOLLECTION_LAUNCHERS', args)
    
@AppMediator.register('SET_DEFAULT_ROM_LAUNCHER')
def cmd_set_default_rom_launchers(args):
    rom_id:str = args['rom_id'] if 'rom_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)        
        rom = repository.find_rom(rom_id)
    
        launchers = rom.get_launchers()
        if len(launchers) == 0:
            kodi.notify('No launchers configured for this ROM!')
            AppMediator.sync_cmd('EDIT_ROM_LAUNCHERS', args)
            return
        
        options = collections.OrderedDict()
        for launcher in launchers:
            options[launcher.get_id()] = launcher.get_name()
        
        s = 'Choose launcher to set as default'
        selected_option = kodi.OrdDictionaryDialog().select(s, options)
        
        if selected_option is None:
            # >> Exits context menu
            logger.debug('Selected None. Closing context menu')
            AppMediator.sync_cmd('EDIT_ROM_LAUNCHERS', args)
            return
        
        # >> Execute subcommand. May be atomic, maybe a submenu.
        logger.debug(f'Selected {selected_option}')
        rom.set_launcher_as_default(selected_option)
        repository.update_rom(rom)
        uow.commit()
    
    AppMediator.sync_cmd('EDIT_ROM_LAUNCHERS', args)
        
# -------------------------------------------------------------------------------------------------
# ROMCollection Launcher executing
# -------------------------------------------------------------------------------------------------
@AppMediator.register('EXECUTE_ROM')
def cmd_execute_rom_with_launcher(args):
    rom_id:str      = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        rom_repository           = ROMsRepository(uow)
        romcollection_repository = ROMCollectionRepository(uow)
        addon_repository         = AelAddonRepository(uow)

        rom = rom_repository.find_rom(rom_id)
        logger.info(f'Executing ROM {rom.get_name()}')
        
        romcollections = romcollection_repository.find_romcollections_by_rom(rom.get_id())
        launchers = rom.get_launchers()
        for romcollection in romcollections: 
            launchers.extend(romcollection.get_launchers())
    
        if launchers is None or len(launchers) == 0:
            logger.warning(f'No launcher configured for ROM {rom.get_name()}')
            if not settings.getSettingAsBool('fallback_to_retroplayer'):
                kodi.notify_warn('No launcher configured.')
                return
            
            logger.info('Automatic fallback to Retroplayer as launcher applied.')
            retroplayer_addon    = addon_repository.find_by_addon_id(constants.RETROPLAYER_LAUNCHER_APP_NAME, constants.AddonType.LAUNCHER)
            retroplayer_launcher = ROMLauncherAddonFactory.create(retroplayer_addon, {})
            launchers.append(retroplayer_launcher)
            
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

    if selected_launcher is None: return
    
    selected_launcher.launch(rom)
    AppMediator.async_cmd('ROM_WAS_LAUNCHED', args)