"""
Management command to seed the database with crop data.

Usage:
    python manage.py seed_crops

This populates the Crop table with all crops that the ML model can predict,
along with default metadata (expected yield, season).
"""

from django.core.management.base import BaseCommand
from apps.models import Crop
from apps.ml_inference import get_predictor


class Command(BaseCommand):
    help = 'Seed the database with crop data from the ML model'

    # Default crop metadata (can be updated via admin panel)
    CROP_METADATA = {
        # Cereals
        'rice': {'season': 'Kharif', 'expected_yield': '3-6 tons/hectare'},
        'wheat': {'season': 'Rabi', 'expected_yield': '2-4 tons/hectare'},
        'maize': {'season': 'Kharif/Rabi', 'expected_yield': '5-8 tons/hectare'},
        'barley': {'season': 'Rabi', 'expected_yield': '2-3 tons/hectare'},
        'jowar': {'season': 'Kharif', 'expected_yield': '1.5-3 tons/hectare'},
        'bajra': {'season': 'Kharif', 'expected_yield': '1-2 tons/hectare'},
        'ragi': {'season': 'Kharif', 'expected_yield': '1-2 tons/hectare'},
        
        # Pulses
        'chickpea': {'season': 'Rabi', 'expected_yield': '0.8-1.5 tons/hectare'},
        'kidneybeans': {'season': 'Kharif', 'expected_yield': '1-1.5 tons/hectare'},
        'pigeonpeas': {'season': 'Kharif', 'expected_yield': '0.8-1.2 tons/hectare'},
        'mothbeans': {'season': 'Kharif', 'expected_yield': '0.3-0.5 tons/hectare'},
        'mungbean': {'season': 'Kharif/Summer', 'expected_yield': '0.5-1 tons/hectare'},
        'blackgram': {'season': 'Kharif', 'expected_yield': '0.5-1 tons/hectare'},
        'lentil': {'season': 'Rabi', 'expected_yield': '0.8-1.2 tons/hectare'},
        'soybean': {'season': 'Kharif', 'expected_yield': '1.5-2.5 tons/hectare'},
        
        # Fruits
        'apple': {'season': 'Year-round', 'expected_yield': '10-15 tons/hectare'},
        'banana': {'season': 'Year-round', 'expected_yield': '30-50 tons/hectare'},
        'grapes': {'season': 'Year-round', 'expected_yield': '20-25 tons/hectare'},
        'mango': {'season': 'Summer', 'expected_yield': '8-12 tons/hectare'},
        'orange': {'season': 'Winter', 'expected_yield': '15-20 tons/hectare'},
        'papaya': {'season': 'Year-round', 'expected_yield': '40-60 tons/hectare'},
        'pomegranate': {'season': 'Year-round', 'expected_yield': '12-18 tons/hectare'},
        'watermelon': {'season': 'Summer', 'expected_yield': '25-35 tons/hectare'},
        'muskmelon': {'season': 'Summer', 'expected_yield': '15-20 tons/hectare'},
        'coconut': {'season': 'Year-round', 'expected_yield': '10000-15000 nuts/hectare'},
        'guava': {'season': 'Year-round', 'expected_yield': '15-25 tons/hectare'},
        'sapota': {'season': 'Year-round', 'expected_yield': '15-20 tons/hectare'},
        'lemon': {'season': 'Year-round', 'expected_yield': '15-20 tons/hectare'},
        'mosambi': {'season': 'Year-round', 'expected_yield': '12-18 tons/hectare'},
        'custard_apple': {'season': 'Monsoon', 'expected_yield': '6-10 tons/hectare'},
        'date_palm': {'season': 'Summer', 'expected_yield': '8-10 tons/hectare'},
        'ber': {'season': 'Winter', 'expected_yield': '8-12 tons/hectare'},
        
        # Vegetables
        'tomato': {'season': 'Year-round', 'expected_yield': '25-40 tons/hectare'},
        'potato': {'season': 'Rabi', 'expected_yield': '20-30 tons/hectare'},
        'onion': {'season': 'Rabi/Kharif', 'expected_yield': '25-35 tons/hectare'},
        'brinjal': {'season': 'Year-round', 'expected_yield': '30-40 tons/hectare'},
        'cabbage': {'season': 'Rabi', 'expected_yield': '30-45 tons/hectare'},
        'cauliflower': {'season': 'Rabi', 'expected_yield': '20-30 tons/hectare'},
        'carrot': {'season': 'Rabi', 'expected_yield': '25-35 tons/hectare'},
        'radish': {'season': 'Rabi', 'expected_yield': '20-30 tons/hectare'},
        'peas': {'season': 'Rabi', 'expected_yield': '8-12 tons/hectare'},
        'spinach': {'season': 'Rabi', 'expected_yield': '10-15 tons/hectare'},
        'ladyfinger': {'season': 'Summer/Kharif', 'expected_yield': '10-15 tons/hectare'},
        'bottle_gourd': {'season': 'Summer', 'expected_yield': '25-35 tons/hectare'},
        'bitter_gourd': {'season': 'Summer', 'expected_yield': '10-15 tons/hectare'},
        'ridge_gourd': {'season': 'Summer', 'expected_yield': '12-18 tons/hectare'},
        'cucumber': {'season': 'Summer', 'expected_yield': '20-30 tons/hectare'},
        'pumpkin': {'season': 'Summer/Kharif', 'expected_yield': '20-30 tons/hectare'},
        
        # Spices
        'chilli': {'season': 'Kharif', 'expected_yield': '1.5-2.5 tons/hectare'},
        'turmeric': {'season': 'Kharif', 'expected_yield': '20-25 tons/hectare'},
        'ginger': {'season': 'Kharif', 'expected_yield': '15-25 tons/hectare'},
        'garlic': {'season': 'Rabi', 'expected_yield': '8-12 tons/hectare'},
        'coriander': {'season': 'Rabi', 'expected_yield': '1-1.5 tons/hectare'},
        'cumin': {'season': 'Rabi', 'expected_yield': '0.4-0.6 tons/hectare'},
        'fenugreek': {'season': 'Rabi', 'expected_yield': '1-1.5 tons/hectare'},
        
        # Cash Crops
        'cotton': {'season': 'Kharif', 'expected_yield': '1.5-2.5 tons/hectare'},
        'jute': {'season': 'Kharif', 'expected_yield': '2-3 tons/hectare'},
        'sugarcane': {'season': 'Kharif', 'expected_yield': '70-100 tons/hectare'},
        'coffee': {'season': 'Year-round', 'expected_yield': '0.5-1 tons/hectare'},
        'tea': {'season': 'Year-round', 'expected_yield': '1.5-2.5 tons/hectare'},
        'groundnut': {'season': 'Kharif', 'expected_yield': '1.5-2 tons/hectare'},
        'sunflower': {'season': 'Rabi/Kharif', 'expected_yield': '1.5-2 tons/hectare'},
        'mustard': {'season': 'Rabi', 'expected_yield': '1-1.5 tons/hectare'},
        'sesame': {'season': 'Kharif', 'expected_yield': '0.3-0.5 tons/hectare'},
        
        # Merged categories (from data augmentation)
        'gourd': {'season': 'Summer', 'expected_yield': '15-25 tons/hectare'},
        'cole_crop': {'season': 'Rabi', 'expected_yield': '25-35 tons/hectare'},
        'citrus': {'season': 'Winter', 'expected_yield': '15-20 tons/hectare'},
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing crops',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting crop seeding...'))
        
        try:
            # Get available crops from ML model
            predictor = get_predictor()
            ml_crops = predictor.get_available_crops()
            
            self.stdout.write(f'Found {len(ml_crops)} crops in ML model')
            
            created_count = 0
            updated_count = 0
            skipped_count = 0
            
            for crop_name in ml_crops:
                # Get metadata if available, otherwise use defaults
                metadata = self.CROP_METADATA.get(crop_name.lower(), {
                    'season': 'Unknown',
                    'expected_yield': 'Varies'
                })
                
                crop, created = Crop.objects.get_or_create(
                    name=crop_name,
                    defaults={
                        'season': metadata.get('season', 'Unknown'),
                        'expected_yield': metadata.get('expected_yield', 'Varies'),
                        'description': f'Recommended crop: {crop_name}'
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'  Created: {crop_name}')
                elif options['force']:
                    # Update existing crop
                    crop.season = metadata.get('season', crop.season)
                    crop.expected_yield = metadata.get('expected_yield', crop.expected_yield)
                    crop.save()
                    updated_count += 1
                    self.stdout.write(f'  Updated: {crop_name}')
                else:
                    skipped_count += 1
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(
                f'Seeding complete! Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            raise
