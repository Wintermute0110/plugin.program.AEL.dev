# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher platform and emulator information
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
from abc import ABCMeta, abstractmethod

from utils import *
from utils_kodi import *

class Reporter(object):
    __metaclass__ = ABCMeta

    def __init__(self, launcher_data, decoratorReporter = None):

        self.launcher_data = launcher_data
        self.decoratorReporter = decoratorReporter

    @abstractmethod
    def open(self):
        pass
    
    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def _write_message(self, message):
        pass

    def write(self, message):
        
        self._write_message(message)

        if self.decoratorReporter:
            self.decoratorReporter.write(message)

class LogReporter(Reporter):
       
    def open(self, report_title):
        return super(LogReporter, self).close()

    def close(self):
        return super(LogReporter, self).close()

    def _write_message(self, message):
        log_info(message)

class FileReporter(Reporter):
    
    def __init__(self, reports_dir, launcher_data, decoratorReporter = None):
        
        self.report_file = reports_dir.pjoin(launcher_data['roms_base_noext'] + '_report.txt')
        super(FileReporter, self).__init__(launcher_data, decoratorReporter)

    def open(self, report_title):

        log_info('Report file OP "{0}"'.format(self.report_file.getOriginalPath()))

        self.report_file.open('w')

        # --- Get information from launcher ---
        launcher_path = FileNameFactory.create(self.launcher_data['rompath'])
        
        self.write('******************** Report: {} ...  ********************'.format(report_title))
        self.write('  Launcher name "{0}"'.format(self.launcher_data['m_name']))
        self.write('  Launcher type "{0}"'.format(self.launcher_data['type'] if 'type' in self.launcher_data else 'Unknown'))
        self.write('  launcher ID   "{0}"'.format(self.launcher_data['id']))
        self.write('  ROM path      "{0}"'.format(launcher_path.getPath()))
        self.write('  ROM ext       "{0}"'.format(self.launcher_data['romext']))
        self.write('  Platform      "{0}"'.format(self.launcher_data['platform']))
        self.write(  'Multidisc     "{0}"'.format(self.launcher_data['multidisc']))
    
    def close(self):
        self.report_file.close()

    def _write_message(self, message):
        self.report_file.write(message.encode('utf-8'))
        self.report_file.write('\n'.encode('utf-8'))