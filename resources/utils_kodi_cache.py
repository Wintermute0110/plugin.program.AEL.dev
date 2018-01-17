# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher
# Copyright (c) 2016-2018 Wintermute0110 <wintermute0110@gmail.com>
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

# -------------------------------------------------------------------------------------------------
# Kodi image cache utilities
# -------------------------------------------------------------------------------------------------
# --- Python compiler flags ---
from __future__ import unicode_literals

# --- Python standard library ---
import sys, os, shutil, time, random, hashlib, urlparse

# --- Kodi modules ---
try:
    import xbmc, xbmcgui
except:
    from utils_kodi_standalone import *

from utils import *

#
# Kodi image cache
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
# Gets where an image is located in Kodi image cache.
# image_path is a Unicode string.
# cache_file_path is a Unicode string.
#
def kodi_get_cached_image_FN(image_FN):
    THUMBS_CACHE_PATH_FN = FileName('special://profile/Thumbnails')
    # >> This function return the cache file base name
    base_name = xbmc.getCacheThumbName(image_FN.getOriginalPath())
    cache_file_path = THUMBS_CACHE_PATH_FN.pjoin(base_name[0]).pjoin(base_name)

    return cache_file_path

#
# Updates Kodi image cache for the image provided in img_path.
# In other words, copies the image img_path into Kodi cache entry.
# Needles to say, only update image cache if image already was on the cache.
# img_path is a Unicode string
#
def kodi_update_image_cache(img_path_FN):
    # What if image is not cached?
    cached_thumb_FN = kodi_get_cached_image_FN(img_path)
    log_debug('kodi_update_image_cache()       img_path_FN OP {0}'.format(img_path_FN.getOriginalPath()))
    log_debug('kodi_update_image_cache()   cached_thumb_FN OP {0}'.format(cached_thumb_FN.getOriginalPath()))

    # For some reason xbmc.getCacheThumbName() returns a filename ending in TBN.
    # However, images in the cache have the original extension. Replace the TBN extension
    # with that of the original image.
    cached_thumb_ext = cached_thumb_FN.getExt()
    if cached_thumb_ext == '.tbn':
        img_path_ext = img_path_FN.getExt()
        cached_thumb_FN = FileName(cached_thumb_FN.getOriginalPath().replace('.tbn', img_path_ext))
        log_debug('kodi_update_image_cache() U cached_thumb_FN OP {0}'.format(cached_thumb.getOriginalPath()))

    # --- Check if file exists in the cache ---
    # xbmc.getCacheThumbName() seems to return a filename even if the local file does not exist!
    if not cached_thumb_FN.isfile():
        log_debug('kodi_update_image_cache() Cached image not found. Doing nothing')
        return

    # --- Copy local image into Kodi image cache ---
    # >> See https://docs.python.org/2/library/sys.html#sys.getfilesystemencoding
    log_debug('kodi_update_image_cache() Image found in cache. Updating Kodi image cache')
    log_debug('kodi_update_image_cache() copying {0}'.format(img_path_FN.getOriginalPath()))
    log_debug('kodi_update_image_cache() into    {0}'.format(cached_thumb_FN.getOriginalPath()))
    # fs_encoding = sys.getfilesystemencoding()
    # log_debug('kodi_update_image_cache() fs_encoding = "{0}"'.format(fs_encoding))
    # encoded_img_path = img_path.encode(fs_encoding, 'ignore')
    # encoded_cached_thumb = cached_thumb.encode(fs_encoding, 'ignore')
    try:
        # shutil.copy2(encoded_img_path, encoded_cached_thumb)
        img_path_FN.copy(cached_thumb_FN)
    except OSError:
        log_kodi_notify_warn('AEL warning', 'Cannot update cached image (OSError)')
        lod_debug('Cannot update cached image (OSError)')
