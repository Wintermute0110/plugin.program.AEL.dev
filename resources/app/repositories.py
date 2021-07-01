# -*- coding: utf-8 -*-
import logging
import typing

import sqlite3
from sqlite3.dbapi2 import Cursor

from ael.settings import *
from ael.utils import text, io
from ael import constants

from resources.app import globals
from resources.app.domain import Category, ROMSet, ROM, ROMLauncherAddon, Asset, AelAddon, ROMSetScanner

logger = logging.getLogger(__name__)

# #################################################################################################
# #################################################################################################
# Data storage objects.
# #################################################################################################
# #################################################################################################
#
# * Repository class for creating and retrieveing Container/Categories/Launchers/ROM Collection objects.
#

#
# ViewRepository works with json files that contain pre-generated data
# to be shown in list containers.
#
class ViewRepository(object):

    def __init__(self, paths: AEL_Paths):
        self.paths = paths

    def find_root_items(self):
        repository_file = self.paths.ROOT_PATH
        logger.debug('find_root_items(): Loading path data from file {}'.format(repository_file.getPath()))
        if not repository_file.exists():
            logger.debug('find_root_items(): Path does not exist {}'.format(repository_file.getPath()))
            return None

        try:
            item_data = repository_file.readJson()
        except ValueError as ex:
            statinfo = repository_file.stat()
            logger.error('find_root_items(): ValueError exception in file.readJson() function')
            message = text.createError(ex)
            logger.error(message)
            logger.error('find_root_items(): Dir  {}'.format(repository_file.getPath()))
            logger.error('find_root_items(): Size {}'.format(statinfo.st_size))
            return None
        
        return item_data

    def find_items(self, collection_id) -> typing.Any:
        repository_file = self.paths.COLLECTIONS_DIR.pjoin('collection_{}.json'.format(collection_id))
        logger.debug('find_items(): Loading path data from file {}'.format(repository_file.getPath()))
        try:
            item_data = repository_file.readJson()
        except ValueError as ex:
            statinfo = repository_file.stat()
            logger.error('find_items(): ValueError exception in file.readJson() function')
            message = text.createError(ex)
            logger.error(message)
            logger.error('find_items(): Dir  {}'.format(repository_file.getPath()))
            logger.error('find_items(): Size {}'.format(statinfo.st_size))
            return None
        
        return item_data

    def store_root_view(self, view_data):
        repository_file = self.paths.ROOT_PATH
        logger.debug('store_root_view(): Storing data in file {}'.format(repository_file.getPath()))
        repository_file.writeJson(view_data)

    def store_view(self, collection_id, view_data):
        repository_file = self.paths.COLLECTIONS_DIR.pjoin('collection_{}.json'.format(collection_id))
        
        if view_data is None: 
            if repository_file.exists():
                logger.debug('store_view(): No data for file {}. Removing file'.format(repository_file.getPath()))
                repository_file.unlink()
            return

        logger.debug('store_view(): Storing data in file {}'.format(repository_file.getPath()))
        repository_file.writeJson(view_data)

#
# XmlConfigurationRepository works with original XML configuration files, which contained the 
# categories and launchers. This repository is to read these files and migrate to current solution.
#
class XmlConfigurationRepository(object):

    def __init__(self, file_path: io.FileName, debug = False):
        self.file_path = file_path
        self.debug = debug

    def get_categories(self) -> typing.Iterator[Category]:
        # --- Parse using cElementTree ---
        # >> If there are issues in the XML file (for example, invalid XML chars) ET.parse will fail
        logger.debug('XmlRepository.get_categories() Loading {0}'.format(self.file_path.getPath()))

        xml_tree = self.file_path.readXml()
        if xml_tree is None:
            return None

        xml_root = xml_tree.getroot()
        # >> Process tags in XML configuration file
        for root_element in xml_root:
            if self.debug: logger.debug('>>> Root child tag <{0}>'.format(root_element.tag))

            if not root_element.tag == 'category':
                continue

            assets = []
            category_temp = {}
            for root_child in root_element:
                # >> By default read strings
                text_XML_line = root_child.text if root_child.text is not None else ''
                text_XML_line = text.unescape_XML(text_XML_line)
                xml_tag  = root_child.tag
                if self.debug: logger.debug('>>> "{0:<11s}" --> "{1}"'.format(xml_tag, text_XML_line))
                category_temp[xml_tag] = text_XML_line
                                
                if xml_tag.startswith('s_'):
                    asset_info = constants.g_assetFactory.get_asset_info_by_key(xml_tag)
                    asset_data = { 'filepath': text_XML_line }
                    assets.append(Asset(asset_info, asset_data))
                
            # --- Add category to categories dictionary ---
            logger.debug('Adding category "{0}" to import list'.format(category_temp['m_name']))
            yield Category(category_temp, assets)

    def get_launchers(self) -> typing.Iterator[ROMSet]:    
        # --- Parse using cElementTree ---
        # >> If there are issues in the XML file (for example, invalid XML chars) ET.parse will fail
        logger.debug('XmlRepository.get_launchers() Loading {0}'.format(self.file_path.getPath()))

        xml_tree = self.file_path.readXml()
        if xml_tree is None:
            return None

        xml_root = xml_tree.getroot()
        # >> Process tags in XML configuration file
        for root_element in xml_root:
            if self.debug: logger.debug('>>> Root child tag <{0}>'.format(root_element.tag))

            if not root_element.tag == 'launcher':
                continue
            
            assets = []
            launcher_temp = {}
            for root_child in root_element:
                # >> By default read strings
                text_XML_line = root_child.text if root_child.text is not None else ''
                text_XML_line = text.unescape_XML(text_XML_line)
                xml_tag  = root_child.tag
                if self.debug: logger.debug('>>> "{0:<11s}" --> "{1}"'.format(xml_tag, text_XML_line))
                if xml_tag == 'categoryID': xml_tag = 'parent_id'                
                launcher_temp[xml_tag] = text_XML_line
                
                if xml_tag.startswith('s_'):
                    asset_info = constants.g_assetFactory.get_asset_info_by_key(xml_tag)
                    asset_data = { 'filepath': text_XML_line }
                    assets.append(Asset(asset_info, asset_data))
                    
            # --- Add launcher to launchers collection ---
            logger.debug('Adding launcher "{0}" to import list'.format(launcher_temp['m_name']))
            yield ROMSet(launcher_temp, assets)


# -------------------------------------------------------------------------------------------------
# --- Repository class for ROM set objects of Standard ROM Launchers (legacy json files) ---
# Arranges retrieving and storing of roms belonging to a particular standard ROM launcher.
#
# NOTE ROMs in a collection are stored as a list and ROMs in Favourites are stored as
#      a dictionary. Convert the Collection list into an ordered dictionary and then
#      converted back the ordered dictionary into a list before saving the collection.
# -------------------------------------------------------------------------------------------------
class ROMsJsonFileRepository(object):

    def __init__(self, file_path: io.FileName, debug = False):
        self.file_path = file_path
        self.debug = debug
    #
    # Loads ROM databases from disk
    #
    def load_ROMs(self) -> typing.List[ROM]:
        logger.debug('ROMsJsonFileRepository::load_ROMs() Starting ...')
        if not self.file_path.exists():
            logger.warning('Launcher JSON not found "{0}"'.format(self.file_path.getPath()))
            return []

        roms_data = []
        # --- Parse using json module ---
        # >> On Github issue #8 a user had an empty JSON file for ROMs. This raises
        #    exception exceptions.ValueError and launcher cannot be deleted. Deal
        #    with this exception so at least launcher can be rescanned.
        logger.debug('ROMsJsonFileRepository.find_by_launcher(): Loading roms from file {0}'.format(self.file_path.getPath()))
        try:
            roms_data = self.file_path.readJson()
        except ValueError:
            statinfo = self.file_path.stat()
            logger.error('ROMsJsonFileRepository.find_by_launcher(): ValueError exception in json.load() function')
            logger.error('ROMsJsonFileRepository.find_by_launcher(): Dir  {0}'.format(self.file_path.getPath()))
            logger.error('ROMsJsonFileRepository.find_by_launcher(): Size {0}'.format(statinfo.st_size))
            return None

        # --- Extract roms from JSON data structure and ensure version is correct ---
        if roms_data and isinstance(roms_data, list) and 'control' in roms_data[0]:
            control_str = roms_data[0]['control']
            version_int = roms_data[0]['version']
            roms_data   = roms_data[1]

        roms = []
        if isinstance(roms_data, list):
            for rom_data in roms_data:
                assets = self._get_assets_from_romdata(rom_data)
                r = ROM(rom_data, assets)
                key = r.get_id()
                roms.append(r)
        else:
            for key in roms_data:
                assets = self._get_assets_from_romdata(roms_data[key])
                r = ROM(roms_data[key], assets)
                roms.append(r)

        return roms
    
    def _get_assets_from_romdata(self, rom_data: dict) -> typing.List[Asset]:
        assets = []
        for key, value in rom_data.items():
            if key.startswith('s_'):
                asset_info = constants.g_assetFactory.get_asset_info_by_key(key)
                asset_data = { 'filepath': value }
                assets.append(Asset(asset_info, asset_data))
        return assets
#
# UnitOfWork to be used with sqlite repositories.
# Can be used to create database scopes/sessions (unit of work pattern).
#
class UnitOfWork(object):

    def __init__(self, db_path: io.FileName):
        self._db_path = db_path
        self._commit = False
    
    def check_database(self):
        if not self._db_path.exists():
            logger.warning("UnitOfWork.check_database(): Database '%s' missing" % self._db_path)
            return False

        self.open_session()
        self.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = self.result_set()

        if not len(tables):
            logger.warning("UnitOfWork.check_database(): Database: '%s' no tables" % self._db_path)
            self.close_session()
            return False

        self.close_session()
        return len(tables) > 1

    def create_empty_database(self, schema_file_path: io.FileName):
        self.open_session()
        
        sql_statements = schema_file_path.loadFileToStr()
        self.conn.executescript(sql_statements)
        self.conn.execute("INSERT INTO ael_version VALUES(?, ?)", [globals.addon_id, globals.addon_version])
        # default addons
        addon_repository = AelAddonRepository(self)
        app_launcher_addon = AelAddon({
            'id': text.misc_generate_random_SID(),
            'name':  'App Launcher', 
            'addon_id': '{}.AppLauncher'.format(globals.addon_id),
            'version': globals.addon_version,
            'addon_type': constants.AddonType.LAUNCHER.name, 
            'execute_uri': globals.router.url_for_path('launcher/app'),
            'configure_uri': globals.router.url_for_path('launcher/app/configure')
        })
        addon_repository.insert_addon(app_launcher_addon)
        folder_scanner_addon = AelAddon({
            'id': text.misc_generate_random_SID(),
            'name':  'Folder scanner', 
            'addon_id': '{}.FolderScanner'.format(globals.addon_id),
            'version': globals.addon_version,
            'addon_type': constants.AddonType.SCANNER.name, 
            'execute_uri': globals.router.url_for_path('scanner/folder'),
            'configure_uri': globals.router.url_for_path('scanner/folder/configure')
        })
        addon_repository.insert_addon(folder_scanner_addon)

        self.commit()
        self.close_session()
        
    def reset_database(self, schema_file_path: io.FileName):
        if self._db_path.exists():
            self._db_path.unlink()
        
        # cleanup collection json files
        if globals.g_PATHS.COLLECTIONS_DIR.exists():
            collection_files = globals.g_PATHS.COLLECTIONS_DIR.scanFilesInPath("collection_*.json")
            for collection_file in collection_files:
                collection_file.unlink()
                
        # cleanup root file
        if globals.g_PATHS.ROOT_PATH.exists():
            globals.g_PATHS.ROOT_PATH.unlink()
            
        self.create_empty_database(schema_file_path)

    def open_session(self):
        self.conn = sqlite3.connect(self._db_path.getPathTranslated())
        self.conn.row_factory = UnitOfWork.dict_factory
        self.cursor = self.conn.cursor()

    def commit(self):
        self._commit = True

    def rollback(self):
        self._commit = False
        self.conn.rollback()

    def close_session(self):
        if self._commit:
            self.conn.commit()

        self.cursor.close()
        self.conn.close()

    def execute(self, sql, *args) -> Cursor:
        return self.cursor.execute(sql, args)

    def single_result(self) -> dict:
        return self.cursor.fetchone()

    def result_set(self) -> typing.List[dict]:
        return self.cursor.fetchall()

    def result_id(self):
        return self.cursor.lastrowid

    def __enter__(self):
        self.open_session()

    def __exit__(self, type, value, traceback):
        if type is not None: # errors raised
            logger.error("type: %s value: %s", type, value)
        self.close_session()

    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

# Shared Queries
QUERY_INSERT_METADATA       = "INSERT INTO metadata (id,year,genre,developer,rating,plot,assets_path,finished) VALUES (?,?,?,?,?,?,?,?)"
QUERY_INSERT_ASSET          = "INSERT INTO assets (id, filepath, asset_type) VALUES (?,?,?)"
QUERY_INSERT_ASSET_PATH     = "INSERT INTO assetspaths (id, path, asset_type) VALUES (?,?,?)"
QUERY_UPDATE_METADATA       = "UPDATE metadata SET year=?, genre=?, developer=?, rating=?, plot=?, assets_path=?, finished=? WHERE id=?"
QUERY_UPDATE_ASSET          = "UPDATE assets SET filepath = ?, asset_type = ? WHERE id = ?"

#
# CategoryRepository -> Category from SQLite DB
#
QUERY_SELECT_CATEGORY                   = "SELECT * FROM vw_categories WHERE id = ?"
QUERY_SELECT_CATEGORY_ASSETS            = "SELECT * FROM vw_category_assets WHERE category_id = ?"
QUERY_SELECT_CATEGORIES                 = "SELECT * FROM vw_categories"
QUERY_SELECT_ALL_CATEGORY_ASSETS        = "SELECT * FROM vw_category_assets"
QUERY_SELECT_ROOT_CATEGORIES            = "SELECT * FROM vw_categories WHERE parent_id IS NULL"
QUERY_SELECT_ROOT_CATEGORY_ASSETS       = "SELECT * FROM vw_category_assets WHERE parent_id IS NULL"
QUERY_SELECT_CATEGORIES_BY_PARENT       = "SELECT * FROM vw_categories WHERE parent_id = ?"
QUERY_SELECT_CATEGORY_ASSETS_BY_PARENT  = "SELECT * FROM vw_category_assets WHERE parent_id = ?"

QUERY_INSERT_CATEGORY             = """
                                    INSERT INTO categories (id,name,parent_id,metadata_id,default_icon,default_fanart,default_banner,default_poster,default_clearlogo) 
                                    VALUES (?,?,?,?,?,?,?,?,?)
                                    """
QUERY_UPDATE_CATEGORY             = """
                                    UPDATE categories SET name=?, 
                                    default_icon=?, default_fanart=?, default_banner=?, default_poster=?, default_clearlogo=?
                                    WHERE id =?
                                    """
QUERY_INSERT_CATEGORY_ASSET       = "INSERT INTO category_assets (category_id, asset_id) VALUES (?, ?)"
QUERY_DELETE_CATEGORY             = "DELETE FROM category WHERE id = ?"
class CategoryRepository(object):

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def find_category(self, category_id: str) -> Category:
        self._uow.execute(QUERY_SELECT_CATEGORY, category_id)
        category_data = self._uow.single_result()
                
        self._uow.execute(QUERY_SELECT_CATEGORY_ASSETS, category_id)
        assets_result_set = self._uow.result_set()
                
        assets = []
        for asset_data in assets_result_set:
            asset_info = constants.g_assetFactory.get_asset_info(asset_data['asset_type'])
            assets.append(Asset(asset_info, asset_data))    
            
        return Category(category_data, assets)

    def find_root_categories(self) -> typing.Iterator[Category]:
        self._uow.execute(QUERY_SELECT_ROOT_CATEGORIES)
        result_set = self._uow.result_set()
        
        self._uow.execute(QUERY_SELECT_ROOT_CATEGORY_ASSETS)
        assets_result_set = self._uow.result_set()
                    
        for category_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['category_id'] == category_data['id'], assets_result_set):
                asset_info = constants.g_assetFactory.get_asset_info(asset_data['asset_type'])
                assets.append(Asset(asset_info, asset_data))    
                
            yield Category(category_data, assets)

    def find_categories_by_parent(self, category_id) -> typing.Iterator[Category]:
        self._uow.execute(QUERY_SELECT_CATEGORIES_BY_PARENT, category_id)
        result_set = self._uow.result_set()
        
        self._uow.execute(QUERY_SELECT_CATEGORY_ASSETS_BY_PARENT, category_id)
        assets_result_set = self._uow.result_set()
                    
        for category_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['category_id'] == category_data['id'], assets_result_set):
                asset_info = constants.g_assetFactory.get_asset_info(asset_data['asset_type'])
                assets.append(Asset(asset_info, asset_data))    
                
            yield Category(category_data, assets)

    def find_all_categories(self) -> typing.Iterator[Category]:
        self._uow.execute(QUERY_SELECT_CATEGORIES)
        result_set = self._uow.result_set()
        
        self._uow.execute(QUERY_SELECT_ALL_CATEGORY_ASSETS)
        assets_result_set = self._uow.result_set()
                    
        for category_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['category_id'] == category_data['id'], assets_result_set):
                asset_info = constants.g_assetFactory.get_asset_info(asset_data['asset_type'])
                assets.append(Asset(asset_info, asset_data))    
                
            yield Category(category_data, assets)

    def insert_category(self, category_obj: Category, parent_obj: Category = None):
        logger.info("CategoryRepository.insert_category(): Inserting new category '{}'".format(category_obj.get_name()))
        metadata_id = text.misc_generate_random_SID()
        assets_path = category_obj.get_assets_path_FN()
        
        self._uow.execute(QUERY_INSERT_METADATA,
            metadata_id,
            category_obj.get_releaseyear(),
            category_obj.get_genre(),
            category_obj.get_developer(),
            category_obj.get_rating(),
            category_obj.get_plot(),
            assets_path.getPath() if assets_path is not None else None,
            category_obj.is_finished())

        self._uow.execute(QUERY_INSERT_CATEGORY,
            category_obj.get_id(),
            category_obj.get_name(),
            parent_obj.get_id() if parent_obj is not None else None,
            metadata_id,
            category_obj.get_mapped_asset_info(asset_id=constants.ASSET_ICON_ID).key,
            category_obj.get_mapped_asset_info(asset_id=constants.ASSET_FANART_ID).key,
            category_obj.get_mapped_asset_info(asset_id=constants.ASSET_BANNER_ID).key,
            category_obj.get_mapped_asset_info(asset_id=constants.ASSET_POSTER_ID).key,
            category_obj.get_mapped_asset_info(asset_id=constants.ASSET_CLEARLOGO_ID).key)

        category_assets = category_obj.get_assets()
        for asset in category_assets: 
            self._insert_asset(asset, category_obj)  
            
    def update_category(self, category_obj: Category):
        logger.info("CategoryRepository.update_category(): Updating category '{}'".format(category_obj.get_name()))
        assets_path = category_obj.get_assets_path_FN()
        
        self._uow.execute(QUERY_UPDATE_METADATA,
            category_obj.get_releaseyear(),
            category_obj.get_genre(),
            category_obj.get_developer(),
            category_obj.get_rating(),
            category_obj.get_plot(),
            assets_path.getPath() if assets_path is not None else None,
            category_obj.is_finished(),
            category_obj.get_custom_attribute('metadata_id'))

        self._uow.execute(QUERY_UPDATE_CATEGORY,
            category_obj.get_name(),
            category_obj.get_mapped_asset_info(asset_id=constants.ASSET_ICON_ID).key,
            category_obj.get_mapped_asset_info(asset_id=constants.ASSET_FANART_ID).key,
            category_obj.get_mapped_asset_info(asset_id=constants.ASSET_BANNER_ID).key,
            category_obj.get_mapped_asset_info(asset_id=constants.ASSET_POSTER_ID).key,
            category_obj.get_mapped_asset_info(asset_id=constants.ASSET_CLEARLOGO_ID).key,
            category_obj.get_id())
        
        for asset in category_obj.get_assets():
            if asset.get_id() == '': self._insert_asset(asset, category_obj)
            else: self._update_asset(asset, category_obj)    

    def delete_category(self, category_id: str):
        logger.info("CategoryRepository.delete_category(): Deleting category '{}'".format(category_id))
        self._uow.execute(QUERY_DELETE_CATEGORY, category_id)
        
    def _insert_asset(self, asset: Asset, category_obj: Category):
        asset_db_id = text.misc_generate_random_SID()
        self._uow.execute(QUERY_INSERT_ASSET, asset_db_id, asset.get_path(), asset.get_asset_info_id())
        self._uow.execute(QUERY_INSERT_CATEGORY_ASSET, category_obj.get_id(), asset_db_id)   
    
    def _update_asset(self, asset: Asset, category_obj: Category):
        self._uow.execute(QUERY_UPDATE_ASSET, asset.get_path(), asset.get_asset_info_id(), asset.get_id())
        if asset.get_custom_attribute('category_id') is None:
            self._uow.execute(QUERY_INSERT_CATEGORY_ASSET, category_obj.get_id(), asset.get_id())   
        
#
# ROMSetRepository -> ROM Sets from SQLite DB
#
QUERY_SELECT_ROMSET             = "SELECT * FROM vw_romsets WHERE id = ?"
QUERY_SELECT_ROMSETS            = "SELECT * FROM vw_romsets"
QUERY_SELECT_ROOT_ROMSETS       = "SELECT * FROM vw_romsets WHERE parent_id IS NULL"
QUERY_SELECT_ROMSETS_BY_PARENT  = "SELECT * FROM vw_romsets WHERE parent_id = ?"

QUERY_INSERT_ROMSET               = """
                                    INSERT INTO romsets (
                                            id,name,parent_id,metadata_id,platform,box_size, 
                                            default_icon,default_fanart,default_banner,default_poster,default_controller,default_clearlogo,
                                            roms_default_icon,roms_default_fanart,roms_default_banner,roms_default_poster,roms_default_clearlogo
                                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                                    """
QUERY_UPDATE_ROMSET               = """
                                    UPDATE romsets SET 
                                        name=?, platform=?, box_size=?, 
                                        default_icon=?, default_fanart=?, default_banner=?, default_poster=?, default_controller=?, default_clearlogo=?,
                                        roms_default_icon=?, roms_default_fanart=?, roms_default_banner=?, roms_default_poster=?, roms_default_clearlogo=?
                                        WHERE id =?
                                    """
QUERY_DELETE_ROMSET               = "DELETE FROM romset WHERE id = ?"

QUERY_SELECT_ROMSET_ASSETS_BY_SET       = "SELECT * FROM vw_romset_assets WHERE romset_id = ?"
QUERY_SELECT_ROOT_ROMSET_ASSETS         = "SELECT * FROM vw_romset_assets WHERE parent_id IS NULL"
QUERY_SELECT_ROMSETS_ASSETS_BY_PARENT   = "SELECT * FROM vw_romset_assets WHERE parent_id = ?"
QUERY_SELECT_ROMSET_ASSETS              = "SELECT * FROM vw_romset_assets"
QUERY_INSERT_ROMSET_ASSET               = "INSERT INTO romset_assets (romset_id, asset_id) VALUES (?, ?)"
QUERY_INSERT_ROMSET_ASSET_PATH          = "INSERT INTO romset_assetspaths (romset_id, assetspaths_id) VALUES (?, ?)"

QUERY_INSERT_ROM_IN_ROMSET        = "INSERT INTO roms_in_romset (rom_id, romset_id) VALUES (?,?)"
QUERY_REMOVE_ROM_FROM_ROMSET      = "DELETE FROM roms_in_romset WHERE rom_id = ? AND romset_id = ?"

QUERY_SELECT_ROMSET_LAUNCHERS     = "SELECT * FROM vw_romset_launchers WHERE romset_id = ?"
QUERY_INSERT_ROMSET_LAUNCHER      = "INSERT INTO romset_launchers (id, romset_id, ael_addon_id, settings, is_non_blocking, is_default) VALUES (?,?,?,?,?,?)"
QUERY_UPDATE_ROMSET_LAUNCHER      = "UPDATE romset_launchers SET settings = ?, is_non_blocking = ?, is_default = ? WHERE id = ?"
QUERY_DELETE_ROMSET_LAUNCHERS     = "DELETE FROM romset_launchers WHERE romset_id = ?"
QUERY_DELETE_ROMSET_LAUNCHER      = "DELETE FROM romset_launchers WHERE romset_id = ? AND id = ?"

QUERY_SELECT_ROMSET_SCANNERS      = "SELECT * FROM vw_romset_scanners WHERE romset_id = ?"
QUERY_INSERT_ROMSET_SCANNER       = "INSERT INTO romset_scanners (id, romset_id, ael_addon_id, settings) VALUES (?,?,?,?)"
QUERY_UPDATE_ROMSET_SCANNER       = "UPDATE romset_scanners SET settings = ? WHERE id = ?"
QUERY_DELETE_ROMSET_SCANNER       = "DELETE FROM romset_scanners WHERE romset_id = ? AND id = ?"
class ROMSetRepository(object):

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def find_romset(self, romset_id: str) -> ROMSet:
        self._uow.execute(QUERY_SELECT_ROMSET, romset_id)
        romset_data = self._uow.single_result()
        
        self._uow.execute(QUERY_SELECT_ROMSET_ASSETS_BY_SET, romset_id)
        assets_result_set = self._uow.result_set()
        assets = []
        for asset_data in assets_result_set:
            asset_info = constants.g_assetFactory.get_asset_info(asset_data['asset_type'])
            assets.append(Asset(asset_info, asset_data))    
        
        self._uow.execute(QUERY_SELECT_ROMSET_LAUNCHERS, romset_id)
        launchers_data = self._uow.result_set()
        launchers = []
        for launcher_data in launchers_data:
            addon = AelAddon(launcher_data.copy())
            launchers.append(ROMLauncherAddon(addon, launcher_data))
        
        self._uow.execute(QUERY_SELECT_ROMSET_SCANNERS, romset_id)
        scanners_data = self._uow.result_set()
        scanners = []
        for scanner_data in scanners_data:
            addon = AelAddon(scanner_data.copy())
            scanners.append(ROMSetScanner(addon, scanner_data))
            
        return ROMSet(romset_data, assets, launchers, scanners)

    def find_all_romsets(self) -> typing.Iterator[ROMSet]:
        self._uow.execute(QUERY_SELECT_ROMSETS)
        result_set = self._uow.result_set()
        
        self._uow.execute(QUERY_SELECT_ROMSET_ASSETS)
        assets_result_set = self._uow.result_set()
                
        for romset_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['romset_id'] == romset_data['id'], assets_result_set):
                asset_info = constants.g_assetFactory.get_asset_info(asset_data['asset_type'])
                assets.append(Asset(asset_info, asset_data))      
                
            yield ROMSet(romset_data, assets)

    def find_root_romsets(self) -> typing.Iterator[ROMSet]:
        self._uow.execute(QUERY_SELECT_ROOT_ROMSETS)
        result_set = self._uow.result_set()
        
        self._uow.execute(QUERY_SELECT_ROOT_ROMSET_ASSETS)
        assets_result_set = self._uow.result_set()
                
        for romset_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['romset_id'] == romset_data['id'], assets_result_set):
                asset_info = constants.g_assetFactory.get_asset_info(asset_data['asset_type'])
                assets.append(Asset(asset_info, asset_data))      
                
            yield ROMSet(romset_data, assets)

    def find_romsets_by_parent(self, category_id) -> typing.Iterator[ROMSet]:
        self._uow.execute(QUERY_SELECT_ROMSETS_BY_PARENT, category_id)
        result_set = self._uow.result_set()
        
        self._uow.execute(QUERY_SELECT_ROMSETS_ASSETS_BY_PARENT, category_id)
        assets_result_set = self._uow.result_set()
                
        for romset_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['romset_id'] == romset_data['id'], assets_result_set):
                asset_info = constants.g_assetFactory.get_asset_info(asset_data['asset_type'])
                assets.append(Asset(asset_info, asset_data))      
                
            yield ROMSet(romset_data, assets)
            
    def insert_romset(self, romset_obj: ROMSet, parent_obj: Category = None):
        logger.info("ROMSetRepository.insert_romset(): Inserting new romset '{}'".format(romset_obj.get_name()))
        metadata_id = text.misc_generate_random_SID()
        assets_path = romset_obj.get_assets_path_FN()
        
        self._uow.execute(QUERY_INSERT_METADATA,
            metadata_id,
            romset_obj.get_releaseyear(),
            romset_obj.get_genre(),
            romset_obj.get_developer(),
            romset_obj.get_rating(),
            romset_obj.get_plot(),
            assets_path.getPath() if assets_path is not None else None,
            romset_obj.is_finished())

        self._uow.execute(QUERY_INSERT_ROMSET,
            romset_obj.get_id(),
            romset_obj.get_name(),
            parent_obj.get_id() if parent_obj is not None else None,
            metadata_id,
            romset_obj.get_platform(),
            romset_obj.get_box_sizing(),    
            romset_obj.get_mapped_asset_info(asset_id=constants.ASSET_ICON_ID).key,
            romset_obj.get_mapped_asset_info(asset_id=constants.ASSET_FANART_ID).key,
            romset_obj.get_mapped_asset_info(asset_id=constants.ASSET_BANNER_ID).key,
            romset_obj.get_mapped_asset_info(asset_id=constants.ASSET_POSTER_ID).key,
            romset_obj.get_mapped_asset_info(asset_id=constants.ASSET_CONTROLLER_ID).key,
            romset_obj.get_mapped_asset_info(asset_id=constants.ASSET_CLEARLOGO_ID).key,            
            romset_obj.get_mapped_ROM_asset_info(asset_id=constants.ASSET_ICON_ID).key,
            romset_obj.get_mapped_ROM_asset_info(asset_id=constants.ASSET_FANART_ID).key,
            romset_obj.get_mapped_ROM_asset_info(asset_id=constants.ASSET_BANNER_ID).key,
            romset_obj.get_mapped_ROM_asset_info(asset_id=constants.ASSET_POSTER_ID).key,
            romset_obj.get_mapped_ROM_asset_info(asset_id=constants.ASSET_CLEARLOGO_ID).key)
        
        romset_assets = romset_obj.get_assets()
        for asset in romset_assets: 
            self._insert_asset(asset, romset_obj)  
            
        romset_launchers = romset_obj.get_launchers()
        for romset_launcher in romset_launchers:
            romset_launcher.set_id(text.misc_generate_random_SID())
            self._uow.execute(QUERY_INSERT_ROMSET_LAUNCHER,
                romset_launcher.get_id(),
                romset_obj.get_id(), 
                romset_launcher.addon.get_id(), 
                romset_launcher.get_settings_str(), 
                romset_launcher.is_non_blocking(),
                romset_launcher.is_default())
            
        romset_scanners = romset_obj.get_scanners()
        for romset_scanner in romset_scanners:
            romset_scanner.set_id(text.misc_generate_random_SID())
            self._uow.execute(QUERY_INSERT_ROMSET_SCANNER,
                romset_scanner.get_id(),
                romset_obj.get_id(), 
                romset_scanner.addon.get_id(), 
                romset_scanner.get_settings_str())
              
    def update_romset(self, romset_obj: ROMSet):
        logger.info("ROMSetRepository.update_romset(): Updating romset '{}'".format(romset_obj.get_name()))
        assets_path = romset_obj.get_assets_path_FN()
        
        self._uow.execute(QUERY_UPDATE_METADATA,
            romset_obj.get_releaseyear(),
            romset_obj.get_genre(),
            romset_obj.get_developer(),
            romset_obj.get_rating(),
            romset_obj.get_plot(),
            assets_path.getPath() if assets_path is not None else None,
            romset_obj.is_finished(),
            romset_obj.get_custom_attribute('metadata_id'))

        self._uow.execute(QUERY_UPDATE_ROMSET,
            romset_obj.get_name(),
            romset_obj.get_platform(),
            romset_obj.get_box_sizing(),
            romset_obj.get_mapped_asset_info(asset_id=constants.ASSET_ICON_ID).key,
            romset_obj.get_mapped_asset_info(asset_id=constants.ASSET_FANART_ID).key,
            romset_obj.get_mapped_asset_info(asset_id=constants.ASSET_BANNER_ID).key,
            romset_obj.get_mapped_asset_info(asset_id=constants.ASSET_POSTER_ID).key,
            romset_obj.get_mapped_asset_info(asset_id=constants.ASSET_CONTROLLER_ID).key,
            romset_obj.get_mapped_asset_info(asset_id=constants.ASSET_CLEARLOGO_ID).key,            
            romset_obj.get_mapped_ROM_asset_info(asset_id=constants.ASSET_ICON_ID).key,
            romset_obj.get_mapped_ROM_asset_info(asset_id=constants.ASSET_FANART_ID).key,
            romset_obj.get_mapped_ROM_asset_info(asset_id=constants.ASSET_BANNER_ID).key,
            romset_obj.get_mapped_ROM_asset_info(asset_id=constants.ASSET_POSTER_ID).key,
            romset_obj.get_mapped_ROM_asset_info(asset_id=constants.ASSET_CLEARLOGO_ID).key,
            romset_obj.get_id())
         
        romset_launchers = romset_obj.get_launchers()
        for romset_launcher in romset_launchers:
            if romset_launcher.get_id() is None:
                romset_launcher.set_id(text.misc_generate_random_SID())
                self._uow.execute(QUERY_INSERT_ROMSET_LAUNCHER,
                    romset_launcher.get_id(),
                    romset_obj.get_id(), 
                    romset_launcher.addon.get_id(), 
                    romset_launcher.get_settings_str(), 
                    romset_launcher.is_non_blocking(),
                    romset_launcher.is_default())
            else:
                self._uow.execute(QUERY_UPDATE_ROMSET_LAUNCHER,
                    romset_launcher.get_settings_str(), 
                    romset_launcher.is_non_blocking(),
                    romset_launcher.is_default(),
                    romset_launcher.get_id())
                
        romset_scanners = romset_obj.get_scanners()
        for romset_scanner in romset_scanners:
            if romset_scanner.get_id() is None:
                romset_scanner.set_id(text.misc_generate_random_SID())
                self._uow.execute(QUERY_INSERT_ROMSET_SCANNER,
                    romset_scanner.get_id(),
                    romset_obj.get_id(), 
                    romset_scanner.addon.get_id(), 
                    romset_scanner.get_settings_str())
            else:
                self._uow.execute(QUERY_UPDATE_ROMSET_SCANNER,
                    romset_scanner.get_settings_str(), 
                    romset_scanner.get_id())

        for asset in romset_obj.get_assets():
            if asset.get_id() == '': self._insert_asset(asset, romset_obj)
            else: self._update_asset(asset, romset_obj)                
            
    def add_rom_to_romset(self, romset_id: str, rom_id: str):
        self._uow.execute(QUERY_INSERT_ROM_IN_ROMSET, rom_id, romset_id)
            
    def remove_rom_from_romset(self, romset_id: str, rom_id: str):
        self._uow.execute(QUERY_REMOVE_ROM_FROM_ROMSET, rom_id, romset_id)
    def delete_romset(self, romset_id: str):
        logger.info("ROMSetRepository.delete_romset(): Deleting romset '{}'".format(romset_id))
        self._uow.execute(QUERY_DELETE_ROMSET, romset_id)

    def remove_launcher(self, romset_id: str, launcher_id:str):
        self._uow.execute(QUERY_DELETE_ROMSET_LAUNCHER, romset_id, launcher_id)

    def remove_scanner(self, romset_id: str, scanner_id:str):
        self._uow.execute(QUERY_DELETE_ROMSET_SCANNER, romset_id, scanner_id)

    def _insert_asset(self, asset: Asset, romset_obj: ROMSet):
        asset_db_id = text.misc_generate_random_SID()
        self._uow.execute(QUERY_INSERT_ASSET, asset_db_id, asset.get_path(), asset.get_asset_info_id())
        self._uow.execute(QUERY_INSERT_ROMSET_ASSET, romset_obj.get_id(), asset_db_id)   
    
    def _update_asset(self, asset: Asset, romset_obj: ROMSet):
        self._uow.execute(QUERY_UPDATE_ASSET, asset.get_path(), asset.get_asset_info_id(), asset.get_id())
        if asset.get_custom_attribute('romset_id') is None:
            self._uow.execute(QUERY_INSERT_ROMSET_ASSET, romset_obj.get_id(), asset.get_id())   
            
#
# ROMsRepository -> ROMs from SQLite DB
#     
QUERY_SELECT_ROM                = "SELECT * FROM vw_roms WHERE id = ?"
QUERY_SELECT_ROMS_BY_SET        = "SELECT r.* FROM vw_roms AS r INNER JOIN roms_in_romset AS rs ON rs.rom_id = r.id AND rs.romset_id = ?"
QUERY_SELECT_ROM_ASSETS         = "SELECT * FROM vw_rom_assets WHERE rom_id = ?"
QUERY_SELECT_ROM_ASSETS_BY_SET  = "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN roms_in_romset AS rs ON rs.rom_id = ra.rom_id AND rs.romset_id = ?"
QUERY_INSERT_ROM                = """
                                INSERT INTO roms (
                                    id, metadata_id, name, num_of_players, esrb_rating, platform, box_size,
                                    nointro_status, cloneof, fav_status, file_path)
                                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                                """ 
QUERY_INSERT_ROM_ASSET          = "INSERT INTO rom_assets (rom_id, asset_id) VALUES (?, ?)"
QUERY_UPDATE_ROM                = """
                                  UPDATE roms 
                                  SET name=?, num_of_players=?, esrb_rating=?, platform = ?, box_size = ?,
                                  nointro_status=?, cloneof=?, fav_status=?, file_path=? WHERE id =?
                                  """

QUERY_SELECT_ROM_LAUNCHERS     = "SELECT * FROM vw_rom_launchers WHERE rom_id = ?"
QUERY_INSERT_ROM_LAUNCHER      = "INSERT INTO rom_launchers (id, rom_id, ael_addon_id, settings, is_non_blocking, is_default) VALUES (?,?,?,?,?,?)"
QUERY_UPDATE_ROM_LAUNCHER      = "UPDATE rom_launchers SET settings = ?, is_non_blocking = ?, is_default = ? WHERE id = ?"
QUERY_DELETE_ROM_LAUNCHERS     = "DELETE FROM rom_launchers WHERE rom_id = ?"
QUERY_DELETE_ROM_LAUNCHER      = "DELETE FROM rom_launchers WHERE romset_id = ? AND id = ?"
          
class ROMsRepository(object):
       
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def find_roms_by_romset(self, romset_id: str) -> typing.Iterator[ROM]:
        self._uow.execute(QUERY_SELECT_ROMS_BY_SET, romset_id)
        result_set = self._uow.result_set()
        
        self._uow.execute(QUERY_SELECT_ROM_ASSETS_BY_SET, romset_id)
        assets_result_set = self._uow.result_set()
                
        for rom_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['rom_id'] == rom_data['id'], assets_result_set):
                asset_info = constants.g_assetFactory.get_asset_info(asset_data['asset_type'])
                assets.append(Asset(asset_info, asset_data))                
            yield ROM(rom_data, assets)

    def find_rom(self, rom_id:str) -> ROM:
        self._uow.execute(QUERY_SELECT_ROM, rom_id)
        rom_data = self._uow.single_result()

        self._uow.execute(QUERY_SELECT_ROM_ASSETS, rom_id)
        assets_result_set = self._uow.result_set()            
        assets = []
        for asset_data in assets_result_set:
            asset_info = constants.g_assetFactory.get_asset_info(asset_data['asset_type'])
            assets.append(Asset(asset_info, asset_data))
                    
        self._uow.execute(QUERY_SELECT_ROM_LAUNCHERS, rom_id)
        launchers_data = self._uow.result_set()
        launchers = []
        for launcher_data in launchers_data:
            addon = AelAddon(launcher_data.copy())
            launchers.append(ROMLauncherAddon(addon, launcher_data))
            
        return ROM(rom_data, assets, launchers)


    def insert_rom(self, rom_obj: ROM): 
        logger.info("ROMsRepository.insert_rom(): Inserting new ROM '{}'".format(rom_obj.get_name()))
        metadata_id = text.misc_generate_random_SID()
        assets_path = rom_obj.get_assets_path_FN()
        
        self._uow.execute(QUERY_INSERT_METADATA,
            metadata_id,
            rom_obj.get_releaseyear(),
            rom_obj.get_genre(),
            rom_obj.get_developer(),
            rom_obj.get_rating(),
            rom_obj.get_plot(),
            assets_path.getPath() if assets_path is not None else None,
            rom_obj.is_finished())

        self._uow.execute(QUERY_INSERT_ROM,
            rom_obj.get_id(),
            metadata_id,
            rom_obj.get_name(),
            rom_obj.get_number_of_players(),
            rom_obj.get_esrb_rating(),   
            rom_obj.get_platform(),
            rom_obj.get_box_sizing(), 
            rom_obj.get_nointro_status(),
            rom_obj.get_clone(),
            rom_obj.get_favourite_status(),
            rom_obj.get_file().getPath())
        
        rom_assets = rom_obj.get_assets()
        for asset in rom_assets:
            self._insert_asset(asset, rom_obj)

        rom_launchers = rom_obj.get_launchers()
        for rom_launchers in rom_launchers:
            rom_launchers.set_id(text.misc_generate_random_SID())
            self._uow.execute(QUERY_INSERT_ROM_LAUNCHER,
                rom_launchers.get_id(),
                rom_obj.get_id(), 
                rom_launchers.addon.get_id(), 
                rom_launchers.get_settings_str(), 
                rom_launchers.is_non_blocking(),
                rom_launchers.is_default())

    def update_rom(self, rom_obj: ROM):
        logger.info("ROMsRepository.update_rom(): Updating ROM '{}'".format(rom_obj.get_name()))
        assets_path = rom_obj.get_assets_path_FN()
        
        self._uow.execute(QUERY_UPDATE_METADATA,
            rom_obj.get_releaseyear(),
            rom_obj.get_genre(),
            rom_obj.get_developer(),
            rom_obj.get_rating(),
            rom_obj.get_plot(),
            assets_path.getPath() if assets_path is not None else None,
            rom_obj.is_finished(),
            rom_obj.get_custom_attribute('metadata_id'))

        self._uow.execute(QUERY_UPDATE_ROM,
            rom_obj.get_name(),
            rom_obj.get_number_of_players(),
            rom_obj.get_esrb_rating(),
            rom_obj.get_platform(),
            rom_obj.get_box_sizing(),
            rom_obj.get_nointro_status(),
            rom_obj.get_clone(),
            rom_obj.get_favourite_status(),
            rom_obj.get_id())
        
        for asset in rom_obj.get_assets():
            if asset.get_id() == '': self._insert_asset(asset, rom_obj)
            else: self._update_asset(asset, rom_obj)            
        
        rom_launchers = rom_obj.get_launchers()
        for rom_launcher in rom_launchers:
            if rom_launcher.get_id() is None:
                rom_launcher.set_id(text.misc_generate_random_SID())
                self._uow.execute(QUERY_INSERT_ROMSET_LAUNCHER,
                    rom_launcher.get_id(),
                    rom_obj.get_id(), 
                    rom_launcher.addon.get_id(), 
                    rom_launcher.get_settings_str(), 
                    rom_launcher.is_non_blocking(),
                    rom_launcher.is_default())
            else:
                self._uow.execute(QUERY_UPDATE_ROMSET_LAUNCHER,
                    rom_launcher.get_settings_str(), 
                    rom_launcher.is_non_blocking(),
                    rom_launcher.is_default(),
                    rom_launcher.get_id())
                    
    def _insert_asset(self, asset: Asset, rom_obj: ROM):
        asset_db_id = text.misc_generate_random_SID()
        self._uow.execute(QUERY_INSERT_ASSET, asset_db_id, asset.get_path(), asset.get_asset_info_id())
        self._uow.execute(QUERY_INSERT_ROM_ASSET, rom_obj.get_id(), asset_db_id)   
    
    def _update_asset(self, asset: Asset, rom_obj: ROM):
        self._uow.execute(QUERY_UPDATE_ASSET, asset.get_path(), asset.get_asset_info_id(), asset.get_id())
        if asset.get_custom_attribute('rom_id') is None:
            self._uow.execute(QUERY_INSERT_ROM_ASSET, rom_obj.get_id(), asset.get_id())   

#
# AelAddonRepository -> AEL Adoon objects from SQLite DB
#     
QUERY_SELECT_ADDON              = "SELECT * FROM ael_addon WHERE id = ?"
QUERY_SELECT_ADDON_BY_ADDON_ID  = "SELECT * FROM ael_addon WHERE addon_id = ?"
QUERY_SELECT_ADDONS             = "SELECT * FROM ael_addon"
QUERY_SELECT_LAUNCHER_ADDONS    = "SELECT * FROM ael_addon WHERE addon_type = 'LAUNCHER' ORDER BY name"
QUERY_SELECT_SCANNER_ADDONS     = "SELECT * FROM ael_addon WHERE addon_type = 'SCANNER' ORDER BY name"
QUERY_INSERT_ADDON              = "INSERT INTO ael_addon(id, name, addon_id, version, addon_type, execute_uri, configure_uri) VALUES(?,?,?,?,?,?,?)" 
QUERY_UPDATE_ADDON              = "UPDATE ael_addon SET name = ?, addon_id = ?, version = ?, addon_type = ?, execute_uri = ?, configure_uri = ? WHERE id = ?" 
class AelAddonRepository(object):

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def find(self, id:str) -> AelAddon:
        self._uow.execute(QUERY_SELECT_ADDON, id)
        result_set = self._uow.single_result()
        return AelAddon(result_set)

    def find_by_addon_id(self, addon_id:str) -> AelAddon:
        self._uow.execute(QUERY_SELECT_ADDON_BY_ADDON_ID, addon_id)
        result_set = self._uow.single_result()
        return AelAddon(result_set)

    def find_all(self) -> typing.Iterator[AelAddon]:
        self._uow.execute(QUERY_SELECT_ADDONS)
        result_set = self._uow.result_set()
        for addon_data in result_set:
            yield AelAddon(addon_data)

    def find_all_launchers(self) -> typing.Iterator[AelAddon]:        
        self._uow.execute(QUERY_SELECT_LAUNCHER_ADDONS)
        result_set = self._uow.result_set()
        for addon_data in result_set:
            yield AelAddon(addon_data)

    def find_all_scanners(self) -> typing.Iterator[AelAddon]:        
        self._uow.execute(QUERY_SELECT_SCANNER_ADDONS)
        result_set = self._uow.result_set()
        for addon_data in result_set:
            yield AelAddon(addon_data)

    def insert_addon(self, addon: AelAddon):
        logger.info("AelAddonRepository.insert_addon(): Saving addon '{}'".format(addon.get_addon_id()))        
        self._uow.execute(QUERY_INSERT_ADDON,
                    addon.get_id(),
                    addon.get_name(),
                    addon.get_addon_id(),
                    addon.get_version(),
                    addon.get_addon_type().name,
                    addon.get_execute_uri(),
                    addon.get_configure_uri())
        
    def update_addon(self, addon: AelAddon):
        logger.info("AelAddonRepository.update_addon(): Updating addon '{}'".format(addon.get_addon_id()))        
        self._uow.execute(QUERY_UPDATE_ADDON,
                    addon.get_name(),
                    addon.get_addon_id(),
                    addon.get_version(),
                    addon.get_addon_type().name,
                    addon.get_execute_uri(),
                    addon.get_configure_uri(),
                    addon.get_id())
