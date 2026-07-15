import httpx, asyncio
async def test():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://kgis.ksrsac.in/"
    }
    async with httpx.AsyncClient(verify=False, timeout=15.0,
                                  headers=headers) as client:
        # Find the IDD AviationProjects service (layers 456, 457)
        # First list all services to find the right folder
        urls = [
            "https://kgis.ksrsac.in/kgismaps1/rest/services/IDD?f=json",
            "https://kgis.ksrsac.in/kgismaps1/rest/services/IDD/AviationProjects?f=json",
            "https://kgis.ksrsac.in/kgismaps1/rest/services?f=json",
        ]
        for url in urls:
            try:
                r = await client.get(url)
                print(f"URL: {url}")
                print(f"Status: {r.status_code}")
                print(f"Response: {r.text[:800]}")
                print("---")
            except Exception as e:
                print(f"URL: {url}")
                print(f"Error: {type(e).__name__}: {e}")
                print("---")
asyncio.run(test())
