import httpx
import asyncio

async def test_health():
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get('http://localhost:8000/health')
            print(f"Health Status: {response.status_code}")
            print(f"Health Response: {response.text}")
        except Exception as e:
            print(f"Health Error: {e}")

async def test_resolve():
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                'http://localhost:8000/api/location/resolve',
                json={'lat': 12.9352, 'lng': 77.6789}
            )
            print(f"Resolve Status: {response.status_code}")
            print(f"Resolve Response: {response.text}")
        except Exception as e:
            print(f"Resolve Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_health())
    asyncio.run(test_resolve())
