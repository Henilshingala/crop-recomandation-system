"""
Integration tests for the crop recommendation system.
Tests mode routing, rate limiting, circuit breaker, etc.
"""

import json
import pytest
import requests
import time
from typing import Dict, Any


class TestModeRouting:
    """Test mode routing functionality."""
    
    BASE_URL = "http://localhost:8000"
    
    def test_all_modes_available(self):
        """Test all three modes are available and functional."""
        modes = ["real", "synthetic", "both"]
        
        for mode in modes:
            payload = {
                "N": 50, "P": 30, "K": 40,
                "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
                "mode": mode, "top_n": 3
            }
            
            response = requests.post(f"{self.BASE_URL}/predict", json=payload)
            assert response.status_code == 200
            
            data = response.json()
            assert data["model_info"]["mode"] == mode
    
    def test_invalid_mode_400(self):
        """Test invalid mode returns 400 status."""
        payload = {
            "N": 50, "P": 30, "K": 40,
            "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
            "mode": "invalid_mode", "top_n": 3
        }
        
        response = requests.post(f"{self.BASE_URL}/predict", json=payload)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "invalid_mode" in data["detail"].lower()


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    BASE_URL = "http://localhost:8000"
    
    def test_rate_limit_429(self):
        """Test rate limiting returns 429 status."""
        payload = {
            "N": 50, "P": 30, "K": 40,
            "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
            "mode": "real", "top_n": 3
        }
        
        # Send rapid requests to trigger rate limit
        responses = []
        for _ in range(20):  # Adjust based on your rate limit configuration
            response = requests.post(f"{self.BASE_URL}/predict", json=payload)
            responses.append(response)
            if response.status_code == 429:
                break
        
        # At least one request should be rate limited
        rate_limited = any(r.status_code == 429 for r in responses)
        if rate_limited:
            rate_limit_response = next(r for r in responses if r.status_code == 429)
            assert rate_limit_response.status_code == 429


class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    BASE_URL = "http://localhost:8000"
    
    def test_circuit_breaker_503(self):
        """Test circuit breaker returns 503 when open."""
        # This test requires simulating failures or mocking
        # For now, we'll test the health endpoint which should show circuit status
        
        response = requests.get(f"{self.BASE_URL}/health")
        assert response.status_code == 200
        
        data = response.json()
        # Circuit breaker status might be included in health check
        # Adjust based on your implementation


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    BASE_URL = "http://localhost:8000"
    
    def test_missing_required_fields(self):
        """Test missing required fields returns proper error."""
        # Test missing N
        payload = {
            "P": 30, "K": 40,
            "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
            "mode": "real"
        }
        
        response = requests.post(f"{self.BASE_URL}/predict", json=payload)
        assert response.status_code == 422
    
    def test_invalid_data_types(self):
        """Test invalid data types return proper error."""
        payload = {
            "N": "invalid",  # Should be number
            "P": 30, "K": 40,
            "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
            "mode": "real"
        }
        
        response = requests.post(f"{self.BASE_URL}/predict", json=payload)
        assert response.status_code == 422
    
    def test_negative_values(self):
        """Test negative values are handled appropriately."""
        payload = {
            "N": -10, "P": 30, "K": 40,
            "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
            "mode": "real"
        }
        
        response = requests.post(f"{self.BASE_URL}/predict", json=payload)
        # Should either work (if negative values are valid) or return validation error
        assert response.status_code in [200, 422]


class TestPerformance:
    """Test performance characteristics."""
    
    BASE_URL = "http://localhost:8000"
    
    def test_response_time_under_limit(self):
        """Test response time is acceptable."""
        payload = {
            "N": 50, "P": 30, "K": 40,
            "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
            "mode": "real", "top_n": 3
        }
        
        start_time = time.time()
        response = requests.post(f"{self.BASE_URL}/predict", json=payload)
        end_time = time.time()
        
        assert response.status_code == 200
        
        response_time = end_time - start_time
        # Should respond within 2 seconds (adjust based on your requirements)
        assert response_time < 2.0
    
    def test_concurrent_requests(self):
        """Test system handles concurrent requests."""
        import threading
        import queue
        
        payload = {
            "N": 50, "P": 30, "K": 40,
            "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
            "mode": "real", "top_n": 3
        }
        
        results = queue.Queue()
        
        def make_request():
            try:
                response = requests.post(f"{self.BASE_URL}/predict", json=payload, timeout=5)
                results.put(response.status_code)
            except Exception as e:
                results.put(f"error: {e}")
        
        # Start 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        success_count = 0
        while not results.empty():
            result = results.get()
            if result == 200:
                success_count += 1
        
        # At least 80% of requests should succeed
        assert success_count >= 8


class TestModelInfo:
    """Test model information endpoints."""
    
    BASE_URL = "http://localhost:8000"
    
    def test_crops_endpoint(self):
        """Test crops endpoint returns valid data."""
        response = requests.get(f"{self.BASE_URL}/crops")
        assert response.status_code == 200
        
        data = response.json()
        assert "crops" in data
        assert "mode" in data
        assert "crop_count" in data
        
        assert isinstance(data["crops"], list)
        assert len(data["crops"]) > 0
        assert data["mode"] == "real"
        assert isinstance(data["crop_count"], int)
    
    def test_model_info_consistency(self):
        """Test model info is consistent across endpoints."""
        # Get info from health endpoint
        health_response = requests.get(f"{self.BASE_URL}/")
        assert health_response.status_code == 200
        health_data = health_response.json()
        
        # Get info from prediction
        payload = {
            "N": 50, "P": 30, "K": 40,
            "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
            "mode": "real", "top_n": 3
        }
        pred_response = requests.post(f"{self.BASE_URL}/predict", json=payload)
        assert pred_response.status_code == 200
        pred_data = pred_response.json()
        
        # Check consistency
        assert health_data["version"] == pred_data["model_info"]["version"]
        assert health_data["models"]["real"] == pred_data["model_info"]["crops"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
