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
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from django.conf import settings
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class CropPredictor:
    """
    Singleton class for ML model inference.
    
    Loads the trained Random Forest model and Label Encoder once,
    then reuses them for all predictions.
    """
    
    _instance: Optional['CropPredictor'] = None
    _model = None
    _label_encoder = None
    _is_loaded = False
    
    # Feature columns in exact order expected by the model
    FEATURE_COLUMNS = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
    
    def __new__(cls):
        """Singleton pattern - only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize and load models if not already loaded."""
        if not self._is_loaded:
            self._load_models()
    
    def _get_model_path(self) -> Path:
        """
        Get the path to AiMl directory containing model files.
        Checks AI_ML_DIR environment variable first, then uses default relative path.
        """
        env_path = os.environ.get("AI_ML_DIR")
        if env_path:
            aiml_dir = Path(env_path)
        else:
            # Navigate from Backend/app to AiMl
            base_dir = Path(settings.BASE_DIR)  # D:/downloads/CRS/Backend/app
            aiml_dir = base_dir.parent.parent / 'AiMl'  # D:/downloads/CRS/AiMl
        
        if not aiml_dir.exists():
            raise FileNotFoundError(f"AiMl directory not found at: {aiml_dir}. Set AI_ML_DIR env var if it's located elsewhere.")
        
        return aiml_dir
    
    def _load_models(self):
        """
        Load the trained model and label encoder from disk.
        
        Files loaded:
        - model_rf.joblib: Trained Random Forest classifier
        - label_encoder.joblib: Scikit-learn LabelEncoder for crop names
        """
        try:
            aiml_dir = self._get_model_path()
            
            model_path = aiml_dir / 'model_rf.joblib'
            encoder_path = aiml_dir / 'label_encoder.joblib'
            
            # Validate files exist
            if not model_path.exists():
                raise FileNotFoundError(f"Model file not found: {model_path}")
            if not encoder_path.exists():
                raise FileNotFoundError(f"Label encoder not found: {encoder_path}")
            
            # Load models
            logger.info(f"Loading ML model from: {model_path}")
            self._model = joblib.load(model_path)
            
            logger.info(f"Loading label encoder from: {encoder_path}")
            self._label_encoder = joblib.load(encoder_path)
            
            self._is_loaded = True
            logger.info("ML models loaded successfully!")
            
            # Log available crop classes
            logger.info(f"Available crops: {list(self._label_encoder.classes_)}")
            
        except Exception as e:
            logger.error(f"Failed to load ML models: {e}")
            raise
    
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
        Predict top N crop recommendations with confidence scores.
        
        Args:
            n: Nitrogen content (kg/ha)
            p: Phosphorus content (kg/ha)
            k: Potassium content (kg/ha)
            temperature: Average temperature (°C)
            humidity: Relative humidity (%)
            ph: Soil pH value
            rainfall: Annual rainfall (mm)
            top_n: Number of top recommendations (default: 3)
        
        Returns:
            List of dictionaries with crop names and confidence percentages:
            [
                {"crop": "rice", "confidence": 98.6},
                {"crop": "wheat", "confidence": 12.3},
                {"crop": "maize", "confidence": 3.1}
            ]
        """
        if not self._is_loaded:
            self._load_models()
        
        # Prepare input data as DataFrame with correct column order
        input_data = pd.DataFrame([{
            'N': n,
            'P': p,
            'K': k,
            'temperature': temperature,
            'humidity': humidity,
            'ph': ph,
            'rainfall': rainfall
        }])[self.FEATURE_COLUMNS]
        
        # Get prediction probabilities for all classes
        probabilities = self._model.predict_proba(input_data)[0]
        
        # Get indices of top N predictions (sorted descending)
        top_indices = np.argsort(probabilities)[-top_n:][::-1]
        
        # Build result list with crop names and confidence scores
        results = []
        for idx in top_indices:
            crop_name = self._label_encoder.inverse_transform([idx])[0]
            confidence = round(probabilities[idx] * 100, 2)  # Convert to percentage
            
            results.append({
                'crop': crop_name,
                'confidence': confidence
            })
        
        logger.info(f"Prediction results: {results}")
        return results
    
    def get_available_crops(self) -> List[str]:
        """Return list of all crop labels the model can predict."""
        if not self._is_loaded:
            self._load_models()
        return list(self._label_encoder.classes_)
    
    def reload_models(self):
        """Force reload models from disk (useful for model updates)."""
        self._is_loaded = False
        self._load_models()


# Global singleton instance
_predictor: Optional[CropPredictor] = None


def get_predictor() -> CropPredictor:
    """
    Get the global CropPredictor instance.
    
    Usage:
        from apps.ml_inference import get_predictor
        
        predictor = get_predictor()
        results = predictor.predict_top_crops(N=90, P=42, K=43, ...)
    """
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
    """
    Convenience function for making predictions.
    
    Wraps the CropPredictor singleton for simpler API.
    
    Usage:
        from apps.ml_inference import predict_top_crops
        
        results = predict_top_crops(
            n=90, p=42, k=43,
            temperature=24.5, humidity=68,
            ph=6.7, rainfall=120
        )
    """
    predictor = get_predictor()
    return predictor.predict_top_crops(
        n=n, p=p, k=k,
        temperature=temperature,
        humidity=humidity,
        ph=ph,
        rainfall=rainfall,
        top_n=top_n
    )
