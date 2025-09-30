# apps/patients/tests/test_list_frontend.py
import pytest
from django.urls import reverse

from apps.patients.tests.factories import PatientFactory


@pytest.mark.django_db
class TestPatientListTemplate:
    """Testes para o template list.html"""

    @pytest.fixture
    def patients(self):
        return [
            PatientFactory(first_name="João", last_name="Silva"),
            PatientFactory(first_name="Maria", last_name="Santos"),
        ]

    def test_patient_list_displays_all_patients(self, client, patients):
        """Testa se a lista exibe todos os pacientes corretamente"""
        url = reverse("patients:list")
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode("utf-8")

        # Verifica se todos os pacientes estão na lista
        assert "João Silva" in content
        assert "Maria Santos" in content

        # Verifica estrutura da tabela
        assert "table" in content
        assert "Nome do Paciente" in content
        assert "Data de Nascimento" in content
        assert "Idade Gestacional" in content
        assert "Ações" in content

    def test_patient_list_has_search_functionality(self, client, patients):
        """Testa se a funcionalidade de busca está presente"""
        url = reverse("patients:list")
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode("utf-8")

        # Verifica elementos de busca
        assert "Buscar por Nome, CPF ou Certidão" in content
        assert 'name="q"' in content
        assert 'type="text"' in content
        assert "Buscar" in content
        assert "Limpar" in content

        # Verifica botão de novo paciente
        assert "Nova Alta de RN" in content
        assert 'href="/patients/create/"' in content
