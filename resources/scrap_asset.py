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
import sys, urllib, urllib2, re, os

# --- AEL modules ---
from scrap import *
from scrap_info import *
from assets import *

# -------------------------------------------------------------------------------------------------
# NULL scraper, does nothing, but it's very fast :)
# Use as base for new scrapers
# -------------------------------------------------------------------------------------------------
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

    def resolve_image_URL(self, id):
        return ('', '')

# -------------------------------------------------------------------------------------------------
# TheGamesDB asset scraper
# -------------------------------------------------------------------------------------------------
class asset_TheGamesDB(Scraper_Asset, Scraper_TheGamesDB):
    def __init__(self):
        self.name = 'TheGamesDB'
        # >> Cache page data in get_images()
        self.get_images_cached_game_id   = ''
        self.get_images_cached_page_data = ''
        Scraper_TheGamesDB.__init__(self)

    # Call scraper shared code in parent class
    def get_search(self, search_string, rom_base_noext, platform):
        return Scraper_TheGamesDB.get_search(self, search_string, rom_base_noext, platform)

    def set_options(self, region, imgsize):
        pass

    def supports_asset(self, asset_kind):
        if asset_kind == ASSET_TITLE   or asset_kind == ASSET_SNAP      or asset_kind == ASSET_FANART   or \
           asset_kind == ASSET_BANNER  or asset_kind == ASSET_CLEARLOGO or asset_kind == ASSET_BOXFRONT or \
           asset_kind == ASSET_BOXBACK:
           return True

        return False

    def get_images(self, game, asset_kind):
        baseImgUrl = 'http://thegamesdb.net/banners/'
        images = []

        # --- If asset kind not supported return inmediately ---
        if not self.supports_asset(asset_kind): return images

        # --- Download game page XML data ---
        game_id_url = 'http://thegamesdb.net/api/GetGame.php?id=' + game['id']
        A = assets_get_info_scheme(asset_kind)
        log_debug('asset_TheGamesDB::get_images game_id_url = {0}'.format(game_id_url))
        log_debug('asset_TheGamesDB::get_images asset_kind  = {0}'.format(A.name))

        # >> Check if URL page data is in cache. If so it's a cache hit.
        # >> If cache miss, then update cache.
        if self.get_images_cached_game_id == game['id']:
            log_debug('asset_TheGamesDB::get_images Cache HIT')
            page_data = self.get_images_cached_page_data
        else:
            log_debug('asset_TheGamesDB::get_images Cache MISS. Updating cache')
            page_data = net_get_URL_oneline(game_id_url)
            self.get_images_cached_game_id   = game['id']
            self.get_images_cached_page_data = page_data

        # --- Parse game thumb information and make list of images ---
        # The XML returned by GetGame.php has many tags. See examples here:
        # SNES Super Castlevania IV --> http://thegamesdb.net/api/GetGame.php?id=1308
        # SNES Super Mario World    --> http://thegamesdb.net/api/GetGame.php?id=136
        #
        # WORKAROUND Title and snap return same images. TheGamesDB does not differentiate between
        #            titles and snaps.
        if asset_kind == ASSET_TITLE:
            # Returns a list of tuples.
            # [0] -> 'width="640" height="480"'
            # [1] -> 'screenshots/136-1.jpg'
            # [2] -> 'screenshots/thumb/136-1.jpg'
            screenshots = re.findall('<screenshot><original (.*?)>(.*?)</original><thumb>(.*?)</thumb></screenshot>', page_data)
            for index, screenshot in enumerate(screenshots):
                log_debug('asset_TheGamesDB::get_images '
                          'Adding title #{0} "{1}" (thumb "{2}")'.format(index + 1, screenshot[1], screenshot[2]))
                images.append({'name' : 'Screenshot {0}'.format(index + 1), 
                               'id' : baseImgUrl + screenshot[1], 'URL' : baseImgUrl + screenshot[2]})

        elif asset_kind == ASSET_SNAP:
            screenshots = re.findall('<screenshot><original (.*?)>(.*?)</original><thumb>(.*?)</thumb></screenshot>', page_data)
            for index, screenshot in enumerate(screenshots):
                log_debug('asset_TheGamesDB::get_images '
                          'Adding snap #{0} "{1}" (thumb "{2}")'.format(index + 1, screenshot[1], screenshot[2]))
                images.append({'name' : 'Screenshot {0}'.format(index + 1), 
                               'id' : baseImgUrl + screenshot[1], 'URL' : baseImgUrl + screenshot[2]})

        elif asset_kind == ASSET_FANART:
            fanarts = re.findall('<fanart><original (.*?)>(.*?)</original><thumb>(.*?)</thumb></fanart>', page_data)
            for index, fanart in enumerate(fanarts):
                log_debug('asset_TheGamesDB::get_images '
                          'Adding fanart #{0} "{1}" (thumb "{2}")'.format(index + 1, fanart[1], fanart[2]))
                images.append({'name' : 'Fanart {0}'.format(index + 1),
                               'id' : baseImgUrl + fanart[1], 'URL' : baseImgUrl + fanart[2]})

        elif asset_kind == ASSET_BANNER:
            banners = re.findall('<banner (.*?)>(.*?)</banner>', page_data)
            for index, banner in enumerate(banners):
                log_debug('asset_TheGamesDB::get_images Adding banner #{0} "{1}"'.format(str(index + 1), banner[1]))
                images.append({'name' : 'Banner {0}'.format(index + 1), 
                               'id' : baseImgUrl + banner[1], 'URL' : baseImgUrl + banner[1]})

        elif asset_kind == ASSET_CLEARLOGO:
            clearlogos = re.findall('<clearlogo (.*?)>(.*?)</clearlogo>', page_data)
            for index, clearlogo in enumerate(clearlogos):
                log_debug('asset_TheGamesDB::get_images Adding clearlogo #{0} "{1}"'.format(str(index + 1), clearlogo[1]))
                images.append({'name' : 'Clearlogo {0}'.format(index + 1),
                               'id' : baseImgUrl + clearlogo[1], 'URL' : baseImgUrl + clearlogo[1]})

        elif asset_kind == ASSET_BOXFRONT:
            boxarts = re.findall('<boxart side="front" (.*?)>(.*?)</boxart>', page_data)
            for index, boxart in enumerate(boxarts):
                log_debug('asset_TheGamesDB::get_images Adding boxfront #{0} {1}'.format(str(index + 1), boxart[1]))
                images.append({'name' : 'Boxfront ' + str(index + 1),
                               'id' : baseImgUrl + boxart[1], 'URL' : baseImgUrl + boxart[1]})
        
        elif asset_kind == ASSET_BOXBACK:
            boxarts = re.findall('<boxart side="back" (.*?)>(.*?)</boxart>', page_data)
            for index, boxart in enumerate(boxarts):
                log_debug('asset_TheGamesDB::get_images Adding boxback #{0} {1}'.format(str(index + 1), boxart[1]))
                images.append({'name' : 'Boxback ' + str(index + 1),
                               'id' : baseImgUrl + boxart[1], 'URL' : baseImgUrl + boxart[1]})

        return images

    def resolve_image_URL(self, image_dic):
        log_debug('asset_TheGamesDB::resolve_image_URL Resolving {0}'.format(image_dic['name']))
        image_url = image_dic['id']
        image_ext = text_get_image_URL_extension(image_dic['id'])
        
        return (image_url, image_ext)

# -------------------------------------------------------------------------------------------------
# GameFAQs asset scraper
# -------------------------------------------------------------------------------------------------
class asset_GameFAQs(Scraper_Asset, Scraper_GameFAQs):
    def __init__(self):
        self.name = 'GameFAQs'
        Scraper_GameFAQs.__init__(self)

    # Call common code in parent class
    def get_search(self, search_string, rom_base_noext, platform):
        return Scraper_GameFAQs.get_search(self, search_string, rom_base_noext, platform)

    def set_options(self, region, imgsize):
        pass

    # >> NOTE In GameFAQS, usually the first screenshoots are the titles for the different ROM regions.
    # >>      Choose the first image as the Title. Choose a random image after first as snap. This should work
    # >>      for most games. On the oppositve, in the GamesDB almost no games have Title.
    def supports_asset(self, asset_kind):
        if asset_kind == ASSET_TITLE or asset_kind == ASSET_SNAP or \
           asset_kind == ASSET_BOXFRONT or asset_kind == ASSET_BOXBACK:
           return True

        return False

    def get_images(self, game, asset_kind):
        images = []

        # --- If asset kind not supported return inmediately ---
        if not self.supports_asset(asset_kind): return images

        # --- Download game page data ---
        game_id_url = 'http://www.gamefaqs.com' + game['id'] + '/images'
        A = assets_get_info_scheme(asset_kind)
        log_debug('asset_GameFAQs::get_images game_id_url = {0}'.format(game_id_url))
        log_debug('asset_GameFAQs::get_images asset_kind  = {0}'.format(A.name))

        # >> Check if URL page data is in cache. If so it's a cache hit.
        # >> If cache miss, then update cache.
        page_data = net_get_URL_oneline(game_id_url)

        # --- Retrieve assets ---
        if asset_kind == ASSET_TITLE or asset_kind == ASSET_SNAP:
            # Example: http://www.gamefaqs.com/snes/588741-super-metroid/images
            # <td class="thumb">
            # <a href="/snes/588741-super-metroid/images/21">
            # <img class="imgboxart" src="http://img.gamefaqs.net/screens/1/4/8/gfs_4598_1_1_thm.jpg" />
            # </a>
            # </td>
            img_pages = []
            results = re.findall('<td class="thumb"><a href="(.+?)"><img class="imgboxart" src="(.+?)" /></a></td>', page_data)
            # print(results)
            for index, boxart in enumerate(results):
                str_index = str(index + 1)
                log_debug('asset_GameFAQs::get_images Artwork page #{0} {1}'.format(str_index, boxart[0]))
                img_pages.append( (boxart[0], boxart[1]) )
            images = []
            if not img_pages: return images
            # Title is usually the first or first snapshoots in GameFAQs
            num_images = len(img_pages)
            if asset_kind == ASSET_TITLE:
                img_page = img_pages[0]
                log_debug('asset_GameFAQs::get_images Title chose image index {0} (of {1})'.format(0, num_images))
            # For Snap choose a random one
            else:
                random_index = random.randint(1, num_images)
                img_page = img_pages[random_index]
                log_debug('asset_GameFAQs::get_images Snap chose image index {0} (of {1})'.format(random_index, num_images))

            # --- Go to full size page and get thumb ---
            image_url = 'http://www.gamefaqs.com' + img_page[0]
            page_data = net_get_URL_oneline(image_url)
            # text_dump_str_to_file(page_data, 'page_data.txt')

            # Example: http://www.gamefaqs.com/snes/588741-super-metroid/images/21
            #
            # <div class="img">
            #  <a href="http://img.gamefaqs.net/screens/5/1/f/gfs_4598_1_1.jpg">
            #   <img class="full_boxshot" src="http://img.gamefaqs.net/screens/5/1/f/gfs_4598_1_1.jpg" alt="Super Metroid Screenshot">
            #  </a>
            # </div>
            results = re.findall('<img class="full_boxshot" src="(.+?)" alt="(.+?)">', page_data)
            # print(results)
            for index, thumb in enumerate(results):
                str_index = str(index + 1)
                log_debug('asset_GameFAQs::get_images Adding thumb #{0} {0}'.format(str_index, thumb[0]))
                images.append({'name' : thumb[1], 'URL' : thumb[0], 'disp_URL' : thumb[0]})

        elif asset_kind == ASSET_BOXFRONT or asset_kind == ASSET_BOXBACK:
            # --- Parse game thumb information ---
            # The game URL shows a page with boxart and screenshots thumbnails.
            # Boxart can be diferent depending on the ROM/game region. Each region has then a separate 
            # page with the full size artwork (boxfront, boxback, etc.)
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
            results = re.findall('<div class="img boxshot"><a href="(.+?)">' +
                                 '<img class="img100 imgboxart" src="(.+?)" alt="(.+?)" /></a>', page_data)
            # print(results)

            # --- Choose one full size artwork page based on game region ---
            for index, boxart in enumerate(results):
                str_index = str(index + 1)
                log_debug('asset_GameFAQs::get_images Artwork page #{0} {1}'.format(str_index, boxart[1]))
                img_pages.append( (boxart[0], boxart[1], boxart[2]) )

            # For now just pick the first one
            if not img_pages: return images
            img_page = img_pages[0]

            # --- Go to full size page and get thumb ---
            image_url = 'http://www.gamefaqs.com' + img_page[0]
            page_data = net_get_URL_oneline(image_url)
            # text_dump_str_to_file('GameFAQs-images.txt', page_data)

            # >> NOTE findall() returns a list of tuples, not a match object!
            # <a href="http://img.gamefaqs.net/box/3/2/1/51321_front.jpg">
            # <img class="full_boxshot" src="http://img.gamefaqs.net/box/3/2/1/51321_front.jpg" alt="Super Metroid Box Front" />
            # </a>
            results = re.findall('<img class="full_boxshot" src="(.+?)" alt="(.+?)" /></a>', page_data)
            # print(results)
            str_index = 1
            for index, boxart in enumerate(results):
                art_name = boxart[1]
                if asset_kind == ASSET_BOXFRONT and art_name.find('Front') >= 0:
                    log_debug('asset_GameFAQs::get_images Adding Boxfront #{0} {1}'.format(str_index, boxart[0]))
                    images.append({'name' : boxart[1], 'URL' : boxart[0], 'disp_URL' : boxart[0]})
                    str_index += 1
                elif asset_kind == ASSET_BOXBACK and art_name.find('Back') >= 0:
                    log_debug('asset_GameFAQs::get_images Adding Boxback #{0} {1}'.format(str_index, boxart[0]))
                    images.append({'name' : boxart[1], 'URL' : boxart[0], 'disp_URL' : boxart[0]})
                    str_index += 1

        return images

# -------------------------------------------------------------------------------------------------
# MobyGames
# -------------------------------------------------------------------------------------------------
class asset_MobyGames(Scraper_Asset, Scraper_MobyGames):
    def __init__(self):
        self.name = 'MobyGames'
        Scraper_MobyGames.__init__(self)

    # Call common code in parent class
    def get_search(self, search_string, rom_base_noext, platform):
        return Scraper_MobyGames.get_search(self, search_string, rom_base_noext, platform)

    def set_options(self, region, imgsize):
        pass

    def supports_asset(self, asset_kind):
        if asset_kind == ASSET_TITLE or asset_kind == ASSET_SNAP or \
           asset_kind == ASSET_BOXFRONT or asset_kind == ASSET_BOXBACK or asset_kind == ASSET_CARTRIDGE:
           return True

        return False

    def get_images(self, game, asset_kind):
        images = []
        
        # --- If asset kind not supported return inmediately ---
        if not self.supports_asset(asset_kind): return images

        if asset_kind == ASSET_TITLE or asset_kind == ASSET_SNAP:
            game_id_url = 'http://www.mobygames.com' + game['id'] + '/screenshots'
            A = assets_get_info_scheme(asset_kind)
            log_debug('asset_MobyGames::get_images() game_id_url = {0}'.format(game_id_url))
            log_debug('asset_MobyGames::get_images() asset_kind  = {0}'.format(A.name))

            # >> Check if URL page data is in cache. If so it's a cache hit.
            # >> If cache miss, then update cache.
            page_data = net_get_URL_oneline(game_id_url)
            # text_dump_str_to_file('MobyGames-screenshots.txt', page_data)

            # NOTE findall() returns a list of tuples, not a match object!
            # <div class="thumbnail-image-wrapper">
            # <a href="/game/snes/super-metroid/screenshots/gameShotId,222488/" 
            #  title="Super Metroid SNES Title screen." class="thumbnail-image" 
            #  style="background-image:url(/images/shots/s/222488-super-metroid-snes-screenshot-title-screen.jpg);">
            # </a></div>
            # <div class="thumbnail-caption"><small>Title screen.</small></div>
            rlist = re.findall(
                '<div class="thumbnail-image-wrapper">       ' +
                '<a href="(.*?)" title="(.*?)" class="thumbnail-image" style="background-image:url\((.*?)\);">' +
                '</a>      </div>      ' +
                '<div class="thumbnail-caption">        <small>(.*?)</small>      </div>', page_data)
            # print('Screenshots rlist = ' + unicode(rlist))
            cover_index = 1
            for index, rtuple in enumerate(rlist):
                art_page_URL = 'http://www.mobygames.com' + rtuple[0]
                art_name     = rtuple[1]
                art_disp_URL = 'http://www.mobygames.com' + rtuple[2]
                # >> This does not work because sometimes the screenshot thumbnail is JPG and the
                # >> actual screenshoot is PNG. An auxiliar function that gets the actual
                # >> imagename is required.
                # art_URL = art_disp_URL.replace('/s/', '/l/')
                
                if asset_kind == ASSET_TITLE and art_name.find('Title') >= 0:
                    # >> Go to artwork page and get actual filename. Skip if empty string returned.
                    art_URL = self.get_shot_URL(art_page_URL)
                    if not art_URL: continue
                    log_debug('asset_MobyGames::get_images() Adding Title #{0} {1}'.format(cover_index, art_name))
                    img_name = 'Title #{0}: {1}'.format(cover_index, art_name)
                    images.append({'name' : img_name, 'URL' : art_URL, 'disp_URL' : art_disp_URL})
                    cover_index += 1
                elif asset_kind == ASSET_SNAP and not art_name.find('Title') >= 0:
                    # >> Go to artwork page and get actual filename. Skip if empty string returned.
                    art_URL = self.get_shot_URL(art_page_URL)
                    if not art_URL: continue
                    log_debug('asset_MobyGames::get_images() Adding Snap #{0} {1}'.format(cover_index, art_name))
                    img_name = 'Snap #{0}: {1}'.format(cover_index, art_name)
                    images.append({'name' : img_name, 'URL' : art_URL, 'disp_URL' : art_disp_URL})
                    cover_index += 1

        elif asset_kind == ASSET_BOXFRONT or asset_kind == ASSET_BOXBACK or asset_kind == ASSET_CARTRIDGE:
            game_id_url = 'http://www.mobygames.com' + game['id'] + '/cover-art'
            A = assets_get_info_scheme(asset_kind)
            log_debug('asset_MobyGames::get_images() game_id_url = {0}'.format(game_id_url))
            log_debug('asset_MobyGames::get_images() asset_kind  = {0}'.format(A.name))
            page_data = net_get_URL_oneline(game_id_url)
            # text_dump_str_to_file('MobyGames-cover-art.txt', page_data)

            # <div class="thumbnail-image-wrapper">
            # <a href="/game/snes/super-metroid/cover-art/gameCoverId,16501/" 
            #  title="Super Metroid SNES Front Cover" class="thumbnail-cover" 
            #  style="background-image:url(/images/covers/s/16501-super-metroid-snes-front-cover.jpg);">
            # </a></div>
            rlist = re.findall(
                '<div class="thumbnail-image-wrapper">       ' +
                '<a href="(.*?)" title="(.*?)" class="thumbnail-cover" style="background-image:url\((.*?)\);">' +
                '</a>      </div>', page_data)
            # print('Cover-Art rlist = ' + unicode(rlist))
            cover_index = 1
            for index, rtuple in enumerate(rlist):
                art_page_URL = rtuple[0]
                art_name     = rtuple[1]
                art_disp_URL = 'http://www.mobygames.com' + rtuple[2]
                art_URL      = art_disp_URL.replace('/s/', '/l/')
                
                if asset_kind == ASSET_BOXFRONT and art_name.find('Front Cover') >= 0:
                    log_debug('asset_MobyGames::get_images() Adding Boxfront #{0} {1}'.format(cover_index, art_name))
                    img_name = 'Boxfront #{0}: {1}'.format(cover_index, art_name)
                    images.append({'name' : img_name, 'URL' : art_URL, 'disp_URL' : art_disp_URL})
                    cover_index += 1
                elif asset_kind == ASSET_BOXBACK and art_name.find('Back Cover') >= 0:
                    log_debug('asset_MobyGames::get_images() Adding Boxback #{0} {1}'.format(cover_index, art_name))
                    img_name = 'Boxback #{0}: {1}'.format(cover_index, art_name)
                    images.append({'name' : img_name, 'URL' : art_URL, 'disp_URL' : art_disp_URL})
                    cover_index += 1
                elif asset_kind == ASSET_CARTRIDGE and art_name.find('Media') >= 0:
                    log_debug('asset_MobyGames::get_images() Adding Cartridge #{0} {1}'.format(cover_index, art_name))
                    img_name = 'Cartridge #{0}: {1}'.format(cover_index, art_name)
                    images.append({'name' : img_name, 'URL' : art_URL, 'disp_URL' : art_disp_URL})
                    cover_index += 1

        return images

    #
    # Get screenshot image URL.
    #
    def get_shot_URL(self, art_page_URL):
        log_debug('asset_MobyGames::get_shot_URL() art_page_URL = {0}'.format(art_page_URL))
        page_data = net_get_URL_oneline(art_page_URL)
        # text_dump_str_to_file(os.path.join('E:/', 'MobyGames-get_shot_URL.txt'), page_data)
        
        # <img 
        #  title="" 
        #  alt="Super Mario World SNES Title screen" 
        #  border="0" 
        #  src="/images/shots/l/218703-super-mario-world-snes-screenshot-title-screen.png" 
        #  height="448" 
        #  width="512" ><h3>
        rlist = re.findall('<div class="screenshot">'
                           '<img title="(.*?)" alt="(.*?)" border="(.*?)" src="(.*?)" height="(.*?)" width="(.*?)" >'
                           '<h3>', page_data)
        # log_debug('Screenshots rlist = ' + unicode(rlist))
        art_URL = ''
        if len(rlist) > 0: art_URL = 'http://www.mobygames.com' + rlist[0][3]
        log_debug('asset_MobyGames::get_shot_URL() art_URL = {0}'.format(art_URL))

        return art_URL

# -------------------------------------------------------------------------------------------------
# Arcade Database (for MAME only) http://adb.arcadeitalia.net/
# -------------------------------------------------------------------------------------------------
class asset_ArcadeDB(Scraper_Asset, Scraper_ArcadeDB):
    def __init__(self):
        self.name = 'Arcade Database'
        Scraper_ArcadeDB.__init__(self)

    # Call common code in parent class
    def get_search(self, search_string, rom_base_noext, platform):
        return Scraper_ArcadeDB.get_search(self, search_string, rom_base_noext, platform)

    def set_options(self, region, imgsize):
        pass

    def supports_asset(self, asset_kind):
        return False

    def get_images(self, game, asset_kind):
        images = []

        return images

# -------------------------------------------------------------------------------------------------
# Google asset scraper
# -------------------------------------------------------------------------------------------------
class asset_Google(Scraper_Asset):
    def __init__(self):
        self.name = 'Google'

    def set_options(self, region, imgsize):
        pass

    def get_search(self, search_string, rom_base_noext, platform):
        return []

    # Checks this... I think Google image search API is deprecated.
    def get_images(self, game):
      qdict = {'q':search, 'imgsz':imgsize}
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
