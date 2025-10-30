from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import EmailAlert


@login_required
def alert_list(request):
    """Lista de alertas (opcional)"""
    alerts = EmailAlert.objects.all().order_by("-created_at")
    return render(request, "email/alert_list.html", {"alerts": alerts})
