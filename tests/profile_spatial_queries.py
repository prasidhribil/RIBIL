#!/usr/bin/env python3
"""
 ============================================================================
 Database Performance Profiling Script - PostGIS Spatial Queries
 ============================================================================
 Description: Analyzes spatial query execution plans and benchmarks performance
 Validates GIST spatial index usage and measures query latency
 Target: Sub-200ms execution time for spatial queries

 Run Instructions:
   python tests/profile_spatial_queries.py
   OR
   python -m pytest tests/profile_spatial_queries.py -v -s
 ============================================================================
"""

import asyncio
import asyncpg
import time
import statistics
from typing import List, Dict, Any, Tuple
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "gis_engine"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "")
}

# Performance threshold (milliseconds)
PERFORMANCE_THRESHOLD_MS = 200

# Mock test coordinates for Bengaluru
TEST_COORDINATES = [
    (12.9716, 77.5946),  # Central Bengaluru
    (12.9814, 77.6225),  # Ulsoor Lake area
    (13.0105, 77.5750),  # Sankey Tank area
    (12.9739, 77.5913),  # Cubbon Park
    (12.8449, 77.6631),  # Electronic City
    (12.9796, 77.5906),  # Vidhana Soudha
    (12.9842, 77.7479),  # Whitefield
    (13.2008, 77.7088),  # BIAL Airport
    (12.9350, 77.5800),  # Jayanagar
    (13.0500, 77.5500),  # Bengaluru North
]


class SpatialQueryProfiler:
    """Profiler for PostGIS spatial query performance."""
    
    def __init__(self):
        self.conn = None
        self.execution_times: List[float] = []
        self.index_usage_detected = False
        self.seq_scan_detected = False
    
    async def connect(self):
        """Establish database connection."""
        try:
            self.conn = await asyncpg.connect(**DB_CONFIG)
            print("[OK] Database connection established")
        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            raise
    
    async def close(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()
            print("[OK] Database connection closed")
    
    async def analyze_execution_plan(self) -> Dict[str, Any]:
        """
        Run EXPLAIN ANALYZE on point-in-polygon query and parse execution plan.
        
        Returns:
            Dictionary with execution plan analysis results
        """
        print("\n" + "=" * 80)
        print("EXECUTION PLAN ANALYSIS")
        print("=" * 80)
        
        # Use a test coordinate
        lat, lng = TEST_COORDINATES[0]
        
        explain_query = """
            EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
            SELECT 
                survey_no,
                village,
                hobli,
                district,
                area_acres
            FROM survey_parcels
            WHERE ST_Contains(
                geom,
                ST_SetSRID(ST_Point($1, $2), 4326)
            )
            LIMIT 1
        """
        
        try:
            result = await self.conn.fetch(explain_query, lng, lat)
            
            # Combine all lines into a single string
            plan_text = "\n".join(row["QUERY PLAN"] for row in result)
            
            print(f"\nTest Coordinates: ({lat}, {lng})")
            print("\nExecution Plan:")
            print("-" * 80)
            print(plan_text)
            print("-" * 80)
            
            # Parse execution plan for index usage
            analysis = self._parse_execution_plan(plan_text)
            
            return analysis
            
        except Exception as e:
            print(f"[ERROR] Execution plan analysis failed: {e}")
            return {"error": str(e)}
    
    def _parse_execution_plan(self, plan_text: str) -> Dict[str, Any]:
        """
        Parse execution plan text for index usage indicators.
        
        Args:
            plan_text: Execution plan output from EXPLAIN ANALYZE
            
        Returns:
            Dictionary with analysis results
        """
        plan_lower = plan_text.lower()
        
        # Check for GIST index usage
        index_scan_detected = "index scan" in plan_lower and "geom" in plan_lower
        bitmap_scan_detected = "bitmap heap scan" in plan_lower
        
        # Check for sequential scan (bad performance indicator)
        seq_scan_detected = "seq scan" in plan_lower
        
        # Extract execution time
        execution_time = self._extract_execution_time(plan_text)
        
        analysis = {
            "index_scan_detected": index_scan_detected,
            "bitmap_scan_detected": bitmap_scan_detected,
            "seq_scan_detected": seq_scan_detected,
            "execution_time_ms": execution_time,
            "index_usage_ok": index_scan_detected or bitmap_scan_detected,
            "performance_warning": seq_scan_detected
        }
        
        # Print analysis results
        print("\nExecution Plan Analysis:")
        print("-" * 80)
        
        if index_scan_detected:
            print("[OK] Index Scan detected: GIST spatial index is being used")
            self.index_usage_detected = True
        elif bitmap_scan_detected:
            print("[OK] Bitmap Heap Scan detected: GIST spatial index is being used")
            self.index_usage_detected = True
        else:
            print("[WARN] No spatial index scan detected")
        
        if seq_scan_detected:
            print("[WARN] WARNING: Sequential Scan detected!")
            print("  This indicates the GIST spatial index may not be active or optimal")
            print("  Expected: Index Scan using survey_parcels_geom_idx")
            self.seq_scan_detected = True
        else:
            print("[OK] No Sequential Scan detected (good)")
        
        print(f"\nExecution Time: {execution_time:.2f} ms")
        print("-" * 80)
        
        return analysis
    
    def _extract_execution_time(self, plan_text: str) -> float:
        """
        Extract execution time from execution plan text.
        
        Args:
            plan_text: Execution plan output
            
        Returns:
            Execution time in milliseconds
        """
        # Look for "Execution Time: X.XX ms" pattern
        import re
        match = re.search(r"Execution Time: ([\d.]+) ms", plan_text)
        if match:
            return float(match.group(1))
        
        # Fallback: look for "total runtime" pattern
        match = re.search(r"total runtime: ([\d.]+) ms", plan_text)
        if match:
            return float(match.group(1))
        
        return 0.0
    
    async def benchmark_spatial_queries(self, num_queries: int = 100) -> Dict[str, Any]:
        """
        Benchmark 100 concurrent spatial point queries.
        
        Args:
            num_queries: Number of queries to run
            
        Returns:
            Dictionary with benchmark results
        """
        print("\n" + "=" * 80)
        print(f"SPATIAL QUERY BENCHMARK - {num_queries} Concurrent Queries")
        print("=" * 80)
        
        query = """
            SELECT 
                survey_no,
                village,
                hobli,
                district,
                area_acres
            FROM survey_parcels
            WHERE ST_Contains(
                geom,
                ST_SetSRID(ST_Point($1, $2), 4326)
            )
            LIMIT 1
        """
        
        execution_times = []
        
        print(f"\nRunning {num_queries} spatial queries...")
        print("This may take a moment...")
        
        start_time = time.time()
        
        for i in range(num_queries):
            # Use different coordinates for each query
            coord_index = i % len(TEST_COORDINATES)
            lat, lng = TEST_COORDINATES[coord_index]
            
            query_start = time.time()
            
            try:
                await self.conn.fetch(query, lng, lat)
                query_end = time.time()
                execution_time_ms = (query_end - query_start) * 1000
                execution_times.append(execution_time_ms)
                
                # Progress indicator
                if (i + 1) % 20 == 0:
                    print(f"  Progress: {i + 1}/{num_queries} queries completed")
                    
            except Exception as e:
                print(f"[ERROR] Query {i + 1} failed: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        self.execution_times = execution_times
        
        # Calculate statistics
        if execution_times:
            avg_latency = statistics.mean(execution_times)
            median_latency = statistics.median(execution_times)
            min_latency = min(execution_times)
            max_latency = max(execution_times)
            p95_latency = statistics.quantiles(execution_times, n=20)[18] if len(execution_times) >= 20 else max_latency
        else:
            avg_latency = median_latency = min_latency = max_latency = p95_latency = 0
        
        results = {
            "num_queries": num_queries,
            "successful_queries": len(execution_times),
            "total_time_seconds": total_time,
            "avg_latency_ms": avg_latency,
            "median_latency_ms": median_latency,
            "min_latency_ms": min_latency,
            "max_latency_ms": max_latency,
            "p95_latency_ms": p95_latency,
            "queries_per_second": num_queries / total_time if total_time > 0 else 0
        }
        
        # Print benchmark results
        print("\nBenchmark Results:")
        print("-" * 80)
        print(f"Total Queries: {num_queries}")
        print(f"Successful: {len(execution_times)}")
        print(f"Total Time: {total_time:.2f} seconds")
        print(f"Queries/Second: {results['queries_per_second']:.2f}")
        print()
        print(f"Average Latency: {avg_latency:.2f} ms")
        print(f"Median Latency: {median_latency:.2f} ms")
        print(f"Min Latency: {min_latency:.2f} ms")
        print(f"Max Latency: {max_latency:.2f} ms")
        print(f"P95 Latency: {p95_latency:.2f} ms")
        print("-" * 80)
        
        # Performance threshold check
        if avg_latency < PERFORMANCE_THRESHOLD_MS:
            print(f"[OK] PERFORMANCE OK: Average latency ({avg_latency:.2f} ms) < threshold ({PERFORMANCE_THRESHOLD_MS} ms)")
        else:
            print(f"[WARN] PERFORMANCE WARNING: Average latency ({avg_latency:.2f} ms) >= threshold ({PERFORMANCE_THRESHOLD_MS} ms)")
        
        print("=" * 80)
        
        return results
    
    def print_summary(self):
        """Print overall summary of profiling results."""
        print("\n" + "=" * 80)
        print("PROFILING SUMMARY")
        print("=" * 80)
        
        print("\nIndex Usage:")
        if self.index_usage_detected:
            print("[OK] GIST spatial index is active and being used")
        else:
            print("[WARN] GIST spatial index may not be active")
        
        if self.seq_scan_detected:
            print("[WARN] WARNING: Sequential scan detected - performance may be degraded")
        
        print("\nPerformance:")
        if self.execution_times:
            avg_latency = statistics.mean(self.execution_times)
            if avg_latency < PERFORMANCE_THRESHOLD_MS:
                print(f"[OK] Average latency ({avg_latency:.2f} ms) meets threshold ({PERFORMANCE_THRESHOLD_MS} ms)")
            else:
                print(f"[WARN] Average latency ({avg_latency:.2f} ms) exceeds threshold ({PERFORMANCE_THRESHOLD_MS} ms)")
        else:
            print("[WARN] No benchmark data available")
        
        print("\nRecommendations:")
        if self.seq_scan_detected:
            print("- Verify GIST index exists on survey_parcels.geom")
            print("- Run ANALYZE on survey_parcels table to update statistics")
            print("- Check if query planner is choosing the right index")
        
        if self.execution_times and statistics.mean(self.execution_times) >= PERFORMANCE_THRESHOLD_MS:
            print("- Consider increasing connection pool size")
            print("- Review database server resources")
            print("- Optimize spatial query parameters")
        
        print("=" * 80)


async def main():
    """Main execution function."""
    profiler = SpatialQueryProfiler()
    
    try:
        # Connect to database
        await profiler.connect()
        
        # Analyze execution plan
        await profiler.analyze_execution_plan()
        
        # Benchmark spatial queries
        await profiler.benchmark_spatial_queries(num_queries=100)
        
        # Print summary
        profiler.print_summary()
        
        # Exit with appropriate code
        if profiler.seq_scan_detected or (profiler.execution_times and statistics.mean(profiler.execution_times) >= PERFORMANCE_THRESHOLD_MS):
            exit(1)  # Exit with error if performance issues detected
        else:
            exit(0)  # Exit successfully
            
    except Exception as e:
        print(f"\n[ERROR] Profiling failed: {e}")
        exit(1)
    finally:
        await profiler.close()


if __name__ == "__main__":
    asyncio.run(main())
