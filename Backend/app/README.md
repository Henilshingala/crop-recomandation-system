# Crop Recommendation System - Backend

Production-ready Django REST API for crop recommendations using Machine Learning.

## Features

- 🌾 **ML-Powered Predictions**: Random Forest model predicts top 3 crop recommendations
- 📊 **Confidence Scores**: Each recommendation includes probability percentage
- 🖼️ **Image Management**: Admin can upload images or provide URLs for each crop
- 📝 **Prediction Logging**: All predictions are logged for analytics
- 🔒 **CORS Enabled**: Configured for React frontend integration
- 🐘 **PostgreSQL**: Production-ready database

## Tech Stack

- Django 5.x
- Django REST Framework
- PostgreSQL
- scikit-learn (ML model inference)
- django-cors-headers

## Project Structure

```
Backend/
└── app/
    ├── app/                    # Django project settings
    │   ├── settings.py         # Configuration (DB, CORS, etc.)
    │   ├── urls.py             # Root URL routing
    │   └── wsgi.py
    ├── apps/                   # Main application
    │   ├── admin.py            # Admin panel config
    │   ├── models.py           # Crop, PredictionLog models
    │   ├── serializers.py      # DRF serializers
    │   ├── views.py            # API views
    │   ├── urls.py             # API routing
    │   ├── ml_inference.py     # ML model loading & prediction
    │   └── management/
    │       └── commands/
    │           └── seed_crops.py
    ├── media/                  # Uploaded crop images
    ├── manage.py
    ├── requirements.txt
    └── .env.example
```

## Quick Start

### 1. Prerequisites

- Python 3.10+
- PostgreSQL 14+
- ML model files in `AiMl/` directory:
  - `model_rf.joblib`
  - `label_encoder.joblib`

### 2. Setup PostgreSQL Database

```sql
-- Create database
CREATE DATABASE crop_recommendation_db;

-- Create user (optional)
CREATE USER crop_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE crop_recommendation_db TO crop_user;
```

### 3. Install Dependencies

```bash
cd Backend/app
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example env file
copy .env.example .env

# Edit .env with your database credentials
```

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Seed Crop Data

```bash
python manage.py seed_crops
```

### 7. Create Admin User

```bash
python manage.py createsuperuser
```

### 8. Run Development Server

```bash
python manage.py runserver
```

Server will start at: http://127.0.0.1:8000

## API Endpoints

### Prediction Endpoint (Main)

**POST** `/api/predict/`

Request:
```json
{
  "N": 90,
  "P": 42,
  "K": 43,
  "temperature": 24.5,
  "humidity": 68,
  "ph": 6.7,
  "rainfall": 120
}
```

Response:
```json
{
  "recommendations": [
    {
      "crop": "rice",
      "confidence": 98.6,
      "image_url": "http://localhost:8000/media/crops/rice.jpg",
      "expected_yield": "3-6 tons/hectare",
      "season": "Kharif"
    },
    {
      "crop": "wheat",
      "confidence": 12.3,
      "image_url": "https://via.placeholder.com/300x200?text=wheat",
      "expected_yield": "2-4 tons/hectare",
      "season": "Rabi"
    },
    {
      "crop": "maize",
      "confidence": 3.1,
      "image_url": "https://example.com/maize.jpg",
      "expected_yield": "5-8 tons/hectare",
      "season": "Kharif/Rabi"
    }
  ]
}
```

### Other Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health/` | Health check (DB + ML status) |
| GET | `/api/crops/` | List all crops |
| GET | `/api/crops/{id}/` | Get specific crop |
| GET | `/api/crops/available/` | List ML model's crop labels |
| GET | `/api/logs/` | Prediction logs (admin only) |

### Admin Panel

Access at: http://127.0.0.1:8000/admin/

Features:
- Manage crops (add/edit/delete)
- Upload crop images OR provide URLs
- View prediction logs
- Analytics dashboard

## Testing with cURL

### Test Prediction API

```bash
curl -X POST http://127.0.0.1:8000/api/predict/ \
  -H "Content-Type: application/json" \
  -d '{
    "N": 90,
    "P": 42,
    "K": 43,
    "temperature": 24.5,
    "humidity": 68,
    "ph": 6.7,
    "rainfall": 120
  }'
```

### Health Check

```bash
curl http://127.0.0.1:8000/api/health/
```

### List All Crops

```bash
curl http://127.0.0.1:8000/api/crops/
```

### Get Available ML Crops

```bash
curl http://127.0.0.1:8000/api/crops/available/
```

## Windows PowerShell cURL Examples

```powershell
# Prediction
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/predict/" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"N": 90, "P": 42, "K": 43, "temperature": 24.5, "humidity": 68, "ph": 6.7, "rainfall": 120}'

# Health Check
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health/"

# List Crops
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/crops/"
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | (insecure default) | Django secret key |
| `DJANGO_DEBUG` | `True` | Debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed hosts |
| `DB_NAME` | `crop_recommendation_db` | PostgreSQL database name |
| `DB_USER` | `postgres` | Database user |
| `DB_PASSWORD` | `postgres` | Database password |
| `DB_HOST` | `localhost` | Database host |
| `DB_PORT` | `5432` | Database port |

## CORS Configuration

The backend is configured to allow requests from:
- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (CRA dev server)

To add more origins, edit `CORS_ALLOWED_ORIGINS` in `settings.py`.

## Production Deployment

1. Set `DJANGO_DEBUG=False`
2. Use a proper `DJANGO_SECRET_KEY`
3. Configure `DJANGO_ALLOWED_HOSTS`
4. Use gunicorn: `gunicorn app.wsgi:application`
5. Set up nginx for static/media files
6. Use environment variables for sensitive data

## License

MIT
