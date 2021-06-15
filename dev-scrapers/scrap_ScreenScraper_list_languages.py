#!/usr/bin/python3 -B
# -*- coding: utf-8 -*-

# Get all ScreenScraper regions and outputs JSON, CSV files, Python code and Kodi XML setting.

# --- Import AEL modules ---
import os
import sys
if __name__ == "__main__" and __package__ is None:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print('Adding to sys.path {}'.format(path))
    sys.path.append(path)
from resources.utils import *
from resources.scrap import *
import common

# --- Python standard library ---
import collections
import pprint

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
    with io.open(filename, 'rt', encoding = 'utf-8') as file:
        json_str = file.read()
    json_data = json.loads(json_str)
else:
    set_log_level(LOG_DEBUG)
    # --- Create scraper object ---
    scraper_obj = ScreenScraper(common.settings)
    scraper_obj.set_verbose_mode(False)
    scraper_obj.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))
    st_dic = kodi_new_status_dic()
    # --- Get platforms ---
    # Call to this function will write file 'assets/ScreenScraper_get_language_list.json'
    json_data = scraper_obj.debug_get_languages(st_dic)
    common.abort_on_error(st_dic)
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

sn_languages_od = collections.OrderedDict()
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
            str(region['id']), region['nomcourt'], region['parent'], region['nom_en'],
        ])
    except UnicodeEncodeError as ex:
        print('Exception UnicodeEncodeError')
        print('ID {}'.format(platform['id']))
        sys.exit(0)
table_str_list = text_render_table(table_str)
sl.extend(table_str_list)
text_str = '\n'.join(sl)
print('\n'.join(table_str_list))

# --- Output file in TXT format ---
print('\nWriting file "{}"'.format(txt_fname))
with io.open(txt_fname, 'wt', encoding = 'utf-8') as file:
    file.write(text_str)

# --- Output file in CSV format ---
text_csv_slist = text_render_table_CSV(table_str)
text_csv = '\n'.join(text_csv_slist)
print('Writing file "{}"'.format(csv_fname))
with io.open(csv_fname, 'wt', encoding = 'utf-8') as file:
    file.write(text_csv)

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
with io.open(py_fname, 'wt', encoding = 'utf-8') as file:
    file.write(py_str)

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
with io.open(xml_fname, 'wt', encoding = 'utf-8') as file:
    file.write(xml_str)
