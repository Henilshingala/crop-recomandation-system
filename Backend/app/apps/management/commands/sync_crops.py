"""
Management command: sync_crops
==============================
Syncs the Crop database table with crops from both the HuggingFace
Space (original/v3) and the synthetic model.

Usage::

    python manage.py sync_crops          # normal sync
    python manage.py sync_crops --dry    # preview without writing

Idempotent — safe to run multiple times.
"""

from django.core.management.base import BaseCommand

from apps.services.crop_sync import (
    fetch_hf_crops,
    get_synthetic_crops,
    sync_crops_to_db,
)


class Command(BaseCommand):
    help = (
        "Sync Crop table with HuggingFace (original) + synthetic crop lists. "
        "Creates missing crops; never deletes existing ones."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry",
            action="store_true",
            help="Show what would be created without writing to the DB.",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("── Crop Sync ──"))

        # 1) Fetch HF crops
        self.stdout.write("Fetching crops from HuggingFace Space...")
        hf_crops = fetch_hf_crops()
        if hf_crops:
            self.stdout.write(self.style.SUCCESS(
                f"  HF original crops: {len(hf_crops)} → {', '.join(sorted(hf_crops))}"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                "  HF unreachable — will use only synthetic list"
            ))

        # 2) Synthetic crops
        synthetic_crops = get_synthetic_crops()
        self.stdout.write(f"  Synthetic crops:   {len(synthetic_crops)}")

        # 3) Merged set
        all_crops = sorted(set(
            [c.lower() for c in hf_crops] +
            [c.lower() for c in synthetic_crops]
        ))
        self.stdout.write(f"  Merged total:      {len(all_crops)}")

        # 4) Dry-run?
        if options["dry"]:
            from apps.models import Crop
            existing = set(
                Crop.objects.values_list("name", flat=True)
                    .iterator()
            )
            existing_lower = {n.lower() for n in existing}
            new_crops = [c for c in all_crops if c not in existing_lower]
            self.stdout.write("")
            if new_crops:
                self.stdout.write(self.style.WARNING(
                    f"Would create {len(new_crops)} new crop(s):"
                ))
                for c in new_crops:
                    self.stdout.write(f"  + {c}")
            else:
                self.stdout.write(self.style.SUCCESS("All crops already exist — nothing to do."))
            self.stdout.write(self.style.NOTICE("[DRY RUN — no changes written]"))
            return

        # 5) Sync
        created, skipped, total = sync_crops_to_db(
            hf_crops=hf_crops,
            synthetic_crops=synthetic_crops,
        )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Sync complete!  Created: {created}  |  Skipped (exists): {skipped}  |  DB total: {total}"
        ))
