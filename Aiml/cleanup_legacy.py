#!/usr/bin/env python3
"""
Cleanup script to remove legacy models and separate training artifacts.
Run this to prepare production deployment.
"""

import os
import shutil
from pathlib import Path

# Legacy models and artifacts to remove from production path
LEGACY_ARTIFACTS = [
    # Old model files
    "model_real_world_honest.joblib",
    "model_real_world_honest_v2.joblib",
    "binary_classifiers_v3.joblib",
    "label_encoder_real_honest.joblib",
    
    # Training datasets (keep only production models and configs)
    "Crop_recommendation.csv",
    "Crop_recommendation_synthetic_AplusB.csv",
    "Crop_recommendation_v2.csv",
    "Crop_recommendation_v2_raw.csv",
    "ICRISAT-District_Level_Data.csv",
    "crop_recommendation_synthetic_v1.csv",
    "data_core.csv",
    "real_world_merged_dataset.csv",
    "real_world_ml_dataset.csv",
    "final_with_season.csv",
    
    # Training notebooks and scripts
    "00_config.py",
    "01_dataset_generation.py",
    "02_baseline_model.py",
    "02_train_and_evaluate.py",
    "03_crossvalidation_eval.py",
    "03_real_world_validation.py",
    "04_data_augmentation.py",
    "05_trained_model_eval.py",
    "06_stress_test.py",
    "07_single_inference.py",
    "08_top3_recommendations.py",
    "09_real_world_pipeline.py",
    "10_honest_model.py",
    "final_stacked_model.py",
    "hybrid_model.py",
    "get_crop_features.py",
    "test_v2_pipeline.py",
    "_analyze_csvs.py",
    
    # Training metadata and reports
    "confusion_matrix.png",
    "confusion_matrix_real.png",
    "confusion_matrix_real_honest.png",
    "confusion_matrix_v2.png",
    "drift_report.json",
    "generation_metadata.json",
    "hybrid_metadata.json",
    "metrics_table.json",
    "real_world_validation_report.json",
    "reliability_metrics.json",
    "robustness_report.json",
    "training_log_v2.txt",
    "training_metadata.json",
    "training_metadata_real.json",
    "training_metadata_real_honest.json",
    
    # Calibration and other configs
    "calibration_config.json",
    "class_weights.json",
    "hybrid_v2_config.joblib",
    
    # Weather data (used only for training)
    "rainfall.csv",
    "temperature.csv",
    
    # Cache directories
    "__pycache__",
]

# Create training directory if it doesn't exist
TRAINING_DIR = Path("training_artifacts")
PRODUCTION_DIR = Path("production_models")

def cleanup_legacy():
    """Move legacy artifacts to training directory."""
    print("🧹 Cleaning up legacy artifacts...")
    
    # Create directories
    TRAINING_DIR.mkdir(exist_ok=True)
    PRODUCTION_DIR.mkdir(exist_ok=True)
    
    moved_count = 0
    
    for artifact in LEGACY_ARTIFACTS:
        src = Path(artifact)
        if src.exists():
            dst = TRAINING_DIR / artifact
            print(f"  Moving {artifact} -> training_artifacts/")
            shutil.move(str(src), str(dst))
            moved_count += 1
    
    print(f"✅ Moved {moved_count} legacy artifacts to training_artifacts/")

def organize_production():
    """Organize production models and configs."""
    print("📦 Organizing production models...")
    
    # Production artifacts to keep
    production_files = [
        "model_registry.json",
        "stacked_ensemble_v3.joblib",
        "label_encoder_v3.joblib",
        "stacked_v3_config.joblib",
        "model_rf.joblib",
        "label_encoder.joblib",
        "Nutrient.csv",
        "app.py",
        "predictors/",
        "requirements.txt",
        "README.md"
    ]
    
    for file_path in production_files:
        src = Path(file_path)
        if src.exists():
            if src.is_file():
                print(f"  Keeping production file: {file_path}")
            elif src.is_dir():
                print(f"  Keeping production directory: {file_path}")

def main():
    """Main cleanup function."""
    print("🚀 Starting Phase 6 cleanup...")
    print()
    
    cleanup_legacy()
    print()
    
    organize_production()
    print()
    
    print("✅ Phase 6 cleanup complete!")
    print("📁 Production-ready structure:")
    print("   - Production models: ./")
    print("   - Training artifacts: training_artifacts/")
    print("   - Legacy code removed")

if __name__ == "__main__":
    main()
