"""
Advanced Dataset Configuration - Production-Ready Synthetic Data Generation
============================================================================
This replaces the basic linspace-based generation with biologically realistic
synthetic data generation using Gaussian distributions, ecological clustering,
and asymmetric noise patterns.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dataset_config")

class AdvancedDatasetConfig:
    """Configuration for biologically realistic synthetic dataset generation"""
    
    def __init__(self):
        # Crop parameters with realistic distributions
        self.CROP_PARAMS = {
            # Format: crop_name: {mean, std, min, max} for each parameter
            'rice': {
                'n': {'mean': 80, 'std': 20, 'min': 40, 'max': 120},
                'p': {'mean': 40, 'std': 15, 'min': 20, 'max': 60},
                'k': {'mean': 40, 'std': 15, 'min': 20, 'max': 60},
                'temperature': {'mean': 26, 'std': 3, 'min': 22, 'max': 32},
                'humidity': {'mean': 75, 'std': 10, 'min': 60, 'max': 90},
                'ph': {'mean': 6.2, 'std': 0.8, 'min': 5.5, 'max': 7.0},
                'rainfall': {'mean': 200, 'std': 80, 'min': 100, 'max': 350},
                'season_preference': [0],  # Kharif
                'soil_preference': [1, 2],  # Loamy, clay
                'irrigation_preference': [0, 1],  # Both rainfed and irrigated
                'sample_weight': 1.2  # Higher weight for common crop
            },
            'wheat': {
                'n': {'mean': 85, 'std': 18, 'min': 50, 'max': 120},
                'p': {'mean': 35, 'std': 12, 'min': 20, 'max': 55},
                'k': {'mean': 35, 'std': 12, 'min': 20, 'max': 55},
                'temperature': {'mean': 18, 'std': 4, 'min': 12, 'max': 24},
                'humidity': {'mean': 60, 'std': 12, 'min': 45, 'max': 75},
                'ph': {'mean': 6.5, 'std': 0.7, 'min': 6.0, 'max': 7.5},
                'rainfall': {'mean': 80, 'std': 40, 'min': 40, 'max': 150},
                'season_preference': [1],  # Rabi
                'soil_preference': [0, 1],  # Sandy, loamy
                'irrigation_preference': [1],  # Primarily irrigated
                'sample_weight': 1.1
            },
            'maize': {
                'n': {'mean': 90, 'std': 22, 'min': 50, 'max': 130},
                'p': {'mean': 45, 'std': 15, 'min': 25, 'max': 65},
                'k': {'mean': 45, 'std': 15, 'min': 25, 'max': 65},
                'temperature': {'mean': 24, 'std': 4, 'min': 18, 'max': 30},
                'humidity': {'mean': 65, 'std': 12, 'min': 50, 'max': 80},
                'ph': {'mean': 6.0, 'std': 0.8, 'min': 5.5, 'max': 7.0},
                'rainfall': {'mean': 120, 'std': 50, 'min': 60, 'max': 200},
                'season_preference': [0, 2],  # Kharif, Zaid
                'soil_preference': [1],  # Loamy
                'irrigation_preference': [0, 1],
                'sample_weight': 1.0
            },
            'cotton': {
                'n': {'mean': 70, 'std': 18, 'min': 40, 'max': 100},
                'p': {'mean': 50, 'std': 15, 'min': 30, 'max': 70},
                'k': {'mean': 50, 'std': 15, 'min': 30, 'max': 70},
                'temperature': {'mean': 27, 'std': 3, 'min': 22, 'max': 32},
                'humidity': {'mean': 55, 'std': 10, 'min': 40, 'max': 70},
                'ph': {'mean': 6.3, 'std': 0.7, 'min': 5.8, 'max': 7.0},
                'rainfall': {'mean': 100, 'std': 40, 'min': 50, 'max': 160},
                'season_preference': [0],  # Kharif
                'soil_preference': [0, 1],  # Sandy, loamy
                'irrigation_preference': [1],  # Irrigated
                'sample_weight': 0.8
            },
            'sugarcane': {
                'n': {'mean': 100, 'std': 25, 'min': 60, 'max': 140},
                'p': {'mean': 60, 'std': 18, 'min': 35, 'max': 85},
                'k': {'mean': 60, 'std': 18, 'min': 35, 'max': 85},
                'temperature': {'mean': 25, 'std': 3, 'min': 20, 'max': 30},
                'humidity': {'mean': 70, 'std': 10, 'min': 55, 'max': 85},
                'ph': {'mean': 6.5, 'std': 0.6, 'min': 6.0, 'max': 7.2},
                'rainfall': {'mean': 150, 'std': 60, 'min': 80, 'max': 250},
                'season_preference': [0, 2],  # Kharif, Zaid
                'soil_preference': [1, 2],  # Loamy, clay
                'irrigation_preference': [1],  # Irrigated
                'sample_weight': 0.7
            },
            # Add more crops with realistic parameters...
            'groundnut': {
                'n': {'mean': 60, 'std': 15, 'min': 35, 'max': 85},
                'p': {'mean': 40, 'std': 12, 'min': 25, 'max': 55},
                'k': {'mean': 40, 'std': 12, 'min': 25, 'max': 55},
                'temperature': {'mean': 26, 'std': 3, 'min': 22, 'max': 30},
                'humidity': {'mean': 65, 'std': 10, 'min': 50, 'max': 80},
                'ph': {'mean': 6.2, 'std': 0.7, 'min': 5.7, 'max': 6.8},
                'rainfall': {'mean': 90, 'std': 35, 'min': 50, 'max': 140},
                'season_preference': [0, 2],  # Kharif, Zaid
                'soil_preference': [0, 1],  # Sandy, loamy
                'irrigation_preference': [0, 1],
                'sample_weight': 0.6
            },
            'pigeonpea': {
                'n': {'mean': 55, 'std': 14, 'min': 30, 'max': 80},
                'p': {'mean': 35, 'std': 10, 'min': 20, 'max': 50},
                'k': {'mean': 35, 'std': 10, 'min': 20, 'max': 50},
                'temperature': {'mean': 27, 'std': 3, 'min': 23, 'max': 31},
                'humidity': {'mean': 60, 'std': 12, 'min': 45, 'max': 75},
                'ph': {'mean': 6.0, 'std': 0.8, 'min': 5.5, 'max': 6.8},
                'rainfall': {'mean': 110, 'std': 45, 'min': 60, 'max': 170},
                'season_preference': [0],  # Kharif
                'soil_preference': [1],  # Loamy
                'irrigation_preference': [0],  # Rainfed
                'sample_weight': 0.5
            },
            'mustard': {
                'n': {'mean': 75, 'std': 16, 'min': 45, 'max': 105},
                'p': {'mean': 40, 'std': 12, 'min': 25, 'max': 55},
                'k': {'mean': 30, 'std': 10, 'min': 15, 'max': 45},
                'temperature': {'mean': 17, 'std': 3, 'min': 12, 'max': 22},
                'humidity': {'mean': 55, 'std': 10, 'min': 40, 'max': 70},
                'ph': {'mean': 6.3, 'std': 0.7, 'min': 5.8, 'max': 7.0},
                'rainfall': {'mean': 70, 'std': 30, 'min': 40, 'max': 110},
                'season_preference': [1],  # Rabi
                'soil_preference': [0, 1],  # Sandy, loamy
                'irrigation_preference': [0, 1],
                'sample_weight': 0.5
            },
            'barley': {
                'n': {'mean': 65, 'std': 15, 'min': 40, 'max': 90},
                'p': {'mean': 30, 'std': 10, 'min': 18, 'max': 42},
                'k': {'mean': 30, 'std': 10, 'min': 18, 'max': 42},
                'temperature': {'mean': 15, 'std': 3, 'min': 10, 'max': 20},
                'humidity': {'mean': 50, 'std': 10, 'min': 35, 'max': 65},
                'ph': {'mean': 6.7, 'std': 0.6, 'min': 6.2, 'max': 7.3},
                'rainfall': {'mean': 60, 'std': 25, 'min': 30, 'max': 90},
                'season_preference': [1],  # Rabi
                'soil_preference': [0, 1],  # Sandy, loamy
                'irrigation_preference': [0, 1],
                'sample_weight': 0.4
            },
            'millet': {
                'n': {'mean': 50, 'std': 12, 'min': 30, 'max': 70},
                'p': {'mean': 30, 'std': 8, 'min': 18, 'max': 42},
                'k': {'mean': 30, 'std': 8, 'min': 18, 'max': 42},
                'temperature': {'mean': 28, 'std': 3, 'min': 24, 'max': 32},
                'humidity': {'mean': 45, 'std': 10, 'min': 30, 'max': 60},
                'ph': {'mean': 6.0, 'std': 0.8, 'min': 5.5, 'max': 6.8},
                'rainfall': {'mean': 80, 'std': 30, 'min': 40, 'max': 120},
                'season_preference': [0],  # Kharif
                'soil_preference': [0],  # Sandy
                'irrigation_preference': [0],  # Rainfed
                'sample_weight': 0.4
            }
        }
        
        # Ecological clustering parameters
        self.ecological_clusters = {
            'cereals': ['rice', 'wheat', 'maize', 'barley', 'millet'],
            'legumes': ['groundnut', 'pigeonpea'],
            'cash_crops': ['cotton', 'sugarcane', 'mustard']
        }
        
        # Asymmetric noise patterns
        self.noise_patterns = {
            'high_nitrogen_crops': ['rice', 'wheat', 'maize', 'sugarcane'],
            'drought_tolerant': ['millet', 'groundnut', 'pigeonpea'],
            'water_loving': ['rice', 'sugarcane']
        }
        
        # Sample counts for class imbalance
        self.base_samples_per_class = 200
        self.imbalance_factor = 2.5  # Ratio between most and least common crops
        
    def generate_samples_for_crop(self, crop_name: str, n_samples: int) -> pd.DataFrame:
        """Generate realistic samples for a specific crop"""
        if crop_name not in self.CROP_PARAMS:
            raise ValueError(f"Unknown crop: {crop_name}")
        
        params = self.CROP_PARAMS[crop_name]
        samples = []
        
        for _ in range(n_samples):
            sample = {}
            
            # Generate core parameters with Gaussian distribution
            for param in ['n', 'p', 'k', 'temperature', 'humidity', 'ph', 'rainfall']:
                mean = params[param]['mean']
                std = params[param]['std']
                min_val = params[param]['min']
                max_val = params[param]['max']
                
                # Generate with Gaussian distribution and clip to valid range
                value = np.random.normal(mean, std)
                value = np.clip(value, min_val, max_val)
                sample[param] = value
            
            # Add ecological clustering effects
            sample = self._apply_ecological_effects(sample, crop_name)
            
            # Add asymmetric noise
            sample = self._apply_asymmetric_noise(sample, crop_name)
            
            # Add categorical features
            sample['season'] = np.random.choice(params['season_preference'])
            sample['soil_type'] = np.random.choice(params['soil_preference'])
            sample['irrigation'] = np.random.choice(params['irrigation_preference'])
            
            # Calculate moisture based on humidity and rainfall
            sample['moisture'] = self._calculate_moisture(sample['humidity'], sample['rainfall'])
            
            # Add label
            sample['label'] = crop_name
            
            samples.append(sample)
        
        return pd.DataFrame(samples)
    
    def _apply_ecological_effects(self, sample: dict, crop_name: str) -> dict:
        """Apply ecological clustering effects"""
        # Crops in the same cluster have some parameter correlations
        for cluster, crops in self.ecological_clusters.items():
            if crop_name in crops:
                if cluster == 'cereals':
                    # Cereals tend to have higher nitrogen requirements
                    sample['n'] *= np.random.uniform(1.0, 1.2)
                elif cluster == 'legumes':
                    # Legumes can fix nitrogen, so requirements are lower
                    sample['n'] *= np.random.uniform(0.8, 1.0)
                elif cluster == 'cash_crops':
                    # Cash crops often need more balanced nutrients
                    sample['p'] *= np.random.uniform(1.0, 1.15)
                    sample['k'] *= np.random.uniform(1.0, 1.15)
                break
        
        return sample
    
    def _apply_asymmetric_noise(self, sample: dict, crop_name: str) -> dict:
        """Apply asymmetric noise patterns"""
        # High nitrogen crops have more variability in N
        if crop_name in self.noise_patterns['high_nitrogen_crops']:
            sample['n'] += np.random.normal(0, sample['n'] * 0.1)
        
        # Drought tolerant crops can handle lower rainfall
        if crop_name in self.noise_patterns['drought_tolerant']:
            sample['rainfall'] *= np.random.uniform(0.7, 1.0)
        
        # Water loving crops have higher rainfall requirements
        if crop_name in self.noise_patterns['water_loving']:
            sample['rainfall'] *= np.random.uniform(1.0, 1.3)
        
        return sample
    
    def _calculate_moisture(self, humidity: float, rainfall: float) -> float:
        """Calculate soil moisture from humidity and rainfall"""
        # Empirical formula: moisture = 0.3*humidity + 0.01*min(rainfall, 500)
        moisture = humidity * 0.3 + min(rainfall, 500) * 0.01
        return np.clip(moisture, 0, 100)
    
    def generate_balanced_dataset(self, output_file: str = "Crop_recommendation_synthetic_advanced.csv"):
        """Generate a balanced synthetic dataset with realistic patterns"""
        logger.info("Generating advanced synthetic dataset...")
        
        all_data = []
        
        for crop_name, params in self.CROP_PARAMS.items():
            # Calculate sample count based on weight and imbalance
            weight = params.get('sample_weight', 1.0)
            n_samples = int(self.base_samples_per_class * weight)
            
            logger.info(f"Generating {n_samples} samples for {crop_name}")
            
            crop_data = self.generate_samples_for_crop(crop_name, n_samples)
            all_data.append(crop_data)
        
        # Combine all data
        final_dataset = pd.concat(all_data, ignore_index=True)
        
        # Shuffle the dataset
        final_dataset = final_dataset.sample(frac=1, random_state=42).reset_index(drop=True)
        
        # Save to CSV
        final_dataset.to_csv(output_file, index=False)
        
        logger.info(f"Generated dataset with {len(final_dataset)} samples")
        logger.info(f"Saved to: {output_file}")
        
        # Print dataset statistics
        print("\n" + "="*60)
        print("ADVANCED SYNTHETIC DATASET STATISTICS")
        print("="*60)
        print(f"Total samples: {len(final_dataset)}")
        print(f"Number of crops: {len(final_dataset['label'].unique())}")
        print(f"Features: {list(final_dataset.columns[:-1])}")  # Exclude label
        
        print("\nSamples per crop:")
        crop_counts = final_dataset['label'].value_counts().sort_values(ascending=False)
        for crop, count in crop_counts.items():
            print(f"{crop:12}: {count:4} samples")
        
        print("\nFeature ranges:")
        for col in ['n', 'p', 'k', 'temperature', 'humidity', 'ph', 'rainfall', 'moisture']:
            print(f"{col:12}: {final_dataset[col].min():6.2f} - {final_dataset[col].max():6.2f}")
        
        return final_dataset

def main():
    """Main function to generate the advanced synthetic dataset"""
    config = AdvancedDatasetConfig()
    dataset = config.generate_balanced_dataset()
    
    logger.info("Advanced synthetic dataset generation completed successfully")

if __name__ == "__main__":
    main()
