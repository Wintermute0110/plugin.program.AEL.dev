# Advanced Kodi Launcher #

Multi-emulator front-end and general application launcher for Kodi, based and build upon AEL (Advanced Emulator Launcher). 
It is a modulair build with support for many plugins to either launch, scan or scrape ROMs and games from your favourite source.  
Plugins are available for offline scrapers for MAME, scanners for No-Intro ROM sets and also support for scrapping ROM metadata and artwork from many different sources online. There is ROM auditing for No-Intro ROMs using No-Intro or Redump XML DAT files.  
Simply launching of games and standalone applications is also available.

| Release | Status |
|----|----|
| Stable | [![Build Status](https://dev.azure.com/jnpro/AKL/_apis/build/status/plugin.program.akl?branchName=master-fork)](https://dev.azure.com/jnpro/AKL/_build/latest?definitionId=5&branchName=master-fork) |

### What is different from AEL?
Not much actually. This is a friendly-ish fork of the original AEL version. The main goal was to separate the launching, scanning and scraping logic to separate plugins so that it is more open to add more of these components to the addon, without doing major releases and changes. So AKL will support more and different types of launchers etc.  
One of the other benefits is instead of having a launcher as the center model, we now use collections of ROMs/games as the center. This means we can associate multiple launchers to whole collections and multiple scanners per collections, so you basically get multi-directory support.

### Kodi forum thread ###

More information and discussion about AEL can be found in the [Advanced Emulator Launcher thread] 
in the Kodi forum.

[Advanced Emulator Launcher thread]: https://forum.kodi.tv/showthread.php?tid=287826

### Documentation ###

The original User's Guide, some tutorials and guides to configure emulators can be found in 
the [Advanced Emulator Launcher Wiki].

[Advanced Emulator Launcher Wiki]: https://github.com/Wintermute0110/plugin.program.advanced.emulator.launcher/wiki

## Installing the latest released version ##

You can install this [repository](https://github.com/chrisism/repository.chrisism) locally in Kodi to install and keep it up to date. Or follow [this link](https://github.com/chrisism/repository.chrisism/tree/master/plugin.program.AEL) 
and download the ZIP file of the version you want. Use this ZIP file to install the addon in Kodi.

## Installing the latest beta version ##
Release candidates and beta versions can be found on the [dev repository](https://github.com/chrisism/dev.repository.chrisism). Simply collect the version you like from there.  
If you want to be really experimental you can clone/download the code from the dev branch and start using that version. Be aware of breaking changes in that version!

## Install plugins
Just like the addon itself you can use the repositories as mentioned above. If you want to install it manually, go to [this link](https://github.com/chrisism/repository.chrisism) and select of the script.akl.*** plugins.
