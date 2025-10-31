from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    ClinicalEvaluationForm,
    ClinicalWarningSignForm,
    ConsultationRecordForm,
    DischargeRecordForm,
    InterdisciplinaryEvaluationForm,
    PatientForm,
    RecordForm,
)
from .growth_charts import get_growth_chart_data
from .models import (
    ClinicalEvaluation,
    ClinicalEvaluationType,
    ClinicalWarningSign,
    Exam,
    InterdisciplinaryEvaluation,
    InterdisciplinaryEvaluationArea,
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
    if request.method != "POST":
        patient_form = PatientForm()
        # já cria uma instância com record_type fixé
        record_form = RecordForm(instance=Record(record_type="discharge"))
        discharge_form = DischargeRecordForm()
        clinical_forms = {
            ctype.value: ClinicalEvaluationForm(
                prefix=f"clinic-{ctype.value}", initial={"type": ctype.value}
            )
            for ctype in ClinicalEvaluationType
        }
        team_forms = {
            area.value: InterdisciplinaryEvaluationForm(
                prefix=f"team-{area.value}", initial={"area": area.value}
            )
            for area in InterdisciplinaryEvaluationArea
        }

    else:
        patient_form = PatientForm(request.POST)
        # instancia com record_type para a validação já ter o valor
        record_form = RecordForm(request.POST, instance=Record(record_type="discharge"))
        discharge_form = DischargeRecordForm(request.POST)
        clinical_forms = {
            ctype.value: ClinicalEvaluationForm(request.POST, prefix=f"clinic-{ctype.value}")
            for ctype in ClinicalEvaluationType
        }
        team_forms = {
            area.value: InterdisciplinaryEvaluationForm(request.POST, prefix=f"team-{area.value}")
            for area in InterdisciplinaryEvaluationArea
        }

        all_forms_valid = all(
            [
                patient_form.is_valid(),
                record_form.is_valid(),
                discharge_form.is_valid(),
                all(f.is_valid() for f in clinical_forms.values()),
                all(f.is_valid() for f in team_forms.values()),
            ]
        )

        print(patient_form.errors, record_form.errors, discharge_form.errors)
        for k, f in clinical_forms.items():
            print("clinic", k, f.errors)
        for k, f in team_forms.items():
            print("team", k, f.errors)

        if all_forms_valid:
            patient = patient_form.save()
            record = record_form.save(commit=False)
            record.patient = patient
            # opcional (já está na instância), mas mantém por clareza:
            record.record_type = "discharge"
            record.save()

            discharge = discharge_form.save(commit=False)
            discharge.record = record
            discharge.save()

            for ctype_value, form in clinical_forms.items():
                if form.cleaned_data.get("status"):
                    ClinicalEvaluation.objects.create(
                        record=record, type=ctype_value, status=form.cleaned_data["status"]
                    )

            for area_value, form in team_forms.items():
                if form.cleaned_data.get("notes"):
                    InterdisciplinaryEvaluation.objects.create(
                        record=record, area=area_value, notes=form.cleaned_data["notes"]
                    )

            return redirect("patients:list")

    context = {
        "patient_form": patient_form,
        "record_form": record_form,
        "discharge_form": discharge_form,
        "clinical_forms": clinical_forms,
        "team_forms": team_forms,
        "ClinicalEvaluationType": ClinicalEvaluationType,
        "InterdisciplinaryEvaluationArea": InterdisciplinaryEvaluationArea,
    }
    return render(request, "patients/newborn-registration.html", context)


@transaction.atomic
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    try:
        record = Record.objects.get(patient=patient, record_type="discharge")
        discharge = record.discharge  # type: ignore
    except (Record.DoesNotExist, Record.discharge.RelatedObjectDoesNotExist):  # type: ignore
        record = None
        discharge = None

    existing_clinical_evals = (
        {e.type: e for e in record.clinical_evaluations.all()} if record else {}  # type: ignore
    )
    existing_team_evals = {e.area: e for e in record.team_evaluations.all()} if record else {}  # type: ignore

    if request.method == "POST":
        patient_form = PatientForm(request.POST, instance=patient)
        record_form = RecordForm(request.POST, instance=record)
        discharge_form = DischargeRecordForm(request.POST, instance=discharge)

        clinical_forms = {
            ctype.value: ClinicalEvaluationForm(
                request.POST,
                instance=existing_clinical_evals.get(ctype.value),
                prefix=f"clinic-{ctype.value}",
            )
            for ctype in ClinicalEvaluationType
        }
        team_forms = {
            area.value: InterdisciplinaryEvaluationForm(
                request.POST,
                instance=existing_team_evals.get(area.value),
                prefix=f"team-{area.value}",
            )
            for area in InterdisciplinaryEvaluationArea
        }

        all_forms_valid = all(
            [
                patient_form.is_valid(),
                record_form.is_valid(),
                discharge_form.is_valid(),
                all(f.is_valid() for f in clinical_forms.values()),
                all(f.is_valid() for f in team_forms.values()),
            ]
        )

        if all_forms_valid:
            patient = patient_form.save()
            record_instance = record_form.save(commit=False)
            record_instance.patient = patient
            record_instance.record_type = "discharge"
            record_instance.save()

            discharge_instance = discharge_form.save(commit=False)
            discharge_instance.record = record_instance
            discharge_instance.save()

            for ctype_enum, form in clinical_forms.items():
                if form.cleaned_data.get("status"):
                    eval_obj, created = ClinicalEvaluation.objects.get_or_create(
                        record=record_instance, type=ctype_enum
                    )
                    eval_obj.status = form.cleaned_data["status"]
                    eval_obj.save()

            for area_enum, form in team_forms.items():
                if form.cleaned_data.get("notes"):
                    eval_obj, created = InterdisciplinaryEvaluation.objects.get_or_create(
                        record=record_instance, area=area_enum
                    )
                    eval_obj.notes = form.cleaned_data["notes"]
                    eval_obj.save()

            return redirect("patients:detail", pk=patient.pk)
    else:  # GET request
        patient_form = PatientForm(instance=patient)
        record_form = RecordForm(instance=record)
        discharge_form = DischargeRecordForm(instance=discharge)

        clinical_forms = {
            ctype.value: ClinicalEvaluationForm(
                instance=existing_clinical_evals.get(ctype.value),
                prefix=f"clinic-{ctype.value}",
            )
            for ctype in ClinicalEvaluationType
        }
        team_forms = {
            area.value: InterdisciplinaryEvaluationForm(
                instance=existing_team_evals.get(area.value),
                prefix=f"team-{area.value}",
            )
            for area in InterdisciplinaryEvaluationArea
        }

    context = {
        "patient": patient,
        "patient_form": patient_form,
        "record_form": record_form,
        "discharge_form": discharge_form,
        "clinical_forms": clinical_forms,
        "team_forms": team_forms,
        "ClinicalEvaluationType": ClinicalEvaluationType,
        "InterdisciplinaryEvaluationArea": InterdisciplinaryEvaluationArea,
    }
    return render(request, "patients/edit.html", context)


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
            and rec.consultation_details  # type: ignore
            and rec.consultation_details.weight is not None  # type: ignore
        ):
            weight = float(rec.consultation_details.weight)  # type: ignore
        # Se não for, checa de forma segura se é um registro de alta com peso
        elif hasattr(rec, "discharge") and rec.discharge and rec.discharge.weight is not None:  # type: ignore
            weight = float(rec.discharge.weight)  # type: ignore

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

            label = f"{prev['date'].strftime('%d/%m')}-{curr['date'].strftime('%d/%m')}"
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

    records_queryset = patient.records.all().order_by("-date")  # type: ignore

    query_text = request.GET.get("q")
    if query_text:
        records_queryset = records_queryset.filter(
            Q(notes__icontains=query_text) | Q(professional__icontains=query_text)
        )

    consultation_records = records_queryset.prefetch_related(
        "consultation_details", "warning_signs", "clinical_evaluations", "team_evaluations"
    )

    patient_exams = Exam.objects.filter(record__patient=patient).order_by("-date")
    patient_vaccines = Vaccine.objects.filter(record__patient=patient).order_by("-date")

    professional_strings = (
        patient.records.exclude(professional__isnull=True)  # type: ignore
        .exclude(professional__exact="")
        .values_list("professional", flat=True)
        .distinct()
    )
    processed_professionals = []
    for prof_string in professional_strings:
        parts = prof_string.split("/")
        name = parts[0].strip()
        role = parts[1].strip() if len(parts) > 1 else "Não especificado"
        processed_professionals.append({"name": name, "role": role})

    chart_context = get_growth_chart_data(patient)
    weight_gain_context = get_weight_gain_analysis_data(patient)

    # Lógica de idade corrigida no header

    patient_status = {
        "text": "Acompanhamento Normal",
        "badge_class": "badge-success",
        "reasons": [],
    }
    latest_record = consultation_records.first()
    if latest_record:
        reasons_list = []
        warning_signs = latest_record.warning_signs.filter(is_present=True)
        for sign in warning_signs:
            reasons_list.append(sign.get_type_display())
        altered_evals = latest_record.clinical_evaluations.filter(status="altered")
        for eval in altered_evals:
            reasons_list.append(f"Avaliação {eval.get_type_display()}: Alterada")
        if reasons_list:
            patient_status["text"] = "Requer Atenção"
            patient_status["badge_class"] = "badge-warning"
            patient_status["reasons"] = reasons_list

    age_details = patient.get_age_details()

    context = {
        "patient": patient,
        "consultation_records": consultation_records,
        "age_details": age_details,
        "patient_exams": patient_exams,
        "patient_vaccines": patient_vaccines,
        "team_professionals": processed_professionals,
        "patient_status": patient_status,
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
