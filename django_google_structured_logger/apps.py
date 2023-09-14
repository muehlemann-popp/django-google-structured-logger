from django.apps import AppConfig  # type: ignore


class DjangoMaterializedViewAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_google_structured_logger"
