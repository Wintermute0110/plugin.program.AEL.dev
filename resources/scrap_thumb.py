# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher scraping engine
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

import sys, urllib, urllib2, re

from scrap import *
from scrap_info import *
# from utils import *

# -----------------------------------------------------------------------------
# NULL scraper, does nothing, but it's very fast :)
# ----------------------------------------------------------------------------- 
class thumb_NULL(Scraper_Thumb):
    def __init__(self):
        self.name = 'NULL'
        self.fancy_name = 'NULL Thumb scraper'

    def get_image_list(self, game):
        return []

# -----------------------------------------------------------------------------
# TheGamesDB thumb scraper
# ----------------------------------------------------------------------------- 
class thumb_TheGamesDB(Scraper_Thumb, Scraper_TheGamesDB):
    def __init__(self):
        self.name = 'TheGamesDB'
        self.fancy_name = 'TheGamesDB Thumb scraper'

    # Call common code in parent class
    def get_games_search(self, search_string, platform, rom_base_noext = ''):
        return Scraper_TheGamesDB.get_games_search(self, search_string, platform, rom_base_noext)

    def get_game_image_list(self, game):
        images = []
        
        # Download game page XML data
        game_id_url = 'http://thegamesdb.net/api/GetGame.php?id=' + game["id"]
        log_debug('get_game_image_list() game_id_url = {}'.format(game_id_url))
        req = urllib2.Request(game_id_url)
        req.add_unredirected_header('User-Agent', USER_AGENT)
        page_data = net_get_URL_text(req)

        # --- Parse game thumb information ---
        # The XML returned has many tags. See an example here:
        # SNES Super Castlevania IV --> http://thegamesdb.net/api/GetGame.php?id=1308
        # Read front boxes
        boxarts = re.findall('<boxart side="front" (.*?)">(.*?)</boxart>', page_data)
        for index, boxart in enumerate(boxarts):
            # print(index, boxart)
            log_debug('get_game_image_list() Adding boxfront #{:>2s} {}'.format(str(index + 1), boxart[1]))
            images.append(("http://thegamesdb.net/banners/" + boxart[1],
                           "http://thegamesdb.net/banners/" + boxart[1],
                           "Cover " + str(index + 1)))
        # Read banners
        banners = re.findall('<banner (.*?)">(.*?)</banner>', page_data)
        for index, banner in enumerate(banners):
            log_debug('get_game_image_list() Adding banner   #{:>2s} {}'.format(str(index + 1), banner[1]))
            images.append(("http://thegamesdb.net/banners/" + banner[1], 
                           "http://thegamesdb.net/banners/" + banner[1],
                           "Banner " + str(index + 1)))

        return images

# -----------------------------------------------------------------------------
# GameFAQs thumb scraper
# ----------------------------------------------------------------------------- 
class thumb_GameFAQs(Scraper_Thumb):
    def __init__(self):
        self.name = 'GameFAQs'
        self.fancy_name = 'GameFAQs Thumb scraper'

    # Checks this... I think Google image search API is deprecated.
    def get_image_list(self, search_string, gamesys, region, imgsize):
      covers = []
      results = []
      try:
          game_id_url = _get_game_page_url(system,search)
          req = urllib2.Request('http://www.gamefaqs.com'+game_id_url)
          req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
          game_page = urllib2.urlopen(req)
          results = re.findall('<div class="img boxshot"><a href="(.*?)"><img class="img100" src="(.*?)" alt="(.*?)" /></a>', game_page.read().replace('\r\n', ''))
          if (region == "All" ):
              return results
          else:
              for result in results:
                  if '('+region+')' in result[2]:
                      covers.append(result)
              return covers
      except:
          return covers

    # It seems that GameFAQs need URL translation... Have to investigate this
    def get_thumbnail(image_url):
        images = []
        try:
            req = urllib2.Request('http://www.gamefaqs.com' + image_url)
            req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
            search_page = urllib2.urlopen(req)
            for line in search_page.readlines():
                if 'Game Box Shot' in line:
                    images = re.findall('g"><a href="(.*?)"><img class="full_boxshot" src="(.*?)"', line)
                    return images[0][0]
        except:
            return ""

# -----------------------------------------------------------------------------
# arcadeHITS
# Site in french, valid only for MAME.
# ----------------------------------------------------------------------------- 
class thumb_arcadeHITS(Scraper_Thumb):
    def __init__(self):
        self.name = 'arcadeHITS'
        self.fancy_name = 'arcadeHITS Thumb scraper'

    # Checks this... I think Google image search API is deprecated.
    def get_image_list(self, search_string, gamesys, region, imgsize):
        covers = []
        results = []
        try:
            f = urllib.urlopen('http://www.arcadehits.net/page/viewdatfiles.php?show=snap&jeu='+search)
            page = f.read().replace('\r\n', '').replace('\n', '')
            results = re.findall('<img src=(.*?).png', page)
            for index, line in enumerate(results):
                covers.append(['http://www.arcadehits.net/'+line+'.png','http://www.arcadehits.net/'+line+'.png','Image '+str(index+1)])

            f = urllib.urlopen('http://www.arcadehits.net/page/viewdatfiles.php?show=flyers&jeu='+search)
            page = f.read().replace('\r\n', '').replace('\n', '')
            results = re.findall('<img src=(.*?).png', page)
            for index, line in enumerate(results):
                covers.append(['http://www.arcadehits.net/'+line+'.png','http://www.arcadehits.net/'+line+'.png','Image '+str(index+1)])

            return covers
        except:
            return covers

# -----------------------------------------------------------------------------
# Google thumb scraper
# ----------------------------------------------------------------------------- 
class thumb_Google(Scraper_Thumb):
    def __init__(self):
        self.name = 'Google'
        self.fancy_name = 'Google Thumb scraper'

    # Checks this... I think Google image search API is deprecated.
    def get_image_list(self, search_string, gamesys, region, imgsize):
      qdict = {'q':search,'imgsz':imgsize}
      query = urllib.urlencode(qdict)
      base_url = ('http://ajax.googleapis.com/ajax/services/search/images?v=1.0&start=%s&rsz=8&%s')
      covers = []
      results = []
      try:
          for start in (0,8,16,24):
              url = base_url % (start,query)
              search_results = urllib.urlopen(url)
              json = simplejson.loads(search_results.read())
              search_results.close()
              results += json['responseData']['results']
          for index, images in enumerate(results):
              thumbnail = os.path.join(CACHE_PATH,str(index) + str(time.time()) + '.jpg')
              h = urllib.urlretrieve(images['tbUrl'],thumbnail)
              covers.append((images['url'],thumbnail,"Image "+str(index+1)))
          return covers
      except:
          return covers
