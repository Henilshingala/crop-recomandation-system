"""
Crop Recommendation System - Main URL Configuration
===================================================
Root URL routing for the Django project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.views import index

urlpatterns = [
    # Home page
    path("", index, name='home'),
    
    # Django Admin Panel
    path("admin/", admin.site.urls),
    
    # API endpoints (v1)
    path("api/", include("apps.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
