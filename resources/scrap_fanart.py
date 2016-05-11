#
# Advanced Emulator Launcher scraping engine
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

# --- Fanart scrapers ----------------------------------------------------------
# All fanart scrapers are online scrapers. If user has a local image then he
# can setup manually using other parts of the GUI.
#
# NOTE Look in scrap-thumb.py for more comments and documentation.
class Scraper_Fanart(Scraper):
    def get_image_list(self, search_string, gamesys, region, imgsize):
        raise NotImplementedError("Subclass must implement get_thumbnail_list() abstract method") 

# -----------------------------------------------------------------------------
# NULL scraper, does nothing, but it's very fast :)
# ----------------------------------------------------------------------------- 
class fanart_NULL(Scraper_Fanart):
    def __init__(self):
        self.name = 'NULL'
        self.fancy_name = 'NULL Fanart scraper'

    def get_image_list(self, search_string, gamesys, region, imgsize):
        pass

# -----------------------------------------------------------------------------
# TheGamesDB
# ----------------------------------------------------------------------------- 
class fanart_TheGamesDB(Scraper_Fanart):
    def __init__(self):
        self.name = 'TheGamesDB'
        self.fancy_name = 'TheGamesDB Fanart scraper'

    def get_image_list(self, search_string, gamesys, region, imgsize):
      full_fanarts = []
      game_id_url = _get_game_page_url(system,search)
      try:
          req = urllib2.Request(game_id_url)
          req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
          f = urllib2.urlopen(req)
          page = f.read().replace('\n', '')
          fanarts = re.findall('<original (.*?)">fanart/(.*?)</original>', page)
          for indexa, fanart in enumerate(fanarts):
              full_fanarts.append(("http://thegamesdb.net/banners/fanart/"+fanarts[indexa][1],"http://thegamesdb.net/banners/fanart/"+fanarts[indexa][1].replace("/original/","/thumb/"),"Fanart "+str(indexa+1)))
          screenshots = re.findall('<original (.*?)">screenshots/(.*?)</original>', page)
          for indexb, screenshot in enumerate(screenshots):
              full_fanarts.append(("http://thegamesdb.net/banners/screenshots/"+screenshots[indexb][1],"http://thegamesdb.net/banners/screenshots/thumb/"+screenshots[indexb][1],"Screenshot "+str(indexb+1)))
          return full_fanarts
      except:
          return full_fanarts

# -----------------------------------------------------------------------------
# GameFAQs
# ----------------------------------------------------------------------------- 
class fanart_GameFAQs(Scraper_Fanart):
    def __init__(self):
        self.name = 'GameFAQs'
        self.fancy_name = 'GameFAQs Fanart scraper'

    def get_image_list(self, search_string, gamesys, region, imgsize):
      full_fanarts = []
      game_id_url = _get_game_page_url(system,search)
      try:
          req = urllib2.Request('http://www.gamefaqs.com'+game_id_url+'?page=0')
          req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
          game_page = urllib2.urlopen(req)
          if game_page:
              for line in game_page.readlines():
                  if 'pod game_imgs' in line:
                      fanarts = re.findall('b"><a href="(.*?)"><img src="(.*?)"', line)
                      for index, item in enumerate(fanarts):
                          full_fanarts.append((item[0],item[1],'Image '+str(index)))
          return full_fanarts
      except:
          return full_fanarts

      # URL conversion
      def _get_fanart(image_url):
          images = []
          try:
              req = urllib2.Request('http://www.gamefaqs.com' + image_url)
              req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
              search_page = urllib2.urlopen(req)
              for line in search_page.readlines():
                  if 'pod game_imgs' in line:
                      images = re.findall('g"><a href="(.*?)"', line)
                      return images[0]
          except:
              return ""

# -----------------------------------------------------------------------------
# arcadeHITS
# Site in french, valid only for MAME.
# ----------------------------------------------------------------------------- 
class fanart_arcadeHITS(Scraper_Fanart):
    def __init__(self):
        self.name = 'arcadeHITS'
        self.fancy_name = 'arcadeHITS Fanart scraper'

    def get_image_list(self, search_string, gamesys, region, imgsize):
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
        self.name = 'Google'
        self.fancy_name = 'Google Fanart scraper'

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
