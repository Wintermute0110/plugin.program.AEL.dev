# -*- coding: utf-8 -*-

# Advanced Emulator Launcher miscellaneous functions.
# Utility functions which DEPEND on Kodi modules

# Copyright (c) 2016-2019 Wintermute0110 <wintermute0110@gmail.com>
# Portions (c) 2010-2015 Angelscry
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See theGNU General Public License for more details.

# --- Python standard library ---
from __future__ import unicode_literals
import sys, os, shutil, time, random, hashlib, urlparse
import pprint

# --- Kodi modules ---
try:
    import xbmc, xbmcgui
except:
    from utils_kodi_standalone import *

# --- AEL modules ---
# utils.py and utils_kodi.py must not depend on any other AEL module to avoid circular dependencies.

# --- Constants ----------------------------------------------------------------------------------
LOG_ERROR   = 0
LOG_WARNING = 1
LOG_INFO    = 2
LOG_VERB    = 3
LOG_DEBUG   = 4

# --- Internal globals ---------------------------------------------------------------------------
current_log_level = LOG_INFO

# ------------------------------------------------------------------------------------------------
# Logging functions
# ------------------------------------------------------------------------------------------------
def set_log_level(level):
    global current_log_level

    current_log_level = level

def log_variable(var_name, var):
    if current_log_level < LOG_DEBUG: return
    log_text = 'AEL DUMP : Dumping variable "{}"\n{}'.format(var_name, pprint.pformat(var))
    xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGERROR)

# For Unicode stuff in Kodi log see http://forum.kodi.tv/showthread.php?tid=144677
def log_debug(str_text):
    # Return inmediately is log level is less than this function level.
    if current_log_level < LOG_DEBUG: return

    # If str_text has type str then we assume it is utf-8 encoded.
    # This will fail if str_text has other encoding (latin, etc).
    if isinstance(str_text, str): str_text = str_text.decode('utf-8')

    # At this point we are sure str_text is a unicode string.
    log_text = 'AEL DEBUG: ' + str_text
    xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGERROR)

def log_verb(str_text):
    if current_log_level < LOG_VERB: return
    if isinstance(str_text, str): str_text = str_text.decode('utf-8')
    log_text = 'AEL VERB : ' + str_text
    xbmc.log(log_text.encode('utf-8'), level=xbmc.LOGERROR)

def log_info(str_text):
    if current_log_level < LOG_INFO: return
    if isinstance(str_text, str): str_text = str_text.decode('utf-8')
    log_text = 'AEL INFO : ' + str_text
    xbmc.log(log_text.encode('utf-8'), level=xbmc.LOGERROR)

def log_warning(str_text):
    if current_log_level < LOG_WARNING: return
    if isinstance(str_text, str): str_text = str_text.decode('utf-8')
    log_text = 'AEL WARN : ' + str_text
    xbmc.log(log_text.encode('utf-8'), level=xbmc.LOGERROR)

def log_error(str_text):
    # Errors are always printed to log.
    if isinstance(str_text, str): str_text = str_text.decode('utf-8')
    log_text = 'AEL ERROR: ' + str_text
    xbmc.log(log_text.encode('utf-8'), level=xbmc.LOGERROR)

# -----------------------------------------------------------------------------
# Kodi notifications and dialogs
# -----------------------------------------------------------------------------
#
# Displays a modal dialog with an OK button. Dialog can have up to 3 rows of text, however first
# row is multiline.
# Call examples:
#  1) ret = kodi_dialog_OK('Launch ROM?')
#  2) ret = kodi_dialog_OK('Launch ROM?', title = 'AEL - Launcher')
#
def kodi_dialog_OK(row1, row2 = '', row3 = '', title = 'Advanced Emulator Launcher'):
    xbmcgui.Dialog().ok(title, row1, row2, row3)

# Returns True is YES was pressed, returns False if NO was pressed or dialog canceled.
def kodi_dialog_yesno(row1, row2='', row3='', title = 'Advanced Emulator Launcher'):
    ret = xbmcgui.Dialog().yesno(title, row1, row2, row3)

    return ret

# Returns True is YES was pressed, returns False if NO was pressed or dialog canceled.
def kodi_dialog_yesno_custom(text, yeslabel_str, nolabel_str):
    title = 'Advanced Emulator Launcher'
    return xbmcgui.Dialog().yesno(title, text, yeslabel = yeslabel_str, nolabel = nolabel_str)

#
# Displays a small box in the low right corner
#
def kodi_notify(text, title = 'Advanced Emulator Launcher', time = 5000):
    # --- Old way ---
    # xbmc.executebuiltin("XBMC.Notification(%s,%s,%s,%s)" % (title, text, time, ICON_IMG_FILE_PATH))

    # --- New way ---
    xbmcgui.Dialog().notification(title, text, xbmcgui.NOTIFICATION_INFO, time)

def kodi_notify_warn(text, title = 'Advanced Emulator Launcher warning', time = 7000):
    xbmcgui.Dialog().notification(title, text, xbmcgui.NOTIFICATION_WARNING, time)

#
# Do not use this function much because it is the same icon as when Python fails, and that may confuse the user.
#
def kodi_notify_error(text, title = 'Advanced Emulator Launcher error', time = 7000):
    xbmcgui.Dialog().notification(title, text, xbmcgui.NOTIFICATION_ERROR, time)

def kodi_refresh_container():
    log_debug('kodi_refresh_container()')
    xbmc.executebuiltin('Container.Refresh')

# Progress dialog that can be closed and reopened.
# If the dialog is canceled this class remembers it forever.
class KodiProgressDialog(object):
    def __init__(self):
        self.title = 'Advanced Emulator Launcher'
        self.progress = 0
        self.flag_dialog_canceled = False
        self.dialog_active = False
        self.progressDialog = xbmcgui.DialogProgress()

    def startProgress(self, message, num_steps = 100):
        self.num_steps = num_steps
        self.progress = 0
        self.dialog_active = True
        self.progressDialog.create(self.title, message)
        self.progressDialog.update(self.progress)

    # Update progress and optionally update messages as well.
    def updateProgress(self, step_index, message1 = '', message2 = ''):
        self.progress = (step_index * 100) / self.num_steps
        self.message1 = message1
        self.message2 = message2
        if message2:
            self.progressDialog.update(self.progress, message1, message2)
        else:
            self.progressDialog.update(self.progress, message1)

    # Update dialog message but keep same progress.
    def updateMessages(self, message1, message2):
        self.message1 = message1
        self.message2 = message2
        self.progressDialog.update(self.progress, message1, message2)

    # Update dialog message but keep same progress. message2 is removed if any.
    def updateMessage(self, message1):
        self.message1 = message1
        self.progressDialog.update(self.progress, message1)

    # Update message2 and keeps same progress and message1
    def updateMessage2(self, message2):
        self.message2 = message2
        self.progressDialog.update(self.progress, self.message1, message2)

    def isCanceled(self):
        # If the user pressed the cancel button before then return it now.
        if self.flag_dialog_canceled:
            return True
        else:
            self.flag_dialog_canceled = self.progressDialog.iscanceled()
            return self.flag_dialog_canceled

    def close(self):
        # Before closing the dialog check if the user pressed the Cancel button and remember
        # the user decision.
        if self.progressDialog.iscanceled(): self.flag_dialog_canceled = True
        self.progressDialog.close()
        self.dialog_active = False

    def endProgress(self):
        # Before closing the dialog check if the user pressed the Cancel button and remember
        # the user decision.
        if self.progressDialog.iscanceled(): self.flag_dialog_canceled = True
        self.progressDialog.update(100)
        self.progressDialog.close()
        self.dialog_active = False

    # Reopens a previously closed dialog, remembering the messages and the progress.
    def reopen(self):
        if not self.message2:
            self.progressDialog.create(self.title, self.message1, self.message2)
        else:
            self.progressDialog.create(self.title, self.message1)
        self.progressDialog.update(self.progress)

# To be used as a base class.
class KodiProgressDialog_Chrisism(object):
    def __init__(self):
        self.progress = 0
        self.progressDialog = xbmcgui.DialogProgress()
        self.verbose = True

    def _startProgressPhase(self, title, message):
        self.progressDialog.create(title, message)

    def _updateProgress(self, progress, message1 = None, message2 = None):
        self.progress = progress
        if not self.verbose:
            self.progressDialog.update(progress)
        else:
            self.progressDialog.update(progress, message1, message2)

    def _updateProgressMessage(self, message1, message2 = None):
        if not self.verbose: return

        self.progressDialog.update(self.progress, message1, message2)

    def _isProgressCanceled(self):
        return self.progressDialog.iscanceled()

    def _endProgressPhase(self, canceled = False):
        if not canceled: self.progressDialog.update(100)
        self.progressDialog.close()

# -------------------------------------------------------------------------------------------------
# Kodi error reporting
# -------------------------------------------------------------------------------------------------
KODI_MESSAGE_NONE        = 100
# Kodi notifications must be short.
KODI_MESSAGE_NOTIFY      = 200
KODI_MESSAGE_NOTIFY_WARN = 300
# Kodi OK dialog to display a message.
KODI_MESSAGE_DIALOG      = 400

# If status_dic['status'] is True then everything is OK. If status_dic['status'] is False,
# then display the notification.
def kodi_new_status_dic(message):
    return {
        'status' : True,
        'dialog' : KODI_MESSAGE_NOTIFY,
        'msg'    : message,
    }

def kodi_display_user_message(op_dic):
    if op_dic['dialog'] == KODI_MESSAGE_NONE:
        return
    elif op_dic['dialog'] == KODI_MESSAGE_NOTIFY:
        kodi_notify(op_dic['msg'])
    elif op_dic['dialog'] == KODI_MESSAGE_NOTIFY_WARN:
        kodi_notify(op_dic['msg'])
    elif op_dic['dialog'] == KODI_MESSAGE_DIALOG:
        kodi_dialog_OK(op_dic['msg'])

# -------------------------------------------------------------------------------------------------
# Kodi specific stuff
# -------------------------------------------------------------------------------------------------
# About Kodi image cache
#
# See http://kodi.wiki/view/Caches_explained
# See http://kodi.wiki/view/Artwork
# See http://kodi.wiki/view/HOW-TO:Reduce_disk_space_usage
# See http://forum.kodi.tv/showthread.php?tid=139568 (What are .tbn files for?)
#
# Whenever Kodi downloads images from the internet, or even loads local images saved along
# side your media, it caches these images inside of ~/.kodi/userdata/Thumbnails/. By default,
# large images are scaled down to the default values shown below, but they can be sized
# even smaller to save additional space.

#
# Gets where in Kodi image cache an image is located.
# image_path is a Unicode string.
# cache_file_path is a Unicode string.
#
def kodi_get_cached_image_FN(image_path):
    THUMBS_CACHE_PATH = os.path.join(xbmc.translatePath('special://profile/' ), 'Thumbnails')

    # --- Get the Kodi cached image ---
    # This function return the cache file base name
    base_name = xbmc.getCacheThumbName(image_path)
    cache_file_path = os.path.join(THUMBS_CACHE_PATH, base_name[0], base_name)

    return cache_file_path

#
# Updates Kodi image cache for the image provided in img_path.
# In other words, copies the image img_path into Kodi cache entry.
# Needles to say, only update image cache if image already was on the cache.
# img_path is a Unicode string
#
def kodi_update_image_cache(img_path):
    # What if image is not cached?
    cached_thumb = kodi_get_cached_image_FN(img_path)
    log_debug('kodi_update_image_cache()       img_path {0}'.format(img_path))
    log_debug('kodi_update_image_cache()   cached_thumb {0}'.format(cached_thumb))

    # For some reason Kodi xbmc.getCacheThumbName() returns a filename ending in TBN.
    # However, images in the cache have the original extension. Replace TBN extension
    # with that of the original image.
    cached_thumb_root, cached_thumb_ext = os.path.splitext(cached_thumb)
    if cached_thumb_ext == '.tbn':
        img_path_root, img_path_ext = os.path.splitext(img_path)
        cached_thumb = cached_thumb.replace('.tbn', img_path_ext)
        log_debug('kodi_update_image_cache() U cached_thumb {0}'.format(cached_thumb))

    # --- Check if file exists in the cache ---
    # xbmc.getCacheThumbName() seems to return a filename even if the local file does not exist!
    if not os.path.isfile(cached_thumb):
        log_debug('kodi_update_image_cache() Cached image not found. Doing nothing')
        return

    # --- Copy local image into Kodi image cache ---
    # >> See https://docs.python.org/2/library/sys.html#sys.getfilesystemencoding
    log_debug('kodi_update_image_cache() Image found in cache. Updating Kodi image cache')
    log_debug('kodi_update_image_cache() copying {0}'.format(img_path))
    log_debug('kodi_update_image_cache() into    {0}'.format(cached_thumb))
    fs_encoding = sys.getfilesystemencoding()
    log_debug('kodi_update_image_cache() fs_encoding = "{0}"'.format(fs_encoding))
    encoded_img_path = img_path.encode(fs_encoding, 'ignore')
    encoded_cached_thumb = cached_thumb.encode(fs_encoding, 'ignore')
    try:
        shutil.copy2(encoded_img_path, encoded_cached_thumb)
    except OSError:
        log_kodi_notify_warn('AEL warning', 'Cannot update cached image (OSError)')
        lod_error('Exception in kodi_update_image_cache()')
        lod_error('(OSError) Cannot update cached image')

    # >> Is this really needed?
    # xbmc.executebuiltin('XBMC.ReloadSkin()')

def kodi_toogle_fullscreen():
    # Frodo and up compatible
    xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Input.ExecuteAction", "params":{"action":"togglefullscreen"}, "id":"1"}')

#
# Displays a text window and requests a monospaced font.
#
def kodi_display_text_window_mono(window_title, info_text):
    log_debug('Setting Window(10000) Property "FontWidth" = "monospaced"')
    xbmcgui.Window(10000).setProperty('FontWidth', 'monospaced')
    xbmcgui.Dialog().textviewer(window_title, info_text)
    log_debug('Setting Window(10000) Property "FontWidth" = "proportional"')
    xbmcgui.Window(10000).setProperty('FontWidth', 'proportional')

#
# Displays a text window with a proportional font (default).
#
def kodi_display_text_window(window_title, info_text):
    xbmcgui.Dialog().textviewer(window_title, info_text)
