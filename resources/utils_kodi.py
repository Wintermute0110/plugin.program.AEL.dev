# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher miscellaneous functions
#

# Copyright (c) 2016-2017 Wintermute0110 <wintermute0110@gmail.com>
# Portions (c) 2010-2015 Angelscry
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

#
# Utility functions which DEPEND on Kodi modules
#

# --- Python standard library ---
from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
import sys, os, shutil, time, random, hashlib, urlparse

# --- Kodi modules ---
try:
    import xbmc, xbmcgui
except:
    from utils_kodi_standalone import *

# --- AEL modules ---
# >> utils.py and utils_kodi.py must not depend on any other AEL module to avoid circular dependencies.

# --- Constants ---------------------------------------------------------------
LOG_ERROR   = 0
LOG_WARNING = 1
LOG_INFO    = 2
LOG_VERB    = 3
LOG_DEBUG   = 4

# --- Internal globals --------------------------------------------------------
current_log_level = LOG_INFO
use_print_instead = False

# -------------------------------------------------------------------------------------------------
# Logging functions
# -------------------------------------------------------------------------------------------------
def set_log_level(level):
    global current_log_level
    current_log_level = level

def set_use_print(use_print):
    global use_print_instead   
    use_print_instead = use_print

# For Unicode stuff in Kodi log see http://forum.kodi.tv/showthread.php?tid=144677
#
def log_debug(str_text):
    if current_log_level >= LOG_DEBUG:
        # if it is str we assume it's "utf-8" encoded.
        # will fail if called with other encodings (latin, etc).
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')

        # At this point we are sure str_text is a unicode string.
        log_text = u'AEL DEBUG: ' + str_text
        log(log_text, LOG_VERB)

def log_verb(str_text):
    if current_log_level >= LOG_VERB:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = u'AEL VERB : ' + str_text
        log(log_text, LOG_VERB)

def log_info(str_text):
    if current_log_level >= LOG_INFO:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = u'AEL INFO : ' + str_text
        log(log_text, LOG_INFO)

def log_warning(str_text):
    if current_log_level >= LOG_WARNING:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = u'AEL WARN : ' + str_text
        log(log_text, LOG_WARNING)

def log_error(str_text):
    if current_log_level >= LOG_ERROR:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = u'AEL ERROR: ' + str_text
        log(log_text, LOG_ERROR)

def log(log_text, level):
    
    if use_print_instead:
        print(log_text.encode('utf-8'))
    else:
        xbmc.log(log_text.encode('utf-8'), level=xbmc.LOGERROR)
 
# -----------------------------------------------------------------------------
# Kodi notifications and dialogs
# -----------------------------------------------------------------------------
#
# Displays a modal dialog with an OK button. Dialog can have up to 3 rows of text, however first
# row is multiline.
# Call examples:
#  1) ret = kodi_dialog_OK('Launch ROM?')
#  2) ret = kodi_dialog_OK('Launch ROM?', title = 'AEL - Launcher')
#
def kodi_dialog_OK(row1, row2='', row3='', title = 'Advanced Emulator Launcher'):
    dialog = xbmcgui.Dialog()
    dialog.ok(title, row1, row2, row3)

#
# Returns True is YES was pressed, returns False if NO was pressed or dialog canceled.
def kodi_dialog_yesno(row1, row2='', row3='', title = 'Advanced Emulator Launcher'):
    dialog = xbmcgui.Dialog()
    ret = dialog.yesno(title, row1, row2, row3)

    return ret

#
# Displays a small box in the low right corner
#
def kodi_notify(text, title = 'Advanced Emulator Launcher', time = 5000):
    # --- Old way ---
    # xbmc.executebuiltin("XBMC.Notification(%s,%s,%s,%s)" % (title, text, time, ICON_IMG_FILE_PATH))

    # --- New way ---
    dialog = xbmcgui.Dialog()
    dialog.notification(title, text, xbmcgui.NOTIFICATION_INFO, time)

def kodi_notify_warn(text, title = 'Advanced Emulator Launcher warning', time = 7000):
    dialog = xbmcgui.Dialog()
    dialog.notification(title, text, xbmcgui.NOTIFICATION_WARNING, time)

#
# Do not use this function much because it is the same icon as when Python fails, and that may confuse the user.
#
def kodi_notify_error(text, title = 'Advanced Emulator Launcher error', time = 7000):
    dialog = xbmcgui.Dialog()
    dialog.notification(title, text, xbmcgui.NOTIFICATION_ERROR, time)

def kodi_busydialog_ON():
    xbmc.executebuiltin('ActivateWindow(busydialog)')

def kodi_busydialog_OFF():
    xbmc.executebuiltin('Dialog.Close(busydialog)')

def kodi_refresh_container():
    log_debug('kodi_refresh_container()')
    xbmc.executebuiltin('Container.Refresh')

def kodi_toogle_fullscreen():
    # >> Frodo and up compatible
    xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Input.ExecuteAction", "params":{"action":"togglefullscreen"}, "id":"1"}')

def kodi_kodi_read_favourites():
    favourites = []
    fav_names = []
    if os.path.isfile(FAVOURITES_PATH):
        fav_xml = parse(FAVOURITES_PATH)
        fav_doc = fav_xml.documentElement.getElementsByTagName( 'favourite' )
        for count, favourite in enumerate(fav_doc):
            try:
                fav_icon = favourite.attributes[ 'thumb' ].nodeValue
            except:
                fav_icon = "DefaultProgram.png"
            favourites.append((favourite.childNodes[ 0 ].nodeValue.encode('utf8','ignore'),
                               fav_icon.encode('utf8','ignore'),
                               favourite.attributes[ 'name' ].nodeValue.encode('utf8','ignore')))
            fav_names.append(favourite.attributes[ 'name' ].nodeValue.encode('utf8','ignore'))

    return favourites, fav_names


#
# The wizarddialog implementations can be used to chain a collection of
# different kodi dialogs and use them to fill a dictionary with user input.
#
# Each wizarddialog accepts a key which will correspond with the key/value combination
# in the dictionary. It will also accept a customFunction (delegate or lambda) which
# will be called after the dialog has been shown. Depending on the type of dialog some
# other arguments might be needed.
# 
# The chaining is implemented by applying the decorator pattern and injecting
# the previous wizarddialog in each new one.
# You can then call the method 'runWizard()' on the last created instance.
# 
class WizardDialog():
    __metaclass__ = ABCMeta
    
    def __init__(self, property_key, title, decoratorDialog,  customFunction = None):
        self.title = title
        self.property_key = property_key
        self.decoratorDialog = decoratorDialog
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
# Wizard dialog which accepts a keyboard user input.
# 
class KeyboardWizardDialog(WizardDialog):
    
    def show(self, properties):

        if self.decoratorDialog is not None:
            if not self.decoratorDialog.show(properties):
                return False

        log_debug('Executing keyboard wizard dialog for key: {0}'.format(self.property_key))
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
# Wizard dialog which shows a list of options to select from.
# 
class SelectionWizardDialog(WizardDialog):

    def __init__(self, property_key, title, options, decoratorDialog, customFunction = None):
        
        self.options = options
        super(SelectionWizardDialog, self).__init__(property_key, title, decoratorDialog, customFunction)
       
    def show(self, properties):
        
        if self.decoratorDialog is not None:
            if not self.decoratorDialog.show(properties):
                return False
            
        log_debug('Executing selection wizard dialog for key: {0}'.format(self.property_key))
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
# Wizard dialog which shows a list of options to select from.
# In comparison with the normal SelectionWizardDialog, this version allows a dictionary or key/value
# list as the selectable options. The selected key will be used.
# 
class DictionarySelectionWizardDialog(WizardDialog):

    def __init__(self, property_key, title, options, decoratorDialog, customFunction = None):
        
        self.options = options
        super(SelectionWizardDialog, self).__init__(property_key, title, decoratorDialog, customFunction)
       
    def show(self, properties):
        
        if self.decoratorDialog is not None:
            if not self.decoratorDialog.show(properties):
                return False
            
        log_debug('Executing dict selection wizard dialog for key: {0}'.format(self.property_key))
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
# Wizard dialog which shows a filebrowser.
# 
class FileBrowseWizardDialog(WizardDialog):
    
    def __init__(self, property_key, title, browseType, filter, decoratorDialog, customFunction = None):
        
        self.browseType = browseType
        self.filter = filter
        super(FileBrowseWizardDialog, self).__init__(property_key, title, decoratorDialog, customFunction)
       
    def show(self, properties):
        
        if self.decoratorDialog is not None:
            if not self.decoratorDialog.show(properties):
                return False
            
        log_debug('Executing file browser wizard dialog for key: {0}'.format(self.property_key))
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
# Wizard dialog which does nothing or shows anything.
# It only sets a certain property with the predefined value.
# 
class DummyWizardDialog(WizardDialog):

    def __init__(self, property_key, predefinedValue, decoratorDialog, customFunction = None):
        
        self.predefinedValue = predefinedValue
        super(DummyWizardDialog, self).__init__(property_key, None, decoratorDialog, customFunction)

    def show(self, properties):
        
        if self.decoratorDialog is not None:
            if not self.decoratorDialog.show(properties):
                return False
            
        log_debug('Executing dummy wizard dialog for key: {0}'.format(self.property_key))
        output = self.predefinedValue
        if self.customFunction is not None:
            output = self.customFunction(output, properties)

        properties[self.property_key] = output
        log_debug('Assigned properties[{0}] value: {1}'.format(self.property_key, output))
        return True

# 
# Kodi dialog with select box based on a dictionary
# 
class DictionaryDialog(object):
    
    def __init__(self):
        self.dialog = xbmcgui.Dialog()

    def select(self, title, dictOptions):
        
        selection = self.dialog.select(title, dictOptions.values())

        if selection < 0:
            return None

        return dictOptions.keys()[selection]

class ProgressDialogStrategy(object):
    
    def __init__(self):

        self.progress = 0
        self.progressDialog = xbmcgui.DialogProgress()
        self.verbose = True

    def _startProgressPhase(self, title, message):        
        self.progressDialog.create(title, message)

    def _updateProgress(self, progress, message1 = None, message2 = None):
        
        self.progress = progress

        if not self.verbose:
            self.progressDialog.update(progress)
        else:
            self.progressDialog.update(progress, message1, message2)

    def _updateProgressMessage(self, message1, message2 = None):

        if not self.verbose:
            return

        self.progressDialog.update(self.progress, message1, message2)

    def _isProgressCanceled(self):
        return self.progressDialog.iscanceled()

    def _endProgressPhase(self, canceled=False):
        
        if not canceled:
            self.progressDialog.update(100)

        self.progressDialog.close()