
# Shared Queries
INSERT_METADATA       = "INSERT INTO metadata (id,year,genre,developer,rating,plot,assets_path,finished) VALUES (?,?,?,?,?,?,?,?)"
INSERT_ASSET          = "INSERT INTO assets (id, filepath, asset_type) VALUES (?,?,?)"
INSERT_ASSET_PATH     = "INSERT INTO assetpaths (id, path, asset_type) VALUES (?,?,?)"
UPDATE_METADATA       = "UPDATE metadata SET year=?, genre=?, developer=?, rating=?, plot=?, assets_path=?, finished=? WHERE id=?"
UPDATE_ASSET          = "UPDATE assets SET filepath = ?, asset_type = ? WHERE id = ?"
UPDATE_ASSET_PATH     = "UPDATE assetpaths SET path = ?, asset_type = ? WHERE id = ?"

# CATEGORIES
SELECT_CATEGORY = "SELECT * FROM vw_categories WHERE id = ?"
SELECT_CATEGORY_ASSETS = "SELECT * FROM vw_category_assets WHERE category_id = ?"
SELECT_CATEGORIES = "SELECT * FROM vw_categories ORDER BY m_name"
SELECT_ALL_CATEGORY_ASSETS = "SELECT * FROM vw_category_assets"
SELECT_ROOT_CATEGORIES = "SELECT * FROM vw_categories WHERE parent_id IS NULL ORDER BY m_name"
SELECT_ROOT_CATEGORY_ASSETS = "SELECT * FROM vw_category_assets WHERE parent_id IS NULL"
SELECT_CATEGORIES_BY_PARENT = "SELECT * FROM vw_categories WHERE parent_id = ? ORDER BY m_name"
SELECT_CATEGORY_ASSETS_BY_PARENT = "SELECT * FROM vw_category_assets WHERE parent_id = ?"

SELECT_CATEGORIES_BY_ROM = "SELECT c.* FROM vw_categories AS c INNER JOIN roms_in_category AS rc ON rc.category_id = c.id WHERE rc.rom_id = ?"
SELECT_CATEGORIES_ASSETS_BY_ROM = "SELECT ca.* FROM vw_category_assets AS ca INNER JOIN roms_in_category AS rc ON rc.category_id = ca.category_id WHERE rc.rom_id = ?"


INSERT_CATEGORY             = """
                                    INSERT INTO categories (id,name,parent_id,metadata_id,default_icon,default_fanart,default_banner,default_poster,default_clearlogo) 
                                    VALUES (?,?,?,?,?,?,?,?,?)
                                    """
UPDATE_CATEGORY             = """
                                    UPDATE categories SET name=?, 
                                    default_icon=?, default_fanart=?, default_banner=?, default_poster=?, default_clearlogo=?
                                    WHERE id =?
                                    """
INSERT_CATEGORY_ASSET = "INSERT INTO category_assets (category_id, asset_id) VALUES (?, ?)"
DELETE_CATEGORY = "DELETE FROM categories WHERE id = ?"
	
INSERT_ROM_IN_CATEGORY = "INSERT INTO roms_in_category (rom_id, category_id) VALUES (?,?)"
INSERT_ROM_IN_ROOT_CATEGORY = "INSERT INTO roms_in_category (rom_id, category_id) VALUES (?,NULL)"
REMOVE_ROM_FROM_CATEGORY = "DELETE FROM roms_in_category WHERE rom_id = ? AND category_id = ?"
REMOVE_ROMS_FROM_CATEGORY = "DELETE FROM roms_in_category WHERE category_id = ?"


#
# ROMCollectionRepository -> ROM Sets from SQLite DB
#
COUNT_ROMCOLLECTIONS             = "SELECT COUNT(*) as count FROM vw_romcollections"
SELECT_ROMCOLLECTION             = "SELECT * FROM vw_romcollections WHERE id = ?"
SELECT_ROMCOLLECTIONS            = "SELECT * FROM vw_romcollections ORDER BY m_name"
SELECT_ROOT_ROMCOLLECTIONS       = "SELECT * FROM vw_romcollections WHERE parent_id IS NULL ORDER BY m_name"
SELECT_ROMCOLLECTIONS_BY_PARENT  = "SELECT * FROM vw_romcollections WHERE parent_id = ? ORDER BY m_name"
SELECT_ROMCOLLECTIONS_BY_ROM     = "SELECT rs.* FROM vw_romcollections AS rs INNER JOIN roms_in_romcollection AS rr ON rr.romcollection_id = rs.id WHERE rr.rom_id = ?"

SELECT_VCOLLECTION_TITLES     = "SELECT DISTINCT(SUBSTR(UPPER(m_name), 1,1)) AS option_value FROM vw_roms"   
SELECT_VCOLLECTION_GENRES     = "SELECT DISTINCT(m_genre) AS option_value FROM vw_roms"   
SELECT_VCOLLECTION_DEVELOPER  = "SELECT DISTINCT(m_developer) AS option_value FROM vw_roms"   
SELECT_VCOLLECTION_ESRB       = "SELECT DISTINCT(m_esrb) AS option_value FROM vw_roms"
SELECT_VCOLLECTION_PEGI       = "SELECT DISTINCT(m_pegi) AS option_value FROM vw_roms"
SELECT_VCOLLECTION_YEAR       = "SELECT DISTINCT(m_year) AS option_value FROM vw_roms"
SELECT_VCOLLECTION_NPLAYERS   = "SELECT DISTINCT(m_nplayers) AS option_value FROM vw_roms"   
SELECT_VCOLLECTION_RATING     = "SELECT DISTINCT(m_rating) AS option_value FROM vw_roms"   

INSERT_ROMCOLLECTION               = """
                                    INSERT INTO romcollections (
                                            id,name,parent_id,metadata_id,platform,box_size, 
                                            default_icon,default_fanart,default_banner,default_poster,default_controller,default_clearlogo,
                                            roms_default_icon,roms_default_fanart,roms_default_banner,roms_default_poster,roms_default_clearlogo
                                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                                    """
UPDATE_ROMCOLLECTION               = """
                                    UPDATE romcollections SET 
                                        name=?, platform=?, box_size=?, 
                                        default_icon=?, default_fanart=?, default_banner=?, default_poster=?, default_controller=?, default_clearlogo=?,
                                        roms_default_icon=?, roms_default_fanart=?, roms_default_banner=?, roms_default_poster=?, roms_default_clearlogo=?
                                        WHERE id =?
                                    """
UPDATE_ROMCOLLECTION_PARENT        = "UPDATE romcollections SET parent_id = ? WHERE id =?"
DELETE_ROMCOLLECTION               = "DELETE FROM romcollections WHERE id = ?"

SELECT_ROMCOLLECTION_ASSETS_BY_SET       = "SELECT * FROM vw_romcollection_assets WHERE romcollection_id = ?"
SELECT_ROOT_ROMCOLLECTION_ASSETS         = "SELECT * FROM vw_romcollection_assets WHERE parent_id IS NULL"
SELECT_ROMCOLLECTIONS_ASSETS_BY_PARENT   = "SELECT * FROM vw_romcollection_assets WHERE parent_id = ?"
SELECT_ROMCOLLECTION_ASSETS_BY_ROM       = "SELECT ra.* FROM vw_romcollection_assets AS ra INNER JOIN roms_in_romcollection AS rr ON rr.romcollection_id = ra.romcollection_id WHERE rr.rom_id = ?"
SELECT_ROMCOLLECTION_ASSETS              = "SELECT * FROM vw_romcollection_assets"
SELECT_ROMCOLLECTION_ASSET_PATHS         = "SELECT * FROM vw_romcollection_asset_paths WHERE romcollection_id = ?"
SELECT_ROMCOLLECTION_ASSETS_PATHS_BY_ROM = "SELECT rap.* FROM vw_romcollection_asset_paths AS rap INNER JOIN roms_in_romcollection AS rr ON rr.romcollection_id = rap.romcollection_id WHERE rr.rom_id = ?"

INSERT_ROMCOLLECTION_ASSET               = "INSERT INTO romcollection_assets (romcollection_id, asset_id) VALUES (?, ?)"
INSERT_ROMCOLLECTION_ASSET_PATH          = "INSERT INTO romcollection_assetpaths (romcollection_id, assetpaths_id) VALUES (?, ?)"

INSERT_ROM_IN_ROMCOLLECTION        = "INSERT INTO roms_in_romcollection (rom_id, romcollection_id) VALUES (?,?)"
REMOVE_ROM_FROM_ROMCOLLECTION      = "DELETE FROM roms_in_romcollection WHERE rom_id = ? AND romcollection_id = ?"
REMOVE_ROMS_FROM_ROMCOLLECTION    =  "DELETE FROM roms_in_romcollection WHERE romcollection_id = ?"

SELECT_ROMCOLLECTION_LAUNCHERS     = "SELECT * FROM vw_romcollection_launchers WHERE romcollection_id = ?"
INSERT_ROMCOLLECTION_LAUNCHER      = "INSERT INTO romcollection_launchers (id, romcollection_id, akl_addon_id, settings, is_default) VALUES (?,?,?,?,?)"
UPDATE_ROMCOLLECTION_LAUNCHER      = "UPDATE romcollection_launchers SET settings = ?, is_default = ? WHERE id = ?"
DELETE_ROMCOLLECTION_LAUNCHERS     = "DELETE FROM romcollection_launchers WHERE romcollection_id = ?"
DELETE_ROMCOLLECTION_LAUNCHER      = "DELETE FROM romcollection_launchers WHERE romcollection_id = ? AND id = ?"

SELECT_ROMCOLLECTION_SCANNERS      = "SELECT * FROM vw_romcollection_scanners WHERE romcollection_id = ?"
INSERT_ROMCOLLECTION_SCANNER       = "INSERT INTO romcollection_scanners (id, romcollection_id, akl_addon_id, settings) VALUES (?,?,?,?)"
UPDATE_ROMCOLLECTION_SCANNER       = "UPDATE romcollection_scanners SET settings = ? WHERE id = ?"
DELETE_ROMCOLLECTION_SCANNER       = "DELETE FROM romcollection_scanners WHERE romcollection_id = ? AND id = ?"

SELECT_ROMCOLLECTION_LAUNCHERS_BY_ROM = "SELECT rl.* FROM vw_romcollection_launchers AS rl INNER JOIN roms_in_romcollection AS rr ON rr.romcollection_id = rl.romcollection_id WHERE rr.rom_id = ?"
SELECT_ROMCOLLECTION_SCANNERS_BY_ROM  = "SELECT rs.* FROM vw_romcollection_scanners AS rs INNER JOIN roms_in_romcollection AS rr ON rr.romcollection_id = rs.romcollection_id WHERE rr.rom_id = ?"

#
# ROMsRepository -> ROMs from SQLite DB
#     
SELECT_ROM                    = "SELECT * FROM vw_roms WHERE id = ?"
SELECT_ROM_ASSETS             = "SELECT * FROM vw_rom_assets WHERE rom_id = ?"
SELECT_ROM_ASSETPATHS         = "SELECT * FROM vw_rom_asset_paths WHERE rom_id = ?"
SELECT_ROM_TAGS               = "SELECT * FROM vw_rom_tags WHERE rom_id = ?"

SELECT_ROMS_BY_SET            = "SELECT r.* FROM vw_roms AS r INNER JOIN roms_in_romcollection AS rs ON rs.rom_id = r.id AND rs.romcollection_id = ?"
SELECT_ROM_ASSETS_BY_SET      = "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN roms_in_romcollection AS rs ON rs.rom_id = ra.rom_id AND rs.romcollection_id = ?"
SELECT_ROM_ASSETPATHS_BY_SET  = "SELECT rap.* FROM vw_rom_asset_paths AS rap INNER JOIN roms_in_romcollection AS rs ON rs.rom_id = rap.rom_id AND rs.romcollection_id = ?"
SELECT_ROM_TAGS_BY_SET        = "SELECT rt.* FROM vw_rom_tags AS rt INNER JOIN roms_in_romcollection AS rs ON rs.rom_id = rt.rom_id AND rs.romcollection_id = ?"

SELECT_ROMS_BY_CATEGORY           = "SELECT r.* FROM vw_roms AS r INNER JOIN roms_in_category AS rc ON rc.rom_id = r.id AND rc.category_id = ?"
SELECT_ROM_ASSETS_BY_CATEGORY     = "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN roms_in_category AS rc ON rc.rom_id = ra.rom_id AND rc.category_id = ?"
SELECT_ROM_ASSETPATHS_BY_CATEGORY = "SELECT rap.* FROM vw_rom_asset_paths AS rap INNER JOIN roms_in_category AS rc ON rc.rom_id = rap.rom_id AND rc.category_id = ?"
SELECT_ROM_TAGS_BY_CATEGORY       = "SELECT rt.* FROM vw_rom_tags AS rt INNER JOIN roms_in_category AS rc ON rc.rom_id = rt.rom_id AND rc.category_id = ?"

SELECT_ROMS_BY_ROOT_CATEGORY = "SELECT r.* FROM vw_roms AS r INNER JOIN roms_in_category AS rc ON rc.rom_id = r.id AND rc.category_id IS NULL"
SELECT_ROM_ASSETS_BY_ROOT_CATEGORY = "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN roms_in_category AS rc ON rc.rom_id = ra.rom_id AND rc.category_id IS NULL"
SELECT_ROM_ASSETPATHS_BY_ROOT_CATEGORY = "SELECT rap.* FROM vw_rom_asset_paths AS rap INNER JOIN roms_in_category AS rc ON rc.rom_id = rap.rom_id AND rc.category_id IS NULL"
SELECT_ROM_TAGS_BY_ROOT_CATEGORY = "SELECT rt.* FROM vw_rom_tags AS rt INNER JOIN roms_in_category AS rc ON rc.rom_id = rt.rom_id AND rc.category_id IS NULL"


# Filter values
SELECT_GENRES_BY_COLLECTION      = "SELECT DISTINCT(r.m_genre) AS genre FROM vw_roms AS r INNER JOIN roms_in_romcollection AS rs ON rs.rom_id = r.id AND rs.romcollection_id = ? ORDER BY genre"
SELECT_YEARS_BY_COLLECTION       = "SELECT DISTINCT(r.m_year) AS year FROM vw_roms AS r INNER JOIN roms_in_romcollection AS rs ON rs.rom_id = r.id AND rs.romcollection_id = ? ORDER BY year"
SELECT_DEVELOPER_BY_COLLECTION   = "SELECT DISTINCT(r.m_developer) AS developer FROM vw_roms AS r INNER JOIN roms_in_romcollection AS rs ON rs.rom_id = r.id AND rs.romcollection_id = ? ORDER BY developer"
SELECT_RATING_BY_COLLECTION      = "SELECT DISTINCT(r.m_rating) AS rating FROM vw_roms AS r INNER JOIN roms_in_romcollection AS rs ON rs.rom_id = r.id AND rs.romcollection_id = ? ORDER BY rating"

INSERT_ROM    = """
                    INSERT INTO roms (
                        id, metadata_id, name, num_of_players, num_of_players_online, esrb_rating, pegi_rating,
                        platform, box_size, nointro_status, cloneof, rom_status, scanned_by_id)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """ 

SELECT_MY_FAVOURITES               = "SELECT * FROM vw_roms WHERE is_favourite = 1"                                
SELECT_RECENTLY_PLAYED_ROMS        = "SELECT * FROM vw_roms WHERE last_launch_timestamp IS NOT NULL ORDER BY last_launch_timestamp DESC LIMIT 100"
SELECT_MOST_PLAYED_ROMS            = "SELECT * FROM vw_roms WHERE launch_count > 0 ORDER BY launch_count DESC LIMIT 100"
SELECT_FAVOURITES_ROM_ASSETS       = "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN roms AS r ON r.id = ra.rom_id WHERE r.is_favourite = 1"
SELECT_RECENTLY_PLAYED_ROM_ASSETS  = """
                                            SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN roms AS r ON r.id = ra.rom_id 
                                            WHERE r.last_launch_timestamp IS NOT NULL ORDER BY last_launch_timestamp DESC LIMIT 100
                                           """
SELECT_MOST_PLAYED_ROM_ASSETS      = """
                                            SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN roms AS r ON r.id = ra.rom_id 
                                            WHERE r.launch_count > 0 ORDER BY launch_count DESC LIMIT 100
                                           """

SELECT_BY_TITLE = "SELECT * FROM vw_roms WHERE m_name LIKE ? || '%'"
SELECT_BY_GENRE = "SELECT * FROM vw_roms WHERE m_genre = ?"
SELECT_BY_DEVELOPER = "SELECT * FROM vw_roms WHERE m_developer = ?"
SELECT_BY_YEAR = "SELECT * FROM vw_roms WHERE m_year = ?"
SELECT_BY_NPLAYERS = "SELECT * FROM vw_roms WHERE m_nplayers = ?"
SELECT_BY_ESRB = "SELECT * FROM vw_roms WHERE m_esrb = ?"
SELECT_BY_PEGI = "SELECT * FROM vw_roms WHERE m_pegi = ?"
SELECT_BY_RATING = "SELECT * FROM vw_roms WHERE m_rating = ?"
                                
SELECT_BY_TITLE_ASSETS    = "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN vw_roms AS r ON r.id = ra.rom_id WHERE UPPER(r.m_name) LIKE ? || '%'"
SELECT_BY_GENRE_ASSETS    = "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN vw_roms AS r ON r.id = ra.rom_id WHERE r.m_genre = ?"
SELECT_BY_DEVELOPER_ASSETS= "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN vw_roms AS r ON r.id = ra.rom_id WHERE r.m_developer = ?"
SELECT_BY_YEAR_ASSETS     = "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN vw_roms AS r ON r.id = ra.rom_id WHERE r.m_year = ?"
SELECT_BY_NPLAYERS_ASSETS = "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN vw_roms AS r ON r.id = ra.rom_id WHERE r.m_nplayers = ?"
SELECT_BY_ESRB_ASSETS     = "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN vw_roms AS r ON r.id = ra.rom_id WHERE r.m_esrb = ?"
SELECT_BY_PEGI_ASSETS     = "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN vw_roms AS r ON r.id = ra.rom_id WHERE r.m_pegi = ?"
SELECT_BY_RATING_ASSETS   = "SELECT ra.* FROM vw_rom_assets AS ra INNER JOIN vw_roms AS r ON r.id = ra.rom_id WHERE r.m_rating = ?"
                                
INSERT_ROM_ASSET          = "INSERT INTO rom_assets (rom_id, asset_id) VALUES (?, ?)"
INSERT_ROM_ASSET_PATH     = "INSERT INTO rom_assetpaths (rom_id, assetpaths_id) VALUES (?, ?)"
INSERT_ROM_SCANNED_DATA   = "INSERT INTO scanned_roms_data (rom_id, data_key, data_value) VALUES (?, ?, ?)"

UPDATE_ROM                = """
                                  UPDATE roms 
                                  SET name=?, num_of_players=?, num_of_players_online=?, esrb_rating=?, pegi_rating=?, platform=?, box_size=?,
                                  nointro_status=?, cloneof=?, rom_status=?, launch_count=?, last_launch_timestamp=?,
                                  is_favourite=?, scanned_by_id=? WHERE id =?
                                  """
DELETE_ROM                = "DELETE FROM roms WHERE id = ?"
DELETE_ROMS_BY_COLLECTION = "DELETE FROM roms WHERE id IN (SELECT rc.rom_id FROM roms_in_romcollection AS rc WHERE rc.romcollection_id = ?)"

SELECT_ROM_SCANNED_DATA = "SELECT s.* FROM scanned_roms_data AS s WHERE s.rom_id = ?"
SELECT_ROM_SCANNED_DATA_BY_SET = "SELECT s.* FROM scanned_roms_data AS s INNER JOIN roms_in_romcollection AS rs ON rs.rom_id = s.rom_id AND rs.romcollection_id = ?"
SELECT_ROM_SCANNED_DATA_BY_CATEGORY = "SELECT s.* FROM scanned_roms_data AS s INNER JOIN roms_in_category AS rc ON rc.rom_id = s.rom_id AND rc.category_id = ?"
SELECT_ROM_SCANNED_DATA_BY_ROOT_CATEGORY = "SELECT s.* FROM scanned_roms_data AS s INNER JOIN roms_in_category AS rc ON rc.rom_id = s.rom_id AND rc.category_id IS NULL"
DELETE_SCANNED_DATA = "DELETE FROM scanned_roms_data WHERE rom_id = ?"

SELECT_ROM_LAUNCHERS     = "SELECT * FROM vw_rom_launchers WHERE rom_id = ?"
INSERT_ROM_LAUNCHER      = "INSERT INTO rom_launchers (id, rom_id, akl_addon_id, settings, is_default) VALUES (?,?,?,?,?)"
UPDATE_ROM_LAUNCHER      = "UPDATE rom_launchers SET settings = ?, is_default = ? WHERE id = ?"
DELETE_ROM_LAUNCHERS     = "DELETE FROM rom_launchers WHERE rom_id = ?"
DELETE_ROM_LAUNCHER      = "DELETE FROM rom_launchers WHERE rom_id = ? AND id = ?"

SELECT_TAGS               = "SELECT * FROM tags"
INSERT_TAG                = "INSERT INTO tags (id, tag) VALUES (?,?)" 
ADD_TAG_TO_ROM            = "INSERT INTO metatags (metadata_id, tag_id) VALUES (?,?)"
DELETE_EXISTING_ROM_TAGS  = "DELETE FROM metatags WHERE metadata_id = ?"
DELETE_TAG                = "DELETE FROM tags WHERE id = ?"

#
# AelAddonRepository -> AKL Adoon objects from SQLite DB
#     
SELECT_ADDON              = "SELECT * FROM akl_addon WHERE id = ?"
SELECT_ADDON_BY_ADDON_ID  = "SELECT * FROM akl_addon WHERE addon_id = ? AND addon_type = ?"
SELECT_ADDONS             = "SELECT * FROM akl_addon"
SELECT_LAUNCHER_ADDONS    = "SELECT * FROM akl_addon WHERE addon_type = 'LAUNCHER' ORDER BY name"
SELECT_SCANNER_ADDONS     = "SELECT * FROM akl_addon WHERE addon_type = 'SCANNER' ORDER BY name"
SELECT_SCRAPER_ADDONS     = "SELECT * FROM akl_addon WHERE addon_type = 'SCRAPER' ORDER BY name"
INSERT_ADDON              = "INSERT INTO akl_addon(id, name, addon_id, version, addon_type, extra_settings) VALUES(?,?,?,?,?,?)" 
UPDATE_ADDON              = "UPDATE akl_addon SET name = ?, addon_id = ?, version = ?, addon_type = ?, extra_settings = ? WHERE id = ?" 
