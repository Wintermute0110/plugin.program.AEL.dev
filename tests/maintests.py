import unittest
import mock
from mock import *

import xbmcaddon

import resources.main as main

class Test_maintests(unittest.TestCase):
    

    # todo: replace by moving settings to external class and mock a simple dictionary
    def mocked_settings(arg):

        if arg == 'scan_metadata_policy' or arg == 'media_state_action' \
            or arg == 'metadata_scraper_mode' or arg == 'asset_scraper_mode' or arg == 'metadata_scraper' \
            or arg == 'asset_scraper' or arg =='scraper_metadata' \
            or arg == 'scraper_title' or  arg =='scraper_snap' or arg == 'scraper_bfront' \
            or arg == 'scraper_bback' or arg == 'scraper_cart' \
            or arg == 'scraper_fanart' or arg == 'scraper_banner' or arg =='scraper_clearlogo' \
            or arg =='scraper_flyer' or arg =='scraper_cabinet' \
            or arg == 'scraper_cpanel' or arg == 'scraper_pcb' or arg =='scraper_flyer_mame' \
            or arg == 'audit_unknown_roms' or arg == 'audit_1G1R_region':
            return 10
        
        if arg == 'scan_asset_policy':
            return 8

        if arg == 'log_level':
            return 1

        if arg == 'delay_tempo':
            return 0

        return '1'
    
    def test_when_running_the_plugin_no_errors_occur(self):
        self.test_when_running_the_plugin_no_errors_occur_mocked()
       
    @patch('resources.main.sys')
    @patch('resources.main.__addon_obj__.getSetting', side_effect = mocked_settings)
    def test_when_running_the_plugin_no_errors_occur_mocked(self, mock_addon, mock_sys):
        
        # arrange
        mock_sys.args.return_value = ['contenttype', 'noarg']
        target = main.Main()
        
        # act
        target.run_plugin()

        # assert
        pass

    def test_when_adding_new_category_the_correct_data_gets_stored(self):
        self.test_when_adding_new_category_the_correct_data_gets_stored_mocked()
        
    @patch('resources.main.xbmc.Keyboard.getText', autospec=True)
    @patch('resources.main.fs_write_catfile')
    @patch('resources.main.__addon_obj__.getSetting', side_effect = mocked_settings)
    def test_when_adding_new_category_the_correct_data_gets_stored_mocked(self, mock_addon, mock_writecatfile, mock_keyboard):
        
        # arrange
        expected =  'MyTestCategory'

        mock_keyboard.return_value = expected
        target = main.Main()
        
        # act
        target._cat_create_default()
        target._command_add_new_category()

        args = mock_writecatfile.call_args
        stored_categories = args[0][1]
        actual_category1 = stored_categories.items()[0][1]
        actual_category2 = stored_categories.items()[1][1]

        actuals = [actual_category1[u'm_name'],actual_category2[u'm_name']]
        print(stored_categories)

        # assert
        self.assertTrue(mock_writecatfile.called)
        self.assertIn(expected, actuals)


if __name__ == '__main__':
    unittest.main()
