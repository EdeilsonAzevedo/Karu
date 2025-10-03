from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

# Importa o modelo LogEntry da biblioteca django-auditlog
from auditlog.models import LogEntry

#@login_required
def audit_log_view(request):
    """
    Exibe a lista de logs de auditoria do django-auditlog em um template customizado.
    """
    # Mapeia os valores do formulário para os valores numéricos do LogEntry
    ACTION_MAP = {
        "create": LogEntry.Action.CREATE,
        "update": LogEntry.Action.UPDATE,
        "delete": LogEntry.Action.DELETE,
    }

    # Inicia a busca por todos os logs, já incluindo dados do autor (actor)
    queryset = LogEntry.objects.select_related("actor").order_by("-timestamp")

    # --- Lógica de Filtros ---
    search_query = request.GET.get("search_query")
    action_type = request.GET.get("action_type")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if search_query:
        queryset = queryset.filter(
            Q(actor__first_name__icontains=search_query)
            | Q(actor__last_name__icontains=search_query)
            | Q(actor__username__icontains=search_query)
            | Q(object_repr__icontains=search_query)
            | Q(changes_text__icontains=search_query)
        )

    if action_type in ACTION_MAP:
        queryset = queryset.filter(action=ACTION_MAP[action_type])

    if start_date:
        queryset = queryset.filter(timestamp__date__gte=start_date)

    if end_date:
        queryset = queryset.filter(timestamp__date__lte=end_date)

    # Paginação
    paginator = Paginator(queryset, 20)  # 20 logs por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Preserva os parâmetros de filtro nos links de paginação
    query_params = request.GET.copy()
    if "page" in query_params:
        del query_params["page"]

    context = {
        "page_obj": page_obj,
        "query_params": query_params.urlencode(),
    }
    return render(request, "manager/audit_log.html", context)