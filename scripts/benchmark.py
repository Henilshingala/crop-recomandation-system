#!/usr/bin/env python3
"""
Performance benchmarking script for Phase 10.
Measures cold start, warm inference, memory usage, and concurrent performance.
"""

import time
import psutil
import requests
import json
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import numpy as np


class PerformanceBenchmark:
    """Performance benchmarking suite."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}
    
    def measure_cold_start(self) -> Dict[str, Any]:
        """Measure cold start time for each mode."""
        print("🧊 Measuring cold start times...")
        
        # Restart service or clear caches to simulate cold start
        cold_start_times = {}
        
        for mode in ["real", "synthetic", "both"]:
            # Make request that triggers model loading
            payload = {
                "N": 50, "P": 30, "K": 40,
                "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
                "mode": mode, "top_n": 3
            }
            
            start_time = time.time()
            response = requests.post(f"{self.base_url}/predict", json=payload)
            end_time = time.time()
            
            if response.status_code == 200:
                cold_start_times[mode] = (end_time - start_time) * 1000  # ms
                print(f"  {mode}: {cold_start_times[mode]:.2f}ms")
            else:
                print(f"  {mode}: Failed with status {response.status_code}")
        
        self.results["cold_start"] = cold_start_times
        return cold_start_times
    
    def measure_warm_inference(self, num_requests: int = 50) -> Dict[str, Any]:
        """Measure warm inference latency."""
        print(f"🔥 Measuring warm inference latency ({num_requests} requests)...")
        
        warm_latencies = {}
        
        for mode in ["real", "synthetic", "both"]:
            latencies = []
            payload = {
                "N": 50, "P": 30, "K": 40,
                "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
                "mode": mode, "top_n": 3
            }
            
            # Warm up
            for _ in range(5):
                requests.post(f"{self.base_url}/predict", json=payload)
            
            # Measure requests
            for _ in range(num_requests):
                start_time = time.time()
                response = requests.post(f"{self.base_url}/predict", json=payload)
                end_time = time.time()
                
                if response.status_code == 200:
                    latencies.append((end_time - start_time) * 1000)
            
            if latencies:
                stats = {
                    "mean": statistics.mean(latencies),
                    "median": statistics.median(latencies),
                    "p95": np.percentile(latencies, 95),
                    "p99": np.percentile(latencies, 99),
                    "min": min(latencies),
                    "max": max(latencies),
                    "std": statistics.stdev(latencies) if len(latencies) > 1 else 0
                }
                warm_latencies[mode] = stats
                
                print(f"  {mode}:")
                print(f"    Mean: {stats['mean']:.2f}ms")
                print(f"    P95: {stats['p95']:.2f}ms")
                print(f"    P99: {stats['p99']:.2f}ms")
        
        self.results["warm_inference"] = warm_latencies
        return warm_latencies
    
    def measure_memory_usage(self) -> Dict[str, Any]:
        """Measure memory usage during operation."""
        print("💾 Measuring memory usage...")
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_usage = {"initial_mb": initial_memory}
        
        # Load each predictor and measure memory
        for mode in ["real", "synthetic", "both"]:
            payload = {
                "N": 50, "P": 30, "K": 40,
                "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
                "mode": mode, "top_n": 3
            }
            
            # Make request to load model
            requests.post(f"{self.base_url}/predict", json=payload)
            
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_usage[f"after_{mode}_mb"] = current_memory
        
        memory_usage["final_mb"] = process.memory_info().rss / 1024 / 1024
        memory_usage["total_increase_mb"] = memory_usage["final_mb"] - initial_memory
        
        print(f"  Initial: {initial_memory:.2f}MB")
        print(f"  Final: {memory_usage['final_mb']:.2f}MB")
        print(f"  Increase: {memory_usage['total_increase_mb']:.2f}MB")
        
        self.results["memory_usage"] = memory_usage
        return memory_usage
    
    def measure_concurrent_performance(self, concurrent_users: int = 10, requests_per_user: int = 10) -> Dict[str, Any]:
        """Measure performance under concurrent load."""
        print(f"⚡ Measuring concurrent performance ({concurrent_users} users, {requests_per_user} requests each)...")
        
        def make_request(mode: str) -> Dict[str, Any]:
            payload = {
                "N": 50, "P": 30, "K": 40,
                "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
                "mode": mode, "top_n": 3
            }
            
            start_time = time.time()
            try:
                response = requests.post(f"{self.base_url}/predict", json=payload, timeout=30)
                end_time = time.time()
                
                return {
                    "status_code": response.status_code,
                    "latency_ms": (end_time - start_time) * 1000,
                    "success": response.status_code == 200
                }
            except Exception as e:
                return {
                    "status_code": 0,
                    "latency_ms": 30000,  # timeout
                    "success": False,
                    "error": str(e)
                }
        
        concurrent_results = {}
        
        for mode in ["real", "synthetic", "both"]:
            all_results = []
            
            with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                futures = []
                
                for _ in range(concurrent_users * requests_per_user):
                    future = executor.submit(make_request, mode)
                    futures.append(future)
                
                for future in as_completed(futures):
                    result = future.result()
                    all_results.append(result)
            
            # Analyze results
            successful_results = [r for r in all_results if r["success"]]
            success_rate = len(successful_results) / len(all_results) * 100
            
            if successful_results:
                latencies = [r["latency_ms"] for r in successful_results]
                stats = {
                    "success_rate": success_rate,
                    "total_requests": len(all_results),
                    "successful_requests": len(successful_results),
                    "mean_latency_ms": statistics.mean(latencies),
                    "p95_latency_ms": np.percentile(latencies, 95),
                    "throughput_rps": len(successful_results) / (max(latencies) / 1000) if latencies else 0
                }
            else:
                stats = {
                    "success_rate": 0,
                    "total_requests": len(all_results),
                    "successful_requests": 0,
                    "mean_latency_ms": 0,
                    "p95_latency_ms": 0,
                    "throughput_rps": 0
                }
            
            concurrent_results[mode] = stats
            
            print(f"  {mode}:")
            print(f"    Success rate: {stats['success_rate']:.1f}%")
            print(f"    Mean latency: {stats['mean_latency_ms']:.2f}ms")
            print(f"    Throughput: {stats['throughput_rps']:.2f} RPS")
        
        self.results["concurrent_performance"] = concurrent_results
        return concurrent_results
    
    def stress_test(self, duration_seconds: int = 60, target_rps: int = 100) -> Dict[str, Any]:
        """Stress test with sustained load."""
        print(f"🚀 Stress testing: {target_rps} RPS for {duration_seconds}s...")
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        request_count = 0
        success_count = 0
        error_count = 0
        latencies = []
        
        def make_stress_request():
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
            with ThreadPoolExecutor(max_workers=min(target_rps, 50)) as executor:
                futures = []
                
                # Submit requests for this second
                for _ in range(target_rps):
                    if time.time() >= end_time:
                        break
                    future = executor.submit(make_stress_request)
                    futures.append(future)
                
                # Wait for this batch
                for future in as_completed(futures):
                    future.result()
            
            time.sleep(1)  # Rate limiting
        
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
                "mean_latency_ms": statistics.mean(latencies),
                "p95_latency_ms": np.percentile(latencies, 95),
                "max_latency_ms": max(latencies)
            })
        
        print(f"  Actual RPS: {actual_rps:.2f}")
        print(f"  Success rate: {stress_results['success_rate']:.1f}%")
        print(f"  Mean latency: {stress_results.get('mean_latency_ms', 0):.2f}ms")
        
        self.results["stress_test"] = stress_results
        return stress_results
    
    def generate_report(self) -> str:
        """Generate performance report."""
        report = []
        report.append("# Performance Benchmark Report\\n")
        
        if "cold_start" in self.results:
            report.append("## Cold Start Times (ms)")
            for mode, time_ms in self.results["cold_start"].items():
                report.append(f"- {mode}: {time_ms:.2f}ms")
            report.append("")
        
        if "warm_inference" in self.results:
            report.append("## Warm Inference Latency (ms)")
            for mode, stats in self.results["warm_inference"].items():
                report.append(f"### {mode}")
                report.append(f"- Mean: {stats['mean']:.2f}ms")
                report.append(f"- P95: {stats['p95']:.2f}ms")
                report.append(f"- P99: {stats['p99']:.2f}ms")
                report.append("")
        
        if "memory_usage" in self.results:
            mem = self.results["memory_usage"]
            report.append("## Memory Usage (MB)")
            report.append(f"- Initial: {mem['initial_mb']:.2f}MB")
            report.append(f"- Final: {mem['final_mb']:.2f}MB")
            report.append(f"- Increase: {mem['total_increase_mb']:.2f}MB")
            report.append("")
        
        if "concurrent_performance" in self.results:
            report.append("## Concurrent Performance")
            for mode, stats in self.results["concurrent_performance"].items():
                report.append(f"### {mode}")
                report.append(f"- Success rate: {stats['success_rate']:.1f}%")
                report.append(f"- Mean latency: {stats['mean_latency_ms']:.2f}ms")
                report.append(f"- Throughput: {stats['throughput_rps']:.2f} RPS")
                report.append("")
        
        if "stress_test" in self.results:
            stress = self.results["stress_test"]
            report.append("## Stress Test")
            report.append(f"- Target RPS: {stress['target_rps']}")
            report.append(f"- Actual RPS: {stress['actual_rps']:.2f}")
            report.append(f"- Success rate: {stress['success_rate']:.1f}%")
            report.append(f"- Duration: {stress['duration_seconds']:.1f}s")
            report.append("")
        
        return "\\n".join(report)
    
    def save_results(self, filename: str = "benchmark_results.json"):
        """Save benchmark results to JSON file."""
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"📄 Results saved to {filename}")


def main():
    """Run full performance benchmark."""
    benchmark = PerformanceBenchmark()
    
    print("🚀 Starting performance benchmark...")
    print()
    
    # Run all benchmarks
    benchmark.measure_cold_start()
    print()
    
    benchmark.measure_warm_inference()
    print()
    
    benchmark.measure_memory_usage()
    print()
    
    benchmark.measure_concurrent_performance()
    print()
    
    benchmark.stress_test()
    print()
    
    # Generate and save report
    report = benchmark.generate_report()
    print(report)
    
    benchmark.save_results()
    
    print("✅ Performance benchmark complete!")


if __name__ == "__main__":
    main()
