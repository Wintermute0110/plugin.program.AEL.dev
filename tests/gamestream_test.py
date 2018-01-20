import unittest
import mock
from mock import *
from fakes import *

import os, binascii

from resources.gamestream import *
from resources.utils import *

class Test_gamestream(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        set_use_print(True)
        set_log_level(LOG_DEBUG)

    def read_file(self, path):
        with open(path, 'r') as f:
            return f.read()
        
    @patch('resources.net_IO.net_get_URL_using_handler')
    def test_connecting_to_a_gamestream_server(self, http_mock):
        
        # arrange
        test_dir = os.path.dirname(os.path.abspath(__file__))
        
        http_mock.return_value = self.read_file(test_dir + "\\gamestreamserver_response.xml")
        server = GameStreamServer('192.168.0.555', FileName(test_dir))
        
        # act
        actual = server.connect()

        # assert
        self.assertTrue(actual)

    @patch('resources.net_IO.net_get_URL_using_handler')
    def test_get_the_version_of_the_gamestream_server(self, http_mock):
         
        # arrange
        test_dir = os.path.dirname(os.path.abspath(__file__))
        
        http_mock.return_value = self.read_file(test_dir + "\\gamestreamserver_response.xml")
        server = GameStreamServer('192.168.0.555', FileName(test_dir))
        expected = '7.1.402.0'
        expectedMajor = 7

        # act
        server.connect()
        actual = server.getServerVersion()

        # assert
        self.assertEquals(expected, actual.getFullString())
        self.assertEquals(expectedMajor, actual.getMajor()) 
      
    @patch('resources.net_IO.net_get_URL_using_handler')
    def test_getting_apps_from_gamestream_server_gives_correct_amount(self, http_mock):

        # arrange
        test_dir = os.path.dirname(os.path.abspath(__file__))
        
        http_mock.return_value = self.read_file(test_dir + "\\gamestreamserver_apps.xml")
        server = GameStreamServer('192.168.0.555', FileName(test_dir))


        
    #@ignore('only testable with actual server')
    @patch('resources.gamestream.GameStreamServer.getCertificateBytes')
    @patch('resources.gamestream.GameStreamServer.getCertificateKeyBytes')
    @patch('resources.gamestream.randomBytes')
    def test_pair_with_gamestream_server(self, random_mock, certificateKeyBytesMock, certificateBytesMock):
        
        # arrange
        test_dir = os.path.dirname(os.path.abspath(__file__))
        addon_dir = FileName(test_dir)
        certificateBytesMock.return_value    = self.read_file(test_dir + "/nvidia.crt")
        certificateKeyBytesMock.return_value = self.read_file(test_dir + "/nvidia.key")
        random_mock.return_value = binascii.unhexlify("50ca25d03b4ac53368875b9a1bfb50cc")

        server = GameStreamServer('192.168.0.5', addon_dir)
        
        # act
        server.connect()
        pincode = server.generatePincode()
        paired = server.pairServer(pincode)

        # assert
        self.assertTrue(paired)

if __name__ == '__main__':
    unittest.main()
