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

import sys, os, shutil, time, random, hashlib

# For xbmc.log(), xbmcgui.Dialog()
import xbmc, xbmcgui

# --- Constants ---------------------------------------------------------------
LOG_ERROR   = 0
LOG_WARNING = 1
LOG_INFO    = 2
LOG_VERB    = 3
LOG_DEBUG   = 4

# --- Internal globals --------------------------------------------------------
current_log_level = LOG_INFO

# --- Logging functions -------------------------------------------------------
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

# --- Kodi image cache -------------------------------------------------------
THUMBS_CACHE_PATH = os.path.join(xbmc.translatePath("special://profile/" ), "Thumbnails")

def get_encoding():
    try:
        return sys.getfilesystemencoding()
    except UnicodeEncodeError, UnicodeDecodeError:
        return "utf-8"

def get_cached_thumb(path1, path2, SPLIT=False):
    # get the locally cached thumb
    filename = xbmc.getCacheThumbName( path1 )
    if SPLIT:
        thumb = os.path.join( filename[ 0 ], filename )
    else:
        thumb = filename
    return os.path.join( path2, thumb )

def get_cached_covers_thumb(strPath):
    return get_cached_thumb(strPath, THUMBS_CACHE_PATH, True)

def update_kodi_image_cache(file_path):
    cached_thumb = get_cached_covers_thumb(file_path).replace("tbn" , os.path.splitext(file_path)[-1][1:4])
    try:
        shutil.copy2(file_path.decode(get_encoding(), 'ignore'), cached_thumb.decode(get_encoding(), 'ignore'))
    except OSError:
        log_kodi_notify_warn('AEL warning', 'Cannot update cached image')
    xbmc.executebuiltin("XBMC.ReloadSkin()")

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

def kodi_toogle_fullscreen():
    # Frodo & + compatible
    xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Input.ExecuteAction","params":{"action":"togglefullscreen"},"id":"1"}')

#
# Generates a random an unique MD5 hash and returns a string with the hash
#
def misc_generate_random_SID():
    t1 = time.time()
    t2 = t1 + random.getrandbits(32)
    base = hashlib.md5( str(t1 + t2) )
    sid = base.hexdigest()

    return sid

def get_kodi_favourites_list():
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
