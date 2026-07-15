# RUN_PROJECT.md - Windows Setup Instructions

## Prerequisites

- **Windows 10/11**
- **Docker Desktop** (for PostgreSQL + PostGIS and Redis)
- **Python 3.10+**
- **Node.js 18+**
- **Git** (optional, for version control)

## Step 1: Clone/Navigate to Project

```powershell
cd "c:\Users\Poorvi A V\OneDrive\Desktop\land record"
```

## Step 2: Start Docker Services (PostgreSQL + PostGIS + Redis)

```powershell
docker-compose up -d
```

**Verify services are running:**
```powershell
docker-compose ps
```

Expected output should show `gis_postgres` and `gis_redis` as "Up".

**Wait 10-15 seconds** for PostgreSQL to fully initialize and enable PostGIS extension.

## Step 3: Verify PostGIS Installation

```powershell
docker exec -it gis_postgres psql -U postgres -d gis_engine -c "SELECT PostGIS_Version();"
```

Expected output:
```
 postgis_version 
-----------------
 3.3.x
(1 row)
```

## Step 4: Run Database Migrations

The migration script is automatically executed by Docker via the docker-entrypoint-initdb.d directory. However, if you need to run it manually:

```powershell
docker exec -it gis_postgres psql -U postgres -d gis_engine -f database/migrations/001_initial_schema.sql
```

**Verify tables were created:**
```powershell
docker exec -it gis_postgres psql -U postgres -d gis_engine -c "\dt"
```

Expected tables:
- karnataka_admin
- survey_parcels
- cdp_zones
- water_bodies
- court_cases
- aai_zones

## Step 5: Set Up Python Virtual Environment

```powershell
python -m venv venv
```

**Activate virtual environment:**
```powershell
venv\Scripts\activate
```

## Step 6: Install Python Dependencies

```powershell
pip install -r requirements.txt
```

**Verify key packages:**
```powershell
pip list | findstr "fastapi uvicorn asyncpg psycopg redis httpx"
```

Expected output should show:
- fastapi
- uvicorn
- asyncpg
- psycopg2-binary
- redis
- httpx

## Step 7: Seed Karnataka Admin Data

```powershell
python database/seeds/seed_karnataka_admin.py
```

This will generate 30,000 mock village records for Bengaluru Urban and Rural districts.

**Verify data was seeded:**
```powershell
docker exec -it gis_postgres psql -U postgres -d gis_engine -c "SELECT COUNT(*) FROM karnataka_admin;"
```

Expected output: ~30,000 records.

## Step 8: Configure Environment Variables

Edit the `.env` file and update the following values:

```env
# PostgreSQL Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gis_engine
DB_USER=postgres
DB_PASSWORD=postgres

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Google Geocoding API (OPTIONAL - for reverse geocoding)
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
NODE_APP_PORT=3000

# JWT Secret for Authentication (REQUIRED for Node.js queue)
JWT_SECRET=change_this_to_a_secure_random_string

# Cache Configuration
CACHE_TTL_SECONDS=172800

# Logging
LOG_LEVEL=INFO
```

**Note:** Without a Google Maps API key, the system will fall back to Nominatim (free but rate-limited).

## Step 9: Install Node.js Dependencies

```powershell
npm install
```

**Verify key packages:**
```powershell
npm list bull ioredis express
```

## Step 10: Start FastAPI Service (Port 8000)

**In a new terminal window:**

```powershell
cd "c:\Users\Poorvi A V\OneDrive\Desktop\land record"
venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Verify FastAPI is running:**
```powershell
curl http://localhost:8000/health
```

Expected output:
```json
{
  "status": "healthy",
  "service": "gis-engine",
  "database": "connected",
  "cache": "connected"
}
```

**Access API documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Step 11: Start Node.js Bull Queue Service (Port 3000)

**In another new terminal window:**

```powershell
cd "c:\Users\Poorvi A V\OneDrive\Desktop\land record"
npm start
```

**Verify Node.js service is running:**
```powershell
curl http://localhost:3000/health
```

Expected output:
```json
{
  "status": "healthy",
  "service": "gis-queue-service",
  "timestamp": "2024-01-01T10:00:00.000Z"
}
```

**Verify queue health:**
```powershell
curl http://localhost:3000/health/queue
```

Expected output:
```json
{
  "status": "healthy",
  "queue": {
    "waiting": 0,
    "active": 0,
    "completed": 0,
    "failed": 0
  },
  "timestamp": "2024-01-01T10:00:00.000Z"
}
```

## Step 12: Test FastAPI Endpoints

### Test Root Endpoint
```powershell
curl http://localhost:8000/
```

### Test Reverse Geocoding (with Google API key)
```powershell
curl -X POST http://localhost:8000/api/location/resolve -H "Content-Type: application/json" -d "{\"lat\": 12.9716, \"lng\": 77.5946}"
```

### Test Hobli List
```powershell
curl "http://localhost:8000/api/location/hobli-list?district=Bengaluru%20Urban&taluk=Bengaluru%20South"
```

### Test Survey Number (will return 404 without survey_parcels data)
```powershell
curl "http://localhost:8000/api/gis/survey-number?lat=12.9716&lng=77.5946"
```

### Test Zone Check (will return default values without GIS data)
```powershell
curl "http://localhost:8000/api/gis/zone-check?lat=12.9716&lng=77.5946"
```

## Step 13: Test Node.js Queue Endpoints

### Generate JWT Token (for testing)
```powershell
# Using Node.js to generate a test token
node -e "const jwt = require('jsonwebtoken'); console.log(jwt.sign({id: 'test_user'}, 'change_this_to_a_secure_random_string'));"
```

### Submit Verification Job (requires JWT)
```powershell
curl -X POST http://localhost:3000/api/property/verify -H "Authorization: Bearer YOUR_JWT_TOKEN" -H "Content-Type: application/json" -d "{\"lat\": 12.9716, \"lng\": 77.5946, \"property_id\": \"TEST-001\"}"
```

### Poll Job Status
```powershell
curl http://localhost:3000/api/property/verify/status/1 -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Step 14: Stop Services

**Stop Docker services:**
```powershell
docker-compose down
```

**Stop FastAPI:** Press `Ctrl+C` in the FastAPI terminal

**Stop Node.js:** Press `Ctrl+C` in the Node.js terminal

## Troubleshooting

### PostgreSQL Connection Issues
```powershell
# Check if PostgreSQL is running
docker-compose ps

# View PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Redis Connection Issues
```powershell
# Check if Redis is running
docker-compose ps

# View Redis logs
docker-compose logs redis

# Test Redis connection
docker exec -it gis_redis redis-cli ping
```

### Port Already in Use
```powershell
# Check what's using port 8000
netstat -ano | findstr :8000

# Check what's using port 3000
netstat -ano | findstr :3000

# Check what's using port 5432
netstat -ano | findstr :5432

# Check what's using port 6379
netstat -ano | findstr :6379
```

### Python Import Errors
```powershell
# Ensure virtual environment is activated
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Node.js Module Errors
```powershell
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rmdir /s /q node_modules
npm install
```

## Database Connectivity Verification

```powershell
# Test PostgreSQL connection from Python
python -c "from app.database import Database; import asyncio; asyncio.run(Database.create_pool())"

# Test Redis connection from Python
python -c "from app.cache import CacheManager; import asyncio; asyncio.run(CacheManager.connect())"
```

## Clean Start (Reset Everything)

```powershell
# Stop and remove Docker containers and volumes
docker-compose down -v

# Remove Python virtual environment
rmdir /s /q venv

# Remove Node.js modules
rmdir /s /q node_modules

# Remove logs
rmdir /s /q logs

# Re-create logs directory
mkdir logs

# Start fresh from Step 2
```

## Summary of Running Services

Once all steps are complete, you should have:

1. **PostgreSQL + PostGIS** running on port 5432 (Docker)
2. **Redis** running on port 6379 (Docker)
3. **FastAPI** running on port 8000 (Python)
4. **Node.js Bull Queue** running on port 3000 (Node.js)

All services should be healthy and ready to accept requests.
