from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponse
from django.shortcuts import redirect, render

from .forms import GestorSignupForm, PaisSignupForm, ProfissionalSignupForm


class MyLoginView(LoginView):
    template_name = "accounts/login.html"

    def form_valid(self, form):
        if self.request.POST.get("remember_me"):
            self.request.session.set_expiry(60 * 60 * 24 * 30)
        return super().form_valid(form)


class MyLogoutView(LogoutView):
    pass


def is_superuser_or_in_group(group_name: str):
    return user_passes_test(
        lambda u: u.is_authenticated
        and (u.is_superuser or u.groups.filter(name=group_name).exists()),
        login_url="login",
    )


@login_required
def home(request):
    user = request.user
    my_groups = list(user.groups.values_list("name", flat=True))

    all_users = None
    if user.is_superuser:
        UserModel = get_user_model()
        all_users = (
            UserModel.objects.all()
            .prefetch_related("groups")
            .only("id", "username", "email", "is_active")
            .order_by("username")
        )

    context = {"my_groups": my_groups, "all_users": all_users}
    return render(request, "accounts/home.html", context)


@login_required
def only_authenticated(request):
    return HttpResponse("Qualquer usuário logado vê isso.")


def in_group(name: str):
    return user_passes_test(
        lambda u: u.is_authenticated and u.groups.filter(name=name).exists(),
        login_url="login",
    )


@in_group("gestores")
def only_gestores(request):
    return HttpResponse("Só quem está no grupo 'gestores' vê isso.")


@in_group("profissionais_saude")
def area_profissional(request):
    return HttpResponse("Área de Profissionais de Saúde.")


@in_group("pais")
def area_pais(request):
    return HttpResponse("Área de Pais/Responsáveis.")


@user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url="login")
def signup_gestor(request):
    if request.method == "POST":
        form = GestorSignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Gestor criado com sucesso.")
            return redirect("home")
    else:
        form = GestorSignupForm()
    return render(request, "accounts/signup_gestor.html", {"form": form})


@is_superuser_or_in_group("gestores")
def signup_profissional(request):
    if request.method == "POST":
        form = ProfissionalSignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Profissional criado com sucesso.")
            return redirect("home")
    else:
        form = ProfissionalSignupForm()
    return render(request, "accounts/signup_profissional.html", {"form": form})


@is_superuser_or_in_group("gestores")
def signup_pais(request):
    if request.method == "POST":
        form = PaisSignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Pai/responsável criado com sucesso.")
            return redirect("home")
    else:
        form = PaisSignupForm()
    return render(request, "accounts/signup_pais.html", {"form": form})
