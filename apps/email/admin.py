from auditlog.registry import auditlog
from django.contrib import admin

from .models import EmailAlert


@admin.register(EmailAlert)
class EmailAlertAdmin(admin.ModelAdmin):
    list_display = ["patient", "alert_type", "status", "scheduled_for", "sent_at"]
    list_filter = ["alert_type", "status", "scheduled_for"]
    search_fields = ["patient__first_name", "patient__last_name", "recipient_email"]
    readonly_fields = ["sent_at", "error_message", "created_at", "updated_at"]
    date_hierarchy = "scheduled_for"


# Registrar apenas para ações CREATE e DELETE, ignorar UPDATE
auditlog.register(
    EmailAlert,
    include_fields=["title", "alert_type", "patient", "recipient_email"],
    exclude_fields=["status", "sent_at", "error_message", "updated_at"],
)
