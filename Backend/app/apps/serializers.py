"""
Crop Recommendation System - Serializers
========================================
Handles API request/response serialization using Django REST Framework.
"""

from rest_framework import serializers
from .models import Crop, PredictionLog


class CropSerializer(serializers.ModelSerializer):
    """
    Serializer for Crop model - used in admin/list views.
    """
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Crop
        fields = [
            'id', 'name', 'image_url', 'expected_yield', 
            'season', 'description', 'created_at'
        ]
    
    def get_image_url(self, obj):
        """Returns the resolved image URL using model's priority logic."""
        request = self.context.get('request')
        image_url = obj.get_image_url()
        
        # If it's a local file, build absolute URL
        if obj.image and hasattr(obj.image, 'url'):
            if request:
                return request.build_absolute_uri(image_url)
        return image_url


class PredictionInputSerializer(serializers.Serializer):
    """
    Validates incoming prediction request data.
    
    Expected Input:
    {
        "N": number,
        "P": number,
        "K": number,
        "temperature": number,
        "humidity": number,
        "ph": number,
        "rainfall": number
    }
    """
    
    N = serializers.FloatField(
        min_value=0,
        max_value=150,
        help_text="Nitrogen content in soil (kg/ha)"
    )
    P = serializers.FloatField(
        min_value=0,
        max_value=150,
        help_text="Phosphorus content in soil (kg/ha)"
    )
    K = serializers.FloatField(
        min_value=0,
        max_value=300,
        help_text="Potassium content in soil (kg/ha)"
    )
    temperature = serializers.FloatField(
        min_value=0,
        max_value=50,
        help_text="Average temperature (°C)"
    )
    humidity = serializers.FloatField(
        min_value=0,
        max_value=100,
        help_text="Relative humidity (%)"
    )
    ph = serializers.FloatField(
        min_value=3.5,
        max_value=9.5,
        help_text="Soil pH value"
    )
    rainfall = serializers.FloatField(
        min_value=0,
        max_value=3000,
        help_text="Annual rainfall (mm)"
    )


class CropRecommendationSerializer(serializers.Serializer):
    """
    Serializer for individual crop recommendation in response.
    """
    crop = serializers.CharField()
    confidence = serializers.FloatField()
    image_url = serializers.CharField()
    image_urls = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Array of 3 image URLs for carousel"
    )
    expected_yield = serializers.CharField(allow_null=True, required=False)
    season = serializers.CharField(allow_null=True, required=False)
    nutrition = serializers.DictField(allow_null=True, required=False, help_text="Nutrition data per kg")


class PredictionResponseSerializer(serializers.Serializer):
    """
    Serializer for the full prediction response.
    
    Expected Output:
    {
        "recommendations": [
            {
                "crop": "rice",
                "confidence": 98.6,
                "image_url": "string",
                "expected_yield": "string",
                "season": "string"
            },
            ...
        ]
    }
    """
    recommendations = CropRecommendationSerializer(many=True)


class PredictionLogSerializer(serializers.ModelSerializer):
    """
    Serializer for PredictionLog model - used for analytics.
    """
    class Meta:
        model = PredictionLog
        fields = '__all__'
        read_only_fields = ['created_at', 'ip_address']
