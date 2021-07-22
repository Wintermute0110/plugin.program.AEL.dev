# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (generating stats and counts)
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
import typing

from ael import constants
from ael.utils import kodi, io

from resources.app.commands.mediator import AppMediator
from resources.app import globals
from resources.app.repositories import UnitOfWork, ROMCollectionRepository, ROMsRepository, ROMsJsonFileRepository
from resources.app.domain import ROM, AssetInfo, g_assetFactory

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# ROM stats
# -------------------------------------------------------------------------------------------------

@AppMediator.register('ROM_WAS_LAUNCHED')
def cmd_process_launching_of_rom(args):
    logger.debug('ROM_WAS_LAUNCHED: cmd_process_launching_of_rom() Processing that a ROM was launched')
    rom_id:str = args['rom_id'] if 'rom_id' in args else None    
    if rom_id is None:
        logger.warn('cmd_process_launching_of_rom(): No rom id supplied.')
        return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        rom.increase_launch_count()
        repository.update_rom(rom)

        uow.commit()
        logger.debug('ROM_WAS_LAUNCHED: cmd_process_launching_of_rom() Processed stats for ROM {}'.format(rom.get_name()))
        AppMediator.async_cmd('RENDER_VCOLLECTION_VIEW', {'vcollection_id': constants.VCOLLECTION_RECENT_ID})
        AppMediator.async_cmd('RENDER_VCOLLECTION_VIEW', {'vcollection_id': constants.VCOLLECTION_MOST_PLAYED_ID})
    
@AppMediator.register('ADD_ROM_TO_FAVOURITES')
def cmd_add_rom_to_favourites(args):
    rom_id:str = args['rom_id'][0] if 'rom_id' in args else None    
    if rom_id is None:
        logger.warn('cmd_add_rom_to_favourites(): No rom id supplied.')
        kodi.notify_warn("Invalid parameters supplied.")
        return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        rom.add_to_favourites()
        repository.update_rom(rom)
        uow.commit()
        
    logger.debug('ADD_ROM_TO_FAVOURITES: cmd_add_rom_to_favourites() Added ROM {} to favourites'.format(rom.get_name()))
    AppMediator.async_cmd('RENDER_VCOLLECTION_VIEW', {'vcollection_id': constants.VCOLLECTION_FAVOURITES_ID})
    