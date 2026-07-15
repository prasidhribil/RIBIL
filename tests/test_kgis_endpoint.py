#!/usr/bin/env python3
"""
 ============================================================================
 KGIS Survey Number Endpoint Tests
 ============================================================================
 Description: Unit tests for the KGIS survey number endpoint
 Tests HTTP calls to KGIS service, response parsing, and error handling
 ============================================================================
"""

import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, patch
from app.routers.gis import router, KGISResponse


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


# ============================================================================
# KGIS Endpoint Tests
# ============================================================================

@pytest.mark.asyncio
async def test_kgis_success(client):
    """Test successful KGIS survey number lookup."""
    kgis_response_data = {
        "district": "Bengaluru Urban",
        "taluk": "Bengaluru South",
        "hobli": "Begur",
        "village": "Bellandur",
        "survey_number": "123/456"
    }
    
    with patch('httpx.AsyncClient.get') as mock_get:
        # Mock successful HTTP response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = kgis_response_data
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response
        
        response = await client.get("/api/gis/survey-number-kgis?latitude=12.9&longitude=77.5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["district"] == "Bengaluru Urban"
        assert data["taluk"] == "Bengaluru South"
        assert data["hobli"] == "Begur"
        assert data["village"] == "Bellandur"
        assert data["survey_number"] == "123/456"
        assert data["message"] is None


@pytest.mark.asyncio
async def test_kgis_timeout(client):
    """Test KGIS endpoint timeout handling."""
    with patch('httpx.AsyncClient.get') as mock_get:
        # Mock timeout exception
        import httpx
        mock_get.side_effect = httpx.TimeoutException("Request timeout")
        
        response = await client.get("/api/gis/survey-number-kgis?latitude=12.9&longitude=77.5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is False
        assert "timeout" in data["message"].lower()
        assert data["district"] is None
        assert data["taluk"] is None
        assert data["hobli"] is None
        assert data["village"] is None
        assert data["survey_number"] is None


@pytest.mark.asyncio
async def test_kgis_http_error(client):
    """Test KGIS endpoint HTTP error handling."""
    with patch('httpx.AsyncClient.get') as mock_get:
        # Mock HTTP status error
        import httpx
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_get.side_effect = httpx.HTTPStatusError(
            "Server error", request=AsyncMock(), response=mock_response
        )
        
        response = await client.get("/api/gis/survey-number-kgis?latitude=12.9&longitude=77.5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is False
        assert "500" in data["message"]
        assert data["district"] is None


@pytest.mark.asyncio
async def test_kgis_connection_error(client):
    """Test KGIS endpoint connection error handling."""
    with patch('httpx.AsyncClient.get') as mock_get:
        # Mock request error
        import httpx
        mock_get.side_effect = httpx.RequestError("Connection error")
        
        response = await client.get("/api/gis/survey-number-kgis?latitude=12.9&longitude=77.5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is False
        assert "unavailable" in data["message"].lower()
        assert data["district"] is None


@pytest.mark.asyncio
async def test_kgis_json_parse_error(client):
    """Test KGIS endpoint JSON parsing error handling."""
    with patch('httpx.AsyncClient.get') as mock_get:
        # Mock response with invalid JSON
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = lambda: None
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        
        response = await client.get("/api/gis/survey-number-kgis?latitude=12.9&longitude=77.5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is False
        assert data["message"] is not None


@pytest.mark.asyncio
async def test_kgis_validation_invalid_latitude(client):
    """Test that invalid latitude is rejected."""
    response = await client.get("/api/gis/survey-number-kgis?latitude=91&longitude=77.5")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_kgis_validation_invalid_longitude(client):
    """Test that invalid longitude is rejected."""
    response = await client.get("/api/gis/survey-number-kgis?latitude=12.9&longitude=181")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_kgis_validation_missing_params(client):
    """Test that missing parameters are rejected."""
    # Missing latitude
    response = await client.get("/api/gis/survey-number-kgis?longitude=77.5")
    assert response.status_code == 422
    
    # Missing longitude
    response = await client.get("/api/gis/survey-number-kgis?latitude=12.9")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_kgis_partial_response(client):
    """Test KGIS endpoint with partial response data."""
    kgis_response_data = {
        "district": "Bengaluru Urban",
        "taluk": "Bengaluru South",
        # Missing hobli, village, survey_number
    }
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = kgis_response_data
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response
        
        response = await client.get("/api/gis/survey-number-kgis?latitude=12.9&longitude=77.5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["district"] == "Bengaluru Urban"
        assert data["taluk"] == "Bengaluru South"
        assert data["hobli"] is None
        assert data["village"] is None
        assert data["survey_number"] is None


@pytest.mark.asyncio
async def test_kgis_response_structure(client):
    """Test that response structure matches expected format."""
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
        
        response = await client.get("/api/gis/survey-number-kgis?latitude=12.9&longitude=77.5")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields are present
        expected_fields = ["success", "district", "taluk", "hobli", "village", "survey_number", "message"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"


@pytest.mark.asyncio
async def test_kgis_valid_coordinates(client):
    """Test with valid coordinate ranges."""
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
        
        # Test boundary values
        test_cases = [
            (0, 0),
            (90, 180),
            (-90, -180),
            (12.9739, 77.5913),  # Cubbon Park
        ]
        
        for lat, lng in test_cases:
            response = await client.get(f"/api/gis/survey-number-kgis?latitude={lat}&longitude={lng}")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
