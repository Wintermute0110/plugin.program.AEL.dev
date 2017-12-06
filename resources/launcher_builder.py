
from collections import OrderedDict

# --- Kodi stuff ---
import xbmc, xbmcgui

# --- Modules/packages in this plugin ---
from constants import *
from utils import *
from utils_kodi import *
from disk_IO import *
from platforms import *

class launcherBuilder():

    def createLauncher(self, categoryID, launchers, categories, settings, categories_file_path):
    
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
        typeOptions[LAUNCHER_ROM]         = 'ROM launcher (Emulator)'
        typeOptions[LAUNCHER_RETROPLAYER] = 'ROM launcher (Kodi Retroplayer)'
        typeOptions[LAUNCHER_RETROARCH]   = 'ROM launcher (Retroarch)'
        typeOptions[LAUNCHER_STEAM]       = 'Steam launcher'
        if sys.platform == 'win32':
            typeOptions[LAUNCHER_LNK] = 'LNK launcher (Windows only)'

        dialog = DictionaryDialog()
        launcher_type = dialog.select('Create New Launcher', typeOptions)
        if type is None: return
    
        log_info('_command_add_new_launcher() New launcher (launcher_type = {0})'.format(launcher_type))

        launcherID       = misc_generate_random_SID()
        launcher         = fs_new_launcher()
        launcher['id']   = launcherID
        launcher['type'] = launcher_type

        filter = '.bat|.exe|.cmd|.lnk' if sys.platform == 'win32' else ''
            
        # --- Standalone launcher ---
        if launcher_type == LAUNCHER_STANDALONE:

            wizard = DummyWizardDialog('categoryID', launcher_categoryID, None)
            wizard = DummyWizardDialog('type', launcher_type, wizard)
            wizard = FileBrowseWizardDialog('application', 'Select the launcher application', 1, filter, wizard)
            wizard = DummyWizardDialog('args', '', wizard)
            wizard = KeyboardWizardDialog('args', 'Application arguments', wizard)
            wizard = DummyWizardDialog('m_name', '', wizard, getTitleFromAppPath)
            wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, getTitleFromAppPath)
            wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
            
        # --- ROM Launcher ---
        elif launcher_type == LAUNCHER_ROM:
        
            wizard = DummyWizardDialog('categoryID', launcher_categoryID, None)
            wizard = DummyWizardDialog('type', launcher_type, wizard)
            wizard = FileBrowseWizardDialog('application', 'Select the launcher application', 1, filter, wizard) 
            wizard = FileBrowseWizardDialog('rompath', 'Select the ROMs path', 0, '', wizard)
            wizard = DummyWizardDialog('romext', '', wizard, getExtensionsFromAppPath)
            wizard = KeyboardWizardDialog('romext','Set files extensions, use "|" as separator. (e.g lnk|cbr)', wizard)
            wizard = DummyWizardDialog('args', '', wizard, getArgumentsFromAppPath)
            wizard = KeyboardWizardDialog('args', 'Application arguments', wizard)
            wizard = DummyWizardDialog('m_name', '', wizard, getTitleFromAppPath)
            wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, getTitleFromAppPath)
            wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
            wizard = DummyWizardDialog('assets_path', '', wizard, getValueFromRomPath)
            wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard) 

        # --- Retroplayer Launcher ---
        elif launcher_type == LAUNCHER_RETROPLAYER:
            wizard = DummyWizardDialog('categoryID', launcher_categoryID, None)
            wizard = DummyWizardDialog('type', launcher_type, wizard)
            wizard = DummyWizardDialog('application', RETROPLAYER_LAUNCHER_APP_NAME, wizard)
            wizard = FileBrowseWizardDialog('rompath', 'Select the ROMs path', 0, filter, wizard) 
            wizard = DummyWizardDialog('romext', '', wizard, getExtensionsFromAppPath)
            wizard = KeyboardWizardDialog('romext','Set files extensions, use "|" as separator. (e.g lnk|cbr)', wizard)
            wizard = DummyWizardDialog('args', '%rom%', wizard)
            wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, getTitleFromAppPath)
            wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
            wizard = DummyWizardDialog('assets_path', '', wizard, getValueFromRomPath)
            wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard) 
            
        # --- LNK launcher (Windows only) ---
        elif launcher_type == LAUNCHER_LNK:
            wizard = DummyWizardDialog('categoryID', launcher_categoryID, None)
            wizard = DummyWizardDialog('type', launcher_type, wizard)
            wizard = DummyWizardDialog('application', LNK_LAUNCHER_APP_NAME, wizard)
            wizard = FileBrowseWizardDialog('rompath', 'Select the LNKs path', 0, '', wizard) 
            wizard = DummyWizardDialog('romext', 'lnk', wizard)
            wizard = DummyWizardDialog('args', '%rom%', wizard)
            wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, getTitleFromAppPath)
            wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
            wizard = DummyWizardDialog('assets_path', '', wizard, getValueFromRomPath)
            wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard) 
            
        # --- Retroarch launcher ---
        elif launcher_type == LAUNCHER_RETROARCH:
            
            # >> If Retroarch System dir not configured or found abort.
            sys_dir_FN = FileName(settings['io_retroarch_sys_dir'])
            if not sys_dir_FN.exists():
                kodi_dialog_OK('Retroarch System directory not found. Please configure it.')
                return

            wizard = DummyWizardDialog('categoryID', launcher_categoryID, None)
            wizard = DummyWizardDialog('type', launcher_type, wizard)
            wizard = DummyWizardDialog('application', settings['io_retroarch_sys_dir'], wizard)
            wizard = SelectionWizardDialog('core', 'Select the core', get_available_retroarch_cores(settings), wizard)
            wizard = FileBrowseWizardDialog('rompath', 'Select the ROMs path', 0, wizard) 
            wizard = DummyWizardDialog('romext', '', wizard, getExtensionsFromAppPath)
            wizard = KeyboardWizardDialog('romext','Set files extensions, use "|" as separator. (e.g lnk|cbr)', wizard)
            wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, getTitleFromAppPath)
            wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
            wizard = DummyWizardDialog('assets_path', '', wizard, getValueFromRomPath)
            wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard) 
    
        # --- Steam launcher ---
        elif launcher_type == LAUNCHER_STEAM:
            wizard = DummyWizardDialog('categoryID', launcher_categoryID, None)
            wizard = DummyWizardDialog('type', launcher_type, wizard)
            wizard = DummyWizardDialog('application', 'Steam', wizard)
            wizard = KeyboardWizardDialog('steamid','Steam ID', wizard)
            wizard = KeyboardWizardDialog('m_name','Set the title of the launcher', wizard, getTitleFromAppPath)
            wizard = SelectionWizardDialog('platform', 'Select the platform', AEL_platform_list, wizard)
            wizard = FileBrowseWizardDialog('assets_path', 'Select asset/artwork directory', 0, '', wizard)
            wizard = DummyWizardDialog('rompath', '', wizard, getValueFromAssetsPath)         

        # --- Create new launcher. categories.xml is save at the end of this function ---
        # NOTE than in the database original paths are always stored.
        launcher = wizard.runWizard(launcher)
        if not launcher:
            return

        launcher['timestamp_launcher'] = time.time()
      
        # Choose launcher ROM XML filename. There may be launchers with same name in different categories, or
        # even launcher with the same name in the same category.
        if launcher_type is not LAUNCHER_STANDALONE:        
            category_name   = categories[launcher_categoryID]['m_name'] if launcher_categoryID in categories else VCATEGORY_ADDONROOT_ID
            roms_base_noext = fs_get_ROMs_basename(category_name, launcher['m_name'], launcherID)
            launcher['roms_base_noext'] = roms_base_noext
            
        # --- Selected asset path ---
        # A) User chooses one and only one assets path
        # B) If this path is different from the ROM path then asset naming scheme 1 is used.
        # B) If this path is the same as the ROM path then asset naming scheme 2 is used.
        # >> Create asset directories. Function detects if we are using naming scheme 1 or 2.
        # >> launcher is edited using Python passing by assignment.
        assets_init_asset_dir(FileName(launcher['assets_path']), launcher)

        launchers[launcherID] = launcher
        # >> Notify user
        kodi_notify('Created {0} {1}'.format(getLauncherTypeName(launcher_type), launcher['m_name']))

        # >> If this point is reached then changes to metadata/images were made.
        # >> Save categories and update container contents so user sees those changes inmediately.
        fs_write_catfile(categories_file_path, categories, launchers)

def getLauncherTypeName(launcher_type):
    
    if launcher_type == LAUNCHER_STANDALONE:
        return "Standalone launcher"

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

def getTitleFromAppPath(input, launcher):

    if input:
        return input

    app = launcher['application']
    appPath = FileName(app)

    title = appPath.getBase_noext()
    title_formatted = title.replace('.' + title.split('.')[-1], '').replace('.', ' ')
    return title_formatted

def getExtensionsFromAppPath(input ,launcher):
    
    if input:
        return input

    app = launcher['application']
    appPath = FileName(app)
    
    extensions = emudata_get_program_extensions(appPath.getBase())
    return extensions

def getArgumentsFromAppPath(input, launcher):
    
    if input:
        return input

    app = launcher['application']
    appPath = FileName(app)
    
    default_arguments = emudata_get_program_arguments(appPath.getBase())
    return default_arguments

def getValueFromRomPath(input, launcher):

    if input:
        return input

    romPath = launcher['rompath']
    return romPath

def getValueFromAssetsPath(input, launcher):

    if input:
        return input

    romPath = FileName(launcher['assets_path'])
    romPath = romPath.pjoin('games')

    return romPath.getOriginalPath()

def get_available_retroarch_cores(settings):

    cores = []
    
    if sys.platform == 'win32':
        retroarchFolder = FileName(settings['io_retroarch_sys_dir'])
        retroarchFolder.append('cores\\')
        log_debug("get_available_retroarch_cores() scanning path '{0}'".format(retroarchFolder.getOriginalPath()))

        if retroarchFolder.exists():
            files = retroarchFolder.scanFilesInPathAsFileNameObjects('*.dll')
            for file in files:
                log_debug("get_available_retroarch_cores() adding core '{0}'".format(file.getOriginalPath()))
                cores.append(file.getBase())

            return cores

    if sys.platform.startswith('linux'):
        androidFolder = FileName('/data/com.retroarch/cores/')
        log_debug("get_available_retroarch_cores() scanning path '{0}'".format(androidFolder.getOriginalPath()))

        if androidFolder.exists():
            files = androidFolder.scanFilesInPathAsFileNameObjects('*.so')
            for file in files:
                log_debug("get_available_retroarch_cores() adding core '{0}'".format(file.getOriginalPath()))
                cores.append(file.getBase())

            return cores

    return cores