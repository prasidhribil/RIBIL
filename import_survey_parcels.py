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
