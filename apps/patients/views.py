from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

# IMPORTS ATUALIZADOS (VERSÃO DO SEU PARCEIRO)
from .forms import (
    ClinicalWarningSignForm,
    ConsultationRecordForm,
    DischargeRecordForm,
    PatientForm,
    RecordForm,
)
from .models import (
    ClinicalWarningSign,
    Exam,
    Patient,
    Record,
    Vaccine,
)


def patient_list(request):
    """Lista + busca por nome, CPF e certidão (q geral ou campos específicos name/cpf/sal)."""
    qs = Patient.objects.all().order_by("first_name", "last_name")

    q = request.GET.get("q")
    name = request.GET.get("name")
    cpf = request.GET.get("cpf")
    sal = request.GET.get("sal")  # certidão

    if q:
        qs = qs.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(cpf__icontains=q)
            | Q(birth_certificate_number__icontains=q)
        )
    else:
        if name:
            qs = qs.filter(Q(first_name__icontains=name) | Q(last_name__icontains=name))
        if cpf:
            qs = qs.filter(cpf__icontains=cpf)
        if sal:
            qs = qs.filter(birth_certificate_number__icontains=sal)

    return render(request, "patients/list.html", {"patients": qs})


@transaction.atomic
def patient_create(request):
    """
    Cria Paciente + Record(discharge) + DischargeRecord.
    """
    if request.method == "POST":
        patient_form = PatientForm(request.POST)
        record_form = RecordForm(request.POST)
        discharge_form = DischargeRecordForm(request.POST)

        if patient_form.is_valid() and record_form.is_valid() and discharge_form.is_valid():
            patient = patient_form.save()

            record = record_form.save(commit=False)
            record.patient = patient
            record.record_type = "discharge"
            record.save()

            discharge = discharge_form.save(commit=False)
            discharge.record = record
            discharge.save()

            return redirect("patients:list")
    else:
        patient_form = PatientForm()
        record_form = RecordForm()
        discharge_form = DischargeRecordForm()

    return render(
        request,
        "patients/newborn-registration.html",
        {
            "patient_form": patient_form,
            "record_form": record_form,
            "discharge_form": discharge_form,
        },
    )


@transaction.atomic
def patient_edit(request, pk):
    """Edita apenas os dados cadastrais básicos do paciente."""
    patient = get_object_or_404(Patient, pk=pk)

    if request.method == "POST":
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            return redirect("patients:detail", pk=patient.pk)
    else:
        form = PatientForm(instance=patient)

    return render(
        request,
        "patients/edit.html",
        {"form": form, "patient": patient},
    )


def _get_growth_chart_data(patient):
    # Busca por registros que contenham medições antropométricas
    records_for_chart = (
        Record.objects.filter(
            Q(consultation_details__isnull=False) | Q(discharge__isnull=False), patient=patient
        )
        .order_by("date")
        .distinct()
    )

    # Prepara as listas para o gráfico
    chart_labels = []
    patient_weight_data = []
    patient_length_data = []
    patient_head_data = []

    for rec in records_for_chart:
        chart_labels.append(rec.date.strftime("%d/%m/%Y"))

        # Pega os dados da consulta ou da alta, o que estiver disponível
        consultation_details = getattr(rec, "consultation_details", None)
        discharge_details = getattr(rec, "discharge", None)

        if consultation_details and consultation_details.weight:
            patient_weight_data.append(float(consultation_details.weight))
            patient_length_data.append(
                float(consultation_details.length) if consultation_details.length else None
            )
            patient_head_data.append(
                float(consultation_details.head_circumference)
                if consultation_details.head_circumference
                else None
            )
        elif discharge_details and discharge_details.weight:
            patient_weight_data.append(float(discharge_details.weight))
            patient_length_data.append(
                float(discharge_details.length) if discharge_details.length else None
            )
            patient_head_data.append(
                float(discharge_details.head_circumference)
                if discharge_details.head_circumference
                else None
            )

    return {
        "chart_labels": chart_labels,
        "weight_data": {
            "patient": patient_weight_data,
            "p10": [weight * 0.9 if weight else None for weight in patient_weight_data],
            "p50": [weight * 1.0 if weight else None for weight in patient_weight_data],
            "p90": [weight * 1.1 if weight else None for weight in patient_weight_data],
        },
        "length_data": {
            "patient": patient_length_data,
            "p10": [length * 0.95 if length else None for length in patient_length_data],
            "p50": [length * 1.0 if length else None for length in patient_length_data],
            "p90": [length * 1.05 if length else None for length in patient_length_data],
        },
        "head_data": {
            "patient": patient_head_data,
            "p10": [head * 0.98 if head else None for head in patient_head_data],
            "p50": [head * 1.0 if head else None for head in patient_head_data],
            "p90": [head * 1.02 if head else None for head in patient_head_data],
        },
    }


def get_weight_gain_analysis_data(patient):
    # Busca todos os registros com peso, ordenados por data
    records_with_weight = (
        Record.objects.filter(
            Q(consultation_details__weight__isnull=False) | Q(discharge__weight__isnull=False),
            patient=patient,
        )
        .order_by("date")
        .distinct()
    )

    if records_with_weight.count() < 2:
        # Não é possível calcular ganho com menos de 2 medições
        return {
            "bar_chart_labels": [],
            "bar_chart_data": [],
            "bar_chart_colors": [],
            "average_gain_30_days": 0,
            "current_gain_7_days": 0,
            "status": "insufficient_data",
        }

    # 1. Cálculo para o Gráfico de Barras (Ganho entre consultas)
    bar_chart_labels = []
    bar_chart_data = []
    bar_chart_colors = []

    # Constrói uma lista simples com data e peso
    measurements = []
    for rec in records_with_weight:
        weight = None
        # Checa de forma segura se é um registro de consulta com peso
        if (
            hasattr(rec, "consultation_details")
            and rec.consultation_details
            and rec.consultation_details.weight is not None
        ):
            weight = float(rec.consultation_details.weight)
        # Se não for, checa de forma segura se é um registro de alta com peso
        elif hasattr(rec, "discharge") and rec.discharge and rec.discharge.weight is not None:
            weight = float(rec.discharge.weight)

        # Só adiciona à lista se um peso válido foi encontrado
        if weight is not None:
            measurements.append({"date": rec.date, "weight": weight})

    for i in range(1, len(measurements)):
        prev = measurements[i - 1]
        curr = measurements[i]

        delta_days = (curr["date"] - prev["date"]).days
        if delta_days > 0:
            delta_weight = curr["weight"] - prev["weight"]
            daily_gain = round(delta_weight / delta_days)

            label = f'{prev["date"].strftime("%d/%m")}-{curr["date"].strftime("%d/%m")}'
            bar_chart_labels.append(label)
            bar_chart_data.append(daily_gain)

            # Define a cor da barra com base na meta
            if 15 <= daily_gain <= 30:
                bar_chart_colors.append("rgba(34, 197, 94, 0.7)")  # Verde
            else:
                bar_chart_colors.append("rgba(245, 158, 11, 0.7)")  # Laranja

    # 2. Cálculo do Ganho Atual (últimos 7 dias)
    current_gain_7_days = bar_chart_data[-1] if bar_chart_data else 0

    # 3. Cálculo do Ganho Médio (últimos 30 dias)
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    recent_measurements = [m for m in measurements if m["date"] >= thirty_days_ago]

    average_gain_30_days = 0
    if len(recent_measurements) >= 2:
        first = recent_measurements[0]
        last = recent_measurements[-1]
        delta_days = (last["date"] - first["date"]).days
        if delta_days > 0:
            delta_weight = last["weight"] - first["weight"]
            average_gain_30_days = round(delta_weight / delta_days)

    # 4. Determinar o status
    status = "adequate"
    if current_gain_7_days < 15:
        status = "low"
    elif current_gain_7_days > 30:
        status = "high"

    return {
        "bar_chart_labels": bar_chart_labels,
        "bar_chart_data": bar_chart_data,
        "bar_chart_colors": bar_chart_colors,
        "average_gain_30_days": average_gain_30_days,
        "current_gain_7_days": current_gain_7_days,
        "status": status,
    }


def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)

    # --- DADOS PARA O HISTÓRICO ---
    # Usamos prefetch_related para otimizar a busca de dados relacionados
    consultation_records = (
        patient.records.filter(record_type="consultation")
        .order_by("-date")
        .prefetch_related("consultation_details", "warning_signs")
    )

    # --- DADOS PARA OS CARDS DE ALERTAS E MEDICAÇÕES ---
    # Busca todos os exames e vacinas de todos os registros do paciente
    patient_exams = Exam.objects.filter(record__patient=patient).order_by("-date")
    patient_vaccines = Vaccine.objects.filter(record__patient=patient).order_by("-date")

    # --- DADOS PARA A EQUIPE RESPONSÁVEL ---
    # Pega os nomes únicos de todos os profissionais que já atenderam o paciente
    team_professionals = (
        patient.records.exclude(professional__isnull=True)
        .exclude(professional__exact="")
        .values_list("professional", flat=True)
        .distinct()
    )

    # --- CÁLCULOS DE IDADE E GRÁFICOS ---
    chart_context = _get_growth_chart_data(patient)
    weight_gain_context = get_weight_gain_analysis_data(patient)

    today = timezone.now().date()
    age_timedelta = today - patient.date_of_birth
    age_in_days = age_timedelta.days
    total_days_corrected = (patient.gestational_age_weeks * 7) + age_in_days
    corrected_age_weeks = total_days_corrected // 7
    corrected_age_remaining_days = total_days_corrected % 7

    # --- MONTAGEM DO CONTEXTO FINAL ---
    context = {
        "patient": patient,
        "consultation_records": consultation_records,
        "age_in_days": age_in_days,
        "corrected_age_weeks": corrected_age_weeks,
        "corrected_age_remaining_days": corrected_age_remaining_days,
        "patient_exams": patient_exams,
        "patient_vaccines": patient_vaccines,
        "team_professionals": team_professionals,
    }

    context.update(chart_context)
    context.update(weight_gain_context)

    return render(request, "patients/patient_detail.html", context)


@transaction.atomic
def consultation_create(request, pk):
    patient = get_object_or_404(Patient, pk=pk)

    if request.method == "POST":
        record_form = RecordForm(request.POST, prefix="record")
        consultation_form = ConsultationRecordForm(request.POST, prefix="consultation")

        warning_sign_forms = []
        for value, label in ClinicalWarningSign.WarningSignType.choices:
            form = ClinicalWarningSignForm(request.POST, prefix=f"warning_{value}")
            warning_sign_forms.append({"form": form, "value": value})

        all_forms_valid = all(
            [
                record_form.is_valid(),
                consultation_form.is_valid(),
                all(item["form"].is_valid() for item in warning_sign_forms),
            ]
        )

        if all_forms_valid:
            record = record_form.save(commit=False)
            record.patient = patient
            record.record_type = "consultation"
            record.save()

            consultation_details = consultation_form.save(commit=False)
            consultation_details.record = record
            consultation_details.save()

            for item in warning_sign_forms:
                if item["form"].cleaned_data.get("is_present"):
                    ClinicalWarningSign.objects.create(
                        record=record, type=item["value"], is_present=True
                    )

            return redirect("patients:detail", pk=patient.pk)

    else:  # GET Request
        record_form = RecordForm(prefix="record")
        consultation_form = ConsultationRecordForm(prefix="consultation")

        clinical_forms_with_labels = []
        for value, label in ClinicalWarningSign.WarningSignType.choices:
            form = ClinicalWarningSignForm(prefix=f"warning_{value}", initial={"type": value})
            clinical_forms_with_labels.append({"form": form, "label": label})

    today = timezone.now().date()
    total_days_corrected = (patient.gestational_age_weeks * 7) + (
        today - patient.date_of_birth
    ).days
    corrected_age_weeks = total_days_corrected // 7
    corrected_age_remaining_days = total_days_corrected % 7

    context = {
        "patient": patient,
        "record_form": record_form,
        "consultation_form": consultation_form,
        "clinical_forms": clinical_forms_with_labels,
        "corrected_age_weeks": corrected_age_weeks,
        "corrected_age_remaining_days": corrected_age_remaining_days,
    }
    return render(request, "patients/consultation_form.html", context)
