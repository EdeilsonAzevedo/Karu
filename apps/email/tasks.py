import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from apps.patients.models import ConsultationRecord

from .models import EmailAlert

logger = logging.getLogger(__name__)

# PARÂMETROS CONFIGURÁVEIS PARA ALERTAS DE PESO
MIN_WEIGHT_LOSS_GRAMS = 30  # Mínimo 30g de perda para considerar significativa
MIN_PERCENTAGE_LOSS = 1.0  # 1.0%
CONSECUTIVE_LOSSES_REQUIRED = 2  # Número mínimo de consultas com perda
MIN_DAYS_BETWEEN_MEASUREMENTS = 2  # Mínimo de dias entre medições para considerar válido


def get_alert_recipients(alert_type):
    """Sempre envia para o email padrão"""
    return [settings.DEFAULT_ALERT_EMAIL]


@shared_task
def send_email_alert(alert_id):
    """
    Task para enviar um alerta por email
    """
    try:
        alert = EmailAlert.objects.get(id=alert_id, status=EmailAlert.AlertStatus.AGUARDANDO_ENVIO)

        # Renderizar template HTML do email
        html_message = render_to_string(
            "email/alert_template.html",
            {
                "alert": alert,
                "patient": alert.patient,
                "site_url": settings.SITE_URL,
            },
        )

        # Versão texto simples SUPER SIMPLES
        text_message = f"""
{alert.title}

Foi detectada uma situação que requer atenção.

Paciente: {alert.patient.first_name} {alert.patient.last_name or ""}
Nascimento: {alert.patient.date_of_birth.strftime("%d/%m/%Y")}

Acesse o prontuário completo para detalhes:
{settings.SITE_URL}/patients/{alert.patient.pk}/

---
Sistema Karu
        """.strip()

        # Enviar email
        send_mail(
            subject=alert.title,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[alert.recipient_email],
            html_message=html_message,
            fail_silently=False,
        )

        # Atualizar status
        alert.status = EmailAlert.AlertStatus.ENVIADO
        alert.sent_at = timezone.now()
        alert.save()

        logger.info(f"✅ Alerta enviado com sucesso: {alert.id} para {alert.recipient_email}")

    except EmailAlert.DoesNotExist:
        logger.error(f"❌ Alerta não encontrado: {alert_id}")
    except Exception as e:
        logger.error(f"❌ Erro ao enviar alerta {alert_id}: {str(e)}")
        try:
            alert = EmailAlert.objects.get(id=alert_id)
            alert.status = EmailAlert.AlertStatus.FALHA_ENVIO
            alert.error_message = str(e)
            alert.save()
        except EmailAlert.DoesNotExist:
            pass


def calculate_weight_loss_percentage(current_weight, previous_weight):
    """Calcula a porcentagem de perda de peso"""
    if not previous_weight or not current_weight:
        return 0
    return ((previous_weight - current_weight) / previous_weight) * 100


def is_significant_weight_loss(current_weight, previous_weight):
    """
    Verifica se a perda de peso é significativa baseada nos critérios:
    - Perda mínima de 30g E
    - Perda percentual mínima de 1.0%
    """
    if not previous_weight or not current_weight:
        return False

    weight_loss_grams = previous_weight - current_weight
    percentage_loss = calculate_weight_loss_percentage(current_weight, previous_weight)

    return weight_loss_grams >= MIN_WEIGHT_LOSS_GRAMS and percentage_loss >= MIN_PERCENTAGE_LOSS


@shared_task
def check_weight_loss_alerts():
    """
    Task periódica para verificar perda de peso com critérios realistas
    """
    from apps.patients.models import Patient

    if not getattr(settings, "ALERT_SETTINGS", {}).get("weight_loss", {}).get("enabled", True):
        return

    logger.info("🔍 Verificando alertas de perda de peso com critérios realistas...")

    try:
        active_patients = Patient.objects.filter(is_active=True)
        alerts_created = 0

        for patient in active_patients:
            # Buscar todas as consultas com peso válido, ordenadas por data
            consultations = (
                ConsultationRecord.objects.filter(
                    record__patient=patient, weight__isnull=False, record__date__isnull=False
                )
                .select_related("record")
                .order_by("record__date")
            )

            if len(consultations) < 2:
                continue

            # Analisar sequência de pesos
            weight_loss_events = []
            valid_measurements = []

            # Filtrar medições válidas (com pelo menos MIN_DAYS_BETWEEN_MEASUREMENTS de diferença)
            for i in range(len(consultations)):
                current = consultations[i]
                if not valid_measurements:
                    valid_measurements.append(current)
                    continue

                last_valid = valid_measurements[-1]
                days_between = (current.record.date - last_valid.record.date).days

                if days_between >= MIN_DAYS_BETWEEN_MEASUREMENTS:
                    valid_measurements.append(current)

            # Verificar perdas significativas entre medições válidas
            for i in range(1, len(valid_measurements)):
                current = valid_measurements[i]
                previous = valid_measurements[i - 1]

                if is_significant_weight_loss(float(current.weight), float(previous.weight)):
                    weight_loss_events.append(
                        {
                            "current": current,
                            "previous": previous,
                            "loss_grams": float(previous.weight) - float(current.weight),
                            "loss_percentage": calculate_weight_loss_percentage(
                                float(current.weight), float(previous.weight)
                            ),
                            "days_between": (current.record.date - previous.record.date).days,
                        }
                    )

            # Criar alerta se houver perdas suficientes
            if len(weight_loss_events) >= CONSECUTIVE_LOSSES_REQUIRED:
                if create_weight_loss_alert(patient, weight_loss_events):
                    alerts_created += 1

        logger.info(f"📊 Análise concluída: {alerts_created} alertas criados")

    except Exception as e:
        logger.error(f"❌ Erro na verificação de perda de peso: {str(e)}")


def create_weight_loss_alert(patient, weight_loss_events):
    """
    Cria alerta de perda de peso para um paciente
    """
    # Verificar se já existe alerta pendente recente (evitar spam)
    recent_alert = EmailAlert.objects.filter(
        patient=patient,
        alert_type=EmailAlert.AlertType.WEIGHT_LOSS,
        status__in=[EmailAlert.AlertStatus.AGUARDANDO_ENVIO, EmailAlert.AlertStatus.ENVIADO],
        scheduled_for__gte=timezone.now() - timedelta(days=3),
    ).exists()

    if recent_alert:
        return False

    recipients = get_alert_recipients("weight_loss")

    # Mensagem SUPER SIMPLES
    for recipient_email in recipients:
        alert = EmailAlert.objects.create(
            patient=patient,
            alert_type=EmailAlert.AlertType.WEIGHT_LOSS,
            title=f"Perda de Peso - {patient.first_name} {patient.last_name or ''}",
            message="Paciente apresentou perda de peso significativa em múltiplas medições. Acesse o prontuário para detalhes completos.",
            scheduled_for=timezone.now(),
            recipient_email=recipient_email,
            status=EmailAlert.AlertStatus.AGUARDANDO_ENVIO,
        )

        # Agendar envio imediato
        send_email_alert.delay(alert.id)
        logger.info(f"📨 Alerta de perda de peso criado para {patient}")

    return True


@shared_task
def check_missed_appointments():
    """
    Task periódica para verificar ausência de consultas
    Considera next_appointment_date E return_plan de forma mais inteligente
    """

    logger.info("🔍 Verificando consultas ausentes...")

    try:
        today = timezone.now().date()
        alerts_created = 0

        # 1. Consultas com next_appointment_date em atraso
        missed_by_date = ConsultationRecord.objects.filter(
            next_appointment_date__lt=today,
            next_appointment_date__isnull=False,
            record__patient__is_active=True,
        ).select_related("record__patient")

        # 2. Consultas com return_plan que indicam retorno em atraso
        # Analisa o texto do return_plan para extrair prazos
        all_consultations_with_plan = ConsultationRecord.objects.filter(
            return_plan__isnull=False,
            return_plan__gt="",  # Não vazio
            record__patient__is_active=True,
        ).select_related("record__patient")

        missed_by_plan = []
        for consultation in all_consultations_with_plan:
            if is_return_plan_overdue(consultation):
                missed_by_plan.append(consultation)

        # 3. Evitar duplicação - remover consultas que já estão em missed_by_date
        missed_by_plan = [c for c in missed_by_plan if c not in missed_by_date]

        # Processar consultas com data agendada em atraso
        for consultation in missed_by_date:
            days_overdue = (today - consultation.next_appointment_date).days
            if days_overdue >= 1:  # Pelo menos 1 dia de atraso
                if create_missed_appointment_alert(consultation, "data_agendada", days_overdue):
                    alerts_created += 1

        # Processar consultas com plano de retorno em atraso
        for consultation in missed_by_plan:
            if create_missed_appointment_alert(consultation, "plano_retorno"):
                alerts_created += 1

        logger.info(
            f"✅ Consultas atrasadas: {len(missed_by_date)} por data + {len(missed_by_plan)} por plano = {alerts_created} alertas"
        )

    except Exception as e:
        logger.error(f"❌ Erro na verificação de consultas ausentes: {str(e)}")


def is_return_plan_overdue(consultation):
    """
    Analisa o return_plan para determinar se está em atraso
    """
    try:
        return_plan_text = consultation.return_plan.lower().strip()
        consultation_date = consultation.record.date
        today = timezone.now().date()

        days_since_consultation = (today - consultation_date).days

        # Lógica para analisar diferentes padrões de return_plan
        if any(term in return_plan_text for term in ["semana", "week"]):
            # Retorno em 1 semana = 7 dias
            expected_days = 7
        elif any(term in return_plan_text for term in ["15 dias", "quinze dias", "2 semanas"]):
            expected_days = 15
        elif any(term in return_plan_text for term in ["1 mês", "um mês", "30 dias"]):
            expected_days = 30
        elif any(term in return_plan_text for term in ["2 meses", "dois meses", "60 dias"]):
            expected_days = 60
        elif any(term in return_plan_text for term in ["3 meses", "três meses", "90 dias"]):
            expected_days = 90
        else:
            # Padrão genérico - procurar números no texto
            import re

            numbers = re.findall(r"\d+", return_plan_text)
            if numbers:
                # Assume que o primeiro número encontrado é o prazo em dias
                expected_days = int(numbers[0])
            else:
                # Se não conseguir extrair um prazo, usa 30 dias como padrão
                expected_days = 30

        # Considera atraso se passou do prazo esperado + 7 dias de tolerância
        return days_since_consultation > (expected_days + 7)

    except Exception as e:
        logger.error(f"Erro ao analisar return_plan: {str(e)}")
        return False


def create_missed_appointment_alert(consultation, motivo, days_overdue=None):
    """
    Cria alerta de consulta ausente
    """
    patient = consultation.record.patient

    # Verificar se já existe alerta pendente recente (evitar spam)
    recent_alert = EmailAlert.objects.filter(
        patient=patient,
        alert_type=EmailAlert.AlertType.MISSED_APPOINTMENT,
        status__in=[EmailAlert.AlertStatus.AGUARDANDO_ENVIO, EmailAlert.AlertStatus.ENVIADO],
        scheduled_for__gte=timezone.now() - timedelta(days=7),
    ).exists()

    if recent_alert:
        return False

    recipients = get_alert_recipients("missed_appointment")

    # Mensagem baseada no motivo
    if motivo == "data_agendada":
        mensagem = f"Consulta agendada para {consultation.next_appointment_date.strftime('%d/%m/%Y')} não realizada ({days_overdue} dias de atraso)."
        title_suffix = "Data Agendada"
    else:
        dias_desde_consulta = (timezone.now().date() - consultation.record.date).days
        mensagem = f"Plano de retorno não cumprido: '{consultation.return_plan}'. Última consulta há {dias_desde_consulta} dias."
        title_suffix = "Plano de Retorno"

    for recipient_email in recipients:
        alert = EmailAlert.objects.create(
            patient=patient,
            alert_type=EmailAlert.AlertType.MISSED_APPOINTMENT,
            title=f"Consulta Atrasada ({title_suffix}) - {patient.first_name} {patient.last_name or ''}",
            message=mensagem,
            scheduled_for=timezone.now(),
            recipient_email=recipient_email,
            status=EmailAlert.AlertStatus.AGUARDANDO_ENVIO,
        )

        send_email_alert.delay(alert.id)
        logger.info(f"📨 Alerta de consulta atrasada criado para {patient} - Motivo: {motivo}")

    return True
