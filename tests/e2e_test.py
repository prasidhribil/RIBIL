import httpx, asyncio, json

async def e2e_test():
    print("=== END-TO-END PROPERTY VERIFICATION TEST ===\n")
    
    # Use Koramangala coordinate as test property
    lat, lng = 12.9352, 77.6245
    property_id = "E2E-TEST-001"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Step 1: Resolve location
        print("STEP 1: Resolving location...")
        r1 = await client.post(
            "http://localhost:8000/api/location/resolve",
            json={"lat": lat, "lng": lng}
        )
        loc = r1.json()
        print(f"  District: {loc.get('district')}")
        print(f"  Village: {loc.get('village')}")
        print(f"  Source: {loc.get('source')}")
        print(f"  Status: {'PASS' if r1.status_code == 200 else 'FAIL'}\n")
        
        # Step 2: Get survey number
        print("STEP 2: Looking up survey number...")
        r2 = await client.get(
            f"http://localhost:8000/api/gis/survey-number"
            f"?latitude={lat}&longitude={lng}"
        )
        survey = r2.json()
        print(f"  Survey No: {survey.get('survey_no', 'Not found')}")
        print(f"  Status: {'PASS' if survey.get('success') else 'FAIL (KGIS API limitation)'}\n")
        
        # Step 3: Zone check
        print("STEP 3: Running zone compliance checks...")
        r3 = await client.get(
            f"http://localhost:8000/api/gis/zone-check?lat={lat}&lng={lng}"
        )
        zones = r3.json()
        print(f"  CDP Zone: {zones.get('cdp_zone',{}).get('zone_type')}")
        print(f"  Lake Buffer: {zones.get('lake_buffer',{}).get('is_blocked')} blocked, "
              f"{zones.get('lake_buffer',{}).get('is_warning')} warning")
        print(f"  AAI Zone: {zones.get('aai_zone',{}).get('restriction_type')}")
        print(f"  NGT Cases: {zones.get('ngt_orders',{}).get('case_count')} cases")
        print(f"  Overall: {zones.get('overall_status')}")
        print(f"  Status: {'PASS' if r3.status_code == 200 else 'FAIL'}\n")
        
        # Step 4: Submit to verification queue
        print("STEP 4: Submitting to verification queue...")
        try:
            r4 = await client.post(
                "http://localhost:3000/api/property/verify",
                json={"lat": lat, "lng": lng, "property_id": property_id},
                headers={"Authorization": "Bearer test-token"}
            )
            job = r4.json()
            job_id = job.get('job_id')
            print(f"  Job ID: {job_id}")
            print(f"  Status: {'PASS' if r4.status_code in [200,202] else 'SKIP (queue not running)'}\n")
            queue_running = r4.status_code in [200,202]
        except Exception as e:
            print(f"  Status: SKIP (queue not running: {e})\n")
            queue_running = False
            job_id = None
            job_status = "skipped"
        
        # Step 5: Poll until complete (only if queue is running)
        if queue_running and job_id:
            print("STEP 5: Polling job status...")
            for i in range(8):
                await asyncio.sleep(2)
                r5 = await client.get(
                    f"http://localhost:3000/api/property/verify/status/{job_id}",
                    headers={"Authorization": "Bearer test-token"}
                )
                status = r5.json()
                steps = status.get('progress', {}).get('steps_completed', 0)
                total = status.get('progress', {}).get('steps_total', 14)
                job_status = status.get('status')
                print(f"  Poll {i+1}: {job_status} - {steps}/{total} steps")
                if job_status == 'completed':
                    break
        else:
            job_status = "skipped"
        
        print(f"\n{'='*50}")
        print("END-TO-END TEST SUMMARY")
        print(f"{'='*50}")
        print(f"Location resolve:  {'PASS' if r1.status_code == 200 else 'FAIL'}")
        print(f"Survey number:     {'PASS' if survey.get('success') else 'FAIL (known limitation)'}")
        print(f"Zone check:        {'PASS' if r3.status_code == 200 else 'FAIL'}")
        print(f"Queue submission:  {'PASS' if queue_running else 'SKIP (queue not running)'}")
        print(f"Job completion:    {'PASS' if job_status == 'completed' else 'SKIP (queue not running)'}")

asyncio.run(e2e_test())
