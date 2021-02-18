# Kodi games database

This is a design proposal for the Kodi games database. First there are a set of chapters written in the form of user documentation or tutorial. These chapters are numbered like *1*, *2*, etc. Then there are a set of chapters with documentation for developers, numbered like *D1*, *D2*, etc.

## 1 Getting started (documentation section)

The purpose of this section is to serve as a tutorial to enable you to properly setup your games/ROMs an the Kodi Game library. Retrogaming could be a vast an overwhelming topic and hence this tutorial has been created with minimal jargon.

The first thing for you to understand is what type of games library you would like to have. If you are a **casual user** with just a bunch of games in a single directory the setup is very simple. However, as you expand your collection by adding more games it is necessary to organize your game collection. Also, if you like arcade games, arcade emulators require that your ROMs have specific file names and must be placed in specific locations.

### 1.1 An introduction to emulation and retrogaming

The purpose of this section is to explain some basic concepts for the very beginners, so skip this section if you are not so. This section is organized as a frequently answered questions (FAQ).

**What is retrogaming and emulation?**

Retrogaming is to play old games for obsoleted and/or abandoned systems on modern hardware and computers. There are several ways to do this and the most common is with **emulation**. Emulation means recreating in software the behaviour of the old hardware. Because modern hardware is much faster than the old one, in most cases emulated machines run at the same speed or faster than in the original hardware but this is not always the case.

**What is a game platform?**

For some platforms the definition is obvious, for example game consoles systems. However, things get complicated for arcade or other kind of systems. In Kodi, a game platform is the set of all games that can be run by a Libretro core. Sega Megadrive and Nintendo SNES are platforms, but also the single game Cave Story is a platform.

**Why games are sometimes named ROMs?**

ROM stands for read-only memory and comes for the systems that used cartridges for game distribution, for example the Sega Mega Drive or the Super Nintendo Entertaiment System. Modern emulators require the original software to execute the games in the form of file dumps of the contents of the ROM cartridges. By extension, modern files containing the dumps of the cartridges are called ROMs itself and the term can be used interchangably with games. Even platforms that did not use cartridges are also called ROMs by extension.

Typically ROMs for console systems consist of a single file, for example ... However, ROMs for arcaded systems are usually complicated and each game has several ROM files with strange names in a single ZIP file. For example, this is the ROM contents for the game Tetris.

**What is a ROM Manager?**

A ROM manager is a program to verify your ROMs. A ROM manager can also fix some problems with your ROMs, for example renaming ROMs with incorrect file name or deleting unknown ROMs. A ROM manager requires a DAT file.

**What is a DAT file?**

A DAT file is a text file, usually in XML, that contain the ROM names and the file checksums. DAT files can be used to verify your ROMs.

**What are No-Intro, Redump and TOSEC?**

No-Intro is an organisation of ROM dumpers that produce DAT files. No-Intro DAT files contain the officially released games but often oficial betas or pre-release versions are also included. No-Intro focuses on cartridge-based platforms. No-Intro ROM sets are the closes possible thing to having the original cartridges. The name No-Intro comes because some ROM dumpers modify the original ROMs to include their group logo and the like, what is called an "intro".

Redump is similar to No-Intro but focused on optical media systems (CD-ROMs, DVDs, LaserDiscs, etc.).

TOSEC is another organisation that provides that files. However, the aim of TOSEC is to catalog every piece of software.

There are other DAT producers like Goodsets, Trurip, etc.

**What is a ROM audit?**

A ROM audit is the process of scanning a set of ROMs and comparing them against a DAT file. The results of the audit is **Have** for ROMs you have that match the DAT, **Missing** for ROMs in the DAT you don't have, and **Unknown** for files you have not in the DAT. ROM manager may have other features, for example renaming ROMs to the correct name and fixing other problems.

### 1.2 A very short guide for the impatient casual user

**Step1** Create a directory and put your ROMs there.

**Step 2** Add the ROMs directory as a game source. As platform select **Mixed** or **Unknown**.

**Step 3** Scan your game library to update the Kodi database.

### 1.3 A very short guide for the impatient amateur/advanced user

**Step 1** Create one directory for each platform and place your ROMs there. It is advised that you follow the Kodi platform list for the platform names.

**Step 2** For each directory with ROMs add it as a games source, making sure you set the correct platform name.

**Step 3** Create the ROMs artwork directory. Then go to Kodi Game settings and set this directory as the **ROM asset directory**.

**Step 4** Download a Kodi Platform Artwork Theme and place it in a directory. Then go to Kodi Game settings and set this directory as the **Platform information directory**.

**Step 5** Scan your game library to update the Kodi database.

This is an example of the filesystem layout for this setup:
```
# Put your ROMs in separate directories, one directory per platform.
/home/user/ROMs/mame/dino.zip
/home/user/ROMs/mame/qsound_hle.zip
/home/user/ROMs/sega-megadrive/Sonic The Hedgehog 3 (Europe).zip
/home/user/ROMs/nintendo-snes/Super Mario All-Stars and Super Mario World (Europe).zip

# Create a directory for the ROMs assets/artwork.
# Configure this directory as the ROM asset directory in Kodi Game settings.
# Kodi will create the platform subdirectories automatically when scanning you game library.
# You can place the ROMs artwork files there.
/home/user/ROM-assets/
/home/user/ROM-assets/Nintendo SNES/
/home/user/ROM-assets/Sega Mega Drive/

# Create a directory for the Platform Artwork.
# Configure this directory as the Platform information directory in Kodi Game settings.
# Kodi will use the platform metadata NFO files and the platform artwork from here.
/home/user/Platform-assets/
/home/user/ROM-assets/Nintendo SNES/
/home/user/ROM-assets/Sega Mega Drive/
```

## 2 Game ROM file layout and ROM file names

This section describes the recommended file layout, that is, how to organize your games/ROMs into directories, and the correct file names for your ROMs.

If you just have some games you can place all of them in a single directory, for example:
```
/home/user/ROMs/dino.zip
/home/user/ROMs/qsound_hle.zip
/home/user/ROMs/Sonic The Hedgehog 3 (Europe).zip
/home/user/ROMs/Super Mario All-Stars and Super Mario World (Europe).zip
```

It is strongly recommended that you organise your games in directories, with one directory for each platform, like in the following example:
```
/home/user/ROMs/mame/dino.zip
/home/user/ROMs/mame/qsound_hle.zip
/home/user/ROMs/sega-megadrive/Sonic The Hedgehog 3 (Europe).zip
/home/user/ROMs/nintendo-snes/Super Mario All-Stars and Super Mario World (Europe).zip
```

You can use the names you wish for the platform names. However, it is advised that you use some logic that suits your needs or even better, take the platform names from the official Kodi platform list.

It is recommended that your ROMs for cartridge-based platforms follow the **No-Intro** naming convention. For optical media-based platforms it is recommended to follow the **Redump** naming convention.
```
# Example of No-Intro ROM file names
xxxxx

# Example of Redump file names
xxxxx
```

### 2.1 Notes for particular platforms

### 2.1.1 Arcade ROMs

## 3 Game database settings and filesystem layout formats

The settings described here are relevant to the Kodi Games database and not to Reptroplayer, the Kodi Libretro player.

In all examples in this section `<pid>` is the **ar**, for example `` in Linux or `` in Windows. ``

**ROM asset placement**

Choose from `In the RAD` (default) or `Next to the ROMs`.

If this setting is `In the RAD` Kodi will look for ROM artwork in the ROM asset directory and scrapers will save the artwork there. For example:
```
<rad>/Nintendo SNES/snaps/
<rad>/Nintendo SNES/titles/
```

If this settings is `Next to the ROMs` then the ROM asset directory setting will be ignored and your artwork files will be searched with a pattern like this:
```
/home/user/ROMs/sega-megadrive/Sonic The Hedgehog 3 (Europe).zip
/home/user/ROMs/sega-megadrive/Sonic The Hedgehog 3 (Europe)_fanart.png
/home/user/ROMs/sega-megadrive/Sonic The Hedgehog 3 (Europe)_title.png
...
```

**ROM asset directory**

If set it will be used to scan for local ROM artwork and for saving ROM scraped artwork.

**ROM asset naming scheme**

Choose from `Long name`, `Short name`, `Compact name`. If the ROM asset directory is not set this setting is ignored.

If this setting is `Long name` then the platform long name will be used for the platform subdirectories. In the following example `/home/user/ROM-assets` is the ROM asset directory.
```
/home/user/ROM-assets/Nintendo SNES/titles
/home/user/ROM-assets/Nintendo SNES/snaps
...
```

If this setting is `Short name`
```
/home/user/ROM-assets/nintendo-snes/titles
/home/user/ROM-assets/nintendo-snes/snaps
...
```

If this setting is `Compact name`
```
/home/user/ROM-assets/snes/titles
/home/user/ROM-assets/snes/snaps
...
/home/user/ROM-assets/megadrive/titles
/home/user/ROM-assets/megadrive/snaps
...
```

**Use only ROMs local artwork**

Boolean, default ON.

If ON do not scrape artwork for ROMs and pick it only from the ROM asset directory.

If OFF use the scrapers for ROM artwork.

**Recursive scan for ROMs**

Boolean, default OFF.

**Platform information directory**

If set it will be used to scan for platform metadata/artwork and saving scraped platform metadata/artwork.

**Platform naming scheme** Choose from `Long name`, `Short name`, `Compact name`.

## 4 Scanning games to the library

### 4.1 Adding games sources to the library

The first step is to set your game sources. In other words, you tell Kodi the directories where your games are.

 * **Step 1**: On the *Home menu* select *Games* from the menu items. 

 * **Step 2**: In the *Games File Browser* select *Add games*. In some cases you may need to select Files to access this. 

 * **Step 3**: In the *Add game source* window select Browse. You can also manually add your game source by selecting the box with <None> then typing in your path.

 * **Step 4**: You will now be taken back to the *Add game source*. Under *Enter a name for this game source* you can optionally name your game source to replace the suggested name. Select OK.

 * **Step 5**: Under *Enter a platform for this game source* choose the platform of this game source. If this game source has ROM for several platforms select the platform **Mixed**. If you are not sure about the platform then choose **Unknown**.

### 4.2 Manually scanning games to the library

After adding one or more game sources these game sources must be scanned to introduce your games into the game library. To manually scan all sources for new and changed items, follow these steps:

 * **Step 1**: Select *Games* from the *Home menu*.

 * **Step 2**: From the *Game Categories screen* or from within any category list (Platform, Genre, Artist, etc.) call up the Left Sidebar Menu which is normally left-arrow key.

 * **Step 4**: Select Update library.

Once the scanner finishes you will have a working games library.

### 4.3 Removing games from library

#### 4.3.1 Removing game sources

#### 4.3.2 Removing individual games

## 5 Platform information directory

```
<pid>/<pname>/<pname>.nfo
<pid>/<pname>/banner.png
<pid>/<pname>/clearlogo.png
<pid>/<pname>/controller.png -> Picture of controller.
<pid>/<pname>/fanart.png
<pid>/<pname>/media.png      -> Picture of cartridge, CD, etc.
<pid>/<pname>/icon.png
<pid>/<pname>/poster.png
<pid>/<pname>/system.png     -> Picture of the system, for example SS picture or illustration.
```

### 5.1 Platform NFO files

See https://kodi.wiki/view/NFO_files/Music

### 5.2 Official names for the platforms

## 6 Game artwork and game metadata NFO files

### 6.1 Supported game artwork types

### 6.2 ROM

All ROMs belonging to the same platform share the artwork.

```
<rad>/<pname>/3dboxes/<ROM_name>.png
...
<rad>/<pname>/titles/<ROM_name>.png
<rad>/<pname>/trailers/<ROM_name>.png
```

### 6.2 Game metadata NFO files

## 7 Updating the games database

## 8 Backup and recovery

## D1 Type of game users (design section)

**Casual user**

This user has only a few games, no more than 100. Possibly all the ROMs are in a single directory.
```
/home/user/ROMs/dino.zip
/home/user/ROMs/qsound_hle.zip
/home/user/ROMs/Sonic The Hedgehog 3 (Europe).zip
/home/user/ROMs/Super Mario All-Stars and Super Mario World (Europe).zip
```

**Amateur/Advanced user**

This user has games from several platforms and possibly multiple games of each platform. ROMs of the same platform are separated into directories.
```
/home/user/ROMs/mame/dino.zip
/home/user/ROMs/mame/qsound_hle.zip
/home/user/ROMs/mame/...
/home/user/ROMs/sega-megadrive/Sonic The Hedgehog 3 (Europe).zip
/home/user/ROMs/sega-megadrive/...
/home/user/ROMs/nintendo-snes/Super Mario All-Stars and Super Mario World (Europe).zip
/home/user/ROMs/nintendo-snes/...
```

Compared with the Amateur user, the Advanced user has full No-Intro and MAME collections which includes thousands of games for each of the main platforms. For example, recent version of MAME have about 40.000 machines and a full collection of SNES games is about 3500 games.

## D2 Game sources and platform names (design section)

Game sources have an associated platform property. The platform name is chosen from a select dialog with a fixed-name list. If a game source directory has mixed ROMs (casual user) then the platform name is `Unknown`. Some platform names could be aliases. There are `Long names`, `Short names` and `Compact names`. Users are not allowed to freely choose platform names, this is to keep the theme layout consistent. A fixed list of platforms also enables automatic Libretro core selection. For example, for platform `megadrive` Kodi knows what libretro cores could be used to launch ROMs.

Some example of platform names:

| Long name       | Short name     | Compact name |
|-----------------|----------------|--------------|
| Arcade - MAME   | arcade-mame    | mame         |
| Nintendo SNES   | nintendo-snes  | snes         |
| Sega Mega Drive | sega-megadrive | megadrive    |

## D3 Kodi game graphical interface (design section)

**MyGames.xml**

In a new installation the user will see the following:
```
Game add-ons  --> Opens MyGames.xml
Add games...  --> Opens DialogMediaSource.xml
```

After adding some game sources and updating the database the user will see the following:
```
Games by Platform           --> Opens a list of platforms. Inside each platform ROMs can be browsed.
Games by Title              --> Opens a list of title initial letters.
Games by Year               --> 
Games by Genre              --> 
Games by Developer          --> 
Games by Publisher          --> 
Games by Number of players  --> 
Most played games           --> Shows the most played games.
Recently added games        --> Shows the recently added games to the database.
Game sources                --> Opens a list of game sources.
Game add-ons                --> Opens the game addons.
Add games...                --> Opens DialogMediaSource.xml.
```

Inside `Games by Platform`:
```
Nintendo SNES
Sega Mega Drive
...
```

Inside `Games by Title`:
```
A
B
...
```

**Add game source window**

**Label** Enter the paths or browse for the game locations.

**Box with source paths** Buttons *Browse*, *Add* and *Remove*.

**Label** Enter a name for this game source.

**string edit box** Default name is the last directory name of the source.

**Label** Enter a platform for this game source.

**Drop down menu or button that opens a select dialog** Default platform is Unknown.

## D4 Game database scanning algorithm (design section)

**Describe the algorithm used for the database scanning**.

## D5 Game database fields and infolabels (design section)

[Music database model MusicDatabase.cpp](https://github.com/xbmc/xbmc/blob/master/xbmc/music/MusicDatabase.cpp)

**Describe the game metadata fields and infolabels**

### D5.1 Game metadata fields

| Name  | Type   | Comment |
|-------|--------|---------|
| title | string | Displayed name for the game |

### D5.2 Game artwork fields


## D6 Previous work (design section)

### Internet Archive Game Launhcer (IAGL)

### Hyperspin/HyperLauncher

### ROM Collection Browser

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

## D7 References and links

[KW: HOW-TO:Create Music Library](https://kodi.wiki/view/HOW-TO:Create_Music_Library)

[KF: when will the games database will be integrated into kodi](https://forum.kodi.tv/showthread.php?tid=343159)

[KF: Games artwork](https://forum.kodi.tv/showthread.php?tid=342558)

[KF: (Guide) Getting Started with Kodi Retroplayer](https://forum.kodi.tv/showthread.php?tid=340684&pid=2841688#pid2841688)

[KF: Advanced Emulator Launcher](https://forum.kodi.tv/showthread.php?tid=287826)

[Retropie EmulationStation](https://github.com/RetroPie/EmulationStation)

[Retropie es-theme-carbon](https://github.com/RetroPie/es-theme-carbon)

[Batocera batocera-themes](https://github.com/batocera-linux/batocera-themes)
