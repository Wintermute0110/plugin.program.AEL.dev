CREATE TABLE IF NOT EXISTS metadata(
    id TEXT PRIMARY KEY, 
    year TEXT,
    genre TEXT,
    developer TEXT,
    rating INTEGER NULL,
    plot TEXT,
    finished INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS assets(
    id TEXT PRIMARY KEY,
    filepath TEXT NOT NULL,
    asset_type INTEGER NOT NULL
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

CREATE TABLE IF NOT EXISTS romset(
    id TEXT PRIMARY KEY, 
    name TEXT NOT NULL,
    parent_id TEXT NULL,
    metadata_id TEXT,
    FOREIGN KEY (parent_id) REFERENCES categories (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (metadata_id) REFERENCES metadata (id) 
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
    FOREIGN KEY (romset_id) REFERENCES romset (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (asset_id) REFERENCES assets (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE VIEW IF NOT EXISTS vw_categories AS SELECT 
    c.id AS id, 
    c.parent_id AS parent_id,
    c.name AS m_name,
    m.year AS m_year, 
    m.genre AS m_genre,
    m.developer AS m_developer,
    m.rating AS m_rating,
    m.plot AS m_plot,
    m.finished AS finished,
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
        
CREATE TABLE IF NOT EXISTS ael_version(version TEXT);