# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Base launchers
#
# Copyright (c) 2016-2018 Wintermute0110 <wintermute0110@gmail.com>
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
from __future__ import division
import abc
import collections
import typing
import logging
import re 
import json

from os.path import expanduser
import uuid
import random
import binascii

# --- AEL packages ---
from resources.lib.utils import io, kodi, text
from resources.lib.executors import *
from resources.lib.constants import *

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# Abstract base class for launching anything that is supported.
# Implement classes that inherit this base class to support new ways of launching.
# -------------------------------------------------------------------------------------------------
class LauncherABC(object):
    __metaclass__ = abc.ABCMeta

    #
    # In an abstract class launcher_data is mandatory.
    #
    def __init__(self, executorFactory: ExecutorFactory):
        self.executorFactory = executorFactory
        self.application     = None
        self.arguments       = None
        self.title           = None

    # --------------------------------------------------------------------------------------------
    # Core methods
    # --------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def get_name(self): pass

    @abc.abstractmethod
    def get_launcher_type(self): pass

    # By default Launchers do not support ROMs. Redefine in child class if Launcher has ROMs.
    def supports_launching_roms(self): return False

    # By default Launchers do not PClone ROMs. Redefine in child class if necessary.
    def supports_parent_clone_roms(self): return False

    # --------------------------------------------------------------------------------------------
    # Launcher build wizard methods
    # --------------------------------------------------------------------------------------------
    #
    # Builds a new Launcher.
    # Leave category_id empty to add launcher to root folder.
    # Returns True if Launcher  was sucesfully built.
    # Returns False if Launcher was not built (user canceled the dialogs or some other
    # error happened).
    #
    def build(self, category):
        logger.debug('LauncherABC::build() Starting ...')

        # --- Call hook before wizard ---
        if not self._build_pre_wizard_hook(): return False

        # --- Launcher build code (ask user about launcher stuff) ---
        wizard = WizardDialog_Dummy(None, 'categoryID', category.get_id())
        wizard = WizardDialog_Dummy(wizard, 'type', self.get_launcher_type())
        # >> Call Child class wizard builder method
        wizard = self._builder_get_wizard(wizard)
        # >> Run wizard
        self.entity_data = wizard.runWizard(self.entity_data)
        if not self.entity_data: return False
        self.entity_data['timestamp_launcher'] = time.time()

        # --- Call hook after wizard ---
        if not self._build_post_wizard_hook(): return False

        return True

    #
    # Creates a new launcher using a wizard of dialogs.
    # Child concrete classes must implement this method.
    #
    @abc.abstractmethod
    def _builder_get_wizard(self, wizard): pass

    @abc.abstractmethod
    def _build_pre_wizard_hook(self): pass

    @abc.abstractmethod
    def _build_post_wizard_hook(self): pass

    def _builder_get_title_from_app_path(self, input, item_key, launcher):
        if input: return input
        appPath = FileName(launcher['application'])
        title = appPath.getBaseNoExt()
        title_formatted = title.replace('.' + title.split('.')[-1], '').replace('.', ' ')

        return title_formatted

    def _builder_get_appbrowser_filter(self, item_key, launcher):
        if item_key in launcher:
            application = launcher[item_key]
            if application == 'JAVA':
                return '.jar'

        return '.bat|.exe|.cmd|.lnk' if is_windows() else ''

    #
    # Wizard helper, when a user wants to set a custom value instead of the predefined list items.
    #
    def _builder_user_selected_custom_browsing(self, item_key, launcher):
        return launcher[item_key] == 'BROWSE'

    # --------------------------------------------------------------------------------------------
    # Launcher edit methods
    # --------------------------------------------------------------------------------------------
    #
    # Returns a dictionary of options to choose from with which you can edit or manage this
    # specific launcher in the "Edit Launcher" context menu.
    # Different launchers have a different may menu, hence this method is abstract.
    #
    @abc.abstractmethod
    def get_main_edit_options(self):
        pass

    #
    # Returns a dictionary of options to choose from with which you can edit the metadata
    # of a launcher.
    # All launchers have the same metadata so method is defined here.
    #
    def get_metadata_edit_options(self):
        logger.debug('LauncherABC::get_metadata_edit_options() Starting ...')
        plot_str = text_limit_string(self.entity_data['m_plot'], PLOT_STR_MAXSIZE)
        rating = self.get_rating() if self.get_rating() != -1 else 'not rated'
        NFO_FileName = fs_get_launcher_NFO_name(self.settings, self.entity_data)
        NFO_found_str = 'NFO found' if NFO_FileName.exists() else 'NFO not found'

        options = collections.OrderedDict()
        options['EDIT_METADATA_TITLE']       = "Edit Title: '{}'".format(self.get_name())
        options['EDIT_METADATA_PLATFORM']    = "Edit Platform: {}".format(self.entity_data['platform'])
        options['EDIT_METADATA_RELEASEYEAR'] = "Edit Release Year: '{}'".format(self.entity_data['m_year'])
        options['EDIT_METADATA_GENRE']       = "Edit Genre: '{}'".format(self.entity_data['m_genre'])
        options['EDIT_METADATA_DEVELOPER']   = "Edit Developer: '{}'".format(self.entity_data['m_developer'])
        options['EDIT_METADATA_RATING']      = "Edit Rating: '{}'".format(rating)
        options['EDIT_METADATA_PLOT']        = "Edit Plot: '{}'".format(plot_str)
        options['EDIT_METADATA_BOXSIZE']     = "Edit Box Size: '{}'".format(self.get_box_sizing())
        options['IMPORT_NFO_FILE']           = 'Import NFO file (default {})'.format(NFO_found_str)
        options['IMPORT_NFO_FILE_BROWSE']    = 'Import NFO file (browse NFO file) ...'
        options['SAVE_NFO_FILE']             = 'Save NFO file (default location)'

        return options

    #
    # get_advanced_modification_options() is custom for every concrete launcher class.
    #
    @abc.abstractmethod
    def get_advanced_modification_options(self): pass

    # ---------------------------------------------------------------------------------------------
    # Execution methods
    # ---------------------------------------------------------------------------------------------
    #
    # Launchs a ROM launcher or standalone launcher
    # For standalone launchers romext is the extension of the application (only used in Windoze)
    #
    @abc.abstractmethod
    def launch(self):
        logger.debug('LauncherABC::launch() Starting ...')

        # --- Create executor object ---
        if self.executorFactory is None:
            logger.error('LauncherABC::launch() self.executorFactory is None')
            logger.error('Cannot create an executor for {}'.format(self.application.getPath()))
            kodi.notify_error('LauncherABC::launch() self.executorFactory is None'
                              'This is a bug, please report it.')
            return
        executor = self.executorFactory.create(self.application)
        if executor is None:
            logger.error('Cannot create an executor for {}'.format(self.application.getPath()))
            kodi.notify_error('Cannot execute application')
            return

        logger.debug('Name        = "{}"'.format(self.title))
        logger.debug('Application = "{}"'.format(self.application.getPath()))
        logger.debug('Arguments   = "{}"'.format(self.arguments))
        logger.debug('Executor    = "{}"'.format(executor.__class__.__name__))

        # --- Execute app ---
        self._launch_pre_exec(self.title, self.is_in_windowed_mode())
        executor.execute(self.application, self.arguments, self.is_non_blocking())
        self._launch_post_exec(self.is_in_windowed_mode())

    #
    # These two functions do things like stopping music before lunch, toggling full screen, etc.
    # Variables set in this function:
    # self.kodi_was_playing      True if Kodi player was ON, False otherwise
    # self.kodi_audio_suspended  True if Kodi audio suspended before launching
    #
    def _launch_pre_exec(self, title, toggle_screen_flag):
        logger.debug('LauncherABC::_launch_pre_exec() Starting ...')

        # --- User notification ---
        if self.settings['display_launcher_notify']:
            kodi.notify('Launching {}'.format(title))

        # --- Stop/Pause Kodi mediaplayer if requested in settings ---
        self.kodi_was_playing = False
        # id="media_state_action" default="0" values="Stop|Pause|Let Play"
        media_state_action = self.settings['media_state_action']
        media_state_str = ['Stop', 'Pause', 'Let Play'][media_state_action]
        logger.debug('_launch_pre_exec() media_state_action is "{}" ({})'.format(media_state_str, media_state_action))
        if media_state_action == 0 and xbmc.Player().isPlaying():
            logger.debug('_launch_pre_exec() Calling xbmc.Player().stop()')
            xbmc.Player().stop()
            xbmc.sleep(100)
            self.kodi_was_playing = True
        elif media_state_action == 1 and xbmc.Player().isPlaying():
            logger.debug('_launch_pre_exec() Calling xbmc.Player().pause()')
            xbmc.Player().pause()
            xbmc.sleep(100)
            self.kodi_was_playing = True

        # --- Force audio suspend if requested in "Settings" --> "Advanced"
        # >> See http://forum.kodi.tv/showthread.php?tid=164522
        self.kodi_audio_suspended = False
        if self.settings['suspend_audio_engine']:
            logger.debug('_launch_pre_exec() Suspending Kodi audio engine')
            xbmc.audioSuspend()
            xbmc.enableNavSounds(False)
            xbmc.sleep(100)
            self.kodi_audio_suspended = True
        else:
            logger.debug('_launch_pre_exec() DO NOT suspend Kodi audio engine')

        # --- Force joystick suspend if requested in "Settings" --> "Advanced"
        # >> See https://forum.kodi.tv/showthread.php?tid=287826&pid=2627128#pid2627128
        # >> See https://forum.kodi.tv/showthread.php?tid=157499&pid=1722549&highlight=input.enablejoystick#pid1722549
        # >> See https://forum.kodi.tv/showthread.php?tid=313615
        self.kodi_joystick_suspended = False
        # if self.settings['suspend_joystick_engine']:
            # logger.debug('_launch_pre_exec() Suspending Kodi joystick engine')
            # >> Research. Get the value of the setting first
            # >> Apparently input.enablejoystick is not supported on Kodi Krypton anymore.
            # c_str = ('{"id" : 1, "jsonrpc" : "2.0",'
            #          ' "method" : "Settings.GetSettingValue",'
            #          ' "params" : {"setting":"input.enablejoystick"}}')
            # response = xbmc.executeJSONRPC(c_str)
            # logger.debug('JSON      ''{0}'''.format(c_str))
            # logger.debug('Response  ''{0}'''.format(response))

            # c_str = ('{"id" : 1, "jsonrpc" : "2.0",'
            #          ' "method" : "Settings.SetSettingValue",'
            #          ' "params" : {"setting" : "input.enablejoystick", "value" : false} }')
            # response = xbmc.executeJSONRPC(c_str)
            # logger.debug('JSON      ''{0}'''.format(c_str))
            # logger.debug('Response  ''{0}'''.format(response))
            # self.kodi_joystick_suspended = True

            # logger.error('_launch_pre_exec() Suspending Kodi joystick engine not supported on Kodi Krypton!')
        # else:
            # logger.debug('_launch_pre_exec() DO NOT suspend Kodi joystick engine')

        # --- Toggle Kodi windowed/fullscreen if requested ---
        if toggle_screen_flag:
            logger.debug('_launch_pre_exec() Toggling Kodi fullscreen')
            kodi.toggle_fullscreen()
        else:
            logger.debug('_launch_pre_exec() Toggling Kodi fullscreen DEACTIVATED in Launcher')

        # Disable screensaver
        if self.settings['suspend_screensaver']:
            kodi.disable_screensaver()
        else:
            screensaver_mode = kodi.get_screensaver_mode()
            logger.debug('_run_before_execution() Screensaver status "{}"'.format(screensaver_mode))

        # --- Pause Kodi execution some time ---
        delay_tempo_ms = self.settings['delay_tempo']
        logger.debug('_launch_pre_exec() Pausing {} ms'.format(delay_tempo_ms))
        xbmc.sleep(delay_tempo_ms)
        logger.debug('LauncherABC::_launch_pre_exec() function ENDS')

    def _launch_post_exec(self, toggle_screen_flag):
        logger.debug('LauncherABC::_launch_post_exec() Starting ...')

        # --- Stop Kodi some time ---
        delay_tempo_ms = self.settings['delay_tempo']
        logger.debug('_launch_post_exec() Pausing {} ms'.format(delay_tempo_ms))
        xbmc.sleep(delay_tempo_ms)

        # --- Toggle Kodi windowed/fullscreen if requested ---
        if toggle_screen_flag:
            logger.debug('_launch_post_exec() Toggling Kodi fullscreen')
            kodi.toggle_fullscreen()
        else:
            logger.debug('_launch_post_exec() Toggling Kodi fullscreen DEACTIVATED in Launcher')

        # --- Resume audio engine if it was suspended ---
        # Calling xmbc.audioResume() takes a loong time (2/4 secs) if audio was not properly suspended!
        # Also produces this in Kodi's log:
        # WARNING: CActiveAE::StateMachine - signal: 0 from port: OutputControlPort not handled for state: 7
        #   ERROR: ActiveAE::Resume - failed to init
        if self.kodi_audio_suspended:
            logger.debug('_launch_post_exec() Kodi audio engine was suspended before launching')
            logger.debug('_launch_post_exec() Resuming Kodi audio engine')
            xbmc.audioResume()
            xbmc.enableNavSounds(True)
            xbmc.sleep(100)
        else:
            logger.debug('_launch_post_exec() DO NOT resume Kodi audio engine')

        # --- Resume joystick engine if it was suspended ---
        if self.kodi_joystick_suspended:
            logger.debug('_launch_post_exec() Kodi joystick engine was suspended before launching')
            logger.debug('_launch_post_exec() Resuming Kodi joystick engine')
            # response = xbmc.executeJSONRPC(c_str)
            # logger.debug('JSON      ''{0}'''.format(c_str))
            # logger.debug('Response  ''{0}'''.format(response))
            logger.debug('_launch_post_exec() Not supported on Kodi Krypton!')
        else:
            logger.debug('_launch_post_exec() DO NOT resume Kodi joystick engine')

        # Restore screensaver status.
        if self.settings['suspend_screensaver']:
            kodi.restore_screensaver()
        else:
            screensaver_mode = kodi.get_screensaver_mode()
            logger.debug('_run_after_execution() Screensaver status "{}"'.format(screensaver_mode))

        # --- Resume Kodi playing if it was paused. If it was stopped, keep it stopped. ---
        media_state_action = self.settings['media_state_action']
        media_state_str = ['Stop', 'Pause', 'Let Play'][media_state_action]
        logger.debug('_launch_post_exec() media_state_action is "{}" ({})'.format(media_state_str, media_state_action))
        logger.debug('_launch_post_exec() self.kodi_was_playing is {}'.format(self.kodi_was_playing))
        if self.kodi_was_playing and media_state_action == 1:
            logger.debug('_launch_post_exec() Calling xbmc.Player().play()')
            xbmc.Player().play()
        logger.debug('LauncherABC::_launch_post_exec() function ENDS')

    # ---------------------------------------------------------------------------------------------
    # Launcher metadata and flags related methods
    # ---------------------------------------------------------------------------------------------
    def get_platform(self): return self.entity_data['platform']

    def set_platform(self, platform): self.entity_data['platform'] = platform

    def get_category_id(self): return self.entity_data['categoryID'] if 'categoryID' in self.entity_data else None

    def update_category(self, category_id): self.entity_data['categoryID'] = category_id

    def is_in_windowed_mode(self): return self.entity_data['toggle_window']

    def set_windowed_mode(self, windowed_mode):
        self.entity_data['toggle_window'] = windowed_mode
        return self.is_in_windowed_mode()

    def is_non_blocking(self):
        return 'non_blocking' in self.entity_data and self.entity_data['non_blocking']

    def set_non_blocking(self, is_non_blocking):
        self.entity_data['non_blocking'] = is_non_blocking
        return self.is_non_blocking()

    # Change the application this launcher uses. Override if application is changeable.
    def change_application(self): return False

# -------------------------------------------------------------------------------------------------
# Standalone application launcher
# -------------------------------------------------------------------------------------------------
class StandaloneLauncher(LauncherABC):
    def __init__(self, PATHS, settings, launcher_dic, objectRepository, executorFactory):
        # --- Create default Standalone Launcher if empty launcher_dic---
        # Concrete classes are responsible of creating a default entity_data dictionary
        # with sensible defaults.
        if launcher_dic is None:
            launcher_dic = fs_new_launcher()
            launcher_dic['id'] = misc_generate_random_SID()
            launcher_dic['type'] = OBJ_LAUNCHER_STANDALONE
        super(StandaloneLauncher, self).__init__(PATHS, settings, launcher_dic, objectRepository, executorFactory)

    # --------------------------------------------------------------------------------------------
    # Core methods
    # --------------------------------------------------------------------------------------------
    def get_object_name(self): return 'Standalone launcher'

    def get_assets_kind(self): return KIND_ASSET_LAUNCHER

    def get_launcher_type(self): return OBJ_LAUNCHER_STANDALONE

    def save_to_disk(self): self.objectRepository.save_launcher(self.entity_data)

    # Object becomes invalid after deletion
    def delete_from_disk(self):
        self.objectRepository.delete_launcher(self.entity_data)
        self.entity_data = None
        self.objectRepository = None

    def supports_launching_roms(self): return False

    def supports_parent_clone_roms(self): return False

    # --------------------------------------------------------------------------------------------
    # Launcher build wizard methods
    # --------------------------------------------------------------------------------------------
    #
    # Returns True if Launcher was sucesfully built.
    # Returns False if Launcher was not built (user canceled the dialogs or some other
    #
    def build(self, launcher): return super(StandaloneLauncher, self).build(launcher)

    #
    # Creates a new launcher using a wizard of dialogs.
    # _builder_get_wizard() is always defined in Launcher concrete classes and it's called by
    # parent build() method.
    #
    def _builder_get_wizard(self, wizard):
        wizard = WizardDialog_FileBrowse(wizard, 'application', 'Select the launcher application',
            1, self._builder_get_appbrowser_filter)
        wizard = WizardDialog_Dummy(wizard, 'args', '')
        wizard = WizardDialog_Keyboard(wizard, 'args', 'Application arguments')
        wizard = WizardDialog_Dummy(wizard, 'm_name', '',
            self._builder_get_title_from_app_path)
        wizard = WizardDialog_Keyboard(wizard, 'm_name','Set the title of the launcher',
            self._builder_get_title_from_app_path)
        wizard = WizardDialog_Selection(wizard, 'platform', 'Select the platform',
            AEL_platform_list)
        return wizard

    def _build_pre_wizard_hook(self): return True

    def _build_post_wizard_hook(self): return True

    # --------------------------------------------------------------------------------------------
    # Launcher edit methods
    # --------------------------------------------------------------------------------------------
    def get_main_edit_options(self, category):
        logger.debug('StandaloneLauncher::get_main_edit_options() Starting ...')

        options = collections.OrderedDict()
        options['EDIT_METADATA']          = 'Edit Metadata ...'
        options['EDIT_ASSETS']            = 'Edit Assets/Artwork ...'
        options['EDIT_DEFAULT_ASSETS']    = 'Choose default Assets/Artwork ...'
        options['EDIT_LAUNCHER_CATEGORY'] = "Change Category: '{0}'".format(category.get_name())
        options['EDIT_LAUNCHER_STATUS']   = 'Launcher status: {0}'.format(self.get_finished_str())
        options['LAUNCHER_ADVANCED_MODS'] = 'Advanced Modifications ...'
        options['EXPORT_LAUNCHER']        = 'Export Launcher XML configuration ...'
        options['DELETE_LAUNCHER']        = 'Delete Launcher'

        return options

    def get_advanced_modification_options(self):
        logger.debug('StandaloneLauncher::get_advanced_modification_options() Starting ...')
        toggle_window_str = 'ON' if self.entity_data['toggle_window'] else 'OFF'
        non_blocking_str  = 'ON' if self.entity_data['non_blocking'] else 'OFF'

        options = collections.OrderedDict()
        options['EDIT_APPLICATION']     = "Change Application: '{0}'".format(self.entity_data['application'])
        options['MODIFY_ARGS']          = "Modify Arguments: '{0}'".format(self.entity_data['args'])
        options['ADDITIONAL_ARGS']      = "Modify aditional arguments ..."
        options['TOGGLE_WINDOWED']      = "Toggle Kodi into windowed mode (now {0})".format(toggle_window_str)
        options['TOGGLE_NONBLOCKING']   = "Non-blocking launcher (now {0})".format(non_blocking_str)

        return options

    # ---------------------------------------------------------------------------------------------
    # Execution methods
    # ---------------------------------------------------------------------------------------------
    def launch(self):
        logger.debug('StandaloneLauncher::launch() Starting ...')
        self.title       = self.entity_data['m_name']
        self.application = FileName(self.entity_data['application'])
        self.arguments   = self.entity_data['args']

        # --- Check for errors and abort if errors found ---
        if not self.application.exists():
            logger.error('Launching app not found "{0}"'.format(self.application.getPath()))
            kodi.notify_warn('App {0} not found.'.format(self.application.getPath()))
            return

        # --- Argument substitution ---
        log_info('Raw arguments   "{0}"'.format(self.arguments))
        self.arguments = self.arguments.replace('$apppath$' , self.application.getDir())
        log_info('Final arguments "{0}"'.format(self.arguments))

        # --- Call LauncherABC.launch(). Executor object is created there and invoked ---
        super(StandaloneLauncher, self).launch()
        logger.debug('StandaloneLauncher::launch() END ...')

    # ---------------------------------------------------------------------------------------------
    # Launcher metadata and flags related methods
    # ---------------------------------------------------------------------------------------------
    def change_application(self):
        current_application = self.entity_data['application']
        selected_application = xbmcgui.Dialog().browse(1, 'Select the launcher application', 'files',
                                                      self._builder_get_appbrowser_filter('application', self.entity_data),
                                                      False, False, current_application).decode('utf-8')

        if selected_application is None or selected_application == current_application:
            return False

        self.entity_data['application'] = selected_application

    def set_args(self, args): self.entity_data['args'] = args

    def get_args(self): return self.entity_data['args']

    def get_additional_argument(self, index):
        args = self.get_all_additional_arguments()
        return args[index]

    def get_all_additional_arguments(self):
        return self.entity_data['args_extra']

    def add_additional_argument(self, arg):
        if not self.entity_data['args_extra']:
            self.entity_data['args_extra'] = []

        self.entity_data['args_extra'].append(arg)
        logger.debug('launcher.add_additional_argument() Appending extra_args to launcher {0}'.format(self.get_id()))

    def set_additional_argument(self, index, arg):
        if not self.entity_data['args_extra']:
            self.entity_data['args_extra'] = []
        self.entity_data['args_extra'][index] = arg
        logger.debug('launcher.set_additional_argument() Edited args_extra[{0}] to "{1}"'.format(index, self.entity_data['args_extra'][index]))

    def remove_additional_argument(self, index):
        del self.entity_data['args_extra'][index]
        logger.debug("launcher.remove_additional_argument() Deleted launcher['args_extra'][{0}]".format(index))
