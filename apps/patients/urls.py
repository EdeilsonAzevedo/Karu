from django.urls import path

from . import views

app_name = "patients"

urlpatterns = [
<<<<<<< HEAD
    path("", views.patient_list, name="list"),  # listagem + busca
    path("create/", views.patient_create, name="create"),  # cadastro (paciente + alta)
    path("<uuid:pk>/edit/", views.patient_edit, name="edit"),
    path("<uuid:pk>/", views.patient_detail, name="detail"),
    path("<uuid:pk>/consultation/create/", views.consultation_create, name="consultation_create"),
=======
    path("", views.patient_list, name="list"),               # listagem + busca
    path("create/", views.patient_create, name="create"),    # cadastro (paciente + alta)
    path("<uuid:pk>/edit/", views.patient_edit, name="edit"),
    path("<uuid:pk>/", views.patient_detail, name="detail"),
    path("<uuid:patient_pk>/consultation/create/", views.consultation_create, name="consultation_create"),

>>>>>>> 8e9abce (feat: adicionado tela de historico de consultas dos RN e criar novas consultas para RN ja registrados)
]
