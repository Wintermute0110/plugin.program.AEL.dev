import unittest, mock, os, sys
from mock import *
from fakes import *

import xbmcaddon

from resources.utils_kodi import *
from resources.constants import *


class Test_utils_kodi_tests(unittest.TestCase):
    
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

    def test_building_a_wizards_works(self):
        
        page1 = KeyboardWizardDialog('x', 'abc', None)
        page2 = SelectionWizardDialog('x2',['aa'], 'abc2', page1)
        page3 = KeyboardWizardDialog('x3', 'abc3', page2)

        props = {}

        page3.runWizard(props)
        
    @patch('resources.utils_kodi.xbmc.Keyboard', autospec=True)     
    def test_starting_wizard_calls_pages_in_right_order(self, mock_keyboard): 
        
        # arrange
        mock_keyboard.getText().return_value = 'test'

        wizard = KeyboardWizardDialog('x1', 'expected1', None)
        wizard = KeyboardWizardDialog('x2', 'expected2', wizard)
        wizard = KeyboardWizardDialog('x3', 'expected3', wizard)

        props = {}

        # act
        wizard.runWizard(props)
        calls = mock_keyboard.call_args_list

        # assert
        self.assertEqual(3, len(calls))
        self.assertEqual(call('','expected1'), calls[0])
        self.assertEqual(call('','expected2'), calls[1])
        self.assertEqual(call('','expected3'), calls[2])

    @patch('resources.utils_kodi.xbmc.Keyboard.getText', autospec=True)     
    def test_when_i_give_the_wizardpage_a_custom_function_it_calls_it_as_expected(self, mock_keyboard): 
        
        # arrange
        mock_keyboard.return_value = 'expected'
        fake = FakeClass()

        props = {}
        page1 = KeyboardWizardDialog('key','title1', None, fake.FakeMethod)

        # act
        page1.runWizard(props)
        
        # assert
        self.assertEqual('expected', fake.value)
                
    @patch('resources.utils_kodi.xbmcgui.Dialog.select', autospec=True)
    def test_when_using_dictionary_select_dialog_it_gives_me_the_correct_result(self, mocked_dialog):

        # arrange
        dialog = DictionaryDialog()

        options = {}
        options['10'] = 'A'
        options['20'] = 'B'
        options['30'] = 'C'

        expected = '20'
        mocked_dialog.return_value = 2

        # act
        actual = dialog.select('mytitle', options)

        # assert
        self.assertIsNotNone(actual)
        self.assertEqual(actual, expected)
        
if __name__ == '__main__':
    unittest.main()
