import httpx, asyncio
async def test():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://kgis.ksrsac.in/"
    }
    async with httpx.AsyncClient(verify=False, timeout=15.0,
                                  headers=headers) as client:
        
        # Query each layer in IDD/IDD that might be airport-related
        # Replace LAYER_ID with IDs found in Step C
        base = "https://kgis.ksrsac.in/kgismaps1/rest/services/IDD/IDD/MapServer"
        
        # Test first 5 layers to understand the data
        for layer_id in range(0, 5):
            url = (f"{base}/{layer_id}/query"
                   f"?geometry=77.7066,13.1986"
                   f"&geometryType=esriGeometryPoint"
                   f"&spatialRel=esriSpatialRelIntersects"
                   f"&outFields=*"
                   f"&returnGeometry=false"
                   f"&f=json")
            try:
                r = await client.get(url)
                data = r.json()
                features = data.get('features', [])
                print(f"Layer {layer_id}: {len(features)} features found")
                if features:
                    print(f"  Fields: {list(features[0].get('attributes',{}).keys())}")
                    print(f"  Sample: {features[0].get('attributes',{})}")
            except Exception as e:
                print(f"Layer {layer_id}: Error - {e}")

asyncio.run(test())
