-- ============================================================================
-- GIS Engine Database Migration Script - Phase 3
-- Focus: Fix water_bodies schema to match import script requirements
-- Description: Adds missing columns (category, objectid) and changes geometry type
--              from Polygon to MultiPolygon to support GeoJSON import
-- ============================================================================

-- ============================================================================
-- Step 1: Add missing columns
-- ============================================================================

-- Add category column (from LULC_Desc_1 in source data)
ALTER TABLE water_bodies ADD COLUMN IF NOT EXISTS category VARCHAR(100);

-- Add objectid column (from OBJECTID in source data)
ALTER TABLE water_bodies ADD COLUMN IF NOT EXISTS objectid INTEGER;

-- ============================================================================
-- Step 2: Change lake_name to nullable (if NOT NULL constraint exists)
-- ============================================================================

-- First check if lake_name has a NOT NULL constraint and drop it
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM pg_constraint 
        WHERE conrelid = 'water_bodies'::regclass 
        AND conname = 'water_bodies_lake_name_not_null'
    ) THEN
        ALTER TABLE water_bodies ALTER COLUMN lake_name DROP NOT NULL;
    END IF;
END $$;

-- ============================================================================
-- Step 3: Change geometry type from Polygon to MultiPolygon
-- ============================================================================

-- This requires recreating the geom column since PostGIS doesn't support direct type change
-- Step 3a: Create a temporary column with the new type
ALTER TABLE water_bodies ADD COLUMN IF NOT EXISTS geom_new GEOMETRY(MultiPolygon, 4326);

-- Step 3b: Convert existing Polygon geometries to MultiPolygon
UPDATE water_bodies SET geom_new = ST_Multi(geom) WHERE geom IS NOT NULL;

-- Step 3c: Drop the old geom column
ALTER TABLE water_bodies DROP COLUMN geom;

-- Step 3d: Rename the new column to geom
ALTER TABLE water_bodies RENAME COLUMN geom_new TO geom;

-- ============================================================================
-- Step 4: Create missing indexes
-- ============================================================================

-- Index on category for filtering
CREATE INDEX IF NOT EXISTS idx_water_bodies_category ON water_bodies USING btree (category);

-- Index on lake_type for filtering
CREATE INDEX IF NOT EXISTS idx_water_bodies_lake_type ON water_bodies USING btree (lake_type);

-- ============================================================================
-- Step 5: Add comments for documentation
-- ============================================================================

COMMENT ON COLUMN water_bodies.lake_name IS 'Lake name from source data (Name field). May be NULL for unnamed water bodies.';

COMMENT ON COLUMN water_bodies.category IS 'Land use category from LULC_Desc_1 (e.g., "Water bodies").';

COMMENT ON COLUMN water_bodies.lake_type IS 'Specific water body type from LULC_Desc_2 (e.g., "Tank", "Lake", "Pond", "Storm Water Drain").';

COMMENT ON COLUMN water_bodies.geom IS 'MultiPolygon geometry in WGS84 (SRID 4326).';

COMMENT ON COLUMN water_bodies.objectid IS 'Original OBJECTID from KSRSAC source data for traceability.';

-- ============================================================================
-- Step 6: Verify the schema
-- ============================================================================

-- This should show all expected columns
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'water_bodies'
ORDER BY ordinal_position;

-- ============================================================================
-- Migration Complete
-- ============================================================================
