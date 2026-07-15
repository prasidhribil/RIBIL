"""
 ============================================================================
 Water Bodies Import Script
 ============================================================================
 Description: Imports Bengaluru lakes GeoJSON into PostgreSQL/PostGIS
              Uses asyncpg for async database operations
              Maps GeoJSON fields to water_bodies table schema
 ============================================================================
"""

import asyncio
import json
import asyncpg
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WaterBodiesImporter:
    """Imports water bodies from GeoJSON to PostgreSQL."""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.pool: Optional[asyncpg.Pool] = None
        self.stats = {
            'total_features': 0,
            'successful_imports': 0,
            'failed_imports': 0,
            'null_names': 0,
            'null_geometries': 0
        }
    
    async def connect(self):
        """Create database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise
    
    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def clear_existing_data(self):
        """Clear existing water_bodies data before import."""
        async with self.pool.acquire() as conn:
            result = await conn.execute("DELETE FROM water_bodies")
            logger.info(f"Cleared existing water_bodies data: {result}")
    
    def map_properties(self, feature: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map GeoJSON properties to water_bodies table columns.
        
        Mapping:
        - Name -> lake_name
        - LULC_Desc_1 -> category
        - LULC_Desc_2 -> lake_type
        - OBJECTID -> objectid
        - SHAPE.STArea() -> area_hectares (converted from sqm to hectares)
        - geometry -> geom
        """
        props = feature.get('properties', {})
        
        lake_name = props.get('Name')
        if lake_name is None:
            self.stats['null_names'] += 1
        
        # Convert area from square meters to hectares
        area_sqm = props.get('SHAPE.STArea()')
        area_hectares = None
        if area_sqm is not None:
            area_hectares = area_sqm / 10000.0
        
        return {
            'lake_name': lake_name,
            'category': props.get('LULC_Desc_1'),
            'lake_type': props.get('LULC_Desc_2'),
            'area_hectares': area_hectares,
            'objectid': props.get('OBJECTID')
        }
    
    def geometry_to_wkt(self, geometry: Dict[str, Any]) -> Optional[str]:
        """
        Convert GeoJSON geometry to PostGIS WKT format.
        Handles MultiPolygon geometry type.
        """
        if not geometry:
            return None
        
        geom_type = geometry.get('type')
        coordinates = geometry.get('coordinates')
        
        if geom_type == 'MultiPolygon' and coordinates:
            # Build WKT for MultiPolygon
            polygons = []
            for polygon in coordinates:
                rings = []
                for ring in polygon:
                    # Convert [lon, lat] pairs to (lon lat) format
                    ring_coords = ', '.join([f"{coord[0]} {coord[1]}" for coord in ring])
                    rings.append(f"({ring_coords})")
                polygons.append(f"({', '.join(rings)})")
            
            wkt = f"MULTIPOLYGON ({', '.join(polygons)})"
            return wkt
        
        logger.warning(f"Unsupported geometry type: {geom_type}")
        return None
    
    async def import_feature(self, feature: Dict[str, Any]) -> bool:
        """
        Import a single GeoJSON feature into water_bodies table.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Map properties
            mapped = self.map_properties(feature)
            
            # Convert geometry to WKT
            geometry = feature.get('geometry')
            if not geometry:
                self.stats['null_geometries'] += 1
                return False
            
            wkt = self.geometry_to_wkt(geometry)
            if not wkt:
                self.stats['null_geometries'] += 1
                return False
            
            # Insert into database
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO water_bodies 
                    (lake_name, category, lake_type, area_hectares, geom, objectid)
                    VALUES ($1, $2, $3, $4, ST_SetSRID(ST_GeomFromText($5), 4326), $6)
                    """,
                    mapped['lake_name'],
                    mapped['category'],
                    mapped['lake_type'],
                    mapped['area_hectares'],
                    wkt,
                    mapped['objectid']
                )
            
            self.stats['successful_imports'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to import feature: {e}")
            self.stats['failed_imports'] += 1
            return False
    
    async def import_geojson(self, geojson_path: Path, clear_existing: bool = True):
        """
        Import all features from GeoJSON file.
        
        Args:
            geojson_path: Path to GeoJSON file
            clear_existing: Whether to clear existing data before import
        """
        logger.info(f"Loading GeoJSON from: {geojson_path}")
        
        # Load GeoJSON
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        features = geojson_data.get('features', [])
        self.stats['total_features'] = len(features)
        
        logger.info(f"Total features to import: {self.stats['total_features']}")
        
        # Clear existing data if requested
        if clear_existing:
            await self.clear_existing_data()
        
        # Import features in batches
        batch_size = 100
        for i in range(0, len(features), batch_size):
            batch = features[i:i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1}/{(len(features) + batch_size - 1) // batch_size}")
            
            tasks = [self.import_feature(feature) for feature in batch]
            await asyncio.gather(*tasks)
            
            logger.info(f"Progress: {min(i + batch_size, len(features))}/{len(features)} features processed")
        
        # Log statistics
        logger.info("=" * 60)
        logger.info("Import Statistics:")
        logger.info(f"  Total features: {self.stats['total_features']}")
        logger.info(f"  Successful imports: {self.stats['successful_imports']}")
        logger.info(f"  Failed imports: {self.stats['failed_imports']}")
        logger.info(f"  Null lake names: {self.stats['null_names']}")
        logger.info(f"  Null geometries: {self.stats['null_geometries']}")
        logger.info("=" * 60)


async def main():
    """Main entry point."""
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'gis_engine',
        'user': 'postgres',
        'password': ''  # Load from environment if needed
    }
    
    # Override with environment variables if present
    import os
    db_config['host'] = os.getenv('DB_HOST', db_config['host'])
    db_config['port'] = int(os.getenv('DB_PORT', db_config['port']))
    db_config['database'] = os.getenv('DB_NAME', db_config['database'])
    db_config['user'] = os.getenv('DB_USER', db_config['user'])
    db_config['password'] = os.getenv('DB_PASSWORD', db_config['password'])
    
    # GeoJSON file path
    geojson_path = Path(__file__).parent / 'water_bodies.geojson'
    
    if not geojson_path.exists():
        logger.error(f"GeoJSON file not found: {geojson_path}")
        sys.exit(1)
    
    # Create importer
    importer = WaterBodiesImporter(db_config)
    
    try:
        # Connect to database
        await importer.connect()
        
        # Import GeoJSON
        await importer.import_geojson(geojson_path, clear_existing=True)
        
        logger.info("Import completed successfully")
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)
    finally:
        # Close connections
        await importer.close()


if __name__ == "__main__":
    asyncio.run(main())
