from abc import ABCMeta, abstractmethod

import os, sys, string, re

# --- Kodi stuff ---
import xbmc, xbmcgui

# --- Modules/packages in this plugin ---
from constants import *
from platforms import *

from executors import *
from romsets import *
from romstats import *
from disk_IO import *
from utils import *
from utils_kodi import *
from autoconfig import *
    
from gamestream import *

class LauncherFactory():

    def __init__(self, settings, romsetFactory, executorFactory):
        self.settings = settings
        self.romsetFactory = romsetFactory
        self.executorFactory = executorFactory

    def _load(self, launcher_type, launcher_data, launchers, rom):
        
        if launcher_type == LAUNCHER_STANDALONE:
            return ApplicationLauncher(self.settings, self.executorFactory, launcher_data)

        if launcher_type == LAUNCHER_FAVOURITES:
            return KodiLauncher(self.settings, self.executorFactory, launcher_data)
                
        statsStrategy = RomStatisticsStrategy(self.romsetFactory, launchers)

        if launcher_type == LAUNCHER_RETROPLAYER:
            return RetroplayerLauncher(self.settings, None, None, self.settings['escape_romfile'], launcher_data, rom)

        if launcher_type == LAUNCHER_RETROARCH:
            return RetroarchLauncher(self.settings, self.executorFactory, statsStrategy, self.settings['escape_romfile'], launcher_data, rom)

        if launcher_type == LAUNCHER_ROM:
            return StandardRomLauncher(self.settings, self.executorFactory, statsStrategy, self.settings['escape_romfile'], launcher_data, rom, True, True)
        
        if launcher_type == LAUNCHER_LNK:
            return LnkLauncher(self.settings, self.executorFactory, statsStrategy, self.settings['escape_romfile'], launcher_data, rom)

        if launcher_type == LAUNCHER_STEAM:
            return SteamLauncher(self.settings, self.executorFactory, statsStrategy, launcher_data, rom)

        if launcher_type == LAUNCHER_NVGAMESTREAM:
            return NvidiaGameStreamLauncher(self.settings, self.executorFactory, statsStrategy, False, launcher_data, rom)

        log_warning('Unsupported launcher requested. Type {}'.format(launcher_type))
        return None

    def create(self, launcherID, launchers, rom = None):
        
        # Create and return new launcher instance
        if launcherID is None:            
            # --- Show "Create New Launcher" dialog ---
            typeOptions = OrderedDict()
            typeOptions[LAUNCHER_STANDALONE]   = 'Standalone launcher (Game/Application)'
            typeOptions[LAUNCHER_FAVOURITES]   = 'Kodi favourite launcher'
            typeOptions[LAUNCHER_ROM]          = 'ROM launcher (Emulator)'
            typeOptions[LAUNCHER_RETROPLAYER]  = 'ROM launcher (Kodi Retroplayer)'
            typeOptions[LAUNCHER_RETROARCH]    = 'ROM launcher (Retroarch)'
            typeOptions[LAUNCHER_NVGAMESTREAM] = 'Nvidia GameStream'
            if not is_android():
                typeOptions[LAUNCHER_STEAM] = 'Steam launcher'
            if is_windows():
                typeOptions[LAUNCHER_LNK] = 'LNK launcher (Windows only)'

            dialog = DictionaryDialog()
            launcher_type = dialog.select('Create New Launcher', typeOptions)
            if type is None: 
                return None
            else:
                log_info('launcherfactory.create() New launcher (launcher_type = {0})'.format(launcher_type))
                return self._load(launcher_type, {}, launchers, None)
        
        # Load existing launcher and return instance
        if launcherID not in launchers:
            log_error('launcherfactory.create(): Launcher "{0}" not found in launchers'.format(launcherID))
            return None
        
        launcher = launchers[launcherID]
        launcher_type = launcher['type'] if 'type' in launcher else None

        return self._load(launcher_type, launcher, launchers, rom)

#
# Abstract base class for launching anything that is supported.
# Implement classes that inherit this base class to support new ways of launching.
#
class Launcher():
    __metaclass__ = ABCMeta
    
    def __init__(self, launcher, settings, executorFactory, toggle_window, non_blocking = False):
        
        self.launcher        = launcher
        self.settings        = settings
        self.executorFactory = executorFactory

        self.toggle_window  = toggle_window
        self.non_blocking   = non_blocking

        self.application    = None
        self.arguments      = None
        self.title          = None
    
    #
    # Build new launcher.
    # Leave category_id empty to add launcher to root folder.
    #
    def build(self, categories, category_id = None):
        
        launcherID            = misc_generate_random_SID()
        self.launcher         = fs_new_launcher()
        self.launcher['id']   = launcherID
                
        wizard = DummyWizardDialog('categoryID', category_id, None)
        wizard = DummyWizardDialog('type', self.get_launcher_type(), wizard)

        wizard = self._get_builder_wizard(wizard)

        # --- Create new launcher. categories.xml is save at the end of this function ---
        # NOTE than in the database original paths are always stored.
        self.launcher = wizard.runWizard(self.launcher)
        if not self.launcher:
            return None
        
        if self.supports_launching_roms():
            # Choose launcher ROM XML filename. There may be launchers with same name in different categories, or
            # even launcher with the same name in the same category.
            category_name   = categories[category_id]['m_name'] if category_id in categories else VCATEGORY_ADDONROOT_ID
            roms_base_noext = fs_get_ROMs_basename(category_name, self.launcher['m_name'], launcherID)
            self.launcher['roms_base_noext'] = roms_base_noext
            
            # --- Selected asset path ---
            # A) User chooses one and only one assets path
            # B) If this path is different from the ROM path then asset naming scheme 1 is used.
            # B) If this path is the same as the ROM path then asset naming scheme 2 is used.
            # >> Create asset directories. Function detects if we are using naming scheme 1 or 2.
            # >> launcher is edited using Python passing by assignment.
            assets_init_asset_dir(FileNameFactory.create(self.launcher['assets_path']), self.launcher)

        self.launcher['timestamp_launcher'] = time.time()
        #launchers[launcherID] = launcher

        return self.launcher
    
    #
    # Launchs a ROM launcher or standalone launcher
    # For standalone launchers romext is the extension of the application (only used in Windoze)
    #
    @abstractmethod
    def launch(self):

        executor = self.executorFactory.create(self.application)
        
        if executor is None:
            log_error("Cannot create an executor for {0}".format(self.application.getPath()))
            kodi_notify_error('Cannot execute application')
            return

        log_debug('Launcher launching = "{0}"'.format(self.title))
        log_debug('Launcher application = "{0}"'.format(self.application.getPath()))
        log_debug('Launcher arguments = "{0}"'.format(self.arguments))
        log_debug('Launcher executor = "{0}"'.format(executor.__class__.__name__))

        self.preExecution(self.title, self.toggle_window)
        executor.execute(self.application, self.arguments, self.non_blocking)
        self.postExecution(self.toggle_window)

        pass
    
    #
    # These two functions do things like stopping music before lunch, toggling full screen, etc.
    # Variables set in this function:
    # self.kodi_was_playing      True if Kodi player was ON, False otherwise
    # self.kodi_audio_suspended  True if Kodi audio suspended before launching
    #
    # def _run_before_execution(self, rom_title, toggle_screen_flag):
    def preExecution(self, title, toggle_screen_flag):
        
        # --- User notification ---
        if self.settings['display_launcher_notify']:
            kodi_notify('Launching {0}'.format(title))

        # --- Stop/Pause Kodi mediaplayer if requested in settings ---
        self.kodi_was_playing = False
        # id="media_state_action" default="0" values="Stop|Pause|Let Play"
        media_state_action = self.settings['media_state_action']
        media_state_str = ['Stop', 'Pause', 'Let Play'][media_state_action]
        log_verb('_run_before_execution() media_state_action is "{0}" ({1})'.format(media_state_str, media_state_action))
        if media_state_action == 0 and xbmc.Player().isPlaying():
            log_verb('_run_before_execution() Calling xbmc.Player().stop()')
            xbmc.Player().stop()
            xbmc.sleep(100)
            self.kodi_was_playing = True
        elif media_state_action == 1 and xbmc.Player().isPlaying():
            log_verb('_run_before_execution() Calling xbmc.Player().pause()')
            xbmc.Player().pause()
            xbmc.sleep(100)
            self.kodi_was_playing = True

        # --- Force audio suspend if requested in "Settings" --> "Advanced"
        # >> See http://forum.kodi.tv/showthread.php?tid=164522
        self.kodi_audio_suspended = False
        if self.settings['suspend_audio_engine']:
            log_verb('_run_before_execution() Suspending Kodi audio engine')
            xbmc.audioSuspend()
            xbmc.enableNavSounds(False)
            xbmc.sleep(100)
            self.kodi_audio_suspended = True
        else:
            log_verb('_run_before_execution() DO NOT suspend Kodi audio engine')

        # --- Force joystick suspend if requested in "Settings" --> "Advanced"
        # >> See https://forum.kodi.tv/showthread.php?tid=287826&pid=2627128#pid2627128
        # >> See https://forum.kodi.tv/showthread.php?tid=157499&pid=1722549&highlight=input.enablejoystick#pid1722549
        # >> See https://forum.kodi.tv/showthread.php?tid=313615
        self.kodi_joystick_suspended = False
        # if self.settings['suspend_joystick_engine']:
            # log_verb('_run_before_execution() Suspending Kodi joystick engine')
            # >> Research. Get the value of the setting first
            # >> Apparently input.enablejoystick is not supported on Kodi Krypton anymore.
            # c_str = ('{"id" : 1, "jsonrpc" : "2.0",'
            #          ' "method" : "Settings.GetSettingValue",'
            #          ' "params" : {"setting":"input.enablejoystick"}}')
            # response = xbmc.executeJSONRPC(c_str)
            # log_debug('JSON      ''{0}'''.format(c_str))
            # log_debug('Response  ''{0}'''.format(response))

            # c_str = ('{"id" : 1, "jsonrpc" : "2.0",'
            #          ' "method" : "Settings.SetSettingValue",'
            #          ' "params" : {"setting" : "input.enablejoystick", "value" : false} }')
            # response = xbmc.executeJSONRPC(c_str)
            # log_debug('JSON      ''{0}'''.format(c_str))
            # log_debug('Response  ''{0}'''.format(response))
            # self.kodi_joystick_suspended = True

            # log_error('_run_before_execution() Suspending Kodi joystick engine not supported on Kodi Krypton!')
        # else:
            # log_verb('_run_before_execution() DO NOT suspend Kodi joystick engine')

        # --- Toggle Kodi windowed/fullscreen if requested ---
        if toggle_screen_flag:
            log_verb('_run_before_execution() Toggling Kodi fullscreen')
            kodi_toogle_fullscreen()
        else:
            log_verb('_run_before_execution() Toggling Kodi fullscreen DEACTIVATED in Launcher')

        # --- Pause Kodi execution some time ---
        delay_tempo_ms = self.settings['delay_tempo']
        log_verb('_run_before_execution() Pausing {0} ms'.format(delay_tempo_ms))
        xbmc.sleep(delay_tempo_ms)
        log_debug('_run_before_execution() function ENDS')

    def postExecution(self, toggle_screen_flag):

        # --- Stop Kodi some time ---
        delay_tempo_ms = self.settings['delay_tempo']
        log_verb('postExecution() Pausing {0} ms'.format(delay_tempo_ms))
        xbmc.sleep(delay_tempo_ms)

        # --- Toggle Kodi windowed/fullscreen if requested ---
        if toggle_screen_flag:
            log_verb('postExecution() Toggling Kodi fullscreen')
            kodi_toogle_fullscreen()
        else:
            log_verb('postExecution() Toggling Kodi fullscreen DEACTIVATED in Launcher')

        # --- Resume audio engine if it was suspended ---
        # Calling xmbc.audioResume() takes a loong time (2/4 secs) if audio was not properly suspended!
        # Also produces this in Kodi's log:
        # WARNING: CActiveAE::StateMachine - signal: 0 from port: OutputControlPort not handled for state: 7
        #   ERROR: ActiveAE::Resume - failed to init
        if self.kodi_audio_suspended:
            log_verb('postExecution() Kodi audio engine was suspended before launching')
            log_verb('postExecution() Resuming Kodi audio engine')
            xbmc.audioResume()
            xbmc.enableNavSounds(True)
            xbmc.sleep(100)
        else:
            log_verb('_run_before_execution() DO NOT resume Kodi audio engine')

        # --- Resume joystick engine if it was suspended ---
        if self.kodi_joystick_suspended:
            log_verb('postExecution() Kodi joystick engine was suspended before launching')
            log_verb('postExecution() Resuming Kodi joystick engine')
            # response = xbmc.executeJSONRPC(c_str)
            # log_debug('JSON      ''{0}'''.format(c_str))
            # log_debug('Response  ''{0}'''.format(response))
            log_verb('postExecution() Not supported on Kodi Krypton!')
        else:
            log_verb('postExecution() DO NOT resume Kodi joystick engine')

        # --- Resume Kodi playing if it was paused. If it was stopped, keep it stopped. ---
        media_state_action = self.settings['media_state_action']
        media_state_str = ['Stop', 'Pause', 'Let Play'][media_state_action]
        log_verb('postExecution() media_state_action is "{0}" ({1})'.format(media_state_str, media_state_action))
        log_verb('postExecution() self.kodi_was_playing is {0}'.format(self.kodi_was_playing))
        if self.kodi_was_playing and media_state_action == 1:
            log_verb('postExecution() Calling xbmc.Player().play()')
            xbmc.Player().play()
        log_debug('postExecution() function ENDS')

    @abstractmethod
    def supports_launching_roms(self):
        return False
    
    @abstractmethod
    def get_launcher_type(self):
        return LAUNCHER_STANDALONE

    @abstractmethod
    def get_launcher_type_name(self):        
        return "Standalone launcher"

    def get_id(self):
        return self.launcher['id']

    def get_name(self):
        return self.launcher['m_name'] if 'm_name' in self.launcher else 'Unknown'
    
    def get_platform(self):
        return self.launcher['platform'] if 'platform' in self.launcher else ''

    def get_releaseyear(self):
        return self.launcher['m_year'] if 'm_year' in self.launcher else ''
        
    def get_genre(self):
        return self.launcher['m_genre'] if 'm_genre' in self.launcher else ''
    
    def get_developer(self):
        return self.launcher['m_developer'] if 'm_developer' in self.launcher else ''

    def get_rating(self):
        return int(self.launcher['m_rating']) if self.launcher['m_rating'] else -1

    def get_plot(self):
        return self.launcher['m_plot'] if 'm_plot' in self.launcher else ''

    def get_category_id(self):
        return self.launcher['category_id'] if 'category_id' in self.launcher else None
    
    def is_in_windowed_mode(self):
        return self.launcher['toggle_window']

    def set_windowed_mode(self, windowed_mode):
        self.launcher['toggle_window'] = windowed_mode
        return self.is_in_windowed_mode()

    def is_non_blocking(self):
        return self.launcher['non_blocking']

    def set_non_blocking(self, is_non_blocking):
        self.launcher['non_blocking'] = is_non_blocking
        return self.is_non_blocking()

    def get_assets(self):
        assets = {}
        
        assets[ASSET_BANNER]     = self.launcher['s_banner']      if self.launcher['s_banner']     else ''
        assets[ASSET_ICON]       = self.launcher['s_icon']        if self.launcher['s_icon']       else ''
        assets[ASSET_FANART]     = self.launcher['s_fanart']      if self.launcher['s_fanart']     else ''
        assets[ASSET_POSTER]     = self.launcher['s_poster']      if self.launcher['s_poster']     else ''
        assets[ASSET_CLEARLOGO]  = self.launcher['s_clearlogo']   if self.launcher['s_clearlogo']  else ''
        assets[ASSET_CONTROLLER] = self.launcher['s_controller']  if self.launcher['s_controller'] else ''
        assets[ASSET_TRAILER]    = self.launcher['s_trailer']     if self.launcher['s_trailer']    else ''

        return assets

    def get_asset_defaults(self):
        default_assets = {}
        
        default_assets[ASSET_BANNER]     = ASSET_KEYS_TO_CONSTANTS[self.launcher['default_banner']]      if self.launcher['default_banner']     else ''
        default_assets[ASSET_ICON]       = ASSET_KEYS_TO_CONSTANTS[self.launcher['default_icon']]        if self.launcher['default_icon']       else ''
        default_assets[ASSET_FANART]     = ASSET_KEYS_TO_CONSTANTS[self.launcher['default_fanart']]      if self.launcher['default_fanart']     else ''
        default_assets[ASSET_POSTER]     = ASSET_KEYS_TO_CONSTANTS[self.launcher['default_poster']]      if self.launcher['default_poster']     else ''
        default_assets[ASSET_CLEARLOGO]  = ASSET_KEYS_TO_CONSTANTS[self.launcher['default_clearlogo']]   if self.launcher['default_clearlogo']  else ''

        return default_assets
    
    def set_default_asset(self, default_asset_kind_key, mapped_to_kind_key):
        
        asset_kind  = assets_get_info_scheme(default_asset_kind_key)
        map_to_kind = assets_get_info_scheme(mapped_to_kind_key)

        self.launcher[asset_kind.default_key] = map_to_kind.key

    def get_data(self):
        return self.launcher

    def get_state(self):
        finished = self.launcher['finished']
        finished_display = 'Finished' if finished == True else 'Unfinished'
        return finished_display
    
    #
    # Returns a dictionary of options to choose from
    # with which you can edit or manage this specific launcher.
    #
    @abstractmethod
    def get_edit_options(self):
        return {}
        
    #
    # Returns a dictionary of options to choose from
    # with which you can do advanced modifications on this specific launcher.
    #
    @abstractmethod
    def get_advanced_modification_options(self):
        
        options = OrderedDict()
        #options['CHANGE_APPLICATION'] = "Change Application: {0}".format(self.get_launcher_type_name()) #deprecated
        
        return options
    #
    # Returns a dictionary of options to choose from
    # with which you can edit the metadata of this specific launcher.
    #
    def get_metadata_edit_options(self):
        
        # >> Metadata edit dialog
        NFO_FileName = fs_get_launcher_NFO_name(self.settings, self.launcher)
        NFO_found_str = 'NFO found' if NFO_FileName.exists() else 'NFO not found'
        plot_str = text_limit_string(self.launcher['m_plot'], PLOT_STR_MAXSIZE)

        rating = self.get_rating()
        if rating == -1:
            rating = 'not rated'

        options = OrderedDict()
        options['EDIT_TITLE']             = "Edit Title: '{0}'".format(self.get_name())
        options['EDIT_PLATFORM']          = "Edit Platform: {0}".format(self.launcher['platform'])
        options['EDIT_RELEASEYEAR']       = "Edit Release Year: '{0}'".format(self.launcher['m_year'])
        options['EDIT_GENRE']             = "Edit Genre: '{0}'".format(self.launcher['m_genre'])
        options['EDIT_DEVELOPER']         = "Edit Developer: '{0}'".format(self.launcher['m_developer'])
        options['EDIT_RATING']            = "Edit Rating: '{0}'".format(rating)
        options['EDIT_PLOT']              = "Edit Plot: '{0}'".format(plot_str)
        options['IMPORT_NFO_FILE']        = 'Import NFO file (default, {0})'.format(NFO_found_str)
        options['IMPORT_NFO_FILE_BROWSE'] = 'Import NFO file (browse NFO file) ...'
        options['SAVE_NFO_FILE']          = 'Save NFO file (default location)'

        return options

    def change_finished_status(self):
        finished = self.launcher['finished']
        finished = False if finished else True
        self.launcher['finished'] = finished

    def update_timestamp(self):
        self.launcher['timestamp_launcher'] = time.time()

    def update_category(self, category_id):
        self.launcher['categoryID'] = category_id

    def update_platform(self, platform):
        self.launcher['platform'] = platform

    def update_releaseyear(self, releaseyear):
        self.launcher['m_year'] = releaseyear

    def update_genre(self, genre):
        self.launcher['m_genre'] = genre

    def update_developer(self, developer):
        self.launcher['m_developer'] = developer

    def update_rating(self, rating):
        self.launcher['m_rating'] = int(rating)
        
    def update_plot(self, plot):
        self.launcher['m_plot'] = plot
      
    #
    # Python data model: lists and dictionaries are mutable. It means the can be changed if passed as
    # parameters of functions. However, items can not be replaced by new objects!
    # Notably, numbers, strings and tuples are immutable. Dictionaries and lists are mutable.
    #
    # See http://stackoverflow.com/questions/986006/how-do-i-pass-a-variable-by-reference
    # See https://docs.python.org/2/reference/datamodel.html
    #
    # Function asumes that the NFO file already exists.
    #
    def import_nfo_file(self, nfo_file_path):

        # --- Get NFO file name ---
        log_debug('launcher.import_nfo_file() Importing launcher NFO "{0}"'.format(nfo_file_path.getOriginalPath()))

        # --- Import data ---
        if nfo_file_path.exists():
            # >> Read NFO file data
            try:
                item_nfo = nfo_file_path.readAllUnicode()
                item_nfo = item_nfo.replace('\r', '').replace('\n', '')
            except:
                kodi_notify_warn('Exception reading NFO file {0}'.format(nfo_file_path.getOriginalPath()))
                log_error("launcher.import_nfo_file() Exception reading NFO file '{0}'".format(nfo_file_path.getOriginalPath()))
                return False
            # log_debug("fs_import_launcher_NFO() item_nfo '{0}'".format(item_nfo))
        else:
            kodi_notify_warn('NFO file not found {0}'.format(nfo_file_path.getBase()))
            log_info("launcher.import_nfo_file() NFO file not found '{0}'".format(nfo_file_path.getOriginalPath()))
            return False

        # Find data
        item_year      = re.findall('<year>(.*?)</year>',           item_nfo)
        item_genre     = re.findall('<genre>(.*?)</genre>',         item_nfo)
        item_developer = re.findall('<developer>(.*?)</developer>', item_nfo)
        item_rating    = re.findall('<rating>(.*?)</rating>',       item_nfo)
        item_plot      = re.findall('<plot>(.*?)</plot>',           item_nfo)

        # >> Careful about object mutability! This should modify the dictionary
        # >> passed as argument outside this function.
        if item_year:      self.update_releaseyear(text_unescape_XML(item_year[0]))
        if item_genre:     self.update_genre(text_unescape_XML(item_genre[0]))
        if item_developer: self.update_developer(text_unescape_XML(item_developer[0]))
        if item_rating:    self.update_rating(text_unescape_XML(item_rating[0]))
        if item_plot:      self.update_plot(text_unescape_XML(item_plot[0]))

        log_verb("import_nfo_file() Imported '{0}'".format(nfo_file_path.getOriginalPath()))

        return True

    #
    # Standalone launchers:
    #   NFO files are stored in self.settings["launchers_nfo_dir"] if not empty.
    #   If empty, it defaults to DEFAULT_LAUN_NFO_DIR.
    #
    # ROM launchers:
    #   Same as standalone launchers.
    #
    def export_nfo_file(self, nfo_FileName):
        # --- Get NFO file name ---
        log_debug('export_nfo_file() Exporting launcher NFO "{0}"'.format(nfo_FileName.getOriginalPath()))

        # If NFO file does not exist then create them. If it exists, overwrite.
        nfo_content = []
        nfo_content.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        nfo_content.append('<!-- Exported by AEL on {0} -->\n'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
        nfo_content.append('<launcher>\n')
        nfo_content.append(XML_text('year',      self.get_releaseyear()))
        nfo_content.append(XML_text('genre',     self.get_genre()))
        nfo_content.append(XML_text('developer', self.get_developer()))
        nfo_content.append(XML_text('rating',    self.get_rating()))
        nfo_content.append(XML_text('plot',      self.get_plot()))
        nfo_content.append('</launcher>\n')
        full_string = ''.join(nfo_content).encode('utf-8')
        try:
            nfo_FileName.writeAll(full_string)
        except:
            kodi_notify_warn('Exception writing NFO file {0}'.format(nfo_FileName.getPath()))
            log_error("export_nfo_file() Exception writing'{0}'".format(nfo_FileName.getOriginalPath()))
            return False
        log_debug("export_nfo_file() Created '{0}'".format(nfo_FileName.getOriginalPath()))

        return True

    def export_configuration(self, path_to_export, categories):
        
        launcher_fn_str = 'Launcher_' + text_title_to_filename_str(self.get_name()) + '.xml'
        log_debug('launcher.export_configuration() Exporting Launcher configuration')
        log_debug('launcher.export_configuration() Name     "{0}"'.format(self.get_name()))
        log_debug('launcher.export_configuration() ID       {0}'.format(self.get_id()))
        log_debug('launcher.export_configuration() l_fn_str "{0}"'.format(launcher_fn_str))

        if not path_to_export: return

        export_FN = FileNameFactory.create(path_to_export).pjoin(launcher_fn_str)
        if export_FN.exists():
            confirm = kodi_dialog_yesno('Overwrite file {0}?'.format(export_FN.getPath()))
            if not confirm:
                kodi_notify_warn('Export of Launcher XML cancelled')
        
        # --- Print error message is something goes wrong writing file ---
        try:
            autoconfig_export_launcher(self.launcher, export_FN, categories)
        except AEL_Error as E:
            kodi_notify_warn('{0}'.format(E))
        else:
            kodi_notify('Exported Launcher "{0}" XML config'.format(self.get_name()))
        # >> No need to update categories.xml and timestamps so return now.

    # todo: move roms_dir to factory and inject through constructor for rom launchers only
    # categories should come from some kind of categoriesrepository
    @abstractmethod
    def change_name(self, new_name, categories, roms_dir):
        return False
        if new_name == '': 
            return False
        
        old_launcher_name = self.get_name()
        new_launcher_name = new_name.rstrip()

        log_debug('launcher.change_name() Changing name: old_launcher_name "{0}"'.format(old_launcher_name))
        log_debug('launcher.change_name() Changing name: new_launcher_name "{0}"'.format(new_launcher_name))
        
        if old_launcher_name == new_launcher_name:
            return False
        
        # --- Rename ROMs XML/JSON file (if it exists) and change launcher ---
        old_roms_base_noext = self.launcher['roms_base_noext']
        categoryID = self.get_category_id()

        category_name = categories[categoryID]['m_name'] if categoryID in categories else VCATEGORY_ADDONROOT_ID
        new_roms_base_noext = fs_get_ROMs_basename(category_name, new_launcher_name, self.get_id())
        fs_rename_ROMs_database(ROMS_DIR, old_roms_base_noext, new_roms_base_noext)

        self.launcher['m_name'] = new_launcher_name
        self.launcher['roms_base_noext'] = new_roms_base_noext

        return True
 
    def save(self, categories_file_path, categories, launchers):
        self.launcher['timestamp_launcher'] = time.time()
        fs_write_catfile(categories_file_path, categories, launchers)
    
    #
    # Creates a new launcher using a wizard of dialogs.
    #
    @abstractmethod
    def _get_builder_wizard(self, wizard):
        return wizard
    
    def _get_title_from_app_path(self, input, item_key, launcher):

        if input:
            return input

        app = launcher['application']
        appPath = FileNameFactory.create(app)

        title = appPath.getBase_noext()
        title_formatted = title.replace('.' + title.split('.')[-1], '').replace('.', ' ')

        return title_formatted
    
    def _get_appbrowser_filter(self, item_key, launcher):
    
        if item_key in launcher:
            application = launcher[item_key]
            if application == 'JAVA':
                return '.jar'

        return '.bat|.exe|.cmd|.lnk' if is_windows() else ''

    #
    # Wizard helper, when a user wants to set a custom value
    # instead of the predefined list items.
    #
    def _user_selected_custom_browsing(self, item_key, launcher):
        return launcher[item_key] == 'BROWSE'
    
#
# Abstract base class for launching anything roms or item based.
# This base class has methods to support launching applications with variable input
# arguments or items like roms.
# Inherit from this base class to implement your own specific rom launcher.
#
class RomLauncher(Launcher):
    __metaclass__ = ABCMeta
    
    def __init__(self, settings, executorFactory, statsStrategy, escape_romfile, launcher, rom, validate_if_app_exists, validate_if_rom_exists):

        self.validate_if_app_exists = validate_if_app_exists
        self.validate_if_rom_exists = validate_if_rom_exists

        self.rom = rom
        self.categoryID = ''

        self.escape_romfile = escape_romfile
        self.statsStrategy = statsStrategy

        non_blocking_flag = launcher['non_blocking'] if 'non_blocking' in launcher else False
        toggle_window =  launcher['toggle_window'] if 'toggle_window' in launcher else False
        super(RomLauncher, self).__init__(launcher, settings, executorFactory, toggle_window, non_blocking_flag)
    
    @abstractmethod
    def _selectApplicationToUse(self):
        pass
    
    @abstractmethod
    def _selectArgumentsToUse(self):
        pass

    @abstractmethod
    def _selectRomFileToUse(self):
        return None
    
    # ~~~~ Argument substitution ~~~~~
    def _parseArguments(self, romFile):
        
        # --- Escape quotes and double quotes in ROMFileName ---
        # >> This maybe useful to Android users with complex command line arguments
        if self.escape_romfile:
            log_info("RomLauncher() Escaping ROMFileName ' and \"")
            romFile.escapeQuotes()

        apppath       = self.application.getDir()
        rompath       = romFile.getDir()
        rombase       = romFile.getBase()
        rombase_noext = romFile.getBase_noext()
        log_info('RomLauncher() romfile      "{0}"'.format(romFile.getPath()))
        log_info('RomLauncher() rompath      "{0}"'.format(rompath))
        log_info('RomLauncher() rombase      "{0}"'.format(rombase))
        log_info('RomLauncher() rombasenoext "{0}"'.format(rombase_noext))
        log_info('RomLauncher() application  "{0}"'.format(self.application.getPath()))
        log_info('RomLauncher() appbase      "{0}"'.format(self.application.getBase()))
        log_info('RomLauncher() apppath      "{0}"'.format(apppath))

        # ~~~~ Argument substitution ~~~~~
        log_info('RomLauncher() raw arguments   "{0}"'.format(self.arguments))
        self.arguments = self.arguments.replace('$categoryID$', self.categoryID)
        self.arguments = self.arguments.replace('$launcherID$', self.launcher['id'])
        self.arguments = self.arguments.replace('$romID$', self.rom['id'])
        self.arguments = self.arguments.replace('$rom$', romFile.getPath())
        self.arguments = self.arguments.replace('$romfile$', romFile.getPath())
        self.arguments = self.arguments.replace('$rompath$', rompath)
        self.arguments = self.arguments.replace('$rombase$', rombase)
        self.arguments = self.arguments.replace('$rombasenoext$', rombase_noext)
        self.arguments = self.arguments.replace('$romtitle$', self.title)
        self.arguments = self.arguments.replace('$apppath$', apppath)
        self.arguments = self.arguments.replace('$appbase$', self.application.getBase())

        # >> Legacy names for argument substitution
        self.arguments = self.arguments.replace('%rom%', romFile.getPath())
        self.arguments = self.arguments.replace('%ROM%', romFile.getPath())

        # automatic substitution of rom values
        for rom_key, rom_value in self.rom.iteritems():
            if isinstance(rom_value, basestring):
                self.arguments = self.arguments.replace('${}$'.format(rom_key), rom_value)        
                
        # automatic substitution of launcher values
        for launcher_key, launcher_value in self.launcher.iteritems():
            if isinstance(launcher_value, basestring):
                self.arguments = self.arguments.replace('${}$'.format(launcher_key), launcher_value)
                
        log_info('RomLauncher() final arguments "{0}"'.format(self.arguments))
    
    def launch(self):
        
        self.title  = self.rom['m_name']

        self._selectApplicationToUse()
        self._selectArgumentsToUse()
        
        ROMFileName = self._selectRomFileToUse()

        log_info('RomLauncher() ROMFileName OP "{0}"'.format(ROMFileName.getOriginalPath()))
        log_info('RomLauncher() ROMFileName  P "{0}"'.format(ROMFileName.getPath()))

        # --- Check for errors and abort if found --- todo: CHECK
        if self.validate_if_app_exists and not self.application.exists():
            log_error('Launching app not found "{0}"'.format(self.application.getPath()))
            kodi_notify_warn('Launching app not found {0}'.format(self.application.getOriginalPath()))
            return

        if self.validate_if_rom_exists and not ROMFileName.exists():
            log_error('ROM not found "{0}"'.format(ROMFileName.getPath()))
            kodi_notify_warn('ROM not found "{0}"'.format(ROMFileName.getOriginalPath()))
            return
        
        self._parseArguments(ROMFileName)
        self.statsStrategy.updateRecentlyPlayedRom(self.rom)       
        
        super(RomLauncher, self).launch()
        pass

    def supports_launching_roms(self):
        return True  
    
    def get_edit_options(self):

        finished_str = 'Finished' if self.launcher['finished'] == True else 'Unfinished'
        category_name = 'ToDo'
        #if self.launchers[launcherID]['categoryID'] == VCATEGORY_ADDONROOT_ID:
        #    category_name = 'Addon root (no category)'
        #else:
        #    category_name = self.categories[self.launchers[launcherID]['categoryID']]['m_name']
        options = OrderedDict([
           ('EDIT_METADATA',        'Edit Metadata ...'),
           ('EDIT_ASSETS',          'Edit Assets/Artwork ...'),
           ('SET_DEFAULT_ASSETS',   'Choose default Assets/Artwork ...'),
           ('CHANGE_CATEGORY',      'Change Category: {0}'.format(category_name)),
           ('LAUNCHER_STATUS',      'Launcher status: {0}'.format(finished_str)),
           ('MANAGE_ROMS',          'Manage ROMs ...'),
           ('AUDIT_ROMS',           'Audit ROMs / Launcher view mode ...'),
           ('ADVANCED_MODS',        'Advanced Modifications ...'),
           ('EXPORT_LAUNCHER',      'Export Launcher XML configuration ...'),
           ('DELETE_LAUNCHER',      'Delete Launcher')  
        ])

        return options
    
    # Returns the dialog options to choose from when managing the roms.
    def get_manage_roms_options(self):
        
        options = OrderedDict()
        options['SET_ROMS_DEFAULT_ARTWORK'] = 'Choose ROMs default artwork ...'
        options['SET_ROMS_ASSET_DIRS']      = 'Manage ROMs asset directories ...'
        options['SCAN_LOCAL_ARTWORK']       = 'Scan ROMs local artwork'
        options['SCRAPE_LOCAL_ARTWORK']     = 'Scrape ROMs local artwork'
        options['REMOVE_DEAD_ROMS']         = 'Remove dead/missing ROMs'
        options['IMPORT_ROMS']              = 'Import ROMs metadata from NFO files'
        options['EXPORT_ROMS']              = 'Export ROMs metadata to NFO files'
        options['DELETE_ROMS_NFO']          = 'Delete ROMs NFO files'
        options['CLEAR_ROMS']               = 'Clear ROMs from launcher'

        return options

    def get_audit_roms_options(self):
        
        display_mode_str        = self.launcher['launcher_display_mode']
        no_intro_display_mode  = self.launcher['nointro_display_mode']

        options = OrderedDict()
        options['CHANGE_DISPLAY_MODE']      = 'Change launcher display mode (now {0}) ...'.format(display_mode_str)

        if self.has_nointro_xml():
            nointro_xml_file = self.launcher['nointro_xml_file']
            options['DELETE_NO_INTRO']      = 'Delete No-Intro/Redump DAT: {0}'.format(nointro_xml_file)
        else:
            options['ADD_NO_INTRO']         = 'Add No-Intro/Redump XML DAT ...'
        
        options['CREATE_PARENTCLONE_DAT']   = 'Create Parent/Clone DAT based on ROM filenames'
        options['CHANGE_DISPLAY_ROMS']      = 'Display ROMs (now {0}) ...'.format(no_intro_display_mode)
        options['UPDATE_ROM_AUDIT']         = 'Update ROM audit'

        return options

    def get_rom_assets(self):
        assets = {}
        
        assets[ASSET_BANNER]     = self.launcher['s_banner']      if self.launcher['s_banner']     else ''
        assets[ASSET_ICON]       = self.launcher['s_icon']        if self.launcher['s_icon']       else ''
        assets[ASSET_FANART]     = self.launcher['s_fanart']      if self.launcher['s_fanart']     else ''
        assets[ASSET_POSTER]     = self.launcher['s_poster']      if self.launcher['s_poster']     else ''
        assets[ASSET_CLEARLOGO]  = self.launcher['s_clearlogo']   if self.launcher['s_clearlogo']  else ''
        assets[ASSET_CONTROLLER] = self.launcher['s_controller']  if self.launcher['s_controller'] else ''
        assets[ASSET_TRAILER]    = self.launcher['s_trailer']     if self.launcher['s_trailer']    else ''

        return assets

    def get_rom_asset_defaults(self):
        
        default_assets = {}
        
        default_assets[ASSET_BANNER]     = ASSET_KEYS_TO_CONSTANTS[self.launcher['roms_default_banner']]    if self.launcher['roms_default_banner']     else ''
        default_assets[ASSET_ICON]       = ASSET_KEYS_TO_CONSTANTS[self.launcher['roms_default_icon']]      if self.launcher['roms_default_icon']       else ''
        default_assets[ASSET_FANART]     = ASSET_KEYS_TO_CONSTANTS[self.launcher['roms_default_fanart']]    if self.launcher['roms_default_fanart']     else ''
        default_assets[ASSET_POSTER]     = ASSET_KEYS_TO_CONSTANTS[self.launcher['roms_default_poster']]    if self.launcher['roms_default_poster']     else ''
        default_assets[ASSET_CLEARLOGO]  = ASSET_KEYS_TO_CONSTANTS[self.launcher['roms_default_clearlogo']] if self.launcher['roms_default_clearlogo']  else ''
        
        return default_assets
    
    def get_duplicated_asset_dirs(self):
        duplicated_bool_list   = [False] * len(ROM_ASSET_LIST)
        duplicated_name_list   = []

        # >> Check for duplicated asset paths
        for i, asset_i in enumerate(ROM_ASSET_LIST[:-1]):
            A_i = assets_get_info_scheme(asset_i)
            for j, asset_j in enumerate(ROM_ASSET_LIST[i+1:]):
                A_j = assets_get_info_scheme(asset_j)
                # >> Exclude unconfigured assets (empty strings).
                if not self.launcher[A_i.path_key] or not self.launcher[A_j.path_key]: continue
                # log_debug('asset_get_duplicated_asset_list() Checking {0:<9} vs {1:<9}'.format(A_i.name, A_j.name))
                if self.launcher[A_i.path_key] == self.launcher[A_j.path_key]:
                    duplicated_bool_list[i] = True
                    duplicated_name_list.append('{0} and {1}'.format(A_i.name, A_j.name))
                    log_info('asset_get_duplicated_asset_list() DUPLICATED {0} and {1}'.format(A_i.name, A_j.name))

        return duplicated_name_list

    def set_default_rom_asset(self, default_asset_kind_key, mapped_to_kind_key):
        
        asset_kind  = assets_get_info_scheme(default_asset_kind_key)
        map_to_kind = assets_get_info_scheme(mapped_to_kind_key)

        self.launcher[asset_kind.rom_default_key] = map_to_kind.key

    def get_asset_path(self, asset_info):
        if not asset_info:
            return None

        return self.launcher[asset_info.path_key] if asset_info.path_key in self.launcher else None

    def set_asset_path(self, asset_info, path):
        log_debug('Setting "{}" to {}'.format(asset_info.path_key, path))
        self.launcher[asset_info.path_key] = path

    # todo: move roms_dir to factory and inject through constructor for rom launchers only
    # categories should come from some kind of categoriesrepository
    def change_name(self, new_name, categories, roms_dir):
        if new_name == '': 
            return False
        
        old_launcher_name = self.get_name()
        new_launcher_name = new_name.rstrip()

        log_debug('launcher.change_name() Changing name: old_launcher_name "{0}"'.format(old_launcher_name))
        log_debug('launcher.change_name() Changing name: new_launcher_name "{0}"'.format(new_launcher_name))
        
        if old_launcher_name == new_launcher_name:
            return False
        
        # --- Rename ROMs XML/JSON file (if it exists) and change launcher ---
        old_roms_base_noext = self.launcher['roms_base_noext']
        categoryID = self.get_category_id()

        category_name = categories[categoryID]['m_name'] if categoryID in categories else VCATEGORY_ADDONROOT_ID
        new_roms_base_noext = fs_get_ROMs_basename(category_name, new_launcher_name, self.get_id())
        fs_rename_ROMs_database(roms_dir, old_roms_base_noext, new_roms_base_noext)

        self.launcher['m_name'] = new_launcher_name
        self.launcher['roms_base_noext'] = new_roms_base_noext

        return True

    def getRomPath(self):
        return FileNameFactory.create(self.launcher['rompath'])

    def change_rom_path(self, path):
        self.launcher['rompath'] = path

    def get_roms_base(self):
        return self.launcher['roms_base_noext']

    # todo: add actual romset here
    def clear_roms(self):
        self.launcher['num_roms'] = 0

    def get_display_mode(self):
        return self.launcher['launcher_display_mode']
            
    def change_display_mode(self, mode):

        if mode == LAUNCHER_DMODE_PCLONE or mode == LAUNCHER_DMODE_1G1R:
            # >> Check if user configured a No-Intro DAT. If not configured  or file does
            # >> not exists refuse to switch to PClone view and force normal mode.
            if not launcher.has_nointro_xml():
                log_info('RomsLauncher.change_display_mode() No-Intro DAT not configured.')
                log_info('RomsLauncher.change_display_mode() Forcing Flat view mode.')
                mode = LAUNCHER_DMODE_FLAT
            else:
                nointro_xml_file_FName = launcher.get_nointro_xml_filepath()
                if not nointro_xml_file_FName.exists():
                    log_info('RomsLauncher.change_display_mode() No-Intro DAT not found.')
                    log_info('RomsLauncher.change_display_mode() Forcing Flat view mode.')
                    kodi_dialog_OK('No-Intro DAT cannot be found. PClone or 1G1R view mode cannot be set.')
                    mode = LAUNCHER_DMODE_FLAT

        self.launcher['launcher_display_mode'] = mode
        log_debug('launcher_display_mode = {0}'.format(mode))
        return mode
        
    def get_nointro_display_mode(self):
        return self.launcher['nointro_display_mode']
           
    def change_nointro_display_mode(self, mode):
        
        self.launcher['nointro_display_mode'] = mode
        log_info('Launcher nointro display mode changed to "{0}"'.format(self.launcher['nointro_display_mode']))
        return mode

    def has_nointro_xml(self):
        return self.launcher['nointro_xml_file']
    
    def get_nointro_xml_filepath(self):
        return FileNameFactory.create(self.launcher['nointro_xml_file'])

    def set_nointro_xml_file(self, path):
        self.launcher['nointro_xml_file'] = path

    def reset_nointro_xmldata(self):
        if self.launcher['nointro_xml_file']:
            log_info('Deleting XML DAT file and forcing launcher to Normal view mode.')
            self.launcher['nointro_xml_file'] = ''

    def set_number_of_roms(self, num_of_roms):
        self.launcher['num_roms'] = num_of_roms
        
    def support_multidisc(self):
        return self.launcher['multidisc']

    def set_multidisc_support(self, supports_multidisc):
        self.launcher['multidisc'] = supports_multidisc
        return self.support_multidisc()

    def _get_extensions_from_app_path(self, input, item_key ,launcher):
    
        if input:
            return input

        app = launcher['application']
        appPath = FileNameFactory.create(app)
    
        extensions = emudata_get_program_extensions(appPath.getBase())
        return extensions
    
    def _get_arguments_from_application_path(self, input, item_key, launcher):
    
        if input:
            return input

        app = launcher['application']
        appPath = FileNameFactory.create(app)
    
        default_arguments = emudata_get_program_arguments(appPath.getBase())
        return default_arguments

    def _get_value_from_rompath(self, input, item_key, launcher):

        if input:
            return input

        romPath = launcher['rompath']
        return romPath

    def _get_value_from_assetpath(self, input, item_key, launcher):

        if input:
            return input

        romPath = FileNameFactory.create(launcher['assets_path'])
        romPath = romPath.pjoin('games')

        return romPath.getOriginalPath()
    
class ApplicationLauncher(Launcher):
    
    def __init__(self, settings, executorFactory, launcher):
        
        toggle_window =  launcher['toggle_window'] if 'toggle_window' in launcher else False
        super(ApplicationLauncher, self).__init__(launcher, settings, executorFactory, toggle_window)
        
    def launch(self):

        self.title              = self.launcher['m_name']
        self.application        = FileNameFactory.create(self.launcher['application'])
        self.arguments          = self.launcher['args']       
        
        # --- Check for errors and abort if errors found ---
        if not self.application.exists():
            log_error('Launching app not found "{0}"'.format(self.application.getPath()))
            kodi_notify_warn('App {0} not found.'.format(self.application.getOriginalPath()))
            return
        
        # ~~~ Argument substitution ~~~
        log_info('ApplicationLauncher() raw arguments   "{0}"'.format(self.arguments))
        self.arguments = self.arguments.replace('$apppath%' , self.application.getDir())
        log_info('ApplicationLauncher() final arguments "{0}"'.format(self.arguments))

        super(ApplicationLauncher, self).launch()
        pass

    def supports_launching_roms(self):
        return False
    
    def get_launcher_type(self):
        return LAUNCHER_STANDALONE
    
    def get_launcher_type_name(self):        
        return "Standalone launcher"
     
    # todo: move roms_dir to factory and inject through constructor for rom launchers only
    # categories should come from some kind of categoriesrepository
    def change_name(self, new_name, categories, roms_dir):
        if new_name == '': 
            return False
        
        old_launcher_name = self.get_name()
        new_launcher_name = new_name.rstrip()

        log_debug('launcher.change_name() Changing name: old_launcher_name "{0}"'.format(old_launcher_name))
        log_debug('launcher.change_name() Changing name: new_launcher_name "{0}"'.format(new_launcher_name))
        
        if old_launcher_name == new_launcher_name:
            return False
        
        self.launcher['m_name'] = new_launcher_name
        return True
    
    def change_arguments(self, args):
        self.launcher['args'] = args
        
    def get_args(self):
        return self.launcher['args']
    
    def get_additional_argument(self, index):
        args = self.get_all_additional_arguments()
        return args[index]

    def get_all_additional_arguments(self):
        return self.launcher['args_extra']

    def add_additional_argument(self, arg):

        if not self.launcher['args_extra']:
            self.launcher['args_extra'] = []

        self.launcher['args_extra'].append(arg)
        log_debug('launcher.add_additional_argument() Appending extra_args to launcher {0}'.format(self.get_id()))
        
    def set_additional_argument(self, index, arg):
        if not self.launcher['args_extra']:
            self.launcher['args_extra'] = []

        self.launcher['args_extra'][index] = arg
        log_debug('launcher.set_additional_argument() Edited args_extra[{0}] to "{1}"'.format(index, self.launcher['args_extra'][index]))

    def remove_additional_argument(self, index):
        del self.launcher['args_extra'][index]
        log_debug("launcher.remove_additional_argument() Deleted launcher['args_extra'][{0}]".format(index))
        
    def get_edit_options(self):

        category_name = 'ToDo'
        #if self.launchers[launcherID]['categoryID'] == VCATEGORY_ADDONROOT_ID:
        #    category_name = 'Addon root (no category)'
        #else:
        #    category_name = self.categories[self.launchers[launcherID]['categoryID']]['m_name']
        options = OrderedDict()
        options['EDIT_METADATA']      = 'Edit Metadata ...'
        options['EDIT_ASSETS']        = 'Edit Assets/Artwork ...'
        options['SET_DEFAULT_ASSETS'] = 'Choose default Assets/Artwork ...'
        options['CHANGE_CATEGORY']    = 'Change Category: {0}'.format(category_name)
        options['LAUNCHER_STATUS']    = 'Launcher status: {0}'.format(self.get_state())
        options['ADVANCED_MODS']      = 'Advanced Modifications ...'
        options['EXPORT_LAUNCHER']    = 'Export Launcher XML configuration ...'
        options['DELETE_LAUNCHER']    = 'Delete Launcher'

        return options

    def get_advanced_modification_options(self):
        
        toggle_window_str = 'ON' if self.launcher['toggle_window'] else 'OFF'
        non_blocking_str  = 'ON' if self.launcher['non_blocking'] else 'OFF'

        options = super(ApplicationLauncher, self).get_advanced_modification_options()
        options['MODIFY_ARGS']          = "Modify Arguments: '{0}'".format(self.launcher['args'])
        options['ADDITIONAL_ARGS']      = "Modify aditional arguments ..."
        options['TOGGLE_WINDOWED']      = "Toggle Kodi into windowed mode (now {0})".format(toggle_window_str)
        options['TOGGLE_NONBLOCKING']   = "Non-blocking launcher (now {0})".format(non_blocking_str)

        return options

    #
    # Creates a new launcher using a wizard of dialogs.
    #
    def _get_builder_wizard(self, wizard):
        
        wizard = FileBrowseWizardDialog('application', 'Select the launcher application', 1, self._get_appbrowser_filter, wizard)
        wizard = DummyWizardDialog('args', '', wizard)
        wizard = KeyboardWizardDialog('args', 'Application arguments', wizard)
        wizard = DummyWizardDialog('m_name', '', wizard, self._get_title_from_app_path)
        wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, self._get_title_from_app_path)
        wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
            
        return wizard

class KodiLauncher(Launcher):
    
    def __init__(self, settings, executorFactory, launcher):
        
        toggle_window =  launcher['toggle_window'] if 'toggle_window' in launcher else False
        super(KodiLauncher, self).__init__(launcher, settings, executorFactory, toggle_window)
        
    def launch(self):

        self.title              = self.launcher['m_name']
        self.application        = FileNameFactory.create('xbmc.exe')
        self.arguments          = self.launcher['application']       
        
        super(KodiLauncher, self).launch()
        pass
    
    def supports_launching_roms(self):
        return False
    
    def get_launcher_type(self):
        return LAUNCHER_FAVOURITES
    
    def get_launcher_type_name(self):        
        return "Kodi favourite launcher"
    
    def get_edit_options(self):

        category_name = 'ToDo'
        #if self.launchers[launcherID]['categoryID'] == VCATEGORY_ADDONROOT_ID:
        #    category_name = 'Addon root (no category)'
        #else:
        #    category_name = self.categories[self.launchers[launcherID]['categoryID']]['m_name']
        options = OrderedDict()
        options['EDIT_METADATA']      = 'Edit Metadata ...'
        options['EDIT_ASSETS']        = 'Edit Assets/Artwork ...'
        options['SET_DEFAULT_ASSETS'] = 'Choose default Assets/Artwork ...'
        options['CHANGE_CATEGORY']    = 'Change Category: {0}'.format(category_name)
        options['LAUNCHER_STATUS']    = 'Launcher status: {0}'.format(self.get_state())
        options['ADVANCED_MODS']      = 'Advanced Modifications ...'
        options['EXPORT_LAUNCHER']    = 'Export Launcher XML configuration ...'
        options['DELETE_LAUNCHER']    = 'Delete Launcher'

        return options
    
    
    def get_advanced_modification_options(self):
        
        toggle_window_str = 'ON' if self.launcher['toggle_window'] else 'OFF'
        non_blocking_str  = 'ON' if self.launcher['non_blocking'] else 'OFF'

        options = super(KodiLauncher, self).get_advanced_modification_options()
        options['TOGGLE_WINDOWED']      = "Toggle Kodi into windowed mode (now {0})".format(toggle_window_str)
        options['TOGGLE_NONBLOCKING']   = "Non-blocking launcher (now {0})".format(non_blocking_str)

        return options

    def change_name(self, new_name, categories, roms_dir):
        if new_name == '': 
            return False
        
        old_launcher_name = self.get_name()
        new_launcher_name = new_name.rstrip()

        log_debug('launcher.change_name() Changing name: old_launcher_name "{0}"'.format(old_launcher_name))
        log_debug('launcher.change_name() Changing name: new_launcher_name "{0}"'.format(new_launcher_name))
        
        if old_launcher_name == new_launcher_name:
            return False
        
        self.launcher['m_name'] = new_launcher_name
        return True

    #
    # Creates a new launcher using a wizard of dialogs.
    #
    def _get_builder_wizard(self, wizard):
        
        wizard = DictionarySelectionWizardDialog('application', 'Select the favourite', self._get_kodi_favourites(), wizard)
        wizard = DummyWizardDialog('s_icon', '', wizard, self._get_icon_from_selected_favourite)
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

class StandardRomLauncher(RomLauncher):
       
    def get_launcher_type(self):
        return LAUNCHER_ROM
    
    def get_launcher_type_name(self):        
        return "ROM launcher"   
    
    def change_arguments(self, args):
        self.launcher['args'] = args
        
    def get_args(self):
        return self.launcher['args']
    
    def get_additional_argument(self, index):
        args = self.get_all_additional_arguments()
        return args[index]

    def get_all_additional_arguments(self):
        return self.launcher['args_extra']

    def add_additional_argument(self, arg):

        if not self.launcher['args_extra']:
            self.launcher['args_extra'] = []

        self.launcher['args_extra'].append(arg)
        log_debug('launcher.add_additional_argument() Appending extra_args to launcher {0}'.format(self.get_id()))
        
    def set_additional_argument(self, index, arg):
        if not self.launcher['args_extra']:
            self.launcher['args_extra'] = []

        self.launcher['args_extra'][index] = arg
        log_debug('launcher.set_additional_argument() Edited args_extra[{0}] to "{1}"'.format(index, self.launcher['args_extra'][index]))

    def remove_additional_argument(self, index):
        del self.launcher['args_extra'][index]
        log_debug("launcher.remove_additional_argument() Deleted launcher['args_extra'][{0}]".format(index))

    def get_rom_extensions(self):
        return self.launcher['romext']

    def change_rom_extensions(self, ext):
        self.launcher['romext'] = ext
       
    def get_advanced_modification_options(self):
        
        toggle_window_str = 'ON' if self.launcher['toggle_window'] else 'OFF'
        non_blocking_str  = 'ON' if self.launcher['non_blocking'] else 'OFF'
        multidisc_str     = 'ON' if self.launcher['multidisc'] else 'OFF'
        
        options = super(StandardRomLauncher, self).get_advanced_modification_options()
        options['MODIFY_ARGS'] = "Modify Arguments: '{0}'".format(self.launcher['args'])
        options['ADDITIONAL_ARGS'] = "Modify aditional arguments ..."
        options['CHANGE_ROMPATH'] = "Change ROM path: '{0}'".format(self.launcher['rompath'])
        options['CHANGE_ROMEXT'] = "Modify ROM extensions: '{0}'".format(self.launcher['romext'])
        options['TOGGLE_WINDOWED'] = "Toggle Kodi into windowed mode (now {0})".format(toggle_window_str)
        options['TOGGLE_NONBLOCKING'] = "Non-blocking launcher (now {0})".format(non_blocking_str)
        options['TOGGLE_MULTIDISC'] = "Multidisc ROM support (now {0})".format(multidisc_str)
        
        return options

    def _selectApplicationToUse(self):

        if self.rom['altapp']:
            log_info('StandardRomLauncher() Using ROM altapp')
            self.application = FileNameFactory.create(self.rom['altapp'])
        else:
            self.application = FileNameFactory.create(self.launcher['application'])

    def _selectArgumentsToUse(self):

        if self.rom['altarg']:
            log_info('StandardRomLauncher() Using ROM altarg')
            self.arguments = self.rom['altarg']
        elif self.launcher['args_extra']:
             # >> Ask user what arguments to launch application
            log_info('StandardRomLauncher() Using Launcher args_extra')
            launcher_args = self.launcher['args']
            arg_list = [self.launcher_args] + self.launcher['args_extra']
            dialog = xbmcgui.Dialog()
            dselect_ret = dialog.select('Select launcher arguments', arg_list)
            
            if dselect_ret < 0: 
                return
            
            log_info('StandardRomLauncher() User chose args index {0} ({1})'.format(dselect_ret, arg_list[dselect_ret]))
            self.arguments = arg_list[dselect_ret]
        else:
            self.arguments = self.launcher['args']

    def _selectRomFileToUse(self):
        
        if not 'disks' in self.rom or not self.rom['disks']:
            return FileNameFactory.create(self.rom['filename'])
                
        log_info('StandardRomLauncher() Multidisc ROM set detected')
        dialog = xbmcgui.Dialog()
        dselect_ret = dialog.select('Select ROM to launch in multidisc set', self.rom['disks'])
        if dselect_ret < 0:
           return

        selected_rom_base = self.rom['disks'][dselect_ret]
        log_info('StandardRomLauncher() Selected ROM "{0}"'.format(selected_rom_base))

        ROM_temp = FileNameFactory.create(self.rom['filename'])
        ROM_dir = FileNameFactory.create(ROM_temp.getDir())
        ROMFileName = ROM_dir.pjoin(selected_rom_base)

        return ROMFileName

    #
    # Creates a new launcher using a wizard of dialogs.
    #
    def _get_builder_wizard(self, wizard):
        
        wizard = FileBrowseWizardDialog('application', 'Select the launcher application', 1, self._get_appbrowser_filter, wizard) 
        wizard = FileBrowseWizardDialog('rompath', 'Select the ROMs path', 0, '', wizard)
        wizard = DummyWizardDialog('romext', '', wizard, self._get_extensions_from_app_path)
        wizard = KeyboardWizardDialog('romext','Set files extensions, use "|" as separator. (e.g lnk|cbr)', wizard)
        wizard = DummyWizardDialog('args', '', wizard, self._get_arguments_from_application_path)
        wizard = KeyboardWizardDialog('args', 'Application arguments', wizard)
        wizard = DummyWizardDialog('m_name', '', wizard, self._get_title_from_app_path)
        wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, self._get_title_from_app_path)
        wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
        wizard = DummyWizardDialog('assets_path', '', wizard, self._get_value_from_rompath)
        wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard) 
            
        return wizard
 
class LnkLauncher(StandardRomLauncher):
    
    def get_launcher_type(self):
        return LAUNCHER_LNK
    
    def get_launcher_type_name(self):        
        return "LNK launcher"
           
    def get_advanced_modification_options(self):
        
        options = super(LnkLauncher, self).get_advanced_modification_options()
        del options['CHANGE_ROMEXT']
        
        return options

    #
    # Creates a new launcher using a wizard of dialogs.
    #
    def _get_builder_wizard(self, wizard):
        
        wizard = DummyWizardDialog('application', LNK_LAUNCHER_APP_NAME, wizard)
        wizard = FileBrowseWizardDialog('rompath', 'Select the LNKs path', 0, '', wizard)
        wizard = DummyWizardDialog('romext', 'lnk', wizard)
        wizard = DummyWizardDialog('args', '%rom%', wizard)
        wizard = DummyWizardDialog('m_name', '', wizard, self._get_title_from_app_path)
        wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, self._get_title_from_app_path)
        wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
        wizard = DummyWizardDialog('assets_path', '', wizard, self._get_value_from_rompath)
        wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard) 
            
        return wizard

# --- Execute Kodi Retroplayer if launcher configured to do so ---
# See https://github.com/Wintermute0110/plugin.program.advanced.emulator.launcher/issues/33
# See https://forum.kodi.tv/showthread.php?tid=295463&pid=2620489#pid2620489
class RetroplayerLauncher(RomLauncher):

    def launch(self):
        log_info('RetroplayerLauncher() Executing ROM with Kodi Retroplayer ...')
                
        self.title = self.rom['m_name']
        self._selectApplicationToUse()

        ROMFileName = self._selectRomFileToUse()
                
        # >> Create listitem object
        label_str = ROMFileName.getBase()
        listitem = xbmcgui.ListItem(label = label_str, label2 = label_str)
        # >> Listitem metadata
        # >> How to fill gameclient = string (game.libretro.fceumm) ???
        genre_list = list(rom['m_genre'])
        listitem.setInfo('game', {'title'    : label_str,     'platform'  : 'Test platform',
                                    'genres'   : genre_list,    'developer' : rom['m_developer'],
                                    'overview' : rom['m_plot'], 'year'      : rom['m_year'] })
        log_info('RetroplayerLauncher() application.getOriginalPath() "{0}"'.format(application.getOriginalPath()))
        log_info('RetroplayerLauncher() ROMFileName.getOriginalPath() "{0}"'.format(ROMFileName.getOriginalPath()))
        log_info('RetroplayerLauncher() label_str                     "{0}"'.format(label_str))

        # --- User notification ---
        if self.settings['display_launcher_notify']:
            kodi_notify('Launching "{0}" with Retroplayer'.format(self.title))

        log_verb('RetroplayerLauncher() Calling xbmc.Player().play() ...')
        xbmc.Player().play(ROMFileName.getOriginalPath(), listitem)
        log_verb('RetroplayerLauncher() Calling xbmc.Player().play() returned. Leaving function.')
        pass
    
    def get_launcher_type(self):
        return LAUNCHER_RETROPLAYER
    
    def get_launcher_type_name(self):        
        return "Retroplayer launcher"
    
    def get_advanced_modification_options(self):
        
        toggle_window_str = 'ON' if self.launcher['toggle_window'] else 'OFF'
        non_blocking_str  = 'ON' if self.launcher['non_blocking'] else 'OFF'
        multidisc_str     = 'ON' if self.launcher['multidisc'] else 'OFF'
        
        options = super(StandardRomLauncher, self).get_advanced_modification_options()
        options['MODIFY_ARGS'] = "Modify Arguments: '{0}'".format(self.launcher['args'])
        options['ADDITIONAL_ARGS'] = "Modify aditional arguments ..."
        options['CHANGE_ROMPATH'] = "Change ROM path: '{0}'".format(self.launcher['rompath'])
        options['CHANGE_ROMEXT'] = "Modify ROM extensions: '{0}'".format(self.launcher['romext'])
        options['TOGGLE_WINDOWED'] = "Toggle Kodi into windowed mode (now {0})".format(toggle_window_str)
        options['TOGGLE_NONBLOCKING'] = "Non-blocking launcher (now {0})".format(non_blocking_str)
        options['TOGGLE_MULTIDISC'] = "Multidisc ROM support (now {0})".format(multidisc_str)
        
        return options

    #
    # Creates a new launcher using a wizard of dialogs.
    #
    def _get_builder_wizard(self, wizard):
        
        wizard = DummyWizardDialog('application', RETROPLAYER_LAUNCHER_APP_NAME, wizard)
        wizard = FileBrowseWizardDialog('rompath', 'Select the ROMs path', 0, '', wizard)
        wizard = DummyWizardDialog('romext', '', wizard, self._get_extensions_from_app_path)
        wizard = KeyboardWizardDialog('romext','Set files extensions, use "|" as separator. (e.g lnk|cbr)', wizard)
        wizard = DummyWizardDialog('args', '%rom%', wizard)
        wizard = DummyWizardDialog('m_name', '', wizard, self._get_title_from_app_path)
        wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, self._get_title_from_app_path)
        wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
        wizard = DummyWizardDialog('assets_path', '', wizard, self._get_value_from_rompath)
        wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard) 
            
        return wizard

#
# Read RetroarchLauncher.md
#
class RetroarchLauncher(RomLauncher):
        
    def _selectApplicationToUse(self):
        
        if is_windows():
            self.application = FileNameFactory.create(self.launcher['application'])
            self.application = self.application.append('retroarch.exe')  
            return

        if is_android():
            self.application = FileNameFactory.create('/system/bin/am')
            return

        #todo other os
        self.application = ''
        pass

    def _selectArgumentsToUse(self):
        
        if is_windows() or is_linux():            
            self.arguments =  '-L "$retro_core$" '
            self.arguments += '-c "$retro_config$" '
            self.arguments += '"$rom$"'
            self.arguments += self.launcher['args']
            return

        if is_android():

            self.arguments =  'start --user 0 -a android.intent.action.MAIN -c android.intent.category.LAUNCHER '
            self.arguments += '-n com.retroarch/.browser.retroactivity.RetroActivityFuture '
            self.arguments += '-e ROM \'$rom$\' '
            self.arguments += '-e LIBRETRO $retro_core$ '
            self.arguments += '-e CONFIGFILE $retro_config$ '
            self.arguments += self.launcher['args']
            return

        #todo other os
        pass 

    def get_launcher_type(self):
        return LAUNCHER_RETROARCH
    
    def get_launcher_type_name(self):        
        return "Retroarch launcher"

    #
    # Creates a new launcher using a wizard of dialogs.
    #
    def _get_builder_wizard(self, wizard):
                
        wizard = DummyWizardDialog('application', self._get_retroarch_app_folder(self.settings), wizard)
        wizard = FileBrowseWizardDialog('application', 'Select the Retroarch path', 0, '', wizard) 
        wizard = DictionarySelectionWizardDialog('retro_config', 'Select the configuration', self._get_available_retroarch_configurations, wizard)
        wizard = FileBrowseWizardDialog('retro_config', 'Select the configuration', 0, '', wizard, None, self._user_selected_custom_browsing) 
        wizard = DictionarySelectionWizardDialog('retro_core_info', 'Select the core', self._get_available_retroarch_cores, wizard, self._load_selected_core_info)
        wizard = KeyboardWizardDialog('retro_core_info', 'Enter path to core file', wizard, self._load_selected_core_info, self._user_selected_custom_browsing)
        wizard = FileBrowseWizardDialog('rompath', 'Select the ROMs path', 0, '', wizard) 
        wizard = KeyboardWizardDialog('romext','Set files extensions, use "|" as separator. (e.g nes|zip)', wizard)
        wizard = DummyWizardDialog('args', self._get_default_retroarch_arguments(), wizard)
        wizard = KeyboardWizardDialog('args', 'Extra application arguments', wizard)
        wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, self._get_title_from_app_path)
        wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
        wizard = DummyWizardDialog('assets_path', '', wizard, self._get_value_from_rompath)
        wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard) 
                    
        return wizard

    def _get_retroarch_app_folder(self, settings):
    
        retroarch_folder = FileNameFactory.create(settings['io_retroarch_sys_dir'])      
    
        if retroarch_folder.exists():
            return retroarch_folder.getOriginalPath()

        if is_android():
        
            android_retroarch_folders = [
                '/storage/emulated/0/Android/data/com.retroarch/',
                '/data/data/com.retroarch/',
                '/storage/sdcard0/Android/data/com.retroarch/',
                '/data/user/0/com.retroarch']

        
            for retroach_folder_path in android_retroarch_folders:
                retroarch_folder = FileNameFactory.create(retroach_folder_path)
                if retroarch_folder.exists():
                    return retroarch_folder.getOriginalPath()

        return '/'

    def _get_available_retroarch_configurations(self, item_key, launcher):
    
        configs = OrderedDict()
        configs['BROWSE'] = 'Browse for configuration'

        retroarch_folders = []
        retroarch_folders.append(FileNameFactory.create(launcher['application']))

        if is_android():
            retroarch_folders.append(FileNameFactory.create('/storage/emulated/0/Android/data/com.retroarch/'))
            retroarch_folders.append(FileNameFactory.create('/data/data/com.retroarch/'))
            retroarch_folders.append(FileNameFactory.create('/storage/sdcard0/Android/data/com.retroarch/'))
            retroarch_folders.append(FileNameFactory.create('/data/user/0/com.retroarch/'))
        
        for retroarch_folder in retroarch_folders:
            log_debug("get_available_retroarch_configurations() scanning path '{0}'".format(retroarch_folder.getOriginalPath()))
            files = retroarch_folder.recursiveScanFilesInPathAsFileNameObjects('*.cfg')
        
            if len(files) < 1:
                continue

            for file in files:
                log_debug("get_available_retroarch_configurations() adding config file '{0}'".format(file.getOriginalPath()))
                
                configs[file.getOriginalPath()] = file.getBase_noext()

            return configs

        return configs

    def _get_available_retroarch_cores(self, item_key, launcher):
    
        cores = OrderedDict()
        cores['BROWSE'] = 'Manual enter path to core'
        cores_ext = '*.*'

        if is_windows():
            cores_ext = '*.dll'
        else:
            cores_ext = '*.so'

        config_file     = FileNameFactory.create(launcher['retro_config'])
        parent_dir      = config_file.getDirAsFileName()
        configuration   = config_file.readPropertyFile()    
        info_folder     = self._create_path_from_retroarch_setting(configuration['libretro_info_path'], parent_dir)
        cores_folder    = self._create_path_from_retroarch_setting(configuration['libretro_directory'], parent_dir)
        
        log_debug("get_available_retroarch_cores() scanning path '{0}'".format(cores_folder.getOriginalPath()))

        if not info_folder.exists():
            log_warning('Retroarch info folder not found {}'.format(info_folder.getOriginalPath()))
            return cores
    
        if not cores_folder.exists():
            log_warning('Retroarch cores folder not found {}'.format(cores_folder.getOriginalPath()))
            return cores

        files = cores_folder.scanFilesInPathAsFileNameObjects(cores_ext)
        for file in files:
                
            log_debug("get_available_retroarch_cores() adding core '{0}'".format(file.getOriginalPath()))    
            info_file = self._switch_core_to_info_file(file, info_folder)

            if not info_file.exists():
                log_warning('get_available_retroarch_cores() Cannot find "{}". Skipping core "{}"'.format(info_file.getOriginalPath(), file.getBase()))
                continue

            log_debug("get_available_retroarch_cores() using info '{0}'".format(info_file.getOriginalPath()))    
            core_info = info_file.readPropertyFile()
            cores[info_file.getOriginalPath()] = core_info['display_name']

        return cores

    def _load_selected_core_info(self, input, item_key, launcher):

        if input == 'BROWSE':
            return input
    
        if is_windows():
            cores_ext = 'dll'
        else:
            cores_ext = 'so'

        if input.endswith(cores_ext):
            core_file = FileNameFactory.create(input)
            launcher['retro_core']  = core_file.getOriginalPath()
            return input

        config_file     = FileNameFactory.create(launcher['retro_config'])
        parent_dir      = config_file.getDirAsFileName()
        configuration   = config_file.readPropertyFile()    
        cores_folder    = self._create_path_from_retroarch_setting(configuration['libretro_directory'], parent_dir)
        info_file       = FileNameFactory.create(input)
        
        if not cores_folder.exists():
            log_warning('Retroarch cores folder not found {}'.format(cores_folder.getOriginalPath()))
            kodi_notify_error('Retroarch cores folder not found {}'.format(cores_folder.getOriginalPath()))
            return ''

        core_file = self._switch_info_to_core_file(info_file, cores_folder, cores_ext)
        core_info = info_file.readPropertyFile()

        launcher[item_key]      = info_file.getOriginalPath()
        launcher['retro_core']  = core_file.getOriginalPath()
        launcher['romext']      = core_info['supported_extensions']
        launcher['platform']    = core_info['systemname']
        launcher['m_developer'] = core_info['manufacturer']
        launcher['m_name']      = core_info['systemname']

        return input

    def _get_default_retroarch_arguments(self):

        args = ''
        if is_android():
            args += '-e IME com.android.inputmethod.latin/.LatinIME -e REFRESH 60'

        return args
    
    def _create_path_from_retroarch_setting(self, path_from_setting, parent_dir):

        if not path_from_setting.endswith('\\') and not path_from_setting.endswith('/'):
            path_from_setting = path_from_setting + parent_dir.path_separator()

        if path_from_setting.startswith(':\\'):
            path_from_setting = path_from_setting[2:]
            return parent_dir.pjoin(path_from_setting)
        else:
            folder = FileNameFactory.create(path_from_setting)
            if '/data/user/0/' in folder.getOriginalPath():
                alternative_folder = foldexr.getOriginalPath()
                alternative_folder = alternative_folder.replace('/data/user/0/', '/data/data/')
                folder = FileNameFactory.create(alternative_folder)

            return folder

    def _switch_core_to_info_file(self, core_file, info_folder):
    
        info_file = core_file.switchExtension('info')
   
        if is_android():
            info_file = info_folder.pjoin(info_file.getBase().replace('_android.', '.'))
        else:
            info_file = info_folder.pjoin(info_file.getBase())

        return info_file

    def _switch_info_to_core_file(self, info_file, cores_folder, cores_ext):
    
        core_file = info_file.switchExtension(cores_ext)

        if is_android():
            core_file = cores_folder.pjoin(core_file.getBase().replace('.', '_android.'))
        else:
            core_file = cores_folder.pjoin(core_file.getBase())

        return core_file
    
 #
 # Launcher to use with a local Steam application and account.
 #   
class SteamLauncher(RomLauncher):

    def __init__(self, settings, executorFactory, statsStrategy, launcher, rom):

        self.rom = rom
        self.categoryID = ''
        self.statsStrategy = statsStrategy

        non_blocking_flag = launcher['non_blocking'] if 'non_blocking' in launcher else False
        toggle_window =  launcher['toggle_window'] if 'toggle_window' in launcher else False
        super(SteamLauncher, self).__init__(launcher, settings, executorFactory, toggle_window, non_blocking_flag)
        
    def launch(self):
        
        self.title  = self.rom['m_name']
        
        url = 'steam://rungameid/'

        self.application = FileNameFactory.create('steam://rungameid/')
        self.arguments = str(self.rom['steamid'])

        log_info('SteamLauncher() ROM ID {0}: @{1}"'.format(self.rom['steamid'], self.rom['m_name']))
        self.statsStrategy.updateRecentlyPlayedRom(self.rom)       
        
        super(SteamLauncher, self).launch()
        pass    

    def get_launcher_type(self):
        return LAUNCHER_STEAM
    
    def get_launcher_type_name(self):        
        return "Steam launcher"
    
    def _get_builder_wizard(self, wizard):
        
        wizard = DummyWizardDialog('application', 'Steam', wizard)
        wizard = KeyboardWizardDialog('steamid','Steam ID', wizard)
        wizard = DummyWizardDialog('m_name', 'Steam', wizard)
        wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, self._get_title_from_app_path)
        wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
        wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard)
        wizard = DummyWizardDialog('rompath', '', wizard, self._get_value_from_assetpath)         
                    
        return wizard
    
    def _get_value_from_assetpath(self, input, item_key, launcher):

        if input:
            return input

        romPath = FileNameFactory.create(launcher['assets_path'])
        romPath = romPath.pjoin('games')

        return romPath.getOriginalPath()
 
 #
 # Launcher to use with Nvidia Gamestream servers.
 #   
class NvidiaGameStreamLauncher(RomLauncher):

    def __init__(self, settings, executorFactory, statsStrategy, escape_romfile, launcher, rom):

        super(NvidiaGameStreamLauncher, self).__init__(settings, executorFactory, statsStrategy, escape_romfile, launcher, rom)
        self.validate_if_rom_exists = False

    def _selectApplicationToUse(self):
        
        streamClient = self.launcher['application']
        
        # java application selected (moonlight-pc)
        if '.jar' in streamClient:
            self.application = FileNameFactory.create(os.getenv("JAVA_HOME"))
            if is_windows():
                self.application = self.application.pjoin('bin\\java.exe')
            else:
                self.application = self.application.pjoin('bin/java')

            return

        if is_windows():
            self.application = FileNameFactory.create(streamClient)
            return

        if is_android():
            self.application = FileNameFactory.create('/system/bin/am')
            return

        pass

    def _selectArgumentsToUse(self):
        
        streamClient = self.launcher['application']
            
        # java application selected (moonlight-pc)
        if '.jar' in streamClient:
            self.arguments =  '-jar "$application$" '
            self.arguments += '-host $server$ '
            self.arguments += '-fs '
            self.arguments += '-app "$gamestream_name$" '
            self.arguments += self.launcher['args']
            return

        if is_android():

            if streamClient == 'NVIDIA':
                self.arguments =  'start --user 0 -a android.intent.action.VIEW '
                self.arguments += '-n com.nvidia.tegrazone3/com.nvidia.grid.UnifiedLaunchActivity '
                self.arguments += '-d nvidia://stream/target/2/$streamid$'
                return

            if streamClient == 'MOONLIGHT':
                self.arguments =  'start --user 0 -a android.intent.action.MAIN '
                self.arguments += '-c android.intent.category.LAUNCHER ' 
                self.arguments += '-n com.limelight/.Game '
                self.arguments += '-e Host $server$ '
                self.arguments += '-e AppId $streamid$ '
                self.arguments += '-e AppName "$gamestream_name$" '
                self.arguments += '-e PcName "$server_hostname$" '
                self.arguments += '-e UUID $server_id$ '
                self.arguments += '-e UniqueId {} '.format(misc_generate_random_SID())

                return
        
        # else
        self.arguments = self.launcher['args']
        pass 
  
    def get_launcher_type(self):
        return LAUNCHER_NVGAMESTREAM
    
    def get_launcher_type_name(self):        
        return "Nvidia GameStream launcher"

    #
    # Creates a new launcher using a wizard of dialogs.
    #
    def _get_builder_wizard(self, wizard):
        
        info_txt = 'To pair with your Geforce Experience Computer we need to make use of valid certificates. '
        info_txt += 'Unfortunately at this moment we cannot create these certificates directly from within Kodi.\n'
        info_txt += 'Please read the wiki for details how to create them before you go further.'

        wizard = FormattedMessageWizardDialog('certificates_path', 'Pairing with Gamestream PC', info_txt, wizard)
        wizard = DictionarySelectionWizardDialog('application', 'Select the client', {'NVIDIA': 'Nvidia', 'MOONLIGHT': 'Moonlight'}, wizard, self._check_if_selected_gamestream_client_exists, lambda pk,p: is_android())
        wizard = DictionarySelectionWizardDialog('application', 'Select the client', {'JAVA': 'Moonlight-PC (java)', 'EXE': 'Moonlight-Chrome (not supported yet)'}, wizard, None, lambda pk,p: not is_android())
        wizard = FileBrowseWizardDialog('application', 'Select the Gamestream client jar', 1, self._get_appbrowser_filter, wizard, None, lambda pk,p: not is_android())
        wizard = KeyboardWizardDialog('args', 'Additional arguments', wizard, None, lambda pk,p: not is_android())
        wizard = InputWizardDialog('server', 'Gamestream Server', xbmcgui.INPUT_IPADDRESS, wizard, self._validate_gamestream_server_connection)
        wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, self._get_title_from_app_path)
        wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard)
        wizard = DummyWizardDialog('rompath', '', wizard, self._get_value_from_assetpath)   
        # Pairing with pin code will be postponed untill crypto and certificate support in kodi
        # wizard = DummyWizardDialog('pincode', None, wizard, generatePairPinCode)
        wizard = DummyWizardDialog('certificates_path', None, wizard, self._try_to_resolve_path_to_nvidia_certificates)
        wizard = FileBrowseWizardDialog('certificates_path', 'Select the path with valid certificates', 0, '', wizard, self._validate_nvidia_certificates) 
        wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)       
                    
        return wizard

    def _generatePairPinCode(self, input, item_key, launcher):
    
        return gamestreamServer(None, None).generatePincode()

    def _check_if_selected_gamestream_client_exists(self, input, item_key, launcher):

        if input == 'NVIDIA':
            nvidiaDataFolder = FileNameFactory.create('/data/data/com.nvidia.tegrazone3/')
            nvidiaAppFolder = FileNameFactory.create('/storage/emulated/0/Android/data/com.nvidia.tegrazone3/')
            if not nvidiaAppFolder.exists() and not nvidiaDataFolder.exists():
                kodi_notify_warn('Could not find Nvidia Gamestream client. Make sure it\'s installed.')

        if input == 'MOONLIGHT':
            moonlightDataFolder = FileNameFactory.create('/data/data/com.limelight/')
            moonlightAppFolder = FileNameFactory.create('/storage/emulated/0/Android/data/com.limelight/')
            if not moonlightAppFolder.exists() and not moonlightDataFolder.exists():
                kodi_notify_warn('Could not find Moonlight Gamestream client. Make sure it\'s installed.')
        
        return input

    def _try_to_resolve_path_to_nvidia_certificates(self, input, item_key, launcher):
    
        path = GameStreamServer.try_to_resolve_path_to_nvidia_certificates()
        return path

    def _validate_nvidia_certificates(self, input, item_key, launcher):

        certificates_path = FileNameFactory.create(input)
        gs = GameStreamServer(input, certificates_path)
        if not gs.validate_certificates():
            kodi_notify_warn('Could not find certificates to validate. Make sure you already paired with the server with the Shield or Moonlight applications.')

        return certificates_path.getOriginalPath()

    def _validate_gamestream_server_connection(self, input, item_key, launcher):

        gs = GameStreamServer(input, None)
        if not gs.connect():
            kodi_notify_warn('Could not connect to gamestream server')

        launcher['server_id'] = gs.get_uniqueid()
        launcher['server_hostname'] = gs.get_hostname()

        log_debug('validate_gamestream_server_connection() Found correct gamestream server with id "{}" and hostname "{}"'.format(launcher['server_id'],launcher['server_hostname']))

        return input