import unittest
import mock
from mock import *
from tests.fakes import *

import os

from resources.utils import *
from resources.constants import *
        
class Test_filename_test(unittest.TestCase):
     
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

    @patch('resources.utils.xbmcvfs.File')
    def test_reading_line_for_line(self, file_mock):

        # arrange
        p = self.TEST_ASSETS_DIR + "\\test-nfo.xml"
        file_mock.return_value = open(p, 'r')
        target = KodiFileName(p)       

        expected = "<game>"

        # act
        f = target.open('r')
        l = target.readline()
        actual = target.readline()
        
        target.close()

        # assert
        self.assertEquals(expected, actual)

        
    @patch('resources.utils.xbmcvfs.File')
    def test_reading_line_for_line_after_file_is_done(self, file_mock):

        # arrange
        p = self.TEST_ASSETS_DIR + "\\test-nfo.xml"
        file_mock.return_value = open(p, 'r')
        target = KodiFileName(p)       

        # file contains 9 lines, so 10th should be passed the end of the file.

        # act
        f = target.open('r')
        for x in range(0, 10):
            line = target.readline()
            print('{}: {}'.format(x, line))

        actual = target.readline()
        
        target.close()

        # assert
        self.assertEquals('', actual)

    def test_reading_property_file_successfull(self):
        # arrange
        p = self.TEST_ASSETS_DIR + "\\retroarch.cfg"
        target = NewFileName(p)       

        # act
        propfile = target.readPropertyFile()
        for key, value in propfile.items():
            print('{}={}'.format(key, value))

        actual = propfile['content_database_path']

        # assert
        self.assertIsNotNone(actual)
        self.assertEquals(u':\\database\\rdb', actual)
        

if __name__ == '__main__':
    unittest.main()
