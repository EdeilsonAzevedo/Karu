# Importa o modelo LogEntry da biblioteca django-auditlog
from auditlog.models import LogEntry
from django.core.paginator import Paginator
from django.db.models import Q, Count, Subquery, OuterRef
from django.shortcuts import render
from django.http import JsonResponse
from collections import defaultdict
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from apps.patients.models import Patient, Record, ConsultationRecord, ClinicalWarningSign
from django.contrib.contenttypes.models import ContentType

# @login_required
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

def _calculate_age_string(birth_date, gestational_weeks):
    """Calcula a idade cronológica e corrigida e retorna uma string formatada."""
    if not birth_date:
        return "Idade desconhecida"
    
    today = timezone.now().date()
    
    # Idade Cronológica
    chrono_days = (today - birth_date).days
    chrono_weeks = chrono_days // 7
    chrono_remaining_days = chrono_days % 7
    
    # Idade Corrigida (se prematuro < 37 semanas)
    corrected_str = ""
    if gestational_weeks < 37:
        prematurity_days = (40 - gestational_weeks) * 7
        corrected_days = max(0, chrono_days - prematurity_days)
        corrected_weeks = corrected_days // 7
        corrected_str = f" (IC: {corrected_weeks}s)"

    return f"{chrono_weeks}s + {chrono_remaining_days}d{corrected_str}"

# @login_required
def manager_dashboard(request):
    """
    Renderiza o template do painel principal do gestor.
    """
    return render(request, 'manager/manager-dashboard.html')

# @login_required
# Em apps/patients/views.py

# ... (Mantenha todos os seus imports, incluindo Count, Q, timezone, etc.)

# @login_required
def dashboard_stats_api(request):
    """
    API view que retorna TODOS os dados dinâmicos para o painel do gestor.
    Card 1 (Acompanhamentos Ativos): TOTAL de pacientes ativos.
    Abas: Acompanhamento (Todos), Alerta (Filtrado), Crítico (Filtrado).
    """
    today = timezone.now().date()
    current_year = today.year
    
    # --- 1. LÓGICA DE STATUS (BASEADA NA ÚLTIMA CONSULTA) ---
    all_patients = Patient.objects.filter(is_active=True).order_by('-created_at')
    
    total_ativos_count = all_patients.count() # <-- Card 1

    # --- 2. CRIANÇAS MONITORADAS (PARA OS CARDS LATERAIS E CONTAGEM) ---
    children_acompanhamento = [] # Lista para TODOS
    children_estaveis = []
    children_alerta = []
    children_critico = []
    
    estaveis_count = 0
    alerta_count = 0
    critico_count = 0

    for patient in all_patients:
        age_str = _calculate_age_string(patient.date_of_birth, patient.gestational_age_weeks)
        patient_data = {
            "id": patient.id,
            "name": str(patient),
            "age": age_str,
            "status": "Acompanhamento regular", # Default
            "real_status": "estaveis" # Default
        }

        latest_consultation = Record.objects.filter(
            patient=patient, 
            record_type='consultation'
        ).order_by('-date', '-created_at').first()

        sinal_count = 0
        consulta_atrasada = False

        if latest_consultation:
            sinal_count = latest_consultation.warning_signs.filter(is_present=True).count()
            
            if sinal_count == 0:
                try:
                    consultation_details = latest_consultation.consultation_details
                    if consultation_details and \
                       consultation_details.next_appointment_date and \
                       consultation_details.next_appointment_date < today:
                        consulta_atrasada = True
                        patient_data["status"] = f"Consulta atrasada desde {consultation_details.next_appointment_date.strftime('%d/%m')}"
                except ConsultationRecord.DoesNotExist:
                    pass
        
        # 3. Classifica e conta baseado nas novas regras
        if sinal_count >= 2:
            # CRÍTICO
            critico_count += 1
            patient_data["real_status"] = "critico"
            sign = latest_consultation.warning_signs.filter(is_present=True).first()
            patient_data["status"] = f"Crítico: {sign.get_type_display() if sign else 'Múltiplos sinais'}" # type: ignore
            children_critico.append(patient_data)
                
        elif sinal_count == 1 or consulta_atrasada:
            # ALERTA
            alerta_count += 1
            patient_data["real_status"] = "alerta"
            if sinal_count == 1:
                sign = latest_consultation.warning_signs.filter(is_present=True).first()
                patient_data["status"] = f"Alerta: {sign.get_type_display()}" # type: ignore
            # else: status de consulta atrasada já foi definido
            children_alerta.append(patient_data)
                
        else:
            # ESTÁVEIS (SAUDÁVEL)
            estaveis_count += 1
            patient_data["real_status"] = "estaveis"
            children_estaveis.append(patient_data)

    # Cria a lista "Acompanhamento" (Todos) com os 20 mais recentes no total
    children_acompanhamento = (children_estaveis + children_alerta + children_critico)
    # Re-ordena pela data de criação do paciente (já feito pela query inicial)
    # Apenas limita a lista final
    children_acompanhamento = children_acompanhamento[:20]
    
    # Limita as sub-listas também
    children_alerta = children_alerta[:20]
    children_critico = children_critico[:20]


    # --- 3. INDICADORES PRINCIPAIS (VISITAS) ---
    visits_completed_this_month = Record.objects.filter(
        record_type='consultation', date__year=today.year, date__month=today.month
    ).count()

    pending_visits_count = ConsultationRecord.objects.filter(
        next_appointment_date__year=today.year,
        next_appointment_date__month=today.month,
        next_appointment_date__gte=today
    ).count()
    overdue_visits_count = ConsultationRecord.objects.filter(
        next_appointment_date__lt=today
    ).count()
    top_professionals = list(
        Record.objects.filter(professional__isnull=False)
        .exclude(professional__exact='')
        .values('professional')
        .annotate(attendances=Count('id'))
        .order_by('-attendances')[:4]
    )
    
    discharge_chart_data = {}
    patient_content_type = ContentType.objects.get_for_model(Patient)

    for year in range(current_year - 2, current_year + 1):
        monthly_counts = [0] * 12
        # Procura no Log por um UPDATE no modelo Patient onde 'is_active' mudou de 'true' para 'false'
        discharges = LogEntry.objects.filter(
            content_type=patient_content_type,
            action=LogEntry.Action.UPDATE,
            timestamp__year=year,
            changes_text__icontains='"is_active": [true, false]' # Busca pela string da mudança
        ).annotate(month=TruncMonth('timestamp')) \
         .values('month') \
         .annotate(count=Count('id')) \
         .order_by('month')
        
        for item in discharges:
            # O mês vem de 'timestamp', não mais de 'date'
            monthly_counts[item['month'].month - 1] = item['count']
        discharge_chart_data[year] = monthly_counts

    data = {
        "stats": {
            'babies_in_stage_3': total_ativos_count, # Card 1 (Total)
            'casos_alerta': alerta_count,            # Card 2 (Alerta)
            'casos_criticos': critico_count,         # Card 3 (Crítico)
            'casos_estaveis': estaveis_count,        # Contagem interna
            
            'visits_completed': visits_completed_this_month,
            'visits_pending': pending_visits_count,
            'overdue_visits': overdue_visits_count,
        },
        "monitored_children": {
            'acompanhamento': children_acompanhamento,
            'alerta': children_alerta,
            'critico': children_critico,
            # 'estaveis': children_estaveis
        },
        "top_professionals": top_professionals,
        "discharge_chart": discharge_chart_data,
        "last_update": timezone.now().strftime("hoje às %H:%M")
    }

    return JsonResponse(data)

def _titlecase_city(name: str) -> str:
    if not name:
        return "Sem Município"
    return " ".join(p.capitalize() for p in name.split())


def api_map_counts(request):
    """
    Retorna um JSON com a CONTAGEM DE PACIENTES POR STATUS por município,
    e uma chave "acompanhamento" com o TOTAL por município.
    """
    today = timezone.now().date()
    
    acompanhamento = defaultdict(int)
    estaveis = defaultdict(int)
    alerta = defaultdict(int)
    critico = defaultdict(int)

    patients = Patient.objects.filter(
        is_active=True, 
        address_state__iexact="AL"
    ).exclude(address_city__isnull=True).exclude(address_city__exact='')

    for patient in patients:
        city_raw = patient.address_city or ""
        city = _titlecase_city(city_raw.strip())
        
        latest_consultation = Record.objects.filter(
            patient=patient, 
            record_type='consultation'
        ).order_by('-date', '-created_at').first()

        status = "estaveis"
        sinal_count = 0
        consulta_atrasada = False

        if latest_consultation:
            sinal_count = latest_consultation.warning_signs.filter(is_present=True).count()
            if sinal_count == 0:
                try:
                    consultation_details = latest_consultation.consultation_details
                    if consultation_details and \
                       consultation_details.next_appointment_date and \
                       consultation_details.next_appointment_date < today:
                        consulta_atrasada = True
                except ConsultationRecord.DoesNotExist:
                    pass
        
        if sinal_count >= 2:
            critico[city] += 1
        elif sinal_count == 1 or consulta_atrasada:
            alerta[city] += 1
        else:
            estaveis[city] += 1
            
    # Cria o dicionário "acompanhamento" (Todos) somando os totais
    all_cities = set(estaveis.keys()) | set(alerta.keys()) | set(critico.keys())
    for city in all_cities:
        acompanhamento[city] = estaveis[city] + alerta[city] + critico[city]

    data = {
        'acompanhamento': dict(acompanhamento), # Chave para "Todos"
        'alerta': dict(alerta),
        'critico': dict(critico),
        # 'estaveis': dict(estaveis)
    }
    return JsonResponse(data)