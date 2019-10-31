## AEL technical notes ##

### Current menus in 0.9.8

Context menu **Edit Launcher**, submenu **Manage ROMs ...**:
```
'Choose ROMs default artwork ...',
'Manage ROMs asset directories ...',
'Rescan ROMs local artwork',
'Scrape ROMs artwork',
'Remove dead/missing ROMs',
'Import ROMs metadata from NFO files',
'Export ROMs metadata to NFO files',
'Delete ROMs NFO files',
'Clear ROMs from launcher',
```

Display modes: LAUNCHER_DMODE_FLAT, LAUNCHER_DMODE_PCLONE, LAUNCHER_DMODE_1G1R.
PCLONE and 1G1R are the same, the difference is that in 1G1R the ROM Context 
Menu **Show clones** is displayed and Parents are launcher automatically. AML now has
FLAT and 1G1R modes only.

Display filters: NOINTRO_DMODE_ALL, NOINTRO_DMODE_HAVE, NOINTRO_DMODE_HAVE_UNK,
NOINTRO_DMODE_HAVE_MISS, NOINTRO_DMODE_MISS, NOINTRO_DMODE_MISS_UNK, NOINTRO_DMODE_UNK.

Context menu **Edit Launcher**, submenu **Audit ROMs / Launcher view mode ...**:
```
'Change launcher display mode (now {0}) ...'.format(display_mode_str),
'Add No-Intro/Redump XML DAT ...' OR 'Delete No-Intro/Redump DAT: {0}'
'Create Parent/Clone DAT based on ROM filenames',
'Display ROMs (now {0}) ...'.format(launcher['nointro_display_mode']),
'Update ROM audit',
```

### New menus in 0.9.9

To be added.

### Separation of ROM Audit and Parent/Clone generation

Complete example of SNES ROMs including all cases.

```
Kaizo Mario World (Japan).zip                   -- EXTRA ROM
Kaizo Mario World 2 (Japan).zip                 -- EXTRA ROM
Super Mario World - Super Mario Bros. 4 (Japan) -- Clone ROM / Different basename
Super Mario World (Europe)                      -- Clone ROM
Super Mario World (Europe) (Rev 1)              -- Parent according to No-Intro DAT
Super Mario World (Japan) (En) (Arcade) [b]     -- Missing ROM / Clone ROM
Super Mario World (USA)                         -- Clone ROM
```

### Multidisc support

#### Multidisc ROM scanner implementation

 1) If the ROM scanner finds a multidisc image belonging to a set, for example
    `Final Fantasy VII (USA) (Disc 3).cue`.
 
    * The filename corresponds to the basename of the set.
 
    * The ROM basename is added to the `disks` list.

    * Asset names will have the basename of the set `Final Fantasy VII (USA)`.

```
    filename = '/home/kodi/ROMs/Final Fantasy VII (USA)'
    disks = ['Final Fantasy VII (USA) (Disc 3).cue']
```

 2) If the ROM scanner finds another image of the set then:
 
    * The basename is added to the `disks` list.
    
    * `disks` list is reordered so ROMs have consecutive order.
    
    * `filename` points to the first image of the set.
    
    * Metadata/Asset scraping is only done for the first ROM of the set.

```
    filename = '/home/kodi/ROMs/Final Fantasy VII (USA)'
    disks = ['Final Fantasy VII (USA) (Disc 1).cue', 'Final Fantasy VII (USA) (Disc 3).cue']
```

 3) ROMs not in a set have an empty `disks` list.

 4) This implementation is safe if there are missing ROMs in the set.
 
 5) Al launching time, users selects from a select dialog of the basenames of the roms of the
    set which one to launch.

### No-Intro ROM names

The official No-Intro naming convention PDF can be downloaded from [ DAT-o-matic](https://datomatic.no-intro.org/) website.

The only mandatory elements are the **Title** and the **Region**.

### Redump/Trurip/TOSEC ISO names

[No-Intro](http://www.no-intro.org/index.html)

[TOSEC naming convention](http://www.tosecdev.org/tosec-naming-convention)

| Organisation | Name example                                                  |
|--------------|---------------------------------------------------------------|
| **TOSEC**    | `Final Fantasy VII (1999)(Square)(NTSC)(US)(Disc 1 of 2).cue` |
|              | `Final Fantasy VII (1999)(Square)(NTSC)(US)(Disc 2 of 2).cue` |
| **Trurip**   | `Final Fantasy VII (EU) - (Disc 1 of 3).cue`                  |
|              | `Final Fantasy VII (EU) - (Disc 2 of 3).cue`                  |
|              | `Final Fantasy VII (EU) - (Disc 3 of 3).cue`                  |
| **Redump**   | `Final Fantasy VII (USA) (Disc 1).cue`                        |
|              | `Final Fantasy VII (USA) (Disc 2).cue`                        |
|              | `Final Fantasy VII (USA) (Disc 3).cue`                        |

### TOSEC/Trurip/Redump image formats

| TOSEC       | Redump  | Trurip          |
|-------------|---------|-----------------|
| cue,iso,wav | cue,bin | cue,img,ccd,sub |

### listitem.setInfo() overlay values and effects

`listitem.setInfo('video', {'overlay'  : 4})`

Kodi Krypton Estuary displays a small icon to the left of the listitem title that can be changed
with the overlay property value. Overlay values are defined in [GUIListItem]:

```
enum GUIIconOverlay {
    ICON_OVERLAY_NONE = 0,
    ICON_OVERLAY_RAR,
    ICON_OVERLAY_ZIP,
    ICON_OVERLAY_LOCKED,
    ICON_OVERLAY_UNWATCHED,
    ICON_OVERLAY_WATCHED,
    ICON_OVERLAY_HD
};
```

[setInfo]: http://mirrors.xbmc.org/docs/python-docs/16.x-jarvis/xbmcgui.html#ListItem-setInfo
[GUIListItem]: https://github.com/cisco-open-source/kodi/blob/master/xbmc/guilib/GUIListItem.h

### Misc stuff

Nothing at the moment.
