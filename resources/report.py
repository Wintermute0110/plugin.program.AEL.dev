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
from abc import ABCMeta
from abc import abstractmethod

# --- AEL modules ---
from utils import *

#
# This must be implemented as a list of strings. See AML for more details.
#
def m_misc_print_string_ROM(rom):
    info_text  = ''
    info_text += "[COLOR violet]id[/COLOR]: '{0}'\n".format(rom.get_id())
    # >> Metadata
    info_text += "[COLOR violet]m_name[/COLOR]: '{0}'\n".format(rom.get_name())
    info_text += "[COLOR violet]m_year[/COLOR]: '{0}'\n".format(rom.get_releaseyear())
    info_text += "[COLOR violet]m_genre[/COLOR]: '{0}'\n".format(rom.get_genre())
    info_text += "[COLOR violet]m_developer[/COLOR]: '{0}'\n".format(rom.get_developer())
    info_text += "[COLOR violet]m_nplayers[/COLOR]: '{0}'\n".format(rom.get_number_of_players())
    info_text += "[COLOR violet]m_esrb[/COLOR]: '{0}'\n".format(rom.get_esrb_rating())
    info_text += "[COLOR violet]m_rating[/COLOR]: '{0}'\n".format(rom.get_rating())
    info_text += "[COLOR violet]m_plot[/COLOR]: '{0}'\n".format(rom.get_plot())
    # >> Info
    info_text += "[COLOR violet]filename[/COLOR]: '{0}'\n".format(rom.get_filename())        
    info_text += "[COLOR skyblue]disks[/COLOR]: {0}\n".format(rom.get_disks())
    info_text += "[COLOR violet]altapp[/COLOR]: '{0}'\n".format(rom.get_alternative_application())
    info_text += "[COLOR violet]altarg[/COLOR]: '{0}'\n".format(rom.get_alternative_arguments())
    info_text += "[COLOR skyblue]finished[/COLOR]: {0}\n".format(rom.is_finished())
    info_text += "[COLOR violet]nointro_status[/COLOR]: '{0}'\n".format(rom.get_nointro_status())
    info_text += "[COLOR violet]pclone_status[/COLOR]: '{0}'\n".format(rom.get_pclone_status())
    info_text += "[COLOR violet]cloneof[/COLOR]: '{0}'\n".format(rom.get_clone())
    # >> Assets/artwork
    asset_infos = self.assetFactory.get_asset_kinds_for_roms()
    for asset_info in asset_infos:
        info_text += "[COLOR violet]{0}[/COLOR]: '{1}'\n".format(asset_info.key, rom.get_asset(asset_info))

    return info_text

def m_misc_print_string_ROM_additional(rom):
    info_text  = ''
    info_text += "[COLOR violet]launcherID[/COLOR]: '{0}'\n".format(rom['launcherID'])
    info_text += "[COLOR violet]platform[/COLOR]: '{0}'\n".format(rom['platform'])
    info_text += "[COLOR violet]application[/COLOR]: '{0}'\n".format(rom['application'])
    info_text += "[COLOR violet]args[/COLOR]: '{0}'\n".format(rom['args'])
    info_text += "[COLOR skyblue]args_extra[/COLOR]: {0}\n".format(rom['args_extra'])
    info_text += "[COLOR violet]rompath[/COLOR]: '{0}'\n".format(rom['rompath'])
    info_text += "[COLOR violet]romext[/COLOR]: '{0}'\n".format(rom['romext'])
    info_text += "[COLOR skyblue]toggle_window[/COLOR]: {0}\n".format(rom['toggle_window'])
    info_text += "[COLOR skyblue]non_blocking[/COLOR]: {0}\n".format(rom['non_blocking'])
    info_text += "[COLOR violet]roms_default_icon[/COLOR]: '{0}'\n".format(rom['roms_default_icon'])
    info_text += "[COLOR violet]roms_default_fanart[/COLOR]: '{0}'\n".format(rom['roms_default_fanart'])
    info_text += "[COLOR violet]roms_default_banner[/COLOR]: '{0}'\n".format(rom['roms_default_banner'])
    info_text += "[COLOR violet]roms_default_poster[/COLOR]: '{0}'\n".format(rom['roms_default_poster'])
    info_text += "[COLOR violet]roms_default_clearlogo[/COLOR]: '{0}'\n".format(rom['roms_default_clearlogo'])

    # >> Favourite ROMs unique fields.
    info_text += "[COLOR violet]fav_status[/COLOR]: '{0}'\n".format(rom['fav_status'])
    # >> 'launch_count' only in Favourite ROMs in "Most played ROMs"
    if 'launch_count' in rom:
        info_text += "[COLOR skyblue]launch_count[/COLOR]: {0}\n".format(rom['launch_count'])

    return info_text

def m_misc_print_string_Launcher(launcher):
    launcher_data = launcher.get_data()

    info_text  = ''
    info_text += "[COLOR violet]id[/COLOR]: '{0}'\n".format(launcher_data['id'])
    info_text += "[COLOR violet]m_name[/COLOR]: '{0}'\n".format(launcher_data['m_name'])
    info_text += "[COLOR violet]m_year[/COLOR]: '{0}'\n".format(launcher_data['m_year'])
    info_text += "[COLOR violet]m_genre[/COLOR]: '{0}'\n".format(launcher_data['m_genre'])
    info_text += "[COLOR violet]m_developer[/COLOR]: '{0}'\n".format(launcher_data['m_developer'])
    info_text += "[COLOR violet]m_rating[/COLOR]: '{0}'\n".format(launcher_data['m_rating'])
    info_text += "[COLOR violet]m_plot[/COLOR]: '{0}'\n".format(launcher_data['m_plot'])

    info_text += "[COLOR violet]platform[/COLOR]: '{0}'\n".format(launcher_data['platform'])
    info_text += "[COLOR violet]categoryID[/COLOR]: '{0}'\n".format(launcher_data['categoryID'])
    info_text += "[COLOR violet]application[/COLOR]: '{0}'\n".format(launcher_data['application'])
    info_text += "[COLOR violet]args[/COLOR]: '{0}'\n".format(launcher_data['args'])
    info_text += "[COLOR skyblue]args_extra[/COLOR]: {0}\n".format(launcher_data['args_extra'])
    info_text += "[COLOR violet]rompath[/COLOR]: '{0}'\n".format(launcher_data['rompath'])
    info_text += "[COLOR violet]romext[/COLOR]: '{0}'\n".format(launcher_data['romext'])
    # Bool settings
    info_text += "[COLOR skyblue]finished[/COLOR]: {0}\n".format(launcher_data['finished'])
    info_text += "[COLOR skyblue]toggle_window[/COLOR]: {0}\n".format(launcher_data['toggle_window'])
    info_text += "[COLOR skyblue]non_blocking[/COLOR]: {0}\n".format(launcher_data['non_blocking'])
    info_text += "[COLOR skyblue]multidisc[/COLOR]: {0}\n".format(launcher_data['multidisc'])

    info_text += "[COLOR violet]roms_base_noext[/COLOR]: '{0}'\n".format(launcher_data['roms_base_noext'])
    info_text += "[COLOR violet]nointro_xml_file[/COLOR]: '{0}'\n".format(launcher_data['nointro_xml_file'])
    info_text += "[COLOR violet]nointro_display_mode[/COLOR]: '{0}'\n".format(launcher_data['nointro_display_mode'])
    info_text += "[COLOR violet]launcher_display_mode[/COLOR]: '{0}'\n".format(launcher_data['launcher_display_mode'])
    info_text += "[COLOR skyblue]num_roms[/COLOR]: {0}\n".format(launcher_data['num_roms'])
    info_text += "[COLOR skyblue]num_parents[/COLOR]: {0}\n".format(launcher_data['num_parents'])
    info_text += "[COLOR skyblue]num_clones[/COLOR]: {0}\n".format(launcher_data['num_clones'])
    info_text += "[COLOR skyblue]num_have[/COLOR]: {0}\n".format(launcher_data['num_have'])
    info_text += "[COLOR skyblue]num_miss[/COLOR]: {0}\n".format(launcher_data['num_miss'])
    info_text += "[COLOR skyblue]num_unknown[/COLOR]: {0}\n".format(launcher_data['num_unknown'])
    info_text += "[COLOR skyblue]timestamp_launcher_data[/COLOR]: {0}\n".format(launcher_data['timestamp_launcher'])
    info_text += "[COLOR skyblue]timestamp_report[/COLOR]: {0}\n".format(launcher_data['timestamp_report'])

    info_text += "[COLOR violet]default_icon[/COLOR]: '{0}'\n".format(launcher_data['default_icon'])
    info_text += "[COLOR violet]default_fanart[/COLOR]: '{0}'\n".format(launcher_data['default_fanart'])
    info_text += "[COLOR violet]default_banner[/COLOR]: '{0}'\n".format(launcher_data['default_banner'])
    info_text += "[COLOR violet]default_poster[/COLOR]: '{0}'\n".format(launcher_data['default_poster'])
    info_text += "[COLOR violet]default_clearlogo[/COLOR]: '{0}'\n".format(launcher_data['default_clearlogo'])
    info_text += "[COLOR violet]default_controller[/COLOR]: '{0}'\n".format(launcher_data['default_controller'])
    info_text += "[COLOR violet]Asset_Prefix[/COLOR]: '{0}'\n".format(launcher_data['Asset_Prefix'])
    info_text += "[COLOR violet]s_icon[/COLOR]: '{0}'\n".format(launcher_data['s_icon'])
    info_text += "[COLOR violet]s_fanart[/COLOR]: '{0}'\n".format(launcher_data['s_fanart'])
    info_text += "[COLOR violet]s_banner[/COLOR]: '{0}'\n".format(launcher_data['s_banner'])
    info_text += "[COLOR violet]s_poster[/COLOR]: '{0}'\n".format(launcher_data['s_poster'])
    info_text += "[COLOR violet]s_clearlogo[/COLOR]: '{0}'\n".format(launcher_data['s_clearlogo'])
    info_text += "[COLOR violet]s_controller[/COLOR]: '{0}'\n".format(launcher_data['s_controller'])
    info_text += "[COLOR violet]s_trailer[/COLOR]: '{0}'\n".format(launcher_data['s_trailer'])

    info_text += "[COLOR violet]roms_default_icon[/COLOR]: '{0}'\n".format(launcher_data['roms_default_icon'])
    info_text += "[COLOR violet]roms_default_fanart[/COLOR]: '{0}'\n".format(launcher_data['roms_default_fanart'])
    info_text += "[COLOR violet]roms_default_banner[/COLOR]: '{0}'\n".format(launcher_data['roms_default_banner'])
    info_text += "[COLOR violet]roms_default_poster[/COLOR]: '{0}'\n".format(launcher_data['roms_default_poster'])
    info_text += "[COLOR violet]roms_default_clearlogo[/COLOR]: '{0}'\n".format(launcher_data['roms_default_clearlogo'])
    info_text += "[COLOR violet]ROM_asset_path[/COLOR]: '{0}'\n".format(launcher_data['ROM_asset_path'])
    info_text += "[COLOR violet]path_title[/COLOR]: '{0}'\n".format(launcher_data['path_title'])
    info_text += "[COLOR violet]path_snap[/COLOR]: '{0}'\n".format(launcher_data['path_snap'])
    info_text += "[COLOR violet]path_boxfront[/COLOR]: '{0}'\n".format(launcher_data['path_boxfront'])
    info_text += "[COLOR violet]path_boxback[/COLOR]: '{0}'\n".format(launcher_data['path_boxback'])
    info_text += "[COLOR violet]path_cartridge[/COLOR]: '{0}'\n".format(launcher_data['path_cartridge'])
    info_text += "[COLOR violet]path_fanart[/COLOR]: '{0}'\n".format(launcher_data['path_fanart'])
    info_text += "[COLOR violet]path_banner[/COLOR]: '{0}'\n".format(launcher_data['path_banner'])
    info_text += "[COLOR violet]path_clearlogo[/COLOR]: '{0}'\n".format(launcher_data['path_clearlogo'])
    info_text += "[COLOR violet]path_flyer[/COLOR]: '{0}'\n".format(launcher_data['path_flyer'])
    info_text += "[COLOR violet]path_map[/COLOR]: '{0}'\n".format(launcher_data['path_map'])
    info_text += "[COLOR violet]path_manual[/COLOR]: '{0}'\n".format(launcher_data['path_manual'])
    info_text += "[COLOR violet]path_trailer[/COLOR]: '{0}'\n".format(launcher_data['path_trailer'])

    return info_text

def m_misc_print_string_Category(category):
    info_text  = ''
    info_text += "[COLOR violet]id[/COLOR]: '{0}'\n".format(category['id'])
    info_text += "[COLOR violet]m_name[/COLOR]: '{0}'\n".format(category['m_name'])
    info_text += "[COLOR violet]m_year[/COLOR]: '{0}'\n".format(category['m_year'])
    info_text += "[COLOR violet]m_genre[/COLOR]: '{0}'\n".format(category['m_genre'])
    info_text += "[COLOR violet]m_developer[/COLOR]: '{0}'\n".format(category['m_developer'])
    info_text += "[COLOR violet]m_rating[/COLOR]: '{0}'\n".format(category['m_rating'])
    info_text += "[COLOR violet]m_plot[/COLOR]: '{0}'\n".format(category['m_plot'])
    info_text += "[COLOR skyblue]finished[/COLOR]: {0}\n".format(category['finished'])
    info_text += "[COLOR violet]default_icon[/COLOR]: '{0}'\n".format(category['default_icon'])
    info_text += "[COLOR violet]default_fanart[/COLOR]: '{0}'\n".format(category['default_fanart'])
    info_text += "[COLOR violet]default_banner[/COLOR]: '{0}'\n".format(category['default_banner'])
    info_text += "[COLOR violet]default_poster[/COLOR]: '{0}'\n".format(category['default_poster'])
    info_text += "[COLOR violet]default_clearlogo[/COLOR]: '{0}'\n".format(category['default_clearlogo'])
    info_text += "[COLOR violet]Asset_Prefix[/COLOR]: '{0}'\n".format(category['Asset_Prefix'])
    info_text += "[COLOR violet]s_icon[/COLOR]: '{0}'\n".format(category['s_icon'])
    info_text += "[COLOR violet]s_fanart[/COLOR]: '{0}'\n".format(category['s_fanart'])
    info_text += "[COLOR violet]s_banner[/COLOR]: '{0}'\n".format(category['s_banner'])
    info_text += "[COLOR violet]s_poster[/COLOR]: '{0}'\n".format(category['s_poster'])
    info_text += "[COLOR violet]s_clearlogo[/COLOR]: '{0}'\n".format(category['s_clearlogo'])
    info_text += "[COLOR violet]s_trailer[/COLOR]: '{0}'\n".format(category['s_trailer'])

    return info_text

def m_misc_print_string_Collection(collection):
    info_text  = ''
    info_text += "[COLOR violet]id[/COLOR]: '{0}'\n".format(collection['id'])
    info_text += "[COLOR violet]m_name[/COLOR]: '{0}'\n".format(collection['m_name'])
    info_text += "[COLOR violet]m_genre[/COLOR]: '{0}'\n".format(collection['m_genre'])
    info_text += "[COLOR violet]m_rating[/COLOR]: '{0}'\n".format(collection['m_rating'])
    info_text += "[COLOR violet]m_plot[/COLOR]: '{0}'\n".format(collection['m_plot'])
    info_text += "[COLOR violet]roms_base_noext[/COLOR]: {0}\n".format(collection['roms_base_noext'])
    info_text += "[COLOR violet]default_icon[/COLOR]: '{0}'\n".format(collection['default_icon'])
    info_text += "[COLOR violet]default_fanart[/COLOR]: '{0}'\n".format(collection['default_fanart'])
    info_text += "[COLOR violet]default_banner[/COLOR]: '{0}'\n".format(collection['default_banner'])
    info_text += "[COLOR violet]default_poster[/COLOR]: '{0}'\n".format(collection['default_poster'])
    info_text += "[COLOR violet]default_clearlogo[/COLOR]: '{0}'\n".format(collection['default_clearlogo'])
    info_text += "[COLOR violet]s_icon[/COLOR]: '{0}'\n".format(collection['s_icon'])
    info_text += "[COLOR violet]s_fanart[/COLOR]: '{0}'\n".format(collection['s_fanart'])
    info_text += "[COLOR violet]s_banner[/COLOR]: '{0}'\n".format(collection['s_banner'])
    info_text += "[COLOR violet]s_poster[/COLOR]: '{0}'\n".format(collection['s_poster'])
    info_text += "[COLOR violet]s_clearlogo[/COLOR]: '{0}'\n".format(collection['s_clearlogo'])
    info_text += "[COLOR violet]s_trailer[/COLOR]: '{0}'\n".format(collection['s_trailer'])

    return info_text

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
