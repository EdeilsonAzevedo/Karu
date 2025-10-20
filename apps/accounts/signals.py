# signals.py
from auditlog.registry import auditlog
from django.contrib.auth import get_user_model

from .models import Filho, GestorProfile, PaisProfile, ProfissionalSaudeProfile

User = get_user_model()

def register_auditlog():
    """Registra os modelos para auditoria"""
    # Remove registros anteriores para evitar duplicação
    try:
        auditlog.unregister(User)
    except Exception:
        pass
    
    try:
        auditlog.unregister(GestorProfile)
    except Exception:
        pass
    
    try:
        auditlog.unregister(ProfissionalSaudeProfile)
    except Exception:
        pass
    
    try:
        auditlog.unregister(PaisProfile)
    except Exception:
        pass
    
    try:
        auditlog.unregister(Filho)
    except Exception:
        pass

    # Registrar modelos para auditoria
    auditlog.register(
        User,
        exclude_fields=['password', 'last_login', 'groups', 'user_permissions']
    )
    auditlog.register(GestorProfile)
    auditlog.register(ProfissionalSaudeProfile)
    auditlog.register(PaisProfile)
    auditlog.register(Filho)

# Chamar a função para registrar
register_auditlog()