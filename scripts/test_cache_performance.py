import httpx, asyncio, time

async def test():
    coords = [
        (12.9352, 77.6789),
        (12.9698, 77.7500),
        (12.8452, 77.6602),
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for lat, lng in coords:
            print(f"\n=== Coordinate: {lat}, {lng} ===")
            
            # Test resolve endpoint
            start = time.time()
            r1 = await client.post(
                "http://localhost:8000/api/location/resolve",
                json={"lat": lat, "lng": lng}
            )
            t1 = (time.time() - start) * 1000
            
            # Second call (should be cache hit)
            start = time.time()
            r2 = await client.post(
                "http://localhost:8000/api/location/resolve",
                json={"lat": lat, "lng": lng}
            )
            t2 = (time.time() - start) * 1000
            
            print(f"resolve: 1st call={t1:.0f}ms, 2nd call={t2:.0f}ms, "
                  f"speedup={t1/t2:.1f}x")
            
            # Test zone-check
            start = time.time()
            r3 = await client.get(
                f"http://localhost:8000/api/gis/zone-check?lat={lat}&lng={lng}"
            )
            t3 = (time.time() - start) * 1000
            
            start = time.time()
            r4 = await client.get(
                f"http://localhost:8000/api/gis/zone-check?lat={lat}&lng={lng}"
            )
            t4 = (time.time() - start) * 1000
            
            print(f"zone-check: 1st call={t3:.0f}ms, 2nd call={t4:.0f}ms, "
                  f"speedup={t3/t4:.1f}x")

asyncio.run(test())
