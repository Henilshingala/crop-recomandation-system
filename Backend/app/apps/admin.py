"""
Crop Recommendation System - Admin Configuration
================================================
Django admin panel customization for managing crops and viewing logs.
"""

from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Crop


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
    - List view with image preview and image count
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
        'image_count',
        'season',
        'created_at'
    ]
    
    # Search fields
    search_fields = ['name']
    
    # Filter sidebar
    list_filter = ['season', 'created_at']
    
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
    
    # Items per page - show all 69 crops on one page
    list_per_page = 69
    
    def image_count(self, obj):
        """Show how many image slots are filled (out of 3)."""
        count = 0
        if (obj.image and hasattr(obj.image, 'url')) or obj.image_url:
            count += 1
        if (obj.image_2 and hasattr(obj.image_2, 'url')) or obj.image_2_url:
            count += 1
        if (obj.image_3 and hasattr(obj.image_3, 'url')) or obj.image_3_url:
            count += 1
        
        if count == 3:
            return format_html('<span style="color: #28a745; font-weight: bold;">✅ {}/3</span>', count)
        elif count >= 1:
            return format_html('<span style="color: #ffc107; font-weight: bold;">⚠️ {}/3</span>', count)
        else:
            return format_html('<span style="color: #dc3545; font-weight: bold;">❌ 0/3</span>')
    image_count.short_description = 'Images'
    
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

# Customize admin site header
admin.site.site_header = "Crop Recommendation System - Admin"
admin.site.site_title = "CRS Admin"
admin.site.index_title = "Manage Crops"
