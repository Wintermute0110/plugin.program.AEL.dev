# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher
# Copyright (c) 2016-2018 Wintermute0110 <wintermute0110@gmail.com>
# Portions (c) 2010-2015 Angelscry and others
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# -------------------------------------------------------------------------------------------------
# Utility functions which DEPEND on Kodi modules
# -------------------------------------------------------------------------------------------------
# --- Python compiler flags ---
from __future__ import unicode_literals

# --- Python standard library ---
from abc import ABCMeta, abstractmethod

import sys, os, shutil, urlparse, json, fnmatch
import xml.etree.ElementTree as ET

# --- Kodi modules ---
try:
    import xbmc, xbmcvfs
except:
    from utils_kodi_standalone import *

# -------------------------------------------------------------------------------------------------
# Factory for creating new FileName instances.
# Can either create a FileName base on xmbcvfs or just normal os operations.
# -------------------------------------------------------------------------------------------------
class FileNameFactory():

    @staticmethod
    def create(pathString, no_xbmcvfs = False):

        if no_xbmcvfs:
            return StandardFileName(pathString)
        
        return KodiFileName(pathString)

# -------------------------------------------------------------------------------------------------
# Filesystem abstract base class
# This class and classes that inherit this one always take and return Unicode string paths.
# Decoding Unicode to UTF-8 or whatever must be done in the caller code.
#
# IMPROVE THE DOCUMENTATION OF THIS CLASS AND HOW IT HANDLES EXCEPTIONS AND ERROR REPORTING!!!
#
# A) Transform paths like smb://server/directory/ into \\server\directory\
# B) Use xbmc.translatePath() for paths starting with special://
# C) Uses xbmcvfs wherever possible
#
# -------------------------------------------------------------------------------------------------
class FileName():
    __metaclass__ = ABCMeta

    # pathString must be a Unicode string object
    def __init__(self, pathString):
        self.originalPath = pathString
        self.path         = pathString
        
        # --- Path transformation ---
        if self.originalPath.lower().startswith('smb:'):
            self.path = self.path.replace('smb:', '')
            self.path = self.path.replace('SMB:', '')
            self.path = self.path.replace('//', '\\\\')
            self.path = self.path.replace('/', '\\')

        elif self.originalPath.lower().startswith('special:'):
            self.path = xbmc.translatePath(self.path)

    # abstract protected method, to be implemented in child classes.
    # Will return a new instance of the desired child implementation.
    @abstractmethod
    def __create__(self, pathString):
        return FileName(pathString)

    def _join_raw(self, arg):
        self.path         = os.path.join(self.path, arg)
        self.originalPath = os.path.join(self.originalPath, arg)

        return self

    # Appends a string to path. Returns self FileName object
    def append(self, arg):
        self.path         = self.path + arg
        self.originalPath = self.originalPath + arg

        return self

    # >> Joins paths. Returns a new FileName object
    def pjoin(self, *args):
        child = self.__create__(self.originalPath)
        for arg in args:
            child._join_raw(arg)

        return child

    # Behaves like os.path.join()
    #
    # See http://blog.teamtreehouse.com/operator-overloading-python
    # other is a FileName object. other originalPath is expected to be a subdirectory (path
    # transformation not required)
    def __add__(self, other):
        current_path = self.originalPath
        if type(other) is FileName:  other_path = other.originalPath
        elif type(other) is unicode: other_path = other
        elif type(other) is str:     other_path = other.decode('utf-8')
        else: raise NameError('Unknown type for overloaded + in FileName object')
        new_path = os.path.join(current_path, other_path)
        child    = self.__create__(new_path)

        return child
        
    def escapeQuotes(self):
        self.path = self.path.replace("'", "\\'")
        self.path = self.path.replace('"', '\\"')

    def path_separator(self):
        count_backslash = self.originalPath.count('\\')
        count_forwardslash = self.originalPath.count('/')

        if count_backslash > count_forwardslash:
            return '\\'
        
        return '/'

    # ---------------------------------------------------------------------------------------------
    # Decomposes a file name path or directory into its constituents
    #   FileName.getOriginalPath()  Full path                                     /home/Wintermute/Sonic.zip
    #   FileName.getPath()          Full path                                     /home/Wintermute/Sonic.zip
    #   FileName.getPath_noext()    Full path with no extension                   /home/Wintermute/Sonic
    #   FileName.getDir()           Directory name of file. Does not end in '/'   /home/Wintermute/
    #   FileName.getBase()          File name with no path                        Sonic.zip
    #   FileName.getBase_noext()    File name with no path and no extension       Sonic
    #   FileName.getExt()           File extension                                .zip
    # ---------------------------------------------------------------------------------------------
    def getOriginalPath(self):
        return self.originalPath

    def getPath(self):
        return self.path

    def getPath_noext(self):
        root, ext = os.path.splitext(self.path)

        return root

    def getDir(self):
        return os.path.dirname(self.path)

    def getDirAsFileName(self):
        return self.__create__(self.getDir())

    def getBase(self):
        return os.path.basename(self.path)

    def getBase_noext(self):
        basename  = os.path.basename(self.path)
        root, ext = os.path.splitext(basename)
        
        return root

    def getExt(self):
        root, ext = os.path.splitext(self.path)
        return ext

    def switchExtension(self, targetExt):
        
        ext = self.getExt()
        copiedPath = self.originalPath
        
        if not targetExt.startswith('.'):
            targetExt = '.{0}'.format(targetExt)

        new_path = self.__create__(copiedPath.replace(ext, targetExt))
        return new_path
    
    # Checks the extension to determine the type of the file
    def is_image_file(self):
        ext = self.getExt()
        return ext.lower() in ['png', 'jpg', 'gif', 'bmp']

    def is_video_file(self):
        ext = self.getExt()
        return ext.lower() in ['mov', 'divx', 'xvid', 'wmv', 'avi', 'mpg', 'mpeg', 'mp4', 'mkv', 'avc']
    
    def is_document(self):
        ext = self.getExt()
        return ext.lower() in ['txt', 'pdf', 'doc']
    
    # ---------------------------------------------------------------------------------------------
    # Scanner functions
    # ---------------------------------------------------------------------------------------------
    @abstractmethod
    def scanFilesInPath(self, mask = '*.*'):
        return []

    @abstractmethod
    def scanFilesInPathAsFileNameObjects(self, mask = '*.*'):
        return []
    
    @abstractmethod
    def recursiveScanFilesInPath(self, mask = '*.*'):
        return []

    @abstractmethod
    def recursiveScanFilesInPathAsFileNameObjects(self, mask = '*.*'):
        return []

    def _decodeName(self, name):
        if type(name) == str:
            try:
                name = name.decode('utf8')
            except:
                name = name.decode('windows-1252')
        
        return name
    
    # ---------------------------------------------------------------------------------------------
    # Filesystem functions
    # ---------------------------------------------------------------------------------------------
    @abstractmethod
    def stat(self):
        return None
    
    @abstractmethod
    def exists(self):
        return None
    
    @abstractmethod
    def isdir(self):
        return False
        
    @abstractmethod
    def isfile(self):
        return False
    
    @abstractmethod
    def makedirs(self):
        pass
    
    @abstractmethod
    def unlink(self):
        pass
    
    @abstractmethod
    def rename(self, to):
        pass
    
    @abstractmethod
    def copy(self, to):        
        pass
                    
    # ---------------------------------------------------------------------------------------------
    # File IO functions
    # ---------------------------------------------------------------------------------------------
    
    @abstractmethod
    def readline(self):
        return None
    
    @abstractmethod
    def readAll(self):
        return None
    
    @abstractmethod
    def readAllUnicode(self, encoding='utf-8'):
        return None
    
    @abstractmethod
    def writeAll(self, bytes, flags='w'):
        pass
    
    @abstractmethod
    def write(self, bytes):
        pass
       
    @abstractmethod
    def open(self, flags):
        pass
      
    @abstractmethod
    def close(self):
        pass

    # Opens file and reads xml. Returns the root of the XML!
    def readXml(self):
        data = self.readAll()
        root = ET.fromstring(data)
        return root

    # Opens JSON file and reads it
    def readJson(self):
        contents = self.readAllUnicode()
        return json.loads(contents)

    # Opens INI file and reads it
    def readIniFile(self):
        import ConfigParser
    
        config = ConfigParser.ConfigParser()
        config.readfp(self.open('r'))

        return config

    # Opens a propery file and reads it
    # Reads a given properties file with each line of the format key=value.  Returns a dictionary containing the pairs.
    def readPropertyFile(self):
        import csv
        
        file_contents = self.readAll()
        file_lines = file_contents.splitlines()

        result={ }
        reader = csv.reader(file_lines, delimiter=str('='), quoting=csv.QUOTE_NONE)
        for row in reader:
            if len(row) != 2:
                raise csv.Error("Too many fields on row with contents: "+str(row))
            result[row[0].strip()] = row[1].strip().lstrip('"').rstrip('"')
        
        return result

    # --- Configure JSON writer ---
    # >> json_unicode is either str or unicode
    # >> See https://docs.python.org/2.7/library/json.html#json.dumps
    # unicode(json_data) auto-decodes data to unicode if str
    # NOTE More compact JSON files (less blanks) load faster because size is smaller.
    def writeJson(self, raw_data, JSON_indent = 1, JSON_separators = (',', ':')):
        json_data = json.dumps(raw_data, ensure_ascii = False, sort_keys = True, 
                                indent = JSON_indent, separators = JSON_separators)
        self.writeAll(unicode(json_data).encode('utf-8'))

    # Opens file and writes xml. Give xml root element.
    def writeXml(self, xml_root):
        data = ET.tostring(xml_root)
        self.writeAll(data)

    def __str__(self):
        return self.getOriginalPath()

# -------------------------------------------------------------------------------------------------
# Kodi Virtual Filesystem helper class.
# Implementation of the FileName helper class which supports the xbmcvfs libraries.
#
# -------------------------------------------------------------------------------------------------
class KodiFileName(FileName):
    
    def __create__(self, pathString):
        return KodiFileName(pathString)

    # ---------------------------------------------------------------------------------------------
    # Scanner functions
    # ---------------------------------------------------------------------------------------------
    def scanFilesInPath(self, mask = '*.*'):
        files = []

        subdirectories, filenames = xbmcvfs.listdir(self.originalPath)
        for filename in fnmatch.filter(filenames, mask):
            files.append(os.path.join(self.originalPath, self._decodeName(filename)))

        return files

    def scanFilesInPathAsFileNameObjects(self, mask = '*.*'):
        files = []
        
        subdirectories, filenames = xbmcvfs.listdir(self.originalPath)
        for filename in fnmatch.filter(filenames, mask):
            filePath = self.pjoin(self._decodeName(filename))
            files.append(self.__create__(filePath.getOriginalPath()))

        return files

    def recursiveScanFilesInPath(self, mask = '*.*'):
        files = []
        
        subdirectories, filenames = xbmcvfs.listdir(str(self.originalPath))
        for filename in fnmatch.filter(filenames, mask):
            filePath = self.pjoin(self._decodeName(filename))
            files.append(filePath.getOriginalPath())

        for subdir in subdirectories:
            subPath = self.pjoin(self._decodeName(subdir))
            subPathFiles = subPath.recursiveScanFilesInPath(mask)
            files.extend(subPathFiles)

        return files
    
    def recursiveScanFilesInPathAsFileNameObjects(self, mask = '*.*'):
        files = []
        
        subdirectories, filenames = xbmcvfs.listdir(str(self.originalPath))
        for filename in fnmatch.filter(filenames, mask):
            filePath = self.pjoin(self._decodeName(filename))
            files.append(self.__create__(filePath.getOriginalPath()))

        for subdir in subdirectories:
            subPath = self.pjoin(self._decodeName(subdir))
            subPathFiles = subPath.recursiveScanFilesInPathAsFileNameObjects(mask)
            files.extend(subPathFiles)

        return files

    # ---------------------------------------------------------------------------------------------
    # Filesystem functions
    # ---------------------------------------------------------------------------------------------
    def stat(self):
        return xbmcvfs.Stat(self.originalPath)

    def exists(self):
        return xbmcvfs.exists(self.originalPath)

    # Warning: not suitable for xbmcvfs paths yet
    def isdir(self):
        
        if not self.exists():
            return False

        try:
            self.open('r')
            self.close()
        except:
            return True
        
        return False
        #return os.path.isdir(self.path)
        
    # Warning: not suitable for xbmcvfs paths yet
    def isfile(self):

        if not self.exists():
            return False

        return not self.isdir()
        #return os.path.isfile(self.path)

    def makedirs(self):
        
        if not self.exists():
            xbmcvfs.mkdirs(self.originalPath)

    def unlink(self):

        if self.isfile():
            xbmcvfs.delete(self.originalPath)

            # hard delete if it doesnt succeed
            #log_debug('xbmcvfs.delete() failed, applying hard delete')
            if self.exists():
                os.remove(self.path)
        else:
            xbmcvfs.rmdir(self.originalPath)

    def rename(self, to):

        if self.isfile():
            xbmcvfs.rename(self.originalPath, to.getOriginalPath())
        else:
            os.rename(self.path, to.getPath())

    def copy(self, to):        
        xbmcvfs.copy(self.getOriginalPath(), to.getOriginalPath())
                    
    # ---------------------------------------------------------------------------------------------
    # File IO functions
    # ---------------------------------------------------------------------------------------------
    
    def readline(self, encoding='utf-8'):
        if self.fileHandle is None:
            raise OSError('file not opened')

        line = u''
        char = self.fileHandle.read(1)
        if char is '':
            return ''

        while char and char != u'\n':
            line += unicode(char, encoding)
            char = self.fileHandle.read(1)

        return line

    def readAll(self):
        contents = None
        file = xbmcvfs.File(self.originalPath)
        contents = file.read()
        file.close()

        return contents
    
    def readAllUnicode(self, encoding='utf-8'):
        contents = None
        file = xbmcvfs.File(self.originalPath)
        contents = file.read()
        file.close()

        return unicode(contents, encoding)
    
    def writeAll(self, bytes, flags='w'):
        file = xbmcvfs.File(self.originalPath, flags)
        file.write(bytes)
        file.close()

    def write(self, bytes):
       if self.fileHandle is None:
           raise OSError('file not opened')

       self.fileHandle.write(bytes)

    def open(self, flags):
        self.fileHandle = xbmcvfs.File(self.originalPath, flags)
        return self
        
    def close(self):
        if self.fileHandle is None:
           raise OSError('file not opened')

        self.fileHandle.close()
        self.fileHandle = None
        
# -------------------------------------------------------------------------------------------------
# Standard Filesystem helper class.
# Implementation of the FileName helper class which just uses standard os operations.
#
# -------------------------------------------------------------------------------------------------
class StandardFileName(FileName):
    
    def __create__(self, pathString):
        return StandardFileName(pathString)

    # ---------------------------------------------------------------------------------------------
    # Scanner functions
    # ---------------------------------------------------------------------------------------------
    def scanFilesInPath(self, mask = '*.*'):
        files = []

        entries = os.listdir(self.path)
        for filename in fnmatch.filter(entries, mask):
            files.append(os.path.join(self.path, self._decodeName(filename)))

        return files

    def scanFilesInPathAsFileNameObjects(self, mask = '*.*'):
        files = []
        
        entries = os.listdir(self.path)
        for filename in fnmatch.filter(entries, mask):
            filePath = self.pjoin(self._decodeName(filename))
            files.append(self.__create__(filePath.getPath()))

        return files

    def recursiveScanFilesInPath(self, mask = '*.*'):
        files = []

        for root, dirs, foundfiles in os.walk(self.path):
            for filename in fnmatch.filter(foundfiles, mask):
                filePath = self.pjoin(self._decodeName(filename))
                files.append(filePath.getPath())

        return files
        
    def recursiveScanFilesInPathAsFileNameObjects(self, mask = '*.*'):
        files = []
        
        for root, dirs, foundfiles in os.walk(self.path):
            for filename in fnmatch.filter(foundfiles, mask):
                filePath = self.__create__(fileName)
                files.append(filePath)

        return files

    # ---------------------------------------------------------------------------------------------
    # Filesystem functions
    # ---------------------------------------------------------------------------------------------
    def stat(self):
        return os.stat(self.path)

    def exists(self):
        return os.path.exists(self.path)

    def isdir(self):
        return os.path.isdir(self.path)
        
    def isfile(self):
        return os.path.isfile(self.path)

    def makedirs(self):
        if not os.path.exists(self.path): 
            os.makedirs(self.path)

    # os.remove() and os.unlink() are exactly the same.
    def unlink(self):
        os.unlink(self.path)

    def rename(self, to):
        os.rename(self.path, to.getPath())

    def copy(self, to):        
        shutil.copy2(self.getPath(), to.getPath())
     
    # ---------------------------------------------------------------------------------------------
    # File IO functions
    # ---------------------------------------------------------------------------------------------
    
    def readline(self):
        if self.fileHandle is None:
            raise OSError('file not opened')

        return self.fileHandle.readline()

    def readAll(self):
        contents = None
        with open(self.path, 'r') as f:
            contents = f.read()
        
        return contents
    
    def readAllUnicode(self, encoding='utf-8'):
        contents = None        
        with open(self.path, 'r') as f:
            contents = f.read()
        
        return unicode(contents, encoding)
    
    def writeAll(self, bytes, flags='w'):
        with open(self.path, flags) as file:
            file.write(bytes)

    def write(self, bytes):
       if self.fileHandle is None:
           raise OSError('file not opened')

       self.fileHandle.write(bytes)

    def open(self, flags):
        self.fileHandle = os.open(self.path, flags)
        return self
        
    def close(self):
        if self.fileHandle is None:
           raise OSError('file not opened')

        self.fileHandle.close()
        self.fileHandle = None