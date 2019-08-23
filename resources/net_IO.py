# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher network IO module
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

# --- Python standard library ---
from __future__ import unicode_literals
import sys
import random
import urllib2
import os

# --- AEL packages ---
from .utils import *

# --- GLOBALS -----------------------------------------------------------------
# Firefox user agents
# USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/68.0'
USER_AGENT = 'Mozilla/5.0 (X11; Linux i586; rv:31.0) Gecko/20100101 Firefox/68.0'

# Where did this user agent come from?
# USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31';

# ---  -----------------------------------------------------------------
def net_get_random_UserAgent():
    platform = random.choice(['Macintosh', 'Windows', 'X11'])
    if platform == 'Macintosh':
        os_str  = random.choice(['68K', 'PPC'])
    elif platform == 'Windows':
        os_str  = random.choice([
            'Win3.11', 'WinNT3.51', 'WinNT4.0', 'Windows NT 5.0', 'Windows NT 5.1', 
            'Windows NT 5.2', 'Windows NT 6.0', 'Windows NT 6.1', 'Windows NT 6.2', 
            'Win95', 'Win98', 'Win 9x 4.90', 'WindowsCE'])
    elif platform == 'X11':
        os_str  = random.choice(['Linux i686', 'Linux x86_64'])
    browser = random.choice(['chrome', 'firefox', 'ie'])
    if browser == 'chrome':
        webkit = str(random.randint(500, 599))
        version = str(random.randint(0, 24)) + '.0' + str(random.randint(0, 1500)) + '.' + str(random.randint(0, 999))
        return 'Mozilla/5.0 (' + os_str + ') AppleWebKit/' + webkit + '.0 (KHTML, live Gecko) Chrome/' + version + ' Safari/' + webkit

    elif browser == 'firefox':
        year = str(random.randint(2000, 2012))
        month = random.randint(1, 12)
        if month < 10:
            month = '0' + str(month)
        else:
            month = str(month)
        day = random.randint(1, 30)
        if day < 10:
            day = '0' + str(day)
        else:
            day = str(day)
        gecko = year + month + day
        version = random.choice([
            '1.0', '2.0', '3.0', '4.0', '5.0', '6.0', '7.0', '8.0', 
            '9.0', '10.0', '11.0', '12.0', '13.0', '14.0', '15.0'])
        return 'Mozilla/5.0 (' + os_str + '; rv:' + version + ') Gecko/' + gecko + ' Firefox/' + version

    elif browser == 'ie':
        version = str(random.randint(1, 10)) + '.0'
        engine = str(random.randint(1, 5)) + '.0'
        option = random.choice([True, False])
        if option == True:
            token = random.choice(['.NET CLR', 'SV1', 'Tablet PC', 'Win64; IA64', 'Win64; x64', 'WOW64']) + '; '
        elif option == False:
            token = ''
        return 'Mozilla/5.0 (compatible; MSIE ' + version + '; ' + os_str + '; ' + token + 'Trident/' + engine + ')'

def net_download_img(img_url, file_path):
    try:
        req = urllib2.Request(img_url)
        # req.add_unredirected_header('User-Agent', net_get_random_UserAgent())
        req.add_unredirected_header('User-Agent', USER_AGENT)
        f = open(file_path, 'wb')
        f.write(urllib2.urlopen(req, timeout = 120).read())
        f.close()
        remove_destination_file = False
    # If an exception happens record it in the log and do nothing.
    # This must be fixed. If an error happened when downloading stuff caller code must
    # known to take action.
    except IOError as ex:
        log_error('(IOError exception) In net_download_img()')
        log_error('Message: {0}'.format(str(ex)))
        remove_destination_file = True
    except Exception as ex:
        log_error('(General exception) In net_download_img()')
        log_error('Message: {0}'.format(str(ex)))
        remove_destination_file = True

    # Remove destination file to avoid 0 sized files or corrupt files.
    # On Windows os.remove() causes a exceptions.WindowsError 
    # WindowsError: [Error 32] The process cannot access the file because it is being used
    # by another process
    # if remove_destination_file:
    #     log_error('Deleting file "{}"'.format(file_path))
    #     os.remove(file_path)

#
# User agent is fixed and defined in global var USER_AGENT
#
# @param url: [Unicode string] URL to open
# @param url_log: [Unicode string] If not None this URL will be used in the logs.
# @return: [tuple] Tuple of strings. First tuple element is a string with the web content as 
#          a Unicode string or None if network error/exception. Second tuple element is the 
#          HTTP status code as integer or None if network error/exception.
def net_get_URL(url, url_log = None):
    req = urllib2.Request(url)
    req.add_unredirected_header('User-Agent', USER_AGENT)
    if url_log is None:
        log_debug('net_get_URL() GET URL "{}"'.format(req.get_full_url()))
    else:
        log_debug('net_get_URL() GET URL "{}"'.format(url_log))

    page_bytes = http_code = None
    try:
        f = urllib2.urlopen(req, timeout = 120)
        page_bytes = f.read()
        http_code = f.getcode()
        f.close()
    # If the server returns an HTTP status code then make sure http_code has the error code
    # and page_bytes the message.
    except urllib2.HTTPError as ex:
        http_code = ex.code
        page_bytes = unicode(ex.reason)
        log_error('(HTTPError) In net_get_URL()')
        log_error('(HTTPError) Object type "{}"'.format(type(ex)))
        log_error('(HTTPError) Message "{}"'.format(str(ex)))
        log_error('(HTTPError) Code {}'.format(http_code))
        return page_bytes, http_code
    # If an unknown exception happens return empty data.
    except Exception as ex:
        log_error('(Exception) In net_get_URL()')
        log_error('(Exception) Object type "{}"'.format(type(ex)))
        log_error('(Exception) Message "{}"'.format(str(ex)))
        return page_bytes, http_code
    log_debug('net_get_URL() Read {} bytes'.format(len(page_bytes)))
    log_debug('net_get_URL() HTTP status code {}'.format(http_code))

    # --- Convert to Unicode ---
    encoding = f.headers['content-type'].split('charset=')[-1]
    page_data = net_decode_URL_data(page_bytes, encoding)

    return page_data, http_code

def net_get_URL_oneline(url, url_log = None):
    page_data, http_code = net_get_URL(url, url_log)
    if page_data is None: return (page_data, http_code)

    # --- Put all page text into one line ---
    page_data = page_data.replace('\r\n', '')
    page_data = page_data.replace('\n', '')

    return page_data, http_code

# Do HTTP request with POST: https://docs.python.org/2/library/urllib2.html#urllib2.Request
def net_post_URL(url, data):
    page_data = ''
    req = urllib2.Request(url, data)
    req.add_unredirected_header('User-Agent', USER_AGENT)
    req.add_header("Content-type", "application/x-www-form-urlencoded")
    req.add_header("Acept", "text/plain")
    log_debug('net_post_URL() POST URL "{0}"'.format(req.get_full_url()))

    try:
        f = urllib2.urlopen(req, timeout = 120)
        page_bytes = f.read()
        f.close()
    # If an exception happens return empty data.
    except IOError as ex:
        log_error('(IOError exception) In net_get_URL()')
        log_error('Message: {0}'.format(str(ex)))
        return page_data
    except Exception as ex:
        log_error('(General exception) In net_get_URL()')
        log_error('Message: {0}'.format(str(ex)))
        return page_data

    num_bytes = len(page_bytes)
    log_debug('net_post_URL() Read {0} bytes'.format(num_bytes))

    # --- Convert page data to Unicode ---
    encoding = f.headers['content-type'].split('charset=')[-1]
    page_data = net_decode_URL_data(page_bytes, encoding)

    return page_data

def net_decode_URL_data(page_bytes, encoding):
    # --- Try to guess enconding ---
    if   encoding == 'text/html':                             encoding = 'utf-8'
    elif encoding == 'application/json':                      encoding = 'utf-8'
    elif encoding == 'text/plain' and 'UTF-8' in page_bytes:  encoding = 'utf-8'
    elif encoding == 'text/plain' and 'UTF-16' in page_bytes: encoding = 'utf-16'
    else:                                                     encoding = 'utf-8'
    # log_debug('net_decode_URL_data() encoding = "{0}"'.format(encoding))

    # --- Decode ---
    if encoding == 'utf-16':
        page_data = page_bytes.encode('utf-16')
    else:
        # python3: page_data = str(page_bytes, encoding)
        page_data = unicode(page_bytes, encoding)

    return page_data
