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
        self._api_url = os.environ.get("HF_API_URL", "https://shingala-crs.hf.space/")
        if not self._api_url.endswith("/predict"):
            self._api_url = f"{self._api_url.rstrip('/')}/predict"
            
        # Get Access Token for private Spaces
        self._token = os.environ.get("HF_TOKEN")
            
        logger.info(f"CropPredictor initialized with API: {self._api_url} (Token: {'Yes' if self._token else 'No'})")
    
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
        
        # Add headers to avoid bot detection
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://huggingface.co/",
            "Origin": "https://huggingface.co"
        }
        
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        
        try:
            logger.info(f"Calling ML API for prediction: {self._api_url}")
            response = requests.post(self._api_url, json=payload, headers=headers, timeout=15, allow_redirects=True)
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
            raise RuntimeError(f"ML Model API Error: {str(e)}")
    
    def get_available_crops(self) -> List[str]:
        """Check if API is live and return available crops."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://huggingface.co/",
            "Origin": "https://huggingface.co"
        }
        
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        
        base_url = self._api_url.replace("/predict", "").rstrip("/")
        urls_to_try = [f"{base_url}/", base_url]
        
        last_error = ""
        for url in urls_to_try:
            try:
                logger.info(f"Probing HF Space at: {url}")
                # HF often uses redirects, ensure we follow them
                response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        return data.get('available_crops', ["API is active"])
                    except:
                        # If not JSON, maybe it's the HF loading page
                        return ["API is active (HTML response)"]
                
                last_error = f"Status {response.status_code} at {url}"
            except Exception as e:
                last_error = str(e)
                
        return [f"API is unreachable: {last_error}"]

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
