#!/usr/bin/python
# -*- coding: utf-8 -*-

# Test fnmatch wildcard behaviour.

# --- Python standard library ---
import fnmatch
import sys

# --- main ---------------------------------------------------------------------------------------
test_path = 'E:\AEL-stuff\AEL-DATs-No-Intro\Atari - 2600 (20191018-075817).dat'
test_patt = '*Atari - 2600*.dat'

print('Filename "{}"'.format(test_path))
print('Pattern  "{}"'.format(test_patt))
if fnmatch.fnmatch(test_path, test_patt): print('Test is True')
else:                                     print('Test is False')
sys.exit(0)
