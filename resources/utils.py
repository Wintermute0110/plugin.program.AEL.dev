# -*- coding: utf-8 -*-
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
import sys, os, shutil, time, random, hashlib, urlparse, re, string
try:
    from utils_kodi import *
except:
    from utils_kodi_standalone import *

# -------------------------------------------------------------------------------------------------
# Strings and text
# -------------------------------------------------------------------------------------------------
#
# If max_length == -1 do nothing (no length limit).
#
def text_limit_string(string, max_length):
  if max_length > 5 and len(string) > max_length:
    string = string[0:max_length-3] + '...'

  return string

# Some XML encoding of special characters:
#   {'\n': '&#10;', '\r': '&#13;', '\t':'&#9;'}
#
# See http://stackoverflow.com/questions/1091945/what-characters-do-i-need-to-escape-in-xml-documents
# See https://wiki.python.org/moin/EscapingXml
# See https://github.com/python/cpython/blob/master/Lib/xml/sax/saxutils.py
# See http://stackoverflow.com/questions/2265966/xml-carriage-return-encoding
#
def text_escape_XML(data_str):
    # Ampersand MUST BE replaced FIRST
    data_str = data_str.replace('&', '&amp;')
    data_str = data_str.replace('>', '&gt;')
    data_str = data_str.replace('<', '&lt;')

    data_str = data_str.replace("'", '&apos;')
    data_str = data_str.replace('"', '&quot;')
    
    # --- Unprintable characters ---
    data_str = data_str.replace('\n', '&#10;')
    data_str = data_str.replace('\r', '&#13;')
    data_str = data_str.replace('\t', '&#9;')

    return data_str

def text_unescape_XML(data_str):
    data_str = data_str.replace('&quot;', '"')
    data_str = data_str.replace('&apos;', "'")

    data_str = data_str.replace('&lt;', '<')
    data_str = data_str.replace('&gt;', '>')
    # Ampersand MUST BE replaced LAST
    data_str = data_str.replace('&amp;', '&')
    
    # --- Unprintable characters ---
    data_str = data_str.replace('&#10;', '\n')
    data_str = data_str.replace('&#13;', '\r')
    data_str = data_str.replace('&#9;', '\t')
    
    return data_str

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

def text_dump_str_to_file(full_string, filename):
    file_obj = open(filename, 'wt')
    file_obj.write(full_string)
    file_obj.close()

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

# def text_ROM_base_filename(filename):
#     filename = re.sub('(\[.*?\]|\(.*?\)|\{.*?\})', '', filename)
#     filename = re.sub('(\.|-| |_)cd\d+$', '', filename)
#
#     return filename.rstrip()

#
# Format ROM file name when scraping is disabled.
# 1) Remove No-Intro/TOSEC tags (), [], {}
#
def text_ROM_title_format(title, clean_tags):
    if clean_tags:
        title = re.sub('\[.*?\]', '', title)
        title = re.sub('\(.*?\)', '', title)
        title = re.sub('\{.*?\}', '', title)
    new_title = title.rstrip()
    
    # if format_title:
    #     if (title.startswith("The ")): new_title = title.replace("The ","", 1)+", The"
    #     if (title.startswith("A ")): new_title = title.replace("A ","", 1)+", A"
    #     if (title.startswith("An ")): new_title = title.replace("An ","", 1)+", An"
    # else:
    #     if (title.endswith(", The")): new_title = "The "+"".join(title.rsplit(", The", 1))
    #     if (title.endswith(", A")): new_title = "A "+"".join(title.rsplit(", A", 1))
    #     if (title.endswith(", An")): new_title = "An "+"".join(title.rsplit(", An", 1))

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
#   F.path        Full path                                     /home/Wintermute/Sonic.zip
#   F.path_noext  Full path with no extension                   /home/Wintermute/Sonic
#   F.dirname     Directory name of file. Does not end in '/'   /home/Wintermute
#   F.base        File name with no path                        Sonic.zip
#   F.base_noext  File name with no path and no extension       Sonic
#   F.ext         File extension                                .zip
#
class FileName:
    pass

def misc_split_path(f_path):
    F = FileName()

    F.path       = f_path
    (root, ext)  = os.path.splitext(F.path)
    F.path_noext = root
    F.dirname    = os.path.dirname(f_path)
    F.base       = os.path.basename(F.path)
    (root, ext)  = os.path.splitext(F.base)
    F.base_noext = root
    F.ext        = ext

    return F

#
# Given the image path with no extension and a list of file extensions search for a file.
#
def misc_look_for_file(file_path_noext, file_exts):
    file_path = ''
    log_debug('Testing file_path_noext {0}'.format(file_path_noext))
    for ext in file_exts:
        test_file = file_path_noext + '.' + ext
        # log_debug('Testing file "{0}"'.format(test_file))
        if os.path.isfile(test_file):
            # Optimization Stop loop as soon as an image is found
            file_path = test_file
            log_debug('Found file "{0}"'.format(test_file))
            break

    return file_path

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

# -------------------------------------------------------------------------------------------------
# Utilities to test scrapers
# -------------------------------------------------------------------------------------------------
ID_LENGTH     = 60
NAME_LENGTH   = 60
GENRE_LENGTH  = 20
YEAR_LENGTH   = 4
STUDIO_LENGTH = 20
PLOT_LENGTH   = 70
URL_LENGTH    = 70

def print_scraper_list(scraper_obj_list):
    print('Short name        Fancy Name')
    print('----------------  ---------------------------------')
    for scraper_obj in scraper_obj_list:
        print('{0:10s}  {1:}'.format(scraper_obj.name.rjust(16), scraper_obj.fancy_name))

# PUT functions to print things returned by Scraper object (which are common to all scrapers)
# into util.py, to be resused by all scraper tests.
def print_games_search(results):
    print('\nFound {0} game/s'.format(len(results)))
    print("{0} {1}".format('Display name'.ljust(NAME_LENGTH), 'Id'.ljust(ID_LENGTH)))
    print("{0} {1}".format('-'*NAME_LENGTH, '-'*ID_LENGTH))
    for game in results:
        display_name = text_limit_string(game['display_name'], NAME_LENGTH)
        id           = text_limit_string(game['id'], ID_LENGTH)
        print("{0} {1}".format(display_name.ljust(NAME_LENGTH), id.ljust(ID_LENGTH)))
    print('')

def print_game_metadata(results, scraperObj):
    # --- Get metadata of first game ---
    if results:
        metadata = scraperObj.get_metadata(results[0])

        title  = text_limit_string(metadata['title'], NAME_LENGTH)
        genre  = text_limit_string(metadata['genre'], GENRE_LENGTH)
        year   = metadata['year']
        studio = text_limit_string(metadata['studio'], STUDIO_LENGTH)
        plot   = text_limit_string(metadata['plot'], PLOT_LENGTH)
        print('\nDisplaying metadata for title "{0}"'.format(title))
        print("{0} {1} {2} {3} {4}".format('Title'.ljust(NAME_LENGTH), 'Genre'.ljust(GENRE_LENGTH), 
                                      'Year'.ljust(YEAR_LENGTH), 'Studio'.ljust(STUDIO_LENGTH), 'Plot'.ljust(PLOT_LENGTH)))
        print("{0} {1} {2} {3} {4}".format('-'*NAME_LENGTH, '-'*GENRE_LENGTH, '-'*YEAR_LENGTH, 
                                      '-'*STUDIO_LENGTH, '-'*PLOT_LENGTH))
        print("{0} {1} {2} {3} {4}".format(title.ljust(NAME_LENGTH), genre.ljust(GENRE_LENGTH), year.ljust(YEAR_LENGTH), 
                                      studio.ljust(STUDIO_LENGTH), plot.ljust(PLOT_LENGTH)))

def print_game_image_list(results, scraperObj):
    # --- Get image list of first game ---
    if results:
        image_list = scraperObj.get_images(results[0])
        print('\nFound {0} image/s'.format(len(image_list)))
        print("{0} {1} {2}".format('Display name'.ljust(NAME_LENGTH), 'URL'.ljust(URL_LENGTH), 'Display URL'.ljust(URL_LENGTH)))
        print("{0} {1} {2}".format('-'*NAME_LENGTH, '-'*URL_LENGTH, '-'*URL_LENGTH))
        for image in image_list:
            display_name  = text_limit_string(image['name'], NAME_LENGTH)
            url           = text_limit_string(image['URL'], URL_LENGTH)
            disp_url      = text_limit_string(image['disp_URL'], URL_LENGTH)
            print("{0} {1} {2}".format(display_name.ljust(NAME_LENGTH), url.ljust(URL_LENGTH), disp_url.ljust(URL_LENGTH)))
