# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher miscellaneous functions
#

# Copyright (c) 2016 Wintermute0110 <wintermute0110@gmail.com>
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

#
# Utility functions which does not depend on Kodi modules (except log_* functions)
#
import sys, os, shutil, time, random, hashlib, urlparse
try:
    from utils_kodi import *
except:
    from utils_kodi_standalone import *

# -------------------------------------------------------------------------------------------------
# Strings and text
# -------------------------------------------------------------------------------------------------
def text_get_encoding():
    try:
        return sys.getfilesystemencoding()
    except UnicodeEncodeError, UnicodeDecodeError:
        return "utf-8"

#
# If max_length == -1 do nothing (no length limit).
#
def text_limit_string(string, max_length):
  if max_length > 5 and len(string) > max_length:
    string = string[0:max_length-3] + '...'

  return string

#
# See http://stackoverflow.com/questions/1091945/what-characters-do-i-need-to-escape-in-xml-documents
#
def text_escape_XML(str):
    str_A = str.replace('"', '&quot;').replace("'", '&apos;').replace('&', '&amp;')

    return str_A.replace('<', '&lt;').replace('>', '&gt;')

def text_unescape_HTML(s):
    s = s.replace('<br />',' ')
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&amp;", "&")
    s = s.replace("&#039;", "'")
    s = s.replace('&quot;', '"')
    s = s.replace('&nbsp;', ' ')
    s = s.replace('&#x26;', '&')
    s = s.replace('&#x27;', "'")

    return s

# -------------------------------------------------------------------------------------------------
# ROM name cleaning and formatting
# -------------------------------------------------------------------------------------------------
#
# This function is used to clean the ROM name to be used as search string for the scraper
#
# Cleans ROM tags: [BIOS], (Europe), (Rev A), ...
# Substitutes some characters by spaces
#
def text_clean_ROM_name_for_scrapping(title):
    title = re.sub('\[.*?\]', '', title)
    title = re.sub('\(.*?\)', '', title)
    title = re.sub('\{.*?\}', '', title)
    
    title = title.replace('_',' ')
    title = title.replace('-',' ')
    title = title.replace(':',' ')
    title = title.replace('.',' ')
    title = title.rstrip()
    
    return title

#
#
#
def text_ROM_base_filename(filename):
    filename = re.sub('(\[.*?\]|\(.*?\)|\{.*?\})', '', filename)
    filename = re.sub('(\.|-| |_)cd\d+$', '', filename)

    return filename.rstrip()

#
# Format ROM file name when scraping is disabled
#
def text_ROM_title_format(title, clean_tags, format_title):
    if clean_tags:
        title = re.sub('\[.*?\]', '', title)
        title = re.sub('\(.*?\)', '', title)
        title = re.sub('\{.*?\}', '', title)
    new_title = title.rstrip()
    
    if format_title:
        if (title.startswith("The ")): new_title = title.replace("The ","", 1)+", The"
        if (title.startswith("A ")): new_title = title.replace("A ","", 1)+", A"
        if (title.startswith("An ")): new_title = title.replace("An ","", 1)+", An"
    else:
        if (title.endswith(", The")): new_title = "The "+"".join(title.rsplit(", The", 1))
        if (title.endswith(", A")): new_title = "A "+"".join(title.rsplit(", A", 1))
        if (title.endswith(", An")): new_title = "An "+"".join(title.rsplit(", An", 1))

    return new_title

# -------------------------------------------------------------------------------------------------
# URLs
# -------------------------------------------------------------------------------------------------
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

# -------------------------------------------------------------------------------------------------
# Filenames
# -------------------------------------------------------------------------------------------------
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

# -------------------------------------------------------------------------------------------------
# Misc stuff
# -------------------------------------------------------------------------------------------------
#
# Generates a random an unique MD5 hash and returns a string with the hash
#
def misc_generate_random_SID():
    t1 = time.time()
    t2 = t1 + random.getrandbits(32)
    base = hashlib.md5( str(t1 + t2) )
    sid = base.hexdigest()

    return sid
