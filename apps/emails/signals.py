from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
import threading
import time
from django.db import transaction
from apps.patients.models import ClinicalWarningSign, ConsultationRecord, Record
from apps.emails.tasks import send_consolidated_alert, send_weight_gain_alert
from apps.emails.models import EmailAlert, AlertType
import logging

logger = logging.getLogger(__name__)

# Dicionário para controlar consultas em processamento
processing_records = {}

@receiver(post_save, sender=ClinicalWarningSign)
def handle_critical_warning_sign(sender, instance, created, **kwargs):
    """
    Detecta quando sinais críticos são marcados com controle de duplicatas
    """
    if instance.is_present and instance.type in [
        'hypothermia', 'respiratory_pause', 'skin_perfusion',
        'regurgitation', 'hypoactivity', 'jaundice', 'abnormalities'
    ]:
        record_id = str(instance.record.id)
        
        # Verifica se já está processando esta consulta
        if record_id in processing_records:
            logger.info(f"⏳ Consulta {record_id} já está sendo processada")
            return
        
        # Marca como em processamento
        processing_records[record_id] = True
        
        def delayed_check():
            try:
                # Aguarda 15 segundos para agrupar todos os sinais
                time.sleep(15)
                
                # Verifica se ainda deve enviar
                recent_alerts = EmailAlert.objects.filter(
                    record_id=instance.record.id,
                    alert_type=AlertType.CRITICAL_WARNING_SIGN,
                    created_at__gte=timezone.now() - timedelta(minutes=10)
                )
                
                if not recent_alerts.exists():
                    logger.info(f"📧 Enviando alerta consolidado para consulta {record_id}")
                    send_consolidated_alert.delay(instance.record.id)
                else:
                    logger.info(f"⏰ Alerta recente já existe para consulta {record_id}")
                
            except Exception as e:
                logger.error(f"Erro no processamento consolidado: {e}")
            finally:
                # Remove do controle de processamento
                if record_id in processing_records:
                    del processing_records[record_id]
        
        thread = threading.Thread(target=delayed_check)
        thread.daemon = True
        thread.start()


@receiver(post_save, sender=Record)
def handle_record_completion(sender, instance, created, **kwargs):
    """
    Verifica sinais críticos e ganho de peso quando um registro é salvo
    """
    if instance.record_type == 'consultation' and instance.pk:
        def schedule_alerts():
            record_id = str(instance.id)
            
            # Evita duplicatas
            if record_id in processing_records:
                return
            
            processing_records[record_id] = True
            
            def check_alerts():
                try:
                    time.sleep(5)  # Aguarda 5 segundos para garantir o save
                    
                    # ✅ VERIFICA SE O RECORD AINDA EXISTE
                    try:
                        Record.objects.get(id=instance.id)
                    except Record.DoesNotExist:
                        logger.warning(f"Record {instance.id} não existe mais - cancelando task")
                        return
                    
                    # Verifica sinais críticos consolidados
                    critical_signs = ClinicalWarningSign.objects.filter(
                        record=instance,
                        is_present=True,
                        type__in=[
                            'hypothermia', 'respiratory_pause', 'skin_perfusion',
                            'regurgitation', 'hypoactivity', 'jaundice', 'abnormalities'
                        ]
                    )
                    
                    if critical_signs.exists():
                        recent_alerts = EmailAlert.objects.filter(
                            record=instance,
                            alert_type=AlertType.CRITICAL_WARNING_SIGN,
                            created_at__gte=timezone.now() - timedelta(minutes=10)
                        )
                        
                        if not recent_alerts.exists():
                            from apps.emails.tasks import send_consolidated_alert
                            send_consolidated_alert.delay(instance.id)
                    
                    # SEMPRE verifica ganho de peso
                    from apps.emails.tasks import check_weight_gain_issues
                    logger.info(f"📈 Signal disparando verificação de peso para record {instance.id}")
                    check_weight_gain_issues.delay(instance.id)
                            
                except Exception as e:
                    logger.error(f"Erro no processamento do record: {e}")
                finally:
                    if record_id in processing_records:
                        del processing_records[record_id]
            
            thread = threading.Thread(target=check_alerts)
            thread.daemon = True
            thread.start()

        transaction.on_commit(schedule_alerts)