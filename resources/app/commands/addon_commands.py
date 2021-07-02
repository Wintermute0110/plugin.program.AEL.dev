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
import typing
from ael import constants

import xbmcaddon

from ael.utils import kodi

from resources.app.commands.mediator import AppMediator
from resources.app import globals
from resources.app.repositories import UnitOfWork, AelAddonRepository
from resources.app.domain import AelAddon

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
            
            if addon.getSetting('ael.launcher.execute_uri') != '':
                _process_launcher_addon(addon_id, addon, existing_addon_ids, addon_repository)
                
            if addon.getSetting('ael.scanner.execute_uri') != '':
                _process_scanner_addon(addon_id, addon, existing_addon_ids, addon_repository)
                
        uow.commit()
        
    logger.info('cmd_scan_addons(): Processed {} addons'.format(addon_count))
    kodi.notify('Scan completed. Found {} addons'.format(addon_count))

def _process_launcher_addon(
    addon_id:str, 
    addon:xbmcaddon.Addon, 
    existing_addon_ids:typing.Dict[str,AelAddon],
    addon_repository:AelAddonRepository):
    
    addon_obj = AelAddon({
        'addon_id': addon_id,
        'version': addon.getAddonInfo('version'),
        'name': addon.getAddonInfo('name'),
        'addon_type': constants.AddonType.LAUNCHER.name,
        'execute_uri': addon.getSetting('ael.launcher.execute_uri') != '',
        'configure_uri': addon.getSetting('ael.launcher.configure_uri')
    })

    if addon_id in existing_addon_ids:
        if existing_addon_ids[addon_id].get_version() == addon_obj.get_version():
            return
        addon_obj.set_id(existing_addon_ids[addon_id].get_id())
        addon_repository.update_addon(addon_obj)
        logger.debug('cmd_scan_addons(): Updated launcher addon {}'.format(addon_id))
    else:
        addon_repository.insert_addon(addon_obj)
        logger.debug('cmd_scan_addons(): Added launcher addon {}'.format(addon_id))
        
def _process_scanner_addon(
    addon_id:str, 
    addon:xbmcaddon.Addon, 
    existing_addon_ids:typing.Dict[str,AelAddon],
    addon_repository:AelAddonRepository):
    
    addon_obj = AelAddon({
        'addon_id': addon_id,
        'version': addon.getAddonInfo('version'),
        'name': addon.getAddonInfo('name'),
        'addon_type': constants.AddonType.SCANNER.name,
        'execute_uri': addon.getSetting('ael.scanner.execute_uri') != '',
        'configure_uri': addon.getSetting('ael.scanner.configure_uri')
    })

    if addon_id in existing_addon_ids:                
        if existing_addon_ids[addon_id].get_version() == addon_obj.get_version():
            return
        addon_obj.set_id(existing_addon_ids[addon_id].get_id())
        addon_repository.update_addon(addon_obj)
        logger.debug('cmd_scan_addons(): Updated scanner addon {}'.format(addon_id))
    else:
        addon_repository.insert_addon(addon_obj)
        logger.debug('cmd_scan_addons(): Added scanner addon {}'.format(addon_id))