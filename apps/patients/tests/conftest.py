# apps/patients/tests/conftest.py
import pytest
from pytest_factoryboy import register

# Importar usando caminho absoluto
from apps.patients.tests.factories import (
    ClinicalEvaluationFactory,
    DischargeRecordFactory,
    ExamFactory,
    FollowUpFactory,
    InterdisciplinaryEvaluationFactory,
    PatientFactory,
    RecordFactory,
    VaccineFactory,
)

# Registrar factories para usar como fixtures automáticas
register(PatientFactory)
register(RecordFactory)
register(DischargeRecordFactory)
register(ClinicalEvaluationFactory)
register(InterdisciplinaryEvaluationFactory)
register(ExamFactory)
register(VaccineFactory)
register(FollowUpFactory)


@pytest.fixture
def patient_with_discharge():
    """Fixture que cria paciente completo com discharge"""
    patient = PatientFactory()
    record = RecordFactory(patient=patient)
    discharge = DischargeRecordFactory(record=record)
    return patient, record, discharge


@pytest.fixture
def patient_with_full_data():
    """Fixture para paciente completo com discharge"""
    patient = PatientFactory(first_name="João", cpf="12345678901")
    record = RecordFactory(patient=patient, record_type="discharge")
    discharge = DischargeRecordFactory(record=record)
    return patient, record, discharge


@pytest.fixture
def multiple_patients():
    """Fixture que cria múltiplos pacientes para testes de lista"""
    patients = [
        PatientFactory(first_name="João", last_name="Silva", cpf="11111111111"),
        PatientFactory(
            first_name="Maria",
            last_name="Santos",
            cpf="22222222222",
            birth_certificate_number="CERT123456",  # ADICIONAR ESTA LINHA
        ),
        PatientFactory(first_name="Pedro", last_name="Oliveira", cpf="33333333333"),
    ]
    return patients


@pytest.fixture
def patient_form_data():
    """Fixture com dados para POST em views"""
    return {
        "first_name": "Ana",
        "last_name": "Costa",
        "sex": "F",
        "date_of_birth": "2023-01-15",
        "cpf": "44444444444",
        "gestational_age_weeks": "39",
        "birth_weight": "3.20",
        "date": "2023-02-01",
        "weight": "3.80",
        "feeding_type": "breastfeeding",
    }


@pytest.fixture
def patient_with_complete_data():
    """Fixture para testes frontend com dados completos"""
    patient = PatientFactory(
        first_name="Test", last_name="Patient", date_of_birth="2023-01-01", gestational_age_weeks=38
    )
    # Adicione outros dados conforme necessário
    return patient
