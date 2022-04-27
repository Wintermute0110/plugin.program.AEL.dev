# -*- coding: utf-8 -*-

# Copyright (c) 2016-2021 Wintermute0110 <wintermute0110@gmail.com>
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
# All functions that depends on Kodi modules that are GUI RELATED.
# This includes IO functions functions.
#
# When Kodi modules are not available replacements can be provided. This is useful
# to use addon modules with CPython for testing or debugging.
#
# This module must NOT include any other addon modules to avoid circular dependencies. The
# only exception to this rule is the module .constants. This module is virtually included
# by every other addon module.

# --- Addon modules ---
import resources.const as const
import resources.log as log
import resources.utils as utils

# --- Kodi modules ---
try:
    import xbmc
    import xbmcaddon
    import xbmcgui
    import xbmcplugin
    import xbmcvfs
except:
    KODI_RUNTIME_AVAILABLE_UTILS = False
else:
    KODI_RUNTIME_AVAILABLE_UTILS = True

# --- Python standard library ---
# Check what modules are really used and remove not used ones.
import math
import time

# -------------------------------------------------------------------------------------------------
# Kodi useful definitions
# -------------------------------------------------------------------------------------------------
# https://codedocs.xyz/AlwinEsch/kodi/group__kodi__guilib__listitem__iconoverlay.html
KODI_ICON_OVERLAY_NONE = 0
KODI_ICON_OVERLAY_RAR = 1
KODI_ICON_OVERLAY_ZIP = 2
KODI_ICON_OVERLAY_LOCKED = 3
KODI_ICON_OVERLAY_UNWATCHED = 4
KODI_ICON_OVERLAY_WATCHED = 5
KODI_ICON_OVERLAY_HD = 6

# -------------------------------------------------------------------------------------------------
# Kodi notifications and dialogs
# -------------------------------------------------------------------------------------------------
# Displays a modal dialog with an OK button. Dialog can have up to 3 rows of text, however first
# row is multiline.
# Call examples:
#  1) ret = kodi.dialog_OK('Launch ROM?')
#  2) ret = kodi.dialog_OK('Launch ROM?', title = 'AML - Launcher')
def dialog_OK(text, title = const.ADDON_LONG_NAME):
    xbmcgui.Dialog().ok(title, text)

# Returns True is YES was pressed, returns False if NO was pressed or dialog canceled.
def dialog_yesno(text, title = const.ADDON_LONG_NAME):
    return xbmcgui.Dialog().yesno(title, text)

# Returns True is YES was pressed, returns False if NO was pressed or dialog canceled.
def dialog_yesno_custom(text, yeslabel_str, nolabel_str, title = const.ADDON_LONG_NAME):
    return xbmcgui.Dialog().yesno(title, text, yeslabel = yeslabel_str, nolabel = nolabel_str)

def dialog_yesno_timer(text, timer_ms = 30000, title = const.ADDON_LONG_NAME):
    return xbmcgui.Dialog().yesno(title, text, autoclose = timer_ms)

# Returns a directory. See https://codedocs.xyz/AlwinEsch/kodi
#
# This supports directories, files, images and writable directories.
# xbmcgui.Dialog().browse(type, heading, shares[, mask, useThumbs, treatAsFolder, defaultt, enableMultiple])
#
# This supports files and images only.
# xbmcgui.Dialog().browseMultiple(type, heading, shares[, mask, useThumbs, treatAsFolder, defaultt])
# 
# This supports directories, files, images and writable directories.
# xbmcgui.Dialog().browseSingle(type, heading, shares[, mask, useThumbs, treatAsFolder, defaultt])
#
# shares   string or unicode - from sources.xml
# "files"  list file sources (added through filemanager)
# "local"  list local drives
# ""       list local drives and network shares

# Returns a directory.
def dialog_get_directory(d_heading, d_dir = ''):
    if d_dir:
        ret = xbmcgui.Dialog().browse(0, d_heading, '', defaultt = d_dir)
    else:
        ret =  xbmcgui.Dialog().browse(0, d_heading, '')

    return ret

# Mask is supported only for files.
# mask  [opt] string or unicode - '|' separated file mask. (i.e. '.jpg|.png')
#
# KODI BUG For some reason *.dat files are not shown on the dialog, but XML files are OK!!!
# Fixed in Krypton Beta 6 http://forum.kodi.tv/showthread.php?tid=298161
def dialog_get_file(d_heading, mask = '', default_file = ''):
    if mask and default_file:
        ret = xbmcgui.Dialog().browse(1, d_heading, '', mask = mask, defaultt = default_file)
    elif default_file:
        ret = xbmcgui.Dialog().browse(1, d_heading, '', defaultt = default_file)
    elif mask:
        ret = xbmcgui.Dialog().browse(1, d_heading, '', mask = mask)
    else:
        ret = xbmcgui.Dialog().browse(1, d_heading, '')

    return ret

def dialog_get_image(d_heading, mask = '', default_file = ''):
    if mask and default_file:
        ret = xbmcgui.Dialog().browse(2, d_heading, '', mask = mask, defaultt = default_file)
    elif default_file:
        ret = xbmcgui.Dialog().browse(2, d_heading, '', defaultt = default_file)
    elif mask:
        ret = xbmcgui.Dialog().browse(2, d_heading, '', mask = mask)
    else:
        ret = xbmcgui.Dialog().browse(2, d_heading, '')

    return ret

def dialog_get_wdirectory(d_heading):
    return xbmcgui.Dialog().browse(3, d_heading, '')

# Select multiple versions of the avobe functions.
def dialog_get_file_multiple(d_heading, mask = '', d_file = ''):
    if mask and d_file:
        ret = xbmcgui.Dialog().browse(1, d_heading, '', mask = mask, defaultt = d_file, enableMultiple = True)
    elif d_file:
        ret = xbmcgui.Dialog().browse(1, d_heading, '', defaultt = d_file, enableMultiple = True)
    elif mask:
        ret = xbmcgui.Dialog().browse(1, d_heading, '', mask = mask, enableMultiple = True)
    else:
        ret = xbmcgui.Dialog().browse(1, d_heading, '', enableMultiple = True)

    return ret

# Displays a small box in the bottom right corner
def notify(text, title = const.ADDON_LONG_NAME, time = 5000):
    xbmcgui.Dialog().notification(title, text, xbmcgui.NOTIFICATION_INFO, time)

def notify_warn(text, title = const.ADDON_LONG_NAME, time = 7000):
    xbmcgui.Dialog().notification(title, text, xbmcgui.NOTIFICATION_WARNING, time)

# Do not use this function much because it is the same icon displayed when Python fails
# with an exception and that may confuse the user.
def notify_error(text, title = const.ADDON_LONG_NAME, time = 7000):
    xbmcgui.Dialog().notification(title, text, xbmcgui.NOTIFICATION_ERROR, time)

# Wrapper function to get a text from the keyboard or None if the keyboard
# modal dialog was canceled.
def get_keyboard_text(heading = 'Kodi keyboard', default_text = ''):
    keyboard = KodiKeyboardDialog(heading, default_text)
    keyboard.executeDialog()
    if not keyboard.isConfirmed(): return None
    new_value_str = keyboard.getData().strip()
    return new_value_str

# Displays a text window and requests a monospaced font.
# v18 Leia change: New optional param added usemono.
def display_text_window_mono(window_title, info_text):
    xbmcgui.Dialog().textviewer(window_title, info_text.encode('utf-8'), True)

# Displays a text window with a proportional font (default).
def display_text_window(window_title, info_text):
    xbmcgui.Dialog().textviewer(window_title, info_text.encode('utf-8'))

# Displays a text window and requests a monospaced font.
# def display_text_window_mono(window_title, info_text):
#     log.debug('Setting Window(10000) Property "FontWidth" = "monospaced"')
#     xbmcgui.Window(10000).setProperty('FontWidth', 'monospaced')
#     xbmcgui.Dialog().textviewer(window_title, info_text)
#     log.debug('Setting Window(10000) Property "FontWidth" = "proportional"')
#     xbmcgui.Window(10000).setProperty('FontWidth', 'proportional')

# Displays a text window with a proportional font (default).
# def display_text_window(window_title, info_text):
#     xbmcgui.Dialog().textviewer(window_title, info_text)

# -------------------------------------------------------------------------------------------------
# Kodi API wrapper objects.
# -------------------------------------------------------------------------------------------------
# Progress dialog that can be closed and reopened.
# Messages and progress in the dialog are always remembered, even if closed and reopened.
# If the dialog is canceled this class remembers it forever.
#
# Kodi Matrix change: Renamed option line1 to message. Removed option line2. Removed option line3.
# See https://forum.kodi.tv/showthread.php?tid=344263&pid=2933596#pid2933596
#
# --- Example 1 ---
# pDialog = KodiProgressDialog()
# pDialog.startProgress('Doing something...', step_total)
# for i in range():
#     pDialog.updateProgressInc()
#     # Do stuff...
# pDialog.endProgress()
class ProgressDialog(object):
    def __init__(self):
        self.heading = const.ADDON_LONG_NAME
        self.progress = 0
        self.flag_dialog_canceled = False
        self.dialog_active = False
        self.progressDialog = xbmcgui.DialogProgress()

    # Creates a new progress dialog.
    def startProgress(self, message, step_total = 100, step_counter = 0):
        if self.dialog_active: raise TypeError
        self.step_total = step_total
        self.step_counter = step_counter
        try:
            self.progress = math.floor((self.step_counter * 100) / self.step_total)
        except ZeroDivisionError:
            # Fix case when step_total is 0.
            self.step_total = 0.001
            self.progress = math.floor((self.step_counter * 100) / self.step_total)
        self.dialog_active = True
        self.message = message
        # In Leia and lower xbmcgui.DialogProgress().update() requires an int.
        if utils.kodi_running_version >= utils.KODI_VERSION_MATRIX:
            self.progressDialog.create(self.heading, self.message)
            self.progressDialog.update(self.progress)
        else:
            self.progressDialog.create(self.heading, self.message, ' ', ' ')
            self.progressDialog.update(int(self.progress))

    # Changes message and resets progress.
    def resetProgress(self, message, step_total = 100, step_counter = 0):
        if not self.dialog_active: raise TypeError
        self.step_total = step_total
        self.step_counter = step_counter
        try:
            self.progress = math.floor((self.step_counter * 100) / self.step_total)
        except ZeroDivisionError:
            # Fix case when step_total is 0.
            self.step_total = 0.001
            self.progress = math.floor((self.step_counter * 100) / self.step_total)
        self.message = message
        if utils.kodi_running_version >= utils.KODI_VERSION_MATRIX:
            self.progressDialog.update(self.progress, self.message)
        else:
            self.progressDialog.update(int(self.progress), self.message, ' ', ' ')

    # Update progress and optionally update message as well.
    def updateProgress(self, step_counter, message = None):
        if not self.dialog_active: raise TypeError
        self.step_counter = step_counter
        self.progress = math.floor((self.step_counter * 100) / self.step_total)
        if message is None:
            if utils.kodi_running_version >= utils.KODI_VERSION_MATRIX:
                self.progressDialog.update(self.progress)
            else:
                self.progressDialog.update(int(self.progress))
        else:
            if type(message) is not text_type: raise TypeError
            self.message = message
            if utils.kodi_running_version >= utils.KODI_VERSION_MATRIX:
                self.progressDialog.update(self.progress, self.message)
            else:
                self.progressDialog.update(int(self.progress), self.message, ' ', ' ')
        # DEBUG code
        # time.sleep(1)

    # Update progress, optionally update message as well, and autoincrements.
    # Progress is incremented AFTER dialog is updated.
    def updateProgressInc(self, message = None):
        if not self.dialog_active: raise TypeError
        self.progress = math.floor((self.step_counter * 100) / self.step_total)
        self.step_counter += 1
        if message is None:
            if utils.kodi_running_version >= utils.KODI_VERSION_MATRIX:
                self.progressDialog.update(self.progress)
            else:
                self.progressDialog.update(int(self.progress))
        else:
            if type(message) is not text_type: raise TypeError
            self.message = message
            if utils.kodi_running_version >= utils.KODI_VERSION_MATRIX:
                self.progressDialog.update(self.progress, self.message)
            else:
                self.progressDialog.update(int(self.progress), self.message, ' ', ' ')

    # Update dialog message but keep same progress.
    def updateMessage(self, message):
        if not self.dialog_active: raise TypeError
        if type(message) is not text_type: raise TypeError
        self.message = message
        if utils.kodi_running_version >= utils.KODI_VERSION_MATRIX:
            self.progressDialog.update(self.progress, self.message)
        else:
            self.progressDialog.update(int(self.progress), self.message, ' ', ' ')

    def isCanceled(self):
        # If the user pressed the cancel button before then return it now.
        if self.flag_dialog_canceled: return True
        # If not check and set the flag.
        if not self.dialog_active: raise TypeError
        self.flag_dialog_canceled = self.progressDialog.iscanceled()
        return self.flag_dialog_canceled

    # Before closing the dialog check if the user pressed the Cancel button and remember
    # the user decision.
    def endProgress(self):
        if not self.dialog_active: raise TypeError
        if self.progressDialog.iscanceled(): self.flag_dialog_canceled = True
        self.progressDialog.update(100)
        self.progressDialog.close()
        self.dialog_active = False

    # Like endProgress() but do not completely fills the progress bar.
    def close(self):
        if not self.dialog_active: raise TypeError
        if self.progressDialog.iscanceled(): self.flag_dialog_canceled = True
        self.progressDialog.close()
        self.dialog_active = False

    # Reopens a previously closed dialog with close(), remembering the messages
    # and the progress it had when it was closed.
    def reopen(self):
        if self.dialog_active: raise TypeError
        if kodi_running_version >= KODI_VERSION_MATRIX:
            self.progressDialog.create(self.heading, self.message)
            self.progressDialog.update(self.progress)
        else:
            self.progressDialog.create(self.heading, self.message, ' ', ' ')
            self.progressDialog.update(int(self.progress))
        self.dialog_active = True

# Wrapper class for xbmcgui.Dialog().select(). Takes care of Kodi bugs.
# v17 (Krypton) Python API changes:
#   Preselect option added.
#   Added new option useDetails.
#   Allow listitems for parameter list
class SelectDialog(object):
    def __init__(self, heading = const.ADDON_LONG_NAME, rows = [], preselect = -1, useDetails = False):
        self.heading = heading
        self.rows = rows
        self.preselect = preselect
        self.useDetails = useDetails
        self.dialog = xbmcgui.Dialog()

    def setHeading(self, heading): self.heading = heading

    def setRows(self, row_list): self.rows = row_list

    def setPreselect(self, preselect): self.preselect = preselect

    def setUseDetails(self, useDetails): self.useDetails = useDetails

    def executeDialog(self):
        # Kodi Krypton bug: if preselect is used then dialog never returns < 0 even if cancel
        # button is pressed. This bug has been solved in Leia.
        # See https://forum.kodi.tv/showthread.php?tid=337011
        if self.preselect >= 0 and utils.kodi_running_version >= utils.KODI_VERSION_LEIA:
            selection = self.dialog.select(self.heading, self.rows, useDetails = self.useDetails,
                preselect = self.preselect)
        else:
            selection = self.dialog.select(self.heading, self.rows, useDetails = self.useDetails)
        selection = None if selection < 0 else selection
        return selection

# Wrapper class for xbmc.Keyboard()
class KeyboardDialog(object):
    def __init__(self, heading = 'Kodi keyboard', default_text = ''):
        self.heading = heading
        self.default_text = default_text
        self.keyboard = xbmc.Keyboard()

    def setHeading(self, heading): self.heading = heading

    def setDefaultText(self, default_text): self.default_text = default_text

    def executeDialog(self):
        self.keyboard.setHeading(self.heading)
        self.keyboard.setDefault(self.default_text)
        self.keyboard.doModal()

    def isConfirmed(self): return self.keyboard.isConfirmed()

    # Use a different name from getText() to avoid coding errors.
    def getData(self): return self.keyboard.getText()
