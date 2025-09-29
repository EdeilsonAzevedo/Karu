# apps/patients/tests/test_models.py
from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from apps.patients.models import DischargeRecord, Patient

# Importar usando caminhos absolutos
from apps.patients.tests.factories import DischargeRecordFactory, PatientFactory, RecordFactory

# ============ TESTES DO MODEL PATIENT ============


@pytest.mark.django_db
def test_patient_creation(patient):
    """Testa criação básica de paciente usando fixture automática"""
    assert patient.pk is not None
    assert patient.first_name == "João"
    assert patient.sex == "M"
    assert patient.gestational_age_weeks == 38


@pytest.mark.django_db
def test_patient_str_method():
    """Testa representação string do paciente"""
    patient = PatientFactory(first_name="Pedro", last_name="Santos")
    assert str(patient) == "Pedro Santos"


@pytest.mark.django_db
def test_patient_str_without_last_name():
    """Testa str quando não tem sobrenome"""
    patient = PatientFactory(first_name="Ana", last_name=None)
    assert str(patient) == "Ana"


@pytest.mark.django_db
def test_cpf_validation():
    """Testa validação de CPF"""
    # CPF válido (11 dígitos)
    patient = PatientFactory()
    patient.full_clean()  # não deve dar erro

    # CPF inválido (menos de 11 dígitos)
    patient_invalid = Patient(
        first_name="Teste",
        sex="M",
        date_of_birth=date(2023, 1, 15),
        cpf="123456789",  # só 9 dígitos
        gestational_age_weeks=38,
        birth_weight=Decimal("3.50"),
    )

    with pytest.raises(ValidationError):
        patient_invalid.full_clean()


@pytest.mark.django_db
def test_cpf_unique_constraint():
    """Testa que CPF deve ser único"""
    PatientFactory(cpf="99999999999")

    with pytest.raises(IntegrityError):
        PatientFactory(cpf="99999999999")


@pytest.mark.django_db
def test_birth_certificate_unique():
    """Testa que certidão deve ser única"""
    PatientFactory(birth_certificate_number="CERT999999")

    with pytest.raises(IntegrityError):
        PatientFactory(birth_certificate_number="CERT999999")


@pytest.mark.django_db
def test_optional_fields():
    """Testa campos opcionais"""
    patient = PatientFactory(
        last_name=None,
        cpf=None,
        birth_certificate_number=None,
        gestational_age_days=None,
        birth_length=None,
        head_circumference=None,
    )

    patient.full_clean()  # não deve dar erro
    assert patient.last_name is None
    assert patient.cpf is None


# Testes parametrizados - muito elegante!
@pytest.mark.django_db
@pytest.mark.parametrize(
    "sex,expected",
    [
        ("M", "M"),
        ("F", "F"),
    ],
)
def test_patient_sex_choices(sex, expected):
    """Testa diferentes opções de sexo"""
    patient = PatientFactory(sex=sex)
    assert patient.sex == expected


# ============ TESTES DO MODEL RECORD ============


@pytest.mark.django_db
def test_record_creation(record):
    """Testa criação de registro usando fixture automática"""
    assert record.pk is not None
    assert record.patient is not None
    assert record.record_type == "discharge"


@pytest.mark.django_db
def test_record_patient_relationship():
    """Testa relacionamento com paciente"""
    patient = PatientFactory()
    record = RecordFactory(patient=patient)

    assert record.patient == patient
    assert record in patient.records.all()


@pytest.mark.django_db
def test_multiple_records_per_patient():
    """Testa múltiplos registros por paciente"""
    patient = PatientFactory()

    records = [
        RecordFactory(patient=patient),
        RecordFactory(patient=patient),
        RecordFactory(patient=patient),
    ]

    assert patient.records.count() == 3
    for record in records:
        assert record in patient.records.all()


@pytest.mark.parametrize("record_type", ["discharge", "consultation", "followup"])
@pytest.mark.django_db
def test_record_types(record_type):
    """Testa diferentes tipos de registro"""
    record = RecordFactory(record_type=record_type)
    assert record.record_type == record_type


# ============ TESTES DO MODEL DISCHARGE RECORD ============


@pytest.mark.django_db
def test_discharge_record_creation(discharge_record):
    """Testa criação de registro de alta usando fixture automática"""
    assert discharge_record.pk is not None
    assert discharge_record.record is not None
    assert discharge_record.weight == Decimal("4.20")
    assert discharge_record.feeding_type == "breastfeeding"


@pytest.mark.django_db
def test_discharge_one_to_one_relationship():
    """Testa relacionamento um-para-um com Record"""
    record = RecordFactory()
    discharge = DischargeRecordFactory(record=record)

    assert discharge.record == record
    assert record.discharge == discharge


@pytest.mark.django_db
def test_discharge_cascade_delete():
    """Testa deleção em cascata"""
    record = RecordFactory()
    discharge = DischargeRecordFactory(record=record)
    discharge_id = discharge.id

    record.delete()

    with pytest.raises(DischargeRecord.DoesNotExist):
        DischargeRecord.objects.get(id=discharge_id)


@pytest.mark.parametrize("feeding_type", ["breastfeeding", "mixed", "formula"])
@pytest.mark.django_db
def test_feeding_types(feeding_type):
    """Testa diferentes tipos de alimentação"""
    discharge = DischargeRecordFactory(feeding_type=feeding_type)
    assert discharge.feeding_type == feeding_type


# ============ TESTES COM FIXTURES COMPLEXAS ============


@pytest.mark.django_db
def test_patient_with_discharge_fixture(patient_with_discharge):
    """Testa usando fixture complexa que cria tudo junto"""
    patient, record, discharge = patient_with_discharge

    assert patient.records.count() == 1
    assert record.patient == patient
    assert discharge.record == record
    assert discharge.weight == Decimal("4.20")


@pytest.mark.django_db
def test_complete_patient_workflow():
    """Testa workflow completo de criação"""
    # Criar paciente
    patient = PatientFactory(first_name="Workflow", cpf="99999999998")

    # Criar record
    record = RecordFactory(patient=patient, record_type="discharge")

    # Criar discharge
    discharge = DischargeRecordFactory(record=record, weight=Decimal("5.00"))

    # Verificar relacionamentos
    assert patient.records.first() == record
    assert record.discharge == discharge
    assert str(patient) == "Workflow Silva"
