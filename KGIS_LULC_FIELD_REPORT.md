# KGIS LULC ArcGIS REST Service Field Report

## Service Information
- **URL**: https://kgis.ksrsac.in/kgismaps1/rest/services/NR_V2/LULC_10K/MapServer/0
- **Capabilities**: Map, Query, Data
- **Geometry Type**: esriGeometryPolygon
- **Supported Query Formats**: JSON, geoJSON
- **Max Record Count**: 1000
- **Spatial Reference**: WKID 32643 (UTM Zone 43N)

## Field Definitions

### Primary Fields
| Field Name | Type | Alias | Length | Description |
|------------|------|-------|--------|-------------|
| NR.DBO.LULC.OBJECTID | esriFieldTypeOID | OBJECTID | - | Object identifier |
| NR.DBO.LULC.KGISLULCID | esriFieldTypeInteger | KGISLULCID | - | KGIS LULC ID |
| NR.DBO.LULC.LULCCode | esriFieldTypeString | LULCCode | 4 | LULC code (primary classification) |
| NR.DBO.LULC.Shape | esriFieldTypeGeometry | Shape | - | Polygon geometry |

### Related Table Fields (LULC_Tbl)
| Field Name | Type | Alias | Length | Description |
|------------|------|-------|--------|-------------|
| NR.DBO.LULC_Tbl.OBJECTID | esriFieldTypeInteger | OBJECTID | - | Object identifier |
| NR.DBO.LULC_Tbl.LULCCode | esriFieldTypeString | LULCCode | 4 | LULC code (foreign key) |
| NR.DBO.LULC_Tbl.LULC_Description | esriFieldTypeString | LULC_Description | 50 | Primary land use description |
| NR.DBO.LULC_Tbl.LULC_Description2 | esriFieldTypeString | LULC_Description2 | 50 | Secondary land use description |
| NR.DBO.LULC_Tbl.LULC_Description1 | esriFieldTypeString | LULC_Description1 | 50 | Tertiary land use description |

## LULC Code Classification

### Built-up Areas
| Code | Label | Category |
|------|-------|----------|
| BUUR | Built up (Urban) | Built-up |
| BUUC | Core urban | Built-up |
| BUUP | Peri urban | Built-up |
| BURU | Built up (Rural) | Built-up |
| BURV | Village | Built-up |
| BURM | Mixed settlement | Built-up |
| BURH | Hamlets and dispersed household | Built-up |
| BUMN | Mining / industrial | Built-up |
| BUTP | Transportation | Built-up |

### Agriculture
| Code | Label | Category |
|------|-------|----------|
| AGCR | Crop land | Agriculture |
| AGPL | Agriculture plantation | Agriculture |
| AGAQ | Aquaculture / pisciculture | Agriculture |

### Forest
| Code | Label | Category |
|------|-------|----------|
| FRDE | Forest | Forest |
| FRPL | Forest plantation | Forest |
| FRMG | Mangrove / Swamp area | Forest |

### Wasteland
| Code | Label | Category |
|------|-------|----------|
| GRGR | Grassland & Grazing land | Wasteland |
| WLST | Salt affected | Wasteland |
| WLGU | Gullied / ravenous | Wasteland |
| WLWL | Waterlogged | Wasteland |
| WLSD | Scrub land Dense | Wasteland |
| WLSP | Scrub land Open | Wasteland |
| WLSA | Sandy areas | Wasteland |
| WLBR | Barren rocky | Wasteland |

### Water Bodies
| Code | Label | Category |
|------|-------|----------|
| WBRS | River / Stream / Drain | Water |
| WBCN | Canal | Water |
| WBRE | Reservoir | Water |
| WBTA | Tank | Water |
| WBLP | Lakes / Ponds | Water |

## Key Fields for API Integration

### Required Fields
1. **LULCCode** (`NR.DBO.LULC.LULCCode`) - 4-character code for land use classification
2. **LULC_Description** (`NR.DBO.LULC_Tbl.LULC_Description`) - Human-readable description
3. **Shape** (`NR.DBO.LULC.Shape`) - Polygon geometry for point-in-polygon queries

### Category Mapping
Based on the renderer's unique value classifications, we can map LULC codes to broader categories:
- **Built-up**: BUUR, BUUC, BUUP, BURU, BURV, BURM, BURH, BUMN, BUTP
- **Agriculture**: AGCR, AGPL, AGAQ
- **Forest**: FRDE, FRPL, FRMG
- **Wasteland**: GRGR, WLST, WLGU, WLWL, WLSD, WLSP, WLSA, WLBR
- **Water**: WBRS, WBCN, WBRE, WBTA, WBLP

## Query Strategy

For point-in-polygon queries, we will use the ArcGIS REST Query operation:
```
https://kgis.ksrsac.in/kgismaps1/rest/services/NR_V2/LULC_10K/MapServer/0/query
```

Parameters:
- `where`: 1=1 (no filter)
- `geometry`: {longitude,latitude}
- `geometryType`: esriGeometryPoint
- `spatialReference`: 4326 (WGS84)
- `inSR`: 4326
- `outSR`: 4326
- `outFields`: NR.DBO.LULC.LULCCode,NR.DBO.LULC_Tbl.LULC_Description
- `returnGeometry`: false
- `f`: json

The service will return features that contain the point geometry.
