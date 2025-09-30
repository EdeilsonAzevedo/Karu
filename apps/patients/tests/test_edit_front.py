
import pytest
from django.urls import reverse
from apps.patients.tests.factories import PatientFactory, RecordFactory, DischargeRecordFactory


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

@pytest.mark.django_db
class TestPatientEditAdditional:
    @pytest.fixture
    def patient_with_existing_discharge(self):
        patient = PatientFactory(
            first_name="João",
            last_name="Santos",
            birth_weight=3.20
        )
        record = RecordFactory(patient=patient, record_type="discharge")
        DischargeRecordFactory(record=record, weight=3.80, feeding_type="breastfeeding")
        return patient

    def test_edit_form_prefills_discharge_data_correctly(self, client, patient_with_existing_discharge):
        """Testa se o formulário pré-preenche dados de alta existentes"""
        url = reverse('patients:edit', kwargs={'pk': patient_with_existing_discharge.pk})
        response = client.get(url)
        
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        
        # Verifica se dados de discharge estão presentes
        assert '3.80' in content  # Peso na alta
        assert 'breastfeeding' in content or 'Aleitamento' in content
        
        # Verifica estrutura de grids responsivas
        assert 'grid grid-cols-1 md:grid-cols-3' in content
        assert 'grid-cols-1 md:grid-cols-4' in content
        assert 'form-control' in content

    def test_edit_form_validation_and_required_fields(self, client, patient_with_existing_discharge):
        """Testa campos obrigatórios e estrutura de validação"""
        url = reverse('patients:edit', kwargs={'pk': patient_with_existing_discharge.pk})
        response = client.get(url)
        
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        
        # Verifica campos obrigatórios
        assert 'required' in content
        assert 'first_name' in content
        assert 'date_of_birth' in content
        assert 'gestational_age_weeks' in content
        assert 'birth_weight' in content
        assert 'weight' in content  # Peso na alta
        
        # Verifica tipos de input
        assert 'type="date"' in content
        assert 'type="text"' in content
        assert 'select' in content
        
        # Verifica labels e ajuda
        assert 'label' in content
        assert 'label-text' in content
        assert 'help_text' in content or 'help' in content