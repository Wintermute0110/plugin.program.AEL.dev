from abc import ABCMeta, abstractmethod

import os, sys, string, re

# --- Kodi stuff ---
import xbmc, xbmcgui

# --- Modules/packages in this plugin ---
from constants import *
from executors import *
from romsets import *
from romstats import *
from disk_IO import *
from utils import *
from utils_kodi import *

class LauncherFactory():

    def __init__(self, settings, romsetFactory, executorFactory):
        self.settings = settings
        self.romsetFactory = romsetFactory
        self.executorFactory = executorFactory

    def create(self, launcherID, launchers, rom = None):
             
        if launcherID not in launchers:
            log_error('launcherfactory.create(): Launcher "{0}" not found in launchers'.format(launcherID))
            return None
        
        launcher = launchers[launcherID]
        launcherType = launcher['type'] if 'type' in launcher else None

        if launcherType is None:
            launcherType = self._determineType(rom) # backwardscompatibilty
            
        if launcherType == LAUNCHER_STANDALONE:
            return ApplicationLauncher(self.settings, self.executorFactory, launcher)

        if launcherType == LAUNCHER_FAVOURITES:
            return KodiLauncher(self.settings, self.executorFactory, launcher)

        if rom is None:
            return None
        
        statsStrategy = RomStatisticsStrategy(self.romsetFactory, launchers)

        if launcherType == LAUNCHER_RETROPLAYER:
            return RetroplayerLauncher(self.settings, None, None, self.settings['escape_romfile'], launcher, rom)

        if launcherType == LAUNCHER_RETROARCH:
            return RetroarchLauncher(self.settings, self.executorFactory, statsStrategy, self.settings['escape_romfile'], launcher, rom)

        if launcherType == LAUNCHER_ROM:
            return StandardRomLauncher(self.settings, self.executorFactory, statsStrategy, self.settings['escape_romfile'], launcher, rom)

        if launcherType == LAUNCHER_STEAM:
            return SteamLauncher(self.settings, self.executorFactory, statsStrategy, launcher, rom)

        if launcherType == LAUNCHER_NVGAMESTREAM:
            return NvidiaGameStreamLauncher(self.settings, self.executorFactory, statsStrategy, False, launcher, rom)


        return None

    # for backwards compatibility
    def _determineType(self, rom):
        if rom is None:
            return LAUNCHER_STANDALONE

        return LAUNCHER_ROM

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

class ApplicationLauncher(Launcher):
    
    def __init__(self, settings, executorFactory, launcher):
        
        super(ApplicationLauncher, self).__init__(launcher, settings, executorFactory, launcher['toggle_window'])
        
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
    
class KodiLauncher(Launcher):
    
    def __init__(self, settings, executorFactory, launcher):
        
        super(KodiLauncher, self).__init__(launcher, settings, executorFactory, launcher['toggle_window'])
        
    def launch(self):

        self.title              = self.launcher['m_name']
        self.application        = FileNameFactory.create('xbmc.exe')
        self.arguments          = self.launcher['application']       
        
        super(KodiLauncher, self).launch()
        pass

class StandardRomLauncher(Launcher):
    
    def __init__(self, settings, executorFactory, statsStrategy, escape_romfile, launcher, rom):

        self.validate_if_app_exists = True
        self.validate_if_rom_exists = True

        self.rom = rom
        self.categoryID = ''

        self.escape_romfile = escape_romfile
        self.statsStrategy = statsStrategy

        non_blocking_flag = launcher['non_blocking'] if 'non_blocking' in launcher else False
        super(StandardRomLauncher, self).__init__(launcher, settings, executorFactory, launcher['toggle_window'], non_blocking_flag)

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
    
    # ~~~~ Argument substitution ~~~~~
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
        log_info('StandardRomLauncher() appbase      "{0}"'.format(self.application.getBase()))
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
                
        log_info('StandardRomLauncher() final arguments "{0}"'.format(self.arguments))
    
    def launch(self):
        
        self.title  = self.rom['m_name']

        self._selectApplicationToUse()
        self._selectArgumentsToUse()
        
        ROMFileName = self._selectRomFileToUse()

        log_info('StandardRomLauncher() ROMFileName OP "{0}"'.format(ROMFileName.getOriginalPath()))
        log_info('StandardRomLauncher() ROMFileName  P "{0}"'.format(ROMFileName.getPath()))

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
        
        super(StandardRomLauncher, self).launch()
        pass

# --- Execute Kodi Retroplayer if launcher configured to do so ---
# See https://github.com/Wintermute0110/plugin.program.advanced.emulator.launcher/issues/33
# See https://forum.kodi.tv/showthread.php?tid=295463&pid=2620489#pid2620489
class RetroplayerLauncher(StandardRomSet):

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

#
# Read RetroarchLauncher.md
#
class RetroarchLauncher(StandardRomLauncher):
        
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

class SteamLauncher(Launcher):

    def __init__(self, settings, executorFactory, statsStrategy, launcher, rom):

        self.rom = rom
        self.categoryID = ''
        self.statsStrategy = statsStrategy

        non_blocking_flag = launcher['non_blocking'] if 'non_blocking' in launcher else False
        super(SteamLauncher, self).__init__(launcher, settings, executorFactory, launcher['toggle_window'], non_blocking_flag)
        
    def launch(self):
        
        self.title  = self.rom['m_name']
        
        url = 'steam://rungameid/'

        self.application = FileNameFactory.create('steam://rungameid/')
        self.arguments = str(self.rom['steamid'])

        log_info('SteamLauncher() ROM ID {0}: @{1}"'.format(self.rom['steamid'], self.rom['m_name']))
        self.statsStrategy.updateRecentlyPlayedRom(self.rom)       
        
        super(SteamLauncher, self).launch()
        pass

class NvidiaGameStreamLauncher(StandardRomLauncher):
        
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