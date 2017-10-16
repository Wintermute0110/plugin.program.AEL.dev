from abc import ABCMeta, abstractmethod

# --- Kodi stuff ---
import xbmc, xbmcgui

# --- Modules/packages in this plugin ---
from constants import *
from utils import *
from utils_kodi import *
from disk_IO import *
from platforms import *

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


class WizardPage():
    __metaclass__ = ABCMeta
    
    def __init__(self, launcher_key, title, decoratorPage,  customFunction = None):
        self.title = title
        self.launcher_key = launcher_key
        self.decoratorPage = decoratorPage
        self.customFunction = customFunction

    def runWizard(self):
        launcherID      = misc_generate_random_SID()
        launcher        = fs_new_launcher()
        launcher['id']  = launcherID

        self.show(launcher)
        
        launcher['timestamp_launcher'] = time.time()
        return launcher
        
    @abstractmethod
    def show(self, launcher):
        return launcher


class KeyboardWizardPage(WizardPage):
    
    def show(self, launcher):

        if self.decoratorPage is not None:
            self.decoratorPage.show(launcher)

        log_debug('Executing keyboard wizard page for key: {0}'.format(self.launcher_key))
        originalText = launcher[self.launcher_key] if self.launcher_key in launcher else ''

        textInput = xbmc.Keyboard(originalText, self.title)
        textInput.doModal()
        if not textInput.isConfirmed(): 
            return

        output = textInput.getText().decode('utf-8')

        if self.customFunction is not None:
            output = self.customFunction(output, launcher)

        launcher[self.launcher_key] = output
        log_debug('Assigned launcher[{0}] value: {1}'.format(self.launcher_key, output))
  
class ComboboxWizardPage(WizardPage):

    def __init__(self, launcher_key, title, options, decoratorPage, customFunction = None):
        
        self.options = options
        super(ComboboxWizardPage, self).__init__(launcher_key, title, decoratorPage, customFunction)
       
    def show(self, launcher):
        
        if self.decoratorPage is not None:
            self.decoratorPage.show(launcher)
            
        log_debug('Executing combobox wizard page for key: {0}'.format(self.launcher_key))
        dialog = xbmcgui.Dialog()
        selection = dialog.select(self.title, self.options)

        if selection < 0:
           return
       
        output = self.options[selection]
        if self.customFunction is not None:
            output = self.customFunction(selection, launcher)

        launcher[self.launcher_key] = output
        log_debug('Assigned launcher[{0}] value: {1}'.format(self.launcher_key, output))


class FileBrowseWizardPage(WizardPage):
    
    def __init__(self, launcher_key, title, browseType, decoratorPage, customFunction = None):
        
        self.browseType = browseType
        super(FileBrowseWizardPage, self).__init__(launcher_key, title, decoratorPage, customFunction)
       
    def show(self, launcher):
        
        if self.decoratorPage is not None:
            self.decoratorPage.show(launcher)
            
        log_debug('Executing file browser wizard page for key: {0}'.format(self.launcher_key))
        originalPath = launcher[self.launcher_key] if self.launcher_key in launcher else ''
       
        output = xbmcgui.Dialog().browse(self.browseType, self.title, 'files', '', False, False, originalPath).decode('utf-8')

        if not output:
           return
       
        if self.customFunction is not None:
            output = self.customFunction(output, launcher)

        launcher[self.launcher_key] = output
        log_debug('Assigned launcher[{0}] value: {1}'.format(self.launcher_key, output))


class DummyWizardPage(WizardPage):

    def __init__(self, launcher_key, predefinedValue, decoratorPage, customFunction = None):
        
        self.predefinedValue = predefinedValue
        super(DummyWizardPage, self).__init__(launcher_key, None, decoratorPage, customFunction)

    def show(self, launcher):
        
        if self.decoratorPage is not None:
            self.decoratorPage.show(launcher)
            
        log_debug('Executing dummy wizard page for key: {0}'.format(self.launcher_key))
        output = self.predefinedValue
        if self.customFunction is not None:
            output = self.customFunction(output, launcher)

        launcher[self.launcher_key] = output
        log_debug('Assigned launcher[{0}] value: {1}'.format(self.launcher_key, output))
