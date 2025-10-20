import datetime
from enum import Enum

from django.test import TestCase
from django.urls import reverse

from apps.patients.models import (
    ClinicalEvaluation,
    DischargeRecord,
    InterdisciplinaryEvaluation,
    Patient,
    Record,
)


# --- ENUMS CORRIGIDOS ---
# Definir Enums completos para o teste garante que todos os campos esperados pela view existam.
# Isso corrige o erro de iteração e garante que `ctype.value` funcione.
class ClinicalEvaluationType(Enum):
    pediatric = "pediatric"
    neurologic = "neurologic"
    cardiac = "cardiac"
    visual = "visual"
    auditory = "auditory"

class InterdisciplinaryEvaluationArea(Enum):
    nursing = "nursing"
    physiotherapy = "physiotherapy"
    speech = "speech"
    psychology = "psychology"
    social_work = "social_work"
    occupational_therapy = "occupational_therapy"


class PatientCreateViewTests(TestCase):
    """
    Testes para a view de criação de pacientes (patient_create).
    """

    def setUp(self):
        """
        Configuração inicial para os testes, define a URL da view e os dados base.
        """
        self.url = reverse("patients:create")

        # 1. Define todas as chaves (tipos e áreas) que a view espera
        self.all_clinical_types = [ctype.value for ctype in ClinicalEvaluationType]
        self.all_team_areas = [area.value for area in InterdisciplinaryEvaluationArea]
        
        # Dados Mínimos Válidos para Reuso
        self.valid_base_data = {
            # PatientForm (campos obrigatórios mínimos)
            "first_name": "Teste",
            "last_name": "Bebe",
            "date_of_birth": "2024-10-01",
            "sex": "M",
            "guardian_name": "Maria Teste",
            "contact_phone": "82999998888",
            "address_street": "Rua dos Testes",
            "address_number": "123",
            "address_neighborhood": "Bairro Teste",
            "address_city": "Maceió",
            "address_state": "AL",
            "address_zip_code": "57000000",
            "gestational_age_weeks": 38,
            "birth_weight": 3000.50,
            
            # RecordForm
            "date": "2024-10-10",
            "professional": "Dr. House",
            "location": "Maternidade X",
            
            # DischargeRecordForm (CAMPOS FALTANTES ADICIONADOS)
            "weight": 3200.00,
            "length": 50.5,
            "head_circumference": 35.2,
            "feeding_type": "breastfeeding",
        }

        # 2. Adiciona TODOS os campos ocultos e de conteúdo dos formulários de avaliação.
        # Isso garante que a validação global 'all_forms_valid' na view passe.

        # ClinicalEvaluationForms (type e status)
        for ctype in self.all_clinical_types:
            self.valid_base_data[f"clinic-{ctype}-type"] = ctype
            self.valid_base_data[f"clinic-{ctype}-status"] = "" 

        # InterdisciplinaryEvaluationForms (area e notes)
        for area in self.all_team_areas:
            self.valid_base_data[f"team-{area}-area"] = area
            self.valid_base_data[f"team-{area}-notes"] = ""

    def test_get_request_loads_form_correctly(self):
        """
        Testa se a página de cadastro é carregada corretamente com um GET request.
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        # Ajuste o nome do template para o que você está usando
        self.assertTemplateUsed(response, "patients/patient_form.html") 
        self.assertIn("patient_form", response.context)
        self.assertFalse(response.context["patient_form"].is_bound)

    def test_post_valid_data_creates_objects_and_redirects(self):
        """
        Testa se o envio de dados válidos (POST) cria os objetos no banco e redireciona.
        """
        form_data = self.valid_base_data.copy()
        form_data.update({
             "cpf": "12345678901", 
             "birth_certificate_number": "CERT12345",
             "clinic-pediatric-status": "normal", 
             "team-nursing-notes": "Orientações de amamentação realizadas.", 
             "length": 50.5,
             "head_circumference": 35.2,
        })

        self.assertEqual(Patient.objects.count(), 0)

        response = self.client.post(self.url, data=form_data)
        
        # 1. Verifica o redirecionamento
        self.assertEqual(response.status_code, 302, f"O formulário não foi validado. Erros: {response.context.get('patient_form').errors if response.context else 'No context'}")
        self.assertRedirects(response, reverse("patients:list")) 

        # 2. Verifica a criação dos objetos
        self.assertEqual(Patient.objects.count(), 1)
        self.assertEqual(Record.objects.count(), 1)
        self.assertEqual(DischargeRecord.objects.count(), 1)
        self.assertEqual(ClinicalEvaluation.objects.count(), 1) 
        self.assertEqual(InterdisciplinaryEvaluation.objects.count(), 1) 

        # 3. Verifica dados específicos
        patient = Patient.objects.first()
        record = Record.objects.first()
        self.assertEqual(patient.cpf, "12345678901") 
        self.assertTrue(ClinicalEvaluation.objects.filter(record=record, type="pediatric", status="normal").exists())
        self.assertTrue(InterdisciplinaryEvaluation.objects.filter(record=record, area="nursing", notes="Orientações de amamentação realizadas.").exists())

    def test_post_invalid_data_rerenders_form_with_errors(self):
        """
        Testa se o envio de dados inválidos não cria objetos e re-renderiza a página com erros.
        """
        form_data = self.valid_base_data.copy()
        form_data["date_of_birth"] = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = self.client.post(self.url, data=form_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Patient.objects.count(), 0)
        self.assertEqual(Record.objects.count(), 0)

        patient_form = response.context["patient_form"]
        self.assertTrue(patient_form.errors)
        self.assertIn("date_of_birth", patient_form.errors)

    def test_post_optional_fields_empty_succeeds(self):
        """
        Testa se o envio sem campos opcionais (CPF, etc.) e sem avaliações funciona.
        """
        form_data = self.valid_base_data.copy()
        
        response = self.client.post(self.url, data=form_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Patient.objects.count(), 1)
        
        # VERIFICAÇÃO CRÍTICA: Nenhuma avaliação deve ser criada se os campos estiverem vazios
        self.assertEqual(ClinicalEvaluation.objects.count(), 0) 
        self.assertEqual(InterdisciplinaryEvaluation.objects.count(), 0) 

        patient = Patient.objects.first()
        self.assertIsNone(patient.cpf)