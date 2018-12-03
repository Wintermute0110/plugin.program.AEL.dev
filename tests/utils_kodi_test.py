import unittest, mock, os, sys
from mock import *
from fakes import *

import xbmcaddon

from resources.utils import *
from resources.constants import *


class Test_utils_kodi_tests(unittest.TestCase):
    
    ROOT_DIR = ''
    TEST_DIR = ''
    TEST_ASSETS_DIR = ''

    @classmethod
    def setUpClass(cls):
        set_log_level(LOG_DEBUG)
        
        cls.TEST_DIR = os.path.dirname(os.path.abspath(__file__))
        cls.ROOT_DIR = os.path.abspath(os.path.join(cls.TEST_DIR, os.pardir))
        cls.TEST_ASSETS_DIR = os.path.abspath(os.path.join(cls.TEST_DIR,'assets/'))
                
        print 'ROOT DIR: {}'.format(cls.ROOT_DIR)
        print 'TEST DIR: {}'.format(cls.TEST_DIR)
        print 'TEST ASSETS DIR: {}'.format(cls.TEST_ASSETS_DIR)
        print '---------------------------------------------------------------------------'

    def test_building_a_wizards_works(self):
        
        page1 = KodiKeyboardWizardDialog('x', 'abc', None)
        page2 = KodiSelectionWizardDialog('x2',['aa'], 'abc2', page1)
        page3 = KodiKeyboardWizardDialog('x3', 'abc3', page2)

        props = {}

        page3.runWizard(props)
        
    @patch('resources.utils.xbmc.Keyboard', autospec=True)     
    def test_starting_wizard_calls_pages_in_right_order(self, mock_keyboard): 
        
        # arrange
        mock_keyboard.getText().return_value = 'test'

        wizard = KodiKeyboardWizardDialog('x1', 'expected1', None)
        wizard = KodiKeyboardWizardDialog('x2', 'expected2', wizard)
        wizard = KodiKeyboardWizardDialog('x3', 'expected3', wizard)

        props = {}

        # act
        wizard.runWizard(props)
        calls = mock_keyboard.call_args_list

        # assert
        self.assertEqual(3, len(calls))
        self.assertEqual(call('','expected1'), calls[0])
        self.assertEqual(call('','expected2'), calls[1])
        self.assertEqual(call('','expected3'), calls[2])

    @patch('resources.utils.xbmc.Keyboard.getText', autospec=True)     
    def test_when_i_give_the_wizardpage_a_custom_function_it_calls_it_as_expected(self, mock_keyboard): 
        
        # arrange
        mock_keyboard.return_value = 'expected'
        fake = FakeClass()

        props = {}
        page1 = KodiKeyboardWizardDialog('key','title1', None, fake.FakeMethod)

        # act
        page1.runWizard(props)
        
        # assert
        self.assertEqual('expected', fake.value)
                
    @patch('resources.utils.xbmcgui.Dialog.select', autospec=True)
    def test_when_using_dictionary_select_dialog_it_gives_me_the_correct_result(self, mocked_dialog):

        # arrange
        dialog = KodiDictionaryDialog()

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
    
    def test_when_using_a_condition_function_with_the_wizard_it_will_responsd_correctly(self):

        # arrange
        expected = 'expected'
        target = KodiDummyWizardDialog('actual', expected, None, None, lambda p1, p2: True)
        props = {}

        # act
        target.runWizard(props)
        actual = props['actual']
        
        # assert
        self.assertEqual(expected, actual)
       
if __name__ == '__main__':
    unittest.main()