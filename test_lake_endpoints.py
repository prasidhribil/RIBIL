#!/usr/bin/env python3
"""
Test lake-related GIS endpoints with real Bengaluru coordinates
"""
import asyncio
import httpx

# Real Bengaluru coordinates
BENGALURU_COORDS = {
    "MG Road": (12.9756, 77.6066),
    "Indiranagar": (12.9784, 77.6408),
    "Koramangala": (12.9352, 77.6245),
    "Whitefield": (12.9698, 77.7499),
    "Electronic City": (12.8444, 77.6757),
}

BASE_URL = "http://localhost:8000"

async def test_endpoint(name, url, params):
    """Test a single endpoint"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            return {
                "endpoint": name,
                "url": str(response.url),
                "status_code": response.status_code,
                "response": response.json(),
                "error": None
            }
        except Exception as e:
            return {
                "endpoint": name,
                "url": url,
                "status_code": None,
                "response": None,
                "error": str(e)
            }

async def main():
    """Test all lake-related endpoints"""
    results = []
    
    # Test 1: Nearest lake lookup
    for location_name, (lat, lng) in BENGALURU_COORDS.items():
        result = await test_endpoint(
            f"lake-nearest ({location_name})",
            f"{BASE_URL}/api/gis/lake-nearest",
            {"lat": lat, "lng": lng}
        )
        results.append(result)
        print(f"[OK] Tested lake-nearest for {location_name}")
    
    # Test 2: Lake distance calculation
    for location_name, (lat, lng) in BENGALURU_COORDS.items():
        result = await test_endpoint(
            f"lake-distance ({location_name})",
            f"{BASE_URL}/api/gis/lake-distance",
            {"lat": lat, "lng": lng}
        )
        results.append(result)
        print(f"[OK] Tested lake-distance for {location_name}")
    
    # Test 3: NGT buffer zone check (75m)
    for location_name, (lat, lng) in BENGALURU_COORDS.items():
        result = await test_endpoint(
            f"lake-buffer-check-75m ({location_name})",
            f"{BASE_URL}/api/gis/lake-buffer-check",
            {"lat": lat, "lng": lng, "buffer_meters": 75}
        )
        results.append(result)
        print(f"[OK] Tested lake-buffer-check (75m) for {location_name}")
    
    # Test 4: NGT buffer zone check (150m)
    for location_name, (lat, lng) in BENGALURU_COORDS.items():
        result = await test_endpoint(
            f"lake-buffer-check-150m ({location_name})",
            f"{BASE_URL}/api/gis/lake-buffer-check",
            {"lat": lat, "lng": lng, "buffer_meters": 150}
        )
        results.append(result)
        print(f"[OK] Tested lake-buffer-check (150m) for {location_name}")
    
    # Test 5: Comprehensive zone check
    for location_name, (lat, lng) in BENGALURU_COORDS.items():
        result = await test_endpoint(
            f"zone-check ({location_name})",
            f"{BASE_URL}/api/gis/zone-check",
            {"lat": lat, "lng": lng}
        )
        results.append(result)
        print(f"[OK] Tested zone-check for {location_name}")
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    success_count = sum(1 for r in results if r.get("status_code") == 200)
    fail_count = len(results) - success_count
    
    print(f"Total tests: {len(results)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    
    if fail_count > 0:
        print("\nFailed tests:")
        for result in results:
            if result.get("status_code") != 200:
                print(f"  - {result['endpoint']}: {result.get('error', 'Unknown error')}")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
