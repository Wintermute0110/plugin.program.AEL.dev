# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (reporting)
#
# Copyright (c) Wintermute0110 <wintermute0110@gmail.com> / Chrisism <crizizz@gmail.com>
# 
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

from ael.utils import kodi, io
from ael import constants, platforms

from resources.lib.commands.mediator import AppMediator

from resources.lib.repositories import ROMsRepository, UnitOfWork, ROMCollectionRepository,
from resources.lib.domain import g_assetFactory
from resources.lib import globals

logger = logging.getLogger(__name__)

@AppMediator.register('CHECK_COLLECTIONS')
def cmd_check_collections(args):
    logger.debug('cmd_check_collections() Beginning...')
    
    main_slist = []
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romcollections_repository = ROMCollectionRepository(uow)
        romcollections = [*romcollections_repository.find_all_romcollections()]