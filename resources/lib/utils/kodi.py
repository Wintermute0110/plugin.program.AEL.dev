# -*- coding: utf-8 -*-
#
import collections
import logging
import json
import pprint

import xbmc
import xbmcgui

from resources.lib import globals
from resources.lib.utils import text

logger = logging.getLogger(__name__)

#
# Access Kodi JSON-RPC interface in an easy way.
# Returns a dictionary with the parsed response 'result' field.
#
# Query input:
#
# {
#     "id" : 1,
#     "jsonrpc" : "2.0",
#     "method" : "Application.GetProperties",
#     "params" : { "properties" : ["name", "version"] }
# }
#
# Query response:
#
# {
#     "id" : 1,
#     "jsonrpc" : "2.0",
#     "result" : {
#         "name" : "Kodi",
#         "version" : {"major":17,"minor":6,"revision":"20171114-a9a7a20","tag":"stable"}
#     }
# }
#
# Query response ERROR:
# {
#     "id" : null,
#     "jsonrpc" : "2.0",
#     "error" : { "code":-32700, "message" : "Parse error."}
# }
#
def jsonrpc_query(method=None, params=None, verbose = False):
    if not method:
        return {}
    query = {
        "jsonrpc": "2.0",
        "method": method,
        "id": 1}
    if params:
        query["params"] = params
    try:
        jrpc = xbmc.executeJSONRPC(json.dumps(query))
        response = json.loads(jrpc)
        if verbose:
            logger.debug('jsonrpc_query() response = \n{}'.format(pprint.pformat(response)))
    except Exception as exc:
        logger.error(u'jsonrpc_query(): JSONRPC Error:\n{}'.format(exc), 1)
        response = {}
    return response

def event(sender=globals.addon_id, method='test', data=None):

    ''' Data is a dictionary.
    '''
    sender = sender or "plugin.program.AEL"
    data = data or {}
    data = json.dumps(data)

    xbmc.executebuiltin('NotifyAll({}, {}, {})'.format(sender, method, data))
    logger.debug("event(): {}/{} => {}".format(sender, method, data))

#
# Displays a small box in the low right corner
#
def notify(text, title = 'Advanced Emulator Launcher', time = 5000):
    # --- Old way ---
    # xbmc.executebuiltin("XBMC.Notification(%s,%s,%s,%s)" % (title, text, time, ICON_IMG_FILE_PATH))

    # --- New way ---
    xbmcgui.Dialog().notification(title, text, xbmcgui.NOTIFICATION_INFO, time)

def notify_warn(text, title = 'Advanced Emulator Launcher warning', time = 7000):
    xbmcgui.Dialog().notification(title, text, xbmcgui.NOTIFICATION_WARNING, time)

#
# Do not use this function much because it is the same icon as when Python fails, and that may confuse the user.
#
def notify_error(text, title = 'Advanced Emulator Launcher error', time = 7000):
    xbmcgui.Dialog().notification(title, text, xbmcgui.NOTIFICATION_ERROR, time)

# -------------------------------------------------------------------------------------------------
# Kodi notifications and dialogs
# -------------------------------------------------------------------------------------------------
#
# Displays a modal dialog with an OK button. Dialog can have up to 3 rows of text, however first
# row is multiline.
# Call examples:
#  1) ret = kodi_dialog_OK('Launch ROM?')
#  2) ret = kodi_dialog_OK('Launch ROM?', title = 'AEL - Launcher')
#
def dialog_OK(text, title = 'Advanced Emulator Launcher'):
    xbmcgui.Dialog().ok(title, text)

# Returns True is YES was pressed, returns False if NO was pressed or dialog canceled.
def dialog_yesno(text, title = 'Advanced Emulator Launcher'):
    return xbmcgui.Dialog().yesno(title, text)

# Returns True is YES was pressed, returns False if NO was pressed or dialog canceled.
def dialog_yesno_custom(text, yeslabel_str, nolabel_str, title = 'Advanced Emulator Launcher'):
    return xbmcgui.Dialog().yesno(title, text, yeslabel = yeslabel_str, nolabel = nolabel_str)

def dialog_yesno_timer(text, timer_ms = 30000, title = 'Advanced Emulator Launcher'):
    return xbmcgui.Dialog().yesno(title, text, autoclose = timer_ms)

def browse(type = 1, text='Choose files', shares='files', mask=None, multiple=False):
    return xbmcgui.Dialog().browse(type, text, shares, mask, enableMultiple = multiple)

# Show keyboard dialog for user input. Returns None if not confirmed.
def dialog_keyboard(title, text='') -> str:
    keyboard = xbmc.Keyboard(text, title)
    keyboard.doModal()
    if not keyboard.isConfirmed(): return None
    return keyboard.getText()

def refresh_container():
    logger.debug('kodi_refresh_container()')
    xbmc.executebuiltin('Container.Refresh')

def get_current_window_id():
    return xbmcgui.getCurrentWindowId()

def set_windowprop(key, value, window_id=10000):
    window = xbmcgui.Window(window_id)
    window.setProperty(key, value)

def dict_to_windowprops(data=None, prefix="", window_id=10000):
    window = xbmcgui.Window(window_id)
    if not data:
        return None
    for (key, value) in data.items():
        window.setProperty('%s%s' % (prefix, key), str(value))

def clear_windowprops(keys=None, prefix="", window_id=10000):
    window = xbmcgui.Window(window_id)
    if not keys:
        return None
    for key in keys:
        window.clearProperty('%s%s' % (prefix, key))

def get_info_label(name):
    return xbmc.getInfoLabel(name)

def translate(id):
    return globals.addon.getLocalizedString(id)

#
# See https://kodi.wiki/view/JSON-RPC_API/v8#Textures
# See https://forum.kodi.tv/showthread.php?tid=337014
# See https://forum.kodi.tv/showthread.php?tid=236320
#
def delete_cache_texture(database_path_str):
    logger.debug('kodi_delete_cache_texture() Deleting texture "{0}:'.format(database_path_str))

    # --- Query texture database ---
    json_fname_str = text.escape_JSON(database_path_str)
    prop_str = (
        '{' +
        '"properties" : [ "url", "cachedurl", "lasthashcheck", "imagehash", "sizes"], ' +
        '"filter" : {{ "field" : "url", "operator" : "is", "value" : "{0}" }}'.format(json_fname_str) +
        '}'
    )
    r_dic = jsonrpc_query('Textures.GetTextures', prop_str, verbose = False)

    # --- Delete cached texture ---
    num_textures = len(r_dic['textures'])
    logger.debug('kodi_delete_cache_texture() Returned list with {0} textures'.format(num_textures))
    if num_textures == 1:
        textureid = r_dic['textures'][0]['textureid']
        logger.debug('kodi_delete_cache_texture() Deleting texture with id {0}'.format(textureid))
        prop_str = '{{ "textureid" : {0} }}'.format(textureid)
        r_dic = jsonrpc_query('Textures.RemoveTexture', prop_str, verbose = False)
    else:
        logger.warning('kodi_delete_cache_texture() Number of textures different from 1. No texture deleted from cache')

def print_texture_info(database_path_str):
    logger.debug('kodi_print_texture_info() File "{0}"'.format(database_path_str))

    # --- Query texture database ---
    json_fname_str = text.escape_JSON(database_path_str)
    prop_str = (
        '{' +
        '"properties" : [ "url", "cachedurl", "lasthashcheck", "imagehash", "sizes"], ' +
        '"filter" : {{ "field" : "url", "operator" : "is", "value" : "{0}" }}'.format(json_fname_str) +
        '}'
    )
    r_dic = jsonrpc_query('Textures.GetTextures', prop_str, verbose = False)

    # --- Delete cached texture ---
    num_textures = len(r_dic['textures'])
    logger.debug('print_texture_info() Returned list with {0} textures'.format(num_textures))
    if num_textures == 1:
        logger.debug('Cached URL  {0}'.format(r_dic['textures'][0]['cachedurl']))
        logger.debug('Hash        {0}'.format(r_dic['textures'][0]['imagehash']))
        logger.debug('Last check  {0}'.format(r_dic['textures'][0]['lasthashcheck']))
        logger.debug('Texture ID  {0}'.format(r_dic['textures'][0]['textureid']))
        logger.debug('Texture URL {0}'.format(r_dic['textures'][0]['url']))

#
# Kodi dialog with select box based on a list.
# preselect is int
# Returns the int index selected or None if dialog was canceled.
#
class ListDialog(object):
    def __init__(self):
        self.dialog = xbmcgui.Dialog()

    def select(self, title, options_list, preselect_idx = 0, use_details = False):
        # --- Execute select dialog menu logic ---
        selection = self.dialog.select(title, options_list, useDetails = use_details, preselect = preselect_idx)
        if selection < 0: return None
        return selection

#
# Kodi dialog with select box based on a dictionary
#
class OrdDictionaryDialog(object):
    def __init__(self):
        self.dialog = xbmcgui.Dialog()

    def select(self, title: str, options_odict: collections.OrderedDict, preselect = None, use_details: bool = False):
        preselected_index = -1
        if preselect is not None:
            preselected_value = options_odict[preselect]
            preselected_index = list(options_odict.values()).index(preselected_value)
            
        # --- Execute select dialog menu logic ---
        selection = self.dialog.select(title, [v for v in options_odict.values()], useDetails = use_details, preselect = preselected_index)       
        if selection < 0: return None
        key = list(options_odict.keys())[selection]

        return key

# Progress dialog that can be closed and reopened.
# If the dialog is canceled this class remembers it forever.
class ProgressDialog(object):
    def __init__(self):
        self.title = 'Advanced Emulator Launcher'
        self.progress = 0
        self.flag_dialog_canceled = False
        self.dialog_active = False
        self.progressDialog = xbmcgui.DialogProgress()

    def startProgress(self, message1, num_steps = 100, message2 = None):
        self.num_steps = num_steps
        self.progress = 0
        self.dialog_active = True
        self.message1 = message1
        self.message2 = message2
        if self.message2:
            self.progressDialog.create(self.title, self.message1, self.message2)
        else:
            # The ' ' is to avoid a bug in Kodi progress dialog that keeps old messages 2
            # if an empty string is passed.
            self.progressDialog.create(self.title, self.message1, ' ')
        self.progressDialog.update(self.progress)

    # Update progress and optionally update messages as well.
    # If not messages specified then keep current message/s
    def updateProgress(self, step_index, message1 = None, message2 = None):
        self.progress = int((step_index * 100) / self.num_steps)
        # Update both messages
        if message1 and message2:
            self.message1 = message1
            self.message2 = message2
        # Update only message1 and deletes message2. There could be no message2 without a message1.
        elif message1:
            self.message1 = message1
            self.message2 = None
            self.progressDialog.update(self.progress, message1, ' ')
            return
        if self.message2:
            self.progressDialog.update(self.progress, self.message1, self.message2)
        else:
            # The ' ' is to avoid a bug in Kodi progress dialog that keeps old messages 2
            # if an empty string is passed.
            self.progressDialog.update(self.progress, self.message1, ' ')

    # Update dialog message but keep same progress. message2 is removed if any.
    def updateMessage(self, message1):
        self.message1 = message1
        self.message2 = None
        self.progressDialog.update(self.progress, self.message1, ' ')

    # Update message2 and keeps same progress and message1
    def updateMessage2(self, message2):
        self.message2 = message2
        self.progressDialog.update(self.progress, self.message1, self.message2)

    # Update dialog message but keep same progress.
    def updateMessages(self, message1, message2):
        self.message1 = message1
        self.message2 = message2
        self.progressDialog.update(self.progress, message1, message2)

    def isCanceled(self):
        # If the user pressed the cancel button before then return it now.
        if self.flag_dialog_canceled:
            return True
        else:
            self.flag_dialog_canceled = self.progressDialog.iscanceled()
            return self.flag_dialog_canceled

    def close(self):
        # Before closing the dialog check if the user pressed the Cancel button and remember
        # the user decision.
        if self.progressDialog.iscanceled(): self.flag_dialog_canceled = True
        self.progressDialog.close()
        self.dialog_active = False

    def endProgress(self):
        # Before closing the dialog check if the user pressed the Cancel button and remember
        # the user decision.
        if self.progressDialog.iscanceled(): self.flag_dialog_canceled = True
        self.progressDialog.update(100)
        self.progressDialog.close()
        self.dialog_active = False

    # Reopens a previously closed dialog, remembering the messages and the progress it had
    # when it was closed.
    def reopen(self):
        if self.message2:
            self.progressDialog.create(self.title, self.message1, self.message2)
        else:
            # The ' ' is to avoid a bug in Kodi progress dialog that keeps old messages 2
            # if an empty string is passed.
            self.progressDialog.create(self.title, self.message1, ' ')
        self.progressDialog.update(self.progress)
        self.dialog_active = True

# To be used as a base class.
class ProgressDialog_Chrisism(object):
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
        if not self.verbose: return

        self.progressDialog.update(self.progress, message1, message2)

    def _isProgressCanceled(self):
        return self.progressDialog.iscanceled()

    def _endProgressPhase(self, canceled = False):
        if not canceled: self.progressDialog.update(100)
        self.progressDialog.close()
        