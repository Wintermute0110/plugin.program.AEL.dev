# Advanced Emulator Launcher #

Multi-emulator front-end and general application launcher for Kodi. Includes offline scrapers for 
MAME and No-Intro ROM sets and also supports scrapping ROM metadata and artwork online. 
ROM auditing for No-Intro ROMs using No-Intro or Redump XML DAT files. Launching of games 
and standalone applications is also available.

### Kodi forum thread ###

More information and discussion about AEL can be found in the [Advanced Emulator Launcher thread] 
in the Kodi forum.

[Advanced Emulator Launcher thread]: https://forum.kodi.tv/showthread.php?tid=287826

### Documentation ###

A User's Guide, some tutorials and guides to configure emulators can be found in 
the [Advanced Emulator Launcher Wiki].

[Advanced Emulator Launcher Wiki]: https://github.com/Wintermute0110/plugin.program.advanced.emulator.launcher/wiki

## Installing the latest released version ##

Follow [this link](https://github.com/Wintermute0110/repository.wintermute0110/tree/master/plugin.program.advanced.emulator.launcher) 
and download the ZIP file of the version you want. Use this ZIP file to install the addon in Kodi.

## Installing the latest development version ##

It is important that you follow this instructions or Advanced Emulator Launcher won't work well.

  1) In this page click on the green button `Clone or Download` --> `Download ZIP`

  2) Uncompress this ZIP file. This will create a folder named `plugin.program.advanced.emulator.launcher-master`

  3) Rename that folder to `plugin.program.advanced.emulator.launcher`

  4) Compress that folder again into a ZIP file. 

  5) In Kodi, use that ZIP file (and not the original one) to install the plugin in `System` --> `Addons` 
     --> `Install from ZIP file`.

  6) You are done!

# Retroarch Launcher

The Retroarch launcher depends on an Retroarch instance to be able to launch the scanned ROM files.
Get your copy from the [Retroarch website](http://www.retroarch.com/).

## Creating a Retroarch Launcher

When you create a Retroarch launcher AEL will try to find all Retroarch configuration files available
in the application folder. Either select one of the found configuration files or specify the path to
the configuration file manually. Once given AEL will automatically load the configuration file and
use the configured cores and infos folder to present the list of available cores.

When you select the desired core AEL will also apply the default ROM extensions of the core and use
the systemname and manufactorer as default information for the launcher. All of this you can change
in the following steps after selecting the core.

You can also add extra launch arguments, but take note that the default launching arguments will be
already added by the launcher itself. The used arguments are for selecting the correct core instance,
the correct configuration file and ofcourse the actual ROM file. 

Details about the CLI arguments can be found [here](https://docs.libretro.com/guides/cli-intro/).

## On Android

The default paths for Retroarch cores and info files under Android are only scannable when the OS
is rooted. When running on a non-rooted Android box the best option is to open up Retroarch and
configure paths for the cores and infos that are actually accessible. 
Don't forget to update/download the cores and info file after changing the paths.

# Pairing with Nvidia Gamestream PC #

We now have the ability to launch PC games through Nvidia gamestreaming. To scan for the available games on your
PC we need to pair with the PC running Geforce Experience and for this we need valid certificates. Unfortunatly at 
the moment we do not have default support in Kodi to do the needed actions with encryption and certificates to make 
a secure connection. So to create the valid certificates and finish up the pairing process you need to do one of 
the following actions.

## 1. Run custom pairing python scripts 

Download the source code for AEL from github and place it on your computer. Make sure you have Python installed and 
the needed libraries, like the OpenSSL. Then go to the /tools folder of the source code.
The script must be called with two parameters, host and path where to store the new certificates.

Example: 
```
>python pair_with_nvidia.py 192.168.1.99 c:\games\gamestream\
```

When started, this tool will show a unique pincode which you need to enter in a dialog on your computer which is running 
Nvidia Geforce Experience. When done correctly it will pair up with that computer and generate certificates needed to 
keep on communicating with the geforce experience computer. These certificates can be used in a Gamestream Launcher when
running AEL in Kodi.

## 2. Use certificates from Moonlight

If you have installed Moonlight as your client for Nvidia Gamestream and you already used that to pair with your Gamestream
server, then you can reuse those certificates. Out of the box the certificates are not yet ready to be used with the AEL scripts.
You will need to have OpenSSL on your computer to transform the private key certificate to the supported format.

Execute the following command with OpenSSL:
```
openssl pkcs8 -topk8 -inform DER -outform PEM -nocrypt -in <MOONLIGHT_KEY_FILE_PATH>.key -out <YOUR_FILE_NAME>.key
```

Copy the new *.key and *.crt to a separate folder. Now you can use these certificate files when creating your launcher in AEL 
in Kodi.
