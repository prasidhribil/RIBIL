#!/usr/bin/env python3
"""
 ============================================================================
 Redis Caching Validator Script - GIS Cache Integration Test
 ============================================================================
 Description: Validates Redis caching layer is protecting APIs and delivering sub-50ms responses
 Tests cache miss (first call) vs cache hit (second call) performance
 Verifies cache key format and TTL configuration

 Run Instructions:
   python tests/test_gis_cache.py
   OR
   python -m pytest tests/test_gis_cache.py -v -s
 ============================================================================
"""

import asyncio
import httpx
import redis.asyncio as redis
import time
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8000"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Performance threshold for cached responses (milliseconds)
CACHE_HIT_THRESHOLD_MS = 50

# Test coordinate (Cubbon Park - central Bengaluru)
TEST_LAT = 12.9739
TEST_LNG = 77.5913


class RedisCacheValidator:
    """Validator for Redis caching integration."""
    
    def __init__(self):
        self.redis_client = None
        self.cache_key = None
        self.cache_ttl = None
        self.first_call_time = 0
        self.second_call_time = 0
        self.cache_hit_detected = False
    
    async def connect_redis(self):
        """Establish Redis connection."""
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                password=REDIS_PASSWORD,
                db=REDIS_DB,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            print("[OK] Redis connection established")
        except Exception as e:
            print(f"[ERROR] Redis connection failed: {e}")
            print("  Ensure Redis server is running")
            raise
    
    async def close_redis(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            print("[OK] Redis connection closed")
    
    def _generate_expected_cache_key(self, lat: float, lng: float, endpoint: str = "zone-check") -> str:
        """
        Generate expected cache key format.
        
        Args:
            lat: Latitude
            lng: Longitude
            endpoint: Endpoint identifier
            
        Returns:
            Expected cache key string
        """
        lat_rounded = round(lat, 6)
        lng_rounded = round(lng, 6)
        return f"gis_cache:{endpoint}:{lat_rounded}:{lng_rounded}"
    
    async def clear_test_cache(self):
        """Clear any existing cache for the test coordinate."""
        expected_key = self._generate_expected_cache_key(TEST_LAT, TEST_LNG, "zone-check")
        try:
            await self.redis_client.delete(expected_key)
            print(f"[OK] Cleared existing cache key: {expected_key}")
        except Exception as e:
            print(f"[WARN] Could not clear cache key: {e}")
    
    async def test_cache_miss(self) -> Dict[str, Any]:
        """
        Test first call (cache miss) - should hit database.
        
        Returns:
            Dictionary with test results
        """
        print("\n" + "=" * 80)
        print("TEST 1: Cache Miss (First Call)")
        print("=" * 80)
        
        url = f"{BASE_URL}/api/gis/zone-check"
        params = {"lat": TEST_LAT, "lng": TEST_LNG}
        
        print(f"\nRequest: GET {url}")
        print(f"Parameters: lat={TEST_LAT}, lng={TEST_LNG}")
        print("\nExpected: Cache miss - should query database")
        
        try:
            start_time = time.time()
            response = await httpx.AsyncClient(timeout=30.0).get(url, params=params)
            end_time = time.time()
            
            self.first_call_time = (end_time - start_time) * 1000  # Convert to ms
            
            print(f"\nResponse Status: {response.status_code}")
            print(f"Response Time: {self.first_call_time:.2f} ms")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\nResponse Data:")
                print(f"  Overall Status: {data.get('overall_status')}")
                print(f"  CDP Zone: {data.get('cdp_zone', {}).get('zone_type', 'N/A')}")
                print(f"  Lake Buffer: Blocked={data.get('lake_buffer', {}).get('is_blocked')}, Warning={data.get('lake_buffer', {}).get('is_warning')}")
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response_time_ms": self.first_call_time,
                    "data": data
                }
            else:
                print(f"[ERROR] Unexpected status code: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Status code {response.status_code}"
                }
                
        except Exception as e:
            print(f"[ERROR] Request failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_cache_hit(self) -> Dict[str, Any]:
        """
        Test second call (cache hit) - should return from cache.
        
        Returns:
            Dictionary with test results
        """
        print("\n" + "=" * 80)
        print("TEST 2: Cache Hit (Second Call)")
        print("=" * 80)
        
        url = f"{BASE_URL}/api/gis/zone-check"
        params = {"lat": TEST_LAT, "lng": TEST_LNG}
        
        print(f"\nRequest: GET {url}")
        print(f"Parameters: lat={TEST_LAT}, lng={TEST_LNG}")
        print("\nExpected: Cache hit - should return from Redis")
        
        try:
            start_time = time.time()
            response = await httpx.AsyncClient(timeout=30.0).get(url, params=params)
            end_time = time.time()
            
            self.second_call_time = (end_time - start_time) * 1000  # Convert to ms
            
            print(f"\nResponse Status: {response.status_code}")
            print(f"Response Time: {self.second_call_time:.2f} ms")
            
            # Performance assertion
            if self.second_call_time < CACHE_HIT_THRESHOLD_MS:
                print(f"[OK] Cache hit performance OK: {self.second_call_time:.2f} ms < {CACHE_HIT_THRESHOLD_MS} ms threshold")
                self.cache_hit_detected = True
            else:
                print(f"[ERROR] Cache hit performance WARNING: {self.second_call_time:.2f} ms >= {CACHE_HIT_THRESHOLD_MS} ms threshold")
                print(f"  Cache may not be working correctly")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\nResponse Data:")
                print(f"  Overall Status: {data.get('overall_status')}")
                print(f"  CDP Zone: {data.get('cdp_zone', {}).get('zone_type', 'N/A')}")
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response_time_ms": self.second_call_time,
                    "meets_threshold": self.second_call_time < CACHE_HIT_THRESHOLD_MS,
                    "data": data
                }
            else:
                print(f"[ERROR] Unexpected status code: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Status code {response.status_code}"
                }
                
        except Exception as e:
            print(f"[ERROR] Request failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def verify_cache_key_and_ttl(self) -> Dict[str, Any]:
        """
        Verify cache key format and TTL in Redis.
        
        Returns:
            Dictionary with verification results
        """
        print("\n" + "=" * 80)
        print("TEST 3: Cache Key and TTL Verification")
        print("=" * 80)
        
        expected_key = self._generate_expected_cache_key(TEST_LAT, TEST_LNG, "zone-check")
        
        print(f"\nExpected Cache Key: {expected_key}")
        print(f"Expected Format: gis_cache:{{endpoint}}:{{lat}}:{{lng}}")
        
        try:
            # Check if key exists
            key_exists = await self.redis_client.exists(expected_key)
            
            if key_exists:
                print(f"[OK] Cache key exists in Redis")
                self.cache_key = expected_key
                
                # Get TTL
                ttl = await self.redis_client.ttl(expected_key)
                self.cache_ttl = ttl
                
                print(f"[OK] Cache TTL: {ttl} seconds ({ttl / 3600:.2f} hours)")
                
                # Get cached data
                cached_data = await self.redis_client.get(expected_key)
                if cached_data:
                    print(f"[OK] Cached data retrieved successfully")
                    print(f"  Data length: {len(cached_data)} characters")
                
                # Verify TTL is reasonable (should be close to 48 hours = 172800 seconds)
                expected_ttl = 172800  # 48 hours
                if ttl > 0:
                    ttl_diff = abs(ttl - expected_ttl)
                    if ttl_diff < 3600:  # Within 1 hour of expected
                        print(f"[OK] TTL is within expected range (48 hours)")
                    else:
                        print(f"[WARN] TTL differs from expected: expected {expected_ttl}s, got {ttl}s")
                
                return {
                    "success": True,
                    "key_exists": True,
                    "key_format": expected_key,
                    "ttl_seconds": ttl,
                    "ttl_hours": ttl / 3600 if ttl > 0 else 0,
                    "cached_data_present": bool(cached_data)
                }
            else:
                print(f"[ERROR] Cache key does not exist in Redis")
                print(f"  This indicates caching may not be working")
                
                # Try to find any GIS cache keys
                all_keys = []
                async for key in self.redis_client.scan_iter(match="gis_cache:*"):
                    all_keys.append(key)
                
                if all_keys:
                    print(f"\nFound {len(all_keys)} other GIS cache keys:")
                    for key in all_keys[:5]:  # Show first 5
                        print(f"  - {key}")
                else:
                    print(f"\nNo GIS cache keys found in Redis")
                
                return {
                    "success": False,
                    "key_exists": False,
                    "expected_key": expected_key,
                    "other_keys_found": len(all_keys)
                }
                
        except Exception as e:
            print(f"[ERROR] Cache verification failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def print_summary(self):
        """Print overall summary of cache validation."""
        print("\n" + "=" * 80)
        print("CACHE VALIDATION SUMMARY")
        print("=" * 80)
        
        print("\nPerformance Comparison:")
        print(f"  First Call (Cache Miss): {self.first_call_time:.2f} ms")
        print(f"  Second Call (Cache Hit): {self.second_call_time:.2f} ms")
        
        if self.first_call_time > 0 and self.second_call_time > 0:
            speedup = self.first_call_time / self.second_call_time if self.second_call_time > 0 else 0
            print(f"  Speedup Factor: {speedup:.2f}x")
        
        print("\nCache Status:")
        if self.cache_hit_detected:
            print(f"[OK] Cache hit detected and meets threshold (< {CACHE_HIT_THRESHOLD_MS} ms)")
        else:
            print(f"[ERROR] Cache hit does not meet threshold (>= {CACHE_HIT_THRESHOLD_MS} ms)")
        
        if self.cache_key:
            print(f"[OK] Cache key format correct: {self.cache_key}")
        else:
            print(f"[ERROR] Cache key not found or incorrect format")
        
        if self.cache_ttl and self.cache_ttl > 0:
            print(f"[OK] Cache TTL configured: {self.cache_ttl} seconds ({self.cache_ttl / 3600:.2f} hours)")
        else:
            print(f"[ERROR] Cache TTL not configured or expired")
        
        print("\nOverall Assessment:")
        all_passed = (
            self.cache_hit_detected and
            self.cache_key and
            self.cache_ttl and self.cache_ttl > 0
        )
        
        if all_passed:
            print("[OK] ALL TESTS PASSED - Redis caching is working correctly")
        else:
            print("[ERROR] SOME TESTS FAILED - Redis caching needs attention")
        
        print("=" * 80)


async def main():
    """Main execution function."""
    validator = RedisCacheValidator()
    
    try:
        # Connect to Redis
        await validator.connect_redis()
        
        # Clear any existing cache for test coordinate
        await validator.clear_test_cache()
        
        # Test 1: Cache miss
        result1 = await validator.test_cache_miss()
        
        # Test 2: Cache hit
        result2 = await validator.test_cache_hit()
        
        # Test 3: Verify cache key and TTL
        result3 = await validator.verify_cache_key_and_ttl()
        
        # Print summary
        validator.print_summary()
        
        # Exit with appropriate code
        all_passed = (
            result1.get("success", False) and
            result2.get("success", False) and
            result2.get("meets_threshold", False) and
            result3.get("success", False)
        )
        
        exit(0 if all_passed else 1)
        
    except Exception as e:
        print(f"\n[ERROR] Cache validation failed: {e}")
        exit(1)
    finally:
        await validator.close_redis()


if __name__ == "__main__":
    asyncio.run(main())
