-- ============================================================================
-- Water Bodies Validation SQL Queries
-- ============================================================================
-- Description: Comprehensive validation queries for water_bodies table
--              Checks data integrity, geometry validity, and spatial constraints
-- ============================================================================

-- ============================================================================
-- 1. Record Count
-- ============================================================================
SELECT 'Total water bodies' AS metric, COUNT(*) AS count FROM water_bodies;

-- ============================================================================
-- 2. Invalid Geometries
-- ============================================================================
SELECT 'Invalid geometries (NULL or invalid)' AS metric, 
       COUNT(*) AS count 
FROM water_bodies 
WHERE geom IS NULL OR NOT ST_IsValid(geom);

-- Show details of invalid geometries
SELECT id, lake_name, lake_type, 
       CASE 
         WHEN geom IS NULL THEN 'NULL geometry'
         WHEN NOT ST_IsValid(geom) THEN 'Invalid geometry'
       END AS issue
FROM water_bodies 
WHERE geom IS NULL OR NOT ST_IsValid(geom)
LIMIT 10;

-- ============================================================================
-- 3. SRID Check
-- ============================================================================
SELECT 'Records with wrong SRID (not 4326)' AS metric, 
       COUNT(*) AS count 
FROM water_bodies 
WHERE ST_SRID(geom) != 4326;

-- Show details of wrong SRID records
SELECT id, lake_name, ST_SRID(geom) AS srid
FROM water_bodies 
WHERE ST_SRID(geom) != 4326
LIMIT 10;

-- ============================================================================
-- 4. Null Lake Names
-- ============================================================================
SELECT 'Records with NULL lake names' AS metric, 
       COUNT(*) AS count 
FROM water_bodies 
WHERE lake_name IS NULL;

-- ============================================================================
-- 5. Named vs Unnamed Water Bodies
-- ============================================================================
SELECT 
    CASE 
        WHEN lake_name IS NULL THEN 'Unnamed'
        ELSE 'Named'
    END AS name_status,
    COUNT(*) AS count
FROM water_bodies
GROUP BY name_status;

-- ============================================================================
-- 6. Lake Type Distribution
-- ============================================================================
SELECT 
    lake_type,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM water_bodies), 2) AS percentage
FROM water_bodies
WHERE lake_type IS NOT NULL
GROUP BY lake_type
ORDER BY count DESC;

-- ============================================================================
-- 7. Category Distribution
-- ============================================================================
SELECT 
    category,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM water_bodies), 2) AS percentage
FROM water_bodies
WHERE category IS NOT NULL
GROUP BY category
ORDER BY count DESC;

-- ============================================================================
-- 8. Area Statistics (in hectares)
-- ============================================================================
SELECT 
    'Minimum area (hectares)' AS metric,
    MIN(area_hectares) AS value
FROM water_bodies
WHERE area_hectares IS NOT NULL

UNION ALL

SELECT 
    'Maximum area (hectares)' AS metric,
    MAX(area_hectares) AS value
FROM water_bodies
WHERE area_hectares IS NOT NULL

UNION ALL

SELECT 
    'Average area (hectares)' AS metric,
    ROUND(AVG(area_hectares), 2) AS value
FROM water_bodies
WHERE area_hectares IS NOT NULL

UNION ALL

SELECT 
    'Total area (hectares)' AS metric,
    ROUND(SUM(area_hectares), 2) AS value
FROM water_bodies
WHERE area_hectares IS NOT NULL;

-- ============================================================================
-- 9. Geometry Type Verification
-- ============================================================================
SELECT 
    ST_GeometryType(geom) AS geometry_type,
    COUNT(*) AS count
FROM water_bodies
WHERE geom IS NOT NULL
GROUP BY ST_GeometryType(geom);

-- ============================================================================
-- 10. Sample Lake Query (Top 10 largest named lakes)
-- ============================================================================
SELECT 
    lake_name,
    lake_type,
    category,
    ROUND(area_hectares, 2) AS area_hectares,
    ROUND(ST_Area(geom::geography) / 10000.0, 2) AS calculated_area_hectares,
    ST_X(ST_Centroid(geom)) AS centroid_lon,
    ST_Y(ST_Centroid(geom)) AS centroid_lat
FROM water_bodies
WHERE lake_name IS NOT NULL
ORDER BY area_hectares DESC NULLS LAST
LIMIT 10;

-- ============================================================================
-- 11. Spatial Extent (Bounding Box)
-- ============================================================================
SELECT 
    'Bounding Box' AS metric,
    ST_XMin(extent) AS min_lon,
    ST_YMin(extent) AS min_lat,
    ST_XMax(extent) AS max_lon,
    ST_YMax(extent) AS max_lat
FROM (
    SELECT ST_Extent(geom) AS extent
    FROM water_bodies
    WHERE geom IS NOT NULL
) AS bbox;

-- ============================================================================
-- 12. Index Usage Check
-- ============================================================================
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched
FROM pg_stat_user_indexes
WHERE tablename = 'water_bodies'
ORDER BY idx_scan DESC;

-- ============================================================================
-- 13. Check for Duplicate OBJECTIDs
-- ============================================================================
SELECT 
    objectid,
    COUNT(*) AS count
FROM water_bodies
WHERE objectid IS NOT NULL
GROUP BY objectid
HAVING COUNT(*) > 1;

-- ============================================================================
-- 14. Lakes with Area Discrepancy (>10% difference)
-- ============================================================================
SELECT 
    lake_name,
    ROUND(area_hectares, 2) AS reported_area,
    ROUND(ST_Area(geom::geography) / 10000.0, 2) AS calculated_area,
    ROUND(
        ABS(area_hectares - (ST_Area(geom::geography) / 10000.0)) / 
        NULLIF(area_hectares, 0) * 100.0, 
        2
    ) AS percent_difference
FROM water_bodies
WHERE area_hectares IS NOT NULL
  AND geom IS NOT NULL
  AND ABS(area_hectares - (ST_Area(geom::geography) / 10000.0)) / 
      NULLIF(area_hectares, 0) > 0.1
ORDER BY percent_difference DESC
LIMIT 10;

-- ============================================================================
-- 15. Complete Validation Summary
-- ============================================================================
WITH stats AS (
    SELECT 
        (SELECT COUNT(*) FROM water_bodies) AS total_records,
        (SELECT COUNT(*) FROM water_bodies WHERE lake_name IS NULL) AS null_names,
        (SELECT COUNT(*) FROM water_bodies WHERE geom IS NULL OR NOT ST_IsValid(geom)) AS invalid_geom,
        (SELECT COUNT(*) FROM water_bodies WHERE ST_SRID(geom) != 4326) AS wrong_srid,
        (SELECT COUNT(*) FROM water_bodies WHERE lake_name IS NOT NULL) AS named_lakes,
        (SELECT COUNT(DISTINCT lake_type) FROM water_bodies WHERE lake_type IS NOT NULL) AS distinct_types,
        (SELECT ROUND(SUM(area_hectares), 2) FROM water_bodies WHERE area_hectares IS NOT NULL) AS total_area
)
SELECT 
    'Total Records' AS metric, total_records AS value FROM stats
UNION ALL
SELECT 'Named Lakes', named_lakes::text FROM stats
UNION ALL
SELECT 'Unnamed Lakes', null_names::text FROM stats
UNION ALL
SELECT 'Invalid Geometries', invalid_geom::text FROM stats
UNION ALL
SELECT 'Wrong SRID', wrong_srid::text FROM stats
UNION ALL
SELECT 'Distinct Lake Types', distinct_types::text FROM stats
UNION ALL
SELECT 'Total Area (hectares)', total_area::text FROM stats;
