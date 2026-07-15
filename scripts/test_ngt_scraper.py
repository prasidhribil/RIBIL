import httpx, asyncio
from bs4 import BeautifulSoup

async def test():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://greentribunal.gov.in",
        "Referer": "https://greentribunal.gov.in/casestatus/freetext"
    }
    
    async with httpx.AsyncClient(
        verify=False, timeout=30.0, 
        headers=headers, follow_redirects=True
    ) as client:
        # First GET the page to find exact form field names and values
        print("=== STEP 1: GET the form page ===")
        r = await client.get(
            "https://greentribunal.gov.in/casestatus/freetext"
        )
        print(f"Status: {r.status_code}")
        
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Find all form inputs
        forms = soup.find_all('form')
        print(f"Forms found: {len(forms)}")
        for i, form in enumerate(forms):
            print(f"\nForm {i}: action={form.get('action')} method={form.get('method')}")
            inputs = form.find_all(['input', 'select', 'textarea'])
            for inp in inputs:
                print(f"  Field: name={inp.get('name')} type={inp.get('type')} value={inp.get('value', '')[:50]}")
        
        # Find select options for Zonal Bench
        selects = soup.find_all('select')
        for sel in selects:
            print(f"\nSelect: name={sel.get('name')}")
            options = sel.find_all('option')
            for opt in options:
                print(f"  Option: value='{opt.get('value')}' text='{opt.get_text(strip=True)}'")
        
        print("\n=== STEP 2: Try POST with discovered field names ===")
        # Try multiple payload variations based on what we find
        payloads = [
            {"zonalBench": "SZ", "searchBy": "1", "freeText": "Bengaluru lake"},
            {"zonalBench": "5", "searchBy": "1", "freeText": "Bengaluru lake"},
            {"bench": "SZ", "searchType": "1", "searchText": "Bengaluru lake"},
            {"zonal_bench": "Southern Zone", "search_by": "Word Search", 
             "free_text": "Bengaluru lake"},
        ]
        
        for payload in payloads:
            try:
                r2 = await client.post(
                    "https://greentribunal.gov.in/casestatus/freetext",
                    data=payload
                )
                print(f"\nPayload {list(payload.keys())}: Status={r2.status_code}, Length={len(r2.text)}")
                if len(r2.text) > 5000:  # substantial response
                    soup2 = BeautifulSoup(r2.text, 'html.parser')
                    tables = soup2.find_all('table')
                    print(f"  Tables found: {len(tables)}")
                    if tables:
                        rows = tables[0].find_all('tr')
                        print(f"  First table rows: {len(rows)}")
                        for row in rows[:3]:
                            print(f"  Row: {row.get_text(strip=True)[:100]}")
            except Exception as e:
                print(f"  Error: {e}")

asyncio.run(test())
