import unittest
import mock
from mock import *

import xbmcaddon, xbmc

import resources.utils as utils
from resources.utils_kodi import *

class Test_utilstests(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        set_use_print(True)

    def test_when_getting_url_extension_it_returns_the_correct_extension(self):

        # arrange
        url = 'http://wwww.somesite.com/with/somepicture.jpg'
        expected = '.jpg'

        # act
        actual = utils.text_get_URL_extension(url)

        # assert
        self.assertEqual(expected, actual)

    def test_when_getting_url_extension_of_an_url_without_an_extension_it_will_return_empty(self):

        
        # arrange
        url = 'http://wwww.somesite.com/with/somepicture'
        expected = ''

        # act
        actual = utils.text_get_URL_extension(url)

        # assert
        self.assertEqual(expected, actual)
        
    def test_when_getting_image_url_extension_it_returns_the_correct_extension(self):

        # arrange
        url = 'http://wwww.somesite.com/with/somepicture.png'
        expected = '.png'

        # act
        actual = utils.text_get_image_URL_extension(url)

        # assert
        self.assertEqual(expected, actual)
                      
    def test_when_getting_image_url_extension_of_an_url_without_an_extension_it_will_return_jpg(self):

        # arrange
        url = 'http://wwww.somesite.com/with/somepicture'
        expected = '.jpg'

        # act
        actual = utils.text_get_image_URL_extension(url)

        # assert
        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
