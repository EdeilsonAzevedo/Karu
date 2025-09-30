# apps/patients/tests/test_edit_frontend.py
import pytest
from django.urls import reverse

from apps.patients.tests.factories import PatientFactory


@pytest.mark.django_db
class TestPatientEditTemplate:
    """Testes para o template edit.html"""

    @pytest.fixture
    def patient(self):
        return PatientFactory(
            first_name="Ana",
            last_name="Costa",
        )

    def test_edit_form_contains_all_sections(self, client, patient):
        """Testa se o formulário de edição contém todas as seções"""
        url = reverse("patients:edit", kwargs={"pk": patient.pk})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode("utf-8")

        # Verifica seções do formulário
        assert "Dados do Paciente" in content
        assert "Dados do Nascimento" in content
        assert "Dados da Alta" in content

        # Verifica campos do formulário
        assert "first_name" in content
        assert "last_name" in content
        assert "date_of_birth" in content
        assert "gestational_age_weeks" in content
        assert "birth_weight" in content

        # Verifica botões de ação
        assert "Salvar Alterações" in content
        assert "Cancelar" in content

    def test_edit_form_prefills_patient_data(self, client, patient):
        """Testa se o formulário pré-preenche os dados do paciente"""
        url = reverse("patients:edit", kwargs={"pk": patient.pk})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode("utf-8")

        # Verifica se os dados do paciente estão no formulário
        assert patient.first_name in content
        assert patient.last_name in content

        # Verifica estrutura do formulário
        assert "form" in content
        assert 'method="POST"' in content
        assert "csrfmiddlewaretoken" in content

        # Verifica navegação
        assert "Voltar para a lista" in content
        assert "Editando Alta de" in content
