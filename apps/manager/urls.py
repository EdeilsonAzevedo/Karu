from django.urls import path

from . import views

app_name = "manager"

urlpatterns = [
    path("audit/", views.audit_log_view, name="audit_log"),
    path("dashboard/", views.manager_dashboard, name="dashboard"),
    path("api/dashboard-stats/", views.dashboard_stats_api, name="api_dashboard_stats"),
    path("api/map-counts/", views.api_map_counts, name="api_map_counts"),
]
