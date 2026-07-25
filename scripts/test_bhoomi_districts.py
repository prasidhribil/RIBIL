import httpx
import json

async def test():
    headers = {"Referer": "https://rdservices.karnataka.gov.in/BhoomiMaps/"}
    
    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        r = await client.post("https://rdservices.karnataka.gov.in/BhoomiMaps/Default/GetDistrict")
        districts_text = r.text
        districts = json.loads(districts_text)
        if isinstance(districts, str):
            districts = json.loads(districts)
        
        print(f"Total districts: {len(districts)}")
        print("\nFirst 10 districts:")
        for d in districts[:10]:
            print(f"  {d['DistrictName']} (code: {d['DISTRICT_CODE']})")
        
        # Search for Bengaluru
        print("\nSearching for Bengaluru:")
        for d in districts:
            if "bengaluru" in d["DistrictName"].lower():
                print(f"  {d['DistrictName']} (code: {d['DISTRICT_CODE']})")

import asyncio
asyncio.run(test())
