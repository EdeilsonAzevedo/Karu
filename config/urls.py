"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

from apps.accounts.views import MyLoginView, MyLogoutView
from apps.manager.views import manager_dashboard

urlpatterns = [
    # ROTA PÚBLICA (landing)
    path("", include("apps.core.urls")),  # <— raiz pública
    # ÁREA AUTENTICADA
    path("home/", manager_dashboard, name="home"),
    path("admin/", admin.site.urls),
    path("patients/", include("apps.patients.urls")),
    path("manager/", include("apps.manager.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("login/", MyLoginView.as_view(), name="login"),
    path("logout/", MyLogoutView.as_view(), name="logout"),
]
