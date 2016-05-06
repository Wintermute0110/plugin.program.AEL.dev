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
plugin.hyper.launcher/addon.xml
plugin.hyper.launcher/changelog.txt
plugin.hyper.launcher/default.py
plugin.hyper.launcher/fanart.jpg
plugin.hyper.launcher/icon.png
plugin.hyper.launcher/LICENSE.txt
plugin.hyper.launcher/README.txt
~~~

I think once the addon has been installed, it can be eddited in place (that is, in the Kodi directory).
This will simplify the development a lot!

I created a soft link to the github cloned directory witht the correct name, plugin.program.advanced.emulator.launcher,
and then created the zipfile with 

`$ zip -r plugin.program.advanced.emulator.launcher.zip plugin.program.advanced.emulator.launcher/*`

Then, intalled in Kodi with System -- Add-ons -- Install from zip file. It worked well.
