# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (romset scanner management)
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
# ROM Scanners management.
# -------------------------------------------------------------------------------------------------

# --- Submenu menu command ---
@AppMediator.register('EDIT_ROMSET_SCANNERS')
def cmd_manage_romset_scanners(args):
    logger.debug('EDIT_ROMSET_SCANNERS: cmd_manage_romset_scanners() SHOW MENU')
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMSetRepository(uow)
        romset = repository.find_romset(romset_id)
        
    options = collections.OrderedDict()
    options['ADD_SCANNER']      = 'Add new scanner'
    options['EDIT_SCANNER']     = 'Edit scanner'
    options['REMOVE_SCANNER']   = 'Remove scanner'
        
    s = 'Manage ROM scanners for "{}"'.format(romset.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_ROMSET_SCANNERS: cmd_manage_romset_scanners() Selected None. Closing context menu')
        kodi.event(command='EDIT_ROMSET', data=args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('EDIT_ROMSET_SCANNERS: cmd_manage_romset_scanners() Selected {}'.format(selected_option))
    kodi.event(command=selected_option, data=args)

# --- Sub commands ---
@AppMediator.register('ADD_SCANNER')
def cmd_add_romset_scanner(args):
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    
    options = collections.OrderedDict()
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository        = AelAddonRepository(uow)
        romset_repository = ROMSetRepository(uow)
        
        addons = repository.find_all_scanners()
        romset = romset_repository.find_romset(romset_id)

        for addon in addons:
            options[addon] = addon.get_name()
    
    s = 'Choose scanner to associate'
    selected_option:AelAddon = kodi.OrdDictionaryDialog().select(s, options)
    
    if selected_option is None:
        # >> Exits context menu
        logger.debug('ADD_SCANNER: cmd_add_romset_scanner() Selected None. Closing context menu')
        kodi.event(command='EDIT_ROMSET_SCANNERS', data=args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('ADD_SCANNER: cmd_add_romset_scanner() Selected {}'.format(selected_option.get_id()))
    
    kodi.execute_uri(selected_option.get_configure_uri(), {
        'romset_id': romset_id
    })