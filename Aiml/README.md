---
title: Crop Recommendation ML API
emoji: 🌾
colorFrom: green
colorTo: yellow
sdk: docker
app_file: app.py
pinned: false
license: mit
---

# Crop Recommendation System - ML API

This Space provides a FastAPI endpoint for crop recommendation based on soil and climate parameters.

## Endpoints

- `POST /predict` - Get crop recommendation with nutrition data
- `GET /` - Health check
- `GET /crops` - List all available crops

## Usage

```python
import requests

response = requests.post(
    "https://shingala-crs.hf.space/predict",
    json={
        "N": 90, "P": 42, "K": 43,
        "temperature": 20.8, "humidity": 82,
        "ph": 6.5, "rainfall": 202
    }
)
print(response.json())
```

## Response Format

```json
{
  "crop": "rice",
  "confidence": 0.98,
  "nutrition": {
    "protein_g": 7.5,
    "fat_g": 0.5,
    "carbs_g": 78.0,
    ...
  }
}
```
