# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher main script file.
#

# Copyright (c) 2016-2018 Wintermute0110 <wintermute0110@gmail.com>
# Portions (c) 2010-2015 Angelscry
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
#
# Globals to be used by the addon

import routing
# --- Kodi stuff ---
import xbmcaddon
# --- AEL stuff ---
from resources.lib import settings

# --- Addon object (used to access settings) ---
addon           = xbmcaddon.Addon()
addon_id        = addon.getAddonInfo('id')
addon_name      = addon.getAddonInfo('name')
addon_version   = addon.getAddonInfo('version')
addon_author    = addon.getAddonInfo('author')
addon_profile   = addon.getAddonInfo('profile')
addon_type      = addon.getAddonInfo('type')

router: routing.Plugin = routing.Plugin()
g_PATHS: settings.AEL_Paths

#
# Bootstrap factory object instances.
#
def g_bootstrap_instances():
    global g_PATHS
    g_PATHS = settings.AEL_Paths(addon_id).build()