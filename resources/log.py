# -*- coding: utf-8 -*-

# Copyright (c) 2016-2022 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# Advanced Emulator/MAME Launcher utility functions.
# The idea if this module is to share it between AEL and AML.
#
# Log related functions.

# --- Addon modules ---
import resources.const as const

# --- Kodi modules ---
try:
    import xbmc
except:
    KODI_RUNTIME_AVAILABLE_UTILS = False
else:
    KODI_RUNTIME_AVAILABLE_UTILS = True

# --- Python standard library ---

# -------------------------------------------------------------------------------------------------
# Logging functions.
# AEL never uses LOG_FATAL. Fatal error in my addons use LOG_ERROR. When an ERROR message is
# printed the addon must stop execution and exit.
# Kodi Matrix has changed the log levels.
# Valid set of log levels should now be: DEBUG, INFO, WARNING, ERROR and FATAL
#
# @python_v17 Default level changed from LOGNOTICE to LOGDEBUG
# @python_v19 Removed LOGNOTICE (use LOGINFO) and LOGSEVERE (use LOGFATAL)
#
# https://forum.kodi.tv/showthread.php?tid=344263&pid=2943703#pid2943703
# https://github.com/xbmc/xbmc/pull/17730
# -------------------------------------------------------------------------------------------------
# Constants
LOG_ERROR   = 0
LOG_WARNING = 1
LOG_INFO    = 2
LOG_DEBUG   = 3

# Internal globals
current_log_level = LOG_INFO

def set_log_level(level):
    global current_log_level
    current_log_level = level

def dump_variable(var_name, var):
    if current_log_level < LOG_DEBUG: return
    log_text = '{} DUMP : Dumping variable "{}"\n{}'.format(ADDON_SHORT_NAME,
        var_name, pprint.pformat(var))
    xbmc.log(log_text, level = xbmc.LOGERROR)

# For Unicode stuff in Kodi log see https://github.com/romanvm/kodi.six
def debug_KR(text_line):
    if current_log_level < LOG_DEBUG: return

    # If it is bytes we assume it's "utf-8" encoded.
    # will fail if called with other encodings (latin, etc).
    if isinstance(text_line, const.binary_type): text_line = text_line.decode('utf-8')

    # At this point we are sure text_line is a Unicode string.
    # Kodi functions (Python 3) require Unicode strings as arguments.
    # Kodi functions (Python 2) require UTF-8 encoded bytes as arguments.
    log_text = const.ADDON_SHORT_NAME + ' DEBUG: ' + text_line
    xbmc.log(log_text, level = xbmc.LOGINFO)

def info_KR(text_line):
    if current_log_level < LOG_INFO: return
    if isinstance(text_line, const.binary_type): text_line = text_line.decode('utf-8')
    log_text = const.ADDON_SHORT_NAME + ' INFO : ' + text_line
    xbmc.log(log_text, level = xbmc.LOGINFO)

def warning_KR(text_line):
    if current_log_level < LOG_WARNING: return
    if isinstance(text_line, const.binary_type): text_line = text_line.decode('utf-8')
    log_text = const.ADDON_SHORT_NAME + ' WARN : ' + text_line
    xbmc.log(log_text, level = xbmc.LOGWARNING)

def error_KR(text_line):
    if current_log_level < LOG_ERROR: return
    if isinstance(text_line, const.binary_type): text_line = text_line.decode('utf-8')
    log_text = const.ADDON_SHORT_NAME + ' ERROR: ' + text_line
    xbmc.log(log_text, level = xbmc.LOGERROR)

# Replacement functions when running outside Kodi with the standard Python interpreter.
def debug_Python(text_line): print(text_line)
def info_Python(text_line): print(text_line)
def warning_Python(text_line): print(text_line)
def error_Python(text_line): print(text_line)

# ------------------------------------------------------------------------------------------------
# If running with Kodi Python interpreter use Kodi proper functions.
# If running with the standard Python interpreter use replacement functions.
# 
# Functions here in the same order as in the Function List browser.
# ------------------------------------------------------------------------------------------------
if KODI_RUNTIME_AVAILABLE_UTILS:
    debug, info, warning, error = debug_KR, info_KR, warning_KR, error_KR
else:
    debug, info, warning, error = debug_Python, info_Python, warning_Python, error_Python
