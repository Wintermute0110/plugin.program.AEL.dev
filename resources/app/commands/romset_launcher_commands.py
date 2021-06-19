# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (romset launcher management)
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

from resources.app.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import *
from resources.lib.utils import kodi

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# ROMSet launcher management.
# -------------------------------------------------------------------------------------------------

# --- Submenu menu command ---
@AppMediator.register('EDIT_ROMSET_LAUNCHERS')
def cmd_manage_romset_launchers(args):
    logger.debug('EDIT_ROMSET_LAUNCHERS: cmd_manage_romset_launchers() SHOW MENU')
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)
        
    launchers = romset.get_launchers()
    default_launcher = next((l for l in launchers if l.is_default()), launchers[0]) if len(launchers) > 0 else None
    default_launcher_name = default_launcher.get_name() if default_launcher is not None else 'None'
    
    options = collections.OrderedDict()
    options['ADD_LAUNCHER']         = 'Add new launcher'
    options['EDIT_LAUNCHER']        = 'Edit launcher'
    options['REMOVE_LAUNCHER']      = 'Remove launcher'
    options['SET_DEFAULT_LAUNCHER'] = 'Set default launcher: "{}"'.format(default_launcher_name)
        
    s = 'Manage Launchers for "{}"'.format(romset.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_ROMSET_LAUNCHERS: cmd_manage_romset_launchers() Selected None. Closing context menu')
        kodi.event(command='EDIT_ROMSET', data=args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('EDIT_ROMSET_LAUNCHERS: cmd_manage_romset_launchers() Selected {}'.format(selected_option))
    kodi.event(command=selected_option, data=args)

# --- Sub commands ---
@AppMediator.register('ADD_LAUNCHER')
def cmd_add_romset_launchers(args):
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    
    options = collections.OrderedDict()
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository        = AelAddonRepository(uow)
        romset_repository = ROMSetRepository(uow)
        
        addons = repository.find_all_launchers()
        romset = romset_repository.find_romset(romset_id)

        for addon in addons:
            options[addon] = addon.get_name()
    
    s = 'Choose launcher to associate'
    selected_option:AelAddon = kodi.OrdDictionaryDialog().select(s, options)
    
    if selected_option is None:
        # >> Exits context menu
        logger.debug('ADD_LAUNCHER: cmd_add_romset_launchers() Selected None. Closing context menu')
        kodi.event(command='EDIT_ROMSET_LAUNCHERS', data=args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('ADD_LAUNCHER: cmd_add_romset_launchers() Selected {}'.format(selected_option.get_id()))
    
    kodi.execute_uri(selected_option.get_configure_uri(), {
        'romset_id': romset_id, 
        'settings': json.dumps({'platform': romset.get_platform()})
    })

@AppMediator.register('EDIT_LAUNCHER')
def cmd_edit_romset_launchers(args):
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romset_repository = ROMSetRepository(uow)        
        romset = romset_repository.find_romset(romset_id)
    
    launchers = romset.get_launchers()
    if len(launchers) == 0:
        kodi.notify('No launchers configured for this romset!')
        kodi.event(command='EDIT_ROMSET_LAUNCHERS', data=args)
        return
    
    options = collections.OrderedDict()
    for launcher in launchers:
        options[launcher] = launcher.get_name()
    
    s = 'Choose launcher to edit'
    selected_option:ROMSetLauncher = kodi.OrdDictionaryDialog().select(s, options)
    
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_LAUNCHER: cmd_edit_romset_launchers() Selected None. Closing context menu')
        kodi.event(command='EDIT_ROMSET_LAUNCHERS', data=args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('EDIT_LAUNCHER: cmd_edit_romset_launchers() Selected {}'.format(selected_option.get_id()))
    kodi.execute_uri(selected_option.addon.get_configure_uri(), {
        'romset_id': romset_id, 
        'launcher_id': selected_option.get_id(),
        'settings': selected_option.get_settings_str()
    })
       
@AppMediator.register('REMOVE_LAUNCHER')
def cmd_remove_romset_launchers(args):
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romset_repository = ROMSetRepository(uow)        
        romset = romset_repository.find_romset(romset_id)
    
        launchers = romset.get_launchers()
        if len(launchers) == 0:
            kodi.notify('No launchers configured for this romset!')
            kodi.event(command='EDIT_ROMSET_LAUNCHERS', data=args)
            return
        
        options = collections.OrderedDict()
        for launcher in launchers:
            options[launcher] = launcher.get_name()
        
        s = 'Choose launcher to remove'
        selected_option:ROMSetLauncher = kodi.OrdDictionaryDialog().select(s, options)
        
        if selected_option is None:
            # >> Exits context menu
            logger.debug('REMOVE_LAUNCHER: cmd_remove_romset_launchers() Selected None. Closing context menu')
            kodi.event(command='EDIT_ROMSET_LAUNCHERS', data=args)
            return
        
        # >> Execute subcommand. May be atomic, maybe a submenu.
        logger.debug('REMOVE_LAUNCHER: cmd_remove_romset_launchers() Selected {}'.format(selected_option.get_id()))
        if not kodi.dialog_yesno('Are you sure to delete launcher "{}"'.format(selected_option.get_name())):
            logger.debug('REMOVE_LAUNCHER: cmd_remove_romset_launchers() Cancelled operation.')
            kodi.event(command='EDIT_ROMSET_LAUNCHERS', data=args)
            return
        
        romset_repository.remove_launcher(romset.get_id(), selected_option.get_id())
        logger.info('REMOVE_LAUNCHER: cmd_remove_romset_launchers() Removed launcher#{}'.format(selected_option.get_id()))
        uow.commit()
    
    kodi.event(command='EDIT_ROMSET_LAUNCHERS', data=args)
    
@AppMediator.register('SET_DEFAULT_LAUNCHER')
def cmd_set_default_romset_launchers(args):
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romset_repository = ROMSetRepository(uow)        
        romset = romset_repository.find_romset(romset_id)
    
        launchers = romset.get_launchers()
        if len(launchers) == 0:
            kodi.notify('No launchers configured for this romset!')
            kodi.event(command='EDIT_ROMSET_LAUNCHERS', data=args)
            return
        
        options = collections.OrderedDict()
        for launcher in launchers:
            options[launcher.get_id()] = launcher.get_name()
        
        s = 'Choose launcher to set as default'
        selected_option = kodi.OrdDictionaryDialog().select(s, options)
        
        if selected_option is None:
            # >> Exits context menu
            logger.debug('SET_DEFAULT_LAUNCHER: cmd_set_default_romset_launchers() Selected None. Closing context menu')
            kodi.event(command='EDIT_ROMSET_LAUNCHERS', data=args)
            return
        
        # >> Execute subcommand. May be atomic, maybe a submenu.
        logger.debug('SET_DEFAULT_LAUNCHER: cmd_set_default_romset_launchers() Selected {}'.format(selected_option))
        #@romset.set_launcher_as_default(launc)
        romset_repository.update_romset(romset)
        uow.commit()
    
    kodi.event(command='EDIT_ROMSET_LAUNCHERS', data=args)
       
# -------------------------------------------------------------------------------------------------
# ROMSet launcher specific configuration.
# -------------------------------------------------------------------------------------------------      
@AppMediator.register('SET_LAUNCHER_SETTINGS')
def cmd_set_launcher_args(args):
    romset_id:str       = args['romset_id'] if 'romset_id' in args else None
    launcher_id:str     = args['launcher_id'] if 'launcher_id' in args else None
    addon_id:str        = args['addon_id'] if 'addon_id' in args else None
    launcher_settings   = args['settings'] if 'settings' in args else None
    is_non_blocking     = args['is_non_blocking'] if 'is_non_blocking' in args else False
    
    #launcher_settings = json.loads(launcher_settings)
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        addon_repository = AelAddonRepository(uow)
        romset_repository = ROMSetRepository(uow)
        
        addon = addon_repository.find_by_addon_id(addon_id)
        romset = romset_repository.find_romset(romset_id)
        
        if launcher_id is None:
            romset.add_launcher(addon, launcher_settings, is_non_blocking)
        else: 
            launcher = romset.get_launcher(launcher_id)
            launcher.set_settings(launcher_settings)
            launcher.change_is_blocking(is_non_blocking)
            
        romset_repository.update_romset(romset)
        uow.commit()
    
    kodi.notify('Configured launcher {}'.format(addon.get_name()))
    kodi.event(command='EDIT_ROMSET', data={'romset_id': romset_id})
 
# -------------------------------------------------------------------------------------------------
# ROMSet Launcher executing
# -------------------------------------------------------------------------------------------------
@AppMediator.register('EXECUTE_ROM')
def cmd_configure_romset_launchers(args):
    rom_id:str = args['rom_id'] if 'rom_id' in args else None

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        rom_repository = ROMsRepository(uow)
        romset_repository = ROMSetRepository(uow)

        rom = rom_repository.find_rom(rom_id)
        romset = romset_repository.find_romset(rom.get_romset_id())

    launchers = romset.get_launchers()
    if launchers is None or len(launchers) == 0:
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

    application = selected_launcher.get_application()
    settings = selected_launcher.get_settings()
    arguments = settings['args']
    
    logger.info('EXECUTE_ROM: selected launcher "{}"'.format(selected_launcher.get_name()))
    logger.info('EXECUTE_ROM: raw arguments     "{}"'.format(arguments))

    #Application based arguments replacements
    if application:
        app = io.FileName(application)
        apppath = app.getDir()

        logger.info('EXECUTE_ROM: application  "{0}"'.format(app.getPath()))
        logger.info('EXECUTE_ROM: appbase      "{0}"'.format(app.getBase()))
        logger.info('EXECUTE_ROM: apppath      "{0}"'.format(apppath))

        arguments = arguments.replace('$apppath$', apppath)
        arguments = arguments.replace('$appbase$', app.getBase())
        
    # ROM based arguments replacements
    if rom:
        rom_file = rom.get_file()
        # --- Escape quotes and double quotes in ROMFileName ---
        # >> This maybe useful to Android users with complex command line arguments
        if settings.getSettingAsBool('escape_romfile'):
            logger.info("EXECUTE_ROM: Escaping ROMFileName ' and \"")
            rom_file.escapeQuotes()

        rompath       = rom_file.getDir()
        rombase       = rom_file.getBase()
        rombase_noext = rom_file.getBaseNoExt()

        logger.info('EXECUTE_ROM: romfile      "{0}"'.format(rom_file.getPath()))
        logger.info('EXECUTE_ROM: rompath      "{0}"'.format(rompath))
        logger.info('EXECUTE_ROM: rombase      "{0}"'.format(rombase))
        logger.info('EXECUTE_ROM: rombasenoext "{0}"'.format(rombase_noext))

        arguments = arguments.replace('$rom$',          rom_file.getPath())
        arguments = arguments.replace('$romfile$',      rom_file.getPath())
        arguments = arguments.replace('$rompath$',      rompath)
        arguments = arguments.replace('$rombase$',      rombase)
        arguments = arguments.replace('$rombasenoext$', rombase_noext)

        # >> Legacy names for argument substitution
        arguments = arguments.replace('%rom%', rom_file.getPath())
        arguments = arguments.replace('%ROM%', rom_file.getPath())

        # Default arguments replacements
        arguments = arguments.replace('$romsetID$', romset.get_id())
        arguments = arguments.replace('$romsetName$', romset.get_name())
        arguments = arguments.replace('$launcherID$', launcher.addon.get_addon_id())
        arguments = arguments.replace('$addonID$', launcher.addon.get_addon_id())
        arguments = arguments.replace('$romID$', rom.get_id())
        arguments = arguments.replace('$romtitle$', rom.get_name())

        # automatic substitution of rom values
        for rom_key, rom_value in rom.get_data_dic().items():
            if isinstance(rom_value, str):
                arguments = arguments.replace('${}$'.format(rom_key), rom_value)        

        logger.info('EXECUTE_ROM: final arguments "{0}"'.format(arguments))

    kodi.execute_uri(selected_launcher.addon.get_execute_uri(), {
        'application': application,
        'settings': selected_launcher.get_settings_str(),
        'args': arguments,
        'is_non_blocking': str(selected_launcher.is_non_blocking())
    })