from django.apps import AppConfig


class AiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Ai"
    verbose_name = "AI Assistant"

    def ready(self):
        try:
            from .views import get_model
            get_model()
        except ImportError:
            pass
