# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher scraping engine
#

# Copyright (c) 2016-2017 Wintermute0110 <wintermute0110@gmail.com>
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
import pprint

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
        Scraper_TheGamesDB.__init__(self)
        self.name = 'TheGamesDB'
        # >> Cache page data in get_images()
        self.get_images_cached_game_id_url = ''
        self.get_images_cached_page_data   = ''

    # Get a URL text and cache it.
    def get_URL_and_cache(self, game_id_url):
        # >> Check if URL page data is in cache. If so it's a cache hit. If cache miss, then update cache.
        if self.get_images_cached_game_id_url == game_id_url:
            log_debug('asset_TheGamesDB::get_URL_and_cache Cache HIT')
            page_data = self.get_images_cached_page_data
        else:
            log_debug('asset_TheGamesDB::get_URL_and_cache Cache MISS. Updating cache')
            page_data = net_get_URL_oneline(game_id_url)
            self.get_images_cached_game_id_url = game_id_url
            self.get_images_cached_page_data   = page_data

        return page_data

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
        AInfo = assets_get_info_scheme(asset_kind)
        log_debug('asset_TheGamesDB::get_images game_id_url = {0}'.format(game_id_url))
        log_debug('asset_TheGamesDB::get_images asset_kind  = {0}'.format(AInfo.name))
        page_data = self.get_URL_and_cache(game_id_url)

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
        Scraper_GameFAQs.__init__(self)
        self.name = 'GameFAQs'
        self.get_images_cached_game_id_url = ''
        self.get_images_cached_page_data   = ''

    # Get a URL text and cache it.
    def get_URL_and_cache(self, game_id_url):
        # >> Check if URL page data is in cache. If so it's a cache hit. If cache miss, then update cache.
        if self.get_images_cached_game_id_url == game_id_url:
            log_debug('asset_GameFAQs::get_URL_and_cache Cache HIT')
            page_data = self.get_images_cached_page_data
        else:
            log_debug('asset_GameFAQs::get_URL_and_cache Cache MISS. Updating cache')
            page_data = net_get_URL_oneline(game_id_url)
            self.get_images_cached_game_id_url = game_id_url
            self.get_images_cached_page_data   = page_data

        return page_data

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
        AInfo = assets_get_info_scheme(asset_kind)
        log_debug('asset_GameFAQs::get_images game_id_url = {0}'.format(game_id_url))
        log_debug('asset_GameFAQs::get_images asset_kind  = {0}'.format(AInfo.name))
        page_data = self.get_URL_and_cache(game_id_url)

        # --- Retrieve assets ---
        if asset_kind == ASSET_TITLE or asset_kind == ASSET_SNAP:
            # URL Examples: 
            # http://www.gamefaqs.com/snes/588741-super-metroid/images
            # http://www.gamefaqs.com/snes/519824-super-mario-world/images
            # <td class="thumb">
            # <a href="/snes/588741-super-metroid/images/21">
            # <img class="imgboxart" src="http://img.gamefaqs.net/screens/1/4/8/gfs_4598_1_1_thm.jpg" />
            # </a>
            # </td>
            results = re.findall('<td class="thumb"><a href="(.+?)">'
                                 '<img class="imgboxart" src="(.+?)" /></a></td>', page_data)
            # print(results)

            # >> Title is usually the first or first snapshoots in GameFAQs.
            for index, boxart in enumerate(results):
                log_debug('asset_GameFAQs::get_images '
                          'Screenshot artwork page #{0:02d} "{1}" (thumb "{2}")'.format(index + 1, boxart[0], boxart[1]))
                name_str = 'Screenshoot #{0}'.format(index + 1)
                images.append({'name' : name_str, 'id' : 'http://www.gamefaqs.com' + boxart[0], 
                               'URL' : boxart[1], 'asset_kind' : asset_kind})

        elif asset_kind == ASSET_BOXFRONT or asset_kind == ASSET_BOXBACK:
            # --- Parse game thumb information ---
            # The Game Images URL shows a page with boxart and screenshots thumbnails.
            # Boxart can be diferent depending on the ROM/game region. Each region has then a 
            # separate page with the full size artwork (boxfront, boxback, etc.)
            #
            # URL Example:
            # http://www.gamefaqs.com/snes/588741-super-metroid/images
            #
            # <div class="img boxshot">
            #  <a href="/snes/588741-super-metroid/images/14598">
            #  <img class="img100 imgboxart" src="http://img.gamefaqs.net/box/3/2/1/51321_thumb.jpg" alt="Super Metroid (JP)" />
            #  </a>
            #  <div class="region">JP 03/19/94</div>
            # </div>
            results = re.findall('<div class="img boxshot"><a href="(.+?)">'
                                 '<img class="img100 imgboxart" src="(.+?)" alt="(.+?)" /></a>', page_data)
            # print(results)

            # --- Choose one full size artwork page based on game region ---
            for index, boxart in enumerate(results):
                log_debug('asset_GameFAQs::get_images '
                          'Boxart artwork page #{0:02d} "{1}" (thumb "{2}")'.format(index + 1, boxart[0], boxart[1]))
                name_str = 'Boxart #{0}'.format(index + 1)
                images.append({'name' : name_str, 'id' : 'http://www.gamefaqs.com' + boxart[0],
                               'URL' : boxart[1], 'asset_kind' : asset_kind})

        return images

    #
    # image_dic['id'] has the URL of the artwork page.
    #
    def resolve_image_URL(self, image_dic):
        log_debug('asset_GameFAQs::resolve_image_URL Resolving {0}'.format(image_dic['name']))
        
        # --- Go to full size page and get thumb ---
        asset_kind = image_dic['asset_kind']
        image_url  = image_dic['id']
        page_data  = net_get_URL_oneline(image_url)
        # text_dump_str_to_file(page_data, 'page_data.txt')

        if asset_kind == ASSET_TITLE or asset_kind == ASSET_SNAP:
            # In an screenshot artwork page there is only one image.
            # URL Example:
            # http://www.gamefaqs.com/snes/588741-super-metroid/images/21
            #
            # <div class="img">
            #  <a href="http://img.gamefaqs.net/screens/5/1/f/gfs_4598_1_1.jpg">
            #   <img class="full_boxshot" src="http://img.gamefaqs.net/screens/5/1/f/gfs_4598_1_1.jpg" alt="Super Metroid Screenshot">
            #  </a>
            # </div>
            results = re.findall('<img class="full_boxshot" src="(.+?)" alt="(.+?)">', page_data)
            # print(results)
            if results:
                image_url = results[0][0]
                image_ext = text_get_image_URL_extension(image_url)
                return (image_url, image_ext)

        elif asset_kind == ASSET_BOXFRONT or asset_kind == ASSET_BOXBACK:
            # NOTE findall() returns a list of tuples, not a match object!
            # In an Boxart artwork page there is typically several images.
            # URL Examples:
            # http://www.gamefaqs.com/snes/588741-super-metroid/images/1277946
            #
            # <a href="http://img.gamefaqs.net/box/3/2/1/51321_front.jpg">
            # <img class="full_boxshot" src="http://img.gamefaqs.net/box/3/2/1/51321_front.jpg" alt="Super Metroid Box Front" />
            # </a>
            results = re.findall('<img class="full_boxshot" src="(.+?)" alt="(.+?)" /></a>', page_data)
            # print(results)
            
            # >> Return as soon as a Boxart assets if found
            for index, boxart in enumerate(results):
                art_name = boxart[1]
                if asset_kind == ASSET_BOXFRONT and art_name.find('Front') >= 0:
                    image_url = boxart[0]
                    image_ext = text_get_image_URL_extension(image_url)
                    return (image_url, image_ext)

                elif asset_kind == ASSET_BOXBACK and art_name.find('Back') >= 0:
                    image_url = boxart[0]
                    image_ext = text_get_image_URL_extension(image_url)
                    return (image_url, image_ext)

        return ('', '')

# -------------------------------------------------------------------------------------------------
# MobyGames
# -------------------------------------------------------------------------------------------------
class asset_MobyGames(Scraper_Asset, Scraper_MobyGames):
    def __init__(self):
        Scraper_MobyGames.__init__(self)
        self.name = 'MobyGames'
        self.get_images_cached_game_id_url = ''
        self.get_images_cached_page_data   = ''

    # --- Get a URL text and cache it ---
    def get_URL_and_cache(self, game_id_url):
        # >> Check if URL page data is in cache. If so it's a cache hit. If cache miss, then update cache.
        if self.get_images_cached_game_id_url == game_id_url:
            log_debug('asset_MobyGames::get_URL_and_cache Cache HIT')
            page_data = self.get_images_cached_page_data
        else:
            log_debug('asset_MobyGames::get_URL_and_cache Cache MISS. Updating cache')
            page_data = net_get_URL_oneline(game_id_url)
            self.get_images_cached_game_id_url = game_id_url
            self.get_images_cached_page_data   = page_data

        return page_data

    # Call common code in parent class
    def get_search(self, search_string, rom_base_noext, platform):
        return Scraper_MobyGames.get_search(self, search_string, rom_base_noext, platform)

    def set_options(self, region, imgsize):
        pass

    def supports_asset(self, asset_kind):
        if asset_kind == ASSET_TITLE    or asset_kind == ASSET_SNAP    or \
           asset_kind == ASSET_BOXFRONT or asset_kind == ASSET_BOXBACK or asset_kind == ASSET_CARTRIDGE:
           return True

        return False

    #
    # 'asset_kind' is a MobyGames additional field.
    #
    def get_images(self, game, asset_kind):
        images = []

        # --- If asset kind not supported return inmediately ---
        if not self.supports_asset(asset_kind): return images

        if asset_kind == ASSET_TITLE or asset_kind == ASSET_SNAP:
            game_id_url = 'http://www.mobygames.com' + game['id'] + '/screenshots'
        elif asset_kind == ASSET_BOXFRONT or asset_kind == ASSET_BOXBACK or asset_kind == ASSET_CARTRIDGE:
            game_id_url = 'http://www.mobygames.com' + game['id'] + '/cover-art'
        AInfo = assets_get_info_scheme(asset_kind)
        log_debug('asset_MobyGames::get_images() game_id_url = {0}'.format(game_id_url))
        log_debug('asset_MobyGames::get_images() asset_kind  = {0}'.format(AInfo.name))
        page_data = self.get_URL_and_cache(game_id_url)
        # text_dump_str_to_file('MobyGames-game_id_url.txt', page_data)

        if asset_kind == ASSET_TITLE or asset_kind == ASSET_SNAP:
            # NOTE findall() returns a list of tuples, not a match object!
            # URL Examples:
            # http://www.mobygames.com/game/snes/super-mario-world/screenshots/
            #
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
                art_name     = text_unescape_HTML(rtuple[1])
                art_page_URL = 'http://www.mobygames.com' + rtuple[0]
                art_disp_URL = 'http://www.mobygames.com' + rtuple[2]
                # >> NOTE: thumbnail is JPG and the actual screenshoot could be PNG. An auxiliar 
                # >> function that gets the actual image URL is required.
                if asset_kind == ASSET_TITLE and art_name.find('Title') >= 0:
                    log_debug('asset_MobyGames::get_images() Adding Title #{0} {1}'.format(cover_index, art_name))
                    img_name = 'Title #{0:02d}: {1}'.format(cover_index, art_name)
                    images.append({'name' : img_name, 'id' : art_page_URL, 'URL' : art_disp_URL, 'asset_kind' : asset_kind})
                    cover_index += 1
                elif asset_kind == ASSET_SNAP and not art_name.find('Title') >= 0:
                    log_debug('asset_MobyGames::get_images() Adding Snap #{0} {1}'.format(cover_index, art_name))
                    img_name = 'Snap #{0:02d}: {1}'.format(cover_index, art_name)
                    images.append({'name' : img_name, 'id' : art_page_URL, 'URL' : art_disp_URL, 'asset_kind' : asset_kind})
                    cover_index += 1

        elif asset_kind == ASSET_BOXFRONT or asset_kind == ASSET_BOXBACK or asset_kind == ASSET_CARTRIDGE:
            # URL examples:
            # http://www.mobygames.com/game/snes/super-mario-world/cover-art/
            #
            # <div class="thumbnail-image-wrapper">
            # <a href="/game/snes/super-metroid/cover-art/gameCoverId,16501/" 
            #  title="Super Metroid SNES Front Cover" class="thumbnail-cover" 
            #  style="background-image:url(/images/covers/s/16501-super-metroid-snes-front-cover.jpg);">
            # </a></div>
            # <div class="thumbnail-cover-caption">        <p>Front Cover</p>      </div>
            #
            rlist = re.findall(
                '<div class="thumbnail-image-wrapper">       ' +
                '<a href="(.*?)" title="(.*?)" class="thumbnail-cover" style="background-image:url\((.*?)\);">' +
                '</a>      </div>      ' + 
                '<div class="thumbnail-cover-caption">        <p>(.*?)</p>      </div>', page_data)
            # log_debug('Cover-Art rlist = {0}'.format(rlist))
            cover_index = 1
            for index, rtuple in enumerate(rlist):
                art_name     = text_unescape_HTML(rtuple[1])
                art_page_URL = 'http://www.mobygames.com' + rtuple[0]
                art_disp_URL = 'http://www.mobygames.com' + rtuple[2]
                if asset_kind == ASSET_BOXFRONT and art_name.find('Front Cover') >= 0:
                    log_debug('asset_MobyGames::get_images() Adding Boxfront #{0} {1}'.format(cover_index, art_name))
                    img_name = 'Boxfront #{0:02d}: {1}'.format(cover_index, art_name)
                    images.append({'name' : img_name, 'id' : art_page_URL, 'URL' : art_disp_URL, 'asset_kind' : asset_kind})
                    cover_index += 1
                elif asset_kind == ASSET_BOXBACK and art_name.find('Back Cover') >= 0:
                    log_debug('asset_MobyGames::get_images() Adding Boxback #{0} {1}'.format(cover_index, art_name))
                    img_name = 'Boxback #{0:02d}: {1}'.format(cover_index, art_name)
                    images.append({'name' : img_name, 'id' : art_page_URL, 'URL' : art_disp_URL, 'asset_kind' : asset_kind})
                    cover_index += 1
                elif asset_kind == ASSET_CARTRIDGE and art_name.find('Media') >= 0:
                    log_debug('asset_MobyGames::get_images() Adding Cartridge #{0} {1}'.format(cover_index, art_name))
                    img_name = 'Cartridge #{0:02d}: {1}'.format(cover_index, art_name)
                    images.append({'name' : img_name, 'id' : art_page_URL, 'URL' : art_disp_URL, 'asset_kind' : asset_kind})
                    cover_index += 1

        return images

    #
    # Get screenshot image URL.
    #
    def get_shot_image_URL(self, art_page_URL):
        log_debug('asset_MobyGames::get_shot_image_URL() art_page_URL = {0}'.format(art_page_URL))
        page_data = net_get_URL_oneline(art_page_URL)
        # text_dump_str_to_file(os.path.join('E:/', 'MobyGames-get_shot_image_URL.txt'), page_data)
        
        # <div class="screenshot">
        # <img 
        #  title="" 
        #  alt="Super Mario World SNES Title screen" 
        #  border="0" 
        #  src="/images/shots/l/218703-super-mario-world-snes-screenshot-title-screen.png" 
        #  height="448" width="512" ><h3>
        rlist = re.findall('<div class="screenshot">'
                           '<img title="(.*?)" alt="(.*?)" border="(.*?)" src="(.*?)" height="(.*?)" width="(.*?)" >'
                           '<h3>', page_data)
        # log_debug('Screenshots rlist = ' + unicode(rlist))
        art_URL = ''
        if len(rlist) > 0: art_URL = 'http://www.mobygames.com' + rlist[0][3]
        log_debug('asset_MobyGames::get_shot_image_URL() art_URL = {0}'.format(art_URL))

        return art_URL

    #
    # Get cover image URL.
    #
    def get_cover_image_URL(self, art_page_URL):
        log_debug('asset_MobyGames::get_cover_image_URL() art_page_URL = {0}'.format(art_page_URL))
        page_data = net_get_URL_oneline(art_page_URL)
        # text_dump_str_to_file(os.path.join('/home/mendi/', 'MobyGames-get_cover_image_URL.txt'), page_data)

        # <br><center>
        # <img 
        #  alt="Sonic the Hedgehog SEGA Master System Media" 
        #  border="0" 
        #  src="/images/covers/l/122094-sonic-the-hedgehog-sega-master-system-media.png" 
        #  height="508" width="800" >
        # </center><br>
        rlist = re.findall('<br><center>'
                           '<img alt="(.*?)" border="(.*?)" src="(.*?)" height="(.*?)" width="(.*?)" >'
                           '</center><br>', page_data)
        # log_debug('Cover rlist = ' + unicode(rlist))
        art_URL = ''
        if len(rlist) > 0: art_URL = 'http://www.mobygames.com' + rlist[0][2]
        log_debug('asset_MobyGames::get_cover_image_URL() art_URL = {0}'.format(art_URL))

        return art_URL

    def resolve_image_URL(self, image_dic):
        log_debug('asset_MobyGames::resolve_image_URL() Resolving {0}'.format(image_dic['name']))
        asset_kind = image_dic['asset_kind']

        # >> Go to artwork page and get actual filename. Skip if empty string returned.
        if asset_kind == ASSET_TITLE or asset_kind == ASSET_SNAP:
            image_url = self.get_shot_image_URL(image_dic['id'])
        elif asset_kind == ASSET_BOXFRONT or asset_kind == ASSET_BOXBACK or asset_kind == ASSET_CARTRIDGE:
            image_url = self.get_cover_image_URL(image_dic['id'])
        else:
            log_error('asset_MobyGames::resolve_image_URL() Wrong asset_kind =  {0}'.format(asset_kind))
            return ('', '')

        # >> Get image extension from URL
        if not image_url: return ('', '')
        image_ext = text_get_image_URL_extension(image_url)
        
        return (image_url, image_ext)

# -------------------------------------------------------------------------------------------------
# Arcade Database (for MAME only) http://adb.arcadeitalia.net/
# -------------------------------------------------------------------------------------------------
class asset_ArcadeDB(Scraper_Asset, Scraper_ArcadeDB):
    def __init__(self):
        Scraper_ArcadeDB.__init__(self)
        self.name = 'Arcade Database'
        self.get_images_cached_game_id_url   = ''
        self.get_images_cached_page_data = ''

    # --- Get a URL text and cache it ---
    def get_URL_and_cache(self, game_id_url):
        # >> Check if URL page data is in cache. If so it's a cache hit. If cache miss, then update cache.
        if self.get_images_cached_game_id_url == game_id_url:
            log_debug('asset_ArcadeDB::get_URL_and_cache Cache HIT')
            page_data = self.get_images_cached_page_data
        else:
            log_debug('asset_ArcadeDB::get_URL_and_cache Cache MISS. Updating cache')
            page_data = net_get_URL_oneline(game_id_url)
            self.get_images_cached_game_id_url = game_id_url
            self.get_images_cached_page_data   = page_data

        return page_data

    # Call common code in parent class
    def get_search(self, search_string, rom_base_noext, platform):
        return Scraper_ArcadeDB.get_search(self, search_string, rom_base_noext, platform)

    def set_options(self, region, imgsize):
        pass

    def supports_asset(self, asset_kind):
        if asset_kind == ASSET_TITLE     or asset_kind == ASSET_SNAP      or \
           asset_kind == ASSET_BANNER    or asset_kind == ASSET_CLEARLOGO or \
           asset_kind == ASSET_BOXFRONT  or asset_kind == ASSET_BOXBACK   or \
           asset_kind == ASSET_CARTRIDGE or asset_kind == ASSET_FLYER:
           return True

        return False

    def get_images(self, game, asset_kind):
        images = []

        # --- If asset kind not supported return inmediately ---
        if not self.supports_asset(asset_kind): return images
        
        # --- Get game info page ---
        # >> Not needed, game artwork is obtained with AJAX.
        # game_id_url = game['id'] 
        # log_debug('asset_ArcadeDB::get_metadata game_id_url "{0}"'.format(game_id_url))
        # page_data = self.get_URL_and_cache(game_id_url)
        # text_dump_str_to_file('ArcadeDB-game_id_url.txt', page_data)

        #
        # <li class="mostra_archivio cursor_pointer" title="Show all images, videos and documents archived for this game"> 
        # <a href="javascript:void mostra_media_archivio();"> <span>Other files</span> </a>
        #
        # Function void mostra_media_archivio(); is in file http://adb.arcadeitalia.net/dettaglio_mame.js?release=87
        #
        # AJAX call >> view-source:http://adb.arcadeitalia.net/dettaglio_mame.php?ajax=mostra_media_archivio&game_name=toki
        # AJAX returns HTML code:
        # <xml><html>
        # <content1 id='elenco_anteprime' type='html'>%26lt%3Bli%20class......gt%3B</content1>
        # </html><result></result><message><code></code><title></title><type></type><text></text></message></xml>
        #
        # pprint.pprint(game)
        AInfo = assets_get_info_scheme(asset_kind)
        log_debug('asset_ArcadeDB::get_metadata game ID "{0}"'.format(game['id']))
        log_debug('asset_ArcadeDB::get_metadata name    "{0}"'.format(game['mame_name']))
        log_debug('asset_ArcadeDB::get_metadata Asset   {0}'.format(AInfo.name))
        AJAX_URL  = 'http://adb.arcadeitalia.net/dettaglio_mame.php?ajax=mostra_media_archivio&game_name={0}'.format(game['mame_name'])
        page_data = self.get_URL_and_cache(AJAX_URL)
        rcode     = re.findall('<xml><html><content1 id=\'elenco_anteprime\' type=\'html\'>(.*?)</content1></html>', page_data)
        if not rcode: return images
        raw_HTML     = rcode[0]
        decoded_HTML = text_decode_HTML(raw_HTML)
        escaped_HTML = text_unescape_HTML(decoded_HTML)
        # text_dump_str_to_file('ArcadeDB-get_images-AJAX-dino-raw.txt', raw_HTML)
        # text_dump_str_to_file('ArcadeDB-get_images-AJAX-dino-decoded.txt', decoded_HTML)
        # text_dump_str_to_file('ArcadeDB-get_images-AJAX-dino-escaped.txt', escaped_HTML)

        #
        # <li class='cursor_pointer' tag="Boss-0" onclick="javascript:set_media(this,'Boss','current','4','0');"  title="Boss" ><div>
        # <img media_id='1' class='colorbox_image' src='http://adb.arcadeitalia.net/media/mame.current/bosses/small/toki.png'
        #      src_full="http://adb.arcadeitalia.net/media/mame.current/bosses/toki.png"></img>
        # </div><span>Boss</span></li>
        # <li class='cursor_pointer' tag="Cabinet-0" onclick="javascript:set_media(this,'Cabinet','current','5','0');"  title="Cabinet" ><div>
        # <img media_id='2' class='colorbox_image' src='http://adb.arcadeitalia.net/media/mame.current/cabinets/small/toki.png'
        #      src_full="http://adb.arcadeitalia.net/media/mame.current/cabinets/toki.png"></img>
        # </div><span>Cabinet</span></li>
        # .....
        # <li class='cursor_pointer'  title="Manuale" >
        # <a href="http://adb.arcadeitalia.net/download_file.php?tipo=mame_current&amp;codice=toki&amp;entity=manual&amp;oper=view&amp;filler=toki.pdf" target='_blank'>
        # <img src='http://adb.arcadeitalia.net/media/mame.current/manuals/small/toki.png'></img><br/><span>Manuale</span></a></li>
        #
        cover_index = 1
        if asset_kind == ASSET_TITLE:
            rlist = re.findall(
                '<li class=\'cursor_pointer\' tag="Titolo-[0-9]" onclick="(.*?)"  title="(.*?)" >' +
                '<div><img media_id=\'(.*?)\' class=\'colorbox_image\' src=\'(.*?)\' src_full="(.*?)"></img></div>', escaped_HTML)
            # pprint.pprint(rlist)
            for index, rtuple in enumerate(rlist):
                img_name = 'Title #{0:02d}'.format(cover_index)
                art_URL = rtuple[4]
                art_disp_URL = rtuple[3]
                log_debug('asset_ArcadeDB::get_images() Adding Title #{0:02d}'.format(cover_index))
                images.append({'name' : img_name, 'id' : art_URL, 'URL' : art_disp_URL})
                cover_index += 1

        elif asset_kind == ASSET_SNAP:
            rlist = re.findall(
                '<li class=\'cursor_pointer\' tag="Gioco-[0-9]" onclick="(.*?)"  title="(.*?)" >' +
                '<div><img media_id=\'(.*?)\' class=\'colorbox_image\' src=\'(.*?)\' src_full="(.*?)"></img></div>', escaped_HTML)
            for index, rtuple in enumerate(rlist):
                img_name = 'Snap #{0:02d}'.format(cover_index)
                art_URL = rtuple[4]
                art_disp_URL = rtuple[3]
                log_debug('asset_ArcadeDB::get_images() Adding Snap #{0:02d}'.format(cover_index))
                images.append({'name' : img_name, 'id' : art_URL, 'URL' : art_disp_URL})
                cover_index += 1

        # Banner is Marquee
        elif asset_kind == ASSET_BANNER:
            rlist = re.findall(
                '<li class=\'cursor_pointer\' tag="Marquee-[0-9]" onclick="(.*?)"  title="(.*?)" >' +
                '<div><img media_id=\'(.*?)\' class=\'colorbox_image\' src=\'(.*?)\' src_full="(.*?)"></img></div>', escaped_HTML)
            for index, rtuple in enumerate(rlist):
                img_name = 'Banner/Marquee #{0:02d}'.format(cover_index)
                art_URL = rtuple[4]
                art_disp_URL = rtuple[3]
                log_debug('asset_ArcadeDB::get_images() Adding Banner/Marquee #{0:02d}'.format(cover_index))
                images.append({'name' : img_name, 'id' : art_URL, 'URL' : art_disp_URL})
                cover_index += 1

        # Clearlogo is called Decal in ArcadeDB
        elif asset_kind == ASSET_CLEARLOGO:
            rlist = re.findall(
                '<li class=\'cursor_pointer\' tag="Scritta-[0-9]" onclick="(.*?)"  title="(.*?)" >' +
                '<div><img media_id=\'(.*?)\' class=\'colorbox_image\' src=\'(.*?)\' src_full="(.*?)"></img></div>', escaped_HTML)
            for index, rtuple in enumerate(rlist):
                img_name = 'Clearlogo #{0:02d}'.format(cover_index)
                art_URL = rtuple[4]
                art_disp_URL = rtuple[3]
                log_debug('asset_ArcadeDB::get_images() Adding Clearlogo #{0:02d}'.format(cover_index))
                images.append({'name' : img_name, 'id' : art_URL, 'URL' : art_disp_URL})
                cover_index += 1

        # Boxfront is Cabinet
        elif asset_kind == ASSET_BOXFRONT:
            rlist = re.findall(
                '<li class=\'cursor_pointer\' tag="Cabinet-[0-9]" onclick="(.*?)"  title="(.*?)" >' +
                '<div><img media_id=\'(.*?)\' class=\'colorbox_image\' src=\'(.*?)\' src_full="(.*?)"></img></div>', escaped_HTML)
            for index, rtuple in enumerate(rlist):
                img_name = 'Boxfront/Cabinet #{0:02d}'.format(cover_index)
                art_URL = rtuple[4]
                art_disp_URL = rtuple[3]
                log_debug('asset_ArcadeDB::get_images() Adding Boxfront/Cabinet #{0:02d}'.format(cover_index))
                images.append({'name' : img_name, 'id' : art_URL, 'URL' : art_disp_URL})
                cover_index += 1

        # Boxback is ControlPanel
        elif asset_kind == ASSET_BOXBACK:
            rlist = re.findall(
                '<li class=\'cursor_pointer\' tag="CPO-[0-9]" onclick="(.*?)"  title="(.*?)" >' +
                '<div><img media_id=\'(.*?)\' class=\'colorbox_image\' src=\'(.*?)\' src_full="(.*?)"></img></div>', escaped_HTML)
            for index, rtuple in enumerate(rlist):
                img_name = 'Boxback/CPanel #{0:02d}'.format(cover_index)
                art_URL = rtuple[4]
                art_disp_URL = rtuple[3]
                log_debug('asset_ArcadeDB::get_images() Adding Boxback/CPanel #{0:02d}'.format(cover_index))
                images.append({'name' : img_name, 'id' : art_URL, 'URL' : art_disp_URL})
                cover_index += 1

        # Cartridge is PCB
        elif asset_kind == ASSET_CARTRIDGE:
            rlist = re.findall(
                '<li class=\'cursor_pointer\' tag="PCB-[0-9]" onclick="(.*?)"  title="(.*?)" >' +
                '<div><img media_id=\'(.*?)\' class=\'colorbox_image\' src=\'(.*?)\' src_full="(.*?)"></img></div>', escaped_HTML)
            for index, rtuple in enumerate(rlist):
                img_name = 'Cartridge/PCB #{0:02d}'.format(cover_index)
                art_URL = rtuple[4]
                art_disp_URL = rtuple[3]
                log_debug('asset_ArcadeDB::get_images() Adding Cartridge/PCB #{0:02d}'.format(cover_index))
                images.append({'name' : img_name, 'id' : art_URL, 'URL' : art_disp_URL})
                cover_index += 1

        elif asset_kind == ASSET_FLYER:
            rlist = re.findall(
                '<li class=\'cursor_pointer\' tag="Volantino-[0-9]" onclick="(.*?)"  title="(.*?)" >' +
                '<div><img media_id=\'(.*?)\' class=\'colorbox_image\' src=\'(.*?)\' src_full="(.*?)"></img></div>', escaped_HTML)
            for index, rtuple in enumerate(rlist):
                img_name = 'Flyer #{0:02d}'.format(cover_index)
                art_URL = rtuple[4]
                art_disp_URL = rtuple[3]
                log_debug('asset_ArcadeDB::get_images() Adding Flyer #{0:02d}'.format(cover_index))
                images.append({'name' : img_name, 'id' : art_URL, 'URL' : art_disp_URL})
                cover_index += 1

        return images

    #
    # image_dic['id'] has the URL of the full size image
    #
    def resolve_image_URL(self, image_dic):
        log_debug('asset_ArcadeDB::resolve_image_URL Resolving {0}'.format(image_dic['name']))
        image_url = image_dic['id']
        image_ext = text_get_image_URL_extension(image_url)
        
        return (image_url, image_ext)
