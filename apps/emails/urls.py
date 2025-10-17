from django.urls import path
from . import views

app_name = "emails"

urlpatterns = [
    # Listas e Dashboard
    path("alerts/", views.AlertListView.as_view(), name="alert_list"),
    path("alerts/dashboard/", views.AlertDashboardView.as_view(), name="alert_dashboard"),
    
    # Detalhes
    path("alerts/<int:pk>/", views.AlertDetailView.as_view(), name="alert_detail"),
    
    # Ações
    path("alerts/<int:pk>/acknowledge/", views.AcknowledgeAlertView.as_view(), name="acknowledge_alert"),
    path("alerts/<int:pk>/resolve/", views.ResolveAlertView.as_view(), name="resolve_alert"),
    path("alerts/<int:pk>/resend/", views.ResendAlertView.as_view(), name="resend_alert"),
    
    # Ações rápidas (POST)
    path("alerts/<int:pk>/quick-acknowledge/", views.quick_acknowledge_alert, name="quick_acknowledge"),
    path("alerts/<int:pk>/quick-resolve/", views.quick_resolve_alert, name="quick_resolve"),
]