import asyncio
import sys
sys.path.insert(0, 'd:\\alstonair')

from app.services.bhoomi_survey import resolve_survey_number

async def test():
    # Use actual centroid from Bhoomi SurveyNo 383
    lat, lng = 12.8521, 77.7893
    result = await resolve_survey_number(lat, lng, "20", "3", "5", "2", cache=None)
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test())
