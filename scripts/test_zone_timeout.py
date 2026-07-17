import httpx
import asyncio

async def test():
    print("Testing zone-check endpoint with 30-second timeout...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "http://localhost:8000/api/gis/zone-check?lat=12.9352&lng=77.6789"
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
    except httpx.TimeoutException:
        print("ERROR: Request timed out after 30 seconds")
    except Exception as e:
        print(f"ERROR: {e}")

asyncio.run(test())
