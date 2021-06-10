# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (App Launcher for ROM Collection)
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
from resources.lib.domain import ROMSetLauncher

from resources.app.commands.mediator import AppMediator
from resources.lib import globals, settings, platforms, executors
from resources.lib.utils import kodi, io

logger = logging.getLogger(__name__)

@AppMediator.register('APP_LAUNCH')
def cmd_app_launcher(cmd_args):
    logger.debug('App Launcher: Starting ...')
    launcher_args:dict  = cmd_args['launcher_args']
    rom_args:dict       = cmd_args['rom_args']
    
    app             = launcher_args['application']
    arguments       = launcher_args['args']
    is_non_blocking = launcher_args['is_non_blocking']
    
    app_path = io.FileName(app)
    executor = _get_executor(app_path)
    
    if executor is None:
        logger.error('Cannot create an executor for {}'.format(app_path.getPath()))
        kodi.notify_error('Cannot execute application')
        return

    logger.debug('Name        = "AppLauncher"')
    logger.debug('Application = "{}"'.format(app_path.getPath()))
    logger.debug('Arguments   = "{}"'.format(arguments))
    logger.debug('Executor    = "{}"'.format(executor.__class__.__name__))
    
    executor.execute(app_path, arguments, is_non_blocking())
    
# -------------------------------------------------------------------------------------------------
# Helper methods
# -------------------------------------------------------------------------------------------------
def _get_executor(app_path: io.FileName) -> executors.ExecutorABC:
    executorSettings                    = executors.ExecutorSettings()
    executorSettings.lirc_state         = settings.getSettingAsBool('lirc_state')
    executorSettings.show_batch_window  = settings.getSettingAsBool('show_batch_window')
    executorSettings.windows_cd_apppath = settings.getSettingAsBool('windows_cd_apppath')
    executorSettings.windows_close_fds  = settings.getSettingAsBool('windows_close_fds')
    
    executorFactory = executors.ExecutorFactory(globals.g_PATHS.LAUNCHER_REPORT_FILE_PATH, executorSettings)
    executor = executorFactory.create(app_path)
    return executor
    
