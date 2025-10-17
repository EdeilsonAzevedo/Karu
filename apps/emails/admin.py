from django.contrib import admin
from .models import EmailAlert, EmailTemplate


@admin.register(EmailAlert)
class EmailAlertAdmin(admin.ModelAdmin):
    list_display = [
        'title_truncated', 
        'patient_link',
        'alert_type_display',
        'status_display', 
        'sent_count',
        'created_at',
    ]
    
    list_filter = [
        'alert_type', 
        'status', 
        'created_at',
    ]
    
    search_fields = [
        'title', 
        'message',
        'patient__first_name',
        'patient__last_name',
    ]
    
    readonly_fields = [
        'created_at', 
        'updated_at', 
        'last_sent_at',
        'acknowledged_at',
        'resolved_at',
        'sent_count'
    ]
    
    fieldsets = (
        ('Informações do Alerta', {
            'fields': (
                'alert_type', 
                'status', 
                'title', 
                'message'
            )
        }),
        ('Relacionamentos', {
            'fields': (
                'patient', 
                'record',
                'triggered_by',
                'acknowledged_by'
            )
        }),
        ('Configurações de Envio', {
            'fields': (
                'recipients',
                'sent_count',
                'last_sent_at'
            )
        }),
        ('Dados de Contexto', {
            'fields': ('context_data',),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': (
                'created_at', 
                'updated_at',
                'acknowledged_at',
                'resolved_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def title_truncated(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_truncated.short_description = 'Título'
    
    def patient_link(self, obj):
        if obj.patient:
            from django.utils.html import format_html
            from django.urls import reverse
            url = reverse('admin:patients_patient_change', args=[obj.patient.id])
            return format_html('<a href="{}">{}</a>', url, f"{obj.patient.first_name} {obj.patient.last_name}")
        return "-"
    patient_link.short_description = 'Paciente'
    
    def alert_type_display(self, obj):
        return obj.get_alert_type_display()
    alert_type_display.short_description = 'Tipo'
    
    def status_display(self, obj):
        return obj.get_status_display()
    status_display.short_description = 'Status'


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    list_editable = ['is_active']
    search_fields = ['name', 'subject']
    readonly_fields = ['created_at', 'updated_at']