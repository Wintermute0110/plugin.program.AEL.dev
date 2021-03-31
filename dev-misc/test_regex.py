#!/usr/bin/python
# -*- coding: utf-8 -*-

# Test regular expressions

# --- Python standard library ---
import pprint
import re
import sys

# --- main ---------------------------------------------------------------------------------------
test_path = 'E:\AEL-stuff\AEL-DATs-No-Intro\Atari - 2600 (20191018-075817).dat'
test_patt = '.*Atari - 2600\s\((\d\d\d\d\d\d\d\d)-(\d\d\d\d\d\d)\)\.dat'

print('Filename "{}"'.format(test_path))
print('Pattern  "{}"'.format(test_patt))
result = re.match(test_patt, test_path)
if result:
    print('Test is True')
    pprint.pprint(result.groups())
else:
    print('Test is False')
sys.exit(0)
