#!/usr/bin/python
#
# Convert MAME output XML into a simplified XML suitable for offline scrapping.
# (c) Wintermute0110 <wintermute0110@gmail.com> 2016
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# To create the MAME XML file type
#   $ mame -listxml > mame-xxxx.xml
# where xxxx is the mame version, 0.173 will be 0173. Then, run this
# utility,
#   $ ./util_simpleXML_from_MAME_XML mame-xxxx.xml
# The output file will be named MAME.xml

# TODO Use catver.ini and possibly other MAME DAT files to get a much better
#      output.

# Python standard library
import xml.etree.ElementTree as ET 
import re
import sys

# -----------------------------------------------------------------------------
# Incremental Parsing approach B (from [1])
# -----------------------------------------------------------------------------
# Do not load whole MAME XML into memory! Use an iterative parser to
# grab only the information we want and discard the rest.
# See http://effbot.org/zone/element-iterparse.htm [1]
__debug_MAME_XML_parser = 0
context = ET.iterparse('mame_0173.xml', events=("start", "end"))
context = iter(context)
event, root = context.next()

# --- Data variables ---
# Create a dictionary of the form,
#   machines = { 'machine_name': machine, ...}
#
# where,
#   machine = {
#     'name' : '', 'description' : '', 'year' : '', 'manufacturer' : ''
#   }
machines = {}
machine_name = ''
num_iteration = 0
num_machines = 0
print('Reading MAME XML file ...')
for event, elem in context:
    # --- Debug the elements we are iterating from the XML file ---
    # print('Event     {0:6s} | Elem.tag    "{1}"'.format(event, elem.tag))
    # print('                   Elem.text   "{0}"'.format(elem.text))
    # print('                   Elem.attrib "{0}"'.format(elem.attrib))

    if event == "start" and elem.tag == "machine":
        machine = {'name' : '', 'description' : '', 'year' : '', 'manufacturer' : '' }
        machine_name = elem.attrib['name']
        machine['name'] = str(machine_name)
        num_machines += 1
        if __debug_MAME_XML_parser:
            print('New machine      {0}'.format(machine_name))

    elif event == "start" and elem.tag == "description":
        desc_str = elem.text
        if type(desc_str) == unicode: desc_str = str.encode('ascii', errors = 'replace')
        machine['description'] = str(desc_str)
        if __debug_MAME_XML_parser:
            print('     description {0}'.format(desc_str))

    elif event == "start" and elem.tag == "year":
        machine['year'] = str(elem.text)
        if __debug_MAME_XML_parser:
            print('            year {0}'.format(machine['year']))

    elif event == "start" and elem.tag == "manufacturer":
        machine['manufacturer'] = str(elem.text)
        if __debug_MAME_XML_parser:
            print('    manufacturer {0}'.format(machine['manufacturer']))
        
    elif event == "end" and elem.tag == "machine":
        if __debug_MAME_XML_parser:    
            print('Deleting machine {0}'.format(machine_name))
        elem.clear()
        machines[machine_name] = machine

    num_iteration += 1
    # --- Stop after some iteration for debug ---
    # if num_iteration > 10000:
    #    break

    # --- Print something to prove we are doing stuff ---
    if num_iteration % 25000 == 0:
      print('Processed {0:10d} events ({1:6d} machines so far) ...'.format(num_iteration, num_machines))
print('Processed {0} MAME XML events'.format(num_iteration))
print('Total number of machines {0}'.format(num_machines))

# -----------------------------------------------------------------------------
# Now write simplified XML output file
# -----------------------------------------------------------------------------
# See http://stackoverflow.com/questions/1091945/what-characters-do-i-need-to-escape-in-xml-documents
def string_to_XML(str):
    str_A = str.replace('"', '&quot;').replace("'", '&apos;').replace('&', '&amp;')

    return str_A.replace('<', '&lt;').replace('>', '&gt;')

# log_info('_fs_write_Favourites_XML_file() Saving XML file {0}'.format(roms_xml_file))
try:
    str_list = []
    str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
    str_list.append('<menu>\n')
    for key in sorted(machines):
        name = string_to_XML(machines[key]['name'])
        description = string_to_XML(machines[key]['description'])
        year = string_to_XML(machines[key]['year'])
        manufacturer = string_to_XML(machines[key]['manufacturer'])
        str_list.append('<game name="{0}">\n'.format(name) +
                        '  <description>'  + description   + '</description>\n' +
                        '  <year>'         + year          + '</year>\n' +
                        '  <manufacturer>' + manufacturer  + '</manufacturer>\n' +
                        '</game>\n')
    str_list.append('</menu>\n')

    file_obj = open('MAME.xml', 'wt' )
    file_obj.write(''.join(str_list)) 
    file_obj.close()
except OSError:
    # gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write {0} file. (OSError)'.format(roms_xml_file))
    pass
except IOError:
    # gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write {0} file. (IOError)'.format(roms_xml_file))
    pass
