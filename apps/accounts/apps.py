# apps.py
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'

    def ready(self):
        # Importa e registra os modelos para auditoria
        from .signals import register_auditlog
        register_auditlog()