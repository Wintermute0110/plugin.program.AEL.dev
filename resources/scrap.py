#
# Advanced Emulator Launcher scraping engine
#

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# -----------------------------------------------------------------------------
# We support online an offline scrapers.
# Note that this module does not depend on Kodi stuff at all, and can be
# called externally from console Python scripts for testing of the scrapers.
# -----------------------------------------------------------------------------

# Load replacements for functions that depend on Kodi modules.
# This enables running this module in standard Python for testing scrapers.
try: import xbmc
except: from standalone import *
from disk_IO import *

#------------------------------------------------------------------------------
# Implement scrapers using polymorphism instead of using Angelscry 
# exec('import ...') hack.
#------------------------------------------------------------------------------
# Base class for all scrapers
# A) Offline or online
# B) Metadata, Thumb, Fanart
#
class Scraper:
    name = ''        # Short name to refer to object in code
    fancy_name = ''  # Fancy name for GUI and logs

#------------------------------------------------------------------------------
# Instantiate scraper objects
#------------------------------------------------------------------------------
from scrap_metadata import *
from scrap_thumb import *
from scrap_fanart import *

# Instantiate scraper objects. This list must match the one in Kodi settings.
scrapers_metadata = [ metadata_NULL(), metadata_Offline(), metadata_TheGamesDB(), metadata_GameFAQs(), metadata_arcadeHITS() ]
scrapers_thumb    = [ thumb_NULL(), thumb_TheGamesDB(), thumb_GameFAQs(), thumb_arcadeHITS(), thumb_Google() ]
scrapers_fanart   = [ fanart_NULL(), fanart_TheGamesDB(), fanart_GameFAQs(), fanart_arcadeHITS(), fanart_Google() ]
