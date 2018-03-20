# Retroarch Launcher
The Retroarch launcher depends on an Retroarch instance to be able to launch the scanned ROM files.
Get your copy from the [Retroarch website](http://www.retroarch.com/).

## Creating a Retroarch Launcher
When you create a Retroarch launcher AEL will try to find all Retroarch configuration files available in the application folder.
Either select one of the found configuration files or specify the path to the configuration file manually. Once given AEL will automatically load the configuration file and use the configured cores and infos folder to present the list of available cores.

When you select the desired core AEL will also apply the default ROM extensions of the core and use the systemname and manufactorer as default information for the launcher. All of this you can change in the following steps after selecting the core.

You can also add extra launch arguments, but take note that the default launching arguments will be already added by the launcher itself. The used arguments are for selecting the correct core instance, the correct configuration file and ofcourse the actual ROM file. 

Details about the CLI arguments can be found [here](https://docs.libretro.com/guides/cli-intro/).

## On Android
The default paths for Retroarch cores and info files under Android are only scannable when the OS is rooted. When running on a non-rooted Android box the best option is to open up Retroarch and configure paths for the cores and infos that are actually accessible. 
Don't forget to update/download the cores and info file after changing the paths.