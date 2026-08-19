from django.apps import AppConfig


class AppsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps"

    def ready(self):
        # Pre-load nutrition data at startup
        from .nutrition import load_nutrition_cache
        load_nutrition_cache()

