#!/usr/bin/python
#
# Sanitize Advanced Launcher launchers.xml (invalid/unescaped characters)
#
# -*- coding: utf-8 -*-

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

# --- Python standar library ---
from __future__ import unicode_literals
import xml.etree.ElementTree as ET 
import re
import sys

# --- Import AEL modules ---
import sys, os
if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from disk_IO import *
from utils_kodi_standalone import *

# --- Configuration -------------------------------------------------------------------------------
launchers_xml_path = 'launchers.xml'
sanitized_xml_path = 'launchers_fixed.xml'

# --- main ----------------------------------------------------------------------------------------
# ~~~ Sanitize XML ~~~
# A) Read launcher.xml line by line
# B) Substitute offending/unescaped XML characters
# C) Write sanitized output XML
log_info('Sanitizing AL launchers.xml...')
with open(launchers_xml_path) as f_in:
    lines = f_in.readlines()
    f_in.close()
f_out = open(sanitized_xml_path, 'w')
p = re.compile(r'^(\s+)<(.+?)>(.+)</\2>(\s+)')
line_counter = 1
for line in lines:
    # >> line is str, convert to Unicode
    line = line.decode('utf-8')

    # >> Filter lines of type \t\t<tag>text</tag>\n
    m = p.match(line)

    if m:
        # log_debug('Matched    "{0}"'.format(line.rstrip()))
        # log_debug('G0 "{0}"'.format(m.group(0)))
        # log_debug('G1 "{0}"'.format(m.group(1)))
        # log_debug('G2 "{0}"'.format(m.group(2)))
        # log_debug('G3 "{0}"'.format(m.group(3)))
        start_blanks = m.group(1)
        tag          = m.group(2)
        string       = m.group(3)
        end_blanks   = m.group(4)

        # >> Escape standard XML characters
        # >> Escape common HTML stuff
        # >> &#xA; is line feed
        string = string.replace('&', '&amp;')      # Must be done first
        string = string.replace('<br>', '&#xA;')
        string = string.replace('<br />', '&#xA;')
        string = string.replace('"', '&quot;')
        string = string.replace("'", '&apos;')
        string = string.replace('<', '&lt;')
        string = string.replace('>', '&gt;')

        line = '{0}<{1}>{2}</{3}>{4}'.format(start_blanks, tag, string, tag, end_blanks)
        # log_debug('New line   "{0}"'.format(line.rstrip()))
    # else:
        # log_debug('No matched "{0}"'.format(line.rstrip()))

    # >> Write line
    f_out.write(line.encode('utf-8'))
    line_counter += 1
    # if line_counter > 310: sys.exit(0)
f_out.close()
log_info('Processed {0} XML lines'.format(line_counter))

# >> Read sanitized launchers.xml using ElementTree
print('Parsing launchers_fixed.xml with ElementTree...')
AL_categories = {}
AL_launchers = {}
fs_load_legacy_AL_launchers(sanitized_xml_path, AL_categories, AL_launchers)

