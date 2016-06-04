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

from scrap import *

# -----------------------------------------------------------------------------
# NULL scraper, does nothing, but it's very fast :)
# ----------------------------------------------------------------------------- 
class fanart_NULL(Scraper_Fanart):
    def __init__(self):
        self.name       = 'NULL'
        self.fancy_name = 'NULL Fanart scraper'

    def set_options(self, region, imgsize):
        pass

    def get_search(self, search_string, rom_base_noext, platform):
        return []

    def get_images(self, game):
        return []

# -----------------------------------------------------------------------------
# TheGamesDB
# ----------------------------------------------------------------------------- 
class fanart_TheGamesDB(Scraper_Thumb, Scraper_TheGamesDB):
    def __init__(self):
        self.name       = 'TheGamesDB'
        self.fancy_name = 'TheGamesDB Fanart scraper'

    def set_options(self, region, imgsize):
        pass

    # Call common code in parent class
    def get_search(self, search_string, rom_base_noext, platform):
        return Scraper_TheGamesDB.get_search(self, search_string, rom_base_noext, platform)

    def get_images(self, game):
        # --- Download game page XML data ---
        # Maybe this is candidate for common code...
        game_id_url = 'http://thegamesdb.net/api/GetGame.php?id=' + game['id']
        log_debug('fanart_TheGamesDB::get_images game_id_url = {0}'.format(game_id_url))
        req = urllib2.Request(game_id_url)
        req.add_unredirected_header('User-Agent', USER_AGENT)
        page_data = net_get_URL_text(req)

        # --- Parse game thumb information and make list of images ---
        image_list = []
        # Read fanart
        fanarts = re.findall('<original (.*?)">fanart/(.*?)</original>', page_data)
        for indexa, fanart in enumerate(fanarts):
          image_list.append({'name'     : 'Fanart ' + str(indexa+1),
                             'URL'      : 'http://thegamesdb.net/banners/fanart/' + fanarts[indexa][1], 
                             'disp_URL' : 'http://thegamesdb.net/banners/fanart/' + fanarts[indexa][1].replace('/original/', '/thumb/')})

        # Read screenshot
        screenshots = re.findall('<original (.*?)">screenshots/(.*?)</original>', page_data)
        for indexb, screenshot in enumerate(screenshots):
          image_list.append({'name'     : 'Screenshot ' + str(indexb+1), 
                             'URL'      : 'http://thegamesdb.net/banners/screenshots/' + screenshots[indexb][1],
                             'disp_URL' : 'http://thegamesdb.net/banners/screenshots/' + screenshots[indexb][1]})

        return image_list

# -----------------------------------------------------------------------------
# GameFAQs
# ----------------------------------------------------------------------------- 
class fanart_GameFAQs(Scraper_Thumb, Scraper_GameFAQs):
    def __init__(self):
        self.name       = 'GameFAQs'
        self.fancy_name = 'GameFAQs Fanart scraper'
        
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

        # --- Get fanarts ---
        full_fanarts = []
        for line in page_data.readlines():
            if 'pod game_imgs' in line:
                fanarts = re.findall('b"><a href="(.*?)"><img src="(.*?)"', line)
                for index, item in enumerate(fanarts):
                    full_fanarts.append({'name' : 'Image ' + str(index), 'URL' : item[0], 'disp_URL' : item[1]})

        return full_fanarts

# -----------------------------------------------------------------------------
# arcadeHITS
# Site in french, valid only for MAME.
# ----------------------------------------------------------------------------- 
class fanart_arcadeHITS(Scraper_Fanart):
    def __init__(self):
        self.name       = 'arcadeHITS'
        self.fancy_name = 'arcadeHITS Fanart scraper'

    def set_options(self, region, imgsize):
        pass

    def get_search(self, search_string, rom_base_noext, platform):
        return []

    def get_images(self, game):
      covers = []
      results = []
      try:
          f = urllib.urlopen('http://www.arcadehits.net/page/viewdatfiles.php?show=snap&jeu='+search)
          page = f.read().replace('\r\n', '').replace('\n', '')
          results = re.findall('<img src=(.*?).png', page)
          for index, line in enumerate(results):
              covers.append(['http://www.arcadehits.net/'+line+'.png','http://www.arcadehits.net/'+line+'.png','Image '+str(index+1)])
          return covers
      except:
          return covers

# -----------------------------------------------------------------------------
# Google
# ----------------------------------------------------------------------------- 
class fanart_Google(Scraper_Fanart):
    def __init__(self):
        self.name       = 'Google'
        self.fancy_name = 'Google Fanart scraper'

    def set_options(self, region, imgsize):
        pass

    def get_search(self, search_string, rom_base_noext, platform):
        return []

    def get_images(self, game):
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
