# apps/patients/tests/test_views.py
from decimal import Decimal

import pytest

from apps.patients.models import DischargeRecord, Patient, Record

# Importar usando caminhos absolutos para pytest
from apps.patients.tests.factories import PatientFactory

# ============ TESTES DA VIEW PATIENT LIST ============


@pytest.mark.django_db
def test_patient_list_view_status_code(client):
    """Testa se a view carrega corretamente"""
    url = "/patients/"  # ou reverse('patients:list') se usar namespaces
    response = client.get(url)

    assert response.status_code == 200


@pytest.mark.django_db
def test_patient_list_shows_patients(client, multiple_patients):
    """Testa se mostra os pacientes na lista"""
    url = "/patients/"
    response = client.get(url)

    assert response.status_code == 200
    assert "João" in response.content.decode()
    assert "Maria" in response.content.decode()
    assert "Pedro" in response.content.decode()


@pytest.mark.django_db
def test_patient_list_search_by_name(client, multiple_patients):
    """Testa busca por nome usando parâmetro 'q'"""
    url = "/patients/"
    response = client.get(url, {"q": "João"})

    content = response.content.decode()
    assert "João" in content
    assert "Maria" not in content
    assert "Pedro" not in content


@pytest.mark.django_db
def test_patient_list_search_by_cpf(client, multiple_patients):
    """Testa busca por CPF usando parâmetro 'q'"""
    url = "/patients/"
    response = client.get(url, {"q": "11111111111"})

    content = response.content.decode()
    assert "João" in content
    assert "Maria" not in content


@pytest.mark.django_db
def test_patient_list_search_by_certificate(client, multiple_patients):
    """Testa busca por certidão usando parâmetro 'q'"""
    url = "/patients/"
    response = client.get(url, {"q": "CERT123456"})

    content = response.content.decode()
    assert "Maria" in content
    assert "João" not in content


@pytest.mark.django_db
@pytest.mark.parametrize(
    "search_param,search_value,expected_name",
    [
        ("name", "João", "João"),
        ("cpf", "22222222222", "Maria"),
        ("sal", "CERT123456", "Maria"),
    ],
)
def test_patient_list_specific_field_search(
    client, multiple_patients, search_param, search_value, expected_name
):
    """Testa busca por campos específicos usando testes parametrizados"""
    url = "/patients/"
    response = client.get(url, {search_param: search_value})

    content = response.content.decode()
    assert expected_name in content


@pytest.mark.django_db
def test_patient_list_empty_search(client, multiple_patients):
    """Testa que busca vazia retorna todos os pacientes"""
    url = "/patients/"
    response = client.get(url, {"q": ""})

    content = response.content.decode()
    assert "João" in content
    assert "Maria" in content
    assert "Pedro" in content


@pytest.mark.django_db
def test_patient_list_no_results(client):
    """Testa busca que não retorna resultados"""
    url = "/patients/"
    response = client.get(url, {"q": "NomeQueNaoExiste"})

    content = response.content.decode()
    assert "João" not in content
    assert "Maria" not in content


# ============ TESTES DA VIEW PATIENT CREATE ============


@pytest.mark.django_db
def test_patient_create_get(client):
    """Testa GET da view de criação"""
    url = "/patients/create/"
    response = client.get(url)

    assert response.status_code == 200


@pytest.mark.django_db
def test_patient_create_post_success(client, patient_form_data):
    """Testa criação bem-sucedida de paciente"""
    url = "/patients/create/"

    # Contar registros antes
    initial_patients = Patient.objects.count()
    initial_records = Record.objects.count()
    initial_discharges = DischargeRecord.objects.count()

    response = client.post(url, patient_form_data)

    # Deve redirecionar após sucesso
    assert response.status_code == 302

    # Verifica se todos foram criados
    assert Patient.objects.count() == initial_patients + 1
    assert Record.objects.count() == initial_records + 1
    assert DischargeRecord.objects.count() == initial_discharges + 1

    # Verifica se o paciente foi criado corretamente
    patient = Patient.objects.get(cpf="44444444444")
    assert patient.first_name == "Ana"
    assert patient.birth_weight == Decimal("3.20")

    # Verifica se o record foi criado
    record = Record.objects.get(patient=patient)
    assert record.record_type == "discharge"

    # Verifica se o discharge foi criado
    discharge = DischargeRecord.objects.get(record=record)
    assert discharge.weight == Decimal("3.80")


@pytest.mark.django_db
def test_patient_create_post_invalid_data(client):
    """Testa criação com dados inválidos"""
    url = "/patients/create/"

    invalid_data = {
        "first_name": "",  # campo obrigatório vazio
        "sex": "M",
        "date_of_birth": "2023-01-15",
    }

    response = client.post(url, invalid_data)

    # Não deve redirecionar, deve mostrar erros
    assert response.status_code == 200


# ============ TESTES DA VIEW PATIENT EDIT ============


@pytest.mark.django_db
def test_patient_edit_get_with_existing_data(client, patient_with_full_data):
    """Testa GET da view de edição com dados existentes"""
    patient, record, discharge = patient_with_full_data

    url = f"/patients/{patient.pk}/edit/"
    response = client.get(url)

    assert response.status_code == 200
    assert patient.first_name in response.content.decode()


@pytest.mark.django_db
def test_patient_edit_get_without_discharge_record(client):
    """Testa GET da view de edição sem record de discharge"""
    patient = PatientFactory()

    url = f"/patients/{patient.pk}/edit/"
    response = client.get(url)

    assert response.status_code == 200


@pytest.mark.django_db
def test_patient_edit_post_success(client, patient_with_full_data):
    """Testa edição bem-sucedida"""
    patient, record, discharge = patient_with_full_data

    url = f"/patients/{patient.pk}/edit/"

    edit_data = {
        "first_name": "João Carlos",  # nome modificado
        "last_name": patient.last_name or "",
        "sex": patient.sex,
        "date_of_birth": "2023-01-15",
        "gestational_age_weeks": str(patient.gestational_age_weeks),
        "birth_weight": str(patient.birth_weight),
        "date": "2023-02-01",
        "weight": "5.00",  # peso modificado
        "feeding_type": discharge.feeding_type,
    }

    response = client.post(url, edit_data)

    assert response.status_code == 302

    # Verifica se as alterações foram salvas
    patient.refresh_from_db()
    discharge.refresh_from_db()

    assert patient.first_name == "João Carlos"
    assert discharge.weight == Decimal("5.00")


@pytest.mark.django_db
def test_patient_edit_creates_missing_records(client):
    """Testa se cria records que não existiam"""
    patient = PatientFactory()

    url = f"/patients/{patient.pk}/edit/"

    data = {
        "first_name": patient.first_name,
        "last_name": patient.last_name or "",
        "sex": patient.sex,
        "date_of_birth": "2023-01-15",
        "gestational_age_weeks": str(patient.gestational_age_weeks),
        "birth_weight": str(patient.birth_weight),
        "date": "2023-02-01",  # novo record
        "weight": "4.50",  # novo discharge
        "feeding_type": "mixed",
    }

    response = client.post(url, data)

    assert response.status_code == 302

    # Verifica se foram criados
    record = Record.objects.get(patient=patient, record_type="discharge")
    discharge = DischargeRecord.objects.get(record=record)

    assert discharge.weight == Decimal("4.50")


@pytest.mark.django_db
def test_patient_edit_invalid_pk(client):
    """Testa acesso com ID inválido"""
    url = "/patients/99999/edit/"
    response = client.get(url)

    assert response.status_code == 404


# ============ TESTES DE INTEGRAÇÃO ============


@pytest.mark.django_db
@pytest.mark.integration
def test_complete_patient_workflow(client, patient_form_data):
    """Testa fluxo completo: criar -> listar -> editar"""

    # 1. Criar paciente
    create_url = "/patients/create/"
    response = client.post(create_url, patient_form_data)
    assert response.status_code == 302

    # 2. Verificar na lista
    list_url = "/patients/"
    response = client.get(list_url)
    assert "Ana" in response.content.decode()

    # 3. Editar paciente
    patient = Patient.objects.get(first_name="Ana")
    edit_url = f"/patients/{patient.pk}/edit/"

    edit_data = patient_form_data.copy()
    edit_data["first_name"] = "Ana Editada"

    response = client.post(edit_url, edit_data)
    assert response.status_code == 302

    # 4. Verificar edição na lista
    response = client.get(list_url)
    content = response.content.decode()
    assert "Ana Editada" in content
