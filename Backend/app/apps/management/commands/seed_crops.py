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
        'finger_millet': {'season': 'Kharif', 'expected_yield': '1-2 tons/hectare'},
        'sorghum': {'season': 'Kharif', 'expected_yield': '1.5-3 tons/hectare'},
        'pearl_millet': {'season': 'Kharif', 'expected_yield': '1-2 tons/hectare'},
        
        # Pulses
        'chickpea': {'season': 'Rabi', 'expected_yield': '0.8-1.5 tons/hectare'},
        'kidneybeans': {'season': 'Kharif', 'expected_yield': '1-1.5 tons/hectare'},
        'pigeonpeas': {'season': 'Kharif', 'expected_yield': '0.8-1.2 tons/hectare'},
        'pigeonpea': {'season': 'Kharif', 'expected_yield': '0.8-1.2 tons/hectare'},
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
        'okra': {'season': 'Summer/Kharif', 'expected_yield': '10-15 tons/hectare'},
        'bottle_gourd': {'season': 'Summer', 'expected_yield': '25-35 tons/hectare'},
        'bitter_gourd': {'season': 'Summer', 'expected_yield': '10-15 tons/hectare'},
        'ridge_gourd': {'season': 'Summer', 'expected_yield': '12-18 tons/hectare'},
        'cucumber': {'season': 'Summer', 'expected_yield': '20-30 tons/hectare'},
        'pumpkin': {'season': 'Summer/Kharif', 'expected_yield': '20-30 tons/hectare'},
        
        # Spices
        'chilli': {'season': 'Kharif', 'expected_yield': '1.5-2.5 tons/hectare'},
        'green_chilli': {'season': 'Kharif', 'expected_yield': '1.5-2.5 tons/hectare'},
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
        'sesamum': {'season': 'Kharif', 'expected_yield': '0.3-0.5 tons/hectare'},
        'castor': {'season': 'Kharif', 'expected_yield': '1-1.5 tons/hectare'},
        'linseed': {'season': 'Rabi', 'expected_yield': '0.8-1.2 tons/hectare'},
        'safflower': {'season': 'Rabi', 'expected_yield': '0.8-1.5 tons/hectare'},
        'tobacco': {'season': 'Rabi', 'expected_yield': '1.5-2.5 tons/hectare'},
        
        # Merged categories (from data augmentation)
        'gourd': {'season': 'Summer', 'expected_yield': '15-25 tons/hectare'},
        'cole_crop': {'season': 'Rabi', 'expected_yield': '25-35 tons/hectare'},
        'citrus': {'season': 'Winter', 'expected_yield': '15-20 tons/hectare'},
    }

    # Expert mapping (for tricky filenames like b1, c1)
    _CROP_IMAGES = {
        "apple":          ["apple1.jpeg", "apple2.jpg", "apple3.jpg"],
        "bajra":          ["bajra1.jpg", "bajra2.webp", "bajra3.avif"],
        "banana":         ["banana1.webp", "banana2.jpg", "banana3.webp"],
        "barley":         ["c1.webp", "c2.jpg", "c3.jpg"],
        "ber":            ["ber1.webp", "ber2.jpg", "ber3.webp"],
        "blackgram":      ["blackgram1.jpg", "blackgram2.webp", "BlackGram3.jpg"],
        "brinjal":        ["brinjal1.avif", "brinjal2.jpg", "brinjal3.webp"],
        "carrot":         ["carrot1.webp", "carrot2.webp", "carrot3.jpg"],
        "castor":         ["castor1.jpg", "castor2.jpg", "castor3.jpg"],
        "chickpea":       ["chickpea1.webp", "chickpea2.avif", "chickpea3.png"],
        "citrus":         ["citrus1.jpg", "citrus2.jpg", "citrus3.jpg"],
        "coconut":        ["coconut1.jpg", "coconut2.webp", "coconut3.jpg"],
        "coffee":         ["coffee1.jpg", "coffee2.avif", "coffee3.jpg"],
        "cole_crop":      ["cole_crop1.jpg", "cole_crop2.jpg", "cole_crop3.jpg"],
        "cotton":         ["cotton1.jpg", "cotton2.webp", "cotton3.webp"],
        "cucumber":       ["Cucumber1.jpg", "cucumber2.webp", "cucumber3.webp"],
        "custard_apple":  ["custard_apple1.jpg", "custard_apple2.jpg", "custard_apple3.jpg"],
        "date_palm":      ["date_palm1.webp", "date_palm2.jpg", "date_palm3.jpg"],
        "finger_millet":  ["finger_millet1.webp", "finger_millet2.jpg", "finger_millet3.jpg"],
        "gourd":          ["gourd1.webp", "gourd2.jpg", "gourd3.jpg"],
        "grapes":         ["grapes1.webp", "grapes2.jpg", "grapes3.jpg"],
        "green_chilli":   ["green_chilli1.jpg", "green_chilli2.webp", "green_chilli3.jpg"],
        "groundnut":      ["groundnut1.jpg", "groundnut2.jpg", "groundnut3.jpg"],
        "guava":          ["guava1.jpg", "guava2.jpg", "guava3.jpg"],
        "jowar":          ["jowar1.webp", "jowar2.jpg", "jowar3.jpg"],
        "jute":           ["jute1.webp", "jute2.jpg", "jute3.jpg"],
        "kidneybeans":    ["kindneybeans1.avif", "kindneybeans2.webp", "kindneybeans3.jpg"],
        "lentil":         ["lentil1.jpg", "lentil2.jpg", "lentil3.jpg"],
        "linseed":        ["linseed1.jpg", "linseed2.webp", "linseed3.jpg"],
        "maize":          ["maize1.jpg", "maize2.webp", "maize3.jpg"],
        "mango":          ["mango1.jpg", "mango2.jpg", "mango3.webp"],
        "mothbeans":      ["mothbeans1.webp", "mothbeans2.webp", "mothbeans3.jpg"],
        "mungbean":       ["mungbean1.webp", "mungbean2.jpg", "mungbean3.webp"],
        "muskmelon":      ["muskmelon1.jpg", "muskmelon2.jpg", "muskmelon3.webp"],
        "mustard":        ["mustard1.avif", "mustard2.jpg", "mustard4.jpg"],
        "okra":           ["okra1.jpg", "okra2.jpg", "okra3.jpg"],
        "onion":          ["onion1.jpg", "onion2.webp", "onion3.webp"],
        "papaya":         ["papaya1.jpg", "papaya2.jpg", "papaya3.webp"],
        "pearl_millet":   ["pearl_millet1.jpg", "pearl_millet2.avif", "pearl_millet3.webp"],
        "pigeonpea":      ["pigeonpeas1.jpg", "pigeonpeas2.jpg", "pigeonpeas3.jpg"],
        "pigeonpeas":     ["pigeonpeas1.jpg", "pigeonpeas2.jpg", "pigeonpeas3.jpg"],
        "pomegranate":    ["pomegranate.png", "pomegranate2.jpg", "pomegranate3.jpg"],
        "potato":         ["potato1.jpeg", "potato2.jpg", "potato3.jpg"],
        "radish":         ["radish1.jpg", "radish2.jpg", "radish3.jpg"],
        "ragi":           ["ragi1.webp", "ragi2.jpg", "ragi3.jpg"],
        "rice":           ["rice1.jpeg", "rice2.jpg", "rice3.avif"],
        "safflower":      ["safflower1.jpg", "safflower2.webp", "safflower3.jpg"],
        "sapota":         ["sapota1.webp", "sapota2.jpg", "sapota3.webp"],
        "sesame":         ["sesame1.jpg", "sesame2.webp", "sesame3.jpg"],
        "sesamum":        ["sesamum1.jpg", "sesame1.jpg", "sesame2.webp"],
        "sorghum":        ["sorghum1.webp", "sorghum2.jpg", "sorghum3.jpg"],
        "soybean":        ["soybean1.webp", "soybean2.jpg", "soybean3.webp"],
        "spinach":        ["spinach1.jpg", "spinach2.jpg", "spinach3.jpg"],
        "sugarcane":      ["sugarcane1.webp", "sugarcane2.jpg", "sugarcane3.avif"],
        "sunflower":      ["sunflower1.jpg", "sunflower2.jpg", "sunflower3.webp"],
        "tobacco":        ["tobacco1.webp", "tobacco.jpg", "tobacco3.png"],
        "tomato":         ["tomato1.jpg", "tomato2.jpg", "tomato3.jpg"],
        "watermelon":     ["watermelon1.jpg", "watermelon2.jpg", "watermelon3.webp"],
        "wheat":          ["wheat2.jpg", "wheat3.jpg", "wheat3.png"],
    }

    def _find_image_file(self, crop_name: str, num: int) -> str | None:
        """Ultimate image matching: Expert Map -> Standard Name -> Greedy Search."""
        import os
        from django.conf import settings
        
        lookup_name = crop_name.lower().strip()
        media_root = settings.MEDIA_ROOT
        crops_dir = os.path.join(media_root, 'crops')
        
        if not os.path.exists(crops_dir):
            return None
            
        # 1. Check Expert Map
        mapped_images = self._CROP_IMAGES.get(lookup_name)
        if mapped_images and len(mapped_images) >= num:
            filename = mapped_images[num-1]
            if filename and os.path.exists(os.path.join(crops_dir, filename)):
                return f"crops/{filename}"

        # 2. Greedy Search: If slot X is missing, try to find ANY matching image for this crop
        # This handles cases like apple2 being image 1 if apple1 is missing.
        extensions = ['.jpg', '.jpeg', '.png', '.webp', '.avif']
        all_files = sorted([f for f in os.listdir(crops_dir) if f.lower().startswith(lookup_name)])
        
        # Filter for validity
        valid_files = [f for f in all_files if any(f.lower().endswith(ext) for ext in extensions)]
        
        if len(valid_files) >= num:
            return f"crops/{valid_files[num-1]}"
            
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
        
        # Track names found in this run
        processed_names = set()

        for crop_name in ml_crops:
            # Normalize
            clean_name = crop_name.strip()
            lookup_name = clean_name.lower()
            
            if lookup_name in processed_names:
                continue
            processed_names.add(lookup_name)

            # Metadata
            metadata = self.CROP_METADATA.get(lookup_name, {
                'season': 'Various',
                'expected_yield': 'Varies'
            })
            
            # Fetch Crop
            crop = Crop.objects.filter(name__iexact=clean_name).first()

            # Assign matching images
            img1 = self._find_image_file(clean_name, 1)
            img2 = self._find_image_file(clean_name, 2)
            img3 = self._find_image_file(clean_name, 3)

            if not crop:
                # CREATION
                crop = Crop.objects.create(
                    name=clean_name,
                    season=metadata.get('season', 'Various'),
                    expected_yield=metadata.get('expected_yield', 'Varies'),
                    description=f"Recommended crop: {clean_name}. Metadata managed by master registry.",
                    image=img1 if img1 else None,
                    image_2=img2 if img2 else None,
                    image_3=img3 if img3 else None,
                )
                created_count += 1
                self.stdout.write(f"  [CREATED] {clean_name} Images: " + 
                                f"{'1 ' if img1 else ''}{'2 ' if img2 else ''}{'3' if img3 else ''}")
            else:
                # UPDATE: Guard manual admin overrides
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
            f"SEALING COMPLETE | Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}"
        ))
        self.stdout.write(self.style.SUCCESS(f"TOTAL CROPS IN DB: {Crop.objects.count()}"))
        self.stdout.write("="*40)
