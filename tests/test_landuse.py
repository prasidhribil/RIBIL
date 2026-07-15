#!/usr/bin/env python3
"""
 ============================================================================
 Land Use API Tests
 ============================================================================
 Description: Unit tests for the land use endpoint
 Tests KGIS ArcGIS REST integration, response parsing, and error handling
 ============================================================================
"""

import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, patch
from app.routers.gis import router, get_landuse_info, LandUseInfo, LULC_CATEGORY_MAP


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
# Service Function Tests
# ============================================================================

@pytest.mark.asyncio
async def test_get_landuse_info_success():
    """Test successful land use info retrieval."""
    kgis_response_data = {
        "features": [
            {
                "attributes": {
                    "NR.DBO.LULC.LULCCode": "BUUR",
                    "NR.DBO.LULC_Tbl.LULC_Description": "Built up (Urban)"
                }
            }
        ]
    }
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = kgis_response_data
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response
        
        result = await get_landuse_info(12.9, 77.5)
        
        assert result is not None
        assert result.land_use == "Built up (Urban)"
        assert result.lulc_code == "BUUR"
        assert result.category == "Built-up"


@pytest.mark.asyncio
async def test_get_landuse_info_no_features():
    """Test land use info when no features found."""
    kgis_response_data = {
        "features": []
    }
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = kgis_response_data
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response
        
        result = await get_landuse_info(12.9, 77.5)
        
        assert result is None


@pytest.mark.asyncio
async def test_get_landuse_info_timeout():
    """Test land use info timeout handling."""
    import httpx
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Request timeout")
        
        result = await get_landuse_info(12.9, 77.5)
        
        assert result is None


@pytest.mark.asyncio
async def test_get_landuse_info_http_error():
    """Test land use info HTTP error handling."""
    import httpx
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_get.side_effect = httpx.HTTPStatusError(
            "Server error", request=AsyncMock(), response=mock_response
        )
        
        result = await get_landuse_info(12.9, 77.5)
        
        assert result is None


@pytest.mark.asyncio
async def test_get_landuse_info_connection_error():
    """Test land use info connection error handling."""
    import httpx
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.side_effect = httpx.RequestError("Connection error")
        
        result = await get_landuse_info(12.9, 77.5)
        
        assert result is None


@pytest.mark.asyncio
async def test_get_landuse_info_category_mapping():
    """Test LULC code to category mapping."""
    kgis_response_data = {
        "features": [
            {
                "attributes": {
                    "NR.DBO.LULC.LULCCode": "AGCR",
                    "NR.DBO.LULC_Tbl.LULC_Description": "Crop land"
                }
            }
        ]
    }
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = kgis_response_data
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response
        
        result = await get_landuse_info(12.9, 77.5)
        
        assert result is not None
        assert result.lulc_code == "AGCR"
        assert result.category == "Agriculture"


@pytest.mark.asyncio
async def test_get_landuse_info_unknown_category():
    """Test LULC code with unknown category."""
    kgis_response_data = {
        "features": [
            {
                "attributes": {
                    "NR.DBO.LULC.LULCCode": "XXXX",
                    "NR.DBO.LULC_Tbl.LULC_Description": "Unknown Land Use"
                }
            }
        ]
    }
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = kgis_response_data
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response
        
        result = await get_landuse_info(12.9, 77.5)
        
        assert result is not None
        assert result.lulc_code == "XXXX"
        assert result.category == "Other"


# ============================================================================
# Endpoint Tests
# ============================================================================

@pytest.mark.asyncio
async def test_landuse_endpoint_success(client):
    """Test successful land use endpoint call."""
    kgis_response_data = {
        "features": [
            {
                "attributes": {
                    "NR.DBO.LULC.LULCCode": "BUUR",
                    "NR.DBO.LULC_Tbl.LULC_Description": "Built up (Urban)"
                }
            }
        ]
    }
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = kgis_response_data
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response
        
        response = await client.get("/api/gis/landuse?latitude=12.9&longitude=77.5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["land_use"] == "Built up (Urban)"
        assert data["lulc_code"] == "BUUR"
        assert data["category"] == "Built-up"
        assert data["source"] == "KGIS LULC"
        assert data["message"] is None


@pytest.mark.asyncio
async def test_landuse_endpoint_no_polygon(client):
    """Test land use endpoint when no polygon found."""
    kgis_response_data = {
        "features": []
    }
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = kgis_response_data
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response
        
        response = await client.get("/api/gis/landuse?latitude=12.9&longitude=77.5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is False
        assert data["message"] == "No land use polygon found at this location"
        assert data["land_use"] is None
        assert data["lulc_code"] is None
        assert data["category"] is None


@pytest.mark.asyncio
async def test_landuse_endpoint_timeout(client):
    """Test land use endpoint timeout handling."""
    import httpx
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Request timeout")
        
        response = await client.get("/api/gis/landuse?latitude=12.9&longitude=77.5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is False
        assert data["message"] == "No land use polygon found at this location"


@pytest.mark.asyncio
async def test_landuse_validation_invalid_latitude(client):
    """Test that invalid latitude is rejected."""
    response = await client.get("/api/gis/landuse?latitude=91&longitude=77.5")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_landuse_validation_invalid_longitude(client):
    """Test that invalid longitude is rejected."""
    response = await client.get("/api/gis/landuse?latitude=12.9&longitude=181")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_landuse_validation_missing_params(client):
    """Test that missing parameters are rejected."""
    # Missing latitude
    response = await client.get("/api/gis/landuse?longitude=77.5")
    assert response.status_code == 422
    
    # Missing longitude
    response = await client.get("/api/gis/landuse?latitude=12.9")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_landuse_response_structure(client):
    """Test that response structure matches expected format."""
    kgis_response_data = {
        "features": [
            {
                "attributes": {
                    "NR.DBO.LULC.LULCCode": "FRDE",
                    "NR.DBO.LULC_Tbl.LULC_Description": "Forest"
                }
            }
        ]
    }
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = kgis_response_data
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response
        
        response = await client.get("/api/gis/landuse?latitude=12.9&longitude=77.5")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields are present
        expected_fields = ["success", "land_use", "lulc_code", "category", "source", "message"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"


@pytest.mark.asyncio
async def test_landuse_valid_coordinates(client):
    """Test with valid coordinate ranges."""
    kgis_response_data = {
        "features": [
            {
                "attributes": {
                    "NR.DBO.LULC.LULCCode": "WBTA",
                    "NR.DBO.LULC_Tbl.LULC_Description": "Tank"
                }
            }
        ]
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
            response = await client.get(f"/api/gis/landuse?latitude={lat}&longitude={lng}")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


# ============================================================================
# Category Mapping Tests
# ============================================================================

def test_lulc_category_map():
    """Test LULC category mapping dictionary."""
    assert "BUUR" in LULC_CATEGORY_MAP
    assert LULC_CATEGORY_MAP["BUUR"] == "Built-up"
    assert "AGCR" in LULC_CATEGORY_MAP
    assert LULC_CATEGORY_MAP["AGCR"] == "Agriculture"
    assert "FRDE" in LULC_CATEGORY_MAP
    assert LULC_CATEGORY_MAP["FRDE"] == "Forest"
    assert "GRGR" in LULC_CATEGORY_MAP
    assert LULC_CATEGORY_MAP["GRGR"] == "Wasteland"
    assert "WBRS" in LULC_CATEGORY_MAP
    assert LULC_CATEGORY_MAP["WBRS"] == "Water"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
