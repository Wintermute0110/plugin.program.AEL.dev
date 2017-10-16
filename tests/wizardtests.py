import unittest
import mock
from mock import *

import xbmcaddon

from resources.launcher_wizards import *
from resources.constants import *

class Test_wizardtests(unittest.TestCase):
    
    def test_building_a_wizards_works(self):
        
        page1 = KeyboardWizardPage('x', 'abc', None)
        page2 = ComboboxWizardPage('x2',['aa'], 'abc2', page1)
        page3 = KeyboardWizardPage('x3', 'abc3', page2)

        page3.runWizard()

    def test_starting_wizard_calls_pages_in_right_order(self):
        self.test_starting_wizard_calls_pages_in_right_order_mocked()

    @patch('resources.main.xbmc.Keyboard', autospec=True)     
    def test_starting_wizard_calls_pages_in_right_order_mocked(self, mock_keyboard): 
        
        # arrange
        mock_keyboard.getText().return_value = 'test'

        wizard = KeyboardWizardPage('x1', 'expected1', None)
        wizard = KeyboardWizardPage('x2', 'expected2', wizard)
        wizard = KeyboardWizardPage('x3', 'expected3', wizard)

        # act
        wizard.runWizard()
        calls = mock_keyboard.call_args_list

        # assert
        self.assertEqual(3, len(calls))
        self.assertEqual(call('','expected1'), calls[0])
        self.assertEqual(call('','expected2'), calls[1])
        self.assertEqual(call('','expected3'), calls[2])

    def test_when_i_give_the_wizardpage_a_custom_function_it_calls_it_as_expected(self):
        self.test_when_i_give_the_wizardpage_a_custom_function_it_calls_it_as_expected_mocked()

    @patch('resources.main.xbmc.Keyboard.getText', autospec=True)     
    def test_when_i_give_the_wizardpage_a_custom_function_it_calls_it_as_expected_mocked(self, mock_keyboard): 
        
        # arrange
        mock_keyboard.return_value = 'expected'
        fake = FakeClass()

        page1 = KeyboardWizardPage('key','title1', None, fake.FakeMethod)

        # act
        page1.runWizard()
        
        # assert
        self.assertEqual('expected', fake.value)


class FakeClass():

    def FakeMethod(self, value, launcher):
        self.value = value

if __name__ == '__main__':
    unittest.main()
