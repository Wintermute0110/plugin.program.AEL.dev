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
import resources.const as const
import resources.log as log
import resources.misc as misc
import resources.utils as utils
import resources.kodi as kodi
import resources.scrap as scrap
import common

# --- Python standard library ---
import collections
import io
import pprint

# --- configuration ------------------------------------------------------------------------------
txt_fname = 'data/ScreenScraper_regions.txt'
csv_fname = 'data/ScreenScraper_regions.csv'
py_fname  = 'data/ScreenScraper_regions.py'
xml_fname = 'data/ScreenScraper_regions.xml'

# --- Settings -----------------------------------------------------------------------------------
use_cached_ScreenScraper_get_regions_list = False

# --- main ---------------------------------------------------------------------------------------
if use_cached_ScreenScraper_get_regions_list:
    filename = 'assets/ScreenScraper_get_regions_list.json'
    print('Loading file "{}"'.format(filename))
    with io.open(filename, 'rt', encoding = 'utf-8') as file:
        json_str = file.read()
    json_data = json.loads(json_str)
else:
    log.set_log_level(log.LOG_DEBUG)
    # --- Create scraper object
    scraper = scrap.ScreenScraper(common.settings)
    scraper.set_verbose_mode(False)
    scraper.set_debug_file_dump(True, os.path.join(os.path.dirname(__file__), 'assets'))
    st = kodi.new_status_dic()
    # --- Get platforms
    # Call to this function will write file 'assets/ScreenScraper_get_platforms.json'
    json_data = scraper.debug_get_regions(st)
    common.abort_on_error(st)
# pprint.pprint(json_data)
# regions_dic is a dictionary of dictionaries
regions_dic = json_data['response']['regions']
# pprint.pprint(regions_dic)

# --- Fix some missing English names in ScreenScraper ---
for r_id in sorted(regions_dic):
    r_dic = regions_dic[r_id]
    if r_dic['nomcourt'] == 'kw': r_dic['nom_en'] = 'Kuwait'
    if r_dic['nomcourt'] == 'no': r_dic['nom_en'] = 'Norway'
    if r_dic['nomcourt'] == 'bg': r_dic['nom_en'] = 'Bulgaria'
    if r_dic['nomcourt'] == 'gr': r_dic['nom_en'] = 'Greece'

# Transform dictionary into a sorted list.
# First make a new dictionary where the key is the unique shortname.
# Then, create a list and put well known regions first. Then, add missing regions to the list.
sn_regions_dic = {}
for r_id in sorted(regions_dic):
    r_dic = regions_dic[r_id]
    sn_regions_dic[r_dic['nomcourt']] = r_dic

sn_regions_od = collections.OrderedDict()
sn_regions_od['wor'] = sn_regions_dic['wor'] # World
sn_regions_od['eu']  = sn_regions_dic['eu']  # Europe
sn_regions_od['us']  = sn_regions_dic['us']  # USA
sn_regions_od['jp']  = sn_regions_dic['jp']  # Japan
sn_regions_od['ss']  = sn_regions_dic['ss']  # ScreenScraper
for r_shortname in sorted(sn_regions_dic):
    if r_shortname not in sn_regions_od:
        sn_regions_od[r_shortname] = sn_regions_dic[r_shortname]

# --- Print list ---
sl = []
sl.append('Number of ScreenScraper regions {}'.format(len(regions_dic)))
sl.append('')
table_str = [
    ['left', 'left', 'left', 'left'],
    ['ID', 'Shortname', 'Parent', 'English'],
]
for shortname in sn_regions_od:
    region = sn_regions_od[shortname]
    try:
        table_str.append([
            str(region['id']), region['nomcourt'], region['parent'], region['nom_en'],
        ])
    except UnicodeEncodeError as ex:
        print('Exception UnicodeEncodeError')
        print('ID {}'.format(platform['id']))
        sys.exit(0)
table_str_list = misc.render_table(table_str)
sl.extend(table_str_list)
text_str = '\n'.join(sl)
print('\n'.join(table_str_list))

# --- Output file in TXT format ---
print('Writing file "{}"'.format(txt_fname))
with io.open(txt_fname, 'wt', encoding = 'utf-8') as file:
    file.write(text_str)

# --- Output file in CSV format ---
text_csv_slist = misc.render_table_CSV(table_str)
text_csv = '\n'.join(text_csv_slist)
print('Writing file "{}"'.format(csv_fname))
with io.open(csv_fname, 'wt', encoding = 'utf-8') as file:
    file.write(text_csv)

# --- Generate Python code with region information ---
#    region_list = [
#        '_wor', # World
#        ...
#    ]
pl = []
pl.append('    region_list = [')
for shortname in sn_regions_od:
    region = sn_regions_od[shortname]
    len_shortname = len(shortname)
    padding = 3 - len_shortname
    pl.append("        '{}', {}# {}".format(shortname, ' ' * padding, region['nom_en']))
pl.append('    ]')
py_str = '\n'.join(pl)

print('Writing file "{}"'.format(py_fname))
with io.open(py_fname, 'wt', encoding = 'utf-8') as file:
    file.write(py_str)

# --- Generate XML for Kodi settings ---
# <setting label="Region" type="enum" id="scraper_region" default="0" values="World|Europe|Japan|America"/>
shorname_list = []
for shortname in sn_regions_od:
    region = sn_regions_od[shortname]
    shorname_list.append(region['nom_en'])
region_str = '|'.join(shorname_list)
xml_str = '<setting label="ScreenScraper region" type="enum" id="scraper_screenscraper_region" default="0" values="{}" />\n'
xml_str = xml_str.format(region_str)

print('Writing file "{}"'.format(xml_fname))
with io.open(xml_fname, 'wt', encoding = 'utf-8') as file:
    file.write(xml_str)
