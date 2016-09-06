# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher main script file
#

# Copyright (c) 2016 Wintermute0110 <wintermute0110@gmail.com>
# Portions (c) 2010-2015 Angelscry and others
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

# --- Modules/packages in this plugin ---
import resources.main

# -------------------------------------------------------------------------------------------------
# Hacks and tests
# -------------------------------------------------------------------------------------------------
# --- Test the image selector class ---
# if __name__ == "__main__":
#     plugin = resources.main.Main()
#     covers = []
#     covers.append(['http://www.captainwilliams.co.uk/sega/32x/images/32xsolo.jpg',
#                    'http://www.captainwilliams.co.uk/sega/32x/images/32xsolo.jpg',
#                    'Sega 32 X'])
#     image_url = plugin.gui_show_image_select(covers)

# -------------------------------------------------------------------------------------------------
# main()
# -------------------------------------------------------------------------------------------------
# Put the main bulk of the code in files inside /resources/, which is a package directory. 
# This way, the Python interpreter will precompile them into bytecode (files PYC/PYO) so
# loading time is faster compared to PY files.
#
# See http://www.network-theory.co.uk/docs/pytut/CompiledPythonfiles.html
if __name__ == "__main__":
    plugin = resources.main.Main()

    plugin.run_plugin()

