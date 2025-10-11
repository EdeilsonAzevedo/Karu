import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from .models import AlertStatus, EmailAlert

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_email_alert(self, alert_id):
    """
    Task para enviar alerta por email com retry automático
    """
    try:
        alert = EmailAlert.objects.get(id=alert_id)

        if alert.status == AlertStatus.SENT:
            logger.info(f"Alerta {alert_id} já foi enviado anteriormente")
            return True

        # Prepara o email
        subject = alert.title
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = alert.recipient_emails

        # Renderiza template HTML baseado no tipo de alerta E se é agrupado
        context = {
            "alert": alert,
            "patient": alert.patient,
            "warning_sign": alert.warning_sign,
            "site_url": "http://localhost:8000",
        }

        # DECIDE QUAL TEMPLATE USAR
        if alert.alert_type == "critical_warning":
            # Verifica se é um alerta agrupado (múltiplos sinais)
            if (
                alert.context_data
                and "warning_count" in alert.context_data
                and alert.context_data["warning_count"] > 1
            ):
                html_message = render_to_string("emails/aggregated_alert.html", context)
            else:
                html_message = render_to_string("emails/critical_alert.html", context)
        else:
            html_message = render_to_string("emails/alert_template.html", context)

        # Envia email
        email = EmailMultiAlternatives(
            subject=subject, body=alert.message, from_email=from_email, to=recipient_list
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)

        # Atualiza status
        alert.status = AlertStatus.SENT
        alert.sent_at = timezone.now()
        alert.save()

        logger.info(f"Alerta {alert_id} enviado com sucesso para {recipient_list}")
        return True

    except Exception as exc:
        logger.error(f"Erro ao enviar alerta {alert_id}: {str(exc)}")

        # Atualiza status de falha
        try:
            alert = EmailAlert.objects.get(id=alert_id)
            alert.status = AlertStatus.FAILED
            alert.error_message = str(exc)
            alert.save()
        except EmailAlert.DoesNotExist:
            pass

        # Re-tenta após 5 minutos
        raise self.retry(exc=exc, countdown=300)


@shared_task
def check_critical_warning_signs():
    """
    Task periódica DESATIVADA - usando apenas signals agora
    """
    logger.info("❌ TASK PERIÓDICA DESATIVADA - usando signals para alertas em tempo real")
    return "Task periódica desativada"


@shared_task
def create_consultation_alert(record_id):
    """
    Cria UM alerta para TODOS os sinais críticos de uma consulta
    """
    try:
        from apps.patients.models import ClinicalWarningSign, Record

        logger.info(f"🎯 CRIANDO ALERTA AGREGADO para consulta {record_id}")

        record = Record.objects.get(id=record_id)
        patient = record.patient

        # Busca TODOS os sinais críticos desta consulta
        critical_signs = ClinicalWarningSign.objects.filter(record=record, is_present=True)

        if not critical_signs.exists():
            logger.info(f"⏭️  Nenhum sinal crítico na consulta {record_id}")
            return "Nenhum sinal crítico nesta consulta"

        # Verifica se já existe alerta recente para esta CONSULTA
        time_limit = timezone.now() - timedelta(minutes=60)
        recent_alert_exists = EmailAlert.objects.filter(
            patient=patient,
            context_data__has_key="record_id",
            context_data__record_id=str(record_id),
            created_at__gte=time_limit,
        ).exists()

        if recent_alert_exists:
            logger.info(f"⏭️  Alerta recente já existe para consulta {record_id}")
            return "Alerta recente já existe"

        # Prepara lista de sinais para o alerta (em ordem correta)
        warning_types = []
        for sign in critical_signs.order_by("created_at"):  # Ordena pela criação
            warning_types.append(sign.get_type_display())

        # CRIA APENAS UM ALERTA para todos os sinais
        alert = EmailAlert.objects.create(
            alert_type="critical_warning",
            patient=patient,
            warning_sign=critical_signs.first(),
            title=f"🚨 {len(critical_signs)} Sinais Críticos Detectados - {patient.first_name}",
            message=(
                f"Paciente: {patient.first_name} {patient.last_name or ''}\n"
                f"Sinais detectados: {', '.join(warning_types)}\n"
                f"Total de sinais: {len(critical_signs)}\n"
                f"Data da consulta: {record.date}\n"
                f"Local: {record.location or 'Não informado'}\n"
                f"Profissional: {record.professional or 'Não informado'}\n\n"
                f"Este é um alerta automático do sistema Karu."
            ),
            recipient_emails=settings.ALERT_EMAIL_RECIPIENTS,
            context_data={
                "record_id": str(record_id),
                "warning_count": len(critical_signs),
                "warning_types": warning_types,
                "consultation_date": record.date.isoformat(),
                "professional": record.professional,
            },
        )

        logger.info(f"📦 ALERTA AGREGADO SALVO: {alert.id} com {len(critical_signs)} sinais")

        # Dispara task para enviar email
        send_email_alert.delay(alert.id)
        return f"Alerta {alert.id} criado com {len(critical_signs)} sinais"

    except Exception as exc:
        logger.error(f"❌ ERRO AO CRIAR ALERTA AGREGADO: {str(exc)}")
        import traceback

        logger.error(traceback.format_exc())
        return f"Erro: {str(exc)}"
