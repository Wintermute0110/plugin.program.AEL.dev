import unittest, os
import unittest.mock

from mock import patch

import logging

import tests.fakes

from resources.lib.repositories import UnitOfWork
from resources.lib.settings import AEL_Paths
from resources.lib import globals
from resources.lib.utils import io
from resources.lib.domain import *

from resources.lib.commands import addon_commands as target

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s %(module)s %(levelname)s: %(message)s',
                datefmt = '%m/%d/%Y %I:%M:%S %p', level = logging.INFO)

class Test_cmd_scan_addons(unittest.TestCase):
    
    ROOT_DIR = ''
    TEST_DIR = ''
    TEST_ASSETS_DIR = ''

    @classmethod
    def setUpClass(cls):        
        cls.TEST_DIR = os.path.dirname(os.path.abspath(__file__))
        cls.ROOT_DIR = os.path.abspath(os.path.join(cls.TEST_DIR, os.pardir))
        cls.TEST_ASSETS_DIR = os.path.abspath(os.path.join(cls.TEST_DIR,'assets/'))
        
        logger.info('ROOT DIR: {}'.format(cls.ROOT_DIR))
        logger.info('TEST DIR: {}'.format(cls.TEST_DIR))
        logger.info('TEST ASSETS DIR: {}'.format(cls.TEST_ASSETS_DIR))
        logger.info('---------------------------------------------------------------------------')
        
        dbPath = io.FileName(os.path.join(cls.TEST_ASSETS_DIR, 'test_db.db'))
        schemaPath = io.FileName(os.path.join(cls.ROOT_DIR, 'resources/schema.sql'))
        
        uow = UnitOfWork(dbPath)
        uow.reset_database(schemaPath)
                
        globals.g_PATHS = AEL_Paths('plugin.tests')
        globals.g_PATHS.DATABASE_FILE_PATH = dbPath
        
    mocked_addons_collection = {}  
    def mocked_addons(addon_id):
        return Test_cmd_scan_addons.mocked_addons_collection[addon_id]
    
    saved_entities = []
    def repository_save(entity):
        Test_cmd_scan_addons.saved_entities.append(entity)
        
    updated_entities = []
    def repository_update(entity):
        Test_cmd_scan_addons.updated_entities.append(entity)
        
    @patch('xbmcaddon.Addon', side_effect = mocked_addons)
    @patch('resources.lib.repositories.AelAddonRepository.save_addon', side_effect = repository_save)
    @patch('resources.lib.repositories.AelAddonRepository.update_addon', side_effect = repository_update)
    @patch('resources.lib.utils.kodi.jsonrpc_query')
    def test_saving_new_addons(self, jsonrpc_response_mock, repo_update_mock, repo_save_mock, addon_mock):
        # arrange
        Test_cmd_scan_addons.mocked_addons_collection = {
            'plugin.mock.A': tests.fakes.FakeAddon({ 'version': '1.2.3', 'ael.enabled': 'true', 'ael.launcher_uri': '' }),
            'plugin.mock.B': tests.fakes.FakeAddon({ 'version': '3.3.1', 'ael.enabled': 'false' }),
            'plugin.mock.C': tests.fakes.FakeAddon({ 'version': '6.8.0', 'ael.enabled': 'true', 'ael.launcher_uri': 'plugin://test.uri' })
        }
        jsonrpc_response_mock.return_value = {
            'result': { 'addons': [ { 'addonid': 'plugin.mock.A' }, { 'addonid': 'plugin.mock.B' }, { 'addonid': 'plugin.mock.C' } ]}
        }
        
        # act
        target.cmd_scan_addons({})
        # assert
        self.assertEqual(len(Test_cmd_scan_addons.saved_entities), 2)