import asyncpg
import asyncio

async def test():
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5433,
            database='gis_engine',
            user='postgres',
            password=''
        )
        print('Connected successfully with empty password (trust auth) on port 5433')
        await conn.close()
    except Exception as e:
        print(f'Connection failed with empty password: {e}')

asyncio.run(test())
