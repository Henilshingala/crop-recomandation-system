#!/usr/bin/env python3
"""
System validation script for deployment preparation.
"""

import json
import os
import sys
from pathlib import Path

def validate_model_registry():
    """Validate model registry exists and has correct structure."""
    print("Validating model registry...")
    
    registry_path = Path("Aiml/model_registry.json")
    if not registry_path.exists():
        print("ERROR: model_registry.json not found")
        return False
    
    try:
        with open(registry_path, "r") as f:
            registry = json.load(f)
        
        required_sections = ["models", "crop_mappings", "version"]
        for section in required_sections:
            if section not in registry:
                print(f"ERROR: Missing section {section}")
                return False
        
        required_modes = ["real", "synthetic", "both"]
        for mode in required_modes:
            if mode not in registry["models"]:
                print(f"ERROR: Missing model config for {mode}")
                return False
        
        print("PASS: Model registry validation")
        return True
        
    except Exception as e:
        print(f"ERROR: Invalid model registry: {e}")
        return False

def validate_no_hardcoded_paths():
    """Validate no hardcoded model paths in predictor files."""
    print("Validating no hardcoded model paths...")
    
    predictor_files = [
        "Aiml/predictors/real.py",
        "Aiml/predictors/synthetic.py", 
        "Aiml/predictors/both.py"
    ]
    
    hardcoded_patterns = [
        "stacked_ensemble_v3.joblib",
        "model_rf.joblib",
        "label_encoder_v3.joblib",
        "label_encoder.joblib"
    ]
    
    for file_path in predictor_files:
        if Path(file_path).exists():
            content = Path(file_path).read_text()
            for pattern in hardcoded_patterns:
                if pattern in content and "model_registry" not in content:
                    print(f"ERROR: Hardcoded model path in {file_path}: {pattern}")
                    return False
    
    print("PASS: No hardcoded model paths")
    return True

def validate_dockerfile():
    """Validate Dockerfile exists and uses multi-stage build."""
    print("Validating Dockerfile...")
    
    dockerfile_path = Path("Dockerfile")
    if not dockerfile_path.exists():
        print("ERROR: Dockerfile not found")
        return False
    
    content = dockerfile_path.read_text()
    if "as builder" not in content.lower():
        print("ERROR: Dockerfile missing multi-stage build")
        return False
    
    if "appuser" not in content:
        print("ERROR: Dockerfile missing non-root user")
        return False
    
    print("PASS: Dockerfile validation")
    return True

def validate_config_exists():
    """Validate config.py exists with environment validation."""
    print("Validating configuration...")
    
    config_path = Path("Aiml/config.py")
    if not config_path.exists():
        print("ERROR: config.py not found")
        return False
    
    content = config_path.read_text()
    if "validate_environment" not in content:
        print("ERROR: config.py missing environment validation")
        return False
    
    print("PASS: Configuration validation")
    return True

def validate_health_endpoints():
    """Validate health endpoints are implemented."""
    print("Validating health endpoints...")
    
    app_path = Path("Aiml/app.py")
    if not app_path.exists():
        print("ERROR: app.py not found")
        return False
    
    content = app_path.read_text()
    if "/health" not in content:
        print("ERROR: Health endpoint not found")
        return False
    
    print("PASS: Health endpoints validation")
    return True

def validate_requirements():
    """Validate requirements.txt includes production dependencies."""
    print("Validating requirements...")
    
    req_path = Path("requirements.txt")
    if not req_path.exists():
        print("ERROR: requirements.txt not found")
        return False
    
    content = req_path.read_text()
    required_deps = ["gunicorn", "python-json-logger", "psutil", "pytest"]
    
    for dep in required_deps:
        if dep not in content:
            print(f"WARNING: Missing dependency {dep}")
    
    print("PASS: Requirements validation")
    return True

def main():
    """Run all system validations."""
    print("Starting system validation...")
    print("=" * 50)
    
    validations = [
        validate_model_registry,
        validate_no_hardcoded_paths,
        validate_dockerfile,
        validate_config_exists,
        validate_health_endpoints,
        validate_requirements,
    ]
    
    passed = 0
    total = len(validations)
    
    for validation in validations:
        if validation():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Validation Summary: {passed}/{total} passed")
    
    if passed == total:
        print("SUCCESS: All system validations passed!")
        return 0
    else:
        print("FAILURE: Some validations failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
