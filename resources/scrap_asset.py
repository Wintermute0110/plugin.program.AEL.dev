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

# --- Python standard library ---
from __future__ import unicode_literals
import sys, urllib, urllib2, re

# --- AEL modules ---
from scrap import *
from scrap_info import *
from assets import *

# -----------------------------------------------------------------------------
# NULL scraper, does nothing, but it's very fast :)
# Use as base for new scrapers
# ----------------------------------------------------------------------------- 
class asset_NULL(Scraper_Asset):
    def __init__(self):
        self.name = 'NULL'

    def get_search(self, search_string, rom_base_noext, platform):
        return []

    def set_options(self, region, imgsize):
        pass

    def supports_asset(asset_kind):
        return False

    def get_images(self, game, asset_kind):
        return []

# -----------------------------------------------------------------------------
# TheGamesDB asset scraper
# ----------------------------------------------------------------------------- 
class asset_TheGamesDB(Scraper_Asset, Scraper_TheGamesDB):
    def __init__(self):
        self.name       = 'TheGamesDB'

    # Call scraper shared code in parent class
    def get_search(self, search_string, rom_base_noext, platform):
        return Scraper_TheGamesDB.get_search(self, search_string, rom_base_noext, platform)

    def set_options(self, region, imgsize):
        pass

    def supports_asset(self, asset_kind):
        if asset_kind == ASSET_SNAP     or asset_kind == ASSET_FANART or \
           asset_kind == ASSET_BANNER   or asset_kind == ASSET_CLEARLOGO or \
           asset_kind == ASSET_BOXFRONT or asset_kind == ASSET_BOXBACK:
           return True

        return False

    def get_images(self, game, asset_kind):
        images = []

        # --- Download game page XML data ---
        game_id_url = 'http://thegamesdb.net/api/GetGame.php?id=' + game['id']
        A = assets_get_info_scheme(asset_kind)
        log_debug('asset_TheGamesDB::get_images game_id_url = {0}'.format(game_id_url))
        log_debug('asset_TheGamesDB::get_images asset_kind  = {0}'.format(A.name))

        # Maybe this is candidate for common code...
        req = urllib2.Request(game_id_url)
        req.add_unredirected_header('User-Agent', USER_AGENT)
        page_data = net_get_URL_text(req)

        # --- Parse game thumb information and make list of images ---
        # The XML returned by GetGame.php has many tags. See an example here:
        # SNES Super Castlevania IV --> http://thegamesdb.net/api/GetGame.php?id=1308
        # SNES Super Mario World    --> http://thegamesdb.net/api/GetGame.php?id=136
        #
        if asset_kind == ASSET_SNAP:
            screenshots = re.findall('<original (.*?)">screenshots/(.*?)</original>', page_data)
            for index, screenshot in enumerate(screenshots):
                log_debug('thumb_TheGamesDB::get_images Adding fanart #{0} {1}'.format(str(index + 1), screenshot[1]))
                images.append({'name'     : 'Screenshot ' + str(index + 1), 
                               'URL'      : 'http://thegamesdb.net/banners/screenshots/' + screenshots[index][1],
                               'disp_URL' : 'http://thegamesdb.net/banners/screenshots/' + screenshots[index][1]})

        elif asset_kind == ASSET_FANART:
            fanarts = re.findall('<original (.*?)">fanart/(.*?)</original>', page_data)
            for index, fanart in enumerate(fanarts):
                log_debug('thumb_TheGamesDB::get_images Adding fanart #{0} {1}'.format(str(index + 1), fanart[1]))
                images.append({'name'     : 'Fanart ' + str(index + 1),
                               'URL'      : 'http://thegamesdb.net/banners/fanart/' + fanart[1], 
                               'disp_URL' : 'http://thegamesdb.net/banners/fanart/' + fanart[1].replace('/original/', '/thumb/')})

        elif asset_kind == ASSET_BANNER:
            banners = re.findall('<banner (.*?)">(.*?)</banner>', page_data)
            for index, banner in enumerate(banners):
                log_debug('thumb_TheGamesDB::get_images Adding banner #{0} {1}'.format(str(index + 1), banner[1]))
                images.append({'name'     : 'Banner ' + str(index + 1), 
                               'URL'      : 'http://thegamesdb.net/banners/' + banner[1],
                               'disp_URL' : 'http://thegamesdb.net/banners/' + banner[1]})

        elif asset_kind == ASSET_CLEARLOGO:
            clearlogos = re.findall('<clearlogo (.*?)">(.*?)</clearlogo>', page_data)
            for index, clearlogo in enumerate(clearlogos):
                log_debug('thumb_TheGamesDB::get_images Adding clearlogo #{0} {1}'.format(str(index + 1), clearlogo[1]))
                images.append({'name'     : 'Clearlogo ' + str(index + 1), 
                               'URL'      : 'http://thegamesdb.net/banners/' + clearlogo[1],
                               'disp_URL' : 'http://thegamesdb.net/banners/' + clearlogo[1]})

        elif asset_kind == ASSET_BOXFRONT:
            boxarts = re.findall('<boxart side="front" (.*?)">(.*?)</boxart>', page_data)
            for index, boxart in enumerate(boxarts):
                # print(index, boxart)
                log_debug('thumb_TheGamesDB::get_images Adding boxfront #{0} {1}'.format(str(index + 1), boxart[1]))
                images.append({'name'     : 'Boxfront ' + str(index + 1),
                               'URL'      : 'http://thegamesdb.net/banners/' + boxart[1],
                               'disp_URL' : 'http://thegamesdb.net/banners/' + boxart[1]})
        
        elif asset_kind == ASSET_BOXBACK:
            boxarts = re.findall('<boxart side="back" (.*?)">(.*?)</boxart>', page_data)
            for index, boxart in enumerate(boxarts):
                # print(index, boxart)
                log_debug('thumb_TheGamesDB::get_images Adding boxfront #{0} {1}'.format(str(index + 1), boxart[1]))
                images.append({'name'     : 'Boxback ' + str(index + 1),
                               'URL'      : 'http://thegamesdb.net/banners/' + boxart[1],
                               'disp_URL' : 'http://thegamesdb.net/banners/' + boxart[1]})

        return images

# -----------------------------------------------------------------------------
# GameFAQs asset scraper
# ----------------------------------------------------------------------------- 
class asset_GameFAQs(Scraper_Asset, Scraper_GameFAQs):
    def __init__(self):
        self.name       = 'GameFAQs'

    def set_options(self, region, imgsize):
        pass

    # Call common code in parent class
    def get_search(self, search_string, rom_base_noext, platform):
        return Scraper_GameFAQs.get_search(self, search_string, rom_base_noext, platform)

    def get_images(self, game):
        # --- Download game page data ---
        # Maybe this is candidate for common code...        
        game_id_url = 'http://www.gamefaqs.com' + game['id'] + '/images'
        log_debug('thumb_GameFAQs::get_images game_id_url = {0}'.format(game_id_url))
        req = urllib2.Request(game_id_url)
        req.add_unredirected_header('User-Agent', USER_AGENT)
        page_data = net_get_URL_text(req)
    
        # --- Parse game thumb information ---
        # The game URL shows a page with boxart and screenshots. Boxart can be diferent depending 
        # on the region. Each region has then a separate page with the full size artwork (boxfront, boxback, etc.)
        #
        # Example: http://www.gamefaqs.com/snes/588741-super-metroid/images
        #
        # <div class="img boxshot">
        #  <a href="/snes/588741-super-metroid/images/14598">
        #  <img class="img100 imgboxart" src="http://img.gamefaqs.net/box/3/2/1/51321_thumb.jpg" alt="Super Metroid (JP)" />
        #  </a>
        #  <div class="region">JP 03/19/94</div>
        # </div>
        img_pages = []
        results = re.findall('<div class="img boxshot"><a href="(.+?)"><img class="img100 imgboxart" src="(.+?)" alt="(.+?)" /></a>', page_data)
        # print(results)

        # Choose one full size artwork page based on game region
        for index, boxart in enumerate(results):
            str_index = str(index + 1)
            log_debug('thumb_GameFAQs::get_images Artwork page #{0:>2s} {1}'.format(str_index, boxart[1]))
            img_pages.append( (boxart[0], boxart[1], boxart[2]) )

        # For now just pick the first one
        images = []
        if not img_pages: return images
        img_page = img_pages[0]

        # --- Go to full size page and get thumb ---
        image_url = 'http://www.gamefaqs.com' + img_page[0]
        log_debug('thumb_GameFAQs::get_images image_url = {0}'.format(image_url))
        req = urllib2.Request(image_url)
        req.add_unredirected_header('User-Agent', USER_AGENT)
        page_data = net_get_URL_text(req)
        # text_dump_str_to_file(page_data, 'page_data.txt')

        # <a href="http://img.gamefaqs.net/box/3/2/1/51321_front.jpg">
        # <img class="full_boxshot" src="http://img.gamefaqs.net/box/3/2/1/51321_front.jpg" alt="Super Metroid Box Front" />
        # </a>
        results = re.findall('<img class="full_boxshot" src="(.+?)" alt="(.+?)" /></a>', page_data)
        # print(results)
        for index, boxart in enumerate(results):
            str_index = str(index + 1)
            log_debug('thumb_GameFAQs::get_images Adding thumb #{0} {1}'.format(str_index, boxart[0]))
            images.append({'name' : boxart[1], 'URL' : boxart[0], 'disp_URL' : boxart[0]})

        return images

# -----------------------------------------------------------------------------
# Google asset scraper
# ----------------------------------------------------------------------------- 
class asset_Google(Scraper_Asset):
    def __init__(self):
        self.name       = 'Google'

    def set_options(self, region, imgsize):
        pass

    def get_search(self, search_string, rom_base_noext, platform):
        return []

    # Checks this... I think Google image search API is deprecated.
    def get_images(self, game):
      qdict = {'q':search,'imgsz':imgsize}
      query = urllib.urlencode(qdict)
      base_url = ('http://ajax.googleapis.com/ajax/services/search/images?v=1.0&start=%s&rsz=8&%s')
      covers = []
      results = []
      try:
          for start in (0, 8, 16, 24):
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

