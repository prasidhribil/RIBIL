import httpx, asyncio, time

async def test():
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(3):
            start = time.time()
            r = await client.post(
                "http://localhost:8000/api/location/resolve",
                json={"lat": 12.9352, "lng": 77.6789}
            )
            elapsed = (time.time() - start) * 1000
            print(f"Call {i+1}: {elapsed:.0f}ms - status={r.status_code}")
            await asyncio.sleep(0.5)

asyncio.run(test())
