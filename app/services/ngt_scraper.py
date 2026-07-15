"""
 ============================================================================
 NGT Scraper Service
 ============================================================================
 Description: Scrapes NGT (National Green Tribunal) Southern Zone cases
 Focus: Environmental violation cases for Karnataka villages
 ============================================================================
"""

import httpx
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


async def scrape_ngt_cases(search_term: str) -> list[dict]:
    """
    Scrapes NGT Southern Zone cases for a given search term.
    Returns list of case dicts matching court_cases table schema.
    
    NOTE: The NGT website requires CAPTCHA for searches, which blocks
    automated scraping. This function attempts the search but will likely
    return empty results due to CAPTCHA protection.
    
    Args:
        search_term: Village name or search term to query
        
    Returns:
        List of case dictionaries with case_number, village, survey_no, 
        violation_type, status, order_date, description
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.greentribunal.gov.in/casestatus/freetext"
    }
    
    # GET to NGT free text search (correct method based on form analysis)
    # zone_type=5 for Southern Zone, search_by=1 for Word Search
    params = {
        "zone_type": "5",  # Southern Zone
        "search_by": "1",  # Word Search
        "text_name": search_term
    }
    
    async with httpx.AsyncClient(
        verify=False, timeout=30.0, headers=headers,
        follow_redirects=True
    ) as client:
        try:
            r = await client.get(
                "https://www.greentribunal.gov.in/casestatus/freetextsearch",
                params=params
            )
            if r.status_code != 200:
                logger.warning(f"NGT scraper returned status {r.status_code}")
                return []
            
            soup = BeautifulSoup(r.text, 'html.parser')
            cases = []
            
            # Parse case table from response
            # Look for table rows with case data
            table = soup.find('table', {'class': lambda x: x and 'table' in x})
            if not table:
                # Try finding any table with case numbers
                tables = soup.find_all('table')
                table = tables[0] if tables else None
            
            if table:
                rows = table.find_all('tr')[1:]  # skip header
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        cases.append({
                            'case_number': cols[0].get_text(strip=True),
                            'village': search_term,  # use search term as village
                            'survey_no': None,
                            'violation_type': 'Environmental Violation',
                            'status': 'Active',
                            'order_date': None,
                            'description': cols[-1].get_text(strip=True)[:500]
                        })
            
            logger.info(f"NGT scraper found {len(cases)} cases for '{search_term}'")
            return cases
            
        except Exception as e:
            logger.error(f"NGT scraper error: {e}")
            return []
