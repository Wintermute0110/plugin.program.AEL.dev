# -*- coding: utf-8 -*-

# Copyright (c) 2016-2022 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# Advanced Emulator Launcher exclusive miscellaneous functions.
#
# Functions in this module only depend on the Python standard library.
# This module can be loaded anywhere without creating circular dependencies.
# Optionally this module can include module const and log.

# --- Addon modules ---
import resources.log as log

# --- Python standard library ---

# ------------------------------------------------------------------------------------------------
# Database visualization functions.
# ------------------------------------------------------------------------------------------------
def print_ROM_slist(rom, sl):
    sl.append("[COLOR violet]id[/COLOR]: '{}'".format(rom['id']))
    # Metadata
    sl.append("[COLOR violet]m_name[/COLOR]: '{}'".format(rom['m_name']))
    sl.append("[COLOR violet]m_year[/COLOR]: '{}'".format(rom['m_year']))
    sl.append("[COLOR violet]m_genre[/COLOR]: '{}'".format(rom['m_genre']))
    sl.append("[COLOR violet]m_developer[/COLOR]: '{}'".format(rom['m_developer']))
    sl.append("[COLOR violet]m_nplayers[/COLOR]: '{}'".format(rom['m_nplayers']))
    sl.append("[COLOR violet]m_esrb[/COLOR]: '{}'".format(rom['m_esrb']))
    sl.append("[COLOR violet]m_rating[/COLOR]: '{}'".format(rom['m_rating']))
    sl.append("[COLOR violet]m_plot[/COLOR]: '{}'".format(rom['m_plot']))
    # Info
    sl.append("[COLOR violet]filename[/COLOR]: '{}'".format(rom['filename']))
    sl.append("[COLOR skyblue]disks[/COLOR]: {}".format(rom['disks']))
    sl.append("[COLOR violet]altapp[/COLOR]: '{}'".format(rom['altapp']))
    sl.append("[COLOR violet]altarg[/COLOR]: '{}'".format(rom['altarg']))
    sl.append("[COLOR skyblue]finished[/COLOR]: {}".format(rom['finished']))
    sl.append("[COLOR violet]nointro_status[/COLOR]: '{}'".format(rom['nointro_status']))
    sl.append("[COLOR violet]pclone_status[/COLOR]: '{}'".format(rom['pclone_status']))
    sl.append("[COLOR violet]cloneof[/COLOR]: '{}'".format(rom['cloneof']))
    sl.append("[COLOR skyblue]i_extra_ROM[/COLOR]: {}".format(rom['i_extra_ROM']))
    # Assets/artwork
    sl.append("[COLOR violet]s_3dbox[/COLOR]: '{}'".format(rom['s_3dbox']))
    sl.append("[COLOR violet]s_title[/COLOR]: '{}'".format(rom['s_title']))
    sl.append("[COLOR violet]s_snap[/COLOR]: '{}'".format(rom['s_snap']))
    sl.append("[COLOR violet]s_boxfront[/COLOR]: '{}'".format(rom['s_boxfront']))
    sl.append("[COLOR violet]s_boxback[/COLOR]: '{}'".format(rom['s_boxback']))
    sl.append("[COLOR violet]s_cartridge[/COLOR]: '{}'".format(rom['s_cartridge']))
    sl.append("[COLOR violet]s_fanart[/COLOR]: '{}'".format(rom['s_fanart']))
    sl.append("[COLOR violet]s_banner[/COLOR]: '{}'".format(rom['s_banner']))
    sl.append("[COLOR violet]s_clearlogo[/COLOR]: '{}'".format(rom['s_clearlogo']))
    sl.append("[COLOR violet]s_flyer[/COLOR]: '{}'".format(rom['s_flyer']))
    sl.append("[COLOR violet]s_map[/COLOR]: '{}'".format(rom['s_map']))
    sl.append("[COLOR violet]s_manual[/COLOR]: '{}'".format(rom['s_manual']))
    sl.append("[COLOR violet]s_trailer[/COLOR]: '{}'".format(rom['s_trailer']))

def print_ROM_additional_slist(rom, sl):
    sl.append("[COLOR violet]launcherID[/COLOR]: '{}'".format(rom['launcherID']))
    sl.append("[COLOR violet]platform[/COLOR]: '{}'".format(rom['platform']))
    sl.append("[COLOR violet]application[/COLOR]: '{}'".format(rom['application']))
    sl.append("[COLOR violet]args[/COLOR]: '{}'".format(rom['args']))
    sl.append("[COLOR skyblue]args_extra[/COLOR]: {}".format(rom['args_extra']))
    sl.append("[COLOR violet]rompath[/COLOR]: '{}'".format(rom['rompath']))
    sl.append("[COLOR violet]romext[/COLOR]: '{}'".format(rom['romext']))
    sl.append("[COLOR skyblue]toggle_window[/COLOR]: {}".format(rom['toggle_window']))
    sl.append("[COLOR skyblue]non_blocking[/COLOR]: {}".format(rom['non_blocking']))
    sl.append("[COLOR violet]roms_default_icon[/COLOR]: '{}'".format(rom['roms_default_icon']))
    sl.append("[COLOR violet]roms_default_fanart[/COLOR]: '{}'".format(rom['roms_default_fanart']))
    sl.append("[COLOR violet]roms_default_banner[/COLOR]: '{}'".format(rom['roms_default_banner']))
    sl.append("[COLOR violet]roms_default_poster[/COLOR]: '{}'".format(rom['roms_default_poster']))
    sl.append("[COLOR violet]roms_default_clearlogo[/COLOR]: '{}'".format(rom['roms_default_clearlogo']))

    # Favourite ROMs unique fields.
    sl.append("[COLOR violet]fav_status[/COLOR]: '{}'".format(rom['fav_status']))
    # 'launch_count' only in Favourite ROMs in "Most played ROMs"
    if 'launch_count' in rom:
        sl.append("[COLOR skyblue]launch_count[/COLOR]: {}".format(rom['launch_count']))

def print_Launcher_slist(launcher, sl):
    sl.append("[COLOR violet]id[/COLOR]: '{}'".format(launcher['id']))
    sl.append("[COLOR violet]m_name[/COLOR]: '{}'".format(launcher['m_name']))
    sl.append("[COLOR violet]m_year[/COLOR]: '{}'".format(launcher['m_year']))
    sl.append("[COLOR violet]m_genre[/COLOR]: '{}'".format(launcher['m_genre']))
    sl.append("[COLOR violet]m_developer[/COLOR]: '{}'".format(launcher['m_developer']))
    sl.append("[COLOR violet]m_rating[/COLOR]: '{}'".format(launcher['m_rating']))
    sl.append("[COLOR violet]m_plot[/COLOR]: '{}'".format(launcher['m_plot']))

    sl.append("[COLOR violet]platform[/COLOR]: '{}'".format(launcher['platform']))
    sl.append("[COLOR violet]categoryID[/COLOR]: '{}'".format(launcher['categoryID']))
    sl.append("[COLOR violet]application[/COLOR]: '{}'".format(launcher['application']))
    sl.append("[COLOR violet]args[/COLOR]: '{}'".format(launcher['args']))
    sl.append("[COLOR skyblue]args_extra[/COLOR]: {}".format(launcher['args_extra']))
    sl.append("[COLOR violet]rompath[/COLOR]: '{}'".format(launcher['rompath']))
    sl.append("[COLOR violet]romextrapath[/COLOR]: '{}'".format(launcher['romextrapath']))
    sl.append("[COLOR violet]romext[/COLOR]: '{}'".format(launcher['romext']))
    # Bool settings
    sl.append("[COLOR skyblue]finished[/COLOR]: {}".format(launcher['finished']))
    sl.append("[COLOR skyblue]toggle_window[/COLOR]: {}".format(launcher['toggle_window']))
    sl.append("[COLOR skyblue]non_blocking[/COLOR]: {}".format(launcher['non_blocking']))
    sl.append("[COLOR skyblue]multidisc[/COLOR]: {}".format(launcher['multidisc']))
    # Strings
    sl.append("[COLOR violet]roms_base_noext[/COLOR]: '{}'".format(launcher['roms_base_noext']))
    sl.append("[COLOR violet]audit_state[/COLOR]: '{}'".format(launcher['audit_state']))
    sl.append("[COLOR violet]audit_auto_dat_file[/COLOR]: '{}'".format(launcher['audit_auto_dat_file']))
    sl.append("[COLOR violet]audit_custom_dat_file[/COLOR]: '{}'".format(launcher['audit_custom_dat_file']))
    sl.append("[COLOR violet]audit_display_mode[/COLOR]: '{}'".format(launcher['audit_display_mode']))
    sl.append("[COLOR violet]launcher_display_mode[/COLOR]: '{}'".format(launcher['launcher_display_mode']))
    # Integers/Floats
    sl.append("[COLOR skyblue]num_roms[/COLOR]: {}".format(launcher['num_roms']))
    sl.append("[COLOR skyblue]num_parents[/COLOR]: {}".format(launcher['num_parents']))
    sl.append("[COLOR skyblue]num_clones[/COLOR]: {}".format(launcher['num_clones']))
    sl.append("[COLOR skyblue]num_have[/COLOR]: {}".format(launcher['num_have']))
    sl.append("[COLOR skyblue]num_miss[/COLOR]: {}".format(launcher['num_miss']))
    sl.append("[COLOR skyblue]num_unknown[/COLOR]: {}".format(launcher['num_unknown']))
    sl.append("[COLOR skyblue]num_extra[/COLOR]: {}".format(launcher['num_extra']))
    sl.append("[COLOR skyblue]timestamp_launcher[/COLOR]: {}".format(launcher['timestamp_launcher']))
    sl.append("[COLOR skyblue]timestamp_report[/COLOR]: {}".format(launcher['timestamp_report']))

    sl.append("[COLOR violet]default_icon[/COLOR]: '{}'".format(launcher['default_icon']))
    sl.append("[COLOR violet]default_fanart[/COLOR]: '{}'".format(launcher['default_fanart']))
    sl.append("[COLOR violet]default_banner[/COLOR]: '{}'".format(launcher['default_banner']))
    sl.append("[COLOR violet]default_poster[/COLOR]: '{}'".format(launcher['default_poster']))
    sl.append("[COLOR violet]default_clearlogo[/COLOR]: '{}'".format(launcher['default_clearlogo']))
    sl.append("[COLOR violet]default_controller[/COLOR]: '{}'".format(launcher['default_controller']))
    sl.append("[COLOR violet]Asset_Prefix[/COLOR]: '{}'".format(launcher['Asset_Prefix']))
    sl.append("[COLOR violet]s_icon[/COLOR]: '{}'".format(launcher['s_icon']))
    sl.append("[COLOR violet]s_fanart[/COLOR]: '{}'".format(launcher['s_fanart']))
    sl.append("[COLOR violet]s_banner[/COLOR]: '{}'".format(launcher['s_banner']))
    sl.append("[COLOR violet]s_poster[/COLOR]: '{}'".format(launcher['s_poster']))
    sl.append("[COLOR violet]s_clearlogo[/COLOR]: '{}'".format(launcher['s_clearlogo']))
    sl.append("[COLOR violet]s_controller[/COLOR]: '{}'".format(launcher['s_controller']))
    sl.append("[COLOR violet]s_trailer[/COLOR]: '{}'".format(launcher['s_trailer']))

    sl.append("[COLOR violet]roms_default_icon[/COLOR]: '{}'".format(launcher['roms_default_icon']))
    sl.append("[COLOR violet]roms_default_fanart[/COLOR]: '{}'".format(launcher['roms_default_fanart']))
    sl.append("[COLOR violet]roms_default_banner[/COLOR]: '{}'".format(launcher['roms_default_banner']))
    sl.append("[COLOR violet]roms_default_poster[/COLOR]: '{}'".format(launcher['roms_default_poster']))
    sl.append("[COLOR violet]roms_default_clearlogo[/COLOR]: '{}'".format(launcher['roms_default_clearlogo']))
    sl.append("[COLOR violet]ROM_asset_path[/COLOR]: '{}'".format(launcher['ROM_asset_path']))
    sl.append("[COLOR violet]path_3dbox[/COLOR]: '{}'".format(launcher['path_3dbox']))
    sl.append("[COLOR violet]path_title[/COLOR]: '{}'".format(launcher['path_title']))
    sl.append("[COLOR violet]path_snap[/COLOR]: '{}'".format(launcher['path_snap']))
    sl.append("[COLOR violet]path_boxfront[/COLOR]: '{}'".format(launcher['path_boxfront']))
    sl.append("[COLOR violet]path_boxback[/COLOR]: '{}'".format(launcher['path_boxback']))
    sl.append("[COLOR violet]path_cartridge[/COLOR]: '{}'".format(launcher['path_cartridge']))
    sl.append("[COLOR violet]path_fanart[/COLOR]: '{}'".format(launcher['path_fanart']))
    sl.append("[COLOR violet]path_banner[/COLOR]: '{}'".format(launcher['path_banner']))
    sl.append("[COLOR violet]path_clearlogo[/COLOR]: '{}'".format(launcher['path_clearlogo']))
    sl.append("[COLOR violet]path_flyer[/COLOR]: '{}'".format(launcher['path_flyer']))
    sl.append("[COLOR violet]path_map[/COLOR]: '{}'".format(launcher['path_map']))
    sl.append("[COLOR violet]path_manual[/COLOR]: '{}'".format(launcher['path_manual']))
    sl.append("[COLOR violet]path_trailer[/COLOR]: '{}'".format(launcher['path_trailer']))

def print_Category_slist(category, sl):
    sl.append("[COLOR violet]id[/COLOR]: '{}'".format(category['id']))
    sl.append("[COLOR violet]m_name[/COLOR]: '{}'".format(category['m_name']))
    sl.append("[COLOR violet]m_year[/COLOR]: '{}'".format(category['m_year']))
    sl.append("[COLOR violet]m_genre[/COLOR]: '{}'".format(category['m_genre']))
    sl.append("[COLOR violet]m_developer[/COLOR]: '{}'".format(category['m_developer']))
    sl.append("[COLOR violet]m_rating[/COLOR]: '{}'".format(category['m_rating']))
    sl.append("[COLOR violet]m_plot[/COLOR]: '{}'".format(category['m_plot']))
    sl.append("[COLOR skyblue]finished[/COLOR]: {}".format(category['finished']))
    sl.append("[COLOR violet]default_icon[/COLOR]: '{}'".format(category['default_icon']))
    sl.append("[COLOR violet]default_fanart[/COLOR]: '{}'".format(category['default_fanart']))
    sl.append("[COLOR violet]default_banner[/COLOR]: '{}'".format(category['default_banner']))
    sl.append("[COLOR violet]default_poster[/COLOR]: '{}'".format(category['default_poster']))
    sl.append("[COLOR violet]default_clearlogo[/COLOR]: '{}'".format(category['default_clearlogo']))
    sl.append("[COLOR violet]Asset_Prefix[/COLOR]: '{}'".format(category['Asset_Prefix']))
    sl.append("[COLOR violet]s_icon[/COLOR]: '{}'".format(category['s_icon']))
    sl.append("[COLOR violet]s_fanart[/COLOR]: '{}'".format(category['s_fanart']))
    sl.append("[COLOR violet]s_banner[/COLOR]: '{}'".format(category['s_banner']))
    sl.append("[COLOR violet]s_poster[/COLOR]: '{}'".format(category['s_poster']))
    sl.append("[COLOR violet]s_clearlogo[/COLOR]: '{}'".format(category['s_clearlogo']))
    sl.append("[COLOR violet]s_trailer[/COLOR]: '{}'".format(category['s_trailer']))

def print_Collection_slist(collection, sl):
    sl.append("[COLOR violet]id[/COLOR]: '{}'".format(collection['id']))
    sl.append("[COLOR violet]m_name[/COLOR]: '{}'".format(collection['m_name']))
    sl.append("[COLOR violet]m_genre[/COLOR]: '{}'".format(collection['m_genre']))
    sl.append("[COLOR violet]m_rating[/COLOR]: '{}'".format(collection['m_rating']))
    sl.append("[COLOR violet]m_plot[/COLOR]: '{}'".format(collection['m_plot']))
    sl.append("[COLOR violet]roms_base_noext[/COLOR]: {}".format(collection['roms_base_noext']))
    sl.append("[COLOR violet]default_icon[/COLOR]: '{}'".format(collection['default_icon']))
    sl.append("[COLOR violet]default_fanart[/COLOR]: '{}'".format(collection['default_fanart']))
    sl.append("[COLOR violet]default_banner[/COLOR]: '{}'".format(collection['default_banner']))
    sl.append("[COLOR violet]default_poster[/COLOR]: '{}'".format(collection['default_poster']))
    sl.append("[COLOR violet]default_clearlogo[/COLOR]: '{}'".format(collection['default_clearlogo']))
    sl.append("[COLOR violet]s_icon[/COLOR]: '{}'".format(collection['s_icon']))
    sl.append("[COLOR violet]s_fanart[/COLOR]: '{}'".format(collection['s_fanart']))
    sl.append("[COLOR violet]s_banner[/COLOR]: '{}'".format(collection['s_banner']))
    sl.append("[COLOR violet]s_poster[/COLOR]: '{}'".format(collection['s_poster']))
    sl.append("[COLOR violet]s_clearlogo[/COLOR]: '{}'".format(collection['s_clearlogo']))
    sl.append("[COLOR violet]s_trailer[/COLOR]: '{}'".format(collection['s_trailer']))

# ROM dictionary is edited by Python passing by assigment
def fix_rom_object(rom):
    # log.debug('fix_rom_object() Fixing ROM {}'.format(rom['id']))
    # Add new fields if not present
    if 'm_nplayers'    not in rom: rom['m_nplayers']    = ''
    if 'm_esrb'        not in rom: rom['m_esrb']        = ESRB_PENDING
    if 'disks'         not in rom: rom['disks']         = []
    if 'pclone_status' not in rom: rom['pclone_status'] = PCLONE_STATUS_NONE
    if 'cloneof'       not in rom: rom['cloneof']       = ''
    if 's_3dbox'       not in rom: rom['s_3dbox']       = ''
    if 'i_extra_ROM'   not in rom: rom['i_extra_ROM']   = False
    # Delete unwanted/obsolete stuff
    if 'nointro_isClone' in rom: rom.pop('nointro_isClone')
    # DB field renamings
    if 'm_studio' in rom:
        rom['m_developer'] = rom['m_studio']
        rom.pop('m_studio')

def fix_Favourite_rom_object(rom):
    # Fix standard ROM fields
    fix_rom_object(rom)

    # Favourite ROMs additional stuff
    if 'args_extra' not in rom: rom['args_extra'] = []
    if 'non_blocking' not in rom: rom['non_blocking'] = False
    if 'roms_default_thumb' in rom:
        rom['roms_default_icon'] = rom['roms_default_thumb']
        rom.pop('roms_default_thumb')
    if 'minimize' in rom:
        rom['toggle_window'] = rom['minimize']
        rom.pop('minimize')

def aux_check_for_file(str_list, dic_key_name, launcher):
    path = launcher[dic_key_name]
    path_FN = utils.FileName(path)
    if path and not path_FN.exists():
        problems_found = True
        str_list.append('{} "{}" not found'.format(dic_key_name, path_FN.getPath()))
