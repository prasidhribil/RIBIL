#!/usr/bin/env python3
"""
 ============================================================================
 Bengaluru Administrative Data Bulk Insertion Script
 ============================================================================
 Description: Efficiently bulk-inserts village directory data into karnataka_admin table
 Focus: Optimized for Bengaluru Urban and Rural districts
 Uses: psycopg2 with batch execution for high-performance inserts
 ============================================================================
"""

import psycopg2
from psycopg2 import sql, extras
import csv
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KarnatakaAdminSeeder:
    """
    Handles bulk insertion of Karnataka administrative data into PostgreSQL.
    Optimized for Bengaluru Urban and Rural districts with batch processing.
    """

    def __init__(self, db_config: Dict[str, str]):
        """
        Initialize database connection and configuration.
        
        Args:
            db_config: Dictionary containing database connection parameters
                      (host, port, database, user, password)
        """
        self.db_config = db_config
        self.conn = None
        self.cursor = None
        self.batch_size = 1000  # Optimal batch size for performance

    def connect(self) -> bool:
        """
        Establish database connection with error handling.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.conn = psycopg2.connect(
                host=self.db_config.get('host', 'localhost'),
                port=self.db_config.get('port', 5432),
                database=self.db_config.get('database', 'gis_engine'),
                user=self.db_config.get('user', 'postgres'),
                password=self.db_config.get('password', '')
            )
            self.cursor = self.conn.cursor()
            logger.info("Database connection established successfully")
            return True
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def disconnect(self):
        """Close database connection safely."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")

    def read_csv_data(self, csv_path: str) -> List[Dict[str, str]]:
        """
        Read village directory CSV file and return list of dictionaries.
        
        Expected CSV format:
        district,taluk,hobli,village,village_code,pin_code
        
        Args:
            csv_path: Path to the CSV file
            
        Returns:
            List of dictionaries containing village data
        """
        data = []
        
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found: {csv_path}")
            return data
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Validate CSV headers
                required_headers = ['district', 'taluk', 'hobli', 'village', 'village_code', 'pin_code']
                if not all(header in reader.fieldnames for header in required_headers):
                    logger.error(f"CSV missing required headers. Found: {reader.fieldnames}")
                    return data
                
                for row in reader:
                    # Filter for Bengaluru districts if needed
                    district = row.get('district', '').strip()
                    if district in ['Bengaluru Urban', 'Bengaluru Rural', 'Bangalore Urban', 'Bangalore Rural']:
                        data.append({
                            'district': district,
                            'taluk': row.get('taluk', '').strip(),
                            'hobli': row.get('hobli', '').strip(),
                            'village': row.get('village', '').strip(),
                            'village_code': row.get('village_code', '').strip() or None,
                            'pin_code': row.get('pin_code', '').strip() or None
                        })
            
            logger.info(f"Read {len(data)} records from CSV (Bengaluru districts only)")
            return data
            
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return data

    def bulk_insert(self, data: List[Dict[str, str]]) -> int:
        """
        Perform bulk insert using execute_batch for optimal performance.
        
        Args:
            data: List of dictionaries containing village data
            
        Returns:
            Number of records inserted
        """
        if not data:
            logger.warning("No data to insert")
            return 0
        
        inserted_count = 0
        total_batches = (len(data) + self.batch_size - 1) // self.batch_size
        
        try:
            # Prepare insert query with ON CONFLICT for upsert capability
            insert_query = sql.SQL("""
                INSERT INTO karnataka_admin (district, taluk, hobli, village, village_code, pin_code)
                VALUES (%(district)s, %(taluk)s, %(hobli)s, %(village)s, %(village_code)s, %(pin_code)s)
                ON CONFLICT (village_code) 
                DO UPDATE SET
                    district = EXCLUDED.district,
                    taluk = EXCLUDED.taluk,
                    hobli = EXCLUDED.hobli,
                    village = EXCLUDED.village,
                    pin_code = EXCLUDED.pin_code,
                    updated_at = CURRENT_TIMESTAMP
            """)
            
            # Process data in batches
            for i in range(0, len(data), self.batch_size):
                batch = data[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                
                try:
                    extras.execute_batch(self.cursor, insert_query, batch)
                    self.conn.commit()
                    inserted_count += len(batch)
                    logger.info(f"Batch {batch_num}/{total_batches} inserted: {len(batch)} records")
                    
                except psycopg2.Error as e:
                    self.conn.rollback()
                    logger.error(f"Error in batch {batch_num}: {e}")
                    continue
            
            logger.info(f"Total records inserted: {inserted_count}/{len(data)}")
            return inserted_count
            
        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Bulk insert failed: {e}")
            return inserted_count

    def generate_mock_data(self, count: int = 30000) -> List[Dict[str, str]]:
        """
        Generate mock village data for testing purposes.
        Focuses on Bengaluru Urban and Rural districts with realistic data.
        
        Args:
            count: Number of mock records to generate
            
        Returns:
            List of dictionaries containing mock village data
        """
        import random
        
        # Bengaluru districts and taluks
        districts = ['Bengaluru Urban', 'Bengaluru Rural']
        
        bengaluru_urban_taluks = [
            'Bengaluru North', 'Bengaluru South', 'Bengaluru East',
            'Yelahanka', 'Kengeri', 'Anekal', 'Dasarahalli', 'Rajarajeshwari Nagar'
        ]
        
        bengaluru_rural_taluks = [
            'Nelamangala', 'Doddaballapur', 'Hoskote', 'Devanahalli',
            'Hunsur', 'Magadi', 'Kanakapura', 'Ramanagara'
        ]
        
        # Sample village and hobli names
        village_prefixes = [
            'Agara', 'Bellandur', 'Domlur', 'Indiranagar', 'Koramangala',
            'HSR Layout', 'Whitefield', 'Electronic City', 'BTM Layout',
            'Jayanagar', 'Malleshwaram', 'Rajajinagar', 'Vijayanagar',
            'Basavanagudi', 'Frazer Town', 'Richmond Road', 'Residency Road'
        ]
        
        village_suffixes = ['Village', 'Palya', 'Halli', 'Nagar', 'Layout', 'Colony']
        
        hoblis = [
            'Begur', 'Varthur', 'Kudlu', 'Madiwala', 'Bommanahalli',
            'Hennur', 'Lingrajpur', 'Kothanur', 'Doddajala', 'Sarjapur'
        ]
        
        data = []
        
        for i in range(count):
            district = random.choice(districts)
            
            if district == 'Bengaluru Urban':
                taluk = random.choice(bengaluru_urban_taluks)
            else:
                taluk = random.choice(bengaluru_rural_taluks)
            
            hobli = random.choice(hoblis)
            village = f"{random.choice(village_prefixes)} {random.choice(village_suffixes)} {i+1}"
            village_code = f"BLR{district[0]}{i+1:06d}"
            pin_code = f"560{random.randint(10, 99):02d}"
            
            data.append({
                'district': district,
                'taluk': taluk,
                'hobli': hobli,
                'village': village,
                'village_code': village_code,
                'pin_code': pin_code
            })
        
        logger.info(f"Generated {count} mock records for Bengaluru districts")
        return data

    def create_sample_csv(self, output_path: str, count: int = 30000):
        """
        Create a sample CSV file with mock data for testing.
        
        Args:
            output_path: Path where CSV file will be created
            count: Number of records to generate
        """
        data = self.generate_mock_data(count)
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['district', 'taluk', 'hobli', 'village', 'village_code', 'pin_code']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"Sample CSV created at: {output_path}")
            
        except Exception as e:
            logger.error(f"Error creating sample CSV: {e}")


def main():
    """
    Main execution function for seeding Karnataka administrative data.
    """
    # Database configuration - load from environment or use defaults
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'gis_engine'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '')
    }
    
    # CSV file path
    csv_path = os.path.join(os.path.dirname(__file__), 'karnataka_villages.csv')
    
    # Initialize seeder
    seeder = KarnatakaAdminSeeder(db_config)
    
    # Connect to database
    if not seeder.connect():
        sys.exit(1)
    
    try:
        # Check if CSV exists, if not create sample data
        if not os.path.exists(csv_path):
            logger.info("CSV file not found, generating sample data...")
            seeder.create_sample_csv(csv_path, count=30000)
        
        # Read data from CSV
        data = seeder.read_csv_data(csv_path)
        
        if not data:
            logger.warning("No data to insert. Using mock data instead.")
            data = seeder.generate_mock_data(30000)
        
        # Perform bulk insert
        start_time = datetime.now()
        inserted = seeder.bulk_insert(data)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Seeding completed in {duration:.2f} seconds")
        logger.info(f"Records inserted: {inserted}")
        
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        sys.exit(1)
    
    finally:
        seeder.disconnect()


if __name__ == '__main__':
    main()
