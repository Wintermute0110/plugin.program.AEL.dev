import sys
import unittest, os
import unittest.mock
from unittest.mock import MagicMock, patch

import logging
from distutils.version import LooseVersion

import tests.fake_routing
from tests.fakes import FakeFile, FakeUnitOfWork

module = type(sys)('routing')
module.Plugin = tests.fake_routing.Plugin
sys.modules['routing'] = module

from resources.lib import globals
from resources.lib.services import AppService

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s %(module)s %(levelname)s: %(message)s',
                    datefmt = '%m/%d/%Y %I:%M:%S %p', level = logging.DEBUG)

class Test_services(unittest.TestCase):
    
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
        
        globals.g_PATHS = globals.AKL_Paths('plugin.tests')
        globals.g_PATHS.DATABASE_MIGRATIONS_PATH = FakeFile('db')
        
    @patch('resources.lib.services.globals.g_bootstrap_instances', autospec=True)
    @patch('akl.utils.io.FileName.scanFilesInPath')
    def test_version_compare(self, file_mock:MagicMock, globals_mock):  
        # arrange
        file_mock.return_value = [
            FakeFile('1.2.1.sql'),
            FakeFile('1.1.0.sql'), 
            FakeFile('/files/1.3.0.sql'),
            FakeFile('1.1.5.sql'),
            FakeFile('/migrations/with/1.2.7.sql')]
        uow_mock = FakeUnitOfWork()
        
        service = AppService()
        start_version = LooseVersion('1.1.1')
        
        # act
        service._do_version_upgrade(uow_mock, start_version)
        
        # assert
        self.assertIsNotNone(uow_mock.executed_files)
        self.assertEqual(uow_mock.executed_files[0], '1.1.5.sql')
        self.assertEqual(uow_mock.executed_files[1], '1.2.1.sql')
        self.assertEqual(uow_mock.executed_files[2], '/migrations/with/1.2.7.sql')
        self.assertEqual(uow_mock.executed_files[3], '/files/1.3.0.sql')
