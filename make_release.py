# -*- coding: utf-8 -*-
#
# Prepare files for a new AML release.
#
#   1) Create directory plugin.program.AML
#
#   2) Copy required files to run AML. Do not copy unnecessary files.
#
#   3) Create file version.txt, which contains current git version.
#
#   4) Edit addon.xml to change plugin id, name and version.

# Copyright (c) 2016-2019 Wintermute0110 <wintermute0110@gmail.com>
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
from __future__ import unicode_literals
from __future__ import division

# --- configuration ---
AML_ID      = 'plugin.program.AML'
AML_NAME    = 'Advanced MAME Launcher'
AML_VERSION = '0.9.9'

# --- main ---------------------------------------------------------------------------------------
print('Implement me!')
