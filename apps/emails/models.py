from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel
from apps.patients.models import ClinicalWarningSign, Patient


class AlertType(models.TextChoices):
    CRITICAL_WARNING_SIGN = "critical_warning", _("Sinal de Alerta Crítico")
    WEIGHT_ALERT = "weight_alert", _("Alerta de Peso")
    FOLLOWUP_MISSED = "followup_missed", _("Consulta Perdida")
    SYSTEM_ALERT = "system_alert", _("Alerta do Sistema")


class AlertStatus(models.TextChoices):
    PENDING = "pending", _("Pendente")
    SENT = "sent", _("Enviado")
    FAILED = "failed", _("Falhou")
    ACKNOWLEDGED = "acknowledged", _("Reconhecido")


class EmailAlert(BaseModel):
    alert_type = models.CharField(max_length=20, choices=AlertType.choices)
    status = models.CharField(
        max_length=15, choices=AlertStatus.choices, default=AlertStatus.PENDING
    )

    # Relacionamentos
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, null=True, blank=True, related_name="email_alerts"
    )
    warning_sign = models.ForeignKey(
        ClinicalWarningSign,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="email_alerts",
    )

    # Dados do alerta
    title = models.CharField(max_length=200)
    message = models.TextField()
    recipient_emails = models.JSONField(default=list)  # Lista de emails
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)

    # Metadados
    context_data = models.JSONField(default=dict)  # Dados contextuais do alerta

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["alert_type", "patient"]),
        ]

    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.patient} - {self.status}"


class AlertTemplate(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    alert_type = models.CharField(max_length=20, choices=AlertType.choices)
    subject_template = models.CharField(max_length=200)
    body_template = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
