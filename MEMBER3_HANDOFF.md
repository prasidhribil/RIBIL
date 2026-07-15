# Member 3 — GIS Engine Handoff Document

## Sprint Completion Status

| Sprint | Status | Completion % | Key Deliverables |
|-------|--------|--------------|-----------------|
| Sprint 1 | COMPLETE | 100% | Database setup, PostGIS water bodies table, basic GIS endpoints |
| Sprint 2 | COMPLETE | 100% | KGIS integration, LULC mapping, survey number endpoint |
| Sprint 3 | COMPLETE | 95% | Lake buffer fix, NGT scraper (CAPTCHA limitation), AAI airport zones |
| Sprint 4 | COMPLETE | 95% | Redis cache fix, pilot validation, manual court cases seed |

**Overall Project Status:** 97.5% Complete

---

## What Is Working (Production Ready)

### 1. Location Resolve Endpoint
**Endpoint:** `POST /api/location/resolve`
**Status:** ✅ Working with Redis cache (3-4ms cached responses)

```bash
curl -X POST "http://localhost:8000/api/location/resolve" \
  -H "Content-Type: application/json" \
  -d '{"lat": 12.9352, "lng": 77.6789}'
```

**Sample Response:**
```json
{
  "district": "Bengaluru (Urban)",
  "taluk": "Bengaluru South",
  "hobli": "Yamalur",
  "village": "Yamalur",
  "districtCode": "20",
  "confidence_score": 0.85,
  "source": "kgis+nominatim"
}
```

### 2. Zone Check Endpoint
**Endpoint:** `GET /api/gis/zone-check`
**Status:** ✅ Working (30/30 pilot test pass)

```bash
curl "http://localhost:8000/api/gis/zone-check?lat=12.9352&lng=77.6789"
```

**Sample Response:**
```json
{
  "cdp_zone": {
    "zone_type": "Agriculture Zone",
    "zone_name": "Crop land",
    "zone_code": "AGCR",
    "in_zone": true
  },
  "lake_buffer": {
    "is_blocked": false,
    "is_warning": false,
    "nearest_lake": "Unnamed Lake",
    "distance_meters": 304.04
  },
  "ngt_orders": {
    "has_violations": false,
    "case_count": 0,
    "cases": []
  },
  "aai_zone": {
    "in_restriction_zone": true,
    "airport_name": "HAL Airport (Bengaluru)",
    "restriction_type": "Runway Protection Zone",
    "height_limit_meters": 0.0
  },
  "overall_status": "blocked"
}
```

### 3. Court Cases Endpoint
**Endpoint:** `GET /api/gis/court-cases`
**Status:** ✅ Working (database-backed, 10 seeded cases)

```bash
curl "http://localhost:8000/api/gis/court-cases?village=Bellandur"
```

**Sample Response:**
```json
{
  "cases": [
    {
      "case_number": "OA-125/2016",
      "village": "Bellandur",
      "survey_no": "Multiple",
      "violation_type": "Lake Encroachment",
      "status": "Active",
      "order_date": "2016-04-15",
      "description": "NGT order on Bellandur Lake pollution and encroachment by builder activities"
    }
  ],
  "source": "database"
}
```

### 4. Lake Buffer Check
**Status:** ✅ Fixed (search radius increased from 150m to 10km)
- Returns nearest lake and distance for all coordinates
- Handles null lake names with "Unnamed Lake" fallback

### 5. AAI Airport Zone Check
**Status:** ✅ Working (analytical distance-based calculation)
- Calculates distances to HAL and BIAL airports
- Returns restriction zones and height limits
- No spatial data required

---

## API Endpoints Reference

| Endpoint | Method | Params | Description | Example |
|----------|--------|--------|-------------|---------|
| `/api/location/resolve` | POST | lat, lng (JSON body) | Reverse geocoding to administrative hierarchy | `{"lat": 12.9352, "lng": 77.6789}` |
| `/api/gis/zone-check` | GET | lat, lng (query params) | Full zone compliance check (CDP, lake, AAI, NGT) | `?lat=12.9352&lng=77.6789` |
| `/api/gis/survey-number` | GET | latitude, longitude (query params) | Survey number lookup (KGIS API limitation) | `?latitude=12.9352&longitude=77.6789` |
| `/api/gis/court-cases` | GET | village (query param) | NGT court cases for village | `?village=Bellandur` |
| `/api/gis/landuse` | GET | latitude, longitude (query params) | LULC classification from KGIS | `?latitude=12.9352&longitude=77.6789` |
| `/api/gis/lakes` | GET | lat, lng (query params), lake_id (optional) | Nearest lakes or specific lake info | `?lat=12.9352&lng=77.6789` |

---

## Architecture Decisions Made

### 1. KGIS+Nominatim instead of karnataka_admin table
**Reasoning:**
- KGIS provides authoritative district codes (required for other APIs)
- Nominatim provides detailed village/hobli/taluk information
- karnataka_admin table has limited coverage and outdated data
- Combined approach gives best of both: authoritative district + detailed hierarchy

**Trade-off:** Slightly slower than pure database lookup, but more accurate and comprehensive

### 2. LULC instead of CDP zones shapefile
**Reasoning:**
- CDP shapefile is static, requires manual updates
- KGIS LULC API is live, always current
- LULC categories can be mapped to CDP zones programmatically
- No file management overhead

**Trade-off:** Requires API call for each request (mitigated by Redis cache)

### 3. Analytical AAI instead of spatial data
**Reasoning:**
- AAI spatial data not publicly available
- Distance-based calculation is mathematically sound
- AAI zones are defined by distance from runway center
- No spatial database required

**Trade-off:** Approximate (not exact), but documented as such

### 4. Manual court cases seed instead of NGT scraper
**Reasoning:**
- NGT website requires CAPTCHA (blocks automation)
- Manual seed provides reliable test data
- Database-backed approach is faster and more reliable
- Can be updated manually as needed

**Trade-off:** Not live data, but functional for MVP

---

## Known Limitations

| Limitation | Reason | Workaround | Future Fix Path |
|------------|--------|------------|-----------------|
| Survey number endpoint | KGIS surveyno API returns empty data even with correct parameters | Returns failure message, zone check still works | Investigate KGIS API documentation or contact KGIS support |
| NGT scraper | CAPTCHA protection prevents automation | Manual seed data (10 cases) | Use official NGT API if available, or manual data entry |
| Redis cache resolve endpoint | Cache method signature mismatch (fixed) | Now working correctly | N/A - Fixed |
| Lake buffer null values | Search radius too small (150m) | Increased to 10km, handles null names | N/A - Fixed |
| Survey parcels table | Empty, no data loaded | Fallback to KGIS API (also limited) | Import official survey parcel data from KGIS |

---

## Environment Setup

### 1. Start Redis
```bash
C:\Redis\redis-server.exe
```

### 2. Start PostgreSQL (Docker)
```bash
docker-compose up -d postgres
```

### 3. Start FastAPI
```bash
venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start Node.js Queue (if using)
```bash
node src/index.js
```

### Environment Variables Required
- `DB_HOST=localhost`
- `DB_PORT=5432`
- `DB_NAME=gis_engine`
- `DB_USER=postgres`
- `DB_PASSWORD=postgres`
- `REDIS_HOST=localhost`
- `REDIS_PORT=6379`
- `REDIS_PASSWORD=`
- `REDIS_DB=0`
- `CACHE_TTL_SECONDS=172800` (48 hours)

---

## Integration Points for Other Members

### Member 1 (Frontend)
**Required from Member 3:**
- List of all API endpoints with request/response schemas
- Authentication requirements (if any)
- Error response formats

**Key Endpoints:**
- `POST /api/location/resolve` - Get administrative hierarchy
- `GET /api/gis/zone-check` - Full zone compliance check
- `GET /api/gis/court-cases` - NGT court cases

**Request/Response Examples:** See "What Is Working" section above

### Member 4 (Scrapers)
**Required from Member 3:**
- Bull queue job payload format (if using queue)
- Status polling endpoint format

**Job Payload Format:**
```json
{
  "lat": 12.9352,
  "lng": 77.6789,
  "property_id": "PROP-001",
  "tasks": ["location", "survey", "zone", "court"]
}
```

**Status Polling:**
```bash
GET /api/property/verify/status/{job_id}
```

### Member 6 (DevOps)
**Required from Member 3:**
- Docker configuration
- Environment variables needed
- Service dependencies

**Docker Config:**
- PostgreSQL: `docker-compose.yml` (postgres service)
- Redis: Native Windows (not Docker)
- FastAPI: Python 3.13, requirements.txt

**Dependencies:**
- PostgreSQL 14 with PostGIS 3.3
- Redis 3.2.100 (native Windows)
- Python 3.13 with asyncpg, httpx, fastapi

---

## Data Sources Used

| Data | Source | Update Frequency | How to Refresh |
|------|--------|------------------|----------------|
| Water bodies | KGIS lake shapefile | Static | Re-run `import_water_bodies.py` |
| Administrative hierarchy | KGIS nearbyadminhierarchy API | Live | Automatic (cached 48h) |
| LULC classification | KGIS LULC API | Live | Automatic (cached 48h) |
| Court cases | Manual seed | Manual | Run `scripts/seed_court_cases.py` |
| Survey numbers | KGIS surveyno API | Live | Automatic (currently non-functional) |
| Airport coordinates | Hardcoded (config.py) | Static | Update config.py if needed |

---

## Files Changed from Original Scaffold

| File | Changes |
|------|---------|
| `app/config.py` | Added airport coordinates and names (HAL, BIAL) |
| `app/cache.py` | Added `get_key()` and `set_key()` methods for string keys |
| `app/database.py` | No changes (original scaffold) |
| `app/routers/gis.py` | Added CDP zone mapping, AAI zone calculation, court cases endpoint, updated survey number logic, fixed cache calls |
| `app/routers/location.py` | Updated cache calls to use `get_key()` and `set_key()` |
| `app/routers/zone.py` | Increased lake buffer search radius to 10km, added null lake name fallback, integrated CDP and AAI functions |
| `app/services/ngt_scraper.py` | Created new file with NGT scraper (CAPTCHA limitation) |
| `requirements.txt` | Added beautifulsoup4 |
| `scripts/seed_court_cases.py` | Created new file for manual court case seeding |
| `tests/sprint4_pilot.py` | Created new file for 30-plot pilot validation |

---

## Database Schema

### Tables Created
1. **water_bodies** - 1356 records (lake polygons with metadata)
2. **karnataka_admin** - Administrative hierarchy reference table
3. **court_cases** - 10 records (NGT Southern Zone cases)
4. **survey_parcels** - Empty (no data loaded)

### Key Queries
```sql
-- Check water bodies count
SELECT COUNT(*) FROM water_bodies;

-- Check court cases count
SELECT COUNT(*) FROM court_cases;

-- Find nearest lake
SELECT lake_name, ST_Distance(geom::geography, ST_SetSRID(ST_Point($1, $2), 4326)::geography) as distance_meters
FROM water_bodies
ORDER BY distance_meters ASC
LIMIT 1;
```

---

## Performance Metrics

### Cache Performance (After Fix)
- Resolve endpoint: 319ms (miss) → 3-4ms (hit) ✅
- Zone check: 13ms-6.5s (miss) → 6-7ms (hit) ✅
- Target: <50ms for cached responses ✅

### Pilot Test Results
- Location resolve: 30/30 (100%) ✅
- Survey number: 0/30 (0%) - KGIS API limitation
- Zone check: 30/30 (100%) ✅

---

## Troubleshooting Guide

### Redis Connection Issues
**Symptom:** "Redis connection timeout"
**Solution:** Start Redis server: `C:\Redis\redis-server.exe`

### Database Connection Issues
**Symptom:** "password authentication failed"
**Solution:** Check docker-compose.yml for correct password (default: postgres)

### KGIS API Timeout
**Symptom:** "KGIS API timeout"
**Solution:** Increase timeout in code or check network connectivity to kgis.ksrsac.in

### Cache Not Working
**Symptom:** Cached responses still slow
**Solution:** Check Redis is running, verify cache key format, check logs for cache errors

---

## Next Steps for Future Development

1. **Survey Number:** Investigate KGIS API documentation or contact KGIS support for correct API usage
2. **NGT Scraper:** Explore official NGT API or alternative data sources
3. **Survey Parcels:** Import official survey parcel data from KGIS
4. **Performance:** Consider adding more aggressive caching for frequently accessed data
5. **Monitoring:** Add metrics collection for API performance monitoring

---

## Contact Information

**Project:** AlstonAir GIS Engine
**Member 3:** GIS Backend Developer
**Last Updated:** 2026-06-21
**Sprint Status:** Sprint 4 Complete (97.5% overall)
