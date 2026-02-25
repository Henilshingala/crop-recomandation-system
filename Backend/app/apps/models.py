"""
Crop Recommendation System - Django Models
==========================================
This module defines the database models for storing crop metadata.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class Crop(models.Model):
    """
    Crop model stores metadata for each crop type.
    
    Clean model ready for fresh image uploads after deployment.
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique crop name (must match ML model label)"
    )
    
    # Crop metadata
    expected_yield = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Expected yield per hectare (e.g., '2-3 tons/hectare')"
    )
    
    season = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Growing season (e.g., 'Kharif', 'Rabi', 'Zaid')"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Brief description of the crop"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Crop'
        verbose_name_plural = 'Crops'
    
    def __str__(self):
        return self.name
    
    def get_image_url(self, image_number=1):
        """
        Returns placeholder image URL until new images are uploaded.
        """
        return f"https://via.placeholder.com/300x200?text={self.name}+{image_number}"


class PredictionLog(models.Model):
    """
    Logs all prediction requests for analytics and debugging.
    """
    
    # Input parameters
    nitrogen = models.FloatField(validators=[MinValueValidator(0)])
    phosphorus = models.FloatField(validators=[MinValueValidator(0)])
    potassium = models.FloatField(validators=[MinValueValidator(0)])
    temperature = models.FloatField()
    humidity = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    ph = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(14)])
    rainfall = models.FloatField(validators=[MinValueValidator(0)])
    
    # Prediction results (stored as JSON string)
    predictions = models.JSONField(
        help_text="Top 3 crop predictions with confidence scores"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Prediction Log'
        verbose_name_plural = 'Prediction Logs'
    
    def __str__(self):
        return f"Prediction at {self.created_at}"
