# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Executors
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

import abc
import shlex
import subprocess
import webbrowser
import logging
import re 
import os
import logging

import xbmc

from resources.lib.utils import io
from resources.lib.utils import kodi

logger = logging.getLogger(__name__)

# #################################################################################################
# #################################################################################################
# Executors
# #################################################################################################
# #################################################################################################
class ExecutorABC():
    __metaclass__ = abc.ABCMeta

    def __init__(self, logFile):
        self.logFile = logFile

    @abc.abstractmethod
    def execute(self, application, arguments, non_blocking): pass

class XbmcExecutor(ExecutorABC):
    # --- Execute Kodi built-in function under certain conditions ---
    def execute(self, application, arguments, non_blocking):
        xbmc.executebuiltin('XBMC.{0}'.format(arguments))

#
# --- Linux ---
# New in AEL 0.9.7: always close all file descriptions except 0, 1 and 2 on the child
# process. This is to avoid Kodi opens sockets be inherited by the child process. A
# wrapper script may terminate Kodi using JSON RPC and if file descriptors are not
# closed Kodi will complain that the remote interfacte cannot be initialised. I believe
# the cause is that the socket is kept open by the wrapper script.
#
class LinuxExecutor(ExecutorABC):
    def __init__(self, logFile, lirc_state):
        self.lirc_state = lirc_state
        super(LinuxExecutor, self).__init__(logFile)

    def execute(self, application, arguments, non_blocking):
        logger.debug('LinuxExecutor::execute() Starting ...')
        arg_list  = shlex.split(arguments, posix = True)
        command = [application.getPath()] + arg_list

        # >> Old way of launching child process. os.system() is deprecated and should not
        # >> be used anymore.
        # os.system('"{0}" {1}'.format(application, arguments).encode('utf-8'))

         # >> New way of launching, uses subproces module. Also, save child process stdout.
        if non_blocking:
            # >> In a non-blocking launch stdout/stderr of child process cannot be recorded.
            logger.info('Launching non-blocking process subprocess.Popen()')
            p = subprocess.Popen(command, close_fds = True)
        else:
            if self.lirc_state: xbmc.executebuiltin('LIRC.stop')
            with open(self.logFile.getPath(), 'w') as f:
                retcode = subprocess.call(
                    command, stdout = f, stderr = subprocess.STDOUT, close_fds = True)
            logger.info('Process retcode = {0}'.format(retcode))
            if self.lirc_state: xbmc.executebuiltin('LIRC.start')
        logger.debug('LinuxExecutor::execute() function ENDS')

class AndroidExecutor(ExecutorABC):
    def __init__(self):
        super(AndroidExecutor, self).__init__(None)

    def execute(self, application, arguments, non_blocking):
        logger.debug('AndroidExecutor::execute() Starting ...')
        retcode = os.system("{0} {1}".format(application.getPath(), arguments).encode('utf-8'))
        logger.info('Process retcode = {0}'.format(retcode))
        logger.debug('AndroidExecutor::execute() function ENDS')

class OSXExecutor(ExecutorABC):
    def execute(self, application, arguments, non_blocking):
        logger.debug('OSXExecutor::execute() Starting ...')
        arg_list  = shlex.split(arguments, posix = True)
        command = [application.getPath()] + arg_list

        # >> Old way.
        # os.system('"{0}" {1}'.format(application, arguments).encode('utf-8'))

        # >> New way.
        with open(self.logFile.getPath(), 'w') as f:
            retcode = subprocess.call(command, stdout = f, stderr = subprocess.STDOUT)
        logger.info('Process retcode = {0}'.format(retcode))
        logger.debug('OSXExecutor::execute() function ENDS')

class WindowsLnkFileExecutor(ExecutorABC):
    def execute(self, application, arguments, non_blocking):
        logger.debug('WindowsLnkFileExecutor::execute() Starting ...')
        logger.debug('Launching LNK application')
        # os.system('start "AEL" /b "{0}"'.format(application).encode('utf-8'))
        retcode = subprocess.call('start "AEL" /b "{0}"'.format(application.getPath()).encode('utf-8'), shell = True)
        logger.info('LNK app retcode = {0}'.format(retcode))
        logger.debug('WindowsLnkFileExecutor::execute() function ENDS')

#
# CMD/BAT files in Windows
#
class WindowsBatchFileExecutor(ExecutorABC):
    def __init__(self, logFile, show_batch_window):
        self.show_batch_window = show_batch_window
        super(WindowsBatchFileExecutor, self).__init__(logFile)

    def execute(self, application, arguments, non_blocking):
        logger.debug('WindowsBatchFileExecutor::execute() Starting ...')
        arg_list  = shlex.split(arguments, posix = True)
        command = [application.getPath()] + arg_list
        apppath = application.getDir()
        
        # --- Workaround to run UNC paths in Windows ---
        # >> Retroarch now support ROMs in UNC paths (Samba remotes)
        new_command = list(command)
        for i, _ in enumerate(command):
            if command[i][0] == '\\':
                new_command[i] = '\\' + command[i]
                logger.debug('Executor (Windows BatchFile): Before arg #{0} = "{1}"'.format(i, command[i]))
                logger.debug('Executor (Windows BatchFile): Now    arg #{0} = "{1}"'.format(i, new_command[i]))
        command = list(new_command)
        logger.debug('Executor (Windows BatchFile): command = {0}'.format(command))
        
        logger.debug('Executor (Windows BatchFile) Launching BAT application')
        logger.debug('Executor (Windows BatchFile) Ignoring setting windows_cd_apppath')
        logger.debug('Executor (Windows BatchFile) Ignoring setting windows_close_fds')
        logger.debug('Executor (Windows BatchFile) show_batch_window = {0}'.format(self.show_batch_window))
        info = subprocess.STARTUPINFO()
        info.dwFlags = 1
        info.wShowWindow = 5 if self.show_batch_window else 0
        retcode = subprocess.call(command, cwd = apppath.encode('utf-8'), close_fds = True, startupinfo = info)
        logger.info('Executor (Windows BatchFile) Process BAR retcode = {0}'.format(retcode))
        logger.debug('WindowsBatchFileExecutor::execute() function ENDS')

#
# --- Windoze ---
# NOTE subprocess24_hack.py was hacked to always set CreateProcess() bInheritHandles to 0.
# bInheritHandles [in] If this parameter TRUE, each inheritable handle in the calling 
# process is inherited by the new process. If the parameter is FALSE, the handles are not 
# inherited. Note that inherited handles have the same value and access rights as the original handles.
# See https://msdn.microsoft.com/en-us/library/windows/desktop/ms682425(v=vs.85).aspx
#
# Same behaviour can be achieved in current version of subprocess with close_fds.
# If close_fds is true, all file descriptors except 0, 1 and 2 will be closed before the 
# child process is executed. (Unix only). Or, on Windows, if close_fds is true then no handles 
# will be inherited by the child process. Note that on Windows, you cannot set close_fds to 
# true and also redirect the standard handles by setting stdin, stdout or stderr.
#
# If I keep old launcher behaviour in Windows (close_fds = True) then program output cannot
# be redirected to a file.
#
class WindowsExecutor(ExecutorABC):
    def __init__(self, logFile, cd_apppath, close_fds):
        self.windows_cd_apppath = cd_apppath
        self.windows_close_fds  = close_fds
        super(WindowsExecutor, self).__init__(logFile)

    def execute(self, application, arguments, non_blocking):
        logger.debug('WindowsExecutor::execute() Starting ...')
        arg_list  = shlex.split(arguments, posix = True)
        command = [application.getPath()] + arg_list
        apppath = application.getDir()

        # --- Workaround to run UNC paths in Windows ---
        # >> Retroarch now support ROMs in UNC paths (Samba remotes)
        new_command = list(command)
        for i, _ in enumerate(command):
            if command[i][0] == '\\':
                new_command[i] = '\\' + command[i]
                logger.debug('WindowsExecutor: Before arg #{0} = "{1}"'.format(i, command[i]))
                logger.debug('WindowsExecutor: Now    arg #{0} = "{1}"'.format(i, new_command[i]))
        command = list(new_command)
        logger.debug('WindowsExecutor: command = {0}'.format(command))

        # >> cwd = apppath.encode('utf-8') fails if application path has Unicode on Windows
        # >> A workaraound is to use cwd = apppath.encode(sys.getfilesystemencoding()) --> DOES NOT WORK
        # >> For the moment AEL cannot launch executables on Windows having Unicode paths.
        logger.debug('Launching regular application')
        logger.debug('windows_cd_apppath = {0}'.format(self.windows_cd_apppath))
        logger.debug('windows_close_fds  = {0}'.format(self.windows_close_fds))

        # >> Note that on Windows, you cannot set close_fds to true and also redirect the 
        # >> standard handles by setting stdin, stdout or stderr.
        if self.windows_cd_apppath and self.windows_close_fds:
            retcode = subprocess.call(command, cwd = apppath.encode('utf-8'), close_fds = True)
        elif self.windows_cd_apppath and not self.windows_close_fds:
            with open(self.logFile.getPath(), 'w') as f:
                retcode = subprocess.call(command, cwd = apppath.encode('utf-8'), close_fds = False,
                                            stdout = f, stderr = subprocess.STDOUT)
        elif not self.windows_cd_apppath and self.windows_close_fds:
            retcode = subprocess.call(command, close_fds = True)
        elif not self.windows_cd_apppath and not self.windows_close_fds:
            with open(self.logFile.getPath(), 'w') as f:
                retcode = subprocess.call(command, close_fds = False, stdout = f, stderr = subprocess.STDOUT)
        else:
            raise Exception('Logical error')
        logger.info('Process retcode = {0}'.format(retcode))
        logger.debug('WindowsExecutor::execute() function ENDS')

class WebBrowserExecutor(ExecutorABC):
    def execute(self, application, arguments, non_blocking):
        logger.debug('WebBrowserExecutor::execute() Starting ...')
        command = application.getPath() + arguments
        logger.debug('Launching URL "{0}"'.format(command))
        webbrowser.open(command)
        logger.debug('WebBrowserExecutor::execute() function ENDS')

# -------------------------------------------------------------------------------------------------
# Abstract Factory Pattern
# See https://www.oreilly.com/library/view/head-first-design/0596007124/ch04.html
# -------------------------------------------------------------------------------------------------
class ExecutorFactory(object):
    def __init__(self, g_PATHS, settings):
        self.settings = settings
        self.logFile  = g_PATHS.LAUNCHER_REPORT_FILE_PATH

    def create_from_pathstring(self, application_string):
        return self.create(io.FileName(application_string))

    def create(self, application: io.FileName):
        if application.getBase().lower().replace('.exe' , '') == 'xbmc' \
            or 'xbmc-fav-' in application.getPath() or 'xbmc-sea-' in application.getPath():
            return XbmcExecutor(self.logFile)

        elif re.search('.*://.*', application.getPath()):
            return WebBrowserExecutor(self.logFile)

        elif io.is_windows():
            # >> BAT/CMD file.
            if application.getExt().lower() == '.bat' or application.getExt().lower() == '.cmd' :
                return WindowsBatchFileExecutor(self.logFile, self.settings['show_batch_window'])
            # >> Standalone launcher where application is a LNK file
            elif application.getExt().lower() == '.lnk': 
                return WindowsLnkFileExecutor(self.logFile)

            # >> Standard Windows executor
            return WindowsExecutor(self.logFile,
                self.settings['windows_cd_apppath'], self.settings['windows_close_fds'])

        elif io.is_android():
            return AndroidExecutor()

        elif io.is_linux():
            return LinuxExecutor(self.logFile, self.settings['lirc_state'])

        elif io.is_osx():
            return OSXExecutor(self.logFile)

        else:
            logger.error('ExecutorFactory::create() Cannot determine the running platform')
            kodi.notify_warn('Cannot determine the running platform')

        return None