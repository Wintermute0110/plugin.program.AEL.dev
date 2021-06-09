# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (Configure App Launcher for ROM Collection)
#
# Copyright (c) 2016-2018 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import logging

from resources.app.commands.mediator import AppMediator
from resources.lib import constants, globals
from resources.lib import repositories
from resources.lib.repositories import *
from resources.lib.utils import kodi, io

logger = logging.getLogger(__name__)

@AppMediator.register('CONFIGURE_APP_LAUNCHER')
def cmd_configure_romset_launchers(args):
    romset_id:str = args['romset_id'] if 'romset_id' in args else None
    platform:str = args['platform'] if 'platform' in args else None
    
      # --- Launcher build code (ask user about launcher stuff) ---
    wizard = kodi.WizardDialog_Dummy(None, 'romset_id', romset_id)
    wizard = kodi.WizardDialog_Dummy(wizard, 'addon_id', '{}.AppLauncher'.format(globals.addon_id))    
    wizard = kodi.WizardDialog_FileBrowse(wizard, 'application', 'Select the launcher application',
            1, _builder_get_appbrowser_filter)
    wizard = kodi.WizardDialog_FileBrowse(wizard, 'rompath', 'Select the ROMs path', 0, '')
    wizard = kodi.WizardDialog_Dummy(wizard, 'romext', '', _builder_get_extensions_from_app_path)
    wizard = kodi.WizardDialog_Keyboard(wizard, 'romext','Set files extensions, use "|" as separator. (e.g lnk|cbr)')
    wizard = kodi.WizardDialog_Dummy(wizard, 'args', '', _builder_get_arguments_from_application_path)
    wizard = kodi.WizardDialog_Keyboard(wizard, 'args', 'Application arguments')
   
def _builder_get_appbrowser_filter(item_key, launcher_args):
    if item_key in launcher_args:
        application = launcher_args[item_key]
        if application == 'JAVA':
            return '.jar'

    return '.bat|.exe|.cmd|.lnk' if io.is_windows() else '' 

def _builder_get_extensions_from_app_path(input, item_key ,launcher_args):
    if input: return input

    app = launcher_args['application']
    appPath = io.FileName(app)

    extensions = emudata_get_program_extensions(appPath.getBase())
    return extensions