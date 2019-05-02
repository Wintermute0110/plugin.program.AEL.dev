import unittest, mock, os, sys
from mock import *

import xbmcaddon, xbmc

from resources.utils import *
from resources.constants import *

class Test_utilstests(unittest.TestCase):
    
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

    def test_when_getting_url_extension_it_returns_the_correct_extension(self):

        # arrange
        url = 'http://wwww.somesite.com/with/somepicture.jpg'
        expected = '.jpg'

        # act
        actual = text_get_URL_extension(url)

        # assert
        self.assertEqual(expected, actual)

    def test_when_getting_url_extension_of_an_url_without_an_extension_it_will_return_empty(self):

        
        # arrange
        url = 'http://wwww.somesite.com/with/somepicture'
        expected = ''

        # act
        actual = text_get_URL_extension(url)

        # assert
        self.assertEqual(expected, actual)
        
    def test_when_getting_image_url_extension_it_returns_the_correct_extension(self):

        # arrange
        url = 'http://wwww.somesite.com/with/somepicture.png'
        expected = '.png'

        # act
        actual = text_get_image_URL_extension(url)

        # assert
        self.assertEqual(expected, actual)
                      
    def test_when_getting_image_url_extension_of_an_url_without_an_extension_it_will_return_jpg(self):

        # arrange
        url = 'http://wwww.somesite.com/with/somepicture'
        expected = '.jpg'

        # act
        actual = text_get_image_URL_extension(url)

        # assert
        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
