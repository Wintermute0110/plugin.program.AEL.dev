# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher main script file
#

# Copyright (c) 2016-2018 Wintermute0110 <wintermute0110@gmail.com>
# Portions (c) 2018 Chrisism
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

# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import sys
import logging

# --- Modules/packages in this plugin ---
from ael.utils import kodilogging, kodi
from resources.app import views

kodilogging.config()
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# Hacks and tests
# -------------------------------------------------------------------------------------------------
# --- Test SHOW_ALL_CATEGORIES / SHOW_ALL_LAUNCHERS / SHOW_ALL_ROMS command ---
# sys.argv[2] = '?com=SHOW_ALL_ROMS'
# resources.main.run_plugin(sys.argv)

# -------------------------------------------------------------------------------------------------
# main()
# -------------------------------------------------------------------------------------------------
# Put the main bulk of the code in files inside /resources/, which is a package directory. 
# This way, the Python interpreter will precompile them into bytecode (files PYC/PYO) so
# loading time is faster compared to loading PY files.
# See http://www.network-theory.co.uk/docs/pytut/CompiledPythonfiles.html
#

try:
    views.run_plugin(sys.argv)
except Exception as ex:
    logger.fatal('Exception in plugin', exc_info=ex)
    kodi.notify_error("General failure")