# -*- coding: utf-8 -*-

# Advanced Emulator Launcher miscellaneous functions

# Copyright (c) 2016-2019 Wintermute0110 <wintermute0110@gmail.com>
# Portions (c) 2010-2015 Angelscry and others
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# --- Module documentation ---
# 1. This function contains utilities that do not depend on Kodi modules and utilities that
#    depend on Kodi modules. Appropiate replacements are provided when the Kodi modules are
#    not available, for example when running this file with the standard Python interpreter and
#    not Kodi Python interpreter.
#
# 2. Filesystem access utilities are located in this file. Filesystem can use the Python
#    standard library or Kodi Virtual FileSystem library if available.
#
# 3. utils.py must not depend on any other AEL module to avoid circular dependencies, with the
#    exception of constants.py
#
# 4. Functions starting with _ are internal module functions not to be called externally.
#

# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division
from io import FileIO, TextIOWrapper

import logging
import errno
import fnmatch
import json
import sys
import os
import shutil
from typing import TextIO

# Python 3
#from html.parser import HTMLParser
#from urllib.parse import urlparse

# --- Python standard library named imports ---
import xml.etree.ElementTree as ET

import xbmc
import xbmcvfs

from resources.lib.constants import *

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# --- New Filesystem class ---
#
# 1. Automatically uses Python standard library for local files and Kodi VFS for remote files.
#
# 2. All paths on all platforms use the slash '/' to separate directories.
#
# 3. Directories always end in a '/' character.
#
# 3. Decoding Unicode to the filesystem encoding is done in this class.
#
# 4. Tested with the following remote protocols:
#
#     a) special://
#
#     b) smb://
#
# --- Function reference ---
# FileName.getPath()         Full path                                     /home/Wintermute/Sonic.zip
# FileName.getPathNoExt()    Full path with no extension                   /home/Wintermute/Sonic
# FileName.getDir()          Directory name of file. Does not end in '/'   /home/Wintermute/
# FileName.getBase()         File name with no path                        Sonic.zip
# FileName.getBaseNoExt()    File name with no path and no extension       Sonic
# FileName.getExt()          File extension                                .zip
#
#
# A) Transform paths like smb://server/directory/ into \\server\directory\
# B) Use xbmcvfs.translatePath() for paths starting with special://
# C) Uses xbmcvfs wherever possible
#
# -------------------------------------------------------------------------------------------------
# Once everything is working like a charm comment all the debug code to speed up.
DEBUG_NEWFILENAME_CLASS = True

class FileName:
    # ---------------------------------------------------------------------------------------------
    # Constructor
    # path_str is an Unicode string.
    # ---------------------------------------------------------------------------------------------
    def __init__(self, path_str, isdir = False):
        self.path_str = path_str
        self.is_a_dir = isdir

        # --- Check if path needs translation ---
        # Note that internally path_tr is always used as the filename.
        if self.path_str.lower().startswith('special://'):
            self.is_translated = True
            self.path_tr = xbmcvfs.translatePath(self.path_str)
            # Check translated path does not contain '\'
            # NOTE We don't care if the translated paths has '\' characters or not. The translated
            #      path is internal to the class and never used outside the class. In the JSON
            #      databases and config files the original path path_str is used always.
            # if self.path_tr.find('\\'):
            #     logger.error('(FileName) path_str "{0}"'.format(self.path_str))
            #     logger.error('(FileName) path_tr  "{0}"'.format(self.path_tr))
            #     e_str = '(FileName) Translated path has \\ characters'
            #     logger.error(e_str)
            #     raise Addon_Error(e_str)
        else:
            self.is_translated = False
            self.path_tr = self.path_str

        # --- Ensure directory separator is the '/' character for all OSes ---
        self.path_str = self.path_str.replace('\\', '/')
        self.path_tr = self.path_tr.replace('\\', '/')

        # --- If a directory, ensure path ends with '/' ---
        if self.is_a_dir:
            if not self.path_str[-1:] == '/': self.path_str = self.path_str + '/'
            if not self.path_tr[-1:] == '/': self.path_tr = self.path_tr + '/'

        # if DEBUG_NEWFILENAME_CLASS:
        #     logger.debug('FileName() path_str "{0}"'.format(self.path_str))
        #     logger.debug('FileName() path_tr  "{0}"'.format(self.path_tr))

        # --- Check if file is local or remote and needs translation ---
        if self.path_str.lower().startswith('smb://'):
            self.is_local = False
        else:
            self.is_local = True

        # --- Assume that translated paths are always local ---
        if self.is_translated and not self.is_local:
            e_str = '(FileName) File is translated and remote.'
            logger.error(e_str)
            raise AddonError(e_str)

        # --- Use Pyhton for local paths and Kodi VFS for remote paths ---
        if self.is_local:
            # --- Filesystem functions ---
            self.exists         = self.exists_python
            self.makedirs       = self.makedirs_python
            self.list           = self.list_python
            self.recursive_list = self.recursive_list_python

            # --- File low-level IO functions ---
            self.open     = self.open_python
            self.read     = self.read_python
            self.write    = self.write_python
            self.close    = self.close_python
            self.unlink   = self.unlink_python
            self.stat     = self.stat_python
        else:
            self.exists         = self.exists_kodivfs
            self.makedirs       = self.makedirs_kodivfs
            self.list           = self.list_kodivfs
            self.recursive_list = self.recursive_list_kodivfs

            self.open     = self.open_kodivfs
            self.read     = self.read_kodivfs
            self.write    = self.write_kodivfs
            self.close    = self.close_kodivfs
            self.unlink   = self.unlink_kodivfs
            self.stat     = self.stat_kodivfs
    
    # ---------------------------------------------------------------------------------------------
    # Core functions
    # ---------------------------------------------------------------------------------------------
    #
    # Wheter the path stored in the FileName class is a directory or a regular file is handled
    # internally. This is to avoid a design flaw of the Kodi VFS library.
    #
    def isdir(self):
        return self.is_a_dir

    #
    # Allow late setting of isdir() if using the constructor call is not available, for example
    # when using FileName.pjoin().
    #
    def set_isdir(self, isdir):
        self.__init__(self.path_str, isdir)

    #
    # Appends a string to path
    # Returns self FileName object
    #
    def append(self, arg):
        self.path_str = self.path_str + arg
        self.path_tr = self.path_tr + arg

        return self

    #
    # Joins paths and returns a new filename object.
    #
    def pjoin(self, path_str, isdir = False):
        return FileName(os.path.join(self.path_str, path_str), isdir)

    # ---------------------------------------------------------------------------------------------
    # Operator overloads
    # ---------------------------------------------------------------------------------------------
    def __str__(self):
        return self.path_str

    # Overloaded operator + behaves like self pjoin()
    # See http://blog.teamtreehouse.com/operator-overloading-python
    # Argument other is a FileName object. other originalPath is expected to be a
    # subdirectory (path transformation not required)
    def __add__(self, path_str):
        return self.pjoin(path_str)

    def __eq__(self, other):
        return self.path_str == other.path_str

    def __ne__(self, other):
        return not self.__eq__(other)

    # ---------------------------------------------------------------------------------------------
    # Path manipulation and file information
    # ---------------------------------------------------------------------------------------------
    def getPath(self):
        return self.path_str

    def getPathTranslated(self):
        return self.path_tr

    def getPathNoExt(self):
        root, ext = os.path.splitext(self.path_str)

        return root

    def getDir(self):
        path_dir = os.path.dirname(self.path_str)
        return os.path.join(path_dir, '')

    # Returns a new FileName object.
    def getDirAsFileName(self):
        return FileName(self.getDir())

    def getBase(self):
        return os.path.basename(self.path_str)

    def getBaseNoExt(self):
        basename  = os.path.basename(self.path_str)
        root, ext = os.path.splitext(basename)

        return root

    def getExt(self):
        root, ext = os.path.splitext(self.path_str)
        return ext

    def changeExtension(self, targetExt):
        #raise AddonError('Implement me.')
        ext = self.getExt()
        copiedPath = self.path_str
        if not targetExt.startswith('.'):
            targetExt = '.{0}'.format(targetExt)
        new_path = FileName(copiedPath.replace(ext, targetExt))
        return new_path

    def escapeQuotes(self):
        self.path_tr = self.path_tr.replace("'", "\\'")
        self.path_tr = self.path_tr.replace('"', '\\"')
        
    # ---------------------------------------------------------------------------------------------
    # Filesystem functions. Python Standard Library implementation
    # ---------------------------------------------------------------------------------------------
    def exists_python(self):
        return os.path.exists(self.path_tr)

    def makedirs_python(self):
        if not os.path.exists(self.path_tr): 
            if DEBUG_NEWFILENAME_CLASS:
                logger.debug('FileName::makedirs_python() path_tr "{0}"'.format(self.path_tr))
            os.makedirs(self.path_tr)

    def list_python(self):        
        return os.listdir(self.path_tr)

    def recursive_list_python(self):
        files = []
        for root, dirs, foundfiles in os.walk(self.path_tr):
            for filename in foundfiles:
                files.append(os.path.join(root, filename))

        return files
    
    def stat_python(self):
        return os.stat(self.path_tr)

    # ---------------------------------------------------------------------------------------------
    # Filesystem functions. Kodi VFS implementation.
    # Kodi VFS functions always work with path_str, not with the translated path.
    # ---------------------------------------------------------------------------------------------
    def exists_kodivfs(self):
        return xbmcvfs.exists(self.path_str)

    def makedirs_kodivfs(self):
        xbmcvfs.mkdirs(self.path_tr)

    def list_kodivfs(self):
        subdirectories, filenames = xbmcvfs.listdir(self.path_tr)
        return filenames
    
    def recursive_list_kodivfs(self):
        files = self.recursive_list_kodivfs_folders(self.path_tr, None)
        return files
    
    def recursive_list_kodivfs_folders(self, fullPath, parentFolder):
        files = []
        subdirectories, filenames = xbmcvfs.listdir(fullPath)
        
        for filename in filenames:
            filePath = os.path.join(parentFolder, filename) if parentFolder is not None else filename
            files.append(filePath)

        for subdir in subdirectories:
            subPath = os.path.join(parentFolder, subdir) if parentFolder is not None else subdir
            subFullPath = os.path.join(fullPath, subdir)
            subPathFiles = self.recursive_list_kodivfs_folders(subFullPath, subPath)
            files.extend(subPathFiles)

        return files

    def stat_kodivfs(self):
        return xbmcvfs.Stat(self.path_tr)

    # ---------------------------------------------------------------------------------------------
    # File low-level IO functions. Python Standard Library implementation
    # ---------------------------------------------------------------------------------------------
    def open_python(self, flags, encoding='utf-8'):
        logger.debug('FileName::open_python() path_tr "{0}"'.format(self.path_tr))
        logger.debug('FileName::open_python() flags   "{0}"'.format(flags))

        # open() is a built-in function.
        # See https://docs.python.org/3/library/functions.html#open
        self.fileHandle = open(self.path_tr, flags, encoding=encoding)

        return self

    def close_python(self):
        if self.fileHandle is None:
            raise OSError('file not opened')
        self.fileHandle.close()
        self.fileHandle = None

    def read_python(self):
       if self.fileHandle is None:
           raise OSError('file not opened')

       return self.fileHandle.read()

    def write_python(self, bytes): 
       if self.fileHandle is None:
           raise OSError('file not opened')
       self.fileHandle.write(bytes)

    def unlink_python(self):
        os.remove(self.path_tr)
            
    # ---------------------------------------------------------------------------------------------
    # File low-level IO functions. Kodi VFS implementation.
    # Kodi VFS documentation in https://alwinesch.github.io/group__python__xbmcvfs.html
    # ---------------------------------------------------------------------------------------------
    def open_kodivfs(self, flags, encoding='utf-8'):
        logger.debug('FileName::open_kodivfs() path_tr "{0}"'.format(self.path_tr))
        logger.debug('FileName::open_kodivfs() flags   "{0}"'.format(flags))

        self.fileHandle = xbmcvfs.File(self.path_tr, flags)
        return self
    
    def read_kodivfs(self):
        if self.fileHandle is None: raise OSError('file not opened')
        return self.fileHandle.read()
 
    def write_kodivfs(self, bytes):
        if self.fileHandle is None: raise OSError('file not opened')
        self.fileHandle.write(bytes)

    def close_kodivfs(self):
        if self.fileHandle is None: raise OSError('file not opened')
        self.fileHandle.close()
        self.fileHandle = None
  
    def unlink_kodivfs(self):
        if self.is_a_dir:
            xbmcvfs.rmdir(self.path_tr)
            return
        
        xbmcvfs.delete(self.path_tr)
        # hard delete if it doesnt succeed
        #logger.debug('xbmcvfs.delete() failed, applying hard delete')
        if self.exists():
            self.unlink_python()
            
    # ---------------------------------------------------------------------------------------------
    # File high-level IO functions
    # These functions are independent of the filesystem implementation.
    # For compatibility with Python 3, use the terms str for Unicode strings and bytes for
    # encoded strings.
    # ---------------------------------------------------------------------------------------------
    #
    # If both files are local use Python SL. Otherwise use Kodi VFS.
    # shutil.copy2() preserves metadata, including atime and mtime. We do not want that.
    #
    # See https://docs.python.org/2/library/shutil.html#shutil.copy
    # See https://docs.python.org/2/library/shutil.html#shutil.copy2
    # See https://docs.python.org/2/library/sys.html#sys.getfilesystemencoding
    #
    def copy(self, to_FN):
        if self.is_local and to_FN.is_local:
            fs_encoding = sys.getfilesystemencoding()
            source_bytes = self.getPath().decode(fs_encoding)
            dest_bytes = to_FN.getPath().decode(fs_encoding)
            if DEBUG_NEWFILENAME_CLASS:
                logger.debug('FileName::copy() Using Python Standard Library')
                logger.debug('FileName::copy() fs encoding "{0}"'.format(fs_encoding))
                logger.debug('FileName::copy() Copy "{0}"'.format(source_bytes))
                logger.debug('FileName::copy() into "{0}"'.format(dest_bytes))
            try:
                shutil.copy(source_bytes, dest_bytes)
            except OSError:
                logger.error('FileName::copy() OSError exception copying image')
                raise AddonError('OSError exception copying image')
            except IOError:
                logger.error('FileName::copy() IOError exception copying image')
                raise AddonError('IOError exception copying image')
        else:
            if DEBUG_NEWFILENAME_CLASS:
                logger.debug('FileName::copy() Using Kodi VFS')
                logger.debug('FileName::copy() Copy "{0}"'.format(self.getPath()))
                logger.debug('FileName::copy() into "{0}"'.format(to_FN.getPath()))
            # >> If xbmcvfs.copy() fails what exceptions raise???
            xbmcvfs.copy(self.getPath(), to_FN.getPath())

    #
    # Loads a file into a Unicode string.
    # By default all files are assumed to be encoded in UTF-8.
    # Returns a Unicode string.
    #
    def loadFileToStr(self, encoding = 'utf-8'):
        if DEBUG_NEWFILENAME_CLASS:
            logger.debug('FileName::loadFileToStr() Loading path_str "{0}"'.format(self.path_str))

        # NOTE Exceptions should be catched, reported and re-raised in the low-level
        # functions, not here!!!
        file_bytes = None
        try:
            self.open('r', )
            file_bytes = self.read()
            self.close()
        except OSError:
            logger.error('(OSError) Exception in FileName::loadFileToStr()')
            logger.error('(OSError) Cannot read {0} file'.format(self.path_tr))
            raise AddonError('(OSError) Cannot read {0} file'.format(self.path_tr))
        except IOError as Ex:
            logger.error('(IOError) Exception in FileName::loadFileToStr()')
            logger.error('(IOError) errno = {0}'.format(Ex.errno))
            if Ex.errno == errno.ENOENT: logger.error('(IOError) No such file or directory.')
            else:                        logger.error('(IOError) Unhandled errno value.')
            logger.error('(IOError) Cannot read {0} file'.format(self.path_tr))
            raise AddonError('(IOError) Cannot read {0} file'.format(self.path_tr))
        
        # Return a Unicode string.
        if encoding is None or file_bytes is None:
            return file_bytes
        
        if type(file_bytes) == str:
            return file_bytes

        return file_bytes.decode(encoding)
    
    #
    # data_str is a Unicode string. Encode it in UTF-8 for file writing.
    #
    def saveStrToFile(self, data_str: str, encoding = 'utf-8'):
        if DEBUG_NEWFILENAME_CLASS:
            logger.debug('FileName::loadFileToStr() Loading path_str "{0}"'.format(self.path_str))
            logger.debug('FileName::loadFileToStr() Loading path_tr  "{0}"'.format(self.path_tr))

        data = data_str if encoding == 'utf-8' else data_str.encode(encoding)
        # --- Catch exceptions in the FilaName class ---
        try:
            self.open('w')
            self.write(data)
            self.close()
        except OSError:
            logger.error('(OSError) Exception in saveStrToFile()')
            logger.error('(OSError) Cannot write {0} file'.format(self.path_tr))
            raise AddonError('(OSError) Cannot write {0} file'.format(self.path_tr))
        except IOError as e:
            logger.error('(IOError) Exception in saveStrToFile()')
            logger.error('(IOError) errno = {0}'.format(e.errno))
            if e.errno == errno.ENOENT: logger.error('(IOError) No such file or directory.')
            else:                       logger.error('(IOError) Unhandled errno value.')
            logger.error('(IOError) Cannot write {0} file'.format(self.path_tr))
            raise AddonError('(IOError) Cannot write {0} file'.format(self.path_tr))

    # Opens a propery file and reads it
    # Reads a given properties file with each line of the format key=value.
    # Returns a dictionary containing the pairs.
    def readPropertyFile(self):
        import csv

        file_contents = self.loadFileToStr()
        file_lines = file_contents.splitlines()

        result={ }
        reader = csv.reader(self._utf_8_encoder(file_lines), delimiter=str('='), quotechar=str('"'), quoting=csv.QUOTE_MINIMAL, skipinitialspace=True)
        for row in reader:
            if len(row) < 2:
               continue
            
            key = str(row[0],'utf-8').strip()
            value = str(row[1],'utf-8').strip().lstrip('"').rstrip('"')
            result[key] = value

        return result

    def _utf_8_encoder(self, unicode_csv_data):
        for line in unicode_csv_data:
            yield line.encode('utf-8')

    # Opens JSON file and reads it
    def readJson(self):
        contents = self.loadFileToStr()
        return json.loads(contents)
        
    # --- Configure JSON writer ---
    # >> json_unicode is either str or unicode
    # >> See https://docs.python.org/2.7/library/json.html#json.dumps
    # unicode(json_data) auto-decodes data to unicode if str
    # NOTE More compact JSON files (less blanks) load faster because size is smaller.
    def writeJson(self, raw_data, JSON_indent = 1, JSON_separators = (',', ':')):
        json_data = json.dumps(raw_data, ensure_ascii = False, sort_keys = True, 
                                indent = JSON_indent, separators = JSON_separators)
        self.saveStrToFile(json_data)

    def readXml(self) -> ET.ElementTree:
        tree = None
        try:
            tree = ET.parse(self.getPath())
        except ET.ParseError as e:
            logger.error('(ParseError) Exception parsing XML {}'.format(self.getPath()))
            logger.error('(ParseError) {0}'.format(str(e)))
    
        return tree

    # Opens file and writes xml. Give xml root element.
    def writeXml(self, xml_root):
        data = ET.tostring(xml_root)
        self.saveStrToFile(data)

    def writeAll(self, bytes, flags = 'w'):
         # --- Catch exceptions in the FilaName class ---
        try:
            self.open(flags)
            self.write(bytes)
            self.close()
        except OSError:
            logger.error('(OSError) Exception in writeAll()')
            logger.error('(OSError) Cannot write {0} file'.format(self.path_tr))
            raise AddonError('(OSError) Cannot write {0} file'.format(self.path_tr))
        except IOError as e:
            logger.error('(IOError) Exception in writeAll()')
            logger.error('(IOError) errno = {0}'.format(e.errno))
            if e.errno == errno.ENOENT: logger.error('(IOError) No such file or directory.')
            else:                       logger.error('(IOError) Unhandled errno value.')
            logger.error('(IOError) Cannot write {0} file'.format(self.path_tr))
            raise AddonError('(IOError) Cannot write {0} file'.format(self.path_tr))
        
    # ---------------------------------------------------------------------------------------------
    # Scanner functions
    # ---------------------------------------------------------------------------------------------
    def scanFilesInPath(self, mask = '*.*'):
        files = []
        all_files = self.list()
        
        for filename in fnmatch.filter(all_files, mask):
            files.append(self.pjoin(filename))
            
        return files
    
    def recursiveScanFilesInPath(self, mask = '*.*'):
        files = []
        all_files = self.recursive_list()
        
        for filename in fnmatch.filter(all_files, mask):
            files.append(self.pjoin(filename))
            
        return files

# --- Determine interpreter running platform ---
# Cache all possible platform values in global variables for maximum speed.
# See http://stackoverflow.com/questions/446209/possible-values-from-sys-platform
cached_sys_platform = sys.platform
def _aux_is_android():
    if not cached_sys_platform.startswith('linux'): return False
    return 'ANDROID_ROOT' in os.environ or 'ANDROID_DATA' in os.environ or 'XBMC_ANDROID_APK' in os.environ

is_windows_bool = cached_sys_platform == 'win32' or cached_sys_platform == 'win64' or cached_sys_platform == 'cygwin'
is_osx_bool     = cached_sys_platform.startswith('darwin')
is_android_bool = _aux_is_android()
is_linux_bool   = cached_sys_platform.startswith('linux') and not is_android_bool

def is_windows():
    return is_windows_bool

def is_osx():
    return is_osx_bool

def is_android():
    return is_android_bool

def is_linux():
    return is_linux_bool


# -------------------------------------------------------------------------------------------------
# Misc stuff
# -------------------------------------------------------------------------------------------------
#
# Given the image path, image filename with no extension and a list of file extensions search for 
# a file.
#
# rootPath       -> FileName object
# filename_noext -> Unicode string
# file_exts      -> list of extenstions with no dot [ 'zip', 'rar' ]
#
# Returns a FileName object if a valid filename is found.
# Returns None if no file was found.
#
def misc_look_for_file(rootPath, filename_noext, file_exts):
    for ext in file_exts:
        file_path = rootPath.pjoin(filename_noext + '.' + ext)
        if file_path.exists():
            return file_path

    return None
