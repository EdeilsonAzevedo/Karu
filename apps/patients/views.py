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
    """
    Edita Paciente + (Record discharge + DischargeRecord).
    Se ainda não existir Record/DischargeRecord, cria durante a edição quando os campos mínimos forem válidos.
    """
    patient = get_object_or_404(Patient, pk=pk)

    # tenta achar o record de alta existente
    record = (
        Record.objects.filter(patient=patient, record_type="discharge").order_by("date").first()
    )
    discharge = None
    if record:
        discharge = DischargeRecord.objects.filter(record=record).first()

    if request.method == "POST":
        patient_form = PatientForm(request.POST, instance=patient)

        # Se já existem, edita; senão, prepara para criar
        record_form = RecordForm(request.POST, instance=record)
        discharge_form = DischargeRecordForm(request.POST, instance=discharge)

        # Validamos tudo; se record/discharge não existirem ainda, os forms sem instance ainda validam os dados
        if patient_form.is_valid() and record_form.is_valid() and discharge_form.is_valid():
            patient_form.save()

            # cria ou atualiza record discharge
            record_obj = record_form.save(commit=False)
            record_obj.patient = patient
            record_obj.record_type = "discharge"
            record_obj.save()

            # cria ou atualiza discharge record
            discharge_obj = discharge_form.save(commit=False)
            discharge_obj.record = record_obj
            discharge_obj.save()

            return redirect("patients:list")
    else:
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
        },
    )

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

def patient_detail(request, pk):
    patient: Patient = get_object_or_404(Patient, pk=pk)
    
    consultation_records = patient.records.filter(record_type='consultation').order_by('-date')
    
    # Calcula a idade atual do paciente em dias
    age = timezone.now().date() - patient.date_of_birth
    age_in_days = age.days

    context = {
        "patient": patient,
        "consultation_records": consultation_records,
        "age_in_days": age_in_days,
    }
    return render(request, "patients/patient_detail.html", context)