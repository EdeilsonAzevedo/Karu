from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .forms import LoginForm
from .models import User


class MyLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm


@login_required
def post_login_router(request):
    u = request.user
    if u.user_type == User.UserType.GESTOR:
        return redirect("accounts:dashboard_gestor")
    if u.user_type == User.UserType.PROFISSIONAL_SAUDE:
        return redirect("accounts:dashboard_profissional")
    return redirect("accounts:dashboard_pais")


@login_required
def dashboard_gestor(request):
    return render(request, "accounts/dash_gestor.html")


@login_required
def dashboard_profissional(request):
    return render(request, "accounts/dash_profissional.html")


@login_required
def dashboard_pais(request):
    return render(request, "accounts/dash_pais.html")
