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
import logging

# --- AEL packages ---
from resources.lib.utils import io, kodi,
from resources.lib import globals, platforms
from resources.lib.executors import *
from resources.lib.constants import *

logger = logging.getLogger(__name__)

class LauncherSettings(object):
    is_non_blocking = False
    toggle_window = False
    display_launcher_notify = True
    media_state_action = 0 # id="media_state_action" default="0" values="Stop|Pause|Let Play"
    suspend_audio_engine = False
    suspend_screensaver = True
    delay_tempo = 1000
    
    
# -------------------------------------------------------------------------------------------------
# Abstract base class for launching anything that is supported.
# Implement classes that inherit this base class to support new ways of launching.
# -------------------------------------------------------------------------------------------------
class LauncherABC(object):
    __metaclass__ = abc.ABCMeta

    #
    # In an abstract class launcher_data is mandatory.
    #
    def __init__(self, executorFactory: ExecutorFactoryABC, settings: LauncherSettings):
        self.executorFactory = executorFactory
        self.settings        = settings
        self.launcher_args   = {}
        self.application     = None
        self.arguments       = None

    # --------------------------------------------------------------------------------------------
    # Core methods
    # --------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def get_name(self) -> str: return ''
    
    @abc.abstractmethod
    def get_launcher_addon_id(self) -> str: return ''

    def get_launcher_args(self) -> dict:
        return self.launcher_args
    
    def set_launcher_args(self, args:dict):
        self.launcher_args = args

    # --------------------------------------------------------------------------------------------
    # Launcher build wizard methods
    # --------------------------------------------------------------------------------------------
    #
    # Builds a new Launcher.
    # Returns True if Launcher  was sucesfully built.
    # Returns False if Launcher was not built (user canceled the dialogs or some other
    # error happened).
    #
    def build(self, romset_id, platform:str):
        logger.debug('LauncherABC::build() Starting ...')

        # --- Call hook before wizard ---
        if not self._build_pre_wizard_hook(): return False

        # --- Launcher build code (ask user about launcher stuff) ---
        wizard = kodi.WizardDialog_Dummy(None, 'romset_id', romset_id)
        wizard = kodi.WizardDialog_Dummy(wizard, 'platform', platform)
        wizard = kodi.WizardDialog_Dummy(wizard, 'addon_id', self.get_launcher_addon_id())
        # >> Call Child class wizard builder method
        wizard = self._builder_get_wizard(wizard)
        # >> Run wizard
        self.launcher_args = wizard.runWizard(self.launcher_args)
        if not self.launcher_args: return False

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

    def _builder_get_appbrowser_filter(self, item_key, launcher):
        if item_key in launcher:
            application = launcher[item_key]
            if application == 'JAVA':
                return '.jar'

        return '.bat|.exe|.cmd|.lnk' if io.is_windows() else ''

    #
    # Wizard helper, when a user wants to set a custom value instead of the predefined list items.
    #
    def _builder_user_selected_custom_browsing(self, item_key, launcher):
        return launcher[item_key] == 'BROWSE'
    
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

        logger.debug('Name        = "{}"'.format(self.get_name()))
        logger.debug('Application = "{}"'.format(self.application.getPath()))
        logger.debug('Arguments   = "{}"'.format(self.arguments))
        logger.debug('Executor    = "{}"'.format(executor.__class__.__name__))

        # --- Execute app ---
        self._launch_pre_exec(self.get_name(), self.settings.toggle_window)
        executor.execute(self.application, self.arguments, self.settings.is_non_blocking)
        self._launch_post_exec(self.settings.toggle_window)

    #
    # These two functions do things like stopping music before lunch, toggling full screen, etc.
    # Variables set in this function:
    # self.kodi_was_playing      True if Kodi player was ON, False otherwise
    # self.kodi_audio_suspended  True if Kodi audio suspended before launching
    #
    def _launch_pre_exec(self, title, toggle_screen_flag):
        logger.debug('LauncherABC::_launch_pre_exec() Starting ...')

        # --- User notification ---
        if self.settings.display_launcher_notify:
            kodi.notify('Launching {}'.format(title))

        # --- Stop/Pause Kodi mediaplayer if requested in settings ---
        self.kodi_was_playing = False
        # id="media_state_action" default="0" values="Stop|Pause|Let Play"
        media_state_action = self.setting.media_state_action
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
        if self.settings.suspend_audio_engine:
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
        if self.settings.suspend_screensaver:
            kodi.disable_screensaver()
        else:
            screensaver_mode = kodi.get_screensaver_mode()
            logger.debug('_run_before_execution() Screensaver status "{}"'.format(screensaver_mode))

        # --- Pause Kodi execution some time ---
        delay_tempo_ms = self.settings.delay_tempo
        logger.debug('_launch_pre_exec() Pausing {} ms'.format(delay_tempo_ms))
        xbmc.sleep(delay_tempo_ms)
        logger.debug('LauncherABC::_launch_pre_exec() function ENDS')

    def _launch_post_exec(self, toggle_screen_flag):
        logger.debug('LauncherABC::_launch_post_exec() Starting ...')

        # --- Stop Kodi some time ---
        delay_tempo_ms = self.settings.delay_tempo
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
        if self.settings.suspend_screensaver:
            kodi.restore_screensaver()
        else:
            screensaver_mode = kodi.get_screensaver_mode()
            logger.debug('_run_after_execution() Screensaver status "{}"'.format(screensaver_mode))

        # --- Resume Kodi playing if it was paused. If it was stopped, keep it stopped. ---
        media_state_action = self.settings.media_state_action
        media_state_str = ['Stop', 'Pause', 'Let Play'][media_state_action]
        logger.debug('_launch_post_exec() media_state_action is "{}" ({})'.format(media_state_str, media_state_action))
        logger.debug('_launch_post_exec() self.kodi_was_playing is {}'.format(self.kodi_was_playing))
        if self.kodi_was_playing and media_state_action == 1:
            logger.debug('_launch_post_exec() Calling xbmc.Player().play()')
            xbmc.Player().play()
        logger.debug('LauncherABC::_launch_post_exec() function ENDS')

# -------------------------------------------------------------------------------------------------
# Abstract base class for launching anything ROMs or item based.
# This class support Parent/Clone generation, multidisc support, and ROM No-Intro/REDUMP audit.
# Inherit from this base class to implement your own specific ROM launcher.
# -------------------------------------------------------------------------------------------------
class AppLauncher(LauncherABC):

    def __init__(self, executorFactory: ExecutorFactoryABC, settings: LauncherSettings):
        super(AppLauncher, self).__init__(executorFactory, settings)

    # --------------------------------------------------------------------------------------------
    # Core methods
    # --------------------------------------------------------------------------------------------
    def get_name(self) -> str: return 'App Launcher'
    
    def get_launcher_addon_id(self) -> str: return '{}.AppLauncher'.format(globals.addon_id)

    # --------------------------------------------------------------------------------------------
    # Launcher build wizard methods
    # --------------------------------------------------------------------------------------------
    #
    # Creates a new launcher using a wizard of dialogs. Called by parent build() method.
    #
    def _builder_get_wizard(self, wizard):
    
        wizard = kodi.WizardDialog_FileBrowse(wizard, 'application', 'Select the launcher application', 1, self._builder_get_appbrowser_filter)
        wizard = kodi.WizardDialog_Dummy(wizard, 'romext', '', self._builder_get_extensions_from_app_path)
        wizard = kodi.WizardDialog_Keyboard(wizard, 'romext','Set files extensions, use "|" as separator. (e.g lnk|cbr)')
        wizard = kodi.WizardDialog_Dummy(wizard, 'args', '', self._builder_get_arguments_from_application_path)
        wizard = kodi.WizardDialog_Keyboard(wizard, 'args', 'Application arguments')
        wizard = kodi.WizardDialog_YesNo(wizard, 'is_non_blocking', 'Is non blocking?')
        
        return wizard
    
    def _build_post_wizard_hook(self):
        return True

    def _builder_get_extensions_from_app_path(self, input, item_key ,launcher_args):
        if input: return input

        app = launcher_args['application']
        appPath = io.FileName(app)

        extensions = platforms.emudata_get_program_extensions(appPath.getBase())
        return extensions

    def _builder_get_arguments_from_application_path(self, input, item_key, launcher_args):
        if input: return input
        app = launcher_args['application']
        appPath = io.FileName(app)
        default_arguments = platforms.emudata_get_program_arguments(appPath.getBase())

        return default_arguments

    def _builder_get_value_from_rompath(self, input, item_key, launcher_args):
        if input: return input
        romPath = launcher_args['rompath']

        return romPath

    def _builder_get_value_from_assetpath(self, input, item_key, launcher_args):
        if input: return input
        romPath = io.FileName(launcher_args['assets_path'])
        romPath = romPath.pjoin('games')

        return romPath.getPath()
    
    # ---------------------------------------------------------------------------------------------
    # Execution methods
    # ---------------------------------------------------------------------------------------------
    def launch(self):
        self.title = self.rom.get_name()
        self.selected_rom_file = None

        applicationIsSet = self._launch_selectApplicationToUse()
        argumentsAreSet  = self._launch_selectArgumentsToUse()
        romIsSelected    = self._launch_selectRomFileToUse()

        if not applicationIsSet or not argumentsAreSet or not romIsSelected:
            return

        self._launch_parseArguments()

        if self.statsStrategy is not None:
            self.statsStrategy.update_launched_rom_stats(self.rom)
            self.save_ROM(self.rom)

        super(AppLauncher, self).launch()

    def _launch_selectApplicationToUse(self):
        if self.rom.has_alternative_application():
            logger.info('StandardRomLauncher() Using ROM altapp')
            self.application = io.FileName(self.rom.get_alternative_application())
        else:
            self.application = io.FileName(self.entity_data['application'])

        # --- Check for errors and abort if found --- todo: CHECK
        if not self.application.exists():
            logger.error('StandardRomLauncher::_selectApplicationToUse(): Launching app not found "{0}"'.format(self.application.getPath()))
            kodi.notify_warn('Launching app not found {0}'.format(self.application.getPath()))
            return False

        return True

    def _launch_selectArgumentsToUse(self):
        if self.rom.has_alternative_arguments():
            logger.info('StandardRomLauncher() Using ROM altarg')
            self.arguments = self.rom.get_alternative_arguments()
        elif self.entity_data['args_extra']:
             # >> Ask user what arguments to launch application
            logger.info('StandardRomLauncher() Using Launcher args_extra')
            launcher_args = self.entity_data['args']
            arg_list = [self.entity_data_args] + self.entity_data['args_extra']
            dialog = xbmcgui.Dialog()
            dselect_ret = dialog.select('Select launcher arguments', arg_list)
            if dselect_ret < 0:
                return False
            logger.info('StandardRomLauncher() User chose args index {0} ({1})'.format(dselect_ret, arg_list[dselect_ret]))
            self.arguments = arg_list[dselect_ret]
        else:
            self.arguments = self.entity_data['args']

        return True

    def _launch_selectRomFileToUse(self):
        if not self.rom.has_multiple_disks():
            self.selected_rom_file = self.rom.get_file()
            return True

        disks = self.rom.get_disks()
        logger.info('StandardRomLauncher._selectRomFileToUse() Multidisc ROM set detected')
        dialog = xbmcgui.Dialog()
        dselect_ret = dialog.select('Select ROM to launch in multidisc set', disks)
        if dselect_ret < 0:
           return False

        selected_rom_base = disks[dselect_ret]
        logger.info('StandardRomLauncher._selectRomFileToUse() Selected ROM "{0}"'.format(selected_rom_base))

        ROM_temp = self.rom.get_file()
        ROM_dir = io.FileName(ROM_temp.getDir())
        ROMFileName = ROM_dir.pjoin(selected_rom_base)

        logger.info('StandardRomLauncher._selectRomFileToUse() ROMFileName OP "{0}"'.format(ROMFileName.getPath()))
        logger.info('StandardRomLauncher._selectRomFileToUse() ROMFileName  P "{0}"'.format(ROMFileName.getPath()))

        if not ROMFileName.exists():
            logger.error('ROM not found "{0}"'.format(ROMFileName.getPath()))
            kodi.notify_warn('ROM not found "{0}"'.format(ROMFileName.getPath()))
            return False

        self.selected_rom_file = ROMFileName

        return True

    # --- Argument substitution ---
    def _launch_parseArguments(self):
        logger.info('RomLauncher() raw arguments   "{0}"'.format(self.arguments))

        #Application based arguments replacements
        if self.application and isinstance(self.application, io.FileName):
           apppath = self.application.getDir()

           logger.info('RomLauncher() application  "{0}"'.format(self.application.getPath()))
           logger.info('RomLauncher() appbase      "{0}"'.format(self.application.getBase()))
           logger.info('RomLauncher() apppath      "{0}"'.format(apppath))

           self.arguments = self.arguments.replace('$apppath$', apppath)
           self.arguments = self.arguments.replace('$appbase$', self.application.getBase())

        # ROM based arguments replacements
        if self.selected_rom_file:
            # --- Escape quotes and double quotes in ROMFileName ---
            # >> This maybe useful to Android users with complex command line arguments
            if self.settings['escape_romfile']:
                logger.info("RomLauncher() Escaping ROMFileName ' and \"")
                self.selected_rom_file.escapeQuotes()

            rompath       = self.selected_rom_file.getDir()
            rombase       = self.selected_rom_file.getBase()
            rombase_noext = self.selected_rom_file.getBaseNoExt()

            logger.info('RomLauncher() romfile      "{0}"'.format(self.selected_rom_file.getPath()))
            logger.info('RomLauncher() rompath      "{0}"'.format(rompath))
            logger.info('RomLauncher() rombase      "{0}"'.format(rombase))
            logger.info('RomLauncher() rombasenoext "{0}"'.format(rombase_noext))

            self.arguments = self.arguments.replace('$rom$', self.selected_rom_file.getPath())
            self.arguments = self.arguments.replace('$romfile$', self.selected_rom_file.getPath())
            self.arguments = self.arguments.replace('$rompath$', rompath)
            self.arguments = self.arguments.replace('$rombase$', rombase)
            self.arguments = self.arguments.replace('$rombasenoext$', rombase_noext)

            # >> Legacy names for argument substitution
            self.arguments = self.arguments.replace('%rom%', self.selected_rom_file.getPath())
            self.arguments = self.arguments.replace('%ROM%', self.selected_rom_file.getPath())

        category_id = self.get_category_id()
        if category_id is None:
            category_id = ''

        # Default arguments replacements
        self.arguments = self.arguments.replace('$categoryID$', category_id)
        self.arguments = self.arguments.replace('$launcherID$', self.entity_data['id'])
        self.arguments = self.arguments.replace('$romID$', self.rom.get_id())
        self.arguments = self.arguments.replace('$romtitle$', self.title)

        # automatic substitution of rom values
        for rom_key, rom_value in self.rom.get_data_dic().iteritems():
            if isinstance(rom_value, str):
                self.arguments = self.arguments.replace('${}$'.format(rom_key), rom_value)        

        # automatic substitution of launcher values
        for launcher_key, launcher_value in self.entity_data.iteritems():
            if isinstance(launcher_value, str):
                self.arguments = self.arguments.replace('${}$'.format(launcher_key), launcher_value)

        logger.info('RomLauncher() final arguments "{0}"'.format(self.arguments))
