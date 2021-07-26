# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (ROM scraper management)
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

from ael.utils import kodi

from resources.app.commands.mediator import AppMediator
from resources.app import globals
from resources.app.repositories import UnitOfWork, ROMCollectionRepository, ROMsRepository, AelAddonRepository
from resources.app.domain import ROM, ROMCollectionScanner, AelAddon
