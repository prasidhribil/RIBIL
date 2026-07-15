"""
 ============================================================================
 Location Router - Reverse Geocoding APIs
 ============================================================================
 Description: FastAPI routes for location resolution and administrative hierarchy
 Focus: Bengaluru Urban and Rural districts with Google/Nominatim fallback
 ============================================================================
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import httpx
import logging
from app.database import get_db
from app.cache import get_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/location", tags=["location"])


# ============================================================================
# Pydantic Models
# ============================================================================

class LocationRequest(BaseModel):
    """Request model for location resolution."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    lng: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")


class LocationResponse(BaseModel):
    """Response model for location resolution."""
    district: Optional[str] = None
    taluk: Optional[str] = None
    hobli: Optional[str] = None
    village: Optional[str] = None
    districtCode: Optional[str] = None
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence score 0-1")
    source: str = Field(..., description="Data source: google, nominatim, kgis, or combined")


class HobliListResponse(BaseModel):
    """Response model for hobli list."""
    hoblis: list[str] = Field(default_factory=list, description="List of hoblis")


# ============================================================================
# Helper Functions
# ============================================================================

async def query_google_geocoding(lat: float, lng: float, api_key: str) -> Dict[str, Any]:
    """
    Query Google Geocoding API for reverse geocoding.
    
    Args:
        lat: Latitude
        lng: Longitude
        api_key: Google Maps API key
        
    Returns:
        Parsed address components from Google API
    """
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "latlng": f"{lat},{lng}",
        "key": api_key,
        "result_type": "administrative_area_level_1|administrative_area_level_2|administrative_area_level_3|locality"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data["status"] != "OK":
            raise HTTPException(status_code=400, detail=f"Google API error: {data['status']}")
        
        return data["results"][0] if data["results"] else None


def parse_google_address_components(result: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Parse Google Geocoding address components for administrative hierarchy.
    Extracts district, taluk, hobli, and village from address_components.
    
    Args:
        result: Google API result object
        
    Returns:
        Dictionary with extracted administrative levels
    """
    components = result.get("address_components", [])
    
    extracted = {
        "district": None,
        "taluk": None,
        "hobli": None,
        "village": None
    }
    
    for component in components:
        types = component.get("types", [])
        long_name = component.get("long_name", "")
        short_name = component.get("short_name", "")
        
        # District (administrative_area_level_2 or 3 for India)
        if "administrative_area_level_2" in types or "administrative_area_level_3" in types:
            # Check for Bengaluru districts
            if "Bengaluru" in long_name or "Bangalore" in long_name:
                extracted["district"] = long_name
            elif extracted["district"] is None:
                extracted["district"] = long_name
        
        # Taluk (sub-district)
        elif "administrative_area_level_3" in types and extracted["taluk"] is None:
            extracted["taluk"] = long_name
        
        # Hobli (smaller administrative unit - may not be in Google)
        elif "sublocality" in types or "locality" in types:
            if extracted["hobli"] is None:
                extracted["hobli"] = long_name
        
        # Village (smallest unit)
        elif "neighborhood" in types or "premise" in types:
            if extracted["village"] is None:
                extracted["village"] = long_name
    
    return extracted


async def query_nominatim_geocoding(lat: float, lng: float) -> Dict[str, Any]:
    """
    Query OpenStreetMap Nominatim API as fallback for reverse geocoding.
    
    Args:
        lat: Latitude
        lng: Longitude
        
    Returns:
        Parsed address data from Nominatim API
    """
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "format": "json",
        "lat": lat,
        "lon": lng,
        "zoom": 14,  # Street level detail
        "addressdetails": 1
    }
    
    headers = {
        "User-Agent": "AlstonaireGISEngine/1.0 (land-verification-system)"  # Required by Nominatim policy
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()


def parse_nominatim_address(data: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Parse Nominatim address data for administrative hierarchy.
    
    Args:
        data: Nominatim API response
        
    Returns:
        Dictionary with extracted administrative levels
    """
    address = data.get("address", {})
    
    # Extract district
    district = address.get("state_district") or address.get("county")
    
    # Extract taluk (city_district is more reliable for urban areas)
    taluk = address.get("city_district") or address.get("suburb")
    
    # Extract hobli (neighbourhood or suburb for urban areas)
    hobli = address.get("neighbourhood")
    
    # Extract village (village, suburb, or neighbourhood)
    # For urban areas like Bengaluru, suburb/locality is the village equivalent
    village = address.get("village") or address.get("suburb") or address.get("neighbourhood")
    
    extracted = {
        "district": district,
        "taluk": taluk,
        "hobli": hobli,
        "village": village
    }
    
    return extracted


async def validate_with_database(
    conn,
    district: Optional[str],
    taluk: Optional[str],
    hobli: Optional[str],
    village: Optional[str]
) -> Dict[str, Optional[str]]:
    """
    Validate extracted administrative names against karnataka_admin table.
    Uses ILIKE for fuzzy matching to find canonical names.
    
    Args:
        conn: Database connection
        district: Extracted district name
        taluk: Extracted taluk name
        hobli: Extracted hobli name
        village: Extracted village name
        
    Returns:
        Dictionary with validated canonical names
    """
    validated = {
        "district": None,
        "taluk": None,
        "hobli": None,
        "village": None
    }
    
    # Validate village first (most specific)
    if village:
        query = """
            SELECT district, taluk, hobli, village
            FROM karnataka_admin
            WHERE village ILIKE $1
            LIMIT 1
        """
        result = await conn.fetchrow(query, f"%{village}%")
        if result:
            validated["district"] = result["district"]
            validated["taluk"] = result["taluk"]
            validated["hobli"] = result["hobli"]
            validated["village"] = result["village"]
            return validated
    
    # Validate hobli if village not found
    if hobli:
        query = """
            SELECT DISTINCT district, taluk, hobli
            FROM karnataka_admin
            WHERE hobli ILIKE $1
            LIMIT 1
        """
        result = await conn.fetchrow(query, f"%{hobli}%")
        if result:
            validated["district"] = result["district"]
            validated["taluk"] = result["taluk"]
            validated["hobli"] = result["hobli"]
    
    # Validate taluk if hobli not found
    if taluk:
        query = """
            SELECT DISTINCT district, taluk
            FROM karnataka_admin
            WHERE taluk ILIKE $1
            LIMIT 1
        """
        result = await conn.fetchrow(query, f"%{taluk}%")
        if result:
            validated["district"] = result["district"]
            validated["taluk"] = result["taluk"]
    
    # Validate district if taluk not found
    if district:
        query = """
            SELECT DISTINCT district
            FROM karnataka_admin
            WHERE district ILIKE $1
            LIMIT 1
        """
        result = await conn.fetchrow(query, f"%{district}%")
        if result:
            validated["district"] = result["district"]
    
    return validated


# ============================================================================
# API Routes
# ============================================================================

@router.post("/resolve", response_model=LocationResponse)
async def resolve_location(
    request: LocationRequest,
    conn = Depends(get_db),
    cache = Depends(get_cache)
):
    """
    Resolve coordinates to administrative hierarchy.
    
    Two-source strategy:
    1. KGIS Admin Hierarchy API (authoritative district for Karnataka)
    2. Nominatim OpenStreetMap (village/hobli/taluk detail)
    
    Merges results from both sources for comprehensive hierarchy.
    
    Args:
        request: Location coordinates (lat, lng)
        
    Returns:
        Administrative hierarchy with confidence score and source
    """
    logger.info(f"DEBUG: resolve_location called with lat={request.lat}, lng={request.lng}")
    lat = request.lat
    lng = request.lng
    
    # Round coordinates to 6 decimal places for cache key
    lat_rounded = round(lat, 6)
    lng_rounded = round(lng, 6)
    cache_key = f"gis_cache:resolve:{lat_rounded}:{lng_rounded}"
    
    # Check cache first
    try:
        cached_result = await cache.get_key(cache_key)
        if cached_result:
            logger.info(f"Cache HIT for location resolve: {cache_key}")
            return LocationResponse(**cached_result)
        else:
            logger.info(f"Cache MISS for location resolve: {cache_key}")
    except Exception as e:
        logger.warning(f"Redis cache error: {e}")
    
    from app.config import settings
    from app.routers.gis import get_admin_hierarchy_from_kgis
    
    # Step 1: Call KGIS for district (authoritative source)
    kgis_result = await get_admin_hierarchy_from_kgis(lat, lng, cache)
    
    # Step 2: Always call Nominatim for village/hobli/taluk detail
    nominatim_data = None
    try:
        nominatim_data = await query_nominatim_geocoding(lat, lng)
    except Exception as e:
        logger.warning(f"Nominatim failed: {e}")
    
    # Step 3: Merge results
    if kgis_result and nominatim_data:
        # Both sources succeeded - merge them
        address = nominatim_data.get("address", {})
        
        # Extract Nominatim fields
        taluk = address.get('city_district') or address.get('county', '')
        hobli = address.get('suburb') or address.get('neighbourhood', '')
        village = address.get('suburb') or address.get('neighbourhood') or address.get('village') or address.get('town', '')
        
        # Use KGIS district (authoritative)
        district = kgis_result.get("district")
        district_code = kgis_result.get("districtCode")
        
        response_data = {
            "district": district,
            "districtCode": district_code,
            "taluk": taluk,
            "hobli": hobli,
            "village": village,
            "confidence_score": 0.85,
            "source": "kgis+nominatim"
        }
        
        logger.info(f"Merged KGIS+Nominatim result: district={district}, village={village}, hobli={hobli}")
        
    elif kgis_result:
        # Only KGIS succeeded
        response_data = {
            "district": kgis_result.get("district"),
            "districtCode": kgis_result.get("districtCode"),
            "taluk": None,
            "hobli": None,
            "village": None,
            "confidence_score": kgis_result.get("confidence_score", 0.95),
            "source": kgis_result.get("source", "kgis")
        }
        
        logger.info(f"KGIS only result: district={response_data['district']}")
        
    elif nominatim_data:
        # Only Nominatim succeeded
        address = nominatim_data.get("address", {})
        
        taluk = address.get('city_district') or address.get('county', '')
        hobli = address.get('suburb') or address.get('neighbourhood', '')
        village = address.get('suburb') or address.get('neighbourhood') or address.get('village') or address.get('town', '')
        district = address.get('state_district', '')
        
        response_data = {
            "district": district,
            "districtCode": None,
            "taluk": taluk,
            "hobli": hobli,
            "village": village,
            "confidence_score": 0.6,
            "source": "nominatim"
        }
        
        logger.info(f"Nominatim only result: district={district}, village={village}")
        
    else:
        # Both failed
        logger.error(f"Both KGIS and Nominatim failed for coordinates: {lat}, {lng}")
        raise HTTPException(
            status_code=404,
            detail="Unable to resolve location - all sources failed"
        )
    
    # Cache the result with 48-hour TTL
    try:
        from app.config import settings
        await cache.set_key(cache_key, response_data, ttl=settings.CACHE_TTL_SECONDS)
        logger.info(f"Stored resolve result in cache: {cache_key}")
    except Exception as e:
        logger.warning(f"Redis cache set error: {e}")
    
    return LocationResponse(**response_data)


@router.get("/hobli-list", response_model=HobliListResponse)
async def get_hobli_list(
    district: str = Query(..., description="District name (e.g., 'Bengaluru Urban')"),
    taluk: str = Query(..., description="Taluk name"),
    conn = Depends(get_db),
    cache = Depends(get_cache)
):
    """
    Get list of hoblis for a given district and taluk.
    
    Priority order:
    1. Query karnataka_admin table (primary source)
    2. KGIS Admin Hierarchy API with aoi=h (best-effort fallback)
    
    Returns distinct, alphabetically ordered list of hoblis.
    
    Args:
        district: District name
        taluk: Taluk name
        
    Returns:
        List of hoblis
    """
    # Check cache
    cache_key = f"hobli_list:{district}:{taluk}"
    cached_result = await cache.get(float(0), float(0), cache_key)
    if cached_result:
        logger.info(f"Cache hit for hobli list: {district}, {taluk}")
        return HobliListResponse(**cached_result)
    
    # Try karnataka_admin table first
    query = """
        SELECT DISTINCT hobli
        FROM karnataka_admin
        WHERE district ILIKE $1 AND taluk ILIKE $2
        AND hobli IS NOT NULL
        ORDER BY hobli ASC
    """
    
    results = await conn.fetch(query, f"%{district}%", f"%{taluk}%")
    
    hoblis = [row["hobli"] for row in results if row["hobli"]]
    
    if hoblis:
        response_data = {"hoblis": hoblis}
        # Cache the result
        await cache.set(float(0), float(0), response_data, cache_key)
        return HobliListResponse(**response_data)
    
    # Fallback to KGIS API (best-effort)
    # Note: This is a best-effort fallback using a hardcoded central coordinate for the taluk.
    # In production, you would need a mapping of taluk names to central coordinates.
    logger.warning(f"No hoblis found in karnataka_admin for {district}, {taluk}, trying KGIS fallback")
    
    from app.routers.gis import get_admin_hierarchy_from_kgis
    
    # Hardcoded central coordinates for major taluks (best-effort fallback)
    # This is not comprehensive - in production, maintain a proper taluk coordinate mapping
    taluk_coordinates = {
        "Bengaluru North": (13.0167, 77.5833),
        "Bengaluru South": (12.9167, 77.6167),
        "Bengaluru East": (12.9833, 77.6667),
        "Bengaluru West": (12.9667, 77.5667),
        "Yelahanka": (13.1000, 77.5667),
        "K.R. Puram": (13.0167, 77.7000),
        "Magadi": (12.9333, 77.2333),
        "Nelamangala": (13.1000, 77.3833),
        "Anekal": (12.8333, 77.7000),
        "Hoskote": (13.0667, 77.8000),
        "Doddaballapur": (13.3000, 77.5333),
        "Devanahalli": (13.2333, 77.7000),
    }
    
    coord = taluk_coordinates.get(taluk)
    if coord:
        try:
            # Call KGIS with aoi=h to get hobli information
            kgis_result = await get_admin_hierarchy_from_kgis(coord[0], coord[1], cache)
            if kgis_result and kgis_result.get("hobli"):
                hoblis = [kgis_result["hobli"]]
                response_data = {"hoblis": hoblis}
                # Cache the result
                await cache.set(float(0), float(0), response_data, cache_key)
                logger.info(f"KGIS fallback returned hobli: {kgis_result['hobli']}")
                return HobliListResponse(**response_data)
        except Exception as e:
            logger.warning(f"KGIS hobli fallback failed: {e}")
    
    # No hoblis found from any source
    logger.warning(f"No hoblis found for {district}, {taluk} from any source")
    return HobliListResponse(hoblis=[])
