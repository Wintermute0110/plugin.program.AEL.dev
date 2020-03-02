#!/usr/bin/python3 -B
# -*- coding: utf-8 -*-

# Show why JSON cannot be decoded

# --- Python standard library ---
from __future__ import unicode_literals
import json
import pprint
import sys

# --- main ---------------------------------------------------------------------------------------
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
sys.exit(0)
