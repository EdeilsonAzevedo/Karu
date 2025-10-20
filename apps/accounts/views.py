from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from auditlog.models import LogEntry
from django.utils import timezone

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


@login_required
def list_users(request):
    UserModel = get_user_model()

    users = UserModel.objects.filter(is_active=True).prefetch_related("groups")

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

    gestores_count = users.filter(user_type='gestor').count()
    profissionais_count = users.filter(user_type='profissional_saude').count()
    pais_count = users.filter(user_type='pais').count()

    paginator = Paginator(users, 20)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "filtros": {"nome": name, "cpf": cpf, "tipo": tipo},
        "total_resultados": paginator.count,
        "gestores_count": gestores_count,
        "profissionais_count": profissionais_count,
        "pais_count": pais_count,
    }

    return render(request, "accounts/list_users.html", context)

@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name__in=['gestores', 'admin']).exists())
def user_detail(request, pk):
    """View para exibir detalhes do usuário em popup"""
    user = get_object_or_404(get_user_model(), pk=pk)
    
    # REGISTRAR AÇÃO DE VISUALIZAÇÃO NO AUDITLOG
    try:
        from django.contrib.contenttypes.models import ContentType
        from auditlog.models import LogEntry
        from django.utils import timezone
        
        LogEntry.objects.create(
            actor=request.user,
            verb='viewed',
            action=0,
            timestamp=timezone.now(),
            content_type=ContentType.objects.get_for_model(user),
            object_pk=str(user.pk),
            object_repr=str(user),
            changes=f"Usuário {request.user} visualizou os detalhes do usuário {user.username}"
        )
    except Exception:
        # Silenciosamente ignora erros no auditlog para não afetar a funcionalidade
        pass
    
    # Determinar o perfil específico do usuário
    profile_data = {}
    if hasattr(user, 'gestor'):
        profile_data = {
            'tipo': 'Gestor',
            'cpf': user.gestor.cpf,
            'telefone': user.gestor.telefone,
            'unidade': user.gestor.unidade,
            'cargo': user.gestor.cargo,
            'departamento': user.gestor.departamento,
        }
    elif hasattr(user, 'profissional'):
        profile_data = {
            'tipo': 'Profissional de Saúde',
            'cpf': user.profissional.cpf,
            'categoria': user.profissional.get_categoria_display(),
            'especialidade': user.profissional.especialidade,
            'conselho': user.profissional.conselho,
            'registro': user.profissional.numero_registro,
            'unidade': user.profissional.unidade,
            'telefone': user.profissional.telefone,
        }
    elif hasattr(user, 'pais'):
        profile_data = {
            'tipo': 'Pais/Responsável',
            'cpf': user.pais.cpf,
            'telefone': user.pais.telefone,
        }
    
    context = {
        'user': user,
        'profile_data': profile_data,
    }
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('accounts/includes/user_detail_modal.html', context)
        return JsonResponse({'html': html})
    
    return render(request, 'accounts/user_detail.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name__in=['gestores', 'admin']).exists())
@require_http_methods(["POST"])
def user_deactivate(request, pk):
    """View para desativar/remover usuário (soft delete)"""
    user = get_object_or_404(get_user_model(), pk=pk)
    
    # Não permitir que usuários se desativem a si mesmos
    if user == request.user:
        return JsonResponse({
            'success': False,
            'message': 'Você não pode desativar sua própria conta.'
        })
    
    # Não permitir desativar superusuários (a menos que seja outro superusuário)
    if user.is_superuser and not request.user.is_superuser:
        return JsonResponse({
            'success': False,
            'message': 'Não é permitido desativar superusuários.'
        })
    
    user.is_active = False
    user.save()
    
    messages.success(request, f'Usuário {user.username} foi desativado com sucesso.')
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Usuário desativado com sucesso.'
        })
    
    return redirect('accounts:listar_usuarios')