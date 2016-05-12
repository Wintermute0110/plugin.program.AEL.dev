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

import sys, os, shutil, time, random, hashlib, urlparse

# For xbmc.log(), xbmcgui.Dialog()
try: import xbmc, xbmcgui
except: from standalone import *

# --- Constants ---------------------------------------------------------------
LOG_ERROR   = 0
LOG_WARNING = 1
LOG_INFO    = 2
LOG_VERB    = 3
LOG_DEBUG   = 4

# --- Internal globals --------------------------------------------------------
current_log_level = LOG_INFO

# -----------------------------------------------------------------------------
# Logging functions
# -----------------------------------------------------------------------------
def set_log_level(level):
    global current_log_level

    current_log_level = level

def log_debug(str_text):
    if current_log_level >= LOG_DEBUG:
        xbmc.log("AEL DEBUG: " + str_text)

def log_verb(str_text):
    if current_log_level >= LOG_VERB:
        xbmc.log("AEL VERB : " + str_text)

def log_info(str_text):
    if current_log_level >= LOG_INFO:
        xbmc.log("AEL INFO : " + str_text)

def log_warning(str_text):
    if current_log_level >= LOG_WARNING:
        xbmc.log("AEL WARN : " + str_text)

def log_error(str_text):
    if current_log_level >= LOG_ERROR:
        xbmc.log("AEL ERROR: " + str_text)

#
# Displays a modal dialog with an OK button.
# Dialog can have up to 3 rows of text.
#
def log_kodi_dialog_OK(title, row1, row2='', row3=''):
    dialog = xbmcgui.Dialog()
    dialog.ok(title, row1, row2, row3)

#
# Displays a small box in the low right corner
#
def log_kodi_notify(title, text, time = 5000):
    # --- Old way ---
    # xbmc.executebuiltin("XBMC.Notification(%s,%s,%s,%s)" % (title, text, time, ICON_IMG_FILE_PATH))

    # --- New way ---
    dialog = xbmcgui.Dialog()
    dialog.notification(title, text, xbmcgui.NOTIFICATION_INFO, time)

def log_kodi_notify_warn(title, text, time = 5000):
    dialog = xbmcgui.Dialog()
    dialog.notification(title, text, xbmcgui.NOTIFICATION_WARNING, time)

#
# Do not use this much because it is the same icon as when Python fails, and that may confuse the user.
#
def log_kodi_notify_error(title, text, time = 5000):
    dialog = xbmcgui.Dialog()
    dialog.notification(title, text, xbmcgui.NOTIFICATION_ERROR, time)

# -----------------------------------------------------------------------------
# Miscellaneous stuff
# -----------------------------------------------------------------------------
def text_get_encoding():
    try:
        return sys.getfilesystemencoding()
    except UnicodeEncodeError, UnicodeDecodeError:
        return "utf-8"

def text_clean_ROM_filename(title):
    title = re.sub('\[.*?\]', '', title)
    title = re.sub('\(.*?\)', '', title)
    title = re.sub('\{.*?\}', '', title)
    title = title.replace('_',' ')
    title = title.replace('-',' ')
    title = title.replace(':',' ')
    title = title.replace('.',' ')
    title = title.rstrip()
    return title

def text_ROM_base_filename(filename):
    filename = re.sub('(\[.*?\]|\(.*?\)|\{.*?\})', '', filename)
    filename = re.sub('(\.|-| |_)cd\d+$', '', filename)
    return filename.rstrip()

#
# Get extension of URL. Returns '' if not found.
#
def text_get_URL_extension(url):
    path = urlparse.urlparse(url).path
    ext = os.path.splitext(path)[1]
    
    return ext

#
# Default to .jpg if URL extension cannot be determined
#
def text_get_image_URL_extension(url):
    path = urlparse.urlparse(url).path
    ext = os.path.splitext(path)[1]
    ret = '.jpg' if ext == '' else ext

    return ret

#
# Generates a random an unique MD5 hash and returns a string with the hash
#
def misc_generate_random_SID():
    t1 = time.time()
    t2 = t1 + random.getrandbits(32)
    base = hashlib.md5( str(t1 + t2) )
    sid = base.hexdigest()

    return sid

#
# Full decomposes a file name path or directory into its constituents
# In theory this is indepedent of the operating system.
# Returns a FileName object:
#   F.path        Full path
#   F.path_noext  Full path with no extension
#   F.base        File name with no path
#   F.base_noext  File name with no path and no extension
#   F.ext         File extension
#
class FileName:
    pass

def misc_split_path(f_path):
    F = FileName()

    F.path       = f_path
    (root, ext)  = os.path.splitext(F.path)
    F.path_noext = root
    F.base       = os.path.basename(F.path)
    (root, ext)  = os.path.splitext(F.base)
    F.base_noext = root
    F.ext        = ext

    return F

#
# Get thumb/fanart filenames
# Given
def misc_get_thumb_path_noext(launcher, F):
    thumb_path  = launcher["thumbpath"]
    fanart_path = launcher["fanartpath"]
    # log_debug('misc_get_thumb_path_noext()  thumb_path {}'.format(thumb_path))
    # log_debug('misc_get_thumb_path_noext() fanart_path {}'.format(fanart_path))

    if thumb_path == fanart_path:
        # log_debug('misc_get_thumb_path_noext() Thumbs/Fanarts have the same path')
        tumb_path_noext = os.path.join(thumb_path, F.base_noext + '_thumb')
    else:
        # log_debug('misc_get_thumb_path_noext() Thumbs/Fanarts into different folders')
        tumb_path_noext = os.path.join(thumb_path, F.base_noext)
    # log_debug('misc_get_thumb_path_noext() tumb_path_noext {}'.format(tumb_path_noext))

    return tumb_path_noext

def misc_get_fanart_path_noext(launcher, F):
    thumb_path  = launcher["thumbpath"]
    fanart_path = launcher["fanartpath"]
    # log_debug('misc_get_fanart_path_noext()  thumb_path {}'.format(thumb_path))
    # log_debug('misc_get_fanart_path_noext() fanart_path {}'.format(fanart_path))

    if thumb_path == fanart_path:
        log_debug('misc_get_fanart_path_noext() Thumbs/Fanarts have the same path')
        fanart_path_noext = os.path.join(fanart_path, F.base_noext + '_fanart')
    else:
        log_debug('misc_get_fanart_path_noext() Thumbs/Fanarts into different folders')
        fanart_path_noext = os.path.join(fanart_path, F.base_noext)
    # log_debug('misc_get_fanart_path_noext() fanart_path_noext {}'.format(fanart_path_noext))

    return fanart_path_noext

def misc_look_for_image(image_path_noext, img_exts):
    image_name = ''
    log_debug('Testing image prefix {}'.format(image_path_noext))
    for ext in img_exts:
        test_img = image_path_noext + '.' + ext
        # log_debug('Testing image "{}"'.format(test_img))
        if os.path.isfile(test_img):
            # Optimization Stop loop as soon as an image is found
            image_name = test_img
            log_debug('Found image "{0}"'.format(test_img))
            break

    return image_name

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
    log_debug('kodi_update_image_cache()     img_path = {}'.format(img_path))
    log_debug('kodi_update_image_cache() cached_thumb = {}'.format(cached_thumb))

    # For some reason Kodi xbmc.getCacheThumbName() returns a filename ending in TBN.
    # However, images in the cache have the original extension. Replace TBN extension
    # with that of the original image.
    F_cached = misc_split_path(cached_thumb)
    if F_cached.ext == '.tbn':
        F_img = misc_split_path(img_path)
        cached_thumb = cached_thumb.replace('.tbn', F_img.ext)
        log_debug('kodi_update_image_cache() New cached_thumb name {}'.format(cached_thumb))

    # Check if file exists in the cache
    # xbmc.getCacheThumbName() seems to return a cache filename even if the local file does not exist!
    if not os.path.isfile(cached_thumb):
        log_debug('kodi_update_image_cache() Cached image not found. Doing nothing')
        return

    # --- Copy local image into Kodi image cache ---
    log_debug('kodi_update_image_cache() copying {}'.format(img_path))
    log_debug('kodi_update_image_cache() into    {}'.format(cached_thumb))
    decoded_img_path     = img_path.decode(text_get_encoding(), 'ignore')
    decoded_cached_thumb = cached_thumb.decode(text_get_encoding(), 'ignore')
    try:
        shutil.copy2(decoded_img_path, decoded_cached_thumb)
    except OSError:
        log_kodi_notify_warn('AEL warning', 'Cannot update cached image (OSError)')
        lod_debug()

    # --- Is this really needed? ---
    # xbmc.executebuiltin('XBMC.ReloadSkin()')

def kodi_toogle_fullscreen():
    # Frodo + compatible
    xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Input.ExecuteAction","params":{"action":"togglefullscreen"},"id":"1"}')

def kodi_kodi_read_favourites():
    favourites = []
    fav_names = []
    if os.path.isfile( FAVOURITES_PATH ):
        fav_xml = parse( FAVOURITES_PATH )
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
