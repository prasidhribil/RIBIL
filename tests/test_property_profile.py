#!/usr/bin/env python3
"""
 ============================================================================
 Property Profile API Tests
 ============================================================================
 Description: Unit tests for the property-profile endpoint
 Tests aggregation of survey parcel, lake, buffer, CDP zone, and court cases
 ============================================================================
"""

import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock
from app.routers.gis import router, get_survey_parcel_info, get_nearest_lake_info, get_buffer_status, get_cdp_zone_info, get_court_cases
from app.database import get_db


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
# Service Function Tests
# ============================================================================

@pytest.mark.asyncio
async def test_get_survey_parcel_info_success(mock_db_connection):
    """Test successful survey parcel info retrieval."""
    mock_db_connection.fetchrow = AsyncMock(return_value={
        "survey_no": "123/456",
        "village": "Bellandur",
        "hobli": "Begur",
        "district": "Bengaluru Urban",
        "area_acres": 2.5
    })
    
    result = await get_survey_parcel_info(mock_db_connection, 77.5, 12.9)
    
    assert result is not None
    assert result.survey_no == "123/456"
    assert result.village == "Bellandur"
    assert result.hobli == "Begur"
    assert result.district == "Bengaluru Urban"
    assert result.area_acres == 2.5


@pytest.mark.asyncio
async def test_get_survey_parcel_info_not_found(mock_db_connection):
    """Test survey parcel info when no parcel found."""
    mock_db_connection.fetchrow = AsyncMock(return_value=None)
    
    result = await get_survey_parcel_info(mock_db_connection, 77.5, 12.9)
    
    assert result is None


@pytest.mark.asyncio
async def test_get_survey_parcel_info_error(mock_db_connection):
    """Test survey parcel info when database error occurs."""
    mock_db_connection.fetchrow = AsyncMock(side_effect=Exception("Database error"))
    
    result = await get_survey_parcel_info(mock_db_connection, 77.5, 12.9)
    
    assert result is None


@pytest.mark.asyncio
async def test_get_nearest_lake_info_success(mock_db_connection):
    """Test successful nearest lake info retrieval."""
    mock_db_connection.fetchrow = AsyncMock(return_value={
        "lake_name": "Bellandur Lake",
        "lake_type": "Lake",
        "distance_meters": 120.5
    })
    
    result = await get_nearest_lake_info(mock_db_connection, 77.5, 12.9)
    
    assert result is not None
    assert result.lake_name == "Bellandur Lake"
    assert result.lake_type == "Lake"
    assert result.distance_meters == 120.5


@pytest.mark.asyncio
async def test_get_nearest_lake_info_not_found(mock_db_connection):
    """Test nearest lake info when no lakes found."""
    mock_db_connection.fetchrow = AsyncMock(return_value=None)
    
    result = await get_nearest_lake_info(mock_db_connection, 77.5, 12.9)
    
    assert result is None


@pytest.mark.asyncio
async def test_get_buffer_status_blocked():
    """Test buffer status for blocked zone (<75m)."""
    result = await get_buffer_status(50.0)
    
    assert result.status == "blocked"
    assert result.distance_meters == 50.0
    assert result.threshold_meters == 75


@pytest.mark.asyncio
async def test_get_buffer_status_warning():
    """Test buffer status for warning zone (75-150m)."""
    result = await get_buffer_status(100.0)
    
    assert result.status == "warning"
    assert result.distance_meters == 100.0
    assert result.threshold_meters == 150


@pytest.mark.asyncio
async def test_get_buffer_status_safe():
    """Test buffer status for safe zone (>150m)."""
    result = await get_buffer_status(200.0)
    
    assert result.status == "safe"
    assert result.distance_meters == 200.0
    assert result.threshold_meters is None


@pytest.mark.asyncio
async def test_get_buffer_status_none():
    """Test buffer status when no lake distance available."""
    result = await get_buffer_status(None)
    
    assert result.status == "safe"
    assert result.distance_meters is None
    assert result.threshold_meters is None


@pytest.mark.asyncio
async def test_get_cdp_zone_info_success(mock_db_connection):
    """Test successful CDP zone info retrieval."""
    mock_db_connection.fetchrow = AsyncMock(return_value={
        "zone_type": "Residential",
        "zone_name": "R1 Zone"
    })
    
    result = await get_cdp_zone_info(mock_db_connection, 77.5, 12.9)
    
    assert result is not None
    assert result.zone_type == "Residential"
    assert result.zone_name == "R1 Zone"


@pytest.mark.asyncio
async def test_get_cdp_zone_info_not_found(mock_db_connection):
    """Test CDP zone info when no zone found."""
    mock_db_connection.fetchrow = AsyncMock(return_value=None)
    
    result = await get_cdp_zone_info(mock_db_connection, 77.5, 12.9)
    
    assert result is None


@pytest.mark.asyncio
async def test_get_court_cases_success(mock_db_connection):
    """Test successful court cases retrieval."""
    from datetime import datetime
    mock_db_connection.fetch = AsyncMock(return_value=[
        {
            "case_number": "CASE-001",
            "case_type": "Civil",
            "status": "Pending",
            "filing_date": datetime(2024, 1, 1)
        },
        {
            "case_number": "CASE-002",
            "case_type": "Criminal",
            "status": "Closed",
            "filing_date": datetime(2023, 6, 15)
        }
    ])
    
    result = await get_court_cases(mock_db_connection, "123/456")
    
    assert len(result) == 2
    assert result[0].case_number == "CASE-001"
    assert result[0].case_type == "Civil"
    assert result[0].status == "Pending"
    assert result[1].case_number == "CASE-002"
    assert result[1].case_type == "Criminal"
    assert result[1].status == "Closed"


@pytest.mark.asyncio
async def test_get_court_cases_no_survey_no(mock_db_connection):
    """Test court cases when no survey number provided."""
    result = await get_court_cases(mock_db_connection, None)
    
    assert result == []


@pytest.mark.asyncio
async def test_get_court_cases_empty_result(mock_db_connection):
    """Test court cases when no cases found."""
    mock_db_connection.fetch = AsyncMock(return_value=[])
    
    result = await get_court_cases(mock_db_connection, "123/456")
    
    assert result == []


# ============================================================================
# Endpoint Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_property_profile_complete(client, mock_db_connection, mock_get_db, monkeypatch):
    """Test property profile with all data sources available."""
    from app.routers import gis
    from datetime import datetime
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    
    # Mock survey parcel query
    survey_result = {
        "survey_no": "123/456",
        "village": "Bellandur",
        "hobli": "Begur",
        "district": "Bengaluru Urban",
        "area_acres": 2.5
    }
    
    # Mock lake query
    lake_result = {
        "lake_name": "Bellandur Lake",
        "lake_type": "Lake",
        "distance_meters": 100.0
    }
    
    # Mock CDP zone query
    zone_result = {
        "zone_type": "Residential",
        "zone_name": "R1 Zone"
    }
    
    # Mock court cases query
    court_results = [
        {
            "case_number": "CASE-001",
            "case_type": "Civil",
            "status": "Pending",
            "filing_date": datetime(2024, 1, 1)
        }
    ]
    
    call_count = [0]
    
    async def mock_fetchrow(query, *args):
        call_count[0] += 1
        if call_count[0] == 1:
            return survey_result
        elif call_count[0] == 2:
            return lake_result
        elif call_count[0] == 3:
            return zone_result
        return None
    
    async def mock_fetch(query, *args):
        return court_results
    
    mock_db_connection.fetchrow = AsyncMock(side_effect=mock_fetchrow)
    mock_db_connection.fetch = AsyncMock(side_effect=mock_fetch)
    
    response = await client.get("/api/gis/property-profile?latitude=12.9&longitude=77.5")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify survey parcel
    assert data["survey_parcel"] is not None
    assert data["survey_parcel"]["survey_no"] == "123/456"
    assert data["survey_parcel"]["village"] == "Bellandur"
    
    # Verify nearest lake
    assert data["nearest_lake"] is not None
    assert data["nearest_lake"]["lake_name"] == "Bellandur Lake"
    assert data["nearest_lake"]["distance_meters"] == 100.0
    
    # Verify buffer status (100m = warning zone)
    assert data["buffer_status"] is not None
    assert data["buffer_status"]["status"] == "warning"
    assert data["buffer_status"]["distance_meters"] == 100.0
    assert data["buffer_status"]["threshold_meters"] == 150
    
    # Verify CDP zone
    assert data["cdp_zone"] is not None
    assert data["cdp_zone"]["zone_type"] == "Residential"
    
    # Verify court cases
    assert data["court_cases"] is not None
    assert len(data["court_cases"]) == 1
    assert data["court_cases"][0]["case_number"] == "CASE-001"


@pytest.mark.asyncio
async def test_property_profile_empty_tables(client, mock_db_connection, mock_get_db, monkeypatch):
    """Test property profile when all tables are empty."""
    from app.routers import gis
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    
    # Mock all queries to return None
    mock_db_connection.fetchrow = AsyncMock(return_value=None)
    mock_db_connection.fetch = AsyncMock(return_value=[])
    
    response = await client.get("/api/gis/property-profile?latitude=12.9&longitude=77.5")
    
    assert response.status_code == 200
    data = response.json()
    
    # All fields should be None
    assert data["survey_parcel"] is None
    assert data["nearest_lake"] is None
    assert data["cdp_zone"] is None
    assert data["court_cases"] is None
    
    # Buffer status should still be "safe" (no lake)
    assert data["buffer_status"] is not None
    assert data["buffer_status"]["status"] == "safe"
    assert data["buffer_status"]["distance_meters"] is None


@pytest.mark.asyncio
async def test_property_profile_validation_invalid_latitude(client, mock_get_db, monkeypatch):
    """Test that invalid latitude is rejected."""
    from app.routers import gis
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    
    response = await client.get("/api/gis/property-profile?latitude=91&longitude=77.5")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_property_profile_validation_invalid_longitude(client, mock_get_db, monkeypatch):
    """Test that invalid longitude is rejected."""
    from app.routers import gis
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    
    response = await client.get("/api/gis/property-profile?latitude=12.9&longitude=181")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_property_profile_validation_missing_params(client, mock_get_db, monkeypatch):
    """Test that missing parameters are rejected."""
    from app.routers import gis
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    
    # Missing latitude
    response = await client.get("/api/gis/property-profile?longitude=77.5")
    assert response.status_code == 422
    
    # Missing longitude
    response = await client.get("/api/gis/property-profile?latitude=12.9")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_property_profile_buffer_blocked(client, mock_db_connection, mock_get_db, monkeypatch):
    """Test buffer status calculation for blocked zone."""
    from app.routers import gis
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    
    # Mock lake at 50m (blocked zone)
    mock_db_connection.fetchrow = AsyncMock(side_effect=[
        None,  # No survey parcel
        {"lake_name": "Test Lake", "lake_type": "Lake", "distance_meters": 50.0},
        None  # No CDP zone
    ])
    mock_db_connection.fetch = AsyncMock(return_value=[])
    
    response = await client.get("/api/gis/property-profile?latitude=12.9&longitude=77.5")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["buffer_status"]["status"] == "blocked"
    assert data["buffer_status"]["distance_meters"] == 50.0
    assert data["buffer_status"]["threshold_meters"] == 75


@pytest.mark.asyncio
async def test_property_profile_response_structure(client, mock_db_connection, mock_get_db, monkeypatch):
    """Test that response structure matches expected format."""
    from app.routers import gis
    monkeypatch.setattr(gis, "get_db", mock_get_db)
    
    mock_db_connection.fetchrow = AsyncMock(return_value=None)
    mock_db_connection.fetch = AsyncMock(return_value=[])
    
    response = await client.get("/api/gis/property-profile?latitude=12.9&longitude=77.5")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify all expected fields are present
    expected_fields = ["survey_parcel", "nearest_lake", "buffer_status", "cdp_zone", "court_cases"]
    for field in expected_fields:
        assert field in data, f"Missing field: {field}"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
