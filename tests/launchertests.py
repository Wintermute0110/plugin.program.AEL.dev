import unittest
import mock
from mock import *

from resources.utils import *
from resources.disk_IO import *
from resources.launchers import *
from resources.utils_kodi import *

class Test_Launcher(unittest.TestCase):

    def test_when_creating_a_launcher_with_not_exisiting_id_it_will_fail(self):
        # arrange
        launchers = {}

        # act
        factory = LauncherFactory(None, None, None)
        actual = factory.create(launchers, None, 'ABC', None)
        
        # assert
        self.assertIsNone(actual)

    def test_when_its_an_app_factory_loads_with_correct_launcher(self):
        self.test_when_its_an_app_factory_loads_with_correct_launcher_mocked()
        
    @patch('resources.executors.ExecutorFactory')    
    def test_when_its_an_app_factory_loads_with_correct_launcher_mocked(self, mock_exeFactory):

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
        launcher = factory.create(launchers, None, 'ABC', None)
        
        # assert        
        actual = launcher.__class__.__name__
        expected = 'ApplicationLauncher'
        self.assertEqual(actual, expected)
        
    def test_if_app_launcher_will_correctly_passthrough_parameters_when_launching(self):
        self.test_if_app_launcher_will_correctly_passthrough_parameters_when_launching_mocked()

    @patch('resources.executors.ExecutorFactory')
    def test_if_app_launcher_will_correctly_passthrough_parameters_when_launching_mocked(self, mock_exeFactory):

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
        launcher = factory.create(launchers, None, 'ABC', None)

        # act
        launcher.launch()

        # assert
        self.assertEqual(expectedApp, mock.actualApplication.getOriginalPath())
        self.assertEqual(expectedArgs, mock.actualArgs)
        
    def test_if_app_launcher_will_correctly_alter_arguments_when_launching(self):
        self.test_if_app_launcher_will_correctly_alter_arguments_when_launching_mocked()

    @patch('resources.executors.ExecutorFactory')
    def test_if_app_launcher_will_correctly_alter_arguments_when_launching_mocked(self, mock_exeFactory):

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
        launcher = factory.create(launchers, None, 'ABC', None)

        # act
        launcher.launch()

        # assert
        self.assertEqual(expectedApp, mock.actualApplication.getOriginalPath())
        self.assertEqual(expectedArgs, mock.actualArgs)

    def test_when_using_romids_the_factory_will_get_the_correct_launcher(self):
        self.test_when_using_romids_the_factory_will_get_the_correct_launcher_mocked()
    
    @patch('resources.romsets.RomSetFactory')
    @patch('resources.executors.ExecutorFactory')
    def test_when_using_romids_the_factory_will_get_the_correct_launcher_mocked(self, mock_exeFactory, mock_romsFactory):
        
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

        mock_romsFactory.create.return_value = FakeRomSet(rom)
        mock = FakeExecutor(None)
        mock_exeFactory.create.return_value = mock

        settings = {}
        settings['lirc_state'] = True
        settings['escape_romfile'] = True

        # act
        factory = LauncherFactory(settings, mock_romsFactory, mock_exeFactory)
        launcher = factory.create(launchers, None, 'ABC', 'qqqq')
        
        # assert
        actual = launcher.__class__.__name__
        expected = 'StandardRomLauncher'
        self.assertEqual(actual, expected)

    def test_if_rom_launcher_will_correctly_passthrough_the_application_when_launching(self):
        self.test_if_rom_launcher_will_correctly_passthrough_the_application_when_launching_mocked()
        
    @patch('resources.romsets.RomSetFactory')
    @patch('resources.executors.ExecutorFactory')
    def test_if_rom_launcher_will_correctly_passthrough_the_application_when_launching_mocked(self, mock_exeFactory, mock_romsFactory):
        
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
        expectedArgs = '-a -b -c -d -e testing.zip -yes'

        factory = LauncherFactory(settings, mock_romsFactory, mock_exeFactory)
        launcher = factory.create(launchers, 'CATX', 'ABC', 'qqqq')

        # act
        launcher.launch()

        # assert
        self.assertEqual(expected, mock.actualApplication.getOriginalPath())
        self.assertEqual(expectedArgs, mock.actualArgs)

    def test_if_rom_launcher_will_use_the_multidisk_launcher_when_romdata_has_disks_field_filled_in(self):
        self.test_if_rom_launcher_will_use_the_multidisk_launcher_when_romdata_has_disks_field_filled_in_mocked()
        
    @patch('resources.romsets.RomSetFactory')
    @patch('resources.executors.ExecutorFactory')
    def test_if_rom_launcher_will_use_the_multidisk_launcher_when_romdata_has_disks_field_filled_in_mocked(self, mock_exeFactory, mock_romsFactory):
        
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
        launcher = factory.create(launchers, None, 'ABC', 'qqqq')
        
        # assert        
        actual = launcher.__class__.__name__
        expected = 'MultiDiscRomLauncher'
        self.assertEqual(actual, expected)

    def test_if_rom_launcher_will_apply_the_correct_disc_in_a_multidisc_situation(self):
        self.test_if_rom_launcher_will_apply_the_correct_disc_in_a_multidisc_situation_mocked()
        
    @patch('resources.romsets.RomSetFactory')
    @patch('resources.launchers.xbmcgui.Dialog.select')
    @patch('resources.executors.ExecutorFactory')
    def test_if_rom_launcher_will_apply_the_correct_disc_in_a_multidisc_situation_mocked(self, mock_exeFactory, mock_dialog, mock_romsFactory):

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
        launcher = factory.create(launchers, 'CATX', 'ABC', 'qqqq')

        # act
        launcher.launch()

        # assert
        self.assertEqual(expectedArgs, mock.actualArgs)

class FakeRomSet(RomSet):

    def __init__(self, rom):
        self.rom = rom

    def romSetFileExists():
        return True
            
    def loadRoms(self):
        return None

    def loadRom(self, romId):
        return self.rom

    def saveRoms(self, roms):
        pass

class FakeExecutor(Executor):
    
    def execute(self, application, arguments):
        self.actualApplication = application
        self.actualArgs = arguments
        pass


if __name__ == '__main__':
   unittest.main()
