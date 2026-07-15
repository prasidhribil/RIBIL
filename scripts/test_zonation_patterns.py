import httpx, asyncio
async def test():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://kgis.ksrsac.in/kgis/webapi.aspx"
    }
    base = "https://kgis.ksrsac.in:9000/genericwebservices/ws/"
    test_cases = [
        "fetchingzonationdata?lat=12.9352&lng=77.6789",
        "fetchingzonationdata?latitude=12.9352&longitude=77.6789",
        "fetchingzonationdata?coordinates=12.9352,77.6789&type=DD&KGISVillageCode=290701",
        "fetchingzonationdata?coordinates=77.6789,12.9352&type=DD",
        "zonationdata?coordinates=12.9352,77.6789&type=DD",
        "getzonation?coordinates=12.9352,77.6789&type=DD",
        "landzonation?coordinates=12.9352,77.6789&type=DD",
    ]
    async with httpx.AsyncClient(verify=False, timeout=10.0,
                                  headers=headers) as client:
        for path in test_cases:
            url = base + path
            try:
                r = await client.get(url)
                print(f"Status {r.status_code}: {path[:60]}")
                if r.status_code == 200:
                    print(f"  RESPONSE: {r.text[:300]}")
            except Exception as e:
                print(f"Error: {path[:60]}: {type(e).__name__}")
asyncio.run(test())
