# -*- coding: utf-8 -*-
import logging
import typing

import sqlite3
from sqlite3.dbapi2 import Cursor

from akl.settings import *
from akl.utils import text, io
from akl import constants

from resources.lib import globals
from resources.lib.domain import Category, ROMCollection, ROM, Asset, AssetPath, VirtualCollection
from resources.lib.domain import VirtualCategoryFactory, VirtualCollectionFactory, ROMLauncherAddonFactory, g_assetFactory
from resources.lib.domain import ROMCollectionScanner, ROMLauncherAddon, AelAddon

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

    def __init__(self, paths: globals.AKL_Paths):
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
            logger.error('find_root_items(): ValueError exception in file.readJson() function', exc_info=ex)
            logger.error('find_root_items(): Dir  {}'.format(repository_file.getPath()))
            logger.error('find_root_items(): Size {}'.format(statinfo.st_size))
            return None
        
        return item_data

    def find_items(self, view_id, is_virtual = False) -> typing.Any:
        repository_file = self.paths.VIEWS_DIR.pjoin('view_{}.json'.format(view_id))
        if is_virtual:
            repository_file = self.paths.GENERATED_VIEWS_DIR.pjoin('view_{}.json'.format(view_id))
            
        logger.debug('find_items(): Loading path data from file {}'.format(repository_file.getPath()))
        try:
            item_data = repository_file.readJson()
        except ValueError as ex:
            statinfo = repository_file.stat()
            logger.error('find_items(): ValueError exception in file.readJson() function', exc_info=ex)
            logger.error('find_items(): Dir  {}'.format(repository_file.getPath()))
            logger.error('find_items(): Size {}'.format(statinfo.st_size))
            return None
        
        return item_data

    def store_root_view(self, view_data):
        repository_file = self.paths.ROOT_PATH
        logger.debug('store_root_view(): Storing data in file {}'.format(repository_file.getPath()))
        repository_file.writeJson(view_data)

    def store_view(self, view_id:str, object_type:str, view_data):        
        if object_type == constants.OBJ_CATEGORY_VIRTUAL or object_type == constants.OBJ_COLLECTION_VIRTUAL:
            repository_file = self.paths.GENERATED_VIEWS_DIR.pjoin(f'view_{view_id}.json')
        else:
            repository_file = self.paths.VIEWS_DIR.pjoin(f'view_{view_id}.json')
        
        if view_data is None: 
            if repository_file.exists():
                logger.debug('store_view(): No data for file {}. Removing file'.format(repository_file.getPath()))
                repository_file.unlink()
            return

        logger.debug(f'store_view(): Storing data in file {repository_file.getPath()}')
        repository_file.writeJson(view_data)

    def cleanup_views(self, view_ids_to_keep:typing.List[str]):
        view_files = self.paths.VIEWS_DIR.scanFilesInPath('view_*.json')
        for view_file in view_files:
            view_id = view_file.getBaseNoExt().replace('view_', '')
            if not view_id in view_ids_to_keep:
                logger.info(f'Removing file for view "{view_id}"')
                view_file.unlink()

    def cleanup_virtual_category_views(self, view_id):
        view_files = self.paths.GENERATED_VIEWS_DIR.scanFilesInPath(f'view_{view_id}_*.json')
        logger.info(f'Removing {len(view_files)} files for virtual category "{view_id}"')
        for view_file in view_files:
            view_file.unlink()
 
    def cleanup_all_virtual_category_views(self):
        view_files = self.paths.GENERATED_VIEWS_DIR.scanFilesInPath('view_vcategory*.json')
        logger.info(f'Removing {len(view_files)} files for all virtual categories')
        for view_file in view_files:
            view_file.unlink()
        
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

        xml_root = self.file_path.readXml()
        if xml_root is None:
            return None

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
                    asset_info = g_assetFactory.get_asset_info_by_key(xml_tag)
                    asset_data = { 'filepath': text_XML_line, 'asset_type': asset_info.id }
                    assets.append(Asset(asset_data))
                
            # --- Add category to categories dictionary ---
            logger.debug('Adding category "{0}" to import list'.format(category_temp['m_name']))
            yield Category(category_temp, assets)

    def get_launchers(self) -> typing.Iterator[ROMCollection]:    
        # --- Parse using cElementTree ---
        # >> If there are issues in the XML file (for example, invalid XML chars) ET.parse will fail
        logger.debug('XmlRepository.get_launchers() Loading {0}'.format(self.file_path.getPath()))

        xml_root = self.file_path.readXml()
        if xml_root is None:
            return None
            
        # >> Process tags in XML configuration file
        for root_element in xml_root:
            if self.debug: logger.debug('>>> Root child tag <{0}>'.format(root_element.tag))

            if not root_element.tag == 'launcher':
                continue
            
            assets = []
            asset_paths = []
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
                    asset_info = g_assetFactory.get_asset_info_by_key(xml_tag)
                    asset_data = { 'filepath': text_XML_line, 'asset_type': asset_info.id }
                    assets.append(Asset(asset_data))
                    
                if xml_tag.startswith('path_'):
                    asset_info = g_assetFactory.get_asset_info_by_pathkey(xml_tag)
                    asset_path_data = { 'path': text_XML_line, 'asset_type': asset_info.id }
                    asset_paths.append(AssetPath(asset_path_data))
                    
            # --- Add launcher to launchers collection ---
            logger.debug('Adding launcher "{0}" to import list'.format(launcher_temp['m_name']))
            yield ROMCollection(launcher_temp, assets, asset_paths, [], [])


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
                compatible_rom_data = self._alter_dictionary_for_compatibility(rom_data)
                scanned_data = self._get_scanned_data_from_romdata(rom_data)
                r = ROM(rom_data, assets, scanned_data=scanned_data)
                key = r.get_id()
                roms.append(r)
        else:
            for key in roms_data:
                assets = self._get_assets_from_romdata(roms_data[key])
                compatible_rom_data = self._alter_dictionary_for_compatibility(roms_data[key])
                scanned_data = self._get_scanned_data_from_romdata(roms_data[key])
                r = ROM(compatible_rom_data, assets, scanned_data=scanned_data)
                roms.append(r)

        return roms
    
    def _get_assets_from_romdata(self, rom_data: dict) -> typing.List[Asset]:
        assets = []
        for key, value in rom_data.items():
            if key.startswith('s_'):
                asset_info = g_assetFactory.get_asset_info_by_key(key)
                asset_data = { 'filepath': value, 'asset_type': asset_info.id }
                assets.append(Asset(asset_data))
        return assets

    def _get_scanned_data_from_romdata(self, rom_data: dict) -> dict:
        scanned_data = { 'file': rom_data['filepath'] }
        return scanned_data
 
    def _alter_dictionary_for_compatibility(self, rom_data: dict) -> dict:
        rom_data['rom_status'] = rom_data['fav_status'] if 'fav_status' in rom_data else None
        return rom_data
#
# UnitOfWork to be used with sqlite repositories.
# Can be used to create database scopes/sessions (unit of work pattern).
#
class UnitOfWork(object):
    VERBOSE = False

    def __init__(self, db_path: io.FileName):
        self._db_path = db_path
        self._commit = False
    
    def check_database(self) -> bool:
        if not self._db_path.exists():
            logger.warning("UnitOfWork.check_database(): Database '%s' missing" % self._db_path)
            return False

        self.open_session()
        self.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = self.result_set()

        if not len(tables) or len(tables) == 0:
            logger.warning("UnitOfWork.check_database(): Database: '%s' no tables" % self._db_path)
            self.close_session()
            return False
        
        self.close_session()
        return len(tables) > 1

    def get_database_version(self) -> str:
        self.open_session()
        
        self.execute(f"SELECT version FROM akl_version WHERE app='{globals.addon_id}';")
        sql_version = self.single_result()
        
        db_version = sql_version['version'] if sql_version else None
        
        self.close_session()
        return db_version

    def create_empty_database(self, schema_file_path: io.FileName):
        self.open_session()
        
        sql_statements = schema_file_path.loadFileToStr()
        self.execute_script(sql_statements)
        self.conn.execute("INSERT INTO akl_version VALUES(?, ?)", [globals.addon_id, globals.addon_version])

        self.commit()
        self.close_session()
        
    def reset_database(self, schema_file_path: io.FileName):
        if self._db_path.exists():
            self._db_path.unlink()
        
        # cleanup collection json files
        if globals.g_PATHS.VIEWS_DIR.exists():
            collection_files = globals.g_PATHS.VIEWS_DIR.scanFilesInPath("view_*.json")
            for collection_file in collection_files:
                collection_file.unlink()
                
        # cleanup root file
        if globals.g_PATHS.ROOT_PATH.exists():
            globals.g_PATHS.ROOT_PATH.unlink()
            
        self.create_empty_database(schema_file_path)

    def migrate_database(self, migration_files:typing.List[io.FileName]):
        self.open_session()
        
        for migration_file in migration_files:
            logger.info(f'Executing migration script: {migration_file.getPath()}')
            sql_statements = migration_file.loadFileToStr()
            self.execute_script(sql_statements)
       
        logger.info(f'Updating database schema version of app {globals.addon_id} to {globals.addon_version}')     
        self.conn.execute("UPDATE akl_version SET version=? WHERE app=?", [globals.addon_version, globals.addon_id])
        self.commit()
        self.close_session()

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
        if self.VERBOSE:
            logger.debug(f'[SQL] {sql}')
            sql_args_str = ','.join(map(str, args))
            logger.debug(f'[SQL] ARGS: {sql_args_str}')
        try:
            return self.cursor.execute(sql, args)
        except Exception as ex:
            logger.error(f'Error while executing query: {sql}', exc_info=ex)
            sql_args_str = ','.join(map(str, args))
            logger.error(f'Used arguments: {sql_args_str}')
            raise
    
    def execute_script(self, sql_statements):
        self.conn.executescript(sql_statements)
            
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
QUERY_INSERT_ASSET_PATH     = "INSERT INTO assetpaths (id, path, asset_type) VALUES (?,?,?)"
QUERY_UPDATE_METADATA       = "UPDATE metadata SET year=?, genre=?, developer=?, rating=?, plot=?, assets_path=?, finished=? WHERE id=?"
QUERY_UPDATE_ASSET          = "UPDATE assets SET filepath = ?, asset_type = ? WHERE id = ?"
QUERY_UPDATE_ASSET_PATH     = "UPDATE assetpaths SET path = ?, asset_type = ? WHERE id = ?"

#
# CategoryRepository -> Category from SQLite DB
#
QUERY_SELECT_CATEGORY                   = "SELECT * FROM vw_categories WHERE id = ?"
QUERY_SELECT_CATEGORY_ASSETS            = "SELECT * FROM vw_category_assets WHERE category_id = ?"
QUERY_SELECT_CATEGORIES                 = "SELECT * FROM vw_categories ORDER BY m_name"
QUERY_SELECT_ALL_CATEGORY_ASSETS        = "SELECT * FROM vw_category_assets"
QUERY_SELECT_ROOT_CATEGORIES            = "SELECT * FROM vw_categories WHERE parent_id IS NULL ORDER BY m_name"
QUERY_SELECT_ROOT_CATEGORY_ASSETS       = "SELECT * FROM vw_category_assets WHERE parent_id IS NULL"
QUERY_SELECT_CATEGORIES_BY_PARENT       = "SELECT * FROM vw_categories WHERE parent_id = ? ORDER BY m_name"
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
        if category_id == constants.VCATEGORY_ADDONROOT_ID: return Category({'m_name': 'Root'})
        
        self._uow.execute(QUERY_SELECT_CATEGORY, category_id)
        category_data = self._uow.single_result()
                
        self._uow.execute(QUERY_SELECT_CATEGORY_ASSETS, category_id)
        assets_result_set = self._uow.result_set()
                
        assets = []
        for asset_data in assets_result_set:
            assets.append(Asset(asset_data))    
            
        return Category(category_data, assets)

    def find_root_categories(self) -> typing.Iterator[Category]:
        self._uow.execute(QUERY_SELECT_ROOT_CATEGORIES)
        result_set = self._uow.result_set()
        
        self._uow.execute(QUERY_SELECT_ROOT_CATEGORY_ASSETS)
        assets_result_set = self._uow.result_set()
                    
        for category_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['category_id'] == category_data['id'], assets_result_set):
                assets.append(Asset(asset_data))    
                
            yield Category(category_data, assets)

    def find_categories_by_parent(self, category_id) -> typing.Iterator[Category]:
        
        if category_id == constants.VCATEGORY_ROOT_ID:
            for vcategory_id in constants.VCATEGORIES:
                yield VirtualCategoryFactory.create(vcategory_id)
        
        if category_id in constants.VCATEGORIES: return []
        
        self._uow.execute(QUERY_SELECT_CATEGORIES_BY_PARENT, category_id)
        result_set = self._uow.result_set()
        
        self._uow.execute(QUERY_SELECT_CATEGORY_ASSETS_BY_PARENT, category_id)
        assets_result_set = self._uow.result_set()
                    
        for category_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['category_id'] == category_data['id'], assets_result_set):
                assets.append(Asset(asset_data))    
                
            yield Category(category_data, assets)

    def find_all_categories(self) -> typing.Iterator[Category]:
        self._uow.execute(QUERY_SELECT_CATEGORIES)
        result_set = self._uow.result_set()
        
        self._uow.execute(QUERY_SELECT_ALL_CATEGORY_ASSETS)
        assets_result_set = self._uow.result_set()
                    
        for category_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['category_id'] == category_data['id'], assets_result_set):
                assets.append(Asset(asset_data))    
                
            yield Category(category_data, assets)

    def insert_category(self, category_obj: Category, parent_obj: Category = None):
        logger.info("CategoryRepository.insert_category(): Inserting new category '{}'".format(category_obj.get_name()))
        metadata_id = text.misc_generate_random_SID()
        assets_path = category_obj.get_assets_root_path()
        parent_category_id = parent_obj.get_id() if parent_obj is not None and parent_obj.get_id() != constants.VCATEGORY_ADDONROOT_ID else None
        
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
            parent_category_id,
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
        assets_path = category_obj.get_assets_root_path()
        
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
# ROMCollectionRepository -> ROM Sets from SQLite DB
#
QUERY_COUNT_ROMCOLLECTIONS             = "SELECT COUNT(*) as count FROM vw_romcollections"
QUERY_SELECT_ROMCOLLECTION             = "SELECT * FROM vw_romcollections WHERE id = ?"
QUERY_SELECT_ROMCOLLECTIONS            = "SELECT * FROM vw_romcollections ORDER BY m_name"
QUERY_SELECT_ROOT_ROMCOLLECTIONS       = "SELECT * FROM vw_romcollections WHERE parent_id IS NULL ORDER BY m_name"
QUERY_SELECT_ROMCOLLECTIONS_BY_PARENT  = "SELECT * FROM vw_romcollections WHERE parent_id = ? ORDER BY m_name"
QUERY_SELECT_ROMCOLLECTIONS_BY_ROM     = "SELECT rs.* FROM vw_romcollections AS rs INNER JOIN roms_in_romcollection AS rr ON rr.romcollection_id = rs.id WHERE rr.rom_id = ?"

QUERY_SELECT_VCOLLECTION_TITLES     = "SELECT DISTINCT(SUBSTR(UPPER(m_name), 1,1)) AS option_value FROM vw_roms"   
QUERY_SELECT_VCOLLECTION_GENRES     = "SELECT DISTINCT(m_genre) AS option_value FROM vw_roms"   
QUERY_SELECT_VCOLLECTION_DEVELOPER  = "SELECT DISTINCT(m_developer) AS option_value FROM vw_roms"   
QUERY_SELECT_VCOLLECTION_ESRB       = "SELECT DISTINCT(m_esrb) AS option_value FROM vw_roms"   
QUERY_SELECT_VCOLLECTION_YEAR       = "SELECT DISTINCT(m_year) AS option_value FROM vw_roms"   
QUERY_SELECT_VCOLLECTION_NPLAYERS   = "SELECT DISTINCT(m_nplayers) AS option_value FROM vw_roms"   
QUERY_SELECT_VCOLLECTION_RATING     = "SELECT DISTINCT(m_rating) AS option_value FROM vw_roms"   

QUERY_INSERT_ROMCOLLECTION               = """
                                    INSERT INTO romcollections (
                                            id,name,parent_id,metadata_id,platform,box_size, 
                                            default_icon,default_fanart,default_banner,default_poster,default_controller,default_clearlogo,
                                            roms_default_icon,roms_default_fanart,roms_default_banner,roms_default_poster,roms_default_clearlogo
                                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                                    """
QUERY_UPDATE_ROMCOLLECTION               = """
                                    UPDATE romcollections SET 
                                        name=?, platform=?, box_size=?, 
                                        default_icon=?, default_fanart=?, default_banner=?, default_poster=?, default_controller=?, default_clearlogo=?,
                                        roms_default_icon=?, roms_default_fanart=?, roms_default_banner=?, roms_default_poster=?, roms_default_clearlogo=?
                                        WHERE id =?
                                    """
QUERY_DELETE_ROMCOLLECTION               = "DELETE FROM romcollection WHERE id = ?"

QUERY_SELECT_ROMCOLLECTION_ASSETS_BY_SET       = "SELECT * FROM vw_romcollection_assets WHERE romcollection_id = ?"
QUERY_SELECT_ROOT_ROMCOLLECTION_ASSETS         = "SELECT * FROM vw_romcollection_assets WHERE parent_id IS NULL"
QUERY_SELECT_ROMCOLLECTIONS_ASSETS_BY_PARENT   = "SELECT * FROM vw_romcollection_assets WHERE parent_id = ?"
QUERY_SELECT_ROMCOLLECTION_ASSETS_BY_ROM       = "SELECT ra.* FROM vw_romcollection_assets AS ra INNER JOIN roms_in_romcollection AS rr ON rr.romcollection_id = ra.romcollection_id WHERE rr.rom_id = ?"
QUERY_SELECT_ROMCOLLECTION_ASSETS              = "SELECT * FROM vw_romcollection_assets"
QUERY_SELECT_ROMCOLLECTION_ASSET_PATHS         = "SELECT * FROM vw_romcollection_asset_paths WHERE romcollection_id = ?"
QUERY_SELECT_ROMCOLLECTION_ASSETS_PATHS_BY_ROM = "SELECT rap.* FROM vw_romcollection_asset_paths AS rap INNER JOIN roms_in_romcollection AS rr ON rr.romcollection_id = rap.romcollection_id WHERE rr.rom_id = ?"

QUERY_INSERT_ROMCOLLECTION_ASSET               = "INSERT INTO romcollection_assets (romcollection_id, asset_id) VALUES (?, ?)"
QUERY_INSERT_ROMCOLLECTION_ASSET_PATH          = "INSERT INTO romcollection_assetpaths (romcollection_id, assetpaths_id) VALUES (?, ?)"

QUERY_INSERT_ROM_IN_ROMCOLLECTION        = "INSERT INTO roms_in_romcollection (rom_id, romcollection_id) VALUES (?,?)"
QUERY_REMOVE_ROM_FROM_ROMCOLLECTION      = "DELETE FROM roms_in_romcollection WHERE rom_id = ? AND romcollection_id = ?"
QUERY_REMOVE_ROMS_FROM_ROMCOLLECTION    =  "DELETE FROM roms_in_romcollection WHERE romcollection_id = ?"

QUERY_SELECT_ROMCOLLECTION_LAUNCHERS     = "SELECT * FROM vw_romcollection_launchers WHERE romcollection_id = ?"
QUERY_INSERT_ROMCOLLECTION_LAUNCHER      = "INSERT INTO romcollection_launchers (id, romcollection_id, akl_addon_id, settings, is_default) VALUES (?,?,?,?,?)"
QUERY_UPDATE_ROMCOLLECTION_LAUNCHER      = "UPDATE romcollection_launchers SET settings = ?, is_default = ? WHERE id = ?"
QUERY_DELETE_ROMCOLLECTION_LAUNCHERS     = "DELETE FROM romcollection_launchers WHERE romcollection_id = ?"
QUERY_DELETE_ROMCOLLECTION_LAUNCHER      = "DELETE FROM romcollection_launchers WHERE romcollection_id = ? AND id = ?"

QUERY_SELECT_ROMCOLLECTION_SCANNERS      = "SELECT * FROM vw_romcollection_scanners WHERE romcollection_id = ?"
QUERY_INSERT_ROMCOLLECTION_SCANNER       = "INSERT INTO romcollection_scanners (id, romcollection_id, akl_addon_id, settings) VALUES (?,?,?,?)"
QUERY_UPDATE_ROMCOLLECTION_SCANNER       = "UPDATE romcollection_scanners SET settings = ? WHERE id = ?"
QUERY_DELETE_ROMCOLLECTION_SCANNER       = "DELETE FROM romcollection_scanners WHERE romcollection_id = ? AND id = ?"

QUERY_SELECT_ROMCOLLECTION_LAUNCHERS_BY_ROM = "SELECT rl.* FROM vw_romcollection_launchers AS rl INNER JOIN roms_in_romcollection AS rr ON rr.romcollection_id = rl.romcollection_id WHERE rr.rom_id = ?"
QUERY_SELECT_ROMCOLLECTION_SCANNERS_BY_ROM  = "SELECT rs.* FROM vw_romcollection_scanners AS rs INNER JOIN roms_in_romcollection AS rr ON rr.romcollection_id = rs.romcollection_id WHERE rr.rom_id = ?"

class ROMCollectionRepository(object):

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def count_collections(self) -> int:
        self._uow.execute(QUERY_COUNT_ROMCOLLECTIONS)
        count_data = self._uow.single_result()
        
        return int(count_data['count'])

    def find_romcollection(self, romcollection_id: str) -> ROMCollection:
        self._uow.execute(QUERY_SELECT_ROMCOLLECTION, romcollection_id)
        romcollection_data = self._uow.single_result()
        
        self._uow.execute(QUERY_SELECT_ROMCOLLECTION_ASSETS_BY_SET, romcollection_id)
        assets_result_set = self._uow.result_set()
        assets = []
        for asset_data in assets_result_set:
            assets.append(Asset(asset_data))
            
        self._uow.execute(QUERY_SELECT_ROMCOLLECTION_ASSET_PATHS, romcollection_id)
        asset_paths_result_set = self._uow.result_set()
        asset_paths = []
        for asset_paths_data in asset_paths_result_set:
            asset_paths.append(AssetPath(asset_paths_data))
        
        self._uow.execute(QUERY_SELECT_ROMCOLLECTION_LAUNCHERS, romcollection_id)
        launchers_data = self._uow.result_set()
        launchers = []
        for launcher_data in launchers_data:
            addon = AelAddon(launcher_data.copy())
            launcher = ROMLauncherAddonFactory.create(addon, launcher_data)
            launchers.append(launcher)
        
        self._uow.execute(QUERY_SELECT_ROMCOLLECTION_SCANNERS, romcollection_id)
        scanners_data = self._uow.result_set()
        scanners = []
        for scanner_data in scanners_data:
            addon = AelAddon(scanner_data.copy())
            scanners.append(ROMCollectionScanner(addon, scanner_data))
            
        return ROMCollection(romcollection_data, assets, asset_paths, launchers, scanners)
    
    def find_all_romcollections(self) -> typing.Iterator[ROMCollection]:
        self._uow.execute(QUERY_SELECT_ROMCOLLECTIONS)
        result_set = self._uow.result_set()
        
        self._uow.execute(QUERY_SELECT_ROMCOLLECTION_ASSETS)
        assets_result_set = self._uow.result_set()
                
        for romcollection_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['romcollection_id'] == romcollection_data['id'], assets_result_set):
                assets.append(Asset(asset_data))      
                
            yield ROMCollection(romcollection_data, assets)

    def find_root_romcollections(self) -> typing.Iterator[ROMCollection]:
        self._uow.execute(QUERY_SELECT_ROOT_ROMCOLLECTIONS)
        result_set = self._uow.result_set()
        
        self._uow.execute(QUERY_SELECT_ROOT_ROMCOLLECTION_ASSETS)
        assets_result_set = self._uow.result_set()
                
        for romcollection_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['romcollection_id'] == romcollection_data['id'], assets_result_set):
                assets.append(Asset(asset_data))      
                
            yield ROMCollection(romcollection_data, assets)

    def find_romcollections_by_parent(self, category_id:str) -> typing.Iterator[ROMCollection]:
        
        if category_id in constants.VCATEGORIES:
            for collection in self.find_virtualcollections_by_category(category_id):
                yield collection
        
        self._uow.execute(QUERY_SELECT_ROMCOLLECTIONS_BY_PARENT, category_id)
        result_set = self._uow.result_set()
        
        self._uow.execute(QUERY_SELECT_ROMCOLLECTIONS_ASSETS_BY_PARENT, category_id)
        assets_result_set = self._uow.result_set()
                
        for romcollection_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['romcollection_id'] == romcollection_data['id'], assets_result_set):
                assets.append(Asset(asset_data))   
                
            yield ROMCollection(romcollection_data, assets)

    def find_virtualcollections_by_category(self, vcategory_id:str) -> typing.Iterator[VirtualCollection]:
        query = self._get_collections_query_by_vcategory_id(vcategory_id)
        if query is None: return []
        
        self._uow.execute(query)
        result_set = self._uow.result_set()
        
        for result in result_set:
            option_value = str(result['option_value'])
            if not option_value: option_value = 'Undefined'
            yield VirtualCollectionFactory.create_by_category(vcategory_id, option_value)
            
    def find_romcollections_by_rom(self, rom_id:str) -> typing.Iterator[ROMCollection]:
        self._uow.execute(QUERY_SELECT_ROMCOLLECTIONS_BY_ROM, rom_id)
        result_set = self._uow.result_set()
        
        self._uow.execute(QUERY_SELECT_ROMCOLLECTION_ASSETS_BY_ROM, rom_id)
        assets_result_set = self._uow.result_set()

        self._uow.execute(QUERY_SELECT_ROMCOLLECTION_ASSETS_PATHS_BY_ROM, rom_id)
        asset_paths_result_set = self._uow.result_set()
        
        self._uow.execute(QUERY_SELECT_ROMCOLLECTION_LAUNCHERS_BY_ROM, rom_id)
        launchers_data = self._uow.result_set()
        
        self._uow.execute(QUERY_SELECT_ROMCOLLECTION_SCANNERS_BY_ROM, rom_id)
        scanners_data = self._uow.result_set()
        
        for romcollection_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['romcollection_id'] == romcollection_data['id'], assets_result_set):
                assets.append(Asset(asset_data))      
            
            asset_paths = []
            for asset_path_data in filter(lambda a: a['romcollection_id'] == romcollection_data['id'], asset_paths_result_set):
                asset_paths.append(AssetPath(asset_path_data))      
                        
            launchers = []
            for launcher_data in launchers_data:
                addon = AelAddon(launcher_data.copy())
                launcher = ROMLauncherAddonFactory.create(addon, launcher_data)
                launchers.append(launcher)
            
            scanners = []
            for scanner_data in scanners_data:
                addon = AelAddon(scanner_data.copy())
                scanners.append(ROMCollectionScanner(addon, scanner_data))
                    
            yield ROMCollection(romcollection_data, assets, asset_paths, launchers, scanners)                       
                        
    def insert_romcollection(self, romcollection_obj: ROMCollection, parent_obj: Category = None):
        logger.info("ROMCollectionRepository.insert_romcollection(): Inserting new romcollection '{}'".format(romcollection_obj.get_name()))
        metadata_id = text.misc_generate_random_SID()
        assets_path = romcollection_obj.get_assets_root_path()
        parent_category_id = parent_obj.get_id() if parent_obj is not None and parent_obj.get_id() != constants.VCATEGORY_ADDONROOT_ID else None
        
        self._uow.execute(QUERY_INSERT_METADATA,
            metadata_id,
            romcollection_obj.get_releaseyear(),
            romcollection_obj.get_genre(),
            romcollection_obj.get_developer(),
            romcollection_obj.get_rating(),
            romcollection_obj.get_plot(),
            assets_path.getPath() if assets_path is not None else None,
            romcollection_obj.is_finished())

        self._uow.execute(QUERY_INSERT_ROMCOLLECTION,
            romcollection_obj.get_id(),
            romcollection_obj.get_name(),
            parent_category_id,
            metadata_id,
            romcollection_obj.get_platform(),
            romcollection_obj.get_box_sizing(),    
            romcollection_obj.get_mapped_asset_info(asset_id=constants.ASSET_ICON_ID).key,
            romcollection_obj.get_mapped_asset_info(asset_id=constants.ASSET_FANART_ID).key,
            romcollection_obj.get_mapped_asset_info(asset_id=constants.ASSET_BANNER_ID).key,
            romcollection_obj.get_mapped_asset_info(asset_id=constants.ASSET_POSTER_ID).key,
            romcollection_obj.get_mapped_asset_info(asset_id=constants.ASSET_CONTROLLER_ID).key,
            romcollection_obj.get_mapped_asset_info(asset_id=constants.ASSET_CLEARLOGO_ID).key,            
            romcollection_obj.get_mapped_ROM_asset_info(asset_id=constants.ASSET_ICON_ID).key,
            romcollection_obj.get_mapped_ROM_asset_info(asset_id=constants.ASSET_FANART_ID).key,
            romcollection_obj.get_mapped_ROM_asset_info(asset_id=constants.ASSET_BANNER_ID).key,
            romcollection_obj.get_mapped_ROM_asset_info(asset_id=constants.ASSET_POSTER_ID).key,
            romcollection_obj.get_mapped_ROM_asset_info(asset_id=constants.ASSET_CLEARLOGO_ID).key)
        
        romcollection_assets = romcollection_obj.get_assets()
        for asset in romcollection_assets: 
            self._insert_asset(asset, romcollection_obj)  
            
        asset_paths = romcollection_obj.get_asset_paths()
        for asset_path in asset_paths:
            self._insert_asset_path(asset_path, romcollection_obj)
            
        romcollection_launchers = romcollection_obj.get_launchers()
        for romcollection_launcher in romcollection_launchers:
            romcollection_launcher.set_id(text.misc_generate_random_SID())
            self._uow.execute(QUERY_INSERT_ROMCOLLECTION_LAUNCHER,
                romcollection_launcher.get_id(),
                romcollection_obj.get_id(), 
                romcollection_launcher.addon.get_id(), 
                romcollection_launcher.get_settings_str(), 
                romcollection_launcher.is_default())
            
        romcollection_scanners = romcollection_obj.get_scanners()
        for romcollection_scanner in romcollection_scanners:
            romcollection_scanner.set_id(text.misc_generate_random_SID())
            self._uow.execute(QUERY_INSERT_ROMCOLLECTION_SCANNER,
                romcollection_scanner.get_id(),
                romcollection_obj.get_id(), 
                romcollection_scanner.addon.get_id(), 
                romcollection_scanner.get_settings_str())
              
    def update_romcollection(self, romcollection_obj: ROMCollection):
        logger.info("ROMCollectionRepository.update_romcollection(): Updating romcollection '{}'".format(romcollection_obj.get_name()))
        assets_path = romcollection_obj.get_assets_root_path()
        
        self._uow.execute(QUERY_UPDATE_METADATA,
            romcollection_obj.get_releaseyear(),
            romcollection_obj.get_genre(),
            romcollection_obj.get_developer(),
            romcollection_obj.get_rating(),
            romcollection_obj.get_plot(),
            assets_path.getPath() if assets_path is not None else None,
            romcollection_obj.is_finished(),
            romcollection_obj.get_custom_attribute('metadata_id'))

        self._uow.execute(QUERY_UPDATE_ROMCOLLECTION,
            romcollection_obj.get_name(),
            romcollection_obj.get_platform(),
            romcollection_obj.get_box_sizing(),
            romcollection_obj.get_mapped_asset_info(asset_id=constants.ASSET_ICON_ID).key,
            romcollection_obj.get_mapped_asset_info(asset_id=constants.ASSET_FANART_ID).key,
            romcollection_obj.get_mapped_asset_info(asset_id=constants.ASSET_BANNER_ID).key,
            romcollection_obj.get_mapped_asset_info(asset_id=constants.ASSET_POSTER_ID).key,
            romcollection_obj.get_mapped_asset_info(asset_id=constants.ASSET_CONTROLLER_ID).key,
            romcollection_obj.get_mapped_asset_info(asset_id=constants.ASSET_CLEARLOGO_ID).key,            
            romcollection_obj.get_mapped_ROM_asset_info(asset_id=constants.ASSET_ICON_ID).key,
            romcollection_obj.get_mapped_ROM_asset_info(asset_id=constants.ASSET_FANART_ID).key,
            romcollection_obj.get_mapped_ROM_asset_info(asset_id=constants.ASSET_BANNER_ID).key,
            romcollection_obj.get_mapped_ROM_asset_info(asset_id=constants.ASSET_POSTER_ID).key,
            romcollection_obj.get_mapped_ROM_asset_info(asset_id=constants.ASSET_CLEARLOGO_ID).key,
            romcollection_obj.get_id())
         
        romcollection_launchers = romcollection_obj.get_launchers()
        for romcollection_launcher in romcollection_launchers:
            if romcollection_launcher.get_id() is None:
                romcollection_launcher.set_id(text.misc_generate_random_SID())
                self._uow.execute(QUERY_INSERT_ROMCOLLECTION_LAUNCHER,
                    romcollection_launcher.get_id(),
                    romcollection_obj.get_id(), 
                    romcollection_launcher.addon.get_id(), 
                    romcollection_launcher.get_settings_str(),
                    romcollection_launcher.is_default())
            else:
                self._uow.execute(QUERY_UPDATE_ROMCOLLECTION_LAUNCHER,
                    romcollection_launcher.get_settings_str(), 
                    romcollection_launcher.is_default(),
                    romcollection_launcher.get_id())
                
        romcollection_scanners = romcollection_obj.get_scanners()
        for romcollection_scanner in romcollection_scanners:
            if romcollection_scanner.get_id() is None:
                romcollection_scanner.set_id(text.misc_generate_random_SID())
                self._uow.execute(QUERY_INSERT_ROMCOLLECTION_SCANNER,
                    romcollection_scanner.get_id(),
                    romcollection_obj.get_id(), 
                    romcollection_scanner.addon.get_id(), 
                    romcollection_scanner.get_settings_str())
            else:
                self._uow.execute(QUERY_UPDATE_ROMCOLLECTION_SCANNER,
                    romcollection_scanner.get_settings_str(), 
                    romcollection_scanner.get_id())

        for asset in romcollection_obj.get_assets():
            if asset.get_id() == '': self._insert_asset(asset, romcollection_obj)
            else: self._update_asset(asset, romcollection_obj)   
                  
        for asset_path in romcollection_obj.get_asset_paths():
            if asset_path.get_id() == '': self._insert_asset_path(asset_path, romcollection_obj)
            else: self._update_asset_path(asset_path, romcollection_obj)           
            
    def add_rom_to_romcollection(self, romcollection_id: str, rom_id: str):
        self._uow.execute(QUERY_INSERT_ROM_IN_ROMCOLLECTION, rom_id, romcollection_id)
            
    def remove_rom_from_romcollection(self, romcollection_id: str, rom_id: str):
        self._uow.execute(QUERY_REMOVE_ROM_FROM_ROMCOLLECTION, rom_id, romcollection_id)
        
    def remove_all_roms_in_launcher(self, romcollection_id: str):
        self._uow.execute(QUERY_REMOVE_ROMS_FROM_ROMCOLLECTION, romcollection_id)
        
    def delete_romcollection(self, romcollection_id: str):
        logger.info("ROMCollectionRepository.delete_romcollection(): Deleting romcollection '{}'".format(romcollection_id))
        self._uow.execute(QUERY_DELETE_ROMCOLLECTION, romcollection_id)

    def remove_launcher(self, romcollection_id: str, launcher_id:str):
        self._uow.execute(QUERY_DELETE_ROMCOLLECTION_LAUNCHER, romcollection_id, launcher_id)

    def remove_scanner(self, romcollection_id: str, scanner_id:str):
        self._uow.execute(QUERY_DELETE_ROMCOLLECTION_SCANNER, romcollection_id, scanner_id)

    def _insert_asset(self, asset: Asset, romcollection_obj: ROMCollection):
        asset_db_id = text.misc_generate_random_SID()
        self._uow.execute(QUERY_INSERT_ASSET, asset_db_id, asset.get_path(), asset.get_asset_info_id())
        self._uow.execute(QUERY_INSERT_ROMCOLLECTION_ASSET, romcollection_obj.get_id(), asset_db_id)
    
    def _update_asset(self, asset: Asset, romcollection_obj: ROMCollection):
        self._uow.execute(QUERY_UPDATE_ASSET, asset.get_path(), asset.get_asset_info_id(), asset.get_id())
        if asset.get_custom_attribute('romcollection_id') is None:
            self._uow.execute(QUERY_INSERT_ROMCOLLECTION_ASSET, romcollection_obj.get_id(), asset.get_id())     
    
    def _insert_asset_path(self, asset_path: AssetPath, romcollection_obj: ROMCollection):
        asset_db_id = text.misc_generate_random_SID()
        self._uow.execute(QUERY_INSERT_ASSET_PATH, asset_db_id, asset_path.get_path(), asset_path.get_asset_info_id())
        self._uow.execute(QUERY_INSERT_ROMCOLLECTION_ASSET_PATH, romcollection_obj.get_id(), asset_db_id)    
        
    def _update_asset_path(self, asset_path: AssetPath, romcollection_obj: ROMCollection):
        self._uow.execute(QUERY_UPDATE_ASSET_PATH, asset_path.get_path(), asset_path.get_asset_info_id(), asset_path.get_id())
        if asset_path.get_custom_attribute('romcollection_id') is None:
            self._uow.execute(QUERY_INSERT_ROMCOLLECTION_ASSET_PATH, romcollection_obj.get_id(), asset_path.get_id())     
            
    def _get_collections_query_by_vcategory_id(self, vcategory_id:str) -> str:
            
        if vcategory_id == constants.VCATEGORY_TITLE_ID:    return QUERY_SELECT_VCOLLECTION_TITLES   
        if vcategory_id == constants.VCATEGORY_GENRE_ID:    return QUERY_SELECT_VCOLLECTION_GENRES
        if vcategory_id == constants.VCATEGORY_DEVELOPER_ID:return QUERY_SELECT_VCOLLECTION_DEVELOPER
        if vcategory_id == constants.VCATEGORY_ESRB_ID:     return QUERY_SELECT_VCOLLECTION_ESRB
        if vcategory_id == constants.VCATEGORY_YEARS_ID:    return QUERY_SELECT_VCOLLECTION_YEAR
        if vcategory_id == constants.VCATEGORY_NPLAYERS_ID: return QUERY_SELECT_VCOLLECTION_NPLAYERS
        if vcategory_id == constants.VCATEGORY_RATING_ID:   return QUERY_SELECT_VCOLLECTION_RATING

        return None             
#
# ROMsRepository -> ROMs from SQLite DB
#     
QUERY_SELECT_ROM                    = "SELECT * FROM vw_roms WHERE id = ?"
QUERY_SELECT_ROMS_BY_SET            = "SELECT r.* FROM vw_roms AS r INNER JOIN roms_in_romcollection AS rs ON rs.rom_id = r.id AND rs.romcollection_id = ?"
QUERY_SELECT_ROM_ASSETS             = "SELECT * FROM vw_rom_assets WHERE rom_id = ?"
QUERY_SELECT_ROM_ASSETPATHS         = "SELECT * FROM vw_rom_asset_paths WHERE rom_id = ?"
QUERY_SELECT_ROM_ASSETS_BY_SET      = "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN roms_in_romcollection AS rs ON rs.rom_id = ra.rom_id AND rs.romcollection_id = ?"
QUERY_SELECT_ROM_ASSETPATHS_BY_SET  = "SELECT rap.* FROM vw_rom_asset_paths AS rap INNER JOIN roms_in_romcollection AS rs ON rs.rom_id = rap.rom_id AND rs.romcollection_id = ?"
QUERY_SELECT_ROM_TAGS_BY_SET        = "SELECT rt.* FROM vw_rom_tags AS rt INNER JOIN roms_in_romcollection AS rs ON rs.rom_id = rt.rom_id AND rs.romcollection_id = ?"
QUERY_SELECT_ROM_TAGS               = "SELECT * FROM vw_rom_tags WHERE rom_id = ?"

QUERY_INSERT_ROM                = """
                                INSERT INTO roms (
                                    id, metadata_id, name, num_of_players, num_of_players_online, esrb_rating,
                                    platform, box_size, nointro_status, cloneof, rom_status, scanned_by_id)
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                                """ 

QUERY_SELECT_MY_FAVOURITES               = "SELECT * FROM vw_roms WHERE is_favourite = 1"                                
QUERY_SELECT_RECENTLY_PLAYED_ROMS        = "SELECT * FROM vw_roms WHERE last_launch_timestamp IS NOT NULL ORDER BY last_launch_timestamp DESC LIMIT 100"
QUERY_SELECT_MOST_PLAYED_ROMS            = "SELECT * FROM vw_roms WHERE launch_count > 0 ORDER BY launch_count DESC LIMIT 100"
QUERY_SELECT_FAVOURITES_ROM_ASSETS       = "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN roms AS r ON r.id = ra.rom_id WHERE r.is_favourite = 1"
QUERY_SELECT_RECENTLY_PLAYED_ROM_ASSETS  = """
                                            SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN roms AS r ON r.id = ra.rom_id 
                                            WHERE r.last_launch_timestamp IS NOT NULL ORDER BY last_launch_timestamp DESC LIMIT 100
                                           """
QUERY_SELECT_MOST_PLAYED_ROM_ASSETS      = """
                                            SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN roms AS r ON r.id = ra.rom_id 
                                            WHERE r.launch_count > 0 ORDER BY launch_count DESC LIMIT 100
                                           """

QUERY_SELECT_BY_TITLE        = "SELECT * FROM vw_roms WHERE m_name LIKE ? || '%'"
QUERY_SELECT_BY_GENRE        = "SELECT * FROM vw_roms WHERE m_genre = ?"
QUERY_SELECT_BY_DEVELOPER    = "SELECT * FROM vw_roms WHERE m_developer = ?"
QUERY_SELECT_BY_YEAR         = "SELECT * FROM vw_roms WHERE m_year = ?"
QUERY_SELECT_BY_NPLAYERS     = "SELECT * FROM vw_roms WHERE m_nplayers = ?"
QUERY_SELECT_BY_ESRB         = "SELECT * FROM vw_roms WHERE m_esrb = ?"
QUERY_SELECT_BY_RATING       = "SELECT * FROM vw_roms WHERE m_rating = ?"
                                
QUERY_SELECT_BY_TITLE_ASSETS    = "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN vw_roms AS r ON r.id = ra.rom_id WHERE UPPER(r.m_name) LIKE ? || '%'"
QUERY_SELECT_BY_GENRE_ASSETS    = "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN vw_roms AS r ON r.id = ra.rom_id WHERE r.m_genre = ?"
QUERY_SELECT_BY_DEVELOPER_ASSETS= "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN vw_roms AS r ON r.id = ra.rom_id WHERE r.m_developer = ?"
QUERY_SELECT_BY_YEAR_ASSETS     = "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN vw_roms AS r ON r.id = ra.rom_id WHERE r.m_year = ?"
QUERY_SELECT_BY_NPLAYERS_ASSETS = "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN vw_roms AS r ON r.id = ra.rom_id WHERE r.m_nplayers = ?"
QUERY_SELECT_BY_ESRB_ASSETS     = "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN vw_roms AS r ON r.id = ra.rom_id WHERE r.m_esrb = ?"
QUERY_SELECT_BY_RATING_ASSETS   = "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN vw_roms AS r ON r.id = ra.rom_id WHERE r.m_rating = ?"
                                
QUERY_INSERT_ROM_ASSET          = "INSERT INTO rom_assets (rom_id, asset_id) VALUES (?, ?)"
QUERY_INSERT_ROM_ASSET_PATH     = "INSERT INTO rom_assetpaths (rom_id, assetpaths_id) VALUES (?, ?)"
QUERY_INSERT_ROM_SCANNED_DATA   = "INSERT INTO scanned_roms_data (rom_id, data_key, data_value) VALUES (?, ?, ?)"

QUERY_UPDATE_ROM                = """
                                  UPDATE roms 
                                  SET name=?, num_of_players=?, num_of_players_online=?, esrb_rating=?, platform=?, box_size=?,
                                  nointro_status=?, cloneof=?, rom_status=?, launch_count=?, last_launch_timestamp=?,
                                  is_favourite=?, scanned_by_id=? WHERE id =?
                                  """
QUERY_DELETE_ROM                = "DELETE FROM roms WHERE id = ?"
QUERY_DELETE_ROMS_BY_COLLECTION = "DELETE FROM roms WHERE id IN (SELECT rc.rom_id FROM roms_in_romcollection AS rc WHERE rc.romcollection_id = ?)"

QUERY_SELECT_ROM_SCANNED_DATA        = "SELECT s.* FROM scanned_roms_data AS s WHERE s.rom_id = ?"
QUERY_SELECT_ROM_SCANNED_DATA_BY_SET = "SELECT s.* FROM scanned_roms_data AS s INNER JOIN roms_in_romcollection AS rs ON rs.rom_id = s.rom_id AND rs.romcollection_id = ?"
QUERY_DELETE_SCANNED_DATA            = "DELETE FROM scanned_roms_data WHERE rom_id = ?"

QUERY_SELECT_ROM_LAUNCHERS     = "SELECT * FROM vw_rom_launchers WHERE rom_id = ?"
QUERY_INSERT_ROM_LAUNCHER      = "INSERT INTO rom_launchers (id, rom_id, akl_addon_id, settings, is_default) VALUES (?,?,?,?,?)"
QUERY_UPDATE_ROM_LAUNCHER      = "UPDATE rom_launchers SET settings = ?, is_default = ? WHERE id = ?"
QUERY_DELETE_ROM_LAUNCHERS     = "DELETE FROM rom_launchers WHERE rom_id = ?"
QUERY_DELETE_ROM_LAUNCHER      = "DELETE FROM rom_launchers WHERE romcollection_id = ? AND id = ?"

QUERY_SELECT_TAGS               = "SELECT * FROM tags"
QUERY_INSERT_TAG                = "INSERT INTO tags (id, tag) VALUES (?,?)" 
QUERY_ADD_TAG_TO_ROM            = "INSERT INTO metatags (metadata_id, tag_id) VALUES (?,?)"
QUERY_DELETE_EXISTING_ROM_TAGS  = "DELETE FROM metatags WHERE metadata_id = ?"

class ROMsRepository(object):
       
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def find_roms_by_romcollection(self, romcollection: ROMCollection) -> typing.Iterator[ROM]:
        is_virtual = romcollection.get_type() == constants.OBJ_COLLECTION_VIRTUAL
        romcollection_id = romcollection.get_id()
        
        if is_virtual:
            vcollection:VirtualCollection = romcollection
            query_param = vcollection.get_collection_value()
            roms_query, rom_assets_query = self._get_queries_by_vcollection_type(romcollection)
            
            if query_param is not None:
                self._uow.execute(roms_query, query_param) 
                result_set = self._uow.result_set()            
                self._uow.execute(rom_assets_query, query_param)
                assets_result_set = self._uow.result_set() 
            else: 
                self._uow.execute(roms_query) 
                result_set = self._uow.result_set()            
                self._uow.execute(rom_assets_query)
                assets_result_set = self._uow.result_set() 
                    
            asset_paths_result_set  = []
            scanned_data_result_set = []
            tags_data_set = {}      
        else:
            self._uow.execute(QUERY_SELECT_ROMS_BY_SET, romcollection_id)
            result_set = self._uow.result_set()
            
            self._uow.execute(QUERY_SELECT_ROM_ASSETS_BY_SET, romcollection_id)
            assets_result_set = self._uow.result_set()
            
            self._uow.execute(QUERY_SELECT_ROM_ASSETPATHS_BY_SET, romcollection_id)
            asset_paths_result_set = self._uow.result_set()
                        
            self._uow.execute(QUERY_SELECT_ROM_SCANNED_DATA_BY_SET, romcollection_id)
            scanned_data_result_set = self._uow.result_set()

            self._uow.execute(QUERY_SELECT_ROM_TAGS_BY_SET, romcollection_id)
            tags_data_set = self._uow.result_set()
                        
        for rom_data in result_set:
            assets = []
            asset_paths = []
            tags = {}
            for asset_data in filter(lambda a: a['rom_id'] == rom_data['id'], assets_result_set):
                assets.append(Asset(asset_data))    
            for asset_paths_data in filter(lambda a: a['rom_id'] == rom_data['id'], asset_paths_result_set):
                asset_paths.append(AssetPath(asset_paths_data))
            for tag in filter(lambda t: t['rom_id'] == rom_data['id'], tags_data_set):
                tags[tag['tag']] = tag['id']
                
            scanned_data = {
                entry['data_key']: entry['data_value'] 
                for entry in filter(lambda s: s['rom_id'] == rom_data['id'], scanned_data_result_set) 
            }
            yield ROM(rom_data, tags, assets, asset_paths, scanned_data)

    def find_rom(self, rom_id:str) -> ROM:
        self._uow.execute(QUERY_SELECT_ROM, rom_id)
        rom_data = self._uow.single_result()

        self._uow.execute(QUERY_SELECT_ROM_ASSETS, rom_id)
        assets_result_set = self._uow.result_set()            
        assets = []
        for asset_data in assets_result_set:
            assets.append(Asset(asset_data))
                                
        self._uow.execute(QUERY_SELECT_ROM_ASSETPATHS, rom_id)
        asset_paths_result_set = self._uow.result_set()
        asset_paths = []
        for asset_paths_data in asset_paths_result_set:
            asset_paths.append(AssetPath(asset_paths_data))
        
        self._uow.execute(QUERY_SELECT_ROM_SCANNED_DATA, rom_id)
        scanned_data_result_set = self._uow.result_set()
        scanned_data = { entry['data_key']: entry['data_value'] for entry in scanned_data_result_set }    
        
        self._uow.execute(QUERY_SELECT_ROM_LAUNCHERS, rom_id)
        launchers_data = self._uow.result_set()
        launchers = []
        for launcher_data in launchers_data:
            addon = AelAddon(launcher_data.copy())
            launcher = ROMLauncherAddonFactory.create(addon, launcher_data)
            launchers.append(launcher)

        self._uow.execute(QUERY_SELECT_ROM_TAGS, rom_id)
        tags_data = self._uow.result_set()
        tags = {}
        for tag_data in tags_data:
            tags[tag_data['tag']] = tag_data['id']
            
        return ROM(rom_data, tags, assets, asset_paths, scanned_data, launchers)

    def insert_rom(self, rom_obj: ROM): 
        logger.info(f"ROMsRepository.insert_rom(): Inserting new ROM '{rom_obj.get_name()}'")
        metadata_id = text.misc_generate_random_SID()
        assets_path = rom_obj.get_assets_root_path()
        
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
            rom_obj.get_number_of_players_online(),
            rom_obj.get_esrb_rating(),   
            rom_obj.get_platform(),
            rom_obj.get_box_sizing(), 
            rom_obj.get_nointro_status(),
            rom_obj.get_clone(),
            rom_obj.get_rom_status(),
            rom_obj.get_scanned_with())
        
        rom_assets = rom_obj.get_assets()
        for asset in rom_assets:
            self._insert_asset(asset, rom_obj)
            
        for asset_path in rom_obj.get_asset_paths():
            if not asset_path.get_id(): self._insert_asset_path(asset_path, rom_obj)
            else: self._update_asset_path(asset_path, rom_obj)

        tag_data = rom_obj.get_tag_data()
        self._insert_tags(tag_data, metadata_id)

        self._update_scanned_data(rom_obj.get_id(), rom_obj.scanned_data)
        self._update_launchers(rom_obj.get_id(), rom_obj.get_launchers())

    def update_rom(self, rom_obj: ROM):
        logger.info("ROMsRepository.update_rom(): Updating ROM '{}'".format(rom_obj.get_name()))
        assets_path = rom_obj.get_assets_root_path()
        
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
            rom_obj.get_number_of_players_online(),
            rom_obj.get_esrb_rating(),
            rom_obj.get_platform(),
            rom_obj.get_box_sizing(),
            rom_obj.get_nointro_status(),
            rom_obj.get_clone(),
            rom_obj.get_rom_status(),
            rom_obj.get_launch_count(),
            rom_obj.get_last_launch_date(),
            rom_obj.is_favourite(),
            rom_obj.get_scanned_with(),
            rom_obj.get_id())
        
        for asset in rom_obj.get_assets():
            if not asset.get_id(): self._insert_asset(asset, rom_obj)
            else: self._update_asset(asset, rom_obj)            
        
        for asset_path in rom_obj.get_asset_paths():
            if not asset_path.get_id(): self._insert_asset_path(asset_path, rom_obj)
            else: self._update_asset_path(asset_path, rom_obj)    

        tag_data = rom_obj.get_tag_data()
        self._update_tags(tag_data, rom_obj.get_custom_attribute('metadata_id'))

        self._update_scanned_data(rom_obj.get_id(),rom_obj.scanned_data)
        self._update_launchers(rom_obj.get_id(), rom_obj.get_launchers())
                
    def delete_rom(self, rom_id: str):
        logger.info("ROMsRepository.delete_rom(): Deleting ROM '{}'".format(rom_id))
        self._uow.execute(QUERY_DELETE_ROM, rom_id)
    
    def delete_roms_by_romcollection(self, romcollection_id:str):
        self._uow.execute(QUERY_DELETE_ROMS_BY_COLLECTION, romcollection_id)
           
    def _insert_asset(self, asset: Asset, rom_obj: ROM):
        asset_db_id = text.misc_generate_random_SID()
        self._uow.execute(QUERY_INSERT_ASSET, asset_db_id, asset.get_path(), asset.get_asset_info_id())
        self._uow.execute(QUERY_INSERT_ROM_ASSET, rom_obj.get_id(), asset_db_id)   
    
    def _update_asset(self, asset: Asset, rom_obj: ROM):
        self._uow.execute(QUERY_UPDATE_ASSET, asset.get_path(), asset.get_asset_info_id(), asset.get_id())
        if asset.get_custom_attribute('rom_id') is None:
            self._uow.execute(QUERY_INSERT_ROM_ASSET, rom_obj.get_id(), asset.get_id())   

    def _insert_asset_path(self, asset_path: AssetPath, rom_obj: ROM):
        asset_db_id = text.misc_generate_random_SID()
        self._uow.execute(QUERY_INSERT_ASSET_PATH, asset_db_id, asset_path.get_path(), asset_path.get_asset_info_id())
        self._uow.execute(QUERY_INSERT_ROM_ASSET_PATH, rom_obj.get_id(), asset_db_id)    
        
    def _update_asset_path(self, asset_path: AssetPath, rom_obj: ROM):
        self._uow.execute(QUERY_UPDATE_ASSET_PATH, asset_path.get_path(), asset_path.get_asset_info_id(), asset_path.get_id())
        if asset_path.get_custom_attribute('rom_id') is None:
            self._uow.execute(QUERY_INSERT_ROM_ASSET_PATH, rom_obj.get_id(), asset_path.get_id())     
    
    def _update_launchers(self, rom_id:str, rom_launchers:typing.List[ROMLauncherAddon]):        
        for rom_launcher in rom_launchers:
            if rom_launcher.get_id() is None:
                rom_launcher.set_id(text.misc_generate_random_SID())
                self._uow.execute(QUERY_INSERT_ROMCOLLECTION_LAUNCHER,
                    rom_launcher.get_id(),
                    rom_id, 
                    rom_launcher.addon.get_id(), 
                    rom_launcher.get_settings_str(), 
                    rom_launcher.is_default())
            else:
                self._uow.execute(QUERY_UPDATE_ROMCOLLECTION_LAUNCHER,
                    rom_launcher.get_settings_str(), 
                    rom_launcher.is_default(),
                    rom_launcher.get_id())
    
    def _update_scanned_data(self, rom_id:str, scanned_data:dict):
        self._uow.execute(QUERY_DELETE_SCANNED_DATA, rom_id)
        for key, value in scanned_data.items():
            self._uow.execute(QUERY_INSERT_ROM_SCANNED_DATA, rom_id, key, value)

    def _get_tags(self) -> dict:
        self._uow.execute(QUERY_SELECT_TAGS)
        tag_data = self._uow.result_set()
        tags = {}
        for tag in tag_data:
            tags[tag['tag']] = tag['id']
        return tags

    def _update_tags(self, tag_data:dict, metadata_id:str):
        self._uow.execute(QUERY_DELETE_EXISTING_ROM_TAGS, metadata_id)
        self._insert_tags(tag_data, metadata_id)

    def _insert_tags(self, tag_data:dict, metadata_id:str):
        existing_tags = self._get_tags()
        for tag_name, tag_id in tag_data.items():
            if tag_id == '':
                if not tag_name in existing_tags.keys():
                    tag_id = self._insert_tag(tag_name)
                else:
                    tag_id = existing_tags[tag_name]
            self._uow.execute(QUERY_ADD_TAG_TO_ROM, metadata_id, tag_id)

    def _insert_tag(self, tag:str) -> str:
        db_id = text.misc_generate_random_SID()
        self._uow.execute(QUERY_INSERT_TAG, db_id, tag)
        return db_id

    def _get_queries_by_vcollection_type(self, vcollection:VirtualCollection) -> typing.Tuple[str, str]:
        
        vcollection_id  = vcollection.get_id()
        vcategory_id    = vcollection.get_parent_id()
        
        if vcategory_id is not None:            
            if vcategory_id == constants.VCATEGORY_TITLE_ID:     return QUERY_SELECT_BY_TITLE, QUERY_SELECT_BY_TITLE_ASSETS            
            if vcategory_id == constants.VCATEGORY_GENRE_ID:     return QUERY_SELECT_BY_GENRE, QUERY_SELECT_BY_GENRE_ASSETS            
            if vcategory_id == constants.VCATEGORY_DEVELOPER_ID: return QUERY_SELECT_BY_DEVELOPER, QUERY_SELECT_BY_DEVELOPER_ASSETS            
            if vcategory_id == constants.VCATEGORY_ESRB_ID:      return QUERY_SELECT_BY_ESRB, QUERY_SELECT_BY_ESRB_ASSETS            
            if vcategory_id == constants.VCATEGORY_YEARS_ID:     return QUERY_SELECT_BY_YEAR, QUERY_SELECT_BY_YEAR_ASSETS            
            if vcategory_id == constants.VCATEGORY_NPLAYERS_ID:  return QUERY_SELECT_BY_NPLAYERS, QUERY_SELECT_BY_NPLAYERS_ASSETS            
            if vcategory_id == constants.VCATEGORY_RATING_ID:    return QUERY_SELECT_BY_RATING, QUERY_SELECT_BY_RATING_ASSETS
        else:
            if vcollection_id == constants.VCOLLECTION_FAVOURITES_ID:   return QUERY_SELECT_MY_FAVOURITES, QUERY_SELECT_FAVOURITES_ROM_ASSETS
            if vcollection_id == constants.VCOLLECTION_RECENT_ID:       return QUERY_SELECT_RECENTLY_PLAYED_ROMS,QUERY_SELECT_RECENTLY_PLAYED_ROM_ASSETS
            if vcollection_id == constants.VCOLLECTION_MOST_PLAYED_ID:  return QUERY_SELECT_MOST_PLAYED_ROMS, QUERY_SELECT_MOST_PLAYED_ROM_ASSETS
            
        return None, None
    
#
# AelAddonRepository -> AKL Adoon objects from SQLite DB
#     
QUERY_SELECT_ADDON              = "SELECT * FROM akl_addon WHERE id = ?"
QUERY_SELECT_ADDON_BY_ADDON_ID  = "SELECT * FROM akl_addon WHERE addon_id = ? AND addon_type = ?"
QUERY_SELECT_ADDONS             = "SELECT * FROM akl_addon"
QUERY_SELECT_LAUNCHER_ADDONS    = "SELECT * FROM akl_addon WHERE addon_type = 'LAUNCHER' ORDER BY name"
QUERY_SELECT_SCANNER_ADDONS     = "SELECT * FROM akl_addon WHERE addon_type = 'SCANNER' ORDER BY name"
QUERY_SELECT_SCRAPER_ADDONS     = "SELECT * FROM akl_addon WHERE addon_type = 'SCRAPER' ORDER BY name"
QUERY_INSERT_ADDON              = "INSERT INTO akl_addon(id, name, addon_id, version, addon_type, extra_settings) VALUES(?,?,?,?,?,?)" 
QUERY_UPDATE_ADDON              = "UPDATE akl_addon SET name = ?, addon_id = ?, version = ?, addon_type = ?, extra_settings = ? WHERE id = ?" 

class AelAddonRepository(object):

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def find(self, id:str) -> AelAddon:
        self._uow.execute(QUERY_SELECT_ADDON, id)
        result_set = self._uow.single_result()
        return AelAddon(result_set)

    def find_by_addon_id(self, addon_id:str, type: constants.AddonType) -> AelAddon:
        self._uow.execute(QUERY_SELECT_ADDON_BY_ADDON_ID, addon_id, type.name)
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

    def find_all_scrapers(self) -> typing.Iterator[AelAddon]:        
        self._uow.execute(QUERY_SELECT_SCRAPER_ADDONS)
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
                    addon.get_extra_settings_str())
        
    def update_addon(self, addon: AelAddon):
        logger.info("AelAddonRepository.update_addon(): Updating addon '{}'".format(addon.get_addon_id()))        
        self._uow.execute(QUERY_UPDATE_ADDON,
                    addon.get_name(),
                    addon.get_addon_id(),
                    addon.get_version(),
                    addon.get_addon_type().name,
                    addon.get_extra_settings_str(),
                    addon.get_id())
