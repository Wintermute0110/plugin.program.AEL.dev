#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Test the formating of ROM titles
#

# Copyright (c) 2016 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# --- Python standard library ---
import sys, os
import re

# --- Import AEL modules ---
# from AEL.resources.utils import *

# --- Main ----------------------------------------------------------------------------------------
ROM_title_list = [
    '[BIOS] CX4 (World)',
    '[BIOS] CX4',
    "'96 Zenkoku Koukou Soccer Senshuken (Japan)",
    'Super Mario World (Europe) (Rev 1)',
    'Super Mario World - Super Mario Bros. 4 (Japan)',
    "Super Mario World 2 - Yoshi's Island (Europe) (En,Fr,De)",
    "Super Mario World 2 - Yoshi's Island"
]

#
# Regexp to decompose a string in tokens
#
reg_exp = '\[.+?\]\s?|\(.+?\)\s?|\{.+?\}|[^\[\(\{]+'
for ROM_filename in ROM_title_list:
    tokens = re.findall(reg_exp, ROM_filename)
    print('---------> "{0}"'.format(ROM_filename))
    for i, token in enumerate(tokens): print('Token {0} -> "{1}"'.format(i, token.strip()))

    str_list = []
    for token in tokens:
        stripped_token = token.strip()
        if (stripped_token[0] == '[' or stripped_token[0] == '(' or stripped_token[0] == '{') and \
           stripped_token != '[BIOS]':
            continue
        str_list.append(stripped_token)
    new_title = ' '.join(str_list)
    print('>>>>>>>>>> "{0}"'.format(new_title))
    print('')
