"""
Crop Recommendation System - Admin Configuration
================================================
Django admin panel customization for managing crops and viewing logs.
"""

from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Crop, PredictionLog


class CropForm(forms.ModelForm):
    """Custom form for Crop model with better URL validation."""
    
    class Meta:
        model = Crop
        fields = '__all__'
    
    def clean(self):
        """Validate image URLs."""
        cleaned_data = super().clean()
        
        # Check image_url
        image_url = cleaned_data.get('image_url')
        image = cleaned_data.get('image')
        
        if image_url and not image:
            # Validate URL format
            if not (image_url.startswith('http://') or image_url.startswith('https://')):
                raise forms.ValidationError(
                    {'image_url': 'Image URL must start with http:// or https://'}
                )
        
        # Check image_2_url
        image_2_url = cleaned_data.get('image_2_url')
        image_2 = cleaned_data.get('image_2')
        
        if image_2_url and not image_2:
            if not (image_2_url.startswith('http://') or image_2_url.startswith('https://')):
                raise forms.ValidationError(
                    {'image_2_url': 'Image 2 URL must start with http:// or https://'}
                )
        
        # Check image_3_url
        image_3_url = cleaned_data.get('image_3_url')
        image_3 = cleaned_data.get('image_3')
        
        if image_3_url and not image_3:
            if not (image_3_url.startswith('http://') or image_3_url.startswith('https://')):
                raise forms.ValidationError(
                    {'image_3_url': 'Image 3 URL must start with http:// or https://'}
                )
        
        return cleaned_data


@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    """
    Admin interface for Crop model.
    
    Features:
    - List view with image preview
    - Search by crop name
    - Filter by season
    - Inline image preview in edit form
    - Instructions for image upload vs URL
    """
    
    # Custom form with URL validation
    form = CropForm
    
    # List display columns
    list_display = [
        'name',
        'image_1_preview',
        'image_2_preview',
        'image_3_preview',
        'created_at'
    ]
    
    # Search fields
    search_fields = ['name']
    
    # Filter sidebar
    list_filter = ['created_at']
    
    # Ordering
    ordering = ['name']
    
    # Fields in the edit form - Only name and 3 images
    fieldsets = (
        ('Crop Name', {
            'fields': ('name',)
        }),
        ('Image 1', {
            'description': (
                '<strong>Choose one:</strong> Upload an image file OR paste an image URL. '
                'If both are provided, uploaded file takes priority.'
            ),
            'fields': ('image', 'image_url', 'image_1_preview_large')
        }),
        ('Image 2', {
            'description': (
                '<strong>Choose one:</strong> Upload an image file OR paste an image URL. '
                'If both are provided, uploaded file takes priority.'
            ),
            'fields': ('image_2', 'image_2_url', 'image_2_preview_large')
        }),
        ('Image 3', {
            'description': (
                '<strong>Choose one:</strong> Upload an image file OR paste an image URL. '
                'If both are provided, uploaded file takes priority.'
            ),
            'fields': ('image_3', 'image_3_url', 'image_3_preview_large')
        }),
    )
    
    # Read-only fields (for previews)
    readonly_fields = [
        'image_1_preview_large',
        'image_2_preview_large',
        'image_3_preview_large'
    ]
    
    # Items per page
    list_per_page = 25
    
    def image_1_preview(self, obj):
        """Show image 1 thumbnail in list view."""
        image_url = obj.get_image_url(1)
        return format_html(
            '<img src="{}" style="max-height: 40px; max-width: 60px; object-fit: cover; border-radius: 4px;" />',
            image_url
        )
    image_1_preview.short_description = 'Image 1'
    
    def image_2_preview(self, obj):
        """Show image 2 thumbnail in list view."""
        image_url = obj.get_image_url(2)
        return format_html(
            '<img src="{}" style="max-height: 40px; max-width: 60px; object-fit: cover; border-radius: 4px;" />',
            image_url
        )
    image_2_preview.short_description = 'Image 2'
    
    def image_3_preview(self, obj):
        """Show image 3 thumbnail in list view."""
        image_url = obj.get_image_url(3)
        return format_html(
            '<img src="{}" style="max-height: 40px; max-width: 60px; object-fit: cover; border-radius: 4px;" />',
            image_url
        )
    image_3_preview.short_description = 'Image 3'
    
    def image_1_preview_large(self, obj):
        """Show larger image 1 preview in edit form."""
        if obj.pk:
            image_url = obj.get_image_url(1)
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 300px; object-fit: contain; border: 1px solid #ddd; padding: 5px; border-radius: 4px;" />'
                '<br/><small>Current URL: {}</small>',
                image_url,
                image_url
            )
        return "Save the crop first to see preview"
    image_1_preview_large.short_description = 'Current Image 1 Preview'
    
    def image_2_preview_large(self, obj):
        """Show larger image 2 preview in edit form."""
        if obj.pk:
            image_url = obj.get_image_url(2)
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 300px; object-fit: contain; border: 1px solid #ddd; padding: 5px; border-radius: 4px;" />'
                '<br/><small>Current URL: {}</small>',
                image_url,
                image_url
            )
        return "Save the crop first to see preview"
    image_2_preview_large.short_description = 'Current Image 2 Preview'
    
    def image_3_preview_large(self, obj):
        """Show larger image 3 preview in edit form."""
        if obj.pk:
            image_url = obj.get_image_url(3)
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 300px; object-fit: contain; border: 1px solid #ddd; padding: 5px; border-radius: 4px;" />'
                '<br/><small>Current URL: {}</small>',
                image_url,
                image_url
            )
        return "Save the crop first to see preview"
    image_3_preview_large.short_description = 'Current Image 3 Preview'


@admin.register(PredictionLog)
class PredictionLogAdmin(admin.ModelAdmin):
    """
    Admin interface for PredictionLog model.
    
    Read-only view for analytics and debugging.
    """
    
    # List display columns
    list_display = [
        'id',
        'created_at',
        'top_prediction',
        'input_summary',
        'ip_address'
    ]
    
    # Search fields
    search_fields = ['ip_address']
    
    # Filter sidebar
    list_filter = ['created_at']
    
    # Ordering (newest first)
    ordering = ['-created_at']
    
    # All fields read-only
    readonly_fields = [
        'nitrogen', 'phosphorus', 'potassium',
        'temperature', 'humidity', 'ph', 'rainfall',
        'predictions', 'created_at', 'ip_address',
        'formatted_predictions'
    ]
    
    # Fieldsets for edit view
    fieldsets = (
        ('Input Parameters', {
            'fields': (
                ('nitrogen', 'phosphorus', 'potassium'),
                ('temperature', 'humidity'),
                ('ph', 'rainfall')
            )
        }),
        ('Predictions', {
            'fields': ('formatted_predictions',)
        }),
        ('Metadata', {
            'fields': ('ip_address', 'created_at')
        }),
    )
    
    # Items per page
    list_per_page = 50
    
    # Disable add/delete in admin
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def top_prediction(self, obj):
        """Show the top predicted crop."""
        if obj.predictions and len(obj.predictions) > 0:
            top = obj.predictions[0]
            return f"{top.get('crop', 'N/A')} ({top.get('confidence', 0):.1f}%)"
        return "N/A"
    top_prediction.short_description = 'Top Prediction'
    
    def input_summary(self, obj):
        """Show a brief summary of input parameters."""
        return f"N:{obj.nitrogen:.0f} P:{obj.phosphorus:.0f} K:{obj.potassium:.0f} | T:{obj.temperature:.1f}°C"
    input_summary.short_description = 'Inputs'
    
    def formatted_predictions(self, obj):
        """Show formatted predictions in edit view."""
        if not obj.predictions:
            return "No predictions"
        
        html = '<table style="border-collapse: collapse;">'
        html += '<tr><th style="padding: 5px; border: 1px solid #ddd;">Rank</th>'
        html += '<th style="padding: 5px; border: 1px solid #ddd;">Crop</th>'
        html += '<th style="padding: 5px; border: 1px solid #ddd;">Confidence</th></tr>'
        
        for i, pred in enumerate(obj.predictions, 1):
            html += f'<tr>'
            html += f'<td style="padding: 5px; border: 1px solid #ddd;">{i}</td>'
            html += f'<td style="padding: 5px; border: 1px solid #ddd;">{pred.get("crop", "N/A")}</td>'
            html += f'<td style="padding: 5px; border: 1px solid #ddd;">{pred.get("confidence", 0):.2f}%</td>'
            html += f'</tr>'
        
        html += '</table>'
        return mark_safe(html)
    formatted_predictions.short_description = 'Prediction Results'


# Customize admin site header
admin.site.site_header = "Crop Recommendation System - Admin"
admin.site.site_title = "CRS Admin"
admin.site.index_title = "Manage Crops & View Predictions"
