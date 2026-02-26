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

    def _find_image_file(self, crop_name: str, num: int) -> str | None:
        """Scan media/crops/ for {crop_name}{num}.{ext}"""
        import os
        from django.conf import settings
        
        media_root = settings.MEDIA_ROOT
        crops_dir = os.path.join(media_root, 'crops')
        
        if not os.path.exists(crops_dir):
            return None
            
        extensions = ['.jpg', '.jpeg', '.png', '.webp', '.avif']
        # Try both "apple1.jpg" and "apple.jpg" (for num=1)
        search_names = [f"{crop_name.lower()}{num}", crop_name.lower()] if num == 1 else [f"{crop_name.lower()}{num}"]
        
        for name in search_names:
            for ext in extensions:
                filename = f"{name}{ext}"
                if os.path.exists(os.path.join(crops_dir, filename)):
                    return f"crops/{filename}"
        return None

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing crops',
        )

    def handle(self, *args, **options):
        # 🔍 1. ML Fetch & Debug
        from apps.ml_inference import get_available_crops
        ml_crops = get_available_crops(mode="both")
        self.stdout.write(self.style.SUCCESS(f"TOTAL CROPS FROM ML: {len(ml_crops)}"))

        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        # Track names found in this run to ensure uniqueness
        processed_names = set()

        for crop_name in ml_crops:
            # Normalize for detection
            clean_name = crop_name.strip()
            lookup_name = clean_name.lower()
            
            if lookup_name in processed_names:
                continue
            processed_names.add(lookup_name)

            # Get metadata if available, otherwise use defaults
            metadata = self.CROP_METADATA.get(lookup_name, {
                'season': 'Various',
                'expected_yield': 'Varies'
            })
            
            # Robust Check: Use filter().first()
            crop = Crop.objects.filter(name__iexact=clean_name).first()

            # Find matching local images
            img1 = self._find_image_file(clean_name, 1)
            img2 = self._find_image_file(clean_name, 2)
            img3 = self._find_image_file(clean_name, 3)

            if not crop:
                # CREATION: Use the exact Case provided by ML Registry
                crop = Crop.objects.create(
                    name=clean_name,
                    season=metadata.get('season', 'Various'),
                    expected_yield=metadata.get('expected_yield', 'Varies'),
                    description=f"Recommended crop species: {clean_name}. Data provided by ML consensus.",
                    image=img1 if img1 else None,
                    image_2=img2 if img2 else None,
                    image_3=img3 if img3 else None,
                )
                created_count += 1
                self.stdout.write(f"  [CREATED] {clean_name} (Auto-Image: {'Yes' if img1 else 'No'})")
            else:
                # UPDATE logic: Only update images IF they are currently empty (prevent overwriting admin uploads)
                modified = False
                if not crop.image and img1:
                    crop.image = img1
                    modified = True
                if not crop.image_2 and img2:
                    crop.image_2 = img2
                    modified = True
                if not crop.image_3 and img3:
                    crop.image_3 = img3
                    modified = True
                    
                if options.get('force'):
                    crop.name = clean_name 
                    crop.season = metadata.get('season', crop.season)
                    crop.expected_yield = metadata.get('expected_yield', crop.expected_yield)
                    modified = True

                if modified:
                    crop.save()
                    updated_count += 1
                    self.stdout.write(f"  [UPDATED] {clean_name}")
                else:
                    skipped_count += 1

        # 🔍 2. Final Result Logs
        self.stdout.write("\n" + "="*40)
        self.stdout.write(self.style.SUCCESS(
            f"SUMMARY: Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}"
        ))
        self.stdout.write(self.style.SUCCESS(f"TOTAL CROPS IN DB: {Crop.objects.count()}"))
        self.stdout.write("="*40)
