# -*- coding: UTF-8 -*-

import re
import os
import urllib
import simplejson

comicvine_api_key = "a1aaa516eaf233abf29c8aefaa46dc39cc0f0873"
comicvine_api_url = "http://beta.comicvine.com/api"

def _get_games_list(search):
    results = []
    display = []
    try:
        for num in range(1,3):
            f = urllib.urlopen('http://www.comicvine.com/jsonsearch/?indices[0]=issue&page='+str(num)+'&q="'+urllib.quote(search.lower())+'"')
            json = simplejson.loads(f.read())
            for issue in json['results']:
                comic = {}
                comic["id"] = issue["id"]
                comic["title"] = issue["title"].encode('utf-8','ignore')
                comic["studio"] = issue["company"].encode('utf-8','ignore')
                try:
                    comic["release"] = " / "+issue["cover_date"][0:4].encode('utf-8','ignore')
                except:
                    comic["release"] = ""
                comic["order"] = 1
                comic_volume = comic["title"].split(' - ')
                if ( comic_volume[0].lower() == search.lower() ):
                    comic["order"] += 1
                if ( comic["title"].lower() == search.lower() ):
                    comic["order"] += 1
                if ( comic["title"].lower().find(search.lower()) != -1 ):
                    comic["order"] += 1
                results.append(comic)
        results.sort(key=lambda result: result["order"], reverse=True)
        for result in results:
            display.append(result["title"]+' ('+result["studio"]+result["release"]+')')
        return results,display
    except:
        return results,display
        
# Return 1st Comic search
def _get_first_game(search,gamesys):
    results,display = _get_games_list(search)
    return results

# Return Comic data
def _get_game_data(comic_id):
    comicdata = {}
    comicdata["genre"] = "Comic"
    comicdata["release"] = ""
    comicdata["studio"] = ""
    comicdata["plot"] = ""
    try:
        f = urllib.urlopen(comicvine_api_url+'/issue/4000-'+str(comic_id)+'/?api_key='+comicvine_api_key+'&format=json&field_list=cover_date,description,volume,name,issue_number')
        json = simplejson.loads(f.read())
        f.close()
        if ( json['results']['cover_date'] ):
            comicdata["release"] = str(json['results']['cover_date'])[0:4]
        if ( json['results']['description'] ):
            p = re.compile(r'<.*?>')
            comicdata["plot"] = p.sub('', unescape(json['results']['description'].encode('utf-8','ignore')))
        if ( json['results']['volume'] ):
            f = urllib.urlopen(str(json['results']['volume']['api_detail_url'])+'?api_key='+comicvine_api_key+'&format=json&field_list=publisher')
            json2 = simplejson.loads(f.read())
            f.close()
            if (json2['results']['publisher']['name']):
                comicdata["studio"] = str(json2['results']['publisher']['name']).encode('utf-8','ignore')
        return comicdata
    except:
        return comicdata

def unescape(s):
    s = s.replace('</p>',' ')
    s = s.replace('<br />',' ')
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&amp;", "&")
    s = s.replace("&#039;","'")
    s = s.replace('<br />',' ')
    s = s.replace('&quot;','"')
    s = s.replace('&nbsp;',' ')
    s = s.replace('&#x26;','&')
    s = s.replace('&#x27;',"'")
    s = s.replace('&#xB0;',"°")
    return s
