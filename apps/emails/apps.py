from django.apps import AppConfig

class EmailsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.emails'
    
    def ready(self):
        import apps.emails.signals  # Isso deve carregar os signals