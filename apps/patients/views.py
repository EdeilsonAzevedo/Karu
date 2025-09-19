from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.db.models import Q
from .models import Patient, Record, DischargeRecord
from .forms import PatientForm, RecordForm, DischargeRecordForm


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
        "patients/create.html",
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
        Record.objects.filter(patient=patient, record_type="discharge")
        .order_by("date")
        .first()
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
