from django.urls import path

from .views import (
    MyLoginView,
    MyLogoutView,
    area_pais,
    area_profissional,
    home,
    only_authenticated,
    only_gestores,
    signup_gestor,
    signup_pais,
    signup_profissional,
)

app_name = "accounts"
urlpatterns = [
    path("login/", MyLoginView.as_view(), name="login"),
    path("logout/", MyLogoutView.as_view(), name="logout"),
    path("home/", home, name="home"),
    path("secure/authenticated/", only_authenticated, name="only_authenticated"),
    path("secure/gestores-only/", only_gestores, name="only_gestores"),
    path("secure/profissionais/", area_profissional, name="area_profissional"),
    path("secure/pais/", area_pais, name="area_pais"),
    path("signup/gestor/", signup_gestor, name="signup_gestor"),
    path("signup/profissional/", signup_profissional, name="signup_profissional"),
    path("signup/pais/", signup_pais, name="signup_pais"),
]
