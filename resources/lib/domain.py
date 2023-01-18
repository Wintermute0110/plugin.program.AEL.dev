# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher miscellaneous set of objects
#
# Copyright (c) Chrisism <crizizz@gmail.com>
# Portions (c) Wintermute0110 <wintermute0110@gmail.com> 
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
from __future__ import annotations

import abc
import typing
import logging
import re 
import time
import datetime
import json

# --- AKL packages ---
from resources.lib import globals

from akl import api
from akl.utils import io, kodi, text
from akl.scrapers import ScraperSettings
from akl import settings, constants

logger = logging.getLogger(__name__)


def _is_a_number(input: any):
    return isinstance(input, int) or isinstance(input, float)


def _is_empty(input: any) -> bool:
    return input is None or (not _is_a_number(input) and len(input) == 0)

def _is_empty_or_default(input: any, default: any):
    if _is_empty(input):
        return True
    return input == default

# -------------------------------------------------------------------------------------------------
# Gets all required information about an asset: path, name, etc.
# Returns an object with all the information
# -------------------------------------------------------------------------------------------------
class AssetInfo(object):
    id              = ''
    key             = ''
    default_key     = ''
    rom_default_key = ''
    name            = ''
    description     = name
    plural          = ''
    fname_infix     = '' # Used only when searching assets when importing XML
    kind_str        = ''
    exts            = []
    exts_dialog     = ''
    path_key        = ''

    def get_description(self):
        if self.description == '': return self.name

        return self.description

    def __eq__(self, other):
        return isinstance(other, AssetInfo) and self.id == other.id

    def __hash__(self):
        return self.id.__hash__()

    def __str__(self):
        return self.name


# Abstract base class for all DB entities
class EntityABC(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, entity_data: typing.Dict[str, typing.Any]):
        self.entity_data = entity_data

    # --- Database ID and utilities ---------------------------------------------------------------
    def set_id(self, id: str):
        self.entity_data['id'] = id

    def get_id(self) -> str:
        return self.entity_data['id'] if 'id' in self.entity_data else None

    def get_data_dic(self):
        return self.entity_data

    def copy_of_data_dic(self):
        return self.entity_data.copy()

    def set_custom_attribute(self, key, value):
        self.entity_data[key] = value

    def get_custom_attribute(self, key, default_value = None):
        return self.entity_data[key] if key in self.entity_data else default_value

    def import_data_dic(self, data):
        if data is None: return
        for key in data:
            self.entity_data[key] = data[key]

    def dump_data_dic_to_log(self):
        logger.debug('Dumping object {0}'.format(self.__class__))
        for key in self.entity_data:
            logger.debug('[{0}] = {1}'.format(key, str(self.entity_data[key])))

    # helper method to convert a dictionary value to a FileName object
    def _get_filename_from_field(self, field) -> io.FileName:
        if not field in self.entity_data: return None
        return self._to_filename(self.entity_data[field])

    def _get_directory_filename_from_field(self, field) -> io.FileName:
        if not field in self.entity_data: return None
        return self._to_filename(self.entity_data[field], isdir=True)
    
    #  helper method to convert a value to filename
    def _to_filename(self, value, isdir = False) -> io.FileName:
        if not value or value == '': return None
        return io.FileName(value, isdir)

# Addons that can be used as AKL plugin (launchers, scrapers)
class AelAddon(EntityABC):
    
    def __init__(self, addon_dic=None):        
        if addon_dic is None:
            addon_dic = {}
            
        if 'associated_addon_id' in addon_dic: 
            addon_dic['id'] = addon_dic['associated_addon_id']
            
        if 'id' not in addon_dic:
            addon_dic['id'] = text.misc_generate_random_SID()
            
        super(AelAddon, self).__init__(addon_dic)
    
    def get_id(self) -> str:
        return self.entity_data['id'] 
    
    def get_name(self) -> str:
        return self.entity_data['name']

    def set_name(self, name: str):
        self.entity_data['name'] = name

    def get_addon_id(self) -> str:
        return self.entity_data['addon_id']
    
    def get_version(self) -> str:
        return self.entity_data['version']
    
    def set_version(self, version: str):
        self.entity_data['version'] = version
    
    def get_addon_type(self) -> constants.AddonType:
        return constants.AddonType[self.entity_data['addon_type']] if 'addon_type' in self.entity_data else constants.AddonType.UNKNOWN
 
    def get_extra_settings_str(self) -> str:
        return self.entity_data['extra_settings'] if 'extra_settings' in self.entity_data else ''
    
    def get_extra_settings(self) -> dict:
        return json.loads(self.get_extra_settings_str())
    
    def set_extra_settings(self, settings: dict):
        self.entity_data['extra_settings'] = json.dumps(settings)
        
class Asset(EntityABC):

    def __init__(self, entity_data: typing.Dict[str, typing.Any] = None):
        self.asset_info:AssetInfo = None
        if entity_data is None:
            entity_data = _get_default_asset_data_model()
        
        if 'asset_type' in entity_data and entity_data['asset_type']:
            self.asset_info = g_assetFactory.get_asset_info(entity_data['asset_type'])
        
        super(Asset, self).__init__(entity_data)
    
    def get_asset_info_id(self) -> str:
        return self.asset_info.id 
    
    def get_asset_info(self) -> AssetInfo:
        return self.asset_info
    
    def get_path(self) -> str:
        return self.entity_data['filepath']
    
    def get_path_FN(self) -> io.FileName:
        return self._get_filename_from_field('filepath')
    
    def set_path(self, path_str):
        self.entity_data['filepath'] = path_str
    
    def set_asset_info(self, info:AssetInfo): 
        self.asset_info = info
    
    def is_assigned(self) -> bool:
        return self.get_path() != ''

    def clear(self):
        self.entity_data['filepath'] = ''
      
    @staticmethod
    def create(asset_info_id):
        asset = Asset()
        asset_info = g_assetFactory.get_asset_info(asset_info_id)
        asset.set_asset_info(asset_info)
        return asset
        
class AssetPath(EntityABC):
        
    def __init__(self, entity_data: typing.Dict[str, typing.Any] = None):
        self.asset_info:AssetInfo = None
        if entity_data is None:
            entity_data = _get_default_asset_path_data_model()
        
        if 'asset_type' in entity_data and entity_data['asset_type']:
            self.asset_info = g_assetFactory.get_asset_info(entity_data['asset_type'])
        
        super(AssetPath, self).__init__(entity_data)
    
    def get_asset_info_id(self) -> str:
        return self.asset_info.id 
    
    def get_asset_info(self) -> AssetInfo:
        return self.asset_info
    
    def get_path(self) -> str:
        return self.entity_data['path']
    
    def get_path_FN(self) -> io.FileName:
        return self._get_filename_from_field('path')
    
    def set_path(self, path_str):
        self.entity_data['path'] = path_str
    
    def set_asset_info(self, info:AssetInfo): 
        self.asset_info = info
    
    def clear(self):
        self.entity_data['path'] = None
         

# legacy
# |----- LauncherABC (abstract class)
#        |
#        |----- StandaloneLauncher (Standalone launcher)
#        |
#        |----- ROMLauncherABC (abstract class)
#               |
#               |----- CollectionLauncher (ROM Collection launcher)
#               |
#               |----- VirtualLauncher (Browse by ... launcher)
#               |
#               |----- StandardRomLauncher (Standard launcher)
#               |
#               |----- LnkLauncher
#               |
#               |----- RetroplayerLauncher
#               |
#               |----- RetroarchLauncher
#               |
#               |----- SteamLauncher
#               |
#               |----- NvidiaGameStreamLauncher
#
# -------------------------------------------------------------------------------------------------

class ROMAddon(EntityABC):
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, addon: AelAddon, entity_data: dict):
        self.addon = addon 
        super(ROMAddon, self).__init__(entity_data)
        
    def get_name(self):
        secondary_name = self.get_secondary_name()
        if secondary_name: return '{} ({})'.format(self.addon.get_name(), secondary_name)
        return self.addon.get_name()
    
    def get_secondary_name(self):
        settings = self.get_settings()
        return settings['secname'] if 'secname' in settings else None   
            
    def get_settings_str(self) -> str:
        return self.entity_data['settings'] if 'settings' in self.entity_data else None
    
    def get_settings(self) -> dict:
        settings = self.get_settings_str()
        if settings is None:
            return {}
        return json.loads(settings)
    
    def set_settings_str(self, addon_settings:str):
        self.entity_data['settings'] = addon_settings
    
    def set_settings(self, addon_settings:dict):
        self.entity_data['settings'] = json.dumps(addon_settings)
    
    def get_addon(self) -> AelAddon:
        return self.addon
            
class ROMLauncherAddon(ROMAddon):
    __metaclass__ = abc.ABCMeta
    
    def is_default(self) -> bool:
        return self.entity_data['is_default'] if 'is_default' in self.entity_data else False
    
    def set_default(self, default_launcher=False):
        self.entity_data['is_default'] = default_launcher
        
    def get_launch_command(self, rom: ROM) -> dict:
        return {
            '--cmd': 'launch',
            '--type': constants.AddonType.LAUNCHER.name,
            '--server_host': globals.WEBSERVER_HOST,
            '--server_port': globals.WEBSERVER_PORT,
            '--akl_addon_id': self.get_id(),
            '--rom_id': rom.get_id()
        }

    def get_configure_command(self, romcollection: ROMCollection) -> dict:                    
        return {
            '--cmd': 'configure',
            '--type': constants.AddonType.LAUNCHER.name,
            '--server_host': globals.WEBSERVER_HOST,
            '--server_port': globals.WEBSERVER_PORT,
            '--romcollection_id': romcollection.get_id(), 
            '--akl_addon_id': self.get_id()
        }
        
    def get_configure_command_for_rom(self, rom: ROM) -> dict:
        return {
            '--cmd': 'configure',
            '--type': constants.AddonType.LAUNCHER.name,
            '--server_host': globals.WEBSERVER_HOST,
            '--server_port': globals.WEBSERVER_PORT,
            '--rom_id': rom.get_id(), 
            '--akl_addon_id': self.get_id()
        }
        
    def launch(self, rom: ROM):
        kodi.run_script(
            self.addon.get_addon_id(), 
            self.get_launch_command(rom))

    def configure(self, romcollection:ROMCollection):
        kodi.run_script(
            self.addon.get_addon_id(), 
            self.get_configure_command(romcollection))
    
    def configure_for_rom(self, rom:ROM):
        kodi.run_script(
            self.addon.get_addon_id(), 
            self.get_configure_command_for_rom(rom))


class RetroplayerLauncherAddon(ROMLauncherAddon):
    
    def get_launch_command(self, rom: ROM) -> dict:
        return None

    def get_configure_command(self, romcollection: ROMCollection) -> dict:
        return None

    def launch(self, rom: ROM):
        rom_file_path = rom.get_scanned_data_element_as_file('file')
        if rom_file_path is None:
            logger.warning(f'Cannot launch ROM {rom.get_rom_identifier()}. No path provided.')
            kodi.notify_warn('Cannot launch ROM')
            return
            
        # >> How to fill gameclient = string (game.libretro.fceumm) ???
        game_info = {
            'title'    : rom.get_name(),     'platform'  : rom.get_platform(),
            'genres'   : [rom.get_genre()],  'developer' : rom.get_developer(),
            'overview' : rom.get_plot(),     'year'      : rom.get_releaseyear()
        }
        logger.info(f'launch() name     "{rom.get_name()}"')
        logger.info(f'launch() path     "{rom_file_path.getPath()}"')

        logger.debug('Executing Retroplayer')
        kodi.play_item(rom.get_name(), rom_file_path.getPath(), 'game', game_info)
        logger.debug('Retroyplayer call finished')
   
    def configure(self, romcollection: ROMCollection):
        post_data = {
            'romcollection_id': romcollection.get_id(),
            'akl_addon_id': self.get_id(),
            'addon_id': self.addon.get_addon_id(),
            'settings': {}
        }        
        is_stored = api.client_post_launcher_settings(globals.WEBSERVER_HOST, globals.WEBSERVER_PORT, post_data)
        if not is_stored:
            kodi.notify_error('Failed to store launchers settings')
            
    def configure_for_rom(self, rom: ROM):
        post_data = {
            'rom_id': rom.get_id(),
            'akl_addon_id': self.get_id(),
            'addon_id': self.addon.get_addon_id(),
            'settings': {}
        }        
        is_stored = api.client_post_launcher_settings(globals.WEBSERVER_HOST, globals.WEBSERVER_PORT, post_data)
        if not is_stored:
            kodi.notify_error('Failed to store launchers settings')
     
class ROMCollectionScanner(ROMAddon):
    
    def get_last_scan_timestamp(self):
        return None
    
    def get_scan_command(self, rom_collection: ROMCollection) -> dict:
        return {
            '--cmd': 'scan',
            '--type': constants.AddonType.SCANNER.name,
            '--server_host': globals.WEBSERVER_HOST,
            '--server_port': globals.WEBSERVER_PORT,
            '--romcollection_id': rom_collection.get_id(),
            '--akl_addon_id': self.get_id()
        }
        
    def get_configure_command(self, romcollection: ROMCollection) -> dict:        
        return {
            '--cmd': 'configure',
            '--type': constants.AddonType.SCANNER.name,
            '--server_host': globals.WEBSERVER_HOST,
            '--server_port': globals.WEBSERVER_PORT,
            '--romcollection_id': romcollection.get_id(),
            '--akl_addon_id':  self.get_id()
        }

class ScraperAddon(ROMAddon):
    
    def __init__(self, addon: AelAddon, scraper_settings: ScraperSettings):        
        entity_data = {
            'settings': json.dumps(scraper_settings.get_data_dic())
        }        
        super(ScraperAddon, self).__init__(addon, entity_data)
    
    def settings_are_applicable(self) -> bool:
        settings = self.get_scraper_settings()

        if settings.scrape_metadata_policy != constants.SCRAPE_ACTION_NONE:
            supported_metadata_types = self.get_supported_metadata()
            if len(supported_metadata_types) > 0: return True

        if settings.scrape_assets_policy != constants.SCRAPE_ACTION_NONE:
            supported_asset_types = self.get_supported_assets()
            if len(supported_asset_types) == 0: return False
            asset_overlap = list(set(supported_asset_types) & set(settings.asset_IDs_to_scrape))
            if len(asset_overlap) > 0: return True
        
        return False

    def is_metadata_supported(self, metadata_id) -> bool:
        supported_items = self.get_supported_metadata()
        return supported_items is not None and metadata_id in supported_items

    def is_asset_supported(self, asset_id) -> bool:
        supported_items = self.get_supported_assets()
        return supported_items is not None and asset_id in supported_items

    def get_supported_metadata(self) -> typing.List[str]:
        extra_settings = self.addon.get_extra_settings()
        supported_types = extra_settings['supported_metadata'] if 'supported_metadata' in extra_settings else None
        if supported_types is None: return None
        return supported_types.split('|')

    def get_supported_assets(self) -> typing.List[str]:
        extra_settings = self.addon.get_extra_settings()
        supported_types = extra_settings['supported_assets'] if 'supported_assets' in extra_settings else None
        if supported_types is None: return None
        return supported_types.split('|')

    def get_scraper_settings(self) -> ScraperSettings:
        settings_dict = self.get_settings()
        return ScraperSettings.from_settings_dict(settings_dict)
        
    def set_scraper_settings(self, settings: ScraperSettings):
        self.entity_data['settings'] = json.dumps(settings.get_data_dic())
        
    def get_scrape_command(self, rom: ROM)-> dict:        
        return {
            '--cmd': 'scrape',
            '--type': constants.AddonType.SCRAPER.name,
            '--server_host': globals.WEBSERVER_HOST,
            '--server_port': globals.WEBSERVER_PORT,
            '--akl_addon_id': self.addon.get_id(),
            '--rom_id': rom.get_id(),
            '--settings':  io.parse_to_json_arg(self.get_settings())
        }
        
    def get_scrape_command_for_collection(self, collection: ROMCollection) -> dict:     
        return {
            '--cmd': 'scrape',
            '--type': constants.AddonType.SCRAPER.name,
            '--server_host': globals.WEBSERVER_HOST,
            '--server_port': globals.WEBSERVER_PORT,
            '--akl_addon_id': self.addon.get_id(),
            '--romcollection_id': collection.get_id(),
            '--settings':  io.parse_to_json_arg(self.get_settings())
        }
 
# -------------------------------------------------------------------------------------------------
# Abstract base class for business objects which support the generic
# metadata fields and assets.
#
# --- Class hierarchy ---
#  
# |-MetaDataItemABC(object) (abstract class)
# |
# |----- Category
# |      |
# |      |----- VirtualCategory
# |
# |----- ROMCollection (Collection)
# |      |
# |      |----- VirtualCollection
# |
# |----- ROM
# |
#
class MetaDataItemABC(EntityABC):
    __metaclass__ = abc.ABCMeta

    def __init__(self, 
                 entity_data: typing.Dict[str, typing.Any], 
                 assets: typing.List[Asset],
                 asset_paths_data: typing.List[AssetPath] = None):
        
        self.assets: typing.Dict[str, Asset] = {}
        if assets is not None:
            for asset in assets:
                self.assets[asset.get_asset_info_id()] = asset
        
        self.asset_paths: typing.Dict[str, AssetPath] = {}
        if asset_paths_data is not None:
            for path in asset_paths_data:
                self.asset_paths[path.get_asset_info_id()] = path
                
        super(MetaDataItemABC, self).__init__(entity_data)

    # --------------------------------------------------------------------------------------------
    # Core functions
    # --------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def get_object_name(self) -> str: pass

    @abc.abstractmethod
    def get_assets_kind(self) -> int:
        pass

    @abc.abstractmethod
    def get_type(self) -> str:
        pass

    # --- Metadata --------------------------------------------------------------------------------
    def get_name(self):
        return self.entity_data['m_name'] if 'm_name' in self.entity_data else 'Unknown'

    def set_name(self, name):
        self.entity_data['m_name'] = name

    def get_releaseyear(self):
        return self.entity_data['m_year'] if 'm_year' in self.entity_data else ''

    def set_releaseyear(self, releaseyear):
        self.entity_data['m_year'] = releaseyear

    def get_genre(self) -> str:
        return self.entity_data['m_genre'] if 'm_genre' in self.entity_data else ''

    def set_genre(self, genre):
        self.entity_data['m_genre'] = genre

    def get_developer(self) -> str:
        return self.entity_data['m_developer'] if 'm_developer' in self.entity_data else ''

    def set_developer(self, developer):
        self.entity_data['m_developer'] = developer

    # In AKL 0.9.7 m_rating is stored as a string.
    def get_rating(self):
        return int(self.entity_data['m_rating']) if 'm_rating' in self.entity_data and self.entity_data['m_rating'] else ''

    def set_rating(self, rating):
        try:
            self.entity_data['m_rating'] = int(rating)
        except:
            self.entity_data['m_rating'] = ''

    def get_plot(self):
        return self.entity_data['m_plot'] if 'm_plot' in self.entity_data else ''

    def set_plot(self, plot):
        self.entity_data['m_plot'] = plot

    #
    # Used when rendering Categories/Launchers/ROMs
    #
    def get_trailer(self):
        return self.assets[constants.ASSET_TRAILER_ID].get_path() if constants.ASSET_TRAILER_ID in self.assets else ''

    def set_trailer(self, trailer_str):
        if 'http' in trailer_str:
            matches = re.search(r'^.*((youtu.(be|com)\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#\&\?]*).*', trailer_str, re.I)
            if matches is not None:
                video_id = matches.groups()[-1]
                trailer_str = 'plugin://plugin.video.youtube/play/?video_id={}'.format(video_id)

        trailer_asset = self.get_asset(constants.ASSET_TRAILER_ID)
        if trailer_asset is None:
            self.assets[constants.ASSET_TRAILER_ID] = Asset.create(constants.ASSET_TRAILER_ID)
                        
        self.assets[constants.ASSET_TRAILER_ID].set_path(trailer_str)

    # --- Finished status stuff -------------------------------------------------------------------
    def is_finished(self):
        return 'finished' in self.entity_data and self.entity_data['finished']

    def get_finished_str(self):
        finished = self.is_finished()
        finished_display = 'Finished' if finished == True else 'Unfinished'

        return finished_display

    def change_finished_status(self):
        finished = self.entity_data['finished']
        finished = False if finished else True
        self.entity_data['finished'] = finished

    # --- Assets/artwork --------------------------------------------------------------------------
    def has_asset(self, asset_info: AssetInfo) -> bool:
        if not asset_info.id in self.assets: return False
        return self.assets[asset_info.id] != None and self.assets[asset_info.id].get_path() != ''

    def get_asset(self, asset_id: str) -> Asset:
        return self.assets[asset_id] if asset_id in self.assets else None
    
    def get_assets(self) -> typing.List[Asset]:
        return list(self.assets.values())
 
    #
    # Returns a collection with the object assets, ready to be edited.
    # Values are the current assets and a path value of '' if the asset is not set.
    #
    def get_available_assets(self) -> typing.List[Asset]:
        asset_info_list = g_assetFactory.get_asset_list_by_IDs(self.get_asset_ids_list())
        available_assets = []
        for asset_info in asset_info_list:
            asset = self.get_asset(asset_info.id)
            if asset is None:
                asset = Asset()
                asset.set_asset_info(asset_info)
                
            available_assets.append(asset)

        return available_assets
                
    # 
    # Gets the asset path (str) of the given assetinfo type.
    #
    def get_asset_str(self, asset_info=None, asset_id=None, fallback = '') -> str:
        if asset_info is None and asset_id is None: return None
        if asset_info is not None: asset_id = asset_info.id
        
        asset = self.get_asset(asset_id)
        if asset is not None:
            path = asset.get_path()
            if path != '': return path
            
        return fallback
            
    def get_asset_FN(self, asset_info: AssetInfo) -> io.FileName:
        if asset_info is None: return None
        
        asset = self.get_asset(asset_info.id)
        if asset is None: return None
        
        return asset.get_path_FN()
        
    def set_asset(self, asset_info: AssetInfo, path_FN: io.FileName):
        path = path_FN.getPath() if path_FN else ''
        
        asset = self.get_asset(asset_info.id)
        if asset is None: self.assets[asset_info.id] = Asset.create(asset_info.id)
                        
        self.assets[asset_info.id].set_path(path)
        
    def clear_asset(self, asset_info: AssetInfo):
        asset = self.get_asset(asset_info.id)
        if asset is None:
            self.assets[asset_info.id] = Asset.create(asset_info.id)
        asset.clear()
        
    def get_assets_root_path(self) -> io.FileName:
        return self._get_directory_filename_from_field('assets_path')  
    
    def set_assets_root_path(self, path: io.FileName, asset_ids = [], create_default_subdirectories = False):
        path_str = path.getPath() if path else ''        
        self.entity_data['assets_path'] = path_str    
        
        if create_default_subdirectories:
            asset_ids = self.get_asset_ids_list() if not asset_ids else asset_ids
            for asset_info_id in asset_ids:
                asset_info = g_assetFactory.get_asset_info(asset_info_id)
                new_path = path.pjoin(asset_info.plural.lower(), isdir=True)
                self.set_asset_path(asset_info, new_path.getPath())
                if not new_path.exists(): new_path.makedirs()
                    
    
    def get_asset_paths(self) -> typing.List[AssetPath]:
        return list(self.asset_paths.values())

    def get_asset_path(self, asset_info: AssetInfo, fallback_to_root = True) -> io.FileName:
        if not asset_info: return None
        if asset_info.id in self.asset_paths:
            return self.asset_paths[asset_info.id].get_path_FN()
        
        if fallback_to_root and self.get_assets_root_path() is not None:
            return self.get_assets_root_path().pjoin(asset_info.plural.lower(), isdir=True)
        return None

    def set_asset_path(self, asset_info: AssetInfo, path: str):
        logger.debug(f'Setting "{asset_info.id}" to {path}')
        asset_path = self.asset_paths[asset_info.id] if asset_info.id in self.asset_paths else AssetPath()
        asset_path.set_path(path)
        asset_path.set_asset_info(asset_info)
        
        self.asset_paths[asset_info.id] = asset_path
    
    @abc.abstractmethod
    def get_asset_ids_list(self) -> typing.List[str]:
        pass
    
    @abc.abstractmethod
    def get_mappable_asset_ids_list(self) -> typing.List[str]:
        return []
    
    @abc.abstractmethod
    def get_default_icon(self) -> str:
        pass 
    
    def is_mappable_asset(self, asset_info) -> bool:
        return asset_info.id in self.get_mappable_asset_ids_list()
    
    # returns the complete set of assets as they are mapped for the view
    def get_view_assets(self) -> typing.Dict[str,str]:
        asset_ids = self.get_asset_ids_list()
        mappable_asset_ids = self.get_mappable_asset_ids_list()
        view_asset_ids = asset_ids + list(set(mappable_asset_ids) - set(asset_ids))
        
        view_assets = {}
        for asset_id in view_asset_ids:
            asset_info = g_assetFactory.get_asset_info(asset_id)
            value = ''
            fallback_str = ''
            
            if asset_id in self.assets:
                asset = self.assets[asset_id]
                value = asset.get_path()
            
            if self.is_mappable_asset(asset_info):
                if asset_info.id == constants.ASSET_ICON_ID: fallback_str = self.get_default_icon()
                value = self.get_mapped_asset_str(asset_info, fallback=fallback_str)
                
            view_assets[asset_info.fname_infix] = value
        return view_assets
    # 
    # Gets the asset path (str) of the mapped asset type following
    # the given input of either an assetinfo object or asset id.
    #
    def get_mapped_asset_str(self, asset_info=None, asset_id=None, fallback = '') -> str:
        asset_info = self.get_mapped_asset_info(asset_info, asset_id)
        asset = self.get_asset(asset_info.id)
        if asset is not None and asset.get_path() != '':
            return asset.get_path()
        
        return fallback
    
    #
    # Get a list of the assets that can be mapped to a defaultable asset.
    # They must be images, no videos, no documents.
    #
    def get_mappable_asset_list(self) -> typing.List[AssetInfo]: 
        return g_assetFactory.get_asset_list_by_IDs(self.get_mappable_asset_ids_list(), 'image')

    def get_mapped_assets(self) -> typing.Dict[str,str]:
        mappable_assets = self.get_mappable_asset_list()
        mapped_assets = {}
        for mappable_asset in mappable_assets:
            if mappable_asset.id == constants.ASSET_ICON_ID: 
                mapped_assets[mappable_asset.fname_infix] = self.get_mapped_asset_str(mappable_asset, fallback=self.get_default_icon())
            else: mapped_assets[mappable_asset.fname_infix] = self.get_mapped_asset_str(mappable_asset)
        return mapped_assets

    #
    # Gets the actual assetinfo object that is mapped for
    # the given assetinfo for this particular MetaDataItem.
    #
    def get_mapped_asset_info(self, asset_info=None, asset_id=None):
        if asset_info is None and asset_id is None: return None
        if asset_id is not None: asset_info = g_assetFactory.get_asset_info(asset_id)
        
        mapped_key = self.get_mapped_asset_key(asset_info)
        mapped_asset_info = g_assetFactory.get_asset_info_by_key(mapped_key)
        return mapped_asset_info
       
    #
    # Gets the database filename mapped for asset_info.
    # Note that the mapped asset uses diferent fields wheter it is a Category/Launcher/ROM
    #
    def get_mapped_asset_key(self, asset_info: AssetInfo):
        if asset_info.default_key == '':
            logger.error('Requested mapping for AssetInfo without default key. Type {}'.format(asset_info.id))
            raise constants.AddonError('Not supported asset type used. This might be a bug!')  
        
        if asset_info.default_key not in self.entity_data:
            return asset_info.key
        
        return self.entity_data[asset_info.default_key]
	
    def set_mapped_asset_key(self, asset_info: AssetInfo, mapped_to_info: AssetInfo):
        self.entity_data[asset_info.default_key] = mapped_to_info.key
        
    def __str__(self):
        return '{}#{}: {}'.format(self.get_object_name(), self.get_id(), self.get_name())

# -------------------------------------------------------------------------------------------------
# Class representing an AKL Cateogry.
# Contains code to generate the context menus passed to Dialog.select()
# -------------------------------------------------------------------------------------------------
class Category(MetaDataItemABC):
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, category_dic: typing.Dict[str, typing.Any] = None, assets: typing.List[Asset] = None):
        # Concrete classes are responsible of creating a default entity_data dictionary
        # with sensible defaults.
        if category_dic is None:
            category_dic = _get_default_category_data_model()
            category_dic['id'] = text.misc_generate_random_SID()
        super(Category, self).__init__(category_dic, assets)

    def get_object_name(self): return 'Category'

    def get_assets_kind(self):
        return constants.KIND_ASSET_CATEGORY
    
    def get_type(self): return constants.OBJ_CATEGORY
    
    # parent category / romcollection this item belongs to.
    def get_parent_id(self) -> str:
        return self.entity_data['parent_id'] if 'parent_id' in self.entity_data else None
    
    def num_romcollections(self) -> int:
        return self.entity_data['num_romcollections'] if 'num_romcollections' in self.entity_data else 0

    def num_categories(self) -> int:
        return self.entity_data['num_categories'] if 'num_categories' in self.entity_data else 0

    def has_items(self) -> bool:
        return self.num_romcollections() > 0 or self.num_categories() > 0

    def get_asset_ids_list(self):
        return constants.CATEGORY_ASSET_ID_LIST
    
    def get_mappable_asset_ids_list(self):
        return constants.MAPPABLE_CATEGORY_ASSET_ID_LIST
    
    def get_default_icon(self) -> str:
        return 'DefaultFolder.png' 
    
    def get_NFO_name(self) -> io.FileName:
        nfo_dir = io.FileName(settings.getSetting('categories_asset_dir'), isdir = True)
        nfo_file_path = nfo_dir.pjoin(self.get_name() + '.nfo')
        logger.debug("Category.get_NFO_name() nfo_file_path = '{0}'".format(nfo_file_path.getPath()))
        return nfo_file_path
    
    # ---------------------------------------------------------------------------------------------
    # NFO files for metadata
    # ---------------------------------------------------------------------------------------------
    #
    # Python data model: lists and dictionaries are mutable. It means the can be changed if passed as
    # parameters of functions. However, items can not be replaced by new objects!
    # Notably, numbers, strings and tuples are immutable. Dictionaries and lists are mutable.
    #
    # See http://stackoverflow.com/questions/986006/how-do-i-pass-a-variable-by-reference
    # See https://docs.python.org/2/reference/datamodel.html
    #
    # Function asumes that the NFO file already exists.
    #
    def import_NFO_file(self, nfo_FileName: io.FileName) -> bool:
        # --- Get NFO file name ---
        logger.debug('Category.import_NFO_file() Importing launcher NFO "{0}"'.format(nfo_FileName.getPath()))

        # --- Import data ---
        if nfo_FileName.exists():
            try:
                item_nfo = nfo_FileName.loadFileToStr()
                item_nfo = item_nfo.replace('\r', '').replace('\n', '')
            except:
                kodi.notify_warn('Exception reading NFO file {0}'.format(nfo_FileName.getPath()))
                logger.error("Category.import_NFO_file() Exception reading NFO file '{0}'".format(nfo_FileName.getPath()))
                return False
        else:
            kodi.notify_warn('NFO file not found {0}'.format(nfo_FileName.getBase()))
            logger.error("Category.import_NFO_file() NFO file not found '{0}'".format(nfo_FileName.getPath()))
            return False

        item_year      = re.findall('<year>(.*?)</year>',           item_nfo)
        item_genre     = re.findall('<genre>(.*?)</genre>',         item_nfo)
        item_developer = re.findall('<developer>(.*?)</developer>', item_nfo)
        item_rating    = re.findall('<rating>(.*?)</rating>',       item_nfo)
        item_plot      = re.findall('<plot>(.*?)</plot>',           item_nfo)

        # >> Careful about object mutability! This should modify the dictionary
        # >> passed as argument outside this function.
        if len(item_year) > 0:      self.set_releaseyear(text.unescape_XML(item_year[0]))
        if len(item_genre) > 0:     self.set_genre(text.unescape_XML(item_genre[0]))
        if len(item_developer) > 0: self.set_developer(text.unescape_XML(item_developer[0]))
        if len(item_rating) > 0:    self.set_rating(text.unescape_XML(item_rating[0]))
        if len(item_plot) > 0:      self.set_plot(text.unescape_XML(item_plot[0]))

        logger.debug("Category.import_NFO_file() Imported '{0}'".format(nfo_FileName.getPath()))

        return True
    
    def export_to_NFO_file(self, nfo_FileName: io.FileName):
        # --- Get NFO file name ---
        logger.debug('Category.export_to_NFO_file() Exporting launcher NFO "{0}"'.format(nfo_FileName.getPath()))

        # If NFO file does not exist then create them. If it exists, overwrite.
        nfo_content = []
        nfo_content.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        nfo_content.append('<!-- Exported by AKL on {0} -->\n'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
        nfo_content.append('<category>\n')
        nfo_content.append(text.XML_line('year',      self.get_releaseyear()))
        nfo_content.append(text.XML_line('genre',     self.get_genre())) 
        nfo_content.append(text.XML_line('developer', self.get_developer()))
        nfo_content.append(text.XML_line('rating',    self.get_rating()))
        nfo_content.append(text.XML_line('plot',      self.get_plot()))
        
        nfo_content.append('</category>\n')
        full_string = ''.join(nfo_content)
        nfo_FileName.writeAll(full_string)
            
    def export_to_file(self, file: io.FileName):
        logger.debug('Category.export_to_file() Category "{0}" (ID "{1}")'.format(self.get_name(), self.get_id()))

        # --- Create list of strings ---
        str_list = []
        str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        str_list.append('<!-- Exported by AKL on {0} -->\n'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
        str_list.append('<advanced_emulator_launcher_configuration>\n')
        str_list.append('<category>\n')
        str_list.append(text.XML_line('name', self.get_name()))
        str_list.append(text.XML_line('year', self.get_releaseyear()))
        str_list.append(text.XML_line('genre', self.get_genre()))
        str_list.append(text.XML_line('developer', self.get_developer()))
        str_list.append(text.XML_line('rating', self.get_rating()))
        str_list.append(text.XML_line('plot', self.get_plot()))
        str_list.append(text.XML_line('Asset_Prefix', self.get_custom_attribute('Asset_Prefix')))
        str_list.append(text.XML_line('s_icon', self.get_asset_str(asset_id=constants.ASSET_ICON_ID)))
        str_list.append(text.XML_line('s_fanart', self.get_asset_str(asset_id=constants.ASSET_FANART_ID)))
        str_list.append(text.XML_line('s_banner', self.get_asset_str(asset_id=constants.ASSET_BANNER_ID)))
        str_list.append(text.XML_line('s_poster', self.get_asset_str(asset_id=constants.ASSET_POSTER_ID)))
        str_list.append(text.XML_line('s_controller', self.get_asset_str(asset_id=constants.ASSET_CONTROLLER_ID)))
        str_list.append(text.XML_line('s_clearlogo', self.get_asset_str(asset_id=constants.ASSET_CLEARLOGO_ID)))
        str_list.append('</category>\n')
        str_list.append('</advanced_emulator_launcher_configuration>\n')
        
        full_string = ''.join(str_list)
        file.writeAll(full_string)
        
    def __str__(self):
        return super().__str__()
    
class VirtualCategory(Category):
    
    def get_object_name(self): return 'Virtual Category'
    
    def get_assets_kind(self): return constants.KIND_ASSET_CATEGORY
    
    def get_type(self): return constants.OBJ_CATEGORY_VIRTUAL
 
# -------------------------------------------------------------------------------------------------
# Class representing a collection of ROMs.
# -------------------------------------------------------------------------------------------------
class ROMCollection(MetaDataItemABC):
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, 
                 entity_data: dict = None, 
                 assets_data: typing.List[Asset] = None,
                 asset_paths: typing.List[AssetPath] = None,
                 launchers_data: typing.List[ROMLauncherAddon] = [], 
                 scanners_data: typing.List[ROMCollectionScanner] = []):
        # Concrete classes are responsible of creating a default entity_data dictionary
        # with sensible defaults.
        if entity_data is None:
            entity_data = _get_default_ROMCollection_data_model()
            entity_data['id'] = text.misc_generate_random_SID()
            
        self.launchers_data = launchers_data
        self.scanners_data = scanners_data
        super(ROMCollection, self).__init__(entity_data, assets_data, asset_paths)

    def get_object_name(self): return 'ROM Collection'

    def get_assets_kind(self): return constants.KIND_ASSET_LAUNCHER
    
    def get_type(self): return constants.OBJ_ROMCOLLECTION
    
    # parent category / romcollection this item belongs to.
    def get_parent_id(self) -> str:
        return self.entity_data['parent_id'] if 'parent_id' in self.entity_data else None
        
    def get_platform(self): return self.entity_data['platform'] if 'platform' in self.entity_data else None

    def set_platform(self, platform): self.entity_data['platform'] = platform

    def get_box_sizing(self):
        return self.entity_data['box_size'] if 'box_size' in self.entity_data else constants.BOX_SIZE_POSTER
    
    def set_box_sizing(self, box_size):
        self.entity_data['box_size'] = box_size

    def get_asset_ids_list(self):
        return constants.LAUNCHER_ASSET_ID_LIST

    def get_mappable_asset_ids_list(self): return constants.MAPPABLE_LAUNCHER_ASSET_ID_LIST

    def get_default_icon(self) -> str:
        return 'DefaultGameAddons.png'   
    
    def get_ROM_mappable_asset_list(self) -> typing.List[AssetInfo]:
        return g_assetFactory.get_asset_list_by_IDs(constants.MAPPABLE_ROM_ASSET_ID_LIST)

    #
    # Gets the actual assetinfo object that is mapped for
    # the given (ROM) assetinfo for this particular MetaDataItem.
    #
    def get_mapped_ROM_asset_info(self, asset_info=None, asset_id=None) -> AssetInfo:
        if asset_info is None and asset_id is None:
            return None
        if asset_id is not None:
            asset_info = g_assetFactory.get_asset_info(asset_id)
        
        mapped_key = self.get_mapped_ROM_asset_key(asset_info)
        mapped_asset_info = g_assetFactory.get_asset_info_by_key(mapped_key)
        return mapped_asset_info

    #
    # Gets the database filename mapped for asset_info.
    # Note that the mapped asset uses diferent fields wheter it is a Category/Launcher/ROM
    #
    def get_mapped_ROM_asset_key(self, asset_info: AssetInfo) -> str:
        if asset_info.rom_default_key == '':
            logger.error(f'Requested mapping for AssetInfo without default key. Type {asset_info.id}')
            raise constants.AddonError('Not supported asset type used. This might be a bug!')  
        
        if asset_info.rom_default_key not in self.entity_data:
            return asset_info.key   
        return self.entity_data[asset_info.rom_default_key]

    def set_mapped_ROM_asset_key(self, asset_info: AssetInfo, mapped_to_info: AssetInfo):
        self.entity_data[asset_info.rom_default_key] = mapped_to_info.key

    #
    # Get a list of assets with duplicated paths. Refuse to do anything if duplicated paths found.
    #
    def get_duplicated_asset_dirs(self):
        duplicated_bool_list   = [False] * len(constants.ROM_ASSET_ID_LIST)
        duplicated_name_list   = []

        # >> Check for duplicated asset paths
        for i, asset_i in enumerate(constants.ROM_ASSET_ID_LIST[:-1]):
            A_i = g_assetFactory.get_asset_info(asset_i)
            for j, asset_j in enumerate(constants.ROM_ASSET_ID_LIST[i+1:]):
                A_j = g_assetFactory.get_asset_info(asset_j)
                # >> Exclude unconfigured assets (empty strings).
                if A_i.path_key not in self.entity_data or A_j.path_key not in self.entity_data  \
                    or not self.entity_data[A_i.path_key] or not self.entity_data[A_j.path_key]: continue
                
                # logger.debug('asset_get_duplicated_asset_list() Checking {0:<9} vs {1:<9}'.format(A_i.name, A_j.name))
                if self.entity_data[A_i.path_key] == self.entity_data[A_j.path_key]:
                    duplicated_bool_list[i] = True
                    duplicated_name_list.append('{0} and {1}'.format(A_i.name, A_j.name))
                    logger.info('asset_get_duplicated_asset_list() DUPLICATED {0} and {1}'.format(A_i.name, A_j.name))

        return duplicated_name_list

    def num_roms(self) -> int:
        return self.entity_data['num_roms'] if 'num_roms' in self.entity_data else 0

    def has_roms(self) -> bool:
        return self.num_roms() > 0

    def has_launchers(self) -> bool:
        return len(self.launchers_data) > 0

    def add_launcher(self, addon: AelAddon, settings: dict, is_non_blocking = True, is_default: bool = False):
        launcher = ROMLauncherAddonFactory.create(addon, { 
            'settings': json.dumps(settings),
            'is_non_blocking': is_non_blocking,
            'is_default': is_default
        })        
        if is_default:
            current_default_launcher = next((l for l in self.launchers_data if l.is_default()), None)
            if current_default_launcher: current_default_launcher.set_default(False)
            
        self.launchers_data.append(launcher)
        logger.debug(f'Adding addon "{addon.get_addon_id()}" to collection "{self.get_name()}"')

    def get_launchers(self) -> typing.List[ROMLauncherAddon]:
        return self.launchers_data

    def get_launcher(self, id:str) -> ROMLauncherAddon:
        return next((l for l in self.launchers_data if l.get_id() == id), None)

    def get_default_launcher(self) -> ROMLauncherAddon:
        if len(self.launchers_data) == 0: return None
        default_launcher = next((l for l in self.launchers_data if l.is_default()), None)
        if default_launcher is None: return self.launchers_data[0]
        
        return default_launcher

    def set_launcher_as_default(self, launcher_id):
        if len(self.launchers_data) == 0: return
        
        current_default_launcher = next((l for l in self.launchers_data if l.is_default()), None)
        if current_default_launcher: current_default_launcher.set_default(False)
        
        launcher_to_be_default = next((l for l in self.launchers_data if l.get_id() == launcher_id), None)
        if launcher_to_be_default:
            launcher_to_be_default.set_default(True)

    def has_scanners(self) -> bool:
        return len(self.scanners_data) > 0
    
    def add_scanner(self, addon: AelAddon, settings: dict):
        scanner = ROMCollectionScanner(addon, {})
        scanner.set_settings(settings)
        self.scanners_data.append(scanner)

    def get_scanners(self) -> typing.List[ROMCollectionScanner]:
        return self.scanners_data

    def get_scanner(self, id:str) -> ROMCollectionScanner:
        return next((s for s in self.scanners_data if s.get_id() == id), None)

    def get_NFO_name(self) -> io.FileName:
        nfo_dir = io.FileName(settings.getSetting('launchers_asset_dir'), isdir = True)
        nfo_file_path = nfo_dir.pjoin(self.get_name() + '.nfo')
        logger.debug("ROMCollection.get_NFO_name() nfo_file_path = '{0}'".format(nfo_file_path.getPath()))
        return nfo_file_path

    # ---------------------------------------------------------------------------------------------
    # NFO files for metadata
    # ---------------------------------------------------------------------------------------------
    #
    # Python data model: lists and dictionaries are mutable. It means the can be changed if passed as
    # parameters of functions. However, items can not be replaced by new objects!
    # Notably, numbers, strings and tuples are immutable. Dictionaries and lists are mutable.
    #
    # See http://stackoverflow.com/questions/986006/how-do-i-pass-a-variable-by-reference
    # See https://docs.python.org/2/reference/datamodel.html
    #
    # Function asumes that the NFO file already exists.
    #
    def import_NFO_file(self, nfo_FileName: io.FileName) -> bool:
        # --- Get NFO file name ---
        logger.debug('ROMCollection.import_NFO_file() Importing launcher NFO "{0}"'.format(nfo_FileName.getPath()))

        # --- Import data ---
        if nfo_FileName.exists():
            try:
                item_nfo = nfo_FileName.loadFileToStr()
                item_nfo = item_nfo.replace('\r', '').replace('\n', '')
            except:
                kodi.notify_warn('Exception reading NFO file {0}'.format(nfo_FileName.getPath()))
                logger.error("ROMCollection.import_NFO_file() Exception reading NFO file '{0}'".format(nfo_FileName.getPath()))
                return False
        else:
            kodi.notify_warn('NFO file not found {0}'.format(nfo_FileName.getBase()))
            logger.error("ROMCollection.import_NFO_file() NFO file not found '{0}'".format(nfo_FileName.getPath()))
            return False

        item_year      = re.findall('<year>(.*?)</year>',           item_nfo)
        item_genre     = re.findall('<genre>(.*?)</genre>',         item_nfo)
        item_developer = re.findall('<developer>(.*?)</developer>', item_nfo)
        item_rating    = re.findall('<rating>(.*?)</rating>',       item_nfo)
        item_plot      = re.findall('<plot>(.*?)</plot>',           item_nfo)

        # >> Careful about object mutability! This should modify the dictionary
        # >> passed as argument outside this function.
        if len(item_year) > 0:      self.set_releaseyear(text.unescape_XML(item_year[0]))
        if len(item_genre) > 0:     self.set_genre(text.unescape_XML(item_genre[0]))
        if len(item_developer) > 0: self.set_developer(text.unescape_XML(item_developer[0]))
        if len(item_rating) > 0:    self.set_rating(text.unescape_XML(item_rating[0]))
        if len(item_plot) > 0:      self.set_plot(text.unescape_XML(item_plot[0]))

        logger.debug("ROMCollection.import_NFO_file() Imported '{0}'".format(nfo_FileName.getPath()))

        return True
    
    def export_to_NFO_file(self, nfo_FileName: io.FileName):
        # --- Get NFO file name ---
        logger.debug('ROMCollection.export_to_NFO_file() Exporting launcher NFO "{0}"'.format(nfo_FileName.getPath()))

        # If NFO file does not exist then create them. If it exists, overwrite.
        nfo_content = []
        nfo_content.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        nfo_content.append('<!-- Exported by AKL on {0} -->\n'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
        nfo_content.append('<romcollection>\n')
        nfo_content.append(text.XML_line('year',      self.get_releaseyear()))
        nfo_content.append(text.XML_line('genre',     self.get_genre())) 
        nfo_content.append(text.XML_line('developer', self.get_developer()))
        nfo_content.append(text.XML_line('rating',    self.get_rating()))
        nfo_content.append(text.XML_line('plot',      self.get_plot()))
        
        nfo_content.append('</romcollection>\n')
        full_string = ''.join(nfo_content)
        nfo_FileName.writeAll(full_string)
            
    def export_to_file(self, file: io.FileName):
        logger.debug('ROMCollection.export_to_file() ROMCollection "{0}" (ID "{1}")'.format(self.get_name(), self.get_id()))

        # --- Create list of strings ---
        str_list = []
        str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        str_list.append('<!-- Exported by AKL on {0} -->\n'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
        str_list.append('<advanced_emulator_launcher_configuration>\n')
        str_list.append('<romcollection>\n')
        str_list.append(text.XML_line('name', self.get_name()))
        str_list.append(text.XML_line('year', self.get_releaseyear()))
        str_list.append(text.XML_line('genre', self.get_genre()))
        str_list.append(text.XML_line('developer', self.get_developer()))
        str_list.append(text.XML_line('rating', self.get_rating()))
        str_list.append(text.XML_line('plot', self.get_plot()))
        #str_list.append(text.XML_line('Asset_Prefix', self.get_custom_attribute('Asset_Prefix')))
        str_list.append(text.XML_line('s_icon', self.get_asset_str(asset_id=constants.ASSET_ICON_ID)))
        str_list.append(text.XML_line('s_fanart', self.get_asset_str(asset_id=constants.ASSET_FANART_ID)))
        str_list.append(text.XML_line('s_banner', self.get_asset_str(asset_id=constants.ASSET_BANNER_ID)))
        str_list.append(text.XML_line('s_poster', self.get_asset_str(asset_id=constants.ASSET_POSTER_ID)))
        str_list.append(text.XML_line('s_controller', self.get_asset_str(asset_id=constants.ASSET_CONTROLLER_ID)))
        str_list.append(text.XML_line('s_clearlogo', self.get_asset_str(asset_id=constants.ASSET_CLEARLOGO_ID)))
        str_list.append(text.XML_line('s_trailer', self.get_trailer()))
        str_list.append('</romcollection>\n')
        str_list.append('</advanced_emulator_launcher_configuration>\n')
        
        full_string = ''.join(str_list)
        file.writeAll(full_string)
            
    def __str__(self):
        return super().__str__()
     
class VirtualCollection(ROMCollection):
    def __init__(self, 
                entity_data: dict = None, 
                assets_data: typing.List[Asset] = None):
        # Concrete classes are responsible of creating a default entity_data dictionary
        # with sensible defaults.
        if entity_data is None:
            entity_data = _get_default_ROMCollection_data_model()
            entity_data['id'] = text.misc_generate_random_SID()
            
        super(VirtualCollection, self).__init__(entity_data, assets_data)

    def get_object_name(self):
        return 'Virtual Collection'
    
    def get_assets_kind(self):
        return constants.KIND_ASSET_COLLECTION
    
    def get_type(self):
        return constants.OBJ_COLLECTION_VIRTUAL
        
    def get_asset_ids_list(self):
        return constants.COLLECTION_ASSET_ID_LIST

    def get_mappable_asset_ids_list(self):
        return constants.MAPPABLE_LAUNCHER_ASSET_ID_LIST
    
    def get_collection_value(self) -> str:
        return self.entity_data['collection_value'] if 'collection_value' in self.entity_data else None
  
# -------------------------------------------------------------------------------------------------
# Class representing a ROM file you can play through AKL.
# -------------------------------------------------------------------------------------------------
class ROM(MetaDataItemABC):
        
    def __init__(self, 
                 rom_data: dict = None,
                 tag_data: dict = None, 
                 assets_data: typing.List[Asset] = None,
                 asset_paths_data: typing.List[AssetPath] = None,
                 scanned_data: dict = {},
                 launchers_data: typing.List[ROMLauncherAddon] = []):
        if rom_data is None:
            rom_data = _get_default_ROM_data_model()
            rom_data['id'] = text.misc_generate_random_SID()
        
        self.tags = tag_data
        self.scanned_data = scanned_data
        self.launchers_data = launchers_data

        if self.tags is None and 'rom_tags' in rom_data:
            tag_data_str = str(rom_data['rom_tags'])
            self.tags = {t: '' for t in tag_data_str.split(',')}
        
        super(ROM, self).__init__(rom_data, assets_data, asset_paths_data)
        
    def get_object_name(self): return 'ROM'

    def get_assets_kind(self):
        return constants.KIND_ASSET_ROM
    
    def get_type(self): return constants.OBJ_ROM
      
    def get_rom_identifier(self) -> str:
        identifier = self.get_scanned_data_element('identifier')
        name = self.get_name()
        
        if identifier:
            return identifier
        if name:
            return name
        
        return f'ROM_{self.get_id()}'
          
    # inherited value from ROMCollection
    def get_platform(self):
        return self.entity_data['platform'] if 'platform' in self.entity_data else None
    
    def get_nointro_status(self):
        return self.entity_data['nointro_status'] if 'nointro_status' in self.entity_data else ''

    def get_pclone_status(self):
        return self.entity_data['pclone_status'] if 'pclone_status' in self.entity_data else ''

    def get_clone(self):
        return self.entity_data['cloneof']
    
    def has_multiple_disks(self):
        return 'disks' in self.entity_data and self.entity_data['disks']

    def get_disks(self):
        if not self.has_multiple_disks():
            return []

        return self.entity_data['disks']
    
    def get_extra_ROM(self):
        return self.entity_data['i_extra_ROM']

    def set_as_extra_ROM(self):
        self.entity_data['i_extra_ROM'] = True

    def get_nfo_file(self):
        ROM_FileName = self.get_scanned_data_element_as_file('file')
        if ROM_FileName:
            nfo_file_path = ROM_FileName.changeExtension('.nfo')            
            return nfo_file_path
        
        return None

    def get_number_of_players(self):
        return self.entity_data['m_nplayers']

    def get_number_of_players_online(self):
        return self.entity_data['m_nplayers_online']

    def get_esrb_rating(self):
        return self.entity_data['m_esrb']

    def get_pegi_rating(self):
        return self.entity_data['m_pegi']
    
    def get_rom_status(self):
        return self.entity_data['rom_status'] if 'rom_status' in self.entity_data else None

    def is_favourite(self) -> bool:
        return self.entity_data['is_favourite'] if 'is_favourite' in self.entity_data else False
    
    def get_tags(self) -> typing.List[str]:
        if self.tags is not None:
            return [tag for tag in list(self.tags.keys()) if tag is not None]
        return []

    def get_tag_data(self) -> dict:
        if self.tags is None:
            self.tags = {}
        return self.tags

    def get_launch_count(self):
        return self.entity_data['launch_count'] if 'launch_count' in self.entity_data else 0

    def get_last_launch_date(self):
        return self.entity_data['last_launch_timestamp'] if 'last_launch_timestamp' in self.entity_data else None

    def get_scanned_with(self) -> str:
        return self.entity_data['scanned_by_id'] if 'scanned_by_id' in self.entity_data else None

    def add_disk(self, disk):
        if not 'disks' in self.entity_data or self.entity_data['disks'] is None:
            self.entity_data['disks'] = []
            
        disks:list = self.entity_data['disks']
        disks.append(disk)
        self.entity_data['disks'] = disks

    def set_number_of_players(self, amount):
        self.entity_data['m_nplayers'] = amount

    def set_number_of_players_online(self, amount):
        self.entity_data['m_nplayers_online'] = amount

    def set_esrb_rating(self, esrb):
        self.entity_data['m_esrb'] = esrb

    def set_pegi_rating(self, pegi):
        self.entity_data['m_pegi'] = pegi
        
    def set_platform(self, platform): 
        self.entity_data['platform'] = platform
    
    def add_tag(self, tag:str):
        if self.tags is None:
            self.tags = {}
        if tag in self.tags:
            return
        self.tags[tag] = ''

    def remove_tag(self, tag:str):
        if self.tags is None: return
        if not tag in self.tags: return
        del self.tags[tag]

    def clear_tags(self):
        self.tags = {}

    def set_nointro_status(self, status):
        self.entity_data['nointro_status'] = status

    def set_pclone_status(self, status):
        self.entity_data['pclone_status'] = status

    def set_clone(self, clone):
        self.entity_data['cloneof'] = clone

    def scanned_with(self, scanner_id: str): 
        self.entity_data['scanned_by_id'] = scanner_id
        
    def get_scanned_data(self):
        return self.scanned_data

    def get_scanned_data_element(self, key:str):
        return self.scanned_data[key] if key in self.scanned_data else None
    
    def get_scanned_data_element_as_file(self, key:str) -> io.FileName:
        scanned_value = self.scanned_data[key] if key in self.scanned_data else None
        return self._to_filename(scanned_value)
    
    def set_scanned_data_element(self, key:str, data):
        self.scanned_data[key] = data
    
    def set_rom_status(self, state):
        self.entity_data['rom_status'] = state

    def add_to_favourites(self):
        self.entity_data['is_favourite'] = True

    def increase_launch_count(self):
        launch_count = self.entity_data['launch_count'] if 'launch_count' in self.entity_data else 0
        launch_count += 1
        self.entity_data['launch_count'] = launch_count
        self.entity_data['last_launch_timestamp'] = datetime.datetime.now()

    def get_box_sizing(self):
        return self.entity_data['box_size'] if 'box_size' in self.entity_data else constants.BOX_SIZE_POSTER
    
    def set_box_sizing(self, box_size):
        self.entity_data['box_size'] = box_size

    def has_launchers(self) -> bool:
        return len(self.launchers_data) > 0

    def add_launcher(self, addon: AelAddon, settings: dict, is_non_blocking = True, is_default: bool = False):
        launcher = ROMLauncherAddonFactory.create(addon, { 
            'settings': json.dumps(settings),
            'is_non_blocking': is_non_blocking,
            'is_default': is_default
        })        
        if is_default:
            current_default_launcher = next((l for l in self.launchers_data if l.is_default()), None)
            if current_default_launcher: current_default_launcher.set_default(False)
            
        self.launchers_data.append(launcher)
        logger.debug(f'Adding addon "{addon.get_addon_id()}" to ROM "{self.get_name()}"')

    def get_launchers(self) -> typing.List[ROMLauncherAddon]:
        return self.launchers_data

    def get_launcher(self, id:str) -> ROMLauncherAddon:
        return next((l for l in self.launchers_data if l.get_id() == id), None)

    def get_default_launcher(self) -> ROMLauncherAddon:
        if len(self.launchers_data) == 0: return None
        default_launcher = next((l for l in self.launchers_data if l.is_default()), None)
        if default_launcher is None: return self.launchers_data[0]
        
        return default_launcher

    def set_launcher_as_default(self, launcher_id):
        if len(self.launchers_data) == 0: return
        
        current_default_launcher = next((l for l in self.launchers_data if l.is_default()), None)
        if current_default_launcher: current_default_launcher.set_default(False)
        
        launcher_to_be_default = next((l for l in self.launchers_data if l.get_id() == launcher_id), None)
        if launcher_to_be_default:
            launcher_to_be_default.set_default(True)
            
    def copy(self):
        data = self.copy_of_data_dic()
        return ROM(data)
	
    def get_asset_ids_list(self):
        return constants.ROM_ASSET_ID_LIST
    
    def get_mappable_asset_ids_list(self): return constants.MAPPABLE_ROM_ASSET_ID_LIST
    
    def get_default_icon(self) -> str: return 'DefaultProgram.png'    
    
    def create_dto(self) -> api.ROMObj:
        dto_data:dict = api.ROMObj.get_data_template()
        for key in list(dto_data.keys()):
            if key in self.entity_data: dto_data[key] = self.entity_data[key]

        dto_data['tags'] = self.get_tags()

        for asset_id in self.get_asset_ids_list():
            asset_info = g_assetFactory.get_asset_info(asset_id)
            asset = self.get_asset(asset_id)
            asset_path = self.get_asset_path(asset_info)
            
            dto_data['asset_paths'][asset_id] = asset_path.getPath() if asset_path is not None else None
            dto_data['assets'][asset_id] = asset.get_path() if asset is not None else None
            dto_data['scanned_data'] = self.scanned_data
            
        return api.ROMObj(dto_data)
    
    #
    # Reads an NFO file with ROM information.
    # See comments in fs_export_ROM_NFO() about verbosity.
    # About reading files in Unicode http://stackoverflow.com/questions/147741/character-reading-from-file-in-python
    #
    # todo: Replace with nfo_file_path.readXml() and just use XPath
    def update_with_nfo_file(self, nfo_file_path:io.FileName, verbose = True):
        logger.debug('Rom.update_with_nfo_file() Loading "{0}"'.format(nfo_file_path.getPath()))
        if not nfo_file_path.exists():
            if verbose:
                kodi.notify_warn('NFO file not found {0}'.format(nfo_file_path.getPath()))
            logger.debug("Rom.update_with_nfo_file() NFO file not found '{0}'".format(nfo_file_path.getPath()))
            return False

        # todo: Replace with nfo_file_path.readXml() and just use XPath

        # --- Import data ---
        # >> Read file, put in a string and remove line endings.
        # >> We assume NFO files are UTF-8. Decode data to Unicode.
        # file = open(nfo_file_path, 'rt')
        nfo_str = nfo_file_path.loadFileToStr()
        nfo_str = nfo_str.replace('\r', '').replace('\n', '')

        # Search for metadata tags. Regular expression is non-greedy.
        # See https://docs.python.org/2/library/re.html#re.findall
        # If RE has no groups it returns a list of strings with the matches.
        # If RE has groups then it returns a list of groups.
        item_title     = re.findall('<title>(.*?)</title>', nfo_str)
        item_year      = re.findall('<year>(.*?)</year>', nfo_str)
        item_genre     = re.findall('<genre>(.*?)</genre>', nfo_str)
        item_developer = re.findall('<developer>(.*?)</developer>', nfo_str)
        item_nplayers  = re.findall('<nplayers>(.*?)</nplayers>', nfo_str)
        item_esrb      = re.findall('<esrb>(.*?)</esrb>', nfo_str)
        item_pegi      = re.findall('<pegi>(.*?)</pegi>', nfo_str)
        item_rating    = re.findall('<rating>(.*?)</rating>', nfo_str)
        item_plot      = re.findall('<plot>(.*?)</plot>', nfo_str)
        item_trailer   = re.findall('<trailer>(.*?)</trailer>', nfo_str)

        # >> Future work: ESRB and maybe nplayer fields must be sanitized.
        if len(item_title) > 0:     self.set_name(text.unescape_XML(item_title[0]))
        if len(item_year) > 0:      self.set_releaseyear(text.unescape_XML(item_year[0]))
        if len(item_genre) > 0:     self.set_genre(text.unescape_XML(item_genre[0]))
        if len(item_developer) > 0: self.set_developer(text.unescape_XML(item_developer[0]))
        if len(item_rating) > 0:    self.set_rating(text.unescape_XML(item_rating[0]))
        if len(item_plot) > 0:      self.set_plot(text.unescape_XML(item_plot[0]))
        if len(item_nplayers) > 0:  self.set_number_of_players(text.unescape_XML(item_nplayers[0]))
        if len(item_esrb) > 0:      self.set_esrb_rating(text.unescape_XML(item_esrb[0]))
        if len(item_pegi) > 0:      self.set_pegi_rating(text.unescape_XML(item_pegi[0]))
        if len(item_trailer) > 0:   self.set_trailer(text.unescape_XML(item_trailer[0]))

        if verbose:
            kodi.notify('Imported {0}'.format(nfo_file_path.getPath()))

        return True
        
    def export_to_NFO_file(self, nfo_FileName: io.FileName):
        # --- Get NFO file name ---
        logger.debug('ROM.export_to_NFO_file() Exporting ROM NFO "{0}"'.format(nfo_FileName.getPath()))

        # If NFO file does not exist then create them. If it exists, overwrite.
        nfo_content = []
        nfo_content.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        nfo_content.append('<!-- Exported by AKL on {0} -->\n'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
        nfo_content.append('<ROM>\n')
        nfo_content.append(text.XML_line('title',     self.get_name()))
        nfo_content.append(text.XML_line('year',      self.get_releaseyear()))
        nfo_content.append(text.XML_line('genre',     self.get_genre())) 
        nfo_content.append(text.XML_line('developer', self.get_developer()))
        nfo_content.append(text.XML_line('nplayers',  self.get_number_of_players()))
        nfo_content.append(text.XML_line('esrb',      self.get_esrb_rating()))
        nfo_content.append(text.XML_line('pegi',      self.get_pegi_rating()))
        nfo_content.append(text.XML_line('rating',    self.get_rating()))
        nfo_content.append(text.XML_line('plot',      self.get_plot()))
        nfo_content.append(text.XML_line('trailer',   self.get_trailer()))
        
        nfo_content.append('</ROM>\n')
        full_string = ''.join(nfo_content)
        nfo_FileName.writeAll(full_string)
    
    # 
    # Updates an ROM entity with the API object given.
    # Flags indicate which elements are allowed to be updated/altered with the incoming data.
    #
    def update_with(self, 
        api_rom_obj: api.ROMObj, 
        metadata_to_update=[], 
        assets_to_update=[], 
        overwrite_existing_metadata=False,
        overwrite_existing_assets=False,
        update_scanned_data=False):

        logger.debug(f"Overwriting existing metadata in domain: {overwrite_existing_metadata}")
        logger.debug(f"Overwriting existing assets in domain: {overwrite_existing_assets}")

        if constants.META_TITLE_ID in metadata_to_update \
            and api_rom_obj.get_name() \
            and (overwrite_existing_metadata or \
                _is_empty_or_default(self.get_name(), constants.DEFAULT_META_TITLE)): 
            self.set_name(api_rom_obj.get_name())

        if constants.META_PLOT_ID in metadata_to_update \
            and api_rom_obj.get_plot() \
            and (overwrite_existing_metadata or \
                _is_empty_or_default(self.get_plot(), constants.DEFAULT_META_PLOT)):              
            self.set_plot(api_rom_obj.get_plot())
    
        if constants.META_YEAR_ID in metadata_to_update \
            and api_rom_obj.get_releaseyear() \
            and (overwrite_existing_metadata or \
                _is_empty_or_default(self.get_releaseyear(), constants.DEFAULT_META_YEAR)):       
            self.set_releaseyear(api_rom_obj.get_releaseyear())
        
        if constants.META_GENRE_ID in metadata_to_update \
            and api_rom_obj.get_genre() \
            and (overwrite_existing_metadata or \
                _is_empty_or_default(self.get_genre(), constants.DEFAULT_META_GENRE)):
            self.set_genre(api_rom_obj.get_genre())
        
        if constants.META_DEVELOPER_ID in metadata_to_update \
            and api_rom_obj.get_developer() \
            and (overwrite_existing_metadata or \
                _is_empty_or_default(self.get_developer(), constants.DEFAULT_META_DEVELOPER)):         
            self.set_developer(api_rom_obj.get_developer())
        
        if constants.META_NPLAYERS_ID in metadata_to_update \
            and api_rom_obj.get_number_of_players() \
            and (overwrite_existing_metadata or \
                _is_empty_or_default(self.get_number_of_players(), constants.DEFAULT_META_NPLAYERS)):
            self.set_number_of_players(api_rom_obj.get_number_of_players())
        
        if constants.META_NPLAYERS_ONLINE_ID in metadata_to_update \
            and api_rom_obj.get_number_of_players_online() \
            and (overwrite_existing_metadata or \
                _is_empty_or_default(self.get_number_of_players_online(), constants.DEFAULT_META_NPLAYERS)):
            self.set_number_of_players_online(api_rom_obj.get_number_of_players_online())
        
        if constants.META_ESRB_ID in metadata_to_update\
                and api_rom_obj.get_esrb_rating() \
                and (overwrite_existing_metadata or \
                    _is_empty_or_default(self.get_esrb_rating(), constants.DEFAULT_META_ESRB)):
            self.set_esrb_rating(api_rom_obj.get_esrb_rating())
        
        if constants.META_PEGI_ID in metadata_to_update\
                and api_rom_obj.get_pegi_rating() \
                and (overwrite_existing_metadata or \
                    _is_empty_or_default(self.get_pegi_rating(), constants.DEFAULT_META_PEGI)):       
            self.set_pegi_rating(api_rom_obj.get_pegi_rating())
        
        if constants.META_RATING_ID in metadata_to_update \
                and api_rom_obj.get_rating() \
                and (overwrite_existing_metadata or \
                    _is_empty_or_default(self.get_rating(), constants.DEFAULT_META_RATING)):            
            self.set_rating(api_rom_obj.get_rating())
        
        if constants.META_TAGS_ID in metadata_to_update and api_rom_obj.get_tags() is not None:
            for tag in api_rom_obj.get_tags():
                self.add_tag(tag)
                    
        if len(assets_to_update) > 0:
            for asset_id in assets_to_update:
                existing_asset = self.get_asset(asset_id)
                new_asset = api_rom_obj.get_asset(asset_id)
                if new_asset is not None and \
                    (overwrite_existing_assets or existing_asset is None or not existing_asset.is_assigned()):
                    if asset_id == constants.ASSET_TRAILER_ID:
                        self.set_trailer(new_asset)
                    else:
                        asset_info = g_assetFactory.get_asset_info(asset_id)
                        asset_path = io.FileName(new_asset)
                        self.set_asset(asset_info, asset_path)
        
        if update_scanned_data:
            scanned_name = api_rom_obj.get_name()
            scanned_data = api_rom_obj.get_scanned_data()
            
            if scanned_name:
                self.set_name(scanned_name)
            for scanned_entry in list(scanned_data.keys()):
                self.set_scanned_data_element(scanned_entry, scanned_data[scanned_entry])
                
            # if 'romcollection' in launcher_settings \
            # and kodi.dialog_yesno('Do you want to overwrite collection metadata properties with values from the launcher?'):
            # romcollection.import_data_dic(launcher_settings['romcollection'])
            # metadata_updated = True
            
    
    def apply_romcollection_asset_paths(self, romcollection: ROMCollection):
        self.set_assets_root_path(romcollection.get_assets_root_path())
        self.asset_paths = {}
        for assetpath in romcollection.get_asset_paths():
            self.asset_paths[assetpath.get_asset_info_id()] = assetpath
            
    def apply_romcollection_asset_mapping(self, romcollection: ROMCollection):
        mappable_assets = romcollection.get_ROM_mappable_asset_list()
        for mappable_asset in mappable_assets:
            mapped_asset = romcollection.get_mapped_ROM_asset_info(mappable_asset)
            self.set_mapped_asset_key(mappable_asset, mapped_asset)
        
    def __str__(self):
        """Overrides the default implementation"""
        return json.dumps(self.entity_data)

# -------------------------------------------------------------------------------------------------
# OBJECT FACTORIES
# -------------------------------------------------------------------------------------------------
#
# Class to interact with the asset engine.
# This class uses the asset_infos, dictionary of AssetInfo indexed by asset_ID
#
class AssetInfoFactory(object):
        
    def __init__(self):        
        # default collections
        self.ASSET_INFO_ID_DICT:typing.Dict[str,AssetInfo] = {} # ID -> object        
        self._load_asset_data()
        
    # -------------------------------------------------------------------------------------------------
    # Asset functions
    # -------------------------------------------------------------------------------------------------
    def get_all(self) -> typing.List[AssetInfo]:
        return list(self.ASSET_INFO_ID_DICT.values())

    def get_asset_info(self, asset_ID) -> AssetInfo:
        asset_info = self.ASSET_INFO_ID_DICT.get(asset_ID, None)

        if asset_info is None:
            logger.error('get_asset_info() Wrong asset_ID = {0}'.format(asset_ID))
            return AssetInfo()

        return asset_info
    
    # Returns the corresponding assetinfo object for the
    # given key (eg: 's_icon')
    def get_asset_info_by_key(self, asset_key):
        asset_info = next((a for a in list(self.ASSET_INFO_ID_DICT.values()) if a.key == asset_key), None)

        if asset_info is None:
            logger.error('get_asset_info_by_key() Wrong asset_key = {0}'.format(asset_key))
            return AssetInfo()

        return asset_info 
             
    # Returns the corresponding assetinfo object for the
    # given path key (eg: 'path_icon')
    def get_asset_info_by_pathkey(self, path_key):
        asset_info = next((a for a in list(self.ASSET_INFO_ID_DICT.values()) if a.path_key == path_key), None)

        if asset_info is None:
            logger.error('get_asset_info_by_pathkey() Wrong path key = {0}'.format(path_key))
            return None

        return asset_info
    
    def get_assets_for_type(self, asset_kind) -> typing.List[AssetInfo]:
        if asset_kind == constants.KIND_ASSET_CATEGORY:
            return self.get_asset_list_by_IDs(constants.CATEGORY_ASSET_ID_LIST)
        if asset_kind == constants.KIND_ASSET_COLLECTION:
            return self.get_asset_list_by_IDs(constants.COLLECTION_ASSET_ID_LIST)
        if asset_kind == constants.KIND_ASSET_LAUNCHER:
            return self.get_asset_list_by_IDs(constants.LAUNCHER_ASSET_ID_LIST)
        if asset_kind == constants.KIND_ASSET_ROM:
            return self.get_asset_list_by_IDs(constants.ROM_ASSET_ID_LIST)
        return []

    def get_asset_kinds_for_roms(self) -> typing.List[AssetInfo]:
        rom_asset_kinds = []
        for rom_asset_id in constants.ROM_ASSET_ID_LIST:
            rom_asset_kinds.append(self.ASSET_INFO_ID_DICT[rom_asset_id])

        return rom_asset_kinds

    # IDs is a list (or an iterable that returns an asset ID
    # Returns a list of AssetInfo objects.
    # If the asset kind is given, it will filter out assets not corresponding to that kind.
    def get_asset_list_by_IDs(self, IDs, kind = None) -> typing.List[AssetInfo]:
        asset_info_list = []
        for asset_ID in IDs:
            asset_info = self.ASSET_INFO_ID_DICT.get(asset_ID, None)
            if asset_info is None:
                logger.error('get_asset_list_by_IDs() Wrong asset_ID = {0}'.format(asset_ID))
                continue
            if kind is None or asset_info.kind_str == kind: asset_info_list.append(asset_info)

        return asset_info_list
  
    # todo: use 1 type of identifier not number constants and name strings ('s_icon')
    def get_asset_info_by_namekey(self, name_key):
        if name_key == '': return None
        kind = constants.ASSET_KEYS_TO_CONSTANTS[name_key]

        return self.get_asset_info(kind)
    #
    # Get extensions to search for files
    # Input : ['png', 'jpg']
    # Output: ['png', 'jpg', 'PNG', 'JPG']
    #
    def asset_get_filesearch_extension_list(self, exts):
        ext_list = list(exts)
        for ext in exts:
            ext_list.append(ext.upper())

        return ext_list

    #
    # Gets extensions to be used in Kodi file dialog.
    # Input : ['png', 'jpg']
    # Output: '.png|.jpg'
    #
    def asset_get_dialog_extension_list(self, exts) -> str:
        ext_string = ''
        for ext in exts:
            ext_string += '.' + ext + '|'
        # >> Remove trailing '|' character
        ext_string = ext_string[:-1]

        return ext_string

    #
    # Scheme SUFIX uses suffixes for artwork. All artwork assets are stored in the same directory.
    # Name example: "Sonic The Hedgehog (Europe)_a3e_title"
    # First 3 characters of the objectID are added to avoid overwriting of images. For example, in the
    # Favourites special category there could be ROMs with the same name for different systems.
    #
    # asset_ID         -> Assets ID defined in constants.py
    # AssetPath        -> FileName object
    # asset_base_noext -> Unicode string
    # objectID         -> Object MD5 ID fingerprint (Unicode string)
    #
    # Returns a FileName object
    #
    def assets_get_path_noext_SUFIX(self, asset_ID, AssetPath, asset_base_noext, objectID = '000'):
        objectID_str = '_' + objectID[0:3]

        if   asset_ID == constants.ASSET_ICON_ID:       asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_icon')
        elif asset_ID == constants.ASSET_FANART_ID:     asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_fanart')
        elif asset_ID == constants.ASSET_BANNER_ID:     asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_banner')
        elif asset_ID == constants.ASSET_POSTER_ID:     asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_poster')
        elif asset_ID == constants.ASSET_CLEARLOGO_ID:  asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_clearlogo')
        elif asset_ID == constants.ASSET_CONTROLLER_ID: asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_controller')
        elif asset_ID == constants.ASSET_TRAILER_ID:    asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_trailer')
        elif asset_ID == constants.ASSET_TITLE_ID:      asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_title')
        elif asset_ID == constants.ASSET_SNAP_ID:       asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_snap')
        elif asset_ID == constants.ASSET_BOXFRONT_ID:   asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_boxfront')
        elif asset_ID == constants.ASSET_BOXBACK_ID:    asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_boxback')
        elif asset_ID == constants.ASSET_CARTRIDGE_ID:  asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_cartridge')
        elif asset_ID == constants.ASSET_FLYER_ID:      asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_flyer')
        elif asset_ID == constants.ASSET_MAP_ID:        asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_map')
        elif asset_ID == constants.ASSET_MANUAL_ID:     asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_manual')
        else:
            asset_path_noext_FN = io.FileName('')
            logger.error('assets_get_path_noext_SUFIX() Wrong asset_ID = {0}'.format(asset_ID))

        return asset_path_noext_FN

    #
    # Search for local assets and put found files into a list.
    # This function is used in _roms_add_new_rom() where there is no need for a file cache.
    #
    def assets_search_local_assets(self, launcher, ROMFile, enabled_ROM_asset_list):
        logger.debug('assets_search_local_assets() Searching for ROM local assets...')
        local_asset_list = [''] * len(constants.ROM_ASSET_ID_LIST)
        for i, asset_kind in enumerate(constants.ROM_ASSET_ID_LIST):
            AInfo = g_assetFactory.get_asset_info(asset_kind)
            if not enabled_ROM_asset_list[i]:
                logger.debug('assets_search_local_assets() Disabled {0:<9}'.format(AInfo.name))
                continue
            asset_path = launcher.get_asset_path(AInfo)
            local_asset = io.misc_look_for_file(asset_path, ROMFile.getBaseNoExt(), AInfo.exts)

            if local_asset:
                local_asset_list[i] = local_asset.getPath()
                logger.debug('assets_search_local_assets() Found    {0:<9} "{1}"'.format(AInfo.name, local_asset_list[i]))
            else:
                local_asset_list[i] = ''
                logger.debug('assets_search_local_assets() Missing  {0:<9}'.format(AInfo.name))

        return local_asset_list

    #
    # A) This function checks if all path_* share a common root directory. If so
    #    this function returns that common directory as an Unicode string.
    # B) If path_* do not share a common root directory this function returns ''.
    #
    def assets_get_ROM_asset_path(self, launcher):
        ROM_asset_path = ''
        duplicated_bool_list = [False] * len(constants.ROM_ASSET_ID_LIST)
        AInfo_first = g_assetFactory.get_asset_info(constants.ROM_ASSET_ID_LIST[0])
        path_first_asset_FN = io.FileName(launcher[AInfo_first.path_key])
        logger.debug('assets_get_ROM_asset_path() path_first_asset "{0}"'.format(path_first_asset_FN.getPath()))
        for i, asset_kind in enumerate(constants.ROM_ASSET_ID_LIST):
            AInfo = g_assetFactory.get_asset_info(asset_kind)
            current_path_FN = io.FileName(launcher[AInfo.path_key])
            if current_path_FN.getDir() == path_first_asset_FN.getDir():
                duplicated_bool_list[i] = True

        return path_first_asset_FN.getDir() if all(duplicated_bool_list) else ''

    #
    # Gets extensions to be used in regular expressions.
    # Input : ['png', 'jpg']
    # Output: '(png|jpg)'
    #
    @staticmethod
    def asset_get_regexp_extension_list(exts):
        ext_string = ''
        for ext in exts:
            ext_string += ext + '|'
        # >> Remove trailing '|' character
        ext_string = ext_string[:-1]

        return '(' + ext_string + ')'
    
    #
    # This must match the order of the list Category_asset_ListItem_list in _command_edit_category()
    # TODO: deprecated?
    @staticmethod
    def assets_choose_Category_mapped_artwork(dict_object, key, index):
        if   index == 0: dict_object[key] = 's_icon'
        elif index == 1: dict_object[key] = 's_fanart'
        elif index == 2: dict_object[key] = 's_banner'
        elif index == 3: dict_object[key] = 's_poster'
        elif index == 4: dict_object[key] = 's_clearlogo'

    #
    # This must match the order of the list Category_asset_ListItem_list in _command_edit_category()
    # TODO: deprecated?
    @staticmethod
    def assets_get_Category_mapped_asset_idx(dict_object, key):
        if   dict_object[key] == 's_icon':       index = 0
        elif dict_object[key] == 's_fanart':     index = 1
        elif dict_object[key] == 's_banner':     index = 2
        elif dict_object[key] == 's_poster':     index = 3
        elif dict_object[key] == 's_clearlogo':  index = 4
        else:                                    index = 0

        return index

    #
    # This must match the order of the list Launcher_asset_ListItem_list in _command_edit_launcher()
    # TODO: deprecated?
    @staticmethod
    def assets_choose_Launcher_mapped_artwork(dict_object, key, index):
        if   index == 0: dict_object[key] = 's_icon'
        elif index == 1: dict_object[key] = 's_fanart'
        elif index == 2: dict_object[key] = 's_banner'
        elif index == 3: dict_object[key] = 's_poster'
        elif index == 4: dict_object[key] = 's_clearlogo'
        elif index == 5: dict_object[key] = 's_controller'

    #
    # This must match the order of the list Launcher_asset_ListItem_list in _command_edit_launcher()
    # TODO: deprecated?
    @staticmethod
    def assets_get_Launcher_mapped_asset_idx(dict_object, key):
        if   dict_object[key] == 's_icon':       index = 0
        elif dict_object[key] == 's_fanart':     index = 1
        elif dict_object[key] == 's_banner':     index = 2
        elif dict_object[key] == 's_poster':     index = 3
        elif dict_object[key] == 's_clearlogo':  index = 4
        elif dict_object[key] == 's_controller': index = 5
        else:                                    index = 0

        return index

    # since we are using a single instance for the assetinfo factory we can automatically load
    # all the asset objects into the memory
    def _load_asset_data(self): 
                
        # >> These are used very frequently so I think it is better to have a cached list.
        a = AssetInfo()
        a.id                            = constants.ASSET_ICON_ID
        a.key                           = 's_icon'
        a.default_key                   = 'default_icon'
        a.rom_default_key               = 'roms_default_icon'
        a.name                          = 'Icon'
        a.plural                        = 'Icons'
        a.fname_infix                   = 'icon'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_icon'        
        self.ASSET_INFO_ID_DICT[a.id]   = a

        a = AssetInfo()
        a.id                            = constants.ASSET_FANART_ID
        a.key                           = 's_fanart'
        a.default_key                   = 'default_fanart'
        a.rom_default_key               = 'roms_default_fanart'
        a.name                          = 'Fanart'
        a.plural                        = 'Fanarts'
        a.fname_infix                   = 'fanart'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_fanart'
        self.ASSET_INFO_ID_DICT[a.id]   = a

        a = AssetInfo()
        a.id                            = constants.ASSET_BANNER_ID
        a.key                           = 's_banner'
        a.default_key                   = 'default_banner'
        a.rom_default_key               = 'roms_default_banner'
        a.name                          = 'Banner'
        a.description                   = 'Banner / Marquee'
        a.plural                        = 'Banners'
        a.fname_infix                   = 'banner'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_banner'
        self.ASSET_INFO_ID_DICT[a.id]   = a

        a = AssetInfo()        
        a.id                            = constants.ASSET_POSTER_ID
        a.key                           = 's_poster'
        a.default_key                   = 'default_poster'
        a.rom_default_key               = 'roms_default_poster'
        a.name                          = 'Poster'
        a.plural                        = 'Posters'
        a.fname_infix                   = 'poster'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_poster'
        self.ASSET_INFO_ID_DICT[a.id]   = a

        a = AssetInfo()
        a.id                            = constants.ASSET_CLEARLOGO_ID
        a.key                           = 's_clearlogo'
        a.default_key                   = 'default_clearlogo'
        a.rom_default_key               = 'roms_default_clearlogo'
        a.name                          = 'Clearlogo'
        a.plural                        = 'Clearlogos'
        a.fname_infix                   = 'clearlogo'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_clearlogo'
        self.ASSET_INFO_ID_DICT[a.id]   = a

        a = AssetInfo()
        a.id                            = constants.ASSET_CONTROLLER_ID
        a.key                           = 's_controller'
        a.default_key                   = 'default_controller'
        a.name                          = 'Controller'
        a.plural                        = 'Controllers'
        a.fname_infix                   = 'controller'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_controller'
        self.ASSET_INFO_ID_DICT[a.id]   = a
        
        a = AssetInfo()
        a.id                            = constants.ASSET_TRAILER_ID
        a.key                           = 's_trailer'
        a.name                          = 'Trailer'
        a.plural                        = 'Trailers'
        a.fname_infix                   = 'trailer'
        a.kind_str                      = 'video'
        a.exts                          = self.asset_get_filesearch_extension_list(constants.TRAILER_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(constants.TRAILER_EXTENSION_LIST)
        a.path_key                      = 'path_trailer'
        self.ASSET_INFO_ID_DICT[a.id]   = a

        a = AssetInfo()
        a.id                            = constants.ASSET_TITLE_ID
        a.key                           = 's_title'
        a.default_key                   = 'default_title'
        a.rom_default_key               = 'roms_default_title'
        a.name                          = 'Title'
        a.plural                        = 'Titles'
        a.fname_infix                   = 'title'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_title'
        self.ASSET_INFO_ID_DICT[a.id]   = a

        a = AssetInfo()
        a.id                            = constants.ASSET_SNAP_ID
        a.key                           = 's_snap'
        a.name                          = 'Snap'
        a.plural                        = 'Snaps'
        a.fname_infix                   = 'snap'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_snap'
        self.ASSET_INFO_ID_DICT[a.id]   = a

        a = AssetInfo()
        a.id                            = constants.ASSET_BOXFRONT_ID
        a.key                           = 's_boxfront'
        a.name                          = 'Boxfront'
        a.description                   = 'Boxfront / Cabinet'
        a.plural                        = 'Boxfronts'
        a.fname_infix                   = 'boxfront'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_boxfront'
        self.ASSET_INFO_ID_DICT[a.id]   = a

        a = AssetInfo()
        a.id                            = constants.ASSET_BOXBACK_ID
        a.key                           = 's_boxback'
        a.name                          = 'Boxback'
        a.description                   = 'Boxback / CPanel'
        a.plural                        = 'Boxbacks'
        a.fname_infix                   = 'boxback'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_boxback'
        self.ASSET_INFO_ID_DICT[a.id]   = a

        a = AssetInfo()
        a.id                            = constants.ASSET_CARTRIDGE_ID
        a.key                           = 's_cartridge'
        a.name                          = 'Cartridge'
        a.description                   = 'Cartridge / PCB'
        a.plural                        = 'Cartridges'
        a.fname_infix                   = 'cartridge'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_cartridge'
        self.ASSET_INFO_ID_DICT[a.id]   = a

        a = AssetInfo()
        a.id                            = constants.ASSET_FLYER_ID
        a.key                           = 's_flyer'
        a.name                          = 'Flyer'
        a.plural                        = 'Flyers'
        a.fname_infix                   = 'flyer'
        a.kind_str                      = 'image'
        a.fname_infix                   = 'poster'
        a.exts                          = self.asset_get_filesearch_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_flyer'
        self.ASSET_INFO_ID_DICT[a.id]   = a

        a = AssetInfo()
        a.id                            = constants.ASSET_MAP_ID
        a.key                           = 's_map'
        a.name                          = 'Map'
        a.plural                        = 'Maps'
        a.fname_infix                   = 'map'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_map'
        self.ASSET_INFO_ID_DICT[a.id]   = a

        a = AssetInfo()
        a.id                            = constants.ASSET_MANUAL_ID
        a.key                           = 's_manual'
        a.name                          = 'Manual'
        a.plural                        = 'Manuals'
        a.fname_infix                   = 'manual'
        a.kind_str                      = 'manual'
        a.exts                          = self.asset_get_filesearch_extension_list(constants.MANUAL_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(constants.MANUAL_EXTENSION_LIST)
        a.path_key                      = 'path_manual'
        self.ASSET_INFO_ID_DICT[a.id]   = a

        a = AssetInfo()
        a.id                            = constants.ASSET_3DBOX_ID
        a.key                           = 's_3dbox'
        a.name                          = '3D Box'
        a.plural                        = '3D Boxes'
        a.fname_infix                   = '3dbox'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(constants.IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_3dbox'
        self.ASSET_INFO_ID_DICT[a.id]   = a

# --- Global object to get asset info ---
g_assetFactory = AssetInfoFactory()

# Factory class to create VirtualCollection instances.
# A VirtualCollection is similar to a ROMCollection except for the fact that the contents are
# generated based on either certain flags or conditions of the ROMs. 
class VirtualCollectionFactory(object):
    
    @staticmethod
    def create(vcollection_id: str) -> VirtualCollection:
        
        default_entity_data = _get_default_ROMCollection_data_model()        
        if vcollection_id == constants.VCOLLECTION_FAVOURITES_ID:
            return VirtualCollection(dict(default_entity_data, **{
                'id' : vcollection_id,
                'm_name' : '<Favourites>',
                'plot': 'Browse AKL Favourite ROMs',
                'finished': settings.getSettingAsBool('display_hide_favs')
            }), [
                Asset({'id' : '', 'asset_type' : constants.ASSET_FANART_ID, 'filepath' : globals.g_PATHS.FANART_FILE_PATH.getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_ICON_ID,   'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Favourites_icon.png').getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_POSTER_ID, 'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Favourites_poster.png').getPath()}),
            ])
            
        if vcollection_id == constants.VCOLLECTION_RECENT_ID:
            return VirtualCollection(dict(default_entity_data, **{
                'id' : vcollection_id,
                'm_name' : '[Recently played ROMs]',
                'plot': 'Browse the ROMs you played recently',
                'finished': settings.getSettingAsBool('display_hide_recent')
            }), [
                Asset({'id' : '', 'asset_type' : constants.ASSET_FANART_ID, 'filepath' : globals.g_PATHS.FANART_FILE_PATH.getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_ICON_ID,   'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Recently_played_icon.png').getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_POSTER_ID, 'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Recently_played_poster.png').getPath()}),
            ])
            
        if vcollection_id == constants.VCOLLECTION_MOST_PLAYED_ID:
            return VirtualCollection(dict(default_entity_data, **{
                'id' : vcollection_id,
                'm_name' : '[Most played ROMs]',
                'plot': 'Browse the ROMs you play most',
                'finished': settings.getSettingAsBool('display_hide_mostplayed')
            }), [
                Asset({'id' : '', 'asset_type' : constants.ASSET_FANART_ID, 'filepath' : globals.g_PATHS.FANART_FILE_PATH.getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_ICON_ID,   'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Most_played_icon.png').getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_POSTER_ID, 'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Most_played_poster.png').getPath()}),
            ])    
        
        return None

    @staticmethod
    def create_by_category(vcategory_id:str, collection_value:str) -> VirtualCollection:

        default_entity_data = _get_default_ROMCollection_data_model()    
        return VirtualCollection(dict(default_entity_data, **{
            'id' : f'{vcategory_id}_{collection_value}',
            'parent_id': vcategory_id,
            'm_name' : collection_value,
            'plot': f"Browse ROMs filtered on '{collection_value}'",
            'collection_value': collection_value,
            'finished': settings.getSettingAsBool('display_hide_vcategories')
        }), [
            Asset({'id' : '', 'asset_type' : constants.ASSET_FANART_ID, 'filepath' : globals.g_PATHS.FANART_FILE_PATH.getPath()})
        ])

class VirtualCategoryFactory(object):
    
    @staticmethod
    def create(vcategory_id: str) -> VirtualCategory:
        
        default_entity_data = _get_default_category_data_model()   
        if vcategory_id  == constants.VCATEGORY_ROOT_ID:
             return VirtualCategory(dict(default_entity_data, **{
                'id' : vcategory_id,
                'm_name' : 'Browse by...',
                'plot': 'Browse the ROMs by specifics',
                'finished': settings.getSettingAsBool('display_hide_vcategories')
            }), [
                Asset({'id' : '', 'asset_type' : constants.ASSET_FANART_ID, 'filepath' : globals.g_PATHS.FANART_FILE_PATH.getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_ICON_ID,   'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_icon.png').getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_POSTER_ID, 'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_poster.png').getPath()}),
            ])
            
        if vcategory_id == constants.VCATEGORY_TITLE_ID:
             return VirtualCategory(dict(default_entity_data, **{
                'id' : vcategory_id,
                'm_name' : 'Browse by Title',
                'plot': 'Browse the ROMs by title',
                'finished': settings.getSettingAsBool('display_hide_vcategories')
            }), [
                Asset({'id' : '', 'asset_type' : constants.ASSET_FANART_ID, 'filepath' : globals.g_PATHS.FANART_FILE_PATH.getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_ICON_ID,   'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_Title_icon.png').getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_POSTER_ID, 'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_Title_poster.png').getPath()}),
            ])
             
        if vcategory_id == constants.VCATEGORY_YEARS_ID:
             return VirtualCategory(dict(default_entity_data, **{
                'id' : vcategory_id,
                'm_name' : 'Browse by Year',
                'plot': 'Browse the ROMs by year',
                'finished': settings.getSettingAsBool('display_hide_vcategories')
            }), [
                Asset({'id' : '', 'asset_type' : constants.ASSET_FANART_ID, 'filepath' : globals.g_PATHS.FANART_FILE_PATH.getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_ICON_ID,   'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_Year_icon.png').getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_POSTER_ID, 'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_Year_poster.png').getPath()}),
            ])     
             
        if vcategory_id == constants.VCATEGORY_GENRE_ID:
             return VirtualCategory(dict(default_entity_data, **{
                'id' : vcategory_id,
                'm_name' : 'Browse by Genre',
                'plot': 'Browse the ROMs by genre',
                'finished': settings.getSettingAsBool('display_hide_vcategories')
            }), [
                Asset({'id' : '', 'asset_type' : constants.ASSET_FANART_ID, 'filepath' : globals.g_PATHS.FANART_FILE_PATH.getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_ICON_ID,   'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_Genre_icon.png').getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_POSTER_ID, 'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_Genre_poster.png').getPath()}),
            ])     
             
        if vcategory_id == constants.VCATEGORY_DEVELOPER_ID:
             return VirtualCategory(dict(default_entity_data, **{
                'id' : vcategory_id,
                'm_name' : 'Browse by Developer',
                'plot': 'Browse the ROMs by developer',
                'finished': settings.getSettingAsBool('display_hide_vcategories')
            }), [
                Asset({'id' : '', 'asset_type' : constants.ASSET_FANART_ID, 'filepath' : globals.g_PATHS.FANART_FILE_PATH.getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_ICON_ID,   'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_Developer_icon.png').getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_POSTER_ID, 'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_Developer_poster.png').getPath()}),
            ])     
             
        if vcategory_id == constants.VCATEGORY_NPLAYERS_ID:
             return VirtualCategory(dict(default_entity_data, **{
                'id' : vcategory_id,
                'm_name' : 'Browse by Number of Players',
                'plot': 'Browse the ROMs by number of players',
                'finished': settings.getSettingAsBool('display_hide_vcategories')
            }), [
                Asset({'id' : '', 'asset_type' : constants.ASSET_FANART_ID, 'filepath' : globals.g_PATHS.FANART_FILE_PATH.getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_ICON_ID,   'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_NPlayers_icon.png').getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_POSTER_ID, 'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_NPlayers_poster.png').getPath()}),
            ])    
                    
        if vcategory_id == constants.VCATEGORY_ESRB_ID:
             return VirtualCategory(dict(default_entity_data, **{
                'id' : vcategory_id,
                'm_name' : 'Browse by ESRB Rating',
                'plot': 'Browse the ROMs by ESRB rating',
                'finished': settings.getSettingAsBool('display_hide_vcategories')
            }), [
                Asset({'id' : '', 'asset_type' : constants.ASSET_FANART_ID, 'filepath' : globals.g_PATHS.FANART_FILE_PATH.getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_ICON_ID,   'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_ESRB_icon.png').getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_POSTER_ID, 'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_ESRB_poster.png').getPath()}),
            ])  
             
        if vcategory_id == constants.VCATEGORY_PEGI_ID:
             return VirtualCategory({
                'id' : vcategory_id,
                'm_name' : 'Browse by PEGI Rating',
                'plot': 'Browse the ROMs by PEGI rating',
                'finished': settings.getSettingAsBool('display_hide_vcategories')
            }, [
                Asset({'id' : '', 'asset_type' : constants.ASSET_FANART_ID, 'filepath' : globals.g_PATHS.FANART_FILE_PATH.getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_ICON_ID,   'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_PEGI_icon.png').getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_POSTER_ID, 'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_PEGI_poster.png').getPath()}),
            ])  
                     
        if vcategory_id == constants.VCATEGORY_RATING_ID:
             return VirtualCategory(dict(default_entity_data, **{
                'id' : vcategory_id,
                'm_name' : 'Browse by Rating',
                'plot': 'Browse the ROMs by rating',
                'finished': settings.getSettingAsBool('display_hide_vcategories')
            }), [
                Asset({'id' : '', 'asset_type' : constants.ASSET_FANART_ID, 'filepath' : globals.g_PATHS.FANART_FILE_PATH.getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_ICON_ID,   'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_User_Rating_icon.png').getPath()}),
                Asset({'id' : '', 'asset_type' : constants.ASSET_POSTER_ID, 'filepath' : globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Browse_by_User_Rating_poster.png').getPath()}),
            ])     
                
        return None
  
class ROMLauncherAddonFactory(object):

    @staticmethod
    def create(addon: AelAddon, data:dict) -> ROMLauncherAddon:
        if addon.get_addon_id() == constants.RETROPLAYER_LAUNCHER_APP_NAME:
            return RetroplayerLauncherAddon(addon, data)
                    
        return ROMLauncherAddon(addon, data)
    
# -------------------------------------------------------------------------------------------------
# Data model used in the plugin
# Internally all string in the data model are Unicode. They will be encoded to
# UTF-8 when writing files.
# -------------------------------------------------------------------------------------------------
# These functions create a new data structure for the given object and (very importantly) 
# fill the correct default values). 
#
def _get_default_category_data_model():
    return {
        'id' : '',
        'type': constants.OBJ_CATEGORY,
        'm_name' : '',
        'm_year' : '',
        'm_genre' : '',
        'm_developer' : '',
        'm_rating' : '',
        'm_plot' : '',
        'finished' : False,
        'default_icon' : 's_icon',
        'default_fanart' : 's_fanart',
        'default_banner' : 's_banner',
        'default_poster' : 's_poster',
        'default_clearlogo' : 's_clearlogo',
        #'Asset_Prefix' : '',
        's_icon' : '',
        's_fanart' : '',
        's_banner' : '',
        's_poster' : '',
        's_clearlogo' : '',
        's_trailer' : ''
    }

def _get_default_ROMCollection_data_model():
    return {
        'id' : '',
        'type': constants.OBJ_ROMCOLLECTION,
        'm_name' : '',
        'm_year' : '',
        'm_genre' : '',
        'm_developer' : '',
        'm_rating' : '',
        'm_plot' : '',
        'platform' : '',
        'categoryID' : '',
        #'application' : '',
        #'args' : '',
        #'args_extra' : [],
        #'rompath' : '',
        #'romext' : '',
        #'romextrapath' : '',
        'finished': False,
        #'toggle_window' : False, # Former 'minimize'
        #'non_blocking' : False,
        #'multidisc' : True,
        #'roms_base_noext' : '',
        'nointro_xml_file' : '', # deprecated? TODO: remove
        'nointro_display_mode' : constants.AUDIT_DMODE_ALL, # deprecated? TODO: remove
        'audit_state' : constants.AUDIT_STATE_OFF,
        'audit_auto_dat_file' : '',
        'audit_custom_dat_file' : '',
        'audit_display_mode' : constants.AUDIT_DMODE_ALL,
        'launcher_display_mode' : constants.LAUNCHER_DMODE_FLAT,        
        'num_roms' : 0,
        'num_parents' : 0,
        'num_clones' : 0,
        'num_have' : 0,
        'num_miss' : 0,
        'num_unknown' : 0,
        'num_extra' : 0,
        'timestamp_launcher' : 0.0,
        'timestamp_report' : 0.0,
        'default_icon' : 's_icon',
        'default_fanart' : 's_fanart',
        'default_banner' : 's_banner',
        'default_poster' : 's_poster',
        'default_clearlogo' : 's_clearlogo',
        'default_controller' : 's_controller',
        'Asset_Prefix' : '',
        's_icon' : '',
        's_fanart' : '',
        's_banner' : '',
        's_poster' : '',
        's_clearlogo' : '',
        's_controller' : '',
        's_trailer' : '',
        'roms_default_icon' : 's_boxfront',
        'roms_default_fanart' : 's_fanart',
        'roms_default_banner' : 's_banner',
        'roms_default_poster' : 's_flyer',
        'roms_default_clearlogo' : 's_clearlogo',
        'ROM_asset_path' : '',
        'path_3dbox' : '',
        'path_title' : '',
        'path_snap' : '',
        'path_boxfront' : '',
        'path_boxback' : '',
        'path_cartridge' : '',
        'path_fanart' : '',
        'path_banner' : '',
        'path_clearlogo' : '',
        'path_flyer' : '',
        'path_map' : '',
        'path_manual' : '',
        'path_trailer' : ''        
    }

def _get_default_ROM_data_model():
    return {
        'id' : '',
        'type': constants.OBJ_ROM,
        'm_name' : '',
        'm_year' : '',
        'm_genre' : '',
        'm_developer' : '',
        'm_nplayers' : '',
        'm_nplayers_online' : '',
        'm_esrb' : constants.ESRB_PENDING,
        'm_pegi' : constants.DEFAULT_META_PEGI,
        'm_rating' : '',
        'm_plot' : '',
        'platform': '',
        'box_size': '',
        'disks' : [],
        'finished' : False,
        'nointro_status' : constants.AUDIT_STATUS_NONE,
        'pclone_status' : constants.PCLONE_STATUS_NONE,
        'cloneof' : '',
        's_3dbox' : '',
        's_title' : '',
        's_snap' : '',
        's_boxfront' : '',
        's_boxback' : '',
        's_cartridge' : '',
        's_fanart' : '',
        's_banner' : '',
        's_clearlogo' : '',
        's_flyer' : '',
        's_map' : '',
        's_manual' : '',
        's_trailer' : ''
    }
    
def _get_default_asset_data_model():
    return {
        'id' : '',
        'filepath' : '',
        'asset_type' : ''
    }
    
def _get_default_asset_path_data_model():
    return {
        'id' : '',
        'path' : '',
        'asset_type' : ''
    }
    