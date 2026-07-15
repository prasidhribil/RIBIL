-- ============================================================================
-- GIS Engine Database Migration Script - Phase 2
-- Focus: Water Bodies Table Update for Bengaluru Lakes
-- Description: Updates water_bodies table to support MultiPolygon geometry
--              and adds category column from KSRSAC/NGT lake data
-- ============================================================================

-- ============================================================================
-- Step 1: Drop existing water_bodies table and recreate with correct schema
-- Reason: Need to change geometry type from Polygon to MultiPolygon
--         and add category column, plus allow NULL lake_name
-- ============================================================================

DROP TABLE IF EXISTS water_bodies CASCADE;

-- ============================================================================
-- Step 2: Recreate water_bodies table with updated schema
-- ============================================================================
CREATE TABLE water_bodies (
    id SERIAL PRIMARY KEY,
    lake_name VARCHAR(200),  -- Changed to allow NULL (many lakes have no name)
    category VARCHAR(100),   -- Added: LULC_Desc_1 (e.g., "Water bodies")
    lake_type VARCHAR(50),   -- LULC_Desc_2 (e.g., "Tank", "Lake", "Pond")
    area_hectares FLOAT,
    geom GEOMETRY(MultiPolygon, 4326),  -- Changed from Polygon to MultiPolygon
    objectid INTEGER,  -- Original OBJECTID from source data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Step 3: Create spatial indexes
-- ============================================================================

-- GIST index on geom for spatial queries (ST_Contains, ST_DWithin, ST_Distance)
CREATE INDEX idx_water_bodies_geom ON water_bodies USING gist (geom);

-- B-Tree index on lake_name for text searches
CREATE INDEX idx_water_bodies_lake_name ON water_bodies USING btree (lake_name);

-- B-Tree index on category for filtering
CREATE INDEX idx_water_bodies_category ON water_bodies USING btree (category);

-- B-Tree index on lake_type for filtering
CREATE INDEX idx_water_bodies_lake_type ON water_bodies USING btree (lake_type);

-- ============================================================================
-- Step 4: Add comments for documentation
-- ============================================================================

COMMENT ON TABLE water_bodies IS 'Bengaluru lakes and water bodies from KSRSAC/NGT data. Geometry type: MultiPolygon (SRID 4326). Used for NGT buffer zone checks (75m blocked, 75-150m warning).';

COMMENT ON COLUMN water_bodies.lake_name IS 'Lake name from source data (Name field). May be NULL for unnamed water bodies.';

COMMENT ON COLUMN water_bodies.category IS 'Land use category from LULC_Desc_1 (e.g., "Water bodies").';

COMMENT ON COLUMN water_bodies.lake_type IS 'Specific water body type from LULC_Desc_2 (e.g., "Tank", "Lake", "Pond", "Storm Water Drain").';

COMMENT ON COLUMN water_bodies.geom IS 'MultiPolygon geometry in WGS84 (SRID 4326).';

COMMENT ON COLUMN water_bodies.objectid IS 'Original OBJECTID from KSRSAC source data for traceability.';

-- ============================================================================
-- Migration Complete
-- ============================================================================
