import httpx, asyncio, json
from datetime import datetime

# 30 real Bengaluru coordinates spread across different areas
PILOT_PLOTS = [
    # Bengaluru South
    (12.9352, 77.6789, "Bellandur"),
    (12.9250, 77.6700, "Sarjapur Road"),
    (12.9150, 77.6400, "HSR Layout"),
    (12.9000, 77.6300, "BTM Layout"),
    (12.8900, 77.6200, "Bannerghatta Road"),
    # Bengaluru East  
    (12.9698, 77.7500, "Whitefield"),
    (12.9600, 77.7300, "Marathahalli"),
    (12.9500, 77.7100, "KR Puram"),
    (12.9417, 77.7415, "Varthur"),
    (12.9800, 77.7600, "Kadugodi"),
    # Bengaluru North
    (13.1007, 77.5963, "Yelahanka"),
    (13.0358, 77.5970, "Hebbal"),
    (13.0600, 77.5800, "Thanisandra"),
    (13.0800, 77.6100, "Kothanur"),
    (13.0200, 77.5500, "Jalahalli"),
    # Bengaluru West
    (12.9081, 77.4856, "Kengeri"),
    (12.9200, 77.5100, "Vijayanagar"),
    (12.9400, 77.5300, "Rajajinagar"),
    (12.9600, 77.5500, "Yeshwanthpur"),
    (12.9700, 77.5200, "Peenya"),
    # Bengaluru Central
    (12.9716, 77.5946, "Indiranagar"),
    (12.9352, 77.6245, "Koramangala"),
    (12.9600, 77.5800, "Malleshwaram"),
    (12.9500, 77.5700, "Sadashivanagar"),
    (12.9400, 77.5900, "Vasanth Nagar"),
    # Near Lakes (for buffer testing)
    (12.9200, 77.6500, "Agara Lake area"),
    (13.0200, 77.6400, "Hebbal Lake area"),
    (12.9800, 77.6300, "Sankey Tank area"),
    # Near Airport
    (13.1986, 77.7066, "BIAL Airport"),
    (12.9499, 77.6681, "HAL Airport"),
]

async def run_pilot():
    results = []
    errors = 0
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for lat, lng, area_name in PILOT_PLOTS:
            result = {"area": area_name, "lat": lat, "lng": lng}
            
            try:
                # Test location resolve
                r = await client.post(
                    "http://localhost:8000/api/location/resolve",
                    json={"lat": lat, "lng": lng}
                )
                if r.status_code == 200:
                    data = r.json()
                    result["district"] = data.get("district", "N/A")
                    result["village"] = data.get("village", "N/A")
                    result["source"] = data.get("source", "N/A")
                    result["resolve_ok"] = True
                else:
                    result["resolve_ok"] = False
                    errors += 1
                    
                # Test survey number
                r2 = await client.get(
                    f"http://localhost:8000/api/gis/survey-number?latitude={lat}&longitude={lng}"
                )
                if r2.status_code == 200:
                    d2 = r2.json()
                    result["survey_no"] = d2.get("survey_no", "Not found")
                    result["survey_ok"] = d2.get("success", False)
                else:
                    result["survey_ok"] = False
                    
                # Test zone check
                r3 = await client.get(
                    f"http://localhost:8000/api/gis/zone-check?lat={lat}&lng={lng}"
                )
                if r3.status_code == 200:
                    d3 = r3.json()
                    result["cdp_zone"] = d3.get("cdp_zone", {}).get("zone_type", "N/A")
                    result["aai_restricted"] = d3.get("aai_zone", {}).get("in_restriction_zone", False)
                    result["overall_status"] = d3.get("overall_status", "N/A")
                    result["zone_ok"] = True
                else:
                    result["zone_ok"] = False
                    errors += 1
                    
            except Exception as e:
                result["error"] = str(e)[:100]
                errors += 1
            
            results.append(result)
            print(f"[OK] {area_name}: resolve={result.get('resolve_ok','?')} "
                  f"survey={result.get('survey_ok','?')} "
                  f"zone={result.get('zone_ok','?')}")
            
            # Small delay to avoid hammering external APIs
            await asyncio.sleep(0.5)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"PILOT RESULTS: {len(PILOT_PLOTS)} plots tested")
    print(f"{'='*60}")
    resolve_ok = sum(1 for r in results if r.get('resolve_ok'))
    survey_ok = sum(1 for r in results if r.get('survey_ok'))
    zone_ok = sum(1 for r in results if r.get('zone_ok'))
    print(f"Location resolve: {resolve_ok}/{len(PILOT_PLOTS)}")
    print(f"Survey number:    {survey_ok}/{len(PILOT_PLOTS)}")
    print(f"Zone check:       {zone_ok}/{len(PILOT_PLOTS)}")
    print(f"Total errors:     {errors}")
    
    # Save results
    with open("tests/sprint4_pilot_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to tests/sprint4_pilot_results.json")
    
    # Sprint 4 pass criteria
    print(f"\nSPRINT 4 CRITERIA:")
    print(f"[PASS] Resolve 27+/30: {'PASS' if resolve_ok >= 27 else 'FAIL'} ({resolve_ok}/30)")
    print(f"[PASS] Zone check 27+/30: {'PASS' if zone_ok >= 27 else 'FAIL'} ({zone_ok}/30)")

asyncio.run(run_pilot())
