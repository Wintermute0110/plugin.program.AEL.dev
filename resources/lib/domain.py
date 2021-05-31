# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher miscellaneous set of objects
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
import abc
import collections
import typing
import logging
import re 
import time
import json

from os.path import expanduser
import uuid
import random
import binascii

# --- AEL packages ---
from resources.lib.utils import io, kodi, text
from resources.lib import settings
from resources.lib.constants import *

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# Gets all required information about an asset: path, name, etc.
# Returns an object with all the information
# -------------------------------------------------------------------------------------------------
class AssetInfo(object):
    id              = 0
    key             = ''
    default_key     = ''
    rom_default_key = ''
    name            = ''
    description     = name
    plural          = ''
    fname_infix     = '' # Used only when searching assets when importing XML
    kind_str        = ''
    exts            = []
    exts_dialog     = []
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
        return self.entity_data['id']

    def get_data_dic(self):
        return self.entity_data

    def copy_of_data_dic(self):
        return self.entity_data.copy()

    def set_custom_attribute(self, key, value):
        self.entity_data[key] = value

    def get_custom_attribute(self, key, default_value = None):
        return self.entity_data[key] if key in self.entity_data else default_value

    def import_data_dic(self, data):
        for key in data:
            self.entity_data[key] = data[key]

    def dump_data_dic_to_log(self):
        logger.debug('Dumping object {0}'.format(self.__class__))
        for key in self.entity_data:
            logger.debug('[{0}] = {1}'.format(key, str(self.entity_data[key])))

    # NOTE Rename to get_filename_from_field()
    def _get_value_as_filename(self, field) -> io.FileName:
        if not field in self.entity_data: return None
        path = self.entity_data[field]
        if path == '': return None

        return io.FileName(path)

    def _get_directory_filename_from_field(self, field) -> io.FileName:
        if not field in self.entity_data: return None
        path = self.entity_data[field]
        if path == '' or path is None: return None

        return io.FileName(path, isdir=True)

# Addons that can be used as AEL plugin (launchers, scrapers)
class AelAddon(EntityABC):
    
    def __init__(self, addon_dic=None):        
        if addon_dic is None:
            addon_dic = {}
        if 'id' not in addon_dic:
            addon_dic['id'] = text.misc_generate_random_SID()
            
        super(AelAddon, self).__init__(addon_dic)
    
    def get_id(self) -> str:
        return self.entity_data['id'] 
    
    def get_name(self) -> str:
        return self.entity_data['name']

    def get_addon_id(self) -> str:
        return self.entity_data['addon_id']
    
    def get_version(self) -> str:
        return self.entity_data['version']
    
    def supports_launching(self) -> bool:
        return self.entity_data['is_launcher']
      
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
# |----- Collection
# |
# |----- ROM
# |
#

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
class MetaDataItemABC(EntityABC):
    __metaclass__ = abc.ABCMeta

    #
    # Addon PATHS is required to store/retrieve assets.
    # Addon settings is required because the way the metadata is displayed may depend on
    # some addon settings.
    #
    def __init__(self, entity_data: typing.Dict[str, typing.Any]):
        super(MetaDataItemABC, self).__init__(entity_data)

    # --------------------------------------------------------------------------------------------
    # Core functions
    # --------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def get_object_name(self): pass

    @abc.abstractmethod
    def get_assets_kind(self): pass

    # parent category / romset this item belongs to.
    def get_parent_id(self) -> str:
        return self.entity_data['parent_id'] if 'parent_id' in self.entity_data else None

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

    # In AEL 0.9.7 m_rating is stored as a string.
    def get_rating(self):
        return int(self.entity_data['m_rating']) if self.entity_data['m_rating'] else ''

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
        return self.entity_data['s_trailer'] if 's_trailer' in self.entity_data else ''

    def set_trailer(self, trailer_str):
        if 'http' in trailer_str:
            matches = re.search(r'^.*((youtu.(be|com)\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#\&\?]*).*', trailer_str, re.I)
            if matches is not None:
                video_id = matches.groups()[-1]
                trailer_str = 'plugin://plugin.video.youtube/play/?video_id={}'.format(video_id)

        self.entity_data['s_trailer'] = trailer_str

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
    def has_asset(self, asset_info) -> bool:
        if not asset_info.key in self.entity_data: return False
        return self.entity_data[asset_info.key] != None and self.entity_data[asset_info.key] != ''

    # 
    # Gets the asset path (str) of the given assetinfo type.
    #
    def get_asset_str(self, asset_info=None, asset_id=None, fallback = '') -> str:
        if asset_info is None and asset_id is None: return None
        if asset_id is not None: asset_info = g_assetFactory.get_asset_info(asset_id)
        
        if asset_info.key in self.entity_data and self.entity_data[asset_info.key]:
            return self.entity_data[asset_info.key] 
        return fallback
            
    def get_asset_FN(self, asset_info):
        if not asset_info or not asset_info.key in self.entity_data :
            return None
        
        return self._get_value_as_filename(asset_info.key)
        
    def set_asset(self, asset_info, path_FN):
        path = path_FN.getPath() if path_FN else ''
        self.entity_data[asset_info.key] = path
        
    def clear_asset(self, asset_info):
        self.entity_data[asset_info.key] = ''

    def get_assets_path_FN(self):
        return self._get_directory_filename_from_field('assets_path')        

    @abc.abstractmethod
    def get_asset_ids_list(self) -> typing.List[str]: pass

    #
    # Returns an ordered dictionary with all the object assets, ready to be edited.
    # Keys are AssetInfo objects.
    # Values are the current file for the asset as Unicode string or '' if the asset is not set.
    #
    def get_assets_odict(self) -> typing.Dict[AssetInfo, str]:
        asset_info_list = g_assetFactory.get_asset_list_by_IDs(self.get_asset_ids_list())
        asset_odict = collections.OrderedDict()
        for asset_info in asset_info_list:
            asset_fname_str = self.entity_data[asset_info.key] if self.entity_data[asset_info.key] else ''
            asset_odict[asset_info] = asset_fname_str

        return asset_odict
     
    # 
    # Gets the asset path (str) of the mapped asset type following
    # the given input of either an assetinfo object or asset id.
    #
    def get_mapped_asset_str(self, asset_info=None, asset_id=None, fallback = '') -> str:
        asset_info = self.get_mapped_asset_info(asset_info, asset_id)
        if asset_info.key in self.entity_data and self.entity_data[asset_info.key]:
            return self.entity_data[asset_info.key] 
        return fallback
    
    #
    # Get a list of the assets that can be mapped to a defaultable asset.
    # They must be images, no videos, no documents.
    #
    def get_mappable_asset_list(self) -> typing.List[AssetInfo]: 
        return g_assetFactory.get_asset_list_by_IDs(self.get_asset_ids_list(), 'image')

    def get_mapped_assets(self) -> typing.Dict[str,str]:
        mappable_assets = self.get_mappable_asset_list()
        mapped_assets = {}
        for mappable_asset in mappable_assets:
            if mappable_asset.id == ASSET_ICON_ID: 
                mapped_assets[mappable_asset.fname_infix] = self.get_mapped_asset_str(mappable_asset, fallback='DefaultFolder.png')
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
            raise AddonError('Not supported asset type used. This might be a bug!')  
            
        return self.entity_data[asset_info.default_key]
	
    def set_mapped_asset_key(self, asset_info, mapped_to_info):
        self.entity_data[asset_info.default_key] = mapped_to_info.key
        
    def __str__(self):
        return '{}}#{}: {}'.format(self.get_object_name(), self.get_id(), self.get_name())

# -------------------------------------------------------------------------------------------------
# Class representing an AEL Cateogry.
# Contains code to generate the context menus passed to Dialog.select()
# -------------------------------------------------------------------------------------------------
class Category(MetaDataItemABC):
    def __init__(self, category_dic: typing.Dict[str, typing.Any]):
        # Concrete classes are responsible of creating a default entity_data dictionary
        # with sensible defaults.
        if category_dic is None:
            category_dic = {}#fs_new_category()
            category_dic['id'] = text.misc_generate_random_SID()
        super(Category, self).__init__(category_dic)

    def get_object_name(self): return 'Category'

    def get_assets_kind(self): return KIND_ASSET_CATEGORY

    def is_virtual(self): return False
    
    def num_romsets(self) -> int:
        return self.entity_data['num_romsets'] if 'num_romsets' in self.entity_data else 0

    def num_categories(self) -> int:
        return self.entity_data['num_categories'] if 'num_categories' in self.entity_data else 0

    def has_items(self) -> bool:
        return len(self.num_romsets()) > 0 or len(self.num_categories()) > 0

    def get_asset_ids_list(self): 
        return COLLECTION_ASSET_ID_LIST
    
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
        nfo_content.append('<!-- Exported by AEL on {0} -->\n'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
        nfo_content.append('<category>\n')
        nfo_content.append(text.XML_line('year',      self.get_year()))
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
        str_list.append('<!-- Exported by AEL on {0} -->\n'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
        str_list.append('<advanced_emulator_launcher_configuration>\n')
        str_list.append('<category>\n')
        str_list.append(text.XML_line('name', self.get_name()))
        str_list.append(text.XML_line('year', self.get_releaseyear()))
        str_list.append(text.XML_line('genre', self.get_genre()))
        str_list.append(text.XML_line('developer', self.get_developer()))
        str_list.append(text.XML_line('rating', self.get_rating()))
        str_list.append(text.XML_line('plot', self.get_plot()))
        str_list.append(text.XML_line('Asset_Prefix', self.get_custom_attribute('Asset_Prefix')))
        str_list.append(text.XML_line('s_icon', self.get_asset_str(asset_id=ASSET_ICON_ID)))
        str_list.append(text.XML_line('s_fanart', self.get_asset_str(asset_id=ASSET_FANART_ID)))
        str_list.append(text.XML_line('s_banner', self.get_asset_str(asset_id=ASSET_BANNER_ID)))
        str_list.append(text.XML_line('s_poster', self.get_asset_str(asset_id=ASSET_POSTER_ID)))
        str_list.append(text.XML_line('s_controller', self.get_asset_str(asset_id=ASSET_CONTROLLER_ID)))
        str_list.append(text.XML_line('s_clearlogo', self.get_asset_str(asset_id=ASSET_CLEARLOGO_ID)))
        str_list.append('</category>\n')
        str_list.append('</advanced_emulator_launcher_configuration>\n')
        
        full_string = ''.join(str_list)
        file.writeAll(full_string)
        
    def __str__(self):
        return super().__str__()
    
# -------------------------------------------------------------------------------------------------
# Class representing the virtual categories in AEL.
# All ROM Collections is a Virtual Category.
# ...
# -------------------------------------------------------------------------------------------------
class VirtualCategory(MetaDataItemABC):
    #
    # obj_dic is mandatory in Virtual Categories an must have the following fields:
    #  1) id
    #  2) type
    #  3) m_name
    #
    def __init__(self, PATHS, settings, obj_dic, objectRepository):
        # Concrete classes are responsible of creating a default entity_data dictionary
        # with sensible defaults.
        # This object is special, obj_dic must be not None and have certain fields.
        entity_data = fs_new_category()
        entity_data['id'] = obj_dic['id']
        entity_data['type'] = obj_dic['type']
        entity_data['m_name'] = obj_dic['m_name']
        super(VirtualCategory, self).__init__(PATHS, settings, entity_data, objectRepository)

    def get_object_name(self): return 'Virtual Category'

    def get_assets_kind(self): return KIND_ASSET_CATEGORY

    def is_virtual(self): return True

class ROMSetLauncher(object):
    
    def __init__(self, addon: AelAddon, args: dict, is_default: bool):
        self.addon = addon
        self.args = args
        self.is_default = is_default
        
    def get_arguments(self) -> str:
        return json.dumps(self.args)
    
# -------------------------------------------------------------------------------------------------
# Class representing a collection of ROMs.
# -------------------------------------------------------------------------------------------------
class ROMSet(MetaDataItemABC):
    def __init__(self, entity_data, launchers_data: typing.List[ROMSetLauncher] = []):
        self.launchers_data = launchers_data
        super(ROMSet, self).__init__(entity_data)

    def get_platform(self): return self.entity_data['platform']

    def set_platform(self, platform): self.entity_data['platform'] = platform

    def get_box_sizing(self):
        return self.entity_data['box_size'] if 'box_size' in self.entity_data else BOX_SIZE_POSTER
    
    def set_box_sizing(self, box_size): self.entity_data['box_size'] = box_size

    def get_assets_kind(self): return KIND_ASSET_LAUNCHER

    def get_asset_ids_list(self): return LAUNCHER_ASSET_ID_LIST

    def get_asset_path(self, asset_info: AssetInfo) -> io.FileName:
        if not asset_info: return None
        return self._get_value_as_filename(asset_info.path_key)

    def set_asset_path(self, asset_info: AssetInfo, path: str):
        logger.debug('Setting "{}" to {}'.format(asset_info.path_key, path))
        self.entity_data[asset_info.path_key] = path

    def get_ROM_mappable_asset_list(self):
        MAPPABLE_ASSETS = [ASSET_ICON_ID, ASSET_FANART_ID, ASSET_BANNER_ID, ASSET_CLEARLOGO_ID, ASSET_POSTER_ID]
        return g_assetFactory.get_asset_list_by_IDs(MAPPABLE_ASSETS)

    #
    # Gets the actual assetinfo object that is mapped for
    # the given (ROM) assetinfo for this particular MetaDataItem.
    #
    def get_mapped_ROM_asset_info(self, asset_info=None, asset_id=None) -> AssetInfo:
        if asset_info is None and asset_id is None: return None
        if asset_id is not None: asset_info = g_assetFactory.get_asset_info(asset_id)
        
        mapped_key = self.get_mapped_ROM_asset_key(asset_info)
        mapped_asset_info = g_assetFactory.get_asset_info_by_key(mapped_key)
        return mapped_asset_info

    #
    # Gets the database filename mapped for asset_info.
    # Note that the mapped asset uses diferent fields wheter it is a Category/Launcher/ROM
    #
    def get_mapped_ROM_asset_key(self, asset_info: AssetInfo) -> str:
        if asset_info.rom_default_key is '':
            logger.error('Requested mapping for AssetInfo without default key. Type {}'.format(asset_info.id))
            raise AddonError('Not supported asset type used. This might be a bug!')  
            
        return self.entity_data[asset_info.rom_default_key]

    def set_mapped_ROM_asset_key(self, asset_info: AssetInfo, mapped_to_info: AssetInfo):
        self.entity_data[asset_info.rom_default_key] = mapped_to_info.key

    #
    # Get a list of assets with duplicated paths. Refuse to do anything if duplicated paths found.
    #
    def get_duplicated_asset_dirs(self):
        duplicated_bool_list   = [False] * len(ROM_ASSET_ID_LIST)
        duplicated_name_list   = []

        # >> Check for duplicated asset paths
        for i, asset_i in enumerate(ROM_ASSET_ID_LIST[:-1]):
            A_i = g_assetFactory.get_asset_info(asset_i)
            for j, asset_j in enumerate(ROM_ASSET_ID_LIST[i+1:]):
                A_j = g_assetFactory.get_asset_info(asset_j)
                # >> Exclude unconfigured assets (empty strings).
                if A_i.path_key not in self.entity_data or A_j.path_key not in self.entity_data  \
                    or not self.entity_data[A_i.path_key] or not self.entity_data[A_j.path_key]: continue
                
                # log_debug('asset_get_duplicated_asset_list() Checking {0:<9} vs {1:<9}'.format(A_i.name, A_j.name))
                if self.entity_data[A_i.path_key] == self.entity_data[A_j.path_key]:
                    duplicated_bool_list[i] = True
                    duplicated_name_list.append('{0} and {1}'.format(A_i.name, A_j.name))
                    logger.info('asset_get_duplicated_asset_list() DUPLICATED {0} and {1}'.format(A_i.name, A_j.name))

        return duplicated_name_list

    def num_roms(self) -> int:
        return self.entity_data['num_roms'] if 'num_roms' in self.entity_data else 0

    def add_launcher(self, addon: AelAddon, args: dict, is_default: bool = False):
        launcher = next((l for l in self.launchers_data if l.addon.get_id() == addon.get_id()), None)
        if launcher is None:
            launcher = ROMSetLauncher(addon, args, is_default)
            self.launchers_data.append(launcher)
        
        launcher.args = args
        if launcher.is_default != is_default:
            if is_default:
                current_default_launcher = next((l for l in self.launchers_data if l.is_default), None)
                current_default_launcher.is_default = False
            launcher.is_default = is_default

    def get_launchers_data(self) -> typing.List[ROMSetLauncher]:
        return self.launchers_data

    def get_NFO_name(self) -> io.FileName:
        nfo_dir = io.FileName(settings.getSetting('launchers_asset_dir'), isdir = True)
        nfo_file_path = nfo_dir.pjoin(self.get_name() + '.nfo')
        logger.debug("ROMSet.get_NFO_name() nfo_file_path = '{0}'".format(nfo_file_path.getPath()))
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
        logger.debug('ROMSet.import_NFO_file() Importing launcher NFO "{0}"'.format(nfo_FileName.getPath()))

        # --- Import data ---
        if nfo_FileName.exists():
            try:
                item_nfo = nfo_FileName.loadFileToStr()
                item_nfo = item_nfo.replace('\r', '').replace('\n', '')
            except:
                kodi.notify_warn('Exception reading NFO file {0}'.format(nfo_FileName.getPath()))
                logger.error("ROMSet.import_NFO_file() Exception reading NFO file '{0}'".format(nfo_FileName.getPath()))
                return False
        else:
            kodi.notify_warn('NFO file not found {0}'.format(nfo_FileName.getBase()))
            logger.error("ROMSet.import_NFO_file() NFO file not found '{0}'".format(nfo_FileName.getPath()))
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

        logger.debug("ROMSet.import_NFO_file() Imported '{0}'".format(nfo_FileName.getPath()))

        return True
    
    def export_to_NFO_file(self, nfo_FileName: io.FileName):
        # --- Get NFO file name ---
        logger.debug('ROMSet.export_to_NFO_file() Exporting launcher NFO "{0}"'.format(nfo_FileName.getPath()))

        # If NFO file does not exist then create them. If it exists, overwrite.
        nfo_content = []
        nfo_content.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        nfo_content.append('<!-- Exported by AEL on {0} -->\n'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
        nfo_content.append('<romset>\n')
        nfo_content.append(text.XML_line('year',      self.get_releaseyear()))
        nfo_content.append(text.XML_line('genre',     self.get_genre())) 
        nfo_content.append(text.XML_line('developer', self.get_developer()))
        nfo_content.append(text.XML_line('rating',    self.get_rating()))
        nfo_content.append(text.XML_line('plot',      self.get_plot()))
        
        nfo_content.append('</romset>\n')
        full_string = ''.join(nfo_content)
        nfo_FileName.writeAll(full_string)
            
    def export_to_file(self, file: io.FileName):
        logger.debug('ROMSet.export_to_file() ROMSet "{0}" (ID "{1}")'.format(self.get_name(), self.get_id()))

        # --- Create list of strings ---
        str_list = []
        str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        str_list.append('<!-- Exported by AEL on {0} -->\n'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
        str_list.append('<advanced_emulator_launcher_configuration>\n')
        str_list.append('<romset>\n')
        str_list.append(text.XML_line('name', self.get_name()))
        str_list.append(text.XML_line('year', self.get_releaseyear()))
        str_list.append(text.XML_line('genre', self.get_genre()))
        str_list.append(text.XML_line('developer', self.get_developer()))
        str_list.append(text.XML_line('rating', self.get_rating()))
        str_list.append(text.XML_line('plot', self.get_plot()))
        #str_list.append(text.XML_line('Asset_Prefix', self.get_custom_attribute('Asset_Prefix')))
        str_list.append(text.XML_line('s_icon', self.get_asset_str(asset_id=ASSET_ICON_ID)))
        str_list.append(text.XML_line('s_fanart', self.get_asset_str(asset_id=ASSET_FANART_ID)))
        str_list.append(text.XML_line('s_banner', self.get_asset_str(asset_id=ASSET_BANNER_ID)))
        str_list.append(text.XML_line('s_poster', self.get_asset_str(asset_id=ASSET_POSTER_ID)))
        str_list.append(text.XML_line('s_controller', self.get_asset_str(asset_id=ASSET_CONTROLLER_ID)))
        str_list.append(text.XML_line('s_clearlogo', self.get_asset_str(asset_id=ASSET_CLEARLOGO_ID)))
        str_list.append(text.XML_line('s_trailer', self.get_trailer()))
        str_list.append('</romset>\n')
        str_list.append('</advanced_emulator_launcher_configuration>\n')
        
        full_string = ''.join(str_list)
        file.writeAll(full_string)
            
    def __str__(self):
        return super().__str__()
    
# -------------------------------------------------------------------------------------------------
# Class representing a ROM file you can play through AEL.
# -------------------------------------------------------------------------------------------------
class ROM(MetaDataItemABC):
        
    def __init__(self, rom_data = None):        
        if rom_data is None:
            #rom_data = fs_new_rom()
            rom_data['id'] = text.misc_generate_random_SID()
            rom_data['type'] = OBJ_ROM
            
        super(ROM, self).__init__(rom_data)
    
    # is this virtual only? Should we make a VirtualRom(Rom)?
    def get_launcher_id(self):
        return self.entity_data['poaren']
    
    def get_platform(self):
        if self.is_virtual_rom():
            return self.entity_data['platform']
                        
        return self.launcher.get_platform()
    
    def get_nointro_status(self):
        return self.entity_data['nointro_status']

    def get_pclone_status(self):
        return self.entity_data['pclone_status'] if 'pclone_status' in self.entity_data else ''

    def get_clone(self):
        return self.entity_data['cloneof']
    
    def has_alternative_application(self):
        return 'altapp' in self.entity_data and self.entity_data['altapp']

    def get_alternative_application(self):
        return self.entity_data['altapp']

    def has_alternative_arguments(self):
        return 'altarg' in self.entity_data and self.entity_data['altarg']

    def get_alternative_arguments(self):
        return self.entity_data['altarg']

    def get_filename(self):
        return self.entity_data['filename']

    def get_file(self):
        return self._get_value_as_filename('filename')

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
        ROM_FileName = self.get_file()
        nfo_file_path = ROM_FileName.changeExtension('.nfo')
        return nfo_file_path

    def get_number_of_players(self):
        return self.entity_data['m_nplayers']

    def get_esrb_rating(self):
        return self.entity_data['m_esrb']

    def get_favourite_status(self):
        return self.entity_data['fav_status'] if 'fav_status' in self.entity_data else None

    def get_launch_count(self):
        return self.entity_data['launch_count']

    def set_file(self, file):
        self.entity_data['filename'] = file.getPath()

    def add_disk(self, disk):
        self.entity_data['disks'].append(disk)

    def set_number_of_players(self, amount):
        self.entity_data['m_nplayers'] = amount

    def set_esrb_rating(self, esrb):
        self.entity_data['m_esrb'] = esrb

    def set_nointro_status(self, status):
        self.entity_data['nointro_status'] = status

    def set_pclone_status(self, status):
        self.entity_data['pclone_status'] = status

    def set_clone(self, clone):
        self.entity_data['cloneof'] = clone

    # todo: definitly something for a inherited FavouriteRom class
    # >> Favourite ROM unique fields
    # >> Favourite ROMs in "Most played ROMs" DB also have 'launch_count' field.
    def set_favourite_status(self, state):
        self.entity_data['fav_status'] = state

    def increase_launch_count(self):
        launch_count = self.entity_data['launch_count'] if 'launch_count' in self.entity_data else 0
        launch_count += 1
        self.entity_data['launch_count'] = launch_count

    def set_alternative_application(self, application):
        self.entity_data['altapp'] = application

    def set_alternative_arguments(self, arg):
        self.entity_data['altarg'] = arg

    def get_box_sizing(self):        
        if 'box_size' in self.entity_data: return self.entity_data['box_size'] 
        # fallback to launcher size 
        if self.launcher: return self.launcher.get_box_sizing()
        return BOX_SIZE_POSTER
    
    def set_box_sizing(self, box_size):
        self.entity_data['box_size'] = box_size

    def copy(self):
        data = self.copy_of_data_dic()
        return ROM(data, self.launcher)

    def copy_as_virtual_ROM(self):
        data = self.copy_of_data_dic()
        data['launcherID'] = self.launcher.get_id()
        data['platform'] = self.get_platform()
        return ROM(data, None)

    # -------------------------------------------------------------------------------------------------
    # Favourite ROM creation/management
    # -------------------------------------------------------------------------------------------------
    #
    # Creates a new Favourite ROM dictionary from parent ROM and Launcher.
    #
    # No-Intro Missing ROMs are not allowed in Favourites or Virtual Launchers.
    # fav_status = ['OK', 'Unlinked ROM', 'Unlinked Launcher', 'Broken'] default 'OK'
    #  'OK'                ROM filename exists and launcher exists and ROM id exists
    #  'Unlinked ROM'      ROM filename exists but ROM ID in launcher does not
    #  'Unlinked Launcher' ROM filename exists but Launcher ID not found
    #                      Note that if the launcher does not exists implies ROM ID does not exist.
    #                      If launcher doesn't exist ROM JSON cannot be loaded.
    #  'Broken'            ROM filename does not exist. ROM is unplayable
    #
    def copy_as_favourite_ROM(self):
        # >> Copy original rom     
        # todo: Should we make a FavouriteRom class inheriting Rom?
        favourite_data = self.copy_of_data_dic()
        
        favourite_data['launcherID'] = self.launcher.get_id()
        favourite_data['platform']   = self.get_platform()
        
        favourite = ROM(favourite_data, None)
        
        # Delete nointro_status field from ROM. Make sure this is done in the copy to be
        # returned to avoid chaning the function parameters (dictionaries are mutable!)
        # See http://stackoverflow.com/questions/5844672/delete-an-element-from-a-dictionary
        # NOTE keep it!
        # del favourite_data['nointro_status']
        
        # >> Favourite ROM unique fields
        # >> Favourite ROMs in "Most played ROMs" DB also have 'launch_count' field.
        favourite.set_favourite_status('OK')

        # >> Copy parent launcher fields into Favourite ROM
        #favourite.set_custom_attribute('launcherID',            self.get_id())
        #favourite.set_custom_attribute('platform',              self.get_platform())
        #favourite.set_custom_attribute('application',           self.get_custom_attribute('application'))
        #favourite.set_custom_attribute('args',                  self.get_custom_attribute('args'))
        #favourite.set_custom_attribute('args_extra',            self.get_custom_attribute('args_extra'))
        #favourite.set_custom_attribute('rompath',               self.get_rom_path().getPath())
        #favourite.set_custom_attribute('romext',                self.get_custom_attribute('romext'))
        #favourite.set_custom_attribute('toggle_window',         self.is_in_windowed_mode())
        #favourite.set_custom_attribute('non_blocking',          self.is_non_blocking())
        #favourite.set_custom_attribute('roms_default_icon',     self.get_custom_attribute('roms_default_icon'))
        #favourite.set_custom_attribute('roms_default_fanart',   self.get_custom_attribute('roms_default_fanart'))
        #favourite.set_custom_attribute('roms_default_banner',   self.get_custom_attribute('roms_default_banner'))
        #favourite.set_custom_attribute('roms_default_poster',   self.get_custom_attribute('roms_default_poster'))
        #favourite.set_custom_attribute('roms_default_clearlogo',self.get_custom_attribute('roms_default_clearlogo'))

        return favourite

    def delete_from_disk(self):
        if self.launcher is None:
            raise AddonError('Launcher not set for ROM')
        
        self.launcher.delete_ROM(self)
        
    def get_assets_kind(self): return KIND_ASSET_ROM
	
    def get_object_name(self): 
        return "ROM"
	
    def save_to_disk(self): 
        if self.launcher is None:
            raise AddonError('Launcher not set for ROM')
        
        self.launcher.save_ROM(self)

    # ---------------------------------------------------------------------------------------------
    # ROM asset methods
    # ---------------------------------------------------------------------------------------------
    #
    # Returns an ordered dictionary with all the object assets, ready to be edited.
    # Keys are AssetInfo objects.
    # Values are the current file for the asset as Unicode string or '' if the asset is not set.
    #
    def get_assets_odict(self):
        asset_info_list = g_assetFactory.get_asset_list_by_IDs(ROM_ASSET_ID_LIST)
        asset_odict = collections.OrderedDict()
        for asset_info in asset_info_list:
            asset_odict[asset_info] = self.get_asset_str(asset_info)

        return asset_odict
    
    def get_assets_path_FN(self):
        if not self.launcher:
            return None
        
        return self.launcher.get_assets_path_FN()
    
    def get_asset_ids_list(self): 
        return ROM_ASSET_ID_LIST
                 
    def get_edit_options(self, category_id):
        delete_rom_txt = 'Delete ROM'
        if category_id == VCATEGORY_FAVOURITES_ID:
            delete_rom_txt = 'Delete Favourite ROM'
        if category_id == VCATEGORY_COLLECTIONS_ID:
            delete_rom_txt = 'Delete Collection ROM'

        options = collections.OrderedDict()
        options['EDIT_METADATA']    = 'Edit Metadata ...'
        options['EDIT_ASSETS']      = 'Edit Assets/Artwork ...'
        options['ROM_STATUS']       = 'Status: {0}'.format(self.get_finished_str()).encode('utf-8')

        options['ADVANCED_MODS']    = 'Advanced Modifications ...'
        options['DELETE_ROM']       = delete_rom_txt

        if category_id == VCATEGORY_FAVOURITES_ID:
            options['MANAGE_FAV_ROM']   = 'Manage Favourite ROM object ...'
            
        elif category_id == VCATEGORY_COLLECTIONS_ID:
            options['MANAGE_COL_ROM']       = 'Manage Collection ROM object ...'
            options['MANAGE_COL_ROM_POS']   = 'Manage Collection ROM position ...'

        return options

    # >> Metadata edit dialog
    def get_metadata_edit_options(self):
        NFO_FileName = fs_get_ROM_NFO_name(self.get_data_dic())
        NFO_found_str = 'NFO found' if NFO_FileName.exists() else 'NFO not found'
        plot_str = text.limit_string(self.entity_data['m_plot'], PLOT_STR_MAXSIZE)

        rating = self.get_rating()
        if rating == -1:
            rating = 'not rated'

        options = collections.OrderedDict()
        options['EDIT_METADATA_TITLE']       = u"Edit Title: '{0}'".format(self.get_name()).encode('utf-8')
        options['EDIT_METADATA_RELEASEYEAR'] = u"Edit Release Year: '{0}'".format(self.get_releaseyear()).encode('utf-8')
        options['EDIT_METADATA_GENRE']       = u"Edit Genre: '{0}'".format(self.get_genre()).encode('utf-8')
        options['EDIT_METADATA_DEVELOPER']   = u"Edit Developer: '{0}'".format(self.get_developer()).encode('utf-8')
        options['EDIT_METADATA_NPLAYERS']    = u"Edit NPlayers: '{0}'".format(self.get_number_of_players()).encode('utf-8')
        options['EDIT_METADATA_ESRB']        = u"Edit ESRB rating: '{0}'".format(self.get_esrb_rating()).encode('utf-8')
        options['EDIT_METADATA_RATING']      = u"Edit Rating: '{}'".format(rating).encode('utf-8')
        options['EDIT_METADATA_PLOT']        = u"Edit Plot: '{}'".format(plot_str).encode('utf-8')
        options['EDIT_METADATA_BOXSIZE']     = u"Edit Box Size: '{}'".format(self.get_box_sizing())
        options['LOAD_PLOT']                 = "Load Plot from TXT file ..."
        options['IMPORT_NFO_FILE']           = u"Import NFO file (default, {})".format(NFO_found_str).encode('utf-8')
        options['SAVE_NFO_FILE']             = "Save NFO file (default location)"
        options['SCRAPE_ROM_METADATA']       = "Scrape Metadata"

        return options

    #
    # Returns a dictionary of options to choose from
    # with which you can do advanced modifications on this specific rom.
    #
    def get_advanced_modification_options(self):
        logger.debug('ROM::get_advanced_modification_options() Returning edit options')
        logger.debug('ROM::get_advanced_modification_options() Returning edit options')
        options = collections.OrderedDict()
        options['CHANGE_ROM_FILE']          = "Change ROM file: '{0}'".format(self.get_filename())
        options['CHANGE_ALT_APPLICATION']   = "Alternative application: '{0}'".format(self.get_alternative_application())
        options['CHANGE_ALT_ARGUMENTS']     = "Alternative arguments: '{0}'".format(self.get_alternative_arguments())

        return options

    #
    # Reads an NFO file with ROM information.
    # See comments in fs_export_ROM_NFO() about verbosity.
    # About reading files in Unicode http://stackoverflow.com/questions/147741/character-reading-from-file-in-python
    #
    # todo: Replace with nfo_file_path.readXml() and just use XPath
    def update_with_nfo_file(self, nfo_file_path, verbose = True):
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
        if len(item_trailer) > 0:   self.set_trailer(text.unescape_XML(item_trailer[0]))

        if verbose:
            kodi.notify('Imported {0}'.format(nfo_file_path.getPath()))

        return True

    def __str__(self):
        """Overrides the default implementation"""
        return json.dumps(self.entity_data)

# #################################################################################################
# #################################################################################################
# ROM scanners
# #################################################################################################
# #################################################################################################
class RomScannersFactory(object):
    def __init__(self, PATHS, settings):
        self.settings = settings
        self.reports_dir = PATHS.REPORTS_DIR
        self.addon_dir = PATHS.ADDON_DATA_DIR

    def create(self, launcher, scraping_strategy, progress_dialog):
        launcherType = launcher.get_launcher_type()
        logger.info('RomScannersFactory: Creating romscanner for {}'.format(launcherType))

        if not launcher.supports_launching_roms():
            return NullScanner(launcher, self.settings, progress_dialog)

        if launcherType == OBJ_LAUNCHER_STEAM:
            return SteamScanner(self.reports_dir, self.addon_dir, launcher, self.settings, scraping_strategy, progress_dialog)

        if launcherType == OBJ_LAUNCHER_NVGAMESTREAM:
            return NvidiaStreamScanner(self.reports_dir, self.addon_dir, launcher, self.settings, scraping_strategy, progress_dialog)
                
        return RomFolderScanner(self.reports_dir, self.addon_dir, launcher, self.settings, scraping_strategy, progress_dialog)

class ScannerStrategyABC(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, launcher, settings, progress_dialog):
        self.launcher = launcher
        self.settings = settings
        self.progress_dialog = progress_dialog     
        super(ScannerStrategyABC, self).__init__()

    #
    # Scans for new roms based on the type of launcher.
    #
    @abc.abstractmethod
    def scan(self):
        return {}

    #
    # Cleans up ROM collection.
    # Remove Remove dead/missing ROMs ROMs
    #
    @abc.abstractmethod
    def cleanup(self):
        return {}

class NullScanner(ScannerStrategyABC):
    def scan(self):
        return {}

    def cleanup(self):
        return {}

class RomScannerStrategy(ScannerStrategyABC):
    __metaclass__ = abc.ABCMeta

    def __init__(self, reports_dir, addon_dir, launcher, settings, scraping_strategy, progress_dialog):
        
        self.reports_dir = reports_dir
        self.addon_dir = addon_dir
           
        self.scraping_strategy = scraping_strategy

        super(RomScannerStrategy, self).__init__(launcher, settings, progress_dialog)

    def scan(self):
               
        # --- Open ROM scanner report file ---
        launcher_report = FileReporter(self.reports_dir, self.launcher.get_data_dic(), LogReporter(self.launcher.get_data_dic()))
        launcher_report.open('RomScanner() Starting ROM scanner')
        
        # >> Check if there is an XML for this launcher. If so, load it.
        # >> If file does not exist or is empty then return an empty dictionary.
        launcher_report.write('Loading launcher ROMs ...')
        roms = self.launcher.get_roms()

        if roms is None:
            roms = []
        
        num_roms = len(roms)
        launcher_report.write('{} ROMs currently in database'.format(num_roms))
        
        launcher_report.write('Collecting candidates ...')
        candidates = self._getCandidates(launcher_report)
        num_candidates = len(candidates)
        launcher_report.write('{} candidates found'.format(num_candidates))
        
        # --- Scan all files in extra ROM path ---------------------------------------------------
        if self.launcher.has_extra_rompath():
            logger.info('Scanning candidates in extra ROM path.')
            extra_candidates = self._getCandidates(launcher_report, self.launcher.get_extra_rompath())            
            logger.info('{} extra candidate files found'.format(len(extra_candidates)))
        else:
            logger.info('Extra ROM path empty. Skipping scanning.')
            extra_candidates = []

        launcher_report.write('Removing dead ROMs ...')
        num_removed_roms = self._removeDeadRoms(candidates, roms)        

        if num_removed_roms > 0:
            kodi.notify('{0} dead ROMs removed successfully'.format(num_removed_roms))
            logger.info('{0} dead ROMs removed successfully'.format(num_removed_roms))
        else:
            logger.info('No dead ROMs found')
        
        # --- Prepare list of candidates to be processed ----------------------------------------------
        # List has tuples (candidate, extra_ROM_flag). List already sorted alphabetically.
        candidates_combined = []
        for candidate in sorted(candidates): candidates_combined.append((candidate, False))
        for candidate in sorted(extra_candidates): candidates_combined.append((candidate, True))

        new_roms = self._processFoundItems(candidates_combined, roms, launcher_report)
        
        if not new_roms:
            return None

        num_new_roms = len(new_roms)
        roms = roms + new_roms

        launcher_report.write('******************** ROM scanner finished. Report ********************')
        launcher_report.write('Removed dead ROMs   {0:6d}'.format(num_removed_roms))
        launcher_report.write('Files checked       {0:6d}'.format(num_candidates))
        launcher_report.write('Extra files checked {0:6d}'.format(len(extra_candidates)))
        launcher_report.write('New added ROMs      {0:6d}'.format(num_new_roms))
        
        if len(roms) == 0:
            launcher_report.write('WARNING Launcher has no ROMs!')
            launcher_report.close()
            kodi.dialogger.OK('No ROMs found! Make sure launcher directory and file extensions are correct.')
            return None
        
        if num_new_roms == 0:
            kodi.notify('Added no new ROMs. Launcher has {0} ROMs'.format(len(roms)))
        else:
            kodi.notify('Added {0} new ROMs'.format(num_new_roms))

        # --- Close ROM scanner report file ---
        launcher_report.write('*** END of the ROM scanner report ***')
        launcher_report.close()

        return roms

    def cleanup(self):
        launcher_report = LogReporter(self.launcher.get_data_dic())
        launcher_report.open('RomScanner() Starting Dead ROM cleaning')
        logger.debug('RomScanner() Starting Dead ROM cleaning')

        roms = self.launcher.get_roms()
        if roms is None:
            launcher_report.close()
            logger.info('RomScanner() No roms available to cleanup')
            return {}
        
        num_roms = len(roms)
        launcher_report.write('{0} ROMs currently in database'.format(num_roms))
        
        launcher_report.write('Collecting candidates ...')
        candidates = self._getCandidates(launcher_report)
        num_candidates = len(candidates)
        logger.info('{0} candidates found'.format(num_candidates))

        launcher_report.write('Removing dead ROMs ...')
        num_removed_roms = self._removeDeadRoms(candidates, roms)        

        if num_removed_roms > 0:
            kodi.notify('{0} dead ROMs removed successfully'.format(num_removed_roms))
            logger.info('{0} dead ROMs removed successfully'.format(num_removed_roms))
        else:
            logger.info('No dead ROMs found')

        launcher_report.close()
        return roms

    # ~~~ Scan for new files (*.*) and put them in a list ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @abc.abstractmethod
    def _getCandidates(self, launcher_report, rom_path = None):
        return []

    # --- Remove dead entries -----------------------------------------------------------------
    @abc.abstractmethod
    def _removeDeadRoms(self, candidates, roms):
        return 0

    # ~~~ Now go processing item by item ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @abc.abstractmethod
    def _processFoundItems(self, items, roms, launcher_report):
        return []

class RomFolderScanner(RomScannerStrategy):
    
    # ~~~ Scan for new files (*.*) and put them in a list ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def _getCandidates(self, launcher_report, rom_path = None):
        self.progress_dialog.startProgress('Scanning and caching files in ROM path ...')
        files = []
        
        if rom_path is None: rom_path = self.launcher.get_rom_path()
        launcher_report.write('Scanning files in {}'.format(rom_path.getPath()))

        if self.settings['scan_recursive']:
            logger.info('Recursive scan activated')
            files = rom_path.recursiveScanFilesInPath('*.*')
        else:
            logger.info('Recursive scan not activated')
            files = rom_path.scanFilesInPath('*.*')

        num_files = len(files)
        launcher_report.write('  File scanner found {} files'.format(num_files))
        self.progress_dialog.endProgress()
                
        return files

    # --- Remove dead entries -----------------------------------------------------------------
    def _removeDeadRoms(self, candidates, roms):
        num_roms = len(roms)
        num_removed_roms = 0
        if num_roms == 0:
            logger.info('Launcher is empty. No dead ROM check.')
            return num_removed_roms
        
        logger.debug('Starting dead items scan')
        i = 0
            
        self.progress_dialog.startProgress('Checking for dead ROMs ...', num_roms)
            
        for rom in reversed(roms):
            fileName = rom.get_file()
            logger.debug('Searching {0}'.format(fileName.getPath()))
            self.progress_dialog.updateProgress(i)
            
            if not fileName.exists():
                logger.debug('Not found')
                logger.debug('Deleting from DB {0}'.format(fileName.getPath()))
                roms.remove(rom)
                num_removed_roms += 1
            i += 1
            
        self.progress_dialog.endProgress()

        return num_removed_roms

    # ~~~ Now go processing item by item ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def _processFoundItems(self, items, roms, launcher_report):

        num_items = len(items)    
        new_roms = []

        self.progress_dialog.startProgress('Scanning found items', num_items)
        logger.debug('============================== Processing ROMs ==============================')
        launcher_report.write('Processing files ...')
        num_items_checked = 0
        
        allowedExtensions = self.launcher.get_rom_extensions()
        launcher_multidisc = self.launcher.supports_multidisc()

        skip_if_scraping_failed = self.settings['scan_skip_on_scraping_failure']
        for ROM_file, extra_ROM_flag in sorted(items):
            self.progress_dialog.updateProgress(num_items_checked)
            
            # --- Get all file name combinations ---
            launcher_report.write('>>> {0}'.format(ROM_file.getPath()).encode('utf-8'))

            # ~~~ Update progress dialog ~~~
            file_text = 'ROM {0}'.format(ROM_file.getBase())
            self.progress_dialog.updateMessages(file_text, 'Checking if has ROM extension ...')
                        
            # --- Check if filename matchs ROM extensions ---
            # The recursive scan has scanned all files. Check if this file matches some of 
            # the ROM extensions. If this file isn't a ROM skip it and go for next one in the list.
            processROM = False

            for ext in allowedExtensions:
                if ROM_file.getExt() == '.' + ext:
                    launcher_report.write("  Expected '{0}' extension detected".format(ext))
                    processROM = True
                    break

            if not processROM: 
                launcher_report.write('  File has not an expected extension. Skipping file.')
                continue
                        
            # --- Check if ROM belongs to a multidisc set ---
            self.progress_dialog.updateMessages(file_text, 'Checking if ROM belongs to multidisc set..')
                       
            MultiDiscInROMs = False
            MDSet = text.get_multidisc_info(ROM_file)
            if MDSet.isMultiDisc and launcher_multidisc:
                logger.info('ROM belongs to a multidisc set.')
                logger.info('isMultiDisc "{0}"'.format(MDSet.isMultiDisc))
                logger.info('setName     "{0}"'.format(MDSet.setName))
                logger.info('discName    "{0}"'.format(MDSet.discName))
                logger.info('extension   "{0}"'.format(MDSet.extension))
                logger.info('order       "{0}"'.format(MDSet.order))
                launcher_report.write('  ROM belongs to a multidisc set.')
                
                # >> Check if the set is already in launcher ROMs.
                MultiDisc_rom_id = None
                for new_rom in new_roms:
                    temp_FN = new_rom.get_file()
                    if temp_FN.getBase() == MDSet.setName:
                        MultiDiscInROMs  = True
                        MultiDisc_rom    = new_rom
                        break

                logger.info('MultiDiscInROMs is {0}'.format(MultiDiscInROMs))

                # >> If the set is not in the ROMs then this ROM is the first of the set.
                # >> Add the set
                if not MultiDiscInROMs:
                    logger.info('First ROM in the set. Adding to ROMs ...')
                    # >> Manipulate ROM so filename is the name of the set
                    ROM_dir = io.FileName(ROM_file.getDir())
                    ROM_file_original = ROM_file
                    ROM_temp = ROM_dir.pjoin(MDSet.setName)
                    logger.info('ROM_temp P "{0}"'.format(ROM_temp.getPath()))
                    ROM_file = ROM_temp
                # >> If set already in ROMs, just add this disk into the set disks field.
                else:
                    logger.info('Adding additional disk "{0}"'.format(MDSet.discName))
                    MultiDisc_rom.add_disk(MDSet.discName)
                    # >> Reorder disks like Disk 1, Disk 2, ...
                    
                    # >> Process next file
                    logger.info('Processing next file ...')
                    continue
            elif MDSet.isMultiDisc and not launcher_multidisc:
                launcher_report.write('  ROM belongs to a multidisc set but Multidisc support is disabled.')
            else:
                launcher_report.write('  ROM does not belong to a multidisc set.')
 
            # --- Check that ROM is not already in the list of ROMs ---
            # >> If file already in ROM list skip it
            self.progress_dialog.updateMessages(file_text, 'Checking if ROM is not already in collection...')
            repeatedROM = False
            for rom in roms:
                rpath = rom.get_file() 
                if rpath == ROM_file: 
                    repeatedROM = True
        
            if repeatedROM:
                launcher_report.write('  File already into launcher ROM list. Skipping file.')
                continue
            else:
                launcher_report.write('  File not in launcher ROM list. Processing it ...')

            # --- Ignore BIOS ROMs ---
            # Name of bios is: '[BIOS] Rom name example (Rev A).zip'
            if self.settings['scan_ignore_bios']:
                BIOS_re = re.findall('\[BIOS\]', ROM_file.getBase())
                if len(BIOS_re) > 0:
                    logger.info("BIOS detected. Skipping ROM '{0}'".format(ROM_file.getPath()))
                    continue

            # ~~~~~ Process new ROM and add to the list ~~~~~
            # --- Create new rom dictionary ---
            # >> Database always stores the original (non transformed/manipulated) path
            new_rom = ROM()
            new_rom.set_file(ROM_file)
                        
            if extra_ROM_flag: new_rom.set_as_extra_ROM()
            
            # checksums
            ROM_checksums = ROM_file_original if MDSet.isMultiDisc and launcher_multidisc else ROM_file

            scraping_succeeded = True
            self.progress_dialog.updateMessages(file_text, 'Scraping {0}...'.format(ROM_file.getBaseNoExt()))
            try:
                self.scraping_strategy.scanner_process_ROM(new_rom, ROM_checksums)
            except Exception as ex:
                scraping_succeeded = False        
                logger.error('(Exception) Object type "{}"'.format(type(ex)))
                logger.error('(Exception) Message "{}"'.format(str(ex)))
                logger.warning('Could not scrape "{}"'.format(ROM_file.getBaseNoExt()))
                #logger.debug(traceback.format_exc())
            
            if not scraping_succeeded and skip_if_scraping_failed:
                kodi.display_user_message({
                    'dialog': KODI_MESSAGE_NOTIFY_WARN,
                    'msg': 'Scraping "{}" failed. Skipping.'.format(ROM_file.getBaseNoExt())
                })
            else:
                # --- This was the first ROM in a multidisc set ---
                if launcher_multidisc and MDSet.isMultiDisc and not MultiDiscInROMs:
                    logger.info('Adding to ROMs dic first disk "{0}"'.format(MDSet.discName))
                    new_rom.add_disk(MDSet.discName)
                
                new_roms.append(new_rom)
            
            # ~~~ Check if user pressed the cancel button ~~~
            if self.progress_dialog.isCanceled():
                self.progress_dialog.endProgress()
                kodi.dialogger.OK('Stopping ROM scanning. No changes have been made.')
                logger.info('User pressed Cancel button when scanning ROMs. ROM scanning stopped.')
                return None
            
            num_items_checked += 1
           
        self.progress_dialog.endProgress()
        return new_roms

class SteamScanner(RomScannerStrategy):
    
    # ~~~ Scan for new items not yet in the rom collection ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def _getCandidates(self, launcher_report, rom_path = None):
               
        logger.debug('Reading Steam account')
        self.progress_dialog.startProgress('Reading Steam account...')

        apikey = self.settings['steam-api-key']
        steamid = self.launcher.get_steam_id()
        url = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={}&steamid={}&include_appinfo=1'.format(apikey, steamid)
        
        self.progress_dialog.updateProgress(70)
        body = net_get_URL_original(url)
        self.progress_dialog.updateProgress(80)
        
        steamJson = json.loads(body)
        games = steamJson['response']['games']
        
        self.progress_dialog.endProgress()
        return games

    # --- Remove dead entries -----------------------------------------------------------------
    def _removeDeadRoms(self, candidates, roms):
    
        if roms is None or len(roms) == 0:
            logger.info('Launcher is empty. No dead ROM check.')
            return 0

        logger.debug('Starting dead items scan')
        num_roms = len(roms)
        num_removed_roms = 0
        i = 0
            
        self.progress_dialog.startProgress('Checking for dead ROMs ...', num_roms)
        
        steamGameIds = set(steamGame['appid'] for steamGame in candidates)

        for rom in reversed(roms):
            romSteamId = rom.get_custom_attribute('steamid')
            
            logger.debug('Searching {0}'.format(romSteamId))
            self.progress_dialog.updateProgress(i)
            i += 1

            if romSteamId not in steamGameIds:
                logger.debug('Not found. Deleting from DB: "{0}"'.format(rom.get_name()))
                roms.remove(rom)
                num_removed_roms += 1
            
        self.progress_dialog.endProgress()

        return num_removed_roms

    def _processFoundItems(self, items, roms, launcher_report):
        
        if items is None or len(items) == 0:
            logger.info('No steam games available.')
            return []

        new_roms = []

        num_games = len(items)
        num_items_checked = 0
            
        self.progress_dialog.startProgress('Checking for new ROMs ...', num_games)
        steamIdsAlreadyInCollection = set(rom.get_custom_attribute('steamid') for rom in roms)
        
        for steamGame, extra_ROM_flag in items:
            
            steamId = steamGame['appid']
            logger.debug('Searching {} with #{}'.format(steamGame['name'], steamId))
            self.progress_dialog.updateProgress(num_items_checked, steamGame['name'])
            
            if steamId not in steamIdsAlreadyInCollection:
                
                logger.debug('========== Processing Steam game ==========')
                launcher_report.write('>>> title: {}'.format(steamGame['name']))
                launcher_report.write('>>> ID: {}'.format(steamGame['appid']))
        
                logger.debug('Not found. Item {} is new'.format(steamGame['name']))

                launcher_path = self.launcher.get_rom_path()
                fake_file_name = text.str_to_filename_str(steamGame['name'])
                romPath = launcher_path.pjoin('{0}.rom'.format(fake_file_name))

                # ~~~~~ Process new ROM and add to the list ~~~~~
                # --- Create new rom dictionary ---
                # >> Database always stores the original (non transformed/manipulated) path
                new_rom  = ROM()
                new_rom.set_file(romPath)

                if extra_ROM_flag: new_rom.set_as_extra_ROM()
            
                new_rom.set_custom_attribute('steamid', steamGame['appid'])
                new_rom.set_custom_attribute('steam_name', steamGame['name'])  # so that we always have the original name
                new_rom.set_name(steamGame['name'])
        
                scraping_succeeded = True
                self.progress_dialog.updateMessages(steamGame['name'], 'Scraping {}...'.format(steamGame['name']))
                try:
                    self.scraping_strategy.scanner_process_ROM(new_rom, None)
                except Exception as ex:
                    scraping_succeeded = False        
                    logger.error('(Exception) Object type "{}"'.format(type(ex)))
                    logger.error('(Exception) Message "{}"'.format(str(ex)))
                    logger.warning('Could not scrape "{}"'.format(steamGame['name']))
                    #logger.debug(traceback.format_exc())
                
                if not scraping_succeeded and skip_if_scraping_failed:
                    kodi.display_user_message({
                        'dialog': KODI_MESSAGE_NOTIFY_WARN,
                        'msg': 'Scraping "{}" failed. Skipping.'.format(steamGame['name'])
                    })
                else:
                    new_roms.append(new_rom)
                            
                # ~~~ Check if user pressed the cancel button ~~~
                if self._isProgressCanceled():
                    self.progress_dialog.endProgress()
                    kodi.dialogger.OK('Stopping ROM scanning. No changes have been made.')
                    logger.info('User pressed Cancel button when scanning ROMs. ROM scanning stopped.')
                    return None
            
                num_items_checked += 1

        self.progress_dialog.endProgress()    
        return new_roms

class NvidiaStreamScanner(RomScannerStrategy):

    # ~~~ Scan for new items not yet in the rom collection ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def _getCandidates(self, launcher_report, rom_path = None):
        logger.debug('Reading Nvidia GameStream server')
        self.progress_dialog.startProgress('Reading Nvidia GameStream server...')

        server_host = self.launcher.get_server()
        certificates_path = self.launcher.get_certificates_path()

        streamServer = GameStreamServer(server_host, certificates_path, False)
        connected = streamServer.connect()

        if not connected:
            kodi.notify_error('Unable to connect to gamestream server')
            return None

        self.progress_dialog.updateProgress(50)
        games = streamServer.getApps()
                
        self.progress_dialog.endProgress()
        return games

    # --- Remove dead entries -----------------------------------------------------------------
    def _removeDeadRoms(self, candidates, roms):
    
        if roms is None or len(roms) == 0:
            logger.info('Launcher is empty. No dead ROM check.')
            return 0

        logger.debug('Starting dead items scan')
        num_roms = len(roms)
        num_removed_roms = 0
        i = 0
            
        self.progress_dialog.startProgress('Checking for dead ROMs ...', num_roms)
        
        streamIds = set(streamableGame['ID'] for streamableGame in candidates)

        for rom in reversed(roms):
            romStreamId = rom.get_custom_attribute('streamid')
            
            logger.debug('Searching {0}'.format(romStreamId))
            self.progress_dialog.updateProgress(i)
            i += 1

            if romStreamId not in streamIds:
                logger.debug('Not found. Deleting from DB {0}'.format(rom.get_name()))
                roms.remove(rom)
                num_removed_roms += 1
            
        self.progress_dialog.endProgress()

        return num_removed_roms

    def _processFoundItems(self, items, roms, launcher_report):
        if items is None or len(items) == 0:
            logger.info('No Nvidia Gamestream games available.')
            return []

        new_roms = []

        num_games = len(items)
        num_items_checked = 0
            
        self.progress_dialog.startProgress('Checking for new ROMs ...', num_games)
        streamIdsAlreadyInCollection = set(rom.get_custom_attribute('streamid') for rom in roms)
        skip_if_scraping_failed = self.settings['scan_skip_on_scraping_failure']
        
        for streamableGame, extra_ROM_flag in items:
            
            streamId = streamableGame['ID']
            logger.debug('Searching {} with #{}'.format(streamableGame['AppTitle'], streamId))

            self.progress_dialog.updateProgress(num_items_checked, streamableGame['AppTitle'])
            
            if streamId in streamIdsAlreadyInCollection:
                logger.debug('Game "{}" with #{} already in collection'.format(streamableGame['AppTitle'], streamId))
                continue
                
            logger.debug('========== Processing Nvidia Gamestream game ==========')
            launcher_report.write('>>> title: {0}'.format(streamableGame['AppTitle']))
            launcher_report.write('>>> ID: {0}'.format(streamableGame['ID']))
    
            logger.debug('Not found. Item {0} is new'.format(streamableGame['AppTitle']))

            launcher_path = self.launcher.get_rom_path()
            fake_file_name = text.str_to_filename_str(streamableGame['AppTitle'])
            romPath = launcher_path.pjoin('{0}.rom'.format(fake_file_name))

            # ~~~~~ Process new ROM and add to the list ~~~~~
            # --- Create new rom dictionary ---
            # >> Database always stores the original (non transformed/manipulated) path
            new_rom  = ROM()
            new_rom.set_file(romPath)

            if extra_ROM_flag: new_rom.set_as_extra_ROM()
            
            new_rom.set_custom_attribute('streamid',        streamableGame['ID'])
            new_rom.set_custom_attribute('gamestream_name', streamableGame['AppTitle'])  # so that we always have the original name
            new_rom.set_name(streamableGame['AppTitle'])
            
            scraping_succeeded = True
            self.progress_dialog.updateMessages(streamableGame['AppTitle'], 'Scraping {0}...'.format(streamableGame['AppTitle']))
            try:
                self.scraping_strategy.scanner_process_ROM(new_rom, None)
            except Exception as ex:
                scraping_succeeded = False        
                logger.error('(Exception) Object type "{}"'.format(type(ex)))
                logger.error('(Exception) Message "{}"'.format(str(ex)))
                logger.warning('Could not scrape "{}"'.format(streamableGame['AppTitle']))
                #logger.debug(traceback.format_exc())
            
            if not scraping_succeeded and skip_if_scraping_failed:
                kodi.display_user_message({
                    'dialog': KODI_MESSAGE_NOTIFY_WARN,
                    'msg': 'Scraping "{}" failed. Skipping.'.format(streamableGame['AppTitle'])
                })
            else:
                new_roms.append(new_rom)
                
            # ~~~ Check if user pressed the cancel button ~~~
            if self.progress_dialog.isCanceled():
                self.progress_dialog.endProgress()
                kodi.dialogger.OK('Stopping ROM scanning. No changes have been made.')
                logger.info('User pressed Cancel button when scanning ROMs. ROM scanning stopped.')
                return None
            
            num_items_checked += 1

        self.progress_dialog.endProgress()
        return new_roms
    
# #################################################################################################
# #################################################################################################
# DAT files and ROM audit
# #################################################################################################
# #################################################################################################
class RomDatFileScanner(object):
    def __init__(self, settings):
        self.settings = settings
        super(RomDatFileScanner, self).__init__()

    #
    # Helper function to update ROMs No-Intro status if user configured a No-Intro DAT file.
    # Dictionaries are mutable, so roms can be changed because passed by assigment.
    # This function also creates the Parent/Clone indices:
    #   1) ADDON_DATA_DIR/db_ROMs/roms_base_noext_PClone_index.json
    #   2) ADDON_DATA_DIR/db_ROMs/roms_base_noext_parents.json
    #
    # A) If there are Unkown ROMs, a fake rom with name [Unknown ROMs] and id UNKNOWN_ROMS_PARENT_ID
    #    is created. This fake ROM is the parent of all Unknown ROMs.
    #    This fake ROM is added to roms_base_noext_parents.json database.
    #    This fake ROM is not present in the main JSON ROM database.
    # 
    # Returns:
    #   True  -> ROM audit was OK
    #   False -> There was a problem with the audit.
    #
    #def _roms_update_NoIntro_status(self, roms, nointro_xml_file_io.FileName):
    def update_roms_NoIntro_status(self, launcher, roms):
        __debug_progress_dialogs = False
        __debug_time_step = 0.0005

        # --- Reset the No-Intro status and removed No-Intro missing ROMs ---
        audit_have = audit_miss = audit_unknown = 0
        self._startProgressPhase('Advanced Emulator Launcher', 'Deleting Missing/Dead ROMs and clearing flags ...')
        self.roms_reset_NoIntro_status(launcher, roms)
        self._updateProgress(100)
        if __debug_progress_dialogs: time.sleep(0.5)

        # --- Check if DAT file exists ---
        nointro_xml_file_io.FileName = launcher.get_nointro_xml_filepath()
        if not nointro_xml_file_io.FileName.exists():
            logger.warning('_roms_update_NoIntro_status() Not found {0}'.format(nointro_xml_file_io.FileName.getPath()))
            return False
        
        self._updateProgress(0, 'Loading No-Intro/Redump XML DAT file ...')
        roms_nointro = audit_load_NoIntro_XML_file(nointro_xml_file_io.FileName)
        self._updateProgress(100)

        if __debug_progress_dialogs: time.sleep(0.5)
        if not roms_nointro:
            logger.warning('_roms_update_NoIntro_status() Error loading {0}'.format(nointro_xml_file_io.FileName.getPath()))
            return False

        # --- Remove BIOSes from No-Intro ROMs ---
        if self.settings['scan_ignore_bios']:
            logger.info('_roms_update_NoIntro_status() Removing BIOSes from No-Intro ROMs ...')
            self._updateProgress(0, 'Removing BIOSes from No-Intro ROMs ...')
            num_items = len(roms_nointro)
            item_counter = 0
            filtered_roms_nointro = {}
            for rom_id in roms_nointro:
                rom_data = roms_nointro[rom_id]
                BIOS_str_list = re.findall('\[BIOS\]', rom_data['name'])
                if not BIOS_str_list:
                    filtered_roms_nointro[rom_id] = rom_data
                else:
                    logger.debug('_roms_update_NoIntro_status() Removed BIOS "{0}"'.format(rom_data['name']))
                item_counter += 1
                self._updateProgress((item_counter*100)/num_items)
                if __debug_progress_dialogs: time.sleep(__debug_time_step)
            roms_nointro = filtered_roms_nointro
            self._updateProgress(100)
        else:
            logger.info('_roms_update_NoIntro_status() User wants to include BIOSes.')

        # --- Put No-Intro ROM names in a set ---
        # >> Set is the fastest Python container for searching elements (implements hashed search).
        # >> No-Intro names include tags
        self._updateProgress(0, 'Creating No-Intro and ROM sets ...')
        roms_nointro_set = set(roms_nointro.keys())
        roms_set = set()
        for rom in roms:
            # >> Use the ROM basename.
            ROM_FileName = rom.get_file()
            roms_set.add(ROM_FileName.getBaseNoExt())
        self._updateProgress(100)
        if __debug_progress_dialogs: time.sleep(0.5)

        # --- Traverse Launcher ROMs and check if they are in the No-Intro ROMs list ---
        self._updateProgress(0, 'Audit Step 1/4: Checking Have and Unknown ROMs ...')
        num_items = len(roms)
        item_counter = 0
        for rom in roms:
            ROM_FileName = rom.get_file()
            if ROM_FileName.getBaseNoExt() in roms_nointro_set:
                rom.set_nointro_status(NOINTRO_STATUS_HAVE)
                audit_have += 1
                logger.debug('_roms_update_NoIntro_status() HAVE    "{0}"'.format(ROM_FileName.getBaseNoExt()))
            else:
                rom.set_nointro_status(NOINTRO_STATUS_UNKNOWN)
                audit_unknown += 1
                logger.debug('_roms_update_NoIntro_status() UNKNOWN "{0}"'.format(ROM_FileName.getBaseNoExt()))
            item_counter += 1
            self._updateProgress((item_counter*100)/num_items)
            if __debug_progress_dialogs: time.sleep(__debug_time_step)
        self._updateProgress(100)

        # --- Mark Launcher dead ROMs as missing ---
        self._updateProgress(0, 'Audit Step 2/4: Checking Missing ROMs ...')
        num_items = len(roms)
        item_counter = 0
        for rom in roms:
            ROM_FileName = rom.get_file()
            if not ROM_FileName.exists():
                rom.set_nointro_status(NOINTRO_STATUS_MISS)
                audit_miss += 1
                logger.debug('_roms_update_NoIntro_status() MISSING "{0}"'.format(ROM_FileName.getBaseNoExt()))
            item_counter += 1
            self._updateProgress((item_counter*100)/num_items)
            if __debug_progress_dialogs: time.sleep(__debug_time_step)
        self._updateProgress(100)

        # --- Now add missing ROMs to Launcher ---
        # >> Traverse the No-Intro set and add the No-Intro ROM if it's not in the Launcher
        # >> Added/Missing ROMs have their own romID.
        self._updateProgress(0, 'Audit Step 3/4: Adding Missing ROMs ...')
        num_items = len(roms_nointro_set)
        item_counter = 0
        ROMPath = launcher.get_rom_path()
        for nointro_rom in sorted(roms_nointro_set):
            # logger.debug('_roms_update_NoIntro_status() Checking "{0}"'.format(nointro_rom))
            if nointro_rom not in roms_set:
                # Add new "fake" missing ROM. This ROM cannot be launched!
                # Added ROMs have special extension .nointro
                rom = ROM()
                rom.set_file(ROMPath.pjoin(nointro_rom + '.nointro'))
                rom.set_name(nointro_rom)
                rom.set_nointro_status(NOINTRO_STATUS_MISS)
                roms.append(rom)
                audit_miss += 1
                logger.debug('_roms_update_NoIntro_status() ADDED   "{0}"'.format(rom.get_name()))
                # logger.debug('_roms_update_NoIntro_status()    OP   "{0}"'.format(rom['filename']))
            item_counter += 1
            self._updateProgress((item_counter*100)/num_items)
            if __debug_progress_dialogs: time.sleep(__debug_time_step)
        self._updateProgress(100)

        # --- Detect if the DAT file has PClone information or not ---
        dat_pclone_dic = audit_make_NoIntro_PClone_dic(roms_nointro)
        num_dat_clones = 0
        for parent_name in dat_pclone_dic: num_dat_clones += len(dat_pclone_dic[parent_name])
        logger.verb('No-Intro/Redump DAT has {0} clone ROMs'.format(num_dat_clones))

        # --- Generate main pclone dictionary ---
        # >> audit_unknown_roms is an int of list = ['Parents', 'Clones']
        # logger.debug("settings['audit_unknown_roms'] = {0}".format(self.settings['audit_unknown_roms']))
        unknown_ROMs_are_parents = True if self.settings['audit_unknown_roms'] == 0 else False
        logger.debug('unknown_ROMs_are_parents = {0}'.format(unknown_ROMs_are_parents))
        # if num_dat_clones == 0 and self.settings['audit_create_pclone_groups']:
        #     # --- If DAT has no PClone information and user want then generate filename-based PClone groups ---
        #     # >> This feature is taken from NARS (NARS Advanced ROM Sorting)
        #     logger.verb('Generating filename-based Parent/Clone groups')
        #     pDialog(0, 'Building filename-based Parent/Clone index ...')
        #     roms_pclone_index = audit_generate_filename_PClone_index(roms, roms_nointro, unknown_ROMs_are_parents)
        #     pDialog(100)
        #     if __debug_progress_dialogs: time.sleep(0.5)
        # else:
        #     # --- Make a DAT-based Parent/Clone index ---
        #     # >> Here we build a roms_pclone_index with info from the DAT file. 2 issues:
        #     # >> A) Redump DATs do not have cloneof information.
        #     # >> B) Also, it is at this point where a region custom parent may be chosen instead of
        #     # >>    the default one.
        #     logger.verb('Generating DAT-based Parent/Clone groups')
        #     pDialog(0, 'Building DAT-based Parent/Clone index ...')
        #     roms_pclone_index = audit_generate_DAT_PClone_index(roms, roms_nointro, unknown_ROMs_are_parents)
        #     pDialog(100)
        #     if __debug_progress_dialogs: time.sleep(0.5)

        # --- Make a DAT-based Parent/Clone index ---
        # >> For 0.9.7 only use the DAT to make the PClone groups. In 0.9.8 decouple the audit
        # >> code from the PClone generation code.
        logger.verb('Generating DAT-based Parent/Clone groups')
        self._updateProgress(0, 'Building DAT-based Parent/Clone index ...')
        roms_pclone_index = audit_generate_DAT_PClone_index(roms, roms_nointro, unknown_ROMs_are_parents)
        self._updateProgress(100)
        if __debug_progress_dialogs: time.sleep(0.5)

        # --- Make a Clone/Parent index ---
        # >> This is made exclusively from the Parent/Clone index
        self._updateProgress(0, 'Building Clone/Parent index ...')
        clone_parent_dic = {}
        for parent_id in roms_pclone_index:
            for clone_id in roms_pclone_index[parent_id]:
                clone_parent_dic[clone_id] = parent_id
        self._updateProgress(100)
        if __debug_progress_dialogs: time.sleep(0.5)

        # --- Set ROMs pclone_status flag and update launcher statistics ---
        self._updateProgress(0, 'Audit Step 4/4: Setting Parent/Clone status and cloneof fields...')
        num_items = len(roms)
        item_counter = 0
        audit_parents = audit_clones = 0
        for rom in roms:
            rom_id = rom.get_id()
            if rom_id in roms_pclone_index:
                rom.set_pclone_status(PCLONE_STATUS_PARENT)
                audit_parents += 1
            else:
                rom.set_clone(clone_parent_dic[rom_id])
                rom.set_pclone_status(PCLONE_STATUS_CLONE)
                audit_clones += 1
            item_counter += 1
            self._updateProgress((item_counter*100)/num_items)
            if __debug_progress_dialogs: time.sleep(__debug_time_step)
        self._updateProgress(100)

        launcher.set_audit_stats(len(roms), audit_parents, audit_clones, audit_have, audit_miss, audit_unknown)

        # --- Make a Parent only ROM list and save JSON ---
        # >> This is to speed up rendering of launchers in 1G1R display mode
        self._updateProgress(0, 'Building Parent/Clone index and Parent dictionary ...')
        parent_roms = audit_generate_parent_ROMs_dic(roms, roms_pclone_index)
        self._updateProgress(100)
        if __debug_progress_dialogs: time.sleep(0.5)

        # --- Save JSON databases ---
        self._updateProgress(0, 'Saving NO-Intro/Redump JSON databases ...')
        fs_write_JSON_file(ROMs_dir, launcher['roms_base_noext'] + '_index_PClone', roms_pclone_index)
        self._updateProgress(30)
        fs_write_JSON_file(ROMS_DIR, launcher['roms_base_noext'] + '_index_CParent', clone_parent_dic)
        self._updateProgress(60)
        fs_write_JSON_file(ROMS_DIR, launcher['roms_base_noext'] + '_parents', parent_roms)
        self._updateProgress(100)
        self._endProgressPhase()

        # --- Update launcher number of ROMs ---
        self.audit_have    = audit_have
        self.audit_miss    = audit_miss
        self.audit_unknown = audit_unknown
        self.audit_total   = len(roms)
        self.audit_parents = audit_parents
        self.audit_clones  = audit_clones

        # --- Report ---
        logger.info('********** No-Intro/Redump audit finished. Report ***********')
        logger.info('Have ROMs    {0:6d}'.format(self.audit_have))
        logger.info('Miss ROMs    {0:6d}'.format(self.audit_miss))
        logger.info('Unknown ROMs {0:6d}'.format(self.audit_unknown))
        logger.info('Total ROMs   {0:6d}'.format(self.audit_total))
        logger.info('Parent ROMs  {0:6d}'.format(self.audit_parents))
        logger.info('Clone ROMs   {0:6d}'.format(self.audit_clones))

        return True

    #
    # Resets the No-Intro status
    # 1) Remove all ROMs which does not exist.
    # 2) Set status of remaining ROMs to nointro_status = AUDIT_STATUS_NONE
    #
    def roms_reset_NoIntro_status_roms_reset_NoIntro_status(self, launcher, roms):
        logger.info('roms_reset_NoIntro_status() Launcher has {0} ROMs'.format(len(roms)))
        if len(roms) < 1: return

        # >> Step 1) Delete missing/dead ROMs
        num_removed_roms = self._roms_delete_missing_ROMs(roms)
        logger.info('roms_reset_NoIntro_status() Removed {0} dead/missing ROMs'.format(num_removed_roms))

        # >> Step 2) Set No-Intro status to AUDIT_STATUS_NONE and
        #            set PClone status to PCLONE_STATUS_NONE
        logger.info('roms_reset_NoIntro_status() Resetting No-Intro status of all ROMs to None')
        for rom in roms: 
            rom.set_nointro_status(AUDIT_STATUS_NONE)
            rom.set_pclone_status(PCLONE_STATUS_NONE)

        logger.info('roms_reset_NoIntro_status() Now launcher has {0} ROMs'.format(len(roms)))

        # >> Step 3) Delete PClone index and Parent ROM list.
        launcher.reset_parent_and_clone_roms()

    # Deletes missing ROMs
    #
    def _roms_delete_missing_ROMs(self, roms):
        num_removed_roms = 0
        num_roms = len(roms)
        logger.info('_roms_delete_missing_ROMs() Launcher has {0} ROMs'.format(num_roms))
        if num_roms > 0:
            logger.verb('_roms_delete_missing_ROMs() Starting dead items scan')

            for rom in reversed(roms):
            
                ROM_FileName = rom.get_file()
                if not ROM_FileName:
                    logger.debug('_roms_delete_missing_ROMs() Skip "{0}"'.format(rom.get_name()))
                    continue

                logger.debug('_roms_delete_missing_ROMs() Test "{0}"'.format(ROM_FileName.getBase()))
                # --- Remove missing ROMs ---
                if not ROM_FileName.exists():
                    logger.debug('_roms_delete_missing_ROMs() RM   "{0}"'.format(ROM_FileName.getBase()))
                    roms.remove(rom)
                    num_removed_roms += 1

            if num_removed_roms > 0:
                logger.info('_roms_delete_missing_ROMs() {0} dead ROMs removed successfully'.format(num_removed_roms))
            else:
                logger.info('_roms_delete_missing_ROMs() No dead ROMs found.')
        else:
            logger.info('_roms_delete_missing_ROMs() Launcher is empty. No dead ROM check.')

        return num_removed_roms

# #################################################################################################
# #################################################################################################
# Gamestream
# #################################################################################################
# #################################################################################################
class GameStreamServer(object):
    
    def __init__(self, host, certificates_path, debug_mode = False):
        self.host = host
        self.unique_id = random.getrandbits(16)
        self.debug_mode = debug_mode

        if certificates_path:
            self.certificates_path = certificates_path
            self.certificate_file_path = self.certificates_path.pjoin('nvidia.crt')
            self.certificate_key_file_path = self.certificates_path.pjoin('nvidia.key')
        else:
            self.certificates_path = io.FileName('')
            self.certificate_file_path = io.FileName('')
            self.certificate_key_file_path = io.FileName('')

        logger.debug('GameStreamServer() Using certificate key file {}'.format(self.certificate_key_file_path.getPath()))
        logger.debug('GameStreamServer() Using certificate file {}'.format(self.certificate_file_path.getPath()))

        self.pem_cert_data = None
        self.key_cert_data = None

    def _perform_server_request(self, end_point,  useHttps=True, parameters = None):
        
        if useHttps:
            url = "https://{0}:47984/{1}?uniqueid={2}&uuid={3}".format(self.host, end_point, self.unique_id, uuid.uuid4().hex)
        else:
            url = "http://{0}:47989/{1}?uniqueid={2}&uuid={3}".format(self.host, end_point, self.unique_id, uuid.uuid4().hex)

        if parameters:
            for key, value in parameters.iteritems():
                url = url + "&{0}={1}".format(key, value)

        handler = HTTPSClientAuthHandler(self.certificate_key_file_path.getPath(), self.certificate_file_path.getPath())
        page_data = net_get_URL_using_handler(url, handler)
    
        if page_data is None:
            return None
        
        root = ET.fromstring(page_data)
        if self.debug_mode:
            logger.debug(ET.tostring(root,encoding='utf8',method='xml'))
       
        return root

    def connect(self):
        logger.debug('Connecting to gamestream server {}'.format(self.host))
        self.server_info = self._perform_server_request("serverinfo")
        
        if not self.is_connected():
            self.server_info = self._perform_server_request("serverinfo", False)
        
        return self.is_connected()

    def is_connected(self):
        if self.server_info is None:
            logger.debug('No succesfull connection to the server has been made')
            return False

        if self.server_info.find('state') is None:
            logger.debug('Server state {0}'.format(self.server_info.attrib['status_code']))
        else:
            logger.debug('Server state {0}'.format(self.server_info.find('state').text))

        return self.server_info.attrib['status_code'] == '200'

    def get_server_version(self):
        appVersion = self.server_info.find('appversion')
        return VersionNumber(appVersion.text)
    
    def get_uniqueid(self):
        uniqueid = self.server_info.find('uniqueid').text
        return uniqueid
    
    def get_hostname(self):
        hostname = self.server_info.find('hostname').text
        return hostname

    def generatePincode(self):
        i1 = random.randint(1, 9)
        i2 = random.randint(1, 9)
        i3 = random.randint(1, 9)
        i4 = random.randint(1, 9)
    
        return '{0}{1}{2}{3}'.format(i1, i2, i3, i4)

    def is_paired(self):
        if not self.is_connected():
            logger.warning('Connect first')
            return False

        pairStatus = self.server_info.find('PairStatus')
        return pairStatus.text == '1'

    def pairServer(self, pincode):
        if not self.is_connected():
            logger.warning('Connect first')
            return False

        version = self.get_server_version()
        logger.info("Pairing with server generation: {0}".format(version.getFullString()))

        majorVersion = version.getMajor()
        if majorVersion >= 7:
            # Gen 7+ uses SHA-256 hashing
            hashAlgorithm = HashAlgorithm(256)
        else:
            # Prior to Gen 7, SHA-1 is used
            hashAlgorithm = HashAlgorithm(1)
        logger.debug('Pin {0}'.format(pincode))

        # Generate a salt for hashing the PIN
        salt = randomBytes(16)
        # Combine the salt and pin
        saltAndPin = salt + bytearray(pincode, 'utf-8')
        # Create an AES key from them
        aes_cypher = AESCipher(saltAndPin, hashAlgorithm)

        # get certificates ready
        logger.debug('Getting local certificate files')
        client_certificate      = self.getCertificateBytes()
        client_key_certificate  = self.getCertificateKeyBytes()
        certificate_signature   = getCertificateSignature(client_certificate)

        # Start pairing with server
        logger.debug('Start pairing with server')
        pairing_result = self._perform_server_request('pair', False, {
            'devicename': 'ael', 
            'updateState': 1, 
            'phrase': 'getservercert', 
            'salt': binascii.hexlify(salt),
            'clientcert': binascii.hexlify(client_certificate)
            })

        if pairing_result is None:
            logger.error('Failed to pair with server. No XML received.')
            return False

        isPaired = pairing_result.find('paired').text
        if isPaired != '1':
            logger.error('Failed to pair with server. Server returned failed state.')
            return False

        server_cert_data = pairing_result.find('plaincert').text
        if server_cert_data is None:
            logger.error('Failed to pair with server. A different pairing session might be in progress.')
            return False
        
        # Generate a random challenge and encrypt it with our AES key
        challenge = randomBytes(16)
        encrypted_challenge = aes_cypher.encryptToHex(challenge)
        
        # Send the encrypted challenge to the server
        logger.debug('Sending encrypted challenge to the server')
        pairing_challenge_result = self._perform_server_request('pair', False, {
            'devicename': 'ael', 
            'updateState': 1, 
            'clientchallenge': encrypted_challenge })
        
        if pairing_challenge_result is None:
            logger.error('Failed to pair with server. No XML received.')
            return False

        isPaired = pairing_challenge_result.find('paired').text
        if isPaired != '1':
            logger.error('Failed to pair with server. Server returned failed state.')
            self._perform_server_request('unpair', False)
            return False

        # Decode the server's response and subsequent challenge
        logger.debug('Decoding server\'s response and challenge response')
        server_challenge_hex = pairing_challenge_result.find('challengeresponse').text
        server_challenge_bytes = bytearray.fromhex(server_challenge_hex)
        server_challenge_decrypted = aes_cypher.decrypt(server_challenge_bytes)
        
        server_challenge_firstbytes = server_challenge_decrypted[:hashAlgorithm.digest_size()]
        server_challenge_lastbytes  = server_challenge_decrypted[hashAlgorithm.digest_size():hashAlgorithm.digest_size()+16]

        # Using another 16 bytes secret, compute a challenge response hash using the secret, our cert sig, and the challenge
        client_secret               = randomBytes(16)
        challenge_response          = server_challenge_lastbytes + certificate_signature + client_secret
        challenge_response_hashed   = hashAlgorithm.hash(challenge_response)
        challenge_response_encrypted= aes_cypher.encryptToHex(challenge_response_hashed)
        
        # Send the challenge response to the server
        logger.debug('Sending the challenge response to the server')
        pairing_secret_response = self._perform_server_request('pair', False, {
            'devicename': 'ael', 
            'updateState': 1, 
            'serverchallengeresp': challenge_response_encrypted })
        
        if pairing_secret_response is None:
            logger.error('Failed to pair with server. No XML received.')
            return False

        isPaired = pairing_secret_response.find('paired').text
        if isPaired != '1':
            logger.error('Failed to pair with server. Server returned failed state.')
            self._perform_server_request('unpair', False)
            return False

        # Get the server's signed secret
        logger.debug('Verifiying server signature')
        server_secret_response  = bytearray.fromhex(pairing_secret_response.find('pairingsecret').text)
        server_secret           = server_secret_response[:16]
        server_signature        = server_secret_response[16:272]

        server_cert = server_cert_data.decode('hex')
        is_verified = verify_signature(str(server_secret), server_signature, server_cert)

        if not is_verified:
            # Looks like a MITM, Cancel the pairing process
            logger.error('Failed to verify signature. (MITM warning)')
            self._perform_server_request('unpair', False)
            return False

        # Ensure the server challenge matched what we expected (aka the PIN was correct)
        logger.debug('Confirming PIN with entered value')
        server_cert_signature       = getCertificateSignature(server_cert)
        server_secret_combination   = challenge + server_cert_signature + server_secret
        server_secret_hashed        = hashAlgorithm.hash(server_secret_combination)

        if server_secret_hashed != server_challenge_firstbytes:
            # Probably got the wrong PIN
            logger.error("Wrong PIN entered")
            self._perform_server_request('unpair', False)
            return False

        logger.debug('Pin is confirmed')

        # Send the server our signed secret
        logger.debug('Sending server our signed secret')
        signed_client_secret = sign_data(client_secret, client_key_certificate)
        client_pairing_secret = client_secret + signed_client_secret

        client_pairing_secret_response = self._perform_server_request('pair', False, {
            'devicename': 'ael', 
            'updateState': 1, 
            'clientpairingsecret':  binascii.hexlify(client_pairing_secret)})
        
        isPaired = client_pairing_secret_response.find('paired').text
        if isPaired != '1':
            logger.error('Failed to pair with server. Server returned failed state.')
            self._perform_server_request('unpair', False)
            return False

        # Do the initial challenge over https
        logger.debug('Initial challenge again')
        pair_challenge_response = self._perform_server_request('pair', True, {
            'devicename': 'ael', 
            'updateState': 1, 
            'phrase':  'pairchallenge'})

        isPaired = pair_challenge_response.find('paired').text
        if isPaired != '1':
            logger.error('Failed to pair with server. Server returned failed state.')
            self._perform_server_request('unpair', False)
            return False

        return True

    def getApps(self):
        apps_response = self._perform_server_request('applist', True)
        if apps_response is None:
            kodi.notify_error('Failure to connect to GameStream server')
            return []

        appnodes = apps_response.findall('App')
        apps = []
        for appnode in appnodes:
            app = {}
            for appnode_attr in appnode:
                if len(list(appnode_attr)) > 1:
                    continue
                
                xml_text = appnode_attr.text if appnode_attr.text is not None else ''
                xml_text = text.unescape_XML(xml_text)
                xml_tag  = appnode_attr.tag
           
                app[xml_tag] = xml_text
            apps.append(app)

        return apps

    def getCertificateBytes(self):
        if self.pem_cert_data:
            return self.pem_cert_data

        if not self.certificate_file_path.exists():
            logger.info('Client certificate file does not exist. Creating')
            create_self_signed_cert("NVIDIA GameStream Client", self.certificate_file_path, self.certificate_key_file_path)

        logger.info('Loading client certificate data from {0}'.format(self.certificate_file_path.getPath()))
        self.pem_cert_data = self.certificate_file_path.loadFileToStr('ascii')

        return str(self.pem_cert_data)

    def getCertificateKeyBytes(self):
        if self.key_cert_data:
            return self.key_cert_data

        if not self.certificate_key_file_path.exists():
            logger.info('Client certificate file does not exist. Creating')
            create_self_signed_cert("NVIDIA GameStream Client", self.certificate_file_path, self.certificate_key_file_path)
        logger.info('Loading client certificate data from {0}'.format(self.certificate_key_file_path.getPath()))
        self.key_cert_data = self.certificate_key_file_path.loadFileToStr('ascii')

        return str(self.key_cert_data)

    def validate_certificates(self):
        if self.certificate_file_path.exists() and self.certificate_key_file_path.exists():
            logger.debug('validate_certificates(): Certificate files exist. Done')
            return True

        certificate_files = self.certificates_path.scanFilesInPath('*.crt')
        key_files = self.certificates_path.scanFilesInPath('*.key')

        if len(certificate_files) < 1:
            logger.warning('validate_certificates(): No .crt files found at given location.')
            return False

        if not self.certificate_file_path.exists():
            logger.debug('validate_certificates(): Copying .crt file to nvidia.crt')
            certificate_files[0].copy(self.certificate_file_path)

        if len(key_files) < 1:
            logger.warning('validate_certificates(): No .key files found at given location.')
            return False

        if not self.certificate_key_file_path.exists():
            logger.debug('validate_certificates(): Copying .key file to nvidia.key')
            key_files[0].copy(certificate_key_file_path)

        return True

    @staticmethod
    def try_to_resolve_path_to_nvidia_certificates():
        home = expanduser("~")
        homePath = io.FileName(home)

        possiblePath = homePath.pjoin('Moonlight/')
        if possiblePath.exists():
            return possiblePath.getPath()

        possiblePath = homePath.pjoin('Limelight/')
        if possiblePath.exists():
            return possiblePath.getPath()

        return homePath.getPath()

#
# Class to interact with the asset engine.
# This class uses the asset_infos, dictionary of AssetInfo indexed by asset_ID
#
class AssetInfoFactory(object):
        
    def __init__(self):
        
        # default collections
        self.ASSET_INFO_ID_DICT = {} # ID -> object
        self.ASSET_INFO_KEY_DICT = {} # Key -> object
        
        self._load_asset_data()
        
    # -------------------------------------------------------------------------------------------------
    # Asset functions
    # -------------------------------------------------------------------------------------------------
    def get_all(self) -> typing.List[AssetInfo]:
        return list(self.ASSET_INFO_ID_DICT.values())

    def get_asset_info(self, asset_ID):
        asset_info = self.ASSET_INFO_ID_DICT.get(asset_ID, None)

        if asset_info is None:
            logger.error('get_asset_info() Wrong asset_ID = {0}'.format(asset_ID))
            return AssetInfo()

        return asset_info
    
    # Returns the corresponding assetinfo object for the
    # given key (eg: 's_icon')
    def get_asset_info_by_key(self, asset_key):
        asset_info = self.ASSET_INFO_KEY_DICT.get(asset_key, None)

        if asset_info is None:
            logger.error('get_asset_info_by_key() Wrong asset_key = {0}'.format(asset_key))
            return AssetInfo()

        return asset_info 
          
    def get_assets_for_type(self, asset_kind) -> typing.List[AssetInfo]:
        if asset_kind == KIND_ASSET_CATEGORY:
            return self.get_asset_list_by_IDs(CATEGORY_ASSET_ID_LIST)
        if asset_kind == KIND_ASSET_COLLECTION:
            return self.get_asset_list_by_IDs(COLLECTION_ASSET_ID_LIST)
        if asset_kind == KIND_ASSET_LAUNCHER:
            return self.get_asset_list_by_IDs(LAUNCHER_ASSET_ID_LIST)
        if asset_kind == KIND_ASSET_ROM:
            return self.get_asset_list_by_IDs(ROM_ASSET_ID_LIST)
        return []

    def get_asset_kinds_for_roms(self):
        rom_asset_kinds = []
        for rom_asset_id in ROM_ASSET_ID_LIST:
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
        kind = ASSET_KEYS_TO_CONSTANTS[name_key]

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
    def asset_get_dialog_extension_list(self, exts):
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

        if   asset_ID == ASSET_ICON_ID:       asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_icon')
        elif asset_ID == ASSET_FANART_ID:     asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_fanart')
        elif asset_ID == ASSET_BANNER_ID:     asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_banner')
        elif asset_ID == ASSET_POSTER_ID:     asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_poster')
        elif asset_ID == ASSET_CLEARLOGO_ID:  asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_clearlogo')
        elif asset_ID == ASSET_CONTROLLER_ID: asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_controller')
        elif asset_ID == ASSET_TRAILER_ID:    asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_trailer')
        elif asset_ID == ASSET_TITLE_ID:      asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_title')
        elif asset_ID == ASSET_SNAP_ID:       asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_snap')
        elif asset_ID == ASSET_BOXFRONT_ID:   asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_boxfront')
        elif asset_ID == ASSET_BOXBACK_ID:    asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_boxback')
        elif asset_ID == ASSET_CARTRIDGE_ID:  asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_cartridge')
        elif asset_ID == ASSET_FLYER_ID:      asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_flyer')
        elif asset_ID == ASSET_MAP_ID:        asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_map')
        elif asset_ID == ASSET_MANUAL_ID:     asset_path_noext_FN = AssetPath.pjoin(asset_base_noext + objectID_str + '_manual')
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
        local_asset_list = [''] * len(ROM_ASSET_ID_LIST)
        for i, asset_kind in enumerate(ROM_ASSET_ID_LIST):
            AInfo = g_assetFactory.get_asset_info(asset_kind)
            if not enabled_ROM_asset_list[i]:
                logger.debug('assets_search_local_assets() Disabled {0:<9}'.format(AInfo.name))
                continue
            asset_path = launcher.get_asset_path(AInfo)
            local_asset = misc_look_for_file(asset_path, ROMFile.getBaseNoExt(), AInfo.exts)

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
        duplicated_bool_list = [False] * len(ROM_ASSET_ID_LIST)
        AInfo_first = g_assetFactory.get_asset_info(ROM_ASSET_ID_LIST[0])
        path_first_asset_FN = io.FileName(launcher[AInfo_first.path_key])
        logger.debug('assets_get_ROM_asset_path() path_first_asset "{0}"'.format(path_first_asset_FN.getPath()))
        for i, asset_kind in enumerate(ROM_ASSET_ID_LIST):
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
        a.id                            = ASSET_ICON_ID
        a.key                           = 's_icon'
        a.default_key                   = 'default_icon'
        a.rom_default_key               = 'roms_default_icon'
        a.name                          = 'Icon'
        a.name_plural                   = 'Icons'
        a.fname_infix                   = 'icon'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_icon'        
        self.ASSET_INFO_ID_DICT[a.id]   = a
        self.ASSET_INFO_KEY_DICT[a.key] = a

        a = AssetInfo()
        a.id                            = ASSET_FANART_ID
        a.key                           = 's_fanart'
        a.default_key                   = 'default_fanart'
        a.rom_default_key               = 'roms_default_fanart'
        a.name                          = 'Fanart'
        a.plural                        = 'Fanarts'
        a.fname_infix                   = 'fanart'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_fanart'
        self.ASSET_INFO_ID_DICT[a.id]   = a
        self.ASSET_INFO_KEY_DICT[a.key] = a

        a = AssetInfo()
        a.id                            = ASSET_BANNER_ID
        a.key                           = 's_banner'
        a.default_key                   = 'default_banner'
        a.rom_default_key               = 'roms_default_banner'
        a.name                          = 'Banner'
        a.description                   = 'Banner / Marquee'
        a.plural                        = 'Banners'
        a.fname_infix                   = 'banner'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_banner'
        self.ASSET_INFO_ID_DICT[a.id]   = a
        self.ASSET_INFO_KEY_DICT[a.key] = a

        a = AssetInfo()        
        a.id                            = ASSET_POSTER_ID
        a.key                           = 's_poster'
        a.default_key                   = 'default_poster'
        a.rom_default_key               = 'roms_default_poster'
        a.name                          = 'Poster'
        a.plural                        = 'Posters'
        a.fname_infix                   = 'poster'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_poster'
        self.ASSET_INFO_ID_DICT[a.id]   = a
        self.ASSET_INFO_KEY_DICT[a.key] = a

        a = AssetInfo()
        a.id                            = ASSET_CLEARLOGO_ID
        a.key                           = 's_clearlogo'
        a.default_key                   = 'default_clearlogo'
        a.rom_default_key               = 'roms_default_clearlogo'
        a.name                          = 'Clearlogo'
        a.plural                        = 'Clearlogos'
        a.fname_infix                   = 'clearlogo'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_clearlogo'
        self.ASSET_INFO_ID_DICT[a.id]   = a
        self.ASSET_INFO_KEY_DICT[a.key] = a

        a = AssetInfo()
        a.id                            = ASSET_CONTROLLER_ID
        a.key                           = 's_controller'
        a.default_key                   = 'default_controller'
        a.name                          = 'Controller'
        a.plural                        = 'Controllers'
        a.fname_infix                   = 'controller'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_controller'
        self.ASSET_INFO_ID_DICT[a.id]   = a
        self.ASSET_INFO_KEY_DICT[a.key] = a

        a = AssetInfo()
        a.id                            = ASSET_TRAILER_ID
        a.key                           = 's_trailer'
        a.name                          = 'Trailer'
        a.plural                        = 'Trailers'
        a.fname_infix                   = 'trailer'
        a.kind_str                      = 'video'
        a.exts                          = self.asset_get_filesearch_extension_list(TRAILER_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(TRAILER_EXTENSION_LIST)
        a.path_key                      = 'path_trailer'
        self.ASSET_INFO_ID_DICT[a.id]   = a
        self.ASSET_INFO_KEY_DICT[a.key] = a

        a = AssetInfo()
        a.id                            = ASSET_TITLE_ID
        a.key                           = 's_title'
        a.default_key                   = 'default_title'
        a.rom_default_key               = 'roms_default_title'
        a.name                          = 'Title'
        a.plural                        = 'Titles'
        a.fname_infix                   = 'title'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_title'
        self.ASSET_INFO_ID_DICT[a.id]   = a
        self.ASSET_INFO_KEY_DICT[a.key] = a

        a = AssetInfo()
        a.id                            = ASSET_SNAP_ID
        a.key                           = 's_snap'
        a.name                          = 'Snap'
        a.plural                        = 'Snaps'
        a.fname_infix                   = 'snap'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_snap'
        self.ASSET_INFO_ID_DICT[a.id]   = a
        self.ASSET_INFO_KEY_DICT[a.key] = a

        a = AssetInfo()
        a.id                            = ASSET_BOXFRONT_ID
        a.key                           = 's_boxfront'
        a.name                          = 'Boxfront'
        a.description                   = 'Boxfront / Cabinet'
        a.plural                        = 'Boxfronts'
        a.fname_infix                   = 'boxfront'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_boxfront'
        self.ASSET_INFO_ID_DICT[a.id]   = a
        self.ASSET_INFO_KEY_DICT[a.key] = a

        a = AssetInfo()
        a.id                            = ASSET_BOXBACK_ID
        a.key                           = 's_boxback'
        a.name                          = 'Boxback'
        a.description                   = 'Boxback / CPanel'
        a.plural                        = 'Boxbacks'
        a.fname_infix                   = 'boxback'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_boxback'
        self.ASSET_INFO_ID_DICT[a.id]   = a
        self.ASSET_INFO_KEY_DICT[a.key] = a

        a = AssetInfo()
        a.id                            = ASSET_CARTRIDGE_ID
        a.key                           = 's_cartridge'
        a.name                          = 'Cartridge'
        a.description                   = 'Cartridge / PCB'
        a.plural                        = 'Cartridges'
        a.fname_infix                   = 'cartridge'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_cartridge'
        self.ASSET_INFO_ID_DICT[a.id]   = a
        self.ASSET_INFO_KEY_DICT[a.key] = a

        a = AssetInfo()
        a.id                            = ASSET_FLYER_ID
        a.key                           = 's_flyer'
        a.name                          = 'Flyer'
        a.plural                        = 'Flyers'
        a.fname_infix                   = 'flyer'
        a.kind_str                      = 'image'
        a.fname_infix                   = 'poster'
        a.exts                          = self.asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_flyer'
        self.ASSET_INFO_ID_DICT[a.id]   = a
        self.ASSET_INFO_KEY_DICT[a.key] = a

        a = AssetInfo()
        a.id                            = ASSET_MAP_ID
        a.key                           = 's_map'
        a.name                          = 'Map'
        a.plural                        = 'Maps'
        a.fname_infix                   = 'map'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_map'
        self.ASSET_INFO_ID_DICT[a.id]   = a
        self.ASSET_INFO_KEY_DICT[a.key] = a

        a = AssetInfo()
        a.id                            = ASSET_MANUAL_ID
        a.key                           = 's_manual'
        a.name                          = 'Manual'
        a.plural                        = 'Manuals'
        a.fname_infix                   = 'manual'
        a.kind_str                      = 'manual'
        a.exts                          = self.asset_get_filesearch_extension_list(MANUAL_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(MANUAL_EXTENSION_LIST)
        a.path_key                      = 'path_manual'
        self.ASSET_INFO_ID_DICT[a.id]   = a
        self.ASSET_INFO_KEY_DICT[a.key] = a

        a = AssetInfo()
        a.id                            = ASSET_3DBOX_ID
        a.key                           = 's_3dbox'
        a.name                          = '3D Box'
        a.fname_infix                   = '3dbox'
        a.kind_str                      = 'image'
        a.exts                          = self.asset_get_filesearch_extension_list(IMAGE_EXTENSION_LIST)
        a.exts_dialog                   = self.asset_get_dialog_extension_list(IMAGE_EXTENSION_LIST)
        a.path_key                      = 'path_3dbox'
        self.ASSET_INFO_ID_DICT[a.id]   = a
        self.ASSET_INFO_KEY_DICT[a.key] = a

# --- Global object to get asset info ---
g_assetFactory = AssetInfoFactory()