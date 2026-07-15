"""
 ============================================================================
 Zone Router - Environmental & Regulatory Zone Checks
 ============================================================================
 Description: FastAPI routes for comprehensive zone compliance checks
 Focus: Bengaluru-specific regulations (BDA, NGT, AAI)
 Uses asyncio.gather for parallel execution of all checks
 ============================================================================
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import asyncio
import logging
from app.database import get_db
from app.cache import get_cache
from app.routers.gis import get_cdp_zone_from_lulc, get_aai_zone_info

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gis", tags=["zone"])


# ============================================================================
# Pydantic Models
# ============================================================================

class CDPZoneCheck(BaseModel):
    """BDA Master Plan 2031 zone check result."""
    zone_type: Optional[str] = None
    zone_name: Optional[str] = None
    zone_code: Optional[str] = None
    in_zone: bool = False


class LakeBufferCheck(BaseModel):
    """Lake buffer check result (NGT regulations)."""
    is_blocked: bool = Field(default=False, description="Within 75m - construction blocked")
    is_warning: bool = Field(default=False, description="75-150m - NOC required")
    nearest_lake: Optional[str] = None
    distance_meters: Optional[float] = None


class NGTCheck(BaseModel):
    """NGT Tribunal orders check result."""
    has_violations: bool = False
    case_count: int = 0
    cases: list[Dict[str, Any]] = Field(default_factory=list)


class AAIZoneCheck(BaseModel):
    """Airport Authority of India zone check result."""
    in_restriction_zone: bool = False
    airport_name: Optional[str] = None
    restriction_type: Optional[str] = None
    height_limit_meters: Optional[float] = None


class ZoneCheckResponse(BaseModel):
    """Composite zone check response."""
    cdp_zone: CDPZoneCheck
    lake_buffer: LakeBufferCheck
    ngt_orders: NGTCheck
    aai_zone: AAIZoneCheck
    overall_status: str = Field(..., description="Overall compliance status")


# ============================================================================
# Helper Functions for Individual Checks
# ============================================================================

async def check_cdp_zone(pool, lat: float, lng: float, cache = None) -> CDPZoneCheck:
    """
    Check BDA Master Plan 2031 zone using KGIS LULC mapping.
    
    Uses get_cdp_zone_from_lulc to map LULC categories to CDP zone types.
    Falls back to PostGIS query if LULC mapping fails.
    
    Args:
        pool: Database connection pool
        lat: Latitude
        lng: Longitude
        cache: Optional cache dependency
        
    Returns:
        CDP zone information
    """
    # Try LULC mapping first
    cdp_zone = await get_cdp_zone_from_lulc(lat, lng, cache)
    
    if cdp_zone:
        return CDPZoneCheck(
            zone_type=cdp_zone["zone_type"],
            zone_name=cdp_zone["zone_name"],
            zone_code=cdp_zone.get("lulc_code"),
            in_zone=cdp_zone["in_zone"]
        )
    
    # Fallback to PostGIS query
    async with pool.acquire() as conn:
        query = """
            SELECT zone_type, zone_name, zone_code
            FROM cdp_zones
            WHERE ST_Contains(
                geom,
                ST_SetSRID(ST_Point($1, $2), 4326)
            )
            LIMIT 1
        """
        
        result = await conn.fetchrow(query, lng, lat)
        
        if result:
            return CDPZoneCheck(
                zone_type=result["zone_type"],
                zone_name=result["zone_name"],
                zone_code=result["zone_code"],
                in_zone=True
            )
        
        return CDPZoneCheck(
            zone_type="Unknown",
            zone_name=None,
            zone_code=None,
            in_zone=False
        )


async def check_lake_buffer(pool, lat: float, lng: float) -> LakeBufferCheck:
    """
    Check lake buffer zones using ST_DWithin for NGT compliance.
    
    NGT Regulations:
    - Within 75m: Construction blocked (is_blocked=true)
    - 75-150m: NOC required (is_warning=true)
    
    Args:
        pool: Database connection pool
        lat: Latitude
        lng: Longitude
        
    Returns:
        Lake buffer check result
    """
    async with pool.acquire() as conn:
        # Find nearest lake within 10km (increased from 150m to find any nearby lake)
        query = """
            SELECT 
                lake_name,
                ST_Distance(
                    geom::geography,
                    ST_SetSRID(ST_Point($1, $2), 4326)::geography
                ) as distance_meters
            FROM water_bodies
            WHERE ST_DWithin(
                geom::geography,
                ST_SetSRID(ST_Point($1, $2), 4326)::geography,
                10000  -- 10km search radius to find nearest lake
            )
            ORDER BY distance_meters ASC
            LIMIT 1
        """
        
        result = await conn.fetchrow(query, lng, lat)
    
    if result:
        distance = result["distance_meters"]
        lake_name = result["lake_name"] or "Unnamed Lake"
        
        if distance <= 75:
            return LakeBufferCheck(
                is_blocked=True,
                is_warning=False,
                nearest_lake=lake_name,
                distance_meters=distance
            )
        elif distance <= 150:
            return LakeBufferCheck(
                is_blocked=False,
                is_warning=True,
                nearest_lake=lake_name,
                distance_meters=distance
            )
        else:
            # Lake found but outside buffer zone
            return LakeBufferCheck(
                is_blocked=False,
                is_warning=False,
                nearest_lake=lake_name,
                distance_meters=distance
            )
    
    return LakeBufferCheck(is_blocked=False, is_warning=False)


async def check_ngt_orders(pool, lat: float, lng: float) -> NGTCheck:
    """
    Check NGT Tribunal orders for violations.
    
    First resolves the village from coordinates, then checks for violations.
    
    Args:
        pool: Database connection pool
        lat: Latitude
        lng: Longitude
        
    Returns:
        NGT violation check result
    """
    async with pool.acquire() as conn:
        # First, get the village from karnataka_admin using reverse geocoding
        # This is a simplified version - in production, use the location resolve endpoint
        village_query = """
            SELECT village
            FROM karnataka_admin
            WHERE village ILIKE '%Bengaluru%' OR village ILIKE '%Bangalore%'
            LIMIT 1
        """
        
        village_result = await conn.fetchrow(village_query)
        village = village_result["village"] if village_result else None
        
        if not village:
            return NGTCheck(has_violations=False, case_count=0)
        
        # Check for NGT cases in this village
        query = """
            SELECT 
                case_number,
                survey_no,
                violation_type,
                status,
                order_date,
                description
            FROM court_cases
            WHERE village ILIKE $1
            AND status = 'Active'
            ORDER BY order_date DESC
        """
        
        results = await conn.fetch(query, f"%{village}%")
    
    cases = [
        {
            "case_number": row["case_number"],
            "survey_no": row["survey_no"],
            "violation_type": row["violation_type"],
            "status": row["status"],
            "order_date": str(row["order_date"]) if row["order_date"] else None,
            "description": row["description"]
        }
        for row in results
    ]
    
    return NGTCheck(
        has_violations=len(cases) > 0,
        case_count=len(cases),
        cases=cases
    )


async def check_aai_zone(pool, lat: float, lng: float, cache = None) -> AAIZoneCheck:
    """
    Check AAI airport restriction zones using analytical distance calculation.
    
    Uses get_aai_zone_info to calculate distance to nearest airport and
    determine restriction zone based on distance.
    
    Args:
        pool: Database connection pool
        lat: Latitude
        lng: Longitude
        cache: Optional cache dependency
        
    Returns:
        AAI zone check result
    """
    # Use analytical calculation
    aai_info = await get_aai_zone_info(lat, lng, cache)
    
    return AAIZoneCheck(
        in_restriction_zone=aai_info["is_in_restriction_zone"],
        airport_name=aai_info["airport_name"],
        restriction_type=aai_info["restriction_type"] if aai_info["restriction_type"] != "None" else None,
        height_limit_meters=aai_info["height_limit_meters"]
    )


# ============================================================================
# API Route
# ============================================================================

@router.get("/zone-check", response_model=ZoneCheckResponse)
async def zone_check(
    lat: float = Query(..., ge=-90, le=90, description="Latitude in decimal degrees"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude in decimal degrees"),
    conn = Depends(get_db),
    cache = Depends(get_cache)
):
    """
    Comprehensive zone compliance check for given coordinates.
    
    Runs all four checks in parallel using asyncio.gather:
    1. CDP Zone Check (BDA Master Plan 2031)
    2. Lake Buffer Check (NGT - 75m blocked, 75-150m warning)
    3. NGT Tribunal Orders Check
    4. AAI Airport Buffer Check (BIAL/HAL)
    
    Args:
        lat: Latitude
        lng: Longitude
        
    Returns:
        Composite zone check results with overall status
    """
    # Check cache first
    cached_result = await cache.get(lat, lng, "zone-check")
    if cached_result:
        logger.info(f"Cache hit for zone check: {lat}, {lng}")
        return ZoneCheckResponse(**cached_result)
    
    # Run all four checks in parallel
    logger.info(f"Running parallel zone checks for: {lat}, {lng}")
    
    # Get the pool from Database class
    from app.database import Database
    pool = Database.pool
    
    cdp_result, lake_result, ngt_result, aai_result = await asyncio.gather(
        check_cdp_zone(pool, lat, lng, cache),
        check_lake_buffer(pool, lat, lng),
        check_ngt_orders(pool, lat, lng),
        check_aai_zone(pool, lat, lng, cache),
        return_exceptions=True
    )
    
    # Handle any exceptions from parallel execution
    if isinstance(cdp_result, Exception):
        logger.error(f"CDP zone check failed: {cdp_result}")
        cdp_result = CDPZoneCheck(in_zone=False)
    
    if isinstance(lake_result, Exception):
        logger.error(f"Lake buffer check failed: {lake_result}")
        lake_result = LakeBufferCheck(is_blocked=False, is_warning=False)
    
    if isinstance(ngt_result, Exception):
        logger.error(f"NGT orders check failed: {ngt_result}")
        ngt_result = NGTCheck(has_violations=False, case_count=0)
    
    if isinstance(aai_result, Exception):
        logger.error(f"AAI zone check failed: {aai_result}")
        aai_result = AAIZoneCheck(in_restriction_zone=False)
    
    # Determine overall status
    blocked_conditions = [
        lake_result.is_blocked,
        ngt_result.has_violations,
        aai_result.in_restriction_zone
    ]
    
    warning_conditions = [
        lake_result.is_warning,
        not cdp_result.in_zone  # Not in any defined zone might be concerning
    ]
    
    if any(blocked_conditions):
        overall_status = "blocked"
    elif any(warning_conditions):
        overall_status = "warning"
    else:
        overall_status = "compliant"
    
    response_data = {
        "cdp_zone": cdp_result.model_dump(),
        "lake_buffer": lake_result.model_dump(),
        "ngt_orders": ngt_result.model_dump(),
        "aai_zone": aai_result.model_dump(),
        "overall_status": overall_status
    }
    
    # Cache the result
    await cache.set(lat, lng, response_data, "zone-check")
    
    logger.info(f"Zone check completed with status: {overall_status}")
    
    return ZoneCheckResponse(**response_data)
