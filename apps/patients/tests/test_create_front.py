# apps/patients/tests/test_create_frontend.py
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestPatientCreateTemplate:
    """Testes para o template newborn-registration.html"""

    def test_create_form_has_all_required_sections(self, client):
        """Testa se o formulário de criação tem todas as seções necessárias"""
        url = reverse("patients:create")
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode("utf-8")

        # Verifica todas as seções do formulário
        assert "Dados do Paciente" in content
        assert "Dados do Nascimento" in content
        assert "Dados da Alta" in content
        assert "Avaliações Clínicas" in content
        assert "Avaliações da Equipe" in content
        assert "Confirmação" in content

        # Verifica passos do progresso
        assert "steps" in content
        assert "Paciente" in content
        assert "Nascimento" in content
        assert "Alta" in content

    def test_create_form_has_required_fields_and_structure(self, client):
        """Testa se o formulário tem campos obrigatórios e estrutura correta"""
        url = reverse("patients:create")
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode("utf-8")

        # Verifica campos obrigatórios
        assert "required" in content
        assert "first_name" in content
        assert "date_of_birth" in content
        assert "sex" in content
        assert "gestational_age_weeks" in content
        assert "birth_weight" in content
        assert "weight" in content
        assert "feeding_type" in content

        # Verifica estrutura do formulário
        assert "form" in content
        assert 'method="POST"' in content
        assert "csrfmiddlewaretoken" in content

        # Verifica botões
        assert "Salvar alta" in content
        assert "Limpar" in content
