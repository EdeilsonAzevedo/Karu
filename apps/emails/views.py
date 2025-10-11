from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import EmailAlert

class AlertListView(LoginRequiredMixin, ListView):
    model = EmailAlert
    template_name = 'emails/alert_list.html'
    context_object_name = 'alerts'
    paginate_by = 20
    
    def get_queryset(self):
        return EmailAlert.objects.select_related('patient').order_by('-created_at')

class AlertDetailView(LoginRequiredMixin, DetailView):
    model = EmailAlert
    template_name = 'emails/alert_detail.html'
    context_object_name = 'alert'