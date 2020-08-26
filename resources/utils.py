# -*- coding: utf-8 -*-

# Advanced Emulator Launcher miscellaneous functions

# Copyright (c) 2016-2019 Wintermute0110 <wintermute0110@gmail.com>
# Portions (c) 2010-2015 Angelscry and others
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# --- Module documentation ---
# 1. This function contains utilities that do not depend on Kodi modules and utilities that
#    depend on Kodi modules. Appropiate replacements are provided when the Kodi modules are
#    not available, for example when running this file with the standard Python interpreter and
#    not Kodi Python interpreter.
#
# 2. Filesystem access utilities are located in this file. Filesystem can use the Python
#    standard library or Kodi Virtual FileSystem library if available.
#
# 3. utils.py must not depend on any other AEL module to avoid circular dependencies, with the
#    exception of constants.py
#
# 4. Functions starting with _ are internal module functions not to be called externally.
#

# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division
import abc
# NOTE binascii must not be used! See https://docs.python.org/2/library/binascii.html
import binascii
import base64
# from base64 import b64decode
# from base64 import b64encode
import errno
import fnmatch
import hashlib
import json
import collections
import sys
import os
import pprint
import random
import re
import shutil
import string
import sys
import time
import zlib

from HTMLParser import HTMLParser
from urlparse import urlparse
from datetime import timedelta
from datetime import datetime

# Python 3
# from html.parser import HTMLParser
# from urllib.parse import urlparse

# --- Python standard library named imports ---
import xml.etree.ElementTree as ET

# NOTE OpenSSL library will be included in Kodi M****
#      Search documentation about this in Garbear's github repo.
try:
    from OpenSSL import crypto, SSL
    UTILS_OPENSSL_AVAILABLE = True
except:
    UTILS_OPENSSL_AVAILABLE = False

try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
    UTILS_CRYPTOGRAPHY_AVAILABLE = True
except:
    UTILS_CRYPTOGRAPHY_AVAILABLE = False

try:
    from Crypto.PublicKey import RSA
    from Crypto.Signature import PKCS1_v1_5
    from Crypto.Hash import SHA256
    from Crypto.Cipher import AES
    from Crypto.Random import get_random_bytes
    UTILS_PYCRYPTO_AVAILABLE = True
except:
    UTILS_PYCRYPTO_AVAILABLE = False

# --- Kodi modules ---
try:
    import xbmc
    import xbmcaddon
    import xbmcgui
    import xbmcplugin
    import xbmcvfs
    UTILS_KODI_RUNTIME_AVAILABLE = True
except:
    UTILS_KODI_RUNTIME_AVAILABLE = False

# --- AEL modules ---
from resources.constants import *

# -------------------------------------------------------------------------------------------------
# A universal AEL error reporting exception
# This exception is raised to report errors in the GUI.
# Unhandled exceptions must not raise AddonException() so the addon crashes and the traceback is printed
# in the Kodi log file.
# -------------------------------------------------------------------------------------------------
# >> Top-level GUI code looks like this
# try:
#     autoconfig_export_category(category, export_FN)
# except Addon_Error as E:
#     kodi_notify_warn('{0}'.format(E))
# else:
#     kodi_notify('Exported Category "{0}" XML config'.format(category['m_name']))
#
# >> Low-level code looks like this
# def autoconfig_export_category(category, export_FN):
#     try:
#         do_something_that_may_fail()
#     except OSError:
#         log_error('(OSError) Cannot write {0} file'.format(export_FN.getBase()))
#         # >> Message to be printed in the GUI
#         raise AddonException('Error writing file (OSError)')
#
class AddonException(Exception):
    def __init__(self, err_str):
        self.err_str = err_str

    def __str__(self):
        return self.err_str

# #################################################################################################
# #################################################################################################
# Standard Python utilities
# #################################################################################################
# #################################################################################################

# --- Determine interpreter running platform ---
# Cache all possible platform values in global variables for maximum speed.
# See http://stackoverflow.com/questions/446209/possible-values-from-sys-platform
cached_sys_platform = sys.platform
def _aux_is_android():
    if not cached_sys_platform.startswith('linux'): return False
    return 'ANDROID_ROOT' in os.environ or 'ANDROID_DATA' in os.environ or 'XBMC_ANDROID_APK' in os.environ

is_windows_bool = cached_sys_platform == 'win32' or cached_sys_platform == 'win64' or cached_sys_platform == 'cygwin'
is_osx_bool     = cached_sys_platform.startswith('darwin')
is_android_bool = _aux_is_android()
is_linux_bool   = cached_sys_platform.startswith('linux') and not is_android_bool

def is_windows():
    return is_windows_bool

def is_osx():
    return is_osx_bool

def is_android():
    return is_android_bool

def is_linux():
    return is_linux_bool

# -------------------------------------------------------------------------------------------------
# Strings and text
# -------------------------------------------------------------------------------------------------
# Limits the length of a string for printing. If max_length == -1 do nothing (string has no
# length limit). The string is trimmed by cutting it and adding three dots ... at the end.
# Including these three dots the length of the returned string is max_length or less.
# Example: 'asdfasdfdasf' -> 'asdfsda...'
#
# @param string: [str] String to be trimmed.
# @param max_length: [int] Integer maximum length of the string.
# @return [str] Trimmed string.
def text_limit_string(string, max_length):
    if max_length > 5 and len(string) > max_length:
        string = string[0:max_length-3] + '...'
    return string

# Given a text clean it so the cleaned string can be used as a filename.
# 1) Convert any non-printable character into ' '
# 2) Remove special chars
# 3) (DISABLED) Convert spaces ' ' into '_'
def text_str_to_filename_str(title_str):
    not_valid_chars = '\',"*/:<>?\\|'
    cleaned_str_1 = ''.join([i if i in string.printable else ' ' for i in title_str])
    cleaned_str_2 = ''.join([i if i not in not_valid_chars else '' for i in cleaned_str_1])
    #cleaned_str_3 = cleaned_str_2.replace(' ', '_')
    return cleaned_str_2

#
# Writes a XML text tag line, indented 2 spaces by default.
# Both tag_name and tag_text must be Unicode strings.
# Returns an Unicode string.
#
def text_XML_line(tag_name, tag_text, num_spaces = 2):
    if tag_text:
        tag_text = text_escape_XML(tag_text)
        line = '{0}<{1}>{2}</{3}>\n'.format(' ' * num_spaces, tag_name, tag_text, tag_name)
    else:
        # >> Empty tag
        line = '{0}<{1} />\n'.format(' ' * num_spaces, tag_name)

    return line

def text_str_2_Uni(string):
    # print(type(string))
    if type(string).__name__ == 'unicode':
        unicode_str = string
    elif type(string).__name__ == 'str':
        unicode_str = string.decode('utf-8', errors = 'replace')
    else:
        print('TypeError: ' + type(string).__name__)
        raise TypeError
    # print(type(unicode_str))

    return unicode_str

def text_remove_Kodi_color_tags(s):
    s = re.sub('\[COLOR \S+?\]', '', s)
    s = re.sub('\[color \S+?\]', '', s)
    s = s.replace('[/color]', '')
    s = s.replace('[/COLOR]', '')

    return s

# Renders a list of list of strings table into a CSV list of strings.
# The list of strings must be joined with '\n'.join()
def text_render_table_CSV(table_str):
    rows = len(table_str)
    cols = len(table_str[0])
    table_str_list = []
    for i in range(1, rows):
        row_str = ''
        for j in range(cols):
            if j < cols - 1:
                row_str += '{},'.format(table_str[i][j])
            else:
                row_str += '{}'.format(table_str[i][j])
        table_str_list.append(row_str)

    return table_str_list

# Returns a list of strings that must be joined with '\n'.join()
#
# First row            column aligment 'right' or 'left'
# Second row           column titles
# Third and next rows  table data
#
# Input:
# table_str = [
#     ['left', 'left', 'left'],
#     ['Platform', 'Parents', 'Clones'],
#     ['', '', ''],
# ]
#
# Output:
#
def text_render_table(table_str, trim_Kodi_colours = False):
    rows = len(table_str)
    cols = len(table_str[0])

    # Remove Kodi tags [COLOR string] and [/COLOR]
    if trim_Kodi_colours:
        new_table_str = []
        for i in range(rows):
            new_table_str.append([])
            for j in range(cols):
                s = text_remove_Kodi_color_tags(table_str[i][j])
                new_table_str[i].append(s)
        table_str = new_table_str

    # Determine sizes and padding.
    # Ignore row 0 when computing sizes.
    table_str_list = []
    col_sizes = text_get_table_str_col_sizes(table_str, rows, cols)
    col_padding = table_str[0]

    # --- Table header ---
    row_str = ''
    for j in range(cols):
        if j < cols - 1:
            row_str += text_print_padded_left(table_str[1][j], col_sizes[j]) + '  '
        else:
            row_str += text_print_padded_left(table_str[1][j], col_sizes[j])
    table_str_list.append(row_str)
    # Table line -----
    total_size = sum(col_sizes) + 2*(cols-1)
    table_str_list.append('{0}'.format('-' * total_size))

    # --- Data rows ---
    for i in range(2, rows):
        row_str = ''
        for j in range(cols):
            if j < cols - 1:
                if col_padding[j] == 'right':
                    row_str += text_print_padded_right(table_str[i][j], col_sizes[j]) + '  '
                else:
                    row_str += text_print_padded_left(table_str[i][j], col_sizes[j]) + '  '
            else:
                if col_padding[j] == 'right':
                    row_str += text_print_padded_right(table_str[i][j], col_sizes[j])
                else:
                    row_str += text_print_padded_left(table_str[i][j], col_sizes[j])
        table_str_list.append(row_str)

    return table_str_list

# First row             column aligment 'right' or 'left'
# Second and next rows  table data
# Input:
# table_str = [
#     ['left', 'left', 'left'],
#     ['Platform', 'Parents', 'Clones'],
#     ['', '', ''],
# ]
#
# Output:
#
def text_render_table_NO_HEADER(table_str, trim_Kodi_colours = False):
    rows = len(table_str)
    cols = len(table_str[0])

    # Remove Kodi tags [COLOR string] and [/COLOR]
    # BUG Currently this code removes all the colour tags so the table is rendered
    #     with no colours.
    # NOTE To render tables with colours is more difficult than this... 
    #      All the paddings changed. I will left this for the future.
    if trim_Kodi_colours:
        new_table_str = []
        for i in range(rows):
            new_table_str.append([])
            for j in range(cols):
                s = text_remove_Kodi_color_tags(table_str[i][j])
                new_table_str[i].append(s)
        table_str = new_table_str

    # Ignore row 0 when computing sizes.
    table_str_list = []
    col_sizes = text_get_table_str_col_sizes(table_str, rows, cols)
    col_padding = table_str[0]

    # --- Data rows ---
    for i in range(1, rows):
        row_str = ''
        for j in range(cols):
            if j < cols - 1:
                if col_padding[j] == 'right':
                    row_str += text_print_padded_right(table_str[i][j], col_sizes[j]) + '  '
                else:
                    row_str += text_print_padded_left(table_str[i][j], col_sizes[j]) + '  '
            else:
                if col_padding[j] == 'right':
                    row_str += text_print_padded_right(table_str[i][j], col_sizes[j])
                else:
                    row_str += text_print_padded_left(table_str[i][j], col_sizes[j])
        table_str_list.append(row_str)

    return table_str_list

#
# Removed Kodi colour tags before computing size (substitute by ''):
#   A) [COLOR skyblue]
#   B) [/COLOR]
#
def text_get_table_str_col_sizes(table_str, rows, cols):
    col_sizes = [0] * cols
    for j in range(cols):
        col_max_size = 0
        for i in range(1, rows):
            cell_str = re.sub(r'\[COLOR \w+?\]', '', table_str[i][j])
            cell_str = re.sub(r'\[/COLOR\]', '', cell_str)
            str_size = len('{0}'.format(cell_str))
            if str_size > col_max_size: col_max_size = str_size
        col_sizes[j] = col_max_size

    return col_sizes

def text_str_list_size(str_list):
    max_str_size = 0
    for str_item in str_list:
        str_size = len('{}'.format(str_item))
        if str_size > max_str_size: max_str_size = str_size

    return max_str_size

def text_str_dic_max_size(dictionary_list, dic_key, title_str = ''):
    max_str_size = 0
    for item in dictionary_list:
        str_size = len('{0}'.format(item[dic_key]))
        if str_size > max_str_size: max_str_size = str_size
    if title_str:
        str_size = len(title_str)
        if str_size > max_str_size: max_str_size = str_size

    return max_str_size

def text_print_padded_left(str, str_max_size):
    formatted_str = '{0}'.format(str)
    padded_str =  formatted_str + ' ' * (str_max_size - len(formatted_str))

    return padded_str

def text_print_padded_right(str, str_max_size):
    formatted_str = '{0}'.format(str)
    padded_str = ' ' * (str_max_size - len(formatted_str)) + formatted_str

    return padded_str

def text_remove_color_tags_slist(slist):
    # Iterate list of strings and remove the following tags
    # 1) [COLOR colorname]
    # 2) [/COLOR]
    #
    # Modifying list already seen is OK when iterating the list. Do not change the size of the
    # list when iterating.
    for i, s in enumerate(slist):
        modified = False
        s_temp = s

        # >> Remove [COLOR colorname]
        m = re.search('(\[COLOR \w+?\])', s_temp)
        if m:
            s_temp = s_temp.replace(m.group(1), '')
            modified = True

        # >> Remove [/COLOR]
        if s_temp.find('[/COLOR]') >= 0:
            s_temp = s_temp.replace('[/COLOR]', '')
            modified = True

        # >> Update list
        if modified:
            slist[i] = s_temp

# Some XML encoding of special characters:
#   {'\n': '&#10;', '\r': '&#13;', '\t':'&#9;'}
#
# See http://stackoverflow.com/questions/1091945/what-characters-do-i-need-to-escape-in-xml-documents
# See https://wiki.python.org/moin/EscapingXml
# See https://github.com/python/cpython/blob/master/Lib/xml/sax/saxutils.py
# See http://stackoverflow.com/questions/2265966/xml-carriage-return-encoding
#
def text_escape_XML(data_str):

    if not isinstance(data_str, basestring):
        data_str = str(data_str)

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

#
# Unquote an HTML string. Replaces %xx with Unicode characters.
# http://www.w3schools.com/tags/ref_urlencode.asp
#
def text_decode_HTML(s):
    s = s.replace('%25', '%') # >> Must be done first
    s = s.replace('%20', ' ')
    s = s.replace('%23', '#')
    s = s.replace('%26', '&')
    s = s.replace('%28', '(')
    s = s.replace('%29', ')')
    s = s.replace('%2C', ',')
    s = s.replace('%2F', '/')
    s = s.replace('%3B', ';')
    s = s.replace('%3A', ':')
    s = s.replace('%3D', '=')
    s = s.replace('%3F', '?')

    return s

#
# Decodes HTML <br> tags and HTML entities (&xxx;) into Unicode characters.
# See https://stackoverflow.com/questions/2087370/decode-html-entities-in-python-string
#
def text_unescape_HTML(s):
    __debug_text_unescape_HTML = False
    if __debug_text_unescape_HTML:
        log_debug('text_unescape_HTML() input  "{0}"'.format(s))

    # --- Replace HTML tag characters by their Unicode equivalent ---
    s = s.replace('<br>',   '\n')
    s = s.replace('<br/>',  '\n')
    s = s.replace('<br />', '\n')

    # --- HTML entities ---
    # s = s.replace('&lt;',   '<')
    # s = s.replace('&gt;',   '>')
    # s = s.replace('&quot;', '"')
    # s = s.replace('&nbsp;', ' ')
    # s = s.replace('&copy;', '©')
    # s = s.replace('&amp;',  '&') # >> Must be done last

    # --- HTML Unicode entities ---
    # s = s.replace('&#039;', "'")
    # s = s.replace('&#149;', "•")
    # s = s.replace('&#x22;', '"')
    # s = s.replace('&#x26;', '&')
    # s = s.replace('&#x27;', "'")

    # s = s.replace('&#x101;', "ā")
    # s = s.replace('&#x113;', "ē")
    # s = s.replace('&#x12b;', "ī")
    # s = s.replace('&#x12B;', "ī")
    # s = s.replace('&#x14d;', "ō")
    # s = s.replace('&#x14D;', "ō")
    # s = s.replace('&#x16b;', "ū")
    # s = s.replace('&#x16B;', "ū")

    # >> Use HTMLParser module to decode HTML entities.
    s = HTMLParser().unescape(s)

    if __debug_text_unescape_HTML:
        log_debug('text_unescape_HTML() output "{0}"'.format(s))

    return s

# Remove HTML tags from string.
def text_remove_HTML_tags(s):
    p = re.compile('<.*?>')
    s = p.sub('', s)

    return s

def text_unescape_and_untag_HTML(s):
    s = text_unescape_HTML(s)
    s = text_remove_HTML_tags(s)

    return s

# See https://www.freeformatter.com/json-escape.html
# The following characters are reserved in JSON and must be properly escaped to be used in strings:
#   Backspace is replaced with \b
#   Form feed is replaced with \f
#   Newline is replaced with \n
#   Carriage return is replaced with \r
#   Tab is replaced with \t
#   Double quote is replaced with \"
#   Backslash is replaced with \\
#
def text_escape_JSON(s):
    s = s.replace('\\', '\\\\') # >> Must be done first
    s = s.replace('"', '\\"')

    return s

def text_translate(id):
    addon = xbmcaddon.Addon()
    return addon.getLocalizedString(id)
    
def text_dump_str_to_file(filename, full_string):
    file_obj = open(filename, 'w')
    file_obj.write(full_string.encode('utf-8'))
    file_obj.close()

# -------------------------------------------------------------------------------------------------
# ROM name cleaning and formatting
# -------------------------------------------------------------------------------------------------
#
# This function is used to clean the ROM name to be used as search string for the scraper.
#
# 1) Cleans ROM tags: [BIOS], (Europe), (Rev A), ...
# 2) Substitutes some characters by spaces
#
def text_format_ROM_name_for_scraping(title):
    title = re.sub('\[.*?\]', '', title)
    title = re.sub('\(.*?\)', '', title)
    title = re.sub('\{.*?\}', '', title)
    
    title = title.replace('_', ' ')
    title = title.replace('-', ' ')
    title = title.replace(':', '')
    title = title.replace('.', ' ')
    title = title.strip()

    return title

#
# Format ROM file name when scraping is disabled.
# 1) Remove No-Intro/TOSEC tags (), [], {} at the end of the file
#
# title      -> Unicode string
# clean_tags -> bool
#
# Returns a Unicode string.
#
def text_format_ROM_title(title, clean_tags):
    #
    # Regexp to decompose a string in tokens
    #
    if clean_tags:
        reg_exp = '\[.+?\]\s?|\(.+?\)\s?|\{.+?\}|[^\[\(\{]+'
        tokens = re.findall(reg_exp, title)
        str_list = []
        for token in tokens:
            stripped_token = token.strip()
            if (stripped_token[0] == '[' or stripped_token[0] == '(' or stripped_token[0] == '{') and \
               stripped_token != '[BIOS]':
                continue
            str_list.append(stripped_token)
        cleaned_title = ' '.join(str_list)
    else:
        cleaned_title = title

    # if format_title:
    #     if (title.startswith("The ")): new_title = title.replace("The ","", 1)+", The"
    #     if (title.startswith("A ")): new_title = title.replace("A ","", 1)+", A"
    #     if (title.startswith("An ")): new_title = title.replace("An ","", 1)+", An"
    # else:
    #     if (title.endswith(", The")): new_title = "The "+"".join(title.rsplit(", The", 1))
    #     if (title.endswith(", A")): new_title = "A "+"".join(title.rsplit(", A", 1))
    #     if (title.endswith(", An")): new_title = "An "+"".join(title.rsplit(", An", 1))

    return cleaned_title

# -------------------------------------------------------------------------------------------------
# Multidisc ROM support
# -------------------------------------------------------------------------------------------------
def text_get_ROM_basename_tokens(basename_str):
    DEBUG_TOKEN_PARSER = False

    # --- Parse ROM base_noext/basename_str into tokens ---
    reg_exp = '\[.+?\]|\(.+?\)|\{.+?\}|[^\[\(\{]+'
    tokens_raw = re.findall(reg_exp, basename_str)
    if DEBUG_TOKEN_PARSER:
        log_debug('text_get_ROM_basename_tokens() tokens_raw   {0}'.format(tokens_raw))

    # >> Strip tokens
    tokens_strip = list()
    for token in tokens_raw: tokens_strip.append(token.strip())
    if DEBUG_TOKEN_PARSER:
        log_debug('text_get_ROM_basename_tokens() tokens_strip {0}'.format(tokens_strip))

    # >> Remove empty tokens ''
    tokens_clean = list()
    for token in tokens_strip: 
        if token: tokens_clean.append(token)
    if DEBUG_TOKEN_PARSER:        
        log_debug('text_get_ROM_basename_tokens() tokens_clean {0}'.format(tokens_clean))

    # >> Remove '-' tokens from Trurip multidisc names
    tokens = list()
    for token in tokens_clean:
        if token == '-': continue
        tokens.append(token)
    if DEBUG_TOKEN_PARSER:
        log_debug('text_get_ROM_basename_tokens() tokens       {0}'.format(tokens))

    return tokens

class MultiDiscInfo:
    def __init__(self, ROM_FN):
        self.ROM_FN      = ROM_FN
        self.isMultiDisc = False
        self.setName     = ''
        self.discName    = ROM_FN.getBase()
        self.extension   = ROM_FN.getExt()
        self.order       = 0

def text_get_multidisc_info(ROM_FN):
    MDSet = MultiDiscInfo(ROM_FN)
    
    # --- Parse ROM base_noext into tokens ---
    tokens = text_get_ROM_basename_tokens(ROM_FN.getBaseNoExt())

    # --- Check if ROM belongs to a multidisc set and get set name and order ---
    # Algortihm:
    # 1) Iterate list of tokens
    # 2) If a token marks a multidisk ROM extract set order
    # 3) Define the set basename by removing the multidisk token
    MultDiscFound = False
    for index, token in enumerate(tokens):
        # --- Redump ---
        matchObj = re.match(r'\(Dis[ck] ([0-9]+)\)', token)
        if matchObj:
            log_debug('text_get_multidisc_info() ### Matched Redump multidisc ROM ###')
            tokens_idx = list(range(0, len(tokens)))
            tokens_idx.remove(index)
            tokens_nodisc_idx = list(tokens_idx)
            tokens_mdisc = [tokens[x] for x in tokens_nodisc_idx]
            MultDiscFound = True
            break

        # --- TOSEC/Trurip ---
        matchObj = re.match(r'\(Dis[ck] ([0-9]+) of ([0-9]+)\)', token)
        if matchObj:
            log_debug('text_get_multidisc_info() ### Matched TOSEC/Trurip multidisc ROM ###')
            tokens_idx = list(range(0, len(tokens)))
            tokens_idx.remove(index)
            tokens_nodisc_idx = list(tokens_idx)
            # log_debug('text_get_multidisc_info() tokens_idx         = {0}'.format(tokens_idx))
            # log_debug('text_get_multidisc_info() index              = {0}'.format(index))
            # log_debug('text_get_multidisc_info() tokens_nodisc_idx  = {0}'.format(tokens_nodisc_idx))
            tokens_mdisc = [tokens[x] for x in tokens_nodisc_idx]
            MultDiscFound = True
            break

    if MultDiscFound:
        MDSet.isMultiDisc = True
        MDSet.setName = ' '.join(tokens_mdisc) + MDSet.extension
        MDSet.order = int(matchObj.group(1))
        log_debug('text_get_multidisc_info() base_noext   "{0}"'.format(ROM_FN.getBaseNoExt()))
        log_debug('text_get_multidisc_info() tokens       {0}'.format(tokens))
        log_debug('text_get_multidisc_info() tokens_mdisc {0}'.format(tokens_mdisc))
        log_debug('text_get_multidisc_info() setName      "{0}"'.format(MDSet.setName))
        log_debug('text_get_multidisc_info() discName     "{0}"'.format(MDSet.discName))
        log_debug('text_get_multidisc_info() extension    "{0}"'.format(MDSet.extension))
        log_debug('text_get_multidisc_info() order        {0}'.format(MDSet.order))

    return MDSet

# -------------------------------------------------------------------------------------------------
# URLs
# -------------------------------------------------------------------------------------------------
#
# Get extension of URL. Returns '' if not found. Examples: 'png', 'jpg', 'gif'.
#
def text_get_URL_extension(url):
    path = urlparse(url).path
    ext = os.path.splitext(path)[1]
    if ext[0] == '.': ext = ext[1:] # Remove initial dot

    return ext

#
# Defaults to 'jpg' if URL extension cannot be determined
#
def text_get_image_URL_extension(url):
    path = urlparse(url).path
    ext = os.path.splitext(path)[1]
    if ext[0] == '.': ext = ext[1:] # Remove initial dot
    ret = 'jpg' if ext == '' else ext

    return ret

# -------------------------------------------------------------------------------------------------
# File cache
# -------------------------------------------------------------------------------------------------
file_cache = {}
def misc_add_file_cache(dir_FN):
    global file_cache
    # >> Create a set with all the files in the directory
    if not dir_FN:
        log_debug('misc_add_file_cache() Empty dir_str. Exiting')
        return

    log_debug('misc_add_file_cache() Scanning path "{0}"'.format(dir_FN.getPath()))

    file_list = dir_FN.scanFilesInPath()
    # lower all filenames for easier matching
    file_set = [file.getBase().lower() for file in file_list]

    log_debug('misc_add_file_cache() Adding {0} files to cache'.format(len(file_set)))
    file_cache[dir_FN.getPath()] = file_set

#
# See misc_look_for_file() documentation below.
#
def misc_search_file_cache(dir_path, filename_noext, file_exts):
    # log_debug('misc_search_file_cache() Searching in  "{0}"'.format(dir_str))
    dir_str = dir_path.getPath()
    if dir_str not in file_cache:
        log_warning('Directory {0} not in file_cache'.format(dir_str))
        return None

    current_cache_set = file_cache[dir_str]
    for ext in file_exts:
        file_base = filename_noext + '.' + ext
        file_base_as_cached = file_base.lower()
        #log_debug('misc_search_file_cache() file_Base = "{0}"'.format(file_base))
        if file_base_as_cached in current_cache_set:
            # log_debug('misc_search_file_cache() Found in cache')
            return dir_path.pjoin(file_base)

    return None

# -------------------------------------------------------------------------------------------------
# Misc stuff
# -------------------------------------------------------------------------------------------------
#
# Given the image path, image filename with no extension and a list of file extensions search for 
# a file.
#
# rootPath       -> FileName object
# filename_noext -> Unicode string
# file_exts      -> list of extenstions with no dot [ 'zip', 'rar' ]
#
# Returns a FileName object if a valid filename is found.
# Returns None if no file was found.
#
def misc_look_for_file(rootPath, filename_noext, file_exts):
    for ext in file_exts:
        file_path = rootPath.pjoin(filename_noext + '.' + ext)
        if file_path.exists():
            return file_path

    return None

def misc_escape_regex_special_chars(s):
    s = s.replace('(', '\(')
    s = s.replace(')', '\)')
    s = s.replace('+', '\+')

    return s

# Search for a No-Intro DAT filename.
def misc_look_for_NoIntro_DAT(platform, DAT_list):
    # log_debug('Testing No-Intro platform "{}"'.format(platform.long_name))
    if not platform.DAT_prefix:
        # log_debug('Empty DAT_prefix. Return empty string.')
        return ''
    # Traverse all files and make a list of DAT matches.
    DAT_str = misc_escape_regex_special_chars(platform.DAT_prefix)
    patt = '.*' + DAT_str + ' \(Parent-Clone\) \((\d\d\d\d\d\d\d\d)-(\d\d\d\d\d\d)\)\.dat'
    # log_variable('patt', patt)
    fname_list = []
    for fname in DAT_list:
        m = re.match(patt, fname)
        if m: fname_list.append(fname)
    # log_variable('fname_list', fname_list)
    if fname_list:
        # If more than one DAT found sort alphabetically and pick the first.
        # Because the fname include the date the most recent must be first.
        return sorted(fname_list, reverse = True)[0]
    else:
        return ''

# Atari - Jaguar CD Interactive Multimedia System - Datfile (10) (2019-08-27 00-06-32)
# Commodore - Amiga CD - Datfile (350) (2019-06-28 13-05-34)
# Commodore - Amiga CD32 - Datfile (157) (2019-09-24 21-03-02)
def misc_look_for_Redump_DAT(platform, DAT_list):
    # log_debug('Testing Redump platform "{}"'.format(platform.long_name))
    if not platform.DAT_prefix:
        # log_debug('Empty DAT_prefix. Return empty string.')
        return ''
    DAT_str = misc_escape_regex_special_chars(platform.DAT_prefix)
    patt = '.*' + DAT_str + ' \(\d+\) \((\d\d\d\d-\d\d-\d\d) (\d\d-\d\d-\d\d)\)\.dat'
    # log_variable('patt', patt)
    fname_list = []
    for fname in DAT_list:
        m = re.match(patt, fname)
        if m: fname_list.append(fname)
    # log_variable('fname_list', fname_list)
    if fname_list:
        return sorted(fname_list, reverse = True)[0]
    else:
        return ''

#
# Generates a random an unique MD5 hash and returns a string with the hash
#
def misc_generate_random_SID():
    t1 = time.time()
    t2 = t1 + random.getrandbits(32)
    base = hashlib.md5(str(t1 + t2))
    sid = base.hexdigest()

    return sid

#
# Lazy function (generator) to read a file piece by piece. Default chunk size: 8k.
#
def misc_read_file_in_chunks(file_object, chunk_size = 8192):
    while True:
        data = file_object.read(chunk_size)
        if not data: break
        yield data

#
# Version helper class
#
class VersionNumber(object):
    def __init__(self, versionString):
        self.versionNumber = versionString.split('.')

    def getFullString(self):
        return '.'.join(self.versionNumber)

    def getMajor(self):
        return int(self.versionNumber[0])

    def getMinor(self):
        return int(self.versionNumber[1])

    def getBuild(self):
        return int(self.versionNumber[2])

# def dump_object_to_log_name(obj_name_str, obj):
#     log_debug('Dumping variable named "{0}"'.format(obj_name_str))
#     log_debug('obj.__class__.__name__ = {0}'.format(obj.__class__.__name__))
#     log_debug(pprint.pformat(obj))

def dump_object_to_log(obj):
    log_debug('Dumping obj.__class__.__name__ = {0}'.format(obj.__class__.__name__))
    log_debug(pprint.pformat(obj))

# #################################################################################################
# #################################################################################################
# Cryptographic utilities
# #################################################################################################
# #################################################################################################

#
# Creates a new self signed certificate base on OpenSSL PEM format.
# cert_name: the CN value of the certificate
# cert_file_path: the path to the .crt file of this certificate
# key_file_paht: the path to the .key file of this certificate
#
def create_self_signed_cert(cert_name, cert_file_path, key_file_path):
    # create a key pair
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)

    now    = datetime.now()
    expire = now + timedelta(days=365)

    # create a self-signed cert
    cert = crypto.X509()
    cert.get_subject().C = "GL"
    cert.get_subject().ST = "GL"
    cert.get_subject().L = "Kodi"
    cert.get_subject().O = "ael"
    cert.get_subject().OU = "ael"
    cert.get_subject().CN = cert_name
    cert.set_serial_number(1000)
    cert.set_notBefore(now.strftime("%Y%m%d%H%M%SZ").encode())
    cert.set_notAfter(expire.strftime("%Y%m%d%H%M%SZ").encode())
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, str('sha1'))

    log_debug('Creating certificate file {0}'.format(cert_file_path.getPath()))
    data = crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
    cert_file_path.saveStrToFile(data, 'ascii')

    log_debug('Creating certificate key file {0}'.format(key_file_path.getPath()))
    data = crypto.dump_privatekey(crypto.FILETYPE_PEM, k)
    key_file_path.saveStrToFile(data, 'ascii')

def getCertificatePublicKeyBytes(certificate_data):
    pk_data = getCertificatePublicKey(certificate_data)
    return bytearray(pk_data)

def getCertificatePublicKey(certificate_data):
    cert = crypto.x509.load_pem_x509_certificate(certificate_data, default_backend())
    pk = cert.public_key()
    pk_data = pk.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo)

    return pk_data

def getCertificateSignature(certificate_data):
    cert = crypto.x509.load_pem_x509_certificate(certificate_data, default_backend())
    return cert.signature

def verify_signature(data, signature, certificate_data):
    pk_data = getCertificatePublicKey(certificate_data)
    rsakey = RSA.importKey(pk_data) 
    signer = PKCS1_v1_5.new(rsakey) 

    digest = SHA256.new() 
    digest.update(data)

    if signer.verify(digest, signature):
        return True

    return False

def sign_data(data, key_certificate):
    rsakey = RSA.importKey(key_certificate) 
    signer = PKCS1_v1_5.new(rsakey) 
    digest = SHA256.new() 
        
    digest.update(data) 
    sign = signer.sign(digest) 

    return sign

def randomBytes(size):
    return get_random_bytes(size)

class HashAlgorithm(object):
    def __init__(self, shaVersion):
        self.shaVersion = shaVersion
        if self.shaVersion == 256:
            self.hashLength = 32
        else:
            self.hashLength = 20
       
    def _algorithm(self):

        if self.shaVersion == 256:
            return hashlib.sha256()
        else:
            return hashlib.sha1()

    def hash(self, value):
        algorithm = self._algorithm()
        algorithm.update(value)
        hashedValue = algorithm.digest()
        return hashedValue

    def hashToHex(self, value):
        hashedValue = self.hash(value)
        return binascii.hexlify(hashedValue)

    def digest_size(self):
        return self.hashLength

# Block size in bytes.
BLOCK_SIZE = 16

class AESCipher(object):

    def __init__(self, key, hashAlgorithm):
        
        keyHashed = hashAlgorithm.hash(key)
        truncatedKeyHashed = keyHashed[:16]

        self.key = truncatedKeyHashed

    def encrypt(self, raw):
        cipher = AES.new(self.key, AES.MODE_ECB)
        encrypted = cipher.encrypt(raw)
        return encrypted

    def encryptToHex(self, raw):
        encrypted = self.encrypt(raw)
        return binascii.hexlify(encrypted)

    def decrypt(self, enc):
        cipher = AES.new(self.key, AES.MODE_ECB)
        decrypted = cipher.decrypt(str(enc))
        return decrypted

def merge_dicts(x, y):
    """Given two dicts, merge them into a new dict as a shallow copy."""
    z = x.copy()
    z.update(y)
    return z

# #################################################################################################
# #################################################################################################
# Filesystem utilities
# #################################################################################################
# #################################################################################################
# This function not finished yet.
def misc_read_bytes_in_chunks(file_bytes, chunk_size = 8192):
    file_length = len(file_bytes)
    block_number = 0
    while True:
        start_index = None
        end_index = None
        data = file_bytes[start_index:end_index]
        yield data

#
# Calculates CRC, MD5 and SHA1 of a file in an efficient way.
# Returns a dictionary with the checksums or None in case of error.
#
# https://stackoverflow.com/questions/519633/lazy-method-for-reading-big-file-in-python
# https://stackoverflow.com/questions/1742866/compute-crc-of-file-in-python 
#
def misc_calculate_checksums(full_file_path):
    if full_file_path is None:
        log_debug('No checksum to complete')
        return None
    
    log_debug('Computing checksums "{}"'.format(full_file_path))
    try:
        f = open(full_file_path, 'rb')
        crc_prev = 0
        md5 = hashlib.md5()
        sha1 = hashlib.sha1()
        for piece in misc_read_file_in_chunks(f):
            crc_prev = zlib.crc32(piece, crc_prev)
            md5.update(piece)
            sha1.update(piece)
        crc_digest = '{:08X}'.format(crc_prev & 0xFFFFFFFF)
        md5_digest = md5.hexdigest()
        sha1_digest = sha1.hexdigest()
        size = os.path.getsize(full_file_path)
    except:
        log_debug('(Exception) In misc_calculate_checksums()')
        log_debug('Returning None')
        return None
    checksums = {
        'crc'  : crc_digest.upper(),
        'md5'  : md5_digest.upper(),
        'sha1' : sha1_digest.upper(),
        'size' : size,
    }

    return checksums

def misc_calculate_stream_checksums(file_bytes):
    log_debug('Computing checksums of bytes stream...'.format(len(file_bytes)))
    crc_prev = 0
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    # Process bytes stream block by block
    # for piece in misc_read_bytes_in_chunks(file_bytes):
    #     crc_prev = zlib.crc32(piece, crc_prev)
    #     md5.update(piece)
    #     sha1.update(piece)
    # Process bytes in one go
    crc_prev = zlib.crc32(file_bytes, crc_prev)
    md5.update(file_bytes)
    sha1.update(file_bytes)
    crc_digest = '{:08X}'.format(crc_prev & 0xFFFFFFFF)
    md5_digest = md5.hexdigest()
    sha1_digest = sha1.hexdigest()
    size = len(file_bytes)

    checksums = {
        'crc'  : crc_digest.upper(),
        'md5'  : md5_digest.upper(),
        'sha1' : sha1_digest.upper(),
        'size' : size,
    }

    return checksums

# Replace an item in dictionary. If dict_in is an OrderedDict then keep original order.
# Returns a dict or OrderedDict
def misc_replace_fav(dict_in, old_item_key, new_item_key, new_value):
    if type(dict_in) is dict:
        dict_in.pop(old_item_key)
        dict_in[new_item_key] = new_value
        return dict_in
    elif type(dict_in) is collections.OrderedDict:
        # In this case create a new OrderedDict to respect original order.
        # This implementation is slow and naive but I don't care, OrderedDict are only use
        # when editing ROM Collections.
        dict_out = collections.OrderedDict()
        for key in dict_in:
            if key == old_item_key:
                dict_out[new_item_key] = new_value
            else:
                dict_out[key] = dict_in[key]
        return dict_out
    else:
        raise TypeError

# Image file magic numbers. All at file offset 0.
# See https://en.wikipedia.org/wiki/List_of_file_signatures
IMAGE_MAGIC_DIC = {
    IMAGE_PNG_ID  : [ b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A' ],
    IMAGE_JPEG_ID : [
        b'\xFF\xD8\xFF\xDB',
        b'\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46\x00\x01',
        b'\xFF\xD8\xFF\xEE',
        b'\xFF\xD8\xFF\xE1',
    ],
    IMAGE_GIF_ID  : [
        b'\x47\x49\x46\x38\x37\x61',
        b'\x47\x49\x46\x38\x39\x61',
    ],
    IMAGE_BMP_ID  : [ b'\x42\x4D' ],
    IMAGE_TIFF_ID : [
        b'\x49\x49\x2A\x00',
        b'\x4D\x4D\x00\x2A',
    ]
}

# Inspects an image file and determine its type by using the magic numbers,
# Returns an image id defined in list IMAGE_IDS or IMAGE_UKNOWN_ID.
def misc_identify_image_id_by_contents(asset_fname):
    # If file size is 0 or less than 64 bytes it is corrupt.
    statinfo = os.stat(asset_fname)
    if statinfo.st_size < 64: return IMAGE_CORRUPT_ID

    # Read first 64 bytes of file.
    # Search for the magic number of the beginning of the file.
    with open(asset_fname, "rb") as f:
        file_bytes = f.read(64)
    for img_id in IMAGE_MAGIC_DIC:
        for magic_bytes in IMAGE_MAGIC_DIC[img_id]:
            magic_bytes_len = len(magic_bytes)
            file_chunk = file_bytes[0:magic_bytes_len]
            if len(file_chunk) != magic_bytes_len: raise TypeError
            if file_chunk == magic_bytes: return img_id

    return IMAGE_UKNOWN_ID

# Returns an image id defined in list IMAGE_IDS or IMAGE_UKNOWN_ID.
def misc_identify_image_id_by_ext(asset_fname):
    asset_root, asset_ext = os.path.splitext(asset_fname)
    # log_debug('asset_ext {}'.format(asset_ext))
    if not asset_ext: return IMAGE_UKNOWN_ID
    asset_ext = asset_ext[1:] # Remove leading dot '.png' -> 'png'
    for img_id in IMAGE_EXTENSIONS:
        for img_ext in IMAGE_EXTENSIONS[img_id]:
            if asset_ext.lower() == img_ext: return img_id

    return IMAGE_UKNOWN_ID

# -------------------------------------------------------------------------------------------------
# --- New Filesystem class ---
#
# 1. Automatically uses Python standard library for local files and Kodi VFS for remote files.
#
# 2. All paths on all platforms use the slash '/' to separate directories.
#
# 3. Directories always end in a '/' character.
#
# 3. Decoding Unicode to the filesystem encoding is done in this class.
#
# 4. Tested with the following remote protocols:
#
#     a) special://
#
#     b) smb://
#
# --- Function reference ---
# FileName.getPath()         Full path                                     /home/Wintermute/Sonic.zip
# FileName.getPathNoExt()    Full path with no extension                   /home/Wintermute/Sonic
# FileName.getDir()          Directory name of file. Does not end in '/'   /home/Wintermute/
# FileName.getBase()         File name with no path                        Sonic.zip
# FileName.getBaseNoExt()    File name with no path and no extension       Sonic
# FileName.getExt()          File extension                                .zip
#
#
# A) Transform paths like smb://server/directory/ into \\server\directory\
# B) Use xbmc.translatePath() for paths starting with special://
# C) Uses xbmcvfs wherever possible
#
# -------------------------------------------------------------------------------------------------
# Once everything is working like a charm comment all the debug code to speed up.
DEBUG_NEWFILENAME_CLASS = True

class NewFileName:
    # ---------------------------------------------------------------------------------------------
    # Constructor
    # path_str is an Unicode string.
    # ---------------------------------------------------------------------------------------------
    def __init__(self, path_str, isdir = False):
        self.path_str = path_str
        self.is_a_dir = isdir

        # --- Check if path needs translation ---
        # Note that internally path_tr is always used as the filename.
        if self.path_str.lower().startswith('special://'):
            self.is_translated = True
            self.path_tr = xbmc.translatePath(self.path_str)
            # Check translated path does not contain '\'
            # NOTE We don't care if the translated paths has '\' characters or not. The translated
            #      path is internal to the class and never used outside the class. In the JSON
            #      databases and config files the original path path_str is used always.
            # if self.path_tr.find('\\'):
            #     log_error('(NewFileName) path_str "{0}"'.format(self.path_str))
            #     log_error('(NewFileName) path_tr  "{0}"'.format(self.path_tr))
            #     e_str = '(NewFileName) Translated path has \\ characters'
            #     log_error(e_str)
            #     raise Addon_Error(e_str)
        else:
            self.is_translated = False
            self.path_tr = self.path_str

        # --- Ensure directory separator is the '/' character for all OSes ---
        self.path_str = self.path_str.replace('\\', '/')
        self.path_tr = self.path_tr.replace('\\', '/')

        # --- If a directory, ensure path ends with '/' ---
        if self.is_a_dir:
            if not self.path_str[-1:] == '/': self.path_str = self.path_str + '/'
            if not self.path_tr[-1:] == '/': self.path_tr = self.path_tr + '/'

        # if DEBUG_NEWFILENAME_CLASS:
        #     log_debug('NewFileName() path_str "{0}"'.format(self.path_str))
        #     log_debug('NewFileName() path_tr  "{0}"'.format(self.path_tr))

        # --- Check if file is local or remote and needs translation ---
        if self.path_str.lower().startswith('smb://'):
            self.is_local = False
        else:
            self.is_local = True

        # --- Assume that translated paths are always local ---
        if self.is_translated and not self.is_local:
            e_str = '(NewFileName) File is translated and remote.'
            log_error(e_str)
            raise AddonException(e_str)

        # --- Use Pyhton for local paths and Kodi VFS for remote paths ---
        if self.is_local:
            # --- Filesystem functions ---
            self.exists         = self.exists_python
            self.makedirs       = self.makedirs_python
            self.list           = self.list_python
            self.recursive_list = self.recursive_list_python

            # --- File low-level IO functions ---
            self.open     = self.open_python
            self.read     = self.read_python
            self.write    = self.write_python
            self.close    = self.close_python
            self.unlink   = self.unlink_python
        else:
            self.exists         = self.exists_kodivfs
            self.makedirs       = self.makedirs_kodivfs
            self.list           = self.list_kodivfs
            self.recursive_list = self.recursive_list_kodivfs

            self.open     = self.open_kodivfs
            self.read     = self.read_kodivfs
            self.write    = self.write_kodivfs
            self.close    = self.close_kodivfs
            self.unlink   = self.unlink_kodivfs

    def _decodeName(self, name):
        if type(name) == str:
            try:
                name = name.decode('utf8')
            except:
                name = name.decode('windows-1252')

        return name
    
    # ---------------------------------------------------------------------------------------------
    # Core functions
    # ---------------------------------------------------------------------------------------------
    #
    # Wheter the path stored in the FileName class is a directory or a regular file is handled
    # internally. This is to avoid a design flaw of the Kodi VFS library.
    #
    def isdir(self):
        return self.is_a_dir

    #
    # Allow late setting of isdir() if using the constructor call is not available, for example
    # when using FileName.pjoin().
    #
    def set_isdir(self, isdir):
        self.__init__(self.path_str, isdir)

    #
    # Appends a string to path
    # Returns self FileName object
    #
    def append(self, arg):
        self.path_str = self.path_str + arg
        self.path_tr = self.path_tr + arg

        return self

    #
    # Joins paths and returns a new filename object.
    #
    def pjoin(self, path_str, isdir = False):
        return FileName(os.path.join(self.path_str, path_str), isdir)

    # ---------------------------------------------------------------------------------------------
    # Operator overloads
    # ---------------------------------------------------------------------------------------------
    def __str__(self):
        return self.path_str

    # Overloaded operator + behaves like self pjoin()
    # See http://blog.teamtreehouse.com/operator-overloading-python
    # Argument other is a FileName object. other originalPath is expected to be a
    # subdirectory (path transformation not required)
    def __add__(self, path_str):
        return self.pjoin(path_str)

    def __eq__(self, other):
        return self.path_str == other.path_str

    def __ne__(self, other):
        return not self.__eq__(other)

    # ---------------------------------------------------------------------------------------------
    # Path manipulation and file information
    # ---------------------------------------------------------------------------------------------
    def getPath(self):
        return self.path_str

    def getPathNoExt(self):
        root, ext = os.path.splitext(self.path_str)

        return root

    def getDir(self):
        return os.path.dirname(self.path_str)

    # Returns a new FileName object.
    def getDirAsFileName(self):
        return NewFileName(self.getDir())

    def getBase(self):
        return os.path.basename(self.path_str)

    def getBaseNoExt(self):
        basename  = os.path.basename(self.path_str)
        root, ext = os.path.splitext(basename)

        return root

    def getExt(self):
        root, ext = os.path.splitext(self.path_str)
        return ext

    def changeExtension(self, targetExt):
        #raise AddonException('Implement me.')
        ext = self.getExt()
        copiedPath = self.path_str
        if not targetExt.startswith('.'):
            targetExt = '.{0}'.format(targetExt)
        new_path = FileName(copiedPath.replace(ext, targetExt))
        return new_path

    def escapeQuotes(self):
        self.path_tr = self.path_tr.replace("'", "\\'")
        self.path_tr = self.path_tr.replace('"', '\\"')
        
    # Checks the extension to determine the type of the file.
    def isImageFile(self):
        return '.' + self.getExt().lower() in IMAGE_EXTENSION_LIST

    def isManual(self):
        return '.' + self.getExt().lower() in MANUAL_EXTENSION_LIST

    def isVideoFile(self):
        return '.' + self.getExt().lower() in TRAILER_EXTENSION_LIST

    # ---------------------------------------------------------------------------------------------
    # Filesystem functions. Python Standard Library implementation
    # ---------------------------------------------------------------------------------------------
    def exists_python(self):
        return os.path.exists(self.path_tr)

    def makedirs_python(self):
        if not os.path.exists(self.path_tr): 
            if DEBUG_NEWFILENAME_CLASS:
                log_debug('NewFileName::makedirs_python() path_tr "{0}"'.format(self.path_tr))
            os.makedirs(self.path_tr)

    def list_python(self):        
        return os.listdir(self.path_tr)

    def recursive_list_python(self):
        files = []
        for root, dirs, foundfiles in os.walk(self.path_tr):
            for filename in foundfiles:
                files.append(os.path.join(root, filename))

        return files
    
    # ---------------------------------------------------------------------------------------------
    # Filesystem functions. Kodi VFS implementation.
    # Kodi VFS functions always work with path_str, not with the translated path.
    # ---------------------------------------------------------------------------------------------
    def exists_kodivfs(self):
        return xbmcvfs.exists(self.path_str)

    def makedirs_kodivfs(self):
        xbmcvfs.mkdirs(self.path_tr)

    def list_kodivfs(self):
        subdirectories, filenames = xbmcvfs.listdir(self.path_tr)
        return filenames
    
    def recursive_list_kodivfs(self):
        files = self.recursive_list_kodivfs_folders(self.path_tr, None)
        return files
    
    def recursive_list_kodivfs_folders(self, fullPath, parentFolder):
        files = []
        subdirectories, filenames = xbmcvfs.listdir(fullPath)
        
        for filename in filenames:
            filePath = os.path.join(parentFolder, filename) if parentFolder is not None else filename
            files.append(filePath)

        for subdir in subdirectories:
            subPath = os.path.join(parentFolder, subdir) if parentFolder is not None else subdir
            subFullPath = os.path.join(fullPath, subdir)
            subPathFiles = self.recursive_list_kodivfs_folders(subFullPath, subPath)
            files.extend(subPathFiles)

        return files

    # ---------------------------------------------------------------------------------------------
    # File low-level IO functions. Python Standard Library implementation
    # ---------------------------------------------------------------------------------------------
    def open_python(self, flags):
        log_debug('NewFileName::open_python() path_tr "{0}"'.format(self.path_tr))
        log_debug('NewFileName::open_python() flags   "{0}"'.format(flags))

        # open() is a built-in function.
        # See https://docs.python.org/3/library/functions.html#open
        self.fileHandle = open(self.path_tr, flags)

        return self

    def close_python(self):
        if self.fileHandle is None:
            raise OSError('file not opened')
        self.fileHandle.close()
        self.fileHandle = None

    def read_python(self):
       if self.fileHandle is None:
           raise OSError('file not opened')

       return self.fileHandle.read()

    def write_python(self, bytes):
       if self.fileHandle is None:
           raise OSError('file not opened')
       self.fileHandle.write(bytes)

    def unlink_python(self):
        os.remove(self.path_tr)
            
    # ---------------------------------------------------------------------------------------------
    # File low-level IO functions. Kodi VFS implementation.
    # Kodi VFS documentation in https://alwinesch.github.io/group__python__xbmcvfs.html
    # ---------------------------------------------------------------------------------------------
    def open_kodivfs(self, flags):
        log_debug('NewFileName::open_kodivfs() path_tr "{0}"'.format(self.path_tr))
        log_debug('NewFileName::open_kodivfs() flags   "{0}"'.format(flags))

        self.fileHandle = xbmcvfs.File(self.path_tr, flags)
        return self
    
    def read_kodivfs(self):
        if self.fileHandle is None: raise OSError('file not opened')
        return self.fileHandle.read()
 
    def write_kodivfs(self, bytes):
        if self.fileHandle is None: raise OSError('file not opened')
        self.fileHandle.write(bytes)

    def close_kodivfs(self):
        if self.fileHandle is None: raise OSError('file not opened')
        self.fileHandle.close()
        self.fileHandle = None
  
    def unlink_kodivfs(self):
        if self.is_a_dir:
            xbmcvfs.rmdir(self.path_tr)
            return
        
        xbmcvfs.delete(self.path_tr)
        # hard delete if it doesnt succeed
        #log_debug('xbmcvfs.delete() failed, applying hard delete')
        if self.exists():
            self.unlink_python()
            
    # ---------------------------------------------------------------------------------------------
    # File high-level IO functions
    # These functions are independent of the filesystem implementation.
    # For compatibility with Python 3, use the terms str for Unicode strings and bytes for
    # encoded strings.
    # ---------------------------------------------------------------------------------------------
    #
    # If both files are local use Python SL. Otherwise use Kodi VFS.
    # shutil.copy2() preserves metadata, including atime and mtime. We do not want that.
    #
    # See https://docs.python.org/2/library/shutil.html#shutil.copy
    # See https://docs.python.org/2/library/shutil.html#shutil.copy2
    # See https://docs.python.org/2/library/sys.html#sys.getfilesystemencoding
    #
    def copy(self, to_FN):
        if self.is_local and to_FN.is_local:
            fs_encoding = sys.getfilesystemencoding()
            source_bytes = self.getPath().decode(fs_encoding)
            dest_bytes = to_FN.getPath().decode(fs_encoding)
            if DEBUG_NEWFILENAME_CLASS:
                log_debug('NewFileName::copy() Using Python Standard Library')
                log_debug('NewFileName::copy() fs encoding "{0}"'.format(fs_encoding))
                log_debug('NewFileName::copy() Copy "{0}"'.format(source_bytes))
                log_debug('NewFileName::copy() into "{0}"'.format(dest_bytes))
            try:
                shutil.copy(source_bytes, dest_bytes)
            except OSError:
                log_error('NewFileName::copy() OSError exception copying image')
                raise AddonException('OSError exception copying image')
            except IOError:
                log_error('NewFileName::copy() IOError exception copying image')
                raise AddonException('IOError exception copying image')
        else:
            if DEBUG_NEWFILENAME_CLASS:
                log_debug('NewFileName::copy() Using Kodi VFS')
                log_debug('NewFileName::copy() Copy "{0}"'.format(self.getPath()))
                log_debug('NewFileName::copy() into "{0}"'.format(to_FN.getPath()))
            # >> If xbmcvfs.copy() fails what exceptions raise???
            xbmcvfs.copy(self.getPath(), to_FN.getPath())

    #
    # Loads a file into a Unicode string.
    # By default all files are assumed to be encoded in UTF-8.
    # Returns a Unicode string.
    #
    def loadFileToStr(self, encoding = 'utf-8'):
        if DEBUG_NEWFILENAME_CLASS:
            log_debug('NewFileName::loadFileToStr() Loading path_str "{0}"'.format(self.path_str))

        # NOTE Exceptions should be catched, reported and re-raised in the low-level
        # functions, not here!!!
        file_bytes = None
        try:
            self.open('r')
            file_bytes = self.read()
            self.close()
        except OSError:
            log_error('(OSError) Exception in FileName::loadFileToStr()')
            log_error('(OSError) Cannot read {0} file'.format(self.path_tr))
            raise AddonException('(OSError) Cannot read {0} file'.format(self.path_tr))
        except IOError as Ex:
            log_error('(IOError) Exception in FileName::loadFileToStr()')
            log_error('(IOError) errno = {0}'.format(Ex.errno))
            if Ex.errno == errno.ENOENT: log_error('(IOError) No such file or directory.')
            else:                        log_error('(IOError) Unhandled errno value.')
            log_error('(IOError) Cannot read {0} file'.format(self.path_tr))
            raise AddonException('(IOError) Cannot read {0} file'.format(self.path_tr))
        
        # Return a Unicode string.
        if encoding is None or file_bytes is None:
            return file_bytes
        
        return file_bytes.decode(encoding)
    
    #
    # data_str is a Unicode string. Encode it in UTF-8 for file writing.
    #
    def saveStrToFile(self, data_str, encoding = 'utf-8'):
        if DEBUG_NEWFILENAME_CLASS:
            log_debug('NewFileName::loadFileToStr() Loading path_str "{0}"'.format(self.path_str))
            log_debug('NewFileName::loadFileToStr() Loading path_tr  "{0}"'.format(self.path_tr))

        # --- Catch exceptions in the FilaName class ---
        try:
            self.open('w')
            self.write(data_str.encode(encoding))
            self.close()
        except OSError:
            log_error('(OSError) Exception in saveStrToFile()')
            log_error('(OSError) Cannot write {0} file'.format(self.path_tr))
            raise AddonException('(OSError) Cannot write {0} file'.format(self.path_tr))
        except IOError as e:
            log_error('(IOError) Exception in saveStrToFile()')
            log_error('(IOError) errno = {0}'.format(e.errno))
            if e.errno == errno.ENOENT: log_error('(IOError) No such file or directory.')
            else:                       log_error('(IOError) Unhandled errno value.')
            log_error('(IOError) Cannot write {0} file'.format(self.path_tr))
            raise AddonException('(IOError) Cannot write {0} file'.format(self.path_tr))

    # Opens a propery file and reads it
    # Reads a given properties file with each line of the format key=value.
    # Returns a dictionary containing the pairs.
    def readPropertyFile(self):
        import csv

        file_contents = self.loadFileToStr()
        file_lines = file_contents.splitlines()

        result={ }
        reader = csv.reader(self._utf_8_encoder(file_lines), delimiter=str('='), quotechar=str('"'), quoting=csv.QUOTE_MINIMAL, skipinitialspace=True)
        for row in reader:
            if len(row) < 2:
               continue
            
            key = unicode(row[0],'utf-8').strip()
            value = unicode(row[1],'utf-8').strip().lstrip('"').rstrip('"')
            result[key] = value

        return result

    def _utf_8_encoder(self, unicode_csv_data):
        for line in unicode_csv_data:
            yield line.encode('utf-8')

    # Opens JSON file and reads it
    def readJson(self):
        contents = self.loadFileToStr()
        return json.loads(contents)
        
    # --- Configure JSON writer ---
    # >> json_unicode is either str or unicode
    # >> See https://docs.python.org/2.7/library/json.html#json.dumps
    # unicode(json_data) auto-decodes data to unicode if str
    # NOTE More compact JSON files (less blanks) load faster because size is smaller.
    def writeJson(self, raw_data, JSON_indent = 1, JSON_separators = (',', ':')):
        json_data = json.dumps(raw_data, ensure_ascii = False, sort_keys = True, 
                                indent = JSON_indent, separators = JSON_separators)
        self.saveStrToFile(json_data)

    # Opens file and writes xml. Give xml root element.
    def writeXml(self, xml_root):
        data = ET.tostring(xml_root)
        self.saveStrToFile(data)

    def writeAll(self, bytes, flags = 'w'):
         # --- Catch exceptions in the FilaName class ---
        try:
            self.open(flags)
            self.write(bytes)
            self.close()
        except OSError:
            log_error('(OSError) Exception in writeAll()')
            log_error('(OSError) Cannot write {0} file'.format(self.path_tr))
            raise AddonException('(OSError) Cannot write {0} file'.format(self.path_tr))
        except IOError as e:
            log_error('(IOError) Exception in writeAll()')
            log_error('(IOError) errno = {0}'.format(e.errno))
            if e.errno == errno.ENOENT: log_error('(IOError) No such file or directory.')
            else:                       log_error('(IOError) Unhandled errno value.')
            log_error('(IOError) Cannot write {0} file'.format(self.path_tr))
            raise AddonException('(IOError) Cannot write {0} file'.format(self.path_tr))
        
    # ---------------------------------------------------------------------------------------------
    # Scanner functions
    # ---------------------------------------------------------------------------------------------
    def scanFilesInPath(self, mask = '*.*'):
        files = []
        all_files = self.list()
        
        for filename in fnmatch.filter(all_files, mask):
            files.append(self.pjoin(self._decodeName(filename)))
            
        return files
    
    def recursiveScanFilesInPath(self, mask = '*.*'):
        files = []
        all_files = self.recursive_list()
        
        for filename in fnmatch.filter(all_files, mask):
            files.append(self.pjoin(self._decodeName(filename)))
            
        return files

# -------------------------------------------------------------------------------------------------
# Decide which class to use for managing filenames.
# -------------------------------------------------------------------------------------------------
# FileName = PythonFileName
# FileName = KodiFileName
FileName = NewFileName

# #################################################################################################
# #################################################################################################
# Kodi utilities
# #################################################################################################
# #################################################################################################

# --- Internal globals ----------------------------------------------------------------------------
current_log_level = LOG_INFO

# -------------------------------------------------------------------------------------------------
# Logging functions
# -------------------------------------------------------------------------------------------------
def set_log_level(level):
    global current_log_level

    current_log_level = level

#
# For Unicode stuff in Kodi log see http://forum.kodi.tv/showthread.php?tid=144677
#
def log_debug_KR(str_text):
    if current_log_level >= LOG_DEBUG:
        # If str_text is str we assume it's "utf-8" encoded.
        # will fail if called with other encodings (latin, etc).
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')

        # At this point we are sure str_text is a unicode string.
        log_text = u'AEL DEBUG: ' + str_text
        xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGNOTICE)

def log_verb_KR(str_text):
    if current_log_level >= LOG_VERB:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = u'AEL VERB : ' + str_text
        xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGNOTICE)

def log_info_KR(str_text):
    if current_log_level >= LOG_INFO:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = u'AEL INFO : ' + str_text
        xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGNOTICE)

def log_warning_KR(str_text):
    if current_log_level >= LOG_WARNING:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = u'AEL WARN : ' + str_text
        xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGWARNING)

def log_error_KR(str_text):
    if current_log_level >= LOG_ERROR:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = u'AEL ERROR: ' + str_text
        xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGERROR)

#
# Replacement functions when running outside Kodi with the standard Python interpreter.
#
def log_debug_Python(str):
    print(str)

def log_verb_Python(str):
    print(str)

def log_info_Python(str):
    print(str)

def log_warning_Python(str):
    print(str)

def log_error_Python(str):
    print(str)

# -------------------------------------------------------------------------------------------------
# Kodi notifications and dialogs
# -------------------------------------------------------------------------------------------------
#
# Displays a modal dialog with an OK button. Dialog can have up to 3 rows of text, however first
# row is multiline.
# Call examples:
#  1) ret = kodi_dialog_OK('Launch ROM?')
#  2) ret = kodi_dialog_OK('Launch ROM?', title = 'AEL - Launcher')
#
def kodi_dialog_OK(text, title = 'Advanced Emulator Launcher'):
    xbmcgui.Dialog().ok(title, text)

# Returns True is YES was pressed, returns False if NO was pressed or dialog canceled.
def kodi_dialog_yesno(text, title = 'Advanced Emulator Launcher'):
    return xbmcgui.Dialog().yesno(title, text)

# Returns True is YES was pressed, returns False if NO was pressed or dialog canceled.
def kodi_dialog_yesno_custom(text, yeslabel_str, nolabel_str, title = 'Advanced Emulator Launcher'):
    return xbmcgui.Dialog().yesno(title, text, yeslabel = yeslabel_str, nolabel = nolabel_str)

def kodi_dialog_yesno_timer(text, timer_ms = 30000, title = 'Advanced Emulator Launcher'):
    return xbmcgui.Dialog().yesno(title, text, autoclose = timer_ms)

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

#
# Deprecated in Leia! Do not use busydialogs anymore!!!!!
# See https://forum.kodi.tv/showthread.php?tid=303073&pid=2739256#pid2739256
# See https://github.com/xbmc/xbmc/pull/13954
# See https://github.com/xbmc/xbmc/pull/13958
#
# def kodi_busydialog_ON(): xbmc.executebuiltin('ActivateWindow(busydialog)')

# def kodi_busydialog_OFF(): xbmc.executebuiltin('Dialog.Close(busydialog)')

def kodi_refresh_container():
    log_debug('kodi_refresh_container()')
    xbmc.executebuiltin('Container.Refresh')

def kodi_toggle_fullscreen():
    kodi_jsonrpc_dict('Input.ExecuteAction', {'action' : 'togglefullscreen'})

def kodi_get_screensaver_mode():
    r_dic = kodi_jsonrpc_dict('Settings.getSettingValue', {'setting' : 'screensaver.mode'})
    screensaver_mode = r_dic['value']
    return screensaver_mode

g_screensaver_mode = None # Global variable to store screensaver status.
def kodi_disable_screensaver():
    global g_screensaver_mode
    g_screensaver_mode = kodi_get_screensaver_mode()
    log_debug('kodi_disable_screensaver() g_screensaver_mode "{}"'.format(g_screensaver_mode))
    p_dic = {
        'setting' : 'screensaver.mode',
        'value' : '',
    }
    kodi_jsonrpc_dict('Settings.setSettingValue', p_dic)
    log_debug('kodi_disable_screensaver() Screensaver disabled.')

# kodi_disable_screensaver() must be called before this function or bad things will happen.
def kodi_restore_screensaver():
    if g_screensaver_mode is None:
        log_error('kodi_disable_screensaver() must be called before kodi_restore_screensaver()')
        raise RuntimeError
    log_debug('kodi_restore_screensaver() Screensaver mode "{}"'.format(g_screensaver_mode))
    p_dic = {
        'setting' : 'screensaver.mode',
        'value' : g_screensaver_mode,
    }
    kodi_jsonrpc_dict('Settings.setSettingValue', p_dic)
    log_debug('kodi_restore_screensaver() Restored previous screensaver status.')

def kodi_jsonrpc_dict(method_str, params_dic, verbose = False):
    params_str = json.dumps(params_dic)
    if verbose:
        log_debug('kodi_jsonrpc_dict() method_str "{}"'.format(method_str))
        log_debug('kodi_jsonrpc_dict() params_dic = \n{}'.format(pprint.pformat(params_dic)))
        log_debug('kodi_jsonrpc_dict() params_str "{}"'.format(params_str))

    # --- Do query ---
    header = '"id" : 1, "jsonrpc" : "2.0"'
    query_str = '{{{}, "method" : "{}", "params" : {} }}'.format(header, method_str, params_str)
    response_json_str = xbmc.executeJSONRPC(query_str)

    # --- Parse JSON response ---
    response_dic = json.loads(response_json_str)
    if 'error' in response_dic:
        result_dic = response_dic['error']
        log_warning('kodi_jsonrpc_dict() JSONRPC ERROR {}'.format(result_dic['message']))
    else:
        result_dic = response_dic['result']
    if verbose:
        log_debug('kodi_jsonrpc_dict() result_dic = \n{}'.format(pprint.pformat(result_dic)))

    return result_dic

#
# Access Kodi JSON-RPC interface in an easy way.
# Returns a dictionary with the parsed response 'result' field.
#
# Query input:
#
# {
#     "id" : 1,
#     "jsonrpc" : "2.0",
#     "method" : "Application.GetProperties",
#     "params" : { "properties" : ["name", "version"] }
# }
#
# Query response:
#
# {
#     "id" : 1,
#     "jsonrpc" : "2.0",
#     "result" : {
#         "name" : "Kodi",
#         "version" : {"major":17,"minor":6,"revision":"20171114-a9a7a20","tag":"stable"}
#     }
# }
#
# Query response ERROR:
# {
#     "id" : null,
#     "jsonrpc" : "2.0",
#     "error" : { "code":-32700, "message" : "Parse error."}
# }
#
def kodi_jsonrpc_query(method_str, params_str, verbose = False):
    if verbose:
        log_debug('kodi_jsonrpc_query() method_str "{0}"'.format(method_str))
        log_debug('kodi_jsonrpc_query() params_str "{0}"'.format(params_str))
        params_dic = json.loads(params_str)
        log_debug('kodi_jsonrpc_query() params_dic = \n{0}'.format(pprint.pformat(params_dic)))

    # --- Do query ---
    query_str = '{{"id" : 1, "jsonrpc" : "2.0", "method" : "{0}", "params" : {1} }}'.format(method_str, params_str)
    # if verbose: log_debug('kodi_jsonrpc_query() query_str "{0}"'.format(query_str))
    response_json_str = xbmc.executeJSONRPC(query_str)
    # if verbose: log_debug('kodi_jsonrpc_query() response "{0}"'.format(response_json_str))

    # --- Parse JSON response ---
    response_dic = json.loads(response_json_str)
    # if verbose: log_debug('kodi_jsonrpc_query() response_dic = \n{0}'.format(pprint.pformat(response_dic)))
    if 'error' in response_dic:
        result_dic = response_dic['error']
        log_warning('kodi_jsonrpc_query() JSONRPC ERROR {0}'.format(result_dic['message']))
    else:
        result_dic = response_dic['result']
    if verbose:
        log_debug('kodi_jsonrpc_query() result_dic = \n{0}'.format(pprint.pformat(result_dic)))

    return result_dic

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

def kodi_dialog_GetText(title_str, default_value):
    output  = xbmcgui.Dialog().input(title_str, default_value, xbmcgui.INPUT_ALPHANUM)
    return output

#
# Kodi dialog to select a file
# Documentation in https://alwinesch.github.io/group__python___dialog.html
#
def kodi_dialog_GetDirectory(title_str, ext_list, current_dir):
    new_dir = xbmcgui.Dialog().browse(0, title_str, 'files', ext_list, True, False, current_dir)

    return new_dir.decode('utf-8')

def kodi_dialog_GetFile(title_str, ext_list, current_dir):
    new_file = xbmcgui.Dialog().browse(1, title_str, 'files', ext_list, True, False, current_dir)

    return new_file.decode('utf-8')

def kodi_dialog_GetImage(title_str, ext_list, current_dir):
    new_image = xbmcgui.Dialog().browse(2, title_str, 'files', ext_list, True, False, current_dir)

    return new_image.decode('utf-8')

#
# See https://kodi.wiki/view/JSON-RPC_API/v8#Textures
# See https://forum.kodi.tv/showthread.php?tid=337014
# See https://forum.kodi.tv/showthread.php?tid=236320
#
def kodi_delete_cache_texture(database_path_str):
    log_debug('kodi_delete_cache_texture() Deleting texture "{0}:'.format(database_path_str))

    # --- Query texture database ---
    json_fname_str = text_escape_JSON(database_path_str)
    prop_str = (
        '{' +
        '"properties" : [ "url", "cachedurl", "lasthashcheck", "imagehash", "sizes"], ' +
        '"filter" : {{ "field" : "url", "operator" : "is", "value" : "{0}" }}'.format(json_fname_str) +
        '}'
    )
    r_dic = kodi_jsonrpc_query('Textures.GetTextures', prop_str, verbose = False)

    # --- Delete cached texture ---
    num_textures = len(r_dic['textures'])
    log_debug('kodi_delete_cache_texture() Returned list with {0} textures'.format(num_textures))
    if num_textures == 1:
        textureid = r_dic['textures'][0]['textureid']
        log_debug('kodi_delete_cache_texture() Deleting texture with id {0}'.format(textureid))
        prop_str = '{{ "textureid" : {0} }}'.format(textureid)
        r_dic = kodi_jsonrpc_query('Textures.RemoveTexture', prop_str, verbose = False)
    else:
        log_warning('kodi_delete_cache_texture() Number of textures different from 1. No texture deleted from cache')

def kodi_print_texture_info(database_path_str):
    log_debug('kodi_print_texture_info() File "{0}"'.format(database_path_str))

    # --- Query texture database ---
    json_fname_str = text_escape_JSON(database_path_str)
    prop_str = (
        '{' +
        '"properties" : [ "url", "cachedurl", "lasthashcheck", "imagehash", "sizes"], ' +
        '"filter" : {{ "field" : "url", "operator" : "is", "value" : "{0}" }}'.format(json_fname_str) +
        '}'
    )
    r_dic = kodi_jsonrpc_query('Textures.GetTextures', prop_str, verbose = False)

    # --- Delete cached texture ---
    num_textures = len(r_dic['textures'])
    log_debug('kodi_print_texture_info() Returned list with {0} textures'.format(num_textures))
    if num_textures == 1:
        log_debug('Cached URL  {0}'.format(r_dic['textures'][0]['cachedurl']))
        log_debug('Hash        {0}'.format(r_dic['textures'][0]['imagehash']))
        log_debug('Last check  {0}'.format(r_dic['textures'][0]['lasthashcheck']))
        log_debug('Texture ID  {0}'.format(r_dic['textures'][0]['textureid']))
        log_debug('Texture URL {0}'.format(r_dic['textures'][0]['url']))

# -------------------------------------------------------------------------------------------------
# Determine Kodi version and create some constants to allow version-dependent code.
# This if useful to work around bugs in Kodi core.
# -------------------------------------------------------------------------------------------------
def kodi_get_Kodi_major_version():
    try:
        rpc_dic = kodi_jsonrpc_query('Application.GetProperties', '{ "properties" : ["version"] }')
        return int(rpc_dic['version']['major'])
    except:
        # default fallback
        return 17

kodi_running_version = kodi_get_Kodi_major_version()

# --- Version constants. Minimum required version is Kodi Krypton ---
KODI_VERSION_KRYPTON = 17
KODI_VERSION_LEIA    = 18

# -------------------------------------------------------------------------------------------------
# Kodi Wizards (by Chrisism)
# -------------------------------------------------------------------------------------------------
#
# The wizarddialog implementations can be used to chain a collection of
# different kodi dialogs and use them to fill a dictionary with user input.
#
# Each wizarddialog accepts a key which will correspond with the key/value combination
# in the dictionary. It will also accept a customFunction (delegate or lambda) which
# will be called after the dialog has been shown. Depending on the type of dialog some
# other arguments might be needed.
#
# The chaining is implemented by applying the decorator pattern and injecting
# the previous wizarddialog in each new one.
# You can then call the method 'runWizard()' on the last created instance.
#
# Each wizard has a customFunction which will can be called after executing this 
# specific dialog. It also has a conditionalFunction which can be called before
# executing this dialog which will indicate if this dialog may be shown (True return value).
#
class WizardDialog():
    __metaclass__ = abc.ABCMeta

    def __init__(self, decoratorDialog, property_key, title, customFunction = None, conditionalFunction = None):
        self.decoratorDialog = decoratorDialog
        self.property_key = property_key
        self.title = title
        self.customFunction = customFunction
        self.conditionalFunction = conditionalFunction
        self.cancelled = False

    def runWizard(self, properties):
        if not self.executeDialog(properties):
            log_warning('User stopped wizard')
            return None

        return properties

    def executeDialog(self, properties):
        if self.decoratorDialog is not None:
            if not self.decoratorDialog.executeDialog(properties):
                return False

        if self.conditionalFunction is not None:
            mayShow = self.conditionalFunction(self.property_key, properties)
            if not mayShow:
                log_debug('Skipping dialog for key: {0}'.format(self.property_key))
                return True

        output = self.show(properties)
        if self.cancelled: return False

        if self.customFunction is not None:
            output = self.customFunction(output, self.property_key, properties)

        if self.property_key:
            log_debug('WizardDialog::executeDialog() props[{0}] =  {1}'.format(self.property_key, output))
            properties[self.property_key] = output

        return True

    @abc.abstractmethod
    def show(self, properties): return True

    def _cancel(self): self.cancelled = True

#
# Wizard dialog which accepts a keyboard user input.
# 
class WizardDialog_Keyboard(WizardDialog):
    def show(self, properties):
        log_debug('Executing keyboard wizard dialog for key: {0}'.format(self.property_key))
        originalText = properties[self.property_key] if self.property_key in properties else ''
        textInput = xbmc.Keyboard(originalText, self.title)
        textInput.doModal()
        if not textInput.isConfirmed(): 
            self._cancel()
            return None
        output = textInput.getText().decode('utf-8')

        return output

#
# Wizard dialog which shows a list of options to select from.
#
class WizardDialog_Selection(WizardDialog):
    def __init__(self, decoratorDialog, property_key, title, options,
                 customFunction = None, conditionalFunction = None):
        self.options = options
        super(WizardDialog_Selection, self).__init__(
            decoratorDialog, property_key, title, customFunction, conditionalFunction)

    def show(self, properties):
        log_debug('Executing selection wizard dialog for key: {0}'.format(self.property_key))
        selection = xbmcgui.Dialog().select(self.title, self.options)
        if selection < 0:
            self._cancel()
            return None
        output = self.options[selection]

        return output

#
# Wizard dialog which shows a list of options to select from.
# In comparison with the normal SelectionWizardDialog, this version allows a dictionary or key/value
# list as the selectable options. The selected key will be used.
# 
class WizardDialog_DictionarySelection(WizardDialog):
    def __init__(self, decoratorDialog, property_key, title, options,
                 customFunction = None, conditionalFunction = None):
        self.options = options
        super(WizardDialog_DictionarySelection, self).__init__(
            decoratorDialog, property_key, title, customFunction, conditionalFunction)

    def show(self, properties):
        log_debug('Executing dict selection wizard dialog for key: {0}'.format(self.property_key))
        dialog = KodiOrdDictionaryDialog()
        if callable(self.options):
            self.options = self.options(self.property_key, properties)
        output = dialog.select(self.title, self.options)
        if output is None:
            self._cancel()
            return None

        return output

#
# Wizard dialog which shows a filebrowser.
#
class WizardDialog_FileBrowse(WizardDialog):
    def __init__(self, decoratorDialog, property_key, title, browseType, filter,
                 customFunction = None, conditionalFunction = None):
        self.browseType = browseType
        self.filter = filter
        super(WizardDialog_FileBrowse, self).__init__(
            decoratorDialog, property_key, title, customFunction, conditionalFunction
        )

    def show(self, properties):
        log_debug('WizardDialog_FileBrowse::show() key = {0}'.format(self.property_key))
        originalPath = properties[self.property_key] if self.property_key in properties else ''

        if callable(self.filter):
            self.filter = self.filter(self.property_key, properties)
        output = xbmcgui.Dialog().browse(self.browseType, self.title, 'files', self.filter, False, False, originalPath).decode('utf-8')

        if not output:
            self._cancel()
            return None
       
        return output

#
# Wizard dialog which shows an input for one of the following types:
#    - xbmcgui.INPUT_ALPHANUM (standard keyboard)
#    - xbmcgui.INPUT_NUMERIC (format: #)
#    - xbmcgui.INPUT_DATE (format: DD/MM/YYYY)
#    - xbmcgui.INPUT_TIME (format: HH:MM)
#    - xbmcgui.INPUT_IPADDRESS (format: #.#.#.#)
#    - xbmcgui.INPUT_PASSWORD (return md5 hash of input, input is masked)
#
class WizardDialog_Input(WizardDialog):
    def __init__(self, decoratorDialog, property_key, title, inputType,
                 customFunction = None, conditionalFunction = None):
        self.inputType = inputType
        super(WizardDialog_Input, self).__init__(
            decoratorDialog, property_key, title, customFunction, conditionalFunction)

    def show(self, properties):
        log_debug('WizardDialog_Input::show() {} key = {}'.format(self.inputType, self.property_key))
        originalValue = properties[self.property_key] if self.property_key in properties else ''
        output = xbmcgui.Dialog().input(self.title, originalValue, self.inputType)
        if not output:
            self._cancel()
            return None

        return output

#
# Wizard dialog which shows you a message formatted with a value from the dictionary.
#
# Example:
#   dictionary item {'token':'roms'}
#   inputtext: 'I like {} a lot'
#   result message on screen: 'I like roms a lot'
#
# Formatting is optional
#
class WizardDialog_FormattedMessage(WizardDialog):
    def __init__(self, decoratorDialog, property_key, title, text,
                 customFunction = None, conditionalFunction = None):
        self.text = text
        super(WizardDialog_FormattedMessage, self).__init__(
            decoratorDialog, property_key, title, customFunction, conditionalFunction)

    def show(self, properties):
        log_debug('Executing message wizard dialog for key: {0}'.format(self.property_key))
        format_values = properties[self.property_key] if self.property_key in properties else ''
        full_text = self.text.format(format_values)
        output = xbmcgui.Dialog().ok(self.title, full_text)

        if not output:
            self._cancel()
            return None

        return output

#
# Wizard dialog which does nothing or shows anything.
# It only sets a certain property with the predefined value.
#
class WizardDialog_Dummy(WizardDialog):
    def __init__(self, decoratorDialog, property_key, predefinedValue,
                 customFunction = None, conditionalFunction = None):
        self.predefinedValue = predefinedValue
        super(WizardDialog_Dummy, self).__init__(
            decoratorDialog, property_key, None, customFunction, conditionalFunction)

    def show(self, properties):
        log_debug('WizardDialog_Dummy::show() {0} key = {0}'.format(self.property_key))

        return self.predefinedValue

#
# Kodi dialog with select box based on a list.
# preselect is int
# Returns the int index selected or None if dialog was canceled.
#
class KodiListDialog(object):
    def __init__(self):
        self.dialog = xbmcgui.Dialog()

    def select(self, title, options_list, preselect_idx = 0, use_details = False):
        # --- Execute select dialog menu logic ---
        # Kodi Krypton bug: if preselect is used then dialog never returns < 0 even if cancel
        # button is pressed. This bug has been solved in Leia.
        # See https://forum.kodi.tv/showthread.php?tid=337011
        if kodi_running_version >= KODI_VERSION_LEIA:
            selection = self.dialog.select(title, options_list, useDetails = use_details, preselect = preselect_idx)
        else:
            log_debug('Executing code < KODI_VERSION_LEIA to overcome select() bug.')
            selection = self.dialog.select(title, options_list, useDetails = use_details)
            
        if selection < 0:
            return None

        return selection

#
# Kodi dialog with select box based on a dictionary
#
class KodiOrdDictionaryDialog(object):
    def __init__(self):
        self.dialog = xbmcgui.Dialog()

    def select(self, title, options_odict, preselect = None, use_details = False):
        preselected_index = -1
        if preselect is not None:
            preselected_value = options_odict[preselect]
            preselected_index = options_odict.values().index(preselected_value)
        # --- Execute select dialog menu logic ---
        # Kodi Krypton bug: if preselect is used then dialog never returns < 0 even if cancel
        # button is pressed. This bug has been solved in Leia.
        # See https://forum.kodi.tv/showthread.php?tid=337011
        if kodi_running_version >= KODI_VERSION_LEIA:
            selection = self.dialog.select(title, options_odict.values(), useDetails = use_details, preselect = preselected_index)
        else:
            log_debug('Executing code < KODI_VERSION_LEIA to overcome select() bug.')
            selection = self.dialog.select(title, options_odict.values(), useDetails = use_details)

        if selection < 0:
            return None
        key = list(options_odict.keys())[selection]

        return key

# Progress dialog that can be closed and reopened.
# If the dialog is canceled this class remembers it forever.
class KodiProgressDialog(object):
    def __init__(self):
        self.title = 'Advanced Emulator Launcher'
        self.progress = 0
        self.flag_dialog_canceled = False
        self.dialog_active = False
        self.progressDialog = xbmcgui.DialogProgress()

    def startProgress(self, message1, num_steps = 100, message2 = None):
        self.num_steps = num_steps
        self.progress = 0
        self.dialog_active = True
        self.message1 = message1
        self.message2 = message2
        if self.message2:
            self.progressDialog.create(self.title, self.message1, self.message2)
        else:
            # The ' ' is to avoid a bug in Kodi progress dialog that keeps old messages 2
            # if an empty string is passed.
            self.progressDialog.create(self.title, self.message1, ' ')
        self.progressDialog.update(self.progress)

    # Update progress and optionally update messages as well.
    # If not messages specified then keep current message/s
    def updateProgress(self, step_index, message1 = None, message2 = None):
        self.progress = int((step_index * 100) / self.num_steps)
        # Update both messages
        if message1 and message2:
            self.message1 = message1
            self.message2 = message2
        # Update only message1 and deletes message2. There could be no message2 without a message1.
        elif message1:
            self.message1 = message1
            self.message2 = None
            self.progressDialog.update(self.progress, message1, ' ')
            return
        if self.message2:
            self.progressDialog.update(self.progress, self.message1, self.message2)
        else:
            # The ' ' is to avoid a bug in Kodi progress dialog that keeps old messages 2
            # if an empty string is passed.
            self.progressDialog.update(self.progress, self.message1, ' ')

    # Update dialog message but keep same progress. message2 is removed if any.
    def updateMessage(self, message1):
        self.message1 = message1
        self.message2 = None
        self.progressDialog.update(self.progress, self.message1, ' ')

    # Update message2 and keeps same progress and message1
    def updateMessage2(self, message2):
        self.message2 = message2
        self.progressDialog.update(self.progress, self.message1, self.message2)

    # Update dialog message but keep same progress.
    def updateMessages(self, message1, message2):
        self.message1 = message1
        self.message2 = message2
        self.progressDialog.update(self.progress, message1, message2)

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

    # Reopens a previously closed dialog, remembering the messages and the progress it had
    # when it was closed.
    def reopen(self):
        if self.message2:
            self.progressDialog.create(self.title, self.message1, self.message2)
        else:
            # The ' ' is to avoid a bug in Kodi progress dialog that keeps old messages 2
            # if an empty string is passed.
            self.progressDialog.create(self.title, self.message1, ' ')
        self.progressDialog.update(self.progress)
        self.dialog_active = True

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
# If runnining with Kodi Python interpreter use Kodi proper functions.
# If running with the standard Python interpreter use replacement functions.
# -------------------------------------------------------------------------------------------------
if UTILS_KODI_RUNTIME_AVAILABLE:
    log_debug   = log_debug_KR
    log_verb    = log_verb_KR
    log_info    = log_info_KR
    log_warning = log_warning_KR
    log_error   = log_error_KR
else:
    log_debug   = log_debug_Python
    log_verb    = log_verb_Python
    log_info    = log_info_Python
    log_warning = log_warning_Python
    log_error   = log_error_Python


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
# Utilities to test scrapers
# -------------------------------------------------------------------------------------------------
# Candidates
NAME_L      = 65
SCORE_L     = 5
ID_L        = 55
PLATFORM_L  = 15
SPLATFORM_L = 15
URL_L       = 70

# Metadata
TITLE_L     = 50
YEAR_L      = 4
GENRE_L     = 20
DEVELOPER_L = 10
NPLAYERS_L  = 10
ESRB_L      = 20
PLOT_L      = 70

# Assets
ASSET_ID_L        = 8
ASSET_NAME_L      = 60
ASSET_URL_THUMB_L = 100

# PUT functions to print things returned by Scraper object (which are common to all scrapers)
# into util.py, to be resused by all scraper tests.
def print_candidate_list(results):
    p_str = "{0} {1} {2} {3} {4}"
    print('Found {0} candidate/s'.format(len(results)))
    print(p_str.format(
        'Display name'.ljust(NAME_L), 'Score'.ljust(SCORE_L),
        'Id'.ljust(ID_L), 'Platform'.ljust(PLATFORM_L), 'SPlatform'.ljust(SPLATFORM_L)))
    print(p_str.format(
        '-'*NAME_L, '-'*SCORE_L, '-'*ID_L, '-'*PLATFORM_L, '-'*SPLATFORM_L))
    for game in results:
        display_name = text_limit_string(game['display_name'], NAME_L)
        score = text_limit_string(str(game['order']), SCORE_L)
        id = text_limit_string(str(game['id']), ID_L)
        platform = text_limit_string(str(game['platform']), PLATFORM_L)
        splatform = text_limit_string(str(game['scraper_platform']), SPLATFORM_L)
        print(p_str.format(
            display_name.ljust(NAME_L), score.ljust(SCORE_L), id.ljust(ID_L),
            platform.ljust(PLATFORM_L), splatform.ljust(SPLATFORM_L)))
    print('')

def print_game_metadata(metadata):
    title     = text_limit_string(metadata['title'], TITLE_L)
    year      = metadata['year']
    genre     = text_limit_string(metadata['genre'], GENRE_L)
    developer = text_limit_string(metadata['developer'], DEVELOPER_L)
    nplayers  = text_limit_string(metadata['nplayers'], NPLAYERS_L)
    esrb      = text_limit_string(metadata['esrb'], ESRB_L)
    plot      = text_limit_string(metadata['plot'], PLOT_L)

    p_str = "{0} {1} {2} {3} {4} {5} {6}"
    print('Displaying metadata for title "{0}"'.format(title))
    print(p_str.format(
        'Title'.ljust(TITLE_L), 'Year'.ljust(YEAR_L), 'Genre'.ljust(GENRE_L),
        'Developer'.ljust(DEVELOPER_L), 'NPlayers'.ljust(NPLAYERS_L), 'ESRB'.ljust(ESRB_L),
        'Plot'.ljust(PLOT_L)))
    print(p_str.format(
        '-'*TITLE_L, '-'*YEAR_L, '-'*GENRE_L, '-'*DEVELOPER_L, '-'*NPLAYERS_L, '-'*ESRB_L, '-'*PLOT_L))
    print(p_str.format(
        title.ljust(TITLE_L), year.ljust(YEAR_L), genre.ljust(GENRE_L), developer.ljust(DEVELOPER_L),
        nplayers.ljust(NPLAYERS_L), esrb.ljust(ESRB_L), plot.ljust(PLOT_L) ))
    print('')

def print_game_assets(image_list):
    # print('Found {0} image/s'.format(len(image_list)))
    p_str = "{0} {1} {2}"
    print(p_str.format(
        'Asset ID'.ljust(ASSET_ID_L), 'Name'.ljust(ASSET_NAME_L),
        'URL thumb'.ljust(ASSET_URL_THUMB_L)))
    print(p_str.format('-'*ASSET_ID_L, '-'*ASSET_NAME_L, '-'*ASSET_URL_THUMB_L))
    for image in image_list:
        id           = text_limit_string(str(image['asset_ID']), ASSET_ID_L)
        display_name = text_limit_string(image['display_name'], ASSET_NAME_L)
        url_thumb    = text_limit_string(image['url_thumb'], ASSET_URL_THUMB_L)
        print(p_str.format(
            id.ljust(ASSET_ID_L), display_name.ljust(ASSET_NAME_L),
            url_thumb.ljust(ASSET_URL_THUMB_L)))
    print('')