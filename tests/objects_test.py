import unittest, mock, os, sys
from mock import *
from fakes import *

from resources.main import *
from resources.objects import *
from resources.constants import *
from resources.utils import *

class Test_objectstests(unittest.TestCase):
    
    ROOT_DIR = ''
    TEST_DIR = ''
    TEST_ASSETS_DIR = ''

    @classmethod
    def setUpClass(cls):
        set_log_level(LOG_DEBUG)
        
        cls.TEST_DIR = os.path.dirname(os.path.abspath(__file__))
        cls.ROOT_DIR = os.path.abspath(os.path.join(cls.TEST_DIR, os.pardir))
        cls.TEST_ASSETS_DIR = os.path.abspath(os.path.join(cls.TEST_DIR,'assets/'))
                
        print('ROOT DIR: {}'.format(cls.ROOT_DIR))
        print('TEST DIR: {}'.format(cls.TEST_DIR))
        print('TEST ASSETS DIR: {}'.format(cls.TEST_ASSETS_DIR))
        print('---------------------------------------------------------------------------')

    def read_file(self, path):
        with open(path, 'r') as f:
            return f.read()

    def test_setting_youtube_url_as_trailer(self):
        
        # arrange
        target = ROM()
        subject = 'https://youtube.com/embed/98CkrjY9Hxo'
        expected = 'plugin://plugin.video.youtube/?action=play_video&videoid=98CkrjY9Hxo'
        
        # act
        target.set_trailer(subject)
        actual = target.get_trailer()

        # assert
        self.assertIsNotNone(actual)
        self.assertEqual(actual, expected)
