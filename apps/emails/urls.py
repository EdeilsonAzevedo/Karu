from django.urls import path

from . import views

app_name = "emails"

urlpatterns = [
    path("alerts/", views.AlertListView.as_view(), name="alert_list"),
    path("alerts/<uuid:pk>/", views.AlertDetailView.as_view(), name="alert_detail"),
]
