# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher miscellaneous functions
#

# Copyright (c) 2016-2017 Wintermute0110 <wintermute0110@gmail.com>
# Portions (c) 2010-2015 Angelscry
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

#
# Utility functions which DEPEND on Kodi modules
#

# --- Python standard library ---
from __future__ import unicode_literals
import sys, os, shutil, time, random, hashlib, urlparse

# --- Kodi modules ---
try:
    import xbmc, xbmcgui
except:
    from utils_kodi_standalone import *

# --- AEL modules ---
# >> utils.py and utils_kodi.py must not depend on any other AEL module to avoid circular dependencies.

# --- Constants ---------------------------------------------------------------
LOG_ERROR   = 0
LOG_WARNING = 1
LOG_INFO    = 2
LOG_VERB    = 3
LOG_DEBUG   = 4

# --- Internal globals --------------------------------------------------------
current_log_level = LOG_INFO

# -------------------------------------------------------------------------------------------------
# Logging functions
# -------------------------------------------------------------------------------------------------
def set_log_level(level):
    global current_log_level

    current_log_level = level

# For Unicode stuff in Kodi log see http://forum.kodi.tv/showthread.php?tid=144677
#
def log_debug(str_text):
    if current_log_level >= LOG_DEBUG:
        # if it is str we assume it's "utf-8" encoded.
        # will fail if called with other encodings (latin, etc).
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')

        # At this point we are sure str_text is a unicode string.
        log_text = u'AEL DEBUG: ' + str_text
        xbmc.log(log_text.encode('utf-8'), level=xbmc.LOGERROR)

def log_verb(str_text):
    if current_log_level >= LOG_VERB:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = u'AEL VERB : ' + str_text
        xbmc.log(log_text.encode('utf-8'), level=xbmc.LOGERROR)

def log_info(str_text):
    if current_log_level >= LOG_INFO:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = u'AEL INFO : ' + str_text
        xbmc.log(log_text.encode('utf-8'), level=xbmc.LOGERROR)

def log_warning(str_text):
    if current_log_level >= LOG_WARNING:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = u'AEL WARN : ' + str_text
        xbmc.log(log_text.encode('utf-8'), level=xbmc.LOGERROR)

def log_error(str_text):
    if current_log_level >= LOG_ERROR:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = u'AEL ERROR: ' + str_text
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
def kodi_dialog_OK(row1, row2='', row3='', title = 'Advanced Emulator Launcher'):
    dialog = xbmcgui.Dialog()
    dialog.ok(title, row1, row2, row3)

#
# Returns True is YES was pressed, returns False if NO was pressed or dialog canceled.
def kodi_dialog_yesno(row1, row2='', row3='', title = 'Advanced Emulator Launcher'):
    dialog = xbmcgui.Dialog()
    ret = dialog.yesno(title, row1, row2, row3)

    return ret

#
# Displays a small box in the low right corner
#
def kodi_notify(text, title = 'Advanced Emulator Launcher', time = 5000):
    # --- Old way ---
    # xbmc.executebuiltin("XBMC.Notification(%s,%s,%s,%s)" % (title, text, time, ICON_IMG_FILE_PATH))

    # --- New way ---
    dialog = xbmcgui.Dialog()
    dialog.notification(title, text, xbmcgui.NOTIFICATION_INFO, time)

def kodi_notify_warn(text, title = 'Advanced Emulator Launcher warning', time = 7000):
    dialog = xbmcgui.Dialog()
    dialog.notification(title, text, xbmcgui.NOTIFICATION_WARNING, time)

#
# Do not use this function much because it is the same icon as when Python fails, and that may confuse the user.
#
def kodi_notify_error(text, title = 'Advanced Emulator Launcher error', time = 7000):
    dialog = xbmcgui.Dialog()
    dialog.notification(title, text, xbmcgui.NOTIFICATION_ERROR, time)

def kodi_busydialog_ON():
    xbmc.executebuiltin('ActivateWindow(busydialog)')

def kodi_busydialog_OFF():
    xbmc.executebuiltin('Dialog.Close(busydialog)')

def kodi_refresh_container():
    log_debug('kodi_refresh_container()')
    xbmc.executebuiltin('Container.Refresh')

# -----------------------------------------------------------------------------
# Kodi specific stuff
# -----------------------------------------------------------------------------
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
#
def kodi_get_cached_image(image_path):
    THUMBS_CACHE_PATH = os.path.join(xbmc.translatePath('special://profile/' ), 'Thumbnails')

    # --- Get the Kodi cached image ---
    # This function return the cache file base name
    base_name = xbmc.getCacheThumbName(image_path)
    cache_file_path = os.path.join(THUMBS_CACHE_PATH, base_name[0], base_name)

    return cache_file_path

#
# Updates Kodi image cache for the image provided with the image itself.
# In other words, copies the image into Kodi cache entry for the image itself.
#
# Needles to say, only update image cache if image already was on the cache.
def kodi_update_image_cache(img_path):
    # What if image is not cached?
    cached_thumb = kodi_get_cached_image(img_path)
    log_debug('kodi_update_image_cache()     img_path {0}'.format(img_path))
    log_debug('kodi_update_image_cache() cached_thumb {0}'.format(cached_thumb))

    # For some reason Kodi xbmc.getCacheThumbName() returns a filename ending in TBN.
    # However, images in the cache have the original extension. Replace TBN extension
    # with that of the original image.
    cached_thumb_root, cached_thumb_ext = os.path.splitext(cached_thumb)
    if cached_thumb_ext == '.tbn':
        img_path_root, img_path_ext = os.path.splitext(img_path)
        cached_thumb = cached_thumb.replace('.tbn', img_path_ext)
        log_debug('kodi_update_image_cache() New cached_thumb {0}'.format(cached_thumb))

    # Check if file exists in the cache
    # xbmc.getCacheThumbName() seems to return a cache filename even if the local file does not exist!
    if not os.path.isfile(cached_thumb):
        log_debug('kodi_update_image_cache() Cached image not found. Doing nothing')
        return

    # --- Copy local image into Kodi image cache ---
    # >> See https://docs.python.org/2/library/sys.html#sys.getfilesystemencoding
    log_debug('kodi_update_image_cache() copying {0}'.format(img_path))
    log_debug('kodi_update_image_cache() into    {0}'.format(cached_thumb))
    fs_encoding = sys.getfilesystemencoding()
    decoded_img_path = img_path.decode(fs_encoding, 'ignore')
    decoded_cached_thumb = cached_thumb.decode(fs_encoding, 'ignore')
    try:
        shutil.copy2(decoded_img_path, decoded_cached_thumb)
    except OSError:
        log_kodi_notify_warn('AEL warning', 'Cannot update cached image (OSError)')
        lod_debug()

    # Is this really needed?
    # xbmc.executebuiltin('XBMC.ReloadSkin()')

def kodi_toogle_fullscreen():
    # Frodo and up compatible
    xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Input.ExecuteAction","params":{"action":"togglefullscreen"},"id":"1"}')

def kodi_kodi_read_favourites():
    favourites = []
    fav_names = []
    if os.path.isfile(FAVOURITES_PATH):
        fav_xml = parse(FAVOURITES_PATH)
        fav_doc = fav_xml.documentElement.getElementsByTagName( 'favourite' )
        for count, favourite in enumerate(fav_doc):
            try:
                fav_icon = favourite.attributes[ 'thumb' ].nodeValue
            except:
                fav_icon = "DefaultProgram.png"
            favourites.append((favourite.childNodes[ 0 ].nodeValue.encode('utf8','ignore'),
                               fav_icon.encode('utf8','ignore'),
                               favourite.attributes[ 'name' ].nodeValue.encode('utf8','ignore')))
            fav_names.append(favourite.attributes[ 'name' ].nodeValue.encode('utf8','ignore'))

    return favourites, fav_names
