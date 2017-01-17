# TODO #

 * Add a search engine for the scrapers based on the Levenshtein Distance. There is a Python
   implementation here,
 
   https://github.com/seatgeek/fuzzywuzzy

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
 
 * GameFAQs: detect when web server is blocked.
 
   Blocked IP Address
   Your IP address has been temporarily blocked due to a large number of HTTP requests. The most 
   common causes of this issue are:
 
   http://forum.kodi.tv/showthread.php?tid=287826&pid=2403674#pid2403674

 * Current patched subprocess_hack module is from Python 2.4. Current Python in Kodi is 2.7. Should
   be upgraded soon...

 * os.system(), os.open(), etc. are deprecated, and the subprocess module should be used instead
   for all platforms. (ONLY IMPLEMENTED IN UNIX). A parser of arguments must be coded in order to
   use the subprocess module.


# Implementation of multidisc support #

To be decided yet...

## Naming conventions ##

[TOSEC Naming Convention]

[TOSEC Naming Convention]: http://www.tosecdev.org/tosec-naming-convention

 Organisation | Name example                                                |
--------------|-------------------------------------------------------------|
 TOSEC        | Final Fantasy VII (1999)(Square)(NTSC)(US)(Disc 1 of 2).cue |
              | Final Fantasy VII (1999)(Square)(NTSC)(US)(Disc 2 of 2).cue |
 Trurip       | Final Fantasy VII (EU) - (Disc 1 of 3).cue                  |
              | Final Fantasy VII (EU) - (Disc 2 of 3).cue                  |
              | Final Fantasy VII (EU) - (Disc 3 of 3).cue                  |
 Redump       | Final Fantasy VII (USA) (Disc 1).cue                        |
              | Final Fantasy VII (USA) (Disc 2).cue                        |
              | Final Fantasy VII (USA) (Disc 3).cue                        |


# TOSEC/Trurip/Redump image formats #

 TOSEC       | Redump  | Trurip          |
-------------|---------|-----------------|
 cue,iso,wav | cue,bin | cue,img,ccd,sub |


# AL subprocess module hack #


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
