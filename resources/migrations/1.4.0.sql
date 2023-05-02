-- CREATE NEW TABLES
CREATE TABLE IF NOT EXISTS assetmappings (
    id TEXT PRIMARY KEY,
    mapped_asset_type TEXT NOT NULL,
    to_asset_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS metadata_assetmappings(
    metadata_id TEXT,
    assetmapping_id TEXT,
    FOREIGN KEY (metadata_id) REFERENCES metadata (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (assetmapping_id) REFERENCES assetmappings (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS romcollection_roms_assetmappings(
    romcollection_id TEXT,
    assetmapping_id TEXT,
    FOREIGN KEY (romcollection_id) REFERENCES romcollections (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (assetmapping_id) REFERENCES assetmappings (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);
--------------------- UPDATE ROWS
DELETE FROM assetmappings;
DELETE FROM metadata_assetmappings;
DELETE FROM romcollection_roms_assetmappings;

-- Category default mappings
INSERT INTO assetmappings (id, mapped_asset_type, to_asset_type)
    SELECT c.id || 'ico', 'icon', substr(c.default_icon, 3)
    FROM categories as c WHERE c.default_icon != 's_icon';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT c.metadata_id, c.id || 'ico'
    FROM categories as c WHERE c.default_icon != 's_icon';

INSERT INTO assetmappings (id, mapped_asset_type, to_asset_type)
    SELECT c.id || 'fan', 'fanart', substr(c.default_fanart, 3)
    FROM categories as c WHERE c.default_fanart != 's_fanart';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT c.metadata_id, c.id || 'fan'
    FROM categories as c WHERE c.default_fanart != 's_fanart';

INSERT INTO assetmappings (id, mapped_asset_type, to_asset_type)
    SELECT c.id || 'ban', 'banner', substr(c.default_banner, 3)
    FROM categories as c WHERE c.default_banner != 's_banner';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT c.metadata_id, c.id || 'ban'
    FROM categories as c WHERE c.default_banner != 's_banner';

INSERT INTO assetmappings (id, mapped_asset_type, to_asset_type)
    SELECT c.id || 'pos', 'poster', substr(c.default_poster, 3)
    FROM categories as c WHERE c.default_poster != 's_poster';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT c.metadata_id, c.id || 'pos'
    FROM categories as c WHERE c.default_poster != 's_poster';

INSERT INTO assetmappings (id, mapped_asset_type, to_asset_type)
    SELECT c.id || 'log', 'clearlogo', substr(c.default_clearlogo, 3)
    FROM categories as c WHERE c.default_clearlogo != 's_clearlogo';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT c.metadata_id, c.id || 'log'
    FROM categories as c WHERE c.default_clearlogo != 's_clearlogo';

-- RomCollection default mappings --------------------
INSERT INTO assetmappings (id, mapped_asset_type, to_asset_type)
    SELECT rc.id || 'ico', 'icon', substr(rc.default_icon, 3)
    FROM romcollections as rc WHERE rc.default_icon != 's_icon';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT rc.metadata_id, rc.id || 'ico'
    FROM romcollections as rc WHERE rc.default_icon != 's_icon';

INSERT INTO assetmappings (id, mapped_asset_type, to_asset_type)
    SELECT rc.id || 'fan', 'fanart', substr(rc.default_fanart, 3)
    FROM romcollections as rc WHERE rc.default_fanart != 's_fanart';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT rc.metadata_id, rc.id || 'fan'
    FROM romcollections as rc WHERE rc.default_fanart != 's_fanart';

INSERT INTO assetmappings (id, mapped_asset_type, to_asset_type)
    SELECT rc.id || 'ban', 'banner', substr(rc.default_banner, 3)
    FROM romcollections as rc WHERE rc.default_banner != 's_banner';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT rc.metadata_id, rc.id || 'ban'
    FROM romcollections as rc WHERE rc.default_banner != 's_banner';

INSERT INTO assetmappings (id, mapped_asset_type, to_asset_type)
    SELECT rc.id || 'pos', 'poster', substr(rc.default_poster, 3)
    FROM romcollections as rc WHERE rc.default_poster != 's_poster';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT rc.metadata_id, rc.id || 'pos'
    FROM romcollections as rc WHERE rc.default_poster != 's_poster';

INSERT INTO assetmappings (id, mapped_asset_type, to_asset_type)
    SELECT rc.id || 'con', 'controller', substr(rc.default_controller, 3)
    FROM romcollections as rc WHERE rc.default_controller != 's_controller';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT rc.metadata_id, rc.id || 'con'
    FROM romcollections as rc WHERE rc.default_controller != 's_controller';
    
INSERT INTO assetmappings (id, mapped_asset_type, to_asset_type)
    SELECT rc.id || 'log', 'clearlogo', substr(rc.default_clearlogo, 3)
    FROM romcollections as rc WHERE rc.default_clearlogo != 's_clearlogo';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT rc.metadata_id, rc.id || 'log'
    FROM romcollections as rc WHERE rc.default_clearlogo != 's_clearlogo';

-- ROMs default mappings --------------------
INSERT INTO assetmappings (id, mapped_asset_type, to_asset_type)
    SELECT rc.id || 'rmico', 'icon', substr(rc.roms_default_icon, 3)
    FROM romcollections as rc WHERE rc.roms_default_icon != 's_boxfront';

INSERT INTO romcollection_roms_assetmappings (romcollection_id, assetmapping_id)
    SELECT rc.id, rc.id || 'rmico'
    FROM romcollections as rc WHERE rc.roms_default_icon != 's_boxfront';

INSERT INTO assetmappings (id, mapped_asset_type, to_asset_type)
    SELECT rc.id || 'rmfan', 'fanart', substr(rc.roms_default_fanart, 3)
    FROM romcollections as rc WHERE rc.roms_default_fanart != 's_fanart';

INSERT INTO romcollection_roms_assetmappings (romcollection_id, assetmapping_id)
    SELECT rc.id, rc.id || 'rmfan'
    FROM romcollections as rc WHERE rc.roms_default_fanart != 's_fanart';

INSERT INTO assetmappings (id, mapped_asset_type, to_asset_type)
    SELECT rc.id || 'rmban', 'banner', substr(rc.roms_default_banner, 3)
    FROM romcollections as rc WHERE rc.roms_default_banner != 's_banner';

INSERT INTO romcollection_roms_assetmappings (romcollection_id, assetmapping_id)
    SELECT rc.id, rc.id || 'rmban'
    FROM romcollections as rc WHERE rc.roms_default_banner != 's_banner';

INSERT INTO assetmappings (id, mapped_asset_type, to_asset_type)
    SELECT rc.id || 'rmpos', 'poster', substr(rc.roms_default_poster, 3)
    FROM romcollections as rc WHERE rc.roms_default_poster != 's_flyer';

INSERT INTO romcollection_roms_assetmappings (romcollection_id, assetmapping_id)
    SELECT rc.id, rc.id || 'rmpos'
    FROM romcollections as rc WHERE rc.roms_default_poster != 's_flyer';

INSERT INTO assetmappings (id, mapped_asset_type, to_asset_type)
    SELECT rc.id || 'rmlog', 'clearlogo', substr(rc.roms_default_clearlogo, 3)
    FROM romcollections as rc WHERE rc.roms_default_clearlogo != 's_clearlogo';

INSERT INTO romcollection_roms_assetmappings (romcollection_id, assetmapping_id)
    SELECT rc.id, rc.id || 'rmlog'
    FROM romcollections as rc WHERE rc.roms_default_clearlogo != 's_clearlogo';

-- UPDATE EXISTING TABLES AND VIEWS
PRAGMA foreign_keys=OFF;
PRAGMA legacy_alter_table=ON;

DROP VIEW IF EXiSTS vw_romcollections;
DROP VIEW IF EXiSTS vw_categories;

ALTER TABLE categories RENAME TO categories_temp;

CREATE TABLE IF NOT EXISTS categories(
    id TEXT PRIMARY KEY, 
    name TEXT NOT NULL,
    parent_id TEXT NULL,
    metadata_id TEXT,
    FOREIGN KEY (parent_id) REFERENCES categories (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (metadata_id) REFERENCES metadata (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

INSERT INTO categories (id, name, parent_id, metadata_id)
    SELECT id, name, parent_id, metadata_id FROM categories_temp;

DROP TABLE categories_temp;

ALTER TABLE romcollections RENAME TO romcollections_temp;

CREATE TABLE IF NOT EXISTS romcollections(
    id TEXT PRIMARY KEY, 
    name TEXT NOT NULL,
    platform TEXT,
    box_size TEXT,
    parent_id TEXT NULL,
    metadata_id TEXT,
    FOREIGN KEY (parent_id) REFERENCES categories (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (metadata_id) REFERENCES metadata (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

INSERT INTO romcollections (id, name, platform, box_size, parent_id, metadata_id)
    SELECT id, name, platform, box_size, parent_id, metadata_id FROM romcollections_temp;

DROP TABLE romcollections_temp;

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
    (SELECT COUNT(*) FROM roms AS rms INNER JOIN roms_in_romcollection AS rrs ON rms.id = rrs.rom_id AND rrs.romcollection_id = r.id) as num_roms
FROM romcollections AS r 
    INNER JOIN metadata AS m ON r.metadata_id = m.id;    

PRAGMA foreign_keys=ON;
PRAGMA legacy_alter_table=OFF;