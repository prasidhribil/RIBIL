# Empty Tables Report - GIS Data Requirements

## Overview

This report identifies all database tables that are currently empty and require manual GIS data ingestion.

## Table 1: survey_parcels

**Status:** EMPTY (0 records)

**Purpose:** Point-in-polygon survey number lookup for property verification

**Schema:**
```sql
CREATE TABLE survey_parcels (
    id SERIAL PRIMARY KEY,
    survey_no TEXT NOT NULL,
    village VARCHAR(200) NOT NULL,
    hobli VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    area_acres FLOAT,
    geom GEOMETRY(Polygon, 4326),  -- WGS84 coordinate system
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_survey_parcels_village FOREIGN KEY (village) 
        REFERENCES karnataka_admin(village) ON DELETE SET NULL
);
```

**Required Data:** Digitized survey parcel polygons with spatial geometry

**Data Format Requirements:**
- Shapefile (.shp) or GeoJSON
- Coordinate System: WGS84 (EPSG:4326)
- Geometry Type: Polygon
- Required Fields: survey_no, village, hobli, district, area_acres, geom

**Data Sources:**
1. **Bhoomi Portal** (Karnataka Land Records Department)
   - Official government source for survey records
   - May require RTI request for bulk data
   - URL: https://bhoomi.karnataka.gov.in

2. **Survey of India**
   - National survey organization
   - Topographic maps with survey boundaries
   - URL: https://surveyofindia.gov.in

3. **Local Municipal Survey Departments**
   - Bengaluru Urban/Rural district offices
   - Physical survey maps available for inspection

**QGIS Workflow:**
1. Download shapefile/GeoJSON from source
2. Open in QGIS
3. Verify coordinate system (reproject to WGS84 if needed)
4. Validate geometry (check for invalid polygons)
5. Join with karnataka_admin table on village name
6. Export to PostgreSQL using DB Manager plugin
7. Run: `INSERT INTO survey_parcels SELECT * FROM imported_data`

**Estimated Records:** 100,000+ for Bengaluru Urban and Rural districts

**Impact of Missing Data:**
- Survey number lookup API returns 404
- Property verification cannot identify survey parcels
- Point-in-polygon queries fail

**Priority:** HIGH (core functionality)

---

## Table 2: water_bodies

**Status:** EMPTY (0 records)

**Purpose:** NGT lake buffer zone compliance checks (75m blocked, 75-150m warning)

**Schema:**
```sql
CREATE TABLE water_bodies (
    id SERIAL PRIMARY KEY,
    lake_name VARCHAR(200) NOT NULL,
    lake_type VARCHAR(50),  -- Lake, Tank, Pond, Storm Water Drain
    area_hectares FLOAT,
    geom GEOMETRY(Polygon, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Required Data:** Bengaluru lakes and water body polygons

**Data Format Requirements:**
- Shapefile (.shp) or GeoJSON
- Coordinate System: WGS84 (EPSG:4326)
- Geometry Type: Polygon
- Required Fields: lake_name, lake_type, area_hectares, geom

**Data Sources:**
1. **KSRSAC** (Karnataka State Remote Sensing Applications Centre)
   - Official state remote sensing agency
   - Satellite-derived lake boundaries
   - URL: https://ksrsac.karnataka.gov.in

2. **NGT (National Green Tribunal)**
   - Official lake data for compliance monitoring
   - Lake buffer zone definitions
   - URL: https://ngt.gov.in

3. **BBMP (Bruhat Bengaluru Mahanagara Palike)**
   - Municipal lake database
   - Storm water drain network
   - URL: https://bbmp.gov.in

**QGIS Workflow:**
1. Download shapefile/GeoJSON from source
2. Open in QGIS
3. Verify coordinate system (reproject to WGS84 if needed)
4. Validate geometry
5. Calculate buffer zones if not pre-calculated:
   - 75m buffer (blocked zone)
   - 150m buffer (warning zone)
6. Export to PostgreSQL using DB Manager plugin
7. Run: `INSERT INTO water_bodies SELECT * FROM imported_data`

**Estimated Records:** 200+ lakes in Bengaluru region

**Impact of Missing Data:**
- Lake buffer checks return default (no restrictions)
- NGT compliance cannot be verified
- Environmental risk assessment incomplete

**Priority:** HIGH (regulatory compliance)

---

## Table 3: cdp_zones

**Status:** EMPTY (0 records)

**Purpose:** BDA Master Plan 2031 zone compliance checks

**Schema:**
```sql
CREATE TABLE cdp_zones (
    id SERIAL PRIMARY KEY,
    zone_type VARCHAR(50) NOT NULL,  -- Residential, Commercial, Industrial, Green Belt, etc.
    zone_name VARCHAR(200),
    zone_code VARCHAR(50),
    geom GEOMETRY(Polygon, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Required Data:** Bangalore Development Authority Comprehensive Development Plan zones

**Data Format Requirements:**
- Shapefile (.shp) or GeoJSON
- Coordinate System: WGS84 (EPSG:4326)
- Geometry Type: Polygon
- Required Fields: zone_type, zone_name, zone_code, geom

**Data Sources:**
1. **BDA (Bangalore Development Authority)**
   - Official CDP 2031 Master Plan
   - Zone classification maps
   - URL: https://bdabangalore.org

2. **Urban Development Department, Karnataka**
   - State-level urban planning authority
   - Master plan approvals

3. **Town and Country Planning**
   - Regional planning authority
   - Land use classification

**QGIS Workflow:**
1. Download CDP 2031 shapefile from BDA
2. Open in QGIS
3. Verify coordinate system (reproject to WGS84 if needed)
4. Validate zone classifications:
   - Residential (R1, R2, R3, etc.)
   - Commercial (C1, C2, etc.)
   - Industrial (I1, I2, etc.)
   - Green Belt (GB)
   - Public/Semi-Public (PSP)
5. Export to PostgreSQL using DB Manager plugin
6. Run: `INSERT INTO cdp_zones SELECT * FROM imported_data`

**Estimated Records:** 50-100 zone polygons

**Impact of Missing Data:**
- CDP zone checks return default (not in any zone)
- Land use compliance cannot be verified
- Building permit eligibility unknown

**Priority:** HIGH (regulatory compliance)

---

## Table 4: aai_zones

**Status:** EMPTY (0 records)

**Purpose:** Airport Authority of India restriction zones (BIAL/HAL)

**Schema:**
```sql
CREATE TABLE aai_zones (
    id SERIAL PRIMARY KEY,
    airport_name VARCHAR(100) NOT NULL,  -- Kempegowda International Airport, HAL Airport
    restriction_type VARCHAR(100) NOT NULL,  -- Runway Protection Zone, Obstacle Free Zone, etc.
    height_limit_meters FLOAT,
    geom GEOMETRY(Polygon, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Required Data:** Airport obstacle limitation surfaces and restriction zones

**Data Format Requirements:**
- Shapefile (.shp) or GeoJSON
- Coordinate System: WGS84 (EPSG:4326)
- Geometry Type: Polygon
- Required Fields: airport_name, restriction_type, height_limit_meters, geom

**Data Sources:**
1. **AAI (Airport Authority of India)**
   - Official obstruction charts
   - Airport technical data
   - URL: https://aai.gov.in

2. **BIAL (Kempegowda International Airport)**
   - Airport technical committee
   - Obstacle limitation surfaces
   - URL: https://bialairport.com

3. **HAL Airport**
   - Technical data for HAL airport
   - Restriction zone maps

**QGIS Workflow:**
1. Download obstruction charts from AAI
2. Open in QGIS
3. Verify coordinate system (reproject to WGS84 if needed)
4. Validate restriction types:
   - Runway Protection Zone (RPZ)
   - Obstacle Free Zone (OFZ)
   - Inner Horizontal Surface
   - Conical Surface
   - Approach Surface
5. Validate height limits for each zone
6. Export to PostgreSQL using DB Manager plugin
7. Run: `INSERT INTO aai_zones SELECT * FROM imported_data`

**Estimated Records:** 10-20 zone polygons per airport

**Impact of Missing Data:**
- AAI zone checks return default (not in restriction zone)
- Building height restrictions unknown
- Aviation safety compliance unverifiable

**Priority:** MEDIUM (aviation safety)

---

## Table 5: court_cases

**Status:** EMPTY (0 records)

**Purpose:** NGT Tribunal orders and violation records

**Schema:**
```sql
CREATE TABLE court_cases (
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
```

**Required Data:** NGT case records for Bengaluru region

**Data Format Requirements:**
- CSV or JSON (tabular data, no geometry)
- Required Fields: case_number, village, survey_no, violation_type, status, order_date, description

**Data Sources:**
1. **NGT (National Green Tribunal)**
   - Official case database
   - Tribunal orders and judgments
   - URL: https://ngt.gov.in

2. **Karnataka State Pollution Control Board**
   - Environmental violation records
   - Case tracking system
   - URL: https://kspcb.karnataka.gov.in

3. **District Courts**
   - Environmental case records
   - Civil litigation related to land

**Import Method:**
1. Download CSV/JSON from source
2. Clean and validate data
3. Direct SQL INSERT or use pgAdmin import wizard
4. Run: `COPY court_cases FROM 'court_cases.csv' DELIMITER ',' CSV HEADER;`

**Estimated Records:** 1000+ active cases

**Impact of Missing Data:**
- NGT orders check returns default (no violations)
- Legal risk assessment incomplete
- Property history unverifiable

**Priority:** MEDIUM (legal compliance)

---

## Summary

| Table | Records | Data Type | QGIS Required | Priority | Impact |
|-------|---------|-----------|---------------|----------|--------|
| survey_parcels | 0 | Spatial (Polygon) | Yes | HIGH | Core functionality blocked |
| water_bodies | 0 | Spatial (Polygon) | Yes | HIGH | Regulatory compliance blocked |
| cdp_zones | 0 | Spatial (Polygon) | Yes | HIGH | Regulatory compliance blocked |
| aai_zones | 0 | Spatial (Polygon) | Yes | MEDIUM | Aviation safety blocked |
| court_cases | 0 | Tabular (CSV) | No | MEDIUM | Legal compliance blocked |

**Total Empty Tables:** 5

**Total Estimated Records Required:** ~101,350+

**QGIS Work Required:** 4 out of 5 tables (80%)

**Data Acquisition Timeline:**
- **Immediate (1-2 weeks):** court_cases (tabular data, easier to obtain)
- **Short-term (1-2 months):** cdp_zones, aai_zones (official government sources)
- **Long-term (3-6 months):** survey_parcels, water_bodies (requires RTI/government approval)

**Recommended Action Plan:**
1. Start with court_cases (no GIS work required)
2. Obtain CDP 2031 zones from BDA (official source)
3. Obtain AAI obstruction charts (aviation safety priority)
4. Request lake data from KSRSAC (environmental compliance)
5. Pursue survey parcel data through Bhoomi RTI request (longest timeline)
