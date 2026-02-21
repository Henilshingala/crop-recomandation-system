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

    Required: N, P, K, temperature, humidity, ph, rainfall
    Optional: mode, soil_type, irrigation, moisture
    """

    MODE_CHOICES = [("original", "Original"), ("synthetic", "Synthetic"), ("both", "Both")]

    N = serializers.FloatField(
        min_value=0, max_value=150,
        help_text="Nitrogen content in soil (kg/ha)",
    )
    P = serializers.FloatField(
        min_value=0, max_value=150,
        help_text="Phosphorus content in soil (kg/ha)",
    )
    K = serializers.FloatField(
        min_value=0, max_value=300,
        help_text="Potassium content in soil (kg/ha)",
    )
    temperature = serializers.FloatField(
        min_value=0, max_value=50,
        help_text="Average temperature (°C)",
    )
    humidity = serializers.FloatField(
        min_value=0, max_value=100,
        help_text="Relative humidity (%)",
    )
    ph = serializers.FloatField(
        min_value=3.5, max_value=9.5,
        help_text="Soil pH value",
    )
    rainfall = serializers.FloatField(
        min_value=0, max_value=3000,
        help_text="Annual rainfall (mm)",
    )
    mode = serializers.ChoiceField(
        choices=MODE_CHOICES,
        default="original",
        required=False,
        help_text="Prediction mode: 'original' (HF v3, 19 crops), 'synthetic' (local, 51 crops), or 'both' (blended)",
    )
    soil_type = serializers.IntegerField(
        min_value=0, max_value=2,
        default=1,
        required=False,
        help_text="0=sandy, 1=loamy (default), 2=clay",
    )
    irrigation = serializers.IntegerField(
        min_value=0, max_value=1,
        default=0,
        required=False,
        help_text="0=rainfed (default), 1=irrigated",
    )
    moisture = serializers.FloatField(
        min_value=0, max_value=100,
        default=43.5,
        required=False,
        help_text="Soil moisture (%)",
    )


class CropRecommendationSerializer(serializers.Serializer):
    """Individual crop recommendation."""

    crop = serializers.CharField()
    confidence = serializers.FloatField()
    risk_level = serializers.CharField(
        required=False, default="medium",
        help_text="low / medium / high based on confidence",
    )
    image_url = serializers.CharField(allow_blank=True, required=False, default="")
    image_urls = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Array of image URLs for carousel",
    )
    expected_yield = serializers.CharField(allow_null=True, required=False)
    season = serializers.CharField(allow_null=True, required=False)
    nutrition = serializers.DictField(
        allow_null=True, required=False,
        help_text="Nutrition data per kg",
    )


class ModelInfoSerializer(serializers.Serializer):
    """Model metadata."""

    coverage = serializers.IntegerField(help_text="Number of crops the model covers")
    type = serializers.CharField(help_text="Model type (e.g. stacked-ensemble-v3)")
    version = serializers.CharField(required=False, help_text="Model version")
    fallback = serializers.BooleanField(required=False, default=False,
                                         help_text="True when HF was unreachable")


class PredictionResponseSerializer(serializers.Serializer):
    """
    Full prediction response.

    {
        "mode": "original" | "synthetic" | "both",
        "top_1": {"crop": "rice", "confidence": 98.6, ...},
        "top_3": [...],
        "model_info": {"coverage": 19, "type": "stacked-ensemble-v3", "version": "3.0"}
    }
    """

    mode = serializers.CharField()
    top_1 = CropRecommendationSerializer()
    top_3 = CropRecommendationSerializer(many=True)
    model_info = ModelInfoSerializer()


class PredictionLogSerializer(serializers.ModelSerializer):
    """
    Serializer for PredictionLog model - used for analytics.
    """
    class Meta:
        model = PredictionLog
        fields = '__all__'
        read_only_fields = ['created_at', 'ip_address']
