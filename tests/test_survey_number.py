#!/usr/bin/env python3
"""
 ============================================================================
 Survey Number Lookup API Tests
 ============================================================================
 Description: Unit tests for the survey-number lookup endpoint
 Tests validation, empty table handling, fallback logic (cache -> KGIS -> PostGIS)
 ============================================================================
"""

import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock, patch
from app.routers.gis import router
from app.database import get_db
from app.cache import get_cache


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def app():
    """Create FastAPI app with GIS router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
async def client(app):
    """Create async HTTP client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_db_connection():
    """Mock database connection."""
    conn = AsyncMock()
    return conn


@pytest.fixture
def mock_get_db(mock_db_connection):
    """Override get_db dependency with mock."""
    async def override_get_db():
        yield mock_db_connection
    return override_get_db


# ============================================================================
# Validation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_survey_number_validation_invalid_latitude(client, mock_get_db, monkeypatch):
    """Test that invalid latitude (out of range) is rejected."""
    from app.routers import gis
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    
    # Test latitude > 90
    response = await client.get("/api/gis/survey-number?latitude=91&longitude=77.5")
    assert response.status_code == 422  # Validation error
    
    # Test latitude < -90
    response = await client.get("/api/gis/survey-number?latitude=-91&longitude=77.5")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_survey_number_validation_invalid_longitude(client, mock_get_db, monkeypatch):
    """Test that invalid longitude (out of range) is rejected."""
    from app.routers import gis
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    
    # Test longitude > 180
    response = await client.get("/api/gis/survey-number?latitude=12.9&longitude=181")
    assert response.status_code == 422
    
    # Test longitude < -180
    response = await client.get("/api/gis/survey-number?latitude=12.9&longitude=-181")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_survey_number_validation_missing_params(client, mock_get_db, monkeypatch):
    """Test that missing parameters are rejected."""
    from app.routers import gis
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    
    # Missing latitude
    response = await client.get("/api/gis/survey-number?longitude=77.5")
    assert response.status_code == 422
    
    # Missing longitude
    response = await client.get("/api/gis/survey-number?latitude=12.9")
    assert response.status_code == 422


# ============================================================================
# Empty Table Tests
# ============================================================================

@pytest.mark.asyncio
async def test_survey_number_empty_table(client, mock_db_connection, mock_get_db, monkeypatch):
    """Test response when survey_parcels table is empty."""
    from app.routers import gis
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    
    # Mock count query to return 0
    mock_db_connection.fetchrow = AsyncMock(return_value={"count": 0})
    
    response = await client.get("/api/gis/survey-number?latitude=12.9&longitude=77.5")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is False
    assert data["message"] == "Survey parcel dataset not yet loaded"
    assert data["survey_no"] is None
    assert data["village"] is None
    assert data["hobli"] is None
    assert data["district"] is None
    assert data["area_acres"] is None


# ============================================================================
# Successful Query Tests
# ============================================================================

@pytest.mark.asyncio
async def test_survey_number_success(client, mock_db_connection, mock_get_db, monkeypatch):
    """Test successful survey number lookup."""
    from app.routers import gis
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    
    # Mock count query to return non-zero
    count_result = {"count": 1}
    survey_result = {
        "survey_no": "123/456",
        "village": "Test Village",
        "hobli": "Test Hobli",
        "district": "Bengaluru Urban",
        "area_acres": 2.5
    }
    
    call_count = [0]
    
    async def mock_fetchrow(query, *args):
        call_count[0] += 1
        if call_count[0] == 1:
            return count_result
        else:
            return survey_result
    
    mock_db_connection.fetchrow = AsyncMock(side_effect=mock_fetchrow)
    
    response = await client.get("/api/gis/survey-number?latitude=12.9&longitude=77.5")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["survey_no"] == "123/456"
    assert data["village"] == "Test Village"
    assert data["hobli"] == "Test Hobli"
    assert data["district"] == "Bengaluru Urban"
    assert data["area_acres"] == 2.5
    assert data["message"] is None


@pytest.mark.asyncio
async def test_survey_number_not_found(client, mock_db_connection, mock_get_db, monkeypatch):
    """Test response when no parcel found at location."""
    from app.routers import gis
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    
    # Mock count query to return non-zero, but no parcel found
    count_result = {"count": 100}
    
    call_count = [0]
    
    async def mock_fetchrow(query, *args):
        call_count[0] += 1
        if call_count[0] == 1:
            return count_result
        else:
            return None  # No parcel found
    
    mock_db_connection.fetchrow = AsyncMock(side_effect=mock_fetchrow)
    
    response = await client.get("/api/gis/survey-number?latitude=12.9&longitude=77.5")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is False
    assert data["message"] == "No survey parcel found at this location"
    assert data["survey_no"] is None
    assert data["village"] is None
    assert data["hobli"] is None
    assert data["district"] is None
    assert data["area_acres"] is None


# ============================================================================
# Query Parameter Tests
# ============================================================================

@pytest.mark.asyncio
async def test_survey_number_valid_coordinates(client, mock_db_connection, mock_get_db, monkeypatch):
    """Test with valid coordinate ranges."""
    from app.routers import gis
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    
    # Mock empty table
    mock_db_connection.fetchrow = AsyncMock(return_value={"count": 0})
    
    # Test boundary values
    test_cases = [
        (0, 0),
        (90, 180),
        (-90, -180),
        (12.9739, 77.5913),  # Cubbon Park
        (13.2008, 77.7088),  # Airport
    ]
    
    for lat, lng in test_cases:
        response = await client.get(f"/api/gis/survey-number?latitude={lat}&longitude={lng}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["message"] == "Survey parcel dataset not yet loaded"


# ============================================================================
# PostGIS Query Tests
# ============================================================================

@pytest.mark.asyncio
async def test_survey_number_postgis_query_format(client, mock_db_connection, mock_get_db, monkeypatch):
    """Test that PostGIS query is called with correct parameters."""
    from app.routers import gis
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    
    # Mock responses
    count_result = {"count": 1}
    survey_result = {
        "survey_no": "456/789",
        "village": "Sample Village",
        "hobli": "Sample Hobli",
        "district": "Bengaluru Rural",
        "area_acres": 1.5
    }
    
    queries_called = []
    
    async def mock_fetchrow(query, *args):
        queries_called.append((query, args))
        if len(queries_called) == 1:
            return count_result
        else:
            return survey_result
    
    mock_db_connection.fetchrow = AsyncMock(side_effect=mock_fetchrow)
    
    response = await client.get("/api/gis/survey-number?latitude=12.9&longitude=77.5")
    
    assert response.status_code == 200
    
    # Verify queries were called
    assert len(queries_called) == 2
    
    # First query should be count check
    assert "COUNT(*)" in queries_called[0][0]
    
    # Second query should be ST_Contains query
    assert "ST_Contains" in queries_called[1][0]
    assert "ST_SetSRID(ST_Point" in queries_called[1][0]
    
    # Verify parameters (longitude, latitude order)
    assert queries_called[1][1][0] == 77.5  # longitude
    assert queries_called[1][1][1] == 12.9  # latitude


# ============================================================================
# Response Model Tests
# ============================================================================

@pytest.mark.asyncio
async def test_survey_number_response_structure(client, mock_db_connection, mock_get_db, monkeypatch):
    """Test that response structure matches expected format."""
    from app.routers import gis
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    
    # Mock empty table
    mock_db_connection.fetchrow = AsyncMock(return_value={"count": 0})
    
    response = await client.get("/api/gis/survey-number?latitude=12.9&longitude=77.5")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify all expected fields are present
    expected_fields = ["success", "survey_no", "village", "hobli", "district", "area_acres", "message"]
    for field in expected_fields:
        assert field in data, f"Missing field: {field}"


# ============================================================================
# Fallback Logic Tests
# ============================================================================

@pytest.fixture
def mock_cache():
    """Mock Redis cache."""
    cache = AsyncMock()
    return cache


@pytest.fixture
def mock_get_cache(mock_cache):
    """Override get_cache dependency with mock."""
    async def override_get_cache():
        yield mock_cache
    return override_get_cache


@pytest.mark.asyncio
async def test_survey_number_cache_hit(client, mock_cache, mock_get_cache, mock_get_db, monkeypatch):
    """Test survey number when cache hit occurs."""
    from app.routers import gis
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    monkeypatch.setattr(gis, "get_cache", mock_get_cache)
    
    # Mock cache hit
    cached_data = {
        "success": True,
        "survey_no": "123/456",
        "village": "Bellandur",
        "hobli": "Begur",
        "district": "Bengaluru Urban",
        "area_acres": 2.5,
        "message": None
    }
    mock_cache.get.return_value = cached_data
    
    response = await client.get("/api/gis/survey-number?latitude=12.9&longitude=77.5")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["survey_no"] == "123/456"
    assert data["village"] == "Bellandur"
    assert data["hobli"] == "Begur"
    assert data["district"] == "Bengaluru Urban"
    assert data["area_acres"] == 2.5
    
    # Verify cache was checked
    mock_cache.get.assert_called_once()


@pytest.mark.asyncio
async def test_survey_number_kgis_success(client, mock_cache, mock_get_cache, mock_db_connection, mock_get_db, monkeypatch):
    """Test survey number when KGIS succeeds (cache miss)."""
    from app.routers import gis
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    monkeypatch.setattr(gis, "get_cache", mock_get_cache)
    
    # Mock cache miss
    mock_cache.get.return_value = None
    
    # Mock KGIS success
    kgis_response_data = {
        "district": "Bengaluru Urban",
        "taluk": "Bengaluru South",
        "hobli": "Begur",
        "village": "Bellandur",
        "survey_number": "123/456"
    }
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = kgis_response_data
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response
        
        response = await client.get("/api/gis/survey-number?latitude=12.9&longitude=77.5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["survey_no"] == "123/456"
        assert data["village"] == "Bellandur"
        assert data["hobli"] == "Begur"
        assert data["district"] == "Bengaluru Urban"
        assert data["area_acres"] is None  # KGIS doesn't provide area_acres
        
        # Verify cache was set
        mock_cache.set.assert_called_once()


@pytest.mark.asyncio
async def test_survey_number_kgis_fallback_to_postgis(client, mock_cache, mock_get_cache, mock_db_connection, mock_get_db, monkeypatch):
    """Test survey number when KGIS fails, falls back to PostGIS."""
    from app.routers import gis
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    monkeypatch.setattr(gis, "get_cache", mock_get_cache)
    
    # Mock cache miss
    mock_cache.get.return_value = None
    
    # Mock KGIS failure
    with patch('httpx.AsyncClient.get') as mock_get:
        import httpx
        mock_get.side_effect = httpx.TimeoutException("Request timeout")
        
        # Mock PostGIS success
        count_result = {"count": 1}
        survey_result = {
            "survey_no": "789/012",
            "village": "Koramangala",
            "hobli": "Begur",
            "district": "Bengaluru Urban",
            "area_acres": 3.5
        }
        
        call_count = [0]
        
        async def mock_fetchrow(query, *args):
            call_count[0] += 1
            if call_count[0] == 1:
                return count_result
            else:
                return survey_result
        
        mock_db_connection.fetchrow = AsyncMock(side_effect=mock_fetchrow)
        
        response = await client.get("/api/gis/survey-number?latitude=12.9&longitude=77.5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["survey_no"] == "789/012"
        assert data["village"] == "Koramangala"
        assert data["hobli"] == "Begur"
        assert data["district"] == "Bengaluru Urban"
        assert data["area_acres"] == 3.5


@pytest.mark.asyncio
async def test_survey_number_all_sources_fail(client, mock_cache, mock_get_cache, mock_db_connection, mock_get_db, monkeypatch):
    """Test survey number when all sources fail."""
    from app.routers import gis
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    monkeypatch.setattr(gis, "get_cache", mock_get_cache)
    
    # Mock cache miss
    mock_cache.get.return_value = None
    
    # Mock KGIS failure
    with patch('httpx.AsyncClient.get') as mock_get:
        import httpx
        mock_get.side_effect = httpx.TimeoutException("Request timeout")
        
        # Mock PostGIS failure (empty table)
        mock_db_connection.fetchrow = AsyncMock(return_value={"count": 0})
        
        response = await client.get("/api/gis/survey-number?latitude=12.9&longitude=77.5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is False
        assert "no data available from any source" in data["message"]


@pytest.mark.asyncio
async def test_survey_number_kgis_field_mapping(client, mock_cache, mock_get_cache, mock_get_db, monkeypatch):
    """Test that KGIS fields are correctly mapped to SurveyNumberResponse schema."""
    from app.routers import gis
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    monkeypatch.setattr(gis, "get_cache", mock_get_cache)
    
    # Mock cache miss
    mock_cache.get.return_value = None
    
    # Mock KGIS response with all fields
    kgis_response_data = {
        "district": "Bengaluru Urban",
        "taluk": "Bengaluru South",
        "hobli": "Begur",
        "village": "Bellandur",
        "survey_number": "123/456"
    }
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = kgis_response_data
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response
        
        response = await client.get("/api/gis/survey-number?latitude=12.9&longitude=77.5")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify field mapping
        assert data["survey_no"] == kgis_response_data["survey_number"]
        assert data["village"] == kgis_response_data["village"]
        assert data["hobli"] == kgis_response_data["hobli"]
        assert data["district"] == kgis_response_data["district"]
        assert data["area_acres"] is None  # KGIS doesn't provide this


@pytest.mark.asyncio
async def test_survey_number_cache_key_format(client, mock_cache, mock_get_cache, mock_get_db, monkeypatch):
    """Test that cache key uses correct format with 6 decimal places."""
    from app.routers import gis
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    monkeypatch.setattr(gis, "get_cache", mock_get_cache)
    
    # Mock cache miss
    mock_cache.get.return_value = None
    
    # Mock KGIS failure to trigger PostGIS
    with patch('httpx.AsyncClient.get') as mock_get:
        import httpx
        mock_get.side_effect = httpx.TimeoutException("Request timeout")
        
        # Mock PostGIS success
        mock_db_connection.fetchrow = AsyncMock(side_effect=[
            {"count": 1},
            {"survey_no": "123/456", "village": "Test", "hobli": "Test", "district": "Test", "area_acres": 1.0}
        ])
        
        # Test with coordinates that need rounding
        response = await client.get("/api/gis/survey-number?latitude=12.9739123&longitude=77.5913456")
        
        # Verify cache key format (should be rounded to 6 decimal places)
        cache_key = mock_cache.get.call_args[0][0]
        assert "gis_cache:survey-number:12.973912:77.591346" in cache_key


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
