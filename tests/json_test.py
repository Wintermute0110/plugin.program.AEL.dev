#!/usr/bin/python
# -*- coding: utf-8 -*-

# --- Python standard library ---
from __future__ import unicode_literals
import pprint
import json
import unittest

# --- main ---------------------------------------------------------------------------------------

class Test_Json(unittest.TestCase):
    
    @unittest.skip('File not available')    
    def test_json_decoding_issues(self):
        JSON_file = 'ScreenScraper_page_data_raw.txt'

        print('Loading "{}"'.format(JSON_file))
        with open(JSON_file, 'r') as file:
            json_str = file.read()
        with open(JSON_file, 'r') as file:
            json_str_list = file.readlines()

        print('Trying to decode JSON...')
        try:
            ar = json.loads(json_str)
        except json.decoder.JSONDecodeError as ex:
            print('Exception json.decoder.JSONDecodeError')
            print('msg "{}"'.format(ex.msg))
            print('pos "{}"'.format(ex.pos))
            print('lineno "{}"'.format(ex.lineno))
            print('colno "{}"'.format(ex.colno))
            print('"{}"'.format(json_str_list[ex.lineno]))
        
        self.assertTrue(ar)
