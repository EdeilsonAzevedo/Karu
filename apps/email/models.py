from django.db import models

from apps.patients.models import Patient


class EmailAlert(models.Model):
    class AlertType(models.TextChoices):
        WEIGHT_LOSS = "weight_loss", "Perda de Peso"
        MISSED_APPOINTMENT = "missed_appointment", "Ausência de Consulta"

    class AlertStatus(models.TextChoices):
        AGUARDANDO_ENVIO = "aguardando_envio", "Aguardando Envio"
        ENVIADO = "enviado", "Enviado"
        FALHA_ENVIO = "falha_envio", "Falha no Envio"
        CANCELADO = "cancelado", "Cancelado"

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="email_alerts")
    alert_type = models.CharField(max_length=30, choices=AlertType.choices)
    status = models.CharField(
        max_length=20, choices=AlertStatus.choices, default=AlertStatus.AGUARDANDO_ENVIO
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    scheduled_for = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    recipient_email = models.EmailField()
    error_message = models.TextField(blank=True, null=True)

    # Campos de auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # REMOVER O STATUS da representação string para não aparecer nos logs
        return f"{self.get_alert_type_display()} - {self.patient}"

    class Meta:
        verbose_name = "Alerta de Email"
        verbose_name_plural = "Alertas de Email"
        ordering = ["-created_at"]
