"""
 ============================================================================
 Bhoomi Maps Survey Number Resolution
 ============================================================================
 Description: Integration with Bhoomi Maps API for Karnataka land survey numbers
 API: https://rdservices.karnataka.gov.in/BhoomiMaps/Default/
 
 Two-step process:
 1. GetVlgOnBhoCode - Sets village in session (requires District, Taluk, Hobli, Village codes)
 2. FnVlgSurveyNoData - Returns all parcels with survey numbers (reads session)
 
 Both calls must use the same httpx.AsyncClient to share session cookie.
 
 Coordinate System: PolyPointlist uses EPSG:32643 (UTM Zone 43N, meters)
 Input GPS coordinates must be converted from EPSG:4326 to EPSG:32643.
 Bhoomi uses swapped axes: "Lat" = Easting, "Lng" = Northing
 ============================================================================
"""

import httpx
import json
import logging
from typing import Optional, Dict, Any, List
from pyproj import Transformer
from shapely.geometry import Point, Polygon
from app.config import settings

logger = logging.getLogger(__name__)

BHOOMI_BASE = settings.BHOOMI_BASE_URL
HEADERS = {"Referer": "https://rdservices.karnataka.gov.in/BhoomiMaps/"}


async def resolve_survey_number(
    lat: float,
    lng: float,
    district: str,
    taluk: str,
    hobli: str,
    village: str,
    cache = None
) -> Optional[Dict[str, Any]]:
    """
    Given GPS coordinates and village codes, return the survey number
    of the parcel containing that point.
    
    Args:
        lat: Latitude in decimal degrees (EPSG:4326)
        lng: Longitude in decimal degrees (EPSG:4326)
        district: District code (e.g., "20")
        taluk: Taluk code (e.g., "3")
        hobli: Hobli code (e.g., "5")
        village: Village code (e.g., "2")
        cache: Optional Redis cache for caching parcel data
        
    Returns:
        Dictionary with survey_no, village, vlg_code, dist_code, source or None if not found
    """
    try:
        # Generate cache key for village parcels
        cache_key = f"bhoomi:parcels:{district}:{taluk}:{hobli}:{village}"
        
        # Check cache first if cache is provided
        if cache:
            try:
                cached_data = await cache.get_key(cache_key)
                if cached_data:
                    logger.info(f"Cache HIT for Bhoomi parcels: {cache_key}")
                    parcels = json.loads(cached_data)
                else:
                    logger.info(f"Cache MISS for Bhoomi parcels: {cache_key}")
                    parcels = await _fetch_village_parcels(district, taluk, hobli, village)
                    if parcels:
                        try:
                            await cache.set_key(cache_key, json.dumps(parcels), ttl=86400)  # 24-hour TTL
                            logger.info(f"Stored Bhoomi parcels in cache: {cache_key}")
                        except Exception as e:
                            logger.warning(f"Redis cache set error for Bhoomi: {e}")
            except Exception as e:
                logger.warning(f"Redis cache error for Bhoomi: {e}")
                parcels = await _fetch_village_parcels(district, taluk, hobli, village)
        else:
            parcels = await _fetch_village_parcels(district, taluk, hobli, village)
        
        if not parcels:
            logger.warning(f"No parcels returned from Bhoomi for village {village}")
            return None
        
        # Transform input GPS coordinates to EPSG:32643 (UTM Zone 43N)
        # CRS investigation confirmed: EPSG:32643 with normal axes gives correct Karnataka coordinates
        # Bhoomi stores coordinates swapped: "Lat" = Easting, "Lng" = Northing
        # For WGS84 -> EPSG:32643 with always_xy=True, pass (lng, lat) as (x, y)
        transformer_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
        
        # Convert input point to UTM - pass (lng, lat) for always_xy=True
        easting, northing = transformer_to_utm.transform(lng, lat)
        # Use standard UTM coordinates (easting=x, northing=y) for point-in-polygon
        x_utm = easting
        y_utm = northing
        logger.info(f"Input GPS ({lat}, {lng}) -> UTM Easting={easting:.2f}, Northing={northing:.2f}")
        
        # Point-in-polygon matching using transformed coordinates
        parcels_checked = 0
        for parcel in parcels:
            try:
                survey_no = parcel.get("SurveyNo")
                if not survey_no or survey_no == "0" or survey_no == "*":
                    continue
                parcels_checked += 1
                
                # Parse PolyPointlist from Bhoomi
                poly_pointlist = parcel.get("PolyPointlist")
                if not poly_pointlist:
                    continue
                
                # Parse coordinates from PolyPointlist
                # Format: [[{'Lat': 802418.96, 'Lng': 1422392.80}, {'Lat': 802420.12, 'Lng': 1422395.50}, ...]]
                # Bhoomi stores coordinates swapped: "Lat" = Easting, "Lng" = Northing
                # Since our transformation produces standard (easting, northing), and Bhoomi uses swapped,
                # we use (Lat, Lng) as (x, y) directly for point-in-polygon
                polygon_coords = []
                try:
                    # poly_pointlist is a nested list: [[{coords}, ...]]
                    if isinstance(poly_pointlist, list) and len(poly_pointlist) > 0:
                        coord_list = poly_pointlist[0]  # Get first (and only) polygon ring
                        for coord in coord_list:
                            if isinstance(coord, dict):
                                lat_val = coord.get('Lat')  # Easting (Bhoomi's swapped storage)
                                lng_val = coord.get('Lng')  # Northing (Bhoomi's swapped storage)
                                if lat_val is not None and lng_val is not None:
                                    # Use (Lat, Lng) as (x, y) since Bhoomi stores them swapped
                                    polygon_coords.append((lat_val, lng_val))
                except Exception as e:
                    logger.debug(f"Error parsing PolyPointlist: {e}")
                    continue
                
                if len(polygon_coords) < 3:
                    continue
                
                # Create polygon and check if point is inside
                polygon = Polygon(polygon_coords)
                point = Point(x_utm, y_utm)
                
                if polygon.contains(point):
                    logger.info(f"Point-in-polygon match found! Survey No: {survey_no}")
                    return {
                        "survey_no": str(survey_no),
                        "village": parcel.get("Vlg"),
                        "vlg_code": parcel.get("VlgCode"),
                        "dist_code": parcel.get("DistCode"),
                        "taluk_code": parcel.get("TalukCode"),
                        "hobli_code": parcel.get("HobliCode"),
                        "source": "bhoomi_maps",
                        "village_verified": True
                    }
                    
            except Exception as e:
                logger.debug(f"Error processing parcel: {e}")
                continue
        
        logger.info(f"Checked {parcels_checked} valid parcels, no match found for point at ({lat}, {lng})")
        return None
        
    except Exception as e:
        logger.error(f"Error resolving survey number from Bhoomi: {e}")
        return None


async def _fetch_village_parcels(
    district: str,
    taluk: str,
    hobli: str,
    village: str
) -> List[Dict]:
    """
    Fetch all survey parcel polygons for a village from Bhoomi Maps.
    
    Uses two-step process:
    1. GetVlgOnBhoCode - Sets village in session
    2. FnVlgSurveyNoData - Returns all parcels (reads session)
    
    Both calls must use the same httpx.AsyncClient to share session cookie.
    
    Args:
        district: District code (e.g., "20")
        taluk: Taluk code (e.g., "3")
        hobli: Hobli code (e.g., "5")
        village: Village code (e.g., "2")
        
    Returns:
        List of parcel dictionaries with SurveyNo, PolyPointlist, etc.
    """
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=30.0) as client:
            # Step 1 - Set village in session
            await client.post(
                f"{BHOOMI_BASE}/GetVlgOnBhoCode",
                data={
                    "District": district,
                    "Taluk": taluk,
                    "Hobli": hobli,
                    "Village": village
                }
            )
            
            # Step 2 - Get all parcels (session carries village selection)
            response = await client.post(f"{BHOOMI_BASE}/FnVlgSurveyNoData")
            response.raise_for_status()
            
            parcels = response.json()
            logger.info(f"Retrieved {len(parcels)} parcels from Bhoomi for village {village}")
            return parcels
            
    except httpx.TimeoutException:
        logger.warning(f"Bhoomi API timeout for village {village}")
        return []
    except httpx.HTTPStatusError as e:
        logger.warning(f"Bhoomi API HTTP error: {e.response.status_code}")
        return []
    except json.JSONDecodeError as e:
        logger.warning(f"Bhoomi API JSON decode error: {e}")
        return []
    except Exception as e:
        logger.error(f"Bhoomi API unexpected error: {e}")
        return []


async def find_bhoomi_village_codes(village_name: str, district_name: str) -> Optional[Dict[str, str]]:
    """
    Search Bhoomi Maps dropdown endpoints to find the correct
    district/taluk/hobli/village codes for a given village name.
    
    Args:
        village_name: Village name (e.g., "Koramangala East")
        district_name: District name (e.g., "Bengaluru Urban")
        
    Returns:
        Dictionary with district, taluk, hobli, village codes or None if not found
    """
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=30.0) as client:
            # Get all districts
            r = await client.post(f"{BHOOMI_BASE}/GetDistrict")
            r.raise_for_status()
            districts_text = r.text
            # Bhoomi returns double-encoded JSON - parse twice
            districts = json.loads(districts_text)
            if isinstance(districts, str):
                districts = json.loads(districts)
            
            # Find matching district (fuzzy match on name)
            # Handle KGIS format "Bengaluru (Urban)" vs Bhoomi format "BENGALURU/ಬೆ೦ಗಳೂರು"
            dist_code = None
            # Extract English part before slash for Bhoomi names
            for d in districts:
                d_name = d["DistrictName"]
                # Extract English part (before slash or Kannada characters)
                english_name = d_name.split('/')[0].strip()
                normalized_d_name = english_name.lower().replace("(", "").replace(")", "").replace(" ", "").strip()
                normalized_district = district_name.lower().replace("(", "").replace(")", "").replace(" ", "").strip()
                
                if normalized_district in normalized_d_name or normalized_d_name in normalized_district:
                    dist_code = str(int(d["DISTRICT_CODE"]))
                    logger.info(f"Found matching district: {d['DistrictName']} (code: {dist_code})")
                    break
            
            if not dist_code:
                logger.warning(f"No matching district found for: {district_name}")
                return None
            
            # Get taluks for district
            r = await client.post(
                f"{BHOOMI_BASE}/GetTaluk",
                data={"DistCode": dist_code}
            )
            r.raise_for_status()
            taluks_text = r.text
            taluks = json.loads(taluks_text)
            if isinstance(taluks, str):
                taluks = json.loads(taluks)
            
            # Try each taluk
            for taluk in taluks:
                taluk_code = str(int(taluk["TALUKA_CODE"]))
                
                # Get hoblis
                r = await client.post(
                    f"{BHOOMI_BASE}/GetHobli",
                    data={"DistCode": dist_code, "TalukCode": taluk_code}
                )
                r.raise_for_status()
                hoblis_text = r.text
                hoblis = json.loads(hoblis_text)
                if isinstance(hoblis, str):
                    hoblis = json.loads(hoblis)
                
                for hobli in hoblis:
                    hobli_code = str(int(hobli["HOBLI_CODE"]))
                    
                    # Get villages
                    r = await client.post(
                        f"{BHOOMI_BASE}/GetVillage",
                        data={"DistCode": dist_code, "TalukCode": taluk_code,
                              "HobliCode": hobli_code}
                    )
                    r.raise_for_status()
                    villages_text = r.text
                    villages = json.loads(villages_text)
                    if isinstance(villages, str):
                        villages = json.loads(villages)
                    
                    for v in villages:
                        if village_name.lower() in v["VillageName"].lower() or \
                           v["VillageName"].lower() in village_name.lower():
                            result = {
                                "district": dist_code,
                                "taluk": taluk_code,
                                "hobli": hobli_code,
                                "village": str(int(v["VILLAGE_CODE"]))
                            }
                            logger.info(f"Found Bhoomi codes for {village_name}: {result}")
                            return result
            
            logger.warning(f"No matching village found for: {village_name}")
            return None
            
    except Exception as e:
        logger.error(f"Error finding Bhoomi village codes: {e}")
        return None


async def get_district_list() -> List[Dict]:
    """
    Get list of all districts from Bhoomi Maps.
    
    Returns:
        List of districts with DISTRICT_CODE and DistrictName
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(f"{BHOOMI_BASE}/GetDistrict")
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.error(f"Error getting district list: {e}")
        return []


async def get_taluk_list(district_code: str) -> List[Dict]:
    """
    Get list of taluks for a district from Bhoomi Maps.
    
    Args:
        district_code: District code (e.g., "20")
        
    Returns:
        List of taluks with TALUKA_CODE and TalukName
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(f"{BHOOMI_BASE}/GetTaluk",
                                 data={"DistrictCode": district_code})
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.error(f"Error getting taluk list: {e}")
        return []


async def get_hobli_list(district_code: str, taluk_code: str) -> List[Dict]:
    """
    Get list of hoblis for a taluk from Bhoomi Maps.
    
    Args:
        district_code: District code (e.g., "20")
        taluk_code: Taluk code (e.g., "3")
        
    Returns:
        List of hoblis with HOBLI_CODE and HobliName
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(f"{BHOOMI_BASE}/GetHobli",
                                 data={"DistrictCode": district_code,
                                       "TalukCode": taluk_code})
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.error(f"Error getting hobli list: {e}")
        return []


async def get_village_list(district_code: str, taluk_code: str, 
                            hobli_code: str) -> List[Dict]:
    """
    Get list of villages for a hobli from Bhoomi Maps.
    
    Args:
        district_code: District code (e.g., "20")
        taluk_code: Taluk code (e.g., "3")
        hobli_code: Hobli code (e.g., "5")
        
    Returns:
        List of villages with VILLAGE_CODE and VillageName
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(f"{BHOOMI_BASE}/GetVillage",
                                 data={"DistrictCode": district_code,
                                       "TalukCode": taluk_code,
                                       "HobliCode": hobli_code})
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.error(f"Error getting village list: {e}")
        return []
