#!/usr/bin/env python3
"""
Run migration 003 to fix water_bodies schema
"""
import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

async def run_migration():
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'gis_engine'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '')
    }
    
    # Read migration SQL
    migration_path = Path(__file__).parent / '003_fix_water_bodies_schema.sql'
    with open(migration_path, 'r') as f:
        sql = f.read()
    
    conn = await asyncpg.connect(**db_config)
    try:
        await conn.execute(sql)
        print("Migration 003 completed successfully")
        
        # Verify schema
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'water_bodies'
            ORDER BY ordinal_position
        """)
        
        print("\nCurrent schema:")
        for col in columns:
            print(f"  {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(run_migration())
