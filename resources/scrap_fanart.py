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

# --- AEL modules ---
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
        log_debug('fanart_GameFAQs::get_images game_id_url = {0}'.format(game_id_url))
        req = urllib2.Request(game_id_url)
        req.add_unredirected_header('User-Agent', USER_AGENT)
        page_data = net_get_URL_text(req)
        # text_dump_str_to_file(page_data, 'data_GameFAQs_Images_page.txt')

        # --- Parse game thumb information ---
        # From GameFAQs, take screenshots as fanarts.
        #
        # Example: http://www.gamefaqs.com/snes/588741-super-metroid/images
        #
        # <td class="thumb">
        # <a href="/snes/588741-super-metroid/images/21">
        # <img class="imgboxart" src="http://img.gamefaqs.net/screens/1/4/8/gfs_4598_1_1_thm.jpg" />
        # </a>
        # </td>
        #
        img_pages = []
        results = re.findall('<td class="thumb"><a href="(.+?)"><img class="imgboxart" src="(.+?)" /></a></td>', page_data)
        # print(results)

        # Choose one full size artwork page based on game region
        for index, boxart in enumerate(results):
            str_index = str(index + 1)
            log_debug('fanart_GameFAQs::get_images Artwork page #{0} {1}'.format(str_index, boxart[0]))
            img_pages.append( (boxart[0], boxart[1]) )

        # For now just pick the first one. According to settings maybe last or something in the middle should
        # be chosen...
        images = []
        if not img_pages: return images
        img_page = img_pages[0]

        # --- Go to full size page and get thumb ---
        image_url = 'http://www.gamefaqs.com' + img_page[0]
        log_debug('fanart_GameFAQs::get_images image_url = {0}'.format(image_url))
        req = urllib2.Request(image_url)
        req.add_unredirected_header('User-Agent', USER_AGENT)
        page_data = net_get_URL_text(req)
        # text_dump_str_to_file(page_data, 'page_data.txt')

        # GameFAQs fanarts are screenshots
        # Example: http://www.gamefaqs.com/snes/588741-super-metroid/images/21
        #
        # <div class="img">
        #  <a href="http://img.gamefaqs.net/screens/5/1/f/gfs_4598_1_1.jpg">
        #   <img class="full_boxshot" src="http://img.gamefaqs.net/screens/5/1/f/gfs_4598_1_1.jpg" alt="Super Metroid Screenshot">
        #  </a>
        # </div>
        results = re.findall('<img class="full_boxshot" src="(.+?)" alt="(.+?)">', page_data)
        # print(results)
        for index, boxart in enumerate(results):
            str_index = str(index + 1)
            log_debug('fanart_GameFAQs::get_images Adding thumb #{0} {0}'.format(str_index, boxart[0]))
            images.append({'name' : boxart[1], 'URL' : boxart[0], 'disp_URL' : boxart[0]})

        return images

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
