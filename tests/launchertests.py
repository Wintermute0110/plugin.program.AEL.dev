import unittest
import mock
from mock import *

from resources.utils import *
from resources.disk_IO import *
from resources.launchers import *
from resources.utils_kodi import *

import resources.constants

class Test_Launcher(unittest.TestCase):

    def test_when_creating_a_launcher_with_not_exisiting_id_it_will_fail(self):
        # arrange
        launchers = {}

        # act
        factory = LauncherFactory(None, None, None)
        actual = factory.create('ABC', launchers)
        
        # assert
        self.assertIsNone(actual)
                
    @patch('resources.executors.ExecutorFactory')    
    def test_when_its_an_app_factory_loads_with_correct_launcher(self, mock_exeFactory):

        # arrange
        mock_exeFactory.create.return_value = FakeExecutor(None)
        set_log_level(LOG_VERB)
        set_use_print(True)

        launchers = {}
        launchers['ABC'] = {}
        launchers['ABC']['application'] = 'path'
        launchers['ABC']['minimize'] = True
        launchers['ABC']['romext'] = ''
        launchers['ABC']['application'] = ''
        launchers['ABC']['args'] = ''
        launchers['ABC']['args_extra'] = ''

        settings = {}
        settings['lirc_state'] = True

        # act
        factory = LauncherFactory(settings, None, mock_exeFactory)
        launcher = factory.create('ABC', launchers)
        
        # assert        
        actual = launcher.__class__.__name__
        expected = 'ApplicationLauncher'
        self.assertEqual(actual, expected)
        
    @patch('resources.executors.ExecutorFactory')
    def test_if_app_launcher_will_correctly_passthrough_parameters_when_launching(self, mock_exeFactory):

        # arrange
        set_log_level(LOG_VERB)
        set_use_print(True)

        expectedApp = 'AbcDefGhiJlkMnoPqrStuVw'
        expectedArgs = 'doop dap dib'

        launchers = {}
        launchers['ABC'] = {}
        launchers['ABC']['application'] = expectedApp
        launchers['ABC']['minimize'] = True
        launchers['ABC']['args'] = expectedArgs
        launchers['ABC']['m_name'] = 'MyApp'

        settings = {}
        settings['windows_cd_apppath'] = ''
        settings['windows_close_fds'] = ''
        settings['display_launcher_notify'] = False
        settings['media_state_action'] = 0
        settings['suspend_audio_engine'] = False
        settings['delay_tempo'] = 1
        
        mock = FakeExecutor(None)
        mock_exeFactory.create.return_value = mock

        factory = LauncherFactory(settings, None, mock_exeFactory)
        launcher = factory.create('ABC', launchers)

        # act
        launcher.launch()

        # assert
        self.assertEqual(expectedApp, mock.actualApplication.getOriginalPath())
        self.assertEqual(expectedArgs, mock.actualArgs)
        
    @patch('resources.executors.ExecutorFactory')
    def test_if_app_launcher_will_correctly_alter_arguments_when_launching(self, mock_exeFactory):

        # arrange
        set_log_level(LOG_VERB)
        set_use_print(True)

        expectedApp = 'C:\Sparta\Action.exe'
        expectedArgs = 'this is C:\Sparta'

        launchers = {}
        launchers['ABC'] = {}
        launchers['ABC']['application'] = expectedApp
        launchers['ABC']['minimize'] = True
        launchers['ABC']['args'] = 'this is $apppath%'
        launchers['ABC']['m_name'] = 'MyApp'
        
        mock = FakeExecutor(None)
        mock_exeFactory.create.return_value = mock

        settings = {}
        settings['windows_cd_apppath'] = ''
        settings['windows_close_fds'] = ''
        settings['display_launcher_notify'] = False
        settings['media_state_action'] = 0
        settings['suspend_audio_engine'] = False
        settings['delay_tempo'] = 1
        
        factory = LauncherFactory(settings, None, mock_exeFactory)
        launcher = factory.create('ABC', launchers)

        # act
        launcher.launch()

        # assert
        self.assertEqual(expectedApp, mock.actualApplication.getOriginalPath())
        self.assertEqual(expectedArgs, mock.actualArgs)
            
    @patch('resources.romsets.RomSetFactory')
    @patch('resources.executors.ExecutorFactory')
    def test_when_using_rom_the_factory_will_get_the_correct_launcher(self, mock_exeFactory, mock_romsFactory):
        
        # arrange
        set_log_level(LOG_VERB)
        set_use_print(True)

        launchers = {}
        launchers['ABC'] = {}
        launchers['ABC']['application'] = 'path'
        launchers['ABC']['minimize'] = True
        launchers['ABC']['romext'] = ''
        launchers['ABC']['application'] = ''
        launchers['ABC']['args'] = ''
        launchers['ABC']['args_extra'] = ''
        launchers['ABC']['roms_base_noext'] = 'snes'

        rom = {}
        rom['m_name'] = 'TestCase'        

        settings = {}
        settings['lirc_state'] = True
        settings['escape_romfile'] = True

        # act
        factory = LauncherFactory(settings, mock_romsFactory, mock_exeFactory)
        launcher = factory.create('ABC', launchers, rom)
        
        # assert
        actual = launcher.__class__.__name__
        expected = 'StandardRomLauncher'
        self.assertEqual(actual, expected)
                
    @patch('resources.romsets.RomSetFactory')
    @patch('resources.executors.ExecutorFactory')
    def test_if_rom_launcher_will_correctly_passthrough_the_application_when_launching(self, mock_exeFactory, mock_romsFactory):
        
        # arrange
        set_log_level(LOG_VERB)
        set_use_print(True)

        launchers = {}
        launchers['ABC'] = {}
        launchers['ABC']['id'] = 'ABC'
        launchers['ABC']['application'] = 'path'
        launchers['ABC']['minimize'] = True
        launchers['ABC']['romext'] = ''
        launchers['ABC']['application'] = ''
        launchers['ABC']['args'] = '-a -b -c -d -e $rom$ -yes'
        launchers['ABC']['args_extra'] = ''
        launchers['ABC']['roms_base_noext'] = 'snes'

        rom = {}
        rom['id'] = 'qqqq'
        rom['m_name'] = 'TestCase'
        rom['filename'] = 'testing.zip'
        rom['altapp'] = ''
        rom['altarg'] = ''
        
        settings = {}
        settings['lirc_state'] = True
        settings['escape_romfile'] = True
        settings['display_launcher_notify'] = False
        settings['media_state_action'] = 0
        settings['suspend_audio_engine'] = False
        settings['delay_tempo'] = 1

        mock_romsFactory.create.return_value = FakeRomSet(rom)
        mock = FakeExecutor(None)
        mock_exeFactory.create.return_value = mock

        expected = launchers['ABC']['application']
        expectedArgs = '-a -b -c -d -e testing.zip -yes'

        factory = LauncherFactory(settings, mock_romsFactory, mock_exeFactory)
        launcher = factory.create('ABC', launchers, rom)

        # act
        launcher.launch()

        # assert
        self.assertEqual(expected, mock.actualApplication.getOriginalPath())
        self.assertEqual(expectedArgs, mock.actualArgs)
                
    @patch('resources.romsets.RomSetFactory')
    @patch('resources.executors.ExecutorFactory')
    def test_if_rom_launcher_will_use_the_multidisk_launcher_when_romdata_has_disks_field_filled_in(self, mock_exeFactory, mock_romsFactory):
        
        # arrange
        set_log_level(LOG_VERB)
        set_use_print(True)

        launchers = {}
        launchers['ABC'] = {}
        launchers['ABC']['application'] = 'path'
        launchers['ABC']['minimize'] = True
        launchers['ABC']['romext'] = ''
        launchers['ABC']['application'] = ''
        launchers['ABC']['args'] = ''
        launchers['ABC']['args_extra'] = ''
        launchers['ABC']['roms_base_noext'] = 'snes'

        rom= {}
        rom['m_name'] = 'TestCase'
        rom['disks'] = ['disc01.zip', 'disc02.zip']
        
        settings = {}
        settings['lirc_state'] = True
        settings['escape_romfile'] = True
        
        mock_romsFactory.create.return_value = FakeRomSet(rom)
        mock = FakeExecutor(None)
        mock_exeFactory.create.return_value = mock

        # act
        factory = LauncherFactory(settings, mock_romsFactory, mock_exeFactory)
        launcher = factory.create('ABC', launchers, rom)
        
        # assert        
        actual = launcher.__class__.__name__
        expected = 'StandardRomLauncher'
        self.assertEqual(actual, expected)
                
    @patch('resources.romsets.RomSetFactory')
    @patch('resources.launchers.xbmcgui.Dialog.select')
    @patch('resources.executors.ExecutorFactory')
    def test_if_rom_launcher_will_apply_the_correct_disc_in_a_multidisc_situation(self, mock_exeFactory, mock_dialog, mock_romsFactory):

        # arrange
        set_log_level(LOG_VERB)
        set_use_print(True)

        launchers = {}
        launchers['ABC'] = {}
        launchers['ABC']['id'] = 'ABC'
        launchers['ABC']['application'] = 'path'
        launchers['ABC']['minimize'] = True
        launchers['ABC']['romext'] = ''
        launchers['ABC']['application'] = ''
        launchers['ABC']['args'] = '-a -b -c -d -e $rom$ -yes'
        launchers['ABC']['args_extra'] = ''
        launchers['ABC']['roms_base_noext'] = 'snes'

        rom = {}
        rom['id'] = 'qqqq'
        rom['m_name'] = 'TestCase'
        rom['filename'] = 'd:\\games\\discXX.zip'
        rom['altapp'] = ''
        rom['altarg'] = ''
        rom['disks'] = ['disc01.zip', 'disc02.zip']

        mock_dialog.return_value = 1
        mock_romsFactory.create.return_value = FakeRomSet(rom)
        mock = FakeExecutor(None)
        mock_exeFactory.create.return_value = mock

        settings = {}
        settings['lirc_state'] = True
        settings['escape_romfile'] = True
        settings['display_launcher_notify'] = False
        settings['media_state_action'] = 0
        settings['suspend_audio_engine'] = False
        settings['delay_tempo'] = 1

        expected = launchers['ABC']['application']
        expectedArgs = '-a -b -c -d -e d:\\games\\disc02.zip -yes'

        factory = LauncherFactory(settings, mock_romsFactory, mock_exeFactory)
        launcher = factory.create('ABC', launchers, rom)

        # act
        launcher.launch()

        # assert
        self.assertEqual(expectedArgs, mock.actualArgs)
                
    @patch('resources.launchers.sys')    
    @patch('resources.romsets.RomSetFactory')
    @patch('resources.executors.ExecutorFactory')
    def test_if_retroarch_launcher_will_apply_the_correct_arguments_when_running_on_android(self, mock_exeFactory, mock_romsFactory, mock_sys):
        
        # arrange
        mock_sys.configure_mock(platform='linux')
        set_log_level(LOG_VERB)
        set_use_print(True)

        launchers = {}
        launchers['ABC'] = {}
        launchers['ABC']['type'] = LAUNCHER_RETROARCH
        launchers['ABC']['id'] = 'ABC'
        launchers['ABC']['minimize'] = True
        launchers['ABC']['romext'] = None
        launchers['ABC']['args_extra'] = None
        launchers['ABC']['roms_base_noext'] = 'snes'
        launchers['ABC']['core'] = 'mame_libretro_android.so'
        launchers['ABC']['application'] = None

        rom = {}
        rom['id'] = 'qqqq'
        rom['m_name'] = 'TestCase'
        rom['filename'] = 'superrom.zip'
        rom['altapp'] = None

        mock_romsFactory.create.return_value = FakeRomSet(rom)
        mock = FakeExecutor(None)
        mock_exeFactory.create.return_value = mock

        settings = {}
        settings['lirc_state'] = True
        settings['escape_romfile'] = True
        settings['display_launcher_notify'] = False
        settings['media_state_action'] = 0
        settings['suspend_audio_engine'] = False
        settings['delay_tempo'] = 1

        expected = '/system/bin/am'
        expectedArgs = "start --user 0 -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -e ROM 'superrom.zip' -e LIBRETRO /data/data/com.retroarch/cores/mame_libretro_android.so -e CONFIGFILE /storage/emulated/0/Android/data/com.retroarch/files/retroarch.cfg -e IME com.android.inputmethod.latin/.LatinIME -e REFRESH 60 -n com.retroarch/.browser.retroactivity.RetroActivityFuture"

        factory = LauncherFactory(settings, mock_romsFactory, mock_exeFactory)
        launcher = factory.create('ABC', launchers, rom)

        # act
        launcher.launch()

        # assert
        self.assertEqual(expected, mock.actualApplication.getPath())
        self.assertEqual(expectedArgs, mock.actualArgs)

class FakeRomSet(RomSet):

    def __init__(self, rom):
        self.rom = rom

    def romSetFileExists(self):
        return True
            
    def loadRoms(self):
        return {}

    def loadRomsAsList(self):
        return []

    def loadRom(self, romId):
        return self.rom

    def saveRoms(self, roms):
        pass

class FakeExecutor(Executor):
    
    def execute(self, application, arguments, non_blocking):
        self.actualApplication = application
        self.actualArgs = arguments
        pass


if __name__ == '__main__':
   unittest.main()
