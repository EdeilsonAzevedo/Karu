from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from datetime import timedelta
import logging

from apps.emails.models import AlertType, AlertStatus, EmailAlert, EmailTemplate
from apps.patients.models import ClinicalWarningSign, Patient, Record, ConsultationRecord

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task
def send_critical_warning_alert(record_id, warning_sign_type):
    """
    Task para enviar alerta de sinal crítico
    """
    try:
        record = Record.objects.select_related('patient').get(id=record_id)
        patient = record.patient
        
        # Verifica se já existe um alerta pendente/sent para este paciente e sinal
        existing_alert = EmailAlert.objects.filter(
            patient=patient,
            alert_type=AlertType.CRITICAL_WARNING_SIGN,
            status__in=[AlertStatus.PENDING, AlertStatus.SENT],
            context_data__warning_sign_type=warning_sign_type,
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).first()
        
        if existing_alert:
            # Se existe e pode reenviar, atualiza e reenvia
            if existing_alert.can_resend():
                return resend_alert.delay(existing_alert.id)
            return f"Alerta já enviado recentemente: {existing_alert.id}"
        
        # Cria novo alerta
        warning_sign_display = dict(ClinicalWarningSign.WarningSignType.choices).get(warning_sign_type, warning_sign_type)
        
        alert = EmailAlert.objects.create(
            alert_type=AlertType.CRITICAL_WARNING_SIGN,
            patient=patient,
            record=record,
            title=f"🚨 Alerta Crítico - {patient.first_name} {patient.last_name}",
            message=f"Paciente {patient.first_name} {patient.last_name} apresentou {warning_sign_display} na consulta de {record.date.strftime('%d/%m/%Y')}.",
            context_data={
                "warning_sign_type": warning_sign_type,
                "warning_sign_display": warning_sign_display,
                "record_date": record.date.isoformat(),
                "professional": record.professional or "Não informado",
            },
            recipients=get_alert_recipients(AlertType.CRITICAL_WARNING_SIGN)
        )
        
        # Envia o email
        return send_alert_email.delay(alert.id)
        
    except Record.DoesNotExist:
        logger.error(f"Record {record_id} não encontrado")
        return f"Record {record_id} não encontrado"
    except Exception as e:
        logger.error(f"Erro ao enviar alerta crítico: {str(e)}")
        return f"Erro ao processar alerta: {str(e)}"


@shared_task
def send_consolidated_alert(record_id):
    """
    Task para enviar alerta consolidado com todos os sinais críticos de uma consulta
    """
    try:
        logger.info(f"🔍 Buscando record {record_id} para alerta consolidado")
        record = Record.objects.select_related('patient').get(id=record_id)
        patient = record.patient
        
        logger.info(f"👶 Paciente: {patient.first_name} {patient.last_name}")
        
        # Busca todos os sinais críticos presentes
        critical_signs = ClinicalWarningSign.objects.filter(
            record=record,
            is_present=True
        )
        
        logger.info(f"📊 Sinais encontrados: {critical_signs.count()}")
        
        if not critical_signs:
            logger.info("❌ Nenhum sinal crítico encontrado")
            return "Nenhum sinal crítico encontrado para consolidar"
        
        # Lista os sinais encontrados
        for sign in critical_signs:
            logger.info(f"   - {sign.type}: {sign.get_type_display()}")
        
        # Verifica se já existe alerta consolidado recente
        existing_alert = EmailAlert.objects.filter(
            record=record,
            alert_type=AlertType.CRITICAL_WARNING_SIGN,
            created_at__gte=timezone.now() - timedelta(hours=2)
        ).first()
        
        if existing_alert:
            logger.info(f"⏰ Alerta recente já existe: {existing_alert.id}")
            if existing_alert.can_resend():
                return resend_alert.delay(existing_alert.id)
            return f"Alerta consolidado já enviado recentemente: {existing_alert.id}"
        
        # Prepara a lista de sinais para o email
        signs_list = []
        for sign in critical_signs:
            signs_list.append({
                'type': sign.type,
                'display': sign.get_type_display(),
            })
        
        # Cria título e mensagem consolidados
        if len(signs_list) == 1:
            title = f"🚨 Alerta Crítico - {patient.first_name} {patient.last_name}"
            message = f"Paciente {patient.first_name} {patient.last_name} apresentou {signs_list[0]['display']} na consulta de {record.date.strftime('%d/%m/%Y')}."
        else:
            title = f"🚨 Múltiplos Alertas Críticos - {patient.first_name} {patient.last_name}"
            signs_text = ", ".join([sign['display'] for sign in signs_list])
            message = f"Paciente {patient.first_name} {patient.last_name} apresentou {len(signs_list)} sinais críticos na consulta de {record.date.strftime('%d/%m/%Y')}: {signs_text}."
        
        logger.info(f"✉️  Criando alerta: {title}")
        
        # Cria alerta consolidado
        alert = EmailAlert.objects.create(
            alert_type=AlertType.CRITICAL_WARNING_SIGN,
            patient=patient,
            record=record,
            title=title,
            message=message,
            context_data={
                "signs_count": len(signs_list),
                "signs_list": signs_list,
                "is_consolidated": True,
                "record_date": record.date.isoformat(),
                "professional": record.professional or "Não informado",
            },
            recipients=get_alert_recipients(AlertType.CRITICAL_WARNING_SIGN)
        )
        
        logger.info(f"✅ Alerta {alert.id} criado, enviando email...")
        
        # Envia o email consolidado
        return send_alert_email.delay(alert.id)
        
    except Record.DoesNotExist:
        logger.error(f"Record {record_id} não encontrado")
        return f"Record {record_id} não encontrado"
    except Exception as e:
        logger.error(f"Erro ao processar alerta consolidado: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Erro ao processar alerta consolidado: {str(e)}"


@shared_task
def send_weight_gain_alert(patient_id, record_id, status, current_gain):
    """
    Task para enviar alerta de problema no ganho de peso - VERSÃO COM DEBUG
    """
    try:
        
        patient = Patient.objects.get(id=patient_id)
        record = Record.objects.get(id=record_id) if record_id else None
        
        current_gain_float = float(current_gain)
        logger.info(f"🔍 DEBUG - current_gain_float: {current_gain_float}, type: {type(current_gain_float)}")
        
        status_display = "baixo" if status == "low" else "alto"
        
        context_data = {
            "status": status,
            "current_gain": current_gain_float,
            "status_display": status_display,
        }
        
        # Tente serializar manualmente para testar
        import json
        try:
            json_test = json.dumps(context_data)
            logger.info(f"🔍 DEBUG - JSON serialization SUCCESS: {json_test}")
        except Exception as json_error:
            logger.error(f"🔍 DEBUG - JSON serialization FAILED: {json_error}")
            # Tente identificar qual campo está causando o problema
            for key, value in context_data.items():
                try:
                    json.dumps({key: value})
                    logger.info(f"🔍 DEBUG - Field '{key}' OK")
                except Exception as field_error:
                    logger.error(f"🔍 DEBUG - Field '{key}' ERROR: {field_error}, value: {value}, type: {type(value)}")
        
        alert = EmailAlert.objects.create(
            alert_type=AlertType.WEIGHT_GAIN_ISSUE,
            patient=patient,
            record=record,
            title=f"⚠️ Ganho de Peso {status_display.title()} - {patient.first_name} {patient.last_name}",
            message=f"Paciente {patient.first_name} {patient.last_name} apresenta ganho de peso {status_display} ({current_gain_float:.1f}g/dia). O ideal é entre 15-30g/dia.",
            context_data=context_data,
            recipients=get_alert_recipients(AlertType.WEIGHT_GAIN_ISSUE)
        )
        
        return send_alert_email.delay(alert.id)
        
    except Patient.DoesNotExist:
        logger.error(f"Paciente {patient_id} não encontrado")
        return f"Paciente {patient_id} não encontrado"
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        return f"Erro ao processar alerta de peso: {str(e)}"

@shared_task
def send_missed_appointment_alert(patient_id, missed_date):
    """
    Task para enviar alerta de consulta perdida
    """
    try:
        patient = Patient.objects.get(id=patient_id)
        
        alert = EmailAlert.objects.create(
            alert_type=AlertType.MISSED_APPOINTMENT,
            patient=patient,
            title=f"📅 Consulta Perdida - {patient.first_name} {patient.last_name}",
            message=f"Paciente {patient.first_name} {patient.last_name} não compareceu à consulta agendada para {missed_date.strftime('%d/%m/%Y')}.",
            context_data={
                "missed_date": missed_date.isoformat(),
            },
            recipients=get_alert_recipients(AlertType.MISSED_APPOINTMENT)
        )
        
        return send_alert_email.delay(alert.id)
        
    except Patient.DoesNotExist:
        logger.error(f"Paciente {patient_id} não encontrado")
        return f"Paciente {patient_id} não encontrado"
    except Exception as e:
        logger.error(f"Erro ao enviar alerta de consulta: {str(e)}")
        return f"Erro ao processar alerta de consulta: {str(e)}"


@shared_task
def send_alert_email(alert_id):
    """
    Task para enviar o email do alerta 
    """
    try:
        alert = EmailAlert.objects.get(id=alert_id)
        logger.info(f"📧 Processando alerta: {alert.title}")
        
        # Define o template baseado no tipo de alerta
        if alert.alert_type == AlertType.CRITICAL_WARNING_SIGN:
            template_name = "alert_consolidated_critical"
        else:
            template_name = "alert_default"
        
        # Busca o template
        template = EmailTemplate.objects.filter(
            name=template_name,
            is_active=True
        ).first()
        
        if not template:
            template = EmailTemplate.objects.filter(
                name="alert_default",
                is_active=True
            ).first()
        
        if not template:
            alert.status = AlertStatus.CANCELLED
            alert.save()
            logger.error(f"Template de email não encontrado para alerta {alert_id}")
            return "Template de email não encontrado"
        
        # Prepara o contexto
        context = {
            'alert': alert,
            'patient': alert.patient,
            'record': alert.record,
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        context.update(alert.context_data)
        
        # Renderiza o template
        html_content = render_to_string(template.template_path, context)
        
        # Conteúdo texto simples
        text_content = f"""
        {alert.title}
        
        {alert.message}
        
        Paciente: {alert.patient.first_name} {alert.patient.last_name}
        Data: {alert.record.date if alert.record else 'N/A'}
        Tipo: {alert.get_alert_type_display()}
        
        Acesse o sistema para mais detalhes: {context['site_url']}
        
        ---
        Sistema Karu - Monitoramento Neonatal
        """
        
        # Prepara o assunto
        try:
            subject = template.subject.format(**context)
        except KeyError as e:
            logger.warning(f"Variável não encontrada no assunto: {e}, usando assunto padrão")
            subject = f"Alerta - {alert.get_alert_type_display()} - {alert.patient.first_name}"
        
        # Envia o email
        logger.info(f"✉️  Enviando email para {len(alert.recipients)} destinatários")
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=alert.recipients,
            reply_to=[settings.DEFAULT_FROM_EMAIL]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        # Atualiza o status do alerta
        alert.mark_sent()
        
        logger.info(f"✅ Alerta {alert_id} enviado com sucesso")
        return f"Alerta {alert_id} enviado com sucesso para {len(alert.recipients)} destinatários"
        
    except EmailAlert.DoesNotExist:
        logger.error(f"Alerta {alert_id} não encontrado")
        return f"Alerta {alert_id} não encontrado"
    except Exception as e:
        logger.error(f"Erro ao enviar email do alerta {alert_id}: {str(e)}")
        return f"Erro ao enviar email: {str(e)}"


@shared_task
def resend_alert(alert_id):
    """
    Task para reenviar um alerta existente
    """
    try:
        alert = EmailAlert.objects.get(id=alert_id)
        
        if alert.status == AlertStatus.RESOLVED:
            logger.info(f"Alerta {alert_id} já resolvido, não pode ser reenviado")
            return "Alerta já resolvido, não pode ser reenviado"
        
        return send_alert_email.delay(alert_id)
        
    except EmailAlert.DoesNotExist:
        logger.error(f"Alerta {alert_id} não encontrado")
        return f"Alerta {alert_id} não encontrado"


@shared_task
def check_pending_alerts():
    """
    Task periódica para verificar alertas pendentes
    """
    pending_alerts = EmailAlert.objects.filter(
        status=AlertStatus.PENDING,
        created_at__gte=timezone.now() - timedelta(hours=24)
    )
    
    results = []
    for alert in pending_alerts:
        result = send_alert_email.delay(alert.id)
        results.append(f"Alerta {alert.id} enviado")
    
    logger.info(f"Processados {pending_alerts.count()} alertas pendentes")
    return f"Processados {pending_alerts.count()} alertas pendentes"


@shared_task
def check_missed_appointments():
    """
    Task periódica para verificar consultas perdidas
    """
    from datetime import date
    
    today = date.today()
    missed_consultations = ConsultationRecord.objects.filter(
        next_appointment_date__lt=today,
        record__patient__isnull=False
    ).select_related('record__patient')
    
    results = []
    for consultation in missed_consultations:
        # Verifica se já existe alerta para esta consulta perdida
        existing_alert = EmailAlert.objects.filter(
            patient=consultation.record.patient,
            alert_type=AlertType.MISSED_APPOINTMENT,
            context_data__missed_date=consultation.next_appointment_date.isoformat(),
            created_at__gte=timezone.now() - timedelta(days=7)
        ).exists()
        
        if not existing_alert:
            result = send_missed_appointment_alert.delay(
                consultation.record.patient.id,
                consultation.next_appointment_date
            )
            results.append(f"Alerta de consulta perdida para {consultation.record.patient}")
    
    logger.info(f"Verificadas {missed_consultations.count()} consultas, {len(results)} alertas enviados")
    return f"Verificadas {missed_consultations.count()} consultas, {len(results)} alertas enviados"


@shared_task
def cleanup_old_alerts():
    """
    Task para limpar alertas antigos (mais de 30 dias)
    """
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=30)
    old_alerts = EmailAlert.objects.filter(created_at__lt=cutoff_date)
    count = old_alerts.count()
    
    old_alerts.delete()
    
    logger.info(f"Limpos {count} alertas antigos")
    return f"Limpos {count} alertas antigos"


def get_alert_recipients(alert_type):
    """
    Obtém a lista de destinatários para cada tipo de alerta
    """
    # Gestores recebem todos os alertas críticos
    managers = User.objects.filter(
        groups__name='gestores',
        is_active=True,
        email__isnull=False
    ).exclude(email='').values_list('email', flat=True)
    
    # Para responsáveis (futura implementação)
    recipients = list(managers)
    
    # Adiciona email padrão se configurado
    default_email = getattr(settings, 'DEFAULT_ALERT_EMAIL', None)
    if default_email and default_email not in recipients:
        recipients.append(default_email)
    
    # Remove emails vazios
    recipients = [email for email in recipients if email and email.strip()]
    
    return recipients

@shared_task
def check_weight_gain_issues(record_id):
    """
    Verifica problemas de ganho de peso - VERSÃO COM TRATAMENTO DE ERRO
    """
    try:
        logger.info(f"⚖️ VERIFICAÇÃO DE PESO PARA RECORD {record_id}")
        
        # ✅ VERIFICAÇÃO ROBUSTA: Tenta buscar o record com tratamento de erro
        try:
            record = Record.objects.select_related('patient', 'consultation_details').get(id=record_id)
        except Record.DoesNotExist:
            logger.error(f"❌ RECORD NÃO ENCONTRADO: {record_id} - Task será ignorada")
            return f"Record {record_id} não encontrado - task cancelada"
        
        # Só processa consultas
        if record.record_type != 'consultation':
            logger.warning("❌ Não é uma consulta")
            return "Não é uma consulta"
            
        if not hasattr(record, 'consultation_details'):
            logger.warning("❌ Consulta sem detalhes")
            return "Consulta sem detalhes"
        
        consultation = record.consultation_details
        current_weight = consultation.weight
        
        if not current_weight:
            logger.warning("❌ Peso atual não informado")
            return "Peso atual não informado"
        
        logger.info(f"📊 Peso atual na consulta: {current_weight}g")
        
        # ✅ LÓGICA SIMPLIFICADA: Compara com peso do nascimento
        birth_weight = record.patient.birth_weight
        
        if not birth_weight:
            logger.warning("❌ Peso ao nascer não disponível")
            return "Peso ao nascer não disponível"
        
        logger.info(f"🤰 Peso ao nascer: {birth_weight}g")
        
        # Calcula dias desde o nascimento
        days_since_birth = (record.date - record.patient.date_of_birth).days
        
        if days_since_birth <= 0:
            logger.warning("❌ Data da consulta inválida")
            return "Data da consulta inválida"
        
        logger.info(f"📅 Dias desde nascimento: {days_since_birth}")
        
        # Calcula ganho diário desde o nascimento
        weight_gain = float(current_weight) - float(birth_weight)
        daily_gain = weight_gain / days_since_birth
        
        logger.info(f"📈 Ganho desde nascimento: {daily_gain:.1f}g/dia")
        
        # Verifica se está fora da faixa ideal (15-30g/dia)
        if daily_gain < 15:
            status = "low"
            logger.warning(f"⚠️ GANHO BAIXO DETECTADO: {daily_gain:.1f}g/dia")
        elif daily_gain > 30:
            status = "high" 
            logger.warning(f"⚠️ GANHO ALTO DETECTADO: {daily_gain:.1f}g/dia")
        else:
            logger.info(f"✅ Ganho adequado: {daily_gain:.1f}g/dia")
            return f"Ganho de peso adequado: {daily_gain:.1f}g/dia"
        
        # Verifica se já existe alerta recente
        existing_alert = EmailAlert.objects.filter(
            patient=record.patient,
            alert_type=AlertType.WEIGHT_GAIN_ISSUE,
            status__in=[AlertStatus.PENDING, AlertStatus.SENT],
            created_at__gte=timezone.now() - timedelta(days=7)
        ).exists()
        
        if not existing_alert:
            logger.info(f"🚨 ENVIANDO ALERTA DE PESO {status}")
            return send_weight_gain_alert.delay(
                record.patient.id,
                record.id,
                status,
                round(daily_gain, 1)
            )
        else:
            logger.info("⏰ Alerta de peso já enviado recentemente")
            return "Alerta já enviado"
            
    except Exception as e:
        logger.error(f"❌ Erro crítico: {str(e)}")
        return f"Erro crítico: {str(e)}"