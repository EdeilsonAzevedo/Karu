from django.urls import path

from . import views

app_name = "patients"

urlpatterns = [
    path("", views.patient_list, name="list"),  # listagem + busca
    path("create/", views.patient_create, name="create"),  # cadastro (paciente + alta)
    path("<int:pk>/edit/", views.patient_edit, name="edit"),  # edição completa
]
