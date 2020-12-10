# Kodi games database

A design for the Kodi games database. When this document is finished I will post it in the Kodi forum.

Get inspiration from the Kodi Music Database in the Kodi wiki.

## Previous work

### Advanced Emulator Launcher

AEL gives total freedom for platform artwork.


### Advanced MAME Launcher


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

## Type of game users

**Casual user**

Has a few games only. Possibly all the ROMs are in a single source.

**Amateur user**

Has several platforms and possible multiple games of each platform.

**Advanced user**

Has full No-Intro and/or MAME romsets.

## Game artwork model

## Platform Information directory

```
$pid$/$platform_name$/$platform_name$.nfo
$pid$/$platform_name$/banner.png
$pid$/$platform_name$/clearlogo.png
$pid$/$platform_name$/controller.png
$pid$/$platform_name$/fanart.png
$pid$/$platform_name$/media.png
$pid$/$platform_name$/icon.png
$pid$/$platform_name$/poster.png
```

## ROMs artwork directory

All ROMs belonging to the same platform share the artwork. What to do with MAME and No-Intro?

```
$rad$/$platform_name$/boxfront/$ROM_name$.png
$rad$/$platform_name$/titles/$ROM_name$.png
```

## Kodi music graphical interface

**MyMusicNav.xml**

With an empty database.

```
Playlists -> Opens MyMusicNav.xml
Sources -> Opens MyMusicNav.xml
Files -> Opens MyMusicNav.xml, inside there is "Add music..." that opens DialogMediaSource.xml
Music add-ons -> Opens MyMusicNav.xml
```

## Kodi game graphical interface

**MyGames.xml**

```
Game add-ons -> Opens MyGames.xml
Add games... -> Opens DialogMediaSource.xml
```

## References

[KW: HOW-TO:Create Music Library](https://kodi.wiki/view/HOW-TO:Create_Music_Library)

[KF: when will the games database will be integrated into kodi](https://forum.kodi.tv/showthread.php?tid=343159)

[KF: Games artwork](https://forum.kodi.tv/showthread.php?tid=342558)

[KF: (Guide) Getting Started with Kodi Retroplayer](https://forum.kodi.tv/showthread.php?tid=340684&pid=2841688#pid2841688)

[KF: Advanced Emulator Launcher](https://forum.kodi.tv/showthread.php?tid=287826)

[Retropie EmulationStation](https://github.com/RetroPie/EmulationStation)

[Retropie es-theme-carbon](https://github.com/RetroPie/es-theme-carbon)

[Batocera batocera-themes](https://github.com/batocera-linux/batocera-themes)
