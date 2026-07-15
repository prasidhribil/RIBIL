import asyncio
import asyncpg

async def check_water_bodies():
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        database="gis_engine",
        user="postgres",
        password="postgres"
    )
    
    try:
        # Query 1: COUNT
        print("=== QUERY 1: COUNT of water_bodies ===")
        count = await conn.fetchval("SELECT COUNT(*) FROM water_bodies")
        print(f"COUNT: {count}")
        
        # Query 2: Sample data with centroids
        print("\n=== QUERY 2: Sample data with centroids ===")
        rows = await conn.fetch("""
            SELECT lake_name, lake_type, 
                   ST_AsText(ST_Centroid(geom)) as center
            FROM water_bodies 
            LIMIT 10
        """)
        for row in rows:
            print(f"  {row['lake_name']} ({row['lake_type']}): {row['center']}")
        
        # Query 3: Distance to nearest lake from test coordinate
        print("\n=== QUERY 3: Distance to nearest lake from (12.9352, 77.6789) ===")
        rows = await conn.fetch("""
            SELECT lake_name,
                   ST_Distance(
                       geom::geography,
                       ST_SetSRID(ST_Point(77.6789, 12.9352), 4326)::geography
                   ) as distance_meters
            FROM water_bodies
            ORDER BY distance_meters ASC
            LIMIT 5
        """)
        for row in rows:
            print(f"  {row['lake_name']}: {row['distance_meters']:.2f} meters")
        
    finally:
        await conn.close()

asyncio.run(check_water_bodies())
