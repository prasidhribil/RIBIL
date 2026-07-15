import httpx
import asyncio

async def test():
    async with httpx.AsyncClient(
        verify=False, timeout=15.0,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://kgis.ksrsac.in/kgis/webapi.aspx",
            "Origin": "https://kgis.ksrsac.in"
        }
    ) as client:
        # Test with aoi=d only
        url1 = "https://kgis.ksrsac.in:9000/genericwebservices/ws/nearbyadminhierarchy?coordinates=12.9352,77.6789&distance=10000&type=DD&aoi=d"
        r1 = await client.get(url1)
        print(f"Test 1 (aoi=d) Status: {r1.status_code}")
        print(f"Test 1 Response: {r1.text}")
        print()
        
        # Test with aoi=d,t
        url2 = "https://kgis.ksrsac.in:9000/genericwebservices/ws/nearbyadminhierarchy?coordinates=12.9352,77.6789&distance=10000&type=DD&aoi=d,t"
        r2 = await client.get(url2)
        print(f"Test 2 (aoi=d,t) Status: {r2.status_code}")
        print(f"Test 2 Response: {r2.text}")
        print()
        
        # Test with aoi=d,h
        url3 = "https://kgis.ksrsac.in:9000/genericwebservices/ws/nearbyadminhierarchy?coordinates=12.9352,77.6789&distance=10000&type=DD&aoi=d,h"
        r3 = await client.get(url3)
        print(f"Test 3 (aoi=d,h) Status: {r3.status_code}")
        print(f"Test 3 Response: {r3.text}")
        print()
        
        # Test with aoi=d,t,h
        url4 = "https://kgis.ksrsac.in:9000/genericwebservices/ws/nearbyadminhierarchy?coordinates=12.9352,77.6789&distance=10000&type=DD&aoi=d,t,h"
        r4 = await client.get(url4)
        print(f"Test 4 (aoi=d,t,h) Status: {r4.status_code}")
        print(f"Test 4 Response: {r4.text}")

asyncio.run(test())
