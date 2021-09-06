# -*- coding: utf-8 -*-
import logging
import typing

import sqlite3
from sqlite3.dbapi2 import Cursor

from ael.settings import *
from ael.utils import text, io
from ael import constants

from resources.lib import globals
from resources.lib.domain import Category, ROMCollection, ROM, ROMLauncherAddon, Asset, AssetPath, AelAddon, ROMCollectionScanner, g_assetFactory

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

    def __init__(self, paths: globals.AEL_Paths):
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

    def find_items(self, collection_id) -> typing.Any:
        repository_file = self.paths.COLLECTIONS_DIR.pjoin('collection_{}.json'.format(collection_id))
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
                    asset_info = g_assetFactory.get_asset_info_by_key(xml_tag)
                    asset_data = { 'filepath': text_XML_line, 'asset_type': asset_info.id }
                    assets.append(Asset(asset_data))
                    
            # --- Add launcher to launchers collection ---
            logger.debug('Adding launcher "{0}" to import list'.format(launcher_temp['m_name']))
            yield ROMCollection(launcher_temp, assets)


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
                r = ROM(rom_data, assets)
                key = r.get_id()
                roms.append(r)
        else:
            for key in roms_data:
                assets = self._get_assets_from_romdata(roms_data[key])
                compatible_rom_data = self._alter_dictionary_for_compatibility(roms_data[key])
                r = ROM(compatible_rom_data, assets)
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

    def _alter_dictionary_for_compatibility(self, rom_data: dict) -> dict:
        rom_data['rom_status'] = rom_data['fav_status'] if 'fav_status' in rom_data else None
        return rom_data
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
QUERY_UPDATE_ASSET_PATH     = "UPDATE assetspaths SET path = ?, asset_type = ? WHERE id = ?"

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
        assets_path = category_obj.get_assets_path_FN()
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
# ROMCollectionRepository -> ROM Sets from SQLite DB
#
QUERY_SELECT_ROMCOLLECTION             = "SELECT * FROM vw_romcollections WHERE id = ?"
QUERY_SELECT_ROMCOLLECTIONS            = "SELECT * FROM vw_romcollections ORDER BY m_name"
QUERY_SELECT_ROOT_ROMCOLLECTIONS       = "SELECT * FROM vw_romcollections WHERE parent_id IS NULL ORDER BY m_name"
QUERY_SELECT_ROMCOLLECTIONS_BY_PARENT  = "SELECT * FROM vw_romcollections WHERE parent_id = ? ORDER BY m_name"
QUERY_SELECT_ROMCOLLECTIONS_BY_ROM     = "SELECT rs.* FROM vw_romcollections AS rs INNER JOIN roms_in_romcollection AS rr ON rr.romcollection_id = rs.id WHERE rr.rom_id = ?"

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
QUERY_INSERT_ROMCOLLECTION_ASSET               = "INSERT INTO romcollection_assets (romcollection_id, asset_id) VALUES (?, ?)"
QUERY_INSERT_ROMCOLLECTION_ASSET_PATH          = "INSERT INTO romcollection_assetspaths (romcollection_id, assetspaths_id) VALUES (?, ?)"

QUERY_INSERT_ROM_IN_ROMCOLLECTION        = "INSERT INTO roms_in_romcollection (rom_id, romcollection_id) VALUES (?,?)"
QUERY_REMOVE_ROM_FROM_ROMCOLLECTION      = "DELETE FROM roms_in_romcollection WHERE rom_id = ? AND romcollection_id = ?"
QUERY_REMOVE_ROMS_FROM_ROMCOLLECTION    =  "DELETE FROM roms_in_romcollection WHERE romcollection_id = ?"

QUERY_SELECT_ROMCOLLECTION_LAUNCHERS     = "SELECT * FROM vw_romcollection_launchers WHERE romcollection_id = ?"
QUERY_INSERT_ROMCOLLECTION_LAUNCHER      = "INSERT INTO romcollection_launchers (id, romcollection_id, ael_addon_id, settings, is_default) VALUES (?,?,?,?,?)"
QUERY_UPDATE_ROMCOLLECTION_LAUNCHER      = "UPDATE romcollection_launchers SET settings = ?, is_default = ? WHERE id = ?"
QUERY_DELETE_ROMCOLLECTION_LAUNCHERS     = "DELETE FROM romcollection_launchers WHERE romcollection_id = ?"
QUERY_DELETE_ROMCOLLECTION_LAUNCHER      = "DELETE FROM romcollection_launchers WHERE romcollection_id = ? AND id = ?"

QUERY_SELECT_ROMCOLLECTION_SCANNERS      = "SELECT * FROM vw_romcollection_scanners WHERE romcollection_id = ?"
QUERY_INSERT_ROMCOLLECTION_SCANNER       = "INSERT INTO romcollection_scanners (id, romcollection_id, ael_addon_id, settings) VALUES (?,?,?,?)"
QUERY_UPDATE_ROMCOLLECTION_SCANNER       = "UPDATE romcollection_scanners SET settings = ? WHERE id = ?"
QUERY_DELETE_ROMCOLLECTION_SCANNER       = "DELETE FROM romcollection_scanners WHERE romcollection_id = ? AND id = ?"

QUERY_SELECT_ROMCOLLECTION_LAUNCHERS_BY_ROM = "SELECT rl.* FROM vw_romcollection_launchers AS rl INNER JOIN roms_in_romcollection AS rr ON rr.romcollection_id = rl.romcollection_id WHERE rr.rom_id = ?"
QUERY_SELECT_ROMCOLLECTION_SCANNERS_BY_ROM  = "SELECT rs.* FROM vw_romcollection_scanners AS rs INNER JOIN roms_in_romcollection AS rr ON rr.romcollection_id = rs.romcollection_id WHERE rr.rom_id = ?"

class ROMCollectionRepository(object):

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def find_romcollection(self, romcollection_id: str) -> ROMCollection:
        self._uow.execute(QUERY_SELECT_ROMCOLLECTION, romcollection_id)
        romcollection_data = self._uow.single_result()
        
        self._uow.execute(QUERY_SELECT_ROMCOLLECTION_ASSETS_BY_SET, romcollection_id)
        assets_result_set = self._uow.result_set()
        assets = []
        for asset_data in assets_result_set:
            assets.append(Asset(asset_data))    
        
        self._uow.execute(QUERY_SELECT_ROMCOLLECTION_LAUNCHERS, romcollection_id)
        launchers_data = self._uow.result_set()
        launchers = []
        for launcher_data in launchers_data:
            addon = AelAddon(launcher_data.copy())
            launchers.append(ROMLauncherAddon(addon, launcher_data))
        
        self._uow.execute(QUERY_SELECT_ROMCOLLECTION_SCANNERS, romcollection_id)
        scanners_data = self._uow.result_set()
        scanners = []
        for scanner_data in scanners_data:
            addon = AelAddon(scanner_data.copy())
            scanners.append(ROMCollectionScanner(addon, scanner_data))
            
        return ROMCollection(romcollection_data, assets, launchers, scanners)
    
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

    def find_romcollections_by_parent(self, category_id) -> typing.Iterator[ROMCollection]:
        self._uow.execute(QUERY_SELECT_ROMCOLLECTIONS_BY_PARENT, category_id)
        result_set = self._uow.result_set()
        
        self._uow.execute(QUERY_SELECT_ROMCOLLECTIONS_ASSETS_BY_PARENT, category_id)
        assets_result_set = self._uow.result_set()
                
        for romcollection_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['romcollection_id'] == romcollection_data['id'], assets_result_set):
                assets.append(Asset(asset_data))   
                
            yield ROMCollection(romcollection_data, assets)

    def find_romcollections_by_rom(self, rom_id:str) -> typing.Iterator[ROMCollection]:
        self._uow.execute(QUERY_SELECT_ROMCOLLECTIONS_BY_ROM, rom_id)
        result_set = self._uow.result_set()
        
        self._uow.execute(QUERY_SELECT_ROMCOLLECTION_ASSETS_BY_ROM, rom_id)
        assets_result_set = self._uow.result_set()

        self._uow.execute(QUERY_SELECT_ROMCOLLECTION_LAUNCHERS_BY_ROM, rom_id)
        launchers_data = self._uow.result_set()
        
        self._uow.execute(QUERY_SELECT_ROMCOLLECTION_SCANNERS_BY_ROM, rom_id)
        scanners_data = self._uow.result_set()
        
        for romcollection_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['romcollection_id'] == romcollection_data['id'], assets_result_set):
                assets.append(Asset(asset_data))      
            
            launchers = []
            for launcher_data in launchers_data:
                addon = AelAddon(launcher_data.copy())
                launchers.append(ROMLauncherAddon(addon, launcher_data))
            
            scanners = []
            for scanner_data in scanners_data:
                addon = AelAddon(scanner_data.copy())
                scanners.append(ROMCollectionScanner(addon, scanner_data))
                    
            yield ROMCollection(romcollection_data, assets, launchers, scanners)                       
                        
    def insert_romcollection(self, romcollection_obj: ROMCollection, parent_obj: Category = None):
        logger.info("ROMCollectionRepository.insert_romcollection(): Inserting new romcollection '{}'".format(romcollection_obj.get_name()))
        metadata_id = text.misc_generate_random_SID()
        assets_path = romcollection_obj.get_assets_path_FN()
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
        assets_path = romcollection_obj.get_assets_path_FN()
        
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
            
#
# ROMsRepository -> ROMs from SQLite DB
#     
QUERY_SELECT_ROM                = "SELECT * FROM vw_roms WHERE id = ?"
QUERY_SELECT_ROMS_BY_SET        = "SELECT r.* FROM vw_roms AS r INNER JOIN roms_in_romcollection AS rs ON rs.rom_id = r.id AND rs.romcollection_id = ?"
QUERY_SELECT_ROM_ASSETS         = "SELECT * FROM vw_rom_assets WHERE rom_id = ?"
QUERY_SELECT_ROM_ASSETS_BY_SET  = "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN roms_in_romcollection AS rs ON rs.rom_id = ra.rom_id AND rs.romcollection_id = ?"
QUERY_INSERT_ROM                = """
                                INSERT INTO roms (
                                    id, metadata_id, name, num_of_players, esrb_rating, platform, box_size,
                                    nointro_status, cloneof, rom_status, file_path, scanned_by_id)
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
                                
QUERY_INSERT_ROM_ASSET          = "INSERT INTO rom_assets (rom_id, asset_id) VALUES (?, ?)"
QUERY_UPDATE_ROM                = """
                                  UPDATE roms 
                                  SET name=?, num_of_players=?, esrb_rating=?, platform = ?, box_size = ?,
                                  nointro_status=?, cloneof=?, rom_status=?, file_path=?, launch_count=?, last_launch_timestamp=?,
                                  is_favourite=? WHERE id =?
                                  """
QUERY_DELETE_ROM                = "DELETE FROM roms WHERE id = ?"
QUERY_DELETE_ROMS_BY_COLLECTION = "DELETE FROM roms WHERE id IN (SELECT rc.rom_id FROM roms_in_romcollection AS rc WHERE rc.romcollection_id = ?)"

QUERY_SELECT_ROM_LAUNCHERS     = "SELECT * FROM vw_rom_launchers WHERE rom_id = ?"
QUERY_INSERT_ROM_LAUNCHER      = "INSERT INTO rom_launchers (id, rom_id, ael_addon_id, settings, is_default) VALUES (?,?,?,?,?)"
QUERY_UPDATE_ROM_LAUNCHER      = "UPDATE rom_launchers SET settings = ?, is_default = ? WHERE id = ?"
QUERY_DELETE_ROM_LAUNCHERS     = "DELETE FROM rom_launchers WHERE rom_id = ?"
QUERY_DELETE_ROM_LAUNCHER      = "DELETE FROM rom_launchers WHERE romcollection_id = ? AND id = ?"
          
class ROMsRepository(object):
       
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def find_roms_by_romcollection(self, romcollection_id: str) -> typing.Iterator[ROM]:
        self._uow.execute(QUERY_SELECT_ROMS_BY_SET, romcollection_id)
        result_set = self._uow.result_set()
        
        self._uow.execute(QUERY_SELECT_ROM_ASSETS_BY_SET, romcollection_id)
        assets_result_set = self._uow.result_set()
                
        for rom_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['rom_id'] == rom_data['id'], assets_result_set):
                assets.append(Asset(asset_data))                
            yield ROM(rom_data, assets)

    def find_roms_by_virtual_collection(self, vcollection_id:str) -> typing.Iterator[ROM]:        
        roms_query = None
        rom_assets_query = None
        
        if vcollection_id == constants.VCOLLECTION_FAVOURITES_ID:
            roms_query = QUERY_SELECT_MY_FAVOURITES
            rom_assets_query = QUERY_SELECT_FAVOURITES_ROM_ASSETS
        if vcollection_id == constants.VCOLLECTION_RECENT_ID: 
            roms_query = QUERY_SELECT_RECENTLY_PLAYED_ROMS
            rom_assets_query = QUERY_SELECT_RECENTLY_PLAYED_ROM_ASSETS
        if vcollection_id == constants.VCOLLECTION_MOST_PLAYED_ID:
            roms_query = QUERY_SELECT_MOST_PLAYED_ROMS
            rom_assets_query = QUERY_SELECT_MOST_PLAYED_ROM_ASSETS
        
        if roms_query is None: return []
        
        self._uow.execute(roms_query)
        result_set = self._uow.result_set()
        if not result_set:
            return []
        
        self._uow.execute(rom_assets_query) 
        assets_result_set = self._uow.result_set()
                
        for rom_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['rom_id'] == rom_data['id'], assets_result_set):
                assets.append(Asset(asset_data))                
            yield ROM(rom_data, assets)

    def find_rom(self, rom_id:str) -> ROM:
        self._uow.execute(QUERY_SELECT_ROM, rom_id)
        rom_data = self._uow.single_result()

        self._uow.execute(QUERY_SELECT_ROM_ASSETS, rom_id)
        assets_result_set = self._uow.result_set()            
        assets = []
        for asset_data in assets_result_set:
            assets.append(Asset(asset_data))
                    
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
            rom_obj.get_rom_status(),
            rom_obj.get_file().getPath(),
            rom_obj.get_scanned_with())
        
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
            rom_obj.get_rom_status(),
            rom_obj.get_file().getPath(),
            rom_obj.get_launch_count(),
            rom_obj.get_last_launch_date(),
            rom_obj.is_favourite(),
            rom_obj.get_id())
        
        for asset in rom_obj.get_assets():
            if asset.get_id() == '': self._insert_asset(asset, rom_obj)
            else: self._update_asset(asset, rom_obj)            
        
        rom_launchers = rom_obj.get_launchers()
        for rom_launcher in rom_launchers:
            if rom_launcher.get_id() is None:
                rom_launcher.set_id(text.misc_generate_random_SID())
                self._uow.execute(QUERY_INSERT_ROMCOLLECTION_LAUNCHER,
                    rom_launcher.get_id(),
                    rom_obj.get_id(), 
                    rom_launcher.addon.get_id(), 
                    rom_launcher.get_settings_str(), 
                    rom_launcher.is_default())
            else:
                self._uow.execute(QUERY_UPDATE_ROMCOLLECTION_LAUNCHER,
                    rom_launcher.get_settings_str(), 
                    rom_launcher.is_default(),
                    rom_launcher.get_id())
                
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

#
# AelAddonRepository -> AEL Adoon objects from SQLite DB
#     
QUERY_SELECT_ADDON              = "SELECT * FROM ael_addon WHERE id = ?"
QUERY_SELECT_ADDON_BY_ADDON_ID  = "SELECT * FROM ael_addon WHERE addon_id = ? AND addon_type = ?"
QUERY_SELECT_ADDONS             = "SELECT * FROM ael_addon"
QUERY_SELECT_LAUNCHER_ADDONS    = "SELECT * FROM ael_addon WHERE addon_type = 'LAUNCHER' ORDER BY name"
QUERY_SELECT_SCANNER_ADDONS     = "SELECT * FROM ael_addon WHERE addon_type = 'SCANNER' ORDER BY name"
QUERY_SELECT_SCRAPER_ADDONS     = "SELECT * FROM ael_addon WHERE addon_type = 'SCRAPER' ORDER BY name"
QUERY_INSERT_ADDON              = "INSERT INTO ael_addon(id, name, addon_id, version, addon_type, extra_settings) VALUES(?,?,?,?,?,?)" 
QUERY_UPDATE_ADDON              = "UPDATE ael_addon SET name = ?, addon_id = ?, version = ?, addon_type = ?, extra_settings = ? WHERE id = ?" 

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
