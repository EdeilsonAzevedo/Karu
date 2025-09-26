from django.urls import path

from .views import (
    LogoutView,
    MyLoginView,
    dashboard_gestor,
    dashboard_pais,
    dashboard_profissional,
    post_login_router,
)

app_name = "accounts"
urlpatterns = [
    path("login/", MyLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("post-login/", post_login_router, name="post_login_router"),
    path("dashboard/gestor/", dashboard_gestor, name="dashboard_gestor"),
    path("dashboard/profissional/", dashboard_profissional, name="dashboard_profissional"),
    path("dashboard/pais/", dashboard_pais, name="dashboard_pais"),
]
