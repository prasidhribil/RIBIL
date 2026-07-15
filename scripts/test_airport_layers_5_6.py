import httpx, asyncio
async def test():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://kgis.ksrsac.in/"
    }
    async with httpx.AsyncClient(verify=False, timeout=15.0,
                                  headers=headers) as client:
        
        base = "https://kgis.ksrsac.in/kgismaps1/rest/services/IDD/IDD/MapServer"
        
        # Test airport layers specifically (5 and 6)
        for layer_id in [5, 6]:
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
                else:
                    print(f"  No features found at BIAL coordinate")
                    # Try a broader query without spatial filter to see what's in the layer
                    url_all = (f"{base}/{layer_id}/query"
                              f"?where=1%3D1"
                              f"&outFields=*"
                              f"&returnGeometry=false"
                              f"&f=json")
                    r_all = await client.get(url_all)
                    data_all = r_all.json()
                    all_features = data_all.get('features', [])
                    print(f"  Total features in layer: {len(all_features)}")
                    if all_features:
                        print(f"  Sample fields: {list(all_features[0].get('attributes',{}).keys())}")
                        print(f"  Sample data: {all_features[0].get('attributes',{})}")
            except Exception as e:
                print(f"Layer {layer_id}: Error - {e}")

asyncio.run(test())
