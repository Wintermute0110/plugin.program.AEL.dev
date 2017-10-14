from abc import ABCMeta, abstractmethod

import os

# --- Kodi stuff ---
import xbmc

# --- Modules/packages in this plugin ---
from disk_IO import *
from utils import *
from utils_kodi import *

# >> Determine platform to execute launcher on
# >> See http://stackoverflow.com/questions/446209/possible-values-from-sys-platform
class ExecutorFactory():

    def __init__(self, settings, logFile):
        
        self.settings = settings
        self.logFile = logFile

    def create_from_pathstring(self, application_string):
        app = FileName(application_string)
        return self.create(app)

    def create(self, application):
        
        if application.getBase().lower().replace('.exe' , '') == 'xbmc' \
            or 'xbmc-fav-' in application.getOriginalPath() or 'xbmc-sea-' in application.getOriginalPath():
            return XbmcExecutor(self.logFile)
        
        if sys.platform == 'win32':
            
            if application.getExt().lower() == '.bat':
                return WindowsBatchFileExecutor(self.logFile, self.settings['show_batch_window'])
            
            # >> Standalone launcher where application is a LNK file
            if application.getExt().lower() == '.lnk': 
                return WindowsLnkFileExecutor(self.logFile)

            return WindowsExecutor(self.logFile, self.settings['windows_cd_apppath'], self.settings['windows_close_fds'])

        if sys.platform.startswith('linux'):
            return LinuxExecutor(self.logFile, self.settings['lirc_state'])
        
        if sys.platform.startswith('darwin'):
            return OSXExecutor(self.logFile)

        kodi_notify_warn('Cannot determine the running platform')
        return None

class Executor():
    __metaclass__ = ABCMeta
    
    def __init__(self, logFile):
        self.logFile = logFile
        
    @abstractmethod
    def execute(self, application, arguments, non_blocking):
        pass

class XbmcExecutor(Executor):

    # --- Execute Kodi built-in function under certain conditions ---
    def execute(self, application, arguments):

        xbmc.executebuiltin('XBMC.{0}'.format(arguments))
        pass
    
# >> Linux and Android
# >> New in 0.9.7: always close all file descriptions except 0, 1 and 2 on the child
# >> process. This is to avoid Kodi opens sockets be inherited by the child process. A
# >> wrapper script may terminate Kodi using JSON RPC and if file descriptors are not
# >> closed Kodi will complain that the remote interfacte cannot be initialised. I believe
# >> the cause is that the socket is kept open by the wrapper script.
class LinuxExecutor(Executor):

    def __init__(self, logFile, lirc_state):
        self.lirc_state = lirc_state
        
        super(LinuxExecutor, self).__init__(logFile)

    def execute(self, application, arguments, non_blocking):
        import subprocess
        import shlex

        if self.lirc_state:
           xbmc.executebuiltin('LIRC.stop')

        arg_list  = shlex.split(arguments, posix = True)
        command = [application.getPath()] + arg_list

        # >> Old way of launching child process. os.system() is deprecated and should not
        # >> be used anymore.
        # os.system('"{0}" {1}'.format(application, arguments).encode('utf-8'))

         # >> New way of launching, uses subproces module. Also, save child process stdout.
        if non_blocking:
            # >> In a non-blocking launch stdout/stderr of child process cannot be recorded.
            log_info('LinuxExecutor: Launching non-blocking process subprocess.Popen()')
            p = subprocess.Popen(exec_list, close_fds = True)
        else:
            with open(self.logFile.getPath(), 'w') as f:
                retcode = subprocess.call(command, stdout = f, stderr = subprocess.STDOUT, close_fds = True)
            log_info('LinuxExecutor: Process retcode = {0}'.format(retcode))
            if self.lirc_state:
                xbmc.executebuiltin('LIRC.start')

        pass

class OSXExecutor(Executor):

    def execute(self, application, arguments):
        import subprocess
        import shlex
        
        arg_list  = shlex.split(arguments, posix = True)
        command = [application.getPath()] + arg_list
        
        # >> Old way
        # os.system('"{0}" {1}'.format(application, arguments).encode('utf-8'))
            
        # >> New way.
        with open(self.logFile.getPath(), 'w') as f:
            retcode = subprocess.call(command, stdout = f, stderr = subprocess.STDOUT)

        log_info('OSXExecutor: Process retcode = {0}'.format(retcode))

        pass

class WindowsLnkFileExecutor(Executor):

    def execute(self, application, arguments):
                
        log_debug('Executor (Windows) Launching LNK application')
        # os.system('start "AEL" /b "{0}"'.format(application).encode('utf-8'))
        retcode = subprocess.call('start "AEL" /b "{0}"'.format(application.getPath()).encode('utf-8'), shell = True)
        log_info('Executor (Windows) LNK app retcode = {0}'.format(retcode))
        pass

# >> CMD/BAT files in Windows
class WindowsBatchFileExecutor(Executor):

    def __init__(self, logFile, show_batch_window):
        self.show_batch_window = show_batch_window

        super(WindowsBatchFileExecutor, self).__init__(logFile)

    def execute(self, application, arguments):
        import subprocess
        import shlex
        
        arg_list  = shlex.split(arguments, posix = True)
        command = [application.getPath()] + arg_list
        apppath = application.getDir()

        log_debug('Executor (Windows BatchFile) Launching BAT application')
        log_debug('Executor (Windows BatchFile) show_batch_window = {0}'.format(self.show_batch_window))
        info = subprocess.STARTUPINFO()
        info.dwFlags = 1
        info.wShowWindow = 5 if self.show_batch_window else 0
        retcode = subprocess.call(command, cwd = apppath.encode('utf-8'), close_fds = True, startupinfo = info)
        log_info('Executor (Windows BatchFile) Process BAR retcode = {0}'.format(retcode))

        pass


class WindowsExecutor(Executor):

    def __init__(self, logFile, cd_apppath, close_fds):
        
        self.windows_cd_apppath = cd_apppath
        self.windows_close_fds  = close_fds

        super(WindowsExecutor, self).__init__(logFile)

                
    # >> Windoze
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
    def execute(self, application, arguments):
        import subprocess
        import shlex
        
        arg_list  = shlex.split(arguments, posix = True)
        command = [application.getPath()] + arg_list
        apppath = application.getDir()
        
        # --- Workaround to run UNC paths in Windows ---
        # >> Retroarch now support ROMs in UNC paths (Samba remotes)
        new_command = list(command)
        for i, _ in enumerate(command):
            if command[i][0] == '\\':
                new_command[i] = '\\' + command[i]
                log_debug('WindowsExecutor: Before arg #{0} = "{1}"'.format(i, command[i]))
                log_debug('WindowsExecutor: Now    arg #{0} = "{1}"'.format(i, new_command[i]))
        command = list(new_command)
        log_debug('WindowsExecutor: command = {0}'.format(command))

        # >> cwd = apppath.encode('utf-8') fails if application path has Unicode on Windows
        # >> A workaraound is to use cwd = apppath.encode(sys.getfilesystemencoding()) --> DOES NOT WORK
        # >> For the moment AEL cannot launch executables on Windows having Unicode paths.
        log_debug('Executor (Windows) Launching regular application')
        log_debug('Executor (Windows) windows_cd_apppath = {0}'.format(self.windows_cd_apppath))
        log_debug('Executor (Windows) windows_close_fds  = {0}'.format(self.windows_close_fds))
       
        # >>  Note that on Windows, you cannot set close_fds to true and also redirect the 
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
        
        log_info('Executor (Windows) Process retcode = {0}'.format(retcode))
           
        pass