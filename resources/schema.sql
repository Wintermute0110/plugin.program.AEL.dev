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
    parent_id TEXT NULL,
    metadata_id TEXT,
    launcher_id TEXT,
    default_icon TEXT DEFAULT 's_icon' NOT NULL,
    default_fanart TEXT DEFAULT 's_fanart' NOT NULL,
    default_banner TEXT DEFAULT 's_banner' NOT NULL,
    default_poster TEXT DEFAULT 's_poster' NOT NULL,
    default_controller TEXT DEFAULT 's_controller' NOT NULL,
    default_clearlogo TEXT DEFAULT 's_clearlogo' NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES categories (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (metadata_id) REFERENCES metadata (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (launcher_id) REFERENCES ael_addon (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

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
    0 AS num_romsets
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
    a_icon.filepath AS s_icon, 
    a_fanart.filepath AS s_fanart,
    a_clearlogo.filepath AS s_clearlogo,
    a_poster.filepath AS s_poster,
    a_banner.filepath AS s_banner,
    a_trailer.filepath AS s_trailer,
    r.default_icon AS default_icon,
    r.default_fanart AS default_fanart,
    r.default_banner AS default_banner,
    r.default_poster AS default_poster,
    r.default_controller AS default_controller,
    r.default_clearlogo AS default_clearlogo
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
        
CREATE TABLE IF NOT EXISTS ael_version(app TEXT, version TEXT);