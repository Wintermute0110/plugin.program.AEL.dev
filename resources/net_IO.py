# -*- coding: utf-8 -*-

# Copyright (c) 2016-2021 Wintermute0110 <wintermute0110@gmail.com>
# Portions (c) 2010-2015 Angelscry
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# Advanced Emulator Launcher network IO module.

# --- Modules/packages in this plugin ---
from .constants import *
from .utils import *

# --- Python standard library ---
import os
import random
import ssl
import sys
if ADDON_RUNNING_PYTHON_2:
    import urllib2
elif ADDON_RUNNING_PYTHON_3:
    import urllib.request
    import urllib.error
else:
    raise TypeError('Undefined Python runtime version.')

# --- GLOBALS -----------------------------------------------------------------
# Firefox user agents
# USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0'
USER_AGENT = 'Mozilla/5.0 (X11; Linux i686; rv:88.0) Gecko/20100101 Firefox/88.0'

def net_get_random_UserAgent():
    platform = random.choice(['Macintosh', 'Windows', 'X11'])
    if platform == 'Macintosh':
        os_str  = random.choice(['68K', 'PPC'])
    elif platform == 'Windows':
        os_str  = random.choice([
            'Win3.11', 'WinNT3.51', 'WinNT4.0', 'Windows NT 5.0', 'Windows NT 5.1',
            'Windows NT 5.2', 'Windows NT 6.0', 'Windows NT 6.1', 'Windows NT 6.2',
            'Win95', 'Win98', 'Win 9x 4.90', 'WindowsCE',
        ])
    elif platform == 'X11':
        os_str  = random.choice(['Linux i686', 'Linux x86_64'])
    browser = random.choice(['chrome', 'firefox', 'ie'])
    if browser == 'chrome':
        webkit = text_type(random.randint(500, 599))
        version = text_type(random.randint(0, 24)) + '.0' + \
            text_type(random.randint(0, 1500)) + '.' + text_type(random.randint(0, 999))
        return 'Mozilla/5.0 (' + os_str + ') AppleWebKit/' + \
            webkit + '.0 (KHTML, live Gecko) Chrome/' + version + ' Safari/' + webkit

    elif browser == 'firefox':
        year = text_type(random.randint(2000, 2012))
        month = random.randint(1, 12)
        if month < 10:
            month = '0' + text_type(month)
        else:
            month = text_type(month)
        day = random.randint(1, 30)
        if day < 10:
            day = '0' + text_type(day)
        else:
            day = text_type(day)
        gecko = year + month + day
        version = random.choice([
            '1.0', '2.0', '3.0', '4.0', '5.0', '6.0', '7.0', '8.0',
            '9.0', '10.0', '11.0', '12.0', '13.0', '14.0', '15.0',
        ])
        return 'Mozilla/5.0 (' + os_str + '; rv:' + version + ') Gecko/' + gecko + ' Firefox/' + version

    elif browser == 'ie':
        version = text_type(random.randint(1, 10)) + '.0'
        engine = text_type(random.randint(1, 5)) + '.0'
        option = random.choice([True, False])
        if option == True:
            token = random.choice(['.NET CLR', 'SV1', 'Tablet PC', 'Win64; IA64', 'Win64; x64', 'WOW64']) + '; '
        elif option == False:
            token = ''
        return 'Mozilla/5.0 (compatible; MSIE ' + version + '; ' + os_str + '; ' + token + 'Trident/' + engine + ')'

def net_download_img(img_url, file_path):
    # --- Download image to a buffer in memory ---
    # If an exception happens here no file is created (avoid creating files with 0 bytes).
    try:
        if ADDON_RUNNING_PYTHON_2:
            req = urllib2.Request(img_url)
            # req.add_unredirected_header('User-Agent', net_get_random_UserAgent())
            req.add_unredirected_header('User-Agent', USER_AGENT)
            # Ignore exception IOError SSL: CERTIFICATE_VERIFY_FAILED
            # response = urllib2.urlopen(req, timeout = 120)
            response = urllib2.urlopen(req, timeout = 120, context = ssl._create_unverified_context())
            img_buf = response.read()
            response.close()
        elif ADDON_RUNNING_PYTHON_3:
            req = urllib.request.Request(img_url)
            req.add_unredirected_header('User-Agent', USER_AGENT)
            response = urllib.request.urlopen(req, timeout = 120, context = ssl._create_unverified_context())
            img_buf = response.read()
            response.close()
    # If an exception happens record it in the log and do nothing.
    # This must be fixed. If an error happened when downloading stuff caller code must
    # known to take action.
    except IOError as ex:
        log_error('(IOError) In net_download_img(), network code.')
        log_error('(IOError) Object type "{}"'.format(type(ex)))
        log_error('(IOError) Message "{}"'.format(text_type(ex)))
        return
    except Exception as ex:
        log_error('(Exception) In net_download_img(), network code.')
        log_error('(Exception) Object type "{}"'.format(type(ex)))
        log_error('(Exception) Message "{}"'.format(text_type(ex)))
        return

    # --- Write image file to disk ---
    # There should be no more 0 size files with this code.
    try:
        f = open(file_path, 'wb')
        f.write(img_buf)
        f.close()
    except IOError as ex:
        log_error('(IOError) In net_download_img(), disk code.')
        log_error('(IOError) Object type "{}"'.format(type(ex)))
        log_error('(IOError) Message "{}"'.format(text_type(ex)))
    except Exception as ex:
        log_error('(Exception) In net_download_img(), disk code.')
        log_error('(Exception) Object type "{}"'.format(type(ex)))
        log_error('(Exception) Message "{}"'.format(text_type(ex)))

# User agent is fixed and defined in global var USER_AGENT
# https://docs.python.org/2/library/urllib2.html
#
# @param url: [Unicode string] URL to open
# @param url_log: [Unicode string] If not None this URL will be used in the logs.
# @return: [tuple] Tuple of strings. First tuple element is a string with the web content as
#          a Unicode string or None if network error/exception. Second tuple element is the
#          HTTP status code as integer or None if network error/exception.
def net_get_URL(url, url_log = None):
    page_bytes, http_code = None, None
    if url_log is not None: log_debug('net_get_URL() GET URL "{}"'.format(url_log))
    if ADDON_RUNNING_PYTHON_2:
        try:
            req = urllib2.Request(url)
            req.add_unredirected_header('User-Agent', USER_AGENT)
            if url_log is None: log_debug('net_get_URL() GET URL "{}"'.format(req.get_full_url()))
            response = urllib2.urlopen(req, timeout = 120)
            page_bytes = response.read()
            http_code = response.getcode()
            encoding = response.headers['content-type'].split('charset=')[-1]
            response.close()
        # If the server returns an HTTP status code then make sure http_code has
        # the error code and page_bytes the message.
        except urllib2.HTTPError as ex:
            http_code = ex.code
            # Try to read contents of the web page at all costs.
            # If it fails get error string from the exception object.
            try:
                page_bytes = ex.read()
                ex.close()
            except:
                page_bytes = text_type(ex.reason)
            log_error('(HTTPError) In net_get_URL()')
            log_error('(HTTPError) Object type "{}"'.format(type(ex)))
            log_error('(HTTPError) Message "{}"'.format(text_type(ex)))
            log_error('(HTTPError) Code {}'.format(http_code))
            return page_bytes, http_code
        # If an unknown exception happens return empty data.
        except Exception as ex:
            log_error('(Exception) In net_get_URL()')
            log_error('(Exception) Object type "{}"'.format(type(ex)))
            log_error('(Exception) Message "{}"'.format(text_type(ex)))
            return page_bytes, http_code
    elif ADDON_RUNNING_PYTHON_3:
        try:
            req = urllib.request.Request(url)
            req.add_unredirected_header('User-Agent', USER_AGENT)
            if url_log is None: log_debug('net_get_URL() GET URL "{}"'.format(req.get_full_url()))
            response = urllib.request.urlopen(req, timeout = 120)
            page_bytes = response.read()
            http_code = response.getcode()
            encoding = response.headers['content-type'].split('charset=')[-1]
            response.close()
        except urllib.error.HTTPError as ex:
            http_code = ex.code
            try:
                page_bytes = ex.read()
                ex.close()
            except:
                page_bytes = text_type(ex.reason)
            log_error('(HTTPError) In net_get_URL()')
            log_error('(HTTPError) Object type "{}"'.format(type(ex)))
            log_error('(HTTPError) Message "{}"'.format(text_type(ex)))
            log_error('(HTTPError) Code {}'.format(http_code))
            return page_bytes, http_code
        except Exception as ex:
            log_error('(Exception) In net_get_URL()')
            log_error('(Exception) Object type "{}"'.format(type(ex)))
            log_error('(Exception) Message "{}"'.format(text_type(ex)))
            return page_bytes, http_code

    # --- Convert to Unicode ---
    log_debug('net_get_URL() Read {} bytes'.format(len(page_bytes)))
    log_debug('net_get_URL() HTTP status code {}'.format(http_code))
    log_debug('net_get_URL() encoding {}'.format(encoding))
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
# If an exception happens return empty data.
def net_post_URL(url, data):
    page_data = ''
    try:
        if ADDON_RUNNING_PYTHON_2:
            req = urllib2.Request(url, data)
            req.add_unredirected_header('User-Agent', USER_AGENT)
            req.add_header("Content-type", "application/x-www-form-urlencoded")
            req.add_header("Acept", "text/plain")
            log_debug('net_post_URL() POST URL "{}"'.format(req.get_full_url()))
            response = urllib2.urlopen(req, timeout = 120)
            page_bytes = response.read()
            encoding = response.headers['content-type'].split('charset=')[-1]
            response.close()
        elif ADDON_RUNNING_PYTHON_3:
            req = urllib.request.Request(url, data)
            req.add_unredirected_header('User-Agent', USER_AGENT)
            req.add_header("Content-type", "application/x-www-form-urlencoded")
            req.add_header("Acept", "text/plain")
            log_debug('net_post_URL() POST URL "{}"'.format(req.get_full_url()))
            response = urllib.request.urlopen(req, timeout = 120)
            page_bytes = response.read()
            encoding = response.headers['content-type'].split('charset=')[-1]
            response.close()
    except IOError as ex:
        log_error('(IOError exception) In net_get_URL()')
        log_error('Message: {}'.format(text_type(ex)))
        return page_data
    except Exception as ex:
        log_error('(General exception) In net_get_URL()')
        log_error('Message: {}'.format(text_type(ex)))
        return page_data
    num_bytes = len(page_bytes)
    log_debug('net_post_URL() Read {} bytes'.format(num_bytes))
    # Convert page data to Unicode
    page_data = net_decode_URL_data(page_bytes, encoding)

    return page_data

def net_decode_URL_data(page_bytes, MIME_type):
    # --- Try to guess encoding ---
    if MIME_type == 'text/html':
        encoding = 'utf-8'
    elif MIME_type == 'application/json':
        encoding = 'utf-8'
    elif MIME_type == 'text/plain' and 'UTF-8' in page_bytes:
        encoding = 'utf-8'
    elif MIME_type == 'text/plain' and 'UTF-16' in page_bytes:
        encoding = 'utf-16'
    else:
        encoding = 'utf-8'
    # log_debug('net_decode_URL_data() MIME_type "{}", encoding "{}"'.format(MIME_type, encoding))

    # Decode
    page_data = page_bytes.decode(encoding)

    return page_data
