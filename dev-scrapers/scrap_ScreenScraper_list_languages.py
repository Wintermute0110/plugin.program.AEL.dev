#!/usr/bin/python -B
# -*- coding: utf-8 -*-

#
# Get all ScreenScraper regions and outputs JSON, CSV files, Python code and Kodi XML setting.
#

# --- Python standard library ---
from __future__ import unicode_literals
from collections import OrderedDict
import os
import pprint
import sys

# --- AEL modules ---
if __name__ == "__main__" and __package__ is None:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print('Adding to sys.path {0}'.format(path))
    sys.path.append(path)
from resources.scrap import *
from resources.utils import *
import common

# --- configuration ------------------------------------------------------------------------------
txt_fname = 'data/ScreenScraper_languages.txt'
csv_fname = 'data/ScreenScraper_languages.csv'
py_fname  = 'data/ScreenScraper_languages.py'
xml_fname = 'data/ScreenScraper_languages.xml'

# --- Settings -----------------------------------------------------------------------------------
use_cached_ScreenScraper_get_language_list = True


# --- main ---------------------------------------------------------------------------------------
if use_cached_ScreenScraper_get_language_list:
    filename = 'assets/ScreenScraper_get_language_list.json'
    print('Loading file "{}"'.format(filename))
    f = open(filename, 'r')
    json_str = f.read()
    f.close()
    json_data = json.loads(json_str)
else:
    set_log_level(LOG_DEBUG)
    # --- Create scraper object ---
    scraper_obj = ScreenScraper(common.settings)
    scraper_obj.set_verbose_mode(False)
    scraper_obj.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))
    status_dic = kodi_new_status_dic('Scraper test was OK')
    # --- Get platforms ---
    # Call to this function will write file 'assets/ScreenScraper_get_platforms.json'
    json_data = scraper_obj.debug_get_languages(status_dic)
    if not status_dic['status']:
        print('SCRAPER ERROR: "' + status_dic['msg'] + '"')
        sys.exit(0)
# pprint.pprint(json_data)
# regions_dic is a dictionary of dictionaries
languages_dic = json_data['response']['langues']
# pprint.pprint(languages_dic)

# --- Fix some missing English names in ScreenScraper ---
for l_id in sorted(languages_dic):
    l_dic = languages_dic[l_id]
    if l_dic['nomcourt'] == 'da': l_dic['nom_en'] = 'Danish'
    if l_dic['nomcourt'] == 'hu': l_dic['nom_en'] = 'Hungarian'
    if l_dic['nomcourt'] == 'sk': l_dic['nom_en'] = 'Slovak'

# Transform dictionary into a sorted list.
# First make a new dictionary where the key is the unique shortname.
# Then, create a list and put well known regions first. Then, add missing regions to the list.
sn_languages_dic = {}
for l_id in sorted(languages_dic):
    l_dic = languages_dic[l_id]
    sn_languages_dic[l_dic['nomcourt']] = l_dic

sn_languages_od = OrderedDict()
sn_languages_od['en'] = sn_languages_dic['en'] # English
sn_languages_od['es'] = sn_languages_dic['es'] # Spanish
sn_languages_od['ja'] = sn_languages_dic['ja'] # Japanese
for r_shortname in sorted(sn_languages_dic):
    if r_shortname not in sn_languages_od:
        sn_languages_od[r_shortname] = sn_languages_dic[r_shortname]

# --- Print list ---
sl = []
sl.append('Number of ScreenScraper languages {}'.format(len(languages_dic)))
sl.append('')
table_str = [
    ['left', 'left', 'left', 'left'],
    ['ID', 'Shortname', 'Parent', 'English'],
]
for shortname in sn_languages_od:
    region = sn_languages_od[shortname]
    # print(region['id'])
    try:
        table_str.append([
            unicode(region['id']), region['nomcourt'], region['parent'], region['nom_en'],
        ])
    except UnicodeEncodeError as ex:
        print('Exception UnicodeEncodeError')
        print('ID {0}'.format(platform['id']))
        sys.exit(0)
table_str_list = text_render_table_str(table_str)
sl.extend(table_str_list)
text_str = '\n'.join(sl)
print('\n'.join(table_str_list))

# --- Output file in TXT format ---
print('\nWriting file "{}"'.format(txt_fname))
text_file = open(txt_fname, 'w')
text_file.write(text_str.encode('utf8'))
text_file.close()

# --- Output file in CSV format ---
text_csv_slist = text_render_table_CSV_slist(table_str)
text_csv = '\n'.join(text_csv_slist)
print('Writing file "{}"'.format(csv_fname))
text_file = open(csv_fname, 'w')
text_file.write(text_csv.encode('utf8'))
text_file.close()

# --- Generate Python code with language information ---
pl = []
pl.append('    language_list = [')
for shortname in sn_languages_od:
    region = sn_languages_od[shortname]
    len_shortname = len(shortname)
    padding = 3 - len_shortname
    pl.append("        '{0}', {1}# {2}".format(shortname, ' ' * padding, region['nom_en']))
pl.append('    ]')
py_str = '\n'.join(pl)

print('Writing file "{}"'.format(py_fname))
text_file = open(py_fname, 'w')
text_file.write(py_str.encode('utf8'))
text_file.close()

# --- Generate XML for Kodi settings ---
# <setting label="Region" type="enum" id="scraper_region" default="0" values="World|Europe|Japan|America"/>
shorname_list = []
for shortname in sn_languages_od:
    region = sn_languages_od[shortname]
    shorname_list.append(region['nom_en'])
region_str = '|'.join(shorname_list)
xml_str = '<setting label="ScreenScraper language" type="enum" id="scraper_screenscraper_language" default="0" values="{}" />'
xml_str = xml_str.format(region_str)

print('Writing file "{}"'.format(xml_fname))
text_file = open(xml_fname, 'w')
text_file.write(xml_str.encode('utf8'))
text_file.close()
