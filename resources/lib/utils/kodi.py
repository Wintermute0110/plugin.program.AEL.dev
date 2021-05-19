# -*- coding: utf-8 -*-
#
import logging
import json
import pprint

import xbmc
import xbmcgui
import xbmcaddon

logger = logging.getLogger(__name__)

__addon__         = xbmcaddon.Addon()
__addon_id__      = __addon__.getAddonInfo('id')

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

def event(sender=__addon_id__, method='test', data=None):

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