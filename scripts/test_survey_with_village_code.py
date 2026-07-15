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
        
        # First get village code
        hierarchy_url = "https://kgis.ksrsac.in:9000/genericwebservices/ws/nearbyadminhierarchy"
        hierarchy_params = {
            "coordinates": "12.9352,77.6789",
            "distance": 10000,
            "type": "DD",
            "aoi": "v"
        }
        
        r = await client.get(hierarchy_url, params=hierarchy_params)
        print(f"Hierarchy response: {r.text[:500]}")
        
        if r.status_code == 200:
            hierarchy_data = r.json()
            if hierarchy_data:
                village_code = hierarchy_data[0].get("villageCode")
                village_name = hierarchy_data[0].get("villageName")
                print(f"\nUsing village code: {village_code} ({village_name})")
                
                # Try different parameter names for village code
                test_params = [
                    {"KGISVillageCode": village_code},
                    {"villageCode": village_code},
                    {"village_code": village_code},
                    {"VillageCode": village_code},
                ]
                
                for params in test_params:
                    survey_url = "https://kgis.ksrsac.in:9000/genericwebservices/ws/surveyno"
                    survey_params = {
                        "coordinates": "12.9352,77.6789",
                        "type": "DD",
                        "distance": 5000,
                        **params
                    }
                    
                    r2 = await client.get(survey_url, params=survey_params)
                    print(f"\nParams: {list(params.keys())}")
                    print(f"Status: {r2.status_code}")
                    print(f"Response: {r2.text[:300]}")

asyncio.run(test())
