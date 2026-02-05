"""
Crop Recommendation Prediction Script
Loads pre-trained Random Forest model and makes predictions on new data.
"""

import os
import joblib
import pandas as pd
import numpy as np

# Paths
MODELS_DIR = 'models'
MODEL_PATH = os.path.join(MODELS_DIR, 'model_rf.joblib')
ENCODERS_PATH = os.path.join(MODELS_DIR, 'encoders.joblib')
DATA_CSV = 'final_with_season.csv'

# Load model and encoders
print('Loading pre-trained model and encoders...')
model = joblib.load(MODEL_PATH)
encoders_dict = joblib.load(ENCODERS_PATH)

ohe = encoders_dict['onehot']
le = encoders_dict['label']
season_columns = encoders_dict['season_columns']

print(f'[OK] Model loaded: {MODEL_PATH}')
print(f'[OK] Encoders loaded: {ENCODERS_PATH}')

# Example: Load data and make predictions
if os.path.exists(DATA_CSV):
    print(f'\nLoading example data from {DATA_CSV}...')
    df = pd.read_csv(DATA_CSV)
    
    # Extract numeric features
    numeric_cols = ['N', 'P', 'K', 'TEMPERATURE', 'HUMIDITY', 'PH', 'RAINFALL']
    X = df[numeric_cols].values
    
    # One-hot encode SEASON
    season_encoded = ohe.transform(df[['SEASON']])
    
    # Combine features
    X_full = np.hstack([X, season_encoded])
    
    # Make predictions
    predictions = model.predict(X_full)
    predicted_labels = le.inverse_transform(predictions)
    
    # Add to dataframe
    df['PREDICTED_CROP'] = predicted_labels
    
    print(f'[OK] Predictions generated for {len(df)} samples')
    print(f'\nFirst 10 predictions:')
    print(df[['N', 'P', 'K', 'TEMPERATURE', 'HUMIDITY', 'PH', 'RAINFALL', 'SEASON', 'PREDICTED_CROP']].head(10))
    
    # Optional: Save predictions
    output_file = 'predictions.csv'
    df.to_csv(output_file, index=False)
    print(f'\n[OK] Full predictions saved to {output_file}')
else:
    print(f'\n[WARNING] Data file {DATA_CSV} not found.')
    print('To make predictions, ensure final_with_season.csv is in the same directory.')

def predict_single(n, p, k, temperature, humidity, ph, rainfall, season):
    """
    Make a prediction for a single sample.
    
    Args:
        n, p, k: Nitrogen, Phosphorus, Potassium (numeric)
        temperature: Numeric
        humidity: Numeric
        ph: Numeric
        rainfall: Numeric
        season: One of ['ZAID', 'RABI', 'KHARIF']
    
    Returns:
        str: Predicted crop name
    """
    X = np.array([[n, p, k, temperature, humidity, ph, rainfall]])
    season_df = pd.DataFrame({'SEASON': [season]})
    season_encoded = ohe.transform(season_df)
    X_full = np.hstack([X, season_encoded])
    
    pred = model.predict(X_full)[0]
    return le.inverse_transform([pred])[0]

if __name__ == '__main__':
    print('\n' + '='*60)
    print('USAGE EXAMPLES:')
    print('='*60)
    print('\nExample 1: Predict a single crop')
    print('>>> from predict import predict_single')
    print('>>> crop = predict_single(30, 20, 10, 25.5, 60, 7.0, 100, "RABI")')
    print('>>> print(crop)')
    print('\nExample 2: Batch predictions from CSV')
    print('Place final_with_season.csv in the same directory and run this script.')
