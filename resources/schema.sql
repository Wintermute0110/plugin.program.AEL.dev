CREATE TABLE IF NOT EXISTS metadata(
    id TEXT PRIMARY KEY, 
    year TEXT,
    genre TEXT,
    developer TEXT,
    rating INTEGER NULL,
    plot TEXT,
    assets_path TEXT,
    finished INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS assets(
    id TEXT PRIMARY KEY,
    filepath TEXT NOT NULL,
    asset_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assetspaths(
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    asset_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ael_addon(
    id TEXT PRIMARY KEY, 
    name TEXT,
    addon_id TEXT,
    version TEXT,
    addon_type TEXT,
    extra_settings TEXT
);

CREATE TABLE IF NOT EXISTS categories(
    id TEXT PRIMARY KEY, 
    name TEXT NOT NULL,
    parent_id TEXT NULL,
    metadata_id TEXT,
    default_icon TEXT DEFAULT 's_icon' NOT NULL,
    default_fanart TEXT DEFAULT 's_fanart' NOT NULL,
    default_banner TEXT DEFAULT 's_banner' NOT NULL,
    default_poster TEXT DEFAULT 's_poster' NOT NULL,
    default_clearlogo TEXT DEFAULT 's_clearlogo' NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES categories (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (metadata_id) REFERENCES metadata (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS romcollections(
    id TEXT PRIMARY KEY, 
    name TEXT NOT NULL,
    platform TEXT,
    box_size TEXT,
    parent_id TEXT NULL,
    metadata_id TEXT,
    default_icon TEXT DEFAULT 's_icon' NOT NULL,
    default_fanart TEXT DEFAULT 's_fanart' NOT NULL,
    default_banner TEXT DEFAULT 's_banner' NOT NULL,
    default_poster TEXT DEFAULT 's_poster' NOT NULL,
    default_controller TEXT DEFAULT 's_controller' NOT NULL,
    default_clearlogo TEXT DEFAULT 's_clearlogo' NOT NULL,
    roms_default_icon TEXT DEFAULT 's_boxfront' NOT NULL,
    roms_default_fanart TEXT DEFAULT 's_fanart' NOT NULL,
    roms_default_banner TEXT DEFAULT 's_banner' NOT NULL,
    roms_default_poster TEXT DEFAULT 's_flyer' NOT NULL,
    roms_default_clearlogo TEXT DEFAULT 's_clearlogo' NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES categories (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (metadata_id) REFERENCES metadata (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS romcollection_launchers(
    id TEXT PRIMARY KEY, 
    romcollection_id TEXT,
    ael_addon_id TEXT,
    settings TEXT,
    is_non_blocking INTEGER DEFAULT 1 NOT NULL,
    is_default INTEGER DEFAULT 0 NOT NULL,
    FOREIGN KEY (romcollection_id) REFERENCES romcollections (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (ael_addon_id) REFERENCES ael_addon (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS romcollection_scanners(
    id TEXT PRIMARY KEY, 
    romcollection_id TEXT,
    ael_addon_id TEXT,
    settings TEXT,
    FOREIGN KEY (romcollection_id) REFERENCES romcollections (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (ael_addon_id) REFERENCES ael_addon (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS roms(
    id TEXT PRIMARY KEY, 
    name TEXT NOT NULL,
    num_of_players INTEGER DEFAULT 1 NOT NULL,
    esrb_rating TEXT,
    nointro_status TEXT, 
    pclone_status TEXT,
    cloneof TEXT,
    platform TEXT,
    box_size TEXT,
    rom_status TEXT,
    is_favourite INTEGER DEFAULT 0 NOT NULL,
    launch_count INTEGER DEFAULT 0 NOT NULL,
    last_launch_timestamp TIMESTAMP,
    file_path TEXT,
    metadata_id TEXT,
    scanned_by_id TEXT NULL,
    FOREIGN KEY (metadata_id) REFERENCES metadata (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (scanned_by_id) REFERENCES romcollection_scanner (id) 
        ON DELETE SET NULL ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS roms_in_romcollection(
    rom_id TEXT,
    romcollection_id TEXT,
    FOREIGN KEY (rom_id) REFERENCES roms (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (romcollection_id) REFERENCES romcollections (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS roms_in_category(
    rom_id TEXT,
    category_id TEXT,
    FOREIGN KEY (rom_id) REFERENCES roms (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (category_id) REFERENCES categories (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS rom_launchers(
    id TEXT PRIMARY KEY, 
    rom_id TEXT,
    ael_addon_id TEXT,
    settings TEXT,
    is_non_blocking INTEGER DEFAULT 1 NOT NULL,
    is_default INTEGER DEFAULT 0 NOT NULL,
    FOREIGN KEY (rom_id) REFERENCES roms (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (ael_addon_id) REFERENCES ael_addon (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);
-------------------------------------------------
-- ASSETS JOIN TABLES
-------------------------------------------------
CREATE TABLE IF NOT EXISTS category_assets(
    category_id TEXT,
    asset_id TEXT,
    FOREIGN KEY (category_id) REFERENCES categories (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (asset_id) REFERENCES assets (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS romcollection_assets(
    romcollection_id TEXT,
    asset_id TEXT,
    FOREIGN KEY (romcollection_id) REFERENCES romcollections (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (asset_id) REFERENCES assets (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS romcollection_assetspaths(
    romcollection_id TEXT,
    assetspaths_id TEXT,
    FOREIGN KEY (romcollection_id) REFERENCES romcollections (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (assetspaths_id) REFERENCES assetspaths (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS rom_assets(
    rom_id TEXT,
    asset_id TEXT,
    FOREIGN KEY (rom_id) REFERENCES roms (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (asset_id) REFERENCES assets (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

-------------------------------------------------
-- VIEWS
-------------------------------------------------
CREATE VIEW IF NOT EXISTS vw_categories AS SELECT 
    c.id AS id, 
    c.parent_id AS parent_id,
    c.metadata_id,
    c.name AS m_name,
    m.year AS m_year, 
    m.genre AS m_genre,
    m.developer AS m_developer,
    m.rating AS m_rating,
    m.plot AS m_plot,
    m.finished AS finished,
    m.assets_path AS assets_path,
    c.default_icon AS default_icon,
    c.default_fanart AS default_fanart,
    c.default_banner AS default_banner,
    c.default_poster AS default_poster,
    c.default_clearlogo AS default_clearlogo,
    (SELECT COUNT(*) FROM categories AS sc WHERE sc.parent_id = c.id) AS num_categories,
    (SELECT COUNT(*) FROM romcollections AS sr WHERE sr.parent_id = c.id) AS num_collections
FROM categories AS c 
    INNER JOIN metadata AS m ON c.metadata_id = m.id;
       
CREATE VIEW IF NOT EXISTS vw_romcollections AS SELECT 
    r.id AS id, 
    r.parent_id AS parent_id,
    r.metadata_id,
    r.name AS m_name,
    m.year AS m_year, 
    m.genre AS m_genre,
    m.developer AS m_developer,
    m.rating AS m_rating,
    m.plot AS m_plot,
    m.finished AS finished,
    m.assets_path AS assets_path,
    r.platform AS platform,
    r.box_size AS box_size,
    r.default_icon AS default_icon,
    r.default_fanart AS default_fanart,
    r.default_banner AS default_banner,
    r.default_poster AS default_poster,
    r.default_controller AS default_controller,
    r.default_clearlogo AS default_clearlogo,
    r.roms_default_icon AS roms_default_icon,
    r.roms_default_fanart AS roms_default_fanart,
    r.roms_default_banner AS roms_default_banner,
    r.roms_default_poster AS roms_default_poster,
    r.roms_default_clearlogo AS roms_default_clearlogo,
    (SELECT COUNT(*) FROM roms AS rms INNER JOIN roms_in_romcollection AS rrs ON rms.id = rrs.rom_id AND rrs.romcollection_id = r.id) as num_roms
FROM romcollections AS r 
    INNER JOIN metadata AS m ON r.metadata_id = m.id;
    
CREATE VIEW IF NOT EXISTS vw_roms AS SELECT 
    r.id AS id, 
    r.metadata_id,
    r.name AS m_name,
    r.num_of_players AS m_nplayers,
    r.esrb_rating AS m_esrb,
    r.file_path AS filename,
    r.nointro_status AS nointro_status,
    r.pclone_status AS pclone_status,
    r.cloneof AS cloneof,
    r.platform AS platform,
    r.box_size AS box_size,
    r.scanned_by_id AS scanned_by_id,
    m.year AS m_year, 
    m.genre AS m_genre,
    m.developer AS m_developer,
    m.rating AS m_rating,
    m.plot AS m_plot,
    m.finished,
    r.rom_status,
    r.is_favourite,
    r.launch_count,
    r.last_launch_timestamp,
    m.assets_path AS assets_path
FROM roms AS r 
    INNER JOIN metadata AS m ON r.metadata_id = m.id;

CREATE VIEW IF NOT EXISTS vw_category_assets AS SELECT
    a.id as id,
    c.id as category_id,
    c.parent_id,
    a.filepath,
    a.asset_type
FROM assets AS a
 INNER JOIN category_assets AS ca ON a.id = ca.asset_id 
 INNER JOIN categories AS c ON ca.category_id = c.id;

CREATE VIEW IF NOT EXISTS vw_romcollection_assets AS SELECT
    a.id as id,
    r.id as romcollection_id,
    r.parent_id,
    a.filepath,
    a.asset_type
FROM assets AS a
 INNER JOIN romcollection_assets AS ra ON a.id = ra.asset_id 
 INNER JOIN romcollections AS r ON ra.romcollection_id = r.id;

CREATE VIEW IF NOT EXISTS vw_rom_assets AS SELECT
    a.id as id,
    r.id as rom_id, 
    a.filepath,
    a.asset_type
FROM assets AS a
 INNER JOIN rom_assets AS ra ON a.id = ra.asset_id 
 INNER JOIN roms AS r ON ra.rom_id = r.id;

CREATE VIEW IF NOT EXISTS vw_romcollection_launchers AS SELECT
    l.id AS id,
    l.romcollection_id,
    a.id AS associated_addon_id,
    a.name,
    a.addon_id,
    a.version,
    a.addon_type,
    a.extra_settings,
    l.settings,
    l.is_non_blocking,
    l.is_default
FROM romcollection_launchers AS l
    INNER JOIN ael_addon AS a ON l.ael_addon_id = a.id;
    
CREATE VIEW IF NOT EXISTS vw_romcollection_scanners AS SELECT
    s.id AS id,
    s.romcollection_id,
    a.id AS associated_addon_id,
    a.name,
    a.addon_id,
    a.version,
    a.addon_type,
    a.extra_settings,
    s.settings
FROM romcollection_scanners AS s
    INNER JOIN ael_addon AS a ON s.ael_addon_id = a.id;

CREATE VIEW IF NOT EXISTS vw_rom_launchers AS SELECT
    l.id AS id,
    l.rom_id,
    a.id AS associated_addon_id,
    a.name,
    a.addon_id,
    a.version,
    a.addon_type,
    l.settings,
    l.is_non_blocking,
    l.is_default
FROM rom_launchers AS l
    INNER JOIN ael_addon AS a ON l.ael_addon_id = a.id;

CREATE TABLE IF NOT EXISTS ael_version(app TEXT, version TEXT);