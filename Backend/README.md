# 🔧 Backend API - Crop Recommendation System

![Django](https://img.shields.io/badge/Django-5.1.7-092e20)
![DRF](https://img.shields.io/badge/Django_REST_Framework-3.15.2-a30000)
![Python](https://img.shields.io/badge/Python-3.11-3776ab)
![SQLite](https://img.shields.io/badge/SQLite-3-003b57)

Robust Django REST API backend serving as the orchestration layer between the frontend and ML model.

---

## 🌐 Live Deployment

**Production URL**: https://crop-recomandation-system.onrender.com/

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Installation & Setup](#-installation--setup)
- [Environment Configuration](#-environment-configuration)
- [API Endpoints](#-api-endpoints)
- [Database Schema](#-database-schema)
- [ML Integration](#-ml-integration)
- [Security & CORS](#-security--cors)
- [Deployment](#-deployment)
- [Practical Considerations](#-practical-considerations)

---

## 🎯 Overview

The backend is a Django REST Framework API that acts as the middleware between the React frontend and the HuggingFace ML model. It provides:

- **RESTful API** endpoints for crop recommendations
- **Crop database** with detailed information for 22 crops
- **ML model orchestration** via HTTP calls to HuggingFace Spaces
- **Static file serving** for crop images
- **CORS management** for secure cross-origin requests
- **Request validation** and error handling

---

## ⚡ Features

### 1. **Crop Recommendation API**
- Accepts 7 input parameters (N, P, K, temperature, humidity, pH, rainfall)
- Calls HuggingFace ML API for predictions
- Enriches predictions with crop details from database
- Returns top-3 recommendations with confidence scores

### 2. **Crop Database Management**
- **22 crops** with comprehensive information
- Cultivation tips, nutritional requirements, climate preferences
- High-quality crop images
- RESTful CRUD operations (currently Read-only)

### 3. **Static File Management**
- **WhiteNoise** for production static file serving
- Efficient compression and caching
- CDN-friendly headers
- Media file support for crop images

### 4. **Security & CORS**
- **Restricted CORS** policy (only Vercel frontend + localhost)
- **HTTPS enforcement** in production
- **Secure cookie** settings
- **HSTS headers** for browsers
- **XSS protection**

### 5. **Error Handling**
- Comprehensive error responses
- User-friendly error messages
- Detailed logging for debugging
- Graceful fallbacks

---

## 🛠️ Technology Stack

### Core Framework

| Technology | Version | Purpose |
|------------|---------|---------|
| **Django** | 5.1.7 | Web framework |
| **Django REST Framework** | 3.15.2 | API framework |
| **Python** | 3.11+ | Programming language |
| **SQLite** | 3.x | Database |

### Additional Libraries

- **django-cors-headers** (4.7.0): CORS middleware
- **WhiteNoise** (6.8.2): Static file serving
- **Requests** (2.32.3): HTTP client for ML API
- **Pillow** (11.0.0): Image processing

---

## 📁 Project Structure

```
Backend/app/
├── app/                        # Django project settings
│   ├── __init__.py
│   ├── settings.py            # Main configuration
│   ├── urls.py                # Root URL configuration
│   └── wsgi.py                # WSGI entry point
│
├── apps/                       # Main application
│   ├── models.py              # Crop model (database schema)
│   ├── views.py               # API views
│   ├── serializers.py         # DRF serializers
│   ├── urls.py                # App URLs
│   ├── ml_inference.py        # ML API client
│   └── management/
│       └── commands/
│           └── seed_crops.py  # Data seeding command
│
├── media/                      # User uploads & crop images
│   └── crops/                 # Crop images
│
├── staticfiles/                # Collected static files (production)
├── db.sqlite3                 # SQLite database
├── manage.py                  # Django management script
├── requirements.txt           # Python dependencies
├── Procfile                   # Render deployment config
└── README.md                  # This file
```

---

## 🚀 Installation & Setup

### Prerequisites

- **Python**: 3.11 or higher
- **pip**: Latest version
- **virtualenv**: For isolated Python environment

### Step-by-Step Installation

#### 1. Navigate to Backend Directory
```bash
cd Backend/app
```

#### 2. Create Virtual Environment
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Set Up Environment Variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

#### 5. Run Database Migrations
```bash
python manage.py migrate
```

#### 6. Seed Crop Data (Optional - already migrated)
```bash
python manage.py seed_crops
```

#### 7. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

#### 8. Start Development Server
```bash
python manage.py runserver
```

Server runs at: `http://localhost:8000`

---

## ⚙️ Environment Configuration

### Environment Variables

Create a `.env` file in `Backend/app/`:

```env
# Django Settings
DJANGO_SECRET_KEY=your-super-secret-key-change-in-production
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com,localhost,127.0.0.1

# CORS Settings (NO wildcard - specific URLs only)
CORS_ALLOWED_ORIGINS=https://crop-recomandation-system.vercel.app,http://localhost:5173

# Security Settings
SECURE_SSL_REDIRECT=True

# HuggingFace ML API
HF_API_URL=https://shingala-crs.hf.space/
# HF_TOKEN=your-token-if-space-is-private  # Optional
```

### Important Notes

| Variable | Format | Example |
|----------|--------|---------|
| `DJANGO_ALLOWED_HOSTS` | Domain only (no protocol) | `example.com,localhost` |
| `CORS_ALLOWED_ORIGINS` | Full URL with protocol | `https://example.com,http://localhost:5173` |
| `HF_API_URL` | Full URL | `https://space.hf.space/` |

### Production vs Development

**Development (`.env`)**:
```env
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
SECURE_SSL_REDIRECT=False
```

**Production (Render Dashboard)**:
```env
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=crop-recomandation-system.onrender.com
CORS_ALLOWED_ORIGINS=https://crop-recomandation-system.vercel.app,http://localhost:5173
SECURE_SSL_REDIRECT=True
HF_API_URL=https://shingala-crs.hf.space/
```

---

## 🌐 API Endpoints

### Base URL
```
Development: http://localhost:8000/api/
Production:  https://crop-recomandation-system.onrender.com/api/
```

---

### 1. **Get Crop Recommendation** (Primary Endpoint)

```http
POST /api/recommend/
Content-Type: application/json
```

**Request Body**:
```json
{
  "N": 90,           // Nitrogen content (0-140)
  "P": 42,           // Phosphorus content (5-145)
  "K": 43,           // Potassium content (5-205)
  "temperature": 20.87,  // Temperature in Celsius (0-50)
  "humidity": 82.00,     // Humidity percentage (0-100)
  "ph": 6.50,            // pH value (3.5-10)
  "rainfall": 202.93     // Rainfall in mm (20-300)
}
```

**Response (Success - 200 OK)**:
```json
{
  "recommendations": [
    {
      "crop": "rice",
      "confidence": 95.2,
      "description": "Rice is a staple cereal grain...",
      "cultivation_tips": "Plant rice in flooded fields...",
      "nutritional_requirements": {
        "nitrogen": "High",
        "phosphorus": "Medium",
        "potassium": "Medium"
      },
      "climate_preferences": {
        "temperature": "20-30°C",
        "humidity": "High",
        "rainfall": "Heavy"
      },
      "image_url": "/media/crops/rice.jpg"
    },
    {
      "crop": "chickpea",
      "confidence": 78.5,
      ...
    },
    {
      "crop": "kidneybeans",
      "confidence": 65.3,
      ...
    }
  ]
}
```

**Error Responses**:

```json
// 400 Bad Request - Invalid input
{
  "error": "Invalid input parameters",
  "details": {
    "N": ["This field is required"],
    "temperature": ["Temperature must be between 0 and 50"]
  }
}

// 503 Service Unavailable - ML model warming up
{
  "error": "ML Model is warming up",
  "message": "Please retry in 30 seconds"
}

// 500 Internal Server Error
{
  "error": "Internal server error",
  "message": "An unexpected error occurred"
}
```

---

### 2. **List All Crops**

```http
GET /api/crops/
```

**Response (200 OK)**:
```json
{
  "count": 22,
  "results": [
    {
      "id": 1,
      "name": "rice",
      "display_name": "Rice",
      "description": "Rice is a staple cereal grain...",
      "cultivation_tips": "...",
      "image": "/media/crops/rice.jpg",
      "created_at": "2024-01-01T00:00:00Z"
    },
    ...
  ]
}
```

**Query Parameters**:
- `?page=1` - Pagination (20 crops per page)
- `?search=rice` - Search by crop name (future)

---

### 3. **Get Crop Details**

```http
GET /api/crops/{crop_name}/
```

**Example**:
```http
GET /api/crops/rice/
```

**Response (200 OK)**:
```json
{
  "id": 1,
  "name": "rice",
  "display_name": "Rice",
  "description": "Detailed description...",
  "cultivation_tips": "Step-by-step cultivation guide...",
  "nutritional_requirements": {
    "nitrogen": "High",
    "phosphorus": "Medium",
    "potassium": "Medium"
  },
  "climate_preferences": {
    "temperature": "20-30°C",
    "humidity": "80-90%",
    "rainfall": "200-300mm",
    "soil_ph": "5.5-7.0"
  },
  "image": "/media/crops/rice.jpg",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Error (404 Not Found)**:
```json
{
  "error": "Crop not found",
  "message": "No crop with name 'xyz' exists"
}
```

---

### 4. **Health Check**

```http
GET /api/health/
```

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-02-17T08:00:00Z"
}
```

---

## 💾 Database Schema

### Crop Model

```python
class Crop(models.Model):
    """
    Stores comprehensive information about each crop.
    """
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField()
    cultivation_tips = models.TextField()
    image = models.ImageField(upload_to='crops/')
    
    # Nutritional requirements (JSON)
    nutritional_requirements = models.JSONField()
    
    # Climate preferences (JSON)
    climate_preferences = models.JSONField()
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Supported Crops**: Rice, Maize, Chickpea, Kidneybeans, Pigeonpeas, Mothbeans, Mungbean, Blackgram, Lentil, Pomegranate, Banana, Mango, Grapes, Watermelon, Muskmelon, Apple, Orange, Papaya, Coconut, Cotton, Jute, Coffee

---

## 🤖 ML Integration

### HuggingFace API Client (`ml_inference.py`)

The backend calls the HuggingFace Space via HTTP:

```python
class CropPredictor:
    """
    Singleton class for ML model inference via HuggingFace API.
    """
    
    def __init__(self):
        self._api_url = os.environ.get(
            "HF_API_URL", 
            "https://shingala-crs.hf.space/"
        )
        self._token = os.environ.get("HF_TOKEN")  # Optional
    
    def predict_top_crops(self, n, p, k, temperature, 
                          humidity, ph, rainfall, top_n=3):
        """
        Calls HuggingFace API for predictions.
        """
        payload = {
            'N': n, 'P': p, 'K': k,
            'temperature': temperature,
            'humidity': humidity,
            'ph': ph,
            'rainfall': rainfall,
            'top_n': top_n
        }
        
        response = requests.post(
            f"{self._api_url}/predict",
            json=payload,
            headers={"Authorization": f"Bearer {self._token}"}
            if self._token else {},
            timeout=15
        )
        
        response.raise_for_status()
        return response.json()
```

### Error Handling

```python
try:
    predictions = predictor.predict_top_crops(...)
except requests.Timeout:
    return Response(
        {"error": "ML model timeout"},
        status=503
    )
except requests.HTTPError as e:
    if e.response.status_code == 503:
        return Response(
            {"error": "Model warming up, retry in 30s"},
            status=503
        )
```

---

## 🔒 Security & CORS

### CORS Configuration (`settings.py`)

```python
# STRICT CORS - Only specific origins allowed
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,https://crop-recomandation-system.vercel.app"
).split(",")

# NO wildcard allowed
CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOW_CREDENTIALS = True
```

### Allowed Hosts

```python
# Domain-only (no https://)
ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1,crop-recomandation-system.onrender.com"
).split(",")
```

### HTTPS Enforcement

```python
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
```

---

## 🚀 Deployment

### Deploying to Render

#### 1. **Create Web Service**
- Go to Render Dashboard
- New → Web Service
- Connect GitHub repository

#### 2. **Configure Service**
```
Name: crop-recommendation-backend
Region: Oregon (US West)
Branch: main
Root Directory: Backend/app
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn app.wsgi:application
```

#### 3. **Environment Variables**
Set in Render Dashboard:
```
DJANGO_SECRET_KEY=<generate-secret-key>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=crop-recomandation-system.onrender.com
CORS_ALLOWED_ORIGINS=https://crop-recomandation-system.vercel.app,http://localhost:5173
SECURE_SSL_REDIRECT=True
HF_API_URL=https://shingala-crs.hf.space/
```

#### 4. **Auto-Deploy**
- Push to `main` branch triggers auto-deploy
- Build logs available in Render dashboard

---

## 🔍 Practical Considerations

### Cold Start Time

**Current Behavior**:
- Render's free tier **sleeps after 15 minutes** of inactivity
- First request after sleep takes **~20-40 seconds** to wake up
- Subsequent requests are instant

**Practical Impact**:
- ✅ Fine for **planning tools** (not real-time systems)
- ✅ **Loading indicators** inform users during cold start
- ✅ **Auto-scaling** prevents downtime during high traffic

**Future Enhancement**:
- Paid tier for **always-on** instances
- **Keep-alive pings** to prevent sleeping (if on paid plan)

### Database Choice: SQLite

**Current Setup**:
- **SQLite database** (file-based, no separate server)
- **Read-heavy** workload (crop database is mostly static)
- **No complex joins** or concurrent writes

**Why SQLite?**:
- ✅ **Perfect for our use case**: Static crop data rarely changes
- ✅ **Zero configuration**: No database server to manage
- ✅ **Fast reads**: Excellent for lookup operations
- ✅ **File-based**: Easy backup and version control

**Practical Considerations**:
- ✅ Handles **hundreds of requests/second** for read operations
- ✅ Crop data changes infrequently (manual updates only)
- ⚠️ Not ideal for **high-concurrency writes** (not our use case)
- ⚠️ Limited to **single server** (fine for our scale)

**When to Migrate to PostgreSQL?**:
- If user-generated content is added (reviews, ratings)
- If concurrent write operations increase significantly
- If we need advanced features (full-text search, geospatial queries)

**Current Status**: SQLite is **perfectly suitable** and **production-ready** for this application

---

## 🧪 Testing (Manual Testing Guide)

### Test Recommendation Endpoint

```bash
curl -X POST https://crop-recomandation-system.onrender.com/api/recommend/ \
  -H "Content-Type: application/json" \
  -d '{
    "N": 90,
    "P": 42,
    "K": 43,
    "temperature": 20.87,
    "humidity": 82.00,
    "ph": 6.50,
    "rainfall": 202.93
  }'
```

**Expected Output**: Top-3 crop recommendations

### Test Crops List

```bash
curl https://crop-recomandation-system.onrender.com/api/crops/
```

**Expected Output**: List of 22 crops

### Test Specific Crop

```bash
curl https://crop-recomandation-system.onrender.com/api/crops/rice/
```

**Expected Output**: Detailed rice information

---

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Render Deployment Guide](https://render.com/docs/deploy-django)
- [WhiteNoise Documentation](http://whitenoise.evans.io/)

---

## 🐛 Troubleshooting

### Issue: CORS Errors

**Solution**: Check that `CORS_ALLOWED_ORIGINS` includes your frontend URL with exact protocol match

### Issue: 503 Errors on Recommendation

**Cause**: HuggingFace Space is sleeping

**Solution**: Wait 30 seconds and retry (space is warming up)

### Issue: Static Files Not Loading

**Solution**: 
```bash
python manage.py collectstatic --noinput
```

---

**Built with Django & Django REST Framework**

*Last Updated: February 2026*
