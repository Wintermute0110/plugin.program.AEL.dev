# -*- coding: utf-8 -*-
import logging
import typing

import sqlite3
from sqlite3.dbapi2 import Cursor

from routing import Plugin

from resources.lib.settings import *
from resources.lib.constants import *
from resources.lib.domain import *
from resources.lib.utils import text
from resources.lib import globals

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

    def __init__(self, paths: AEL_Paths, router: Plugin):
        self.paths = paths
        self.router = router

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

            category_temp = {}
            for root_child in root_element:
                # >> By default read strings
                text_XML_line = root_child.text if root_child.text is not None else ''
                text_XML_line = text.unescape_XML(text_XML_line)
                xml_tag  = root_child.tag
                if self.debug: logger.debug('>>> "{0:<11s}" --> "{1}"'.format(xml_tag, text_XML_line))
                category_temp[xml_tag] = text_XML_line
            # --- Add category to categories dictionary ---
            logger.debug('Adding category "{0}" to import list'.format(category_temp['m_name']))
            yield Category(category_temp)

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

            launcher_temp = {}
            for root_child in root_element:
                # >> By default read strings
                text_XML_line = root_child.text if root_child.text is not None else ''
                text_XML_line = text.unescape_XML(text_XML_line)
                xml_tag  = root_child.tag
                if self.debug: logger.debug('>>> "{0:<11s}" --> "{1}"'.format(xml_tag, text_XML_line))
                if xml_tag == 'categoryID': xml_tag = 'parent_id'                
                launcher_temp[xml_tag] = text_XML_line
            # --- Add launcher to launchers dictionary ---
            logger.debug('Adding launcher "{0}" to import list'.format(launcher_temp['m_name']))
            yield ROMSet(launcher_temp)

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
        self.conn.execute(QUERY_INSERT_ADDON, 
                          [text.misc_generate_random_SID(), '{}.AppLauncher'.format(globals.addon_id), 
                           globals.addon_version, True, globals.router.url_for_path('launcher/app')])

        self.commit()
        self.close_session()
        
    def reset_database(self, schema_file_path: io.FileName):
        if self._db_path.exists():
            self._db_path.unlink()
        
        # cleanup collection json files
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

    def single_result(self):
        return self.cursor.fetchone()

    def result_set(self):
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
QUERY_SELECT_CATEGORY             = "SELECT * FROM vw_categories WHERE id = ?"
QUERY_SELECT_CATEGORIES           = "SELECT * FROM vw_categories"
QUERY_SELECT_ROOT_CATEGORIES      = "SELECT * FROM vw_categories WHERE parent_id IS NULL"
QUERY_SELECT_CATEGORIES_BY_PARENT = "SELECT * FROM vw_categories WHERE parent_id = ?"
QUERY_INSERT_CATEGORY             = """
                                    INSERT INTO categories (id,name,parent_id,metadata_id,default_icon,default_fanart,default_banner,default_poster,default_clearlogo) 
                                    VALUES (?,?,?,?,?,?,?,?,?)
                                    """
QUERY_UPDATE_CATEGORY             = "UPDATE categories SET name=? WHERE id =?"
QUERY_INSERT_CATEGORY_ASSET       = "INSERT INTO category_assets (category_id, asset_id) VALUES (?, ?)"

class CategoryRepository(object):

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def find_category(self, category_id: str) -> Category:
        self._uow.execute(QUERY_SELECT_CATEGORY, category_id)
        category_data = self._uow.single_result()
        return Category(category_data)

    def find_root_categories(self) -> typing.Iterator[Category]:
        self._uow.execute(QUERY_SELECT_ROOT_CATEGORIES)
        result_set = self._uow.result_set()
        for category_data in result_set:
            yield Category(category_data)

    def find_categories_by_parent(self, category_id) -> typing.Iterator[Category]:
        self._uow.execute(QUERY_SELECT_CATEGORIES_BY_PARENT, category_id)
        result_set = self._uow.result_set()
        for category_data in result_set:
            yield Category(category_data)

    def find_all_categories(self) -> typing.Iterator[Category]:
        self._uow.execute(QUERY_SELECT_CATEGORIES)
        result_set = self._uow.result_set()
        for category_data in result_set:
            yield Category(category_data)

    def save_category(self, category_obj: Category, parent_obj: Category = None):
        logger.info("CategoryRepository.save_category(): Inserting new category '{}'".format(category_obj.get_name()))
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
            category_obj.get_mapped_asset_info(asset_id=ASSET_ICON_ID).key,
            category_obj.get_mapped_asset_info(asset_id=ASSET_FANART_ID).key,
            category_obj.get_mapped_asset_info(asset_id=ASSET_BANNER_ID).key,
            category_obj.get_mapped_asset_info(asset_id=ASSET_POSTER_ID).key,
            category_obj.get_mapped_asset_info(asset_id=ASSET_CLEARLOGO_ID).key)

        category_assets = category_obj.get_assets_odict()
        for asset in category_assets:
            asset_db_id = text.misc_generate_random_SID()
            self._uow.execute(QUERY_INSERT_ASSET,
                asset_db_id, category_assets[asset], asset.id)
            self._uow.execute(QUERY_INSERT_CATEGORY_ASSET,
                category_obj.get_id(), asset_db_id)
            
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
            category_obj.get_id())

#
# ROMSetRepository -> ROM Sets from SQLite DB
#
QUERY_SELECT_ROMSETS              = "SELECT * FROM vw_romsets"
QUERY_SELECT_ROOT_ROMSETS         = "SELECT * FROM vw_romsets WHERE parent_id IS NULL"
QUERY_SELECT_ROMSETS_BY_PARENT    = "SELECT * FROM vw_romsets WHERE parent_id = ?"
QUERY_INSERT_ROMSET               = """
                                    INSERT INTO romsets (
                                            id,name,parent_id,metadata_id,platform, 
                                            default_icon,default_fanart,default_banner,default_poster,default_controller,default_clearlogo
                                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                                    """
QUERY_UPDATE_ROMSET               = "UPDATE romsets SET name=?,platform=? WHERE id =?"
QUERY_INSERT_ROMSET_ASSET         = "INSERT INTO romset_assets (romset_id, asset_id) VALUES (?, ?)"
QUERY_INSERT_ROMSET_ASSET_PATH    = "INSERT INTO romset_assetspaths (romset_id, assetspaths_id) VALUES (?, ?)"
QUERY_INSERT_ROMSET_LAUNCHER      = "INSERT INTO romset_launchers (romset_id, ael_addon_id, args, is_default) VALUES (?,?,?,?)"
QUERY_DELETE_ROMSET_LAUNCHERS     = "DELETE FROM romset_launchers WHERE romset_id = ?"

class ROMSetRepository(object):

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def find_all_romsets(self) -> typing.Iterator[ROMSet]:
        self._uow.execute(QUERY_SELECT_ROMSETS)
        result_set = self._uow.result_set()
        for romset_data in result_set:
            yield ROMSet(romset_data)

    def find_root_romsets(self) -> typing.Iterator[ROMSet]:
        self._uow.execute(QUERY_SELECT_ROOT_ROMSETS)
        result_set = self._uow.result_set()
        for romset_data in result_set:
            yield ROMSet(romset_data)

    def find_romsets_by_parent(self, category_id) -> typing.Iterator[ROMSet]:
        self._uow.execute(QUERY_SELECT_ROMSETS_BY_PARENT, category_id)
        result_set = self._uow.result_set()
        for romset_data in result_set:
            yield ROMSet(romset_data)
            
    def save_romset(self, romset_obj: ROMSet, parent_obj: Category = None):
        logger.info("ROMSetRepository.save_romset(): Inserting new romset '{}'".format(romset_obj.get_name()))
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
            romset_obj.get_mapped_asset_info(asset_id=ASSET_ICON_ID).key,
            romset_obj.get_mapped_asset_info(asset_id=ASSET_FANART_ID).key,
            romset_obj.get_mapped_asset_info(asset_id=ASSET_BANNER_ID).key,
            romset_obj.get_mapped_asset_info(asset_id=ASSET_POSTER_ID).key,
            romset_obj.get_mapped_asset_info(asset_id=ASSET_CONTROLLER_ID).key,
            romset_obj.get_mapped_asset_info(asset_id=ASSET_CLEARLOGO_ID).key)

        romset_assets = romset_obj.get_assets_odict()
        for asset in romset_assets:
            asset_db_id = text.misc_generate_random_SID()
            self._uow.execute(QUERY_INSERT_ASSET,
                asset_db_id, romset_assets[asset], asset.id)
            self._uow.execute(QUERY_INSERT_ROMSET_ASSET,
                romset_obj.get_id(), asset_db_id)     
            
        romset_launchers = romset_obj.get_launchers_data()
        for romset_launcher in romset_launchers:
            self._uow.execute(QUERY_INSERT_ROMSET_LAUNCHER,
                romset_obj.get_id(), romset_launcher.addon.get_id(), romset_launcher.get_arguments(), romset_launcher.is_default)
              
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
            romset_obj.get_id())
         
        self._uow.execute(QUERY_DELETE_ROMSET_LAUNCHERS, romset_obj.get_id())
        romset_launchers = romset_obj.get_launchers_data()
        for romset_launcher in romset_launchers:
            self._uow.execute(QUERY_INSERT_ROMSET_LAUNCHER,
                romset_obj.get_id(), romset_launcher.addon.get_id(), romset_launcher.get_arguments(), romset_launcher.is_default)
                   
#
# AelAddonRepository -> AEL Adoon objects from SQLite DB
#     
QUERY_SELECT_ADDONS = "SELECT * FROM ael_addon"
QUERY_INSERT_ADDON  = "INSERT INTO ael_addon(id, addon_id, version, is_launcher, launcher_uri) VALUES(?,?,?,?,?)" 
QUERY_UPDATE_ADDON  = "UPDATE ael_addon SET addon_id = ?, version = ?, is_launcher = ?, launcher_uri = ? WHERE id = ?" 
class AelAddonRepository(object):

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def find_all(self) -> typing.Iterator[AelAddon]:
        self._uow.execute(QUERY_SELECT_ADDONS)
        result_set = self._uow.result_set()
        for addon_data in result_set:
            yield AelAddon(addon_data)

    def save_addon(self, addon: AelAddon):
        logger.info("AelAddonRepository.save_addon(): Saving addon '{}'".format(addon.get_addon_id()))        
        self._uow.execute(QUERY_INSERT_ADDON,
                    addon.get_id(),
                    addon.get_addon_id(),
                    addon.get_version(),
                    addon.supports_launching(),
                    addon.get_custom_attribute('launcher_uri'))
        
    def update_addon(self, addon: AelAddon):
        logger.info("AelAddonRepository.update_addon(): Updating addon '{}'".format(addon.get_addon_id()))        
        self._uow.execute(QUERY_INSERT_ADDON,
                    addon.get_addon_id(),
                    addon.get_version(),
                    addon.supports_launching(),
                    addon.get_custom_attribute('launcher_uri'),
                    addon.get_id())
