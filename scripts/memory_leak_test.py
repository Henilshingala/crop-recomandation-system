#!/usr/bin/env python3
"""
Memory leak detection script for Phase 10.
Tests for memory leaks in predictor loading and sustained usage.
"""

import time
import psutil
import requests
import gc
import threading
from typing import List, Dict, Any
import matplotlib.pyplot as plt


class MemoryLeakDetector:
    """Memory leak detection and monitoring."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.process = psutil.Process()
        self.memory_snapshots = []
    
    def take_memory_snapshot(self, label: str) -> Dict[str, Any]:
        """Take a memory snapshot with label."""
        memory_info = self.process.memory_info()
        memory_percent = self.process.memory_percent()
        
        snapshot = {
            "label": label,
            "timestamp": time.time(),
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": memory_percent,
            "available_mb": psutil.virtual_memory().available / 1024 / 1024
        }
        
        self.memory_snapshots.append(snapshot)
        return snapshot
    
    def test_predictor_loading_leaks(self, iterations: int = 20) -> Dict[str, Any]:
        """Test for memory leaks during predictor loading."""
        print("🔍 Testing predictor loading for memory leaks...")
        
        # Baseline memory
        baseline = self.take_memory_snapshot("baseline")
        
        loading_memory = []
        
        for i in range(iterations):
            # Test each mode
            for mode in ["real", "synthetic", "both"]:
                payload = {
                    "N": 50, "P": 30, "K": 40,
                    "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
                    "mode": mode, "top_n": 3
                }
                
                # Make request to trigger loading
                response = requests.post(f"{self.base_url}/predict", json=payload)
                
                # Take memory snapshot
                snapshot = self.take_memory_snapshot(f"load_{mode}_iter_{i}")
                loading_memory.append(snapshot)
            
            # Force garbage collection
            gc.collect()
            
            if (i + 1) % 5 == 0:
                print(f"  Completed {i + 1}/{iterations} iterations")
        
        # Analyze memory growth
        memory_growth = self._analyze_memory_growth(loading_memory, "predictor_loading")
        
        return {
            "baseline": baseline,
            "iterations": iterations,
            "memory_growth": memory_growth,
            "final_snapshot": self.memory_snapshots[-1]
        }
    
    def test_sustained_usage_leaks(self, duration_minutes: int = 10, requests_per_minute: int = 60) -> Dict[str, Any]:
        """Test for memory leaks during sustained usage."""
        print(f"⏱️  Testing sustained usage for {duration_minutes} minutes...")
        
        # Baseline
        baseline = self.take_memory_snapshot("sustained_baseline")
        
        sustained_memory = []
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        request_interval = 60.0 / requests_per_minute
        
        request_count = 0
        
        while time.time() < end_time:
            # Make request
            payload = {
                "N": 50, "P": 30, "K": 40,
                "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
                "mode": "real", "top_n": 3
            }
            
            try:
                response = requests.post(f"{self.base_url}/predict", json=payload, timeout=30)
                request_count += 1
            except Exception as e:
                print(f"Request failed: {e}")
            
            # Take memory snapshot every 30 seconds
            if int(time.time() - start_time) % 30 == 0:
                snapshot = self.take_memory_snapshot(f"sustained_{int(time.time() - start_time)}s")
                sustained_memory.append(snapshot)
            
            # Rate limiting
            time.sleep(request_interval)
        
        # Final snapshot
        final_snapshot = self.take_memory_snapshot("sustained_final")
        
        # Analyze memory growth
        memory_growth = self._analyze_memory_growth(sustained_memory, "sustained_usage")
        
        print(f"  Completed {request_count} requests")
        
        return {
            "baseline": baseline,
            "duration_minutes": duration_minutes,
            "requests_per_minute": requests_per_minute,
            "total_requests": request_count,
            "memory_growth": memory_growth,
            "final_snapshot": final_snapshot
        }
    
    def test_concurrent_leaks(self, concurrent_threads: int = 5, duration_seconds: int = 60) -> Dict[str, Any]:
        """Test for memory leaks under concurrent load."""
        print(f"🔄 Testing concurrent memory usage ({concurrent_threads} threads, {duration_seconds}s)...")
        
        baseline = self.take_memory_snapshot("concurrent_baseline")
        
        concurrent_memory = []
        request_count = 0
        error_count = 0
        
        def worker_thread(thread_id: int):
            nonlocal request_count, error_count
            
            end_time = time.time() + duration_seconds
            
            while time.time() < end_time:
                payload = {
                    "N": 50, "P": 30, "K": 40,
                    "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
                    "mode": "real", "top_n": 3
                }
                
                try:
                    response = requests.post(f"{self.base_url}/predict", json=payload, timeout=10)
                    if response.status_code == 200:
                        request_count += 1
                    else:
                        error_count += 1
                except Exception:
                    error_count += 1
                
                time.sleep(0.1)  # Small delay between requests
        
        # Start threads
        threads = []
        for i in range(concurrent_threads):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Monitor memory during test
        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            time.sleep(5)
            snapshot = self.take_memory_snapshot(f"concurrent_{int(time.time() - start_time)}s")
            concurrent_memory.append(snapshot)
        
        # Wait for threads to finish
        for thread in threads:
            thread.join()
        
        # Final snapshot
        final_snapshot = self.take_memory_snapshot("concurrent_final")
        
        # Analyze memory growth
        memory_growth = self._analyze_memory_growth(concurrent_memory, "concurrent")
        
        print(f"  Completed {request_count} successful requests")
        print(f"  {error_count} errors")
        
        return {
            "baseline": baseline,
            "concurrent_threads": concurrent_threads,
            "duration_seconds": duration_seconds,
            "successful_requests": request_count,
            "error_count": error_count,
            "memory_growth": memory_growth,
            "final_snapshot": final_snapshot
        }
    
    def _analyze_memory_growth(self, snapshots: List[Dict[str, Any]], test_name: str) -> Dict[str, Any]:
        """Analyze memory growth from snapshots."""
        if len(snapshots) < 2:
            return {"error": "Insufficient snapshots for analysis"}
        
        memory_values = [s["rss_mb"] for s in snapshots]
        time_values = [s["timestamp"] for s in snapshots]
        
        # Calculate growth metrics
        initial_memory = memory_values[0]
        final_memory = memory_values[-1]
        total_growth = final_memory - initial_memory
        max_memory = max(memory_values)
        
        # Calculate growth rate (MB per minute)
        duration_minutes = (time_values[-1] - time_values[0]) / 60
        growth_rate = total_growth / duration_minutes if duration_minutes > 0 else 0
        
        # Detect potential leak (growth > 10MB per hour)
        potential_leak = growth_rate > 10/60  # 10MB per hour threshold
        
        return {
            "test_name": test_name,
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "total_growth_mb": total_growth,
            "max_memory_mb": max_memory,
            "growth_rate_mb_per_minute": growth_rate,
            "duration_minutes": duration_minutes,
            "potential_leak": potential_leak,
            "snapshots_count": len(snapshots)
        }
    
    def generate_memory_report(self) -> str:
        """Generate memory leak detection report."""
        report = []
        report.append("# Memory Leak Detection Report\\n")
        
        for snapshot in self.memory_snapshots:
            report.append(f"## {snapshot['label']}")
            report.append(f"- RSS: {snapshot['rss_mb']:.2f}MB")
            report.append(f"- Memory %: {snapshot['percent']:.2f}%")
            report.append(f"- Available: {snapshot['available_mb']:.2f}MB")
            report.append("")
        
        return "\\n".join(report)
    
    def plot_memory_timeline(self, filename: str = "memory_timeline.png"):
        """Plot memory usage timeline."""
        if len(self.memory_snapshots) < 2:
            print("Insufficient data for plotting")
            return
        
        timestamps = [s["timestamp"] for s in self.memory_snapshots]
        rss_memory = [s["rss_mb"] for s in self.memory_snapshots]
        labels = [s["label"] for s in self.memory_snapshots]
        
        plt.figure(figsize=(12, 6))
        plt.plot(timestamps, rss_memory, 'b-', linewidth=2)
        plt.xlabel('Time')
        plt.ylabel('RSS Memory (MB)')
        plt.title('Memory Usage Timeline')
        plt.grid(True, alpha=0.3)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)
        
        # Add annotations for key points
        for i, (ts, mem, label) in enumerate(zip(timestamps, rss_memory, labels)):
            if i % max(1, len(timestamps) // 10) == 0:  # Show every 10th label
                plt.annotate(label, (ts, mem), xytext=(5, 5), 
                           textcoords='offset points', fontsize=8, alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"📊 Memory timeline plot saved to {filename}")
    
    def save_results(self, filename: str = "memory_leak_results.json"):
        """Save memory leak test results."""
        import json
        
        results = {
            "test_timestamp": time.time(),
            "memory_snapshots": self.memory_snapshots
        }
        
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"📄 Memory leak results saved to {filename}")


def main():
    """Run memory leak detection tests."""
    detector = MemoryLeakDetector()
    
    print("🔍 Starting memory leak detection...")
    print()
    
    # Test 1: Predictor loading leaks
    loading_results = detector.test_predictor_loading_leaks(iterations=10)
    print(f"  Loading test growth: {loading_results['memory_growth']['total_growth_mb']:.2f}MB")
    print()
    
    # Test 2: Sustained usage leaks
    sustained_results = detector.test_sustained_usage_leaks(duration_minutes=5, requests_per_minute=30)
    print(f"  Sustained test growth: {sustained_results['memory_growth']['total_growth_mb']:.2f}MB")
    print()
    
    # Test 3: Concurrent leaks
    concurrent_results = detector.test_concurrent_leaks(concurrent_threads=3, duration_seconds=30)
    print(f"  Concurrent test growth: {concurrent_results['memory_growth']['total_growth_mb']:.2f}MB")
    print()
    
    # Generate report and plots
    print(detector.generate_memory_report())
    detector.plot_memory_timeline()
    detector.save_results()
    
    # Summary
    print("📊 Memory Leak Detection Summary:")
    print(f"  Predictor loading: {'⚠️  Potential leak' if loading_results['memory_growth']['potential_leak'] else '✅ OK'}")
    print(f"  Sustained usage: {'⚠️  Potential leak' if sustained_results['memory_growth']['potential_leak'] else '✅ OK'}")
    print(f"  Concurrent usage: {'⚠️  Potential leak' if concurrent_results['memory_growth']['potential_leak'] else '✅ OK'}")
    
    print("✅ Memory leak detection complete!")


if __name__ == "__main__":
    main()
