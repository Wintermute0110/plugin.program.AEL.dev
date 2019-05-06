# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher network IO module
#

# Copyright (c) 2016-2018 Wintermute0110 <wintermute0110@gmail.com>
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
from __future__ import division
import sys
import random
import json
import ssl
import xml.etree.ElementTree as ET

from httplib import HTTPSConnection
from urllib2 import urlopen, build_opener, Request, HTTPSHandler

# Python3 
# import http
# from urllib.request import urlopen

# --- AEL packages ---
from resources.utils import log_debug, log_warning, log_error, log_info

# --- GLOBALS -----------------------------------------------------------------
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31'

# ---  -----------------------------------------------------------------
def net_get_random_UserAgent():
    platform = random.choice(['Macintosh', 'Windows', 'X11'])
    if platform == 'Macintosh':
        os  = random.choice(['68K', 'PPC'])
    elif platform == 'Windows':
        os  = random.choice(['Win3.11', 'WinNT3.51', 'WinNT4.0', 'Windows NT 5.0', 'Windows NT 5.1', 
                             'Windows NT 5.2', 'Windows NT 6.0', 'Windows NT 6.1', 'Windows NT 6.2', 
                             'Win95', 'Win98', 'Win 9x 4.90', 'WindowsCE'])
    elif platform == 'X11':
        os  = random.choice(['Linux i686', 'Linux x86_64'])

    browser = random.choice(['chrome', 'firefox', 'ie'])
    if browser == 'chrome':
        webkit = str(random.randint(500, 599))
        version = str(random.randint(0, 24)) + '.0' + str(random.randint(0, 1500)) + '.' + str(random.randint(0, 999))
        return 'Mozilla/5.0 (' + os + ') AppleWebKit/' + webkit + '.0 (KHTML, live Gecko) Chrome/' + version + ' Safari/' + webkit
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
        version = random.choice(['1.0', '2.0', '3.0', '4.0', '5.0', '6.0', '7.0', '8.0', 
                                 '9.0', '10.0', '11.0', '12.0', '13.0', '14.0', '15.0'])
        return 'Mozilla/5.0 (' + os + '; rv:' + version + ') Gecko/' + gecko + ' Firefox/' + version
    elif browser == 'ie':
        version = str(random.randint(1, 10)) + '.0'
        engine = str(random.randint(1, 5)) + '.0'
        option = random.choice([True, False])
        if option == True:
            token = random.choice(['.NET CLR', 'SV1', 'Tablet PC', 'Win64; IA64', 'Win64; x64', 'WOW64']) + '; '
        elif option == False:
            token = ''
        return 'Mozilla/5.0 (compatible; MSIE ' + version + '; ' + os + '; ' + token + 'Trident/' + engine + ')'

def net_download_img(img_url, file_path):
    try:
        req = Request(img_url)
        req.add_unredirected_header('User-Agent', net_get_random_UserAgent())

        file_path.writeAll(urlopen(req).read(),'wb')
    except IOError as e:    
        log_error('(IOError) Exception in net_download_img()')
        log_error('(IOError) {0}'.format(str(e)))

# User agent is fixed and defined in global var USER_AGENT
# Returns a Unicode string.
#
def net_get_URL_oneline(url):
    page_data = ''
    req = Request(url)
    req.add_unredirected_header('User-Agent', USER_AGENT)
    log_debug('net_get_URL_oneline() Reading URL "{0}"'.format(req.get_full_url()))

    try:
        # --- Open network connection (socket) ---
        f = urlopen(req)

        # --- Read data from socket ---
        encoding = f.headers['content-type'].split('charset=')[-1]
        # >> Fix for wrong encodings...
        if encoding == 'text/html': encoding = 'utf-8'
        log_debug('net_get_URL_oneline() Encoding = "{0}"'.format(encoding))
        page_bytes = f.read()
        f.close()
    except IOError as e:    
        log_error('(IOError) Exception in net_get_URL_oneline()')
        log_error('(IOError) {0}'.format(str(e)))
        return page_data
    except Exception as e:
        log_error('(Error) Exception in net_get_URL_oneline()')
        log_error('(Error) {0}'.format(str(e)))
        return page_data


    # --- Convert to Unicode ---
    num_bytes = len(page_bytes)
    log_debug('net_get_URL_oneline() Read {0} bytes'.format(num_bytes))
    #python 3: page_data = str(page_bytes, encoding)
    page_data = unicode(page_bytes, encoding)

    # --- Put all page text into one line ---
    page_data = page_data.replace('\r\n', '')
    page_data = page_data.replace('\n', '')

    return page_data

def net_get_URL_original(url):
    page_data = ''
    
    req = Request(url)
    req.add_unredirected_header('User-Agent', USER_AGENT)
    log_debug('net_get_URL_original() Reading URL "{0}"'.format(req.get_full_url()))

    try:
        f = urlopen(req)
        encoding = f.headers['content-type'].split('charset=')[-1]
        page_bytes = f.read()
        f.close()
    except IOError as e:    
        log_error('(IOError) Exception in net_get_URL_original()')
        log_error('(IOError) {0}'.format(str(e)))
        return page_data

    num_bytes = len(page_bytes)
    log_debug('net_get_URL_original() Read {0} bytes'.format(num_bytes))

    # --- Convert to Unicode ---    
    if encoding == 'text/html': encoding = 'utf-8'
    if encoding == 'text/plain' and 'UTF-8' in page_bytes: encoding = 'utf-8'
    if encoding == 'text/plain' and 'UTF-16' in page_bytes: encoding = 'utf-16'
    if encoding == 'application/json': encoding = 'utf-8'
    
    log_debug('net_get_URL_original() encoding = "{0}"'.format(encoding))
    if encoding != 'utf-16':
        #python 3: page_data = str(page_bytes, encoding)
        page_data = unicode(page_bytes, encoding)

    if encoding == 'utf-16':
        page_data = page_bytes.encode('utf-16')

    return page_data

def net_post_URL_original(url, params):
    page_data = ''
    
    req = Request(url, params)
    req.add_unredirected_header('User-Agent', USER_AGENT)
    req.add_header("Content-type", "application/x-www-form-urlencoded")
    req.add_header("Acept", "text/plain")

    log_debug('net_post_URL_original() POSTING URL "{0}"'.format(req.get_full_url()))
    
    try:
        f = urlopen(req)
        encoding = f.headers['content-type'].split('charset=')[-1]
        page_bytes = f.read()
        f.close()
    except IOError as e:    
        log_error('(IOError) Exception in net_post_URL_original()')
        log_error('(IOError) {0}'.format(str(e)))
        return page_data

    num_bytes = len(page_bytes)
    log_debug('net_post_URL_original() Read {0} bytes'.format(num_bytes))

    # --- Convert to Unicode ---    
    if encoding == 'text/html': encoding = 'utf-8'
    if encoding == 'text/plain' and 'UTF-8' in page_bytes: encoding = 'utf-8'
    if encoding == 'text/plain' and 'UTF-16' in page_bytes: encoding = 'utf-16'
    if encoding == 'application/json': encoding = 'utf-8'
    
    log_debug('net_post_URL_original() encoding = "{0}"'.format(encoding))
    if encoding != 'utf-16':
        #python3: page_data = str(page_bytes, encoding)
        page_data = unicode(page_bytes, encoding)

    if encoding == 'utf-16':
        page_data = page_bytes.encode('utf-16')

    return page_data

def net_get_URL_using_handler(url, handler = None):

    page_data = None
    opener = build_opener(handler)
    
    log_debug('net_get_URL_using_handler() Reading URL "{0}"'.format(url))
    try:
        f = opener.open(url)
        encoding = f.headers['content-type'].split('charset=')[-1]
        page_bytes = f.read()
        f.close()
    except IOError as e:    
        log_error('(IOError) Exception in net_get_URL_using_handler()')
        log_error('(IOError) {0}'.format(str(e)))
        return page_data

    num_bytes = len(page_bytes)
    log_debug('net_get_URL_using_handler() Read {0} bytes'.format(num_bytes))

    # --- Convert to Unicode ---    
    if encoding == 'text/html': encoding = 'utf-8'
    if encoding == 'text/plain' and 'UTF-8' in page_bytes: encoding = 'utf-8'
    if encoding == 'text/plain' and 'UTF-16' in page_bytes: encoding = 'utf-16'
    
    log_debug('net_get_URL_using_handler() encoding = "{0}"'.format(encoding))
    if encoding != 'utf-16':
        page_data = unicode(page_bytes, encoding)

    if encoding == 'utf-16':
        page_data = page_bytes.encode('utf-16')
    return page_data
    
def net_get_URL_as_json(url):

    page_data = net_get_URL_original(url)
    return json.loads(page_data)

class HTTPSClientAuthHandler(HTTPSHandler):
    def __init__(self, key, cert):
        ctx = ssl._create_unverified_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    
        HTTPSHandler.__init__(self, context = ctx)
        
        self.context = ctx
        self.key = key
        self.cert = cert

    def https_open(self, req):
        return self.do_open(self.getConnection, req)

    def getConnection(self, host, timeout=300):
        return HTTPSConnection(host, key_file=self.key, cert_file=self.cert, context = self.context)