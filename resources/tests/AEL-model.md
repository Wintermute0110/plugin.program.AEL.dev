* Advanced Emulator Launcher metadata and artwork data model *

** Console ROMs Metadata **

 Metada source | Title | Year | Genre | Studio | Plot | Platform |
---------------|-------|------|-------|--------|------|----------|


** MAME/Arcade Metadata **


 Metada source | Title | Year | Genre | Studio | Plot | Manual | Status | Input | Players | Coins | Orientation | 
---------------|-------|------|-------|--------|------|--------|--------|-------|---------|-------|-------------|
 MAME XML      |


** Software Lists Metadata **


** Console ROMs Artwork **

 Artwork site  | Title | Snap | Fanart | Banner | Boxfront | Boxback | Cartridge | Flyer | Map | Manual | Video trailer |
---------------|-------|------|--------|--------|----------|---------|-----------|-------|-----|--------|---------------|
 EmuMovies     |  YES  | YES  |   NO   |   NO   |   YES    |   YES   |    YES    |  YES  | YES |  YES   |      YES      |
 No-Intro      |
 Retroarch     |
 TheGamesDB    |
 GameFAQs      |
 MobyGames     | 
 GiantBomb     |


** MAME/Arcade Artwork **

 Artwork site  |  Title | Snap | Fanart | Banner | Boss | GameOver | Score | Cabinet | Marquee | PCB | CPO | Flyer | Video trailer |
---------------|--------|------|--------|--------|------|----------|-------|---------|---------|-----|-----|-------|---------------|
 Pleasuredome  |
 ProgrettoEmma |
 ArcadeItalia  |


** Software Lists Artwork **

 
** AEL artwork policy **

 * One artwork directory will be required for every ROM launcher.
 * User will be asked for one Artwork directory. AEL will create subdirectories inside.
 * To deal with Confluence (default) skin, user will be able to choose which artwork to 
   display as thumb/fanart. For example: 
   thumb  -> Boxfront
   fanart -> Fanart
 * No more separated thumb/fanart scrapers. Thumb/fanart scrapers will be unified into artwork scrapers.
   Artwork scrapers will download all possible Artwork depending on site availabililty.
 * Categories and Launchers Artwork will consist of thumb/fanart/banner.
   
Example 1:

 1. Launcher name `SNES (Retroarch bsnes balanced)`
 2. Launcher and artwork in SEPARATED DIRECTORIES
 3. **This is the recommended layout**.

```
ROMs directory           ~/ROMs/SNES/Super Mario World (Europe).zip
Artwork directory        ~/Artwork/SNES/
created automatically -> ~/Artwork/SNES/titles/Super Mario World (Europe).png
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
```

Example 2:

 1. Launcher name `SNES (Retroarch bsnes balanced)`
 2. Launcher and artwork in SAME directory
 3. **This layout is not recommended** (although some people seems to like it).

```
ROMs directory           ~/ROMs/SNES/Super Mario World (Europe).zip
                         ~/ROMs/SNES/Super Mario World (Europe)_title.png
                         ~/ROMs/SNES/Super Mario World (Europe)_snap.png
                         ~/ROMs/SNES/Super Mario World (Europe)_fanart.png
                         ~/ROMs/SNES/Super Mario World (Europe)_banner.png
                         ~/ROMs/SNES/Super Mario World (Europe)_boxfront.png
                         ~/ROMs/SNES/Super Mario World (Europe)_boxback.png
                         ~/ROMs/SNES/Super Mario World (Europe)_cartridge.png
                         ~/ROMs/SNES/Super Mario World (Europe)_flyer.png
                         ~/ROMs/SNES/Super Mario World (Europe)_map.png
                         ~/ROMs/SNES/Super Mario World (Europe)_manual.pdf
                         ~/ROMs/SNES/Super Mario World (Europe)_trailer.mpeg
```

** AL import into AEL **

 * AL thumb will be imported as title.
 * AL fanart will be imported as fanart.
 * User will have to reorganise artwork directories to take full advantage of AEL
   capabilities after importing AL launchers.xml.
