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


# Things to change in Advanced Emulator Launcher (AEL) #

*   AL initial load is very slow. Entering a category or launcher is very slow.
 
    SOLUTION: Use separate XML files for every launcher instead of one big launchers.xml


*   AL translation system is horrible. It is based on numbers!
 
    SOLUTION: Remove all languages and use English. I will think of a better translation
    scheme later.

 
*   There is no favourites in AL launcher. Favourites can only be added to Kodi favourites.
 
    SOLUTION: Create a special AEL favourites category.


*   No Tumb/Fanart when ".." is selected in navigation screen.
 
    SOLUTION: I do not know at the moment...

# Development environment #

    1. Installed the packages `kodi` and `kodi-visualization-spectrum` in Debian.

    2. Kodi can be run from the command line in windowed mode.

    3. Created a basic package for AEL and install it from zip file.

    4. Once installed, addon code is located in `~/.kodi/addons/plugin.addon.name`

# Kodi addon zip files #

The zipfile must have this structure:

~~~
plugin.program.advanced.emulator.launcher/addon.xml
plugin.program.advanced.emulator.launcher/changelog.txt
plugin.program.advanced.emulator.launcher/default.py
plugin.program.advanced.emulator.launcher/fanart.jpg
plugin.program.advanced.emulator.launcher/icon.png
plugin.program.advanced.emulator.launcher/LICENSE.txt
plugin.program.advanced.emulator.launcher/README.txt
~~~

Once the addon has been installed, it can be eddited in place (that is, in the Kodi directory where
the addon Python files are installed). This will simplify the development a lot!

## Developed environment ##

I created a soft link to the github cloned directory witht the correct name 
`plugin.program.advanced.emulator.launcher` and then created the zipfile with 

`$ zip -r plugin.program.advanced.emulator.launcher.zip plugin.program.advanced.emulator.launcher/*`

Then, intalled in Kodi with System -- Add-ons -- Install from zip file. It worked well.

# Installing the addon from github #

It is very important that the addon files are inside the correct directory
`plugin.program.advanced.emulator.launcher`.

To install the plugin from Github, click on `Clone or download` -- `Download ZIP`.
This will download the repository contents to a ZIP file named
`plugin.program.advanced.emulator.launcher-master.zip`. Also, addon is
packed inside directory `plugin.program.advanced.emulator.launcher-master`.

This ZIP file should be decompressed, the directory renamed to
`plugin.program.advanced.emulator.launcher`, and packed into a ZIP file again.
Then, install the ZIP file.
