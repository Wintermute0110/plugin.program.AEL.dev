import sys
import unittest, os
from unittest.mock import patch, MagicMock, Mock

import logging

import tests.fake_routing
import tests.fakes

import pprint

module = type(sys)('routing')
module.Plugin = tests.fake_routing.Plugin
sys.modules['routing'] = module

from resources.lib.repositories import UnitOfWork
from resources.lib.domain import *
from resources.lib import globals

from resources.lib.commands import view_rendering_commands as target


from resources.lib.domain import Category, ROMCollection

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s %(module)s %(levelname)s: %(message)s',
                datefmt = '%m/%d/%Y %I:%M:%S %p', level = logging.INFO)

class Test_View_Rendering_Commands(unittest.TestCase):
    
    ROOT_DIR = ''
    TEST_DIR = ''
    TEST_ASSETS_DIR = ''
    CREATED_VIEWS = []

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
        globals.g_PATHS = globals.AEL_Paths('plugin.tests')
        globals.g_PATHS.DATABASE_FILE_PATH = dbPath
        
    def write_json(view_data):
         json_data = json.dumps(view_data)
         pprint.pprint(json_data)
         Test_View_Rendering_Commands.CREATED_VIEWS.append(json_data)
         
    def store_root_view(obj, view_data):
        Test_View_Rendering_Commands.write_json(view_data)
        
    def store_view(obj, id, type, view_data):
        Test_View_Rendering_Commands.write_json(view_data)
        
    @patch('resources.lib.repositories.ViewRepository.store_root_view', autospec=True, side_effect = store_root_view)
    @patch('resources.lib.repositories.ViewRepository.store_view', autospec=True, side_effect = store_view)
    @patch('ael.utils.kodi.notify', autospec=True)
    @patch('ael.utils.kodi.refresh_container', autospec=True)
    def test_rendering_views_based_on_database_data(self, refresh_mock, notify_mock, store_mock, store_root_mock):
                
        # arrange
        Test_View_Rendering_Commands.CREATED_VIEWS = []
        
        # act
        target.cmd_render_views_data(None)
        
        # assert
        self.assertIsNotNone(Test_View_Rendering_Commands.CREATED_VIEWS)
        