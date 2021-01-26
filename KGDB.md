# Kodi games database

A design for the Kodi games database. When this document is finished I will post it in the Kodi forum. Get inspiration from the Kodi Music Database in the Kodi wiki.

## Previous work

### Advanced Emulator Launcher

AEL gives total freedom for platform artwork. Each asset can be set on its own.

ROMs artwork are stored on a dedicated folders, each class of artwork in a subfolder there.

### Advanced MAME Launcher

AML uses a fixed set of directory names to store assets.

### EmulationStation themes

EmulationStation differentiates between **scraping platform** and **theme platform**. The scraping platform must be from the [official platform list names](https://github.com/RetroPie/EmulationStation/blob/master/es-app/src/PlatformId.cpp). The theme platform name is arbitrary, however all EmulationStation use the same names to keep compatibility among themes. The ES platform names are short names, for example `nes`, `genesis`, `megadrive`, `scummvm`, `cavestory`.

```
~/theme.xml
~/arcade/theme.xml
~/arcade/art/controller.svg
~/arcade/art/system.svg
~/genesis/theme.xml
~/genesis/art/controller.svg
~/genesis/art/system.svg
```

### Kodi Music Database

Kodi Music uses the **Artist information folder**.

### Kodi music graphical interface

**MyMusicNav.xml**

With an empty database.

```
Playlists     -> Opens MyMusicNav.xml
Sources       -> Opens MyMusicNav.xml
Files         -> Opens MyMusicNav.xml, inside there is "Add music..." that opens DialogMediaSource.xml
Music add-ons -> Opens MyMusicNav.xml
```

Music settings (complete).

## Type of game users

**Casual user**

This user has a few games only. Possibly all the ROMs are in a single directory.

```
/home/user/ROMs/dino.zip
/home/user/ROMs/qsound_hle.zip
/home/user/ROMs/Sonic The Hedgehog 3 (Europe).zip
/home/user/ROMs/Super Mario All-Stars and Super Mario World (Europe).zip
```

**Amateur user**

Has several platforms and possibly multiple games of each platform. ROMs of the same platform are separated into directories.

```
/home/user/ROMs/mame/dino.zip
/home/user/ROMs/mame/qsound_hle.zip
/home/user/ROMs/sega-megadrive/Sonic The Hedgehog 3 (Europe).zip
/home/user/ROMs/nintendo-snes/Super Mario All-Stars and Super Mario World (Europe).zip
```

**Advanced user**

Has full No-Intro and/or MAME romsets. Layout of ROMs is same as the amateur user. ROMs of the same platform are separated into directories.

## Getting started

Write a short tutorial of how to use the KGDB. First describe the simple case of all ROMs in one directory and then the case of ROMs in several directories.

### Simple setup for beginner users

### Recommended setup

First, organize your ROMs sorted by system.

```

```

Then, create the ROM Information Directory.

If you want to use platform metadata and artwork, create the ...

## Game sources and platform names

Game sources have the associated platform property. The platform name is chosen from a select dialog with a fixed-name list. If a game source directory has mixed ROMs (casual user) then the platform name is `Unknown`.

Platform names are a fixed list. Some platform names could be aliases. There are `Long names`, `Short names` and `Compact names`. Users are not allowed to freely choose platform names, this is to keep the theme layout consistent. A fixed list of platforms also enables automatic Libretro core selection. For example, for platform `megadrive` Kodi knows what libretro cores could be used to launch ROMs.

## Kodi Game Settings

**Setting.xml**

 * **ROM asset placement** Choose from `In the RAD` (default) or `Next to the ROMs`.

 * **ROM asset directory** If set it will be used to scan for local ROM artwork and for saving ROM scraped artwork.

 * **ROM asset naming scheme** Choose from `Long name`, `Short name`, `Compact name`. This is used for the platform directory names in the RAD.

 * **Recursive scan for ROMs** Boolean, default OFF.

 * **Platform information directory** If set it will be used to scan for platform metadata/artwork and saving scraped platform metadata/artwork.

 * **Platform naming scheme** Choose from `Long name`, `Short name`, `Compact name`.

## Kodi game graphical interface

**MyGames.xml**

In a new installation the user will see the following:

```
Game add-ons  --> Opens MyGames.xml
Add games...  --> Opens DialogMediaSource.xml
```

After adding some game sources and updating the database the user will see the following:

```
Platforms       --> Opens a list of platforms. Inside each platform ROMs can be browsed.
Games by Yitle  --> Opens a list of initial letter.
Games by Year   --> 
Games by Genre  --> 
Something more???
Game sources    --> Opens a list of game sources???
Something more???
Game add-ons    --> Opens MyGames.xml
Add games...    --> Opens DialogMediaSource.xml
```

## Game database scanning algortihm

**Describe the algorithm used for the database scanning**.

### Scanning for platform artwork

 * If the **platform information directory** is configured Kodi will search for platform metadata and artwork there.

```
<pid>/<pname>/<pname>.nfo
<pid>/<pname>/banner.png
<pid>/<pname>/clearlogo.png
<pid>/<pname>/controller.png -> Picture of controller.
<pid>/<pname>/fanart.png
<pid>/<pname>/media.png      -> Picture of cartridge, CD, etc.
<pid>/<pname>/icon.png
<pid>/<pname>/poster.png
<pid>/<pname>/system.png     -> Picture of the system, SS picture or illustration.
```

 * If the platform information directory is not set...

### ROMs asset directory

All ROMs belonging to the same platform share the artwork.

```
<rad>/<pname>/3dboxes/<ROM_name>.png
...
<rad>/<pname>/titles/<ROM_name>.png
<rad>/<pname>/trailers/<ROM_name>.png
```

Put the table for all the artwork types supported for each platform.

## Game database fields and infolabels

**Describe the game metadata fields and infolabels**

**How to deal with the platforms?** For example, each game have an associated platform and this platform have metadata and artwork that can be useful to display in game views.

## References

[KW: HOW-TO:Create Music Library](https://kodi.wiki/view/HOW-TO:Create_Music_Library)

[KF: when will the games database will be integrated into kodi](https://forum.kodi.tv/showthread.php?tid=343159)

[KF: Games artwork](https://forum.kodi.tv/showthread.php?tid=342558)

[KF: (Guide) Getting Started with Kodi Retroplayer](https://forum.kodi.tv/showthread.php?tid=340684&pid=2841688#pid2841688)

[KF: Advanced Emulator Launcher](https://forum.kodi.tv/showthread.php?tid=287826)

[Retropie EmulationStation](https://github.com/RetroPie/EmulationStation)

[Retropie es-theme-carbon](https://github.com/RetroPie/es-theme-carbon)

[Batocera batocera-themes](https://github.com/batocera-linux/batocera-themes)
