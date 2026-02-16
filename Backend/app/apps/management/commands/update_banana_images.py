"""
Update banana crop images in the database
"""
from django.core.management.base import BaseCommand
from apps.models import Crop


class Command(BaseCommand):
    help = 'Update banana crop images'

    def handle(self, *args, **options):
        try:
            # Get or create banana crop
            banana, created = Crop.objects.get_or_create(
                name='banana',
                defaults={
                    'expected_yield': '30-50 tons/hectare',
                    'season': 'Year-round',
                    'description': 'Recommended crop: banana'
                }
            )
            
            # Update image URLs
            banana.image_url = 'https://raw.githubusercontent.com/Henilshingala/crop-recomandation-system/main/Backend/app/media/crops/banana1.webp'
            banana.image_2_url = 'https://raw.githubusercontent.com/Henilshingala/crop-recomandation-system/main/Backend/app/media/crops/banana2.jpg'
            banana.image_3_url = 'https://raw.githubusercontent.com/Henilshingala/crop-recomandation-system/main/Backend/app/media/crops/banana3.jpg'
            
            banana.save()
            
            self.stdout.write(self.style.SUCCESS(f'✅ Successfully updated banana crop images'))
            self.stdout.write(f'   Image 1: {banana.image_url}')
            self.stdout.write(f'   Image 2: {banana.image_2_url}')
            self.stdout.write(f'   Image 3: {banana.image_3_url}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error updating banana: {str(e)}'))
