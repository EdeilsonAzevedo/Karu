from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.patients.models import Patient, Record

User = get_user_model()


class AlertType(models.TextChoices):
    CRITICAL_WARNING_SIGN = "critical_warning", _("Sinal de Alerta Crítico")
    WEIGHT_GAIN_ISSUE = "weight_gain", _("Problema no Ganho de Peso")
    MISSED_APPOINTMENT = "missed_appointment", _("Consulta Perdida")
    SYSTEM_ALERT = "system", _("Alerta do Sistema")


class AlertStatus(models.TextChoices):
    PENDING = "pending", _("Pendente")
    SENT = "sent", _("Enviado")
    ACKNOWLEDGED = "acknowledged", _("Reconhecido")
    RESOLVED = "resolved", _("Resolvido")
    CANCELLED = "cancelled", _("Cancelado")


class EmailAlert(models.Model):
    alert_type = models.CharField(
        _("Tipo de Alerta"), max_length=20, choices=AlertType.choices
    )
    status = models.CharField(
        _("Status"), max_length=15, choices=AlertStatus.choices, default=AlertStatus.PENDING
    )
    
    # Relacionamentos
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="email_alerts", null=True, blank=True
    )
    record = models.ForeignKey(
        Record, on_delete=models.CASCADE, related_name="email_alerts", null=True, blank=True
    )
    triggered_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="triggered_alerts"
    )
    acknowledged_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="acknowledged_alerts"
    )
    
    # Dados do alerta
    title = models.CharField(_("Título"), max_length=200)
    message = models.TextField(_("Mensagem"))
    context_data = models.JSONField(_("Dados de Contexto"), default=dict, blank=True)
    
    # Controle de envio
    recipients = models.JSONField(_("Destinatários"), default=list)
    sent_count = models.PositiveIntegerField(_("Quantidade de Envios"), default=0)
    last_sent_at = models.DateTimeField(_("Último Envio"), null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_("Criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Atualizado em"), auto_now=True)
    acknowledged_at = models.DateTimeField(_("Reconhecido em"), null=True, blank=True)
    resolved_at = models.DateTimeField(_("Resolvido em"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Alerta de Email")
        verbose_name_plural = _("Alertas de Email")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "alert_type"]),
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["created_at"]),
        ]
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.title} - {self.get_status_display()}"
    
    def mark_sent(self):
        """Marca o alerta como enviado"""
        from django.utils import timezone
        
        self.status = AlertStatus.SENT
        self.sent_count += 1
        self.last_sent_at = timezone.now()
        self.save(update_fields=["status", "sent_count", "last_sent_at", "updated_at"])
    
    def acknowledge(self, user):
        """Marca o alerta como reconhecido por um usuário"""
        from django.utils import timezone
        
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save(
            update_fields=[
                "status", "acknowledged_by", "acknowledged_at", "updated_at"
            ]
        )
    
    def resolve(self):
        """Marca o alerta como resolvido"""
        from django.utils import timezone
        
        self.status = AlertStatus.RESOLVED
        self.resolved_at = timezone.now()
        self.save(update_fields=["status", "resolved_at", "updated_at"])
    
    def can_resend(self):
        """Verifica se o alerta pode ser reenviado"""
        from datetime import timedelta

        from django.utils import timezone
        
        if self.last_sent_at:
            # Permite reenvio a cada 1 hora no máximo
            return timezone.now() - self.last_sent_at > timedelta(hours=1)
        return True
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('emails:alert_detail', kwargs={'pk': self.pk})


class EmailTemplate(models.Model):
    name = models.CharField(_("Nome"), max_length=100, unique=True)
    subject = models.CharField(_("Assunto"), max_length=200)
    template_path = models.CharField(_("Caminho do Template"), max_length=200)
    is_active = models.BooleanField(_("Ativo"), default=True)
    context_variables = models.JSONField(
        _("Variáveis de Contexto"), 
        default=list,
        blank=True,    # ADICIONE ESTA LINHA
        null=True,     # ADICIONE ESTA LINHA
        help_text=_("Lista de variáveis disponíveis no template")
    )
    
    created_at = models.DateTimeField(_("Criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Atualizado em"), auto_now=True)
    
    class Meta:
        verbose_name = _("Template de Email")
        verbose_name_plural = _("Templates de Email")
    
    def __str__(self):
        return self.name