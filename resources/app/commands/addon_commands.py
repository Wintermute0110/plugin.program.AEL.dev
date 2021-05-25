# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (import & export of configurations)
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

import xbmcaddon

from resources.app.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import *
from resources.lib.utils import kodi

logger = logging.getLogger(__name__)

@AppMediator.register('SCAN_FOR_ADDONS')
def cmd_scan_addons(args):
    kodi.notify('Scanning for AEL supported addons')
    json_response = kodi.jsonrpc_query("Addons.GetAddons", params={
        'installed': True, 'enabled': True, 
        'type': 'xbmc.python.pluginsource'})
    
    addon_count = 0
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        addon_repository    = AelAddonRepository(uow)
        existing_addons     = [*addon_repository.find_all()]
        existing_addon_ids  = { a.get_addon_id(): a for a in existing_addons }
                
        for row in json_response['result'].get('addons', []):
            addon_id = row['addonid']
            addon = xbmcaddon.Addon(addon_id)           
            # Check if add-on is a AEL support plugin
            if addon.getSetting('ael.enabled').lower() != 'true':
                continue
            
            logger.debug('cmd_scan_addons(): Found addon {}'.format(addon_id))
            addon_count = addon_count + 1                        
            addon_obj = AelAddon({
                'addon_id': addon_id,
                'version': addon.getAddonInfo('version'),
                'name': addon.getAddonInfo('name'),
                'is_launcher': addon.getSetting('ael.launcher_uri') != '',
                'launcher_uri': addon.getSetting('ael.launcher_uri')
            })
            
            if addon_id in existing_addon_ids:
                if existing_addon_ids[addon_id].get_version() == addon_obj.get_version():
                    continue
                addon_obj.set_id(existing_addon_ids[addon_id].get_id())
                addon_repository.update_addon(addon_obj)
                logger.debug('cmd_scan_addons(): Updated addon {}'.format(addon_id))
            else:
                addon_repository.save_addon(addon_obj)
                logger.debug('cmd_scan_addons(): Added addon {}'.format(addon_id))
            
        uow.commit()
        
    logger.info('cmd_scan_addons(): Processed {} addons'.format(addon_count))
    kodi.notify('Scan completed. Found {} addons'.format(addon_count))

