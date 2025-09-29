from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    ClinicalWarningSignForm,
    ConsultationRecordForm,
    DischargeRecordForm,
    PatientForm,
    RecordForm,
)
from .models import (
    ClinicalWarningSign,
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


@transaction.atomic
def patient_create(request):
    """
    Cria Paciente + Record(discharge) + DischargeRecord.
    Campos mínimos exigidos:
      - Patient: básicos (modelo)
      - Record: date
      - DischargeRecord: weight
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
    """Edita dados do paciente e cria/atualiza seus registros de alta."""
    patient = get_object_or_404(Patient, pk=pk)

    # Tenta buscar o record e discharge existentes. Pode não haver nenhum.
    try:
        record = Record.objects.get(patient=patient, record_type="discharge")
        discharge = record.discharge
    except (Record.DoesNotExist, Record.discharge.RelatedObjectDoesNotExist):
        record = None
        discharge = None

    if request.method == "POST":
        # Passamos 'instance=...' para os forms para que eles saibam se devem
        # atualizar um objeto existente (UPDATE) ou criar um novo (INSERT).
        patient_form = PatientForm(request.POST, instance=patient)
        record_form = RecordForm(request.POST, instance=record)
        discharge_form = DischargeRecordForm(request.POST, instance=discharge)

        if patient_form.is_valid() and record_form.is_valid() and discharge_form.is_valid():
            # Salva as alterações do paciente
            patient = patient_form.save()

            # Cria ou atualiza o Record
            record_instance = record_form.save(commit=False)
            record_instance.patient = patient
            record_instance.record_type = "discharge"
            record_instance.save()

            # Cria ou atualiza o DischargeRecord
            discharge_instance = discharge_form.save(commit=False)
            discharge_instance.record = record_instance
            discharge_instance.save()

            return redirect("patients:detail", pk=patient.pk)
    else:
        # Popula os formulários com os dados existentes
        patient_form = PatientForm(instance=patient)
        record_form = RecordForm(instance=record)
        discharge_form = DischargeRecordForm(instance=discharge)

    return render(
        request,
        "patients/edit.html",
        {
            "patient_form": patient_form,
            "record_form": record_form,
            "discharge_form": discharge_form,
            "patient": patient,
        },
    )


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
