# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

"""
Module for accessing addon configuration

This module enables access to the static addon config as well as user specific
settings

The module itself keeps the read settings inside a cache, which is then accessed from the addon

Settings listed under Appconfig are defined at compile time and cannot be changed by the user
Settings listed under Userconfig are initially set to a default but can be changed by the user

_PATH is a filename | _DIR is a directory name (with trailing /)
"""

from __future__ import unicode_literals
from abc import ABCMeta
import xbmcaddon
from resources.utils import FileName

__addon_obj__ = xbmcaddon.Addon()

BOOL = "bool"
ENUM = "enum"
TEXT = "text"
FOLDER = "folder"
SLIDER = "slider"


class Metadata:
    """
    Contains some metadata regarding the addon itself
    """
    __metaclass__ = ABCMeta

    # -- Addon metadata ---
    addon_id = __addon_obj__.getAddonInfo('id').decode('utf-8')
    addon_name = __addon_obj__.getAddonInfo('name').decode('utf-8')
    addon_version = __addon_obj__.getAddonInfo('version').decode('utf-8')
    addon_author = __addon_obj__.getAddonInfo('author').decode('utf-8')
    addon_profile = __addon_obj__.getAddonInfo('profile').decode('utf-8')
    addon_type = __addon_obj__.getAddonInfo('type').decode('utf-8')


class Appconfig:
    """
    Contains string constants of the app configuration ids to make referencing inside an IDE easier
    """
    __metaclass__ = ABCMeta

    # --- Paths ---
    HOME_DIR = "home_dir"
    PROFILE_DIR = "profile_dir"
    ADDON_DATA_DIR = "addon_data_dir"
    ADDON_CODE_DIR = "addon_code_dir"
    ICON_FILE_PATH = "icon_file_path"
    FANART_FILE_PATH = "fanart_file_path"

    # --- Databases ---
    CATEGORIES_FILE_PATH = "categories_file_path"
    FAV_JSON_FILE_PATH = "fav_json_file_path"
    COLLECTIONS_FILE_PATH = "collections_file_path"
    VCAT_TITLE_FILE_PATH = "vcat_title_file_path"
    VCAT_YEARS_FILE_PATH = "vcat_years_file_path"
    VCAT_GENRE_FILE_PATH = "vcat_genre_file_path"
    VCAT_DEVELOPER_FILE_PATH = "vcat_developer_file_path"
    VCAT_NPLAYERS_FILE_PATH = "vcat_nplayers_file_path"
    VCAT_ESRB_FILE_PATH = "vcat_esrb_file_path"
    VCAT_RATING_FILE_PATH = "vcat_rating_file_path"
    VCAT_CATEGORY_FILE_PATH = "vcat_category_file_path"
    LAUNCH_LOG_FILE_PATH = "launch_log_file_path"
    RECENT_PLAYED_FILE_PATH = "recent_played_file_path"
    MOST_PLAYED_FILE_PATH = "most_played_file_path"

    # --- Report ---
    BIOS_REPORT_FILE_PATH = "bios_report_file_path"
    LAUNCHER_REPORT_FILE_PATH = "launcher_report_file_path"
    ROM_SYNC_REPORT_FILE_PATH = "rom_sync_report_file_path"
    ROM_ART_INTEGRITY_REPORT_FILE_PATH = "rom_art_integrity_report_file_path"

    # --- Offline Scraper ---
    GAMEDB_INFO_DIR = "gamedb_info_dir"
    GAMEDB_JSON_BASE_NOEXT = "gamedb_json_base_noext"
    # LAUNCHBOX_INFO_DIR = "launchbox_info_dir"
    # LAUNCHBOX_JSON_BASE_NOEXT = "launchbox_json_base_noext"

    # --- Online Scraper Cache ---
    SCRAPER_CACHE_DIR = "scraper_cache_dir"

    # --- Categories Launcher Metadata ---
    DEFAULT_CAT_ASSET_DIR = "default_cat_asset_dir"
    DEFAULT_COL_ASSET_DIR = "default_col_asset_dir"
    DEFAULT_LAUN_ASSET_DIR = "default_laun_asset_dir"
    DEFAULT_FAV_ASSET_DIR = "default_fav_asset_dir"
    VIRTUAL_CAT_TITLE_DIR = "virtual_cat_title_dir"
    VIRTUAL_CAT_YEARS_DIR = "virtual_cat_years_dir"
    VIRTUAL_CAT_GENRE_DIR = "virtual_cat_genre_dir"
    VIRTUAL_CAT_DEVELOPER_DIR = "virtual_cat_developer_dir"
    VIRTUAL_CAT_NPLAYERS_DIR = "virtual_cat_nplayers_dir"
    VIRTUAL_CAT_ESRB_DIR = "virtual_cat_esrb_dir"
    VIRTUAL_CAT_RATING_DIR = "virtual_cat_rating_dir"
    VIRTUAL_CAT_CATEGORY_DIR = "virtual_cat_category_dir"
    ROMS_DIR = "roms_dir"
    COLLECTIONS_DIR = "collections_dir"
    REPORTS_DIR = "reports_dir"

    # Settings required by the scrapers (they are not really settings)
    SCRAPER_SCREENSCRAPER_AEL_SOFTNAME = "scraper_screenscraper_AEL_softname"
    SCRAPER_AELOFFLINE_ADDON_CODE_DIR_STR = "scraper_aeloffline_addon_code_dir_str"
    SCRAPER_CACHE_DIR_STR = "scraper_cache_dir_str"


class Userconfig:
    """
    Contains string constants of the user settings ids to make referencing inside an IDE easier
    """
    __metaclass__ = ABCMeta

    # --- ROM Scanner settings ---
    SCAN_RECURSIVE = ("scan_recursive", BOOL)
    SCAN_IGNORE_BIOS = ("scan_ignore_bios", BOOL)
    SCAN_IGNORE_SCRAP_TITLE = ("scan_ignore_scrap_title", BOOL)
    SCAN_IGNORE_SCRAP_TITLE_MAME = ("scan_ignore_scrap_title_MAME", BOOL)
    SCAN_CLEAN_TAGS = ("scan_clean_tags", BOOL)
    SCAN_UPDATE_NFO_FILES = ("scan_update_NFO_files", BOOL)

    # --- ROM scraping ---
    # Scanner settings
    SCAN_METADATA_POLICY = ("scan_metadata_policy", ENUM)
    SCAN_ASSET_POLICY = ("scan_asset_policy", ENUM)
    GAME_SELECTION_MODE = ("game_selection_mode", ENUM)
    ASSET_SELECTION_MODE = ("asset_selection_mode", ENUM)

    # Scanner scrapers
    SCRAPER_METADATA = ("scraper_metadata", ENUM)
    SCRAPER_ASSET = ("scraper_asset", ENUM)
    SCRAPER_METADATA_MAME = ("scraper_metadata_MAME", ENUM)
    SCRAPER_ASSET_MAME = ("scraper_asset_MAME", ENUM)

    # --- Misc settings ---
    SCRAPER_MOBYGAMES_APIKEY = ("scraper_mobygames_apikey", TEXT)
    SCRAPER_SCREENSCRAPER_SSID = ("scraper_screenscraper_ssid", TEXT)
    SCRAPER_SCREENSCRAPER_SSPASS = ("scraper_screenscraper_sspass", TEXT)

    SCRAPER_SCREENSCRAPER_REGION = ("scraper_screenscraper_region", ENUM)
    SCRAPER_SCREENSCRAPER_LANGUAGE = ("scraper_screenscraper_language", ENUM)

    IO_RETROARCH_SYS_DIR = ("io_retroarch_sys_dir", FOLDER)
    IO_RETROARCH_ONLY_MANDATORY = ("io_retroarch_only_mandatory", BOOL)

    # --- ROM audit ---
    AUDIT_UNKNOWN_ROMS = ("audit_unknown_roms", ENUM)
    AUDIT_PCLONE_ASSETS = ("audit_pclone_assets", BOOL)
    AUDIT_NOINTRO_DIR = ("audit_nointro_dir", FOLDER)
    AUDIT_REDUMP_DIR = ("audit_redump_dir", FOLDER)

    # AUDIT_1G1R_FIRST_REGION = ("audit_1G1R_first_region", ENUM)
    # AUDIT_1G1R_SECOND_REGION = ("audit_1G1R_second_region", ENUM)
    # AUDIT_1G1R_THIRD_REGION = ("audit_1G1R_third_region", ENUM)

    # --- Display ---
    DISPLAY_CATEGORY_MODE = ("display_category_mode", ENUM)
    DISPLAY_LAUNCHER_NOTIFY = ("display_launcher_notify", BOOL)
    DISPLAY_HIDE_FINISHED = ("display_hide_finished", BOOL)
    DISPLAY_LAUNCHER_ROMS = ("display_launcher_roms", BOOL)

    DISPLAY_ROM_IN_FAV = ("display_rom_in_fav", BOOL)
    DISPLAY_NOINTRO_STAT = ("display_nointro_stat", BOOL)
    DISPLAY_FAV_STATUS = ("display_fav_status", BOOL)

    DISPLAY_HIDE_FAVS = ("display_hide_favs", BOOL)
    DISPLAY_HIDE_COLLECTIONS = ("display_hide_collections", BOOL)
    DISPLAY_HIDE_VLAUNCHERS = ("display_hide_vlaunchers", BOOL)
    DISPLAY_HIDE_AEL_SCRAPER = ("display_hide_AEL_scraper", BOOL)
    DISPLAY_HIDE_RECENT = ("display_hide_recent", BOOL)
    DISPLAY_HIDE_MOSTPLAYED = ("display_hide_mostplayed", BOOL)
    DISPLAY_HIDE_UTILITIES = ("display_hide_utilities", BOOL)
    DISPLAY_HIDE_G_REPORTS = ("display_hide_g_reports", BOOL)

    CATEGORIES_ASSET_DIR = ("categories_asset_dir", FOLDER)
    LAUNCHERS_ASSET_DIR = ("launchers_asset_dir", FOLDER)
    FAVOURITES_ASSET_DIR = ("favourites_asset_dir", FOLDER)
    COLLECTIONS_ASSET_DIR = ("collections_asset_dir", FOLDER)

    MEDIA_STATE_ACTION = ("media_state_action", ENUM)
    DELAY_TEMPO = ("delay_tempo", SLIDER)
    SUSPEND_AUDIO_ENGINE = ("suspend_audio_engine", BOOL)
    SUSPEND_SCREENSAVER = ("suspend_screensaver", BOOL)
    # SUSPEND_JOYSTICK_ENGINE = ("suspend_joystick_engine", BOOL)
    ESCAPE_ROMFILE = ("escape_romfile", BOOL)
    LIRC_STATE = ("lirc_state", BOOL)
    SHOW_BATCH_WINDOW = ("show_batch_window", BOOL)
    WINDOWS_CLOSE_FDS = ("windows_close_fds", BOOL)
    WINDOWS_CD_APPPATH = ("windows_cd_apppath", BOOL)
    LOG_LEVEL = ("log_level", ENUM)


class Config:
    """
    Static class for accessing the settings cache

    Also contains functions for initialisation
    """
    __metaclass__ = ABCMeta

    __app_settings = {}

    @staticmethod
    def load_app_settings():
        """
        Loads the static application configuration cache

        Also creates the necessary directories, if they do not exist yet
        """

        def in_addon_data_dir(filename):
            return Config.get(Appconfig.ADDON_DATA_DIR).pjoin(filename)

        def __create_dir_if_not_exists(path):
            if not path.exists():
                path.makedirs()

        Config.__app_settings.update({
            Appconfig.HOME_DIR: FileName("special://home"),
            Appconfig.PROFILE_DIR: FileName("special://profile"),
            Appconfig.ADDON_DATA_DIR: FileName("special://profile/addon_data").pjoin(Metadata.addon_id)
        })

        Config.__app_settings.update({
            Appconfig.ADDON_CODE_DIR: Config.get(Appconfig.HOME_DIR).pjoin("addons").pjoin(Metadata.addon_id)
        })

        Config.__app_settings.update({
            Appconfig.ICON_FILE_PATH: Config.get(Appconfig.ADDON_CODE_DIR).pjoin("media/icon.png"),
            Appconfig.FANART_FILE_PATH: Config.get(Appconfig.ADDON_CODE_DIR).pjoin("media/fanart.jpg"),

            Appconfig.CATEGORIES_FILE_PATH: in_addon_data_dir("categories.xml"),
            Appconfig.FAV_JSON_FILE_PATH: in_addon_data_dir("favourites.json"),
            Appconfig.COLLECTIONS_FILE_PATH: in_addon_data_dir("collections.xml"),
            Appconfig.VCAT_TITLE_FILE_PATH: in_addon_data_dir("vcat_title.xml"),
            Appconfig.VCAT_YEARS_FILE_PATH: in_addon_data_dir("vcat_years.xml"),
            Appconfig.VCAT_GENRE_FILE_PATH: in_addon_data_dir("vcat_genre.xml"),
            Appconfig.VCAT_DEVELOPER_FILE_PATH: in_addon_data_dir("vcat_developers.xml"),
            Appconfig.VCAT_NPLAYERS_FILE_PATH: in_addon_data_dir("vcat_nplayers.xml"),
            Appconfig.VCAT_ESRB_FILE_PATH: in_addon_data_dir("vcat_esrb.xml"),
            Appconfig.VCAT_RATING_FILE_PATH: in_addon_data_dir("vcat_rating.xml"),
            Appconfig.VCAT_CATEGORY_FILE_PATH: in_addon_data_dir("vcat_category.xml"),
            Appconfig.LAUNCH_LOG_FILE_PATH: in_addon_data_dir("launcher.log"),
            Appconfig.RECENT_PLAYED_FILE_PATH: in_addon_data_dir("history.json"),
            Appconfig.MOST_PLAYED_FILE_PATH: in_addon_data_dir("most_played.json"),

            Appconfig.BIOS_REPORT_FILE_PATH: in_addon_data_dir("report_BIOS.txt"),
            Appconfig.LAUNCHER_REPORT_FILE_PATH: in_addon_data_dir("report_Launchers.txt"),
            Appconfig.ROM_SYNC_REPORT_FILE_PATH: in_addon_data_dir("report_ROM_sync_status.txt"),
            Appconfig.ROM_ART_INTEGRITY_REPORT_FILE_PATH: in_addon_data_dir("report_ROM_artwork_integrity.txt"),

            Appconfig.GAMEDB_INFO_DIR: Config.get(Appconfig.ADDON_CODE_DIR).pjoin("data-AOS"),
            Appconfig.GAMEDB_JSON_BASE_NOEXT: "AOS_GameDB_info",
            # Appconfig.LAUNCHBOX_INFO_DIR: Config.get(Appconfig.ADDON_CODE_DIR).pjoin("LaunchBox"),
            # Appconfig.LAUNCHBOX_JSON_BASE_NOEXT: "LaunchBox_info",

            Appconfig.SCRAPER_CACHE_DIR: in_addon_data_dir("ScraperCache"),

            Appconfig.DEFAULT_CAT_ASSET_DIR: in_addon_data_dir("asset-categories"),
            Appconfig.DEFAULT_COL_ASSET_DIR: in_addon_data_dir("asset-collections"),
            Appconfig.DEFAULT_LAUN_ASSET_DIR: in_addon_data_dir("asset-launchers"),
            Appconfig.DEFAULT_FAV_ASSET_DIR: in_addon_data_dir("asset-favourites"),
            Appconfig.VIRTUAL_CAT_TITLE_DIR: in_addon_data_dir("db_title"),
            Appconfig.VIRTUAL_CAT_YEARS_DIR: in_addon_data_dir("db_year"),
            Appconfig.VIRTUAL_CAT_GENRE_DIR: in_addon_data_dir("db_genre"),
            Appconfig.VIRTUAL_CAT_DEVELOPER_DIR: in_addon_data_dir("db_developer"),
            Appconfig.VIRTUAL_CAT_NPLAYERS_DIR: in_addon_data_dir("db_nplayer"),
            Appconfig.VIRTUAL_CAT_ESRB_DIR: in_addon_data_dir("db_esrb"),
            Appconfig.VIRTUAL_CAT_RATING_DIR: in_addon_data_dir("db_rating"),
            Appconfig.VIRTUAL_CAT_CATEGORY_DIR: in_addon_data_dir("db_category"),
            Appconfig.ROMS_DIR: in_addon_data_dir("db_ROMs"),
            Appconfig.COLLECTIONS_DIR: in_addon_data_dir("db_Collections"),
            Appconfig.REPORTS_DIR: in_addon_data_dir("reports"),

            Appconfig.SCRAPER_SCREENSCRAPER_AEL_SOFTNAME: "AEL_{}".format(Metadata.addon_version),
            Appconfig.SCRAPER_AELOFFLINE_ADDON_CODE_DIR_STR: Config.get(Appconfig.ADDON_CODE_DIR).getPath()
        })

        Config.__app_settings.update({
            Appconfig.SCRAPER_CACHE_DIR_STR: Config.get(Appconfig.SCRAPER_CACHE_DIR).getPath()
        })

        __create_dir_if_not_exists(Config.get(Appconfig.ADDON_DATA_DIR))
        __create_dir_if_not_exists(Config.get(Appconfig.SCRAPER_CACHE_DIR))
        __create_dir_if_not_exists(Config.get(Appconfig.DEFAULT_CAT_ASSET_DIR))
        __create_dir_if_not_exists(Config.get(Appconfig.DEFAULT_COL_ASSET_DIR))
        __create_dir_if_not_exists(Config.get(Appconfig.DEFAULT_LAUN_ASSET_DIR))
        __create_dir_if_not_exists(Config.get(Appconfig.DEFAULT_FAV_ASSET_DIR))
        __create_dir_if_not_exists(Config.get(Appconfig.VIRTUAL_CAT_TITLE_DIR))
        __create_dir_if_not_exists(Config.get(Appconfig.VIRTUAL_CAT_YEARS_DIR))
        __create_dir_if_not_exists(Config.get(Appconfig.VIRTUAL_CAT_GENRE_DIR))
        __create_dir_if_not_exists(Config.get(Appconfig.VIRTUAL_CAT_DEVELOPER_DIR))
        __create_dir_if_not_exists(Config.get(Appconfig.VIRTUAL_CAT_NPLAYERS_DIR))
        __create_dir_if_not_exists(Config.get(Appconfig.VIRTUAL_CAT_ESRB_DIR))
        __create_dir_if_not_exists(Config.get(Appconfig.VIRTUAL_CAT_RATING_DIR))
        __create_dir_if_not_exists(Config.get(Appconfig.VIRTUAL_CAT_CATEGORY_DIR))
        __create_dir_if_not_exists(Config.get(Appconfig.ROMS_DIR))
        __create_dir_if_not_exists(Config.get(Appconfig.COLLECTIONS_DIR))
        __create_dir_if_not_exists(Config.get(Appconfig.REPORTS_DIR))

    __user_settings = {}

    @staticmethod
    def load_user_settings():
        """
        Loads the user settings cache

        This function should also be used, to refresh the cache
        """

        def __get_setting(name, setting_type):
            if setting_type == BOOL:
                return __addon_obj__.getSettingBool(name)
            if setting_type == ENUM:
                return __addon_obj__.getSettingInt(name)
            if setting_type == TEXT or setting_type == FOLDER:
                return __addon_obj__.getSetting(name).decode("utf-8")
            if setting_type == SLIDER:
                return __addon_obj__.getSettingInt(name)

        for setting, setting_id in vars(Userconfig).items():
            if not setting.startswith("_"):
                Config.__user_settings[setting_id[0]] = __get_setting(setting_id[0], setting_id[1])

        # Check if user changed default artwork paths for categories/launchers. If not, set defaults.
        if Config.get(Userconfig.CATEGORIES_ASSET_DIR) == "":
            Config.__user_settings[
                "categories_asset_dir"] = Config.get(Appconfig.DEFAULT_CAT_ASSET_DIR).getOriginalPath()
        if Config.get(Userconfig.LAUNCHERS_ASSET_DIR) == "":
            Config.__user_settings[
                "launchers_asset_dir"] = Config.get(Appconfig.DEFAULT_LAUN_ASSET_DIR).getOriginalPath()
        if Config.get(Userconfig.FAVOURITES_ASSET_DIR) == "":
            Config.__user_settings[
                "favourites_asset_dir"] = Config.get(Appconfig.DEFAULT_FAV_ASSET_DIR).getOriginalPath()
        if Config.get(Userconfig.COLLECTIONS_ASSET_DIR) == "":
            Config.__user_settings[
                "collections_asset_dir"] = Config.get(Appconfig.DEFAULT_COL_ASSET_DIR).getOriginalPath()

    @staticmethod
    def get(name):
        """
        Reads a setting from the cache

        The available settings can be identified via the Appconfig and Userconfig classes in this module
        """
        if name in Config.__app_settings:
            return Config.__app_settings.get(name)
        if name[0] in Config.__user_settings:
            return Config.__user_settings.get(name[0])
        raise KeyError("requested configuration could not be found")

    @staticmethod
    def dump_user_settings():
        """
        Retrieves a formatted output of the current user settings cache

        Useful for debugging purposes
        """
        return "\n".join(["{id} --> {value:10s} {type}".format(id=key.rjust(21), value=Config.__user_settings[key],
                                                               type=type(Config.__user_settings[key])) for key in
                          sorted(Config.__user_settings)])
