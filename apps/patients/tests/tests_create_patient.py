from django.test import TestCase
from django.urls import reverse
from apps.patients.models import (
    Patient,
    Record,
    DischargeRecord,
    ClinicalEvaluation,
    InterdisciplinaryEvaluation,
)
# Note: Você precisará importar ClinicalEvaluationType e InterdisciplinaryEvaluationArea
# Se estes enums não estiverem em models.py, ajuste a importação.
# Assumindo que você pode acessar os valores diretamente para o teste.

# Importação de enums (substitua com o caminho real se necessário)
try:
    from apps.patients.views import ClinicalEvaluationType, InterdisciplinaryEvaluationArea
except ImportError:
    # Definindo valores mockados para o teste funcionar, se os enums não forem fornecidos
    class ClinicalEvaluationType:
        pediatric = "pediatric"
        neurologic = "neurologic"
    class InterdisciplinaryEvaluationArea:
        nursing = "nursing"
        physiotherapy = "physiotherapy"
        # Adicione aqui todas as áreas que a sua view itera
        speech = "speech"
        psychology = "psychology"
        social_work = "social_work"
        occupational_therapy = "occupational_therapy"

import datetime


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
            "address_city": "Maceió",
            "address_state": "AL",
            "address_zip_code": "57000000",
            "gestational_age_weeks": 38,
            "birth_weight": 3000.50,
            
            # RecordForm
            "date": "2024-10-10",
            "professional": "Dr. House",
            "location": "Maternidade X",
            
            # DischargeRecordForm
            "weight": 3200.00,
            "feeding_type": "breastfeeding",
        }

        # 2. Adiciona TODOS os campos ocultos e de conteúdo dos formulários de avaliação.
        # Isso garante que a validação global 'all_forms_valid' na view passe.

        # ClinicalEvaluationForms (type e status)
        for ctype in self.all_clinical_types:
            # Campo oculto (type)
            self.valid_base_data[f"clinic-{ctype}-type"] = ctype
            # Campo de conteúdo (status) - enviamos vazio ("") para que não seja criado por padrão
            self.valid_base_data[f"clinic-{ctype}-status"] = "" 

        # InterdisciplinaryEvaluationForms (area e notes)
        for area in self.all_team_areas:
            # Campo oculto (area)
            self.valid_base_data[f"team-{area}-area"] = area
            # Campo de conteúdo (notes) - enviamos vazio ("")
            self.valid_base_data[f"team-{area}-notes"] = ""

    def test_get_request_loads_form_correctly(self):
        """
        Testa se a página de cadastro é carregada corretamente com um GET request.
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "patients/newborn-registration.html")
        self.assertIn("patient_form", response.context)
        self.assertFalse(response.context["patient_form"].is_bound)

    def test_post_valid_data_creates_objects_and_redirects(self):
        """
        Testa se o envio de dados válidos (POST) cria os objetos no banco de dados
        e redireciona.
        """
        # Apenas 1 ClinicalEvaluation e 1 InterdisciplinaryEvaluation serão preenchidos
        form_data = self.valid_base_data.copy()
        form_data.update({
             "cpf": "12345678901", 
             "birth_certificate_number": "CERT12345",
             # Preenche o status de uma avaliação clínica
             "clinic-pediatric-status": "normal", 
             # Preenche as notas de uma avaliação de equipe
             "team-nursing-notes": "Orientações de amamentação realizadas.", 
        })

        # Verifica o estado do banco ANTES do POST
        self.assertEqual(Patient.objects.count(), 0)

        # Envia a requisição POST
        response = self.client.post(self.url, data=form_data)
        
        # 1. Verifica se houve um redirecionamento (status 302)
        # O teste agora DEVE PASSAR neste ponto, corrigindo o 200 != 302
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("patients:list")) 

        # 2. Verifica se os objetos foram criados
        self.assertEqual(Patient.objects.count(), 1)
        self.assertEqual(Record.objects.count(), 1)
        self.assertEqual(DischargeRecord.objects.count(), 1)
        
        # A view só salva o objeto se o campo de conteúdo (status/notes) estiver preenchido
        self.assertEqual(ClinicalEvaluation.objects.count(), 1) 
        self.assertEqual(InterdisciplinaryEvaluation.objects.count(), 1) 

        # 3. Verifica alguns dados
        patient = Patient.objects.first()
        record = Record.objects.first()
        self.assertEqual(patient.cpf, "12345678901") 
        self.assertTrue(ClinicalEvaluation.objects.filter(record=record, type="pediatric", status="normal").exists())
        self.assertTrue(InterdisciplinaryEvaluation.objects.filter(record=record, area="nursing", notes="Orientações de amamentação realizadas.").exists())


    def test_post_invalid_data_rerenders_form_with_errors(self):
        """
        Testa se o envio de dados inválidos (ex: data de nascimento no futuro)
        não cria objetos e re-renderiza a página com os erros.
        """
        # Pega os dados válidos e torna um deles inválido, mas mantém todos os campos HiddenInput
        form_data = self.valid_base_data.copy()
        form_data.update({
             "date_of_birth": (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d"), # INVÁLIDO
        })
        
        response = self.client.post(self.url, data=form_data)

        # 1. Verifica se a página foi re-renderizada (status 200)
        self.assertEqual(response.status_code, 200)

        # 2. NENHUM objeto foi criado
        self.assertEqual(Patient.objects.count(), 0)
        self.assertEqual(Record.objects.count(), 0)

        # 3. Verifica se o formulário no contexto contém erros
        patient_form = response.context["patient_form"]
        self.assertTrue(patient_form.errors)
        self.assertIn("date_of_birth", patient_form.errors)


    def test_post_cpf_validation_failure(self):
        """
        Testa se a validação customizada do CPF falha com menos de 11 dígitos.
        """
        form_data = self.valid_base_data.copy()
        form_data.update({
            "cpf": "123",  # CPF inválido
        })

        response = self.client.post(self.url, data=form_data)

        # 1. Deve re-renderizar o formulário com erro (status 200)
        self.assertEqual(response.status_code, 200)
        
        # 2. Verifica se o erro customizado está presente
        patient_form = response.context["patient_form"]
        self.assertIn("cpf", patient_form.errors)
        
        # 3. Nenhuma criação de objeto
        self.assertEqual(Patient.objects.count(), 0)

    def test_post_optional_fields_empty_succeeds(self):
        """
        Testa se o envio de dados sem campos opcionais (como CPF ou Notas da Equipe)
        cria os objetos e redireciona. (e garante que ZERO avaliações são criadas)
        """
        form_data = self.valid_base_data.copy()
        # Remove campos opcionais que são limpos para None no ModelForm (como CPF)
        form_data.pop("cpf", None) 
        form_data.pop("birth_certificate_number", None)
        
        # Os campos 'status' e 'notes' já estão vazios ("") no self.valid_base_data
        
        response = self.client.post(self.url, data=form_data)

        # 1. Deve redirecionar (status 302) - a validação global PASSOU
        self.assertEqual(response.status_code, 302)
        
        # 2. Objetos principais criados
        self.assertEqual(Patient.objects.count(), 1)
        
        # 3. VERIFICAÇÃO CRÍTICA: NENHUM objeto de avaliação deve ser criado!
        # Isso corrige o erro 'AssertionError: 0 != 2'
        self.assertEqual(ClinicalEvaluation.objects.count(), 0) 
        self.assertEqual(InterdisciplinaryEvaluation.objects.count(), 0) 

        # 4. Verifica se o campo opcional (CPF) ficou nulo/vazio
        patient = Patient.objects.first()
        self.assertIsNone(patient.cpf)
        
    def test_post_interdisciplinary_evaluation_with_notes_saves_correctly(self):
        """
        Testa se as notas enviadas para uma InterdisciplinaryEvaluation são salvas corretamente.
        """
        test_notes = "Paciente responsivo e teve bom contato visual. Sem dificuldades de posicionamento."
        
        form_data = self.valid_base_data.copy()
        form_data.update({
            # Preenche apenas as notas da fisioterapia (o resto fica vazio)
            "team-physiotherapy-notes": test_notes,
        })
        
        # Envia a requisição POST
        response = self.client.post(self.url, data=form_data)
        
        # 1. Verifica se houve um redirecionamento (status 302)
        self.assertEqual(response.status_code, 302)

        # 2. Verifica se APENAS um objeto de avaliação interdiscipinar foi criado
        self.assertEqual(InterdisciplinaryEvaluation.objects.count(), 1)
        
        # 3. Verifica se o conteúdo das notas foi salvo corretamente
        team_physio = InterdisciplinaryEvaluation.objects.get(area="physiotherapy")
        self.assertEqual(team_physio.notes, test_notes)