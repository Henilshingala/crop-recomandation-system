# 🔧 CRS Backend — V10

![Django](https://img.shields.io/badge/Django-5.x-092e20)
![DRF](https://img.shields.io/badge/Django_REST_Framework-3.15-a30000)
![Python](https://img.shields.io/badge/Python-3.11-3776ab)
![Version](https://img.shields.io/badge/version-10.0-blue)

Django REST Framework backend serving as the orchestration layer between the React frontend and the HuggingFace ML engine.

**Production URL**: https://crop-recomandation-system-kcoh.onrender.com/

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech stack](#-tech-stack)
- [Project structure](#-project-structure)
- [Installation](#-installation)
- [Environment variables](#-environment-variables)
- [API endpoints](#-api-endpoints)
- [Security](#-security)
- [Deployment on Render](#-deployment-on-render)
- [Troubleshooting](#-troubleshooting)
- [Changelog](#-changelog)

---

## 🎯 Overview

The backend is a Django REST Framework API that acts as the secure middleware between the React frontend and the HuggingFace ML model. Responsibilities:

- **Input validation** — strict range checks via `SecurePredictionSerializer`
- **ML gateway** — proxies prediction requests to the HuggingFace FastAPI Space
- **Data enrichment** — attaches crop images, yield, season, and nutrition to ML results
- **AI chatbot** — Hybrid FAQ + OpenRouter LLM assistant with NLLB translation
- **Geocoding proxy** — keeps OpenCage API key server-side (never exposed to frontend)
- **Government schemes** — serves 831 multilingual agriculture schemes
- **Rate limiting** — per-IP middleware (20 req/min for `/api/predict/`)

---

## ⚡ Features

| Feature | Details |
|---------|---------|
| Crop prediction | 51 crops, V10 NCS+EMS decision matrix |
| Data enrichment | Images, yield, season, nutrition per crop |
| AI assistant | FAQ fuzzy-match + OpenRouter LLM fallback |
| Government schemes | 831 schemes, 22 languages, full filter set |
| Weather geocoding | Secure proxy endpoint for OpenCage |
| Rate limiting | Per-IP sliding window middleware |
| Caching | Redis (production) / LocMem (dev) |
| Security | HSTS, secure cookies, CORS allowlist, no wildcards |

---

## 🛠️ Tech stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Django** | 5.x | Web framework |
| **Django REST Framework** | 3.15 | API framework |
| **Python** | 3.11+ | Runtime |
| **SQLite** | 3.x | Database |
| **WhiteNoise** | 6.x | Static file serving |
| **django-cors-headers** | 4.x | CORS middleware |
| **Requests** | 2.x | HTTP client for ML gateway |
| **Gunicorn** | latest | WSGI server |

---

## 📁 Project structure

```
Backend/app/
├── app/                        # Django project settings
│   ├── settings.py             # Production-ready configuration
│   ├── urls.py                 # Root URL routing
│   └── wsgi.py                 # WSGI entry point
│
├── apps/                       # Main Django application
│   ├── models.py               # Crop, PredictionLog models
│   ├── views.py                # All API endpoint handlers
│   ├── urls.py                 # API route definitions
│   ├── serializers.py          # DRF serializers
│   ├── validators.py           # Input validation + SecurePredictionSerializer
│   ├── middleware.py           # Per-IP rate limiting
│   ├── ml_inference.py         # HuggingFace gateway client
│   ├── nutrition.py            # Nutritional data lookup (Nutrient.csv)
│   ├── version.py              # Version constant "10.0.0"
│   └── services/
│       ├── faq_search.py       # Fuzzy FAQ matching
│       ├── openrouter_client.py # LLM fallback client
│       ├── translator.py       # NLLB translation service
│       ├── scheme_service.py   # Government schemes data service
│       ├── hf_service.py       # HuggingFace ML service
│       └── crop_sync.py        # Crop data synchronisation
│
├── Ai/                         # FAQ data (Ai.json)
├── media/crops/                # Crop images
├── staticfiles/                # Collected static files (production)
├── db.sqlite3                  # SQLite database
├── manage.py
└── requirements.txt
```

---

## 🚀 Installation

### Prerequisites

- Python 3.11+
- pip

### Steps

```bash
cd Backend/app

# Create and activate virtualenv
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env   # then edit .env

python manage.py migrate
python manage.py seed_crops
python manage.py collectstatic --noinput
python manage.py runserver
```

Server runs at `http://localhost:8000`.

---

## ⚙️ Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DJANGO_SECRET_KEY` | ✅ | Django secret key — raises `ValueError` if missing |
| `DJANGO_DEBUG` | ❌ | `True` / `False` (default `False`) |
| `DJANGO_ALLOWED_HOSTS` | ❌ | Comma-separated hosts (no protocol) |
| `CORS_ALLOWED_ORIGINS` | ❌ | Comma-separated origins (with protocol) |
| `HF_MODEL_URL` | ❌ | HuggingFace Space URL (default: `https://shingala-crs.hf.space`) |
| `HF_TOKEN` | ❌ | HF token for private spaces |
| `OPENCAGE_API_KEY` | ❌ | OpenCage geocoding key (kept server-side) |
| `OPENROUTER_API_KEY` | ❌ | OpenRouter LLM fallback key |
| `REDIS_URL` | ❌ | Redis cache URL (falls back to LocMemCache) |
| `SECURE_SSL_REDIRECT` | ❌ | `True` / `False` (default `True` in production) |

### Example `.env` (development)

```env
DJANGO_SECRET_KEY=change-me-use-a-long-random-string
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
SECURE_SSL_REDIRECT=False
HF_MODEL_URL=https://shingala-crs.hf.space
```

---

## 🌐 API endpoints

### Base URL
```
Development:  http://localhost:8000/api/
Production:   https://crop-recomandation-system-kcoh.onrender.com/api/
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health/` | Health check (returns version + status) |
| `POST` | `/api/predict/` | Crop prediction (7 soil/climate inputs) |
| `GET` | `/api/crops/` | List all crops in DB |
| `GET` | `/api/crops/available/` | ML model's supported crops |
| `GET` | `/api/model/limits/` | Feature validation ranges |
| `GET` | `/api/schemes/` | Government schemes (filterable) |
| `GET` | `/api/schemes/options/` | Available filter values |
| `POST` | `/api/assistant/chat/` | AI chatbot (Krishi Mitra) |
| `GET` | `/api/geocode/` | Geocoding proxy (OpenCage, key stays backend) |
| `GET` | `/api/locations/states/` | Indian states list |
| `GET` | `/api/locations/districts/` | Districts for a state |
| `GET` | `/api/locations/subdistricts/` | Sub-districts for a district |
| `GET` | `/api/locations/villages/` | Villages for a sub-district |

### POST `/api/predict/` — example

**Request:**
```json
{
  "N": 90, "P": 42, "K": 43,
  "temperature": 24.5, "humidity": 68,
  "ph": 6.7, "rainfall": 120
}
```

**Response:**
```json
{
  "top_1": { "crop": "rice", "confidence": 96.4, "risk_level": "low", ... },
  "top_3": [ ... ],
  "model_info": { "coverage": 51, "type": "stacked-ensemble-v10", "version": "10.0.0" },
  "version": "10.0.0"
}
```

### GET `/api/health/` — example

```json
{
  "status": "healthy",
  "database": "ok",
  "ml_model": "ok",
  "version": "10.0.0",
  "soil_crops": 22,
  "extended_crops": 51
}
```

---

## 🔒 Security

| Control | Implementation |
|---------|---------------|
| **No wildcard CORS** | `CORS_ALLOW_ALL_ORIGINS = False` |
| **HSTS** | 1-year, subdomains, preload |
| **Secure cookies** | `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` |
| **SSL redirect** | `SECURE_SSL_REDIRECT = True` in production |
| **API key protection** | OpenCage key stored only in Render env vars; `/api/geocode/` proxies it |
| **Input validation** | `SecurePredictionSerializer` — strict float ranges, suspicious pattern detection |
| **Rate limiting** | 20 req/min on `/api/predict/` per IP via `RateLimitMiddleware` |
| **No debug in production** | `DJANGO_DEBUG=False` enforced |
| **No wildcard hosts** | `*` in `ALLOWED_HOSTS` raises `ValueError` at startup |
| **Logger safety** | `logger.warning("msg: %s", data)` — no f-strings in log calls |

---

## 🚢 Deployment on Render

### render.yaml key fields

```yaml
services:
  - type: web
    name: crop-recomandation-system
    env: python
    rootDir: Backend/app
    buildCommand: pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
    startCommand: gunicorn app.wsgi:application --workers 1 --timeout 120 --bind 0.0.0.0:$PORT
```

### Required env vars on Render

```
DJANGO_SECRET_KEY   # generate with: python -c "import secrets; print(secrets.token_hex(50))"
DJANGO_DEBUG=False
CORS_ALLOWED_ORIGINS=https://crop-recomandation-system.vercel.app,http://localhost:5173
HF_MODEL_URL=https://shingala-crs.hf.space
OPENCAGE_API_KEY=<your-key>
OPENROUTER_API_KEY=<your-key>
```

---

## 🐛 Troubleshooting

| Issue | Cause | Solution |
|-------|-------|---------|
| CORS errors | Origin not in allow list | Add frontend URL to `CORS_ALLOWED_ORIGINS` env var |
| 503 on predict | HF Space sleeping | Wait ~30 s, HF Space will wake |
| Static files 404 | `collectstatic` not run | `python manage.py collectstatic --noinput` |
| `ValueError: DJANGO_SECRET_KEY` | Env var missing | Set `DJANGO_SECRET_KEY` in Render env vars |

---

## 🔄 Changelog

### V10.0.0 — 2026-03-25 (Current)
- `views.py` — removed redundant bare `import os / settings / Http404` inside function body (now module-level only)
- `views.py` — updated docstring from V7 → V10
- `views.py` — health check now returns `"version": "10.0.0"`
- `validators.py` — replaced f-string in `logger.warning` with `%s` lazy format
- `version.py` — new file, `VERSION = "10.0.0"` as single source of truth
- `settings.py` — `APP_VERSION = "10.0.0"` constant added

### V9.0.0
- NCS + EMS decision matrix
- Geocoding moved to backend proxy (security)

### V8.0.0
- Government schemes service (831 schemes, 22 languages)
- Weather cascading location API

---

<p align="center">
  Part of the <strong>Crop Recommendation System</strong> · Built by <strong>Henil Shingala</strong>
</p>
