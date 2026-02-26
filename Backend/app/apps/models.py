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
    
    # Image 1 (Primary)
    image = models.ImageField(
        upload_to='crops/',
        blank=True,
        null=True,
        help_text="Primary crop image (uploaded file)"
    )
    image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Primary crop image (external URL)"
    )
    
    # Image 2
    image_2 = models.ImageField(
        upload_to='crops/',
        blank=True,
        null=True,
        help_text="Secondary crop image (uploaded file)"
    )
    image_2_url = models.URLField(
        blank=True,
        null=True,
        help_text="Secondary crop image (external URL)"
    )
    
    # Image 3
    image_3 = models.ImageField(
        upload_to='crops/',
        blank=True,
        null=True,
        help_text="Tertiary crop image (uploaded file)"
    )
    image_3_url = models.URLField(
        blank=True,
        null=True,
        help_text="Tertiary crop image (external URL)"
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
        Returns the best available image URL with cache-busting:
        1. Uploaded file
        2. External URL
        3. Placeholder (last resort)
        """
        import time
        ts = int(time.time())
        url = None

        if image_number == 1:
            if self.image: url = self.image.url
            elif self.image_url: url = self.image_url
        elif image_number == 2:
            if self.image_2: url = self.image_2.url
            elif self.image_2_url: url = self.image_2_url
        elif image_number == 3:
            if self.image_3: url = self.image_3.url
            elif self.image_3_url: url = self.image_3_url
            
        if not url:
            url = f"https://via.placeholder.com/300x200?text={self.name.replace(' ', '+')}+{image_number}"

        # Add cache busting timestamp for local media and external URLs
        separator = '&' if '?' in url else '?'
        return f"{url}{separator}v={ts}"


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
