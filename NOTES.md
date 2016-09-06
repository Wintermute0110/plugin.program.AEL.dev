# TODO #

 * Add nplayers metadata field?
 
   Will have a look next week in detail. Billyc999 database has nplayers NFO. Will check RetroarchDB 
   and if that also has nplayers will add a nplayers metadata field. 
   
   http://forum.kodi.tv/showthread.php?tid=287826&pid=2407055#pid2407055

 * Do you have any plans to add multi-disk support in? I have my roms set up for Advanced Launcher, 
   which only scanned the first disk in a set and popped up a submenu to select the other disks. It 
   did this by looking for a "-cdXX" appended to the file name to determine the CD number, and 
   allowed you to specify what names were shown in the interface with curly brackets (for example 
   "Chrono Cross {English Disk 2}-cd2.cue" would show up as entry 2 in the submenu as "English Disk 2."). 
   It was super handy for multi-disk games and hiding mods behind a sub-category.

   http://forum.kodi.tv/showthread.php?tid=287826&pid=2406770#pid2406770
 
   I use playlists for emulators that support them, but a lot of emulators (and PC games) don't 
   support them and the one's that do have pretty minimal interfaces to use playlists, so it's better 
   from a GUI perspective to be able to handle it on the Kodi side. 
 
   http://forum.kodi.tv/showthread.php?tid=287826&pid=2407122#pid2407122
 
 * It seems AEL can't work with .lnk file shortcuts. Do you plan on working that in or should I 
   start changing all the paths to my applications/games? 
 
   http://forum.kodi.tv/showthread.php?tid=287826&pid=2405485#pid2405485

   In addition to some launching some roms, I use the old Advanced Launcher to open a bunch of 
   couch/controller-friendly Steam games that are all .lnk shortcuts placed in a folder with 
   their corresponding box and fanart. It has been easy to drop a .lnk shortcut and some art in the 
   folder and then scan for new additions with Advanced Launcher as I add games (damn Steam sales 
   making me buy more games).
   
   http://forum.kodi.tv/showthread.php?tid=287826&pid=2405624#pid2405624

 * Add Libretro artwork scraper.
 
   GitHub may be a place you can consider as a source. The libretro-thumbnails database 
   is getting respectable 

   http://forum.kodi.tv/showthread.php?tid=287826&pid=2404280#pid2404280

 * GameFAQs: detect when web server if blocked.
 
   Blocked IP Address
   Your IP address has been temporarily blocked due to a large number of HTTP requests. The most 
   common causes of this issue are:
 
   http://forum.kodi.tv/showthread.php?tid=287826&pid=2403674#pid2403674

 * Issue 14: [Feature request] Add the platforn in the gamedb url query.

 * Scraper should report wheter it supports and asset or not.
 
 * Scraper should download the correct asset or nothing at all if it does not support and specific
   asset.
 
 * Scraper should cache web pages between searches to reduce bandwidth usage and increase speed.

 * Edition of ROMs in Collections is not working at the moment.
 
 * Not all fields of ROMs in Favourites can be edited.

 * Current patched subprocess_hack module is from Python 2.4. Current Python in Kodi is 2.7. Should
   be upgraded soon...

 * os.system(), os.open(), etc. are deprecated, and the subprocess module should be used instead
   for all platforms. (ONLY IMPLEMENTED IN UNIX). A parser of arguments must be coded in order to
   use the subprocess module.


# DONE #

 * Integrate AL launchers.xml sanitizer in AEL plugin.

 * Ensure all artwork directories are different! If assets have same directory then artwork image 
   files will be overwritten!

 * I can't see trailers in the file browser when manually adding them.
 
   When scraping trailers are given the jpg filetype. I have videos stored locaaly and havr been 
   able to viee them by editing the extension in the json but this takes too long.
 
   http://forum.kodi.tv/showthread.php?tid=287826&pid=2402647#pid2402647

 * Issue 21: cannot add roms (release verison 0.9.0)

 * I can't set the directories for the artwork for my roms. If I go to: C (context menu) - Edit Launcher 
   - Manage Rom Asset Directories ... and then for example "Change Fanarts Path" (which is empty right 
   now) the context menu is disappearing and I'm back at my collection without a chance to change/add 
   the directory.
 
   http://forum.kodi.tv/showthread.php?tid=287826&pid=2400253#pid2400253

 * Favourite ROMs should be able to configure default thumb/fanart/poster/banner/clearlogo on a 
   ROM-per-ROM basis. Create a menu entry in the "Edit ROM from Favourites" for this.

 * Collections should have thumb/fanart/banner/flyer artwork. User should be able to choose default
   thumb/fanart/banner/poster/clearlogo.

 * Add a new menu entry in "Edit Category/Launcher" to choose default artwork.

 * Add a new menu entry in "Edit Launcher" to choose default artwork for ROMs.

 * Be able to choose thumb/fanart/banner/poster/clearlogo, not only just thumb/fanart. 
   Reason is that Confluence uses banner instead of thumb if present and other skins
   may have similar behaviour. In this way, user can choose which artwork to use.
   Create new fields default_banner/default_poster/default_clearlogo.

 * Favourite ROMs should inherit default thumb/fanart/poster/banner/clearlogo from launcher.

 * AEL may record the stdout of the launching program. This could be very useful to solve problems
   with the emulators. (ONLY IMPLEMENTED IN UNIX).

 * Record launching process stdout/stderr to file (UNIX only).

 * Make sure Launching from Favourites/Collections/Virtual Launchers works OK.

 * Command to delete Collections.

 * Fix scraper in `Edit ROM/Launcher` menus.

 * Make sure ROM scanner does not search/scrape assets whose directory is not configured.

 * Make sure scraper does not scrape assets with unconfigured directories when editing 
   Categories/Launchers/ROMs.


# listitem.setInfo() overlay values and effects #

`listitem.setInfo('video', {'overlay'  : 4})`

Kodi Krypton Estuary displays a small icon to the left of the listitem title that can be changed
with the overlay property value. Overlay values are defined in [GUIListItem],

```
enum GUIIconOverlay { ICON_OVERLAY_NONE = 0,
                      ICON_OVERLAY_RAR,
                      ICON_OVERLAY_ZIP,
                      ICON_OVERLAY_LOCKED,
                      ICON_OVERLAY_UNWATCHED,
                      ICON_OVERLAY_WATCHED,
                      ICON_OVERLAY_HD};
```

[setInfo]: http://mirrors.xbmc.org/docs/python-docs/16.x-jarvis/xbmcgui.html#ListItem-setInfo
[GUIListItem]: https://github.com/cisco-open-source/kodi/blob/master/xbmc/guilib/GUIListItem.h


# Development environment #

    1. Installed the packages `kodi` and `kodi-visualization-spectrum` in Debian.

    2. Kodi can be run from the command line in windowed mode.

    3. Created a basic package for AEL and install it from zip file.

    4. Once installed, addon code is located in `~/.kodi/addons/plugin.addon.name`

    5. Once installed, addon can be developed in place. A repository can be cloned in
       `~/.kodi/addons/plugin.addon.name`.


# Installing the addon from github #

It is very important that the addon files are inside the correct directory
`~/.kodi/addons/plugin.program.advanced.emulator.launcher`.

To install the plugin from Github, click on `Clone or download` -- `Download ZIP`.
This will download the repository contents to a ZIP file named
`plugin.program.advanced.emulator.launcher-master.zip`. Also, addon is
packed inside directory `plugin.program.advanced.emulator.launcher-master`.

This ZIP file should be decompressed, the directory renamed to
`plugin.program.advanced.emulator.launcher`, and packed into a ZIP file again.
Then, install the ZIP file.
