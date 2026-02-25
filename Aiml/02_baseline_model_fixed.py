"""
Baseline Model Training - Aligned with Production Features
==========================================================
This script trains a baseline model using the same 11 features as production
to ensure consistent evaluation and fair comparison.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.preprocessing import LabelEncoder
import joblib
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("baseline_model")

def infer_season(temperature: float) -> int:
    """Infer season from temperature"""
    if temperature >= 28: 
        return 0  # Kharif
    elif temperature <= 22: 
        return 1  # Rabi
    else: 
        return 2  # Zaid

def load_and_validate_dataset(filepath: str) -> pd.DataFrame:
    """Load and validate dataset structure"""
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Dataset not found: {filepath}")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")
    
    # Check required columns
    required_cols = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall', 'label']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    return df

def add_production_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add the same features used in production"""
    df = df.copy()
    
    # Add season (inferred from temperature)
    df['season'] = df['temperature'].apply(infer_season)
    
    # Add soil_type (default to loamy = 1 for baseline)
    # In production, this would come from user input or soil analysis
    df['soil_type'] = 1  # Default: loamy soil
    
    # Add irrigation (default to rainfed = 0 for baseline)
    # In production, this would come from user input
    df['irrigation'] = 0  # Default: rainfed
    
    # Add moisture (estimated from humidity and rainfall)
    # Simple heuristic: moisture = 0.3 * humidity + 0.01 * min(rainfall, 500)
    df['moisture'] = df['humidity'] * 0.3 + df['rainfall'].apply(lambda x: min(x, 500) * 0.01)
    df['moisture'] = df['moisture'].clip(0, 100)  # Ensure 0-100 range
    
    logger.info("Added production features: season, soil_type, irrigation, moisture")
    return df

def train_baseline_model(df: pd.DataFrame, save_model: bool = True):
    """Train baseline model with production-aligned features"""
    
    # Production feature set (11 features)
    PRODUCTION_FEATURES = [
        'n', 'p', 'k', 'temperature', 'humidity', 'ph', 'rainfall',
        'season', 'soil_type', 'irrigation', 'moisture'
    ]
    
    # Convert column names to match production (lowercase)
    df.columns = [col.lower() for col in df.columns]
    
    # Add production features
    df = add_production_features(df)
    
    # Validate all production features exist
    missing_features = [f for f in PRODUCTION_FEATURES if f not in df.columns]
    if missing_features:
        raise ValueError(f"Missing production features: {missing_features}")
    
    # Prepare features and target
    X = df[PRODUCTION_FEATURES]
    y = df['label']
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    # Train-test split with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded,
        test_size=0.2,
        random_state=42,
        stratify=y_encoded
    )
    
    logger.info(f"Training set: {len(X_train)} samples")
    logger.info(f"Test set: {len(X_test)} samples")
    logger.info(f"Number of classes: {len(label_encoder.classes_)}")
    
    # Train Random Forest with production-like parameters
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'  # Handle class imbalance
    )
    
    model.fit(X_train, y_train)
    
    # Predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)
    
    # Evaluation
    accuracy = accuracy_score(y_test, y_pred)
    
    # Calculate top-3 accuracy (important for crop recommendation)
    top3_accuracies = []
    for i, true_class in enumerate(y_test):
        top3_classes = np.argsort(y_pred_proba[i])[-3:][::-1]
        top3_accuracies.append(1 if true_class in top3_classes else 0)
    top3_accuracy = np.mean(top3_accuracies)
    
    print("\n" + "="*60)
    print("BASELINE MODEL EVALUATION (Production-Aligned)")
    print("="*60)
    print(f"Top-1 Accuracy: {accuracy:.4f}")
    print(f"Top-3 Accuracy: {top3_accuracy:.4f}")
    print(f"Number of Features: {len(PRODUCTION_FEATURES)}")
    print(f"Number of Classes: {len(label_encoder.classes_)}")
    
    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)
    
    print("\nClassification Report:")
    class_names = label_encoder.inverse_transform(range(len(label_encoder.classes_)))
    print(classification_report(y_test, y_pred, target_names=class_names))
    
    # Feature importance
    importances = pd.Series(
        model.feature_importances_,
        index=PRODUCTION_FEATURES
    ).sort_values(ascending=False)
    
    print("\nFeature Importances:")
    for feature, importance in importances.items():
        print(f"{feature:12}: {importance:.4f}")
    
    # Save model artifacts if requested
    if save_model:
        artifacts = {
            'model': model,
            'label_encoder': label_encoder,
            'features': PRODUCTION_FEATURES,
            'feature_importances': importances.to_dict(),
            'metrics': {
                'accuracy': accuracy,
                'top3_accuracy': top3_accuracy,
                'n_classes': len(label_encoder.classes_),
                'n_features': len(PRODUCTION_FEATURES)
            }
        }
        
        joblib.dump(artifacts, 'baseline_model_production_aligned.joblib')
        logger.info("Saved baseline model artifacts to 'baseline_model_production_aligned.joblib'")
    
    return {
        'model': model,
        'label_encoder': label_encoder,
        'features': PRODUCTION_FEATURES,
        'accuracy': accuracy,
        'top3_accuracy': top3_accuracy,
        'feature_importances': importances
    }

def main():
    """Main training pipeline"""
    try:
        # Load dataset (try synthetic v2 first, then fallback to v1)
        dataset_files = [
            "Crop_recommendation_v2.csv",
            "crop_recommendation_synthetic_v1.csv"
        ]
        
        df = None
        for filepath in dataset_files:
            try:
                df = load_and_validate_dataset(filepath)
                logger.info(f"Using dataset: {filepath}")
                break
            except FileNotFoundError:
                continue
        
        if df is None:
            raise FileNotFoundError("No valid dataset found")
        
        # Train and evaluate
        results = train_baseline_model(df, save_model=True)
        
        logger.info("Baseline model training completed successfully")
        
    except Exception as e:
        logger.error(f"Baseline model training failed: {e}")
        raise

if __name__ == "__main__":
    main()
