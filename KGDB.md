This is a design proposal for the Kodi games database. First there are a set of chapters written in the form of user documentation or tutorial. These chapters are numbered like *1*, *2*, etc. Then there are a set of chapters with documentation for developers, numbered like *D1*, *D2*, etc.

# 1 Getting started (documentation section)

The purpose of this section is to serve as a tutorial to enable you to properly setup your games/ROMs and the Kodi Game library. Retrogaming could be a vast an overwhelming topic and hence this tutorial has been created with minimal jargon.

The first thing for you to understand is what type of games library you would like to have. If you are a **casual user** with just a bunch of games in a single directory the setup is very simple. However, as you expand your library by adding more games it is necessary to organize your game collection. Also, if you like arcade games then proper organization is a must because arcade emulators require that your ROMs have specific file names and must be placed in specific locations.

## 1.1 An introduction to emulation and retrogaming

The purpose of this section is to explain some basic concepts for the very beginners, so skip this section if you are not so. This section is organized as a frequently answered questions (FAQ).

**What is retrogaming and emulation?**

Retrogaming is to preserve and play old games for obsolete or abandoned systems on modern hardware and computers. There are several ways to do this and the most common is with **emulation**. Emulation means recreating in software the behaviour of the old hardware. Because modern hardware is much faster than the old one, in most cases emulated machines run at the same speed or even much faster than in the original hardware. However, this is not always the case and as a rule of thumb the more recent a system is the more powerful a computer you need to emulate it at full speed.

**What is a game platform?**

In most cases the definition is obvious, for example for console game systems. However, things get complicated for arcade or computer systems. In Kodi, a game platform is the set of all games that can be run by a Libretro core. Sega Megadrive and Nintendo SNES are platforms, but also the single game Cave Story is a platform.

**Why games are sometimes named ROMs?**

ROM stands for read-only memory and comes from the systems that used cartridges for game distribution, for example the Sega Mega Drive or the Super Nintendo Entertaiment System. Modern emulators require the original software to execute the games in the form of file dumps of the contents of the cartridge ROMs. By extension, modern files containing the dumps of the cartridges are called ROMs itself and the term can be used interchangably with games. Even platforms that did not use cartridges are also called ROMs by extension.

Typically ROMs for console systems consist of a single file which is in a ZIP file to save disk space. However, ROMs for arcade systems are usually complex and each game has several ROM files with strange names in a single ZIP file. For example, this is the ROM contents for the arcade game Tetris. In order to play the game, these 2 files must reside in a ZIP file named `atetris.zip` that must be placed in a specific directory. Otherwise, the emulator won't work.

| ROM name        | Size   |
|-----------------|--------|
| 136066-1100.45f | 65,536 |
| 136066-1101.35a | 65,536 |

**What is a ROM Manager?**

A ROM manager is a program to verify your ROMs. A ROM manager can also fix some problems with your ROMs, for example renaming ROMs with incorrect file name or deleting unknown ROMs. A ROM manager requires a DAT file for each platform to verify.

**What is a DAT file?**

A DAT file is a text file, usually in XML format, that contain the ROM names and the file checksums. DAT files are databases and can be used to verify your ROMs.

**What are No-Intro, Redump and TOSEC?**

No-Intro is an organisation of ROM dumpers that produce DAT files. No-Intro DAT files contain the officially released games and often betas or pre-release versions for preservation and historical purposes. No-Intro focuses on cartridge-based platforms. No-Intro ROM sets are the closest possible thing to having the original cartridges. The name No-Intro comes because some ROM dumpers modify the original ROMs to include their group logo and the like, what is called an "intro".

Redump is similar to No-Intro but focused on optical media systems (CD-ROMs, DVDs, LaserDiscs, etc.).

TOSEC is another organisation that provides DAT files. However, the aim of TOSEC is to catalog every piece of software including what many people consider garbage, for example, incorrect ROM dumps, overdumped files, etc.

There are other DAT producers like Goodsets, Trurip, etc.

**What is a ROM audit?**

A ROM audit is the process of scanning a set of ROM files and comparing them against a DAT database file. The results of the audit is **Have** for ROMs you have that match the DAT, **Missing** for ROMs in the DAT you don't have, and **Unknown** for files you have not in the DAT. ROM managers may have other features, for example renaming ROMs to the correct name and fixing other problems.

## 1.2 A very short guide for the impatient casual user

**Step 1** Create a directory and put your ROMs there.

**Step 2** Add the ROMs directory as a game source. As platform select **Mixed** or **Unknown**.

**Step 3** Scan your game library to update the Kodi games library.

## 1.3 A very short guide for the impatient amateur/advanced user

**Step 1** Create one directory for each platform and place your ROMs there. It is advised that you follow the Kodi platform list for the platform names to keep your setup tidy and organized.

**Step 2** For each directory with ROMs add it as a games source, making sure you set the correct platform name.

**Step 3** Create the ROMs artwork directory. Then go to Kodi Game settings and set this directory as the **ROM asset directory**.

**Step 4** Download a Kodi Platform Artwork Theme and place it in a directory. Then go to Kodi Game settings and set this directory as the **Platform information directory**.

**Step 5** Scan your game library to update the Kodi games library.

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
/home/user/Platform-assets/Nintendo SNES/
/home/user/Platform-assets/Sega Mega Drive/
```

# 2 Preparing the files: Game ROM file layout and ROM file names

This section describes the recommended file layout, that is, how to organize your games/ROMs into directories, and the correct file names for your ROMs.

## 2.1 Preparation of files for the casual user

If you just have some games you can place all of them in a single directory, for example:
```
/home/user/ROMs/dino.zip
/home/user/ROMs/qsound_hle.zip
/home/user/ROMs/Sonic The Hedgehog 3 (Europe).zip
/home/user/ROMs/Super Mario All-Stars and Super Mario World (Europe).zip
```

This is the most simple setup and some users will find it suitable. However, it is strongly advised that you separate you ROMs into per-platform directories. If you place all your ROMs in a single directory then Kodi has to guess the platform of each game and in some cases this is very difficult and prone to mistakes.

## 2.2 Preparation of files for the amateur/advanced user

Place you games in directories with one directory for each platform, like in the following example:
```
/home/user/ROMs/mame/dino.zip
/home/user/ROMs/mame/qsound_hle.zip
/home/user/ROMs/sega-megadrive/Sonic The Hedgehog 3 (Europe).zip
/home/user/ROMs/nintendo-snes/Super Mario All-Stars and Super Mario World (Europe).zip
```

You can use the names you wish for the platform names. However, it is advised that you use some logic that suits your needs or even better, take the platform names from the official Kodi platform list.

## 2.3 Game/ROM file names

You can choose the filenames you want for your ROMs and Kodi and the scrapers will do their best to correctly deal with your game. However, in order to maximize your experience with the game library it is recommended that your ROMs for cartridge-based platforms follow the **No-Intro** naming convention. For optical media-based platforms it is recommended to follow the **Redump** or **Trurip** naming conventions. No-Intro and Redump file names include the game region and the game languages which will improve the scraping of your ROMs.
```
# Examples of No-Intro ROM file names
Super Mario World (Europe) (Rev 1).zip
Super Mario World (USA, Europe) (Virtual Console, Classic Mini, Switch Online).zip
Sonic The Hedgehog (USA, Europe).zip
Sonic The Hedgehog 2 (World).zip
Sonic The Hedgehog 3 (USA).zip

# Examples of Redump file names
Final Fantasy VII (Europe) (Disc 1).chd
Final Fantasy VII (Europe) (Disc 2).chd
Final Fantasy VII (Europe) (Disc 3).chd

# Examples of Trurip file names
xxxxx
```

Note that arcade emulators, and MAME in particular, require the game ROMs to have specific and often cryptical names, for example Capcom's Cadillacs and Dinosaurs ROM must be named `dino.zip`.

## 2.4 Notes for special platforms

## 2.4.1 Arcade ROMs

> **Question for devs** The arcade ROMs in MAME and other arcade emulators have special names, for example `atetris.zip` or `dino.zip`. This games must be translated to proper names when scanning the database. Should Kodi include a database to convert MAME names into proper titles? Should this XML/JSON database included in an addon? EmulationStation, AEL, and other front-ends use this offline scraper databases.

## 2.4.2 ScummVM

> **Question for devs** The ScummVM ROMs consist of several files and are usually kept in a subdirectory. This subdirectory has the real game name.

# 3 Game database settings

The settings described here are relevant to the Kodi Games database and not to Reptroplayer, the Kodi Libretro player. In all examples in this section:

 * `<rad>` is the **ROM asset directory**, for example `/home/kodi/ROM-assets/` in Linux or `Z:\ROM-assets\` in Windows.

 * `<pid>` is the **Platform information directory**, for example `/home/user/Platform-assets/` in Linux or `Z:\Platform-assets/` in Windows.

> **TODO** How to support multidisc games? 

**ROM asset placement**

Choose from `In the RAD` (default) or `Next to the ROMs`. If this setting is `In the RAD` Kodi will look for ROM artwork in the ROM asset directory and scrapers will save the artwork there. For example:
```
<rad>/Nintendo SNES/snaps/
<rad>/Nintendo SNES/titles/
...
```

> **Question for devs** If recursive ROM scan is enabled how to generate the ROM artwork filenames? Note that in some special platform like ScummVM the ROM title is the subdirectory name...

If this setting is `Next to the ROMs` then the ROM asset directory setting will be ignored and your artwork files will be searched with a pattern like this:
```
/home/user/ROMs/sega-megadrive/Sonic The Hedgehog 3 (Europe).zip
/home/user/ROMs/sega-megadrive/Sonic The Hedgehog 3 (Europe)_fanart.png
/home/user/ROMs/sega-megadrive/Sonic The Hedgehog 3 (Europe)_title.png
...
```

**ROM asset directory**

If set it will be used to scan for local ROM artwork and for saving ROM scraped artwork.

**ROM asset naming scheme**

Choose from `Long name`, `Short name`, `Compact name`. If the ROM asset directory is not set this setting is ignored. Kodi will create the platform subdirectories automatically when the game library is scanned.

If this setting is `Long name` then the platform long name will be used for the platform subdirectories in the RAD.
```
<rad>/Nintendo SNES/titles
<rad>/Nintendo SNES/snaps
...
```

If this setting is `Short name` then the platform long name will be used for the platform subdirectories in the RAD.
```
<rad>/nintendo-snes/titles
<rad>/nintendo-snes/snaps
...
```

If this setting is `Compact name` then the platform long name will be used for the platform subdirectories in the RAD.
```
<rad>/snes/titles
<rad>/snes/snaps
...
```

**Only use ROMs local artwork**

Boolean, default ON. If ON do not scrape artwork for ROMs and pick it only from the ROM asset directory. If OFF use the scrapers for ROM artwork.

> **Question for devs** Should the scrapers download the ROM artwork and place it in the RAD or just place the online artwork into the Kodi texture cache?

**Recursive scan for ROMs**

Boolean, default OFF.

> **Question for devs** See comments in setting **ROM asset placement**.

**Platform information directory**

If set it will be used to scan for platform metadata/artwork and saving scraped platform metadata/artwork.

# 4 Scanning games to the library

## 4.1 Adding games sources to the library

The first step is to set your game sources. In other words, you tell Kodi the directories where your games are.

 * **Step 1**: On the *Home menu* select *Games* from the menu items. 

 * **Step 2**: In the *Games File Browser* select *Add games*. In some cases you may need to select Files to access this. 

 * **Step 3**: In the *Add game source* window select Browse. You can also manually add your game source by selecting the box with <None> then typing in your path.

 * **Step 4**: You will now be taken back to the *Add game source*. Under *Enter a name for this game source* you can optionally name your game source to replace the suggested name. Select OK.

 * **Step 5**: Under *Enter a platform for this game source* choose the platform of this game source. If this game source has ROM for several platforms select the platform **Mixed**. If you are not sure about the platform then choose **Unknown**.

## 4.2 Manually scanning games to the library

After adding one or more game sources these game sources must be scanned to introduce your games into the game library. To manually scan all sources for new and changed items, follow these steps:

 * **Step 1**: Select *Games* from the *Home menu*.

 * **Step 2**: From the *Game Categories screen* or from within any category list (Platform, Genre, Artist, etc.) call up the Left Sidebar Menu which is normally left-arrow key.

 * **Step 4**: Select Update library.

Once the scanner finishes you will have a working games library.

# 5 Platform information directory

The **Platform information directory** is a read-only directory to place the platform metadata NFO files and the platform arwork. This allows to create platform themes for Kodi that can be downloaded and changed, or even placed inside Kodi addons.

The layout for the platform information directory is a follows:
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

## 5.1 Platform NFO files

See [KW: NFO_files/Music](https://kodi.wiki/view/NFO_files/Music)

## 5.2 Supported platform artwork

See...

## 5.3 Official names for the platforms

# 6 Game artwork and game metadata NFO files

## 6.1 Supported game artwork types

## 6.2 ROM artwork

All ROMs belonging to the same platform share the artwork.

```
<rad>/<pname>/3dboxes/<ROM_name>.png
...
<rad>/<pname>/titles/<ROM_name>.png
<rad>/<pname>/trailers/<ROM_name>.png
```

## 6.2 Game metadata NFO files

# 7 Scraping additional game data and artwork

# 8 Updating the games database

This page will provide information to enable you to add new games, modify existing games and removing games from your **existing** games library.

## 8.1 Scanning the games library

The **Update library** function scans your game sources looking for new or changed games.

## 8.2 Scraping game library metadata and artwork

To be written.

## 8.3 Removing games from the library

Removing games from the library can be done using two methods.

### 8.3.1 Removing a game source

If you remove a game source all the games contained in that source will be reomved from the game library. To remove a game source follow these steps:

**Step 1** Select **Games** from the main menu.

**Step 2** Navigate to and enter the **Game sources** section.

**Step 3** Highlight the game source to be removed and open the context menu. In the game source context menu select **Remove source**

**Questions for devs** Should the games be removed inmmediately or when the library is next updated? Does it make sense to have games in the library if the game source has been removed?

### 8.3.2 Removing a single game from the library

Single games can be removed from the game library. However, note that if you do not remove the ROM filename of the game it will be added again when you update your library. There are two methods to remove a single game from the library:

**Option 1** Use the file browser or manager in your operating system and remove the game ROM or place in a directory that is not a game source. Then, in Kodi settings run a **Clean games library**.

**Option 2** In the Kodi main menu select **Games**, enter and select **Files**. Browse and locate the game ROM you want to delete. Open the context menu and select **Delete**. Be aware that this will delete your game ROM file from your hard disk. Finally go to Kodi settings and run **Clean games library**.

**Questions for devs** This procedure works for standard No-Intro ROM ZIP files or MAME zipped ROMs where each game is a single file. However, in some platforms like ScummVM each game is composed of multiple files, usually inside a subdirectory in the game source.

# 9 Importing and exporting your games library

To be written.

# 10 Backup and recovery

To be written.

# D1 Type of game users (design section)

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

Compared with the Amateur user, the Advanced user has full No-Intro and MAME collections which includes thousands of games for each of the main platforms. For example, recent version of MAME have about 40,000 machines and a full collection of SNES games is about 3,500 games.

# D2 Game sources and platform names (design section)

Game sources have an associated platform property. The platform name is chosen from a select dialog with a fixed-name list. If a game source directory has mixed ROMs (casual user) then the platform name is `Unknown`. Some platform names could be aliases. There are `Long names`, `Short names` and `Compact names`. Users are not allowed to freely choose platform names, this is to keep the theme layout consistent. A fixed list of platforms also enables automatic Libretro core selection. For example, for platform `megadrive` Kodi knows what libretro cores could be used to launch ROMs.

Some example of platform names:

| Long name       | Short name     | Compact name |
|-----------------|----------------|--------------|
| Arcade - MAME   | arcade-mame    | mame         |
| Nintendo SNES   | nintendo-snes  | snes         |
| Sega Mega Drive | sega-megadrive | megadrive    |

# D3 Kodi game graphical interface (design section)

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

# D4 Game database scanning algorithm (design section)

**Describe the algorithm used for the database scanning**.

# D5 Game database fields and infolabels (design section)

[Music database model MusicDatabase.cpp](https://github.com/xbmc/xbmc/blob/master/xbmc/music/MusicDatabase.cpp)

**NOTE** Here I use Python data types to describe the database. I will change this to an SQL model ASAP. Proper changes must be made when translating to SQL, for example, **genre** is a list of string in Python which requires a table for the unique genres plus an additional table to link game_ids to genre_ids.

## D5.1 Game metadata fields

[KW: Infolabels#Game](https://kodi.wiki/view/InfoLabels#Game)

| Kodi v | Name       | Type            | Infolabel       | Comment |
|--------|------------|-----------------|-----------------|---------|
| v18    | title      | string          | Game.Title      | Displayed name for the game |
| v18    | platform   | string          | Game.Platform   | Platform list is fixed. (4) |
| v18    | genres     | list of strings | Game.Genres     | Genres of the game (eg. Action) |
| v18    | developer  | string          | Game.Publisher  | Game developer. |
| v18    | publisher  | string          | Game.Developer  | Publishing company of the game. |
| v18    | overview   | string          | Game.Overview   | Game plot or description. |
| v18    | year       | date            | Game.Year       | Release year. Delete and use release. |
| v18    | gameclinet | date            | Game.GameClient | Name of the used emulator. |
|        | release    | date            |                 | Release date. |
|        | nplayers   | string          |                 | Number of players (1) |
|        | esrb       | string          |                 | ESRB rating. |
|        | regions    | list of strings |                 | Game regions (2)   |
|        | languages  | list of strings |                 | Game languages (3) |
|        | rating     | string?         |                 | User rating. |

(1) Use the MAME nplayers.ini format, "1P", "2P sim", "2P alt", etc.

(2) Use No-Intro region names.

(3) Use No-Intro language names. Language is set if not implicit from the region. For example, a game for the region Japan in Japanese do not need to set this field. However, if the Japanese game is in Japanese and English then this field is set to En,Ja.

(4) The name of the platforms is a fixed list. The user can choose the platform but not change the platform name. There is the platform "Unknown" and its alias "Mixed".

## D5.2 Game artwork fields

See [AEL technical notes](https://github.com/Wintermute0110/plugin.program.AEL/blob/release-0.x.y-python2/NOTES.md).

# D6 Previous work (design section)

## Internet Archive Game Launhcer (IAGL)

## Hyperspin/HyperLauncher

## ROM Collection Browser

## Advanced Emulator Launcher

AEL gives total freedom for platform artwork. Each asset can be set on its own.

ROMs artwork are stored on a dedicated folders, each class of artwork in a subfolder there.

## Advanced MAME Launcher

AML uses a fixed set of directory names to store assets.

## EmulationStation themes

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

## Kodi Music Database

Kodi Music uses the **Artist information folder**.

## Kodi music graphical interface

**MyMusicNav.xml**

With an empty database.

```
Playlists     -> Opens MyMusicNav.xml
Sources       -> Opens MyMusicNav.xml
Files         -> Opens MyMusicNav.xml, inside there is "Add music..." that opens DialogMediaSource.xml
Music add-ons -> Opens MyMusicNav.xml
```

Music settings (complete).

# D7 References and links

[KW: HOW-TO:Create Music Library](https://kodi.wiki/view/HOW-TO:Create_Music_Library)

[KF: when will the games database will be integrated into kodi](https://forum.kodi.tv/showthread.php?tid=343159)

[KF: Games artwork](https://forum.kodi.tv/showthread.php?tid=342558)

[KF: (Guide) Getting Started with Kodi Retroplayer](https://forum.kodi.tv/showthread.php?tid=340684&pid=2841688#pid2841688)

[KF: Advanced Emulator Launcher](https://forum.kodi.tv/showthread.php?tid=287826)

[Retropie EmulationStation](https://github.com/RetroPie/EmulationStation)

[Retropie es-theme-carbon](https://github.com/RetroPie/es-theme-carbon)

[Batocera batocera-themes](https://github.com/batocera-linux/batocera-themes)
