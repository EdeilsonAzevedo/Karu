from auditlog.registry import auditlog
from django.contrib import admin

from .models import AlertTemplate, EmailAlert


@admin.register(EmailAlert)
class EmailAlertAdmin(admin.ModelAdmin):
    list_display = ["title", "patient", "alert_type", "status", "created_at", "sent_at"]
    list_filter = ["alert_type", "status", "created_at"]
    search_fields = ["title", "patient__first_name", "patient__last_name"]
    readonly_fields = ["created_at", "updated_at"]
    actions = ["resend_alerts"]

    def resend_alerts(self, request, queryset):
        from .tasks import send_email_alert

        for alert in queryset.filter(status__in=["failed", "pending"]):
            send_email_alert.delay(alert.id)
        self.message_user(request, f"{queryset.count()} alertas enviados para reenvio.")

    resend_alerts.short_description = "Reenviar alertas selecionados"


@admin.register(AlertTemplate)
class AlertTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "alert_type", "is_active"]
    list_filter = ["alert_type", "is_active"]


# Registra no auditlog
auditlog.register(EmailAlert)
auditlog.register(AlertTemplate)
