"""
Crop Recommendation System - URL Routing
========================================
API endpoint definitions for the crop recommendation system.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CropPredictionView,
    CropViewSet,
    PredictionLogViewSet,
    health_check,
    available_crops,
    index
)

# DRF Router for ViewSets
router = DefaultRouter()
router.register(r'crops', CropViewSet, basename='crop')
router.register(r'logs', PredictionLogViewSet, basename='prediction-log')

# URL patterns
urlpatterns = [
    # Main prediction endpoint (POST)
    path('predict/', CropPredictionView.as_view(), name='predict'),
    
    # Health check endpoint (GET)
    path('health/', health_check, name='health-check'),
    
    # Available crops from ML model (GET)
    path('crops/available/', available_crops, name='available-crops'),
    
    # Index page
    path('index/', index, name='index'),
    
    # Include router URLs (CRUD for crops and logs)
    path('', include(router.urls)),
]

"""
API Endpoints Summary:
======================

Prediction:
    POST /api/predict/              - Get crop recommendations

Crops (CRUD):
    GET  /api/crops/                - List all crops
    POST /api/crops/                - Create crop (admin)
    GET  /api/crops/{id}/           - Get specific crop
    PUT  /api/crops/{id}/           - Update crop (admin)
    DELETE /api/crops/{id}/         - Delete crop (admin)
    GET  /api/crops/available/      - List ML model's crop labels

Prediction Logs (Read-only, admin):
    GET  /api/logs/                 - List all prediction logs
    GET  /api/logs/{id}/            - Get specific log

Health:
    GET  /api/health/               - System health check
"""
