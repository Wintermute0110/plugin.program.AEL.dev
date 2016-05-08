#
# Advanced Emulator Launcher miscellaneous functions
#

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# --- Constants ---------------------------------------------------------------
LOG_DEBUG = 0
LOG_WARNING = 1
LOG_INFO = 2
LOG_VERB = 3
LOG_DEBUG = 4

# --- Internal globals --------------------------------------------------------
current_log_level = LOG_INFO

# --- Logging functions -------------------------------------------------------
def set_log_level(level);
    current_log_level = level

def log_debug(str_text):
    if Settings.log_level >= LOG_DEBUG:
        xbmc.log("AEL DEBUG: " + str_text)

def log_verb(str_text):
    if Settings.log_level >= LOG_VERB:
        xbmc.log("AEL VERB : " + str_text)

def log_info(str_text):
    if Settings.log_level >= LOG_INFO:
        xbmc.log("AEL INFO : " + str_text)

def log_warn(str_text):
    if Settings.log_level >= LOG_WARNING:
        xbmc.log("AEL WARN : " + str_text)

def log_err(str_text):
    if Settings.log_level >= LOG_ERROR:
        xbmc.log("AEL ERROR: " + str_text)

#
# Displays a modal dialog with an OK button.
# Dialog can have up to 3 rows of text.
#
def log_kodi_dialog_OK(title, row1, row2='', row3=''):
    dialog = xbmcgui.Dialog()
    ok = dialog.ok(title, row1, row2, row3)

#
# Displays a small box in the low right corner
#
def log_kodi_notify(title, text, time=5000):
    xbmc.executebuiltin("XBMC.Notification(%s,%s,%s,%s)" % (title, text, time, ICON_IMG_FILE_PATH))
