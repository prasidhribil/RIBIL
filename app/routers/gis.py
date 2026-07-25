"""
 ============================================================================
 GIS Router - Spatial Survey Number Engine
 ============================================================================
 Description: FastAPI routes for spatial queries using PostGIS
 Focus: Bengaluru parcel lookup with point-in-polygon and nearest neighbor
 ============================================================================
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional
import logging
import httpx
import math
import json
from app.database import get_db
from app.cache import get_cache
from app.config import settings
from app.services.ngt_scraper import scrape_ngt_cases
from app.services.bhoomi_survey import resolve_survey_number, find_bhoomi_village_codes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gis", tags=["gis"])


# ============================================================================
# Pydantic Models
# ============================================================================

class SurveyNumberResponse(BaseModel):
    """Response model for survey number lookup."""
    success: bool
    survey_no: Optional[str] = None
    village: Optional[str] = None
    hobli: Optional[str] = None
    district: Optional[str] = None
    area_acres: Optional[float] = None
    message: Optional[str] = None
    village_verified: Optional[bool] = None
    village_source: Optional[str] = None
    kgis_village: Optional[str] = None


class LakeResponse(BaseModel):
    """Response model for lake lookup."""
    id: Optional[int] = None
    lake_name: Optional[str] = None
    lake_type: Optional[str] = None
    category: Optional[str] = None
    area_hectares: Optional[float] = None
    distance_meters: Optional[float] = None
    buffer_status: Optional[str] = None
    buffer_distance: Optional[float] = None


class SurveyParcelInfo(BaseModel):
    """Survey parcel information."""
    survey_no: Optional[str] = None
    village: Optional[str] = None
    hobli: Optional[str] = None
    district: Optional[str] = None
    area_acres: Optional[float] = None


class LakeInfo(BaseModel):
    """Nearest lake information."""
    lake_name: Optional[str] = None
    lake_type: Optional[str] = None
    distance_meters: Optional[float] = None


class BufferStatus(BaseModel):
    """Lake buffer status."""
    status: str  # "blocked", "warning", "safe"
    distance_meters: Optional[float] = None
    threshold_meters: Optional[float] = None


class CDPZoneInfo(BaseModel):
    """CDP zone information."""
    zone_type: Optional[str] = None
    zone_name: Optional[str] = None


class CourtCaseInfo(BaseModel):
    """Court case information."""
    case_number: Optional[str] = None
    case_type: Optional[str] = None
    status: Optional[str] = None
    filing_date: Optional[str] = None


class LandUseInfo(BaseModel):
    """Land use information from KGIS LULC service."""
    land_use: Optional[str] = None
    lulc_code: Optional[str] = None
    category: Optional[str] = None


class LandUseResponse(BaseModel):
    """Response model for land use lookup."""
    success: bool
    land_use: Optional[str] = None
    lulc_code: Optional[str] = None
    category: Optional[str] = None
    source: str = "KGIS LULC"
    message: Optional[str] = None


class PropertyProfileResponse(BaseModel):
    """Complete GIS property profile response."""
    survey_parcel: Optional[SurveyParcelInfo] = None
    nearest_lake: Optional[LakeInfo] = None
    buffer_status: Optional[BufferStatus] = None
    cdp_zone: Optional[CDPZoneInfo] = None
    court_cases: Optional[list[CourtCaseInfo]] = None
    land_use: Optional[LandUseInfo] = None


class KGISResponse(BaseModel):
    """Response model for KGIS survey number lookup."""
    success: bool
    district: Optional[str] = None
    taluk: Optional[str] = None
    hobli: Optional[str] = None
    village: Optional[str] = None
    survey_number: Optional[str] = None
    message: Optional[str] = None


class LandUseInfo(BaseModel):
    """Land use information from KGIS LULC service."""
    land_use: Optional[str] = None
    lulc_code: Optional[str] = None
    category: Optional[str] = None


class LandUseResponse(BaseModel):
    """Response model for land use lookup."""
    success: bool
    land_use: Optional[str] = None
    lulc_code: Optional[str] = None
    category: Optional[str] = None
    source: str = "KGIS LULC"
    message: Optional[str] = None


# ============================================================================
# API Routes
# ============================================================================

@router.get("/survey-number", response_model=SurveyNumberResponse)
async def get_survey_number(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude in decimal degrees"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude in decimal degrees"),
    district: Optional[str] = Query(None, description="District code (e.g., '20') for Bhoomi Maps"),
    taluk: Optional[str] = Query(None, description="Taluk code (e.g., '3') for Bhoomi Maps"),
    hobli: Optional[str] = Query(None, description="Hobli code (e.g., '5') for Bhoomi Maps"),
    village: Optional[str] = Query(None, description="Village code (e.g., '2') for Bhoomi Maps"),
    conn = Depends(get_db),
    cache = Depends(get_cache)
):
    """
    Get survey number for given coordinates using fallback strategy.

    Lookup order:
    1. Redis cache (gis_cache:survey-number:{lat}:{lng})
    2. KGIS live service
    3. Bhoomi Maps API (if village codes provided)
    4. PostGIS ST_Contains query on survey_parcels

    Args:
        latitude: Latitude between -90 and 90
        longitude: Longitude between -180 and 180
        district: Optional district code for Bhoomi Maps
        taluk: Optional taluk code for Bhoomi Maps
        hobli: Optional hobli code for Bhoomi Maps
        village: Optional village code for Bhoomi Maps

    Returns:
        Survey parcel information if found, or error message if all sources fail
    """
    # Round coordinates to 6 decimal places for cache key
    lat_rounded = round(latitude, 6)
    lng_rounded = round(longitude, 6)
    cache_key = f"gis_cache:survey-number:{lat_rounded}:{lng_rounded}"
    
    # Step 1: Check Redis cache
    try:
        cached_data = await cache.get_key(cache_key)
        if cached_data:
            logger.info(f"Cache HIT for survey number: {cache_key}")
            return SurveyNumberResponse(**json.loads(cached_data))
        else:
            logger.info(f"Cache MISS for survey number: {cache_key}")
    except Exception as e:
        logger.warning(f"Redis cache error: {e}")
    
    # Step 2: Try KGIS live service
    kgis_result = await _get_survey_number_from_kgis(latitude, longitude)
    if kgis_result:
        # Store in cache with 48-hour TTL
        try:
            await cache.set_key(cache_key, json.dumps(kgis_result.dict()), ttl=settings.CACHE_TTL_SECONDS)
            logger.info(f"Stored survey number in cache: {cache_key}")
        except Exception as e:
            logger.warning(f"Redis cache set error: {e}")
        
        return kgis_result
    
    # Step 3: Try Bhoomi Maps API
    # If village codes are not provided, auto-resolve them using location/resolve
    kgis_village_name = None
    if not (district and taluk and hobli and village):
        logger.info("Village codes not provided, resolving from location/resolve...")
        try:
            from app.routers.location import LocationRequest
            from app.routers.gis import get_admin_hierarchy_from_kgis
            
            # Call KGIS directly to get village name
            kgis_result = await get_admin_hierarchy_from_kgis(latitude, longitude, cache)
            if kgis_result:
                village_name = kgis_result.get("village")
                district_name = kgis_result.get("district")
                kgis_village_name = village_name  # Store for later use in response
                
                if village_name and district_name:
                    logger.info(f"Resolved location: village={village_name}, district={district_name}")
                    bhoomi_codes = await find_bhoomi_village_codes(village_name, district_name)
                    if bhoomi_codes:
                        district = bhoomi_codes["district"]
                        taluk = bhoomi_codes["taluk"]
                        hobli = bhoomi_codes["hobli"]
                        village = bhoomi_codes["village"]
                        logger.info(f"Auto-resolved Bhoomi codes: {bhoomi_codes}")
                    else:
                        logger.warning(f"Could not find Bhoomi codes for {village_name}")
        except Exception as e:
            logger.warning(f"Error resolving location for Bhoomi codes: {e}")
    
    # Try Bhoomi Maps API if we have village codes
    if district and taluk and hobli and village:
        logger.info(f"Trying Bhoomi Maps with village codes: district={district}, taluk={taluk}, hobli={hobli}, village={village}")
        bhoomi_result = await resolve_survey_number(
            latitude, longitude, district, taluk, hobli, village, cache
        )
        if bhoomi_result:
            # Update location cache with correct Bhoomi village name
            if bhoomi_result and bhoomi_result.get("village"):
                correct_village = bhoomi_result["village"]
                location_cache_key = f"gis_cache:resolve:{lat_rounded}:{lng_rounded}"
                cached = await cache.get_key(location_cache_key)
                if cached:
                    # Handle both old dict format and new JSON string format
                    if isinstance(cached, dict):
                        loc_data = cached
                    else:
                        loc_data = json.loads(cached)
                    loc_data["village"] = correct_village
                    loc_data["village_source"] = "bhoomi_verified"
                    await cache.set_key(location_cache_key, json.dumps(loc_data), ttl=86400)
                    logger.info(f"Updated location cache with Bhoomi village: {correct_village}")
            
            # Map Bhoomi result to SurveyNumberResponse with both village names
            response = SurveyNumberResponse(
                success=True,
                survey_no=bhoomi_result.get("survey_no"),
                village=bhoomi_result.get("village"),
                message=bhoomi_result.get("source")
            )
            # Add extra fields for village verification context
            response_dict = response.dict()
            response_dict["village_verified"] = bhoomi_result.get("village_verified", True)
            response_dict["village_source"] = "bhoomi_maps"
            if kgis_village_name:
                response_dict["kgis_village"] = kgis_village_name
            
            # Store in cache with 48-hour TTL
            try:
                await cache.set_key(cache_key, json.dumps(response_dict), ttl=settings.CACHE_TTL_SECONDS)
                logger.info(f"Stored survey number in cache: {cache_key}")
            except Exception as e:
                logger.warning(f"Redis cache set error: {e}")
            
            return SurveyNumberResponse(**response_dict)
    
    # Step 4: Fall back to PostGIS ST_Contains query
    postgis_result = await _get_survey_number_from_postgis(conn, longitude, latitude)
    if postgis_result:
        return postgis_result
    
    # Step 5: All sources failed
    logger.error(f"All survey number sources failed for coordinates: {latitude}, {longitude}")
    return SurveyNumberResponse(
        success=False,
        message="Survey number lookup failed - no data available from any source"
    )


async def _get_survey_number_from_kgis(latitude: float, longitude: float) -> Optional[SurveyNumberResponse]:
    """
    Get survey number from KGIS live service and map to SurveyNumberResponse schema.
    
    Two-step process:
    1. Call nearbyadminhierarchy with aoi=v to get village code
    2. Call surveyno with village code to get survey number
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        
    Returns:
        SurveyNumberResponse or None if KGIS fails
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://kgis.ksrsac.in/kgis/webapi.aspx",
            "Origin": "https://kgis.ksrsac.in"
        }
        
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            # Step 1: Get village code from nearbyadminhierarchy
            hierarchy_url = "https://kgis.ksrsac.in:9000/genericwebservices/ws/nearbyadminhierarchy"
            hierarchy_params = {
                "coordinates": f"{latitude},{longitude}",
                "distance": 10000,
                "type": "DD",
                "aoi": "v"  # Get village level
            }
            
            hierarchy_response = await client.get(hierarchy_url, params=hierarchy_params, headers=headers)
            hierarchy_response.raise_for_status()
            hierarchy_data = hierarchy_response.json()
            
            if not hierarchy_data or len(hierarchy_data) == 0:
                logger.warning(f"KGIS admin hierarchy returned empty for coordinates: {latitude}, {longitude}")
                return None
            
            # Get first village code
            village_code = hierarchy_data[0].get("villageCode")
            village_name = hierarchy_data[0].get("villageName")
            
            if not village_code:
                logger.warning(f"KGIS admin hierarchy missing village code: {hierarchy_data}")
                return None
            
            logger.info(f"Found village code: {village_code} ({village_name})")
            
            # Step 2: Get survey number using village code
            survey_url = "https://kgis.ksrsac.in:9000/genericwebservices/ws/surveyno"
            survey_params = {
                "coordinates": f"{latitude},{longitude}",
                "type": "DD",
                "distance": 5000,
                "villagecode": village_code  # Correct parameter name (lowercase)
            }
            
            survey_response = await client.get(survey_url, params=survey_params, headers=headers)
            survey_response.raise_for_status()
            survey_data = survey_response.json()
            
            # Check if response has 'surveynumber' key
            if 'surveynumber' not in survey_data:
                logger.warning(f"KGIS response missing 'surveynumber' key for village code: {village_code}")
                return None
            
            # Check if surveynumber array is not empty
            surveynumber_array = survey_data.get('surveynumber', [])
            if not surveynumber_array or len(surveynumber_array) == 0:
                logger.info(f"KGIS returned no survey numbers for village code {village_code} at coordinates {latitude},{longitude}")
                return None
            
            # Get first survey number result
            survey_record = surveynumber_array[0]
            
            # Map KGIS response to SurveyNumberResponse schema
            result = SurveyNumberResponse(
                success=True,
                survey_no=survey_record.get("surveyNo"),
                village=village_name,
                hobli=survey_record.get("hobli"),
                district=survey_record.get("district"),
                area_acres=survey_record.get("areaAcres")
            )
            
            logger.info(f"KGIS survey number found: {result.survey_no} for village {village_name}")
            return result
            
    except httpx.TimeoutException:
        logger.warning(f"KGIS API timeout for coordinates: {latitude}, {longitude}")
        return None
        
    except httpx.HTTPStatusError as e:
        logger.warning(f"KGIS API HTTP error: {e.response.status_code}")
        return None
        
    except httpx.RequestError as e:
        logger.warning(f"KGIS API request error: {e}")
        return None
        
    except Exception as e:
        logger.warning(f"KGIS API unexpected error: {e}")
        return None


async def _get_survey_number_from_postgis(conn, longitude: float, latitude: float) -> Optional[SurveyNumberResponse]:
    """
    Get survey number from PostGIS survey_parcels table.
    
    Args:
        conn: Database connection
        longitude: Longitude in decimal degrees
        latitude: Latitude in decimal degrees
        
    Returns:
        SurveyNumberResponse or None if no parcel found
    """
    try:
        # Check if survey_parcels table is empty
        check_empty_query = """
            SELECT COUNT(*) as count
            FROM survey_parcels
        """
        
        count_result = await conn.fetchrow(check_empty_query)
        
        if count_result["count"] == 0:
            logger.warning("Survey parcel dataset not yet loaded")
            return None
        
        # Query using ST_Contains for exact point-in-polygon match
        query = """
            SELECT
                survey_no,
                village,
                hobli,
                district,
                area_acres
            FROM survey_parcels
            WHERE ST_Contains(
                geom,
                ST_SetSRID(ST_Point($1, $2), 4326)
            )
            LIMIT 1
        """
        
        result = await conn.fetchrow(query, longitude, latitude)
        
        if result:
            response_data = {
                "success": True,
                "survey_no": result["survey_no"],
                "village": result["village"],
                "hobli": result["hobli"],
                "district": result["district"],
                "area_acres": result["area_acres"]
            }
            
            logger.info(f"PostGIS survey number found: {result['survey_no']}")
            return SurveyNumberResponse(**response_data)
        
        # No parcel found at this location
        logger.warning(f"No survey parcel found for coordinates: {latitude}, {longitude}")
        return None
        
    except Exception as e:
        logger.error(f"PostGIS query error: {e}")
        return None


async def _get_survey_number_from_bhoomi(
    latitude: float, 
    longitude: float,
    district: str,
    taluk: str,
    hobli: str,
    village: str,
    cache = None
) -> Optional[SurveyNumberResponse]:
    """
    Get survey number from Bhoomi Maps API using village codes.
    
    Fetches village parcels from Bhoomi Maps and performs point-in-polygon
    lookup to find the survey number for the given coordinates.
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        district: District code (e.g., "20")
        taluk: Taluk code (e.g., "3")
        hobli: Hobli code (e.g., "5")
        village: Village code (e.g., "2")
        cache: Optional cache dependency for caching results
        
    Returns:
        SurveyNumberResponse or None if Bhoomi fails
    """
    try:
        # Generate cache key based on village codes
        cache_key = f"bhoomi:village_parcels:{district}:{taluk}:{hobli}:{village}"
        
        # Check cache first if cache is provided
        if cache:
            try:
                cached_data = await cache.get_key(cache_key)
                if cached_data:
                    logger.info(f"Cache HIT for Bhoomi village parcels: {cache_key}")
                    # Parse cached GeoJSON and find survey number
                    return _find_survey_in_geojson(json.loads(cached_data), latitude, longitude)
                else:
                    logger.info(f"Cache MISS for Bhoomi village parcels: {cache_key}")
            except Exception as e:
                logger.warning(f"Redis cache error for Bhoomi: {e}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://bhoomi.karnataka.gov.in",
            "Origin": "https://bhoomi.karnataka.gov.in"
        }
        
        # Build Bhoomi Maps API URL with village codes
        bhoomi_url = settings.BHOOMI_MAPS_URL
        params = {
            "district": district,
            "taluk": taluk,
            "hobli": hobli,
            "village": village,
            "format": "geojson"
        }
        
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            response = await client.get(bhoomi_url, params=params, headers=headers)
            response.raise_for_status()
            
            # Parse JSON response
            raw_data = response.json()
            
            # Handle double-encoded GeoJSON (escaped JSON string inside JSON array)
            if isinstance(raw_data, list) and len(raw_data) > 0:
                first_item = raw_data[0]
                if isinstance(first_item, dict) and "GeoJson" in first_item:
                    # GeoJson field is a string that needs to be parsed again
                    geojson_str = first_item["GeoJson"]
                    if isinstance(geojson_str, str):
                        logger.info("Detected double-encoded GeoJSON, parsing nested string")
                        geojson_data = json.loads(geojson_str)
                    else:
                        geojson_data = geojson_str
                else:
                    geojson_data = raw_data
            else:
                geojson_data = raw_data
            
            # Cache the GeoJSON data with 24-hour TTL (86400 seconds)
            if cache:
                try:
                    await cache.set_key(cache_key, json.dumps(geojson_data), ttl=86400)
                    logger.info(f"Stored Bhoomi village parcels in cache: {cache_key}")
                except Exception as e:
                    logger.warning(f"Redis cache set error for Bhoomi: {e}")
            
            # Find survey number using point-in-polygon
            result = _find_survey_in_geojson(geojson_data, latitude, longitude)
            
            if result:
                logger.info(f"Bhoomi survey number found: {result.survey_no}")
                return result
            else:
                logger.info(f"No matching parcel found in Bhoomi data for coordinates: {latitude}, {longitude}")
                return None
            
    except httpx.TimeoutException:
        logger.warning(f"Bhoomi API timeout for coordinates: {latitude}, {longitude}")
        return None
        
    except httpx.HTTPStatusError as e:
        logger.warning(f"Bhoomi API HTTP error: {e.response.status_code}")
        return None
        
    except httpx.RequestError as e:
        logger.warning(f"Bhoomi API request error: {e}")
        return None
        
    except json.JSONDecodeError as e:
        logger.warning(f"Bhoomi API JSON decode error: {e}")
        return None
        
    except Exception as e:
        logger.warning(f"Bhoomi API unexpected error: {e}")
        return None


def _find_survey_in_geojson(geojson_data: dict, latitude: float, longitude: float) -> Optional[SurveyNumberResponse]:
    """
    Find survey number in GeoJSON data using point-in-polygon lookup.
    
    Args:
        geojson_data: GeoJSON FeatureCollection
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        
    Returns:
        SurveyNumberResponse or None if no matching parcel found
    """
    try:
        features = geojson_data.get("features", [])
        
        if not features:
            logger.warning("No features found in Bhoomi GeoJSON response")
            return None
        
        # Print first feature properties for debugging (check property names)
        if features:
            first_props = features[0].get("properties", {})
            logger.info(f"First feature properties: {list(first_props.keys())}")
        
        # Point-in-polygon check for each feature
        point = (longitude, latitude)  # GeoJSON uses (lon, lat) order
        
        for feature in features:
            geometry = feature.get("geometry")
            properties = feature.get("properties", {})
            
            if not geometry or geometry.get("type") != "Polygon":
                continue
            
            coordinates = geometry.get("coordinates", [])
            if not coordinates:
                continue
            
            # Check if point is inside polygon using ray casting algorithm
            polygon = coordinates[0]  # Exterior ring
            if _point_in_polygon(point, polygon):
                # Extract survey number from properties
                # Try common property name variations
                survey_no = (
                    properties.get("SurveyNo") or
                    properties.get("SURVEY_NO") or
                    properties.get("surveyno") or
                    properties.get("survey_no") or
                    properties.get("Survey_Number") or
                    properties.get("surveyNumber")
                )
                
                if survey_no:
                    return SurveyNumberResponse(
                        success=True,
                        survey_no=str(survey_no),
                        village=properties.get("village") or properties.get("Village"),
                        hobli=properties.get("hobli") or properties.get("Hobli"),
                        district=properties.get("district") or properties.get("District"),
                        area_acres=properties.get("area_acres") or properties.get("AreaAcres"),
                        message="Survey number from Bhoomi Maps"
                    )
        
        # No polygon contains the point
        logger.info(f"Point not found in any Bhoomi parcel polygon")
        return None
        
    except Exception as e:
        logger.error(f"Error parsing Bhoomi GeoJSON: {e}")
        return None


def _point_in_polygon(point: tuple, polygon: list) -> bool:
    """
    Ray casting algorithm to check if point is inside polygon.
    
    Args:
        point: (longitude, latitude) tuple
        polygon: List of [(longitude, latitude)] tuples forming polygon exterior
        
    Returns:
        True if point is inside polygon, False otherwise
    """
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside


@router.get("/lake-nearest", response_model=LakeResponse)
async def get_nearest_lake(
    lat: float = Query(..., ge=-90, le=90, description="Latitude in decimal degrees"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude in decimal degrees"),
    conn = Depends(get_db),
    cache = Depends(get_cache)
):
    """
    Get nearest lake to given coordinates using PostGIS spatial queries.
    
    Uses ST_Distance to find the nearest water body.
    Calculates buffer zone status based on NGT guidelines:
    - 0-75m: Blocked zone (no construction allowed)
    - 75-150m: Warning zone (restrictions apply)
    - >150m: Safe zone
    
    Args:
        lat: Latitude
        lng: longitude
        
    Returns:
        Nearest lake information with distance and buffer status
    """
    # Check cache first
    lat_rounded = round(lat, 6)
    lng_rounded = round(lng, 6)
    cache_key = f"gis_cache:lake-nearest:{lat_rounded}:{lng_rounded}"
    
    cached_result = await cache.get_key(cache_key)
    if cached_result:
        logger.info(f"Cache HIT for nearest lake: {cache_key}")
        return LakeResponse(**json.loads(cached_result))
    else:
        logger.info(f"Cache MISS for nearest lake: {cache_key}")
    
    # Query to find nearest lake with distance calculation
    query = """
        SELECT 
            id,
            lake_name,
            lake_type,
            category,
            area_hectares,
            ST_Distance(
                geom::geography,
                ST_SetSRID(ST_Point($1, $2), 4326)::geography
            ) as distance_meters
        FROM water_bodies
        WHERE geom IS NOT NULL
        ORDER BY distance_meters ASC
        LIMIT 1
    """
    
    result = await conn.fetchrow(query, lng, lat)
    
    if result:
        distance = result["distance_meters"]
        
        # Determine buffer status based on NGT guidelines
        if distance <= 75:
            buffer_status = "blocked"
            buffer_distance = 75
        elif distance <= 150:
            buffer_status = "warning"
            buffer_distance = 150
        else:
            buffer_status = "safe"
            buffer_distance = None
        
        response_data = {
            "id": result["id"],
            "lake_name": result["lake_name"],
            "lake_type": result["lake_type"],
            "category": result["category"],
            "area_hectares": result["area_hectares"],
            "distance_meters": round(distance, 2),
            "buffer_status": buffer_status,
            "buffer_distance": buffer_distance
        }
        
        logger.info(
            f"Nearest lake found: {result['lake_name'] or 'Unnamed'} "
            f"(distance: {distance:.2f}m, status: {buffer_status})"
        )
        
        # Cache the result
        await cache.set_key(cache_key, json.dumps(response_data), ttl=settings.CACHE_TTL_SECONDS)
        
        return LakeResponse(**response_data)
    
    # No lakes found in database
    logger.warning(f"No water bodies found for coordinates: {lat}, {lng}")
    raise HTTPException(
        status_code=404,
        detail="No water bodies found in the database for this location"
    )


@router.get("/lake-buffer-check")
async def check_lake_buffer(
    lat: float = Query(..., ge=-90, le=90, description="Latitude in decimal degrees"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude in decimal degrees"),
    buffer_meters: float = Query(75, ge=0, description="Buffer distance in meters (default: 75m NGT blocked zone)"),
    conn = Depends(get_db)
):
    """
    Check if a point falls within a lake buffer zone.
    
    Uses ST_DWithin to find all lakes within the specified buffer distance.
    Returns detailed information about all lakes in the buffer zone.
    
    Args:
        lat: Latitude
        lng: Longitude
        buffer_meters: Buffer distance in meters (default: 75 for NGT blocked zone)
        
    Returns:
        List of lakes within buffer zone with distances
    """
    # Query to find all lakes within buffer distance
    # Simplified: if distance <= buffer_meters, point is within buffer
    query = """
        SELECT 
            id,
            lake_name,
            lake_type,
            category,
            area_hectares,
            ST_Distance(
                geom::geography,
                ST_SetSRID(ST_Point($1, $2), 4326)::geography
            ) as distance_meters
        FROM water_bodies
        WHERE geom IS NOT NULL
          AND ST_DWithin(
              geom::geography,
              ST_SetSRID(ST_Point($1, $2), 4326)::geography,
              $3
          )
        ORDER BY distance_meters ASC
    """
    
    results = await conn.fetch(query, lng, lat, buffer_meters)
    
    if not results:
        return {
            "within_buffer": False,
            "buffer_meters": buffer_meters,
            "lakes_in_buffer": [],
            "message": f"No lakes found within {buffer_meters}m buffer zone"
        }
    
    # Format results
    lakes = []
    for result in results:
        distance = result["distance_meters"]
        lakes.append({
            "id": result["id"],
            "lake_name": result["lake_name"],
            "lake_type": result["lake_type"],
            "category": result["category"],
            "area_hectares": result["area_hectares"],
            "distance_meters": round(distance, 2),
            "within_buffer": distance <= buffer_meters
        })
    
    # Check if point is within any lake buffer
    within_any_buffer = any(lake["within_buffer"] for lake in lakes)
    
    response_data = {
        "within_buffer": within_any_buffer,
        "buffer_meters": buffer_meters,
        "lakes_in_buffer": lakes,
        "count": len(lakes),
        "message": f"Found {len(lakes)} lake(s) within {buffer_meters}m buffer zone"
    }
    
    logger.info(
        f"Buffer check: {len(lakes)} lake(s) within {buffer_meters}m, "
        f"within buffer: {within_any_buffer}"
    )
    
    return response_data


@router.get("/lake-distance")
async def get_lake_distance(
    lat: float = Query(..., ge=-90, le=90, description="Latitude in decimal degrees"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude in decimal degrees"),
    lake_id: Optional[int] = Query(None, description="Specific lake ID to check distance to"),
    conn = Depends(get_db)
):
    """
    Calculate distance from a point to a specific lake or all lakes.
    
    Uses ST_Distance to calculate precise distances.
    If lake_id is provided, returns distance to that specific lake.
    Otherwise, returns distances to all lakes sorted by proximity.
    
    Args:
        lat: Latitude
        lng: Longitude
        lake_id: Optional specific lake ID
        
    Returns:
        Distance information
    """
    if lake_id:
        # Query distance to specific lake
        query = """
            SELECT 
                id,
                lake_name,
                lake_type,
                category,
                area_hectares,
                ST_Distance(
                    geom::geography,
                    ST_SetSRID(ST_Point($1, $2), 4326)::geography
                ) as distance_meters
            FROM water_bodies
            WHERE id = $3
        """
        
        result = await conn.fetchrow(query, lng, lat, lake_id)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Lake with ID {lake_id} not found"
            )
        
        return {
            "lake_id": result["id"],
            "lake_name": result["lake_name"],
            "lake_type": result["lake_type"],
            "category": result["category"],
            "area_hectares": result["area_hectares"],
            "distance_meters": round(result["distance_meters"], 2),
            "point": {"lat": lat, "lng": lng}
        }
    else:
        # Query distances to all lakes (limited to top 20)
        query = """
            SELECT 
                id,
                lake_name,
                lake_type,
                category,
                area_hectares,
                ST_Distance(
                    geom::geography,
                    ST_SetSRID(ST_Point($1, $2), 4326)::geography
                ) as distance_meters
            FROM water_bodies
            WHERE geom IS NOT NULL
            ORDER BY distance_meters ASC
            LIMIT 20
        """
        
        results = await conn.fetch(query, lng, lat)
        
        lakes = []
        for result in results:
            lakes.append({
                "id": result["id"],
                "lake_name": result["lake_name"],
                "lake_type": result["lake_type"],
                "category": result["category"],
                "area_hectares": result["area_hectares"],
                "distance_meters": round(result["distance_meters"], 2)
            })
        
        return {
            "point": {"lat": lat, "lng": lng},
            "lakes": lakes,
            "count": len(lakes)
        }


# ============================================================================
# Service Functions for Property Profile
# ============================================================================

async def get_survey_parcel_info(conn, longitude: float, latitude: float) -> Optional[SurveyParcelInfo]:
    """
    Get survey parcel information using ST_Contains.
    
    Args:
        conn: Database connection
        longitude: Longitude
        latitude: Latitude
        
    Returns:
        SurveyParcelInfo or None if not found
    """
    try:
        query = """
            SELECT
                survey_no,
                village,
                hobli,
                district,
                area_acres
            FROM survey_parcels
            WHERE ST_Contains(
                geom,
                ST_SetSRID(ST_Point($1, $2), 4326)
            )
            LIMIT 1
        """
        result = await conn.fetchrow(query, longitude, latitude)
        
        if result:
            return SurveyParcelInfo(
                survey_no=result["survey_no"],
                village=result["village"],
                hobli=result["hobli"],
                district=result["district"],
                area_acres=result["area_acres"]
            )
        return None
    except Exception as e:
        logger.error(f"Error fetching survey parcel: {e}")
        return None


async def get_nearest_lake_info(conn, longitude: float, latitude: float) -> Optional[LakeInfo]:
    """
    Get nearest lake information using ST_Distance.
    
    Args:
        conn: Database connection
        longitude: Longitude
        latitude: Latitude
        
    Returns:
        LakeInfo or None if no lakes found
    """
    try:
        query = """
            SELECT
                lake_name,
                lake_type,
                ST_Distance(
                    geom::geography,
                    ST_SetSRID(ST_Point($1, $2), 4326)::geography
                ) as distance_meters
            FROM water_bodies
            WHERE geom IS NOT NULL
            ORDER BY distance_meters ASC
            LIMIT 1
        """
        result = await conn.fetchrow(query, longitude, latitude)
        
        if result:
            return LakeInfo(
                lake_name=result["lake_name"],
                lake_type=result["lake_type"],
                distance_meters=round(result["distance_meters"], 2)
            )
        return None
    except Exception as e:
        logger.error(f"Error fetching nearest lake: {e}")
        return None


async def get_buffer_status(distance_meters: Optional[float]) -> BufferStatus:
    """
    Determine buffer status based on distance to lake.
    
    Args:
        distance_meters: Distance to nearest lake in meters
        
    Returns:
        BufferStatus object
    """
    if distance_meters is None:
        return BufferStatus(status="safe", distance_meters=None, threshold_meters=None)
    
    if distance_meters <= 75:
        return BufferStatus(
            status="blocked",
            distance_meters=distance_meters,
            threshold_meters=75
        )
    elif distance_meters <= 150:
        return BufferStatus(
            status="warning",
            distance_meters=distance_meters,
            threshold_meters=150
        )
    else:
        return BufferStatus(
            status="safe",
            distance_meters=distance_meters,
            threshold_meters=None
        )


async def get_cdp_zone_info(conn, longitude: float, latitude: float) -> Optional[CDPZoneInfo]:
    """
    Get CDP zone information using ST_Contains.
    
    Args:
        conn: Database connection
        longitude: Longitude
        latitude: Latitude
        
    Returns:
        CDPZoneInfo or None if not found
    """
    try:
        query = """
            SELECT
                zone_type,
                zone_name
            FROM cdp_zones
            WHERE ST_Contains(
                geom,
                ST_SetSRID(ST_Point($1, $2), 4326)
            )
            LIMIT 1
        """
        result = await conn.fetchrow(query, longitude, latitude)
        
        if result:
            return CDPZoneInfo(
                zone_type=result["zone_type"],
                zone_name=result["zone_name"]
            )
        return None
    except Exception as e:
        logger.error(f"Error fetching CDP zone: {e}")
        return None


async def get_court_cases(conn, survey_no: Optional[str]) -> list[CourtCaseInfo]:
    """
    Get court cases for a survey number.
    
    Args:
        conn: Database connection
        survey_no: Survey number
        
    Returns:
        List of CourtCaseInfo objects
    """
    if not survey_no:
        return []
    
    try:
        query = """
            SELECT
                case_number,
                case_type,
                status,
                filing_date
            FROM court_cases
            WHERE survey_no = $1
        """
        results = await conn.fetch(query, survey_no)
        
        court_cases = []
        for result in results:
            court_cases.append(CourtCaseInfo(
                case_number=result["case_number"],
                case_type=result["case_type"],
                status=result["status"],
                filing_date=result["filing_date"].isoformat() if result["filing_date"] else None
            ))
        
        return court_cases
    except Exception as e:
        logger.error(f"Error fetching court cases: {e}")
        return []


# ============================================================================
# Property Profile Endpoint
# ============================================================================

@router.get("/property-profile", response_model=PropertyProfileResponse)
async def get_property_profile(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude in decimal degrees"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude in decimal degrees"),
    conn = Depends(get_db)
):
    """
    Get complete GIS property profile for a coordinate.
    
    Aggregates information from multiple data sources:
    - Survey parcel information (ST_Contains)
    - Nearest lake information (ST_Distance)
    - Lake buffer status (blocked/warning/safe)
    - CDP zone information (ST_Contains)
    - Court cases for the survey number
    - Land use information from KGIS LULC service
    
    Args:
        latitude: Latitude between -90 and 90
        longitude: Longitude between -180 and 180
        
    Returns:
        Complete property profile with all available GIS information
    """
    logger.info(f"Property profile request for: {latitude}, {longitude}")
    
    # Fetch all data sources in parallel
    survey_parcel = await get_survey_parcel_info(conn, longitude, latitude)
    nearest_lake = await get_nearest_lake_info(conn, longitude, latitude)
    cdp_zone = await get_cdp_zone_info(conn, longitude, latitude)
    land_use = await get_landuse_info(latitude, longitude)
    
    # Calculate buffer status based on lake distance
    buffer_status = await get_buffer_status(nearest_lake.distance_meters if nearest_lake else None)
    
    # Fetch court cases if survey number is available
    survey_no = survey_parcel.survey_no if survey_parcel else None
    court_cases = await get_court_cases(conn, survey_no)
    
    response = PropertyProfileResponse(
        survey_parcel=survey_parcel,
        nearest_lake=nearest_lake,
        buffer_status=buffer_status,
        cdp_zone=cdp_zone,
        court_cases=court_cases if court_cases else None,
        land_use=land_use
    )
    
    logger.info(f"Property profile returned: survey={survey_parcel.survey_no if survey_parcel else None}, "
                f"lake={nearest_lake.lake_name if nearest_lake else None}, "
                f"zone={cdp_zone.zone_type if cdp_zone else None}, "
                f"land_use={land_use.land_use if land_use else None}")
    
    return response


# ============================================================================
# KGIS LULC Service Functions
# ============================================================================

# LULC Code to Category Mapping
LULC_CATEGORY_MAP = {
    # Built-up Areas
    "BUUR": "Built-up",
    "BUUC": "Built-up",
    "BUUP": "Built-up",
    "BURU": "Built-up",
    "BURV": "Built-up",
    "BURM": "Built-up",
    "BURH": "Built-up",
    "BUMN": "Built-up",
    "BUTP": "Built-up",
    # Agriculture
    "AGCR": "Agriculture",
    "AGPL": "Agriculture",
    "AGAQ": "Agriculture",
    # Forest
    "FRDE": "Forest",
    "FRPL": "Forest",
    "FRMG": "Forest",
    # Wasteland
    "GRGR": "Wasteland",
    "WLST": "Wasteland",
    "WLGU": "Wasteland",
    "WLWL": "Wasteland",
    "WLSD": "Wasteland",
    "WLSP": "Wasteland",
    "WLSA": "Wasteland",
    "WLBR": "Wasteland",
    # Water Bodies
    "WBRS": "Water",
    "WBCN": "Water",
    "WBRE": "Water",
    "WBTA": "Water",
    "WBLP": "Water",
}


async def get_landuse_info(latitude: float, longitude: float) -> Optional[LandUseInfo]:
    """
    Get land use information from KGIS ArcGIS REST service.
    
    Performs point-in-polygon lookup using the provided coordinates.
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        
    Returns:
        LandUseInfo or None if no matching polygon found
    """
    try:
        # Build ArcGIS REST query parameters
        params = {
            "where": "1=1",
            "geometry": f"{longitude},{latitude}",
            "geometryType": "esriGeometryPoint",
            "spatialReference": {"wkid": 4326},
            "inSR": 4326,
            "outSR": 4326,
            "outFields": "NR.DBO.LULC.LULCCode,NR.DBO.LULC_Tbl.LULC_Description",
            "returnGeometry": False,
            "f": "json"
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://kgis.ksrsac.in/kgis/webapi.aspx",
            "Origin": "https://kgis.ksrsac.in"
        }
        
        # Call KGIS ArcGIS REST service with timeout and browser headers
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            response = await client.get(settings.KGIS_LULC_URL, params=params, headers=headers)
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            # Check if any features were found
            features = data.get("features", [])
            if not features:
                logger.info(f"No LULC polygon found for coordinates: {latitude}, {longitude}")
                return None
            
            # Extract LULC information from first feature
            feature = features[0]
            attributes = feature.get("attributes", {})
            
            lulc_code = attributes.get("NR.DBO.LULC.LULCCode")
            land_use = attributes.get("NR.DBO.LULC_Tbl.LULC_Description")
            
            # Map LULC code to category
            category = LULC_CATEGORY_MAP.get(lulc_code, "Other")
            
            logger.info(f"LULC found: {lulc_code} - {land_use} ({category})")
            
            return LandUseInfo(
                land_use=land_use,
                lulc_code=lulc_code,
                category=category
            )
            
    except httpx.TimeoutException:
        logger.error(f"KGIS LULC API timeout for coordinates: {latitude}, {longitude}")
        return None
        
    except httpx.HTTPStatusError as e:
        logger.error(f"KGIS LULC API HTTP error: {e.response.status_code}")
        return None
        
    except httpx.RequestError as e:
        logger.error(f"KGIS LULC API request error: {e}")
        return None
        
    except Exception as e:
        logger.error(f"KGIS LULC API unexpected error: {e}")
        return None


# ============================================================================
# CDP Zone from LULC Mapping Function
# ============================================================================

async def get_cdp_zone_from_lulc(lat: float, lng: float, cache = None) -> Optional[dict]:
    """
    Get CDP zone information by mapping KGIS LULC category to CDP zone types.
    
    Args:
        lat: Latitude in decimal degrees
        lng: Longitude in decimal degrees
        cache: Optional cache dependency for caching results
        
    Returns:
        Dictionary with zone_type, zone_name, lulc_code, source, in_zone or None
    """
    # Round coordinates to 6 decimal places for cache key
    lat_rounded = round(lat, 6)
    lng_rounded = round(lng, 6)
    cache_key = f"gis_cache:cdp-zone:{lat_rounded}:{lng_rounded}"
    
    # Check cache first if cache is provided
    if cache:
        try:
            cached_data = await cache.get_key(cache_key)
            if cached_data:
                logger.info(f"Cache HIT for CDP zone: {cache_key}")
                return json.loads(cached_data)
            else:
                logger.info(f"Cache MISS for CDP zone: {cache_key}")
        except Exception as e:
            logger.warning(f"Redis cache error for CDP zone: {e}")
    
    # Call existing get_landuse_info function
    landuse_info = await get_landuse_info(lat, lng)
    
    if not landuse_info:
        logger.warning(f"No LULC data found for coordinates: {lat}, {lng}")
        return None
    
    # Map LULC category to CDP zone_type
    lulc_code = landuse_info.lulc_code
    category = landuse_info.category
    land_use = landuse_info.land_use
    
    if category == "Built-up":
        if lulc_code and lulc_code.startswith("BUUR"):
            zone_type = "Residential"
        elif lulc_code and lulc_code.startswith("BUUC"):
            zone_type = "Commercial"
        elif lulc_code and lulc_code.startswith("BUUP"):
            zone_type = "Public & Semi-Public"
        elif lulc_code and lulc_code.startswith("BUTP"):
            zone_type = "Transport"
        else:
            zone_type = "Mixed Use"
    elif category == "Agriculture":
        zone_type = "Agriculture Zone"
    elif category == "Forest":
        zone_type = "Green Belt"
    elif category == "Wasteland":
        zone_type = "Green Belt"
    elif category == "Water":
        zone_type = "Water Body / Buffer Zone"
    else:
        zone_type = "Unclassified"
    
    result = {
        "zone_type": zone_type,
        "zone_name": land_use,
        "lulc_code": lulc_code,
        "source": "kgis_lulc",
        "in_zone": True
    }
    
    logger.info(f"CDP zone mapped from LULC: {zone_type} (from {category}/{lulc_code})")
    
    # Cache the result if cache is provided
    if cache:
        try:
            await cache.set_key(cache_key, json.dumps(result), ttl=settings.CACHE_TTL_SECONDS)
            logger.info(f"Stored CDP zone in cache: {cache_key}")
        except Exception as e:
            logger.warning(f"Redis cache set error for CDP zone: {e}")
    
    return result


# ============================================================================
# AAI Airport Zone Analytical Function
# ============================================================================

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points using Haversine formula.
    
    Args:
        lat1, lon1: Latitude and longitude of first point in decimal degrees
        lat2, lon2: Latitude and longitude of second point in decimal degrees
        
    Returns:
        Distance in meters
    """
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi/2)**2 + 
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2)
    return 2 * R * math.asin(math.sqrt(a))


async def get_aai_zone_info(lat: float, lng: float, cache = None) -> dict:
    """
    Get AAI airport restriction zone information using analytical distance calculation.
    
    Calculates distance to both KIAL (BIAL) and HAL airports and determines
    restriction zone based on distance to nearest airport.
    
    Args:
        lat: Latitude in decimal degrees
        lng: Longitude in decimal degrees
        cache: Optional cache dependency for caching results
        
    Returns:
        Dictionary with airport restriction information
    """
    # Round coordinates to 6 decimal places for cache key
    lat_rounded = round(lat, 6)
    lng_rounded = round(lng, 6)
    cache_key = f"gis_cache:aai-zone:{lat_rounded}:{lng_rounded}"
    
    # Check cache first if cache is provided
    if cache:
        try:
            cached_data = await cache.get_key(cache_key)
            if cached_data:
                logger.info(f"Cache HIT for AAI zone: {cache_key}")
                return json.loads(cached_data)
            else:
                logger.info(f"Cache MISS for AAI zone: {cache_key}")
        except Exception as e:
            logger.warning(f"Redis cache error for AAI zone: {e}")
    
    # Calculate distances to both airports
    dist_kial = haversine(lat, lng, settings.KIAL_LAT, settings.KIAL_LNG)
    dist_hal = haversine(lat, lng, settings.HAL_LAT, settings.HAL_LNG)
    
    # Determine nearest airport
    if dist_kial <= dist_hal:
        nearest_airport = settings.KIAL_NAME
        distance_meters = dist_kial
    else:
        nearest_airport = settings.HAL_NAME
        distance_meters = dist_hal
    
    distance_km = distance_meters / 1000
    
    # Determine restriction based on distance
    if distance_km <= 2.5:
        restriction_type = "Runway Protection Zone"
        height_limit_meters = 0
        is_in_restriction_zone = True
    elif distance_km <= 4:
        restriction_type = "Inner Horizontal Surface"
        height_limit_meters = 45
        is_in_restriction_zone = True
    elif distance_km <= 8:
        restriction_type = "Conical Surface"
        height_limit_meters = 100
        is_in_restriction_zone = True
    elif distance_km <= 15:
        restriction_type = "Outer Horizontal Surface"
        height_limit_meters = 150
        is_in_restriction_zone = True
    else:
        restriction_type = None
        height_limit_meters = None
        is_in_restriction_zone = False
    
    result = {
        "is_in_restriction_zone": is_in_restriction_zone,
        "restriction_type": restriction_type or "None",
        "airport_name": nearest_airport,
        "distance_to_airport_km": round(distance_km, 2),
        "height_limit_meters": height_limit_meters,
        "note": "Approximate distance-based estimate. Verify with AAI NOC application for actual height clearance certificate.",
        "source": "analytical"
    }
    
    logger.info(f"AAI zone calculated: {restriction_type or 'None'} at {distance_km:.2f}km from {nearest_airport}")
    
    # Cache the result if cache is provided (7 days TTL)
    if cache:
        try:
            await cache.set_key(cache_key, json.dumps(result), ttl=604800)  # 7 days = 604800 seconds
            logger.info(f"Stored AAI zone in cache: {cache_key}")
        except Exception as e:
            logger.warning(f"Redis cache set error for AAI zone: {e}")
    
    return result


# ============================================================================
# KGIS Admin Hierarchy Service Functions
# ============================================================================

async def get_admin_hierarchy_from_kgis(lat: float, lng: float, cache = None) -> Optional[dict]:
    """
    Get administrative hierarchy (district, taluk, hobli, village) from KGIS nearbyadminhierarchy endpoint.
    
    Args:
        lat: Latitude in decimal degrees
        lng: Longitude in decimal degrees
        cache: Optional cache dependency for caching results
        
    Returns:
        Dictionary with district, taluk, hobli, village if successful, None on failure
    """
    # Round coordinates to 6 decimal places for cache key
    lat_rounded = round(lat, 6)
    lng_rounded = round(lng, 6)
    cache_key = f"gis_cache:admin-hierarchy:{lat_rounded}:{lng_rounded}"
    
    # Check cache first if cache is provided
    if cache:
        try:
            cached_data = await cache.get_key(cache_key)
            if cached_data:
                logger.info(f"Cache HIT for admin hierarchy: {cache_key}")
                return json.loads(cached_data)
            else:
                logger.info(f"Cache MISS for admin hierarchy: {cache_key}")
        except Exception as e:
            logger.warning(f"Redis cache error for admin hierarchy: {e}")
    
    try:
        # Build KGIS API URL with query parameters
        # Call both aoi=d (district) and aoi=v (village) to get complete hierarchy
        params_d = {
            "coordinates": f"{lat},{lng}",
            "distance": 10000,
            "type": "DD",
            "aoi": "d"
        }
        params_v = {
            "coordinates": f"{lat},{lng}",
            "distance": 10000,
            "type": "DD",
            "aoi": "v"
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://kgis.ksrsac.in/kgis/webapi.aspx",
            "Origin": "https://kgis.ksrsac.in"
        }
        
        logger.info(f"DEBUG: Calling KGIS API with params_d and params_v")
        
        # Call KGIS API with timeout and browser headers
        async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
            # Call aoi=d for district
            response_d = await client.get(settings.KGIS_ADMIN_URL, params=params_d, headers=headers)
            logger.info(f"DEBUG: KGIS API aoi=d response status: {response_d.status_code}")
            response_d.raise_for_status()
            kgis_data_d = response_d.json()
            logger.info(f"DEBUG: KGIS API aoi=d response data: {kgis_data_d}")
            
            # Call aoi=v for village
            response_v = await client.get(settings.KGIS_ADMIN_URL, params=params_v, headers=headers)
            logger.info(f"DEBUG: KGIS API aoi=v response status: {response_v.status_code}")
            response_v.raise_for_status()
            kgis_data_v = response_v.json()
            logger.info(f"DEBUG: KGIS API aoi=v raw response: {kgis_data_v}")
            if kgis_data_v and len(kgis_data_v) > 0:
                logger.info(f"DEBUG: First village item keys: {list(kgis_data_v[0].keys())}")
                logger.info(f"DEBUG: First village item full: {kgis_data_v[0]}")
            
            # Parse district from aoi=d response
            district = None
            district_code = None
            if kgis_data_d and isinstance(kgis_data_d, list) and len(kgis_data_d) > 0:
                for item in kgis_data_d:
                    if "Bengaluru (Urban)" in item.get("districtName", ""):
                        district = item["districtName"]
                        district_code = item.get("districtCode")
                        break
                    elif district is None:
                        district = item["districtName"]
                        district_code = item.get("districtCode")
            
            # Parse village from aoi=v response (first village is closest)
            village = None
            if kgis_data_v and isinstance(kgis_data_v, list) and len(kgis_data_v) > 0:
                # Try multiple possible field names for village
                village = (kgis_data_v[0].get("villageName") or 
                          kgis_data_v[0].get("VILLAGE_NAME") or
                          kgis_data_v[0].get("villagename") or
                          kgis_data_v[0].get("VillageName") or
                          kgis_data_v[0].get("VILLAGE"))
            
            if not district:
                logger.warning(f"KGIS admin hierarchy missing district")
                return None
            
            result = {
                "district": district,
                "districtCode": district_code,
                "taluk": None,  # KGIS doesn't provide taluk/hobli in these endpoints
                "hobli": None,
                "village": village,
                "confidence_score": 0.90,
                "source": "kgis"
            }
            
            logger.info(f"KGIS admin hierarchy found: district={result.get('district')}, "
                       f"taluk={result.get('taluk')}, hobli={result.get('hobli')}, "
                       f"village={result.get('village')}, source={result.get('source')}, confidence={result.get('confidence_score')}")
            
            # Cache the result if cache is provided
            if cache:
                try:
                    await cache.set_key(cache_key, json.dumps(result), ttl=settings.CACHE_TTL_SECONDS)
                    logger.info(f"Stored admin hierarchy in cache: {cache_key}")
                except Exception as e:
                    logger.warning(f"Redis cache set error for admin hierarchy: {e}")
            
            return result
            
    except httpx.TimeoutException:
        logger.warning(f"KGIS admin hierarchy API timeout for coordinates: {lat}, {lng}")
        return None
        
    except httpx.HTTPStatusError as e:
        logger.warning(f"KGIS admin hierarchy API HTTP error: {e.response.status_code}")
        return None
        
    except httpx.RequestError as e:
        logger.warning(f"KGIS admin hierarchy API request error: {e}")
        return None
        
    except Exception as e:
        logger.warning(f"KGIS admin hierarchy API unexpected error: {e}")
        return None


# ============================================================================
# KGIS Survey Number Endpoint
# ============================================================================

@router.get("/survey-number-kgis", response_model=KGISResponse)
async def get_survey_number_kgis(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude in decimal degrees"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude in decimal degrees")
):
    """
    Get survey number from official KGIS web service.
    
    Calls the Karnataka GIS (KGIS) survey number API to retrieve
    survey information for given coordinates.
    
    Args:
        latitude: Latitude between -90 and 90
        longitude: Longitude between -180 and 180
        
    Returns:
        Survey information from KGIS including district, taluk, hobli, village, and survey number
    """
    logger.info(f"KGIS survey number request for: {latitude}, {longitude}")
    
    try:
        # Build KGIS API URL with query parameters
        kgis_url = f"{settings.KGIS_API_URL}?latitude={latitude}&longitude={longitude}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://kgis.ksrsac.in/kgis/webapi.aspx",
            "Origin": "https://kgis.ksrsac.in"
        }
        
        # Call KGIS API with timeout and browser headers
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            response = await client.get(kgis_url, headers=headers)
            response.raise_for_status()
            
            # Parse JSON response
            kgis_data = response.json()
            
            # Extract required fields from KGIS response
            # Note: Adjust field names based on actual KGIS API response structure
            result = KGISResponse(
                success=True,
                district=kgis_data.get("district"),
                taluk=kgis_data.get("taluk"),
                hobli=kgis_data.get("hobli"),
                village=kgis_data.get("village"),
                survey_number=kgis_data.get("survey_number")
            )
            
            logger.info(f"KGIS survey number found: {result.survey_number}")
            return result
            
    except httpx.TimeoutException:
        logger.error(f"KGIS API timeout for coordinates: {latitude}, {longitude}")
        return KGISResponse(
            success=False,
            message="KGIS service timeout - request took too long"
        )
        
    except httpx.HTTPStatusError as e:
        logger.error(f"KGIS API HTTP error: {e.response.status_code}")
        return KGISResponse(
            success=False,
            message=f"KGIS service returned HTTP {e.response.status_code}"
        )
        
    except httpx.RequestError as e:
        logger.error(f"KGIS API request error: {e}")
        return KGISResponse(
            success=False,
            message="KGIS service unavailable - connection error"
        )
        
    except Exception as e:
        logger.error(f"KGIS API unexpected error: {e}")
        return KGISResponse(
            success=False,
            message="KGIS service error - unable to process request"
        )


# ============================================================================
# Land Use Endpoint
# ============================================================================

@router.get("/landuse", response_model=LandUseResponse)
async def get_landuse(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude in decimal degrees"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude in decimal degrees")
):
    """
    Get land use information from KGIS ArcGIS REST LULC service.
    
    Performs point-in-polygon lookup using the provided coordinates
    to determine land use classification.
    
    Args:
        latitude: Latitude between -90 and 90
        longitude: Longitude between -180 and 180
        
    Returns:
        Land use information including land_use, lulc_code, category, and source
    """
    logger.info(f"Land use request for: {latitude}, {longitude}")
    
    land_use_info = await get_landuse_info(latitude, longitude)
    
    if land_use_info:
        return LandUseResponse(
            success=True,
            land_use=land_use_info.land_use,
            lulc_code=land_use_info.lulc_code,
            category=land_use_info.category,
            source="KGIS LULC"
        )
    else:
        return LandUseResponse(
            success=False,
            message="No land use polygon found at this location"
        )


# ============================================================================
# Court Cases Endpoint
# ============================================================================

@router.get("/court-cases")
async def get_court_cases_endpoint(
    village: str = Query(..., description="Village name to search for NGT cases"),
    conn = Depends(get_db)
):
    """
    Get NGT court cases for a village.
    
    First checks the court_cases table for existing data.
    If no data found, scrapes NGT Southern Zone website for cases.
    Scraped results are inserted into the database for future use.
    
    Args:
        village: Village name to search
        
    Returns:
        List of court cases or empty list with message
    """
    logger.info(f"Court cases request for village: {village}")
    
    # First, check court_cases table
    try:
        query = """
            SELECT 
                case_number,
                village,
                survey_no,
                violation_type,
                status,
                order_date,
                description
            FROM court_cases
            WHERE village ILIKE $1
            LIMIT 20
        """
        results = await conn.fetch(query, f"%{village}%")
        
        if results:
            cases = [
                {
                    "case_number": row["case_number"],
                    "village": row["village"],
                    "survey_no": row["survey_no"],
                    "violation_type": row["violation_type"],
                    "status": row["status"],
                    "order_date": str(row["order_date"]) if row["order_date"] else None,
                    "description": row["description"]
                }
                for row in results
            ]
            logger.info(f"Found {len(cases)} court cases in database for {village}")
            return {"cases": cases, "source": "database"}
    except Exception as e:
        logger.error(f"Error querying court_cases table: {e}")
    
    # If table is empty for this village, scrape NGT
    logger.info(f"No court cases found in database, scraping NGT for {village}")
    scraped_cases = await scrape_ngt_cases(village)
    
    if scraped_cases:
        # Insert scraped cases into database
        try:
            for case in scraped_cases:
                insert_query = """
                    INSERT INTO court_cases (
                        case_number, village, survey_no, violation_type, 
                        status, order_date, description
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (case_number) DO NOTHING
                """
                await conn.execute(
                    insert_query,
                    case["case_number"],
                    case["village"],
                    case["survey_no"],
                    case["violation_type"],
                    case["status"],
                    case["order_date"],
                    case["description"]
                )
            logger.info(f"Inserted {len(scraped_cases)} scraped cases into database")
        except Exception as e:
            logger.error(f"Error inserting scraped cases: {e}")
        
        return {"cases": scraped_cases, "source": "ngt_scraper"}
    
    # If scraper also returns nothing
    return {"cases": [], "message": "No NGT cases found for this village"}
