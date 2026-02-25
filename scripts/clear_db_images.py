#!/usr/bin/env python3
"""
Clear all image references from Django database.
"""

import os
import sys
import django
from pathlib import Path

# Add Django path
sys.path.append(str(Path(__file__).parent.parent / "Backend" / "app"))

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from apps.models import Crop

def clear_database_images():
    """Clear all image references from Crop model."""
    print("Clearing database images...")
    
    # Get all crops
    crops = Crop.objects.all()
    print(f"Found {crops.count()} crops in database")
    
    # Clear image fields
    cleared_count = 0
    for crop in crops:
        if crop.image:
            print(f"Clearing image for crop: {crop.name}")
            crop.image = None
            crop.save()
            cleared_count += 1
    
    print(f"Cleared images for {cleared_count} crops")
    
    # Verify no images remain
    remaining_images = Crop.objects.exclude(image__isnull=True).exclude(image='')
    print(f"Remaining images in DB: {remaining_images.count()}")
    
    return cleared_count

def delete_media_files():
    """Delete all image files from media directory."""
    print("\nDeleting media files...")
    
    media_dir = Path(__file__).parent.parent / "Backend" / "app" / "media"
    if media_dir.exists():
        image_files = list(media_dir.rglob("*.jpg")) + list(media_dir.rglob("*.png")) + list(media_dir.rglob("*.jpeg"))
        
        deleted_count = 0
        for img_file in image_files:
            print(f"Deleting: {img_file}")
            img_file.unlink()
            deleted_count += 1
        
        print(f"Deleted {deleted_count} image files")
    else:
        print("Media directory not found")

def main():
    """Main function."""
    print("=== DATABASE IMAGE RESET ===")
    
    cleared_count = clear_database_images()
    delete_media_files()
    
    print(f"\n✅ Database image reset complete")
    print(f"   Cleared {cleared_count} image references")
    print("   All media files deleted")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
