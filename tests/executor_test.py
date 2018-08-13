import unittest, mock, os, sys 
from mock import *

from resources.utils import *
from resources.disk_IO import *
from resources.executors import *
from resources.utils_kodi import *

class Test_executortests(unittest.TestCase):
    
    ROOT_DIR = ''
    TEST_DIR = ''
    TEST_ASSETS_DIR = ''

    @classmethod
    def setUpClass(cls):
        set_use_print(True)
        set_log_level(LOG_DEBUG)
        
        cls.TEST_DIR = os.path.dirname(os.path.abspath(__file__))
        cls.ROOT_DIR = os.path.abspath(os.path.join(cls.TEST_DIR, os.pardir))
        cls.TEST_ASSETS_DIR = os.path.abspath(os.path.join(cls.TEST_DIR,'assets/'))
                
        print 'ROOT DIR: {}'.format(cls.ROOT_DIR)
        print 'TEST DIR: {}'.format(cls.TEST_DIR)
        print 'TEST ASSETS DIR: {}'.format(cls.TEST_ASSETS_DIR)
        print '---------------------------------------------------------------------------'
        
    @patch('resources.executors.is_windows')
    @patch('resources.executors.is_linux')            
    def test_if_on_linux_factory_loads_with_correct_executor(self, is_linux_mock, is_windows_mock):
        
        # arrange
        is_linux_mock.return_value = True
        is_windows_mock.return_value = False
        
        launcherPath = FileNameFactory.create('path')

        settings = {}
        settings['lirc_state'] = True

        # act
        factory = ExecutorFactory(settings, None)
        executor = factory.create(launcherPath)
        
        # assert
        actual = executor.__class__.__name__
        expected = 'LinuxExecutor'
        self.assertEqual(actual, expected)
                
    @patch('resources.executors.is_windows')
    @patch('resources.executors.is_osx')
    @patch('resources.executors.is_linux')                   
    def test_if_on_windows_factory_loads_with_correct_executor(self, is_linux_mock, is_osx_mock, is_windows_mock):
        
        # arrange
        is_linux_mock.return_value = False
        is_windows_mock.return_value = True
        is_osx_mock.return_value = False

        launcherPath = FileNameFactory.create('path')

        settings = {}
        settings['windows_cd_apppath'] = ''
        settings['windows_close_fds'] = ''

        # act
        factory = ExecutorFactory(settings, None)
        executor = factory.create(launcherPath)
        
        # assert
        actual = executor.__class__.__name__
        expected = 'WindowsExecutor'
        self.assertEqual(actual, expected)  
        
    @patch('resources.executors.is_windows')
    @patch('resources.executors.is_osx')
    @patch('resources.executors.is_linux')               
    def test_if_on_windows_with_bat_files_factory_loads_with_correct_executor(self, is_linux_mock, is_osx_mock, is_windows_mock):

        # arrange
        is_linux_mock.return_value = False
        is_windows_mock.return_value = True
        is_osx_mock.return_value = False
                
        launcherPath = FileNameFactory.create('c:\\app\\testcase.bat')

        settings = {}
        settings['show_batch_window'] = False

        # act
        factory = ExecutorFactory(settings, None)
        executor = factory.create(launcherPath)
        
        # assert
        actual = executor.__class__.__name__
        expected = 'WindowsBatchFileExecutor'
        self.assertEqual(actual, expected)  
        
    @patch('resources.executors.is_windows')
    @patch('resources.executors.is_osx')
    @patch('resources.executors.is_linux')       
    def test_if_on_windows_with_lnk_files_factory_loads_with_correct_executor(self, is_linux_mock, is_osx_mock, is_windows_mock):

        # arrange
        is_linux_mock.return_value = False
        is_windows_mock.return_value = True
        is_osx_mock.return_value = False
        
        launcherPath = FileNameFactory.create('c:\\app\\testcase.lnk')

        settings = {}

        # act
        factory = ExecutorFactory(settings, None)
        executor = factory.create(launcherPath)

        # assert
        actual = executor.__class__.__name__
        expected = 'WindowsLnkFileExecutor'
        self.assertEqual(actual, expected)
        
    def test_if_xbmc_apppath_factory_loads_with_correct_executor(self):
         
        # arrange
        set_log_level(LOG_VERB)
        set_use_print(True)
        
        launcherPath = FileNameFactory.create('c:\\boop\\xbmc.exe')

        settings = {}

        # act
        factory = ExecutorFactory(settings, None)
        executor = factory.create(launcherPath)

        # assert
        actual = executor.__class__.__name__
        expected = 'XbmcExecutor'
        self.assertEqual(actual, expected)
        
    @patch('resources.executors.is_windows')
    @patch('resources.executors.is_osx')
    @patch('resources.executors.is_linux')            
    def test_if_on_osx_factory_loads_with_correct_executor(self, is_linux_mock, is_osx_mock, is_windows_mock):

        # arrange
        is_linux_mock.return_value = False
        is_windows_mock.return_value = False
        is_osx_mock.return_value = True

        launcherPath = FileNameFactory.create('durp\\apple\\durp')

        settings = {}

        # act
        factory = ExecutorFactory(settings, None)
        executor = factory.create(launcherPath)

        # assert
        actual = executor.__class__.__name__
        expected = 'OSXExecutor'
        self.assertEqual(actual, expected)
       
    def test_when_using_urls_the_correct_web_executor_loads(self):
        
        # arrange
        launcherPath = FileNameFactory.create('durp\\apple\\durp')

        settings = {}

        # act
        factory = ExecutorFactory(settings, None)
        executor = factory.create(FileNameFactory.create('steam://rungameid/'))

        # assert
        actual = executor.__class__.__name__
        expected = 'WebBrowserExecutor'
        self.assertEqual(actual, expected)

if __name__ == '__main__':
    unittest.main()
