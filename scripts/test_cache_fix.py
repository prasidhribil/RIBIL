import httpx
import asyncio

async def test():
    print("Testing cache fix - checking for WARNING logs...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test resolve endpoint
        print("\n1. Testing resolve endpoint...")
        r1 = await client.post(
            "http://localhost:8000/api/location/resolve",
            json={"lat": 12.9352, "lng": 77.6789}
        )
        print(f"   Status: {r1.status_code}")
        print(f"   Response: {r1.json()}")
        
        # Test survey number endpoint
        print("\n2. Testing survey number endpoint...")
        r2 = await client.get(
            "http://localhost:8000/api/gis/survey-number?latitude=12.9352&longitude=77.6789"
        )
        print(f"   Status: {r2.status_code}")
        print(f"   Response: {r2.json()}")
        
        # Test zone check endpoint
        print("\n3. Testing zone check endpoint...")
        r3 = await client.get(
            "http://localhost:8000/api/gis/zone-check?lat=12.9352&lng=77.6789"
        )
        print(f"   Status: {r3.status_code}")
        print(f"   Response: {r3.json()}")
        
        print("\nCheck FastAPI logs for any WARNING messages related to cache.")
        print("Expected: Zero cache WARNING messages (all should use get_key/set_key)")

asyncio.run(test())
