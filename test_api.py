import httpx
import asyncio

async def test_resolve():
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                'http://localhost:8000/api/location/resolve',
                json={'lat': 12.9352, 'lng': 77.6789}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_resolve())
