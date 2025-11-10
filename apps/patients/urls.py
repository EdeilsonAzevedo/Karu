from django.urls import path

from . import views

app_name = "patients"

urlpatterns = [
    path("", views.patient_list, name="list"),  # listagem + busca
    path("create/", views.patient_create, name="create"),  # cadastro (paciente + alta)
    path("<uuid:pk>/edit/", views.patient_edit, name="edit"),
    path("<uuid:pk>/", views.patient_detail, name="detail"),
    path("<uuid:pk>/consultation/create/", views.consultation_create, name="consultation_create"),
    path("<uuid:pk>/exam/add/", views.exam_add, name="exam_add"),
    path("<uuid:pk>/vaccine/add/", views.vaccine_add, name="vaccine_add"),
    path("<uuid:pk>/exam/<uuid:exam_pk>/delete/", views.exam_delete, name="exam_delete"),
    path(
        "<uuid:pk>/vaccine/<uuid:vaccine_pk>/delete/", views.vaccine_delete, name="vaccine_delete"
    ),
    path(
        "<uuid:pk>/consultation/<uuid:record_pk>/delete/",
        views.consultation_delete,
        name="consultation_delete",
    ),
    path("<uuid:pk>/exam/<uuid:exam_pk>/edit/", views.exam_edit, name="exam_edit"),
    path("<uuid:pk>/vaccine/<uuid:vaccine_pk>/edit/", views.vaccine_edit, name="vaccine_edit"),
    path(
        "<uuid:pk>/consultation/<uuid:record_pk>/edit/",
        views.consultation_edit,
        name="consultation_edit",
    ),
    path("<uuid:pk>/discharge/", views.patient_discharge, name="discharge"),
    path("<uuid:pk>/exam/<uuid:exam_pk>/result/", views.exam_result, name="exam_result"),
]
