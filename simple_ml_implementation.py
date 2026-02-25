# Simple ML Implementation - Crop Recommendation System
# Final Year Project - Clean and Maintainable

# ================================
# 1. Crop Registry - Mode Separation
# ================================

class CropRegistry:
    """Simple crop classification for clean mode separation"""
    
    # Real crops from actual dataset (22 crops)
    REAL_CROPS = {
        'rice', 'wheat', 'maize', 'cotton', 'groundnut', 'pigeonpea',
        'mustard', 'barley', 'millet', 'sugarcane', 'castor', 'chickpea',
        'linseed', 'safflower', 'sesamum', 'sorghum', 'soybean', 
        'sunflower', 'finger_millet', 'pearl_millet', 'blackgram'
    }
    
    # Synthetic crops from generated data (28 crops to make ~50 total)
    SYNTHETIC_CROPS = {
        'apple', 'banana', 'brinjal', 'carrot', 'citrus', 'coconut',
        'coffee', 'cucumber', 'date_palm', 'gourd', 'grapes', 
        'green_chilli', 'guava', 'jute', 'kidneybeans', 'lentil', 
        'mango', 'mothbeans', 'mungbean', 'muskmelon', 'okra', 
        'onion', 'papaya', 'pomegranate', 'potato', 'radish', 
        'sapota', 'spinach', 'tobacco', 'tomato', 'watermelon'
    }
    
    @classmethod
    def get_allowed_crops(cls, mode: str) -> set:
        """Get allowed crops for a mode"""
        if mode == 'real':
            return cls.REAL_CROPS
        elif mode == 'synthetic':
            return cls.SYNTHETIC_CROPS
        elif mode == 'both':
            return cls.REAL_CROPS | cls.SYNTHETIC_CROPS
        else:
            return cls.REAL_CROPS  # Default fallback
    
    @classmethod
    def validate_prediction(cls, crop: str, mode: str) -> bool:
        """Check if crop is valid for the mode"""
        allowed = cls.get_allowed_crops(mode)
        return crop.lower() in allowed
    
    @classmethod
    def get_crop_counts(cls) -> dict:
        """Get crop counts for documentation"""
        return {
            'real': len(cls.REAL_CROPS),
            'synthetic': len(cls.SYNTHETIC_CROPS),
            'both': len(cls.REAL_CROPS | cls.SYNTHETIC_CROPS)
        }

# ================================
# 2. Confidence Handler - FIXED
# ================================

import numpy as np

class ConfidenceHandler:
    """Simple confidence normalization without over-engineering"""
    
    @staticmethod
    def normalize_confidence(real_conf: float, synthetic_conf: float) -> tuple:
        """
        Normalize confidences to comparable scale.
        Simple approach: both models output 0-100, no complex calibration needed.
        """
        # Basic validation
        real_conf = np.clip(real_conf, 0, 100)
        synthetic_conf = np.clip(synthetic_conf, 0, 100)
        
        return real_conf, synthetic_conf
    
    @staticmethod
    def get_honest_confidence(confidence: float, source: str) -> dict:
        """
        Return honest confidence information
        """
        return {
            'confidence': round(confidence, 1),
            'source': source,  # 'real' or 'synthetic'
            'note': ConfidenceHandler._get_confidence_note(confidence)  # FIXED: Removed self
        }
    
    @staticmethod
    def _get_confidence_note(confidence: float) -> str:  # FIXED: Made static
        """Simple confidence interpretation"""
        if confidence >= 80:
            return "High confidence - reliable prediction"
        elif confidence >= 60:
            return "Medium confidence - consider alternatives"
        else:
            return "Low confidence - verify with expert knowledge"

# ================================
# 3. Hybrid Merger - Clean Logic
# ================================

from typing import List, Dict, Any

class HybridMerger:
    """Simple, transparent hybrid prediction merging"""
    
    def __init__(self, real_weight: float = 0.7, synthetic_weight: float = 0.3):
        # Simple weights - can be tuned
        self.real_weight = real_weight
        self.synthetic_weight = synthetic_weight
        
        # Ensure weights sum to 1
        total = self.real_weight + self.synthetic_weight
        self.real_weight /= total
        self.synthetic_weight /= total
    
    def merge_predictions(self, real_preds: List[Dict], 
                         synthetic_preds: List[Dict]) -> List[Dict]:
        """
        Simple merging logic:
        1. If crop appears in both, use weighted average
        2. If crop appears in only one, use that prediction
        3. Sort by final confidence
        """
        # Create crop mapping
        crop_predictions = {}
        
        # Add real predictions
        for pred in real_preds:
            crop = pred['crop'].lower()
            if CropRegistry.validate_prediction(crop, 'real'):
                crop_predictions[crop] = {
                    'real_conf': pred['confidence'],
                    'synthetic_conf': 0,
                    'sources': ['real']
                }
        
        # Add synthetic predictions
        for pred in synthetic_preds:
            crop = pred['crop'].lower()
            if CropRegistry.validate_prediction(crop, 'synthetic'):
                if crop in crop_predictions:
                    crop_predictions[crop]['synthetic_conf'] = pred['confidence']
                    crop_predictions[crop]['sources'].append('synthetic')
                else:
                    crop_predictions[crop] = {
                        'real_conf': 0,
                        'synthetic_conf': pred['confidence'],
                        'sources': ['synthetic']
                    }
        
        # Calculate merged confidence
        merged_predictions = []
        for crop, confs in crop_predictions.items():
            if confs['real_conf'] > 0 and confs['synthetic_conf'] > 0:
                # Weighted average for crops in both models
                merged_conf = (self.real_weight * confs['real_conf'] + 
                              self.synthetic_weight * confs['synthetic_conf'])
                source_note = f"Combined (real: {confs['real_conf']:.1f}%, synthetic: {confs['synthetic_conf']:.1f}%)"
            elif confs['real_conf'] > 0:
                # Only in real model
                merged_conf = confs['real_conf']
                source_note = "Real model only"
            else:
                # Only in synthetic model
                merged_conf = confs['synthetic_conf']
                source_note = "Synthetic model only"
            
            merged_predictions.append({
                'crop': crop,
                'confidence': round(merged_conf, 1),
                'sources': confs['sources'],
                'source_note': source_note,
                'honest_confidence': ConfidenceHandler.get_honest_confidence(merged_conf, 'hybrid')
            })
        
        # Sort by confidence and return top results
        merged_predictions.sort(key=lambda x: x['confidence'], reverse=True)
        return merged_predictions

# ================================
# 4. Feature Validator - Basic Checks
# ================================

class FeatureValidator:
    """Simple input validation for crop recommendations"""
    
    # Basic feature ranges based on agricultural knowledge
    FEATURE_RANGES = {
        'N': (0, 150),      # Nitrogen (kg/ha)
        'P': (0, 150),      # Phosphorus (kg/ha)
        'K': (0, 300),      # Potassium (kg/ha)
        'temperature': (0, 50),  # Temperature (°C)
        'humidity': (0, 100),    # Humidity (%)
        'ph': (0, 14),          # Soil pH
        'rainfall': (0, 3000),   # Rainfall (mm)
        'moisture': (0, 100),    # Soil moisture (%)
        'season': (0, 2),        # Season (0=Kharif, 1=Rabi, 2=Zaid)
        'soil_type': (0, 2),     # Soil type (0=sandy, 1=loamy, 2=clay)
        'irrigation': (0, 1)      # Irrigation (0=rainfed, 1=irrigated)
    }
    
    REQUIRED_FEATURES = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
    
    @classmethod
    def validate_input(cls, input_data: Dict) -> Dict[str, Any]:
        """Validate input data and return validation result"""
        errors = []
        warnings = []
        
        # Check required features
        for feature in cls.REQUIRED_FEATURES:
            if feature not in input_data:
                errors.append(f"Missing required feature: {feature}")
            elif input_data[feature] is None:
                errors.append(f"Feature {feature} cannot be None")
        
        # Validate feature ranges
        for feature, value in input_data.items():
            if feature in cls.FEATURE_RANGES and value is not None:
                min_val, max_val = cls.FEATURE_RANGES[feature]
                if not (min_val <= value <= max_val):
                    errors.append(f"{feature} value {value} outside valid range [{min_val}, {max_val}]")
        
        # Basic agricultural sanity checks
        if 'temperature' in input_data and 'humidity' in input_data:
            temp = input_data['temperature']
            humidity = input_data['humidity']
            if temp > 40 and humidity < 30:
                warnings.append("High temperature with low humidity - unusual combination")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @classmethod
    def ensure_feature_consistency(cls, input_data: Dict) -> Dict:
        """Ensure consistent feature format"""
        # Convert to lowercase keys for consistency
        consistent_data = {}
        for key, value in input_data.items():
            consistent_data[key.lower()] = value
        
        # Add default values for optional features
        defaults = {
            'moisture': 50.0,
            'season': None,  # Will be inferred
            'soil_type': 1,  # Default to loamy
            'irrigation': 0   # Default to rainfed
        }
        
        for feature, default_value in defaults.items():
            if feature not in consistent_data or consistent_data[feature] is None:
                consistent_data[feature] = default_value
        
        return consistent_data

# ================================
# 5. Model Version Labeling
# ================================

from datetime import datetime
import json

class ModelVersion:
    """Simple model version tracking"""
    
    def __init__(self, model_type: str, version: str, description: str = ""):
        self.model_type = model_type  # 'real', 'synthetic', 'hybrid'
        self.version = version
        self.description = description
        self.created_at = datetime.now().isoformat()
        self.metadata = {
            'model_type': model_type,
            'version': version,
            'description': description,
            'created_at': self.created_at,
            'training_dataset': self._get_dataset_info(model_type),
            'num_classes': self._get_num_classes(model_type)
        }
    
    def _get_dataset_info(self, model_type: str) -> str:
        """Get dataset information for model type"""
        if model_type == 'real':
            return "Real agricultural dataset (22 crops)"
        elif model_type == 'synthetic':
            return "Synthetic dataset (28 crops) - biologically inspired"
        else:
            return "Hybrid combination of real and synthetic models"
    
    def _get_num_classes(self, model_type: str) -> int:
        """Get number of classes for model type"""
        counts = CropRegistry.get_crop_counts()
        return counts.get(model_type, 0)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return self.metadata.copy()

# Current model versions
CURRENT_VERSIONS = {
    'real': ModelVersion('real', '1.0.0', 'Real dataset model with 22 crops'),
    'synthetic': ModelVersion('synthetic', '1.0.0', 'Synthetic dataset model with 28 crops'),
    'hybrid': ModelVersion('hybrid', '1.0.0', 'Hybrid model combining real and synthetic predictions')
}

# ================================
# 6. Simple Metrics Storage - FIXED
# ================================

class SimpleMetricsStorage:
    """Simple metrics storage for student project"""
    
    def __init__(self, metrics_file: str = "model_metrics.json"):
        self.metrics_file = metrics_file
        self.metrics_data = self._load_metrics()
    
    def _load_metrics(self) -> Dict:
        """Load existing metrics from file"""
        try:
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'models': {}, 'evaluations': []}
    
    def save_metrics(self):
        """Save metrics to file"""
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics_data, f, indent=2)
    
    def record_model_evaluation(self, model_type: str, version: str, 
                              metrics: Dict[str, float]):
        """Record model evaluation metrics"""
        evaluation_record = {
            'model_type': model_type,
            'version': version,
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics
        }
        
        self.metrics_data['evaluations'].append(evaluation_record)
        
        # Update latest metrics for model
        if model_type not in self.metrics_data['models']:
            self.metrics_data['models'][model_type] = {}
        
        self.metrics_data['models'][model_type]['latest_version'] = version
        self.metrics_data['models'][model_type]['latest_metrics'] = metrics
        self.metrics_data['models'][model_type]['last_evaluation'] = datetime.now().isoformat()
        
        self.save_metrics()
    
    def get_model_metrics(self, model_type: str) -> Dict:
        """Get latest metrics for a model"""
        return self.metrics_data['models'].get(model_type, {})

# FIXED: Simple evaluation function with correct Top-3 accuracy
def evaluate_model_simple(y_true: List, y_pred: List, y_pred_proba: List, label_encoder=None) -> Dict[str, float]:
    """Simple model evaluation with correct Top-3 accuracy"""
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support
    
    accuracy = accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='weighted')
    
    # FIXED: Correct Top-3 accuracy calculation
    top3_accuracy = 0.0
    if y_pred_proba and label_encoder:
        top3_correct = 0
        for i, true_class in enumerate(y_true):
            # Get true class index
            true_class_idx = list(label_encoder.classes_).index(true_class)
            
            # Get top 3 predicted class indices
            top3_indices = sorted(range(len(y_pred_proba[i])), 
                                 key=lambda x: y_pred_proba[i][x], reverse=True)[:3]
            
            # Check if true class index is in top 3 predictions
            if true_class_idx in top3_indices:
                top3_correct += 1
        
        top3_accuracy = top3_correct / len(y_true)
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'top3_accuracy': top3_accuracy
    }

# ================================
# 7. Integration with Existing System
# ================================

# Initialize global components
hybrid_merger = HybridMerger()
metrics_storage = SimpleMetricsStorage()

def predict_top_crops_simple(input_data: Dict, mode: str = 'real', top_n: int = 3) -> Dict:
    """
    Simple prediction function with validation and clean mode separation
    """
    # Validate input
    validation_result = FeatureValidator.validate_input(input_data)
    if not validation_result['valid']:
        raise ValueError(f"Invalid input: {validation_result['errors']}")
    
    # Ensure feature consistency
    consistent_input = FeatureValidator.ensure_feature_consistency(input_data)
    
    # Route to appropriate mode
    if mode == 'real':
        result = _predict_via_real(consistent_input, top_n)
    elif mode == 'synthetic':
        result = _predict_via_synthetic(consistent_input, top_n)
    elif mode == 'both':
        # Get predictions from both models
        real_result = _predict_via_real(consistent_input, top_n)
        synthetic_result = _predict_via_synthetic(consistent_input, top_n)
        
        # Merge with honest confidence handling
        merged_predictions = hybrid_merger.merge_predictions(
            real_result['predictions'], synthetic_result['predictions']
        )
        
        result = {
            'mode': 'both',
            'predictions': merged_predictions[:top_n],
            'model_info': {
                'type': 'hybrid',
                'version': CURRENT_VERSIONS['hybrid'].version,
                'description': CURRENT_VERSIONS['hybrid'].description
            },
            'crop_counts': CropRegistry.get_crop_counts()
        }
    else:
        raise ValueError(f"Invalid mode: {mode}. Use 'real', 'synthetic', or 'both'")
    
    # Add model version info and warnings
    result['model_version'] = CURRENT_VERSIONS[mode].to_dict()
    result['input_warnings'] = validation_result['warnings']
    result['crop_counts'] = CropRegistry.get_crop_counts()
    
    return result

def _predict_via_real(input_data: Dict, top_n: int) -> Dict:
    """Real model prediction with validation"""
    # Call your existing real model prediction
    # This is a placeholder - integrate with your actual model
    predictions = [
        {'crop': 'rice', 'confidence': 85.5},
        {'crop': 'wheat', 'confidence': 78.2},
        {'crop': 'maize', 'confidence': 72.1}
    ]
    
    # Validate predictions belong to real crops
    valid_predictions = []
    for pred in predictions:
        if CropRegistry.validate_prediction(pred['crop'], 'real'):
            pred['honest_confidence'] = ConfidenceHandler.get_honest_confidence(
                pred['confidence'], 'real'
            )
            valid_predictions.append(pred)
    
    return {
        'mode': 'real',
        'predictions': valid_predictions[:top_n],
        'model_info': {
            'type': 'real',
            'version': CURRENT_VERSIONS['real'].version,
            'description': CURRENT_VERSIONS['real'].description
        }
    }

def _predict_via_synthetic(input_data: Dict, top_n: int) -> Dict:
    """Synthetic model prediction with validation"""
    # Call your existing synthetic model prediction
    # This is a placeholder - integrate with your actual model
    predictions = [
        {'crop': 'apple', 'confidence': 75.3},
        {'crop': 'banana', 'confidence': 68.7},
        {'crop': 'brinjal', 'confidence': 65.2}
    ]
    
    # Validate predictions belong to synthetic crops
    valid_predictions = []
    for pred in predictions:
        if CropRegistry.validate_prediction(pred['crop'], 'synthetic'):
            pred['honest_confidence'] = ConfidenceHandler.get_honest_confidence(
                pred['confidence'], 'synthetic'
            )
            valid_predictions.append(pred)
    
    return {
        'mode': 'synthetic',
        'predictions': valid_predictions[:top_n],
        'model_info': {
            'type': 'synthetic',
            'version': CURRENT_VERSIONS['synthetic'].version,
            'description': CURRENT_VERSIONS['synthetic'].description
        }
    }

# ================================
# 8. Example Usage
# ================================

if __name__ == "__main__":
    # Example input
    test_input = {
        'N': 50,
        'P': 30,
        'K': 40,
        'temperature': 25,
        'humidity': 65,
        'ph': 6.5,
        'rainfall': 1000
    }
    
    print("=== Crop Recommendation System ===")
    print(f"Crop counts: {CropRegistry.get_crop_counts()}")
    print()
    
    # Test each mode
    for mode in ['real', 'synthetic', 'both']:
        print(f"--- {mode.upper()} MODE ---")
        try:
            result = predict_top_crops_simple(test_input, mode=mode)
            print(f"Status: Success")
            print(f"Model: {result['model_info']['type']} v{result['model_info']['version']}")
            print("Predictions:")
            for i, pred in enumerate(result['predictions'], 1):
                print(f"  {i}. {pred['crop']} - {pred['confidence']}% ({pred['honest_confidence']['note']})")
            if result.get('input_warnings'):
                print(f"Warnings: {result['input_warnings']}")
        except Exception as e:
            print(f"Error: {e}")
        print()
