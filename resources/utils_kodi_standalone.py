# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher miscellaneous functions
#

# Copyright (c) 2016-2017 Wintermute0110 <wintermute0110@gmail.com>
# Portions (c) 2010-2015 Angelscry
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

#
# Replace functionality that depends on Kodi modules, so we can execute code
# outside Kodi in standard Python.
#

# --- Python standard library ---
from __future__ import unicode_literals

# --- Make fake Kodi functions ---
class xbmc_wrapper:
    LOGINFO  = 3
    LOGERROR = 5

    def log(self, log_text, level):
        print(log_text)

# --- Fake xbmc class ---
xbmc = xbmc_wrapper()
