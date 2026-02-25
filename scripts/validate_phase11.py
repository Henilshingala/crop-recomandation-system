#!/usr/bin/env python3
"""
Phase 11 final validation script.
Validates architectural cleanup and separation of concerns.
"""

import os
import json
import ast
import re
from pathlib import Path
from typing import Dict, List, Set


class Phase11Validator:
    """Validates Phase 11 architectural cleanup requirements."""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.issues = []
        self.warnings = []
    
    def log_issue(self, category: str, message: str, severity: str = "error"):
        """Log an issue found during validation."""
        if severity == "error":
            self.issues.append(f"[{category}] {message}")
        else:
            self.warnings.append(f"[{category}] {message}")
    
    def validate_folder_structure(self) -> bool:
        """Validate clean folder structure."""
        print("📁 Validating folder structure...")
        
        required_structure = {
            "Aiml/": ["app.py", "config.py", "model_registry.json", "predictors/"],
            "Backend/": ["backend/", "api/"],
            "Frontend/": ["src/", "public/"],
            "scripts/": ["run_tests.py", "benchmark.py", "memory_leak_test.py"],
            "tests/": ["test_contract.py", "test_integration.py"],
            "environments/": ["staging.env"]
        }
        
        structure_valid = True
        
        for folder, required_items in required_structure.items():
            folder_path = self.project_root / folder
            if not folder_path.exists():
                self.log_issue("structure", f"Missing required folder: {folder}")
                structure_valid = False
                continue
            
            for item in required_items:
                item_path = folder_path / item
                if not item_path.exists():
                    self.log_issue("structure", f"Missing required item: {folder}{item}")
                    structure_valid = False
        
        # Check for cleanup of legacy files
        legacy_patterns = [
            "Aiml/00_*.py",
            "Aiml/01_*.py",
            "Aiml/02_*.py",
            "Aiml/*training*.py",
            "Aiml/*dataset*.py",
            "Aiml/*validation*.py",
            "Aiml/confusion_matrix*.png",
            "Aiml/*metadata*.json",
            "Aiml/training_log*.txt"
        ]
        
        for pattern in legacy_patterns:
            matches = list(self.project_root.glob(pattern))
            if matches:
                for match in matches:
                    self.log_issue("cleanup", f"Legacy file still present: {match}")
        
        if structure_valid:
            print("✅ Folder structure validation passed")
        
        return structure_valid
    
    def validate_separation_of_concerns(self) -> bool:
        """Validate separation of concerns between services."""
        print("🔍 Validating separation of concerns...")
        
        concerns_valid = True
        
        # Check FastAPI (ML Engine) - should only do ML inference
        fastapi_files = list(self.project_root.glob("Aiml/*.py"))
        for file_path in fastapi_files:
            if file_path.name in ["app.py", "config.py", "logging_config.py"]:
                content = file_path.read_text()
                
                # Should not contain database logic
                db_patterns = [
                    r"import.*sqlite",
                    r"from.*django",
                    r"models\.Model",
                    r"\.objects\.",
                    r"SELECT.*FROM",
                    r"INSERT.*INTO"
                ]
                
                for pattern in db_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        self.log_issue("separation", f"FastAPI file contains database logic: {file_path.name}")
                        concerns_valid = False
        
        # Check Django (Backend) - should not contain ML logic
        backend_files = list(self.project_root.glob("Backend/**/*.py"), recursive=True)
        for file_path in backend_files:
            if file_path.is_file():
                content = file_path.read_text()
                
                # Should not contain ML inference
                ml_patterns = [
                    r"joblib\.load",
                    r"predict\(",
                    r"model\.",
                    r"sklearn",
                    r"numpy.*predict",
                    r"pandas.*DataFrame"
                ]
                
                for pattern in ml_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        # Allow pandas for data processing, but not ML inference
                        if "predict" in content.lower() and "joblib" in content.lower():
                            self.log_issue("separation", f"Django file contains ML logic: {file_path}")
                            concerns_valid = False
        
        # Check Frontend - should not contain business logic
        frontend_files = list(self.project_root.glob("Frontend/src/**/*.{js,jsx,ts,tsx}"), recursive=True)
        for file_path in frontend_files:
            if file_path.is_file():
                content = file_path.read_text()
                
                # Should not contain complex validation logic
                if "cropCount === 19" in content or "cropCount === 51" in content:
                    self.log_issue("separation", f"Frontend contains hardcoded crop counts: {file_path}")
                    concerns_valid = False
        
        if concerns_valid:
            print("✅ Separation of concerns validation passed")
        
        return concerns_valid
    
    def validate_no_hardcoded_values(self) -> bool:
        """Validate no hardcoded crop counts or model paths."""
        print("🔢 Validating no hardcoded values...")
        
        hardcoded_valid = True
        
        # Check for hardcoded crop counts
        patterns_to_check = [
            (r"19", "hardcoded crop count 19"),
            (r"51", "hardcoded crop count 51"),
            (r"54", "hardcoded crop count 54"),
            (r"stacked_ensemble_v3\.joblib", "hardcoded model path"),
            (r"model_rf\.joblib", "hardcoded model path"),
            (r"label_encoder.*\.joblib", "hardcoded encoder path")
        ]
        
        # Files to check
        files_to_check = []
        files_to_check.extend(self.project_root.glob("Aiml/**/*.py"))
        files_to_check.extend(self.project_root.glob("Backend/**/*.py"))
        
        for file_path in files_to_check:
            if file_path.is_file() and file_path.name != "model_registry.json":
                content = file_path.read_text()
                lines = content.split('\\n')
                
                for i, line in enumerate(lines, 1):
                    # Skip comments and imports
                    if line.strip().startswith('#') or line.strip().startswith('"""') or line.strip().startswith("'''"):
                        continue
                    
                    for pattern, description in patterns_to_check:
                        if re.search(pattern, line):
                            # Check if it's actually a hardcoded value
                            if not any(skip in line.lower() for skip in ["comment", "todo", "example"]):
                                # More specific checks
                                if "19" in line and not any(x in line.lower() for x in ["version", "port", "year"]):
                                    if not line.strip().startswith('"') and not line.strip().startswith("'"):
                                        self.log_issue("hardcoded", f"{description} in {file_path}:{i}: {line.strip()}")
                                        hardcoded_valid = False
        
        if hardcoded_valid:
            print("✅ No hardcoded values validation passed")
        
        return hardcoded_valid
    
    def validate_model_registry_usage(self) -> bool:
        """Validate model registry is being used correctly."""
        print("📋 Validating model registry usage...")
        
        registry_valid = True
        
        # Check model registry exists and is valid
        registry_path = self.project_root / "Aiml" / "model_registry.json"
        if not registry_path.exists():
            self.log_issue("registry", "model_registry.json not found")
            return False
        
        try:
            with open(registry_path, "r") as f:
                registry = json.load(f)
            
            # Validate registry structure
            required_sections = ["models", "crop_mappings", "version"]
            for section in required_sections:
                if section not in registry:
                    self.log_issue("registry", f"Missing section in model registry: {section}")
                    registry_valid = False
            
            # Check predictors are using registry
            predictor_files = [
                self.project_root / "Aiml" / "predictors" / "real.py",
                self.project_root / "Aiml" / "predictors" / "synthetic.py",
                self.project_root / "Aiml" / "predictors" / "both.py"
            ]
            
            for predictor_file in predictor_files:
                if predictor_file.exists():
                    content = predictor_file.read_text()
                    if "model_registry.json" not in content:
                        self.log_issue("registry", f"Predictor not using model registry: {predictor_file.name}")
                        registry_valid = False
        
        except json.JSONDecodeError as e:
            self.log_issue("registry", f"Invalid JSON in model registry: {e}")
            registry_valid = False
        
        if registry_valid:
            print("✅ Model registry usage validation passed")
        
        return registry_valid
    
    def validate_shared_utilities(self) -> bool:
        """Validate shared utilities are properly implemented."""
        print("🛠️  Validating shared utilities...")
        
        utilities_valid = True
        
        # Check season_utils exists and is used
        season_utils_path = self.project_root / "Aiml" / "predictors" / "season_utils.py"
        if not season_utils_path.exists():
            self.log_issue("utilities", "season_utils.py not found")
            utilities_valid = False
        else:
            # Check it contains required functions
            content = season_utils_path.read_text()
            if "def infer_season" not in content:
                self.log_issue("utilities", "infer_season function not found in season_utils.py")
                utilities_valid = False
            
            if "def get_season_name" not in content:
                self.log_issue("utilities", "get_season_name function not found in season_utils.py")
                utilities_valid = False
        
        # Check predictors are using shared utilities
        predictor_files = [
            self.project_root / "Aiml" / "predictors" / "real.py",
            self.project_root / "Aiml" / "predictors" / "synthetic.py",
            self.project_root / "Aiml" / "predictors" / "both.py"
        ]
        
        for predictor_file in predictor_files:
            if predictor_file.exists():
                content = predictor_file.read_text()
                if "from .season_utils import" not in content:
                    self.log_issue("utilities", f"Predictor not using shared season utils: {predictor_file.name}")
                    utilities_valid = False
                
                # Check for duplicate season inference
                if "def infer_season" in content and predictor_file.name != "season_utils.py":
                    self.log_issue("utilities", f"Duplicate season inference in {predictor_file.name}")
                    utilities_valid = False
        
        if utilities_valid:
            print("✅ Shared utilities validation passed")
        
        return utilities_valid
    
    def validate_configuration_externalization(self) -> bool:
        """Validate configuration is properly externalized."""
        print("⚙️  Validating configuration externalization...")
        
        config_valid = True
        
        # Check config.py exists
        config_path = self.project_root / "Aiml" / "config.py"
        if not config_path.exists():
            self.log_issue("config", "config.py not found")
            return False
        
        # Check environment files exist
        env_files = [
            self.project_root / "environments" / "staging.env"
        ]
        
        for env_file in env_files:
            if not env_file.exists():
                self.log_issue("config", f"Environment file not found: {env_file}")
                config_valid = False
        
        # Check app.py is using config
        app_py = self.project_root / "Aiml" / "app.py"
        if app_py.exists():
            content = app_py.read_text()
            if "from config import config" not in content:
                self.log_issue("config", "app.py not using config module")
                config_valid = False
        
        if config_valid:
            print("✅ Configuration externalization validation passed")
        
        return config_valid
    
    def generate_report(self) -> str:
        """Generate validation report."""
        report = []
        report.append("# Phase 11 Validation Report\\n")
        
        if self.issues:
            report.append("## Issues Found\\n")
            for issue in self.issues:
                report.append(f"❌ {issue}")
            report.append("")
        
        if self.warnings:
            report.append("## Warnings\\n")
            for warning in self.warnings:
                report.append(f"⚠️  {warning}")
            report.append("")
        
        if not self.issues and not self.warnings:
            report.append("## ✅ All validations passed!\\n")
            report.append("Phase 11 architectural cleanup is complete and validated.")
        
        return "\\n".join(report)
    
    def run_all_validations(self) -> bool:
        """Run all Phase 11 validations."""
        print("🚀 Starting Phase 11 validation...")
        print()
        
        validations = [
            self.validate_folder_structure,
            self.validate_separation_of_concerns,
            self.validate_no_hardcoded_values,
            self.validate_model_registry_usage,
            self.validate_shared_utilities,
            self.validate_configuration_externalization,
        ]
        
        all_passed = True
        
        for validation in validations:
            if not validation():
                all_passed = False
            print()
        
        # Generate report
        report = self.generate_report()
        print(report)
        
        # Save report
        with open("phase11_validation_report.md", "w") as f:
            f.write(report)
        
        print("📄 Validation report saved to phase11_validation_report.md")
        
        return all_passed


def main():
    """Main validation runner."""
    validator = Phase11Validator()
    
    success = validator.run_all_validations()
    
    if success:
        print("✅ Phase 11 validation complete - all requirements met!")
        return 0
    else:
        print("❌ Phase 11 validation failed - issues found!")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
