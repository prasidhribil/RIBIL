import httpx, asyncio
async def test():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://kgis.ksrsac.in/kgis/webapi.aspx"
    }
    async with httpx.AsyncClient(
        verify=False, timeout=15.0, headers=headers
    ) as client:
        
        # Get village codes for our 10 test coordinates
        test_coords = [
            (12.9352, 77.6789, "Bellandur"),
            (12.9698, 77.7500, "Whitefield"),
            (12.9352, 77.6245, "Koramangala"),
        ]
        
        for lat, lng, name in test_coords:
            url = (f"https://kgis.ksrsac.in:9000/genericwebservices/ws/"
                   f"nearbyadminhierarchy?coordinates={lat},{lng}"
                   f"&distance=10000&type=DD&aoi=v")
            r = await client.get(url)
            print(f"\n{name} ({lat},{lng}):")
            print(f"Status: {r.status_code}")
            print(f"Response: {r.text[:500]}")
            
            # If village codes returned, try survey number with each
            if r.status_code == 200 and r.text.strip() not in ['[]', '']:
                import json
                try:
                    villages = json.loads(r.text)
                    for v in villages[:3]:  # try first 3 village codes
                        village_code = (v.get('villageCode') or 
                                       v.get('KGISVillageCode') or
                                       v.get('VillageCode') or
                                       v.get('code'))
                        if village_code:
                            survey_url = (
                                f"https://kgis.ksrsac.in:9000/genericwebservices/ws/"
                                f"surveyno?coordinates={lat},{lng}&type=DD"
                                f"&distance=5000&KGISVillageCode={village_code}"
                            )
                            r2 = await client.get(survey_url)
                            print(f"  Village code {village_code}: {r2.text[:200]}")
                except:
                    pass

asyncio.run(test())
