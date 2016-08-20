# TODO #

 * Favourite ROMs should be able to configure default thumb/fanart/poster/banner/clearlogo on a 
   ROM-per-ROM basis. Create a menu entry in the "Edit ROM from Favourites" for this.

 * Scraper should report wheter it supports and asset or not.
 
 * Scraper should download the correct asset or nothing at all if it does not support and specific
   asset.
 
 * Scraper should cache web pages between searches to reduce bandwidth usage and increase speed.

 * Current patched subprocess_hack module is from Python 2.4. Current Python in Kodi is 2.7. Should
   be upgraded soon...

 * os.system(), os.open(), etc. are deprecated, and the subprocess module should be used instead
   for all platforms. (ONLY IMPLEMENTED IN UNIX). A parser of arguments must be coded in order to
   use the subprocess module.


# DONE # 

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
