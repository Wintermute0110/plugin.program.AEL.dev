﻿#
# Advanced Emulator Launcher main script file
#

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.


# --- Modules/packages in this plugin ---
import resources.main

# -------------------------------------------------------------------------------------------------
# Hacks
# -------------------------------------------------------------------------------------------------
# --- Test the image selector class ---
# if __name__ == "__main__":
#     covers = []
#     covers.append(['http://www.captainwilliams.co.uk/sega/32x/images/32xsolo.jpg',
#                    'http://www.captainwilliams.co.uk/sega/32x/images/32xsolo.jpg',
#                    'Sega 32 X'])
#     image_url = main.gui_show_image_select(covers)

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
