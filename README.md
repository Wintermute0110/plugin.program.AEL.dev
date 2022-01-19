# Advanced Kodi Launcher #

Advanced Kodi Launcher or AKL in short is another iteration of the launcher addons for Kodi. AKL is a multi-emulator front-end and general application launcher for Kodi, based and build upon AEL (Advanced Emulator Launcher). 
It is a modulair build with support for many plugins to either launch, scan or scrape ROMs and games from your favourite source.
Plugins are available for scanning your ROMs from different locations on your disks or from online sources like your steam library. There is support for scrapping ROM metadata and artwork from local disks or many different sources online. Also you can do ROM auditing for No-Intro ROMs using No-Intro or Redump XML DAT files (WiP). Of course, simply launching games with your favorite emulator or application is supported.  
Basically the possibilities are endless since you can easily extend AKL with your own plugins to add your type of launcher. Now you don't have to build a complete launcher addon, simply implement the plugin and hook it up in AKL. So one launcher addon to support all support them all. Add your own plugin now.

| Release | Status |
|----|----|
| Stable | [![Build Status](https://dev.azure.com/jnpro/AKL/_apis/build/status/plugin.program.akl?branchName=master)](https://dev.azure.com/jnpro/AKL/_build/latest?definitionId=5&branchName=master) |
| Beta | [![Build Status](https://dev.azure.com/jnpro/AKL/_apis/build/status/plugin.program.akl?branchName=release/1.0.0)](https://dev.azure.com/jnpro/AKL/_build/latest?definitionId=5&branchName=release/1.0.0) |
| Unstable | [![Build Status](https://dev.azure.com/jnpro/AKL/_apis/build/status/plugin.program.akl?branchName=dev)](https://dev.azure.com/jnpro/AKL/_build/latest?definitionId=5&branchName=dev) |

## What is different from AEL?
Not much actually. This is a friendly-ish fork of the original AEL version. I already was helping out and adding features to AEL, but with too many different features and alternative solutions we like to make it a bit more clear and make sure both versions can be stable. The main goal of AKL was to separate the launching, scanning and scraping logic to separate plugins so that it is more open to add more of these components to the addon, with an extra benefit that it is easier to maintain the core addon without doing major releases and changes. So as a result AKL can support more and different types of launchers, scanners and scrapers.  
Another benefit is that instead of having a launcher as the center entity, we now use collections of ROMs/games to build everything around. This means we can associate multiple launchers to whole collections and multiple scanners per collections, so you basically get multi-directory support. So not launcher based collections, but simply collections with multiple launchers, scanners and scrapers.  

*The goal still remains that the functionality and data will be as closely related and interchangeable as possible with AEL.*  
Meaning you can import and export your data from and to AEL if needed. I will keep on working together with Wintermute0110 on AEL and AKL and let both addons benefit from new things we add or discover. Most of the things discussed or mentioned in the AEL thread will also apply for AKL.

A special thanks to Wintermute0110 making AEL possible.

## Kodi forum thread ###

More information and discussion about AKL can be found here on the kodi forum [thread](https://forum.kodi.tv/showthread.php?tid=366351).  
More about AEL can be found in the original Advanced Emulator Launcher [thread](https://forum.kodi.tv/showthread.php?tid=287826) on the kodi forum.

## Documentation ###

Documentation about how to setup and use AKL can be found in the [Advanced Kodi Launcher Wiki](https://github.com/chrisism/plugin.program.akl/wiki).  
The original User's Guide for AEL, some tutorials and guides to configure emulators can be found in the [Advanced Emulator Launcher Wiki](https://github.com/Wintermute0110/plugin.program.advanced.emulator.launcher/wiki)

## Installing the latest released version ##

You can install my [repository](https://github.com/chrisism/repository.chrisism) locally in Kodi to install the plugin from there and keep it up to date. Or follow [this link](https://github.com/chrisism/repository.chrisism/tree/master/plugin.program.AKL) 
and download the ZIP file of the version you want. Use this ZIP file to install the addon in Kodi.

## Installing the latest beta version ##
Release candidates and beta versions can be found on the [dev repository](https://github.com/chrisism/repository.chrisism.dev). Simply collect the version you like from there.  
If you want to be really experimental you can clone/download the code from the dev branch and start using that version. Be aware of breaking changes in that version!

## Installing any version manual ##
If you are not a fan of repositories or you want to get the latests changes straight from development, you can always simply download the package yourself from the build pipeline in azure devops. Click on the status badge of the desired build type on the top of this page and you look for the proper release in the azure devops environment. 

## Install plugins
Just like the addon itself you can use the repositories as mentioned above. If you want to install it manually, go to [this link](https://github.com/chrisism/repository.chrisism) and select of the script.akl.*** plugins.
