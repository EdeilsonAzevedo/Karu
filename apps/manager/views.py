# Importa o modelo LogEntry da biblioteca django-auditlog
import unicodedata
from collections import defaultdict

from auditlog.models import LogEntry
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from apps.patients.models import ConsultationRecord, Patient, Record


def normalize_str(s):
    """
    Remove acentos, converte para minúsculo, remove espaços extras
    e aplica title case. Ex: ' MãCeIó ' -> 'Maceio'
    """
    if not s:
        return ""
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("utf-8").strip().title()


MICRORREGIAO_POR_MUNICIPIO = {
    "Maceió": "1ª Região de Saúde",
    "Barra de Santo Antônio": "1ª Região de Saúde",
    "Barra de São Miguel": "1ª Região de Saúde",
    "Coqueiro Seco": "1ª Região de Saúde",
    "Flexeiras": "1ª Região de Saúde",
    "Marechal Deodoro": "1ª Região de Saúde",
    "Messias": "1ª Região de Saúde",
    "Paripueira": "1ª Região de Saúde",
    "Pilar": "1ª Região de Saúde",
    "Rio Largo": "1ª Região de Saúde",
    "Santa Luzia do Norte": "1ª Região de Saúde",
    "Satuba": "1ª Região de Saúde",
    "Jacuípe": "2ª Região de Saúde",
    "Japaratinga": "2ª Região de Saúde",
    "Maragogi": "2ª Região de Saúde",
    "Matriz de Camaragibe": "2ª Região de Saúde",
    "Passo de Camaragibe": "2ª Região de Saúde",
    "Porto Calvo": "2ª Região de Saúde",
    "Porto de Pedras": "2ª Região de Saúde",
    "São Luís do Quitunde": "2ª Região de Saúde",
    "São Miguel dos Milagres": "2ª Região de Saúde",
    "Branquinha": "3ª Região de Saúde",
    "Campestre": "3ª Região de Saúde",
    "Colônia Leopoldina": "3ª Região de Saúde",
    "Ibateguara": "3ª Região de Saúde",
    "Joaquim Gomes": "3ª Região de Saúde",
    "Jundiá": "3ª Região de Saúde",
    "Novo Lino": "3ª Região de Saúde",
    "Santana do Mundaú": "3ª Região de Saúde",
    "São José da Laje": "3ª Região de Saúde",
    "União dos Palmares": "3ª Região de Saúde",
    "Atalaia": "4ª Região de Saúde",
    "Cajueiro": "4ª Região de Saúde",
    "Capela": "4ª Região de Saúde",
    "Chã Preta": "4ª Região de Saúde",
    "Mar Vermelho": "4ª Região de Saúde",
    "Maribondo": "4ª Região de Saúde",
    "Murici": "4ª Região de Saúde",
    "Paulo Jacinto": "4ª Região de Saúde",
    "Pindoba": "4ª Região de Saúde",
    "Quebrangulo": "4ª Região de Saúde",
    "Viçosa": "4ª Região de Saúde",
    "Anadia": "5ª Região de Saúde",
    "Boca da Mata": "5ª Região de Saúde",
    "Campo Alegre": "5ª Região de Saúde",
    "Junqueiro": "5ª Região de Saúde",
    "Limoeiro de Anadia": "5ª Região de Saúde",
    "Roteiro": "5ª Região de Saúde",
    "São Miguel dos Campos": "5ª Região de Saúde",
    "Tanque d'Arca": "5ª Região de Saúde",
    "Teotônio Vilela": "5ª Região de Saúde",
    "Coruripe": "6ª Região de Saúde",
    "Feliz Deserto": "6ª Região de Saúde",
    "Igreja Nova": "6ª Região de Saúde",
    "Jequiá da Praia": "6ª Região de Saúde",
    "Olho d'Água Grande": "6ª Região de Saúde",
    "Penedo": "6ª Região de Saúde",
    "Piaçabuçu": "6ª Região de Saúde",
    "Porto Real do Colégio": "6ª Região de Saúde",
    "São Brás": "6ª Região de Saúde",
    "Arapiraca": "7ª Região de Saúde",
    "Batalha": "7ª Região de Saúde",
    "Belo Monte": "7ª Região de Saúde",
    "Campo Grande": "7ª Região de Saúde",
    "Coité do Nóia": "7ª Região de Saúde",
    "Craíbas": "7ª Região de Saúde",
    "Feira Grande": "7ª Região de Saúde",
    "Girau do Ponciano": "7ª Região de Saúde",
    "Jacaré dos Homens": "7ª Região de Saúde",
    "Jaramataia": "7ª Região de Saúde",
    "Lagoa da Canoa": "7ª Região de Saúde",
    "Monteirópolis": "7ª Região de Saúde",
    "Olho d'Água das Flores": "7ª Região de Saúde",
    "Olivença": "7ª Região de Saúde",
    "São Sebastião": "7ª Região de Saúde",
    "Taquarana": "7ª Região de Saúde",
    "Traipu": "7ª Região de Saúde",
    "Belém": "8ª Região de Saúde",
    "Cacimbinhas": "8ª Região de Saúde",
    "Estrela de Alagoas": "8ª Região de Saúde",
    "Igaci": "8ª Região de Saúde",
    "Major Isidoro": "8ª Região de Saúde",
    "Minador do Negrão": "8ª Região de Saúde",
    "Palmeira dos Índios": "8ª Região de Saúde",
    "Canapi": "9ª Região de Saúde",
    "Carneiros": "9ª Região de Saúde",
    "Dois Riachos": "9ª Região de Saúde",
    "Maravilha": "9ª Região de Saúde",
    "Ouro Branco": "9ª Região de Saúde",
    "Palestina": "9ª Região de Saúde",
    "Pão de Açúcar": "9ª Região de Saúde",
    "Poço das Trincheiras": "9ª Região de Saúde",
    "Santana do Ipanema": "9ª Região de Saúde",
    "São José da Tapera": "9ª Região de Saúde",
    "Senador Rui Palmeira": "9ª Região de Saúde",
    "Água Branca": "10ª Região de Saúde",
    "Delmiro Gouveia": "10ª Região de Saúde",
    "Inhapi": "10ª Região de Saúde",
    "Mata Grande": "10ª Região de Saúde",
    "Olho d'Água do Casado": "10ª Região de Saúde",
    "Pariconha": "10ª Região de Saúde",
    "Piranhas": "10ª Região de Saúde",
}

MICRORREGIAO_POR_MUNICIPIO = {normalize_str(k): v for k, v in MICRORREGIAO_POR_MUNICIPIO.items()}

# Mapeia cada Microrregião para sua respectiva Macrorregião de Saúde
MACRORREGIAO_POR_MICRORREGIAO = {
    "1ª Região de Saúde": "Macrorregião I",
    "2ª Região de Saúde": "Macrorregião I",
    "3ª Região de Saúde": "Macrorregião I",
    "4ª Região de Saúde": "Macrorregião I",
    "5ª Região de Saúde": "Macrorregião I",
    "10ª Região de Saúde": "Macrorregião II",
    "6ª Região de Saúde": "Macrorregião I",
    "7ª Região de Saúde": "Macrorregião II",
    "8ª Região de Saúde": "Macrorregião II",
    "9ª Região de Saúde": "Macrorregião II",
}


@login_required
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


@login_required
def manager_dashboard(request):
    """
    Renderiza o template do painel principal do gestor.
    """
    return render(request, "manager/manager-dashboard.html")


@login_required
def dashboard_stats_api(request):
    """
    API view que retorna TODOS os dados dinâmicos para o painel do gestor.
    """
    today = timezone.now().date()
    current_year = today.year

    # --- 1. LÓGICA DE STATUS (BASEADA NA ÚLTIMA CONSULTA) ---
    all_patients = Patient.objects.filter(is_active=True).order_by("-created_at")

    total_ativos_count = all_patients.count()  # <-- Card 1

    # --- 2. CRIANÇAS MONITORADAS (PARA OS CARDS LATERAIS E CONTAGEM) ---
    children_acompanhamento = []  # Lista para TODOS
    children_estaveis = []  # Lista para Estáveis
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
            "status": "Acompanhamento regular",  # Default
            "real_status": "estaveis",  # Default
        }

        # Lógica de busca de consulta (N+1, mas sabemos que funciona)
        latest_consultation = (
            Record.objects.filter(patient=patient, record_type="consultation")
            .order_by("-date", "-created_at")
            .first()
        )

        sinal_count = 0
        consulta_atrasada = False
        data_atraso_str = ""

        if latest_consultation:
            sinal_count = latest_consultation.warning_signs.filter(is_present=True).count()  # type: ignore

            try:
                consultation_details = latest_consultation.consultation_details  # type: ignore

                if (
                    consultation_details
                    and consultation_details.next_appointment_date
                    and consultation_details.next_appointment_date < today
                ):
                    consulta_atrasada = True
                    data_atraso_str = f"Consulta atrasada desde {consultation_details.next_appointment_date.strftime('%d/%m')}"
            except (ConsultationRecord.DoesNotExist, AttributeError):
                pass

        # 3. Classifica e conta baseado nas novas regras
        if sinal_count >= 2:
            # CRÍTICO
            critico_count += 1
            patient_data["real_status"] = "critico"
            sign = (
                latest_consultation.warning_signs.filter(is_present=True).first()  # type: ignore
                if latest_consultation
                else None
            )
            patient_data["status"] = (
                f"Crítico: {sign.get_type_display() if sign else 'Múltiplos sinais'}"  # type: ignore
            )
            children_critico.append(patient_data)

        elif sinal_count == 1 or consulta_atrasada:
            # ALERTA
            alerta_count += 1
            patient_data["real_status"] = "alerta"
            if sinal_count == 1:
                sign = (
                    latest_consultation.warning_signs.filter(is_present=True).first()  # type: ignore
                    if latest_consultation
                    else None
                )
                patient_data["status"] = f"Alerta: {sign.get_type_display() if sign else 'Alerta'}"  # type: ignore
            else:
                patient_data["status"] = data_atraso_str
            children_alerta.append(patient_data)

        else:
            # ESTÁVEIS (SAUDÁVEL)
            estaveis_count += 1
            patient_data["real_status"] = "estaveis"
            children_estaveis.append(patient_data)

    # Cria a lista "Acompanhamento" (Todos) com os 20 mais recentes no total
    children_acompanhamento = children_estaveis + children_alerta + children_critico
    children_acompanhamento = children_acompanhamento[:20]

    # Limita as sub-listas também
    children_alerta = children_alerta[:20]
    children_critico = children_critico[:20]
    children_estaveis = children_estaveis[:20]

    # --- 3. INDICADORES PRINCIPAIS (VISITAS) ---
    visits_completed_this_month = Record.objects.filter(
        record_type="consultation", date__year=today.year, date__month=today.month
    ).count()

    pending_visits_count = ConsultationRecord.objects.filter(
        next_appointment_date__year=today.year,
        next_appointment_date__month=today.month,
        next_appointment_date__gte=today,
    ).count()
    overdue_visits_count = ConsultationRecord.objects.filter(
        next_appointment_date__lt=today
    ).count()
    top_professionals = list(
        Record.objects.filter(professional__isnull=False)
        .exclude(professional__exact="")
        .values("professional")
        .annotate(attendances=Count("id"))
        .order_by("-attendances")[:4]
    )

    discharge_chart_data = {}
    patient_content_type = ContentType.objects.get_for_model(Patient)

    for year in range(current_year - 2, current_year + 1):
        monthly_counts = [0] * 12
        discharges = (
            LogEntry.objects.filter(
                content_type=patient_content_type,
                action=LogEntry.Action.UPDATE,
                timestamp__year=year,
                changes_text__icontains='"is_active": [true, false]',
            )
            .annotate(month=TruncMonth("timestamp"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )

        for item in discharges:
            monthly_counts[item["month"].month - 1] = item["count"]
        discharge_chart_data[year] = monthly_counts

    data = {
        "stats": {
            "babies_in_stage_3": total_ativos_count,
            "casos_alerta": alerta_count,
            "casos_criticos": critico_count,
            "casos_estaveis": estaveis_count,
            "visits_completed": visits_completed_this_month,
            "visits_pending": pending_visits_count,
            "overdue_visits": overdue_visits_count,
        },
        "monitored_children": {
            "acompanhamento": children_acompanhamento,
            "alerta": children_alerta,
            "critico": children_critico,
            "estaveis": children_estaveis,
        },
        "top_professionals": top_professionals,
        "discharge_chart": discharge_chart_data,
        "last_update": timezone.now().strftime("hoje às %H:%M"),
    }

    return JsonResponse(data)


def _titlecase_city(name: str) -> str:
    if not name:
        return "Sem Município"
    return " ".join(p.capitalize() for p in name.split())


def create_count_entry():
    return {"total": 0, "alerta": 0, "critico": 0, "estavel": 0}


def api_map_counts(request):
    """
    API que retorna as contagens de pacientes (total, alerta, critico)
    agregadas.
    """
    today = timezone.now().date()

    counts_municipio = defaultdict(create_count_entry)
    counts_microrregiao = defaultdict(create_count_entry)
    counts_macrorregiao = defaultdict(create_count_entry)

    # 1. Pega TODOS os pacientes ativos
    patients = Patient.objects.filter(is_active=True)

    # 2. Itera por CADA paciente
    for patient in patients:
        city = patient.address_city

        if not city:
            continue

        city_normalized = normalize_str(patient.address_city)

        status = "estavel"
        sinal_count = 0
        consulta_atrasada = False

        # 3. Busca a última consulta (N+1 query, igual ao dashboard_stats_api)
        latest_consultation = (
            Record.objects.filter(patient=patient, record_type="consultation")
            .order_by("-date", "-created_at")
            .first()
        )

        if latest_consultation:
            # 4. Busca os sinais e detalhes (N+1 query)
            sinal_count = latest_consultation.warning_signs.filter(is_present=True).count()  # type: ignore

            # 5. LÓGICA CORRIGIDA: Verifica consulta atrasada INDEPENDENTEMENTE dos sinais
            try:
                consultation_details = latest_consultation.consultation_details  # type: ignore

                if (
                    consultation_details
                    and consultation_details.next_appointment_date
                    and consultation_details.next_appointment_date < today
                ):
                    consulta_atrasada = True
            except (ConsultationRecord.DoesNotExist, AttributeError):
                pass

        # 6. Classifica o status
        if sinal_count >= 2:
            status = "critico"
        elif sinal_count == 1 or consulta_atrasada:
            status = "alerta"
        else:
            status = "estavel"

        # 7. Agregação
        counts_municipio[city_normalized]["total"] += 1
        counts_municipio[city_normalized][status] += 1

        microrregiao = MICRORREGIAO_POR_MUNICIPIO.get(city_normalized)
        if microrregiao:
            counts_microrregiao[microrregiao]["total"] += 1
            counts_microrregiao[microrregiao][status] += 1

            macrorregiao = MACRORREGIAO_POR_MICRORREGIAO.get(microrregiao)
            if macrorregiao:
                counts_macrorregiao[macrorregiao]["total"] += 1
                counts_macrorregiao[macrorregiao][status] += 1

    return JsonResponse(
        {
            "municipio": dict(counts_municipio),
            "microrregiao": dict(counts_microrregiao),
            "macrorregiao": dict(counts_macrorregiao),
        }
    )
