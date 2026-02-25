#!/usr/bin/env python3
"""
Staging performance validation script.
Tests cold start, warm inference, stress testing, and memory usage.
"""

import time
import requests
import json
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

class StagingPerformanceTest:
    """Performance testing for staging environment."""
    
    def __init__(self, base_url: str = "http://localhost:7860"):
        self.base_url = base_url
        self.results = {}
    
    def test_health_endpoint(self) -> bool:
        """Test health endpoint."""
        print("Testing health endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"Health status: {data.get('status')}")
                print(f"Models available: {list(data.get('models', {}).keys())}")
                return True
            else:
                print(f"Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"Health check error: {e}")
            return False
    
    def measure_cold_start(self) -> Dict[str, float]:
        """Measure cold start time for each mode."""
        print("Measuring cold start times...")
        
        cold_starts = {}
        
        for mode in ["real", "synthetic", "both"]:
            payload = {
                "N": 50, "P": 30, "K": 40,
                "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
                "mode": mode, "top_n": 3
            }
            
            start_time = time.time()
            try:
                response = requests.post(f"{self.base_url}/predict", json=payload, timeout=30)
                end_time = time.time()
                
                if response.status_code == 200:
                    cold_starts[mode] = (end_time - start_time) * 1000
                    print(f"  {mode}: {cold_starts[mode]:.2f}ms")
                else:
                    print(f"  {mode}: Failed with status {response.status_code}")
                    cold_starts[mode] = -1
            except Exception as e:
                print(f"  {mode}: Error - {e}")
                cold_starts[mode] = -1
        
        self.results["cold_start"] = cold_starts
        return cold_starts
    
    def measure_warm_inference(self, num_requests: int = 20) -> Dict[str, Dict[str, float]]:
        """Measure warm inference latency."""
        print(f"Measuring warm inference latency ({num_requests} requests)...")
        
        warm_latency = {}
        
        for mode in ["real", "synthetic", "both"]:
            payload = {
                "N": 50, "P": 30, "K": 40,
                "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
                "mode": mode, "top_n": 3
            }
            
            latencies = []
            
            # Warm up
            for _ in range(3):
                try:
                    requests.post(f"{self.base_url}/predict", json=payload, timeout=10)
                except:
                    pass
            
            # Measure requests
            for _ in range(num_requests):
                start_time = time.time()
                try:
                    response = requests.post(f"{self.base_url}/predict", json=payload, timeout=10)
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        latencies.append((end_time - start_time) * 1000)
                except Exception as e:
                    print(f"  Request failed: {e}")
            
            if latencies:
                stats = {
                    "p50": statistics.median(latencies),
                    "p95": sorted(latencies)[int(len(latencies) * 0.95)],
                    "p99": sorted(latencies)[int(len(latencies) * 0.99)],
                    "mean": statistics.mean(latencies),
                    "min": min(latencies),
                    "max": max(latencies)
                }
                warm_latency[mode] = stats
                
                print(f"  {mode}:")
                print(f"    P50: {stats['p50']:.2f}ms")
                print(f"    P95: {stats['p95']:.2f}ms")
                print(f"    P99: {stats['p99']:.2f}ms")
            else:
                print(f"  {mode}: No successful requests")
                warm_latency[mode] = {}
        
        self.results["warm_inference"] = warm_latency
        return warm_latency
    
    def stress_test(self, duration_seconds: int = 60, target_rps: int = 100) -> Dict[str, Any]:
        """Stress test with sustained load."""
        print(f"Stress testing: {target_rps} RPS for {duration_seconds}s...")
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        request_count = 0
        success_count = 0
        error_count = 0
        latencies = []
        
        def make_request():
            nonlocal request_count, success_count, error_count
            
            payload = {
                "N": 50, "P": 30, "K": 40,
                "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
                "mode": "real", "top_n": 3
            }
            
            req_start = time.time()
            try:
                response = requests.post(f"{self.base_url}/predict", json=payload, timeout=10)
                req_end = time.time()
                
                request_count += 1
                if response.status_code == 200:
                    success_count += 1
                    latencies.append((req_end - req_start) * 1000)
                else:
                    error_count += 1
                    
            except Exception:
                request_count += 1
                error_count += 1
        
        # Generate requests at target RPS
        while time.time() < end_time:
            batch_start = time.time()
            
            with ThreadPoolExecutor(max_workers=min(target_rps, 50)) as executor:
                futures = []
                requests_in_second = min(target_rps, 20)  # Limit concurrent requests
                
                for _ in range(requests_in_second):
                    if time.time() >= end_time:
                        break
                    future = executor.submit(make_request)
                    futures.append(future)
                
                for future in as_completed(futures):
                    future.result()
            
            # Rate limiting
            elapsed = time.time() - batch_start
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
        
        actual_duration = time.time() - start_time
        actual_rps = request_count / actual_duration
        
        stress_results = {
            "duration_seconds": actual_duration,
            "target_rps": target_rps,
            "actual_rps": actual_rps,
            "total_requests": request_count,
            "successful_requests": success_count,
            "failed_requests": error_count,
            "success_rate": (success_count / request_count * 100) if request_count > 0 else 0,
        }
        
        if latencies:
            stress_results.update({
                "p50_latency_ms": statistics.median(latencies),
                "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)],
                "max_latency_ms": max(latencies)
            })
        
        print(f"  Actual RPS: {actual_rps:.2f}")
        print(f"  Success rate: {stress_results['success_rate']:.1f}%")
        print(f"  P95 latency: {stress_results.get('p95_latency_ms', 0):.2f}ms")
        
        self.results["stress_test"] = stress_results
        return stress_results
    
    def test_memory_usage(self) -> Dict[str, Any]:
        """Test memory usage via health endpoint."""
        print("Testing memory usage...")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                memory_usage = data.get("memory_usage", {})
                
                print(f"  Real predictor loaded: {memory_usage.get('real_predictor_loaded', 'unknown')}")
                print(f"  Synthetic predictor loaded: {memory_usage.get('synthetic_predictor_loaded', 'unknown')}")
                print(f"  Both predictor loaded: {memory_usage.get('both_predictor_loaded', 'unknown')}")
                
                self.results["memory_usage"] = memory_usage
                return memory_usage
            else:
                print(f"  Failed to get memory usage: {response.status_code}")
                return {}
        except Exception as e:
            print(f"  Memory usage test error: {e}")
            return {}
    
    def test_rate_limiting(self) -> bool:
        """Test rate limiting is working."""
        print("Testing rate limiting...")
        
        payload = {
            "N": 50, "P": 30, "K": 40,
            "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
            "mode": "real", "top_n": 3
        }
        
        # Send rapid requests
        rate_limited = False
        for i in range(30):  # Send 30 requests rapidly
            response = requests.post(f"{self.base_url}/predict", json=payload, timeout=5)
            if response.status_code == 429:
                rate_limited = True
                print(f"  Rate limiting triggered after {i+1} requests")
                break
        
        if not rate_limited:
            print("  Rate limiting not triggered (may not be configured)")
        
        return rate_limited
    
    def generate_report(self) -> str:
        """Generate performance test report."""
        report = []
        report.append("# Staging Performance Test Report\\n")
        
        if "cold_start" in self.results:
            report.append("## Cold Start Times (ms)")
            for mode, time_ms in self.results["cold_start"].items():
                if time_ms > 0:
                    report.append(f"- {mode}: {time_ms:.2f}ms")
                else:
                    report.append(f"- {mode}: FAILED")
            report.append("")
        
        if "warm_inference" in self.results:
            report.append("## Warm Inference Latency (ms)")
            for mode, stats in self.results["warm_inference"].items():
                if stats:
                    report.append(f"### {mode}")
                    report.append(f"- P50: {stats['p50']:.2f}ms")
                    report.append(f"- P95: {stats['p95']:.2f}ms")
                    report.append(f"- P99: {stats['p99']:.2f}ms")
            report.append("")
        
        if "stress_test" in self.results:
            stress = self.results["stress_test"]
            report.append("## Stress Test Results")
            report.append(f"- Target RPS: {stress['target_rps']}")
            report.append(f"- Actual RPS: {stress['actual_rps']:.2f}")
            report.append(f"- Success Rate: {stress['success_rate']:.1f}%")
            report.append(f"- Duration: {stress['duration_seconds']:.1f}s")
            if "p95_latency_ms" in stress:
                report.append(f"- P95 Latency: {stress['p95_latency_ms']:.2f}ms")
            report.append("")
        
        return "\\n".join(report)
    
    def save_results(self, filename: str = "staging_performance_results.json"):
        """Save test results to JSON file."""
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"Results saved to {filename}")


def main():
    """Run staging performance tests."""
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:7860"
    
    tester = StagingPerformanceTest(base_url)
    
    print("Starting staging performance validation...")
    print("=" * 60)
    
    # Health check first
    if not tester.test_health_endpoint():
        print("FAILED: Health check failed. Cannot continue.")
        return 1
    
    print()
    
    # Run performance tests
    tester.measure_cold_start()
    print()
    
    tester.measure_warm_inference()
    print()
    
    tester.test_memory_usage()
    print()
    
    tester.stress_test(duration_seconds=30, target_rps=50)  # Shorter test for staging
    print()
    
    tester.test_rate_limiting()
    print()
    
    # Generate report
    report = tester.generate_report()
    print(report)
    
    tester.save_results()
    
    print("=" * 60)
    print("Staging performance validation complete!")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
