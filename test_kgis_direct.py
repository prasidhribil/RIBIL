import httpx
import asyncio

async def test():
    async with httpx.AsyncClient(
        verify=False, timeout=15.0,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://kgis.ksrsac.in/kgis/webapi.aspx",
            "Origin": "https://kgis.ksrsac.in"
        }
    ) as client:
        url = "https://kgis.ksrsac.in:9000/genericwebservices/ws/nearbyadminhierarchy?coordinates=12.9352,77.6789&distance=10000&type=DD&aoi=d"
        r = await client.get(url)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")

asyncio.run(test())
