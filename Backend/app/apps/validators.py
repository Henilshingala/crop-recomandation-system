"""
Input Validation Utilities for Crop Recommendation API
====================================================
Ranges loaded from feature_ranges.json — single source of truth.
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework import serializers

logger = logging.getLogger(__name__)

# ── Load feature ranges from the shared JSON (single source of truth) ──
_FEATURE_RANGES_PATHS = [
    os.path.join(settings.BASE_DIR.parent.parent, "Aiml", "feature_ranges.json"),
    os.path.join(settings.BASE_DIR.parent, "Aiml", "feature_ranges.json"),
    os.path.join(settings.BASE_DIR, "..", "..", "Aiml", "feature_ranges.json"),
]

FEATURE_RANGES: dict = {}
for _p in _FEATURE_RANGES_PATHS:
    if os.path.isfile(_p):
        with open(_p, encoding="utf-8") as _f:
            FEATURE_RANGES = json.load(_f)
        logger.info("Loaded feature_ranges.json from %s", _p)
        break
else:
    logger.warning("feature_ranges.json not found — using fallback acceptance ranges")

# Build SAFE_RANGES from the acceptance section (or fallback)
if FEATURE_RANGES and "acceptance" in FEATURE_RANGES:
    _acc = FEATURE_RANGES["acceptance"]
    SAFE_RANGES = {
        k: {"min": v["min"], "max": v["max"], "unit": v.get("unit", "")}
        for k, v in _acc.items()
        if not k.startswith("_")
    }
else:
    # Fallback — matches feature_ranges.json acceptance as of V6 (2026-03-03)
    SAFE_RANGES = {
        'N':           {'min': 0,    'max': 210,  'unit': 'kg/ha'},
        'P':           {'min': 0,    'max': 115,  'unit': 'kg/ha'},
        'K':           {'min': 0,    'max': 315,  'unit': 'kg/ha'},
        'temperature': {'min': 5,    'max': 50,   'unit': '°C'},
        'humidity':    {'min': 0,    'max': 100,  'unit': '%'},
        'ph':          {'min': 3.0,  'max': 10.0, 'unit': 'pH'},
        'rainfall':    {'min': 0,    'max': 3200, 'unit': 'mm'},
        'moisture':    {'min': 0,    'max': 100,  'unit': '%'},
        'soil_type':   {'min': 0,    'max': 4,    'unit': 'type'},
        'irrigation':  {'min': 0,    'max': 1,    'unit': 'type'},
        'season':      {'min': 0,    'max': 2,    'unit': 'type'},
    }

logger.info("SAFE_RANGES: %s", {k: [v['min'], v['max']] for k, v in SAFE_RANGES.items()})


class PredictionInputValidator:
    """Comprehensive validator for prediction inputs."""
    
    @staticmethod
    def validate_numeric_range(value: float, param_name: str) -> float:
        """Validate numeric value is within safe agricultural ranges."""
        if param_name not in SAFE_RANGES:
            raise ValidationError(f"Unknown parameter: {param_name}")
        
        range_info = SAFE_RANGES[param_name]
        
        # Check if value is actually a number
        try:
            value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{param_name} must be a valid number")
        
        # Check range
        if value < range_info['min'] or value > range_info['max']:
            raise ValidationError(
                f"{param_name} ({value}{range_info['unit']}) outside safe range "
                f"({range_info['min']}-{range_info['max']}{range_info['unit']})"
            )
        
        return value
    
    @staticmethod
    def sanitize_input(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize and validate all input data."""
        sanitized = {}
        
        # Validate required numeric parameters
        required_params = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
        for param in required_params:
            if param not in data:
                raise ValidationError(f"Missing required parameter: {param}")
            
            sanitized[param] = PredictionInputValidator.validate_numeric_range(
                data[param], param
            )
        
        # Validate optional parameters
        optional_params = ['moisture', 'soil_type', 'irrigation', 'season']
        for param in optional_params:
            if param in data:
                sanitized[param] = PredictionInputValidator.validate_numeric_range(
                    data[param], param
                )
            else:
                # Set defaults
                defaults = {'moisture': 43.5, 'soil_type': 1, 'irrigation': 0}
                if param in defaults:
                    sanitized[param] = defaults[param]
        
        # Validate top_n
        if 'top_n' in data:
            try:
                top_n = int(data['top_n'])
                if top_n < 1 or top_n > 10:
                    raise ValidationError("top_n must be between 1 and 10")
                sanitized['top_n'] = top_n
            except (ValueError, TypeError):
                raise ValidationError("top_n must be a valid integer")
        
        return sanitized
    
    @staticmethod
    def detect_suspicious_patterns(data: Dict[str, Any]) -> List[str]:
        """Detect potentially malicious input patterns."""
        warnings = []
        
        # Check for extreme values that might indicate attacks
        extreme_checks = {
            'N': 250,   # Very high nitrogen
            'P': 150,   # Very high phosphorus  
            'K': 150,   # Very high potassium
            'temperature': 45,  # Extreme temperature
            'rainfall': 800,    # Extreme rainfall
        }
        
        for param, threshold in extreme_checks.items():
            if param in data and float(data[param]) > threshold:
                warnings.append(f"Extreme {param} value: {data[param]}")
        
        # Check for repeated values (might indicate automated attacks)
        numeric_values = [float(v) for k, v in data.items() 
                         if k in ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']]
        if len(set(numeric_values)) == 1 and len(numeric_values) > 3:
            warnings.append("All input parameters have the same value - suspicious pattern")
        
        return warnings


class SecurePredictionSerializer(serializers.Serializer):
    """Enhanced serializer with comprehensive validation."""
    
    N = serializers.FloatField(
        min_value=SAFE_RANGES['N']['min'],
        max_value=SAFE_RANGES['N']['max'],
        help_text="Nitrogen content (kg/ha)"
    )
    P = serializers.FloatField(
        min_value=SAFE_RANGES['P']['min'], 
        max_value=SAFE_RANGES['P']['max'],
        help_text="Phosphorus content (kg/ha)"
    )
    K = serializers.FloatField(
        min_value=SAFE_RANGES['K']['min'],
        max_value=SAFE_RANGES['K']['max'], 
        help_text="Potassium content (kg/ha)"
    )
    temperature = serializers.FloatField(
        min_value=SAFE_RANGES['temperature']['min'],
        max_value=SAFE_RANGES['temperature']['max'],
        help_text="Temperature (°C)"
    )
    humidity = serializers.FloatField(
        min_value=SAFE_RANGES['humidity']['min'],
        max_value=SAFE_RANGES['humidity']['max'],
        help_text="Humidity (%)"
    )
    ph = serializers.FloatField(
        min_value=SAFE_RANGES['ph']['min'],
        max_value=SAFE_RANGES['ph']['max'],
        help_text="Soil pH"
    )
    rainfall = serializers.FloatField(
        min_value=SAFE_RANGES['rainfall']['min'],
        max_value=SAFE_RANGES['rainfall']['max'],
        help_text="Rainfall (mm)"
    )
    moisture = serializers.FloatField(
        min_value=SAFE_RANGES['moisture']['min'],
        max_value=SAFE_RANGES['moisture']['max'],
        default=43.5,
        help_text="Soil moisture (%)"
    )
    soil_type = serializers.IntegerField(
        min_value=SAFE_RANGES['soil_type']['min'],
        max_value=SAFE_RANGES['soil_type']['max'],
        default=1,
        help_text="Soil type (0=sandy, 1=loamy, 2=clay, 3=silty)"
    )
    irrigation = serializers.IntegerField(
        min_value=SAFE_RANGES['irrigation']['min'],
        max_value=SAFE_RANGES['irrigation']['max'],
        default=0,
        help_text="Irrigation (0=rainfed, 1=irrigated)"
    )
    season = serializers.IntegerField(
        min_value=SAFE_RANGES['season']['min'],
        max_value=SAFE_RANGES['season']['max'],
        required=False,
        help_text="Season (0=Kharif, 1=Rabi, 2=Zaid)"
    )
    # mode removed in V7 — system runs all models internally
    top_n = serializers.IntegerField(
        min_value=1,
        max_value=10,
        default=3,
        help_text="Number of top predictions to return"
    )
    
    def validate(self, attrs):
        """Cross-field validation and security checks."""
        # Detect suspicious patterns
        warnings = PredictionInputValidator.detect_suspicious_patterns(attrs)
        if warnings:
            logger.warning(f"Suspicious input detected: {warnings}")
            # Add warnings to response but don't block
            self._warnings = warnings
        
        return attrs
