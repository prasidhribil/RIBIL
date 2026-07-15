import asyncio
import sys
from datetime import datetime
sys.path.insert(0, 'd:/alstonair')

from app.database import Database

# Manual seed data for NGT court cases
COURT_CASES_DATA = [
    {
        "case_number": "OA-125/2016",
        "village": "Bellandur",
        "survey_no": "Multiple",
        "violation_type": "Lake Encroachment",
        "status": "Active",
        "order_date": "2016-04-15",
        "description": "NGT order on Bellandur Lake pollution and encroachment by builder activities"
    },
    {
        "case_number": "OA-222/2017",
        "village": "Varthur",
        "survey_no": "Multiple",
        "violation_type": "Lake Pollution",
        "status": "Active",
        "order_date": "2017-08-22",
        "description": "Varthur Lake sewage discharge violation order"
    },
    {
        "case_number": "OA-444/2018",
        "village": "Agara",
        "survey_no": "Survey 99",
        "violation_type": "Unauthorized Construction",
        "status": "Closed",
        "order_date": "2018-03-10",
        "description": "Construction within 75m buffer zone of Agara Lake"
    },
    {
        "case_number": "OA-156/2019",
        "village": "Hebbal",
        "survey_no": "Survey 12",
        "violation_type": "Lake Encroachment",
        "status": "Active",
        "order_date": "2019-06-30",
        "description": "Hebbal Lake boundary violation and illegal dumping"
    },
    {
        "case_number": "OA-789/2020",
        "village": "Ulsoor",
        "survey_no": "Survey 45",
        "violation_type": "Water Body Pollution",
        "status": "Pending",
        "order_date": "2020-11-15",
        "description": "Industrial effluent discharge into Ulsoor Lake"
    },
    {
        "case_number": "OA-234/2021",
        "village": "Sankey",
        "survey_no": "Survey 8",
        "violation_type": "Encroachment",
        "status": "Active",
        "order_date": "2021-02-28",
        "description": "Construction within buffer zone of Sankey Tank"
    },
    {
        "case_number": "OA-567/2022",
        "village": "Puttenahalli",
        "survey_no": "Survey 33",
        "violation_type": "Unauthorized Fill",
        "status": "Closed",
        "order_date": "2022-07-12",
        "description": "Illegal filling of Puttenahalli Lake for layout"
    },
    {
        "case_number": "OA-890/2023",
        "village": "Jakkur",
        "survey_no": "Survey 67",
        "violation_type": "Lake Encroachment",
        "status": "Active",
        "order_date": "2023-01-20",
        "description": "Encroachment on Jakkur Lake foreshore land"
    },
    {
        "case_number": "OA-123/2023",
        "village": "Kaikondrahalli",
        "survey_no": "Survey 89",
        "violation_type": "Buffer Violation",
        "status": "Pending",
        "order_date": "2023-09-05",
        "description": "Construction within NGT mandated buffer zone"
    },
    {
        "case_number": "OA-456/2024",
        "village": "Doddakallasandra",
        "survey_no": "Survey 15",
        "violation_type": "Pollution",
        "status": "Active",
        "order_date": "2024-03-18",
        "description": "Sewage and solid waste dumping in lake"
    },
]

async def seed_court_cases():
    await Database.create_pool()
    
    try:
        async with Database.pool.acquire() as conn:
            # Check current count
            count = await conn.fetchval("SELECT COUNT(*) FROM court_cases")
            print(f"Current court_cases count: {count}")
            
            # Insert seed data
            inserted = 0
            for case in COURT_CASES_DATA:
                try:
                    # Convert date string to date object
                    order_date = datetime.strptime(case["order_date"], "%Y-%m-%d").date()
                    
                    query = """
                        INSERT INTO court_cases (
                            case_number, village, survey_no, violation_type, 
                            status, order_date, description
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (case_number) DO NOTHING
                    """
                    await conn.execute(
                        query,
                        case["case_number"],
                        case["village"],
                        case["survey_no"],
                        case["violation_type"],
                        case["status"],
                        order_date,
                        case["description"]
                    )
                    inserted += 1
                    print(f"  Inserted: {case['case_number']} - {case['village']}")
                except Exception as e:
                    print(f"  Error inserting {case['case_number']}: {e}")
            
            # Verify final count
            final_count = await conn.fetchval("SELECT COUNT(*) FROM court_cases")
            print(f"\nFinal court_cases count: {final_count}")
            print(f"Inserted {inserted} new cases")
            
    finally:
        await Database.close_pool()

asyncio.run(seed_court_cases())
