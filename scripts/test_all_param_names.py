import httpx, asyncio
async def test():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://kgis.ksrsac.in/kgis/webapi.aspx"
    }
    async with httpx.AsyncClient(
        verify=False, timeout=15.0, headers=headers
    ) as client:
        
        # Use Bellandur coordinate and first village code
        lat, lng = 12.9352, 77.6789
        village_code = "2001010013"
        
        # Try all parameter name variations
        param_names = [
            "KGISVillageCode",
            "villageCode", 
            "village_code",
            "VillageCode",
            "kgisVillageCode",
            "KGIS_VillageCode",
            "villagecode"
        ]
        
        print(f"Testing survey number API with village code {village_code}\n")
        
        for param_name in param_names:
            survey_url = (
                f"https://kgis.ksrsac.in:9000/genericwebservices/ws/"
                f"surveyno?coordinates={lat},{lng}&type=DD"
                f"&distance=5000&{param_name}={village_code}"
            )
            r = await client.get(survey_url)
            print(f"{param_name}: {r.text[:200]}")

asyncio.run(test())
