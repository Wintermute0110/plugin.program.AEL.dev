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

# --- AEL modules ---
from resources.app.domain import *
#
# This must be implemented as a list of strings. See AML for more details.
#
def report_print_ROM(slist: list, rom: ROM):
    slist.append('')
    slist.append("[COLOR violet]id[/COLOR]: '{0}'".format(rom.get_id()))
    # >> Metadata
    slist.append("[COLOR violet]m_name[/COLOR]: '{0}'".format(rom.get_name()))
    slist.append("[COLOR violet]m_year[/COLOR]: '{0}'".format(rom.get_releaseyear()))
    slist.append("[COLOR violet]m_genre[/COLOR]: '{0}'".format(rom.get_genre()))
    slist.append("[COLOR violet]m_developer[/COLOR]: '{0}'".format(rom.get_developer()))
    slist.append("[COLOR violet]m_nplayers[/COLOR]: '{0}'".format(rom.get_number_of_players()))
    slist.append("[COLOR violet]m_esrb[/COLOR]: '{0}'".format(rom.get_esrb_rating()))
    slist.append("[COLOR violet]m_rating[/COLOR]: '{0}'".format(rom.get_rating()))
    slist.append("[COLOR violet]m_plot[/COLOR]: '{0}'".format(rom.get_plot()))
    # >> Info
    slist.append("[COLOR violet]filename[/COLOR]: '{0}'".format(rom.get_filename()))
    slist.append("[COLOR skyblue]disks[/COLOR]: {0}".format(rom.get_disks()))
    slist.append("[COLOR violet]altapp[/COLOR]: '{0}'".format(rom.get_alternative_application()))
    slist.append("[COLOR violet]altarg[/COLOR]: '{0}'".format(rom.get_alternative_arguments()))
    slist.append("[COLOR skyblue]finished[/COLOR]: {0}".format(rom.is_finished()))
    slist.append("[COLOR violet]nointro_status[/COLOR]: '{0}'".format(rom.get_nointro_status()))
    slist.append("[COLOR violet]pclone_status[/COLOR]: '{0}'".format(rom.get_pclone_status()))
    slist.append("[COLOR violet]cloneof[/COLOR]: '{0}'".format(rom.get_clone()))       
    slist.append("[COLOR skyblue]i_extra_ROM[/COLOR]: {0}\n".format(rom.get_extra_ROM()))

    # >> Assets/artwork
    asset_infos = g_assetFactory.get_asset_kinds_for_roms()
    for asset_info in asset_infos:
        slist.append("[COLOR violet]{0}[/COLOR]: '{1}'".format(asset_info.key, rom.get_asset(asset_info)))

    #return info_text
    return slist

def report_print_ROM_additional(slist: list, rom: dict):
    slist.append('')
    slist.append("[COLOR violet]launcherID[/COLOR]: '{0}'".format(rom['launcherID']))
    slist.append("[COLOR violet]platform[/COLOR]: '{0}'".format(rom['platform']))
    slist.append("[COLOR violet]application[/COLOR]: '{0}'".format(rom['application']))
    slist.append("[COLOR violet]args[/COLOR]: '{0}'".format(rom['args']))
    slist.append("[COLOR skyblue]args_extra[/COLOR]: {0}".format(rom['args_extra']))
    slist.append("[COLOR violet]rompath[/COLOR]: '{0}'".format(rom['rompath']))
    slist.append("[COLOR violet]romext[/COLOR]: '{0}'".format(rom['romext']))
    slist.append("[COLOR skyblue]toggle_window[/COLOR]: {0}".format(rom['toggle_window']))
    slist.append("[COLOR skyblue]non_blocking[/COLOR]: {0}".format(rom['non_blocking']))
    slist.append("[COLOR violet]roms_default_icon[/COLOR]: '{0}'".format(rom['roms_default_icon']))
    slist.append("[COLOR violet]roms_default_fanart[/COLOR]: '{0}'".format(rom['roms_default_fanart']))
    slist.append("[COLOR violet]roms_default_banner[/COLOR]: '{0}'".format(rom['roms_default_banner']))
    slist.append("[COLOR violet]roms_default_poster[/COLOR]: '{0}'".format(rom['roms_default_poster']))
    slist.append("[COLOR violet]roms_default_clearlogo[/COLOR]: '{0}'".format(rom['roms_default_clearlogo']))

    # >> Favourite ROMs unique fields.
    slist.append("[COLOR violet]fav_status[/COLOR]: '{0}'".format(rom['fav_status']))
    # >> 'launch_count' only in Favourite ROMs in "Most played ROMs"
    if 'launch_count' in rom:
        slist.append("[COLOR skyblue]launch_count[/COLOR]: {0}".format(rom['launch_count']))

def report_print_Launcher(slist, launcher_dic):
    slist.append("[COLOR violet]id[/COLOR]: '{0}'".format(launcher_dic['id']))
    slist.append("[COLOR violet]type[/COLOR]: '{0}'".format(launcher_dic['type']))
    slist.append("[COLOR violet]m_name[/COLOR]: '{0}'".format(launcher_dic['m_name']))
    slist.append("[COLOR violet]m_year[/COLOR]: '{0}'".format(launcher_dic['m_year']))
    slist.append("[COLOR violet]m_genre[/COLOR]: '{0}'".format(launcher_dic['m_genre']))
    slist.append("[COLOR violet]m_developer[/COLOR]: '{0}'".format(launcher_dic['m_developer']))
    slist.append("[COLOR violet]m_rating[/COLOR]: '{0}'".format(launcher_dic['m_rating']))
    slist.append("[COLOR violet]m_plot[/COLOR]: '{0}'".format(launcher_dic['m_plot']))

    slist.append("[COLOR violet]platform[/COLOR]: '{0}'".format(launcher_dic['platform']))
    slist.append("[COLOR violet]categoryID[/COLOR]: '{0}'".format(launcher_dic['categoryID']))
    slist.append("[COLOR violet]application[/COLOR]: '{0}'".format(launcher_dic['application']))
    slist.append("[COLOR violet]args[/COLOR]: '{0}'".format(launcher_dic['args']))
    slist.append("[COLOR skyblue]args_extra[/COLOR]: {0}".format(launcher_dic['args_extra']))
    slist.append("[COLOR violet]rompath[/COLOR]: '{0}'".format(launcher_dic['rompath']))
    slist.append("[COLOR violet]romext[/COLOR]: '{0}'".format(launcher_dic['romext']))
    slist.append("[COLOR violet]romextrapath[/COLOR]: '{0}'\n".format(launcher_dic['romextrapath']))

    # Bool settings
    slist.append("[COLOR skyblue]finished[/COLOR]: {0}".format(launcher_dic['finished']))
    slist.append("[COLOR skyblue]toggle_window[/COLOR]: {0}".format(launcher_dic['toggle_window']))
    slist.append("[COLOR skyblue]non_blocking[/COLOR]: {0}".format(launcher_dic['non_blocking']))
    slist.append("[COLOR skyblue]multidisc[/COLOR]: {0}".format(launcher_dic['multidisc']))

    slist.append("[COLOR violet]roms_base_noext[/COLOR]: '{0}'".format(launcher_dic['roms_base_noext']))
    slist.append("[COLOR violet]nointro_xml_file[/COLOR]: '{0}'".format(launcher_dic['nointro_xml_file']))
    slist.append("[COLOR violet]nointro_display_mode[/COLOR]: '{0}'".format(launcher_dic['nointro_display_mode']))
    slist.append("[COLOR violet]launcher_display_mode[/COLOR]: '{0}'".format(launcher_dic['launcher_display_mode']))
    slist.append("[COLOR skyblue]num_roms[/COLOR]: {0}".format(launcher_dic['num_roms']))
    slist.append("[COLOR skyblue]num_parents[/COLOR]: {0}".format(launcher_dic['num_parents']))
    slist.append("[COLOR skyblue]num_clones[/COLOR]: {0}".format(launcher_dic['num_clones']))
    slist.append("[COLOR skyblue]num_have[/COLOR]: {0}".format(launcher_dic['num_have']))
    slist.append("[COLOR skyblue]num_miss[/COLOR]: {0}".format(launcher_dic['num_miss']))
    slist.append("[COLOR skyblue]num_unknown[/COLOR]: {0}".format(launcher_dic['num_unknown']))
    slist.append("[COLOR skyblue]timestamp_launcher_dic[/COLOR]: {0}".format(launcher_dic['timestamp_launcher']))
    slist.append("[COLOR skyblue]timestamp_report[/COLOR]: {0}".format(launcher_dic['timestamp_report']))

    slist.append("[COLOR violet]default_icon[/COLOR]: '{0}'".format(launcher_dic['default_icon']))
    slist.append("[COLOR violet]default_fanart[/COLOR]: '{0}'".format(launcher_dic['default_fanart']))
    slist.append("[COLOR violet]default_banner[/COLOR]: '{0}'".format(launcher_dic['default_banner']))
    slist.append("[COLOR violet]default_poster[/COLOR]: '{0}'".format(launcher_dic['default_poster']))
    slist.append("[COLOR violet]default_clearlogo[/COLOR]: '{0}'".format(launcher_dic['default_clearlogo']))
    slist.append("[COLOR violet]default_controller[/COLOR]: '{0}'".format(launcher_dic['default_controller']))
    slist.append("[COLOR violet]Asset_Prefix[/COLOR]: '{0}'".format(launcher_dic['Asset_Prefix']))
    slist.append("[COLOR violet]s_icon[/COLOR]: '{0}'".format(launcher_dic['s_icon']))
    slist.append("[COLOR violet]s_fanart[/COLOR]: '{0}'".format(launcher_dic['s_fanart']))
    slist.append("[COLOR violet]s_banner[/COLOR]: '{0}'".format(launcher_dic['s_banner']))
    slist.append("[COLOR violet]s_poster[/COLOR]: '{0}'".format(launcher_dic['s_poster']))
    slist.append("[COLOR violet]s_clearlogo[/COLOR]: '{0}'".format(launcher_dic['s_clearlogo']))
    slist.append("[COLOR violet]s_controller[/COLOR]: '{0}'".format(launcher_dic['s_controller']))
    slist.append("[COLOR violet]s_trailer[/COLOR]: '{0}'".format(launcher_dic['s_trailer']))

    slist.append("[COLOR violet]roms_default_icon[/COLOR]: '{0}'".format(launcher_dic['roms_default_icon']))
    slist.append("[COLOR violet]roms_default_fanart[/COLOR]: '{0}'".format(launcher_dic['roms_default_fanart']))
    slist.append("[COLOR violet]roms_default_banner[/COLOR]: '{0}'".format(launcher_dic['roms_default_banner']))
    slist.append("[COLOR violet]roms_default_poster[/COLOR]: '{0}'".format(launcher_dic['roms_default_poster']))
    slist.append("[COLOR violet]roms_default_clearlogo[/COLOR]: '{0}'".format(launcher_dic['roms_default_clearlogo']))
    slist.append("[COLOR violet]ROM_asset_path[/COLOR]: '{0}'".format(launcher_dic['ROM_asset_path']))
    slist.append("[COLOR violet]path_title[/COLOR]: '{0}'".format(launcher_dic['path_title']))
    slist.append("[COLOR violet]path_snap[/COLOR]: '{0}'".format(launcher_dic['path_snap']))
    slist.append("[COLOR violet]path_boxfront[/COLOR]: '{0}'".format(launcher_dic['path_boxfront']))
    slist.append("[COLOR violet]path_boxback[/COLOR]: '{0}'".format(launcher_dic['path_boxback']))
    slist.append("[COLOR violet]path_cartridge[/COLOR]: '{0}'".format(launcher_dic['path_cartridge']))
    slist.append("[COLOR violet]path_fanart[/COLOR]: '{0}'".format(launcher_dic['path_fanart']))
    slist.append("[COLOR violet]path_banner[/COLOR]: '{0}'".format(launcher_dic['path_banner']))
    slist.append("[COLOR violet]path_clearlogo[/COLOR]: '{0}'".format(launcher_dic['path_clearlogo']))
    slist.append("[COLOR violet]path_flyer[/COLOR]: '{0}'".format(launcher_dic['path_flyer']))
    slist.append("[COLOR violet]path_map[/COLOR]: '{0}'".format(launcher_dic['path_map']))
    slist.append("[COLOR violet]path_manual[/COLOR]: '{0}'".format(launcher_dic['path_manual']))
    slist.append("[COLOR violet]path_trailer[/COLOR]: '{0}'".format(launcher_dic['path_trailer']))

def report_print_Category(slist, category_dic):
    slist.append("[COLOR violet]id[/COLOR]: '{0}'".format(category_dic['id']))
    slist.append("[COLOR violet]m_name[/COLOR]: '{0}'".format(category_dic['m_name']))
    slist.append("[COLOR violet]m_year[/COLOR]: '{0}'".format(category_dic['m_year']))
    slist.append("[COLOR violet]m_genre[/COLOR]: '{0}'".format(category_dic['m_genre']))
    slist.append("[COLOR violet]m_developer[/COLOR]: '{0}'".format(category_dic['m_developer']))
    slist.append("[COLOR violet]m_rating[/COLOR]: '{0}'".format(category_dic['m_rating']))
    slist.append("[COLOR violet]m_plot[/COLOR]: '{0}'".format(category_dic['m_plot']))
    slist.append("[COLOR skyblue]finished[/COLOR]: {0}".format(category_dic['finished']))
    slist.append("[COLOR violet]default_icon[/COLOR]: '{0}'".format(category_dic['default_icon']))
    slist.append("[COLOR violet]default_fanart[/COLOR]: '{0}'".format(category_dic['default_fanart']))
    slist.append("[COLOR violet]default_banner[/COLOR]: '{0}'".format(category_dic['default_banner']))
    slist.append("[COLOR violet]default_poster[/COLOR]: '{0}'".format(category_dic['default_poster']))
    slist.append("[COLOR violet]default_clearlogo[/COLOR]: '{0}'".format(category_dic['default_clearlogo']))
    slist.append("[COLOR violet]Asset_Prefix[/COLOR]: '{0}'".format(category_dic['Asset_Prefix']))
    slist.append("[COLOR violet]s_icon[/COLOR]: '{0}'".format(category_dic['s_icon']))
    slist.append("[COLOR violet]s_fanart[/COLOR]: '{0}'".format(category_dic['s_fanart']))
    slist.append("[COLOR violet]s_banner[/COLOR]: '{0}'".format(category_dic['s_banner']))
    slist.append("[COLOR violet]s_poster[/COLOR]: '{0}'".format(category_dic['s_poster']))
    slist.append("[COLOR violet]s_clearlogo[/COLOR]: '{0}'".format(category_dic['s_clearlogo']))
    slist.append("[COLOR violet]s_trailer[/COLOR]: '{0}'".format(category_dic['s_trailer']))

def report_print_Collection(slist, collection):
    slist.append('')
    slist.append("[COLOR violet]id[/COLOR]: '{0}'".format(collection['id']))
    slist.append("[COLOR violet]m_name[/COLOR]: '{0}'".format(collection['m_name']))
    slist.append("[COLOR violet]m_genre[/COLOR]: '{0}'".format(collection['m_genre']))
    slist.append("[COLOR violet]m_rating[/COLOR]: '{0}'".format(collection['m_rating']))
    slist.append("[COLOR violet]m_plot[/COLOR]: '{0}'".format(collection['m_plot']))
    slist.append("[COLOR violet]roms_base_noext[/COLOR]: {0}".format(collection['roms_base_noext']))
    slist.append("[COLOR violet]default_icon[/COLOR]: '{0}'".format(collection['default_icon']))
    slist.append("[COLOR violet]default_fanart[/COLOR]: '{0}'".format(collection['default_fanart']))
    slist.append("[COLOR violet]default_banner[/COLOR]: '{0}'".format(collection['default_banner']))
    slist.append("[COLOR violet]default_poster[/COLOR]: '{0}'".format(collection['default_poster']))
    slist.append("[COLOR violet]default_clearlogo[/COLOR]: '{0}'".format(collection['default_clearlogo']))
    slist.append("[COLOR violet]s_icon[/COLOR]: '{0}'".format(collection['s_icon']))
    slist.append("[COLOR violet]s_fanart[/COLOR]: '{0}'".format(collection['s_fanart']))
    slist.append("[COLOR violet]s_banner[/COLOR]: '{0}'".format(collection['s_banner']))
    slist.append("[COLOR violet]s_poster[/COLOR]: '{0}'".format(collection['s_poster']))
    slist.append("[COLOR violet]s_clearlogo[/COLOR]: '{0}'".format(collection['s_clearlogo']))
    slist.append("[COLOR violet]s_trailer[/COLOR]: '{0}'".format(collection['s_trailer']))
