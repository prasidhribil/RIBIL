import httpx, asyncio
async def test():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://kgis.ksrsac.in/kgis/webapi.aspx",
        "Accept": "application/json, text/plain, */*"
    }
    async with httpx.AsyncClient(
        verify=False, timeout=15.0, headers=headers
    ) as client:
        
        # The KGIS survey number API needs a village code
        # districtCode 20 = Bengaluru Urban (confirmed working)
        # We need to find the correct village code format
        
        test_urls = [
            # Try without village code first
            "https://kgis.ksrsac.in:9000/genericwebservices/ws/surveyno?coordinates=12.9352,77.6789&type=DD&distance=5000",
            
            # Try with KGISVillageCode from known Bengaluru villages
            "https://kgis.ksrsac.in:9000/genericwebservices/ws/surveyno?coordinates=12.9352,77.6789&type=DD&distance=5000&KGISVillageCode=201020003",
            
            # Try nearbyadminhierarchy with aoi=v to get village codes
            "https://kgis.ksrsac.in:9000/genericwebservices/ws/nearbyadminhierarchy?coordinates=12.9352,77.6789&distance=10000&type=DD&aoi=v",
            
            # Try the admin hierarchy with village level
            "https://kgis.ksrsac.in:9000/genericwebservices/ws/nearbyadminhierarchy?coordinates=12.9352,77.6789&distance=10000&type=DD&aoi=d,t,h,v",
        ]
        
        for url in test_urls:
            try:
                r = await client.get(url)
                print(f"\nURL: {url[-80:]}")
                print(f"Status: {r.status_code}")
                print(f"Response: {r.text[:400]}")
            except Exception as e:
                print(f"\nURL: {url[-80:]}")
                print(f"Error: {type(e).__name__}: {e}")

asyncio.run(test())
