from django.urls import path

from . import views

app_name = "patients"

urlpatterns = [
    path("", views.patient_list, name="list"),  # listagem + busca
    path("create/", views.patient_create, name="create"),  # cadastro (paciente + alta)
    path("<uuid:pk>/edit/", views.patient_edit, name="edit"),
    path("<uuid:pk>/", views.patient_detail, name="detail"),
    path("<uuid:pk>/consultation/create/", views.consultation_create, name="consultation_create"),
]
