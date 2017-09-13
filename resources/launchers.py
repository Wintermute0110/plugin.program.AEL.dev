from abc import ABCMeta, abstractmethod

import os, sys, string, re

# --- Kodi stuff ---
import xbmc, xbmcgui

# --- Modules/packages in this plugin ---
from constants import *
from executors import *
from romsets import *
from disk_IO import *
from utils import *
from utils_kodi import *

class LauncherFactory():

    def __init__(self, settings, romsetFactory, executorFactory):
        self.settings = settings
        self.romsetFactory = romsetFactory
        self.executorFactory = executorFactory

    def create(self, launchers, categoryID, launcherID, romID = None):
                
        if launcherID not in launchers:
            log_error('launcherID not found in launchers')
            return None

        launcher = launchers[launcherID]

        if romID is not None:
            return self.createRomLauncher(launcher, launcherID, romID, categoryID)

        return ApplicationLauncher(self.settings, self.executorFactory, launcher)
    
    def createRomLauncher(self, launcher, launcherID, romID, categoryID):
        
        romSet = self.romsetFactory.create(launcherID, categoryID, launcher['roms_base_noext'] if 'roms_base_noext' in launcher else None)
        romData = romSet.loadRom(romID)
        
        if romData is None:
            log_error('Rom not found in romset')
            return None

        if 'disks' in romData and romData['disks']:
            return MultiDiscRomLauncher(self.settings, self.executorFactory, self.settings['escape_romfile'], launcher, romData)
        
        log_info('LauncherFactory() Sigle ROM detected (no multidisc)')
        return StandardRomLauncher(self.settings, self.executorFactory, self.settings['escape_romfile'], launcher, romData)


#
# Abstract base class for launching anything that is supported.
# Implement classes that inherit this base class to support new ways of launching.
#
class Launcher():
    __metaclass__ = ABCMeta
    
    def __init__(self, settings, executorFactory, minimize_flag):

        self.settings        = settings
        self.executorFactory = executorFactory

        self.minimize_flag  = minimize_flag
        self.application    = None
        self.arguments      = None
        self.title          = None

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

        self.preExecution(self.title, self.minimize_flag)
        executor.execute(self.application, self.arguments)
        self.postExecution(self.minimize_flag)

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

        # --- Resume Kodi playing if it was paused. If it was stopped, keep it stopped. ---
        media_state_action = self.settings['media_state_action']
        media_state_str = ['Stop', 'Pause', 'Let Play'][media_state_action]
        log_verb('postExecution() media_state_action is "{0}" ({1})'.format(media_state_str, media_state_action))
        log_verb('postExecution() self.kodi_was_playing is {0}'.format(self.kodi_was_playing))
        if self.kodi_was_playing and media_state_action == 1:
            log_verb('postExecution() Calling xbmc.Player().play()')
            xbmc.Player().play()
        log_debug('postExecution() function ENDS')

class ApplicationLauncher(Launcher):
    
    def __init__(self, settings, executorFactory, launcher):

        self.launcher = launcher                
        super(ApplicationLauncher, self).__init__(settings, executorFactory, launcher['minimize'])
        
    def launch(self):

        self.title              = self.launcher['m_name']
        self.application        = FileName(self.launcher['application'])
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


class StandardRomLauncher(Launcher):

    def __init__(self, settings, executorFactory, escape_romfile, launcher, rom):
        self.launcher = launcher
        self.rom = rom
        self.categoryID = ''

        self.escape_romfile = escape_romfile
        
        super(StandardRomLauncher, self).__init__(settings, executorFactory, launcher['minimize'])

    def _parseArguments(self, romFile):
        
        # --- Escape quotes and double quotes in ROMFileName ---
        # >> This maybe useful to Android users with complex command line arguments
        if self.escape_romfile:
            log_info("StandardRomLauncher() Escaping ROMFileName ' and \"")
            romFile.escapeQuotes()

        apppath       = self.application.getDir()
        rompath       = romFile.getDir()
        rombase       = romFile.getBase()
        rombase_noext = romFile.getBase_noext()
        log_info('StandardRomLauncher() romfile      "{0}"'.format(romFile.getPath()))
        log_info('StandardRomLauncher() rompath      "{0}"'.format(rompath))
        log_info('StandardRomLauncher() rombase      "{0}"'.format(rombase))
        log_info('StandardRomLauncher() rombasenoext "{0}"'.format(rombase_noext))
        log_info('StandardRomLauncher() application  "{0}"'.format(self.application.getPath()))
        log_info('StandardRomLauncher() apppath      "{0}"'.format(apppath))

        
        # ~~~~ Argument substitution ~~~~~
        log_info('StandardRomLauncher() raw arguments   "{0}"'.format(self.arguments))
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
        # >> Legacy names for argument substitution
        self.arguments = self.arguments.replace('%rom%', romFile.getPath())
        self.arguments = self.arguments.replace('%ROM%', romFile.getPath())
        log_info('StandardRomLauncher() final arguments "{0}"'.format(self.arguments))

    def launch(self):
        
        self.title  = self.rom['m_name']

        if self.rom['altapp']:
            log_info('StandardRomLauncher() Using ROM altapp')
            self.application = FileName(self.rom['altapp'])
        else:
            self.application = FileName(self.launcher['application'])

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
        
        ROMFileName = FileName(self.rom['filename'])

        log_info('StandardRomLauncher() ROMFileName OP "{0}"'.format(ROMFileName.getOriginalPath()))
        log_info('StandardRomLauncher() ROMFileName  P "{0}"'.format(ROMFileName.getPath()))

        # --- Check for errors and abort if found --- todo: CHECK
        if not self.application.exists():
            log_error('Launching app not found "{0}"'.format(self.application.getPath()))
            kodi_notify_warn('Launching app not found {0}'.format(self.application.getOriginalPath()))
            return

        if not ROMFileName.exists():
            log_error('ROM not found "{0}"'.format(ROMFileName.getPath()))
            kodi_notify_warn('ROM not found "{0}"'.format(ROMFileName.getOriginalPath()))
            return
        
        # ~~~~ Argument substitution ~~~~~
        self._parseArguments(ROMFileName)

        ## --- Compute ROM recently played list ---
        #MAX_RECENT_PLAYED_ROMS = 100
        #recent_roms_list = fs_load_Collection_ROMs_JSON(RECENT_PLAYED_FILE_PATH)
        #recent_roms_list = [rom for rom in recent_roms_list if rom['id'] != recent_rom['id']]
        #recent_roms_list.insert(0, recent_rom)
        #if len(recent_roms_list) > MAX_RECENT_PLAYED_ROMS:
        #    log_debug('_command_run_rom() len(recent_roms_list) = {0}'.format(len(recent_roms_list)))
        #    log_debug('_command_run_rom() Trimming list to {0} ROMs'.format(MAX_RECENT_PLAYED_ROMS))
        #    temp_list        = recent_roms_list[:MAX_RECENT_PLAYED_ROMS]
        #    recent_roms_list = temp_list
        #fs_write_Collection_ROMs_JSON(RECENT_PLAYED_FILE_PATH, recent_roms_list)
        #
        ## --- Compute most played ROM statistics ---
        #most_played_roms = fs_load_Favourites_JSON(MOST_PLAYED_FILE_PATH)
        #if recent_rom['id'] in most_played_roms:
        #    rom_id = recent_rom['id']
        #    most_played_roms[rom_id]['launch_count'] += 1
        #else:
        #    # >> Add field launch_count to recent_rom to count how many times have been launched.
        #    recent_rom['launch_count'] = 1
        #    most_played_roms[recent_rom['id']] = recent_rom
        #
        #fs_write_Favourites_JSON(MOST_PLAYED_FILE_PATH, most_played_roms)
        
        super(StandardRomLauncher, self).launch()
        pass

class MultiDiscRomLauncher(StandardRomLauncher):

    def launch(self):

        log_info('MultiDiscRomLauncher() Multidisc ROM set detected')
        dialog = xbmcgui.Dialog()
        dselect_ret = dialog.select('Select ROM to launch in multidisc set', self.rom['disks'])
        if dselect_ret < 0:
           return

        selected_rom_base = self.rom['disks'][dselect_ret]
        log_info('MultiDiscRomLauncher() Selected ROM "{0}"'.format(selected_rom_base))

        ROM_temp = FileName(self.rom['filename'])
        ROM_dir = FileName(ROM_temp.getDir())
        ROMFileName = ROM_dir.pjoin(selected_rom_base)

        self.rom['filename'] = ROMFileName.getOriginalPath()
        
        super(MultiDiscRomLauncher, self).launch()
        pass
