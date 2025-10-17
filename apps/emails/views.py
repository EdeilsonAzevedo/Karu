from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, TemplateView, UpdateView

from apps.emails.models import AlertStatus, AlertType, EmailAlert


class AlertListView(LoginRequiredMixin, ListView):
    model = EmailAlert
    template_name = "emails/alert_list.html"
    context_object_name = "alerts"
    paginate_by = 20
    
    def get_queryset(self):
        queryset = EmailAlert.objects.select_related('patient', 'record', 'triggered_by', 'acknowledged_by')
        
        # Filtros
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        alert_type = self.request.GET.get('type')
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        patient_name = self.request.GET.get('patient')
        if patient_name:
            queryset = queryset.filter(
                Q(patient__first_name__icontains=patient_name) |
                Q(patient__last_name__icontains=patient_name)
            )
        
        # Ordenação
        sort = self.request.GET.get('sort', '-created_at')
        if sort in ['created_at', '-created_at', 'status', '-status']:
            queryset = queryset.order_by(sort)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas para o dashboard
        context['stats'] = {
            'total': EmailAlert.objects.count(),
            'pending': EmailAlert.objects.filter(status=AlertStatus.PENDING).count(),
            'sent': EmailAlert.objects.filter(status=AlertStatus.SENT).count(),
            'acknowledged': EmailAlert.objects.filter(status=AlertStatus.ACKNOWLEDGED).count(),
            'resolved': EmailAlert.objects.filter(status=AlertStatus.RESOLVED).count(),
        }
        
        context['status_choices'] = AlertStatus.choices
        context['type_choices'] = AlertType.choices
        context['current_filters'] = {
            'status': self.request.GET.get('status', ''),
            'type': self.request.GET.get('type', ''),
            'patient': self.request.GET.get('patient', ''),
            'sort': self.request.GET.get('sort', '-created_at'),
        }
        
        return context


class AlertDetailView(LoginRequiredMixin, DetailView):
    model = EmailAlert
    template_name = "emails/alert_detail.html"
    context_object_name = "alert"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Histórico de alertas similares
        similar_alerts = EmailAlert.objects.filter(
            patient=self.object.patient,
            alert_type=self.object.alert_type
        ).exclude(id=self.object.id).order_by('-created_at')[:5]
        
        context['similar_alerts'] = similar_alerts
        return context


class AcknowledgeAlertView(LoginRequiredMixin, UpdateView):
    model = EmailAlert
    fields = []
    template_name = "emails/acknowledge_alert.html"
    
    def get_success_url(self):
        return self.object.get_absolute_url()
    
    def form_valid(self, form):
        alert = self.get_object()
        alert.acknowledge(self.request.user)
        
        messages.success(
            self.request, 
            f"Alerta '{alert.title}' reconhecido com sucesso."
        )
        
        # Log no auditlog
        from auditlog.models import LogEntry
        LogEntry.objects.log_action(
            user_id=self.request.user.id,
            content_type_id=alert._meta.model_id,
            object_id=alert.id,
            object_repr=f"Alerta reconhecido: {alert.title}",
            action_flag=LogEntry.Action.UPDATE
        )
        
        return super().form_valid(form)


class ResolveAlertView(LoginRequiredMixin, UpdateView):
    model = EmailAlert
    fields = []
    template_name = "emails/resolve_alert.html"
    
    def get_success_url(self):
        return self.object.get_absolute_url()
    
    def form_valid(self, form):
        alert = self.get_object()
        alert.resolve()
        
        messages.success(
            self.request, 
            f"Alerta '{alert.title}' marcado como resolvido."
        )
        
        # Log no auditlog
        from auditlog.models import LogEntry
        LogEntry.objects.log_action(
            user_id=self.request.user.id,
            content_type_id=alert._meta.model_id,
            object_id=alert.id,
            object_repr=f"Alerta resolvido: {alert.title}",
            action_flag=LogEntry.Action.UPDATE
        )
        
        return super().form_valid(form)


class ResendAlertView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = EmailAlert
    fields = []
    template_name = "emails/resend_alert.html"
    
    def get_success_url(self):
        return self.object.get_absolute_url()
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name='gestores').exists()
    
    def form_valid(self, form):
        alert = self.get_object()
        
        from apps.emails.tasks import resend_alert
        resend_alert.delay(alert.id)
        
        messages.info(
            self.request, 
            f"Alerta '{alert.title}' será reenviado em breve."
        )
        
        return super().form_valid(form)


class AlertDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "emails/alert_dashboard.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas gerais
        alerts = EmailAlert.objects.all()
        
        # Alertas por status
        status_stats = alerts.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Alertas por tipo
        type_stats = alerts.values('alert_type').annotate(
            count=Count('id')
        ).order_by('alert_type')
        
        # Alertas recentes (últimos 7 dias)
        recent_alerts = alerts.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        )
        
        # Alertas críticos não resolvidos
        critical_unresolved = alerts.filter(
            alert_type=AlertType.CRITICAL_WARNING_SIGN,
            status__in=[AlertStatus.PENDING, AlertStatus.SENT, AlertStatus.ACKNOWLEDGED]
        ).order_by('-created_at')[:10]
        
        context.update({
            'status_stats': status_stats,
            'type_stats': type_stats,
            'recent_alerts': recent_alerts[:10],
            'critical_unresolved': critical_unresolved,
            'total_alerts': alerts.count(),
            'unresolved_alerts': alerts.exclude(status=AlertStatus.RESOLVED).count(),
            'critical_alerts': alerts.filter(alert_type=AlertType.CRITICAL_WARNING_SIGN).count(),
        })
        
        return context


@require_POST
def quick_acknowledge_alert(request, pk):
    """View para reconhecimento rápido de alerta"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    alert = get_object_or_404(EmailAlert, pk=pk)
    alert.acknowledge(request.user)
    
    messages.success(request, f"Alerta reconhecido: {alert.title}")
    
    if request.META.get('HTTP_REFERER'):
        return redirect(request.META.get('HTTP_REFERER'))
    return redirect('emails:alert_list')


@require_POST
def quick_resolve_alert(request, pk):
    """View para resolução rápida de alerta"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    alert = get_object_or_404(EmailAlert, pk=pk)
    alert.resolve()
    
    messages.success(request, f"Alerta resolvido: {alert.title}")
    
    if request.META.get('HTTP_REFERER'):
        return redirect(request.META.get('HTTP_REFERER'))
    return redirect('emails:alert_list')