# --- Python standard library ---
from __future__ import unicode_literals
import sys, os, shutil, time, random, hashlib, urlparse

# --- Kodi modules ---
try:
    import xbmc, xbmcgui
except:
    from utils_kodi_standalone import *

from utils import *

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

    THUMBS_CACHE_PATH = FileName('special://profile/Thumbnails')

    # --- Get the Kodi cached image ---
    # This function return the cache file base name
    base_name = xbmc.getCacheThumbName(image_path.getOriginalPath())
    cache_file_path = THUMBS_CACHE_PATH.join(base_name[0]).join(base_name)

    return cache_file_path

#
# Updates Kodi image cache for the image provided with the image itself.
# In other words, copies the image into Kodi cache entry for the image itself.
#
# Needles to say, only update image cache if image already was on the cache.
def kodi_update_image_cache(img_path):
    # What if image is not cached?
    cached_thumb = kodi_get_cached_image(img_path)
    log_debug('kodi_update_image_cache()     img_path {0}'.format(img_path.getOriginalPath()))
    log_debug('kodi_update_image_cache() cached_thumb {0}'.format(cached_thumb.getOriginalPath()))

    # For some reason Kodi xbmc.getCacheThumbName() returns a filename ending in TBN.
    # However, images in the cache have the original extension. Replace TBN extension
    # with that of the original image.
    #cached_thumb_root, cached_thumb_ext = os.path.splitext(cached_thumb)
    cached_thumb_ext = cached_thumb.getExt()
    if cached_thumb_ext == '.tbn':
        img_path_ext = img_path.getExt()
        cached_thumb = FileName(cached_thumb.getOriginalPath().replace('.tbn', img_path_ext))
        log_debug('kodi_update_image_cache() New cached_thumb {0}'.format(cached_thumb))

    # Check if file exists in the cache
    # xbmc.getCacheThumbName() seems to return a cache filename even if the local file does not exist!
    if not cached_thumb.isfile():
        log_debug('kodi_update_image_cache() Cached image not found. Doing nothing')
        return

    # --- Copy local image into Kodi image cache ---
    # >> See https://docs.python.org/2/library/sys.html#sys.getfilesystemencoding
    log_debug('kodi_update_image_cache() copying {0}'.format(img_path.getOriginalPath()))
    log_debug('kodi_update_image_cache() into    {0}'.format(cached_thumb.getOriginalPath()))
    try:
        img_path.copy(cached_thumb)
    except OSError:
        log_kodi_notify_warn('AEL warning', 'Cannot update cached image (OSError)')
        lod_debug()

    # Is this really needed?
    # xbmc.executebuiltin('XBMC.ReloadSkin()')