# Water Bodies Testing Guide

This document provides exact commands to import, verify, and test the water_bodies dataset.

## Prerequisites

- PostgreSQL with PostGIS extension installed
- Database `gis_engine` created
- Python 3.8+ with asyncpg installed
- FastAPI application running

## 1. Database Setup

### Run Migrations

```bash
# Run migration 001 (initial schema)
psql -h localhost -U postgres -d gis_engine -f database/migrations/001_initial_schema.sql

# Run migration 002 (water_bodies table with MultiPolygon)
psql -h localhost -U postgres -d gis_engine -f database/migrations/002_update_water_bodies.sql
```

### Verify Table Exists

```bash
psql -h localhost -U postgres -d gis_engine -c "\d water_bodies"
```

Expected output should show:
- Table: water_bodies
- Columns: id, lake_name, category, lake_type, area_hectares, geom (GEOMETRY(MultiPolygon,4326)), objectid, created_at
- Indexes: idx_water_bodies_geom (GIST), idx_water_bodies_lake_name, idx_water_bodies_category, idx_water_bodies_lake_type

## 2. Import GeoJSON Data

### Set Environment Variables (if not in .env)

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=gis_engine
export DB_USER=postgres
export DB_PASSWORD=your_password
```

### Run Import Script

```bash
python import_water_bodies.py
```

Expected output:
```
2024-XX-XX XX:XX:XX - __main__ - INFO - Database connection pool created successfully
2024-XX-XX XX:XX:XX - __main__ - INFO - Loading GeoJSON from: d:\alstonair\water_bodies.geojson
2024-XX-XX XX:XX:XX - __main__ - INFO - Total features to import: XXXX
2024-XX-XX XX:XX:XX - __main__ - INFO - Cleared existing water_bodies data: DELETE X
2024-XX-XX XX:XX:XX - __main__ - INFO - Processing batch 1/XX
2024-XX-XX XX:XX:XX - __main__ - INFO - Progress: 100/XXXX features processed
...
2024-XX-XX XX:XX:XX - __main__ - INFO - ============================================================
2024-XX-XX XX:XX:XX - __main__ - INFO - Import Statistics:
2024-XX-XX XX:XX:XX - __main__ - INFO -   Total features: XXXX
2024-XX-XX XX:XX:XX - __main__ - INFO -   Successful imports: XXXX
2024-XX-XX XX:XX:XX - __main__ - INFO -   Failed imports: 0
2024-XX-XX XX:XX:XX - __main__ - INFO -   Null lake names: XXX
2024-XX-XX XX:XX:XX - __main__ - INFO -   Null geometries: 0
2024-XX-XX XX:XX:XX - __main__ - INFO - ============================================================
2024-XX-XX XX:XX:XX - __main__ - INFO - Import completed successfully
```

## 3. Verify Import

### Run Validation SQL

```bash
psql -h localhost -U postgres -d gis_engine -f database/validation_water_bodies.sql
```

Key validation queries to check manually:

```sql
-- Record count
SELECT COUNT(*) FROM water_bodies;

-- Check for invalid geometries
SELECT COUNT(*) FROM water_bodies WHERE geom IS NULL OR NOT ST_IsValid(geom);

-- Check SRID
SELECT COUNT(*) FROM water_bodies WHERE ST_SRID(geom) != 4326;

-- Check null lake names
SELECT COUNT(*) FROM water_bodies WHERE lake_name IS NULL;

-- Sample query - top 10 largest named lakes
SELECT lake_name, lake_type, category, area_hectares
FROM water_bodies
WHERE lake_name IS NOT NULL
ORDER BY area_hectares DESC NULLS LAST
LIMIT 10;
```

## 4. Start FastAPI Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 5. API Testing

### 5.1 Nearest Lake Endpoint

Get the nearest lake with buffer zone status.

**Endpoint:** `GET /api/gis/lake-nearest`

**Parameters:**
- `lat` (required): Latitude in decimal degrees
- `lng` (required): Longitude in decimal degrees

**Example Request:**

```bash
curl "http://localhost:8000/api/gis/lake-nearest?lat=12.9716&lng=77.5946"
```

**Expected Response:**
```json
{
  "id": 123,
  "lake_name": "Ulsoor Lake",
  "lake_type": "Tank",
  "category": "Water bodies",
  "area_hectares": 45.5,
  "distance_meters": 125.3,
  "buffer_status": "warning",
  "buffer_distance": 150
}
```

**Buffer Status Codes:**
- `blocked`: Distance ≤ 75m (NGT blocked zone - no construction allowed)
- `warning`: Distance 75-150m (NGT warning zone - restrictions apply)
- `safe`: Distance > 150m (Safe zone)

### 5.2 Lake Buffer Check Endpoint

Check if a point falls within a specified lake buffer zone.

**Endpoint:** `GET /api/gis/lake-buffer-check`

**Parameters:**
- `lat` (required): Latitude in decimal degrees
- `lng` (required): Longitude in decimal degrees
- `buffer_meters` (optional): Buffer distance in meters (default: 75)

**Example Request - 75m Buffer (NGT Blocked Zone):**

```bash
curl "http://localhost:8000/api/gis/lake-buffer-check?lat=12.9716&lng=77.5946&buffer_meters=75"
```

**Expected Response:**
```json
{
  "within_buffer": true,
  "buffer_meters": 75,
  "lakes_in_buffer": [
    {
      "id": 123,
      "lake_name": "Ulsoor Lake",
      "lake_type": "Tank",
      "category": "Water bodies",
      "area_hectares": 45.5,
      "distance_meters": 50.2,
      "within_buffer": true
    }
  ],
  "count": 1,
  "message": "Found 1 lake(s) within 75m buffer zone"
}
```

**Example Request - 150m Buffer (NGT Warning Zone):**

```bash
curl "http://localhost:8000/api/gis/lake-buffer-check?lat=12.9716&lng=77.5946&buffer_meters=150"
```

### 5.3 Lake Distance Endpoint

Calculate distance to a specific lake or all lakes.

**Endpoint:** `GET /api/gis/lake-distance`

**Parameters:**
- `lat` (required): Latitude in decimal degrees
- `lng` (required): Longitude in decimal degrees
- `lake_id` (optional): Specific lake ID to check distance to

**Example Request - Distance to All Lakes (Top 20):**

```bash
curl "http://localhost:8000/api/gis/lake-distance?lat=12.9716&lng=77.5946"
```

**Expected Response:**
```json
{
  "point": {
    "lat": 12.9716,
    "lng": 77.5946
  },
  "lakes": [
    {
      "id": 123,
      "lake_name": "Ulsoor Lake",
      "lake_type": "Tank",
      "category": "Water bodies",
      "area_hectares": 45.5,
      "distance_meters": 125.3
    },
    {
      "id": 456,
      "lake_name": "Sankey Tank",
      "lake_type": "Tank",
      "category": "Water bodies",
      "area_hectares": 32.1,
      "distance_meters": 890.5
    }
  ],
  "count": 20
}
```

**Example Request - Distance to Specific Lake:**

```bash
curl "http://localhost:8000/api/gis/lake-distance?lat=12.9716&lng=77.5946&lake_id=123"
```

**Expected Response:**
```json
{
  "lake_id": 123,
  "lake_name": "Ulsoor Lake",
  "lake_type": "Tank",
  "category": "Water bodies",
  "area_hectares": 45.5,
  "distance_meters": 125.3,
  "point": {
    "lat": 12.9716,
    "lng": 77.5946
  }
}
```

## 6. Test Coordinates for Bengaluru

Use these known Bengaluru coordinates for testing:

| Location | Latitude | Longitude | Description |
|----------|----------|-----------|-------------|
| MG Road | 12.9756 | 77.6066 | Central business district |
| Indiranagar | 12.9784 | 77.6408 | Residential area |
| Koramangala | 12.9352 | 77.6245 | IT hub area |
| Whitefield | 12.9698 | 77.7498 | IT corridor |
| Electronic City | 12.8452 | 77.6720 | Industrial area |

**Example Test:**

```bash
# Test near MG Road
curl "http://localhost:8000/api/gis/lake-nearest?lat=12.9756&lng=77.6066"

# Test buffer check near Indiranagar
curl "http://localhost:8000/api/gis/lake-buffer-check?lat=12.9784&lng=77.6408&buffer_meters=75"

# Test distance query near Koramangala
curl "http://localhost:8000/api/gis/lake-distance?lat=12.9352&lng=77.6245"
```

## 7. PostGIS Functions Used

The API endpoints use the following PostGIS functions:

- **ST_Distance**: Calculates distance between geometries in meters (using geography type)
- **ST_DWithin**: Finds geometries within a specified distance
- **ST_Contains**: Checks if a geometry contains another geometry
- **ST_Buffer**: Creates a buffer around a geometry
- **ST_SetSRID**: Sets the spatial reference system ID
- **ST_Point**: Creates a point geometry from coordinates
- **ST_IsValid**: Checks if a geometry is valid

## 8. Troubleshooting

### Import Fails

Check database connection:
```bash
psql -h localhost -U postgres -d gis_engine -c "SELECT version();"
```

Check PostGIS extension:
```bash
psql -h localhost -U postgres -d gis_engine -c "SELECT PostGIS_Version();"
```

### API Returns 404

Verify data exists:
```bash
psql -h localhost -U postgres -d gis_engine -c "SELECT COUNT(*) FROM water_bodies;"
```

Check geometry validity:
```bash
psql -h localhost -U postgres -d gis_engine -c "SELECT COUNT(*) FROM water_bodies WHERE geom IS NULL OR NOT ST_IsValid(geom);"
```

### Slow Query Performance

Check index usage:
```bash
psql -h localhost -U postgres -d gis_engine -c "SELECT * FROM pg_stat_user_indexes WHERE tablename = 'water_bodies';"
```

Rebuild index if needed:
```bash
psql -h localhost -U postgres -d gis_engine -c "REINDEX INDEX idx_water_bodies_geom;"
```

## 9. Performance Notes

- The import script processes features in batches of 100 for optimal performance
- Spatial queries use GIST indexes on the geom column
- API responses are cached using Redis (48-hour TTL by default)
- Buffer checks use ST_DWithin for efficient spatial filtering
