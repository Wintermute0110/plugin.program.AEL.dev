# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher network IO module
#

# Copyright (c) 2016 Wintermute0110 <wintermute0110@gmail.com>
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

# Python standard library
import sys, random, urllib2

# AEL packages
try:
    from utils_kodi import *
except:
    from utils_kodi_standalone import *

# --- GLOBALS -----------------------------------------------------------------
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31';

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

# def net_download_page(url):
#     req = urllib2.Request(url)
#     req.add_unredirected_header('User-Agent', net_get_random_UserAgent())
#    
#     return urllib2.urlopen(req)

def net_download_img(img_url, file_path):
    req = urllib2.Request(img_url)
    req.add_unredirected_header('User-Agent', net_get_random_UserAgent())

    f = open(file_path, 'wb')
    f.write(urllib2.urlopen(req).read())
    f.close()                                

def net_get_URL_text(req):
    log_debug('net_get_URL_text() Reading URL "{0}"'.format(req.get_full_url()))
    page_data = ''
    try:
        # Read data
        f = urllib2.urlopen(req)
        page_data = f.read()
        f.close()

        # Put all text into one string
        page_data = page_data.replace('\r\n', '')
        page_data = page_data.replace('\n', '')
    except: # Catches all exceptions
        e = sys.exc_info()[0]
        log_debug('Exception {0}'.format(e))
    log_debug('net_get_URL_text() Read {0} bytes'.format(len(page_data)))

    return page_data
