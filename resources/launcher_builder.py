
from collections import OrderedDict

# --- Kodi stuff ---
import xbmc, xbmcgui

# --- Modules/packages in this plugin ---
from constants import *
from utils import *
from utils_kodi import *
from disk_IO import *
from platforms import *
from gamestream import *

class launcherBuilder():

    def __init__(self, settings, categories_file_path):
        self.settings = settings
        self.categories_file_path = categories_file_path

    def createLauncher(self, categoryID, launchers, categories):
    
        # >> If categoryID not found user is creating a new launcher using the context menu
        # >> of a launcher in addon root.
        if categoryID not in categories:
            log_info('Category ID not found. Creating laucher in addon root.')
            launcher_categoryID = VCATEGORY_ADDONROOT_ID
        else:
            # --- Ask user if launcher is created on selected category or on root menu ---
            category_name = categories[categoryID]['m_name']
            options = {}
            options[categoryID]             = 'Create Launcher in "{0}" category'.format(category_name)
            options[VCATEGORY_ADDONROOT_ID] = 'Create Launcher in addon root'

            dialog = DictionaryDialog()
            launcher_categoryID = dialog.select('Choose Launcher category', options)

        if launcher_categoryID is None:
            return
       
        # --- Show "Create New Launcher" dialog ---
        typeOptions = OrderedDict()
        typeOptions[LAUNCHER_STANDALONE]  = 'Standalone launcher (Game/Application)'
        typeOptions[LAUNCHER_FAVOURITES]  = 'Kodi favourite launcher'
        typeOptions[LAUNCHER_ROM]         = 'ROM launcher (Emulator)'
        typeOptions[LAUNCHER_RETROPLAYER] = 'ROM launcher (Kodi Retroplayer)'
        typeOptions[LAUNCHER_RETROARCH]   = 'ROM launcher (Retroarch)'
        typeOptions[LAUNCHER_NVGAMESTREAM] = 'Nvidia GameStream'

        if is_windows():
            typeOptions[LAUNCHER_LNK] = 'LNK launcher (Windows only)'

        if not is_android():
            typeOptions[LAUNCHER_STEAM]       = 'Steam launcher'

        dialog = DictionaryDialog()
        launcher_type = dialog.select('Create New Launcher', typeOptions)
        if type is None: return
    
        log_info('_command_add_new_launcher() New launcher (launcher_type = {0})'.format(launcher_type))

        launcherID       = misc_generate_random_SID()
        launcher         = fs_new_launcher()
        launcher['id']   = launcherID
        launcher['type'] = launcher_type
                    
        # --- Standalone launcher ---
        if launcher_type == LAUNCHER_STANDALONE:

            wizard = DummyWizardDialog('categoryID', launcher_categoryID, None)
            wizard = DummyWizardDialog('type', launcher_type, wizard)
            wizard = FileBrowseWizardDialog('application', 'Select the launcher application', 1, get_appbrowser_filter, wizard)
            wizard = DummyWizardDialog('args', '', wizard)
            wizard = KeyboardWizardDialog('args', 'Application arguments', wizard)
            wizard = DummyWizardDialog('m_name', '', wizard, get_title_from_app_path)
            wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, get_title_from_app_path)
            wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
            
        # --- Standalone launcher ---
        if launcher_type == LAUNCHER_FAVOURITES:

            wizard = DummyWizardDialog('categoryID', launcher_categoryID, None)
            wizard = DummyWizardDialog('type', launcher_type, wizard)
            wizard = DictionarySelectionWizardDialog('application', 'Select the favourite', get_kodi_favourites(), wizard)
            wizard = DummyWizardDialog('s_icon', '', wizard, get_icon_from_selected_favourite)
            wizard = DummyWizardDialog('m_name', '', wizard, get_title_from_selected_favourite)
            wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard)
            wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
            
        # --- ROM Launcher ---
        elif launcher_type == LAUNCHER_ROM:
        
            wizard = DummyWizardDialog('categoryID', launcher_categoryID, None)
            wizard = DummyWizardDialog('type', launcher_type, wizard)
            wizard = FileBrowseWizardDialog('application', 'Select the launcher application', 1, get_appbrowser_filter, wizard) 
            wizard = FileBrowseWizardDialog('rompath', 'Select the ROMs path', 0, '', wizard)
            wizard = DummyWizardDialog('romext', '', wizard, getExtensionsFromAppPath)
            wizard = KeyboardWizardDialog('romext','Set files extensions, use "|" as separator. (e.g lnk|cbr)', wizard)
            wizard = DummyWizardDialog('args', '', wizard, getArgumentsFromAppPath)
            wizard = KeyboardWizardDialog('args', 'Application arguments', wizard)
            wizard = DummyWizardDialog('m_name', '', wizard, get_title_from_app_path)
            wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, get_title_from_app_path)
            wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
            wizard = DummyWizardDialog('assets_path', '', wizard, get_value_from_rompath)
            wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard) 

        # --- Retroplayer Launcher ---
        elif launcher_type == LAUNCHER_RETROPLAYER:
            wizard = DummyWizardDialog('categoryID', launcher_categoryID, None)
            wizard = DummyWizardDialog('type', launcher_type, wizard)
            wizard = DummyWizardDialog('application', RETROPLAYER_LAUNCHER_APP_NAME, wizard)
            wizard = FileBrowseWizardDialog('rompath', 'Select the ROMs path', 0, get_appbrowser_filter, wizard) 
            wizard = DummyWizardDialog('romext', '', wizard, getExtensionsFromAppPath)
            wizard = KeyboardWizardDialog('romext','Set files extensions, use "|" as separator. (e.g lnk|cbr)', wizard)
            wizard = DummyWizardDialog('args', '%rom%', wizard)
            wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, get_title_from_app_path)
            wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
            wizard = DummyWizardDialog('assets_path', '', wizard, get_value_from_rompath)
            wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard) 
            
        # --- LNK launcher (Windows only) ---
        elif launcher_type == LAUNCHER_LNK:
            wizard = DummyWizardDialog('categoryID', launcher_categoryID, None)
            wizard = DummyWizardDialog('type', launcher_type, wizard)
            wizard = DummyWizardDialog('application', LNK_LAUNCHER_APP_NAME, wizard)
            wizard = FileBrowseWizardDialog('rompath', 'Select the LNKs path', 0, '', wizard) 
            wizard = DummyWizardDialog('romext', 'lnk', wizard)
            wizard = DummyWizardDialog('args', '%rom%', wizard)
            wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, get_title_from_app_path)
            wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
            wizard = DummyWizardDialog('assets_path', '', wizard, get_value_from_rompath)
            wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard) 
            
        # --- Retroarch launcher ---
        elif launcher_type == LAUNCHER_RETROARCH:
            
            # >> If Retroarch System dir not configured or found abort.
            sys_dir_FN = FileNameFactory.create(self.settings['io_retroarch_sys_dir'])
            if not sys_dir_FN.exists():
                kodi_dialog_OK('Retroarch System directory not found. Please configure it.')
                return

            wizard = DummyWizardDialog('categoryID', launcher_categoryID, None)
            wizard = DummyWizardDialog('type', launcher_type, wizard)
            wizard = DummyWizardDialog('application', self.settings['io_retroarch_sys_dir'], wizard)
            wizard = DictionarySelectionWizardDialog('retro_config', 'Select the configuration', get_available_retroarch_configurations, wizard)
            wizard = FileBrowseWizardDialog('retro_config', 'Select the configuration', 0, '', wizard, None, user_selected_custom_browsing) 
            wizard = DictionarySelectionWizardDialog('retro_core_info', 'Select the core', get_available_retroarch_cores, wizard, load_selected_core_info)
            wizard = KeyboardWizardDialog('retro_core_info', 'Enter path to core file', wizard, load_selected_core_info, user_selected_custom_browsing)
            wizard = FileBrowseWizardDialog('rompath', 'Select the ROMs path', 0, '', wizard) 
            wizard = KeyboardWizardDialog('romext','Set files extensions, use "|" as separator. (e.g nes|zip)', wizard)
            wizard = DummyWizardDialog('args', get_default_retroarch_arguments(), wizard)
            wizard = KeyboardWizardDialog('args', 'Extra application arguments', wizard)
            wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, get_title_from_app_path)
            wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
            wizard = DummyWizardDialog('assets_path', '', wizard, get_value_from_rompath)
            wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard) 
    
        # --- Steam launcher ---
        elif launcher_type == LAUNCHER_STEAM:
            wizard = DummyWizardDialog('categoryID', launcher_categoryID, None)
            wizard = DummyWizardDialog('type', launcher_type, wizard)
            wizard = DummyWizardDialog('application', 'Steam', wizard)
            wizard = KeyboardWizardDialog('steamid','Steam ID', wizard)
            wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, get_title_from_app_path)
            wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
            wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard)
            wizard = DummyWizardDialog('rompath', '', wizard, getValueFromAssetsPath)         
            
        # --- NVidia Gamestream launcher ---
        elif launcher_type == LAUNCHER_NVGAMESTREAM:
            info_txt = 'To pair with your Geforce Experience Computer we need to make use of valid certificates. '
            info_txt += 'Unfortunately at this moment we cannot create these certificates directly from within Kodi.\n'
            info_txt += 'Please read the wiki for details how to create them before you go further.'

            wizard = DummyWizardDialog('categoryID', launcher_categoryID, None)
            wizard = DummyWizardDialog('type', launcher_type, wizard)
            wizard = FormattedMessageWizardDialog('certificates_path', 'Pairing with Gamestream PC', info_txt, wizard)
            wizard = DictionarySelectionWizardDialog('application', 'Select the client', {'NVIDIA': 'Nvidia', 'MOONLIGHT': 'Moonlight'}, wizard, check_if_selected_gamestream_client_exists, lambda p: is_android())
            wizard = DictionarySelectionWizardDialog('application', 'Select the client', {'JAVA': 'Moonlight-PC (java)', 'EXE': 'Moonlight-Chrome (not supported yet)'}, wizard, None, lambda p: not is_android())
            wizard = FileBrowseWizardDialog('application', 'Select the Gamestream client jar', 1, get_appbrowser_filter, wizard, None, lambda p: not is_android())
            wizard = KeyboardWizardDialog('args', 'Additional arguments', wizard, None, lambda p: not is_android())
            wizard = InputWizardDialog('server', 'Gamestream Server', xbmcgui.INPUT_IPADDRESS, wizard, validate_gamestream_server_connection)
            wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, get_title_from_app_path)
            wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard)
            wizard = DummyWizardDialog('rompath', '', wizard, getValueFromAssetsPath)   
            # Pairing with pin code will be postponed untill crypto and certificate support in kodi
            # wizard = DummyWizardDialog('pincode', None, wizard, generatePairPinCode)
            wizard = DummyWizardDialog('certificates_path', None, wizard, try_to_resolve_path_to_nvidia_certificates)
            wizard = FileBrowseWizardDialog('certificates_path', 'Select the path with valid certificates', 0, '', wizard, validate_nvidia_certificates) 
            wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)


        # --- Create new launcher. categories.xml is save at the end of this function ---
        # NOTE than in the database original paths are always stored.
        launcher = wizard.runWizard(launcher)
        if not launcher:
            return
              
        if launcher_supports_roms(launcher_type):   
        
            # Choose launcher ROM XML filename. There may be launchers with same name in different categories, or
            # even launcher with the same name in the same category.
            category_name   = categories[launcher_categoryID]['m_name'] if launcher_categoryID in categories else VCATEGORY_ADDONROOT_ID
            roms_base_noext = fs_get_ROMs_basename(category_name, launcher['m_name'], launcherID)
            launcher['roms_base_noext'] = roms_base_noext
            
            # --- Selected asset path ---
            # A) User chooses one and only one assets path
            # B) If this path is different from the ROM path then asset naming scheme 1 is used.
            # B) If this path is the same as the ROM path then asset naming scheme 2 is used.
            # >> Create asset directories. Function detects if we are using naming scheme 1 or 2.
            # >> launcher is edited using Python passing by assignment.
            assets_init_asset_dir(FileNameFactory.create(launcher['assets_path']), launcher)

        launcher['timestamp_launcher'] = time.time()
        launchers[launcherID] = launcher
        msg = 'Created {0} {1}'.format(get_launcher_type_name(launcher_type), launcher['m_name'])
        # >> Notify user
        kodi_notify(msg)
        
        for key in sorted(launcher.iterkeys()):
            log_debug('launcher[{}] = {}'.format(key, launcher[key]))

        # >> If this point is reached then changes to metadata/images were made.
        # >> Save categories and update container contents so user sees those changes inmediately.
        fs_write_catfile(self.categories_file_path, categories, launchers)

def get_launcher_type_name(launcher_type):
    
    if launcher_type == LAUNCHER_STANDALONE:
        return "Standalone launcher"
    
    if launcher_type == LAUNCHER_FAVOURITES:
        return 'Kodi favourite launcher'

    if launcher_type == LAUNCHER_ROM:
        return "ROM launcher"

    if launcher_type == LAUNCHER_RETROARCH:
        return "Retroarch launcher"

    if launcher_type == LAUNCHER_RETROPLAYER:
        return "Retroplayer launcher"

    if launcher_type == LAUNCHER_LNK:
        return "LNK launcher"

    if launcher_type == LAUNCHER_STEAM:
        return "Steam launcher"
    
    if launcher_type == LAUNCHER_NVGAMESTREAM:
        return "Nvidia GameStream launcher"

def get_title_from_app_path(input, item_key, launcher):

    if input:
        return input

    app = launcher['application']
    appPath = FileNameFactory.create(app)

    title = appPath.getBase_noext()
    title_formatted = title.replace('.' + title.split('.')[-1], '').replace('.', ' ')
    return title_formatted

def getExtensionsFromAppPath(input, item_key ,launcher):
    
    if input:
        return input

    app = launcher['application']
    appPath = FileNameFactory.create(app)
    
    extensions = emudata_get_program_extensions(appPath.getBase())
    return extensions

def getArgumentsFromAppPath(input, item_key, launcher):
    
    if input:
        return input

    app = launcher['application']
    appPath = FileNameFactory.create(app)
    
    default_arguments = emudata_get_program_arguments(appPath.getBase())
    return default_arguments

def get_value_from_rompath(input, item_key, launcher):

    if input:
        return input

    romPath = launcher['rompath']
    return romPath

def getValueFromAssetsPath(input, item_key, launcher):

    if input:
        return input

    romPath = FileNameFactory.create(launcher['assets_path'])
    romPath = romPath.pjoin('games')

    return romPath.getOriginalPath()

def get_kodi_favourites():

    favourites = kodi_read_favourites()
    fav_options = {}

    for key in favourites:
        fav_options[key] = favourites[key][0]

    return fav_options

def get_icon_from_selected_favourite(input, item_key, launcher):

    fav_action = launcher['application']
    favourites = kodi_read_favourites()

    for key in favourites:
        if fav_action == key:
            return favourites[key][1]

    return 'DefaultProgram.png'

def get_title_from_selected_favourite(input, item_key, launcher):
    
    fav_action = launcher['application']
    favourites = kodi_read_favourites()

    for key in favourites:
        if fav_action == key:
            return favourites[key][0]

    return get_title_from_app_path(input, launcher)

def get_appbrowser_filter(item_key, launcher):
    
    if item_key in launcher:
        application = launcher[item_key]
        if application == 'JAVA':
            return '.jar'

    return '.bat|.exe|.cmd|.lnk' if is_windows() else ''

def generatePairPinCode(input, item_key, launcher):
    
    return gamestreamServer(None, None).generatePincode()

def check_if_selected_gamestream_client_exists(input, item_key, launcher):

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


def try_to_resolve_path_to_nvidia_certificates(input, item_key, launcher):
    
    path = GameStreamServer.try_to_resolve_path_to_nvidia_certificates()
    return path

def validate_nvidia_certificates(input, item_key, launcher):

    certificates_path = FileNameFactory.create(input)
    gs = GameStreamServer(input, certificates_path)
    if not gs.validate_certificates():
        kodi_notify_warn('Could not find certificates to validate. Make sure you already paired with the server with the Shield or Moonlight applications.')

    return certificates_path.getOriginalPath()


def validate_gamestream_server_connection(input, item_key, launcher):

    gs = GameStreamServer(input, None)
    if not gs.connect():
        kodi_notify_warn('Could not connect to gamestream server')

    launcher['server_id'] = gs.get_uniqueid()
    launcher['server_hostname'] = gs.get_hostname()

    log_debug('validate_gamestream_server_connection() Found correct gamestream server with id "{}" and hostname "{}"'.format(launcher['server_id'],launcher['server_hostname']))

    return input

def get_retroarch_app_folder(settings):
    
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

def get_available_retroarch_configurations(item_key, launcher):
    
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

def user_selected_custom_browsing(item_key, launcher):
    return launcher[item_key] == 'BROWSE'

def get_available_retroarch_cores(item_key, launcher):
    
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
    info_folder     = create_path_from_retroarch_setting(configuration['libretro_info_path'], parent_dir)
    cores_folder    = create_path_from_retroarch_setting(configuration['libretro_directory'], parent_dir)
        
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
        info_file = switch_core_to_info_file(file, info_folder)

        if not info_file.exists():
            log_warning('get_available_retroarch_cores() Cannot find "{}". Skipping core "{}"'.format(info_file.getOriginalPath(), file.getBase()))
            continue

        log_debug("get_available_retroarch_cores() using info '{0}'".format(info_file.getOriginalPath()))    
        core_info = info_file.readPropertyFile()
        cores[info_file.getOriginalPath()] = core_info['display_name']

    return cores

def create_path_from_retroarch_setting(path_from_setting, parent_dir):

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

def load_selected_core_info(input, item_key, launcher):

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
    cores_folder    = create_path_from_retroarch_setting(configuration['libretro_directory'], parent_dir)
    info_file       = FileNameFactory.create(input)
        
    if not cores_folder.exists():
        log_warning('Retroarch cores folder not found {}'.format(cores_folder.getOriginalPath()))
        kodi_notify_error('Retroarch cores folder not found {}'.format(cores_folder.getOriginalPath()))
        return ''

    core_file = switch_info_to_core_file(info_file, cores_folder, cores_ext)
    core_info = info_file.readPropertyFile()

    launcher[item_key]      = info_file.getOriginalPath()
    launcher['retro_core']  = core_file.getOriginalPath()
    launcher['romext']      = core_info['supported_extensions']
    launcher['platform']    = core_info['systemname']
    launcher['m_developer'] = core_info['manufacturer']
    launcher['m_name']      = core_info['systemname']

    return input

def switch_core_to_info_file(core_file, info_folder):
    
    info_file = core_file.switchExtension('info')
   
    if is_android():
        info_file = info_folder.pjoin(info_file.getBase().replace('_android.', '.'))
    else:
        info_file = info_folder.pjoin(info_file.getBase())

    return info_file

def switch_info_to_core_file(info_file, cores_folder, cores_ext):
    
    core_file = info_file.switchExtension(cores_ext)

    if is_android():
        core_file = cores_folder.pjoin(core_file.getBase().replace('.', '_android.'))
    else:
        core_file = cores_folder.pjoin(core_file.getBase())

    return core_file

def get_default_retroarch_arguments():

    args = ''
    if is_android():
        args += '-e IME com.android.inputmethod.latin/.LatinIME -e REFRESH 60'

    return args
            