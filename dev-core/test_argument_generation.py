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
from resources.utils import *
from resources.misc import *

# --- Python standard library ---
import re
import shlex

# --- Main ----------------------------------------------------------------------------------------
ROM = '\\\\STORM\\SEGA Dreamcast\\4 Wheel Thunder (E).chd'
arguments = '-run=dc -image="$rom$"'
application = 'Z:\\mame\\mame.exe'

if ROM[0] == '\\' and ROM[1] == '\\':
    print('Windows path detected!')

ROMFileName = FileName(ROM)
rom_str = ROMFileName.getPath()
arguments = arguments.replace('$rom$', rom_str)
log_info('_command_run_rom() final arguments "{}"'.format(arguments))

arg_list = shlex.split(arguments, posix = True)
exec_list = [application] + arg_list
log_debug('_run_process() arguments = {}'.format(arguments))
log_debug('_run_process() arg_list  = {}'.format(arg_list))
log_debug('_run_process() exec_list = {}'.format(exec_list))
