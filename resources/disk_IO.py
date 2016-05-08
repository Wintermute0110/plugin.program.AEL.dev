#
# Advanced Emulator Launcher filesystem I/O functions
#

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# --- XML stuff ---
# ~~~ cElementTree sometimes fails to parse XML in Kodi's Python interpreter... I don't know why
# import xml.etree.cElementTree as ET

# ~~~ Using ElementTree seems to solve the problem
import xml.etree.ElementTree as ET

#
# Write to disk categories.xml
#
def _fs_write_catfile(self):
    self._print_log('_fs_create_default_catfile() Saving categories.xml file')
    xbmc.executebuiltin('ActivateWindow(busydialog)')

    # Original Angelscry method for generating the XML was to grow a string, like this
    # xml_content = 'test'
    # xml_content += 'more test'
    # However, this method is very slow because string has to be reallocated every time is grown.
    # It is much faster to create a list of string and them join them!
    # See https://waymoot.org/home/python_string/
    try:
        str_list = []
        str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        str_list.append('<advanced_emulator_launcher version="1.0">\n')

        # Create Categories XML list
        for categoryID in sorted(self.categories, key = lambda x : self.categories[x]["name"]):
            category = self.categories[categoryID]
            # Data which is not string must be converted to string
            str_list.append("<category>\n" +
                            "  <id>"          + categoryID                 + "</id>\n" +
                            "  <name>"        + category["name"]           + "</name>\n" +
                            "  <thumb>"       + category["thumb"]          + "</thumb>\n"
                            "  <fanart>"      + category["fanart"]         + "</fanart>\n" +
                            "  <genre>"       + category["genre"]          + "</genre>\n" +
                            "  <description>" + category["description"]    + "</description>\n" +
                            "  <finished>"    + str(category["finished"])  + "</finished>\n" +
                            "</category>\n")
        # Write launchers
        for launcherID in sorted(self.launchers, key = lambda x : self.launchers[x]["name"]):
            launcher = self.launchers[launcherID]
            # Data which is not string must be converted to string
            str_list.append("<launcher>\n" +
                            "  <id>"            + launcherID                + "</id>\n" +
                            "  <name>"          + launcher["name"]          + "</name>\n" +
                            "  <category>"      + launcher["category"]      + "</category>\n" +
                            "  <application>"   + launcher["application"]   + "</application>\n"
                            "  <args>"          + launcher["args"]          + "</args>\n" +
                            "  <rompath>"       + launcher["rompath"]       + "</rompath>\n" +
                            "  <thumbpath>"     + launcher["thumbpath"]     + "</thumbpath>\n" +
                            "  <fanartpath>"    + launcher["fanartpath"]    + "</fanartpath>\n" +
                            "  <custompath>"    + launcher["custompath"]    + "</custompath>\n" +
                            "  <trailerpath>"   + launcher["trailerpath"]   + "</trailerpath>\n" +
                            "  <romext>"        + launcher["romext"]        + "</romext>\n" +
                            "  <gamesys>"       + launcher["gamesys"]       + "</gamesys>\n" +
                            "  <thumb>"         + launcher["thumb"]         + "</thumb>\n" +
                            "  <fanart>"        + launcher["fanart"]        + "</fanart>\n" +
                            "  <genre>"         + launcher["genre"]         + "</genre>\n" +
                            "  <release>"       + launcher["release"]       + "</release>\n" +
                            "  <studio>"        + launcher["studio"]        + "</studio>\n" +
                            "  <plot>"          + launcher["plot"]          + "</plot>\n" +
                            "  <lnk>"           + str(launcher["lnk"])      + "</lnk>\n" +
                            "  <finished>"      + str(launcher["finished"]) + "</finished>\n" +
                            "  <minimize>"      + str(launcher["minimize"]) + "</minimize>\n" +
                            "  <roms_xml_file>" + launcher["roms_xml_file"] + "</roms_xml_file>\n" +
                            "</launcher>\n")
        # End of file
        str_list.append('</advanced_emulator_launcher>\n')

        # Join string and escape XML characters
        full_string = ''.join(str_list)
        full_string = self._fs_escape_XML(full_string)

        # Save categories.xml file
        file_obj = open(CATEGORIES_FILE_PATH, 'wt' )
        file_obj.write(full_string)
        file_obj.close()
    except OSError:
        gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write categories.xml file. (OSError)')
    except IOError:
        gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write categories.xml file. (IOError)')

    # --- We are not busy anymore ---
    xbmc.executebuiltin('Dialog.Close(busydialog)')

#
# Loads categories.xml from disk and fills dictionary self.categories
#
def _fs_load_catfile(self):
    __debug_xml_parser = 0
    self.categories = {}
    self.launchers = {}
    xbmc.executebuiltin('ActivateWindow(busydialog)')

    # --- Parse using cElementTree ---
    xbmc.log('Parsing {0}'.format(CATEGORIES_FILE_PATH))

    # If file = '' is not used then instead of reading a file CATEGORIES_FILE_PATH is considered a string!!!
    xml_tree = ET.parse(CATEGORIES_FILE_PATH)
    xml_root = xml_tree.getroot()
    for category_element in xml_root:
        if __debug_xml_parser: xbmc.log('Root child {0}'.format(category_element.tag))

        if category_element.tag == 'category':
            # Default values
            category = {'id' : '', 'name' : '', 'thumb' : '', 'fanart' : '', 'genre' : '', 'description' : '', 'finished' : False}

            # Parse child tags of category
            for category_child in category_element:
                # By default read strings
                xml_text = category_child.text if category_child.text is not None else ''
                xml_tag  = category_child.tag
                if __debug_xml_parser: xbmc.log('{0} --> {1}'.format(xml_tag, xml_text))
                category[xml_tag] = xml_text

                # Now transform data depending on tag name
                if xml_tag == 'finished':
                    xml_bool = False if xml_text == 'False' else True
                    category[xml_tag] = xml_bool

            # Add category to categories dictionary
            self.categories[category['id']] = category

        elif category_element.tag == 'launcher':
            # Default values
            launcher = {
                "id" : '',
                "name" : '', "category" : '', "application" : '',  "args" : '',
                "rompath" : "", "thumbpath" : '', "fanartpath" : '',
                "custompath" : "", "trailerpath" : "", "romext" : "", "gamesys" : '',
                "thumb" : "", "fanart" : "", "genre" : "", "release" : "", "studio" : "",
                "plot" : "",  "lnk" : False, "finished": False, "minimize" : False,
                "roms_xml_file" : '' }

            # Parse child tags of category
            for category_child in category_element:
                # By default read strings
                xml_text = category_child.text if category_child.text is not None else ''
                xml_tag  = category_child.tag
                if __debug_xml_parser: xbmc.log('{0} --> {1}'.format(xml_tag, xml_text))
                launcher[xml_tag] = xml_text

                # Now transform data depending on tag name
                if xml_tag == 'lnk' or xml_tag == 'finished' or xml_tag == 'minimize':
                    xml_bool = True if xml_text == 'True' else False
                    launcher[xml_tag] = xml_bool

            # Add launcher to categories dictionary
            self.launchers[launcher['id']] = launcher
    xbmc.executebuiltin('Dialog.Close(busydialog)')

def _fs_escape_XML(self, str):
    return str.replace('&', '&amp;')

#
# Write to disk categories.xml
#
def _fs_write_ROM_XML_file(self, roms, launcherID, roms_xml_file):
    self._print_log('_fs_write_ROM_XML_file() Saving XML file {0}'.format(roms_xml_file))

    # --- Notify we are busy doing things ---
    xbmc.executebuiltin('ActivateWindow(busydialog)')
    
    # Original Angelscry method for generating the XML was to grow a string, like this
    # xml_content = 'test'
    # xml_content += 'more test'
    # However, this method is very slow because string has to be reallocated every time is grown.
    # It is much faster to create a list of string and them join them!
    # See https://waymoot.org/home/python_string/
    try:
        str_list = []
        str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        str_list.append('<advanced_emulator_launcher_ROMs version="1.0">\n')

        # Print some information in the XML so the user can now which launcher created it.
        # Note that this is ignored when reading the file.
        str_list.append('<launcher>\n')
        str_list.append('  <id        >{0}</id>\n'.format(launcherID))
        str_list.append('  <name      >{0}</name>\n'.format(self.launchers[launcherID]['name']))            
        str_list.append('  <category  >{0}</category>\n'.format(self.launchers[launcherID]['category']))
        str_list.append('  <rompath   >{0}</rompath>\n'.format(self.launchers[launcherID]['rompath']))
        str_list.append('  <thumbpath >{0}</thumbpath>\n'.format(self.launchers[launcherID]['thumbpath']))
        str_list.append('  <fanartpath>{0}</fanartpath>\n'.format(self.launchers[launcherID]['fanartpath']))
        str_list.append('</launcher>\n')

        # Create list of ROMs
        # TODO Size optimization: only write in the XML fields which are not ''. This
        #      will save A LOT of disk space and reduce loading times (at a cost of
        #      some writing time, but writing is much less frequent than reading).
        for romID in sorted(roms, key = lambda x : roms[x]["name"]):
            rom = roms[romID]
            # Data which is not string must be converted to string
            str_list.append("<rom>\n" +
                            "  <id>"       + romID                + "</id>\n" +
                            "  <name>"     + rom["name"]          + "</name>\n" +
                            "  <filename>" + rom["filename"]      + "</filename>\n" +
                            "  <gamesys>"  + rom["gamesys"]       + "</gamesys>\n" +
                            "  <thumb>"    + rom["thumb"]         + "</thumb>\n" +
                            "  <fanart>"   + rom["fanart"]        + "</fanart>\n" +
                            "  <trailer>"  + rom["trailer"]       + "</trailer>\n" +
                            "  <custom>"   + rom["custom"]        + "</custom>\n" +
                            "  <genre>"    + rom["genre"]         + "</genre>\n" +
                            "  <release>"  + rom["release"]       + "</release>\n" +
                            "  <studio>"   + rom["studio"]        + "</studio>\n" +
                            "  <plot>"     + rom["plot"]          + "</plot>\n" +
                            "  <altapp>"   + rom["altapp"]        + "</altapp>\n" +
                            "  <altarg>"   + rom["altarg"]        + "</altarg>\n" +
                            "  <finished>" + str(rom["finished"]) + "</finished>\n" +
                            "</rom>\n")
        # End of file
        str_list.append('</advanced_emulator_launcher_ROMs>\n')

        # Join string and escape XML characters
        full_string = ''.join(str_list)
        full_string = self._fs_escape_XML(full_string)

        # Save categories.xml file
        file_obj = open(roms_xml_file, 'wt' )
        file_obj.write(full_string)
        file_obj.close()
    except OSError:
        gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write {0} file. (OSError)'.format(roms_xml_file))
    except IOError:
        gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write {0} file. (IOError)'.format(roms_xml_file))

    # --- We are not busy anymore ---
    xbmc.executebuiltin('Dialog.Close(busydialog)')

#
# Loads a launcher XML with the ROMs
#
def _fs_load_ROM_XML_file(self, roms_xml_file):
    __debug_xml_parser = 0
    roms = {}

    # --- If file does not exist return empty dictionary ---
    if not os.path.isfile(roms_xml_file):
        return {}

    xbmc.executebuiltin('ActivateWindow(busydialog)')

    # --- Parse using cElementTree ---
    xbmc.log('_fs_load_ROM_XML_file() Loading XML file {0}'.format(roms_xml_file))
    xml_tree = ET.parse(roms_xml_file)
    xml_root = xml_tree.getroot()
    for root_element in xml_root:
        if __debug_xml_parser: xbmc.log('Root child {0}'.format(root_element.tag))

        if root_element.tag == 'rom':
            # Default values
            rom = {'id' : '', 'name' : '', "filename" : '', "gamesys" : '', "thumb" : '', "fanart" : '',
                    "trailer" : '', "custom" : '', "genre" : '', "release" : '', "studio" : '',
                    "plot" : '', "finished" : False, "altapp" : '', "altarg" : '' }
            for rom_child in root_element:
                # By default read strings
                xml_text = rom_child.text if rom_child.text is not None else ''
                xml_tag  = rom_child.tag
                if __debug_xml_parser: xbmc.log('{0} --> {1}'.format(xml_tag, xml_text))
                rom[xml_tag] = xml_text
                
                # Now transform data depending on tag name
                if xml_tag == 'finished':
                    xml_bool = True if xml_text == 'True' else False
                    rom[xml_tag] = xml_bool
            roms[rom['id']] = rom
    xbmc.executebuiltin('Dialog.Close(busydialog)')

    return roms

#
# Write to disk categories.xml
#
def _fs_write_Favourites_XML_file(self, roms, roms_xml_file):
    self._print_log('_fs_write_Favourites_XML_file() Saving XML file {0}'.format(roms_xml_file))
    xbmc.executebuiltin('ActivateWindow(busydialog)')
    try:
        str_list = []
        str_list.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        str_list.append('<advanced_emulator_launcher_Favourites version="1.0">\n')
        for romID in sorted(roms, key = lambda x : roms[x]["name"]):
            rom = roms[romID]
            str_list.append("<rom>\n" +
                            "  <id>"       + romID                + "</id>\n" +
                            "  <name>"     + rom["name"]          + "</name>\n" +
                            "  <filename>" + rom["filename"]      + "</filename>\n" +
                            "  <gamesys>"  + rom["gamesys"]       + "</gamesys>\n" +
                            "  <thumb>"    + rom["thumb"]         + "</thumb>\n" +
                            "  <fanart>"   + rom["fanart"]        + "</fanart>\n" +
                            "  <trailer>"  + rom["trailer"]       + "</trailer>\n" +
                            "  <custom>"   + rom["custom"]        + "</custom>\n" +
                            "  <genre>"    + rom["genre"]         + "</genre>\n" +
                            "  <release>"  + rom["release"]       + "</release>\n" +
                            "  <studio>"   + rom["studio"]        + "</studio>\n" +
                            "  <plot>"     + rom["plot"]          + "</plot>\n" +
                            "  <finished>" + str(rom["finished"]) + "</finished>\n" +
                            "  <altapp>"   + rom["altapp"]        + "</altapp>\n" +
                            "  <altarg>"   + rom["altarg"]        + "</altarg>\n" +
                            "  <application>" + rom["application"] + "</application>\n" +
                            "  <args>"        + rom["args"]        + "</args>\n" +
                            "  <launcherID>"  + rom["launcherID"]  + "</launcherID>\n" +
                            "</rom>\n")
        str_list.append('</advanced_emulator_launcher_Favourites>\n')
        full_string = ''.join(str_list)
        full_string = self._fs_escape_XML(full_string)
        file_obj = open(roms_xml_file, 'wt' )
        file_obj.write(full_string)
        file_obj.close()
    except OSError:
        gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write {0} file. (OSError)'.format(roms_xml_file))
    except IOError:
        gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write {0} file. (IOError)'.format(roms_xml_file))
    xbmc.executebuiltin('Dialog.Close(busydialog)')

#
# Loads an XML file containing the favourite ROMs
# It is basically the same as ROMs, but with some more fields to store launching application data.
#
def _fs_load_Favourites_XML_file(self, roms_xml_file):
    __debug_xml_parser = 0
    roms = {}

    # --- If file does not exist return empty dictionary ---
    if not os.path.isfile(roms_xml_file):
        return {}

    xbmc.executebuiltin('ActivateWindow(busydialog)')
    # --- Parse using cElementTree ---
    xbmc.log('_fs_load_Favourites_XML_file() Loading XML file {0}'.format(roms_xml_file))
    xml_tree = ET.parse(roms_xml_file)
    xml_root = xml_tree.getroot()
    for root_element in xml_root:
        if __debug_xml_parser: xbmc.log('Root child {0}'.format(root_element.tag))

        if root_element.tag == 'rom':
            # Default values
            rom = {'id' : '', 'name' : '', 'filename' : '', 'gamesys' : '', 'thumb' : '', 'fanart' : '',
                    'trailer' : '', 'custom' : '', 'genre' : '', 'release' : '', 'studio' : '',
                    'plot' : '', 'finished' : False, 'altapp' : '', 'altarg' : '', 
                    'application' : '',  'args' : '', 'launcherID' : '' }
            for rom_child in root_element:
                # By default read strings
                xml_text = rom_child.text if rom_child.text is not None else ''
                xml_tag  = rom_child.tag
                if __debug_xml_parser: xbmc.log('{0} --> {1}'.format(xml_tag, xml_text))
                rom[xml_tag] = xml_text
                
                # Now transform data depending on tag name
                if xml_tag == 'finished':
                    xml_bool = True if xml_text == 'True' else False
                    rom[xml_tag] = xml_bool
            roms[rom['id']] = rom
    xbmc.executebuiltin('Dialog.Close(busydialog)')

    return roms

#
# Reads an NFO file with ROM information and places items in a dictionary.
#
def _fs_load_NFO_file(nfo_file):
    self._print_log('_fs_load_NFO_file() Loading "{0}"'.format(nfo_file))
    
    # Read file, put in a string and remove line endings
    ff = open(nfo_file, 'rt')
    nfo_str = ff.read().replace('\r', '').replace('\n', '')
    ff.close()

    # Fill default values
    nfo_dic = {'title' : '', 'platform' : '', 'year' : '', 'publisher' : '', 'genre' : '', 'plot' : ''}

    # Search for items
    item_title     = re.findall( "<title>(.*?)</title>", nfo_str )
    item_platform  = re.findall( "<platform>(.*?)</platform>", nfo_str )
    item_year      = re.findall( "<year>(.*?)</year>", nfo_str )
    item_publisher = re.findall( "<publisher>(.*?)</publisher>", nfo_str )
    item_genre     = re.findall( "<genre>(.*?)</genre>", nfo_str )
    item_plot      = re.findall( "<plot>(.*?)</plot>", nfo_str )

    if len(item_title) > 0:     nfo_dic['title']     = item_title[0]
    if len(item_title) > 0:     nfo_dic['platform']  = item_platform[0]
    if len(item_year) > 0:      nfo_dic['year']      = item_year[0]
    if len(item_publisher) > 0: nfo_dic['publisher'] = item_publisher[0]
    if len(item_genre) > 0:     nfo_dic['genre']     = item_genre[0]
    # Should end of lines deeconded from the XML file???
    # See http://stackoverflow.com/questions/2265966/xml-carriage-return-encoding
    if len(item_plot) > 0:
        plot_str = item_plot[0]
        plot_str.replace('&quot;', '"')
        nfo_dic['plot'] = plot_str

    # DEBUG
    self._print_log(' title     : "{0}"'.format(nfo_dic['title']))
    self._print_log(' platform  : "{0}"'.format(nfo_dic['platform']))
    self._print_log(' year      : "{0}"'.format(nfo_dic['year']))
    self._print_log(' publisher : "{0}"'.format(nfo_dic['publisher']))
    self._print_log(' genre     : "{0}"'.format(nfo_dic['genre']))
    self._print_log(' plot      : "{0}"'.format(nfo_dic['plot']))

    return nfo_dic


def _import_rom_nfo(self, launcher, rom):
    # Edition of the rom name
    nfo_file=os.path.splitext(self.launchers[launcher]["roms"][rom]["filename"])[0]+".nfo"
    if (os.path.isfile(nfo_file)):
        f = open(nfo_file, 'r')
        item_nfo = f.read().replace('\r','').replace('\n','')
        f.close()
        item_title = re.findall( "<title>(.*?)</title>", item_nfo )
        item_platform = re.findall( "<platform>(.*?)</platform>", item_nfo )
        item_year = re.findall( "<year>(.*?)</year>", item_nfo )
        item_publisher = re.findall( "<publisher>(.*?)</publisher>", item_nfo )
        item_genre = re.findall( "<genre>(.*?)</genre>", item_nfo )
        item_plot = re.findall( "<plot>(.*?)</plot>", item_nfo )
        if len(item_title) > 0 : self.launchers[launcher]["roms"][rom]["name"] = item_title[0].rstrip()
        self.launchers[launcher]["roms"][rom]["gamesys"] = self.launchers[launcher]["gamesys"]
        if len(item_year) > 0 :  self.launchers[launcher]["roms"][rom]["release"] = item_year[0]
        if len(item_publisher) > 0 : self.launchers[launcher]["roms"][rom]["studio"] = item_publisher[0]
        if len(item_genre) > 0 : self.launchers[launcher]["roms"][rom]["genre"] = item_genre[0]
        if len(item_plot) > 0 : self.launchers[launcher]["roms"][rom]["plot"] = item_plot[0].replace('&quot;','"')
        self._save_launchers()
        xbmc_notify('Advanced Emulator Launcher', __language__( 30083 ) % os.path.basename(nfo_file),3000)
    else:
        xbmc_notify('Advanced Emulator Launcher', __language__( 30082 ) % os.path.basename(nfo_file),3000)

def _export_rom_nfo(self, launcher, rom):
    nfo_file=os.path.splitext(self.launchers[launcher]["roms"][rom]["filename"].decode(get_encoding()))[0]+".nfo"
    if (os.path.isfile(nfo_file)):
        shutil.move( nfo_file, nfo_file+".tmp" )
        destination= open( nfo_file, "w" )
        source= open( nfo_file+".tmp", "r" )
        first_genre=0
        for line in source:
            item_title = re.findall( "<title>(.*?)</title>", line )
            item_platform = re.findall( "<platform>(.*?)</platform>", line )
            item_year = re.findall( "<year>(.*?)</year>", line )
            item_publisher = re.findall( "<publisher>(.*?)</publisher>", line )
            item_genre = re.findall( "<genre>(.*?)</genre>", line )
            item_plot = re.findall( "<plot>(.*?)</plot>", line )
            if len(item_title) > 0 : line = "\t<title>"+self.launchers[launcher]["roms"][rom]["name"]+"</title>\n"
            if len(item_platform) > 0 : line = "\t<platform>"+self.launchers[launcher]["roms"][rom]["gamesys"]+"</platform>\n"
            if len(item_year) > 0 : line = "\t<year>"+self.launchers[launcher]["roms"][rom]["release"]+"</year>\n"
            if len(item_publisher) > 0 : line = "\t<publisher>"+self.launchers[launcher]["roms"][rom]["studio"]+"</publisher>\n"
            if len(item_genre) > 0 :
                if first_genre == 0 :
                    line = "\t<genre>"+self.launchers[launcher]["roms"][rom]["genre"]+"</genre>\n"
                    first_genre = 1
            if len(item_plot) > 0 : line = "\t<plot>"+self.launchers[launcher]["roms"][rom]["plot"]+"</plot>\n"
            destination.write( line )
        source.close()
        destination.close()
        os.remove(nfo_file+".tmp")
        xbmc_notify('Advanced Emulator Launcher', __language__( 30087 ) % os.path.basename(nfo_file).encode('utf8','ignore'),3000)
    else:
        nfo_content = "<game>\n\t<title>"+self.launchers[launcher]["roms"][rom]["name"]+"</title>\n\t<platform>"+self.launchers[launcher]["roms"][rom]["gamesys"]+"</platform>\n\t<year>"+self.launchers[launcher]["roms"][rom]["release"]+"</year>\n\t<publisher>"+self.launchers[launcher]["roms"][rom]["studio"]+"</publisher>\n\t<genre>"+self.launchers[launcher]["roms"][rom]["genre"]+"</genre>\n\t<plot>"+self.launchers[launcher]["roms"][rom]["plot"]+"</plot>\n</game>\n"
        usock = open( nfo_file, 'w' )
        usock.write(nfo_content)
        usock.close()
        xbmc_notify('Advanced Emulator Launcher', __language__( 30086 ) % os.path.basename(nfo_file).encode('utf8','ignore'),3000)

def _export_launcher_nfo(self, launcherID):
    if ( len(self.launchers[launcherID]["rompath"]) > 0 ):
        nfo_file = os.path.join(self.launchers[launcherID]["rompath"],os.path.basename(os.path.splitext(self.launchers[launcherID]["application"])[0]+".nfo"))
    else:
        if ( len(self.settings[ "launcher_nfo_path" ]) > 0 ):
            nfo_file = os.path.join(self.settings[ "launcher_nfo_path" ],os.path.basename(os.path.splitext(self.launchers[launcherID]["application"])[0]+".nfo"))
        else:
            nfo_path = xbmcgui.Dialog().browse(0,__language__( 30089 ),"files",".nfo", False, False)
            nfo_file = os.path.join(nfo_path,os.path.basename(os.path.splitext(self.launchers[launcherID]["application"])[0]+".nfo"))
    if (os.path.isfile(nfo_file)):
        shutil.move( nfo_file, nfo_file+".tmp" )
        destination= open( nfo_file, "w" )
        source= open( nfo_file+".tmp", "r" )
        for line in source:
            item_title = re.findall( "<title>(.*?)</title>", line )
            item_platform = re.findall( "<platform>(.*?)</platform>", line )
            item_year = re.findall( "<year>(.*?)</year>", line )
            item_publisher = re.findall( "<publisher>(.*?)</publisher>", line )
            item_genre = re.findall( "<genre>(.*?)</genre>", line )
            item_plot = re.findall( "<plot>(.*?)</plot>", line )
            if len(item_title) > 0 : line = "\t<title>"+self.launchers[launcherID]["name"]+"</title>\n"
            if len(item_platform) > 0 : line = "\t<platform>"+self.launchers[launcherID]["gamesys"]+"</platform>\n"
            if len(item_year) > 0 : line = "\t<year>"+self.launchers[launcherID]["release"]+"</year>\n"
            if len(item_publisher) > 0 : line = "\t<publisher>"+self.launchers[launcherID]["studio"]+"</publisher>\n"
            if len(item_genre) > 0 : line = "\t<genre>"+self.launchers[launcherID]["genre"]+"</genre>\n"
            if len(item_plot) > 0 : line = "\t<plot>"+self.launchers[launcherID]["plot"]+"</plot>\n"
            destination.write( line )
        source.close()
        destination.close()
        os.remove(nfo_file+".tmp")
        xbmc_notify('Advanced Emulator Launcher', __language__( 30087 ) % os.path.basename(nfo_file),3000)
    else:
        nfo_content = "<launcher>\n\t<title>"+self.launchers[launcherID]["name"]+"</title>\n\t<platform>"+self.launchers[launcherID]["gamesys"]+"</platform>\n\t<year>"+self.launchers[launcherID]["release"]+"</year>\n\t<publisher>"+self.launchers[launcherID]["studio"]+"</publisher>\n\t<genre>"+self.launchers[launcherID]["genre"]+"</genre>\n\t<plot>"+self.launchers[launcherID]["plot"]+"</plot>\n</launcher>\n"
        usock = open( nfo_file, 'w' )
        usock.write(nfo_content)
        usock.close()
        xbmc_notify('Advanced Emulator Launcher', __language__( 30086 ) % os.path.basename(nfo_file),3000)
