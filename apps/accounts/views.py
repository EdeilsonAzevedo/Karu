import json

from auditlog.models import LogEntry
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import GestorSignupForm, PaisSignupForm, ProfissionalSignupForm
from .models import ProfissionalSaudeProfile, User
from .forms import GestorSignupForm, PaisSignupForm, PasswordResetByDataForm, ProfissionalSignupForm

User = get_user_model()


class MyLoginView(LoginView):
    template_name = "accounts/login.html"

    def form_valid(self, form):
        if self.request.POST.get("remember_me"):
            self.request.session.set_expiry(60 * 60 * 24 * 30)
        return super().form_valid(form)

    def get_success_url(self):
        user = self.request.user

        # Se for Gestor ou Profissional, vai para a 'home' normal
        if not user.is_pais:
            return reverse("home")  # Ou seu dashboard principal

        # Se for Pai/Responsável
        try:
            # 1. Busca o primeiro paciente (filho) vinculado a este responsável
            #    Usamos o related_name "patients" que definimos no Modelo
            first_patient = user.pais.patients.first()

            if first_patient:
                # 2. Se encontrou, redireciona para a página de detalhes desse paciente
                return reverse("patients:detail", kwargs={"pk": first_patient.pk})
            else:
                # 3. Se é um pai sem paciente vinculado, manda para a home
                return reverse("home")
        except Exception:
            # 4. Se der erro (ex: user.pais não existe), manda para a home
            return reverse("home")


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
            form.save(request=request)
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


@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name="gestores").exists())
def editar_usuario(request, user_id):
    """View para editar usuário"""
    try:
        user = get_object_or_404(User, id=user_id)

        if request.method == "POST":
            print(f"DEBUG: Iniciando edição do usuário {user_id}")

            # Capturar dados antes das alterações
            dados_anteriores = _capturar_dados_anteriores(user)
            print(f"DEBUG: Dados anteriores: {dados_anteriores}")

            # Atualizar dados básicos do usuário
            user.first_name = request.POST.get("first_name", "").strip()
            user.email = request.POST.get("email", "").strip().lower()
            user.is_active = request.POST.get("is_active") == "on"

            # Só permite alterar tipo de usuário se for superuser
            if request.user.is_superuser:
                novo_tipo = request.POST.get("user_type")
                if novo_tipo in dict(User.UserType.choices):
                    user.user_type = novo_tipo

            print(
                f"DEBUG: Dados novos do usuário - Nome: {user.first_name}, Email: {user.email}, Ativo: {user.is_active}"
            )
            user.save()

            # Atualizar perfil específico
            _atualizar_perfil_usuario(request, user)

            # Registrar no auditlog
            _registrar_edicao_auditlog(request, user, dados_anteriores)

            # Sempre retornar JSON para requisições AJAX
            return JsonResponse({"success": True, "message": "Usuário atualizado com sucesso!"})

        else:
            # GET request - retornar formulário de edição
            context = _preparar_contexto_edicao(user, request)

            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                html = render_to_string(
                    "accounts/_editar_usuario_content.html", context, request=request
                )
                return HttpResponse(html)

            return render(request, "accounts/editar_usuario.html", context)

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao editar usuário {user_id}: {str(e)}")

        # Retornar erro em JSON
        return JsonResponse(
            {"success": False, "message": f"Erro ao atualizar usuário: {str(e)}"}, status=400
        )


def _preparar_contexto_edicao(user, request):
    """Prepara o contexto para o template de edição"""
    context = {
        "usuario": user,
        "info_adicional": {},
        "tipos_usuario": User.UserType.choices,
        "request": request,  # Passar request para o template
    }

    # Coletar informações específicas do tipo de usuário
    if hasattr(user, "gestor"):
        perfil = user.gestor
        context["info_adicional"] = {
            "tipo": "Gestor",
            "unidade": perfil.unidade,
            "cargo": perfil.cargo,
            "departamento": perfil.departamento,
            "telefone": perfil.telefone,
        }
        context["perfil_type"] = "gestor"

    elif hasattr(user, "profissional"):
        perfil = user.profissional
        context["info_adicional"] = {
            "tipo": "Profissional de Saúde",
            "categoria": perfil.categoria,
            "especialidade": perfil.especialidade,
            "conselho": perfil.conselho,
            "numero_registro": perfil.numero_registro,
            "unidade": perfil.unidade,
            "telefone": perfil.telefone,
        }
        context["categorias"] = ProfissionalSaudeProfile.Categoria.choices
        context["perfil_type"] = "profissional"

    elif hasattr(user, "pais"):
        perfil = user.pais
        context["info_adicional"] = {
            "tipo": "Pais/Responsável",
            "telefone": perfil.telefone,
        }
        context["perfil_type"] = "pais"

    return context


@transaction.atomic
def _processar_edicao_usuario(request, user):
    """Processa a edição do usuário"""
    try:
        dados_anteriores = _capturar_dados_anteriores(user)

        # Atualizar dados básicos do usuário
        user.first_name = request.POST.get("first_name", "").strip()
        user.email = request.POST.get("email", "").strip().lower()
        user.is_active = request.POST.get("is_active") == "on"

        # Só permite alterar tipo de usuário se for superuser
        if request.user.is_superuser:
            novo_tipo = request.POST.get("user_type")
            if novo_tipo in dict(User.UserType.choices):
                user.user_type = novo_tipo

        user.save()

        # Atualizar perfil específico
        _atualizar_perfil_usuario(request, user)

        # Registrar no auditlog
        _registrar_edicao_auditlog(request, user, dados_anteriores)

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": "Usuário atualizado com sucesso!"})

        messages.success(request, "Usuário atualizado com sucesso!")
        return redirect("accounts:listar_usuarios")

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao processar edição do usuário {user.id}: {str(e)}")

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {"success": False, "message": f"Erro ao atualizar usuário: {str(e)}"}, status=400
            )

        messages.error(request, f"Erro ao atualizar usuário: {str(e)}")
        return redirect("accounts:listar_usuarios")


def _capturar_dados_anteriores(user):
    """Captura os dados anteriores para o auditlog"""
    dados = {
        "user": {
            "first_name": user.first_name,
            "email": user.email,
            "user_type": user.user_type,
            "is_active": user.is_active,
        }
    }

    if hasattr(user, "gestor"):
        perfil = user.gestor
        dados["gestor"] = {
            "telefone": perfil.telefone,
            "unidade": perfil.unidade,
            "cargo": perfil.cargo,
            "departamento": perfil.departamento,
        }
    elif hasattr(user, "profissional"):
        perfil = user.profissional
        dados["profissional"] = {
            "telefone": perfil.telefone,
            "categoria": perfil.categoria,
            "especialidade": perfil.especialidade,
            "conselho": perfil.conselho,
            "numero_registro": perfil.numero_registro,
            "unidade": perfil.unidade,
        }
    elif hasattr(user, "pais"):
        perfil = user.pais
        dados["pais"] = {"telefone": perfil.telefone}

    return dados


def _atualizar_perfil_usuario(request, user):
    """Atualiza o perfil específico do usuário"""
    telefone = request.POST.get("telefone", "").strip()

    if hasattr(user, "gestor"):
        perfil = user.gestor
        perfil.telefone = telefone
        perfil.unidade = request.POST.get("unidade", "").strip()
        perfil.cargo = request.POST.get("cargo", "").strip()
        perfil.departamento = request.POST.get("departamento", "").strip()
        perfil.save()

    elif hasattr(user, "profissional"):
        perfil = user.profissional
        perfil.telefone = telefone
        perfil.categoria = request.POST.get("categoria", "")
        perfil.especialidade = request.POST.get("especialidade", "").strip()
        perfil.conselho = request.POST.get("conselho", "").strip() or None
        perfil.numero_registro = request.POST.get("numero_registro", "").strip() or None
        perfil.unidade = request.POST.get("unidade", "").strip()
        perfil.save()

    elif hasattr(user, "pais"):
        perfil = user.pais
        perfil.telefone = telefone
        perfil.save()


def _registrar_edicao_auditlog(request, user, dados_anteriores):
    """Registra a edição no auditlog"""
    try:
        changes = []

        # Comparar dados do usuário
        campos_user = ["first_name", "email", "user_type", "is_active"]
        for campo in campos_user:
            valor_anterior = dados_anteriores["user"].get(campo)
            valor_novo = getattr(user, campo)

            # Converter para string para comparação
            str_anterior = str(valor_anterior) if valor_anterior is not None else ""
            str_novo = str(valor_novo) if valor_novo is not None else ""

            if str_anterior != str_novo:
                changes.append({campo: [str_anterior, str_novo]})

        # Comparar dados do perfil específico
        if hasattr(user, "gestor"):
            perfil = user.gestor
            campos_perfil = ["telefone", "unidade", "cargo", "departamento"]
            for campo in campos_perfil:
                valor_anterior = dados_anteriores.get("gestor", {}).get(campo)
                valor_novo = getattr(perfil, campo)

                str_anterior = str(valor_anterior) if valor_anterior is not None else ""
                str_novo = str(valor_novo) if valor_novo is not None else ""

                if str_anterior != str_novo:
                    changes.append({f"gestor_{campo}": [str_anterior, str_novo]})

        elif hasattr(user, "profissional"):
            perfil = user.profissional
            campos_perfil = [
                "telefone",
                "categoria",
                "especialidade",
                "conselho",
                "numero_registro",
                "unidade",
            ]
            for campo in campos_perfil:
                valor_anterior = dados_anteriores.get("profissional", {}).get(campo)
                valor_novo = getattr(perfil, campo)

                str_anterior = str(valor_anterior) if valor_anterior is not None else ""
                str_novo = str(valor_novo) if valor_novo is not None else ""

                if str_anterior != str_novo:
                    changes.append({f"profissional_{campo}": [str_anterior, str_novo]})

        elif hasattr(user, "pais"):
            perfil = user.pais
            campos_perfil = ["telefone"]
            for campo in campos_perfil:
                valor_anterior = dados_anteriores.get("pais", {}).get(campo)
                valor_novo = getattr(perfil, campo)

                str_anterior = str(valor_anterior) if valor_anterior is not None else ""
                str_novo = str(valor_novo) if valor_novo is not None else ""

                if str_anterior != str_novo:
                    changes.append({f"pais_{campo}": [str_anterior, str_novo]})

        # Registrar mudanças no auditlog
        if changes:
            content_type = ContentType.objects.get_for_model(User)

            # Criar uma representação legível das mudanças
            changes_text = " | ".join(
                [
                    f"{list(change.keys())[0]}: {list(change.values())[0][0]} → {list(change.values())[0][1]}"
                    for change in changes
                ]
            )

            LogEntry.objects.log_create(
                instance=user,
                action=LogEntry.Action.UPDATE,
                changes=json.dumps(changes),
                changes_text=changes_text,
                actor=request.user,
            )

            print(f"DEBUG: Registradas {len(changes)} mudanças no auditlog para usuário {user.id}")
            print(f"DEBUG: Mudanças: {changes}")
        else:
            print("DEBUG: Nenhuma mudança detectada para registro no auditlog")

    except Exception as e:
        print(f"DEBUG: Erro ao registrar no auditlog: {e}")
        import traceback

        traceback.print_exc()
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
