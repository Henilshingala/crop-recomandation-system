CROP RECOMMENDATION MODEL - PRODUCTION DEPLOYMENT
===================================================

OVERVIEW
--------
This package contains a trained Random Forest model for crop recommendation
based on soil nutrients and environmental conditions.

MODEL PERFORMANCE
-----------------
- Overall Test Accuracy: 90.80%
- Base Model: RandomForestClassifier
- Best Hyperparameters:
  * n_estimators: 500
  * max_depth: 20
  * min_samples_split: 5
  * min_samples_leaf: 1
  * max_features: log2

PACKAGE CONTENTS
----------------
- model_rf.joblib       : Trained Random Forest model
- encoders.joblib      : OneHotEncoder and LabelEncoder for features/labels
- final_with_season.csv: Reference dataset with all 56 crop classes
- predict.py           : Prediction script with usage examples
- README.txt           : This file

REQUIREMENTS
------------
- Python 3.7+
- scikit-learn
- pandas
- numpy
- joblib

INSTALLATION
------------
1. Extract crop_recommendation_production.zip
2. Install dependencies: pip install scikit-learn pandas numpy joblib

USAGE
-----

Option 1: Batch Prediction (with CSV)
--------------------------------------
Place final_with_season.csv in the same directory as predict.py, then:
  python predict.py

Output: predictions.csv with PREDICTED_CROP column added

Option 2: Single Prediction (Programmatic)
-------------------------------------------
  from predict import predict_single
  
  crop = predict_single(
      n=30,           # Nitrogen level
      p=20,           # Phosphorus level
      k=10,           # Potassium level
      temperature=25.5,
      humidity=60,
      ph=7.0,
      rainfall=100,
      season='RABI'   # One of: ZAID, RABI, KHARIF
  )
  print(crop)  # Output: predicted crop name

FEATURES
--------
Input features (8 total):
- N: Nitrogen content in soil
- P: Phosphorus content in soil
- K: Potassium content in soil
- TEMPERATURE: Temperature in degrees Celsius
- HUMIDITY: Relative humidity in percentage
- PH: Soil pH value
- RAINFALL: Rainfall in mm
- SEASON: Growing season (ZAID, RABI, or KHARIF)

Output:
- LABEL: Predicted crop name (56 possible classes)

SUPPORTED CROPS (56 classes)
-----------------------------
ADZUKIBEANS, APPLE, BANANA, BARLEY, BERSEEM, BLACKGRAM, BLACKPEPPER,
BRINJAL, CABBAGE, CASTOR, CAULIFLOWER, CHICKPEA, CHILLI, COCONUT,
COFFEE, CORIANDER, COTTON, COWPEA, CUMIN, FINGERMILLET, GARLIC,
GINGER, GRAPES, GROUNDNUT, GUAVA, JUTE, KIDNEYBEANS, LENTIL, LINSEED,
MAIZE, MANGO, MILLET, MOTHBEANS, MUNGBEAN, MUSKMELON, MUSTARD, OKRA,
ONION, ORANGE, PAPAYA, PEARLMILLET, PEAS, PIGEONPEAS, POMEGRANATE,
POTATO, RICE, RUBBER, SORGHUM, SOYBEAN, SUGARCANE, TEA, TOBACCO,
TOMATO, TURMERIC, WATERMELON, WHEAT

PER-CLASS PERFORMANCE (Recall by Crop)
---------------------------------------
Perfect (100% recall): ADZUKIBEANS, APPLE, BANANA, BLACKGRAM, CABBAGE,
CHICKPEA, COCONUT, COFFEE, COTTON, GRAPES, GROUNDNUT, LENTIL, MILLET,
MOTHBEANS, MUNGBEAN, MUSKMELON, ONION, ORANGE, PAPAYA, PEAS,
POMEGRANATE, RICE, RUBBER, TEA, TOBACCO, WATERMELON, WHEAT

Excellent (90-99% recall): BERSEEM, LINSEED, MAIZE, OKRA, PEARLMILLET,
POTATO, SUGARCANE, CUMIN, JUTE, KIDNEYBEANS

Good (80-89% recall): BARLEY, CAULIFLOWER, COWPEA, GARLIC, GUAVA,
MUSTARD, PIGEONPEAS, SOYBEAN, TURMERIC

Fair (70-79% recall): BRINJAL, FINGERMILLET

Needs Improvement (< 70%): CHILLI, CORIANDER, CASTOR, SORGHUM, TOMATO

NOTES
-----
- Model was trained with stratified 80/20 split
- SEASON feature is one-hot encoded (ZAID, RABI, KHARIF)
- No feature scaling applied (as per training specification)
- Synthetic training samples included (not separately flagged)
- RandomizedSearchCV tuning: 50 iterations, 3-fold CV

TROUBLESHOOTING
---------------
Q: "ModuleNotFoundError: No module named 'sklearn'"
A: Install scikit-learn: pip install scikit-learn

Q: "FileNotFoundError: models/model_rf.joblib"
A: Ensure folder structure is preserved. model_rf.joblib must be in models/

Q: "ValueError: feature_names_in_ not matching"
A: Ensure input data has exactly 8 columns in the correct order:
   N, P, K, TEMPERATURE, HUMIDITY, PH, RAINFALL, SEASON

DEPLOYMENT CHECKLIST
--------------------
✓ Model trained and validated
✓ Encoders saved with model
✓ No data leakage (encoders fit on training set only)
✓ Prediction script tested and working
✓ Ready for production deployment on any system with Python 3.7+

For questions or updates, refer to model training documentation.
