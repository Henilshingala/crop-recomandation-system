"""
Contract tests between Django and FastAPI.
Validates API contracts and response structures.
"""

import json
import pytest
import requests
from typing import Dict, Any


class TestFastAPIContract:
    """FastAPI contract tests."""
    
    BASE_URL = "http://localhost:8000"  # Adjust for your environment
    
    def test_health_endpoint(self):
        """Test health endpoint returns expected structure."""
        response = requests.get(f"{self.BASE_URL}/")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "modes" in data
        assert "models" in data
        assert data["status"] == "online"
        assert isinstance(data["modes"], list)
        assert isinstance(data["models"], dict)
    
    def test_predict_real_mode(self):
        """Test prediction for real mode."""
        payload = {
            "N": 50, "P": 30, "K": 40,
            "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
            "mode": "real", "top_n": 3
        }
        
        response = requests.post(f"{self.BASE_URL}/predict", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        self._validate_prediction_response(data, "real", 19)
    
    def test_predict_synthetic_mode(self):
        """Test prediction for synthetic mode."""
        payload = {
            "N": 50, "P": 30, "K": 40,
            "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
            "mode": "synthetic", "top_n": 3
        }
        
        response = requests.post(f"{self.BASE_URL}/predict", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        self._validate_prediction_response(data, "synthetic", 51)
    
    def test_predict_both_mode(self):
        """Test prediction for both mode."""
        payload = {
            "N": 50, "P": 30, "K": 40,
            "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
            "mode": "both", "top_n": 3
        }
        
        response = requests.post(f"{self.BASE_URL}/predict", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        self._validate_prediction_response(data, "both", 54)
    
    def test_invalid_mode(self):
        """Test invalid mode returns 400."""
        payload = {
            "N": 50, "P": 30, "K": 40,
            "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
            "mode": "invalid", "top_n": 3
        }
        
        response = requests.post(f"{self.BASE_URL}/predict", json=payload)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
    
    def test_missing_required_fields(self):
        """Test missing required fields returns 422."""
        payload = {
            "N": 50, "P": 30,
            # Missing K, temperature, etc.
            "mode": "real"
        }
        
        response = requests.post(f"{self.BASE_URL}/predict", json=payload)
        assert response.status_code == 422
    
    def _validate_prediction_response(self, data: Dict[str, Any], expected_mode: str, expected_crop_count: int):
        """Validate prediction response structure."""
        # Check top-level structure
        assert "predictions" in data
        assert "model_info" in data
        assert "environment_info" in data
        
        # Validate predictions
        predictions = data["predictions"]
        assert isinstance(predictions, list)
        assert len(predictions) > 0
        
        for pred in predictions:
            assert "crop" in pred
            assert "confidence" in pred
            assert isinstance(pred["confidence"], (int, float))
            assert 0 <= pred["confidence"] <= 100
        
        # Validate model_info
        model_info = data["model_info"]
        assert model_info["mode"] == expected_mode
        assert model_info["crops"] == expected_crop_count
        assert "version" in model_info
        assert "type" in model_info
        
        # Validate environment_info
        env_info = data["environment_info"]
        assert "season_used" in env_info
        assert "inferred" in env_info
        assert isinstance(env_info["inferred"], bool)


class TestDjangoFastAPIContract:
    """Contract tests between Django gateway and FastAPI ML engine."""
    
    DJANGO_URL = "http://localhost:8001"  # Django gateway
    FASTAPI_URL = "http://localhost:8000"  # FastAPI ML engine
    
    def test_django_to_fastapi_routing(self):
        """Test Django correctly routes to FastAPI modes."""
        payload = {
            "N": 50, "P": 30, "K": 40,
            "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
            "mode": "real", "top_n": 3
        }
        
        # Test through Django gateway
        django_response = requests.post(f"{self.DJANGO_URL}/api/predict", json=payload)
        assert django_response.status_code == 200
        
        # Test direct FastAPI
        fastapi_response = requests.post(f"{self.FASTAPI_URL}/predict", json=payload)
        assert fastapi_response.status_code == 200
        
        # Compare structure (should be identical)
        django_data = django_response.json()
        fastapi_data = fastapi_response.json()
        
        assert django_data["model_info"]["mode"] == fastapi_data["model_info"]["mode"]
        assert django_data["model_info"]["crops"] == fastapi_data["model_info"]["crops"]
    
    def test_mode_routing_consistency(self):
        """Test mode routing is consistent across all modes."""
        modes = ["real", "synthetic", "both"]
        
        for mode in modes:
            payload = {
                "N": 50, "P": 30, "K": 40,
                "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
                "mode": mode, "top_n": 3
            }
            
            django_response = requests.post(f"{self.DJANGO_URL}/api/predict", json=payload)
            fastapi_response = requests.post(f"{self.FASTAPI_URL}/predict", json=payload)
            
            assert django_response.status_code == fastapi_response.status_code
            
            if django_response.status_code == 200:
                django_data = django_response.json()
                fastapi_data = fastapi_response.json()
                assert django_data["model_info"]["mode"] == mode
                assert fastapi_data["model_info"]["mode"] == mode


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
