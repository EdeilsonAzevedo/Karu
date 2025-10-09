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
from .models import (
    ClinicalEvaluation,
    ClinicalEvaluationType,
    ClinicalWarningSign,
    InterdisciplinaryEvaluation,
    InterdisciplinaryEvaluationArea,
    Patient,
    Record,
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


# Em patients/views.py


@transaction.atomic
def patient_create(request):
    if request.method == "POST":
        patient_form = PatientForm(request.POST)
        record_form = RecordForm(request.POST)
        discharge_form = DischargeRecordForm(request.POST)

        # --- ADICIONE ESTES FORMULÁRIOS ---
        clinical_forms = {
            ctype.value: ClinicalEvaluationForm(request.POST, prefix=f"clinic-{ctype.value}")
            for ctype in ClinicalEvaluationType
        }
        team_forms = {
            area.value: InterdisciplinaryEvaluationForm(request.POST, prefix=f"team-{area.value}")
            for area in InterdisciplinaryEvaluationArea
        }

        # --- ATUALIZE A CONDIÇÃO DE VALIDAÇÃO ---
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

            record = record_form.save(commit=False)
            record.patient = patient
            record.record_type = "discharge"
            record.save()

            discharge = discharge_form.save(commit=False)
            discharge.record = record
            discharge.save()

            # --- ADICIONE A LÓGICA PARA SALVAR AS AVALIAÇÕES ---
            for ctype_enum, form in clinical_forms.items():
                if form.cleaned_data.get("status"):
                    ClinicalEvaluation.objects.create(
                        record=record, type=ctype_enum, status=form.cleaned_data["status"]
                    )

            for area_enum, form in team_forms.items():
                if form.cleaned_data.get("notes"):
                    InterdisciplinaryEvaluation.objects.create(
                        record=record, area=area_enum, notes=form.cleaned_data["notes"]
                    )
            # --- FIM DAS ADIÇÕES ---

            return redirect("patients:list")
        else:
            # Opcional, mas recomendado para debug:
            print("Patient Form Errors:", patient_form.errors)
            print("Record Form Errors:", record_form.errors)
            print("Discharge Form Errors:", discharge_form.errors)
            for key, form in clinical_forms.items():
                if not form.is_valid():
                    print(f"Clinical Form ({key}) Errors:", form.errors)
            for key, form in team_forms.items():
                if not form.is_valid():
                    print(f"Team Form ({key}) Errors:", form.errors)

    else:  # GET request
        patient_form = PatientForm()
        record_form = RecordForm()
        discharge_form = DischargeRecordForm()

        # --- ADICIONE ESTES FORMULÁRIOS TAMBÉM NO GET ---
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

    return render(
        request,
        "patients/newborn-registration.html",
        {
            "patient_form": patient_form,
            "record_form": record_form,
            "discharge_form": discharge_form,
            "clinical_forms": clinical_forms,
            "team_forms": team_forms,
            "ClinicalEvaluationType": ClinicalEvaluationType,
            "InterdisciplinaryEvaluationArea": InterdisciplinaryEvaluationArea,
        },
    )


@transaction.atomic
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    try:
        record = Record.objects.get(patient=patient, record_type="discharge")
        discharge = record.discharge
    except (Record.DoesNotExist, Record.discharge.RelatedObjectDoesNotExist):
        record = None
        discharge = None

    existing_clinical_evals = (
        {e.type: e for e in record.clinical_evaluations.all()} if record else {}
    )
    existing_team_evals = {e.area: e for e in record.team_evaluations.all()} if record else {}

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
    else:
        patient_form = PatientForm(instance=patient)
        record_form = RecordForm(instance=record)
        discharge_form = DischargeRecordForm(instance=discharge)

        clinical_forms = {
            ctype.value: ClinicalEvaluationForm(
                instance=existing_clinical_evals.get(ctype.value),
                prefix=f"clinic-{ctype.value}",
                initial={"type": ctype.value},
            )
            for ctype in ClinicalEvaluationType
        }
        team_forms = {
            area.value: InterdisciplinaryEvaluationForm(
                instance=existing_team_evals.get(area.value),
                prefix=f"team-{area.value}",
                initial={"area": area.value},
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


def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)

    # --- DADOS PARA O HISTÓRICO ---
    consultation_records = patient.records.filter(record_type="consultation").order_by("-date")

    # --- CÁLCULO DAS IDADES ---
    today = timezone.now().date()

    # 1. Idade Cronológica
    age_timedelta = today - patient.date_of_birth
    age_in_days = age_timedelta.days

    # 2. Idade Corrigida

    full_term_weeks = 40
    prematurity_in_weeks = full_term_weeks - patient.gestational_age_weeks
    corrected_age_in_days = age_in_days
    total_days_corrected = (patient.gestational_age_weeks * 7) + age_in_days
    corrected_age_weeks = total_days_corrected // 7
    corrected_age_remaining_days = total_days_corrected % 7

    if prematurity_in_weeks > 0:
        prematurity_in_days = prematurity_in_weeks * 7
        corrected_age_timedelta = age_timedelta - timedelta(days=prematurity_in_days)
        corrected_age_in_days = max(0, corrected_age_timedelta.days)

    # Dados para o gráfico de peso ao longo do tempo
    # Por enquanto busca apenas por 'discharge records' que têm peso
    # Quando as consultas tiverem peso, a lógica aqui será expandida
    records_for_chart = (
        Record.objects.filter(patient=patient, discharge__isnull=False)
        .order_by("date")
        .select_related("discharge")
    )

    chart_labels = [rec.date.strftime("%d/%m/%Y") for rec in records_for_chart]
    chart_data = [float(rec.discharge.weight) for rec in records_for_chart]

    # MONTAGEM DO CONTEXTO FINAL
    context = {
        "patient": patient,
        "consultation_records": consultation_records,
        "age_in_days": age_in_days,
        "corrected_age_in_days": corrected_age_in_days,
        "chart_labels": chart_labels,
        "chart_data": chart_data,
        "corrected_age_weeks": corrected_age_weeks,
        "corrected_age_remaining_days": corrected_age_remaining_days,
    }

    return render(request, "patients/patient_detail.html", context)


@transaction.atomic
def consultation_create(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    # Não vamos mais usar 'warning_sign_types' aqui

    if request.method == "POST":
        # A lógica de POST precisa ser ajustada para recriar os forms da mesma forma
        record_form = RecordForm(request.POST, prefix="record")
        consultation_form = ConsultationRecordForm(request.POST, prefix="consultation")

        # Recria os forms de sinais de alerta para validação
        warning_sign_forms = []
        for value, label in ClinicalWarningSign.WarningSignType.choices:
            form = ClinicalWarningSignForm(request.POST, prefix=f"warning_{value}")
            warning_sign_forms.append({"form": form, "value": value})

        # Validação
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

        # --- LÓGICA CORRIGIDA ---
        # Criamos uma lista, onde cada item tem o form e o seu label
        clinical_forms_with_labels = []
        for value, label in ClinicalWarningSign.WarningSignType.choices:
            form = ClinicalWarningSignForm(prefix=f"warning_{value}", initial={"type": value})
            clinical_forms_with_labels.append({"form": form, "label": label})
        # --- FIM DA LÓGICA CORRIGIDA ---

    # Lógica de idade corrigida
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
        "clinical_forms": clinical_forms_with_labels,  # Enviando a nova lista para o template
        "corrected_age_weeks": corrected_age_weeks,
        "corrected_age_remaining_days": corrected_age_remaining_days,
    }
    return render(request, "patients/consultation_form.html", context)
