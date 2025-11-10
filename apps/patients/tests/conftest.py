import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from pytest_factoryboy import register

from apps.accounts.factories import (
    GestorProfileFactory,
    PaisProfileFactory,
    ProfissionalSaudeProfileFactory,
    UserFactory,
)
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

register(UserFactory)
register(GestorProfileFactory)
register(ProfissionalSaudeProfileFactory)
register(PaisProfileFactory)


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
            birth_certificate_number="CERT123456",
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
        "gestational_age_weeks": 39,
        "birth_weight": "3.20",
        "date": "2023-02-01",
        "weight": "3.80",
        "feeding_type": "breastfeeding",
    }


User = get_user_model()


@pytest.fixture
def ensure_groups(db):
    """Cria os grupos necessários e retorna dict com instâncias."""
    groups = {}
    for name in ["gestores", "profissionais_saude", "pais"]:
        groups[name], _ = Group.objects.get_or_create(name=name)
    return groups


@pytest.fixture
def gestor_user(db, ensure_groups):
    """Usuário no grupo gestores (pode criar prof/pais)."""
    u = User.objects.create_user(
        username="11111111111",
        first_name="Gestor",
        email="gestor@example.com",
        password="Gestor@1234",
        is_active=True,
    )
    u.groups.add(ensure_groups["gestores"])
    return u


@pytest.fixture
def client_logged_gestor(client, gestor_user):
    client.login(username=gestor_user.username, password="Gestor@1234")
    return client
