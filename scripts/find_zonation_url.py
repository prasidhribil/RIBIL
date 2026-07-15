import httpx, asyncio
async def test():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://kgis.ksrsac.in/"
    }
    async with httpx.AsyncClient(verify=False, timeout=15.0,
                                  headers=headers) as client:
        r = await client.get("https://kgis.ksrsac.in/kgis/webapi.aspx")
        print(f"Status: {r.status_code}")
        # Search for zonation-related text in the page
        text = r.text
        # Find all occurrences of relevant keywords
        import re
        # Look for service URLs in the page
        urls = re.findall(
            r'https?://[^\s\'"<>]+(?:zonat|zone|cdp|landuse|lulc)[^\s\'"<>]*', 
            text, re.IGNORECASE
        )
        print(f"Found URLs with zone/zonation keywords: {urls}")
        
        # Also find any text near "Fetching Zonation"
        idx = text.lower().find('zonation')
        if idx > 0:
            print(f"Context around 'zonation': {text[max(0,idx-200):idx+500]}")
        else:
            print("Word 'zonation' not found in page")
            
        # Also search for all API endpoint URLs on the page
        all_ws_urls = re.findall(
            r'https?://kgis\.ksrsac\.in[^\s\'"<>]*genericwebservices[^\s\'"<>]*',
            text, re.IGNORECASE
        )
        print(f"All genericwebservices URLs found: {all_ws_urls}")

asyncio.run(test())
