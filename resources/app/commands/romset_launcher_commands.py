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

from resources.app.commands.mediator import AppMediator
from resources.lib import constants, globals
from resources.lib import repositories
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
    default_launcher = next((l for l in launchers if l.is_default), launchers[0]) if len(launchers) > 0 else None
    default_launcher_name = default_launcher.name if default_launcher is not None else 'None'
    
    def_launcher_name = ''
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
        kodi.event(method='EDIT_ROMSET', data=args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('EDIT_ROMSET_LAUNCHERS: cmd_manage_romset_launchers() Selected {}'.format(selected_option))
    kodi.event(method=selected_option, data=args)

# --- Sub commands ---
@AppMediator.register('ADD_LAUNCHER')
def cmd_add_romset_launchers(args):
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = AelAddonRepository(uow)
        addons = repository.find_all_launchers()
    
    options = collections.OrderedDict()
    for addon in addons:
        options[addon.get_id()] = addon.get_name()
    
    s = 'Choose launcher to associate'
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    
    if selected_option is None:
        # >> Exits context menu
        logger.debug('ADD_LAUNCHER: cmd_add_romset_launchers() Selected None. Closing context menu')
        kodi.event(method='EDIT_ROMSET_LAUNCHERS', data=args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('ADD_LAUNCHER: cmd_add_romset_launchers() Selected {}'.format(selected_option))
    kodi.event(method='CONFIGURE_LAUNCHER', data={'romset_id': romset_id, 'ael_addon_id': selected_option})
        
@AppMediator.register('CONFIGURE_LAUNCHER')
def cmd_configure_romset_launchers(args):
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    ael_addon_id:str = args['ael_addon_id'] if 'ael_addon_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        addon_repository = AelAddonRepository(uow)
        romset_repository = ROMSetRepository(uow)
        
        addon = addon_repository.find(ael_addon_id)
        romset = romset_repository.find_romset(romset_id)
    
    kodi.execute_uri(addon.get_configure_uri(), {'romset_id': romset_id, 'platform': romset.get_platform()})        
      
@AppMediator.register('SET_LAUNCHER_ARGS')
def cmd_set_launcher_args(args):
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    addon_id:str = args['addon_id'] if 'addon_id' in args else None
    launcher_args = args['args'] if 'args' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        addon_repository = AelAddonRepository(uow)
        romset_repository = ROMSetRepository(uow)
        
        addon = addon_repository.find_by_addon_id(addon_id)
        romset = romset_repository.find_romset(romset_id)
        
        romset.add_launcher(addon, launcher_args)
        romset_repository.update_romset(romset)
        uow.commit()
    
    kodi.notify('Configured launcher {}'.format(addon.get_name()))
    kodi.event(method='EDIT_ROMSET', data={'romset_id': romset_id})
    
    
    EXECUTE_ROM