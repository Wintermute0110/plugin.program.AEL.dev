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

# -----------------------------------------------------------------------------
# We support online an offline scrapers.
# Note that this module does not depend on Kodi stuff at all, and can be
# called externally from console Python scripts for testing of the scrapers.
# -----------------------------------------------------------------------------

from scrap import *

# -----------------------------------------------------------------------------
# Metadata scrapers base class
# -----------------------------------------------------------------------------
# All scrapers (offline or online) must implement the abstract methods.
# Metadata scrapers are for ROMs and standalone launchers (games)
# Metadata for machines (consoles, computers) should be different, I guess...
class Scraper_Metadata(Scraper):
    # Offline XML data will be cached here (from disk)
    games = {}

    # Load XML information for this scraper and keep it cached in memory.
    # For offline scrapers.
    def initialise_scraper(self, gamesys):
        xml_file = offline_scrapers_dic[gamesys]
        self.games = fs_load_GameInfo_XML(xml_file)

    # This function is called when the user wants to search a whole list of
    # games. It returns gamesys information.
    #
    # Returns:
    #   results = [game, game, ... ]
    #   display = [string, string, ... ]
    def get_game_list(self, search_string):
        raise NotImplementedError("Subclass must implement get_metadata() abstract method")

    # This is called after get_games_list() to get metadata of a particular ROM.
    # game_url univocally determines how to get the game metadata. For online
    # scrapers it is an URL. For offline scrapers it is the No-Intro or MAME name.
    def get_game_data(self, game_url):
        raise NotImplementedError("Subclass must implement get_metadata() abstract method")
    
    # This is called in automatic scraping mode. Only one result is returned.
    # Argument gamesys is AEL official platform list, and it should be translated
    # to how the site names the system. 
    # Note that some scrapers (MAME) only support one gamesys.
    def get_game_data_first(self, search_string, gamesys):
        raise NotImplementedError("Subclass must implement get_metadata() abstract method")

# -----------------------------------------------------------------------------
# NULL scraper, does nothing
# -----------------------------------------------------------------------------
class metadata_NULL(Scraper_Metadata):
    def __init__(self):
        self.name = 'NULL'
        self.fancy_name = 'NULL Metadata scraper'

    def get_game_list(self, search_string):
        return []

    def get_game_data(self, game_url):
        return []
    
    def get_game_data_first(self, search_string, gamesys):
        return []

# -----------------------------------------------------------------------------
# Offline scraper using XML files for MAME ROMs.
# -----------------------------------------------------------------------------
class metadata_MAME(Scraper_Metadata):
    def __init__(self):
        self.name = 'MAME'
        self.fancy_name = 'MAME Metadata offline scraper'

    def initialise_scraper(self):
        Scraper_Metadata.initialise_scraper(self, 'MAME')

    # In MAME machines, the rom_name is exactly the key of the dictionary.
    def get_metadata(self, rom_name):
        __debug_get_metadata = 0
        log_verb('Searching for "{0}" in game name'.format(rom_name))

        if rom_name in self.games:
            print(' name         = "{0}"'.format(self.games[rom_name]['name']))
            print(' description  = "{0}"'.format(self.games[rom_name]['description']))
            print(' year         = "{0}"'.format(self.games[rom_name]['year']))
            print(' manufacturer = "{0}"'.format(self.games[rom_name]['manufacturer']))
        else:
            log_verb('Not found')

        return None

    def get_game_list(self, search_string):
        return []

    def get_game_data(self, game_url):
        return []
    
    def get_game_data_first(self, search_string, gamesys):
        return []

# -----------------------------------------------------------------------------
# Offline scraper using XML files for ROMs in No-Intro name format.
# -----------------------------------------------------------------------------
class metadata_NoIntro(Scraper_Metadata):
    def __init__(self):
        self.name = 'No-Intro'
        self.fancy_name = 'No-Intro Metadata offline scraper'
        
    # Search in-memory database and return metadata.  
    def get_metadata(self, rom_name):
        __debug_get_metadata = 0
        log_verb('Searching for "{0}" in game name'.format(rom_name))

        regexp = '.*{0}.*'.format(rom_name.lower())
        p = re.compile(regexp)
        log_debug('Search regexp "{0}"'.format(regexp))
        for key in self.games:
          # Make search case insensitive.
          name_str = self.games[key]['name'].lower()
          if __debug_get_metadata: log_debug('Test string "{0}"'.format(name_str))
          match = p.match(name_str)
          if match:
            print(' name        = "{0}"'.format(self.games[key]['name']))
            print(' description = "{0}"'.format(self.games[key]['description']))
            print(' year        = "{0}"'.format(self.games[key]['year']))

        return None

    def get_game_list(self, search_string):
        return []

    def get_game_data(self, game_url):
        return []
    
    def get_game_data_first(self, search_string, gamesys):
        return []

# -----------------------------------------------------------------------------
# TheGamesDB online metadata scraper
# -----------------------------------------------------------------------------
class metadata_TheGamesDB(Scraper_Metadata):
    def __init__(self):
        self.name = 'TheGamesDB'
        self.fancy_name = 'TheGamesDB Metadata scraper'

    def get_game_list(self, search_string):
        results = []
        display = []
        try:
            req = urllib2.Request('http://thegamesdb.net/api/GetGamesList.php?name='+urllib.quote_plus(search))
            req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
            f = urllib2.urlopen(req)
            page = f.read().replace("\n", "")
            games = re.findall("<Game><id>(.*?)</id><GameTitle>(.*?)</GameTitle>(.*?)<Platform>(.*?)</Platform></Game>", page)
            for item in games:
                game = {}
                game["id"] = "http://thegamesdb.net/api/GetGame.php?id="+item[0]
                game["title"] = item[1]
                game["gamesys"] = item[3]
                game["order"] = 1
                if ( game["title"].lower() == search.lower() ):
                    game["order"] += 1
                if ( game["title"].lower().find(search.lower()) != -1 ):
                    game["order"] += 1
                results.append(game)
                print game
            results.sort(key=lambda result: result["order"], reverse=True)
            for result in results:
                display.append(result["title"]+" / "+result["gamesys"])
            return results,display
        except:
            return results,display

    def get_game_data(self, game_url):
        gamedata = {}
        gamedata["genre"] = ""
        gamedata["release"] = ""
        gamedata["studio"] = ""
        gamedata["plot"] = ""
        try:
            req = urllib2.Request(game_url)
            req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
            f = urllib2.urlopen(req)
            page = f.read().replace('\n', '')
            game_genre = ' / '.join(re.findall('<genre>(.*?)</genre>', page))
            if game_genre:
                gamedata["genre"] = unescape(game_genre)
            game_release = ''.join(re.findall('<ReleaseDate>(.*?)</ReleaseDate>', page))
            if game_release:
                gamedata["release"] = unescape(game_release[-4:])
            game_studio = ''.join(re.findall('<Developer>(.*?)</Developer>', page))
            if game_studio:
                gamedata["studio"] = unescape(game_studio)
            game_plot = ''.join(re.findall('<Overview>(.*?)</Overview>', page))
            if game_plot:
                gamedata["plot"] = unescape(game_plot)
            return gamedata
        except:
            return gamedata
    
    def get_game_data_first(self, search_string, gamesys):
        platform = _system_conversion(gamesys)
        results = []
        try:
            req = urllib2.Request('http://thegamesdb.net/api/GetGamesList.php?name='+urllib.quote_plus(search)+'&platform='+urllib.quote_plus(platform))
            req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
            f = urllib2.urlopen(req)
            page = f.read().replace("\n", "")
            if (platform == "Sega Genesis" ) :
                req = urllib2.Request('http://thegamesdb.net/api/GetGamesList.php?name='+urllib.quote_plus(search)+'&platform='+urllib.quote_plus('Sega Mega Drive'))
                req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
                f2 = urllib2.urlopen(req)
                page = page + f2.read().replace("\n", "")
            games = re.findall("<Game><id>(.*?)</id><GameTitle>(.*?)</GameTitle>(.*?)<Platform>(.*?)</Platform></Game>", page)
            for item in games:
                game = {}
                game["id"] = "http://thegamesdb.net/api/GetGame.php?id="+item[0]
                game["title"] = item[1]
                game["gamesys"] = item[3]
                game["order"] = 1
                if ( game["title"].lower() == search.lower() ):
                    game["order"] += 1
                if ( game["title"].lower().find(search.lower()) != -1 ):
                    game["order"] += 1
                results.append(game)
            results.sort(key=lambda result: result["order"], reverse=True)
            return results
        except:
            return results

# -----------------------------------------------------------------------------
# GameFAQs online metadata scraper
# -----------------------------------------------------------------------------
class metadata_GameFAQs(Scraper_Metadata):
    def __init__(self):
        self.name = 'GameFAQs'
        self.fancy_name = 'GameFAQs Metadata scraper'
        
    def get_game_list(self, search_string):
        display=[]
        results=[]
        try:
            req = urllib2.Request('http://www.gamefaqs.com/search/index.html?platform=0&game='+search.replace(' ','+')+'')
            req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
            f = urllib2.urlopen(req)
            gets = {}
            gets = re.findall('<td class="rtitle">(.*?)<a href="(.*?)"(.*?)class="sevent_(.*?)">(.*?)</a></td>', f.read().replace('\r\n', ''))
            for get in gets:
                game = {}
                gamesystem = get[1].split('/')
                game["id"] = 'http://www.gamefaqs.com'+get[1]
                game["title"] = unescape(get[4])
                game["gamesys"] = gamesystem[1].capitalize()
                results.append(game)
                display.append(game["title"]+" / "+game["gamesys"])
            return results,display
        except:
            return results,display

    def get_game_data(self, game_url):
        print game_url
        gamedata = {}
        gamedata["genre"] = ""
        gamedata["release"] = ""
        gamedata["studio"] = ""
        gamedata["plot"] = ""
        try:
            req = urllib2.Request(game_url)
            req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
            f = urllib2.urlopen(req)
            page = f.read().replace('\r\n', '')
            game_genre = re.findall('<li class="crumb top-crumb"><a href="/(.*?)">(.*?)</a></li><li class="crumb"><a href="/(.*?)/list-(.*?)">(.*?)</a></li>', page)
            if game_genre:
                gamedata["genre"] = game_genre[0][4]
            game_release = re.findall('Release: <a href="(.*?)">(.*?) &raquo;</a>', page)
            if game_release:
                gamedata["release"] = game_release[0][1][-4:]
            game_studio = re.findall('<li><a href="/features/company/(.*?)">(.*?)</a>', page)
            if game_studio:
                p = re.compile(r'<.*?>')
                gamedata["studio"] = p.sub('', game_studio[0][1])
            game_plot = re.findall('Description</h2></div><div class="body game_desc"><div class="desc">(.*?)</div>', page)
            if game_plot:
                gamedata["plot"] = unescape(game_plot[0])
            return gamedata
        except:
            return gamedata

    def get_game_data_first(self, search_string, gamesys):
        platform = _system_conversion(gamesys)
        results = []
        try:
            req = urllib2.Request('http://www.gamefaqs.com/search/index.html?platform='+platform+'&game='+search.replace(' ','+')+'')
            req.add_unredirected_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')
            f = urllib2.urlopen(req)
            gets = {}
            gets = re.findall('<td class="rtitle">(.*?)<a href="(.*?)"(.*?)class="sevent_(.*?)">(.*?)</a></td>', f.read().replace('\r\n', ''))
            for get in gets:
                game = {}
                game["id"] = 'http://www.gamefaqs.com'+get[1]
                game["title"] = unescape(get[4])
                game["gamesys"] = gamesys
                results.append(game)
            return results
        except:
            return results

# -----------------------------------------------------------------------------
# arcadeHITS
# Site in French!
# -----------------------------------------------------------------------------
class metadata_arcadeHITS(Scraper_Metadata):
    def __init__(self):
        self.name = 'arcadeHITS'
        self.fancy_name = 'arcadeHITS Metadata scraper'

    def get_game_list(self, search_string):
        results = []
        display = []
        try:
            f = urllib.urlopen('http://www.arcadehits.net/index.php?p=roms&jeu='+search)
            page = f.read().replace('\r\n', '').replace('\n', '')
            game = {}
            romname = ''.join(re.findall('<h4>(.*?)</h4>', page))
            game["title"] = unescape(romname)
            game["id"] = search
            game["gamesys"] = 'Arcade'
            if game["title"]:
                results.append(game)
                display.append(romname+" / "+game["gamesys"])
            return results,display
        except:
            return results,display

    def get_game_data(self, game_url):
        gamedata = {}
        gamedata["genre"] = ""
        gamedata["release"] = ""
        gamedata["studio"] = ""
        gamedata["plot"] = ""
        f = urllib.urlopen('http://www.arcadehits.net/index.php?p=roms&jeu='+game_id)
        page = f.read().replace('\r\n', '').replace('\n', '').replace('\r', '').replace('          ', '')
        game_genre = re.findall('<span class=mini>Genre: </span></td><td align=left>&nbsp;&nbsp;<strong>(.*?)>(.*?)</a>', page)
        if game_genre:
            gamedata["genre"] = game_genre[0][1]
        game_release = re.findall('<span class=mini>Ann&eacute;e: </span></td><td align=left>&nbsp;&nbsp;<strong>(.*?)>(.*?)</a>', page)
        if game_release:
            gamedata["release"] = game_release[0][1]
        game_studio = re.findall('<span class=mini>Fabricant: </span></td><td align=left>&nbsp;&nbsp;<strong>(.*?)>(.*?)</a>', page)
        if game_studio:
            gamedata["studio"] = game_studio[0][1]
        f = urllib.urlopen('http://www.arcadehits.net/page/viewdatfiles.php?show=history&jeu='+game_id)
        page = f.read().replace('\r\n', '').replace('\n', '').replace('\r', '')
        game_plot = re.findall('<br><br>(.*?)<br><br>',page)
        if game_plot:
            gamedata["plot"] = unescape(game_plot[0])
        return gamedata
    
    def get_game_data_first(self, search_string, gamesys):
        results = []
        try:
            f = urllib.urlopen('http://www.arcadehits.net/index.php?p=roms&jeu='+search)
            page = f.read().replace('\r\n', '').replace('\n', '')
            game = {}
            romname = ''.join(re.findall('<h4>(.*?)</h4>', page))
            game["title"] = unescape(romname)
            game["id"] = search
            game["gamesys"] = 'Arcade'
            results.append(game)
            return results
        except:
            return results
