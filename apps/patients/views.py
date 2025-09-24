from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import DischargeRecordForm, PatientForm, RecordForm, ClinicalEvaluationForm, InterdisciplinaryEvaluationForm
from .models import DischargeRecord, Patient, Record, ClinicalEvaluationType, InterdisciplinaryEvaluationArea

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
    patient = get_object_or_404(Patient, pk=pk)
    try:
        record = Record.objects.get(patient=patient, record_type="discharge")
        discharge = record.discharge
    except (Record.DoesNotExist, Record.discharge.RelatedObjectDoesNotExist):
        record = None
        discharge = None

    existing_clinical_evals = {e.type: e for e in record.clinical_evaluations.all()} if record else {}
    existing_team_evals = {e.area: e for e in record.team_evaluations.all()} if record else {}

    if request.method == "POST":
        patient_form = PatientForm(request.POST, instance=patient)
        record_form = RecordForm(request.POST, instance=record)
        discharge_form = DischargeRecordForm(request.POST, instance=discharge)

        clinical_forms = {
            ctype.value: ClinicalEvaluationForm(
                request.POST,
                instance=existing_clinical_evals.get(ctype.value),
                prefix=f'clinic-{ctype.value}'
            ) for ctype in ClinicalEvaluationType
        }
        team_forms = {
            area.value: InterdisciplinaryEvaluationForm(
                request.POST,
                instance=existing_team_evals.get(area.value),
                prefix=f'team-{area.value}'
            ) for area in InterdisciplinaryEvaluationArea
        }

        all_forms_valid = all([
            patient_form.is_valid(),
            record_form.is_valid(),
            discharge_form.is_valid(),
            all(f.is_valid() for f in clinical_forms.values()),
            all(f.is_valid() for f in team_forms.values())
        ])

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
                if form.cleaned_data.get('status'):
                    eval_obj, created = ClinicalEvaluation.objects.get_or_create(
                        record=record_instance, type=ctype_enum
                    )
                    eval_obj.status = form.cleaned_data['status']
                    eval_obj.save()

            for area_enum, form in team_forms.items():
                if form.cleaned_data.get('notes'):
                    eval_obj, created = InterdisciplinaryEvaluation.objects.get_or_create(
                        record=record_instance, area=area_enum
                    )
                    eval_obj.notes = form.cleaned_data['notes']
                    eval_obj.save()

            return redirect("patients:detail", pk=patient.pk)
    else:
        patient_form = PatientForm(instance=patient)
        record_form = RecordForm(instance=record)
        discharge_form = DischargeRecordForm(instance=discharge)

        clinical_forms = {
            ctype.value: ClinicalEvaluationForm(
                instance=existing_clinical_evals.get(ctype.value),
                prefix=f'clinic-{ctype.value}',
                initial={'type': ctype.value}
            ) for ctype in ClinicalEvaluationType
        }
        team_forms = {
            area.value: InterdisciplinaryEvaluationForm(
                instance=existing_team_evals.get(area.value),
                prefix=f'team-{area.value}',
                initial={'area': area.value}
            ) for area in InterdisciplinaryEvaluationArea
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

    # 2. Idade Gestacional Corrigida (formato semanas + dias)
    total_days_corrected = (patient.gestational_age_weeks * 7) + age_in_days
    corrected_age_weeks = total_days_corrected // 7
    corrected_age_remaining_days = total_days_corrected % 7
    
    # --- PREPARAÇÃO DOS DADOS PARA O GRÁFICO ---
    # (Supondo que as funções auxiliares _get_growth_chart_data e get_weight_gain_analysis_data existem)
    chart_context = _get_growth_chart_data(patient)
    weight_gain_context = get_weight_gain_analysis_data(patient)

    # --- MONTAGEM DO CONTEXTO FINAL ---
    context = {
        "patient": patient,
        "consultation_records": consultation_records,
        "age_in_days": age_in_days,
        "corrected_age_weeks": corrected_age_weeks,
        "corrected_age_remaining_days": corrected_age_remaining_days,
    }
    
    # Adiciona os dados dos gráficos ao contexto
    context.update(chart_context)
    context.update(weight_gain_context)
    
    return render(request, "patients/patient_detail.html", context)

@transaction.atomic
def consultation_create(request, patient_pk):
    patient = get_object_or_404(Patient, pk=patient_pk)
    
    clinical_types = ClinicalEvaluationType.values
    team_areas = InterdisciplinaryEvaluationArea.values
    
    if request.method == "POST":
        # Instancia o formulário do registro principal
        record_form = RecordForm(request.POST, prefix="record")
        
        # Instancia um formulário para cada tipo de avaliação
        clinical_forms = {
            ctype: ClinicalEvaluationForm(request.POST, prefix=f"clinical_{ctype}")
            for ctype in clinical_types
        }
        team_forms = {
            area: InterdisciplinaryEvaluationForm(request.POST, prefix=f"team_{area}")
            for area in team_areas
        }

        # Valida todos os formulários
        if record_form.is_valid() and all(f.is_valid() for f in clinical_forms.values()) and all(f.is_valid() for f in team_forms.values()):
            # Salva o registro principal
            record = record_form.save(commit=False)
            record.patient = patient
            record.record_type = "consultation"
            record.save()

            # Salva cada avaliação clínica, ligando ao registro principal
            for ctype, form in clinical_forms.items():
                if form.cleaned_data.get("status"): # Salva apenas se um status foi selecionado
                    evaluation = form.save(commit=False)
                    evaluation.record = record
                    evaluation.type = ctype
                    evaluation.save()

            # Salva cada avaliação da equipe, ligando ao registro principal
            for area, form in team_forms.items():
                if form.cleaned_data.get("notes"): # Salva apenas se houver anotações
                    evaluation = form.save(commit=False)
                    evaluation.record = record
                    evaluation.area = area
                    evaluation.save()

            return redirect("patients:list") # Ou para uma página de detalhes do paciente
    else:
        # Cria formulários vazios para a página
        record_form = RecordForm(prefix="record")
        clinical_forms = {
            ctype: ClinicalEvaluationForm(prefix=f"clinical_{ctype}", initial={'type': ctype})
            for ctype in clinical_types
        }
        team_forms = {
            area: InterdisciplinaryEvaluationForm(prefix=f"team_{area}", initial={'area': area})
            for area in team_areas
        }

    context = {
        "patient": patient,
        "record_form": record_form,
        "clinical_forms": clinical_forms,
        "team_forms": team_forms,
    }
    return render(request, "patients/consultation_form.html", context)

