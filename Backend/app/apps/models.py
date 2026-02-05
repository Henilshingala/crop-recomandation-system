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
    
    Admin can upload an image file OR provide an image URL.
    Priority: uploaded image > image_url > placeholder
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique crop name (must match ML model label)"
    )
    
    # Image 1 - either file upload or URL
    image = models.ImageField(
        upload_to='crops/',
        blank=True,
        null=True,
        help_text="Upload crop image 1 (takes priority over URL)"
    )
    
    image_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Image 1 URL (used if no file uploaded)"
    )
    
    # Image 2 - either file upload or URL
    image_2 = models.ImageField(
        upload_to='crops/',
        blank=True,
        null=True,
        help_text="Upload crop image 2 (takes priority over URL)"
    )
    
    image_2_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Image 2 URL (used if no file uploaded)"
    )
    
    # Image 3 - either file upload or URL
    image_3 = models.ImageField(
        upload_to='crops/',
        blank=True,
        null=True,
        help_text="Upload crop image 3 (takes priority over URL)"
    )
    
    image_3_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Image 3 URL (used if no file uploaded)"
    )
    
    # Crop metadata (kept for compatibility but not shown in admin)
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
        Returns the appropriate image URL based on priority:
        1. Uploaded image file (if exists)
        2. External image URL (if provided)
        3. Placeholder image URL
        """
        if image_number == 1:
            if self.image and hasattr(self.image, 'url'):
                return self.image.url
            elif self.image_url:
                return self.image_url
        elif image_number == 2:
            if self.image_2 and hasattr(self.image_2, 'url'):
                return self.image_2.url
            elif self.image_2_url:
                return self.image_2_url
        elif image_number == 3:
            if self.image_3 and hasattr(self.image_3, 'url'):
                return self.image_3.url
            elif self.image_3_url:
                return self.image_3_url
        
        # Return a placeholder image
        return f"https://via.placeholder.com/300x200?text={self.name}+{image_number}"
    
    def clean(self):
        """Validate and clean image URLs."""
        # Strip whitespace from URLs
        if self.image_url:
            self.image_url = self.image_url.strip()
        if self.image_2_url:
            self.image_2_url = self.image_2_url.strip()
        if self.image_3_url:
            self.image_3_url = self.image_3_url.strip()
        
        # Validate URLs start with http:// or https://
        errors = {}
        
        if self.image_url and not (self.image_url.startswith('http://') or self.image_url.startswith('https://')):
            errors['image_url'] = 'URL must start with http:// or https://'
        
        if self.image_2_url and not (self.image_2_url.startswith('http://') or self.image_2_url.startswith('https://')):
            errors['image_2_url'] = 'URL must start with http:// or https://'
        
        if self.image_3_url and not (self.image_3_url.startswith('http://') or self.image_3_url.startswith('https://')):
            errors['image_3_url'] = 'URL must start with http:// or https://'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Save model and ensure URLs are properly formatted."""
        # Strip whitespace from URLs before saving
        if self.image_url:
            self.image_url = self.image_url.strip()
        if self.image_2_url:
            self.image_2_url = self.image_2_url.strip()
        if self.image_3_url:
            self.image_3_url = self.image_3_url.strip()
        
        # Call clean to validate
        self.full_clean()
        
        # Call parent save
        super().save(*args, **kwargs)


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
