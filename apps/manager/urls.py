from django.urls import path
from . import views

app_name = "manager"

urlpatterns = [
    path("audit/", views.audit_log_view, name="audit_log"),
]