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

# --- Thumb scrapers ----------------------------------------------------------
# All thumb scrapers are online scrapers. If user has a local image then he
# can setup manually using other parts of the GUI.
class Scraper_Thumb(Scraper):
    # This function is called when the user wants to search a whole list of
    # thumbs. Note that gamesys is AEL official system name, and must be
    # translated to the scraper system name, which may be different.
    # Example: AEL name 'Sega MegaDrive' -> Scraper name 'Sega Genesis'
    #
    # Returns:
    #   url_list  List or URLs where images can be downloaded
    def get_image_list(search_string, gamesys, region, imgsize):
      raise NotImplementedError("Subclass must implement get_thumbnail_list() abstract method") 

# -----------------------------------------------------------------------------
# NULL scraper, does nothing, but it's very fast :)
# ----------------------------------------------------------------------------- 
class thumb_NULL(Scraper_Thumb):
    def __init__(self):
        self.name = 'NULL'
        self.fancy_name = 'NULL Thumb scraper'

    def get_image_list(self, search_string, gamesys, region, imgsize):
        return []

# -----------------------------------------------------------------------------
# TheGamesDB thumb scraper
# ----------------------------------------------------------------------------- 
class thumb_TheGamesDB(Scraper_Thumb):
    def __init__(self):
        self.name = 'TheGamesDB'
        self.fancy_name = 'TheGamesDB Thumb scraper'

    def get_image_list(self, search_string, gamesys, region, imgsize):
      covers = []
      game_id_url = _get_game_page_url(system,search)
      try:
          req = urllib2.Request(game_id_url)
          req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
          f = urllib2.urlopen(req)
          page = f.read().replace('\n', '')
          boxarts = re.findall('<boxart side="front" (.*?)">(.*?)</boxart>', page)
          for indexa, boxart in enumerate(boxarts):
              covers.append(("http://thegamesdb.net/banners/"+boxarts[indexa][1],"http://thegamesdb.net/banners/"+boxarts[indexa][1],"Cover "+str(indexa+1)))
          banners = re.findall('<banner (.*?)">(.*?)</banner>', page)
          for indexb, banner in enumerate(banners):
              covers.append(("http://thegamesdb.net/banners/"+banners[indexb][1],"http://thegamesdb.net/banners/"+banners[indexb][1],"Banner "+str(indexb+1)))
          return covers
      except:
          return covers

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
