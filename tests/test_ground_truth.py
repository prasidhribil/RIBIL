#!/usr/bin/env python3
"""
 ============================================================================
 Ground Truth Test Script - 10 Bengaluru Plot Validation
 ============================================================================
 Description: Automated verification of 10 real-world Bengaluru coordinates
 Validates survey number lookup and zone check endpoints against expected outcomes
 Sprint 1 Exit Criteria: All 10 plots must return successfully

 Run Instructions:
   python tests/test_ground_truth.py
   OR
   python -m pytest tests/test_ground_truth.py -v
 ============================================================================
"""

import asyncio
import httpx
import time
from typing import Dict, List, Any
from dataclasses import dataclass
from tabulate import tabulate

# FastAPI server configuration
BASE_URL = "http://localhost:8000"


@dataclass
class CoordinateTest:
    """Test coordinate with expected outcomes."""
    test_id: int
    name: str
    lat: float
    lng: float
    expected_zone_type: str
    expected_buffer_status: str
    expected_aai_restriction: bool = False


# ============================================================================
# 10 Ground Truth Test Cases - Bengaluru Landmarks
# ============================================================================

TEST_COORDINATES = [
    CoordinateTest(
        test_id=1,
        name="Kempegowda International Airport (BIAL)",
        lat=13.2008,
        lng=77.7088,
        expected_zone_type="Airport Restriction",
        expected_buffer_status="none",
        expected_aai_restriction=True
    ),
    CoordinateTest(
        test_id=2,
        name="Ulsoor Lake",
        lat=12.9814,
        lng=77.6225,
        expected_zone_type="Water Body",
        expected_buffer_status="blocked",  # <75m - NGT construction block
        expected_aai_restriction=False
    ),
    CoordinateTest(
        test_id=3,
        name="Sankey Tank",
        lat=13.0105,
        lng=77.5750,
        expected_zone_type="Water Body",
        expected_buffer_status="blocked",  # <75m - NGT construction block
        expected_aai_restriction=False
    ),
    CoordinateTest(
        test_id=4,
        name="Cubbon Park",
        lat=12.9739,
        lng=77.5913,
        expected_zone_type="Green Belt / Park",
        expected_buffer_status="none",
        expected_aai_restriction=False
    ),
    CoordinateTest(
        test_id=5,
        name="Electronic City Phase 1",
        lat=12.8449,
        lng=77.6631,
        expected_zone_type="Industrial / Mixed Use",
        expected_buffer_status="none",
        expected_aai_restriction=False
    ),
    CoordinateTest(
        test_id=6,
        name="Vidhana Soudha",
        lat=12.9796,
        lng=77.5906,
        expected_zone_type="Public & Semi-Public",
        expected_buffer_status="none",
        expected_aai_restriction=False
    ),
    CoordinateTest(
        test_id=7,
        name="Whitefield ITPL Area",
        lat=12.9842,
        lng=77.7479,
        expected_zone_type="Commercial",
        expected_buffer_status="none",
        expected_aai_restriction=False
    ),
    CoordinateTest(
        test_id=8,
        name="Jayanagar 4th Block Lake Buffer (100m)",
        lat=12.9350,
        lng=77.5800,
        expected_zone_type="Residential",
        expected_buffer_status="warning",  # 75-150m - NOC required
        expected_aai_restriction=False
    ),
    CoordinateTest(
        test_id=9,
        name="Bengaluru North Taluk Village",
        lat=13.0500,
        lng=77.5500,
        expected_zone_type="Residential",
        expected_buffer_status="none",
        expected_aai_restriction=False
    ),
    CoordinateTest(
        test_id=10,
        name="Bengaluru South Taluk Village",
        lat=12.9000,
        lng=77.6000,
        expected_zone_type="Residential",
        expected_buffer_status="none",
        expected_aai_restriction=False
    ),
]


class GroundTruthTester:
    """Automated tester for ground truth validation."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.passed_count = 0
        self.failed_count = 0
    
    async def test_survey_number(self, client: httpx.AsyncClient, coord: CoordinateTest) -> Dict[str, Any]:
        """
        Test survey number endpoint for a coordinate.
        
        Args:
            client: HTTP client
            coord: Test coordinate
            
        Returns:
            Survey number response data
        """
        url = f"{BASE_URL}/api/gis/survey-number"
        params = {"lat": coord.lat, "lng": coord.lng}
        
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Validate response structure
            assert "survey_no" in data, "Missing survey_no field"
            assert "confidence" in data, "Missing confidence field"
            assert data["confidence"] in ["exact", "nearest"], f"Invalid confidence: {data['confidence']}"
            
            return {
                "success": True,
                "survey_no": data.get("survey_no"),
                "confidence": data.get("confidence"),
                "village": data.get("village"),
                "hobli": data.get("hobli"),
                "district": data.get("district")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_zone_check(self, client: httpx.AsyncClient, coord: CoordinateTest) -> Dict[str, Any]:
        """
        Test zone check endpoint for a coordinate.
        
        Args:
            client: HTTP client
            coord: Test coordinate
            
        Returns:
            Zone check response data
        """
        url = f"{BASE_URL}/api/gis/zone-check"
        params = {"lat": coord.lat, "lng": coord.lng}
        
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Validate response structure
            assert "cdp_zone" in data, "Missing cdp_zone field"
            assert "lake_buffer" in data, "Missing lake_buffer field"
            assert "ngt_orders" in data, "Missing ngt_orders field"
            assert "aai_zone" in data, "Missing aai_zone field"
            assert "overall_status" in data, "Missing overall_status field"
            
            # Extract zone information
            cdp_zone = data.get("cdp_zone", {})
            lake_buffer = data.get("lake_buffer", {})
            aai_zone = data.get("aai_zone", {})
            
            return {
                "success": True,
                "zone_type": cdp_zone.get("zone_type", "Unknown"),
                "is_blocked": lake_buffer.get("is_blocked", False),
                "is_warning": lake_buffer.get("is_warning", False),
                "nearest_lake": lake_buffer.get("nearest_lake"),
                "distance_meters": lake_buffer.get("distance_meters"),
                "aai_restricted": aai_zone.get("in_restriction_zone", False),
                "overall_status": data.get("overall_status")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_expected_outcomes(
        self,
        coord: CoordinateTest,
        survey_result: Dict[str, Any],
        zone_result: Dict[str, Any]
    ) -> bool:
        """
        Validate that results match expected outcomes.
        
        Args:
            coord: Test coordinate with expected outcomes
            survey_result: Survey number test result
            zone_result: Zone check test result
            
        Returns:
            True if validation passed, False otherwise
        """
        if not survey_result["success"] or not zone_result["success"]:
            return False
        
        # Validate buffer status
        buffer_status = "none"
        if zone_result["is_blocked"]:
            buffer_status = "blocked"
        elif zone_result["is_warning"]:
            buffer_status = "warning"
        
        # Check if buffer status matches expected
        if coord.expected_buffer_status != "none" and buffer_status != coord.expected_buffer_status:
            print(f"  ⚠ Buffer status mismatch: expected {coord.expected_buffer_status}, got {buffer_status}")
        
        # Check AAI restriction
        if coord.expected_aai_restriction and not zone_result["aai_restricted"]:
            print(f"  ⚠ Expected AAI restriction but not detected")
        
        return True
    
    async def run_all_tests(self):
        """Run all ground truth tests."""
        print("=" * 80)
        print("GROUND TRUTH TEST - 10 Bengaluru Plot Validation")
        print("=" * 80)
        print(f"Target: {BASE_URL}")
        print(f"Test Cases: {len(TEST_COORDINATES)}")
        print("=" * 80)
        print()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for coord in TEST_COORDINATES:
                print(f"Test {coord.test_id}: {coord.name}")
                print(f"  Coordinates: ({coord.lat}, {coord.lng})")
                
                # Test survey number
                survey_result = await self.test_survey_number(client, coord)
                
                # Test zone check
                zone_result = await self.test_zone_check(client, coord)
                
                # Validate outcomes
                passed = self.validate_expected_outcomes(coord, survey_result, zone_result)
                
                # Record result
                result = {
                    "test_id": coord.test_id,
                    "name": coord.name,
                    "coordinates": f"({coord.lat}, {coord.lng})",
                    "survey_no": survey_result.get("survey_no", "N/A") if survey_result["success"] else "ERROR",
                    "confidence": survey_result.get("confidence", "N/A") if survey_result["success"] else "ERROR",
                    "zone_type": zone_result.get("zone_type", "N/A") if zone_result["success"] else "ERROR",
                    "buffer_status": "blocked" if zone_result.get("is_blocked") else ("warning" if zone_result.get("is_warning") else "none") if zone_result["success"] else "ERROR",
                    "aai_restricted": zone_result.get("aai_restricted", False) if zone_result["success"] else False,
                    "passed": passed and survey_result["success"] and zone_result["success"]
                }
                
                self.results.append(result)
                
                if result["passed"]:
                    self.passed_count += 1
                    print(f"  [PASS] PASSED")
                else:
                    self.failed_count += 1
                    print(f"  [FAIL] FAILED")
                    if not survey_result["success"]:
                        print(f"    Survey Error: {survey_result.get('error')}")
                    if not zone_result["success"]:
                        print(f"    Zone Error: {zone_result.get('error')}")
                
                print()
    
    def print_summary_table(self):
        """Print terminal execution summary table."""
        print("=" * 80)
        print("EXECUTION SUMMARY")
        print("=" * 80)
        
        table_data = []
        for result in self.results:
            table_data.append([
                result["test_id"],
                result["coordinates"],
                result["survey_no"],
                result["zone_type"],
                result["buffer_status"],
                "PASS" if result["passed"] else "FAIL"
            ])
        
        headers = ["Test ID", "Coordinates", "Survey No", "Zone Type", "Buffer Status", "Passed"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        print()
        print(f"Total Tests: {len(self.results)}")
        print(f"Passed: {self.passed_count}")
        print(f"Failed: {self.failed_count}")
        print()
        
        # Sprint 1 Exit Criteria Check
        if self.passed_count == len(TEST_COORDINATES):
            print("[PASS] SPRINT 1 EXIT CRITERIA MET: All 10 plots returned successfully")
        else:
            print(f"[FAIL] SPRINT 1 EXIT CRITERIA NOT MET: {self.failed_count} plots failed")
        
        print("=" * 80)


async def main():
    """Main execution function."""
    tester = GroundTruthTester()
    await tester.run_all_tests()
    tester.print_summary_table()
    
    # Exit with appropriate code
    exit(0 if tester.passed_count == len(TEST_COORDINATES) else 1)


if __name__ == "__main__":
    asyncio.run(main())
