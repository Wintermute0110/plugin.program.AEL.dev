# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher main script file
#

# Copyright (c) Chrisism <crizizz@gmail.com>
# Big Portions (c) Wintermute0110 <wintermute0110@gmail.com> 
# Portions (c) 2010-2015 Angelscry and others
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# Advanced Emulator Launcher main script file.

import sys
import logging

# --- Modules/packages in this plugin ---
from akl.utils import kodilogging, kodi
from resources.lib import views

kodilogging.config()
logger = logging.getLogger(__name__)

# --- Python standard library ---
import sys

# -------------------------------------------------------------------------------------------------
# Entrypoint of the Frontend/UI application
# -------------------------------------------------------------------------------------------------

try:
    views.run_plugin(sys.argv)
except Exception as ex:
    logger.fatal('Exception in plugin', exc_info=ex)
    kodi.notify_error("General failure")
