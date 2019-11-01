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

Current fields in database:
```
"cloneof":"",
"disks":[],
"nointro_status":"Miss",
"pclone_status":"Parent",
```

### New menus in 0.9.9

Display modes: LAUNCHER_DMODE_FLAT (default), LAUNCHER_DMODE_PCLONE, LAUNCHER_DMODE_1G1R.

Audit status: AUDIT_STATUS_ON, AUDIT_STATUS_OFF (default).

Display filters: AUDIT_FILTER_ALL (default), AUDIT_FILTER_HAVE, AUDIT_FILTER_HAVE_UNK,
AUDIT_FILTER_HAVE_MISS, AUDIT_FILTER_MISS, AUDIT_FILTER_MISS_UNK, AUDIT_FILTER_UNK.

Context menu **Edit Launcher**, submenu **Audit ROMs / Launcher view mode ...**:
```
'Change launcher display mode (now {0}) ...'.format(display_mode_str),

'Audit launcher with No-Intro/Redump XML DAT',
'Undo ROM audit (remove missing ROMs)',
'Audit display filter (now {0}) ...'.format(launcher['display_filter']),
'Add custom XML DAT ...' OR 'Delete custom XML DAT',
```

 * The Parent/Clone information is ALWAYS computed, regardles of the audit status, whenever
   the launcher ROMs change.

 * The ROM region information is ALWAYS computed, regardless of the audit status, whenever
   the launcher ROMs change.

 * Audit filters can be used if and only if the audit status is ON.

 * The ROM Audit is very easy to do. The difficult part is to make the Parent/Clone groups
   and choosing the parent ROM.

New database fields:
```
"i_cloneof" : ROMID,        -- Same as m_parent but uses ROM ID
"i_audit_status" : "Have",  -- Determined by the ROM Audit exclusively
"i_regions" : ['', ''],     -- Same as m_region
"i_languages" : ['', ''],   -- Same as m_language
"i_tags" : ['', ''],        -- Always extracted from filename
"m_parent" : '',            -- Override the ROM parent (read-only)
"m_region" : '',            -- Override the ROM regions (read-only)
"m_language" : '',          -- Override the ROM languages (read-only)
```

### Computation of the Parent/Clone ROMs

A report of the PClone group generation shoudl be generated so the user can check for errors
or unwanted configurations.

 1. Parent/Clone groups are computed:
 
    1. If a No-Intro XML DAT is available it will be used.
       For Have and Missing ROMs take `m_parent` from the DAT.
       For Have and MIssing ROMs extrace `m_region` and `m_language` from filename.

    2. The Offline Scraper database will be used.
       For found ROMs `m_parent`, `m_region` and `m_language` will be used.

    3. For Unknown ROMs, the ROM basename will be used to compute `m_parent` and `m_region`
       and `m_language` extracted from the filename.

    4. The fiels `m_parent`, `m_region` and `m_language` in the ROM metadata override any
       of the above.

 2. With `m_parent`, `m_region` and `m_language` the fields `i_cloneof`, `i_regions`,
    `i_languages` and `i_tages` are computed and used to set the order in the PClone group.

    1. User chooses the primary and secondary ROM regions.

    2. User chooses the primary and secondary ROM languages.

    3. Other tags like (Rev) are used to choose the preferred ROM.

    4. PClone groups are reordered according to the user preferences.

    5. `i_cloneof` is updated to reflect the new parent.

    6. The file roms_<Launcher_name>_PClone_index.json is create. This file is used when
       rendering the PClone group window.

    7. To render the Parent ROMs in PCLONE mode open the ROMs database and render only the
       Parents.

**Potential problems**

 * What if the parent of a PClone group is a Missing ROM?

   1. If all ROMs in the PClone group are Unknown choose the Parent as usual.

   2. Otherwise, short the ROMs in the group accouring to the user preferences and choose
      the first Have or Unknown ROM as Parent.

 * What if the user wants to force an specific Parent? How to do this?

   1. The Parent can be changed with the ROM Region and ROM Language settings.

   2. Maybe having a read-only setting bool `m_forceparent`???
      This can create a conflict in the settings that must be solved.

### Computation of the ROM Audit

 1. Only ROMs in the main ROM directory are audited.

 2. All ROMs in the extra ROM directory are Extra ROMs.

 3. The XML DAT for No-Intro ROMs is chosen automatically from the No-Intro DAT directory 
    as a function of the platform launcher.

 4. The XML DAT for Redump ROMs is chosen automatically from the Redump DAT directory 
    as a function of the platform launcher.

 5. Users can manually configure a custom XML DAT file for every launcher.

**Potential problems**

 1. How to audit multidisc ROMs???

    1. For now, do not allow multidisc ROMs and ROM Audit for the same launcher.

### Separation of ROM Audit and Parent/Clone generation

Complete example of SNES ROMs including all cases except multidisc ROMs.

```
Kaizo Mario World (Japan)                       -- EXTRA ROM / Different basename from any ROM in set
Kaizo Mario World 2 (Japan)                     -- EXTRA ROM / Different basename from any ROM in set
Super Mario World - Super Mario Bros. 4 (Japan) -- CLONE ROM / Different basename from any ROM in set
Super Mario World (Europe)                      -- CLONE ROM
Super Mario World (Europe) (Rev 1)              -- PARENT ROM / According to No-Intro DAT
Super Mario World (Japan) (En) (Arcade) [b]     -- MISSING ROM / CLONE ROM
Super Mario World (USA)                         -- CLONE ROM
```

### Multidisc support

**The current implementation of multidisc ROMs is deficient and must be improved.**

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
