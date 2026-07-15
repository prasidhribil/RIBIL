# Bengaluru GIS Engine & Reverse Geocoding Service

Complete backend architecture for GIS spatial computing and property verification, focused on Bengaluru Urban and Rural districts.

## Architecture Overview

This project implements a multi-tier backend architecture:

- **Python FastAPI** (Port 8000): GIS APIs with PostGIS spatial queries
- **Node.js Express + Bull Queue** (Port 3000): Background job orchestration
- **PostgreSQL + PostGIS**: Spatial database storage
- **Redis**: High-performance caching layer

## Features

### Phase 1: Database Schema & Seeding
- `karnataka_admin` table with administrative hierarchy (district, taluk, hobli, village)
- `survey_parcels` table with spatial geometry for point-in-polygon queries
- Bulk insertion script for efficient data loading (~30k records)
- PostGIS GIST and B-Tree indexes for optimal query performance

### Phase 2: Reverse Geocoding APIs
- `POST /api/location/resolve` - Reverse geocoding with Google/Nominatim fallback
- `GET /api/location/hobli-list` - Administrative hierarchy queries
- Database validation for canonical village names

### Phase 3: Spatial Survey Number Engine
- `GET /api/gis/survey-number` - Point-in-polygon survey lookup
- ST_Contains for exact matches
- ST_Distance fallback for nearest parcel

### Phase 4: Environmental & Regulatory Zone Checks
- `GET /api/gis/zone-check` - Composite zone compliance check
- Parallel execution using asyncio.gather:
  - BDA Master Plan 2031 (CDP zones)
  - Lake buffer checks (NGT: 75m blocked, 75-150m warning)
  - NGT Tribunal orders verification
  - AAI airport restriction zones (BIAL/HAL)

### Phase 5: Bull Job Queue Infrastructure
- `POST /api/property/verify` - Submit verification jobs
- `GET /api/property/verify/status/:job_id` - Poll job status
- Concurrency limit: 5 parallel jobs
- 14-step verification workflow with progress tracking

## Project Structure

```
land record/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── database.py             # PostgreSQL connection pool
│   ├── cache.py                # Redis cache manager
│   └── routers/
│       ├── __init__.py
│       ├── location.py         # Reverse geocoding APIs
│       ├── gis.py              # Survey number engine
│       └── zone.py             # Zone check endpoints
├── database/
│   ├── migrations/
│   │   └── 001_initial_schema.sql  # PostGIS schema
│   └── seeds/
│       └── seed_karnataka_admin.py # Bulk insertion script
├── src/
│   ├── index.js                # Express server entry point
│   ├── middleware/
│   │   └── auth.js             # JWT authentication
│   ├── queues/
│   │   └── verifyQueue.js      # Bull queue setup
│   └── routes/
│       └── property.js        # Property verification routes
├── requirements.txt            # Python dependencies
├── package.json               # Node.js dependencies
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## Prerequisites

- **PostgreSQL 14+** with PostGIS extension
- **Redis 7+**
- **Python 3.10+**
- **Node.js 18+**
- **Google Maps API Key** (for geocoding)

## Setup Instructions

### 1. Database Setup

```bash
# Create PostgreSQL database
createdb gis_engine

# Enable PostGIS extension
psql -d gis_engine -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# Run migration script
psql -d gis_engine -f database/migrations/001_initial_schema.sql
```

### 2. Python Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Node.js Environment Setup

```bash
# Install dependencies
npm install
```

### 4. Redis Setup

```bash
# Start Redis server
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### 5. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# Required variables:
# - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
# - REDIS_HOST, REDIS_PORT
# - GOOGLE_MAPS_API_KEY
# - JWT_SECRET
```

### 6. Seed Administrative Data

```bash
# Run bulk insertion script
python database/seeds/seed_karnataka_admin.py

# This will generate mock data for Bengaluru districts
# Or provide your own CSV at database/seeds/karnataka_villages.csv
```

## Running the Services

### Start FastAPI Service (Port 8000)

```bash
# Development mode with auto-reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Start Node.js Queue Service (Port 3000)

```bash
# Development mode
npm run dev

# Production mode
npm start
```

## API Documentation

### FastAPI Endpoints

Once running, access interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### Location APIs

**Reverse Geocoding**
```bash
POST /api/location/resolve
Content-Type: application/json

{
  "lat": 12.9716,
  "lng": 77.5946
}

Response:
{
  "district": "Bengaluru Urban",
  "taluk": "Bengaluru South",
  "hobli": "Begur",
  "village": "Bellandur",
  "confidence_score": 0.9,
  "source": "google"
}
```

**Hobli List**
```bash
GET /api/location/hobli-list?district=Bengaluru%20Urban&taluk=Bengaluru%20South

Response:
{
  "hoblis": ["Begur", "Varthur", "Kudlu", "Madiwala"]
}
```

#### GIS APIs

**Survey Number Lookup**
```bash
GET /api/gis/survey-number?latitude=12.9716&longitude=77.5946

Response (success):
{
  "success": true,
  "survey_no": "123/456",
  "village": "Bellandur",
  "hobli": "Begur",
  "district": "Bengaluru Urban",
  "area_acres": 2.5
}

Response (empty table):
{
  "success": false,
  "message": "Survey parcel dataset not yet loaded"
}

Response (no parcel found):
{
  "success": false,
  "message": "No survey parcel found at this location"
}
```

**Query Parameters:**
- `latitude` (required): Latitude between -90 and 90
- `longitude` (required): Longitude between -180 and 180

**Description:** Uses PostGIS ST_Contains to find the exact survey parcel containing the given coordinates. Returns survey number, village, hobli, district, and area in acres.

**Property Profile**
```bash
GET /api/gis/property-profile?latitude=12.9716&longitude=77.5946

Response:
{
  "survey_parcel": {
    "survey_no": "123/456",
    "village": "Bellandur",
    "hobli": "Begur",
    "district": "Bengaluru Urban",
    "area_acres": 2.5
  },
  "nearest_lake": {
    "lake_name": "Bellandur Lake",
    "lake_type": "Lake",
    "distance_meters": 120.5
  },
  "buffer_status": {
    "status": "warning",
    "distance_meters": 120.5,
    "threshold_meters": 150
  },
  "cdp_zone": {
    "zone_type": "Residential",
    "zone_name": "R1 Zone"
  },
  "court_cases": [
    {
      "case_number": "CASE-001",
      "case_type": "Civil",
      "status": "Pending",
      "filing_date": "2024-01-01"
    }
  ]
}
```

**Query Parameters:**
- `latitude` (required): Latitude between -90 and 90
- `longitude` (required): Longitude between -180 and 180

**Description:** Aggregates complete GIS property profile from multiple data sources. Returns survey parcel information, nearest lake with buffer status, CDP zone information, court cases, and land use information. Returns null for any data source that is empty or unavailable.

**KGIS Survey Number**
```bash
GET /api/gis/survey-number-kgis?latitude=12.9716&longitude=77.5946

Response (success):
{
  "success": true,
  "district": "Bengaluru Urban",
  "taluk": "Bengaluru South",
  "hobli": "Begur",
  "village": "Bellandur",
  "survey_number": "123/456"
}

Response (error):
{
  "success": false,
  "message": "KGIS service timeout - request took too long"
}
```

**Query Parameters:**
- `latitude` (required): Latitude between -90 and 90
- `longitude` (required): Longitude between -180 and 180

**Description:** Calls the official Karnataka GIS (KGIS) survey number web service to retrieve survey information for given coordinates. Returns district, taluk, hobli, village, and survey number. Includes comprehensive error handling for service timeouts, HTTP errors, and connection failures.

**Configuration:**
Set the KGIS API URL in `.env`:
```
KGIS_API_URL=https://kgis.karnataka.gov.in/api/survey-number
```

**Land Use**
```bash
GET /api/gis/landuse?latitude=12.9716&longitude=77.5946

Response (success):
{
  "success": true,
  "land_use": "Built up (Urban)",
  "lulc_code": "BUUR",
  "category": "Built-up",
  "source": "KGIS LULC"
}

Response (no polygon found):
{
  "success": false,
  "message": "No land use polygon found at this location"
}
```

**Query Parameters:**
- `latitude` (required): Latitude between -90 and 90
- `longitude` (required): Longitude between -180 and 180

**Description:** Calls the KGIS ArcGIS REST LULC service to retrieve land use classification for given coordinates. Performs point-in-polygon lookup to determine land use, LULC code, and category. Returns null if no polygon is found at the location.

**Configuration:**
Set the KGIS LULC URL in `.env`:
```
KGIS_LULC_URL=https://kgis.ksrsac.in/kgismaps1/rest/services/NR_V2/LULC_10K/MapServer/0/query
```

**LULC Categories:**
- **Built-up**: BUUR, BUUC, BUUP, BURU, BURV, BURM, BURH, BUMN, BUTP
- **Agriculture**: AGCR, AGPL, AGAQ
- **Forest**: FRDE, FRPL, FRMG
- **Wasteland**: GRGR, WLST, WLGU, WLWL, WLSD, WLSP, WLSA, WLBR
- **Water**: WBRS, WBCN, WBRE, WBTA, WBLP

**Zone Check**
```bash
GET /api/gis/zone-check?lat=12.9716&lng=77.5946

Response:
{
  "cdp_zone": {
    "zone_type": "Residential",
    "zone_name": "R1 Zone",
    "in_zone": true
  },
  "lake_buffer": {
    "is_blocked": false,
    "is_warning": true,
    "nearest_lake": "Bellandur Lake",
    "distance_meters": 120
  },
  "ngt_orders": {
    "has_violations": false,
    "case_count": 0,
    "cases": []
  },
  "aai_zone": {
    "in_restriction_zone": false
  },
  "overall_status": "warning"
}
```

### Node.js Queue Endpoints

**Submit Verification Job**
```bash
POST /api/property/verify
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "lat": 12.9716,
  "lng": 77.5946,
  "property_id": "PROP-12345"
}

Response (202 Accepted):
{
  "job_id": "1",
  "status": "queued",
  "message": "Verification started. Poll status endpoint."
}
```

**Poll Job Status**
```bash
GET /api/property/verify/status/1
Authorization: Bearer <JWT_TOKEN>

Response:
{
  "job_id": "1",
  "status": "active",
  "progress": {
    "steps_completed": 7,
    "steps_total": 14,
    "current_step": 7,
    "logs": [
      {
        "step": 1,
        "message": "Validating input coordinates",
        "timestamp": "2024-01-01T10:00:00Z"
      }
    ]
  },
  "created_at": "2024-01-01T10:00:00Z"
}
```

## Testing

### Test Database Connection

```bash
# Python
python -c "from app.database import Database; import asyncio; asyncio.run(Database.create_pool())"

# Node.js
node -e "const redis = require('ioredis'); const client = new redis(); client.ping().then(() => console.log('Redis OK'))"
```

### Test FastAPI Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Reverse geocoding
curl -X POST http://localhost:8000/api/location/resolve \
  -H "Content-Type: application/json" \
  -d '{"lat": 12.9716, "lng": 77.5946}'

# Survey number
curl http://localhost:8000/api/gis/survey-number?lat=12.9716&lng=77.5946

# Zone check
curl http://localhost:8000/api/gis/zone-check?lat=12.9716&lng=77.5946
```

### Test Node.js Queue

```bash
# Health check
curl http://localhost:3000/health

# Queue health
curl http://localhost:3000/health/queue

# Submit job (requires JWT token)
curl -X POST http://localhost:3000/api/property/verify \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"lat": 12.9716, "lng": 77.5946, "property_id": "TEST-001"}'
```

## Redis Cache Configuration

Cache keys follow the pattern: `gis_cache:{endpoint}:{lat}:{lng}`

- **TTL**: 48 hours (172800 seconds)
- **Precision**: 6 decimal places (~11cm)
- **Endpoints cached**:
  - `resolve` - Reverse geocoding results
  - `survey-number` - Survey parcel data
  - `zone-check` - Zone compliance results

### Cache Management

```python
# Invalidate all GIS cache
from app.cache import CacheManager
import asyncio
asyncio.run(CacheManager.invalidate_pattern("gis_cache:*"))
```

## Performance Targets

- **Cached queries**: < 50ms
- **Uncached spatial queries**: < 200ms
- **Zone check (parallel)**: < 500ms
- **Queue job submission**: < 100ms (immediate return)

## Production Considerations

### Security
- Replace mock JWT authentication with production auth
- Configure CORS origins appropriately
- Use environment variables for all secrets
- Enable HTTPS/TLS

### Scaling
- FastAPI: Run with multiple workers (gunicorn + uvicorn workers)
- Node.js: Scale horizontally with multiple queue instances
- Redis: Use Redis Cluster for high availability
- PostgreSQL: Configure connection pooling and read replicas

### Monitoring
- Implement structured logging (Winston for Node.js, Python logging for FastAPI)
- Set up metrics collection (Prometheus/Grafana)
- Monitor queue backlog and job failure rates
- Track cache hit/miss ratios

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
pg_isready

# Test PostGIS extension
psql -d gis_engine -c "SELECT PostGIS_Version();"
```

### Redis Connection Issues
```bash
# Check Redis is running
redis-cli ping

# Check Redis logs
redis-cli MONITOR
```

### Port Conflicts
```bash
# Check what's using ports
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac
```

## Team Integration

This is **Member 3's** contribution to the GIS Engine project:

- **Member 1**: Frontend UI (React/Vue)
- **Member 2**: Data Collection & Validation
- **Member 3**: Backend Architecture (This project)
- **Member 4**: Web Scrapers & External APIs
- **Member 5**: DevOps & Deployment

## License

MIT License - See LICENSE file for details

## Contact

For questions or issues, please contact the development team.
