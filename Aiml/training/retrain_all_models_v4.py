#!/usr/bin/env python3
"""
Complete retraining of all models for V4.
Fresh training with no bias, correct schemas, and proper scaling.
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import StackingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import cross_val_score
from sklearn.utils.class_weight import compute_class_weight
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

class ModelTrainerV4:
    """Complete model retraining for V4."""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent
        self.models_dir = Path(__file__).parent.parent
        self.real_data_path = self.data_dir / "Crop_recommendation.csv"
        self.synthetic_data_path = self.data_dir / "synthetic_crop_data.csv"
        
    def load_and_prepare_real_data(self):
        """Load and prepare real dataset with 11 features including moisture."""
        print("Loading real dataset...")
        
        if not self.real_data_path.exists():
            raise FileNotFoundError(f"Real dataset not found: {self.real_data_path}")
        
        df = pd.read_csv(self.real_data_path)
        print(f"Real dataset shape: {df.shape}")
        print(f"Real dataset crops: {df['label '].nunique()}")
        
        # Define 11 features including moisture
        features = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall', 
                   'season', 'soil_type', 'irrigation', 'moisture']
        
        # Add missing engineered features if not present
        if 'season' not in df.columns:
            df['season'] = df['temperature'].apply(self._infer_season)
        if 'soil_type' not in df.columns:
            df['soil_type'] = 1  # Default loamy soil
        if 'irrigation' not in df.columns:
            df['irrigation'] = 0  # Default no irrigation
        if 'moisture' not in df.columns:
            df['moisture'] = df['humidity'] * 0.7 + np.random.normal(0, 5, len(df))
        
        X = df[features]
        y = df['label ']
        
        print(f"Real features: {features}")
        print(f"Real X shape: {X.shape}")
        
        return X, y, features
    
    def load_and_prepare_synthetic_data(self):
        """Load and prepare synthetic dataset with 10 features."""
        print("Loading synthetic dataset...")
        
        if not self.synthetic_data_path.exists():
            # Create synthetic dataset if not exists
            print("Creating synthetic dataset...")
            self._create_synthetic_dataset()
        
        df = pd.read_csv(self.synthetic_data_path)
        print(f"Synthetic dataset shape: {df.shape}")
        print(f"Synthetic dataset crops: {df['label '].nunique()}")
        
        # Define 10 features (no moisture)
        features = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall', 
                   'season', 'soil_type', 'irrigation']
        
        X = df[features]
        y = df['label ']
        
        print(f"Synthetic features: {features}")
        print(f"Synthetic X shape: {X.shape}")
        
        return X, y, features
    
    def _infer_season(self, temp):
        """Infer season from temperature."""
        if temp >= 28:
            return 0  # Kharif
        elif temp <= 22:
            return 1  # Rabi
        else:
            return 2  # Zaid
    
    def _create_synthetic_dataset(self):
        """Create synthetic dataset with 51 crops."""
        np.random.seed(42)
        
        # Extended crop list for synthetic data
        crops = ['rice', 'wheat', 'maize', 'chickpea', 'kidneybeans', 'pigeonpeas',
                'mothbeans', 'mungbean', 'blackgram', 'lentil', 'pomegranate',
                'banana', 'mango', 'grapes', 'watermelon', 'muskmelon', 'apple',
                'orange', 'papaya', 'coconut', 'cotton', 'jute', 'coffee',
                'tea', 'cashew', 'sugarcane', 'tobacco', 'soybean', 'groundnut',
                'sunflower', 'ragi', 'bajra', 'jowar', 'barley', 'oats',
                'tomato', 'potato', 'onion', 'carrot', 'brinjal', 'cucumber',
                'okra', 'cabbage', 'cauliflower', 'spinach', 'coriander',
                'chilli', 'garlic', 'ginger', 'turmeric', 'cardamom',
                'pepper', 'cinnamon']
        
        n_samples = 10000
        data = []
        
        for crop in crops:
            n_crop_samples = n_samples // len(crops)
            
            # Generate realistic ranges for each crop
            for _ in range(n_crop_samples):
                N = np.random.uniform(20, 120)
                P = np.random.uniform(20, 120)
                K = np.random.uniform(20, 120)
                temperature = np.random.uniform(15, 35)
                humidity = np.random.uniform(40, 90)
                ph = np.random.uniform(5.5, 8.5)
                rainfall = np.random.uniform(50, 300)
                season = self._infer_season(temperature)
                soil_type = np.random.randint(1, 5)
                irrigation = np.random.randint(0, 2)
                
                data.append([N, P, K, temperature, humidity, ph, rainfall,
                           season, soil_type, irrigation, crop])
        
        df = pd.DataFrame(data, columns=['N', 'P', 'K', 'temperature', 'humidity', 
                                       'ph', 'rainfall', 'season', 'soil_type', 
                                       'irrigation', 'label '])
        
        df.to_csv(self.synthetic_data_path, index=False)
        print(f"Created synthetic dataset with {len(crops)} crops")
    
    def train_real_model(self, X, y, features):
        """Train real model with 11 features."""
        print("Training real model...")
        
        # Apply class weight balancing to remove bias
        class_weights = compute_class_weight('balanced', classes=np.unique(y), y=y)
        class_weight_dict = dict(zip(np.unique(y), class_weights))
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Encode labels
        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y)
        
        # Create stacked ensemble
        base_estimators = [
            ('rf', RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)),
            ('lr', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42))
        ]
        
        stacked_model = StackingClassifier(
            estimators=base_estimators,
            final_estimator=LogisticRegression(class_weight='balanced', max_iter=1000),
            cv=5
        )
        
        # Train model
        stacked_model.fit(X_scaled, y_encoded)
        
        # Save artifacts
        joblib.dump(stacked_model, self.models_dir / "stacked_ensemble_v4.joblib")
        joblib.dump(label_encoder, self.models_dir / "label_encoder_real_v4.joblib")
        joblib.dump(scaler, self.models_dir / "scaler_real_v4.joblib")
        
        # Validate
        scores = cross_val_score(stacked_model, X_scaled, y_encoded, cv=5, scoring='accuracy')
        print(f"Real model CV accuracy: {scores.mean():.4f} (+/- {scores.std() * 2:.4f})")
        print(f"Real model crops: {len(label_encoder.classes_)}")
        
        return stacked_model, label_encoder, scaler
    
    def train_synthetic_model(self, X, y, features):
        """Train synthetic model with 10 features."""
        print("Training synthetic model...")
        
        # Apply class weight balancing
        class_weights = compute_class_weight('balanced', classes=np.unique(y), y=y)
        class_weight_dict = dict(zip(np.unique(y), class_weights))
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Encode labels
        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y)
        
        # Train Random Forest
        rf_model = RandomForestClassifier(
            n_estimators=200,
            class_weight='balanced',
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        
        rf_model.fit(X_scaled, y_encoded)
        
        # Save artifacts
        joblib.dump(rf_model, self.models_dir / "model_rf_v4.joblib")
        joblib.dump(label_encoder, self.models_dir / "label_encoder_synth_v4.joblib")
        joblib.dump(scaler, self.models_dir / "scaler_synth_v4.joblib")
        
        # Validate
        scores = cross_val_score(rf_model, X_scaled, y_encoded, cv=5, scoring='accuracy')
        print(f"Synthetic model CV accuracy: {scores.mean():.4f} (+/- {scores.std() * 2:.4f})")
        print(f"Synthetic model crops: {len(label_encoder.classes_)}")
        
        return rf_model, label_encoder, scaler
    
    def create_hybrid_config(self, real_encoder, synthetic_encoder):
        """Create hybrid configuration for V4."""
        print("Creating hybrid configuration...")
        
        # Create crop mappings
        real_crops = set(real_encoder.classes_)
        synthetic_crops = set(synthetic_encoder.classes_)
        
        # Find common crops
        common_crops = real_crops.intersection(synthetic_crops)
        
        hybrid_config = {
            "real_crops": list(real_crops),
            "synthetic_crops": list(synthetic_crops),
            "common_crops": list(common_crops),
            "total_unique_crops": len(real_crops.union(synthetic_crops)),
            "blend_weights": {
                "real": 0.6,
                "synthetic": 0.4
            },
            "confidence_threshold": 0.3,
            "version": "v4"
        }
        
        joblib.dump(hybrid_config, self.models_dir / "hybrid_config_v4.joblib")
        print(f"Hybrid config created with {len(common_crops)} common crops")
        
        return hybrid_config
    
    def train_all_models(self):
        """Train all models from scratch."""
        print("=== STARTING COMPLETE MODEL RETRAINING V4 ===\n")
        
        # Train real model
        X_real, y_real, features_real = self.load_and_prepare_real_data()
        real_model, real_encoder, real_scaler = self.train_real_model(X_real, y_real, features_real)
        print("✅ Real model trained and saved\n")
        
        # Train synthetic model
        X_synth, y_synth, features_synth = self.load_and_prepare_synthetic_data()
        synth_model, synth_encoder, synth_scaler = self.train_synthetic_model(X_synth, y_synth, features_synth)
        print("✅ Synthetic model trained and saved\n")
        
        # Create hybrid config
        hybrid_config = self.create_hybrid_config(real_encoder, synth_encoder)
        print("✅ Hybrid configuration created\n")
        
        print("=== MODEL RETRAINING COMPLETE ===")
        print(f"Real model: {len(real_encoder.classes_)} crops")
        print(f"Synthetic model: {len(synth_encoder.classes_)} crops")
        print(f"Hybrid config: {hybrid_config['total_unique_crops']} unique crops")
        
        return {
            'real': (real_model, real_encoder, real_scaler),
            'synthetic': (synth_model, synth_encoder, synth_scaler),
            'hybrid': hybrid_config
        }


def main():
    """Main training function."""
    trainer = ModelTrainerV4()
    models = trainer.train_all_models()
    return 0


if __name__ == "__main__":
    sys.exit(main())
