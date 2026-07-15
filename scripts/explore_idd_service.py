import httpx, asyncio, json
async def test():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://kgis.ksrsac.in/"
    }
    async with httpx.AsyncClient(verify=False, timeout=15.0,
                                  headers=headers) as client:
        
        # Get all layers in IDD/IDD MapServer
        url = "https://kgis.ksrsac.in/kgismaps1/rest/services/IDD/IDD/MapServer?f=json"
        r = await client.get(url)
        print(f"IDD/IDD MapServer status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            layers = data.get('layers', [])
            print(f"Total layers: {len(layers)}")
            print("All layer names and IDs:")
            for layer in layers:
                print(f"  ID {layer.get('id')}: {layer.get('name')}")
            
            # Find airport-related layers
            airport_layers = [l for l in layers if any(
                keyword in l.get('name','').lower() 
                for keyword in ['airport', 'aviation', 'aai', 'bial', 'hal', 
                               'airstrip', 'runway', 'idd']
            )]
            print(f"\nAirport-related layers: {airport_layers}")

asyncio.run(test())
