from abc import ABCMeta, abstractmethod

# --- Kodi stuff ---
import xbmc, xbmcgui

# --- Modules/packages in this plugin ---
from utils import *

#
# The wizardpage implementations can be used to chain a collection of
# different kodi dialogs and use them to fill a dictionary with user input.
#
# Each wizardpage accepts a key which will correspond with the key/value combination
# in the dictionary. It will also accept a customFunction (delegate or lambda) which
# will be called after the dialog has been shown. Depending on the type of dialog some
# other arguments might be needed.
# 
# The chaining is implemented by applying the decorator pattern and injecting
# the previous wizardpage in each new one.
# You can then call the method 'runWizard()' on the last created instance.
# 
class WizardPage():
    __metaclass__ = ABCMeta
    
    def __init__(self, property_key, title, decoratorPage,  customFunction = None):
        self.title = title
        self.property_key = property_key
        self.decoratorPage = decoratorPage
        self.customFunction = customFunction

    def runWizard(self, properties):

        if not self.show(properties):
            log_warning('User stopped wizard')
            return None
        
        return properties
        
    @abstractmethod
    def show(self, properties):
        return True

#
# Wizard page which accepts a keyboard user input.
# 
class KeyboardWizardPage(WizardPage):
    
    def show(self, properties):

        if self.decoratorPage is not None:
            if not self.decoratorPage.show(properties):
                return False

        log_debug('Executing keyboard wizard page for key: {0}'.format(self.property_key))
        originalText = properties[self.property_key] if self.property_key in properties else ''

        textInput = xbmc.Keyboard(originalText, self.title)
        textInput.doModal()
        if not textInput.isConfirmed(): 
            return False

        output = textInput.getText().decode('utf-8')

        if self.customFunction is not None:
            output = self.customFunction(output, properties)

        properties[self.property_key] = output
        log_debug('Assigned properties[{0}] value: {1}'.format(self.property_key, output))

        return True
  
#
# Wizard page which shows a list of options to select from.
# 
class SelectionWizardPage(WizardPage):

    def __init__(self, property_key, title, options, decoratorPage, customFunction = None):
        
        self.options = options
        super(SelectionWizardPage, self).__init__(property_key, title, decoratorPage, customFunction)
       
    def show(self, properties):
        
        if self.decoratorPage is not None:
            if not self.decoratorPage.show(properties):
                return False
            
        log_debug('Executing selection wizard page for key: {0}'.format(self.property_key))
        dialog = xbmcgui.Dialog()
        selection = dialog.select(self.title, self.options)

        if selection < 0:
           return False
       
        output = self.options[selection]
        if self.customFunction is not None:
            output = self.customFunction(selection, properties)

        properties[self.property_key] = output
        log_debug('Assigned properties[{0}] value: {1}'.format(self.property_key, output))
        return True

  
#
# Wizard page which shows a list of options to select from.
# In comparison with the normal SelectionWizardPage, this version allows a dictionary or key/value
# list as the selectable options. The selected key will be used.
# 
class DictionarySelectionWizardPage(WizardPage):

    def __init__(self, property_key, title, options, decoratorPage, customFunction = None):
        
        self.options = options
        super(SelectionWizardPage, self).__init__(property_key, title, decoratorPage, customFunction)
       
    def show(self, properties):
        
        if self.decoratorPage is not None:
            if not self.decoratorPage.show(properties):
                return False
            
        log_debug('Executing dict selection wizard page for key: {0}'.format(self.property_key))
        dialog = xbmcgui.DictionaryDialog()
        output = dialog.select(self.title, self.options)

        if output is None:
           return False
       
        if self.customFunction is not None:
            output = self.customFunction(output, properties)

        properties[self.property_key] = output
        log_debug('Assigned properties[{0}] value: {1}'.format(self.property_key, output))
        return True
    
#
# Wizard page which shows a filebrowser.
# 
class FileBrowseWizardPage(WizardPage):
    
    def __init__(self, property_key, title, browseType, filter, decoratorPage, customFunction = None):
        
        self.browseType = browseType
        self.filter = filter
        super(FileBrowseWizardPage, self).__init__(property_key, title, decoratorPage, customFunction)
       
    def show(self, properties):
        
        if self.decoratorPage is not None:
            if not self.decoratorPage.show(properties):
                return False
            
        log_debug('Executing file browser wizard page for key: {0}'.format(self.property_key))
        originalPath = properties[self.property_key] if self.property_key in properties else ''
       
        output = xbmcgui.Dialog().browse(self.browseType, self.title, 'files', self.filter, False, False, originalPath).decode('utf-8')

        if not output:
           return False
       
        if self.customFunction is not None:
            output = self.customFunction(output, properties)

        properties[self.property_key] = output
        log_debug('Assigned properties[{0}] value: {1}'.format(self.property_key, output))
        return True
    
#
# Wizard page which does nothing or shows anything.
# It only sets a certain property with the predefined value.
# 
class DummyWizardPage(WizardPage):

    def __init__(self, property_key, predefinedValue, decoratorPage, customFunction = None):
        
        self.predefinedValue = predefinedValue
        super(DummyWizardPage, self).__init__(property_key, None, decoratorPage, customFunction)

    def show(self, properties):
        
        if self.decoratorPage is not None:
            if not self.decoratorPage.show(properties):
                return False
            
        log_debug('Executing dummy wizard page for key: {0}'.format(self.property_key))
        output = self.predefinedValue
        if self.customFunction is not None:
            output = self.customFunction(output, properties)

        properties[self.property_key] = output
        log_debug('Assigned properties[{0}] value: {1}'.format(self.property_key, output))
        return True

# 
# Kodi dialog with select box based on a dictionary
# 
class DictionaryDialog():
    
    def __init__(self):
        self.dialog = xbmcgui.Dialog()

    def select(self, title, dictOptions):
        
        selection = self.dialog.select(title, dictOptions.values())

        if selection < 0:
            return None

        return dictOptions.keys()[selection]