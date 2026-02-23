"""
Management command: prune_logs
==============================
Deletes PredictionLog entries older than N days. Default 90 days.

Usage::

    python manage.py prune_logs           # delete older than 90 days
    python manage.py prune_logs --days 30 # delete older than 30 days
    python manage.py prune_logs --dry     # preview only
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.models import PredictionLog


class Command(BaseCommand):
    help = "Delete PredictionLog entries older than N days (default 90)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Delete logs older than this many days (default: 90)",
        )
        parser.add_argument(
            "--dry",
            action="store_true",
            help="Show count without deleting.",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry = options["dry"]
        cutoff = timezone.now() - timedelta(days=days)

        to_delete = PredictionLog.objects.filter(created_at__lt=cutoff)
        count = to_delete.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS(f"No logs older than {days} days."))
            return

        if dry:
            self.stdout.write(self.style.WARNING(
                f"[DRY RUN] Would delete {count} log(s) older than {days} days."
            ))
            return

        to_delete.delete()
        self.stdout.write(self.style.SUCCESS(
            f"Deleted {count} PredictionLog(s) older than {days} days."
        ))
