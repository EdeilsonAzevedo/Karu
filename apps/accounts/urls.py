from django.urls import path

from .views import (
    area_pais,
    area_profissional,
    ativar_usuario,
    desativar_usuario,
    detalhes_usuario,
    editar_usuario,
    list_users,
    only_authenticated,
    only_gestores,
    signup_gestor,
    signup_pais,
    signup_profissional,
)

app_name = "accounts"
urlpatterns = [
    path("secure/authenticated/", only_authenticated, name="only_authenticated"),
    path("secure/gestores-only/", only_gestores, name="only_gestores"),
    path("secure/profissionais/", area_profissional, name="area_profissional"),
    path("secure/pais/", area_pais, name="area_pais"),
    path("signup/gestor/", signup_gestor, name="signup_gestor"),
    path("signup/profissional/", signup_profissional, name="signup_profissional"),
    path("signup/pais/", signup_pais, name="signup_pais"),
    path("usuarios/", list_users, name="listar_usuarios"),
    path("usuarios/<int:user_id>/detalhes/", detalhes_usuario, name="detalhes_usuario"),
    path("usuarios/<int:user_id>/editar/", editar_usuario, name="editar_usuario"),  # NOVA URL
    path("usuarios/<int:user_id>/desativar/", desativar_usuario, name="desativar_usuario"),
    path("usuarios/<int:user_id>/ativar/", ativar_usuario, name="ativar_usuario"),
]
