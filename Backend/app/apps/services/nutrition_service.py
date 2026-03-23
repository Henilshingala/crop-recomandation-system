import csv
import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class NutritionService:
    _instance = None
    _data = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NutritionService, cls).__new__(cls)
            cls._instance._load_data()
        return cls._instance

    def _load_data(self):
        csv_path = os.path.join(settings.BASE_DIR, '..', '..', 'Aiml', 'Nutrient.csv')
        # Normalize the path
        csv_path = os.path.abspath(csv_path)
        
        if not os.path.exists(csv_path):
            logger.error(f"Nutrient.csv not found at {csv_path}")
            return

        try:
            with open(csv_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Use food_name as key, normalized to lower case and snake_case for matching
                    name = row.get('food_name', '').lower().strip()
                    if name:
                        self._data[name] = row
            logger.info(f"Loaded {len(self._data)} nutritional entries from {csv_path}")
        except Exception as e:
            logger.error(f"Error loading Nutrient.csv: {e}")

    def get_nutrition(self, crop_name):
        """
        Get nutritional data for a crop. 
        Tries to match normalized name.
        """
        if not crop_name:
            return None
            
        lookup_name = crop_name.lower().strip()
        
        # Exact match
        if lookup_name in self._data:
            return self._data[lookup_name]
            
        # Partial match / cleaning
        # Handle things like "rice (white)" or "bajra"
        for key in self._data.keys():
            if lookup_name in key or key in lookup_name:
                return self._data[key]
                
        return None

nutrition_service = NutritionService()
