import httpx, asyncio
async def test():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://kgis.ksrsac.in/"
    }
    async with httpx.AsyncClient(
        verify=False, timeout=15.0, headers=headers
    ) as client:
        # Try to get village codes for Bengaluru Urban district (code 20)
        master_urls = [
            "https://kgis.ksrsac.in:9000/genericwebservices/ws/kgisvillage?districtCode=20",
            "https://kgis.ksrsac.in:9000/genericwebservices/ws/village?districtCode=20",
            "https://kgis.ksrsac.in:9000/genericwebservices/ws/kgisvillage?districtCode=20&talukCode=01",
            "https://kgis.ksrsac.in:9000/genericwebservices/ws/kgisvillagecode?districtCode=20",
        ]
        for url in master_urls:
            try:
                r = await client.get(url)
                print(f"Status {r.status_code}: {url[-60:]}")
                if r.status_code == 200:
                    print(f"  Response: {r.text[:300]}")
            except Exception as e:
                print(f"Error: {url[-60:]}: {e}")

asyncio.run(test())
