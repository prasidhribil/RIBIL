#!/usr/bin/env python3
"""
 ============================================================================
 Bengaluru Water Bodies Import Script
 ============================================================================
 Description: Imports water_bodies GeoJSON data into PostgreSQL with PostGIS
              Uses asyncpg for async database operations
              Handles missing lake names and maps fields correctly
 ============================================================================
"""

import asyncio
import asyncpg
import json
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
print("RUNNING IMPORT SCRIPT")
from pathlib import Path

env_path = Path(__file__).resolve().parents[2] / ".env"
print("Loading ENV from:", env_path)

load_dotenv(env_path)

print("DB_HOST =", os.getenv("DB_HOST"))
print("DB_NAME =", os.getenv("DB_NAME"))
print("DB_USER =", os.getenv("DB_USER"))
print("DB_PASSWORD length =", len(os.getenv("DB_PASSWORD", "")))
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WaterBodiesImporter:
    """
    Handles import of Bengaluru water bodies from GeoJSON to PostgreSQL.
    Uses asyncpg for async database operations with PostGIS.
    """

    def __init__(self, db_config: Dict[str, Any]):
        """
        Initialize database connection configuration.
        
        Args:
            db_config: Dictionary containing database connection parameters
        """
        self.db_config = db_config
        self.pool: Optional[asyncpg.Pool] = None
        self.geojson_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'water_bodies.geojson'
        )

    async def create_pool(self) -> asyncpg.Pool:
        """
        Create asyncpg connection pool.
        
        Returns:
            asyncpg.Pool: Connection pool instance
        """
        self.pool = await asyncpg.create_pool(
            host=self.db_config.get('host', 'localhost'),
            port=self.db_config.get('port', 5432),
            database=self.db_config.get('database', 'gis_engine'),
            user=self.db_config.get('user', 'postgres'),
            password=self.db_config.get('password', ''),
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        logger.info("Database connection pool created")
        return self.pool

    async def close_pool(self):
        """Close the connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    def load_geojson(self) -> Optional[Dict[str, Any]]:
        """
        Load GeoJSON file from disk.
        
        Returns:
            GeoJSON data as dictionary, or None if failed
        """
        if not os.path.exists(self.geojson_path):
            logger.error(f"GeoJSON file not found: {self.geojson_path}")
            return None
        
        try:
            with open(self.geojson_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded GeoJSON with {len(data.get('features', []))} features")
            return data
        except Exception as e:
            logger.error(f"Failed to load GeoJSON: {e}")
            return None

    def process_feature(self, feature: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single GeoJSON feature and map fields to database schema.
        
        Mapping:
        - Name -> lake_name
        - LULC_Desc_1 -> category
        - LULC_Desc_2 -> lake_type
        - geometry -> geom (as GeoJSON for PostGIS ST_GeomFromGeoJSON)
        
        Args:
            feature: GeoJSON feature dictionary
            
        Returns:
        
            Dictionary with mapped fields ready for database insertion
        """
        props = feature.get('properties', {})
        geometry = feature.get('geometry', {})
        
        # Extract and map fields
        lake_name = props.get('Name')
        # Handle null, empty string, or whitespace-only names
        if not lake_name or not lake_name.strip():
            lake_name = None
        else:
            lake_name = lake_name.strip()
        
        category = props.get('LULC_Desc_1')
        if category:
            category = category.strip()
        
        lake_type = props.get('LULC_Desc_2')
        if lake_type:
            lake_type = lake_type.strip()
        
        # Calculate area from SHAPE.STArea() if available (convert to hectares)
        area_sqm = props.get('SHAPE.STArea()')
        area_hectares = None
        if area_sqm:
            try:
                # Convert square meters to hectares (1 hectare = 10,000 sq m)
                area_hectares = float(area_sqm) / 10000.0
            except (ValueError, TypeError):
                pass
        
        objectid = props.get('OBJECTID')
        
        # Prepare geometry as GeoJSON string for PostGIS
        geom_geojson = json.dumps(geometry)
        
        return {
            'lake_name': lake_name,
            'category': category,
            'lake_type': lake_type,
            'area_hectares': area_hectares,
            'geom': geom_geojson,
            'objectid': objectid
        }

    async def import_water_bodies(self, batch_size: int = 100) -> Dict[str, Any]:
        """
        Import water bodies from GeoJSON to database.
        
        Args:
            batch_size: Number of records to insert per batch
            
        Returns:
            Dictionary with import statistics
        """
        # Load GeoJSON
        geojson_data = self.load_geojson()
        if not geojson_data:
            return {'success': False, 'error': 'Failed to load GeoJSON'}
        
        features = geojson_data.get('features', [])
        total_features = len(features)
        
        if total_features == 0:
            return {'success': False, 'error': 'No features found in GeoJSON'}
        
        logger.info(f"Starting import of {total_features} water bodies")
        
        # Create connection pool
        await self.create_pool()
        
        stats = {
            'success': True,
            'total_features': total_features,
            'imported': 0,
            'failed': 0,
            'with_names': 0,
            'without_names': 0,
            'errors': []
        }
        
        try:
            async with self.pool.acquire() as conn:
                # Clear existing data
                await conn.execute("TRUNCATE TABLE water_bodies RESTART IDENTITY CASCADE")
                logger.info("Cleared existing water_bodies table")
                
                # Process and insert in batches
                for i in range(0, total_features, batch_size):
                    batch = features[i:i + batch_size]
                    batch_num = (i // batch_size) + 1
                    total_batches = (total_features + batch_size - 1) // batch_size
                    
                    logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} features)")
                    
                    for feature in batch:
                        try:
                            processed = self.process_feature(feature)
                            
                            # Insert using ST_GeomFromGeoJSON with SRID 4326
                            await conn.execute("""
                                INSERT INTO water_bodies 
                                (lake_name, category, lake_type, area_hectares, geom, objectid)
                                VALUES ($1, $2, $3, $4, ST_SetSRID(ST_GeomFromGeoJSON($5), 4326), $6)
                            """, 
                                processed['lake_name'],
                                processed['category'],
                                processed['lake_type'],
                                processed['area_hectares'],
                                processed['geom'],
                                processed['objectid']
                            )
                            
                            stats['imported'] += 1
                            
                            if processed['lake_name']:
                                stats['with_names'] += 1
                            else:
                                stats['without_names'] += 1
                                
                        except Exception as e:
                            stats['failed'] += 1
                            error_msg = f"Feature {i + stats['imported'] + stats['failed']}: {str(e)}"
                            stats['errors'].append(error_msg)
                            logger.error(error_msg)
                    
                    logger.info(f"Batch {batch_num} completed: {stats['imported']} imported, {stats['failed']} failed")
                
                # Create spatial indexes if they don't exist
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_water_bodies_geom ON water_bodies USING gist (geom);
                    CREATE INDEX IF NOT EXISTS idx_water_bodies_lake_name ON water_bodies USING btree (lake_name);
                    CREATE INDEX IF NOT EXISTS idx_water_bodies_category ON water_bodies USING btree (category);
                    CREATE INDEX IF NOT EXISTS idx_water_bodies_lake_type ON water_bodies USING btree (lake_type);
                """)
                logger.info("Spatial indexes created/verified")
                
                # Analyze table for query optimization
                await conn.execute("ANALYZE water_bodies")
                logger.info("Table analyzed for query optimization")
                
        except Exception as e:
            stats['success'] = False
            stats['error'] = str(e)
            logger.error(f"Import failed: {e}")
        
        finally:
            await self.close_pool()
        
        return stats

    async def validate_import(self) -> Dict[str, Any]:
        """
        Validate the imported data.
        
        Returns:
            Dictionary with validation results
        """
        await self.create_pool()
        
        validation = {
            'total_records': 0,
            'null_lake_names': 0,
            'invalid_geometries': 0,
            'wrong_srid': 0,
            'sample_lakes': []
        }
        
        try:
            async with self.pool.acquire() as conn:
                # Total record count
                validation['total_records'] = await conn.fetchval(
                    "SELECT COUNT(*) FROM water_bodies"
                )
                
                # Null lake names
                validation['null_lake_names'] = await conn.fetchval(
                    "SELECT COUNT(*) FROM water_bodies WHERE lake_name IS NULL"
                )
                
                # Invalid geometries (NULL or invalid)
                invalid_geom = await conn.fetchval("""
                    SELECT COUNT(*) FROM water_bodies 
                    WHERE geom IS NULL OR NOT ST_IsValid(geom)
                """)
                validation['invalid_geometries'] = invalid_geom
                
                # Wrong SRID (should be 4326)
                validation['wrong_srid'] = await conn.fetchval("""
                    SELECT COUNT(*) FROM water_bodies 
                    WHERE ST_SRID(geom) != 4326
                """)
                
                # Sample lakes with names
                sample_rows = await conn.fetch("""
                    SELECT lake_name, category, lake_type, area_hectares
                    FROM water_bodies
                    WHERE lake_name IS NOT NULL
                    LIMIT 5
                """)
                
                validation['sample_lakes'] = [
                    {
                        'lake_name': row['lake_name'],
                        'category': row['category'],
                        'lake_type': row['lake_type'],
                        'area_hectares': row['area_hectares']
                    }
                    for row in sample_rows
                ]
                
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            validation['error'] = str(e)
        
        finally:
            await self.close_pool()
        
        return validation


async def main():
    """
    Main execution function for water bodies import.
    """
    # Database configuration from environment variables
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'gis_engine'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'POOrvi@125')
    }
    
    logger.info("Starting water bodies import process")
    logger.info(f"Database: {db_config['database']}@{db_config['host']}:{db_config['port']}")
    
    # Initialize importer
    importer = WaterBodiesImporter(db_config)
    
    # Run import
    start_time = datetime.now()
    import_stats = await importer.import_water_bodies(batch_size=100)
    end_time = datetime.now()
    
    duration = (end_time - start_time).total_seconds()
    
    # Print results
    print("\n" + "="*70)
    print("WATER BODIES IMPORT RESULTS")
    print("="*70)
    print(f"Duration: {duration:.2f} seconds")
    print(f"Total features: {import_stats['total_features']}")
    print(f"Successfully imported: {import_stats['imported']}")
    print(f"Failed: {import_stats['failed']}")
    print(f"With lake names: {import_stats['with_names']}")
    print(f"Without lake names: {import_stats['without_names']}")
    
    if import_stats.get('errors'):
        print(f"\nErrors ({len(import_stats['errors'])}):")
        for error in import_stats['errors'][:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(import_stats['errors']) > 10:
            print(f"  ... and {len(import_stats['errors']) - 10} more errors")
    
    print("="*70)
    
    # Run validation if import was successful
    if import_stats['success']:
        logger.info("Running validation...")
        validation = await importer.validate_import()
        
        print("\n" + "="*70)
        print("VALIDATION RESULTS")
        print("="*70)
        print(f"Total records in database: {validation['total_records']}")
        print(f"Null lake names: {validation['null_lake_names']}")
        print(f"Invalid geometries: {validation['invalid_geometries']}")
        print(f"Wrong SRID (not 4326): {validation['wrong_srid']}")
        
        if validation['sample_lakes']:
            print("\nSample lakes:")
            for lake in validation['sample_lakes']:
                print(f"  - {lake['lake_name']} ({lake['lake_type']}, {lake['area_hectares']:.2f} ha)")
        
        print("="*70)
    
    # Exit with appropriate code
    if not import_stats['success']:
        logger.error("Import failed")
        exit(1)
    else:
        logger.info("Import completed successfully")
        exit(0)


if __name__ == '__main__':
    asyncio.run(main())
