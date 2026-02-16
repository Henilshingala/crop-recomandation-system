"""
Crop Recommendation System - ML Inference Utility
=================================================
Handles loading the trained ML model and making predictions.

This module:
- Loads model_rf.joblib and label_encoder.joblib from AiMl directory
- Provides predict_top_crops() function for getting top 3 recommendations
- Caches the model in memory for fast inference
"""

import os
import logging
import requests
from django.conf import settings
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class CropPredictor:
    """
    ML model inference client that calls a remote API (Hugging Face).
    
    This avoids loading large models into memory on restricted environments like Render.
    """
    
    _instance: Optional['CropPredictor'] = None
    _api_url = None
    
    def __new__(cls):
        """Singleton pattern - only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize with API configuration."""
        # Use Hugging Face Space URL from environment
        self._api_url = os.environ.get("HF_API_URL", "https://shingala-crs.hf.space")
        if not self._api_url.endswith("/predict"):
            self._api_url = f"{self._api_url.rstrip('/')}/predict"
            
        logger.info(f"CropPredictor initialized with API: {self._api_url}")
    
    def predict_top_crops(
        self,
        n: float,
        p: float,
        k: float,
        temperature: float,
        humidity: float,
        ph: float,
        rainfall: float,
        top_n: int = 3
    ) -> List[Dict]:
        """
        Predict top N crop recommendations via remote API.
        """
        payload = {
            'N': n,
            'P': p,
            'K': k,
            'temperature': temperature,
            'humidity': humidity,
            'ph': ph,
            'rainfall': rainfall
        }
        
        try:
            logger.info(f"Calling ML API for prediction: {self._api_url}")
            response = requests.post(self._api_url, json=payload, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Return the API response with crop, confidence, and nutrition
            return [{
                'crop': data['crop'],
                'confidence': round(data['confidence'] * 100, 2),
                'nutrition': data.get('nutrition')  # Include nutrition from API
            }]
            
        except Exception as e:
            logger.error(f"Prediction API call failed: {e}")
            # Return a graceful fallback or raise depending on preference
            # For now, we raise to let the view handle the error
            raise RuntimeError(f"ML Model API Error: {str(e)}")
    
    def get_available_crops(self) -> List[str]:
        """Check if API is live."""
        try:
            health_url = self._api_url.replace("/predict", "/")
            response = requests.get(health_url, timeout=5)
            response.raise_for_status()
            return ["API is active"]
        except:
            return ["API is unreachable"]

    def reload_models(self):
        """No-op for remote API."""
        pass


# Global singleton instance
_predictor: Optional[CropPredictor] = None


def get_predictor() -> CropPredictor:
    """Get the global CropPredictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = CropPredictor()
    return _predictor


def predict_top_crops(
    n: float,
    p: float,
    k: float,
    temperature: float,
    humidity: float,
    ph: float,
    rainfall: float,
    top_n: int = 3
) -> List[Dict]:
    """Convenience function for making predictions."""
    predictor = get_predictor()
    return predictor.predict_top_crops(
        n=n, p=p, k=k,
        temperature=temperature,
        humidity=humidity,
        ph=ph,
        rainfall=rainfall,
        top_n=top_n
    )
