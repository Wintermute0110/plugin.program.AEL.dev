#!/usr/bin/python3 -B
# -*- coding: utf-8 -*-

# Copyright (c) 2021 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# Test the formating of ROM titles

# --- Import AEL modules ---
import os
import sys
if __name__ == "__main__" and __package__ is None:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print('Adding to sys.path {}'.format(path))
    sys.path.append(path)
from resources.misc import *

# --- Python standard library ---
import re

# --- Main ----------------------------------------------------------------------------------------
string_list = [
    'Test string',
    '"Test string"',
    '"Test string',
    'Test string"',
    "'Test string'",
    "'Test string",
    "Test string'",
]

for my_str in string_list:
    print('{} -> {}'.format(my_str, misc_strip_quotes(my_str)))
