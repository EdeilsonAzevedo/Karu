from django.apps import AppConfig


class EmailsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.emails"
    verbose_name = "Sistema de Email e Alertas"

    def ready(self):
        # Registra os signals
        pass