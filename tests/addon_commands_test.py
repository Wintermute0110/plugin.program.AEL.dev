import unittest, os
import unittest.mock

from mock import patch

import logging

from resources.lib.repositories import UnitOfWork
from resources.lib.settings import AEL_Paths
from resources.lib import globals
from resources.lib.utils import io
from resources.lib.domain import *

from resources.lib.commands import addon_commands as target

logger = logging.getLogger(__name__)

class Test_cmd_scan_addons(unittest.TestCase):
    
    ROOT_DIR = ''
    TEST_DIR = ''
    TEST_ASSETS_DIR = ''

    @classmethod
    def setUpClass(cls):        
        cls.TEST_DIR = os.path.dirname(os.path.abspath(__file__))
        cls.ROOT_DIR = os.path.abspath(os.path.join(cls.TEST_DIR, os.pardir))
        cls.TEST_ASSETS_DIR = os.path.abspath(os.path.join(cls.TEST_DIR,'assets/'))
        
        print('ROOT DIR: {}'.format(cls.ROOT_DIR))
        print('TEST DIR: {}'.format(cls.TEST_DIR))
        print('TEST ASSETS DIR: {}'.format(cls.TEST_ASSETS_DIR))
        print('---------------------------------------------------------------------------')
        
        dbPath = io.FileName(os.path.join(cls.TEST_ASSETS_DIR, 'test_db.db'))
        schemaPath = io.FileName(os.path.join(cls.ROOT_DIR, 'resources/schema.sql'))
        
        uow = UnitOfWork(dbPath)
        uow.reset_database(schemaPath)
                
        globals.g_PATHS = AEL_Paths('plugin.tests')
        globals.g_PATHS.DATABASE_FILE_PATH = dbPath
        
    @patch('resources.lib.utils.kodi.jsonrpc_query')
    def test_saving_new_addons(self, jsonrpc_response_mock):
        jsonrpc_response_mock.return_value = [
            { 'addonid': 'plugin.mock.A' },
            { 'addonid': 'plugin.mock.B' },
            { 'addonid': 'plugin.mock.c' }
        ]
        target.cmd_scan_addons({})