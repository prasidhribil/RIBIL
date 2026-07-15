# Missing Requirements - Environment Variables, API Keys, and External Datasets

## Critical Missing Environment Variables

### 1. GOOGLE_MAPS_API_KEY
- **Status:** REQUIRED but OPTIONAL (fallback to Nominatim available)
- **Purpose:** Reverse geocoding for location resolution
- **Impact:** Without this key, the system falls back to Nominatim (free but rate-limited to 1 request/second)
- **How to Obtain:** 
  - Go to Google Cloud Console
  - Create a project
  - Enable Maps JavaScript API and Geocoding API
  - Create API credentials
  - Add to `.env` file: `GOOGLE_MAPS_API_KEY=your_actual_key_here`
- **Cost:** Free tier: $200 credit/month (approximately 40,000 geocoding requests)
- **Current Value:** `your_google_maps_api_key` (placeholder)

### 2. JWT_SECRET
- **Status:** REQUIRED for Node.js Queue Service
- **Purpose:** JWT token verification for property verification API endpoints
- **Impact:** Without a secure secret, authentication is vulnerable to attacks
- **How to Obtain:** Generate a secure random string
  ```powershell
  # Using Node.js
  node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
  ```
- **Current Value:** `your_jwt_secret_key_here` (placeholder)
- **Recommendation:** Use a strong 32+ character random string

## Optional Environment Variables (Have Defaults)

### DB_PASSWORD
- **Current Value:** `your_password` (placeholder in .env.example)
- **Recommended Value:** `postgres` (matches docker-compose.yml)
- **Action Required:** Update `.env` to match docker-compose.yml password

### REDIS_PASSWORD
- **Current Value:** Empty (no password)
- **Recommended Value:** Leave empty for development
- **Action Required:** None (Redis in docker-compose.yml has no password)

## External API Dependencies

### 1. Google Maps Geocoding API
- **Endpoint:** https://maps.googleapis.com/maps/api/geocode/json
- **Purpose:** Primary reverse geocoding service
- **Rate Limits:** 50 requests/second (with API key)
- **Fallback:** Nominatim (OpenStreetMap)
- **Authentication:** API Key required
- **Cost:** Free tier available

### 2. Nominatim API (OpenStreetMap)
- **Endpoint:** https://nominatim.openstreetmap.org/reverse
- **Purpose:** Fallback reverse geocoding service
- **Rate Limits:** 1 request/second (strictly enforced)
- **Authentication:** None required (but User-Agent header mandatory)
- **Cost:** Free
- **Usage Policy:** Must include unique User-Agent header (already implemented)

## External Dataset Requirements (Member 4 Integration)

### 1. Property Document Scraper API
- **Status:** NOT IMPLEMENTED (TODO in verifyQueue.js)
- **Purpose:** Scrape property documents from government portals
- **Integration Point:** Step 8 in Bull Queue workflow
- **Required Data:** 
  - Property documents (PDFs, scanned images)
  - Encumbrance certificates
  - Title deeds
- **Current Implementation:** Mock delay (2 seconds)
- **Action Required:** Coordinate with Member 4 for scraper API endpoint

### 2. Property Details Extraction Service
- **Status:** NOT IMPLEMENTED (TODO in verifyQueue.js)
- **Purpose:** Extract structured data from scraped documents
- **Integration Point:** Step 9 in Bull Queue workflow
- **Required Data:** 
  - Owner names
  - Property dimensions
  - Survey numbers
  - Transaction history
- **Current Implementation:** Mock delay (1 second)
- **Action Required:** Coordinate with Member 4 for extraction service

### 3. Encumbrance Database
- **Status:** NOT IMPLEMENTED (TODO in verifyQueue.js)
- **Purpose:** Query property encumbrance records
- **Integration Point:** Step 11 in Bull Queue workflow
- **Required Data:** 
  - Mortgage records
  - Liens
  - Legal disputes
- **Current Implementation:** Mock delay (1 second)
- **Action Required:** Coordinate with Member 4 for database access

### 4. Tax Payment Database
- **Status:** NOT IMPLEMENTED (TODO in verifyQueue.js)
- **Purpose:** Verify property tax payment status
- **Integration Point:** Step 12 in Bull Queue workflow
- **Required Data:** 
  - Property tax records
  - Payment history
  - Outstanding dues
- **Current Implementation:** Mock delay (1 second)
- **Action Required:** Coordinate with Member 4 for database access

## GIS Data Requirements (Empty Tables)

### 1. survey_parcels Table
- **Status:** EMPTY (requires manual data)
- **Purpose:** Point-in-polygon survey number lookup
- **Required Data:** Digitized survey parcel polygons
- **Data Format:** Shapefile (.shp) or GeoJSON
- **Coordinate System:** WGS84 (EPSG:4326)
- **Source Options:**
  - Bhoomi portal (Karnataka land records)
  - Survey of India
  - Local municipal survey departments
- **QGIS Workflow Required:** Yes
  - Import shapefile/GeoJSON
  - Reproject to WGS84 if needed
  - Export to PostgreSQL using PostGIS plugin
- **Estimated Records:** 100,000+ for Bengaluru region
- **Impact:** Without this data, survey number lookup returns 404

### 2. water_bodies Table
- **Status:** EMPTY (requires manual data)
- **Purpose:** NGT lake buffer zone compliance checks (75m blocked, 75-150m warning)
- **Required Data:** Bengaluru lakes and water body polygons
- **Data Format:** Shapefile (.shp) or GeoJSON
- **Coordinate System:** WGS84 (EPSG:4326)
- **Source Options:**
  - KSRSAC (Karnataka State Remote Sensing Applications Centre)
  - NGT (National Green Tribunal) lake data
  - BBMP (Bruhat Bengaluru Mahanagara Palike) lake database
- **QGIS Workflow Required:** Yes
  - Import shapefile/GeoJSON
  - Reproject to WGS84 if needed
  - Calculate buffer zones (75m, 150m) if not pre-calculated
  - Export to PostgreSQL using PostGIS plugin
- **Estimated Records:** 200+ lakes in Bengaluru
- **Impact:** Without this data, lake buffer checks return default (no restrictions)

### 3. cdp_zones Table
- **Status:** EMPTY (requires manual data)
- **Purpose:** BDA Master Plan 2031 zone compliance checks
- **Required Data:** Bangalore Development Authority Comprehensive Development Plan zones
- **Data Format:** Shapefile (.shp) or GeoJSON
- **Coordinate System:** WGS84 (EPSG:4326)
- **Source Options:**
  - BDA (Bangalore Development Authority) official CDP 2031
  - BDA Master Plan shapefiles
  - Urban Development Department, Karnataka
- **QGIS Workflow Required:** Yes
  - Import shapefile/GeoJSON
  - Reproject to WGS84 if needed
  - Validate zone classifications (Residential, Commercial, Industrial, Green Belt, etc.)
  - Export to PostgreSQL using PostGIS plugin
- **Estimated Records:** 50-100 zone polygons
- **Impact:** Without this data, CDP zone checks return default (not in any zone)

### 4. aai_zones Table
- **Status:** EMPTY (requires manual data)
- **Purpose:** Airport Authority of India restriction zones (BIAL/HAL)
- **Required Data:** Airport obstacle limitation surfaces and restriction zones
- **Data Format:** Shapefile (.shp) or GeoJSON
- **Coordinate System:** WGS84 (EPSG:4326)
- **Source Options:**
  - AAI (Airport Authority of India) official obstruction charts
  - BIAL (Kempegowda International Airport) technical data
  - HAL Airport technical data
- **QGIS Workflow Required:** Yes
  - Import shapefile/GeoJSON
  - Reproject to WGS84 if needed
  - Validate restriction types (Runway Protection Zone, Obstacle Free Zone, etc.)
  - Export to PostgreSQL using PostGIS plugin
- **Estimated Records:** 10-20 zone polygons per airport
- **Impact:** Without this data, AAI zone checks return default (not in restriction zone)

### 5. court_cases Table
- **Status:** EMPTY (requires manual data)
- **Purpose:** NGT Tribunal orders and violation records
- **Required Data:** NGT case records for Bengaluru region
- **Data Format:** CSV or JSON
- **Source Options:**
  - NGT (National Green Tribunal) official case database
  - Karnataka State Pollution Control Board
  - Environmental clearance records
- **QGIS Workflow Required:** No (tabular data only)
- **Import Method:** Direct SQL INSERT or CSV import
- **Estimated Records:** 1000+ active cases
- **Impact:** Without this data, NGT orders check returns default (no violations)

## Summary of Missing Requirements

### Immediate Action Required (Blocking Core Functionality)
1. **JWT_SECRET** - Required for Node.js Queue Service authentication
2. **DB_PASSWORD** - Must match docker-compose.yml (set to `postgres`)

### Recommended for Full Functionality
1. **GOOGLE_MAPS_API_KEY** - For reliable reverse geocoding (fallback available)
2. **survey_parcels data** - For survey number lookup
3. **water_bodies data** - For lake buffer compliance checks
4. **cdp_zones data** - For BDA Master Plan compliance
5. **aai_zones data** - For airport restriction checks
6. **court_cases data** - For NGT tribunal order checks

### Member 4 Integration Required (For Complete Verification Workflow)
1. **Property Document Scraper API** - Step 8 in queue workflow
2. **Property Details Extraction Service** - Step 9 in queue workflow
3. **Encumbrance Database** - Step 11 in queue workflow
4. **Tax Payment Database** - Step 12 in queue workflow

### Current Runnable State
- **FastAPI Service:** Can start and serve basic APIs
- **Reverse Geocoding:** Works with Nominatim fallback (rate-limited)
- **Administrative Hierarchy:** Works (karnataka_admin table seeded with 30,000 mock records)
- **Survey Number Lookup:** Returns 404 (no survey_parcels data)
- **Zone Checks:** Returns default values (no GIS data)
- **Node.js Queue Service:** Can start and accept jobs (but workflow is mocked)
