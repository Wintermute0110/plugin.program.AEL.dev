## AKL technical notes ##

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

Context menu **Edit Launcher**, submenu **Audit ROMs / Launcher view mode ...**:
```
'Change launcher display mode (now {0}) ...'.format(display_mode_str),
'Add No-Intro/Redump XML DAT ...' OR 'Delete No-Intro/Redump DAT: {0}'
'Create Parent/Clone DAT based on ROM filenames',
'Display ROMs (now {0}) ...'.format(launcher['nointro_display_mode']),
'Update ROM audit',
```

Display modes: LAUNCHER_DMODE_FLAT, LAUNCHER_DMODE_PCLONE, LAUNCHER_DMODE_1G1R.
PCLONE and 1G1R are the same, the difference is that in 1G1R the ROM Context 
Menu **Show clones** is displayed and Parents are launcher automatically. AML now has
FLAT and 1G1R modes only.

Display filters: NOINTRO_DMODE_ALL, NOINTRO_DMODE_HAVE, NOINTRO_DMODE_HAVE_UNK,
NOINTRO_DMODE_HAVE_MISS, NOINTRO_DMODE_MISS, NOINTRO_DMODE_MISS_UNK, NOINTRO_DMODE_UNK.

Current fields in Launchers database:
```
    'nointro_xml_file' : '',
    'nointro_display_mode' : NOINTRO_DMODE_ALL,
    'launcher_display_mode' : LAUNCHER_DMODE_FLAT,
```

Current fields in ROMs database:
```
    'disks' : [],
    'nointro_status' : 'Miss',
    'pclone_status' : 'Parent',
    'cloneof' : '',
```

### Menus in future AEL releases

Context menu **Edit Launcher**, submenu **Manage ROMs ...**:
```
'Choose ROMs default artwork ...',
'Manage ROMs asset directories ...',
'Rescan ROMs local artwork',
'Scrape ROMs artwork',
'Import ROMs metadata from NFO files',
'Export ROMs metadata to NFO files',
'Delete ROMs NFO files',
'Delete ROMs from launcher',
```

Context menu **Edit Launcher**, submenu **Audit ROMs / Launcher view mode ...**:
```
'Launcher display mode (now {0}) ...'.format(display_mode_str),
'Audit display filter (now {0}) ...'.format(launcher['display_filter']),
'Audit launcher ROMs',
'Undo ROM audit (remove missing ROMs)',
'Add custom XML DAT ...' OR 'Delete custom XML DAT',
```

Launcher display modes: LAUNCHER_DMODE_FLAT (default), LAUNCHER_DMODE_PCLONE.

Launcher audit status: AUDIT_STATE_ON, AUDIT_STATE_OFF (default).

Launcher audit display filter: AUDIT_FILTER_ALL (default), AUDIT_FILTER_HAVE, AUDIT_FILTER_HAVE_UNK,
AUDIT_FILTER_HAVE_MISS, AUDIT_FILTER_MISS, AUDIT_FILTER_MISS_UNK, AUDIT_FILTER_UNK. For now,
always display Extra ROMs.

### Future AEL guidelines

 * The Parent/Clone information is ALWAYS computed, regardles of the audit status, whenever
   the launcher ROMs change.

 * The ROM region information is ALWAYS computed, regardless of the audit status, whenever
   the launcher ROMs change.

 * The Parent of the Parent/Clone group is chosen according to the preferred Region and
   Language. User selects the preferred Region and Language with global settings. These
   global settings may be overriden with Launcher-specific settings.

 * The Launcher display mode is always available.

 * The Launcher audit display filter is available if and only if the audit status is ON.

 * The ROM Audit is very easy to do. The difficult part is to make the Parent/Clone groups
   and choosing the parent ROM.

Future fields in Launchers database:
```
    'audit_state' : AUDIT_STATE_ON or AUDIT_STATE_OFF,  Reports if audit is ON or not
    'audit_auto_dat_file' : '',                         Filled in automatically
    'audit_custom_dat_file' : '',                       Previous nointro_xml_file
    'audit_display_mode' : AUDIT_DMODE_ALL,             Previous nointro_display_mode
    'launcher_display_mode' : LAUNCHER_DMODE_FLAT,
```

Future ROMs database fields:
```
    'm_cloneof' : '',              Override the ROM parent (read-only field)
    'm_region' : '',               Override the ROM regions (read-only field)
    'm_language' : '',             Override the ROM languages (read-only field)
    'disks' : [],
    'i_audit_status' : 'Have',     Determined by the ROM Audit exclusively, former nointro_status
    'i_pclone_status' : 'Parent',  Based on i_cloneof, used to set skin properties, former pclone_status
    'i_cloneof' : ROMID,           ROM ID of the final parent ROM, former cloneof
    'i_extra_ROM' : bool,          If True ROM is an extra ROM, false otherwise
    'i_order' : int,               Position of the ROM in the Parent/Clone group
    'i_regions' : ['', ''],        Same as m_region
    'i_languages' : ['', ''],      Same as m_language
    'i_tags' : ['', ''],           Always extracted from filename
                                   Other unrecognised tags not region or language
```

### Computation of the Parent/Clone ROMs

 1. First Parent/Clone groups are computed:
 
    1. If a No-Intro XML DAT is available it will be used.
       For Have and Missing ROMs take `i_cloneof` from the DAT.
       For Have and Missing ROMs extract `i_regions` and `i_languages` from filename.

    2. The Offline Scraper database will be used next, or first if the DAT is not found.
       For found ROMs `i_cloneof`, `i_regions` and `i_languages` will be taken from the database.

    3. For Unknown ROMs, the ROM basename will be used to compute `i_cloneof` and `i_regions`
       and `i_languages` extracted from the filename.

    4. The fiels `m_cloneof`, `m_region` and `m_language` in the ROM metadata override any of 
       the `i_*` fields.

 2. With the fields `i_cloneof`, `i_regions`, `i_languages` and `i_tags` the order in the
    Parent/Clone group is calculated:

    1. User chooses the primary and secondary ROM regions.

    2. User chooses the primary and secondary ROM languages.

    3. Other tags like (Rev X) are used to choose the preferred Parent in the set.
       AEL needs to have an histogram of all the No-Intro and Redump tags and
       use the information when building the Parent/Clone groups according to the settings.

    4. PClone groups are reordered according to the user settings. The Parent of the group will
       be the first ROM in the set.

    5. `i_cloneof` is updated to reflect the new Parent of each set.

    6. `i_order` is updated to reflect the ROM positions in the set.

    6. The file `roms_<Launcher_name>_PClone_index.json` is created.
       This file is used when rendering the PClone group list when the user select the
       context menu "Show clone ROMs".

    7. To render the Parent ROMs in PCLONE launcher display mode open the ROM JSON database
       and render only the Parent ROMs.

A report of the PClone group generation should be generated so the user can check for errors
or unwanted configurations.

**Potential problems**

 * What if the parent of a PClone group is a Missing ROM?

   1. If all ROMs in the PClone group are Missing choose the Parent ROM as usual.

   2. Otherwise, short the ROMs in the group according to the user preferences and choose
      the first Have or Unknown ROM as Parent.

 * What if the user wants to force a specific Parent? How to do this?

   1. The Parent can be changed with the ROM Region and ROM Language settings.

   2. Maybe having a read-only setting bool `m_forceparent`???
      This can create a conflict in the settings that must be solved.

 * What if there is a conflic when creating the Parent/Clone groups? For example, the No-Intro
   DAT says the Parent of a ROM is A and the user sets the parent of the ROM to B.

   1. A report of the Parent/Clone groups must be created so the user knows what happened
      and fix any error or misconfiguration. This report can be read using the Launcher
      context menu.

### Computation of the ROM Audit

 1. Only ROMs in the main ROM directory are audited.

 2. All ROMs in the extra ROM directory are Extra ROMs. Extra ROMs can be ROM hacks, etc., which
    are not in the official DATs but may be included in the Offline Scraper database.

 3. The XML DAT for No-Intro ROMs is chosen automatically from the No-Intro DAT directory 
    as a function of the platform launcher.

 4. The XML DAT for Redump ROMs is chosen automatically from the Redump DAT directory 
    as a function of the platform launcher.

 5. Users can manually configure a custom XML DAT file for every launcher.
    In this case, the automatic DAT selection is ignored.

 6. The Offline Scraper database can be used for the ROM Audit instead of an external DAT XML file.

**Potential problems**

 1. How to audit multidisc ROMs???

    1. For now, do not allow multidisc ROMs and ROM Audit for the same launcher at the same time.

### Examples of ROM Audit and Parent/Clone generation

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

To be written...

### Multidisc support

**The current implementation of multidisc ROMs is deficient and must be improved.**

#### Multidisc ROM scanner implementation

 1. If the ROM scanner finds a multidisc image belonging to a set, for example
    `Final Fantasy VII (USA) (Disc 3).cue`.
 
    * The filename corresponds to the basename of the set.
 
    * The ROM basename is added to the `disks` list.

    * Asset names will have the basename of the set `Final Fantasy VII (USA)`.

    ```
    filename = '/home/kodi/ROMs/Final Fantasy VII (USA)'
    disks = ['Final Fantasy VII (USA) (Disc 3).cue']
    ```

 2. If the ROM scanner finds another image of the set then:

    * The basename is added to the `disks` list.
    
    * `disks` list is reordered so ROMs have consecutive order.
    
    * `filename` points to the first image of the set.
    
    * Metadata/Asset scraping is only done for the first ROM of the set.

    ```
    filename = '/home/kodi/ROMs/Final Fantasy VII (USA)'
    disks = ['Final Fantasy VII (USA) (Disc 1).cue', 'Final Fantasy VII (USA) (Disc 3).cue']
    ```

 3. ROMs not in a set have an empty `disks` list.

 4. This implementation is safe if there are missing ROMs in the set.

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

### ROM Collections

Way of storing ROM Collections when saving the collection:
```
Sonic the Hedgehog.json
Sonic the Hedgehog_banner.png
Sonic the Hedgehog_fanart.png
Sonic the Hedgehog_icon.png
Sonic the Hedgehog_poster.png
Sonic the Hedgehog/Sonic The Hedgehog (USA, Europe)_fanart.png          megadrive
Sonic the Hedgehog/Sonic The Hedgehog (USA, Europe)_title.png
Sonic the Hedgehog/Sonic The Hedgehog (USA, Europe)_snap.png
Sonic the Hedgehog/Sonic The Hedgehog (USA, Europe, Brazil)_fanart.png  sms
Sonic the Hedgehog/Sonic The Hedgehog (USA, Europe, Brazil)_title.png
Sonic the Hedgehog/Sonic The Hedgehog (USA, Europe, Brazil)_snap.png
```

There could be more than 1 image that will be shown to the user when importing the
ROM Collection JSON file. The user then chooses what image to import.
This applies to the artwork of the collection itself and to the Collection ROMs:
```
Sonic the Hedgehog.json
Sonic the Hedgehog_banner.png
Sonic the Hedgehog_banner1.png
Sonic the Hedgehog_banner2.png
Sonic the Hedgehog_fanart.png
Sonic the Hedgehog_fanart1.png
Sonic the Hedgehog_fanart2.png
Sonic the Hedgehog_fanart3.png
```

If two ROMs in different platforms have the same filename then a platform compact name
suffix is added to resolve the filename collision:
```
Sonic the Hedgehog/Sonic The Hedgehog (USA, Europe)_fanart.png      megadrive
Sonic the Hedgehog/Sonic The Hedgehog (USA, Europe)_title.png
Sonic the Hedgehog/Sonic The Hedgehog (USA, Europe)_snap.png
Sonic the Hedgehog/Sonic The Hedgehog (USA, Europe)_sms_fanart.png  sms
Sonic the Hedgehog/Sonic The Hedgehog (USA, Europe)_sms_title.png
Sonic the Hedgehog/Sonic The Hedgehog (USA, Europe)_sms_snap.png
```

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
