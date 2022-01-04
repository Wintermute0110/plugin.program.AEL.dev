#!/usr/bin/python
# -*- coding: utf-8 -*-

# Test regular expressions

# --- Python standard library ---
from __future__ import unicode_literals
import pprint
import re
import unittest
import fnmatch

# --- main ---------------------------------------------------------------------------------------

class Test_Regex(unittest.TestCase):
        
    def test_regex_patterns(self):
        test_path = 'E:\AEL-stuff\AEL-DATs-No-Intro\Atari - 2600 (20191018-075817).dat'
        test_patt = '.*Atari - 2600\s\((\d\d\d\d\d\d\d\d)-(\d\d\d\d\d\d)\)\.dat'
        
        print('Filename "{}"'.format(test_path))
        print('Pattern  "{}"'.format(test_patt))
        result = re.match(test_patt, test_path)
        
        self.assertTrue(result)
        pprint.pprint(result.groups())
        
    def test_fmatch(self):
        test_path = 'E:\AEL-stuff\AEL-DATs-No-Intro\Atari - 2600 (20191018-075817).dat'
        test_patt = '*Atari - 2600*.dat'

        print('Filename "{}"'.format(test_path))
        print('Pattern  "{}"'.format(test_patt))
        result = fnmatch.fnmatch(test_path, test_patt)
        
        self.assertTrue(result)