from auditlog.registry import auditlog
from django.contrib.auth import get_user_model
from .models import GestorProfile, ProfissionalSaudeProfile, PaisProfile

User = get_user_model()

def register_auditlog():
    """Registra os modelos para auditoria"""
    auditlog.register(
        User,
        exclude_fields=['password', 'last_login', 'groups', 'user_permissions']
    )
    auditlog.register(GestorProfile)
    auditlog.register(ProfissionalSaudeProfile)
    auditlog.register(PaisProfile)

# Chamar a função para registrar
register_auditlog()