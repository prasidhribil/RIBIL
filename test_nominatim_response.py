import httpx
import asyncio

async def test_nominatim():
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "format": "json",
                "lat": 12.9352,
                "lon": 77.6789,
                "zoom": 14,
                "addressdetails": 1
            },
            headers={
                "User-Agent": "AlstonaireGISEngine/1.0 (land-verification-system)"
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

if __name__ == "__main__":
    asyncio.run(test_nominatim())
