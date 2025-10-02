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

@pytest.mark.django_db
class TestPatientListAdditional:
    """Testes adicionais para o template list.html"""
    
    @pytest.fixture
    def patients_with_various_data(self):
        return [
            PatientFactory(first_name="Ana", last_name="Silva", gestational_age_weeks=38),
            PatientFactory(first_name="Paulo", last_name="", gestational_age_weeks=32, gestational_age_days=3),
            PatientFactory(first_name="Maria", last_name="Costa", gestational_age_weeks=40),
        ]

    def test_list_displays_gestational_age_correctly(self, client, patients_with_various_data):
        """Testa se a idade gestacional é exibida corretamente em todos os formatos"""
        url = reverse('patients:list')
        response = client.get(url)
        
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        
        # Verifica diferentes formatos de idade gestacional
        assert '38 semanas' in content
        assert '32 semanas e 3 dias' in content or '32 semanas' in content
        assert '40 semanas' in content
        
        # Verifica pacientes sem sobrenome
        assert 'Paulo' in content  # Nome sem sobrenome deve aparecer

    def test_list_empty_state_and_pagination_elements(self, client):
        """Testa estados vazios e elementos de paginação/controle"""
        url = reverse('patients:list')
        response = client.get(url)
        
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        
        # Verifica elementos de controle da tabela
        assert 'table' in content
        assert 'thead' in content
        assert 'tbody' in content
        assert 'Nenhum paciente encontrado' in content
        
        # Verifica botões de ação
        assert 'Editar' in content
        assert 'btn' in content
        assert 'btn-info' in content or 'btn-outline' in content
        
        # Verifica estrutura responsiva
        assert 'overflow-x-auto' in content
        assert 'table-zebra' in content or 'table' in content
=======
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
>>>>>>> cbc9f21 (test: adicionar cobertura completa de testes templates)
=======

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

@pytest.mark.django_db
class TestPatientListAdditional:
    """Testes adicionais para o template list.html"""
    
    @pytest.fixture
    def patients_with_various_data(self):
        return [
            PatientFactory(first_name="Ana", last_name="Silva", gestational_age_weeks=38),
            PatientFactory(first_name="Paulo", last_name="", gestational_age_weeks=32, gestational_age_days=3),
            PatientFactory(first_name="Maria", last_name="Costa", gestational_age_weeks=40),
        ]

    def test_list_displays_gestational_age_correctly(self, client, patients_with_various_data):
        """Testa se a idade gestacional é exibida corretamente em todos os formatos"""
        url = reverse('patients:list')
        response = client.get(url)
        
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        
        # Verifica diferentes formatos de idade gestacional
        assert '38 semanas' in content
        assert '32 semanas e 3 dias' in content or '32 semanas' in content
        assert '40 semanas' in content
        
        # Verifica pacientes sem sobrenome
        assert 'Paulo' in content  # Nome sem sobrenome deve aparecer

    def test_list_empty_state_and_pagination_elements(self, client):
        """Testa estados vazios e elementos de paginação/controle"""
        url = reverse('patients:list')
        response = client.get(url)
        
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        
        # Verifica elementos de controle da tabela
        assert 'table' in content
        assert 'thead' in content
        assert 'tbody' in content
        assert 'Nenhum paciente encontrado' in content
        
        # Verifica botões de ação
        assert 'Editar' in content
        assert 'btn' in content
        assert 'btn-info' in content or 'btn-outline' in content
        
        # Verifica estrutura responsiva
        assert 'overflow-x-auto' in content
        assert 'table-zebra' in content or 'table' in content
>>>>>>> a900ad8 (test: adicionar novos testes para cada template)
