import sys
import unittest, os
from unittest.mock import patch, MagicMock, Mock

import logging

import tests.fake_routing
import tests.fakes

module = type(sys)('routing')
module.Plugin = tests.fake_routing.Plugin
sys.modules['routing'] = module

from resources.lib.domain import ROM
from resources.lib import globals

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s %(module)s %(levelname)s: %(message)s',
                datefmt = '%m/%d/%Y %I:%M:%S %p', level = logging.INFO)


class Test_objectstests(unittest.TestCase):
    
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
        
        globals.g_PATHS = globals.AEL_Paths('plugin.tests')
        
    def test_setting_youtube_url_as_trailer(self):
        
        # arrange
        target = ROM()
        subject = 'https://youtube.com/embed/98CkrjY9Hxo'
        expected = 'plugin://plugin.video.youtube/play/?video_id=98CkrjY9Hxo'
        
        # act
        target.set_trailer(subject)
        actual = target.get_trailer()

        # assert
        self.assertIsNotNone(actual)
        self.assertEqual(actual, expected)
