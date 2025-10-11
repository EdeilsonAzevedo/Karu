from django.db.models.signals import post_save
from django.dispatch import receiver
from auditlog.models import LogEntry
from apps.patients.models import ClinicalWarningSign
from .tasks import create_consultation_alert  # ← MUDE PARA A NOVA FUNÇÃO
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=ClinicalWarningSign)
def handle_warning_sign_creation(sender, instance, created, **kwargs):
    """
    Dispara alerta AGREGADO quando sinais críticos são criados
    """
    if instance.is_present:
        # Dispara alerta agrupado por CONSULTA
        create_consultation_alert.apply_async(
            args=[instance.record_id], 
            countdown=10  # Espera 10 segundos para agrupar todos os sinais da mesma consulta
        )
        logger.info(f"📢 SIGNAL: Alerta agrupado disparado para consulta {instance.record_id}")

@receiver(post_save, sender=LogEntry)
def handle_audit_log(sender, instance, created, **kwargs):
    """
    Monitora logs de auditoria para ações críticas
    """
    # Filtra ações relevantes para alertas
    critical_actions = [
        'patients.patient', 
        'patients.clinicalwarningSign',
        'patients.consultationrecord'
    ]
    
    if instance.content_type.model in critical_actions and instance.action == LogEntry.Action.DELETE:
        # Dispara alerta para deleções críticas
        from .tasks import send_system_alert
        send_system_alert.delay(
            f"Exclusão crítica detectada: {instance.object_repr}",
            f"Usuário {instance.actor} excluiu {instance.object_repr}"
        )