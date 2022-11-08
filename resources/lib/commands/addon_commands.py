# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Commands (import & export of configurations)
#
# Copyright (c) Wintermute0110 <wintermute0110@gmail.com> / Chrisism <crizizz@gmail.com>
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
import collections

# -- Kodi libs -- 
import xbmc
import xbmcaddon

# -- AKL libs -- 
from akl import constants
from akl.utils import kodi

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import UnitOfWork, AelAddonRepository
from resources.lib.domain import AelAddon

logger = logging.getLogger(__name__)

@AppMediator.register('SCAN_FOR_ADDONS')
def cmd_scan_addons(args):
    kodi.notify('Scanning for AKL supported addons')
    addon_count = _check_installed_addons()
    
    msg = 'No AKL addons found. Search and install default plugin addons for AKL?'
    if addon_count == 0 and kodi.dialog_yesno(msg):
        xbmc.executebuiltin('InstallAddon(script.akl.defaults)', True)
        addon_count = _check_installed_addons()
        
    logger.info('cmd_scan_addons(): Processed {} addons'.format(addon_count))
    kodi.notify('Scan completed. Found {} addons'.format(addon_count))

@AppMediator.register('SHOW_ADDONS')
def cmd_show_addons(args):    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = AelAddonRepository(uow)
        addons = repository.find_all()

        options = collections.OrderedDict()
        for addon in addons:
            logger.info(f"Installed Addon {addon.get_addon_id()} v{addon.get_version()} {addon.get_addon_type()}")
            if addon.get_addon_id() in options:
                continue
            name = f"{addon.get_name()} v{addon.get_version()}"
            options[addon.get_addon_id()] = name

        s = 'Addons'
        selected_option = kodi.OrdDictionaryDialog().select(s, options)
        if selected_option is None:
            return
  

def _check_installed_addons() -> int:
    addon_count = 0
    json_response = kodi.jsonrpc_query("Addons.GetAddons", params={
        'installed': True, 'enabled': True, 
        'type': 'xbmc.python.script'})
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        addon_repository    = AelAddonRepository(uow)
        existing_addons     = [*addon_repository.find_all()]
        
        existing_launcher_ids  = { a.get_addon_id(): a for a in existing_addons if a.get_addon_type() == constants.AddonType.LAUNCHER }
        existing_scanner_ids   = { a.get_addon_id(): a for a in existing_addons if a.get_addon_type() == constants.AddonType.SCANNER }
        existing_scraper_ids   = { a.get_addon_id(): a for a in existing_addons if a.get_addon_type() == constants.AddonType.SCRAPER }
                
        for row in json_response['result'].get('addons', []):
            addon_id = row['addonid']
            addon = xbmcaddon.Addon(addon_id)           
            # Check if add-on is a AKL support plugin
            if addon.getSetting('akl.enabled').lower() != 'true':
                continue
            
            logger.debug('cmd_scan_addons(): Found addon {}'.format(addon_id))
            addon_types = addon.getSettingString('akl.plugin_types').split('|')
            addon_count = addon_count + 1  
            
            if constants.AddonType.LAUNCHER.name in addon_types:
                _process_launcher_addon(addon_id, addon, existing_launcher_ids, addon_repository)
                
            if constants.AddonType.SCANNER.name in addon_types:
                _process_scanner_addon(addon_id, addon, existing_scanner_ids, addon_repository)
                
            if constants.AddonType.SCRAPER.name in addon_types:
                _process_scraper_addon(addon_id, addon, existing_scraper_ids, addon_repository)
                
        uow.commit()
    return addon_count

def _process_launcher_addon(
    addon_id:str, 
    addon:xbmcaddon.Addon, 
    existing_addon_ids:typing.Dict[str,AelAddon],
    addon_repository:AelAddonRepository):
    
    addon_name = addon.getSetting('akl.launcher.friendlyname')
    addon_name = addon.getAddonInfo('name') if addon_name is None or addon_name == '' else addon_name
    
    addon_obj = AelAddon({
        'addon_id': addon_id,
        'version': addon.getAddonInfo('version'),
        'name': addon_name,
        'addon_type': constants.AddonType.LAUNCHER.name
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
    
    addon_name = addon.getSetting('akl.scanner.friendlyname')
    addon_name = addon.getAddonInfo('name') if addon_name is None or addon_name == '' else addon_name
    
    addon_obj = AelAddon({
        'addon_id': addon_id,
        'version': addon.getAddonInfo('version'),
        'name': addon_name,
        'addon_type': constants.AddonType.SCANNER.name
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
        
def _process_scraper_addon(
    addon_id:str, 
    addon:xbmcaddon.Addon, 
    existing_addon_ids:typing.Dict[str,AelAddon],
    addon_repository:AelAddonRepository):
        
    addon_name = addon.getSetting('akl.scraper.friendlyname')
    addon_name = addon.getAddonInfo('name') if addon_name is None or addon_name == '' else addon_name
    
    addon_obj = AelAddon({
        'addon_id': addon_id,
        'version': addon.getAddonInfo('version'),
        'name': addon_name,
        'addon_type': constants.AddonType.SCRAPER.name,
    })
    
    addon_obj.set_extra_settings({
        'supported_metadata':  addon.getSetting('akl.scraper.supported_metadata'),
        'supported_assets': addon.getSetting('akl.scraper.supported_assets')
    })

    if addon_id in existing_addon_ids:                
        if existing_addon_ids[addon_id].get_version() == addon_obj.get_version():
            return
        addon_obj.set_id(existing_addon_ids[addon_id].get_id())
        addon_repository.update_addon(addon_obj)
        logger.debug('cmd_scan_addons(): Updated scraper addon {}'.format(addon_id))
    else:
        addon_repository.insert_addon(addon_obj)
        logger.debug('cmd_scan_addons(): Added scraper addon {}'.format(addon_id))        