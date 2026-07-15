#!/usr/bin/env python3
import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

async def verify():
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST','localhost'),
        port=int(os.getenv('DB_PORT',5432)),
        database=os.getenv('DB_NAME','gis_engine'),
        user=os.getenv('DB_USER','postgres'),
        password=os.getenv('DB_PASSWORD','')
    )
    
    columns = await conn.fetch("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name='water_bodies'
        ORDER BY ordinal_position
    """)
    
    print("Current water_bodies schema:")
    for col in columns:
        print(f"  {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
    
    await conn.close()

asyncio.run(verify())
