import httpx, asyncio
async def test():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://kgis.ksrsac.in/kgis/webapi.aspx"
    }
    async with httpx.AsyncClient(verify=False, timeout=15.0, 
                                  headers=headers) as client:
        # Try common URL patterns for zonation endpoint
        urls = [
            "https://kgis.ksrsac.in:9000/genericwebservices/ws/fetchingzonationdata?coordinates=12.9352,77.6789&type=DD",
            "https://kgis.ksrsac.in:9000/genericwebservices/ws/zonation?coordinates=12.9352,77.6789&type=DD",
            "https://kgis.ksrsac.in:9000/genericwebservices/ws/fetchzonation?coordinates=12.9352,77.6789&type=DD",
        ]
        for url in urls:
            try:
                r = await client.get(url)
                print(f"URL: {url[:80]}")
                print(f"Status: {r.status_code}")
                print(f"Response: {r.text[:500]}")
                print("---")
            except Exception as e:
                print(f"URL: {url[:80]}")
                print(f"Error: {type(e).__name__}: {e}")
                print("---")
asyncio.run(test())
