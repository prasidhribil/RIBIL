-- ============================================================================
-- GIS Engine Database Migration Script - Phase 1
-- Focus: Bengaluru Urban & Rural Districts
-- Description: Creates core administrative and spatial tables with PostGIS indexes
-- ============================================================================

-- Enable PostGIS extension if not already enabled
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================================
-- Table: karnataka_admin
-- Description: Administrative hierarchy for Karnataka villages, focused on Bengaluru
-- Columns: district, taluk, hobli, village, village_code, pin_code
-- ============================================================================
CREATE TABLE IF NOT EXISTS karnataka_admin (
    id SERIAL PRIMARY KEY,
    district VARCHAR(100) NOT NULL,
    taluk VARCHAR(100) NOT NULL,
    hobli VARCHAR(100) NOT NULL,
    village VARCHAR(200) NOT NULL,
    village_code VARCHAR(20) UNIQUE,
    pin_code VARCHAR(6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create B-Tree index on village for fast ILIKE searches
CREATE INDEX idx_karnataka_admin_village ON karnataka_admin USING btree (village);

-- Create composite index on (district, taluk, hobli) for hierarchical queries
CREATE INDEX idx_karnataka_admin_hierarchy ON karnataka_admin USING btree (district, taluk, hobli);

-- Create index on district for filtering
CREATE INDEX idx_karnataka_admin_district ON karnataka_admin USING btree (district);

-- Create index on taluk for filtering
CREATE INDEX idx_karnataka_admin_taluk ON karnataka_admin USING btree (taluk);

-- Add comment to table
COMMENT ON TABLE karnataka_admin IS 'Administrative hierarchy for Karnataka villages, optimized for Bengaluru Urban and Rural districts';

-- ============================================================================
-- Table: survey_parcels
-- Description: Digitized survey parcel polygons with spatial geometry
-- Columns: id, survey_no, village, hobli, district, area_acres, geom
-- ============================================================================
CREATE TABLE IF NOT EXISTS survey_parcels (
    id SERIAL PRIMARY KEY,
    survey_no TEXT NOT NULL,
    village VARCHAR(200) NOT NULL,
    hobli VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    area_acres FLOAT,
    geom GEOMETRY(Polygon, 4326),  -- WGS84 coordinate system
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    
);

-- Create mandatory GIST spatial index on geom for spatial queries
CREATE INDEX idx_survey_parcels_geom ON survey_parcels USING gist (geom);

-- Create B-Tree index on survey_no for lookups
CREATE INDEX idx_survey_parcels_survey_no ON survey_parcels USING btree (survey_no);

-- Create composite index on (district, village) for district-level filtering
CREATE INDEX idx_survey_parcels_district_village ON survey_parcels USING btree (district, village);

-- Add comment to table
COMMENT ON TABLE survey_parcels IS 'Digitized survey parcel polygons with spatial geometry for point-in-polygon queries';

-- ============================================================================
-- Table: cdp_zones (BDA Master Plan 2031)
-- Description: Bangalore Development Authority Comprehensive Development Plan zones
-- Columns: id, zone_type, zone_name, geom
-- ============================================================================
CREATE TABLE IF NOT EXISTS cdp_zones (
    id SERIAL PRIMARY KEY,
    zone_type VARCHAR(50) NOT NULL,  -- Residential, Commercial, Industrial, Green Belt, etc.
    zone_name VARCHAR(200),
    zone_code VARCHAR(50),
    geom GEOMETRY(Polygon, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create GIST spatial index on geom
CREATE INDEX idx_cdp_zones_geom ON cdp_zones USING gist (geom);

-- Create index on zone_type
CREATE INDEX idx_cdp_zones_type ON cdp_zones USING btree (zone_type);

COMMENT ON TABLE cdp_zones IS 'BDA Master Plan 2031 zone polygons for land utilization classification';

-- ============================================================================
-- Table: water_bodies (KSRSAC / NGT Lake Data)
-- Description: Bengaluru lakes and water bodies with buffer zones
-- Columns: id, lake_name, lake_type, geom, area_hectares
-- ============================================================================
CREATE TABLE IF NOT EXISTS water_bodies (
    id SERIAL PRIMARY KEY,
    lake_name VARCHAR(200) NOT NULL,
    lake_type VARCHAR(50),  -- Lake, Tank, Pond, Storm Water Drain
    area_hectares FLOAT,
    geom GEOMETRY(Polygon, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create GIST spatial index on geom
CREATE INDEX idx_water_bodies_geom ON water_bodies USING gist (geom);

-- Create index on lake_name
CREATE INDEX idx_water_bodies_name ON water_bodies USING btree (lake_name);

COMMENT ON TABLE water_bodies IS 'Bengaluru lakes and water bodies for NGT buffer zone checks (75m blocked, 75-150m warning)';

-- ============================================================================
-- Table: court_cases (NGT Tribunal Orders)
-- Description: National Green Tribunal violation orders and case records
-- Columns: id, case_number, village, survey_no, violation_type, status, order_date
-- ============================================================================
CREATE TABLE IF NOT EXISTS court_cases (
    id SERIAL PRIMARY KEY,
    case_number VARCHAR(100) UNIQUE NOT NULL,
    village VARCHAR(200) NOT NULL,
    survey_no TEXT,
    violation_type VARCHAR(100),  -- Encroachment, Pollution, Unauthorized Construction
    status VARCHAR(50),  -- Active, Closed, Pending
    order_date DATE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create composite index on (village, survey_no) for fast violation checks
CREATE INDEX idx_court_cases_village_survey ON court_cases USING btree (village, survey_no);

-- Create index on status
CREATE INDEX idx_court_cases_status ON court_cases USING btree (status);

-- Create full-text search index on description
CREATE INDEX idx_court_cases_description_fts ON court_cases USING gin (to_tsvector('english', description));

COMMENT ON TABLE court_cases IS 'NGT Tribunal orders and violation records for regulatory compliance checks';

-- ============================================================================
-- Table: aai_zones (Airport Authority of India - BIAL/HAL)
-- Description: Airport obstacle limitation surfaces and restriction zones
-- Columns: id, airport_name, restriction_type, geom, height_limit_meters
-- ============================================================================
CREATE TABLE IF NOT EXISTS aai_zones (
    id SERIAL PRIMARY KEY,
    airport_name VARCHAR(100) NOT NULL,  -- Kempegowda International Airport, HAL Airport
    restriction_type VARCHAR(100) NOT NULL,  -- Runway Protection Zone, Obstacle Free Zone, etc.
    height_limit_meters FLOAT,
    geom GEOMETRY(Polygon, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create GIST spatial index on geom
CREATE INDEX idx_aai_zones_geom ON aai_zones USING gist (geom);

-- Create index on airport_name
CREATE INDEX idx_aai_zones_airport ON aai_zones USING btree (airport_name);

-- Create index on restriction_type
CREATE INDEX idx_aai_zones_type ON aai_zones USING btree (restriction_type);

COMMENT ON TABLE aai_zones IS 'AAI airport restriction zones for BIAL and HAL obstacle limitation surfaces';

-- ============================================================================
-- Trigger: Update timestamp on row modification
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all tables with updated_at column
CREATE TRIGGER update_karnataka_admin_updated_at BEFORE UPDATE ON karnataka_admin
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_survey_parcels_updated_at BEFORE UPDATE ON survey_parcels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Migration Complete
-- ============================================================================
