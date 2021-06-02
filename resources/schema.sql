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
    asset_type INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS assetspaths(
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    asset_type INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ael_addon(
    id TEXT PRIMARY KEY, 
    addon_id TEXT,
    version TEXT,
    is_launcher INTEGER DEFAULT 0 NOT NULL,
    launcher_uri TEXT
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

CREATE TABLE IF NOT EXISTS romsets(
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
    FOREIGN KEY (parent_id) REFERENCES categories (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (metadata_id) REFERENCES metadata (id) 
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
    fav_status TEXT,
    is_favourite INTEGER DEFAULT 0 NOT NULL,
    launch_count INTEGER DEFAULT 0 NOT NULL,
    last_launch_timestamp TIMESTAMP,
    file_path TEXT,
    romset_id TEXT NULL,
    category_id TEXT NULL,
    metadata_id TEXT,
    FOREIGN KEY (romset_id) REFERENCES romset (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (category_id) REFERENCES categories (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (metadata_id) REFERENCES metadata (id) 
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

CREATE TABLE IF NOT EXISTS romset_assets(
    romset_id TEXT,
    asset_id TEXT,
    FOREIGN KEY (romset_id) REFERENCES romsets (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (asset_id) REFERENCES assets (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS romset_assetspaths(
    romset_id TEXT,
    assetspaths_id TEXT,
    FOREIGN KEY (romset_id) REFERENCES romsets (id) 
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
-- LAUNCHERS
-------------------------------------------------
CREATE TABLE IF NOT EXISTS romset_launchers(
    romset_id TEXT,
    ael_addon_id TEXT,
    args TEXT,
    is_default INTEGER DEFAULT 0 NOT NULL,
    FOREIGN KEY (romset_id) REFERENCES romsets (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (ael_addon_id) REFERENCES ael_addon (id) 
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
    a_icon.filepath AS s_icon, 
    a_fanart.filepath AS s_fanart,
    a_clearlogo.filepath AS s_clearlogo,
    a_poster.filepath AS s_poster,
    a_banner.filepath AS s_banner,
    a_trailer.filepath AS s_trailer,
    c.default_icon AS default_icon,
    c.default_fanart AS default_fanart,
    c.default_banner AS default_banner,
    c.default_poster AS default_poster,
    c.default_clearlogo AS default_clearlogo,
    (SELECT COUNT(*) FROM categories AS sc WHERE sc.parent_id = c.id) AS num_categories,
    (SELECT COUNT(*) FROM romsets AS sr WHERE sr.parent_id = c.id) AS num_romsets
FROM categories AS c 
    INNER JOIN metadata AS m ON c.metadata_id = m.id
    LEFT JOIN category_assets AS ca_icon ON ca_icon.category_id = c.id
        INNER JOIN assets AS a_icon ON a_icon.id = ca_icon.asset_id AND a_icon.asset_type = 'icon'
    LEFT JOIN category_assets AS ca_fanart ON ca_fanart.category_id = c.id
        INNER JOIN assets AS a_fanart ON a_fanart.id = ca_fanart.asset_id AND a_fanart.asset_type = 'fanart'
    LEFT JOIN category_assets AS ca_clearlogo ON ca_clearlogo.category_id = c.id
        INNER JOIN assets AS a_clearlogo ON a_clearlogo.id = ca_clearlogo.asset_id AND a_clearlogo.asset_type = 'clearlogo'
    LEFT JOIN category_assets AS ca_poster ON ca_poster.category_id = c.id
        INNER JOIN assets AS a_poster ON a_poster.id = ca_poster.asset_id AND a_poster.asset_type = 'poster'
    LEFT JOIN category_assets AS ca_banner ON ca_banner.category_id = c.id
        INNER JOIN assets AS a_banner ON a_banner.id = ca_banner.asset_id AND a_banner.asset_type = 'banner'
    LEFT JOIN category_assets AS ca_trailer ON ca_trailer.category_id = c.id
        INNER JOIN assets AS a_trailer ON a_trailer.id = ca_trailer.asset_id AND a_trailer.asset_type = 'trailer';
       
CREATE VIEW IF NOT EXISTS vw_romsets AS SELECT 
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
    a_icon.filepath AS s_icon, 
    a_fanart.filepath AS s_fanart,
    a_clearlogo.filepath AS s_clearlogo,
    a_poster.filepath AS s_poster,
    a_banner.filepath AS s_banner,
    a_controller.filepath As s_controller,
    a_trailer.filepath AS s_trailer,
    r.default_icon AS default_icon,
    r.default_fanart AS default_fanart,
    r.default_banner AS default_banner,
    r.default_poster AS default_poster,
    r.default_controller AS default_controller,
    r.default_clearlogo AS default_clearlogo,
    (SELECT COUNT(*) FROM roms AS rms WHERE rms.romset_id = r.id) as num_roms
FROM romsets AS r 
    INNER JOIN metadata AS m ON r.metadata_id = m.id
    LEFT JOIN romset_assets AS rsa_icon ON rsa_icon.romset_id = r.id
        INNER JOIN assets AS a_icon ON a_icon.id = rsa_icon.asset_id AND a_icon.asset_type = 'icon'
    LEFT JOIN romset_assets AS rsa_fanart ON rsa_fanart.romset_id = r.id
        INNER JOIN assets AS a_fanart ON a_fanart.id = rsa_fanart.asset_id AND a_fanart.asset_type = 'fanart'
    LEFT JOIN romset_assets AS rsa_clearlogo ON rsa_clearlogo.romset_id = r.id
        INNER JOIN assets AS a_clearlogo ON a_clearlogo.id = rsa_clearlogo.asset_id AND a_clearlogo.asset_type = 'clearlogo'
    LEFT JOIN romset_assets AS rsa_poster ON rsa_poster.romset_id = r.id
        INNER JOIN assets AS a_poster ON a_poster.id = rsa_poster.asset_id AND a_poster.asset_type = 'poster'
    LEFT JOIN romset_assets AS rsa_banner ON rsa_banner.romset_id = r.id
        INNER JOIN assets AS a_banner ON a_banner.id = rsa_banner.asset_id AND a_banner.asset_type = 'banner'
    LEFT JOIN romset_assets AS rsa_controller ON rsa_controller.romset_id = r.id
        INNER JOIN assets AS a_controller ON a_controller.id = rsa_controller.asset_id AND a_controller.asset_type = 'controller'
    LEFT JOIN romset_assets AS rsa_trailer ON rsa_trailer.romset_id = r.id
        INNER JOIN assets AS a_trailer ON a_trailer.id = rsa_trailer.asset_id AND a_trailer.asset_type = 'trailer';

CREATE VIEW IF NOT EXISTS vw_rom_launchers AS SELECT 
    r.*,
    a.*
FROM romset_launchers AS r
    INNER JOIN ael_addon AS a ON r.ael_addon_id = a.id;

CREATE VIEW IF NOT EXISTS vw_roms AS SELECT 
    r.id AS id, 
    r.romset_id AS romset_id,
    r.category_id AS category_id,
    r.metadata_id,
    r.name AS m_name,
    r.num_of_players AS m_nplayers,
    r.esrb_rating AS m_esrb,
    r.file_path AS filename,
    r.nointro_status AS nointro_status,
    r.pclone_status AS pclone_status,
    r.cloneof AS cloneof,
    m.year AS m_year, 
    m.genre AS m_genre,
    m.developer AS m_developer,
    m.rating AS m_rating,
    m.plot AS m_plot,
    m.finished AS finished,
    r.fav_status AS fav_status,
    r.launch_count AS launch_count,
    m.assets_path AS assets_path,
    rs.platform AS platform,
    rs.box_size AS box_size,
    --a_icon.filepath AS s_icon, 
    a_fanart.filepath AS s_fanart,
    a_clearlogo.filepath AS s_clearlogo,
    --a_poster.filepath AS s_poster,
    a_banner.filepath AS s_banner,
    a_boxfront.filepath AS s_boxfront, 
    a_boxback.filepath AS s_boxback, 
    a_3dbox.filepath AS s_3dbox,
    a_flyer.filepath AS s_flyer,
    a_snap.filepath AS s_snap,
    a_cartridge.filepath AS s_cartridge,
    a_manual.filepath AS s_manual,
    a_map.filepath AS s_map,
    a_title.filepath AS s_title,
    a_trailer.filepath AS s_trailer
FROM roms AS r 
    INNER JOIN metadata AS m ON r.metadata_id = m.id
    LEFT JOIN romsets AS rs ON r.romset_id = rs.id
    -- LEFT JOIN rom_assets AS ra_icon ON ra_icon.rom_id = r.id
    --     INNER JOIN assets AS a_icon ON a_icon.id = ra_icon.asset_id AND a_icon.asset_type = 'icon'
    LEFT JOIN rom_assets AS ra_fanart ON ra_fanart.rom_id = r.id
        INNER JOIN assets AS a_fanart ON a_fanart.id = ra_fanart.asset_id AND a_fanart.asset_type = 'fanart'
    LEFT JOIN rom_assets AS ra_clearlogo ON ra_clearlogo.rom_id = r.id
        INNER JOIN assets AS a_clearlogo ON a_clearlogo.id = ra_clearlogo.asset_id AND a_clearlogo.asset_type = 'clearlogo'
    -- LEFT JOIN rom_assets AS ra_poster ON ra_poster.rom_id = r.id
    --     INNER JOIN assets AS a_poster ON a_poster.id = ra_poster.asset_id AND a_poster.asset_type = 'poster'
    LEFT JOIN rom_assets AS ra_banner ON ra_banner.rom_id = r.id
        INNER JOIN assets AS a_banner ON a_banner.id = ra_banner.asset_id AND a_banner.asset_type = 'banner'
    LEFT JOIN rom_assets AS ra_boxfront ON ra_boxfront.rom_id = r.id
        INNER JOIN assets AS a_boxfront ON a_boxfront.id = ra_boxfront.asset_id AND a_boxfront.asset_type = 'boxfront'
    LEFT JOIN rom_assets AS ra_boxback ON ra_banner.rom_id = r.id
        INNER JOIN assets AS a_boxback ON a_boxback.id = ra_banner.asset_id AND a_boxback.asset_type = 'boxback'
    LEFT JOIN rom_assets AS ra_3dbox ON ra_3dbox.rom_id = r.id
        INNER JOIN assets AS a_3dbox ON a_3dbox.id = ra_3dbox.asset_id AND a_3dbox.asset_type = '3dbox'
    LEFT JOIN rom_assets AS ra_flyer ON ra_flyer.rom_id = r.id
        INNER JOIN assets AS a_flyer ON a_flyer.id = ra_flyer.asset_id AND a_flyer.asset_type = 'flyer'
    LEFT JOIN rom_assets AS ra_snap ON ra_snap.rom_id = r.id
        INNER JOIN assets AS a_snap ON a_snap.id = ra_snap.asset_id AND a_snap.asset_type = 'snap'
    LEFT JOIN rom_assets AS ra_cartridge ON ra_cartridge.rom_id = r.id
        INNER JOIN assets AS a_cartridge ON a_cartridge.id = ra_cartridge.asset_id AND a_cartridge.asset_type = 'cartridge'
    LEFT JOIN rom_assets AS ra_manual ON ra_manual.rom_id = r.id
        INNER JOIN assets AS a_manual ON a_manual.id = ra_manual.asset_id AND a_manual.asset_type = 'manual'
    LEFT JOIN rom_assets AS ra_map ON ra_map.rom_id = r.id
        INNER JOIN assets AS a_map ON a_map.id = ra_map.asset_id AND a_map.asset_type = 'map'
    LEFT JOIN rom_assets AS ra_title ON ra_title.rom_id = r.id
        INNER JOIN assets AS a_title ON a_title.id = ra_title.asset_id AND a_title.asset_type = 'title'           
    LEFT JOIN rom_assets AS ra_trailer ON ra_trailer.rom_id = r.id
        INNER JOIN assets AS a_trailer ON a_trailer.id = ra_trailer.asset_id AND a_trailer.asset_type = 'trailer';

CREATE TABLE IF NOT EXISTS ael_version(app TEXT, version TEXT);