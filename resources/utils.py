# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher utilities and misc functions.
#

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
import sys
import os
import shutil
import time
import random
import hashlib
import urlparse
import re
import string
import fnmatch
import HTMLParser
import json
# NOTE binascii must not be used! See https://docs.python.org/2/library/binascii.html
import binascii
import base64
# from base64 import b64decode
# from base64 import b64encode
from abc import ABCMeta
from abc import abstractmethod
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
    import xbmcgui
    import xbmcplugin
    import xbmcaddon
    import xbmcvfs
    UTILS_KODI_RUNTIME_AVAILABLE = True
except:
    UTILS_KODI_RUNTIME_AVAILABLE = False

# --- AEL modules ---
from constants import *

# #################################################################################################
# #################################################################################################
# Standard Python utilities
# #################################################################################################
# #################################################################################################

# -------------------------------------------------------------------------------------------------
# OS utils
# -------------------------------------------------------------------------------------------------
# Determine interpreter running platform
# See http://stackoverflow.com/questions/446209/possible-values-from-sys-platform

# --- Determine the platform and cache all possible values for maximum speed ---
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
    return is_linux_bool

def is_linux():
    return is_android_bool

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

#
# Given a Category/Launcher name clean it so the cleaned srt can be used as a filename.
#  1) Convert any non-printable character into '_'
#  2) Convert spaces ' ' into '_'
#
def text_title_to_filename_str(title_str):
    cleaned_str_1 = ''.join([i if i in string.printable else '_' for i in title_str])
    cleaned_str_2 = cleaned_str_1.replace(' ', '_')

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
    s = HTMLParser.HTMLParser().unescape(s)

    if __debug_text_unescape_HTML:
        log_debug('text_unescape_HTML() output "{0}"'.format(s))

    return s

#
# Remove HTML tags
#
def text_remove_HTML_tags(s):
    p = re.compile(r'<.*?>')
    s = p.sub('', s)

    return s

def text_unescape_and_untag_HTML(s):
    s = text_unescape_HTML(s)
    s = text_remove_HTML_tags(s)

    return s

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
    
    title = title.replace('_', '')
    title = title.replace('-', '')
    title = title.replace(':', '')
    title = title.replace('.', '')
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
    tokens = text_get_ROM_basename_tokens(ROM_FN.getBase_noext())

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
            tokens_idx = range(0, len(tokens))
            tokens_idx.remove(index)
            tokens_nodisc_idx = list(tokens_idx)
            tokens_mdisc = [tokens[x] for x in tokens_nodisc_idx]
            MultDiscFound = True
            break

        # --- TOSEC/Trurip ---
        matchObj = re.match(r'\(Dis[ck] ([0-9]+) of ([0-9]+)\)', token)
        if matchObj:
            log_debug('text_get_multidisc_info() ### Matched TOSEC/Trurip multidisc ROM ###')
            tokens_idx = range(0, len(tokens))
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
        log_debug('text_get_multidisc_info() base_noext   "{0}"'.format(ROM_FN.getBase_noext()))
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
# Get extension of URL. Returns '' if not found.
#
def text_get_URL_extension(url):
    
    urlPath = FileNameFactory.create(url)
    return urlPath.getExt()

#
# Defaults to .jpg if URL extension cannot be determined
#
def text_get_image_URL_extension(url):
    ext = text_get_URL_extension(url)
    ret = '.jpg' if ext == '' else ext

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

    log_debug('misc_add_file_cache() Scanning OP "{0}"'.format(dir_FN.getOriginalPath()))

    file_list = dir_FN.scanFilesInPathAsFileNameObjects()
    # lower all filenames for easier matching
    file_set = [file.getBase().lower() for file in file_list]

    log_debug('misc_add_file_cache() Adding {0} files to cache'.format(len(file_set)))
    file_cache[dir_FN.getOriginalPath()] = file_set

#
# See misc_look_for_file() documentation below.
#
def misc_search_file_cache(dir_path, filename_noext, file_exts):
    # log_debug('misc_search_file_cache() Searching in  "{0}"'.format(dir_str))
    dir_str = dir_path.getOriginalPath()
    if dir_str not in file_cache:
        log_warning('Directory {0} not in file_cache'.format(dir_str))
        return None

    current_cache_set = file_cache[dir_str]
    for ext in file_exts:
        file_base = filename_noext + '.' + ext
        file_base = file_base.lower()
        #log_debug('misc_search_file_cache() file_Base = "{0}"'.format(file_base))
        if file_base in current_cache_set:
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

# -------------------------------------------------------------------------------------------------
# Utilities to test scrapers
# -------------------------------------------------------------------------------------------------
ID_LENGTH     = 70
NAME_LENGTH   = 60
GENRE_LENGTH  = 20
YEAR_LENGTH   = 4
STUDIO_LENGTH = 20
PLOT_LENGTH   = 70
URL_LENGTH    = 70

def print_scraper_list(scraper_obj_list):
    print('Scraper name')
    print('--------------------------------')
    for scraper_obj in scraper_obj_list:
        print('{0}'.format(scraper_obj.name))
    print('')

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

def print_game_metadata(scraperObj, results):
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
                                           'Year'.ljust(YEAR_LENGTH), 'Studio'.ljust(STUDIO_LENGTH),
                                           'Plot'.ljust(PLOT_LENGTH)))
        print("{0} {1} {2} {3} {4}".format('-'*NAME_LENGTH, '-'*GENRE_LENGTH, '-'*YEAR_LENGTH, 
                                           '-'*STUDIO_LENGTH, '-'*PLOT_LENGTH))
        print("{0} {1} {2} {3} {4}".format(title.ljust(NAME_LENGTH), genre.ljust(GENRE_LENGTH), 
                                           year.ljust(YEAR_LENGTH), studio.ljust(STUDIO_LENGTH),
                                           plot.ljust(PLOT_LENGTH)))

def print_game_image_list(scraperObj, results, asset_kind):
    # --- Get image list of first game ---
    if results:
        image_list = scraperObj.get_images(results[0], asset_kind)
        print('Found {0} image/s'.format(len(image_list)))
        print("{0} {1} {2}".format('Display name'.ljust(NAME_LENGTH),
                                   'ID'.ljust(ID_LENGTH), 
                                   'URL'.ljust(URL_LENGTH)))
        print("{0} {1} {2}".format('-'*NAME_LENGTH, '-'*URL_LENGTH, '-'*URL_LENGTH))
        for image in image_list:
            display_name  = text_limit_string(image['name'], NAME_LENGTH)
            id            = text_limit_string(image['id'], ID_LENGTH)
            url           = text_limit_string(image['URL'], URL_LENGTH)
            print("{0} {1} {2}".format(display_name.ljust(NAME_LENGTH), id.ljust(ID_LENGTH), url.ljust(URL_LENGTH)))
        print('\n')

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
    cert.sign(k, 'sha1')

    log_debug('Creating certificate file {0}'.format(cert_file_path.getOriginalPath()))
    data = crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
    cert_file_path.writeAll(data, 'wt')

    log_debug('Creating certificate key file {0}'.format(key_file_path.getOriginalPath()))
    data = crypto.dump_privatekey(crypto.FILETYPE_PEM, k)
    key_file_path.writeAll(data, 'wt')

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

# #################################################################################################
# #################################################################################################
# Filesystem utilities
# #################################################################################################
# #################################################################################################

# -------------------------------------------------------------------------------------------------
# Factory for creating new FileName instances.
# Can either create a FileName base on xmbcvfs or just normal os operations.
# -------------------------------------------------------------------------------------------------
class FileNameFactory():
    @staticmethod
    def create(pathString, no_xbmcvfs = False):

        if no_xbmcvfs:
            return StandardFileName(pathString)
        
        return KodiFileName(pathString)

# -------------------------------------------------------------------------------------------------
# Filesystem abstract base class
# This class and classes that inherit this one always take and return Unicode string paths.
# Decoding Unicode to UTF-8 or whatever must be done in the caller code.
#
# IMPROVE THE DOCUMENTATION OF THIS CLASS AND HOW IT HANDLES EXCEPTIONS AND ERROR REPORTING!!!
#
# A) Transform paths like smb://server/directory/ into \\server\directory\
# B) Use xbmc.translatePath() for paths starting with special://
# C) Uses xbmcvfs wherever possible
#
# -------------------------------------------------------------------------------------------------
class FileName():
    __metaclass__ = ABCMeta

    # pathString must be a Unicode string object
    def __init__(self, pathString):
        self.originalPath = pathString
        self.path         = pathString
        
        # --- Path transformation ---
        if self.originalPath.lower().startswith('smb:'):
            self.path = self.path.replace('smb:', '')
            self.path = self.path.replace('SMB:', '')
            self.path = self.path.replace('//', '\\\\')
            self.path = self.path.replace('/', '\\')

        elif self.originalPath.lower().startswith('special:'):
            self.path = xbmc.translatePath(self.path)

    # abstract protected method, to be implemented in child classes.
    # Will return a new instance of the desired child implementation.
    @abstractmethod
    def __create__(self, pathString):
        return FileName(pathString)

    def _join_raw(self, arg):
        self.path         = os.path.join(self.path, arg)
        self.originalPath = os.path.join(self.originalPath, arg)

        return self

    # Appends a string to path. Returns self FileName object
    def append(self, arg):
        self.path         = self.path + arg
        self.originalPath = self.originalPath + arg

        return self

    # >> Joins paths. Returns a new FileName object
    def pjoin(self, *args):
        child = self.__create__(self.originalPath)
        for arg in args:
            child._join_raw(arg)

        return child

    # Behaves like os.path.join()
    #
    # See http://blog.teamtreehouse.com/operator-overloading-python
    # other is a FileName object. other originalPath is expected to be a subdirectory (path
    # transformation not required)
    def __add__(self, other):
        current_path = self.originalPath
        if type(other) is FileName:  other_path = other.originalPath
        elif type(other) is unicode: other_path = other
        elif type(other) is str:     other_path = other.decode('utf-8')
        else: raise NameError('Unknown type for overloaded + in FileName object')
        new_path = os.path.join(current_path, other_path)
        child    = self.__create__(new_path)

        return child
        
    def escapeQuotes(self):
        self.path = self.path.replace("'", "\\'")
        self.path = self.path.replace('"', '\\"')

    def path_separator(self):
        count_backslash = self.originalPath.count('\\')
        count_forwardslash = self.originalPath.count('/')

        if count_backslash > count_forwardslash:
            return '\\'
        
        return '/'

    # ---------------------------------------------------------------------------------------------
    # Decomposes a file name path or directory into its constituents
    #   FileName.getOriginalPath()  Full path                                     /home/Wintermute/Sonic.zip
    #   FileName.getPath()          Full path                                     /home/Wintermute/Sonic.zip
    #   FileName.getPath_noext()    Full path with no extension                   /home/Wintermute/Sonic
    #   FileName.getDir()           Directory name of file. Does not end in '/'   /home/Wintermute/
    #   FileName.getBase()          File name with no path                        Sonic.zip
    #   FileName.getBase_noext()    File name with no path and no extension       Sonic
    #   FileName.getExt()           File extension                                .zip
    # ---------------------------------------------------------------------------------------------
    def getOriginalPath(self):
        return self.originalPath

    def getPath(self):
        return self.path

    def getPath_noext(self):
        root, ext = os.path.splitext(self.path)

        return root

    def getDir(self):
        return os.path.dirname(self.path)

    def getDirAsFileName(self):
        return self.__create__(self.getDir())

    def getBase(self):
        return os.path.basename(self.path)

    def getBase_noext(self):
        basename  = os.path.basename(self.path)
        root, ext = os.path.splitext(basename)
        
        return root

    def getExt(self):
        root, ext = os.path.splitext(self.path)
        return ext

    def switchExtension(self, targetExt):
        
        ext = self.getExt()
        copiedPath = self.originalPath
        
        if not targetExt.startswith('.'):
            targetExt = '.{0}'.format(targetExt)

        new_path = self.__create__(copiedPath.replace(ext, targetExt))
        return new_path
    
    # Checks the extension to determine the type of the file
    def is_image_file(self):
        ext = self.getExt()
        return ext.lower() in ['png', 'jpg', 'gif', 'bmp']

    def is_video_file(self):
        ext = self.getExt()
        return ext.lower() in ['mov', 'divx', 'xvid', 'wmv', 'avi', 'mpg', 'mpeg', 'mp4', 'mkv', 'avc']
    
    def is_document(self):
        ext = self.getExt()
        return ext.lower() in ['txt', 'pdf', 'doc']
    
    # ---------------------------------------------------------------------------------------------
    # Scanner functions
    # ---------------------------------------------------------------------------------------------
    @abstractmethod
    def scanFilesInPath(self, mask = '*.*'):
        return []

    @abstractmethod
    def scanFilesInPathAsFileNameObjects(self, mask = '*.*'):
        return []
    
    @abstractmethod
    def recursiveScanFilesInPath(self, mask = '*.*'):
        return []

    @abstractmethod
    def recursiveScanFilesInPathAsFileNameObjects(self, mask = '*.*'):
        return []

    def _decodeName(self, name):
        if type(name) == str:
            try:
                name = name.decode('utf8')
            except:
                name = name.decode('windows-1252')
        
        return name
    
    # ---------------------------------------------------------------------------------------------
    # Filesystem functions
    # ---------------------------------------------------------------------------------------------
    @abstractmethod
    def stat(self):
        return None
    
    @abstractmethod
    def exists(self):
        return None
    
    @abstractmethod
    def isdir(self):
        return False
        
    @abstractmethod
    def isfile(self):
        return False
    
    @abstractmethod
    def makedirs(self):
        pass
    
    @abstractmethod
    def unlink(self):
        pass
    
    @abstractmethod
    def rename(self, to):
        pass
    
    @abstractmethod
    def copy(self, to):        
        pass
                    
    # ---------------------------------------------------------------------------------------------
    # File IO functions
    # ---------------------------------------------------------------------------------------------
    
    @abstractmethod
    def readline(self):
        return None
    
    @abstractmethod
    def readAll(self):
        return None
    
    @abstractmethod
    def readAllUnicode(self, encoding='utf-8'):
        return None
    
    @abstractmethod
    def writeAll(self, bytes, flags='w'):
        pass
    
    @abstractmethod
    def write(self, bytes):
        pass
       
    @abstractmethod
    def open(self, flags):
        pass
      
    @abstractmethod
    def close(self):
        pass

    # Opens file and reads xml. Returns the root of the XML!
    def readXml(self):
        data = self.readAll()
        root = ET.fromstring(data)
        return root

    # Opens JSON file and reads it
    def readJson(self):
        contents = self.readAllUnicode()
        return json.loads(contents)

    # Opens INI file and reads it
    def readIniFile(self):
        import ConfigParser
    
        config = ConfigParser.ConfigParser()
        config.readfp(self.open('r'))

        return config

    # Opens a propery file and reads it
    # Reads a given properties file with each line of the format key=value.  Returns a dictionary containing the pairs.
    def readPropertyFile(self):
        import csv
        
        file_contents = self.readAll()
        file_lines = file_contents.splitlines()

        result={ }
        reader = csv.reader(file_lines, delimiter=str('='), quoting=csv.QUOTE_NONE)
        for row in reader:
            if len(row) != 2:
                raise csv.Error("Too many fields on row with contents: "+str(row))
            result[row[0].strip()] = row[1].strip().lstrip('"').rstrip('"')
        
        return result

    # --- Configure JSON writer ---
    # >> json_unicode is either str or unicode
    # >> See https://docs.python.org/2.7/library/json.html#json.dumps
    # unicode(json_data) auto-decodes data to unicode if str
    # NOTE More compact JSON files (less blanks) load faster because size is smaller.
    def writeJson(self, raw_data, JSON_indent = 1, JSON_separators = (',', ':')):
        json_data = json.dumps(raw_data, ensure_ascii = False, sort_keys = True, 
                                indent = JSON_indent, separators = JSON_separators)
        self.writeAll(unicode(json_data).encode('utf-8'))

    # Opens file and writes xml. Give xml root element.
    def writeXml(self, xml_root):
        data = ET.tostring(xml_root)
        self.writeAll(data)

    def __str__(self):
        """Overrides the default implementation"""
        return self.getOriginalPath()

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, FileName):
            return self.getOriginalPath().lower() == other.getOriginalPath().lower()
        
        return False

    def __ne__(self, other):
        """Overrides the default implementation (unnecessary in Python 3)"""
        return not self.__eq__(other)

# -------------------------------------------------------------------------------------------------
# Kodi Virtual Filesystem helper class.
# Implementation of the FileName helper class which supports the xbmcvfs libraries.
#
# -------------------------------------------------------------------------------------------------
class KodiFileName(FileName):
    
    def __create__(self, pathString):
        return KodiFileName(pathString)

    # ---------------------------------------------------------------------------------------------
    # Scanner functions
    # ---------------------------------------------------------------------------------------------
    def scanFilesInPath(self, mask = '*.*'):
        files = []

        subdirectories, filenames = xbmcvfs.listdir(self.originalPath)
        for filename in fnmatch.filter(filenames, mask):
            files.append(os.path.join(self.originalPath, self._decodeName(filename)))

        return files

    def scanFilesInPathAsFileNameObjects(self, mask = '*.*'):
        files = []
        
        subdirectories, filenames = xbmcvfs.listdir(self.originalPath)
        for filename in fnmatch.filter(filenames, mask):
            filePath = self.pjoin(self._decodeName(filename))
            files.append(self.__create__(filePath.getOriginalPath()))

        return files

    def recursiveScanFilesInPath(self, mask = '*.*'):
        files = []
        
        subdirectories, filenames = xbmcvfs.listdir(str(self.originalPath))
        for filename in fnmatch.filter(filenames, mask):
            filePath = self.pjoin(self._decodeName(filename))
            files.append(filePath.getOriginalPath())

        for subdir in subdirectories:
            subPath = self.pjoin(self._decodeName(subdir))
            subPathFiles = subPath.recursiveScanFilesInPath(mask)
            files.extend(subPathFiles)

        return files
    
    def recursiveScanFilesInPathAsFileNameObjects(self, mask = '*.*'):
        files = []
        
        subdirectories, filenames = xbmcvfs.listdir(str(self.originalPath))
        for filename in fnmatch.filter(filenames, mask):
            filePath = self.pjoin(self._decodeName(filename))
            files.append(self.__create__(filePath.getOriginalPath()))

        for subdir in subdirectories:
            subPath = self.pjoin(self._decodeName(subdir))
            subPathFiles = subPath.recursiveScanFilesInPathAsFileNameObjects(mask)
            files.extend(subPathFiles)

        return files

    # ---------------------------------------------------------------------------------------------
    # Filesystem functions
    # ---------------------------------------------------------------------------------------------
    def stat(self):
        return xbmcvfs.Stat(self.originalPath)

    def exists(self):
        return xbmcvfs.exists(self.originalPath)

    # Warning: not suitable for xbmcvfs paths yet
    def isdir(self):
        
        if not self.exists():
            return False

        try:
            self.open('r')
            self.close()
        except:
            return True
        
        return False
        #return os.path.isdir(self.path)
        
    # Warning: not suitable for xbmcvfs paths yet
    def isfile(self):

        if not self.exists():
            return False

        return not self.isdir()
        #return os.path.isfile(self.path)

    def makedirs(self):
        
        if not self.exists():
            xbmcvfs.mkdirs(self.originalPath)

    def unlink(self):

        if self.isfile():
            xbmcvfs.delete(self.originalPath)

            # hard delete if it doesnt succeed
            #log_debug('xbmcvfs.delete() failed, applying hard delete')
            if self.exists():
                os.remove(self.path)
        else:
            xbmcvfs.rmdir(self.originalPath)

    def rename(self, to):

        if self.isfile():
            xbmcvfs.rename(self.originalPath, to.getOriginalPath())
        else:
            os.rename(self.path, to.getPath())

    def copy(self, to):        
        xbmcvfs.copy(self.getOriginalPath(), to.getOriginalPath())
                    
    # ---------------------------------------------------------------------------------------------
    # File IO functions
    # ---------------------------------------------------------------------------------------------
    
    def readline(self, encoding='utf-8'):
        if self.fileHandle is None:
            raise OSError('file not opened')

        line = u''
        char = self.fileHandle.read(1)
        if char is '':
            return ''

        while char and char != u'\n':
            line += unicode(char, encoding)
            char = self.fileHandle.read(1)

        return line

    def readAll(self):
        contents = None
        file = xbmcvfs.File(self.originalPath)
        contents = file.read()
        file.close()

        return contents
    
    def readAllUnicode(self, encoding='utf-8'):
        contents = None
        file = xbmcvfs.File(self.originalPath)
        contents = file.read()
        file.close()

        return unicode(contents, encoding)
    
    def writeAll(self, bytes, flags='w'):
        file = xbmcvfs.File(self.originalPath, flags)
        file.write(bytes)
        file.close()

    def write(self, bytes):
       if self.fileHandle is None:
           raise OSError('file not opened')

       self.fileHandle.write(bytes)

    def open(self, flags):
        self.fileHandle = xbmcvfs.File(self.originalPath, flags)
        return self
        
    def close(self):
        if self.fileHandle is None:
           raise OSError('file not opened')

        self.fileHandle.close()
        self.fileHandle = None
        
# -------------------------------------------------------------------------------------------------
# Standard Filesystem helper class.
# Implementation of the FileName helper class which just uses standard os operations.
#
# -------------------------------------------------------------------------------------------------
class StandardFileName(FileName):
    
    def __create__(self, pathString):
        return StandardFileName(pathString)

    # ---------------------------------------------------------------------------------------------
    # Scanner functions
    # ---------------------------------------------------------------------------------------------
    def scanFilesInPath(self, mask = '*.*'):
        files = []

        entries = os.listdir(self.path)
        for filename in fnmatch.filter(entries, mask):
            files.append(os.path.join(self.path, self._decodeName(filename)))

        return files

    def scanFilesInPathAsFileNameObjects(self, mask = '*.*'):
        files = []
        
        entries = os.listdir(self.path)
        for filename in fnmatch.filter(entries, mask):
            filePath = self.pjoin(self._decodeName(filename))
            files.append(self.__create__(filePath.getPath()))

        return files

    def recursiveScanFilesInPath(self, mask = '*.*'):
        files = []

        for root, dirs, foundfiles in os.walk(self.path):
            for filename in fnmatch.filter(foundfiles, mask):
                filePath = self.pjoin(self._decodeName(filename))
                files.append(filePath.getPath())

        return files
        
    def recursiveScanFilesInPathAsFileNameObjects(self, mask = '*.*'):
        files = []
        
        for root, dirs, foundfiles in os.walk(self.path):
            for filename in fnmatch.filter(foundfiles, mask):
                filePath = self.__create__(fileName)
                files.append(filePath)

        return files

    # ---------------------------------------------------------------------------------------------
    # Filesystem functions
    # ---------------------------------------------------------------------------------------------
    def stat(self):
        return os.stat(self.path)

    def exists(self):
        return os.path.exists(self.path)

    def isdir(self):
        return os.path.isdir(self.path)
        
    def isfile(self):
        return os.path.isfile(self.path)

    def makedirs(self):
        if not os.path.exists(self.path): 
            os.makedirs(self.path)

    # os.remove() and os.unlink() are exactly the same.
    def unlink(self):
        os.unlink(self.path)

    def rename(self, to):
        os.rename(self.path, to.getPath())

    def copy(self, to):        
        shutil.copy2(self.getPath(), to.getPath())
     
    # ---------------------------------------------------------------------------------------------
    # File IO functions
    # ---------------------------------------------------------------------------------------------
    
    def readline(self):
        if self.fileHandle is None:
            raise OSError('file not opened')

        return self.fileHandle.readline()

    def readAll(self):
        contents = None
        with open(self.path, 'r') as f:
            contents = f.read()
        
        return contents
    
    def readAllUnicode(self, encoding='utf-8'):
        contents = None        
        with open(self.path, 'r') as f:
            contents = f.read()
        
        return unicode(contents, encoding)
    
    def writeAll(self, bytes, flags='w'):
        with open(self.path, flags) as file:
            file.write(bytes)

    def write(self, bytes):
       if self.fileHandle is None:
           raise OSError('file not opened')

       self.fileHandle.write(bytes)

    def open(self, flags):
        self.fileHandle = os.open(self.path, flags)
        return self
        
    def close(self):
        if self.fileHandle is None:
           raise OSError('file not opened')

        self.fileHandle.close()
        self.fileHandle = None

# #################################################################################################
# #################################################################################################
# Kodi utilities
# #################################################################################################
# #################################################################################################

# --- Constants -----------------------------------------------------------------------------------
LOG_ERROR   = 0
LOG_WARNING = 1
LOG_INFO    = 2
LOG_VERB    = 3
LOG_DEBUG   = 4

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
        log_text = u'AML DEBUG: ' + str_text
        xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGNOTICE)

def log_verb_KR(str_text):
    if current_log_level >= LOG_VERB:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = u'AML VERB : ' + str_text
        xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGNOTICE)

def log_info_KR(str_text):
    if current_log_level >= LOG_INFO:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = u'AML INFO : ' + str_text
        xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGNOTICE)

def log_warning_KR(str_text):
    if current_log_level >= LOG_WARNING:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = u'AML WARN : ' + str_text
        xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGWARNING)

def log_error_KR(str_text):
    if current_log_level >= LOG_ERROR:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = u'AML ERROR: ' + str_text
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
def kodi_dialog_OK(row1, row2 = '', row3 = '', title = 'Advanced Emulator Launcher'):
    return xbmcgui.Dialog().ok(title, row1, row2, row3)

#
# Returns True is YES was pressed, returns False if NO was pressed or dialog canceled.
#
def kodi_dialog_yesno(row1, row2 = '', row3 = '', title = 'Advanced Emulator Launcher'):
    ret = xbmcgui.Dialog().yesno(title, row1, row2, row3)

    return ret

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
# NOTE I think Krypton introduced new API functions to activate the busy dialog window. Check that
#      out!
# NOTE Deprecated in Leia! Do not use busydialogs anymore!!!!!
#
def kodi_busydialog_ON():
    xbmc.executebuiltin('ActivateWindow(busydialog)')

def kodi_busydialog_OFF():
    xbmc.executebuiltin('Dialog.Close(busydialog)')

def kodi_refresh_container():
    log_debug('kodi_refresh_container()')
    xbmc.executebuiltin('Container.Refresh')

def kodi_toogle_fullscreen():
    json_str = ('{"jsonrpc" : "2.0", "id" : "1",'
                '"method" : "Input.ExecuteAction",'
                '"params" : {"action" : "togglefullscreen"}}')

    xbmc.executeJSONRPC(json_str)

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
class KodiWizardDialog():
    __metaclass__ = ABCMeta

    def __init__(self, property_key, title, decoratorDialog, customFunction = None, conditionalFunction = None):
        self.title = title
        self.property_key = property_key
        self.decoratorDialog = decoratorDialog
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
        
        if self.cancelled:
            return False

        if self.customFunction is not None:
            output = self.customFunction(output, self.property_key, properties)

        if self.property_key:
            properties[self.property_key] = output
            log_debug('Assigned properties[{0}] value: {1}'.format(self.property_key, output))

        return True

    @abstractmethod
    def show(self, properties):
        return True

    def _cancel(self):
        self.cancelled = True

#
# Wizard dialog which accepts a keyboard user input.
# 
class KodiKeyboardWizardDialog(KodiWizardDialog):
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
class KodiSelectionWizardDialog(KodiWizardDialog):
    def __init__(self, property_key, title, options, decoratorDialog, customFunction = None, conditionalFunction = None):
        self.options = options
        super(SelectionWizardDialog, self).__init__(property_key, title, decoratorDialog, customFunction, conditionalFunction)

    def show(self, properties):
        log_debug('Executing selection wizard dialog for key: {0}'.format(self.property_key))
        dialog = xbmcgui.Dialog()
        selection = dialog.select(self.title, self.options)

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
class KodiDictionarySelectionWizardDialog(KodiWizardDialog):
    def __init__(self, property_key, title, options, decoratorDialog, customFunction = None, conditionalFunction = None):
        self.options = options
        super(DictionarySelectionWizardDialog, self).__init__(property_key, title, decoratorDialog, customFunction, conditionalFunction)

    def show(self, properties):
        log_debug('Executing dict selection wizard dialog for key: {0}'.format(self.property_key))
        dialog = DictionaryDialog()
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
class KodiFileBrowseWizardDialog(KodiWizardDialog):
    def __init__(self, property_key, title, browseType, filter, decoratorDialog, customFunction = None, conditionalFunction = None):
        self.browseType = browseType
        self.filter = filter
        super(FileBrowseWizardDialog, self).__init__(property_key, title, decoratorDialog, customFunction, conditionalFunction)

    def show(self, properties):
        log_debug('Executing file browser wizard dialog for key: {0}'.format(self.property_key))
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
class KodiInputWizardDialog(KodiWizardDialog):
    def __init__(self, property_key, title, inputType, decoratorDialog, customFunction = None, conditionalFunction = None):
        self.inputType = inputType
        super(InputWizardDialog, self).__init__(property_key, title, decoratorDialog, customFunction, conditionalFunction)

    def show(self, properties):
        log_debug('Executing {0} input wizard dialog for key: {1}'.format(self.inputType, self.property_key))
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
class KodiFormattedMessageWizardDialog(KodiWizardDialog):
    def __init__(self, property_key, title, text, decoratorDialog, customFunction = None, conditionalFunction = None):
        self.text = text
        super(FormattedMessageWizardDialog, self).__init__(property_key, title, decoratorDialog, customFunction, conditionalFunction)

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
class KodiDummyWizardDialog(KodiWizardDialog):
    def __init__(self, property_key, predefinedValue, decoratorDialog, customFunction = None, conditionalFunction = None):
        self.predefinedValue = predefinedValue
        super(DummyWizardDialog, self).__init__(property_key, None, decoratorDialog, customFunction, conditionalFunction)

    def show(self, properties):
        
        log_debug('Executing dummy wizard dialog for key: {0}'.format(self.property_key))
        return self.predefinedValue

#
# Kodi dialog with select box based on a dictionary
#
class KodiDictionaryDialog(object):
    def __init__(self):
        self.dialog = xbmcgui.Dialog()

    def select(self, title, dictOptions, preselect = None):
        preselected_index = -1
        if preselect is not None:
            preselected_value = dictOptions[preselect]
            preselected_index = dictOptions.values().index(preselected_value)

        selection = self.dialog.select(title, dictOptions.values(), preselect = preselected_index)

        if selection < 0:
            return None
        
        key = list(dictOptions.keys())[selection]
        return key

class KodiProgressDialogStrategy(object):
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

        if not self.verbose:
            return

        self.progressDialog.update(self.progress, message1, message2)

    def _isProgressCanceled(self):
        return self.progressDialog.iscanceled()

    def _endProgressPhase(self, canceled=False):
        
        if not canceled:
            self.progressDialog.update(100)

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
