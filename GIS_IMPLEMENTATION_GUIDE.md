# GIS Implementation Guide - Bengaluru Urban Cadastral Data

## Objective

Populate `survey_parcels` table with real Bengaluru village cadastral data to enable the `GET /api/gis/survey-number` endpoint to return actual survey numbers instead of 404 errors.

## Target Scope

- **District:** Bengaluru Urban
- **Initial Pilot:** 2 villages (Bellandur and Kadubeesanahalli - Begur Hobli, Bengaluru South Taluk)
- **Estimated Parcels:** 200-500 parcels per village
- **Timeline:** 1-2 weeks for pilot completion

---

## Part 1: Fastest Sources for Cadastral/Tippan Maps

### Recommended Villages for Pilot

Based on data availability and proximity to tech corridor:

1. **Bellandur** (Begur Hobli, Bengaluru South Taluk)
   - High-profile area with good documentation
   - Near Outer Ring Road
   - Survey numbers: 1-250 approximately

2. **Kadubeesanahalli** (Begur Hobli, Bengaluru South Taluk)
   - Adjacent to Bellandur
   - Well-documented in land records
   - Survey numbers: 1-200 approximately

### Data Sources Ranked by Speed

#### Source 1: Bhoomi RTC (Record of Rights, Tenancy and Crops) Portal - FASTEST

**URL:** https://bhoomi.karnataka.gov.in

**Why Fastest:**
- Online portal with immediate access
- No physical visit required
- PDF tippan maps downloadable
- Free of cost

**Steps to Download:**
1. Visit https://bhoomi.karnataka.gov.in
2. Click on "View RTC" or "View Pahani"
3. Select District: "Bengaluru Urban"
4. Select Taluk: "Bengaluru South"
5. Select Hobli: "Begur"
6. Select Village: "Bellandur" or "Kadubeesanahalli"
7. Enter Survey Number (start with 1, iterate through available numbers)
8. Click "View RTC"
9. Download the RTC document (contains tippan map as embedded image)
10. Extract tippan map image from PDF

**Limitations:**
- One survey number at a time
- Tippan maps are low-resolution scanned images
- No georeferencing information
- May require multiple visits if session times out

**Estimated Time:** 2-3 hours per village (100-200 survey numbers)

---

#### Source 2: Karnataka Land Records Department (Physical Visit) - MEDIUM SPEED

**Location:** 
- Bengaluru Urban District Revenue Office
- Near K.R. Circle, Bengaluru

**Why Medium Speed:**
- Can request entire village tippan book at once
- Higher resolution maps
- Official certified copies
- Requires physical visit and paperwork

**Steps to Obtain:**
1. Visit District Revenue Office, Bengaluru Urban
2. Submit application for "Village Map" or "Tippan Book"
3. Pay nominal fee (₹50-100 per village)
4. Provide village details: Bellandur/Kadubeesanahalli
5. Wait 1-2 business days for processing
6. Collect scanned copies or physical maps

**Limitations:**
- Requires physical visit
- Government office hours only
- Processing time 1-2 days
- May require RTI if denied

**Estimated Time:** 1-2 days including visit and processing

---

#### Source 3: Survey of India Toposheets - SLOW BUT ACCURATE

**URL:** https://surveyofindia.gov.in

**Why Slow:**
- Not cadastral-level detail
- Topographic maps (1:50,000 scale)
- Requires purchase or special request
- General reference only

**Not Recommended For:** Parcel-level digitization

**Use Case:** Background reference for village boundaries

---

#### Source 4: OpenStreetMap / Google Earth - FAST BUT NOT CADASTRAL

**URL:** https://www.openstreetmap.org or Google Earth Pro

**Why Fast:**
- Immediately accessible
- High-resolution satellite imagery
- Can trace approximate boundaries

**Limitations:**
- Not official cadastral data
- No survey numbers
- Legal validity questionable
- For reference only

**Use Case:** Preliminary boundary tracing before official maps arrive

---

### Recommended Approach: Hybrid Strategy

**Phase 1 (Immediate - Today):**
- Download tippan maps from Bhoomi for 2 villages
- Start with Bellandur survey numbers 1-50
- Use OpenStreetMap for village boundary reference

**Phase 2 (Parallel - This Week):**
- Submit application to District Revenue Office for complete village maps
- This provides backup and higher-resolution source

**Phase 3 (If Bhoomi fails):**
- File RTI application for village tippan books
- RTI timeline: 30 days (statutory)

---

## Part 2: Detailed Bhoomi Download Process

### Step-by-Step Guide for Bellandur Village

#### Prerequisites
- Computer with internet connection
- PDF reader (Adobe Acrobat or browser)
- Image extraction tool (Adobe Acrobat or online PDF to image converter)
- Survey number list (start from 1, iterate)

#### Download Process

**Step 1: Access Bhoomi Portal**
```
URL: https://bhoomi.kannada.gov.in (Kannada version)
     https://bhoomi.karnataka.gov.in (English version)
```

**Step 2: Navigate to RTC View**
- Click on "View RTC" or "View Pahani" button
- Select language (English recommended)

**Step 3: Select Administrative Hierarchy**
```
District: Bengaluru Urban
Taluk: Bengaluru South
Hobli: Begur
Village: Bellandur
```

**Step 4: Enter Survey Number**
- Start with Survey Number: 1
- If survey number 1 doesn't exist, try 2, 3, etc.
- Note: Survey numbers may not be sequential
- Common pattern: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15...

**Step 5: View and Download RTC**
- Click "View RTC" or "Submit"
- RTC document opens as PDF
- The PDF contains:
  - Landowner details
  - Survey number
  - Extent in acres/guntas
  - **Tippan map** (usually on page 2 or 3)
  - Encumbrance details

**Step 6: Extract Tippan Map Image**
- Open PDF in Adobe Acrobat
- Navigate to page with tippan map
- Use "Export Image" or "Save as Image"
- Save as PNG or JPG (300 DPI recommended)
- Naming convention: `bellandur_sn_001.png`, `bellandur_sn_002.png`, etc.

**Alternative: Online PDF to Image Converter**
- Upload PDF to https://www.ilovepdf.com/pdf_to_image
- Convert to PNG
- Download images

**Step 7: Organize Downloaded Maps**
Create folder structure:
```
C:\GIS_Project\Bellandur\
  ├── tippan_maps\
  │   ├── bellandur_sn_001.png
  │   ├── bellandur_sn_002.png
  │   └── ...
  ├── georeferenced\
  └── digitized\
```

**Step 8: Repeat for All Survey Numbers**
- Iterate through survey numbers 1-50 for pilot
- Skip numbers that return "No records found"
- Document which survey numbers are available
- Create spreadsheet to track progress:
  ```
  Survey Number | Downloaded | Georeferenced | Digitized | Notes
  1            | Yes        | No           | No        | 
  2            | Yes        | No           | No        |
  ...
  ```

**Step 9: Extract Metadata from RTC**
For each survey number, record:
- Survey number (e.g., "1", "2", "3/1")
- Extent in acres (e.g., "2.5 acres")
- Owner name (for reference)
- Village: "Bellandur"
- Hobli: "Begur"
- District: "Bengaluru Urban"

This metadata will be used as attributes in QGIS.

---

### Alternative: Bhoomi Mobile App

**App Name:** Bhoomi Karnataka (available on Google Play Store)

**Advantages:**
- Mobile-friendly interface
- Can download on smartphone
- Easier for quick checks

**Disadvantages:**
- May not have tippan map download feature
- Screen resolution limitations
- Harder to extract images

**Recommendation:** Use web portal for desktop work

---

## Part 3: QGIS Installation and Configuration on Windows

### System Requirements

- **OS:** Windows 10/11 (64-bit)
- **RAM:** 8 GB minimum (16 GB recommended)
- **Disk Space:** 1 GB for QGIS + 10 GB for project data
- **Processor:** Intel i5 or equivalent

### Installation Steps

#### Step 1: Download QGIS

**Official Download Page:** https://qgis.org/en/site/forusers/download.html

**Recommended Version:** QGIS LTR (Long Term Release)
- Current LTR: QGIS 3.28.x or later
- LTR is stable and supported for 1 year
- Avoid latest release (may have bugs)

**Direct Download Link (Windows 64-bit):**
```
https://download.qgis.org/downloads/QGIS-OSGeo4W-3.28-1-1.msi
```
(Update version number as needed)

#### Step 2: Run Installer

1. Double-click the downloaded `.msi` file
2. Click "Next" on welcome screen
3. Accept license agreement
4. Choose installation location (default: `C:\Program Files\QGIS 3.28`)
5. Select components:
   - ✅ QGIS (required)
   - ✅ GRASS GIS (recommended for advanced analysis)
   - ✅ SAGA GIS (optional)
   - ✅ GDAL/OGR (required for GeoJSON export)
   - ✅ Python (required for plugins)
6. Click "Install"
7. Wait for installation (5-10 minutes)
8. Click "Finish"

#### Step 3: Verify Installation

1. Open QGIS from Start Menu
2. You should see the QGIS interface with:
   - Menu bar at top
   - Toolbar below menu
   - Layers panel on left
   - Map canvas in center
   - Status bar at bottom

#### Step 4: Configure QGIS Settings

**Set Coordinate Reference System (CRS):**
1. Go to **Settings** → **Options**
2. Go to **CRS** tab
3. Check "Use CRS from first layer added" (recommended)
4. Default CRS: EPSG:4326 - WGS 84
5. Click "OK"

**Enable Auto-Save:**
1. Go to **Settings** → **Options**
2. Go to **Rendering** tab
3. Check "Save project changes when required"
4. Click "OK"

**Configure Digitizing Toolbar:**
1. Right-click on toolbar area
2. Select **Digitizing Toolbar**
3. Digitizing tools appear in toolbar

**Configure Georeferencer Plugin:**
1. Go to **Plugins** → **Manage and Install Plugins**
2. Search for "Georeferencer GDAL"
3. Check if installed (should be by default)
4. If not, select and click "Install Plugin"

#### Step 5: Install Recommended Plugins

**OpenLayers Plugin (for background maps):**
1. Go to **Plugins** → **Manage and Install Plugins**
2. Search for "QuickMapServices" or "OpenLayers"
3. Install "QuickMapServices" (more reliable)
4. After installation, go to **Web** → **QuickMapServices** → **Settings**
5. Click "Get contributed pack"
6. Select all services and click "OK"

**Now you can add:**
- Google Satellite
- OpenStreetMap
- Bing Maps
- As background reference

#### Step 6: Create Project Structure

Create folders:
```
C:\GIS_Project\
  ├── Bellandur\
  │   ├── tippan_maps\        (raw scanned images)
  │   ├── georeferenced\      (georeferenced TIFF files)
  │   ├── digitized\          (QGIS project files)
  │   └── export\             (final GeoJSON exports)
  └── Kadubeesanahalli\
      ├── tippan_maps\
      ├── georeferenced\
      ├── digitized\
      └── export\
```

#### Step 7: Create New QGIS Project

1. Open QGIS
2. Go to **Project** → **New**
3. Save as: `C:\GIS_Project\Bellandur\digitized\bellandur_qgis_project.qgz`
4. Set Project CRS: EPSG:4326 (WGS 84)
   - Go to **Project** → **Properties** → **CRS**
   - Filter: "4326"
   - Select "WGS 84"
   - Click "OK"

#### Step 8: Add Background Map

1. Go to **Web** → **QuickMapServices** → **OSM** → **OSM Standard**
2. OpenStreetMap loads as background
3. Navigate to Bellandur area:
   - Use search bar (Ctrl+F)
   - Type: "Bellandur, Bengaluru"
   - QGIS zooms to Bellandur
4. Save bookmark:
   - Go to **View** → **Bookmarks** → **Add Bookmark**
   - Name: "Bellandur Village"
   - Click "OK"

---

## Part 4: Georeferencing Workflow

### Understanding Georeferencing

**Purpose:** Assign real-world coordinates to scanned tippan maps

**Input:** Scanned tippan map image (PNG/JPG, no coordinates)
**Output:** GeoTIFF file with embedded georeferencing information
**Method:** Thin Plate Spline (TPS) transformation
**Minimum GCPs:** 4 ground control points
**Target CRS:** EPSG:4326 (WGS 84)

### Step-by-Step Georeferencing

#### Step 1: Open Georeferencer

1. In QGIS, go to **Raster** → **Georeferencer** → **Georeferencer**
2. Georeferencer window opens (separate from main QGIS window)

#### Step 2: Load Tippan Map Image

1. Click **Open Raster** (folder icon)
2. Navigate to: `C:\GIS_Project\Bellandur\tippan_maps\`
3. Select: `bellandur_sn_001.png`
4. Click **Open**
5. Image loads in Georeferencer window

#### Step 3: Set Transformation Settings

1. Click **Transformation Settings** (gear icon)
2. Configure settings:

**Transformation Type:**
- Select: **Thin Plate Spline (TPS)**
- Why TPS: Handles non-linear distortions common in scanned paper maps
- Alternative: Polynomial 1 (linear, less accurate for old maps)

**Resampling Method:**
- Select: **Cubic** (best quality)
- Alternative: Nearest Neighbor (faster, lower quality)

**Target CRS:**
- Click "..." button
- Filter: "4326"
- Select: **EPSG:4326 - WGS 84**
- Click "OK"

**Output File:**
- Browse to: `C:\GIS_Project\Bellandur\georeferenced\`
- Filename: `bellandur_sn_001_georef.tif`
- Format: GeoTIFF

**Checkboxes:**
- ✅ Load in QGIS when done
- ✅ Create world file
- ✅ Use 0 as transparency value (if map has white background)

3. Click **OK**

#### Step 4: Add Ground Control Points (GCPs)

**What are GCPs?**
- Known locations on the map with real-world coordinates
- Match features on scanned map to same features on reference map

**GCP Selection Strategy:**
- Choose 4-6 clearly identifiable points
- Best GCPs: Road intersections, temple corners, landmark boundaries
- Spread GCPs across the map (not all in one corner)
- Avoid points that may have changed over time

**Process for Adding GCPs:**

**GCP 1: Road Intersection**
1. In Georeferencer window, zoom to a clear road intersection on tippan map
2. Click **Add Point** (yellow crosshair icon)
3. Click on the intersection in tippan map
4. "Map Canvas" window opens (shows QGIS main window with background map)
5. Navigate to the same intersection in QGIS (using OpenStreetMap background)
6. Click on the same intersection in QGIS
7. Coordinates are automatically captured
8. Click "OK"
9. GCP 1 added to table

**GCP 2: Temple/Building Corner**
1. Repeat process for another clear landmark
2. Choose a corner of a temple or permanent building
3. Add point in tippan map
4. Match to same location in QGIS
5. GCP 2 added

**GCP 3: Another Road Intersection**
1. Choose intersection on opposite side of map
2. Add point
3. Match in QGIS
4. GCP 3 added

**GCP 4: Village Boundary Point**
1. Choose point on village boundary (if visible)
2. Add point
3. Match in QGIS
4. GCP 4 added

**GCP 5 & 6 (Optional but Recommended):**
- Add 2 more points for better accuracy
- Aim for 6 GCPs total
- More GCPs = better transformation accuracy

#### Step 5: Verify GCP Accuracy

**Check GCP Table:**
- Look at "dX" and "dY" columns (residual errors)
- Ideal: dX and dY should be small (< 5 meters)
- If errors are large (> 10 meters), remove and re-add GCP

**Check GCP Distribution:**
- GCPs should be spread across the map
- Not clustered in one area
- Cover all four corners if possible

#### Step 6: Run Georeferencing

1. Click **Start Georeferencing** (green play icon)
2. Progress bar shows processing
3. Georeferenced GeoTIFF created at specified location
4. GeoTIFF automatically loads in QGIS main window

#### Step 7: Verify Georeferencing

**Visual Check:**
1. In QGIS main window, georeferenced map should overlay correctly on background
2. Toggle visibility on/off to check alignment
3. Roads should match OpenStreetMap roads
4. Village boundaries should align

**Accuracy Check:**
1. Add a few more test GCPs (without running transformation)
2. Check if they align correctly
3. If misaligned, adjust existing GCPs and re-run

#### Step 8: Save GCP Points

1. In Georeferencer, go to **File** → **Save GCP Points as**
2. Save as: `bellandur_sn_001_gcps.points`
3. This allows you to reload GCPs later if needed

#### Step 9: Repeat for All Tippan Maps

Repeat steps 1-8 for all downloaded tippan maps:
- bellandur_sn_002.png
- bellandur_sn_003.png
- ... and so on

**Time Estimate:** 10-15 minutes per map (including GCP selection)

**Total Time for 50 maps:** 8-12 hours

---

### Alternative: Batch Georeferencing (Advanced)

If all tippan maps are from same village and same scale:

1. Georeference first map carefully with 6 GCPs
2. Save GCP points
3. For subsequent maps:
   - Load saved GCP points
   - Adjust GCP positions slightly if needed
   - Run transformation
4. This saves time as GCP locations are similar

---

## Part 5: Digitizing Parcel Boundaries

### Understanding Digitization

**Purpose:** Trace parcel boundaries from georeferenced tippan maps to create vector polygons

**Input:** Georeferenced GeoTIFF files
**Output:** Polygon shapefile or GeoPackage
**Method:** Manual on-screen digitizing
**Tools:** QGIS Digitizing Toolbar

### Step-by-Step Digitization

#### Step 1: Create New Polygon Layer

1. In QGIS, go to **Layer** → **Create Layer** → **New Shapefile Layer**
2. Configure:

**File:**
- Format: ESRI Shapefile
- File name: `bellandur_parcels.shp`
- Location: `C:\GIS_Project\Bellandur\digitized\`

**Geometry:**
- Type: Polygon
- CRS: EPSG:4326 (WGS 84)

**Attributes (Field Configuration):**
Click "Add Field" for each:

| Field Name | Type | Width | Precision | Description |
|------------|------|-------|-----------|-------------|
| survey_no | Text | 20 | 0 | Survey number (e.g., "1", "2/1") |
| village | Text | 200 | 0 | Village name (e.g., "Bellandur") |
| hobli | Text | 100 | 0 | Hobli name (e.g., "Begur") |
| district | Text | 100 | 0 | District (e.g., "Bengaluru Urban") |
| area_acres | Decimal | 10 | 4 | Area in acres (e.g., 2.5000) |

3. Click **OK**
4. New layer appears in Layers panel
5. Layer is currently empty (no features)

#### Step 2: Enable Editing

1. Select `bellandur_parcels` layer in Layers panel
2. Click **Toggle Editing** (pencil icon) in toolbar
3. Layer becomes editable (pencil icon highlighted)

#### Step 3: Set Snapping Options

**Why Snapping?**
- Ensures adjacent parcels share common boundaries
- Prevents gaps and overlaps
- Essential for accurate topology

**Configure Snapping:**
1. Go to **Settings** → **Snapping Options**
2. Check "Enable Snapping"
3. Select `bellandur_parcels` layer
4. Snapping mode: "To vertex and segment"
5. Tolerance: 10 pixels
6. Click "OK"

#### Step 4: Load Georeferenced Map

1. Add georeferenced map to QGIS:
   - Go to **Layer** → **Add Layer** → **Add Raster Layer**
   - Select: `bellandur_sn_001_georef.tif`
   - Click "Add"
2. Map loads in canvas
3. In Layers panel, drag georeferenced map BELOW parcel layer
4. Set parcel layer opacity to 50%:
   - Right-click parcel layer → **Properties** → **Transparency**
   - Set global opacity to 50%
   - Click "OK"

#### Step 5: Digitize First Parcel

**Locate Parcel Boundary:**
1. Zoom to georeferenced map
2. Identify parcel boundary (usually outlined in red/black on tippan)
3. Note survey number from map or RTC document

**Start Digitizing:**
1. Click **Add Polygon Feature** (polygon icon) in Digitizing Toolbar
2. Cursor changes to crosshair
3. Click on first vertex of parcel boundary
4. Move to next vertex, click
5. Continue clicking along boundary
6. For curved boundaries, add more vertices for accuracy
7. To finish, right-click or click on first vertex again

**Enter Attributes:**
1. Feature form opens after closing polygon
2. Enter values:
   - survey_no: "1" (from RTC)
   - village: "Bellandur"
   - hobli: "Begur"
   - district: "Bengaluru Urban"
   - area_acres: 2.5 (from RTC, in acres)
3. Click "OK"

**Parcel Added:**
- Polygon appears on map
- Attribute table updated

#### Step 6: Digitize Adjacent Parcels

**For adjacent parcels:**
1. Click **Add Polygon Feature**
2. Start digitizing from shared boundary
3. Snapping will snap to existing parcel vertices
4. This ensures no gaps between parcels
5. Continue tracing new parcel boundary
6. Enter attributes for new parcel
7. Click "OK"

**Repeat for all parcels in the map.**

#### Step 7: Handle Complex Cases

**Split Parcels:**
- If a survey number is split into multiple polygons:
- Digitize each polygon separately
- Use same survey_no for all polygons
- Note: This requires database schema modification later

**Holes in Parcels:**
- If parcel has internal holes (e.g., water body inside):
- Digitize outer boundary first
- Then digitize inner boundary (hole)
- QGIS will create polygon with hole

**Shared Boundaries:**
- Always use snapping for shared boundaries
- Never digitize the same boundary twice
- This prevents sliver gaps

#### Step 8: Save Edits

1. Click **Save Edits** (floppy disk icon) in toolbar
2. Edits saved to shapefile
3. Can continue editing or stop editing

#### Step 9: Stop Editing

1. Click **Toggle Editing** (pencil icon) to stop
2. Layer is no longer editable
3. All changes saved

#### Step 10: Verify Topology

**Check for Gaps:**
1. Go to **Vector** → **Geometry Tools** → **Check Geometry**
2. Select `bellandur_parcels` layer
3. Click "OK"
4. Results show any geometry errors
5. Fix errors if found

**Check for Overlaps:**
1. Go to **Vector** → **Data Management Tools** → **Check Validity**
2. Select layer
3. Check for overlaps
4. Fix if found

#### Step 11: Repeat for All Maps

Repeat digitization for all georeferenced tippan maps:
- Add each georeferenced map to QGIS
- Digitize all parcels in that map
- Continue until all 50 maps digitized

**Time Estimate:** 5-10 minutes per parcel
**Total Time for 250 parcels:** 20-40 hours

---

## Part 6: Attribute Schema Details

### Complete Schema for survey_parcels Table

```sql
CREATE TABLE survey_parcels (
    id SERIAL PRIMARY KEY,
    survey_no TEXT NOT NULL,
    village VARCHAR(200) NOT NULL,
    hobli VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    area_acres FLOAT,
    geom GEOMETRY(Polygon, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_survey_parcels_village FOREIGN KEY (village) 
        REFERENCES karnataka_admin(village) ON DELETE SET NULL
);
```

### QGIS Attribute Schema

| Field Name | QGIS Type | Width | Precision | Example Value | Required? |
|------------|-----------|-------|-----------|---------------|-----------|
| survey_no | String | 20 | 0 | "1", "2/1", "45A" | Yes |
| village | String | 200 | 0 | "Bellandur" | Yes |
| hobli | String | 100 | 0 | "Begur" | Yes |
| district | String | 100 | 0 | "Bengaluru Urban" | Yes |
| area_acres | Decimal | 10 | 4 | 2.5000 | Yes |

### Data Entry Guidelines

**survey_no:**
- Use exact value from RTC document
- Include suffixes: "1", "2/1", "45A", "100B"
- Do not add prefixes (e.g., don't add "SN-")
- Text field to accommodate alphanumeric values

**village:**
- Use exact village name from karnataka_admin table
- For Bellandur pilot: "Bellandur"
- Case-sensitive: use title case

**hobli:**
- Use exact hobli name from karnataka_admin table
- For Bellandur pilot: "Begur"
- Case-sensitive: use title case

**district:**
- Use exact district name from karnataka_admin table
- For Bengaluru Urban pilot: "Bengaluru Urban"
- Case-sensitive: use title case

**area_acres:**
- Extract from RTC document
- Convert to acres if in guntas (1 acre = 40 guntas)
- Use 4 decimal places for precision
- Example: 2.5 acres = 2.5000

### Foreign Key Constraint

The `village` field has a foreign key constraint to `karnataka_admin(village)`.

**Before importing:**
1. Ensure village name exists in karnataka_admin table
2. Run: `SELECT * FROM karnataka_admin WHERE village = 'Bellandur';`
3. If not found, add it first:
   ```sql
   INSERT INTO karnataka_admin (district, taluk, hobli, village, village_code, pin_code)
   VALUES ('Bengaluru Urban', 'Bengaluru South', 'Begur', 'Bellandur', 'BLRU001', '560103');
   ```

---

## Part 7: GeoJSON Export Process

### Step-by-Step Export

#### Step 1: Verify Layer

1. In QGIS, ensure `bellandur_parcels` layer is selected
2. Open attribute table (right-click → **Open Attribute Table**)
3. Verify all parcels have attributes filled
4. Check for NULL values in required fields

#### Step 2: Export to GeoJSON

1. Right-click on `bellandur_parcels` layer
2. Select **Export** → **Save Features As**
3. Configure export dialog:

**Format:**
- Format: GeoJSON
- File name: `bellandur_parcels.geojson`
- Location: `C:\GIS_Project\Bellandur\export\`

**Extent:**
- Save extent: Layer extent

**CRS:**
- CRS: EPSG:4326 (WGS 84)
- This matches database schema requirement

**Geometry:**
- Geometry type: Polygon
- Include z-dimension: No (not needed)

**Attributes:**
- ✅ Export all attributes
- ✅ Keep field names as is

**Options:**
- Coordinate precision: 6 (recommended for ~11cm precision)
- RFC 7946: Yes (modern GeoJSON standard)

4. Click "OK"
5. GeoJSON file created

#### Step 3: Verify GeoJSON

**Open in Text Editor:**
1. Open `bellandur_parcels.geojson` in Notepad++ or VS Code
2. Verify structure:
   ```json
   {
     "type": "FeatureCollection",
     "features": [
       {
         "type": "Feature",
         "geometry": {
           "type": "Polygon",
           "coordinates": [[[77.1234, 12.5678], ...]]
         },
         "properties": {
           "survey_no": "1",
           "village": "Bellandur",
           "hobli": "Begur",
           "district": "Bengaluru Urban",
           "area_acres": 2.5
         }
       }
     ]
   }
   ```

**Validate GeoJSON:**
1. Use online validator: https://geojson.io
2. Upload GeoJSON file
3. Verify it renders correctly
4. Check for syntax errors

#### Step 4: Check File Size

- Typical size for 250 parcels: 500 KB - 2 MB
- If file is very large (>10 MB), check for:
  - Too many vertices (simplify geometry)
  - Duplicate features
  - Incorrect coordinate precision

---

## Part 8: Python Script to Import GeoJSON

### Import Script

Create file: `import_survey_parcels.py` in project root.

```python
#!/usr/bin/env python3
"""
 ============================================================================
 GeoJSON to PostgreSQL Import Script for survey_parcels
 ============================================================================
 Description: Import digitized parcel polygons from GeoJSON to PostGIS
 Usage: python import_survey_parcels.py <path_to_geojson>
 ============================================================================
"""

import asyncio
import json
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

import asyncpg
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SurveyParcelImporter:
    """Import GeoJSON survey parcels into PostgreSQL survey_parcels table."""

    def __init__(self, geojson_path: str):
        """
        Initialize importer with GeoJSON file path.
        
        Args:
            geojson_path: Path to GeoJSON file
        """
        self.geojson_path = Path(geojson_path)
        self.conn = None
        self.imported_count = 0
        self.failed_count = 0

    async def connect(self):
        """Establish database connection."""
        try:
            self.conn = await asyncpg.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD
            )
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    async def close(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()
            logger.info("Database connection closed")

    def load_geojson(self) -> Dict[str, Any]:
        """
        Load GeoJSON file.
        
        Returns:
            GeoJSON data as dictionary
        """
        if not self.geojson_path.exists():
            logger.error(f"GeoJSON file not found: {self.geojson_path}")
            raise FileNotFoundError(f"File not found: {self.geojson_path}")

        with open(self.geojson_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"Loaded GeoJSON file: {self.geojson_path}")
        logger.info(f"Total features: {len(data.get('features', []))}")
        return data

    def validate_feature(self, feature: Dict[str, Any]) -> bool:
        """
        Validate feature has required attributes.
        
        Args:
            feature: GeoJSON feature
            
        Returns:
            True if valid, False otherwise
        """
        props = feature.get('properties', {})
        required_fields = ['survey_no', 'village', 'hobli', 'district', 'area_acres']
        
        for field in required_fields:
            if field not in props or props[field] is None:
                logger.warning(f"Feature missing required field: {field}")
                return False
        
        geometry = feature.get('geometry')
        if not geometry or geometry.get('type') != 'Polygon':
            logger.warning("Feature missing or invalid Polygon geometry")
            return False
        
        return True

    def geometry_to_wkt(self, geometry: Dict[str, Any]) -> str:
        """
        Convert GeoJSON geometry to PostGIS WKT format.
        
        Args:
            geometry: GeoJSON geometry object
            
        Returns:
            WKT string
        """
        if geometry['type'] != 'Polygon':
            raise ValueError(f"Unsupported geometry type: {geometry['type']}")
        
        # GeoJSON coordinates: [longitude, latitude] (x, y)
        # WKT format: POLYGON((x1 y1, x2 y2, ...))
        coordinates = geometry['coordinates'][0]  # Exterior ring
        
        coord_pairs = []
        for coord in coordinates:
            lon, lat = coord[0], coord[1]
            coord_pairs.append(f"{lon} {lat}")
        
        wkt = f"POLYGON(({', '.join(coord_pairs)}))"
        return wkt

    async def check_village_exists(self, village: str) -> bool:
        """
        Check if village exists in karnataka_admin table.
        
        Args:
            village: Village name
            
        Returns:
            True if exists, False otherwise
        """
        query = """
            SELECT COUNT(*) 
            FROM karnataka_admin 
            WHERE village = $1
        """
        count = await self.conn.fetchval(query, village)
        return count > 0

    async def import_feature(self, feature: Dict[str, Any]) -> bool:
        """
        Import a single feature into survey_parcels table.
        
        Args:
            feature: GeoJSON feature
            
        Returns:
            True if successful, False otherwise
        """
        try:
            props = feature['properties']
            geometry = feature['geometry']
            
            # Validate village exists first
            village = props['village']
            if not await self.check_village_exists(village):
                logger.warning(f"Village '{village}' not found in karnataka_admin table")
                # Optionally, auto-create village entry here
                return False
            
            # Convert geometry to WKT
            wkt = self.geometry_to_wkt(geometry)
            
            # Insert into database
            query = """
                INSERT INTO survey_parcels 
                (survey_no, village, hobli, district, area_acres, geom)
                VALUES ($1, $2, $3, $4, $5, ST_GeomFromText($6, 4326))
                ON CONFLICT DO NOTHING
            """
            
            await self.conn.execute(
                query,
                props['survey_no'],
                props['village'],
                props['hobli'],
                props['district'],
                props['area_acres'],
                wkt
            )
            
            logger.info(f"Imported survey_no: {props['survey_no']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import feature: {e}")
            return False

    async def import_all(self):
        """Import all features from GeoJSON file."""
        try:
            # Load GeoJSON
            data = self.load_geojson()
            features = data.get('features', [])
            
            if not features:
                logger.warning("No features found in GeoJSON")
                return
            
            # Connect to database
            await self.connect()
            
            # Import each feature
            for feature in features:
                if self.validate_feature(feature):
                    success = await self.import_feature(feature)
                    if success:
                        self.imported_count += 1
                    else:
                        self.failed_count += 1
                else:
                    self.failed_count += 1
            
            logger.info(f"Import complete: {self.imported_count} succeeded, {self.failed_count} failed")
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            raise
        finally:
            await self.close()


async def main():
    """Main execution function."""
    if len(sys.argv) < 2:
        logger.error("Usage: python import_survey_parcels.py <path_to_geojson>")
        sys.exit(1)
    
    geojson_path = sys.argv[1]
    
    logger.info(f"Starting import from: {geojson_path}")
    logger.info(f"Database: {settings.DB_NAME}@{settings.DB_HOST}:{settings.DB_PORT}")
    
    importer = SurveyParcelImporter(geojson_path)
    await importer.import_all()
    
    logger.info("Import process completed")


if __name__ == '__main__':
    asyncio.run(main())
```

### Usage Instructions

**Step 1: Activate Virtual Environment**
```powershell
cd "c:\Users\Poorvi A V\OneDrive\Desktop\land record"
venv\Scripts\activate
```

**Step 2: Run Import Script**
```powershell
python import_survey_parcels.py C:\GIS_Project\Bellandur\export\bellandur_parcels.geojson
```

**Step 3: Verify Output**
```
2024-01-01 10:00:00 - INFO - Starting import from: C:\GIS_Project\Bellandur\export\bellandur_parcels.geojson
2024-01-01 10:00:00 - INFO - Database: gis_engine@localhost:5432
2024-01-01 10:00:01 - INFO - Loaded GeoJSON file: C:\GIS_Project\Bellandur\export\bellandur_parcels.geojson
2024-01-01 10:00:01 - INFO - Total features: 250
2024-01-01 10:00:02 - INFO - Database connection established
2024-01-01 10:00:02 - INFO - Imported survey_no: 1
2024-01-01 10:00:02 - INFO - Imported survey_no: 2
...
2024-01-01 10:00:30 - INFO - Import complete: 250 succeeded, 0 failed
2024-01-01 10:00:30 - INFO - Import process completed
```

### Error Handling

**If village not found in karnataka_admin:**
```sql
-- Add village first
INSERT INTO karnataka_admin (district, taluk, hobli, village, village_code, pin_code)
VALUES ('Bengaluru Urban', 'Bengaluru South', 'Begur', 'Bellandur', 'BLRU001', '560103');
```

**If geometry validation fails:**
- Check GeoJSON coordinate order (should be [lon, lat])
- Verify all polygons are closed (first point = last point)
- Fix in QGIS: Vector → Geometry Tools → Check Geometry

**If duplicate survey numbers:**
- Script uses ON CONFLICT DO NOTHING
- Duplicates are skipped
- Check for duplicates in QGIS before export

---

## Part 9: SQL Verification Queries

### Query 1: Verify Total Count

```sql
-- Check total number of parcels imported
SELECT COUNT(*) as total_parcels 
FROM survey_parcels 
WHERE village = 'Bellandur';
```

**Expected Output:** 250 (or your actual count)

---

### Query 2: Verify Geometry Validity

```sql
-- Check for invalid geometries
SELECT 
    id, 
    survey_no, 
    ST_IsValid(geom) as is_valid,
    ST_IsValidReason(geom) as validity_reason
FROM survey_parcels 
WHERE village = 'Bellandur'
AND NOT ST_IsValid(geom);
```

**Expected Output:** 0 rows (all geometries should be valid)

**If invalid geometries found:**
```sql
-- Fix invalid geometries
UPDATE survey_parcels
SET geom = ST_MakeValid(geom)
WHERE village = 'Bellandur'
AND NOT ST_IsValid(geom);
```

---

### Query 3: Verify Coordinate System

```sql
-- Check SRID of geometries
SELECT 
    DISTINCT ST_SRID(geom) as srid
FROM survey_parcels 
WHERE village = 'Bellandur';
```

**Expected Output:** 4326 (WGS 84)

**If wrong SRID:**
```sql
-- Reproject to correct SRID
UPDATE survey_parcels
SET geom = ST_SetSRID(geom, 4326)
WHERE village = 'Bellandur';
```

---

### Query 4: Verify Attribute Data

```sql
-- Check for NULL values in required fields
SELECT 
    COUNT(*) as null_count,
    'survey_no' as field_name
FROM survey_parcels 
WHERE village = 'Bellandur' AND survey_no IS NULL

UNION ALL

SELECT 
    COUNT(*),
    'village'
FROM survey_parcels 
WHERE village = 'Bellandur' AND village IS NULL

UNION ALL

SELECT 
    COUNT(*),
    'hobli'
FROM survey_parcels 
WHERE village = 'Bellandur' AND hobli IS NULL

UNION ALL

SELECT 
    COUNT(*),
    'district'
FROM survey_parcels 
WHERE village = 'Bellandur' AND district IS NULL

UNION ALL

SELECT 
    COUNT(*),
    'area_acres'
FROM survey_parcels 
WHERE village = 'Bellandur' AND area_acres IS NULL;
```

**Expected Output:** 0 for all fields

---

### Query 5: Verify Spatial Index

```sql
-- Check if GIST index exists on geom column
SELECT 
    indexname, 
    indexdef
FROM pg_indexes
WHERE tablename = 'survey_parcels'
AND indexname LIKE '%geom%';
```

**Expected Output:** 
```
indexname: idx_survey_parcels_geom
indexdef: CREATE INDEX idx_survey_parcels_geom ON public.survey_parcels USING gist (geom)
```

**If index missing:**
```sql
-- Create spatial index
CREATE INDEX idx_survey_parcels_geom 
ON survey_parcels 
USING gist (geom);
```

---

### Query 6: Verify Foreign Key Constraint

```sql
-- Check if all villages exist in karnataka_admin
SELECT 
    DISTINCT sp.village
FROM survey_parcels sp
LEFT JOIN karnataka_admin ka ON sp.village = ka.village
WHERE sp.village = 'Bellandur'
AND ka.village IS NULL;
```

**Expected Output:** 0 rows (all villages should exist)

---

### Query 7: Sample Data Inspection

```sql
-- View sample of imported data
SELECT 
    id,
    survey_no,
    village,
    hobli,
    district,
    area_acres,
    ST_AsText(geom) as geometry_wkt,
    ST_Area(geom::geography) / 4046.86 as area_calculated_acres
FROM survey_parcels 
WHERE village = 'Bellandur'
LIMIT 5;
```

**Expected Output:** 
- 5 sample rows with all attributes
- area_calculated_acres should be close to area_acres

---

### Query 8: Check for Duplicate Survey Numbers

```sql
-- Find duplicate survey numbers within village
SELECT 
    survey_no, 
    COUNT(*) as count
FROM survey_parcels 
WHERE village = 'Bellandur'
GROUP BY survey_no
HAVING COUNT(*) > 1;
```

**Expected Output:** 0 rows (no duplicates)

**If duplicates found:**
- This may be legitimate (split parcels)
- Consider adding suffix to distinguish: "1-A", "1-B"

---

### Query 9: Verify Polygon Closure

```sql
-- Check if polygons are properly closed (first point = last point)
SELECT 
    id,
    survey_no,
    ST_IsClosed(geom) as is_closed
FROM survey_parcels 
WHERE village = 'Bellandur'
AND NOT ST_IsClosed(geom);
```

**Expected Output:** 0 rows (all polygons should be closed)

---

### Query 10: Total Area Calculation

```sql
-- Calculate total area of all parcels in acres
SELECT 
    SUM(area_acres) as total_area_reported,
    SUM(ST_Area(geom::geography)) / 4046.86 as total_area_calculated,
    village
FROM survey_parcels 
WHERE village = 'Bellandur'
GROUP BY village;
```

**Expected Output:** 
- total_area_reported: Sum of area_acres from attributes
- total_area_calculated: Sum calculated from geometry
- Values should be reasonably close (within 5-10% tolerance)

---

## Part 10: Bengaluru Test Coordinates for ST_Contains Validation

### Test Coordinates for Bellandur Village

These coordinates are within or near Bellandur village boundaries. Use them to test the `GET /api/gis/survey-number` endpoint after importing real data.

**Coordinate Selection Criteria:**
- Located within Bellandur village area
- Distributed across different parts of village
- Include edge cases (near boundaries)
- Based on known landmarks in Bellandur

### Test Coordinate Set

| # | Latitude | Longitude | Description | Expected Result |
|---|----------|-----------|-------------|-----------------|
| 1 | 12.9256 | 77.6628 | Bellandur Lake (North) | Should return survey number if lake has parcels |
| 2 | 12.9185 | 77.6685 | Bellandur Lake (South) | Should return survey number if lake has parcels |
| 3 | 12.9220 | 77.6650 | Near Bellandur Gate | Should return survey number |
| 4 | 12.9280 | 77.6700 | Outer Ring Road junction | Should return survey number |
| 5 | 12.9200 | 77.6600 | Residential area (West) | Should return survey number |
| 6 | 12.9240 | 77.6750 | Residential area (East) | Should return survey number |
| 7 | 12.9260 | 77.6635 | Near Bellandur Agraahara | Should return survey number |
| 8 | 12.9210 | 77.6670 | Central Bellandur | Should return survey number |
| 9 | 12.9290 | 77.6660 | Near Bellandur railway station | Should return survey number |
| 10 | 12.9235 | 77.6625 | Bellandur village boundary | May return nearest parcel |

### Testing Procedure

**Step 1: Start FastAPI Service**
```powershell
cd "c:\Users\Poorvi A V\OneDrive\Desktop\land record"
venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Step 2: Test Each Coordinate**

**Test Coordinate 1:**
```powershell
curl "http://localhost:8000/api/gis/survey-number?lat=12.9256&lng=77.6628"
```

**Expected Response (with data):**
```json
{
  "survey_no": "45",
  "village": "Bellandur",
  "hobli": "Begur",
  "district": "Bengaluru Urban",
  "area_acres": 2.5,
  "confidence": "exact"
}
```

**Expected Response (without data - before import):**
```json
{
  "detail": "No survey parcels found in the database for this location"
}
```

**Test Coordinate 2:**
```powershell
curl "http://localhost:8000/api/gis/survey-number?lat=12.9185&lng=77.6685"
```

**Repeat for all 10 coordinates.**

### SQL Test Queries

**Direct SQL Test for ST_Contains:**

```sql
-- Test coordinate 1
SELECT 
    survey_no,
    village,
    hobli,
    district,
    area_acres,
    ST_Distance(
        geom::geography,
        ST_SetSRID(ST_Point(77.6628, 12.9256), 4326)::geography
    ) as distance_meters
FROM survey_parcels
WHERE village = 'Bellandur'
AND ST_Contains(
    geom,
    ST_SetSRID(ST_Point(77.6628, 12.9256), 4326)
)
LIMIT 1;
```

**Test all coordinates:**
```sql
-- Test all 10 coordinates
WITH test_points AS (
    SELECT 
        1 as id, 12.9256 as lat, 77.6628 as lng, 'Bellandur Lake North' as description
    UNION ALL SELECT 2, 12.9185, 77.6685, 'Bellandur Lake South'
    UNION ALL SELECT 3, 12.9220, 77.6650, 'Near Bellandur Gate'
    UNION ALL SELECT 4, 12.9280, 77.6700, 'Outer Ring Road junction'
    UNION ALL SELECT 5, 12.9200, 77.6600, 'Residential area West'
    UNION ALL SELECT 6, 12.9240, 77.6750, 'Residential area East'
    UNION ALL SELECT 7, 12.9260, 77.6635, 'Near Bellandur Agraahara'
    UNION ALL SELECT 8, 12.9210, 77.6670, 'Central Bellandur'
    UNION ALL SELECT 9, 12.9290, 77.6660, 'Near railway station'
    UNION ALL SELECT 10, 12.9235, 77.6625, 'Village boundary'
)
SELECT 
    tp.id,
    tp.description,
    tp.lat,
    tp.lng,
    sp.survey_no,
    sp.area_acres,
    'EXACT MATCH' as match_type
FROM test_points tp
JOIN survey_parcels sp ON ST_Contains(
    sp.geom,
    ST_SetSRID(ST_Point(tp.lng, tp.lat), 4326)
)
WHERE sp.village = 'Bellandur'

UNION ALL

SELECT 
    tp.id,
    tp.description,
    tp.lat,
    tp.lng,
    sp.survey_no,
    sp.area_acres,
    'NEAREST PARCEL' as match_type
FROM test_points tp
LEFT JOIN survey_parcels sp ON ST_Contains(
    sp.geom,
    ST_SetSRID(ST_Point(tp.lng, tp.lat), 4326)
)
CROSS JOIN LATERAL (
    SELECT 
        survey_no,
        area_acres,
        ST_Distance(
            geom::geography,
            ST_SetSRID(ST_Point(tp.lng, tp.lat), 4326)::geography
        ) as distance
    FROM survey_parcels
    WHERE village = 'Bellandur'
    ORDER BY distance ASC
    LIMIT 1
) sp
WHERE sp.survey_no IS NOT NULL
ORDER BY tp.id;
```

**Expected Output:** 
- Each test point should return either an exact match (point inside polygon) or nearest parcel
- Distance in meters for nearest parcel
- Survey number and area for matched parcel

---

## Part 11: Complete Workflow Summary

### End-to-End Process Timeline

| Phase | Task | Estimated Time | Dependencies |
|-------|------|---------------|--------------|
| **Phase 1** | Download tippan maps from Bhoomi (50 survey numbers) | 2-3 hours | Internet access |
| **Phase 2** | Install and configure QGIS | 30 minutes | None |
| **Phase 3** | Georeference 50 tippan maps | 8-12 hours | QGIS installed |
| **Phase 4** | Digitize 250 parcel boundaries | 20-40 hours | Georeferenced maps |
| **Phase 5** | Export to GeoJSON | 5 minutes | Digitized layer |
| **Phase 6** | Import GeoJSON to PostgreSQL | 5 minutes | GeoJSON file |
| **Phase 7** | Verify with SQL queries | 15 minutes | Import complete |
| **Phase 8** | Test with API endpoints | 15 minutes | Import complete |

**Total Estimated Time:** 31-67 hours (4-8 working days)

### Critical Success Factors

1. **Data Quality:** Clear, high-resolution tippan maps
2. **GCP Accuracy:** Well-distributed ground control points
3. **Topology:** Proper snapping to prevent gaps/overlaps
4. **Attribute Accuracy:** Correct survey numbers from RTC
5. **Coordinate System:** Consistent use of EPSG:4326

### Common Pitfalls and Solutions

| Pitfall | Solution |
|---------|----------|
| Low-resolution tippan maps | Request higher resolution from Revenue Office |
| Poor GCP selection | Use permanent landmarks (temples, road intersections) |
| Gaps between parcels | Enable snapping in QGIS |
| Wrong coordinate order | GeoJSON uses [lon, lat], not [lat, lon] |
| Village not in database | Add to karnataka_admin before import |
| Invalid geometries | Use ST_MakeValid() to fix |
| Duplicate survey numbers | Add suffixes (1-A, 1-B) for split parcels |

### Next Steps After Pilot

1. **Scale to More Villages:**
   - Apply same workflow to Kadubeesanahalli
   - Then expand to entire Begur Hobli
   - Eventually cover all Bengaluru South Taluk

2. **Automate Where Possible:**
   - Batch georeferencing for same-scale maps
   - Python scripts for bulk attribute updates
   - Automated validation checks

3. **Quality Assurance:**
   - Random sample verification (10% of parcels)
   - Cross-check with original RTC documents
   - Field verification for critical parcels

4. **Documentation:**
   - Maintain metadata for each village
   - Document GCP locations for reproducibility
   - Track data sources and dates

---

## Part 12: Quick Reference Commands

### QGIS Commands

**Open Georeferencer:**
```
Raster → Georeferencer → Georeferencer
```

**Add Background Map:**
```
Web → QuickMapServices → OSM → OSM Standard
```

**Toggle Editing:**
```
Click pencil icon in toolbar
```

**Add Polygon Feature:**
```
Click polygon icon in Digitizing Toolbar
```

**Save Edits:**
```
Click floppy disk icon in toolbar
```

**Export to GeoJSON:**
```
Right-click layer → Export → Save Features As → GeoJSON
```

### Python Commands

**Import GeoJSON:**
```powershell
python import_survey_parcels.py C:\GIS_Project\Bellandur\export\bellandur_parcels.geojson
```

### SQL Commands

**Check parcel count:**
```sql
SELECT COUNT(*) FROM survey_parcels WHERE village = 'Bellandur';
```

**Test ST_Contains:**
```sql
SELECT survey_no FROM survey_parcels
WHERE ST_Contains(geom, ST_SetSRID(ST_Point(77.6628, 12.9256), 4326))
LIMIT 1;
```

### API Commands

**Test survey number endpoint:**
```powershell
curl "http://localhost:8000/api/gis/survey-number?lat=12.9256&lng=77.6628"
```

---

## Conclusion

This guide provides a complete, step-by-step workflow for populating the `survey_parcels` table with real Bengaluru cadastral data. By following this process, you will:

1. ✅ Obtain official cadastral maps from Bhoomi
2. ✅ Georeference maps using Thin Plate Spline transformation
3. ✅ Digitize parcel boundaries with proper topology
4. ✅ Export to GeoJSON with correct attributes
5. ✅ Import to PostgreSQL using Python script
6. ✅ Verify data integrity with SQL queries
7. ✅ Test API endpoints with real coordinates

**Result:** The `GET /api/gis/survey-number` endpoint will return actual survey numbers instead of 404 errors, enabling real property verification for Bengaluru Urban district.

**Estimated Completion Time:** 4-8 working days for 2-village pilot (250 parcels)

**Scalability:** This workflow can be scaled to cover all villages in Bengaluru Urban and Rural districts, eventually achieving the target of 100,000+ parcels.
