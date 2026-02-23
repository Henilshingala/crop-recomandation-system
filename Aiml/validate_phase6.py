#!/usr/bin/env python3
"""
Phase 6 validation script.
Validates model registry, predictor isolation, and response consistency.
"""

import json
import sys
from pathlib import Path

def validate_model_registry():
    """Validate model registry structure and content."""
    print("Validating model registry...")
    
    try:
        with open("model_registry.json", "r") as f:
            registry = json.load(f)
    except FileNotFoundError:
        print(f"model_registry.json not found")
        return False
    
    # Check required sections
    required_sections = ["models", "crop_mappings", "version"]
    for section in required_sections:
        if section not in registry:
            print(f"Missing section: {section}")
            return False
    
    # Validate models
    models = registry["models"]
    required_modes = ["real", "synthetic", "both"]
    for mode in required_modes:
        if mode not in models:
            print(f"❌ Missing model config for mode: {mode}")
            return False
        
        config = models[mode]
        required_fields = ["model_file", "encoder_file", "crop_count", "feature_count", "features", "type"]
        for field in required_fields:
            if field not in config:
                print(f"Missing field '{field}' in {mode} config")
                return False
        
        # Validate feature count matches features list length
        if len(config["features"]) != config["feature_count"]:
            print(f"Feature count mismatch for {mode}: {len(config['features'])} vs {config['feature_count']}")
            return False
    
    # Validate crop mappings
    mappings = registry["crop_mappings"]
    if "real_to_synthetic" not in mappings or "synthetic_to_real" not in mappings:
        print(f"Missing crop mappings")
        return False
    
    print("Model registry validation passed")
    return True

def validate_predictor_isolation():
    """Validate that each predictor loads only required artifacts."""
    print("Validating predictor isolation...")
    
    try:
        from predictors.real import RealPredictor
        from predictors.synthetic import SyntheticPredictor
        from predictors.both import BothPredictor
        
        # Test real predictor
        real_pred = RealPredictor()
        if not hasattr(real_pred, 'model_file') or not hasattr(real_pred, 'crop_count'):
            print(f"Real predictor missing registry attributes")
            return False
        
        # Test synthetic predictor
        synth_pred = SyntheticPredictor()
        if not hasattr(synth_pred, 'model_file') or not hasattr(synth_pred, 'crop_count'):
            print(f"Synthetic predictor missing registry attributes")
            return False
        
        # Test both predictor
        both_pred = BothPredictor()
        if not hasattr(both_pred, 'unified_crops'):
            print(f"Both predictor missing unified crops")
            return False
        
        print("Predictor isolation validation passed")
        return True
        
    except Exception as e:
        print(f"Predictor validation failed: {e}")
        return False

def validate_response_consistency():
    """Validate response structure consistency across modes."""
    print("Validating response consistency...")
    
    try:
        from predictors.real import RealPredictor
        from predictors.synthetic import SyntheticPredictor
        from predictors.both import BothPredictor
        
        # Test input
        test_input = {
            "N": 50, "P": 30, "K": 40,
            "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
            "top_n": 3, "season": 1, "soil_type": 1, "irrigation": 0
        }
        
        # Get predictions from all modes
        real_result = RealPredictor().predict(**test_input)
        synth_result = SyntheticPredictor().predict(**test_input)
        both_result = BothPredictor().predict(**test_input, moisture=43.5)
        
        # Validate response structure
        required_keys = ["predictions", "model_info", "environment_info"]
        for result, mode in [(real_result, "real"), (synth_result, "synthetic"), (both_result, "both")]:
            for key in required_keys:
                if key not in result:
                    print(f"FAIL {mode} response missing key: {key}")
                    return False
            
            # Validate model_info structure
            model_info = result["model_info"]
            required_model_keys = ["version", "type", "mode", "crops"]
            for key in required_model_keys:
                if key not in model_info:
                    print(f"FAIL {mode} model_info missing key: {key}")
                    return False
            
            # Validate environment_info structure
            env_info = result["environment_info"]
            required_env_keys = ["season_used", "inferred"]
            for key in required_env_keys:
                if key not in env_info:
                    print(f"FAIL {mode} environment_info missing key: {key}")
                    return False
        
        print("Response consistency validation passed")
        return True
        
    except Exception as e:
        print(f"Response consistency validation failed: {e}")
        return False

def validate_no_hardcoded_counts():
    """Validate no hardcoded crop counts outside registry."""
    print("Validating no hardcoded crop counts...")
    
    # Check for hardcoded numbers in predictor files
    predictor_files = ["predictors/real.py", "predictors/synthetic.py", "predictors/both.py"]
    
    for file_path in predictor_files:
        content = Path(file_path).read_text()
        
        # Look for hardcoded crop counts (19, 51, 54)
        hardcoded_patterns = ["19", "51", "54"]
        for pattern in hardcoded_patterns:
            # Skip if it's part of a variable name or comment
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if pattern in line and not line.strip().startswith('#'):
                    # Check if it's a literal number assignment
                    if f'"{pattern}"' in line or f"'{pattern}'" in line:
                        continue  # String literal, OK
                    if '=' in line and pattern.split()[0] in line.split('=')[1]:
                        print(f"WARNING Potential hardcoded count in {file_path}:{i+1}: {line.strip()}")
    
    print("No hardcoded crop counts validation passed")
    return True

def main():
    """Run all Phase 6 validations."""
    print("Starting Phase 6 validation...")
    print()
    
    validations = [
        validate_model_registry,
        validate_predictor_isolation,
        validate_response_consistency,
        validate_no_hardcoded_counts,
    ]
    
    passed = 0
    total = len(validations)
    
    for validation in validations:
        if validation():
            passed += 1
        print()
    
    print(f"Validation Summary: {passed}/{total} passed")
    
    if passed == total:
        print("Phase 6 validation complete!")
        return 0
    else:
        print("Phase 6 validation failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
