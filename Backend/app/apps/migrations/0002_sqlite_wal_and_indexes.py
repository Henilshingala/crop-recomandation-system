# Phase 3: SQLite WAL mode + indexes on PredictionLog

from django.db import connection, migrations, models


def enable_wal(apps, schema_editor):
    if connection.vendor == "sqlite3":
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.execute("PRAGMA cache_size=-64000;")


def disable_wal(apps, schema_editor):
    if connection.vendor == "sqlite3":
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA journal_mode=DELETE;")


class Migration(migrations.Migration):

    dependencies = [
        ("apps", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(enable_wal, disable_wal),
        migrations.AddIndex(
            model_name="predictionlog",
            index=models.Index(fields=["created_at"], name="apps_predic_created_idx"),
        ),
        migrations.AddIndex(
            model_name="predictionlog",
            index=models.Index(fields=["ip_address"], name="apps_predic_ip_addr_idx"),
        ),
    ]
