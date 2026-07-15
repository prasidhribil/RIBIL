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
    count = await conn.fetchval('SELECT COUNT(*) FROM water_bodies')
    print(f'Total records: {count}')
    await conn.close()

asyncio.run(verify())
