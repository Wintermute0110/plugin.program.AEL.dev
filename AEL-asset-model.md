# Advanced Emulator Launcher metadata and artwork data model #

 * Look in [Pydocs_setInfo] for valid setInfo() infoLabels.

 * Look in [Pydocs_setArt] for valid setArt() infoLabels.

 * Look in [Pydocs_setProperty] for valid setProperty() infoLabels.
 
 * Look in [Kodi_wiki_artwork] for supported Kodi artwork.
 
[Pydocs_setInfo]: http://mirrors.xbmc.org/docs/python-docs/16.x-jarvis/xbmcgui.html#ListItem-setInfo
[Pydocs_setArt]: http://mirrors.xbmc.org/docs/python-docs/16.x-jarvis/xbmcgui.html#ListItem-setArt
[Pydocs_setProperty]: http://mirrors.xbmc.org/docs/python-docs/16.x-jarvis/xbmcgui.html#ListItem-setProperty
[Kodi_wiki_artwork]: http://kodi.wiki/view/InfoLabels#Images_Available_in_Kodi


## Category metadata labels ##

 Metadata name | AEL name  | setInfo label | Type                 |
---------------|-----------|---------------|----------------------|
 Title         | m_name    | title         | string               |
 Genre         | m_genre   | genre         | string               |
 Plot          | m_plot    | plot          | string               |
 Rating        | m_rating  | rating        | string range 0 to 10 |
 Trailer       | s_trailer | trailer       | string               |
               |           | overlay       | int range 0 to 8     |

 * setInfo first argument is `video`. 


## Categories asset labels ##
 
 Asset name  | AEL name    | setArt label | setInfo label |
-------------|-------------|--------------|---------------|
 Thumb       | s_thumb     | thumb        |               |
 Fanart      | s_fanart    | fanart       |               |
 Banner      | s_banner    | banner       |               |
 Flyer       | s_flyer     | poster       |               |
 Trailer     | s_trailer   |              | trailer       |
 Extrafanart | extrafanart | extrafanart1 |               |
 Extrafanart | extrafanart | extrafanart2 |               |

 * `thumb` = `DefaultFolder.png` is the default for categories.

 * Trailer is an asset, however label is set with `setInfo()` instead of `setArt()`.

 * Do not set any artwork in the ListItem constructor, only with setArt().

 * `extrafanart` is a Python list.

## Launcher metadata labels ##

 Metadata name | AEL name  | setInfo | setProperty | Type                 |
---------------|-----------|---------|-------------|----------------------|
 Title         | m_name    | title   |             | string               |
 Year          | m_year    | year    |             | string               |
 Genre         | m_genre   | genre   |             | string               |
 Plot          | m_plot    | plot    |             | string               |
 Studio        | m_studio  | studio  |             | string               |
 Rating        | m_rating  | rating  |             | string range 0 to 10 |
 Trailer       | s_trailer | trailer |             | string               |
 Platform      | platform  |         | platform    | string               |
               |           | overlay |             | int range 0 to 8     |

 * `setInfo()` first argument is `video`. 
 
 * AEL platform uses an internal "official" list for the scrapers to work properly. 
   Platform is never read from NFO files. Also, AEL platform is a Launcher property, 
   not a ROM property.

 * Year and Rating are integers according to Kodi Pydocs. However, they are stored as string. 
   If Year and Rating are not set they are the empty strings, which is different from integer 0. 
   Kodi seems to handle this behaviour well.


## Launchers asset labels ##
 
 Asset name  | AEL name    | setArt label | setInfo label |
-------------|-------------|--------------|---------------|
 Thumb       | s_thumb     | thumb        |               |
 Fanart      | s_fanart    | fanart       |               |
 Banner      | s_banner    | banner       |               |
 Flyer       | s_flyer     | poster       |               |
 Trailer     | s_trailer   |              | trailer       |
 Extrafanart | extrafanart | extrafanart1 |               |
 Extrafanart | extrafanart | extrafanart2 |               |

 * `thumb` label is set to `DefaultProgram.png` or `DefaultFolder.png`.

 * Trailer is an asset, however label is set with `setInfo()` instead of `setArt()`.

 * `extrafanart` is a Python list.

## ROMs metadata labels ##

 Metadata name | AEL name  | setInfo | setProperty | Type                 |
---------------|-----------|---------|-------------|----------------------|
 Title         | m_name    | title   |             | string               |
 Year          | m_year    | year    |             | string               |
 Genre         | m_genre   | genre   |             | string               |
 Plot          | m_plot    | plot    |             | string               |
 Studio        | m_studio  | studio  |             | string               |
 Rating        | m_rating  | rating  |             | string range 0 to 10 |
 Trailer       | s_trailer | trailer |             | string               |
 Platform      | platform  |         | platform    | string               |
               |           | overlay |             | int range 0 to 8     |

 * setInfo first argument is `video`. 

 * Platform is a launcher property, not a ROM property. Also, `setProperty()` is used instead 
   of `setInfo()`.

 * Year and Rating are integers according to Kodi Pydocs. However, they are stored as string. 
   If Year and Rating are not set they are the empty strings, which is different from integer 0. 
   Kodi seems to handle this behaviour well.


## ROMs asset labels ##
 
 Asset name  | AEL name    | setArt label | setInfo label | MAME mapping for MAME views |
-------------|-------------|--------------|---------------|-----------------------------|
 Title       | s_title     | title/thumb  |               | title                       |
 Snap        | s_snap      | snap         |               | snap                        |
 Fanart      | s_fanart    | fanart       |               | fanart                      |
 Banner      | s_banner    | banner       |               | marquee                     |
 Clearlogo   | s_clearlogo | clearlogo    |               | clearlogo                   |
 Boxfront    | s_boxfront  | boxfront     |               | cabinet                     |
 Boxback     | s_boxback   | boxback      |               | cpanel                      |
 Cartridge   | s_cartridge | cartridge    |               | pcb                         |
 Flyer       | s_flyer     | poster       |               | flyer                       |
 Map         | s_map       | map          |               |                             |
 Manual      | s_manual    |              |               | manual                      |
 Trailer     | s_trailer   |              | trailer       | trailer                     |
 Extrafanart | extrafanart | extrafanart1 |               | extrafanart                 |
 Extrafanart | extrafanart | extrafanart2 |               | extrafanart                 |
 
 * `thumb` label is set to `DefaultProgram.png`.

 * For Confluence/Estuary, user will be able to configure what artwork will be set as `thumb`
   and `fanart`. 

 * Trailer is an asset, however label is set with setInfo() instead of setArt()

 * `extrafanart` is a Python list.

## Launchers/Categories artwork supported by plugins ##

 Plugin | Thumb | Fanart | Banner | Poster | Trailer |
--------|-------|--------|--------|--------|---------|
AL      |  YES  |  YES   |  NO    |  NO    | NO      |
AEL     |  YES  |  YES   |  YES   |  YES   | YES     |
HL      |  YES  |  YES   |  YES   |  YES   | ???     |
IARL    |  ???  |  ???   |  ???   |  ???   | ???     |


## Console ROMs asset availability ##

  Artwork site    | Title | Snap | Fanart | Banner | Boxfront | Boxback | Cartridge | Flyer | Map | Manual | Trailer |
------------------|-------|------|--------|--------|----------|---------|-----------|-------|-----|--------|---------|
[EmuMovies]       |  YES  | YES  |  NO    |   NO   |   YES    |   YES   |    YES    |  YES  | YES |  YES   |   YES   |
[HyperSpin Media] |  NO   | NO   |  <1>   |   YES  |   YES    |   NO    |    YES    |  <1>  | <1> |  NO    |   NO    |
[No-Intro]        |  YES  | NO   |  NO    |   NO   |   YES    |   YES   |    YES    |  NO   | NO  |  YES   |   NO    |
[Retroarch]       |  YES  | YES  |  NO    |   NO   |   YES    |   NO    |    NO     |  NO   | NO  |  NO    |   NO    |
[TheGamesDB]      |  <2>  | <2>  |  YES   |   YES  |   YES    |   YES   |    NO     |  NO   | NO  |  NO    | YouTube |
[GameFAQs]        |  <2>  | <2>  |  NO    |   NO   |   YES    |   YES   |    NO     |  NO   | NO  |  NO    |   NO    |
[MobyGames]       |  <2>  | <2>  |  NO    |   NO   |   YES    |   YES   |    YES    |  NO   | NO  |  NO    |   NO    |
[GiantBomb]       |  <3>  | <3>  |  <3>   |   <3>  |   YES    |   <3>   |    <3>    |  NO   | NO  |  NO    | YouTube |

  * `Banner` is a horizontal image with name of ROM/system. It is called `Wheel` in Hyperspin and `Logo` in HL.
     
     Also, HL has both `Logo`/`Wheel` and `Banner` in separated directories. I do not know the difference between them. 
     
     No idea about what is HL `Clearart`.

  * `Flyer` is a vertical image. It is called `Poster` in HL.

  * EmuMovies/HyperSpin Media provide 2D and 3D version of `Boxfront` and `Cartridges`.

  * <1> In the HyperSpin forum you can find per-game/per-system themes that have `Fanart` and `Banner`. However, in 
    many cases assets are inside SWF files and difficult to use outside HyperSpin.

  * <2> TheGamesDB/GameFAQs/MobyGames do not differentiate between `Title`/`Snap`. They just have screenshots.

  * GameFAQs have gamebox `Spine`, which can be considered a kind of `Banner`.

  * <3> GiantBomb has quite a lot of artwork. However, everything is mixed (`Title`, `Snaps`, `Fanart`, all showing
    on the same page) and makes it difficult to scrape. `Boxfront` is easy to scrape from GiantBomb.

  * RetroPie and Emulation Station users have nice No-Intro artwork collections including `Title`, `Snap` and `Boxfront`.

[EmuMovies]: http://emumovies.com/
[HyperSpin Media]: http://www.hyperspin-fe.com/files/category/2-hyperspin-media/
[No-Intro]: http://no-intro.dlgsoftware.net
[Retroarch]: https://github.com/libretro/libretro-thumbnails/
[TheGamesDB]: http://thegamesdb.net/
[GameFAQs]: http://www.gamefaqs.com/
[MobyGames]: http://www.mobygames.com/
[GiantBomb]: http://www.giantbomb.com/


## AEL artwork policy ##

 * One artwork directory will be required for every ROM launcher.
   User will be asked for one Artwork directory and AEL will create subdirectories inside 
   automatically.

 * To deal with Confluence (default) skin, user will be able to choose which artwork to 
   display as thumb/fanart. For example: thumb -> Boxfront, fanart -> Fanart.

 * No more separated thumb/fanart scrapers. Thumb/fanart scrapers will be unified into artwork 
   scrapers. Artwork scrapers will download all possible Artwork depending on site availabililty.

### ROM artwork storage ###

 1. Asset directory may be the same as the ROMs directory.

```
ROMs directory         ~/ROMs/SNES/Super Mario World (Europe).zip
Artwork directory      ~/Artwork/SNES/
Created automatically  ~/Artwork/SNES/titles/Super Mario World (Europe).png
                       ~/Artwork/SNES/snaps/Super Mario World (Europe).png
                       ~/Artwork/SNES/fanarts/Super Mario World (Europe).png
                       ~/Artwork/SNES/banners/Super Mario World (Europe).png
                       ~/Artwork/SNES/boxfronts/Super Mario World (Europe).png
                       ~/Artwork/SNES/boxbacks/Super Mario World (Europe).png
                       ~/Artwork/SNES/cartridges/Super Mario World (Europe).png
                       ~/Artwork/SNES/flyers/Super Mario World (Europe).png
                       ~/Artwork/SNES/maps/Super Mario World (Europe).png
                       ~/Artwork/SNES/manuals/Super Mario World (Europe).pdf
                       ~/Artwork/SNES/trailers/Super Mario World (Europe).mpeg
                       ~/Artwork/SNES/extrafanart/Super Mario World (Europe)/fanart1.png
                       ~/Artwork/SNES/extrafanart/Super Mario World (Europe)/fanart2.png
                       ~/Artwork/SNES/extrafanart/Super Mario World (Europe)/fanart3.png
```

### Launcher/Category artwork storage ###

 1. Category name `SEGA`. Each category will have a subdirectory with same name to store
    extrafanart.

 2. Launcher name `SNES (Retroarch bsnes balanced)`. Each launcher will have a subdirectory to
    store extrafanart.

```
Artwork directory  ADDON_DATA_DIR/asset-categories/
                   ADDON_DATA_DIR/asset-categories/SEGA/fanart1.png
                   ADDON_DATA_DIR/asset-categories/SEGA/fanart2.png
                   ADDON_DATA_DIR/asset-categories/SEGA/fanart3.png

Artwork directory  ADDON_DATA_DIR/asset-launchers/
                   ADDON_DATA_DIR/asset-launchers/SNES (Retroarch bsnes balanced)/fanart1.png
                   ADDON_DATA_DIR/asset-launchers/SNES (Retroarch bsnes balanced)/fanart2.png
                   ADDON_DATA_DIR/asset-launchers/SNES (Retroarch bsnes balanced)/fanart3.png
```

## Importing AL stuff into AEL ##

 * AL thumb will be imported as title.

 * AL fanart will be imported as fanart.

 * User will have to reorganise artwork directories to take full advantage of AEL
   capabilities after importing AL `launchers.xml`.
