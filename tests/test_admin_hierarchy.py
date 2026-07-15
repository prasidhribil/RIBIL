#!/usr/bin/env python3
"""
 ============================================================================
 Admin Hierarchy Tests
 ============================================================================
 Description: Unit tests for KGIS admin hierarchy integration
 Tests KGIS as primary source, Google/Nominatim fallback, and caching
 ============================================================================
"""

import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, patch, MagicMock
from app.routers.location import router, LocationResponse
from app.routers.gis import get_admin_hierarchy_from_kgis


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def app():
    """Create FastAPI app with location router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
async def client(app):
    """Create async HTTP client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_cache():
    """Mock cache dependency."""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=None)
    return cache


@pytest.fixture
def mock_db():
    """Mock database dependency."""
    db = AsyncMock()
    return db


# ============================================================================
# KGIS Admin Hierarchy Function Tests
# ============================================================================

@pytest.mark.asyncio
async def test_kgis_admin_hierarchy_success():
    """Test successful KGIS admin hierarchy lookup with all 3 aoi values."""
    kgis_response_data = [
        {"districtName": "Bengaluru Urban", "districtCode": "02"},
        {"talukName": "Bengaluru South", "talukCode": "01"},
        {"hobliName": "Begur", "hobliCode": "001"}
    ]
    
    mock_cache = AsyncMock()
    mock_cache.get = AsyncMock(return_value=None)
    mock_cache.set = AsyncMock(return_value=None)
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = kgis_response_data
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response
        
        result = await get_admin_hierarchy_from_kgis(12.9352, 77.6789, mock_cache)
        
        assert result is not None
        assert result["district"] == "Bengaluru Urban"
        assert result["taluk"] == "Bengaluru South"
        assert result["hobli"] == "Begur"
        mock_cache.set.assert_called_once()


@pytest.mark.asyncio
async def test_kgis_admin_hierarchy_timeout():
    """Test KGIS admin hierarchy timeout handling."""
    mock_cache = AsyncMock()
    mock_cache.get = AsyncMock(return_value=None)
    
    with patch('httpx.AsyncClient.get') as mock_get:
        import httpx
        mock_get.side_effect = httpx.TimeoutException("Request timeout")
        
        result = await get_admin_hierarchy_from_kgis(12.9352, 77.6789, mock_cache)
        
        assert result is None
        mock_cache.set.assert_not_called()


@pytest.mark.asyncio
async def test_kgis_admin_hierarchy_http_error():
    """Test KGIS admin hierarchy HTTP error handling."""
    mock_cache = AsyncMock()
    mock_cache.get = AsyncMock(return_value=None)
    
    with patch('httpx.AsyncClient.get') as mock_get:
        import httpx
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_get.side_effect = httpx.HTTPStatusError(
            "Server error", request=AsyncMock(), response=mock_response
        )
        
        result = await get_admin_hierarchy_from_kgis(12.9352, 77.6789, mock_cache)
        
        assert result is None
        mock_cache.set.assert_not_called()


@pytest.mark.asyncio
async def test_kgis_admin_hierarchy_cache_hit():
    """Test KGIS admin hierarchy cache hit scenario."""
    cached_data = {
        "district": "Bengaluru Urban",
        "taluk": "Bengaluru South",
        "hobli": "Begur"
    }
    
    mock_cache = AsyncMock()
    mock_cache.get = AsyncMock(return_value=cached_data)
    
    result = await get_admin_hierarchy_from_kgis(12.9352, 77.6789, mock_cache)
    
    assert result == cached_data
    mock_cache.get.assert_called_once()
    mock_cache.set.assert_not_called()


@pytest.mark.asyncio
async def test_kgis_admin_hierarchy_missing_district():
    """Test KGIS admin hierarchy when district is missing."""
    kgis_response_data = [
        {"talukName": "Bengaluru South", "talukCode": "01"},
        {"hobliName": "Begur", "hobliCode": "001"}
    ]
    
    mock_cache = AsyncMock()
    mock_cache.get = AsyncMock(return_value=None)
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = kgis_response_data
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response
        
        result = await get_admin_hierarchy_from_kgis(12.9352, 77.6789, mock_cache)
        
        assert result is None


# ============================================================================
# Location Resolve Endpoint Tests with KGIS Integration
# ============================================================================

@pytest.mark.asyncio
async def test_resolve_location_kgis_primary_success(client, mock_db, mock_cache):
    """Test POST /api/location/resolve with KGIS as primary source."""
    kgis_response_data = [
        {"districtName": "Bengaluru Urban", "districtCode": "02"},
        {"talukName": "Bengaluru South", "talukCode": "01"},
        {"hobliName": "Begur", "hobliCode": "001"}
    ]
    
    # Mock database validation to return matched values
    mock_db.fetchrow = AsyncMock(return_value=MagicMock(
        district="Bengaluru Urban",
        taluk="Bengaluru South",
        hobli="Begur",
        village="Bellandur"
    ))
    
    with patch('app.routers.location.get_admin_hierarchy_from_kgis') as mock_kgis, \
         patch('app.routers.location.get_cache', return_value=mock_cache), \
         patch('app.routers.location.get_db', return_value=mock_db):
        
        mock_kgis.return_value = {
            "district": "Bengaluru Urban",
            "taluk": "Bengaluru South",
            "hobli": "Begur"
        }
        
        response = await client.post(
            "/api/location/resolve",
            json={"lat": 12.9352, "lng": 77.6789}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["district"] == "Bengaluru Urban"
        assert data["taluk"] == "Bengaluru South"
        assert data["hobli"] == "Begur"
        assert data["confidence_score"] == 0.95
        assert data["source"] == "kgis"


@pytest.mark.asyncio
async def test_resolve_location_kgis_timeout_fallback_to_google(client, mock_db, mock_cache):
    """Test KGIS timeout falls through to Google Geocoding."""
    mock_db.fetchrow = AsyncMock(return_value=MagicMock(
        district="Bengaluru Urban",
        taluk="Bengaluru South",
        hobli="Begur",
        village="Bellandur"
    ))
    
    with patch('app.routers.location.get_admin_hierarchy_from_kgis') as mock_kgis, \
         patch('app.routers.location.query_google_geocoding') as mock_google, \
         patch('app.routers.location.parse_google_address_components') as mock_parse, \
         patch('app.routers.location.get_cache', return_value=mock_cache), \
         patch('app.routers.location.get_db', return_value=mock_db), \
         patch('app.config.settings') as mock_settings:
        
        # KGIS fails
        mock_kgis.return_value = None
        
        # Google succeeds
        mock_google.return_value = {
            "address_components": [
                {"long_name": "Bengaluru Urban", "types": ["administrative_area_level_2"]},
                {"long_name": "Bengaluru South", "types": ["administrative_area_level_3"]},
            ]
        }
        mock_parse.return_value = {
            "district": "Bengaluru Urban",
            "taluk": "Bengaluru South",
            "hobli": None,
            "village": None
        }
        mock_settings.GOOGLE_MAPS_API_KEY = "test_key"
        
        response = await client.post(
            "/api/location/resolve",
            json={"lat": 12.9352, "lng": 77.6789}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["source"] == "google"
        assert data["confidence_score"] == 0.9


@pytest.mark.asyncio
async def test_resolve_location_kgis_google_fail_nominatim_success(client, mock_db, mock_cache):
    """Test KGIS + Google fail, Nominatim used as final fallback."""
    mock_db.fetchrow = AsyncMock(return_value=MagicMock(
        district="Bengaluru Urban",
        taluk="Bengaluru South",
        hobli="Begur",
        village="Bellandur"
    ))
    
    with patch('app.routers.location.get_admin_hierarchy_from_kgis') as mock_kgis, \
         patch('app.routers.location.query_google_geocoding') as mock_google, \
         patch('app.routers.location.query_nominatim_geocoding') as mock_nominatim, \
         patch('app.routers.location.parse_nominatim_address') as mock_parse_nominatim, \
         patch('app.routers.location.get_cache', return_value=mock_cache), \
         patch('app.routers.location.get_db', return_value=mock_db), \
         patch('app.config.settings') as mock_settings:
        
        # KGIS fails
        mock_kgis.return_value = None
        
        # Google fails
        mock_google.side_effect = Exception("Google API error")
        
        # Nominatim succeeds
        mock_nominatim.return_value = {
            "address": {
                "county": "Bengaluru Urban",
                "city_district": "Bengaluru South",
                "suburb": "Begur"
            }
        }
        mock_parse_nominatim.return_value = {
            "district": "Bengaluru Urban",
            "taluk": "Bengaluru South",
            "hobli": "Begur",
            "village": None
        }
        mock_settings.GOOGLE_MAPS_API_KEY = "test_key"
        
        response = await client.post(
            "/api/location/resolve",
            json={"lat": 12.9352, "lng": 77.6789}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["source"] == "nominatim"
        assert data["confidence_score"] == 0.7


@pytest.mark.asyncio
async def test_resolve_location_all_sources_fail_404(client, mock_db, mock_cache):
    """Test all sources fail returns 404."""
    with patch('app.routers.location.get_admin_hierarchy_from_kgis') as mock_kgis, \
         patch('app.routers.location.query_google_geocoding') as mock_google, \
         patch('app.routers.location.query_nominatim_geocoding') as mock_nominatim, \
         patch('app.routers.location.get_cache', return_value=mock_cache), \
         patch('app.routers.location.get_db', return_value=mock_db), \
         patch('app.config.settings') as mock_settings:
        
        # All sources fail
        mock_kgis.return_value = None
        mock_google.side_effect = Exception("Google API error")
        mock_nominatim.side_effect = Exception("Nominatim error")
        mock_settings.GOOGLE_MAPS_API_KEY = "test_key"
        
        response = await client.post(
            "/api/location/resolve",
            json={"lat": 12.9352, "lng": 77.6789}
        )
        
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_resolve_location_cache_hit(client, mock_db, mock_cache):
    """Test cache hit scenario for location resolve."""
    cached_data = {
        "district": "Bengaluru Urban",
        "taluk": "Bengaluru South",
        "hobli": "Begur",
        "village": "Bellandur",
        "confidence_score": 0.95,
        "source": "kgis"
    }
    
    mock_cache.get = AsyncMock(return_value=cached_data)
    
    with patch('app.routers.location.get_cache', return_value=mock_cache), \
         patch('app.routers.location.get_db', return_value=mock_db):
        
        response = await client.post(
            "/api/location/resolve",
            json={"lat": 12.9352, "lng": 77.6789}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data == cached_data
        mock_cache.get.assert_called_once()


@pytest.mark.asyncio
async def test_resolve_location_response_structure(client, mock_db, mock_cache):
    """Test response always contains all required fields."""
    mock_db.fetchrow = AsyncMock(return_value=MagicMock(
        district="Bengaluru Urban",
        taluk="Bengaluru South",
        hobli="Begur",
        village="Bellandur"
    ))
    
    with patch('app.routers.location.get_admin_hierarchy_from_kgis') as mock_kgis, \
         patch('app.routers.location.get_cache', return_value=mock_cache), \
         patch('app.routers.location.get_db', return_value=mock_db):
        
        mock_kgis.return_value = {
            "district": "Bengaluru Urban",
            "taluk": "Bengaluru South",
            "hobli": "Begur"
        }
        
        response = await client.post(
            "/api/location/resolve",
            json={"lat": 12.9352, "lng": 77.6789}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields are present
        required_fields = ["district", "taluk", "hobli", "village", "confidence_score", "source"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify confidence_score is between 0 and 1
        assert 0 <= data["confidence_score"] <= 1


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
