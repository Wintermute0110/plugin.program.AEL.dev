# TODO #

 * GameFAQs: detect when web server is blocked.
 
   Blocked IP Address
   Your IP address has been temporarily blocked due to a large number of HTTP requests. The most 
   common causes of this issue are:
 
   http://forum.kodi.tv/showthread.php?tid=287826&pid=2403674#pid2403674


# Multidisc support #

## ROM scanner implementation ##

 1) If the ROM scanner finds a multidisc image belonging to a set, for example
    `Final Fantasy VII (USA) (Disc 3).cue`.
 
    * The filename corresponds to the basename of the set.
 
    * The ROM basename is added to the `disks` list.

    * Asset names will have the basename of the set `Final Fantasy VII (USA)`.

```
    filename = '/home/kodi/ROMs/Final Fantasy VII (USA)'
    disks = ['Final Fantasy VII (USA) (Disc 3).cue']
```

 2) If the ROM scanner finds another image of the set then:
 
    * The basename is added to the `disks` list.
    
    * `disks` list is reordered so ROMs have consecutive order.
    
    * `filename` points to the first image of the set.
    
    * Metadata/Asset scraping is only done for the first ROM of the set.

```
    filename = '/home/kodi/ROMs/Final Fantasy VII (USA)'
    disks = ['Final Fantasy VII (USA) (Disc 1).cue', 'Final Fantasy VII (USA) (Disc 3).cue']
```

 3) ROMs not in a set have an empty `disks` list.

 4) This implementation is safe if there are missing ROMs in the set.
 
 5) Al launching time, users selects from a select dialog of the basenames of the roms of the
    set which one to launch.

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
