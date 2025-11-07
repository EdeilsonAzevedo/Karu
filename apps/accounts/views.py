from auditlog.models import LogEntry
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods

from .forms import GestorSignupForm, PaisSignupForm, PasswordResetByDataForm, ProfissionalSignupForm

User = get_user_model()


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
            # Passe o request para o form poder acessar o usuário atual
            form.set_actor(request.user)
            form.save(request=request)
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
            form.set_actor(request.user)
            form.save(request=request)
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
            form.set_actor(request.user)
            user = form.save(request=request)
            messages.success(request, "Pai/responsável criado com sucesso.")
            return redirect("home")
    else:
        form = PaisSignupForm()
    return render(request, "accounts/signup_pais.html", {"form": form})


@login_required
def list_users(request):
    UserModel = get_user_model()

    users = UserModel.objects.all().prefetch_related("groups")

    name = request.GET.get("nome", "").strip()
    if name:
        users = users.filter(
            Q(first_name__icontains=name)
            | Q(last_name__icontains=name)
            | Q(username__icontains=name)
        )

    cpf = request.GET.get("cpf", "").strip()
    if cpf:
        cpf_clear = cpf.replace(".", "").replace("-", "").replace(" ", "")
        users = users.filter(
            Q(gestor__cpf__icontains=cpf_clear)
            | Q(profissional__cpf__icontains=cpf_clear)
            | Q(pais__cpf__icontains=cpf_clear)
        )

    tipo = request.GET.get("tipo", "").strip()
    if tipo:
        users = users.filter(user_type=tipo)

    # Ordenação
    users = users.order_by("username").distinct()

    contadores = UserModel.objects.values("user_type").annotate(count=Count("id"))

    contadores_dict = {item["user_type"]: item["count"] for item in contadores}

    gestores_count = contadores_dict.get("gestor", 0)
    profissionais_count = contadores_dict.get("profissional_saude", 0)
    pais_count = contadores_dict.get("pais", 0)

    paginator = Paginator(users, 20)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    tipos_disponiveis = UserModel.UserType.choices  # type: ignore

    context = {
        "page_obj": page_obj,
        "grupos_disponiveis": tipos_disponiveis,
        "filtros": {"nome": name, "cpf": cpf, "tipo": tipo},
        "total_resultados": paginator.count,
        "gestores_count": gestores_count,
        "profissionais_count": profissionais_count,
        "pais_count": pais_count,
    }

    return render(request, "accounts/list_users.html", context)


@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name="gestores").exists())
def detalhes_usuario(request, user_id):
    """Exibe os detalhes completos de um usuário (para modal)"""
    try:
        user = get_object_or_404(get_user_model(), id=user_id)

        # Coletar informações específicas do tipo de usuário
        info_adicional = {}

        # Verificar se o usuário tem perfil de gestor
        if hasattr(user, "gestor"):
            perfil = user.gestor
            info_adicional = {
                "tipo": "Gestor",
                "unidade": perfil.unidade,
                "cargo": perfil.cargo,
                "departamento": perfil.departamento,
                "telefone": perfil.telefone,
                "data_criacao": perfil.created_at,
            }
        # Verificar se o usuário tem perfil de profissional
        elif hasattr(user, "profissional"):
            perfil = user.profissional
            info_adicional = {
                "tipo": "Profissional de Saúde",
                "categoria": perfil.get_categoria_display(),
                "especialidade": perfil.especialidade,
                "conselho": perfil.conselho,
                "numero_registro": perfil.numero_registro,
                "unidade": perfil.unidade,
                "telefone": perfil.telefone,
                "data_criacao": perfil.created_at,
            }
        # Verificar se o usuário tem perfil de pais
        elif hasattr(user, "pais"):
            perfil = user.pais
            info_adicional = {
                "tipo": "Pais/Responsável",
                "telefone": perfil.telefone,
                "data_criacao": perfil.created_at,
            }
            # Adicionar filhos se existirem
            if hasattr(perfil, "filhos"):
                info_adicional["filhos"] = list(perfil.filhos.all())

        context = {
            "usuario": user,
            "info_adicional": info_adicional,
        }

        # Se for requisição AJAX, retorna apenas o conteúdo do modal
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            html = render_to_string("accounts/_detalhes_usuario_content.html", context)
            return HttpResponse(html)

        # Se não for AJAX, retorna a página completa (fallback)
        return render(request, "accounts/detalhes_usuario.html", context)

    except Exception as e:
        # Log do erro para debug
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao carregar detalhes do usuário {user_id}: {str(e)}")

        # Retorna uma mensagem de erro
        error_message = f"Erro ao carregar detalhes do usuário: {str(e)}"

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return HttpResponse(f'<div class="alert alert-error"><p>{error_message}</p></div>')

        messages.error(request, error_message)
        return redirect("accounts:listar_usuarios")


@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name="gestores").exists())
def desativar_usuario(request, user_id):
    """Desativa um usuário, removendo seu acesso ao sistema"""
    try:
        if request.method == "POST":
            user = get_object_or_404(User, id=user_id)

            # Não permitir que usuários desativem a si mesmos
            if user == request.user:
                messages.error(request, "Você não pode desativar sua própria conta.")
                return redirect("accounts:listar_usuarios")

            # Não permitir que gestores desativem superusuários
            if user.is_superuser and not request.user.is_superuser:
                messages.error(
                    request, "Apenas superusuários podem desativar outros superusuários."
                )
                return redirect("accounts:listar_usuarios")

            # Salvar estado anterior
            was_active = user.is_active

            # Desativar o usuário
            user.is_active = False
            user.save()

            # Criar registro manual no auditlog
            content_type = ContentType.objects.get_for_model(User)

            LogEntry.objects.create(
                content_type=content_type,
                object_pk=str(user.pk),
                object_id=user.id,
                object_repr=str(user),
                action=LogEntry.Action.UPDATE,
                changes=f'[{{"is_active": [{str(was_active).lower()}, false]}}]',
                actor=request.user,
                remote_addr=request.META.get("REMOTE_ADDR"),
            )

            messages.success(
                request,
                f"Usuário {user.get_full_name() or user.username} (CPF: {user.username}) foi desativado com sucesso.",
            )

        return redirect("accounts:listar_usuarios")

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao desativar usuário {user_id}: {str(e)}")
        messages.error(request, f"Erro ao desativar usuário: {str(e)}")
        return redirect("accounts:listar_usuarios")


@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name="gestores").exists())
def ativar_usuario(request, user_id):
    """Ativa um usuário, restaurando seu acesso ao sistema"""
    try:
        if request.method == "POST":
            user = get_object_or_404(User, id=user_id)

            # Salvar estado anterior
            was_active = user.is_active

            # Ativar o usuário
            user.is_active = True
            user.save()

            # Criar registro manual no auditlog
            content_type = ContentType.objects.get_for_model(User)

            LogEntry.objects.create(
                content_type=content_type,
                object_pk=str(user.pk),
                object_id=user.id,
                object_repr=str(user),
                action=LogEntry.Action.UPDATE,
                changes=f'[{{"is_active": [{str(was_active).lower()}, true]}}]',
                actor=request.user,
                remote_addr=request.META.get("REMOTE_ADDR"),
            )

            messages.success(
                request,
                f"Usuário {user.get_full_name() or user.username} (CPF: {user.username}) foi ativado com sucesso.",
            )

        return redirect("accounts:listar_usuarios")

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao ativar usuário {user_id}: {str(e)}")
        messages.error(request, f"Erro ao ativar usuário: {str(e)}")
        return redirect("accounts:listar_usuarios")
    
    
@require_http_methods(["GET", "POST"])
def password_reset_manual(request):
    form = PasswordResetByDataForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(
            request, "Senha alterada com sucesso. Faça login com seu CPF e a nova senha."
        )
        return redirect("login")
    return render(
        request,
        "accounts/password_reset_manual.html",
        {"form": form, "hide_sidebar": True},
    )
