#
# Old or obsolete code.
#

# -------------------------------------------------------------------------------------------------
# Kodi favorites launcher
# Do not use, AEL must not access favoruites.xml directly. Otherwise, addon will not be
# accepted in the Kodi official repository.
# -------------------------------------------------------------------------------------------------
class KodiLauncher(LauncherABC):
    def launch(self):
        self.title       = self.entity_data['m_name']
        self.application = FileName('xbmc.exe')
        self.arguments   = self.entity_data['application']
        super(KodiLauncher, self).launch()

    def supports_launching_roms(self): return False

    def get_launcher_type(self): return LAUNCHER_KODI_FAVOURITES

    def get_launcher_type_name(self): return "Kodi favourites launcher"

    def change_application(self):
        current_application = self.entity_data['application']
        dialog = KodiDictionaryDialog()
        selected_application = dialog.select('Select the favourite', self._get_kodi_favourites(), current_application)
        if selected_application is None or selected_application == current_application:
            return False
        self.entity_data['application'] = selected_application
        self.entity_data['original_favname'] = self._get_title_from_selected_favourite(selected_application, 'original_favname', self.entity_data)

        return True

    def get_edit_options(self):
        options = collections.OrderedDict()
        options['EDIT_METADATA']      = 'Edit Metadata ...'
        options['EDIT_ASSETS']        = 'Edit Assets/Artwork ...'
        options['SET_DEFAULT_ASSETS'] = 'Choose default Assets/Artwork ...'
        options['CHANGE_CATEGORY']    = 'Change Category'
        options['LAUNCHER_STATUS']    = 'Launcher status: {0}'.format(self.get_state())
        options['ADVANCED_MODS']      = 'Advanced Modifications ...'
        options['EXPORT_LAUNCHER']    = 'Export Launcher XML configuration ...'
        options['DELETE_LAUNCHER']    = 'Delete Launcher'

        return options

    def get_advanced_modification_options(self):
        log_debug('KodiLauncher::get_advanced_modification_options() Returning edit options')
        toggle_window_str = 'ON' if self.entity_data['toggle_window'] else 'OFF'
        non_blocking_str  = 'ON' if self.entity_data['non_blocking'] else 'OFF'
        org_favname = self.entity_data['original_favname'] if 'original_favname' in self.entity_data else 'unknown'
        options = super(KodiLauncher, self).get_advanced_modification_options()
        options['CHANGE_APPLICATION']   = "Change favourite: '{0}'".format(org_favname)
        options['TOGGLE_WINDOWED']      = "Toggle Kodi into windowed mode (now {0})".format(toggle_window_str)
        options['TOGGLE_NONBLOCKING']   = "Non-blocking launcher (now {0})".format(non_blocking_str)

        return options

    def _get_builder_wizard(self, wizard):
        wizard = DictionarySelectionWizardDialog('application', 'Select the favourite', self._get_kodi_favourites(), wizard)
        wizard = DummyWizardDialog('s_icon', '', wizard, self._get_icon_from_selected_favourite)
        wizard = DummyWizardDialog('original_favname', '', wizard, self._get_title_from_selected_favourite)
        wizard = DummyWizardDialog('m_name', '', wizard, self._get_title_from_selected_favourite)
        wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard)
        wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)

        return wizard

    def _get_kodi_favourites(self):
        favourites = kodi_read_favourites()
        fav_options = {}
        for key in favourites:
            fav_options[key] = favourites[key][0]

        return fav_options

    def _get_icon_from_selected_favourite(self, input, item_key, launcher):
        fav_action = launcher['application']
        favourites = kodi_read_favourites()
        for key in favourites:
            if fav_action == key:
                return favourites[key][1]

        return 'DefaultProgram.png'

    def _get_title_from_selected_favourite(self, input, item_key, launcher):
        fav_action = launcher['application']
        favourites = kodi_read_favourites()
        for key in favourites:
            if fav_action == key:
                return favourites[key][0]

        return _get_title_from_app_path(input, launcher)



# -------------------------------------------------------------------------------------------------
# XmlDataContext should be a singleton and only used by the repository classes.
# This class holds the actual XML data and reads/writes that data.
# OBSOLETE CODE THAT WILL BE REMOVE.
# -------------------------------------------------------------------------------------------------
class XmlDataContext(object):
    def __init__(self, xml_file_path):
        log_debug('XmlDataContext::init() "{0}"'.format(xml_file_path.getPath()))
        self._xml_root = None
        self.repo_fname = xml_file_path

    def xml_exists(self):
        return self.repo_fname.exists()

    #
    # If the XML file does not exists (for example, when the addon is first execute) then
    # allow to setup initial data.
    #
    def set_xml_root(self, xml_repo_str):
        self._xml_root = fs_get_XML_root_from_str(xml_repo_str)

    # Lazy loading of xml data through property
    @property
    def xml_data(self):
        if self._xml_root is None: self._load_xml()

        return self._xml_root

    #
    # If there is any problem with the filesystem then the functions display an error
    # dialog and produce an Addon_Error exception.
    #
    def _load_xml(self):
        log_debug('XmlDataContext::_load_xml() Loading "{0}"'.format(self.repo_fname.getPath()))
        xml_repo_str = self.repo_fname.loadFileToStr()
        self._xml_root = fs_get_XML_root_from_str(xml_repo_str)

    def commit(self):
        log_info('XmlDataContext::commit() Saving "{0}"'.format(self.repo_fname.getPath()))
        xml_repo_str = fs_get_str_from_XML_root(self._xml_root)
        self.repo_fname.saveStrToFile(xml_repo_str)

    def get_nodes(self, tag):
        log_debug('XmlDataContext::get_nodes(): xpath query "{}"'.format(tag))

        return self.xml_data.findall(tag)

    def get_node(self, tag, id):
        query = "{}[id='{}']".format(tag, id)
        log_debug('XmlDataContext::get_node(): xpath query "{}"'.format(query))

        return self.xml_data.find(query)

    def get_nodes_by(self, tag, field, value):
        query = "{}[{}='{}']".format(tag, field, value)
        log_debug('XmlDataContext::get_nodes_by(): xpath query "{}"'.format(query))

        return self.xml_data.findall(query)

    # creates/updates xml node identified by tag and id with the given dictionary of data
    def save_node(self, tag, id, updated_data):
        node_to_update = self.get_node(tag, id)

        if node_to_update is None:
            node_to_update = self.xml_data.makeelement(tag, {}) 
            self.xml_data.append(node_to_update)

        node_to_update.clear()
        for key in updated_data:
            element = self.xml_data.makeelement(key, {})  
            updated_value = updated_data[key]

            # >> To simulate a list with XML allow multiple XML tags.
            if isinstance(updated_data, list):
                for extra_value in updated_value:
                    element.text = unicode(extra_value)
                    node_to_update.append(element)
            else:
                element.text = unicode(updated_value)
                node_to_update.append(element)

    def remove_node(self, tag, id):
        node_to_remove = self.get_node(tag, id)
        if node_to_remove is None:
            return
        self.xml_data.remove(node_to_remove)

# -------------------------------------------------------------------------------------------------
# --- Repository class for Category objects ---
# Arranges retrieving and storing of the categories from and into the XML data file.
# Creates Category objects with a reference to an instance of AELObjectFactory.
# OBSOLETE CODE THAT WILL BE REMOVE.
# -------------------------------------------------------------------------------------------------
class CategoryRepository(object):
    def __init__(self, data_context, obj_factory):
        self.data_context = data_context
        self.obj_factory = obj_factory

        # When AEL is executed for the first time categories.xml does not exists. In this case,
        # create an empty memory file to avoid concurrent writing problems (AEL maybe called
        # concurrently by skins). When the user creates a Category/Launcher then write
        # categories.xml to the filesystem.
        if not self.data_context.xml_exists():
            log_debug('CategoryRepository::init() Creating empty categories repository.')
            xml_repo_str = (
                '<?xml version="1.0" encoding="utf-8" standalone="yes"?>'
                '<advanced_emulator_launcher version="1">'
                '<control>'
                '<update_timestamp>0.0</update_timestamp>'
                '</control>'
                '</advanced_emulator_launcher>'
            )
            data_context.set_xml_root(xml_repo_str)

    # -------------------------------------------------------------------------------------------------
    # Data model used in the plugin
    # Internally all string in the data model are Unicode. They will be encoded to
    # UTF-8 when writing files.
    # -------------------------------------------------------------------------------------------------
    # These three functions create a new data structure for the given object and (very importantly) 
    # fill the correct default values). These must match what is written/read from/to the XML files.
    # Tag name in the XML is the same as in the data dictionary.
    #
    def _parse_xml_to_dictionary(self, category_element):
        __debug_xml_parser = False
        category = {}
        # Parse child tags of category
        for category_child in category_element:
            # By default read strings
            xml_text = category_child.text if category_child.text is not None else ''
            xml_text = text_unescape_XML(xml_text)
            xml_tag  = category_child.tag
            if __debug_xml_parser: log_debug('{0} --> {1}'.format(xml_tag, xml_text.encode('utf-8')))

            # Now transform data depending on tag name
            if xml_tag == 'finished':
                category[xml_tag] = True if xml_text == 'True' else False
            else:
                # Internal data is always stored as Unicode. ElementTree already outputs Unicode.
                category[xml_tag] = xml_text

        return category

    # Finds a Category by ID in the database. ID may be a Virtual/Special category.
    # Returns a Category object instance or None if the category ID is not found in the DB.
    def find(self, category_id):
        if category_id == VCATEGORY_ADDONROOT_ID:
            category_dic = fs_new_category()
            category_dic['type'] = OBJ_CATEGORY_VIRTUAL
            category_dic['id'] = VCATEGORY_ADDONROOT_ID
            category_dic['m_name'] = 'Root category'
        else:
            category_element = self.data_context.get_node('category', category_id)
            if category_element is None:
                log_debug('Cannot find category with id {0}'.format(category_id))
                return None
            category_dic = self._parse_xml_to_dictionary(category_element)
        category = self.obj_factory.create_from_dic(category_dic)

        return category

    # Returns a list with all the Category objects. Each list element if a Category instance.
    def find_all(self):
        categories = []
        category_elements = self.data_context.get_nodes('category')
        log_debug('Found {0} categories'.format(len(category_elements)))
        for category_element in category_elements:
            category_dic = self._parse_xml_to_dictionary(category_element)
            log_debug('Creating category instance for category {0}'.format(category_dic['id']))
            category = self.obj_factory.create_from_dic(category_dic)
            categories.append(category)

        return categories

    def get_simple_list(self):
        category_list = {}
        category_elements = self.data_context.get_nodes('category')
        for category_element in category_elements:
            id = category_element.find('id').text
            name = category_element.find('m_name').text
            category_list[id] = name

        return category_list

    def count(self):
        return len(self.data_context.get_nodes('category'))

    def save(self, category):
        category_id = category.get_id()
        self.data_context.save_node('category', category_id, category.get_data_dic())
        self.data_context.commit()

    def save_multiple(self, categories):
        for category in categories:
            category_id = category.get_id()
            self.data_context.save_node('category', category_id, category.get_data_dic())
        self.data_context.commit()

    def delete(self, category):
        category_id = category.get_id()
        self.data_context.remove_node('category', category_id)
        self.data_context.commit()

# -------------------------------------------------------------------------------------------------
# Repository class for Launchers objects.
# Arranges retrieving and storing of the launchers from and into the xml data file.
# OBSOLETE CODE THAT WILL BE REMOVE.
# -------------------------------------------------------------------------------------------------
class LauncherRepository(object):
    def __init__(self, data_context, obj_factory):
        # Categories and Launchers share an XML repository file. If categories.xml does not
        # exists, the CategoryRepository() class initialises the XmlDataContext() with
        # empty data.
        self.data_context = data_context
        self.obj_factory = obj_factory

    def _parse_xml_to_dictionary(self, launcher_element):
        __debug_xml_parser = False
        # Sensible default values
        launcher = fs_new_launcher()

        if __debug_xml_parser: 
            log_debug('Element has {0} child elements'.format(len(launcher_element)))

        # Parse child tags of launcher element
        for element_child in launcher_element:
            # >> By default read strings
            xml_text = element_child.text if element_child.text is not None else ''
            xml_text = text_unescape_XML(xml_text)
            xml_tag  = element_child.tag

            if __debug_xml_parser: 
                log_debug('{0} --> {1}'.format(xml_tag, xml_text.encode('utf-8')))

            # >> Transform list() datatype
            if xml_tag == 'args_extra':
                launcher[xml_tag].append(xml_text)
            # >> Transform Bool datatype
            elif xml_tag == 'finished' or xml_tag == 'toggle_window' or xml_tag == 'non_blocking' or \
                 xml_tag == 'multidisc':
                launcher[xml_tag] = True if xml_text == 'True' else False
            # >> Transform Int datatype
            elif xml_tag == 'num_roms' or xml_tag == 'num_parents' or xml_tag == 'num_clones' or \
                 xml_tag == 'num_have' or xml_tag == 'num_miss' or xml_tag == 'num_unknown':
                launcher[xml_tag] = int(xml_text)
            # >> Transform Float datatype
            elif xml_tag == 'timestamp_launcher' or xml_tag == 'timestamp_report':
                launcher[xml_tag] = float(xml_text)
            else:
                launcher[xml_tag] = xml_text

        return launcher

    def find(self, launcher_id):
        if launcher_id in [VLAUNCHER_FAVOURITES_ID, VLAUNCHER_RECENT_ID, VLAUNCHER_MOST_PLAYED_ID]:
            launcher = self.launcher_factory.create_new(launcher_id)
            return launcher

        launcher_element = self.data_context.get_node('launcher', launcher_id)
        if launcher_element is None:
            log_debug('Launcher ID {} not found'.format(launcher_id))
            return None
        launcher_dic = self._parse_xml_to_dictionary(launcher_element)
        launcher = self.obj_factory.create_from_dic(launcher_dic)

        return launcher

    def find_all_ids(self):
        launcher_ids = []
        launcher_id_elements = self.data_context.get_nodes('launcher/id')
        for launcher_id_element in launcher_id_elements:
            launcher_ids.append(launcher_id_element.text())

        return launcher_ids

    def find_all(self):
        launchers = []
        launcher_elements = self.data_context.get_nodes('launcher')
        for launcher_element in launcher_elements:
            launcher_dic = self._parse_xml_to_dictionary(launcher_element)
            launcher = self.obj_factory.create_from_dic(launcher_dic)
            launchers.append(launcher)

        return launchers

    def find_by_launcher_type(self, launcher_type):
        launchers = []
        launcher_elements = self.data_context.get_nodes_by('launcher', 'type', launcher_type )
        for launcher_element in launcher_elements:
            launcher_dic = self._parse_xml_to_dictionary(launcher_element)
            launcher = self.obj_factory.create_from_dic(launcher_dic)
            launchers.append(launcher)

        return launchers

    def find_by_category(self, category_id):
        launchers = []
        launcher_elements = self.data_context.get_nodes_by('launcher', 'categoryID', category_id )
        if launcher_elements is None or len(launcher_elements) == 0:
            log_debug('No launchers found in category {0}'.format(category_id))
            return launchers
        log_debug('{0} launchers found in category {1}'.format(len(launcher_elements), category_id))
        for launcher_element in launcher_elements:
            launcher_dic = self._parse_xml_to_dictionary(launcher_element)
            launcher = self.obj_factory.create_from_dic(launcher_dic)
            launchers.append(launcher)

        return launchers

    def count(self):
        return len(self.data_context.get_nodes('launcher'))

    def save(self, launcher, update_launcher_timestamp = True):
        if update_launcher_timestamp:
            launcher.update_timestamp()
        launcher_id = launcher.get_id()
        launcher_data_dic = launcher.get_data_dic()
        self.data_context.save_node('launcher', launcher_id, launcher_data_dic)
        self.data_context.commit()

    def save_multiple(self, launchers, update_launcher_timestamp = True):
        for launcher in launchers:
            if update_launcher_timestamp:
                launcher.update_timestamp()
            launcher_id = launcher.get_id()
            launcher_data_dic = launcher.get_data_dic()
            self.data_context.save_node('launcher', launcher_id, launcher_data_dic)
        self.data_context.commit()

    def delete(self, launcher):
        launcher_id = launcher.get_id()
        self.data_context.remove_node('launcher', launcher_id)
        self.data_context.commit()



# #################################################################################################
# #################################################################################################
# ROMsets
# #################################################################################################
# #################################################################################################
class RomSetFactory():
    def __init__(self, pluginDataDir):
        self.ROMS_DIR                   = pluginDataDir.pjoin('db_ROMs')
        self.FAV_JSON_FILE_PATH         = pluginDataDir.pjoin('favourites.json')
        self.RECENT_PLAYED_FILE_PATH    = pluginDataDir.pjoin('history.json')
        self.MOST_PLAYED_FILE_PATH      = pluginDataDir.pjoin('most_played.json')
        self.COLLECTIONS_FILE_PATH      = pluginDataDir.pjoin('collections.xml')
        self.COLLECTIONS_DIR            = pluginDataDir.pjoin('db_Collections')
        self.VIRTUAL_CAT_TITLE_DIR      = pluginDataDir.pjoin('db_title')
        self.VIRTUAL_CAT_YEARS_DIR      = pluginDataDir.pjoin('db_years')
        self.VIRTUAL_CAT_GENRE_DIR      = pluginDataDir.pjoin('db_genre')
        self.VIRTUAL_CAT_DEVELOPER_DIR  = pluginDataDir.pjoin('db_developer')
        self.VIRTUAL_CAT_CATEGORY_DIR   = pluginDataDir.pjoin('db_category')
        self.VIRTUAL_CAT_NPLAYERS_DIR   = pluginDataDir.pjoin('db_nplayers')
        self.VIRTUAL_CAT_ESRB_DIR       = pluginDataDir.pjoin('db_esrb')
        self.VIRTUAL_CAT_RATING_DIR     = pluginDataDir.pjoin('db_rating')

        if not self.ROMS_DIR.exists():                  self.ROMS_DIR.makedirs()
        if not self.VIRTUAL_CAT_TITLE_DIR.exists():     self.VIRTUAL_CAT_TITLE_DIR.makedirs()
        if not self.VIRTUAL_CAT_YEARS_DIR.exists():     self.VIRTUAL_CAT_YEARS_DIR.makedirs()
        if not self.VIRTUAL_CAT_GENRE_DIR.exists():     self.VIRTUAL_CAT_GENRE_DIR.makedirs()
        if not self.VIRTUAL_CAT_DEVELOPER_DIR.exists(): self.VIRTUAL_CAT_DEVELOPER_DIR.makedirs()
        if not self.VIRTUAL_CAT_CATEGORY_DIR.exists():  self.VIRTUAL_CAT_CATEGORY_DIR.makedirs()
        if not self.VIRTUAL_CAT_NPLAYERS_DIR.exists():  self.VIRTUAL_CAT_NPLAYERS_DIR.makedirs()
        if not self.VIRTUAL_CAT_ESRB_DIR.exists():      self.VIRTUAL_CAT_ESRB_DIR.makedirs()
        if not self.VIRTUAL_CAT_RATING_DIR.exists():    self.VIRTUAL_CAT_RATING_DIR.makedirs()
        if not self.COLLECTIONS_DIR.exists():           self.COLLECTIONS_DIR.makedirs()

    def create(self, categoryID, launcher_data):
        
        launcherID = launcher_data['id']
        log_debug('romsetfactory.create(): categoryID={0}'.format(categoryID))
        log_debug('romsetfactory.create(): launcherID={0}'.format(launcherID))
        
        description = self.createDescription(categoryID)

        # --- ROM in Favourites ---
        if categoryID == VCATEGORY_FAVOURITES_ID and launcherID == VLAUNCHER_FAVOURITES_ID:
            return FavouritesRomSet(self.FAV_JSON_FILE_PATH, launcher_data, description)
                
        # --- ROM in Most played ROMs ---
        elif categoryID == VCATEGORY_MOST_PLAYED_ID and launcherID == VLAUNCHER_MOST_PLAYED_ID:
            return FavouritesRomSet(self.MOST_PLAYED_FILE_PATH, launcher_data, description)

        # --- ROM in Recently played ROMs list ---
        elif categoryID == VCATEGORY_RECENT_ID and launcherID == VLAUNCHER_RECENT_ID:
            return RecentlyPlayedRomSet(self.RECENT_PLAYED_FILE_PATH, launcher_data, description)

        # --- ROM in Collection ---
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            return CollectionRomSet(self.COLLECTIONS_FILE_PATH, launcher_data, self.COLLECTIONS_DIR, launcherID, description)

        # --- ROM in Virtual Launcher ---
        elif categoryID == VCATEGORY_TITLE_ID:
            log_info('RomSetFactory() loading ROM set Title Virtual Launcher ...')
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_TITLE_DIR, launcher_data, launcherID, description)
        elif categoryID == VCATEGORY_YEARS_ID:
            log_info('RomSetFactory() loading ROM set Years Virtual Launcher ...')
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_YEARS_DIR, launcher_data, launcherID, description)
        elif categoryID == VCATEGORY_GENRE_ID:
            log_info('RomSetFactory() loading ROM set Genre Virtual Launcher ...')
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_GENRE_DIR, launcher_data, launcherID, description)
        elif categoryID == VCATEGORY_DEVELOPER_ID:
            log_info('RomSetFactory() loading ROM set Studio Virtual Launcher ...')
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_DEVELOPER_DIR, launcher_data, launcherID, description)
        elif categoryID == VCATEGORY_NPLAYERS_ID:
            log_info('RomSetFactory() loading ROM set NPlayers Virtual Launcher ...')
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_NPLAYERS_DIR, launcher_data, launcherID, description)
        elif categoryID == VCATEGORY_ESRB_ID:
            log_info('RomSetFactory() loading ROM set ESRB Virtual Launcher ...')
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_ESRB_DIR, launcher_data, launcherID, description)
        elif categoryID == VCATEGORY_RATING_ID:
            log_info('RomSetFactory() loading ROM set Rating Virtual Launcher ...')
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_RATING_DIR, launcher_data, launcherID, description)
        elif categoryID == VCATEGORY_CATEGORY_ID:
            return VirtualLauncherRomSet(self.VIRTUAL_CAT_CATEGORY_DIR, launcher_data, launcherID, description)
          
        elif categoryID == VCATEGORY_PCLONES_ID \
            and 'launcher_display_mode' in launcher_data \
            and launcher_data['launcher_display_mode'] != LAUNCHER_DMODE_FLAT:
            return PcloneRomSet(self.ROMS_DIR, launcher_data, description)
        
        log_info('RomSetFactory() loading standard romset...')
        return StandardRomSet(self.ROMS_DIR, launcher_data, description)

    def createDescription(self, categoryID):
        if categoryID == VCATEGORY_FAVOURITES_ID:
            return RomSetDescription('Favourite', 'Browse favourites')
        elif categoryID == VCATEGORY_MOST_PLAYED_ID:
            return RomSetDescription('Most Played ROM', 'Browse most played')
        elif categoryID == VCATEGORY_RECENT_ID:
            return RomSetDescription('Recently played ROM', 'Browse by recently played')
        elif categoryID == VCATEGORY_TITLE_ID:
            return RomSetDescription('Virtual Launcher Title', 'Browse by Title')
        elif categoryID == VCATEGORY_YEARS_ID:
            return RomSetDescription('Virtual Launcher Years', 'Browse by Year')
        elif categoryID == VCATEGORY_GENRE_ID:
            return RomSetDescription('Virtual Launcher Genre', 'Browse by Genre')
        elif categoryID == VCATEGORY_DEVELOPER_ID:
            return RomSetDescription('Virtual Launcher Studio','Browse by Studio')
        elif categoryID == VCATEGORY_NPLAYERS_ID:
            return RomSetDescription('Virtual Launcher NPlayers', 'Browse by Number of Players')
        elif categoryID == VCATEGORY_ESRB_ID:
            return RomSetDescription('Virtual Launcher ESRB', 'Browse by ESRB Rating')
        elif categoryID == VCATEGORY_RATING_ID:
            return RomSetDescription('Virtual Launcher Rating', 'Browse by User Rating')
        elif categoryID == VCATEGORY_CATEGORY_ID:
            return RomSetDescription('Virtual Launcher Category', 'Browse by Category')

       #if virtual_categoryID == VCATEGORY_TITLE_ID:
       #    vcategory_db_filename = VCAT_TITLE_FILE_PATH
       #    vcategory_name        = 'Browse by Title'
       #elif virtual_categoryID == VCATEGORY_YEARS_ID:
       #    vcategory_db_filename = VCAT_YEARS_FILE_PATH
       #    vcategory_name        = 'Browse by Year'
       #elif virtual_categoryID == VCATEGORY_GENRE_ID:
       #    vcategory_db_filename = VCAT_GENRE_FILE_PATH
       #    vcategory_name        = 'Browse by Genre'
       #elif virtual_categoryID == VCATEGORY_STUDIO_ID:
       #    vcategory_db_filename = VCAT_STUDIO_FILE_PATH
       #    vcategory_name        = 'Browse by Studio'
       #elif virtual_categoryID == VCATEGORY_NPLAYERS_ID:
       #    vcategory_db_filename = VCAT_NPLAYERS_FILE_PATH
       #    vcategory_name        = 'Browse by Number of Players'
       #elif virtual_categoryID == VCATEGORY_ESRB_ID:
       #    vcategory_db_filename = VCAT_ESRB_FILE_PATH
       #    vcategory_name        = 'Browse by ESRB Rating'
       #elif virtual_categoryID == VCATEGORY_RATING_ID:
       #    vcategory_db_filename = VCAT_RATING_FILE_PATH
       #    vcategory_name        = 'Browse by User Rating'
       #elif virtual_categoryID == VCATEGORY_CATEGORY_ID:
       #    vcategory_db_filename = VCAT_CATEGORY_FILE_PATH
       #    vcategory_name        = 'Browse by Category'

        return None

class RomSetDescription():
    def __init__(self, title, description, isRegularLauncher = False):
        
        self.title = title
        self.description = description

        self.isRegularLauncher = isRegularLauncher

class RomSet():
    __metaclass__ = abc.ABCMeta

    def __init__(self, romsDir, launcher, description):
        self.romsDir = romsDir
        self.launcher = launcher
        
        self.description = description

    @abc.abstractmethod
    def romSetFileExists(self):
        return False

    @abc.abstractmethod
    def loadRoms(self):
        return {}
    
    @abc.abstractmethod
    def loadRomsAsList(self):
        return []

    @abc.abstractmethod
    def loadRom(self, romId):
        return None

    @abc.abstractmethod
    def saveRoms(self, roms):
        pass

    @abc.abstractmethod
    def clear(self):
        pass

class StandardRomSet(RomSet):
    def __init__(self, romsDir, launcher, description):
        self.roms_base_noext = launcher['roms_base_noext'] if launcher is not None and 'roms_base_noext' in launcher else None
        self.view_mode = launcher['launcher_display_mode'] if launcher is not None and 'launcher_display_mode' in launcher else None

        if self.roms_base_noext is None:
            self.repositoryFile = romsDir
        elif self.view_mode == LAUNCHER_DMODE_FLAT:
            self.repositoryFile = romsDir.pjoin(self.roms_base_noext + '.json')
        else:
            self.repositoryFile = romsDir.pjoin(self.roms_base_noext + '_parents.json')

        super(StandardRomSet, self).__init__(romsDir, launcher, description)

    def romSetFileExists(self):
        return self.repositoryFile.exists()

    def loadRoms(self):

        if not self.romSetFileExists():
            log_warning('Launcher "{0}" JSON not found.'.format(self.roms_base_noext))
            return None

        log_info('StandardRomSet() Loading ROMs in Launcher ...')
        # was disk_IO.fs_load_ROMs_JSON()
        roms = {}
        # --- Parse using json module ---
        # >> On Github issue #8 a user had an empty JSON file for ROMs. This raises
        #    exception exceptions.ValueError and launcher cannot be deleted. Deal
        #    with this exception so at least launcher can be rescanned.
        log_verb('StandardRomSet.loadRoms() FILE  {0}'.format(self.repositoryFile.getPath()))
        try:
            roms = self.repositoryFile.readJson()
        except ValueError:
            statinfo = roms_json_file.stat()
            log_error('StandardRomSet.loadRoms() ValueError exception in json.load() function')
            log_error('StandardRomSet.loadRoms() Dir  {0}'.format(self.repositoryFile.getPath()))
            log_error('StandardRomSet.loadRoms() Size {0}'.format(statinfo.st_size))

        return roms

    def loadRomsAsList(self):
        roms_dict = self.loadRoms()

        if roms_dict is None:
            return None

        roms = []
        for key in roms_dict:
            roms.append(roms_dict[key])

        return roms

    def loadRom(self, romId):
        roms = self.loadRoms()

        if roms is None:
            log_error("StandardRomSet(): Could not load roms")
            return None

        romData = roms[romId]
        
        if romData is None:
            log_warning("StandardRomSet(): Rom with ID '{0}' not found".format(romId))
            return None

        return romData

    def saveRoms(self, roms):
        fs_write_ROMs_JSON(self.romsDir, self.launcher, roms)
        pass

    def clear(self):
        fs_unlink_ROMs_database(self.romsDir, self.launcher)

class PcloneRomSet(StandardRomSet):
    def __init__(self, romsDir, launcher, description):
        super(PcloneRomSet, self).__init__(romsDir, launcher, description)
        
        self.roms_base_noext = launcher['roms_base_noext'] if launcher is not None and 'roms_base_noext' in launcher else None
        self.repositoryFile = self.romsDir.pjoin(self.roms_base_noext + '_index_PClone.json')

class FavouritesRomSet(StandardRomSet):
    def loadRoms(self):
        log_info('FavouritesRomSet() Loading ROMs in Favourites ...')
        roms = fs_load_Favourites_JSON(self.repositoryFile)
        return roms

    def saveRoms(self, roms):
        log_info('FavouritesRomSet() Saving Favourites ROMs ...')
        fs_write_Favourites_JSON(self.repositoryFile, roms)

class VirtualLauncherRomSet(StandardRomSet):
    def __init__(self, romsDir, launcher, launcherID, description):
        self.launcherID = launcherID
        super(VirtualLauncherRomSet, self).__init__(romsDir, launcher, description)

    def romSetFileExists(self):
        hashed_db_filename = self.romsDir.pjoin(self.launcherID + '.json')
        return hashed_db_filename.exists()

    def loadRoms(self):
        if not self.romSetFileExists():
            log_warning('VirtualCategory "{0}" JSON not found.'.format(self.launcherID))
            return None

        log_info('VirtualCategoryRomSet() Loading ROMs in Virtual Launcher ...')
        roms = fs_load_VCategory_ROMs_JSON(self.romsDir, self.launcherID)
        return roms

    def saveRoms(self, roms):
        fs_write_Favourites_JSON(self.romsDir, roms)
        pass

class RecentlyPlayedRomSet(RomSet):
    def romSetFileExists(self):
        return self.romsDir.exists()

    def loadRoms(self):
        log_info('RecentlyPlayedRomSet() Loading ROMs in Recently Played ROMs ...')
        romsList = self.loadRomsAsList()

        roms = collections.OrderedDict()
        for rom in romsList:
            roms[rom['id']] = rom
            
        return roms

    def loadRomsAsList(self):
        roms = fs_load_Collection_ROMs_JSON(self.romsDir)
        return roms

    def loadRom(self, romId):
        roms = self.loadRomsAsList()

        if roms is None:
            log_error("RecentlyPlayedRomSet(): Could not load roms")
            return None
        
        current_ROM_position = fs_collection_ROM_index_by_romID(romId, roms)
        if current_ROM_position < 0:
            kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
            return None
            
        romData = roms[current_ROM_position]
        
        if romData is None:
            log_warning("RecentlyPlayedRomSet(): Rom with ID '{0}' not found".format(romId))
            return None

        return romData

    def saveRoms(self, roms):
        fs_write_Collection_ROMs_JSON(self.romsDir, roms)
        pass

    def clear(self):
        pass

class CollectionRomSet(RomSet):
    def __init__(self, romsDir, launcher, collection_dir, launcherID, description):
        self.collection_dir = collection_dir
        self.launcherID = launcherID
        super(CollectionRomSet, self).__init__(romsDir, launcher, description)

    def romSetFileExists(self):
        (collections, update_timestamp) = fs_load_Collection_index_XML(self.romsDir)
        collection = collections[self.launcherID]

        roms_json_file = self.romsDir.pjoin(collection['roms_base_noext'] + '.json')
        return roms_json_file.exists()

    def loadRomsAsList(self):
        (collections, update_timestamp) = fs_load_Collection_index_XML(self.romsDir)
        collection = collections[self.launcherID]
        roms_json_file = self.collection_dir.pjoin(collection['roms_base_noext'] + '.json')
        romsList = fs_load_Collection_ROMs_JSON(roms_json_file)
        return romsList
    
    # NOTE ROMs in a collection are stored as a list and ROMs in Favourites are stored as
    #      a dictionary. Convert the Collection list into an ordered dictionary and then
    #      converted back the ordered dictionary into a list before saving the collection.
    def loadRoms(self):
        log_info('CollectionRomSet() Loading ROMs in Collection ...')

        romsList = self.loadRomsAsList()
        
        roms = collections.OrderedDict()
        for rom in romsList:
            roms[rom['id']] = rom
            
        return roms

    def loadRom(self, romId):
        roms = self.loadRomsAsList()

        if roms is None:
            log_error("CollectionRomSet(): Could not load roms")
            return None

        current_ROM_position = fs_collection_ROM_index_by_romID(romId, roms)
        if current_ROM_position < 0:
            kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
            return
            
        romData = roms[current_ROM_position]
        
        if romData is None:
            log_warning("CollectionRomSet(): Rom with ID '{0}' not found".format(romId))
            return None

        return romData

    def saveRoms(self, roms):
        # >> Convert back the OrderedDict into a list and save Collection
        collection_rom_list = []
        for key in roms:
            collection_rom_list.append(roms[key])

        json_file_path = self.romsDir.pjoin(collection['roms_base_noext'] + '.json')
        fs_write_Collection_ROMs_JSON(json_file_path, collection_rom_list)

    def clear(self):
        pass
